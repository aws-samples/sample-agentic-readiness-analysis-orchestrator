#!/usr/bin/env bash
#
# LIVE DEMO — Act 1: "a new service appears in the portfolio"
#
# LOCAL mode (default): pricing-cgi is already on disk — just re-run discovery.
#   This script does that for you, or you can ask Claude: "run discovery"
#
# REMOTE mode: creates the repo in the GitHub org and pushes, then discovery.
#   Run from YOUR terminal (Code Defender blocks agent pushes).
#
# Usage:
#   ./demo-scripts/01-live-discovery-push.sh           # local (just re-discover)
#   ./demo-scripts/01-live-discovery-push.sh --remote  # github push + discover
#
set -uo pipefail

MODE="local"
[ "${1:-}" = "--remote" ] && MODE="remote"

ORG="YOUR-GITHUB-ORG"
REPO="legacy-pricing-cgi"
SOURCE="mig-mod-demo"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORTFOLIO_DIR="$PROJECT_DIR/sample-legacy-portfolio"

echo "==> Live Discovery ($MODE mode): $REPO"

if [ "$MODE" = "local" ]; then
  # In local mode, pricing-cgi is already in the portfolio dir on disk.
  # Discovery re-scans the full dir; we then trim back to only keep the repos we care about.
  KEEP_REPOS=(legacy-shipping-api legacy-storefront-rails legacy-loan-calculator "$REPO")

  echo "    Re-scanning source..."
  atx ct discovery scan --source "$SOURCE" 2>&1 | tail -12
  echo

  # Trim: remove everything not in KEEP_REPOS
  while IFS= read -r slug; do
    [ -z "$slug" ] && continue
    repo_name="${slug##*::}"
    keep=false
    for r in "${KEEP_REPOS[@]}"; do [ "$repo_name" = "$r" ] && keep=true && break; done
    [ "$keep" = "false" ] && atx ct repository delete --repo "$slug" --source "$SOURCE" >/dev/null 2>&1 </dev/null
  done < <(atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq -r '.items[].slug' 2>/dev/null)

  # Verify
  if atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq -r '.items[].slug' 2>/dev/null | grep -q "$REPO"; then
    echo "==> SUCCESS: $REPO discovered!"
    echo "    Total repos now: $(atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq '.total')"
  else
    echo "!! $REPO was NOT discovered — check that it exists in portfolio dir"
    exit 1
  fi

else
  # Remote mode: create repo and push
  SRC_DIR="$PORTFOLIO_DIR/$REPO"
  cd "$SRC_DIR" || { echo "!! source dir not found"; exit 1; }

  if gh repo view "$ORG/$REPO" >/dev/null 2>&1; then
    echo "    Repo already exists in org."
  else
    echo "    Creating repo in org..."
    gh repo create "$ORG/$REPO" --public \
      --description "Legacy C++ CGI pricing service — pre-modernization baseline" \
      || { echo "!! repo create failed"; exit 1; }
  fi

  git remote remove origin 2>/dev/null || true
  git remote add origin "git@github.com:$ORG/$REPO.git"
  echo "    Pushing main..."
  git push --no-verify -u origin main || { echo "!! push failed"; exit 1; }

  echo "    Running discovery..."
  atx ct discovery scan --source "$SOURCE" 2>&1 | tail -8
  echo
  echo "==> Done. $ORG/$REPO is live and discovered."
fi
