#!/usr/bin/env python3
"""
Tests that the two `program-library.md` copies stay byte-identical.

The AWS Program & GTM Library is shipped alongside BOTH portfolio TDs — a TD folder is a
self-contained publishable package (`scripts/publish-td.sh` submits one directory), so the
file cannot be shared by reference and exists twice on purpose:

    definitions/managed/portfolio-agentic-readiness-analysis/references/program-library.md
    definitions/managed/portfolio-modernization-readiness-analysis/references/program-library.md

Both portfolio TDs load it at runtime to produce engagement-program recommendations, and
`definitions/managed/README.md` states the rule plainly: "If you update the program library,
you must update it in both places. The two copies must stay identical."

Nothing enforced that until this test. Editing one copy and not the other is a silent
divergence: each TD publishes fine, each runs fine, and the two analyses simply start
recommending different programs from the same portfolio — a discrepancy that surfaces as a
confusing customer-facing report rather than as any kind of error. A grep across `harness/`,
`tools/`, `scripts/`, and `.gitlab-ci.yml` for `program-library` finds only comments.

The failure mode is the same class as the fixture-integrity tests next door: no crash, no
message, just a quietly wrong answer. Hence a test rather than a convention.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_program_library_copies.py
"""
from __future__ import annotations

import difflib
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANAGED = REPO / "definitions" / "managed"

COPIES = (
    MANAGED / "portfolio-agentic-readiness-analysis" / "references" / "program-library.md",
    MANAGED / "portfolio-modernization-readiness-analysis" / "references" / "program-library.md",
)


def test_both_copies_exist():
    """A missing copy breaks that TD's Step 7 with no other signal."""
    missing = [str(p.relative_to(REPO)) for p in COPIES if not p.is_file()]
    assert not missing, (
        f"program-library.md is missing from: {missing}. Both portfolio TDs load it at "
        f"runtime to recommend engagement programs; a TD folder is a self-contained "
        f"publishable package, so the file must exist in both."
    )


def test_copies_are_byte_identical():
    """Edit one, edit both — enforced here rather than trusted to reviewer memory."""
    blobs = [p.read_bytes() for p in COPIES]
    if blobs[0] == blobs[1]:
        return

    digests = [hashlib.md5(b).hexdigest() for b in blobs]
    diff = list(
        difflib.unified_diff(
            blobs[0].decode("utf-8", "replace").splitlines(),
            blobs[1].decode("utf-8", "replace").splitlines(),
            fromfile=str(COPIES[0].relative_to(REPO)),
            tofile=str(COPIES[1].relative_to(REPO)),
            lineterm="",
            n=1,
        )
    )
    # Cap the report: a whole-file divergence would otherwise bury the first real hunk.
    shown = "\n".join(diff[:40])
    more = "" if len(diff) <= 40 else f"\n... ({len(diff) - 40} more diff lines)"
    raise AssertionError(
        "The two program-library.md copies have diverged.\n"
        f"  {COPIES[0].relative_to(REPO)}  md5={digests[0]}\n"
        f"  {COPIES[1].relative_to(REPO)}  md5={digests[1]}\n"
        "Both portfolio TDs must ship the SAME library, or the two analyses recommend "
        "different programs from the same portfolio. Copy one over the other:\n"
        f"  cp {COPIES[0].relative_to(REPO)} \\\n     {COPIES[1].relative_to(REPO)}\n\n"
        f"{shown}{more}"
    )


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
