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
    summary: dict[str, Any] = {
        "no_op": impact.get("no_op", True),
        "changed_tds": impact.get("changed_tds", []),
        "dimensions_moved": [],
        "highlights": [],
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
rubric/config for a modernization-readiness assessment. Your job is to judge whether \
the OBSERVED DELTA in analysis output matches the contributor's STATED INTENT.

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
- verdict = "LGTM" when the change is safe and intent-aligned; "needs-work" otherwise.
- score 0-100: higher = more confident the change is good AND matches intent.

Respond with ONLY a JSON object, no prose, matching exactly this schema:
{"score": <int 0-100>, "verdict": "LGTM"|"needs-work",
 "intent_match": "aligned"|"partial"|"mismatch",
 "rationale": "<2-4 sentences citing specifics>",
 "concerns": [{"dimension": "D1".."D5", "detail": "<...>"}],
 "no_op_warning": <bool>}"""


def build_user_prompt(intent: dict, impact_summary: dict, diff_text: str) -> str:
    return (
        "## Contributor intent\n"
        f"What: {intent.get('what') or '(none stated)'}\n"
        f"Why: {intent.get('why') or '(none stated)'}\n"
        f"Expected impact: {intent.get('expected_impact') or '(none stated)'}\n"
        f"Rubric edited directly in the AWS Transform service: {intent.get('edited_in_service')}\n\n"
        "## Observed delta (from the deterministic differ)\n"
        f"no_op: {impact_summary['no_op']}\n"
        f"changed_tds: {impact_summary['changed_tds']}\n"
        f"dimensions_moved: {impact_summary['dimensions_moved']}\n"
        "highlights:\n" + ("\n".join(f"  - {h}" for h in impact_summary['highlights']) or "  (none)")
        + "\n\n## Raw change diff (may be truncated)\n"
        + (diff_text[:4000] if diff_text else "(not provided)")
        + "\n\nReturn the JSON verdict now."
    )


def judge_with_bedrock(intent: dict, impact_summary: dict, diff_text: str,
                       model: str) -> Optional[dict]:
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
                          "content": build_user_prompt(intent, impact_summary, diff_text)}],
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

    verdict = None
    if not args.no_llm:
        verdict = judge_with_bedrock(intent, impact_summary, diff_text, args.model)
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
