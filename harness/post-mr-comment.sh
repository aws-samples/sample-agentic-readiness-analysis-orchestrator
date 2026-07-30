#!/usr/bin/env bash
#
# post-mr-comment.sh — post the judge's verdict.json as an ADVISORY GitLab MR note.
#
# This never blocks the pipeline (the calling job is allow_failure: true, and this
# script exits 0 even when it can't post). It renders verdict.json into a compact
# markdown comment and PUTs it to the MR via the GitLab API. Outside an MR context
# (e.g. the web-triggered harness:full job), it fails softly so the caller can fall
# back to `cat verdict.json`. See DESIGN.md §6.
#
# Auth: uses CI_JOB_TOKEN against $CI_API_V4_URL (both injected by GitLab CI). If a
# richer token is needed for notes, set HARNESS_MR_TOKEN and it takes precedence.
#
# Usage:
#   post-mr-comment.sh verdict.json
#
set -euo pipefail

VERDICT="${1:-verdict.json}"

if [[ ! -f "${VERDICT}" ]]; then
  echo "post-mr-comment: no verdict file at ${VERDICT}" >&2
  exit 1
fi

# --- render verdict.json -> markdown -------------------------------------------------
# Pure-python render so we don't depend on jq being present in the slim image.
BODY="$(python3 - "${VERDICT}" <<'PY'
import json, sys
v = json.load(open(sys.argv[1]))
score = v.get("score", "?")
verdict = v.get("verdict", "?")
match = v.get("intent_match", "?")
emoji = {"LGTM": "✅", "needs-work": "⚠️"}.get(verdict, "❓")
match_emoji = {"aligned": "🟢", "partial": "🟡", "mismatch": "🔴"}.get(match, "⚪")
engine = v.get("_engine", "?")

lines = []
lines.append(f"### {emoji} Change-Impact Harness — advisory verdict")
lines.append("")
lines.append(f"**Verdict:** {verdict} &nbsp;|&nbsp; **Score:** {score}/100 "
             f"&nbsp;|&nbsp; **Intent match:** {match_emoji} {match}")
if v.get("quality_regression"):
    lines.append("")
    lines.append("> 🔴 **Possible quality regression:** the judge thinks this change may make "
                 "the analysis worse. See rationale/concerns below and confirm before merging.")
if v.get("no_op_warning"):
    lines.append("")
    lines.append("> ⛔ **No-op warning:** the intent describes a change but the delta is "
                 "empty. If the rubric was edited in the AWS Transform service, refresh the "
                 "golden baselines (`harness:full`).")
lines.append("")
lines.append(v.get("rationale", "").strip() or "_(no rationale)_")

summ = v.get("_impact_summary") or {}

# Scope of the run. An MR analyzes only the fixtures that exercise the edited questions,
# so state that plainly — a reviewer must not read "no impact" over 2 of 26 reports as
# "no impact portfolio-wide". Silence here would be the misleading option.
cov = summ.get("coverage") or {}
if cov.get("partial"):
    lines.append("")
    lines.append(f"> 🔍 **Scoped run:** {cov.get('compared')} of {cov.get('baseline_total')} "
                 f"baseline reports re-analyzed ({cov.get('not_analyzed_count')} not analyzed). "
                 "The harness runs only the fixtures that exercise the edited questions, so an "
                 "empty delta is not proof the change is inert portfolio-wide — run "
                 "`harness:full` for the exhaustive sweep.")
elif cov.get("compared"):
    lines.append("")
    lines.append(f"> ✅ **Full sweep:** all {cov.get('compared')} baseline reports re-analyzed.")

moved = summ.get("dimensions_moved") or []
if moved:
    lines.append("")
    lines.append(f"**Dimensions moved:** {', '.join(moved)} "
                 f"across `{', '.join(summ.get('changed_tds') or []) or '—'}`")
highlights = summ.get("highlights") or []
if highlights:
    lines.append("")
    lines.append("<details><summary>Delta highlights</summary>")
    lines.append("")
    for h in highlights[:20]:
        lines.append(f"- {h}")
    lines.append("")
    lines.append("</details>")

concerns = v.get("concerns") or []
if concerns:
    lines.append("")
    lines.append("**Concerns:**")
    for c in concerns[:10]:
        lines.append(f"- `{c.get('dimension','-')}` — {c.get('detail','')}")

suggestions = v.get("suggestions") or []
if suggestions:
    lines.append("")
    lines.append("**Suggested improvements:**")
    for s in suggestions[:3]:
        lines.append(f"- {s}")

lines.append("")
lines.append(f"<sub>advisory only — never blocks the merge · judge engine: {engine}</sub>")
print("\n".join(lines))
PY
)"

# --- locate the MR + API -------------------------------------------------------------
PROJECT_ID="${CI_PROJECT_ID:-}"
MR_IID="${CI_MERGE_REQUEST_IID:-}"
API="${CI_API_V4_URL:-}"
TOKEN="${HARNESS_MR_TOKEN:-${CI_JOB_TOKEN:-}}"

if [[ -z "${PROJECT_ID}" || -z "${MR_IID}" || -z "${API}" ]]; then
  echo "post-mr-comment: not in an MR pipeline (no CI_MERGE_REQUEST_IID) — printing instead:" >&2
  echo "" >&2
  printf '%s\n' "${BODY}" >&2
  exit 1   # caller (harness:full) falls back to `cat verdict.json`
fi

if [[ -z "${TOKEN}" ]]; then
  echo "post-mr-comment: no CI_JOB_TOKEN/HARNESS_MR_TOKEN available — cannot post." >&2
  printf '%s\n' "${BODY}" >&2
  exit 0   # advisory: don't fail the job over a missing note token
fi

# --- post the note -------------------------------------------------------------------
URL="${API}/projects/${PROJECT_ID}/merge_requests/${MR_IID}/notes"
echo "post-mr-comment: POST ${URL}" >&2

# Send the body as a form field; curl handles the URL-encoding via --data-urlencode.
http_code="$(curl -sS -o /tmp/mr-note-resp.json -w '%{http_code}' \
  --request POST "${URL}" \
  --header "JOB-TOKEN: ${TOKEN}" \
  --header "PRIVATE-TOKEN: ${TOKEN}" \
  --data-urlencode "body=${BODY}" || echo "000")"

if [[ "${http_code}" =~ ^2 ]]; then
  echo "post-mr-comment: posted (HTTP ${http_code})." >&2
else
  echo "post-mr-comment: could not post note (HTTP ${http_code}); verdict follows:" >&2
  cat /tmp/mr-note-resp.json >&2 || true
  echo "" >&2
  printf '%s\n' "${BODY}" >&2
fi

# Advisory tool — always succeed so the pipeline stays green.
exit 0
