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
# Human-readable rendering of the baseline above. Generated by --markdown, never edited.
SCORES_MD = REPO / "harness" / "SCORES.md"

# What each deterministic check actually asserts, in plain language, for SCORES.md.
#
# "1 FAIL" in a table is unreadable on its own — a reader cannot tell whether the report is
# unusable or merely answered one question more than the rubric defines. Every one of these
# is a report contradicting ITSELF (its own counters, its own arithmetic, its own coverage),
# so none of them depend on sample depth or grader judgement: they are true at n=1.
CHECK_MEANINGS = {
    "severity_counter_undercount": (
        "high",
        "A severity counter is LOWER than the findings the report itself enumerated. "
        "Exclusion rules can push a counter above the enumerated set, never below it, so "
        "this is always an error — and because the ARA tier is computed from these counters, "
        "an undercount can mechanically relax the tier."),
    "tier_contradicts_counts": (
        "critical",
        "The stated tier is not what its own blocker/risk-safety counts produce. The tier is "
        "pure arithmetic, so this is never a judgement call."),
    "missing_safety_qualifier": (
        "high",
        "RISK-SAFETY findings exist with no BLOCKER, which requires the "
        "\"Safety Concerns\" qualifier, and it is absent — the report reads safer than the "
        "rubric says it is."),
    "spurious_safety_qualifier": (
        "medium",
        "A \"Safety Concerns\" qualifier is set although the counts do not call for one."),
    "severity_exceeds_td_ceiling": (
        "high",
        "A finding's severity is HIGHER than the severity documented in its own question "
        "heading. Only two mechanisms move a severity and neither raises it: the 9 "
        "conditional (⚡) questions resolve per `agent_scope`, and surface-flag/archetype "
        "calibration only ever downgrades. So the heading is a ceiling. This is not "
        "cosmetic — the ARA tier is arithmetic over the severity counters, so one "
        "unauthorized escalation silently moves a repo to a STRICTER tier than the rubric "
        "assigns. Severe evidence belongs in the finding's evidence and recommendation "
        "text, not in the severity field. Only escalation is flagged; a downgrade can be a "
        "legitimate calibration outcome and is left to the judge."),
    "overall_score_not_mean_of_categories": (
        "high",
        "MOD overall_score is not the equally-weighted mean of its category scores "
        "(beyond rounding tolerance)."),
    "overall_score_band_error": (
        "critical",
        "The MOD band printed does not match the band its own category mean falls in, so the "
        "headline maturity verdict is wrong."),
    "category_band_mismatch": (
        "high",
        "A MOD category's score_rating disagrees with the band its own numeric_score falls "
        "in."),
    "question_in_both_findings_and_evaluations": (
        "high",
        "A rubric question was resolved twice. findings and evaluations are disjoint by "
        "design, so a double answer means the two can disagree about the same question."),
    "duplicate_question_ids": (
        "medium",
        "The same question id appears more than once within findings or evaluations."),
    "incomplete_question_coverage": (
        "critical",
        "The report answered FEWER rubric questions than the rubric defines (ARA 43, "
        "MOD 37) — the assessment is incomplete, and the gap is silent."),
    "unexpected_question_count": (
        "low",
        "More questions were resolved than the rubric defines. Usually a stray or "
        "hallucinated id."),
}

DEFAULT_MODEL = os.environ.get(
    "HARNESS_SCORE_MODEL", "global.anthropic.claude-opus-4-5-20251101-v1:0")

# The question/severity table, the rubric sizes and the tier/band arithmetic all live in
# skill_table.py, shared with diff-reports.py and the judge. Importing rather than
# re-deriving is the whole point: two copies of the severity table drift silently, and this
# grader and the differ disagreeing about what AUTH-Q5 is would be invisible until a verdict
# came out wrong.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_table import (  # noqa: E402
    EXPECTED_QUESTIONS, SEVERITY_RANK, SKILLS, expected_ara_tier, mod_band, parse_questions,
    rel as _rel, parse_calibrations, parse_extended, parse_mod_archetype_calibrated,
    parse_mod_surface_gates, parse_na_map, parse_scope_severities,
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


def _report_flags(rpt: dict) -> dict:
    """This report's surface_flags as a plain dict, keys lowercased. Absent -> {}."""
    sf = (rpt.get("metadata") or {}).get("surface_flags") or {}
    return {str(k).strip().lower(): v for k, v in sf.items()} if isinstance(sf, dict) else {}


def ara_scope_resolution(rpt: dict) -> str:
    """Pre-resolve every scope-dependent ARA severity for THIS report's agent_scope.

    The severity table teaches the RULE ([C]/[S] resolve by agent_scope) but never told the
    grader which scope the report under review actually used, leaving it to notice
    `metadata.agent_scope` in the JSON and apply the rule itself 9 times. That is
    deterministic work handed to an LLM, and it graded inconsistently: on
    legacy-storefront-rails the grader talked itself in and out of one call inside a single
    sentence ("AUTH-Q6 ... should be BLOCKER ... which is actually correct"). A correct
    read-only downgrade scored as a miss is the grader's error, not the report's.

    The resolved severity per scope is PARSED from the TD's own bullets, not inferred. An
    earlier version assumed "conditional BLOCKER -> RISK-SAFETY under read-only", which is
    wrong for API-Q4 (the TD sends it to INFO, SKILL.md:719): that over-resolved API-Q4 by a
    full class on all 11 read-only reports AND, because this block is stated as authoritative,
    told the grader to praise a report that over-escalated it. See parse_scope_severities.

    DATA-Q1 is scope-dependent too but uses a Stage-A/B-tier ladder rather than plain bullets,
    so it is described separately rather than reduced to one severity.

    Absent scope => read-only: the TD's documented default (SKILL.md:278, "the safer
    default", chosen to avoid false escalation). 1 of 12 golden ARA reports omits the field.
    """
    scope = ((rpt.get("metadata") or {}).get("agent_scope") or "").strip().lower()
    stated = scope or "read-only (ABSENT from metadata — TD default assumed)"
    write_enabled = scope == "write-enabled"
    qs = parse_questions("ara")
    lines = []
    for qid, sev_by_scope in parse_scope_severities("ara").items():
        # DATA-Q1 now parses, but its parsed value is only the B1 LAYER, not the question's
        # severity. DATA-Q1 is a Stage-A/B ladder: B1/B2/B3 fire independently and the highest
        # wins, Stage A gates the whole question, the stateless-utility archetype and the
        # dev-library-application override each send it to INFO, and any layer may contribute
        # no finding at all. Stating "DATA-Q1 -> RISK-SAFETY" here would flatten all of that
        # and turn every legitimately CLEAR or INFO DATA-Q1 into a false miss — the exact error
        # class this whole block exists to remove. It gets the `data_q1` ladder block below.
        # Do NOT "simplify" by deleting this skip.
        if qid == "DATA-Q1":
            continue
        if write_enabled:
            # The ⚡ heading severity IS the escalated (write-enabled) value by TD convention,
            # and it is the precise class: the read-only bullets write a terse "RISK" for the
            # [S] questions where the heading says RISK-SAFETY. Trust the heading here.
            resolved = str((qs.get(qid) or {}).get("severity") or "").strip().upper()
        else:
            # Read-only: the per-question bullet, NOT a blanket rule — API-Q4 is INFO here,
            # not RISK-SAFETY, which the old assume-BLOCKER->RISK-SAFETY shortcut got wrong.
            resolved = sev_by_scope.get("read-only")
        if resolved:
            lines.append(f"  - {qid} {(qs.get(qid) or {}).get('title', '')} -> {resolved}")
    data_q1 = ("  - DATA-Q1 Sensitive Data Classification: a Stage-A/B ladder. Its B1 BLOCKER "
               "tier fires only under write-enabled scope; under read-only B1 is RISK-SAFETY. "
               "Stage A = No, a stateless-utility archetype, or a dev-library-application all "
               "send the whole question to INFO; all layers clear => no finding.\n")
    return (
        f"\nTHIS REPORT'S `agent_scope` IS: {stated}\n"
        f"So for these scope-dependent (⚡) questions, the CORRECT severity in THIS report is "
        f"exactly (note API-Q4 goes to INFO, NOT RISK-SAFETY, under read-only):\n"
        + "\n".join(lines) + "\n" + data_q1
        + "A report that resolves these as listed has applied the TD CORRECTLY. Do NOT record "
        f"it as a miss, an understatement, an over-escalation, or a wrong severity — this is "
        f"the resolution the TD prescribes for this scope.\n")


def ara_calibration_resolution(rpt: dict) -> str:
    """The surface-flag and archetype calibrations — the downgrades the scope block does NOT
    cover. These are the biggest remaining source of false misses: 15 surface-flag questions
    and 8 archetype questions the grader was told keep a fixed severity "independent of scope".

    The rules are handed over VERBATIM (parse_calibrations returns the TD prose), paired with
    THIS report's actual archetype + surface_flags, so the deterministic part (which flags are
    set) is separated from the judgement (does the rule fire). Both are named in the TD as
    downgrade-only (SKILL.md:292, "Calibration only downgrades severity — it never upgrades"),
    so a calibrated INFO on any of these is correct, never an understatement.
    """
    cal = parse_calibrations("ara")
    if not cal:
        return ""
    meta = rpt.get("metadata") or {}
    archetype = str(meta.get("service_archetype") or "unknown").strip()
    flags = _report_flags(rpt)
    flag_line = ", ".join(f"{k}={v}" for k, v in flags.items()) or "(none in metadata)"
    qs = parse_questions("ara")
    lines = []
    for qid in sorted(cal):
        title = (qs.get(qid) or {}).get("title", "")
        lines.append(f"  - {qid} {title}:")
        for c in cal[qid]:
            lines.append(f"      [{c['kind']}] {c['rule']}")
    return (
        f"\nCALIBRATION DOWNGRADES (surface-flag + archetype). These OVERRIDE the fixed "
        f"severity table for the questions below — the table is the DEFAULT, calibration is "
        f"the exception, and it only ever DOWNGRADES (SKILL.md:292).\n"
        f"THIS REPORT'S service_archetype = `{archetype}`; surface_flags: {flag_line}\n"
        f"Apply each rule below against those exact values. If a rule fires, the question is "
        f"correctly recorded as INFO and is NOT a miss or an understatement:\n"
        + "\n".join(lines) + "\n")


def ara_extended_resolution(rpt: dict) -> str:
    """ARA's 18 extended questions and their triggers. An untriggered extended question is
    recorded `not_evaluated_extended` and excluded from scoring (SKILL.md:49) — the single
    largest false-miss source: 88 such records across the golden set, STATE-Q4 (a fixed
    RISK-SAFETY) among them in 9 of 12 reports. Without this the grader reads every one as an
    unresolved RISK-SAFETY question.
    """
    ext = parse_extended("ara")
    if not ext:
        return ""
    qs = parse_questions("ara")
    lines = [f"  - {qid} {(qs.get(qid) or {}).get('title', '')}: triggered when {cond}"
             for qid, cond in ext.items()]
    return (
        f"\nEXTENDED QUESTIONS (evaluated ONLY when triggered; otherwise "
        f"`not_evaluated_extended` and EXCLUDED from scoring — SKILL.md:49). A question below "
        f"recorded not-evaluated because its trigger is absent is CORRECT, even if the "
        f"severity table assigns it BLOCKER or RISK-SAFETY. Only record a miss here if the "
        f"trigger condition IS met in the source and the report still skipped it:\n"
        + "\n".join(lines) + "\n")


def _na_resolution(rpt: dict, analysis: str) -> str:
    """The repo_type N/A mapping for THIS report's repo_type. N/A questions are excluded from
    every count and from the profile (SKILL.md ARA:617 / MOD:494). All 12 golden fixtures are
    `application` (empty N/A set) so this fires on none of them today — but the harness exists
    to score reruns under change, and the first `library` fixture would otherwise draw a wall
    of ENG-Q1..Q5 misses. Parsed so it cannot silently disagree with the TD table.
    """
    repo_type = str((rpt.get("metadata") or {}).get("repo_type") or "application").strip()
    na = parse_na_map(analysis).get(repo_type, [])
    if not na:
        return (f"\nREPO TYPE = `{repo_type}`: all questions apply (no N/A mapping). "
                f"A finding on any question is in-scope.\n")
    return (
        f"\nREPO TYPE = `{repo_type}`: these questions are N/A and are recorded in the N/A "
        f"display format, EXCLUDED from all counts and from the readiness profile "
        f"(SKILL.md exclusion rules). A question below recorded N/A is CORRECT, not a miss, "
        f"even if its default severity is BLOCKER; and a FINDING emitted on one is itself a "
        f"defect: {', '.join(na)}\n")


def mod_calibration_resolution(rpt: dict) -> str:
    """MOD's analogue of the ARA calibration block — surface-flag gates + archetype-keyed
    rubrics. MOD's exclusions are arithmetically load-bearing: a gated question leaves BOTH
    the numerator and denominator of its category mean (SKILL.md:494-499), so a grader that
    thinks a gated question should have scored 1 also flags the category mean and the overall
    band as wrong — one unstated rule becomes three apparent defects. Archetype calibration
    here can BOTH raise and lower a score (SKILL.md:150), unlike ARA's downgrade-only rule.
    """
    gates = parse_mod_surface_gates()
    arch = parse_mod_archetype_calibrated()
    if not gates and not arch:
        return ""
    meta = rpt.get("metadata") or {}
    archetype = str(meta.get("service_archetype") or "unknown").strip()
    flags = _report_flags(rpt)
    flag_line = ", ".join(f"{k}={v}" for k, v in flags.items()) or "(none in metadata)"
    qs = parse_questions("mod")
    gate_lines = [
        f"  - {qid} {(qs.get(qid) or {}).get('title', '')}: gate = {g['flag']}; "
        f"when false -> {g['when_false']}"
        for qid, g in gates.items()]
    arch_line = ", ".join(arch)
    return (
        f"\nMOD SURFACE-FLAG GATES. A gated question whose flag is `false` is recorded "
        f"`not_evaluated_surface_flag` (\"Not Evaluated (archetype-N/A)\") and EXCLUDED from "
        f"BOTH the numerator and denominator of its category mean (SKILL.md:494) — it does "
        f"NOT default to Score 1. So a gated-out question is correct, not a missed Score 1, "
        f"and it does NOT drag the category or overall score down.\n"
        f"THIS REPORT'S service_archetype = `{archetype}`; surface_flags: {flag_line}\n"
        + "\n".join(gate_lines) + "\n"
        f"ARCHETYPE-KEYED RUBRICS ({arch_line}): these score against an archetype-specific "
        f"rubric that can BOTH raise and lower the score vs the default — e.g. a "
        f"stateless-utility correctly scores 4 on INF-Q4 for sync-only HTTP where an "
        f"orchestrator would score 1 (SKILL.md:150). Do not treat the archetype-appropriate "
        f"score as an error.\n")


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

Each question below has a DEFAULT assigned severity. A report that resolves an issue under
the owning question at that severity is CORRECT. But the default is not the whole story:
several mechanisms below the table legitimately move a severity OFF this default for a
particular report (agent_scope, surface-flag calibration, archetype calibration, the
extended-question triggers, and the repo_type N/A mapping). Those per-report resolutions are
spelled out AFTER this table and OVERRIDE it — read them before recording any miss.

{_severity_block(qs)}

[C] = CONDITIONAL BLOCKER: resolves to BLOCKER only when `agent_scope` is "write-enabled".
      Under "read-only" (the TD's DEFAULT, chosen deliberately to avoid false escalation)
      these resolve to RISK-SAFETY or INFO — see the per-report resolution below for the
      exact class, which is NOT uniform (API-Q4 goes to INFO, not RISK-SAFETY).
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

    # 3. No finding may exceed the severity ceiling in its own TD heading.
    #
    # This is the check the harness was missing. The TD names the severity in each `####
    # <qid>:` heading and only two documented mechanisms move it: the 9 conditional (⚡)
    # questions resolve by `agent_scope`, and surface-flag/archetype calibration only ever
    # DOWNGRADES. So the heading is a ceiling, and a report above it has invented severity.
    #
    # It matters because the ARA tier is pure arithmetic over blocker_count and
    # risk_safety_count: one unauthorized escalation silently moves a repo to a stricter
    # tier than the rubric assigns, and every downstream consumer reads that as the
    # rubric's verdict. Escalation was the ACTUAL observed failure (AUTH-Q5 emitted as
    # BLOCKER on 6 of 12 golden reports, tier-shifting several), and it was invisible until
    # someone diffed severities by hand.
    #
    # Only escalation is flagged. Under-statement is left to the judge: a downgrade can be
    # a legitimate calibration outcome, and the TD's downgrade rules are prose with nested
    # conditions that this function deliberately does not try to evaluate (see
    # skill_table.parse_calibrations).
    qs, scope = parse_questions("ara"), parse_scope_severities("ara")
    for f in findings:
        qid, got = f.get("question_id"), _native(f)
        q = qs.get(str(qid))
        if not q or not got:
            continue
        # A conditional question's ceiling is the most severe resolution the TD permits it,
        # across every scope — this check does not know the report's scope, and resolving it
        # wrongly would be worse than a slightly loose ceiling.
        allowed = [q["severity"]] + (list((scope.get(str(qid)) or {}).values())
                                     if q.get("conditional") else [])
        ranked = [(SEVERITY_RANK.get(str(s).upper(), -1), s) for s in allowed if s]
        if not ranked:
            continue
        ceil_rank, ceiling = max(ranked)
        if SEVERITY_RANK.get(str(got).upper(), -1) > ceil_rank:
            tier_moving = str(got).upper() in ("BLOCKER", "RISK-SAFETY")
            out.append({
                "check": "severity_exceeds_td_ceiling",
                "severity": "high" if tier_moving else "medium",
                "detail": f"{qid} reported {got} but the TD heading documents {ceiling}"
                          + (" (conditional ⚡ — this is the most severe scope resolution)"
                             if q.get("conditional") else "")
                          + ". Severity may only be DOWNGRADED (calibration) or resolved "
                            "per agent_scope; describe severe evidence in the evidence and "
                            "recommendation text, not the severity field",
            })
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
    # Resolve by SEARCHING the fixture tree, not by assuming a layout. Hardcoding
    # `portfolio/<repo>` silently returned "" for the 3 `modern/` fixtures, and an empty
    # source does not fail — it renders as "(source unavailable)", so the judge scored the
    # reports on plausibility alone and marked every cited file unverifiable. That reads as
    # a report defect (0.35-0.45) when it is really a missing input.
    root = next((c for c in (FIXTURES / repo,
                             FIXTURES / "portfolio" / repo,
                             FIXTURES / "modern" / repo) if c.is_dir()), None)
    if root is None:
        root = next((p for p in sorted(FIXTURES.glob(f"*/{repo}")) if p.is_dir()), None)
    if root is None:
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
    # Append the per-report resolution of every mechanism that legitimately moves a severity
    # off the fixed table. Without these the grader is told severity is "independent of scope"
    # and records correct downgrades as misses — the dominant false-miss source. Each block is
    # rule (parsed from the TD) + this report's actual scope/archetype/flags/repo_type.
    if analysis == "ara":
        context += ara_scope_resolution(rpt)
        context += ara_calibration_resolution(rpt)
        context += ara_extended_resolution(rpt)
        context += _na_resolution(rpt, "ara")
    else:
        # MOD has no agent_scope, but it DOES have surface-flag gates and archetype-keyed
        # rubrics, and those move ARITHMETIC (category means), so it needs the same treatment.
        context += mod_calibration_resolution(rpt)
        context += _na_resolution(rpt, "mod")
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

    `by_tree` maps tree name -> that run's score, KEYED rather than positional. `scores`
    drops non-numeric entries while `sources` lists every tree, so the two lists misalign
    the moment one run errors — reading "batch 2's score" off a positional index would then
    attribute the wrong number to the wrong run. Per-batch reporting uses `by_tree`.
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
        row["by_tree"] = {r.get("source_tree"): r.get("score") for r in rs}
        # `scored_runs` is NOT `runs`: a run that errored contributes a row (so the tree is
        # listed in `sources`) but no number. Variance must be gated on the numbers, and
        # downstream must be able to tell "we have 3 numbers" from "we have 3 attempts".
        row["scored_runs"] = len(scores)
        if scores:
            mean = sum(scores) / len(scores)
            row["score"] = round(mean, 3)
        # BOTH variance measures stay None below 2 numeric scores, for the same reason.
        # `max - min` over a single score is 0.0, which reads in a published table as
        # "re-run and never moved" when nothing was compared at all — the identical
        # misleading zero the stddev guard below exists to prevent, and the one the ARA rows
        # spent this whole exercise eliminating. Not measured is not the same as stable.
        row["spread"] = (round(max(scores) - min(scores), 3)
                         if len(scores) >= 2 else None)
        # stddev stays None below 2 numeric scores. A single draw would otherwise report
        # stddev 0.0 — indistinguishable from "measured 3x, perfectly stable" — and a
        # threshold read off that 0.0 makes ANY wobble look like a regression. None is the
        # honest value: not measured. See compare_to_baseline, which floors on it.
        if len(scores) >= 2:
            var = sum((s - mean) ** 2 for s in scores) / len(scores)
            row["stddev"] = round(var ** 0.5, 3)
        else:
            row["stddev"] = None
        agg.append(row)
    return sorted(agg, key=lambda r: (r["analysis"], r["repo"]))


def merge_baseline(prior: list[dict], rows: list[dict],
                   analysis: str) -> tuple[list[dict], set[str], str]:
    """Replace `analysis`' baseline rows with `rows`; carry the other analysis' rows through.

    Returns (merged, dropped_repos, note). `dropped_repos` are fixtures that HAD a baseline
    row for this analysis and no longer do — the failure a merge can hide, since the row
    just stops existing and every later comparison silently skips it. Reported, not fatal:
    retiring a fixture is legitimate.
    """
    keep = [b for b in prior if b.get("analysis") != analysis]
    fresh = [r for r in rows if r.get("analysis") == analysis]
    replaced = [b for b in prior if b.get("analysis") == analysis]
    missing = {b["repo"] for b in replaced} - {r["repo"] for r in fresh}
    merged = sorted(keep + fresh, key=lambda r: (r["analysis"], r["repo"]))
    others = "/".join(sorted({b["analysis"] for b in keep})) or "other"
    note = (f"  merged: kept {len(keep)} {others} row(s), "
            f"replaced {len(replaced)} {analysis} row(s) with {len(fresh)}")
    return merged, missing, note


# Measured noise floor per analysis, from THREE INDEPENDENT ANALYSIS RUNS over the same
# fixtures (golden + s2 + s3, 11 fixtures x 2 analyses, 2026-07-30):
#
#            median sd   max sd   max spread   2*median_sd
#     ARA       0.123     0.198      0.46         0.246
#     MOD       0.014     0.123      0.26         0.028
#
# The earlier values (ARA 0.10, MOD 0.02) came from RE-SCORING BYTE-IDENTICAL reports, which
# measures only the JUDGE's jitter and holds constant the thing that actually dominates: the
# analysis agent. Re-running the TD moves storefront-rails 0.42 -> 0.88 -> 0.52 with no code
# change at all. So 0.10 understated ARA's real floor by ~2.5x, and every delta between 0.10
# and 0.25 was being reported as "improved"/"regressed" when it was indistinguishable from a
# different roll of the dice. That is the failure mode most likely to make a contributor
# trust a number they should not.
#
# ARA is set to 2*median_sd. Deliberately NOT 2*max_sd (0.396) — that is so wide it would
# call every plausible TD improvement "within-noise" and the harness would stop saying
# anything. The per-fixture stddev path below is the real fix; these are only the fallback
# for a single-draw baseline.
#
# These remain FALLBACKS: a multi-sample baseline supplies a real per-fixture `stddev`, which
# is strictly better evidence and takes precedence in compare_to_baseline(). Treat a
# sub-threshold delta as "NOT MEASURED", never as "proven equal".
NOISE_FLOOR = {"ara": 0.25, "mod": 0.03}


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
        # Per-fixture measured variance beats the global constant, but ONLY when it is
        # actually measured — and only as a FLOOR-RAISING term, never a floor-lowering one.
        #
        # Two ways `stddev == 0` lies, both of which turn any wobble into a "regression":
        #   - runs < 2: a single draw reports stddev 0.0 (not null), so it looks maximally
        #     stable when in truth nothing was measured at all.
        #   - runs >= 2 but every draw scored identically: 6 of 14 MOD fixtures do this. It
        #     means "quiet across 3 draws", not "a 0.04 move is meaningful" — the judge
        #     reports on a 0.01-ish grid, so the next draw can differ without anything
        #     changing.
        # So take the LARGER of 2*stddev and the analysis noise floor. A jittery fixture
        # raises its own bar above the floor; a quiet one can never fall below it.
        # `scored_runs` (numeric scores) over `runs` (attempts) — an errored run inflates
        # `runs` without contributing to the variance.
        sd = b.get("stddev")
        runs = b.get("scored_runs", b.get("runs"))
        floor = NOISE_FLOOR.get(r.get("analysis"), 0.10)
        if isinstance(sd, (int, float)) and sd > 0 and isinstance(runs, int) and runs >= 2:
            if 2 * sd > floor:
                threshold, basis = round(2 * sd, 3), f"2*stddev over {runs} runs"
            else:
                threshold = floor
                basis = f"noise floor (exceeds 2*stddev={2 * sd:.3f} over {runs} runs)"
        else:
            threshold = floor
            basis = ("measured noise floor (baseline has no multi-run variance"
                     f"{'' if runs is None else f'; runs={runs}'})")
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
                    help=f"write results to {_rel(BASELINE)} (the committed record). "
                         "With --analysis, MERGES: replaces that analysis' rows and keeps "
                         "the other's — a TD edit only invalidates its own prior draws")
    ap.add_argument("--show-baseline", action="store_true",
                    help="print the committed baseline scores and exit — no scoring, no cost")
    ap.add_argument("--compare-baseline", action="store_true",
                    help="classify each score against the committed baseline as improved / "
                         "regressed / within-noise, and write compare.json")
    ap.add_argument("--compare-out", type=Path, default=None,
                    help="where to write the comparison JSON (implies --compare-baseline)")
    # Renders the committed scores as a readable MD table. Generated rather than hand-written
    # so it cannot drift from the JSON it summarizes.
    ap.add_argument("--markdown", type=Path, nargs="?", const=SCORES_MD, default=None,
                    metavar="PATH",
                    help=f"write a human-readable score table (default: {_rel(SCORES_MD)})")
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
        if args.markdown:
            args.markdown.write_text(render_markdown(rows), encoding="utf-8")
            print(f"wrote {_rel(args.markdown)}", file=sys.stderr)
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

    # Unit list is the UNION over every tree, not trees[0]. A repo present in only some
    # trees contributes fewer samples (reported as `runs`), which aggregate() already
    # handles — but taking the list from trees[0] alone SILENTLY DISCARDS any unit the
    # first tree lacks. That is not hypothetical: the 3 modern fixtures exist only in s3,
    # so `--trees golden samples/s2 samples/s3` scored 22 units and dropped 5 without a
    # word, and the "modern" tiers those fixtures were built to cover went unmeasured
    # while the run still reported success.
    seen: set[tuple[str, str]] = set()
    units = []
    for t in trees:
        for r, a in discover(t):
            if (r, a) in seen:
                continue
            if (args.only and r not in args.only) or (args.analysis and a != args.analysis):
                continue
            seen.add((r, a))
            units.append((r, a))
    if not units:
        print("no matching reports", file=sys.stderr)
        return 2
    # Say so when coverage is ragged. A unit scored on 1 of 3 trees has no spread, so its
    # mean cannot be compared against a 3-tree mean — silence here reads as "all equal".
    partial = [(r, a, n) for r, a in units
               if (n := sum((t / f"{r}-{a}-report.json").exists() for t in trees)) < len(trees)]
    if partial:
        print(f"note: {len(partial)} of {len(units)} units are missing from some tree(s) "
              f"and will have fewer runs:", file=sys.stderr)
        for r, a, n in partial:
            print(f"  {r} {a}: {n}/{len(trees)} tree(s)", file=sys.stderr)

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
        if args.only:
            print("--update-baseline writes every fixture of an analysis; drop --only",
                  file=sys.stderr)
            return 2
        if args.analysis:
            # `--analysis` MERGES: rows for this analysis are replaced, rows for the other
            # are carried through untouched.
            #
            # This is not a convenience. The two analyses can legitimately have different
            # valid sample sets, because a TD edit invalidates only ITS OWN prior draws:
            # when the ARA severity-ceiling rule landed, every pre-existing ARA tree became
            # stale while MOD's three draws stayed valid. Forcing one whole-baseline write
            # would mean either re-running MOD's 3 sweeps for nothing, or baselining ARA
            # against reports its own TD no longer produces.
            prior = (json.loads(BASELINE.read_text(encoding="utf-8"))
                     if BASELINE.exists() else [])
            rows_out, missing, note = merge_baseline(prior, rows, args.analysis)
        else:
            rows_out, missing, note = rows, set(), ""
        BASELINE.write_text(json.dumps(rows_out, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {len(rows_out)} rows to {_rel(BASELINE)}", file=sys.stderr)
        if note:
            print(note, file=sys.stderr)
        # A fixture that vanished is the failure mode a merge can hide: the row simply stops
        # existing and every later comparison silently skips it. Say so; do not fail, since
        # deliberately retiring a fixture is legitimate.
        if missing:
            print(f"  NOTE: {len(missing)} fixture(s) had a baseline row for another "
                  f"analysis but none here: {', '.join(sorted(missing))}", file=sys.stderr)
    if args.markdown:
        args.markdown.write_text(render_markdown(rows), encoding="utf-8")
        print(f"wrote {_rel(args.markdown)}", file=sys.stderr)
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
                # "—", not 0.000, when a unit was drawn once: it exists in only some of the
                # trees (the modern fixtures live in s3 alone), and printing 0.000 there
                # reads as rock-steady when nothing was measured at all.
                sd = r.get("stddev")
                sd_s = "    —" if sd is None else f"{sd:>5.3f}"
                sp = r.get("spread")
                sp_s = "     —" if sp is None else f"{sp:>6.2f}"
                cols = f" {r.get('scored_runs', r.get('runs', 1)):>2} {sd_s} {sp_s}"
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


_SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _num(v, places: int) -> str:
    """Format a maybe-missing statistic. None renders "—", NOT 0.

    Variance statistics are None whenever they were not measured (a unit drawn once), and
    `f"{v or 0:.3f}"` would turn "unknown" into the most reassuring value on the scale.
    """
    return "—" if not isinstance(v, (int, float)) else f"{v:.{places}f}"


def render_markdown(rows: list[dict]) -> str:
    """Render the scores as a committed, human-readable SCORES.md.

    GENERATED, never hand-written. A transcribed score table goes stale silently the moment
    the baseline is refreshed — the same failure mode as a transcribed severity table (see
    skill_table.py), and the reader has no way to tell. Regenerating from the baseline JSON
    means the doc cannot disagree with the data it came from.

    The sample depth is stated up front and per-analysis, because it governs what the numbers
    can support: at n=1 there is no measured variance, so the NOISE_FLOOR applies and a
    single-fixture ARA difference of 0.10 (the width of the whole observed range) is not a
    ranking. Publishing scores without that caveat invites exactly the over-reading the
    thresholds exist to prevent.
    """
    multi = any(r.get("runs", 1) > 1 for r in rows)
    max_runs = max((r.get("runs", 1) for r in rows), default=1)
    # Counted, not asserted in prose: the depth is uneven (a fixture added late exists in
    # fewer batches), and a hand-written "up to N runs" sentence stops matching the table the
    # first time the baseline is refreshed at a different depth.
    single_draw = sum(1 for r in rows if (r.get("scored_runs") or r.get("runs", 1)) < 2)
    out = [
        "# Report accuracy scores",
        "",
        "> **GENERATED FILE — do not edit.** Regenerate with:",
        "> `harness/score-reports.py --show-baseline --markdown harness/SCORES.md`",
        "> (or add `--markdown` to any `--update-baseline` run).",
        "",
        f"Source: [`{_rel(BASELINE)}`]({BASELINE.name})",
        "",
        "Each score is an LLM grader's assessment of how well a generated report is "
        "**grounded in the fixture's actual source code** — fabrications and misses count "
        "against it. This is the *accuracy* axis, and it is what the judge compares a TD "
        "change against. It is NOT the ARA tier or the MOD band, which are the report's own "
        "verdicts about the app and appear here as context.",
        "",
        "The **Checks** column is a different axis entirely: deterministic, arithmetic "
        "assertions that a report does not contradict **itself** — its own severity "
        "counters, its own tier arithmetic, its own question coverage. No LLM and no "
        "sampling is involved, so a failure here is a real defect at any sample depth, and "
        "is safe to act on immediately. A report can be perfectly grounded in the source "
        "(high score) and still fail a check by miscounting what it found. Each failure "
        "names the check; see [What the checks mean](#what-the-checks-mean).",
        "",
    ]

    if multi:
        out += [
            f"**Sample depth: up to {max_runs} independent runs per fixture"
            + (f", {single_draw} fixture(s) drawn once" if single_draw else "")
            + ".** `sd` is the measured per-fixture standard deviation and `spread` the "
            "max−min across runs. Both read `—` for a fixture drawn only once — not "
            "`0.000`, which would read as re-run and rock-steady when nothing was compared "
            "at all.",
            "",
            "A delta counts as real only past `max(2·sd, floor)` — the noise floor "
            f"(**ARA {NOISE_FLOOR['ara']:.2f}**, **MOD {NOISE_FLOOR['mod']:.2f}**) is a "
            "lower bound the measured `sd` can raise but never lower. A jittery fixture is "
            "held to a stricter bar than the floor; a quiet one is not held to a looser one, "
            f"because an n={max_runs} `sd` is far too weak an estimator to justify shrinking "
            "the bar and shrinking it is the direction that manufactures false improvements. "
            "**Below the threshold means NOT MEASURED — never \"proven equal\".**",
            "",
        ]
        out += [
            "The per-run scores are listed in the **Runs** column rather than one column per "
            "batch: the two analyses are sampled from different batches, so a shared column "
            "per batch left every row half-empty and the reader counting dashes to work out "
            "which run was which. The point of showing the runs at all is that the mean "
            "hides disagreement — 0.72 / 0.92 and a steady 0.82 both average to 0.82, but "
            "only one of them is a measurement.",
            "",
        ]
    else:
        out += [
            "**Sample depth: 1 run per fixture (single draw).** There is no measured "
            "variance, so the threshold falls back to the noise floor — "
            f"**ARA {NOISE_FLOOR['ara']:.2f}**, **MOD {NOISE_FLOOR['mod']:.2f}** per "
            "fixture. That floor was measured by RE-RUNNING the analysis three times, not "
            "by re-scoring one report: re-scoring holds the analysis agent constant and so "
            "measures only judge jitter, which understated ARA's real noise about 2.5×. "
            f"Since the ARA floor ({NOISE_FLOOR['ara']:.2f}) is comparable to the whole "
            "observed score range, ARA scores at this depth **cannot rank fixtures against "
            "each other**; only the deterministic defects below are safe to act on.",
            "",
        ]

    for a in ("ara", "mod"):
        sub = [r for r in rows if r.get("analysis") == a]
        if not sub:
            continue
        scored = [r["score"] for r in sub if isinstance(r.get("score"), (int, float))]
        out.append(f"## {a.upper()} — {len(sub)} reports")
        out.append("")
        if scored:
            out.append(f"Mean **{sum(scored) / len(scored):.2f}**, range "
                       f"{min(scored):.2f}–{max(scored):.2f}.")
            out.append("")
        detail_hdr = "Tier / blockers" if a == "ara" else "MOD score / band"
        # This analysis' OWN batches, in chronological (first-appearance) order. Scoped per
        # analysis on purpose: ARA and MOD are sampled from different batches, so a shared
        # column set printed 6 columns of which 3 were always "—" on every row.
        trees: list[str] = []
        for r in sub:
            for t in (r.get("by_tree") or {}):
                if t and t not in trees:
                    trees.append(t)
        # The runs go in ONE column as a compact list. Per-batch columns don't survive
        # contact with more batches: at n=4 the table was already 12 columns wide and wraps
        # in a terminal and on GitLab, which is where contributors actually read it. Which
        # batch a run came from is in the JSON; what a reader needs here is the SHAPE of the
        # disagreement, and "0.72 / 0.88 / 0.82" shows that in one glance.
        cols = (["Repo"] + (["Mean"] if multi else ["Score"])
                + (["Runs", "sd", "spread"] if multi else []) + ["Checks", detail_hdr])
        out.append("| " + " | ".join(cols) + " |")
        out.append("|" + "|".join(["---"] * len(cols)) + "|")
        # Worst first: the reports needing attention should be read first, and a reader
        # scanning the top of the table should land on problems, not on the best case.
        for r in sorted(sub, key=lambda x: (x.get("score") is None, x.get("score") or 0)):
            sc = "—" if r.get("score") is None else f"{r['score']:.2f}"
            failed = r.get("checks_failed") or []
            # Severity only. The check NAMES used to be inlined here too, which made this the
            # widest column in the table while repeating verbatim what the defects table
            # below already lists per failure — with the detail string that makes the name
            # mean something. A reader scanning for "which reports are broken" wants the
            # severity; a reader acting on one wants the defects table.
            if not failed:
                flag = "PASS"
            else:
                worst = min((c.get("severity", "low") for c in failed),
                            key=lambda s: _SEV_ORDER.get(s, 9))
                n = f" ×{len(failed)}" if len(failed) > 1 else ""
                flag = f"**{worst.upper()}**{n}"
            detail = (f"{r.get('tier')} / {r.get('blockers')}" if a == "ara"
                      else f"{r.get('overall_score')} / {r.get('band')}")
            cells = [f"`{r['repo']}`", sc]
            if multi:
                # In batch order, so the list is reproducible rather than sorted into a
                # tidier-looking sequence that no longer says which run moved.
                bt = r.get("by_tree") or {}
                runs = [f"{bt[t]:.2f}" for t in trees
                        if isinstance(bt.get(t), (int, float))]
                cells.append(" / ".join(runs) if runs else "—")
                # A single-draw unit publishes "—" for both. `stddev: 0.000` in a published
                # table is the most misleading cell the harness could print: a reader takes
                # it as "measured, never moved" and trusts a delta the harness never
                # measured. See aggregate().
                cells += [_num(r.get("stddev"), 3), _num(r.get("spread"), 2)]
            cells += [flag, detail]
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
        if multi:
            sd = [r["spread"] for r in sub if r.get("spread") is not None]
            if sd:
                out.append(f"Run-to-run spread: mean {sum(sd) / len(sd):.3f}, worst "
                           f"{max(sd):.2f} — treat any delta below the worst spread as noise.")
                out.append("")

    bad = [(r, c) for r in rows for c in (r.get("checks_failed") or [])]
    out.append(f"## Deterministic defects — {len(bad)} across "
               f"{len({r['repo'] + r['analysis'] for r, _ in bad})} reports")
    out.append("")
    if not bad:
        out.append("None.")
        out.append("")
    else:
        # These are ARITHMETIC, not sampled judgement: a counter below the findings it
        # enumerates is wrong at n=1. They are the one part of this file that is actionable
        # without more samples, which is why they get their own section.
        out.append("Arithmetic contradictions inside a single report — **actionable now**, "
                   "independent of sample depth.")
        out.append("")
        out.append("| Severity | Repo | Check | Detail |")
        out.append("|---|---|---|---|")
        for r, c in sorted(bad, key=lambda x: _SEV_ORDER.get(x[1].get("severity"), 9)):
            det = str(c.get("detail", "")).replace("|", "\\|")
            out.append(f"| {c['severity']} | `{r['repo']}` ({r['analysis'].upper()}) | "
                       f"`{c['check']}` | {det} |")
        out.append("")

    # Glossary. Only the checks that actually FIRED, so the doc explains what is on screen
    # rather than making the reader filter a catalogue of 11 for the 2 that matter.
    fired = {c.get("check") for _, c in bad}
    out.append("## What the checks mean")
    out.append("")
    out.append("Each check asserts a report is internally consistent. All are deterministic "
               "arithmetic — no LLM, no sampling — so a failure is a genuine defect "
               "regardless of how many runs we have.")
    out.append("")
    if fired:
        out.append("| Check | Severity | What a failure means |")
        out.append("|---|---|---|")
        for name in sorted(fired, key=lambda n: _SEV_ORDER.get(
                (CHECK_MEANINGS.get(n) or ("low",))[0], 9)):
            sev, meaning = CHECK_MEANINGS.get(
                name, ("?", "(no description registered for this check)"))
            out.append(f"| `{name}` | {sev} | {meaning} |")
        out.append("")
        quiet = [n for n in CHECK_MEANINGS if n not in fired]
        if quiet:
            out.append(f"The other {len(quiet)} checks passed everywhere: "
                       + ", ".join(f"`{n}`" for n in sorted(quiet)) + ".")
            out.append("")
    else:
        out.append("All checks passed on every report. The full set: "
                   + ", ".join(f"`{n}`" for n in sorted(CHECK_MEANINGS)) + ".")
        out.append("")

    findings = [r for r in rows if r.get("fabrications") or r.get("misses")
                or r.get("deliverable_defects")]
    if findings:
        out.append("## Per-report grader notes")
        out.append("")
        out.append("<details><summary>Fabrications and misses per report "
                   f"({len(findings)} reports)</summary>")
        out.append("")
        for r in findings:
            out.append(f"### `{r['repo']}` ({r['analysis'].upper()}) — {r.get('score')}")
            out.append("")
            if r.get("summary"):
                out.append(str(r["summary"]))
                out.append("")
            for f in r.get("fabrications") or []:
                out.append(f"- **FABRICATION** {f.get('question_id')}: {f.get('why_wrong')}")
            for m in r.get("misses") or []:
                out.append(f"- **MISS** [{m.get('severity_should_be')}] "
                           f"{m.get('where')}: {m.get('what')}")
            for d in r.get("deliverable_defects") or []:
                out.append(f"- **DELIVERABLE** {d.get('deliverable')}: "
                           f"{d.get('what_is_wrong')}")
            out.append("")
        out.append("</details>")
        out.append("")

    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
