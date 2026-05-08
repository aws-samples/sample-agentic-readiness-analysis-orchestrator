#!/bin/bash
# Smoke test for V6.2 simulated MOD reports (2 repos)
set -u

MOD_DIR="example-reports/zg-cmp-full-assessment-v6/v6.2/modernization-assessment"
REQUIRED="question_id category category_id title description gap recommendation severity priority effort phase evidence"

FAIL=0

echo "=== v6.2 Check 1: 12 required V6 finding fields (MOD per-repo) ==="
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  for field in $REQUIRED; do
    COUNT=$(jq -r "[.findings[] | select(has(\"$field\") | not)] | length" "$f" 2>/dev/null)
    if [ "$COUNT" != "0" ] && [ -n "$COUNT" ]; then
      echo "  FAIL: $(basename "$f") missing '$field' in $COUNT findings"
      FAIL=$((FAIL+1))
    fi
  done
done
echo "v6.2 Check 1: $FAIL failures"

echo ""
echo "=== v6.2 Check 2: Severity enum + tier enum + score_label + surface flags ==="
F=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  # Severity enum
  BAD=$(jq -r '[.findings[] | select(.severity != "High" and .severity != "Medium" and .severity != "Low") | .severity] | unique | join(",")' "$f")
  [ -n "$BAD" ] && [ "$BAD" != "" ] && echo "  FAIL: $(basename "$f") bad severity: $BAD" && F=$((F+1))
  # Tier enum
  TIER=$(jq -r '.classification.tier' "$f")
  case "$TIER" in "Cloud-Native Ready"|"Pilot-Ready"|"Remediation Required"|"Not Ready") ;; *) echo "  FAIL: $(basename "$f") tier='$TIER'"; F=$((F+1));; esac
  # Score label
  BAD_LABEL=$(jq -r '[.findings[] | select(.mod_metadata.score_label == "Not Present")] | length' "$f")
  [ "$BAD_LABEL" != "0" ] && echo "  FAIL: $(basename "$f") $BAD_LABEL score_label='Not Present'" && F=$((F+1))
  # Surface flags present
  MISSING_SF=$(jq -r '[.metadata.surface_flags | keys | .[]]| length' "$f")
  [ "$MISSING_SF" -lt 6 ] 2>/dev/null && echo "  FAIL: $(basename "$f") has only $MISSING_SF of 6 surface flags" && F=$((F+1))
done
echo "v6.2 Check 2: $F failures"

echo ""
echo "=== v6.2 Check 3: Severity mapping (score 1 + core=true => High; score 2 => Medium) ==="
F=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  MISMATCH=$(jq -r '[.findings[] | select(.mod_metadata.internal_score == 1 and .mod_metadata.core_question == true and .severity != "High") | "\(.question_id)=\(.severity)"] | join(",")' "$f")
  [ -n "$MISMATCH" ] && [ "$MISMATCH" != "" ] && echo "  FAIL: $(basename "$f") score=1+core=true but not High: $MISMATCH" && F=$((F+1))
  MISMATCH2=$(jq -r '[.findings[] | select(.mod_metadata.internal_score == 2 and .severity != "Medium") | "\(.question_id)=\(.severity)"] | join(",")' "$f")
  [ -n "$MISMATCH2" ] && [ "$MISMATCH2" != "" ] && echo "  FAIL: $(basename "$f") score=2 but not Medium: $MISMATCH2" && F=$((F+1))
done
echo "v6.2 Check 3: $F failures"

echo ""
echo "=== v6.2 Check 4: No findings for N/A / Not Evaluated / Score 4 questions ==="
F=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  # Score 4 leak
  LEAK=$(jq -r '[.findings[] | select(.mod_metadata.internal_score == 4)] | length' "$f")
  [ "$LEAK" != "0" ] && echo "  FAIL: $(basename "$f") $LEAK findings emitted for passing (score=4) questions" && F=$((F+1))
done
echo "v6.2 Check 4: $F failures"

echo ""
echo "=== v6.2 Check 5: All 4 artifacts present per repo ==="
F=0
for base in $(ls "$MOD_DIR"/*-mod-report.md 2>/dev/null | sed 's|.*/||' | sed 's|-mod-report.md||'); do
  for ext in md json html metadata.json; do
    [ ! -f "$MOD_DIR/$base-mod-report.$ext" ] && echo "  FAIL: $base missing .$ext" && F=$((F+1))
  done
done
echo "v6.2 Check 5: $F failures"

echo ""
echo "======================================="
echo "v6.2 smoke test complete."
echo "======================================="
