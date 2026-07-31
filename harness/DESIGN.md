# Change-Impact Harness — Design

> **Status:** Implemented on `feat/harness`. All decisions locked — see [§0](#0-locked-decisions).
> **Scope:** the **4 managed TDs** only (`agentic-readiness-analysis`, `modernization-readiness-analysis`, `portfolio-agentic-readiness-analysis`, `portfolio-modernization-readiness-analysis`). Custom TDs (EBA, BAO, portfolio-BAO, bridge) are out of scope — they are planning/opportunity layers with looser, less-deterministic outputs.

## 0. Locked decisions

| Decision | Choice |
|---|---|
| Scope | 4 managed TDs only |
| Scored dimensions | D1 Findings (ARA+MOD), D2 Tier/readiness label (ARA+MOD), D3 Pathways (MOD), D4 Programs (ARA **and** MOD portfolio), D5 MOD numeric score (band-crossing) |
| D5 drift check | Band-crossing only — flag on `score_rating` band change, not raw numeric wobble |
| Before/after mechanism | **Committed golden reports** — baseline JSON per fixture; MR re-runs only the changed TD's fixtures and diffs vs golden |
| Judge gate | **Advisory MR comment only** — never blocks the pipeline |
| **What the score means** | **Measured accuracy of the regenerated report, 0.0–1.0** — produced by `score-reports.py`, the same scale and same grader used for the committed baseline. The judge does **not** author it; it reads score vs baseline and reports **direction** (`analysis_effect: improves \| neutral \| degrades`). **Not** intent-match — see §6.1 |
| Judge intent input | Contributor intent captured in a GitLab MR-template field (§8.1). Used as **evidence** — it separates signal from nondeterministic noise, and a mismatch lowers confidence and raises a concern — but it does **not** drive the score |
| Trigger model | **Watched-TD deterministic gate** (`should-run.sh`, NOT an LLM). Runs when a change lands under any *watched TD directory* (`definitions/managed/**` SKILL.md + references/); everything else is skipped unless it is a fixture change. The mechanism is generic (`HARNESS_TD_PATHS`); the config is the 4 managed TDs. Manual `harness:full` for a full re-baseline. LLM is spent only at the *end* (judge). |
| What contributors edit | Contributors edit the **TD definitions themselves** — `definitions/managed/<td>/SKILL.md` + `references/` — which ARE git-visible. The harness runs the *edited* TD via `atx custom def exec` (see §7), so the diff under review is exactly what gets tested. The published managed TD on AWS Transform Continuous Modernization stays authoritative until an approved change is published there. |
| CI platform | **Runs on GitLab ONLY** — AWS access via the **AWS Credential Vendor** on the shared runner fleet (OIDC does NOT work on internal `gitlab.aws.dev` — IAM can't reach it to verify tokens). One CI var `AWS_CREDS_TARGET_ROLE` points at a per-project IAM role in the target AWS account; the runner auto-vends temp creds. GitHub stays **open for contributions** (issue/PR templates kept) but runs **no** automation; content mirrors both ways. |
| Templates | GitHub `.github/ISSUE_TEMPLATE/` kept (contributions welcome there); GitLab adds `.gitlab/` templates that also capture judge **intent** (§8.1). |

## 1. Purpose

Give any contributor **automatic feedback on whether a change they made to a managed TD actually impacts the analysis — and whether that impact is good or bad.**

Two questions the harness answers on every PR/MR:
1. **Did this change do anything?** — Show the concrete delta in analysis output across a representative set of use cases. A TD edit that moves zero findings/pathways is probably a no-op (or a mistake).
2. **Is the change good or bad *for the analysis*?** — An LLM-as-judge scores whether the delta makes the ARA/MOD assessment more or less accurate/useful/safe-to-act-on, and posts an advisory verdict (score + `analysis_effect` + `LGTM` / `needs-work` + `quality_regression` flag + rationale citing specific question/pathway/program IDs), plus up to 3 improvement suggestions.

### 6.1 Why the score measures analysis effect, not intent match

The score originally answered *"does the observed delta match the contributor's stated intent?"* That was well-calibrated but **graded the contributor instead of the analysis**, and it failed in both directions:

- **False positive:** `dropped-questions` — a change described accurately and executed exactly as described, which left the report answering **41 of 43** rubric questions. Intent-match rewards this; it is a coverage regression.
- **False negative:** an edit that silently never applied scored ~15 even though the analysis was **byte-identical** to baseline — nothing was harmed.

The MR !14 shape is the canonical case: intent achieved *perfectly*, and a BLOCKER lost with the readiness tier relaxed as a side effect.

Intent is still supplied and still reported — it is what lets the judge separate real movement from the analysis agent's run-to-run nondeterminism (§6.2), and a mismatch means the contributor may not understand what their edit did. But it is **evidence that adjusts confidence**, not the quantity being measured.

### 6.1.1 There is one score, and the judge does not author it

The fix above was the first half. The second half: the judge used to emit its **own 0–100
score** alongside the scorer's 0.0–1.0 accuracy scale. Two scales for one question meant
the number in an MR comment could not be compared to the number in `SCORES.md` for the
same report, and the judge was authoring a *measurement* it was not positioned to take —
it sees a diff, not the fixture source.

Now `score-reports.py` is the only thing that produces a score. It grades the regenerated
report exactly as it graded the committed baseline (recall-weighted groundedness against
the fixture source; a missed BLOCKER costs far more than a spurious INFO) and the judge
consumes **both** numbers to reason only about **direction**:

| measured move | judge reports |
| --- | --- |
| `delta > threshold` | measured accuracy **improvement** |
| `abs(delta) <= threshold` | **within noise — NOT MEASURED** → `analysis_effect: neutral` |
| `delta < -threshold` | measured accuracy **regression** |

A delta must **exceed** the band, not merely reach it — the comparison is `abs(delta) <=
threshold`. The scores are not continuous: the grader's observed MOD alphabet is `[0.52,
0.62, 0.72, 0.82, 0.88, 0.92]`, whose smallest gap is exactly `0.04` = `NOISE_FLOOR["mod"]`.
Under a strict `<`, one grid step — the smallest move the grader can express — was reported
as a **confirmed regression on 12 of 14 MOD fixtures** (MR !15 published exactly that).
Raising the MOD floor to `2q = 0.08` is *not* the alternative fix: `0.08` exceeds the entire
headroom of a `0.92`-baseline fixture, so it kills 7 rows and re-creates the ARA defect below.

`threshold` is per fixture: `max(2·sd, NOISE_FLOOR)` — measured variance may only ever RAISE
the bar, never lower it below the floor. The floor is **ARA 0.09 / MOD 0.04**
(`score-reports.py: NOISE_FLOOR`), **derived as `2 × median per-fixture stddev`** over
independent re-runs of the analysis on a byte-identical rubric (ARA n=4, MOD n=3 — see
`golden-accuracy-baseline.json`). Re-derive it whenever you re-baseline; a test recomputes it
from the baseline and fails when the constant drifts.

Two retired values, because the floor has been wrong in both directions and each time a green
test pinned it:

- **ARA 0.10 / MOD 0.02** — derived from re-scoring one report tree, which holds the dominant
  variance source (the analysis agent) fixed. Too small: reported dice-rolls as improvements.
- **ARA 0.25** — a real measurement (median sd 0.123) that was never updated after the noise
  fixes and the n=4 ARA re-baseline cut median sd to 0.0455. Too large by ~4× the entire
  observed ARA range (0.825–0.890), which made `within-noise` the *only verdict ARA could
  ever return*. A harness that can only say "not measured" still looks like it is working —
  that is the more dangerous of the two failures.

Consequences worth stating, because each replaced an earlier design:

- **A no-op no longer needs a "mid-band".** There is no band to sit in — the score is
  whatever the report measured, and harmlessness is carried by `analysis_effect: neutral`.
  The old 45–59 neutral band existed only because the judge invented the number.
- **The safety floor does not cap the score.** A tier-material alert forces
  `verdict: needs-work` and `analysis_effect: degrades`, but capping a measured number
  would make `verdict.json` disagree with `SCORES.md` about the same report. The hold rides
  on the judgement fields, which can carry it.
- **No measurement ⇒ validation is not possible.** A missing score is reported as a harness
  error to fix (`verdict: needs-work`, naming `score-reports.py`), never a substituted
  number and never a quiet pass.

The asymmetry survives as a *judgement*, not arithmetic: a change making the analysis
stricter outranks one making it more permissive, because only the latter can present a
system as safer than the evidence supports.

`calibrate-judge.py` was **deleted** along with the 0–100 axis. It existed to check that a
judge-authored score was *ordered* (a worse change scoring lower than a better one) — a
question that only makes sense when a model invents the number. A measurement's ordering is
a property of the scorer, and `test_score_reports.py` plus the deterministic checks cover
that. The semantics the calibration ladder used to protect are now pinned directly in
`test_judge.py`: an unmet intent must leave the score **exactly** equal (it was the
`no-op-expected` / `no-op-unexpected` pair, previously 95/15, then 50/47, now identical by
construction), the floor must pass a measured score through untouched in both directions,
and the unscored path must refuse to return LGTM.

## 2. What the managed TDs emit (the contract the harness scores against)

Grounded in the real reports under `harness/golden/` (the committed baseline).

> **All four report shapes below are verified against the real artifacts in `harness/golden/` (the committed baseline, regenerated from the edited managed TDs).**

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

The 10 repos in `harness/fixtures/portfolio/` are a genuinely diverse fixture set. Confirmed profiles:

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

Plus `harness/fixtures/monolith/` (PHP) already used in analysis runs.

**`usecases.yaml` structure (per fixture):**
```yaml
- id: legacy-shipping-api
  path: harness/fixtures/portfolio/legacy-shipping-api
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

> **The TD definitions ARE the git-visible surface (verified 2026-07-28).** A contributor's change lands on `definitions/managed/<td>/SKILL.md` + its `references/` — full, editable definitions in *this* repo, NOT hidden behind the AWS Transform service. A `git diff` of `definitions/managed/**` therefore sees the exact change under review. The harness runs that edited definition directly via `atx custom def exec` (§7), so "before" is the published managed TD's output and "after" is the *proposed* TD's output. Once a change is published to Continuous Modernization, an `atx ct` parity path can replace the custom-exec generator. This drives the trigger model below.

**Trigger model — watched-TD deterministic gate (GitLab only for now):** the gate is a **deterministic path check, not an LLM**. `should-run.sh` runs `git diff --name-only` against the base and **RUNs when any changed path lives under a watched TD directory** — `definitions/managed/<td>/` (its `SKILL.md` and `references/`). The set of watched directories is configurable via `HARNESS_TD_PATHS` (colon-separated); the default is the 4 managed TDs this harness owns. To automate another TD — managed OR custom, wherever it lives — add its path; no other code change is needed. A watched-TD match RUNs even for a `.md` file, because `SKILL.md` (a `.md` file the generic docs denylist would otherwise skip) is exactly the thing we automate for. Everything not under a watched TD is skipped unless it is a fixture change. No model decides whether to run (that would be slow, non-deterministic, costly per MR); the LLM is spent **only at the judge step (§6)**. Entry points:
1. **MR pipeline (GitLab)** — watched-TD gate as above. The primary contribution path.
2. **Manual `harness:full` run** — a maintainer wants a full re-baseline (e.g. after publishing an approved change), or to force a full run. Fired from the GitLab "Run pipeline" button.
3. **Skip** — when no changed path is under a watched TD (and no fixture changed). Job stops cleanly, no `atx`, no cost.

```
should-run.sh   ── deterministic git-diff; run UNLESS all-denylisted ──▶  run │ skip   (no LLM)
      │ run
      ▼
run-fixtures ─▶ diff-reports.py ─▶ judge.py                            ◀── the ONLY LLM, at the end
```

> **TD-as-contribution:** the TD definition itself (`SKILL.md` + `references/`) is edited under `definitions/managed/<td>/`, so "add `AUTH-Q9`" or "re-score `INF-Q11`" is a normal reviewable MR the harness runs against by publishing the edited folder as a custom def and exec'ing it (§7). The published managed TD on Continuous Modernization remains authoritative; an approved change is published there separately (the repo is the *proposal + test* surface, Continuous Modernization is the *deploy* surface). All of this runs on **GitLab only** for now; GitHub stays open for issues/PRs but triggers nothing.

```
0. Gate                              should-run.sh → run | skip (watched-TD path check)
1. Resolve scope                     HARNESS_CHANGED_TD from the gate → a TD edit is portfolio-wide → all fixtures
2. Select applicable fixtures        from usecases.yaml (--changed-only subset, or --all on manual full run)
3. Produce after-reports             publish edited TD as custom def + atx custom def exec on selected fixtures  [see §7]
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

- **Input:** `impact.json` (the delta) + `compare.json` (the **measured** accuracy of the regenerated reports vs the committed baseline, with a per-fixture noise threshold) + the fixture `expectations` + the raw diff of the changed file(s) **+ the contributor's INTENT** (see below).
- **Intent is evidence, not a score driver.** The judge reads the delta *against what the contributor said they were trying to do* — a change that adds 40 findings reads differently under "tighten AUTH scoring" than under "fix a typo in a recommendation string." But intent cannot move the score, because the score is a measurement (`compare.json`); a mismatch lowers **confidence** and raises a concern instead. Intent is captured in a **structured MR-template field** (§8.1) and passed as `intent: {what, why, expected_impact}`.
- **Prompt shape:** "You are reviewing a proposed change to an AWS Transform analysis TD. The contributor's stated intent is: {intent}. Here is the observed delta (before = published TD output, after = proposed TD output). (1) Does the delta match the stated intent? (2) Is the change a quality regression, or can it be improved?" The judge is instructed to cite `question_id`s / `pathway.id`s / program acronyms, and to flag **intent mismatch**, **no-op** (they intended a change but delta is empty), and **quality regression** (the delta plausibly makes the analysis worse — e.g. a tier now contradicts its own blocker/severity counts, a pathway fires when the repo can't trigger it).
- **Output (structured):**
  ```jsonc
  {
    // MEASURED by score-reports.py, not authored by the judge. Same 0.0-1.0 scale and
    // same grader as the committed baseline, so the two are directly comparable.
    "score": 0.842,               // regenerated report accuracy (mean over fixtures scored)
    "baseline_score": 0.815,      // committed baseline mean for the SAME fixtures
    "scored": true,               // false => the change COULD NOT BE VALIDATED (see below)
    "accuracy_verdicts": {        // per fixture, already noise-thresholded by the scorer
      "legacy-shipping-api:ara": { "score": 0.88, "baseline": 0.82, "delta": 0.06,
                                   "threshold": 0.09, "verdict": "not-measured",
                                   "basis": "noise-floor" }
    },
    // JUDGED. Direction, not magnitude.
    "analysis_effect": "improves" | "neutral" | "degrades",
    "verdict": "LGTM" | "needs-work",
    "intent_match": "aligned" | "partial" | "mismatch",   // delta vs stated intent
    "rationale": "…cites AUTH-Q5, move-to-cloud-native, etc.…",
    "concerns": [ { "dimension": "D3", "detail": "…" } ],
    "quality_regression": false,  // true if the delta plausibly makes the analysis worse
    "safety_hold": false,         // tier-material alert — independent of the score
    "suggestions": [ "…up to 3 concrete, actionable improvements…" ],
    "no_op_warning": false        // true if intent claimed a change but delta is empty
  }
  ```
  `scored: false` (no `compare.json`, or nothing in it was scorable) is **not** a neutral
  result — it means no measurement was taken, so the change cannot be validated. Both the
  LLM and heuristic paths force `verdict: needs-work` and raise a concern naming
  `score-reports.py`, and the MR comment says "could not be validated". Neither path is
  permitted to substitute a placeholder number.
- **Gate policy:** **advisory only.** The judge posts the verdict + score as an MR comment; it **never fails the pipeline.** Humans decide. (Chosen this session; can tighten to regression-blocking later.)
- **Backend:** Bedrock (Anthropic Claude) via boto3 using the creds the AWS Credential Vendor already vends into the job. If Bedrock is unavailable (local dev, no creds), `judge.py` falls back to a deterministic heuristic so the pipeline still emits a usable `verdict.json` offline — the heuristic reports movement and defers the quality read to the LLM run rather than guessing correctness. Judge runs against the report JSON, not the HTML/MD renders.
- **Schema guardrail (distinct axis):** alongside the semantic judge, `validate-contract.py` structurally validates every collected report against the JSON contract (`--validate` on `run-fixtures.sh`, plus an offline `tests/test_validate_contract.py` shape-fixture suite). Semantic quality is the judge's job; structural conformance is the guardrail's — a change that emits off-contract JSON is caught deterministically, no LLM needed.

## 7. Before/after mechanism — committed golden reports (decided)

**Chosen:** committed golden reports.

- `harness/golden/` holds one baseline report JSON per fixture, per applicable TD (the "before"). **The golden baseline is generated from the MODIFIED TDs in this repo** (via `run-fixtures.sh --all --write-golden`), so it is the true "current proposal" surface until the TDs publish to Continuous Modernization — at which point `atx ct` can supply the published "before".
- **Generator = `atx custom def exec` on the edited TD** (not `atx ct`). `run-fixtures.sh` publishes each `definitions/managed/<td>/` folder as a custom def (name suffixed `-harness` so it never clobbers the managed name), execs it per fixture, collects the report JSON, and (with `--validate`) contract-checks each report as it lands. `atx ct` runs the OLD published defs and can't see the edit under review — hence custom-exec. See the header of `run-fixtures.sh`.
- On a triggered run: `should-run.sh` decides run/skip → `run-fixtures.sh --changed-only` produces the "after" reports → `diff-reports.py` diffs after vs golden → `impact.json`.
- A TD edit is portfolio-wide, so `--changed-only` analyzes all fixtures; a bare fixture edit narrows the set.
- Golden files double as **regression fixtures**: an unexpected diff vs golden is itself a signal.
- **Refreshing goldens:** intentional TD changes will legitimately move the baseline. Refresh via a dedicated "baseline update" MR (`run-fixtures.sh --all --write-golden --validate`), reviewed on its own so baseline churn never hides inside a feature MR.

Rejected: *live baseline + rerun* (every MR runs full ATX twice — too slow, double AWS cost); *judge-only, no rerun* (no true delta — weakest signal).

## 8. GitLab CI wiring (`.gitlab-ci.yml`) — **GitLab-only automation**

**Automation lives ONLY on GitLab.** GitHub stays open for contributions — the `.github/` dir keeps issue/PR templates so people can file and propose there — but carries **no** GitHub Actions/workflows. All analysis runs on GitLab, where the AWS credentials live. This keeps a single source of CI truth and avoids double AWS cost. Content mirrors between the two remotes; automation does not.

Jobs (all advisory — `allow_failure: true`, never blocks). See the real `.gitlab-ci.yml` for the full before_script (atx install + Credential Vendor identity check):

```yaml
stages: [gate, test, analyze, judge]

# Schema guardrail (offline, no AWS) — the STRUCTURAL axis, distinct from the judge.
harness:contract-tests:
  stage: test
  rules: [ {if: '$CI_PIPELINE_SOURCE == "merge_request_event"'}, {if: '$CI_PIPELINE_SOURCE == "web"'} ]
  script:
    - python3 -m pytest harness/tests/ -q   # whole suite: contract shapes, differ, SKILL.md parse
  allow_failure: true

# Entry 1: MR pipeline — watched-TD gate → run edited TD → diff → judge → comment
harness:impact:
  stage: analyze
  rules: [ {if: '$CI_PIPELINE_SOURCE == "merge_request_event"'} ]
  script:
    - harness/should-run.sh || exit 0                        # gate: skip if no watched-TD change (§5)
    - harness/run-fixtures.sh --changed-only --validate      # custom-def exec → after-reports + contract check [§7]
    - harness/diff-reports.py --baseline harness/golden --after "$AFTER_DIR" -o impact.json
    - harness/judge.py --impact impact.json --intent "$CI_MERGE_REQUEST_DESCRIPTION" > verdict.json
    - harness/post-mr-comment.sh verdict.json                # advisory comment, non-blocking
  allow_failure: true

# Entry 2: manual/web run — full re-baseline / forced run
harness:full:
  stage: analyze
  rules: [ {if: '$CI_PIPELINE_SOURCE == "web"'} ]            # "Run pipeline" button
  variables: { CHANGED_TD: "", RUN_SCOPE: "all", RUN_INTENT: "" }
  script:
    - harness/run-fixtures.sh --scope "$RUN_SCOPE" --td "$CHANGED_TD" --validate
    - harness/diff-reports.py --baseline harness/golden --after "$AFTER_DIR" -o impact.json
    - harness/judge.py --impact impact.json --intent "$RUN_INTENT" > verdict.json
    - harness/post-mr-comment.sh verdict.json || cat verdict.json
  allow_failure: true
```

Requires AWS access on the GitLab runner for the `atx` step (analysis-scoped; a developer-owned AWS account for now). Auth is the **AWS Credential Vendor** on the shared fleet — set the single CI var `AWS_CREDS_TARGET_ROLE` to a per-project IAM role whose trust policy allows the GitLab runner fleet's jump role to assume it, gated by `aws:PrincipalTag/GitLab:{Project,Group}`. The jump-role ARN is in `harness/README.md`. The runner injects temp `AWS_ACCESS_KEY_ID/_SECRET_ACCESS_KEY/_SESSION_TOKEN` automatically — no OIDC, no static keys. See `harness/README.md` for the role setup.

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
├── golden/                   # committed baseline reports per fixture, from the MODIFIED TDs (§7)
├── should-run.sh             # gate: watched-TD run|skip (HARNESS_TD_PATHS) (§5)
├── run-fixtures.sh           # publish edited TD as custom def + atx custom def exec (§7)
├── diff-reports.py           # D1–D5 delta → impact.json (§5)
├── judge.py                  # LLM-as-judge (+ intent, quality-regression, suggestions) → verdict.json (§6)
├── validate-contract.py      # schema guardrail: structural JSON-contract check (§6)
├── coverage-heatmap.py       # render the use-case heatmap from usecases.yaml axes
├── post-mr-comment.sh        # advisory MR comment
└── tests/
    ├── test_validate_contract.py   # offline shape-fixture suite for the schema guardrail
    └── …                            # differ unit tests against synthetic before/after pairs

.gitlab/
├── merge_request_templates/rubric-change.md   # intent capture (§8.1)
└── issue_templates/rubric-change.md           # mirror for issues
.gitlab-ci.yml                # GitLab-only automation (§8)
```

## 10. Build order

1. **`usecases.yaml`** for all 10 fixtures + `coverage-heatmap.py` (proves the matrix; no ATX needed).
2. **`diff-reports.py`** (D1–D5) + `tests/` against the committed `harness/golden/` baseline as test input (no ATX needed).
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

The differ (`diff-reports.py`) must handle these real-artifact quirks (observed across the `harness/golden/` baseline):
- **Findings array key differs by scope:** portfolio findings add `repo_name`; **portfolio MOD drops `description`/`gap`/`recommendation`** (leaner than per-repo MOD); per-repo ARA nests `native_severity`/`safety_impact` under `ara_metadata`, while portfolio ARA promotes them to top level. Match on `(repo_name, question_id)`.
- **Pathways:** per-repo uses `status`; portfolio uses `portfolio_status`. `triggering_questions[]` is top-level per-repo but nested under each `contributing_repos[]` element in portfolio.
- **Distributions differ in shape:** ARA `readiness_distribution` = `{count, percentage}` objects; MOD `tier_distribution` and `score_band_distribution` = flat integers.
- **D5 category field name differs:** per-repo MOD `categories[].numeric_score`; portfolio MOD `category_score_averages[].average`. Per-repo score band lives in `categories[].score_rating`; per-finding score in `mod_metadata.internal_score`/`score_label`.
- `evidence` may be `null` or `{file, lines}`, and `lines` itself may be `null`.
- **Filenames:** `<repo>-ara-report.json`, `<repo>-mod-report.json`, `<portfolio>-portfolio-ara-report.json`, `<portfolio>-portfolio-mod-report.json`. Portfolio also identifiable by top-level `assessment_type` + `repositories[]`; per-repo by `repo_name`.
