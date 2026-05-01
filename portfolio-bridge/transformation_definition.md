## Name

Portfolio Agentic Readiness — Modernization Bridge Assessment

## Objective

Cross-reference the portfolio-level Agentic Readiness Assessment (ARA) report and the portfolio-level Modernization Assessment (MOD) report to produce a unified bridge report that maps shared findings, quantifies the agentic readiness impact of modernization work, identifies foundational gaps that block ARA remediation, and deduplicates overlapping remediation items — enabling coordinated planning across both assessments.

## Summary

This transformation consumes two portfolio-level reports — the portfolio ARA report (`*-portfolio-ara-report.md`) and the portfolio MOD report (`*-portfolio-mod-report.md`) — and produces a single bridge report that unifies findings from both assessments. It uses a built-in cross-reference mapping (see Step 0.4) to connect ARA findings with their MOD co-requisites.

The bridge report answers three critical planning questions:
1. **What work is shared?** Which remediation items resolve findings in both assessments simultaneously?
2. **What is the modernization dividend?** How many ARA BLOCKERs would be resolved as a side effect of completing MOD Phase 0?
3. **What blocks what?** Where do MOD foundational gaps prevent ARA remediation from even starting?

The transformation follows a 5-section pipeline:
1. **Shared Remediation Mapping** — Map ARA findings to MOD co-requisites using the built-in cross-reference mapping
2. **Agentic Readiness Delta** — Quantify ARA BLOCKERs resolved if MOD Phase 0 were completed
3. **MOD Readiness Gate** — Advisory when MOD SEC or OPS category averages indicate foundational gaps
4. **Unified Remediation Sequence** — Merge ARA remediation and MOD Phase 0 roadmap into a single plan
5. **Shared Findings Deduplication** — List findings appearing in both portfolio reports

The output is a Markdown report saved as `{portfolio_name}-bridge-report.md` at the portfolio root directory.

This bridge TD only runs when `assessment_type: full` — it requires both portfolio reports to exist. It is supplementary: if it fails, the already-completed ARA and MOD portfolio reports are unaffected.

## Entry Criteria

- Both the portfolio ARA report and the portfolio MOD report exist and are readable at the paths specified in `additionalPlanContext`
- Reports follow the expected structure: readiness profiles, severity counts, category averages, cross-cutting findings, and phased roadmaps
- Write permissions exist to create the bridge report file at the portfolio root directory

## Implementation Steps

### Step 0: Read additionalPlanContext and Validate Inputs

Before beginning analysis, read the bridge assessment context from `additionalPlanContext` and validate that both required portfolio reports exist.

#### 0.1 Read Bridge Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `portfolio_ara_report_path` | string | **Yes** | — | File path to the portfolio ARA report (e.g., `agentic-readiness-assessment/ecommerce-platform-v2-portfolio-ara-report.md`). |
| `portfolio_mod_report_path` | string | **Yes** | — | File path to the portfolio MOD report (e.g., `modernization-assessment/ecommerce-platform-v2-portfolio-mod-report.md`). |
| `portfolio_name` | string | **Yes** | — | Name of the portfolio (e.g., `ecommerce-platform-v2`). Used in the output filename and report title. |
| `bpmn_opportunity_report_paths` | string[] | No | — | **Deprecated.** Use `portfolio_bao_report_path` instead. If individual report paths are provided, the Bridge TD will still attempt to read them but the preferred input is the portfolio-level BAO report. |
| `portfolio_bao_report_path` | string | No | -- | File path to the Portfolio BAO report (e.g., `bpmn-opportunity-assessment/my-platform-portfolio-bao-report.md`). When present, the bridge report includes a BAO + ARA Readiness Matrix (Section 6). When absent, Section 6 is omitted and the bridge report works as before (ARA + MOD only). |

**Example `additionalPlanContext`:**

```yaml
additionalPlanContext: |
  portfolio_ara_report_path: "agentic-readiness-assessment/ecommerce-platform-v2-portfolio-ara-report.md"
  portfolio_mod_report_path: "modernization-assessment/ecommerce-platform-v2-portfolio-mod-report.md"
  portfolio_name: "ecommerce-platform-v2"
  portfolio_bao_report_path: "bpmn-opportunity-assessment/ecommerce-platform-v2-portfolio-bao-report.md"
```

#### 0.2 Validate Required Inputs

Attempt to read both portfolio reports at the specified paths. If either report is missing or unreadable, **terminate immediately** with the following error message:

```
ERROR: Cannot generate bridge report. Missing required input:
- Portfolio ARA report: {portfolio_ara_report_path} — {found/NOT FOUND}
- Portfolio MOD report: {portfolio_mod_report_path} — {found/NOT FOUND}

The bridge report requires both portfolio reports. Run the full assessment 
(assessment_type: full) to generate both reports before running the bridge TD.
```

Do not proceed to any subsequent steps if either report is missing. The bridge report cannot be generated from a single assessment.

#### 0.3 Parse Portfolio Reports

Once both reports are validated as present and readable, parse the following data from each:

**From the Portfolio ARA Report:**
- Readiness distribution (count of services per profile)
- Readiness snapshot metrics (total_blockers, total_risks, total_risk_safety, total_risk_quality, cross_cutting_blockers, cross_cutting_risks)
- Cross-cutting BLOCKERs (question IDs, affected services, severity)
- Cross-cutting RISKs by tier (RISK-SAFETY and RISK-QUALITY question IDs, affected services)
- Per-service findings (question ID → severity for each service)
- Portfolio-level remediation guidance

**From the Portfolio MOD Report:**
- Category score averages (INF, APP, DATA, SEC, OPS)
- Per-service scores by category
- Cross-cutting foundational blockers (question IDs, affected services, scores)
- Phase 0 roadmap items (cross-cutting foundation activities)
- Pathway aggregation results
- Per-service findings (question ID → score for each service)

#### 0.4 MOD-ARA Cross-Reference Mapping

Use the following built-in mapping table to connect ARA findings with their MOD co-requisites. This mapping defines the relationships between the two assessment frameworks — MOD evaluates whether infrastructure is modern enough to support cloud-native patterns, while ARA evaluates whether that infrastructure is safe enough for autonomous AI agents. The relationship is directional: MOD foundation → ARA safety layer → agent deployment.

**Mapping Table:**

| ARA Finding | ARA Severity | MOD Co-Requisite(s) | Relationship | Direction |
|---|---|---|---|---|
| AUTH-Q1: Machine Identity | BLOCKER | SEC-Q3: API Authentication + SEC-Q4: Centralized Identity | MOD is prerequisite | MOD → ARA |
| AUTH-Q2: Scoped Permissions | RISK | SEC-Q3: API Authentication + SEC-Q4: Centralized Identity | Same infrastructure | MOD → ARA |
| AUTH-Q3: Action-Level Auth | RISK | SEC-Q3: API Authentication + INF-Q6: API Entry Point | Same infrastructure | MOD → ARA |
| AUTH-Q4: Identity Propagation | RISK | SEC-Q4: Centralized Identity | MOD is prerequisite | MOD → ARA |
| AUTH-Q5: Credential Management | RISK | SEC-Q5: Secrets Management | Same finding, different lens | Shared |
| AUTH-Q6: Immutable Audit Logging | RISK | SEC-Q1: Audit Logging + OPS-Q1: Distributed Tracing | MOD is prerequisite | MOD → ARA |
| AUTH-Q7: Identity Suspension | RISK | SEC-Q4: Centralized Identity | MOD is prerequisite | MOD → ARA |
| API-Q2: Machine-Readable Spec | RISK | APP-Q5: API Versioning | Complementary | Shared |
| API-Q3: Structured Errors | RISK | APP-Q5: API Versioning + INF-Q6: API Entry Point | Complementary | Shared |
| STATE-Q5: Rate Limiting | RISK | INF-Q6: API Entry Point | MOD is prerequisite | MOD → ARA |
| OBS-Q1: Distributed Tracing | RISK | OPS-Q1: Distributed Tracing | Same finding | Shared |
| OBS-Q2: Alerting | RISK | OPS-Q4: Anomaly Detection | Same finding | Shared |
| DISC-Q1: Schema Versioning | RISK | APP-Q5: API Versioning | Same finding, different lens | Shared |
| ENG-Q1: Infra Governance | RISK | INF-Q10: IaC Coverage | Same finding | Shared |
| ENG-Q2: CI/CD + Contract Tests | RISK | INF-Q11: CI/CD Automation + OPS-Q6: Integration Testing | MOD is prerequisite | MOD → ARA |
| DATA-Q1: Data Classification | BLOCKER | DATA-Q1: Unstructured Data + SEC-Q5: Secrets Mgmt | Complementary | ARA extends MOD |
| HITL-Q3: Sandbox/Staging | RISK | OPS-Q5: Deployment Strategy | MOD is prerequisite | MOD → ARA |

**Relationship types:**
- **MOD → ARA**: MOD finding must be resolved before ARA finding can be addressed. ARA remediation is blocked until MOD co-requisite scores improve.
- **Shared**: Same underlying gap viewed through different lenses. One remediation action resolves both the MOD and ARA findings.
- **ARA extends MOD**: ARA adds agent-specific requirements on top of what MOD already evaluates. MOD remediation partially addresses the ARA finding, but additional agent-specific work is needed.

Store this mapping table for use in Sections 1–5.

---

### Step 1: Shared Remediation Mapping

Map ARA findings to their MOD co-requisites using the built-in cross-reference mapping. This section shows teams which remediation actions resolve findings in both assessments.

#### 1.1 Build the Mapping Table

For each entry in the MOD-ARA mapping table:

1. Look up the ARA finding in the portfolio ARA report:
   - Determine the resolved severity (BLOCKER, RISK-SAFETY, RISK-QUALITY, INFO, or N/A)
   - Identify which services are affected (severity is not INFO or N/A)
   - Count the number of affected services

2. Look up the MOD co-requisite(s) in the portfolio MOD report:
   - Determine the average score across all services for each MOD question
   - Identify which services score below 2.0 (indicating a gap)
   - Count the number of services with gaps

3. Record the relationship type (MOD → ARA prerequisite, Shared, ARA extends MOD)

4. Derive the shared remediation action from the cross-reference mapping relationships

#### 1.2 Output Format

Present the shared remediation mapping as a table:

```markdown
## Section 1: Shared Remediation Mapping

This section maps ARA findings to their MOD co-requisites using the built-in cross-reference mapping. 
Each row shows an ARA finding, its MOD dependency, and the shared remediation action that resolves both.

| ARA Finding | ARA Severity | Affected Services | MOD Co-Requisite(s) | MOD Avg Score | MOD Gap Services | Relationship | Shared Remediation Action |
|---|---|---|---|---|---|---|---|
| AUTH-Q1: Machine Identity | BLOCKER | 4 of 5 | SEC-Q3: API Auth (avg X.X) + SEC-Q4: Centralized Identity (avg X.X) | X.X | N of M | MOD → ARA | Deploy centralized identity provider (e.g., Amazon Cognito) with client_credentials grant |
| AUTH-Q2: Scoped Permissions | RISK-SAFETY | N of M | SEC-Q3: API Auth + SEC-Q4: Centralized Identity | X.X | N of M | MOD → ARA | Configure fine-grained OAuth2 scopes in centralized identity provider |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

For each mapping entry, include a brief narrative explaining the relationship:
- **MOD → ARA prerequisite**: "The MOD gap must be resolved before the ARA finding can be addressed. ARA remediation is blocked until MOD co-requisite scores improve."
- **Shared**: "Same underlying gap viewed through different lenses. One remediation action resolves both the MOD and ARA findings."
- **ARA extends MOD**: "ARA adds agent-specific requirements on top of what MOD evaluates. MOD remediation partially addresses the ARA finding, but additional agent-specific work is needed."

If no mapping matches are found between the portfolio reports, output:
```
No shared findings identified between ARA and MOD reports. The two assessments did not flag overlapping concerns for this portfolio.
```

---

### Step 2: Agentic Readiness Delta

Quantify how many ARA BLOCKERs would be resolved if MOD Phase 0 cross-cutting foundation items were completed. This gives teams a concrete answer to: "What is the agentic readiness dividend of modernization?"

#### 2.1 Identify Eligible ARA BLOCKERs

From the portfolio ARA report, collect all ARA BLOCKERs (both per-service and cross-cutting). For each BLOCKER:

1. Check if the BLOCKER's question ID appears in the MOD-ARA mapping table
2. Check if the relationship type is `MOD → ARA` (MOD is prerequisite)
3. If yes, this BLOCKER is eligible for resolution via MOD Phase 0

#### 2.2 Check MOD Phase 0 Coverage

For each eligible ARA BLOCKER:

1. Identify the MOD co-requisite question(s) from the mapping table
2. Check if the MOD co-requisite appears in the portfolio MOD report's Phase 0 roadmap (cross-cutting foundation items)
3. If the MOD co-requisite is in Phase 0, the ARA BLOCKER would be resolved when Phase 0 completes

#### 2.3 Calculate the Delta

Count the total ARA BLOCKERs and the number that would be resolved by MOD Phase 0:

```markdown
## Section 2: Agentic Readiness Delta

**If MOD Phase 0 were completed, {X} of {Y} ARA BLOCKERs would be resolved.**

This means {percentage}% of the portfolio's agentic readiness blockers are actually modernization prerequisites — 
completing MOD Phase 0 delivers an agentic readiness dividend without any ARA-specific remediation work.

### BLOCKERs Resolved by MOD Phase 0

| ARA BLOCKER | Affected Services | MOD Phase 0 Item | How It Resolves |
|---|---|---|---|
| AUTH-Q1: Machine Identity | 4 services | Deploy centralized identity (SEC-Q3 + SEC-Q4) | Centralized identity provider enables machine identity for agents |
| ... | ... | ... | ... |

### BLOCKERs Requiring ARA-Specific Remediation

| ARA BLOCKER | Affected Services | Why MOD Phase 0 Doesn't Resolve |
|---|---|---|
| DATA-Q1: Data Classification | 3 services | ARA requires field-level PII classification and agent-specific redaction — MOD data platform maturity doesn't cover this |
| ... | ... | ... |
```

#### 2.4 Edge Cases

- If no ARA BLOCKERs have MOD → ARA prerequisite relationships, state: "No ARA BLOCKERs have MOD prerequisites. ARA remediation can proceed independently of modernization work."
- If all ARA BLOCKERs would be resolved by MOD Phase 0, state: "All ARA BLOCKERs are modernization prerequisites. Completing MOD Phase 0 would eliminate all agentic readiness blockers."

---

### Step 3: MOD Readiness Gate

Provide an informational advisory when MOD category averages indicate foundational gaps that will block ARA remediation. This is not a hard gate — it is guidance to help teams sequence their work correctly.

#### 3.1 Check MOD Category Averages

From the portfolio MOD report's category score averages, check:

1. **SEC (Security Baseline) category average**: If < 2.0, ARA identity and access remediation will be blocked
2. **OPS (Operations & Observability) category average**: If < 2.0, ARA observability remediation will be blocked

#### 3.2 Output Format

```markdown
## Section 3: MOD Readiness Gate

This section provides informational advisories when MOD category averages indicate foundational gaps 
that will block ARA remediation efforts. These are not hard gates — they are sequencing guidance.
```

**If MOD SEC category average < 2.0:**
```markdown
### ⚠️ Security Baseline Gap

**MOD SEC category average: {score} / 4.0**

ARA identity and access remediation (AUTH-Q1 through AUTH-Q7) will be blocked by MOD security baseline gaps.

**What this means:** The portfolio's security infrastructure (API authentication, centralized identity, secrets management, 
audit logging) scores below the minimum threshold for ARA remediation to be effective. Teams should prioritize MOD SEC 
remediation before attempting ARA AUTH remediation.

**Affected ARA findings:** AUTH-Q1 (Machine Identity), AUTH-Q2 (Scoped Permissions), AUTH-Q3 (Action-Level Auth), 
AUTH-Q4 (Identity Propagation), AUTH-Q5 (Credential Management), AUTH-Q6 (Audit Logging), AUTH-Q7 (Identity Suspension)
```

**If MOD OPS category average < 2.0:**
```markdown
### ⚠️ Operational Baseline Gap

**MOD OPS category average: {score} / 4.0**

ARA observability remediation (AUTH-Q6, OBS-Q1, OBS-Q2) will be blocked by MOD operational gaps.

**What this means:** The portfolio's operational infrastructure (distributed tracing, anomaly detection, deployment strategies) 
scores below the minimum threshold for ARA observability remediation to be effective. Teams should prioritize MOD OPS 
remediation before attempting ARA observability remediation.

**Affected ARA findings:** AUTH-Q6 (Immutable Audit Logging), OBS-Q1 (Distributed Tracing), OBS-Q2 (Alerting)
```

**If neither gate is triggered:**
```markdown
MOD category averages are above the 2.0 threshold for both SEC ({sec_score}) and OPS ({ops_score}). 
No foundational gaps are blocking ARA remediation. Teams can proceed with ARA remediation in parallel with MOD improvements.
```

**If MOD category averages are unavailable:**
```markdown
MOD category averages not available — readiness gate analysis skipped. 
Verify that the portfolio MOD report contains category score averages.
```

---

### Step 4: Unified Remediation Sequence

Merge the ARA remediation guidance and MOD Phase 0 roadmap into a single sequence that shows which items resolve findings in both assessments simultaneously. This prevents teams from planning the same work twice under different labels.

#### 4.1 Build the Unified Sequence

Using the MOD-ARA mapping and the data parsed from both portfolio reports:

1. **Start with MOD Phase 0 items** — These are the cross-cutting foundation activities from the portfolio MOD report's phased roadmap. For each Phase 0 item:
   - Identify which MOD findings it resolves (from the MOD report)
   - Cross-reference with the mapping table to identify which ARA findings it also resolves
   - List both MOD and ARA resolutions

2. **Add ARA-specific remediation items** — These are ARA findings that have no MOD co-requisite (relationship type `ARA extends MOD`) or where the MOD co-requisite is not in Phase 0. These must be addressed separately after MOD Phase 0.

3. **Sequence the items** — MOD Phase 0 items come first (they unblock ARA remediation), followed by ARA-specific items.

#### 4.2 Output Format

```markdown
## Section 4: Unified Remediation Sequence

This section merges the ARA remediation guidance and MOD Phase 0 roadmap into a single sequence. 
Items that resolve findings in both assessments are marked as **dual-resolution** — completing them 
delivers value for both modernization and agentic readiness simultaneously.

### Phase 0: Cross-Cutting Foundation (MOD + ARA)

These items come from the MOD Phase 0 roadmap. Each item shows which MOD findings AND which ARA findings 
it resolves. Complete these first — they unblock ARA remediation.

#### 1. {Foundation Item Title}

**MOD Findings Resolved:**
- {MOD question ID}: {topic} — {N} services affected

**ARA Findings Resolved:**
- {ARA question ID}: {topic} ({severity}) — {N} services affected

**ARA Findings Unblocked** (can be addressed after this item completes):
- {ARA question ID}: {topic} ({severity})

**Dual-Resolution Impact:** This single item resolves {X} MOD findings and {Y} ARA findings across {Z} services.

---

#### 2. {Next Foundation Item}
...

### ARA-Specific Remediation (After Phase 0)

These ARA findings have no MOD co-requisite or require agent-specific work beyond what MOD Phase 0 provides. 
Address these after MOD Phase 0 completes.

#### 1. {ARA Remediation Item Title}

**ARA Finding:** {question ID}: {topic} ({severity}) — {N} services affected
**Why Not Covered by MOD:** {explanation}
**Remediation Action:** {action}
```

---

### Step 5: Shared Findings Deduplication

List findings that appear in both portfolio reports so teams don't plan the same work twice. This section identifies overlapping findings by matching ARA question IDs to their MOD co-requisites from the mapping table.

#### 5.1 Identify Overlapping Findings

For each entry in the MOD-ARA mapping table where the relationship is `Shared`:

1. Check if the ARA finding appears in the portfolio ARA report as a finding (not N/A, not INFO)
2. Check if the MOD co-requisite appears in the portfolio MOD report as a gap (score < 2.0 in any service)
3. If both conditions are met, this is a shared finding that teams might plan twice

Also check `MOD → ARA` relationships where both the ARA finding and MOD co-requisite are flagged — these represent the same underlying infrastructure gap even though the relationship is directional.

#### 5.2 Output Format

```markdown
## Section 5: Shared Findings Deduplication

These findings appear in both the portfolio ARA report and the portfolio MOD report. 
They represent the same underlying gap viewed through different assessment lenses. 
**Plan remediation once, not twice.**

| # | ARA Finding | ARA Severity | MOD Finding | MOD Avg Score | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 1 | AUTH-Q5: Credential Management | RISK-SAFETY | SEC-Q5: Secrets Management | X.X | Shared | Migrate to AWS Secrets Manager with automated rotation |
| 2 | OBS-Q1: Distributed Tracing | RISK-QUALITY | OPS-Q1: Distributed Tracing | X.X | Shared | Deploy X-Ray/ADOT across all services |
| ... | ... | ... | ... | ... | ... | ... |

### Deduplication Summary

- **{N} findings** appear in both assessments
- **{M} remediation items** can be consolidated (planned once instead of twice)
- **Estimated effort savings:** Teams avoid duplicating planning and execution for shared infrastructure gaps
```

If no overlapping findings are found:
```markdown
No overlapping findings identified between the ARA and MOD portfolio reports. 
All findings are unique to their respective assessments and should be planned independently.
```

---

### Step 6: BAO + ARA Readiness Matrix (Conditional)

When `portfolio_bao_report_path` is present in `additionalPlanContext`, read the Portfolio BAO report and cross-reference agent task dependencies against Portfolio ARA findings to produce a readiness matrix. When absent, skip this step entirely and omit Section 6 from the report.

#### 6.1 Read Portfolio BAO Report

Read the Portfolio BAO report at the specified path. Extract:
- Portfolio opportunity summary (total tasks, agent count, categories)
- Top agent opportunities with their dependencies
- Dependency coverage (by type and vendor)
- Unknown dependencies (tasks with no system references)

#### 6.2 Build the Readiness Matrix

For each agent-classified task in the BPMN reports:

1. Identify the task's target system dependencies (from the dependency section of the BPMN report)
2. Look up each target system in the portfolio ARA report:
   - If the target system has an ARA report: record its readiness profile and BLOCKER count
   - If the target system has no ARA report: mark as "unassessed"
3. Classify the agent opportunity:
   - **Ready**: target system is Agent-Ready or Pilot-Ready (0 BLOCKERs)
   - **Blocked**: target system has 1+ ARA BLOCKERs
   - **Unassessed**: target system has no ARA assessment

#### 6.3 Output Format

```markdown
## Section 6: BAO + ARA Readiness Matrix

> This section cross-references BAO-identified agent opportunities with ARA readiness
> findings for their target systems. It answers: "Which agent opportunities can we build
> today, which are blocked by ARA findings, and which need ARA assessment first?"

### Readiness Matrix

| BPMN Process | Agent Task | Target System | ARA Profile | BLOCKERs | Status |
|---|---|---|---|---|---|
| {process} | {task_name} | {target_ref} | {profile or "Unassessed"} | {count or "N/A"} | Ready / Blocked / Unassessed |

### Summary

| Status | Agent Opportunities | Description |
|--------|--------------------:|-------------|
| Ready | {N} | Target systems are Agent-Ready or Pilot-Ready, build agents now |
| Blocked | {N} | Target systems have ARA BLOCKERs, resolve before building agents |
| Unassessed | {N} | Target systems not yet evaluated by ARA, run ARA to determine readiness |

### Blocked Opportunities Detail

For each blocked agent opportunity, list the specific ARA BLOCKERs on the target system
and cross-reference with the MOD co-requisites from Section 1:

| Agent Task | Target System | ARA BLOCKER(s) | MOD Co-Requisite | In MOD Phase 0? |
|---|---|---|---|---|
| {task} | {system} | {blocker_ids} | {mod_ids or "None"} | Yes / No / N/A |

> **Interpretation**: Blocked opportunities where the ARA BLOCKER has a MOD Phase 0 co-requisite
> will be unblocked when MOD Phase 0 completes (see Section 2: Agentic Readiness Delta).
```

If no Portfolio BAO report is available or is unreadable, omit this entire section.

---

### Step 7: Generate Bridge Report

Compile all sections into the final bridge report and save it.

#### 6.1 Report Structure

```markdown
# Portfolio ARA–MOD Bridge Report

**Portfolio**: {portfolio_name}
**Date**: {current_date}
**ARA Report**: {portfolio_ara_report_path}
**MOD Report**: {portfolio_mod_report_path}

---

## Bridge Summary

| Metric | Value |
|--------|-------|
| Shared Remediation Mappings | {count from Section 1} |
| ARA BLOCKERs Resolvable by MOD Phase 0 | {X of Y from Section 2} |
| MOD Readiness Gates Triggered | {count from Section 3} |
| Unified Remediation Items | {count from Section 4} |
| Deduplicated Shared Findings | {count from Section 5} |
| BPMN Agent Opportunities (Ready / Blocked / Unassessed) | {X / Y / Z from Section 6, or "N/A" if no Portfolio BAO report} |

---

{Section 1: Shared Remediation Mapping}

---

{Section 2: Agentic Readiness Delta}

---

{Section 3: MOD Readiness Gate}

---

{Section 4: Unified Remediation Sequence}

---

{Section 5: Shared Findings Deduplication}

---

{Section 6: BAO + ARA Readiness Matrix -- included only when portfolio_bao_report_path is provided}
```

#### 6.2 Save the Report

Save the bridge report as `{portfolio_name}-bridge-report.md` at the portfolio root directory (the same level as the `agentic-readiness-assessment/` and `modernization-assessment/` directories, not inside either one).

**Output path:** `{portfolio_name}-bridge-report.md`
