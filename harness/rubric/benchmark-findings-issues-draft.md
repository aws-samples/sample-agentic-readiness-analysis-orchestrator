# ZG external-repo benchmark — TD defect issue drafts

Source: benchmarking-team grader over ZG-org GitHub repos, 2 runs (batches 1 & 2), 2026-08-10.
These are the **genuine TD defects** that survived triage — i.e. NOT the two clusters that
turned out to be grader-side:

- **Excluded — grader artifact (fixed):** INF-Q8/Q9 "N/A without spec authority" was a stale
  benchmark scorer prompt (`mod-scorer-prompt.md` §1 omitted both gates). Fixed in MR !21; the
  live harness grader was never affected (it parses gates from the TD at runtime). A CI drift
  guard now pins the prompt to the TD gate set.
- **Excluded — mostly correct behavior:** library "blanket N/A" (OpenAPITools, getsentry, tqdm)
  is what the `library` repo_type mapping requires (INF-Q1–Q11 + OPS-Q2–Q9 all N/A). The same
  repos scored NO in batch 1 and YES in batch 2 → grader inconsistency, not a TD bug. Flagged to
  the benchmarking team as a grader-consistency note, not filed as a TD issue.

Each draft below is ready to paste as a GitLab issue. Evidence rows are `repo (batch): note`.

---

## Issue 1 — MOD summary counts & overall_score don't reconcile with `findings[]`

**Labels:** `bug`, `mod-td`, `arithmetic`, `help-wanted`

### Summary
The MOD report's summary/classification block (High/Medium/Low counts, category means,
`overall_score`) is authored separately from the `findings[]` / `evaluations[]` arrays and drifts
out of sync. The counts a customer reads in the header don't match the findings the report
actually emitted, and in several cases the classification is computed off the wrong counts.

### Evidence (both batches)
- FlowiseAI/Flowise (b1): `medium_count` = 19 but the findings array has 21 Medium entries.
- conductor-oss/conductor (b1): classification counts 6H/7M/5L reported vs 7H/17M/9L in
  findings[]; (b2) `low_count`=4 vs correct 5; APP-Q2/Q3 misplaced in `evaluations[]`.
- Prowlarr/Prowlarr (b2): severity counts in classification 5H/12M vs actual 6H/20M.
- serverless/serverless (b2): SEC-Q5 scored at 4 but excluded from the SEC category mean →
  wrong overall_score & band. (Arithmetic defect, not a count-vs-findings drift, but same root:
  summary computed independently of the scored set.)
- webpack/webpack (b1): `overall_score` computed over 4 categories, not 5.
- coreui/...angular-admin-template (b2): DATA excluded from `overall_score`.
- realworld/angular-realworld-example-app (b2): improper N/A inflates `overall_score` from
  ~1.55 to 2.21 (interacts with issue-adjacent N/A errors, but the arithmetic doesn't
  self-check).

### Suspected root cause
The report template computes the summary block from a running tally the agent maintains, rather
than deriving it from the emitted `findings[]`/`evaluations[]` as the single source. There is no
in-report reconciliation step that recomputes counts from findings and asserts equality. The
`classification_consistency_check` the output contract already requires (see scorer prompt
"CLASSIFICATION") is either not emitted or passes without actually recomputing.

### Suggested fix direction
- Derive every summary number (per-severity counts, per-category means, `overall_score`) from
  the emitted findings/evaluations arrays — do not maintain a parallel tally.
- Make `classification_consistency_check` recompute High/Medium counts **from findings[]** and
  fail the analysis if they disagree with the classification block.
- Add a harness scoring check (offline) that recomputes counts from a report's findings and flags
  drift, so this class is caught on fixtures too.

---

## Issue 2 — MOD band label & Markdown-vs-JSON divergence

**Labels:** `bug`, `mod-td`, `report-template`, `help-wanted`

### Summary
The numeric score is right, but the band/severity **label** rendered from it is wrong, and the
Markdown and JSON renderings of the same report disagree. JSON is the authoritative contract, so
an MD headline that contradicts it misleads any human reading the report.

### Evidence
- Prowlarr/Prowlarr (b1): OPS category mean 1.50 labeled "Not Ready" instead of "Needs Work"
  (band table: `1.5–2.4 → Needs Work`, `< 1.5 → Not Ready`; 1.50 is Needs Work).
- gulpjs/gulp (b2): MD says Pilot-Ready but JSON (authoritative) correctly says Cloud-Native
  Ready.
- ToolJet/ToolJet (b2): INF `severity_status` "Critical" in MD vs correct "Needs Work" in JSON.
- greenshot/greenshot (b1): MD headline "Not Ready" instead of "Remediation Required".
- Lidarr/Lidarr (b2): DATA `severity_status` label inconsistency.
- umami-software/umami (b2): DATA has a High finding but `severity_status` = "Needs Work"
  (cosmetic but wrong rollup).

### Suspected root cause
Two things: (a) band-boundary handling at the exact boundary value (1.50) is off-by-one on `>=`
vs `>`; (b) the MD report and JSON report each format the band/severity independently from the
score rather than the JSON serializing first and the MD rendering *from* the JSON.

### Suggested fix direction
- Single source: compute band label & `severity_status` once, serialize to JSON, render MD from
  that JSON — never re-derive labels in the MD path.
- Pin the band boundaries explicitly in the report template (`>= 3.5 Mature | 2.5–3.4 Partial |
  1.5–2.4 Needs Work | < 1.5 Not Ready`) and add a fixture test at the 1.50 / 2.50 / 3.50
  boundaries.

---

## Issue 3 — MOD pathway trigger logic (invented rules / missed triggers)

**Labels:** `bug`, `mod-td`, `pathways`, `help-wanted`

### Summary
Two opposite failure modes on the 7-pathway model: a pathway suppressed by a rule the spec does
not contain, and a pathway that fails to trigger despite its Primary condition being clearly met.

### Evidence
- Alluxio/alluxio (b1): move-to-cloud-native incorrectly suppressed — the report invented a
  compound trigger rule. (Primary is `APP-Q2 < 3` alone; Supporting conditions must not gate it.)
  Note: scored 0.93 clean in b2 → partly run-variance.
- thingsboard/thingsboard (b1): move-to-open-source not triggered despite `DATA-Q4 = 2 < 3`
  meeting the Primary trigger condition. (0.93 clean in b2.)
- greenshot/greenshot (b2): move-to-containers not triggered — debatable for a desktop app;
  worth confirming the guard.

### Suspected root cause
The pathway step re-implements trigger logic in prose rather than mechanically evaluating
`Primary condition met AND guard not blocked`. "Supporting strengthens but never triggers alone"
and "Primary alone triggers" are being conflated case-by-case. The run-to-run flip (b1 defect →
b2 clean on Alluxio/thingsboard) says the logic is under-specified enough that the model resolves
it differently each run.

### Suggested fix direction
- Restate each pathway as an explicit boolean: `Triggered ⟺ (Primary condition) AND NOT (guard)`,
  with Supporting conditions marked as evidence-only (never part of the trigger boolean).
- Require `triggering_questions[]` to be `(question_id, score<3)` tuples drawn from the pathway's
  trigger set — so a trigger with no qualifying tuple is self-evidently wrong.
- The scorer prompt §3 already encodes the correct Primary/guard model — mirror that exact
  phrasing into the TD `02-pathways.md` so the two can't diverge.

---

## Issue 4 — MOD discovery miss: `.github/dependabot.yml` not detected

**Labels:** `bug`, `mod-td`, `discovery`, `help-wanted`

### Summary
The analysis claims no Dependabot configuration when `.github/dependabot.yml` exists in the repo,
producing wrong SEC-Q6 (Compute Hardening/Patching) and SEC-Q7 (Application Security Pipeline)
scores. A factual grounding miss on a well-known config path.

### Evidence
- iterative/dvc (b1): "claims no Dependabot when `.github/dependabot.yml` exists" → affects
  SEC-Q6/Q7.
- Sonarr/Sonarr (b2): same — denies `dependabot.yml` exists; also a Low-count arithmetic error
  (overlaps issue 1).

### Suspected root cause
Discovery/evidence-gathering for dependency-update automation looks for a narrower set of signals
than the real one, or misses the `.github/` path. Dependabot config canonically lives at
`.github/dependabot.yml` (also `.github/dependabot.yaml`); Renovate at `renovate.json` /
`.github/renovate.json`.

### Suggested fix direction
- Add the canonical paths to the SEC-Q6/Q7 "look for" evidence list: `.github/dependabot.yml`,
  `.github/dependabot.yaml`, `renovate.json`, `.renovaterc*`, and dependency-scan steps in CI.
- Add a fixture with a `.github/dependabot.yml` and assert SEC-Q6/Q7 credit it, so a future
  discovery regression is caught.

---

### Filing notes
- Target: internal GitLab (`gitlab.aws.dev/agentic-readiness-assessment/...`). No `glab`/token
  on the maintainer box at draft time — paste manually, or set a token and file via the API.
- Recommended sequencing: land the scorer-prompt fix (MR !21), ask the benchmarking team to
  re-run, then file whichever of #1–#4 still reproduce. #1 (counts) and #4 (dependabot) are
  run-stable and safe to file now; #3 (pathways) shows run-variance so confirm on a fresh run.
