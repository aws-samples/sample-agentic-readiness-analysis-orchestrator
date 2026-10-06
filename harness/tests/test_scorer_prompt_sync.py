#!/usr/bin/env python3
"""
Tests for scorer-prompt-sync.py — the drift gate between the TD and the EXTERNAL Benchmark
scorer prompts (harness/rubric/{ara,mod}-scorer-prompt.md).

WHY THIS MATTERS
The in-repo grader (score-reports.py) parses the TD on every run, so it can never go stale.
The external prompts bake the same TD facts in as literal text and are published to a
separate platform — so they DO go stale the instant a severity, count, tier or question
changes in SKILL.md, and nothing downstream notices. This tool (and this test) is the only
thing that turns such a drift into a red CI signal that says "re-generate and re-publish".

The load-bearing test is test_committed_prompts_are_in_sync_with_the_td: it fails the moment
the TD is edited without re-running `--write`, which is exactly the moment the published
prompt would silently diverge.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_scorer_prompt_sync.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "scorer_prompt_sync", REPO / "harness" / "scorer-prompt-sync.py")
sps = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sps)  # type: ignore


# --- the load-bearing gate ------------------------------------------------------------

def test_committed_prompts_are_in_sync_with_the_td():
    """The CI gate. If this fails, the TD moved but the published scorer prompt did not —
    run `python3 harness/scorer-prompt-sync.py --write`, review, and re-publish to Benchmark."""
    assert sps.run(write=False) == 0


def test_each_committed_lock_matches_derived_facts():
    for analysis in ("ara", "mod"):
        facts = sps.derive_facts(analysis)
        committed = json.loads(sps.LOCK[analysis].read_text())
        assert committed["analysis"] == analysis
        assert committed["facts"] == facts, f"{analysis} lock is stale vs the TD"
        assert committed["fingerprint"] == sps._fingerprint(facts)


def test_committed_gen_blocks_equal_the_renderers():
    for analysis in ("ara", "mod"):
        text = sps.PROMPT[analysis].read_text()
        _, stale = sps.apply_blocks(text, analysis, write=False)
        assert stale == [], f"{analysis} has stale GEN blocks: {stale}"


# --- the drift the tool was built to catch --------------------------------------------

def test_ara_severity_table_pins_the_live_counts():
    # The committed prompt shipped "RISK-SAFETY (16)" while the live rubric has 12 — the
    # exact drift that motivated the tool. Pin the derived counts so a regression is loud.
    table = sps.render_ara_severity_table()
    assert "RISK-SAFETY (12):" in table
    assert "BLOCKER (2 default, 7 with conditionals):" in table
    assert "RISK-QUALITY (17):" in table
    assert "INFO (7):" in table


def test_ara_tier_ladder_is_the_rubric_arithmetic():
    # Collapse the alignment padding so the assertion doesn't pin the exact column width.
    ladder = " ".join(sps.render_ara_tier().split())
    assert "risk_safety_count >= 3 -> Pilot-Ready (Safety Concerns)" in ladder
    assert "blocker_count >= 3 (any risk_safety_count) -> Not Agent-Integrable" in ladder


def test_mod_bands_render_from_the_rubric():
    assert sps.render_mod_bands() == (
        ">= 3.5 Mature | 2.5-3.4 Partial | 1.5-2.4 Needs Work | < 1.5 Not Ready")


# --- GEN marker plumbing --------------------------------------------------------------

def test_apply_blocks_regenerates_a_stale_block():
    # A hand-corrupted count between the markers must be rewritten to the derived value.
    good = sps.render_mod_catalog()
    bad = good.replace("(INF, 11)", "(INF, 99)")
    text = f"pre\n<!-- GEN:mod-question-catalog -->\n{bad}\n<!-- /GEN:mod-question-catalog -->\npost\n"
    new_text, stale = sps.apply_blocks(text, "mod", write=True)
    assert stale == ["mod-question-catalog"]
    assert "(INF, 11)" in new_text and "(INF, 99)" not in new_text


def test_apply_blocks_reports_stale_without_writing_when_check():
    good = sps.render_mod_catalog()
    bad = good.replace("(INF, 11)", "(INF, 99)")
    text = f"<!-- GEN:mod-question-catalog -->\n{bad}\n<!-- /GEN:mod-question-catalog -->\n"
    new_text, stale = sps.apply_blocks(text, "mod", write=False)
    assert stale == ["mod-question-catalog"]
    assert new_text == text, "check mode must not mutate the text"


def test_missing_marker_is_a_hard_error():
    import pytest
    with pytest.raises(SystemExit):
        sps.apply_blocks("no markers here", "mod", write=False)


# --- lock fingerprint / diff ----------------------------------------------------------

def test_fingerprint_is_stable_and_key_order_independent():
    a = {"n_questions": 2, "questions": {"B": 1, "A": 2}}
    b = {"questions": {"A": 2, "B": 1}, "n_questions": 2}
    assert sps._fingerprint(a) == sps._fingerprint(b)


def test_diff_names_the_exact_fact_that_moved():
    old = {"questions": {"AUTH-Q2": {"severity": "RISK-SAFETY"}}}
    new = {"questions": {"AUTH-Q2": {"severity": "BLOCKER"}}}
    lines = sps._diff(old, new)
    joined = "\n".join(lines)
    assert "questions.AUTH-Q2.severity" in joined
    assert "RISK-SAFETY" in joined and "BLOCKER" in joined


def test_diff_flags_added_and_removed_keys():
    lines = sps._diff({"a": 1}, {"a": 1, "b": 2})
    assert any(l.strip().startswith("+ b") for l in lines)
    lines = sps._diff({"a": 1, "b": 2}, {"a": 1})
    assert any(l.strip().startswith("- b") for l in lines)


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
