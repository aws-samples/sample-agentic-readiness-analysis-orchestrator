# BPMN Agentic Opportunity Assessment: Process Data Example

**Repository**: camunda8-order-process
**BPMN File**: BPMN_DMN/process-five.bpmn
**Date**: 2025-07-16
**Context**: Camunda 8 order processing with Zeebe job workers, BPMN error events, timer escalation patterns, and event subprocesses.
**Daily Volume**: 200
**Priority**: P0
**Tags**: camunda8, zeebe, order-processing, bpmn-error-events, timer-escalation

---

## Summary

Process Data Example contains 8 tasks. 0 are agent opportunities (0 build-now, 0 data-first), 7 are automatable with deterministic logic, and 1 requires human involvement. Estimated monthly Bedrock cost for agent tasks: $0.00 at 200 invocations/day.

All tasks in this process are suited for deterministic automation (service endpoints, DMN rules, Zeebe job workers) rather than AI agent deployment. The process leverages Camunda 8 / Zeebe patterns including parallel execution, timer-based escalation, error boundary events, and event subprocesses — all of which map well to orchestration engines and do not require LLM-based reasoning.

> **Future Agent Candidates**: "Validate Data" and "Manual Check" have the highest AI benefit scores (0.7 each) and are the strongest candidates for agentic AI if the process evolves to require more judgment-based decisions.

## Opportunity Classification

| Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------|----------|----------|---------|
| Validate Data | service | userTask | 0.70 | 0.35 | Automate | -- | -- |
| Manual Check | service | userTask | 0.70 | 0.38 | Automate | -- | -- |
| Process Data | service | serviceTask | 0.40 | 0.35 | Automate | -- | -- |
| Decide on Assignee | service | businessRuleTask | 0.50 | 0.60 | Automate | -- | -- |
| Update External Audit | service | sendTask | --¹ | --¹ | Automate | -- | -- |
| Send SLA Warning | service | sendTask | --¹ | --¹ | Automate | -- | -- |
| Event Subprocess | service | subProcess | 0.35 | 0.20 | Automate | -- | -- |
| Enter Cancellation Details | human | userTask | --¹ | --¹ | Human Required | -- | -- |

¹ Scores not pre-computed in the analysis report. Task classified from BPMN element type and structural context.

## Agent Opportunities (ranked by composite score)

**No tasks are currently classified as agent opportunities.**

All 8 tasks in the Process Data Example process are either automatable with deterministic logic (7 tasks) or require mandatory human involvement (1 task). None require LLM-based reasoning that would justify AI agent deployment.

### Future Agent Candidates

While no tasks currently warrant agent classification, the following tasks have elevated AI benefit scores and should be re-evaluated if process requirements change:

#### 1. Validate Data
- **Current Category**: Automate (service)
- **AI Benefit Score**: 0.70 (highest in process)
- **Composite Score**: 0.16 (highest in process)
- **Why not agent now**: The analysis report classifies this as "service" — the validation logic is deterministic and rule-based. The current BPMN user task with `zeebe:assignmentDefinition` suggests human review, but the validation criteria are structured.
- **When to reconsider**: If validation requirements expand to include unstructured document analysis, natural language interpretation, or multi-source data correlation, this task would benefit from an AI agent.
- **Potential Autonomy Level**: Prepared (risk=0.35 falls in 0.2–0.4 range) — Agent would synthesize and recommend; human reviews and approves.

#### 2. Manual Check
- **Current Category**: Automate (service)
- **AI Benefit Score**: 0.70
- **Composite Score**: 0.136
- **Why not agent now**: Triggered by the 5-minute timer timeout as an escalation path. The "manual check" logic is currently structured enough for deterministic automation.
- **When to reconsider**: If the check involves interpreting ambiguous data patterns, assessing edge cases, or making judgment calls beyond predefined rules.
- **Potential Autonomy Level**: Prepared (risk=0.38 falls in 0.2–0.4 range) — Agent would synthesize and recommend; human reviews and approves.

## Automatable Tasks

| Task | BPMN Element | Data Readiness | Recommendation |
|------|-------------|----------------|----------------|
| Process Data | serviceTask | Ready | Zeebe job worker (DoLongWork) already deployed. Maintain current REST connector pattern. Consider Step Functions for long-running orchestration if migrating off Camunda. |
| Decide on Assignee | businessRuleTask | Ready | DMN decision table (Decide_on_Assignee) with structured inputs (complexity: High/Medium/Low) and outputs (processOwner, needsUser). Keep as DMN evaluation or migrate to AWS rule engine. |
| Update External Audit | sendTask | Ready | Zeebe job worker (DoWork) with error boundary event. Deterministic send with built-in error handling. Maintain REST connector pattern. ⚠️ **Compliance flag**: "audit" keyword — ensure audit trail requirements are preserved in any migration. |
| Send SLA Warning | sendTask | Ready | Zeebe job worker (DoWork) triggered by non-interrupting 1-minute repeating timer (R/PT1M). Deterministic notification. Consider Amazon EventBridge for timer-based triggers if migrating. |
| Validate Data | userTask | Unknown | Currently a human task assigned to `processOwner`. Automate with REST connector wrapping validation rules. Data source integration needed first (see Data Readiness Gaps). |
| Manual Check | userTask | Unknown | Escalation path from 5-minute timer on Process Data. Automate with REST connector wrapping check logic. Define structured input/output schema first (see Data Readiness Gaps). |
| Event Subprocess | subProcess | Unknown | Event subprocess triggered by CancelMessage. Contains cancellation workflow. The subprocess container itself is deterministic orchestration — maintain as-is in BPM engine. |

## Human-Required Tasks

| Task | BPMN Element | Risk Score | Reason |
|------|-------------|------------|--------|
| Enter Cancellation Details | userTask | --¹ | Cancellation workflow requires human input for details. Located inside event subprocess triggered by CancelMessage. Human must provide cancellation reason and details — cannot be inferred by automation or AI. Assigned to `processOwner` via `zeebe:assignmentDefinition`. |

¹ Score not pre-computed; task identified from BPMN XML analysis.

## Data Readiness Gaps

| Task | Data Source | Current State | Remediation |
|------|-----------|---------------|-------------|
| Validate Data | Unknown — no dataStore or dataObject references in BPMN | No system references; user task relies on human knowledge | Identify the data sources used for validation. Expose them via REST API. Define structured input/output schema for the validation logic. |
| Manual Check | Unknown — triggered by timer escalation, no system references | User task with no documented data dependencies | Document what data the manual checker reviews. Create API endpoints for the data sources. Define decision criteria as structured rules. |
| Event Subprocess (Activity_0ijh0e2) | CancelMessage via Zeebe message correlation | Message-triggered subprocess; internal data flow not documented | Document the CancelMessage payload schema. Ensure message correlation key ("CANCEL") and payload are well-defined for integration. |

> **Note**: Data readiness could not be fully assessed from the BPMN model alone for these tasks. Run ARA on the target systems for a complete classification.

## ARA Cross-Reference

*No ARA report available. Run the Agentic Readiness Assessment on the target systems for a complete readiness view.*

No `ara_report_path` was provided in the assessment configuration. Without ARA findings, data readiness and system readiness assessments are based solely on BPMN metadata analysis. The following limitations apply:

- DATA readiness for user tasks (Validate Data, Manual Check) could not be verified against actual system APIs
- AUTH and connectivity blockers for external audit systems are unknown
- Integration readiness for the DoWork and DoLongWork Zeebe job worker endpoints has not been independently verified

**Recommendation**: Run the Agentic Readiness Assessment targeting:
1. The Zeebe cluster and job worker endpoints (DoWork, DoLongWork)
2. Any external audit system connected to "Update External Audit"
3. Data sources used by "Validate Data" and "Manual Check" tasks

## Implementation Roadmap

### Wave 1: Build Now — Service Automation (Ready)

These tasks have confirmed service endpoints and are ready for deterministic automation:

| Priority | Task | Action | Estimated Effort |
|----------|------|--------|-----------------|
| 1 | Process Data | Maintain Zeebe job worker (DoLongWork). Optimize long-running task handling with retry/timeout patterns. | Low — already deployed |
| 2 | Decide on Assignee | Maintain DMN decision table. Consider migrating to AWS-native rule engine if platform migration is planned. | Low — already deployed |
| 3 | Update External Audit | Maintain Zeebe job worker (DoWork) with error boundary event. Ensure audit compliance requirements are documented. | Low — already deployed |
| 4 | Send SLA Warning | Maintain Zeebe job worker (DoWork) with timer trigger. Consider EventBridge for timer-based scheduling if migrating. | Low — already deployed |

> **Note**: All Wave 1 tasks are already implemented as Zeebe job workers. The "build now" action is to validate, optimize, and document the existing automation rather than build new automation.

### Wave 2: After Data Work — Data Platform Prerequisites

These tasks have unknown data readiness and need data platform work before any future automation or agent consideration:

| Priority | Task | Prerequisites | Estimated Effort |
|----------|------|--------------|-----------------|
| 1 | Validate Data | Identify data sources → expose via API → define validation schema | Medium |
| 2 | Manual Check | Document check criteria → create data API → define decision rules | Medium |
| 3 | Event Subprocess | Document CancelMessage payload → validate message correlation | Low |

### Wave 3: After System Remediation

No ARA blockers have been identified (no ARA report was provided). This wave is currently empty.

If an ARA assessment reveals blockers on target systems, affected tasks should be moved to this wave with specific remediation steps.

## Process Structure Summary

- **Total elements**: 15
- **Tasks**: 8 (2 userTask, 1 serviceTask, 1 businessRuleTask, 2 sendTask, 1 subProcess, 1 userTask in subprocess)
- **Gateways**: 4 (2 exclusive / XOR, 2 parallel / AND)
- **Events**: 8 (1 start, 4 end including 1 terminate, 2 timer boundary, 1 error boundary, 1 message start in subprocess)
- **Exclusive branches (XOR)**: 2 — "Needs User Involvement" (Yes/No) and "Action" (Cancel/Retry)
- **Parallel branches (AND)**: 1 — splits into "Needs User Involvement" path and "Update External Audit" path after "Decide on Assignee"
- **Linear chains**: Start → Decide on Assignee → [parallel split] → [parallel join] → Process Data → End
- **Constraint density**: 1.27 (19 constraints / 15 elements)
- **Max gateway depth**: 4 (deeply nested)
- **Key structural insight**: This is a deeply nested process with sophisticated orchestration patterns. The parallel split after the DMN decision allows concurrent user validation and external audit. The timer escalation on "Process Data" (1-min SLA warning + 5-min manual check fallback) implements a progressive escalation strategy. The event subprocess provides graceful cancellation via message correlation. The error boundary on "Update External Audit" triggers a terminate end event, indicating that audit failures are considered process-critical. These patterns are well-served by the Camunda 8 / Zeebe engine and do not require AI agent capabilities.

## Cost Summary

| Metric | Value |
|--------|-------|
| Agent tasks | 0 |
| Total tokens/invocation (all agents) | 0 |
| Estimated monthly cost (200/day) | $0.00 |
| Recommended models | N/A (no agent tasks) |

> **Cost note**: All tasks in this process are classified as deterministic service automations. There are no AI agent tasks requiring LLM inference, so the Bedrock cost projection is $0. If "Validate Data" or "Manual Check" are reclassified as agent tasks in the future, estimated costs would be approximately $2.40–$3.60 per 1,000 invocations using Claude 3 Haiku (~1,500 tokens/invocation), projecting to ~$14–$22/month at 200 invocations/day.

---

*Report generated by BPMN Agentic Opportunity Assessment*
*Analysis report source: bpmn-analysis.json*
*BPMN source: BPMN_DMN/process-five.bpmn*
*DMN source: BPMN_DMN/decide-on-assignee.dmn*
