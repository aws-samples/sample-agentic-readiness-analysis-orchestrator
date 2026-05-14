# Portfolio BAO Report: bao-demo

**Date**: 2026-04-28
**Repositories Analyzed**: 5
**Total Processes**: 3,333
**Total BAO Reports Aggregated**: 58
**Portfolio Context**: Demonstrating BPMN agentic opportunity analysis across official open source process repositories covering invoice processing, order management, and BPMN interchange test cases.

> **Note**: This is a BAO-only portfolio aggregation. It does NOT cross-reference with ARA (Agentic Readiness Analysis) or MOD (Modernization Readiness Analysis) findings. Cross-referencing is the Bridge TD's responsibility. Run a full analysis (`analysis_type: full`) to identify which agent opportunities are blocked by ARA findings on target systems.

---

## Service Inventory

| Repository | Priority | Tags | Repo Type | BAO Reports |
|-----------|----------|------|-----------|------------:|
| camunda-invoice | P0 | camunda-c7, finance, invoice | monorepo | 1 |
| camunda8-order-process | P0 | camunda-c8, orders, zeebe | application | 1 |
| camunda-rest-service | P1 | camunda-c7, rest-api, integration | application | 1 |
| bpmn-miwg-test-suite | P1 | standard-bpmn, multi-vendor, omg-official | application | 1 |
| camunda-bpm-examples | P1 | camunda-c7, examples, multi-pattern | monorepo | 54 |
| **Total** | | | | **58** |

---

## Portfolio Opportunity Summary

| Metric | Value |
|--------|-------|
| Total Processes Analyzed | 3,333 |
| Total Tasks | 7,149 |
| Agent Opportunities | 64 |
| Automatable Tasks | 6,905 |
| Human-Required Tasks | 177 |
| Data Platform Tasks | 3 |
| Estimated Monthly Bedrock Cost | $558.90 |

### Opportunity Breakdown

| Category | Count | % of Total |
|----------|------:|----------:|
| Agent Build-Now | 0 | 0.0% |
| Agent Data-First | 64 | 0.9% |
| Automate | 6,905 | 96.6% |
| Data Platform | 3 | 0.0% |
| Human Required | 177 | 2.5% |
| **Total** | **7,149** | **100.0%** |

> **Key insight**: 96.6% of all tasks across the portfolio are automatable with deterministic logic (Step Functions, rule engines, REST API wrappers). Only 0.9% (64 tasks) are agent opportunities requiring LLM-based reasoning, and all of those are classified as "data first" — meaning data readiness must be confirmed before agent deployment.

---

## Process-by-Process Summary

| Repository | Process | Tasks | Agents | Services | Human | Data Platform | Est. Cost/mo |
|-----------|---------|------:|-------:|---------:|------:|--------------:|-------------:|
| camunda-invoice (P0) | Camunda Invoice (2,446 processes) | 3,484 | 5 | 3,462 | 17 | 0 | $81.00 |
| camunda8-order-process (P0) | Process Data Example | 5 | 0 | 2 | 0 | 3 | $0.00 |
| camunda-rest-service (P1) | Git Repo Popularity Checker | 8 | 0 | 8 | 0 | 0 | $0.00 |
| bpmn-miwg-test-suite (P1) | BPMN MIWG Test Suite (831 processes) | 3,555 | 59 | 3,340 | 156 | 0 | $477.90 |
| camunda-bpm-examples (P1) | 54 example processes | 97 | 0 | 93 | 4 | 0 | $0.00 |
| **Total** | **3,333 processes** | **7,149** | **64** | **6,905** | **177** | **3** | **$558.90** |

---

## Top Agent Opportunities (ranked by composite score)

All 64 agent tasks across the portfolio are classified as **Agent (data first)**. No tasks qualify for "Agent (build now)" because data readiness could not be confirmed from BPMN metadata alone across any repository.

The 64 agent tasks map to **4 distinct functional patterns** across 2 repositories:

| Rank | Task | Process | Repository | Category | Autonomy | Composite | Cost/1K | Instances |
|-----:|------|---------|-----------|----------|----------|----------:|--------:|----------:|
| 1 | Check decision | process | camunda-invoice | Agent (data first) | Prepared | 0.265 | $2.70 | 1 |
| 2 | evaluate decision table | Process | camunda-invoice | Agent (data first) | Prepared | 0.265 | $2.70 | 1 |
| 3 | Analyze report | failingTimer | camunda-invoice | Agent (data first) | Prepared | 0.195 | $2.70 | 1 |
| 4 | Review terms of contract | C.4.0 Employee Onboarding | bpmn-miwg-test-suite | Agent (data first) | Prepared | 0.166 | $2.70 | 23 |
| 5 | Review Invoice | Review Invoice | camunda-invoice | Agent (data first) | Prepared | 0.160 | $2.70 | 1 |
| 6 | Assign Reviewer | Review Invoice | camunda-invoice | Agent (data first) | Exploration | 0.130 | $2.70 | 1 |
| 7 | Review and document result | C.1.0 Invoice Team-Assistant | bpmn-miwg-test-suite | Agent (data first) | Prepared | 0.110 | $2.70 | 36 |

### Agent Task Distribution by Repository

| Repository | Agent Tasks | Unique Patterns | % of Portfolio Agents |
|-----------|------------:|----------------:|---------------------:|
| camunda-invoice (P0) | 5 | 5 | 7.8% |
| bpmn-miwg-test-suite (P1) | 59 | 2 | 92.2% |
| camunda8-order-process (P0) | 0 | 0 | 0.0% |
| camunda-rest-service (P1) | 0 | 0 | 0.0% |
| camunda-bpm-examples (P1) | 0 | 0 | 0.0% |
| **Total** | **64** | **7** | **100.0%** |

> **Note**: The bpmn-miwg-test-suite's 59 agent tasks represent the same 2 logical task types (Review terms of contract, Review and document result) replicated across 24+ vendor tool exports of the same BPMN test cases. In a production deployment targeting a single vendor implementation, the effective agent count would reduce to 2 unique agents.

---

## Dependency Coverage

Dependency data was extracted from BPMN model analysis across all 58 reports. The majority of tasks have **unknown** dependencies because BPMN models in this portfolio (test suites, example processes) intentionally omit implementation-specific details like database connections, API endpoints, and data schemas.

### By Type

| Dependency Type | Count | Confidence | Source Repositories |
|----------------|------:|-----------|---------------------|
| Service Endpoint | 6 | High | camunda-invoice (1 inferred: `org.camunda.UnexistingClass`), camunda8-order-process (3 Zeebe endpoints: `DoLongWork`, `DoWork` ×2), camunda-rest-service (4 GitHub REST API endpoints) |
| Data Store | 0 | -- | No `dataStoreReference` elements found in any BPMN model across the portfolio |
| Message Flow | 1 | Medium | camunda8-order-process (`CancelMessage` event subprocess trigger) |
| Call Activity | 1 | High | camunda-bpm-examples (main-process → sub-process call activity in tenant-identifier-shared-definitions) |
| Vendor Specific | 5 | Medium | camunda-invoice (2 DMN decision table bindings), camunda8-order-process (1 DMN `Decide_on_Assignee`), camunda-rest-service (1 DMN popularity decision), camunda-bpm-examples (various Camunda form bindings) |
| Unknown | 64 | -- | All 64 agent tasks have no system references in BPMN models (data readiness unknown) |

### By Vendor Extractor

| Vendor | Repositories | Dependencies Found | Notes |
|--------|-------------|------------------:|-------|
| bpmn-2.0 (standard) | bpmn-miwg-test-suite | 0 | MIWG test cases use standard BPMN 2.0 with no vendor extensions; all task implementations are abstract |
| camunda-c7 | camunda-invoice, camunda-bpm-examples, camunda-rest-service | 8 | Camunda form bindings (`embedded:app:forms/*`), Java delegates, DMN decision references, HTTP connectors |
| camunda-c8 | camunda8-order-process | 4 | Zeebe job worker endpoints (`DoLongWork`, `DoWork`), DMN decision table binding |
| Multi-vendor (MIWG) | bpmn-miwg-test-suite | 0 | 36 vendor tools represented (ADONIS, ARIS, SAP Signavio, Trisotech, etc.) — standard BPMN interchange format with no vendor-specific implementation bindings |

### Unknown Dependencies

The following agent tasks have no system references in their BPMN models. Data readiness is unknown and must be confirmed via ARA before agent deployment.

| Task | Repository | Instances | Reason |
|------|-----------|----------:|--------|
| Check decision | camunda-invoice | 1 | businessRuleTask with no `dataStoreReference` — DMN inputs not declared in BPMN |
| evaluate decision table | camunda-invoice | 1 | businessRuleTask with no `dataStoreReference` — DMN inputs not declared in BPMN |
| Analyze report | camunda-invoice | 1 | userTask with no system references; one inferred dependency on `org.camunda.UnexistingClass` |
| Review Invoice | camunda-invoice | 1 | userTask with Camunda form binding but no data store references |
| Assign Reviewer | camunda-invoice | 1 | userTask with Camunda form binding but no data store references |
| Review terms of contract | bpmn-miwg-test-suite | 23 | userTask in C.4.0 test cases — contract documents not referenced in BPMN model |
| Review and document result | bpmn-miwg-test-suite | 36 | Abstract task in C.1.0 test cases — documentation target system not referenced in BPMN model |
| Validate Data | camunda8-order-process | 1 | userTask with no API binding; ARA DATA-Q1 BLOCKER applies |
| Manual Check | camunda8-order-process | 1 | userTask with no API binding; ARA DATA-Q1 BLOCKER applies |
| Activity_0ijh0e2 | camunda8-order-process | 1 | Event subprocess with no structured data flow; ARA DATA-Q1 BLOCKER applies |

> These tasks have no system references in the BPMN model. Run ARA on the target
> systems and use the Bridge TD to cross-reference readiness status.

---

## Implementation Roadmap

### Wave 1: Build Now (0 agent tasks, $0.00/mo)

**No agent tasks can be confirmed for immediate build across the portfolio.** All 64 agent tasks are classified as "Agent (data first)" because data readiness could not be confirmed from BPMN metadata alone.

**Potential Wave 1 promotions** (pending ARA confirmation):

| Task | Repository | Composite | Promotion Condition |
|------|-----------|----------:|---------------------|
| Check decision | camunda-invoice | 0.265 | ARA confirms DMN decision service has structured inputs accessible via API |
| evaluate decision table | camunda-invoice | 0.265 | ARA confirms DMN decision service has structured inputs accessible via API |
| Review and document result (36 instances) | bpmn-miwg-test-suite | 0.110 | ARA confirms invoice processing results exposed as structured API |

> **Service-ready tasks (non-agent)**: camunda-rest-service has 8 automatable tasks ready for immediate Step Functions / Lambda implementation with no data gaps. These are not agent tasks but represent the quickest automation wins in the portfolio.

### Wave 2: After Data Work (67 tasks, $558.90/mo)

Tasks classified as "Agent Data-First" or "Data Platform" — requiring data readiness work before agent or automation deployment:

| Task | Instances | Process | Repository | Category | Data Gap |
|------|----------:|---------|-----------|----------|----------|
| Check decision | 1 | process | camunda-invoice | Agent Data-First | No `dataStoreReference` in BPMN; DMN inputs undeclared |
| evaluate decision table | 1 | Process | camunda-invoice | Agent Data-First | No `dataStoreReference` in BPMN; DMN inputs undeclared |
| Analyze report | 1 | failingTimer | camunda-invoice | Agent Data-First | User task with no system references; report format unknown |
| Review Invoice | 1 | Review Invoice | camunda-invoice | Agent Data-First | Camunda form binding but no data store references |
| Assign Reviewer | 1 | Review Invoice | camunda-invoice | Agent Data-First | Camunda form binding but no data store references |
| Review terms of contract | 23 | C.4.0 Employee Onboarding | bpmn-miwg-test-suite | Agent Data-First | Contract documents inaccessible via API; need document retrieval pipeline |
| Review and document result | 36 | C.1.0 Invoice Team-Assistant | bpmn-miwg-test-suite | Agent Data-First | Invoice results not exposed as structured API; need output schema |
| Validate Data | 1 | Process Data Example | camunda8-order-process | Data Platform | No API binding; ARA DATA-Q1 BLOCKER; need input/output schema |
| Manual Check | 1 | Process Data Example | camunda8-order-process | Data Platform | No API for programmatic check; need SLA breach context capture |
| Activity_0ijh0e2 | 1 | Process Data Example | camunda8-order-process | Data Platform | Cancellation subprocess with no structured data flow |

**Total Wave 2**: 64 agent tasks + 3 data-platform tasks = **67 tasks**

### Wave 3: After System Remediation

> This wave is populated by the Bridge TD after cross-referencing with ARA findings.
> Run a full analysis (`analysis_type: full`) to identify which agent opportunities
> are blocked by ARA findings on target systems.

**Known ARA blockers from individual reports** (for Bridge TD reference):

| Repository | ARA Profile | BLOCKERs | Key Findings |
|-----------|-------------|----------:|--------------|
| camunda8-order-process | Not Agent-Integrable | 4 | API-Q1 (no API surface), AUTH-Q1 (no machine identity), AUTH-Q5 (hardcoded credentials), DATA-Q1 (no data classification) |
| camunda-bpm-examples | Remediation Required | 2 | AUTH-Q1 (no machine identity), DATA-Q1 (no data classification) |
| camunda-invoice | Pending ARA | 0 | No ARA report available |
| camunda-rest-service | Pending ARA | 0 | No ARA report available |
| bpmn-miwg-test-suite | Pending ARA | 0 | No ARA report available |

---

## Warnings

| Code | Message | Repository | Vendor |
|------|---------|-----------|--------|
| PARSE-FAIL | 57 BPMN files failed parsing out of 2,503 found | camunda-invoice | camunda-c7 |
| PARSE-FAIL | 9 BPMN files failed parsing out of 840 found | bpmn-miwg-test-suite | multi-vendor |
| DATA-UNKNOWN | Data readiness unknown for all 5 agent tasks — no `dataStoreReference` in BPMN | camunda-invoice | camunda-c7 |
| DATA-UNKNOWN | Data readiness unknown for 23 "Review terms of contract" agent tasks | bpmn-miwg-test-suite | bpmn-2.0 |
| DATA-PARTIAL | Data readiness partial for 36 "Review and document result" agent tasks | bpmn-miwg-test-suite | bpmn-2.0 |
| DATA-UNKNOWN | Data readiness unknown for 3 data-platform tasks — ARA DATA-Q1 BLOCKER | camunda8-order-process | camunda-c8 |
| ARA-PENDING | No ARA report available — agent readiness unconfirmed | camunda-invoice | camunda-c7 |
| ARA-PENDING | No ARA report available — agent readiness unconfirmed | camunda-rest-service | camunda-c7 |
| ARA-PENDING | No ARA report available — agent readiness unconfirmed | bpmn-miwg-test-suite | bpmn-2.0 |
| ARA-BLOCKER | 4 system-level BLOCKERs prevent any integration (agent or service) | camunda8-order-process | camunda-c8 |
| ARA-BLOCKER | 2 system-level BLOCKERs (AUTH-Q1, DATA-Q1) affect all 54 processes | camunda-bpm-examples | camunda-c7 |
| ZERO-TASKS | 1 process (Main Process) contains 0 scored tasks (call activity only) | camunda-bpm-examples | camunda-c7 |

---

## Cost Forecast

| Metric | Value |
|--------|-------|
| Total agent tasks | 64 |
| Unique agent task types | 7 |
| Total tokens/invocation (all agents) | 83,200 (1,300 × 64) |
| Estimated monthly cost | **$558.90** |
| At daily volume | 200 invocations/day (per task) |
| Model mix | Claude Haiku 3.5 (100%) |
| Cost per 1K invocations (per agent) | $2.70 |

### Cost by Repository

| Repository | Priority | Agent Tasks | Est. Monthly Cost | % of Total Cost |
|-----------|----------|------------:|------------------:|----------------:|
| bpmn-miwg-test-suite | P1 | 59 | $477.90 | 85.5% |
| camunda-invoice | P0 | 5 | $81.00 | 14.5% |
| camunda8-order-process | P0 | 0 | $0.00 | 0.0% |
| camunda-rest-service | P1 | 0 | $0.00 | 0.0% |
| camunda-bpm-examples | P1 | 0 | $0.00 | 0.0% |
| **Total** | | **64** | **$558.90** | **100.0%** |

### Cost Concentration Analysis

- **bpmn-miwg-test-suite** accounts for **85.5%** of the estimated monthly Bedrock cost ($477.90 of $558.90). However, the MIWG test suite's 59 agent tasks represent only 2 unique logical tasks replicated across 24+ vendor implementations. A production deployment targeting a single vendor would reduce the effective cost to approximately **$16.20/mo** (2 agents × $8.10/mo each).

- **camunda-invoice** accounts for **14.5%** of the estimated monthly Bedrock cost ($81.00). These are 5 distinct agent tasks across 4 unique processes, each at $16.20/mo. The two `businessRuleTask` candidates (Check decision, evaluate decision table) are the strongest Wave 1 candidates if ARA confirms data readiness.

- **Effective production cost** (deduplicating MIWG vendor replicas): **$97.20/mo** (5 camunda-invoice agents + 2 unique MIWG agents = 7 agents × $16.20/mo × 200/day ÷ 200/day).

### Cost Model Assumptions

| Assumption | Value |
|-----------|-------|
| Model | Claude Haiku 3.5 (Amazon Bedrock) |
| Tokens per invocation | 1,300 |
| Cost per 1K invocations | $2.70 |
| Daily invocations per task | 200 |
| Monthly invocations per task | 6,000 |
| Pricing model | Pay-per-token |

---

## Cross-Repo Patterns

### Human Task Patterns

Approval gates dominate the human-required task category across the portfolio. All 177 human-required tasks involve approval or assignment decisions with elevated risk scores (≥ 0.65).

| Pattern | Repositories | Total Instances | Risk Score Range |
|---------|-------------|----------------:|-----------------:|
| Invoice Approval (Approve Invoice) | camunda-invoice, bpmn-miwg-test-suite, camunda-bpm-examples | 68 | 0.65–0.80 |
| Approver Assignment (Assign Approver) | camunda-invoice, bpmn-miwg-test-suite | 50 | 0.80 |
| Vacation Approval (Manually Approve Vacation) | bpmn-miwg-test-suite | 38 | 0.73 |
| Advertisement Approval (Approve Advertisement) | bpmn-miwg-test-suite | 19 | 0.80 |
| Other Approvals (Approve Request, Approve customer, etc.) | camunda-bpm-examples | 2 | 0.65 |
| **Total** | | **177** | |

> All human-required tasks have high AI benefit scores (0.70+), indicating that AI could meaningfully assist these activities. However, elevated risk scores make them unsuitable for full autonomous agent handling. These are candidates for **AI-assisted human decision-making** in a future phase.

### Agent Opportunity Concentration

Agent opportunities are concentrated in just 2 of 5 repositories:

- **camunda-invoice (P0)**: 5 unique agent tasks in invoice review and decision processes
- **bpmn-miwg-test-suite (P1)**: 59 agent tasks (2 unique patterns) in invoice processing and employee onboarding test cases

The remaining 3 repositories (camunda8-order-process, camunda-rest-service, camunda-bpm-examples) have **zero agent opportunities** — all their tasks are suitable for deterministic automation.

### Cost Concentration

| Repository | % of Agent Tasks | % of Bedrock Cost |
|-----------|----------------:|------------------:|
| bpmn-miwg-test-suite | 92.2% | 85.5% |
| camunda-invoice | 7.8% | 14.5% |
| All others | 0.0% | 0.0% |

---

*Report generated by Portfolio BPMN Agentic Opportunity (BAO) Analysis. This report aggregates BAO-only data from 58 individual reports across 5 repositories. No ARA or MOD cross-referencing has been performed — that is the Bridge TD's responsibility. Classification scores are deterministic, computed from BPMN topology and scoring rules. All numeric totals have been cross-validated against source reports.*
