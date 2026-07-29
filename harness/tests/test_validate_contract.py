#!/usr/bin/env python3
"""
Tests for validate-contract.py — the ingester-contract conformance guard.

Strategy: the drifted shape fixtures under tests/fixtures/shapes/ are exactly the shapes
the 2026-07-16 regression produced, so they MUST fail the contract. A synthesized
conforming report (built to the restored-TD contract) MUST pass. This is the regression
guard's own regression guard.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_validate_contract.py    (no pytest needed)
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHAPES = Path(__file__).resolve().parent / "fixtures" / "shapes"

_spec = importlib.util.spec_from_file_location(
    "validate_contract", REPO / "harness" / "validate-contract.py")
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)  # type: ignore


# --- conforming report builders (to the restored-TD contract) ------------------------

def _finding(qid: str, cat_id: str, meta_key: str) -> dict:
    meta = ({"native_severity": "BLOCKER", "safety_impact": True}
            if meta_key == "ara_metadata"
            else {"internal_score": 1, "score_label": "Not Ready",
                  "archetype_calibrated": False, "core_question": True})
    return {
        "question_id": qid, "category": "Cat Name", "category_id": cat_id,
        "title": "t", "description": "d", "gap": "g", "recommendation": "r",
        "severity": "High", "priority": "P0", "effort": "High", "phase": 1,
        "evidence": {"file": "a.py", "lines": "1-2"},
        meta_key: meta,
    }


def _conforming_ara() -> dict:
    return {
        "analysis_type": "ara",
        "repository": "demo",
        "findings": [_finding("AUTH-Q1", "AUTH", "ara_metadata")],
        "evaluations": [{"question_id": "API-Q1", "category_id": "API",
                         "status": "pass", "reason": "ok"}],
        "classification": {"tier": "Pilot-Ready", "blocker_count": 0,
                           "risk_safety_count": 1, "rule_matched": "…"},
        "categories": [],
    }


def _conforming_mod() -> dict:
    return {
        "analysis_type": "mod",
        "repository": "demo",
        "overall_score": 2.5,
        "findings": [_finding("INF-Q1", "INF", "mod_metadata")],
        "evaluations": [{"question_id": "APP-Q1", "category_id": "APP",
                         "status": "pass", "reason": "ok"}],
        "categories": [{"category_id": "INF", "numeric_score": 2.5,
                        "score_rating": "Partial", "severity_status": "Needs Work"}],
        "classification": {"tier": "Remediation Required", "high_count": 1,
                           "medium_count": 0, "low_count": 0, "rule_matched": "…",
                           "classification_consistency_check": "consistent"},
        "top_gaps": [],
        "pathways": [{"id": pid, "name": pid, "status": "Not Triggered"}
                     for pid in vc.MOD_PATHWAY_IDS],
    }


# --- conforming passes ---------------------------------------------------------------

def test_conforming_ara_passes():
    v = vc.Violations(Path("demo-ara-report.json"), "ara")
    vc.validate_ara(v, _conforming_ara(), strict=False)
    assert v.ok, v.errors


def test_conforming_mod_passes():
    v = vc.Violations(Path("demo-mod-report.json"), "mod")
    vc.validate_mod(v, _conforming_mod(), strict=False)
    assert v.ok, v.errors


# --- the regression must be caught ---------------------------------------------------

def test_ara_dict_by_category_rejected():
    # A1 is the exact regression shape: findings dict keyed by camelCase category.
    import json
    data = json.loads((SHAPES / "A1_ara_dict_by_category.json").read_text())
    v = vc.validate_report(SHAPES / "A1_ara_dict_by_category.json", data, "ara", False)
    assert not v.ok
    assert any("dict keyed by category" in e for e in v.errors)


def test_mod_missing_analysis_type_literal_rejected():
    import json
    for stem in ("M1_mod_pathways_list", "M3_mod_pathways_dict_findings"):
        data = json.loads((SHAPES / f"{stem}.json").read_text())
        v = vc.validate_report(SHAPES / f"{stem}.json", data, "mod", False)
        assert not v.ok, stem
        # analysis_type is "modernization-readiness", not the literal "mod"
        assert any("analysis_type" in e for e in v.errors), stem


def test_mod_missing_flat_findings_rejected():
    import json
    data = json.loads((SHAPES / "M1_mod_pathways_list.json").read_text())
    v = vc.validate_report(SHAPES / "M1_mod_pathways_list.json", data, "mod", False)
    assert any("findings" in e for e in v.errors)
    assert any("overall_score" in e for e in v.errors)


# --- targeted field checks -----------------------------------------------------------

def test_ara_native_severity_in_top_level_severity_rejected():
    bad = _conforming_ara()
    bad["findings"][0]["severity"] = "BLOCKER"  # native vocab leaked to top-level
    v = vc.Violations(Path("x-ara-report.json"), "ara")
    vc.validate_ara(v, bad, strict=False)
    assert any("native BLOCKER/RISK/INFO belongs in" in e for e in v.errors)


def test_mod_pathway_with_nested_findings_rejected():
    bad = _conforming_mod()
    bad["pathways"][0]["findings"] = [{"id": "x"}]  # findings must be top-level only
    v = vc.Violations(Path("x-mod-report.json"), "mod")
    vc.validate_mod(v, bad, strict=False)
    assert any("nested `findings`" in e for e in v.errors)


def test_mod_missing_pathway_id_rejected():
    bad = _conforming_mod()
    bad["pathways"] = bad["pathways"][:-1]  # drop one canonical pathway
    v = vc.Violations(Path("x-mod-report.json"), "mod")
    vc.validate_mod(v, bad, strict=False)
    assert any("missing canonical id" in e for e in v.errors)


def test_missing_finding_field_named():
    bad = _conforming_mod()
    del bad["findings"][0]["recommendation"]
    v = vc.Violations(Path("x-mod-report.json"), "mod")
    vc.validate_mod(v, bad, strict=False)
    assert any("recommendation" in e for e in v.errors)


def test_detect_analysis_from_filename_and_field():
    assert vc.detect_analysis(Path("foo-ara-report.json"), {}) == "ara"
    assert vc.detect_analysis(Path("foo-mod-report.json"), {}) == "mod"
    assert vc.detect_analysis(Path("weird.json"), {"analysis_type": "mod"}) == "mod"
    assert vc.detect_analysis(Path("weird.json"), {}) is None


# --- fallback runner (no pytest) -----------------------------------------------------

def _run_all():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            passed += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}: {exc}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
