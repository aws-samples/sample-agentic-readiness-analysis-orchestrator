# BPMN Agentic Opportunity Assessment: Invoice Receipt

**Repository**: camunda-bpm-platform
**BPMN File**: examples/invoice/src/main/resources/invoice.v2.bpmn
**Date**: 2025-07-16
**Priority**: P0
**Context**: Camunda 7 invoice receipt process with Java delegate service tasks, DMN business rules, data store references, and call activities.
**Daily Volume**: 200

---

## Summary

Invoice Receipt contains 4 tasks. 0 are agent opportunities (0 build-now, 0 data-first), 3 are automatable with deterministic logic, and 1 requires human involvement. Estimated monthly Bedrock cost for agent tasks: $0.00 at 200 invocations/day.

This process is a well-structured Camunda 7 workflow that already leverages DMN business rules for approver assignment and a Java delegate for invoice archiving. The analysis finds that all automatable tasks are best served by deterministic service wrappers (REST APIs, Step Functions, or rule engines) rather than agentic AI. The single human-required task — Approve Invoice — involves a high-risk financial approval decision (risk score: 0.73) that must remain under human control.

## Opportunity Classification

| Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------|----------|----------|---------|
| Assign Approver Group | service | businessRuleTask | 0.65 | 0.60 | Automate | -- | -- |
| Approve Invoice | human | userTask | 0.70 | 0.73 | Human Required | -- | -- |
| Prepare Bank Transfer | service | userTask | 0.40 | 0.38 | Automate | -- | -- |
| Archive Invoice | service | serviceTask | 0.15 | 0.30 | Automate | -- | -- |

## Agent Opportunities (ranked by composite score)

No tasks were classified as agent opportunities in this process.

All tasks with potential AI benefit are either service-automatable (deterministic logic suitable for REST APIs and rule engines) or require human involvement due to elevated risk scores. The "Assign Approver Group" task has the highest AI benefit score (0.65) but is already implemented as a DMN business rule task with well-defined decision tables, making it a clear candidate for deterministic automation rather than agentic AI. The "Approve Invoice" task has a high AI benefit score (0.70) but its risk score of 0.73 places it firmly in the human-required category for financial approval decisions.

**Note:** If business requirements evolve to allow AI-assisted invoice approval with human oversight, the "Approve Invoice" task could be reconsidered as an agent opportunity with **Guardrail** autonomy (risk > 0.6). This would require explicit risk acceptance from process owners and regulatory review.

## Automatable Tasks

| Task | BPMN Element | Data Readiness | Recommendation |
|------|-------------|----------------|----------------|
| Assign Approver Group | businessRuleTask | Ready | DMN engine call or REST API wrapper. The existing DMN decision table (`invoice-assign-approver`) with COLLECT hit policy already implements the full logic. Wrap as a REST endpoint or invoke via Camunda DMN engine API. |
| Prepare Bank Transfer | userTask | Ready | REST API wrapper with Financial Accounting System integration. The task references `DataStoreReference_1` (Financial Accounting System) via `DataInputAssociation`. Convert to a Step Functions state or REST endpoint that reads from the data store and prepares transfer data. |
| Archive Invoice | serviceTask | Ready | Existing Java delegate (`ArchiveInvoiceService`) already implements the logic. Expose as a REST endpoint or containerized Lambda function. The delegate processes `invoiceDocument` (FileValue) and `invoiceNumber` variables. |

### Detailed Automation Recommendations

#### 1. Assign Approver Group (assignApprover)
- **Current Implementation**: Camunda businessRuleTask referencing DMN decision `invoice-assign-approver`
- **DMN Details**: Two-stage decision — `invoiceClassification` (maps amount + category → classification) feeds into `invoice-assign-approver` (maps classification → approver group, COLLECT hit policy)
- **Decision Inputs**: `amount` (double), `invoiceCategory` (string: "Travel Expenses", "Misc", "Software License Costs")
- **Decision Output**: `approverGroups` (collected string entries: "management", "accounting", "sales")
- **Migration Path**: Wrap DMN evaluation as REST API. The decision logic is fully deterministic with 5 classification rules and 3 approver assignment rules. No AI reasoning needed.
- **Composite Score**: 0.095

#### 2. Prepare Bank Transfer (prepareBankTransfer)
- **Current Implementation**: Camunda userTask with form key `embedded:app:forms/prepare-bank-transfer.html`
- **Data Association**: `DataInputAssociation` from `DataStoreReference_1` → Financial Accounting System
- **Migration Path**: Replace human task with REST API that reads from Financial Accounting System data store and prepares bank transfer payload. Candidate groups: `accounting`.
- **Composite Score**: 0.016

#### 3. Archive Invoice (ServiceTask_1)
- **Current Implementation**: Camunda serviceTask with `camunda:class="org.camunda.bpm.example.invoice.service.ArchiveInvoiceService"` (JavaDelegate)
- **Implementation Details**: Reads `shouldFail` (Boolean) and `invoiceDocument` (FileValue) variables. Logs invoice number and filename. Simple archiving operation.
- **Migration Path**: Already a service task. Expose existing Java delegate as REST endpoint or containerize as Lambda. No changes to business logic needed.
- **Composite Score**: -0.015

## Human-Required Tasks

| Task | BPMN Element | Risk Score | Reason |
|------|-------------|------------|--------|
| Approve Invoice | userTask | 0.73 | Financial approval gate requiring human judgment. High-risk decision involving invoice approval/rejection that triggers either bank transfer (approved) or review cycle (not approved). Candidate groups determined dynamically by DMN rule (`${approverGroups}`). |

### Approve Invoice — Detailed Analysis
- **Element ID**: approveInvoice
- **Form**: `embedded:app:forms/approve-invoice.html`
- **Assignment**: Dynamic via `${approverGroups}` candidate groups, with task listener scripts for assignee management
- **Structural Position**: Sits between "Assign Approver Group" (upstream) and the exclusive gateway "Invoice approved?" (downstream). Rejection loops back to "Review Invoice" call activity, creating an approval-review cycle.
- **AI Augmentation Opportunity**: While this task must remain human-controlled, AI could augment the approver by:
  - Surfacing similar past invoice decisions
  - Flagging anomalies in invoice amounts or categories
  - Pre-populating approval recommendations (with explicit human override)
  - This would require **Guardrail** autonomy level (risk > 0.6): Human acts freely, agent monitors for errors.

## Data Readiness Gaps

| Task | Data Source | Current State | Remediation |
|------|-----------|---------------|-------------|
| Approve Invoice | Unknown — no data store or system references in BPMN | Unknown — user task with form key and candidate groups only; no explicit data associations | Run ARA (Agentic Readiness Assessment) on the systems providing invoice data for approval decisions. Identify data sources, APIs, and access patterns. |

**Note**: Data readiness could not be fully assessed from the BPMN model alone for the "Approve Invoice" task. The task's input data likely comes from process variables set by earlier tasks (invoice document, amount, category, creditor) but the BPMN model does not declare explicit data store references for this task. Run ARA on the target systems for a complete classification.

## ARA Cross-Reference

| Agent Task | Target System | ARA Profile | Blockers | Status |
|---|---|---|---|---|
| *(No agent tasks identified)* | -- | -- | -- | -- |

*No ARA report available. Run the Agentic Readiness Assessment on the target systems for a complete readiness view.*

No `ara_report_path` was provided in the assessment configuration. To complete the readiness picture:
1. Run ARA on the **Financial Accounting System** (referenced by `prepareBankTransfer` via `DataStoreReference_1`)
2. Run ARA on the **invoice document storage system** (referenced by `ArchiveInvoiceService`)
3. Run ARA on the **approval workflow system** to assess data readiness for potential future AI augmentation of the "Approve Invoice" task

## Implementation Roadmap

### Wave 1: Build Now
All three automatable service tasks have ready data and existing implementations. They can be migrated to deterministic REST endpoints immediately.

| Priority | Task | Action | Effort Score | Prerequisites |
|----------|------|--------|-------------|---------------|
| 1 | Archive Invoice | Expose existing `ArchiveInvoiceService` Java delegate as REST endpoint or Lambda | 0.20 | Deploy as REST API; configure BPM connector to call REST instead of Java delegate |
| 2 | Assign Approver Group | Wrap DMN decision `invoice-assign-approver` as REST API | 0.20 | Deploy DMN engine as REST API; define input/output JSON schema matching current decision table |
| 3 | Prepare Bank Transfer | Build REST API wrapper with Financial Accounting System integration | 0.50 | Map user task input/output to REST request/response; integrate with Financial Accounting System data store; configure BPM connector |

### Wave 2: After Data Work
No tasks currently identified for this wave. All automatable tasks have ready data.

### Wave 3: After System Remediation
No tasks currently identified for this wave. No ARA blockers have been assessed (ARA report not available).

### Future Consideration
- **Approve Invoice**: Remains human-required. Consider AI augmentation (Guardrail autonomy) as a future enhancement once:
  - ARA has been run on the approval system and data sources
  - Historical approval decision data is available for pattern analysis
  - Regulatory and compliance review has been completed for AI-assisted financial approvals

## Process Structure Summary

- **Total elements**: 9
- **Tasks**: 4 (1 businessRuleTask, 2 userTasks, 1 serviceTask) + 1 callActivity (Review Invoice)
- **Gateways**: 2 (both exclusive/XOR: "Invoice approved?" and "Review successful?")
- **Events**: 3 (1 start event: "Invoice received", 2 end events: "Invoice not processed", "Invoice processed")
- **Exclusive branches (XOR)**: 2
- **Parallel branches (AND)**: 0
- **Linear chains**: 2 (StartEvent → Assign Approver → Approve Invoice; Prepare Bank Transfer → Archive Invoice → End)
- **Constraint profile**: 12 total constraints, density 1.33, max gateway depth 2
  - Ordering: 4 | Exclusion: 0 | Coexistence: 3
  - Succession: 3 | Precedence: 1 | Chain succession: 1 | Chain precedence: 1 | Alternate response: 1
- **Key structural insight**: The process features an approval loop pattern — when an invoice is not approved, it flows to a "Review Invoice" call activity (subprocess with 2 user tasks), then back through a "Review successful?" gateway that either loops to "Approve Invoice" again or terminates the process. This creates a bounded retry cycle with two exit paths (approved → bank transfer → archive → done; review failed → invoice not processed). The loop pattern means the approval task may execute multiple times per process instance, which is a key consideration for volume estimation.

## Cost Summary

| Metric | Value |
|--------|-------|
| Agent tasks | 0 |
| Total tokens/invocation (all agents) | 0 |
| Estimated monthly cost (200/day) | $0.00 |
| Recommended models | N/A — no agent tasks identified |

**Cost note**: This process has zero agentic AI cost because all automatable tasks are deterministic and best served by service wrappers (REST APIs, rule engines, Step Functions). The three automatable tasks will incur standard compute costs (Lambda/ECS/EC2) rather than LLM token costs. If future AI augmentation is added to the "Approve Invoice" task, costs would depend on the model and token usage for that specific task.
