#!/bin/bash
# Smoke test for V6.1 MOD reports (validation batch)
set -u

MOD_DIR="example-reports/zg-cmp-full-assessment-v6/v6.1/modernization-assessment"
REQUIRED="question_id category category_id title description gap recommendation severity priority effort phase evidence"

FAIL=0
CHECKS=0

echo "=== v6.1 Check 1: 12 required V6 finding fields (MOD per-repo) ==="
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  for field in $REQUIRED; do
    COUNT=$(jq -r "[.findings[] | select(has(\"$field\") | not)] | length" "$f" 2>/dev/null)
    CHECKS=$((CHECKS+1))
    if [ "$COUNT" != "0" ] && [ -n "$COUNT" ]; then
      echo "  FAIL: $(basename "$f") missing '$field' in $COUNT findings"
      FAIL=$((FAIL+1))
    fi
  done
done
echo "v6.1 Check 1: $FAIL failures across $CHECKS checks"

echo ""
echo "=== v6.1 Check 2: Severity enum (High/Medium/Low) ==="
S_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  BAD=$(jq -r '[.findings[] | select(.severity != "High" and .severity != "Medium" and .severity != "Low") | .severity] | unique | join(",")' "$f" 2>/dev/null)
  if [ -n "$BAD" ] && [ "$BAD" != "" ]; then
    echo "  FAIL: $(basename "$f") bad severity: $BAD"
    S_FAIL=$((S_FAIL+1))
  fi
done
echo "v6.1 Check 2: $S_FAIL failures"

echo ""
echo "=== v6.1 Check 3: MOD tier enum ==="
T_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  TIER=$(jq -r '.classification.tier // "MISSING"' "$f")
  case "$TIER" in
    "Cloud-Native Ready"|"Pilot-Ready"|"Remediation Required"|"Not Ready") ;;
    *) echo "  FAIL: $(basename "$f") tier='$TIER'"; T_FAIL=$((T_FAIL+1));;
  esac
done
echo "v6.1 Check 3: $T_FAIL failures"

echo ""
echo "=== v6.1 Check 4: score_label uses 'Not Ready' ==="
L_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  COUNT=$(jq -r '[.findings[] | select(.mod_metadata.score_label == "Not Present")] | length' "$f" 2>/dev/null)
  if [ "$COUNT" != "0" ] && [ -n "$COUNT" ]; then
    echo "  FAIL: $(basename "$f") $COUNT findings use 'Not Present'"
    L_FAIL=$((L_FAIL+1))
  fi
done
echo "v6.1 Check 4: $L_FAIL failures"

echo ""
echo "=== v6.1 Check 5: core_question matches G4 designation table ==="
C_FAIL=0
CORE_LIST="INF-Q1 INF-Q2 INF-Q5 INF-Q10 INF-Q11 APP-Q2 DATA-Q1 DATA-Q3 DATA-Q4 SEC-Q1 SEC-Q2 SEC-Q5 OPS-Q5 OPS-Q6"
NONCORE_LIST="INF-Q3 INF-Q4 INF-Q6 INF-Q7 INF-Q8 INF-Q9 APP-Q1 APP-Q3 APP-Q4 APP-Q5 APP-Q6 DATA-Q2 SEC-Q3 SEC-Q4 SEC-Q6 SEC-Q7 OPS-Q1 OPS-Q2 OPS-Q3 OPS-Q4 OPS-Q7 OPS-Q8 OPS-Q9"
is_core() {
  q=$1
  for c in $CORE_LIST; do [ "$c" = "$q" ] && echo true && return; done
  for n in $NONCORE_LIST; do [ "$n" = "$q" ] && echo false && return; done
  echo UNKNOWN
}
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  while IFS='|' read -r qid got; do
    expected=$(is_core "$qid")
    [ "$expected" = "UNKNOWN" ] && continue
    if [ "$expected" != "$got" ]; then
      echo "  FAIL: $(basename "$f") $qid got core_question=$got expected $expected"
      C_FAIL=$((C_FAIL+1))
    fi
  done < <(jq -r '.findings[] | "\(.question_id)|\(.mod_metadata.core_question)"' "$f" 2>/dev/null)
done
echo "v6.1 Check 5: $C_FAIL failures"

echo ""
echo "=== v6.1 Check 6: Severity mapping (score 1 + core=true => High) ==="
SM_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  MISMATCH=$(jq -r '[.findings[] | 
    select(.mod_metadata.internal_score == 1 and .mod_metadata.core_question == true and .severity != "High")
    | "\(.question_id)=\(.severity)"] | join(",")' "$f" 2>/dev/null)
  if [ -n "$MISMATCH" ] && [ "$MISMATCH" != "" ]; then
    echo "  FAIL: $(basename "$f") score=1+core=true but severity not High: $MISMATCH"
    SM_FAIL=$((SM_FAIL+1))
  fi
done
echo "v6.1 Check 6: $SM_FAIL failures"

echo ""
echo "=== v6.1 Check 7: Severity mapping (score 2 => Medium) ==="
SM2_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  MISMATCH=$(jq -r '[.findings[] | 
    select(.mod_metadata.internal_score == 2 and .severity != "Medium")
    | "\(.question_id)=\(.severity)"] | join(",")' "$f" 2>/dev/null)
  if [ -n "$MISMATCH" ] && [ "$MISMATCH" != "" ]; then
    echo "  FAIL: $(basename "$f") score=2 but severity not Medium: $MISMATCH"
    SM2_FAIL=$((SM2_FAIL+1))
  fi
done
echo "v6.1 Check 7: $SM2_FAIL failures"

echo ""
echo "======================================="
echo "v6.1 smoke test complete."
echo "======================================="
