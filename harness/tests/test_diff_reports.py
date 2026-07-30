#!/usr/bin/env python3
"""
Tests for diff-reports.py — the ATX-free core of the harness.

Strategy: load REAL reports from the committed harness/golden/ baseline, deep-copy them
into synthetic before/after pairs, mutate the "after" to simulate the kind of change a TD
edit would produce, and assert the differ reports exactly the right dimension moved.

golden/ IS the differ's real-world input (the same tree an MR diffs against), so testing
the differ against it keeps the tests and the harness reading one dataset — no separate
sample corpus to drift. golden/ is a flat directory (all *-report.json in one folder), so
load_tree(GOLDEN) picks up ARA + MOD + portfolio together; where a test needs one analysis
in isolation it filters the loaded tree by key rather than by subdirectory.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_diff_reports.py     (no pytest needed — has a fallback runner)
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "harness" / "golden"
# golden/ is flat — ARA and MOD reports live side by side. The per-analysis "dirs" the
# tests used to load are now the same folder; load_tree() classifies by content, and the
# few tests that need one analysis alone filter the tree by key.
ARA_DIR = GOLDEN
MOD_DIR = GOLDEN

# Import the hyphenated module by path.
_spec = importlib.util.spec_from_file_location(
    "diff_reports", REPO / "harness" / "diff-reports.py")
dr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dr)  # type: ignore


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


ARA_REPO = GOLDEN / "monolith-ara-report.json"
MOD_REPO = GOLDEN / "monolith-mod-report.json"
ARA_PORT = GOLDEN / "harness-portfolio-portfolio-ara-report.json"
MOD_PORT = GOLDEN / "harness-portfolio-portfolio-mod-report.json"


# --- classification / loading --------------------------------------------------------

def test_classify_all_four_types():
    assert dr.classify_report(ARA_REPO, _load(ARA_REPO))[:2] == ("ara", "repo")
    assert dr.classify_report(MOD_REPO, _load(MOD_REPO))[:2] == ("mod", "repo")
    assert dr.classify_report(ARA_PORT, _load(ARA_PORT))[:2] == ("ara", "portfolio")
    assert dr.classify_report(MOD_PORT, _load(MOD_PORT))[:2] == ("mod", "portfolio")


def test_metadata_files_ignored():
    # `.metadata.json` sidecars must be skipped by classification regardless of content —
    # assert on the filename rule directly so the test doesn't depend on a sample file.
    meta = ARA_DIR / "monolith-ara-report.metadata.json"
    assert dr.classify_report(meta, {"analysis_type": "ara"}) is None


def test_identical_trees_are_no_op():
    tree = dr.load_tree(ARA_DIR)
    assert tree, "expected to load ARA reports"
    impact = dr.build_impact(tree, copy.deepcopy(tree))
    assert impact["no_op"] is True
    assert impact["changed_tds"] == []


# --- D1 findings ---------------------------------------------------------------------

def test_d1_added_and_removed_finding():
    before = _load(ARA_REPO)
    after = copy.deepcopy(before)
    # remove first finding, add a synthetic new one
    removed_qid = after["findings"][0]["question_id"]
    after["findings"] = after["findings"][1:]
    after["findings"].append({"question_id": "AUTH-Q99", "category_id": "AUTH",
                              "severity": "High", "title": "synthetic"})
    d = dr.diff_findings(before, after)
    assert "AUTH-Q99" in d["added"]
    assert removed_qid in d["removed"]


def test_d1_reseverity_detected():
    before = _load(ARA_REPO)
    after = copy.deepcopy(before)
    after["findings"][0]["severity"] = "Low"  # was High
    d = dr.diff_findings(before, after)
    assert any(r["question_id"] == before["findings"][0]["question_id"]
               for r in d["reseveritied"])


def test_d1_native_severity_nesting_ara_repo():
    # per-repo ARA nests native_severity under ara_metadata
    before = _load(ARA_REPO)
    f = before["findings"][0]
    assert dr._native_severity(f) == (f.get("ara_metadata") or {}).get("native_severity")


# --- D2 tier -------------------------------------------------------------------------

def test_d2_repo_tier_change():
    before = _load(MOD_REPO)
    after = copy.deepcopy(before)
    after["classification"]["tier"] = "Cloud-Native-Ready"
    d = dr.diff_tier_repo(before, after, "mod")
    assert d["changed"] is True
    assert d["after"] == "Cloud-Native-Ready"


def test_d2_portfolio_distribution_shapes():
    # ARA uses {count,percentage}; MOD uses flat ints — both must diff cleanly.
    ara = _load(ARA_PORT)
    ara_after = copy.deepcopy(ara)
    # bump a readiness bucket count
    rd = ara_after["executive_dashboard"]["readiness_distribution"]
    first = next(iter(rd))
    rd[first]["count"] = (rd[first].get("count") or 0) + 1
    d = dr.diff_distribution(ara, ara_after, "ara")
    assert d["changed"] is True

    mod = _load(MOD_PORT)
    mod_after = copy.deepcopy(mod)
    td = mod_after["executive_dashboard"]["tier_distribution"]
    k = next(iter(td))
    td[k] = (td[k] or 0) + 1
    d2 = dr.diff_distribution(mod, mod_after, "mod")
    assert d2["changed"] is True


# --- D3 pathways ---------------------------------------------------------------------

def test_d3_pathway_newly_triggered_repo():
    before = _load(MOD_REPO)
    after = copy.deepcopy(before)
    # flip a Not-Triggered pathway to Triggered (per-repo uses `status`)
    flipped = None
    for p in after["pathways"]:
        if str(p.get("status")).lower() != "triggered":
            p["status"] = "Triggered"
            flipped = p.get("id") or p.get("name")
            break
    d = dr.diff_pathways(before, after)
    if flipped:
        assert flipped in d["newly_triggered"]


def test_d3_portfolio_uses_portfolio_status():
    before = _load(MOD_PORT)
    after = copy.deepcopy(before)
    flipped = None
    for p in after["pathways"]:
        if str(p.get("portfolio_status")).lower() == "triggered":
            p["portfolio_status"] = "Not Triggered"
            flipped = p.get("id") or p.get("name")
            break
    d = dr.diff_pathways(before, after)
    if flipped:
        assert flipped in d["newly_suppressed"]


# --- D4 programs ---------------------------------------------------------------------

def test_d4_program_added_and_removed():
    before = _load(MOD_PORT)
    after = copy.deepcopy(before)
    # suppress an existing triggered program
    removed = None
    for a in after["recommended_actions"]:
        if a.get("acronym") and str(a.get("status")).lower() == "triggered":
            a["status"] = "Not Triggered"
            removed = a["acronym"]
            break
    # add a new triggered program
    after["recommended_actions"].append(
        {"acronym": "ZZZ", "type": "program", "status": "Triggered"})
    d = dr.diff_programs(before, after)
    assert "ZZZ" in d["added"]
    if removed:
        assert removed in d["removed"]


def test_d4_short_program_extraction():
    assert dr._short_program("Experience-Based Acceleration (EBA)") == "EBA"
    assert dr._short_program("MAP") == "MAP"


def test_d4_per_repo_actions_have_no_programs():
    # per-repo ARA recommended_actions have no acronym → not counted as programs
    repo = _load(ARA_REPO)
    m = dr._program_status_map(repo)
    assert m == {}


# --- D5 score band-crossing ----------------------------------------------------------

def test_d5_band_crossing_flagged_category():
    before = _load(MOD_REPO)
    after = copy.deepcopy(before)
    # move one category across a band boundary
    cat = after["categories"][0]
    cat["score_rating"] = "Mature" if cat["score_rating"] != "Mature" else "Not Ready"
    d = dr.diff_score_repo(before, after)
    assert cat["category_id"] in d["categories"]
    assert d["categories"][cat["category_id"]]["band_crossed"] is True


def test_d5_within_band_wobble_not_flagged():
    before = _load(MOD_REPO)
    after = copy.deepcopy(before)
    # nudge numeric score but keep the SAME score_rating → must NOT flag
    after["categories"][0]["numeric_score"] = \
        (after["categories"][0].get("numeric_score") or 2.0) + 0.05
    # score_rating unchanged
    d = dr.diff_score_repo(before, after)
    assert after["categories"][0]["category_id"] not in d["categories"]


def test_d5_overall_band_labels():
    assert dr._overall_band_label(0.5) == "Not Ready"
    assert dr._overall_band_label(1.5) == "Needs Work"
    assert dr._overall_band_label(2.31) == "Partial"
    assert dr._overall_band_label(3.5) == "Mature"
    assert dr._overall_band_label(None) is None


def test_d5_portfolio_band_distribution_shift():
    before = _load(MOD_PORT)
    after = copy.deepcopy(before)
    dist = after["executive_dashboard"]["score_band_distribution"]
    # Bump one band up by 1 and pick a DIFFERENT band with a positive count to drop by 1,
    # rather than hardcoding band names — the real distribution may have any band at 0
    # (a 0 band can't decrement, so it wouldn't register a shift).
    bump = next(iter(dist))
    drop = next((k for k in dist if k != bump and (dist.get(k) or 0) > 0), None)
    dist[bump] = (dist.get(bump) or 0) + 1
    if drop:
        dist[drop] = dist[drop] - 1
    d = dr.diff_score_portfolio(before, after)
    assert d["band_distribution_shift"].get(bump) == 1
    if drop:
        assert d["band_distribution_shift"].get(drop) == -1


# --- end-to-end impact.json ----------------------------------------------------------

def test_build_impact_end_to_end_mod_repo_change():
    before_tree = dr.load_tree(MOD_DIR)
    after_tree = copy.deepcopy(before_tree)
    # pick the per-repo MOD entry and change its tier
    key = next(k for k in after_tree if k[0] == "mod" and k[1] == "repo")
    after_tree[key]["classification"]["tier"] = "Cloud-Native-Ready"
    impact = dr.build_impact(before_tree, after_tree)
    assert impact["no_op"] is False
    assert "modernization-readiness-analysis" in impact["changed_tds"]
    repo_key = key[2]
    assert impact["per_repo"][repo_key]["D2_mod_tier"]["changed"] is True


# --- shape normalizer (real ATX CT 3.7.0 reports) ------------------------------------
#
# ATX CT 3.7.0 emits a different JSON shape per repo. These fixtures are verbatim real
# reports (one per observed shape) snapshotted from a portfolio run on 2026-07-29. The
# normalizer must flatten all of them onto the canonical findings/pathways contract that
# the D1–D5 diff functions consume. See diff-reports.py "Shape normalizer" section.

SHAPES = Path(__file__).resolve().parent / "fixtures" / "shapes"

# (fixture stem, analysis, expected findings floor, expected triggered-pathway count)
# Counts are floors (>=) so content drift between re-runs doesn't make the test brittle;
# the point is that the shape yields findings at all, where the old code returned 0.
_SHAPE_CASES = [
    ("A1_ara_dict_by_category",        "ara", 10, None),
    ("A2_ara_categories_list_noid",    "ara", 10, None),
    ("A3_ara_categories_dict",         "ara", 10, None),
    ("A4_ara_flat_list",               "ara", 10, None),
    ("M1_mod_pathways_list",           "mod", 20, 1),
    ("M2_mod_pathways_dict_counts",    "mod", 0, 1),   # counts-only: 0 findings but pathways fire
    ("M3_mod_pathways_dict_findings",  "mod", 20, 1),
    ("M4_mod_modernization_pathways",  "mod", 15, 1),
]


def test_shape_fixtures_present():
    for stem, *_ in _SHAPE_CASES:
        assert (SHAPES / f"{stem}.json").exists(), f"missing fixture {stem}.json"


def test_every_shape_yields_findings_or_pathways():
    for stem, analysis, min_findings, min_triggered in _SHAPE_CASES:
        data = _load(SHAPES / f"{stem}.json")
        norm = dr.normalize_report(analysis, data)
        assert len(norm["findings"]) >= min_findings, \
            f"{stem}: expected >={min_findings} findings, got {len(norm['findings'])}"
        if min_triggered is not None:
            triggered = [p for p in norm["pathways"]
                         if str(p["status"]).lower() == "triggered"]
            assert len(triggered) >= min_triggered, \
                f"{stem}: expected >={min_triggered} triggered pathways"


def test_normalized_finding_ids_are_unique_and_stringy():
    for stem, analysis, *_ in _SHAPE_CASES:
        norm = dr.normalize_report(analysis, _load(SHAPES / f"{stem}.json"))
        ids = [f["question_id"] for f in norm["findings"]]
        assert all(isinstance(i, str) and i for i in ids), f"{stem}: non-string/empty id"
        assert len(ids) == len(set(ids)), f"{stem}: duplicate question_id after normalize"


def test_diff_across_two_real_shapes_is_stable_on_identity():
    # Same report normalized twice must diff to a no-op (identity), proving the canonical
    # keys are deterministic across the various source shapes.
    for stem, analysis, *_ in _SHAPE_CASES:
        data = _load(SHAPES / f"{stem}.json")
        b = dr.normalize_report(analysis, data)
        a = dr.normalize_report(analysis, copy.deepcopy(data))
        d = dr.diff_findings(b, a)
        assert d["added"] == [] and d["removed"] == [] and d["reseveritied"] == [], \
            f"{stem}: identical report should diff to no-op, got {d}"


def test_added_finding_detected_in_dict_by_category_shape():
    # Mutate the real A1 shape (findings dict keyed by camelCase category) and confirm the
    # normalizer + differ catch a new finding — the exact case the old flat-list code missed.
    data = _load(SHAPES / "A1_ara_dict_by_category.json")
    before = dr.normalize_report("ara", data)
    mutated = copy.deepcopy(data)
    bucket = next(iter(mutated["findings"]))          # first category bucket
    mutated["findings"][bucket].append(
        {"id": "SYN-99", "severity": "BLOCKER", "title": "synthetic injected finding"})
    after = dr.normalize_report("ara", mutated)
    d = dr.diff_findings(before, after)
    assert "SYN-99" in d["added"]


def test_mod_flat_findings_still_extracted():
    # The committed-example MOD shape carries a flat top-level findings[] (not pathway-
    # nested). Regression guard: normalization must not drop it.
    data = _load(MOD_REPO)
    norm = dr.normalize_report("mod", data)
    assert len(norm["findings"]) == len(data["findings"])


# --- partial (scoped) runs ------------------------------------------------------------
# An MR analyzes only the 1-2 fixtures that exercise the edited questions, so `after`
# holds a SUBSET of golden. build_impact() used to UNION the key sets, which made every
# unanalyzed baseline diff against {} — its whole findings list read as DELETED. A
# byte-identical 2-report run produced 540 phantom "removed" findings and flagged all four
# TDs, i.e. a catastrophic-regression verdict on every MR. These pin the intersection
# semantics AND that real drift is still caught inside the narrowed scope.

def _subset(tree: dict, n: int, analysis: str = "ara", scope: str = "repo") -> dict:
    keys = [k for k in sorted(tree) if k[0] == analysis and k[1] == scope][:n]
    return {k: copy.deepcopy(tree[k]) for k in keys}


def test_partial_run_of_unchanged_reports_is_still_a_no_op():
    full = dr.load_tree(GOLDEN)
    impact = dr.build_impact(full, _subset(full, 2))
    assert impact["no_op"] is True, "identical subset must not look like a change"
    assert impact["changed_tds"] == []


def test_partial_run_invents_no_phantom_removals():
    full = dr.load_tree(GOLDEN)
    impact = dr.build_impact(full, _subset(full, 2))
    phantom = sum(len(d.get("removed") or [])
                  for entry in impact["per_repo"].values()
                  for k, d in entry.items()
                  if k.endswith("findings") and isinstance(d, dict))
    assert phantom == 0, f"unanalyzed baselines counted as deletions ({phantom})"


def test_partial_run_only_reports_the_repos_it_analyzed():
    full = dr.load_tree(GOLDEN)
    impact = dr.build_impact(full, _subset(full, 2))
    assert len(impact["per_repo"]) == 2
    assert impact["portfolio"] == {}, "no portfolio was analyzed -> nothing to report"


def test_coverage_records_the_narrowing():
    full = dr.load_tree(GOLDEN)
    impact = dr.build_impact(full, _subset(full, 2))
    cov = impact["coverage"]
    assert cov["partial"] is True
    assert cov["compared"] == 2
    assert cov["baseline_total"] == len(full)
    assert len(cov["not_analyzed"]) == len(full) - 2
    assert cov["unbaselined"] == []


def test_full_run_is_not_marked_partial():
    full = dr.load_tree(GOLDEN)
    cov = dr.build_impact(full, copy.deepcopy(full))["coverage"]
    assert cov["partial"] is False
    assert cov["not_analyzed"] == []
    assert cov["compared"] == len(full)


def test_real_drift_inside_a_partial_run_is_still_detected():
    # The narrowing must not cost sensitivity: drop one finding from the ONE report we
    # analyzed and the differ must still flag it, and only the TD it belongs to.
    full = dr.load_tree(GOLDEN)
    after = _subset(full, 1)
    (key,) = after.keys()
    findings = after[key].get("findings")
    assert findings, "fixture precondition: golden ARA report has a flat findings list"
    dropped = findings[0].get("question_id")
    after[key]["findings"] = findings[1:]
    impact = dr.build_impact(full, after)
    assert impact["no_op"] is False
    assert impact["changed_tds"] == ["agentic-readiness-analysis"]
    removed = impact["per_repo"][key[2]]["D1_ara_findings"]["removed"]
    assert dropped in removed


def test_report_absent_from_golden_is_unbaselined_not_added():
    # A brand-new fixture has no baseline. That's real signal (it must not be hidden),
    # but it also isn't a diff — it belongs in `unbaselined`, not in per_repo.
    full = dr.load_tree(GOLDEN)
    after = _subset(full, 1)
    (key,) = after.keys()
    novel = (key[0], key[1], "brand-new-fixture")
    after[novel] = copy.deepcopy(after[key])
    impact = dr.build_impact(full, after)
    assert impact["coverage"]["unbaselined"] == ["ara/repo/brand-new-fixture"]
    assert "brand-new-fixture" not in impact["per_repo"]


# --- safety alerts (the MR !14 tier regression) ---------------------------------------
# These reproduce the exact delta the judge waved through: AUTH-Q5 dropping from BLOCKER to
# RISK-SAFETY in legacy-loan-calculator, taking blocker_count 3 -> 2 with it and relaxing
# the tier from Not Agent-Integrable to Remediation Required. AUTH-Q5 was outside the edit
# scope, so the noise rule swallowed it. The alerts must fire regardless of scope, because
# the tier move is rubric arithmetic, not variance.

LOAN_ARA = ("ara", "repo", "legacy-loan-calculator")


def _downgrade_a_blocker(tree: dict, qid: str = "API-Q1",
                         to: str = "RISK-SAFETY") -> dict:
    """Mutate an 'after' tree the way MR !14's delta did: one BLOCKER reclassified.

    Defaults to API-Q1, which the TD documents as an UNCONDITIONAL BLOCKER — so downgrading
    it is a genuine safety relaxation that MUST still hold. (AUTH-Q5, the previous default,
    is documented RISK-SAFETY, so downgrading IT is an over-escalation correction, not a
    relaxation — that case has its own tests below.)

    Also decrements the classification counters and re-applies the rubric's own tier rule,
    because in a real report those move together — a test that changed only the finding
    would be asserting against a state the analysis agent can never produce.
    """
    rpt = tree[LOAN_ARA]
    for f in rpt["findings"]:
        if f.get("question_id") == qid:
            f["ara_metadata"]["native_severity"] = to
            break
    else:
        raise AssertionError(f"fixture precondition: {qid} not in the loan-calculator report")
    c = rpt["classification"]
    c["blocker_count"] -= 1
    c["risk_safety_count"] += 1
    # >=3 BLOCKER -> Not Agent-Integrable; 1-2 -> Remediation Required (SKILL.md).
    c["tier"] = "Not Agent-Integrable" if c["blocker_count"] >= 3 else "Remediation Required"
    return tree


def test_lost_blocker_raises_all_three_alerts():
    full = dr.load_tree(GOLDEN)
    before = copy.deepcopy(full)
    after = _downgrade_a_blocker(copy.deepcopy(full))
    impact = dr.build_impact(before, after)
    kinds = {a["kind"] for a in impact["safety_alerts"]}
    assert kinds == {"blocker_downgraded", "blocker_count_fell", "tier_relaxed"}, \
        f"expected all three alerts, got {kinds}"


def test_alerts_attribute_the_tier_move_to_the_lost_blocker():
    # The whole point: a reader must not have to rediscover that "blocker lost" and "tier
    # relaxed" are one event. The tier alert names the cause.
    full = dr.load_tree(GOLDEN)
    after = _downgrade_a_blocker(copy.deepcopy(full))
    impact = dr.build_impact(copy.deepcopy(full), after)
    tier_alert = [a for a in impact["safety_alerts"] if a["kind"] == "tier_relaxed"][0]
    assert tier_alert["attributed_to"] == ["API-Q1"]
    assert "API-Q1" in tier_alert["detail"]
    assert tier_alert["before"] == "Not Agent-Integrable"
    assert tier_alert["after"] == "Remediation Required"


def test_a_clean_rerun_raises_no_alerts():
    # The guard is worthless if it cries on an identity diff — that is how a real alert
    # gets trained away.
    full = dr.load_tree(GOLDEN)
    impact = dr.build_impact(full, copy.deepcopy(full))
    assert impact["safety_alerts"] == []


def test_getting_stricter_is_not_a_safety_alert():
    """Direction matters. A question GAINING a blocker is the rubric tightening."""
    full = dr.load_tree(GOLDEN)
    after = copy.deepcopy(full)
    rpt = after[LOAN_ARA]
    for f in rpt["findings"]:
        if f.get("question_id") == "DATA-Q1":
            f["ara_metadata"]["native_severity"] = "BLOCKER"
            break
    c = rpt["classification"]
    c["blocker_count"] += 1
    impact = dr.build_impact(copy.deepcopy(full), after)
    # Precondition: the differ DID see the reseverity, so silence below is the direction
    # check doing its job and not the mutation failing to register.
    res = impact["per_repo"]["legacy-loan-calculator"]["D1_ara_findings"]["reseveritied"]
    assert [r["question_id"] for r in res] == ["DATA-Q1"]
    assert impact["safety_alerts"] == [], \
        f"a stricter rubric must not alert: {impact['safety_alerts']}"


def test_correcting_an_over_escalation_does_not_hold():
    """The AUTH-Q5 regression, inverted. AUTH-Q5 is documented RISK-SAFETY (unconditional),
    so a report emitting it as BLOCKER is over-escalating. Correcting BLOCKER -> RISK-SAFETY
    is an IMPROVEMENT: it must raise NO tier-material alert, even though blocker_count and
    the tier both move — the same mechanical movement that, for a real blocker, WOULD hold.
    """
    full = dr.load_tree(GOLDEN)
    after = _downgrade_a_blocker(copy.deepcopy(full), qid="AUTH-Q5")
    impact = dr.build_impact(copy.deepcopy(full), after)
    alerts = impact["safety_alerts"]
    assert alerts, "the correction should still be REPORTED, just not held"
    assert not any(a.get("tier_material") for a in alerts), \
        f"an over-escalation correction must not be tier-material: {alerts}"
    kinds = {a["kind"] for a in alerts}
    assert "over_escalation_corrected" in kinds
    assert "tier_corrected" in kinds and "tier_relaxed" not in kinds, \
        f"the tier move is a correction, not a relaxation: {kinds}"


def test_a_real_lost_blocker_still_holds_alongside_a_correction():
    """A downgrade of a GENUINE blocker (API-Q1) must still hold even when an over-escalation
    correction (AUTH-Q5) happens in the same delta — the correction must not launder the
    real relaxation."""
    full = dr.load_tree(GOLDEN)
    after = copy.deepcopy(full)
    _downgrade_a_blocker(after, qid="API-Q1")     # genuine relaxation
    _downgrade_a_blocker(after, qid="AUTH-Q5")    # over-escalation correction
    impact = dr.build_impact(copy.deepcopy(full), after)
    alerts = impact["safety_alerts"]
    assert any(a.get("tier_material") for a in alerts), \
        "a genuine lost blocker must still force a hold"
    downgraded = {a["question_id"] for a in alerts if a["kind"] == "blocker_downgraded"}
    assert downgraded == {"API-Q1"}, f"only the real blocker should be a relaxation: {alerts}"


def test_mod_is_exempt_from_safety_alerts():
    """MOD has no BLOCKER class and no agent-readiness tier — nothing mechanical to assert.

    Deliberately moves the MOD tier along a transition that WOULD fire for ARA
    ("Remediation Required" -> "Pilot-Ready" are both ranked), so the exemption is what
    keeps this quiet rather than the tier name simply being unrecognised.
    """
    full = dr.load_tree(GOLDEN)
    key = ("mod", "repo", "legacy-loan-calculator")
    assert full[key]["classification"]["tier"] == "Remediation Required"
    assert dr._tier_relaxed("Remediation Required", "Pilot-Ready") is True, \
        "fixture precondition: this transition must be one ARA would alert on"
    after = copy.deepcopy(full)
    after[key]["classification"]["tier"] = "Pilot-Ready"
    impact = dr.build_impact(copy.deepcopy(full), after)
    assert impact["safety_alerts"] == [], \
        f"MOD must be exempt, got {impact['safety_alerts']}"
    # ...but the tier move itself must still be reported as an ordinary D2 change.
    assert impact["per_repo"]["legacy-loan-calculator"]["D2_mod_tier"]["changed"] is True


def test_severity_and_tier_rank_helpers():
    assert dr._severity_relaxed("BLOCKER", "RISK-SAFETY") is True
    assert dr._severity_relaxed("RISK-QUALITY", "RISK-SAFETY") is False   # stricter
    assert dr._severity_relaxed("BLOCKER", "BLOCKER") is False
    assert dr._severity_relaxed(None, "BLOCKER") is False                 # unknown -> quiet
    assert dr._severity_relaxed("BLOCKER", "NOT-A-CLASS") is False
    assert dr._tier_relaxed("Not Agent-Integrable", "Agent-Ready") is True
    assert dr._tier_relaxed("Agent-Ready", "Not Agent-Integrable") is False
    assert dr._tier_relaxed("Pilot-Ready", "Pilot-Ready") is None
    assert dr._tier_relaxed("Made Up Tier", "Agent-Ready") is None


def test_malformed_finding_entries_do_not_crash_the_alerts():
    # The differ runs on agent-authored JSON. A non-dict in `reseveritied` must not take
    # down the whole comparison.
    alerts = dr.safety_alerts(
        "r", "ara",
        {"added": [], "removed": [], "reseveritied": ["not-a-dict", None, {}]},
        {"changed": False, "blocker_count": {"before": None, "after": None}})
    assert alerts == []


def test_risk_safety_downgrade_is_reported_but_not_tier_material_while_blockers_remain():
    """Found by reading a real advisory comment, not by reasoning about the code.

    The judge filed `DATA-Q1 RISK-SAFETY -> RISK-QUALITY` as "likely run-to-run variance",
    and the first cut of safety_alerts() — keyed on BLOCKER alone — silently agreed. It IS a
    tier-driving class (SKILL.md 1571-1573), so it must be reported. But all 11 ARA fixtures
    sit at blocker_count 1-3, where risk_safety_count does not affect the tier and drifts
    several findings per rerun, so it must NOT force a hold or the gate fires on every MR.
    """
    full = dr.load_tree(GOLDEN)
    after = copy.deepcopy(full)
    rpt = after[LOAN_ARA]
    assert rpt["classification"]["blocker_count"] > 0, "fixture precondition"
    for f in rpt["findings"]:
        if f.get("question_id") == "DATA-Q1":
            assert f["ara_metadata"]["native_severity"] == "RISK-SAFETY"
            f["ara_metadata"]["native_severity"] = "RISK-QUALITY"
            break
    rpt["classification"]["risk_safety_count"] -= 1
    rpt["classification"]["risk_quality_count"] += 1
    impact = dr.build_impact(copy.deepcopy(full), after)
    kinds = {a["kind"] for a in impact["safety_alerts"]}
    assert "safety_class_downgraded" in kinds, \
        f"a RISK-SAFETY downgrade must be reported, got {kinds}"
    assert all(a["tier_material"] is False for a in impact["safety_alerts"]), \
        "must not hold while blocker_count > 0 — that would fire on nearly every MR"


def test_risk_safety_downgrade_is_tier_material_once_blockers_are_clear():
    """Same movement, blockers cleared: now it IS the tier driver and must hold.

    risk_safety_count 1 -> 0 with blocker_count 0 is the step that declares a repo
    Agent-Ready, which is the single most consequential claim the rubric can make.
    """
    full = dr.load_tree(GOLDEN)
    before = copy.deepcopy(full)
    before[LOAN_ARA]["classification"].update(
        {"blocker_count": 0, "risk_safety_count": 1, "tier": "Pilot-Ready"})
    after = copy.deepcopy(before)
    after[LOAN_ARA]["classification"].update(
        {"blocker_count": 0, "risk_safety_count": 0, "tier": "Agent-Ready"})
    for f in after[LOAN_ARA]["findings"]:
        if f.get("question_id") == "DATA-Q1":
            f["ara_metadata"]["native_severity"] = "RISK-QUALITY"
            break
    impact = dr.build_impact(before, after)
    material = [a for a in impact["safety_alerts"] if a["tier_material"]]
    assert material, f"must hold once risk_safety drives the tier: {impact['safety_alerts']}"
    kinds = {a["kind"] for a in material}
    assert "risk_safety_count_fell" in kinds and "tier_relaxed" in kinds


def test_a_genuine_lost_blocker_is_always_tier_material():
    # A downgrade of an UNCONDITIONAL blocker (API-Q1) always holds. Contrast with
    # test_correcting_an_over_escalation_does_not_hold, where an over-escalated "blocker"
    # (AUTH-Q5, documented RISK-SAFETY) does not.
    full = dr.load_tree(GOLDEN)
    after = _downgrade_a_blocker(copy.deepcopy(full))
    impact = dr.build_impact(copy.deepcopy(full), after)
    assert all(a["tier_material"] for a in impact["safety_alerts"])


# --- question coverage (43 ARA / 37 MOD) ----------------------------------------------

def test_every_golden_per_repo_report_answers_the_full_rubric():
    """Pins the 43/37 totals against the real baseline.

    Counted from the reports, never grepped from SKILL.md: the MOD rubric prose names
    ARA's DATA-Q7 in a namespace-collision note, so grepping over-counts MOD as 38.
    """
    full = dr.load_tree(GOLDEN)
    for (analysis, scope, repo), rpt in full.items():
        if scope != "repo":
            continue
        n = len(dr._answered_question_ids(rpt))
        assert n == dr._EXPECTED_QUESTIONS[analysis], \
            f"{repo} ({analysis}) answers {n}, expected {dr._EXPECTED_QUESTIONS[analysis]}"


def test_evaluations_and_findings_are_disjoint():
    """The bug that made the first cut of the coverage guard fire on all 22 baselines.

    A question that passed lands in `evaluations`, one that flagged in `findings` — they
    never overlap, so coverage is the UNION. Reading either alone sees ~half the rubric.
    """
    full = dr.load_tree(GOLDEN)
    rpt = full[LOAN_ARA]
    ev = {e["question_id"] for e in rpt["evaluations"]}
    fi = {f["question_id"] for f in rpt["findings"]}
    assert ev & fi == set(), "evaluations and findings overlap — coverage math must change"
    assert len(ev) + len(fi) == 43


def test_clean_tree_reports_no_coverage_gaps():
    full = dr.load_tree(GOLDEN)
    impact = dr.build_impact(full, copy.deepcopy(full))
    assert impact["coverage_gaps"] == []


def test_dropped_questions_are_reported_as_a_coverage_gap():
    # A rubric question that stops being answered surfaces as a pile of removed findings,
    # which is exactly what ordinary nondeterministic churn looks like. Assert it
    # structurally so it cannot be filed as noise.
    full = dr.load_tree(GOLDEN)
    after = copy.deepcopy(full)
    rpt = after[LOAN_ARA]
    dropped = {"API-Q1", "AUTH-Q5"}
    rpt["findings"] = [f for f in rpt["findings"]
                       if f.get("question_id") not in dropped]
    rpt["evaluations"] = [e for e in rpt["evaluations"]
                          if e.get("question_id") not in dropped]
    impact = dr.build_impact(copy.deepcopy(full), after)
    gaps = [g for g in impact["coverage_gaps"] if g["repo"] == "legacy-loan-calculator"]
    assert len(gaps) == 1, f"expected one gap, got {impact['coverage_gaps']}"
    gap = gaps[0]
    assert gap["after_answered"] == 41 and gap["expected"] == 43
    assert set(gap["missing_vs_baseline"]) == dropped
    assert "API-Q1" in gap["detail"]


def test_structurally_empty_report_is_not_a_coverage_gap():
    # No question ids at all is a broken/absent report, handled elsewhere. Reporting it as
    # a coverage dip would bury the real gaps in noise.
    assert dr.question_coverage("r", "ara", {"findings": []}, {"findings": []}) is None


def test_unknown_analysis_has_no_expected_total():
    assert dr.question_coverage("r", "portfolio-ish", {}, {}) is None


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
