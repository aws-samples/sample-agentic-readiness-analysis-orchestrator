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
#                         A TD edit is portfolio-wide in PRINCIPLE, but analyzing all 11
#                         fixtures x 2 analyses = 22 units, each billing ~110-130 AGENT-
#                         minutes (internal compute; wall-clock per unit is ~10-20 min,
#                         measured), and atx's progress spinner blows GitLab's 4 MB log
#                         cap after ~4 units. So a
#                         changed TD now selects the 1-2 fixtures that best EXERCISE the
#                         edited questions, via select-fixtures.py (category-matched off
#                         usecases.yaml expectations). Tune with --mr-fixtures N.
#                         The exhaustive sweep is --scope all, run locally or via
#                         harness:full — not on an MR.
#   --mr-fixtures <N>     How many fixtures the changed-only path selects (default 2).
#   --scope all | --all   Analyze every fixture in usecases.yaml (full re-baseline).
#   --td <name>           Restrict to one managed TD's analysis type (ara|mod or TD name).
#   --write-golden        After collecting, copy reports into harness/golden/ (baseline
#                         refresh — used by the dedicated "baseline update" MR only).
#   --after-dir <dir>     Where to write collected reports (default: harness/_after).
#                         Refuses to start if the dir already holds reports — each
#                         baseline batch must stay a separate, intact draw.
#   --force               Reuse an --after-dir that already holds reports (e.g. to resume
#                         a batch that died part-way). Overwrites matching reports.
#   --name-suffix <s>     Suffix on published custom-def names so we never clobber the
#                         managed names (default: -harness).
#   --portfolio-name <n>  portfolio_name passed to the portfolio TDs (default: harness-portfolio).
#   --skip-publish        Reuse already-published custom defs (skip the publish step).
#   --no-portfolio        Per-repo ARA/MOD only; skip the two portfolio stages.
#   --validate            Also check each collected report against validate-contract.py.
#   --jobs <N>            Run the per-repo execs in parallel, up to N at a time
#                         (default 1 = serial). ALL per-repo units (ARA + MOD for every
#                         fixture) share ONE throttled pool — ARA and MOD interleave and a
#                         MOD unit backfills a slot as soon as any ARA unit finishes (no
#                         wave barrier). The two portfolios run serially AFTER the pool
#                         drains (they aggregate the per-repo reports). Each exec waits on
#                         Bedrock, so pooling is a big wall-clock win.
#   --only <name>         Restrict the run to a single fixture (its path basename). Composes
#                         with any --scope; errors if the name matches no fixture. Use to
#                         backfill one fixture a transient failure dropped from a batch.
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
# Allow reusing an --after-dir that already holds reports (see the clobber guard below).
FORCE="false"
# Honor an inherited AFTER_DIR (the CI job sets it) so the reports we write here land
# exactly where diff-reports.py reads them. The --after-dir flag still overrides both.
AFTER_DIR="${AFTER_DIR:-${HARNESS_DIR}/_after}"
NAME_SUFFIX="-harness"
PORTFOLIO_NAME="harness-portfolio"
SKIP_PUBLISH="false"
NO_PORTFOLIO="false"
VALIDATE="false"
JOBS=1
MR_FIXTURES="${HARNESS_MR_FIXTURES:-2}"   # changed-only: how many fixtures to select
DRY_RUN="false"
ONLY=""                  # restrict the run to one fixture (matched by path basename)

# --- arg parsing ---------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --changed-only)  SCOPE="changed"; shift ;;
    --scope)         SCOPE="$2"; shift 2 ;;
    --all)           SCOPE="all"; shift ;;
    --td)            TD_FILTER="$2"; shift 2 ;;
    --write-golden)  WRITE_GOLDEN="true"; shift ;;
    --force)         FORCE="true"; shift ;;
    --after-dir)     AFTER_DIR="$2"; shift 2 ;;
    --name-suffix)   NAME_SUFFIX="$2"; shift 2 ;;
    --portfolio-name) PORTFOLIO_NAME="$2"; shift 2 ;;
    --skip-publish)  SKIP_PUBLISH="true"; shift ;;
    --no-portfolio)  NO_PORTFOLIO="true"; shift ;;
    --validate)      VALIDATE="true"; shift ;;
    --jobs)          JOBS="$2"; shift 2 ;;
    --mr-fixtures)   MR_FIXTURES="$2"; shift 2 ;;
    --only)          ONLY="$2"; shift 2 ;;
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
# Accumulates the question ids the rubric edit touched (see the selector loop below). Written
# to ${AFTER_DIR}/edited-questions.txt for the judge step; empty on a full sweep (nothing was
# "edited" in particular) or when no TD changed.
_edited_q_file="$(mktemp "${TMPDIR:-/tmp}/harness-edited-q.XXXXXX")"
trap 'rm -f "${_edited_q_file}"' EXIT
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
    # A TD edit affects every repo in principle — but "analyze all 11" is 22 units of
    # ~110-130 agent-min each, and it truncated the CI log, so it is not an MR feedback
    # loop. Instead pick the 1-2 fixtures whose declared expectations actually
    # exercise the EDITED questions (select-fixtures.py matches the question-id category
    # prefix, e.g. API-Q2 -> API, against usecases.yaml must_have_categories).
    # The exhaustive sweep stays available as --scope all (local / harness:full).
    sel_base="${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:+origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}}"
    sel_base="${sel_base:-origin/main}"
    # Every selection decision below is a diff against sel_base, and in GitLab's shallow
    # `git depth 20` clone that ref is normally ABSENT — the diff then comes back empty and
    # we cannot tell "nothing changed" from "I can't see the change". should-run.sh fetches
    # it, but don't depend on having been run through the gate (local invocations, or a
    # future job that calls this directly). Fetch it here too; idempotent when present.
    if ! git -C "${REPO_ROOT}" rev-parse --verify --quiet "${sel_base}" >/dev/null 2>&1; then
      echo "run-fixtures: ${sel_base} missing locally (shallow clone) — fetching for selection" >&2
      git -C "${REPO_ROOT}" fetch -q --depth=50 origin \
        "+refs/heads/${sel_base#origin/}:refs/remotes/origin/${sel_base#origin/}" 2>/dev/null \
        || echo "run-fixtures: WARN could not fetch ${sel_base}; selection will fall back" >&2
    fi
    # A portfolio TD change must select >=2 fixtures: the rollup it edits aggregates
    # per-repo reports, and aggregating one repo exercises nothing. Floor it here so the
    # portfolio stage below isn't skipped by its own >=2 guard.
    if [[ "${HARNESS_CHANGED_PORTFOLIO_TD:-false}" == "true" && "${MR_FIXTURES}" -lt 2 ]]; then
      echo "changed-only: portfolio TD changed → raising --mr-fixtures ${MR_FIXTURES} → 2" >&2
      MR_FIXTURES=2
    fi
    selected=()
    # Biggest single MR saving: only run the analysis types the MR actually touched.
    # An ARA-only rubric edit cannot move a MOD report, so running MOD fixtures for it
    # doubles the bill for zero signal. Narrow to the TDs that really changed (per-repo
    # OR its portfolio counterpart, since both read the same rubric). If the diff names
    # no managed TD at all, keep whatever --td left enabled.
    _touched="$(git -C "${REPO_ROOT}" diff --name-only "${sel_base}...HEAD" 2>/dev/null \
                | grep '^definitions/managed/' || true)"
    if [[ -n "${_touched}" ]]; then
      if ! grep -q 'managed/\(portfolio-\)\?agentic-readiness-analysis/' <<< "${_touched}"; then
        [[ "${run_ara}" == "true" ]] && echo "changed-only: ARA TD untouched → skipping ARA" >&2
        run_ara="false"
      fi
      if ! grep -q 'managed/\(portfolio-\)\?modernization-readiness-analysis/' <<< "${_touched}"; then
        [[ "${run_mod}" == "true" ]] && echo "changed-only: MOD TD untouched → skipping MOD" >&2
        run_mod="false"
      fi
      if [[ "${run_ara}" != "true" && "${run_mod}" != "true" ]]; then
        echo "changed-only: no managed TD matched a known analysis type → keeping both" >&2
        run_ara="true"; run_mod="true"
      fi
    fi
    for _analysis in ara mod; do
      # Only select for analyses we're actually going to run.
      [[ "${_analysis}" == "ara" && "${run_ara}" != "true" ]] && continue
      [[ "${_analysis}" == "mod" && "${run_mod}" != "true" ]] && continue
      _td_dir="${MANAGED}/agentic-readiness-analysis"
      [[ "${_analysis}" == "mod" ]] && _td_dir="${MANAGED}/modernization-readiness-analysis"
      # stdout = fixture paths, stderr = the selector's reasoning (kept in the CI log).
      while IFS= read -r _p; do
        [[ -z "${_p}" ]] && continue
        # de-dupe: ARA and MOD often pick the same fixture
        case " ${selected[*]:-} " in *" ${_p} "*) ;; *) selected+=("${_p}") ;; esac
      done < <(python3 "${HARNESS_DIR}/select-fixtures.py" \
                 --analysis "${_analysis}" --td "${_td_dir}" \
                 --base "${sel_base}" --count "${MR_FIXTURES}")
      # Record WHICH questions the edit touched. The judge needs this to tell in-scope
      # movement (signal) from the analysis agent's run-to-run nondeterminism (noise) —
      # a same-rubric re-run moves 10-20 findings, so on a one-question edit the noise is
      # larger than the signal and the judge otherwise reads it as "far broader than stated".
      python3 "${HARNESS_DIR}/select-fixtures.py" \
        --analysis "${_analysis}" --td "${_td_dir}" --base "${sel_base}" \
        --count "${MR_FIXTURES}" --format json 2>/dev/null \
        | python3 -c 'import json,sys
try: print("\n".join(json.load(sys.stdin).get("changed_questions") or []))
except Exception: pass' >> "${_edited_q_file}" || true
    done
    if [[ ${#selected[@]} -eq 0 ]]; then
      echo "changed-only: selector returned nothing → using the broadest fixture per analysis" >&2
      selected=("${ALL_FIXTURES[0]}")
    else
      echo "changed-only: a watched TD changed → ${#selected[@]} targeted fixture(s); use --scope all for the full sweep" >&2
    fi
  else
    base="${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:+origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}}"
    base="${base:-origin/main}"
    changed_paths=()
    while IFS= read -r line; do
      [[ -n "${line}" ]] && changed_paths+=("${line}")
    done < <(git -C "${REPO_ROOT}" diff --name-only "${base}...HEAD" 2>/dev/null || true)
    # `${changed_paths[@]}` on an EMPTY array is an unbound-variable error under `set -u`
    # in bash 3.2 (macOS) — and an empty diff is exactly what a shallow CI clone produces
    # when the base ref can't be resolved, so this crashed the whole job. Guard the loop.
    if [[ ${#changed_paths[@]} -gt 0 ]]; then
      for fx in "${ALL_FIXTURES[@]}"; do
        for cp in "${changed_paths[@]}"; do
          [[ "${cp}" == "${fx}"* ]] && { selected+=("${fx}"); break; }
        done
      done
    fi
    # No fixture directly changed but the gate said run (e.g. a harness-only change).
    #
    # This used to expand to ALL fixtures, which is what actually blew up on MR !14: the
    # gate's base ref was unresolvable in the shallow CI clone, so HARNESS_CHANGED_TD came
    # out false, we landed HERE, and a harness-only MR launched 22 units / ~2,400 agent-min.
    # `--changed-only` must NEVER silently mean "everything" — an unbounded full sweep is
    # only ever something an operator asks for explicitly (--scope all / harness:full).
    # Cap at --mr-fixtures instead: enough to prove the pipeline works end to end, and if
    # no TD changed there is no rubric delta for extra fixtures to reveal anyway.
    if [[ ${#selected[@]} -eq 0 ]]; then
      _cap="${MR_FIXTURES}"
      [[ "${_cap}" -gt ${#ALL_FIXTURES[@]} ]] && _cap=${#ALL_FIXTURES[@]}
      echo "changed-only: no TD or fixture changed → smoke-running ${_cap} fixture(s)." >&2
      echo "              (no rubric edit ⇒ no delta to find; use --scope all to force a sweep.)" >&2
      selected=()
      for ((_i = 0; _i < _cap; _i++)); do selected+=("${ALL_FIXTURES[$_i]}"); done
    fi
  fi
fi

# Hard ceiling on the changed-only path. Belt-and-braces over the branches above: no
# combination of a bad base ref, a stale should-run.env, or a future edit may turn an MR
# into an unbounded sweep. --scope all is the ONLY way to get every fixture.

# --only restricts to a single fixture by path basename — used to backfill one fixture that
# a transient failure left missing from a batch, and for fast single-fixture re-runs. It is
# an exact match on the fixture's directory name, applied before the changed-only cap so it
# composes with any scope. An unmatched name is a hard error, not a silent empty run.
if [[ -n "${ONLY}" ]]; then
  _only_sel=()
  for _p in "${selected[@]}"; do
    [[ "$(basename "${_p}")" == "${ONLY}" ]] && _only_sel+=("${_p}")
  done
  if [[ ${#_only_sel[@]} -eq 0 ]]; then
    echo "error: --only '${ONLY}' matched no fixture in scope '${SCOPE}'" >&2
    echo "  available: $(printf '%s ' "${selected[@]##*/}")" >&2
    exit 2
  fi
  selected=("${_only_sel[@]}")
fi

if [[ "${SCOPE}" != "all" && ${#selected[@]} -gt "${MR_FIXTURES}" ]]; then
  echo "changed-only: capping ${#selected[@]} selected fixture(s) → ${MR_FIXTURES} (--mr-fixtures)." >&2
  _capped=()
  for ((_i = 0; _i < MR_FIXTURES; _i++)); do _capped+=("${selected[$_i]}"); done
  selected=("${_capped[@]}")
fi

echo "run-fixtures: scope=${SCOPE} ara=${run_ara} mod=${run_mod} fixtures=${#selected[@]} after=${AFTER_DIR} (engine: atx custom def exec)" >&2

# AWS Transform custom-def only resolves in us-east-1 — a stray AWS_REGION (e.g. a shell
# default of us-west-2) makes the endpoint fail. Pin us-east-1 unconditionally unless the
# operator explicitly overrides via HARNESS_AWS_REGION (escape hatch, not the shell env).
export AWS_REGION="${HARNESS_AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="${HARNESS_AWS_REGION:-us-east-1}"

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
  # Newest match. `stat` is NOT portable here and MUST NOT be used: BSD/macOS spells
  # the format flag `stat -f '%m %N'` while on GNU/Linux `-f` means "show FILESYSTEM
  # info", so the CI runner printed "Total: ... Free: ..." (inode stats) instead of a
  # path — which then flowed downstream as a bogus filename:
  #   cp: cannot stat 'Total: 104856560  Free: 104235319'
  #   ara: CONTRACT VIOLATION           <- a portability bug, NOT real contract drift
  # Python's os.path.getmtime is identical on both platforms, and -print0 keeps paths
  # with spaces/newlines intact.
  found="$(find "${search}" -type f -name "${glob}" -print0 2>/dev/null \
           | python3 -c 'import os,sys
paths=[p for p in sys.stdin.buffer.read().split(b"\0") if p]
if paths:
    newest=max(paths, key=lambda p: os.path.getmtime(os.fsdecode(p)))
    sys.stdout.write(os.fsdecode(newest))')"
  if [[ -z "${found}" ]]; then
    echo "warn: no ${glob} emitted (${analysis})" >&2; return 1
  fi
  dest="${AFTER_DIR}/$(basename "${found}")"
  cp -f "${found}" "${dest}"
  echo "collected ${dest}" >&2
  # Backfill the flaky top-level envelope (analysis_type / repo_name) the TD sometimes
  # drops — deterministically, from values the harness already knows (the analysis it ran
  # and the fixture name). This never touches structural fields, so the strict contract
  # check below still catches real drift; it only removes envelope-coin-flip noise.
  # repo_name = report basename minus the trailing "-<ara|mod|...>-report.json".
  local repo_name; repo_name="$(basename "${dest}")"
  repo_name="${repo_name%-report.json}"; repo_name="${repo_name%-${analysis}}"
  python3 "${HARNESS_DIR}/normalize-report.py" "${dest}" \
    --analysis "${analysis}" --repo-name "${repo_name}" || true
  if [[ "${VALIDATE}" == "true" ]]; then
    python3 "${HARNESS_DIR}/validate-contract.py" "${dest}" --analysis "${analysis}" \
      && echo "${analysis}: CONTRACT OK" >&2 \
      || echo "${analysis}: CONTRACT VIOLATION" >&2
  fi
}

# --- refuse to clobber an existing batch ---------------------------------------------
# Reports are collected with `cp` into AFTER_DIR, so re-running with the same --after-dir
# would silently overwrite reports that already cost ~110 agent-min each to produce. A
# multi-run baseline is only meaningful if each batch stays a SEPARATE, intact draw, so an
# accidental re-run must not quietly merge two runs into one directory. Opt in with
# --force to reuse a directory on purpose (e.g. resuming a batch that died part-way).
if [[ "${DRY_RUN}" != "true" && "${FORCE:-false}" != "true" ]]; then
  # `find` on a MISSING dir exits non-zero; under `set -euo pipefail` that killed the whole
  # script here with exit 1 and NO message — the guard below never ran, so a brand-new batch
  # dir (the normal case for a fresh sample) silently produced nothing at all. Create the dir
  # first: the guard only cares whether reports already exist INSIDE it.
  mkdir -p "${AFTER_DIR}"
  _existing="$(find "${AFTER_DIR}" -maxdepth 1 -name '*-report.json' 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${_existing}" -gt 0 ]]; then
    echo "refusing to run: ${AFTER_DIR} already holds ${_existing} report(s)." >&2
    echo "  Each batch must stay a separate draw — overwriting would corrupt the sample." >&2
    echo "  Use a new --after-dir (e.g. harness/samples/s3), or --force to reuse this one." >&2
    exit 2
  fi
fi

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
# Each analysis of each fixture is an independent UNIT — its own stage dir, its own
# `git init`. Two reasons this is load-bearing, not cosmetic:
#
#   1. Isolation. `atx custom def exec` runs git on whatever repo ENCLOSES its -p target
#      (it creates an `atx-result-staging-*` branch and commits the report bundle). Git
#      discovery walks UP until it finds a `.git`; without a local one, atx climbs into
#      OUR repo and hijacks HEAD — and parallel execs fight over that single `.git`. A
#      per-unit `.git` stops discovery at the boundary, so atx stays fully contained and
#      our repo is never touched.
#   2. Max parallelism, safely. The rule is "never two execs in ONE repo" (atx switches
#      branches), NOT "never two execs at once". Because every unit gets its own staged
#      copy + own .git — `_src/ara/X` and `_src/mod/X` are separate repos — ALL units are
#      mutually independent and any of them can run concurrently. So we pour every unit
#      into ONE throttled pool and a MOD unit backfills a slot the moment any ARA unit
#      finishes, with no wave barrier and no per-fixture mutex.
#      assert_unique_unit_dests() enforces the invariant that makes this sound.
#
# The portfolio stage (below) aggregates the per-repo reports, so it runs AFTER the pool
# drains (one barrier). Each exec mostly waits on Bedrock, so pooling is a big win.

# Remember our repo's branch so we can PROVE atx never moved it (belt-and-suspenders on
# top of the per-unit .git isolation above).
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

# Build the flat UNIT list: one entry per (fixture, enabled analysis). Parallel arrays
# (bash 3.2 — no structs), each staged into its own git repo up front.
UNIT_ANALYSIS=(); UNIT_NAME=(); UNIT_DEST=(); UNIT_DEFNAME=(); UNIT_GLOB=()

stage_unit() {
  local analysis="$1" name="$2" defname="$3" glob="$4" target="$5"
  # Analysis goes in a PARENT dir, not the leaf: the TD derives both the report filename
  # and the report's internal `repo_name` from basename(-p dir). A leaf of `${name}-ara`
  # would produce `${name}-ara-ara-report.json` and repo_name `${name}-ara`, breaking
  # golden filename matching AND the portfolio's per-repo rollup. `_src/<analysis>/<name>`
  # keeps the leaf a clean fixture name while still isolating ARA and MOD into separate dirs.
  local dest="${STAGE}/${analysis}/${name}"
  if [[ "${DRY_RUN}" != "true" ]]; then
    mkdir -p "${dest}"
    # Copy contents WITHOUT any nested .git from the source, then init a fresh one.
    cp -RL "${target}/." "${dest}/" 2>/dev/null || cp -R "${target}/." "${dest}/"
    rm -rf "${dest}/.git"
    git_init_stage "${dest}"
  fi
  UNIT_ANALYSIS+=("${analysis}"); UNIT_NAME+=("${name}")
  UNIT_DEST+=("${dest}"); UNIT_DEFNAME+=("${defname}"); UNIT_GLOB+=("${glob}")
}

# Zero fixtures means we'd publish the TDs, analyze nothing, and exit 0 — a GREEN job that
# tested nothing, the worst possible failure mode for a guardrail. Every branch above is
# supposed to pick at least one, so this is a bug, not a valid state: fail loudly.
# (Also avoids the bash 3.2 `set -u` unbound-variable error on an empty array below.)
if [[ ${#selected[@]} -eq 0 ]]; then
  echo "FATAL: no fixtures selected — refusing to report success having analyzed nothing." >&2
  echo "       This is a selection bug; check the base-ref resolution warnings above." >&2
  exit 5
fi

for fx in "${selected[@]}"; do
  name="$(basename "${fx}")"
  target="${REPO_ROOT}/${fx}"
  [[ -e "${target}" ]] || { echo "warn: fixture path missing: ${fx}" >&2; continue; }
  if [[ "${run_ara}" == "true" ]]; then
    stage_unit ara "${name}" "agentic-readiness-analysis${NAME_SUFFIX}" '*-ara-report.json' "${target}"
  fi
  if [[ "${run_mod}" == "true" ]]; then
    stage_unit mod "${name}" "modernization-readiness-analysis${NAME_SUFFIX}" '*-mod-report.json' "${target}"
  fi
done
[[ "${DRY_RUN}" != "true" ]] && mkdir -p "${AFTER_DIR}/_logs"

# Abort the run if our repo's HEAD ever moves (would mean the isolation failed).
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

# atx's progress chatter, as one extended-regex. Every few hundred ms it emits a braille
# spinner frame plus a keepalive line; on the 22-unit run that was 74,660 of 89,459 lines
# (83.5%) and blew GitLab's 4 MB job-log cap after 4 units, truncating the differ/judge.
# Stripped from the per-unit logs at write time (run_unit) — real atx output is kept.
SPINNER_RE='Still here, working on it|agent min|Analyzing output|^[[:space:]]*[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]'

# Block until fewer than JOBS background jobs are running (bash 3.2: no `wait -n`).
wait_for_slot() {
  while [[ "$(jobs -rp | wc -l | tr -d ' ')" -ge "${JOBS}" ]]; do sleep 1; done
}

# --- concurrency invariant ------------------------------------------------------------
# atx SWITCHES BRANCHES in the repo enclosing its -p target (it creates an
# `atx-result-staging-*` branch and commits the report bundle). So two execs must never
# share one repo — they would fight over its .git and HEAD.
#
# We satisfy that STRUCTURALLY rather than with a lock: stage_unit() gives every
# (analysis, fixture) unit its OWN copy of the fixture at `_src/<analysis>/<fixture>`,
# each with its own freshly-`git init`ed .git. `_src/ara/X` and `_src/mod/X` are two
# distinct repos, so even same-fixture ARA and MOD never touch the same .git and are safe
# to run concurrently. No mutex needed — and no lock to leak and hang the pool.
#
# This assert makes the invariant fail LOUDLY if the staging layout is ever changed such
# that two units resolve to the same directory.
assert_unique_unit_dests() {
  local dup
  # Empty array + `set -u` = unbound variable in bash 3.2, so bail early. (Reaching here
  # with zero units also means nothing would run, which the guard above already rejects.)
  [[ ${#UNIT_DEST[@]} -eq 0 ]] && return 0
  dup="$(printf '%s\n' "${UNIT_DEST[@]}" | sort | uniq -d | head -1)"
  if [[ -n "${dup}" ]]; then
    echo "FATAL: two units share a stage dir (${dup}) — concurrent atx execs would" >&2
    echo "       fight over one .git. Fix stage_unit()'s path layout." >&2
    exit 4
  fi
}

# run one (analysis, fixture) unit: exec the def, then collect+validate its report.
# When parallel, atx's verbose output is routed to a per-unit log so the main log stays
# readable; only concise markers go to the shared stderr. Always returns 0 (never trips
# set -e / the `wait` below), since a missing report is a warning, not a fatal error.
run_unit() {
  local analysis="$1" name="$2" dest="$3" defname="$4" glob="$5"
  local label; label="$(echo "${analysis}" | tr '[:lower:]' '[:upper:]')"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "=== ${label}: ${name} ===" >&2
    echo "+ atx custom def exec -n ${defname} -p ${dest} --non-interactive --trust-all-tools --do-not-learn" >&2
    return 0
  fi
  echo "=== ${label}: ${name} ===" >&2
  # atx streams a progress SPINNER ("⠋ Analyzing output...", "Still here, working on
  # it...", "~N agent min") every few hundred ms. That is 83% of the output and it blew
  # GitLab's 4 MB job-log cap after only 4 of 22 units, which cut off the differ/judge
  # entirely ("Job's log exceeded limit of 4194304 bytes"). So atx's full output ALWAYS
  # goes to a per-unit file (kept as a CI artifact for debugging) and never to the job
  # log; only our own concise markers reach stderr.
  # The spinner is also 83% of the FILE, which would make the artifact as unreadable as
  # the job log was (and ~4 MB per unit on disk). Filter it out as it streams, so the
  # kept log is only real atx output. `grep --line-buffered -v` keeps this streaming
  # (no buffering until exit) and PIPESTATUS preserves atx's own exit code.
  local ulog="${AFTER_DIR}/_logs/${name}-${analysis}.log"
  set +e
  atx custom def exec -n "${defname}" -p "${dest}" \
    --non-interactive --trust-all-tools --do-not-learn 2>&1 \
    | grep --line-buffered -vE "${SPINNER_RE}" > "${ulog}"
  local rc=${PIPESTATUS[0]}
  set -e
  [[ ${rc} -ne 0 ]] && echo "warn: ${analysis} exec failed for ${name} (rc=${rc}, see ${ulog})" >&2
  # Surface the tail on failure so a broken exec is still diagnosable from the job log.
  if ! grep -q "${glob#\*}" "${ulog}" 2>/dev/null; then
    echo "  (${analysis}/${name}: no report marker in atx output — last lines:)" >&2
    tail -8 "${ulog}" 2>/dev/null | sed 's/^/    /' >&2 || true
  fi
  collect_report "${dest}" "${glob}" "${analysis}" || true
  return 0
}

# --- run the whole pool: ALL units (ARA+MOD interleaved), throttled to JOBS, one barrier
echo "" >&2
assert_unique_unit_dests
# Name the analyses actually in the pool. The label used to be a hardcoded "ARA+MOD
# interleaved" even when one analysis had been skipped — misleading in exactly the line an
# operator reads to confirm the run was scoped correctly.
_pool_kinds=""
[[ "${run_ara}" == "true" ]] && _pool_kinds="ARA"
[[ "${run_mod}" == "true" ]] && _pool_kinds="${_pool_kinds:+${_pool_kinds}+}MOD"
echo "--- pool: ${#UNIT_NAME[@]} unit(s) (${_pool_kinds:-none}), jobs=${JOBS} ---" >&2
for ((u = 0; u < ${#UNIT_NAME[@]}; u++)); do
  if [[ "${JOBS}" -gt 1 ]]; then
    wait_for_slot
    run_unit "${UNIT_ANALYSIS[$u]}" "${UNIT_NAME[$u]}" "${UNIT_DEST[$u]}" \
             "${UNIT_DEFNAME[$u]}" "${UNIT_GLOB[$u]}" &
  else
    run_unit "${UNIT_ANALYSIS[$u]}" "${UNIT_NAME[$u]}" "${UNIT_DEST[$u]}" \
             "${UNIT_DEFNAME[$u]}" "${UNIT_GLOB[$u]}"
  fi
done
[[ "${JOBS}" -gt 1 ]] && wait || true
assert_repo_head

# --- Stage 2: portfolio ARA + MOD -----------------------------------------------------
# The portfolio TDs aggregate the per-repo reports Stage 1 collected. Stage those into a
# portfolio input dir (its OWN git repo, same isolation as Stage 1) and exec the portfolio
# TD against it, passing portfolio_name via additionalPlanContext.
# WHEN it runs (§ "only when needed"): the portfolio TDs aggregate per-repo reports, so
#   (a) they need >=2 per-repo reports — a rollup over ONE repo tells you nothing about
#       rollup behaviour, and
#   (b) on an MR they are only worth their cost if a PORTFOLIO TD actually changed
#       (HARNESS_CHANGED_PORTFOLIO_TD from should-run.sh). A per-repo-only rubric edit is
#       fully judged by the per-repo delta.
# --scope all always runs them (that's a re-baseline); --no-portfolio always skips.
run_portfolio="${NO_PORTFOLIO:+false}"
if [[ "${NO_PORTFOLIO}" == "true" ]]; then
  run_portfolio="false"
elif [[ "${SCOPE}" == "all" ]]; then
  run_portfolio="true"
elif [[ "${HARNESS_CHANGED_PORTFOLIO_TD:-false}" == "true" ]]; then
  run_portfolio="true"
else
  run_portfolio="false"
  echo "portfolio: SKIPPED — no portfolio TD changed (per-repo delta is sufficient);" >&2
  echo "           use --scope all or edit a portfolio TD to exercise the rollup." >&2
fi

# Guard (a): a portfolio rollup needs at least 2 per-repo reports to be meaningful.
if [[ "${run_portfolio}" == "true" && "${DRY_RUN}" != "true" ]]; then
  _n_repo_reports="$(find "${AFTER_DIR}" -maxdepth 1 -name '*-report.json' \
                       ! -name '*portfolio*' 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${_n_repo_reports}" -lt 2 ]]; then
    run_portfolio="false"
    echo "portfolio: SKIPPED — only ${_n_repo_reports} per-repo report(s); a rollup needs >=2." >&2
    echo "           (raise --mr-fixtures, or use --scope all.)" >&2
  fi
fi

if [[ "${run_portfolio}" == "true" ]]; then
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

# --- hand the edit scope to the judge ------------------------------------------------
# The judge weighs movement on these questions as signal and everything else as run-to-run
# noise. Written as a file (not stdout) because stdout here is human-facing progress.
if [[ -s "${_edited_q_file}" ]]; then
  mkdir -p "${AFTER_DIR}"
  sort -u "${_edited_q_file}" | paste -sd, - > "${AFTER_DIR}/edited-questions.txt"
  echo "edit scope: $(cat "${AFTER_DIR}/edited-questions.txt") → ${AFTER_DIR}/edited-questions.txt" >&2
fi

echo "done." >&2
