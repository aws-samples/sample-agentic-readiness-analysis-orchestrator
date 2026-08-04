#!/usr/bin/env bash
#
# LIVE DEMO — Act 2: "the agent fixes it"
#
# Runs the containerize-service TD against one repo and shows the generated container baseline.
#
# TWO EXECUTION PATHS. Both verified 2026-08-04 against legacy-storefront-rails:
#
#   ct    (default) — `atx ct remediation create` in direct-TD mode (--transformation-name + --repo,
#                     no findings needed). The documented path: visible in the Console's
#                     Remediations tab, commits to a branch (atx/<td>-<timestamp>). ~4 min.
#                     REQUIRES the TD published in the AWS-credentials namespace — see below.
#   exec  (opt-in)  — `atx custom def exec`. Same TD against the working tree, no registry
#                     round-trip, no Console record, changes left uncommitted. ~5-10 min.
#
# The registry is tenanted by authentication mode: two namespaces behind one endpoint. The ct
# remediation worker only reads the AWS-credentials one, so a TD published the other way is a 404
# there even though `custom def get` confirms it. publish-td.sh defaults to MIDWAY=false to keep
# both sides in the same namespace.
#
# You can also ask Claude: "containerize legacy-storefront-rails"
#
# Usage:
#   ./demo-scripts/03-remediate.sh                            # ct path, default repo
#   ./demo-scripts/03-remediate.sh legacy-loan-calculator
#   ./demo-scripts/03-remediate.sh --path exec                # local fallback, no Console record
#
set -uo pipefail

PATH_MODE="ct"
REPO=""
TD_OVERRIDE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --path) PATH_MODE="${2:-}"; shift 2 ;;
    --td)   TD_OVERRIDE="${2:-}"; shift 2 ;;
    --remote) PATH_MODE="ct"; shift ;;   # back-compat: remote implied the ct path
    -*) echo "!! unknown flag: $1"; exit 1 ;;
    *)  REPO="$1"; shift ;;
  esac
done
case "$PATH_MODE" in
  exec|ct) ;;
  *) echo "!! --path must be 'exec' or 'ct'"; exit 1 ;;
esac

SOURCE="mig-mod-demo"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORTFOLIO_DIR="$PROJECT_DIR/harness/fixtures/portfolio"

REMED_TD="${TD_OVERRIDE:-containerize-service}"
REMED_TD_DIR="$PROJECT_DIR/definitions/custom/containerize-service"

# Default target must LACK a Dockerfile, or this additive TD correctly does nothing.
# legacy-shipping-api and legacy-pricing-cgi already ship Dockerfile + k8s/.
REPO="${REPO:-legacy-storefront-rails}"
REPO_DIR="$PORTFOLIO_DIR/$REPO"

export AWS_REGION=us-east-1

echo "==> Containerize: $REMED_TD on $REPO  (path: $PATH_MODE)"
echo

# --- Pre-flight ---
[ -d "$REPO_DIR/.git" ] || { echo "!! $REPO_DIR is not a git repo — run 00-full-setup.sh first"; exit 1; }

if [ -f "$REPO_DIR/Dockerfile" ]; then
  echo "    note: $REPO already has a Dockerfile. This TD is additive and skips existing"
  echo "          artifacts, so expect little or no change. Pick a repo without one."
  echo
fi

# The TD must resolve in the AWS-credentials namespace — the one the ct remediation worker reads.
# MIDWAY=false is what makes this probe authoritative: without it `get` may query the other
# namespace and pass for a TD remediation cannot see. Use `get` rather than grepping
# `custom def list`, which wraps names across lines and invites substring false positives.
td_probe=$(cd "$(mktemp -d)" && MIDWAY=false atx custom def get -n "$REMED_TD" </dev/null 2>&1)
if printf '%s' "$td_probe" | grep -qi "not found"; then
  echo "!! TD '$REMED_TD' does not resolve in the AWS-credentials namespace. Publish it:"
  echo "     ./scripts/publish-td.sh $REMED_TD_DIR"
  echo "   (publish-td.sh pins MIDWAY=false; a TD published in the other namespace is invisible"
  echo "    here and must be re-published — publishing one does not backfill the other.)"
  exit 1
fi
echo "    TD '$REMED_TD' resolves (AWS-credentials namespace)."

# The worktree must be clean. A repo that was just analyzed IS dirty (ct writes its report bundle
# into the working tree), and these paths either refuse to run or bury the demo diff in noise.
if [ -n "$(git -C "$REPO_DIR" status --porcelain 2>/dev/null)" ]; then
  echo "    Worktree dirty (analysis artifacts) — clearing regenerable output..."
  rm -rf "$REPO_DIR/services" 2>/dev/null
  git -C "$REPO_DIR" clean -fd >/dev/null 2>&1
  git -C "$REPO_DIR" checkout -- . >/dev/null 2>&1
fi
if [ -n "$(git -C "$REPO_DIR" status --porcelain 2>/dev/null)" ]; then
  echo "!! $REPO_DIR still has uncommitted changes:"
  git -C "$REPO_DIR" status --short | sed 's/^/       /'
  exit 1
fi
echo "    worktree clean."
BASE_BRANCH=$(git -C "$REPO_DIR" branch --show-current 2>/dev/null)
BASE_COMMIT=$(git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null)
echo

# --- Run ---
if [ "$PATH_MODE" = "exec" ]; then
  echo "==> Running: atx custom def exec -n $REMED_TD  (~5-10 min of agent time)"
  atx custom def exec -n "$REMED_TD" -p "$REPO_DIR" -x -t </dev/null 2>&1 | tail -18
  echo
  echo "==> Result (working tree)"
  changed=$(git -C "$REPO_DIR" status --porcelain 2>/dev/null)
  if [ -z "$changed" ]; then
    echo "    No changes. For an additive TD that means every target artifact already existed."
    echo "    Check: ls $REPO_DIR"
    exit 0
  fi
  echo "    Files generated:"
  printf '%s\n' "$changed" | sed 's/^/      /'
  echo
  echo "    Show the full diff on screen with:"
  echo "      git -C $REPO_DIR diff"
  echo "      git -C $REPO_DIR status --short"
  echo
  echo "    (Uncommitted on '$BASE_BRANCH'. Reset with: git -C $REPO_DIR checkout -- . && git -C $REPO_DIR clean -fd)"
else
  echo "==> Running: atx ct remediation create --transformation-name $REMED_TD --local"
  echo "    Direct-TD mode: needs no findings, appears in the Console's Remediations tab,"
  echo "    and commits to a branch. ~4 min."
  REMED_OUT=$(atx ct remediation create \
    --repo "$SOURCE::$REPO" --source "$SOURCE" \
    --transformation-name "$REMED_TD" --name "containerize-$REPO" --local </dev/null 2>&1)
  printf '%s\n' "$REMED_OUT" | tail -12 | sed 's/^/    /'

  REMED_ID=$(printf '%s' "$REMED_OUT" | grep -oE '01[A-Z0-9]{24}' | head -1)
  [ -n "$REMED_ID" ] || { echo "!! could not parse a remediation id"; exit 1; }
  echo

  # Remediation has no report_paths to cross-check, so status IS the terminal signal here
  # (unlike `analysis`, where it is not).
  echo "==> Polling $REMED_ID"
  deadline=$(( $(date +%s) + 20 * 60 ))
  while :; do
    st=$(atx ct remediation status --id "$REMED_ID" --json 2>/dev/null | jq -r '.status // "unknown"' 2>/dev/null)
    st="${st:-unknown}"
    case "$st" in completed|pr_open|failed|cancelled) break ;; esac
    echo "    $st ($(date +%H:%M:%S))"
    [ "$(date +%s)" -ge "$deadline" ] && { echo "!! timed out (status=$st)"; break; }
    sleep 20
  done
  echo "    terminal status: $st"
  echo

  if [ "$st" = "failed" ]; then
    atx ct remediation status --id "$REMED_ID" --json 2>/dev/null \
      | jq -r '(.repos // {}) | to_entries[] | "    \(.key): \(.value.error // "no error")"' 2>/dev/null | head -8
    echo
    echo "    'not found in the registry' here means the TD isn't in the AWS-credentials namespace"
    echo "    that this worker reads. Re-publish, then retry:"
    echo "      ./scripts/publish-td.sh $REMED_TD_DIR   # defaults to MIDWAY=false"
    echo "    Local fallback that skips the registry entirely: --path exec"
    exit 1
  fi

  BRANCH=$(git -C "$REPO_DIR" for-each-ref --sort=-creatordate \
             --format='%(refname:short)' 'refs/heads/atx*' 2>/dev/null | head -1)
  if [ -n "$BRANCH" ]; then
    echo "==> Branch: $BRANCH"
    git -C "$REPO_DIR" diff --stat "$BASE_COMMIT...$BRANCH" 2>/dev/null | sed 's/^/      /'
    echo
    echo "    Full diff: git -C $REPO_DIR diff $BASE_BRANCH...$BRANCH"
  else
    echo "    Completed, but no atx* branch found — the TD may have made no change."
  fi
fi
echo
echo "==> Done."
