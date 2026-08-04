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
PORTFOLIO_DIR="$PROJECT_DIR/harness/fixtures/portfolio"
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

# Wait for an analysis to ACTUALLY finish.
#
# `status` alone is not a terminal signal on a multi-repo run: it flips to `complete` when the
# per-repo phase ends, while the portfolio phase keeps running for tens of minutes. In that
# window report_paths is {}, findings is empty and portfolio_*_summary is null — the run looks
# like it produced nothing. `report_paths` is written in the FINAL record update, so require it
# non-empty too. Timeout is required: a genuine early failure leaves it empty forever.
#
# Prints the terminal status on stdout; returns non-zero on timeout.
wait_for_analysis() {
  local id="$1" label="$2" timeout_min="${3:-90}"
  local deadline=$(( $(date +%s) + timeout_min * 60 ))
  local st n
  while :; do
    read -r st n < <(atx ct analysis get --id "$id" --json 2>/dev/null \
      | jq -r '"\(.status // "unknown") \(.report_paths // {} | length)"' 2>/dev/null)
    st="${st:-unknown}"; n="${n:-0}"

    if [ "$st" = "failed" ]; then echo "$st"; return 0; fi
    if [ "$st" = "complete" ] && [ "$n" -gt 0 ]; then echo "$st"; return 0; fi

    if [ "$st" = "complete" ] && [ "$n" -eq 0 ]; then
      echo "    $label: portfolio phase still running... ($(date +%H:%M:%S))" >&2
    else
      echo "    $label: $st ($(date +%H:%M:%S))" >&2
    fi

    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "!! $label: timed out after ${timeout_min}m (status=$st, reports=$n)" >&2
      echo "$st"; return 1
    fi
    sleep 30
  done
}

# --- Step 0: Pre-flight ---
echo "==> [0/7] Pre-flight checks"
aws sts get-caller-identity >/dev/null 2>&1 || { echo "!! AWS creds not active"; exit 1; }
command -v atx >/dev/null 2>&1 || { echo "!! atx CLI not found"; exit 1; }
command -v jq  >/dev/null 2>&1 || { echo "!! jq not found (required)"; exit 1; }
# Inside Claude Code a bare `atx --version` reports Builder Toolbox's version (2.1.x), which atx
# inherits from $TOOLBOX_TOOL_VERSION. Strip it to read the real one. Needs >= 3.9.0: 3.7.0 had a
# report parser that silently extracted 0 findings.
atx_ver=$(env -u TOOLBOX_TOOL_VERSION atx --version 2>/dev/null | tr -d '[:space:]')
echo "    atx version: ${atx_ver:-unknown}"
case "$atx_ver" in
  3.9.*|3.1[0-9].*|[4-9].*) ;;
  *) echo "    !! expected atx >= 3.9.0; older builds silently produce 0 findings."
     echo "       Upgrade: curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash" ;;
esac

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

# --- Step 1: Health check ---
# There is NO server to start. Analyses run in-process; `atx ct server` still exists but is
# deprecated and hidden, and starting it just blocks a shell on :8081 for no benefit.
echo "==> [1/7] Checking ct health"
health=$(atx ct status --health 2>&1)
if [ "$health" != "healthy" ]; then
  echo "!! ct is not healthy: $health"
  echo "   Usually AWS credentials. Try: aws sts get-caller-identity"
  exit 1
fi
echo "    healthy."
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

st=$(wait_for_analysis "$ARA_ID" "ARA" 90) || { echo "!! ARA did not finish in time"; exit 1; }

# A `failed` ARA is NOT fatal for the demo. The known repositoryId-null persist bug fires at the
# very end of any multi-repo run that emits a cross-cutting blocker: the reports are already on
# disk and the per-repo findings are already stored, so only the cross-cutting findings are lost
# (they remain readable in portfolio_ara_summary.cross_cutting_blockers). Only bail if nothing
# was actually produced.
ARA_FINDINGS=$(atx ct findings list --analysis-id "$ARA_ID" --json 2>/dev/null | jq 'length' 2>/dev/null)
ARA_FINDINGS=${ARA_FINDINGS:-0}
if [ "$st" = "failed" ]; then
  if [ "$ARA_FINDINGS" -gt 0 ]; then
    echo "    ARA reports 'failed' but produced $ARA_FINDINGS findings — this is the known"
    echo "    portfolio persist bug (cross-cutting findings only). Continuing."
  else
    echo "!! ARA failed with no findings"
    atx ct analysis get --id "$ARA_ID" --json 2>/dev/null | jq -r '.error // "no error recorded"'
    exit 1
  fi
else
  echo "    ARA complete: $ARA_FINDINGS findings"
fi
echo

# --- Step 5: Run MODA ---
echo "==> [5/7] Running MODA (modernization-readiness) — ~15-30 min"
MODA_OUT=$(atx ct analysis run --type modernization-readiness --source "$SOURCE" 2>&1)
echo "    $MODA_OUT"
MODA_ID=$(echo "$MODA_OUT" | grep -oE '01[A-Z0-9]{24}' | head -1)

if [ -z "$MODA_ID" ]; then echo "!! Failed to launch MODA"; exit 1; fi

st=$(wait_for_analysis "$MODA_ID" "MODA" 120) || { echo "!! MODA did not finish in time"; exit 1; }

MODA_FINDINGS=$(atx ct findings list --analysis-id "$MODA_ID" --json 2>/dev/null | jq 'length' 2>/dev/null)
MODA_FINDINGS=${MODA_FINDINGS:-0}
if [ "$st" = "failed" ]; then
  if [ "$MODA_FINDINGS" -gt 0 ]; then
    echo "    MODA reports 'failed' but produced $MODA_FINDINGS findings — continuing."
  else
    echo "!! MODA failed with no findings"
    atx ct analysis get --id "$MODA_ID" --json 2>/dev/null | jq -r '.error // "no error recorded"'
    exit 1
  fi
else
  echo "    MODA complete: $MODA_FINDINGS findings"
fi

# MODA can also read `complete` while its portfolio report is missing — recorded as a repo_error,
# which does not fail the run. Surface it so the demo operator knows before showing the console.
moda_repo_errs=$(atx ct analysis get --id "$MODA_ID" --json 2>/dev/null | jq -r '(.repo_errors // {}) | length' 2>/dev/null)
if [ "${moda_repo_errs:-0}" -gt 0 ]; then
  echo "    note: MODA recorded $moda_repo_errs repo_error(s):"
  atx ct analysis get --id "$MODA_ID" --json 2>/dev/null | jq -r '(.repo_errors // {}) | to_entries[] | "      \(.key): \(.value)"' 2>/dev/null | head -5
fi
echo

# --- Step 6: Export artifacts ---
echo "==> [6/7] Exporting report artifacts"
mkdir -p "$REPORTS_DIR/ara" "$REPORTS_DIR/moda"

# `analysis list-artifacts` and `get-artifact` were REMOVED (atx 3.9.0: "unknown command").
# Copy straight off disk instead. Reports live in the source-scoped run tree, which is the ONLY
# complete copy — report_paths on the analysis record is markdown-only, and the portfolio .html
# and .json exist here and nowhere else. Two reasons to glob rather than construct these paths:
# the segment after the source name is the SOURCE's analysis root (a MOD run lands under
# .../agentic-readiness/runs/<id>/), and per-repo dirs are slug-mangled <source>-<repo>-<16hex>.
export_run() {
  local id="$1" dest="$2" n=0 f rel
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    # flatten <repo-dir>/<type>-analysis/<file> into one filename
    rel=$(printf '%s' "$f" | sed "s|.*/runs/$id/||; s|/|__|g")
    cp "$f" "$dest/$rel" 2>/dev/null && n=$((n+1))
  done < <(find "$HOME/.atxct/sources" -path "*runs/$id/*" -type f \
             \( -name '*.md' -o -name '*.json' -o -name '*.html' \) 2>/dev/null)
  echo "$n"
}

ara_n=$(export_run "$ARA_ID" "$REPORTS_DIR/ara")
echo "    ara/  $ara_n files"
moda_n=$(export_run "$MODA_ID" "$REPORTS_DIR/moda")
echo "    moda/ $moda_n files"

if [ "$ara_n" -eq 0 ] && [ "$moda_n" -eq 0 ]; then
  echo "    !! no artifacts found on disk — check: find ~/.atxct/sources -path '*runs/$ARA_ID/*'"
fi

# The portfolio .json is what the EBA execution-plan TD consumes; the .html is what you open in a
# browser during the demo. Point at them explicitly so nobody goes hunting.
for f in "$HOME"/.atxct/sources/*/*/runs/"$ARA_ID"/portfolio-*/*-analysis/*.html \
         "$HOME"/.atxct/sources/*/*/runs/"$MODA_ID"/portfolio-*/*-analysis/*.html; do
  [ -f "$f" ] && echo "    portfolio html: $f"
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
echo "  4. Remediation — publish a TD FIRST; there is no built-in containerization transform."
echo "     ARA/MOD findings are assessment-only (fix: null), so remediation always runs a TD"
echo "     you name. Any TD works; user-published ones resolve fine. Names go stale, so"
echo "     verify the exact name in THIS account+region before demoing:"
echo "       AWS_REGION=us-east-1 atx custom def publish -n <my-td> --sd <td-dir> --description \"...\""
echo "       (cd \"\$(mktemp -d)\" && AWS_REGION=us-east-1 atx custom def get -n <my-td>)   # ✓ = ready"
if [ "$MODE" = "local" ]; then
  echo "     Then ask Claude 'containerize shipping-api' (add --local for local sources)"
  echo "     → creates a local branch. Show with: git -C <repo> diff main"
else
  echo "     Then ask Claude 'containerize shipping-api'"
  echo "     → opens a PR in GitHub."
fi
echo
