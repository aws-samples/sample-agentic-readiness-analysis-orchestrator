#!/usr/bin/env python3
"""
Automated checks over `advisor/` — the modernization-advisor agent skill.

Nothing read this directory before. The 377 tests next door cover the transformation
definitions, the differ, the scorers and the fixtures; the skill that an SA actually runs
commands out of was verified by hand, once per review round, by a human reading it.

That is not a theoretical gap. The same two facts have been corrected, re-broken and
corrected again across review rounds:

  * `atx update` does not exist. Top-level commands are `custom`, `json`, `mcp`, `ct`;
    you upgrade by re-running the installer.
  * Omitting `--agent-scope` does NOT mean read-only. The CLI's own help says the
    assessment infers it from the repository.

and the CLI baseline version is hard-coded independently in five files, which have drifted
out of step with each other more than once.

So this file pins the mechanical properties — the ones a reviewer should never have to
spend attention on:

  1. every relative link and `#anchor` inside `advisor/` resolves;
  2. every repo-root-relative path named in a fenced code block exists on disk;
  3. "atx update" appears only inside a phrase that denies it;
  4. the `--agent-scope` infer sentence is present, and no "defaults to read-only"
     variant is;
  5. the changelog-archaeology words are absent (this skill states current truth; it is
     not a release-notes file);
  6. exactly ONE `atx` X.Y.Z baseline version string appears across the five files that
     carry one.

Judgement — whether the advice is good, whether the routing is right — stays with the
reviewer. This covers only what a machine can hold.

Run:  python3 -m pytest harness/tests/ -q
  or: python3 harness/tests/test_advisor_skill.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO / "advisor"

# The five files that each carry the `atx` baseline version independently. Kept explicit
# rather than globbed: the assertion is "these five agree", and a new file that quotes a
# version should be added here deliberately.
VERSIONED = (
    SKILL_DIR / "SKILL.md",
    SKILL_DIR / "references" / "transform-paths.md",
    SKILL_DIR / "references" / "td-catalog.md",
    SKILL_DIR / "references" / "ct-operations.md",
    SKILL_DIR / "references" / "getting-started.md",
)

# Top-level repo directories a code fence may legitimately reference by a repo-rooted path.
# A token whose first segment is one of these is checked against the filesystem.
# ‼ `advisor` MUST be here: it is the directory this file polices, and its absence meant a
# wrong `advisor/...` path inside an advisor/ code fence went unchecked — the exact shape most
# likely to be wrong right after a rename. Entries are also DROPPED when a directory stops
# being part of the published tree: listing one that is not published is inert here, and it
# enumerates absent paths for no benefit. Keep this to directories that actually ship.
REPO_ROOTED = (
    "advisor",
    "definitions",
    "harness",
    "tools",
    "examples",
    "docs",
)

# Changelog archaeology. The skill is written to state what is true now; "X no longer does
# Y" tells a reader about a CLI they do not have, and ages into a second lie when the
# behavior changes again.
#
# ‼ "as of X.Y" is in this pattern because the first version of this guard missed exactly
# that phrasing: "The terminal UI is the default as of 3.15" survived review while the
# regex matched nothing in it. A legitimate minimum-version note reads
# "(requires atx >= X.Y)" and is allowed; "as of X.Y" dates a fact that is simply true
# now, which is the thing this test exists to stop.
ARCHAEOLOGY = re.compile(
    r"no longer|used to\b|previously|was removed|earlier version"
    r"|as of \d+\.\d+"
    r"|\bin (?:version )?\d+\.\d+(?:\.\d+)? this (?:changed|became)",
    re.I)

FENCE = re.compile(r"^(```|~~~)")

# `[text](target)` — target captured lazily so a trailing `)` inside prose does not swallow it.
MD_LINK = re.compile(r"\[(?:[^\]]*)\]\(([^)\s]+)\)")

ATX_VERSION = re.compile(r"\batx`?\s+(\d+\.\d+\.\d+)")


def md_files() -> list[Path]:
    files = sorted(SKILL_DIR.rglob("*.md"))
    assert files, f"no markdown found under {SKILL_DIR.relative_to(REPO)}"
    return files


def rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def split_fences(text: str) -> tuple[list[str], list[tuple[int, str]]]:
    """Return (code-fence lines, [(1-indexed line no, prose line)])."""
    code: list[str] = []
    prose: list[tuple[int, str]] = []
    inside = False
    for n, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line.strip()):
            inside = not inside
            continue
        (code if inside else prose).append(line if inside else (n, line))  # type: ignore[arg-type]
    return code, prose


def heading_anchors(text: str) -> set[str]:
    """GitHub-flavoured heading slugs for one document."""
    anchors: set[str] = set()
    inside_fence = False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            inside_fence = not inside_fence
            continue
        if inside_fence or not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        # GitHub: lowercase, strip anything but word chars / spaces / hyphens, spaces -> '-'.
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
        slug = re.sub(r"\s+", "-", slug.strip())
        anchors.add(slug)
    return anchors


# --------------------------------------------------------------------------------------
# 1. links and anchors
# --------------------------------------------------------------------------------------


def test_relative_links_and_anchors_resolve() -> None:
    anchor_cache: dict[Path, set[str]] = {}
    broken: list[str] = []
    checked = 0

    for path in md_files():
        text = path.read_text(encoding="utf-8")
        _, prose = split_fences(text)
        for lineno, line in prose:
            for target in MD_LINK.findall(line):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                checked += 1
                file_part, _, anchor = target.partition("#")
                dest = path.parent / file_part if file_part else path
                dest = dest.resolve()
                if not dest.exists():
                    broken.append(f"{rel(path)}:{lineno}  ->  {target}  (no such file)")
                    continue
                if not anchor:
                    continue
                if dest not in anchor_cache:
                    anchor_cache[dest] = heading_anchors(dest.read_text(encoding="utf-8"))
                if anchor.lower() not in anchor_cache[dest]:
                    broken.append(f"{rel(path)}:{lineno}  ->  {target}  (no such heading)")

    assert checked, "found no relative links at all — the extractor is broken, not the docs"
    assert not broken, "unresolvable links/anchors in advisor/:\n  " + "\n  ".join(broken)


# --------------------------------------------------------------------------------------
# 2. repo-rooted paths inside code fences
# --------------------------------------------------------------------------------------


def test_repo_rooted_paths_in_code_fences_exist() -> None:
    token = re.compile(r"(?:" + "|".join(REPO_ROOTED) + r")/[A-Za-z0-9._/@-]+")
    missing: list[str] = []
    checked = 0

    for path in md_files():
        code, _ = split_fences(path.read_text(encoding="utf-8"))
        for line in code:
            # Strip shell comments: they hold prose, not paths to check.
            body = line.split("#", 1)[0]
            for raw in token.findall(body):
                # Placeholders (`<name>`, globs, `$var`, brace expansion) are not paths.
                if any(c in raw for c in "<>*?$}{"):
                    continue
                candidate = raw.rstrip(".,;:)\"'")
                if candidate.endswith("/"):
                    candidate = candidate[:-1]
                checked += 1
                if not (REPO / candidate).exists():
                    missing.append(f"{rel(path)}  ->  {candidate}")

    assert checked, "found no repo-rooted paths in any code fence — the extractor is broken"
    assert not missing, (
        "code fences in advisor/ name repo paths that do not exist:\n  "
        + "\n  ".join(sorted(set(missing)))
    )


# --------------------------------------------------------------------------------------
# 3. `atx update` does not exist
# --------------------------------------------------------------------------------------


def test_atx_update_only_appears_denied() -> None:
    """Every mention of `atx update` must sit inside a phrase that says it does not exist.

    Regressed twice. A bare "run atx update" sends an SA to a subcommand the CLI has
    never had; the top-level commands are custom, json, mcp, ct.
    """
    denial = re.compile(r"(?:there is |is )?no[tn]?\s+`?atx update`?|`?atx update`?\s+does not exist", re.I)
    offenders: list[str] = []

    for path in md_files():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "atx update" not in line:
                continue
            if not denial.search(line):
                offenders.append(f"{rel(path)}:{n}  {line.strip()[:140]}")

    assert not offenders, (
        "`atx update` is named without denying it — there is no such subcommand "
        "(upgrade by re-running the installer):\n  " + "\n  ".join(offenders)
    )


# --------------------------------------------------------------------------------------
# 4. `--agent-scope` is infer-else-honor, not read-only-by-default
# --------------------------------------------------------------------------------------


def test_agent_scope_absence_means_inferred() -> None:
    """The fact, and the absence of its inverse.

    Also regressed twice. "Omitting --agent-scope means read-only" is the dangerous
    direction: it implies the five conditional BLOCKERs cannot fire, so a write-capable
    repository reads as safe.
    """
    corpus = {p: p.read_text(encoding="utf-8") for p in md_files()}

    present = [rel(p) for p, t in corpus.items() if "infers it from the repository" in t]
    assert present, (
        "the `--agent-scope` infer sentence is gone from advisor/. The CLI's help "
        'reads "If omitted, the assessment infers it from the repository." — state it.'
    )

    # The inverse claim, in the forms it has actually been written in. The middle group
    # refuses to step over `not` / `never`, so the correct sentence — "Omitting
    # `--agent-scope` does NOT mean read-only" — cannot match its own negation.
    wrong = re.compile(
        r"(?:--agent-scope|agent_scope|omitting[^.\n]{0,20}scope)"
        r"(?:(?!\bnot\b|\bnever\b)[^.\n]){0,60}"
        r"(?:default(?:s|ed)?\s+to|means?|implies|falls?\s+back\s+to)\s+`?read-only",
        re.I,
    )
    offenders: list[str] = []
    for path, text in corpus.items():
        for n, line in enumerate(text.splitlines(), start=1):
            if wrong.search(line):
                offenders.append(f"{rel(path)}:{n}  {line.strip()[:140]}")

    assert not offenders, (
        "an `--agent-scope` defaults-to-read-only claim is back. Absence means INFERRED "
        "from the repository, and absence never lowers a score:\n  " + "\n  ".join(offenders)
    )


# --------------------------------------------------------------------------------------
# 5. no changelog archaeology
# --------------------------------------------------------------------------------------


def test_no_changelog_archaeology() -> None:
    offenders: list[str] = []
    for path in md_files():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            m = ARCHAEOLOGY.search(line)
            if m:
                offenders.append(f"{rel(path)}:{n}  ...{m.group(0)}...  {line.strip()[:120]}")

    assert not offenders, (
        "advisor/ states current truth — it is not a changelog. Drop the history and "
        "say what is true on the current CLI (a bare minimum-version tag is fine where a "
        "feature genuinely needs one):\n  " + "\n  ".join(offenders)
    )


# --------------------------------------------------------------------------------------
# 6. one baseline version, five files
# --------------------------------------------------------------------------------------


def test_exactly_one_atx_baseline_version() -> None:
    found: dict[str, list[str]] = {}
    for path in VERSIONED:
        assert path.exists(), f"{rel(path)} is missing — update VERSIONED in this test"
        text = path.read_text(encoding="utf-8")
        versions = set(ATX_VERSION.findall(text))
        assert versions, (
            f"{rel(path)} carries no `atx` X.Y.Z baseline. Each of the five files states "
            "the version it was written against; a file that silently loses it cannot be "
            "reconciled with the others."
        )
        for v in versions:
            found.setdefault(v, []).append(rel(path))

    assert len(found) == 1, (
        "the five version-carrying files disagree on the `atx` baseline — reconcile them "
        "in one commit:\n  "
        + "\n  ".join(f"{v}: {', '.join(files)}" for v, files in sorted(found.items()))
    )


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
