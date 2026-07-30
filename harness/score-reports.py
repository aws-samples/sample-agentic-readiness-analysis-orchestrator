#!/usr/bin/env python3
"""
score-reports.py — is the ANALYSIS ITSELF any good?

This answers a DIFFERENT question from judge.py, and the distinction is the whole point:

  judge.py       scores a CHANGE:  "does this MR make the analysis better or worse?"
                 Inputs: golden(before) vs after(after) + the MR intent.
                 It never opens a single line of the analyzed repository.

  score-reports.py scores a REPORT: "is what this report says actually TRUE of the repo?"
                 Inputs: the report + the FULL fixture source it was produced from.
                 No baseline, no intent, no delta. Ground truth, not consistency.

So a change can score 92 on judge.py (did exactly what it claimed) while the reports it
produces are confidently wrong — judge.py has no way to notice. That gap is what this
closes, and it is what found the counter defects below.

RUBRIC: the two prompts are the benchmarking team's own ARA / MOD evaluation prompts,
carried verbatim (ARA_RUBRIC / MOD_RUBRIC) so a score here is comparable with theirs
rather than a private invention. They score 0.0-1.0 and weight a MISSED BLOCKER /
missed High finding far above a spurious INFO — the asymmetry we want, since a missed
agent-safety blocker is the expensive error.

The fixture source is small (2-12 KB per repo; shipping-api ~100 KB, monolith ~185 KB),
so the model sees the ENTIRE repository rather than a sample. Groundedness claims here
are checkable, not impressionistic.

DETERMINISTIC PRE-CHECKS run first, with no model at all (`--checks-only`), because
some accuracy failures are pure arithmetic and an LLM should never be asked to
"probably" catch them:
  * severity counters vs. the enumerated findings   <- already found 5 defects
  * ARA tier as a function of blocker/risk_safety counts (SKILL.md 1569-1573)
  * MOD overall_score vs. the mean of its category scores, and its band
  * question coverage: 43 ARA / 37 MOD, each question in EXACTLY one of
    findings|evaluations (never both, never neither)
A deterministic failure is reported as a hard defect regardless of what the model says.

Usage:
  harness/score-reports.py --checks-only            # fast, free, no Bedrock
  harness/score-reports.py                          # full LLM scoring, all 22 reports
  harness/score-reports.py --only legacy-loan-calculator --analysis ara
  harness/score-reports.py --json -o scores.json
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "harness" / "golden"
FIXTURES = REPO / "harness" / "fixtures"

DEFAULT_MODEL = os.environ.get(
    "HARNESS_SCORE_MODEL", "global.anthropic.claude-opus-4-5-20251101-v1:0")

# Rubric sizes. Counted from the reports themselves, NEVER by grepping SKILL.md: MOD's
# DATA-Q* namespace-collision note names ARA's DATA-Q7, which over-counts MOD as 38.
EXPECTED_QUESTIONS = {"ara": 43, "mod": 37}

# ARA tier is a deterministic function of two counts (SKILL.md 1569-1573). Everything
# else (RISK-QUALITY, INFO) is tier-INERT (line 2054).
def expected_ara_tier(blockers: int, risk_safety: int) -> tuple[str, Optional[str]]:
    if blockers >= 3:
        return "Not Agent-Integrable", None
    if blockers >= 1:
        return "Remediation Required", None
    if risk_safety >= 3:
        return "Pilot-Ready", "Safety Concerns"
    if risk_safety >= 1:
        return "Pilot-Ready", None
    return "Agent-Ready", None


# MOD bands over the 1-4 overall_score (SKILL.md line 2014).
def mod_band(score: float) -> str:
    if score >= 3.5:
        return "Mature"
    if score >= 2.5:
        return "Partial"
    if score >= 1.5:
        return "Needs Work"
    return "Not Ready"


# ---------------------------------------------------------------------------------------
# Benchmark rubrics — VERBATIM from the benchmarking team's evaluation prompts.
# Do not paraphrase these: the point is that a score here is comparable with theirs.
# ---------------------------------------------------------------------------------------

ARA_RUBRIC = """\
Evaluate the Agentic Readiness Assessment report found in the GENERATED REPORT OUTPUT section.
Especially focus on **severity consistency** (is the readiness profile — Agent-Ready, Pilot-Ready,
Remediation Required, or Not Agent-Integrable — consistent with the BLOCKER and RISK-SAFETY counts;
`[+]` the tier is a *deterministic* function of those counts, so a tier that contradicts the report's
own BLOCKER/RISK-SAFETY counts is a hard failure, and the `Pilot-Ready (Safety Concerns)` qualifier
must appear exactly when RISK-SAFETY findings are present without a BLOCKER), **evidence quality**
(does each question cite specific files and code patterns from the repository), **service archetype
accuracy** (is the detected archetype correct — stateless-utility, stateful-crud, orchestrator,
data-gateway, or event-processor), **repository classification accuracy** (is the repo_type correct —
libraries should not be asked infrastructure questions; `[+]` and there should be no spurious findings
on questions that are N/A for the repo type), and **agent readiness determination accuracy**.
`[+]` Also verify **question coverage** — all 43 questions across the 8 sections (API Surface, Auth,
State Management, Human-in-the-Loop, Data Accessibility, Discovery & Documentation, Observability,
Engineering Maturity) are resolved, with each question landing in exactly one of findings or
evaluations (never both, never neither). `[+]` Check **conditional-BLOCKER reasoning** — the 5
scope-dependent questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2) escalate to BLOCKER only for
a write-enabled agent scope, so confirm their severity matches the repo's actual agent scope.
`[+]` Confirm **native-severity vocabulary** — findings use BLOCKER / RISK-SAFETY / RISK-QUALITY /
INFO natively and map correctly to the unified High/Medium/Low. `[+]` When scoring, weight a **missed
BLOCKER or RISK-SAFETY** far more heavily than a spurious INFO — a missed agent-safety blocker is the
expensive error. Provide an overall score from 0.0 to 1.0 in the format `<score>X.X</score>` followed
by a brief summary."""

MOD_RUBRIC = """\
Evaluate the Modernization Readiness Assessment report found in the GENERATED REPORT OUTPUT section.
Especially focus on **pathway accuracy** (are the 7 modernization pathways triggered correctly based on
what was actually found in the repository — for example, a repo with no database should not trigger
Move to Managed Databases, and a repo already using containers should not trigger Move to Containers;
`[+]` and each triggered pathway's `triggering_questions[]` must cite the questions that actually drove
it, at the scores that justify the trigger), **evidence quality** (does each question cite specific
files, configs, and code patterns from the repository), **service archetype accuracy** (is the detected
archetype correct — stateless-utility, stateful-crud, orchestrator, data-gateway, or event-processor),
and **repository classification accuracy** (is the repo_type correct — application, library,
infrastructure-only, etc.). Also verify that **recommendation quality** aligns with the triggered
pathways. `[+]` Additionally verify **question coverage** — all 37 questions across the 5 categories
(Infrastructure 11, Application 6, Data 4, Security 7, Operations 9) are resolved, with each question
landing in exactly one of findings or evaluations (never both, never neither). `[+]` Check
**tier and score consistency** — the tier (Cloud-Native Ready / Pilot-Ready / Remediation Required /
Not Ready) is driven by the High/Medium finding counts, so a tier that contradicts those counts is a
hard failure; and the report's own `classification_consistency_check` (which compares the count-based
tier against the score-based band) must itself be correct — a silent divergence is a defect. `[+]`
Check **numeric-band accuracy** — the per-category `numeric_score` / `score_rating` band and the
`overall_score` (0–4) must match the evidence; treat within-band numeric wobble as noise but a
cross-band error (e.g. Needs Work vs Partial) as a defect. `[+]` When scoring, weight a **missed High
finding** heavily. Provide an overall score from 0.0 to 1.0 in the format `<score>X.X</score>`
followed by a brief summary."""

SYSTEM_PROMPT = """You are a strict evaluator of automated code-assessment reports.

You are given (a) the COMPLETE source of a repository and (b) a generated assessment report
about that repository. Judge whether the report is ACCURATE ABOUT THAT SOURCE.

This is a GROUNDEDNESS evaluation. You have the entire repository, so verify claims against
it rather than judging plausibility:
  * A finding citing a file, function, or pattern that does not exist is a FABRICATION.
  * A real, serious problem visible in the source but absent from the report is a MISS —
    and per the rubric a missed BLOCKER / High finding is the expensive error, weighted far
    above a spurious low-severity one.
  * Prose that restates a question without pointing at concrete evidence is WEAK EVIDENCE.

Be skeptical and specific: cite question_ids and file paths. Do not award credit for
confident tone, thorough formatting, or plausible-sounding generic advice. A report can be
fluent, internally consistent, and still wrong about the code.

Note the repositories are deliberately small legacy fixtures. Judge the report against what
is ACTUALLY THERE — do not penalise it for not finding problems the source does not contain,
and do not reward it for findings the source does not support.

Respond with ONLY a JSON object, no prose:
{"score": <float 0.0-1.0>,
 "summary": "<2-4 sentences: is this report accurate about this repo?>",
 "fabrications": [{"question_id": "<id>", "claim": "<what it claimed>",
                   "why_wrong": "<what the source actually shows>"}],
 "misses":       [{"what": "<real issue in the source>", "where": "<file>",
                   "severity_should_be": "BLOCKER|RISK-SAFETY|High|Medium",
                   "why_it_matters": "<...>"}],
 "weak_evidence": ["<question_id: what is missing>"],
 "strengths": ["<what the report got genuinely right, with specifics>"]}"""


# ---------------------------------------------------------------------------------------
# Deterministic pre-checks — no model. A failure here is a fact, not an opinion.
# ---------------------------------------------------------------------------------------

def _native(f: dict) -> Optional[str]:
    return ((f.get("ara_metadata") or {}).get("native_severity"))


def check_ara(rpt: dict) -> list[dict]:
    """Arithmetic that must hold inside any ARA report, independent of the repo."""
    out: list[dict] = []
    findings = rpt.get("findings") or []
    cls = rpt.get("classification") or {}

    # 1. Severity counters vs. the findings actually enumerated.
    #
    # Direction matters: exclusion rules (N/A questions, read-only scope downgrades,
    # not_evaluated_extended) REMOVE questions from the findings list while the counter may
    # still describe the full rubric — so a counter can legitimately be HIGHER than what is
    # enumerated. It can NEVER be LOWER: that means the report enumerated findings it did
    # not count, and nothing in the rubric produces that. So only undercounts are flagged.
    tally: dict[str, int] = {}
    for f in findings:
        n = _native(f)
        if n:
            tally[n] = tally.get(n, 0) + 1
    for cls_name, key in (("BLOCKER", "blocker_count"), ("RISK-SAFETY", "risk_safety_count"),
                          ("RISK-QUALITY", "risk_quality_count"), ("INFO", "info_count")):
        claimed = cls.get(key)
        actual = tally.get(cls_name, 0)
        if isinstance(claimed, int) and claimed < actual:
            out.append({
                "check": "severity_counter_undercount",
                "severity": "high" if cls_name in ("BLOCKER", "RISK-SAFETY") else "medium",
                "detail": f"{key}={claimed} but {actual} findings are natively {cls_name} "
                          f"(undercount by {actual - claimed}; no exclusion rule can lower "
                          f"a counter below the enumerated findings)",
            })

    # 2. Tier vs. its own counts — the tier is arithmetic, so this cannot be a judgement call.
    b, rs = cls.get("blocker_count"), cls.get("risk_safety_count")
    if isinstance(b, int) and isinstance(rs, int):
        want_tier, want_qual = expected_ara_tier(b, rs)
        got_tier = cls.get("tier")
        if got_tier != want_tier:
            out.append({"check": "tier_contradicts_counts", "severity": "critical",
                        "detail": f"tier={got_tier!r} but blocker_count={b}, "
                                  f"risk_safety_count={rs} -> {want_tier!r}"})
        got_qual = cls.get("sub_qualifier")
        # The qualifier must appear EXACTLY when RISK-SAFETY is present without a BLOCKER.
        if want_qual and got_qual != want_qual:
            out.append({"check": "missing_safety_qualifier", "severity": "high",
                        "detail": f"blocker_count=0 and risk_safety_count={rs} requires "
                                  f"sub_qualifier={want_qual!r}, got {got_qual!r}"})
        if got_qual and not want_qual:
            out.append({"check": "spurious_safety_qualifier", "severity": "medium",
                        "detail": f"sub_qualifier={got_qual!r} set but blocker_count={b}, "
                                  f"risk_safety_count={rs} does not call for one"})
    return out


def check_mod(rpt: dict) -> list[dict]:
    out: list[dict] = []
    cats = rpt.get("categories") or []
    scores = [c.get("numeric_score") for c in cats
              if isinstance(c.get("numeric_score"), (int, float))]
    overall = rpt.get("overall_score")

    # overall_score is the EQUALLY-weighted mean of the category scores, regardless of how
    # many questions each category holds.
    if scores and isinstance(overall, (int, float)):
        want = sum(scores) / len(scores)
        if abs(want - overall) > 0.06:      # tolerate publication rounding only
            out.append({"check": "overall_score_not_mean_of_categories", "severity": "high",
                        "detail": f"overall_score={overall} but mean of {len(scores)} "
                                  f"category scores = {want:.2f}"})
        if mod_band(overall) != mod_band(want):
            out.append({"check": "overall_score_band_error", "severity": "critical",
                        "detail": f"overall_score={overall} ({mod_band(overall)}) but the "
                                  f"category mean {want:.2f} bands as {mod_band(want)}"})

    # Each category's own score_rating must match its own number.
    for c in cats:
        ns, sr = c.get("numeric_score"), c.get("score_rating")
        if isinstance(ns, (int, float)) and sr and mod_band(ns) != sr:
            out.append({"check": "category_band_mismatch", "severity": "high",
                        "detail": f"{c.get('category_id')}: numeric_score={ns} bands as "
                                  f"{mod_band(ns)} but score_rating={sr!r}"})
    return out


def check_coverage(rpt: dict, analysis: str) -> list[dict]:
    """Every rubric question in EXACTLY one of findings|evaluations — never both, never neither.

    The benchmark prompts call for this explicitly, and it is the check that catches a
    report quietly answering less of the rubric than it should. `evaluations` and `findings`
    are DISJOINT by design (loan-calculator: 22 + 21 = 43, zero intersection), so the
    covered set is their UNION.
    """
    out: list[dict] = []
    fq = [f.get("question_id") for f in (rpt.get("findings") or []) if f.get("question_id")]
    eq = [e.get("question_id") for e in (rpt.get("evaluations") or []) if e.get("question_id")]
    both = set(fq) & set(eq)
    if both:
        out.append({"check": "question_in_both_findings_and_evaluations", "severity": "high",
                    "detail": f"{len(both)} question(s) resolved twice: "
                              f"{', '.join(sorted(both)[:8])}"})
    dupes = {q for q in fq if fq.count(q) > 1} | {q for q in eq if eq.count(q) > 1}
    if dupes:
        out.append({"check": "duplicate_question_ids", "severity": "medium",
                    "detail": f"repeated ids: {', '.join(sorted(dupes)[:8])}"})
    answered = set(fq) | set(eq)
    want = EXPECTED_QUESTIONS[analysis]
    if len(answered) < want:
        out.append({"check": "incomplete_question_coverage", "severity": "critical",
                    "detail": f"{len(answered)} of {want} rubric questions resolved "
                              f"({want - len(answered)} unanswered)"})
    elif len(answered) > want:
        out.append({"check": "unexpected_question_count", "severity": "low",
                    "detail": f"{len(answered)} questions resolved, rubric defines {want}"})
    return out


def run_checks(rpt: dict, analysis: str) -> list[dict]:
    checks = check_coverage(rpt, analysis)
    checks += check_ara(rpt) if analysis == "ara" else check_mod(rpt)
    return checks


# ---------------------------------------------------------------------------------------
# LLM scoring
# ---------------------------------------------------------------------------------------

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".idea", "target", "build",
              # PRIOR ANALYSIS OUTPUT IS NOT SOURCE. legacy-shipping-api has a previously
              # generated MOD report committed under services/<repo>/<analysis>/ — 93 KB,
              # 89% of that fixture. Including it let the scorer grade a report against a
              # near-copy of itself: the model cited a "Reference report" nobody gave it,
              # called five findings fabrications for disagreeing with that stale file, and
              # both shipping-api scores came out as the only outliers in the set (ARA 0.52
              # vs 0.72-0.82, MOD 0.55 vs 0.82-0.92). Groundedness must be judged against
              # CODE, never against another verdict.
              "modernization-readiness-analysis", "agentic-readiness-analysis"}

# Same reason, by filename: a report can be dropped anywhere in a fixture tree.
_SKIP_NAME_RE = re.compile(r"-(ara|mod)-report\.(json|md)$")


def load_source(repo: str, max_bytes: int = 220_000) -> str:
    """Concatenate the fixture source. Small enough to send whole — that is what makes
    groundedness checkable rather than impressionistic."""
    root = FIXTURES / "monolith" if repo == "monolith" else FIXTURES / "portfolio" / repo
    if not root.exists():
        return ""
    parts, total = [], 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(d in p.parts for d in _SKIP_DIRS):
            continue
        if _SKIP_NAME_RE.search(p.name):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = p.relative_to(root)
        if total + len(text) > max_bytes:
            parts.append(f"\n----- {rel} (TRUNCATED) -----\n{text[:max(0, max_bytes - total)]}")
            break
        parts.append(f"\n----- {rel} -----\n{text}")
        total += len(text)
    return "".join(parts)


def build_prompt(repo: str, analysis: str, rpt: dict, source: str, checks: list[dict]) -> str:
    rubric = ARA_RUBRIC if analysis == "ara" else MOD_RUBRIC
    # Hand the model the deterministic findings rather than hoping it recomputes them.
    # They are FACTS; asking an LLM to verify arithmetic it can already be told is waste,
    # and a model that misses one would understate a confirmed defect.
    if checks:
        cnote = ("\n## Deterministic pre-checks (already computed — these are FACTS, not "
                 "claims to re-verify)\nThese failed on this report. Treat each as "
                 "established and weight it in your score:\n"
                 + "\n".join(f"  ! [{c['severity']}] {c['check']}: {c['detail']}"
                             for c in checks) + "\n")
    else:
        cnote = ("\n## Deterministic pre-checks\nAll structural checks PASSED (question "
                 "coverage complete, counters consistent, tier/score arithmetic correct). "
                 "Judge the report on GROUNDEDNESS against the source below.\n")
    return (
        f"## Evaluation rubric\n{rubric}\n"
        f"{cnote}"
        f"\n## COMPLETE REPOSITORY SOURCE — {repo}\n"
        f"(this is the entire repository; verify the report's claims against it)\n"
        f"{source or '(source unavailable)'}\n"
        f"\n## GENERATED REPORT OUTPUT\n"
        f"{json.dumps(rpt, indent=1)}\n"
        f"\nReturn the JSON verdict now."
    )


def score_with_bedrock(prompt: str, model: str) -> Optional[dict]:
    try:
        import boto3  # noqa: PLC0415
    except ImportError:
        return None
    try:
        client = boto3.client("bedrock-runtime",
                              region_name=os.environ.get("AWS_REGION", "us-east-1"))
        resp = client.invoke_model(modelId=model, body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }))
        payload = json.loads(resp["body"].read())
        text = "".join(b.get("text", "") for b in payload.get("content", []))
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return {"error": f"no JSON in response: {text[:200]}"}
        return json.loads(m.group(0))
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"[:300]}


def score_report(repo: str, analysis: str, model: str, checks_only: bool) -> dict:
    path = GOLDEN / f"{repo}-{analysis}-report.json"
    rpt = json.loads(path.read_text(encoding="utf-8"))
    checks = run_checks(rpt, analysis)
    row: dict[str, Any] = {
        "repo": repo, "analysis": analysis,
        "checks_failed": checks,
        "n_findings": len(rpt.get("findings") or []),
        "n_evaluations": len(rpt.get("evaluations") or []),
    }
    if analysis == "ara":
        cls = rpt.get("classification") or {}
        row["tier"] = cls.get("tier")
        row["blockers"] = cls.get("blocker_count")
    else:
        row["overall_score"] = rpt.get("overall_score")
        row["band"] = (mod_band(rpt["overall_score"])
                       if isinstance(rpt.get("overall_score"), (int, float)) else None)
    if checks_only:
        return row
    verdict = score_with_bedrock(
        build_prompt(repo, analysis, rpt, load_source(repo), checks), model)
    if verdict is None:
        row["error"] = "boto3 unavailable"
    elif "error" in verdict:
        row["error"] = verdict["error"]
    else:
        row.update({
            "score": verdict.get("score"),
            "summary": verdict.get("summary", ""),
            "fabrications": verdict.get("fabrications") or [],
            "misses": verdict.get("misses") or [],
            "weak_evidence": verdict.get("weak_evidence") or [],
            "strengths": verdict.get("strengths") or [],
        })
    return row


def discover() -> list[tuple[str, str]]:
    units = []
    for p in sorted(GOLDEN.glob("*-report.json")):
        m = re.match(r"(.+)-(ara|mod)-report\.json$", p.name)
        if not m:
            continue
        repo = m.group(1)
        # Portfolio roll-ups are deliberately EXCLUDED: two identical-input runs produced
        # 368 -> 155 findings and 11 -> 5 services, so count- and text-level scoring is
        # meaningless there. A portfolio scorer must be categorical/ordinal only.
        if repo.startswith("harness-portfolio"):
            continue
        units.append((repo, m.group(2)))
    return units


def main() -> int:
    ap = argparse.ArgumentParser(description="Score report ACCURACY against fixture source")
    ap.add_argument("--only", nargs="*", help="repo names to score")
    ap.add_argument("--analysis", choices=["ara", "mod"], help="restrict to one analysis")
    ap.add_argument("--checks-only", action="store_true",
                    help="deterministic checks only — no Bedrock, instant, free")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--jobs", type=int, default=4, help="concurrent Bedrock calls")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--out", type=Path, help="also write results as JSON here")
    args = ap.parse_args()

    units = [(r, a) for r, a in discover()
             if (not args.only or r in args.only)
             and (not args.analysis or a == args.analysis)]
    if not units:
        print("no matching reports", file=sys.stderr)
        return 2

    if args.checks_only:
        rows = [score_report(r, a, args.model, True) for r, a in units]
    else:
        print(f"scoring {len(units)} reports with {args.model} "
              f"({args.jobs} concurrent)...", file=sys.stderr)
        rows = [None] * len(units)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(score_report, r, a, args.model, False): i
                    for i, (r, a) in enumerate(units)}
            for fut in concurrent.futures.as_completed(futs):
                i = futs[fut]
                try:
                    rows[i] = fut.result()
                except Exception as exc:  # noqa: BLE001
                    rows[i] = {"repo": units[i][0], "analysis": units[i][1],
                               "error": f"{type(exc).__name__}: {exc}"[:200]}
                print(f"  done {units[i][0]} {units[i][1]}", file=sys.stderr)
        rows = [r for r in rows if r]

    if args.out:
        args.out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        _report(rows, args.checks_only)
    return 0


def _report(rows: list[dict], checks_only: bool) -> None:
    for a in ("ara", "mod"):
        sub = [r for r in rows if r["analysis"] == a]
        if not sub:
            continue
        print(f"\n{'=' * 78}\n{a.upper()}  ({len(sub)} reports)\n{'=' * 78}")
        hdr = f"{'repo':<28} {'score':>6} {'checks':>7}  detail"
        print(hdr)
        for r in sorted(sub, key=lambda x: (x.get("score") is None, x.get("score") or 0)):
            sc = "—" if r.get("score") is None else f"{r['score']:.2f}"
            nbad = len(r.get("checks_failed") or [])
            flag = "PASS" if not nbad else f"{nbad} FAIL"
            extra = (f"tier={r.get('tier')} blockers={r.get('blockers')}" if a == "ara"
                     else f"score={r.get('overall_score')} band={r.get('band')}")
            if r.get("error"):
                extra += f"  ERROR: {r['error'][:60]}"
            print(f"{r['repo']:<28} {sc:>6} {flag:>7}  {extra}")

        scored = [r["score"] for r in sub if isinstance(r.get("score"), (int, float))]
        if scored:
            print(f"\n  mean accuracy score: {sum(scored) / len(scored):.2f}   "
                  f"range {min(scored):.2f}-{max(scored):.2f}")

    bad = [(r, c) for r in rows for c in (r.get("checks_failed") or [])]
    print(f"\n{'=' * 78}\nDETERMINISTIC DEFECTS: {len(bad)} across "
          f"{len({r['repo'] + r['analysis'] for r, _ in bad})} reports\n{'=' * 78}")
    for r, c in sorted(bad, key=lambda x: x[1]["severity"]):
        print(f"  [{c['severity']:<8}] {r['repo']} ({r['analysis'].upper()}) "
              f"{c['check']}\n             {c['detail']}")

    if checks_only:
        print("\n(deterministic checks only — re-run without --checks-only for "
              "groundedness scoring against the fixture source)")
        return
    for r in rows:
        if not (r.get("fabrications") or r.get("misses")):
            continue
        print(f"\n--- {r['repo']} ({r['analysis'].upper()}) score "
              f"{r.get('score')} ---")
        print(f"  {r.get('summary', '')}")
        for f in r.get("fabrications") or []:
            print(f"  FABRICATION {f.get('question_id')}: {f.get('why_wrong')}")
        for m in r.get("misses") or []:
            print(f"  MISS [{m.get('severity_should_be')}] {m.get('where')}: {m.get('what')}")


if __name__ == "__main__":
    raise SystemExit(main())
