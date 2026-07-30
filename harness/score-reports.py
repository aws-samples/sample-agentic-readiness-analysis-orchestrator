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
queries). It was grading against a rubric it had never been shown. ara_context() /
mod_context() close that: the authoritative question->severity table, the scope boundary,
and the tier arithmetic. They are ADDITIVE context, not scoring policy — the rubric still
decides what matters.

Those tables are PARSED FROM SKILL.md ON EVERY RUN, not transcribed. A transcribed table
goes stale the moment someone edits a severity, and it goes stale SILENTLY — the prompt
would keep asserting the old severity as authoritative and the scorer would confidently
mark a correct report wrong. Since the TD is exactly the thing under change here, that is
the one kind of staleness this harness cannot afford. The parse asserts 43/37 and raises
if the heading format moves, so a TD edit that breaks it stops the run instead of quietly
handing the model a table with holes in it.

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

ONE REPORT TREE IS A DRAW, NOT A MEASUREMENT. What we are measuring is TD OUTPUT QUALITY,
and the TD prompt is fixed — the analysis agent is what varies, by 10-20 findings per
fixture per rerun. So a single tree cannot separate "the TD got better" from "the agent
rolled differently", which is the entire judgement this harness exists to support. Measured
on two independent ARA trees, 5 of 11 fixtures moved and the worst moved 0.10 — the same
magnitude as the ARA-vs-MOD gap we had been reading as a real signal.

Pass several trees with `--trees` and every row carries mean/stddev/spread. The published
TDs deserve an honest number: a claimed improvement smaller than the spread has not been
measured. Note the samples must be separate ANALYSIS RUNS (run-fixtures.sh into different
--after-dir targets); re-scoring one report N times only measures the scorer's own jitter
and reports a false precision.

Usage:
  harness/score-reports.py --checks-only            # fast, free, no Bedrock
  harness/score-reports.py                          # full LLM scoring, all 22 reports
  harness/score-reports.py --only legacy-loan-calculator --analysis ara
  harness/score-reports.py --trees harness/_run1 harness/_run2 harness/_run3   # mean+spread
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
# The committed record of how accurate the golden tree is. Regenerate it with
# --update-baseline whenever the goldens are re-baselined; read it for free with
# --show-baseline.
BASELINE = REPO / "harness" / "golden-accuracy-baseline.json"

DEFAULT_MODEL = os.environ.get(
    "HARNESS_SCORE_MODEL", "global.anthropic.claude-opus-4-5-20251101-v1:0")

# The question/severity table, the rubric sizes and the tier/band arithmetic all live in
# skill_table.py, shared with diff-reports.py and the judge. Importing rather than
# re-deriving is the whole point: two copies of the severity table drift silently, and this
# grader and the differ disagreeing about what AUTH-Q5 is would be invisible until a verdict
# came out wrong.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_table import (  # noqa: E402
    EXPECTED_QUESTIONS, SKILLS, expected_ara_tier, mod_band, parse_questions, rel as _rel,
)


def _tier_ladder() -> str:
    """Render the ARA tier table FROM expected_ara_tier() rather than restating it.

    The arithmetic already lives in two places (SKILL.md:1569-1573 and that function);
    typing it a third time into a prompt is how the prompt ends up disagreeing with the
    checker it is supposed to agree with.
    """
    rows = [(3, 0), (1, 0), (0, 3), (0, 1), (0, 0)]
    labels = {(3, 0): "blocker_count >= 3", (1, 0): "blocker_count 1-2",
              (0, 3): "blocker_count 0 AND risk_safety >= 3",
              (0, 1): "blocker_count 0 AND risk_safety 1-2",
              (0, 0): "blocker_count 0 AND risk_safety 0"}
    lines = []
    for b, rs in rows:
        tier, qual = expected_ara_tier(b, rs)
        got = f"{tier} + \"{qual}\" qualifier" if qual else f"{tier}"
        if not qual and b == 0 and rs:
            got += " (NO qualifier)"
        lines.append(f"  {labels[(b, rs)]:<40} -> {got}")
    return "\n".join(lines)


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
#
# The FACTUAL half is DERIVED from SKILL.md at runtime (question->severity table,
# conditional markers, tier arithmetic). Hardcoding it would go stale silently the moment
# someone edits a severity — the exact drift this harness exists to catch — and it is also
# how the prompt ends up disagreeing with check_ara().
#
# The POLICY half below stays hand-written, because SKILL.md cannot state it about itself:
#   * which real problems NO question covers (negative space — a TD cannot enumerate its
#     own blind spots)
#   * that a severity disagreement is not a miss, and one root cause is one item
#   * the calibration bands
# Those are judging policy, not TD facts. Keep the two separated: policy is ours to tune,
# facts are the TD's to declare.
# ---------------------------------------------------------------------------------------

# Which questions own the vulnerability classes a general-purpose grader over-escalates.
# Derived qid -> the note appended to it. Written by hand because it encodes what we LEARNED
# about grader failure modes, not anything SKILL.md declares.
_OWNERSHIP_NOTES = {
    "DATA-Q4": "OWNS SQL injection, NoSQL injection, XXE, command injection, path "
               "traversal and unvalidated input. Its own evaluation criteria list "
               "\"parameterized queries (protection against injection)\".",
    "ENG-Q5":  "Encryption AT REST only — NOT transport security.",
    "AUTH-Q5": "Credential management, including hardcoded secrets.",
}


def _severity_block(qs: dict[str, dict[str, str]]) -> str:
    """Group questions by severity, newest-longest first, with conditional markers."""
    order = ["BLOCKER", "RISK-SAFETY", "RISK-QUALITY", "INFO"]
    by_sev: dict[str, list[str]] = {s: [] for s in order}
    for qid, q in qs.items():
        sev = q["severity"]
        if sev not in by_sev:
            by_sev.setdefault(sev, [])
        mark = " [C]" if q["conditional"] and sev == "BLOCKER" else (
            " [S]" if q["conditional"] else "")
        note = _OWNERSHIP_NOTES.get(qid)
        entry = f"{qid} {q['title']}{mark}"
        if note:
            entry += f"\n      -> {note}"
        by_sev[sev].append(entry)
    out = []
    for sev in list(order) + [s for s in by_sev if s not in order]:
        items = by_sev.get(sev)
        if not items:
            continue
        out.append(f"{sev} ({len(items)}):")
        out += [f"  - {i}" for i in items]
    return "\n".join(out)


def ara_context() -> str:
    qs = parse_questions("ara")
    # Fail LOUDLY. A parse that silently yields 41 hands the model a table with two
    # questions missing and it fills the hole by guessing — which is the original bug.
    # score-reports.py is not in CI, so this assertion is the only thing standing between a
    # TD heading-format change and a quietly wrong prompt.
    want = EXPECTED_QUESTIONS["ara"]
    assert len(qs) == want, (
        f"ARA severity table parse yielded {len(qs)} questions, expected {want}. The "
        f"'#### <QID>: <title> — <SEVERITY>' heading format in {_rel(SKILLS['ara'])} has "
        f"probably changed. Fix _Q_HEADING before scoring — do NOT score with a partial "
        f"table.")
    return f"""\
## Authoritative ARA severity table (parsed from {_rel(SKILLS['ara'])} — the spec)

SCOPE BOUNDARY: ARA is a design-time architecture review. It evaluates whether controls
exist in code and configuration. It is NOT a penetration test, a runtime security scan, or
a CVE audit. Findings are scored by which rubric question owns them, at that question's
assigned severity. "This is a serious vulnerability" is not by itself grounds for BLOCKER.

Each question below has ONE assigned severity. A report that resolves an issue under the
owning question at that severity is CORRECT.

{_severity_block(qs)}

[C] = CONDITIONAL BLOCKER: resolves to BLOCKER only when `agent_scope` is "write-enabled".
      Under "read-only" (the TD's DEFAULT, chosen deliberately to avoid false escalation)
      these resolve to RISK-SAFETY or INFO, and that is CORRECT — not an understatement.
[S] = SCOPE-CALIBRATED: counts as RISK-SAFETY when write-enabled, downgrades to INFO under
      read-only scope. A report marking these not-evaluated under read-only scope is
      following the TD.

INJECTION, INPUT-HANDLING AND VALIDATION DEFECTS — READ THIS BEFORE RECORDING A MISS.
Injection and traversal defects are owned by DATA-Q4, whose severity is listed above. A
report that files SQL injection under DATA-Q4 at that severity has applied the rubric
CORRECTLY. Do NOT record it as a missed BLOCKER or missed RISK-SAFETY, and do not
double-count one root cause across several question_ids.

NOT COVERED BY ANY OF THE {want} QUESTIONS — do not penalise their absence:
transport security / TLS / HTTPS-vs-HTTP in transit, session fixation and session-token
rotation, end-of-life runtime or dependency CVEs, and secrets committed to source control
except where AUTH-Q5 Credential Management genuinely owns the agent-facing credential
path. These are real problems and legitimate TD coverage gaps, but a report cannot be
marked down for a question the rubric lacks. If you notice one, list it under
`rubric_gaps`, NOT under `misses`.

TIER ARITHMETIC (deterministic — already verified for you in the pre-checks):
{_tier_ladder()}
RISK-QUALITY and INFO counts are tier-INERT — they never change the tier."""


def mod_context() -> str:
    qs = parse_questions("mod")
    want = EXPECTED_QUESTIONS["mod"]
    assert len(qs) == want, (
        f"MOD question parse yielded {len(qs)} questions, expected {want}. Note INF-Q1 "
        f"appears TWICE in {_rel(SKILLS['mod'])} and must be deduped by qid; a naive parse "
        f"returns 38.")
    # MOD headings carry no severity — questions score 1-4 — so list them by category to
    # give the grader the shape of the rubric without inventing severities it does not have.
    cats: dict[str, list[str]] = {}
    for qid, q in qs.items():
        cats.setdefault(qid.split("-")[0], []).append(f"{qid} {q['title']}")
    catlines = "\n".join(f"{c} ({len(v)}): " + " · ".join(v) for c, v in cats.items())
    bands = "\n".join(
        f"    {lo:>4} - {hi:<4} -> {mod_band(lo)}"
        for lo, hi in ((3.5, 4.0), (2.5, 3.4), (1.5, 2.4), (1.0, 1.4)))
    return f"""\
## Authoritative MOD scoring context (parsed from {_rel(SKILLS['mod'])} — the spec)

SCALE: every question and category scores **1-4**. There is no 0.
  4 Mature      — fully meets the criterion, best-practice implementation
  3 Partial     — partially meets it, minor gaps, functional but improvable
  2 Needs Work  — exists but significant gaps
  1 Not Ready   — missing entirely or fundamentally inadequate
A repo scoring 1.0-1.2 overall is at the FLOOR of the scale. That is an expected result for
an unmodernized legacy fixture, not evidence the report is wrong.

{want} questions in {len(cats)} categories:
{catlines}

`overall_score` is the EQUALLY-weighted mean of the category scores, regardless of how many
questions each category holds. (Already verified in the pre-checks.)

TWO LADDERS, and they are different things — do not conflate them:
  * score-based BANDS from `overall_score`:
{bands}
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

GRADE THE DELIVERABLES, NOT JUST THE QUESTION ANSWERS. The per-question findings are the
report's WORKING; the deliverables are what a customer actually reads and acts on, so they
carry real weight in your score:
  * `metadata.service_archetype` — is it right for this code (stateless-utility,
    stateful-crud, orchestrator, data-gateway, event-processor), and does
    `archetype_justification` cite real structure? A wrong archetype mis-frames everything
    downstream.
  * ARA `remediation_roadmap` / `recommended_actions` — is the PHASING sound? Every BLOCKER
    belongs in phase 1; a blocker sequenced behind a quality nit is a defect even when the
    finding itself is correct. Do the `question_ids`, `priority` and `effort` on each action
    match the findings it claims to resolve, and is the action a concrete change to THIS
    repo rather than generic best-practice advice?
  * MOD `pathways` — is each of the 7 pathways triggered or not-triggered correctly for this
    stack, and do the `triggering_questions` actually name the questions that drove it? A
    pathway triggered with no supporting question, or a stack that plainly needs one and
    does not get it, is a defect.
  * MOD `top_gaps` and `decomposition_strategy` — are the ranked gaps the ones that matter
    most here, and is the recommended approach proportionate to the codebase (full
    microservices decomposition of a one-file app is wrong even if every score is right)?
An unsupported or misordered deliverable is a defect on the same footing as a bad finding:
record it in `deliverable_defects` and reflect it in the score.

Be skeptical and specific: cite question_ids and file paths. Do not award credit for
confident tone, thorough formatting, or plausible-sounding generic advice. A report can be
fluent, internally consistent, and still wrong about the code.

Note the repositories are deliberately small legacy fixtures. Judge the report against what
is ACTUALLY THERE — do not penalise it for not finding problems the source does not contain,
and do not reward it for findings the source does not support. A legacy fixture landing at
the bottom of the scale is very often the CORRECT answer; scoring it that way is accuracy,
not leniency, and a report is not more accurate for being harsher about its repo.

CALIBRATION. Score how ACCURATE the report is, not how bad the repo is:
  0.90-1.00  no fabrications, no covered-question misses, sound deliverables, evidence is
             concrete and checks out
  0.75-0.89  accurate overall; minor weak evidence, one debatable severity call, or a
             cosmetic deliverable flaw
  0.55-0.74  a real defect — a covered question missed, a demonstrably wrong severity, a
             wrong archetype, or a blocker misphased in the roadmap
  0.30-0.54  multiple real defects, or a fabrication that changes the conclusion
  0.00-0.29  the report is substantially wrong about this repository
A report with nothing in `fabrications`, nothing in `misses` and nothing in
`deliverable_defects` after applying rules 1-3 belongs at 0.90+. Do not reserve the top of
the range for reports that cannot exist.

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
 "deliverable_defects": [{"deliverable": "service_archetype|remediation_roadmap|"
                          "recommended_actions|pathways|top_gaps|decomposition_strategy",
                          "what_is_wrong": "<...>", "why": "<what the source supports instead>"}],
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
    context = ara_context() if analysis == "ara" else mod_context()
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


def score_report(repo: str, analysis: str, model: str, checks_only: bool,
                 tree: Path = GOLDEN) -> dict:
    path = tree / f"{repo}-{analysis}-report.json"
    rpt = json.loads(path.read_text(encoding="utf-8"))
    checks = run_checks(rpt, analysis)
    row: dict[str, Any] = {
        "repo": repo, "analysis": analysis,
        "source_tree": tree.name,
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
            # Archetype, roadmap phasing, pathway triggering, decomposition. These are the
            # part of the report a customer actually acts on, and a correct finding set can
            # still be packaged into wrong advice.
            "deliverable_defects": verdict.get("deliverable_defects") or [],
            "weak_evidence": verdict.get("weak_evidence") or [],
            "strengths": verdict.get("strengths") or [],
        })
    return row


def discover(tree: Path = GOLDEN) -> list[tuple[str, str]]:
    units = []
    for p in sorted(tree.glob("*-report.json")):
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


def aggregate(rows: list[dict]) -> list[dict]:
    """Collapse N REPORT TREES into one row per (repo, analysis), carrying the SPREAD.

    Each tree is an independent run of the TD over the same fixtures, so each score is one
    DRAW of that TD's output quality — which is the quantity under measurement. The TD
    prompt is fixed; what varies is the analysis agent, and it varies a lot: 10-20 findings
    move per fixture per rerun. A single tree therefore cannot separate "the TD got better"
    from "the agent rolled differently", and that separation is the entire job here.

    So the mean is the number to act on, and `stddev`/`spread` say how far to trust it. A
    fixture whose spread exceeds the improvement you are claiming has not measured the
    improvement.

    `sources` records which trees contributed. The LAST tree supplies the qualitative
    fields (fabrications, misses, rubric_gaps): those are examples to go read, not
    statistics to average, and picking the best-scoring tree would launder exactly the
    noise this function exists to expose.
    """
    out: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        out.setdefault((r["repo"], r["analysis"]), []).append(r)
    agg = []
    for (repo, analysis), rs in out.items():
        row = dict(rs[-1])
        scores = [r["score"] for r in rs if isinstance(r.get("score"), (int, float))]
        row["runs"] = len(rs)
        row["scores"] = scores
        row["sources"] = [r.get("source_tree") for r in rs]
        if scores:
            mean = sum(scores) / len(scores)
            var = sum((s - mean) ** 2 for s in scores) / len(scores)
            row["score"] = round(mean, 3)
            row["stddev"] = round(var ** 0.5, 3)
            row["spread"] = round(max(scores) - min(scores), 3)
        agg.append(row)
    return sorted(agg, key=lambda r: (r["analysis"], r["repo"]))


# Measured noise floor per analysis: the largest single-fixture move observed between two
# scorer passes over BYTE-IDENTICAL golden reports. ARA reached 0.10; MOD did not move at all
# (all 11 MOD fixtures floor-score on legacy code, so nothing is in doubt).
#
# These are FALLBACKS, used only while the baseline is a single draw and therefore carries no
# stddev of its own. A multi-sample baseline supplies a real per-fixture `stddev`, which is
# strictly better evidence and takes precedence in compare_to_baseline().
#
# n=2 makes 0.10 a FLOOR on ARA's noise, not a characterization of it. Treat a sub-threshold
# delta as "not measured", never as "proven equal".
NOISE_FLOOR = {"ara": 0.10, "mod": 0.02}


def compare_to_baseline(rows: list[dict],
                        baseline: Optional[list[dict]] = None) -> dict:
    """Compare freshly-scored rows against the committed baseline, with a noise threshold.

    This is the anchor the judge otherwise lacks: without past data a 0-100 verdict is
    produced from nothing and cannot say whether the TD is better than it was last month.

    Every delta is classified against a threshold rather than reported raw, because the
    dominant term is NOT the TD -- it is the analysis agent, which moves 10-20 findings per
    fixture per rerun. On ARA that reaches 0.10, which is the width of the entire observed
    ARA range (0.72-0.82). So a raw "+0.07 improved" is indistinguishable from a different
    roll of the dice, and reporting it as an improvement is the single easiest way to talk
    yourself into a regression.

    Threshold per fixture, best evidence first:
      1. 2 * baseline stddev, when the baseline is multi-sample (real measured variance)
      2. NOISE_FLOOR[analysis], while the baseline is a single draw
    """
    if baseline is None:
        baseline = (json.loads(BASELINE.read_text(encoding="utf-8"))
                    if BASELINE.exists() else [])
    base = {(b.get("repo"), b.get("analysis")): b for b in baseline}

    units, improved, regressed, noise, unscored = [], 0, 0, 0, 0
    for r in rows:
        key = (r.get("repo"), r.get("analysis"))
        b = base.get(key)
        now, was = r.get("score"), (b or {}).get("score")
        if not isinstance(now, (int, float)) or not isinstance(was, (int, float)):
            unscored += 1
            units.append({**{k: r.get(k) for k in ("repo", "analysis")},
                          "score": now, "baseline": was, "verdict": "unscored"})
            continue
        sd = b.get("stddev")
        if isinstance(sd, (int, float)) and sd > 0:
            threshold, basis = round(2 * sd, 3), f"2*stddev over {b.get('runs')} runs"
        else:
            threshold = NOISE_FLOOR.get(r.get("analysis"), 0.10)
            basis = "measured noise floor (baseline is a single draw)"
        delta = round(now - was, 3)
        if abs(delta) < threshold:
            verdict = "within-noise"
            noise += 1
        elif delta > 0:
            verdict = "improved"
            improved += 1
        else:
            verdict = "regressed"
            regressed += 1
        units.append({
            "repo": r.get("repo"), "analysis": r.get("analysis"),
            "score": now, "baseline": was, "delta": delta,
            "threshold": threshold, "threshold_basis": basis, "verdict": verdict,
        })

    def _mean(vals):
        return round(sum(vals) / len(vals), 3) if vals else None

    now_all = [u["score"] for u in units if isinstance(u.get("score"), (int, float))]
    was_all = [u["baseline"] for u in units if isinstance(u.get("baseline"), (int, float))]
    return {
        "baseline_path": _rel(BASELINE),
        "units": sorted(units, key=lambda u: (u["analysis"] or "", u["repo"] or "")),
        "summary": {
            "improved": improved, "regressed": regressed,
            "within_noise": noise, "unscored": unscored,
            "mean_now": _mean(now_all), "mean_baseline": _mean(was_all),
            # The mean delta is reported but deliberately NOT classified: averaging over
            # fixtures hides direction (a +0.10 and a -0.10 read as "no change"), so the
            # per-unit verdicts above are the answer and this is context only.
            "mean_delta": (round(_mean(now_all) - _mean(was_all), 3)
                           if now_all and was_all else None),
        },
    }


_VERDICT_MARK = {"improved": "+", "regressed": "-", "within-noise": "~", "unscored": "?"}


def _report_comparison(cmp: dict) -> None:
    s = cmp["summary"]
    print(f"\n{'=' * 78}\nACCURACY vs BASELINE ({cmp['baseline_path']})\n{'=' * 78}")
    print(f"{'':1} {'repo':<28}{'was':>6}{'now':>7}{'delta':>8}{'thresh':>8}  verdict")
    for u in cmp["units"]:
        if u["verdict"] == "unscored":
            print(f"? {u['repo']:<28}{'—':>6}{'—':>7}{'—':>8}{'—':>8}  unscored")
            continue
        print(f"{_VERDICT_MARK[u['verdict']]} {u['repo']:<28}"
              f"{u['baseline']:>6.2f}{u['score']:>7.2f}{u['delta']:>+8.3f}"
              f"{u['threshold']:>8.2f}  {u['verdict']}")
    print(f"\n  improved {s['improved']} · regressed {s['regressed']} · "
          f"within-noise {s['within_noise']} · unscored {s['unscored']}")
    if s["mean_baseline"] is not None:
        print(f"  mean {s['mean_baseline']:.3f} -> {s['mean_now']:.3f} "
              f"({s['mean_delta']:+.3f})")
    if s["within_noise"]:
        print("\n  'within-noise' means NOT MEASURED, not 'equal'. The analysis agent moves\n"
              "  10-20 findings per fixture per rerun; a sub-threshold delta is a different\n"
              "  roll of the dice. Raise confidence with more baseline samples (--trees).")


def main() -> int:
    ap = argparse.ArgumentParser(description="Score report ACCURACY against fixture source")
    ap.add_argument("--only", nargs="*", help="repo names to score")
    ap.add_argument("--analysis", choices=["ara", "mod"], help="restrict to one analysis")
    ap.add_argument("--checks-only", action="store_true",
                    help="deterministic checks only — no Bedrock, instant, free")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--jobs", type=int, default=4, help="concurrent Bedrock calls")
    # THE SAMPLES ARE REPORT TREES, not repeated scorer passes. We are measuring TD OUTPUT
    # QUALITY, so a sample is one run of the TD over the fixtures. Re-scoring one report N
    # times would only measure the scorer's own jitter and would report a false precision:
    # it holds constant the very thing that varies.
    #
    # Produce the trees with run-fixtures.sh --after-dir harness/_sample-N (see STABILITY.md),
    # then pass them all here.
    ap.add_argument("--trees", nargs="+", type=Path, metavar="DIR",
                    help="report trees to score as independent samples of the same TD "
                         "(default: harness/golden alone). With 2+, each (repo, analysis) "
                         "row carries mean/stddev/spread across trees.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--out", type=Path, help="also write results as JSON here")
    # The committed baseline is the point of this tool: it is the record of how accurate the
    # goldens are, and it is what a future re-baseline gets compared against. Naming it as a
    # flag beats `-o harness/golden-accuracy-baseline.json` from memory.
    ap.add_argument("--update-baseline", action="store_true",
                    help=f"write results to {_rel(BASELINE)} (the committed record)")
    ap.add_argument("--show-baseline", action="store_true",
                    help="print the committed baseline scores and exit — no scoring, no cost")
    ap.add_argument("--compare-baseline", action="store_true",
                    help="classify each score against the committed baseline as improved / "
                         "regressed / within-noise, and write compare.json")
    ap.add_argument("--compare-out", type=Path, default=None,
                    help="where to write the comparison JSON (implies --compare-baseline)")
    args = ap.parse_args()
    if args.compare_out:
        args.compare_baseline = True

    if args.show_baseline:
        if not BASELINE.exists():
            print(f"no baseline at {_rel(BASELINE)}", file=sys.stderr)
            return 2
        rows = json.loads(BASELINE.read_text(encoding="utf-8"))
        if args.only:
            rows = [r for r in rows if r.get("repo") in args.only]
        if args.analysis:
            rows = [r for r in rows if r.get("analysis") == args.analysis]
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            _report(rows, False)
        return 0

    trees = args.trees or [GOLDEN]
    for t in trees:
        if not t.is_dir():
            print(f"not a report tree: {t}", file=sys.stderr)
            return 2

    # Parse the TDs up front, even under --checks-only, which otherwise returns before any
    # prompt is built. This runs in CI on every MR (harness:contract-tests), so a TD edit
    # that breaks the severity-table parse fails a pipeline instead of silently degrading
    # the grader's prompt the next time someone scores.
    for analysis in ("ara", "mod"):
        (ara_context if analysis == "ara" else mod_context)()

    # Unit list comes from the FIRST tree; a repo absent from a later tree simply
    # contributes fewer samples (reported as `runs`) rather than failing the whole run.
    units = [(r, a) for r, a in discover(trees[0])
             if (not args.only or r in args.only)
             and (not args.analysis or a == args.analysis)]
    if not units:
        print("no matching reports", file=sys.stderr)
        return 2

    jobs = [(r, a, t) for t in trees for r, a in units
            if (t / f"{r}-{a}-report.json").exists()]

    if args.checks_only:
        rows = [score_report(r, a, args.model, True, t) for r, a, t in jobs]
    else:
        print(f"scoring {len(units)} reports x {len(trees)} tree(s) = {len(jobs)} calls "
              f"with {args.model} ({args.jobs} concurrent)...", file=sys.stderr)
        rows = [None] * len(jobs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(score_report, r, a, args.model, False, t): i
                    for i, (r, a, t) in enumerate(jobs)}
            for fut in concurrent.futures.as_completed(futs):
                i = futs[fut]
                r, a, t = jobs[i]
                try:
                    rows[i] = fut.result()
                except Exception as exc:  # noqa: BLE001
                    rows[i] = {"repo": r, "analysis": a, "source_tree": t.name,
                               "error": f"{type(exc).__name__}: {exc}"[:200]}
                print(f"  done {r} {a} [{t.name}]", file=sys.stderr)
        rows = [r for r in rows if r]

    if len(trees) > 1:
        rows = aggregate(rows)

    if args.out:
        args.out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    if args.update_baseline:
        # Refuse to overwrite the committed record with a partial or checks-only run — a
        # baseline missing half its rows, or carrying no scores at all, is worse than a stale
        # one because it looks current.
        if args.checks_only:
            print("--update-baseline needs real scores; drop --checks-only", file=sys.stderr)
            return 2
        if args.only or args.analysis:
            print("--update-baseline writes the WHOLE baseline; drop --only/--analysis",
                  file=sys.stderr)
            return 2
        BASELINE.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {len(rows)} rows to {_rel(BASELINE)}", file=sys.stderr)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        _report(rows, args.checks_only)

    if args.compare_baseline:
        cmp = compare_to_baseline(rows)
        out = args.compare_out or (REPO / "harness" / "compare.json")
        out.write_text(json.dumps(cmp, indent=2) + "\n", encoding="utf-8")
        _report_comparison(cmp)
        print(f"wrote {_rel(out) if out.is_relative_to(REPO) else out}", file=sys.stderr)
    return 0


def _report(rows: list[dict], checks_only: bool) -> None:
    for a in ("ara", "mod"):
        sub = [r for r in rows if r["analysis"] == a]
        if not sub:
            continue
        multi = any(r.get("runs", 1) > 1 for r in sub)
        print(f"\n{'=' * 78}\n{a.upper()}  ({len(sub)} reports)\n{'=' * 78}")
        spread_hdr = f" {'n':>2} {'sd':>5} {'spread':>6}" if multi else ""
        print(f"{'repo':<28} {'score':>6}{spread_hdr} {'checks':>7}  detail")
        for r in sorted(sub, key=lambda x: (x.get("score") is None, x.get("score") or 0)):
            sc = "—" if r.get("score") is None else f"{r['score']:.2f}"
            nbad = len(r.get("checks_failed") or [])
            flag = "PASS" if not nbad else f"{nbad} FAIL"
            extra = (f"tier={r.get('tier')} blockers={r.get('blockers')}" if a == "ara"
                     else f"score={r.get('overall_score')} band={r.get('band')}")
            if r.get("error"):
                extra += f"  ERROR: {r['error'][:60]}"
            cols = ""
            if multi:
                cols = (f" {r.get('runs', 1):>2} {r.get('stddev', 0):>5.3f} "
                        f"{r.get('spread', 0):>6.2f}")
            print(f"{r['repo']:<28} {sc:>6}{cols} {flag:>7}  {extra}")

        scored = [r["score"] for r in sub if isinstance(r.get("score"), (int, float))]
        if scored:
            print(f"\n  mean accuracy score: {sum(scored) / len(scored):.2f}   "
                  f"range {min(scored):.2f}-{max(scored):.2f}")
        # The spread is the headline when there is one: a per-fixture spread of 0.10 means
        # any claimed improvement below 0.10 is indistinguishable from a rerun.
        if multi:
            sd = [r["spread"] for r in sub if r.get("spread") is not None]
            if sd:
                print(f"  run-to-run spread: mean {sum(sd) / len(sd):.3f}, worst "
                      f"{max(sd):.2f} — treat any delta below the worst spread as noise")

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
        if not (r.get("fabrications") or r.get("misses")
                or r.get("deliverable_defects")):
            continue
        print(f"\n--- {r['repo']} ({r['analysis'].upper()}) score "
              f"{r.get('score')} ---")
        print(f"  {r.get('summary', '')}")
        for f in r.get("fabrications") or []:
            print(f"  FABRICATION {f.get('question_id')}: {f.get('why_wrong')}")
        for m in r.get("misses") or []:
            print(f"  MISS [{m.get('severity_should_be')}] {m.get('where')}: {m.get('what')}")
        for d in r.get("deliverable_defects") or []:
            print(f"  DELIVERABLE {d.get('deliverable')}: {d.get('what_is_wrong')}")


if __name__ == "__main__":
    raise SystemExit(main())
