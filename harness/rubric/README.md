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
> when you add or remove a question, which needs a one-line count bump (see below).

See [`harness/DESIGN.md`](../DESIGN.md) — especially §2 (what the TDs emit), §3 (the five
scored dimensions), §5 (change → impact flow), and §8.1 (MR intent capture) — for how a rubric
change flows through the harness.

## Files in this directory

| File | Purpose |
|---|---|
| [`ara-scorer-prompt.md`](./ara-scorer-prompt.md) | Self-contained ARA report-scoring prompt for the **external benchmarking platform**. A hand-pinned snapshot of the harness grader as a **single prompt** (rubric + baked-in severity/tier tables + per-report resolution rules) that emits `<score>X.X</score>` + a summary — the format the benchmark parses. |
| [`mod-scorer-prompt.md`](./mod-scorer-prompt.md) | Same, for MOD (1–4 scale, core/non-core mapping, classification thresholds, 7 pathways). |

These `.md` prompts are the ONLY rubric-derived artifacts here that need hand-maintenance —
see the last section.

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
2. **Bump the count.** The harness asserts on rubric size:
   `EXPECTED_QUESTIONS = {"ara": 43, "mod": 37}` in
   [`harness/skill_table.py`](../skill_table.py). Increment (add) or decrement (remove) the
   number for the affected analysis, in the same MR.
3. Open a `rubric-change` MR with intent + expected impact and let the harness post its
   advisory verdict.
4. A maintainer refreshes the golden baselines on approval (DESIGN.md §7).

### Why the count is a manual step (and the only one)

The assertion fires on **any** size change — adding (43→44), removing (43→42), or a heading the
parser can no longer read all trip it. It is deliberate: a rubric that silently parses to the
wrong size hands the judge a table with questions missing, and the model fills the hole by
guessing — the exact bug this guard kills. If you forget the bump, **CI fails loudly** and the
assertion message states the count it parsed plus the two causes (intentional add/remove → bump
the constant; accidental parse drift → fix the heading, don't score on a partial table).

Everything that is NOT a count change — a severity flip, a reworded title, a changed
`agent_scope` resolution or archetype rubric, a pathway trigger — is read from the TD at runtime
and needs **no code edit**.

## The benchmarking scorer prompts need hand-maintenance on EVERY rubric change

Unlike the harness, [`ara-scorer-prompt.md`](./ara-scorer-prompt.md) and
[`mod-scorer-prompt.md`](./mod-scorer-prompt.md) are **hand-pinned snapshots** — the external
benchmarking platform can't read the TD at runtime the way the harness does, so the tables are
baked into the prompt text. That means they have **no runtime coupling and no assertion**: ANY
rubric change (count *or* severity *or* wording *or* pathway) requires editing them by hand.
Each file carries a "Maintenance" table mapping which kind of TD change touches which section.

> **Planned:** a deterministic exporter that regenerates these `.md` files from the harness's
> own `build_prompt()` output, plus a CI drift-check (`git diff --exit-code`) that fails when
> they fall out of sync — giving them the same "fail loudly when stale" protection the judge's
> count assertion already has. Until that lands, treat updating the two prompts as a manual
> follow-up on every rubric MR.

## Important notes

- **If you edited the rubric directly in the AWS Transform service** (not in this repo's TDs),
  there is no git diff for the harness to catch. Tick that box in the MR/issue template so a
  maintainer runs `harness:full` manually and re-baselines the goldens (DESIGN.md §5, §8).
- **Keep the two remotes in sync.** Content mirrors between GitHub and GitLab; automation runs
  on **GitLab only**. GitHub stays open for issues/PRs but triggers nothing.
- Never put credentials, account IDs, or customer data in these files.
