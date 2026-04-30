#!/usr/bin/env python3
"""
Run BPMN analysis and produce a JSON report for the BPMN Opportunity TD.

Usage:
    # Single file
    python run_analysis.py --bpmn path/to/process.bpmn [--output report.json]

    # Directory mode: analyze all .bpmn files in a repo
    python run_analysis.py --bpmn-dir path/to/repo [--output report.json]

The output JSON contains:
- process metadata (name, element count, flow count)
- constraint profile (total, density, by type)
- task evaluations (scores, classification, cost estimates)
- dependency extraction (declared, inferred, unknown)
- pattern evaluation (recommended pattern, complexity score)

In directory mode, the output is a JSON object with:
- "processes": array of per-file analysis results
- "portfolio_summary": aggregated counts across all files
- "errors": array of files that failed to parse (with error details)

This JSON is consumed by the BPMN Opportunity Transformation Definition
which applies the opportunity classification (four categories + autonomy levels)
and generates the final markdown report.
"""
import argparse
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parser.bpmn_parser import parse_bpmn
from analyzer.constraint_extractor import extract_constraints
from analyzer.dependency_extractor import extract_dependencies, to_dict as deps_to_dict
from analyzer.exceptions import BPMNAnalysisError, AnalysisWarning
import analyzer.vendors  # noqa: F401 -- triggers auto-registration
from augmentor.task_evaluator import evaluate_tasks


def analyze_bpmn(bpmn_path: str, daily_volume: int = 100) -> dict:
    """Run the full analysis pipeline and return structured JSON."""
    process = parse_bpmn(bpmn_path)
    constraints = extract_constraints(process)
    dep_report = extract_dependencies(bpmn_path, process)
    plan = evaluate_tasks(process, constraints, daily_volume=daily_volume)

    return {
        "process": {
            "name": process.name or process.id,
            "id": process.id,
            "source_file": str(bpmn_path),
            "total_elements": len(process.elements),
            "total_flows": len(process.flows),
            "start_events": list(process.start_events),
            "end_events": list(process.end_events),
        },
        "constraints": {
            "total": constraints.total_constraints,
            "density": round(constraints.constraint_density, 2),
            "max_gateway_depth": constraints.max_gateway_depth,
            "deeply_nested": constraints.deeply_nested,
            "ordering": constraints.ordering_constraints,
            "exclusion": constraints.exclusion_constraints,
            "coexistence": constraints.coexistence_constraints,
            "by_type": constraints.by_type,
        },
        "tasks": [
            {
                "element_id": e.element_id,
                "element_name": e.element_name,
                "element_type": e.element_type,
                "scores": {
                    "ai_benefit": e.score.ai_benefit,
                    "complexity": e.score.complexity,
                    "risk": e.score.risk,
                    "effort": e.score.effort,
                    "composite": round(e.score.composite, 3),
                },
                "verdict": e.verdict.value,
                "migration_type": e.migration_type.value,
                "reasoning": e.reasoning,
                "agent_description": e.agent_description,
                "service_description": e.service_description,
                "integration_approach": e.integration_approach,
                "prerequisites": e.prerequisites,
                "cost_estimate": {
                    "tokens_per_invocation": e.cost_estimate.estimated_tokens_per_invocation,
                    "recommended_model": e.cost_estimate.recommended_model,
                    "cost_per_1k_usd": e.cost_estimate.cost_per_1k_invocations_usd,
                } if e.cost_estimate else None,
                "cost_override_reason": e.cost_override_reason,
            }
            for e in plan.evaluations
        ],
        "dependencies": deps_to_dict(dep_report),
        "summary": {
            "total_tasks": plan.total_tasks,
            "agent_count": plan.agent_count,
            "service_count": plan.service_count,
            "human_count": plan.human_count,
            "recommended_order": plan.recommended_order,
            "total_estimated_monthly_cost_usd": plan.total_estimated_monthly_cost_usd,
        },
    }


def analyze_bpmn_directory(dir_path: str, daily_volume: int = 100) -> dict:
    """Scan a directory for .bpmn files and analyze each one.

    Returns a combined report with per-file results, a portfolio summary,
    and an errors list for files that failed to parse.
    """
    root = Path(dir_path)

    # Use os.walk for performance on large repos -- skip .git, node_modules,
    # target, build, and other directories that never contain BPMN files.
    import os
    _SKIP_DIRS = {".git", "node_modules", "target", "build", "dist", ".gradle",
                  ".mvn", "__pycache__", ".pytest_cache", "vendor", ".ash-output"}
    bpmn_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for f in filenames:
            if f.endswith(".bpmn") or f.endswith(".bpmn2") or f.endswith(".bpmn20.xml"):
                bpmn_files.append(Path(dirpath) / f)
    bpmn_files.sort()

    if not bpmn_files:
        return {
            "processes": [],
            "portfolio_summary": {
                "total_files_found": 0,
                "total_files_analyzed": 0,
                "total_files_failed": 0,
                "total_tasks": 0,
                "agent_count": 0,
                "service_count": 0,
                "human_count": 0,
                "total_estimated_monthly_cost_usd": 0,
            },
            "errors": [],
        }

    processes = []
    errors = []

    for bpmn_file in bpmn_files:
        try:
            result = analyze_bpmn(str(bpmn_file), daily_volume=daily_volume)
            processes.append(result)
        except BPMNAnalysisError as exc:
            errors.append({
                "file": str(bpmn_file),
                "error_type": type(exc).__name__,
                "message": str(exc),
                "context": exc.context,
            })
        except Exception as exc:
            errors.append({
                "file": str(bpmn_file),
                "error_type": type(exc).__name__,
                "message": str(exc),
            })

    # Aggregate summary
    total_tasks = sum(p["summary"]["total_tasks"] for p in processes)
    agent_count = sum(p["summary"]["agent_count"] for p in processes)
    service_count = sum(p["summary"]["service_count"] for p in processes)
    human_count = sum(p["summary"]["human_count"] for p in processes)
    total_cost = sum(p["summary"]["total_estimated_monthly_cost_usd"] for p in processes)

    return {
        "processes": processes,
        "portfolio_summary": {
            "total_files_found": len(bpmn_files),
            "total_files_analyzed": len(processes),
            "total_files_failed": len(errors),
            "total_tasks": total_tasks,
            "agent_count": agent_count,
            "service_count": service_count,
            "human_count": human_count,
            "total_estimated_monthly_cost_usd": round(total_cost, 2),
        },
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Run BPMN analysis for opportunity classification")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bpmn", help="Path to a single BPMN file")
    group.add_argument("--bpmn-dir", help="Path to directory (analyzes all .bpmn files recursively)")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    parser.add_argument("--volume", type=int, default=100, help="Daily invocation volume (default: 100)")
    args = parser.parse_args()

    try:
        if args.bpmn_dir:
            result = analyze_bpmn_directory(args.bpmn_dir, daily_volume=args.volume)
            n = result["portfolio_summary"]
            print(
                f"Analyzed {n['total_files_analyzed']} of {n['total_files_found']} BPMN files "
                f"({n['total_files_failed']} failed). "
                f"{n['total_tasks']} tasks: {n['agent_count']} agent, "
                f"{n['service_count']} service, {n['human_count']} human.",
                file=sys.stderr,
            )
        else:
            result = analyze_bpmn(args.bpmn, daily_volume=args.volume)
    except BPMNAnalysisError as exc:
        error_result = {
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "file_path": exc.file_path,
                "context": exc.context,
            }
        }
        if args.output:
            Path(args.output).write_text(json.dumps(error_result, indent=2))
        else:
            print(json.dumps(error_result, indent=2))
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(f"Analysis written to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
