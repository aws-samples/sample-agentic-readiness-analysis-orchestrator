# Report accuracy scores

> **GENERATED FILE — do not edit.** Regenerate with:
> `harness/score-reports.py --show-baseline --markdown harness/SCORES.md`
> (or add `--markdown` to any `--update-baseline` run).

Source: [`harness/golden-accuracy-baseline.json`](golden-accuracy-baseline.json)

Each score is an LLM grader's assessment of how well a generated report is **grounded in the fixture's actual source code** — fabrications and misses count against it. This is the *accuracy* axis, and it is what the judge compares a TD change against. It is NOT the ARA tier or the MOD band, which are the report's own verdicts about the app and appear here as context.

The **Checks** column is a different axis entirely: deterministic, arithmetic assertions that a report does not contradict **itself** — its own severity counters, its own tier arithmetic, its own question coverage. No LLM and no sampling is involved, so a failure here is a real defect at any sample depth, and is safe to act on immediately. A report can be perfectly grounded in the source (high score) and still fail a check by miscounting what it found. Each failure names the check; see [What the checks mean](#what-the-checks-mean).

**Sample depth: up to 3 independent runs per fixture.** `sd` is the measured per-fixture standard deviation and `spread` the max−min across runs; both read `—` where a fixture was drawn only once (it exists in only some batches), because `0.000` there would read as rock-steady when nothing was measured at all.

A delta counts as real only past `max(2·sd, floor)` — the noise floor (**ARA 0.25**, **MOD 0.03**) is a lower bound the measured `sd` can raise but never lower. A jittery fixture is held to a stricter bar than the floor; a quiet one is not held to a looser one, because an n=3 `sd` is far too weak an estimator to justify shrinking the bar and shrinking it is the direction that manufactures false improvements. **Below the threshold means NOT MEASURED — never "proven equal".**

Every batch has its own column — same TD, same fixtures, different run. Columns: `after-tdfix`, `ara-draw2`, `ara-draw3`, `golden`, `s2`, `s3`. The point of showing them side by side is that the mean alone hides disagreement: 0.72 / 0.92 and a steady 0.82 both average to 0.82, but only one of them is a measurement.

## ARA — 14 reports

Mean **0.85**, range 0.81–0.89.

| Repo | Mean | after-tdfix | ara-draw2 | ara-draw3 | golden | s2 | s3 | sd | spread | Checks | Tier / blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `legacy-loan-calculator` | 0.81 | 0.72 | 0.88 | 0.82 | — | — | — | 0.066 | 0.16 | PASS | Remediation Required / 2 |
| `modern-orders-service` | 0.81 | 0.82 | 0.72 | 0.88 | — | — | — | 0.066 | 0.16 | **HIGH** — `missing_safety_qualifier` | Pilot-Ready / 0 |
| `modern-payments-api` | 0.81 | 0.72 | 0.88 | 0.82 | — | — | — | 0.066 | 0.16 | **HIGH** — `missing_safety_qualifier` | Pilot-Ready / 0 |
| `legacy-timesheet-webforms` | 0.81 | 0.78 | 0.88 | 0.78 | — | — | — | 0.047 | 0.10 | PASS | Remediation Required / 2 |
| `legacy-payroll-system` | 0.83 | 0.72 | 0.88 | 0.88 | — | — | — | 0.075 | 0.16 | PASS | Remediation Required / 2 |
| `modern-catalog-graphql` | 0.85 | 0.82 | 0.92 | 0.82 | — | — | — | 0.047 | 0.10 | **HIGH** — `missing_safety_qualifier` | Pilot-Ready / 0 |
| `legacy-partner-soap` | 0.86 | 0.88 | 0.82 | 0.88 | — | — | — | 0.028 | 0.06 | PASS | Remediation Required / 2 |
| `legacy-pricing-cgi` | 0.86 | 0.78 | 0.88 | 0.92 | — | — | — | 0.059 | 0.14 | PASS | Remediation Required / 1 |
| `legacy-helpdesk-tickets` | 0.87 | 0.82 | 0.88 | 0.91 | — | — | — | 0.037 | 0.09 | PASS | Remediation Required / 2 |
| `legacy-document-portal` | 0.88 | 0.88 | 0.88 | 0.88 | — | — | — | 0.000 | 0.00 | PASS | Remediation Required / 2 |
| `legacy-shipping-api` | 0.88 | 0.88 | 0.88 | 0.88 | — | — | — | 0.000 | 0.00 | PASS | Remediation Required / 1 |
| `legacy-storefront-rails` | 0.88 | 0.88 | 0.88 | 0.88 | — | — | — | 0.000 | 0.00 | PASS | Remediation Required / 2 |
| `monolith` | 0.88 | 0.88 | 0.88 | 0.88 | — | — | — | 0.000 | 0.00 | PASS | Remediation Required / 1 |
| `legacy-crm-desktop` | 0.89 | 0.88 | 0.91 | 0.88 | — | — | — | 0.014 | 0.03 | PASS | Remediation Required / 2 |

Run-to-run spread: mean 0.083, worst 0.16 — treat any delta below the worst spread as noise.

## MOD — 14 reports

Mean **0.86**, range 0.62–0.92.

| Repo | Mean | after-tdfix | ara-draw2 | ara-draw3 | golden | s2 | s3 | sd | spread | Checks | MOD score / band |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `modern-orders-service` | 0.62 | — | — | — | — | — | 0.62 | — | 0.00 | PASS | 1.99 / Needs Work |
| `modern-catalog-graphql` | 0.72 | — | — | — | — | — | 0.72 | — | 0.00 | PASS | 2.8 / Partial |
| `legacy-pricing-cgi` | 0.76 | — | — | — | 0.88 | 0.52 | 0.88 | 0.170 | 0.36 | PASS | 1.64 / Needs Work |
| `legacy-shipping-api` | 0.86 | — | — | — | 0.88 | 0.88 | 0.82 | 0.028 | 0.06 | PASS | 1.65 / Needs Work |
| `legacy-partner-soap` | 0.89 | — | — | — | 0.88 | 0.88 | 0.92 | 0.019 | 0.04 | PASS | 1.18 / Not Ready |
| `monolith` | 0.89 | — | — | — | 0.88 | 0.88 | 0.92 | 0.019 | 0.04 | PASS | 1.94 / Needs Work |
| `legacy-helpdesk-tickets` | 0.90 | — | — | — | 0.88 | — | 0.92 | 0.020 | 0.04 | PASS | 1.15 / Not Ready |
| `legacy-loan-calculator` | 0.91 | — | — | — | 0.88 | 0.92 | 0.92 | 0.019 | 0.04 | PASS | 1.2 / Not Ready |
| `legacy-crm-desktop` | 0.92 | — | — | — | 0.92 | 0.92 | 0.92 | 0.000 | 0.00 | PASS | 1.05 / Not Ready |
| `legacy-document-portal` | 0.92 | — | — | — | 0.92 | 0.92 | 0.92 | 0.000 | 0.00 | PASS | 1.18 / Not Ready |
| `legacy-payroll-system` | 0.92 | — | — | — | 0.92 | 0.92 | 0.92 | 0.000 | 0.00 | PASS | 1.05 / Not Ready |
| `legacy-storefront-rails` | 0.92 | — | — | — | 0.92 | 0.92 | 0.92 | 0.000 | 0.00 | PASS | 1.15 / Not Ready |
| `legacy-timesheet-webforms` | 0.92 | — | — | — | 0.92 | 0.92 | 0.92 | 0.000 | 0.00 | PASS | 1.18 / Not Ready |
| `modern-payments-api` | 0.92 | — | — | — | — | — | 0.92 | — | 0.00 | PASS | 3.3 / Partial |

Run-to-run spread: mean 0.041, worst 0.36 — treat any delta below the worst spread as noise.

## Deterministic defects — 3 across 3 reports

Arithmetic contradictions inside a single report — **actionable now**, independent of sample depth.

| Severity | Repo | Check | Detail |
|---|---|---|---|
| high | `modern-catalog-graphql` (ARA) | `missing_safety_qualifier` | blocker_count=0 and risk_safety_count=3 requires sub_qualifier='Safety Concerns', got 'Pilot-Ready (Safety Concerns)' |
| high | `modern-orders-service` (ARA) | `missing_safety_qualifier` | blocker_count=0 and risk_safety_count=10 requires sub_qualifier='Safety Concerns', got 'Pilot-Ready (Safety Concerns)' |
| high | `modern-payments-api` (ARA) | `missing_safety_qualifier` | blocker_count=0 and risk_safety_count=4 requires sub_qualifier='Safety Concerns', got 'Pilot-Ready (Safety Concerns)' |

## What the checks mean

Each check asserts a report is internally consistent. All are deterministic arithmetic — no LLM, no sampling — so a failure is a genuine defect regardless of how many runs we have.

| Check | Severity | What a failure means |
|---|---|---|
| `missing_safety_qualifier` | high | RISK-SAFETY findings exist with no BLOCKER, which requires the "Safety Concerns" qualifier, and it is absent — the report reads safer than the rubric says it is. |

The other 11 checks passed everywhere: `category_band_mismatch`, `duplicate_question_ids`, `incomplete_question_coverage`, `overall_score_band_error`, `overall_score_not_mean_of_categories`, `question_in_both_findings_and_evaluations`, `severity_counter_undercount`, `severity_exceeds_td_ceiling`, `spurious_safety_qualifier`, `tier_contradicts_counts`, `unexpected_question_count`.

## Per-report grader notes

<details><summary>Fabrications and misses per report (18 reports)</summary>

### `legacy-crm-desktop` (ARA) — 0.89

The report is largely accurate about this legacy VB6 desktop CRM repository. It correctly identifies the stateful-crud archetype, applies surface-flag calibrations appropriately (downgrading API-Q2, API-Q3, etc. for no HTTP/RPC surface), and handles the read-only agent_scope conditional severities correctly. The findings cite real code patterns (hardcoded credentials, SQL injection, no API surface). Minor issues include API-Q7 being marked 'pass' when it should be evaluated as a finding for stateful-crud archetype, and some count inconsistencies between findings and evaluations.

- **MISS** [INFO] frmCustomer.frm - INSERT operations with no event emission: API-Q7 Event Emission for State Changes should be evaluated as a finding, not passed
- **DELIVERABLE** remediation_roadmap: Phase 1 includes RISK-SAFETY findings (AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, STATE-Q1, DATA-Q1, DATA-Q2) mixed with BLOCKERs

### `legacy-document-portal` (ARA) — 0.88

The report is largely accurate about this legacy ColdFusion repository. It correctly identifies the two BLOCKERs (API-Q1, AUTH-Q1), properly applies read-only scope downgrades for conditional questions, and the service archetype (stateful-crud) is justified by the SQL Server database and document CRUD operations. Minor issues include weak evidence on some findings and one questionable remediation phasing decision.

- **DELIVERABLE** remediation_roadmap: DATA-Q4 (SQL injection) placed in Phase 1 with correct priority but marked as P2 in the finding itself

### `legacy-loan-calculator` (ARA) — 0.807

The report is largely accurate about this legacy Struts application, correctly identifying the lack of API interface, machine authentication, SQL injection, and hardcoded credentials. The archetype (stateful-crud), repo_type (application), and tier calculation (Remediation Required with 2 BLOCKERs) are all correct. However, there are some calibration issues: AUTH-Q7 should be INFO due to has_auth_surface=false, and DATA-Q6 should also be INFO given has_logging_of_user_data=false AND has_persistent_data_store=true does not fully satisfy the downgrade condition but the surface flags suggest minimal PII logging risk. The evidence quality is strong with specific file/line citations.

- **DELIVERABLE** remediation_roadmap: API-Q4 is listed in Phase 2 findings but it is INFO severity under read-only scope - INFO items should be Phase 3 Quality, not Phase 2 Safety
- **DELIVERABLE** recommended_actions: DATA-Q4 action is marked P1 but the question severity is RISK-QUALITY (Medium), and the action groups it with DATA-Q6 which has different ownership

### `legacy-partner-soap` (ARA) — 0.86

The report is largely accurate about this legacy SOAP service. It correctly identifies the two BLOCKERs (API-Q1 no REST interface, AUTH-Q1 no machine authentication), properly applies conditional severity downgrades for read-only agent scope, and grounds findings in specific code evidence. The archetype classification (stateful-crud) and surface flags are correct. Minor weaknesses include AUTH-Q7 not being downgraded to INFO per calibration rules given has_auth_surface=false, and some findings lack the strongest possible evidence citations.

- **MISS** [INFO (calibration downgrade)] Report metadata shows has_auth_surface=false: AUTH-Q7 should be INFO under calibration rules when has_auth_surface=false
- **DELIVERABLE** remediation_roadmap: DATA-Q4 (SQL injection) is sequenced in Phase 1 with other blockers but marked priority P2 in the finding, creating inconsistency

### `legacy-payroll-system` (ARA) — 0.827

The report is largely accurate and well-grounded in the source code. It correctly identifies the mainframe COBOL batch system with hardcoded FTP credentials, lack of API surface, and sensitive data handling issues. The archetype (stateful-crud) and surface flags are appropriate. However, there are minor issues with the tier arithmetic - the report claims 2 BLOCKERs but API-Q1's BLOCKER status is questionable since the system has no HTTP/RPC surface (the calibration rules suggest this context matters), and DATA-Q6 was incorrectly elevated to RISK-SAFETY when the surface_flags show has_logging_of_user_data=false, which per calibration rules should downgrade it to INFO.

- **DELIVERABLE** recommended_actions: DATA-Q6 PII Redaction in Logs rated as RISK-SAFETY and placed in Phase 1, but calibration rules state it should be INFO when has_logging_of_user_data=false AND has_persistent_data_store=false

### `legacy-shipping-api` (ARA) — 0.88

The report is largely accurate about the legacy-shipping-api repository. It correctly identifies the service archetype (data-gateway), properly applies read-only agent scope calibrations, and grounds findings in actual code evidence. The hardcoded API key, lack of authentication mechanisms, missing input validation, and absence of logging are all real issues correctly identified. Minor issues include some weak evidence citations and a debatable downgrade of AUTH-Q4 to INFO.

- **DELIVERABLE** remediation_roadmap: STATE-Q1 is sequenced in Phase 1 as a blocker-level item but it correctly resolved to RISK-SAFETY under read-only scope

### `legacy-timesheet-webforms` (ARA) — 0.813

The report accurately identifies the key issues in this legacy WebForms application and correctly classifies it as stateful-crud with read-only agent scope. The tier determination (Remediation Required with 2 BLOCKERs) is correct. However, there are several issues: some INFO-level evaluations claim findings were 'emitted' but no corresponding findings exist in the findings array, and the question coverage appears incomplete for several INFO questions that should have findings but only have evaluations.

- **FABRICATION** API-Q5: No finding for API-Q5 exists in the findings array. The evaluation claims a finding was emitted but none was.
- **FABRICATION** API-Q7: No finding for API-Q7 exists in the findings array. The evaluation claims a finding was emitted but none was.
- **FABRICATION** API-Q8: No finding for API-Q8 exists in the findings array. The evaluation claims a finding was emitted but none was.
- **FABRICATION** DATA-Q7: No finding for DATA-Q7 exists in the findings array. The evaluation claims a finding was emitted but none was.
- **FABRICATION** DISC-Q2: No finding for DISC-Q2 exists in the findings array. The evaluation claims a finding was emitted but none was.
- **FABRICATION** DISC-Q3: No finding for DISC-Q3 exists in the findings array. The evaluation claims a finding was emitted but none was.
- **FABRICATION** OBS-Q3: No finding for OBS-Q3 exists in the findings array. The evaluation claims a finding was emitted but none was.
- **FABRICATION** API-Q4: No finding for API-Q4 exists in the findings array despite the evaluation claiming one was emitted.
- **FABRICATION** STATE-Q3: No finding for STATE-Q3 exists in the findings array despite the evaluation claiming one was emitted.
- **FABRICATION** STATE-Q6: No finding for STATE-Q6 exists in the findings array despite the evaluation claiming one was emitted.
- **FABRICATION** HITL-Q1: No finding for HITL-Q1 exists in the findings array despite the evaluation claiming one was emitted.
- **FABRICATION** HITL-Q2: No finding for HITL-Q2 exists in the findings array despite the evaluation claiming one was emitted.
- **DELIVERABLE** remediation_roadmap: DATA-Q4 (SQL injection) is placed in Phase 1 with P2 priority in the finding but P1 in recommended_actions - inconsistent prioritization
- **DELIVERABLE** recommended_actions: Counts are inconsistent - report claims 12 INFO findings but only 29 total findings exist, and evaluations claim findings were emitted that don't exist

### `modern-catalog-graphql` (ARA) — 0.853

The report is largely accurate about this repository, correctly identifying the stateful-crud archetype, the GraphQL/DynamoDB/Lambda stack, and most technical gaps. The tier arithmetic is correct (0 BLOCKER, 3 RISK-SAFETY = Pilot-Ready with Safety Concerns), though the pre-check flagged a formatting issue with sub_qualifier. The report correctly applies scope-dependent severities for read-only scope and grounds findings in actual code. However, there are some weak evidence issues and one questionable finding.

- **DELIVERABLE** service_archetype: None - archetype is correct
- **DELIVERABLE** remediation_roadmap: Phase 1 includes AUTH-Q6 and STATE-Q5 which are RISK-SAFETY, correctly prioritized as safety concerns. However, AUTH-Q4 (also RISK-SAFETY) is placed in Phase 2 instead of Phase 1

### `modern-orders-service` (ARA) — 0.807

The report is substantially accurate about the repository. It correctly identifies the stateful-crud archetype, applies scope-dependent severity downgrades correctly for read-only agent_scope, and grounds findings in real code patterns. The main defect is a malformed sub_qualifier field that puts the qualifier text in a redundant location. Evidence quality is strong with specific file and line references that check out against the source.

- **DELIVERABLE** service_archetype: sub_qualifier field contains redundant tier prefix

### `modern-payments-api` (ARA) — 0.807

The report is largely accurate about this well-architected payments API, correctly identifying its strengths (idempotency, OAuth2 auth, structured logging, IaC) and finding reasonable gaps (no explicit rate limits, no immutable audit storage, no data residency docs). However, there's a structural defect in the classification tier (missing Safety Concerns qualifier format issue noted in pre-checks) and some weak evidence on a few findings. The archetype, surface flags, and most findings are grounded in the actual source code.

- **DELIVERABLE** service_archetype: sub_qualifier format is redundant

### `monolith` (ARA) — 0.88

The report is largely accurate and well-grounded in the source code. It correctly identifies the stateful-crud archetype, properly resolves conditional severities for read-only scope, and provides evidence-based findings. The main issues are some findings that should be in evaluations (INFO items listed as findings instead of pass evaluations) and the question coverage appears incomplete - several INFO-severity items mentioned as 'finding in findings[]' are not actually present in the findings array.

- **DELIVERABLE** remediation_roadmap: Phase 1 includes AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q6 which are all RISK-SAFETY severity, not BLOCKERs. Only AUTH-Q1 is actually a BLOCKER.
- **DELIVERABLE** recommended_actions: Question coverage issue - report claims INFO findings exist in findings[] for API-Q4, API-Q5, API-Q7, API-Q8, STATE-Q3, STATE-Q6, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q7, DISC-Q3, OBS-Q3 but these are not present in the actual findings array

### `legacy-helpdesk-tickets` (MOD) — 0.9

The report is highly accurate about this legacy repository. All 37 questions are correctly resolved with evidence that matches the source code. The service archetype (stateful-crud) is correct given the PostgreSQL/Django CRUD pattern. Pathway triggers are well-grounded: Move to Containers, Move to Managed Databases, and Move to Modern DevOps all cite the right questions at Score 1. The decomposition strategy appropriately recommends Modular Monolith over microservices for this tiny codebase. Minor issues include INF-Q9 being scored when has_deployed_workload=false should gate it out.

- **DELIVERABLE** pathways: INF-Q9 (High Availability) is scored as a finding with Score 1, but has_deployed_workload=false per surface_flags, which should gate it to not_evaluated_surface_flag

### `legacy-pricing-cgi` (MOD) — 0.76

The report is largely accurate and well-grounded in the repository source. Service archetype (stateless-utility), surface flags, and repo_type are all correct. The pathway triggers are appropriate — Move to Containers correctly NOT triggered because Dockerfile/k8s exists, Move to Managed Databases correctly NOT triggered because no database. Most findings cite real evidence from the source. Minor issues include some archetype-gated questions that could arguably have scored 4 rather than being marked not_evaluated, and INF-Q9 was scored as a finding when the surface_flag gate should have excluded it.

- **MISS** [N/A] N/A: INF-Q9 was resolved as a finding with score 2, but the surface_flag gate (has_deployed_workload AND (has_api_surface OR has_persistent_data_store)) evaluates to TRUE for this repo, so this is actually correct - the question should be evaluated. However, the authoritative context says INF-Q9 should be Not Evaluated when gate is false, but gate is TRUE here. This is NOT a miss.
- **DELIVERABLE** pathways: OPS-Q2 is listed in findings with score 1, but according to the surface_flags and authoritative context, OPS-Q2 should be not_evaluated_surface_flag because its gate is (has_api_surface OR has_persistent_data_store). However, has_api_surface=true means the gate IS met, so OPS-Q2 should be evaluated. The report correctly evaluated it as a finding. This is actually NOT a defect.

### `legacy-shipping-api` (MOD) — 0.86

The report is largely accurate and well-grounded in the repository source. It correctly identifies the legacy stack, hardcoded credentials, lack of CI/CD, and EOL dependencies. The archetype (data-gateway) is justified, pathways are appropriately triggered, and most findings cite real evidence. However, there are some scoring inconsistencies and one debatable pathway decision that prevent a higher score.

- **DELIVERABLE** pathways: Move to Containers pathway marked 'Not Triggered' despite containerization being incomplete for production deployment
- **DELIVERABLE** top_gaps: DATA-Q1 ranked in top 5 gaps may be overstated

### `legacy-timesheet-webforms` (MOD) — 0.92

The report is highly accurate about this legacy WebForms repository. It correctly identifies the stateful-crud archetype, properly scores nearly all 37 questions with concrete evidence from the source files, and triggers the right modernization pathways. The findings accurately cite real issues like SQL injection in Timesheet.aspx.vb, plaintext credentials in web.config, and the EOL .NET Framework 2.0/SQL Server 2005 stack. Minor issues include some findings lacking line-number specificity and one debatable pathway decision.

- **DELIVERABLE** pathways: Move to Open Source marked Not Triggered despite self-managed SQL Server 2005 being a commercial database

### `modern-catalog-graphql` (MOD) — 0.72

The report correctly identifies the service archetype, detects many genuine gaps in CI/CD and observability, and accurately triggers only the Move to Modern DevOps pathway. However, it significantly overstates the severity of several operational gaps (OPS-Q5, OPS-Q6, INF-Q11), treating them as High findings when the evidence shows a modern, well-architected serverless application with reasonable maturity. The report also misses that deployment strategy assessment from source code alone is explicitly gated per the spec, and the resulting 'Remediation Required' tier contradicts the actual state of this near-production-ready codebase.

- **DELIVERABLE** top_gaps: OPS-Q5 scored as High/Score 1 claiming 'No deployment strategy — direct-to-production releases'
- **DELIVERABLE** service_archetype: Archetype classification is correct but surface_flags include has_multi_instance_deployment=true without evidence

### `modern-orders-service` (MOD) — 0.62

The report has several accurate findings but contains significant errors. Most critically, DATA-Q1 (Unstructured Data Storage) is marked as a High severity finding claiming the service lacks S3/document handling, but this is inappropriate for an orders service that deals with structured data only - there's no evidence documents are needed. The report also claims 'no tests exist' (OPS-Q6) when the README explicitly states 'Unit + integration tests' and a 'healthy test suite' exists. Additionally, several archetype-appropriate scoring opportunities were missed (e.g., APP-Q3, APP-Q4 could reasonably score higher for a stateful-crud service making limited external calls).

- **FABRICATION** OPS-Q6: README.md explicitly states 'Unit + integration tests' and describes a 'healthy test suite'. The absence of test files in this fixture is due to it being a minimal repository sample, but the report should have noted the documented claim of existing tests rather than asserting definitively that none exist.
- **FABRICATION** DATA-Q1: This is speculative - nothing in the repository indicates the service needs to handle unstructured data. The service deals with structured order data in PostgreSQL. Marking this as High severity is unjustified fabrication of a requirement.
- **DELIVERABLE** top_gaps: DATA-Q1 ranked as a top gap with High severity for missing S3/unstructured data
- **DELIVERABLE** pathways: Move to Modern DevOps pathway correctly triggered but claims 'No tests' as supporting evidence

### `modern-payments-api` (MOD) — 0.92

The report is highly accurate for this well-modernized serverless payments API. The stateful-crud archetype is correct (DynamoDB CRUD operations), the Pilot-Ready tier matches the 1 High finding (OPS-Q5 deployment strategy), and the 37 questions are correctly resolved with strong evidence. The Move to Modern DevOps pathway is appropriately triggered based on INF-Q11/OPS-Q5/OPS-Q6 scores. Minor quibbles exist around SEC-Q7 severity (scored 1 but marked Medium instead of High) but this is within acceptable range given the internal_score is correctly 1.

- **DELIVERABLE** top_gaps: SEC-Q7 listed at rank 3 with score=1 but severity=Medium; a score of 1 (Not Ready) typically warrants High severity

</details>
