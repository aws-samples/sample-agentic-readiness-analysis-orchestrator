#!/usr/bin/env bash
#
# run-fixtures.sh — drive `atx ct` analysis over the harness fixtures and collect the
# resulting report JSON into an "after" tree that diff-reports.py can consume.
#
# This is the ONE step that needs AWS (via creds vended by the AWS Credential Vendor
# in CI — see harness/README.md). Everything downstream (diff-reports.py, judge.py) is
# offline. See DESIGN.md §5, §7.
#
# Modes:
#   --changed-only        Analyze only fixtures relevant to what changed (default in MRs).
#   --scope all           Analyze every fixture in usecases.yaml (full re-baseline).
#   --td <name>           Restrict to one managed TD's analysis type (ara|mod or the TD name).
#   --write-golden        After collecting, copy the reports into harness/golden/ (baseline
#                         refresh — used by the dedicated "baseline update" MR only).
#   --after-dir <dir>     Where to write collected reports (default: harness/_after).
#   --source-name <name>  ct source name (default: harness-portfolio).
#   --dry-run             Print the atx commands without executing (offline sanity check).
#
# Fixture list comes from harness/usecases.yaml (the `fixtures[].path` entries).
#
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HARNESS_DIR}/.." && pwd)"
USECASES="${HARNESS_DIR}/usecases.yaml"

# --- defaults ------------------------------------------------------------------------
SCOPE="changed"          # changed | all
TD_FILTER=""             # "", ara, mod, or a managed TD folder name
WRITE_GOLDEN="false"
# Honor an inherited AFTER_DIR (the CI job sets it) so the reports we write here land
# exactly where diff-reports.py reads them. Fall back to a local default otherwise.
# The --after-dir flag still overrides both.
AFTER_DIR="${AFTER_DIR:-${HARNESS_DIR}/_after}"
SOURCE_NAME="harness-portfolio"
DRY_RUN="false"

# --- arg parsing ---------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --changed-only)  SCOPE="changed"; shift ;;
    --scope)         SCOPE="$2"; shift 2 ;;
    --all)           SCOPE="all"; shift ;;
    --td)            TD_FILTER="$2"; shift 2 ;;
    --write-golden)  WRITE_GOLDEN="true"; shift ;;
    --after-dir)     AFTER_DIR="$2"; shift 2 ;;
    --source-name)   SOURCE_NAME="$2"; shift 2 ;;
    --dry-run)       DRY_RUN="true"; shift ;;
    -h|--help)       sed -n '2,40p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# --- normalize TD filter to analysis types -------------------------------------------
# The 4 managed TDs map to 2 analysis run types (each run produces per-repo + portfolio).
run_ara="true"; run_mod="true"
case "${TD_FILTER}" in
  ""|all) : ;;
  ara|agentic-readiness-analysis|portfolio-agentic-readiness-analysis)     run_mod="false" ;;
  mod|moda|modernization-readiness-analysis|portfolio-modernization-readiness-analysis) run_ara="false" ;;
  *) echo "warn: unknown --td '${TD_FILTER}', running both analyses" >&2 ;;
esac

# --- resolve which fixtures to analyze -----------------------------------------------
# `all`     → every fixtures[].path in usecases.yaml
# `changed` → intersect git-changed paths with fixture paths; if a non-fixture output
#             surface changed (rubric / program-library), analyze ALL fixtures (a rubric
#             change affects every repo). See should-run.sh outputs.
ALL_FIXTURES=()
while IFS= read -r line; do
  [[ -n "${line}" ]] && ALL_FIXTURES+=("${line}")
done < <(
  python3 - "${USECASES}" <<'PY'
import sys, yaml
doc = yaml.safe_load(open(sys.argv[1]))
for f in doc.get("fixtures", []):
    print(f["path"])
PY
)

selected=()
if [[ "${SCOPE}" == "all" ]]; then
  selected=("${ALL_FIXTURES[@]}")
else
  # changed-only: source the gate's env if present, else compute a diff here.
  changed_rubric="${HARNESS_CHANGED_RUBRIC:-false}"
  changed_prog="${HARNESS_CHANGED_PROGRAM_LIBRARY:-false}"
  if [[ -f "${REPO_ROOT}/should-run.env" ]]; then
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/should-run.env" || true
    changed_rubric="${HARNESS_CHANGED_RUBRIC:-${changed_rubric}}"
    changed_prog="${HARNESS_CHANGED_PROGRAM_LIBRARY:-${changed_prog}}"
  fi
  if [[ "${changed_rubric}" == "true" || "${changed_prog}" == "true" ]]; then
    echo "changed-only: rubric/program-library change affects all fixtures → analyzing all" >&2
    selected=("${ALL_FIXTURES[@]}")
  else
    base="${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:+origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}}"
    base="${base:-origin/main}"
    changed_paths=()
    while IFS= read -r line; do
      [[ -n "${line}" ]] && changed_paths+=("${line}")
    done < <(git -C "${REPO_ROOT}" diff --name-only "${base}...HEAD" 2>/dev/null || true)
    for fx in "${ALL_FIXTURES[@]}"; do
      for cp in "${changed_paths[@]}"; do
        [[ "${cp}" == "${fx}"* ]] && { selected+=("${fx}"); break; }
      done
    done
    # No fixture directly changed but the gate said run (e.g. harness config) → analyze all.
    [[ ${#selected[@]} -eq 0 ]] && selected=("${ALL_FIXTURES[@]}")
  fi
fi

echo "run-fixtures: scope=${SCOPE} ara=${run_ara} mod=${run_mod} fixtures=${#selected[@]} after=${AFTER_DIR}" >&2

# --- helper to run or echo -----------------------------------------------------------
run() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "+ $*" >&2
  else
    echo "+ $*" >&2
    "$@"
  fi
}

# --- build a local ct source pointing at the selected fixtures -----------------------
# ct's local provider takes a parent dir of repos. Our fixtures live in two trees
# (sample-legacy-portfolio/ and examples/fixtures/), so we stage symlinks into one dir.
STAGE="${AFTER_DIR}/_src"
mkdir -p "${STAGE}" "${AFTER_DIR}"
for fx in "${selected[@]}"; do
  name="$(basename "${fx}")"
  target="${REPO_ROOT}/${fx}"
  [[ -e "${target}" ]] || { echo "warn: fixture path missing: ${fx}" >&2; continue; }
  ln -sfn "${target}" "${STAGE}/${name}"
done

run atx ct status --health || echo "warn: atx health check failed (creds?)" >&2
run atx ct source add --name "${SOURCE_NAME}" --provider local --path "${STAGE}" || true
run atx ct discovery scan --source "${SOURCE_NAME}"

# --- run analyses --------------------------------------------------------------------
if [[ "${run_ara}" == "true" ]]; then
  run atx ct analysis run --type agentic-readiness --source "${SOURCE_NAME}" --wait
fi
if [[ "${run_mod}" == "true" ]]; then
  run atx ct analysis run --type modernization-readiness --source "${SOURCE_NAME}" --wait
fi

# --- collect artifacts into the after tree -------------------------------------------
# On local sources ct writes report JSON into the repo working trees; for portability we
# also pull via get-artifact. Collect everything matching our report naming into AFTER_DIR.
if [[ "${DRY_RUN}" != "true" ]]; then
  # Sweep any *-report.json produced under the staged sources / working trees.
  find "${STAGE}" -type f \( -name '*-ara-report.json' -o -name '*-mod-report.json' \) \
    -exec cp -f {} "${AFTER_DIR}/" \; 2>/dev/null || true
  # Portfolio reports (ct writes these to the source root or a portfolio dir).
  find "${STAGE}" -type f -name '*-portfolio-*-report.json' \
    -exec cp -f {} "${AFTER_DIR}/" \; 2>/dev/null || true
  echo "collected $(find "${AFTER_DIR}" -maxdepth 1 -name '*-report.json' | wc -l | tr -d ' ') report(s) into ${AFTER_DIR}" >&2
fi

# --- optionally refresh golden baselines ---------------------------------------------
if [[ "${WRITE_GOLDEN}" == "true" ]]; then
  GOLDEN="${HARNESS_DIR}/golden"
  mkdir -p "${GOLDEN}"
  if [[ "${DRY_RUN}" != "true" ]]; then
    cp -f "${AFTER_DIR}"/*-report.json "${GOLDEN}/" 2>/dev/null || true
    echo "golden baselines refreshed in ${GOLDEN}" >&2
  else
    echo "+ cp ${AFTER_DIR}/*-report.json ${GOLDEN}/" >&2
  fi
fi

echo "done." >&2
