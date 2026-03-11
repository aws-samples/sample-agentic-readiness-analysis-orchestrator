# V2 Design: Goal-Driven Agentic Readiness Assessment

> This document captures ALL agreed design decisions from the brainstorming sessions.
> It is the single source of truth for implementation — follow it across sessions without context loss.
> **Status**: Ready for implementation. Follow the [Implementation Order](#12-implementation-order).

---

## Table of Contents

1. [Context & Motivation](#1-context--motivation)
2. [What Is NOT Changing](#2-what-is-not-changing)
3. [Goal-Driven Priority Lens](#3-goal-driven-priority-lens)
4. [Smart Repo Classification](#4-smart-repo-classification)
5. [Pathway Table Improvements](#5-pathway-table-improvements)
6. [Goal-Scoped Decomposition Section](#6-goal-scoped-decomposition-section)
7. [Quick Agent Wins Section](#7-quick-agent-wins-section)
8. [Simplified Config Schema](#8-simplified-config-schema)
9. [Portfolio Assessment Changes](#9-portfolio-assessment-changes)
10. [AWS Programs Section (Portfolio Only)](#10-aws-programs-section-portfolio-only)
11. [POWER.md Updates](#11-powermd-updates)
12. [Implementation Order](#12-implementation-order)
13. [Open Questions (Resolved)](#13-open-questions-resolved)
14. [File Inventory & Change Map](#14-file-inventory--change-map)

---

## 1. Context & Motivation

This project is an **AWS Transform (ATX) custom transformation** that evaluates code repositories
against **56 criteria** across **5 categories**, maps to **7 AWS Modernization Pathways**, and
produces structured readiness reports.

The system has three components:
- **Individual assessment** (`individual-aws-agentic-assessment/transformation_definition.md`) — evaluates a single repo
- **Portfolio assessment** (`portfolio-agentic-assessment/transformation_definition.md`) — aggregates individual reports into a portfolio view
- **Kiro Power** (`agentic-assessment-orchestrator/POWER.md`) — orchestrates both via `atx custom def exec`

**Who consumes these reports:**
- AWS Modernization Specialists running EBA (Experience-Based Acceleration) engagements
- Customer decision-makers evaluating modernization investments

Each triggered pathway = a qualified engagement opportunity (EBA Move to Containers, EBA Move to Managed Databases, etc.).

**Why V2:**
The current assessment is goal-agnostic — it treats all 56 criteria equally regardless of what the customer actually wants to achieve. A customer focused on agentic AI enablement gets the same decomposition-heavy report as one focused on cost optimization. V2 introduces a goal-driven lens that re-weights priorities, adjusts report framing, and eliminates noise.

---

## 2. What Is NOT Changing

These elements remain exactly as-is:

- The **56 assessment criteria** themselves (INF-Q1 through OPS-Q12)
- The **5 category structure** (Infrastructure, Application, Data, Security, Operations)
- The **1–4 scoring scale** and scoring definitions
- The **7 AWS Modernization Pathways** (all still evaluated for every repo)
- The **pathway trigger rules** (same conditions trigger the same pathways)
- The **learning materials catalog** (same links, same modules)
- The **evidence-based approach** (IaC is ground truth, absence is evidence, read before judging)
- The **`atx custom def exec`** execution model and CLI flags

---

## 3. Goal-Driven Priority Lens

### Core Concept

The goal is a **priority lens**, not a filter. All 7 pathways still get evaluated for every repo.
The goal changes:
- Which pathways are **highlighted as primary** vs secondary opportunities
- How the **roadmap phases are named and sequenced**
- Which criteria are **emphasized** in the Top Priorities section
- Whether certain report sections appear (decomposition, quick agent wins)
- The **framing and tone** of recommendations

### Predefined Goals

Four predefined goals cover ~80% of engagements. If someone needs something different, they use
`general-readiness` + `goal_context` with a detailed description.

#### `agentic-ai-enablement`

- **Description**: Enable the portfolio to support agentic AI workflows — autonomous agents that can discover, invoke, and orchestrate application capabilities as tools.
- **Primary pathways**: Move to AI, Move to Managed Databases (vector/RAG), Move to Modern DevOps (observability)
- **Phase names** (individual report):
  - Phase 1 — Agent Quick Wins (Days 1–30)
  - Phase 2 — Agent Foundations (Months 1–3)
  - Phase 3 — Agent Scale & Optimization (Months 3–6)
- **Priority criteria**: APP-Q2 (API docs), APP-Q13 (AI frameworks), DATA-Q1/Q2/Q3 (vector DB, RAG), SEC-Q7 (human approval), OPS-Q3 (evals), OPS-Q6 (LLM cost tracking)

#### `cloud-native-modernization`

- **Description**: Decompose and modernize applications into cloud-native architectures using managed services, containers, and serverless.
- **Primary pathways**: Move to Cloud Native, Move to Containers, Move to Modern DevOps
- **Phase names** (individual report):
  - Phase 1 — Containerize & Automate (Days 1–30)
  - Phase 2 — Decompose & Decouple (Months 1–3)
  - Phase 3 — Optimize & Scale (Months 3–6)
- **Priority criteria**: APP-Q4 (monolith), INF-Q1 (compute), INF-Q5 (IaC), INF-Q6 (CI/CD), APP-Q3 (async), OPS-Q9 (deployment strategy)

#### `cost-optimization`

- **Description**: Reduce operational costs through license elimination, managed service adoption, and right-sizing.
- **Primary pathways**: Move to Open Source, Move to Managed Databases, Move to Managed Analytics
- **Phase names** (individual report):
  - Phase 1 — License & Quick Savings (Days 1–30)
  - Phase 2 — Managed Service Migration (Months 1–3)
  - Phase 3 — Optimization & Governance (Months 3–6)
- **Priority criteria**: INF-Q2 (managed DB), DATA-Q2 (managed vector), DATA-Q10 (DB EOL), DATA-Q11 (stored procedures/commercial SQL), INF-Q8 (managed streaming)

#### `general-readiness`

- **Description**: Comprehensive assessment across all dimensions with no specific weighting. Suitable when the modernization direction hasn't been decided yet.
- **Primary pathways**: All pathways evaluated equally
- **Phase names** (individual report):
  - Phase 1 — Quick Wins (Days 1–30)
  - Phase 2 — Foundation (Months 1–3)
  - Phase 3 — Advanced Capabilities (Months 3–6)
- **Priority criteria**: All criteria weighted equally

### `goal_context` Free-Text Field

Optional. Gives the agent additional context for scoping recommendations.

Example: `"We're building a customer support agent that needs access to our order and inventory data"`

This influences:
- The Quick Agent Wins section (what specific agent use cases to suggest)
- Which services matter most in the portfolio view
- Framing of recommendations

### Handling Unknown Goals

- If `goal` is not one of the 4 predefined values → treat as `general-readiness`
- Log a warning: "Unrecognized goal '{value}', defaulting to general-readiness"
- The `goal_context` field still gets passed through and used for framing

### How Goal Affects the Individual Report

The transformation definition must include a new section (before Step 1) that:

1. Reads the `goal` from `additionalPlanContext` (defaults to `general-readiness` if absent)
2. Reads `goal_context` if present
3. Uses the goal to:
   - Select phase names for the Readiness Roadmap (Step 8)
   - Prioritize the Top 5 Critical Gaps — goal priority criteria rank higher
   - Add "Goal Alignment" column to the pathway table (High/Medium/Low)
   - Control whether decomposition section appears (see [Section 6](#6-goal-scoped-decomposition-section))
   - Control whether Quick Agent Wins section appears (see [Section 7](#7-quick-agent-wins-section))

### How Goal Affects the Portfolio Report

- Portfolio-level `goal` takes precedence over any per-repo context
- Phase 0 is always "Cross-Cutting Foundation" regardless of goal
- Phases 1–3 get goal-specific names (see portfolio phase examples below)
- Cross-cutting concerns split into "blocking your goal" vs "general opportunities"
- Roadmap activities re-weighted by goal alignment

**Portfolio phases by goal:**

| Goal | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|---------|
| `agentic-ai-enablement` | Cross-Cutting Foundation (Mo 0–1) | Agent Quick Wins (Mo 1–2) | Agent Foundations (Mo 2–4) | Agent Scale & Optimization (Mo 4–6+) |
| `cloud-native-modernization` | Cross-Cutting Foundation (Mo 0–1) | Containerize & Automate (Mo 1–2) | Decompose & Decouple (Mo 2–4) | Optimize & Scale (Mo 4–6+) |
| `cost-optimization` | Cross-Cutting Foundation (Mo 0–1) | License & Quick Savings (Mo 1–2) | Managed Service Migration (Mo 2–4) | Optimization & Governance (Mo 4–6+) |
| `general-readiness` | Cross-Cutting Foundation (Mo 0–1) | Quick Wins (Mo 1–2) | Foundation (Mo 2–4) | Advanced Capabilities (Mo 4–6+) |

---

## 4. Smart Repo Classification

### Problem

People have IaC and deployment configs centralized sometimes, sometimes alongside the application.
An infrastructure-only repo shouldn't get a full 56-criteria assessment — APP-Q1 through APP-Q13
are meaningless for a Terraform-only repo.

### Solution

The agent auto-detects repo type during Step 1 (Discovery). One transformation definition handles
all types — no separate definitions per repo type.

### Repo Types

| Type | Description | Example |
|------|-------------|---------|
| `application` | Contains application source code (the default) | Java service, Python API, Node.js app |
| `infrastructure-only` | Only IaC, no application code | Terraform modules, CDK stacks, CloudFormation templates |
| `deployment-cicd` | CI/CD pipelines, deployment scripts, no app code | GitHub Actions workflows, Jenkinsfiles, Helm charts |
| `monorepo` | Multiple services/apps in one repo | Monorepo with `services/`, `packages/` dirs |
| `library` | Shared library/SDK, not a deployable service | Internal SDK, shared utilities package |

### Detection Logic (added to Step 1)

After the file discovery scan, the agent classifies the repo:

1. If source code files (.py, .java, .js, .ts, .go, .cs) exist → likely `application` or `monorepo`
2. If ONLY IaC files exist (no source code) → `infrastructure-only`
3. If ONLY CI/CD definitions exist → `deployment-cicd`
4. If multiple independent service directories with separate build configs → `monorepo`
5. If package manifest exists but no deployable entry point (no Dockerfile, no IaC, no main) → `library`
6. User can override via config: `repo_type: "infrastructure-only"` (optional field)

### Scoring Impact

Criteria that don't apply to the detected repo type are scored as **N/A** with an explanation,
and **excluded from category averages**.

| Repo Type | Criteria Scored as N/A |
|-----------|----------------------|
| `infrastructure-only` | APP-Q1 through APP-Q13, DATA-Q1 through DATA-Q9, DATA-Q11 |
| `deployment-cicd` | APP-Q1 through APP-Q13, DATA-Q1 through DATA-Q11, INF-Q1 through INF-Q4, INF-Q7 through INF-Q10 |
| `library` | INF-Q1 through INF-Q10, OPS-Q4 through OPS-Q12 (no deployment = no ops) |
| `monorepo` | All criteria apply, but assessed per-service within the repo |
| `application` | All 56 criteria apply (default behavior) |

### Report Display for N/A Criteria

```markdown
#### APP-Q1: Programming Languages
- **Score**: N/A
- **Finding**: This is an infrastructure-only repository. Application architecture criteria do not apply.
- **Gap**: N/A
- **Recommendation**: N/A
```

Category averages only include scored criteria:
- If Infrastructure has 10 criteria but 3 are N/A, average is calculated from the 7 scored ones
- Overall score is average of the 5 category scores (each already adjusted for N/A)

---

## 5. Pathway Table Improvements

### Current State (V1)

The pathway table has two columns: Triggered (Yes/No) and Priority.

### New State (V2)

Three changes to the pathway summary table in individual reports:

1. **Three statuses** instead of Yes/No:
   - **Triggered** — pathway trigger conditions met
   - **Not Triggered** — trigger conditions not met, but pathway still listed
   - **Not Applicable** — with reason (e.g., "Infrastructure-only repo — no application compute to containerize")

2. **New "Goal Alignment" column** — High/Medium/Low based on whether the pathway is a primary pathway for the selected goal

3. **Priority only shown for Triggered pathways** — Not Triggered and N/A show "—"

### New Table Format

```markdown
| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | High | High | APP-Q4: 1/4, INF-Q1: 1/4 | High |
| Move to Containers | Triggered | High | High | INF-Q1: 1/4 | Medium |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Triggered | Medium | Medium | INF-Q2: 2/4 | Medium |
| Move to Managed Analytics | Not Applicable | Low | — | Infra-only repo | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q5: 1/4, INF-Q6: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4 | High |
```

### Goal Alignment Rules

| Goal | High Alignment | Medium Alignment | Low Alignment |
|------|---------------|-----------------|--------------|
| `agentic-ai-enablement` | Move to AI, Move to Managed Databases, Move to Modern DevOps | Move to Cloud Native, Move to Containers | Move to Open Source, Move to Managed Analytics |
| `cloud-native-modernization` | Move to Cloud Native, Move to Containers, Move to Modern DevOps | Move to Managed Databases, Move to Open Source | Move to AI, Move to Managed Analytics |
| `cost-optimization` | Move to Open Source, Move to Managed Databases, Move to Managed Analytics | Move to Containers, Move to Modern DevOps | Move to Cloud Native, Move to AI |
| `general-readiness` | All Medium | — | — |

---

## 6. Goal-Scoped Decomposition Section

### Problem

The current Microservices Decomposition Strategy section is extensive (Strangler Fig, EventStorming,
pattern recommendations, etc.). When the goal is `agentic-ai-enablement`, this content pollutes
the report — the customer doesn't care about decomposition patterns, they want to know about
agent tools and RAG pipelines.

### Rules

| Goal | Decomposition Section Behavior |
|------|-------------------------------|
| `cloud-native-modernization` | **Full section** — all decomposition options, patterns, LoE estimates (current V1 behavior) |
| `general-readiness` | **Full section** — same as cloud-native |
| `agentic-ai-enablement` | **Condensed paragraph** — "This monolith would benefit from service extraction to create clear agent tool boundaries. See the Move to Cloud Native pathway for decomposition guidance. For now, agents can interact with the monolith via its existing API surface." |
| `cost-optimization` | **Skip entirely** unless decomposition directly reduces cost (e.g., extracting a service to move from commercial DB to open source). If relevant, include a brief note only. |

### Implementation

In Step 8 (Generate Report), the decomposition section is conditionally included based on the goal.
The trigger condition (APP-Q4 < 4) still determines IF a monolith exists — the goal determines
HOW MUCH decomposition guidance to include.

---

## 7. Quick Agent Wins Section

### What It Is

A new section in individual reports that identifies immediately actionable agent opportunities,
even for low-scoring repos. The message: "even though your overall score is 1.5, you could build
a RAG-based internal knowledge agent using your existing API docs as a starting point."

Modernization and agent adoption can happen in parallel, not sequentially.

### When It Appears

| Goal | Quick Agent Wins Section |
|------|------------------------|
| `agentic-ai-enablement` | **Always included** — this is the primary value of the assessment |
| `general-readiness` | **Included** — useful context for any assessment |
| `cloud-native-modernization` | **Not included** — focus is on architecture, not agents |
| `cost-optimization` | **Not included** — focus is on cost reduction |

### Content Structure

```markdown
## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are
available based on your current architecture:

1. **<Win Title>** — <1-2 sentence description of what agent could be built now>
   - **Leverages**: <existing capability found in assessment, e.g., "OpenAPI spec at /api/swagger.json">
   - **Effort**: Low/Medium
   - **Value**: <what it enables>

2. **<Win Title>** — ...

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.
```

### How the Agent Identifies Wins

The agent looks for existing capabilities that can be leveraged:
- API documentation exists (APP-Q2 ≥ 2) → "Build an API-aware agent that can discover and invoke your existing endpoints"
- Structured JSON responses (APP-Q5 ≥ 3) → "Agent tool integration is straightforward with your JSON APIs"
- Existing docs/README/wiki content → "Build a RAG-based knowledge agent using your existing documentation"
- Database with clear schema (DATA-Q7 ≥ 2) → "Build a data query agent with natural language to SQL"
- CI/CD pipeline exists (INF-Q6 ≥ 2) → "Build a DevOps agent that can trigger deployments and check status"

If `goal_context` is provided, the agent tailors wins to that context.

### Portfolio Aggregation

At portfolio level, Quick Agent Wins are aggregated across repos:
- Group by win type (e.g., "3 repos have API docs suitable for agent tool discovery")
- Identify cross-repo agent opportunities (e.g., "Build a unified agent that orchestrates across service-a and service-b APIs")
- Prioritize by goal alignment and effort

---

## 8. Simplified Config Schema

### Individual Assessment Config

The individual assessment receives config via `additionalPlanContext` in the ATX config file.
The current verbose format with nested `database_constraints`, `deployment_constraints`,
`compliance_requirements`, etc. is replaced with a flat, simple structure.

**New individual `additionalPlanContext` format:**

```yaml
goal: "agentic-ai-enablement"
goal_context: "Building a customer support agent for order and inventory data"
repo_type: "application"          # optional — agent auto-detects if absent
context: "Legacy PHP e-commerce app running on EC2 with MySQL"  # optional free text
preferences:
  prefer: ["eks", "containers"]
  avoid: ["serverless"]
priority: "P0"                    # from portfolio config, passed through
tags: ["monolith", "php"]         # from portfolio config, passed through
```

That's it. No nested constraint objects. The `preferences.prefer` and `preferences.avoid` arrays
replace all of: `avoid_technologies`, `prefer_technologies`, `avoid_patterns`, `prefer_patterns`,
`database_constraints`, `deployment_constraints`, etc.

The agent interprets preferences intelligently:
- `avoid: ["serverless"]` → don't recommend Lambda, prefer containers
- `prefer: ["eks", "aurora"]` → recommend EKS for compute, Aurora for databases
- `avoid: ["microservices-decomposition"]` → keep as monolith, focus on containerization

### Portfolio Config (portfolio-config.yaml)

**New simplified format:**

```yaml
portfolio_name: "ecommerce-platform"
goal: "agentic-ai-enablement"
goal_context: "Building customer-facing AI agents for support and order management"

transformation_definitions:
  individual_assessment: "individual-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka"]

repositories:
  - name: "service-a"
    path: "./services/a"
    priority: "P0"
    context: "Main order processing service, handles 80% of traffic"  # optional
    preferences:                                                       # optional, merges with global
      prefer: ["dynamodb"]
      avoid: ["rds"]

  - name: "service-b"
    path: "./services/b"
    priority: "P1"
    tags: ["infrastructure"]

  - name: "infra-repo"
    path: "./infrastructure"
    repo_type: "infrastructure-only"   # optional override
    priority: "P2"

dependency_overrides:                  # stays at portfolio level
  - source: "service-a"
    target: "service-b"
    type: "sync"
    description: "REST API calls for inventory checks"
```

### What Was Removed from Per-Repo Config

All of these nested objects are gone from per-repo `transformation_preferences`:
- `database_constraints` (avoid_migration, keep_current_database, avoid_managed_services)
- `deployment_constraints` (avoid_containers, avoid_orchestration, prefer_vm_based)
- `compliance_requirements`
- `budget_constraints`
- `timeline_constraints`
- `modernization_approach`
- `avoid_microservices_decomposition` / `keep_as_monolith`
- `avoid_patterns` / `prefer_patterns`
- `custom_constraints`

All replaced by the flat `preferences.prefer` / `preferences.avoid` arrays + `context` free text.

### What Was Removed from Global Config

Same simplification at portfolio level:
- `global_transformation_preferences` → replaced by top-level `preferences`
- `transformation_options` → removed (output path, thresholds, etc. are defaults in the transformation definition)
- `exclusions` → removed (handle via not listing the repo)
- `metadata` → removed (organization, contact_email, aws_account_ids — not used by the assessment)

### What Stays

- `portfolio_name` — required
- `goal` — new, required (defaults to `general-readiness`)
- `goal_context` — new, optional
- `transformation_definitions` — required (unchanged)
- `preferences` — new simplified format (global level)
- `repositories` — required, simplified per-repo fields
- `dependency_overrides` — stays at portfolio level (unchanged)

### Schema File

Replace `portfolio-config.schema.json` with the new simplified schema.
The old schema is not backward-compatible — this is a breaking change.
Old example configs in `example-reports/example-transform-custom-additional-context/` will need updating.

---

## 9. Portfolio Assessment Changes

The portfolio transformation definition needs aligned changes to consume the new individual
report format and produce goal-aware portfolio output.

### Parsing Changes (Step 2)

- Parse the new N/A criteria format — understand that some criteria may be N/A due to repo type
- Extract `repo_type` from individual reports (agent will include it in the report metadata)
- Extract `goal_alignment` from pathway tables
- Parse Quick Agent Wins sections when present

### Pathway Aggregation Table (New)

Portfolio report gets a new aggregation view showing repos per pathway:

```markdown
### Portfolio Pathway Aggregation

| Pathway | Triggered | Not Triggered | Not Applicable | Goal Alignment |
|---------|-----------|---------------|----------------|---------------|
| Move to Cloud Native | service-a, service-b | books-api | infra-repo | High |
| Move to Containers | service-a, service-b, books-api | — | infra-repo | High |
| Move to AI | service-a | service-b, books-api | infra-repo | High |
| ... | ... | ... | ... | ... |
```

### Cross-Cutting Concerns Split

Currently all cross-cutting concerns are listed together. V2 splits them:

1. **Blocking Your Goal** — cross-cutting gaps in goal-priority criteria
   - Example (agentic-ai-enablement): "4 of 5 repos lack API documentation (APP-Q2 < 3) — this blocks agent tool discovery across the portfolio"

2. **General Opportunities** — cross-cutting gaps in non-priority criteria
   - Example: "3 of 5 repos lack auto-scaling (INF-Q10 < 3) — important but not blocking agentic enablement"

### Roadmap Phase Changes

- Phase 0 always "Cross-Cutting Foundation" regardless of goal
- Phases 1–3 use goal-specific names (see table in [Section 3](#3-goal-driven-priority-lens))
- Activities within each phase re-weighted by goal alignment
- Phase assignment algorithm unchanged (fan-in/fan-out/blast radius logic stays)

### Quick Agent Wins Aggregation (New Section)

When goal is `agentic-ai-enablement` or `general-readiness`:

```markdown
### Portfolio Quick Agent Wins

Across the portfolio, these agent opportunities are immediately available:

**API-Aware Agents** (3 repos: service-a, service-b, books-api)
- All three have OpenAPI specs. A unified agent could discover and invoke APIs across services.

**Cross-Service Orchestration** (service-a → service-b)
- Order processing (service-a) and inventory (service-b) have clear API contracts.
  A multi-tool agent could orchestrate order-to-fulfillment workflows.

**Documentation RAG** (all repos)
- Combined README and API docs across the portfolio provide a knowledge base for
  an internal developer support agent.
```

---

## 10. AWS Programs Section (Portfolio Only)

### What It Is

A new section in the **portfolio report only** that maps assessment findings to relevant
AWS engagement programs. This makes the report directly actionable for Modernization Specialists
who need to identify which programs to propose to the customer.

### Programs Catalog

Based on Module 8 (Orchestration & Programs) from the learning plan:

| Program | Acronym | Trigger Signal from Assessment |
|---------|---------|-------------------------------|
| Migration Acceleration Program | MAP | Portfolio has 3+ repos needing significant modernization (overall score < 2.5) |
| Optimization and Licensing Assessment | OLA | Any repo has Oracle, SQL Server, VMware, or commercial license findings (DATA-Q11, INF-Q2) |
| Microsoft Modernization Program | MMP | Any repo has .NET/Windows workloads detected (APP-Q1 findings) |
| VMware Modernization Program | VMP | Any repo has VMware references in IaC or deployment configs |
| Windows App Modernization Program | WAMP | Any repo has Windows-based deployment targets |
| Experience-Based Acceleration | EBA | Each triggered pathway = potential EBA engagement (EBA Move to Containers, EBA Move to Managed Databases, etc.) |
| ISV Workload Migration Program | ISV WMP | Portfolio is an ISV SaaS platform being modernized |
| Cloud Economics | CE | Goal is `cost-optimization` OR portfolio has significant licensing costs |

### Report Format

```markdown
## AWS Programs & Engagement Recommendations

Based on the portfolio assessment findings, the following AWS programs may accelerate
your modernization journey:

### Recommended Programs

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| EBA — Move to Containers | High | 3 repos need containerization (INF-Q1 < 3) | Request EBA engagement via SA |
| EBA — Move to Managed Databases | High | 2 repos have self-managed DBs (INF-Q2 < 4) | Request EBA engagement via SA |
| OLA | Medium | Oracle DB detected in service-a | Request OLA for licensing analysis |
| MAP | Medium | Portfolio-wide modernization effort is High | Evaluate MAP eligibility |

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.
```

### Why Portfolio Only

Programs are engagement-level decisions, not per-repo. You don't run an OLA for one repo —
you run it for the customer's Oracle estate. The portfolio view has the right scope to make
these recommendations.

---

## 11. POWER.md Updates

The Kiro Power (`agentic-assessment-orchestrator/POWER.md`) orchestrates both assessments.
It needs these changes:

### 1. Read Goal from Portfolio Config

When parsing `portfolio-config.yaml`, extract:
- `goal` (required, default `general-readiness`)
- `goal_context` (optional)
- `preferences` (new simplified format)

### 2. Validate Goal Value

- Must be one of: `agentic-ai-enablement`, `cloud-native-modernization`, `cost-optimization`, `general-readiness`
- If unrecognized → warn and default to `general-readiness`
- If missing → default to `general-readiness`

### 3. Pass Goal to Individual Assessments

When generating the per-repo ATX config file (`additionalPlanContext`), include:
```yaml
goal: "agentic-ai-enablement"           # from portfolio config
goal_context: "Building customer support agent..."  # from portfolio config
repo_type: "application"                 # from per-repo config if specified
context: "Legacy PHP e-commerce app"     # from per-repo config
preferences:
  prefer: ["eks"]                        # merged: global + per-repo
  avoid: ["serverless"]                  # merged: global + per-repo
priority: "P0"                           # from per-repo config
tags: ["monolith", "php"]               # from per-repo config
```

Preference merging: per-repo `prefer`/`avoid` arrays are appended to global arrays.
If a value appears in both global `prefer` and per-repo `avoid`, per-repo wins (more specific).

### 4. Pass Goal to Portfolio Assessment

When generating the portfolio-level ATX config file, include:
```yaml
goal: "agentic-ai-enablement"
goal_context: "Building customer support agent..."
preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka"]
# ... plus the existing service inventory, dependency overrides, etc.
```

### 5. Generate Simplified Config Format

The Quick Start section and config generation examples in POWER.md must use the new
simplified format (no nested constraint objects).

### 6. Update Config Validation

The Power currently validates the old schema fields. Update to validate:
- `goal` is a valid predefined value (or absent → default)
- `preferences` has `prefer` and/or `avoid` arrays (both optional)
- Per-repo fields: `name`, `path` required; `priority`, `context`, `preferences`, `repo_type`, `tags` optional
- `dependency_overrides` unchanged

---

## 12. Implementation Order

Execute in this order. Each step builds on the previous.

### Step 1: Individual Assessment Transformation Definition
**File**: `individual-aws-agentic-assessment/transformation_definition.md`
**Changes**:
- Add new "Step 0: Read Goal & Classify Repo" before current Step 1
  - Read `goal`, `goal_context`, `repo_type`, `context`, `preferences` from additionalPlanContext
  - Default goal to `general-readiness` if absent
  - Auto-detect repo type during discovery (Step 1) if not provided
- Modify Step 1 (Discovery) to include repo type classification logic
- Modify scoring steps (2–6) to handle N/A criteria based on repo type
- Modify Step 7 (Pathway Mapping) to:
  - Add "Not Applicable" status for repos where pathway doesn't apply
  - Add "Goal Alignment" column
- Modify Step 8 (Report Generation) to:
  - Use goal-specific phase names
  - Conditionally include/exclude decomposition section based on goal
  - Add Quick Agent Wins section (when goal is `agentic-ai-enablement` or `general-readiness`)
  - Add Goal Alignment to pathway table
  - Add repo type and goal to report metadata header
  - Adjust Top 5 Priorities to weight goal-priority criteria higher
- Update report template with new sections and table format
- Update Constraints and Guardrails with new rules for N/A scoring and goal handling
- Update Validation / Exit Criteria to include new sections

### Step 2: Portfolio Assessment Transformation Definition
**File**: `portfolio-agentic-assessment/transformation_definition.md`
**Changes**:
- Modify Step 2 (Parse) to handle N/A criteria, repo types, goal alignment from individual reports
- Add pathway aggregation table (repos per pathway with Triggered/Not Triggered/N/A)
- Split cross-cutting concerns into "blocking your goal" vs "general opportunities"
- Use goal-specific phase names for Phases 1–3 (Phase 0 always "Cross-Cutting Foundation")
- Add Quick Agent Wins aggregation section
- Add AWS Programs section (new Step, after Risk Assessment)
- Update report template with all new sections
- Read `goal` and `goal_context` from additionalPlanContext

### Step 3: Config Schema
**File**: `portfolio-config.schema.json`
**Changes**:
- Replace entirely with new simplified schema
- Add `goal` enum field (4 values)
- Add `goal_context` string field
- Replace `global_transformation_preferences` with `preferences: { prefer: [], avoid: [] }`
- Simplify per-repo to: name, path, priority, context, preferences, repo_type, tags, repository_url, report_path
- Remove: transformation_options, exclusions, metadata, all nested constraint objects
- Keep: dependency_overrides (unchanged)

### Step 4: POWER.md
**File**: `agentic-assessment-orchestrator/POWER.md`
**Changes**:
- Update config parsing to read `goal`, `goal_context`, `preferences`
- Add goal validation logic
- Update ATX config generation for individual assessments (pass goal, simplified preferences)
- Update ATX config generation for portfolio assessment (pass goal)
- Update Quick Start examples with new config format
- Update config validation section

### Step 5: README
**File**: `README.md`
**Changes**:
- Document the goal concept and the 4 predefined goals
- Update config examples to new simplified format
- Document repo type classification
- Update any references to old config fields

### Step 6: Example Configs
**Files**: `test-portfolio-config.yaml`, `example-reports/example-transform-custom-additional-context/*.yaml`
**Changes**:
- Rewrite `test-portfolio-config.yaml` in new simplified format
- Update or replace example ATX config files
- Add `goal` field to all examples

### Step 7: Example Reports (Optional / Later)
**Files**: `example-reports/agentic-readiness-assessment/*.md`
**Decision**: Mark as "v1 format" for now. Regenerate after implementation is stable.
These are output artifacts — they'll be regenerated naturally when running the new transformation.

---

## 13. Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Should AWS Programs section be in individual reports too? | **No. Portfolio only.** Programs are engagement-level decisions, not per-repo. |
| Should portfolio roadmap phase names change based on goal? | **Yes.** Phase 0 always "Cross-Cutting Foundation". Phases 1–3 get goal-specific names. |
| Should the Power validate goal values? | **Yes.** Must be one of 4 predefined values. Unknown → default to `general-readiness` with warning. |
| Schema backward compatibility — keep old schema? | **No. Replace it.** This is a breaking change. Old configs won't work with V2. |
| Example report regeneration timing? | **Later.** Mark existing as "v1 format". Regenerate after V2 implementation is stable. |
| Per-repo goal override at portfolio level? | **No.** Portfolio-level goal takes precedence. Per-repo can add `context` but not override the goal. If achieving the goal requires decomposition (e.g., breaking a monolith to enable agents), the assessment handles that naturally through pathway triggers. |
| Should infra/deployment/library repos get full 56-criteria assessment? | **No.** Agent auto-detects repo type and scores inapplicable criteria as N/A, excluded from averages. One transformation definition handles all types. |
| How to handle goals we haven't predefined? | **Use `general-readiness` + `goal_context`.** The 4 predefined goals cover ~80% of engagements. New goals can be added later as patterns emerge. |

---

## 14. File Inventory & Change Map

| File | Change Type | Priority |
|------|------------|----------|
| `individual-aws-agentic-assessment/transformation_definition.md` | **Major rewrite** — goal handling, repo classification, N/A scoring, new report sections | Step 1 |
| `portfolio-agentic-assessment/transformation_definition.md` | **Major rewrite** — goal-aware parsing, pathway aggregation, programs section, split cross-cutting | Step 2 |
| `portfolio-config.schema.json` | **Replace** — new simplified schema | Step 3 |
| `agentic-assessment-orchestrator/POWER.md` | **Moderate update** — goal passthrough, simplified config generation, validation | Step 4 |
| `README.md` | **Moderate update** — document goals, new config format, repo types | Step 5 |
| `test-portfolio-config.yaml` | **Rewrite** — new simplified format | Step 6 |
| `example-reports/example-transform-custom-additional-context/*.yaml` | **Rewrite** — new simplified format | Step 6 |
| `example-reports/agentic-readiness-assessment/*.md` | **Skip for now** — mark as v1, regenerate later | Step 7 |
| `portfolio-schema-example.yaml` | **Rewrite** — new simplified format | Step 6 |

### Reference Files (Read-Only, Do Not Modify)

| File | Purpose |
|------|---------|
| `modernization_tab_enhanced.md` | Module 8 AWS Programs reference (MAP, OLA, MMP, VMP, WAMP, EBA, etc.) |
| `example-reports/agentic-readiness-assessment/monolith-agentic-readiness-report.md` | Current V1 report format reference |
| `sprint-plan.svg` | Visual reference |

---

## Appendix: Goal Definition Reference Card

Quick reference for implementers — copy this into the transformation definition.

```
GOAL DEFINITIONS:

agentic-ai-enablement:
  description: "Enable agentic AI workflows — autonomous agents discovering, invoking, orchestrating app capabilities"
  primary_pathways: [Move to AI, Move to Managed Databases, Move to Modern DevOps]
  phases: [Agent Quick Wins, Agent Foundations, Agent Scale & Optimization]
  priority_criteria: [APP-Q2, APP-Q13, DATA-Q1, DATA-Q2, DATA-Q3, SEC-Q7, OPS-Q3, OPS-Q6]

cloud-native-modernization:
  description: "Decompose and modernize into cloud-native architectures"
  primary_pathways: [Move to Cloud Native, Move to Containers, Move to Modern DevOps]
  phases: [Containerize & Automate, Decompose & Decouple, Optimize & Scale]
  priority_criteria: [APP-Q4, INF-Q1, INF-Q5, INF-Q6, APP-Q3, OPS-Q9]

cost-optimization:
  description: "Reduce costs through license elimination, managed services, right-sizing"
  primary_pathways: [Move to Open Source, Move to Managed Databases, Move to Managed Analytics]
  phases: [License & Quick Savings, Managed Service Migration, Optimization & Governance]
  priority_criteria: [INF-Q2, DATA-Q2, DATA-Q10, DATA-Q11, INF-Q8]

general-readiness:
  description: "Comprehensive assessment, no specific weighting"
  primary_pathways: [all equal]
  phases: [Quick Wins, Foundation, Advanced Capabilities]
  priority_criteria: [all equal]
```
