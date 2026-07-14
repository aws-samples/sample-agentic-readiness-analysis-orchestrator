---
name: portfolio-execution-plan-generation
description: Generate portfolio-level unified execution plan from aggregated MODA and/or ARA reports
version: 0.2.0
---

## Name

Portfolio Execution Plan Generation

## Objective

Generate a comprehensive portfolio-level execution plan by consuming the portfolio MODA report (modernization pathways) AND/OR the portfolio ARA report (agent-readiness BLOCKERs/RISKs) and producing ONE unified engagement-level roadmap. At least one report must exist; when both exist the plan covers both dimensions with cross-dependency detection.

The portfolio MODA report provides triggered modernization pathways (containers, DevOps, cloud native, managed DBs). The portfolio ARA report provides agent-readiness findings (BLOCKERs that must be fixed before agents can safely call services, and RISKs that are recommended improvements). This TD focuses purely on **planning**: converting those aggregated analyses into deduplicated work streams, cross-service dependency ordering, phased timelines, risk registers, cost estimations, and success metrics — enabling coordinated execution planning across the entire service estate.

## Summary

This transformation uses a **layered input approach** with TWO optional primary inputs (at least one required):

1. **Portfolio MODA report** (`{portfolio-name}-mod-portfolio-report.json`) — modernization pathways, per-service scores, triggered pathways, dependency maps
2. **Portfolio ARA report** (`{portfolio-name}-ara-portfolio-report.json`) — agent-readiness findings, BLOCKERs, RISKs, cross-cutting themes, remediation roadmap

With optional drill-down into individual per-service reports only when deeper granularity is needed. It does NOT re-evaluate codebases or re-aggregate per-service data — that work is already done by the portfolio MODA/ARA TDs. Instead, it:

1. **Reads the portfolio MODA report** (if exists) from `./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json`
2. **Reads the portfolio ARA report** (if exists) from `./portfolio-agentic-readiness-analysis/{portfolio-name}-ara-portfolio-report.json`
3. **Validates at least one exists** — terminates with error if neither is found
4. **Optionally reads per-service MODA reports** from `./services/{name}/modernization-readiness-analysis/{slug}-mod-report.json` — only for decomposition strategy details
5. **Optionally reads per-service ARA reports** from `./services/{name}/agentic-readiness-analysis/{slug}-ara-report.json` — only for detailed evidence and remediation specifics
6. **Generates Modernization Work Streams** (from MODA) — ONE work stream per unique triggered pathway, listing all affected services
7. **Generates Agent-Readiness Work Streams** (from ARA) — ONE work stream per ARA category with BLOCKERs/RISKs, with BLOCKERs mapped to mandatory tasks and RISKs to recommended tasks
8. **Detects cross-dimension dependencies** — where MODA work enables ARA readiness (e.g., "Move to Modern DevOps" enables "Add Agent Observability")
9. **Establishes shared infrastructure tasks** for work streams affecting multiple services
10. **Maps cross-service dependencies** between work streams
11. **Produces a phased timeline** with parallelization strategy based on risk tolerance and dependency ordering
12. **Identifies risks** at the engagement level
13. **Estimates effort and cost** at the engagement level with three-point estimates (optimistic / expected / pessimistic)
14. **Defines decision points** where customer input is required before proceeding

The output is a **four-artifact bundle**:
- `{portfolio-name}-portfolio-exec-plan.md` — narrative execution plan
- `{portfolio-name}-portfolio-exec-plan.json` — canonical machine-readable contract
- `{portfolio-name}-portfolio-exec-plan.html` — self-contained HTML visualization
- `{portfolio-name}-portfolio-exec-plan.metadata.json` — version sidecar

**What this TD does NOT do:**
- Re-run MODA scoring or ARA evaluation (consumes portfolio outputs as-is)
- Re-aggregate per-service reports (the portfolio TDs already do this — per-service reports are only used for optional enrichment)
- Ask interactive questions (all context provided upfront via `additionalPlanContext`)
- Generate Word documents or CSV files (uses standard four-artifact contract)
- Execute or modify source code
- Make technology decisions — it recommends options with tradeoffs, customer decides
- Produce per-service execution plans — it produces ONE portfolio-level plan covering ALL services

**Key differentiator from per-service execution plan TD:** This TD operates at the portfolio level with a layered input model. It uses the already-aggregated portfolio MODA and/or ARA reports as its primary inputs and only drills into individual per-service reports for enrichment when deeper detail is needed. It focuses purely on planning — deduplicating shared work (e.g., "Move to Modern DevOps" triggered by 3 services becomes ONE work stream; "Implement Machine Identity" BLOCKERing 4 services becomes ONE agent-readiness work stream), identifying cross-service AND cross-dimension dependencies, and estimating engagement-level cost rather than per-service cost.

## Entry Criteria

- **Required (at least one):**
  - Portfolio MODA report JSON at `./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json` — AND/OR —
  - Portfolio ARA report JSON at `./portfolio-agentic-readiness-analysis/{portfolio-name}-ara-portfolio-report.json`
- At least ONE of the above must exist. Both are consumed when available for a unified plan.
- If MODA report exists: must follow expected schema — `metadata` with `portfolio_name`, `assessment_date`, `services_assessed`; `pathways[]` array with `portfolio_status`; `repositories[]` array with per-service scores and triggered pathways; produced by `portfolio-modernization-readiness-analysis` TD with at least 2 assessed services
- If ARA report exists: must follow expected schema — `assessment_type: "portfolio-ara"`, `metadata` with `portfolio_name`, `assessment_date`, `services_assessed`; `findings[]` array with `native_severity` (BLOCKER/RISK-SAFETY/RISK-QUALITY/INFO); `repositories[]` array; `remediation_roadmap` with phased items; produced by `portfolio-agentic-readiness-analysis` TD with at least 2 assessed services
- **Optional:** Individual per-service MODA reports at `./services/{name}/modernization-readiness-analysis/{slug}-mod-report.json` — used for enrichment only
- **Optional:** Individual per-service ARA reports at `./services/{name}/agentic-readiness-analysis/{slug}-ara-report.json` — used for enrichment only
- The TD degrades gracefully if per-service reports are unavailable
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
| `ai_acceleration` | enum | No | `"enabled"` | One of: `enabled`, `disabled`, `custom`. Controls whether AI-accelerated effort estimates are generated. `enabled` = standard acceleration factors (40-60% for code tasks, 0-10% for design). `disabled` = only traditional estimates shown. `custom` = use `ai_acceleration_overrides` for per-category factors. |
| `ai_acceleration_overrides` | object | No | — | Override default acceleration percentages per task category. Keys are category names from the acceleration table (e.g., `code_migration: 50`, `iac_generation: 55`). Values are percentage reductions (0-80). Only used when `ai_acceleration: "custom"`. |
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
- **`timeline_constraint`** → Compared against AI-accelerated timeline to determine feasibility (Green/Yellow/Red). If infeasible, recommendations include scope reduction or team expansion.
- **`compliance_requirements`** → Generates additional risks in the Compliance category. Adds validation gates and dual-running requirements to affected work streams.
- **`existing_capabilities`** → When absent or indicating gaps, generates training decision points. When team has strong capabilities, reduces effort multipliers.
- **`ai_acceleration`** → When `enabled` (default), produces dual-perspective effort estimates on every task and work stream. Timeline and cost default to AI-accelerated values. When `disabled`, only traditional estimates are produced. When `custom`, uses `ai_acceleration_overrides` factors instead of defaults.


### Step 1: Discover and Load Reports (Layered Input)

This TD uses a **layered input approach** with two optional primary inputs (at least one required):

| Layer | Source | Purpose | When Used |
|-------|--------|---------|-----------|
| **Primary A** | Portfolio MODA report | Aggregated pathways, service tiers, cross-cutting themes, priority weighting | When exists — provides modernization work streams |
| **Primary B** | Portfolio ARA report | Agent-readiness BLOCKERs, RISKs, cross-cutting findings, remediation roadmap | When exists — provides agent-readiness work streams |
| **Secondary** | Individual per-service reports (MODA + ARA) | Detailed evidence files, specific question scores, decomposition strategy details | Only when a work stream needs deeper granularity |

The TD does NOT re-aggregate data across services — that work is already done in the portfolio reports.

#### 1.1 Load Portfolio MODA Report (Primary Input A — Optional)

Read the portfolio MODA report from the expected path:

```
./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json
```

If `portfolio_name` is specified in `additionalPlanContext`, use it to construct the filename. Otherwise, look for the single `*-mod-portfolio-report.json` file in the directory.

**Validation (if file exists):**
- Is a valid JSON document
- Has `metadata` with `portfolio_name`, `assessment_date`, `services_assessed` (integer >= 2)
- Has `pathways[]` array with entries containing `id` and `portfolio_status`
- Has `repositories[]` array with entries containing `repo_name`, `overall_score`, `classification`

**If the file does not exist, note MODA is unavailable and continue to Step 1.2.**

**Extract from the portfolio MODA report (when available):**

- **Portfolio metadata** — `metadata.portfolio_name`, `metadata.assessment_date`, `metadata.services_assessed`
- **Triggered pathways** — entries in `pathways[]` where `portfolio_status == "Triggered"`, collecting `id`, `contributing_repos[]`, `priority`, and `effort`
- **Per-service data** — from `repositories[]`: `repo_name`, `overall_score`, `classification.tier`, `pathways_triggered[]`
- **Dependency map** — from `dependency_map` if present (cross-service relationships already identified by portfolio MODA)
- **Remediation roadmap** — from `remediation_roadmap` if present (pre-computed phasing from portfolio MODA)

#### 1.2 Load Portfolio ARA Report (Primary Input B — Optional)

Read the portfolio ARA report from the expected path:

```
./portfolio-agentic-readiness-analysis/{portfolio-name}-ara-portfolio-report.json
```

If `portfolio_name` is specified in `additionalPlanContext`, use it to construct the filename. Otherwise, look for the single `*-ara-portfolio-report.json` file in the directory.

**Validation (if file exists):**
- Is a valid JSON document
- Has `assessment_type: "portfolio-ara"`
- Has `metadata` with `portfolio_name`, `assessment_date`, `services_assessed` (integer >= 2)
- Has `findings[]` array with entries containing `question_id`, `repo_name`, `native_severity`, `category_id`
- Has `repositories[]` array with entries containing `repo_name`, `classification.tier`, `classification.blocker_count`
- Has `remediation_roadmap` with phased items

**If the file does not exist, note ARA is unavailable and continue to Step 1.3.**

**Extract from the portfolio ARA report (when available):**

- **Portfolio metadata** — `metadata.portfolio_name`, `metadata.assessment_date`, `metadata.services_assessed`
- **BLOCKERs** — findings where `native_severity == "BLOCKER"`, grouped by `category_id` and collecting `repo_name`, `question_id`, `title`, `recommendation`, `effort`, `phase`
- **RISKs (Safety)** — findings where `native_severity == "RISK-SAFETY"`, grouped by `category_id`
- **RISKs (Quality)** — findings where `native_severity == "RISK-QUALITY"`, grouped by `category_id`
- **Per-service readiness** — from `repositories[]`: `repo_name`, `classification.tier`, `classification.blocker_count`, `classification.risk_safety_count`
- **Remediation roadmap** — from `remediation_roadmap.items[]`: phased remediation actions already computed by portfolio ARA
- **Cross-cutting findings** — from `cross_cutting_findings[]` if present (issues affecting multiple services in the same category)
- **Dependency map** — from `dependency_map` if present

#### 1.3 Validate At Least One Report Exists

**Terminate with a clear error if NEITHER the portfolio MODA report NOR the portfolio ARA report was found:**

```
Portfolio execution plan generation failed: neither portfolio MODA report nor portfolio ARA report 
found at expected paths. At least one must exist.
Expected MODA: ./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json
Expected ARA: ./portfolio-agentic-readiness-analysis/{portfolio-name}-ara-portfolio-report.json
```

Set availability flags:
- `has_moda = true/false`
- `has_ara = true/false`
- `mode = "unified"` (both) | `"moda-only"` | `"ara-only"`

#### 1.4 Load Per-Service Reports (Secondary/Enrichment Input)

Only drill into individual per-service reports when a work stream requires deeper granularity that the portfolio reports do not provide.

**Per-service MODA reports** at:
```
./services/{service-name}/modernization-readiness-analysis/{slug}-mod-report.json
```

**Per-service ARA reports** at:
```
./services/{service-name}/agentic-readiness-analysis/{slug}-ara-report.json
```

**When to read a per-service MODA report:**
- The work stream involves Cloud Native decomposition and needs detailed `decomposition_strategy`
- Effort estimation requires specific question scores
- A task's `moda_trace` needs precise evidence file references for acceptance criteria

**When to read a per-service ARA report:**
- The work stream needs detailed evidence for a specific BLOCKER remediation
- Task acceptance criteria require specific file/line references from ARA findings
- Effort estimation needs question-level detail on the severity or scope of a finding

**What NOT to do with per-service reports:**
- Do NOT re-aggregate (the portfolio reports already have canonical aggregated data)
- Do NOT use per-service reports to override portfolio-level status or priority
- Do NOT fail if a per-service report is unavailable — degrade gracefully

#### 1.5 Report Currency Check

For each available portfolio report, calculate age from `metadata.assessment_date`. If a report is older than 90 days, note this in the plan's assumptions with a staleness caveat. Also check per-repository analysis dates if available.


### Step 2: Extract Pathway-to-Services Map (MODA)

**Skip this step if `has_moda == false`.**

#### 2.1 Build Pathway-to-Services Map

From the portfolio MODA report's `pathways[]` array (already aggregated by the portfolio MODA TD):
- For each pathway where `portfolio_status == "Triggered"`, extract `contributing_repos[].repo_name` as the list of affected services
- Identify shared pathways (contributing_repos length >= 2)
- Identify single-service pathways (contributing_repos length == 1)

#### 2.2 Identify Services Without Modernization Work

Services in `repositories[]` with empty `pathways_triggered[]` are noted in the executive summary as "services_no_moda_action" and excluded from modernization work stream generation.

#### 2.3 Deduplication Principle

**Critical rule:** Each unique triggered pathway produces exactly ONE modernization work stream, regardless of how many services trigger it. A pathway triggered by 3 services produces one work stream with 3 services listed — NOT 3 separate work streams. The portfolio MODA report already enforces this deduplication at the pathway level.


### Step 3: Generate Modernization Work Streams (MODA)

**Skip this step if `has_moda == false`.**

For each unique triggered pathway (filtered by `priority_pathways` / `excluded_pathways`), generate a single modernization work stream.

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
| `effort_weeks_traditional` | Three-point estimate (optimistic, expected, pessimistic) — manual engineering effort without AI tooling |
| `effort_weeks_ai_accelerated` | Three-point estimate (optimistic, expected, pessimistic) — with AI-assisted code generation, automated testing, IaC generation |
| `ai_acceleration_pct` | Percentage reduction from traditional to AI-accelerated (weighted average across tasks) |
| `risk_level` | High / Medium / Low |
| `phases` | Ordered execution phases with tasks |
| `success_criteria` | Measurable outcomes confirming completion |

#### 3.2 Task Decomposition

Within each work stream, decompose into tasks at 1-2 week (1-10 day) granularity:

- Each task has: `id`, `description`, `effort_days_traditional` (1-10), `effort_days_ai_accelerated` (1-10), `ai_acceleration_factor` (percentage reduction), `service` (which service or "shared"), `dependencies` (other task IDs), `acceptance_criteria`, `moda_trace` (traceability to source MODA finding)
- Task IDs are globally unique across all work streams
- Every task must specify which service it applies to (or "shared" for cross-cutting infrastructure)
- Every task must classify its AI acceleration potential based on task type (see Step 3.5)

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

#### 3.5 Effort Estimation (Dual-Perspective)

All effort estimates MUST include TWO perspectives: **Traditional** (manual engineering) and **AI-Accelerated** (with agent-assisted tooling).

**Traditional effort** (base) per work stream depends on:
- Pathway complexity (Cloud Native = higher base effort than DevOps)
- Number of affected services (more services = multiplier on effort)
- Risk tolerance adjustment: `aggressive` reduces by 20%, `conservative` increases by 30%
- Team size adjustment: small teams (< 4) increase by 20%

**AI-Accelerated effort** applies a per-task acceleration factor based on task type:

| Task Category | AI Acceleration | Reduction | Rationale |
|---------------|----------------|-----------|-----------|
| Code migration/refactoring | High | 40-60% | Agent-assisted code transformation, pattern application, automated refactoring |
| IaC generation (CDK, Terraform, CloudFormation) | High | 40-60% | AI generates infrastructure code from requirements, handles boilerplate |
| Test suite creation | High | 40-60% | AI generates unit tests, integration tests, test fixtures from existing code |
| Documentation generation | High | 50-60% | API specs, runbooks, architecture docs generated from code analysis |
| Boilerplate/scaffolding | Very High | 50-70% | Project setup, configuration templates, CI/CD pipeline definitions |
| API specification writing (OpenAPI, Smithy) | High | 40-50% | AI generates specs from existing endpoint implementations |
| Architecture decisions & design | Minimal | 0-10% | Requires human judgment, stakeholder alignment, trade-off evaluation |
| Production cutover & validation | Minimal | 0-10% | Requires careful human oversight, rollback readiness, real traffic |
| Performance/load testing | Minimal | 5-15% | Test execution is automated but design and analysis are human-driven |
| Compliance audits & reviews | Minimal | 0-10% | Requires human attestation, regulatory understanding, organizational context |
| Team training & knowledge transfer | Minimal | 0-10% | Learning requires human cognitive effort; AI assists with materials only |
| Data migration & validation | Low-Medium | 15-30% | Scripts are AI-generatable but validation requires domain knowledge |

**Acceleration Benchmarks (Field-Calibrated)**

These acceleration factors are calibrated against observed results from production EBA engagements using AWS Transform Custom + AI-assisted tooling:

| Activity | Traditional | AI-Accelerated (Observed) | Acceleration Factor |
|----------|-------------|--------------------------|---------------------|
| Code analysis & readiness assessment | 4-8 weeks | ~90 minutes | ~200x |
| Architecture decomposition design (668K+ LOC monolith → microservices) | 2-4 months | ~2 days | ~10-20x |
| Service extraction + containerization + DB migration (per service) | 2-4 weeks | ~1 day | ~5-10x |
| Infrastructure migration execution (DB, networking, IAM) | 2-3 weeks | 3-5 days | ~3-5x |

These benchmarks represent the upper end of achievable acceleration with experienced practitioners using mature AI tooling. Actual acceleration varies by:
- Codebase complexity and documentation quality
- Team proficiency with AI-assisted workflows
- Degree of technical debt and coupling
- Regulatory/compliance validation requirements (which remain human-paced)

When generating estimates, use the **task-level acceleration table above** (40-60% reduction ranges) as the conservative planning default. The field benchmarks demonstrate that skilled teams can achieve significantly higher acceleration in practice, particularly for assessment and design phases.

**Calculating AI-accelerated effort:**
1. For each task, assign the appropriate acceleration category
2. Apply the reduction percentage to `effort_days_traditional` to get `effort_days_ai_accelerated`
3. Round up to nearest half-day (minimum 0.5 days per task)
4. Sum across tasks for work stream `effort_weeks_ai_accelerated`
5. Calculate `ai_acceleration_pct` as: `(1 - ai_accelerated / traditional) * 100`

Present BOTH estimates as three-point estimates satisfying: optimistic <= expected <= pessimistic.


### Step 4: Generate Agent-Readiness Work Streams (ARA)

**Skip this step if `has_ara == false`.**

For each ARA category that contains BLOCKERs or RISKs (RISK-SAFETY, RISK-QUALITY) affecting services in the portfolio, generate an agent-readiness work stream. ARA categories map to work streams as follows:

| ARA Category ID | Work Stream Name | Focus |
|-----------------|-----------------|-------|
| `AUTH` | Implement Agent Identity & Authorization | Machine identity, scoped permissions, action-level auth, identity propagation, credential rotation, suspension capability |
| `API` | Harden API Surface | Machine-readable specs, structured errors, idempotency, pagination, versioning |
| `STATE` | Ensure Transactional Integrity | Idempotent mutations, compensating transactions, circuit breakers, rate limiting, graceful degradation |
| `HITL` | Add Human-in-the-Loop Controls | Confirmation flows, approval queues, undo/cancel, escalation paths, blast-radius limits |
| `DATA` | Improve Data Accessibility | PII filtering, data residency, pagination, input validation, temporal metadata |
| `DISC` | Enhance Discoverability | Schema versioning, API contracts, service registry, capability advertisement |
| `OBS` | Add Agent Observability | Distributed tracing, structured logging, agent-specific metrics, anomaly detection, audit trails |
| `ENG` | Strengthen Engineering Maturity | Test coverage, deployment automation, rollback capability, environment parity |

#### 4.1 ARA Work Stream Structure

Each agent-readiness work stream contains:

| Field | Description |
|-------|-------------|
| `id` | Sequential identifier continuing from MODA work streams (e.g., WS-05, WS-06, ...) |
| `name` | Maps to ARA category (e.g., "Implement Agent Identity & Authorization") |
| `dimension` | `"agent-readiness"` |
| `ara_category` | Category ID (e.g., "AUTH") |
| `services` | All service IDs affected by BLOCKERs/RISKs in this category |
| `blockers` | Count of BLOCKER findings in this category — these produce MANDATORY tasks |
| `risks` | Count of RISK findings — these produce RECOMMENDED tasks |
| `objective` | Concrete outcome when complete |
| `prerequisites` | Other work stream IDs (may include MODA work streams) |
| `effort_weeks_traditional` | Three-point estimate (optimistic, expected, pessimistic) — manual engineering |
| `effort_weeks_ai_accelerated` | Three-point estimate (optimistic, expected, pessimistic) — with AI tooling |
| `ai_acceleration_pct` | Percentage reduction from traditional to AI-accelerated |
| `risk_level` | High (has BLOCKERs) / Medium (RISKs only) / Low |
| `phases` | Ordered execution phases with tasks |
| `success_criteria` | Measurable outcomes confirming completion |

#### 4.2 Severity-to-Priority Mapping

ARA findings map to task priority:

| ARA Native Severity | Task Priority | Requirement Level |
|---------------------|---------------|-------------------|
| `BLOCKER` | Mandatory (P0) | Must be completed before agents can safely call the service |
| `RISK-SAFETY` | Strongly Recommended (P1) | Safety impact — should be completed before production agent deployment |
| `RISK-QUALITY` | Recommended (P2) | Quality improvement — improves agent integration quality |
| `INFO` | Optional (P3) | Not included in work streams unless it enables a BLOCKER/RISK fix |

#### 4.3 Task Decomposition (ARA)

Within each ARA work stream, decompose into tasks at 1-2 week (1-10 day) granularity:

- Each task has: `id`, `description`, `effort_days_traditional` (1-10), `effort_days_ai_accelerated` (1-10), `ai_acceleration_factor` (percentage reduction), `service` (which service or "shared"), `dependencies` (other task IDs), `acceptance_criteria`, `ara_trace` (traceability to source ARA finding — `question_id` + `repo_name`)
- BLOCKER tasks are ordered first within each phase
- Tasks from `cross_cutting_findings` produce shared infrastructure tasks
- When multiple services have the same BLOCKER (e.g., AUTH-Q1 across 4 services), generate ONE shared pattern task + per-service implementation tasks
- Apply the same AI acceleration categories from Step 3.5 (e.g., implementing OAuth2 patterns = code migration/refactoring = 40-60% acceleration; compliance review of auth changes = minimal acceleration)

#### 4.4 Shared Infrastructure Tasks (ARA)

For categories where the same finding affects multiple services:
- Generate a "shared" pattern/infrastructure task establishing the common approach
- Example: "Design shared machine identity authentication pattern (OAuth2 client credentials + API Gateway authorizers) for all services"
- Per-service implementation tasks depend on the shared pattern task

#### 4.5 Effort Estimation (ARA — Dual-Perspective)

**Traditional effort** (base) per ARA work stream depends on:
- Number of BLOCKERs (each BLOCKER adds 1-2 weeks depending on effort rating in ARA report)
- Number of RISKs (each RISK adds 0.5-1 week)
- Number of affected services (multiplier for per-service implementation)
- Existing capability adjustment (if team has auth/security experience, reduce AUTH/STATE effort)
- Risk tolerance adjustment: same as MODA work streams

**AI-Accelerated effort** applies the same per-task acceleration framework from Step 3.5. ARA tasks typically break down as:
- Implementing auth patterns, API specs, observability instrumentation → High acceleration (40-60%)
- Writing IaC for API gateways, rate limiters, circuit breakers → High acceleration (40-60%)
- Generating test suites for auth flows, error handling → High acceleration (40-60%)
- Security architecture design, threat modeling → Minimal acceleration (0-10%)
- Compliance validation of auth/HITL implementations → Minimal acceleration (0-10%)

Present BOTH estimates as three-point estimates satisfying: optimistic <= expected <= pessimistic.


### Step 5: Detect Cross-Dimension Dependencies

**Skip this step if `mode != "unified"` (only one report available).**

Identify where MODA modernization work enables or is required by ARA agent-readiness work, and vice versa. These cross-dimension dependencies create ordering constraints in the unified timeline.

#### 5.1 Common Cross-Dimension Dependencies

| MODA Work Stream | Enables ARA Work Stream | Rationale |
|------------------|------------------------|-----------|
| Move to Modern DevOps | Add Agent Observability | Modern CI/CD provides the deployment pipeline for observability instrumentation |
| Move to Modern DevOps | Strengthen Engineering Maturity | DevOps automation is prerequisite for deployment automation and rollback |
| Move to Containers | Harden API Surface | Containerized services enable API gateway patterns and service mesh |
| Move to Containers | Ensure Transactional Integrity | Container orchestration provides circuit breaker and rate limiting infrastructure |
| Move to Cloud Native | Enhance Discoverability | Cloud-native architectures support service registry and API versioning |
| Move to Managed Databases | Improve Data Accessibility | Managed databases provide built-in pagination, encryption, access controls |

#### 5.2 Dependency Detection Logic

For each ARA work stream:
1. Check if any MODA work stream provides infrastructure that the ARA work stream needs
2. If the ARA work stream's tasks reference infrastructure provided by a MODA pathway (e.g., "API Gateway" when containers/cloud-native provides it), add a prerequisite
3. Record the dependency as: `{ source_ws: "WS-XX", target_ws: "WS-YY", type: "enables", rationale: "..." }`

For each MODA work stream:
1. Check if any ARA BLOCKER must be resolved BEFORE the modernization can proceed safely
2. Example: If AUTH BLOCKERs exist and the service is being migrated to a public-facing container, the auth fix should precede the migration
3. Record reverse dependencies where safety requires ARA-first ordering

#### 5.3 Cross-Dependency Output

Store detected cross-dimension dependencies in:
```json
{
  "cross_dimension_dependencies": [
    {
      "source_ws": "WS-01",
      "source_dimension": "modernization",
      "target_ws": "WS-05",
      "target_dimension": "agent-readiness",
      "type": "enables",
      "rationale": "Modern DevOps CI/CD pipeline required for deploying observability instrumentation"
    }
  ]
}
```

These dependencies are surfaced in both the timeline phasing and the narrative report's cross-dependency section.


### Step 6: Generate Timeline

The timeline defaults to **AI-accelerated effort estimates**. Traditional estimates are shown as a reference column to quantify the acceleration benefit. Feasibility assessment uses the AI-accelerated timeline.

#### 6.1 Timeline Phases

Divide the engagement into phases based on available dimensions:

| Phase | Name | Coverage |
|-------|------|----------|
| Foundation & Safety | Weeks 0-4 | DevOps pathway work streams + ARA BLOCKER remediation (AUTH, STATE) |
| Core Execution | Weeks 4-70% | All work streams (MODA + ARA) in parallel/sequential per risk tolerance |
| Optimization & Validation | 70%-100% | Final validation, optimization, handover, agent readiness verification |

When only MODA is available, Phase 1 focuses on DevOps. When only ARA is available, Phase 1 focuses on BLOCKER remediation. When both are present, Phase 1 combines DevOps foundation with critical BLOCKER fixes (AUTH/STATE) since both are foundational.

#### 6.2 Milestones

Define gate milestones (adapted to available dimensions):

**MODA milestones (when `has_moda`):**
- **DevOps Foundation Complete** (Week 4) — CI/CD pipelines operational, IaC coverage > 80%
- **Pilot Service Migrated** (40% mark) — First service fully migrated, integration tests passing

**ARA milestones (when `has_ara`):**
- **Critical BLOCKERs Resolved** (Week 4-6) — All BLOCKER findings remediated, agents can authenticate
- **Agent Pilot Ready** (60% mark) — First service passes full ARA re-evaluation with no BLOCKERs

**Unified milestone (always):**
- **Portfolio Execution Complete** (100%) — All work streams complete, exit criteria met

#### 6.3 Critical Path

Identify the longest dependency chain through ALL work streams (MODA + ARA + cross-dimension dependencies). The critical path determines minimum calendar duration. Cross-dimension dependencies may extend the critical path beyond what either dimension alone would produce.

#### 6.4 Parallelization Strategy

Based on `risk_tolerance`:
- **Conservative** — No parallel work stream groups. All sequential.
- **Moderate** — Independent streams (those with no prerequisites and not depended upon by others) run in parallel. Dependent streams run sequentially.
- **Aggressive** — Maximum parallelism. All independent streams in parallel groups.

Validate: work streams with prerequisite relationships (including cross-dimension dependencies) must NOT appear in the same parallel group.


### Step 7: Risk Register

Generate engagement-level risks with sequential IDs (RISK-001, RISK-002, ...):

#### 7.1 Standard Risks (Always Generated)

| ID | Category | Description |
|----|----------|-------------|
| RISK-001 | Technical | Cross-service dependency complexity creates integration failures during parallel execution |
| RISK-002 | Organizational | Team spread across multiple work streams reduces velocity per stream |
| RISK-003 | Timeline | Timeline constraint may be infeasible given scope |

#### 7.2 Conditional Risks

- **Compliance** — If `compliance_requirements` is non-empty, add compliance risk about maintaining compliance during transition periods
- **Budget** — If `budget_constraint` is specified and tight relative to estimated cost
- **Capability** — If `existing_capabilities` indicates gaps
- **Agent Safety** (when `has_ara`) — If BLOCKERs exist and agents are already calling services, add risk: "Unresolved BLOCKERs create safety exposure if agents are deployed before remediation completes"
- **Cross-Dimension** (when `mode == "unified"`) — Add risk: "Cross-dimension dependencies between modernization and agent-readiness may extend critical path beyond single-dimension estimates"

Each risk has: `id`, `category` (Technical/Organizational/Timeline/Cost/Compliance/AgentSafety), `description`, `likelihood`, `impact`, `mitigation`, `contingency`, `affected_services`, `owner` (role), `trigger` (observable signal).


### Step 8: Cost Estimation

#### 8.1 Engagement-Level Cost (Dual-Perspective)

Cost estimation is at the engagement level (`engagement_level: true`), not per-service. Covers BOTH dimensions when available. Produce TWO cost projections:

**Traditional Cost (reference baseline):**
- **People cost** — total_effort_weeks_traditional (MODA + ARA combined) x team_size x hourly_rate ($250) x weekly_hours (40)
- **Infrastructure delta** — estimated monthly AWS spend change during engagement ($2000/month per service with work) x calendar_months_traditional
- **Training** — $15,000 per MODA pathway if capabilities are lacking, $5,000 if team has existing capabilities; $10,000 for agent-readiness patterns (auth, observability) if team lacks experience
- **Total Traditional** — Sum of people + infrastructure + training (three-point: optimistic/expected/pessimistic)

**AI-Accelerated Cost (primary/default projection):**
- **People cost** — total_effort_weeks_ai_accelerated x team_size x hourly_rate ($250) x weekly_hours (40)
- **AI tooling cost** — $500/month per engineer for AI coding assistants and agent tooling (included in AI-accelerated projection)
- **Infrastructure delta** — same monthly rate but fewer months: $2000/month x calendar_months_ai_accelerated
- **Training** — same as traditional (AI acceleration does not reduce training needs)
- **Total AI-Accelerated** — Sum of people + AI tooling + infrastructure + training (three-point: optimistic/expected/pessimistic)

**Cost savings summary:**
- `cost_savings_absolute` = Total Traditional - Total AI-Accelerated
- `cost_savings_pct` = (1 - AI-Accelerated / Traditional) * 100
- `calendar_time_saved_weeks` = calendar_weeks_traditional - calendar_weeks_ai_accelerated

The AI-accelerated projection is the **default** used for timeline planning and feasibility assessment. Traditional is presented as a reference baseline to quantify the value of AI tooling.

#### 8.2 Consistency Rules

All cost categories must satisfy: optimistic <= expected <= pessimistic. This applies independently to both Traditional and AI-Accelerated projections.


### Step 9: Decision Points

Generate decision points (DP-001, DP-002, ...) where customer input is required:

- One per MODA work stream: implementation approach (incremental vs big-bang vs phased)
- One per ARA BLOCKER category: remediation approach (shared pattern vs per-service, timeline priority)
- Training approach (if team capabilities gap exists or team is small)
- Agent deployment timing (when `has_ara`): at what point in the plan can agents begin calling services?
- Each decision point has: `id`, `question`, `options` (>= 2), `recommendation`, `deadline`, `affected_services`


### Step 10: Success Metrics

Define:
- **Leading indicators** — Sprint velocity, test coverage, integration test pass rate
- **Lagging indicators (MODA)** — Deployment frequency, MTTR, MODA re-score improvement
- **Lagging indicators (ARA)** — BLOCKER count reduction, ARA re-score improvement, agent authentication success rate, agent error rate
- **Exit criteria** — All triggered pathways addressed (MODA), all BLOCKERs resolved (ARA), no High-severity gaps remaining, portfolio re-score improvement on both dimensions


### Step 11: Assumptions

Document engagement assumptions including:
- Team availability (70% capacity for execution)
- No major production incidents requiring sustained attention
- Report currency (MODA and/or ARA reports within 90 days)
- Infrastructure and tooling budget approved
- Agent deployment does not proceed until BLOCKER remediation completes (when `has_ara`)
- AI tooling available to engineers (coding assistants, agent-based code generation, automated test generation) — AI-accelerated estimates assume this tooling is provisioned and team is proficient
- AI acceleration estimates are based on 2025-2026 tooling capabilities; actual acceleration may vary by team proficiency and task complexity


## Report Template

The analysis emits a four-artifact bundle: `{portfolio-name}-portfolio-exec-plan.md`, `{portfolio-name}-portfolio-exec-plan.json`, `{portfolio-name}-portfolio-exec-plan.html`, and `{portfolio-name}-portfolio-exec-plan.metadata.json`.

### MD Report Required Sections

The markdown report MUST contain the following sections as H1/H2 headings. Sections marked with dimension indicators are only included when that dimension's report is available:

1. **Portfolio Execution Plan** (H1 title)
2. **Executive Summary** — includes AI acceleration benefit summary (total weeks saved, cost savings percentage)
3. **Portfolio Analysis Summary** — includes MODA summary (if available) and ARA summary (if available)
4. **Modernization Work Streams** (MODA) — only when `has_moda`
5. **Agent-Readiness Work Streams** (ARA) — only when `has_ara`
6. **AI Acceleration Analysis** — shows per-work-stream acceleration breakdown, which tasks benefit most, total savings
7. **Cross-Dimension Dependencies** — only when `mode == "unified"`
8. **Cross-Service Dependencies**
9. **Unified Timeline and Phasing** — uses AI-accelerated estimates as default; traditional shown as reference
10. **Critical Path Analysis**
11. **Risk Register**
12. **Engagement Cost Estimation** — dual columns: Traditional vs AI-Accelerated, with savings summary
13. **Success Metrics and Phase Gates**
14. **Assumptions and Constraints**
15. **Recommendations and Decision Points**

The report MUST include a portfolio-level metadata table at the top containing:
- `| **Portfolio** |` row
- `| **Services Assessed** |` row
- `| **Dimensions** |` row — value is "MODA + ARA" or "MODA only" or "ARA only"
- `| **MODA Pathways Planned** |` row (when `has_moda`)
- `| **ARA BLOCKERs Addressed** |` row (when `has_ara`)
- `| **Total Effort (Traditional)** |` row — e.g., "42-56 weeks"
- `| **Total Effort (AI-Accelerated)** |` row — e.g., "24-34 weeks"
- `| **AI Acceleration Benefit** |` row — e.g., "43% effort reduction, 18 weeks saved"

### Work Stream Table Format

Work stream overview tables in the markdown report MUST use dual-column effort format:

```markdown
| ID | Work Stream | Services | Traditional (wks) | AI-Accelerated (wks) | Savings | Risk |
|----|-------------|----------|-------------------|---------------------|---------|------|
| WS-01 | Move to Modern DevOps | 3 | 8-12 | 4-7 | 45% | Medium |
| WS-02 | Implement Agent Identity | 4 | 6-10 | 3-5 | 50% | High |
```

This format enables stakeholders to see both the baseline effort and the AI-accelerated projection at a glance, quantifying the value of AI tooling investment.


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
  "dimensions": ["moda", "ara"],
  "mode": "unified | moda-only | ara-only",
  "moda_report_date": "YYYY-MM-DD or null",
  "ara_report_date": "YYYY-MM-DD or null",
  "moda_report_dates": {
    "service-id-1": "YYYY-MM-DD",
    "service-id-2": "YYYY-MM-DD"
  },
  "ara_report_dates": {
    "service-id-1": "YYYY-MM-DD",
    "service-id-2": "YYYY-MM-DD"
  }
}
```

### JSON Schema (Top-Level Keys)

The portfolio execution plan JSON artifact MUST emit these top-level keys:

| Key | Description |
|-----|-------------|
| `metadata` | Analysis type, date, TD version, portfolio name, services count, dimensions, mode, team size, risk tolerance, report sources |
| `executive_summary` | Feasibility, total effort, calendar duration, top risks, pathways planned (MODA), blockers addressed (ARA), services in/out of scope, decision point count |
| `portfolio_input` | Per-service input data from both dimensions. MODA: scores, triggered pathways, classification. ARA: classification tier, blocker count, risk counts |
| `modernization_work_streams` | (when `has_moda`) ONE per unique triggered pathway. Each contains: id, name, dimension:"modernization", pathway, services, objective, prerequisites, effort_weeks_traditional, effort_weeks_ai_accelerated, ai_acceleration_pct, risk_level, phases with tasks (each task has effort_days_traditional + effort_days_ai_accelerated), success_criteria |
| `agent_readiness_work_streams` | (when `has_ara`) ONE per ARA category with BLOCKERs/RISKs. Each contains: id, name, dimension:"agent-readiness", ara_category, services, blockers, risks, objective, prerequisites, effort_weeks_traditional, effort_weeks_ai_accelerated, ai_acceleration_pct, risk_level, phases with tasks, success_criteria |
| `cross_dimension_dependencies` | (when `mode == "unified"`) Array of dependencies between MODA and ARA work streams with source_ws, target_ws, type, rationale |
| `timeline` | Phases (start/end week using AI-accelerated estimates), milestones, critical path (spanning both dimensions), parallelization strategy. Includes `timeline_traditional` as reference. |
| `risk_register` | Sequential risks (RISK-001...) with category (including AgentSafety), description, likelihood, impact, mitigation, contingency, affected services, owner, trigger |
| `cost_estimation` | Engagement-level flag, dual projections: `traditional` and `ai_accelerated` (each with people/infrastructure/training/total three-point estimates). Includes `savings_summary` with absolute and percentage savings. |
| `ai_acceleration_summary` | Portfolio-wide acceleration stats: total_traditional_weeks, total_ai_accelerated_weeks, overall_acceleration_pct, weeks_saved, per_work_stream breakdown, task_category_distribution (how much effort falls in high/medium/minimal acceleration buckets) |
| `success_metrics` | Leading indicators, lagging indicators (MODA + ARA), exit criteria |
| `assumptions` | Array of assumption strings |
| `decision_points` | Sequential DPs (DP-001...) with question, options (>=2), recommendation, deadline, affected services |

### Key Structural Invariants

1. **One work stream per pathway/category** — MODA: `modernization_work_streams[].pathway` values are unique. ARA: `agent_readiness_work_streams[].ara_category` values are unique.
2. **Task IDs globally unique** — no two tasks across any work stream (MODA or ARA) share an ID
3. **Effort ordering** — all three-point estimates satisfy optimistic <= expected <= pessimistic
4. **No phantom services** — every service referenced in work streams must have a corresponding report in the consumed portfolio report(s)
5. **No phantom pathways/categories** — every pathway in MODA work streams must be triggered in the portfolio MODA report; every ARA category in agent-readiness work streams must have findings in the portfolio ARA report
6. **Prerequisites are acyclic** — work stream prerequisites (including cross-dimension) must not form circular dependencies
7. **Shared tasks are dependencies** — in multi-service work streams, shared infrastructure tasks are listed as dependencies of per-service tasks
8. **Cost is engagement-level** — `cost_estimation.engagement_level` is always `true`
9. **Traceability** — MODA tasks have `moda_trace` linking to source service and question; ARA tasks have `ara_trace` linking to `question_id` and `repo_name`
10. **Severity-to-priority** — ARA BLOCKERs produce mandatory (P0) tasks; RISK-SAFETY produces P1; RISK-QUALITY produces P2


## Constraints and Guardrails

- **Read-only analysis**: Do not modify any source code, configuration, or infrastructure. Only create the output portfolio artifact bundle (MD, JSON, HTML, and metadata.json).
- **Stay on the current branch**: Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out.
- **At least one report required**: The TD requires at least one of: portfolio MODA report OR portfolio ARA report. Terminate with error if neither exists.
- **Layered input**: Primary inputs are the portfolio MODA and/or ARA reports (aggregated). Per-service reports are secondary/enrichment only — never re-aggregate from them. The portfolio TDs handle aggregation; this TD handles planning.
- **Graceful degradation**: If only one dimension is available, produce the plan for that dimension only. If per-service reports are unavailable, produce the plan using portfolio-level data only. Never fail because a per-service report is missing or because one dimension's portfolio report is absent.
- **Minimum 2 services**: Terminate with a clear error if any available portfolio report assessed fewer than 2 services.
- **Deduplication**: Each triggered MODA pathway produces exactly one modernization work stream. Each ARA category with findings produces exactly one agent-readiness work stream. Never create per-service work streams for the same pathway/category.
- **Engagement-level scope**: Cost, effort, timeline, and risk are all at the portfolio/engagement level — not per-service.
- **Evidence-based**: All work streams trace to specific MODA pathway triggers or ARA findings and service IDs. Do not generate work streams for untriggered pathways or categories without findings.
- **No hallucination**: Only reference services that have reports. Only reference pathways/categories that exist in the consumed reports. Do not invent services, pathways, findings, or ARA categories.
- **Preferences for framing only**: Technology preferences influence recommendation language but do not change pathway logic, effort estimates, or feasibility assessments.
- **Task granularity**: All tasks must be 1-10 days of effort (1-2 week tasks). If larger, decompose further.
- **Sequential IDs**: Work stream IDs (WS-01, WS-02), risk IDs (RISK-001, RISK-002), decision point IDs (DP-001, DP-002) are sequential with no gaps. MODA work streams are numbered first, then ARA work streams continue the sequence.


## Error Handling

### No Reports Found

IF neither the portfolio MODA report nor the portfolio ARA report is found at the expected paths, THEN terminate with: "Portfolio execution plan generation failed: neither portfolio MODA report nor portfolio ARA report found. At least one must exist."

### Invalid Report

IF a found report is invalid JSON or missing required schema fields, THEN terminate with: "Portfolio execution plan generation failed: {report_type} report found but invalid at {path}."

### Insufficient Services

IF any available portfolio report's `metadata.services_assessed` is fewer than 2, THEN terminate with: "Portfolio execution plan generation failed: requires portfolio report covering at least 2 services. Found {N} in {report_type}."

### No Actionable Findings

IF MODA has no triggered pathways AND ARA has no BLOCKERs or RISKs, emit a minimal plan: "Analysis identified no actionable work across {N} services. Portfolio is either already mature (MODA) and agent-ready (ARA), or no findings met threshold. Recommend periodic re-evaluation."

### Infeasible Timeline

IF calculated timeline exceeds `timeline_constraint` by >50% AND risk_tolerance is aggressive, set feasibility to "Red". Otherwise if pathways >= 4 or total effort > 40 weeks, set feasibility to "Yellow". Emit structured recommendations: (a) increase team size, (b) reduce scope (defer pathways), (c) accept extended timeline.
