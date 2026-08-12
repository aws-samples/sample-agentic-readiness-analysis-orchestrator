#!/usr/bin/env python3
"""Tests for rebaseline-digest.py — the render-only whole-picture MR digest.

Pure function tests: build synthetic compare/results dicts (the exact schema
score-reports.py emits via --compare-out and -o) and assert the markdown says the right
thing. No network, no AWS, no files.

The load-bearing behaviours pinned here:
  - the verdict headline follows worst-first precedence (partial > regression > below-floor
    > clean) — a reviewer must never read "CLEAN" over a regression,
  - a below-floor report surfaces its WHY from the results rationale,
  - deterministic offline-check failures are reported SEPARATELY from the noisy accuracy
    scores (they are bugs, not draw noise),
  - --results is optional: the verdict + table still render without it.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_rebaseline_digest.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

# The module filename has a hyphen, so import it by path rather than `import`.
_SPEC = importlib.util.spec_from_file_location(
    "rebaseline_digest", Path(__file__).resolve().parents[1] / "rebaseline-digest.py")
digest = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(digest)


def _unit(repo, analysis, was, now, verdict, *, below=False, stale=False):
    return {"repo": repo, "analysis": analysis, "baseline": was, "score": now,
            "delta": round(now - was, 3), "threshold": 0.10, "verdict": verdict,
            "below_quality_floor": below, "baseline_stale": stale}


def _cmp(units, **summary_over):
    scored = [u for u in units if isinstance(u.get("score"), (int, float))]
    summary = {
        "improved": sum(u["verdict"] == "improved" for u in units),
        "regressed": sum(u["verdict"] == "regressed" for u in units),
        "within_noise": sum(u["verdict"] == "within-noise" for u in units),
        "unscored": sum(u["verdict"] == "unscored" for u in units),
        "stale": sum(bool(u.get("baseline_stale")) for u in units),
        "stale_units": [f"{u['repo']} ({u['analysis'].upper()})"
                        for u in units if u.get("baseline_stale")],
        "low_quality": sum(bool(u.get("below_quality_floor")) for u in units),
        "low_quality_units": [f"{u['repo']} ({u['analysis'].upper()})"
                              for u in units if u.get("below_quality_floor")],
        "mean_now": round(sum(u["score"] for u in scored) / len(scored), 3) if scored else None,
        "mean_baseline": round(sum(u["baseline"] for u in scored) / len(scored), 3) if scored else None,
        "mean_delta": None,
    }
    summary.update(summary_over)
    return {"baseline_path": "harness/golden-accuracy-baseline.json", "base_ref": "origin/main",
            "quality_floor": 0.80, "units": units, "summary": summary}


def test_clean_headline():
    md = digest.build_digest(_cmp([_unit("a", "ara", 0.85, 0.86, "within-noise")]), [])
    assert "✅" in md and "CLEAN" in md
    assert "REGRESSION" not in md and "BELOW FLOOR" not in md


def test_regression_beats_below_floor_in_precedence():
    # A regressed AND below-floor sweep must headline REGRESSION, never CLEAN or a mere floor note.
    units = [_unit("a", "ara", 0.85, 0.70, "regressed", below=True)]
    md = digest.build_digest(_cmp(units), [])
    assert "🛑" in md and "REGRESSION" in md
    assert "✅" not in md.split("\n")[2]  # headline line is not the clean one


def test_mean_below_floor_is_a_broad_warning():
    # A mean under the floor means the AVERAGE report is ungrounded — a broad collapse, the
    # hard-warn case (distinct from a lone below-floor outlier under a healthy mean).
    units = [_unit("catalog", "mod", 0.72, 0.62, "within-noise", below=True)]
    md = digest.build_digest(_cmp(units), [], reset=True)
    assert "BELOW FLOOR" in md
    assert "mean groundedness 0.620" in md
    assert "RESET" in md          # names that the ratchet was disabled
    assert "OVERALL HEALTHY" not in md


def test_healthy_mean_with_below_floor_is_merge_safe_with_potential_issues():
    # THE core case: overall mean >= 0.80 is merge-safe even with a below-floor report; the
    # below-floor report is surfaced as a POTENTIAL ISSUE, not a blocker.
    units = [_unit("catalog", "mod", 0.62, 0.62, "within-noise", below=True),
             _unit("healthy", "mod", 0.98, 0.98, "within-noise")]  # mean = 0.80
    md = digest.build_digest(_cmp(units), [])
    assert "OVERALL HEALTHY" in md and "safe to merge" in md
    assert "Potential issues to review" in md
    assert "1 report(s) below the 0.80 floor" in md
    assert "REGRESSION" not in md and "🛑" not in md


def test_below_floor_pulls_rationale_from_results():
    units = [_unit("catalog", "mod", 0.72, 0.62, "within-noise", below=True)]
    results = [{"repo": "catalog", "analysis": "mod", "score": 0.62,
                "summary": "tier over-escalated vs a Pilot-Ready README",
                "fabrications": ["OPS-Q6 invented", "APP-Q5 invented"],
                "misses": [], "deliverable_defects": [], "checks_failed": []}]
    md = digest.build_digest(_cmp(units), results)
    assert "Potential issues — reports below the 0.80 floor" in md
    assert "tier over-escalated" in md
    assert "OPS-Q6 invented" in md


def test_deterministic_defect_makes_a_healthy_sweep_report_potential_issues():
    # A report can be ABOVE the floor and still carry a deterministic defect (helpdesk case):
    # the sweep is merge-safe, but the defect is surfaced as a potential issue, NOT "clean".
    units = [_unit("helpdesk", "mod", 0.85, 0.85, "within-noise")]
    results = [{"repo": "helpdesk", "analysis": "mod", "score": 0.85, "summary": "",
                "fabrications": [], "misses": [], "deliverable_defects": [],
                "checks_failed": [{"check": "mod_count_findings_mismatch", "severity": "medium",
                                   "detail": "medium_count=21 but 20 findings are Medium"}]}]
    md = digest.build_digest(_cmp(units), results)
    assert "OVERALL HEALTHY" in md and "1 deterministic defect(s)" in md
    assert "CLEAN" not in md            # a failed check is not "clean"
    assert "Deterministic defects" in md
    assert "mod_count_findings_mismatch" in md
    assert "medium_count=21" in md
    # It must NOT be in the below-floor section (the report is above the floor).
    assert "reports below the 0.80 floor" not in md


def test_results_optional_still_renders_verdict_and_table():
    units = [_unit("a", "ara", 0.85, 0.70, "regressed", below=True)]
    md = digest.build_digest(_cmp(units), None)  # None => no results file
    assert "REGRESSION" in md
    assert "| repo | analysis |" in md          # table header present
    assert "no results JSON supplied" in md      # degradation pointer
    # Without results we cannot show WHY, so the below-floor detail degrades to a pointer.
    assert "run with `--results`" in md


def test_partial_headline_wins_over_everything():
    units = [_unit("a", "ara", 0.85, 0.86, "within-noise")]
    md = digest.build_digest(_cmp(units), [], partial=True)
    assert "PARTIAL SWEEP" in md and "🛑" in md


def test_noise_note_present_only_with_within_noise():
    with_noise = digest.build_digest(_cmp([_unit("a", "ara", 0.85, 0.86, "within-noise")]), [])
    assert "within-noise' means NOT MEASURED" in with_noise
    only_regressed = digest.build_digest(
        _cmp([_unit("a", "ara", 0.85, 0.60, "regressed")]), [])
    assert "within-noise' means NOT MEASURED" not in only_regressed


def test_table_and_flags():
    units = [_unit("doc", "ara", 0.80, 0.72, "within-noise", below=True, stale=True)]
    md = digest.build_digest(_cmp(units), [])
    assert "| doc | ARA |" in md
    assert "✗ below floor" in md and "⚠ stale" in md


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
