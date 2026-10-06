#!/usr/bin/env python3
"""
Tests for run-fixtures.sh --shard I/N and --portfolio-only.

These two flags exist so a full re-baseline can be split across N CI jobs, each with its
OWN fresh AWS credential vend. The AWS Credential Vendor assumes our role via ROLE CHAINING,
which AWS hard-caps at 1 HOUR regardless of MaxSessionDuration — so a single job running all
28 units (~2h wall-clock at jobs=6) physically cannot finish before its own creds expire. It
did exactly that on the first RESET re-baseline: 21 of 28 units passed, then every later exec
died with "security token expired". Sharding removes the deadline as a factor: each shard runs
a disjoint slice well under the hour, and a final --portfolio-only gather step (fresh vend,
seconds of work) rolls the merged per-repo reports up.

Two invariants are load-bearing and pinned here:

1. The shards PARTITION the fixture list — disjoint (no unit runs twice, doubling the bill and
   racing two execs into one report name) AND complete (every fixture lands in exactly one
   shard, or a silently-dropped fixture rots the baseline).
2. A shard NEVER runs the portfolio rollup (it only sees its own slice; the rollup needs all
   per-repo reports), and --portfolio-only runs ONLY the rollup (no per-repo execs).

No AWS, no atx: every case runs with --dry-run, which prints the atx commands it WOULD run to
stderr. We assert on those printed markers.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_run_fixtures_shard.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "harness" / "run-fixtures.sh"
USECASES = REPO / "harness" / "usecases.yaml"


def _all_fixture_names() -> list[str]:
    doc = yaml.safe_load(USECASES.read_text(encoding="utf-8"))
    return [Path(f["path"]).name for f in doc.get("fixtures", [])]


def _env(tmp: str, **extra: str) -> dict:
    # Inherit the real environment, and put THIS interpreter's dir first on PATH so the
    # script's bare `python3` resolves to the same one running pytest — the one with PyYAML.
    # (usecases.yaml is read via `python3 - <<PY ... import yaml`; a python3 without PyYAML
    # silently yields an empty fixture list, and every shard then has nothing to run.)
    # Do NOT override HOME: PyYAML is installed in the USER site-packages ($HOME/.local/...),
    # which Python locates via HOME — repointing it hides yaml. Only AFTER_DIR is redirected
    # to keep the (dry-run) output out of the repo.
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), env.get("PATH", "")])
    env["AFTER_DIR"] = str(Path(tmp) / "after")
    env.update(extra)
    return env


def _run(*args: str) -> subprocess.CompletedProcess:
    """Run run-fixtures.sh --dry-run with a throwaway AFTER_DIR. Never touches AWS."""
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["bash", str(SCRIPT), "--scope", "all", "--dry-run", *args]
        return subprocess.run(cmd, env=_env(tmp), capture_output=True, text=True, timeout=120)


# The per-repo exec markers run_unit prints: "=== ARA: <name> ===" / "=== MOD: <name> ===".
_UNIT_RE = re.compile(r"^=== (ARA|MOD): (\S+) ===$", re.M)
# The portfolio phase markers run_portfolio_exec's caller prints.
_PORTFOLIO_RE = re.compile(r"^=== portfolio (ARA|MOD) ===$", re.M)


def _units(stderr: str) -> set[tuple[str, str]]:
    return {(m.group(1), m.group(2)) for m in _UNIT_RE.finditer(stderr)}


def _fixture_names(stderr: str) -> list[str]:
    # Every fixture that appeared, ARA side (MOD mirrors it) — order-preserving, deduped.
    seen: list[str] = []
    for analysis, name in _UNIT_RE.findall(stderr):
        if name not in seen:
            seen.append(name)
    return seen


# --- the partition invariant ----------------------------------------------------------

@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7])
def test_shards_partition_the_fixture_list(n: int):
    """Every fixture lands in EXACTLY ONE shard — the union is complete and the shards are
    pairwise disjoint. A dropped fixture rots the baseline silently; a duplicated one doubles
    the bill and races two execs onto one report filename."""
    all_names = set(_all_fixture_names())
    seen: dict[str, int] = {}
    for i in range(1, n + 1):
        res = _run("--shard", f"{i}/{n}")
        assert res.returncode == 0, f"shard {i}/{n} exited {res.returncode}: {res.stderr[-500:]}"
        for name in _fixture_names(res.stderr):
            seen[name] = seen.get(name, 0) + 1
    assert set(seen) == all_names, f"partition dropped/added fixtures: {set(seen) ^ all_names}"
    dupes = {k: c for k, c in seen.items() if c != 1}
    assert not dupes, f"fixtures ran in more than one shard: {dupes}"


def test_shard_slice_is_a_subset_of_the_unsharded_run():
    """A shard must only ever run fixtures the full sweep would — never invent one."""
    full = set(_fixture_names(_run().stderr))
    for i in range(1, 4):
        slice_names = set(_fixture_names(_run("--shard", f"{i}/3").stderr))
        assert slice_names <= full, f"shard {i}/3 ran non-sweep fixtures: {slice_names - full}"


def test_shards_are_roughly_balanced():
    """Round-robin, not contiguous blocks: 14 fixtures / 4 shards → sizes differ by <=1, so no
    single job carries a disproportionate share of the 1h budget."""
    sizes = [len(_fixture_names(_run("--shard", f"{i}/4").stderr)) for i in range(1, 5)]
    assert max(sizes) - min(sizes) <= 1, f"unbalanced shards: {sizes}"
    assert sum(sizes) == len(_all_fixture_names())


# --- shards never roll up; --portfolio-only only rolls up -----------------------------

def test_a_shard_never_runs_the_portfolio_rollup():
    """A shard sees only its slice, so a rollup there would aggregate a partial portfolio.
    The gather step (--portfolio-only) owns the rollup."""
    res = _run("--shard", "1/4")
    assert not _PORTFOLIO_RE.search(res.stderr), "a shard ran the portfolio rollup"


def test_portfolio_only_runs_the_rollup_and_no_per_repo_units():
    """--portfolio-only is the gather step: it consumes the merged per-repo reports already in
    AFTER_DIR and runs ONLY the two portfolio execs, never a per-repo analysis."""
    with tempfile.TemporaryDirectory() as tmp:
        after = Path(tmp) / "after"
        after.mkdir()
        # Two per-repo reports already present — the merged shard output the gather consumes.
        (after / "alpha-ara-report.json").write_text("{}")
        (after / "beta-mod-report.json").write_text("{}")
        env = _env(tmp, AFTER_DIR=str(after))
        res = subprocess.run(
            ["bash", str(SCRIPT), "--scope", "all", "--portfolio-only", "--dry-run"],
            env=env, capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stderr[-500:]
    assert not _units(res.stderr), f"--portfolio-only ran per-repo units: {_units(res.stderr)}"
    assert _PORTFOLIO_RE.search(res.stderr), "--portfolio-only did not run the rollup"


# --- an empty shard is legitimate, not a bug ------------------------------------------

def test_an_empty_shard_exits_clean_not_fatal():
    """N greater than the fixture count leaves the tail shards empty. That is a valid no-op,
    NOT the 'analyzed nothing' selection bug the FATAL guard exists to catch — so it must exit
    0 rather than 5."""
    res = _run("--shard", "20/20")
    assert res.returncode == 0, f"empty shard should be a clean no-op, got {res.returncode}"
    assert not _units(res.stderr), "empty shard staged units it should not have"
    assert "FATAL" not in res.stderr


# --- bad --shard values fail loudly ---------------------------------------------------

@pytest.mark.parametrize("bad", ["5/4", "0/4", "2/0", "abc", "3", "/4", "4/", "-1/4"])
def test_malformed_shard_is_rejected(bad: str):
    """A bad shard spec must be a hard error up front — silently selecting all fixtures would
    defeat the split and race the very credential cap it exists to avoid."""
    res = _run("--shard", bad)
    assert res.returncode == 2, f"--shard {bad!r} should exit 2, got {res.returncode}"
    assert "error:" in res.stderr


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
