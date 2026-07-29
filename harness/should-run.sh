#!/usr/bin/env bash
#
# should-run.sh — deterministic default-run gate for the change-impact harness.
#
# Decides whether an MR is worth running the full analyze→diff→judge cycle on.
# This is a PURE PATH CHECK — no LLM, no network, no cost. The LLM is spent only at
# the judge step, after this gate has already said "run". See harness/DESIGN.md §5.
#
# Policy: DEFAULT-RUN. We run UNLESS *every* changed path matches the skip denylist.
# This is permissive by design so contributors are never boxed in — a rubric edit, a
# program-library change, a new/edited fixture, or a harness change all run. Only pure
# docs/license/meta changes skip.
#
# Exit codes:
#   0  → RUN  (at least one changed path is not denylisted, or diff is empty/unknown)
#   1  → SKIP (every changed path is denylisted)
#
# The harness automates a SPECIFIC, CONFIGURED set of TD directories — a change under
# any watched TD path (its SKILL.md + references/) RUNs the harness. A TD edit is
# inherently portfolio-wide, so it always triggers a full run. Note SKILL.md is a `.md`
# file, so the `*.md` denylist below would otherwise SKIP it — a watched-TD match wins.
#
# The MECHANISM is generic (match any configured path prefix); the CONFIG is specific.
# Today we watch the 4 managed TDs. To automate another TD — managed OR custom, wherever
# it lives — add its directory path to HARNESS_TD_PATHS (colon-separated) or edit the
# default list below. No other code change is needed.
#
# Scope resolution: prints the changed watched paths to stdout (informational), and sets
# these outputs when run under GitLab CI (written to should-run.env for `dotenv`):
#   HARNESS_RUN=true|false
#   HARNESS_CHANGED_TD=true|false     (a watched TD directory changed)
#   HARNESS_CHANGED_FIXTURES=true|false
#
# Usage:
#   should-run.sh [BASE_REF]        # BASE_REF defaults to the MR target or origin/main
#
set -euo pipefail

# Watched TD directory prefixes (repo-relative). Override/extend via HARNESS_TD_PATHS
# (colon-separated) to automate other TDs without touching this script. Default = the 4
# managed TDs this harness currently owns.
DEFAULT_TD_PATHS="definitions/managed/agentic-readiness-analysis:\
definitions/managed/modernization-readiness-analysis:\
definitions/managed/portfolio-agentic-readiness-analysis:\
definitions/managed/portfolio-modernization-readiness-analysis"
IFS=':' read -r -a TD_PATHS <<< "${HARNESS_TD_PATHS:-${DEFAULT_TD_PATHS}}"

# --- resolve the base ref to diff against --------------------------------------------
BASE_REF="${1:-}"
if [[ -z "${BASE_REF}" ]]; then
  if [[ -n "${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-}" ]]; then
    BASE_REF="origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}"
  elif [[ -n "${CI_DEFAULT_BRANCH:-}" ]]; then
    BASE_REF="origin/${CI_DEFAULT_BRANCH}"
  else
    BASE_REF="origin/main"
  fi
fi

# --- collect changed paths -----------------------------------------------------------
# Prefer a merge-base diff; fall back to a plain diff, then to "unknown → run".
changed=""
if git rev-parse --verify --quiet "${BASE_REF}" >/dev/null 2>&1; then
  merge_base="$(git merge-base "${BASE_REF}" HEAD 2>/dev/null || echo "${BASE_REF}")"
  changed="$(git diff --name-only "${merge_base}...HEAD" 2>/dev/null || true)"
fi
if [[ -z "${changed}" ]]; then
  # Last-committed change (e.g. detached CI checkout) — better to run than to miss.
  changed="$(git diff --name-only HEAD~1...HEAD 2>/dev/null || true)"
fi

# --- denylist: paths that provably cannot move analysis output -----------------------
# A change is a SKIP candidate only if it matches one of these. Everything else RUNS.
is_denylisted() {
  local p="$1"
  case "${p}" in
    LICENSE|LICENSE.*|NOTICE) return 0 ;;
    *.md)                     return 0 ;;   # docs, incl. DESIGN.md / READMEs
    .github/*)                return 0 ;;   # GitHub templates run nothing here
    .gitignore|.gitattributes|.editorconfig) return 0 ;;
    *.png|*.jpg|*.jpeg|*.gif|*.svg|*.ico|*.pdf) return 0 ;;
    .vscode/*|.kiro/*|.claude/*) return 0 ;;
    *) return 1 ;;
  esac
}

# --- classify + decide ---------------------------------------------------------------
# A path is a watched-TD change if it lives under any configured TD directory prefix.
is_watched_td() {
  local p="$1" prefix
  for prefix in "${TD_PATHS[@]}"; do
    [[ -n "${prefix}" && "${p}" == "${prefix}/"* ]] && return 0
  done
  return 1
}

run="false"
changed_td="false"
changed_fixtures="false"
nondenylisted=()

while IFS= read -r path; do
  [[ -z "${path}" ]] && continue
  # A watched-TD change ALWAYS runs, even if it's a .md file (SKILL.md) the denylist
  # would otherwise skip — the TD is exactly the thing we automate for.
  if is_watched_td "${path}"; then
    changed_td="true"; run="true"; nondenylisted+=("${path}")
    continue
  fi
  if ! is_denylisted "${path}"; then
    run="true"
    nondenylisted+=("${path}")
  fi
  case "${path}" in
    sample-legacy-portfolio/*|examples/fixtures/*) changed_fixtures="true"; run="true" ;;
  esac
done <<< "${changed}"

# Empty/unknown diff → default to RUN (never silently skip when we can't tell).
if [[ -z "${changed// /}" ]]; then
  run="true"
fi

# --- emit outputs --------------------------------------------------------------------
{
  echo "HARNESS_RUN=${run}"
  echo "HARNESS_CHANGED_TD=${changed_td}"
  echo "HARNESS_CHANGED_FIXTURES=${changed_fixtures}"
} > should-run.env 2>/dev/null || true

if [[ "${run}" == "true" ]]; then
  echo "RUN — analysis-affecting change detected (base=${BASE_REF})" >&2
  if [[ ${#nondenylisted[@]} -gt 0 ]]; then
    printf '  %s\n' "${nondenylisted[@]}" >&2
  fi
  exit 0
else
  echo "SKIP — every changed path is docs/meta only (base=${BASE_REF})" >&2
  exit 1
fi
