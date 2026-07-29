#!/usr/bin/env bash
#
# run-fixtures.sh — produce the harness "after" report tree by running OUR edited
# managed TDs over the fixtures, then collect the report JSON for diff-reports.py.
#
# WHY `atx custom def exec` AND NOT `atx ct`:
#   A contributor's change lands on the TD definitions IN THIS REPO
#   (definitions/managed/**) — it is NOT on AWS Transform Continuous Modernization yet.
#   `atx ct` runs the OLD service-side definitions, so it
#   CANNOT see the edit under review — it would diff a change it can't observe. To test
#   the change that's actually proposed, we publish our repo's TD folders as CUSTOM defs
#   and run `atx custom def exec`, which runs exactly the SKILL.md we ship. Once the TDs
#   are published to Continuous Modernization, an `atx ct` parity path can replace this.
#
# This is the ONE step that needs AWS (creds vended by the AWS Credential Vendor in CI —
# see harness/README.md). Everything downstream (diff-reports.py, judge.py) is offline.
# See DESIGN.md §5, §7.
#
# Modes:
#   --changed-only        Analyze only fixtures relevant to what changed (default in MRs).
#   --scope all | --all   Analyze every fixture in usecases.yaml (full re-baseline).
#   --td <name>           Restrict to one managed TD's analysis type (ara|mod or TD name).
#   --write-golden        After collecting, copy reports into harness/golden/ (baseline
#                         refresh — used by the dedicated "baseline update" MR only).
#   --after-dir <dir>     Where to write collected reports (default: harness/_after).
#   --name-suffix <s>     Suffix on published custom-def names so we never clobber the
#                         managed names (default: -harness).
#   --portfolio-name <n>  portfolio_name passed to the portfolio TDs (default: harness-portfolio).
#   --skip-publish        Reuse already-published custom defs (skip the publish step).
#   --no-portfolio        Per-repo ARA/MOD only; skip the two portfolio stages.
#   --validate            Also check each collected report against validate-contract.py.
#   --jobs <N>            Run the per-repo execs in parallel, up to N at a time
#                         (default 1 = serial). Waves: all ARA concurrently, then all
#                         MOD concurrently, then the portfolios serially (they aggregate
#                         the per-repo reports, so they must run after both waves). Each
#                         exec waits on Bedrock, so parallelism is a big wall-clock win.
#   --dry-run             Print the atx commands without executing (offline sanity check).
#
# Fixture list comes from harness/usecases.yaml (the `fixtures[].path` entries).
#
# bash 3.2 compatible (macOS default) — no associative arrays, no `wait -n`.
#
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HARNESS_DIR}/.." && pwd)"
MANAGED="${REPO_ROOT}/definitions/managed"
USECASES="${HARNESS_DIR}/usecases.yaml"

# --- defaults ------------------------------------------------------------------------
SCOPE="changed"          # changed | all
TD_FILTER=""             # "", ara, mod, or a managed TD folder name
WRITE_GOLDEN="false"
# Honor an inherited AFTER_DIR (the CI job sets it) so the reports we write here land
# exactly where diff-reports.py reads them. The --after-dir flag still overrides both.
AFTER_DIR="${AFTER_DIR:-${HARNESS_DIR}/_after}"
NAME_SUFFIX="-harness"
PORTFOLIO_NAME="harness-portfolio"
SKIP_PUBLISH="false"
NO_PORTFOLIO="false"
VALIDATE="false"
JOBS=1
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
    --name-suffix)   NAME_SUFFIX="$2"; shift 2 ;;
    --portfolio-name) PORTFOLIO_NAME="$2"; shift 2 ;;
    --skip-publish)  SKIP_PUBLISH="true"; shift ;;
    --no-portfolio)  NO_PORTFOLIO="true"; shift ;;
    --validate)      VALIDATE="true"; shift ;;
    --jobs)          JOBS="$2"; shift 2 ;;
    --dry-run)       DRY_RUN="true"; shift ;;
    -h|--help)       sed -n '2,48p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# --- validate --jobs -----------------------------------------------------------------
case "${JOBS}" in
  ''|*[!0-9]*) echo "error: --jobs must be a positive integer, got '${JOBS}'" >&2; exit 2 ;;
esac
[[ "${JOBS}" -lt 1 ]] && JOBS=1

# --- normalize TD filter to analysis types -------------------------------------------
# The 4 managed TDs map to 2 analysis types (each runs per-repo + portfolio).
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
  # A TD change is portfolio-wide → analyze every fixture. Only a fixture-specific edit
  # (which contributors don't normally make — they edit the TDs) narrows the set.
  changed_td="${HARNESS_CHANGED_TD:-false}"
  if [[ -f "${REPO_ROOT}/should-run.env" ]]; then
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/should-run.env" || true
    changed_td="${HARNESS_CHANGED_TD:-${changed_td}}"
  fi
  if [[ "${changed_td}" == "true" ]]; then
    echo "changed-only: a watched TD changed → analyzing all fixtures (portfolio-wide)" >&2
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

echo "run-fixtures: scope=${SCOPE} ara=${run_ara} mod=${run_mod} fixtures=${#selected[@]} after=${AFTER_DIR} (engine: atx custom def exec)" >&2

# A stray AWS_REGION=us-west-2 makes the custom-def endpoint fail to resolve; only
# us-east-1 resolves. Set it unless the caller already pinned a region.
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

command -v atx >/dev/null 2>&1 || { echo "error: atx CLI not found" >&2; exit 2; }

run() { echo "+ $*" >&2; [[ "${DRY_RUN}" == "true" ]] || "$@"; }

# --- helpers -------------------------------------------------------------------------

# description from a SKILL.md YAML frontmatter `description:` line (publish needs it).
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

# collect newest report matching a glob under a dir, copy to AFTER_DIR (optional validate).
# args: <search-dir> <glob> <analysis-type>
collect_report() {
  local search="$1" glob="$2" analysis="$3" found dest
  [[ "${DRY_RUN}" == "true" ]] && return 0
  found="$(find "${search}" -type f -name "${glob}" \
             -exec stat -f '%m %N' {} \; 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
  if [[ -z "${found}" ]]; then
    echo "warn: no ${glob} emitted (${analysis})" >&2; return 1
  fi
  dest="${AFTER_DIR}/$(basename "${found}")"
  cp -f "${found}" "${dest}"
  echo "collected ${dest}" >&2
  if [[ "${VALIDATE}" == "true" ]]; then
    python3 "${HARNESS_DIR}/validate-contract.py" "${dest}" --analysis "${analysis}" \
      && echo "${analysis}: CONTRACT OK" >&2 \
      || echo "${analysis}: CONTRACT VIOLATION" >&2
  fi
}

# --- prepare staging + publish the TDs we need ---------------------------------------
STAGE="${AFTER_DIR}/_src"
if [[ "${DRY_RUN}" != "true" ]]; then
  rm -rf "${STAGE}"; mkdir -p "${STAGE}" "${AFTER_DIR}"
fi

# per-repo | analysis | td-folder | report-glob   (filtered by run_ara/run_mod below)
if [[ "${run_ara}" == "true" ]]; then
  publish_td "${MANAGED}/agentic-readiness-analysis" "agentic-readiness-analysis${NAME_SUFFIX}" || exit 2
fi
if [[ "${run_mod}" == "true" ]]; then
  publish_td "${MANAGED}/modernization-readiness-analysis" "modernization-readiness-analysis${NAME_SUFFIX}" || exit 2
fi

# --- Stage 1: per-repo ARA + MOD over each selected fixture ---------------------------
# We COPY each fixture into its OWN stage dir and `git init` that copy as a SELF-CONTAINED
# git repo. This is load-bearing, not cosmetic:
#
#   `atx custom def exec` runs git commands on whatever repo ENCLOSES its -p target
#   (it creates an `atx-result-staging-*` branch and commits the report bundle). Git
#   discovery walks UP the tree until it finds a `.git`. If the stage dir has no `.git`,
#   atx climbs into OUR repo and hijacks HEAD — and N parallel execs then fight over one
#   `.git`, corrupting the branch. Giving each stage dir its own `.git` stops discovery at
#   that boundary: atx's git dance stays fully contained, so (a) our repo is never touched
#   and (b) parallel execs are safe by construction (each mutates only its own nested repo).
#
# Run in WAVES: all ARA concurrently, then all MOD concurrently (throttled to --jobs).
# The portfolio stages (below) aggregate the per-repo reports, so they run AFTER both
# waves. Each exec mostly waits on Bedrock, so wave parallelism is a large wall-clock win.

# Remember our repo's branch so we can PROVE atx never moved it (belt-and-suspenders on
# top of the per-stage .git isolation above).
GUARD_REPO_HEAD=""
if [[ "${DRY_RUN}" != "true" ]]; then
  GUARD_REPO_HEAD="$(git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
fi

# git-init a stage dir as a self-contained repo with one baseline commit, so atx's git
# operations have a local HEAD to branch from and never escape into an ancestor repo.
git_init_stage() {
  local d="$1"
  git -C "${d}" init -q 2>/dev/null || return 1
  git -C "${d}" config user.email "harness@local" 2>/dev/null || true
  git -C "${d}" config user.name  "harness" 2>/dev/null || true
  git -C "${d}" config commit.gpgsign false 2>/dev/null || true
  git -C "${d}" add -A 2>/dev/null || true
  git -C "${d}" commit -q -m "fixture baseline" 2>/dev/null || true
}

# Stage every fixture locally up front (fast, local copy), each as its own git repo.
STAGE_NAMES=()
STAGE_DIRS=()
for fx in "${selected[@]}"; do
  name="$(basename "${fx}")"
  target="${REPO_ROOT}/${fx}"
  [[ -e "${target}" ]] || { echo "warn: fixture path missing: ${fx}" >&2; continue; }
  dest="${STAGE}/${name}"
  if [[ "${DRY_RUN}" != "true" ]]; then
    mkdir -p "${dest}"
    # Copy contents WITHOUT any nested .git from the source, then init a fresh one.
    cp -RL "${target}/." "${dest}/" 2>/dev/null || cp -R "${target}/." "${dest}/"
    rm -rf "${dest}/.git"
    git_init_stage "${dest}"
  fi
  STAGE_NAMES+=("${name}")
  STAGE_DIRS+=("${dest}")
done
[[ "${DRY_RUN}" != "true" ]] && mkdir -p "${AFTER_DIR}/_logs"

# Abort the run if our repo's HEAD ever moves (would mean the isolation failed). Called
# after each wave and after the portfolio stage.
assert_repo_head() {
  [[ "${DRY_RUN}" == "true" || -z "${GUARD_REPO_HEAD}" ]] && return 0
  local now; now="$(git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
  if [[ "${now}" != "${GUARD_REPO_HEAD}" ]]; then
    echo "FATAL: repo HEAD moved (${GUARD_REPO_HEAD} -> ${now}) — atx escaped its stage repo." >&2
    echo "       Restoring branch and aborting so nothing corrupts the working tree." >&2
    git -C "${REPO_ROOT}" checkout -q "${GUARD_REPO_HEAD}" 2>/dev/null || true
    exit 3
  fi
}

# Block until fewer than JOBS background jobs are running (bash 3.2: no `wait -n`).
wait_for_slot() {
  while [[ "$(jobs -rp | wc -l | tr -d ' ')" -ge "${JOBS}" ]]; do sleep 1; done
}

# run one (analysis, fixture) unit: exec the def, then collect+validate its report.
# When parallel, atx's verbose output is routed to a per-unit log so the main log stays
# readable; only concise markers go to the shared stderr. Always returns 0 (never trips
# set -e / the `wait` below), since a missing report is a warning, not a fatal error.
run_unit() {
  local analysis="$1" name="$2" dest="$3" defname="$4" glob="$5"
  local label; label="$(echo "${analysis}" | tr '[:lower:]' '[:upper:]')"
  echo "=== ${label}: ${name} ===" >&2
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "+ atx custom def exec -n ${defname} -p ${dest} --non-interactive --trust-all-tools --do-not-learn" >&2
    return 0
  fi
  local ulog="${AFTER_DIR}/_logs/${name}-${analysis}.log"
  if [[ "${JOBS}" -gt 1 ]]; then
    atx custom def exec -n "${defname}" -p "${dest}" \
      --non-interactive --trust-all-tools --do-not-learn > "${ulog}" 2>&1 \
      || echo "warn: ${analysis} exec failed for ${name} (see ${ulog})" >&2
  else
    atx custom def exec -n "${defname}" -p "${dest}" \
      --non-interactive --trust-all-tools --do-not-learn 2>&1 | tee "${ulog}" \
      || echo "warn: ${analysis} exec failed for ${name} (see ${ulog})" >&2
  fi
  collect_report "${dest}" "${glob}" "${analysis}" || true
  return 0
}

# run all fixtures for one analysis as a wave, throttled to JOBS, then barrier.
run_wave() {
  local analysis="$1" defname="$2" glob="$3" i
  echo "" >&2
  echo "--- wave: ${analysis} — ${#STAGE_NAMES[@]} fixture(s), jobs=${JOBS} ---" >&2
  for ((i = 0; i < ${#STAGE_NAMES[@]}; i++)); do
    if [[ "${JOBS}" -gt 1 ]]; then
      wait_for_slot
      run_unit "${analysis}" "${STAGE_NAMES[$i]}" "${STAGE_DIRS[$i]}" "${defname}" "${glob}" &
    else
      run_unit "${analysis}" "${STAGE_NAMES[$i]}" "${STAGE_DIRS[$i]}" "${defname}" "${glob}"
    fi
  done
  [[ "${JOBS}" -gt 1 ]] && wait || true
}

if [[ "${run_ara}" == "true" ]]; then
  run_wave ara "agentic-readiness-analysis${NAME_SUFFIX}" '*-ara-report.json'
  assert_repo_head
fi
if [[ "${run_mod}" == "true" ]]; then
  run_wave mod "modernization-readiness-analysis${NAME_SUFFIX}" '*-mod-report.json'
  assert_repo_head
fi

# --- Stage 2: portfolio ARA + MOD -----------------------------------------------------
# The portfolio TDs aggregate the per-repo reports Stage 1 collected. Stage those into a
# portfolio input dir (its OWN git repo, same isolation as Stage 1) and exec the portfolio
# TD against it, passing portfolio_name via additionalPlanContext.
if [[ "${NO_PORTFOLIO}" != "true" ]]; then
  PORT_SRC="${AFTER_DIR}/_portfolio_src"
  if [[ "${DRY_RUN}" != "true" ]]; then
    rm -rf "${PORT_SRC}"; mkdir -p "${PORT_SRC}"
    cp -f "${AFTER_DIR}"/*-ara-report.json "${AFTER_DIR}"/*-mod-report.json "${PORT_SRC}/" 2>/dev/null || true
    git_init_stage "${PORT_SRC}"
  fi
  if [[ "${run_ara}" == "true" ]]; then
    publish_td "${MANAGED}/portfolio-agentic-readiness-analysis" "portfolio-agentic-readiness-analysis${NAME_SUFFIX}" || true
    echo "" >&2; echo "=== portfolio ARA ===" >&2
    run atx custom def exec -n "portfolio-agentic-readiness-analysis${NAME_SUFFIX}" -p "${PORT_SRC}" \
      --non-interactive --trust-all-tools --do-not-learn \
      --configuration "additionalPlanContext=portfolio_name: ${PORTFOLIO_NAME}"
    collect_report "${PORT_SRC}" '*portfolio-ara-report.json' portfolio-ara
  fi
  if [[ "${run_mod}" == "true" ]]; then
    publish_td "${MANAGED}/portfolio-modernization-readiness-analysis" "portfolio-modernization-readiness-analysis${NAME_SUFFIX}" || true
    echo "" >&2; echo "=== portfolio MOD ===" >&2
    run atx custom def exec -n "portfolio-modernization-readiness-analysis${NAME_SUFFIX}" -p "${PORT_SRC}" \
      --non-interactive --trust-all-tools --do-not-learn \
      --configuration "additionalPlanContext=portfolio_name: ${PORTFOLIO_NAME}"
    collect_report "${PORT_SRC}" '*portfolio-mod-report.json' portfolio-mod
  fi
  assert_repo_head
fi

if [[ "${DRY_RUN}" != "true" ]]; then
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
