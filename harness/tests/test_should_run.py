#!/usr/bin/env python3
"""
Tests for should-run.sh — the deterministic run|skip gate.

The gate is DEFAULT-RUN: it runs the change-harness unless every changed path is either
denylisted (docs/license/meta) or a committed-baseline path (harness/golden/ + the
accuracy baseline). The baseline-only skip is the load-bearing one pinned here: a
re-baseline MR touches only the golden, and re-analyzing the fixtures against the very
golden the MR just wrote would diff a fresh nondeterministic draw against it — every
tier/blocker difference would be draw-vs-draw noise, which the judge surfaces as a FALSE
SAFETY HOLD. The golden was already validated upstream by the ratchet in
harness:rebaseline-gather, so there is nothing for this harness to evaluate.

If a denylist edit ever lets a golden-only MR RUN again, that false SAFETY HOLD comes
back on every weekly auto-rebaseline — so these tests exist to make that regression loud.

No AWS, no network: each case builds a throwaway git repo and diffs a feature branch
against a base branch, exactly as CI does.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_should_run.py
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "harness" / "should-run.sh"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _write(cwd: Path, rel: str, text: str) -> None:
    p = cwd / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture()
def repo():
    """A minimal repo with a `base` branch already carrying every path a case might touch."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git(root, "init")
        _git(root, "config", "user.email", "t@t.co")
        _git(root, "config", "user.name", "t")
        _write(root, "README.md", "base\n")
        _write(root, "harness/golden/x-ara-report.json", "g0\n")
        _write(root, "harness/golden-accuracy-baseline.json", "b0\n")
        _write(root, "definitions/managed/agentic-readiness-analysis/SKILL.md", "td0\n")
        _write(root, "harness/fixtures/portfolio/x/app.py", "f0\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "base")
        _git(root, "branch", "base")
        yield root


def _decide(repo: Path, mutate: dict[str, str]) -> bool:
    """Apply file edits on a fresh branch, run should-run.sh, return True if it says RUN."""
    _git(repo, "checkout", "-q", "base")
    _git(repo, "checkout", "-q", "-B", "feature")
    for rel, text in mutate.items():
        _write(repo, rel, text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "case")
    # Keep the emitted dotenv OUT of the work tree so it never blocks the next checkout.
    with tempfile.TemporaryDirectory() as envdir:
        env = {"SHOULD_RUN_ENV": str(Path(envdir) / "sr.env"),
               "PATH": __import__("os").environ["PATH"]}
        proc = subprocess.run(["bash", str(SCRIPT), "base"], cwd=repo, env=env,
                              capture_output=True, text=True)
    # exit 0 => RUN, exit 1 => SKIP (see the script header).
    assert proc.returncode in (0, 1), f"unexpected exit {proc.returncode}: {proc.stderr}"
    return proc.returncode == 0


def test_golden_only_change_skips(repo):
    """A re-baseline MR (golden report tree + accuracy baseline) must SKIP.

    This is the whole point: no re-analysis, no judge, no false SAFETY HOLD from diffing a
    fresh draw against the golden the MR just wrote.
    """
    assert _decide(repo, {
        "harness/golden/x-ara-report.json": "g1\n",
        "harness/golden-accuracy-baseline.json": "b1\n",
    }) is False


def test_accuracy_baseline_only_change_skips(repo):
    assert _decide(repo, {"harness/golden-accuracy-baseline.json": "b1\n"}) is False


def test_golden_plus_td_change_runs(repo):
    """A golden change RIDING ALONG with a TD edit still RUNS — the TD edit is the thing
    to evaluate, and a contributor who added a question lands both together."""
    assert _decide(repo, {
        "harness/golden/x-ara-report.json": "g1\n",
        "definitions/managed/agentic-readiness-analysis/SKILL.md": "td1\n",
    }) is True


def test_golden_plus_fixture_change_runs(repo):
    assert _decide(repo, {
        "harness/golden/x-ara-report.json": "g1\n",
        "harness/fixtures/portfolio/x/app.py": "f1\n",
    }) is True


def test_td_only_change_runs(repo):
    assert _decide(repo, {
        "definitions/managed/agentic-readiness-analysis/SKILL.md": "td1\n",
    }) is True


def test_docs_only_change_skips(repo):
    assert _decide(repo, {"README.md": "base\nmore\n"}) is False


def test_scorer_sync_bot_commit_skips(repo):
    """The harness:scorer-sync bot's auto-commit touches ONLY the external Benchmark scorer
    prompt (.md, caught by the docs arm) and its facts-lock (.json). Neither feeds the
    in-repo grader, so this must SKIP — otherwise every auto-sync would re-trigger a full,
    hours-long atx sweep on a change that provably cannot move analysis output."""
    assert _decide(repo, {
        "harness/rubric/ara-scorer-prompt.md": "regenerated\n",
        "harness/rubric/ara-scorer-facts.lock.json": '{"n": 1}\n',
    }) is False


def test_scorer_lock_riding_with_td_change_runs(repo):
    """The lock is only inert on its OWN. A lock change accompanying a real TD edit still
    RUNS — the TD edit is the thing to evaluate, and both land together on the branch."""
    assert _decide(repo, {
        "harness/rubric/ara-scorer-facts.lock.json": '{"n": 2}\n',
        "definitions/managed/agentic-readiness-analysis/SKILL.md": "td1\n",
    }) is True


def test_rebaseline_digest_only_change_skips(repo):
    """The digest renderer is a render-only consumer of JSON the gather job already produced,
    and runs only in the rebaseline gather/post path — never in the analyze path — so it
    cannot move analysis output. A digest-only edit must SKIP the atx sweep; its correctness
    is covered by harness/tests/test_rebaseline_digest.py, not the sweep."""
    assert _decide(repo, {"harness/rebaseline-digest.py": "print('x')\n"}) is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
