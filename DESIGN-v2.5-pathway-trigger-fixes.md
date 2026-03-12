# V2.5 Design: Pathway Trigger Precision & Goal-Weighted Triggering

> This document captures all agreed design decisions from the V2.5 brainstorming session.
> It is the single source of truth for implementation — follow it across sessions without context loss.
> **Status**: Ready for implementation.
> **Predecessor**: `DESIGN-v2-goal-driven-assessment.md` (V2 is fully implemented; V2.5 builds on it)

---

## Table of Contents

1. [Context & Motivation](#1-context--motivation)
2. [What Is NOT Changing](#2-what-is-not-changing)
3. [Problem Analysis](#3-problem-analysis)
4. [Fix 1: Contextual Relevance Guards](#4-fix-1-contextual-relevance-guards)
5. [Fix 2: Goal-Weighted Trigger Thresholds](#5-fix-2-goal-weighted-trigger-thresholds)
6. [Revised Pathway Trigger Rules](#6-revised-pathway-trigger-rules)
7. [Expected Results Validation](#7-expected-results-validation)
8. [Implementation Order](#8-implementation-order)
9. [File Inventory & Change Map](#9-file-inventory--change-map)

> **Companion Document**: Tiered Common Gaps (originally planned as Fix 3 in this doc)
> has been extracted to its own design document: `DESIGN-v2.5b-tiered-common-gaps.md`.
> That document covers the portfolio report's common gaps classification into three tiers
> (Foundational Blockers, Goal-Specific Prerequisites, Goal Deliverables). It is independent
> of this document and can be implemented separately.

---

## 1. Context & Motivation

V2 introduced goal-driven assessments with 4 predefined goals, repo type classification, and
simplified config. The pathway trigger rules were carried over from V1 with minimal changes —
only a "Goal Alignment" column (High/Medium/Low) was added to the pathway table.

**The problem**: In practice, 5–6 out of 7 pathways trigger for every repository regardless of
the goal or the repo's actual architecture. This makes the assessment noisy and undermines the
goal-driven lens. A customer focused on `agentic-ai-enablement` sees "Move to Managed Analytics"
triggered for a simple CRUD API, and "Move to Cloud Native" triggered for a repo that's already
fully decomposed into Lambda microservices.

**Root causes identified**:
1. Trigger thresholds are too low — most use `< 3` or `< 4`, catching anything not perfect
2. The goal doesn't influence whether a pathway triggers — only the alignment label
3. "Absence of something you never needed" is treated as a gap (no Kinesis = needs analytics)
4. Some pathways conflate different concerns (Cloud Native mixes decomposition with async maturity)

**What V2.5 fixes**: Pathway trigger precision and goal-weighted triggering. No changes to
scoring, criteria, report structure, config schema, or the Power orchestrator.

---

## 2. What Is NOT Changing

These elements remain exactly as-is from V2:

- The **56 assessment criteria** themselves (INF-Q1 through OPS-Q12)
- The **5 category structure** and **1–4 scoring scale**
- The **7 AWS Modernization Pathways** (all still listed in every report)
- The **goal definitions** (4 predefined goals, goal_context, phase names)
- The **repo type classification** and N/A scoring logic
- The **report structure** (sections, tables, Quick Agent Wins, AWS Programs)
- The **config schema** (portfolio-config.yaml format unchanged)
- The **POWER.md** orchestrator (no changes needed)
- The **portfolio assessment** transformation definition (consumes individual reports as-is)
- The **pathway table format** (Status, Goal Alignment, Priority, Key Trigger Criteria, Est. Effort)
- The **Not Applicable rules by repo type** (section 7.3 unchanged)
- The **Goal Alignment column** logic (section 7.4 unchanged)
- The **Move to Open Source** trigger rules (already precise — only fires on commercial licenses)

---

## 3. Problem Analysis

### 3.1 Observed Results (test-portfolio-config.yaml, goal: agentic-ai-enablement)

| Pathway | unishop-monolith | aws-microservices | local-monolith | books-api |
|---------|-----------------|-------------------|----------------|-----------|
| Cloud Native | Triggered | Triggered | Triggered | Triggered |
| Containers | Triggered | Triggered | Triggered | Not Triggered |
| Open Source | Not Triggered | Not Triggered | Not Triggered | Not Triggered |
| Managed Databases | Triggered | Triggered | Triggered | Not Triggered |
| Managed Analytics | Triggered | Triggered | Not Triggered | Triggered |
| Modern DevOps | Triggered | Triggered | Triggered | Triggered |
| Move to AI | Triggered | Triggered | Triggered | Triggered |

That's 5–6 out of 7 triggered per repo. Only Open Source consistently doesn't trigger.

### 3.2 Why Each Over-Trigger Happens

**Move to Cloud Native triggers for aws-microservices (already microservices)**:
- APP-Q4 = 4/4 (correctly recognized as microservices)
- But APP-Q3 = 2/4 (only 8% async) and APP-Q10 = 2/4 (no status polling)
- The OR rule fires on async gaps even though the architecture is already decomposed
- The pathway name implies decomposition, but the criteria catch async maturity gaps

**Move to Cloud Native triggers for books-api (modular serverless)**:
- APP-Q4 = 3/4 (modular Lambda functions)
- But APP-Q3 = 1/4 (fully synchronous) fires the trigger
- A simple CRUD API doesn't need to "Move to Cloud Native" — it IS cloud-native

**Move to Containers triggers for aws-microservices (Lambda-based)**:
- "No Dockerfile found" fires the trigger
- But this is a serverless app — absence of Dockerfile is expected, not a gap

**Move to Managed Analytics triggers for books-api and aws-microservices**:
- INF-Q8 = 1/4 (no Kinesis/MSK) fires the trigger
- But these are CRUD/event-driven apps with no analytics workloads
- Absence of streaming ≠ need for streaming

**Move to Managed Analytics inconsistently NOT triggered for local-monolith**:
- INF-Q8 = 1/4 (same score as the others) but shows "Not Triggered"
- The agent applied the rules inconsistently — a non-determinism problem
- The vague "no managed analytics detected" clause gives the agent wiggle room

**Move to Managed Databases triggers for aws-microservices (DynamoDB = fully managed)**:
- DATA-Q2 = 1/4 (no vector DB) fires the `< 4` threshold
- But DynamoDB is already a managed database — the trigger is really about vector DB absence
- Absence of vector DB is an AI concern, not a managed database concern

### 3.3 Two Root Cause Categories

**Category A — Contextual Relevance**: The trigger rules don't check whether the capability
is actually relevant to the repo. They treat absence as a gap regardless of context.

**Category B — Goal Influence on Triggering**: The goal only affects the alignment label
(High/Medium/Low) but doesn't influence whether a pathway triggers at all. Low-alignment
pathways trigger just as easily as high-alignment ones.

---

## 4. Fix 1: Contextual Relevance Guards

### Core Principle

**Absence of a capability is NOT a gap unless the capability is relevant to the repo's
architecture and workload.** A CRUD API without Kinesis doesn't need analytics. A Lambda
microservice without a Dockerfile doesn't need containers.

### Guard Rules by Pathway

Each pathway gets a contextual guard that must pass BEFORE trigger conditions are evaluated.
If the guard fails, the pathway is "Not Triggered" regardless of scores.

**Move to Cloud Native**:
- Guard: APP-Q4 < 3 (actual monolith or tightly coupled). If APP-Q4 ≥ 3 (already
  modular/microservices), the secondary criteria (APP-Q3, APP-Q10, INF-Q1) are treated
  as improvement opportunities within the existing architecture, not Cloud Native triggers.
- Rationale: A service that's already decomposed into Lambda microservices with EventBridge
  shouldn't be told to "Move to Cloud Native." Its async gaps are maturity concerns, not
  architectural decomposition needs.

**Move to Containers**:
- Guard: Compute must be EC2/VM-based or bare-metal (INF-Q1 findings show EC2, on-prem,
  or no managed compute). If compute is already Lambda/Fargate/ECS (INF-Q1 ≥ 3), absence
  of Dockerfile is expected for serverless, not a gap.
- Remove the `APP-Q4 < 4` condition entirely — monolith detection is a Cloud Native concern.
- Rationale: Serverless apps don't need containers. The pathway should only trigger for
  workloads running on unmanaged compute that would benefit from containerization.

**Move to Managed Analytics**:
- Guard: Evidence of data processing, ETL, analytics workloads, or self-managed streaming
  infrastructure (Kafka, RabbitMQ, self-hosted Redis Streams, Spark, Hadoop) must be found
  during discovery. If none found, the pathway is "Not Triggered."
- Remove the vague "no managed analytics services detected" catch-all clause entirely.
- `INF-Q8 < 3` only triggers if the repo actually HAS self-managed streaming (not just
  absence of any streaming).
- `DATA-Q4 < 3` stays as-is (data sprawl is a real signal regardless).
- Rationale: A CRUD API or event-driven microservice with no analytics needs shouldn't be
  told to adopt Redshift/Kinesis/Athena.

**Move to Managed Databases**:
- Tighten thresholds: `INF-Q2 < 3` (not `< 4`), `DATA-Q10 < 3` (not `< 4`).
- Remove `DATA-Q2 < 4` as a trigger — absence of vector DB is an AI pathway concern, not
  a managed database concern. Vector DB gaps are already captured by Move to AI.
- Add guard: INF-Q2 findings must show self-managed or significantly under-managed databases
  (self-hosted MySQL/PostgreSQL on EC2, unmanaged Redis, etc.). If all databases are already
  fully managed (DynamoDB, Aurora, RDS), the pathway should not trigger.
- Rationale: aws-microservices uses DynamoDB (fully managed). Telling it to "Move to Managed
  Databases" because it doesn't have a vector DB is misleading.

**Move to Modern DevOps** — no contextual guard changes (criteria are universally relevant).

**Move to AI** — no contextual guard changes (criteria are universally relevant for the
agentic assessment context).

**Move to Open Source** — no changes (already precise).


---

## 5. Fix 2: Goal-Weighted Trigger Thresholds

### Core Principle

**The goal should influence whether a pathway triggers, not just its label.** A pathway with
Low alignment to the current goal should require stronger evidence (more severe gaps) to trigger
than a High alignment pathway.

### Threshold Tiers

**High Alignment pathways** (primary pathways for the goal):
- Keep current sensitive OR-based triggering
- ANY single trigger condition met → Triggered
- Rationale: These are the pathways the customer cares about most. Catching even minor gaps
  is valuable because the customer is actively pursuing this direction.

**Medium Alignment pathways**:
- Require at least 2 trigger conditions met (not just 1 OR)
- Single condition alone is insufficient — could be noise
- Rationale: These pathways are relevant but not the customer's focus. A single marginal gap
  shouldn't generate a pathway recommendation that distracts from the primary goal.

**Low Alignment pathways**:
- Require the primary trigger criterion to score ≤ 2 AND be contextually relevant (pass
  the guard from Fix 1)
- A score of 3 on a low-alignment pathway is "good enough" — don't trigger
- Rationale: These pathways are tangential to the customer's goal. Only severe, undeniable
  gaps should surface them.

### How Goal Weighting Interacts with Contextual Guards

The two fixes are layered:

1. **First**, the contextual relevance guard (Fix 1) is evaluated. If the guard fails,
   the pathway is "Not Triggered" regardless of goal alignment.
2. **Then**, if the guard passes, the goal-weighted threshold (Fix 2) determines whether
   the trigger conditions are sufficient given the pathway's alignment level.

```
Evaluation Order:
  1. Is pathway N/A for repo type? → Not Applicable (unchanged from V2)
  2. Does contextual guard pass? → If no: Not Triggered
  3. Are trigger conditions met at the goal-weighted threshold? → If yes: Triggered
  4. Otherwise: Not Triggered
```

### Special Case: general-readiness

For `general-readiness`, all pathways are Medium alignment. This means all pathways require
at least 2 trigger conditions met. This is intentionally stricter than V2 (where everything
triggered on a single OR) because general-readiness should surface only meaningful gaps, not
every minor imperfection.


---

## 6. Revised Pathway Trigger Rules

These rules replace section 7.2 of the individual assessment `transformation_definition.md`.
Each pathway now has three components: (A) contextual guard, (B) trigger conditions, and
(C) goal-weighted threshold behavior.

### 6.1 Move to Cloud Native

**Contextual Guard**: APP-Q4 < 3. If APP-Q4 ≥ 3 (already modular or microservices), the
pathway does NOT trigger. Async and long-running process gaps (APP-Q3, APP-Q10) in an
already-decomposed service are maturity improvements, not Cloud Native migration needs.

**Trigger Conditions** (evaluated only if guard passes):
- APP-Q4 < 3 (monolith or tightly coupled)
- INF-Q1 < 3 (EC2-heavy compute)
- APP-Q3 < 3 (sync-heavy communication)
- APP-Q10 < 3 (no async for long-running operations)

**Goal-Weighted Thresholds**:
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: APP-Q4 ≤ 2 (primary criterion, severe gap) → Triggered

### 6.2 Move to Containers

**Contextual Guard**: Compute must be EC2/VM-based or bare-metal. If INF-Q1 ≥ 3 (already
Lambda/Fargate/ECS), absence of Dockerfile is expected for serverless — not a gap.

**Trigger Conditions** (evaluated only if guard passes):
- INF-Q1 < 3 (no managed container orchestration or serverless)
- No Dockerfile or container definitions found in discovery

**Removed**: `APP-Q4 < 4` is no longer a trigger. Monolith detection is a Cloud Native
concern, not a Containers concern. A monolith on ECS is already containerized.

**Goal-Weighted Thresholds**:
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: Both conditions met → Triggered
- Low alignment: INF-Q1 ≤ 2 AND no Dockerfile → Triggered


### 6.3 Move to Open Source

**No changes.** The current trigger rules are already precise:
- DATA-Q11 < 3 (proprietary SQL/stored procedures detected)
- INF-Q2 findings mention commercial database engines (Oracle, SQL Server, commercial licenses)

These are concrete, evidence-based triggers that don't suffer from the "absence = gap" problem.
No contextual guard needed. Goal-weighted thresholds apply normally.

**Goal-Weighted Thresholds**:
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: Primary criterion (DATA-Q11 or INF-Q2) ≤ 2 → Triggered

### 6.4 Move to Managed Databases

**Contextual Guard**: INF-Q2 findings must show self-managed or significantly under-managed
databases (self-hosted MySQL/PostgreSQL on EC2, unmanaged Redis, MongoDB on containers, etc.).
If all databases are already fully managed (DynamoDB, Aurora, RDS, ElastiCache, DocumentDB),
the pathway does NOT trigger.

**Trigger Conditions** (evaluated only if guard passes):
- INF-Q2 < 3 (self-managed databases detected) — threshold raised from `< 4`
- DATA-Q10 < 3 (EOL or unpinned database engine versions) — threshold raised from `< 4`

**Removed**: `DATA-Q2 < 4` (absence of vector DB) is no longer a trigger for this pathway.
Vector DB gaps are an AI pathway concern. A service using DynamoDB (fully managed, score 4
on INF-Q2) should not be told to "Move to Managed Databases" because it lacks a vector store.

**Goal-Weighted Thresholds**:
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: INF-Q2 ≤ 2 (severe self-managed DB gap) → Triggered


### 6.5 Move to Managed Analytics

**Contextual Guard**: Evidence of data processing, ETL, analytics workloads, or self-managed
streaming infrastructure (self-hosted Kafka, RabbitMQ, Redis Streams, Spark, Hadoop, Flink)
must be found during the Step 1 discovery scan. If none found, the pathway is "Not Triggered"
regardless of scores.

**Trigger Conditions** (evaluated only if guard passes):
- INF-Q8 < 3 (self-managed streaming detected) — note: this now only fires when the repo
  actually HAS self-managed streaming, not when streaming is simply absent
- DATA-Q4 < 3 (data source sprawl with no unified access layer)

**Removed**: The vague "no managed analytics services detected in discovery" catch-all clause
is eliminated entirely. This was the primary source of false positives — it triggered for any
repo that didn't use Kinesis/Redshift/Athena, even if the repo had zero analytics needs.

**Goal-Weighted Thresholds**:
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: Both conditions met → Triggered
- Low alignment: INF-Q8 ≤ 2 (severe self-managed streaming gap) → Triggered

### 6.6 Move to Modern DevOps

**No contextual guard changes.** DevOps criteria (IaC, CI/CD, deployment strategies,
testing, observability) are universally relevant to all application and infrastructure repos.

**Trigger Conditions** (unchanged from V2):
- INF-Q5 < 3 (low IaC coverage)
- INF-Q6 < 3 (no CI/CD automation)
- OPS-Q9 < 3 (no canary/blue-green deployments)
- OPS-Q10 < 3 (no integration tests)
- OPS-Q1 < 3 (no distributed tracing)

**Goal-Weighted Thresholds**:
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: At least 2 conditions met AND one scores ≤ 2 → Triggered

### 6.7 Move to AI

**No contextual guard changes.** In the context of an agentic readiness assessment, AI
criteria are universally relevant — the entire assessment exists to evaluate AI readiness.

**Trigger Conditions** (unchanged from V2):
- APP-Q13 < 3 (no agent frameworks)
- DATA-Q1 < 3 (no vector database)
- DATA-Q3 < 3 (no RAG implementation)
- OPS-Q3 < 3 (no eval framework)
- OPS-Q6 < 3 (no LLM cost tracking)

**Goal-Weighted Thresholds**:
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: At least 2 conditions met AND one scores ≤ 2 → Triggered


### 6.8 Summary: V2 vs V2.5 Trigger Rule Comparison

| Pathway | V2 Rule | V2.5 Rule | Key Change |
|---------|---------|-----------|------------|
| Cloud Native | ANY of: APP-Q4<4, INF-Q1<3, APP-Q3<3, APP-Q10<3 | Guard: APP-Q4<3. Then goal-weighted on remaining conditions |
 Guard blocks already-decomposed services; goal weights remaining triggers |
| Containers | ANY of: INF-Q1<3, APP-Q4<4, no Dockerfile | Guard: INF-Q1<3 (serverless = no gap). Removed APP-Q4 trigger | Serverless apps no longer told to containerize |
| Open Source | DATA-Q11<3 OR commercial DB engines | Unchanged + goal-weighted thresholds | Already precise |
| Managed DBs | ANY of: INF-Q2<4, DATA-Q2<4, DATA-Q10<4 | Guard: self-managed DBs exist. Thresholds raised to <3. Removed DATA-Q2 | Fully-managed DB repos no longer trigger; vector DB moved to AI |
| Managed Analytics | ANY of: INF-Q8<3, DATA-Q4<3, no analytics detected | Guard: analytics/streaming workload exists. Removed catch-all clause | CRUD APIs no longer told to adopt analytics |
| Modern DevOps | ANY of: INF-Q5<3, INF-Q6<3, OPS-Q9<3, OPS-Q10<3, OPS-Q1<3 | Unchanged + goal-weighted thresholds | Goal weighting reduces noise for non-DevOps goals |
| Move to AI | ANY of: APP-Q13<3, DATA-Q1<3, DATA-Q3<3, OPS-Q3<3, OPS-Q6<3 | Unchanged + goal-weighted thresholds | Goal weighting reduces noise for non-AI goals |


---

## 7. Expected Results Validation

### 7.1 Expected Results for goal: `agentic-ai-enablement`

Recall the Goal Alignment for `agentic-ai-enablement`:
- High: Move to AI, Move to Managed Databases, Move to Modern DevOps
- Medium: Move to Cloud Native, Move to Containers
- Low: Move to Open Source, Move to Managed Analytics

| Pathway | unishop-monolith | aws-microservices | local-monolith | books-api |
|---------|-----------------|-------------------|----------------|-----------|
| Cloud Native | Triggered (monolith, APP-Q4=1) | Not Triggered (guard: APP-Q4=4) | Triggered (monolith, APP-Q4=2) | Not Triggered (guard: APP-Q4=3) |
| Containers | Triggered (EC2/VM, no Docker) | Not Triggered (guard: INF-Q1≥3, Lambda) | Triggered (EC2/VM, no Docker) | Not Triggered (guard: INF-Q1≥3, Lambda) |
| Open Source | Not Triggered (no commercial) | Not Triggered (no commercial) | Not Triggered (no commercial) | Not Triggered (no commercial) |
| Managed DBs | Triggered (self-managed MySQL) | Not Triggered (guard: DynamoDB=managed) | Triggered (self-managed MySQL) | Not Triggered (guard: no self-managed DB) |
| Managed Analytics | Not Triggered (guard: no analytics workload) | Not Triggered (guard: no analytics workload) | Not Triggered (guard: no analytics workload) | Not Triggered (guard: no analytics workload) |
| Modern DevOps | Triggered (High align, 1 cond) | Triggered (High align, 1 cond) | Triggered (High align, 1 cond) | Triggered (High align, 1 cond) |
| Move to AI | Triggered (High align, 1 cond) | Triggered (High align, 1 cond) | Triggered (High align, 1 cond) | Triggered (High align, 1 cond) |

**Pathway counts**:
- unishop-monolith: 5 Triggered (Cloud Native, Containers, Managed DBs, Modern DevOps, AI)
- aws-microservices: 2 Triggered (Modern DevOps, AI)
- local-monolith: 5 Triggered (Cloud Native, Containers, Managed DBs, Modern DevOps, AI)
- books-api: 2 Triggered (Modern DevOps, AI)

**Comparison to V2**:
- V2: 5–6 pathways triggered per repo (including microservices repos)
- V2.5: Monoliths get 5 pathways (correct — they need the most work). Microservices/serverless
  get 2 pathways (correct — they mainly need DevOps maturity and AI enablement).
- Managed Analytics: 0 triggers (correct — none of these repos have analytics workloads)
- Open Source: 0 triggers (correct — no commercial licenses detected)


### 7.2 Expected Results for goal: `cloud-native-modernization`

Goal Alignment for `cloud-native-modernization`:
- High: Move to Cloud Native, Move to Containers, Move to Modern DevOps
- Medium: Move to Managed Databases, Move to Open Source
- Low: Move to AI, Move to Managed Analytics

| Pathway | unishop-monolith | aws-microservices | local-monolith | books-api |
|---------|-----------------|-------------------|----------------|-----------|
| Cloud Native | Triggered (High, monolith) | Not Triggered (guard) | Triggered (High, monolith) | Not Triggered (guard) |
| Containers | Triggered (High, EC2) | Not Triggered (guard) | Triggered (High, EC2) | Not Triggered (guard) |
| Open Source | Not Triggered | Not Triggered | Not Triggered | Not Triggered |
| Managed DBs | Triggered (Med, needs 2 conds) | Not Triggered (guard) | Triggered (Med, needs 2 conds) | Not Triggered (guard) |
| Managed Analytics | Not Triggered (guard) | Not Triggered (guard) | Not Triggered (guard) | Not Triggered (guard) |
| Modern DevOps | Triggered (High, 1 cond) | Triggered (High, 1 cond) | Triggered (High, 1 cond) | Triggered (High, 1 cond) |
| Move to AI | Not Triggered (Low, needs severe) | Not Triggered (Low, needs severe) | Not Triggered (Low, needs severe) | Not Triggered (Low, needs severe) |

**Key difference from agentic-ai-enablement**: Move to AI drops off for cloud-native goal
(Low alignment, requires severe gap). Modern DevOps stays because it's High alignment for
both goals. This correctly reflects that a cloud-native customer cares about decomposition
and containers, not AI enablement.

### 7.3 Validation Criteria for Spec Implementation

When implementing V2.5, validate against these assertions:

1. **aws-microservices** should NOT trigger Cloud Native (APP-Q4=4, guard blocks)
2. **aws-microservices** should NOT trigger Containers (Lambda-based, INF-Q1≥3, guard blocks)
3. **aws-microservices** should NOT trigger Managed Databases (DynamoDB=fully managed, guard blocks)
4. **books-api** should NOT trigger Cloud Native (APP-Q4=3, guard blocks)
5. **books-api** should NOT trigger Managed Analytics (no analytics workload, guard blocks)
6. **Managed Analytics** should trigger 0 repos in the test portfolio (none have analytics workloads)
7. **unishop-monolith** and **local-monolith** SHOULD trigger Cloud Native (APP-Q4 < 3)
8. **unishop-monolith** and **local-monolith** SHOULD trigger Containers (EC2/VM compute)
9. **Modern DevOps** and **Move to AI** should trigger for all repos under `agentic-ai-enablement`
   (High alignment, universally relevant criteria, at least 1 condition met)
10. **Move to AI** should NOT trigger for any repo under `cloud-native-modernization` unless
    a severe gap exists (Low alignment threshold)


---

## 8. Implementation Order

### Phase 1: Update Pathway Trigger Rules (section 7.2 of transformation_definition.md)

1. Add the evaluation order preamble to section 7.2:
   ```
   Evaluation Order:
     1. Is pathway N/A for repo type? → Not Applicable (unchanged)
     2. Does contextual guard pass? → If no: Not Triggered
     3. Are trigger conditions met at the goal-weighted threshold? → If yes: Triggered
     4. Otherwise: Not Triggered
   ```

2. Replace each pathway's trigger rule block with the V2.5 version from Section 6 of this
   document. Each pathway block now has three subsections:
   - **Contextual Guard** (new)
   - **Trigger Conditions** (modified for some pathways)
   - **Goal-Weighted Thresholds** (new)

3. Add a new section 7.2.1 "Goal-Weighted Threshold Reference" with the tier definitions:
   - High alignment: ANY 1 condition → Triggered
   - Medium alignment: At least 2 conditions → Triggered
   - Low alignment: Primary criterion ≤ 2 AND contextually relevant → Triggered

### Phase 2: Validate with Test Portfolio

1. Re-run the individual assessments for all 4 repos in `test-portfolio-config.yaml`
   using goal `agentic-ai-enablement`
2. Compare pathway trigger results against the Expected Results table in Section 7.1
3. Verify all 10 validation assertions from Section 7.3 pass
4. Re-run with goal `cloud-native-modernization` and verify Section 7.2 expectations

### Phase 3: Re-run Portfolio Assessment

1. After individual assessments are validated, re-run the portfolio aggregation
2. Verify the portfolio report correctly aggregates the new trigger patterns
3. Confirm the portfolio heatmap reflects fewer triggered pathways for microservices repos

### What NOT to Change

- Do NOT modify sections 7.3 (N/A rules by repo type) — unchanged
- Do NOT modify sections 7.4 (Goal Alignment column) — unchanged
- Do NOT modify sections 7.5, 7.6, 7.7 (priority, table format, parallel execution) — unchanged
- Do NOT modify Steps 0–6 (scoring criteria) — unchanged
- Do NOT modify Step 8 (report generation) — unchanged
- Do NOT modify the portfolio assessment transformation_definition.md — unchanged
- Do NOT modify the POWER.md orchestrator — unchanged
- Do NOT modify the config schema — unchanged


---

## 9. File Inventory & Change Map

### Files Modified

| File | Section Changed | Nature of Change |
|------|----------------|------------------|
| `individual-aws-agentic-assessment/transformation_definition.md` | Section 7.2 (Pathway Trigger Rules) | Replace all 7 pathway trigger blocks with V2.5 versions including contextual guards and goal-weighted thresholds |
| `individual-aws-agentic-assessment/transformation_definition.md` | New section 7.2.1 | Add Goal-Weighted Threshold Reference table |

### Files NOT Modified

| File | Reason |
|------|--------|
| `individual-aws-agentic-assessment/transformation_definition.md` sections 0–6, 7.3–7.7, 8 | Scoring, N/A rules, alignment, priority, report generation — all unchanged |
| `portfolio-agentic-assessment/transformation_definition.md` | Consumes individual reports as-is; no changes needed |
| `agentic-assessment-orchestrator/POWER.md` | Orchestrator unchanged |
| `portfolio-config.schema.json` | Config schema unchanged |
| `dashboard-generator/generate_dashboard.py` | Dashboard generator unchanged |

### Files Re-Generated (validation artifacts)

| File | Action |
|------|--------|
| `agentic-readiness-assessment/*-agentic-readiness-report.md` (×4) | Re-generate all individual reports to validate V2.5 trigger behavior |
| `agentic-readiness-assessment/ecommerce-platform-test-portfolio-agentic-readiness-report.md` | Re-generate portfolio report after individual reports are validated |
| `agentic-readiness-assessment/dashboard.html` | Re-generate dashboard after portfolio report is validated |

---

> **End of V2.5 Design Document**
> 
> This document is self-contained. A spec session should:
> 1. Read this document as the single source of truth
> 2. Implement the changes described in Section 8 (Implementation Order)
> 3. Validate against Section 7 (Expected Results)
> 4. Touch ONLY the files listed in Section 9 (File Inventory)
