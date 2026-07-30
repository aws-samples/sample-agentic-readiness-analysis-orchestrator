#!/usr/bin/env python3
"""
Tests for score-reports.py — the report ACCURACY scorer.

Scope note: this tool asks "is what the report says TRUE of the repo?", which is a
different question from judge.py's "does this change make the analysis better?". Only the
deterministic half is tested here; the LLM half is exercised by running the tool.

The deterministic checks are worth pinning tightly because they make FACTUAL claims about
published reports. A false positive here would send someone chasing a defect that does not
exist, and the counter check in particular has a subtle direction rule that is easy to get
backwards (see test_counter_check_only_flags_undercounts).

Run:  python3 -m pytest harness/tests/ -q
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location("score_reports",
                                               REPO / "harness" / "score-reports.py")
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)  # type: ignore


def _ara(blockers=0, risk_safety=0, tier="Agent-Ready", qual=None, findings=None) -> dict:
    return {
        "analysis_type": "agentic-readiness",
        "classification": {"tier": tier, "sub_qualifier": qual,
                           "blocker_count": blockers, "risk_safety_count": risk_safety,
                           "risk_quality_count": 0, "info_count": 0},
        "findings": findings if findings is not None else [],
        "evaluations": [],
    }


def _f(qid: str, native: str) -> dict:
    return {"question_id": qid, "ara_metadata": {"native_severity": native}}


# --- ARA tier arithmetic (SKILL.md 1569-1573) ------------------------------------------

def test_tier_table_matches_the_rubric_arithmetic():
    assert sr.expected_ara_tier(3, 0) == ("Not Agent-Integrable", None)
    assert sr.expected_ara_tier(9, 9) == ("Not Agent-Integrable", None)
    assert sr.expected_ara_tier(1, 0) == ("Remediation Required", None)
    assert sr.expected_ara_tier(2, 5) == ("Remediation Required", None)
    # RISK-SAFETY only drives the tier once blockers are clear.
    assert sr.expected_ara_tier(0, 3) == ("Pilot-Ready", "Safety Concerns")
    assert sr.expected_ara_tier(0, 1) == ("Pilot-Ready", None)
    assert sr.expected_ara_tier(0, 0) == ("Agent-Ready", None)


def test_tier_contradicting_its_own_counts_is_critical():
    bad = _ara(blockers=3, tier="Pilot-Ready")
    hits = [c for c in sr.check_ara(bad) if c["check"] == "tier_contradicts_counts"]
    assert hits and hits[0]["severity"] == "critical"


def test_correct_tier_is_not_flagged():
    assert not [c for c in sr.check_ara(_ara(blockers=3, tier="Not Agent-Integrable"))
                if c["check"] == "tier_contradicts_counts"]


def test_safety_concerns_qualifier_is_required_when_it_applies():
    # blockers clear + 3 RISK-SAFETY -> the qualifier must be present.
    hits = [c["check"] for c in sr.check_ara(_ara(0, 4, "Pilot-Ready", None))]
    assert "missing_safety_qualifier" in hits


def test_safety_concerns_qualifier_is_flagged_when_spurious():
    hits = [c["check"] for c in sr.check_ara(
        _ara(0, 0, "Agent-Ready", "Safety Concerns"))]
    assert "spurious_safety_qualifier" in hits


def test_qualifier_present_exactly_when_due_is_clean():
    assert not [c for c in sr.check_ara(_ara(0, 3, "Pilot-Ready", "Safety Concerns"))
                if "qualifier" in c["check"]]


# --- severity counters -----------------------------------------------------------------

def test_counter_check_only_flags_undercounts():
    """THE direction rule, and the reason the check is trustworthy.

    Exclusion rules (N/A questions, read-only scope downgrades, not_evaluated_extended)
    remove questions from the findings list while the counter may still describe the full
    rubric — so a counter legitimately runs HIGHER than what is enumerated. It can never
    run LOWER. Flagging overcounts too would produce false defects on every report that
    excludes anything; flagging neither would have missed the 5 real ones.
    """
    over = _ara(findings=[_f("A-Q1", "RISK-SAFETY")])
    over["classification"]["risk_safety_count"] = 5          # counter > enumerated: OK
    assert not [c for c in sr.check_ara(over)
                if c["check"] == "severity_counter_undercount"]

    under = _ara(findings=[_f(f"A-Q{i}", "RISK-SAFETY") for i in range(5)])
    under["classification"]["risk_safety_count"] = 2          # counter < enumerated: DEFECT
    hits = [c for c in sr.check_ara(under)
            if c["check"] == "severity_counter_undercount"]
    assert hits and "undercount by 3" in hits[0]["detail"]


def test_blocker_undercount_outranks_a_quality_undercount():
    # Severity is not cosmetic here: a lost BLOCKER changes the tier, a RISK-QUALITY
    # miscount cannot (RISK-QUALITY is tier-inert), and the benchmark rubric weights a
    # missed blocker far above a spurious low-severity finding.
    b = _ara(findings=[_f("A-Q1", "BLOCKER")])
    b["classification"]["blocker_count"] = 0
    q = _ara(findings=[_f("A-Q1", "RISK-QUALITY")])
    q["classification"]["risk_quality_count"] = 0
    assert [c for c in sr.check_ara(b)][0]["severity"] == "high"
    assert [c for c in sr.check_ara(q)][0]["severity"] == "medium"


# --- question coverage -----------------------------------------------------------------

def test_full_coverage_passes_for_both_analyses():
    ara = {"findings": [{"question_id": f"Q{i}"} for i in range(20)],
           "evaluations": [{"question_id": f"Q{i}"} for i in range(20, 43)]}
    assert sr.check_coverage(ara, "ara") == []
    mod = {"findings": [{"question_id": f"Q{i}"} for i in range(15)],
           "evaluations": [{"question_id": f"Q{i}"} for i in range(15, 37)]}
    assert sr.check_coverage(mod, "mod") == []


def test_coverage_is_the_union_not_either_list_alone():
    """`findings` and `evaluations` are DISJOINT sets and BOTH resolve a question.

    Measured on loan-calculator: 21 findings + 22 evaluations = 43, zero intersection.
    Counting only one list would report every report as ~50% covered.
    """
    rpt = {"findings": [{"question_id": f"Q{i}"} for i in range(21)],
           "evaluations": [{"question_id": f"Q{i}"} for i in range(21, 43)]}
    assert sr.check_coverage(rpt, "ara") == []


def test_missing_questions_are_critical():
    rpt = {"findings": [{"question_id": f"Q{i}"} for i in range(41)], "evaluations": []}
    hits = [c for c in sr.check_coverage(rpt, "ara")
            if c["check"] == "incomplete_question_coverage"]
    assert hits and hits[0]["severity"] == "critical"
    assert "41 of 43" in hits[0]["detail"]


def test_a_question_resolved_twice_is_a_defect():
    # The benchmark prompts require EXACTLY one of findings|evaluations — never both.
    rpt = {"findings": [{"question_id": "API-Q1"}], "evaluations": [{"question_id": "API-Q1"}]}
    assert "question_in_both_findings_and_evaluations" in [
        c["check"] for c in sr.check_coverage(rpt, "ara")]


def test_mod_expects_37_not_43():
    # ARA is 43, MOD is 37. Counted from reports, never grepped from SKILL.md — MOD's
    # DATA-Q* namespace-collision note names ARA's DATA-Q7 and over-counts MOD as 38.
    assert sr.EXPECTED_QUESTIONS == {"ara": 43, "mod": 37}
    rpt = {"findings": [{"question_id": f"Q{i}"} for i in range(37)], "evaluations": []}
    assert sr.check_coverage(rpt, "mod") == []
    assert [c for c in sr.check_coverage(rpt, "ara")]  # same report is short for ARA


# --- MOD score derivation --------------------------------------------------------------

def test_mod_bands_match_the_rubric_boundaries():
    # SKILL.md line 2014, on the 1-4 scale (NOT 1-5).
    assert sr.mod_band(4.0) == "Mature"
    assert sr.mod_band(3.5) == "Mature"
    assert sr.mod_band(3.49) == "Partial"
    assert sr.mod_band(2.5) == "Partial"
    assert sr.mod_band(2.49) == "Needs Work"
    assert sr.mod_band(1.5) == "Needs Work"
    assert sr.mod_band(1.49) == "Not Ready"
    assert sr.mod_band(1.0) == "Not Ready"


def test_overall_score_must_be_the_mean_of_categories():
    rpt = {"overall_score": 3.0,
           "categories": [{"category_id": "INF", "numeric_score": 1.0},
                          {"category_id": "APP", "numeric_score": 1.0}]}
    hits = [c["check"] for c in sr.check_mod(rpt)]
    assert "overall_score_not_mean_of_categories" in hits


def test_rounding_wobble_is_tolerated():
    rpt = {"overall_score": 1.15,
           "categories": [{"category_id": "A", "numeric_score": 1.1},
                          {"category_id": "B", "numeric_score": 1.2}]}
    assert not [c for c in sr.check_mod(rpt)
                if c["check"] == "overall_score_not_mean_of_categories"]


def test_category_band_must_match_its_own_number():
    rpt = {"categories": [{"category_id": "INF", "numeric_score": 1.2,
                           "score_rating": "Partial"}]}
    assert "category_band_mismatch" in [c["check"] for c in sr.check_mod(rpt)]


# --- source loading: prior analysis output is NOT source --------------------------------

def test_prior_analysis_output_is_excluded_from_the_source_view():
    """legacy-shipping-api ships a previously generated MOD report inside the fixture.

    At 93 KB it was 89% of the fixture, and feeding it in let the model grade a report
    against a near-copy of itself: it cited a "Reference report" nobody supplied, called
    five findings fabrications purely for disagreeing with that stale file, and both
    shipping-api scores became the only outliers in the set (ARA 0.52 vs 0.72-0.82,
    MOD 0.55 vs 0.82-0.92). Excluding it moved them to 0.72 / 0.88.
    """
    src = sr.load_source("legacy-shipping-api")
    assert src, "fixture source should load"
    assert "modernization-readiness-analysis" not in src
    assert "classification_consistency_check" not in src
    # ...while the real code is still there.
    assert "server.js" in src
    assert "k8s/deployment.yaml" in src


def test_source_loads_real_code_for_a_clean_fixture():
    src = sr.load_source("legacy-loan-calculator")
    assert "LoanAction.java" in src
    assert "struts-config.xml" in src


def test_unknown_repo_yields_empty_source_rather_than_raising():
    assert sr.load_source("does-not-exist") == ""


# --- discovery -------------------------------------------------------------------------

def test_discovery_finds_all_11_repos_on_both_analyses():
    units = sr.discover()
    assert len(units) == 22, f"expected 11 repos x 2 analyses, got {len(units)}"
    assert len({r for r, _ in units}) == 11


def test_portfolio_rollups_are_excluded_from_scoring():
    """Two identical-input portfolio runs produced 368 -> 155 findings and 11 -> 5
    services, so count- and text-level scoring is meaningless there. A portfolio scorer
    has to be categorical/ordinal only — scoring them here would manufacture noise."""
    assert not [r for r, _ in sr.discover() if r.startswith("harness-portfolio")]


# --- the rubrics stay verbatim ---------------------------------------------------------

def test_rubrics_are_the_benchmark_prompts_verbatim():
    """The point of carrying these verbatim is comparability with the benchmarking team.

    Paraphrasing them silently decouples our scores from theirs, so pin the load-bearing
    clauses — especially the error-weighting asymmetry, which is what makes a missed
    blocker cost more than a spurious INFO.
    """
    assert "43 questions across the 8 sections" in sr.ARA_RUBRIC
    # Match on a single line: the prompts are carried with their original hard wraps, so a
    # phrase spanning a line break will not appear contiguously.
    assert "missed agent-safety blocker is the" in sr.ARA_RUBRIC
    assert "expensive error" in sr.ARA_RUBRIC
    assert "<score>X.X</score>" in sr.ARA_RUBRIC
    assert "37 questions across the 5 categories" in sr.MOD_RUBRIC
    assert "missed High" in sr.MOD_RUBRIC
    assert "<score>X.X</score>" in sr.MOD_RUBRIC


def test_system_prompt_demands_groundedness_not_plausibility():
    sp = sr.SYSTEM_PROMPT.lower()
    assert "fabrication" in sp
    assert "miss" in sp
    # It must not reward tone or formatting — the failure mode of a fluent wrong report.
    assert "confident tone" in sp or "fluent" in sp


# --- fallback runner -------------------------------------------------------------------

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
