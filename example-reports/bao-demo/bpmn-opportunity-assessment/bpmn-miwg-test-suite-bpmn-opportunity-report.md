# BPMN Agentic Opportunity Assessment: BPMN MIWG Test Suite

**Repository**: `agentic-readiness-assessment/example-reports/bao-demo/repos/bpmn-miwg-test-suite`
**BPMN Files**: 840 files across 36 vendor directories (831 successfully analyzed, 9 failed)
**Date**: 2026-04-28
**Context**: Demonstrating BPMN agentic opportunity analysis across official open source process repositories covering invoice processing, order management, and BPMN interchange test cases.
**Daily Volume**: 200
**Priority**: P1
**Tags**: --

---

## Summary

The BPMN MIWG Test Suite portfolio contains **831 processes** with **3,555 tasks** across 24 BPMN 2.0 test case patterns (A.1.0 through C.9.2) and 36 vendor tool implementations. Of these tasks:

- **59** are agent opportunities (all classified as **Agent — data first** due to limited data readiness signals in the BPMN models)
- **3,340** are automatable with deterministic logic (**Automate**)
- **156** require human involvement (**Human Required**)

Agent tasks fall into two functional categories:
1. **"Review terms of contract"** (23 instances across C.4.0 test cases) — contract review in employee onboarding
2. **"Review and document result"** (36 instances across C.1.0 test cases) — documentation of invoice processing results

Estimated monthly Amazon Bedrock cost for agent tasks: **$477.90** at 200 invocations/day using Claude Haiku 3.5.

---

## Opportunity Classification

### Portfolio-Level Summary by Test Case

| Test Case | Description | Processes | Tasks | Agent | Automate | Human | Primary Opportunity |
|-----------|-------------|-----------|-------|-------|----------|-------|---------------------|
| A.1.0 | Basic sequential flow | 64 | 192 | 0 | 192 | 0 | Automate |
| A.1.1 | Sequential with conditions | 5 | 15 | 0 | 15 | 0 | Automate |
| A.1.2 | Sequential with typed tasks | 5 | 15 | 0 | 15 | 0 | Automate |
| A.2.0 | Exclusive gateway | 65 | 260 | 0 | 260 | 0 | Automate |
| A.2.1 | Inclusive gateway | 36 | 144 | 0 | 144 | 0 | Automate |
| A.3.0 | Collapsed sub-process | 60 | 293 | 0 | 293 | 0 | Automate |
| A.4.0 | Expanded sub-process | 56 | 126 | 0 | 126 | 0 | Automate |
| A.4.1 | Expanded sub-process (alt) | 49 | 100 | 0 | 100 | 0 | Automate |
| B.1.0 | Collaboration diagram | 54 | 129 | 0 | 129 | 0 | Automate |
| B.2.0 | Complex collaboration | 51 | 340 | 0 | 340 | 0 | Automate |
| **C.1.0** | **Invoice — Team-Assistant** | **46** | **178** | **36** | **128** | **14** | **Agent + Human** |
| C.1.1 | Invoice — Full process | 43 | 215 | 0 | 130 | 85 | Automate + Human |
| C.2.0 | E-commerce ordering | 44 | 59 | 0 | 59 | 0 | Automate |
| C.3.0 | Customer service repair | 45 | 217 | 0 | 217 | 0 | Automate |
| **C.4.0** | **Employee onboarding** | **38** | **306** | **23** | **283** | **0** | **Agent** |
| C.5.0 | Customer onboarding | 31 | 370 | 0 | 370 | 0 | Automate |
| C.6.0 | Travel booking | 24 | 73 | 0 | 73 | 0 | Automate |
| C.7.0 | Advertisement approval | 21 | 120 | 0 | 101 | 19 | Automate + Human |
| C.8.0 | Vacation approval | 20 | 100 | 0 | 80 | 20 | Automate + Human |
| C.8.1 | Vacation approval (alt) | 21 | 91 | 0 | 73 | 18 | Automate + Human |
| C.9.0 | Credit application | 17 | 129 | 0 | 129 | 0 | Automate |
| C.9.1 | Credit — call activity | 17 | 16 | 0 | 16 | 0 | Automate |
| C.9.2 | Credit — decision | 17 | 64 | 0 | 64 | 0 | Automate |
| Other | Miscellaneous | 2 | 3 | 0 | 3 | 0 | Automate |
| **TOTAL** | | **831** | **3,555** | **59** | **3,340** | **156** | |

### All 59 Agent Tasks — Detailed Classification

| # | Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K | Vendor |
|---|------|------|-------------|------------|------|----------|----------|---------|--------|
| 1 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | ADONIS 17.0 |
| 2 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | ADONIS 17.0 |
| 3 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | ARIS 10.2025.07 |
| 4 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | ARIS 10.2025.07 |
| 5 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | ARIS 10.2025.07 |
| 6 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | ARIS 10.2025.07 |
| 7 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | BIC Cloud Design 6.2.0 |
| 8 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | BPMN-Modeler for Confluence |
| 9 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | BPMN-Modeler for Confluence |
| 10 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | BPMN-Modeler for Confluence |
| 11 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | BPMN-Modeler for Confluence |
| 12 | Review and document result | agent | serviceTask | 0.50 | 0.30 | Data first | Prepared | $2.70 | Bonita BPM 7.2.3 |
| 13 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Camunda Eclipse Plugin 3.0.0 |
| 14 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Camunda Eclipse Plugin 3.0.0 |
| 15 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Cardanit 4.9.1 |
| 16 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Cardanit 4.9.1 |
| 17 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Cardanit 4.9.1 |
| 18 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Cardanit 4.9.1 |
| 19 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Enterprise Explorer 1.0.0 |
| 20 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Enterprise Explorer 1.0.0 |
| 21 | Review terms of Contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Enterprise Explorer 1.0.0 |
| 22 | Review terms of Contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Enterprise Explorer 1.0.0 |
| 23 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | MID Innovator 16.1.1 |
| 24 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | MID Innovator 16.1.1 |
| 25 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | MID Innovator 16.1.1 |
| 26 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | MID Innovator 16.1.1 |
| 27 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | MID bpanda 2019.05 |
| 28 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | MID bpanda 2019.05 |
| 29 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | ModelFoundry 1.1.1 |
| 30 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Modelio 3.5 |
| 31 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Modelio 3.5 |
| 32 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | OMNITRACKER BPMN 12.3 |
| 33 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Open-BPMN 1.2.8 |
| 34 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Open-BPMN 1.2.8 |
| 35 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Open-BPMN 1.2.8 |
| 36 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Open-BPMN 1.2.8 |
| 37 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Reference |
| 38 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Reference |
| 39 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | SAP Signavio 19.9.0 |
| 40 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | SAP Signavio 19.9.0 |
| 41 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | SAP Signavio 19.9.0 |
| 42 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | SAP Signavio 19.9.0 |
| 43 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Trisotech Visio Add-in 5.0.1 |
| 44 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Trisotech Visio Add-in 5.0.1 |
| 45 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Trisotech Workflow 12.13.0 |
| 46 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Trisotech Workflow 12.13.0 |
| 47 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | Trisotech Workflow 12.13.0 |
| 48 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | W4 BPMN+ V.10.4 |
| 49 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | W4 BPMN+ V.10.4 |
| 50 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | W4 BPMN+ V.10.4 |
| 51 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | W4 BPMN+ V.9.4 |
| 52 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | W4 BPMN+ V.9.4 |
| 53 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | Yaoqiang BPMN 4.0 |
| 54 | Review and Document Result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | bpmn.io (Camunda) 18.6.1 |
| 55 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | bpmn.io (Camunda) 18.6.1 |
| 56 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | bpmn.io (Camunda) 18.6.1 |
| 57 | Review terms of contract | agent | userTask | 0.70 | 0.28 | Data first | Prepared | $2.70 | bpmn.io (Camunda) 18.6.1 |
| 58 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | ibo Prometheus 3.9.0 |
| 59 | Review and document result | agent | task | 0.50 | 0.30 | Data first | Prepared | $2.70 | itp-commerce Visio 6 |

## Agent Opportunities (ranked by composite score)

The 59 agent tasks map to **two distinct functional patterns** that recur across vendor implementations of BPMN MIWG test cases C.1.0 (Invoice Processing — Team-Assistant) and C.4.0 (Employee Onboarding). Below, opportunities are presented by unique task type rather than per-vendor instance, since the same logical task appears identically across 24+ vendor exports.

### 1. Review Terms of Contract (23 instances — C.4.0 Employee Onboarding)

- **Category**: Agent (data first)
- **Autonomy**: **Prepared** — Agent synthesizes contract terms and recommends acceptance/rejection. Human reviews and approves.
- **Scores**: AI Benefit: **0.70** | Complexity: 0.30 | Risk: **0.28** | Effort: 0.50 | Composite: **0.166**
- **Data Readiness**: **Unknown** — Task name suggests unstructured document review ("terms of contract"). No `dataStoreReference` or service endpoint found in the BPMN models. Contract documents are likely stored in a DMS or file share not referenced in the process model.
- **Cost**: ~$2.70/1K invocations (Claude Haiku 3.5, ~1,300 tokens/invocation)
- **Structural Position**: Appears within the C.4.0 employee onboarding process (22 tasks/process). The process has high constraint density (2.23), gateway depth of 5, 16 ordering constraints, 2 exclusion constraints, and 12 coexistence constraints. The task sits within a parallel branch alongside "Perform training for position" and "Compile welcome package" — indicating it can be processed concurrently with other onboarding steps.
- **Integration Approach**: Replace the `userTask` with a Bedrock agent invocation via the BPM engine's service task connector. The agent receives the contract document (PDF/DOCX), extracts key terms (compensation, non-compete, IP assignment), and returns a structured summary with a recommendation. Route to human reviewer when confidence < 80%.
- **Prerequisites**:
  1. Contract documents must be accessible via API (S3, DMS REST endpoint, or similar)
  2. Contract term extraction prompt engineering and testing
  3. Human review escalation workflow for edge cases
  4. Document OCR pipeline if contracts are scanned images

**Vendor distribution**: ADONIS (2), ARIS (2), BIC Cloud Design (1), BPMN-Modeler for Confluence (2), Cardanit (2), Enterprise Explorer (2), MID Innovator (2), Open-BPMN (2), Reference (1), SAP Signavio (2), Trisotech Workflow (2), W4 BPMN+ V.10.4 (1), bpmn.io/Camunda (2)

---

### 2. Review and Document Result (36 instances — C.1.0 Invoice Processing)

- **Category**: Agent (data first)
- **Autonomy**: **Prepared** — Agent reviews invoice processing results and drafts documentation. Human reviews the documentation before finalizing.
- **Scores**: AI Benefit: **0.50** | Complexity: 0.30 | Risk: **0.30** | Effort: 0.30 | Composite: **0.110**
- **Data Readiness**: **Partial** — Task name suggests structured data review ("result"), likely referencing invoice processing outcomes. However, no explicit `dataStoreReference` or service endpoint is declared in the BPMN model. The preceding tasks ("Scan Invoice", "Assign approver") suggest structured data flows within the process, but the documentation target system is unknown.
- **Cost**: ~$2.70/1K invocations (Claude Haiku 3.5, ~1,300 tokens/invocation)
- **Structural Position**: Appears in the C.1.0 Team-Assistant process, which is a simpler collaboration (constraint density 0.70, gateway depth 0, 1 ordering constraint, 1 coexistence constraint). This is a terminal task in the Team-Assistant lane, following the main invoice approval flow. Linear chain structure with minimal branching.
- **Integration Approach**: Replace the abstract `task` element with a Bedrock agent invocation. The agent receives the invoice processing outcome (approved/rejected, amount, approver, date), generates a structured documentation entry, and stores it. This is a summarization and documentation task well-suited for LLM augmentation.
- **Prerequisites**:
  1. Invoice processing results must be available as structured data (JSON/XML process variables)
  2. Documentation template or target system API (database, document management)
  3. Prompt engineering for consistent documentation format
  4. Validation rules for documentation completeness

**Vendor distribution**: ARIS (2), BPMN-Modeler for Confluence (2), Bonita BPM (1), Camunda Eclipse (2), Cardanit (2), Enterprise Explorer (2), MID Innovator (2), MID bpanda (2), ModelFoundry (1), Modelio (2), OMNITRACKER (1), Open-BPMN (2), Reference (1), SAP Signavio (2), Trisotech Visio (2), Trisotech Workflow (1), W4 BPMN+ V.10.4 (2), W4 BPMN+ V.9.4 (2), Yaoqiang (1), bpmn.io/Camunda (2), ibo Prometheus (1), itp-commerce (1)

---

## Automatable Tasks

The 3,340 service tasks represent deterministic, rule-based operations that can be automated with Step Functions, rule engines, or direct API integrations. Below is a summary grouped by test case pattern.

| Test Case | Representative Tasks | Count | Recommendation |
|-----------|---------------------|-------|----------------|
| A.1.0 | Task 1, Task 2, Task 3 | 192 | Step Functions — sequential state machine |
| A.1.1 | Task 1, Task 2, Task 3 | 15 | Step Functions — conditional branching |
| A.1.2 | Task 1, Task 2, Task 3 | 15 | Step Functions — typed task routing |
| A.2.0 | Task 1–4 | 260 | Step Functions — exclusive choice gateway |
| A.2.1 | Task 1–4 | 144 | Step Functions — inclusive (parallel) gateway |
| A.3.0 | Task 1–4, Collapsed Sub-Process | 293 | Step Functions with nested workflows |
| A.4.0 | Task 1–3, Expanded Sub-Process | 126 | Step Functions with Map/Parallel states |
| A.4.1 | Task 1–3, Expanded Sub-Process | 100 | Step Functions with Map/Parallel states |
| B.1.0 | Abstract Task 1–4, Service Task 3, User Task 2 | 129 | EventBridge + Step Functions collaboration |
| B.2.0 | User Task 8–13, Service Task 14 | 340 | Complex orchestration — Step Functions + EventBridge |
| C.1.0 | Assign approver, Scan Invoice, Archive original | 128 | Invoice processing pipeline — Step Functions + Lambda |
| C.1.1 | Archive Invoice, Rechnung klären, Prepare Bank Transfer | 130 | Invoice processing pipeline — Step Functions + Lambda |
| C.2.0 | Take Payment, Load Truck, Deliver Items | 59 | Order fulfillment pipeline — Step Functions |
| C.3.0 | Replace fridge, Analyse request, Perform repair | 217 | Customer service routing — Step Functions + rule engine |
| C.4.0 | Compile welcome package, Perform training, Register insurance | 283 | Employee onboarding pipeline — Step Functions (parallel) |
| C.5.0 | Interview customer, Create customer, Risk assessment | 370 | KYC/onboarding pipeline — Step Functions + Lambda |
| C.6.0 | Charge Credit Card, Update Customer Record, Make Booking | 73 | Travel booking pipeline — API orchestration |
| C.7.0 | Complete advertisement, Publish on platforms | 101 | Content publishing pipeline — Step Functions |
| C.8.0 | Update Remaining Vacation, Vacation Approval, Fetch Info | 80 | Leave management — Step Functions + rule engine |
| C.8.1 | Update Remaining Vacation, Vacation Approval, Fetch Info | 73 | Leave management — Step Functions + rule engine |
| C.9.0 | Check application, Get credit score, Deliver confirmation | 129 | Credit decision pipeline — Step Functions + ML scoring |
| C.9.1 | Call customer | 16 | Call activity — Lambda invocation |
| C.9.2 | Decide on application | 64 | Decision task — business rules engine |
| Other | Miscellaneous | 3 | Case-by-case evaluation |
| **TOTAL** | | **3,340** | |

---

## Human-Required Tasks

The 156 human-required tasks are concentrated in four functional categories, all representing approval gates or assignment decisions with elevated risk scores (0.73–0.80). These tasks involve financial or personnel decisions where human judgment is mandated.

| Task | Test Case | Instances | BPMN Element | Risk Score | Reason |
|------|-----------|-----------|-------------|------------|--------|
| Approve Invoice | C.1.0, C.1.1 | 47 | userTask | 0.80 | Financial approval gate — elevated risk. Human judgment required for invoice validation and payment authorization. |
| Assign Approver | C.1.0, C.1.1 | 44 | userTask | 0.80 | Assignment decision — elevated risk. Routing decision requires organizational knowledge and authority matrix awareness. |
| Manually Approve Vacation | C.8.0, C.8.1 | 38 | userTask | 0.73 | Personnel approval gate — elevated risk. Manager discretion required for leave approval considering team workload. |
| Approve Advertisement | C.7.0 | 19 | userTask | 0.80 | Content approval gate — elevated risk. Brand and compliance review requires human editorial judgment. |
| Assign Approver (variant) | C.1.0, C.1.1 | 4 | userTask | 0.80 | Same as "Assign Approver" — whitespace variant in task name. |
| Approve Invoice (variant) | C.1.1 | 2 | userTask | 0.80 | Same as "Approve Invoice" — casing variant in task name. |
| Assign approver (variant) | C.1.1 | 2 | userTask | 0.80 | Same as "Assign Approver" — casing variant in task name. |
| **TOTAL** | | **156** | | | |

> **Note**: All human-required tasks have high AI benefit scores (0.70), indicating that AI could meaningfully assist these activities. However, the elevated risk scores (≥0.73) and the approval/assignment nature of these tasks make them unsuitable for full autonomous agent handling. These are candidates for **AI-assisted human decision-making** — the agent could prepare supporting information (invoice summary, approval history, team availability) while the human retains the final decision authority.

---

## Data Readiness Gaps

Data readiness for agent tasks was assessed using BPMN model signals (data associations, service task implementations, message flows) and task name inference. No ARA report was available for system-level validation.

| Agent Task | Data Source | Current State | Readiness | Remediation |
|-----------|-----------|---------------|-----------|-------------|
| Review terms of contract (C.4.0) | Contract documents | Unknown — No `dataStoreReference` or service endpoint in BPMN model. Contract documents likely in DMS/file share not referenced in process. | **Unknown** | 1. Identify contract document repository (DMS, SharePoint, S3). 2. Build API endpoint for document retrieval. 3. Implement document parsing pipeline (PDF/DOCX → structured text). 4. Run ARA on the contract management system. |
| Review and document result (C.1.0) | Invoice processing results | Partial — Task name implies structured data ("result"), but no explicit data store reference. Preceding tasks (Scan Invoice, Assign Approver) suggest structured data exists in-process. | **Partial** | 1. Expose invoice processing variables as structured API (process engine REST API). 2. Define documentation output schema. 3. Validate that all required fields are available in process context. |

> **Data readiness could not be fully assessed from the BPMN model alone.** The BPMN MIWG Test Suite contains standardized test cases that intentionally omit implementation-specific details (database connections, API endpoints, data schemas). In a production deployment:
>
> - Run the **Agentic Readiness Assessment (ARA)** on the target systems (contract management, invoice processing, document management) to obtain system-level data readiness signals.
> - Check for DATA BLOCKERs (missing APIs, scattered data, incompatible formats) that would require remediation before agent deployment.

---

## ARA Cross-Reference

*No ARA report available. Run the Agentic Readiness Assessment on the target systems for a complete readiness view.*

No `ara_report_path` was provided in the analysis configuration. Without ARA findings:

- Data readiness assessments rely solely on BPMN model analysis (data associations, service task implementations, message flows, and task name inference)
- No system-level AUTH, DATA, or INTEGRATION blockers have been evaluated
- No opportunity category overrides have been applied (no "Agent build now" → "Agent data first" downgrades)
- The implementation roadmap assumes no system-level blockers exist

**Recommended next step**: Run the Agentic Readiness Assessment on the following target systems:

| System | Reason | Priority |
|--------|--------|----------|
| Contract Management System | Data source for "Review terms of contract" agent tasks | High |
| Invoice Processing System | Data source for "Review and document result" agent tasks | High |
| Document Management System | Storage target for documentation output | Medium |
| BPM Engine REST API | Integration point for all agent task invocations | High |

---

## Implementation Roadmap

### Wave 1: Build Now

> **No tasks qualify for immediate build.** All 59 agent tasks are classified as "Agent (data first)" because data readiness could not be confirmed from the BPMN model alone. The BPMN MIWG Test Suite uses standardized test cases that omit implementation-specific details.
>
> **To promote tasks to Wave 1**: Run ARA on the target systems. If contract documents and invoice processing results are accessible via API, the corresponding agent tasks can be reclassified as "Agent (build now)."

**Preparatory actions for Wave 1 promotion:**

1. **Contract Management System**: Verify API access to contract documents. If available, 23 "Review terms of contract" tasks move to Wave 1.
2. **Invoice Processing System**: Verify structured output of invoice processing results via BPM engine API. If available, 36 "Review and document result" tasks move to Wave 1.
3. **Pilot scope**: Select one vendor implementation (e.g., Reference or bpmn.io/Camunda) for initial agent prototype.

### Wave 2: After Data Work

| Task | Instances | Data Gap | Required Work | Estimated Effort |
|------|-----------|----------|---------------|-----------------|
| Review terms of contract | 23 | Contract documents inaccessible via API | Build document retrieval API, implement PDF/DOCX parsing pipeline, deploy to S3/DMS | 2–4 weeks |
| Review and document result | 36 | Invoice results not exposed as structured API | Expose BPM engine process variables via REST API, define documentation output schema | 1–2 weeks |

**Total Wave 2 tasks**: 59 agent tasks across 24 vendor implementations

### Wave 3: After System Remediation

> **No tasks in Wave 3.** No ARA blockers have been identified (no ARA report was provided). If ARA identifies AUTH, DATA, or INTEGRATION blockers on target systems, affected agent tasks would be deferred to this wave.

### Roadmap Timeline (Estimated)

```
Week 1-2:   Run ARA on target systems (contract mgmt, invoice processing, BPM engine)
Week 2-3:   Remediate data gaps identified in Wave 2
Week 3-4:   Pilot agent for "Review and document result" (simpler, higher volume)
Week 4-6:   Pilot agent for "Review terms of contract" (more complex, document-heavy)
Week 6-8:   Production rollout across vendor implementations
Week 8+:    Monitor, tune prompts, expand to AI-assisted human tasks
```

---

## Process Structure Summary

| Metric | Value |
|--------|-------|
| **Total BPMN files found** | 840 |
| **Successfully analyzed** | 831 |
| **Failed (malformed)** | 9 |
| **Total elements** | 7,256 |
| **Total tasks** | 3,555 |
| **Total flows** | 7,915 |
| **Start events** | 842 |
| **End events** | 1,506 |
| **Vendors represented** | 36 |
| **Test case patterns** | 24 (A.1.0 – C.9.2) |

### Element Type Distribution

| Element Type | Count | % of Tasks |
|-------------|-------|------------|
| task (abstract) | 1,431 | 40.3% |
| userTask | 1,305 | 36.7% |
| serviceTask | 437 | 12.3% |
| subProcess | 308 | 8.7% |
| businessRuleTask | 74 | 2.1% |

### Gateway Depth Distribution

| Max Depth | Process Count | Description |
|-----------|--------------|-------------|
| 0 | 470 (56.6%) | Linear/simple processes (A.1.x series) |
| 1 | 41 (4.9%) | Single decision point |
| 2 | 249 (30.0%) | Standard branching (A.2.x, C.x series) |
| 3 | 26 (3.1%) | Nested decisions |
| 5 | 23 (2.8%) | Complex processes (C.4.0, C.5.0) |
| 8 | 22 (2.6%) | Deeply nested (C.9.x credit decision) |

### Constraint Profile (Aggregate)

| Constraint Type | Count |
|----------------|-------|
| Ordering | 3,876 |
| Coexistence | 2,537 |
| Exclusion | 1,666 |
| Deeply nested processes | 45 |

### Key Structural Insights

1. **The portfolio is heavily weighted toward deterministic processes.** 94% of tasks (3,340) are service-type with low AI benefit, reflecting the test suite's focus on basic BPMN interchange patterns (sequential flows, gateways, sub-processes).

2. **Agent opportunities cluster in two specific test cases.** C.1.0 (Invoice Team-Assistant) and C.4.0 (Employee Onboarding) are the only patterns that produce agent-classified tasks. C.4.0 is structurally more complex (gateway depth 5, high constraint density) while C.1.0 is simpler (linear chain in the Team-Assistant lane).

3. **Human-required tasks correlate with approval gates.** All 156 human tasks are `userTask` elements with high risk scores (0.73–0.80), concentrated in processes that model approval workflows (invoice approval, vacation approval, advertisement approval).

4. **Process topology is consistent across vendors.** The same test case produces nearly identical task counts and classifications across all 36 vendor implementations, confirming that the BPMN MIWG interchange format preserves process semantics faithfully.

---

## Cost Summary

| Metric | Value |
|--------|-------|
| Agent tasks | 59 |
| Unique agent task types | 2 |
| Tokens per invocation (per agent) | 1,300 |
| Total tokens/invocation (all agents) | 76,700 |
| Daily volume (configured) | 200 invocations/day |
| Estimated monthly cost (200/day) | **$477.90** |
| Cost per 1K invocations (per agent) | $2.70 |
| Recommended model | Claude Haiku 3.5 |

### Cost Breakdown by Agent Type

| Agent Task | Instances | Tokens/Invocation | Cost/1K | Monthly Cost (200/day) |
|-----------|-----------|-------------------|---------|----------------------|
| Review terms of contract | 23 | 1,300 | $2.70 | $186.30 |
| Review and document result | 36 | 1,300 | $2.70 | $291.60 |
| **Total** | **59** | **76,700** | | **$477.90** |

> **Note**: Cost projections assume all 59 agent task instances are invoked at the configured daily volume of 200 invocations/day. In practice, the BPMN MIWG Test Suite represents the same logical process modeled by different vendor tools. A production deployment would target a single vendor implementation per process, reducing the effective agent count to 2 (one per unique task type) with a monthly cost of approximately **$16.20** (2 agents × 200/day × 30 days × $2.70/1K ÷ 1000 × 1300 tokens).

---

*Report generated by BPMN Agentic Opportunity Assessment • 2026-04-28*
