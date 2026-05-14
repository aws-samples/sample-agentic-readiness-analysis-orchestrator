# BPMN Agentic Opportunity Analysis: Camunda Invoice

**Repository**: `agentic-readiness-analysis/example-reports/bao-demo/repos/camunda-invoice`
**BPMN Files**: 2,503 found · 2,446 analyzed · 57 failed parsing
**Date**: 2025-07-14
**Priority**: P0
**Context**: Demonstrating BPMN agentic opportunity analysis across official open source process repositories covering invoice processing, order management, and BPMN interchange test cases.
**Daily Volume**: 200 invocations/day (per task)

---

## Summary

The Camunda Invoice portfolio contains **3,484 tasks** across **2,446 BPMN processes**. Of these:

- **5** are agent opportunities (0 build-now, **5 data-first** — data readiness could not be confirmed from BPMN metadata alone)
- **3,462** are automatable with deterministic logic (service tasks)
- **17** require human involvement (approval gates with elevated risk scores)

Estimated monthly Amazon Bedrock cost for agent tasks: **$81.00** at 200 invocations/day per task.

> **Note:** Data readiness could not be assessed from the BPMN models. All agent tasks are classified as "data first" pending an Agentic Readiness Analysis (ARA) on the target systems. The two `businessRuleTask` candidates (Check decision, evaluate decision table) are strong Wave 1 candidates if ARA confirms data readiness.

---

## Opportunity Classification

### All Agent Tasks

| Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------|----------|----------|---------|
| Check decision | agent | businessRuleTask | 0.85 | 0.30 | Agent (data first) | Prepared | $2.70 |
| evaluate decision table | agent | businessRuleTask | 0.85 | 0.30 | Agent (data first) | Prepared | $2.70 |
| Analyze report | agent | userTask | 0.75 | 0.30 | Agent (data first) | Prepared | $2.70 |
| Review Invoice | agent | userTask | 0.70 | 0.30 | Agent (data first) | Prepared | $2.70 |
| Assign Reviewer | agent | userTask | 0.70 | 0.45 | Agent (data first) | Exploration | $2.70 |

### Human-Required Tasks (sample)

| Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------|----------|----------|---------|
| approve invoice | human | userTask | 0.70 | 0.80 | Human Required | -- | -- |
| assign approver | human | userTask | 0.70 | 0.80 | Human Required | -- | -- |
| Approve Invoice | human | userTask | 0.70 | 0.73 | Human Required | -- | -- |
| approve (noStartOrTaskForm) | human | userTask | 0.75 | 0.65 | Human Required | -- | -- |
| Approve expenses | human | userTask | 0.75 | 0.65 | Human Required | -- | -- |
| Approve Request | human | userTask | 0.75 | 0.65 | Human Required | -- | -- |
| Approve Variables | human | userTask | 0.70 | 0.65 | Human Required | -- | -- |

### Service Tasks (3,462 total — representative sample)

| Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------|----------|----------|---------|
| Error Task | service | serviceTask | 0.35 | 0.30 | Automate | -- | -- |
| externalTask | service | serviceTask | 0.35 | 0.30 | Automate | -- | -- |
| Activity_1mvoh71 | service | serviceTask | 0.35 | 0.30 | Automate | -- | -- |
| theTask | service | userTask | 0.35 | 0.30 | Automate | -- | -- |
| miTasks | service | userTask | 0.35 | 0.30 | Automate | -- | -- |

> **Classification totals**: 5 agent + 3,462 service + 17 human_required = **3,484 tasks** (all classified, none remaining).

---

## Agent Opportunities (ranked by composite score)

### 1. Check decision

- **Process**: process (`process`)
- **Source**: `qa/integration-tests-engine/src/test/resources/org/camunda/bpm/integrationtest/functional/dmn/BusinessRuleTaskVersionTagTest.bpmn20.xml`
- **Category**: Agent (data first)
- **Autonomy**: **Prepared** — Agent synthesizes and recommends. Human reviews and approves.
- **Scores**: AI Benefit: 0.85 | Complexity: 0.30 | Risk: 0.30 | Effort: 0.20 | Composite: 0.265
- **Verdict**: strong_candidate — High AI benefit; task involves judgment/analysis.
- **Data Readiness**: Unknown — No `dataStoreReference` or WSDL/REST endpoints in BPMN model. No ARA report available. Business rule tasks typically consume structured decision inputs, making this a strong candidate for quick data readiness confirmation.
- **Cost**: ~$2.70/1K invocations (haiku-3.5, 1,300 tokens) · **$16.20/month** at 200/day
- **Structural Position**: Linear process (3 elements, 2 flows). Constraint density: 0.67. No gateway branching. Simple init→task→end chain.
- **Agent Description**: AI agent replaces rule engine for 'Check decision'. Can handle edge cases and nuance beyond static rules.
- **Integration Approach**: REST connector: Replace DMN/Drools call with agent endpoint. Agent receives the decision inputs and returns the same output schema the BPM engine expects.
- **Prerequisites**:
  1. Deploy Strands agent on AgentCore or as REST API
  2. Prepare training examples or few-shot prompts for the agent

### 2. evaluate decision table

- **Process**: Process (`Process`)
- **Source**: `qa/performance-tests-engine/src/test/resources/org/camunda/bpm/qa/performance/engine/dmn/DmnBusinessRuleTaskTest.businessRuleTask.bpmn`
- **Category**: Agent (data first)
- **Autonomy**: **Prepared** — Agent synthesizes and recommends. Human reviews and approves.
- **Scores**: AI Benefit: 0.85 | Complexity: 0.30 | Risk: 0.30 | Effort: 0.20 | Composite: 0.265
- **Verdict**: strong_candidate — High AI benefit; task involves judgment/analysis.
- **Data Readiness**: Unknown — No `dataStoreReference` or WSDL/REST endpoints in BPMN model. No ARA report available. As a decision table evaluator, structured inputs are expected—strong candidate for quick data readiness confirmation.
- **Cost**: ~$2.70/1K invocations (haiku-3.5, 1,300 tokens) · **$16.20/month** at 200/day
- **Structural Position**: Linear process (3 elements, 2 flows). Constraint density: 0.67. No gateway branching. Simple init→task→end chain.
- **Agent Description**: AI agent replaces rule engine for 'evaluate decision table'. Can handle edge cases and nuance beyond static rules.
- **Integration Approach**: REST connector: Replace DMN/Drools call with agent endpoint. Agent receives the decision inputs and returns the same output schema the BPM engine expects.
- **Prerequisites**:
  1. Deploy Strands agent on AgentCore or as REST API
  2. Prepare training examples or few-shot prompts for the agent

### 3. Analyze report

- **Process**: failingTimer (`failingTimer`)
- **Source**: `qa/test-db-instance-migration/test-fixture-712/src/main/resources/org/camunda/bpm/qa/upgrade/customretries/failingTimerJob.bpmn20.xml`
- **Category**: Agent (data first)
- **Autonomy**: **Prepared** — Agent synthesizes and recommends. Human reviews and approves.
- **Scores**: AI Benefit: 0.75 | Complexity: 0.30 | Risk: 0.30 | Effort: 0.40 | Composite: 0.195
- **Verdict**: good_candidate — High AI benefit; task involves judgment/analysis; currently requires human; AI could augment or replace.
- **Data Readiness**: Unknown — User task with no system references in BPMN model. One inferred dependency (`Failing Service` → `org.camunda.UnexistingClass`, service endpoint, high confidence). No ARA report available.
- **Cost**: ~$2.70/1K invocations (haiku-3.5, 1,300 tokens) · **$16.20/month** at 200/day
- **Structural Position**: 4 elements, 3 flows. Constraint density: 0.75. No gateway branching. Contains a preceding service task (`Failing Service`). Two end events suggest alternate termination paths.
- **Agent Description**: AI agent replaces human 'Analyze report' task. Agent receives the same inputs, applies reasoning, and returns a decision. Human escalation for low-confidence cases.
- **Integration Approach**: REST connector: BPM engine calls agent API endpoint instead of creating a human task. Agent returns decision + confidence. If confidence < threshold, fall back to human task queue.
- **Prerequisites**:
  1. Deploy Strands agent on AgentCore or as REST API
  2. Map human task input/output to agent request/response schema
  3. Configure BPM connector to call REST instead of task queue
  4. Prepare training examples or few-shot prompts for the agent

### 4. Review Invoice

- **Process**: Review Invoice (`ReviewInvoice`)
- **Source**: `examples/invoice/src/main/resources/reviewInvoice.bpmn`
- **Category**: Agent (data first)
- **Autonomy**: **Prepared** — Agent synthesizes and recommends. Human reviews and approves.
- **Scores**: AI Benefit: 0.70 | Complexity: 0.30 | Risk: 0.30 | Effort: 0.50 | Composite: 0.16
- **Verdict**: good_candidate — High AI benefit; task involves judgment/analysis; currently requires human; AI could augment or replace.
- **Data Readiness**: Unknown — User task with no system references in BPMN model. Uses Camunda form (`embedded:app:forms/review-invoice.html`). Assignee is dynamic (`${reviewer}`). No `dataStoreReference` or data object associations. No ARA report available.
- **Cost**: ~$2.70/1K invocations (haiku-3.5, 1,300 tokens) · **$16.20/month** at 200/day
- **Structural Position**: 4 elements, 3 flows in the Review Invoice subprocess. Constraint density: 1.75 (high — 7 constraints for 4 elements). Ordering, coexistence, succession, and chain constraints indicate a tightly coupled sequential flow: Assign Reviewer → Review Invoice. No branching.
- **Agent Description**: AI agent replaces human 'Review Invoice' task. Agent receives the same inputs, applies reasoning, and returns a decision. Human escalation for low-confidence cases.
- **Integration Approach**: REST connector: BPM engine calls agent API endpoint instead of creating a human task. Agent returns decision + confidence. If confidence < threshold, fall back to human task queue.
- **Prerequisites**:
  1. Deploy Strands agent on AgentCore or as REST API
  2. Map human task input/output to agent request/response schema
  3. Configure BPM connector to call REST instead of task queue
  4. Prepare training examples or few-shot prompts for the agent

### 5. Assign Reviewer

- **Process**: Review Invoice (`ReviewInvoice`)
- **Source**: `examples/invoice/src/main/resources/reviewInvoice.bpmn`
- **Category**: Agent (data first)
- **Autonomy**: **Exploration** — Human leads investigation. Agent surfaces data in real time.
- **Scores**: AI Benefit: 0.70 | Complexity: 0.30 | Risk: 0.45 | Effort: 0.40 | Composite: 0.13
- **Verdict**: good_candidate — High AI benefit; task involves judgment/analysis; currently requires human; AI could augment or replace.
- **Data Readiness**: Unknown — User task with no system references in BPMN model. Uses Camunda form (`embedded:app:forms/assign-reviewer.html`). Hardcoded assignee (`demo`). No `dataStoreReference` or data object associations. No ARA report available.
- **Cost**: ~$2.70/1K invocations (haiku-3.5, 1,300 tokens) · **$16.20/month** at 200/day
- **Structural Position**: First task in the Review Invoice subprocess. Feeds directly into Review Invoice task via chain succession constraint. Same process structure as task #4 above.
- **Agent Description**: AI agent replaces human 'Assign Reviewer' task. Agent receives the same inputs, applies reasoning, and returns a decision. Human escalation for low-confidence cases.
- **Integration Approach**: REST connector: BPM engine calls agent API endpoint instead of creating a human task. Agent returns decision + confidence. If confidence < threshold, fall back to human task queue.
- **Prerequisites**:
  1. Deploy Strands agent on AgentCore or as REST API
  2. Map human task input/output to agent request/response schema
  3. Configure BPM connector to call REST instead of task queue
  4. Prepare training examples or few-shot prompts for the agent

---

## Automatable Tasks

The portfolio contains **3,462 service-classified tasks** across 2,446 processes. These tasks have low AI benefit scores and are best served by deterministic logic (Step Functions, rule engines, REST API wrappers).

### Task Type Distribution (service-classified)

| BPMN Element Type | Count | Recommendation |
|-------------------|-------|----------------|
| userTask | 1,978 | Low-risk user tasks suitable for form automation or Step Functions workflows |
| serviceTask | 801 | Already automated — maintain as REST API / microservice endpoints |
| subProcess | 515 | Orchestrate via Step Functions or BPM engine subprocess execution |
| scriptTask | 76 | Execute via Lambda functions or container tasks |
| task | 60 | Generic tasks — evaluate individually for automation approach |
| businessRuleTask | 35 | DMN engine / rule engine — keep deterministic unless edge-case handling needed |

### Representative Examples

| Task | Process | BPMN Element | Recommendation |
|------|---------|-------------|----------------|
| Error Task | Test Process | serviceTask | REST API wrapper — deterministic endpoint |
| externalTask | External Task with String Topic Process | serviceTask | External task worker pattern — maintain as-is |
| Activity_1mvoh71 | Process_14ltot0 | serviceTask | REST API wrapper — deterministic endpoint |
| theTask | calledProcess | userTask | Form automation via Step Functions |
| Task in super process | callingProcess | userTask | Orchestration task — Step Functions parent workflow |
| afterCallActivityTask | callingProcessConditionalFlow | userTask | Post-subprocess continuation — Step Functions |
| serviceTask | executionListener | serviceTask | Event-driven — maintain with execution listener pattern |
| miTasks | executionListener | userTask | Multi-instance pattern — Step Functions map state |

---

## Human-Required Tasks

All 17 human-required tasks involve **approval or financial decision gates** with elevated risk scores (≥ 0.65). These tasks are classified as human-required because the combination of high AI benefit and high risk produces a low composite score, indicating that human judgment is essential for risk mitigation.

| # | Task | Process | BPMN Element | Risk | Composite | Reason |
|---|------|---------|-------------|------|-----------|--------|
| 1 | approve | noStartOrTaskForm | userTask | 0.65 | 0.09 | Approval gate, elevated financial/approval risk |
| 2 | Approve expenses | Multiple candidate groups example | userTask | 0.65 | 0.09 | Approval gate, elevated financial/approval risk |
| 3 | approve invoice | invoice receipt (fox) | userTask | 0.80 | 0.055 | Approval gate, high financial/approval risk |
| 4 | assign approver | invoice receipt (fox) | userTask | 0.80 | 0.025 | Approval gate, high financial/approval risk |
| 5 | approve invoice | invoice receipt (fox) [long ID] | userTask | 0.80 | 0.055 | Approval gate, high financial/approval risk |
| 6 | assign approver | invoice receipt (fox) [long ID] | userTask | 0.80 | 0.025 | Approval gate, high financial/approval risk |
| 7 | approve invoice | invoice receipt (fox) [long ID, non-exec] | userTask | 0.80 | 0.055 | Approval gate, high financial/approval risk |
| 8 | assign approver | invoice receipt (fox) [long ID, non-exec] | userTask | 0.80 | 0.025 | Approval gate, high financial/approval risk |
| 9 | Approve Invoice | Invoice Receipt (v1) | userTask | 0.73 | 0.061 | Approval gate, high financial/approval risk |
| 10 | Approve Invoice | Invoice Receipt (v2) | userTask | 0.73 | 0.061 | Approval gate, high financial/approval risk |
| 11 | Approve Request | Broken Process | userTask | 0.65 | 0.09 | Approval gate, elevated financial/approval risk |
| 12 | Approve Variables | Change Variables Process | userTask | 0.65 | 0.055 | Approval gate, elevated financial/approval risk |
| 13 | approve invoice | invoice receipt Generated Forms | userTask | 0.80 | 0.055 | Approval gate, high financial/approval risk |
| 14 | assign approver | invoice receipt Generated Forms | userTask | 0.80 | 0.025 | Approval gate, high financial/approval risk |
| 15 | Approve Invoice | Invoice Receipt (webapps/pa3) | userTask | 0.80 | 0.055 | Approval gate, high financial/approval risk |
| 16 | Approve Invoice | Invoice Receipt (deployment-binding) | userTask | 0.80 | 0.055 | Approval gate, high financial/approval risk |
| 17 | Approve Invoice | Invoice Receipt (webapps/common) | userTask | 0.80 | 0.055 | Approval gate, high financial/approval risk |

---

## Data Readiness Gaps

| Task | Data Source | Current State | Remediation |
|------|-----------|---------------|-------------|
| Check decision | DMN decision table inputs | Unknown — no `dataStoreReference` in BPMN, no ARA analysis | Run ARA on the DMN decision service. Business rule tasks typically consume structured inputs — likely ready. |
| evaluate decision table | DMN decision table inputs | Unknown — no `dataStoreReference` in BPMN, no ARA analysis | Run ARA on the DMN decision service. Business rule tasks typically consume structured inputs — likely ready. |
| Analyze report | Report data (unstructured) | Unknown — user task with no system references. One inferred dependency on `org.camunda.UnexistingClass` | Run ARA on the report generation system. Identify report format and data extraction requirements. |
| Review Invoice | Invoice document + form data | Unknown — user task with Camunda form (`review-invoice.html`), dynamic assignee `${reviewer}` | Run ARA on the invoice management system. Map form fields to agent input schema. Assess invoice document format (PDF, structured data, etc.). |
| Assign Reviewer | Reviewer pool / org data | Unknown — user task with Camunda form (`assign-reviewer.html`), hardcoded assignee `demo` | Run ARA on the identity/org management system. Map reviewer selection criteria to agent decision model. |

> **Data readiness could not be assessed from the BPMN model. Run ARA on the target systems for a complete classification.**

---

## ARA Cross-Reference

| Agent Task | Target System | ARA Profile | Blockers | Status |
|---|---|---|---|---|
| Check decision | DMN decision service | -- | -- | Pending ARA |
| evaluate decision table | DMN decision service | -- | -- | Pending ARA |
| Analyze report | Report analysis system | -- | -- | Pending ARA |
| Review Invoice | Invoice management system | -- | -- | Pending ARA |
| Assign Reviewer | Identity/org management | -- | -- | Pending ARA |

*No ARA report available. Run the Agentic Readiness Analysis on the target systems for a complete readiness view.*

---

## Implementation Roadmap

### Wave 1: Build Now

No tasks can be confirmed for immediate build — data readiness is unknown for all agent tasks.

**Potential Wave 1 candidates** (pending ARA confirmation):
- **Check decision** (composite: 0.265) — businessRuleTask with structured decision inputs; likely ready
- **evaluate decision table** (composite: 0.265) — businessRuleTask with structured decision inputs; likely ready

> Run ARA on the DMN decision services. If no DATA blockers are found, promote these two tasks to Wave 1.

### Wave 2: After Data Work

All 5 agent tasks are currently assigned to Wave 2 pending data readiness confirmation:

| Priority | Task | Composite | Process | Estimated Effort |
|----------|------|-----------|---------|-----------------|
| 1 | Check decision | 0.265 | process | Low (2 prerequisites) |
| 2 | evaluate decision table | 0.265 | Process | Low (2 prerequisites) |
| 3 | Analyze report | 0.195 | failingTimer | Medium (4 prerequisites) |
| 4 | Review Invoice | 0.160 | Review Invoice | Medium (4 prerequisites) |
| 5 | Assign Reviewer | 0.130 | Review Invoice | Medium (4 prerequisites) |

**Data work required:**
1. Run ARA on all target systems to assess data readiness
2. For user tasks: map Camunda form fields to agent input/output schemas
3. For business rule tasks: document DMN input/output contracts
4. Establish data pipelines for any unstructured data sources

### Wave 3: After System Remediation

Not applicable — no ARA findings available to identify system-level blockers. This wave will be populated after ARA analyses are completed.

---

## Process Structure Summary

| Metric | Value |
|--------|-------|
| **Total BPMN files found** | 2,503 |
| **Total files analyzed** | 2,446 |
| **Total files failed** | 57 |
| **Total processes** | 2,446 |
| **Total elements** | 9,442 |
| **Total flows** | 6,301 |
| **Tasks** | 3,484 |
| **Task types** | userTask: 1,995 · serviceTask: 801 · subProcess: 515 · scriptTask: 76 · task: 60 · businessRuleTask: 37 |
| **Processes with gateways** | 355 (14.5%) |
| **Linear processes (no gateways)** | 2,069 (84.6%) |
| **Max gateway depth** | 5 |
| **Deeply nested processes** | 10 |
| **Exclusive branches (XOR)** | 62 |
| **Parallel branches (AND)** | 0 |
| **Ordering constraints** | 632 |
| **Exclusion constraints** | 124 |
| **Coexistence constraints** | 712 |

**Key structural insight:** The vast majority of processes (84.6%) are linear chains with no branching, reflecting the repository's nature as an engine test suite with many minimal test-case processes. The 355 processes with gateways (14.5%) contain the meaningful business logic, including the invoice receipt and review workflows where agent opportunities concentrate. The 5 agent-eligible tasks exist in 4 processes with low to moderate constraint density (0.67–1.75), indicating straightforward integration paths.

---

## Cost Summary

| Metric | Value |
|--------|-------|
| Agent tasks | 5 |
| Total tokens/invocation (all agents) | 6,500 (1,300 × 5) |
| Cost per 1K invocations (per agent) | $2.70 |
| Monthly invocations (at 200/day) | 6,000 per task · 30,000 total |
| Estimated monthly cost (200/day) | **$81.00** |
| Estimated monthly cost (100/day, baseline) | $40.50 |
| Recommended model | Claude Haiku 3.5 |
| Cost model | Pay-per-token (Amazon Bedrock) |

---

*Report generated by BPMN Agentic Opportunity Analysis. Classification scores are deterministic (computed from BPMN topology and scoring rules). Opportunity categories and autonomy levels are derived from the classification model described in the transformation definition.*
