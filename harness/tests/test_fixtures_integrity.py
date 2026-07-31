#!/usr/bin/env python3
"""
Tests that every fixture is COMPLETE IN GIT — not merely complete on disk.

A fixture is the input to an analysis run, so a file that exists locally but was never
committed produces a failure mode with no error message anywhere: CI clones the repo, the
fixture is quietly missing its most interesting code, the analysis runs clean, and the
scorer reports a plausible number. Nothing crashes. The score just silently measures a
different, tamer repository than the one the fixture author wrote.

This is not hypothetical. `.gitignore` carried a bare `services/` entry (intended for
root-level cloned repos from portfolio runs) which, per gitignore semantics, matches a
directory named `services` at ANY depth. It swallowed
`harness/fixtures/modern/modern-orders-service/src/services/order-service.ts` — the single
file holding the hardDelete / non-idempotent-refund / cancel-and-recall-shipment paths that
the modern-orders-service fixture exists to exercise, and which `src/routes.ts` imports. The
committed fixture had a dangling import and none of its unsafe code.

So these tests assert against `git ls-files`, never the filesystem. Checking the filesystem
would have passed happily the entire time the file was missing from the repo.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_fixtures_integrity.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
USECASES = REPO / "harness" / "usecases.yaml"

# Source extensions worth guarding. A fixture is judged on its code and contracts, so a
# dropped .ts/.py/.yaml changes the analysis; a dropped .md usually does not.
SOURCE_SUFFIXES = {".ts", ".js", ".py", ".java", ".rb", ".php", ".cs", ".vb", ".cpp", ".c",
                   ".cbl", ".jcl", ".cfm", ".frm", ".bas", ".yaml", ".yml", ".json",
                   ".graphql", ".tf", ".sql"}


def _tracked() -> set[str]:
    """Repo-relative paths of every file GIT knows about.

    Fails LOUDLY and in one line when git is unavailable or the checkout is not a repo.
    Both happen in CI and neither is a fixture problem, so neither should present as a
    200-line subprocess traceback that buries which of the two it was:

      - no git binary — the runner clones via a separate helper image, so a job that
        overrides the default `before_script` (harness:contract-tests) drops the
        `apt-get install git` and the tests die on FileNotFoundError. With
        `allow_failure: true` on the job, that reads as an advisory red rather than
        "this axis never ran".
      - not a work tree — a shallow/detached export with no .git.

    These MUST NOT be silently skipped. Returning an empty set here would make every
    caller trivially pass and re-open exactly the invisible gap this file exists to close.
    """
    try:
        proc = subprocess.run(["git", "-C", str(REPO), "ls-files"],
                              capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise AssertionError(
            "git is not installed in this environment, so fixture integrity CANNOT be "
            "checked (these tests deliberately assert against `git ls-files`, not the "
            "filesystem — the regression they pin is invisible on disk). Install git in "
            "the job: any .gitlab-ci.yml job that overrides the default before_script "
            "must still `apt-get install -y git`.") from None
    except subprocess.CalledProcessError as exc:
        raise AssertionError(
            f"`git ls-files` failed in {REPO} (exit {exc.returncode}): "
            f"{(exc.stderr or '').strip()}") from None
    tracked = set(proc.stdout.splitlines())
    assert tracked, f"`git ls-files` returned nothing in {REPO} — not a git work tree?"
    return tracked


def _fixture_dirs() -> list[Path]:
    data = yaml.safe_load(USECASES.read_text(encoding="utf-8"))
    return [REPO / f["path"] for f in data["fixtures"]]


def test_every_fixture_path_in_usecases_exists_in_git():
    """A fixture declared in usecases.yaml but absent from git is analyzed as an empty repo."""
    tracked = _tracked()
    missing = []
    for f in yaml.safe_load(USECASES.read_text(encoding="utf-8"))["fixtures"]:
        prefix = f["path"].rstrip("/") + "/"
        if not any(t.startswith(prefix) for t in tracked):
            missing.append(f["id"])
    assert not missing, (
        "fixtures declared in usecases.yaml with NO tracked files — analysis would run "
        f"against nothing: {missing}")


def test_no_fixture_source_file_is_untracked():
    """The .gitignore-swallowed-a-fixture regression, pinned.

    Walks what is on disk and demands git know about each source file. An ignore rule that
    silently excludes fixture code fails here instead of showing up as a mildly different
    accuracy score three runs later.
    """
    tracked = _tracked()
    untracked: list[str] = []
    for d in _fixture_dirs():
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if not p.is_file() or p.suffix not in SOURCE_SUFFIXES:
                continue
            rel = p.relative_to(REPO).as_posix()
            # Generated analysis output can legitimately sit in a fixture tree after a local
            # run; it is not fixture source and is not meant to be committed.
            if re.search(r"-(ara|mod|portfolio)-report\.(json|md)$", rel):
                continue
            if rel not in tracked:
                untracked.append(rel)
    assert not untracked, (
        "fixture SOURCE files exist on disk but are not tracked by git. CI clones the repo, "
        "so the analysis will run without them and still score plausibly. Check .gitignore "
        f"for an unanchored pattern: {untracked}")


def test_gitignore_clone_rules_are_root_anchored():
    """The specific defect: a bare `services/` matches at every depth.

    These entries exist for repos cloned into the workspace root by portfolio runs. Written
    unanchored they also match any nested directory of the same name — which is exactly how
    a fixture's `src/services/` disappeared. Anchoring is what makes them mean "at the root".
    """
    lines = [ln.strip() for ln in (REPO / ".gitignore").read_text(
        encoding="utf-8").splitlines()]
    for name in ("services", "unishop-monolith-to-microservices", "aws-microservices",
                 "aws-serverless-books-api-sample"):
        assert f"{name}/" not in lines, (
            f"`{name}/` in .gitignore is unanchored and matches a directory named "
            f"'{name}' at ANY depth, including inside harness/fixtures. Anchor it as "
            f"`/{name}/` so it only matches the repo root.")


def test_no_generated_report_is_committed_inside_a_fixture():
    """Analysis output inside a fixture is input contamination, not source.

    A committed `*-mod-report.json` under a fixture gets read back as part of the repo the
    next run analyzes, and it also breaks the glob-based progress counting the sample runs
    rely on.
    """
    stray = [t for t in _tracked()
             if t.startswith("harness/fixtures/")
             and re.search(r"-(ara|mod|portfolio)-report\.(json|md)$", t)]
    assert not stray, f"generated reports committed inside fixture trees: {stray}"


# --- the CI job that runs these tests must give them git ------------------------------

def test_the_ci_job_running_this_suite_installs_git():
    """A job that overrides `before_script` inherits NONE of the default's apt installs.

    `harness:contract-tests` overrides it to skip the atx/Node install (that is most of why
    it is fast) and for a while dropped `git` along with it. The three git-backed tests above
    then failed on `FileNotFoundError: 'git'` — and because every harness job is
    `allow_failure: true`, that surfaced as an advisory red rather than "the fixture-integrity
    axis has never run in CI". The job container genuinely has no git: the runner clones via a
    separate helper image.

    So pin the invariant where it is cheap to check: any job whose script runs this pytest
    suite must install git in its own before_script.
    """
    ci = (REPO / ".gitlab-ci.yml").read_text(encoding="utf-8")
    blocks = re.findall(r"^([a-z][\w:.-]*):\n((?:[ \t].*\n|\n)*)", ci, re.M)
    offenders = []
    for name, body in blocks:
        if name in {"default", "stages", "variables", "include", "workflow"}:
            continue
        # Strip YAML comments BEFORE matching. Prose is not a dependency: an earlier draft
        # of this test matched the word "install ... git" anywhere in the block, and the
        # explanatory comment directly above the apt line satisfied it — so deleting the
        # real install kept the test green. A guard that a comment can satisfy is not a
        # guard.
        code = "\n".join(re.sub(r"#.*$", "", ln) for ln in body.splitlines())
        runs_suite = "pytest harness/tests" in code
        overrides = "before_script:" in code
        if runs_suite and overrides and not re.search(r"install[^\n]*\bgit\b", code):
            offenders.append(name)
    assert not offenders, (
        "these .gitlab-ci.yml jobs run the harness pytest suite AND override "
        "before_script, but never install git — the git-backed fixture-integrity tests "
        f"will die on FileNotFoundError inside them: {offenders}. Add "
        "`apt-get install -y --no-install-recommends git` to the job's before_script.")


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                fails += 1
                print(f"FAIL {name}\n     {exc}")
    sys.exit(1 if fails else 0)
