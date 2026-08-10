# Contributing to the Transformation Definitions

**Start here** if you want to add, remove, re-score, or tweak a question or rubric in
one of the assessments. This is the front door — it does not re-explain what other docs
already own; it routes you to them and gives you the mental model to navigate.

> **Why this folder exists.** The knowledge needed to change a TD is spread across the
> SKILL spines, `harness/rubric/README.md`, `harness/DESIGN.md`, and `CONTRIBUTING.md`.
> This hub is the single index over all of it. When a linked doc and this page disagree,
> **the linked doc wins** — this page is a map, not a source of truth.

## What is a Transformation Definition (TD)?

A TD is the rubric the AWS Transform service runs against a repository. There are four
**managed** TDs (what `main` ships to prod):

| TD | What it scores | Questions |
|---|---|---|
| `agentic-readiness-analysis` (ARA) | Is a system safe for AI agents to call? | 43 |
| `modernization-readiness-analysis` (MOD) | Is a system ready to modernize? | 37 |
| `portfolio-agentic-readiness-analysis` | ARA rolled up across a portfolio + program recs | — |
| `portfolio-modernization-readiness-analysis` | MOD rolled up + program recs | — |

Each TD is a lean **`SKILL.md` orchestration spine** plus **`references/*.md`** files loaded
on demand. To understand how a TD is put together before you edit one, read
[**td-anatomy.md**](./td-anatomy.md).

## The one decision that routes everything

> **Are you changing the *number* of questions?**

- **No** (re-score, reword, flip a severity, change an `agent_scope`/archetype/pathway) →
  edit the TD's `references/*.md`, open a `rubric-change` MR. **No code change.** The harness
  picks it up at runtime.
- **Yes** (add or remove a question) → same as above **plus** bump
  `EXPECTED_QUESTIONS = {"ara": 43, "mod": 37}` in
  [`harness/skill_table.py`](../../harness/skill_table.py) in the same commit, or CI fails loudly.

The full playbook — including the permanent-ID rule (never renumber to close a gap) — lives in
[**change-a-question.md**](./change-a-question.md), which routes to the canonical steps in
[`harness/rubric/README.md`](../../harness/rubric/README.md).

## Before you open a PR

```bash
pip install -r harness/requirements.txt
python3 -m pytest harness/tests/ -q          # full harness suite, ~250 tests, seconds
```

Then read [**invariants.md**](./invariants.md) — the short checklist of things that break
*silently* (no test goes red) if you get them wrong. It is the highest-leverage page here.

## The four docs in this folder

| Doc | Read it when |
|---|---|
| [td-anatomy.md](./td-anatomy.md) | You want to know where a question, severity, or band actually lives before editing. |
| [change-a-question.md](./change-a-question.md) | You're adding / removing / re-scoring a question and want the exact steps. |
| [invariants.md](./invariants.md) | Always, before you commit — the "what breaks silently" checklist. |
| this README | You're lost and need to find the right doc. |

## Where the deeper docs live (authoritative)

- [`harness/rubric/README.md`](../../harness/rubric/README.md) — **canonical** rubric change
  workflow (re-score vs add/remove, ID rules, benchmarking-prompt maintenance).
- [`harness/README.md`](../../harness/README.md) — operator guide: the 6-step MR flow, the one
  score, the noise band.
- [`harness/DESIGN.md`](../../harness/DESIGN.md) — full design: what the TDs emit (§2), the
  scored dimensions (§3), change→impact flow (§5), the LLM judge (§6), CI wiring (§8).
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — repo-level PR mechanics + the GitLab-only
  automation caveat.
- Each TD's `SKILL.md` — the authoritative rubric itself.
