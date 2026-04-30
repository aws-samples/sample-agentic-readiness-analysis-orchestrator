#!/usr/bin/env python3
"""
BPMN Process Analyzer — AI-powered analysis of BPMN 2.0 processes.

Analyzes one or more BPMN files and produces a comprehensive report covering:
  1. Structural Constraints — formal declarative constraints from BPMN topology
  2. Process Understanding  — use case, domains, decisions, integrations
  3. Pattern Evaluation     — which multi-agent pattern fits, complexity score
  4. Task Augmentation      — which tasks are good candidates for AI replacement
  5. Element Mapping        — how each BPMN element maps to agentic concepts
  6. Compute Recommendation — AgentCore vs EKS vs ECS
  7. Cross-Process Analysis — shared domains and reusable agents (multi-file)

Constraint extraction (step 1) is deterministic — no LLM needed. It feeds
structural signals into steps 3 and 4 for more accurate scoring.

Usage:
    # Full analysis with AI (requires AWS credentials for Bedrock)
    python analyze.py --bpmn samples/loan_approval.bpmn

    # Multiple files for cross-process analysis
    python analyze.py --bpmn samples/loan_approval.bpmn samples/kyc_onboarding.bpmn

    # Dry-run with sample data (no AWS credentials needed)
    python analyze.py --bpmn samples/loan_approval.bpmn --dry-run

    # Output as JSON instead of console report
    python analyze.py --bpmn samples/loan_approval.bpmn --dry-run --format json

    # Save report to file
    python analyze.py --bpmn samples/loan_approval.bpmn --dry-run --out report.json
"""
import argparse
import json
import sys

from parser.bpmn_parser import parse_bpmn
from analyzer.constraint_extractor import extract_constraints
from analyzer.process_analyzer import (
    build_analysis_prompt,
    parse_analysis_response,
)
from analyzer.pattern_evaluator import (
    evaluate_patterns,
    build_evaluation_prompt,
    parse_llm_evaluation,
)
from analyzer.cross_process_analyzer import analyze_cross_process
from augmentor.task_evaluator import evaluate_tasks, MigrationType
from mapper.strands_mapper import map_process
from llm.bedrock_client import BedrockClient, BedrockConfig, BedrockError


def main():
    ap = argparse.ArgumentParser(
        description="BPMN Process Analyzer — understand your BPM process"
    )
    ap.add_argument(
        "--bpmn", required=True, nargs="+",
        help="Path(s) to BPMN 2.0 XML file(s)",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Use sample analysis data instead of calling LLM",
    )
    ap.add_argument(
        "--format", choices=["console", "json"], default="console",
        help="Output format (default: console)",
    )
    ap.add_argument(
        "--out", default=None,
        help="Write JSON report to file (implies --format json)",
    )
    ap.add_argument(
        "--region", default="us-east-1",
        help="AWS region for Bedrock (default: us-east-1)",
    )
    ap.add_argument(
        "--model", default="sonnet-4.6",
        help="Model alias or full ID (default: sonnet-4.6). "
             "Aliases: sonnet-4.6, sonnet-4, sonnet-3.5, haiku-3.5",
    )
    args = ap.parse_args()

    if args.out:
        args.format = "json"

    bpmn_files = args.bpmn
    is_multi = len(bpmn_files) > 1

    # Set up LLM client once (if not dry-run)
    client = None
    if not args.dry_run:
        config = BedrockConfig(region=args.region, model=args.model)
        client = BedrockClient(config)

    # ── Per-file pipeline ───────────────────────────────────────────────
    per_file_results = []
    for bpmn_path in bpmn_files:
        result = _run_single_file_pipeline(bpmn_path, args, client)
        per_file_results.append(result)

    if not is_multi:
        # Single-file mode: use the one result directly
        r = per_file_results[0]
        if args.format == "json":
            report = build_json_report(
                r["process"], r["understanding"], r["evaluation"],
                r["augmentation"], r["blueprint"], r["constraint_profile"],
            )
            output = json.dumps(report, indent=2, default=str)
            if args.out:
                with open(args.out, "w") as f:
                    f.write(output)
                print(f"Report written to {args.out}")
            else:
                print(output)
        else:
            print_console_report(
                r["process"], r["understanding"], r["evaluation"],
                r["augmentation"], r["blueprint"], r["constraint_profile"],
            )
    else:
        # Multi-file mode: run cross-process analysis, then output
        understandings = [
            (r["process"].name or r["process"].id, r["understanding"])
            for r in per_file_results
        ]
        cross_analysis = analyze_cross_process(understandings)

        if args.format == "json":
            report = build_multi_file_json_report(per_file_results, cross_analysis)
            output = json.dumps(report, indent=2, default=str)
            if args.out:
                with open(args.out, "w") as f:
                    f.write(output)
                print(f"Report written to {args.out}")
            else:
                print(output)
        else:
            # Console: print each file's report, then cross-process summary
            for r in per_file_results:
                print_console_report(
                    r["process"], r["understanding"], r["evaluation"],
                    r["augmentation"], r["blueprint"], r["constraint_profile"],
                )
            _print_cross_process_console(cross_analysis)


def _run_single_file_pipeline(bpmn_path, args, client):
    """Run the full analysis pipeline for a single BPMN file.

    Returns a dict with keys: process, constraint_profile, understanding,
    evaluation, augmentation, blueprint.
    """
    # ── Step 1: Parse BPMN ──────────────────────────────────────────
    process = parse_bpmn(bpmn_path)

    # ── Step 1b: Extract Structural Constraints ─────────────────────
    # Constraint extraction is deterministic (no LLM). Wrap in try/except
    # so the pipeline continues with None on failure (Req 10.4).
    constraint_profile = None
    try:
        constraint_profile = extract_constraints(process)
    except Exception as e:
        print(f"  [Constraints] Extraction failed for {bpmn_path}: {e}",
              file=sys.stderr)

    # ── Step 2: Process Understanding (LLM or dry-run) ──────────────
    analysis_prompt = build_analysis_prompt(process, constraint_profile)

    if args.dry_run:
        analysis_json = _load_sample("samples/sample_analysis.json")
    else:
        try:
            llm_response = client.analyze(analysis_prompt)
            analysis_json = llm_response.content
            print(f"  [Step 2] LLM: {llm_response.model_id} | "
                  f"{llm_response.input_tokens}+{llm_response.output_tokens} tokens | "
                  f"{llm_response.latency_ms:.0f}ms", file=sys.stderr)
        except BedrockError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    understanding = parse_analysis_response(analysis_json)

    # ── Step 3: Pattern Evaluation (heuristic + constraints) ────────
    heuristic_eval = evaluate_patterns(understanding, constraint_profile)

    # ── Step 3b: LLM-Augmented Pattern Evaluation ──────────────────
    if not args.dry_run:
        try:
            eval_prompt = build_evaluation_prompt(
                understanding, constraint_profile, heuristic_eval
            )
            llm_eval_response = client.analyze(eval_prompt)
            evaluation = parse_llm_evaluation(
                llm_eval_response.content, heuristic_eval
            )
            print(f"  [Step 3] LLM: {llm_eval_response.model_id} | "
                  f"{llm_eval_response.input_tokens}+{llm_eval_response.output_tokens} tokens | "
                  f"{llm_eval_response.latency_ms:.0f}ms", file=sys.stderr)
        except (BedrockError, Exception) as e:
            print(f"  [Step 3] LLM augmentation failed, using heuristic: {e}",
                  file=sys.stderr)
            evaluation = heuristic_eval
    else:
        evaluation = heuristic_eval

    # ── Step 4: Task-Level Augmentation Scoring (+ constraints) ─────
    augmentation = evaluate_tasks(process, constraint_profile)

    # ── Step 5: Element Mapping (+ constraints) ─────────────────────
    blueprint = map_process(process, constraint_profile)

    return {
        "process": process,
        "constraint_profile": constraint_profile,
        "understanding": understanding,
        "evaluation": evaluation,
        "augmentation": augmentation,
        "blueprint": blueprint,
    }


def build_json_report(process, understanding, evaluation, augmentation, blueprint,
                      constraint_profile):
    """Build a complete JSON report from all analysis stages."""
    # ── structural_constraints with SIGNAL/LTLf formulas (Req 10.5) ──
    structural_constraints = _build_structural_constraints_section(constraint_profile)

    # ── cost_analysis section (Req 5.7) ──
    cost_analysis = _build_cost_analysis_section(augmentation)

    return {
        "process": {
            "id": process.id,
            "name": process.name,
            "element_count": len(process.elements),
            "flow_count": len(process.flows),
            "start_events": process.start_events,
            "end_events": process.end_events,
        },
        "structural_constraints": structural_constraints,
        "understanding": {
            "use_case": understanding.use_case,
            "business_goal": understanding.business_goal,
            "domains": [
                {
                    "name": d.name,
                    "description": d.description,
                    "elements": d.elements,
                    "capabilities": d.capabilities,
                    "needs_human": d.needs_human,
                }
                for d in understanding.domains
            ],
            "decision_points": understanding.decision_points,
            "integration_points": understanding.integration_points,
            "human_touchpoints": understanding.human_touchpoints,
        },
        "pattern_evaluation": {
            "is_hybrid": evaluation.is_hybrid,
            "primary_pattern": evaluation.primary_pattern,
            "complexity_score": evaluation.complexity_score,
            "summary": evaluation.evaluation_summary,
            "regions": [
                {
                    "domain": r.domain,
                    "recommended_pattern": r.recommended_pattern,
                    "scores": r.scores,
                    "signals": r.signals,
                    "is_complex": r.is_complex,
                    "reasoning": r.reasoning,
                }
                for r in evaluation.region_evaluations
            ],
            "hybrid": {
                "outer_pattern": evaluation.hybrid.outer_pattern,
                "inner_patterns": evaluation.hybrid.inner_patterns,
                "nesting_map": evaluation.hybrid.nesting_map,
                "reasoning": evaluation.hybrid.reasoning,
            } if evaluation.hybrid else None,
        },
        "task_augmentation": {
            "total_tasks": augmentation.total_tasks,
            "agent_count": augmentation.agent_count,
            "service_count": augmentation.service_count,
            "human_count": augmentation.human_count,
            "summary": augmentation.summary,
            "recommended_order": augmentation.recommended_order,
            "evaluations": [
                {
                    "element_id": e.element_id,
                    "element_name": e.element_name,
                    "element_type": e.element_type,
                    "verdict": e.verdict.value,
                    "migration_type": e.migration_type.value,
                    "scores": {
                        "ai_benefit": e.score.ai_benefit,
                        "complexity": e.score.complexity,
                        "risk": e.score.risk,
                        "effort": e.score.effort,
                        "composite": e.score.composite,
                    },
                    "reasoning": e.reasoning,
                    "agent_description": e.agent_description,
                    "service_description": e.service_description,
                    "integration_approach": e.integration_approach,
                    "prerequisites": e.prerequisites,
                    "cost_estimate": {
                        "estimated_tokens_per_invocation": e.cost_estimate.estimated_tokens_per_invocation,
                        "recommended_model": e.cost_estimate.recommended_model,
                        "cost_per_1k_invocations_usd": e.cost_estimate.cost_per_1k_invocations_usd,
                    } if e.cost_estimate else None,
                    "cost_override_reason": e.cost_override_reason,
                }
                for e in augmentation.evaluations
            ],
        },
        "cost_analysis": cost_analysis,
        "strands_mapping": {
            "process_name": blueprint.process_name,
            "agents_needed": blueprint.agents_needed,
            "tools_needed": blueprint.tools_needed,
            "has_human_escalation": blueprint.has_human_escalation,
            "elements": [
                {
                    "bpmn_id": m.bpmn_id,
                    "bpmn_name": m.bpmn_name,
                    "bpmn_type": m.bpmn_type.value,
                    "strands_concept": m.strands_concept.value,
                    "strands_implementation": m.strands_implementation,
                    "notes": m.notes,
                }
                for m in blueprint.elements
            ],
        },
        "compute_recommendation": {
            "primary": blueprint.compute.primary.value,
            "reasoning": blueprint.compute.reasoning,
            "considerations": blueprint.compute.considerations,
            "alternatives": blueprint.compute.alternatives,
        } if blueprint.compute else None,
    }


def _build_structural_constraints_section(constraint_profile):
    """Build the structural_constraints section with SIGNAL/LTLf formulas."""
    if constraint_profile is None:
        return {
            "total_constraints": 0,
            "constraint_density": 0.0,
            "max_gateway_depth": 0,
            "deeply_nested": False,
            "by_type": {},
            "ordering_constraints": 0,
            "exclusion_constraints": 0,
            "coexistence_constraints": 0,
            "constraints": [],
        }

    return {
        "total_constraints": constraint_profile.total_constraints,
        "constraint_density": round(constraint_profile.constraint_density, 2),
        "max_gateway_depth": constraint_profile.max_gateway_depth,
        "deeply_nested": constraint_profile.deeply_nested,
        "by_type": constraint_profile.by_type,
        "ordering_constraints": constraint_profile.ordering_constraints,
        "exclusion_constraints": constraint_profile.exclusion_constraints,
        "coexistence_constraints": constraint_profile.coexistence_constraints,
        "constraints": [
            {
                "type": c.constraint_type.value,
                "source": c.source,
                "target": c.target,
                "description": c.description,
                "signal": c.to_signal(),
                "ltlf": c.to_ltlf(),
            }
            for c in constraint_profile.constraints
        ],
    }


def _build_cost_analysis_section(augmentation):
    """Build the cost_analysis section with per-task estimates and total monthly projection."""
    daily_volume = 100  # default when no event log is available
    per_task = []
    for e in augmentation.evaluations:
        if e.migration_type == MigrationType.AGENT and e.cost_estimate:
            monthly_cost = round(
                e.cost_estimate.cost_per_1k_invocations_usd * daily_volume / 1000 * 30,
                2,
            )
            per_task.append({
                "task": e.element_name,
                "migration_type": e.migration_type.value,
                "recommended_model": e.cost_estimate.recommended_model,
                "estimated_tokens_per_invocation": e.cost_estimate.estimated_tokens_per_invocation,
                "cost_per_1k_invocations_usd": e.cost_estimate.cost_per_1k_invocations_usd,
                "monthly_cost_usd": monthly_cost,
            })

    return {
        "per_task": per_task,
        "total_estimated_monthly_cost_usd": augmentation.total_estimated_monthly_cost_usd,
        "daily_volume": daily_volume,
        "note": "Default daily volume used (no event log available)",
    }


def build_multi_file_json_report(per_file_results, cross_analysis):
    """Build a JSON report for multi-file analysis with cross-process data."""
    processes = []
    for r in per_file_results:
        single_report = build_json_report(
            r["process"], r["understanding"], r["evaluation"],
            r["augmentation"], r["blueprint"], r["constraint_profile"],
        )
        processes.append(single_report)

    # Build reusable_agents section (Req 7.5)
    reusable_agents = [
        {
            "name": agent.name,
            "served_processes": agent.served_processes,
            "shared_tools": agent.shared_tools,
            "process_specific_extensions": agent.process_specific_extensions,
        }
        for agent in cross_analysis.reusable_agents
    ]

    return {
        "processes": processes,
        "cross_process_analysis": {
            "shared_domains": [
                {
                    "domain_name": sd.domain_name,
                    "matching_processes": sd.matching_processes,
                    "shared_capabilities": sd.shared_capabilities,
                    "process_specific_capabilities": sd.process_specific_capabilities,
                    "similarity": round(sd.similarity, 3),
                    "recommendation": sd.recommendation,
                }
                for sd in cross_analysis.shared_domains
            ],
            "summary": cross_analysis.summary,
        },
        "reusable_agents": reusable_agents,
    }


def _print_cross_process_console(cross_analysis):
    """Print cross-process analysis summary to console."""
    W = 72
    SEP = "=" * W
    sep = "-" * W

    print(f"\n{SEP}")
    print(f"  CROSS-PROCESS ANALYSIS")
    print(f"{SEP}\n")

    if cross_analysis.shared_domains:
        print(f"  Shared Domains ({len(cross_analysis.shared_domains)}):")
        print(f"{sep}")
        for sd in cross_analysis.shared_domains:
            print(f"    • {sd.domain_name}")
            print(f"      Processes: {', '.join(sd.matching_processes)}")
            print(f"      Similarity: {sd.similarity:.2f}")
            print(f"      Recommendation: {sd.recommendation}")
            print(f"      Shared: {', '.join(sd.shared_capabilities)}")
            print()

    if cross_analysis.reusable_agents:
        print(f"  Reusable Agents ({len(cross_analysis.reusable_agents)}):")
        print(f"{sep}")
        for agent in cross_analysis.reusable_agents:
            print(f"    • {agent.name}")
            print(f"      Serves: {', '.join(agent.served_processes)}")
            print(f"      Shared tools: {', '.join(agent.shared_tools)}")
            print()

    print(f"  {cross_analysis.summary}")
    print(f"\n{SEP}")
    print(f"  END OF CROSS-PROCESS ANALYSIS")
    print(f"{SEP}\n")


def print_console_report(process, understanding, evaluation, augmentation, blueprint,
                         constraint_profile):
    """Print a human-readable analysis report to the console."""
    W = 72
    SEP = "=" * W
    sep = "-" * W

    # ── Header ──────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print(f"  BPMN PROCESS ANALYSIS REPORT")
    print(f"  Process: {process.name or process.id}")
    print(f"  Elements: {len(process.elements)}  |  Flows: {len(process.flows)}")
    print(f"{SEP}\n")

    # ── 1. Structural Constraints ───────────────────────────────────────
    print(f"  1. STRUCTURAL CONSTRAINTS")
    print(f"{sep}")
    if constraint_profile is None:
        print(f"  Constraint extraction was not available for this process.")
        print()
    else:
        print(f"  Total Constraints: {constraint_profile.total_constraints}")
        print(f"  Constraint Density: {constraint_profile.constraint_density:.2f} "
              f"(constraints per element)")
        print(f"  Ordering: {constraint_profile.ordering_constraints}  |  "
              f"Exclusion: {constraint_profile.exclusion_constraints}  |  "
              f"Co-existence: {constraint_profile.coexistence_constraints}")
        print()

        by_type = constraint_profile.by_type
        if by_type:
            print(f"  Breakdown:")
            for ctype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * min(count, 20)
                print(f"    {ctype:<20} {count:>3}  {bar}")
            print()

        # Show a few key constraints
        key_types = {"exclusive_choice", "not_coexistence", "init", "end"}
        key_constraints = [c for c in constraint_profile.constraints
                           if c.constraint_type.value in key_types]
        if key_constraints:
            print(f"  Key Constraints:")
            for c in key_constraints[:10]:
                print(f"    [{c.constraint_type.value}] {c.description}")
            print()

    # ── 2. Process Understanding ────────────────────────────────────────
    print(f"  2. PROCESS UNDERSTANDING")
    print(f"{sep}")
    print(f"  Use Case:")
    print(f"    {understanding.use_case}\n")
    print(f"  Business Goal:")
    print(f"    {understanding.business_goal}\n")

    print(f"  Domain Clusters ({len(understanding.domains)}):")
    for d in understanding.domains:
        human = " [HUMAN]" if d.needs_human else ""
        print(f"    • {d.name}{human}")
        print(f"      {d.description}")
        print(f"      Elements: {', '.join(d.elements)}")
        print(f"      Capabilities: {', '.join(d.capabilities)}")
        print()

    if understanding.decision_points:
        print(f"  Decision Points ({len(understanding.decision_points)}):")
        for dp in understanding.decision_points:
            ai = "✓ AI-suitable" if dp.get("ai_suitable") else "✗ Needs human"
            print(f"    • {dp.get('element_id', '?')}: {dp.get('business_question', '?')}")
            print(f"      {ai} — {dp.get('confidence_note', '')}")
        print()

    if understanding.integration_points:
        print(f"  Integration Points ({len(understanding.integration_points)}):")
        for ip in understanding.integration_points:
            print(f"    • {ip.get('element_id', '?')} → {ip.get('system', '?')}")
            print(f"      {ip.get('purpose', '')}")
        print()

    if understanding.human_touchpoints:
        print(f"  Human Touchpoints ({len(understanding.human_touchpoints)}):")
        for ht in understanding.human_touchpoints:
            truly = "Truly needed" if ht.get("truly_needs_human") else "Could be automated"
            print(f"    • {ht.get('element_id', '?')}: {ht.get('reason', '?')}")
            print(f"      {truly} — {ht.get('alternative', '')}")
        print()

    # ── 3. Pattern Evaluation ───────────────────────────────────────────
    print(f"  3. PATTERN EVALUATION")
    print(f"{sep}")
    print(f"  Complexity Score: {evaluation.complexity_score:.2f} / 1.00")
    print(f"  Hybrid Needed:   {'Yes' if evaluation.is_hybrid else 'No'}")
    print(f"  Primary Pattern: {evaluation.primary_pattern}\n")

    for r in evaluation.region_evaluations:
        marker = " ⚡" if r.is_complex else ""
        print(f"    • {r.domain} → {r.recommended_pattern}{marker}")
        scores_str = "  ".join(f"{p}: {s:.2f}" for p, s in r.scores.items())
        print(f"      Scores: {scores_str}")
        print(f"      Signals: {', '.join(r.signals) if r.signals else 'none'}")
    print()

    if evaluation.hybrid:
        print(f"  Hybrid Composition:")
        print(f"    Outer: {evaluation.hybrid.outer_pattern}")
        for n in evaluation.hybrid.nesting_map:
            if n["node_type"] == "nested_pattern":
                print(f"    ↳ {n['domain']} → nested {n['pattern']}")
            else:
                print(f"    • {n['domain']} → direct {n['pattern']} node")
        print(f"    {evaluation.hybrid.reasoning}")
        print()

    print(f"  Summary: {evaluation.evaluation_summary}\n")

    # ── 4. Task Augmentation Scoring ────────────────────────────────────
    print(f"  4. TASK AUGMENTATION SCORING")
    print(f"{sep}")
    print(f"  Tasks Evaluated: {augmentation.total_tasks}")
    print(f"  Migration: {augmentation.agent_count} agents, "
          f"{augmentation.service_count} services, "
          f"{augmentation.human_count} human")
    print(f"  Estimated Monthly Cost: ${augmentation.total_estimated_monthly_cost_usd:.2f}\n")

    for ev in augmentation.evaluations:
        icon = {
            "strong_candidate": "🟢",
            "good_candidate": "🟡",
            "keep_as_is": "⚪",
            "human_required": "🔴",
        }.get(ev.verdict.value, "⚪")

        migration_icon = {
            "agent": "🤖",
            "service": "⚙️",
            "human_required": "🧑",
        }.get(ev.migration_type.value, "")

        print(f"    {icon} {migration_icon} {ev.element_name} ({ev.element_type})")
        print(f"       Verdict:   {ev.verdict.value}  |  Type: {ev.migration_type.value}")
        print(f"       AI Benefit: {ev.score.ai_benefit:.2f}  "
              f"Risk: {ev.score.risk:.2f}  "
              f"Composite: {ev.score.composite:.2f}")
        print(f"       {ev.reasoning}")
        if ev.migration_type == MigrationType.AGENT and ev.cost_estimate:
            print(f"       Cost: {ev.cost_estimate.recommended_model} | "
                  f"{ev.cost_estimate.estimated_tokens_per_invocation} tokens | "
                  f"${ev.cost_estimate.cost_per_1k_invocations_usd}/1k invocations")
        if ev.verdict.value in ("strong_candidate", "good_candidate"):
            if ev.agent_description:
                print(f"       Agent: {ev.agent_description}")
            if ev.service_description:
                print(f"       Service: {ev.service_description}")
            print(f"       Integration: {ev.integration_approach}")
        print()

    if augmentation.recommended_order:
        print(f"  Recommended Replacement Order:")
        for i, eid in enumerate(augmentation.recommended_order, 1):
            name = next(
                (e.element_name for e in augmentation.evaluations if e.element_id == eid),
                eid,
            )
            print(f"    {i}. {name}")
        print()

    print(f"  {augmentation.summary}\n")

    # ── 5. Strands Mapping ──────────────────────────────────────────────
    print(f"  5. BPMN → STRANDS AGENTS MAPPING")
    print(f"{sep}")
    print(f"  Agents needed: {blueprint.agents_needed}  |  "
          f"Tools needed: {blueprint.tools_needed}  |  "
          f"Human escalation: {'Yes' if blueprint.has_human_escalation else 'No'}")
    print()

    type_width = max(len(m.bpmn_type.value) for m in blueprint.elements)
    for m in blueprint.elements:
        print(f"    {m.bpmn_type.value:<{type_width}}  {m.bpmn_name or m.bpmn_id}")
        print(f"    {'':>{type_width}}  → {m.strands_concept.value}")
        print(f"    {'':>{type_width}}    {m.strands_implementation}")
        if m.notes:
            first_line = m.notes.split("\n")[0]
            print(f"    {'':>{type_width}}    {first_line}")
        print()

    # ── 6. Compute Recommendation ───────────────────────────────────────
    if blueprint.compute:
        print(f"  6. COMPUTE RECOMMENDATION")
        print(f"{sep}")
        print(f"  Primary: {blueprint.compute.primary.value.upper()}")
        print(f"  {blueprint.compute.reasoning}")
        print()

        print(f"  Considerations:")
        for c in blueprint.compute.considerations:
            print(f"    • {c}")
        print()

        if blueprint.compute.alternatives:
            print(f"  Alternatives:")
            for alt in blueprint.compute.alternatives:
                print(f"    • {alt['option'].upper()}")
                print(f"      {alt['when']}")
            print()
    print(f"\n{SEP}")
    print(f"  END OF ANALYSIS REPORT")
    print(f"{SEP}\n")


def _load_sample(path: str) -> dict:
    """Load a sample JSON file for dry-run mode."""
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    main()
