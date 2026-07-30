#!/usr/bin/env python3
"""
calibrate-judge.py — is the judge's SCORE actually meaningful?

The judge emits a 0-100 score, and nothing so far has checked whether that number is
ordered. A score is only useful if a worse change reliably scores lower than a better one;
if a no-op, a clean intended edit and a rubric-weakening edit all land in the 70s, the
number is decoration and reviewers will learn to ignore it.

So: synthesize a ladder of deltas against the committed golden baseline, from "nothing
changed" through "silently weakened the safety rubric", run the real judge over each, and
print the scores in expected order. Each scenario carries the band it SHOULD land in, and
the script reports which ones fall outside it — that is the calibration signal.

This is a diagnostic tool, not a test: it costs a Bedrock call per scenario and the analysis
agent is nondeterministic, so it is run deliberately rather than in CI.

Usage:
  python3 harness/calibrate-judge.py                 # all scenarios
  python3 harness/calibrate-judge.py --only no-op clean-reclassify
  python3 harness/calibrate-judge.py --heuristic     # no Bedrock (fast, tests plumbing)
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "harness" / "golden"

_spec = importlib.util.spec_from_file_location("diff_reports", REPO / "harness" / "diff-reports.py")
dr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dr)  # type: ignore

LOAN = ("ara", "repo", "legacy-loan-calculator")


# --- mutations -------------------------------------------------------------------------
# Each takes an `after` tree and mutates it in place. They mirror what the analysis agent
# would emit for a given rubric edit, INCLUDING the classification counters — a mutation
# that moved a finding without its counts would be asserting against a state no real run
# can produce.

def _find(rpt: dict, qid: str) -> dict | None:
    for f in rpt.get("findings") or []:
        if f.get("question_id") == qid:
            return f
    return None


def _reclassify_everywhere(after: dict, qid: str, frm: str, to: str) -> int:
    n = 0
    for key, rpt in after.items():
        if key[0] != "ara" or key[1] != "repo":
            continue
        f = _find(rpt, qid)
        if f and f.get("ara_metadata", {}).get("native_severity") == frm:
            f["ara_metadata"]["native_severity"] = to
            n += 1
    return n


def m_noop(after: dict) -> None:
    return None


def m_clean_reclassify(after: dict) -> None:
    """The intended MR !14 edit alone: API-Q2 RISK-QUALITY -> RISK-SAFETY."""
    _reclassify_everywhere(after, "API-Q2", "RISK-QUALITY", "RISK-SAFETY")


def m_stricter(after: dict) -> None:
    """The rubric getting HARSHER: a RISK-SAFETY question promoted to BLOCKER."""
    rpt = after[LOAN]
    f = _find(rpt, "DATA-Q1")
    f["ara_metadata"]["native_severity"] = "BLOCKER"
    c = rpt["classification"]
    c["blocker_count"] += 1
    c["risk_safety_count"] -= 1


def m_risk_safety_drift(after: dict) -> None:
    """Tier-inert drift: RISK-SAFETY -> RISK-QUALITY while blockers remain."""
    rpt = after[LOAN]
    f = _find(rpt, "DATA-Q1")
    f["ara_metadata"]["native_severity"] = "RISK-QUALITY"
    c = rpt["classification"]
    c["risk_safety_count"] -= 1
    c["risk_quality_count"] += 1


def m_mr14_as_shipped(after: dict) -> None:
    """What MR !14 actually produced: the intended edit PLUS a blocker loss."""
    m_clean_reclassify(after)
    m_lost_blocker(after)


def m_lost_blocker(after: dict) -> None:
    """A BLOCKER downgraded, taking the tier with it."""
    rpt = after[LOAN]
    f = _find(rpt, "AUTH-Q5")
    f["ara_metadata"]["native_severity"] = "RISK-SAFETY"
    c = rpt["classification"]
    c["blocker_count"] -= 1
    c["risk_safety_count"] += 1
    c["tier"] = "Remediation Required"
    c["rule_matched"] = "1-2 BLOCKER -> Remediation Required"


def m_gutted(after: dict) -> None:
    """The worst case: all blockers cleared and the repo declared Agent-Ready."""
    rpt = after[LOAN]
    for qid in ("API-Q1", "AUTH-Q1", "AUTH-Q5"):
        f = _find(rpt, qid)
        if f:
            f["ara_metadata"]["native_severity"] = "RISK-QUALITY"
    for f in rpt.get("findings") or []:
        if f.get("ara_metadata", {}).get("native_severity") == "RISK-SAFETY":
            f["ara_metadata"]["native_severity"] = "RISK-QUALITY"
    c = rpt["classification"]
    c["blocker_count"] = 0
    c["risk_safety_count"] = 0
    c["tier"] = "Agent-Ready"
    c["rule_matched"] = "0 BLOCKER, 0 RISK-SAFETY -> Agent-Ready"


def m_dropped_questions(after: dict) -> None:
    """Two rubric questions stop being answered — looks exactly like churn."""
    rpt = after[LOAN]
    drop = {"API-Q1", "AUTH-Q5"}
    rpt["findings"] = [f for f in rpt["findings"] if f.get("question_id") not in drop]
    rpt["evaluations"] = [e for e in rpt["evaluations"] if e.get("question_id") not in drop]


# --- scenarios -------------------------------------------------------------------------
# `band` is the score range this SHOULD land in. Deliberately wide: the point is ordering
# and rough magnitude, not a pinned number an LLM can never hit reproducibly.

SCENARIOS = [
    {
        "name": "no-op-expected",
        "mutate": m_noop,
        "intent": "no rubric change — re-running the harness to confirm the baseline is stable",
        "edited": "",
        "band": (75, 100),
        "note": "An empty delta against an intent that PREDICTED an empty delta. Scores "
                "HIGH: the harness confirmed exactly what was claimed. (My first band here "
                "said 0-40 and the judge scored 95 — the judge was right and the band was "
                "wrong, which is the whole reason this ladder exists.)",
    },
    {
        "name": "no-op-unexpected",
        "mutate": m_noop,
        "intent": "reclassify API-Q2 from RISK-QUALITY to RISK-SAFETY so unauthenticated "
                  "API surfaces stop being filed as mere quality issues",
        "edited": "API-Q2",
        "band": (0, 40),
        "note": "The SAME empty delta against an intent that described a real change. This "
                "must score LOW: an edit that produced no movement usually means it never "
                "took effect (e.g. edited in the AWS Transform service, baselines stale). "
                "Same delta, opposite verdict — the score has to come from intent-vs-delta, "
                "not from delta size alone.",
    },
    {
        "name": "clean-reclassify",
        "mutate": m_clean_reclassify,
        "intent": "reclassify API-Q2 from RISK-QUALITY to RISK-SAFETY because an "
                  "unauthenticated API surface is a safety concern, not a quality one",
        "edited": "API-Q2",
        "band": (75, 100),
        "note": "The ideal MR: intent stated, delta matches exactly, nothing else moved.",
    },
    {
        "name": "stricter-rubric",
        "mutate": m_stricter,
        "intent": "promote DATA-Q1 to BLOCKER — unencrypted PII at rest should stop an "
                  "agent integration outright",
        "edited": "DATA-Q1",
        "band": (70, 100),
        "note": "Tightening the rubric. Must NOT be penalised as a regression — the tier "
                "moved toward LESS agent-ready, which is the safe direction.",
    },
    {
        "name": "risk-safety-drift",
        "mutate": m_risk_safety_drift,
        "intent": "reclassify API-Q2 from RISK-QUALITY to RISK-SAFETY",
        "edited": "API-Q2",
        "band": (0, 45),
        "note": "The stated edit (API-Q2) produced NOTHING while an unrelated question "
                "moved. That is a real mismatch, so a low score is correct — but note there "
                "is no HOLD: the DATA-Q1 drift is tier-inert while blockers remain, so it is "
                "reported without vetoing. Low score, no hold, is the intended combination.",
    },
    {
        "name": "mr14-as-shipped",
        "mutate": m_mr14_as_shipped,
        "intent": "reclassify API-Q2 from RISK-QUALITY to RISK-SAFETY because an "
                  "unauthenticated API surface is a safety concern, not a quality one",
        "edited": "API-Q2",
        "band": (0, 40),
        "note": "THE REGRESSION CASE. Intent achieved, but a BLOCKER was lost and the tier "
                "relaxed. Shipped as LGTM/72 before the safety floor existed.",
    },
    {
        "name": "gutted-rubric",
        "mutate": m_gutted,
        "intent": "simplify severity classes to reduce false positives in the loan calculator",
        "edited": "",
        "band": (0, 25),
        "note": "Worst case: every blocker cleared and the repo declared Agent-Ready under "
                "an innocuous-sounding intent. Must score at the floor.",
    },
    {
        "name": "dropped-questions",
        "mutate": m_dropped_questions,
        "intent": "remove redundant API-Q1 and AUTH-Q5 checks to shorten the rubric",
        "edited": "",
        "band": (0, 40),
        "note": "Coverage gap. Surfaces as removed findings, which is what churn looks "
                "like — the structural guard is the only thing that catches it.",
    },
]


def run_scenario(sc: dict, heuristic: bool, model: str) -> dict:
    before = dr.load_tree(GOLDEN)
    after = copy.deepcopy(before)
    sc["mutate"](after)
    impact = dr.build_impact(before, after)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(impact, fh)
        impact_path = fh.name

    cmd = [sys.executable, str(REPO / "harness" / "judge.py"),
           "--impact", impact_path, "--intent", sc["intent"], "--model", model]
    if sc["edited"]:
        cmd += ["--edited-questions", sc["edited"]]
    if heuristic:
        cmd += ["--no-llm"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    Path(impact_path).unlink(missing_ok=True)
    if proc.returncode != 0:
        return {"error": (proc.stderr or "")[-300:]}
    v = json.loads(proc.stdout)
    return {
        "score": v["score"],
        "verdict": v["verdict"],
        "match": v["intent_match"],
        "hold": bool(v.get("safety_hold")),
        "regression": v["quality_regression"],
        "no_op": bool(v.get("no_op_warning")),
        "alerts": len(impact["safety_alerts"]),
        "material": sum(1 for a in impact["safety_alerts"] if a.get("tier_material", True)),
        "gaps": len(impact["coverage_gaps"]),
        "engine": v.get("_engine"),
        "rationale": v["rationale"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="scenario names to run")
    ap.add_argument("--heuristic", action="store_true",
                    help="skip Bedrock (fast; exercises plumbing only)")
    ap.add_argument("--model", default="global.anthropic.claude-opus-4-5-20251101-v1:0")
    ap.add_argument("--json", action="store_true", help="emit raw results as JSON")
    args = ap.parse_args()

    todo = [s for s in SCENARIOS if not args.only or s["name"] in args.only]
    results = []
    for sc in todo:
        r = run_scenario(sc, args.heuristic, args.model)
        r["name"] = sc["name"]
        r["band"] = sc["band"]
        r["note"] = sc["note"]
        if "error" not in r:
            lo, hi = sc["band"]
            r["in_band"] = lo <= r["score"] <= hi
        results.append(r)
        if not args.json:
            _print_one(r)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    ok = [r for r in results if r.get("in_band")]
    print(f"\n{'=' * 78}\n{len(ok)}/{len(results)} scenarios landed in their expected band.")
    off = [r for r in results if "error" not in r and not r.get("in_band")]
    if off:
        print("\nOUT OF BAND (score needs tuning, or the band was wrong):")
        for r in off:
            print(f"  {r['name']}: scored {r['score']}, expected {r['band'][0]}-{r['band'][1]}")

    # Ordering matters more than any single score: a reviewer reads the number as a ranking.
    scored = [r for r in results if "error" not in r]
    print("\nRANKED (best -> worst):")
    for r in sorted(scored, key=lambda x: -x["score"]):
        flag = " [HOLD]" if r["hold"] else ""
        print(f"  {r['score']:3}  {r['name']}{flag}")
    return 0 if not off else 1


def _print_one(r: dict) -> None:
    print(f"\n{'=' * 78}\n### {r['name']}")
    if "error" in r:
        print(f"  ERROR: {r['error']}")
        return
    mark = "OK " if r.get("in_band") else "OFF"
    print(f"  [{mark}] score {r['score']} (expected {r['band'][0]}-{r['band'][1]})  "
          f"verdict={r['verdict']}  match={r['match']}")
    print(f"  hold={r['hold']}  regression={r['regression']}  no_op={r['no_op']}  "
          f"alerts={r['alerts']} ({r['material']} tier-material)  gaps={r['gaps']}")
    print(f"  expected: {r['note']}")
    print(f"  judge: {r['rationale'][:400]}")


if __name__ == "__main__":
    raise SystemExit(main())
