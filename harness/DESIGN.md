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
| CI platform | **GitLab first**, then sync to GitHub (harness dev flow is GitLab → GitHub) |

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

## 5. Change → impact flow (per PR/MR)

```
1. Detect changed managed TD(s)      git diff --name-only vs base → which definitions/managed/* changed
2. Select applicable fixtures        from usecases.yaml (all, or a --changed-only subset)
3. Produce after-reports             run the changed TD via atx on selected fixtures  [see §7]
4. Diff vs baseline                   compute per-dimension delta (D1–D5)
5. Judge                              LLM-as-judge consumes {delta, expectations, changed-TD diff}
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

- **Input:** `impact.json` (the delta) + the fixture `expectations` + the raw diff of the changed TD(s).
- **Prompt shape:** "You are reviewing a change to a managed Transformation Definition. Here is the change, the use cases it was run against, the expected behavior, and the observed delta. Score the change and decide LGTM / needs-work." Rubric explicitly instructs it to cite `question_id`s / `pathway.id`s.
- **Output (structured):**
  ```jsonc
  {
    "score": 0-100,
    "verdict": "LGTM" | "needs-work",
    "rationale": "…cites AUTH-Q5, move-to-cloud-native, etc.…",
    "concerns": [ { "dimension": "D3", "detail": "…" } ],
    "no_op_warning": false
  }
  ```
- **Gate policy:** **advisory only.** The judge posts the verdict + score as an MR comment; it **never fails the pipeline.** Humans decide. (Chosen this session; can tighten to regression-blocking later.)
- **Implementation note:** reuse the same LLM-as-judge pattern the orchestrator already relies on. Judge runs against the report JSON, not the HTML/MD renders.

## 7. Before/after mechanism — committed golden reports (decided)

**Chosen:** committed golden reports.

- `harness/golden/` holds one baseline report JSON per fixture, per applicable TD (the "before").
- On MR: `detect-changed-tds.sh` finds which managed TD(s) changed → `run-fixtures.sh --changed-only` re-runs **only that TD's** applicable fixtures via `atx` (the "after") → `diff-reports.py` diffs after vs golden → `impact.json`.
- Most fixtures are **not** re-analyzed each MR — only the ones the change touches — so MR pipelines stay fast.
- Golden files double as **regression fixtures**: an unexpected diff vs golden is itself a signal.
- **Refreshing goldens:** intentional rubric changes will legitimately move the baseline. Refresh via a dedicated "baseline update" MR (`run-fixtures.sh --all --write-golden`), reviewed on its own so baseline churn never hides inside a feature MR.

Rejected: *live baseline + rerun* (every MR runs full ATX twice — too slow, double AWS cost); *judge-only, no rerun* (no true delta — weakest signal).

## 8. GitLab CI wiring (`.gitlab-ci.yml`, MR pipeline)

Per Track B, automation lands on GitLab first (GitLab = mirror of GitHub, both at the same `main`). Sketch:

```yaml
harness:impact:
  rules: [ { if: '$CI_PIPELINE_SOURCE == "merge_request_event"' } ]
  script:
    - harness/detect-changed-tds.sh                    # → changed_tds
    - harness/run-fixtures.sh --changed-only           # atx runs → after-reports  [§7]
    - harness/diff-reports.py --baseline golden/ ...    # → impact.json
    - harness/judge.py impact.json > verdict.json      # LLM-as-judge
    - harness/post-mr-comment.sh verdict.json          # advisory comment, non-blocking
  allow_failure: true                                   # advisory: never blocks the MR
```

Requires AWS creds available to the GitLab runner for the `atx` step (scoped to analysis only).

## 9. Proposed directory layout

```
harness/
├── DESIGN.md                 # this file
├── usecases.yaml             # fixture matrix + axes + expectations (§4)
├── golden/                   # committed baseline reports per fixture (§7, if approved)
├── detect-changed-tds.sh     # which managed TDs a diff touched
├── run-fixtures.sh           # drive atx over selected fixtures
├── diff-reports.py           # D1–D5 delta → impact.json (§5)
├── judge.py                  # LLM-as-judge → verdict.json (§6)
├── coverage-heatmap.py       # render the use-case heatmap from usecases.yaml axes
└── post-mr-comment.sh        # advisory MR comment
```

## 10. Build order (next sessions)

1. **`usecases.yaml`** for all 10 fixtures + `coverage-heatmap.py` (proves the matrix; no ATX needed).
2. **`diff-reports.py`** (D1–D5) against the existing `examples/reports/` as test input (no ATX needed).
3. **`golden/`** baselines + `run-fixtures.sh` + `detect-changed-tds.sh` (§7).
4. **`judge.py`** + prompt, validated on hand-made before/after pairs.
5. **`.gitlab-ci.yml`** MR job, advisory.

All work is committed and pushed to **GitLab `main` first**; GitHub `origin/main` is fast-forwarded to match once a batch is stable.

## 11. Non-goals / deferred
- Scoring the custom TDs (out of scope this cycle).
- Blocking gates (advisory-only for now).
- Auto-refreshing golden baselines (manual "baseline update" MR).
