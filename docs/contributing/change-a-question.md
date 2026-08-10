# Change a Question — the playbook

A decision tree over the four kinds of change. The **authoritative** steps live in
[`harness/rubric/README.md`](../../harness/rubric/README.md) "Workflow: change the rubric" —
this page routes you to the right branch and flags what's easy to miss. When the two disagree,
that doc wins.

First, find where the question lives → [td-anatomy.md](./td-anatomy.md).

---

## A. Re-score a question (severity / wording / criteria / scope / archetype / pathway)

The common case. **No code change, no count bump.**

1. Edit the owning `references/*.md` (or `SKILL.md`) in the TD:
   - **ARA severity** → the `— SEVERITY` suffix on the `#### <ID>: … — SEVERITY` heading.
   - **MOD scoring** → the 1–4 criteria table for that question.
   - **scope / archetype / pathway** → the relevant resolution block.
2. **Do not change the question's `id`** — it's the join key for every downstream artifact.
3. Open a **`rubric-change`** MR. State *intent* and *expected impact* (which of D1–D5 should
   move, e.g. "tighten AUTH-Q5 so missing rotation is RISK-SAFETY not INFO; expect more
   RISK-SAFETY findings, possible ARA tier drops"). Vague intent → vague verdict.
4. The GitLab pipeline runs the harness and posts an **advisory** verdict. It never blocks.

## B. Add a question

1. Add the question in its `references/*.md` section **and** any count/summary tables that
   reference it, in one change.
2. **Use the next free number in the category, never reuse a retired one** (highest `AUTH-Q7`
   → add `AUTH-Q8`).
3. **Bump the count:** increment the affected entry in
   `EXPECTED_QUESTIONS = {"ara": 43, "mod": 37}` in
   [`harness/skill_table.py`](../../harness/skill_table.py), **same MR**. Forget this and CI
   fails loudly with the count it parsed and the two causes.
4. Open a `rubric-change` MR with intent + expected impact.
5. A maintainer refreshes the golden baselines on approval (DESIGN.md §7).

## C. Remove a question

Same as add, but:

- **Leave the gap** (`Q1, Q2, Q4, …`). **Do NOT** slide `Q4→Q3` to close it — that silently
  reassigns every finding, baseline row, and priority to a *different* question, and the count
  assertion won't catch it (count is unchanged either way).
- If the gap bothers you, retire the *question* (mark deprecated / Not Evaluated) but keep the
  ID reserved.
- **Decrement the count** in `EXPECTED_QUESTIONS`, same MR.

## D. Change a threshold, band boundary, or severity display name

Edit it **in the TD only.** Every such value is parsed from the TD by
`harness/skill_table.py`. **Never hardcode a second copy** in Python or a test — a second copy
goes stale silently. This has bitten the repo twice; both times a green test was pinning the
wrong value. See [invariants.md](./invariants.md).

---

## Don't forget the benchmarking scorer prompts

The two prompts in [`harness/rubric/`](../../harness/rubric/) —
[`ara-scorer-prompt.md`](../../harness/rubric/ara-scorer-prompt.md) and
[`mod-scorer-prompt.md`](../../harness/rubric/mod-scorer-prompt.md) — are hand-pinned snapshots
of the rubric for the external benchmarking platform. They are the **only** rubric-derived
artifacts that need manual updating on **every** rubric change. The harness itself reads the TD
at runtime and needs no such sync; these two do. See the last section of
[`harness/rubric/README.md`](../../harness/rubric/README.md).

## Before every PR

```bash
pip install -r harness/requirements.txt
python3 -m pytest harness/tests/ -q
```

Then walk [invariants.md](./invariants.md) — the things that break without a red test.
