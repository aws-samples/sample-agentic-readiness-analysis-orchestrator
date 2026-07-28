"""
Constraint Extractor — Extracts formal declarative constraints from a
parsed BPMN process, inspired by the BPMN2Constraints approach (Bergman,
Rebmann, Kampik — SAP Signavio).

Produces DECLARE-style constraints directly from the BPMN graph topology:
  - init / end              — which activities start/end the process
  - succession              — A always followed by B (and B preceded by A)
  - precedence              — A must happen before B
  - response                — after A, B must eventually happen
  - co_existence            — A and B always appear together
  - exclusive_choice        — exactly one of A or B (XOR gateway)
  - choice                  — at least one of A or B
  - not_coexistence         — A and B never both occur (derived from XOR)
  - chain_succession        — A immediately followed by B in a linear chain
  - alternate_response      — after A, B must happen before A recurs
  - chain_precedence        — B immediately preceded by A
  - responded_existence     — if A occurs then B must also occur (parallel)

No external dependencies. Works directly on our BPMNProcess dataclass.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from collections import deque
from parser.bpmn_parser import BPMNProcess, ProcessElement, ElementType

# Characters that require quoting an activity name inside formulas
_OPERATOR_PATTERN = re.compile(r'[∧∨→¬FGXU()]')


class ConstraintType(Enum):
    INIT = "init"
    END = "end"
    SUCCESSION = "succession"
    PRECEDENCE = "precedence"
    RESPONSE = "response"
    CO_EXISTENCE = "co_existence"
    EXCLUSIVE_CHOICE = "exclusive_choice"
    CHOICE = "choice"
    NOT_COEXISTENCE = "not_coexistence"
    CHAIN_SUCCESSION = "chain_succession"
    ALTERNATE_RESPONSE = "alternate_response"
    CHAIN_PRECEDENCE = "chain_precedence"
    RESPONDED_EXISTENCE = "responded_existence"


def _quote_name(name: str) -> str:
    """Wrap an activity name in double quotes if it contains operator symbols or parentheses."""
    if _OPERATOR_PATTERN.search(name):
        return f'"{name}"'
    return name


@dataclass
class Constraint:
    """A single declarative constraint between process activities."""
    constraint_type: ConstraintType
    source: str            # element name (or id if unnamed)
    target: str = ""       # second element (empty for init/end)
    description: str = ""

    def to_signal(self) -> str:
        """Return SIGNAL temporal logic formula string."""
        A = _quote_name(self.source)
        B = _quote_name(self.target) if self.target else ""
        ct = self.constraint_type
        try:
            return {
                ConstraintType.INIT:                A,
                ConstraintType.END:                 f"F({A} ∧ ¬X ⊤)",
                ConstraintType.SUCCESSION:          f"G({A} → X {B})",
                ConstraintType.RESPONSE:            f"G({A} → F {B})",
                ConstraintType.PRECEDENCE:          f"¬{B} U {A}",
                ConstraintType.EXCLUSIVE_CHOICE:    f"G({A} → ¬F {B}) ∧ G({B} → ¬F {A})",
                ConstraintType.CO_EXISTENCE:        f"(F {A} → F {B}) ∧ (F {B} → F {A})",
                ConstraintType.NOT_COEXISTENCE:     f"¬(F {A} ∧ F {B})",
                ConstraintType.CHOICE:              f"F {A} ∨ F {B}",
                ConstraintType.CHAIN_SUCCESSION:    f"G({A} → X {B}) ∧ G({B} → Y {A})",
                ConstraintType.ALTERNATE_RESPONSE:  f"G({A} → X(¬{A} U {B}))",
                ConstraintType.CHAIN_PRECEDENCE:    f"G({B} → Y {A})",
                ConstraintType.RESPONDED_EXISTENCE: f"F {A} → F {B}",
            }[ct]
        except KeyError:
            type_str = ct.value if isinstance(ct, ConstraintType) else str(ct)
            return f"UNSUPPORTED: {type_str}"

    def to_ltlf(self) -> str:
        """Return LTLf formula string."""
        A = _quote_name(self.source)
        B = _quote_name(self.target) if self.target else ""
        ct = self.constraint_type
        try:
            return {
                ConstraintType.INIT:                A,
                ConstraintType.END:                 f"F({A} ∧ ¬X ⊤)",
                ConstraintType.SUCCESSION:          f"G({A} → X {B}) ∧ G({B} → ¬{B} U {A})",
                ConstraintType.RESPONSE:            f"G({A} → F {B})",
                ConstraintType.PRECEDENCE:          f"¬{B} U {A}",
                ConstraintType.EXCLUSIVE_CHOICE:    f"(F {A} ∨ F {B}) ∧ ¬(F {A} ∧ F {B})",
                ConstraintType.CO_EXISTENCE:        f"(F {A} → F {B}) ∧ (F {B} → F {A})",
                ConstraintType.NOT_COEXISTENCE:     f"¬(F {A} ∧ F {B})",
                ConstraintType.CHOICE:              f"F {A} ∨ F {B}",
                ConstraintType.CHAIN_SUCCESSION:    f"G({A} → X {B}) ∧ G({B} → Y {A})",
                ConstraintType.ALTERNATE_RESPONSE:  f"G({A} → X(¬{A} U {B}))",
                ConstraintType.CHAIN_PRECEDENCE:    f"G({B} → Y {A})",
                ConstraintType.RESPONDED_EXISTENCE: f"F {A} → F {B}",
            }[ct]
        except KeyError:
            type_str = ct.value if isinstance(ct, ConstraintType) else str(ct)
            return f"unsupported constraint type: {type_str}"


@dataclass
class ConstraintProfile:
    """Complete constraint profile for a BPMN process."""
    process_name: str
    constraints: list[Constraint] = field(default_factory=list)
    total_elements: int = 0
    total_tasks: int = 0
    max_gateway_depth: int = 0
    deeply_nested: bool = False  # True when max_gateway_depth >= 4

    # ── Derived metrics ──────────────────────────────────────────────
    @property
    def total_constraints(self) -> int:
        return len(self.constraints)

    @property
    def constraint_density(self) -> float:
        """Constraints per element — higher = more structurally complex."""
        return self.total_constraints / max(self.total_elements, 1)

    @property
    def by_type(self) -> dict[str, int]:
        """Count constraints by type."""
        counts: dict[str, int] = {}
        for c in self.constraints:
            key = c.constraint_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def ordering_constraints(self) -> int:
        """Count of ordering constraints (succession + precedence + response)."""
        ordering = {ConstraintType.SUCCESSION, ConstraintType.PRECEDENCE,
                     ConstraintType.RESPONSE}
        return sum(1 for c in self.constraints if c.constraint_type in ordering)

    @property
    def exclusion_constraints(self) -> int:
        """Count of mutual exclusion constraints (exclusive_choice + not_coexistence)."""
        exclusion = {ConstraintType.EXCLUSIVE_CHOICE, ConstraintType.NOT_COEXISTENCE}
        return sum(1 for c in self.constraints if c.constraint_type in exclusion)

    @property
    def coexistence_constraints(self) -> int:
        """Count of co-occurrence constraints."""
        return sum(1 for c in self.constraints
                   if c.constraint_type == ConstraintType.CO_EXISTENCE)

    def constraints_for(self, element_name: str) -> list[Constraint]:
        """All constraints involving a specific element."""
        return [c for c in self.constraints
                if c.source == element_name or c.target == element_name]

    def dependency_count(self, element_name: str) -> int:
        """How many ordering constraints reference this element."""
        ordering = {ConstraintType.SUCCESSION, ConstraintType.PRECEDENCE,
                     ConstraintType.RESPONSE}
        return sum(1 for c in self.constraints
                   if c.constraint_type in ordering
                   and (c.source == element_name or c.target == element_name))

    def to_signal_all(self) -> list[str]:
        """Return SIGNAL formulas for all constraints."""
        return [c.to_signal() for c in self.constraints]

    def to_ltlf_all(self) -> list[str]:
        """Return LTLf formulas for all constraints."""
        return [c.to_ltlf() for c in self.constraints]

    def to_dict(self) -> dict:
        """Returns JSON-compatible dict with keys:
        process_name, total_elements, total_tasks, constraints
        (list of {type, source, target, description}),
        max_gateway_depth, deeply_nested."""
        return {
            "process_name": self.process_name,
            "total_elements": self.total_elements,
            "total_tasks": self.total_tasks,
            "constraints": [
                {
                    "type": c.constraint_type.value,
                    "source": c.source,
                    "target": c.target,
                    "description": c.description,
                }
                for c in self.constraints
            ],
            "max_gateway_depth": self.max_gateway_depth,
            "deeply_nested": self.deeply_nested,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConstraintProfile":
        """Reconstructs from dict. Raises ValueError for missing keys
        or unrecognized constraint types."""
        required_keys = {"process_name", "total_elements", "total_tasks",
                         "constraints", "max_gateway_depth"}
        missing = required_keys - set(data.keys())
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(sorted(missing))}")

        # Build a lookup for valid constraint type values
        valid_types = {ct.value: ct for ct in ConstraintType}

        constraints = []
        for entry in data["constraints"]:
            type_str = entry.get("type", "")
            if type_str not in valid_types:
                raise ValueError(
                    f"Unrecognized constraint type: '{type_str}'"
                )
            constraints.append(Constraint(
                constraint_type=valid_types[type_str],
                source=entry.get("source", ""),
                target=entry.get("target", ""),
                description=entry.get("description", ""),
            ))

        return cls(
            process_name=data["process_name"],
            constraints=constraints,
            total_elements=data["total_elements"],
            total_tasks=data["total_tasks"],
            max_gateway_depth=data["max_gateway_depth"],
            deeply_nested=data.get("deeply_nested", data["max_gateway_depth"] >= 4),
        )


# ─── Gateway helpers ──────────────────────────────────────────────────────────

GATEWAY_TYPES = {
    ElementType.EXCLUSIVE_GATEWAY,
    ElementType.PARALLEL_GATEWAY,
    ElementType.INCLUSIVE_GATEWAY,
}

TASK_TYPES = {
    ElementType.TASK,
    ElementType.SERVICE_TASK,
    ElementType.USER_TASK,
    ElementType.SCRIPT_TASK,
    ElementType.BUSINESS_RULE_TASK,
    ElementType.SUBPROCESS,
}

EVENT_TYPES = {
    ElementType.START_EVENT,
    ElementType.END_EVENT,
    ElementType.TIMER_EVENT,
}


def _label(elem: ProcessElement) -> str:
    """Get a human-readable label for an element."""
    return elem.name if elem.name else elem.id


def _is_task(elem: ProcessElement) -> bool:
    return elem.element_type in TASK_TYPES


def _is_gateway(elem: ProcessElement) -> bool:
    return elem.element_type in GATEWAY_TYPES


def _resolve_successors(
    elem: ProcessElement,
    bpmn: BPMNProcess,
    visited: set[str] | None = None,
) -> list[ProcessElement]:
    """
    Get the task-level successors of an element, skipping through gateways.
    If the direct successor is a gateway, follow its outgoing flows to find
    the actual task successors.  Uses a visited set to handle gateway cycles.
    """
    if visited is None:
        visited = set()
    if elem.id in visited:
        return []
    visited.add(elem.id)

    result = []
    for flow_id in elem.outgoing:
        flow = bpmn.flows.get(flow_id)
        if not flow:
            continue
        target = bpmn.elements.get(flow.target_ref)
        if not target:
            continue
        if _is_task(target):
            result.append(target)
        elif _is_gateway(target):
            # Recurse through gateway with cycle detection
            result.extend(_resolve_successors(target, bpmn, visited))
        elif target.element_type == ElementType.END_EVENT:
            result.append(target)
    return result


def _resolve_predecessors(
    elem: ProcessElement,
    bpmn: BPMNProcess,
    visited: set[str] | None = None,
) -> list[ProcessElement]:
    """Get task-level predecessors, skipping through gateways with cycle detection."""
    if visited is None:
        visited = set()
    if elem.id in visited:
        return []
    visited.add(elem.id)

    result = []
    for flow_id in elem.incoming:
        flow = bpmn.flows.get(flow_id)
        if not flow:
            continue
        source = bpmn.elements.get(flow.source_ref)
        if not source:
            continue
        if _is_task(source):
            result.append(source)
        elif _is_gateway(source):
            result.extend(_resolve_predecessors(source, bpmn, visited))
        elif source.element_type == ElementType.START_EVENT:
            result.append(source)
    return result


def _gateway_task_successors(
    gateway: ProcessElement,
    bpmn: BPMNProcess,
    visited: set[str] | None = None,
) -> list[ProcessElement]:
    """Get the immediate task successors of a gateway (recursive through nested gateways, cycle-safe)."""
    if visited is None:
        visited = set()
    if gateway.id in visited:
        return []
    visited.add(gateway.id)

    result = []
    for flow_id in gateway.outgoing:
        flow = bpmn.flows.get(flow_id)
        if not flow:
            continue
        target = bpmn.elements.get(flow.target_ref)
        if not target:
            continue
        if _is_task(target):
            result.append(target)
        elif _is_gateway(target):
            result.extend(_gateway_task_successors(target, bpmn, visited))
    return result


def _gateway_task_predecessors(
    gateway: ProcessElement,
    bpmn: BPMNProcess,
    visited: set[str] | None = None,
) -> list[ProcessElement]:
    """Get the immediate task predecessors of a gateway (cycle-safe)."""
    if visited is None:
        visited = set()
    if gateway.id in visited:
        return []
    visited.add(gateway.id)

    result = []
    for flow_id in gateway.incoming:
        flow = bpmn.flows.get(flow_id)
        if not flow:
            continue
        source = bpmn.elements.get(flow.source_ref)
        if not source:
            continue
        if _is_task(source):
            result.append(source)
        elif _is_gateway(source):
            result.extend(_gateway_task_predecessors(source, bpmn, visited))
    return result


# ─── New extraction algorithms ────────────────────────────────────────────────

def _get_direct_successor(elem: ProcessElement, bpmn: BPMNProcess) -> ProcessElement | None:
    """Get the single direct successor element (task or gateway) via sequence flow."""
    if len(elem.outgoing) != 1:
        return None
    flow = bpmn.flows.get(elem.outgoing[0])
    if not flow:
        return None
    return bpmn.elements.get(flow.target_ref)


def _get_direct_predecessor(elem: ProcessElement, bpmn: BPMNProcess) -> ProcessElement | None:
    """Get the single direct predecessor element (task or gateway) via sequence flow."""
    if len(elem.incoming) != 1:
        return None
    flow = bpmn.flows.get(elem.incoming[0])
    if not flow:
        return None
    return bpmn.elements.get(flow.source_ref)


def _extract_chain_successions(bpmn: BPMNProcess) -> list[Constraint]:
    """
    Walk consecutive sequence flows with no intervening gateways.
    For a linear chain A → B → C, emit chain_succession(A, B) and chain_succession(B, C).
    Also emits chain_precedence(A, B) and alternate_response(A, B) for each pair.
    """
    constraints = []
    visited_pairs: set[tuple[str, str]] = set()

    for elem in bpmn.elements.values():
        if not _is_task(elem):
            continue
        # Walk forward from this task through direct task-to-task links
        current = elem
        while True:
            successor = _get_direct_successor(current, bpmn)
            if not successor or not _is_task(successor):
                break
            # Check the predecessor also has a single incoming from current
            pred = _get_direct_predecessor(successor, bpmn)
            if not pred or pred.id != current.id:
                break
            src = _label(current)
            tgt = _label(successor)
            pair = (src, tgt)
            if pair not in visited_pairs:
                visited_pairs.add(pair)
                constraints.append(Constraint(
                    constraint_type=ConstraintType.CHAIN_SUCCESSION,
                    source=src, target=tgt,
                    description=f"{src} is immediately followed by {tgt} in a linear chain",
                ))
                constraints.append(Constraint(
                    constraint_type=ConstraintType.CHAIN_PRECEDENCE,
                    source=src, target=tgt,
                    description=f"{tgt} is immediately preceded by {src}",
                ))
                constraints.append(Constraint(
                    constraint_type=ConstraintType.ALTERNATE_RESPONSE,
                    source=src, target=tgt,
                    description=f"After {src}, {tgt} must happen before {src} recurs",
                ))
            current = successor
    return constraints


def _extract_responded_existence(bpmn: BPMNProcess) -> list[Constraint]:
    """
    For each parallel gateway with K >= 2 outgoing branches, find the first
    task on each branch and emit responded_existence(T1, T2) for all pairs.
    """
    constraints = []
    for elem in bpmn.elements.values():
        if elem.element_type != ElementType.PARALLEL_GATEWAY:
            continue
        if len(elem.outgoing) < 2:
            continue

        # Get the first task on each branch
        branch_first_tasks: list[ProcessElement] = []
        for flow_id in elem.outgoing:
            flow = bpmn.flows.get(flow_id)
            if not flow:
                continue
            target = bpmn.elements.get(flow.target_ref)
            if not target:
                continue
            if _is_task(target):
                branch_first_tasks.append(target)
            elif _is_gateway(target):
                # Follow through nested gateway to find first tasks
                nested_tasks = _gateway_task_successors(target, bpmn)
                if nested_tasks:
                    branch_first_tasks.append(nested_tasks[0])

        # Emit responded_existence for all pairs
        for a, b in combinations(branch_first_tasks, 2):
            la, lb = _label(a), _label(b)
            constraints.append(Constraint(
                constraint_type=ConstraintType.RESPONDED_EXISTENCE,
                source=la, target=lb,
                description=f"If {la} occurs then {lb} must also occur (parallel branches)",
            ))
    return constraints


def _compute_gateway_depth(bpmn: BPMNProcess) -> int:
    """
    Compute the maximum gateway nesting depth via BFS with visited-set cycle detection.
    A gateway nested inside another gateway's branch increases the depth.
    """
    if not bpmn.elements:
        return 0

    # Build a map: for each gateway, which gateways are directly reachable
    # from its outgoing flows (one hop, possibly through tasks)
    gateway_ids = [
        eid for eid, e in bpmn.elements.items() if _is_gateway(e)
    ]
    if not gateway_ids:
        return 0

    # For each gateway, find child gateways reachable from its outgoing flows
    # (before hitting another gateway's join)
    def _direct_child_gateways(gw_id: str) -> list[str]:
        """Find gateways directly reachable from a gateway's outgoing flows."""
        gw = bpmn.elements[gw_id]
        children = []
        queue = deque[str]()
        visited_local: set[str] = {gw_id}

        for flow_id in gw.outgoing:
            flow = bpmn.flows.get(flow_id)
            if flow and flow.target_ref != gw_id:
                queue.append(flow.target_ref)

        while queue:
            elem_id = queue.popleft()
            if elem_id in visited_local:
                continue
            visited_local.add(elem_id)

            elem = bpmn.elements.get(elem_id)
            if not elem:
                continue

            if _is_gateway(elem):
                children.append(elem_id)
                # Don't traverse through this gateway — it's a child
                continue

            # For tasks/events, continue following outgoing flows
            for flow_id in elem.outgoing:
                flow = bpmn.flows.get(flow_id)
                if flow and flow.target_ref not in visited_local:
                    queue.append(flow.target_ref)

        return children

    # Build parent→children adjacency for gateways
    children_map: dict[str, list[str]] = {}
    for gw_id in gateway_ids:
        children_map[gw_id] = _direct_child_gateways(gw_id)

    # BFS/DFS to find max depth from any root gateway
    max_depth = 0

    def _dfs_depth(gw_id: str, visited: set[str]) -> int:
        if gw_id in visited:
            return 0
        visited.add(gw_id)
        depth = 1
        max_child_depth = 0
        for child_id in children_map.get(gw_id, []):
            child_depth = _dfs_depth(child_id, visited)
            max_child_depth = max(max_child_depth, child_depth)
        # Remove from visited to allow other paths (but keep cycle detection)
        return depth + max_child_depth

    # Find root gateways (gateways not nested inside another gateway)
    nested_gateways: set[str] = set()
    for gw_id, children in children_map.items():
        for child in children:
            nested_gateways.add(child)

    root_gateways = [gw_id for gw_id in gateway_ids if gw_id not in nested_gateways]
    # If all gateways are nested (cycle), use all as potential roots
    if not root_gateways:
        root_gateways = gateway_ids

    for root_id in root_gateways:
        visited: set[str] = set()
        depth = _dfs_depth(root_id, visited)
        max_depth = max(max_depth, depth)

    return max_depth


# ─── Main Extraction ──────────────────────────────────────────────────────────

def extract_constraints(bpmn: BPMNProcess) -> ConstraintProfile:
    """
    Extract declarative constraints from a BPMN process.

    Walks the process graph and produces constraints based on:
    - Sequential flows → succession, co_existence
    - Gateways → exclusive_choice, choice, not_coexistence, co_existence
    - Start/end positions → init, end
    - Gateway joins → response, precedence
    """
    profile = ConstraintProfile(
        process_name=bpmn.name or bpmn.id,
        total_elements=len(bpmn.elements),
        total_tasks=sum(1 for e in bpmn.elements.values() if _is_task(e)),
    )

    constraints = []

    # ── Init constraints (first tasks after start) ──
    for start_id in bpmn.start_events:
        start_elem = bpmn.elements.get(start_id)
        if not start_elem:
            continue
        first_tasks = _resolve_successors(start_elem, bpmn)
        for task in first_tasks:
            if _is_task(task):
                constraints.append(Constraint(
                    constraint_type=ConstraintType.INIT,
                    source=_label(task),
                    description=f"Process starts with {_label(task)}",
                ))

    # ── End constraints (last tasks before end) ──
    for end_id in bpmn.end_events:
        end_elem = bpmn.elements.get(end_id)
        if not end_elem:
            continue
        last_tasks = _resolve_predecessors(end_elem, bpmn)
        for task in last_tasks:
            if _is_task(task):
                constraints.append(Constraint(
                    constraint_type=ConstraintType.END,
                    source=_label(task),
                    description=f"Process can end with {_label(task)}",
                ))

    # ── Task-level succession and co-existence ──
    for elem in bpmn.elements.values():
        if not _is_task(elem):
            continue
        successors = _resolve_successors(elem, bpmn)
        for succ in successors:
            if not _is_task(succ):
                continue
            src = _label(elem)
            tgt = _label(succ)
            constraints.append(Constraint(
                constraint_type=ConstraintType.SUCCESSION,
                source=src, target=tgt,
                description=f"{src} is directly followed by {tgt}",
            ))
            constraints.append(Constraint(
                constraint_type=ConstraintType.CO_EXISTENCE,
                source=src, target=tgt,
                description=f"{src} and {tgt} always co-occur",
            ))
    # ── Gateway constraints ──
    for elem in bpmn.elements.values():
        if not _is_gateway(elem):
            continue

        is_splitting = len(elem.outgoing) > 1
        is_joining = len(elem.incoming) > 1

        if is_splitting:
            branch_tasks = _gateway_task_successors(elem, bpmn)
            predecessor_tasks = _gateway_task_predecessors(elem, bpmn)

            if elem.element_type == ElementType.EXCLUSIVE_GATEWAY:
                # XOR: exactly one branch executes
                for a, b in combinations(branch_tasks, 2):
                    la, lb = _label(a), _label(b)
                    constraints.append(Constraint(
                        constraint_type=ConstraintType.EXCLUSIVE_CHOICE,
                        source=la, target=lb,
                        description=f"Exactly one of {la} or {lb} (XOR)",
                    ))
                    constraints.append(Constraint(
                        constraint_type=ConstraintType.NOT_COEXISTENCE,
                        source=la, target=lb,
                        description=f"{la} and {lb} never both occur",
                    ))
                    constraints.append(Constraint(
                        constraint_type=ConstraintType.CHOICE,
                        source=la, target=lb,
                        description=f"At least one of {la} or {lb}",
                    ))

            elif elem.element_type == ElementType.PARALLEL_GATEWAY:
                # AND: all branches execute
                for a, b in combinations(branch_tasks, 2):
                    la, lb = _label(a), _label(b)
                    constraints.append(Constraint(
                        constraint_type=ConstraintType.CO_EXISTENCE,
                        source=la, target=lb,
                        description=f"{la} and {lb} always co-occur (parallel)",
                    ))

            elif elem.element_type == ElementType.INCLUSIVE_GATEWAY:
                # OR: at least one branch
                for a, b in combinations(branch_tasks, 2):
                    la, lb = _label(a), _label(b)
                    constraints.append(Constraint(
                        constraint_type=ConstraintType.CHOICE,
                        source=la, target=lb,
                        description=f"At least one of {la} or {lb} (inclusive)",
                    ))

            # Precedence: predecessors of gateway precede all branch tasks
            for pred in predecessor_tasks:
                for succ in branch_tasks:
                    lp, ls = _label(pred), _label(succ)
                    constraints.append(Constraint(
                        constraint_type=ConstraintType.PRECEDENCE,
                        source=lp, target=ls,
                        description=f"{lp} must precede {ls}",
                    ))

        if is_joining:
            # Response: all predecessors respond to successors
            join_preds = _gateway_task_predecessors(elem, bpmn)
            join_succs = _gateway_task_successors(elem, bpmn)
            for pred in join_preds:
                for succ in join_succs:
                    if not _is_task(succ):
                        continue
                    lp, ls = _label(pred), _label(succ)
                    constraints.append(Constraint(
                        constraint_type=ConstraintType.RESPONSE,
                        source=lp, target=ls,
                        description=f"After {lp}, {ls} must eventually happen",
                    ))

    # ── Chain succession constraints (linear task chains) ──
    constraints.extend(_extract_chain_successions(bpmn))

    # ── Responded existence from parallel gateways ──
    constraints.extend(_extract_responded_existence(bpmn))

    # ── Gateway depth computation ──
    gateway_depth = _compute_gateway_depth(bpmn)
    profile.max_gateway_depth = gateway_depth
    profile.deeply_nested = gateway_depth >= 4

    # Deduplicate
    seen = set()
    unique = []
    for c in constraints:
        key = (c.constraint_type, c.source, c.target)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    profile.constraints = unique
    return profile
