#!/usr/bin/env bash
#
# exec-contract.sh — run OUR fixed managed TDs against a repo via `atx custom def exec`
# and validate the emitted JSON against the ingester contract.
#
# WHY THIS EXISTS (and why NOT `atx ct`):
#   The fixed TD definitions currently live ONLY in this repo — they are not yet
#   published to AWS Transform Continuous Modernization. So `atx ct` (which
#   run-fixtures.sh drives) still runs the OLD service-side definitions and emits the
#   drifted 3.7.0 shape — it cannot exercise our edits. To test the contract TODAY we
#   publish our repo's TD folders as CUSTOM defs and run `atx custom def exec`, which
#   runs exactly the SKILL.md we ship. Once the fixed TDs are published to Continuous
#   Modernization, `atx ct` + the golden path will validate the same contract end-to-end.
#
# Covers all FOUR managed TDs: per-repo ARA + MOD, then portfolio ARA + MOD (which
# aggregate the per-repo *-{ara,mod}-report.json produced by the first stage).
#
# Usage:
#   exec-contract.sh [--repo <path>] [--out <dir>] [--name-suffix <s>]
#                    [--portfolio-name <n>] [--skip-publish] [--no-portfolio] [--dry-run]
#     --repo            repo to analyze per-repo (default: sample-legacy-portfolio/legacy-shipping-api)
#     --out             where to collect reports (default: harness/_contract)
#     --name-suffix     appended to published TD names so we never clobber managed names
#                       (default: -contract-test)
#     --portfolio-name  portfolio_name passed to the portfolio TDs (default: contract-portfolio)
#     --skip-publish    reuse already-published custom defs (skip publish step)
#     --no-portfolio    per-repo ARA+MOD only; skip the two portfolio stages
#     --dry-run         print commands without executing
#
# bash 3.2 compatible (macOS default) — no associative arrays.
#
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HARNESS_DIR}/.." && pwd)"
MANAGED="${REPO_ROOT}/definitions/managed"

REPO_PATH="${REPO_ROOT}/sample-legacy-portfolio/legacy-shipping-api"
OUT_DIR="${HARNESS_DIR}/_contract"
NAME_SUFFIX="-contract-test"
PORTFOLIO_NAME="contract-portfolio"
SKIP_PUBLISH="false"
NO_PORTFOLIO="false"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)           REPO_PATH="$2"; shift 2 ;;
    --out)            OUT_DIR="$2"; shift 2 ;;
    --name-suffix)    NAME_SUFFIX="$2"; shift 2 ;;
    --portfolio-name) PORTFOLIO_NAME="$2"; shift 2 ;;
    --skip-publish)   SKIP_PUBLISH="true"; shift ;;
    --no-portfolio)   NO_PORTFOLIO="true"; shift ;;
    --dry-run)        DRY_RUN="true"; shift ;;
    -h|--help)        sed -n '2,40p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

run() { echo "+ $*" >&2; [[ "${DRY_RUN}" == "true" ]] || "$@"; }

command -v atx >/dev/null 2>&1 || { echo "error: atx CLI not found" >&2; exit 2; }
[[ -d "${REPO_PATH}" ]] || { echo "error: repo not found: ${REPO_PATH}" >&2; exit 2; }

mkdir -p "${OUT_DIR}"
OVERALL=0

# description from a SKILL.md YAML frontmatter `description:` line (publish path needs it).
skill_description() {
  awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{exit} \
       f&&/^description:[[:space:]]*/{sub(/^description:[[:space:]]*/,"");print;exit}' "$1"
}

# publish a TD folder as a custom def under a non-clobbering name.
publish_td() {
  local src="$1" td_name="$2" desc
  [[ -f "${src}/SKILL.md" ]] || { echo "error: no SKILL.md in ${src}" >&2; return 2; }
  [[ "${SKIP_PUBLISH}" == "true" ]] && { echo "(skip-publish) ${td_name}" >&2; return 0; }
  desc="$(skill_description "${src}/SKILL.md")"; [[ -n "${desc}" ]] || desc="${td_name}"
  run atx custom def publish -n "${td_name}" --description "${desc}" --sd "${src}"
}

# collect newest report matching a glob under a dir, copy to OUT_DIR, validate.
# args: <search-dir> <glob> <analysis-type>
collect_and_validate() {
  local search="$1" glob="$2" analysis="$3" found dest
  [[ "${DRY_RUN}" == "true" ]] && return 0
  found="$(find "${search}" -type f -name "${glob}" \
             -exec stat -f '%m %N' {} \; 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
  if [[ -z "${found}" ]]; then
    echo "error: no ${glob} emitted (${analysis})" >&2; OVERALL=1; return 1
  fi
  dest="${OUT_DIR}/$(basename "${found}")"
  cp -f "${found}" "${dest}"
  echo "collected ${dest}" >&2
  if python3 "${HARNESS_DIR}/validate-contract.py" "${dest}" --analysis "${analysis}"; then
    echo "${analysis}: CONTRACT OK" >&2
  else
    echo "${analysis}: CONTRACT VIOLATION" >&2; OVERALL=1
  fi
}

# ---- Stage 1: per-repo ARA + MOD ----------------------------------------------------
# analysis | td-folder | report-glob
PER_REPO="ara agentic-readiness-analysis *-ara-report.json
mod modernization-readiness-analysis *-mod-report.json"

while read -r analysis folder glob; do
  [[ -z "${analysis}" ]] && continue
  src="${MANAGED}/${folder}"
  td_name="${folder}${NAME_SUFFIX}"
  echo "" >&2; echo "=== per-repo ${analysis}: ${td_name} ===" >&2
  publish_td "${src}" "${td_name}" || { OVERALL=1; continue; }
  run atx custom def exec -n "${td_name}" -p "${REPO_PATH}" \
    --non-interactive --trust-all-tools --do-not-learn
  collect_and_validate "${REPO_PATH}" "${glob}" "${analysis}"
done <<< "${PER_REPO}"

# ---- Stage 2: portfolio ARA + MOD ---------------------------------------------------
# Portfolio TDs aggregate the per-repo *-{ara,mod}-report.json. We stage the per-repo
# reports the first stage collected into a portfolio input dir and exec the portfolio
# TD against it, passing portfolio_name via additionalPlanContext.
if [[ "${NO_PORTFOLIO}" != "true" ]]; then
  PORT_SRC="${OUT_DIR}/_portfolio_src"
  if [[ "${DRY_RUN}" != "true" ]]; then
    rm -rf "${PORT_SRC}"; mkdir -p "${PORT_SRC}"
    cp -f "${OUT_DIR}"/*-ara-report.json "${OUT_DIR}"/*-mod-report.json "${PORT_SRC}/" 2>/dev/null || true
  fi

  # analysis | td-folder | report-glob
  PORTFOLIO="portfolio-ara portfolio-agentic-readiness-analysis *portfolio-ara-report.json
portfolio-mod portfolio-modernization-readiness-analysis *portfolio-mod-report.json"

  while read -r analysis folder glob; do
    [[ -z "${analysis}" ]] && continue
    src="${MANAGED}/${folder}"
    td_name="${folder}${NAME_SUFFIX}"
    echo "" >&2; echo "=== ${analysis}: ${td_name} ===" >&2
    publish_td "${src}" "${td_name}" || { OVERALL=1; continue; }
    run atx custom def exec -n "${td_name}" -p "${PORT_SRC}" \
      --non-interactive --trust-all-tools --do-not-learn \
      --configuration "additionalPlanContext=portfolio_name: ${PORTFOLIO_NAME}"
    collect_and_validate "${PORT_SRC}" "${glob}" "${analysis}"
  done <<< "${PORTFOLIO}"
fi

echo "" >&2
if [[ "${OVERALL}" -eq 0 ]]; then
  echo "exec-contract: all analyses conform to the ingester contract." >&2
else
  echo "exec-contract: at least one analysis violated the contract (see above)." >&2
fi
exit "${OVERALL}"
