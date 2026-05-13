"""
Pattern Evaluator — Evaluates process complexity and recommends
single or hybrid multi-agent patterns using Strands Agents SDK.

Strands supports nesting: a Graph node can be a Swarm, another Graph,
a custom FunctionNode, or an Agent-as-Tool orchestrator. This evaluator
scores each process region against pattern characteristics and recommends
hybrid compositions when no single pattern fits.
"""
from dataclasses import dataclass, field
from analyzer.process_analyzer import ProcessUnderstanding, DomainCluster
from analyzer.constraint_extractor import ConstraintProfile, ConstraintType


# ─── Scoring Signals ─────────────────────────────────────────────────────────

PATTERN_SIGNALS = {
    "graph": {
        "conditional_branching",
        "parallel_paths",
        "deterministic_flow",
        "gateway_heavy",
        "error_routing",
        "cyclic_review",
    },
    "swarm": {
        "exploratory",
        "collaborative",
        "exception_heavy",
        "adaptive_routing",
        "specialist_handoff",
        "investigation",
    },
    "workflow": {
        "sequential",
        "repeatable",
        "parallelizable_tasks",
        "batch_processing",
        "pipeline",
        "no_branching",
    },
    "agents_as_tools": {
        "llm_reasoning_needed",
        "dynamic_tool_selection",
        "complex_decision_logic",
        "unstructured_input",
        "multi_capability",
    },
}


@dataclass
class RegionEvaluation:
    """Evaluation of a single process region (domain cluster)."""
    domain: str
    description: str
    signals: list[str] = field(default_factory=list)
    scores: dict = field(default_factory=dict)  # pattern -> score
    recommended_pattern: str = "graph"
    reasoning: str = ""
    is_complex: bool = False  # needs its own sub-pattern


@dataclass
class HybridRecommendation:
    """A recommended hybrid pattern composition."""
    outer_pattern: str  # the top-level orchestration
    inner_patterns: dict = field(default_factory=dict)  # domain -> pattern
    nesting_map: list = field(default_factory=list)  # how they compose
    reasoning: str = ""


@dataclass
class PatternEvaluation:
    """Complete pattern evaluation result."""
    is_hybrid: bool = False
    primary_pattern: str = "graph"
    region_evaluations: list[RegionEvaluation] = field(default_factory=list)
    hybrid: HybridRecommendation = None
    complexity_score: float = 0.0  # 0-1, higher = more complex
    evaluation_summary: str = ""



# ─── Signal Detection ─────────────────────────────────────────────────────────

def _detect_signals(
    domain: DomainCluster,
    understanding: ProcessUnderstanding,
    constraint_profile: ConstraintProfile | None = None,
) -> list[str]:
    """
    Detect pattern signals from a domain cluster, its context, and
    structural constraints extracted from the BPMN topology.

    Two layers:
    1. Keyword heuristics (original) — from descriptions and capabilities
    2. Structural signals (new) — from formal constraints on domain elements
    """
    signals = []
    caps = " ".join(domain.capabilities).lower()
    desc = domain.description.lower()
    text = f"{caps} {desc}"

    # ── Layer 1: Keyword heuristics ───────────────────────────────────

    # Graph signals
    if any(w in text for w in ["route", "branch", "condition", "gateway", "if ", "check"]):
        signals.append("conditional_branching")
    if any(w in text for w in ["parallel", "concurrent", "simultaneous"]):
        signals.append("parallel_paths")
    if any(w in text for w in ["sequence", "step", "then", "after", "pipeline"]):
        signals.append("deterministic_flow")
    if any(w in text for w in ["error", "exception", "fallback", "retry"]):
        signals.append("error_routing")
    if any(w in text for w in ["review", "loop", "iterate", "revise", "feedback"]):
        signals.append("cyclic_review")

    # Swarm signals
    if any(w in text for w in ["investigate", "explore", "research", "discover"]):
        signals.append("exploratory")
        signals.append("investigation")
    if any(w in text for w in ["collaborate", "team", "discuss", "negotiate"]):
        signals.append("collaborative")
    if any(w in text for w in ["handoff", "transfer", "escalat", "delegate"]):
        signals.append("specialist_handoff")
    if any(w in text for w in ["adapt", "dynamic", "flexible", "situational"]):
        signals.append("adaptive_routing")
    if any(w in text for w in ["exception", "anomal", "unusual", "edge case"]):
        signals.append("exception_heavy")

    # Workflow signals
    if any(w in text for w in ["batch", "bulk", "mass", "process all"]):
        signals.append("batch_processing")
    if any(w in text for w in ["repeatable", "standard", "template", "routine"]):
        signals.append("repeatable")
    if any(w in text for w in ["independent", "no dependency", "standalone"]):
        signals.append("parallelizable_tasks")

    # Agents-as-Tools signals
    if any(w in text for w in ["reason", "judgment", "interpret", "understand"]):
        signals.append("llm_reasoning_needed")
    if any(w in text for w in ["unstructured", "free text", "natural language", "document"]):
        signals.append("unstructured_input")
    if any(w in text for w in ["select", "choose", "decide which", "pick"]):
        signals.append("dynamic_tool_selection")
    if len(domain.capabilities) > 4:
        signals.append("multi_capability")

    # Human involvement often signals complexity
    if domain.needs_human:
        signals.append("specialist_handoff")

    # ── Layer 2: Structural signals from constraints ──────────────────
    if constraint_profile:
        domain_elements = set(domain.elements)

        # Collect constraints that touch this domain's elements
        domain_constraints = [
            c for c in constraint_profile.constraints
            if c.source in domain_elements or c.target in domain_elements
        ]

        # Count constraint types for this domain
        n_succession = sum(1 for c in domain_constraints
                          if c.constraint_type == ConstraintType.SUCCESSION)
        n_precedence = sum(1 for c in domain_constraints
                          if c.constraint_type == ConstraintType.PRECEDENCE)
        n_exclusive = sum(1 for c in domain_constraints
                         if c.constraint_type == ConstraintType.EXCLUSIVE_CHOICE)
        n_not_coexist = sum(1 for c in domain_constraints
                           if c.constraint_type == ConstraintType.NOT_COEXISTENCE)
        n_coexist = sum(1 for c in domain_constraints
                        if c.constraint_type == ConstraintType.CO_EXISTENCE)
        n_response = sum(1 for c in domain_constraints
                         if c.constraint_type == ConstraintType.RESPONSE)
        n_choice = sum(1 for c in domain_constraints
                       if c.constraint_type == ConstraintType.CHOICE)

        # Strong ordering (succession + precedence) → graph signal
        if n_succession + n_precedence >= 2:
            signals.append("deterministic_flow")
            signals.append("conditional_branching")

        # Exclusive choices → graph (conditional edges)
        if n_exclusive >= 1:
            signals.append("conditional_branching")
            signals.append("gateway_heavy")

        # Not-coexistence → mutual exclusion paths (graph with XOR)
        if n_not_coexist >= 1:
            signals.append("conditional_branching")

        # High co-existence → parallel paths (graph or workflow)
        if n_coexist >= 2:
            signals.append("parallel_paths")
            signals.append("parallelizable_tasks")

        # Many response constraints → complex handoff chains
        if n_response >= 2:
            signals.append("specialist_handoff")

        # Choice without exclusion → inclusive/adaptive routing
        if n_choice >= 2 and n_exclusive == 0:
            signals.append("adaptive_routing")

        # High constraint density on few elements → complex decision logic
        domain_density = len(domain_constraints) / max(len(domain_elements), 1)
        if domain_density >= 3.0:
            signals.append("complex_decision_logic")
            signals.append("llm_reasoning_needed")

    return list(set(signals))


def _score_pattern(signals: list[str], pattern: str) -> float:
    """Score how well a set of signals matches a pattern (0-1)."""
    pattern_sigs = PATTERN_SIGNALS.get(pattern, set())
    if not pattern_sigs:
        return 0.0
    matches = len(set(signals) & pattern_sigs)
    return matches / len(pattern_sigs)


# ─── Evaluation Logic ─────────────────────────────────────────────────────────

def _apply_constraint_density_boosts(
    domain: DomainCluster,
    scores: dict[str, float],
    signals: list[str],
    constraint_profile: ConstraintProfile,
) -> tuple[dict[str, float], list[str], float]:
    """
    Apply constraint-density-based score boosts and signals for a domain.

    Returns (boosted_scores, updated_signals, domain_density).

    Rules:
      - density > 4.0 → "highly_constrained" signal, graph +0.1
      - 2+ EXCLUSIVE_CHOICE → "branching_heavy", graph +0.05
      - 0 ordering + 2+ CO_EXISTENCE → "loosely_coupled", swarm +0.1
      - 3+ CHAIN_SUCCESSION → "strict_pipeline", workflow +0.1
    All scores clamped to [0.0, 1.0].
    """
    domain_elements = set(domain.elements)

    # Collect constraints that touch this domain's elements
    domain_constraints = [
        c for c in constraint_profile.constraints
        if c.source in domain_elements or c.target in domain_elements
    ]

    domain_density = len(domain_constraints) / max(len(domain_elements), 1)

    # Count specific constraint types within domain constraints
    n_exclusive = sum(
        1 for c in domain_constraints
        if c.constraint_type == ConstraintType.EXCLUSIVE_CHOICE
    )
    n_ordering = sum(
        1 for c in domain_constraints
        if c.constraint_type in {
            ConstraintType.SUCCESSION,
            ConstraintType.PRECEDENCE,
            ConstraintType.RESPONSE,
        }
    )
    n_coexistence = sum(
        1 for c in domain_constraints
        if c.constraint_type == ConstraintType.CO_EXISTENCE
    )
    n_chain_succession = sum(
        1 for c in domain_constraints
        if c.constraint_type == ConstraintType.CHAIN_SUCCESSION
    )

    boosted = dict(scores)
    new_signals = list(signals)

    # Rule 1: density > 4.0 → "highly_constrained" + graph +0.1
    if domain_density > 4.0:
        if "highly_constrained" not in new_signals:
            new_signals.append("highly_constrained")
        boosted["graph"] = boosted.get("graph", 0.0) + 0.1

    # Rule 2: 2+ EXCLUSIVE_CHOICE → "branching_heavy" + graph +0.05
    if n_exclusive >= 2:
        if "branching_heavy" not in new_signals:
            new_signals.append("branching_heavy")
        boosted["graph"] = boosted.get("graph", 0.0) + 0.05

    # Rule 3: 0 ordering + 2+ CO_EXISTENCE → "loosely_coupled" + swarm +0.1
    if n_ordering == 0 and n_coexistence >= 2:
        if "loosely_coupled" not in new_signals:
            new_signals.append("loosely_coupled")
        boosted["swarm"] = boosted.get("swarm", 0.0) + 0.1

    # Rule 4: 3+ CHAIN_SUCCESSION → "strict_pipeline" + workflow +0.1
    if n_chain_succession >= 3:
        if "strict_pipeline" not in new_signals:
            new_signals.append("strict_pipeline")
        boosted["workflow"] = boosted.get("workflow", 0.0) + 0.1

    # Clamp all scores to [0.0, 1.0]
    for pattern in boosted:
        boosted[pattern] = round(min(1.0, max(0.0, boosted[pattern])), 3)

    return boosted, new_signals, domain_density


def evaluate_patterns(
    understanding: ProcessUnderstanding,
    constraint_profile: ConstraintProfile | None = None,
) -> PatternEvaluation:
    """
    Evaluate the process and recommend single or hybrid patterns.

    Strategy:
    1. Score each domain cluster against all 4 patterns
    2. Use structural constraints (if available) to boost signal accuracy
    3. If all domains agree on one pattern → single pattern
    4. If domains disagree → hybrid with nesting
    5. Compute overall complexity score grounded in constraint density
    """
    region_evals = []

    for domain in understanding.domains:
        signals = _detect_signals(domain, understanding, constraint_profile)
        scores = {}
        for pattern in PATTERN_SIGNALS:
            scores[pattern] = round(_score_pattern(signals, pattern), 3)

        # Apply constraint-density-based boosts when profile is available
        domain_density = None
        if constraint_profile is not None:
            scores, signals, domain_density = _apply_constraint_density_boosts(
                domain, scores, signals, constraint_profile,
            )

        best_pattern = max(scores, key=scores.get)
        best_score = scores[best_pattern]

        # A region is "complex" if its top two patterns are close in score
        sorted_scores = sorted(scores.values(), reverse=True)
        is_complex = (
            len(sorted_scores) >= 2
            and sorted_scores[0] > 0
            and sorted_scores[1] > 0
            and (sorted_scores[0] - sorted_scores[1]) < 0.15
        )

        reasoning = _explain_region(domain.name, best_pattern, scores, signals)
        # Append per-domain constraint density to reasoning (2 decimal places)
        if domain_density is not None:
            reasoning += f" Constraint density: {domain_density:.2f}."

        region_evals.append(RegionEvaluation(
            domain=domain.name,
            description=domain.description,
            signals=signals,
            scores=scores,
            recommended_pattern=best_pattern,
            reasoning=reasoning,
            is_complex=is_complex,
        ))

    # Determine if hybrid is needed
    unique_patterns = set(r.recommended_pattern for r in region_evals)
    has_complex_regions = any(r.is_complex for r in region_evals)

    # Complexity score: grounded in constraint density when available
    n_domains = len(understanding.domains)
    n_decisions = len(understanding.decision_points)
    n_integrations = len(understanding.integration_points)
    pattern_diversity = len(unique_patterns) / 4.0

    if constraint_profile:
        # Structural complexity from constraints
        density = constraint_profile.constraint_density
        exclusion_ratio = (
            constraint_profile.exclusion_constraints
            / max(constraint_profile.total_constraints, 1)
        )
        complexity = min(1.0, (
            0.15 * min(n_domains / 6, 1.0)
            + 0.15 * min(n_decisions / 5, 1.0)
            + 0.10 * min(n_integrations / 4, 1.0)
            + 0.25 * pattern_diversity
            + 0.20 * min(density / 5.0, 1.0)       # constraint density
            + 0.15 * min(exclusion_ratio * 3, 1.0)  # branching complexity
        ))
    else:
        complexity = min(1.0, (
            0.2 * min(n_domains / 6, 1.0)
            + 0.25 * min(n_decisions / 5, 1.0)
            + 0.15 * min(n_integrations / 4, 1.0)
            + 0.4 * pattern_diversity
        ))

    is_hybrid = len(unique_patterns) > 1 or has_complex_regions

    if is_hybrid:
        hybrid = _build_hybrid_recommendation(region_evals, understanding)
        primary = hybrid.outer_pattern
        summary = (
            f"Process complexity score: {complexity:.2f}/1.00. "
            f"Hybrid pattern recommended: {primary} outer with nested "
            f"{', '.join(set(hybrid.inner_patterns.values()))} patterns. "
            f"{hybrid.reasoning}"
        )
    else:
        hybrid = None
        primary = region_evals[0].recommended_pattern if region_evals else "graph"
        summary = (
            f"Process complexity score: {complexity:.2f}/1.00. "
            f"Single pattern sufficient: {primary}. "
            f"All {len(region_evals)} domains align on this pattern."
        )

    return PatternEvaluation(
        is_hybrid=is_hybrid,
        primary_pattern=primary,
        region_evaluations=region_evals,
        hybrid=hybrid,
        complexity_score=round(complexity, 3),
        evaluation_summary=summary,
    )


def _build_hybrid_recommendation(
    region_evals: list[RegionEvaluation],
    understanding: ProcessUnderstanding,
) -> HybridRecommendation:
    """Build a hybrid pattern recommendation with nesting strategy."""
    inner_patterns = {}
    for r in region_evals:
        inner_patterns[r.domain] = r.recommended_pattern

    # Determine outer pattern: Graph is the natural outer container
    # because it supports conditional edges and can nest Swarms/Graphs
    pattern_counts = {}
    for p in inner_patterns.values():
        pattern_counts[p] = pattern_counts.get(p, 0) + 1

    # If most regions are graph, use graph as outer
    # If most are swarm, still use graph as outer (swarm can't nest graphs)
    # Graph is almost always the best outer pattern for hybrid
    outer = "graph"

    # Build nesting map
    nesting = []
    for r in region_evals:
        if r.recommended_pattern == outer:
            nesting.append({
                "domain": r.domain,
                "node_type": "agent",
                "pattern": outer,
                "note": f"Direct {outer} node — {r.domain}",
            })
        else:
            nesting.append({
                "domain": r.domain,
                "node_type": "nested_pattern",
                "pattern": r.recommended_pattern,
                "note": (
                    f"Nested {r.recommended_pattern} inside {outer} — "
                    f"{r.domain} benefits from {r.recommended_pattern} "
                    f"because: {r.reasoning}"
                ),
            })

    # Build reasoning
    nested_patterns = [n for n in nesting if n["node_type"] == "nested_pattern"]
    if nested_patterns:
        nested_desc = "; ".join(
            f"{n['domain']} as {n['pattern']}" for n in nested_patterns
        )
        reasoning = (
            f"Graph as outer orchestrator with nested patterns: {nested_desc}. "
            f"Strands SDK supports this via GraphBuilder.add_node() which accepts "
            f"Swarm, Graph, or custom MultiAgentBase nodes."
        )
    else:
        reasoning = f"All regions fit {outer} pattern."

    return HybridRecommendation(
        outer_pattern=outer,
        inner_patterns=inner_patterns,
        nesting_map=nesting,
        reasoning=reasoning,
    )


def _explain_region(domain: str, pattern: str, scores: dict, signals: list[str]) -> str:
    """Generate a human-readable explanation for a region's pattern choice."""
    top_signals = [s for s in signals if s in PATTERN_SIGNALS.get(pattern, set())]
    runner_up = sorted(
        [(p, s) for p, s in scores.items() if p != pattern],
        key=lambda x: x[1],
        reverse=True,
    )
    runner_up_text = ""
    if runner_up and runner_up[0][1] > 0:
        runner_up_text = f" Runner-up: {runner_up[0][0]} ({runner_up[0][1]:.2f})."

    return (
        f"{domain} → {pattern} (score: {scores[pattern]:.2f}). "
        f"Key signals: {', '.join(top_signals) if top_signals else 'general fit'}."
        f"{runner_up_text}"
    )


# ─── LLM-Enhanced Evaluation Prompt ──────────────────────────────────────────

def build_evaluation_prompt(
    understanding: ProcessUnderstanding,
    constraint_profile: ConstraintProfile | None = None,
    heuristic_eval: PatternEvaluation | None = None,
) -> str:
    """
    Build a prompt for LLM-enhanced pattern evaluation.

    Includes:
    - Domain clusters and decision points from Step 2
    - Structural constraints from Step 1b (if available)
    - Heuristic evaluation results (if available) for the LLM to validate/override
    """
    domains_text = ""
    for d in understanding.domains:
        domains_text += f"""
  Domain: {d.name}
    Description: {d.description}
    Capabilities: {', '.join(d.capabilities)}
    Needs human: {d.needs_human}
    Elements: {', '.join(d.elements)}
"""

    decisions_text = "\n".join(
        f"  - {dp.get('element_id', '?')}: {dp.get('business_question', 'unknown')}"
        for dp in understanding.decision_points
    )

    # Constraints section
    constraints_text = ""
    if constraint_profile:
        constraints_text = f"""
STRUCTURAL CONSTRAINTS (formal facts from BPMN topology):
  Total: {constraint_profile.total_constraints} | Density: {constraint_profile.constraint_density:.2f}/element
  Ordering: {constraint_profile.ordering_constraints} | Exclusion: {constraint_profile.exclusion_constraints} | Co-existence: {constraint_profile.coexistence_constraints}

  Key constraints:
"""
        # Include the most informative constraints
        key_types = {"exclusive_choice", "not_coexistence", "precedence", "response"}
        for c in constraint_profile.constraints:
            if c.constraint_type.value in key_types:
                constraints_text += f"    [{c.constraint_type.value}] {c.description}\n"

    # Heuristic results section
    heuristic_text = ""
    if heuristic_eval:
        heuristic_text = f"""
HEURISTIC EVALUATION (our algorithm's initial assessment — validate or override):
  Complexity: {heuristic_eval.complexity_score:.2f}/1.00
  Primary pattern: {heuristic_eval.primary_pattern}
  Hybrid needed: {heuristic_eval.is_hybrid}

  Per-domain scores:
"""
        for r in heuristic_eval.region_evaluations:
            scores_str = ", ".join(f"{p}: {s:.2f}" for p, s in r.scores.items())
            heuristic_text += (
                f"    {r.domain} → {r.recommended_pattern} "
                f"(scores: {scores_str}) "
                f"signals: {', '.join(r.signals)}\n"
            )
        heuristic_text += f"""
  Review each domain's pattern assignment. Override if your understanding
  of the business logic suggests a different pattern is more appropriate.
  Explain any overrides.
"""

    return f"""Evaluate this business process for multi-agent pattern selection.

USE CASE: {understanding.use_case}
BUSINESS GOAL: {understanding.business_goal}

DOMAINS:
{domains_text}

DECISION POINTS:
{decisions_text}
{constraints_text}{heuristic_text}
Strands Agents SDK supports these patterns (and nesting them):

1. GRAPH — Deterministic directed graph. Nodes are agents, edges are dependencies.
   Supports conditional edges, cycles, parallel execution.
   Can nest Swarms, other Graphs, or custom nodes inside.

2. SWARM — Autonomous agent handoffs. Agents decide who to hand off to.
   Best for exploratory, collaborative, investigation tasks.

3. WORKFLOW — Pre-defined task DAG. Independent tasks run in parallel.
   Best for repeatable, well-defined sequences.

4. AGENTS-AS-TOOLS — LLM orchestrator invokes specialist agents as @tool functions.
   Best when the orchestrator needs to reason about which agents to call.

HYBRID PATTERNS: Strands supports nesting. A Graph node can be a Swarm
(e.g., a fraud investigation swarm inside a claims processing graph).
A Graph node can also be another Graph, a custom FunctionNode, or an
Agent-as-Tool orchestrator.

For each domain, evaluate which pattern fits best. Then determine:
- Can a single pattern handle the entire process?
- Or does the process need a hybrid (outer pattern + nested inner patterns)?

Return JSON:
{{
  "is_hybrid": true/false,
  "primary_pattern": "graph|swarm|workflow|agents_as_tools",
  "complexity_score": 0.0-1.0,
  "region_evaluations": [
    {{
      "domain": "string",
      "recommended_pattern": "string",
      "signals": ["string"],
      "reasoning": "string",
      "overridden": true/false,
      "override_reason": "string or null"
    }}
  ],
  "hybrid_recommendation": {{
    "outer_pattern": "graph",
    "inner_patterns": {{"domain_name": "pattern"}},
    "nesting_map": [
      {{
        "domain": "string",
        "node_type": "agent|nested_pattern",
        "pattern": "string",
        "note": "string"
      }}
    ],
    "reasoning": "string"
  }},
  "evaluation_summary": "string"
}}"""


def parse_llm_evaluation(llm_json: dict, heuristic_eval: PatternEvaluation) -> PatternEvaluation:
    """
    Parse the LLM's pattern evaluation response and merge with heuristic results.

    The LLM can override domain pattern assignments. When it does, we keep
    the heuristic scores but update the recommended pattern and reasoning.
    """
    region_evals = []

    # Build a lookup from heuristic results
    heuristic_by_domain = {r.domain: r for r in heuristic_eval.region_evaluations}

    for llm_region in llm_json.get("region_evaluations", []):
        domain_name = llm_region.get("domain", "")
        heuristic_region = heuristic_by_domain.get(domain_name)

        if heuristic_region:
            # Merge: keep heuristic scores, use LLM's pattern if overridden
            reasoning = llm_region.get("reasoning", heuristic_region.reasoning)
            if llm_region.get("overridden"):
                reasoning = (
                    f"[LLM override] {llm_region.get('override_reason', '')} "
                    f"Original: {heuristic_region.recommended_pattern}. "
                    f"{reasoning}"
                )

            region_evals.append(RegionEvaluation(
                domain=domain_name,
                description=heuristic_region.description,
                signals=llm_region.get("signals", heuristic_region.signals),
                scores=heuristic_region.scores,  # keep heuristic scores
                recommended_pattern=llm_region.get(
                    "recommended_pattern", heuristic_region.recommended_pattern
                ),
                reasoning=reasoning,
                is_complex=heuristic_region.is_complex,
            ))
        else:
            # New domain from LLM (shouldn't happen, but handle gracefully)
            region_evals.append(RegionEvaluation(
                domain=domain_name,
                description="",
                signals=llm_region.get("signals", []),
                scores={},
                recommended_pattern=llm_region.get("recommended_pattern", "graph"),
                reasoning=llm_region.get("reasoning", ""),
            ))

    # Use LLM's hybrid recommendation if provided
    hybrid = None
    llm_hybrid = llm_json.get("hybrid_recommendation")
    if llm_hybrid and llm_json.get("is_hybrid"):
        hybrid = HybridRecommendation(
            outer_pattern=llm_hybrid.get("outer_pattern", "graph"),
            inner_patterns=llm_hybrid.get("inner_patterns", {}),
            nesting_map=llm_hybrid.get("nesting_map", []),
            reasoning=llm_hybrid.get("reasoning", ""),
        )

    # Blend complexity: average of heuristic and LLM
    llm_complexity = llm_json.get("complexity_score", heuristic_eval.complexity_score)
    blended_complexity = round(
        0.4 * heuristic_eval.complexity_score + 0.6 * llm_complexity, 3
    )

    return PatternEvaluation(
        is_hybrid=llm_json.get("is_hybrid", heuristic_eval.is_hybrid),
        primary_pattern=llm_json.get("primary_pattern", heuristic_eval.primary_pattern),
        region_evaluations=region_evals if region_evals else heuristic_eval.region_evaluations,
        hybrid=hybrid if hybrid else heuristic_eval.hybrid,
        complexity_score=blended_complexity,
        evaluation_summary=llm_json.get(
            "evaluation_summary", heuristic_eval.evaluation_summary
        ),
    )
