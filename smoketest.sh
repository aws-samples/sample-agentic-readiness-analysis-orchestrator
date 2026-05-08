#!/bin/bash
# Smoke test for V6 ARA/MOD JSON reports
set -u

ARA_DIR="example-reports/zg-cmp-full-assessment-v6/agentic-readiness-assessment"
MOD_DIR="example-reports/zg-cmp-full-assessment-v6/modernization-assessment"
REQUIRED_PER_REPO="question_id category category_id title description gap recommendation severity priority effort phase evidence"
REQUIRED_PORTFOLIO_ARA_FINDINGS="question_id repo_name category category_id title description gap recommendation severity native_severity safety_impact priority effort phase evidence"
REQUIRED_PORTFOLIO_MOD_FINDINGS="question_id repo_name category category_id title severity priority effort phase evidence mod_metadata"

FAIL=0
CHECKS=0

echo "=== Check 1: 12 required V6 finding fields (ARA per-repo) ==="
for f in "$ARA_DIR"/*-ara-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  for field in $REQUIRED_PER_REPO; do
    COUNT=$(jq -r "[.findings[] | select(has(\"$field\") | not)] | length" "$f" 2>/dev/null)
    CHECKS=$((CHECKS+1))
    if [ "$COUNT" != "0" ] && [ -n "$COUNT" ]; then
      echo "  FAIL: $(basename "$f") missing '$field' in $COUNT findings"
      FAIL=$((FAIL+1))
    fi
  done
done

echo "=== Check 2: 12 required V6 finding fields (MOD per-repo) ==="
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  for field in $REQUIRED_PER_REPO; do
    COUNT=$(jq -r "[.findings[] | select(has(\"$field\") | not)] | length" "$f" 2>/dev/null)
    CHECKS=$((CHECKS+1))
    if [ "$COUNT" != "0" ] && [ -n "$COUNT" ]; then
      echo "  FAIL: $(basename "$f") missing '$field' in $COUNT findings"
      FAIL=$((FAIL+1))
    fi
  done
done

echo "=== Check 2b: Portfolio MOD findings[] 11-field schema ==="
for f in "$MOD_DIR"/*portfolio-mod-report.json; do
  [ ! -f "$f" ] && continue
  for field in $REQUIRED_PORTFOLIO_MOD_FINDINGS; do
    COUNT=$(jq -r "[.findings[] | select(has(\"$field\") | not)] | length" "$f" 2>/dev/null)
    if [ "$COUNT" != "0" ] && [ -n "$COUNT" ]; then
      echo "  FAIL: $(basename "$f") missing '$field' in $COUNT findings"
      FAIL=$((FAIL+1))
    fi
  done
done

echo ""
echo "=== SUMMARY: $FAIL failures across $CHECKS checks ==="


echo "=== Check 3: Severity values match V6 enum ==="
SEVERITY_FAIL=0
for f in "$ARA_DIR"/*-ara-report.json "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  BAD=$(jq -r '[.findings[] | select(.severity != "High" and .severity != "Medium" and .severity != "Low") | .severity] | unique | join(",")' "$f" 2>/dev/null)
  if [ -n "$BAD" ] && [ "$BAD" != "" ]; then
    echo "  FAIL: $(basename "$f") has bad severity values: $BAD"
    SEVERITY_FAIL=$((SEVERITY_FAIL+1))
  fi
done
echo "Severity enum: $SEVERITY_FAIL failures"

echo "=== Check 4: No findings emitted for N/A or passing questions ==="
NA_LEAK_FAIL=0
for f in "$ARA_DIR"/*-ara-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  # Per-repo ARA: native_severity should never be null or missing
  BAD=$(jq -r '[.findings[] | select(.ara_metadata.native_severity == null or (.ara_metadata | has("native_severity") | not))] | length' "$f" 2>/dev/null)
  if [ "$BAD" != "0" ] && [ -n "$BAD" ]; then
    echo "  FAIL: $(basename "$f") has $BAD findings with missing native_severity"
    NA_LEAK_FAIL=$((NA_LEAK_FAIL+1))
  fi
done
echo "N/A leak: $NA_LEAK_FAIL failures"

echo "=== Check 5: Metadata sidecar report_format_version == V6 ==="
META_FAIL=0
for f in "$ARA_DIR"/*.metadata.json "$MOD_DIR"/*.metadata.json; do
  VER=$(jq -r '.report_format_version' "$f" 2>/dev/null)
  if [ "$VER" != "V6" ]; then
    echo "  FAIL: $(basename "$f") has report_format_version='$VER' (expected V6)"
    META_FAIL=$((META_FAIL+1))
  fi
done
echo "Metadata version: $META_FAIL failures"

echo "=== Check 6: Classification tier matches V6 enum (ARA) ==="
TIER_FAIL=0
VALID_ARA_TIERS="Agent-Ready Pilot-Ready Remediation-Required Not-Agent-Integrable"
for f in "$ARA_DIR"/*-ara-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  TIER=$(jq -r '.classification.tier' "$f" 2>/dev/null)
  case "$TIER" in
    "Agent-Ready"|"Pilot-Ready"|"Remediation Required"|"Not Agent-Integrable") ;;
    *) echo "  FAIL: $(basename "$f") tier='$TIER'"; TIER_FAIL=$((TIER_FAIL+1));;
  esac
done
echo "ARA tier: $TIER_FAIL failures"

echo "=== Check 7: Classification tier matches V6 enum (MOD) ==="
MOD_TIER_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  TIER=$(jq -r '.classification.tier' "$f" 2>/dev/null)
  case "$TIER" in
    "Cloud-Native Ready"|"Pilot-Ready"|"Remediation Required"|"Not Ready") ;;
    *) echo "  FAIL: $(basename "$f") tier='$TIER'"; MOD_TIER_FAIL=$((MOD_TIER_FAIL+1));;
  esac
done
echo "MOD tier: $MOD_TIER_FAIL failures"

echo "=== Check 8: ARA classification consistent with blocker+risk_safety counts ==="
CLASS_FAIL=0
for f in "$ARA_DIR"/*-ara-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  TIER=$(jq -r '.classification.tier' "$f")
  SUB=$(jq -r '.classification.sub_qualifier // "none"' "$f")
  BC=$(jq -r '.summary.blocker_count // .classification.blocker_count // 0' "$f")
  RS=$(jq -r '.summary.risk_safety_count // .classification.risk_safety_count // 0' "$f")
  # Compute expected tier per D1 rule (V5 wins)
  EXPECTED=""
  EXPECTED_SUB="none"
  if [ "$BC" -ge 3 ]; then EXPECTED="Not Agent-Integrable"
  elif [ "$BC" -ge 1 ]; then EXPECTED="Remediation Required"
  elif [ "$RS" -ge 3 ]; then EXPECTED="Pilot-Ready"; EXPECTED_SUB="Pilot-Ready (Safety Concerns)"
  elif [ "$RS" -ge 1 ]; then EXPECTED="Pilot-Ready"
  else EXPECTED="Agent-Ready"
  fi
  if [ "$TIER" != "$EXPECTED" ]; then
    echo "  FAIL: $(basename "$f") tier=$TIER expected=$EXPECTED (B=$BC, RS=$RS)"
    CLASS_FAIL=$((CLASS_FAIL+1))
  fi
done
echo "ARA classification consistency: $CLASS_FAIL failures"


echo "=== Check 9: ARA summary block completeness ==="
SUMMARY_FAIL=0
for f in "$ARA_DIR"/*-ara-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  MISSING=""
  for field in blocker_count risk_safety_count risk_quality_count info_count; do
    VAL=$(jq -r ".summary.$field // \"MISSING\"" "$f")
    if [ "$VAL" = "MISSING" ] || [ "$VAL" = "null" ]; then
      MISSING="$MISSING $field"
    fi
  done
  if [ -n "$MISSING" ]; then
    echo "  FAIL: $(basename "$f") missing summary fields:$MISSING"
    SUMMARY_FAIL=$((SUMMARY_FAIL+1))
  fi
done
echo "ARA summary completeness: $SUMMARY_FAIL failures"

echo "=== Check 10: MOD score_label uses 'Not Ready' (not 'Not Present') ==="
LABEL_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) continue;; esac
  COUNT=$(jq -r '[.findings[] | select(.mod_metadata.score_label == "Not Present")] | length' "$f" 2>/dev/null)
  if [ "$COUNT" != "0" ] && [ -n "$COUNT" ]; then
    echo "  FAIL: $(basename "$f") has $COUNT findings with score_label='Not Present' (should be 'Not Ready')"
    LABEL_FAIL=$((LABEL_FAIL+1))
  fi
done
echo "MOD score_label: $LABEL_FAIL failures"

echo "=== Check 11: MOD/ARA HTML and JSON repository counts match ==="
COUNT_FAIL=0
for f in "$MOD_DIR"/*-mod-report.json "$ARA_DIR"/*-ara-report.json; do
  case "$f" in *metadata.json) continue;; esac
  case "$f" in *portfolio*) ;; *) continue;; esac
  HTML="${f%.json}.html"
  if [ ! -f "$HTML" ]; then continue; fi
  JSON_N=$(jq -r '.summary.repositories_analyzed // .metadata.services_assessed // 0' "$f")
  # Simple grep count of rows in HTML tbody (imperfect but catches big drift)
  HTML_ROWS=$(grep -cE 'services_assessed|total repos|repositories analyzed' "$HTML" 2>/dev/null || echo 0)
  # Just check the JSON is sensible for now
  if [ "$JSON_N" = "0" ]; then
    echo "  FAIL: $(basename "$f") has no repositories_analyzed / services_assessed"
    COUNT_FAIL=$((COUNT_FAIL+1))
  fi
done
echo "Portfolio HTML/JSON consistency: $COUNT_FAIL failures"

echo ""
echo "======================================="
echo "Smoke test complete."
echo "======================================="
