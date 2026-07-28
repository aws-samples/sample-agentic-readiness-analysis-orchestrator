#!/usr/bin/env python3
"""
coverage-heatmap.py — render the use-case coverage matrix from harness/usecases.yaml.

Answers "which use-case types are the managed TDs exercised against, and where are the
gaps?" (DESIGN.md §4). Pure/offline — reads only usecases.yaml.

Outputs (Markdown by default; --format json for machine use):
  1. Per-axis value counts (how many fixtures cover each axis value).
  2. Declared-but-uncovered axis values → coverage GAPS (a value in `axes` with 0 fixtures).
  3. A language × has_iac cross-tab (the pairing that matters most for IaC-sensitive rules).

Usage:
  coverage-heatmap.py [--usecases harness/usecases.yaml] [--format md|json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("error: pyyaml required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

HARNESS_DIR = Path(__file__).resolve().parent


def load(usecases: Path) -> dict:
    return yaml.safe_load(usecases.read_text(encoding="utf-8"))


def analyze(doc: dict) -> dict:
    axes_vocab: dict = doc.get("axes", {}) or {}
    fixtures: list = doc.get("fixtures", []) or []

    # Count coverage per axis value.
    counts: dict[str, Counter] = {axis: Counter() for axis in axes_vocab}
    for fx in fixtures:
        for axis, val in (fx.get("axes", {}) or {}).items():
            counts.setdefault(axis, Counter())[str(val)] += 1

    # Gaps: declared vocab values with zero fixtures.
    gaps: dict[str, list] = {}
    for axis, vocab in axes_vocab.items():
        covered = set(counts.get(axis, {}))
        missing = [str(v) for v in vocab if str(v) not in covered]
        if missing:
            gaps[axis] = missing

    # language × has_iac cross-tab.
    crosstab: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for fx in fixtures:
        ax = fx.get("axes", {}) or {}
        lang = str(ax.get("language", "?"))
        iac = str(ax.get("has_iac", "?"))
        crosstab[lang][iac] += 1

    return {
        "total_fixtures": len(fixtures),
        "counts": {a: dict(c) for a, c in counts.items()},
        "gaps": gaps,
        "language_x_has_iac": {k: dict(v) for k, v in crosstab.items()},
    }


def render_md(result: dict) -> str:
    lines = ["# Use-case coverage heatmap", ""]
    lines.append(f"**{result['total_fixtures']} fixtures** across the managed-TD matrix.")
    lines.append("")

    for axis, counts in result["counts"].items():
        lines.append(f"## {axis}")
        lines.append("")
        lines.append("| value | fixtures |")
        lines.append("|---|---:|")
        for val, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"| {val} | {n} |")
        if axis in result["gaps"]:
            lines.append(f"| _uncovered:_ {', '.join(result['gaps'][axis])} | 0 |")
        lines.append("")

    lines.append("## language × has_iac")
    lines.append("")
    lines.append("| language | iac:true | iac:false |")
    lines.append("|---|---:|---:|")
    for lang in sorted(result["language_x_has_iac"]):
        row = result["language_x_has_iac"][lang]
        lines.append(f"| {lang} | {row.get('true', 0)} | {row.get('false', 0)} |")
    lines.append("")

    if result["gaps"]:
        lines.append("## ⚠ Coverage gaps (declared vocab with no fixture)")
        lines.append("")
        for axis, missing in result["gaps"].items():
            lines.append(f"- **{axis}**: {', '.join(missing)}")
    else:
        lines.append("## ✓ No coverage gaps — every declared axis value has ≥1 fixture.")
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render the use-case coverage heatmap.")
    ap.add_argument("--usecases", type=Path, default=HARNESS_DIR / "usecases.yaml")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    args = ap.parse_args(argv)

    doc = load(args.usecases)
    result = analyze(doc)
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(render_md(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
