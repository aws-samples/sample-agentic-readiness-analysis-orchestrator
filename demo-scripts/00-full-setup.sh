#!/usr/bin/env bash
#
# DEMO HARNESS — Full Setup
#
# Brings up the entire pre-baked demo environment from scratch.
# Supports two modes:
#   LOCAL  (default) — uses the portfolio dir on disk. No push, no Code Defender,
#                      no GitHub. Remediation creates local branches. Fast, reliable.
#   REMOTE (opt-in)  — GitHub org as source. Remediation opens PRs.
#                      Needs: gh auth + self-attest + repo push.
#
# Usage:
#   ./demo-scripts/00-full-setup.sh           # local mode (default)
#   ./demo-scripts/00-full-setup.sh --remote  # github mode
#
# Timeline: ~30-45 min (ARA + MODA are the long pole)
#
set -uo pipefail

MODE="local"
[ "${1:-}" = "--remote" ] && MODE="remote"

ORG="YOUR-GITHUB-ORG"
SOURCE="mig-mod-demo"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORTFOLIO_DIR="$PROJECT_DIR/sample-legacy-portfolio"
REPORTS_DIR="$PROJECT_DIR/reports"

# Pre-baked repos (analyzed) vs held-back (live discovery star)
PRE_BAKED_REPOS=(legacy-shipping-api legacy-storefront-rails legacy-loan-calculator)
LIVE_REPO="legacy-pricing-cgi"

export AWS_REGION=us-east-1

echo "============================================"
echo "  DEMO HARNESS — Full Setup ($MODE mode)"
echo "  $(date)"
echo "============================================"
echo

# --- Step 0: Pre-flight ---
echo "==> [0/7] Pre-flight checks"
aws sts get-caller-identity >/dev/null 2>&1 || { echo "!! AWS creds not active"; exit 1; }
atx --version >/dev/null 2>&1 || { echo "!! atx CLI not found"; exit 1; }

if [ "$MODE" = "remote" ]; then
  gh auth status >/dev/null 2>&1 || { echo "!! gh not authenticated"; exit 1; }
  for r in "${PRE_BAKED_REPOS[@]}"; do
    if ! gh repo view "$ORG/$r" --json isEmpty -q '.isEmpty' 2>/dev/null | grep -q false; then
      echo "!! $ORG/$r is empty or missing — run 00-push-repos.sh first"; exit 1
    fi
  done
  # Code Defender self-attest
  echo "    Self-attesting repos with Code Defender..."
  for r in "${PRE_BAKED_REPOS[@]}" "$LIVE_REPO"; do
    git-defender self-attest --reason 1 --url "https://github.com/$ORG/$r.git" >/dev/null 2>&1 || true
  done
fi

if [ "$MODE" = "local" ]; then
  [ -d "$PORTFOLIO_DIR" ] || { echo "!! Portfolio dir not found: $PORTFOLIO_DIR"; exit 1; }
  # Fresh clones of the harness ship the portfolio WITHOUT nested .git dirs
  # (they can't live inside the parent repo). ct discovery scans for .git
  # subdirs, so init any repo that's missing one.
  for d in "$PORTFOLIO_DIR"/*/; do
    d="${d%/}"
    [ -d "$d/.git" ] && continue
    echo "    Initializing git in $(basename "$d")..."
    git -C "$d" init -b main >/dev/null 2>&1
    git -C "$d" add -A >/dev/null 2>&1
    git -C "$d" -c user.name="demo-harness" -c user.email="demo@harness.local" \
      commit -m "Initial commit - legacy application source" >/dev/null 2>&1
  done
fi

echo "    All pre-flight checks passed."
echo

# --- Step 1: Start ct server ---
echo "==> [1/7] Starting ct server (us-east-1, system python)"
if [ "$(atx ct status --health 2>/dev/null)" = "healthy" ]; then
  echo "    Already running and healthy."
else
  pkill -f "atx ct server" 2>/dev/null || true
  sleep 2
  PYENV_VERSION=system AWS_REGION=us-east-1 atx ct server >/dev/null 2>&1 &
  CT_PID=$!
  echo "    Started (pid $CT_PID). Waiting for healthy..."
  for i in $(seq 1 20); do
    [ "$(atx ct status --health 2>/dev/null)" = "healthy" ] && break
    sleep 2
  done
  if [ "$(atx ct status --health 2>/dev/null)" != "healthy" ]; then
    echo "!! ct server failed to start"; exit 1
  fi
  echo "    Healthy."
fi
echo

# --- Step 2: Add source ---
echo "==> [2/7] Adding source '$SOURCE' ($MODE)"
if atx ct source list --json 2>/dev/null | jq -r '.[].source' 2>/dev/null | grep -qx "$SOURCE"; then
  echo "    Source already exists."
else
  if [ "$MODE" = "local" ]; then
    atx ct source add --name "$SOURCE" --provider local --path "$PORTFOLIO_DIR" 2>&1
  else
    GH_TOKEN=$(gh auth token 2>/dev/null)
    atx ct source add --name "$SOURCE" --provider github --org "$ORG" --token "$GH_TOKEN" 2>&1
  fi
fi
echo

# --- Step 3: Discovery + trim to pre-baked set ---
echo "==> [3/7] Running discovery"
atx ct discovery scan --source "$SOURCE" 2>&1 | tail -12

REPO_COUNT=$(atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq '.total' 2>/dev/null)
echo "    Discovered $REPO_COUNT repos total."

# Remove all repos NOT in the pre-baked set (keep only the 3 we want analyzed)
echo "    Trimming to pre-baked set (${PRE_BAKED_REPOS[*]})..."
# Build a list of slugs to delete (must collect first — atx eats stdin in loops)
slugs_to_delete=()
while IFS= read -r slug; do
  [ -z "$slug" ] && continue
  repo_name="${slug##*::}"
  keep=false
  for r in "${PRE_BAKED_REPOS[@]}"; do
    [ "$repo_name" = "$r" ] && keep=true && break
  done
  [ "$keep" = "false" ] && slugs_to_delete+=("$slug")
done < <(atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq -r '.items[].slug' 2>/dev/null)

for slug in "${slugs_to_delete[@]}"; do
  atx ct repository delete --repo "$slug" --source "$SOURCE" >/dev/null 2>&1 </dev/null
done
echo "    Kept $(atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq '.total') repos for analysis."
echo

# --- Step 4: Run ARA ---
echo "==> [4/7] Running ARA (agentic-readiness) — ~15-25 min"
ARA_OUT=$(atx ct analysis run --type agentic-readiness --source "$SOURCE" 2>&1)
echo "    $ARA_OUT"
ARA_ID=$(echo "$ARA_OUT" | grep -oE '01[A-Z0-9]{24}' | head -1)

if [ -z "$ARA_ID" ]; then echo "!! Failed to launch ARA"; exit 1; fi

while true; do
  st=$(atx ct analysis get --id "$ARA_ID" --json 2>/dev/null | jq -r '.status' 2>/dev/null)
  echo "    ARA: $st ($(date +%H:%M:%S))"
  case "$st" in complete|failed) break;; esac
  sleep 30
done
if [ "$st" = "failed" ]; then echo "!! ARA failed"; exit 1; fi
ARA_FINDINGS=$(atx ct findings list --analysis-id "$ARA_ID" --json 2>/dev/null | jq 'length' 2>/dev/null)
echo "    ARA complete: $ARA_FINDINGS findings"
echo

# --- Step 5: Run MODA ---
echo "==> [5/7] Running MODA (modernization-readiness) — ~15-30 min"
MODA_OUT=$(atx ct analysis run --type modernization-readiness --source "$SOURCE" 2>&1)
echo "    $MODA_OUT"
MODA_ID=$(echo "$MODA_OUT" | grep -oE '01[A-Z0-9]{24}' | head -1)

if [ -z "$MODA_ID" ]; then echo "!! Failed to launch MODA"; exit 1; fi

while true; do
  st=$(atx ct analysis get --id "$MODA_ID" --json 2>/dev/null | jq -r '.status' 2>/dev/null)
  echo "    MODA: $st ($(date +%H:%M:%S))"
  case "$st" in complete|failed) break;; esac
  sleep 30
done
if [ "$st" = "failed" ]; then echo "!! MODA failed"; exit 1; fi
MODA_FINDINGS=$(atx ct findings list --analysis-id "$MODA_ID" --json 2>/dev/null | jq 'length' 2>/dev/null)
echo "    MODA complete: $MODA_FINDINGS findings"
echo

# --- Step 6: Export artifacts ---
echo "==> [6/7] Exporting report artifacts"
mkdir -p "$REPORTS_DIR/ara" "$REPORTS_DIR/moda"

atx ct analysis list-artifacts --id "$ARA_ID" --json 2>/dev/null | jq -c '.[]' | while read -r line; do
  repo=$(echo "$line" | jq -r '.repo')
  name=$(echo "$line" | jq -r '.name')
  safe="${repo//::/__}__${name//\//_}"
  atx ct analysis get-artifact --id "$ARA_ID" --repo "$repo" --name "$name" > "$REPORTS_DIR/ara/${safe}" 2>/dev/null
  echo "    ara/$safe"
done

atx ct analysis list-artifacts --id "$MODA_ID" --json 2>/dev/null | jq -c '.[]' | while read -r line; do
  repo=$(echo "$line" | jq -r '.repo')
  name=$(echo "$line" | jq -r '.name')
  safe="${repo//::/__}__${name//\//_}"
  atx ct analysis get-artifact --id "$MODA_ID" --repo "$repo" --name "$name" > "$REPORTS_DIR/moda/${safe}" 2>/dev/null
  echo "    moda/$safe"
done

cat > "$REPORTS_DIR/_ids.txt" <<EOF
ARA_ID=$ARA_ID
MODA_ID=$MODA_ID
MODE=$MODE
EOF
echo

# --- Step 7: Summary ---
echo "==> [7/7] Summary"
echo "    Mode:       $MODE"
echo "    Source:     $SOURCE"
echo "    Repos:      $(atx ct repository list --source "$SOURCE" --json 2>/dev/null | jq '.total')"
echo "    ARA:        $ARA_FINDINGS findings"
echo "    MODA:       $MODA_FINDINGS findings"
echo "    Reports in: $REPORTS_DIR/"
echo
echo "============================================"
echo "  SETUP COMPLETE — ready for demo"
echo "============================================"
echo
echo "Next steps:"
echo "  1. Open AWS Transform Console → Continuous Modernization"
echo "  2. Live discovery: ./demo-scripts/01-live-discovery-push.sh"
echo "  3. Reset discovery: ./demo-scripts/02-reset-live-discovery.sh"
if [ "$MODE" = "local" ]; then
  echo "  4. Remediation: ask Claude 'containerize shipping-api'"
  echo "     → creates a local branch. Show with: git -C <repo> diff main"
else
  echo "  4. Remediation: ask Claude 'containerize shipping-api'"
  echo "     → opens a PR in GitHub."
fi
echo
