#!/usr/bin/env python3
"""
patch-mod-findings.py — restore the top-level `findings[]` array in MOD report JSON.

atx CT ≥ 3.7.0 modernization-readiness reports moved findings under
`pathways[].findings[]` and dropped the top-level `findings[]` array. The CT
`parseModReport` step still looks for a top-level `findings[]`; when it's absent
it logs `json_missing_findings_array` and falls back to markdown — so findings
"disappear" from JSON consumers (portfolio aggregation, HTML regeneration, any
tool that reads the sibling JSON).

This script flattens `pathways[].findings[]` into a synthesized top-level
`findings[]`, preserving the per-record fields and attributing each to its
pathway. It is IDEMPOTENT: a report that already has a non-empty top-level
`findings[]` is left untouched (unless --force).

Record mapping (MOD pathway finding {id, finding, severity, effort} → top-level):
    id          -> id            (prefixed with pathway index if not unique)
    severity    -> severity
    finding     -> title AND description  (the parser/renderers key on title)
    effort      -> effort         (preserved)
    <pathway>   -> pathway, category

Usage:
    patch-mod-findings.py <file-or-dir> [<file-or-dir> ...] [--force] [--dry-run]
    # dir args are scanned for *-mod-report.json (non-recursive by default; -r to recurse)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _pathway_findings(data: dict) -> list[dict]:
    """Return every pathway-nested finding as a flat list of enriched records."""
    out: list[dict] = []
    pathways = data.get("pathways") or data.get("modernization_pathways") or []
    if not isinstance(pathways, list):
        return out
    seen_ids: set[str] = set()
    for pw in pathways:
        if not isinstance(pw, dict):
            continue
        pname = pw.get("name") or pw.get("id") or pw.get("pathway") or "unknown-pathway"
        for raw in (pw.get("findings") or []):
            if not isinstance(raw, dict):
                continue
            text = raw.get("finding") or raw.get("title") or raw.get("description") or ""
            fid = str(raw.get("id") or raw.get("question_id") or "").strip()
            # Guarantee a unique, stable id (pathway findings often share "1.1"/"2.1"…).
            if not fid or fid in seen_ids:
                fid = f"{pname}:{fid or len(out)}"
            seen_ids.add(fid)
            rec = {
                "id": fid,
                "severity": raw.get("severity"),
                "title": text,
                "description": text,
                "pathway": pname,
                "category": pname,
            }
            if "effort" in raw:
                rec["effort"] = raw.get("effort")
            out.append(rec)
    return out


def patch_report(data: dict, *, force: bool = False) -> tuple[dict, int]:
    """Return (patched_data, n_added). n_added==0 means no change was made."""
    existing = data.get("findings")
    if isinstance(existing, list) and existing and not force:
        return data, 0  # already has a usable top-level array
    flat = _pathway_findings(data)
    if not flat:
        return data, 0  # nothing to synthesize (not a pathway-nested MOD report)
    data["findings"] = flat
    return data, len(flat)


def _iter_targets(paths: list[Path], recurse: bool) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            globber = p.rglob if recurse else p.glob
            files.extend(sorted(globber("*-mod-report.json")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"warn: skipping missing path {p}", file=sys.stderr)
    return files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Restore top-level findings[] in MOD reports")
    ap.add_argument("paths", nargs="+", type=Path, help="MOD report file(s) or dir(s)")
    ap.add_argument("--force", action="store_true",
                    help="Re-synthesize even if a top-level findings[] already exists")
    ap.add_argument("--dry-run", action="store_true", help="Report what would change; write nothing")
    ap.add_argument("-r", "--recurse", action="store_true", help="Recurse into directories")
    args = ap.parse_args(argv)

    targets = _iter_targets(args.paths, args.recurse)
    if not targets:
        print("no MOD report files found", file=sys.stderr)
        return 1

    changed = skipped = 0
    for f in targets:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"warn: cannot read {f}: {exc}", file=sys.stderr)
            continue
        _, n = patch_report(data, force=args.force)
        if n == 0:
            skipped += 1
            continue
        changed += 1
        if args.dry_run:
            print(f"[dry-run] {f.name}: would add {n} top-level findings")
        else:
            f.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"patched  {f.name}: +{n} top-level findings (from pathways)")
    print(f"\n{changed} patched, {skipped} unchanged", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
