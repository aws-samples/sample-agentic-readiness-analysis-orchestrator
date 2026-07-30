#!/usr/bin/env python3
"""
Tests for select-fixtures.py — the MR cost governor.

This module decides how much an MR costs. A regression here is expensive in a way the
other harness tests are not: silently widening the selection puts the pipeline back on
the ~39h / 22-unit path that blew the log cap, while silently narrowing it (or picking a
fixture that can't observe the edited category) makes the harness report "no impact" for
a change that really did move scores. So these tests pin BOTH directions.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_select_fixtures.py    (no pytest needed)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "select_fixtures", REPO / "harness" / "select-fixtures.py")
sf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sf)  # type: ignore

# A miniature usecases.yaml. Deliberately hand-built rather than loaded from the real
# file so these tests pin the ALGORITHM and don't churn when a fixture is added.
USECASES = {
    "fixtures": [
        {"id": "api-heavy", "path": "harness/fixtures/api-heavy",
         "axes": {"has_api": "rest", "has_iac": True, "auth_present": "oauth"},
         "expectations": {"ara": {"must_have_categories": ["API", "AUTH", "OBS"]},
                          "mod": {"must_have_categories": ["INF", "SEC"]}}},
        {"id": "batch-only", "path": "harness/fixtures/batch-only",
         "axes": {"has_api": "none", "has_iac": False, "auth_present": "none"},
         "expectations": {"ara": {"must_have_categories": ["STATE", "DATA"]},
                          "mod": {"must_have_categories": ["APP"]}}},
        {"id": "iac-rich", "path": "harness/fixtures/iac-rich",
         "axes": {"has_api": "rest", "has_iac": True, "auth_present": "none"},
         "expectations": {"ara": {"must_have_categories": ["API"]},
                          "mod": {"must_have_categories": ["INF", "OPS", "APP"]}}},
        # Participates in MOD only — must never be chosen for an ARA selection.
        {"id": "mod-only", "path": "harness/fixtures/mod-only",
         "axes": {"has_iac": True},
         "expectations": {"mod": {"must_have_categories": ["INF"]}}},
    ]
}


def ids(chosen):
    return [c["id"] for c in chosen]


# --- category matching ----------------------------------------------------------------

def test_picks_fixture_that_exercises_the_touched_category():
    chosen = sf.select(USECASES, "ara", {"API"}, 1)
    # api-heavy and iac-rich both cover API; the axis tie-break (auth_present) favours
    # api-heavy, so a 1-fixture MR gets the better probe.
    assert ids(chosen) == ["api-heavy"]


def test_excludes_fixtures_that_cannot_observe_the_category():
    # batch-only has no API category at all — selecting it for an API edit would report
    # "no impact" for a change that really did move scores.
    chosen = sf.select(USECASES, "ara", {"API"}, 4)
    assert "batch-only" not in ids(chosen)


def test_fixture_not_participating_in_the_analysis_is_never_selected():
    chosen = sf.select(USECASES, "ara", set(), 4)
    assert "mod-only" not in ids(chosen), "mod-only has no ara expectations"


def test_multi_category_edit_prefers_highest_overlap():
    # iac-rich covers all three MOD categories; api-heavy covers one.
    chosen = sf.select(USECASES, "mod", {"INF", "OPS", "APP"}, 1)
    assert ids(chosen) == ["iac-rich"]


# --- the count contract (this is the cost ceiling) ------------------------------------

def test_count_is_a_hard_ceiling():
    for n in (1, 2, 3):
        assert len(sf.select(USECASES, "ara", {"API", "AUTH", "STATE", "DATA"}, n)) <= n


def test_count_larger_than_the_fixture_pool_does_not_pad():
    chosen = sf.select(USECASES, "ara", {"API"}, 99)
    assert len(chosen) == 2, "only api-heavy and iac-rich cover API"


# --- fallbacks ------------------------------------------------------------------------

def test_no_categories_falls_back_to_broadest_coverage():
    # A prose-only TD edit yields no question ids. We must still return something
    # runnable, and it should be the most representative fixture, not an arbitrary one.
    chosen = sf.select(USECASES, "ara", set(), 1)
    assert ids(chosen) == ["api-heavy"], "3 ara categories beats 2 and 1"


def test_unmatched_category_still_returns_something_runnable():
    # An edit to a category no fixture declares must not select ZERO fixtures — that
    # would silently turn the harness into a no-op for that MR.
    chosen = sf.select(USECASES, "ara", {"NOPE"}, 2)
    assert len(chosen) == 2


# --- determinism ----------------------------------------------------------------------

def test_selection_is_deterministic():
    # Same MR must always pick the same fixtures, or a delta isn't comparable
    # run-to-run and a surprising result isn't reproducible.
    first = ids(sf.select(USECASES, "ara", {"API"}, 2))
    for _ in range(5):
        assert ids(sf.select(USECASES, "ara", {"API"}, 2)) == first


def test_ties_break_on_id_not_dict_order():
    reversed_uc = {"fixtures": list(reversed(USECASES["fixtures"]))}
    a = ids(sf.select(USECASES, "mod", {"INF"}, 4))
    b = ids(sf.select(reversed_uc, "mod", {"INF"}, 4))
    assert a == b, "input ordering must not change the selection"


# --- question-id parsing --------------------------------------------------------------

def test_question_re_extracts_category_prefixes():
    line = "+| API-Q2 | machine-readable spec | RISK-SAFETY | AUTH-Q5 and INF-Q11 |"
    found = {f"{m.group(1)}-Q{m.group(2)}" for m in sf.QUESTION_RE.finditer(line)}
    assert found == {"API-Q2", "AUTH-Q5", "INF-Q11"}


def test_question_re_ignores_non_question_tokens():
    # RISK-SAFETY / RISK-QUALITY are severity labels, not question ids — matching them
    # would invent a bogus "RISK" category and skew every selection.
    line = "+| API-Q2 | something | RISK-SAFETY | RISK-QUALITY |"
    cats = {m.group(1) for m in sf.QUESTION_RE.finditer(line)}
    assert cats == {"API"}


# --- axis tie-breaker -----------------------------------------------------------------

def test_axis_bonus_rewards_the_relevant_axis():
    assert sf.axis_bonus({"has_api": "rest"}, {"API"}) == 1
    assert sf.axis_bonus({"has_api": "none"}, {"API"}) == 0
    assert sf.axis_bonus({"has_iac": True}, {"INF"}) == 1
    assert sf.axis_bonus({"has_iac": False}, {"INF"}) == 0


def test_axis_bonus_ignores_categories_without_a_hint():
    assert sf.axis_bonus({"has_api": "rest"}, {"STATE"}) == 0


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
