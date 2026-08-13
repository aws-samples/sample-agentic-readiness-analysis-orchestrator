#!/usr/bin/env python3
"""
select-fixtures.py — pick the 1-2 fixtures that best exercise a rubric change.

WHY THIS EXISTS
A TD edit is portfolio-wide in principle, so run-fixtures.sh's changed-only path used to
analyze every fixture: currently 14 fixtures x 2 analyses = 28 units (the AUTHORITATIVE
count is harness/usecases.yaml, not this comment — the set has grown from 11 and will grow
again). Each unit bills ~110-130 AGENT-minutes (internal compute, parallelized inside atx;
wall-clock is ~10-20 min per unit as measured on the runner), so a full sweep is a large
multiple of the cost needed to observe a single rubric edit. Worse, atx's progress spinner blew GitLab's 4 MB log limit
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
DEFAULT_GOLDEN = HARNESS_DIR / "golden"

# The program catalog the portfolio TDs recommend from. Both managed copies are kept in
# sync (portfolio ARA + portfolio MOD), so a program edit normally touches both.
DEFAULT_PROGRAM_LIBRARIES = [
    REPO_ROOT / "definitions" / "managed" / "portfolio-agentic-readiness-analysis"
    / "references" / "program-library.md",
    REPO_ROOT / "definitions" / "managed" / "portfolio-modernization-readiness-analysis"
    / "references" / "program-library.md",
]

# A question id looks like API-Q2 / AUTH-Q11 / INF-Q3.
QUESTION_RE = re.compile(r"\b([A-Z]{3,6})-Q(\d+)\b")

# A program-library entry is an H3 heading — "### MAP (Migration Acceleration Program)
# `[ARA+MOD]` `Active`" — and the Tier-2 compact index lists more as table rows. Both
# carry a `[TAG]` (ARA/MOD) span, which is what distinguishes a *program* line from a
# section header ("### Status Key") or the pathway→workshop mapping table.
_H3_RE = re.compile(r"^\s*###\s+(.*\S)\s*$")
_BACKTICK_SPAN_RE = re.compile(r"`[^`]*`")               # `[TAG]` / `Active` decorations
_TAG_SPAN_RE = re.compile(r"`\[(?:ARA|MOD)[^\]]*\]`")    # the program Tag: `[ARA]`,`[MOD]`…

# Axis hints: when a category is touched, these axes make a fixture a better probe for it.
# value None means "any truthy/non-'none' value counts".
AXIS_HINTS = {
    "API": ("has_api", None),        # a repo with no API can't exercise API questions
    "INF": ("has_iac", True),
    "OPS": ("has_iac", True),
    "AUTH": ("auth_present", None),
    "SEC": ("has_iac", True),      # SEC-Q1/Q2 read IaC; only Q3/Q4 are about auth
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


def _acronymish(tok: str) -> bool:
    """True for a short ALL-CAPS token like MAP / OLA / AMA / 'AI DLC' — the id a report
    is likely to use — and False for prose like 'Migration Evaluator' or 'AWS'-led names."""
    tok = tok.strip()
    return bool(tok) and len(tok) <= 8 and tok == tok.upper() and any(c.isalpha() for c in tok)


def _program_tokens(label: str) -> set[str]:
    """Identifiers a report/reader might use for a program, from its library label.

    Always the full label, plus a derived short acronym so the token set overlaps what the
    differ emits under D4 (`recommended_actions[].acronym`, e.g. MAP/EBA):
      "MAP (Migration Acceleration Program)"   -> {full, "MAP"}
      "AWS Modernization Assurance (AMA)"       -> {full, "AMA"}
      "AI DLC (AI Driven Development Lifecycle)"-> {full, "AI DLC"}
      "Migration Evaluator"                     -> {full}   (no acronym to derive)
    """
    label = label.strip()
    if not label:
        return set()
    toks = {label}
    head, inner = label, ""
    if label.endswith(")") and "(" in label:
        i = label.rindex("(")
        head, inner = label[:i].strip(), label[i + 1:-1].strip()
    if _acronymish(inner):      # trailing "(AMA)" acronym
        toks.add(inner)
    if _acronymish(head):       # leading "MAP"/"AI DLC" acronym
        toks.add(head)
    return toks


def _program_names(line: str) -> set[str]:
    """Program identifiers named on a single line of program-library.md (heading or the
    Tier-2 index row); empty for section headers, prose, and the workshop-mapping table."""
    m = _H3_RE.match(line)
    if m and _TAG_SPAN_RE.search(m.group(1)):
        return _program_tokens(_BACKTICK_SPAN_RE.sub("", m.group(1)).strip())
    if line.lstrip().startswith("|") and _TAG_SPAN_RE.search(line):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] and cells[0].lower() != "program":
            return _program_tokens(cells[0])
    return set()


def changed_programs(library_paths: list[Path], base: str) -> list[str]:
    """Program identifiers whose program-library.md entry was added/removed/edited vs base.

    Mirrors changed_question_ids: a scope hint for the judge, computed from the diff of the
    program catalog rather than the rubric. Empty when the diff touches only prose (intro,
    the status key, vocabulary-alignment notes) — those move no program's trigger surface.
    """
    tokens: set[str] = set()
    for p in library_paths:
        try:
            diff = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--unified=0", f"{base}...HEAD", "--", str(p)],
                capture_output=True, text=True, check=False,
            ).stdout
        except OSError:
            continue
        for line in diff.splitlines():
            if line[:1] in "+-" and not line.startswith(("+++", "---")):
                tokens |= _program_names(line[1:])
    return sorted(tokens)


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


def has_golden(fx: dict, analysis: str, golden_dir: Path) -> bool:
    """Is there a baseline report this fixture's regenerated report can be diffed against?

    The report key is the fixture PATH BASENAME, not its usecases.yaml `id` — run-fixtures.sh
    names the report from `basename(fixture dir)` (run-fixtures.sh:488 -> stage_unit), so
    `monolith-php` writes `monolith-mod-report.json`. Keying off `id` here would call the
    monolith unbaselined when it is in fact the best-covered fixture in the set.
    """
    key = Path(str(fx.get("path") or fx.get("id") or "")).name
    return (golden_dir / f"{key}-{analysis}-report.json").is_file()


def select(usecases: dict, analysis: str, categories: set[str], count: int,
           golden_dir: Path | None = DEFAULT_GOLDEN) -> list[dict]:
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
            # A fixture with no golden report CANNOT produce a measurement: diff-reports.py
            # files it under coverage.unbaselined, it gets no per_repo entry, no safety alert
            # and no score -- so an MR that selects only such fixtures burns ~110 agent-min
            # per unit and reports `no_op: true`, telling the contributor their edit "probably
            # didn't land". Ranking must therefore prefer a baselined fixture over an
            # unbaselined one, ABOVE axis relevance: a slightly-less-apt probe that actually
            # measures beats a perfect probe that measures nothing.
            #
            # This is not hypothetical. MOD/OPS is declared by modern-orders-service,
            # modern-payments-api, monolith-php and legacy-helpdesk-tickets. The first two
            # have no golden, and won on the (-overlap, -bonus, id) sort because
            # `modern-*` sorts before `monolith`/`legacy-*` alphabetically -- so every OPS-*
            # edit, 9 of MOD's 37 questions, measured exactly nothing.
            "baselined": has_golden(fx, analysis, golden_dir) if golden_dir else True,
        })
    # Highest overlap, then MEASURABILITY, then axis relevance, then id for stable ordering.
    scored.sort(key=lambda r: (-r["score"], not r["baselined"], -r["bonus"], str(r["id"])))
    chosen = [r for r in scored if r["score"] > 0][:count]
    if not chosen:  # nothing overlapped at all — still return something runnable
        chosen = scored[:count]
    return chosen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", choices=["ara", "mod"],
                    help="required unless --emit-changed-programs")
    ap.add_argument("--td", help="path to the changed TD folder (for diffing)")
    ap.add_argument("--base", default="origin/main", help="diff base (default origin/main)")
    ap.add_argument("--changed-questions", help="comma-separated ids, bypassing git diff")
    ap.add_argument("--emit-changed-programs", action="store_true",
                    help="print program identifiers whose program-library.md entry changed "
                         "vs --base (one per line) and exit; ignores --analysis")
    ap.add_argument("--program-library", action="append", type=Path, dest="program_library",
                    help="program-library.md path to diff (repeatable; default: both managed copies)")
    ap.add_argument("--count", type=int, default=2, help="max fixtures to select (default 2)")
    ap.add_argument("--usecases", type=Path, default=DEFAULT_USECASES)
    ap.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN,
                    help="baseline report dir; fixtures with a golden report are preferred "
                         "because only they can produce a measurement (default harness/golden)")
    ap.add_argument("--format", choices=["lines", "json"], default="lines")
    args = ap.parse_args(argv)

    if args.emit_changed_programs:
        libs = args.program_library or DEFAULT_PROGRAM_LIBRARIES
        for tok in changed_programs(libs, args.base):
            print(tok)
        return 0
    if not args.analysis:
        ap.error("--analysis is required unless --emit-changed-programs")

    usecases = yaml.safe_load(args.usecases.read_text())

    if args.changed_questions:
        ids = {q.strip() for q in args.changed_questions.split(",") if q.strip()}
    elif args.td:
        ids = changed_question_ids(Path(args.td), args.base)
    else:
        ids = set()

    categories = {i.split("-Q")[0] for i in ids}
    chosen = select(usecases, args.analysis, categories, max(1, args.count),
                    golden_dir=args.golden)

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
                  f"(overlap={r['score']} axis_bonus={r['bonus']} "
                  f"baselined={'yes' if r['baselined'] else 'NO'} cats={r['categories']})",
                  file=sys.stderr)
        # Say it out loud rather than letting the differ report `no_op` and the judge
        # conclude "the edit probably didn't land". An unbaselined selection is a harness
        # coverage hole, not a contributor mistake.
        if chosen and not any(r["baselined"] for r in chosen):
            print(f"select-fixtures: WARNING: no selected fixture has a "
                  f"{args.analysis} golden report in {args.golden} — this run will produce "
                  f"NO measurement (every report lands in coverage.unbaselined). Generate a "
                  f"golden for one of these fixtures, or the verdict is not evidence.",
                  file=sys.stderr)
        for r in chosen:
            print(r["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
