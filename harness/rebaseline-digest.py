#!/usr/bin/env python3
"""rebaseline-digest.py — render the rebaseline "whole picture" reviewer digest.

PURE RENDER. No network, no AWS, no Bedrock — it only reads two JSON files that
harness:rebaseline-gather has already produced and joins them into one markdown synthesis:

  --compare  rebaseline-compare.json   score-reports.py --compare-out  (deltas + verdicts,
                                       written on BOTH the clean and ratchet-refused paths)
  --results  rebaseline-results.json   score-reports.py -o             (per-report LLM
                                       rationale + the deterministic offline checks)

The output reproduces, deterministically, the same summary a reviewer would otherwise
hand-assemble from the gather job log:

  1. a go/no-go verdict headline (regression > partial > below-floor > clean),
  2. the was -> now -> delta score table with per-unit verdict + flags,
  3. a BELOW-FLOOR section — which reports are too ungrounded to trust, and WHY (pulled
     from the results rationale), because that is the question a below-floor score raises,
  4. the DETERMINISTIC DEFECTS — offline checks that failed (count/tier reconciliation,
     severity undercounts): these are bugs, not noise, and survive every re-roll,
  5. the within-noise caveat, so a reader does not mistake "within-noise" for "equal".

The gather job POSTs this as a note on the rebaseline MR, so the whole picture rides with
the MR instead of scrolling away in a job log. `--results` is optional: without it the
verdict + table still render (the compare JSON alone carries them); only the WHY sections
degrade to a pointer.

Usage:
  rebaseline-digest.py --compare rebaseline-compare.json \
                       [--results rebaseline-results.json] \
                       [--out rebaseline-digest.md] \
                       [--reset true|false] [--partial "$(cat .rebaseline-partial)"]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# Keep the digest scannable: a report can carry many fabrications/misses, but the MR note is
# a summary, not the full results JSON (attached as an artifact for the deep dive).
_MAX_RATIONALE_ITEMS = 3


def _truthy(s: Optional[str]) -> bool:
    return bool(s) and s.strip().lower() in {"true", "1", "yes", "on"}


def _key(row: dict) -> tuple:
    return (row.get("repo"), row.get("analysis"))


def _index_results(results: Optional[list]) -> dict[tuple, dict]:
    return {_key(r): r for r in (results or []) if isinstance(r, dict)}


def _upper(a: Any) -> str:
    return str(a or "").upper()


def _fmt_score(v: Any) -> str:
    return f"{v:.2f}" if isinstance(v, (int, float)) else "—"


# --- sections ------------------------------------------------------------------------

def _verdict(cmp: dict, *, partial: bool, reset: bool, defects: int = 0) -> tuple[str, list[str]]:
    """Deterministic headline + status lines from the compare summary.

    Precedence is worst-first, and it mirrors the ratchet's OWN gate rather than reacting to
    any single report:
      - a PARTIAL sweep or a real regression is a hard stop;
      - a MEAN below the floor is a broad-collapse stop — the average report is ungrounded;
      - a healthy mean (>= floor) is merge-safe EVEN with a few below-floor reports, because
        the floor is judged holistically: the analysis agent is nondeterministic, so one
        fixture landing a marginal draw below 0.80 is a bad roll, not a degradation. Those
        below-floor reports and any deterministic-check failures are surfaced as POTENTIAL
        ISSUES TO REVIEW (candidate TD issues), not blockers;
      - nothing below floor and no failed checks is clean.
    """
    s = cmp.get("summary", {})
    floor = cmp.get("quality_floor", 0.80)
    regressed = s.get("regressed", 0) or 0
    low_q = s.get("low_quality", 0) or 0
    stale = s.get("stale", 0) or 0
    mean_now = s.get("mean_now")

    def _potential() -> str:
        bits = []
        if low_q:
            bits.append(f"{low_q} report(s) below the {floor:.2f} floor")
        if defects:
            bits.append(f"{defects} deterministic defect(s)")
        return " and ".join(bits)

    if partial:
        head = ("🛑 **PARTIAL SWEEP — do not merge as a full re-baseline.** A shard dropped "
                "its slice, so some fixtures kept the stale baseline. Re-run the pipeline.")
    elif regressed:
        head = (f"🛑 **REGRESSION — {regressed} report(s) scored below baseline beyond noise.** "
                "A merged change may have degraded the analysis; investigate before merging.")
    elif not isinstance(mean_now, (int, float)):
        head = ("⚠️ **NOT SCORED — no groundedness scores in this sweep.** Nothing to judge; "
                "check the job log for a scoring error before merging.")
    elif mean_now < floor:
        why = " The ratchet was DISABLED (RESET)." if reset else ""
        head = (f"⚠️ **BELOW FLOOR — mean groundedness {mean_now:.3f} < {floor:.2f}.** The "
                f"average report is too ungrounded to trust across the baseline.{why} "
                "Investigate before merging.")
    else:
        potential = _potential()
        if potential:
            head = (f"✅ **OVERALL HEALTHY — mean groundedness {mean_now:.3f} ≥ {floor:.2f}, "
                    "safe to merge as a re-baseline.** Potential issues to review below "
                    f"(candidate TD issues, NOT merge blockers): {potential}.")
        else:
            head = (f"✅ **CLEAN — mean groundedness {mean_now:.3f} ≥ {floor:.2f}, every report "
                    "within-noise and above the floor.** No below-floor report, no failed check.")

    status = [
        f"- **Scores:** improved {s.get('improved', 0)} · regressed {regressed} · "
        f"within-noise {s.get('within_noise', 0)} · unscored {s.get('unscored', 0)}",
    ]
    mn, mb, md = s.get("mean_now"), s.get("mean_baseline"), s.get("mean_delta")
    if isinstance(mn, (int, float)) and isinstance(mb, (int, float)):
        tail = f" ({md:+.3f})" if isinstance(md, (int, float)) else ""
        status.append(f"- **Mean groundedness:** {mb:.3f} → {mn:.3f}{tail}")
    if low_q:
        status.append(f"- **Below the {floor:.2f} floor:** {low_q} — "
                      + ", ".join(s.get("low_quality_units") or []))
    if stale:
        status.append(f"- **Stale baseline rows:** {stale} — "
                      + ", ".join(s.get("stale_units") or []))
    if reset:
        status.append("- **Mode:** RESET (ratchet disabled — human review is the only gate)")
    return head, status


_MARK = {"improved": "▲", "regressed": "▼", "within-noise": "~", "unscored": "?"}


def _score_table(cmp: dict) -> str:
    rows = ["| repo | analysis | was | now | Δ | verdict | flags |",
            "|---|---|---:|---:|---:|---|---|"]
    for u in cmp.get("units", []):
        flags = []
        if u.get("below_quality_floor"):
            flags.append("✗ below floor")
        if u.get("baseline_stale"):
            flags.append("⚠ stale")
        v = u.get("verdict", "")
        delta = u.get("delta")
        delta_s = f"{delta:+.3f}" if isinstance(delta, (int, float)) else "—"
        rows.append(
            f"| {u.get('repo', '')} | {_upper(u.get('analysis'))} "
            f"| {_fmt_score(u.get('baseline'))} | {_fmt_score(u.get('score'))} "
            f"| {delta_s} | {_MARK.get(v, '')} {v} | {', '.join(flags)} |")
    return "\n".join(rows)


def _rationale_bullets(row: dict) -> list[str]:
    """Compressed WHY for a below-floor report, from the results-JSON rationale."""
    out = []
    summary = (row.get("summary") or "").strip()
    if summary:
        out.append(f"  - _{summary}_")
    for label, key in (("fabricated", "fabrications"), ("missed", "misses"),
                       ("deliverable", "deliverable_defects")):
        items = row.get(key) or []
        for it in items[:_MAX_RATIONALE_ITEMS]:
            text = it if isinstance(it, str) else (
                it.get("detail") or it.get("deliverable") or json.dumps(it))
            out.append(f"  - **{label}:** {str(text).strip()}")
        if len(items) > _MAX_RATIONALE_ITEMS:
            out.append(f"  - _…and {len(items) - _MAX_RATIONALE_ITEMS} more {label} item(s) "
                       "(see the results artifact)._")
    return out


def _below_floor_section(cmp: dict, ridx: dict[tuple, dict]) -> Optional[str]:
    units = [u for u in cmp.get("units", []) if u.get("below_quality_floor")]
    if not units:
        return None
    floor = cmp.get("quality_floor", 0.80)
    lines = [f"### Potential issues — reports below the {floor:.2f} floor",
             "*Individually too ungrounded to trust, independent of the delta — a report can "
             "hold steady vs a mediocre baseline and still land here. Candidate TD issues to "
             "review; not merge blockers when the overall mean is healthy.*", ""]
    for u in units:
        lines.append(f"- **{u.get('repo')} ({_upper(u.get('analysis'))}) — "
                     f"{_fmt_score(u.get('score'))}**")
        row = ridx.get(_key(u))
        if row:
            lines.extend(_rationale_bullets(row))
        else:
            lines.append("  - _(no rationale — run with `--results` for the WHY)_")
    return "\n".join(lines)


def _deterministic_defects_section(ridx: dict[tuple, dict]) -> Optional[str]:
    """Offline checks that failed. These are bugs, not draw noise — they reproduce every run,
    so they are the highest-signal thing in the digest and get called out separately from the
    (noisy) accuracy scores."""
    if not ridx:
        return None
    hits = []
    for key in sorted(ridx, key=lambda k: (str(k[1]), str(k[0]))):
        row = ridx[key]
        for c in row.get("checks_failed") or []:
            hits.append((key, c))
    if not hits:
        return None
    lines = ["### Deterministic defects (offline checks failed)",
             "*These are reproducible bugs, not accuracy noise — they survive every re-roll "
             "and are worth a TD issue.*", ""]
    for (repo, analysis), c in hits:
        name = c.get("check", "check") if isinstance(c, dict) else str(c)
        sev = c.get("severity", "") if isinstance(c, dict) else ""
        detail = c.get("detail", "") if isinstance(c, dict) else ""
        sev_s = f" _{sev}_" if sev else ""
        lines.append(f"- **{repo} ({_upper(analysis)})** — `{name}`{sev_s}: {detail}".rstrip(": "))
    return "\n".join(lines)


def _noise_note(cmp: dict) -> Optional[str]:
    if not (cmp.get("summary", {}).get("within_noise")):
        return None
    return ("> **'within-noise' means NOT MEASURED, not 'equal'.** The analysis agent moves "
            "10–20 findings per fixture per re-run; a sub-threshold delta is a different roll "
            "of the dice, not a stable result. Raise confidence with more baseline samples.")


# --- assembly ------------------------------------------------------------------------

def build_digest(cmp: dict, results: Optional[list], *,
                 partial: bool = False, reset: bool = False) -> str:
    ridx = _index_results(results)
    defects = sum(len(r.get("checks_failed") or []) for r in ridx.values())
    head, status = _verdict(cmp, partial=partial, reset=reset, defects=defects)
    parts = ["## Re-baseline digest", "", head, "", *status, "",
             "### Accuracy vs baseline", _score_table(cmp)]
    for section in (_below_floor_section(cmp, ridx),
                    _deterministic_defects_section(ridx)):
        if section:
            parts += ["", section]
    if results is None:
        parts += ["", "> _Rationale + deterministic-defect detail omitted — no results JSON "
                  "supplied. The full per-report results are attached as a job artifact._"]
    note = _noise_note(cmp)
    if note:
        parts += ["", note]
    base = cmp.get("baseline_path")
    if base:
        parts += ["", f"<sub>Baseline: `{base}` · base ref: `{cmp.get('base_ref', '?')}`. "
                  "Full deltas in `rebaseline-compare.json`, per-report results in "
                  "`rebaseline-results.json` (job artifacts).</sub>"]
    return "\n".join(parts) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Render the rebaseline whole-picture digest.")
    ap.add_argument("--compare", type=Path, required=True,
                    help="rebaseline-compare.json (score-reports.py --compare-out)")
    ap.add_argument("--results", type=Path, default=None,
                    help="rebaseline-results.json (score-reports.py -o); optional")
    ap.add_argument("--out", type=Path, default=None,
                    help="write markdown here (also always printed to stdout)")
    ap.add_argument("--partial", default="",
                    help="non-empty (e.g. the .rebaseline-partial marker) => PARTIAL sweep")
    ap.add_argument("--reset", default="false", help="true => RESET run (ratchet was disabled)")
    args = ap.parse_args()

    if not args.compare.exists():
        print(f"rebaseline-digest: compare file not found: {args.compare}", file=sys.stderr)
        return 2
    cmp = json.loads(args.compare.read_text(encoding="utf-8"))
    results = None
    if args.results and args.results.exists():
        results = json.loads(args.results.read_text(encoding="utf-8"))
    elif args.results:
        print(f"rebaseline-digest: results file not found: {args.results} — "
              "rendering verdict + table only.", file=sys.stderr)

    md = build_digest(cmp, results,
                      partial=_truthy(args.partial), reset=_truthy(args.reset))
    if args.out:
        args.out.write_text(md, encoding="utf-8")
        print(f"rebaseline-digest: wrote {args.out}", file=sys.stderr)
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
