# Report accuracy scores

> **GENERATED FILE — do not edit.** Regenerate with:
> `harness/score-reports.py --show-baseline --markdown harness/SCORES.md`
> (or add `--markdown` to any `--update-baseline` run).

Source: [`harness/golden-accuracy-baseline.json`](golden-accuracy-baseline.json)

Each score is an LLM grader's assessment of how well a generated report is **grounded in the fixture's actual source code** — fabrications and misses count against it. This is the *accuracy* axis, and it is what the judge compares a TD change against. It is NOT the ARA tier or the MOD band, which are the report's own verdicts about the app and appear here as context.

The **Checks** column is a different axis entirely: deterministic, arithmetic assertions that a report does not contradict **itself** — its own severity counters, its own tier arithmetic, its own question coverage. No LLM and no sampling is involved, so a failure here is a real defect at any sample depth, and is safe to act on immediately. A report can be perfectly grounded in the source (high score) and still fail a check by miscounting what it found. Each failure names the check; see [What the checks mean](#what-the-checks-mean).

**Sample depth: 1 run per fixture (single draw).** There is no measured variance, so the threshold falls back to the noise floor — **ARA 0.09**, **MOD 0.04** per fixture. That floor was measured by RE-RUNNING the analysis three times, not by re-scoring one report: re-scoring holds the analysis agent constant and so measures only judge jitter, which understated ARA's real noise about 2.5×. Since the ARA floor (0.09) is comparable to the whole observed score range, ARA scores at this depth **cannot rank fixtures against each other**; only the deterministic defects below are safe to act on.

## ARA — 14 reports

Mean **0.85**, range 0.72–0.92.

| Repo | Score | Checks | Tier / blockers |
|---|---|---|---|
| `legacy-loan-calculator` | 0.72 | **HIGH** ×2 | Not Agent-Integrable / 4 |
| `legacy-partner-soap` | 0.72 | PASS | Not Agent-Integrable / 5 |
| `modern-catalog-graphql` | 0.78 | PASS | Remediation Required / 1 |
| `legacy-timesheet-webforms` | 0.82 | **MEDIUM** | Not Agent-Integrable / 5 |
| `modern-payments-api` | 0.82 | PASS | Remediation Required / 2 |
| `legacy-document-portal` | 0.88 | PASS | Not Agent-Integrable / 5 |
| `legacy-helpdesk-tickets` | 0.88 | PASS | Not Agent-Integrable / 7 |
| `legacy-payroll-system` | 0.88 | PASS | Not Agent-Integrable / 7 |
| `legacy-shipping-api` | 0.88 | PASS | Remediation Required / 1 |
| `legacy-storefront-rails` | 0.88 | PASS | Not Agent-Integrable / 7 |
| `modern-orders-service` | 0.88 | PASS | Not Agent-Integrable / 4 |
| `monolith` | 0.88 | PASS | Not Agent-Integrable / 4 |
| `legacy-crm-desktop` | 0.92 | PASS | Not Agent-Integrable / 7 |
| `legacy-pricing-cgi` | 0.92 | PASS | Remediation Required / 2 |

## MOD — 14 reports

Mean **0.86**, range 0.72–0.92.

| Repo | Score | Checks | MOD score / band |
|---|---|---|---|
| `legacy-shipping-api` | 0.72 | PASS | 1.44 / Not Ready |
| `modern-catalog-graphql` | 0.72 | PASS | 2.83 / Partial |
| `modern-orders-service` | 0.72 | PASS | 2.13 / Needs Work |
| `modern-payments-api` | 0.82 | PASS | 3.34 / Partial |
| `legacy-partner-soap` | 0.88 | PASS | 1.18 / Not Ready |
| `legacy-payroll-system` | 0.88 | PASS | 1.2 / Not Ready |
| `legacy-pricing-cgi` | 0.88 | PASS | 1.94 / Needs Work |
| `legacy-storefront-rails` | 0.88 | PASS | 1.18 / Not Ready |
| `legacy-loan-calculator` | 0.91 | PASS | 1.22 / Not Ready |
| `legacy-crm-desktop` | 0.92 | PASS | 1.05 / Not Ready |
| `legacy-document-portal` | 0.92 | PASS | 1.18 / Not Ready |
| `legacy-helpdesk-tickets` | 0.92 | PASS | 1.18 / Not Ready |
| `legacy-timesheet-webforms` | 0.92 | PASS | 1.18 / Not Ready |
| `monolith` | 0.92 | PASS | 1.89 / Needs Work |

## Deterministic defects — 3 across 2 reports

Arithmetic contradictions inside a single report — **actionable now**, independent of sample depth.

| Severity | Repo | Check | Detail |
|---|---|---|---|
| high | `legacy-loan-calculator` (ARA) | `severity_counter_undercount` | blocker_count=4 but 5 findings are natively BLOCKER (undercount by 1; no exclusion rule can lower a counter below the enumerated findings) |
| medium | `legacy-loan-calculator` (ARA) | `severity_counter_undercount` | risk_quality_count=8 but 10 findings are natively RISK-QUALITY (undercount by 2; no exclusion rule can lower a counter below the enumerated findings) |
| medium | `legacy-timesheet-webforms` (ARA) | `severity_counter_undercount` | risk_quality_count=10 but 15 findings are natively RISK-QUALITY (undercount by 5; no exclusion rule can lower a counter below the enumerated findings) |

## What the checks mean

Each check asserts a report is internally consistent. All are deterministic arithmetic — no LLM, no sampling — so a failure is a genuine defect regardless of how many runs we have.

| Check | Severity | What a failure means |
|---|---|---|
| `severity_counter_undercount` | high | A severity counter is LOWER than the findings the report itself enumerated. Exclusion rules can push a counter above the enumerated set, never below it, so this is always an error — and because the ARA tier is computed from these counters, an undercount can mechanically relax the tier. |

The other 12 checks passed everywhere: `category_band_mismatch`, `duplicate_question_ids`, `fabricated_question_id`, `incomplete_question_coverage`, `missing_safety_qualifier`, `overall_score_band_error`, `overall_score_not_mean_of_categories`, `phantom_id_moves_tier`, `question_in_both_findings_and_evaluations`, `severity_exceeds_td_ceiling`, `spurious_safety_qualifier`, `tier_contradicts_counts`.

## Per-report grader notes

<details><summary>Fabrications and misses per report (22 reports)</summary>

### `legacy-crm-desktop` (ARA) — 0.92

The report is highly accurate and well-grounded in the repository source. It correctly identifies the VB6 desktop application architecture, the Access database with hardcoded credentials, SQL injection via string concatenation, lack of any API surface, and the 'On Error Resume Next' error swallowing. The tier classification of 'Not Agent-Integrable' with 7 BLOCKERs is consistent with the findings. Minor issues include AUTH-Q7 being marked INFO when it should remain RISK-SAFETY (has_write_operations is true), and DATA-Q6 similarly should remain RISK-SAFETY given the persistent data store.

- **MISS** [RISK-SAFETY] frmCustomer.frm: AUTH-Q7 downgraded to INFO but system has write operations
- **DELIVERABLE** recommended_actions: AUTH-Q7 not included in any recommended action despite being RISK-SAFETY

### `legacy-document-portal` (ARA) — 0.88

The report is largely accurate about this legacy ColdFusion repository. It correctly identifies the stateful-crud archetype, properly flags the lack of programmatic API, SQL injection vulnerabilities, hardcoded credentials, and absent authentication mechanisms. The tier determination (Not Agent-Integrable with 5 BLOCKERs) is consistent with findings. Minor issues include DATA-Q2 being resolved as INFO when it should be BLOCKER under write-enabled scope with has_persistent_data_store=true, and some phase sequencing concerns in the roadmap.

- **MISS** [BLOCKER] Report finding DATA-Q2: DATA-Q2 resolved as INFO but should be BLOCKER under write-enabled scope with persistent data store
- **DELIVERABLE** remediation_roadmap: DATA-Q4 (SQL injection fix) placed in Phase 1 but given priority P2 in the finding, while DATA-Q1 is in Phase 2 but marked P0

### `legacy-document-portal` (MOD) — 0.92

This is an accurate and well-grounded MOD report for a legacy ColdFusion application. The report correctly identifies the service archetype (stateful-crud), appropriately triggers 4 of 7 modernization pathways based on real evidence, and the findings cite actual code patterns and README documentation. The tier classification (Not Ready with 12 High findings) is consistent with the score-based band (1.18 = Not Ready), and the surface flag gating is correctly applied.

- **DELIVERABLE** pathways: Move to Open Source pathway lists DATA-Q4 in triggering_questions despite the pathway being Not Triggered

### `legacy-helpdesk-tickets` (ARA) — 0.88

The report is largely accurate and well-grounded in the source code. It correctly identifies the service archetype, repo type, and most findings with appropriate evidence. The tier calculation is correct (7 BLOCKERs → Not Agent-Integrable). Minor issues include missing 4 questions from the 43-question requirement (DISC-Q2 and OBS-Q3 are in evaluations but counted as pass, not findings, which is correct, but the total count shows 39 findings + 4 evaluations = 43, so coverage is actually complete). The SQL injection finding is correctly placed under DATA-Q4 at RISK-QUALITY per the rubric.

- **DELIVERABLE** remediation_roadmap: Phase 1 mixes BLOCKERs with RISK-SAFETY and even RISK-QUALITY findings (DATA-Q4 is RISK-QUALITY per rubric)

### `legacy-loan-calculator` (ARA) — 0.72

The report accurately identifies the major issues in this legacy Struts application and correctly classifies it as stateful-crud with write-enabled scope. However, there are several severity inconsistencies: DATA-Q2 should be BLOCKER under write-enabled scope but is marked RISK-SAFETY, HITL-Q1 and HITL-Q2 should be evaluated as RISK-SAFETY findings (not skipped as extended), and AUTH-Q4/AUTH-Q7 are incorrectly downgraded to INFO when they should remain RISK-SAFETY. The blocker_count is undercounted (should be 5, not 4), and the pre-checks confirm counter discrepancies.

- **MISS** [BLOCKER] src/com/acme/loan/LoanAction.java: DATA-Q2 Data Residency and Sovereignty should be BLOCKER under write-enabled scope with PII
- **MISS** [RISK-SAFETY] src/com/acme/loan/LoanAction.java: HITL-Q1 Draft/Pending State should be evaluated as RISK-SAFETY finding, not skipped
- **MISS** [RISK-SAFETY] src/com/acme/loan/LoanAction.java: HITL-Q2 Configurable Approval Gates should be evaluated as RISK-SAFETY finding, not skipped
- **DELIVERABLE** remediation_roadmap: AUTH-Q4 and AUTH-Q7 are marked as INFO in findings but AUTH-Q4 is RISK-SAFETY per the rubric (no calibration rule applies to stateful-crud with has_write_operations=true), and AUTH-Q7 should be RISK-SAFETY since has_write_operations=true
- **DELIVERABLE** service_archetype: Archetype justification is accurate - stateful-crud is correct for a form-based CRUD application with Oracle persistence

### `legacy-partner-soap` (ARA) — 0.72

The report correctly identifies the repository as a stateful-crud application with write-enabled scope and finds many legitimate issues. However, it incorrectly downgrades DATA-Q2 from BLOCKER to RISK-SAFETY under write-enabled scope when the calibration rules don't apply (has_persistent_data_store=true), and STATE-Q3 should be evaluated as RISK-SAFETY per the extended-question trigger (write-enabled + persistent state) but was marked not_evaluated_extended with a flawed rationale. AUTH-Q4 is incorrectly marked INFO when the calibration rule only applies to stateless-utility/data-gateway archetypes, not stateful-crud.

- **MISS** [BLOCKER] src/com/acme/partner/PurchaseOrderService.java: DATA-Q2 should be BLOCKER under write-enabled scope with has_persistent_data_store=true
- **MISS** [RISK-SAFETY] src/com/acme/partner/PurchaseOrderService.java: STATE-Q3 Concurrency Controls should be evaluated as RISK-SAFETY
- **DELIVERABLE** remediation_roadmap: DATA-Q2 is listed in phase 1 at RISK-SAFETY but should be BLOCKER
- **DELIVERABLE** recommended_actions: AUTH-Q4 incorrectly assigned INFO severity in findings when archetype calibration doesn't apply

### `legacy-partner-soap` (MOD) — 0.88

The report is accurate about this legacy SOAP repository. It correctly identifies the hardcoded credentials, EOL stack, lack of IaC/CI-CD, and SQL injection risks with proper file citations. The archetype (stateful-crud), surface flags, and pathway triggers are all well-grounded. Minor issues include DATA-Q4 scoring 4 when the raw JDBC with string concatenation arguably represents significant data access issues, and some weak evidence on infrastructure claims that can only be inferred from README rather than seen in code.

- **DELIVERABLE** top_gaps: DATA-Q1 ranked as #1 gap with score 1 is debatable priority vs SEC-Q5 (hardcoded credentials) which the report itself ranks #1

### `legacy-payroll-system` (ARA) — 0.88

The report is largely accurate about this legacy COBOL payroll system. It correctly identifies the absence of API surfaces, authentication mechanisms, audit logging, and other critical gaps. The tier classification (Not Agent-Integrable with 7 BLOCKERs) is arithmetically correct. However, there are minor issues with question coverage (39 findings+evaluations vs 43 required) and some severity calibration questions where surface-flag downgrades should have applied but didn't.

- **DELIVERABLE** recommended_actions: AUTH-Q7 is marked as finding but listed in Phase 3 as INFO - but the surface-flag calibration rule for AUTH-Q7 states it should be INFO only when has_auth_surface=false AND has_write_operations=false. Since has_write_operations=true, AUTH-Q7 should remain RISK-SAFETY, not INFO.

### `legacy-payroll-system` (MOD) — 0.88

The report is accurate and well-grounded in the repository source. It correctly identifies the COBOL/JCL mainframe system, the hardcoded FTP credentials, the EOL DB2 database, and the complete absence of modern DevOps practices. The archetype classification as event-processor is defensible for a scheduled batch system. Pathway triggers are appropriate and cite real evidence. Minor issues include some surface flag handling that could be questioned.

- **DELIVERABLE** pathways: Move to Open Source pathway logic is questionable

### `legacy-pricing-cgi` (ARA) — 0.92

The report is highly accurate and well-grounded in the repository source. It correctly identifies the stateless-utility archetype, applies scope-dependent severity downgrades properly for read-only agent scope, and cites real code locations. The two BLOCKERs (API-Q1 for HTML-only response, AUTH-Q1 for no authentication) are legitimate and correctly identified. Minor issues include AUTH-Q4 and AUTH-Q7 being filed as INFO findings rather than not_evaluated_extended, but this is defensible given the calibration rules.

- **DELIVERABLE** remediation_roadmap: Phase 1 includes AUTH-Q2, AUTH-Q3, AUTH-Q6, and STATE-Q5 which are RISK-SAFETY severity, not BLOCKERs. The phase is named 'Blockers' but mixes severity levels.

### `legacy-pricing-cgi` (MOD) — 0.88

The report is largely accurate and well-grounded in the repository source. It correctly identifies the stateless-utility archetype, properly gates surface-flag questions (INF-Q2, INF-Q8, SEC-Q1, SEC-Q2, OPS-Q9), and provides concrete evidence from actual files. The pathway triggering is mostly correct, with Move to Modern DevOps appropriately triggered. Minor issues include questionable scoring on a few questions and some weak evidence citations, but no fabrications were found.

- **MISS** [Medium] k8s/deployment.yaml: INF-Q9 was scored as a finding (score 1) but should have been gated out as not_evaluated_surface_flag
- **MISS** [Medium] k8s/: OPS-Q2 was scored as a finding (score 1) but per surface flags (has_api_surface=true), this is correctly evaluated, not gated
- **MISS** [Medium] k8s/deployment.yaml: OPS-Q5 and OPS-Q7 were evaluated as findings but per the gating rules (has_deployed_workload gate), they should be evaluated since has_deployed_workload=true
- **DELIVERABLE** pathways: Move to Cloud Native pathway lists INF-Q1=3 as not meeting threshold, but the logic explanation is confusing - it says 'INF-Q1 = 3 does not meet < 3 threshold' but then in notes says 'INF-Q1 = 3 meets threshold'

### `legacy-shipping-api` (ARA) — 0.88

The report is largely accurate and well-grounded in the source code. It correctly identifies the service archetype as data-gateway, properly applies read-only agent scope calibrations, and grounds findings in specific files and line numbers. The tier determination is correct (Remediation Required with 1 BLOCKER). Minor issues include API-Q1 being marked as a pass when the README explicitly states the service has no documented API interface, and some weak evidence on a few findings.

- **MISS** [BLOCKER] server.js, README.md: API-Q1 should be a BLOCKER finding - there is no documented API interface. The README describes the architecture but the actual endpoints (GET /rates, POST /quote) are only discoverable by reading server.js code. No API documentation, OpenAPI spec, or interface contract exists.

### `legacy-shipping-api` (MOD) — 0.72

The report demonstrates solid understanding of the repository's legacy state and correctly identifies most issues, but contains a significant fabrication regarding IaC coverage (ignoring the CloudFormation template), misses the ALB's HTTP-only exposure as a security concern under SEC-Q3, and has some pathway triggering inconsistencies. The archetype selection and most findings are well-grounded in the source code.

- **FABRICATION** INF-Q10: infrastructure/shipping-alb.yaml is a CloudFormation template that provisions an ALB, security group, target group, listener, and S3 bucket. This is IaC, not 0% coverage. Score should be 2 (Needs Work) not 1, as partial IaC exists but doesn't cover compute/database.
- **MISS** [High] infrastructure/shipping-alb.yaml: ALB exposes API over HTTP-only (port 80) with plaintext API key transmission across public internet - TODO comment explicitly notes HTTPS blocked since 2019
- **DELIVERABLE** pathways: Move to Containers marked 'Not Triggered' because container definitions exist, but the pathway should evaluate whether the containerization is DEPLOYED on managed compute, not just whether files exist
- **DELIVERABLE** top_gaps: INF-Q10 listed as top gap with 'No IaC' claim

### `legacy-storefront-rails` (ARA) — 0.88

The report is largely accurate and well-grounded in the source code. It correctly identifies the major issues (SQL injection, hardcoded credentials, mass assignment, lack of authentication) and maps them appropriately to the ARA rubric questions. The service archetype (stateful-crud), repo type (application), and agent scope (write-enabled) are all correct. The tier calculation is consistent with the blocker/risk-safety counts. Minor issues include some weak evidence citations and a few questions that could have been more precisely evaluated.

- **DELIVERABLE** remediation_roadmap: Phase 1 includes RISK-SAFETY findings (AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q7, STATE-Q3, STATE-Q4, STATE-Q5, HITL-Q1, HITL-Q2, DATA-Q6) mixed with BLOCKERs

### `legacy-storefront-rails` (MOD) — 0.88

The report is largely accurate about this legacy Rails repository. Service archetype (stateful-crud), repo type (application), and surface flags are correctly identified. The 37 questions are properly resolved with appropriate gating. Most findings cite real evidence from README.md and orders_controller.rb. Minor issues include some debatable severity classifications and the DATA category score calculation appears slightly off, but overall the report correctly identifies this as a deeply legacy codebase requiring significant modernization.

- **DELIVERABLE** top_gaps: DATA-Q3 listed with score 1 but DATA category shows numeric_score 1.75, which requires DATA-Q4=4 to average correctly with DATA-Q1=1, DATA-Q2=1, DATA-Q3=1. The math checks out (1+1+1+4)/4=1.75, so this is actually correct.

### `legacy-timesheet-webforms` (ARA) — 0.82

The report is largely accurate about this legacy WebForms repository, correctly identifying the lack of API surface, SQL injection vulnerabilities, hardcoded credentials, and missing authentication mechanisms. The service archetype (stateful-crud) and surface flags are correct. However, the risk_quality_count is undercounted (10 vs 15 actual RISK-QUALITY findings), and DATA-Q1/DATA-Q2 are resolved to INFO when the write-enabled scope and surface flags should trigger BLOCKER severity for these conditional questions.

- **MISS** [BLOCKER] Timesheet.aspx.vb: DATA-Q1 should be BLOCKER under write-enabled scope with has_persistent_data_store=true
- **DELIVERABLE** remediation_roadmap: DATA-Q4 (SQL injection) placed in Phase 1 but should arguably be higher priority given active injection vulnerability

### `modern-catalog-graphql` (ARA) — 0.78

The report is largely accurate about this well-structured GraphQL catalog service, correctly identifying the stateful-crud archetype, write-enabled scope, and most findings are grounded in real code. However, the AUTH-Q6 BLOCKER finding is questionable given the README explicitly states soft-delete is recoverable and the infrastructure includes X-Ray tracing. The report also correctly identifies several quality gaps (no CI/CD, no tests, missing depth limits) with proper evidence. The main issue is the tier determination - given the codebase has JWT auth, idempotent writes, and soft-delete, the BLOCKER severity for AUTH-Q6 is debatable.

- **DELIVERABLE** remediation_roadmap: STATE-Q3 and STATE-Q5 placed in Phase 1 alongside the BLOCKER, but these are RISK-SAFETY not BLOCKER
- **DELIVERABLE** recommended_actions: HITL-Q1 and HITL-Q2 grouped as P1 priority

### `modern-catalog-graphql` (MOD) — 0.72

The report is largely grounded in the repository source but makes several questionable severity calls and has pathway/deliverable issues. The archetype and repo_type are correct. However, marking OPS-Q5 and OPS-Q6 as High findings for a serverless Lambda application is debatable — Lambda deployments are atomic by design and the README explicitly states this is 'close to agent-ready' with 'only routine hardening advised.' The report's tier of 'Remediation Required' contradicts the README's own assessment of 'Pilot-Ready.'

- **DELIVERABLE** pathways: Move to Modern DevOps pathway correctly triggered, but the severity assessment driving it is questionable for serverless architecture
- **DELIVERABLE** top_gaps: SEC-Q7 listed as Score 1 but marked Medium severity, yet appears in top_gaps. OPS-Q5 and OPS-Q6 as High findings for a serverless app is aggressive

### `modern-orders-service` (ARA) — 0.88

The report accurately identifies the key safety gaps documented in the repository (idempotency, audit logging, compensation/rollback, rate limiting, HITL controls) and correctly classifies the service as stateful-crud with write-enabled scope. The tier determination is consistent with the blocker count, and evidence citations point to real code patterns. However, there are a few issues: AUTH-Q2 and AUTH-Q3 are marked as passing but the report doesn't address that role-based auth exists only at the broad read/write level without fine-grained per-operation authorization (e.g., separate permission for delete vs refund). The DATA-Q1 resolution is well-reasoned through the B1/B2/B3 ladder. Minor weakness in some evidence lacking specific line references.

- **DELIVERABLE** remediation_roadmap: Phase 1 mixes BLOCKERs with RISK-SAFETY findings without clear separation

### `modern-orders-service` (MOD) — 0.72

The report correctly identifies the service archetype, repo type, and most infrastructure gaps, but contains several inaccuracies including a fabricated High-severity finding for DATA-Q1 (object storage) which is inappropriate for this CRUD service, incorrectly gates out SEC-Q1 when the IaC does provision AWS resources, and the triggered pathway for Modern DevOps is reasonable but some pathway logic is questionable. The overall assessment is grounded but has notable defects.

- **FABRICATION** DATA-Q1: This is an orders CRUD service with PostgreSQL for structured order data. There is no evidence the service needs object storage - no receipts, invoices, or document handling mentioned in the actual code. The README and SAFETY.md describe order management, not document storage. Scoring this as High/P1 is inappropriate for a service that doesn't need this capability.
- **DELIVERABLE** top_gaps: DATA-Q1 (Unstructured Data Storage) ranked as a top gap with High severity when this CRUD service has no requirement for object storage
- **DELIVERABLE** pathways: SEC-Q1 marked as not_evaluated_surface_flag claiming 'application-level IaC only' when has_iac_provisioning_aws_resources=true in the surface flags

### `modern-payments-api` (MOD) — 0.82

The report is largely accurate and well-grounded in the source code. It correctly identifies the stateful-crud archetype, accurately scores the modern serverless architecture, and appropriately triggers the Modern DevOps pathway for the missing CD pipeline. However, there are some questionable findings around the Move to AI pathway trigger (weak justification) and the OPS-Q9 score of 1 is arguably harsh given the SAM template does have some implicit resource organization, though the lack of explicit tags is real.

- **DELIVERABLE** pathways: Move to AI pathway triggered with weak justification

### `monolith` (ARA) — 0.88

The report is largely accurate and well-grounded in the source code. It correctly identifies the stateful-crud archetype, write-enabled scope, and major gaps including missing machine identity auth, non-idempotent writes, lack of compensation logic, and incomplete audit logging. The tier calculation is correct (4 BLOCKERs → Not Agent-Integrable). Minor issues include DATA-Q2 being marked as pass when it should be a BLOCKER under write-enabled scope, and some weak evidence on specific line citations.

- **MISS** [BLOCKER] index.php (MySQL database with customer PII), infrastructure/monolith-apprunner.yaml: DATA-Q2 Data Residency and Sovereignty marked as pass but should be BLOCKER under write-enabled scope with has_persistent_data_store=true
- **DELIVERABLE** remediation_roadmap: DATA-Q2 is not in phase 1 because it was incorrectly evaluated as pass

</details>
