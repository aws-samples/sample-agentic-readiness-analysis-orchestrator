#!/usr/bin/env python3
"""
diff-reports.py — deterministic before/after differ for the change-impact harness.

Compares committed golden reports (the "before") against freshly produced reports
(the "after") and emits a structured `impact.json` describing the delta across the
five scored dimensions (see harness/DESIGN.md §3, §5, §12):

  D1  Findings          — ARA + MOD, per-repo + portfolio  (added / removed / reseveritied)
  D2  Classification    — ARA + MOD tier (per-repo) + distribution (portfolio)
  D3  Pathways          — MOD only, per-repo + portfolio (newly triggered / suppressed)
  D4  Programs          — portfolio only, ARA + MOD (recommended_actions[] + pathway programs)
  D5  MOD numeric score — MOD only; BAND-CROSSING only (score_rating band boundary)

This step is pure Python — NO ATX, NO LLM, NO network. It is the ATX-free core and is
unit-tested against examples/reports/full-analysis/. The LLM judge (judge.py) consumes
the impact.json this produces.

Report field-path quirks handled (verified against real artifacts, DESIGN.md §12):
  - portfolio findings add `repo_name`; match on (repo_name, question_id)
  - portfolio MOD findings drop description/gap/recommendation (leaner than per-repo)
  - per-repo ARA nests native_severity/safety_impact under `ara_metadata`;
    portfolio ARA promotes them to top level
  - pathways use `status` (per-repo) vs `portfolio_status` (portfolio)
  - ARA readiness_distribution = {count,percentage}; MOD tier/score distributions = flat ints
  - per-repo MOD score = categories[].numeric_score; portfolio = category_score_averages[].average
  - evidence may be null or {file, lines}; lines may be null

Usage:
  diff-reports.py --baseline harness/golden --after <dir> [-o impact.json]
  diff-reports.py --baseline <before_dir> --after <after_dir>    # any two report trees

A "report tree" is a directory containing report JSON files named:
  <repo>-ara-report.json                 (per-repo ARA)
  <repo>-mod-report.json                 (per-repo MOD)
  <portfolio>-portfolio-ara-report.json  (portfolio ARA)
  <portfolio>-portfolio-mod-report.json  (portfolio MOD)
Nested subdirectories are searched recursively.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# --- score_rating bands, ordered low→high. Band-crossing detection uses the index. -----
SCORE_BANDS = ["Not Ready", "Needs Work", "Partial", "Mature"]
_BAND_INDEX = {b: i for i, b in enumerate(SCORE_BANDS)}


# ---------------------------------------------------------------------------------------
# Report tree loading / classification
# ---------------------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def classify_report(path: Path, data: dict) -> Optional[tuple[str, str, str]]:
    """Return (analysis, scope, key) or None if not a managed-TD report we diff.

    analysis: "ara" | "mod"
    scope:    "repo" | "portfolio"
    key:      repo_name (repo scope) or portfolio/assessment id (portfolio scope)
    """
    name = path.name.lower()
    if not name.endswith(".json") or name.endswith(".metadata.json"):
        return None

    # Portfolio reports carry `repositories[]` + `assessment_type`; per-repo carry `repo_name`.
    is_portfolio = "repositories" in data and "repo_name" not in data

    if "-ara-report" in name or _is_ara(data):
        analysis = "ara"
    elif "-mod-report" in name or _is_mod(data):
        analysis = "mod"
    else:
        return None

    if is_portfolio:
        key = (data.get("metadata", {}) or {}).get("portfolio_name") \
            or _strip_suffixes(path.name)
        return analysis, "portfolio", key
    key = data.get("repo_name") or _strip_suffixes(path.name)
    return analysis, "repo", key


def _is_ara(data: dict) -> bool:
    at = str(data.get("analysis_type") or data.get("assessment_type") or "").lower()
    return "agentic" in at or "ara" in at


def _is_mod(data: dict) -> bool:
    at = str(data.get("analysis_type") or data.get("assessment_type") or "").lower()
    return "modern" in at or "mod" in at


def _strip_suffixes(filename: str) -> str:
    stem = filename
    for suf in ("-portfolio-ara-report.json", "-portfolio-mod-report.json",
                "-ara-report.json", "-mod-report.json", ".json"):
        if stem.endswith(suf):
            return stem[: -len(suf)]
    return stem


def load_tree(root: Path) -> dict[tuple[str, str, str], dict]:
    """Index every managed report under `root` by (analysis, scope, key)."""
    tree: dict[tuple[str, str, str], dict] = {}
    if not root.exists():
        return tree
    for path in sorted(root.rglob("*.json")):
        try:
            data = _load_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        ident = classify_report(path, data)
        if ident is None:
            continue
        # First writer wins; report trees shouldn't contain duplicate identities, but if a
        # repo report is mirrored under services/ AND full-analysis/, prefer the shorter path.
        if ident not in tree:
            tree[ident] = data
    return tree


# ---------------------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------------------

def _finding_key(f: dict) -> str:
    """Stable identity for a finding within one report scope."""
    return str(f.get("question_id") or f.get("title") or id(f))


def _finding_index(findings: list[dict]) -> dict[str, dict]:
    return {_finding_key(f): f for f in (findings or [])}


def _native_severity(f: dict) -> Optional[str]:
    """native_severity is top-level in portfolio ARA but nested in per-repo ARA."""
    if "native_severity" in f:
        return f.get("native_severity")
    meta = f.get("ara_metadata") or {}
    return meta.get("native_severity")


def _band_of(score_rating: Optional[str]) -> Optional[int]:
    if score_rating is None:
        return None
    return _BAND_INDEX.get(str(score_rating).strip())


# ---------------------------------------------------------------------------------------
# D1 — findings delta
# ---------------------------------------------------------------------------------------

def diff_findings(before: dict, after: dict) -> dict:
    b_idx = _finding_index(before.get("findings"))
    a_idx = _finding_index(after.get("findings"))

    added = sorted(set(a_idx) - set(b_idx))
    removed = sorted(set(b_idx) - set(a_idx))

    reseveritied = []
    for qid in sorted(set(a_idx) & set(b_idx)):
        bs, as_ = b_idx[qid].get("severity"), a_idx[qid].get("severity")
        bn, an = _native_severity(b_idx[qid]), _native_severity(a_idx[qid])
        if bs != as_ or bn != an:
            reseveritied.append({
                "question_id": qid,
                "severity": {"before": bs, "after": as_},
                "native_severity": {"before": bn, "after": an},
            })

    return {
        "added": added,
        "removed": removed,
        "reseveritied": reseveritied,
        "count": {"before": len(b_idx), "after": len(a_idx)},
    }


# ---------------------------------------------------------------------------------------
# D2 — classification tier / distribution
# ---------------------------------------------------------------------------------------

def diff_tier_repo(before: dict, after: dict, analysis: str) -> dict:
    bc = before.get("classification", {}) or {}
    ac = after.get("classification", {}) or {}
    out = {
        "before": bc.get("tier"),
        "after": ac.get("tier"),
        "changed": bc.get("tier") != ac.get("tier"),
        "rule_matched": {"before": bc.get("rule_matched"), "after": ac.get("rule_matched")},
    }
    if analysis == "ara":
        out["blocker_count"] = {"before": bc.get("blocker_count"), "after": ac.get("blocker_count")}
        out["risk_safety_count"] = {
            "before": bc.get("risk_safety_count"), "after": ac.get("risk_safety_count")}
    else:
        for f in ("high_count", "medium_count", "low_count"):
            out[f] = {"before": bc.get(f), "after": ac.get(f)}
    return out


def diff_distribution(before: dict, after: dict, analysis: str) -> dict:
    """Portfolio-level tier distribution. ARA = {count,percentage}; MOD = flat ints."""
    bed = before.get("executive_dashboard", {}) or {}
    aed = after.get("executive_dashboard", {}) or {}
    field = "readiness_distribution" if analysis == "ara" else "tier_distribution"
    bd, ad = bed.get(field, {}) or {}, aed.get(field, {}) or {}

    changes = {}
    for tier in sorted(set(bd) | set(ad)):
        bv, av = _dist_count(bd.get(tier)), _dist_count(ad.get(tier))
        if bv != av:
            changes[tier] = {"before": bv, "after": av}
    return {"field": field, "changed": bool(changes), "by_tier": changes}


def _dist_count(v: Any) -> Optional[int]:
    if isinstance(v, dict):
        return v.get("count")
    return v


# ---------------------------------------------------------------------------------------
# D3 — pathways (MOD only)
# ---------------------------------------------------------------------------------------

def _pathway_status_map(report: dict) -> dict[str, str]:
    out = {}
    for p in report.get("pathways", []) or []:
        status = p.get("status", p.get("portfolio_status"))  # per-repo vs portfolio
        pid = p.get("id") or p.get("name")
        if pid is not None:
            out[pid] = status
    return out


def diff_pathways(before: dict, after: dict) -> dict:
    b_map = _pathway_status_map(before)
    a_map = _pathway_status_map(after)

    def _triggered(s: Optional[str]) -> bool:
        return str(s).strip().lower() == "triggered"

    newly_triggered, newly_suppressed = [], []
    for pid in sorted(set(a_map) | set(b_map)):
        was, now = _triggered(b_map.get(pid)), _triggered(a_map.get(pid))
        if now and not was:
            newly_triggered.append(pid)
        elif was and not now:
            newly_suppressed.append(pid)
    return {"newly_triggered": newly_triggered, "newly_suppressed": newly_suppressed}


# ---------------------------------------------------------------------------------------
# D4 — programs (portfolio only)
# ---------------------------------------------------------------------------------------

def _program_status_map(report: dict) -> dict[str, str]:
    """acronym -> status from recommended_actions[], plus pathway recommended_aws_programs."""
    out: dict[str, str] = {}
    for a in report.get("recommended_actions", []) or []:
        acr = a.get("acronym")
        if acr is None:
            continue  # per-repo remediation actions have no acronym — skip
        out[acr] = a.get("status", "Triggered")
    # MOD portfolio also lists programs per triggered pathway.
    for p in report.get("pathways", []) or []:
        status = str(p.get("portfolio_status", p.get("status"))).strip().lower()
        if status != "triggered":
            continue
        for prog in p.get("recommended_aws_programs", []) or []:
            out.setdefault(_short_program(prog), "Triggered")
    return out


def _short_program(name: str) -> str:
    """'Experience-Based Acceleration (EBA)' -> 'EBA'; else return as-is."""
    if "(" in name and name.rstrip().endswith(")"):
        return name[name.rindex("(") + 1: -1].strip()
    return name.strip()


def diff_programs(before: dict, after: dict) -> dict:
    b_map = _program_status_map(before)
    a_map = _program_status_map(after)

    def _on(s: Optional[str]) -> bool:
        return str(s).strip().lower() == "triggered"

    added, removed = [], []
    for acr in sorted(set(a_map) | set(b_map)):
        if _on(a_map.get(acr)) and not _on(b_map.get(acr)):
            added.append(acr)
        elif _on(b_map.get(acr)) and not _on(a_map.get(acr)):
            removed.append(acr)
    return {"added": added, "removed": removed}


# ---------------------------------------------------------------------------------------
# D5 — MOD numeric score (band-crossing only)
# ---------------------------------------------------------------------------------------

def diff_score_repo(before: dict, after: dict) -> dict:
    """Per-repo MOD: overall_score band + per-category score_rating band crossings."""
    b_overall = before.get("overall_score")
    a_overall = after.get("overall_score")
    b_bands = _repo_category_bands(before)
    a_bands = _repo_category_bands(after)

    overall = {
        "before": b_overall,
        "after": a_overall,
        "band_before": _overall_band_label(b_overall),
        "band_after": _overall_band_label(a_overall),
    }
    overall["band_crossed"] = overall["band_before"] != overall["band_after"]

    categories = {}
    for cat in sorted(set(b_bands) | set(a_bands)):
        bb, ab = b_bands.get(cat), a_bands.get(cat)
        if bb != ab:
            categories[cat] = {"band_before": bb, "band_after": ab, "band_crossed": True}
    return {"overall": overall, "categories": categories}


def _repo_category_bands(report: dict) -> dict[str, Optional[str]]:
    return {c.get("category_id"): c.get("score_rating")
            for c in report.get("categories", []) or [] if c.get("category_id")}


# Overall numeric scores don't carry an explicit band; derive from thresholds aligned to
# the same 4 bands. Boundaries at 1/2/3 on the 0–4 scale (kept simple + documented).
def _overall_band_label(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    try:
        s = float(score)
    except (TypeError, ValueError):
        return None
    if s < 1.0:
        return "Not Ready"
    if s < 2.0:
        return "Needs Work"
    if s < 3.0:
        return "Partial"
    return "Mature"


def diff_score_portfolio(before: dict, after: dict) -> dict:
    bed = (before.get("executive_dashboard", {}) or {})
    aed = (after.get("executive_dashboard", {}) or {})
    b_over = (bed.get("portfolio_score_overview", {}) or {}).get("portfolio_overall_score")
    a_over = (aed.get("portfolio_score_overview", {}) or {}).get("portfolio_overall_score")

    b_dist = bed.get("score_band_distribution", {}) or {}
    a_dist = aed.get("score_band_distribution", {}) or {}
    shift = {}
    for band in ("mature", "partial", "needs_work", "not_ready"):
        bv, av = b_dist.get(band, 0) or 0, a_dist.get(band, 0) or 0
        if bv != av:
            shift[band] = av - bv

    band_before = _overall_band_label(b_over)
    band_after = _overall_band_label(a_over)
    return {
        "before": b_over,
        "after": a_over,
        "band_before": band_before,
        "band_after": band_after,
        "band_crossed": band_before != band_after,
        "band_distribution_shift": shift,
    }


# ---------------------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------------------

def _nonempty_findings(d: dict) -> bool:
    return bool(d["added"] or d["removed"] or d["reseveritied"])


def build_impact(before_tree: dict, after_tree: dict) -> dict:
    per_repo: dict[str, dict] = {}
    portfolio: dict[str, dict] = {}

    all_keys = set(before_tree) | set(after_tree)
    changed_tds: set[str] = set()

    for (analysis, scope, key) in sorted(all_keys):
        before = before_tree.get((analysis, scope, key), {})
        after = after_tree.get((analysis, scope, key), {})

        if scope == "repo":
            entry = per_repo.setdefault(key, {})
            fd = diff_findings(before, after)
            td = diff_tier_repo(before, after, analysis)
            entry[f"D1_{analysis}_findings"] = fd
            entry[f"D2_{analysis}_tier"] = td
            moved = _nonempty_findings(fd) or td["changed"]
            if analysis == "mod":
                pw = diff_pathways(before, after)
                sc = diff_score_repo(before, after)
                entry["D3_mod_pathways_repo"] = pw
                entry["D5_mod_score"] = sc
                moved = moved or pw["newly_triggered"] or pw["newly_suppressed"] \
                    or sc["overall"]["band_crossed"] or bool(sc["categories"])
            if moved:
                changed_tds.add(_td_name(analysis, scope))
        else:  # portfolio
            entry = portfolio.setdefault(analysis, {})
            fd = diff_findings(before, after)
            dist = diff_distribution(before, after, analysis)
            prog = diff_programs(before, after)
            entry["D1_findings"] = fd
            entry["D2_distribution"] = dist
            entry["D4_programs"] = prog
            moved = _nonempty_findings(fd) or dist["changed"] or prog["added"] or prog["removed"]
            if analysis == "mod":
                pw = diff_pathways(before, after)
                sc = diff_score_portfolio(before, after)
                entry["D3_pathways"] = pw
                entry["D5_portfolio_score"] = sc
                moved = moved or pw["newly_triggered"] or pw["newly_suppressed"] \
                    or sc["band_crossed"] or bool(sc["band_distribution_shift"])
            if moved:
                changed_tds.add(_td_name(analysis, scope))

    impact = {
        "changed_tds": sorted(changed_tds),
        "per_repo": per_repo,
        "portfolio": portfolio,
    }
    impact["no_op"] = not changed_tds
    return impact


def _td_name(analysis: str, scope: str) -> str:
    base = "agentic-readiness-analysis" if analysis == "ara" else "modernization-readiness-analysis"
    return f"portfolio-{base}" if scope == "portfolio" else base


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Diff before/after managed-TD reports → impact.json")
    ap.add_argument("--baseline", required=True, type=Path,
                    help="Directory of 'before' reports (e.g. harness/golden)")
    ap.add_argument("--after", required=True, type=Path,
                    help="Directory of 'after' reports (freshly produced)")
    ap.add_argument("-o", "--out", type=Path, default=None,
                    help="Write impact.json here (default: stdout)")
    args = ap.parse_args(argv)

    before_tree = load_tree(args.baseline)
    after_tree = load_tree(args.after)

    if not before_tree and not after_tree:
        print(f"error: no managed reports found under {args.baseline} or {args.after}",
              file=sys.stderr)
        return 2

    impact = build_impact(before_tree, after_tree)
    text = json.dumps(impact, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}  (no_op={impact['no_op']}, changed_tds={impact['changed_tds']})",
              file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
