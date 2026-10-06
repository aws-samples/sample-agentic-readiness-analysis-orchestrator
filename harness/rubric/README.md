# Rubric — Source of Truth & Change Workflow

> **New to changing rubrics?** The orientation guide is
> [`docs/contributing/`](../../docs/contributing/README.md) (TD anatomy, decision tree,
> invariants). **This page is the authoritative change workflow it routes to** — the steps
> below are canonical.

> **Where the rubric lives:** the **Task Definitions in this repo** are authoritative.
> The ARA and MOD question sets, severities, scoring logic, archetype calibration, MOD score
> bands, and the 7 modernization pathways are all defined in:
>
> - `definitions/managed/agentic-readiness-analysis/` — `SKILL.md` + `references/*.md`
> - `definitions/managed/modernization-readiness-analysis/` — `SKILL.md` + `references/*.md`
>
> **Edit the TD directly to change the rubric.** The harness reads those files at runtime
> (`skill_table.py::parse_questions` concatenates `SKILL.md` + `references/*.md`), so a TD edit
> is picked up on the next run with no separate mirror to maintain and no code change — except
> when you add or remove a question, which needs a one-line update to a single test literal
> (see below).

See [`harness/DESIGN.md`](../DESIGN.md) — especially §2 (what the TDs emit), §3 (the five
scored dimensions), §5 (change → impact flow), and §8.1 (MR intent capture) — for how a rubric
change flows through the harness.

## Files in this directory

| File | Purpose |
|---|---|
| [`ara-scorer-prompt.md`](./ara-scorer-prompt.md) | Self-contained ARA report-scoring prompt for the **external external benchmarking platform**. A pinned snapshot of the harness grader as a **single prompt** (rubric + baked-in severity/tier tables + per-report resolution rules) that emits `<score>X.X</score>` + a summary — the format the benchmark parses. Its mechanical blocks are marked `GEN` and auto-regenerated; the calibration/extended/N/A prose is hand-owned (see the last section). |
| [`mod-scorer-prompt.md`](./mod-scorer-prompt.md) | Same, for MOD (1–4 scale, core/non-core mapping, classification thresholds, 7 pathways). |
| [`ara-scorer-facts.lock.json`](./ara-scorer-facts.lock.json) | Machine-readable snapshot of **every TD-derived fact the ARA prompt bakes in** — the question set, severities, tier arithmetic, surface gates, N/A mappings — as parsed from the TD by `skill_table.py`. It is the drift baseline: `scorer-prompt-sync.py --check` re-derives these facts from the live TD and fails when they no longer match the lock, which is the signal that the prompt (and the Benchmark platform copy) must be regenerated and re-published. **Generated, never hand-edited** — `--write` (and the `harness:scorer-sync` CI bot) rewrite it. |
| [`mod-scorer-facts.lock.json`](./mod-scorer-facts.lock.json) | Same, for the MOD prompt. |

The two `.md` prompts and their `.lock.json` files are all rubric-derived. The locks are
regenerated mechanically; only the hand-owned *prose* in the prompts needs a human — see the
last section.

## Workflow: change the rubric

### Re-score an existing question (severity / wording / scoring criteria)

1. Edit the owning `references/*.md` (or `SKILL.md`) in the relevant TD — change the severity
   heading, the 1–4 criteria, an `agent_scope` resolution, an archetype rubric, a pathway
   trigger, etc. Do **not** change the question's `id`; that breaks the mapping to emitted
   findings.
2. Open a Merge Request using the **`rubric-change`** MR template. State the *intent* and the
   *expected impact* (which of D1–D5 should move — e.g. "tighten AUTH-Q5 so missing rotation is
   RISK-SAFETY not INFO; expect more RISK-SAFETY findings and possible ARA tier drops").
3. The GitLab pipeline runs the harness (`should-run.sh` → fixtures → `diff-reports.py` →
   judge) and posts an **advisory** verdict: did the delta match your intent, and is it a
   no-op? It never blocks the MR.
4. **No count bump needed** — re-scoring does not change the number of questions. The judge
   reflects your edit automatically on the next run.

### Add or remove a question

**IDs are permanent — add at the end, removal leaves a hole, never renumber.** A `question_id`
(e.g. `AUTH-Q7`) is a stable key, not a position: the parser reads whatever ID the heading
carries, and everything downstream joins on `(analysis_type, question_id)` — golden baselines,
the static priority table, portfolio aggregation, the findings/evaluations split. Nothing
requires the numbers to be contiguous.

- **Adding:** use the next free number in the category and never reuse a retired one — highest
  `AUTH-Q7` → add `AUTH-Q8`.
- **Removing:** delete the entry and **leave the gap** (`Q1, Q2, Q4, …`). Do **NOT** slide
  `Q4→Q3` to close it — that silently reassigns every finding, baseline row, and priority for
  those questions to a *different* question, and the count assertion won't catch it because the
  count is unchanged. If a gap bothers you, retire the *question* (mark it deprecated / Not
  Evaluated in the TD) but keep the ID reserved.

Steps:

1. Add (or delete) the question in the TD — its `references/*.md` section **and** anywhere the
   count/tables reference it — in one change. Respect the ID rule above.
2. **Update the count literal.** The rubric size is *derived* from the parse —
   `EXPECTED_QUESTIONS = {a: len(parse_questions(a)) for a in ("ara", "mod")}` in
   [`harness/skill_table.py`](../skill_table.py) — so there is no constant to keep in sync. The
   one place a size is pinned to a literal is the test
   `test_the_severity_table_is_parsed_from_the_td_not_transcribed` in
   [`harness/tests/test_skill_table.py`](../tests/test_skill_table.py) (`43` for ARA, `37` for
   MOD). Increment (add) or decrement (remove) the affected number there, in the same MR.
3. Open a `rubric-change` MR with intent + expected impact and let the harness post its
   advisory verdict.
4. A maintainer refreshes the golden baselines on approval (DESIGN.md §7).

### Why the count literal is a manual step (and the only one)

Because the runtime count *derives* from the parse, every consumer follows the TD automatically —
but that derivation is only safe because one test still pins the expected size to a literal. An
**accidental** parse drift (a broken `####` heading, a hyphen where an em-dash belongs, a
duplicated row) changes the parsed count but not the literal, so it trips **there**, loudly — a
rubric that silently parses to the wrong size would otherwise hand the judge a table with
questions missing and the model would fill the hole by guessing, the exact bug this guard kills.
An **intentional** add/remove is the one time you touch the literal. If you forget, **CI fails
loudly** and the assertion states the count it parsed plus the two causes (intentional add/remove
→ update the literal; accidental parse drift → fix the heading, don't score on a partial table).

Everything that is NOT a count change — a severity flip, a reworded title, a changed
`agent_scope` resolution or archetype rubric, a pathway trigger — is read from the TD at runtime
and needs **no code edit**.

## Keeping the benchmarking scorer prompts in sync with the TD

Unlike the harness, [`ara-scorer-prompt.md`](./ara-scorer-prompt.md) and
[`mod-scorer-prompt.md`](./mod-scorer-prompt.md) are **pinned snapshots** — the external Benchmark
platform can't read the TD at runtime the way the harness does, so the facts are baked into the
prompt text and can go stale. [`scorer-prompt-sync.py`](../scorer-prompt-sync.py) closes that gap
by deriving every baked-in fact from the same parsers the grader uses (`skill_table.py`):

- **`--check` (default, run in CI):** fails when the derived facts no longer match the
  `*-scorer-facts.lock.json`, **or** when a `GEN`-marked block in the `.md` is stale. The message
  names exactly which fact moved. Its *silence* is also a signal — a TD edit that doesn't touch a
  baked-in fact leaves the published prompt valid as-is.
- **`--write`:** regenerates the `GEN`-marked mechanical blocks (the severity/question table and
  the tier arithmetic) and rewrites the facts-lock.

**What is automated vs. still manual:**

- **Mechanical facts** (`GEN` blocks + the lock) — regenerated by `--write`. The
  **`harness:scorer-sync`** CI job runs on any TD-touching MR, regenerates them, and commits the
  result back to the branch, so you rarely run `--write` by hand.
- **Tuned prose** (calibration, extended-trigger wording, N/A-mapping rationale) is **hand-owned**
  — the exporter won't write it. When a TD change moves that prose, edit the prompt by hand. Each
  file's "Maintenance" table maps which kind of TD change touches which section.
- **Benchmark re-publish is always manual.** The steps above only fix the *in-repo* copy. The
  Benchmark platform serves a separate copy, so whenever a fact moves, `harness:scorer-sync` posts
  an **"ACTION REQUIRED: re-publish to Benchmark"** MR note — re-upload the regenerated prompt there,
  or the benchmark keeps scoring against stale facts. That note is the only signal; it isn't
  automated.

## Important notes

- **If you edited the rubric directly in the AWS Transform service** (not in this repo's TDs),
  there is no git diff for the harness to catch. Tick that box in the MR/issue template so a
  maintainer runs `harness:full` manually and re-baselines the goldens (DESIGN.md §5, §8).
- **Keep the two remotes in sync.** Content mirrors between GitHub and GitLab; automation runs
  on **GitLab only**. GitHub stays open for issues/PRs but triggers nothing.
- Never put credentials, account IDs, or customer data in these files.
