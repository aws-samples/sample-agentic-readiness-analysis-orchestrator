#!/usr/bin/env python3
"""
judge.py — LLM-as-judge for the change-impact harness (DESIGN.md §6).

Consumes the deterministic delta (impact.json from diff-reports.py) plus the
contributor's stated intent (the MR description / --intent) and asks an LLM:
**is this change GOOD FOR THE ANALYSIS?** The verdict is ADVISORY — it is posted as an
MR comment and NEVER fails the pipeline (see .gitlab-ci.yml `allow_failure: true`).

WHAT THE SCORE MEASURES (changed deliberately — see below):
  score = "does this change make the ARA/MOD analysis BETTER or WORSE?"

It used to mean "does the observed delta match the contributor's stated intent?" That
was measurable and well-calibrated, but it answered the wrong question. Intent-match
scores the CONTRIBUTOR, not the analysis: an edit that lands exactly as described but
strips safety signal scored ~92, while an edit that quietly failed to apply scored ~15
even though the analysis was left completely untouched and unharmed. Reviewers read
this number to decide whether merging helps or hurts the assessment, so that is now
what it measures.

Intent is still supplied and still scored, but it has been DEMOTED to evidence:
  * it tells the judge which movement is signal and which is run-to-run noise
    (essential — see _scope_note), and
  * a mismatch means the contributor may not understand what they changed, which is a
    reason to lower CONFIDENCE and raise a concern — not a reason to call an
    analysis-neutral change bad.

`intent_match` and `no_op_warning` therefore still ride in the output; they just no
longer drive the number.

Output (stdout, JSON — schema from DESIGN.md §6):
  {
    "score": 0-100,               # is the ANALYSIS better or worse for this change?
    "analysis_effect": "improves" | "neutral" | "degrades",
    "verdict": "LGTM" | "needs-work",
    "intent_match": "aligned" | "partial" | "mismatch",   # evidence, not the score
    "rationale": "…cites AUTH-Q5, pathway ids, program acronyms…",
    "concerns": [ { "dimension": "D3", "detail": "…" } ],
    "no_op_warning": false
  }

LLM backend: uses Bedrock (Anthropic Claude) via boto3 with the creds already vended
into the job by the AWS Credential Vendor (same creds the atx step uses). If boto3 /
Bedrock is unavailable (e.g. local dev with no creds), falls back to a DETERMINISTIC
heuristic verdict so the pipeline still produces a usable verdict.json offline.

Usage:
  judge.py --impact impact.json --intent "MR description text"
  judge.py --impact impact.json --intent-file intent.md [--model <bedrock-model-id>]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

DEFAULT_MODEL = os.environ.get(
    "HARNESS_JUDGE_MODEL", "anthropic.claude-sonnet-5-20250929-v1:0")
VALID_VERDICTS = {"LGTM", "needs-work"}
VALID_MATCHES = {"aligned", "partial", "mismatch"}
# The primary axis the score now tracks: effect on the ANALYSIS, not on intent-match.
VALID_EFFECTS = {"improves", "neutral", "degrades"}


# ---------------------------------------------------------------------------------------
# Intent parsing — the MR template (§8.1) is structured markdown; pull the fields out.
# ---------------------------------------------------------------------------------------

def parse_intent(raw: str) -> dict:
    """Extract {what, why, expected_impact, edited_in_service} from MR-template text.

    Tolerant of free-form text: if the template headings aren't present, the whole
    blob becomes `what` so the judge still has something to score against.
    """
    intent = {"what": "", "why": "", "expected_impact": "", "edited_in_service": None,
              "raw": raw or ""}
    if not raw:
        return intent

    # Map template headings (§8.1) to fields; match case-insensitively on the prefix.
    headings = [
        ("what are you changing", "what"),
        ("why", "why"),
        ("expected impact", "expected_impact"),
    ]
    current = None
    buf: dict[str, list[str]] = {"what": [], "why": [], "expected_impact": []}
    for line in raw.splitlines():
        stripped = line.strip()
        low = stripped.lower().lstrip("#").strip().rstrip("?").strip()
        matched = None
        for prefix, field in headings:
            if low.startswith(prefix):
                matched = field
                break
        if matched:
            current = matched
            # capture any trailing text on the heading line itself
            rest = stripped.split("?", 1)[-1] if "?" in stripped else ""
            if rest.strip():
                buf[current].append(rest.strip())
            continue
        # "edited in service" checkbox line
        if "rubric edited" in low or "edited in the aws transform service" in low:
            intent["edited_in_service"] = "[x]" in stripped.lower() or "[X]" in stripped
            continue
        if current:
            buf[current].append(line)

    for field in ("what", "why", "expected_impact"):
        intent[field] = "\n".join(buf[field]).strip()
    # If nothing matched the template, treat the whole thing as `what`.
    if not any(intent[f] for f in ("what", "why", "expected_impact")):
        intent["what"] = raw.strip()
    return intent


# ---------------------------------------------------------------------------------------
# Impact summarisation — a compact, judge-friendly digest of the delta.
# ---------------------------------------------------------------------------------------

def summarize_impact(impact: dict) -> dict:
    """Flatten impact.json into a small dict the LLM (and heuristic) can reason over."""
    cov = impact.get("coverage") or {}
    summary: dict[str, Any] = {
        "no_op": impact.get("no_op", True),
        "changed_tds": impact.get("changed_tds", []),
        "dimensions_moved": [],
        "highlights": [],
        # How much of the baseline this delta actually covers. An MR analyzes only the
        # 1-2 fixtures that exercise the edit, so "nothing moved" can mean "nothing moved
        # in the 2 repos we ran" — materially weaker evidence than a full sweep. The judge
        # must not report a scoped clean run with the same confidence as an exhaustive one.
        "coverage": {
            "compared": cov.get("compared"),
            "baseline_total": cov.get("baseline_total"),
            "partial": bool(cov.get("partial")),
            "not_analyzed_count": len(cov.get("not_analyzed") or []),
        },
        # Deterministic, rubric-arithmetic findings from the differ. Carried through
        # VERBATIM and never summarised away: these are the facts the judge is forbidden
        # from attributing to noise, so dropping them here would silently restore the bug
        # they exist to prevent (a relaxed readiness tier waved through as run-to-run
        # variance because the question that caused it was outside the edit scope).
        "safety_alerts": impact.get("safety_alerts") or [],
        "coverage_gaps": impact.get("coverage_gaps") or [],
    }
    moved: set[str] = set()

    for repo, entry in (impact.get("per_repo") or {}).items():
        for key, d in entry.items():
            _note_dimension(key, d, repo, moved, summary["highlights"])
    for analysis, entry in (impact.get("portfolio") or {}).items():
        for key, d in entry.items():
            _note_dimension(key, d, f"portfolio-{analysis}", moved, summary["highlights"])

    summary["dimensions_moved"] = sorted(moved)
    return summary


def _dim_of(key: str) -> Optional[str]:
    # keys look like "D1_ara_findings", "D2_mod_tier", "D3_pathways", "D5_portfolio_score"
    if key.startswith("D") and len(key) > 1 and key[1].isdigit():
        return key[:2]
    return None


def _note_dimension(key: str, d: Any, scope: str, moved: set, highlights: list) -> None:
    dim = _dim_of(key)
    if dim is None or not isinstance(d, dict):
        return
    hit = False
    if dim == "D1":
        added, removed, res = d.get("added") or [], d.get("removed") or [], d.get("reseveritied") or []
        if added or removed or res:
            hit = True
            highlights.append(
                f"[{scope}] D1 findings: +{len(added)} / -{len(removed)} / "
                f"{len(res)} reseveritied"
                + (f" (added: {', '.join(added[:5])})" if added else ""))
            # A RESEVERITY is usually the whole point of a rubric edit (e.g. "reclassify
            # API-Q2 RISK-QUALITY -> RISK-SAFETY"), so it must be named, not just counted.
            # Passing only a count made the judge rule `mismatch` on exactly the change the
            # intent described: it could see "1 reseveritied" but not WHICH question, so it
            # concluded the edited question never moved. The differ already records
            # question_id + before/after severity — surface it.
            for r in res[:8]:
                if not isinstance(r, dict):
                    continue
                sev = r.get("severity") or {}
                nat = r.get("native_severity") or {}
                # native_severity carries the rubric-level class (RISK-SAFETY /
                # RISK-QUALITY / BLOCKER); `severity` is the normalized High/Med/Low.
                # Show whichever actually moved, preferring the native class.
                if nat.get("before") != nat.get("after"):
                    before, after = nat.get("before"), nat.get("after")
                else:
                    before, after = sev.get("before"), sev.get("after")
                highlights.append(
                    f"[{scope}] D1 reseveritied: {r.get('question_id')} "
                    f"{before} -> {after}")
    elif dim == "D2":
        if d.get("changed"):
            hit = True
            if "before" in d and "after" in d:
                highlights.append(f"[{scope}] D2 tier: {d.get('before')} -> {d.get('after')}")
            else:
                highlights.append(f"[{scope}] D2 distribution shifted: {d.get('by_tier')}")
    elif dim == "D3":
        nt, ns = d.get("newly_triggered") or [], d.get("newly_suppressed") or []
        if nt or ns:
            hit = True
            highlights.append(f"[{scope}] D3 pathways: +{nt} / -{ns}")
    elif dim == "D4":
        added, removed = d.get("added") or [], d.get("removed") or []
        if added or removed:
            hit = True
            highlights.append(f"[{scope}] D4 programs: +{added} / -{removed}")
    elif dim == "D5":
        crossed = d.get("band_crossed") or (d.get("overall") or {}).get("band_crossed") \
            or bool(d.get("categories")) or bool(d.get("band_distribution_shift"))
        if crossed:
            hit = True
            highlights.append(f"[{scope}] D5 score band crossing detected")
    if hit:
        moved.add(dim)


# ---------------------------------------------------------------------------------------
# LLM backend (Bedrock) with an offline heuristic fallback.
# ---------------------------------------------------------------------------------------

SYSTEM_PROMPT = """You are reviewing a proposed change to an AWS Transform analysis \
rubric/config for agentic-readiness (ARA) and modernization-readiness (MOD) assessments. \
The change is NOT live yet — the "before" is what the service produces today, the "after" \
is what the proposed change produces.

YOUR PRIMARY QUESTION — the one the score answers:
    Does this change make the ANALYSIS BETTER OR WORSE?

"Better" means the assessment becomes more accurate, more useful, or safer to act on: \
real risks surfaced that were previously missed, severities that better reflect actual \
danger, tiers that better reflect true readiness, clearer or better-targeted \
recommendations. "Worse" means the assessment loses signal, understates risk, answers \
less of the rubric, or would lead a reader to a decision the evidence does not support.

Judge the ANALYSIS, not the contributor. A change can be sloppily described and still \
improve the analysis; it can be described perfectly and still damage it. Score the \
effect on the output.

You are advisory: humans make the final call. Be concrete and cite specifics \
(question_ids like AUTH-Q5, pathway ids, program acronyms like EBA/MAP) from the delta.

Scoring rubric:
- analysis_effect = "improves" : the assessment is now more accurate / safer to act on.
- analysis_effect = "neutral"  : the assessment is materially unchanged in quality —
                              INCLUDING the case where nothing moved at all. A no-op is
                              not a defect in the analysis; it is simply no improvement.
- analysis_effect = "degrades" : the assessment lost signal, understates risk, or covers
                              less of the rubric than before.

- intent_match is SECONDARY EVIDENCE, not the thing being scored. Report it honestly:
  - "aligned"  : the delta does what the intent said it would.
  - "partial"  : the delta partly matches, or moves extra dimensions the intent
                 didn't mention.
  - "mismatch" : the delta contradicts the intent, or moves entirely different
                 dimensions.
  A mismatch means the contributor may not understand what their edit did, so it LOWERS
  CONFIDENCE and MUST become a concern — but it does NOT by itself make the change bad
  for the analysis. Do NOT score a harmless or beneficial change low merely because the
  description was inaccurate, and do NOT score a damaging change high merely because it
  was described accurately.
- no_op_warning = true       : the intent claimed a behavioural change but the delta is
                              empty (nothing moved) — the edit likely never took effect,
                              or the baselines are stale. Raise it as a concern; it is an
                              unmet expectation, NOT damage to the analysis, so it should
                              not by itself sink the score.
- quality_regression = true  : the delta plausibly makes the analysis WORSE — e.g. a tier
                              now contradicts its own blocker/severity counts, a pathway
                              fires when the repo clearly can't trigger it (or stops firing
                              when it should), or a score crosses a band the wrong way.
                              Requires a CAUSAL story linking the EDITED rubric text to the
                              bad output. Do NOT flag this merely because findings outside
                              the edit scope moved — the analysis agent is nondeterministic
                              and that movement is expected noise (see "Edit scope" below,
                              when present).

                              EXCEPT — and this overrides the noise rule entirely — a
                              "SAFETY ALERTS" section, when present, lists movements that
                              were computed DETERMINISTICALLY from the rubric's own
                              arithmetic, not inferred. A lost BLOCKER, a falling
                              blocker_count, or a readiness tier moving toward MORE
                              agent-ready is NEVER noise, EVEN IF the question involved is
                              outside the edit scope: the ARA rubric derives the tier from
                              blocker_count (>=3 -> Not Agent-Integrable, 1-2 ->
                              Remediation Required), so losing a blocker mechanically
                              relaxes the tier. You MUST address every safety alert
                              explicitly in `rationale` or `concerns`, and you MUST NOT
                              describe one as noise or as expected variance. If a safety
                              alert has no innocent causal explanation, set
                              quality_regression = true and do NOT return LGTM — a system
                              being newly judged safer for agent use is the one claim that
                              must never be waved through.
                              A COVERAGE GAPS section means a report stopped answering part
                              of the rubric (ARA has 43 questions, MOD 37). Treat that as a
                              defect, never as noise.
- verdict = "LGTM" when the change is safe for the analysis and not a regression;
            "needs-work" otherwise.

- score 0-100 = HOW MUCH BETTER OR WORSE THE ANALYSIS IS, and how confident you are:
    85-100  clear improvement — real risk surfaced, or severity/tier now better reflects
            reality. Well-evidenced.
    60-84   likely improvement, or a safe change with some uncertainty (e.g. partial
            coverage, or an inaccurate description you had to reason around).
    45-59   genuinely NEUTRAL — the analysis is neither better nor worse. An empty delta
            belongs here by default: nothing was gained, but nothing was harmed. Land
            here for "no effect on quality" rather than reaching for an extreme.
    20-44   likely degradation — signal lost, risk understated, or rubric coverage fell.
    0-19    clear, serious degradation — a system is newly presented as safer than the
            evidence supports.
  A NEUTRAL change is a MID score, not a low one. Reserve the bottom of the range for
  actual damage to the assessment. Note the asymmetry, and honour it: a change that
  makes the analysis harsher/more cautious is far less dangerous than one that makes it
  more permissive, so when uncertain, score a stricter change ABOVE a laxer one.
- suggestions: 0-3 concrete, actionable improvements to the change (empty if none).

Respond with ONLY a JSON object, no prose, matching exactly this schema:
{"score": <int 0-100>, "verdict": "LGTM"|"needs-work",
 "analysis_effect": "improves"|"neutral"|"degrades",
 "intent_match": "aligned"|"partial"|"mismatch",
 "rationale": "<2-4 sentences citing specifics; say plainly whether the ANALYSIS is
               better, unchanged, or worse, and why>",
 "concerns": [{"dimension": "D1".."D5", "detail": "<...>"}],
 "quality_regression": <bool>,
 "suggestions": ["<concrete improvement>", ...],
 "no_op_warning": <bool>}"""


def _coverage_note(impact_summary: dict) -> str:
    """One line telling the judge how much evidence this delta actually rests on."""
    cov = impact_summary.get("coverage") or {}
    if not cov.get("partial"):
        return "coverage: FULL — every baseline report was re-analyzed.\n"
    return (
        f"coverage: PARTIAL — {cov.get('compared')} of {cov.get('baseline_total')} baseline "
        f"reports were re-analyzed ({cov.get('not_analyzed_count')} not analyzed).\n"
        "  The harness deliberately runs only the fixtures that exercise the edited\n"
        "  questions, so an empty delta here means 'nothing moved in what we ran' — it is\n"
        "  NOT proof the change is inert portfolio-wide. Temper confidence accordingly and\n"
        "  say so in the rationale; suggest a full sweep (harness:full) if the edit looks\n"
        "  broader than the fixtures covered.\n"
    )


def _scope_note(edited_questions: list[str]) -> str:
    """Tell the judge which questions the MR actually edited, and that the rest is noise.

    WHY THIS IS ESSENTIAL: the underlying analysis agent is NONDETERMINISTIC. Two runs of
    the byte-identical rubric on the same fixture differ by ~10-20 findings (measured
    across two golden refreshes of an unedited rubric). So a delta is always
    `signal + run-to-run noise`, and for a one-question edit the noise DWARFS the signal.

    Without this note the judge sees "+13 findings" next to an intent about one question
    and correctly-but-uselessly concludes `mismatch: the change is far broader than
    stated`. Naming the edited questions lets it weigh movement IN scope as evidence and
    movement OUT of scope as suspected noise — which is the only way a verdict on a
    narrow edit can mean anything.
    """
    if not edited_questions:
        return ""
    return (
        "\n## Edit scope (from the rubric diff — authoritative)\n"
        f"questions actually edited: {', '.join(edited_questions)}\n"
        "IMPORTANT — how to weigh the delta against this scope:\n"
        "  * The analysis agent is NONDETERMINISTIC. Re-running the SAME rubric on the same\n"
        "    fixture moves roughly 10-20 findings purely from run-to-run variance.\n"
        "  * Therefore ORDINARY FINDINGS CHURN on questions OUTSIDE the edited set is\n"
        "    EXPECTED NOISE. Do NOT treat it as a regression or as evidence the change is\n"
        "    broader than stated, and do NOT ground a `mismatch` verdict in it. Mention it\n"
        "    at most as an aside.\n"
        "  * BUT THIS NOISE RULE HAS HARD LIMITS. It covers findings appearing/disappearing\n"
        "    and severity moving among the non-blocking classes. It does NOT cover:\n"
        "      - a BLOCKER being downgraded or lost,\n"
        "      - blocker_count falling,\n"
        "      - the readiness tier moving toward MORE agent-ready,\n"
        "      - a report answering fewer rubric questions than the baseline.\n"
        "    Those are SAFETY-MATERIAL and stay in scope no matter which question caused\n"
        "    them — being out of edit scope is NOT a reason to dismiss one. Any such\n"
        "    movement is listed under \"SAFETY ALERTS\" / \"COVERAGE GAPS\" below, computed\n"
        "    deterministically from the rubric, and you must address each one.\n"
        "  * Judge intent-match PRIMARILY on whether the EDITED questions moved as the\n"
        "    intent describes (a severity reclassification shows up as a `reseveritied`\n"
        "    entry naming that question, not as an added/removed finding).\n"
        "  * A reclassification changes a finding's SEVERITY CLASS, so the finding count\n"
        "    barely moves. Do not expect added/removed findings from one.\n"
    )


def _alerts_note(impact_summary: dict) -> str:
    """Render the deterministic safety alerts / coverage gaps as must-address facts.

    Placed IMMEDIATELY BEFORE the delta highlights and worded as an obligation, because the
    failure mode this fixes was the judge reading a real tier regression as noise: it had
    the tier change in its highlights but no signal that the change was rubric-mechanical
    rather than incidental. Being explicit that these are computed, not inferred, is what
    stops the edit-scope noise rule from swallowing them.
    """
    alerts = impact_summary.get("safety_alerts") or []
    gaps = impact_summary.get("coverage_gaps") or []
    if not alerts and not gaps:
        return ""
    out = ["\n## SAFETY ALERTS — deterministic, NOT noise, MUST be addressed"]
    if alerts:
        out.append(
            "Computed from the rubric's own arithmetic by the differ, not inferred by a\n"
            "model. Each of these is safety-material REGARDLESS of whether the question\n"
            "involved was in the edit scope. Address every one in rationale or concerns;\n"
            "never call one noise. If any lacks an innocent causal explanation, set\n"
            "quality_regression = true and do not return LGTM.")
        for a in alerts[:12]:
            if isinstance(a, dict):
                # Mark which alerts actually move the tier. Without this the judge cannot
                # tell a veto-worthy blocker loss from a RISK-SAFETY drift that is real but
                # tier-inert while blockers remain, and would either over- or under-react.
                mark = "TIER-MATERIAL" if a.get("tier_material", True) else "notable"
                out.append(f"  ! [{a.get('kind')}] ({mark}) {a.get('detail')}")
    if gaps:
        out.append(
            "COVERAGE GAPS — a report answered fewer rubric questions than its baseline\n"
            "(ARA defines 43, MOD 37). This is a rubric/analysis defect, not variance:")
        for g in gaps[:12]:
            if isinstance(g, dict):
                out.append(f"  ! {g.get('detail')}")
    return "\n".join(out) + "\n"


def build_user_prompt(intent: dict, impact_summary: dict, diff_text: str,
                      edited_questions: Optional[list[str]] = None) -> str:
    return (
        "## Contributor intent\n"
        f"What: {intent.get('what') or '(none stated)'}\n"
        f"Why: {intent.get('why') or '(none stated)'}\n"
        f"Expected impact: {intent.get('expected_impact') or '(none stated)'}\n"
        f"Rubric edited directly in the AWS Transform service: {intent.get('edited_in_service')}\n"
        + _scope_note(edited_questions or [])
        + "\n## Observed delta (from the deterministic differ)\n"
        f"no_op: {impact_summary['no_op']}\n"
        f"changed_tds: {impact_summary['changed_tds']}\n"
        f"dimensions_moved: {impact_summary['dimensions_moved']}\n"
        + _coverage_note(impact_summary)
        + _alerts_note(impact_summary)
        + "highlights:\n" + ("\n".join(f"  - {h}" for h in impact_summary['highlights']) or "  (none)")
        + "\n\n## Raw change diff (may be truncated)\n"
        + (diff_text[:4000] if diff_text else "(not provided)")
        + "\n\nReturn the JSON verdict now."
    )


def judge_with_bedrock(intent: dict, impact_summary: dict, diff_text: str,
                       model: str,
                       edited_questions: Optional[list[str]] = None) -> Optional[dict]:
    """Call Bedrock; return a parsed verdict dict, or None if unavailable/failed."""
    try:
        import boto3  # noqa: PLC0415
    except ImportError:
        return None
    try:
        region = os.environ.get("AWS_REGION", "us-east-1")
        client = boto3.client("bedrock-runtime", region_name=region)
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user",
                          "content": build_user_prompt(intent, impact_summary, diff_text,
                                                       edited_questions)}],
        }
        resp = client.invoke_model(modelId=model, body=json.dumps(body))
        payload = json.loads(resp["body"].read())
        text = "".join(blk.get("text", "") for blk in payload.get("content", []))
        return _coerce_verdict(_extract_json(text))
    except Exception as exc:  # noqa: BLE001 — advisory tool must never hard-fail
        print(f"judge: Bedrock call failed ({exc}); falling back to heuristic", file=sys.stderr)
        return None


def _extract_json(text: str) -> dict:
    """Pull the first {...} JSON object out of an LLM response."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object in LLM response")
    return json.loads(text[start:end + 1])


# ---------------------------------------------------------------------------------------
# Deterministic heuristic fallback (no LLM). Keeps the pipeline useful offline.
# ---------------------------------------------------------------------------------------

def judge_heuristic(intent: dict, impact_summary: dict) -> dict:
    no_op = impact_summary["no_op"]
    moved = impact_summary["dimensions_moved"]
    intent_claims_change = bool(
        (intent.get("what") or intent.get("expected_impact") or "").strip())

    concerns: list[dict] = []
    no_op_warning = no_op and intent_claims_change

    # An empty delta is NEUTRAL for the analysis in BOTH branches below — nothing was
    # gained and nothing was harmed. What differs is only how much we trust the
    # contributor's description, which is a confidence signal, not damage. Under the old
    # intent-match semantics the two branches scored 25 vs 80; now they sit close together
    # and mid-range, because the analysis is in exactly the same state either way.
    if no_op:
        effect = "neutral"
        if no_op_warning:
            verdict, match, score = "needs-work", "mismatch", 50
            concerns.append({"dimension": "-",
                             "detail": "Intent describes a change but the delta is empty (no-op) "
                                       "— the edit likely never took effect. The analysis is "
                                       "unharmed, but the change also achieves nothing."})
            rationale = ("The analysis is UNCHANGED — no movement across D1–D5 — so this "
                         "neither improves nor degrades the assessment. But the intent "
                         "describes a behavioural change, so the edit probably didn't land: "
                         "either it was made in-service and the golden baselines need "
                         "refreshing (fire harness:full), or it has no effect at all. "
                         "needs-work reflects the unmet expectation, not damage.")
        else:
            verdict, match, score = "LGTM", "aligned", 55
            rationale = ("No analysis output moved and the intent did not claim one would — "
                         "consistent with a docs/metadata-only change. Neutral for the "
                         "analysis: nothing gained, nothing harmed.")
            # A clean result over 2 of 26 reports is weaker evidence than a full sweep,
            # so trim confidence — but stay in the neutral band, since partial coverage
            # is missing evidence about the analysis, not evidence of harm to it.
            cov = impact_summary.get("coverage") or {}
            if cov.get("partial"):
                score = 48
                rationale += (
                    f" NOTE: only {cov.get('compared')} of {cov.get('baseline_total')} baseline "
                    "reports were re-analyzed (the MR path runs just the fixtures that exercise "
                    "the edit), so this is not proof the change is inert portfolio-wide.")
    else:
        # Something moved. Offline we cannot assess whether the analysis got BETTER or WORSE
        # — that judgement is exactly what needs a model. So report the movement, claim
        # nothing about direction, and sit in the neutral band. The deterministic safety
        # floor below still catches the one case that must never pass quietly.
        effect, verdict, match, score = "neutral", "LGTM", "partial", 55
        rationale = (f"Delta moved dimensions {moved} across {impact_summary['changed_tds']}. "
                     "Heuristic (offline) mode CANNOT judge whether the analysis improved or "
                     "degraded — that needs the LLM judge — so this score is a neutral "
                     "placeholder, not a positive assessment. A human should confirm the "
                     "moved dimensions make the assessment better. "
                     "Highlights: " + "; ".join(impact_summary["highlights"][:4]))
        for h in impact_summary["highlights"][:6]:
            dim = h.split("]", 1)[-1].strip().split(" ", 1)[0] if "]" in h else "-"
            concerns.append({"dimension": dim, "detail": h})

    return {
        "score": score,
        "verdict": verdict,
        "analysis_effect": effect,
        "intent_match": match,
        "rationale": rationale,
        "concerns": concerns,
        # Offline heuristic can't judge correctness — leave regression unflagged and say so.
        "quality_regression": False,
        "suggestions": ["Run with the LLM judge (Bedrock creds) for a quality-regression "
                        "read and improvement suggestions — offline heuristic can't assess "
                        "correctness."] if not no_op else [],
        "no_op_warning": no_op_warning,
        "_engine": "heuristic",
    }


# ---------------------------------------------------------------------------------------
# Verdict coercion / validation — never emit an off-schema verdict.
# ---------------------------------------------------------------------------------------

def _append_alert_concerns(verdict: dict, alerts: list, gaps: list) -> list:
    """Add each alert/gap to the verdict concerns, deduped by detail (so it is idempotent).

    Split out because a NON-tier-material alert must still reach the reader as a concern
    even though it does not force a hold — reporting it and vetoing on it are two decisions,
    not one.
    """
    concerns = [c for c in (verdict.get("concerns") or []) if isinstance(c, dict)]
    existing = {str(c.get("detail") or "") for c in concerns}
    for a in alerts:
        detail = f"SAFETY ALERT [{a.get('kind')}] {a.get('detail')}"
        if detail not in existing:
            concerns.append({"dimension": "D2", "detail": detail})
            existing.add(detail)
    for g in gaps:
        detail = f"COVERAGE GAP {g.get('detail')}"
        if detail not in existing:
            concerns.append({"dimension": "D1", "detail": detail})
            existing.add(detail)
    return concerns


def _enforce_safety_floor(verdict: dict, impact_summary: dict) -> dict:
    """Prevent an LGTM from surviving an unexplained safety alert or coverage gap.

    Deliberately blunt, and deliberately NOT trying to decide whether the alert is innocent
    — that judgement needs a human. What it guarantees is that the alert is impossible to
    miss: verdict downgraded, quality_regression set, score capped, and every alert present
    as its own concern. Idempotent, so calling it twice cannot double-append.
    """
    alerts = [a for a in (impact_summary.get("safety_alerts") or []) if isinstance(a, dict)]
    gaps = [g for g in (impact_summary.get("coverage_gaps") or []) if isinstance(g, dict)]
    if not alerts and not gaps:
        return verdict

    # Only TIER-MATERIAL alerts force the hold. A RISK-SAFETY downgrade while
    # blocker_count is still above 0 does not move the tier, and that count drifts on every
    # nondeterministic rerun — holding on it would fire on nearly every MR, and a gate that
    # always fires is a gate nobody reads. Non-material alerts are still reported below, and
    # the judge is still asked to explain them; they just do not veto on their own.
    # Alerts predating this field have no `tier_material` key — default them to holding,
    # so a missing field can only ever be over-cautious.
    holding = [a for a in alerts if a.get("tier_material", True)]
    if not holding and not gaps:
        verdict["concerns"] = _append_alert_concerns(verdict, alerts, gaps)
        return verdict

    verdict["concerns"] = _append_alert_concerns(verdict, alerts, gaps)
    verdict["quality_regression"] = True
    verdict["verdict"] = "needs-work"
    # A tier-material alert IS a degradation of the analysis by definition: a system is now
    # presented as safer than it was, from the rubric's own arithmetic. Under the new
    # score semantics that has to be stated on the primary axis, not just in the verdict —
    # otherwise the comment could read "degrades the analysis" nowhere while holding.
    verdict["analysis_effect"] = "degrades"
    # Cap rather than zero: the judge's own score still carries information about the rest
    # of the change, which stays useful once a human clears the alert.
    verdict["score"] = min(int(verdict.get("score", 50) or 0), 40)
    # A machine-readable marker so the MR comment and any downstream tooling can tell a
    # human-reviewable safety hold apart from an ordinary needs-work verdict.
    verdict["safety_hold"] = True
    return verdict


def _coerce_verdict(v: dict) -> dict:
    out = {
        "score": int(max(0, min(100, v.get("score", 50)))),
        "verdict": v.get("verdict") if v.get("verdict") in VALID_VERDICTS else "needs-work",
        "intent_match": v.get("intent_match") if v.get("intent_match") in VALID_MATCHES else "partial",
        # The primary axis. Defaults to "neutral", NOT "degrades": an absent field means the
        # model did not claim harm, and inventing a degradation would trip the safety
        # framing on well-behaved changes.
        "analysis_effect": (v.get("analysis_effect")
                            if v.get("analysis_effect") in VALID_EFFECTS else "neutral"),
        "rationale": str(v.get("rationale") or "").strip() or "(no rationale)",
        "concerns": [c for c in (v.get("concerns") or []) if isinstance(c, dict)],
        "quality_regression": bool(v.get("quality_regression", False)),
        "suggestions": [str(s).strip() for s in (v.get("suggestions") or []) if str(s).strip()][:3],
        "no_op_warning": bool(v.get("no_op_warning", False)),
    }
    return out


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Intent-aware LLM-as-judge -> verdict.json")
    ap.add_argument("--impact", required=True, type=Path, help="impact.json from diff-reports.py")
    ap.add_argument("--intent", default="", help="Contributor intent (MR description text)")
    ap.add_argument("--intent-file", type=Path, default=None,
                    help="Read intent from a file instead of --intent")
    ap.add_argument("--diff-file", type=Path, default=None,
                    help="Optional raw diff of the changed file(s) for extra judge context")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Bedrock model id")
    ap.add_argument("--no-llm", action="store_true", help="Force the offline heuristic")
    # The questions the MR actually edited (comma-separated, e.g. "API-Q2"). run-fixtures.sh
    # already extracts these via select-fixtures.py, so pass them through: they let the judge
    # separate in-scope movement (signal) from the analysis agent's run-to-run
    # nondeterminism (noise), which for a one-question edit is the larger of the two.
    ap.add_argument("--edited-questions", default="",
                    help="comma-separated question ids the change edited (scope signal)")
    args = ap.parse_args(argv)

    try:
        impact = json.loads(args.impact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read impact.json: {exc}", file=sys.stderr)
        return 2

    raw_intent = args.intent
    if args.intent_file and args.intent_file.exists():
        raw_intent = args.intent_file.read_text(encoding="utf-8")
    intent = parse_intent(raw_intent)

    diff_text = ""
    if args.diff_file and args.diff_file.exists():
        diff_text = args.diff_file.read_text(encoding="utf-8", errors="replace")

    impact_summary = summarize_impact(impact)
    edited_questions = [q.strip().upper() for q in args.edited_questions.split(",")
                        if q.strip()]
    if edited_questions:
        impact_summary["edited_questions"] = edited_questions

    verdict = None
    if not args.no_llm:
        verdict = judge_with_bedrock(intent, impact_summary, diff_text, args.model,
                                     edited_questions)
        if verdict is not None:
            verdict["_engine"] = "bedrock"
    if verdict is None:
        verdict = judge_heuristic(intent, impact_summary)

    # HARD BACKSTOP — enforced in code, after whichever engine produced the verdict.
    #
    # The prompt tells the judge that a lost BLOCKER / relaxed tier is never noise, but a
    # prompt is a request, not a guarantee: the LLM already dismissed exactly this movement
    # as "likely noise" once and still returned LGTM/72. The heuristic fallback does not
    # reason about it at all. So the floor lives here, where nothing can talk it down.
    #
    # We do NOT overwrite the rationale or invent a causal story — we downgrade the verdict
    # and surface each alert as a concern, leaving the model's own reasoning intact so a
    # reviewer can see the disagreement. A safety alert is exactly the case where the
    # harness should fail loud rather than defer.
    verdict = _enforce_safety_floor(verdict, impact_summary)

    # Attach the digest so the MR comment / artifact is self-contained.
    verdict["_impact_summary"] = impact_summary
    print(json.dumps(verdict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
