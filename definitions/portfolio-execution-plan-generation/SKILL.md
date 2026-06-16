---
name: portfolio-execution-plan-generation
description: Generate portfolio-level modernization execution plan from aggregated MODA report
version: 0.1.0
---

## Name

Portfolio Execution Plan Generation

## Objective

Generate a comprehensive portfolio-level modernization execution plan by consuming the portfolio MODA report (the aggregated output of the `portfolio-modernization-readiness-analysis` TD) and producing ONE holistic engagement-level roadmap. The portfolio MODA report already aggregates per-service scores, triggered pathways, dependency maps, and remediation roadmaps — this TD focuses purely on **planning**: converting that aggregated analysis into deduplicated work streams, cross-service dependency ordering, phased timelines, risk registers, cost estimations, and success metrics — enabling coordinated execution planning across the entire service estate.

## Summary

This transformation uses a **layered input approach**: the portfolio MODA report (`{portfolio-name}-mod-portfolio-report.json`) as its primary input, with optional drill-down into individual per-service MODA reports only when deeper granularity is needed for a specific work stream. It does NOT re-evaluate codebases or re-aggregate per-service data — that work is already done by the portfolio MODA TD. Instead, it:

1. **Reads the portfolio MODA report** (primary) from `./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json` — sufficient for 90% of planning
2. **Optionally reads per-service MODA reports** (secondary) from `./services/{name}/modernization-readiness-analysis/{slug}-mod-report.json` — only for decomposition strategy details, specific question scores, or evidence file references
3. **Extracts triggered pathways** from the portfolio report's `pathways[]` array (already aggregated with `contributing_repos` per pathway)
3. **Generates deduplicated work streams** — ONE work stream per unique triggered pathway (not per service), listing all affected services within each stream
4. **Establishes shared infrastructure tasks** for pathways affecting multiple services
5. **Maps cross-service dependencies** between work streams (e.g., DevOps foundation before Cloud Native decomposition)
6. **Produces a phased timeline** with parallelization strategy based on risk tolerance and dependency ordering
7. **Identifies risks** at the engagement level (cross-service integration complexity, team capacity spread, timeline feasibility)
8. **Estimates effort and cost** at the engagement level with three-point estimates (optimistic / expected / pessimistic)
9. **Defines decision points** where customer input is required before proceeding

The output is a **four-artifact bundle**:
- `{portfolio-name}-portfolio-exec-plan.md` — narrative execution plan
- `{portfolio-name}-portfolio-exec-plan.json` — canonical machine-readable contract
- `{portfolio-name}-portfolio-exec-plan.html` — self-contained HTML visualization
- `{portfolio-name}-portfolio-exec-plan.metadata.json` — version sidecar

**What this TD does NOT do:**
- Re-run MODA scoring (consumes portfolio MODA output as-is)
- Re-aggregate per-service reports (the portfolio MODA report already does this — per-service reports are only used for optional enrichment)
- Ask interactive questions (all context provided upfront via `additionalPlanContext`)
- Generate Word documents or CSV files (uses standard four-artifact contract)
- Execute or modify source code
- Make technology decisions — it recommends options with tradeoffs, customer decides
- Produce per-service execution plans — it produces ONE portfolio-level plan covering ALL services

**Key differentiator from per-service execution plan TD:** This TD operates at the portfolio level with a layered input model. It uses the already-aggregated portfolio MODA report as its primary input (90% of planning needs) and only drills into individual per-service reports for enrichment when deeper detail is needed. It focuses purely on planning — deduplicating shared modernization work (e.g., "Move to Modern DevOps" triggered by 3 services becomes ONE work stream with shared infrastructure tasks plus per-service implementation tasks), identifying cross-service dependencies, and estimating engagement-level cost rather than per-service cost.

## Entry Criteria

- **Required:** A portfolio MODA report JSON exists at `./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json`
- The portfolio report follows the expected schema: `metadata` with `portfolio_name`, `assessment_date`, `services_assessed`; `pathways[]` array with `portfolio_status`; `repositories[]` array with per-service scores and triggered pathways
- The portfolio report was produced by the `portfolio-modernization-readiness-analysis` TD and contains at least 2 assessed services
- **Optional:** Individual per-service MODA reports at `./services/{name}/modernization-readiness-analysis/{slug}-mod-report.json` — used for enrichment only; the TD degrades gracefully if these are unavailable
- Write permissions exist to create the output directory and portfolio artifact bundle (MD, JSON, HTML, and metadata.json)
- The analysis operates in **read-only mode** — it will not modify any source code, configuration, or infrastructure
- Stay on the current branch — do not create, switch, or checkout any git branches

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning discovery, read the portfolio execution context from `additionalPlanContext` to extract team constraints, timeline requirements, and engagement parameters.

#### 0.1 Read Portfolio Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `portfolio_name` | string | No | derived from directory | Identifier for the portfolio. Used to name the output bundle. If absent, derive from the parent directory name or MODA report metadata. |
| `team_size` | integer | No | 5 | Number of engineers available for modernization work. Affects effort-to-calendar-time conversion and parallelization capacity. |
| `timeline_constraint` | string | No | — | Hard deadline or desired completion window (e.g., "6 months", "12 months", "Q4 2026"). Used to assess feasibility. |
| `budget_constraint` | string | No | — | Budget envelope or cost sensitivity (e.g., "minimize cost", "$500K total", "no constraint"). |
| `compliance_requirements` | string[] | No | — | Regulatory/compliance frameworks that must be maintained during migration (e.g., ["PCI-DSS", "SOC2", "HIPAA"]). Generates compliance-specific risks and validation gates. |
| `availability_requirement` | string | No | — | Uptime SLA during migration (e.g., "99.9%", "99.95%", "zero-downtime required"). Affects migration strategy (big-bang vs incremental). |
| `risk_tolerance` | enum | No | `"moderate"` | One of: `conservative`, `moderate`, `aggressive`. Controls parallelism of work streams, timeline compression, and validation gate density. |
| `existing_capabilities` | string | No | — | What the team already has (e.g., "Strong K8s, Terraform, CI/CD experience"). Affects training work stream generation and effort multipliers. |
| `priority_pathways` | string[] | No | all triggered | Subset of MODA pathways to plan for. If omitted, plans for ALL triggered pathways across all services. |
| `excluded_pathways` | string[] | No | — | MODA pathways to explicitly exclude from planning. |
| `preferences` | object | No | — | Technology preferences (same format as MODA: `prefer` and `avoid` arrays). Steers recommendations but does not change pathway logic. |
| `service_inventory` | object[] | No | — | List of services with metadata (name, path, priority, classification_tier). Used to enrich service context. |
| `dependency_overrides` | object[] | No | — | Explicit cross-service dependency declarations. Each entry: `source`, `target`, `type`, `description`. |

**Example `additionalPlanContext`:**

```yaml
additionalPlanContext: |
  portfolio_name: "ecommerce-platform-v2"
  team_size: 5
  timeline_constraint: "12 months"
  budget_constraint: "$800K including training and infrastructure"
  compliance_requirements: ["PCI-DSS", "SOC2"]
  availability_requirement: "99.95%"
  risk_tolerance: "moderate"
  existing_capabilities: "Java/Spring, basic Docker, some CI/CD, no Kubernetes"
  preferences:
    prefer: ["eks", "aurora-postgresql", "graviton"]
    avoid: ["lambda", "dynamodb"]
  service_inventory:
    - name: "order-service"
      path: "../order-service"
      priority: "P0"
      classification_tier: "Remediation Required"
    - name: "catalog-service"
      path: "../catalog-service"
      priority: "P1"
      classification_tier: "Pilot-Ready"
```

#### 0.2 Apply Defaults

- **`team_size`** → Default 5 if absent
- **`risk_tolerance`** → Default "moderate" if absent
- **`timeline_constraint`** → No default. If absent, timeline is unconstrained and feasibility is always Green/Yellow.
- **`compliance_requirements`** → No default. If absent, no compliance-specific risks are generated.
- **`existing_capabilities`** → No default. If absent, assume moderate capability and include a training decision point.

#### 0.3 How Context Fields Are Used

- **`team_size`** → Effort-to-calendar conversion (person-weeks / team_size x 0.7 allocation = calendar weeks). Also scales cost estimation.
- **`risk_tolerance`** → Controls parallelization strategy: `conservative` = sequential execution, no parallel groups; `moderate` = parallel independent streams, sequential dependent ones; `aggressive` = maximum parallelism, compressed timelines, reduced effort multipliers.
- **`timeline_constraint`** → Compared against calculated timeline to determine feasibility (Green/Yellow/Red). If infeasible, recommendations include scope reduction or team expansion.
- **`compliance_requirements`** → Generates additional risks in the Compliance category. Adds validation gates and dual-running requirements to affected work streams.
- **`existing_capabilities`** → When absent or indicating gaps, generates training decision points. When team has strong capabilities, reduces effort multipliers.


### Step 1: Discover and Load MODA Reports (Layered Input)

This TD uses a **layered input approach**:

| Layer | Source | Purpose | When Used |
|-------|--------|---------|-----------|
| **Primary** | Portfolio MODA report | Aggregated pathways, service tiers, cross-cutting themes, priority weighting | Always — sufficient for 90% of planning |
| **Secondary** | Individual per-service MODA reports | Detailed evidence files, specific question scores, decomposition strategy details | Only when a work stream needs deeper granularity |

The TD does NOT re-aggregate pathways across services — that work is already done in the portfolio MODA report.

#### 1.1 Load Portfolio MODA Report (Primary Input)

Read the portfolio MODA report from the expected path:

```
./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json
```

If `portfolio_name` is specified in `additionalPlanContext`, use it to construct the filename. Otherwise, look for the single `*-mod-portfolio-report.json` file in the directory.

**Validation:**
- Is a valid JSON document
- Has `metadata` with `portfolio_name`, `assessment_date`, `services_assessed` (integer >= 2)
- Has `pathways[]` array with entries containing `id` and `portfolio_status`
- Has `repositories[]` array with entries containing `repo_name`, `overall_score`, `classification`

**Terminate with a clear error if the portfolio MODA report is missing or invalid.**

**Extract from the portfolio report:**

- **Portfolio metadata** — `metadata.portfolio_name`, `metadata.assessment_date`, `metadata.services_assessed`
- **Triggered pathways** — entries in `pathways[]` where `portfolio_status == "Triggered"`, collecting `id`, `contributing_repos[]`, `priority`, and `effort`
- **Per-service data** — from `repositories[]`: `repo_name`, `overall_score`, `classification.tier`, `pathways_triggered[]`
- **Dependency map** — from `dependency_map` if present (cross-service relationships already identified by portfolio MODA)
- **Remediation roadmap** — from `remediation_roadmap` if present (pre-computed phasing from portfolio MODA)

#### 1.2 Load Per-Service MODA Reports (Secondary/Enrichment Input)

Only drill into individual per-service reports when a work stream requires deeper granularity that the portfolio report does not provide. Per-service reports are located at:

```
./services/{service-name}/modernization-readiness-analysis/{slug}-mod-report.json
```

**When to read a per-service report:**
- The work stream involves Cloud Native decomposition and needs detailed `decomposition_strategy` (strangler-fig patterns, bounded contexts, migration sequence)
- Effort estimation requires specific question scores (e.g., INF-Q11 score to determine DevOps maturity baseline)
- A task's `moda_trace` needs precise evidence file references for acceptance criteria
- The portfolio report's `repositories[].pathways_triggered[]` lacks detail on triggering questions or gap severity

**What NOT to do with per-service reports:**
- Do NOT re-aggregate pathways (the portfolio report already has the canonical `pathways[]` with `contributing_repos`)
- Do NOT use per-service reports to override portfolio-level pathway status or priority
- Do NOT fail if a per-service report is unavailable — degrade gracefully using portfolio-level data only

**Extract from per-service reports (when loaded):**
- `decomposition_strategy` — detailed migration approach for Cloud Native pathway
- `categories[].questions[]` — specific question IDs and scores for effort calibration
- `evidence_files[]` — concrete file references for task acceptance criteria
- `top_gaps[]` — detailed gap descriptions for task decomposition

#### 1.3 MODA Currency Check

Calculate age from portfolio report's `metadata.assessment_date`. If the portfolio report is older than 90 days, note this in the plan's assumptions: "All MODA reports reflect current state (within 90 days)" — with a caveat if stale. Also check per-repository analysis dates if available in `repositories[].metadata.analysis_date`.


### Step 2: Extract Pathway-to-Services Map

#### 2.1 Build Pathway-to-Services Map

From the portfolio report's `pathways[]` array (already aggregated by the portfolio MODA TD):
- For each pathway where `portfolio_status == "Triggered"`, extract `contributing_repos[].repo_name` as the list of affected services
- Identify shared pathways (contributing_repos length >= 2)
- Identify single-service pathways (contributing_repos length == 1)

#### 2.2 Identify Services Without Work

Services in `repositories[]` with empty `pathways_triggered[]` are noted in the executive summary as "services_no_action" and excluded from work stream generation.

#### 2.3 Deduplication Principle

**Critical rule:** Each unique triggered pathway produces exactly ONE work stream, regardless of how many services trigger it. A pathway triggered by 3 services produces one work stream with 3 services listed — NOT 3 separate work streams. The portfolio MODA report already enforces this deduplication at the pathway level.


### Step 3: Generate Work Streams

For each unique triggered pathway (filtered by `priority_pathways` / `excluded_pathways`), generate a single work stream.

#### 3.1 Work Stream Structure

Each work stream contains:

| Field | Description |
|-------|-------------|
| `id` | Sequential identifier (WS-01, WS-02, ...) |
| `name` | Maps to pathway name (e.g., "Move to Cloud Native") |
| `pathway` | Pathway ID (e.g., "move-to-cloud-native") |
| `services` | All service IDs that trigger this pathway |
| `objective` | Concrete outcome when complete — includes all affected services |
| `prerequisites` | Other work stream IDs that must complete first |
| `effort_weeks` | Three-point estimate: optimistic, expected, pessimistic |
| `risk_level` | High / Medium / Low |
| `phases` | Ordered execution phases with tasks |
| `success_criteria` | Measurable outcomes confirming completion |

#### 3.2 Task Decomposition

Within each work stream, decompose into tasks at 1-2 week (1-10 day) granularity:

- Each task has: `id`, `description`, `effort_days` (1-10), `service` (which service or "shared"), `dependencies` (other task IDs), `acceptance_criteria`, `moda_trace` (traceability to source MODA finding)
- Task IDs are globally unique across all work streams
- Every task must specify which service it applies to (or "shared" for cross-cutting infrastructure)

#### 3.3 Shared Infrastructure Tasks

For work streams affecting multiple services (shared pathways):
- Generate a "shared" infrastructure task as the first task
- This task establishes common patterns, templates, and infrastructure
- All per-service tasks depend on the shared task
- Example: "Establish shared Move to Modern DevOps infrastructure and patterns for all affected services"

#### 3.4 Cross-Stream Dependencies (Prerequisites)

Map dependencies between work streams based on pathway ordering:
- "Move to Modern DevOps" is typically prerequisite for "Move to Cloud Native" and "Move to Containers"
- "Move to Containers" typically precedes "Move to Cloud Native"
- "Move to Managed Databases" can often run in parallel with containers work
- These prerequisites must not form cycles

#### 3.5 Effort Estimation

Base effort per work stream depends on:
- Pathway complexity (Cloud Native = higher base effort than DevOps)
- Number of affected services (more services = multiplier on effort)
- Risk tolerance adjustment: `aggressive` reduces by 20%, `conservative` increases by 30%
- Team size adjustment: small teams (< 4) increase by 20%

Present as three-point estimate satisfying: optimistic <= expected <= pessimistic.


### Step 4: Generate Timeline

#### 4.1 Timeline Phases

Divide the engagement into 3 phases:

| Phase | Name | Coverage |
|-------|------|----------|
| Foundation & DevOps | Weeks 0-4 | DevOps pathway work streams |
| Core Migration | Weeks 4-70% | All work streams in parallel/sequential per risk tolerance |
| Optimization & Validation | 70%-100% | Final validation, optimization, handover |

#### 4.2 Milestones

Define gate milestones:
- **DevOps Foundation Complete** (Week 4) — CI/CD pipelines operational, IaC coverage > 80%
- **Pilot Service Migrated** (40% mark) — First service fully migrated, integration tests passing
- **Portfolio Migration Complete** (100%) — All work streams complete, exit criteria met

#### 4.3 Critical Path

Identify the longest dependency chain through work streams. The critical path determines minimum calendar duration.

#### 4.4 Parallelization Strategy

Based on `risk_tolerance`:
- **Conservative** — No parallel work stream groups. All sequential.
- **Moderate** — Independent streams (those with no prerequisites and not depended upon by others) run in parallel. Dependent streams run sequentially.
- **Aggressive** — Maximum parallelism. All independent streams in parallel groups.

Validate: work streams with prerequisite relationships must NOT appear in the same parallel group.


### Step 5: Risk Register

Generate engagement-level risks with sequential IDs (RISK-001, RISK-002, ...):

#### 5.1 Standard Risks (Always Generated)

| ID | Category | Description |
|----|----------|-------------|
| RISK-001 | Technical | Cross-service dependency complexity creates integration failures during parallel modernization |
| RISK-002 | Organizational | Team spread across multiple pathways reduces velocity per work stream |
| RISK-003 | Timeline | Timeline constraint may be infeasible given scope |

#### 5.2 Conditional Risks

- **Compliance** — If `compliance_requirements` is non-empty, add compliance risk about maintaining compliance during migration transition periods
- **Budget** — If `budget_constraint` is specified and tight relative to estimated cost
- **Capability** — If `existing_capabilities` indicates gaps

Each risk has: `id`, `category` (Technical/Organizational/Timeline/Cost/Compliance), `description`, `likelihood`, `impact`, `mitigation`, `contingency`, `affected_services`, `owner` (role), `trigger` (observable signal).


### Step 6: Cost Estimation

#### 6.1 Engagement-Level Cost

Cost estimation is at the engagement level (`engagement_level: true`), not per-service:

- **People cost** — total_effort_weeks x team_size x hourly_rate ($250) x weekly_hours (40)
- **Infrastructure delta** — estimated monthly AWS spend change during migration ($2000/month per service with work)
- **Training** — $15,000 per pathway if capabilities are lacking, $5,000 if team has existing capabilities
- **Total** — Sum of people + training (three-point: optimistic/expected/pessimistic)

#### 6.2 Consistency Rules

All cost categories must satisfy: optimistic <= expected <= pessimistic.


### Step 7: Decision Points

Generate decision points (DP-001, DP-002, ...) where customer input is required:

- One per work stream: implementation approach (incremental vs big-bang vs phased)
- Training approach (if team capabilities gap exists or team is small)
- Each decision point has: `id`, `question`, `options` (>= 2), `recommendation`, `deadline`, `affected_services`


### Step 8: Success Metrics

Define:
- **Leading indicators** — Sprint velocity, test coverage, integration test pass rate
- **Lagging indicators** — Deployment frequency, MTTR, MODA re-score
- **Exit criteria** — All triggered pathways addressed, no High-severity gaps remaining, portfolio MODA re-score improvement


### Step 9: Assumptions

Document engagement assumptions including:
- Team availability (70% capacity for modernization)
- No major production incidents requiring sustained attention
- MODA report currency (within 90 days)
- Infrastructure and tooling budget approved


## Report Template

The analysis emits a four-artifact bundle: `{portfolio-name}-portfolio-exec-plan.md`, `{portfolio-name}-portfolio-exec-plan.json`, `{portfolio-name}-portfolio-exec-plan.html`, and `{portfolio-name}-portfolio-exec-plan.metadata.json`.

### MD Report Required Sections

The markdown report MUST contain the following 13 sections as H1/H2 headings:

1. **Portfolio Modernization Execution Plan** (H1 title)
2. **Executive Summary**
3. **Portfolio MODA Summary**
4. **Work Stream Overview**
5. **Detailed Work Streams**
6. **Cross-Service Dependencies**
7. **Portfolio Timeline and Phasing**
8. **Critical Path Analysis**
9. **Risk Register**
10. **Engagement Cost Estimation**
11. **Success Metrics and Phase Gates**
12. **Assumptions and Constraints**
13. **Recommendations and Decision Points**

The report MUST include a portfolio-level metadata table at the top containing `| **Portfolio** |` and `| **Services Assessed** |` rows.


## Four-Artifact Output Contract (Portfolio EXEC)

| Artifact | Filename | Purpose |
|---|---|---|
| Markdown report | `{portfolio-name}-portfolio-exec-plan.md` | Narrative execution plan — full work streams, timeline, risk register |
| JSON report | `{portfolio-name}-portfolio-exec-plan.json` | Canonical machine-readable contract for programmatic consumption |
| HTML report | `{portfolio-name}-portfolio-exec-plan.html` | Self-contained HTML visualization with timeline and risk views |
| Metadata sidecar | `{portfolio-name}-portfolio-exec-plan.metadata.json` | Version compatibility data |

### Metadata Sidecar

```json
{
  "analysis_type": "portfolio-exec-plan",
  "analysis_date": "YYYY-MM-DD",
  "td_version": "portfolio-execution-plan-generation",
  "portfolio_name": "{portfolio_name}",
  "services_count": N,
  "moda_report_dates": {
    "service-id-1": "YYYY-MM-DD",
    "service-id-2": "YYYY-MM-DD"
  }
}
```

### JSON Schema (Top-Level Keys)

The portfolio execution plan JSON artifact MUST emit these top-level keys:

| Key | Description |
|-----|-------------|
| `metadata` | Analysis type, date, TD version, portfolio name, services count, team size, risk tolerance, MODA sources |
| `executive_summary` | Feasibility, total effort, calendar duration, top risks, pathways planned, services in/out of scope, decision point count |
| `portfolio_input` | Per-service input data (scores, triggered pathways, classification) and pathway summary (deduplication map) |
| `work_streams` | ONE per unique triggered pathway. Each contains: id, name, pathway, services, objective, prerequisites, effort_weeks, risk_level, phases with tasks, success_criteria |
| `timeline` | Phases (start/end week, work streams), milestones (name, week, gate criteria), critical path, parallelization strategy |
| `risk_register` | Sequential risks (RISK-001...) with category, description, likelihood, impact, mitigation, contingency, affected services, owner, trigger |
| `cost_estimation` | Engagement-level flag, people/infrastructure/training/total with three-point estimates |
| `success_metrics` | Leading indicators, lagging indicators, exit criteria |
| `assumptions` | Array of assumption strings |
| `decision_points` | Sequential DPs (DP-001...) with question, options (>=2), recommendation, deadline, affected services |

### Key Structural Invariants

1. **One work stream per pathway** — `work_streams[].pathway` values are unique (no duplicates)
2. **Task IDs globally unique** — no two tasks across any work stream share an ID
3. **Effort ordering** — all three-point estimates satisfy optimistic <= expected <= pessimistic
4. **No phantom services** — every service referenced in work streams must have a corresponding MODA report
5. **No phantom pathways** — every pathway in work streams must be triggered in at least one consumed MODA report
6. **Prerequisites are acyclic** — work stream prerequisites must not form circular dependencies
7. **Shared tasks are dependencies** — in multi-service work streams, shared infrastructure tasks are listed as dependencies of per-service tasks
8. **Cost is engagement-level** — `cost_estimation.engagement_level` is always `true`
9. **MODA traceability** — every task has `moda_trace` linking to source service and question


## Constraints and Guardrails

- **Read-only analysis**: Do not modify any source code, configuration, or infrastructure. Only create the output portfolio artifact bundle (MD, JSON, HTML, and metadata.json).
- **Stay on the current branch**: Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out.
- **Layered input**: Primary input is the portfolio MODA report (aggregated). Per-service MODA reports are secondary/enrichment only — never re-aggregate from them. The portfolio MODA TD handles aggregation; this TD handles planning.
- **Graceful degradation**: If per-service reports are unavailable, produce the plan using portfolio-level data only. Never fail because a per-service report is missing.
- **Minimum 2 services**: Terminate with a clear error if the portfolio MODA report assessed fewer than 2 services.
- **Deduplication**: Each triggered pathway across the portfolio produces exactly one work stream. Never create per-service work streams for the same pathway.
- **Engagement-level scope**: Cost, effort, timeline, and risk are all at the portfolio/engagement level — not per-service.
- **Evidence-based**: All work streams trace to specific MODA pathway triggers and service IDs. Do not generate work streams for pathways nobody triggered.
- **No hallucination**: Only reference services that have MODA reports. Only reference pathways that exist in the MODA pathway vocabulary. Do not invent services, pathways, or findings.
- **Preferences for framing only**: Technology preferences influence recommendation language but do not change pathway logic, effort estimates, or feasibility assessments.
- **Task granularity**: All tasks must be 1-10 days of effort (1-2 week tasks). If larger, decompose further.
- **Sequential IDs**: Work stream IDs (WS-01, WS-02), risk IDs (RISK-001, RISK-002), decision point IDs (DP-001, DP-002) are sequential with no gaps.


## Error Handling

### Missing or Invalid Portfolio MODA Report

IF the portfolio MODA report is not found at the expected path or is invalid JSON, THEN terminate with: "Portfolio execution plan generation failed: portfolio MODA report not found or invalid at expected path."

### Insufficient Services

IF the portfolio MODA report's `metadata.services_assessed` is fewer than 2, THEN terminate with: "Portfolio execution plan generation failed: requires portfolio MODA report covering at least 2 services. Found {N}."

### No Triggered Pathways

IF all pathways in the portfolio report have `portfolio_status` != "Triggered" (all services are already mature), emit a minimal plan: "MODA identified no modernization pathways requiring action across {N} services. Current portfolio average score is {X}/4.0. Recommend periodic re-evaluation."

### Infeasible Timeline

IF calculated timeline exceeds `timeline_constraint` by >50% AND risk_tolerance is aggressive, set feasibility to "Red". Otherwise if pathways >= 4 or total effort > 40 weeks, set feasibility to "Yellow". Emit structured recommendations: (a) increase team size, (b) reduce scope (defer pathways), (c) accept extended timeline.
