#!/usr/bin/env python3
"""
Tests for post-mr-comment.sh — the advisory MR note.

Two things are pinned here, both learned from MR !14 returning HTTP 401:

1. WHICH AUTH HEADER GOES OUT. The script used to send JOB-TOKEN *and* PRIVATE-TOKEN
   with the same value. That is not a belt-and-braces fallback — GitLab authenticates
   the two by different paths, and a Project Access Token arriving in a JOB-TOKEN header
   is rejected on that header rather than retried against the other. So the moment
   HARNESS_MR_TOKEN was finally configured, the dual header would have kept 401ing and
   the token would have looked like the culprit.

2. THAT IT STAYS ADVISORY. This runs at the very end of a job that has already spent
   ~130 agent-minutes. If it ever exits non-zero on a posting failure it converts "we
   couldn't comment" into "the harness is red", which is the opposite of advisory — and
   it must still print the verdict so the work is not lost.

No network: the script is run with a bogus API host and we assert on the *chosen header*
via `bash -x` tracing plus the script's own stderr.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_post_mr_comment.py
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "harness" / "post-mr-comment.sh"

# Point at a CLOSED PORT on localhost, not an unroutable address. TEST-NET-1 (192.0.2.1)
# blackholes packets, so each test burned the full --connect-timeout and the suite took
# ~83s; a closed local port returns ECONNREFUSED immediately, exercising the same
# "post failed" branch in milliseconds. This suite runs on every MR, so its speed matters.
FAKE_API = "http://127.0.0.1:1/api/v4"


def _verdict_file(tmpdir: str) -> str:
    p = Path(tmpdir) / "verdict.json"
    p.write_text(json.dumps({
        "score": 85,
        "verdict": "LGTM",
        "intent_match": "aligned",
        "quality_regression": False,
        "rationale": "API-Q2 moved RISK-QUALITY -> RISK-SAFETY as intended.",
        "_engine": "bedrock",
        "_impact_summary": {
            "dimensions_moved": ["D1"],
            "changed_tds": ["agentic-readiness-analysis"],
            "highlights": ["[repo] D1 reseveritied: API-Q2 RISK-QUALITY -> RISK-SAFETY"],
            "coverage": {"compared": 2, "baseline_total": 24, "partial": True,
                         "not_analyzed_count": 22},
        },
    }))
    return str(p)


def _run(env_extra: dict, trace: bool = False) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        vf = _verdict_file(tmp)
        env = {
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": tmp,
            "CI_PROJECT_ID": "99999",
            "CI_MERGE_REQUEST_IID": "14",
            "CI_API_V4_URL": FAKE_API,
        }
        env.update(env_extra)
        cmd = ["bash"] + (["-x"] if trace else []) + [str(SCRIPT), vf]
        return subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)


# --- the 401 bug: exactly one auth header, and the right one -------------------------

def test_project_access_token_is_sent_as_private_token():
    r = _run({"HARNESS_MR_TOKEN": "pat-sentinel", "CI_JOB_TOKEN": "job-sentinel"},
             trace=True)
    assert "PRIVATE-TOKEN: pat-sentinel" in r.stderr, \
        "a Project Access Token must go out in PRIVATE-TOKEN"


def test_project_access_token_is_never_sent_as_job_token():
    """The actual MR !14 regression. GitLab rejects a PAT in JOB-TOKEN outright."""
    r = _run({"HARNESS_MR_TOKEN": "pat-sentinel", "CI_JOB_TOKEN": "job-sentinel"},
             trace=True)
    assert "JOB-TOKEN: pat-sentinel" not in r.stderr, \
        "PAT was sent in a JOB-TOKEN header — GitLab rejects this, causing a 401"
    # and the job token must not be smuggled along either
    assert "job-sentinel" not in r.stderr, \
        "CI_JOB_TOKEN leaked into the request while a PAT was configured"


def test_only_one_auth_header_is_sent():
    r = _run({"HARNESS_MR_TOKEN": "pat-sentinel"}, trace=True)
    curl_lines = [ln for ln in r.stderr.splitlines() if "curl" in ln and "--header" in ln]
    assert curl_lines, f"no curl invocation traced; stderr={r.stderr[-600:]}"
    joined = "\n".join(curl_lines)
    assert joined.count("--header") == 1, \
        f"expected exactly one auth header, got {joined.count('--header')}"


def test_job_token_only_warns_that_notes_are_unsupported():
    """CI_JOB_TOKEN cannot create notes at all; the log must say so, or the inevitable
    401 gets misread as a bad PAT / missing permission."""
    r = _run({"CI_JOB_TOKEN": "job-sentinel"})
    low = r.stderr.lower()
    assert "harness_mr_token" in low, "the warning must name the variable that fixes it"
    assert "401" in low or "cannot create" in low


# --- advisory contract ---------------------------------------------------------------

def test_posting_failure_still_exits_zero():
    # The job is allow_failure:true, but a non-zero exit here would still paint the
    # pipeline red and discard a completed analysis.
    r = _run({"HARNESS_MR_TOKEN": "pat-sentinel"})
    assert r.returncode == 0, \
        f"must stay advisory on a failed post, exited {r.returncode}"


def test_transport_failure_reports_a_single_http_code():
    """`|| echo 000` on a captured `-w '%{http_code}'` APPENDS to curl's output.

    On a refused connection that produced "000000" in the log — a code that does not
    exist. The comparison still worked by luck, so this would only ever have surfaced as
    an operator staring at a nonsense status while debugging a real posting failure.
    """
    r = _run({"HARNESS_MR_TOKEN": "pat-sentinel"})
    assert "HTTP 000)" in r.stderr or "HTTP 000;" in r.stderr, \
        f"expected a single synthesized 000 code; stderr tail={r.stderr[-400:]}"
    assert "000000" not in r.stderr, "curl's -w output was appended to, not replaced"


def test_stale_response_body_is_not_reprinted():
    """The body file must be per-run, not a fixed /tmp path.

    curl writes NOTHING to -o when the connection fails, so a fixed path leaves the
    PREVIOUS run's body in place — and the script would print an unrelated older error as
    if it were this attempt's API response. Caught exactly that way in local testing: a
    302 from a much earlier call resurfaced under a fresh failure.
    """
    poison = "POISON-STALE-BODY-SHOULD-NOT-APPEAR"
    Path("/tmp/mr-note-resp.json").write_text(poison)
    try:
        r = _run({"HARNESS_MR_TOKEN": "pat-sentinel"})
        assert poison not in r.stderr, \
            "a stale response body from a previous run was printed as this run's response"
    finally:
        Path("/tmp/mr-note-resp.json").unlink(missing_ok=True)


def test_verdict_is_printed_when_posting_fails():
    # If we can't comment, the verdict must survive in the job log.
    r = _run({"HARNESS_MR_TOKEN": "pat-sentinel"})
    assert "Change-Impact Harness" in r.stderr
    assert "RISK-QUALITY -> RISK-SAFETY" in r.stderr


def test_missing_token_does_not_fail_the_job():
    r = _run({})
    assert r.returncode == 0
    assert "Change-Impact Harness" in r.stderr


def test_outside_mr_context_exits_nonzero_for_caller_fallback():
    # harness:full relies on this: `post-mr-comment.sh || cat verdict.json`.
    with tempfile.TemporaryDirectory() as tmp:
        vf = _verdict_file(tmp)
        r = subprocess.run(
            ["bash", str(SCRIPT), vf],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp},
            capture_output=True, text=True, timeout=60)
    assert r.returncode == 1, "no-MR context must signal the caller to fall back"
    assert "not in an MR pipeline" in r.stderr


# --- rendering -----------------------------------------------------------------------

def test_scoped_run_is_disclosed_in_the_comment():
    """A reviewer must not read a 2-of-24 delta as portfolio-wide proof."""
    r = _run({"HARNESS_MR_TOKEN": "pat-sentinel"})
    assert "Scoped run" in r.stderr
    assert "2 of 24" in r.stderr


def test_regression_flag_renders_a_warning_block():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps({"score": 20, "verdict": "needs-work",
                                 "intent_match": "mismatch",
                                 "quality_regression": True,
                                 "rationale": "tier contradicts blocker count"}))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    assert "quality regression" in r.stderr.lower()


def test_missing_verdict_file_is_an_error():
    r = subprocess.run(
        ["bash", str(SCRIPT), "/nonexistent/verdict.json"],
        env={"PATH": "/usr/bin:/bin:/usr/local/bin"},
        capture_output=True, text=True, timeout=60)
    assert r.returncode == 1
    assert "no verdict file" in r.stderr


# --- fallback runner (no pytest) -----------------------------------------------------

def _run_all():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            passed += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}: {exc}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
