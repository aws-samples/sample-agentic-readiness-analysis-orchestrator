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

RUBRIC: ARA_RUBRIC / MOD_RUBRIC started as the benchmarking team's own evaluation prompts,
carried verbatim so a score here would be comparable with theirs. They are no longer
verbatim — we own them now, and two factual errors against our TDs were corrected (see
the comments above each). They score 0.0-1.0 and weight a MISSED BLOCKER / missed High
finding above a spurious INFO — the asymmetry we want, since a missed agent-safety
blocker is the expensive error.

THE RUBRIC IS NOT SELF-SUFFICIENT, and assuming it was cost us ~0.04-0.08 of ARA score.
A ~2 KB rubric summary does not tell the model which of the 43 questions owns what, so
handed a legacy repo full of SQL injection it fell back on general AppSec instinct and
demanded BLOCKER for 6 findings the reports had correctly filed under DATA-Q4 (which is
RISK-QUALITY *by definition*, and whose own "look for" list includes parameterized
queries). It was grading against a rubric it had never been shown. ARA_CONTEXT /
MOD_CONTEXT close that: the authoritative question->severity table, the scope boundary,
and the tier arithmetic, extracted from SKILL.md. They are ADDITIVE context, not scoring
policy — the rubric still decides what matters.

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
# Evaluation rubrics. These began as the benchmarking team's prompts, carried verbatim for
# comparability. That is no longer true and the divergence is deliberate: the originals
# contained statements that are FACTUALLY WRONG about our TDs, so carrying them verbatim
# bought a grader validating against a spec that does not exist. Each fix is marked
# `[fix]` with the SKILL.md line that governs. This corrected text is what we send back to
# the benchmarking team — their scores are affected by the same errors.
#
# Everything NOT marked `[fix]` is still their wording. Keep it that way: paraphrasing for
# taste re-opens the comparability gap for no benefit.
# ---------------------------------------------------------------------------------------

ARA_RUBRIC = """\
Evaluate the Agentic Readiness Assessment report found in the GENERATED REPORT OUTPUT section.
Especially focus on **severity consistency** (is the readiness profile — Agent-Ready, Pilot-Ready,
Remediation Required, or Not Agent-Integrable — consistent with the BLOCKER and RISK-SAFETY counts;
`[+]` the tier is a *deterministic* function of those counts, so a tier that contradicts the report's
own BLOCKER/RISK-SAFETY counts is a hard failure, and the `Pilot-Ready (Safety Concerns)` qualifier
must appear exactly when `blocker_count` is 0 AND `risk_safety_count` >= 3 — at 1-2 RISK-SAFETY with
no BLOCKER the correct tier is plain `Pilot-Ready` with NO qualifier), **evidence quality**
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
expensive error. `[fix]` But a missed BLOCKER means a question the rubric assigns BLOCKER severity that
the report failed to resolve — NOT a finding you would personally have rated higher. If the report
resolved the issue under the question that owns it, at that question's rubric severity, it is CORRECT
and must not be recorded as a miss. Judge severity against the AUTHORITATIVE SEVERITY TABLE below, not
against general application-security intuition. Provide an overall score from 0.0 to 1.0 in the format
`<score>X.X</score>` followed by a brief summary."""

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
`overall_score` must match the evidence; treat within-band numeric wobble as noise but a
cross-band error (e.g. Needs Work vs Partial) as a defect. `[fix]` The scale is **1-4, not 0-4**: 1 is
the floor and means "missing entirely or fundamentally inadequate", so a repo scoring 1.0-1.2 is at the
bottom of the scale, not the bottom fifth of it. `[+]` When scoring, weight a **missed High
finding** heavily. `[fix]` But a missed High means a question the rubric would score 1-2 that the report
failed to resolve or scored materially too high — NOT a finding you would personally have weighted more.
A question resolved at a defensible score, citing real evidence, is CORRECT even if you would have
scored it one step lower; that is within-band wobble. Provide an overall score from 0.0 to 1.0 in the
format `<score>X.X</score>` followed by a brief summary."""

# ---------------------------------------------------------------------------------------
# Authoritative TD context. NOT scoring policy — this is the spec the rubric refers to.
# Extracted from definitions/managed/*/SKILL.md; regenerate if the TDs change (the
# question->severity table comes from the `#### <QID>: <title> — <severity>` headings).
# ---------------------------------------------------------------------------------------

ARA_CONTEXT = """\
## Authoritative ARA severity table (from the TD — this is the spec, not a suggestion)

SCOPE BOUNDARY: ARA is a design-time architecture review. It evaluates whether controls
exist in code and configuration. It is NOT a penetration test, a runtime security scan, or
a CVE audit. Findings are scored by which rubric question owns them, at that question's
assigned severity. "This is a serious vulnerability" is not by itself grounds for BLOCKER.

Each question below has ONE assigned severity. A report that resolves an issue under the
owning question at that severity is CORRECT.

BLOCKER (7): API-Q1 Documented API Interface · AUTH-Q1 Machine Identity Authentication ·
  API-Q4 Idempotent Writes [C] · AUTH-Q6 Immutable Audit Logging [C] ·
  STATE-Q1 Compensation and Rollback [C] · DATA-Q1 Sensitive Data Classification [C] ·
  DATA-Q2 Data Residency [C]
RISK-SAFETY (12): AUTH-Q2 Scoped Permissions · AUTH-Q3 Action-Level Authorization ·
  AUTH-Q4 Identity Propagation · AUTH-Q5 Credential Management ·
  AUTH-Q7 Agent Identity Suspension · STATE-Q4 Circuit Breakers ·
  STATE-Q5 Rate Limiting · DATA-Q6 PII Redaction in Logs ·
  STATE-Q3 Concurrency Controls [S] · STATE-Q6 Blast Radius [S] ·
  HITL-Q1 Draft/Pending State [S] · HITL-Q2 Approval Gates [S]
RISK-QUALITY (17): API-Q2 · API-Q3 · API-Q6 · STATE-Q2 · STATE-Q7 · HITL-Q3 · DATA-Q3 ·
  DATA-Q4 Input Validation and Schema Enforcement · DATA-Q5 · DISC-Q1 · OBS-Q1 · OBS-Q2 ·
  ENG-Q1 · ENG-Q2 · ENG-Q3 · ENG-Q4 · ENG-Q5 Encryption at Rest
INFO (7): API-Q5 · API-Q7 · API-Q8 · DATA-Q7 · DISC-Q2 · DISC-Q3 · OBS-Q3

[C] = CONDITIONAL BLOCKER: resolves to BLOCKER only when `agent_scope` is "write-enabled".
      Under "read-only" (the TD's DEFAULT, chosen deliberately to avoid false escalation)
      these resolve to RISK-SAFETY or INFO, and that is CORRECT — not an understatement.
[S] = SCOPE-CALIBRATED: counts as RISK-SAFETY when write-enabled, downgrades to INFO under
      read-only scope. A report marking these not-evaluated under read-only scope is
      following the TD.

INJECTION, INPUT-HANDLING AND VALIDATION DEFECTS — READ THIS BEFORE RECORDING A MISS.
SQL injection, NoSQL injection, XXE, command injection, path traversal and unvalidated
input are owned by **DATA-Q4, which is RISK-QUALITY**. DATA-Q4's own evaluation criteria
list "parameterized queries (protection against injection)" as a thing to look for. So a
report that files SQL injection under DATA-Q4 as RISK-QUALITY has applied the rubric
CORRECTLY. Do NOT record it as a missed BLOCKER or missed RISK-SAFETY, and do not
double-count one root cause across several question_ids.

NOT COVERED BY ANY OF THE 43 QUESTIONS — do not penalise their absence:
transport security / TLS / HTTPS-vs-HTTP in transit (ENG-Q5 is encryption AT REST only),
session fixation and session-token rotation, end-of-life runtime or dependency CVEs,
and secrets committed to source control except where AUTH-Q5 Credential Management
genuinely owns the agent-facing credential path. These are real problems and legitimate
TD coverage gaps, but a report cannot be marked down for a question the rubric lacks. If
you notice one, list it under `rubric_gaps`, NOT under `misses`.

TIER ARITHMETIC (deterministic — already verified for you in the pre-checks):
  blocker_count >= 3                      -> Not Agent-Integrable
  blocker_count 1-2                       -> Remediation Required
  blocker_count 0 AND risk_safety >= 3    -> Pilot-Ready + "Safety Concerns" qualifier
  blocker_count 0 AND risk_safety 1-2     -> Pilot-Ready (NO qualifier)
  blocker_count 0 AND risk_safety 0       -> Agent-Ready
RISK-QUALITY and INFO counts are tier-INERT — they never change the tier."""

MOD_CONTEXT = """\
## Authoritative MOD scoring context (from the TD — this is the spec)

SCALE: every question and category scores **1-4**. There is no 0.
  4 Mature      — fully meets the criterion, best-practice implementation
  3 Partial     — partially meets it, minor gaps, functional but improvable
  2 Needs Work  — exists but significant gaps
  1 Not Ready   — missing entirely or fundamentally inadequate
A repo scoring 1.0-1.2 overall is at the FLOOR of the scale. That is an expected result for
an unmodernized legacy fixture, not evidence the report is wrong.

37 questions in 5 categories: INF Infrastructure/Platform/DevOps (11) ·
APP Application Architecture (6) · DATA Data Platform (4) · SEC Security Baseline (7) ·
OPS Operations & Observability (9).

`overall_score` is the EQUALLY-weighted mean of the 5 category scores, regardless of how
many questions each category holds. (Already verified in the pre-checks.)

TWO LADDERS, and they are different things — do not conflate them:
  * score-based BANDS from `overall_score`: >=3.5 Mature · 2.5-3.4 Partial ·
    1.5-2.4 Needs Work · <1.5 Not Ready
  * count-based TIERS from unified High/Medium counts: 0 High and <=1 Medium ->
    Cloud-Native Ready · 0 High and >=2 Medium -> Pilot-Ready · 1 High -> Pilot-Ready ·
    2-11 High -> Remediation Required · >=12 High -> Not Ready
`classification_consistency_check` is the report comparing those two ladders against each
other; a divergence it declares openly is the TD working as designed, not a defect.
MOD has NO sub-qualifier — "Safety Concerns" is ARA-only.

MOD classification is deliberately SOFTER than ARA on "1 High": ARA gates on agent safety
so one High blocks deployment, whereas MOD measures modernization maturity where one High
is typically a single modernization gap. Do not import ARA's severity instincts here.

MOD measures MODERNIZATION MATURITY, not application security. Code-level vulnerabilities
are ARA's or a SAST tool's concern except where a SEC question genuinely owns them."""

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

YOU ARE GRADING RUBRIC APPLICATION, NOT RE-DOING THE ASSESSMENT YOURSELF. The report was
produced by answering a FIXED question set at FIXED severities, given to you below as the
authoritative severity table. Grade whether it applied that rubric correctly and grounded
its answers in real code. Three consequences, and they are the difference between a fair
score and a harsh one:
  1. A finding resolved under the question that OWNS it, at THAT question's severity, is
     CORRECT — even if you would personally have rated the underlying issue higher. That
     is not a miss. It is not an understatement. Record nothing.
  2. A real problem the rubric has NO question for is a RUBRIC GAP, not a report miss. Put
     it in `rubric_gaps`. The report cannot answer a question it was never asked, and
     penalising it there measures the rubric, not the report.
  3. One root cause is ONE item. Do not count the same underlying defect once per
     question_id it touches.
Only record a MISS when a question the rubric DOES cover was left unresolved, resolved at
the wrong severity per the table, or answered with evidence the source contradicts.

Be skeptical and specific: cite question_ids and file paths. Do not award credit for
confident tone, thorough formatting, or plausible-sounding generic advice. A report can be
fluent, internally consistent, and still wrong about the code.

Note the repositories are deliberately small legacy fixtures. Judge the report against what
is ACTUALLY THERE — do not penalise it for not finding problems the source does not contain,
and do not reward it for findings the source does not support. A legacy fixture landing at
the bottom of the scale is very often the CORRECT answer; scoring it that way is accuracy,
not leniency, and a report is not more accurate for being harsher about its repo.

CALIBRATION. Score how ACCURATE the report is, not how bad the repo is:
  0.90-1.00  no fabrications, no covered-question misses, evidence is concrete and checks out
  0.75-0.89  accurate overall; minor weak evidence or one debatable severity call
  0.55-0.74  a real defect — a covered question missed or a demonstrably wrong severity
  0.30-0.54  multiple real defects, or a fabrication that changes the conclusion
  0.00-0.29  the report is substantially wrong about this repository
A report with nothing in `fabrications` and nothing in `misses` after applying rules 1-3
belongs at 0.90+. Do not reserve the top of the range for reports that cannot exist.

Respond with ONLY a JSON object, no prose:
{"score": <float 0.0-1.0>,
 "summary": "<2-4 sentences: is this report accurate about this repo?>",
 "fabrications": [{"question_id": "<id>", "claim": "<what it claimed>",
                   "why_wrong": "<what the source actually shows>"}],
 "misses":       [{"what": "<real issue in the source>", "where": "<file>",
                   "question_id": "<the rubric question that OWNS it — required>",
                   "severity_should_be": "BLOCKER|RISK-SAFETY|High|Medium",
                   "why_it_matters": "<...>"}],
 "rubric_gaps":  [{"what": "<real issue no rubric question covers>", "where": "<file>",
                   "why_no_question_fits": "<...>"}],
 "weak_evidence": ["<question_id: what is missing>"],
 "strengths": ["<what the report got genuinely right, with specifics>"]}

Every entry in `misses` MUST name the question_id that owns it. If you cannot name one from
the severity table, it belongs in `rubric_gaps` instead."""


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
    context = ARA_CONTEXT if analysis == "ara" else MOD_CONTEXT
    # Hand the model the deterministic findings rather than hoping it recomputes them.
    # They are FACTS; asking an LLM to verify arithmetic it can already be told is waste,
    # and a model that misses one would understate a confirmed defect.
    #
    # But do NOT ask it to re-weight them into its score. These defects are already
    # reported on their own axis (`checks_failed`), so scoring them again bills one bug
    # twice. That double charge was visible in the v1 baseline: 5 of the 6 ARA reports at
    # 0.72 had a failed check and NONE of the 5 above 0.72 did — the counter undercount
    # was doing the work of a groundedness defect it has nothing to do with.
    if checks:
        cnote = ("\n## Deterministic pre-checks (already computed — these are FACTS, not "
                 "claims to re-verify)\nThese failed on this report:\n"
                 + "\n".join(f"  ! [{c['severity']}] {c['check']}: {c['detail']}"
                             for c in checks)
                 + "\nThese are structural defects, ALREADY RECORDED AND REPORTED on a "
                   "separate axis. Do NOT deduct for them again — that would bill one "
                   "defect twice. Use them only as context. Your score measures "
                   "GROUNDEDNESS: is the report's substance true of the source below?\n")
    else:
        cnote = ("\n## Deterministic pre-checks\nAll structural checks PASSED (question "
                 "coverage complete, counters consistent, tier/score arithmetic correct). "
                 "Judge the report on GROUNDEDNESS against the source below.\n")
    return (
        f"## Evaluation rubric\n{rubric}\n"
        f"\n{context}\n"
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
            # Real problems no rubric question covers. Kept OUT of `misses` on purpose:
            # these measure the TD's coverage, not the report's accuracy, and conflating
            # them is what let the rubric's own blind spots depress report scores.
            "rubric_gaps": verdict.get("rubric_gaps") or [],
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
