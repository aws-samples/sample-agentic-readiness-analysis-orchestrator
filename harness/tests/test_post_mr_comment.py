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


def test_safety_hold_renders_a_prominent_block():
    """A safety hold is rubric arithmetic, not the judge's opinion — it must lead."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps({
            "score": 40, "verdict": "needs-work", "intent_match": "aligned",
            "quality_regression": True, "safety_hold": True,
            "rationale": "AUTH-Q5 movement is likely noise.",
            "concerns": [{"dimension": "D2",
                          "detail": "SAFETY ALERT [tier_relaxed] tier moved"}],
        }))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    assert "SAFETY HOLD" in r.stderr
    # It replaces the generic regression note rather than stacking two warnings, so a
    # reader is not left guessing which of the two is the actual blocker.
    assert "Possible quality regression" not in r.stderr
    assert r.stderr.index("SAFETY HOLD") < r.stderr.index("likely noise")


def test_comment_shows_the_measured_accuracy_against_its_baseline():
    """A measured number must be rendered WITH the baseline it is compared against.

    A bare "0.842" invites the reader to grade it out of 100 — the exact confusion the
    single 0-1 scale exists to remove. Showing `score vs baseline (delta)` makes the
    comparison, not the magnitude, the thing being read. Intent match must stay visibly
    demoted, or the old "this number grades the contributor" reading survives in the reader
    even though the code changed.
    """
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps({
            "score": 0.842, "baseline_score": 0.815, "scored": True,
            "verdict": "LGTM", "analysis_effect": "improves",
            "intent_match": "partial", "quality_regression": False,
            "rationale": "DATA-Q1 promoted to BLOCKER surfaces real risk.",
        }))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    assert "improves the analysis" in r.stderr
    # The measurement, its anchor, and the signed delta must all be present.
    assert "0.842" in r.stderr and "0.815" in r.stderr, "score or baseline missing"
    assert "+0.027" in r.stderr, "the signed delta against the baseline is missing"
    assert "/100" not in r.stderr, "the retired 0-100 axis is still being rendered"
    assert "grounded in the fixture" in r.stderr, "the accuracy legend is missing"
    assert "does not drive the measurement" in r.stderr, \
        "intent match is not shown as demoted"
    # Effect leads, intent match trails.
    assert r.stderr.index("improves the analysis") < r.stderr.index("Intent match")


def test_unbaselined_run_is_never_rendered_as_an_inert_edit():
    """A run that compared 0 reports must NOT read as "the edit did nothing".

    The audit case: an MR selects fixtures with no golden. Every regenerated report lands
    in coverage.unbaselined, the differ reports compared=0 / no_op=true, and without this
    block the comment shows a scoped-run line and an empty delta -- which a reviewer reads
    as "the change is inert" after ~110 agent-minutes per unit were actually spent. The
    comment has to say NOTHING WAS MEASURED.
    """
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps({
            "score": None, "baseline_score": None, "scored": False,
            "verdict": "needs-work", "analysis_effect": "neutral",
            "intent_match": "unknown", "quality_regression": False,
            "rationale": "Nothing was measured.",
            "_impact_summary": {
                "dimensions_moved": [], "changed_tds": [], "highlights": [],
                "coverage": {"compared": 0, "baseline_total": 28, "partial": True,
                             "not_analyzed_count": 28,
                             "unbaselined": ["mod/repo/modern-orders-service",
                                             "mod/repo/modern-payments-api"]},
            },
        }))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    assert "NOT MEASURED" in r.stderr, "an unbaselined run must be labelled not-measured"
    assert "modern-orders-service" in r.stderr, \
        "the comment must NAME the unbaselined fixtures so a maintainer can fix the gap"
    assert "vacuous" in r.stderr, \
        "the comment must say the empty delta is not evidence the edit is inert"


def test_partially_unbaselined_run_still_discloses_the_dropped_reports():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps({
            "score": 0.84, "baseline_score": 0.83, "scored": True,
            "verdict": "LGTM", "analysis_effect": "neutral",
            "intent_match": "aligned", "quality_regression": False,
            "rationale": "One fixture measured.",
            "_impact_summary": {
                "dimensions_moved": ["D1"], "changed_tds": ["mod"], "highlights": [],
                "coverage": {"compared": 1, "baseline_total": 28, "partial": True,
                             "not_analyzed_count": 27,
                             "unbaselined": ["mod/repo/brand-new-fixture"]},
            },
        }))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    assert "brand-new-fixture" in r.stderr
    assert "unbaselined" in r.stderr.lower()
    # It measured something, so it must NOT claim nothing was measured.
    assert "NOT MEASURED" not in r.stderr


def test_comment_says_validation_was_not_possible_when_unscored():
    """A missing score is an ERROR TO FIX, never a silent pass.

    If the comment simply omitted the number, a scoring failure would render as an ordinary
    verdict and a reviewer would merge on the strength of a measurement that was never
    taken. The comment has to say the change could not be validated.
    """
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps({
            "score": None, "baseline_score": None, "scored": False,
            "verdict": "needs-work", "analysis_effect": "neutral",
            "intent_match": "partial", "quality_regression": False,
            "rationale": "Scoring step did not produce compare.json.",
        }))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    assert "not measured" in r.stderr
    assert "could not be validated" in r.stderr, \
        "a missing measurement must be stated as a failure to validate"
    assert "score-reports.py" in r.stderr, "the comment must name the step to fix"
    assert "None" not in r.stderr, "rendered a raw None instead of the unscored branch"


def test_degrades_is_rendered_unmissably():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps({
            "score": 20, "verdict": "needs-work", "analysis_effect": "degrades",
            "intent_match": "aligned", "quality_regression": True,
            "rationale": "AUTH-Q5 lost BLOCKER status.",
        }))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    # An aligned intent must not soften a degradation — that pairing IS the MR !14 shape.
    assert "DEGRADES the analysis" in r.stderr


def test_render_script_has_no_apostrophes():
    """The heredoc lives inside $(...) and bash 3.2 re-parses the substitution body.

    A single apostrophe anywhere in it — prose OR comment — opens a quote bash never sees
    closed, and the script dies with "unexpected EOF while looking for matching )" before
    executing a line. Caught exactly that way: adding "the judge's opinion" to a comment
    broke all 10 tests in this file at once. Cheaper to pin than to rediscover.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    start = text.index("<<'PY'")
    end = text.index("\nPY\n", start)
    body = text[start + len("<<'PY'"):end]
    # Python string literals legitimately use ' as a delimiter, so a flat ban is too
    # strict; what breaks bash is an UNPAIRED one. Require an even count per line.
    unbalanced = [ln for ln in body.splitlines() if ln.count("'") % 2 == 1]
    assert not unbalanced, (
        "unbalanced apostrophe inside the $(...) heredoc — bash 3.2 will refuse to parse "
        f"the whole script: {unbalanced}")


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



# --- the wiring-test job must actually exercise the path it claims to prove ------------

def _canned_verdict_from_ci() -> dict:
    """Extract the canned verdict.json heredoc out of .gitlab-ci.yml."""
    import re
    ci = (REPO / ".gitlab-ci.yml").read_text()
    m = re.search(r"cat > verdict\.json <<'JSON'\n(.*?)\n\s*JSON\n", ci, re.S)
    assert m, "could not find the canned verdict heredoc in .gitlab-ci.yml"
    body = "\n".join(l[6:] if l.startswith(" " * 6) else l.lstrip()
                      for l in m.group(1).splitlines())
    return json.loads(body)


def test_canned_comment_check_verdict_renders_a_real_accuracy_line():
    """harness:comment-check exists to prove the comment path works before a full run.

    It used to carry `"score": 85` (the retired 0-100 scale) with no `scored` /
    `baseline_score`, so the renderer took its "not measured" branch: the job passed while
    the scored branch it exists to validate was never executed. Pin the payload shape.
    """
    v = _canned_verdict_from_ci()
    assert v.get("scored") is True, "canned verdict must exercise the SCORED branch"
    assert isinstance(v.get("score"), float) and 0.0 <= v["score"] <= 1.0, \
        f"score must be on the live 0.0-1.0 scale, got {v.get('score')!r}"
    assert isinstance(v.get("baseline_score"), float), \
        "without baseline_score the renderer cannot show the delta"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "v.json"
        p.write_text(json.dumps(v))
        r = subprocess.run(
            ["bash", str(SCRIPT), str(p)],
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": tmp,
                 "CI_PROJECT_ID": "1", "CI_MERGE_REQUEST_IID": "14",
                 "CI_API_V4_URL": FAKE_API, "HARNESS_MR_TOKEN": "pat"},
            capture_output=True, text=True, timeout=120)
    assert "not measured" not in r.stderr, (
        "the canned payload still renders the unscored branch, so comment-check would "
        "green-light a regression in the accuracy line")
    assert "vs baseline" in r.stderr, "the accuracy comparison line did not render"

if __name__ == "__main__":
    raise SystemExit(_run_all())
