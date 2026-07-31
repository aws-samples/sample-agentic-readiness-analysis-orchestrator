#!/usr/bin/env python3
"""
normalize-report.py — backfill ONLY the flaky top-level envelope on a collected report.

Why this exists
---------------
The managed ARA/MOD TDs are nondeterministic about the top-level *envelope* fields
`analysis_type` (the ingester's discriminator) and `repo_name`: most runs emit them, but
some runs drop them while the body of the report (findings[], evaluations[], counts,
classification, …) is otherwise complete. That coin-flip made an occasional report fail
validate-contract.py for a reason that has nothing to do with the change under test.

Scope — this is a BRIDGE for the pre-publication MR harness path only. Today the harness
generates "after" reports with `atx custom def exec` on the edited TDs (they are not yet
published to Continuous Modernization), and that path is where the envelope coin-flip
shows up. It runs from collect_report() in run-fixtures.sh; the `atx ct` golden/after path
never calls it. Once the TDs are published to managed CT, `atx ct` emits the envelope
consistently and this backfill becomes a permanent no-op — safe to leave in place.

The harness already KNOWS both values without reading the model output at all:
  * analysis_type — the caller passes which analysis it ran (ara|mod|portfolio-ara|portfolio-mod).
  * repo_name     — the fixture directory name (per-repo reports only).

So we deterministically backfill just those two envelope fields when absent. This is the
narrow, safe seam:
  * We NEVER touch structural/semantic fields (findings[], categories[], overall_score,
    classification, pathways[], …). Backfilling those would fabricate signal and could
    hide real drift — exactly what the harness exists to catch. validate-contract.py stays
    strict on all of those; this only stops the envelope coin-flip from causing noise.
  * Idempotent: fields already present (even if "wrong") are left untouched — we only fill
    a MISSING key, so we never override real model output, and a conforming report is a
    no-op.

Usage:
    normalize-report.py <report.json> --analysis ara|mod|portfolio-ara|portfolio-mod
                        [--repo-name <name>]   # per-repo only; ignored for portfolio
    # exit 0 always on a readable/writable JSON file (prints what it changed to stderr);
    # exit 2 on IO/parse error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The four analysis values map 1:1 to the literal `analysis_type` discriminator.
VALID_ANALYSIS = {"ara", "mod", "portfolio-ara", "portfolio-mod"}
PORTFOLIO = {"portfolio-ara", "portfolio-mod"}


def normalize(data: dict, analysis: str, repo_name: str | None) -> list[str]:
    """Backfill missing envelope fields in-place. Return a list of the changes made."""
    changed: list[str] = []

    # analysis_type — the discriminator the ingester joins on. Backfill only if absent;
    # never overwrite a value the model actually emitted (a wrong one is real drift the
    # validator must still catch).
    if "analysis_type" not in data:
        data["analysis_type"] = analysis
        changed.append(f"analysis_type := {analysis!r}")

    # repo_name — per-repo only; portfolio reports are keyed by portfolio_name, not repo.
    if analysis not in PORTFOLIO and repo_name and "repo_name" not in data:
        data["repo_name"] = repo_name
        changed.append(f"repo_name := {repo_name!r}")

    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Backfill the flaky top-level report envelope")
    ap.add_argument("report", type=Path, help="report JSON to normalize in-place")
    ap.add_argument("--analysis", required=True, choices=sorted(VALID_ANALYSIS),
                    help="analysis type the harness ran (source of truth for analysis_type)")
    ap.add_argument("--repo-name", help="fixture name for per-repo reports (source of truth "
                                        "for repo_name); ignored for portfolio")
    args = ap.parse_args(argv)

    try:
        data = json.loads(args.report.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"normalize: cannot read/parse {args.report}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print(f"normalize: {args.report} is not a JSON object; leaving untouched", file=sys.stderr)
        return 0

    changed = normalize(data, args.analysis, args.repo_name)
    if changed:
        try:
            args.report.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"normalize: cannot write {args.report}: {exc}", file=sys.stderr)
            return 2
        print(f"normalize: {args.report.name}: backfilled {', '.join(changed)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
