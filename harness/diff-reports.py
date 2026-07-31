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
unit-tested against the committed harness/golden/ baseline. The LLM judge (judge.py)
consumes the impact.json this produces.

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
import re
import sys
from pathlib import Path
from typing import Any, Optional

# Shared read of the managed TDs' severity tables — the SAME parse the judge prompt uses,
# so "was this BLOCKER correct?" is answered from the rubric, not re-transcribed here.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_table import is_over_escalation_correction, mod_band  # noqa: E402

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

    # Portfolio vs per-repo discrimination. Two schema generations seen in the wild:
    #   old (committed example): portfolio has `repositories[]`, per-repo has `repo_name`.
    #   atx CT 3.7.0: portfolio has `portfolio_name` + `report_type`/`services`/
    #     `services_analyzed`/`pathway_aggregation`; per-repo has none of these and is
    #     identified by the `-portfolio-` / `portfolio-` filename or the absence of repo keys.
    # A per-repo report never carries `portfolio_name`, so treat any of these as portfolio.
    _PORTFOLIO_MARKERS = ("repositories", "portfolio_name", "report_type", "services",
                          "services_analyzed", "pathway_aggregation",
                          "classification_tier_distribution", "portfolio_findings_summary")
    is_portfolio = (
        ("portfolio" in name and "repo_name" not in data)
        or (any(k in data for k in _PORTFOLIO_MARKERS) and "repo_name" not in data)
    )

    if "-ara-report" in name or _is_ara(data):
        analysis = "ara"
    elif "-mod-report" in name or _is_mod(data):
        analysis = "mod"
    else:
        return None

    if is_portfolio:
        # 3.7.0 puts portfolio_name at top level; older reports nested it under metadata.
        key = data.get("portfolio_name") \
            or (data.get("metadata", {}) or {}).get("portfolio_name") \
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
# Shape normalizer
# ---------------------------------------------------------------------------------------
#
# ATX CT 3.7.0 report JSON has NO stable schema — the same analysis type serializes
# differently per repo (verified against real artifacts, 2026-07-29). The differ core
# (D1–D5) expects ONE contract: a flat `findings` list keyed on `question_id`, and a
# flat `pathways` list of {id, status}. This layer maps every observed shape onto that
# contract and is called once per report in build_impact(), so the diff functions stay
# shape-agnostic. Unrecognized structure degrades to [] (logged), never raises.
#
# ARA `findings` shapes observed:
#   A1  dict keyed by camelCase category -> [ {id, severity, title, description} ]   (shipping-api)
#   A2  no `findings`; `categories` LIST of {name, findings:[{severity,title,desc}]} (storefront — findings carry NO id)
#   A3  no `findings`; `categories` DICT of {score, findings:[{id,severity,desc}]}   (loan-calculator)
#   A4  flat `findings` LIST of {id, severity, category, title, description}          (partner-soap)
#   plus cross-cutting arrays (crossCuttingSecurityConcerns / security_findings /
#        security_vulnerabilities) holding real findings NOT in the category buckets.
#
# MOD findings live inside pathways. Pathway shapes observed:
#   M1  `pathways` LIST of {name, severity_status, score_rating, findings:[{id,severity,effort,finding}]}  (shipping)
#   M2  `pathways` DICT of {finding_count, high_findings, ...} counts-only, NO nested findings            (storefront;
#        findings surface in top-level security_findings dict of counts)
#   M3  `pathways` DICT of {score_rating, findings:[{id,finding,severity,effort,description}]}            (loan)
#   M4  key `modernization_pathways` LIST of {pathway, score_rating, findings:[{id,title,severity,...}]}  (partner-soap)

_ARA_CROSSCUT_KEYS = ("crossCuttingSecurityConcerns", "security_findings",
                      "security_vulnerabilities", "crossCuttingSecurity")
_MOD_PATHWAY_KEYS = ("pathways", "modernization_pathways")


def _slug(text: Any) -> str:
    """Collapse a name to a case/punctuation-insensitive token for cross-shape matching.
    'Move to Cloud Native' / 'move_to_cloud_native' -> 'movetocloudnative'."""
    return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())


def _canon_finding(raw: dict, *, category: Optional[str] = None,
                   seq: Optional[int] = None) -> dict:
    """Map a raw finding record onto the canonical contract.

    Identity precedence: explicit id/question_id > title > (category, seq) fallback so
    two id-less findings in the same bucket stay distinct and stable across before/after.
    """
    fid = raw.get("question_id") or raw.get("id")
    title = raw.get("title") or raw.get("finding") or raw.get("name")
    cat = raw.get("category") or category
    if fid is None:
        fid = title or (f"{_slug(cat)}#{seq}" if cat is not None and seq is not None
                        else f"anon#{seq}")
    return {
        "question_id": str(fid),
        "severity": raw.get("severity"),
        # native_severity may be top-level, nested in ara_metadata, or absent.
        "native_severity": _native_severity(raw),
        "title": title,
        "category": cat,
        "description": raw.get("description") or raw.get("finding"),
    }


def _extract_ara_findings(data: dict) -> list[dict]:
    out: list[dict] = []
    findings = data.get("findings")

    if isinstance(findings, list):                         # A4: flat list
        out.extend(_canon_finding(f, seq=i) for i, f in enumerate(findings)
                   if isinstance(f, dict))
    elif isinstance(findings, dict):                       # A1: dict keyed by category
        for cat, bucket in findings.items():
            if isinstance(bucket, list):
                out.extend(_canon_finding(f, category=cat, seq=i)
                           for i, f in enumerate(bucket) if isinstance(f, dict))

    cats = data.get("categories")
    if isinstance(cats, list):                             # A2: categories LIST of {name, findings}
        for c in cats:
            if not isinstance(c, dict):
                continue
            cat = c.get("name") or c.get("category_id") or c.get("category")
            for i, f in enumerate(c.get("findings") or []):
                if isinstance(f, dict):
                    out.append(_canon_finding(f, category=cat, seq=i))
    elif isinstance(cats, dict):                           # A3: categories DICT keyed by id
        for cat, c in cats.items():
            if not isinstance(c, dict):
                continue
            for i, f in enumerate(c.get("findings") or []):
                if isinstance(f, dict):
                    out.append(_canon_finding(f, category=cat, seq=i))

    # Cross-cutting security findings live outside the category buckets. Only lists carry
    # real records; count-only dicts (e.g. {high_count: 7}) are summaries — skip them.
    for k in _ARA_CROSSCUT_KEYS:
        arr = data.get(k)
        if isinstance(arr, list):
            out.extend(_canon_finding(f, category=k, seq=i)
                       for i, f in enumerate(arr) if isinstance(f, dict))

    return _dedupe_findings(out)


def _mod_pathway_entries(data: dict) -> list[tuple[str, dict]]:
    """Return [(pathway_slug, entry_dict)] across the list/dict/alt-key shapes."""
    for key in _MOD_PATHWAY_KEYS:
        pw = data.get(key)
        if isinstance(pw, list):                           # M1 / M4
            out = []
            for p in pw:
                if isinstance(p, dict):
                    name = p.get("name") or p.get("pathway") or p.get("id")
                    out.append((_slug(name), p))
            return out
        if isinstance(pw, dict):                           # M2 / M3
            return [(_slug(name), p) for name, p in pw.items() if isinstance(p, dict)]
    return []


def _extract_mod_findings(data: dict) -> list[dict]:
    out: list[dict] = []
    # M0 (committed example / portfolio): flat top-level findings list, pathways separate.
    top = data.get("findings")
    if isinstance(top, list):
        out.extend(_canon_finding(f, seq=i) for i, f in enumerate(top)
                   if isinstance(f, dict))
    # M1/M3/M4: findings nested inside each pathway entry.
    for slug, entry in _mod_pathway_entries(data):
        for i, f in enumerate(entry.get("findings") or []):
            if isinstance(f, dict):
                out.append(_canon_finding(f, category=slug, seq=i))
    # M2 has no nested findings anywhere (only counts) — nothing to extract; D3 still
    # sees the pathway via _extract_pathways below.
    return _dedupe_findings(out)


def _extract_pathways(data: dict) -> list[dict]:
    """Canonical pathway list of {id, status}. A pathway is 'triggered' when it carries
    findings or a non-zero finding_count, unless an explicit status says otherwise."""
    out = []
    for slug, entry in _mod_pathway_entries(data):
        explicit = entry.get("status") or entry.get("portfolio_status")
        if explicit is not None:
            status = str(explicit)
        else:
            n = entry.get("finding_count")
            has = (n or 0) > 0 if isinstance(n, (int, float)) else bool(entry.get("findings"))
            status = "triggered" if has else "not_triggered"
        out.append({"id": slug, "status": status,
                    "name": entry.get("name") or entry.get("pathway"),
                    # passthrough for D4 (portfolio program recommendations)
                    "recommended_aws_programs": entry.get("recommended_aws_programs", []),
                    "portfolio_status": entry.get("portfolio_status")})
    return out


def _dedupe_findings(findings: list[dict]) -> list[dict]:
    """Collapse records that share a question_id (same finding surfaced in two buckets)."""
    seen: dict[str, dict] = {}
    for f in findings:
        seen.setdefault(f["question_id"], f)
    return list(seen.values())


def normalize_report(analysis: str, data: dict) -> dict:
    """Return a shallow copy of `data` with canonical `findings` and (MOD) `pathways`.

    Every other top-level key (classification, categories, executive_dashboard,
    overall_score, …) is left untouched so D2/D5 keep reading them directly.
    """
    if not isinstance(data, dict):
        return {}
    norm = dict(data)
    if analysis == "ara":
        norm["findings"] = _extract_ara_findings(data)
    else:
        norm["findings"] = _extract_mod_findings(data)
        norm["pathways"] = _extract_pathways(data)
    return norm


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


# Overall numeric scores don't carry an explicit band; derive it. This MUST use the same
# boundaries as skill_table.mod_band, which are parsed from the TD (MOD SKILL.md:1579-1582,
# 2014): 3.5 / 2.5 / 1.5 on the 1-4 scale. An earlier local copy here banded at 1/2/3
# "kept simple" — a second, WRONG implementation of a TD threshold. It mislabeled 9 of 14
# golden MOD fixtures (every score in 1.0-1.49 read "Needs Work" when the TD says "Not
# Ready", and a 3.3 read "Mature" when the TD says "Partial"), so band_crossed both invented
# crossings the TD does not have (1.9->2.1) and missed real ones (1.15->1.55), feeding a
# wrong `moved` flag and a wrong D5 judge highlight. Never re-inline the thresholds; a band
# boundary has exactly one home, and it is the TD parse.
def _overall_band_label(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    try:
        s = float(score)
    except (TypeError, ValueError):
        return None
    return mod_band(s)


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


# ---------------------------------------------------------------------------------------
# SAFETY ALERTS — deterministic, computed here rather than judged by the LLM
# ---------------------------------------------------------------------------------------
# WHY THIS IS NOT THE JUDGE'S JOB: on MR !14 the delta moved
# `AUTH-Q5 BLOCKER -> RISK-SAFETY` in legacy-loan-calculator, which dropped
# blocker_count 3 -> 2 and moved the ARA tier `Not Agent-Integrable -> Remediation
# Required`. The judge was told (correctly) that movement outside the edited questions is
# nondeterministic noise, AUTH-Q5 was outside the edit scope, so it filed a genuine tier
# regression as "likely noise" and still returned LGTM.
#
# That is not a prompt bug to be tuned away. Some facts are ARITHMETIC, not judgement:
# the ARA rubric states `blocker_count >= 3 -> Not Agent-Integrable` and `1-2 ->
# Remediation Required`, so a lost BLOCKER *mechanically* relaxes the tier. A fixture
# becoming "safer to hand to an agent" is the single claim that most deserves scrutiny,
# and it must not depend on an LLM choosing to mention it.
#
# So these are computed deterministically and REGARDLESS OF EDIT SCOPE. Scope explains
# findings churn; it never excuses a blocker disappearing. The judge still gets them, but
# as facts it must address rather than evidence it may weigh away.
#
# Direction matters: severity classes are ordered, and only movement toward LESS severe
# is alarming. A question GAINING a blocker is the rubric getting stricter — worth noting,
# never a safety alert.
_ARA_SEVERITY_RANK = {"BLOCKER": 3, "RISK-SAFETY": 2, "RISK-QUALITY": 1, "INFO": 0}

# ARA tiers ordered least -> most permissive for an agent. A move DOWN this list means the
# analysis now considers the system more agent-ready, which is the direction that needs a
# causal explanation.
_ARA_TIER_RANK = {
    "Not Agent-Integrable": 0,
    "Remediation Required": 1,
    "Pilot-Ready (Safety Concerns)": 2,
    "Pilot-Ready": 3,
    "Agent-Ready": 4,
}


def _severity_relaxed(before: Optional[str], after: Optional[str]) -> bool:
    """True when `after` is a strictly LESS severe ARA class than `before`."""
    b = _ARA_SEVERITY_RANK.get(str(before or "").strip().upper())
    a = _ARA_SEVERITY_RANK.get(str(after or "").strip().upper())
    if b is None or a is None:
        return False
    return a < b


def _tier_relaxed(before: Optional[str], after: Optional[str]) -> Optional[bool]:
    """True when the tier moved toward MORE agent-ready. None if unrecognised/unchanged."""
    b = _ARA_TIER_RANK.get(str(before or "").strip())
    a = _ARA_TIER_RANK.get(str(after or "").strip())
    if b is None or a is None or a == b:
        return None
    return a > b


def safety_alerts(repo: str, analysis: str, findings: dict, tier: dict,
                  changed_qids: Optional[set[str]] = None) -> list[dict]:
    """Deterministic safety-material alerts for one (repo, analysis) pair.

    Returns a list of dicts, each naming the specific movement and — where the rubric makes
    it mechanical — the causal link between them, so a reader does not have to rediscover
    that "blocker lost" and "tier relaxed" are the same event.

    `changed_qids` is the set of question ids whose documented severity/conditional row was
    edited in THIS MR (from `skill_table.diff_severity_tables`, resolved in the shell layer
    that owns the merge base — this file stays git-free and offline). A qid in that set is
    barred from the over-escalation-correction exemption below: the exemption assumes the
    report over-stated against a STABLE table, and an MR that moved the table in the same
    change cannot claim its report merely "corrected" toward it. Defaults to None so the
    committed-baseline tests, which have no MR diff, see the prior behaviour unchanged.
    """
    alerts: list[dict] = []
    if analysis != "ara":
        # MOD has no BLOCKER class and no agent-readiness tier; its D5 band crossing is
        # already surfaced separately. Nothing rubric-mechanical to assert here.
        return alerts

    # TIER-MATERIAL vs MERELY NOTABLE. Every alert is reported, but only tier-material ones
    # force a hold, and the distinction is load-bearing rather than cosmetic.
    #
    # The tier rules read blocker_count FIRST: while blocker_count > 0 the risk_safety_count
    # does not affect the tier at all. All 11 ARA fixtures currently sit at blocker_count
    # 1-3 with risk_safety_count 3-11, and that second number drifts by several findings on
    # every nondeterministic rerun. So treating any risk_safety movement as a hold would
    # trip on essentially every MR — and a gate that always fires is a gate nobody reads,
    # which is precisely how the AUTH-Q5 regression got waved through in the first place.
    #
    # Once blocker_count reaches 0, risk_safety_count becomes the sole tier driver (and the
    # 1 -> 0 step is what declares a repo Agent-Ready), so it is tier-material exactly then.
    bc_after = (tier.get("blocker_count") or {}).get("after")
    blockers_clear = bc_after == 0

    # --- 1. a tier-material severity class was downgraded ------------------------------
    # BOTH tier-driving classes matter, not just BLOCKER. SKILL.md lines 1569-1573:
    #   blocker_count >= 3                      -> Not Agent-Integrable
    #   blocker_count 1-2                       -> Remediation Required
    #   blocker_count == 0, risk_safety >= 3    -> Pilot-Ready (Safety Concerns)
    #   blocker_count == 0, risk_safety 1-2     -> Pilot-Ready
    #   blocker_count == 0, risk_safety == 0    -> Agent-Ready
    # So RISK-SAFETY -> RISK-QUALITY is ALSO a mechanical tier relaxation once blockers are
    # clear, and it is the move that carries a repo the last step to Agent-Ready. Only
    # RISK-QUALITY and INFO are tier-inert ("RISK-QUALITY count has no effect", line 2054).
    #
    # This gap was found by reading a real advisory comment: the judge filed
    # `DATA-Q1 RISK-SAFETY -> RISK-QUALITY` as "likely run-to-run variance" while the first
    # cut of this function, keyed on BLOCKER alone, stayed silent and agreed with it.
    lost_safety: dict[str, list[str]] = {"BLOCKER": [], "RISK-SAFETY": []}
    # Downgrades that align a finding WITH the TD's documented severity. Tracked separately
    # so the count-fall and tier-relaxation checks below can tell a legitimate correction
    # (blocker_count 3->2 because AUTH-Q5 should never have been a blocker) apart from a real
    # relaxation. `corrected["BLOCKER"]` are the over-escalations whose class was BLOCKER.
    corrected: dict[str, list[str]] = {"BLOCKER": [], "RISK-SAFETY": []}
    for r in findings.get("reseveritied") or []:
        if not isinstance(r, dict):
            continue
        nat = r.get("native_severity") or {}
        before_cls = str(nat.get("before") or "").strip().upper()
        if before_cls not in lost_safety:
            continue
        if not _severity_relaxed(nat.get("before"), nat.get("after")):
            continue
        qid = str(r.get("question_id"))

        # Is this downgrade a CORRECTION toward the TD's own table, not a relaxation?
        # A report that emitted AUTH-Q5 as BLOCKER was over-escalating — the TD documents
        # it RISK-SAFETY unconditionally — so BLOCKER -> RISK-SAFETY makes the analysis
        # MORE accurate. Such a move must not count toward `lost_safety` (it never fed a
        # correct tier), must not be tier-material, and is emitted as its own `kind` so the
        # judge reads it as an improvement rather than a hazard to explain away.
        if is_over_escalation_correction(analysis, qid, nat.get("before"), nat.get("after"),
                                         changed_qids):
            corrected[before_cls].append(qid)
            alerts.append({
                "kind": "over_escalation_corrected",
                "repo": repo,
                "question_id": r.get("question_id"),
                "before": nat.get("before"),
                "after": nat.get("after"),
                "tier_material": False,
                "correction": True,
                "detail": (f"{qid} moved {before_cls} -> {nat.get('after')}, which MATCHES "
                           f"the TD's documented severity for {qid}. The prior "
                           f"{before_cls} was an over-escalation; this correction makes the "
                           "analysis more accurate and does not relax any correct tier."),
            })
            continue

        lost_safety[before_cls].append(qid)
        if before_cls == "BLOCKER":
            tier_material = True
            why = ("A lost BLOCKER relaxes the readiness tier mechanically "
                   "(>=3 BLOCKER -> Not Agent-Integrable; 1-2 -> Remediation Required), "
                   "so this is never mere noise.")
        else:
            tier_material = blockers_clear
            why = ("RISK-SAFETY drives the tier once blocker_count is 0 "
                   "(>=3 -> Pilot-Ready (Safety Concerns); 1-2 -> Pilot-Ready; "
                   "0 -> Agent-Ready), and RISK-QUALITY is tier-inert. "
                   + ("blocker_count is now 0, so this DOES move the tier."
                      if blockers_clear else
                      "blocker_count is still above 0 here, so the tier does not move "
                      "yet — noted rather than held, but check it is intended."))
        alerts.append({
            "kind": "blocker_downgraded" if before_cls == "BLOCKER"
                    else "safety_class_downgraded",
            "repo": repo,
            "question_id": r.get("question_id"),
            "before": nat.get("before"),
            "after": nat.get("after"),
            "tier_material": tier_material,
            "detail": f"{qid} was {before_cls} and is now {nat.get('after')}. {why}",
        })
    lost_blockers = lost_safety["BLOCKER"]
    # Everything that moved a repo toward agent-ready, for attributing the tier move below.
    lost_all = lost_blockers + lost_safety["RISK-SAFETY"]

    # A finding that disappeared ENTIRELY is the same hazard as one downgraded — `removed`
    # carries only question ids, so we cannot read its class from the delta and must rely on
    # the counts below to catch it.

    # --- 2. a tier-driving count fell --------------------------------------------------
    for field, label in (("blocker_count", "blocker_count"),
                         ("risk_safety_count", "risk_safety_count")):
        cc = tier.get(field) or {}
        c_before, c_after = cc.get("before"), cc.get("after")
        if not (isinstance(c_before, int) and isinstance(c_after, int)):
            continue
        if c_after >= c_before:
            continue
        is_blocker = field == "blocker_count"
        attributed = lost_blockers if is_blocker else lost_safety["RISK-SAFETY"]
        corrected_here = corrected["BLOCKER"] if is_blocker else corrected["RISK-SAFETY"]
        # How much of the fall is a genuine relaxation vs an over-escalation correction? A
        # blocker_count of 3->2 driven ENTIRELY by correcting AUTH-Q5 (which should never
        # have been a blocker) has not made the system any more agent-ready than the rubric
        # already said it was. Subtract the corrections; only a residual fall is a relaxation.
        real_fall = (c_before - c_after) - len(corrected_here)
        # risk_safety_count drifts on every rerun while blockers remain, so it only holds
        # when it is actually the tier driver. blocker_count always holds — UNLESS the whole
        # fall is corrections, in which case there is nothing to hold on.
        tier_material = real_fall > 0 and (is_blocker or blockers_clear)
        if real_fall <= 0:
            detail = (f"{label} fell {c_before} -> {c_after}, entirely from correcting "
                      f"over-escalated findings ({', '.join(corrected_here)}). This aligns "
                      "the count with the TD's severity table; it is not a relaxation.")
        elif tier_material:
            detail = (f"{label} fell {c_before} -> {c_after}"
                      + (f" (downgraded: {', '.join(attributed)})" if attributed else "")
                      + ". A lower tier-driving count means the analysis now considers "
                        "this system closer to agent-ready — confirm that is intended.")
        else:
            detail = (f"{label} fell {c_before} -> {c_after}"
                      + (f" (downgraded: {', '.join(attributed)})" if attributed else "")
                      + ". blocker_count is still above 0, so this does not move the tier "
                        "on its own; noted because it is one blocker fix away from doing so.")
        alerts.append({
            "kind": "blocker_count_fell" if is_blocker else "risk_safety_count_fell",
            "repo": repo,
            "field": label,
            "before": c_before,
            "after": c_after,
            "attributed_to": attributed,
            "corrected": corrected_here,
            "tier_material": tier_material,
            "detail": detail,
        })

    # --- 3. the readiness tier relaxed -------------------------------------------------
    corrected_all = corrected["BLOCKER"] + corrected["RISK-SAFETY"]
    if tier.get("changed"):
        relaxed = _tier_relaxed(tier.get("before"), tier.get("after"))
        if relaxed is True:
            # A tier move driven ONLY by over-escalation corrections (nothing in lost_all)
            # is the tier being corrected, not relaxed: the TD's severity table always
            # implied this tier — the report was simply mis-derived from an inflated count.
            # e.g. AUTH-Q5 wrongly a BLOCKER inflated blocker_count to 3 (Not
            # Agent-Integrable) when the two real blockers put it at Remediation Required.
            correction_only = bool(corrected_all) and not lost_all
            alerts.append({
                "kind": "tier_corrected" if correction_only else "tier_relaxed",
                "repo": repo,
                "before": tier.get("before"),
                "after": tier.get("after"),
                "attributed_to": lost_all,
                "corrected": corrected_all,
                # A genuine relaxation is always tier-material; a correction is not.
                "tier_material": not correction_only,
                "correction": correction_only,
                "detail": ((f"readiness tier moved {tier.get('before')} -> "
                            f"{tier.get('after')} because over-escalated findings "
                            f"({', '.join(corrected_all)}) were corrected to their "
                            "documented severity. The tier now matches what the TD's "
                            "severity table always implied — a correction, not a relaxation.")
                           if correction_only else
                           (f"readiness tier moved {tier.get('before')} -> "
                            f"{tier.get('after')}, i.e. MORE agent-ready"
                            + (f", caused by downgrading {', '.join(lost_all)}"
                               if lost_all else "")
                            + ". This is a safety-material change and requires a causal "
                              "explanation, not a noise attribution.")),
            })
    return alerts


# ---------------------------------------------------------------------------------------
# QUESTION COVERAGE — every per-repo report must answer the WHOLE rubric
# ---------------------------------------------------------------------------------------
# The ARA rubric defines 43 questions and MOD 37, and every per-repo golden report answers
# all of them (verified across all 24 baselines). A report that suddenly answers fewer has
# either lost a question from the rubric or silently failed to evaluate one — and either
# way the harness would report it as a pile of REMOVED findings, indistinguishable from the
# analysis agent's ordinary nondeterministic churn. The judge would then quite reasonably
# call it noise. So assert coverage structurally instead of hoping the delta reveals it.
#
# Counted from the report itself, NOT parsed out of SKILL.md: the rubric prose mentions ids
# it does not define (MOD's namespace-collision note names ARA's DATA-Q7, which is not a
# MOD question), so grepping the rubric over-counts. The expected totals are pinned here
# and asserted against the baseline by the tests.
_EXPECTED_QUESTIONS = {"ara": 43, "mod": 37}


def _answered_question_ids(report: dict) -> set[str]:
    """Question ids the report actually answered.

    `evaluations` and `findings` are DISJOINT, not overlapping: a question that flagged an
    issue is recorded in `findings`, one that passed in `evaluations`. On
    legacy-loan-calculator that is 22 + 21 = 43 with zero intersection. So coverage is the
    UNION of both — reading either alone reports roughly half the rubric and makes every
    healthy report look like it dropped 20 questions (which is exactly what the first cut
    of this function did against all 24 baselines).
    """
    ids: set[str] = set()
    for key in ("evaluations", "findings"):
        for e in report.get(key) or []:
            if isinstance(e, dict) and isinstance(e.get("question_id"), str):
                ids.add(e["question_id"])
    return ids


def question_coverage(repo: str, analysis: str,
                      before: dict, after: dict) -> Optional[dict]:
    """Flag a per-repo report that stopped answering the full rubric.

    Returns None when coverage is intact or cannot be assessed. Compares against the
    BASELINE's own count as well as the expected total, so a baseline that was itself
    incomplete does not mask a further regression.
    """
    expected = _EXPECTED_QUESTIONS.get(analysis)
    if expected is None:
        return None
    b_ids, a_ids = _answered_question_ids(before), _answered_question_ids(after)
    if not a_ids:
        # No question ids at all — a structurally broken report, not a coverage dip.
        return None
    missing_vs_baseline = sorted(b_ids - a_ids)
    if len(a_ids) >= expected and not missing_vs_baseline:
        return None
    return {
        "repo": repo,
        "analysis": analysis,
        "expected": expected,
        "baseline_answered": len(b_ids),
        "after_answered": len(a_ids),
        "missing_vs_baseline": missing_vs_baseline,
        "detail": (f"{repo} ({analysis.upper()}) answered {len(a_ids)} of {expected} "
                   f"rubric questions (baseline answered {len(b_ids)})"
                   + (f"; no longer answering: {', '.join(missing_vs_baseline[:10])}"
                      if missing_vs_baseline else "")
                   + ". A dropped question surfaces as removed findings and is easily "
                     "mistaken for noise — treat it as a rubric/analysis defect."),
    }


def build_impact(before_tree: dict, after_tree: dict,
                 changed_severity_qids: Optional[dict[str, set[str]]] = None) -> dict:
    per_repo: dict[str, dict] = {}
    portfolio: dict[str, dict] = {}
    alerts: list[dict] = []
    coverage_gaps: list[dict] = []
    # {analysis: {qids whose documented severity moved in this MR}}. Threaded to
    # safety_alerts so a report matching a freshly-edited rubric row cannot be waved through
    # as an "over-escalation correction". None/absent = the differ was pointed at two static
    # report trees with no rubric diff (all unit tests, and `--after <dir>` with no base ref).
    changed_severity_qids = changed_severity_qids or {}

    # Compare only reports present on BOTH sides.
    #
    # This used to be a UNION, which was correct only while every run was a full sweep.
    # An MR now analyzes just the 1-2 fixtures that exercise the edit (and only the
    # changed analysis type, and often no portfolio), so `after` legitimately holds a
    # SUBSET of golden's 26 reports. Under a union, every unanalyzed baseline diffed
    # against `{}` and its entire findings list read as DELETED: a byte-identical 2-report
    # no-op produced 540 phantom "removed" findings across 11 repos, no_op=False, and all
    # four TDs flagged as changed — i.e. a catastrophic-regression verdict on every MR.
    #
    # A report we did not generate is UNKNOWN, not unchanged and not deleted. So we skip
    # it here and record it under `not_analyzed` so the judge can see the run was scoped
    # (silently narrowing the comparison would be its own kind of wrong).
    compared_keys = set(before_tree) & set(after_tree)
    not_analyzed = sorted(
        f"{analysis}/{scope}/{key}"
        for (analysis, scope, key) in set(before_tree) - set(after_tree)
    )
    # In `after` but not in golden = a genuinely NEW report (e.g. a new fixture). That is
    # real signal and must not be hidden, but it has no baseline to diff against.
    unbaselined = sorted(
        f"{analysis}/{scope}/{key}"
        for (analysis, scope, key) in set(after_tree) - set(before_tree)
    )
    changed_tds: set[str] = set()

    for (analysis, scope, key) in sorted(compared_keys):
        before = normalize_report(analysis, before_tree.get((analysis, scope, key), {}))
        after = normalize_report(analysis, after_tree.get((analysis, scope, key), {}))

        if scope == "repo":
            entry = per_repo.setdefault(key, {})
            fd = diff_findings(before, after)
            td = diff_tier_repo(before, after, analysis)
            entry[f"D1_{analysis}_findings"] = fd
            entry[f"D2_{analysis}_tier"] = td
            # Deterministic guards. Collected regardless of whether anything else "moved",
            # and regardless of the MR's edit scope — a relaxed tier is material even when
            # the questions that caused it were never touched.
            alerts.extend(safety_alerts(key, analysis, fd, td,
                                        changed_severity_qids.get(analysis)))
            gap = question_coverage(key, analysis, before, after)
            if gap:
                coverage_gaps.append(gap)
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
        # Deterministic findings the judge must ADDRESS rather than weigh away. Kept at the
        # top level (not buried per-repo) so neither the prompt builder nor a human reader
        # can miss them, and so `harness/judge.py` can refuse to return LGTM while a
        # safety alert is unexplained.
        "safety_alerts": alerts,
        "coverage_gaps": coverage_gaps,
        # Scope of THIS comparison. `no_op` below means "nothing moved in what we
        # compared" — these fields say how much that was, so a clean verdict on a
        # scoped run can't be mistaken for a clean verdict on a full sweep.
        "coverage": {
            "compared": len(compared_keys),
            "baseline_total": len(before_tree),
            "not_analyzed": not_analyzed,
            "unbaselined": unbaselined,
            "partial": bool(not_analyzed),
        },
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
    ap.add_argument("--changed-severity", type=Path, default=None,
                    help="JSON file {analysis: [qids]} of questions whose documented "
                         "severity/conditional row was edited in this MR (from "
                         "`skill_table.py diff-severity`). Those qids are barred from the "
                         "over-escalation-correction exemption so a report matching a "
                         "freshly-edited rubric row still alerts as a real relaxation. "
                         "Absent/empty => no gate (the committed baseline has no MR diff).")
    args = ap.parse_args(argv)

    before_tree = load_tree(args.baseline)
    after_tree = load_tree(args.after)

    if not before_tree and not after_tree:
        print(f"error: no managed reports found under {args.baseline} or {args.after}",
              file=sys.stderr)
        return 2

    # {analysis: set(qids)}; None when no diff was supplied. A malformed/empty file is
    # treated as "no gate" rather than fatal — this is an advisory job (`allow_failure`),
    # and failing the differ because a severity-diff file was unreadable would throw away
    # the whole delta over a belt-and-braces guard.
    changed_severity: Optional[dict[str, set[str]]] = None
    if args.changed_severity and args.changed_severity.is_file():
        try:
            raw = json.loads(args.changed_severity.read_text(encoding="utf-8") or "{}")
            changed_severity = {
                str(k): {str(q).strip().upper() for q in (v or [])}
                for k, v in (raw or {}).items()
            }
            _named = sorted(q for s in changed_severity.values() for q in s)
            if _named:
                print(f"diff-reports: severity-table edited for {_named} — these are barred "
                      "from the over-escalation-correction exemption", file=sys.stderr)
        except (ValueError, AttributeError) as exc:
            print(f"diff-reports: WARN could not parse {args.changed_severity} "
                  f"({exc}); proceeding with no severity gate", file=sys.stderr)

    impact = build_impact(before_tree, after_tree, changed_severity)
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
