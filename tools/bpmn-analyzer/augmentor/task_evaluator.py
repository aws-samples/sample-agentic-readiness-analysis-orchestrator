"""
Task Evaluator — Analyzes individual BPMN tasks and scores them
for AI agent replacement suitability.

Instead of migrating the entire process, this evaluates which tasks
benefit most from being replaced by an AI agent while the BPM engine
continues to orchestrate the overall flow.

Scoring dimensions:
  - AI Benefit:  How much does AI improve this task vs deterministic code?
  - Complexity:  How complex is the task (simple API call vs judgment)?
  - Risk:        What's the risk of AI making a wrong decision here?
  - Effort:      How much effort to build the agent connector?
"""
from dataclasses import dataclass, field
from enum import Enum
from parser.bpmn_parser import BPMNProcess, ProcessElement, ElementType
from analyzer.constraint_extractor import ConstraintProfile, ConstraintType


class ReplacementVerdict(Enum):
    STRONG_CANDIDATE = "strong_candidate"     # High AI benefit, manageable risk
    GOOD_CANDIDATE = "good_candidate"         # Moderate benefit, worth exploring
    KEEP_AS_IS = "keep_as_is"                 # Low benefit or too risky
    HUMAN_REQUIRED = "human_required"         # Genuinely needs a human (for now)


class MigrationType(Enum):
    """Classification of a task for migration planning."""
    AGENT = "agent"                   # Needs LLM reasoning
    SERVICE = "service"               # Deterministic API call
    HUMAN_REQUIRED = "human_required" # Needs human judgment


@dataclass
class TaskScore:
    """Scores for a single BPMN task."""
    ai_benefit: float = 0.0    # 0-1: how much AI improves over current impl
    complexity: float = 0.0    # 0-1: task complexity (higher = more complex)
    risk: float = 0.0          # 0-1: risk of AI error (higher = riskier)
    effort: float = 0.0        # 0-1: integration effort (higher = harder)

    @property
    def composite(self) -> float:
        """Weighted composite: high benefit + low risk = good candidate."""
        return (
            0.40 * self.ai_benefit
            + 0.15 * self.complexity
            - 0.30 * self.risk
            - 0.15 * self.effort
        )


@dataclass
class CostEstimate:
    """Per-task LLM cost projection."""
    estimated_tokens_per_invocation: int
    recommended_model: str          # key from MODEL_PRICING
    cost_per_1k_invocations_usd: float  # rounded to 2 decimal places


# ─── Cost Configuration (Req 5.4) ────────────────────────────────────────────

MODEL_PRICING = {
    "haiku-3.5":  {"input_per_1m": 0.80, "output_per_1m": 4.00},
    "sonnet-4":   {"input_per_1m": 3.00, "output_per_1m": 15.00},
    "sonnet-4.6": {"input_per_1m": 3.00, "output_per_1m": 15.00},
}

COST_DOWNGRADE_THRESHOLD = 5.00  # USD per 1k invocations, configurable


@dataclass
class TaskEvaluation:
    """Evaluation result for a single BPMN task."""
    element_id: str
    element_name: str
    element_type: str
    score: TaskScore
    verdict: ReplacementVerdict
    reasoning: str
    agent_description: str = ""       # what the replacement agent would do
    service_description: str = ""     # populated when migration_type == SERVICE
    integration_approach: str = ""    # how to connect BPM ↔ Agent
    prerequisites: list[str] = field(default_factory=list)
    migration_type: MigrationType = MigrationType.AGENT
    cost_estimate: CostEstimate | None = None
    cost_override_reason: str = ""


@dataclass
class AugmentationPlan:
    """Complete plan for which tasks to replace with agents."""
    process_name: str
    total_tasks: int
    evaluations: list[TaskEvaluation] = field(default_factory=list)
    recommended_order: list[str] = field(default_factory=list)  # element IDs in priority order
    summary: str = ""
    agent_count: int = 0
    service_count: int = 0
    human_count: int = 0
    total_estimated_monthly_cost_usd: float = 0.0


# ─── Heuristic Scoring ────────────────────────────────────────────────────────

# Keywords that signal high AI benefit
AI_BENEFIT_SIGNALS = {
    "high": [
        "review", "assess", "evaluate", "analyze", "interpret", "classify",
        "recommend", "summarize", "extract", "understand", "validate",
        "check", "verify", "decision", "approve", "reject", "triage",
        "communicate", "notify", "draft", "compose", "personalize",
    ],
    "low": [
        "send", "store", "save", "log", "record", "transfer", "copy",
        "delete", "archive", "move", "update status",
    ],
}

# Keywords that signal high risk
RISK_SIGNALS = [
    "approve", "reject", "financial", "payment", "transfer funds",
    "legal", "compliance", "regulatory", "sign", "commit", "execute",
    "irreversible",
]

# ─── Classification Keywords (Req 4.2, 4.3) ──────────────────────────────────

REASONING_KEYWORDS = [
    "review", "assess", "evaluate", "analyze", "interpret", "classify",
    "recommend", "decision",
]

MECHANICAL_KEYWORDS = [
    "send", "store", "save", "log", "record", "transfer", "copy", "create",
]


def evaluate_tasks(
    process: BPMNProcess,
    constraint_profile: ConstraintProfile | None = None,
    daily_volume: int = 100,
) -> AugmentationPlan:
    """
    Evaluate all tasks in a BPMN process for agent replacement suitability.
    When a constraint profile is provided, uses structural position data
    to refine risk and complexity scores.

    Classifies each task as agent/service/human_required, computes cost
    estimates for agents, and applies constraint-driven score refinements.
    """
    evaluations = []

    # Only evaluate tasks (not gateways, events)
    task_types = {
        ElementType.TASK,
        ElementType.SERVICE_TASK,
        ElementType.USER_TASK,
        ElementType.SCRIPT_TASK,
        ElementType.BUSINESS_RULE_TASK,
        ElementType.SUBPROCESS,
    }

    # Also include generic tasks (parsed as SERVICE_TASK or similar)
    for elem_id, elem in process.elements.items():
        if elem.element_type not in task_types:
            # Check if it's a generic <task> element (Kogito uses these)
            if elem.element_type.value not in ("startEvent", "endEvent",
                                                 "exclusiveGateway",
                                                 "parallelGateway",
                                                 "inclusiveGateway",
                                                 "intermediateCatchEvent"):
                task_types.add(elem.element_type)

    tasks = [e for e in process.elements.values() if e.element_type in task_types]

    for task in tasks:
        evaluation = _evaluate_single_task(task, process, constraint_profile)
        evaluations.append(evaluation)

    # Sort by composite score (best candidates first)
    evaluations.sort(key=lambda e: e.score.composite, reverse=True)

    # Build recommended order (only candidates, not keep_as_is)
    recommended = [
        e.element_id for e in evaluations
        if e.verdict in (ReplacementVerdict.STRONG_CANDIDATE,
                         ReplacementVerdict.GOOD_CANDIDATE)
    ]

    strong = sum(1 for e in evaluations if e.verdict == ReplacementVerdict.STRONG_CANDIDATE)
    good = sum(1 for e in evaluations if e.verdict == ReplacementVerdict.GOOD_CANDIDATE)
    keep = sum(1 for e in evaluations if e.verdict == ReplacementVerdict.KEEP_AS_IS)
    human = sum(1 for e in evaluations if e.verdict == ReplacementVerdict.HUMAN_REQUIRED)

    # Count by migration type (Req 4.6)
    agent_count = sum(1 for e in evaluations if e.migration_type == MigrationType.AGENT)
    service_count = sum(1 for e in evaluations if e.migration_type == MigrationType.SERVICE)
    human_count = sum(1 for e in evaluations if e.migration_type == MigrationType.HUMAN_REQUIRED)

    # Compute total monthly cost (Req 5.6)
    total_monthly = 0.0
    for e in evaluations:
        if e.migration_type == MigrationType.AGENT and e.cost_estimate:
            total_monthly += e.cost_estimate.cost_per_1k_invocations_usd * daily_volume / 1000 * 30

    summary = (
        f"Evaluated {len(tasks)} tasks: "
        f"{strong} strong candidates, {good} good candidates, "
        f"{keep} keep as-is, {human} human-required. "
        f"Migration: {agent_count} agents, {service_count} services, {human_count} human. "
        f"Recommended replacement order: {', '.join(recommended) if recommended else 'none'}."
    )

    return AugmentationPlan(
        process_name=process.name or process.id,
        total_tasks=len(tasks),
        evaluations=evaluations,
        recommended_order=recommended,
        summary=summary,
        agent_count=agent_count,
        service_count=service_count,
        human_count=human_count,
        total_estimated_monthly_cost_usd=round(total_monthly, 2),
    )


def _evaluate_single_task(
    task: ProcessElement,
    process: BPMNProcess,
    constraint_profile: ConstraintProfile | None = None,
) -> TaskEvaluation:
    """Score and evaluate a single task for agent replacement."""
    name_lower = (task.name or task.id).lower()
    task_label = task.name if task.name else task.id

    # --- AI Benefit ---
    ai_benefit = 0.3  # baseline
    for keyword in AI_BENEFIT_SIGNALS["high"]:
        if keyword in name_lower:
            ai_benefit = min(1.0, ai_benefit + 0.15)
    for keyword in AI_BENEFIT_SIGNALS["low"]:
        if keyword in name_lower:
            ai_benefit = max(0.0, ai_benefit - 0.15)

    # User tasks get a boost (replacing human work with AI)
    if task.element_type == ElementType.USER_TASK:
        ai_benefit = min(1.0, ai_benefit + 0.25)
    # Business rule tasks: AI can handle complex rules
    if task.element_type == ElementType.BUSINESS_RULE_TASK:
        ai_benefit = min(1.0, ai_benefit + 0.2)

    # --- Complexity ---
    complexity = 0.3
    # More connections = more complex context
    n_incoming = len(task.incoming)
    n_outgoing = len(task.outgoing)
    if n_incoming > 1 or n_outgoing > 1:
        complexity = min(1.0, complexity + 0.2)
    # Subprocesses are inherently complex
    if task.element_type == ElementType.SUBPROCESS:
        complexity = min(1.0, complexity + 0.3)

    # --- Risk ---
    risk = 0.2  # baseline
    for keyword in RISK_SIGNALS:
        if keyword in name_lower:
            risk = min(1.0, risk + 0.15)
    # User tasks that are approval gates are high risk
    if task.element_type == ElementType.USER_TASK and "approv" in name_lower:
        risk = min(1.0, risk + 0.2)

    # --- Effort ---
    effort = 0.3  # baseline
    if task.element_type == ElementType.SERVICE_TASK:
        effort = 0.2  # easiest: just swap the endpoint
    elif task.element_type == ElementType.USER_TASK:
        effort = 0.5  # need to handle human-in-the-loop
    elif task.element_type == ElementType.SUBPROCESS:
        effort = 0.7  # complex: need to replace entire sub-flow

    # --- Constraint-based refinements (existing) ---
    if constraint_profile:
        dep_count = constraint_profile.dependency_count(task_label)
        task_constraints = constraint_profile.constraints_for(task_label)

        # High dependency count → this task is structurally critical
        # More things depend on it = higher risk if AI gets it wrong
        if dep_count >= 4:
            risk = min(1.0, risk + 0.15)
            complexity = min(1.0, complexity + 0.1)
        elif dep_count >= 2:
            risk = min(1.0, risk + 0.08)

        # If task is in exclusive_choice or not_coexistence constraints,
        # it's on a conditional branch — risk is somewhat contained
        has_exclusion = any(
            c.constraint_type in (ConstraintType.EXCLUSIVE_CHOICE,
                                   ConstraintType.NOT_COEXISTENCE)
            for c in task_constraints
        )
        if has_exclusion:
            # Conditional branch = isolated impact, slightly lower risk
            risk = max(0.0, risk - 0.05)

        # If task has many precedence constraints (things must happen before it),
        # it has rich context available → AI can make better decisions
        n_preceded_by = sum(
            1 for c in task_constraints
            if c.constraint_type == ConstraintType.PRECEDENCE and c.target == task_label
        )
        if n_preceded_by >= 2:
            ai_benefit = min(1.0, ai_benefit + 0.1)

        # If task is an INIT task (first in process), effort is lower
        # because there's no upstream context to integrate
        is_init = any(
            c.constraint_type == ConstraintType.INIT and c.source == task_label
            for c in task_constraints
        )
        if is_init:
            effort = max(0.0, effort - 0.1)

        # --- Constraint-driven score refinements (Req 4.7) ---
        ai_benefit, complexity, risk = _apply_constraint_refinements(
            task_label, ai_benefit, complexity, risk, constraint_profile,
        )

    score = TaskScore(
        ai_benefit=round(ai_benefit, 2),
        complexity=round(complexity, 2),
        risk=round(risk, 2),
        effort=round(effort, 2),
    )

    # Determine verdict
    composite = score.composite
    if composite >= 0.25:
        verdict = ReplacementVerdict.STRONG_CANDIDATE
    elif composite >= 0.10:
        verdict = ReplacementVerdict.GOOD_CANDIDATE
    elif task.element_type == ElementType.USER_TASK and risk > 0.6:
        verdict = ReplacementVerdict.HUMAN_REQUIRED
    else:
        verdict = ReplacementVerdict.KEEP_AS_IS

    # --- Classification (Req 4.1–4.4) ---
    migration_type = _classify_task(task, score)

    # --- Cost estimation for agents (Req 5.1–5.3) ---
    cost_estimate = None
    cost_override_reason = ""
    if migration_type == MigrationType.AGENT:
        cost_estimate = _estimate_cost(task, score)
        # Cost-based downgrade (Req 5.5)
        if cost_estimate.cost_per_1k_invocations_usd > COST_DOWNGRADE_THRESHOLD:
            migration_type = MigrationType.SERVICE
            cost_override_reason = (
                f"Downgraded from agent to service: cost ${cost_estimate.cost_per_1k_invocations_usd:.2f}/1k "
                f"exceeds threshold ${COST_DOWNGRADE_THRESHOLD:.2f}/1k"
            )

    # Build descriptions
    reasoning = _build_reasoning(task, score, verdict)
    if cost_override_reason:
        reasoning += f" [{cost_override_reason}]"

    agent_desc = ""
    service_desc = ""
    if migration_type == MigrationType.SERVICE:
        service_desc = _build_service_description(task)
    else:
        agent_desc = _build_agent_description(task)

    integration = _build_integration_approach(task)
    prereqs = _build_prerequisites(task, score)

    return TaskEvaluation(
        element_id=task.id,
        element_name=task.name or task.id,
        element_type=task.element_type.value,
        score=score,
        verdict=verdict,
        reasoning=reasoning,
        agent_description=agent_desc,
        service_description=service_desc,
        integration_approach=integration,
        prerequisites=prereqs,
        migration_type=migration_type,
        cost_estimate=cost_estimate,
        cost_override_reason=cost_override_reason,
    )


def _classify_task(task: ProcessElement, score: TaskScore) -> MigrationType:
    """
    Classification rules (Req 4.1–4.4):
      - "human_required" when userTask AND risk > 0.6
      - "agent" when ai_benefit >= 0.4 AND reasoning keywords present
      - "service" when ai_benefit < 0.4 OR mechanical keywords only
    """
    name_lower = (task.name or task.id).lower()

    # Check human_required first (Req 4.4)
    if task.element_type == ElementType.USER_TASK and score.risk > 0.6:
        return MigrationType.HUMAN_REQUIRED

    # Check for reasoning keywords (Req 4.2)
    has_reasoning = any(kw in name_lower for kw in REASONING_KEYWORDS)
    # Check for mechanical keywords (Req 4.3)
    has_mechanical = any(kw in name_lower for kw in MECHANICAL_KEYWORDS)

    if score.ai_benefit >= 0.4 and has_reasoning:
        return MigrationType.AGENT

    if score.ai_benefit < 0.4 or has_mechanical:
        return MigrationType.SERVICE

    # Default: if ai_benefit >= 0.4 but no reasoning keywords → service
    return MigrationType.SERVICE


def _estimate_cost(task: ProcessElement, score: TaskScore) -> CostEstimate:
    """
    Token estimation (Req 5.2):
      system_prompt(500) + input_context(200|500|1000 by complexity)
      + tool_calls(300 * expected_tools) + output(300)
    Model selection (Req 5.3):
      complexity < 0.4 → haiku-3.5
      0.4 <= complexity < 0.7 → sonnet-4
      complexity >= 0.7 → sonnet-4.6
    """
    # Input context by complexity thresholds
    if score.complexity < 0.4:
        input_context = 200
    elif score.complexity < 0.7:
        input_context = 500
    else:
        input_context = 1000

    # Expected tools: estimate from outgoing connections
    expected_tools = max(1, len(task.outgoing))

    # Token formula
    tokens = 500 + input_context + (300 * expected_tools) + 300

    # Model selection
    if score.complexity < 0.4:
        model = "haiku-3.5"
    elif score.complexity < 0.7:
        model = "sonnet-4"
    else:
        model = "sonnet-4.6"

    # Cost calculation from MODEL_PRICING
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["sonnet-4.6"])
    # Assume ~60% input, ~40% output token split
    input_tokens = int(tokens * 0.6)
    output_tokens = tokens - input_tokens
    cost_per_invocation = (
        (input_tokens / 1_000_000) * pricing["input_per_1m"]
        + (output_tokens / 1_000_000) * pricing["output_per_1m"]
    )
    cost_per_1k = round(cost_per_invocation * 1000, 2)

    return CostEstimate(
        estimated_tokens_per_invocation=tokens,
        recommended_model=model,
        cost_per_1k_invocations_usd=cost_per_1k,
    )


def _apply_constraint_refinements(
    task_label: str,
    ai_benefit: float,
    complexity: float,
    risk: float,
    constraint_profile: ConstraintProfile,
) -> tuple[float, float, float]:
    """
    Constraint-driven score refinements (Req 4.7):
      - density > 0.15 → risk +0.10
      - 2+ CHAIN_SUCCESSION → complexity +0.10
      - EXCLUSIVE_CHOICE + NOT_COEXISTENCE → risk -0.05
      - 0 ordering constraints → ai_benefit +0.05
    All clamped to [0.0, 1.0].
    """
    task_constraints = constraint_profile.constraints_for(task_label)

    # Task-local constraint density
    if task_constraints:
        density = len(task_constraints) / max(constraint_profile.total_tasks, 1)
    else:
        density = 0.0

    # density > 0.15 → risk +0.10
    if density > 0.15:
        risk = min(1.0, risk + 0.10)

    # 2+ CHAIN_SUCCESSION → complexity +0.10
    chain_count = sum(
        1 for c in task_constraints
        if c.constraint_type == ConstraintType.CHAIN_SUCCESSION
    )
    if chain_count >= 2:
        complexity = min(1.0, complexity + 0.10)

    # EXCLUSIVE_CHOICE + NOT_COEXISTENCE → risk -0.05
    has_exclusive = any(
        c.constraint_type == ConstraintType.EXCLUSIVE_CHOICE for c in task_constraints
    )
    has_not_coexist = any(
        c.constraint_type == ConstraintType.NOT_COEXISTENCE for c in task_constraints
    )
    if has_exclusive and has_not_coexist:
        risk = max(0.0, risk - 0.05)

    # 0 ordering constraints → ai_benefit +0.05
    ordering_types = {ConstraintType.SUCCESSION, ConstraintType.PRECEDENCE,
                      ConstraintType.RESPONSE}
    ordering_count = sum(
        1 for c in task_constraints if c.constraint_type in ordering_types
    )
    if ordering_count == 0:
        ai_benefit = min(1.0, ai_benefit + 0.05)

    return ai_benefit, complexity, risk


def _build_service_description(task: ProcessElement) -> str:
    """Build a description for a task classified as a service (Req 4.5)."""
    name = task.name or task.id
    return (
        f"REST API wrapper for '{name}': deterministic endpoint that receives "
        f"process variables as JSON, executes the business logic, and returns "
        f"structured results. No LLM reasoning required."
    )


def _build_reasoning(task: ProcessElement, score: TaskScore, verdict: ReplacementVerdict) -> str:
    parts = []
    if score.ai_benefit >= 0.6:
        parts.append("High AI benefit — task involves judgment/analysis")
    elif score.ai_benefit >= 0.4:
        parts.append("Moderate AI benefit")
    else:
        parts.append("Low AI benefit — mostly mechanical/deterministic")

    if score.risk >= 0.5:
        parts.append("elevated risk (financial/approval decision)")
    if task.element_type == ElementType.USER_TASK:
        parts.append("currently requires human — AI could augment or replace")

    return f"{verdict.value}: {'; '.join(parts)}. Composite: {score.composite:.2f}"


def _build_agent_description(task: ProcessElement) -> str:
    name = task.name or task.id
    type_label = task.element_type.value
    if task.element_type == ElementType.USER_TASK:
        return (
            f"AI agent replaces human '{name}' task. "
            f"Agent receives the same inputs, applies reasoning, "
            f"and returns a decision. Human escalation for low-confidence cases."
        )
    elif task.element_type == ElementType.BUSINESS_RULE_TASK:
        return (
            f"AI agent replaces rule engine for '{name}'. "
            f"Can handle edge cases and nuance beyond static rules."
        )
    else:
        return (
            f"AI agent handles '{name}' ({type_label}). "
            f"Receives process variables, performs the task, returns results."
        )


def _build_integration_approach(task: ProcessElement) -> str:
    if task.element_type == ElementType.USER_TASK:
        return (
            "REST connector: BPM engine calls agent API endpoint instead of "
            "creating a human task. Agent returns decision + confidence. "
            "If confidence < threshold, fall back to human task queue."
        )
    elif task.element_type == ElementType.SERVICE_TASK:
        return (
            "REST connector: Replace the service task's endpoint URL with "
            "the agent's API Gateway endpoint. Agent receives process "
            "variables as JSON, returns result in expected format."
        )
    elif task.element_type == ElementType.BUSINESS_RULE_TASK:
        return (
            "REST connector: Replace DMN/Drools call with agent endpoint. "
            "Agent receives the decision inputs and returns the same "
            "output schema the BPM engine expects."
        )
    else:
        return (
            "REST connector: BPM engine calls agent endpoint via HTTP. "
            "Agent processes the request and returns structured JSON."
        )


def _build_prerequisites(task: ProcessElement, score: TaskScore) -> list[str]:
    prereqs = ["Deploy Strands agent on AgentCore or as REST API"]
    if score.risk >= 0.5:
        prereqs.append("Define guardrails and confidence thresholds")
        prereqs.append("Set up human fallback for low-confidence decisions")
    if task.element_type == ElementType.USER_TASK:
        prereqs.append("Map human task input/output to agent request/response schema")
        prereqs.append("Configure BPM connector to call REST instead of task queue")
    if score.ai_benefit >= 0.6:
        prereqs.append("Prepare training examples or few-shot prompts for the agent")
    return prereqs


# ─── LLM-Enhanced Evaluation Prompt ──────────────────────────────────────────

def build_task_evaluation_prompt(process: BPMNProcess) -> str:
    """Build a prompt for LLM-enhanced task-level evaluation."""
    tasks_text = ""
    for elem in process.elements.values():
        if elem.element_type.value in ("startEvent", "endEvent",
                                        "exclusiveGateway", "parallelGateway",
                                        "inclusiveGateway"):
            continue
        tasks_text += (
            f"  - [{elem.element_type.value}] {elem.name or elem.id} "
            f"(id: {elem.id})\n"
        )

    flows_text = ""
    for flow in process.flows.values():
        line = f"  - {flow.source_ref} → {flow.target_ref}"
        if flow.name:
            line += f" [{flow.name}]"
        if flow.condition:
            line += f" when: {flow.condition}"
        flows_text += line + "\n"

    return f"""Evaluate each task in this BPMN process for AI agent replacement.

The BPM engine STAYS as the orchestrator. We're replacing individual tasks
with AI agents — the BPM engine calls the agent via REST instead of running
the original implementation.

Process: {process.name or process.id}

Tasks:
{tasks_text}

Flows:
{flows_text}

For each task, evaluate:
1. AI Benefit (0-1): How much does AI improve this vs current implementation?
   - High: tasks involving judgment, analysis, interpretation, communication
   - Low: simple CRUD, data transfer, status updates

2. Risk (0-1): What's the risk if the AI makes a wrong decision?
   - High: financial approvals, legal compliance, irreversible actions
   - Low: notifications, data enrichment, classification

3. Integration Approach: How does the BPM engine connect to the agent?
   - REST connector (most common)
   - Async callback (for long-running agent tasks)
   - Event-driven (agent publishes result to message queue)

4. Recommended Order: Which tasks to replace first? Start with high-benefit,
   low-risk tasks to build confidence.

Return JSON:
{{
  "evaluations": [
    {{
      "element_id": "string",
      "element_name": "string",
      "ai_benefit": 0.0-1.0,
      "risk": 0.0-1.0,
      "verdict": "strong_candidate|good_candidate|keep_as_is|human_required",
      "reasoning": "string",
      "agent_description": "what the replacement agent does",
      "integration_approach": "how BPM connects to agent",
      "prerequisites": ["string"]
    }}
  ],
  "recommended_order": ["element_id in priority order"],
  "summary": "string"
}}"""
