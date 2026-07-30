#!/usr/bin/env python3
"""
judge.py — intent-aware LLM-as-judge for the change-impact harness (DESIGN.md §6).

Consumes the deterministic delta (impact.json from diff-reports.py) plus the
contributor's STATED INTENT (the MR description / --intent) and asks an LLM to score
the delta *against that intent*. The verdict is ADVISORY — it is posted as an MR
comment and NEVER fails the pipeline (see .gitlab-ci.yml `allow_failure: true`).

Why intent matters (user's explicit requirement): a delta of "+40 findings" is GOOD
if the intent was "tighten AUTH scoring" and BAD if the intent was "fix a typo in a
recommendation string." The judge scores the observed delta relative to what the
contributor said they were trying to do — not against raw baseline.

Output (stdout, JSON — schema from DESIGN.md §6):
  {
    "score": 0-100,
    "verdict": "LGTM" | "needs-work",
    "intent_match": "aligned" | "partial" | "mismatch",
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
is what the proposed change produces. Your job has two parts:
1. Does the OBSERVED DELTA match the contributor's STATED INTENT?
2. Is the change a QUALITY REGRESSION, or does it make sense — and can it be improved?

You are advisory: humans make the final call. Be concrete and cite specifics \
(question_ids like AUTH-Q5, pathway ids, program acronyms like EBA/MAP) from the delta.

Scoring rubric:
- intent_match = "aligned"  : the delta does what the intent said it would.
- intent_match = "partial"  : the delta partly matches, or moves extra dimensions the
                              intent didn't mention.
- intent_match = "mismatch" : the delta contradicts the intent, or moves entirely
                              different dimensions.
- no_op_warning = true       : the intent claimed a behavioural change but the delta is
                              empty (nothing moved). This is almost always a problem.
- quality_regression = true  : the delta plausibly makes the analysis WORSE — e.g. a tier
                              now contradicts its own blocker/severity counts, a pathway
                              fires when the repo clearly can't trigger it (or stops firing
                              when it should), or a score crosses a band the wrong way.
                              Requires a CAUSAL story linking the EDITED rubric text to the
                              bad output. Do NOT flag this merely because findings outside
                              the edit scope moved — the analysis agent is nondeterministic
                              and that movement is expected noise (see "Edit scope" below,
                              when present).
- verdict = "LGTM" when the change is safe, intent-aligned, and not a regression;
            "needs-work" otherwise.
- score 0-100: higher = more confident the change is good, matches intent, and is not a
            regression.
- suggestions: 0-3 concrete, actionable improvements to the change (empty if none).

Respond with ONLY a JSON object, no prose, matching exactly this schema:
{"score": <int 0-100>, "verdict": "LGTM"|"needs-work",
 "intent_match": "aligned"|"partial"|"mismatch",
 "rationale": "<2-4 sentences citing specifics>",
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
        "  * Therefore movement on questions OUTSIDE the edited set is EXPECTED NOISE. Do\n"
        "    NOT treat it as a regression or as evidence the change is broader than stated,\n"
        "    and do NOT ground a `mismatch` verdict in it. Mention it at most as an aside.\n"
        "  * Judge intent-match PRIMARILY on whether the EDITED questions moved as the\n"
        "    intent describes (a severity reclassification shows up as a `reseveritied`\n"
        "    entry naming that question, not as an added/removed finding).\n"
        "  * A reclassification changes a finding's SEVERITY CLASS, so the finding count\n"
        "    barely moves. Do not expect added/removed findings from one.\n"
    )


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

    if no_op:
        if no_op_warning:
            verdict, match, score = "needs-work", "mismatch", 25
            concerns.append({"dimension": "-",
                             "detail": "Intent describes a change but the delta is empty (no-op)."})
            rationale = ("The contributor's intent describes a behavioural change, but the "
                         "deterministic differ found NO movement across D1–D5. Either the "
                         "rubric edit didn't land, or it was made in-service and the golden "
                         "baselines need refreshing (fire harness:full).")
        else:
            verdict, match, score = "LGTM", "aligned", 80
            rationale = ("No analysis output moved and the intent did not claim one would — "
                         "consistent with a docs/metadata-only change.")
            # A clean result over 2 of 26 reports is weaker evidence than a full sweep.
            # Don't hand out an unqualified 80 for a scoped run.
            cov = impact_summary.get("coverage") or {}
            if cov.get("partial"):
                score = 70
                rationale += (
                    f" NOTE: only {cov.get('compared')} of {cov.get('baseline_total')} baseline "
                    "reports were re-analyzed (the MR path runs just the fixtures that exercise "
                    "the edit), so this is not proof the change is inert portfolio-wide.")
    else:
        # Something moved. Without an LLM we can't verify it matches intent word-for-word,
        # so we report the movement and lean neutral-positive, flagging for human review.
        verdict, match, score = "LGTM", "partial", 65
        rationale = (f"Delta moved dimensions {moved} across {impact_summary['changed_tds']}. "
                     "Heuristic (offline) mode cannot confirm alignment with the stated intent — "
                     "a human should confirm the moved dimensions match what was intended. "
                     "Highlights: " + "; ".join(impact_summary["highlights"][:4]))
        for h in impact_summary["highlights"][:6]:
            dim = h.split("]", 1)[-1].strip().split(" ", 1)[0] if "]" in h else "-"
            concerns.append({"dimension": dim, "detail": h})

    return {
        "score": score,
        "verdict": verdict,
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

def _coerce_verdict(v: dict) -> dict:
    out = {
        "score": int(max(0, min(100, v.get("score", 50)))),
        "verdict": v.get("verdict") if v.get("verdict") in VALID_VERDICTS else "needs-work",
        "intent_match": v.get("intent_match") if v.get("intent_match") in VALID_MATCHES else "partial",
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

    # Attach the digest so the MR comment / artifact is self-contained.
    verdict["_impact_summary"] = impact_summary
    print(json.dumps(verdict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
