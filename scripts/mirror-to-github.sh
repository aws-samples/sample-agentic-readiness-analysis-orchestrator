#!/usr/bin/env bash
# Mirror a GitLab branch's CONTENT to the public GitHub remote as ONE squashed commit.
#
#   scripts/mirror-to-github.sh [--push] [<source-ref>] [<github-branch>]
#
# Defaults: source-ref = main, github-branch = main.
# Without --push it is a DRY RUN: it builds the commit locally, prints the scan and the
# diffstat, and stops. Nothing reaches GitHub until you re-run with --push.
#
# WHY SQUASH, NOT A NORMAL PUSH
# -----------------------------
# A normal push publishes every ancestor commit. Four commits reachable from main carry an
# AWS account id in .gitlab-ci.yml (it lived inline while the pipeline was being validated,
# then moved to a CI variable in fa7e30d). Those blobs stay fetchable by SHA on GitHub even
# after a later cleanup commit, so the only way to publish the CONTENT without the ID is to
# publish a tree, not a history. GitLab stays the real development line with full history;
# GitHub gets a content mirror. This also keeps committer emails out of the public repo.
#
# The squash is built on top of whatever GitHub already has, so it is a fast-forward for
# them and never needs --force. If someone merged a PR on GitHub that is not in the source
# ref, this script REFUSES to run rather than silently reverting it.
set -euo pipefail

PUSH=0
if [ "${1:-}" = "--push" ]; then PUSH=1; shift; fi
SRC="${1:-main}"
DST="${2:-main}"
GITHUB_REMOTE="${GITHUB_REMOTE:-origin}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

say() { printf '%s\n' "$*"; }
die() { printf 'mirror: %s\n' "$*" >&2; exit 1; }

git rev-parse --verify -q "$SRC" >/dev/null || die "source ref '$SRC' does not exist"
[ -z "$(git status --porcelain)" ] || die "working tree is dirty — commit or stash first"

say "==> fetching $GITHUB_REMOTE"
git fetch -q "$GITHUB_REMOTE"

REMOTE_URL="$(git remote get-url "$GITHUB_REMOTE")"
case "$REMOTE_URL" in
  *github.com*) : ;;
  *) die "remote '$GITHUB_REMOTE' is $REMOTE_URL — refusing; this script only targets GitHub" ;;
esac

# ---------------------------------------------------------------------------
# Refuse to discard public work. Anything on the GitHub branch that is not an
# ancestor of the source ref would be reverted by a content squash.
# ---------------------------------------------------------------------------
UPSTREAM="$GITHUB_REMOTE/$DST"
if git rev-parse --verify -q "$UPSTREAM" >/dev/null; then
  if ! git merge-base --is-ancestor "$UPSTREAM" "$SRC"; then
    AHEAD="$(git rev-list --count "$SRC..$UPSTREAM")"
    say ""
    say "mirror: $UPSTREAM has $AHEAD commit(s) not in '$SRC':"
    git log --oneline "$SRC..$UPSTREAM" | sed 's/^/    /'
    say ""
    say "A content squash would REVERT those. Some may already be present as equivalent"
    say "text (a cherry-pick or a re-apply on the GitLab side) — in that case the revert is"
    say "only apparent. Verify per commit, then merge or cherry-pick into '$SRC' and re-run."
    die "refusing to discard public commits"
  fi
fi

# ---------------------------------------------------------------------------
# Sensitive-content scan of the exact tree that would be published.
# Uses a temp worktree so the scan reads FILES, not a ref: `git grep <ref>` silently
# reads the committed tree, which is easy to mistake for the staged one.
# ---------------------------------------------------------------------------
SCAN_DIR="$(mktemp -d)"
cleanup() { git worktree remove --force "$SCAN_DIR" >/dev/null 2>&1 || true; rm -rf "$SCAN_DIR"; }
trap cleanup EXIT
git worktree add -q --detach "$SCAN_DIR" "$SRC"

say "==> scanning the tree that would be published"
FINDINGS=0
scan() {  # scan <label> <extended-regex> [allowlist-regex]
  local label="$1" pattern="$2" allow="${3:-}" hits
  hits="$(grep -rInE --binary-files=without-match \
            --exclude-dir=.git "$pattern" "$SCAN_DIR" 2>/dev/null || true)"
  [ -n "$allow" ] && hits="$(printf '%s\n' "$hits" | grep -vE "$allow" || true)"
  hits="$(printf '%s\n' "$hits" | sed "s|^$SCAN_DIR/||" | grep -v '^$' || true)"
  if [ -n "$hits" ]; then
    say "  !! $label"
    printf '%s\n' "$hits" | head -20 | sed 's/^/       /'
    FINDINGS=$((FINDINGS + 1))
  else
    say "  ok $label"
  fi
}

# 979517299116 = AWS's shared GitLab runner fleet (needed in the trust-policy example).
# 123456789012 = the placeholder from AWS's own docs.
scan "no AWS account ids"      '[^0-9A-Za-z._-][0-9]{12}([^0-9]|$)' '979517299116|123456789012|\.(html|svg|css):'
scan "no access keys"          '(AKIA|ASIA)[A-Z0-9]{16}'
scan "no private keys"         'BEGIN [A-Z ]*PRIVATE KEY'
scan "no real SCM tokens"      'glpat-[A-Za-z0-9_-]{20}|ghp_[A-Za-z0-9]{36}'
scan "no internal systems"     '[Ii]sengard|mwinit|[Mm]idway|w\.amazon\.com|code\.amazon\.com|\.a2z\.com|corp\.amazon|[Tt]askei|[Qq]uip'
scan "no employee emails"      '[A-Za-z0-9._%-]+@(amazon|aws)\.[a-z.]+' 'opensource-codeofconduct@amazon\.com|aws-security@amazon\.com'

if [ "$FINDINGS" -gt 0 ]; then
  die "$FINDINGS scan(s) flagged content — resolve before mirroring"
fi

# ---------------------------------------------------------------------------
# Build the squash commit: GitHub's tip as parent, the source ref's tree as content.
# ---------------------------------------------------------------------------
TREE="$(git rev-parse "$SRC^{tree}")"
SRC_SHA="$(git rev-parse --short "$SRC")"
if git rev-parse --verify -q "$UPSTREAM" >/dev/null; then
  if [ "$(git rev-parse "$UPSTREAM^{tree}")" = "$TREE" ]; then
    say "==> $UPSTREAM already has this exact tree — nothing to mirror"
    exit 0
  fi
  PARENT_ARG=(-p "$UPSTREAM")
else
  PARENT_ARG=()
fi

COMMIT="$(git commit-tree "$TREE" "${PARENT_ARG[@]}" -m "mirror: sync content from $SRC ($SRC_SHA)

Squashed content mirror of the GitLab development line. GitLab carries the full
commit history; this repository receives the resulting tree so that no internal
identifiers are published in reachable history.")"

say ""
say "==> squash commit $(git rev-parse --short "$COMMIT")  (tree of $SRC @ $SRC_SHA)"
if [ "${#PARENT_ARG[@]}" -gt 0 ]; then
  git diff --stat "$UPSTREAM" "$COMMIT" | tail -25
else
  say "    (new branch on $GITHUB_REMOTE — no parent to diff against)"
fi

if [ "$PUSH" -eq 0 ]; then
  say ""
  say "DRY RUN. Nothing was pushed. To publish:"
  say "    scripts/mirror-to-github.sh --push $SRC $DST"
  exit 0
fi

say ""
say "==> pushing to $GITHUB_REMOTE $DST"
git push "$GITHUB_REMOTE" "$COMMIT:refs/heads/$DST"
say "done."
