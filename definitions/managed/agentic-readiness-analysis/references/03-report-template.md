# ARA Report Template

> **Purpose:** Loaded by the Agentic Readiness Analysis (ARA) TD when compiling findings into the markdown report artifact. Defines the metadata header, readiness-profile determination, summary counts, BLOCKER/RISK/INFO sections, detailed findings, evidence index, and table of contents. The JSON/HTML artifacts render subsets of this same data per the Output Contract.

---

## Report Template

After evaluating all 43 questions across Steps 2–9, compile the findings into the **four-artifact bundle** defined in the Four-Artifact Output Contract below: `{repo-name}-ara-report.md` (narrative), `{repo-name}-ara-report.json` (canonical JSON), `{repo-name}-ara-report.html` (self-contained HTML), and `{repo-name}-ara-report.metadata.json` (version sidecar). This section specifies the MD structure; the JSON and HTML render subsets of the same data per the contract.

Create the report file with exactly this structure. Every section is required. All 43 questions must appear in the detailed findings — N/A questions are listed using the N/A display format, not omitted.

### Report Metadata Header

```markdown
# Agentic Readiness Analysis Report
**Target**: <repository path>
**Date**: <date>
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: <resolved from `atx custom def get -n agentic-readiness-analysis` — the version ID of the published TD that produced this report, e.g., "3g1ef0edkgh173d9yafo0lio">
**Repository Type**: <resolved repo_type>
**Service Archetype**: <resolved service_archetype> (auto-detected | user-provided)
**Agent Scope**: <resolved agent_scope>
**Priority**: <priority if provided, otherwise omit this line>
**Tags**: <tags if provided, otherwise omit this line>
**Context**: <context if provided, otherwise omit this line>
```

If `service_archetype` was auto-detected, include:
```markdown
**Archetype Justification**: <1-2 sentence explanation>
```

If `repo_type` was defaulted due to an unrecognized value, include a warning line:
```markdown
**Warning**: Unrecognized repo_type '<original value>', defaulted to 'application'.
```

---

### Readiness Profile Determination

Determine the readiness profile using the BLOCKER and RISK-SAFETY counts from non-N/A, non-"Not Evaluated (extended)" questions only. N/A questions and Not Evaluated (extended) questions are excluded from all counts and have no effect on the profile. RISK-QUALITY count has no effect on profile assignment.

| Readiness Profile | BLOCKERs | RISK-SAFETY | RISK-QUALITY | Recommendation | Deployment Gate |
|-------------------|----------|-------------|--------------|----------------|-----------------|
| **Agent-Ready** | 0 | 0 | Any | Broad deployment | Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first. |
| **Pilot-Ready** | 0 | 1–2 | Any | Narrow pilot | Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK-SAFETY, (4) remediation timeline before expanding scope. |
| **Pilot-Ready (Safety Concerns)** | 0 | 3+ | Any | Supervised pilot, prioritize safety remediation | Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3. |
| **Remediation Required** | 1–2 | Any | Any | Remediate BLOCKERs first | Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. |
| **Not Agent-Integrable** | 3+ | Any | Any | Deferred or descoped | Exclude from agent toolset or plan major remediation before re-evaluation. |

**Rules:**
1. Count only non-N/A, non-"Not Evaluated (extended)" questions with severity BLOCKER → `blocker_count`.
2. Count only non-N/A, non-"Not Evaluated (extended)" questions with severity RISK-SAFETY → `risk_safety_count`.
3. RISK-QUALITY count is not used in profile determination.
4. If `blocker_count >= 3` → **Not Agent-Integrable**.
5. If `blocker_count` is 1 or 2 → **Remediation Required** (RISK-SAFETY count is irrelevant).
6. If `blocker_count == 0` and `risk_safety_count >= 3` → **Pilot-Ready (Safety Concerns)**.
7. If `blocker_count == 0` and `risk_safety_count` is 1 or 2 → **Pilot-Ready**.
8. If `blocker_count == 0` and `risk_safety_count == 0` → **Agent-Ready**.

Display the readiness profile in the report:

```markdown
---

## Readiness Profile: <profile name>

**BLOCKERs**: <blocker_count> | **RISK-SAFETY**: <risk_safety_count> | **RISK-QUALITY**: <risk_quality_count> | **INFOs**: <info_count>

<Deployment gate description from the table above.>
```

---

### Summary Counts

Display the severity distribution for all non-N/A questions. N/A questions are excluded from these counts entirely.

```markdown
## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | <count> |
| RISK-SAFETY | <count> |
| RISK-QUALITY | <count> |
| INFO | <count> |
| N/A | <count> |
| Not Evaluated (extended) | <count> |
| **Total** | **43** |

**Core Questions Evaluated**: 25 (or fewer if repo_type N/A applies)
**Extended Questions Triggered**: <count>
**Extended Questions Not Triggered**: <count>
**Questions N/A (repo_type: <repo_type>)**: <N/A count>
**Service Archetype**: <archetype> (auto-detected | user-provided)
```

---

### BLOCKERs Section

List all questions that received a BLOCKER severity (including conditional BLOCKERs that resolved to BLOCKER based on `agent_scope`). For each BLOCKER, include remediation guidance.

If there are no BLOCKERs, display: "No BLOCKERs identified."

```markdown
## BLOCKERs — Must Resolve Before Agent Deployment

### <question_id>: <question topic>

- **Severity**: BLOCKER
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing or non-compliant>
- **Remediation**:
  - **Immediate**: <first concrete step to resolve this blocker>
  - **Target State**: <what "resolved" looks like>
  - **Estimated Effort**: <Low / Medium / High>
  - **Dependencies**: <other blockers or risks that interact with this one, or "None">
- **Evidence**: <specific files cited>

<Repeat for each BLOCKER question.>
```

**Remediation Prioritization Guidance:**

There is no universal remediation order — it depends on the use case, the blockers found, and the organization's constraints. However, the following principles apply:

- **Resolve BLOCKERs first.** No agent deployment (including pilots) should proceed with open BLOCKERs. Start with whichever blocker is fastest to resolve to unblock a scoped pilot.
- **Identity before data access.** If both identity (AUTH-Q1) and data classification (DATA-Q1) are blockers, fix identity first — you cannot enforce data access controls without knowing who is calling.
- **Read-only before write-enabled.** If write-operation blockers (API-Q4, STATE-Q1) are present, consider scoping the initial agent to read-only operations while remediating write safety. This unblocks value faster.

---

### RISKs Section

List all questions that received a RISK-SAFETY or RISK-QUALITY severity, grouped by tier. RISK-SAFETY findings are listed first, followed by RISK-QUALITY findings. For each RISK, include compensating control options that allow a scoped pilot to proceed while the risk is remediated.

If there are no RISKs (neither RISK-SAFETY nor RISK-QUALITY), display: "No RISKs identified."

```markdown
## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### <question_id>: <question topic> — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing or incomplete>
- **Compensating Controls**:
  - <option 1: a control that mitigates this risk for a scoped pilot>
  - <option 2: an alternative mitigation approach>
- **Remediation Timeline**: <suggested timeline to fully resolve — e.g., "30–60 days">
- **Recommendation**: <specific next step to remediate>
- **Evidence**: <specific files cited>

<Repeat for each RISK-SAFETY question.>

### RISK-QUALITY — Address as Capacity Allows

#### <question_id>: <question topic> — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing or incomplete>
- **Compensating Controls**:
  - <option 1: a control that mitigates this risk for a scoped pilot>
  - <option 2: an alternative mitigation approach>
- **Remediation Timeline**: <suggested timeline to fully resolve — e.g., "30–60 days">
- **Recommendation**: <specific next step to remediate>
- **Evidence**: <specific files cited>

<Repeat for each RISK-QUALITY question.>
```

**RISK Prioritization Guidance:**

- RISK-SAFETY findings take priority over RISK-QUALITY findings. Address safety risks first — they affect the readiness profile and determine whether the agent can operate safely.
- RISK-QUALITY findings do not affect the readiness profile. They indicate areas where agent effectiveness is reduced, not where safety is compromised. Address as capacity allows.
- Compensating controls buy time, not exemptions. A RISK mitigated by a compensating control (e.g., human-in-the-loop gate) is acceptable for a pilot but must be remediated before expanding scope.

---

### INFOs Section

List all questions that received an INFO severity. INFOs are not deployment gates — they shape architecture decisions and agent design.

If there are no INFOs, display: "No INFOs identified."

```markdown
## INFOs — Architecture and Design Inputs

### <question_id>: <question topic>

- **Severity**: INFO
- **Finding**: <what was observed, with specific file and resource references>
- **Implication**: <how this shapes agent design or architecture decisions>
- **Recommendation**: <optional improvement or consideration>
- **Evidence**: <specific files cited>

<Repeat for each INFO question.>
```

---

### Detailed Findings — All 43 Questions

List every question from all 8 sections in order (API-Q1 through ENG-Q5). This section is the complete record of the analysis. All 43 questions must appear — including N/A questions.

```markdown
## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: <BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO / N/A>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing, or "N/A">
- **Recommendation**: <specific next step, or "N/A">
- **Evidence**: <files cited, or "N/A">

#### API-Q2: Machine-Readable API Specification
- **Severity**: <BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO / N/A>
- **Finding**: <what was observed>
- **Gap**: <what is missing, or "N/A">
- **Recommendation**: <specific next step, or "N/A">
- **Evidence**: <files cited, or "N/A">

<Continue for API-Q3 through API-Q8>

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: <BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO / N/A>
- **Finding**: <what was observed>
- **Gap**: <what is missing, or "N/A">
- **Recommendation**: <specific next step, or "N/A">
- **Evidence**: <files cited, or "N/A">

<Continue for AUTH-Q2 through AUTH-Q7>

### 03 — State Management and Transactional Integrity

<STATE-Q1 through STATE-Q7 in the same format>

### 04 — Human-in-the-Loop and Approval Workflows

<HITL-Q1 through HITL-Q3 in the same format>

### 05 — Data Accessibility and Quality

<DATA-Q1 through DATA-Q7 in the same format>

### 06 — Discoverability and Semantic Readiness

<DISC-Q1 through DISC-Q3 in the same format>

### 07 — Observability of Target Systems

<OBS-Q1 through OBS-Q3 in the same format>

### 08 — Engineering and Deployment Maturity

<ENG-Q1 through ENG-Q5 in the same format>
```

**For N/A questions**, use the N/A display format defined in the N/A Mapping section:

```markdown
#### <question_id>: <question topic>
- **Severity**: N/A
- **Finding**: This is a `<repo_type>` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A
```

**For conditional BLOCKER (⚡) questions** (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2), include the resolved severity based on `agent_scope`:

```markdown
#### <question_id>: <question topic> ⚡
- **Severity**: <BLOCKER if write-enabled / INFO or RISK-SAFETY if read-only>
- **Conditional**: agent_scope is "<agent_scope>" — evaluated as <resolved severity>
- **Finding**: <what was observed>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>
- **Evidence**: <files cited>
```

**For scope-calibrated RISK (⚡) questions** (HITL-Q1, HITL-Q2, STATE-Q3, STATE-Q6), include the resolved severity based on `agent_scope`:

```markdown
#### <question_id>: <question topic> ⚡
- **Severity**: <RISK if write-enabled / INFO if read-only>
- **Scope-Calibrated**: agent_scope is "<agent_scope>" — evaluated as <resolved severity>
- **Finding**: <what was observed>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>
- **Evidence**: <files cited>
```

---

### Evidence Index

Compile a complete index of all files cited as evidence across the analysis. Group by file type for easy reference.

```markdown
## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |
```

If no files were found for a category, omit that category from the evidence index.

**Evidence Rules:**
- Every finding must cite at least one file or explicitly state "No evidence found — absence is itself a finding."
- File paths must be relative to the repository root.
- The same file may appear in multiple categories if it serves multiple purposes (e.g., a `docker-compose.yml` may be cited for both container definitions and configuration).

---

### Table of Contents

The complete report structure, for reference:

```markdown
# Agentic Readiness Analysis Report

1. Readiness Profile
2. Summary
3. BLOCKERs — Must Resolve Before Agent Deployment
4. RISKs
   - RISK-SAFETY — Must Address for Agent Safety
   - RISK-QUALITY — Address as Capacity Allows
5. INFOs — Architecture and Design Inputs
6. Detailed Findings
   - 01 — API Surface and Interface Design (API-Q1 through API-Q8)
   - 02 — Authentication, Authorization, and Identity (AUTH-Q1 through AUTH-Q7)
   - 03 — State Management and Transactional Integrity (STATE-Q1 through STATE-Q7)
   - 04 — Human-in-the-Loop and Approval Workflows (HITL-Q1 through HITL-Q3)
   - 05 — Data Accessibility and Quality (DATA-Q1 through DATA-Q7)
   - 06 — Discoverability and Semantic Readiness (DISC-Q1 through DISC-Q3)
   - 07 — Observability of Target Systems (OBS-Q1 through OBS-Q3)
   - 08 — Engineering and Deployment Maturity (ENG-Q1 through ENG-Q5)
7. Evidence Index
```

