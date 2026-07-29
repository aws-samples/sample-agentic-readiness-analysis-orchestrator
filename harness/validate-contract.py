#!/usr/bin/env python3
"""
validate-contract.py — assert an ARA/MOD per-repo report JSON conforms to the web-UI
ingester contract.

Why this exists
---------------
The 2026-07-16 re-version replaced the full managed TD definitions with schema-less
SKILL.md stubs. That silently dropped the JSON output contract the ingester reads:
  * MOD lost the top-level `analysis_type: "mod"` literal + the flat `findings[]` array
    (CT `parseModReport` fell back to markdown → 0 findings) plus
    `overall_score`/`evaluations[]`/`categories[]`/`classification{}`/`top_gaps[]`.
  * ARA `findings[]` became a dict keyed by camelCase category with BLOCKER/RISK/INFO
    severities instead of a flat array of 12-field records with High/Medium/Low.

This validator is the regression guard: it encodes the contract (read directly from the
restored managed TDs, which are now the source of truth) and FAILS on any report that
does not conform — so the drift cannot silently recur. It is intentionally strict about
the exact deltas the ingester broke on, and lenient about optional/extra fields.

It is deterministic and offline (no AWS, no LLM). Two consumers:
  1. `atx custom def exec` output — the live proof our repo's TDs emit conforming JSON
     (see exec-contract.sh). This is what we can run TODAY, before the fixed TDs are
     published to Continuous Modernization.
  2. `atx ct` golden/after reports — once the fixed TDs ship to Continuous Modernization,
     the same check gates the existing harness report path.

It covers all four managed report types: per-repo ARA/MOD and portfolio ARA/MOD.
Portfolio reports carry `analysis_type: "portfolio-ara"|"portfolio-mod"`, an
`executive_dashboard`, a `repositories[]` roll-up, and `recommended_actions[]` PROGRAMS
(D4) — a leaner findings shape than per-repo (portfolio MOD findings drop
description/gap/recommendation).

Usage:
    validate-contract.py <file-or-dir> [<file-or-dir> ...]
                         [--analysis ara|mod|portfolio-ara|portfolio-mod]
                         [--strict] [--json]
    # dir args are scanned for *-ara-report.json / *-mod-report.json (portfolio filenames
    #   also match); non-recursive by default (-r to recurse)
    # exit 0 = all conform, 1 = at least one violation, 2 = usage/IO error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# --- contract constants (sourced from the restored managed TDs) ----------------------

# 12 required per-finding fields — IDENTICAL across ARA and MOD by design so one webapp
# renders both without per-analysis branching (see both SKILL.md "Per-Finding Required
# Fields" tables).
FINDING_FIELDS = [
    "question_id", "category", "category_id", "title", "description",
    "gap", "recommendation", "severity", "priority", "effort", "phase", "evidence",
]

# Unified severity vocabulary on the top-level `severity` field (native BLOCKER/RISK/INFO
# lives in {ara,mod}_metadata.native_severity, NOT here).
SEVERITY_VALUES = {"High", "Medium", "Low"}
PRIORITY_VALUES = {"P0", "P1", "P2", "P3"}
EFFORT_VALUES = {"High", "Medium", "Low"}

ARA_TIERS = {"Agent-Ready", "Pilot-Ready", "Remediation Required", "Not Agent-Integrable"}
MOD_TIERS = {"Cloud-Native Ready", "Pilot-Ready", "Remediation Required", "Not Ready"}

# MOD category-level three-label coexistence (categories[]).
MOD_SCORE_RATINGS = {"Mature", "Partial", "Needs Work", "Not Ready"}
MOD_SEVERITY_STATUS = {"Ready", "Needs Work", "Critical"}

# The 7 canonical MOD pathway ids — every per-repo MOD report emits exactly these.
MOD_PATHWAY_IDS = {
    "move-to-cloud-native", "move-to-containers", "move-to-open-source",
    "move-to-managed-databases", "move-to-managed-analytics",
    "move-to-modern-devops", "move-to-ai",
}

ARA_METADATA_REQUIRED = {"native_severity", "safety_impact"}
ARA_NATIVE_SEVERITY = {"BLOCKER", "RISK-SAFETY", "RISK-QUALITY", "INFO"}
MOD_METADATA_REQUIRED = {"internal_score", "score_label", "archetype_calibrated", "core_question"}
MOD_SCORE_LABELS = {"Not Ready", "Needs Work", "Partial"}


class Violations:
    """Collects contract violations for one report."""

    def __init__(self, path: Path, analysis: str):
        self.path = path
        self.analysis = analysis
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


# --- analysis-type detection ---------------------------------------------------------

def detect_analysis(path: Path, data: dict) -> str | None:
    """Return 'ara'|'mod'|'portfolio-ara'|'portfolio-mod'|None.

    A report is portfolio when its analysis_type says so, or (filename-only fallback)
    the name contains 'portfolio' AND it carries a repositories[] roll-up.
    """
    name = path.name.lower()
    at = str(data.get("analysis_type", "")).lower()

    # analysis_type literal is the strongest signal.
    if at in ("portfolio-ara", "portfolio-agentic-readiness"):
        return "portfolio-ara"
    if at in ("portfolio-mod", "portfolio-modernization"):
        return "portfolio-mod"
    if at in ("ara", "agentic-readiness", "agentic-readiness-analysis"):
        return "ara"
    if at in ("mod", "modernization-readiness", "modernization-readiness-analysis"):
        return "mod"

    # Filename fallback (no/unknown analysis_type).
    is_portfolio = "portfolio" in name or isinstance(data.get("repositories"), list)
    if name.endswith("-ara-report.json") or "-ara-" in name:
        return "portfolio-ara" if is_portfolio else "ara"
    if name.endswith("-mod-report.json") or "-mod-" in name:
        return "portfolio-mod" if is_portfolio else "mod"
    return None


# --- shared finding validation -------------------------------------------------------

def _check_findings_array(v: Violations, data: dict, meta_key: str,
                          native_values: set[str], strict: bool) -> None:
    """The core regression: findings MUST be a flat top-level array of 12-field records."""
    findings = data.get("findings")
    if findings is None:
        v.err("missing top-level `findings[]` — the ingester reads a flat top-level array "
              "(this is the exact field that went to 0 after the schema regression)")
        return
    if isinstance(findings, dict):
        v.err("`findings` is a dict keyed by category — the ingester requires a FLAT "
              f"top-level array. Keys seen: {sorted(findings)[:6]}")
        return
    if not isinstance(findings, list):
        v.err(f"`findings` must be a list, got {type(findings).__name__}")
        return

    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            v.err(f"findings[{i}] is not an object")
            continue
        qid = f.get("question_id") or f.get("id") or f"<index {i}>"
        missing = [k for k in FINDING_FIELDS if k not in f]
        if missing:
            v.err(f"finding {qid}: missing required field(s) {missing} "
                  f"(all 12 per-finding fields are REQUIRED)")
        sev = f.get("severity")
        if sev is not None and sev not in SEVERITY_VALUES:
            v.err(f"finding {qid}: severity {sev!r} not in {sorted(SEVERITY_VALUES)} "
                  f"(native BLOCKER/RISK/INFO belongs in {meta_key}.native_severity)")
        if strict:
            if f.get("priority") not in PRIORITY_VALUES:
                v.warn(f"finding {qid}: priority {f.get('priority')!r} not in {sorted(PRIORITY_VALUES)}")
            if f.get("effort") not in EFFORT_VALUES:
                v.warn(f"finding {qid}: effort {f.get('effort')!r} not in {sorted(EFFORT_VALUES)}")
        # metadata subobject
        meta = f.get(meta_key)
        if not isinstance(meta, dict):
            v.err(f"finding {qid}: missing `{meta_key}` subobject")
        else:
            req = ARA_METADATA_REQUIRED if meta_key == "ara_metadata" else MOD_METADATA_REQUIRED
            miss = [k for k in req if k not in meta]
            if miss:
                v.err(f"finding {qid}: `{meta_key}` missing {miss}")
            ns = meta.get("native_severity")
            if meta_key == "ara_metadata" and ns is not None and ns not in native_values:
                v.err(f"finding {qid}: ara_metadata.native_severity {ns!r} not in {sorted(native_values)}")


def _check_evaluations(v: Violations, data: dict) -> None:
    ev = data.get("evaluations")
    if ev is None:
        v.err("missing `evaluations[]` — every question resolves to either findings[] or "
              "evaluations[]; the array must be present")
        return
    if not isinstance(ev, list):
        v.err(f"`evaluations` must be a list, got {type(ev).__name__}")
        return
    for i, e in enumerate(ev):
        if not isinstance(e, dict):
            v.err(f"evaluations[{i}] is not an object")
            continue
        miss = [k for k in ("question_id", "category_id", "status", "reason") if k not in e]
        if miss:
            v.err(f"evaluations[{i}] ({e.get('question_id','?')}): missing {miss}")


def _check_analysis_type(v: Violations, data: dict, expected: str) -> None:
    """The other half of the regression: the literal analysis_type discriminator."""
    at = data.get("analysis_type")
    if at is None:
        v.err(f"missing top-level `analysis_type` (must be the literal {expected!r})")
    elif at != expected:
        v.err(f"`analysis_type` is {at!r} — the ingester requires the literal {expected!r} "
              f"(the join key is (analysis_type, question_id))")


# --- ARA ------------------------------------------------------------------------------

def validate_ara(v: Violations, data: dict, strict: bool) -> None:
    _check_analysis_type(v, data, "ara")
    _check_findings_array(v, data, "ara_metadata", ARA_NATIVE_SEVERITY, strict)
    _check_evaluations(v, data)

    cls = data.get("classification")
    if not isinstance(cls, dict):
        v.err("missing `classification{}` object")
    else:
        tier = cls.get("tier")
        if tier not in ARA_TIERS:
            v.err(f"classification.tier {tier!r} not in {sorted(ARA_TIERS)}")
        for c in ("blocker_count", "risk_safety_count", "rule_matched"):
            if c not in cls:
                v.err(f"classification missing `{c}`")

    if "categories" not in data:
        v.warn("no top-level `categories[]` (ARA carries category rollups; present in full reports)")


# --- MOD ------------------------------------------------------------------------------

def validate_mod(v: Violations, data: dict, strict: bool) -> None:
    _check_analysis_type(v, data, "mod")
    _check_findings_array(v, data, "mod_metadata", set(), strict)
    _check_evaluations(v, data)

    # overall_score — drives the report score independently of findings.
    if "overall_score" not in data:
        v.err("missing top-level `overall_score` (float 0-4) — absence forces a 0 score")
    elif not isinstance(data["overall_score"], (int, float)):
        v.err(f"`overall_score` must be numeric, got {type(data['overall_score']).__name__}")

    cats = data.get("categories")
    if not isinstance(cats, list):
        v.err("missing `categories[]` array")
    else:
        for c in cats:
            if not isinstance(c, dict):
                continue
            cid = c.get("category_id", "?")
            for lbl in ("numeric_score", "score_rating", "severity_status"):
                if lbl not in c:
                    v.err(f"categories[{cid}]: missing `{lbl}` (all three labels coexist)")
            sr = c.get("score_rating")
            if sr is not None and sr not in MOD_SCORE_RATINGS:
                v.err(f"categories[{cid}]: score_rating {sr!r} not in {sorted(MOD_SCORE_RATINGS)}")
            ss = c.get("severity_status")
            if ss is not None and ss not in MOD_SEVERITY_STATUS:
                v.err(f"categories[{cid}]: severity_status {ss!r} not in {sorted(MOD_SEVERITY_STATUS)}")

    cls = data.get("classification")
    if not isinstance(cls, dict):
        v.err("missing `classification{}` object")
    else:
        tier = cls.get("tier")
        if tier not in MOD_TIERS:
            v.err(f"classification.tier {tier!r} not in {sorted(MOD_TIERS)}")
        for c in ("high_count", "medium_count", "low_count", "rule_matched",
                  "classification_consistency_check"):
            if c not in cls:
                v.err(f"classification missing `{c}`")

    if "top_gaps" not in data:
        v.err("missing `top_gaps[]`")

    # pathways[] — must exist, be trigger-tracking objects with the 7 canonical ids.
    pathways = data.get("pathways")
    if not isinstance(pathways, list):
        v.err("missing `pathways[]` array (7 canonical entries expected)")
    else:
        ids = {p.get("id") for p in pathways if isinstance(p, dict)}
        missing_ids = MOD_PATHWAY_IDS - ids
        if missing_ids:
            v.err(f"pathways[] missing canonical id(s): {sorted(missing_ids)}")
        for p in pathways:
            if isinstance(p, dict) and "findings" in p:
                v.err(f"pathways[{p.get('id','?')}] carries nested `findings` — MOD pathways "
                      "are trigger-tracking objects (id/name/status/…); findings are top-level only")


# --- portfolio ------------------------------------------------------------------------

def _check_portfolio_programs(v: Violations, data: dict) -> None:
    """D4: portfolio recommended_actions[] carry PROGRAMS (acronym/name/status), not plain
    per-repo remediation actions. This is the portfolio-only program surface."""
    ra = data.get("recommended_actions")
    if not isinstance(ra, list):
        v.err("missing `recommended_actions[]` (portfolio programs surface)")
        return
    # At least one entry should look like a program (has a name/acronym + status).
    program_like = [a for a in ra if isinstance(a, dict)
                    and (a.get("acronym") or a.get("name")) and "status" in a]
    if ra and not program_like:
        v.warn("`recommended_actions[]` has no program-shaped entries "
               "(expected name/acronym + status — AI DLC/AXE/EBA/MAP/OLA/…)")


def _check_repositories_rollup(v: Violations, data: dict) -> None:
    repos = data.get("repositories")
    if not isinstance(repos, list):
        v.err("missing `repositories[]` roll-up")
        return
    for i, r in enumerate(repos):
        if isinstance(r, dict) and "classification" not in r and "tier" not in r:
            v.warn(f"repositories[{i}]: no classification/tier on the roll-up entry")


def validate_portfolio_ara(v: Violations, data: dict, strict: bool) -> None:
    _check_analysis_type(v, data, "portfolio-ara")
    if not isinstance(data.get("executive_dashboard"), dict):
        v.err("missing `executive_dashboard{}`")
    _check_repositories_rollup(v, data)
    # portfolio ARA has BOTH findings[] and cross_cutting_findings[]
    if not isinstance(data.get("findings"), list):
        v.err("missing portfolio `findings[]` array")
    if "cross_cutting_findings" not in data:
        v.warn("no `cross_cutting_findings[]` (portfolio-aggregated findings surface)")
    _check_portfolio_programs(v, data)


def validate_portfolio_mod(v: Violations, data: dict, strict: bool) -> None:
    _check_analysis_type(v, data, "portfolio-mod")
    ed = data.get("executive_dashboard")
    if not isinstance(ed, dict):
        v.err("missing `executive_dashboard{}`")
    else:
        if "score_band_distribution" not in ed:
            v.err("executive_dashboard missing `score_band_distribution`")
        if "tier_distribution" not in ed:
            v.err("executive_dashboard missing `tier_distribution` "
                  "(dual-distribution must agree with score bands)")
    _check_repositories_rollup(v, data)
    if not isinstance(data.get("findings"), list):
        v.err("missing portfolio `findings[]` array")
    if "remediation_roadmap" not in data:
        v.err("missing `remediation_roadmap`")
    # portfolio pathways[] carry the 7 canonical ids too
    pathways = data.get("pathways")
    if isinstance(pathways, list):
        ids = {p.get("id") for p in pathways if isinstance(p, dict)}
        missing_ids = MOD_PATHWAY_IDS - ids
        if missing_ids:
            v.warn(f"portfolio pathways[] missing canonical id(s): {sorted(missing_ids)}")
    else:
        v.err("missing portfolio `pathways[]` array")
    _check_portfolio_programs(v, data)


# --- driver --------------------------------------------------------------------------

_VALIDATORS = {
    "ara": validate_ara,
    "mod": validate_mod,
    "portfolio-ara": validate_portfolio_ara,
    "portfolio-mod": validate_portfolio_mod,
}


def validate_report(path: Path, data: dict, forced: str | None, strict: bool) -> Violations:
    analysis = forced or detect_analysis(path, data)
    if analysis is None:
        v = Violations(path, "?")
        v.err("cannot determine analysis type from filename or `analysis_type` "
              "(expected *-ara-report.json / *-mod-report.json)")
        return v
    v = Violations(path, analysis)
    _VALIDATORS[analysis](v, data, strict)
    return v


def _iter_targets(paths: list[Path], recurse: bool) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            globber = p.rglob if recurse else p.glob
            for pat in ("*-ara-report.json", "*-mod-report.json"):
                files.extend(sorted(globber(pat)))
        elif p.is_file():
            files.append(p)
        else:
            print(f"warn: skipping missing path {p}", file=sys.stderr)
    # de-dup, keep order
    seen: set[Path] = set()
    out: list[Path] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate ARA/MOD report JSON against the ingester contract")
    ap.add_argument("paths", nargs="+", type=Path, help="report file(s) or dir(s)")
    ap.add_argument("--analysis", choices=("ara", "mod", "portfolio-ara", "portfolio-mod"),
                    help="force analysis type (else inferred)")
    ap.add_argument("--strict", action="store_true", help="promote priority/effort vocab checks to warnings")
    ap.add_argument("-r", "--recurse", action="store_true", help="recurse into directories")
    ap.add_argument("--json", action="store_true", help="emit a machine-readable JSON summary")
    args = ap.parse_args(argv)

    targets = _iter_targets(args.paths, args.recurse)
    if not targets:
        print("no report files found", file=sys.stderr)
        return 2

    results: list[Violations] = []
    for f in targets:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            v = Violations(f, "?")
            v.err(f"cannot read/parse: {exc}")
            results.append(v)
            continue
        results.append(validate_report(f, data, args.analysis, args.strict))

    failed = [r for r in results if not r.ok]

    if args.json:
        payload = {
            "conform": len(results) - len(failed),
            "violated": len(failed),
            "reports": [
                {"file": str(r.path), "analysis": r.analysis, "ok": r.ok,
                 "errors": r.errors, "warnings": r.warnings}
                for r in results
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        for r in results:
            status = "PASS" if r.ok else "FAIL"
            print(f"[{status}] {r.analysis.upper():3} {r.path.name}")
            for e in r.errors:
                print(f"    ✗ {e}")
            for w in r.warnings:
                print(f"    ⚠ {w}")
        print(f"\n{len(results) - len(failed)}/{len(results)} conform, {len(failed)} violated",
              file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
