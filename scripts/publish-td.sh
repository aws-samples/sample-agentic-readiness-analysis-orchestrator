#!/usr/bin/env bash
# Publish a TD to the ATX registry.
# Usage: ./scripts/publish-td.sh <path-to-td-folder> [--draft]
#
# Each TD folder must contain either:
#   - SKILL.md + optional references/    (EXPERIMENTAL_SKILL schema)
#   - transformation_definition.md + optional summaries.md + document_references/  (DEFAULT schema)
#
# The TD name is derived from the folder name.
# Requires AWS_REGION=us-east-1 (or a supported region).

set -euo pipefail

usage() {
  echo "Usage: $0 <path-to-td-folder> [--draft]" >&2
  exit 1
}

TD_DIR=""
DRAFT=false

for arg in "$@"; do
  case "$arg" in
    --draft)
      DRAFT=true
      ;;
    -h|--help)
      usage
      ;;
    *)
      if [[ -n "$TD_DIR" ]]; then
        echo "Error: unexpected argument '$arg'" >&2
        usage
      fi
      TD_DIR="$arg"
      ;;
  esac
done

[[ -n "$TD_DIR" ]] || usage

if [[ ! -d "$TD_DIR" ]]; then
  echo "Error: '$TD_DIR' is not a directory" >&2
  exit 1
fi

# Resolve to an absolute path and derive the TD name from the folder basename.
TD_DIR="$(cd "$TD_DIR" && pwd)"
TD_NAME="$(basename "$TD_DIR")"

# Detect schema and extract the description.
DESCRIPTION=""
if [[ -f "$TD_DIR/SKILL.md" ]]; then
  SCHEMA="EXPERIMENTAL_SKILL"
  # Description from the YAML frontmatter of SKILL.md.
  DESCRIPTION="$(awk '
    NR==1 && $0=="---" { in_fm=1; next }
    in_fm && $0=="---" { exit }
    in_fm && /^description:[[:space:]]*/ {
      sub(/^description:[[:space:]]*/, ""); print; exit
    }
  ' "$TD_DIR/SKILL.md")"
elif [[ -f "$TD_DIR/transformation_definition.md" ]]; then
  SCHEMA="DEFAULT"
  # Description from the first markdown heading of transformation_definition.md.
  DESCRIPTION="$(awk '/^#+[[:space:]]+/ { sub(/^#+[[:space:]]+/, ""); print; exit }' \
    "$TD_DIR/transformation_definition.md")"
else
  echo "Error: '$TD_DIR' contains neither SKILL.md nor transformation_definition.md" >&2
  exit 1
fi

if [[ -z "$DESCRIPTION" ]]; then
  DESCRIPTION="$TD_NAME"
fi

# The API restricts description to printable ASCII (`[\x20-\x7E\t\r\n]*`) and rejects the whole
# request otherwise. Markdown headings routinely contain em dashes and smart quotes, so transliterate
# the common ones and drop anything else non-ASCII rather than failing the publish.
DESCRIPTION="$(printf '%s' "$DESCRIPTION" \
  | sed $'s/[—–]/-/g; s/[‘’]/\'/g; s/[“”]/"/g; s/…/.../g' \
  | tr -d '\000-\010\013\014\016-\037' \
  | LC_ALL=C tr -cd '\11\15\40-\176')"

if [[ -z "$DESCRIPTION" ]]; then
  DESCRIPTION="$TD_NAME"
fi

if ! command -v atx >/dev/null 2>&1; then
  echo "Error: 'atx' CLI not found. Install: curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash" >&2
  exit 1
fi

if [[ -z "${AWS_REGION:-}" ]]; then
  echo "Warning: AWS_REGION is not set; defaulting to us-east-1" >&2
  export AWS_REGION=us-east-1
fi

# The TD registry is tenanted by authentication mode: one endpoint, two separate namespaces, and a
# TD published in one is a 404 in the other. `atx` picks the mode in AuthenticationManager
# .isAWSMode(): MIDWAY=false forces AWS-credentials mode, and when MIDWAY is unset the default
# flips based on whether TOOLBOX_TOOL_VERSION is set in the environment.
#
# That matters because the `ct remediation` worker subprocess always runs in AWS-credentials mode.
# If a publish defaults the other way, `custom def get` confirms the TD while `remediation create`
# reports "not found in the registry" — and publishing to one namespace does not backfill the other,
# so the only fix is to re-publish. Pin AWS-credentials mode here so what we publish is what
# remediation resolves. An explicit MIDWAY=true still overrides.
if [[ -z "${MIDWAY:-}" ]]; then
  export MIDWAY=false
fi

ACTION="publish"
if [[ "$DRAFT" == true ]]; then
  ACTION="save-draft"
fi

# `atx custom def publish` validates the source dir against the schema's allowlist and hard-fails
# on anything else: "Unsupported file(s) or directory in DEFAULT transformation definition:
# README.md. Allowed contents are: transformation_definition.md, summaries.md,
# document_references". A README aimed at contributors is useful to keep beside the TD, so publish
# from a staged copy containing only the allowed entries rather than from the folder itself.
SUBMIT_DIR="$TD_DIR"
if [[ "$SCHEMA" == "DEFAULT" ]]; then
  ALLOWED=(transformation_definition.md summaries.md document_references)
else
  ALLOWED=(SKILL.md references)
fi

EXCLUDED=()
while IFS= read -r entry; do
  [[ -n "$entry" ]] || continue
  keep=false
  for a in "${ALLOWED[@]}"; do
    [[ "$entry" == "$a" ]] && keep=true && break
  done
  [[ "$keep" == false ]] && EXCLUDED+=("$entry")
done < <(ls -A "$TD_DIR")

if [[ ${#EXCLUDED[@]} -gt 0 ]]; then
  STAGE_DIR="$(mktemp -d)"
  trap 'rm -rf "$STAGE_DIR"' EXIT
  for a in "${ALLOWED[@]}"; do
    [[ -e "$TD_DIR/$a" ]] && cp -R "$TD_DIR/$a" "$STAGE_DIR/"
  done
  SUBMIT_DIR="$STAGE_DIR"
  echo "Excluded:    ${EXCLUDED[*]} (not part of the $SCHEMA schema)"
fi

echo "TD name:     $TD_NAME"
echo "Schema:      $SCHEMA"
echo "Description: $DESCRIPTION"
echo "Action:      atx custom def $ACTION"
echo "Region:      $AWS_REGION"
echo

OUTPUT_FILE="$(mktemp)"
# Preserve any STAGE_DIR cleanup already registered above.
trap 'rm -f "$OUTPUT_FILE"; [[ -n "${STAGE_DIR:-}" ]] && rm -rf "$STAGE_DIR"' EXIT

set +e
atx custom def "$ACTION" \
  -n "$TD_NAME" \
  --description "$DESCRIPTION" \
  --sd "$SUBMIT_DIR" \
  2>&1 | tee "$OUTPUT_FILE"
STATUS=${PIPESTATUS[0]}
set -e

if [[ "$STATUS" -eq 0 ]]; then
  # atx outputs either JSON (--json flag) or a human line like:
  #   ✓ Saved a draft ... with version '3ghtdm8ik...' in the registry
  #   ✓ Published ... with version '3ggp9vjo...'
  VERSION="$(grep -oE "version '[^']+'" "$OUTPUT_FILE" | grep -oE "'[^']+'" | tr -d "'" | head -1 || true)"
  # Fallback: try JSON format
  [[ -z "$VERSION" ]] && VERSION="$(grep -oE '"version":"[^"]*"' "$OUTPUT_FILE" | head -1 | cut -d'"' -f4 || true)"
  echo
  if [[ -n "$VERSION" ]]; then
    echo "SUCCESS: '$TD_NAME' ${ACTION}ed (version: $VERSION)"
  else
    echo "SUCCESS: '$TD_NAME' ${ACTION}ed"
  fi
else
  echo
  echo "FAILURE: 'atx custom def $ACTION' exited with status $STATUS for '$TD_NAME'" >&2
  exit "$STATUS"
fi
