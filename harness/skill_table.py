"""Shared read of the managed TDs' question/severity tables.

The TDs are the single source of truth for question severities. Parsing them beats
hardcoding: a hardcoded table goes stale SILENTLY the moment someone edits a severity,
which is precisely the drift this harness exists to catch.

This module exists so the differ (`diff-reports.py`) and the judge (`judge.py`) reason
about severity from the SAME parsed table. It was extracted from the retired
`score-reports.py`; the parser is unchanged, only relocated.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[1]

# The four managed TDs whose severity tables we parse. Portfolio TDs roll these up and add
# no per-question severities of their own, so only the two per-repo analyses appear here.
SKILLS = {
    "ara": REPO / "definitions" / "managed" / "agentic-readiness-analysis" / "SKILL.md",
    "mod": REPO / "definitions" / "managed" / "modernization-readiness-analysis" / "SKILL.md",
}

# Rubric sizes. Kept as literals ON PURPOSE even though parse_questions() derives the same
# numbers from SKILL.md: these are the independent check that the parse is right. If a
# heading regex drifts and silently yields 41, callers can assert against these.
#
# A NAIVE grep over MOD's headings returns 38, not 37 — INF-Q1 "Managed Compute" appears
# twice. Dedup by question id (parse_questions does) and the 11/6/4/7/9 split is exact.
EXPECTED_QUESTIONS = {"ara": 43, "mod": 37}

# `#### API-Q4: Idempotent Write Operations — BLOCKER ⚡ (Conditional)`
# ARA headings carry the severity; MOD headings are `#### INF-Q1: Managed Compute` with no
# severity (MOD scores 1-4 per question instead), so the severity group is optional.
_Q_HEADING = re.compile(
    r"^#### ((?:API|AUTH|STATE|HITL|DATA|DISC|OBS|ENG|INF|APP|SEC|OPS)-Q\d+):"
    r"\s*(.+?)\s*(?:—\s*(.+?))?\s*$", re.M)

# Severity classes ordered most -> least severe. Shared with diff-reports' relaxation check.
SEVERITY_RANK = {"BLOCKER": 3, "RISK-SAFETY": 2, "RISK-QUALITY": 1, "INFO": 0}


def rel(path: Path) -> str:
    """Repo-relative path — both SKILL.md files share a basename, so `.name` is ambiguous
    in a prompt and useless in an assertion message."""
    return str(path.relative_to(REPO))


def parse_questions(analysis: str) -> dict[str, dict]:
    """Extract {qid: {title, severity, conditional}} from a TD, in document order.

    Deduplicates by qid, keeping the FIRST occurrence (MOD repeats INF-Q1). Returns {} if
    the TD is missing rather than raising — callers assert on the count, which gives a far
    more useful error than a stack trace from a regex that matched nothing.
    """
    path = SKILLS.get(analysis)
    if not path or not path.exists():
        return {}
    out: dict[str, dict] = {}
    for qid, title, sev in _Q_HEADING.findall(path.read_text(encoding="utf-8")):
        if qid in out:
            continue
        raw = (sev or "").strip()
        # "BLOCKER ⚡ (Conditional)" -> severity BLOCKER, conditional marker separately.
        # The marker is load-bearing: it is what tells a downstream check that a
        # read-only-scope downgrade is CORRECT rather than an understatement.
        out[qid] = {
            "title": title.strip(),
            "severity": raw.split("⚡")[0].replace("*", "").strip(),
            "conditional": "⚡" in raw,
        }
    return out


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


def is_over_escalation_correction(
        analysis: str, qid: Optional[str],
        before: Optional[str], after: Optional[str]) -> bool:
    """True when a severity DOWNGRADE brings a finding INTO LINE with the TD's own table.

    This is the distinction the harness was missing: a lost BLOCKER is only a safety
    relaxation if the BLOCKER was *correct*. AUTH-Q5 (Credential Management) is documented
    RISK-SAFETY unconditionally (SKILL.md:870); a report that emitted it as BLOCKER was
    OVER-escalating, and `BLOCKER -> RISK-SAFETY` is a *correction*, not a relaxation — it
    must not force a safety hold or read as a degradation.

    Deliberately conservative — returns True ONLY when all of:
      - the TD documents this qid with a fixed (non-conditional) severity, AND
      - `before` was strictly MORE severe than that documented severity, AND
      - `after` equals the documented severity exactly.

    So it never exempts:
      - conditional blockers (the 5 ⚡ questions) — their severity is scope-dependent, so a
        downgrade there is a real judgement call, not a mechanical correction;
      - an UNDER-statement (`after` less severe than documented) — that is the dangerous
        direction and must still alert;
      - a partial move that overshoots or undershoots the documented level.
    """
    if not qid:
        return False
    q = parse_questions(analysis).get(str(qid))
    if not q or q.get("conditional"):
        return False
    documented = SEVERITY_RANK.get(str(q.get("severity") or "").strip().upper())
    b = SEVERITY_RANK.get(str(before or "").strip().upper())
    a = SEVERITY_RANK.get(str(after or "").strip().upper())
    if documented is None or b is None or a is None:
        return False
    return b > documented and a == documented
