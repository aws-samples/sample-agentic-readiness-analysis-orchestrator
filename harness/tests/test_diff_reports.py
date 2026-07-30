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
