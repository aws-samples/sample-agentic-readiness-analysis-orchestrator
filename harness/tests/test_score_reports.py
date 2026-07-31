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
import json
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


def test_the_qualifier_spelling_the_td_actually_emits_is_accepted():
    """The regression this check shipped with, and the reason it survived the suite.

    Every test above spells the qualifier `"Safety Concerns"` — the bare form
    expected_ara_tier() returns, because its first element already carries the tier. But the
    TD's output contract writes the FULL tier label into the field (SKILL.md:2061 and the
    example at 2068), and every real report emits `"Pilot-Ready (Safety Concerns)"`. An `!=`
    between those two spellings of the same verdict fired `missing_safety_qualifier` HIGH on
    3 fixtures x 4 draws, all correct reports.

    That is the worst failure mode this check has: it is documented as pure arithmetic that
    is "safe to act on immediately", so a contributor has no reason to doubt it, and it never
    blocks the merge so nothing else contradicts it. Assert the form the TD PRODUCES, not
    only the form the helper returns.
    """
    for spelling in ("Pilot-Ready (Safety Concerns)", "Safety Concerns",
                     "pilot-ready (safety concerns)"):
        hits = [c["check"] for c in sr.check_ara(_ara(0, 4, "Pilot-Ready", spelling))]
        assert "missing_safety_qualifier" not in hits, spelling
    # Still absent means still flagged — the fix must not turn the check off entirely.
    assert "missing_safety_qualifier" in [
        c["check"] for c in sr.check_ara(_ara(0, 4, "Pilot-Ready", None))]
    # And an unrelated string does NOT satisfy it.
    assert "missing_safety_qualifier" in [
        c["check"] for c in sr.check_ara(_ara(0, 4, "Pilot-Ready", "Pilot-Ready"))]


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


def test_source_resolves_every_fixture_subdirectory_not_just_portfolio():
    """Fixtures live under SEVERAL subdirectories and the loader must find all of them.

    This is a SILENT failure, which is why it needs a test. load_source hardcoded
    `fixtures/portfolio/<repo>`, so the 3 `fixtures/modern/` fixtures resolved to "" — and
    an empty source does not raise, it renders as "(source unavailable)". The judge then
    scored those reports on plausibility alone and called every cited file unverifiable,
    landing MOD at 0.35-0.45. Restoring the source moved them to 0.62-0.92. A missing input
    must never be reportable as a low quality score.
    """
    for repo in ("modern-payments-api", "modern-orders-service", "modern-catalog-graphql"):
        assert sr.load_source(repo), f"{repo} source must resolve (fixtures/modern/)"
    assert sr.load_source("monolith")                    # fixtures/<repo>
    assert sr.load_source("legacy-crm-desktop")          # fixtures/portfolio/<repo>


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
    # 2 attempts but only 1 NUMBER: the variance is unmeasured, and `scored_runs` is what
    # says so. Reading `runs` here would claim a 2-sample stddev off a single score.
    assert agg[("a", "ara")]["scored_runs"] == 1
    assert agg[("a", "ara")]["stddev"] is None
    assert agg[("a", "mod")]["score"] == 0.9


def test_one_draw_reports_no_stddev_rather_than_a_perfectly_stable_zero():
    """`stddev: 0.0` on a single draw is a lie with teeth.

    It is indistinguishable from "measured 3x, never moved", and a threshold derived from
    it is 0.0 — so every subsequent wobble reads as a regression. None means NOT MEASURED,
    and compare_to_baseline must fall back to the noise floor for it.

    `spread` is held to the SAME rule: `max - min` over one score is also 0.0, and it is
    published in SCORES.md right beside the stddev, so a guarded stddev next to a 0.00
    spread still tells the reader the fixture was re-run and never moved.
    """
    (one,) = sr.aggregate([{"repo": "a", "analysis": "ara", "source_tree": "t1",
                            "score": 0.80}])
    assert one["stddev"] is None and one["scored_runs"] == 1
    assert one["spread"] is None, "max-min over a single score is 0.0, not 'stable'"
    # Delta chosen relative to the floor rather than hardcoded, so a re-derived floor does
    # not silently invert what this test is asserting.
    verdict = sr.compare_to_baseline(
        [{"repo": "a", "analysis": "ara",
          "score": round(0.80 + sr.NOISE_FLOOR["ara"] / 2, 3)}], [one])["units"][0]
    assert verdict["verdict"] == "within-noise"          # half the floor is not a measurement
    assert verdict["threshold"] == sr.NOISE_FLOOR["ara"]


def test_a_genuinely_stable_baseline_still_gets_the_noise_floor_not_a_zero_threshold():
    """6 of 14 MOD fixtures score identically across 3 draws (true sd 0.000).

    That means "quiet across 3 draws", NOT "a 0.01 move is meaningful" — the judge reports
    on a coarse grid, so the 4th draw can differ with nothing having changed. The threshold
    must therefore be max(2*stddev, floor): measured variance may only RAISE the bar.
    """
    base = [{"repo": "a", "analysis": "mod", "score": 0.90,
             "stddev": 0.0, "scored_runs": 3, "runs": 3}]
    got = sr.compare_to_baseline(
        [{"repo": "a", "analysis": "mod", "score": 0.88}], base)["units"][0]
    assert got["threshold"] == sr.NOISE_FLOOR["mod"]
    assert got["verdict"] == "within-noise"
    # And a low-but-nonzero sd is likewise floored, never used to shrink the threshold.
    base[0]["stddev"] = 0.005
    got = sr.compare_to_baseline(
        [{"repo": "a", "analysis": "mod", "score": 0.88}], base)["units"][0]
    assert got["threshold"] == sr.NOISE_FLOOR["mod"]
    assert "noise floor" in got["threshold_basis"]


def test_noise_floor_matches_the_committed_baseline():
    """The floor is DERIVED (2*median per-fixture sd), so re-derive it and compare.

    This replaces a hardcoded `>= 0.24` assertion that pinned a floor measured before the
    ARA noise fixes and the n=4 re-baseline. It stayed green while the data moved under it,
    which is precisely how the constant went stale — so this test reads the baseline
    instead of restating a number.
    """
    import statistics as st
    rows = json.loads((REPO / "harness" / "golden-accuracy-baseline.json").read_text())
    for analysis, floor in sr.NOISE_FLOOR.items():
        sds = [r["stddev"] for r in rows
               if r.get("analysis") == analysis
               and isinstance(r.get("stddev"), (int, float))
               and (r.get("scored_runs") or 0) >= 2]
        if len(sds) < 2:            # pragma: no cover - baseline is multi-sample
            continue
        want = 2 * st.median(sds)
        assert abs(floor - want) <= 0.011, (
            f"NOISE_FLOOR['{analysis}'] is {floor}, but 2*median_sd over the committed "
            f"baseline is {want:.4f}. Re-derive the floor or re-baseline, but do not let "
            f"the constant drift from the data it claims to be measured from.")


def test_noise_floor_cannot_exceed_the_observed_score_range():
    """A floor wider than the data makes `within-noise` the only reachable verdict.

    The ARA floor was 0.25 while ARA's entire observed range was 0.065 and no fixture had
    even 0.18 of headroom to a perfect 1.0 — so no possible improvement could ever clear
    the bar. A harness that can only say "not measured" looks like it is working, which is
    why this is pinned separately from the derivation above.
    """
    rows = json.loads((REPO / "harness" / "golden-accuracy-baseline.json").read_text())
    for analysis, floor in sr.NOISE_FLOOR.items():
        scores = [r["score"] for r in rows if r.get("analysis") == analysis
                  and isinstance(r.get("score"), (int, float))]
        if not scores:              # pragma: no cover - baseline covers both analyses
            continue
        headroom = max(1.0 - s for s in scores)
        assert floor < headroom, (
            f"NOISE_FLOOR['{analysis}']={floor} exceeds the largest possible improvement "
            f"({headroom:.3f}) for every baselined fixture: no {analysis} MR could ever be "
            f"reported as improved or regressed.")


def test_one_grid_step_is_never_a_measured_regression():
    """The MOD score alphabet's smallest gap IS the MOD noise floor. Pin the boundary.

    The grader emits MOD scores on a coarse alphabet — the committed baseline contains only
    [0.52, 0.62, 0.72, 0.82, 0.88, 0.92], whose smallest positive gap is exactly 0.04, which
    is exactly NOISE_FLOOR["mod"]. So the smallest move the grader can express is precisely
    the width of the band, and with a strict `abs(delta) < threshold` it fell on the
    measured side: `regressed` on 12 of 14 MOD fixtures for the quietest possible wobble.
    MR !15 was published with "one confirmed accuracy regression" on exactly this.

    The comparison must therefore be `<=`: a delta EXCEEDS the band or it is not a
    measurement. Raising the floor to 2*q=0.08 instead is not the fix — it re-creates the
    ARA disease (0.08 exceeds a 0.92-baseline fixture's entire headroom to 1.0, killing 7
    rows), which is why this is pinned at the boundary and not at the constant.
    """
    rows = json.loads((REPO / "harness" / "golden-accuracy-baseline.json").read_text())
    for analysis, floor in sr.NOISE_FLOOR.items():
        # Reconstruct the grader's observed alphabet from the PER-RUN scores, not the
        # aggregated means — the means are averages of grid points and land off-grid.
        vals = sorted({s for r in rows if r.get("analysis") == analysis
                       for s in (r.get("scores") or [])})
        gaps = [round(y - x, 4) for x, y in zip(vals, vals[1:])]
        if not gaps:                # pragma: no cover - baseline carries per-run scores
            continue
        q = min(gaps)
        if q > floor:               # a grid step wider than the band is genuinely a signal
            continue
        base = [{"repo": "a", "analysis": analysis, "score": 0.80,
                 "stddev": 0.0, "scored_runs": 3, "runs": 3}]
        got = sr.compare_to_baseline(
            [{"repo": "a", "analysis": analysis, "score": round(0.80 - q, 3)}],
            base)["units"][0]
        assert got["verdict"] == "within-noise", (
            f"a single {analysis} grid step ({q}) is the smallest delta the grader can "
            f"emit and does not exceed the {floor} band, so it CANNOT be a measured "
            f"regression — got {got['verdict']}. The comparison must be "
            f"abs(delta) <= threshold.")


def test_a_delta_exactly_on_the_threshold_is_not_measured():
    """Boundary, stated directly and independently of the baseline's grid.

    `abs(delta) == threshold` means the move is exactly the size of the noise we already
    know is there — indistinguishable from it, so NOT MEASURED. Two grid steps still clear
    the bar, which is what keeps the harness able to detect anything at all.
    """
    base = [{"repo": "a", "analysis": "mod", "score": 0.80,
             "stddev": 0.0, "scored_runs": 3, "runs": 3}]
    floor = sr.NOISE_FLOOR["mod"]
    for delta in (floor, -floor):
        got = sr.compare_to_baseline(
            [{"repo": "a", "analysis": "mod", "score": round(0.80 + delta, 3)}],
            base)["units"][0]
        assert got["verdict"] == "within-noise", f"delta {delta:+} == threshold {floor}"
    # Strictly past it is a measurement in both directions — the band must not swallow real
    # movement, or the harness measures nothing.
    for delta, want in ((2 * floor, "improved"), (-2 * floor, "regressed")):
        got = sr.compare_to_baseline(
            [{"repo": "a", "analysis": "mod", "score": round(0.80 + delta, 3)}],
            base)["units"][0]
        assert got["verdict"] == want, f"delta {delta:+} must be {want}"


def test_a_jittery_baseline_raises_its_own_bar_above_the_floor():
    """Per-fixture measured variance may RAISE the threshold, never lower it.

    A fixture measured noisier than its analysis' median (ARA pricing-cgi-style, sd 0.20)
    has earned a stricter bar than the global floor: 2*0.20 = 0.40 > 0.25, so a +0.30 move
    on THAT fixture is still dice. Sampling N trees buys this — it is the only way a unit
    can be held to a higher standard than the prior.

    Deliberately NOT symmetric; see
    test_a_genuinely_stable_baseline_still_gets_the_noise_floor_not_a_zero_threshold. An
    n=3 stddev is far too weak an estimator to justify SHRINKING the bar, and shrinking is
    the direction that manufactures false "improved" verdicts.
    """
    base = [{"repo": "a", "analysis": "ara", "score": 0.55,
             "stddev": 0.20, "scored_runs": 3, "runs": 3}]
    got = sr.compare_to_baseline(
        [{"repo": "a", "analysis": "ara", "score": 0.85}], base)["units"][0]
    assert got["threshold"] == 0.4
    assert "stddev over 3 runs" in got["threshold_basis"]
    assert got["verdict"] == "within-noise"              # +0.30 does not clear 0.40
    # Only a move past the fixture's OWN measured spread counts.
    got = sr.compare_to_baseline(
        [{"repo": "a", "analysis": "ara", "score": 0.99}], base)["units"][0]
    assert got["verdict"] == "improved"


def test_units_are_the_union_of_all_trees_not_just_the_first():
    """A unit missing from trees[0] must still be scored, and must be ANNOUNCED.

    Taking the unit list from trees[0] silently dropped the 3 modern fixtures (they exist
    only in s3): `--trees golden s2 s3` scored 22 units, discarded 5, and reported success.
    The tiers those fixtures were built to cover went unmeasured. Since discover() is the
    seam, assert at that level that a later-tree-only unit is visible.
    """
    trees = [REPO / "harness" / "golden", REPO / "harness" / "samples" / "s3"]
    if not all(t.is_dir() for t in trees):
        return                                            # sample trees are gitignored
    first = set(sr.discover(trees[0]))
    union = set().union(*(set(sr.discover(t)) for t in trees))
    assert union - first, "fixture layout changed; this test needs a later-tree-only unit"
    assert ("modern-catalog-graphql", "ara") in union


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


# --- agent_scope resolution (the ⚡ set) ------------------------------------------------

def test_read_only_resolves_conditional_blockers_down_and_calibrated_to_info():
    t = sr.ara_scope_resolution({"metadata": {"agent_scope": "read-only"}})
    assert "read-only" in t
    # [C] BLOCKERs land on RISK-SAFETY under read-only...
    assert "AUTH-Q6 Immutable Audit Logging -> RISK-SAFETY" in t
    # ...EXCEPT API-Q4, which the TD sends to INFO (SKILL.md:719). This is the bug the parsed
    # per-scope table fixes: the old blanket "BLOCKER -> RISK-SAFETY" over-resolved it.
    assert "API-Q4 Idempotent Write Operations -> INFO" in t
    assert "API-Q4 Idempotent Write Operations -> RISK-SAFETY" not in t
    # [S] RISK questions drop to INFO.
    assert "HITL-Q1 Draft/Pending State -> INFO" in t
    assert "STATE-Q3 Concurrency Controls -> INFO" in t
    # DATA-Q1 uses a Stage-A/B ladder, so it is described rather than reduced to one class.
    assert "DATA-Q1 Sensitive Data Classification: a Stage-A/B ladder" in t


def test_write_enabled_keeps_the_documented_severity():
    t = sr.ara_scope_resolution({"metadata": {"agent_scope": "write-enabled"}})
    assert "AUTH-Q6 Immutable Audit Logging -> BLOCKER" in t
    assert "API-Q4 Idempotent Write Operations -> BLOCKER" in t
    # The [S] questions escalate to their heading class RISK-SAFETY (the read-only bullet's
    # terse "RISK" must not leak through as the resolved severity).
    assert "HITL-Q1 Draft/Pending State -> RISK-SAFETY" in t
    assert "HITL-Q1 Draft/Pending State -> RISK\n" not in t
    assert "-> INFO" not in t


def test_absent_scope_defaults_to_read_only_and_says_so():
    # 1 of 12 golden ARA reports omits the field; silently guessing write-enabled would
    # invert a third of the severity surface, so the default must be explicit in the prompt.
    t = sr.ara_scope_resolution({"metadata": {}})
    assert "ABSENT" in t
    assert "AUTH-Q6 Immutable Audit Logging -> RISK-SAFETY" in t
    assert "API-Q4 Idempotent Write Operations -> INFO" in t


def test_only_the_conditional_questions_are_resolved():
    # AUTH-Q5 is unconditional RISK-SAFETY (SKILL.md:870). If it ever shows up here, the ⚡
    # parse has drifted and the grader is being told a fixed severity is scope-dependent.
    t = sr.ara_scope_resolution({"metadata": {"agent_scope": "read-only"}})
    assert "AUTH-Q5" not in t
    assert "AUTH-Q1" not in t
    # 8 questions resolve via the per-scope bullets; DATA-Q1 is the 9th, described separately.
    bullets = [ln for ln in t.splitlines() if ln.startswith("  - ")]
    assert len(bullets) == 9
    assert sum(1 for ln in bullets if "Stage-A/B ladder" in ln) == 1


def test_scope_resolution_reaches_the_ara_prompt_but_not_mod():
    import json
    rpt = json.loads((REPO / "harness" / "golden"
                      / "legacy-crm-desktop-ara-report.json").read_text())
    assert "THIS REPORT'S `agent_scope` IS" in sr.build_prompt(
        "legacy-crm-desktop", "ara", rpt, "src", [])
    mod = json.loads((REPO / "harness" / "golden"
                      / "legacy-loan-calculator-mod-report.json").read_text())
    # MOD scores 1-4 and has no agent_scope — injecting ARA's ⚡ set would be noise.
    assert "THIS REPORT'S `agent_scope` IS" not in sr.build_prompt(
        "legacy-loan-calculator", "mod", mod, "src", [])


# --- calibration / extended / N/A resolution (the downgrades beyond scope) --------------

def test_calibration_pairs_the_report_flags_with_the_verbatim_rules():
    rpt = {"metadata": {"service_archetype": "stateless-utility",
                        "surface_flags": {"has_http_rpc_surface": True,
                                          "has_auth_surface": False}}}
    t = sr.ara_calibration_resolution(rpt)
    # This report's actual values are stated so the grader applies rules against them...
    assert "service_archetype = `stateless-utility`" in t
    assert "has_http_rpc_surface=True" in t
    # ...and the rule text is verbatim from the TD, not paraphrased.
    assert "[surface-flag]" in t and "[archetype]" in t
    assert "AUTH-Q4" in t          # archetype-calibrated, RISK-SAFETY by default
    assert "only ever DOWNGRADES" in t   # the SKILL.md:292 downgrade-only guard


def test_extended_lists_all_18_triggers_and_names_state_q4():
    t = sr.ara_extended_resolution({"metadata": {}})
    # The biggest false-miss source: STATE-Q4 is a fixed RISK-SAFETY recorded not_evaluated
    # in 9 of 12 goldens. The grader must know its trigger, not read it as an unresolved risk.
    assert "STATE-Q4" in t and "external dependencies" in t
    assert "not_evaluated_extended" in t and "EXCLUDED from scoring" in t
    assert len([ln for ln in t.splitlines() if ln.startswith("  - ")]) == 18


def test_na_resolution_reports_empty_for_application_and_lists_for_library():
    app = sr._na_resolution({"metadata": {"repo_type": "application"}}, "ara")
    assert "all questions apply" in app
    lib = sr._na_resolution({"metadata": {"repo_type": "library"}}, "ara")
    # A library draws ENG-Q1..Q5 as N/A; without this the grader would miss all five.
    assert "ENG-Q1" in lib and "ENG-Q5" in lib
    assert "EXCLUDED from all counts" in lib


def test_mod_calibration_covers_gates_and_archetype_rubrics():
    rpt = {"metadata": {"service_archetype": "stateless-utility",
                        "surface_flags": {"has_persistent_data_store": False}}}
    t = sr.mod_calibration_resolution(rpt)
    assert "INF-Q2" in t and "has_persistent_data_store" in t
    # MOD gates move ARITHMETIC — the block must say they leave the denominator.
    assert "numerator and denominator" in t
    # Archetype-keyed rubrics can raise AND lower, unlike ARA's downgrade-only calibration.
    assert "INF-Q4" in t and "raise and lower" in t


def test_mod_prompt_gets_calibration_and_na_but_not_ara_scope():
    import json
    mod = json.loads((REPO / "harness" / "golden"
                      / "legacy-pricing-cgi-mod-report.json").read_text())
    p = sr.build_prompt("legacy-pricing-cgi", "mod", mod, "src", [])
    assert "MOD SURFACE-FLAG GATES" in p
    assert "REPO TYPE = `" in p
    assert "THIS REPORT'S `agent_scope` IS" not in p


def test_ara_prompt_gets_all_four_resolution_blocks():
    import json
    rpt = json.loads((REPO / "harness" / "golden"
                      / "legacy-pricing-cgi-ara-report.json").read_text())
    p = sr.build_prompt("legacy-pricing-cgi", "ara", rpt, "src", [])
    assert "THIS REPORT'S `agent_scope` IS" in p
    assert "CALIBRATION DOWNGRADES" in p
    assert "EXTENDED QUESTIONS" in p
    assert "REPO TYPE = `application`" in p
    # The corrected API-Q4 resolution must actually reach the assembled prompt.
    assert "API-Q4 Idempotent Write Operations -> INFO" in p




def test_update_baseline_with_an_analysis_filter_merges_instead_of_truncating():
    """A per-analysis re-baseline must not delete the other analysis' rows.

    The two analyses can legitimately have different valid sample sets: a TD edit
    invalidates only ITS OWN prior draws. When the ARA severity-ceiling rule landed, every
    pre-existing ARA tree went stale while MOD's three draws stayed valid. A whole-baseline
    write would force either re-running MOD for nothing, or baselining ARA against reports
    its own TD no longer produces.
    """
    prior = [
        {"repo": "a", "analysis": "ara", "score": 0.50},
        {"repo": "b", "analysis": "ara", "score": 0.60},
        {"repo": "a", "analysis": "mod", "score": 0.90},
    ]
    fresh = [
        {"repo": "a", "analysis": "ara", "score": 0.80},
        {"repo": "b", "analysis": "ara", "score": 0.85},
        # A stray row of the OTHER analysis in the input must be ignored, not written --
        # a partial run would otherwise clobber the good MOD row with a one-draw one.
        {"repo": "a", "analysis": "mod", "score": 0.11},
    ]
    merged, missing, note = sr.merge_baseline(prior, fresh, "ara")
    got = {(r["analysis"], r["repo"]): r["score"] for r in merged}
    assert got == {("ara", "a"): 0.80, ("ara", "b"): 0.85, ("mod", "a"): 0.90}
    assert not missing
    assert "kept 1 mod row(s)" in note


def test_a_merge_announces_a_fixture_that_lost_its_baseline_row():
    """A dropped row is invisible afterwards: comparisons just skip that fixture. Say so."""
    prior = [{"repo": "a", "analysis": "ara", "score": 0.5},
             {"repo": "gone", "analysis": "ara", "score": 0.5}]
    merged, missing, _ = sr.merge_baseline(
        prior, [{"repo": "a", "analysis": "ara", "score": 0.8}], "ara")
    assert missing == {"gone"}
    assert len(merged) == 1


# --- severity ceiling (the mechanism the AUTH-Q5 defect exploited) ---------------------

def test_a_finding_above_its_td_heading_severity_is_flagged():
    """The observed defect, now caught deterministically.

    AUTH-Q5 (Credential Management) is documented RISK-SAFETY unconditionally
    (SKILL.md:870), yet 6 of 12 golden reports emitted it as BLOCKER on severe evidence
    (hardcoded production credentials) -- tier-shifting several repos, since the ARA tier is
    pure arithmetic over blocker_count. It stayed invisible until someone diffed severities
    by hand. High severity because BLOCKER/RISK-SAFETY are the tier-moving classes.
    """
    rpt = _ara(blockers=1, tier="Remediation Required",
               findings=[_f("AUTH-Q5", "BLOCKER")])
    rpt["classification"]["blocker_count"] = 1
    hits = [c for c in sr.check_ara(rpt) if c["check"] == "severity_exceeds_td_ceiling"]
    assert hits and hits[0]["severity"] == "high"
    assert "AUTH-Q5" in hits[0]["detail"] and "RISK-SAFETY" in hits[0]["detail"]


def test_a_finding_at_or_below_its_ceiling_is_clean():
    """Downgrades are LEGITIMATE (calibration only ever downgrades) and must not be flagged.

    Flagging them would fire on every calibrated report and drown the real signal -- and
    understatement is the judge's call, since the TD's downgrade rules are prose with nested
    conditions this check deliberately does not evaluate.
    """
    for sev in ("RISK-SAFETY", "RISK-QUALITY", "INFO"):
        rpt = _ara(findings=[_f("AUTH-Q5", sev)])
        assert not [c for c in sr.check_ara(rpt)
                    if c["check"] == "severity_exceeds_td_ceiling"], sev


def test_a_conditional_question_is_judged_against_its_most_severe_resolution():
    """The 9 ⚡ questions resolve by `agent_scope`, so their ceiling is the strictest
    resolution the TD permits -- this check does not know the report's scope, and guessing
    it wrong would be worse than a slightly loose ceiling. STATE-Q1 is a conditional
    BLOCKER, so BLOCKER must pass here even though read-only would resolve it lower.
    """
    q = sr.parse_questions("ara").get("STATE-Q1") or {}
    assert q.get("conditional"), "STATE-Q1 must be a ⚡ question for this test to mean anything"
    rpt = _ara(blockers=1, tier="Remediation Required",
               findings=[_f("STATE-Q1", "BLOCKER")])
    assert not [c for c in sr.check_ara(rpt)
                if c["check"] == "severity_exceeds_td_ceiling"]


def test_an_unknown_question_id_does_not_trip_the_ceiling_check():
    """A qid absent from the TD has no documented ceiling. Silence beats a false defect."""
    rpt = _ara(findings=[_f("BOGUS-Q99", "BLOCKER")])
    assert not [c for c in sr.check_ara(rpt)
                if c["check"] == "severity_exceeds_td_ceiling"]

# --- the published noise floor must match the code ------------------------------------
# The audit found DESIGN.md still quoting "ARA 0.10, MOD 0.02" -- the values the in-code
# comment documents as WRONG by ~2.5x (they came from re-scoring one report tree, which holds
# the dominant variance source fixed). A contributor following the doc computes a threshold
# 2.5x too small and reads run-to-run noise as a measured improvement. Docs that state a
# threshold are code; pin them.

def test_published_noise_floor_matches_the_code():
    """The doc must state the LIVE floor, and must not present a retired one as current.

    Retired values may still be *named as retired* — DESIGN.md documents both past floors
    and why each was wrong, which is the only thing that stops the constant being "fixed"
    back to a stale number. So the guard is: every stated floor line must carry the live
    value, and any retired value must appear in a sentence marked as retired.
    """
    floor = sr.NOISE_FLOOR
    live = {f"ARA {floor['ara']:.2f}", f"MOD {floor['mod']:.2f}"}
    retired_markers = ("retired", "Too small", "Too large", "was never updated",
                       "understated", "predated")
    for doc in ("DESIGN.md", "README.md"):
        text = (REPO / "harness" / doc).read_text()
        for bad in ("ARA 0.10", "MOD 0.02", "ARA 0.25"):
            if bad in text:
                # Permitted only where the doc explains it is no longer the floor.
                assert any(m.lower() in text.lower() for m in retired_markers), (
                    f"{doc} states '{bad}' with nothing marking it retired; the live floor "
                    f"is ARA {floor['ara']:.2f} / MOD {floor['mod']:.2f}. A floor has "
                    f"exactly one home: score-reports.py NOISE_FLOOR.")
        for want in live:
            assert want in text, f"{doc} never states the live floor '{want}'"


def test_design_doc_describes_the_threshold_as_a_max_not_an_either_or():
    """`max(2*sd, floor)` is the rule: measured variance may only RAISE the bar. An
    "either/or" phrasing invites reimplementing it as a replacement, which would let a
    fixture that happens to read sd=0.00 get a zero threshold."""
    text = (REPO / "harness" / "DESIGN.md").read_text()
    assert "max(2" in text.replace("·", "*").replace(" ", "") or "max(2*sd" in \
        text.replace("·", "*").replace(" ", ""), \
        "DESIGN.md must state the threshold as max(2*sd, NOISE_FLOOR)"


# --- fallback runner -------------------------------------------------------------------
# MUST stay the LAST thing in this file. _run_all() collects globals() at call time, so when
# this block sat mid-file it ran before the remaining tests were defined and silently skipped
# them -- `python3 harness/tests/test_score_reports.py` reported 58 passed while pytest
# collected 64. A green run that quietly omits 6 tests is worse than a red one.

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
