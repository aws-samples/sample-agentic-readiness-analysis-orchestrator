#!/usr/bin/env python3
"""
Tests for normalize-report.py — the envelope backfill for the pre-publication MR harness.

The normalizer's contract is deliberately narrow: fill a MISSING top-level `analysis_type`
/ `repo_name` from values the harness already knows, and touch NOTHING else. These tests
pin that narrowness — especially that it never overwrites an existing value and never
fabricates structural fields (which would mask real drift the contract check must catch).

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_normalize_report.py    (no pytest needed)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "normalize_report", REPO / "harness" / "normalize-report.py")
nr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nr)  # type: ignore


def test_backfills_missing_envelope_on_ara():
    data = {"findings": [], "evaluations": []}
    changed = nr.normalize(data, "ara", "monolith")
    assert data["analysis_type"] == "ara"
    assert data["repo_name"] == "monolith"
    assert len(changed) == 2


def test_never_overwrites_existing_analysis_type():
    # A WRONG analysis_type is real drift — the normalizer must leave it for the validator.
    data = {"analysis_type": "mod", "repo_name": "x"}
    changed = nr.normalize(data, "ara", "monolith")
    assert data["analysis_type"] == "mod"      # untouched
    assert data["repo_name"] == "x"            # untouched
    assert changed == []


def test_conforming_report_is_a_noop():
    data = {"analysis_type": "ara", "repo_name": "monolith", "findings": []}
    assert nr.normalize(data, "ara", "monolith") == []


def test_portfolio_gets_analysis_type_but_not_repo_name():
    # Portfolio reports are keyed by portfolio_name, not repo — repo_name must NOT be added.
    data = {"executive_dashboard": {}}
    changed = nr.normalize(data, "portfolio-mod", "ignored")
    assert data["analysis_type"] == "portfolio-mod"
    assert "repo_name" not in data
    assert changed == ["analysis_type := 'portfolio-mod'"]


def test_only_envelope_no_structural_fabrication():
    # The seam is envelope-only: a report with no findings/categories stays that way,
    # so the strict contract check can still fail it for the real (structural) reason.
    data = {}
    nr.normalize(data, "ara", "monolith")
    assert set(data.keys()) == {"analysis_type", "repo_name"}
    for structural in ("findings", "evaluations", "categories", "classification",
                       "overall_score", "pathways"):
        assert structural not in data


def test_missing_repo_name_arg_leaves_repo_name_absent():
    data = {}
    changed = nr.normalize(data, "ara", None)
    assert data == {"analysis_type": "ara"}
    assert changed == ["analysis_type := 'ara'"]


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
