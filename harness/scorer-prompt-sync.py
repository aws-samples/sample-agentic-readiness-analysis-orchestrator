#!/usr/bin/env python3
"""
scorer-prompt-sync.py — keep the external Benchmark scorer prompts honest against the TD.

WHY THIS EXISTS
There are two scorers, built from ONE source of truth (the managed TD SKILL.md):
  1. harness/score-reports.py — the IN-REPO live grader. It PARSES the TD on every run,
     so the facts it feeds the model can never go stale.
  2. harness/rubric/{ara,mod}-scorer-prompt.md — the EXTERNAL, self-contained prompt
     published to the external benchmarking platform. Its TD facts are BAKED IN as literal
     text and hand-maintained, so they DO go stale the moment a severity, calibration,
     surface gate, extended trigger, or N/A mapping changes in the TD.

This script closes that gap. It DERIVES every TD fact the external prompt depends on from
the same parsers score-reports.py uses (skill_table.py), and:

  --check  (default)  Fails (exit 1) when the derived facts no longer match the committed
                      facts-lock, OR when a GEN-marked block in the .md is stale. The
                      message names EXACTLY which fact moved. That is the signal that the
                      Benchmark scorer prompt must be re-generated and re-published — and,
                      just as importantly, its silence is the signal that a TD edit did NOT
                      touch the baked-in facts, so the published prompt can stay as-is.
  --write             Regenerates the GEN-marked mechanical blocks in the .md and rewrites
                      the facts-lock. Review the diff, hand-update any tuned PROSE the
                      change implies (calibration/extended/N/A wording — see below), then
                      re-publish the prompt.

WHAT IS DERIVED vs HAND-OWNED
  * Derived + auto-regenerated in place (GEN markers): the severity/question table and the
    tier arithmetic — pure mechanical renders of the parsed rubric. Never hand-edit these;
    edit the TD and run --write.
  * Derived + drift-detected only (in the lock, NOT auto-written): calibration rules,
    extended triggers, surface gates, N/A mappings. These live as TUNED PROSE in the .md
    that a regex cannot safely rewrite, but the lock still fingerprints them, so a TD edit
    that changes them fails --check and tells you which prose section to hand-edit.
  * Hand-owned, not tracked here: the scoring scale, "one root cause = one item", the
    ownership notes — judging policy, not TD fact.

Run:  python3 harness/scorer-prompt-sync.py --check     # CI gate
      python3 harness/scorer-prompt-sync.py --write      # after a TD edit
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
RUBRIC = HARNESS / "rubric"
sys.path.insert(0, str(HARNESS))

import skill_table as st  # noqa: E402


def _import_score_reports():
    """score-reports.py has a hyphen, so it cannot be a normal import. We only need its
    hand-written ownership notes — the one bit of the severity table that is judging
    policy rather than a parsed TD fact, kept in exactly one place."""
    spec = importlib.util.spec_from_file_location("score_reports", HARNESS / "score-reports.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


_OWNERSHIP_NOTES = _import_score_reports()._OWNERSHIP_NOTES

# ---------------------------------------------------------------------------------------
# Display labels. These are the human-facing section/category NAMES, not TD facts — the
# TD carries the qid prefixes (API, AUTH, ...) and the counts, which we derive. The prose
# name of a section does not drift with a severity edit, so it is safe to keep it here.
# ---------------------------------------------------------------------------------------
ARA_SECTIONS = [
    ("API", "API Surface"), ("AUTH", "Authentication & Authorization"),
    ("STATE", "State Management"), ("HITL", "Human-in-the-Loop"),
    ("DATA", "Data Accessibility"), ("DISC", "Discovery & Documentation"),
    ("OBS", "Observability"), ("ENG", "Engineering Maturity"),
]
MOD_CATEGORIES = [
    ("INF", "INFRASTRUCTURE & DevOps"), ("APP", "APPLICATION ARCHITECTURE"),
    ("DATA", "DATA PLATFORM"), ("SEC", "SECURITY BASELINE"),
    ("OPS", "OPERATIONS & OBSERVABILITY"),
]
_SEV_ORDER = ["BLOCKER", "RISK-SAFETY", "RISK-QUALITY", "INFO"]


# ---------------------------------------------------------------------------------------
# Fact derivation — the canonical, machine-diffable snapshot of everything the external
# prompt bakes in. This dict IS the lock. Keep it pure data (no rendered prose beyond the
# two hardcoded ladders) so a diff points at a rubric fact, not a formatting choice.
# ---------------------------------------------------------------------------------------
def derive_facts(analysis: str) -> dict:
    qs = st.parse_questions(analysis)
    facts: dict = {
        "n_questions": len(qs),
        "questions": {
            qid: {"title": q["title"], "severity": q["severity"],
                  "conditional": bool(q["conditional"])}
            for qid, q in qs.items()
        },
        "na_map": st.parse_na_map(analysis),
    }
    if analysis == "ara":
        facts["scope_severities"] = st.parse_scope_severities("ara")
        facts["calibrations"] = {
            qid: [d["rule"] for d in rules]
            for qid, rules in st.parse_calibrations("ara").items()
        }
        facts["extended"] = st.parse_extended("ara")
        # Tier arithmetic is hardcoded in skill_table (SKILL.md 1569-1573), not parsed;
        # locking the rendered ladder catches a skill_table edit too.
        facts["tier_ladder"] = render_ara_tier()
    else:
        facts["surface_gates"] = st.parse_mod_surface_gates()
        facts["archetype_calibrated"] = st.parse_mod_archetype_calibrated()
        facts["score_bands"] = render_mod_bands()
    return facts


# ---------------------------------------------------------------------------------------
# Renderers for the GEN-marked mechanical blocks. Output format matches the committed .md
# so the first --write is a minimal, correct diff (it fixes drift, it does not reflow).
# ---------------------------------------------------------------------------------------
def _wrap_sections(prefix: str, parts: list[str], suffix: str, per_line: int = 3) -> str:
    """Render the 8-section / 5-category summary paragraph with a stable line break every
    `per_line` items, so the generated text is deterministic run-to-run."""
    lines, chunk = [], []
    for i, p in enumerate(parts):
        chunk.append(p)
        if len(chunk) == per_line and i != len(parts) - 1:
            lines.append(", ".join(chunk) + ",")
            chunk = []
    if chunk:
        lines.append(", ".join(chunk))
    body = "\n".join(lines)
    return f"{prefix}{body}{suffix}"


def render_ara_severity_table() -> str:
    qs = st.parse_questions("ara")
    order = list(qs)  # document order, for stable within-group ordering
    by_sev: dict[str, list[str]] = {s: [] for s in _SEV_ORDER}
    for idx, (qid, q) in enumerate(qs.items()):
        by_sev.setdefault(q["severity"], []).append(qid)
    blocks: list[str] = []
    for sev in _SEV_ORDER:
        qids = by_sev.get(sev, [])
        # non-conditional first (document order), then conditional (document order)
        qids.sort(key=lambda x: (qs[x]["conditional"], order.index(x)))
        n_cond = sum(1 for x in qids if qs[x]["conditional"])
        if sev == "BLOCKER" and n_cond:
            header = f"BLOCKER ({len(qids) - n_cond} default, {len(qids)} with conditionals):"
        else:
            header = f"{sev} ({len(qids)}):"
        lines = [header]
        for qid in qids:
            q = qs[qid]
            mark = " [C]" if (q["conditional"] and sev == "BLOCKER") else (
                " [S]" if q["conditional"] else "")
            lines.append(f"  - {qid} {q['title']}{mark}")
            note = _OWNERSHIP_NOTES.get(qid)
            if note:
                wrapped = note.replace(". ", ".\n         ")  # keep the sub-bullet readable
                lines.append(f"      -> {wrapped}")
        blocks.append("\n".join(lines))

    counts = {p: sum(1 for qid in qs if qid.split("-")[0] == p) for p, _ in ARA_SECTIONS}
    parts = [f"{name} ({p}, {counts[p]} q)" for p, name in ARA_SECTIONS]
    section_para = _wrap_sections(
        "(The severity groupings above are not the 8 rubric sections. The 8 sections are: ",
        parts, f" = {len(qs)}.)")
    return "\n".join(blocks) + "\n\n" + section_para


def render_ara_tier() -> str:
    rows = [
        ("blocker_count 0 AND risk_safety_count 0", 0, 0),
        ("blocker_count 0 AND risk_safety_count 1-2", 0, 1),
        ("blocker_count 0 AND risk_safety_count >= 3", 0, 3),
        ("blocker_count 1-2 (any risk_safety_count)", 1, 0),
        ("blocker_count >= 3 (any risk_safety_count)", 3, 0),
    ]
    width = max(len(label) for label, _, _ in rows)
    out = []
    for label, b, rs in rows:
        tier, qual = st.expected_ara_tier(b, rs)
        got = f"{tier} ({qual})" if qual else tier
        out.append(f"  - {label:<{width}} -> {got}")
    return "\n".join(out)


def render_mod_catalog() -> str:
    qs = st.parse_questions("mod")
    by_cat: dict[str, list[str]] = {}
    for qid in qs:
        by_cat.setdefault(qid.split("-")[0], []).append(qid)
    blocks = []
    for prefix, name in MOD_CATEGORIES:
        qids = by_cat.get(prefix, [])
        lines = [f"{name} ({prefix}, {len(qids)}):"]
        for qid in qids:
            lines.append(f"  - {qid} {qs[qid]['title']}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def render_mod_bands() -> str:
    return (f">= 3.5 {st.mod_band(3.5)} | 2.5-3.4 {st.mod_band(2.5)} | "
            f"1.5-2.4 {st.mod_band(1.5)} | < 1.5 {st.mod_band(1.0)}")


# name -> (analysis, renderer). Only PURE mechanical blocks belong here; tuned prose stays
# hand-owned and is covered by the lock instead.
BLOCKS = {
    "ara-severity-table": ("ara", render_ara_severity_table),
    "ara-tier-arithmetic": ("ara", render_ara_tier),
    "mod-question-catalog": ("mod", render_mod_catalog),
}
PROMPT = {"ara": RUBRIC / "ara-scorer-prompt.md", "mod": RUBRIC / "mod-scorer-prompt.md"}
LOCK = {"ara": RUBRIC / "ara-scorer-facts.lock.json", "mod": RUBRIC / "mod-scorer-facts.lock.json"}


# ---------------------------------------------------------------------------------------
# GEN marker plumbing.  <!-- GEN:name --> ... <!-- /GEN:name -->
# ---------------------------------------------------------------------------------------
def _marker_re(name: str) -> re.Pattern:
    return re.compile(
        rf"(<!-- GEN:{re.escape(name)}[^\n]*-->\n)(.*?)(\n<!-- /GEN:{re.escape(name)} -->)",
        re.S)


def apply_blocks(text: str, analysis: str, *, write: bool) -> tuple[str, list[str]]:
    """Replace (write) or diff (check) every GEN block for `analysis`. Returns the new
    text and the list of block names whose committed content is stale."""
    stale: list[str] = []
    for name, (block_analysis, render) in BLOCKS.items():
        if block_analysis != analysis:
            continue
        pat = _marker_re(name)
        m = pat.search(text)
        if not m:
            raise SystemExit(
                f"ERROR: {PROMPT[analysis].name} is missing the GEN:{name} marker pair. "
                f"Add\n    <!-- GEN:{name} -->\n    ...\n    <!-- /GEN:{name} -->\naround "
                f"the block so it can be kept in sync.")
        generated = render()
        if m.group(2) != generated:
            stale.append(name)
            if write:
                text = text[:m.start()] + m.group(1) + generated + m.group(3) + text[m.end():]
    return text, stale


# ---------------------------------------------------------------------------------------
# Lock plumbing.
# ---------------------------------------------------------------------------------------
def _canonical(facts: dict) -> str:
    return json.dumps(facts, indent=2, sort_keys=True, ensure_ascii=False)


def _fingerprint(facts: dict) -> str:
    return hashlib.sha256(_canonical(facts).encode()).hexdigest()


def lock_payload(analysis: str, facts: dict) -> dict:
    return {"analysis": analysis, "fingerprint": _fingerprint(facts), "facts": facts}


def _diff(old, new, path=""):
    """Human-readable list of the JSON paths that changed between two fact snapshots."""
    out = []
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            p = f"{path}.{k}" if path else k
            if k not in old:
                out.append(f"  + {p}")
            elif k not in new:
                out.append(f"  - {p}")
            else:
                out += _diff(old[k], new[k], p)
    elif old != new:
        out.append(f"  ~ {path}: {_short(old)} -> {_short(new)}")
    return out


def _short(v) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 70 else s[:67] + "..."


# ---------------------------------------------------------------------------------------
# Commands.
# ---------------------------------------------------------------------------------------
def run(write: bool) -> int:
    problems = 0
    for analysis in ("ara", "mod"):
        facts = derive_facts(analysis)
        prompt_path, lock_path = PROMPT[analysis], LOCK[analysis]

        # 1) GEN blocks in the .md
        text = prompt_path.read_text()
        new_text, stale = apply_blocks(text, analysis, write=write)
        if write and new_text != text:
            prompt_path.write_text(new_text)

        # 2) the facts lock
        committed = json.loads(lock_path.read_text()) if lock_path.exists() else None
        lock_changed = committed is None or committed.get("facts") != facts
        if write and lock_changed:
            lock_path.write_text(_canonical(lock_payload(analysis, facts)) + "\n")

        # 3) report
        tag = analysis.upper()
        if write:
            if stale:
                print(f"[{tag}] regenerated GEN blocks: {', '.join(stale)}")
            if lock_changed:
                print(f"[{tag}] rewrote facts-lock {lock_path.name}")
                if committed is not None:
                    for line in _diff(committed.get("facts", {}), facts):
                        print(line)
            if not stale and not lock_changed:
                print(f"[{tag}] already in sync")
        else:
            if stale:
                problems += 1
                print(f"[{tag}] STALE GEN block(s) in {prompt_path.name}: "
                      f"{', '.join(stale)} — run: python3 harness/scorer-prompt-sync.py --write")
            if lock_changed:
                problems += 1
                if committed is None:
                    print(f"[{tag}] no facts-lock yet ({lock_path.name}) — run --write")
                else:
                    print(f"[{tag}] TD facts drifted from {lock_path.name} — the baked-in "
                          f"facts in {prompt_path.name} are stale; re-generate and RE-PUBLISH "
                          f"the Benchmark scorer. Changed:")
                    for line in _diff(committed.get("facts", {}), facts):
                        print(line)
            if not stale and not lock_changed:
                print(f"[{tag}] in sync — no re-publish needed")

    if not write and problems:
        print(f"\n{problems} drift issue(s). The external scorer prompt(s) no longer match "
              f"the TD.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true",
                   help="(default) fail if the prompts have drifted from the TD")
    g.add_argument("--write", action="store_true",
                   help="regenerate GEN blocks and rewrite the facts-lock")
    args = ap.parse_args(argv)
    return run(write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
