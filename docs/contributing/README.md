# Contributing to the Transformation Definitions

**Start here** to add, remove, re-score, or tweak a question or rubric in one of the
assessments. This one page is the whole contributor guide: TD anatomy, the change playbook,
and the invariants that break *silently*. It is self-contained — the only things it routes
out to are the authoritative rubric text (each TD's `SKILL.md`) and the deep design doc
([`harness/DESIGN.md`](../../harness/DESIGN.md)).

**Contents**

1. [What is a Transformation Definition?](#what-is-a-transformation-definition-td)
2. [TD anatomy — where everything lives](#td-anatomy--where-everything-lives)
3. [The change playbook](#the-change-playbook)
4. [The benchmarking scorer prompts](#the-benchmarking-scorer-prompts-hand-maintained)
5. [Before you open a PR / MR](#before-you-open-a-pr--mr)
6. [Invariants — what breaks silently](#invariants--what-breaks-silently)
7. [Where the deeper docs live](#where-the-deeper-docs-live)

---

## What is a Transformation Definition (TD)?

A TD is the rubric the AWS Transform service runs against a repository. There are four
**managed** TDs (what `main` ships to prod):

| TD | What it scores | Questions |
|---|---|---|
| `agentic-readiness-analysis` (ARA) | Is a system safe for AI agents to call? | 43 |
| `modernization-readiness-analysis` (MOD) | Is a system ready to modernize? | 37 |
| `portfolio-agentic-readiness-analysis` | ARA rolled up across a portfolio + program recs | — |
| `portfolio-modernization-readiness-analysis` | MOD rolled up + program recs | — |

> **Vocabulary:** product docs say **MODA** (the AWS *Modernization Assessment*); the code and
> this harness abbreviate the same thing as **MOD**. Same rubric, two names.

Each TD is a lean **`SKILL.md` orchestration spine** plus **`references/*.md`** files loaded on
demand. The harness reads `SKILL.md` + `references/*.md` concatenated at runtime
(`harness/skill_table.py::parse_questions`), so **a TD edit takes effect on the next run with no
code change** — the only exception is a change to the *number* of questions (see
[the change playbook](#the-change-playbook)).

---

## TD anatomy — where everything lives

Before you edit a rubric, know its shape.

### ARA — `definitions/managed/agentic-readiness-analysis/`

```
SKILL.md                       # spine: name, objective, 8-section summary, flow, "load X here"
references/
├── 01-scoring-model.md        # tiers, severity model, unified severity/category display,
│                              #   RISK-tier assignment, service-archetype, readiness-profile
├── 02-question-bank.md        # all 43 questions (Steps 2–9) — severity, scope, calibration
├── 03-report-template.md      # markdown report: header, profile, counts, BLOCKER/RISK/INFO
└── 04-output-contract.md      # machine-readable 4-artifact contract, ara_metadata, HTML
```

**Where a question's severity lives:** in the **question heading itself**, e.g.
`#### API-Q1: Documented API Interface — BLOCKER`. Two easy-to-miss details the parser depends
on: the separator is an **em-dash `—` (U+2014), not a hyphen**, and the heading is **four
`#`**. ARA has exactly **3 unified severities** (BLOCKER / RISK / INFO, with RISK sub-tiers like
RISK-SAFETY / RISK-QUALITY assigned in `01-scoring-model.md`). To re-score a question, edit the
`— SEVERITY` suffix on its heading. ARA categories: `AUTH / API / STATE / DATA / OBS / ENG /
HITL / DISC`.

**The `⚡` marker is load-bearing.** It flags the 9 scope-dependent questions (5 conditional
BLOCKERs + 4 scope-calibrated RISK-SAFETY). It flips how a downgrade on that question is judged
(a scope-driven downgrade is a judgement call, not a mechanical correction), so **do not add,
remove, or move it casually** — it is not decoration.

### MOD — `definitions/managed/modernization-readiness-analysis/`

```
SKILL.md                       # spine
references/
├── 01-question-bank.md        # all 37 questions
├── 02-pathways.md             # the 7 modernization pathways + triggers
├── 03-report-template.md      # markdown report structure
└── 04-output-contract.md      # machine-readable contract
```

**Where a question's severity lives:** MOD does **not** carry severity in the heading
(`#### INF-Q1: Managed Compute`). Instead each question has a **1–4 rubric table** scored against
criteria; the classification thresholds and 3 unified severities are defined in the scoring
section. To re-score, edit the 1–4 criteria table for that question. MOD categories: `APP / DATA
/ INF / OPS / SEC`.

### Portfolio TDs

`portfolio-agentic-readiness-analysis/` and `portfolio-modernization-readiness-analysis/` each
carry a `SKILL.md` + `references/program-library.md` (the AWS Program & GTM Library, loaded at
runtime). They roll up the per-repo results and attach program recommendations; **they do not
define new questions.**

### Question IDs are permanent keys

A `question_id` (`AUTH-Q7`, `INF-Q1`) is a stable key, **not a position**. Everything downstream
— golden baselines, the static priority table, portfolio aggregation, the findings/evaluations
split — joins on `(analysis_type, question_id)`. **Never renumber to close a gap.** (See
[Invariant #1](#1-never-renumber-a-question-to-close-a-gap).)

### How the harness sees the TD — and the one count tripwire

The parser concatenates the spine and references and extracts every `#### <ID>: <title>` heading.
The parsed count is then the **single source of truth**: `EXPECTED_QUESTIONS` in
[`harness/skill_table.py`](../../harness/skill_table.py) is *derived* from the parse
(`{a: len(parse_questions(a)) for a in ("ara", "mod")}`), so every consumer's count follows the
TD automatically — **no code constant to keep in sync.**

That derivation is safe only because **one** literal still pins the expected number: the test
`test_the_severity_table_is_parsed_from_the_td_not_transcribed` in
[`harness/tests/test_skill_table.py`](../../harness/tests/test_skill_table.py) asserts
`len(parse_questions("ara")) == 43` and `... ("mod") == 37`. An **accidental** parse drift (a
broken `####` heading, a hyphen where an em-dash belongs, a duplicated row) changes the parsed
count but not the literal, so it fails **loudly, there**. An **intentional** add/remove is the
one time you touch that literal — in the same MR as the TD edit. For what the TD emits and how
it is scored end-to-end, see [`harness/DESIGN.md`](../../harness/DESIGN.md) §2–§3.

---

## The change playbook

> **The one decision that routes everything: are you changing the *number* of questions?**
>
> - **No** (re-score, reword, flip a severity, change a scope/archetype/pathway) → edit the TD,
>   open a `rubric-change` MR. **No code change.** The harness picks it up at runtime.
> - **Yes** (add or remove a question) → same as above **plus** update the count literal in
>   [`harness/tests/test_skill_table.py`](../../harness/tests/test_skill_table.py) in the same
>   MR, or CI fails loudly.

### A. Re-score a question (severity / wording / criteria / scope / archetype / pathway)

The common case. **No code change, no count edit.**

1. Edit the owning `references/*.md` (or `SKILL.md`) in the TD:
   - **ARA severity** → the `— SEVERITY` suffix on the `#### <ID>: … — SEVERITY` heading.
   - **MOD scoring** → the 1–4 criteria table for that question.
   - **scope / archetype / pathway** → the relevant resolution block.
2. **Do not change the question's `id`** — it's the join key for every downstream artifact.
3. Open a **`rubric-change`** MR. State *intent* and *expected impact* — which of D1–D5 should
   move (e.g. "tighten AUTH-Q5 so missing rotation is RISK-SAFETY not INFO; expect more
   RISK-SAFETY findings, possible ARA tier drops"). Vague intent → vague verdict.
4. The GitLab pipeline runs the harness and posts an **advisory** verdict. It never blocks.

### B. Add a question

1. Add the question in its `references/*.md` section **and** any count/summary tables that
   reference it, in one change.
2. **Use the next free number in the category, never reuse a retired one** (highest `AUTH-Q7`
   → add `AUTH-Q8`).
3. **Update the count literal:** bump the affected number in
   `test_the_severity_table_is_parsed_from_the_td_not_transcribed`
   ([`harness/tests/test_skill_table.py`](../../harness/tests/test_skill_table.py)) — `43`→`44`
   for ARA, `37`→`38` for MOD — in the **same MR**. Forget it and CI fails loudly with the count
   it parsed and the two causes.
4. Open a `rubric-change` MR with intent + expected impact.
5. A maintainer refreshes the golden baselines on approval (DESIGN.md §7).

### C. Remove a question

Same as add, but:

- **Leave the gap** (`Q1, Q2, Q4, …`). **Do NOT** slide `Q4→Q3` to close it — that silently
  reassigns every finding, baseline row, and priority to a *different* question, and the count
  assertion won't catch it (count moves the same either way). See
  [Invariant #1](#1-never-renumber-a-question-to-close-a-gap).
- If the gap bothers you, retire the *question* (mark deprecated / Not Evaluated) but keep the
  ID reserved.
- **Decrement the count literal** in `test_skill_table.py`, same MR.

### D. Change a threshold, band boundary, or severity display name

Edit it **in the TD only.** Every such value is parsed from the TD by
`harness/skill_table.py`. **Never hardcode a second copy** in Python or a test — a second copy
goes stale silently. This has bitten the repo twice; both times a green test was pinning the
wrong value. See [Invariant #2](#2-never-hardcode-a-threshold-band-or-severity-in-code).

---

## The benchmarking scorer prompts (hand-maintained)

The two prompts in [`harness/rubric/`](../../harness/rubric/) —
[`ara-scorer-prompt.md`](../../harness/rubric/ara-scorer-prompt.md) and
[`mod-scorer-prompt.md`](../../harness/rubric/mod-scorer-prompt.md) — are hand-pinned snapshots
of the rubric for the **external benchmarking platform**. They are the **only** rubric-derived
artifacts that need manual updating on **every** rubric change (count *or* severity *or* wording
*or* pathway). The harness itself reads the TD at runtime and needs no such sync; these two do.
See the last section of [`harness/rubric/README.md`](../../harness/rubric/README.md).

---

## Before you open a PR / MR

```bash
pip install -r harness/requirements.txt
python3 -m pytest harness/tests/ -q          # the full harness suite, a few hundred tests, seconds
```

Then walk the [invariants](#invariants--what-breaks-silently) below — the things that break
without a red test. That is the highest-leverage part of this page.

---

## Invariants — what breaks *silently*

The harness has hundreds of tests, but the failures that hurt most are the ones **no test
catches**: they produce a green build and a wrong assessment. Walk this list before every rubric
MR.

### 1. Never renumber a question to close a gap

A `question_id` is a permanent join key. Sliding `Q4→Q3` after deleting `Q3` silently reassigns
every finding, golden-baseline row, and priority-table entry to a *different* question. The count
assertion **won't** catch it. Removals leave a hole: `Q1, Q2, Q4, …`. → [playbook §C](#c-remove-a-question).

### 2. Never hardcode a threshold, band, or severity in code

Every threshold, band boundary, and severity display name is parsed from the TD by
`harness/skill_table.py`. A second copy in Python or a test goes stale silently. **This has
bitten the repo twice — both times a green test was pinning the wrong value.** Change it in the
TD; let the parser read it.

### 3. Update the count literal when you add or remove a question

The count now *derives* from the parse, so you never edit `skill_table.py`. The one thing you do
edit is the literal in `test_the_severity_table_is_parsed_from_the_td_not_transcribed`
([`harness/tests/test_skill_table.py`](../../harness/tests/test_skill_table.py)). It **does**
fail loudly if you forget — but only for a *count* change. It cannot tell an intentional add from
an accidental parse drift, so if a heading drifts and the count happens to still match, nothing
fires. Keep headings in the exact `#### <ID>: <title> — SEVERITY` form (four `#`, em-dash).

### 4. Never edit generated files by hand

- `harness/SCORES.md` — regenerated by `harness/score-reports.py`.
- `harness/golden-accuracy-baseline.json` — a measurement, not an opinion; regenerated by the
  rebaseline pipeline.

Hand-editing either makes the baseline lie. Golden report trees under `harness/golden/` are
likewise refreshed by a maintainer / the rebaseline job, not by hand.

### 5. Keep the benchmarking scorer prompts in sync

`harness/rubric/ara-scorer-prompt.md` and `mod-scorer-prompt.md` are hand-pinned snapshots.
Nothing auto-syncs them; a rubric change that skips them leaves the external benchmark scoring
against the old rubric. → [scorer prompts](#the-benchmarking-scorer-prompts-hand-maintained).

### 6. Don't silently relax a safety signal

Changing *how* a signal is inferred is fine. Moving a question into a **less severe** band (e.g.
a RISK-SAFETY → INFO demotion), or removing/moving the `⚡` scope marker, is a real safety
change — state it explicitly in the MR intent so the judge and reviewers can weigh it. Never let
a demotion ride in unremarked.

### 7. A green GitHub PR is not "the harness approved this"

The change-impact harness is **GitLab-only** — it needs AWS credentials to run the analysis, so
it lives in the internal AWS GitLab mirror, not GitHub Actions. A GitHub PR gets human review but
**no automated harness feedback**; a maintainer runs the harness and reports back. Push
harness/TD work to the `gitlab` remote to get CI. → [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

### 8. Describe your intent, or get a vague verdict

The harness diffs your change against a committed baseline and asks an LLM judge whether the
delta matches **what you said you were changing**. No stated intent → the judge has nothing to
check the delta against. Fill in the `rubric-change` MR template. → DESIGN.md §6, §8.1.

> **The through-line:** the TD is the single source of truth. Anything that keeps a *second* copy
> of a rubric value — a test literal, a Python constant, a scorer prompt, a stale doc — is a
> silent-drift hazard. When in doubt, read the value from the TD.

---

## Where the deeper docs live

- Each TD's `SKILL.md` — the **authoritative rubric itself**.
- [`harness/rubric/README.md`](../../harness/rubric/README.md) — rubric source-of-truth notes +
  benchmarking-prompt maintenance detail.
- [`harness/README.md`](../../harness/README.md) — operator guide: the MR flow, the one score,
  the noise band.
- [`harness/DESIGN.md`](../../harness/DESIGN.md) — full design: what the TDs emit (§2), the scored
  dimensions (§3), change→impact flow (§5), the LLM judge (§6), CI wiring (§8).
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — repo-level PR mechanics + the GitLab-only
  automation caveat.
