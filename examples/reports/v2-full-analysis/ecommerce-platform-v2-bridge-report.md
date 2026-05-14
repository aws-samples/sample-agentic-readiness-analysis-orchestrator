# Portfolio ARA–MOD Bridge Report

**Portfolio**: ecommerce-platform-v2
**Date**: 2026-04-17
**ARA Report**: portfolio-ara-report.md
**MOD Report**: portfolio-mod-report.md

---

## Bridge Summary

| Metric | Value |
|--------|-------|
| Shared Remediation Mappings | 17 (all 17 cross-reference entries have active findings in both reports) |
| ARA BLOCKERs Resolvable by MOD Phase 0 | 5 of 9 (4 service-level AUTH-Q1 instances + 1 portfolio-level PORT-ARA-Q1) |
| MOD Readiness Gates Triggered | 2 (SEC at 1.86 and OPS at 1.33, both < 2.0) |
| Unified Remediation Items | 14 (8 MOD Phase 0 items + 6 ARA-specific items) |
| Deduplicated Shared Findings | 15 (7 Shared + 8 MOD → ARA with both sides active) |

---

## Section 1: Shared Remediation Mapping

This section maps ARA findings to their MOD co-requisites using the built-in cross-reference mapping.
Each row shows an ARA finding, its MOD dependency, and the shared remediation action that resolves both.

| ARA Finding | ARA Severity | Affected Services | MOD Co-Requisite(s) | MOD Avg Score | MOD Gap Services | Relationship | Shared Remediation Action |
|---|---|---|---|---|---|---|---|
| AUTH-Q1: Machine Identity | BLOCKER | 4 of 5 | SEC-Q3: API Auth (avg 1.60) + SEC-Q4: Centralized Identity (avg 1.60) | 1.60 | 3 of 5 | MOD → ARA | Deploy shared Amazon Cognito User Pool with `client_credentials` grant for machine-to-machine auth |
| AUTH-Q2: Scoped Permissions | RISK-SAFETY | 5 of 5 | SEC-Q3: API Auth (avg 1.60) + SEC-Q4: Centralized Identity (avg 1.60) | 1.60 | 3 of 5 | MOD → ARA | Configure fine-grained OAuth2 scopes in centralized Cognito with per-service resource servers |
| AUTH-Q3: Action-Level Auth | RISK-SAFETY | 5 of 5 | SEC-Q3: API Auth (avg 1.60) + INF-Q6: API Entry Point (avg 2.40) | 2.00 | 3 of 5 | MOD → ARA | Add API Gateway authorizers with method-level restrictions and per-service action-level middleware |
| AUTH-Q4: Identity Propagation | RISK | 5 of 5 | SEC-Q4: Centralized Identity (avg 1.60) | 1.60 | 3 of 5 | MOD → ARA | Implement token propagation via shared Cognito — JWT tokens carry identity across service boundaries |
| AUTH-Q5: Credential Management | RISK-QUALITY | 1 of 5 | SEC-Q5: Secrets Management (avg 2.40) | 2.40 | 3 of 5 (< 3) | Shared | Migrate all secrets to AWS Secrets Manager with automated rotation; use External Secrets Operator on EKS |
| AUTH-Q6: Immutable Audit Logging | RISK-SAFETY | 5 of 5 | SEC-Q1: Audit Logging (avg 1.40) + OPS-Q1: Distributed Tracing (avg 1.60) | 1.50 | 3–4 of 5 | MOD → ARA | Deploy account-level CloudTrail with S3 Object Lock + ADOT/X-Ray for distributed tracing |
| AUTH-Q7: Identity Suspension | RISK-SAFETY | 5 of 5 | SEC-Q4: Centralized Identity (avg 1.60) | 1.60 | 3 of 5 | MOD → ARA | Build suspension into shared Cognito — disable App Client to revoke agent access in seconds |
| API-Q2: Machine-Readable Spec | RISK-QUALITY | 4 of 4 | APP-Q5: API Versioning (avg 1.00) | 1.00 | 4 of 4 | Shared | Mandate `/v1/` URL versioning + generate OpenAPI 3.0 specs for all services |
| API-Q3: Structured Errors | RISK-QUALITY | 4 of 4 | APP-Q5: API Versioning (avg 1.00) + INF-Q6: API Entry Point (avg 2.40) | 1.70 | 3–4 of 5 | Shared | Define portfolio-wide error schema (`error_code`, `message`, `retryable`) + API Gateway error mapping |
| STATE-Q5: Rate Limiting | RISK-SAFETY | 4 of 4 | INF-Q6: API Entry Point (avg 2.40) | 2.40 | 3 of 5 (< 3) | MOD → ARA | Deploy API Gateway with usage plans and per-agent-key throttling for all services |
| OBS-Q1: Distributed Tracing | RISK-QUALITY | 5 of 5 | OPS-Q1: Distributed Tracing (avg 1.60) | 1.60 | 4 of 5 | Shared | Deploy ADOT Collector on EKS + enable X-Ray on all Lambda functions (books-api is reference) |
| OBS-Q2: Alerting | RISK-QUALITY | 5 of 5 | OPS-Q4: Anomaly Detection (avg 1.20) | 1.20 | 4 of 5 | Shared | Deploy centralized CloudWatch alarms + Prometheus AlertManager on EKS + SNS integration |
| DISC-Q1: Schema Versioning | RISK-QUALITY | 4 of 4 | APP-Q5: API Versioning (avg 1.00) | 1.00 | 4 of 4 | Shared | Add `/v1/` prefix to all API paths + commit OpenAPI specs + add breaking change detection to CI |
| ENG-Q1: Infra Governance | RISK-QUALITY | 5 of 5 | INF-Q10: IaC Coverage (unishop=1) | 1.00* | 1 of 5 | Shared | Require IaC for all services; create Terraform IaC for unishop-monolith; add AWS Config drift detection |
| ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY | 5 of 5 | INF-Q11: CI/CD Automation (avg 1.60) + OPS-Q6: Integration Testing (avg 1.40) | 1.50 | 3–4 of 5 | MOD → ARA | Create shared CI/CD pipeline templates with API contract test stages using OpenAPI spec diffs |
| DATA-Q1: Data Classification | BLOCKER | 4 of 4 | DATA-Q1: Unstructured Data (avg 1.00) + SEC-Q5: Secrets Mgmt (avg 2.40) | 1.70 | 4 of 4 | ARA extends MOD | Create portfolio-wide data classification policy + per-service PII tagging + Macie for automated detection |
| HITL-Q3: Sandbox/Staging | RISK-QUALITY | 4 of 4 | OPS-Q5: Deployment Strategy (avg 1.80) | 1.80 | 3 of 5 | MOD → ARA | Implement progressive delivery (CodeDeploy, Flagger) + create agent-testing-focused staging environments |

*INF-Q10 is not a cross-cutting foundational blocker at the portfolio level — only unishop-monolith scores 1; other services have IaC and score higher.*

### Relationship Type Explanations

- **MOD → ARA prerequisite** (9 entries): The MOD gap must be resolved before the ARA finding can be addressed. ARA remediation is blocked until MOD co-requisite scores improve. Example: AUTH-Q1 (Machine Identity) cannot be implemented without SEC-Q3 (API Authentication) and SEC-Q4 (Centralized Identity) infrastructure.

- **Shared** (7 entries): Same underlying gap viewed through different lenses. One remediation action resolves both the MOD and ARA findings. Example: OBS-Q1 (Distributed Tracing in ARA) and OPS-Q1 (Distributed Tracing in MOD) are literally the same finding — deploying ADOT/X-Ray resolves both.

- **ARA extends MOD** (1 entry): ARA adds agent-specific requirements on top of what MOD already evaluates. MOD remediation partially addresses the ARA finding, but additional agent-specific work is needed. Example: DATA-Q1 in ARA requires field-level PII classification and agent-specific redaction — MOD's unstructured data storage only addresses the storage platform.

## Section 2: Agentic Readiness Delta

**If MOD Phase 0 were completed, 5 of 9 ARA BLOCKERs would be resolved.**

This means 56% of the portfolio's agentic readiness blockers are actually modernization prerequisites — completing MOD Phase 0 delivers an agentic readiness dividend without any ARA-specific remediation work.

**Breakdown:**
- Total ARA BLOCKERs: 9 (AUTH-Q1 × 4 services + DATA-Q1 × 4 services + PORT-ARA-Q1 × 1 portfolio-level)
- Resolvable by MOD Phase 0: 5 (AUTH-Q1 × 4 services + PORT-ARA-Q1)
- Requiring ARA-specific remediation: 4 (DATA-Q1 × 4 services)

### BLOCKERs Resolved by MOD Phase 0

| ARA BLOCKER | Affected Services | MOD Phase 0 Item | How It Resolves |
|---|---|---|---|
| AUTH-Q1: Machine Identity (unishop-monolith) | 1 of 4 | Centralized Identity (Cognito) — SEC-Q3 + SEC-Q4 | Shared Cognito User Pool with `client_credentials` grant enables machine identity; unishop-monolith enables existing Spring Security OAuth2 with Cognito provider |
| AUTH-Q1: Machine Identity (aws-microservices) | 1 of 4 | Centralized Identity (Cognito) — SEC-Q3 + SEC-Q4 | Cognito authorizer added to all 3 API Gateway REST APIs via CDK |
| AUTH-Q1: Machine Identity (local-monolith) | 1 of 4 | Centralized Identity (Cognito) — SEC-Q3 + SEC-Q4 | OAuth2 bearer token validation middleware added to PHP application |
| AUTH-Q1: Machine Identity (books-api) | 1 of 4 | Centralized Identity (Cognito) — SEC-Q3 + SEC-Q4 | Existing Cognito User Pool extended with `client_credentials` App Client (lowest effort — 1–2 days) |
| PORT-ARA-Q1: Centralized Identity Plane | Portfolio-level | Centralized Identity (Cognito) — SEC-Q3 + SEC-Q4 | Shared Cognito pool across all services simultaneously addresses the portfolio-level identity gap |

**Modernization Dividend:** Completing the "Centralized Identity (Cognito)" item in MOD Phase 0 eliminates all 4 AUTH-Q1 service-level BLOCKERs and the PORT-ARA-Q1 portfolio-level BLOCKER in a single investment. This also **unblocks** ARA remediation for AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q6, and AUTH-Q7 across all 5 services — identity is the prerequisite for all other security controls.

### BLOCKERs Requiring ARA-Specific Remediation

| ARA BLOCKER | Affected Services | Why MOD Phase 0 Doesn't Resolve |
|---|---|---|
| DATA-Q1: Data Classification (unishop-monolith) | 1 of 4 | ARA requires field-level PII classification (`email`, `first_name`, `last_name` in `unicorn_user`) and agent-specific response filtering. MOD Phase 0 DATA-Q1 addresses unstructured data *storage* (S3 buckets) but not data *classification* for agent safety. |
| DATA-Q1: Data Classification (aws-microservices) | 1 of 4 | ARA requires PII tagging and field-level encryption for `cardInfo` and `email` in DynamoDB. MOD Phase 0 does not include data classification or PII protection — only S3 object storage. |
| DATA-Q1: Data Classification (local-monolith) | 1 of 4 | ARA requires classification of customer PII across 9 MySQL tables and API response filtering for agent endpoints. MOD Phase 0 does not address relational data classification. |
| DATA-Q1: Data Classification (books-api) | 1 of 4 | ARA requires explicit `data-classification: public` and `contains-pii: false` tags on DynamoDB table to provide auditable proof that data is non-sensitive. Effort is minimal (hours) but is not part of MOD Phase 0. |

**Note:** DATA-Q1 has a `ARA extends MOD` relationship. MOD's DATA-Q1 (Unstructured Data Storage) and SEC-Q5 (Secrets Management) are complementary but not sufficient. ARA requires agent-specific data classification, PII redaction, and field-level access controls that go beyond what MOD evaluates.

## Section 3: MOD Readiness Gate

This section provides informational advisories when MOD category averages indicate foundational gaps
that will block ARA remediation efforts. These are not hard gates — they are sequencing guidance.

### ⚠️ Security Baseline Gap

**MOD SEC category average: 1.86 / 4.0**

ARA identity and access remediation (AUTH-Q1 through AUTH-Q7) will be blocked by MOD security baseline gaps.

**What this means:** The portfolio's security infrastructure (API authentication, centralized identity, secrets management,
audit logging) scores below the minimum 2.0 threshold for ARA remediation to be effective. Teams should prioritize MOD SEC
remediation before attempting ARA AUTH remediation.

**Per-service SEC scores:**
| Service | SEC Score | Status |
|---------|-----------|--------|
| unishop-monolith | 1.00 | ❌ Below threshold |
| aws-microservices | 1.71 | ❌ Below threshold |
| eks-saas-gitops | 1.86 | ❌ Below threshold |
| local-monolith | 2.00 | ✅ At threshold |
| books-api | 2.71 | ✅ Above threshold |

**Affected ARA findings:** AUTH-Q1 (Machine Identity), AUTH-Q2 (Scoped Permissions), AUTH-Q3 (Action-Level Auth),
AUTH-Q4 (Identity Propagation), AUTH-Q5 (Credential Management), AUTH-Q6 (Immutable Audit Logging), AUTH-Q7 (Identity Suspension)

**Sequencing guidance:** Complete MOD Phase 0 "Centralized Identity (Cognito)" and "CloudTrail & Audit Logging" items before beginning ARA AUTH remediation. These two Phase 0 items directly address SEC-Q3, SEC-Q4, and SEC-Q1 — the three foundational blockers dragging down the SEC category average.

### ⚠️ Operational Baseline Gap

**MOD OPS category average: 1.33 / 4.0**

ARA observability remediation (AUTH-Q6, OBS-Q1, OBS-Q2) will be blocked by MOD operational gaps.

**What this means:** The portfolio's operational infrastructure (distributed tracing, anomaly detection, deployment strategies)
scores below the minimum 2.0 threshold for ARA observability remediation to be effective. Teams should prioritize MOD OPS
remediation before attempting ARA observability remediation.

**Per-service OPS scores:**
| Service | OPS Score | Status |
|---------|-----------|--------|
| unishop-monolith | 1.00 | ❌ Below threshold |
| aws-microservices | 1.00 | ❌ Below threshold |
| eks-saas-gitops | 1.11 | ❌ Below threshold |
| local-monolith | 1.11 | ❌ Below threshold |
| books-api | 2.44 | ✅ Above threshold |

**Affected ARA findings:** AUTH-Q6 (Immutable Audit Logging), OBS-Q1 (Distributed Tracing), OBS-Q2 (Alerting)

**Sequencing guidance:** Complete MOD Phase 0 "Centralized Observability Platform" item before beginning ARA OBS remediation. This Phase 0 item addresses OPS-Q1, OPS-Q2, OPS-Q3, and OPS-Q4 — four of the foundational blockers that produce the 1.33 average.

**Note:** AUTH-Q6 (Immutable Audit Logging) appears in both advisories — it depends on both security audit logging infrastructure (SEC-Q1) and operational tracing infrastructure (OPS-Q1). Both MOD SEC and MOD OPS gaps must be addressed before AUTH-Q6 can be fully remediated.

## Section 4: Unified Remediation Sequence

This section merges the ARA remediation guidance and MOD Phase 0 roadmap into a single sequence.
Items that resolve findings in both analyses are marked as **dual-resolution** — completing them
delivers value for both modernization and agentic readiness simultaneously.

### Phase 0: Cross-Cutting Foundation (MOD + ARA)

These items come from the MOD Phase 0 roadmap. Each item shows which MOD findings AND which ARA findings
it resolves. Complete these first — they unblock ARA remediation.

#### 1. Centralized Identity (Cognito) ⭐ Dual-Resolution

**MOD Findings Resolved:**
- SEC-Q3: API Authentication — 3 services affected (unishop-monolith, aws-microservices, eks-saas-gitops)
- SEC-Q4: Centralized Identity — 3 services affected (local-monolith, unishop-monolith, aws-microservices)

**ARA Findings Resolved:**
- AUTH-Q1: Machine Identity (BLOCKER) — 4 services affected (unishop-monolith, aws-microservices, local-monolith, books-api)
- PORT-ARA-Q1: Centralized Identity Plane (BLOCKER) — portfolio-level

**ARA Findings Unblocked** (can be addressed after this item completes):
- AUTH-Q2: Scoped Permissions (RISK-SAFETY) — 5 services
- AUTH-Q3: Action-Level Authorization (RISK-SAFETY) — 5 services
- AUTH-Q4: Identity Propagation (RISK) — 5 services
- AUTH-Q7: Identity Suspension (RISK-SAFETY) — 5 services

**Dual-Resolution Impact:** This single item resolves 2 MOD foundational blockers and 2 ARA BLOCKERs (5 BLOCKER instances total) across all 5 services. **This is the highest-value item in the entire portfolio.**

---

#### 2. CloudTrail & Audit Logging ⭐ Dual-Resolution

**MOD Findings Resolved:**
- SEC-Q1: Audit Logging — 3 services affected (unishop-monolith, aws-microservices, eks-saas-gitops)

**ARA Findings Resolved:**
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY) — partially resolved for 5 services (CloudTrail provides the immutable audit foundation; per-service structured logging still needed)

**ARA Findings Unblocked:**
- PORT-ARA-Q2: Cross-Service Audit Correlation (RISK) — shared CloudTrail enables cross-service audit trail

**Dual-Resolution Impact:** This single item resolves 1 MOD foundational blocker and partially resolves 1 ARA RISK-SAFETY finding across 5 services.

---

#### 3. Centralized Observability Platform ⭐ Dual-Resolution

**MOD Findings Resolved:**
- OPS-Q1: Distributed Tracing — 4 services affected (local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops)
- OPS-Q2: SLO Definitions — 4 services affected
- OPS-Q3: Business Metrics — 5 services affected
- OPS-Q4: Anomaly Detection — 4 services affected

**ARA Findings Resolved:**
- OBS-Q1: Distributed Tracing (RISK-QUALITY) — 5 services affected
- OBS-Q2: Alerting (RISK-QUALITY) — 5 services affected

**ARA Findings Unblocked:**
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY) — tracing component now available (combined with CloudTrail from item 2)

**Dual-Resolution Impact:** This single item resolves 4 MOD foundational blockers and 2 ARA RISK-QUALITY findings across all 5 services.

---

#### 4. CI/CD Pipeline Templates ⭐ Dual-Resolution

**MOD Findings Resolved:**
- INF-Q11: CI/CD Automation — 3 services affected (local-monolith, unishop-monolith, aws-microservices)

**ARA Findings Resolved:**
- ENG-Q2: CI/CD + Contract Tests (RISK-QUALITY) — partially resolved for 5 services (pipeline infrastructure established; contract test stages still need OpenAPI specs)

**ARA Findings Unblocked:**
- ENG-Q3: Rollback Capability (RISK-QUALITY) — CI/CD enables automated deployment and rollback
- ENG-Q4: API Test Coverage (RISK-QUALITY) — CI/CD provides the pipeline to run tests

**Dual-Resolution Impact:** This single item resolves 1 MOD foundational blocker and partially resolves 1 ARA RISK-QUALITY finding across 5 services.

---

#### 5. API Versioning Standard ⭐ Dual-Resolution

**MOD Findings Resolved:**
- APP-Q5: API Versioning — 4 services affected (local-monolith, unishop-monolith, aws-microservices, books-api)

**ARA Findings Resolved:**
- API-Q2: Machine-Readable Spec (RISK-QUALITY) — 4 services affected (OpenAPI spec generation is part of this initiative)
- DISC-Q1: Schema Versioning (RISK-QUALITY) — 4 services affected (API versioning convention enables schema versioning)

**ARA Findings Unblocked:**
- API-Q3: Structured Errors (RISK-QUALITY) — OpenAPI specs enable standardized error schemas

**Dual-Resolution Impact:** This single item resolves 1 MOD foundational blocker and 2 ARA RISK-QUALITY findings across 4 services.

---

#### 6. Security Scanning Pipeline (MOD-Only)

**MOD Findings Resolved:**
- SEC-Q7: Application Security Pipeline — 4 services affected (local-monolith, unishop-monolith, aws-microservices, books-api)

**ARA Findings:** No direct ARA mapping. However, security scanning improves overall portfolio security posture which benefits agent integration safety.

---

#### 7. Tagging Standard (MOD-Only)

**MOD Findings Resolved:**
- OPS-Q9: Resource Tagging Governance — 3 services affected (unishop-monolith, aws-microservices, eks-saas-gitops)

**ARA Findings:** No direct ARA mapping.

---

#### 8. EventBridge Event Bus (MOD-Only)

**MOD Findings Resolved:**
- INF-Q4: Async Messaging and Streaming — 3 services affected (local-monolith, unishop-monolith, books-api)

**ARA Findings:** No direct ARA mapping. However, EventBridge provides the foundation for agent-triggered event-driven workflows.

---

### ARA-Specific Remediation (After Phase 0)

These ARA findings have no MOD co-requisite or require agent-specific work beyond what MOD Phase 0 provides.
Address these after MOD Phase 0 completes.

#### 1. Data Classification and PII Protection (DATA-Q1) — BLOCKER

**ARA Finding:** DATA-Q1: Sensitive Data Classification (BLOCKER) — 4 services affected (unishop-monolith, aws-microservices, local-monolith, books-api)
**Why Not Covered by MOD Phase 0:** MOD Phase 0 DATA-Q1 addresses unstructured data *storage* (S3 buckets), not data *classification*. ARA requires field-level PII classification, agent-specific redaction, and classification tags — capabilities that go beyond the MOD analysis scope.
**Remediation Action:**
1. Create portfolio-wide data classification policy (Public / Internal / Confidential / Restricted)
2. Tag books-api DynamoDB as `data-classification: public` (hours)
3. Classify and tag PII fields in unishop-monolith, aws-microservices, local-monolith (1–4 weeks each)
4. Implement API response filtering for agent endpoints
5. Deploy Amazon Macie for automated PII detection
**Estimated Effort:** Medium (policy: 1 week; per-service: hours to 8 weeks)
**Priority:** Critical — this is the remaining BLOCKER after MOD Phase 0

#### 2. Rate Limiting and Throttling (STATE-Q5) — RISK-SAFETY

**ARA Finding:** STATE-Q5: Rate Limiting (RISK-SAFETY) — 4 services affected
**Why Not Covered by MOD Phase 0:** MOD co-requisite INF-Q6 (API Entry Point) is classified as an Improvement Opportunity (avg 2.40), not a Foundational Blocker, so it is not explicitly in Phase 0. However, the "API Versioning Standard" Phase 0 item partially addresses this by establishing API Gateway patterns.
**Remediation Action:** Deploy API Gateway with usage plans and per-agent-key throttling. Add WAF rate-based rules to local-monolith's existing WAF.
**Estimated Effort:** Low–Medium (7–30 days per service)

#### 3. Compensation and Rollback (STATE-Q1) — RISK-SAFETY

**ARA Finding:** STATE-Q1: Compensation and Rollback (RISK-SAFETY) — 4 services affected
**Why Not Covered by MOD Phase 0:** No MOD co-requisite in the mapping table. This is an ARA-specific safety requirement for agent write operations.
**Remediation Action:** Document compensating transaction patterns. Implement saga patterns for aws-microservices checkout flow and local-monolith fulfillment workflow before expanding to write-enabled agent scope.
**Estimated Effort:** High (60–90 days per service)

#### 4. Data Residency and Sovereignty (DATA-Q2) — RISK-SAFETY

**ARA Finding:** DATA-Q2: Data Residency (RISK-SAFETY) — 4 services affected
**Why Not Covered by MOD Phase 0:** No MOD co-requisite in the mapping table. This is an ARA-specific requirement for agent data handling compliance.
**Remediation Action:** Document portfolio-wide data residency policy. Pin deployment regions for PII-containing services. Ensure agents use same-region Amazon Bedrock endpoints.
**Estimated Effort:** Low (1–2 weeks)

#### 5. PII Redaction in Logs (DATA-Q6) — RISK-SAFETY

**ARA Finding:** DATA-Q6: PII Redaction in Logs (RISK-SAFETY) — 4 services affected
**Why Not Covered by MOD Phase 0:** No MOD co-requisite in the mapping table. This is an ARA-specific safety requirement — agent interactions may increase log volume with PII exposure.
**Remediation Action:** Adopt portfolio-wide structured logging standard with field-level allowlists. Implement per-service log scrubbing (SLF4J patterns for Java, Lambda Powertools for Node.js, centralized error handler for PHP).
**Estimated Effort:** Low–Medium (14–30 days per service)

#### 6. Sandbox/Staging Environments (HITL-Q3) — RISK-QUALITY

**ARA Finding:** HITL-Q3: Sandbox/Staging Environment (RISK-QUALITY) — 4 services affected
**Why Not Covered by MOD Phase 0:** MOD co-requisite OPS-Q5 (Deployment Strategy) is a Foundational Blocker partially addressed by Phase 0 CI/CD pipeline work, but agent-specific staging environments with test data require additional effort.
**Remediation Action:** Create portfolio-wide staging environment strategy with agent test data scripts and documented agent testing processes for each service.
**Estimated Effort:** Medium (14–30 days per service)

## Section 5: Shared Findings Deduplication

These findings appear in both the portfolio ARA report and the portfolio MOD report.
They represent the same underlying gap viewed through different analysis lenses.
**Plan remediation once, not twice.**

### Shared Relationship Findings (Same Gap, Different Lens)

| # | ARA Finding | ARA Severity | MOD Finding | MOD Avg Score | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 1 | AUTH-Q5: Credential Management | RISK-QUALITY | SEC-Q5: Secrets Management | 2.40 | Shared | Migrate all secrets to AWS Secrets Manager with automated rotation; use External Secrets Operator on EKS |
| 2 | API-Q2: Machine-Readable Spec | RISK-QUALITY | APP-Q5: API Versioning | 1.00 | Shared | Generate OpenAPI 3.0 specs for all services with `/v1/` URL versioning convention |
| 3 | API-Q3: Structured Errors | RISK-QUALITY | APP-Q5: API Versioning + INF-Q6: API Entry Point | 1.00 / 2.40 | Shared | Define portfolio-wide error response schema and implement via API Gateway error mapping |
| 4 | OBS-Q1: Distributed Tracing | RISK-QUALITY | OPS-Q1: Distributed Tracing | 1.60 | Shared | Deploy ADOT Collector on EKS + enable X-Ray on all Lambda functions |
| 5 | OBS-Q2: Alerting | RISK-QUALITY | OPS-Q4: Anomaly Detection | 1.20 | Shared | Deploy CloudWatch alarms + Prometheus AlertManager + SNS integration |
| 6 | DISC-Q1: Schema Versioning | RISK-QUALITY | APP-Q5: API Versioning | 1.00 | Shared | Add `/v1/` prefix to all API paths + commit OpenAPI specs + breaking change detection in CI |
| 7 | ENG-Q1: Infra Governance | RISK-QUALITY | INF-Q10: IaC Coverage | 1.00* | Shared | Require IaC for all services; create Terraform for unishop-monolith; add AWS Config drift detection |

### MOD → ARA Prerequisite Findings (Both Sides Active)

These have a directional MOD → ARA relationship, but both the ARA finding and the MOD co-requisite are flagged as gaps in their respective reports — indicating the same underlying infrastructure deficiency.

| # | ARA Finding | ARA Severity | MOD Finding | MOD Avg Score | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 8 | AUTH-Q1: Machine Identity | BLOCKER | SEC-Q3: API Auth + SEC-Q4: Centralized Identity | 1.60 | MOD → ARA | Deploy shared Cognito User Pool with `client_credentials` grant |
| 9 | AUTH-Q2: Scoped Permissions | RISK-SAFETY | SEC-Q3: API Auth + SEC-Q4: Centralized Identity | 1.60 | MOD → ARA | Configure fine-grained OAuth2 scopes in centralized Cognito |
| 10 | AUTH-Q3: Action-Level Auth | RISK-SAFETY | SEC-Q3: API Auth + INF-Q6: API Entry Point | 1.60 / 2.40 | MOD → ARA | Add API Gateway authorizers with method-level restrictions |
| 11 | AUTH-Q6: Immutable Audit Logging | RISK-SAFETY | SEC-Q1: Audit Logging + OPS-Q1: Distributed Tracing | 1.40 / 1.60 | MOD → ARA | Deploy CloudTrail with S3 Object Lock + ADOT/X-Ray tracing |
| 12 | AUTH-Q7: Identity Suspension | RISK-SAFETY | SEC-Q4: Centralized Identity | 1.60 | MOD → ARA | Build suspension capability into shared Cognito (disable App Client) |
| 13 | ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY | INF-Q11: CI/CD Automation + OPS-Q6: Integration Testing | 1.60 / 1.40 | MOD → ARA | Create shared CI/CD pipeline templates with contract test stages |
| 14 | STATE-Q5: Rate Limiting | RISK-SAFETY | INF-Q6: API Entry Point | 2.40 | MOD → ARA | Deploy API Gateway with usage plans and per-agent throttling |
| 15 | HITL-Q3: Sandbox/Staging | RISK-QUALITY | OPS-Q5: Deployment Strategy | 1.80 | MOD → ARA | Implement progressive delivery + agent-testing staging environments |

*INF-Q10 gap is limited to unishop-monolith (score=1); other services have IaC.*

### Deduplication Summary

- **15 findings** appear in both analyses (7 Shared + 8 MOD → ARA with both sides active)
- **11 remediation items** can be consolidated (planned once instead of twice) — several ARA findings map to the same MOD co-requisite (e.g., AUTH-Q1, AUTH-Q2, AUTH-Q7 all map to SEC-Q3/SEC-Q4 → single Cognito deployment)
- **Estimated effort savings:** Teams avoid duplicating planning and execution for shared infrastructure gaps. The 5 dual-resolution Phase 0 items (Cognito, CloudTrail, Observability, CI/CD, API Versioning) each resolve findings in both reports — executing them once delivers double the value.

### What's NOT Shared (ARA-Only Findings)

The following ARA findings have no MOD counterpart and require independent remediation planning:

| ARA Finding | ARA Severity | Why No MOD Overlap |
|---|---|---|
| STATE-Q1: Compensation and Rollback | RISK-SAFETY | Agent-specific safety requirement for write operations — not in MOD scope |
| DATA-Q2: Data Residency | RISK-SAFETY | Agent data handling compliance — not in MOD scope |
| DATA-Q6: PII Redaction in Logs | RISK-SAFETY | Agent-specific log safety — not in MOD scope |
| DATA-Q1: Data Classification | BLOCKER | ARA extends MOD — MOD addresses storage, ARA requires classification (partially shared but remediation diverges) |

---

*End of Portfolio ARA–MOD Bridge Report*
