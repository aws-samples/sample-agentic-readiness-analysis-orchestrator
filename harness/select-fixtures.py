#!/usr/bin/env python3
"""
select-fixtures.py — pick the 1-2 fixtures that best exercise a rubric change.

WHY THIS EXISTS
A TD edit is portfolio-wide in principle, so run-fixtures.sh's changed-only path used to
analyze every fixture: 11 fixtures x 2 analyses = 22 units. Each unit bills ~110-130
AGENT-minutes (internal compute, parallelized inside atx; wall-clock is ~10-20 min per
unit as measured on the runner), so 22 units is a large multiple of the cost needed to
observe a single rubric edit. Worse, atx's progress spinner blew GitLab's 4 MB log limit
after only 4 units, so the differ/judge never even reported.

So: the FULL sweep is a local / harness:full concern, and an MR runs the SMALLEST set of
fixtures that can actually observe the edited questions.

HOW IT PICKS
Rubric question ids are prefixed by category (API-Q2, AUTH-Q5, INF-Q11...), and each
fixture in usecases.yaml declares expectations.<analysis>.must_have_categories. So:

  1. Diff the changed TD's SKILL.md to find which question ids the MR touched.
  2. Take their category prefixes (API-Q2 -> API).
  3. Score every fixture by how many of those categories it exercises, breaking ties
     toward the fixture whose axes are most relevant (has_api for API, has_iac for INF,
     auth_present for AUTH/SEC) and then by fixture id for determinism.
  4. Emit the top N (default 2, and never more than the number of fixtures).

If the diff touches no recognisable question id (e.g. only prose or a scoring table),
fall back to the highest-coverage fixtures for that analysis type — a broad change needs
a broadly representative repo, not a niche one.

DETERMINISM: no randomness and no commit-hash rotation. The same MR always picks the same
fixtures, so a delta is comparable run-to-run and a surprising result is reproducible.

Usage:
  select-fixtures.py --analysis ara --td definitions/managed/agentic-readiness-analysis \
                     --base origin/main [--count 2] [--format lines|json]
  select-fixtures.py --analysis mod --changed-questions INF-Q3,SEC-Q1   # explicit ids
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is in requirements.txt
    print("select-fixtures: pyyaml required", file=sys.stderr)
    raise SystemExit(2)

HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_DIR.parent
DEFAULT_USECASES = HARNESS_DIR / "usecases.yaml"

# A question id looks like API-Q2 / AUTH-Q11 / INF-Q3.
QUESTION_RE = re.compile(r"\b([A-Z]{3,6})-Q(\d+)\b")

# Axis hints: when a category is touched, these axes make a fixture a better probe for it.
# value None means "any truthy/non-'none' value counts".
AXIS_HINTS = {
    "API": ("has_api", None),        # a repo with no API can't exercise API questions
    "INF": ("has_iac", True),
    "OPS": ("has_iac", True),
    "AUTH": ("auth_present", None),
    "SEC": ("auth_present", None),
    "DATA": ("persistence", None),
}


def changed_question_ids(td_path: Path, base: str) -> set[str]:
    """Question ids appearing on changed lines of the TD's markdown."""
    try:
        diff = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--unified=0", f"{base}...HEAD", "--", str(td_path)],
            capture_output=True, text=True, check=False,
        ).stdout
    except OSError:
        return set()
    ids: set[str] = set()
    for line in diff.splitlines():
        # Only added/removed content lines — skip hunk headers (@@) and +++/--- file lines.
        if line[:1] in "+-" and not line.startswith(("+++", "---")):
            for m in QUESTION_RE.finditer(line):
                ids.add(f"{m.group(1)}-Q{m.group(2)}")
    return ids


def axis_bonus(axes: dict, categories: set[str]) -> int:
    """Small tie-breaker: does this fixture have the axis a touched category keys off?"""
    bonus = 0
    for cat in categories:
        hint = AXIS_HINTS.get(cat)
        if not hint:
            continue
        key, want = hint
        val = axes.get(key)
        if want is None:
            # Truthy and not the explicit "absent" sentinels.
            if val not in (None, False, "none", "None", ""):
                bonus += 1
        elif val == want:
            bonus += 1
    return bonus


def select(usecases: dict, analysis: str, categories: set[str], count: int) -> list[dict]:
    fixtures = usecases.get("fixtures") or []
    scored = []
    for fx in fixtures:
        exp = (fx.get("expectations") or {}).get(analysis) or {}
        cats = set(exp.get("must_have_categories") or [])
        if not cats:
            continue  # fixture doesn't participate in this analysis type
        axes = fx.get("axes") or {}
        if categories:
            overlap = len(cats & categories)
            bonus = axis_bonus(axes, categories)
        else:
            # No identifiable question ids -> prefer the broadest fixture for this analysis.
            overlap = len(cats)
            bonus = axis_bonus(axes, cats)
        scored.append({
            "id": fx.get("id"),
            "path": fx.get("path"),
            "score": overlap,
            "bonus": bonus,
            "categories": sorted(cats),
        })
    # Highest overlap, then axis relevance, then id for stable ordering.
    scored.sort(key=lambda r: (-r["score"], -r["bonus"], str(r["id"])))
    chosen = [r for r in scored if r["score"] > 0][:count]
    if not chosen:  # nothing overlapped at all — still return something runnable
        chosen = scored[:count]
    return chosen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", required=True, choices=["ara", "mod"])
    ap.add_argument("--td", help="path to the changed TD folder (for diffing)")
    ap.add_argument("--base", default="origin/main", help="diff base (default origin/main)")
    ap.add_argument("--changed-questions", help="comma-separated ids, bypassing git diff")
    ap.add_argument("--count", type=int, default=2, help="max fixtures to select (default 2)")
    ap.add_argument("--usecases", type=Path, default=DEFAULT_USECASES)
    ap.add_argument("--format", choices=["lines", "json"], default="lines")
    args = ap.parse_args(argv)

    usecases = yaml.safe_load(args.usecases.read_text())

    if args.changed_questions:
        ids = {q.strip() for q in args.changed_questions.split(",") if q.strip()}
    elif args.td:
        ids = changed_question_ids(Path(args.td), args.base)
    else:
        ids = set()

    categories = {i.split("-Q")[0] for i in ids}
    chosen = select(usecases, args.analysis, categories, max(1, args.count))

    if args.format == "json":
        print(json.dumps({
            "analysis": args.analysis,
            "changed_questions": sorted(ids),
            "categories": sorted(categories),
            "selected": chosen,
        }, indent=2))
    else:
        # stderr = the reasoning (for the CI log); stdout = just paths (for consumption).
        if ids:
            print(f"select-fixtures: {args.analysis}: touched {sorted(ids)} "
                  f"-> categories {sorted(categories)}", file=sys.stderr)
        else:
            print(f"select-fixtures: {args.analysis}: no question ids in the diff "
                  f"-> falling back to broadest-coverage fixtures", file=sys.stderr)
        for r in chosen:
            print(f"select-fixtures:   picked {r['id']} "
                  f"(overlap={r['score']} axis_bonus={r['bonus']} cats={r['categories']})",
                  file=sys.stderr)
        for r in chosen:
            print(r["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
