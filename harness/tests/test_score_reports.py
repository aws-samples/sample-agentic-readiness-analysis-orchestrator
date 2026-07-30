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
    # ARA is 43, MOD is 37. A NAIVE heading grep over MOD returns 38 — INF-Q1 "Managed
    # Compute" is present twice — so the parse must dedup by qid (see
    # test_the_severity_table_is_parsed_from_the_td_not_transcribed).
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


# --- multi-run sampling: one tree is a draw, not a measurement --------------------------

def test_aggregate_reports_the_spread_across_report_trees():
    """We are measuring TD OUTPUT QUALITY, so a sample is one RUN OF THE TD.

    Re-scoring a single report N times would measure the scorer's jitter while holding
    constant the thing that actually varies — the analysis agent, which moves 10-20 findings
    per fixture per rerun. So samples are report TREES, and the row carries mean/stddev/
    spread so a claimed improvement can be compared against the noise floor.
    """
    rows = [
        {"repo": "a", "analysis": "ara", "source_tree": "t1", "score": 0.70},
        {"repo": "a", "analysis": "ara", "source_tree": "t2", "score": 0.80},
        {"repo": "a", "analysis": "ara", "source_tree": "t3", "score": 0.90},
    ]
    (agg,) = sr.aggregate(rows)
    assert agg["runs"] == 3
    assert agg["score"] == 0.8                       # the MEAN is the number to act on
    assert agg["spread"] == 0.2                      # ...and this says how far to trust it
    assert abs(agg["stddev"] - 0.0816) < 0.001
    assert agg["scores"] == [0.70, 0.80, 0.90]       # raw draws kept, never discarded
    assert agg["sources"] == ["t1", "t2", "t3"]


def test_aggregate_keeps_units_separate_and_survives_a_failed_run():
    rows = [
        {"repo": "a", "analysis": "ara", "source_tree": "t1", "score": 0.7},
        {"repo": "a", "analysis": "mod", "source_tree": "t1", "score": 0.9},
        # A tree where the Bedrock call failed contributes no score but must not poison
        # the mean or crash the aggregation.
        {"repo": "a", "analysis": "ara", "source_tree": "t2", "error": "throttled"},
    ]
    agg = {(r["repo"], r["analysis"]): r for r in sr.aggregate(rows)}
    assert agg[("a", "ara")]["score"] == 0.7
    assert agg[("a", "ara")]["runs"] == 2 and agg[("a", "ara")]["scores"] == [0.7]
    assert agg[("a", "mod")]["score"] == 0.9


def test_a_report_tree_is_a_parameter_not_a_hardcoded_path():
    # Sampling N runs is only possible if the scorer can read a tree other than golden/.
    after = REPO / "harness" / "_after"
    if not after.is_dir():
        return                                        # scratch tree is gitignored
    assert sr.discover(after), "discover() must accept an alternate tree"
    row = sr.score_report("monolith", "ara", "unused", True, after)
    assert row["source_tree"] == "_after"


# --- the rubrics stay verbatim ---------------------------------------------------------

def test_rubrics_keep_the_benchmark_structure_and_error_weighting():
    """These began as the benchmarking team's prompts and still carry their shape.

    They are no longer verbatim — see test_corrected_rubric_bugs_stay_fixed. What must
    survive any edit is the load-bearing structure: the question counts, the output
    contract, and the error-weighting asymmetry that makes a missed blocker cost more than
    a spurious INFO.
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


def test_corrected_rubric_bugs_stay_fixed():
    """Two statements in the original prompts were FACTUALLY WRONG about our TDs.

    Both were latent rather than harmless. The qualifier rule only misfires once a repo
    reaches blocker_count 0 — which no fixture does yet, so it would have first appeared
    as a mystery failure on the new Pilot-Ready fixtures. Pin them so a future re-sync
    with the benchmarking team cannot silently reintroduce either.
    """
    # 1. The qualifier needs risk_safety_count >= 3 (SKILL.md 2054), not merely "RISK-SAFETY
    #    present without a BLOCKER" — at 1-2 the correct tier is plain Pilot-Ready.
    assert "risk_safety_count` >= 3" in sr.ARA_RUBRIC
    assert "must appear exactly when RISK-SAFETY findings are present" not in sr.ARA_RUBRIC
    # 2. MOD's scale is 1-4 (SKILL.md 1915), not 0-4. 1 is the floor, not a fifth of it.
    assert "1-4, not 0-4" in sr.MOD_RUBRIC
    assert "`overall_score` (0–4)" not in sr.MOD_RUBRIC


def test_the_severity_table_is_parsed_from_the_td_not_transcribed():
    """The prompt's severity table must come FROM SKILL.md on every run.

    A transcribed table drifts silently: someone edits a severity in the TD, the prompt
    keeps asserting the old one as authoritative, and the scorer marks a CORRECT report
    wrong. The TD is the thing under change here, so this is the one staleness the harness
    cannot tolerate.
    """
    ara, mod = sr.parse_questions("ara"), sr.parse_questions("mod")
    assert len(ara) == 43
    assert len(mod) == 37, "MOD must dedup INF-Q1; a naive heading grep returns 38"
    # Severities are read, not assumed.
    assert ara["API-Q1"]["severity"] == "BLOCKER"
    assert ara["DATA-Q4"]["severity"] == "RISK-QUALITY"
    # AUTH-Q5 is RISK-SAFETY unconditionally (SKILL.md:870). Six golden reports emit it as
    # BLOCKER, which pushes them to blocker_count 3 and the worst tier — the table has to
    # state the TD's severity so the grader does not ratify the report's.
    assert ara["AUTH-Q5"]["severity"] == "RISK-SAFETY"
    assert not ara["AUTH-Q5"]["conditional"]
    # The 5 conditional BLOCKERs, marked so a read-only downgrade reads as CORRECT.
    conditional = {q for q, v in ara.items() if v["conditional"] and v["severity"] == "BLOCKER"}
    assert conditional == {"API-Q4", "STATE-Q1", "AUTH-Q6", "DATA-Q1", "DATA-Q2"}
    # MOD questions carry no severity at all — they score 1-4.
    assert all(not v["severity"] for v in mod.values())


def test_a_broken_parse_fails_loudly_rather_than_scoring_with_a_partial_table():
    """Half a table is worse than no table: the model fills the holes by guessing.

    Nothing else catches this — score-reports.py is not wired into .gitlab-ci.yml — so the
    assertion inside ara_context() is the only guard between a TD heading-format edit and
    a confidently wrong score.
    """
    original = sr.SKILLS["ara"]
    try:
        sr.SKILLS["ara"] = original.parent / "NOPE.md"   # simulate a moved/renamed TD
        raised = False
        try:
            sr.ara_context()
        except AssertionError as exc:
            raised = True
            assert "43" in str(exc)                     # tells you what it expected
            assert "NOPE.md" in str(exc)                # ...and where it looked
        assert raised, "a TD that cannot be parsed must raise, not return a partial table"
    finally:
        sr.SKILLS["ara"] = original


def test_ara_context_carries_the_authoritative_severity_table():
    """The omission that made the v1 scores unfair: the model was asked to grade against
    a 43-question rubric it had never been shown, so it fell back on AppSec instinct and
    demanded BLOCKER for 6 findings correctly filed under DATA-Q4."""
    ctx = sr.ara_context()
    # Every question id must appear, or the table has a hole the model will fill by guessing.
    for qid in ("API-Q1", "API-Q4", "AUTH-Q1", "AUTH-Q6", "STATE-Q1", "DATA-Q1", "DATA-Q2"):
        assert qid in ctx, f"{qid} missing from the BLOCKER list"
    assert "DATA-Q4" in ctx and "RISK-QUALITY" in ctx
    # The specific misclassification that cost the most.
    assert "SQL injection" in ctx
    # The scope boundary (SKILL.md:17) — ARA is not a pentest.
    assert "NOT a penetration test" in ctx
    # Conditional/scope-calibrated markers, and that read-only is the DEFAULT.
    assert "write-enabled" in ctx and "read-only" in ctx
    assert "DEFAULT" in ctx


def test_ara_context_names_the_rubrics_own_coverage_gaps():
    # Reports were docked for questions the rubric does not contain. Naming them keeps
    # them out of `misses` and in `rubric_gaps`, where they measure the TD instead.
    ctx = sr.ara_context()
    assert "NOT COVERED BY ANY OF THE 43 QUESTIONS" in ctx
    assert "session fixation" in ctx
    assert "rubric_gaps" in ctx


def test_mod_context_states_the_scale_and_both_ladders():
    ctx = sr.mod_context()
    assert "1-4" in ctx and "There is no 0" in ctx
    # Score-based bands and count-based tiers are DIFFERENT ladders; conflating them was
    # my own earlier error, and a grader that conflates them mis-reads every MOD report.
    assert "Cloud-Native Ready" in ctx      # count-based tier
    assert "Mature" in ctx                  # score-based band
    assert "NO sub-qualifier" in ctx        # "Safety Concerns" is ARA-only
    assert "SOFTER than ARA" in ctx


def test_the_tier_ladder_in_the_prompt_is_rendered_from_the_checker():
    """One arithmetic, one source. The tier rule already lives in SKILL.md and in
    expected_ara_tier(); typing it a third time into a prompt is how the prompt ends up
    contradicting the checker it is meant to agree with."""
    ladder = sr._tier_ladder()
    for blockers, risk_safety in ((3, 0), (1, 0), (0, 3), (0, 1), (0, 0)):
        tier, _ = sr.expected_ara_tier(blockers, risk_safety)
        assert tier in ladder
    # The rule the original benchmark prompt got wrong: 1-2 RISK-SAFETY is plain
    # Pilot-Ready, and the prompt must say so explicitly rather than leaving it inferable.
    assert "Pilot-Ready (NO qualifier)" in ladder
    assert '"Safety Concerns" qualifier' in ladder


def test_both_contexts_are_injected_into_the_prompt():
    rpt = {"findings": [], "evaluations": [], "classification": {}}
    ara = sr.build_prompt("r", "ara", rpt, "src", [])
    mod = sr.build_prompt("r", "mod", rpt, "src", [])
    assert "Authoritative ARA severity table" in ara
    assert "Authoritative MOD scoring context" in mod
    # ...and are NOT crossed over: ARA instincts must not leak into MOD grading.
    assert "Authoritative MOD scoring context" not in ara
    assert "Authoritative ARA severity table" not in mod


def test_deterministic_defects_are_not_charged_to_the_llm_score():
    """One defect, one deduction.

    v1 told the model to "weight each in your score" for defects already reported on the
    checks_failed axis. The fingerprint was unmistakable: 5 of 6 ARA reports at 0.72 had a
    failed check, none of the 5 above 0.72 did.
    """
    checks = [{"severity": "high", "check": "severity_counter_undercount",
               "detail": "risk_quality_count=6 but 10 findings are natively RISK-QUALITY"}]
    p = sr.build_prompt("r", "ara", {"findings": []}, "src", checks)
    assert "Do NOT deduct for them again" in p
    assert "weight it in your score" not in p
    # The fact itself must still reach the model as context.
    assert "severity_counter_undercount" in p


def test_system_prompt_separates_grading_the_report_from_redoing_the_analysis():
    sp = sr.SYSTEM_PROMPT
    assert "NOT RE-DOING THE ASSESSMENT" in sp
    # The three fairness rules that keep a severity disagreement from becoming a "miss".
    # Match within a line: the prompt is hard-wrapped, so "is CORRECT" spans a break.
    assert "at THAT question's severity, is" in sp
    assert "RUBRIC GAP" in sp
    assert "One root cause is ONE item" in sp
    # A miss must be attributable to a question, else it is a rubric gap.
    assert "question_id" in sp and "rubric_gaps" in sp


def test_system_prompt_has_an_explicit_top_band():
    # v1 had no calibration ladder at all, and two zero-miss reports still capped at 0.82 —
    # the model had no signal that a clean report belongs at 0.90+.
    sp = sr.SYSTEM_PROMPT
    assert "0.90-1.00" in sp
    assert "belongs at 0.90+" in sp
    # And that a legitimately terrible repo does not mean an inaccurate report.
    assert "not leniency" in sp


def test_the_deliverables_are_scored_not_just_the_question_answers():
    """The per-question findings are the report's WORKING; the deliverables are the product.

    A report can answer all 43/37 questions correctly and still hand the customer wrong
    advice — a misdetected archetype, a BLOCKER sequenced behind a quality nit, a
    modernization pathway triggered with no supporting question. Those were in the prompt
    payload all along (build_prompt dumps the whole report) but nothing ever asked the model
    to look at them, so they could not affect a score.
    """
    sp = sr.SYSTEM_PROMPT
    assert "GRADE THE DELIVERABLES" in sp
    for d in ("service_archetype", "remediation_roadmap", "recommended_actions",
              "pathways", "top_gaps", "decomposition_strategy"):
        assert d in sp, f"{d} is never mentioned, so it cannot be graded"
    # Phasing is the specific defect a per-question score cannot see.
    assert "belongs in phase 1" in sp
    assert "deliverable_defects" in sp
    # ...and it has to reach the score, not just the output.
    assert "deliverable_defects` after applying rules 1-3" in sp


def test_deliverables_reach_the_model_in_the_report_payload():
    import json as _json
    rpt = _json.loads((REPO / "harness" / "golden"
                       / "legacy-loan-calculator-mod-report.json").read_text())
    p = sr.build_prompt("legacy-loan-calculator", "mod", rpt, "src", [])
    for key in ("pathways", "decomposition_strategy", "top_gaps", "service_archetype"):
        assert key in p


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
