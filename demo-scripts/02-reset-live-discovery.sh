#!/usr/bin/env bash
#
# LIVE DEMO — Reset the live-discovery beat for rehearsal.
#
# Removes pricing-cgi from ct (and its findings) so discovery will "find" it again.
#
# Usage:
#   ./demo-scripts/02-reset-live-discovery.sh           # local
#   ./demo-scripts/02-reset-live-discovery.sh --remote  # also deletes GitHub repo
#
set -uo pipefail

MODE="local"
[ "${1:-}" = "--remote" ] && MODE="remote"

ORG="YOUR-GITHUB-ORG"
REPO="legacy-pricing-cgi"
SOURCE="mig-mod-demo"
SLUG="${SOURCE}::${REPO}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORTFOLIO_DIR="$PROJECT_DIR/sample-legacy-portfolio"

echo "==> Resetting live-discovery for $REPO ($MODE mode)"

# 1) Remove pricing-cgi findings from ct
echo "--> ct: purging findings for $SLUG"
open_ids=$(atx ct findings list --repo "$SLUG" --status open --json 2>/dev/null | jq -r '.[].id' 2>/dev/null | paste -sd, -)
if [ -n "$open_ids" ]; then
  atx ct findings batch-update --ids "$open_ids" --status dismissed --reason "reset" >/dev/null 2>&1 || true
fi
for id in $(atx ct findings list --repo "$SLUG" --json 2>/dev/null | jq -r '.[].id' 2>/dev/null); do
  [ -z "$id" ] && continue
  atx ct findings delete --id "$id" >/dev/null 2>&1 || true
done

# 2) Remove the repo entry from ct
echo "--> ct: removing repo $SLUG"
atx ct repository delete --repo "$SLUG" --source "$SOURCE" >/dev/null 2>&1 \
  && echo "    removed from ct" \
  || echo "    not present in ct (already clean)"

# 3) Remote-mode: also delete GitHub repo
if [ "$MODE" = "remote" ]; then
  if gh auth status 2>&1 | grep -q "delete_repo"; then
    if gh repo view "$ORG/$REPO" >/dev/null 2>&1; then
      echo "--> github: deleting $ORG/$REPO"
      gh repo delete "$ORG/$REPO" --yes && echo "    deleted"
    fi
  else
    echo "--> github: SKIP delete — token lacks 'delete_repo' scope."
  fi
  git -C "$PORTFOLIO_DIR/$REPO" remote remove origin 2>/dev/null || true
fi

# 4) Report
echo
echo "==> Reset complete."
echo "    ct repos: $(atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq '.total')"
echo
echo "==> Ready to rehearse: ./demo-scripts/01-live-discovery-push.sh$([ "$MODE" = "remote" ] && echo ' --remote')"
