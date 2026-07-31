# Report accuracy scores

> **GENERATED FILE — do not edit.** Regenerate with:
> `harness/score-reports.py --show-baseline --markdown harness/SCORES.md`
> (or add `--markdown` to any `--update-baseline` run).

Source: [`harness/golden-accuracy-baseline.json`](golden-accuracy-baseline.json)

Each score is an LLM grader's assessment of how well a generated report is **grounded in the fixture's actual source code** — fabrications and misses count against it. This is the *accuracy* axis, and it is what the judge compares a TD change against. It is NOT the ARA tier or the MOD band, which are the report's own verdicts about the app and appear here as context.

The **Checks** column is a different axis entirely: deterministic, arithmetic assertions that a report does not contradict **itself** — its own severity counters, its own tier arithmetic, its own question coverage. No LLM and no sampling is involved, so a failure here is a real defect at any sample depth, and is safe to act on immediately. A report can be perfectly grounded in the source (high score) and still fail a check by miscounting what it found. Each failure names the check; see [What the checks mean](#what-the-checks-mean).

**Sample depth: up to 4 independent runs per fixture, 3 fixture(s) drawn once.** `sd` is the measured per-fixture standard deviation and `spread` the max−min across runs. Both read `—` for a fixture drawn only once — not `0.000`, which would read as re-run and rock-steady when nothing was compared at all.

A delta counts as real only past `max(2·sd, floor)` — the noise floor (**ARA 0.25**, **MOD 0.03**) is a lower bound the measured `sd` can raise but never lower. A jittery fixture is held to a stricter bar than the floor; a quiet one is not held to a looser one, because an n=4 `sd` is far too weak an estimator to justify shrinking the bar and shrinking it is the direction that manufactures false improvements. **Below the threshold means NOT MEASURED — never "proven equal".**

The per-run scores are listed in the **Runs** column rather than one column per batch: the two analyses are sampled from different batches, so a shared column per batch left every row half-empty and the reader counting dashes to work out which run was which. The point of showing the runs at all is that the mean hides disagreement — 0.72 / 0.92 and a steady 0.82 both average to 0.82, but only one of them is a measurement.

## ARA — 14 reports

Mean **0.86**, range 0.82–0.89.

| Repo | Mean | Runs | sd | spread | Checks | Tier / blockers |
|---|---|---|---|---|---|---|
| `legacy-payroll-system` | 0.82 | 0.72 / 0.82 / 0.88 / 0.88 | 0.065 | 0.16 | PASS | Remediation Required / 2 |
| `modern-orders-service` | 0.82 | 0.88 / 0.72 / 0.88 / 0.82 | 0.065 | 0.16 | PASS | Pilot-Ready / 0 |
| `modern-payments-api` | 0.82 | 0.72 / 0.88 / 0.82 / 0.88 | 0.065 | 0.16 | PASS | Pilot-Ready / 0 |
| `legacy-timesheet-webforms` | 0.83 | 0.78 / 0.88 / 0.78 / 0.88 | 0.050 | 0.10 | PASS | Remediation Required / 2 |
| `legacy-loan-calculator` | 0.84 | 0.72 / 0.88 / 0.88 / 0.88 | 0.069 | 0.16 | PASS | Remediation Required / 2 |
| `legacy-partner-soap` | 0.86 | 0.88 / 0.82 / 0.88 / 0.85 | 0.025 | 0.06 | PASS | Remediation Required / 2 |
| `legacy-document-portal` | 0.86 | 0.88 / 0.88 / 0.88 / 0.82 | 0.026 | 0.06 | PASS | Remediation Required / 2 |
| `legacy-helpdesk-tickets` | 0.87 | 0.82 / 0.92 / 0.92 / 0.82 | 0.050 | 0.10 | PASS | Remediation Required / 2 |
| `legacy-pricing-cgi` | 0.87 | 0.78 / 0.88 / 0.92 / 0.91 | 0.055 | 0.14 | PASS | Remediation Required / 2 |
| `legacy-crm-desktop` | 0.88 | 0.88 / 0.88 / 0.88 / 0.88 | 0.000 | 0.00 | PASS | Remediation Required / 2 |
| `legacy-shipping-api` | 0.88 | 0.88 / 0.88 / 0.88 / 0.88 | 0.000 | 0.00 | PASS | Remediation Required / 1 |
| `legacy-storefront-rails` | 0.88 | 0.88 / 0.88 / 0.88 / 0.88 | 0.000 | 0.00 | PASS | Remediation Required / 2 |
| `modern-catalog-graphql` | 0.89 | 0.88 / 0.92 / 0.82 / 0.92 | 0.041 | 0.10 | PASS | Pilot-Ready / 0 |
| `monolith` | 0.89 | 0.88 / 0.92 / 0.88 / 0.88 | 0.017 | 0.04 | PASS | Remediation Required / 1 |

Run-to-run spread: mean 0.089, worst 0.16 — treat any delta below the worst spread as noise.

## MOD — 14 reports

Mean **0.86**, range 0.62–0.92.

| Repo | Mean | Runs | sd | spread | Checks | MOD score / band |
|---|---|---|---|---|---|---|
| `modern-orders-service` | 0.62 | 0.62 | — | — | PASS | 1.99 / Needs Work |
| `modern-catalog-graphql` | 0.72 | 0.72 | — | — | PASS | 2.8 / Partial |
| `legacy-pricing-cgi` | 0.76 | 0.88 / 0.52 / 0.88 | 0.170 | 0.36 | PASS | 1.64 / Needs Work |
| `legacy-shipping-api` | 0.86 | 0.88 / 0.88 / 0.82 | 0.028 | 0.06 | PASS | 1.65 / Needs Work |
| `legacy-partner-soap` | 0.89 | 0.88 / 0.88 / 0.92 | 0.019 | 0.04 | PASS | 1.18 / Not Ready |
| `monolith` | 0.89 | 0.88 / 0.88 / 0.92 | 0.019 | 0.04 | PASS | 1.94 / Needs Work |
| `legacy-helpdesk-tickets` | 0.90 | 0.88 / 0.92 | 0.020 | 0.04 | PASS | 1.15 / Not Ready |
| `legacy-loan-calculator` | 0.91 | 0.88 / 0.92 / 0.92 | 0.019 | 0.04 | PASS | 1.2 / Not Ready |
| `legacy-crm-desktop` | 0.92 | 0.92 / 0.92 / 0.92 | 0.000 | 0.00 | PASS | 1.05 / Not Ready |
| `legacy-document-portal` | 0.92 | 0.92 / 0.92 / 0.92 | 0.000 | 0.00 | PASS | 1.18 / Not Ready |
| `legacy-payroll-system` | 0.92 | 0.92 / 0.92 / 0.92 | 0.000 | 0.00 | PASS | 1.05 / Not Ready |
| `legacy-storefront-rails` | 0.92 | 0.92 / 0.92 / 0.92 | 0.000 | 0.00 | PASS | 1.15 / Not Ready |
| `legacy-timesheet-webforms` | 0.92 | 0.92 / 0.92 / 0.92 | 0.000 | 0.00 | PASS | 1.18 / Not Ready |
| `modern-payments-api` | 0.92 | 0.92 | — | — | PASS | 3.3 / Partial |

Run-to-run spread: mean 0.053, worst 0.36 — treat any delta below the worst spread as noise.

## Deterministic defects — 0 across 0 reports

None.

## What the checks mean

Each check asserts a report is internally consistent. All are deterministic arithmetic — no LLM, no sampling — so a failure is a genuine defect regardless of how many runs we have.

All checks passed on every report. The full set: `category_band_mismatch`, `duplicate_question_ids`, `incomplete_question_coverage`, `missing_safety_qualifier`, `overall_score_band_error`, `overall_score_not_mean_of_categories`, `question_in_both_findings_and_evaluations`, `severity_counter_undercount`, `severity_exceeds_td_ceiling`, `spurious_safety_qualifier`, `tier_contradicts_counts`, `unexpected_question_count`.

## Per-report grader notes

<details><summary>Fabrications and misses per report (19 reports)</summary>

### `legacy-crm-desktop` (ARA) — 0.88

The report accurately identifies the legacy VB6 desktop application's fundamental lack of API surface and authentication, correctly classifying it as stateful-crud with read-only agent scope. Evidence citations are concrete and grounded in the actual source code. The tier arithmetic is correct (2 BLOCKERs → Remediation Required), and scope-dependent questions are properly resolved. Minor issues include DATA-Q6 being elevated to RISK-SAFETY when surface flags suggest INFO would be appropriate, and some weak evidence on extended questions.

- **DELIVERABLE** remediation_roadmap: DATA-Q6 listed in Phase 1 as RISK-SAFETY finding, but per calibration rules it should be INFO

### `legacy-document-portal` (ARA) — 0.865

The report is largely accurate about the legacy ColdFusion application, correctly identifying its lack of API surface, authentication mechanisms, and numerous security deficiencies. The archetype (stateful-crud) and scope handling are correct. However, there are issues with the has_http_rpc_surface flag being set to false when the application does serve HTTP requests, and some calibration downgrades were applied incorrectly as a result.

- **DELIVERABLE** service_archetype: has_http_rpc_surface set to false

### `legacy-helpdesk-tickets` (ARA) — 0.87

The report is largely accurate about this legacy Django repository, correctly identifying the lack of API surface, missing authentication, hardcoded credentials, SQL injection vulnerabilities, and PII exposure. The service archetype (stateful-crud) and repo_type (application) are correct. However, there are some issues with AUTH-Q7 severity under the calibration rules and a few weak evidence items. The roadmap phasing is generally sound with blockers in phase 1.

- **DELIVERABLE** recommended_actions: AUTH-Q7 is marked RISK-SAFETY but should be INFO per calibration rules

### `legacy-loan-calculator` (ARA) — 0.84

The report is largely accurate about this legacy loan calculator repository. It correctly identifies the stateful-crud archetype, the lack of programmatic API, hardcoded credentials, SQL injection vulnerability, and absence of modern infrastructure. The conditional BLOCKER resolutions for read-only scope are correctly applied. Minor issues include some weak evidence citations and a questionable DATA-Q6 finding given the surface flag indicates no user data logging.

- **DELIVERABLE** recommended_actions: DATA-Q6 finding is questionable given surface_flags.has_logging_of_user_data=false

### `legacy-partner-soap` (ARA) — 0.857

The report is largely accurate about this legacy SOAP service, correctly identifying the stateful-crud archetype, documenting real issues like SQL injection, XXE vulnerabilities, hardcoded credentials, and missing modern API interfaces. The tier calculation is correct (2 BLOCKERs → Remediation Required), and scope-dependent questions are properly resolved for read-only scope. However, there are minor issues with deliverable phasing and some weak evidence citations.

- **DELIVERABLE** remediation_roadmap: API-Q4 (idempotency) is placed in Phase 2 but was correctly resolved as INFO under read-only scope - INFO items should be Phase 3
- **DELIVERABLE** recommended_actions: Action 5 'Implement input validation and parameterized queries' is marked P1 but DATA-Q4 is RISK-QUALITY severity which maps to P2

### `legacy-payroll-system` (ARA) — 0.825

The report is largely accurate about this legacy COBOL payroll system. It correctly identifies the lack of API surface (API-Q1) and machine authentication (AUTH-Q1) as BLOCKERs, properly applies scope-dependent severity downgrades for read-only agent_scope, and appropriately marks questions N/A due to surface flags (no HTTP/RPC surface). The archetype classification and surface flags are correct. Minor issues include weak evidence for DATA-Q6 (the claim of PII in logs is speculative) and some phase sequencing that mixes RISK-SAFETY items into Phase 1.

- **DELIVERABLE** remediation_roadmap: Phase 1 includes RISK-SAFETY findings (AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, STATE-Q1, DATA-Q1, DATA-Q2) alongside the actual BLOCKERs

### `legacy-shipping-api` (ARA) — 0.88

The report is largely accurate and well-grounded in the source code. It correctly identifies the service archetype as data-gateway, appropriately applies read-only scope calibrations, and cites specific files and line numbers for evidence. The tier determination (Remediation Required with 1 BLOCKER) is consistent with the findings. Minor issues include AUTH-Q4 being resolved as INFO which is correct per calibration rules, but some weak evidence exists where findings cite broad line ranges.

- **DELIVERABLE** remediation_roadmap: STATE-Q1 is placed in Phase 2 but has native_severity RISK-SAFETY

### `legacy-storefront-rails` (ARA) — 0.88

The report is largely accurate and well-grounded in the source code. It correctly identifies the service archetype, applies conditional BLOCKER resolutions appropriately for read-only scope, and cites real evidence from the repository. The tier calculation is correct (2 BLOCKERs = Remediation Required). Minor issues include some evaluations marked 'pass' that should emit INFO findings, and a few weak evidence citations for infrastructure-level findings.

- **DELIVERABLE** remediation_roadmap: Phase 1 includes AUTH-Q4 (Identity Propagation) which is RISK-SAFETY, but the report places it in Phase 2 in the roadmap items while listing it correctly in Phase 1 summary text - inconsistent
- **DELIVERABLE** recommended_actions: STATE-Q1 (Compensation and Rollback) is a RISK-SAFETY finding but is not included in any recommended action

### `legacy-timesheet-webforms` (ARA) — 0.83

The report is largely accurate about this legacy WebForms repository. It correctly identifies the BLOCKERs (API-Q1, AUTH-Q1), applies scope-calibrated severities correctly for read-only agent_scope, and grounds findings in real code patterns (SQL injection, plaintext credentials, lack of API surface). The archetype classification as stateful-crud is correct. Minor issues include DATA-Q6 being elevated to RISK-SAFETY when surface-flag calibration should have applied (has_logging_of_user_data=false), and some weak evidence on a few evaluations.

- **DELIVERABLE** remediation_roadmap: DATA-Q6 is included in Phase 1 as a RISK-SAFETY finding, but per surface-flag calibration rules, with has_logging_of_user_data=false AND has_persistent_data_store=true, the calibration rule does not fully apply. However, the finding claims PII exposure through error messages, which is a different vector than logging. This is a borderline interpretation issue rather than a clear defect.

### `modern-orders-service` (ARA) — 0.825

The report is largely accurate about this repository, correctly identifying the stateful-crud archetype, documenting real safety gaps around irreversible operations, and properly applying read-only scope calibration to conditional questions. The main defect is a structural one with the tier qualifier format (already flagged in pre-checks). Evidence citations are concrete and verifiable against the source. Some findings could be stronger in evidence specificity, but there are no fabrications and no missed BLOCKERs or RISK-SAFETY issues given the read-only scope.

- **DELIVERABLE** remediation_roadmap: Phase 1 includes INFO-severity items (API-Q4, STATE-Q3, HITL-Q1, HITL-Q2) alongside RISK-SAFETY items

### `modern-payments-api` (ARA) — 0.825

The report is largely accurate and well-grounded in the source code. It correctly identifies the stateful-crud archetype, properly applies read-only scope calibrations for conditional BLOCKERs, and provides evidence-backed findings. The main structural defect is the malformed sub_qualifier field ('Pilot-Ready (Safety Concerns)' instead of just 'Safety Concerns'), but this was already flagged in pre-checks. Most findings cite real files and patterns that exist in the repository.

- **DELIVERABLE** service_archetype: sub_qualifier format is incorrect

### `monolith` (ARA) — 0.89

The report is largely accurate about the repository, correctly identifying the PHP monolithic e-commerce application's lack of machine identity authentication (AUTH-Q1 BLOCKER), session-based auth, and various security gaps. The service archetype (stateful-crud) is correct given the MySQL database with CRUD operations. Most findings cite real code patterns. However, there are some issues with findings recorded where evaluations should be (INFO items appearing in findings rather than evaluations), and a few extended questions that should have been evaluated were marked not_evaluated_extended.

- **MISS** [INFO] index.php - order_status_history table and update_order_status function: API-Q7 Event Emission for State Changes should be evaluated as a finding since stateful-crud archetype triggers it
- **DELIVERABLE** recommended_actions: First action claims to address AUTH-Q2, AUTH-Q3, AUTH-Q7 but implementing API keys alone does not solve scoped permissions (AUTH-Q2), action-level authorization (AUTH-Q3), or identity suspension (AUTH-Q7)
- **DELIVERABLE** remediation_roadmap: Phase 1 includes AUTH-Q4 (Identity Propagation) but AUTH-Q4 is listed as Phase 2 in the finding itself with P2 priority

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
