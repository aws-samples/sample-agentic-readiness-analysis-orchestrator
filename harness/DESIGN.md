# Change-Impact Harness — Design

> **Status:** Design approved (plan only, no code yet). All decisions locked — see [§0](#0-locked-decisions).
> **Scope:** the **4 managed TDs** only (`agentic-readiness-analysis`, `modernization-readiness-analysis`, `portfolio-agentic-readiness-analysis`, `portfolio-modernization-readiness-analysis`). Custom TDs (EBA, BAO, portfolio-BAO, bridge) are out of scope — they are planning/opportunity layers with looser, less-deterministic outputs.

## 0. Locked decisions

| Decision | Choice |
|---|---|
| Scope | 4 managed TDs only |
| Scored dimensions | D1 Findings (ARA+MOD), D2 Tier/readiness label (ARA+MOD), D3 Pathways (MOD), D4 Programs (ARA **and** MOD portfolio), D5 MOD numeric score (band-crossing) |
| D5 drift check | Band-crossing only — flag on `score_rating` band change, not raw numeric wobble |
| Before/after mechanism | **Committed golden reports** — baseline JSON per fixture; MR re-runs only the changed TD's fixtures and diffs vs golden |
| Judge gate | **Advisory MR comment only** — never blocks the pipeline |
| Judge intent input | Judge scores delta **against contributor intent** captured in a GitLab MR-template field (§8.1) |
| Trigger model | **Default-run, deterministic gate** (`should-run.sh`, NOT an LLM). Runs for *any* change that could plausibly move output; **skips only an explicit denylist** (LICENSE, README, docs, images, DESIGN.md). Permissive by design — never boxes contributors in. Manual `harness:full` for in-service rubric edits. LLM is spent only at the *end* (judge). |
| Rubric contributions | Rubric (questions/scores) is authored in a **git-visible contribution surface** (`harness/rubric/`) so adding/editing a question is a reviewable MR the harness runs against. The AWS Transform service stays authoritative; **the maintainer syncs approved rubric MRs into the service** (that step is intentionally human-owned). Contributions are open (mainly internal). |
| CI platform | **Runs on GitLab ONLY** — AWS access via the **AWS Credential Vendor** on the shared runner fleet (OIDC does NOT work on internal `gitlab.aws.dev` — IAM can't reach it to verify tokens). One CI var `AWS_CREDS_TARGET_ROLE` points at a per-project IAM role in the Isengard account; the runner auto-vends temp creds. GitHub stays **open for contributions** (issue/PR templates kept) but runs **no** automation; content mirrors both ways. |
| Templates | GitHub `.github/ISSUE_TEMPLATE/` kept (contributions welcome there); GitLab adds `.gitlab/` templates that also capture judge **intent** (§8.1). |

## 1. Purpose

Give any contributor **automatic feedback on whether a change they made to a managed TD actually impacts the analysis — and whether that impact is good or bad.**

Two questions the harness answers on every PR/MR:
1. **Did this change do anything?** — Show the concrete delta in analysis output across a representative set of use cases. A rubric edit that moves zero findings/pathways is probably a no-op (or a mistake).
2. **Is the change good or bad?** — An LLM-as-judge scores the delta against a baseline expectation and posts an advisory verdict (score + `LGTM` / `needs-work` + rationale citing specific rubric IDs).

## 2. What the managed TDs emit (the contract the harness scores against)

Grounded in the real reports under `examples/reports/full-analysis/`.

> **All four report shapes below are verified against the real artifacts in `examples/reports/full-analysis/` (deep scan, 2026-07-28).**

### ARA per-repo — `<repo>-ara-report.json`
- `classification` → `tier` (Agent-Ready / Pilot-Ready / Remediation Required / Not Agent-Integrable), `sub_qualifier`, `blocker_count`, `risk_safety_count`, `risk_quality_count`, `rule_matched`
- `counts` → totals by severity + `blocker` / `risk_safety` / `risk_quality` / `na`
- `findings[]` → `question_id` (e.g. `AUTH-Q5`), `category_id` (**AUTH / API / STATE / DATA / OBS / ENG / HITL / DISC**), `title`, `gap`, `recommendation`, `severity`, `priority`, `effort`, `phase`
- `evaluations[]` → per-question `status` / `reason` (the full rubric pass, of which findings are the notable subset)
- `recommended_actions[]` → **per-repo remediation actions only** (`action`, `question_ids`, `priority`, `effort`, `rationale`) — **no program/acronym fields**. Programs are portfolio-level only.

### MOD per-repo — `<repo>-mod-report.json`
- `classification` → `tier`, `high_count`/`medium_count`/`low_count`, `rule_matched`, `classification_consistency_check`
- `overall_score` (0–4, e.g. `3.0`), `categories[]` → `category_id`, `numeric_score`, `score_rating` (Not Ready / Needs Work / Partial / Mature) — **D5**
- `top_gaps[]`
- `findings[]` → **same schema as ARA findings**, with MOD `category_id` (**APP / DATA / INF / OPS / SEC**)
- `evaluations[]` → `question_id`, `category_id`, `status` (pass/fail), `score` (0–4), `reason`
- `pathways[]` → **present at the per-repo level too**: `id`, `name`, `status`, `priority`, `effort`, `key_trigger_criteria`, `triggering_questions[]`, `detail`

### ARA portfolio — `<portfolio>-ara-portfolio-report.json`
- `executive_dashboard` → `readiness_distribution`, `portfolio_summary` (`cross_cutting_blockers`, `cross_cutting_risks`)
- `repositories[]` → each with its own `classification.tier`
- `findings[]` (137 in the sample), `cross_cutting_findings[]` (`cross_cutting_type` = blocker/risk, `affected_repos_count`), `portfolio_level_findings[]`
- **`recommended_actions[]` → PROGRAMS.** Structured: `id`, `name`, `acronym`, `type` (`program` / `workshop`), `status` (**Triggered / Not Triggered**), `trigger_reason`, `suggested_timing`, `duration`, `what_it_provides`. Sample: **AI DLC** (workshop), **AXE** (program), **EBA on Agentic AI** (program).

### MOD portfolio — `<portfolio>-mod-portfolio-report.json`
- `executive_dashboard.tier_distribution`; **D5:** `executive_dashboard.portfolio_score_overview` (`portfolio_overall_score` e.g. `2.31`, `score_range`), `category_score_averages[]`, `score_band_distribution` {mature/partial/needs_work/not_ready}
- `technology_stack_summary`, `repositories[]` (each with `classification.tier`, `overall_score`, `category_scores[]`, `pathways_triggered[]`)
- `findings[]` (135 in the sample), `remediation_roadmap` (`total_pathways`, `items[].pathway_id`)
- **`recommended_actions[]` → PROGRAMS**, same structured shape as ARA portfolio. Sample: **EBA, MAP, OLA, MMP, WAMP, VMP, ISV WMP** (all `type: program`).
- `pathways[]` → the 7 modernization pathways, each:
  - `id` (`move-to-cloud-native`, …), `name`, `portfolio_status` (**Triggered / Not Triggered**), `priority`, `effort`
  - `triggered_in_repos_count`, `applicable_repos_count`
  - `recommended_aws_programs[]` (e.g. `Experience-Based Acceleration (EBA)`) — a **second** program surface, attached per-pathway
  - `contributing_repos[]` → `triggering_questions[]` (`question_id`, `score`, `note`)
  - `per_repo_not_triggered_reasons[]` → `consulted_questions[]` (why a pathway did **not** trigger)

**Key insight:** pathways record *both* why they triggered and why they didn't, so a change can be checked for correct **triggering / suppression**. Programs appear as **structured, scoreable objects** (`acronym` + `status`) on **both** portfolio reports — a much sharper signal than "a finding count changed."

## 3. The five scored dimensions

Verified mapping of each dimension to where it actually lives:

| # | Dimension | Applies to | Source in report | What a change can move |
|---|-----------|-----------|------------------|------------------------|
| D1 | **Findings** | **ARA + MOD** (per-repo **and** portfolio) | `findings[]` (+ ARA `counts`) | New/removed/re-severitied findings by `question_id` + `category_id` |
| D2 | **Classification tier** (readiness label) | **ARA + MOD** (per-repo **and** portfolio `repositories[]`) | `classification.tier`, `rule_matched` | Repo/portfolio moving between readiness tiers |
| D3 | **Modernization pathways** | **MOD only** (per-repo `pathways[]` **and** portfolio) | `pathways[].status`/`portfolio_status`, `triggering_questions` | A pathway newly Triggered / Not-Triggered; which questions drove it |
| D4 | **AWS program recommendations** | **ARA portfolio + MOD portfolio** | `recommended_actions[]` (`acronym`, `type`, `status`); MOD also `pathways[].recommended_aws_programs` | Which programs/workshops (AI DLC, AXE, EBA, MAP, OLA…) trigger for a portfolio |
| D5 | **Modernization numeric score** | **MOD only** (per-repo **and** portfolio) | `overall_score`, `categories[].numeric_score`/`score_rating`, portfolio `category_score_averages` + `score_band_distribution` | A category/overall score crossing a `score_rating` band (Not Ready / Needs Work / Partial / Mature) |

**D1 — findings exist on all four reports.** Same schema across ARA (categories AUTH/API/STATE/DATA/OBS/ENG/HITL/DISC) and MOD (categories APP/DATA/INF/OPS/SEC). Per-repo reports carry the repo's findings; portfolio reports carry the rolled-up `findings[]` plus (ARA) `cross_cutting_findings[]`.

**D2 — the tier classification (the "Agent-Ready / Pilot-Ready / …" readiness label).** Measured for every repo and every portfolio `repositories[]` entry, both analyses. This is the *categorical* readiness signal (distinct from D5's number). Tier vocabularies:
- **ARA tiers:** `Agent-Ready` / `Pilot-Ready` / `Pilot-Ready (Safety Concerns)` / `Remediation Required` / `Not Agent-Integrable`. Rolled up at portfolio level in `executive_dashboard.readiness_distribution` (percentages).
- **MOD tiers:** `Cloud-Native-Ready` / `Pilot-Ready` / `Remediation Required` / `Not Ready`. Rolled up in `executive_dashboard.tier_distribution`.

Tier drivers differ by analysis:
- **ARA:** **blocker-driven** — `blocker_count` (+ RISK-SAFETY counts) → tier via `rule_matched` (e.g. `0 BLOCKER, ≥3 RISK-SAFETY → Pilot-Ready (Safety Concerns)`). Measure **blocker count → tier**.
- **MOD:** **severity-count-driven** — High/Medium/Low counts → tier via `rule_matched` (e.g. `0 High, ≥2 Medium → Pilot-Ready`), with `classification_consistency_check`.

**ARA readiness is measured ONLY by D2** (categorical) — ARA reports carry no numeric score. MOD readiness is measured **both** categorically (D2 tier) **and** numerically (D5).

**D3 — pathways are MOD-only** but appear at **both** levels: per-repo `pathways[]` (`status` + `triggering_questions`) and portfolio `pathways[]` (`portfolio_status` + `contributing_repos` + `per_repo_not_triggered_reasons`).

**D4 — programs are PORTFOLIO-only, on BOTH ARA and MOD** (corrected):
- **ARA portfolio** `recommended_actions[]` → AI DLC, AXE, EBA-on-Agentic-AI (each with `acronym`, `type`, `status`, `trigger_reason`).
- **MOD portfolio** `recommended_actions[]` → EBA, MAP, OLA, MMP, WAMP, VMP, ISV WMP; **and** `pathways[].recommended_aws_programs[]` per triggered pathway.
- **Per-repo reports have no programs** — their `recommended_actions[]` are plain remediation actions with no `acronym`/`type`.

**D5 — MOD numeric score (MOD only, complements D2).** MOD carries a 0–4 numeric scoring layer that ARA does not:
- **Per-repo:** `overall_score` (e.g. `3.0`) and per-category `categories[].numeric_score` + `score_rating` (e.g. INF `3.36` "Partial", OPS `2.33` "Needs Work"). Findings also carry `mod_metadata.internal_score` / `score_label`.
- **Portfolio:** `executive_dashboard.portfolio_score_overview.portfolio_overall_score` (e.g. `2.31`), `category_score_averages[]`, and `score_band_distribution` {mature / partial / needs_work / not_ready}.
- **Drift check = band-crossing only** (decided): flag a change when a category or overall `score_rating` crosses a band (Not Ready ↔ Needs Work ↔ Partial ↔ Mature) or the portfolio `score_band_distribution` shifts. Raw numeric wobble within the same band is **not** flagged, to tolerate run-to-run noise. This catches score-only drift that D2 (tier) and D1 (findings) would miss — e.g. a rubric edit nudging INF 2.9→3.1 across the Needs-Work/Partial line without changing any finding or tier.
- **ARA has no D5** — its readiness is tier + distribution only (D2).

## 4. Use-case heatmap (`harness/usecases.yaml`)

The 10 repos in `sample-legacy-portfolio/` are a genuinely diverse fixture set. Confirmed profiles:

| Fixture | Stack / era | IaC | Notes |
|---|---|---|---|
| legacy-crm-desktop | VB6 (`.frm`) | no | thick-client desktop |
| legacy-document-portal | ColdFusion (`.cfm`) | no | legacy web |
| legacy-helpdesk-tickets | Python (`.py`) | no | script-era |
| legacy-loan-calculator | Java (`.java`, `.xml`) | no | JVM |
| legacy-partner-soap | Java + SOAP (`.wsdl`) | no | SOAP API surface |
| legacy-payroll-system | COBOL / JCL (`.jcl`) | no | mainframe |
| legacy-pricing-cgi | CGI (`.yaml` IaC) | **yes** | has IaC |
| legacy-shipping-api | Node.js (`package.json`) | **yes** | has IaC + REST API (also the Dependabot fixture) |
| legacy-storefront-rails | Ruby on Rails (`.rb`) | no | framework monolith |
| legacy-timesheet-webforms | VB.NET (`.vb`) | no | WebForms |

Plus `examples/fixtures/monolith/` (PHP) already used in analysis runs.

**`usecases.yaml` structure (per fixture):**
```yaml
- id: legacy-shipping-api
  path: sample-legacy-portfolio/legacy-shipping-api
  axes:                      # heatmap dimensions — used to prove coverage & find gaps
    language: nodejs
    era: legacy
    has_iac: true
    has_api: rest
    architecture: service
  expectations:              # baseline the judge scores against (per-repo, per applicable TD)
    ara:                     # per-repo ARA
      tier: Pilot-Ready               # D2: blocker-driven tier
      max_blockers: 0                 # D2: ARA tier is driven by blocker_count
      must_have_categories: [AUTH, DATA]   # D1: ARA findings expected in these categories
    mod:                     # per-repo MOD
      tier: Remediation Required      # D2: severity-count-driven tier
      must_have_categories: [INF, OPS]     # D1: MOD findings (MOD has findings too)
      pathways_triggered: [move-to-cloud-native]   # D3: per-repo pathways[] status
      overall_score_band: Partial     # D5: MOD numeric score → band (Not Ready/Needs Work/Partial/Mature)
      score_ratings: {INF: Partial, OPS: Needs Work}   # D5: per-category score_rating
# programs (D4) are PORTFOLIO-only, on BOTH ARA and MOD portfolios — expressed once per portfolio:
portfolio_expectations:
  ara:
    programs_expected: [AI DLC, AXE]                          # D4: ARA portfolio recommended_actions[]
  mod:
    pathways_triggered: [move-to-cloud-native, move-to-managed-databases]   # D3: portfolio pathways[]
    programs_expected: [EBA, MAP, OLA]                        # D4: MOD portfolio recommended_actions[] + pathways[].recommended_aws_programs
    portfolio_score_band: Partial                             # D5: portfolio_overall_score → band
```

The **coverage heatmap** is generated from the `axes` across all fixtures: it renders a matrix (language × has_iac × has_api × architecture) and flags gaps — e.g. "no Go fixture," "only 2 IaC fixtures," "no serverless architecture." This is what lets a reviewer see *which use-case types a TD is (and isn't) exercised against.*

## 5. Change → impact flow (per MR)

> **Reality check (verified 2026-07-28):** the managed rubric — questions (`AUTH-Q9`…), categories, MOD score bands, and the 7 pathways — is **not** stored in this repo. Every managed `SKILL.md` states the full definition is *"maintained in the AWS Transform service and versioned independently."* A `git diff` of `definitions/managed/**` therefore **cannot** see a rubric edit. The only git-visible thing that changes managed *output* is `references/program-library.md` (the D4 program triggers), which exists as **two identical copies** that must stay in sync. This drives the trigger model below.

**Trigger model — default-run, deterministic gate (GitLab only for now):** the gate is a **deterministic path check, not an LLM**, and it is **permissive by default.** `should-run.sh` runs `git diff --name-only` against the base and **runs unless *every* changed path matches a skip denylist** (`LICENSE`, `*.md` docs, `CONTRIBUTING`, `SECURITY`, images, `harness/DESIGN.md`, `.github/**`). Anything that could plausibly move output — a rubric edit under `harness/rubric/`, a `program-library.md` change, a new/edited fixture, a config change — runs. This deliberately does **not** box contributors in: if in doubt, it runs. No model decides whether to run (that would be slow, non-deterministic, costly per MR); the LLM is spent **only at the judge step (§6)**. Entry points:
1. **MR pipeline (GitLab)** — default-run gate as above. The primary contribution path.
2. **Manual `harness:full` run** — a maintainer edited the rubric *in the AWS Transform service* and wants a full re-baseline, or wants to force a full run. Fired from the GitLab "Run pipeline" button with a TD variable.
3. **Skip** — only when the whole diff is denylisted (docs/license/etc). Job stops cleanly, no `atx`, no cost.

```
should-run.sh   ── deterministic git-diff; run UNLESS all-denylisted ──▶  run │ skip   (no LLM)
      │ run
      ▼
run-fixtures ─▶ diff-reports.py ─▶ judge.py                            ◀── the ONLY LLM, at the end
```

> **Rubric-as-contribution:** the rubric (questions/scores) is authored under `harness/rubric/` so "add `AUTH-Q9`" or "re-score `INF-Q11`" is a normal reviewable MR the harness runs against. The AWS Transform service remains authoritative; the **maintainer syncs an approved rubric MR into the service by hand** — that human step is intentional (the repo is the *proposal + test* surface, the service is the *deploy* surface). All of this runs on **GitLab only** for now; GitHub stays open for issues/PRs but triggers nothing.

```
0. Gate                              should-run.sh → run | skip (see trigger model above)
1. Resolve scope                     git diff (program-library / harness) OR manual TD var → which TD(s) + fixtures
2. Select applicable fixtures        from usecases.yaml (--changed-only subset, or --all on manual full run)
3. Produce after-reports             run the affected TD via atx on selected fixtures  [see §7]
4. Diff vs baseline                   compute per-dimension delta (D1–D5) → impact.json
5. Judge                              LLM-as-judge consumes {delta, expectations, diff, INTENT from MR}  [§6]
6. Report                            post advisory verdict as MR comment (never blocks — §6)
```

**Delta computation (deterministic, pre-judge):** a small differ compares before/after reports and emits a structured `impact.json`:
```jsonc
{
  "changed_tds": ["modernization-readiness-analysis"],
  "per_repo": {                          // D1, D2, MOD per-repo D3, and MOD per-repo D5 live here
    "legacy-shipping-api": {
      "D1_ara_findings": { "added": [], "removed": [], "reseveritied": [] },
      "D1_mod_findings": { "added": ["INF-Q11"], "removed": [], "reseveritied": [] },  // MOD has findings too
      "D2_ara_tier": { "before": "Pilot-Ready", "after": "Pilot-Ready", "changed": false,
                       "blocker_count": { "before": 0, "after": 0 } },      // ARA: blocker-driven
      "D2_mod_tier": { "before": "Remediation Required", "after": "Remediation Required", "changed": false },
      "D3_mod_pathways_repo": { "newly_triggered": ["move-to-managed-databases"], "newly_suppressed": [] },
      "D5_mod_score": { "overall": { "before": 3.0, "after": 2.5, "band_before": "Partial", "band_after": "Needs Work", "band_crossed": true },
                        "categories": { "OPS": { "band_before": "Partial", "band_after": "Needs Work", "band_crossed": true } } }
      // D5 flags ONLY band crossings — a 3.0→2.9 drop that stays in "Partial" is not reported
    }
  },
  "portfolio": {
    "ara": {                             // D4 programs exist on the ARA portfolio too
      "D2_tier_distribution": { "changed": false },
      "D4_programs": { "added": [], "removed": [] }         // e.g. AI DLC / AXE / EBA-Agentic
    },
    "mod": {
      "D3_pathways": { "newly_triggered": ["move-to-managed-databases"], "newly_suppressed": [] },
      "D4_programs": { "added": ["OLA"], "removed": [] },   // recommended_actions[] + pathways[].recommended_aws_programs
      "D5_portfolio_score": { "before": 2.31, "after": 2.18, "band_before": "Needs Work", "band_after": "Needs Work", "band_crossed": false,
                              "band_distribution_shift": { "mature": 0, "partial": -1, "needs_work": +1, "not_ready": 0 } }
    }
  },
  "no_op": false   // true if every dimension is empty across every fixture → flags a likely no-op change
}
```

## 6. LLM-as-judge agent

- **Input:** `impact.json` (the delta) + the fixture `expectations` + the raw diff of the changed file(s) **+ the contributor's INTENT** (see below).
- **Intent is a first-class input.** The judge scores the delta *against what the contributor said they were trying to do* — not just against raw baseline. A change that adds 40 findings is "good" if intent was "tighten AUTH scoring" and "bad" if intent was "fix a typo in a recommendation string." Intent is captured in a **structured MR-template field** (§8.1) and passed to the judge as `intent: {what, why, expected_impact}`.
- **Prompt shape:** "You are reviewing a change to the analysis rubric/config. The contributor's stated intent is: {intent}. Here is the change, the use cases it was run against, the expected behavior, and the observed delta. Does the delta match the stated intent? Score it and decide LGTM / needs-work." Rubric explicitly instructs it to cite `question_id`s / `pathway.id`s and to flag **intent mismatch** (delta doesn't match what they said they'd do) and **no-op** (they intended a change but delta is empty).
- **Output (structured):**
  ```jsonc
  {
    "score": 0-100,
    "verdict": "LGTM" | "needs-work",
    "intent_match": "aligned" | "partial" | "mismatch",   // delta vs stated intent
    "rationale": "…cites AUTH-Q5, move-to-cloud-native, etc.…",
    "concerns": [ { "dimension": "D3", "detail": "…" } ],
    "no_op_warning": false        // true if intent claimed a change but delta is empty
  }
  ```
- **Gate policy:** **advisory only.** The judge posts the verdict + score as an MR comment; it **never fails the pipeline.** Humans decide. (Chosen this session; can tighten to regression-blocking later.)
- **Implementation note:** reuse the same LLM-as-judge pattern the orchestrator already relies on. Judge runs against the report JSON, not the HTML/MD renders.

## 7. Before/after mechanism — committed golden reports (decided)

**Chosen:** committed golden reports.

- `harness/golden/` holds one baseline report JSON per fixture, per applicable TD (the "before").
- On a triggered run: `should-run.sh` decides run/skip and resolves scope → `run-fixtures.sh` re-runs the affected fixtures via `atx` (the "after") → `diff-reports.py` diffs after vs golden → `impact.json`.
- Most fixtures are **not** re-analyzed each run — only the ones in scope — so pipelines stay fast.
- Golden files double as **regression fixtures**: an unexpected diff vs golden is itself a signal.
- **Refreshing goldens:** intentional rubric changes will legitimately move the baseline. Refresh via a dedicated "baseline update" MR (`run-fixtures.sh --all --write-golden`), reviewed on its own so baseline churn never hides inside a feature MR. This is also the mechanism for capturing an in-service rubric edit: run full, review the delta, commit the new golden.

Rejected: *live baseline + rerun* (every MR runs full ATX twice — too slow, double AWS cost); *judge-only, no rerun* (no true delta — weakest signal).

## 8. GitLab CI wiring (`.gitlab-ci.yml`) — **GitLab-only automation**

**Automation lives ONLY on GitLab.** GitHub stays open for contributions — the `.github/` dir keeps issue/PR templates so people can file and propose there — but carries **no** GitHub Actions/workflows. All analysis runs on GitLab, where the AWS credentials live. This keeps a single source of CI truth and avoids double AWS cost. Content mirrors between the two remotes; automation does not.

Two entry points, both advisory (`allow_failure: true` — never blocks):

```yaml
stages: [harness]

# Entry 1: MR pipeline — auto-gates on git-visible, output-affecting changes
harness:impact:
  stage: harness
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  script:
    - harness/should-run.sh || exit 0                  # gate: skip docs-only / unrelated MRs (§5)
    - harness/run-fixtures.sh --changed-only           # atx → after-reports  [§7]
    - harness/diff-reports.py --baseline harness/golden --after "$AFTER_DIR" -o impact.json
    - harness/judge.py --impact impact.json --intent "$CI_MERGE_REQUEST_DESCRIPTION" > verdict.json
    - harness/post-mr-comment.sh verdict.json          # advisory comment, non-blocking
  allow_failure: true

# Entry 2: manual/web run — the rubric-changed-in-service path (§5, trigger model)
harness:full:
  stage: harness
  rules:
    - if: '$CI_PIPELINE_SOURCE == "web"'               # "Run pipeline" button
  variables:
    CHANGED_TD: ""                                      # operator names the TD edited in-service
    RUN_SCOPE: "all"
  script:
    - harness/run-fixtures.sh --scope "$RUN_SCOPE" --td "$CHANGED_TD"
    - harness/diff-reports.py --baseline harness/golden --after "$AFTER_DIR" -o impact.json
    - harness/judge.py --impact impact.json --intent "$RUN_INTENT" > verdict.json
    - harness/post-mr-comment.sh verdict.json || cat verdict.json
  allow_failure: true
```

Requires AWS access on the GitLab runner for the `atx` step (analysis-scoped; personal Isengard account for now). Auth is the **AWS Credential Vendor** on the shared fleet — set the single CI var `AWS_CREDS_TARGET_ROLE` to a per-project IAM role whose trust policy allows `arn:aws:iam::979517299116:role/gitlab-runners-prod` to assume it, gated by `aws:PrincipalTag/GitLab:{Project,Group}`. The runner injects temp `AWS_ACCESS_KEY_ID/_SECRET_ACCESS_KEY/_SESSION_TOKEN` automatically — no OIDC, no static keys. See `harness/README.md` for the role setup.

### 8.1 MR template — captures INTENT for the judge (§6)

`.gitlab/merge_request_templates/rubric-change.md` gives contributors a structured intent block the judge consumes:
```markdown
## What are you changing?  <!-- e.g. "Tightened AUTH-Q5 scoring; added AUTH-Q9 for token rotation" -->
## Why?                    <!-- the problem this fixes -->
## Expected impact         <!-- which dimension(s) should move: more AUTH findings? tier drop on X? -->
## Was the rubric edited in the AWS Transform service?  [ ] yes → fire `harness:full` manually  [ ] no
```
The judge reads these as `intent.{what, why, expected_impact}` and scores the observed delta **against** them.

## 9. Proposed directory layout

```
harness/
├── DESIGN.md                 # this file
├── usecases.yaml             # fixture matrix + axes + expectations (§4)
├── golden/                   # committed baseline reports per fixture (§7)
├── should-run.sh             # gate: run|skip + resolve scope (git-visible or manual) (§5)
├── run-fixtures.sh           # drive atx over selected fixtures
├── diff-reports.py           # D1–D5 delta → impact.json (§5)
├── judge.py                  # LLM-as-judge (+ intent) → verdict.json (§6)
├── coverage-heatmap.py       # render the use-case heatmap from usecases.yaml axes
├── post-mr-comment.sh        # advisory MR comment
└── tests/                    # differ unit tests against synthetic before/after pairs

.gitlab/
├── merge_request_templates/rubric-change.md   # intent capture (§8.1)
└── issue_templates/rubric-change.md           # mirror for issues
.gitlab-ci.yml                # GitLab-only automation (§8)
```

## 10. Build order

1. **`usecases.yaml`** for all 10 fixtures + `coverage-heatmap.py` (proves the matrix; no ATX needed).
2. **`diff-reports.py`** (D1–D5) + `tests/` against the existing `examples/reports/` as test input (no ATX needed).
3. **`golden/`** baselines + `run-fixtures.sh` + `should-run.sh` (§7).
4. **`judge.py`** + prompt (intent-aware), validated on hand-made before/after pairs.
5. **`.gitlab-ci.yml`** + `.gitlab/` templates (§8), advisory.

All work lands on **GitLab `feat/harness`**; GitHub receives mirrored content once a batch is stable (no GitHub automation).

## 11. Non-goals / deferred
- Scoring the custom TDs (out of scope this cycle).
- Blocking gates (advisory-only for now).
- Auto-refreshing golden baselines (manual "baseline update" MR).
- GitHub Actions / any non-GitLab automation.

## 12. Verified report field paths (differ contract)

The differ (`diff-reports.py`) must handle these real-artifact quirks (deep scan of `examples/reports/full-analysis/`, 2026-07-28):
- **Findings array key differs by scope:** portfolio findings add `repo_name`; **portfolio MOD drops `description`/`gap`/`recommendation`** (leaner than per-repo MOD); per-repo ARA nests `native_severity`/`safety_impact` under `ara_metadata`, while portfolio ARA promotes them to top level. Match on `(repo_name, question_id)`.
- **Pathways:** per-repo uses `status`; portfolio uses `portfolio_status`. `triggering_questions[]` is top-level per-repo but nested under each `contributing_repos[]` element in portfolio.
- **Distributions differ in shape:** ARA `readiness_distribution` = `{count, percentage}` objects; MOD `tier_distribution` and `score_band_distribution` = flat integers.
- **D5 category field name differs:** per-repo MOD `categories[].numeric_score`; portfolio MOD `category_score_averages[].average`. Per-repo score band lives in `categories[].score_rating`; per-finding score in `mod_metadata.internal_score`/`score_label`.
- `evidence` may be `null` or `{file, lines}`, and `lines` itself may be `null`.
- **Filenames:** `<repo>-ara-report.json`, `<repo>-mod-report.json`, `<portfolio>-portfolio-ara-report.json`, `<portfolio>-portfolio-mod-report.json`. Portfolio also identifiable by top-level `assessment_type` + `repositories[]`; per-repo by `repo_name`.
