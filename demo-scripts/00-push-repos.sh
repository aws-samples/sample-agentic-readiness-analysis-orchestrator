#!/usr/bin/env bash
#
# DEMO HARNESS — Push pre-baked repos to the GitHub org
#
# Run this from YOUR terminal (Code Defender blocks the agent from pushing).
# Pushes the 3 pre-baked repos. Does NOT push pricing-cgi (held back for live).
#
# Usage:
#   ./demo-scripts/00-push-repos.sh
#
set -uo pipefail

ORG="YOUR-GITHUB-ORG"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORTFOLIO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/sample-legacy-portfolio"

REPOS=(legacy-shipping-api legacy-storefront-rails legacy-loan-calculator)

echo "==> Pushing ${#REPOS[@]} pre-baked repos to $ORG"
echo "    (pricing-cgi is held back for live discovery)"
echo

for r in "${REPOS[@]}"; do
  echo "--- $r ---"
  cd "$PORTFOLIO_DIR/$r"

  # Create repo in org (idempotent)
  if gh repo view "$ORG/$r" >/dev/null 2>&1; then
    echo "  repo exists"
  else
    gh repo create "$ORG/$r" --public \
      --description "Legacy service for mig/mod demo — pre-modernization baseline" \
      || { echo "!! create failed for $r"; continue; }
  fi

  # Wire remote and push
  git remote remove origin 2>/dev/null || true
  git remote add origin "git@github.com:$ORG/$r.git"
  git push --no-verify -u origin main || { echo "!! push failed for $r"; continue; }
  echo "  pushed."
  echo
done

echo "==> Done. All 3 pre-baked repos are live in $ORG."
echo "==> Next: run ./demo-scripts/00-full-setup.sh"
