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
# Auth: REQUIRES HARNESS_MR_TOKEN — a Project Access Token with `api` scope (Reporter is
# enough), set as a project CI variable. Masked is fine; Protected is NOT (a protected
# variable is only injected on protected branches, so MRs from feature branches would
# silently get no comment).
#
# CI_JOB_TOKEN is NOT a usable fallback here even though CI injects it: GitLab limits it
# to a fixed API allowlist (jobs, artifacts, registry, packages) which excludes the notes
# endpoint, so it returns 401 regardless of project permissions. We still try it as a last
# resort, but the script warns first so the 401 isn't mistaken for a misconfigured PAT.
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
score = v.get("score")
baseline_score = v.get("baseline_score")
scored = bool(v.get("scored"))
verdict = v.get("verdict", "?")
match = v.get("intent_match", "?")
effect = v.get("analysis_effect", "?")
emoji = {"LGTM": "✅", "needs-work": "⚠️"}.get(verdict, "❓")
match_emoji = {"aligned": "🟢", "partial": "🟡", "mismatch": "🔴"}.get(match, "⚪")
# The score measures EFFECT ON THE ANALYSIS, so that axis leads and intent-match trails.
effect_emoji = {"improves": "📈", "neutral": "➖", "degrades": "📉"}.get(effect, "❓")
effect_label = {"improves": "improves the analysis",
                "neutral": "neutral for the analysis",
                "degrades": "DEGRADES the analysis"}.get(effect, effect)
engine = v.get("_engine", "?")

lines = []
lines.append(f"### {emoji} Change-Impact Harness — advisory verdict")
lines.append("")

# The score is the regenerated report ACCURACY on the same 0.0-1.0 scale as the committed
# baseline, produced by the same scorer. It is a MEASUREMENT, so it is rendered next to the
# baseline it is compared against -- a bare number with no anchor invites the reader to grade
# it out of 100, which is exactly the confusion the single scale exists to remove.
if scored and isinstance(score, (int, float)) and isinstance(baseline_score, (int, float)):
    delta = score - baseline_score
    score_cell = (f"**Accuracy:** {score:.3f} vs baseline {baseline_score:.3f} "
                  f"({delta:+.3f})")
elif scored and isinstance(score, (int, float)):
    score_cell = f"**Accuracy:** {score:.3f} (no baseline)"
else:
    score_cell = "**Accuracy:** not measured"
lines.append(f"**Verdict:** {verdict} &nbsp;|&nbsp; {score_cell} "
             f"&nbsp;|&nbsp; **Effect:** {effect_emoji} {effect_label}")
lines.append("")
if scored:
    # Spell out what the number is and, just as importantly, what it is not: it grades the
    # REPORT against the fixture source, not the merge request.
    lines.append(f"<sub>Accuracy = how well the regenerated report is grounded in the fixture "
                 f"source (misses and fabrications count against it), scored 0.000-1.000 by "
                 f"the same scorer that produced the committed baseline. The **Effect** is the "
                 f"judgement: whether the measured move is an improvement, a regression, or "
                 f"inside the per-fixture noise band. Intent match: {match_emoji} {match} — "
                 f"supporting evidence only, it does not drive the measurement.</sub>")
else:
    # No measurement means no validation. Say that plainly rather than letting a reader read
    # a missing number as a neutral one.
    lines.append("<sub>⚠️ The regenerated report was **not scored**, so there is no accuracy "
                 "number and no baseline comparison: **this change could not be validated.** "
                 "The scoring step (`score-reports.py --compare-out`) needs to be fixed and "
                 "re-run. Treat this as a harness error, not a pass.</sub>")
# A safety hold outranks the generic regression note and replaces it. This is not a
# judgement call but deterministic rubric arithmetic (lost BLOCKER, relaxed readiness
# tier, dropped rubric questions), so it is stated as fact and placed first.
#
# NOTE: no apostrophes anywhere in this heredoc, including in comments. It sits inside a
# $(...) command substitution, and bash 3.2 (the macOS default, where the test suite runs)
# re-parses the substitution body and treats a single quote character as opening a quoted
# string -- yielding "unexpected EOF while looking for matching )" and a script that will
# not run at all. Prefer plural or possessive-free phrasing here.
if v.get("safety_hold"):
    lines.append("")
    lines.append("> 🚨 **SAFETY HOLD — needs a human decision.** The differ found a change that "
                 "makes a system look *safer for agent use* than before: a lost BLOCKER, a "
                 "relaxed readiness tier, or a report answering fewer rubric questions. This "
                 "is computed from the rubric arithmetic, **not** run-to-run noise, and it "
                 "holds even when the question involved was outside the edited scope. "
                 "Confirm each alert below is intended before merging.")
elif v.get("quality_regression"):
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

# Pick the RIGHT header for the token we have — never send both. GitLab authenticates
# JOB-TOKEN and PRIVATE-TOKEN by different paths, and sending a Project Access Token in
# a JOB-TOKEN header is an authentication FAILURE, not a fallback: the request is rejected
# on that header rather than retried against the other one. Sending both is therefore a
# 401 waiting to happen the moment HARNESS_MR_TOKEN is set.
#
# CI_JOB_TOKEN cannot post notes AT ALL. GitLab restricts it to a fixed API allowlist
# (jobs, artifacts, registry, packages) that excludes /notes, so it 401s no matter what
# permissions the project grants — unlike GitHub Actions' GITHUB_TOKEN. A Project Access
# Token with `api` scope in HARNESS_MR_TOKEN is the only thing that works; say so clearly
# instead of emitting a bare 401 a reader would blame on the token's role.
if [[ -n "${HARNESS_MR_TOKEN:-}" ]]; then
  AUTH_HEADER="PRIVATE-TOKEN: ${TOKEN}"
else
  AUTH_HEADER="JOB-TOKEN: ${TOKEN}"
  echo "post-mr-comment: NOTE — falling back to CI_JOB_TOKEN, which cannot create MR" >&2
  echo "  notes (GitLab excludes /notes from its allowlist). Expect 401; set" >&2
  echo "  HARNESS_MR_TOKEN to a Project Access Token with 'api' scope to post." >&2
fi

# Send the body as a form field; curl handles the URL-encoding via --data-urlencode.
# Timeouts are REQUIRED, not defensive dressing: this is the last step of a job that has
# already spent ~130 agent-minutes, and curl left to its own devices will wait on an
# unreachable or wedged endpoint indefinitely — burning a runner and eventually dying on
# the job timeout with the verdict never printed. Bounded here so a network problem
# degrades to "couldn't post, here's the verdict" within seconds.
# Response body goes to a per-run temp file, NOT a fixed /tmp path. curl writes NOTHING to
# -o when the connection itself fails, so a fixed path would leave a PREVIOUS run's body in
# place and we would print a stale, unrelated error as if it were this attempt's response.
RESP="$(mktemp "${TMPDIR:-/tmp}/mr-note-resp.XXXXXX")"
trap 'rm -f "${RESP}"' EXIT

# NOTE the `-w` output is captured, so a `|| echo 000` fallback would APPEND to whatever
# curl already wrote and yield nonsense like "000000". Capture and branch on curl's exit
# code instead, and synthesize the code only when curl produced none.
if curl -sS -o "${RESP}" -w '%{http_code}' \
     --connect-timeout 10 --max-time 30 \
     --request POST "${URL}" \
     --header "${AUTH_HEADER}" \
     --data-urlencode "body=${BODY}" > "${RESP}.code" 2>"${RESP}.err"; then
  http_code="$(cat "${RESP}.code" 2>/dev/null)"
else
  # Transport-level failure (DNS, refused, timeout) — there is no HTTP status at all.
  http_code="000"
  cat "${RESP}.err" >&2 || true
fi
rm -f "${RESP}.code" "${RESP}.err"
http_code="${http_code:-000}"

if [[ "${http_code}" =~ ^2 ]]; then
  echo "post-mr-comment: posted (HTTP ${http_code})." >&2
else
  echo "post-mr-comment: could not post note (HTTP ${http_code}); verdict follows:" >&2
  # -s: quiet when the body is empty (a transport failure writes nothing) rather than
  # printing a bare newline that reads like an empty API response.
  [[ -s "${RESP}" ]] && cat "${RESP}" >&2 || true
  echo "" >&2
  printf '%s\n' "${BODY}" >&2
fi

# Advisory tool — always succeed so the pipeline stays green.
exit 0
