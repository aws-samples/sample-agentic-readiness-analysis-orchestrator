#!/usr/bin/env python3
"""
Tests for judge.py — the summarisation layer that decides WHAT THE LLM GETS TO SEE.

These tests deliberately do NOT exercise the Bedrock call. The judge's failure mode in
practice was not a bad model response — it was a good model reasoning correctly over an
incomplete digest. On MR !14 (reclassify API-Q2 RISK-QUALITY -> RISK-SAFETY) the delta
contained exactly one reseveritied finding per repo, but summarize_impact() passed only
a COUNT ("1 reseveritied"). The judge could not see WHICH question moved, so it ruled
`intent_match: mismatch` on precisely the change the intent described, and told the
contributor their edit hadn't taken effect.

So what's pinned here is the CONTRACT BETWEEN THE DIFFER AND THE PROMPT: every fact the
judge needs in order to match a delta against an intent must survive summarisation.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_judge.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location("judge", REPO / "harness" / "judge.py")
judge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(judge)  # type: ignore


def _impact_with_reseverity(qid: str = "API-Q2",
                            native_before: str = "RISK-QUALITY",
                            native_after: str = "RISK-SAFETY") -> dict:
    """An impact.json shaped like the real MR !14 delta: one reseverity, some additions."""
    return {
        "no_op": False,
        "changed_tds": ["agentic-readiness-analysis"],
        "per_repo": {
            "legacy-helpdesk-tickets": {
                "D1_ara_findings": {
                    "added": ["DATA-Q2", "DATA-Q3"],
                    "removed": [],
                    "reseveritied": [{
                        "question_id": qid,
                        "severity": {"before": "High", "after": "High"},
                        "native_severity": {"before": native_before, "after": native_after},
                    }],
                },
            },
        },
        "portfolio": {},
        "coverage": {"compared": 2, "baseline_total": 24, "partial": True,
                     "not_analyzed": ["x"] * 22, "unbaselined": []},
    }


# --- the regression that produced a false `mismatch` ---------------------------------

def test_reseveritied_question_id_reaches_the_judge():
    """The edited question must be NAMED in the digest, not just counted.

    This is the bug: with only "1 reseveritied" in the highlights, the LLM has no way to
    tell an intent about API-Q2 from an intent about AUTH-Q5.
    """
    summ = judge.summarize_impact(_impact_with_reseverity())
    blob = "\n".join(summ["highlights"])
    assert "API-Q2" in blob, (
        "the reseveritied question_id was dropped during summarisation — the judge "
        f"cannot match intent against it. highlights={summ['highlights']}")


def test_reseverity_before_and_after_classes_reach_the_judge():
    # Naming the question isn't enough: "API-Q2 moved" doesn't say which DIRECTION, and
    # RISK-QUALITY -> RISK-SAFETY vs the reverse are opposite intents.
    summ = judge.summarize_impact(_impact_with_reseverity())
    blob = "\n".join(summ["highlights"])
    assert "RISK-QUALITY" in blob and "RISK-SAFETY" in blob, \
        f"before/after severity classes missing from digest: {summ['highlights']}"


def test_reseverity_prefers_native_class_but_falls_back_to_normalized():
    # When only the normalized severity moves (no native class change), report THAT —
    # otherwise the highlight would read "None -> None" and tell the judge nothing.
    impact = _impact_with_reseverity(native_before="RISK-SAFETY", native_after="RISK-SAFETY")
    entry = impact["per_repo"]["legacy-helpdesk-tickets"]["D1_ara_findings"]
    entry["reseveritied"][0]["severity"] = {"before": "Medium", "after": "High"}
    blob = "\n".join(judge.summarize_impact(impact)["highlights"])
    assert "Medium -> High" in blob, f"normalized severity fallback missing: {blob}"
    assert "None" not in blob, f"emitted a None-valued transition: {blob}"


def test_d1_still_reports_counts_and_additions():
    # The naming fix must not displace the existing count/added summary.
    summ = judge.summarize_impact(_impact_with_reseverity())
    blob = "\n".join(summ["highlights"])
    assert "+2 / -0 / 1 reseveritied" in blob
    assert "DATA-Q2" in blob
    assert "D1" in summ["dimensions_moved"]


def test_many_reseverities_are_capped_but_present():
    # A broad rubric edit can move dozens; the digest must stay prompt-sized without
    # silently emitting nothing.
    impact = _impact_with_reseverity()
    entry = impact["per_repo"]["legacy-helpdesk-tickets"]["D1_ara_findings"]
    entry["reseveritied"] = [
        {"question_id": f"API-Q{i}",
         "severity": {"before": "Low", "after": "High"},
         "native_severity": {"before": "RISK-QUALITY", "after": "RISK-SAFETY"}}
        for i in range(20)
    ]
    named = [h for h in judge.summarize_impact(impact)["highlights"]
             if "reseveritied:" in h]
    assert 1 <= len(named) <= 8, f"expected a capped but non-empty list, got {len(named)}"


def test_malformed_reseverity_entry_does_not_crash():
    # impact.json is machine-generated, but the judge is the last stage before a human
    # sees a verdict — it must degrade rather than traceback.
    impact = _impact_with_reseverity()
    impact["per_repo"]["legacy-helpdesk-tickets"]["D1_ara_findings"]["reseveritied"] = [
        "API-Q2", None, {"question_id": "AUTH-Q5"},
    ]
    summ = judge.summarize_impact(impact)          # must not raise
    assert "D1" in summ["dimensions_moved"]
    assert "AUTH-Q5" in "\n".join(summ["highlights"])


# --- coverage plumbing (scoped runs must not read as full sweeps) ---------------------

def test_partial_coverage_is_flagged_for_the_judge():
    summ = judge.summarize_impact(_impact_with_reseverity())
    assert summ["coverage"]["partial"] is True
    assert summ["coverage"]["compared"] == 2
    assert summ["coverage"]["baseline_total"] == 24
    assert summ["coverage"]["not_analyzed_count"] == 22
    note = judge._coverage_note(summ)
    assert "PARTIAL" in note and "2 of 24" in note


def test_full_coverage_note_says_full():
    impact = _impact_with_reseverity()
    impact["coverage"] = {"compared": 24, "baseline_total": 24, "partial": False,
                          "not_analyzed": [], "unbaselined": []}
    note = judge._coverage_note(judge.summarize_impact(impact))
    assert "FULL" in note


# --- edit-scope signal (signal vs. nondeterminism noise) -----------------------------
# The analysis agent is NONDETERMINISTIC: re-running the byte-identical rubric on the same
# fixture moves ~10-20 findings (measured across two golden refreshes of an unedited
# rubric). So on a one-question edit the delta is mostly noise. The judge must be told
# which questions were actually edited or it reads the noise as "the change is far broader
# than stated" — which is exactly the false `mismatch` MR !14 produced.

def test_scope_note_names_the_edited_questions():
    note = judge._scope_note(["API-Q2"])
    assert "API-Q2" in note


def test_scope_note_warns_that_out_of_scope_movement_is_noise():
    note = judge._scope_note(["API-Q2"]).lower()
    assert "nondeterministic" in note
    assert "noise" in note
    # It must explicitly tell the judge not to hang a mismatch on out-of-scope movement.
    assert "mismatch" in note


def test_scope_note_explains_reclassification_shows_as_reseverity():
    # Otherwise the judge expects added/removed findings from a severity change and calls
    # the (correct) absence of them a failure to take effect.
    note = judge._scope_note(["API-Q2"]).lower()
    assert "reseveritied" in note or "severity" in note


def test_scope_note_absent_when_scope_unknown():
    # A full sweep / non-TD change has no "edited questions"; stay silent rather than
    # asserting an empty scope, which would read as "nothing was edited".
    assert judge._scope_note([]) == ""


def test_prompt_carries_scope_and_reseverity_together():
    impact = _impact_with_reseverity()
    prompt = judge.build_user_prompt(
        {"what": "reclassify API-Q2 to RISK-SAFETY"},
        judge.summarize_impact(impact), "", ["API-Q2"])
    assert "questions actually edited: API-Q2" in prompt
    # and the delta evidence the judge needs to match it against
    assert "API-Q2 RISK-QUALITY -> RISK-SAFETY" in prompt


def test_prompt_is_valid_without_scope():
    # Back-compat: the arg is optional and omitting it must not break the prompt.
    prompt = judge.build_user_prompt({"what": "x"},
                                     judge.summarize_impact(_impact_with_reseverity()), "")
    assert "## Observed delta" in prompt
    assert "questions actually edited" not in prompt


def test_system_prompt_requires_causal_story_for_regression():
    # Guard the prompt rule that stops out-of-scope churn being labelled a regression.
    sp = judge.SYSTEM_PROMPT.lower()
    assert "nondeterministic" in sp
    assert "causal" in sp


# --- safety floor (the over-correction the scope note introduced) ---------------------
# Fixing the false `mismatch` created the opposite failure. On MR !14 the delta ALSO moved
# `AUTH-Q5 BLOCKER -> RISK-SAFETY`, dropping blocker_count 3 -> 2 and relaxing the ARA tier
# to Remediation Required. AUTH-Q5 was out of scope, the scope note says out-of-scope
# movement is noise, so the judge filed a real tier regression as "likely noise" and
# returned LGTM/72.
#
# The prompt now carves blockers and tiers out of the noise rule, but a prompt is a request.
# `_enforce_safety_floor` is the guarantee: it runs in code after whichever engine produced
# the verdict, so neither the LLM nor the heuristic fallback can talk it down.

_MR14_ALERTS = [
    {"kind": "blocker_downgraded", "repo": "legacy-loan-calculator",
     "question_id": "AUTH-Q5", "before": "BLOCKER", "after": "RISK-SAFETY",
     "detail": "AUTH-Q5 was a BLOCKER and is now RISK-SAFETY."},
    {"kind": "tier_relaxed", "repo": "legacy-loan-calculator",
     "before": "Not Agent-Integrable", "after": "Remediation Required",
     "attributed_to": ["AUTH-Q5"],
     "detail": "readiness tier moved Not Agent-Integrable -> Remediation Required"},
]
_COVERAGE_GAP = [{"repo": "legacy-loan-calculator", "analysis": "ara", "expected": 43,
                  "after_answered": 41, "missing_vs_baseline": ["API-Q1", "AUTH-Q5"],
                  "detail": "legacy-loan-calculator (ARA) answered 41 of 43"}]


def _lgtm() -> dict:
    """The verdict the judge actually returned on MR !14 — the one that must not survive.

    `score` is on the committed 0.0-1.0 accuracy scale (the scorer's measurement of the
    regenerated report), not a 0-100 judge opinion.
    """
    return {"score": 0.82, "baseline_score": 0.82, "scored": True,
            "verdict": "LGTM", "intent_match": "aligned",
            "quality_regression": False, "concerns": [],
            "rationale": "AUTH-Q5 movement is likely noise.", "_engine": "bedrock"}


def test_alerts_survive_summarisation():
    # The differ computes them; if summarize_impact drops them the floor never sees them
    # and the prompt never mentions them.
    summ = judge.summarize_impact(
        {**_impact_with_reseverity(), "safety_alerts": _MR14_ALERTS,
         "coverage_gaps": _COVERAGE_GAP})
    assert summ["safety_alerts"] == _MR14_ALERTS
    assert summ["coverage_gaps"] == _COVERAGE_GAP


def test_alerts_note_marks_them_as_not_noise():
    note = judge._alerts_note({"safety_alerts": _MR14_ALERTS,
                               "coverage_gaps": _COVERAGE_GAP})
    assert "AUTH-Q5" in note
    assert "Not Agent-Integrable -> Remediation Required" in note
    low = note.lower()
    assert "noise" in low, "the note must explicitly override the noise rule"
    assert "regardless" in low, "it must say edit scope does not excuse these"
    assert "43" in note and "41 of 43" in note


def test_alerts_note_silent_when_there_are_none():
    # A permanently-present empty section trains the reader to skip it.
    assert judge._alerts_note({}) == ""
    assert judge._alerts_note({"safety_alerts": [], "coverage_gaps": []}) == ""


def test_prompt_places_alerts_before_the_highlights():
    # Ordering is deliberate: the judge read the tier change in its highlights and had no
    # signal it was rubric-mechanical. The alerts must land before that evidence.
    prompt = judge.build_user_prompt(
        {"what": "reclassify API-Q2"},
        judge.summarize_impact({**_impact_with_reseverity(),
                                "safety_alerts": _MR14_ALERTS}),
        "", ["API-Q2"])
    assert "SAFETY ALERTS" in prompt
    assert prompt.index("SAFETY ALERTS") < prompt.index("highlights:")


def test_safety_floor_overrides_an_lgtm():
    """The exact MR !14 verdict, forced down.

    The hold rides on verdict / analysis_effect / safety_hold — NOT on the score. The score
    is the scorer's measurement of the regenerated report's accuracy on the committed 0-1
    scale; capping it here would make verdict.json disagree with SCORES.md about the same
    report, and the one number that has to stay comparable to the baseline would stop being
    a measurement at all.
    """
    v = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": _MR14_ALERTS})
    assert v["verdict"] == "needs-work"
    assert v["quality_regression"] is True
    assert v["analysis_effect"] == "degrades"
    assert v["safety_hold"] is True
    assert v["score"] == _lgtm()["score"], \
        "the floor must not rewrite a measured accuracy score"


def test_safety_floor_surfaces_every_alert_as_a_concern():
    v = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": _MR14_ALERTS,
                                              "coverage_gaps": _COVERAGE_GAP})
    blob = "\n".join(c["detail"] for c in v["concerns"])
    assert "AUTH-Q5" in blob
    assert "Not Agent-Integrable -> Remediation Required" in blob
    assert "41 of 43" in blob
    assert len(v["concerns"]) == 3


def test_safety_floor_preserves_the_model_rationale():
    # We downgrade the verdict but do NOT rewrite the reasoning: a reviewer should be able
    # to see that the judge disagreed, which is itself information about the judge.
    v = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": _MR14_ALERTS})
    assert "likely noise" in v["rationale"]


def test_safety_floor_is_idempotent():
    # main() calls it once, but a retry or a future second call must not double-append
    # concerns or re-cap an already-capped score.
    first = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": _MR14_ALERTS})
    n = len(first["concerns"])
    second = judge._enforce_safety_floor(first, {"safety_alerts": _MR14_ALERTS})
    assert len(second["concerns"]) == n


def test_non_tier_material_alert_is_reported_without_forcing_a_hold():
    """Reporting and vetoing are two decisions, not one.

    A RISK-SAFETY downgrade while blocker_count > 0 is real and must reach the reader, but
    that count drifts every rerun — holding on it would make every MR a needs-work, and a
    gate that always fires is a gate nobody reads.
    """
    drift = [{"kind": "safety_class_downgraded", "repo": "legacy-loan-calculator",
              "question_id": "DATA-Q1", "before": "RISK-SAFETY", "after": "RISK-QUALITY",
              "tier_material": False,
              "detail": "DATA-Q1 was RISK-SAFETY and is now RISK-QUALITY."}]
    v = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": drift})
    assert v["verdict"] == "LGTM", "a tier-inert drift must not veto"
    assert v["score"] == 0.82
    assert "safety_hold" not in v
    # ...but it must still be visible.
    assert "DATA-Q1" in "\n".join(c["detail"] for c in v["concerns"])


def test_one_tier_material_alert_holds_even_among_drift():
    drift = {"kind": "safety_class_downgraded", "tier_material": False,
             "detail": "DATA-Q1 drift"}
    v = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": [drift] + _MR14_ALERTS})
    assert v["safety_hold"] is True
    assert v["verdict"] == "needs-work"


def test_alert_without_the_field_defaults_to_holding():
    # Forward/backward compatibility: a missing tier_material must fail SAFE, never quiet.
    v = judge._enforce_safety_floor(
        _lgtm(), {"safety_alerts": [{"kind": "tier_relaxed", "detail": "no flag present"}]})
    assert v["safety_hold"] is True


def test_alerts_note_marks_tier_material_vs_notable():
    note = judge._alerts_note({"safety_alerts": [
        {"kind": "tier_relaxed", "tier_material": True, "detail": "tier moved"},
        {"kind": "safety_class_downgraded", "tier_material": False, "detail": "drift"},
    ]})
    assert "TIER-MATERIAL" in note
    assert "notable" in note


def test_safety_floor_is_a_no_op_without_alerts():
    # It must not turn every clean run into needs-work — that would make the signal useless.
    v = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": [], "coverage_gaps": []})
    assert v["verdict"] == "LGTM"
    assert v["score"] == 0.82
    assert "safety_hold" not in v


def test_safety_floor_never_touches_the_measured_score():
    # The score is a MEASUREMENT, so the floor passes it through untouched in BOTH
    # directions: it neither caps a good score nor lifts a bad one. A low-accuracy report
    # that also trips a safety alert must still report its real accuracy.
    v = judge._enforce_safety_floor(
        {**_lgtm(), "score": 0.05}, {"safety_alerts": _MR14_ALERTS})
    assert v["score"] == 0.05
    assert v["safety_hold"] is True


def test_safety_floor_tolerates_malformed_alerts():
    v = judge._enforce_safety_floor(_lgtm(), {"safety_alerts": ["nope", None],
                                              "coverage_gaps": [None]})
    assert v["verdict"] == "LGTM", "no well-formed alert means nothing to hold on"


def test_system_prompt_exempts_blockers_from_the_noise_rule():
    sp = judge.SYSTEM_PROMPT.lower()
    assert "safety alerts" in sp
    assert "blocker" in sp
    assert "coverage gaps" in sp


def test_scope_note_states_the_limits_of_the_noise_rule():
    """Without this the noise rule reads as unconditional — which is how it swallowed the
    AUTH-Q5 tier regression."""
    note = judge._scope_note(["API-Q2"]).lower()
    assert "blocker" in note
    assert "tier" in note


# --- what the score MEASURES: effect on the analysis, not intent match ----------------
# The score used to answer "does the delta match the stated intent?". That was well
# calibrated but answered the wrong question: it graded the CONTRIBUTOR. An edit that
# landed exactly as described while stripping safety signal scored ~92, and an edit that
# silently failed to apply scored ~15 despite leaving the analysis untouched. Reviewers
# read this number to decide whether merging helps or hurts the assessment, so the score
# now measures effect on the ANALYSIS and intent match is demoted to evidence.
#
# These tests pin the semantics at the seams where a future edit could quietly revert them.

def _empty_impact(partial: bool = False) -> dict:
    return {"no_op": True, "changed_tds": [], "per_repo": {}, "portfolio": {},
            "safety_alerts": [], "coverage_gaps": [],
            "coverage": {"compared": 2 if partial else 24, "baseline_total": 24,
                         "partial": partial, "not_analyzed": ["x"] * 22 if partial else [],
                         "unbaselined": []}}


def _compare(now: float = 0.84, baseline: float = 0.82) -> dict:
    """A compare.json carrying the scorer's MEASUREMENT of the regenerated report."""
    return {"summary": {"mean_now": now, "mean_baseline": baseline,
                        "mean_delta": round(now - baseline, 3)},
            "units": [{"repo": "legacy-loan-calculator", "analysis": "ara",
                       "score": now, "baseline": baseline,
                       "delta": round(now - baseline, 3), "threshold": 0.10,
                       "threshold_basis": "noise floor (n=1)", "verdict": "within-noise"}]}


def test_an_empty_delta_is_neutral_whether_or_not_it_was_predicted():
    """THE defining test of the new semantics.

    The analysis is in byte-identical shape in both cases, so the score must be IDENTICAL —
    not merely close. Under the old intent-match scoring these were 80 and 25, a 55-point
    spread over a delta that did not differ at all. Now the score is the scorer's
    measurement of the report, and the intent cannot reach it by construction: equality is
    the invariant, and any drift means an opinion has leaked back into a measurement.
    """
    summ = judge.summarize_impact(_empty_impact())
    cmp = _compare()
    predicted = judge.judge_heuristic({"what": ""}, summ, cmp)
    unmet = judge.judge_heuristic({"what": "reclassify API-Q2 to RISK-SAFETY"}, summ, cmp)
    assert predicted["analysis_effect"] == "neutral"
    assert unmet["analysis_effect"] == "neutral"
    assert predicted["score"] == unmet["score"] == 0.84, (
        "the intent must not move the score at all — the ANALYSIS is identical in both "
        f"cases. predicted={predicted['score']} unmet={unmet['score']}")
    assert predicted["baseline_score"] == unmet["baseline_score"] == 0.82


def test_the_score_is_the_measurement_not_a_judge_opinion():
    """A no-op does not get a "mid-band" number invented for it.

    The old semantics needed a neutral band because the judge authored the number, so a
    harmless change had to land somewhere that read as neither praise nor damage. There is
    no band to sit in now: the score is whatever the scorer measured the report to be, and
    "harmless" is carried by analysis_effect == "neutral" instead. This test pins that the
    heuristic reports the measurement verbatim rather than substituting a placeholder.
    """
    for intent in ({"what": ""}, {"what": "reclassify API-Q2 to RISK-SAFETY"}):
        v = judge.judge_heuristic(intent, judge.summarize_impact(_empty_impact()),
                                  _compare(now=0.97, baseline=0.96))
        assert v["score"] == 0.97, \
            f"heuristic invented a score instead of reporting the measurement, for {intent}"
        assert v["analysis_effect"] == "neutral", \
            "harmlessness belongs on analysis_effect, not on the measured score"


def test_heuristic_without_a_measurement_cannot_validate():
    """No score => no validation, and that is an error to fix, not a quiet pass.

    The offline heuristic is allowed to be ignorant of DIRECTION, but it must never bless a
    change whose regenerated report was never scored — that would let a scoring failure
    read as a clean run.
    """
    v = judge.judge_heuristic({"what": ""}, judge.summarize_impact(_empty_impact()), None)
    assert v["scored"] is False
    assert v["score"] is None and v["baseline_score"] is None
    assert v["verdict"] == "needs-work", "an unvalidated change must not return LGTM"
    blob = (v["rationale"] + "\n".join(c["detail"] for c in v["concerns"])).lower()
    assert "cannot be validated" in blob or "not possible" in blob


def test_an_unmet_intent_still_becomes_a_concern():
    # Demoted from driving the score, NOT dropped: "your edit did not take effect" is the
    # single most actionable thing the harness can tell a contributor.
    v = judge.judge_heuristic({"what": "reclassify API-Q2 to RISK-SAFETY"},
                              judge.summarize_impact(_empty_impact()))
    assert v["no_op_warning"] is True
    assert v["verdict"] == "needs-work", "an edit that never landed still needs work"
    blob = "\n".join(c["detail"] for c in v["concerns"]).lower()
    assert "no-op" in blob or "never took effect" in blob


def test_offline_heuristic_never_claims_the_analysis_improved():
    # Direction-of-effect is exactly the judgement that needs a model. Claiming "improves"
    # offline would let a degradation ride out as a positive verdict whenever Bedrock is
    # unreachable — the fallback must be honest about what it cannot assess.
    moved = {"no_op": False, "changed_tds": ["agentic-readiness-analysis"],
             "per_repo": {"r": {"D1_ara_findings": {"added": ["DATA-Q2"], "removed": [],
                                                    "reseveritied": []}}},
             "portfolio": {}, "safety_alerts": [], "coverage_gaps": [],
             "coverage": {"compared": 24, "baseline_total": 24, "partial": False,
                          "not_analyzed": [], "unbaselined": []}}
    v = judge.judge_heuristic({"what": "tighten DATA scoring"}, judge.summarize_impact(moved))
    assert v["analysis_effect"] == "neutral", \
        "the offline heuristic cannot judge direction and must not assert 'improves'"
    assert "cannot" in v["rationale"].lower()


def test_safety_floor_marks_the_analysis_as_degraded():
    """A tier-material alert IS a degradation, by the rubric's own arithmetic.

    If the floor only set verdict/score, the comment could render "improves the analysis"
    next to a SAFETY HOLD — the primary axis has to agree with the hold.
    """
    v = judge._enforce_safety_floor({**_lgtm(), "analysis_effect": "improves"},
                                    {"safety_alerts": _MR14_ALERTS})
    assert v["analysis_effect"] == "degrades"
    assert v["safety_hold"] is True


def test_system_prompt_scores_analysis_effect_not_intent_match():
    sp = judge.SYSTEM_PROMPT
    assert "analysis_effect" in sp
    low = sp.lower()
    # The primary question must be stated as an effect on the analysis...
    assert "better or worse" in low
    # ...intent match must be explicitly demoted...
    assert "secondary" in low
    # ...and the mid band must be named, or the model reaches for an extreme on a no-op.
    assert "neutral" in low


def test_system_prompt_forbids_scoring_on_description_accuracy_alone():
    """Both failure directions the inversion is meant to prevent, spelled out for the model."""
    low = judge.SYSTEM_PROMPT.lower()
    assert "do not score a harmless or beneficial change low merely because the" in low
    assert "described accurately" in low


def test_coerce_defaults_effect_to_neutral_not_degrades():
    # A model that omits the field has not claimed harm. Defaulting to "degrades" would
    # trip the degradation framing on well-behaved changes whenever the JSON was terse.
    assert judge._coerce_verdict({"score": 80})["analysis_effect"] == "neutral"
    assert judge._coerce_verdict({"analysis_effect": "nonsense"})["analysis_effect"] == "neutral"
    assert judge._coerce_verdict({"analysis_effect": "degrades"})["analysis_effect"] == "degrades"


def test_effect_survives_coercion_for_every_valid_value():
    for eff in ("improves", "neutral", "degrades"):
        assert judge._coerce_verdict({"analysis_effect": eff})["analysis_effect"] == eff


# --- intent parsing ------------------------------------------------------------------

def test_intent_freeform_becomes_what():
    intent = judge.parse_intent("reclassify API-Q2 from RISK-QUALITY to RISK-SAFETY")
    assert "API-Q2" in intent["what"]


def test_empty_intent_is_safe():
    intent = judge.parse_intent("")
    assert intent["what"] == ""
    assert intent["raw"] == ""


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
