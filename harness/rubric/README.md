# Rubric Contribution Surface

> **What this is:** the **git-visible proposal surface** for the assessment rubric (the
> questions the ARA and MOD Task Definitions score against, and how gaps map to
> severity/score). It exists so that adding a new question or re-scoring an existing one is
> a **normal, reviewable Merge Request** the change-impact harness can run against.
>
> **What this is NOT:** the authoritative rubric. The live rubric — the full question set,
> scoring logic, category weights, MOD score bands, and the 7 modernization pathways — is
> **maintained in the AWS Transform managed service and versioned independently**
> (see every managed `SKILL.md`). The files here are a **proposal mirror**, not the source
> of truth.

See [`harness/DESIGN.md`](../DESIGN.md) — especially §2 (what the TDs emit), §3 (the five
scored dimensions), §5 (change → impact flow), and §8.1 (MR intent capture) — for how this
surface plugs into the harness.

## Why a git surface at all?

The rubric lives in the Transform service, so a `git diff` of `definitions/managed/**`
can never *see* a rubric edit. That makes rubric changes invisible to review and impossible
to test before they ship. This directory fixes that: it gives contributors a place to
**propose** a rubric change as text, open an MR, and get **automatic, evidence-backed
feedback** on what the change would actually do to the analysis output — before a maintainer
commits it into the service.

The split of responsibilities is intentional:

| Surface | Role | Owner |
|---|---|---|
| `harness/rubric/*.yaml` (this dir) | **Propose + test** a question/score change | Any contributor (mainly internal) |
| Harness (GitLab CI) | **Run** the change against fixtures, score the delta | Automated |
| AWS Transform service | **Deploy** — the authoritative rubric | Maintainer (manual sync) |

## Files

| File | Analysis | Contents |
|---|---|---|
| [`ara-questions.yaml`](./ara-questions.yaml) | Agentic Readiness (ARA) | Question bank across categories `AUTH / API / STATE / DATA / OBS / ENG / HITL / DISC`, each with `severity_guidance` mapping a gap to `native_severity` (`BLOCKER` / `RISK-SAFETY` / `RISK-QUALITY` / `INFO`). |
| [`mod-questions.yaml`](./mod-questions.yaml) | Modernization Readiness (MOD) | Question bank across categories `APP / DATA / INF / OPS / SEC`, each with `scoring_guidance` mapping a gap to the 0–4 `score` and `score_rating` band (`Not Ready` / `Needs Work` / `Partial` / `Mature`). |

These YAML files are a **representative seed**, not the complete rubric. They mirror real
`question_id` / `category_id` formats seen in the emitted reports (e.g. `AUTH-Q1`, `INF-Q11`)
so a machine — and a reviewer — can line a proposal up against actual analysis output.

## Workflow

### Propose a NEW question

1. Open the relevant YAML (`ara-questions.yaml` or `mod-questions.yaml`).
2. Find the category you want to extend (e.g. `AUTH`). Append a new entry using the **next
   free Q number** for that category (e.g. if `AUTH-Q7` is the highest, add `AUTH-Q8`). Keep
   the schema identical to the surrounding entries.
3. Fill in `title`, `intent` (what the question checks), and the guidance block
   (`severity_guidance` for ARA, `scoring_guidance` for MOD).
4. Open a Merge Request using the **`rubric-change`** MR template. Describe *what* you added,
   *why*, and the *expected impact* (which dimension(s) D1–D5 should move — e.g. "more AUTH
   findings on token-rotation gaps," "a repo drops a tier," "a pathway newly triggers").
5. The GitLab pipeline runs the harness (`should-run.sh` → fixtures → `diff-reports.py` →
   judge) and posts an **advisory** verdict comment: did the delta match your stated intent,
   and is it a no-op? The comment never blocks the MR.
6. A maintainer reviews. On approval, the maintainer **manually syncs** the new question into
   the AWS Transform service and refreshes the golden baselines (a dedicated "baseline update"
   MR, per DESIGN.md §7).

### Re-score an EXISTING question

1. Locate the question by its `id` in the YAML.
2. Edit only its guidance block — `severity_guidance` (ARA) or `scoring_guidance` (MOD). Do
   **not** renumber or delete the entry; changing an `id` breaks the mapping to emitted
   findings.
3. Open a `rubric-change` MR and state the intent (e.g. "tighten `AUTH-Q5` so missing rate
   limiting is `RISK-SAFETY` instead of `INFO`; expect more RISK-SAFETY findings and possible
   ARA tier drops").
4. Same as above: the harness runs, the judge posts an advisory verdict, a maintainer syncs
   the approved change into the service.

## Important notes

- **Editing YAML here does not change production behavior.** Nothing is live until a
  maintainer syncs it into the AWS Transform service. This surface is a proposal + test bed.
- **If you edited the rubric directly in the AWS Transform service** (not here), there is no
  git diff for the harness to catch. Tick that box in the MR/issue template so a maintainer
  runs `harness:full` manually and re-baselines the goldens (DESIGN.md §5, §8).
- **Keep the two remotes in sync.** Content mirrors between GitHub and GitLab; automation runs
  on **GitLab only**. GitHub stays open for issues/PRs but triggers nothing.
- Never put credentials, account IDs, or customer data in these files.
