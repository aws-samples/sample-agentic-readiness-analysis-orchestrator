# V2.5b Design: Tiered Common Gaps in Portfolio Report

> This document captures the agreed design for restructuring how the portfolio report
> presents "Common Gaps." It is a companion to `DESIGN-v2.5-pathway-trigger-fixes.md`
> and should be implemented in the same spec session or immediately after.
> **Status**: Ready for implementation.
> **Scope**: Portfolio assessment only (`portfolio-agentic-assessment/transformation_definition.md`).
> Individual assessments are NOT changed — they keep scoring everything 1–4 as-is.

---

## Table of Contents

1. [Problem](#1-problem)
2. [Design: Three-Tier Gap Classification](#2-design-three-tier-gap-classification)
3. [Tier Definitions](#3-tier-definitions)
4. [Goal-Driven Tier 3 Mapping](#4-goal-driven-tier-3-mapping)
5. [Revised Common Gaps Report Structure](#5-revised-common-gaps-report-structure)
6. [Cross-Cutting Concerns Update](#6-cross-cutting-concerns-update)
7. [Expected Results](#7-expected-results)
8. [Implementation Order](#8-implementation-order)
9. [File Inventory & Change Map](#9-file-inventory--change-map)

---

## 1. Problem

The portfolio report's "Common Gaps" section currently lists all criteria with low scores
as gaps, regardless of whether they represent:

- A missing foundation that blocks everything (no IaC, no CI/CD)
- A prerequisite that specifically enables the goal (no API docs for agent discovery)
- The goal itself (no agent frameworks — but that's literally what they're building)

This creates a confusing report. A customer pursuing `agentic-ai-enablement` sees "No AI/Agent
Frameworks (APP-Q13)" listed as a gap — which is obvious and unhelpful. It's like telling
someone who came to a doctor "you're sick." Of course they don't have agent frameworks; that's
why they're running this assessment.

Similarly, "No Human Approval Workflows (SEC-Q7)" is listed as a blocker, but human-in-the-loop
guardrails are designed as part of the agent system itself (Bedrock Agents, Strands). You don't
need pre-existing approval workflows before you can start building agents.

The current "Blocking Your Goal" vs "General Opportunities" split in Cross-Cutting Concerns
(Step 4) partially addresses this, but it still treats goal deliverables as "blocking" gaps
rather than recognizing them as the work the customer is here to do.

---

## 2. Design: Three-Tier Gap Classification

The key question for each gap: **"Can you start building toward your goal without fixing
this first?"**

- If NO → Tier 1 (Foundational Blocker) or Tier 2 (Goal-Specific Prerequisite)
- If YES, because it IS the goal → Tier 3 (Goal Deliverable)

### Where This Logic Lives

**Portfolio assessment only (Option A).** The individual assessments keep scoring everything
1–4 with gaps-are-gaps framing. The portfolio report is where strategic tiering happens when
it aggregates common gaps. This keeps the individual assessment as a clean factual scoring
exercise and the portfolio as the strategic framing layer.

---

## 3. Tier Definitions

### Tier 1 — Foundational Blockers

Gaps that block ALL modernization, not just the customer's specific goal. These are "you
need to walk before you run" — prerequisites for operating any production system.

**Criteria** (static across all goals — always Tier 1 when score < 2):
- INF-Q5 < 2 (no IaC at all)
- INF-Q6 < 2 (no CI/CD at all)
- OPS-Q1 < 2 (no observability at all)
- APP-Q8 < 2 AND SEC-Q5 < 2 (no rate limiting at all)

**Threshold**: Score < 2 (missing entirely). A score of 2 means "exists but needs work" —
enough to not be a foundational blocker. A score of 1 means "missing entirely" which truly
blocks everything.

**Report framing**: "These foundational gaps block all modernization efforts, not just
your stated goal. Address these first."

### Tier 2 — Goal-Specific Prerequisites

Gaps that specifically enable the customer's goal but aren't the goal itself. These are
the bridge between existing services and the target state.

**Criteria** (dynamic, depends on goal — see Section 4):

For `agentic-ai-enablement`:
- APP-Q2 (API documentation) — agents need machine-readable specs to discover tools
- SEC-Q3 (identity propagation) — agents need to act on behalf of users

For `cloud-native-modernization`:
- INF-Q5 (IaC at score 2) — need better IaC for automated infra provisioning
- INF-Q6 (CI/CD at score 2) — need better CI/CD for safe deployment iteration

For `cost-optimization`:
- INF-Q5 (IaC) — need IaC to measure and control resources
- OPS-Q1 (observability) — need observability to identify waste

For `general-readiness`:
- No Tier 2 — everything is treated equally (all gaps go to "General Opportunities")

**Threshold**: Score < 3 on a goal-prerequisite criterion (the criterion exists but has
significant gaps that specifically impede the goal).

**Report framing**: "These gaps specifically block your path to <goal>. They aren't the
goal itself, but you can't get there without them."


### Tier 3 — Goal Deliverables

Gaps that ARE the goal itself. The customer doesn't have these yet — that's why they're
running the assessment. Listing them as "blockers" is circular and unhelpful.

**Criteria** (dynamic, depends on goal — see Section 4 for full mapping):

For `agentic-ai-enablement`:
- APP-Q13 (no agent frameworks) — this IS what they're building
- DATA-Q1 (no vector database) — this IS part of the agent architecture
- DATA-Q2 (no semantic search) — this IS part of the agent architecture
- DATA-Q3 (no RAG pipeline) — this IS part of the agent architecture
- SEC-Q7 (no human approval workflows) — human-in-the-loop is designed as part of
  the agent system (Bedrock Agents guardrails, Strands), not a prerequisite
- OPS-Q3 (no eval framework) — agent evaluation is built alongside the agent
- OPS-Q6 (no LLM cost tracking) — cost tracking comes after LLM integration

For `cloud-native-modernization`:
- APP-Q4 (monolith architecture) — decomposition IS the goal
- APP-Q3 (sync-heavy communication) — async adoption IS part of the goal
- INF-Q1 (EC2-heavy compute) — moving to managed compute IS the goal
- OPS-Q9 (no canary/blue-green) — advanced deployment IS part of the goal

For `cost-optimization`:
- INF-Q2 (self-managed databases) — moving to managed IS the goal
- DATA-Q10 (EOL database versions) — upgrading IS part of the goal
- DATA-Q11 (proprietary SQL) — migrating to open source IS the goal
- INF-Q8 (self-managed streaming) — moving to managed streaming IS the goal

For `general-readiness`:
- No Tier 3 — everything is treated equally (no goal to be "delivering")

**Threshold**: Any score on a goal-deliverable criterion. These are reported regardless
of score because they represent the work to be done, not blockers.

**Report framing**: "These are the capabilities you're here to build. Your individual
assessment reports detail the current state and recommendations for each."


---

## 4. Goal-Driven Tier 3 Mapping

This section provides the complete mapping of which criteria fall into which tier for
each goal. Tier 1 is static (same for all goals). Tiers 2 and 3 are goal-dependent.

### 4.1 `agentic-ai-enablement`

| Tier | Criteria | Rationale |
|------|----------|-----------|
| Tier 1 (Foundational) | INF-Q5 < 2, INF-Q6 < 2, OPS-Q1 < 2, APP-Q8 < 2 + SEC-Q5 < 2 | No IaC, no CI/CD, no observability, no rate limiting — blocks everything |
| Tier 2 (Prerequisite) | APP-Q2 < 3 (API docs), SEC-Q3 < 3 (identity propagation) | Agents need machine-readable API specs and user-context propagation |
| Tier 3 (Deliverable) | APP-Q13 (agent frameworks), DATA-Q1 (vector DB), DATA-Q2 (semantic search), DATA-Q3 (RAG), SEC-Q7 (human approval), OPS-Q3 (eval framework), OPS-Q6 (LLM cost tracking) | These ARE the agent capabilities the customer is here to build |
| General Opportunity | Everything else with score < 3 | Important but not blocking the agentic goal |

### 4.2 `cloud-native-modernization`

| Tier | Criteria | Rationale |
|------|----------|-----------|
| Tier 1 (Foundational) | INF-Q5 < 2, INF-Q6 < 2, OPS-Q1 < 2, APP-Q8 < 2 + SEC-Q5 < 2 | Same foundational blockers |
| Tier 2 (Prerequisite) | INF-Q5 score 2 (IaC exists but weak), INF-Q6 score 2 (CI/CD exists but weak) | Need better IaC and CI/CD to iterate on cloud-native infra safely |
| Tier 3 (Deliverable) | APP-Q4 (monolith decomposition), APP-Q3 (async communication), INF-Q1 (managed compute), OPS-Q9 (canary/blue-green) | These ARE the cloud-native capabilities the customer is pursuing |
| General Opportunity | Everything else with score < 3 | Important but not blocking cloud-native goal |

### 4.3 `cost-optimization`

| Tier | Criteria | Rationale |
|------|----------|-----------|
| Tier 1 (Foundational) | INF-Q5 < 2, INF-Q6 < 2, OPS-Q1 < 2, APP-Q8 < 2 + SEC-Q5 < 2 | Same foundational blockers |
| Tier 2 (Prerequisite) | INF-Q5 < 3 (IaC — need it to measure/control resources), OPS-Q1 < 3 (observability — need it to identify waste) | Can't optimize costs without visibility and control |
| Tier 3 (Deliverable) | INF-Q2 (managed DB migration), DATA-Q10 (EOL DB upgrades), DATA-Q11 (open source migration), INF-Q8 (managed streaming) | These ARE the cost-reduction migrations the customer is pursuing |
| General Opportunity | Everything else with score < 3 | Important but not blocking cost optimization |

### 4.4 `general-readiness`

| Tier | Criteria | Rationale |
|------|----------|-----------|
| Tier 1 (Foundational) | INF-Q5 < 2, INF-Q6 < 2, OPS-Q1 < 2, APP-Q8 < 2 + SEC-Q5 < 2 | Same foundational blockers — still relevant even without a specific goal |
| Tier 2 (Prerequisite) | None | No specific goal means no goal-specific prerequisites |
| Tier 3 (Deliverable) | None | No specific goal means nothing is a "deliverable" |
| General Opportunity | Everything else with score < 3 | All gaps treated equally |

**Special handling**: For `general-readiness`, the report uses only two sections:
Tier 1 (Foundational Blockers) and General Opportunities. Tiers 2 and 3 are omitted
since they require a specific goal to be meaningful.

---

## 5. Revised Common Gaps Report Structure

The current portfolio report's Step 4 (Cross-Cutting Concerns) has two subsections:
"Blocking Your Goal" and "General Opportunities." This design replaces that with a
four-section structure.

### Current Structure (V2)

```
## Cross-Cutting Concerns
### Blocking Your Goal
  - Gap 1 (criterion, count, impact)
  - Gap 2 ...
### General Opportunities
  - Gap 3 ...
```

### New Structure (V2.5b)

```
## Cross-Cutting Concerns

### 🚨 Foundational Blockers
> These gaps block all modernization efforts, not just <goal>.
> Address these first — nothing else matters until these are resolved.

  - No IaC (INF-Q5): X of Y services score < 2. [details]
  - No CI/CD (INF-Q6): X of Y services score < 2. [details]
  ...
```

```
### ⚠️ Prerequisites for <Goal>
> These gaps specifically block your path to <goal>.
> They aren't the goal itself, but you can't get there without them.

  - No API Documentation (APP-Q2): X of Y services score < 3. [details]
  - No Identity Propagation (SEC-Q3): X of Y services score < 3. [details]
  ...

### 🎯 Goal Deliverables — What You're Here to Build
> These are the capabilities your <goal> initiative will deliver.
> Low scores here confirm the need for the initiative, not additional blockers.
> Your individual assessment reports detail the current state and roadmap for each.

  - Agent Frameworks (APP-Q13): X of Y services score < 3. [current state summary]
  - Vector Database (DATA-Q1): X of Y services score < 3. [current state summary]
  - RAG Pipeline (DATA-Q3): X of Y services score < 3. [current state summary]
  ...

### 💡 General Improvement Opportunities
> These gaps are important but do not directly block <goal>.
> Address them as capacity allows or in parallel with goal work.

  - No Auto-Scaling (INF-Q10): X of Y services score < 3. [details]
  - No Integration Tests (OPS-Q10): X of Y services score < 3. [details]
  ...
```

### Rendering Rules

1. **Tier 1 section**: Only rendered if at least one Tier 1 criterion has a portfolio
   average < 2 across applicable services. If no foundational blockers exist, omit the
   section entirely (don't show an empty section).

2. **Tier 2 section**: Only rendered if the goal has Tier 2 criteria defined AND at least
   one has a portfolio average < 3. Omitted for `general-readiness`.

3. **Tier 3 section**: Only rendered if the goal has Tier 3 criteria defined AND at least
   one has a portfolio average < 3. Omitted for `general-readiness`. The framing is
   informational ("here's where you stand") not prescriptive ("fix this blocker").

4. **General Opportunities section**: Always rendered. Contains all cross-cutting gaps
   that don't fall into Tiers 1, 2, or 3.

5. **`general-readiness` special case**: Only two sections rendered — Tier 1 (if any)
   and General Opportunities. A note is added: "With `general-readiness` as the goal,
   all non-foundational gaps are treated as equal improvement opportunities."


---

## 6. Cross-Cutting Concerns Update

### What Changes in Step 4 of `portfolio-agentic-assessment/transformation_definition.md`

The current Step 4 logic for "Cross-Cutting Concerns Classification by Goal" is replaced.

**Current logic (V2)**:
- Group findings by criterion ID
- Count services with score < 3.0 (excluding N/A)
- If count >= 3, flag as cross-cutting concern
- Split into "Blocking Your Goal" (criterion in goal's priority list) vs "General Opportunities"

**New logic (V2.5b)**:
- Group findings by criterion ID (unchanged)
- Count services with score < threshold (threshold varies by tier — see below)
- If count >= 2 services (lowered from 3 to catch smaller portfolios), flag as cross-cutting
- Classify each flagged criterion into its tier using the mapping from Section 4
- Render using the four-section structure from Section 5

### Threshold by Tier

| Tier | Threshold for "gap" | Minimum services to flag |
|------|--------------------|-----------------------|
| Tier 1 | Score < 2 | 2+ services (or 50%+ of portfolio, whichever is lower) |
| Tier 2 | Score < 3 | 2+ services |
| Tier 3 | Score < 3 | 2+ services |
| General | Score < 3 | 3+ services (keep current threshold for noise reduction) |

### Classification Algorithm (Pseudocode)

```
for each criterion_id in all_criteria:
    scores = [s for s in service_scores[criterion_id] if s != N/A]
    if len(scores) == 0: continue

    # Check Tier 1 first (static, goal-independent)
    if criterion_id in TIER_1_CRITERIA:
        low_count = count(s < 2 for s in scores)
        if low_count >= min(2, len(scores) * 0.5):
            classify as Tier 1
            continue

    # Check Tier 2 (goal-dependent)
    if criterion_id in TIER_2_MAP[goal]:
        gap_count = count(s < 3 for s in scores)
        if gap_count >= 2:
            classify as Tier 2
            continue

    # Check Tier 3 (goal-dependent)
    if criterion_id in TIER_3_MAP[goal]:
        gap_count = count(s < 3 for s in scores)
        if gap_count >= 2:
            classify as Tier 3
            continue

    # Default: General Opportunity
    gap_count = count(s < 3 for s in scores)
    if gap_count >= 3:
        classify as General Opportunity
```


### What Happens to the Existing "Priority Criteria by Goal" Table

The existing table in Step 4 that maps goals to priority criteria is kept but reframed.
It now serves as the source for Tier 2 + Tier 3 classification rather than the binary
"blocking vs general" split. The table itself doesn't change — only how it's used.

---

## 7. Expected Results

### 7.1 Test Portfolio: `agentic-ai-enablement` Goal

Using the same 4-repo test portfolio (unishop-monolith, aws-microservices, local-monolith,
books-api), here's how the common gaps would be reclassified:

**Tier 1 — Foundational Blockers**:
- No Observability (OPS-Q1): 3 of 4 services score < 2 (zero distributed tracing).
  Only aws-microservices has basic CloudWatch. This blocks debugging for any initiative.
- No IaC (INF-Q5): 2 of 4 services score < 2 (monoliths have no IaC at all).
  Can't automate anything without infrastructure as code.

**Tier 2 — Prerequisites for Agentic AI**:
- No API Documentation (APP-Q2): 4 of 4 services score < 3. Zero OpenAPI/Swagger specs.
  Agents cannot discover or invoke service capabilities without machine-readable API specs.
  This is a prerequisite — you need API docs before agents can use your services as tools.
- No Identity Propagation (SEC-Q3): 3 of 4 services score < 3. Agents need to act on
  behalf of users with proper identity context.

**Tier 3 — Goal Deliverables (What You're Here to Build)**:
- No AI/Agent Frameworks (APP-Q13): 4 of 4 services score 1/4. This confirms the need
  for the initiative — not a surprise blocker. Your roadmap Phase 2-3 addresses this.
- No Vector Databases (DATA-Q1, DATA-Q2): 4 of 4 services score 1/4. Semantic search
  infrastructure is part of the agent architecture you're building.
- No RAG Pipeline (DATA-Q3): 4 of 4 services score 1/4. Knowledge retrieval is a core
  agent capability to be delivered.
- No Human Approval Workflows (SEC-Q7): 4 of 4 services score 1-2/4. Human-in-the-loop
  guardrails are designed as part of the agent system (Bedrock Agents, Strands), not a
  prerequisite that must exist before you start.
- No Eval Framework (OPS-Q3): 4 of 4 services score 1/4. Agent evaluation is built
  alongside the agent, not before it.
- No LLM Cost Tracking (OPS-Q6): 4 of 4 services score 1/4. Cost tracking comes after
  LLM integration, not before.

**General Opportunities**:
- No Rate Limiting (APP-Q8, SEC-Q5): 4 of 4 services score 1/4. Important for agent
  safety but not a foundational blocker (score threshold for Tier 1 requires < 2 on 
  BOTH APP-Q8 AND SEC-Q5 — if either has some coverage, it's not a total blocker).
- No Integration Tests (OPS-Q10): 3 of 4 services score < 3. Good practice but not
  blocking the agentic goal specifically.

### 7.2 Comparison: V2 vs V2.5b Common Gaps

| Gap | V2 Classification | V2.5b Classification | Why the change |
|-----|-------------------|---------------------|----------------|
| No Observability (OPS-Q1) | Blocking Your Goal | Tier 1 (Foundational) | Blocks everything, not just agents |
| No API Docs (APP-Q2) | Blocking Your Goal | Tier 2 (Prerequisite) | Agents need this, but it's not the goal itself |
| No Agent Frameworks (APP-Q13) | Blocking Your Goal | Tier 3 (Deliverable) | This IS what they're building |
| No Vector DB (DATA-Q1) | Blocking Your Goal | Tier 3 (Deliverable) | Part of the agent architecture to deliver |
| No RAG (DATA-Q3) | Blocking Your Goal | Tier 3 (Deliverable) | Part of the agent architecture to deliver |
| No Human Approval (SEC-Q7) | Blocking Your Goal | Tier 3 (Deliverable) | Built as part of agent system, not a prereq |
| No Rate Limiting (APP-Q8) | General Opportunities | General Opportunities | Unchanged — correctly classified already |
| No IaC (INF-Q5) | General Opportunities | Tier 1 (Foundational) | Promoted — this blocks everything |

### 7.3 Validation Criteria

1. APP-Q13, DATA-Q1, DATA-Q2, DATA-Q3, SEC-Q7, OPS-Q3, OPS-Q6 must appear in Tier 3
   (not "Blocking") for `agentic-ai-enablement`
2. APP-Q2 must appear in Tier 2 (prerequisite, not deliverable) for `agentic-ai-enablement`
3. INF-Q5 < 2 and OPS-Q1 < 2 must appear in Tier 1 regardless of goal
4. For `general-readiness`, no Tier 2 or Tier 3 sections should be rendered
5. For `cloud-native-modernization`, APP-Q4 and INF-Q1 must appear in Tier 3 (deliverables)
6. Tier 3 framing must be informational, not prescriptive — no "fix this blocker" language


---

## 8. Implementation Order

### Phase 1: Add Tier Classification Constants

Add the tier mapping data structures to the portfolio transformation definition. These
are static lookup tables that the agent uses during Step 4 analysis.

1. Add a new section "4.1: Tiered Gap Classification" to `portfolio-agentic-assessment/transformation_definition.md`
   immediately before the existing cross-cutting concerns logic.

2. Define the three constant maps:
   - `TIER_1_CRITERIA` — static list: `[INF-Q5, INF-Q6, OPS-Q1, APP-Q8+SEC-Q5]`
   - `TIER_2_MAP` — goal → criteria list (from Section 4 of this document)
   - `TIER_3_MAP` — goal → criteria list (from Section 4 of this document)

3. Define the tier thresholds:
   - Tier 1: score < 2
   - Tier 2: score < 3
   - Tier 3: score < 3
   - General: score < 3

### Phase 2: Replace Cross-Cutting Concerns Classification Logic

Replace the existing "Cross-Cutting Concerns Classification by Goal" logic in Step 4
with the tiered classification algorithm from Section 6 of this document.

1. Replace the binary "Blocking Your Goal" / "General Opportunities" split with the
   four-tier classification (Tier 1, Tier 2, Tier 3, General Opportunities)
2. Update the rendering instructions to use the four-section structure from Section 5
3. Keep the existing threshold for flagging cross-cutting concerns (count >= 3 for
   General, count >= 2 for Tiers 1-3)
4. Keep the N/A exclusion logic unchanged
5. Keep the `general-readiness` special handling (two sections only)

### Phase 3: Update Report Template Instructions

Update the report generation instructions (Step 5 or wherever the portfolio report
Markdown structure is defined) to reflect the new four-section layout.

1. Replace the "Cross-Cutting Concerns" section template with the new structure
   from Section 5 (emoji headers, tier-specific framing text, rendering rules)
2. Add conditional rendering logic for each tier section (only render if non-empty)
3. Add the `general-readiness` two-section fallback

### Phase 4: Validate with Test Portfolio

1. Re-run the portfolio assessment for the 4-repo test portfolio with goal
   `agentic-ai-enablement`
2. Verify the common gaps are classified per Section 7.1 expected results
3. Verify all 6 validation criteria from Section 7.3 pass
4. Verify Tier 3 framing is informational, not prescriptive
5. Verify `general-readiness` renders only two sections

### What NOT to Change

- Do NOT modify individual assessment transformation definition — tiering is portfolio-only
- Do NOT modify the scoring criteria or 1-4 scale
- Do NOT modify the pathway trigger rules (those are in V2.5, separate concern)
- Do NOT modify the POWER.md orchestrator
- Do NOT modify the config schema
- Do NOT modify the dashboard generator

---

## 9. File Inventory & Change Map

### Files Modified

| File | Section Changed | Nature of Change |
|------|----------------|------------------|
| `portfolio-agentic-assessment/transformation_definition.md` | Step 4 (Cross-Cutting Concerns) | Replace binary "Blocking/General" split with four-tier classification |
| `portfolio-agentic-assessment/transformation_definition.md` | New section 4.1 | Add Tiered Gap Classification constants and algorithm |
| `portfolio-agentic-assessment/transformation_definition.md` | Report template (Step 5 or equivalent) | Update Markdown structure for four-section common gaps |

### Files NOT Modified

| File | Reason |
|------|--------|
| `individual-aws-agentic-assessment/transformation_definition.md` | Individual assessments keep scoring everything 1-4 as-is. Tiering is portfolio-only. |
| `agentic-assessment-orchestrator/POWER.md` | Orchestrator unchanged |
| `portfolio-config.schema.json` | Config schema unchanged |
| `dashboard-generator/generate_dashboard.py` | Dashboard generator unchanged |

### Files Re-Generated (validation artifacts)

| File | Action |
|------|--------|
| `agentic-readiness-assessment/ecommerce-platform-test-portfolio-agentic-readiness-report.md` | Re-generate portfolio report to validate tiered common gaps |
| `agentic-readiness-assessment/dashboard.html` | Re-generate dashboard after portfolio report is validated |

### Relationship to V2.5 (Pathway Trigger Fixes)

This document (V2.5b) is independent of `DESIGN-v2.5-pathway-trigger-fixes.md` (V2.5).
They can be implemented in either order:

- V2.5 changes the **individual assessment** (pathway trigger rules)
- V2.5b changes the **portfolio assessment** (common gaps classification)

However, implementing V2.5 first is recommended because the portfolio report consumes
individual reports. Cleaner individual reports (fewer false-positive pathways) will make
the portfolio tiering more accurate.

---

> **End of V2.5b Design Document**
>
> This document is self-contained. A spec session should:
> 1. Read this document as the single source of truth for tiered common gaps
> 2. Implement the changes described in Section 8 (Implementation Order)
> 3. Validate against Section 7 (Expected Results)
> 4. Touch ONLY the files listed in Section 9 (File Inventory)
