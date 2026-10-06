#!/usr/bin/env python3
"""
add-ara-category-display.py — deterministic golden migration for ARA UI-parity.

Adds a `category_display` sibling immediately after every dimension `category` field in
the ARA golden reports (per-repo + portfolio), mirroring the CM Console's service-canon
category labels. The existing `category` field is left byte-for-byte unchanged — it
remains the internal/matching key the portfolio program-library keys on. `category_display`
is derived deterministically from `category` (identity for the already-canonical values).

Scope: the eight ARA dimension categories, which only ever appear in `findings[]` and
`cross_cutting_findings[]`. The `remediation_roadmap` subtree's `category` values are
remediation focus-area labels ("Machine Identity Authentication", etc.), NOT dimension
names — they are outside the map and are deliberately left untouched (they are not
documented to carry `category_display`).

Implementation is a line-based textual insertion so ALL existing formatting is preserved
byte-for-byte (the goldens use a custom serializer with inline `evidence` objects that a
plain json.dump would reflow). Idempotent: an already-present `category_display` line is
reconciled in place. JSON validity is asserted before and after.

Usage:
    python3 harness/scripts/add-ara-category-display.py            # migrate in place
    python3 harness/scripts/add-ara-category-display.py --check    # report, do not write
"""
import argparse
import glob
import json
import os
import re
import sys

# current `category` value  ->  console-canon `category_display`
CATEGORY_DISPLAY_MAP = {
    "API Surface": "API & Tooling",
    "Data Accessibility": "Data Access",
    "Engineering Maturity": "Engineering Practices",
    "State Management": "State & Memory",
    # identity mappings (already match the console canon)
    "Authentication & Authorization": "Authentication & Authorization",
    "Discovery & Documentation": "Discovery & Documentation",
    "Human-in-the-Loop": "Human-in-the-Loop",
    "Observability": "Observability",
}

GOLDEN_GLOB = "harness/golden/*-ara-report.json"

CATEGORY_RE = re.compile(r'^(?P<indent>\s*)"category":\s*"(?P<val>[^"]*)",\s*$')
CATEGORY_DISPLAY_RE = re.compile(r'^\s*"category_display":')


def migrate_text(text):
    """Return (new_text, num_inserted). Inserts/reconciles a category_display line
    directly after each dimension category line. Preserves all other formatting."""
    lines = text.split("\n")
    out = []
    inserted = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = CATEGORY_RE.match(line)
        if m and m.group("val") in CATEGORY_DISPLAY_MAP:
            indent = m.group("indent")
            display = CATEGORY_DISPLAY_MAP[m.group("val")]
            new_line = f'{indent}"category_display": "{display}",'
            # idempotency: replace an existing category_display line that follows
            if i + 1 < len(lines) and CATEGORY_DISPLAY_RE.match(lines[i + 1]):
                i += 1  # skip the stale line; emit the reconciled one
            out.append(new_line)
            inserted += 1
        i += 1
    return "\n".join(out), inserted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report changes without writing")
    args = ap.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    files = sorted(glob.glob(os.path.join(repo_root, GOLDEN_GLOB)))
    if not files:
        print(f"no golden files matched {GOLDEN_GLOB!r} under {repo_root}", file=sys.stderr)
        return 2

    total_changed = 0
    total_fields = 0
    for path in files:
        with open(path, encoding="utf-8") as fh:
            orig = fh.read()
        json.loads(orig)  # assert valid input
        new_text, inserted = migrate_text(orig)
        json.loads(new_text)  # assert valid output
        total_fields += inserted
        rel = os.path.relpath(path, repo_root)
        if new_text != orig:
            total_changed += 1
            if not args.check:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new_text)
            print(f"{'WOULD UPDATE' if args.check else 'updated'}  {rel}  (+{inserted} category_display)")
        else:
            print(f"unchanged     {rel}  ({inserted} category_display present)")

    verb = "would change" if args.check else "changed"
    print(f"\n{total_changed}/{len(files)} file(s) {verb}; {total_fields} category_display field(s) total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
