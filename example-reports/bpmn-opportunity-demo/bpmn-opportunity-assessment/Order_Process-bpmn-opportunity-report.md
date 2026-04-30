# BPMN Agentic Opportunity Assessment: Order Process

**Repository**: camunda-bpm-examples
**BPMN File**: clients/java/order-handling/order-handling.bpmn
**Date**: 2025-07-17
**Priority**: P1
**Context**: Official Camunda Platform 7 usage examples covering service tasks, external tasks, multi-tenancy, and Spring Boot integration patterns.
**Daily Volume**: 200

---

## Summary

Order Process contains 2 tasks. 0 are agent opportunities (0 build-now, 0 data-first), 2 are automatable with deterministic logic, and 0 require human involvement. Estimated monthly Bedrock cost for agent tasks: $0.00 at 200 invocations/day.

This is a lightweight, linear order-handling process built on the Camunda Platform 7 external task pattern. Both tasks are deterministic service operations (invoice creation and archival) with low AI benefit scores and no reasoning complexity that would warrant agentic AI. The recommended path is to keep these as deterministic service automations.

---

## Opportunity Classification

| Task | Type | BPMN Element | AI Benefit | Complexity | Risk | Effort | Composite | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------------|------|--------|-----------|----------|----------|---------|
| Task_1nbdup3 (Create Invoice subprocess) | service | subProcess | 0.35 | 0.60 | 0.30 | 0.60 | 0.050 | Automate | -- | -- |
| Archive invoice | service | serviceTask | 0.20 | 0.30 | 0.30 | 0.20 | 0.005 | Automate | -- | -- |

---

## Agent Opportunities (ranked by composite score)

No tasks were classified as agent opportunities in this process. All tasks are deterministic and suitable for automation via service connectors or rule engines.

Both tasks scored below the agent threshold on AI benefit (0.35 and 0.20 respectively), confirming that the business logic involved — invoice creation and invoice archival — is mechanical and does not require LLM-based reasoning, judgment, or natural-language understanding.

---

## Automatable Tasks

| Task | BPMN Element | External Topic | Scores (AI / Complexity / Risk / Effort) | Recommendation |
|------|-------------|----------------|------------------------------------------|----------------|
| Task_1nbdup3 (Create Invoice subprocess) | subProcess | invoiceCreator | 0.35 / 0.60 / 0.30 / 0.60 | Retain as Camunda external task worker. Alternatively, migrate to AWS Step Functions with a Lambda function for invoice creation. Deterministic logic — no LLM required. |
| Archive invoice | serviceTask | invoiceArchiver | 0.20 / 0.30 / 0.30 / 0.20 | Retain as Camunda external task worker. Alternatively, implement as a Step Functions task or EventBridge rule that triggers an S3/archival Lambda. Deterministic logic — no LLM required. |

---

## Human-Required Tasks

No tasks in this process require mandatory human involvement.

All tasks are classified as `service` type with low risk scores (0.30), indicating no regulatory gates, approval steps, or subjective decision points that would mandate human-in-the-loop.

---

## Data Readiness Gaps

| Task | Data Source | Current State | Assessment | Remediation |
|------|-----------|---------------|------------|-------------|
| Task_1nbdup3 (Create Invoice subprocess) | External task topic: `invoiceCreator` | API-based (Camunda external task pattern) | Ready | No remediation needed. External task workers provide structured JSON input/output. |
| Archive invoice | External task topic: `invoiceArchiver` | API-based (Camunda external task pattern) | Ready | No remediation needed. External task workers provide structured JSON input/output. |

> **Note**: Data readiness was assessed as **Ready** for both service tasks based on the Camunda external task pattern, which implies structured API-based data exchange. However, data readiness could not be fully assessed from BPMN model metadata alone (no `dataStoreReference` or `dataObject` elements are present in the BPMN file). Run ARA on the target systems for a complete classification.

---

## ARA Cross-Reference

*No ARA report available. Run the Agentic Readiness Assessment on the target systems for a complete readiness view.*

No `ara_report_path` was provided in the assessment configuration. To get a full picture of system readiness — including authentication patterns, data accessibility, API maturity, and infrastructure blockers — run the Agentic Readiness Assessment (ARA) on the systems backing the `invoiceCreator` and `invoiceArchiver` external task topics.

---

## Implementation Roadmap

### Wave 1: Build Now

Both service tasks can be implemented immediately as deterministic automations. No data remediation or system changes are required.

| Task | Action | Estimated Effort |
|------|--------|-----------------|
| Task_1nbdup3 (Create Invoice subprocess) | Retain existing Camunda external task worker or migrate to AWS Step Functions + Lambda. Deploy REST API wrapper as described in the analysis report. | Low — existing external task worker pattern already provides service connectivity. |
| Archive invoice | Retain existing Camunda external task worker or migrate to AWS Step Functions + Lambda / EventBridge rule. Deploy REST API wrapper as described in the analysis report. | Low — deterministic archival with structured input. |

### Wave 2: After Data Work

No tasks require data remediation before implementation.

### Wave 3: After System Remediation

No tasks are blocked by system-level issues. (ARA assessment not available to confirm — see ARA Cross-Reference section.)

---

## Process Structure Summary

| Metric | Value |
|--------|-------|
| **Total elements** | 5 |
| **Tasks** | 2 (1 subProcess, 1 serviceTask) |
| **Gateways** | 0 |
| **Events** | 3 (1 timer start event, 1 conditional boundary event, 2 end events) |
| **Exclusive branches (XOR)** | 0 |
| **Parallel branches (AND)** | 0 |
| **Linear chains** | 1 |
| **Sequence flows** | 4 |
| **Constraint density** | 0.60 |
| **Max gateway depth** | 0 |

**Key structural insight**: This is a compact, linear process with no gateway-based branching. The process starts on a timer schedule (cron: `0/5 0/1 * 1/1 * ?`), executes a subprocess containing a single "Create Invoice" service task via Camunda external task worker, and terminates. A conditional boundary event (`${invoiceId != null}`) on the subprocess triggers an optional "Archive invoice" service task on a separate path, creating two possible end states. The absence of gateways and parallel paths makes this process straightforward to automate with deterministic service orchestration.

**Dependencies** (inferred from Camunda external task pattern):

| Source Task | Target | Type | Confidence |
|------------|--------|------|------------|
| Create Invoice (Task_06z99p1) | external:invoiceCreator | service_endpoint | High |
| Archive invoice (Task_1yjkccw) | external:invoiceArchiver | service_endpoint | High |

---

## Cost Summary

| Metric | Value |
|--------|-------|
| Agent tasks | 0 |
| Total tokens/invocation (all agents) | 0 |
| Estimated monthly cost (200/day) | $0.00 |
| Recommended models | N/A — no agent tasks identified |

All tasks in this process are deterministic service operations. No LLM inference costs apply. The operational cost is limited to compute for external task workers (or equivalent Lambda/Step Functions execution costs if migrated to AWS).
