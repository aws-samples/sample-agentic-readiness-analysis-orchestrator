# BPMN Agentic Opportunity Assessment: Team-Assistant

**Repository**: bpmn-miwg-test-suite
**BPMN File**: Reference/C.1.0.bpmn
**Process ID**: sid-5FBB6CB3-8A7C-42B5-9024-15BB2684EC57
**Date**: 2026-04-27
**Priority**: P1
**Context**: OMG official BPMN 2.0 Model Interchange test cases with reference models exported from multiple vendor tools.
**Daily Volume**: 200

---

## Summary

Team-Assistant contains 4 tasks. 1 is an agent opportunity (0 build-now, 1 data-first), 3 are automatable with deterministic logic, and 0 require human involvement. Estimated monthly Bedrock cost for agent tasks: $16.20 at 200 invocations/day.

## Opportunity Classification

| Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------|----------|----------|---------|
| Review and document result | agent | task | 0.50 | 0.30 | Agent (data first) | Prepared | $2.70 |
| Assign approver | service | task | 0.50 | 0.50 | Automate | -- | -- |
| Scan Invoice | service | task | 0.30 | 0.30 | Automate | -- | -- |
| Archive original | service | task | 0.15 | 0.30 | Automate | -- | -- |

## Agent Opportunities (ranked by composite score)

### 1. Review and document result

- **Category**: Agent (data first)
- **Autonomy**: Prepared — Agent synthesizes and recommends. Human reviews and approves.
- **Scores**: AI Benefit: 0.50 | Complexity: 0.30 | Risk: 0.30 | Effort: 0.30 | Composite: 0.11
- **Data Readiness**: Unknown — Data readiness could not be assessed from the BPMN model. The task has an outbound message flow to `reviewInvoice` in the Process Engine pool, which indicates message-based integration (a partial readiness signal), but no `dataStoreReference`, service implementation details, or ARA report are available to confirm structured data availability. Run ARA on the target systems for a complete classification.
- **Cost**: ~$2.70/1K invocations (haiku-3.5, 1,300 tokens)
- **Structural Position**: This task sits in a linear chain after an event-based gateway branch. It is preceded by the "Invoice review needed" intermediate catch event and followed directly by an end event. Constraint density is 0.70 with succession, co-existence, chain succession, chain precedence, and alternate response constraints governing the process flow. Max gateway depth is 0 (no deeply nested branching).
- **Integration Approach**: REST connector: BPM engine calls agent endpoint via HTTP. Agent processes the request and returns structured JSON.
- **Prerequisites**:
  - Deploy Strands agent on AgentCore or as REST API
  - Confirm data readiness: assess whether invoice review data is accessible via structured API (run ARA on target systems)
  - Define input/output contract for the review-and-document agent

## Automatable Tasks

| Task | BPMN Element | Recommendation |
|------|-------------|----------------|
| Assign approver | task | Deterministic REST API / Step Functions — receives process variables as JSON, executes approver assignment logic, returns structured results. Has message flow integration with Process Engine pool (`assignApprover`). |
| Scan Invoice | task | Deterministic REST API / Step Functions — receives invoice data, performs scanning/OCR, returns structured results. Has message flow to Process Engine start event (`StartEvent_1`). |
| Archive original | task | Deterministic REST API / Step Functions — receives document reference, performs archival operation, returns confirmation. Simple storage operation with no external message flow dependencies. |

## Human-Required Tasks

No tasks require mandatory human involvement in the Team-Assistant process. All 4 tasks are classified as either agent or service opportunities.

## Data Readiness Gaps

| Task | Data Source | Current State | Remediation |
|------|-----------|---------------|-------------|
| Review and document result | Invoice review data via message flow to `reviewInvoice` | Unknown — no `dataStoreReference` in BPMN, no service task implementation details, no ARA report available | Run Agentic Readiness Assessment (ARA) on the Process Engine (Invoice Receipt) system to determine data availability, format, and API readiness. Confirm whether invoice review data is accessible as structured JSON via the existing message flow protocol. |

## ARA Cross-Reference

*No ARA report available. Run the Agentic Readiness Assessment on the target systems for a complete readiness view.*

No `ara_report_path` was provided in the assessment configuration. Without ARA findings, data readiness and system readiness cannot be fully validated. The agent task "Review and document result" is conservatively classified as "Agent (data first)" pending ARA confirmation.

| Agent Task | Target System | ARA Profile | Blockers | Status |
|---|---|---|---|---|
| Review and document result | Process Engine - Invoice Receipt | Not assessed | Unknown | Run ARA |

## Implementation Roadmap

### Wave 1: Build Now

**Deterministic Service Tasks** — These 3 tasks can be implemented immediately as REST API endpoints or Step Functions without LLM involvement:

1. **Scan Invoice** — Deploy as a deterministic scanning/OCR service. Lowest effort score (0.2) and low complexity (0.3). Connects to Process Engine via message flow.
2. **Assign approver** — Deploy as a deterministic assignment service. Has elevated risk (0.5) due to financial/approval decision nature; include guardrails and confidence thresholds with human fallback.
3. **Archive original** — Deploy as a deterministic archival service. Lowest AI benefit (0.15) confirms this is purely mechanical. No external message flow dependencies.

*No agent tasks qualify for Wave 1 because the single agent opportunity ("Review and document result") has unknown data readiness.*

### Wave 2: After Data Work

1. **Review and document result** — Agent deployment pending data readiness confirmation.
   - **Action required**: Run ARA on the Process Engine (Invoice Receipt) system
   - **Validate**: Invoice review data is available as structured JSON via message flow
   - **Then**: Deploy Strands agent on AgentCore or as REST API with Prepared autonomy level
   - **Estimated cost**: $16.20/month at 200 invocations/day

### Wave 3: After System Remediation

*No ARA blockers identified — this wave is empty. If ARA reveals system-level blockers (e.g., AUTH or DATA issues), affected tasks should be moved to this wave.*

## Process Structure Summary

- **Total elements**: 10
- **Tasks**: 4
- **Gateways**: 1 (event-based gateway, max depth: 0)
- **Events**: 5 (1 start event, 2 intermediate catch events, 2 end events)
- **Sequence flows**: 10
- **Exclusive branches (XOR)**: 0
- **Parallel branches (AND)**: 0
- **Event-based branches**: 1 (diverging, with timer and message catch paths)
- **Linear chains**: 3 (Start → Scan Invoice → Archive original → Approver wait; Assign approver → Gateway; Invoice review → Review and document result → End)
- **Constraint density**: 0.70 (7 constraints across 10 elements)
- **Constraint types**: init (1), end (1), succession (1), co-existence (1), chain succession (1), chain precedence (1), alternate response (1)
- **Key structural insight**: The Team-Assistant process follows a predominantly linear flow pattern with message-based collaboration to the Process Engine (Invoice Receipt) pool. After scanning and archiving the invoice, the process enters an event-based gateway that branches between a 7-day timer timeout (leading to one end event) and an invoice review request (leading to the agent task "Review and document result" and a second end event). The process has no deeply nested gateways (max depth = 0) and relies on inter-pool message flows for coordination rather than internal branching complexity.

## Cost Summary

| Metric | Value |
|--------|-------|
| Agent tasks | 1 |
| Total tokens/invocation (all agents) | 1,300 |
| Estimated monthly cost (200/day) | $16.20 |
| Recommended models | haiku-3.5 |

*Note: Service tasks (Assign approver, Scan Invoice, Archive original) incur infrastructure costs only — no LLM token costs. The $16.20 monthly estimate covers only the agent task "Review and document result" at 200 daily invocations × 30 days = 6,000 monthly invocations × $2.70/1K invocations.*
