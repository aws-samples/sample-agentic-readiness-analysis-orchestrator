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
4. [A worked example — re-scoring one question, end to end](#a-worked-example--re-scoring-one-question-end-to-end)
5. [Reading the verdict you get back](#reading-the-verdict-you-get-back)
6. [The contributor use-case matrix — what passes, what fails, why](#the-contributor-use-case-matrix--what-passes-what-fails-why)
7. [Refreshing the golden baseline — two ways](#refreshing-the-golden-baseline--two-ways)
8. [The benchmarking scorer prompts](#the-benchmarking-scorer-prompts-hand-maintained)
9. [Before you open a PR / MR](#before-you-open-a-pr--mr)
10. [Invariants — what breaks silently](#invariants--what-breaks-silently)
11. [Where the deeper docs live](#where-the-deeper-docs-live)

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
code change** — the only follow-up is when you change the *number* of questions: that touches one
count literal, and **adding** one also needs a golden rebaseline (see
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

That derivation is safe only because **one** literal still pins the expected number: the
constant `EXPECTED_QUESTION_COUNTS = {"ara": 43, "mod": 37}` at the top of
[`harness/tests/test_skill_table.py`](../../harness/tests/test_skill_table.py) — the single,
greppable place a rubric-size change is acknowledged. An **accidental** parse drift (a
broken `####` heading, a hyphen where an em-dash belongs, a duplicated row) changes the parsed
count but not the literal, so it fails **loudly, there**. An **intentional** add/remove is the
one time you touch that literal — in the same MR as the TD edit. For what the TD emits and how
it is scored end-to-end, see [`harness/DESIGN.md`](../../harness/DESIGN.md) §2–§3.

---

## The change playbook

**Anyone can add, remove, or edit any question or rubric value.** What differs is the *follow-up* —
and there are only three cases. This table is the whole routing decision; the rest of this section
is just the detail for each row.

| If you… | Edit the TD | Count literal (`test_skill_table.py`) | Golden rebaseline | Then | See |
|---|:---:|:---:|:---:|---|---|
| **Edit a question** (re-score, reword, change scope / severity / archetype / pathway) | ✅ | — | ❌ **no** | validate the specific use case, **trust the judge** on the semantics | [§A](#a-re-score-a-question-severity--wording--criteria--scope--archetype--pathway) |
| **Add a question** | ✅ | bump (`43→44`) | ✅ **required** | the golden can't answer a question that didn't exist when it was made | [§B](#b-add-a-question) |
| **Remove a question** | ✅ | decrement (`44→43`) | ❌ **not needed** (optional cleanup) | the golden still covers the *smaller* rubric — it's a superset | [§C](#c-remove-a-question) |

> **The rebaseline rule in one line — and it's the opposite of what intuition suggests:**
> **ADD needs a rebaseline, REMOVE does not.** The golden must be able to answer *at least* every
> question in the rubric. Adding grows the rubric past what the golden covers → refresh. Removing
> shrinks it → the golden still covers everything → fine. Editing a question changes neither the
> question set nor the count, so the harness picks it up at runtime with **no code change and no
> rebaseline** — you just state your intent and let the judge weigh the delta.

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

Adding a question is the one case that needs a **golden refresh** — and it's worth understanding
*why*, because [removing](#c-remove-a-question) one does not. The golden report trees under
`harness/golden/` were generated before your new question existed, so they physically cannot
answer it. The coverage contract is a **superset check** (`rubric_ids ⊆ answered_ids`): after you
add `ENG-Q6`, every golden report is *missing* it, and the harness flags an incomplete-coverage
gap. No test edit can paper over that — it is a real gap until the golden is regenerated against
your edited TD.

1. Add the question in its `references/*.md` section **and** any count/summary tables that
   reference it, in one change.
2. **Use the next free number in the category, never reuse a retired one** (highest `AUTH-Q7`
   → add `AUTH-Q8`).
3. **Update the count:** bump the affected number in `EXPECTED_QUESTION_COUNTS` at the top of
   [`harness/tests/test_skill_table.py`](../../harness/tests/test_skill_table.py) — `43`→`44`
   for ARA, `37`→`38` for MOD — in the **same MR**. It's the first thing in the file, above the
   tests. Forget it and CI fails loudly with the count it parsed and the two causes.
4. **Refresh the golden** so the baseline reports answer the new question — you do NOT hand-edit
   them; you *regenerate* them with the harness. See
   [Refreshing the golden baseline](#refreshing-the-golden-baseline--two-ways) for both paths
   (a local `atx` run, or the no-setup CI path that opens a golden-refresh MR into your own
   branch).
5. Open a `rubric-change` MR with intent + expected impact.

### C. Remove a question

Same as add, but **no golden refresh is required.** After you delete `ENG-Q5`, every golden report
still answers all the *remaining* questions — it's a strict superset of the smaller rubric, so the
`rubric_ids ⊆ answered_ids` check still holds and coverage stays green. The one thing that fails is
the count tripwire, which you fix by decrementing the literal. (You *may* refresh the golden to
drop the now-orphan answer, but it is optional — the orphan is tolerated as a benign extra.)

- **Leave the gap** (`Q1, Q2, Q4, …`). **Do NOT** slide `Q4→Q3` to close it — that silently
  reassigns every finding, baseline row, and priority to a *different* question, and the count
  assertion won't catch it (count moves the same either way). See
  [Invariant #1](#1-never-renumber-a-question-to-close-a-gap).
- If the gap bothers you, retire the *question* (mark deprecated / Not Evaluated) but keep the
  ID reserved.
- **Decrement `EXPECTED_QUESTION_COUNTS`** at the top of `harness/tests/test_skill_table.py`
  (`44`→`43`), same MR — the same constant an [add](#b-add-a-question) bumps, decremented instead.

### D. Change a threshold, band boundary, or severity display name

Edit it **in the TD only.** Every such value is parsed from the TD by
`harness/skill_table.py`. **Never hardcode a second copy** in Python or a test — a second copy
goes stale silently. This has bitten the repo twice; both times a green test was pinning the
wrong value. See [Invariant #2](#2-never-hardcode-a-threshold-band-or-severity-in-code).

---

## A worked example — re-scoring one question, end to end

The playbook above is the map; here is one whole trip through it, the most common change there
is: **re-scoring an existing question.** Nothing here is new — it just shows the pieces in order.

Say you want AUTH-Q5 (credential management) to weigh missing rotation more heavily. Today its
heading reads:

```
#### AUTH-Q5: Credential Management — RISK-SAFETY
```

1. **Edit the TD, and only the TD.** Open
   `definitions/managed/agentic-readiness-analysis/references/02-question-bank.md`, find the
   AUTH-Q5 block, and adjust its calibration prose (or, if you were changing the *band*, the
   `— SEVERITY` suffix on that heading). You touch **no** Python, **no** count literal (the
   question set didn't change), and **no** golden (re-scoring, per [§A](#a-re-score-a-question-severity--wording--criteria--scope--archetype--pathway)).
2. **Run the offline suite** — the same one CI runs, no AWS, seconds:
   ```bash
   python3 -m pytest harness/tests/ -q
   ```
   Green means you didn't break the output contract. An edit like this *should* be green with
   zero test changes; if a test went red, you changed more than you thought (e.g. a heading
   format the parser depends on).
3. **Open a `rubric-change` MR** using the template (it auto-loads on GitLab; on GitHub use the
   PR template). Fill in **What / Why / Expected impact** concretely — e.g. *"tightened AUTH-Q5
   so an unrotated static credential reads as RISK-SAFETY, not INFO; expect more AUTH RISK-SAFETY
   findings on `legacy-shipping-api`, and a possible ARA tier drop there."* The judge scores the
   observed delta **against this intent**, so vague intent → vague verdict.
4. **Answer the template's one non-obvious question: "Was the rubric edited in the AWS Transform
   service?"** For a repo edit like this the answer is **no** (the default) — see the box below
   for why that question exists.
5. **Read the advisory verdict** the pipeline posts as an MR comment (next section).

> **In-repo vs in-service — why the template asks.** This repo is the *proposal and test* surface;
> the live rubric runs inside the **AWS Transform service** (Continuous Modernization). The
> harness fixtures always execute the **repo copy** of the TD. So if you edited the rubric
> *in-service* instead of here, the fixtures run the unedited repo copy and the delta comes back
> **empty** — which looks identical to "my edit didn't land." Checking **yes** tells the judge to
> read an empty delta as *stale goldens*, not *a no-op edit*, and is the cue to fire
> `harness:full` (web pipeline → **Run pipeline**) to regenerate the goldens from the in-service
> rubric. For the normal path — you edited `SKILL.md`/`references/` in this repo — the answer is
> **no**, and the fixtures pick your change up automatically.

## Reading the verdict you get back

The pipeline posts **one advisory comment** on your MR. It never blocks the merge — every harness
job is `allow_failure: true`. Read it as a **second opinion**, not a gate. Three fields carry the
signal:

| Field | Values | What it means for you |
|---|---|---|
| `analysis_effect` | `improves` / `neutral` / `degrades` | The measured direction: is the assessment more accurate/safer (`improves`), materially unchanged (`neutral`, i.e. within noise — **not** a failure), or did it lose signal / understate risk (`degrades`)? |
| `verdict` | `LGTM` / `needs-work` | `LGTM` = safe for the analysis and not a regression. `needs-work` = look again (a degrade, an unscored report the harness couldn't measure, or a quality/safety flag fired). |
| `safety_hold` | `true` / `false` | An independent axis: a **tier-material safety signal moved** (a blocker/RISK-SAFETY relaxation that changes a readiness tier). When true you get `needs-work` regardless of intent — a human must sign off. |

**When the verdict disagrees with your intent, that is the harness doing its job — not a bug to
route around.** A change can be described perfectly and still degrade the analysis; the judge
measures the *delta*, and reports your intent only as supporting evidence. Two common cases:

- **`needs-work` + "within noise / unscored":** the delta was too small to measure, or a report
  failed to score, so the change **can't be validated** — it's reported as a harness error to
  fix, never as a silent pass. Re-run, or narrow the change so the effect is measurable.
- **`safety_hold: true` on a change you meant to be safe:** you relaxed a safety signal without
  saying so. Either it's wrong (restore the severity) or it's deliberate — in which case
  **state it in the MR intent** ([Invariant #6](#6-dont-silently-relax-a-safety-signal)) so the
  judge and a reviewer can weigh it on purpose. Never let a demotion ride in unremarked.

The rationale cites specific `question_id`s / pathway ids / program acronyms, so it tells you
*which* part of the delta drove the call. For the full calibration ladder see
[`harness/DESIGN.md` §6](../../harness/DESIGN.md).

## The contributor use-case matrix — what passes, what fails, why

The [change playbook](#the-change-playbook) above covers the three things *you* do (add / remove /
edit). This matrix is the fuller picture: it adds the cases the *harness* decides on its own — how
a report that invents an id is treated, what a parse typo does, what a safety demotion triggers — so
you can predict the suite's behavior before you push. You should not have to guess, and you should
**never** have to hand-edit tests to make a legitimate rubric edit pass: a rubric change touches
**at most one** test literal (the count tripwire) plus, for an add, a golden refresh. Everything
else derives from the TD at runtime. This table is the contract — if your change behaves
differently, that's a bug in the harness, not a cue to edit tests.

| You did this | Count tripwire (`test_skill_table.py`) | Golden refresh | Other test edits | Local check result |
|---|---|---|---|---|
| **Edit a question** (re-score / wording / criteria / scope / archetype / pathway) | — | — | none | ✅ green — picked up at runtime |
| **Add a question** | bump the literal (`43→44`) | **required** (golden can't answer the new id) | none | ❌ until golden refreshed → then ✅ |
| **Remove a question** | decrement the literal (`44→43`) | optional (superset still covers) | none | ✅ once literal matches |
| **Rename a question's title** (same id) | — | — | none | ✅ — the id is the key, not the title |
| **Renumber an id** (`Q4→Q3`) | — (count unchanged) | — | none | ⚠️ **passes but is WRONG** — [Invariant #1](#1-never-renumber-a-question-to-close-a-gap). Don't. |
| **Report invents an extra id** (`DATA-Q3-ext`), no tier-moving severity | — | — | none | ✅ tolerated as a benign extra (low demerit), *not* a hard fail |
| **Report invents an extra id carrying BLOCKER / RISK-SAFETY** | — | — | none | ❌ hard fail — a phantom id must not feed `blocker_count`/`risk_safety_count` |
| **Add a fixture** | — | golden for the new fixture | none | ❌ until the new fixture has a golden |
| **Accidental parse drift** (hyphen for em-dash, broken `####`) | fails HERE, loudly | — | none | ❌ — fix the heading, don't bump the number |
| **Demote a safety signal** (RISK-SAFETY→INFO, drop `⚡`) | — | — | none | ✅ mechanically — but [state it in MR intent](#6-dont-silently-relax-a-safety-signal) or the judge can't weigh it |

Two ideas do all the work in that table:

- **The count doesn't matter; the output contract does.** Coverage is a *membership* check
  (`rubric_ids ⊆ answered_ids`), not a count-equality check. A report that answers every real
  question passes even if it also emits a grounded extra id; a report that drops a real question
  fails even if a fabricated id keeps the total looking right. So a fabricated-but-harmless `-ext`
  id is a low-severity demerit, while a *dropped* real question — or a fabricated id that carries a
  tier-moving severity — is a hard fail. Severity, not arithmetic, decides.
- **Trust the judge for the semantics; pin only the one number.** The unit tests assert the
  *contract* (coverage is complete, findings and evaluations are disjoint, severities are read from
  the TD not transcribed), not specific finding text. The semantic question — "does this delta
  match what you said you were changing?" — is the LLM judge's job on the MR, not a brittle literal
  in a test. That's why re-scoring a question needs **zero** test edits.

## Where the fixtures live (and adding one)

The fixtures are the sample repositories every TD is exercised against. They live under
[`harness/fixtures/`](../../harness/fixtures/) (`modern/`, `monolith/`, `portfolio/`) and are
indexed by [`harness/usecases.yaml`](../../harness/usecases.yaml) — that file, not the directory,
is the source of truth for what runs. Each entry pairs a fixture with its coverage **axes**
(language, era, api, architecture, …) and per-TD **expectations** (the intent baseline the judge
scores the delta against — *not* an asserted equality):

```yaml
- id: legacy-crm-desktop
  path: harness/fixtures/portfolio/legacy-crm-desktop
  axes: { language: vb6, era: legacy, has_api: none, architecture: desktop, auth_present: false }
  expectations:
    ara: { tier: Not Agent-Integrable, must_have_categories: [AUTH, API, DISC] }
    mod: { tier: Not Ready, pathways_triggered: [move-to-cloud-native], overall_score_band: Not Ready }
```

**To add a fixture:** drop the repo under one of the `harness/fixtures/` trees, add its entry to
`usecases.yaml` (path + axes + expectations), and **generate its golden** — a new fixture has no
baseline, so coverage fails until one exists ([refresh the golden](#refreshing-the-golden-baseline--two-ways)).
Pick axes that fill a **gap** the coverage heatmap flags (`harness/coverage-heatmap.py`); a fixture
that only duplicates axes already covered adds runtime without adding signal. The axis vocab is
**closed** — add a value to the `axes:` block only alongside a fixture that uses it.

## Refreshing the golden baseline — two ways

The golden report trees under `harness/golden/` are the committed "before" picture the harness
diffs against. **Never hand-edit them** ([Invariant #4](#4-never-edit-generated-files-by-hand)) —
they are *regenerated* by running the harness over the fixtures with your edited TD. You only need
this when [adding a question](#b-add-a-question) or [a fixture](#the-contributor-use-case-matrix--what-passes-what-fails-why);
re-scoring and removals don't.

There are two paths. Pick by whether you have `atx` + AWS credentials set up locally.

#### Prerequisites at a glance

| | Path 1 (local) | Path 2 (CI, on your branch) |
|---|---|---|
| **Python + harness deps** | ✅ `pip install -r harness/requirements.txt` | ✅ (only to run the offline suite / read the diff) |
| **`atx` CLI** installed | ✅ **required** | ❌ not needed — CI has it |
| **AWS credentials** (Bedrock access) | ✅ **required** — this is the one step that calls AWS | ❌ not needed — CI vends its own via the Credential Vendor |
| **Push access to the GitLab mirror** | ✅ to open the MR | ✅ to push your branch + trigger the web pipeline |
| **Wall-clock** | ~10–20 min/fixture × the sweep, local | pipeline time, hands-off |

If you have neither `atx` nor AWS set up, use **Path 2** — that's exactly what it's for. Everything
*except* regenerating the golden (editing the TD, bumping the literal, running
`python3 -m pytest harness/tests/ -q`) is fully offline and needs only Python + the harness deps.

### Path 1 — locally (default, fastest feedback)

**Requires:** `atx` installed **and** AWS credentials with Bedrock access (see
[`harness/README.md`](../../harness/README.md) for the credential setup CI uses). If you don't have
these, jump to [Path 2](#path-2--let-ci-do-it-on-your-own-branch-no-local-atx-needed).

Regenerate the golden yourself and commit it alongside your TD edit — no round-trip through CI:

```sh
# Re-run the harness over every fixture with YOUR edited TD and write the results
# into the committed golden tree. This publishes the repo's TD folders as CUSTOM defs
# and runs `atx custom def exec` (NOT `atx ct` — that runs the old service-side TD and
# can't see your edit). This is the one step that needs AWS. See harness/README.md.
harness/run-fixtures.sh --scope all --write-golden --validate --jobs 6

# Refresh the accuracy baseline from the new golden, then confirm the suite is green
# against it — the same self-test CI runs.
harness/score-reports.py --trees harness/golden --update-baseline --ratchet --markdown
python3 -m pytest harness/tests/ -q
```

Commit the TD edit, the count literal, `harness/golden/`, `golden-accuracy-baseline.json`, and
`SCORES.md` **together** in one MR.

### Path 2 — let CI do it, on your own branch (no local `atx` needed)

If you can't run `atx` locally, you don't have to. Push your TD edit and let the pipeline
regenerate the golden for you and open a refresh MR **into your own branch**:

1. Edit the TD, bump the count literal, push your feature branch, open your `rubric-change` MR to
   `main`. It will go **red** — the golden can't answer your new question yet. That's expected; the
   failure message names the missing id.
2. On your branch, trigger a **web pipeline** (GitLab → CI/CD → **Run pipeline**, with your branch
   selected) and set the variable **`REBASELINE=true`**. The rebaseline job re-runs the harness
   over the fixtures with *your* edited TD.
3. Because it's a web run on a non-`main` branch, the job opens a golden-refresh MR **targeting your
   feature branch** (schedules and `main` runs still target `main`). It self-tests the fresh golden
   before proposing, so a broken refresh never lands.
4. Merge that refresh MR into your branch. Your original `rubric-change` MR now goes **green**, and
   you never touched a golden file by hand.

> **The refresh MR itself won't post a harness verdict — that's expected, not a stuck pipeline.** It
> touches *only* `harness/golden/` + the accuracy baseline, and the run/skip gate (`should-run.sh`)
> deliberately SKIPs a golden-only MR: re-analyzing the fixtures would just diff a fresh
> nondeterministic draw against the very golden the MR wrote, so every difference is draw-vs-draw
> noise, not a signal. The golden was already validated upstream by the ratchet in the rebaseline
> job before the MR was opened. The verdict you care about is on your `rubric-change` MR, where your
> TD edit lives.

> Why the refresh targets *your* branch: the weekly automated rebaseline maintains `main`, but a
> contributor's new question lives on a feature branch and can't merge to `main` until its golden
> exists. Sending the refresh back to the contributor's branch closes that loop without a
> maintainer in the middle. (Wired in `.gitlab-ci.yml`, `harness:rebaseline-gather`.)

> **The refresh MR *does* carry a whole-picture digest** — posted as a note by the rebaseline job
> itself, not by a harness run on the MR. It renders a go/no-go headline (overall mean groundedness
> vs the 0.80 floor: a healthy mean is merge-safe even with a below-floor outlier), the accuracy
> table (`was → now → Δ` per fixture), and any **potential issues to review** — reports below the
> floor and deterministic-check failures (count/tier reconciliation, severity undercounts) — framed
> as candidate TD issues, not merge blockers. It's a read-only join of `rebaseline-compare.json` +
> `rebaseline-results.json` (both job artifacts). See [`harness/rebaseline-digest.py`](../../harness/rebaseline-digest.py).
> This is distinct from the change-impact judge, which still does not run on a golden-only MR.

Either way the golden is *measured*, never authored — see
[Invariant #4](#4-never-edit-generated-files-by-hand).

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

**This step is fully offline** — it needs only Python and the harness deps, no `atx` and no AWS.
Run it on every rubric change, no matter which [golden-refresh path](#refreshing-the-golden-baseline--two-ways)
you use:

```bash
pip install -r harness/requirements.txt   # one-time; Python 3.11+
python3 -m pytest harness/tests/ -q        # the full harness suite, a few hundred tests, seconds
```

This is the same suite the MR pipeline runs — **run it locally so you don't discover a broken
contract only at the MR validator (the last step).** A green run here means your change satisfies
the output contract (coverage, disjoint findings/evaluations, severities read from the TD); a
red run tells you exactly which invariant you tripped. If you added a question, expect the count
tripwire and the coverage gap to be red until you [refresh the golden](#refreshing-the-golden-baseline--two-ways).

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
edit is the `EXPECTED_QUESTION_COUNTS` constant at the top of
[`harness/tests/test_skill_table.py`](../../harness/tests/test_skill_table.py). It **does**
fail loudly if you forget — but only for a *count* change. It cannot tell an intentional add from
an accidental parse drift, so if a heading drifts and the count happens to still match, nothing
fires. Keep headings in the exact `#### <ID>: <title> — SEVERITY` form (four `#`, em-dash).
Remember the asymmetry: an **add** also needs a
[golden refresh](#refreshing-the-golden-baseline--two-ways) (the golden can't answer the new
question); a **remove** does not (the golden still covers the smaller rubric).

### 4. Never edit generated files by hand

- `harness/SCORES.md` — regenerated by `harness/score-reports.py`.
- `harness/golden-accuracy-baseline.json` — a measurement, not an opinion; regenerated by the
  rebaseline pipeline.

Hand-editing either makes the baseline lie. Golden report trees under `harness/golden/` are
likewise *regenerated* — by you locally (`run-fixtures.sh --write-golden`) or by the CI rebaseline
job on your branch — never edited by hand. See
[Refreshing the golden baseline](#refreshing-the-golden-baseline--two-ways).

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
