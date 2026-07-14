#!/usr/bin/env bash
#
# DEMO HARNESS — Full Reset
#
# Tears down the ENTIRE demo environment so you can start fresh.
# Supports both local and remote modes.
#
# Usage:
#   ./demo-scripts/99-full-reset.sh           # local mode (default)
#   ./demo-scripts/99-full-reset.sh --remote  # also clean GitHub repos
#
set -uo pipefail

MODE="local"
[ "${1:-}" = "--remote" ] && MODE="remote"

ORG="YOUR-GITHUB-ORG"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORTFOLIO_DIR="$PROJECT_DIR/sample-legacy-portfolio"
LOCAL_STAGED_DIR="$PROJECT_DIR/.local-source"
REPORTS_DIR="$PROJECT_DIR/reports"

export AWS_REGION=us-east-1

echo "============================================"
echo "  DEMO HARNESS — Full Reset ($MODE)"
echo "  $(date)"
echo "============================================"
echo
echo "  This will destroy ALL demo state."
echo "  Press Ctrl+C within 5 seconds to abort."
sleep 5
echo

# --- Ensure ct server is running ---
if [ "$(atx ct status --health 2>/dev/null)" != "healthy" ]; then
  echo "==> Starting ct server..."
  pkill -f "atx ct server" 2>/dev/null || true
  sleep 2
  PYENV_VERSION=system AWS_REGION=us-east-1 atx ct server >/dev/null 2>&1 &
  for i in $(seq 1 15); do
    [ "$(atx ct status --health 2>/dev/null)" = "healthy" ] && break
    sleep 2
  done
fi
echo "==> ct server: $(atx ct status --health 2>/dev/null)"
echo

# --- Step 1: Delete all analyses (cascades findings) ---
echo "==> [1/5] Deleting analyses + findings"
n=0
for id in $(atx ct analysis list --json 2>/dev/null | jq -r '.[].id' 2>/dev/null); do
  [ -z "$id" ] && continue
  atx ct analysis delete --id "$id" --cascade-findings >/dev/null 2>&1 </dev/null && n=$((n+1))
done
echo "    Deleted $n analyses."
echo

# --- Step 2: Delete all repos from ct ---
echo "==> [2/5] Deleting repos from ct"
repo_lines=$(atx ct repository list --json 2>/dev/null | jq -r '.items[] | "\(.slug)\t\(.source)"' 2>/dev/null)
while IFS=$'\t' read -r slug src; do
  [ -z "$slug" ] && continue
  atx ct repository delete --repo "$slug" --source "$src" >/dev/null 2>&1 </dev/null && echo "    del $slug"
done <<< "$repo_lines"
echo

# --- Step 3: Clean findings + remediations + sources ---
echo "==> [3/5] Cleaning residual findings, remediations, sources"
# Dismiss open findings (use single-update — batch-update has UnknownError on some IDs)
for id in $(atx ct findings list --status open --json 2>/dev/null | jq -r '.[].id' 2>/dev/null); do
  [ -z "$id" ] && continue
  atx ct findings update --id "$id" --status dismissed --reason "full reset" >/dev/null 2>&1 </dev/null
done

# Delete all findings
for id in $(atx ct findings list --json 2>/dev/null | jq -r '.[].id' 2>/dev/null); do
  [ -z "$id" ] && continue
  atx ct findings delete --id "$id" >/dev/null 2>&1 </dev/null
done

# Delete remediations
for id in $(atx ct remediation list --json 2>/dev/null | jq -r '.[].id' 2>/dev/null); do
  [ -z "$id" ] && continue
  atx ct remediation delete --id "$id" >/dev/null 2>&1 </dev/null
done

# Remove sources
for name in $(atx ct source list --json 2>/dev/null | jq -r '.[].source' 2>/dev/null); do
  [ -z "$name" ] && continue
  atx ct source remove --name "$name" >/dev/null 2>&1 </dev/null && echo "    removed source $name"
done
echo

# --- Step 4: Clean GitHub repos (remote mode only) ---
echo "==> [4/5] Cleaning GitHub repos"
if [ "$MODE" = "remote" ]; then
  if gh auth status 2>&1 | grep -q "delete_repo"; then
    for r in legacy-shipping-api legacy-storefront-rails legacy-loan-calculator legacy-pricing-cgi; do
      if gh repo view "$ORG/$r" >/dev/null 2>&1; then
        gh repo delete "$ORG/$r" --yes 2>&1 && echo "    deleted $ORG/$r"
      fi
    done
  else
    echo "    SKIPPED — token lacks 'delete_repo' scope."
    echo "    Run: gh auth refresh --hostname github.com -s delete_repo"
  fi
else
  echo "    SKIPPED (local mode — no GitHub repos to clean)"
fi
echo

# --- Step 5: Clean local state ---
echo "==> [5/5] Cleaning local state"
# Remove staged dir
rm -rf "$LOCAL_STAGED_DIR"
echo "    Removed .local-source/"

# Remove remotes + analysis artifacts + staging branches from local clones
for d in "$PORTFOLIO_DIR"/legacy-*; do
  [ -d "$d/.git" ] || continue
  git -C "$d" remote remove origin 2>/dev/null || true
  rm -rf "$d/services" 2>/dev/null
  # Reset to main if on a staging branch
  current=$(git -C "$d" branch --show-current 2>/dev/null)
  if [ "$current" != "main" ] && git -C "$d" rev-parse --verify main >/dev/null 2>&1; then
    git -C "$d" checkout main >/dev/null 2>&1
  fi
  # Delete staging branches
  git -C "$d" branch 2>/dev/null | grep "atx-result-staging" | while read -r br; do
    git -C "$d" branch -D "$(echo "$br" | tr -d ' *')" >/dev/null 2>&1
  done
done
echo "    Cleared git remotes, analysis artifacts, and staging branches."

# Remove exported reports
rm -rf "$REPORTS_DIR"
echo "    Removed reports/"

# Clean up atxct working copies
rm -rf ~/.atxct/sources/mig-mod-demo 2>/dev/null
echo "    Cleaned ~/.atxct/sources/mig-mod-demo"
echo

# --- Final verification (with retry sweep) ---
verify_counts() {
  SRC_N=$(atx ct source list --json 2>/dev/null | jq 'length' 2>/dev/null)
  REPO_N=$(atx ct repository list --json 2>/dev/null | jq '.total' 2>/dev/null)
  AN_N=$(atx ct analysis list --json 2>/dev/null | jq 'length' 2>/dev/null)
  FND_N=$(atx ct findings list --json 2>/dev/null | jq 'length' 2>/dev/null)
}
verify_counts

if [ "${REPO_N:-0}" != "0" ] || [ "${SRC_N:-0}" != "0" ] || [ "${FND_N:-0}" != "0" ]; then
  echo "==> Residuals detected — sweep pass 2"
  repo_lines=$(atx ct repository list --json 2>/dev/null | jq -r '.items[] | "\(.slug)\t\(.source)"' 2>/dev/null)
  while IFS=$'\t' read -r slug src; do
    [ -z "$slug" ] && continue
    atx ct repository delete --repo "$slug" --source "$src" >/dev/null 2>&1 </dev/null && echo "    del $slug"
  done <<< "$repo_lines"
  for id in $(atx ct findings list --status open --json 2>/dev/null | jq -r '.[].id' 2>/dev/null); do
    [ -z "$id" ] && continue
    atx ct findings update --id "$id" --status dismissed --reason "full reset" >/dev/null 2>&1 </dev/null
  done
  for id in $(atx ct findings list --json 2>/dev/null | jq -r '.[].id' 2>/dev/null); do
    [ -z "$id" ] && continue
    atx ct findings delete --id "$id" >/dev/null 2>&1 </dev/null
  done
  for name in $(atx ct source list --json 2>/dev/null | jq -r '.[].source' 2>/dev/null); do
    atx ct source remove --name "$name" >/dev/null 2>&1 </dev/null && echo "    removed source $name"
  done
  verify_counts
fi

echo "==> Final state:"
echo "    ct sources:   ${SRC_N:-0}"
echo "    ct repos:     ${REPO_N:-0}"
echo "    ct analyses:  ${AN_N:-0}"
echo "    ct findings:  ${FND_N:-0}"
if [ "${SRC_N:-0}" != "0" ] || [ "${REPO_N:-0}" != "0" ] || [ "${AN_N:-0}" != "0" ] || [ "${FND_N:-0}" != "0" ]; then
  echo "    ⚠️  WARNING: reset incomplete — re-run this script."
fi
echo
echo "============================================"
echo "  RESET COMPLETE"
echo "============================================"
echo
echo "To set up again:"
if [ "$MODE" = "local" ]; then
  echo "  ./demo-scripts/00-full-setup.sh"
else
  echo "  1. ./demo-scripts/00-push-repos.sh"
  echo "  2. ./demo-scripts/00-full-setup.sh --remote"
fi
echo
