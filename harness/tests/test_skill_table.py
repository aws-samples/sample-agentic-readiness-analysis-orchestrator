"""Tests for skill_table.py — the shared read of the managed TDs' severity tables.

This parse is load-bearing in a non-obvious way: it is what tells the differ that a
BLOCKER -> RISK-SAFETY move on AUTH-Q5 is a CORRECTION rather than a safety relaxation. If a
TD heading format drifts and the parse silently returns a partial table, over-escalation
detection turns off and legitimate rubric fixes get scored as degradations again. So these
tests assert the parse is complete and fail loudly when it is not.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))

import skill_table as st  # noqa: E402


def test_the_severity_table_is_parsed_from_the_td_not_transcribed():
    ara, mod = st.parse_questions("ara"), st.parse_questions("mod")
    assert len(ara) == st.EXPECTED_QUESTIONS["ara"] == 43
    # A naive heading grep returns 38 for MOD — INF-Q1 "Managed Compute" appears twice.
    assert len(mod) == st.EXPECTED_QUESTIONS["mod"] == 37


def test_auth_q5_is_risk_safety_which_is_the_whole_point():
    """The regression this module exists to prevent. AUTH-Q5 Credential Management is
    RISK-SAFETY UNCONDITIONALLY (SKILL.md:870) — not a BLOCKER, and not conditional."""
    q = st.parse_questions("ara")["AUTH-Q5"]
    assert q["severity"] == "RISK-SAFETY"
    assert q["conditional"] is False
    assert q["title"] == "Credential Management"


def test_the_scope_dependent_questions_are_marked():
    """The ⚡ marker covers NINE questions, in two groups that are easy to conflate:

      - 5 CONDITIONAL BLOCKERs — escalate to BLOCKER only for a write-enabled agent scope.
      - 4 SCOPE-CALIBRATED RISK-SAFETY — severity calibrated by scope, never a blocker.

    Both are excluded from over-escalation correction (their severity is genuinely
    scope-dependent, so a downgrade is a judgement call rather than a mechanical fix).
    """
    ara = st.parse_questions("ara")
    conditional = {q for q, v in ara.items() if v["conditional"]}
    assert conditional == {"API-Q4", "STATE-Q1", "AUTH-Q6", "DATA-Q1", "DATA-Q2",
                           "STATE-Q3", "STATE-Q6", "HITL-Q1", "HITL-Q2"}
    # The conditional BLOCKERs specifically.
    assert {q for q in conditional if ara[q]["severity"] == "BLOCKER"} == \
        {"API-Q4", "STATE-Q1", "AUTH-Q6", "DATA-Q1", "DATA-Q2"}


def test_only_api_q1_and_auth_q1_are_unconditional_blockers():
    """These are the ONLY two questions whose downgrade is always a real relaxation."""
    ara = st.parse_questions("ara")
    hard = {q for q, v in ara.items()
            if v["severity"] == "BLOCKER" and not v["conditional"]}
    assert hard == {"API-Q1", "AUTH-Q1"}


def test_mod_questions_carry_no_severity():
    """MOD scores 1-4 per question instead of assigning a severity class."""
    assert all(not v["severity"] for v in st.parse_questions("mod").values())


def test_a_missing_td_returns_empty_rather_than_raising(monkeypatch):
    monkeypatch.setitem(st.SKILLS, "ara", REPO / "definitions" / "NOPE.md")
    assert st.parse_questions("ara") == {}


# --- is_over_escalation_correction ------------------------------------------------------

def test_correcting_auth_q5_to_its_documented_severity_is_a_correction():
    assert st.is_over_escalation_correction("ara", "AUTH-Q5", "BLOCKER", "RISK-SAFETY")


def test_downgrading_a_real_blocker_is_not_a_correction():
    """API-Q1 is documented BLOCKER, so losing it is a genuine safety relaxation."""
    assert not st.is_over_escalation_correction("ara", "API-Q1", "BLOCKER", "RISK-SAFETY")


def test_a_scope_dependent_downgrade_is_never_auto_excused():
    """All 9 ⚡ questions are a real judgement call, not a mechanical correction."""
    for qid in ("API-Q4", "STATE-Q1", "AUTH-Q6", "DATA-Q1", "DATA-Q2",
                "STATE-Q3", "STATE-Q6", "HITL-Q1", "HITL-Q2"):
        assert not st.is_over_escalation_correction("ara", qid, "BLOCKER", "RISK-SAFETY"), qid


def test_understating_below_the_documented_severity_is_not_a_correction():
    """The dangerous direction. AUTH-Q5 is RISK-SAFETY; dropping it to RISK-QUALITY or INFO
    understates it and must still alert."""
    assert not st.is_over_escalation_correction("ara", "AUTH-Q5", "BLOCKER", "RISK-QUALITY")
    assert not st.is_over_escalation_correction("ara", "AUTH-Q5", "RISK-SAFETY", "INFO")


def test_a_correction_must_land_exactly_on_the_documented_severity():
    # BLOCKER -> INFO overshoots past RISK-SAFETY; not a clean correction.
    assert not st.is_over_escalation_correction("ara", "AUTH-Q5", "BLOCKER", "INFO")


def test_unknown_qid_or_missing_severity_is_not_a_correction():
    assert not st.is_over_escalation_correction("ara", "NOPE-Q99", "BLOCKER", "RISK-SAFETY")
    assert not st.is_over_escalation_correction("ara", None, "BLOCKER", "RISK-SAFETY")
    assert not st.is_over_escalation_correction("ara", "AUTH-Q5", None, "RISK-SAFETY")


def test_getting_stricter_is_not_a_correction():
    """Direction matters — gaining severity is the rubric tightening, never a 'correction'."""
    assert not st.is_over_escalation_correction("ara", "AUTH-Q5", "RISK-QUALITY", "RISK-SAFETY")


# --- tier arithmetic (moved here with the parser) ---------------------------------------

@pytest.mark.parametrize("blockers,risk_safety,tier,qual", [
    (3, 0, "Not Agent-Integrable", None),
    (1, 0, "Remediation Required", None),
    (0, 3, "Pilot-Ready", "Safety Concerns"),
    (0, 1, "Pilot-Ready", None),      # 1-2 RISK-SAFETY: NO qualifier
    (0, 0, "Agent-Ready", None),
])
def test_ara_tier_arithmetic(blockers, risk_safety, tier, qual):
    assert st.expected_ara_tier(blockers, risk_safety) == (tier, qual)


@pytest.mark.parametrize("score,band", [
    (4.0, "Mature"), (3.5, "Mature"), (3.4, "Partial"), (2.5, "Partial"),
    (2.4, "Needs Work"), (1.5, "Needs Work"), (1.4, "Not Ready"), (1.0, "Not Ready"),
])
def test_mod_bands(score, band):
    assert st.mod_band(score) == band
