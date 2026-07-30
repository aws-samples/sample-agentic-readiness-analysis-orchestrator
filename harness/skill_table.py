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

# Shared by every parser here. Both TDs prefix question ids by section.
_QID = r"(?:API|AUTH|STATE|HITL|DATA|DISC|OBS|ENG|INF|APP|SEC|OPS)-Q\d+"

# `#### API-Q4: Idempotent Write Operations — BLOCKER ⚡ (Conditional)`
# ARA headings carry the severity; MOD headings are `#### INF-Q1: Managed Compute` with no
# severity (MOD scores 1-4 per question instead), so the severity group is optional.
_Q_HEADING = re.compile(
    rf"^#### ({_QID}):\s*(.+?)\s*(?:—\s*(.+?))?\s*$", re.M)

# Severity classes ordered most -> least severe. Shared with diff-reports' relaxation check.
SEVERITY_RANK = {"BLOCKER": 3, "RISK-SAFETY": 2, "RISK-QUALITY": 1, "INFO": 0}


def rel(path: Path) -> str:
    """Repo-relative path — both SKILL.md files share a basename, so `.name` is ambiguous
    in a prompt and useless in an assertion message.

    Resolves first, so a path given relative to the cwd (e.g. an `--markdown` argument)
    still lands inside REPO instead of raising. Anything genuinely outside the repo is
    returned as-is: this function only ever builds log lines and prompt text, so it must
    not be able to fail a run that has already done its expensive work.
    """
    try:
        return str(Path(path).resolve().relative_to(REPO))
    except ValueError:
        return str(path)


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


def _owning_qid(text: str, pos: int) -> Optional[str]:
    """The question whose `#### <QID>:` heading most recently precedes `pos`.

    Calibration rules live in prose paragraphs UNDER their question's heading, with no id of
    their own, so position is the only thing that binds a rule to its question.
    """
    last = None
    for m in _Q_HEADING.finditer(text):
        if m.start() > pos:
            break
        last = m.group(1)
    return last


def _expand_range(spec: str) -> list[str]:
    """`API-Q1 through API-Q8` -> the 8 ids. Plain ids pass through unchanged.

    The N/A tables write runs as ranges, so a literal id scan silently sees 2 of 8.
    """
    out: list[str] = []
    for part in re.split(r",| and ", spec):
        # Strip markdown emphasis and code ticks: the "except" keyword is bold in the TD
        # (`**except**`), which otherwise leaves a leading `**` glued to the first range.
        part = part.strip().strip("*").strip("`").strip()
        rng = re.match(rf"^({_QID})\s+through\s+({_QID})$", part)
        if rng:
            (sec, lo), (_, hi) = (rng.group(1).split("-Q"), rng.group(2).split("-Q"))
            out += [f"{sec}-Q{n}" for n in range(int(lo), int(hi) + 1)]
        elif re.match(rf"^{_QID}$", part):
            out.append(part)
    return out


def parse_scope_severities(analysis: str = "ara") -> dict[str, dict[str, str]]:
    """{qid: {"write-enabled": SEV, "read-only": SEV}} from the ⚡ conditional bullets.

    THIS IS WHY IT IS PARSED AND NOT ASSUMED. The obvious shortcut — "a conditional BLOCKER
    becomes RISK-SAFETY under read-only" — is WRONG for API-Q4, which the TD sends all the way
    to INFO (SKILL.md:719, "idempotency is informational only"). Only AUTH-Q6, STATE-Q1 and
    DATA-Q2 land on RISK-SAFETY. A blanket rule over-resolves API-Q4 by one full class on
    every read-only report, and since the prompt states these resolutions as authoritative it
    does not merely mis-grade — it actively licenses an over-escalation.
    """
    path = SKILLS.get(analysis)
    if not path or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {}
    # Two phrasings carry the same authoritative rule and BOTH must be parsed. Four of the five
    # conditional BLOCKERs (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q2) use the "When ... Evaluate as"
    # form; DATA-Q1 alone uses the "If ... → **SEV**" arrow form. Matching only the first
    # silently drops DATA-Q1 to `None`, which (a) withholds its read-only resolution from the
    # grader prompt and (b) leaves the ceiling check falling back to DATA-Q1's heading (BLOCKER)
    # as the ceiling — so a read-only report that resolves DATA-Q1 to BLOCKER (the TD says
    # RISK-SAFETY, SKILL.md:1176-1177) passes both gates unchallenged. The arrow pattern is
    # anchored on `agent_scope` so it ignores the non-scoped arrow bullets nearby (e.g. the
    # differentiation and aspirational rules), which key on evidence, not scope.
    patterns = (
        # - **When `agent_scope` is `"read-only"`:** Evaluate as **RISK-SAFETY**. ...
        re.compile(r"When `agent_scope` is `\"(write-enabled|read-only)\"`:\*\*\s*"
                   r"Evaluate as \*\*([A-Z][A-Z-]*)\*\*"),
        # - If `agent_scope` is `write-enabled` AND ... → **BLOCKER**
        re.compile(r"If `agent_scope` is `(write-enabled|read-only)`[^\n]*?"
                   r"→\s*\*\*([A-Z][A-Z-]*)\*\*"),
    )
    for pat in patterns:
        for m in pat.finditer(text):
            qid = _owning_qid(text, m.start())
            if qid:
                out.setdefault(qid, {})[m.group(1)] = m.group(2).strip()
    return out


def parse_calibrations(analysis: str = "ara") -> dict[str, list[dict[str, str]]]:
    """{qid: [{"kind": "surface-flag"|"archetype", "rule": <verbatim prose>}]}.

    Returned VERBATIM rather than compiled into predicates. The severity table is a table and
    parses cleanly; these are prose with nested boolean conditions ("if X is false AND Y is
    false", "or if the repo was classified as dev-library-application"), several of which also
    embed the exact rationale string the report is required to emit. A regex that tried to
    evaluate them would be the least trustworthy part of this harness. Handing the rule text
    to the grader alongside the report's ACTUAL flag values keeps the deterministic part
    (which flags are set) separate from the judgement (does this rule fire).
    """
    path = SKILLS.get(analysis)
    if not path or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[str, list[dict[str, str]]] = {}
    pat = re.compile(r"\*\*(Surface-flag|Archetype) [Cc]alibration:\*\*\s*(.+?)\s*$", re.M)
    for m in pat.finditer(text):
        qid = _owning_qid(text, m.start())
        if qid:
            out.setdefault(qid, []).append(
                {"kind": m.group(1).lower(), "rule": m.group(2).strip()})
    return out


def parse_extended(analysis: str = "ara") -> dict[str, str]:
    """{qid: trigger condition} for ARA's 18 extended questions.

    An untriggered extended question is recorded `not_evaluated_extended` and excluded from
    scoring (SKILL.md:49) — 88 such records across the 12 golden ARA reports, including
    STATE-Q4 in 9 of them. A grader told only that STATE-Q4 is RISK-SAFETY reads every one as
    an unresolved RISK-SAFETY question. This is the single largest source of false misses.
    """
    path = SKILLS.get(analysis)
    if not path or not path.exists():
        return {}
    out: dict[str, str] = {}
    # | STATE-Q4 | Service has external dependencies (calls other services or external APIs) |
    for m in re.finditer(rf"^\|\s*({_QID})\s*\|\s*([^|]+?)\s*\|\s*$",
                         path.read_text(encoding="utf-8"), re.M):
        out.setdefault(m.group(1), m.group(2).strip())
    return out


def parse_mod_surface_gates() -> dict[str, dict[str, str]]:
    """{qid: {"flag": <gate expression>, "when_false": <behaviour>}} from MOD's gate table.

    MOD's exclusions are arithmetically load-bearing in a way ARA's are not: a gated question
    leaves BOTH the numerator and the denominator of its category mean (SKILL.md:494-499), so
    a grader that thinks a gated question should have scored 1 also thinks the category mean
    and the overall band are wrong. One unstated rule cascades into three apparent defects.
    """
    path = SKILLS.get("mod")
    if not path or not path.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    # | **INF-Q2** (Managed Databases) | `has_persistent_data_store` | Not Evaluated ... |
    pat = re.compile(
        rf"^\|\s*\*\*({_QID})\*\*[^|]*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", re.M)
    for m in pat.finditer(path.read_text(encoding="utf-8")):
        out.setdefault(m.group(1), {"flag": m.group(2).strip().replace("`", ""),
                                    "when_false": m.group(3).strip()})
    return out


def parse_mod_archetype_calibrated() -> list[str]:
    """The MOD questions whose RUBRIC is archetype-keyed (INF-Q3/Q4, APP-Q3/Q4).

    Distinct from ARA's archetype calibration, and the difference matters to a grader: MOD's
    "can both downgrade and upgrade a score relative to the default rubric" (SKILL.md:150) —
    a `stateless-utility` scoring 4 on INF-Q4 for sync-only HTTP is the rubric working, where
    the same evidence scores 1 for an `orchestrator`. ARA calibration only ever downgrades.
    """
    path = SKILLS.get("mod")
    if not path or not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    out: list[str] = []
    for m in re.finditer(r"\*\*Archetype Calibration:\*\*", text):
        qid = _owning_qid(text, m.start())
        if qid and qid not in out:
            out.append(qid)
    return out


def parse_na_map(analysis: str) -> dict[str, list[str]]:
    """{repo_type: [qids that are N/A]} from the "N/A Question Mappings by Repo Type" table.

    Rows reading "None — all 43 questions apply" yield []. The `deployment-config` row is
    phrased as an EXCLUSION ("All questions N/A except ...") and is inverted here against the
    parsed question set, so it stays correct if the rubric grows.
    """
    path = SKILLS.get(analysis)
    if not path or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^### N/A Question Mappings by Repo Type\s*$(.+?)^###", text,
                  re.M | re.S)
    if not m:
        return {}
    every = list(parse_questions(analysis))
    out: dict[str, list[str]] = {}
    for row in re.finditer(r"^\|\s*`([a-z-]+)`\s*\|\s*([^|]+?)\s*\|\s*$", m.group(1), re.M):
        rtype, spec = row.group(1), row.group(2)
        if spec.lower().startswith("none"):
            out[rtype] = []
        elif "except" in spec.lower():
            keep = set(_expand_range(spec.split("except", 1)[1]))
            out[rtype] = [q for q in every if q not in keep]
        else:
            out[rtype] = _expand_range(spec)
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
