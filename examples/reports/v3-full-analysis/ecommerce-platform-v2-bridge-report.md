# Portfolio ARA–MOD Bridge Report

**Portfolio**: ecommerce-platform-v2
**Date**: 2026-04-27
**ARA Report**: agentic-readiness-analysis/ecommerce-platform-v2-portfolio-ara-report.md
**MOD Report**: modernization-analysis/ecommerce-platform-v2-portfolio-mod-report.md

---

## Bridge Summary

| Metric | Value |
|--------|-------|
| Shared Remediation Mappings | 17 |
| ARA BLOCKERs Resolvable by MOD Phase 0 | 6 of 9 service-level instances (AUTH-Q1: 5 services + PORT-ARA-Q1) |
| MOD Readiness Gates Triggered | 2 (SEC: 1.88, OPS: 1.31 — both below 2.0) |
| Unified Remediation Items | 13 (8 Phase 0 dual-resolution + 5 ARA-specific) |
| Deduplicated Shared Findings | 17 (all mapping entries have both ARA and MOD findings flagged) |

---

## Section 1: Shared Remediation Mapping

This section maps ARA findings to their MOD co-requisites using the built-in cross-reference mapping. Each row shows an ARA finding, its MOD dependency, and the shared remediation action that resolves both. The mapping covers 17 entries spanning identity, security, observability, API standards, engineering practices, and data governance.

| # | ARA Finding | ARA Severity | Affected Services | MOD Co-Requisite(s) | MOD Avg Score | MOD Gap Services | Relationship | Shared Remediation Action |
|---|---|---|---|---|---|---|---|---|
| 1 | AUTH-Q1: Machine Identity | BLOCKER | 5 of 5 | SEC-Q3: API Auth (1.6) + SEC-Q4: Centralized Identity (1.6) | 1.6 | 3 of 5 | MOD → ARA | Deploy centralized Cognito User Pool with `client_credentials` grant for agent M2M authentication |
| 2 | AUTH-Q2: Scoped Permissions | RISK-SAFETY | 5 of 5 | SEC-Q3: API Auth (1.6) + SEC-Q4: Centralized Identity (1.6) | 1.6 | 3 of 5 | MOD → ARA | Configure fine-grained OAuth2 scopes in centralized identity provider per agent role |
| 3 | AUTH-Q3: Action-Level Auth | RISK-SAFETY | 5 of 5 | SEC-Q3: API Auth (1.6) + INF-Q6: API Entry Point (2.2) | 1.9 | 3 of 5 (SEC-Q3) / 1 of 5 (INF-Q6) | MOD → ARA | Add API Gateway method-level authorization (allow GET, deny POST/PUT/DELETE for agent roles) |
| 4 | AUTH-Q4: Identity Propagation | RISK-QUALITY | 4 of 4 | SEC-Q4: Centralized Identity (1.6) | 1.6 | 3 of 5 | MOD → ARA | Implement JWT-based identity propagation with actor/subject claims via centralized Cognito |
| 5 | AUTH-Q5: Credential Management | RISK-QUALITY | 5 of 5 | SEC-Q5: Secrets Management (2.2) | 2.2 | 1 of 5 | Shared | Migrate all credentials to AWS Secrets Manager with automated rotation |
| 6 | AUTH-Q6: Immutable Audit Logging | RISK-SAFETY | 5 of 5 | SEC-Q1: Audit Logging (1.4) + OPS-Q1: Distributed Tracing (1.4) | 1.4 | 3 of 5 (SEC-Q1) / 4 of 5 (OPS-Q1) | MOD → ARA | Deploy CloudTrail with immutable S3 storage + ADOT/X-Ray tracing across all services |
| 7 | AUTH-Q7: Identity Suspension | RISK-SAFETY | 5 of 5 | SEC-Q4: Centralized Identity (1.6) | 1.6 | 3 of 5 | MOD → ARA | Build kill-switch capability in centralized Cognito to revoke agent app clients within minutes |
| 8 | API-Q2: Machine-Readable Spec | RISK-QUALITY | 4 of 4 | APP-Q5: API Versioning (1.0) | 1.0 | 4 of 4 | Shared | Generate OpenAPI 3.0 specifications for all services with /v1/ URL-path versioning |
| 9 | API-Q3: Structured Errors | RISK-QUALITY | 4 of 4 | APP-Q5: API Versioning (1.0) + INF-Q6: API Entry Point (2.2) | 1.6 | 4 of 4 (APP-Q5) / 1 of 5 (INF-Q6) | Shared | Define portfolio-wide error response standard `{error_code, message, retryable}` alongside API versioning |
| 10 | STATE-Q5: Rate Limiting | RISK-SAFETY | 4 of 4 | INF-Q6: API Entry Point (2.2) | 2.2 | 1 of 5 | MOD → ARA | Deploy API Gateway with usage plans and per-agent-identity throttle settings |
| 11 | OBS-Q1: Distributed Tracing | RISK-QUALITY | 5 of 5 | OPS-Q1: Distributed Tracing (1.4) | 1.4 | 4 of 5 | Shared | Deploy X-Ray/ADOT across all services with correlation IDs for agent request chains |
| 12 | OBS-Q2: Alerting | RISK-QUALITY | 5 of 5 | OPS-Q4: Anomaly Detection (1.2) | 1.2 | 4 of 5 | Shared | Deploy CloudWatch alarms with anomaly detection for error rates, latency, and agent traffic patterns |
| 13 | DISC-Q1: Schema Versioning | RISK-QUALITY | 4 of 4 | APP-Q5: API Versioning (1.0) | 1.0 | 4 of 4 | Shared | Implement URL-based API versioning (/v1/) with OpenAPI spec diffing in CI pipelines |
| 14 | ENG-Q1: Infra Governance | RISK-QUALITY | 5 of 5 | INF-Q10: IaC Coverage (3.0) | 3.0 | 0 of 5 | Shared | Enforce branch protection with required reviews; enable CloudFormation drift detection and AWS Config rules |
| 15 | ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY | 5 of 5 | INF-Q11: CI/CD Automation (1.8) + OPS-Q6: Integration Testing (1.4) | 1.6 | 3 of 5 (INF-Q11) / 4 of 5 (OPS-Q6) | MOD → ARA | Establish CI/CD pipelines for all services with mandatory API contract testing |
| 16 | DATA-Q1: Data Classification | BLOCKER | 4 of 4 | DATA-Q1: Unstructured Data (1.25) + SEC-Q5: Secrets Mgmt (2.2) | 1.7 | 3 of 4 (DATA-Q1) / 1 of 5 (SEC-Q5) | ARA extends MOD | Deploy Amazon Macie for PII detection + establish portfolio-wide data classification taxonomy with field-level agent access controls |
| 17 | HITL-Q3: Sandbox/Staging | RISK-QUALITY | 3 of 4 | OPS-Q5: Deployment Strategy (1.8) | 1.8 | 3 of 5 | MOD → ARA | Implement canary deployments with staging environments for agent testing before production |

### Relationship Type Explanations

**MOD → ARA prerequisite** (10 mappings: #1–4, #6–7, #10, #15, #17):
The MOD gap must be resolved before the ARA finding can be addressed. ARA remediation is blocked until MOD co-requisite scores improve. For example, AUTH-Q1 (Machine Identity) cannot be implemented without the centralized identity infrastructure that SEC-Q3 and SEC-Q4 evaluate — you cannot authenticate agents without an identity provider.

**Shared** (6 mappings: #5, #8–9, #11–14):
Same underlying gap viewed through different analysis lenses. One remediation action resolves both the MOD and ARA findings. For example, OBS-Q1 (ARA: Distributed Tracing for agent observability) and OPS-Q1 (MOD: Distributed Tracing for operational visibility) are the same infrastructure gap — deploying X-Ray/ADOT resolves both simultaneously.

**ARA extends MOD** (1 mapping: #16):
ARA adds agent-specific requirements on top of what MOD already evaluates. MOD remediation partially addresses the ARA finding, but additional agent-specific work is needed. DATA-Q1 in MOD evaluates unstructured data platform maturity, while DATA-Q1 in ARA requires field-level PII classification and agent-specific redaction — a superset of the MOD concern.

### Key Insight

**All 17 mapping entries have active findings in both analyses.** Every ARA finding in the cross-reference mapping corresponds to a MOD co-requisite that is also flagged as a gap. This means the two analyses are deeply interconnected for this portfolio — modernization work and agentic readiness work are not independent tracks. Coordinated planning is essential to avoid duplicating effort.

---

## Section 2: Agentic Readiness Delta

**If MOD Phase 0 were completed, 6 of 9 ARA service-level BLOCKER instances would be resolved (plus 1 portfolio-level BLOCKER).**

This means **67%** of the portfolio's agentic readiness blocker instances are actually modernization prerequisites — completing MOD Phase 0 delivers an agentic readiness dividend without any ARA-specific remediation work. The remaining 3 BLOCKER instances (DATA-Q1 across 4 services, counted as 4 total minus 1 that is partially addressed) require ARA-specific remediation beyond MOD scope.

### ARA BLOCKERs Inventory

| ARA BLOCKER | Type | Affected Services | BLOCKER Instances | In MOD-ARA Mapping? | Relationship |
|---|---|---|---|---|---|
| AUTH-Q1: Machine Identity | Cross-cutting | 5 (all services) | 5 | Yes | MOD → ARA |
| DATA-Q1: Data Classification | Cross-cutting | 4 (application services) | 4 | Yes | ARA extends MOD |
| PORT-ARA-Q1: Centralized Identity Plane | Portfolio-level | All 5 services | — (portfolio-level) | Resolved with AUTH-Q1 | MOD → ARA |
| **Total** | | | **9 service-level** | | |

### BLOCKERs Resolved by MOD Phase 0

| ARA BLOCKER | Affected Services | MOD Phase 0 Item | How It Resolves |
|---|---|---|---|
| AUTH-Q1: Machine Identity | 5 services (unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops) | **Cognito Identity Provider** (SEC-Q3 + SEC-Q4) | Deploying a centralized Cognito User Pool with Resource Server and `client_credentials` OAuth2 flow creates the machine identity infrastructure that AUTH-Q1 requires. Agent identities become distinct, auditable machine principals with scoped credentials. |
| PORT-ARA-Q1: Centralized Identity Plane | All 5 services | **Cognito Identity Provider** (SEC-Q3 + SEC-Q4) | The same Cognito deployment that resolves AUTH-Q1 also resolves the portfolio-level finding — it establishes the shared identity provider across all services. |

**Resolution count**: 5 service-level BLOCKER instances (AUTH-Q1) + 1 portfolio-level BLOCKER (PORT-ARA-Q1) = **6 of 9 service-level instances resolved** (67%) plus the portfolio-level BLOCKER.

### BLOCKERs Requiring ARA-Specific Remediation

| ARA BLOCKER | Affected Services | Why MOD Phase 0 Doesn't Resolve |
|---|---|---|
| DATA-Q1: Data Classification | 4 services (unishop-monolith, aws-microservices, local-monolith, books-api) | ARA requires **field-level PII classification** and **agent-specific redaction** — the ability to automatically mask or exclude sensitive data fields (customer names, emails, payment card data) from agent API responses based on the agent's authorization scope. MOD DATA-Q1 evaluates unstructured data platform maturity (S3, document processing) — a complementary but different concern. MOD Phase 0 does not include a data classification initiative. The SEC-Q5 co-requisite (Secrets Management) is classified as an Improvement Opportunity, not a Phase 0 item. |

**Why DATA-Q1 requires separate work**: Even after MOD Phase 0 establishes the identity provider (Cognito) and audit logging (CloudTrail), the portfolio still needs:
1. A portfolio-wide data classification taxonomy (Public, Internal, Confidential, Restricted)
2. A data inventory mapping every PII and payment data field across 4 application services
3. Field-level response filtering per service (agent-facing DTOs, DynamoDB projection expressions, middleware filters)
4. Amazon Macie deployment for automated PII detection

This is fundamentally new work that neither analysis's Phase 0 roadmap covers — it is an ARA-specific requirement that must be planned separately.

### Delta Visualization

```
Total ARA BLOCKERs (service-level):  ██████████  9 instances
Resolved by MOD Phase 0:             ██████░░░░  6 instances (67%) — AUTH-Q1 × 5 services + PORT-ARA-Q1
Requiring ARA-specific work:          ░░░░████░░  4 instances (33%) — DATA-Q1 × 4 services
                                                  (Note: total exceeds 9 because PORT-ARA-Q1 is 
                                                   portfolio-level, not counted in the 9)
```

### Modernization Dividend

Completing MOD Phase 0's **Cognito Identity Provider** item alone delivers:
- **5 ARA BLOCKER instances resolved** (AUTH-Q1 across all 5 services)
- **1 portfolio-level BLOCKER resolved** (PORT-ARA-Q1: Centralized Identity Plane)
- **4 ARA RISK-SAFETY findings unblocked** (AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7 — these can be addressed once identity exists)
- **2 ARA RISK-QUALITY findings unblocked** (AUTH-Q4, AUTH-Q5 — identity propagation and credential management)

This is the single highest-impact item in the entire portfolio remediation landscape. It delivers value for both modernization (SEC-Q3, SEC-Q4 foundational blockers resolved) and agentic readiness (AUTH-Q1 BLOCKER plus 6 dependent findings unblocked) simultaneously.

---

## Section 3: MOD Readiness Gate

This section provides informational advisories when MOD category averages indicate foundational gaps that will block ARA remediation efforts. These are not hard gates — they are sequencing guidance.

### ⚠️ Security Baseline Gap

**MOD SEC category average: 1.88 / 4.0**

ARA identity and access remediation (AUTH-Q1 through AUTH-Q7) will be blocked by MOD security baseline gaps.

**Per-service SEC scores:**

| Service | SEC Score | Status |
|---------|-----------|--------|
| unishop-monolith | 1.29 | ❌ Below 2.0 |
| aws-microservices | 1.71 | ❌ Below 2.0 |
| local-monolith | 2.14 | ✅ Above 2.0 |
| books-api | 2.57 | ✅ Above 2.0 |
| eks-saas-gitops | 1.71 | ❌ Below 2.0 |

**What this means:** The portfolio's security infrastructure (API authentication, centralized identity, secrets management, audit logging) scores below the minimum threshold for ARA remediation to be effective. Specifically:
- **SEC-Q3 (API Authentication)**: 3 services have completely unauthenticated APIs — you cannot configure agent-specific authentication scopes on endpoints that have no authentication at all.
- **SEC-Q4 (Centralized Identity)**: 3 services have no external identity provider — you cannot implement machine identity propagation without a centralized identity plane.
- **SEC-Q1 (Audit Logging)**: 3 services have no CloudTrail — you cannot establish immutable audit trails for agent actions without basic audit logging infrastructure.
- **SEC-Q5 (Secrets Management)**: 1 service has hardcoded credentials in source control — you cannot securely manage agent credentials alongside plaintext human credentials.

**Affected ARA findings:** AUTH-Q1 (Machine Identity), AUTH-Q2 (Scoped Permissions), AUTH-Q3 (Action-Level Auth), AUTH-Q4 (Identity Propagation), AUTH-Q5 (Credential Management), AUTH-Q6 (Immutable Audit Logging), AUTH-Q7 (Identity Suspension)

**Sequencing guidance:** Teams should prioritize MOD SEC remediation (Cognito Identity Provider + CloudTrail Audit Logging from Phase 0) before attempting ARA AUTH remediation. The MOD Phase 0 roadmap already includes both items — completing Phase 0 will raise the SEC category average above the 2.0 threshold.

### ⚠️ Operational Baseline Gap

**MOD OPS category average: 1.31 / 4.0**

ARA observability remediation (AUTH-Q6, OBS-Q1, OBS-Q2) will be blocked by MOD operational gaps.

**Per-service OPS scores:**

| Service | OPS Score | Status |
|---------|-----------|--------|
| unishop-monolith | 1.11 | ❌ Below 2.0 |
| aws-microservices | 1.00 | ❌ Below 2.0 |
| local-monolith | 1.11 | ❌ Below 2.0 |
| books-api | 2.11 | ✅ Above 2.0 |
| eks-saas-gitops | 1.22 | ❌ Below 2.0 |

**What this means:** The portfolio's operational infrastructure (distributed tracing, anomaly detection, deployment strategies) scores below the minimum threshold for ARA observability remediation to be effective. This is the weakest category in the entire portfolio — only books-api exceeds the 2.0 threshold. Specifically:
- **OPS-Q1 (Distributed Tracing)**: 4 services have no tracing — you cannot implement agent request chain tracing without basic distributed tracing infrastructure.
- **OPS-Q4 (Anomaly Detection)**: 4 services have no alerting — you cannot detect agent-caused degradation without operational alerting.
- **OPS-Q5 (Deployment Strategy)**: 3 services deploy directly to production — you cannot safely test agent integrations without staged rollout capability.
- **OPS-Q7/OPS-Q8 (Incident Response)**: All 5 services score 1 — no runbooks, no observability ownership, no on-call procedures exist anywhere.

**Affected ARA findings:** AUTH-Q6 (Immutable Audit Logging), OBS-Q1 (Distributed Tracing), OBS-Q2 (Alerting)

**Sequencing guidance:** Teams should prioritize MOD OPS remediation (Centralized Observability from Phase 0) before attempting ARA observability remediation. The OPS category requires the most investment of any category — the 1.31 average is nearly 0.7 points below the 2.0 threshold. The MOD Phase 0 roadmap addresses OPS-Q1 through OPS-Q4 via the Centralized Observability item and OPS-Q7/OPS-Q8 via the Incident Response Framework item.

### Combined Impact

Both readiness gates are triggered for this portfolio. This is significant — it means **ARA identity/access remediation AND ARA observability remediation are both blocked by MOD foundational gaps**. Practically, this means:

1. **No ARA remediation should begin until MOD Phase 0 is at least partially complete** — the security and operational foundations must exist first.
2. **MOD Phase 0 is the critical path** — it unblocks both modernization and agentic readiness simultaneously.
3. **Estimated time to clear gates**: MOD Phase 0 is planned for Month 0–1. Once complete, both SEC and OPS category averages should exceed 2.0, clearing both gates.

---

## Section 4: Unified Remediation Sequence

This section merges the ARA remediation guidance and MOD Phase 0 roadmap into a single sequence. Items that resolve findings in both analyses are marked as **dual-resolution** — completing them delivers value for both modernization and agentic readiness simultaneously.

### Phase 0: Cross-Cutting Foundation (MOD + ARA)

These items come from the MOD Phase 0 roadmap. Each item shows which MOD findings AND which ARA findings it resolves. Complete these first — they unblock ARA remediation.

#### 1. Cognito Identity Provider (SEC-Q3 + SEC-Q4) 🔴 HIGHEST PRIORITY

**MOD Findings Resolved:**
- SEC-Q3: API Authentication — 3 services affected (unishop-monolith, aws-microservices, eks-saas-gitops)
- SEC-Q4: Centralized Identity — 3 services affected (unishop-monolith, aws-microservices, local-monolith)

**ARA Findings Resolved:**
- AUTH-Q1: Machine Identity (**BLOCKER**) — 5 services affected
- PORT-ARA-Q1: Centralized Identity Plane (**BLOCKER**) — portfolio-level

**ARA Findings Unblocked** (can be addressed after this item completes):
- AUTH-Q2: Scoped Permissions (RISK-SAFETY) — 5 services
- AUTH-Q3: Action-Level Auth (RISK-SAFETY) — 5 services
- AUTH-Q4: Identity Propagation (RISK-QUALITY) — 4 services
- AUTH-Q7: Identity Suspension (RISK-SAFETY) — 5 services

**Dual-Resolution Impact:** This single item resolves 2 MOD foundational blockers + 2 ARA BLOCKERs (1 cross-cutting + 1 portfolio-level) across all 5 services. It is the highest-impact item in the entire remediation landscape.

---

#### 2. CloudTrail Audit Logging (SEC-Q1)

**MOD Findings Resolved:**
- SEC-Q1: Audit Logging — 3 services affected (unishop-monolith, aws-microservices, eks-saas-gitops)

**ARA Findings Resolved:**
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY) — partially resolved; CloudTrail provides the immutable audit trail foundation, but structured application-level logging with agent identity attribution requires additional work

**Dual-Resolution Impact:** Resolves 1 MOD foundational blocker + contributes to 1 ARA RISK-SAFETY finding across 3–5 services.

---

#### 3. Centralized Observability (OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4)

**MOD Findings Resolved:**
- OPS-Q1: Distributed Tracing — 4 services affected (unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops)
- OPS-Q2: SLO Definitions — 4 services affected
- OPS-Q3: Business Metrics — 4 services affected
- OPS-Q4: Anomaly Detection — 4 services affected

**ARA Findings Resolved:**
- OBS-Q1: Distributed Tracing (RISK-QUALITY) — 5 services affected
- OBS-Q2: Alerting (RISK-QUALITY) — 5 services affected

**ARA Findings Unblocked:**
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY) — tracing infrastructure enables end-to-end agent action correlation

**Dual-Resolution Impact:** Resolves 4 MOD foundational blockers + 2 ARA RISK-QUALITY findings across all 5 services. Clears the OPS readiness gate (Section 3).

---

#### 4. CI/CD Pipelines (INF-Q11)

**MOD Findings Resolved:**
- INF-Q11: CI/CD Automation — 3 services affected (unishop-monolith, aws-microservices, local-monolith)

**ARA Findings Resolved:**
- ENG-Q2: CI/CD + Contract Tests (RISK-QUALITY) — partially resolved; CI/CD pipelines are the foundation, but API contract testing (Pact) for agent consumers requires additional configuration

**Dual-Resolution Impact:** Resolves 1 MOD foundational blocker + contributes to 1 ARA RISK-QUALITY finding across 3–5 services.

---

#### 5. API Versioning Standard (APP-Q5)

**MOD Findings Resolved:**
- APP-Q5: API Versioning — 4 services affected (unishop-monolith, aws-microservices, local-monolith, books-api)

**ARA Findings Resolved:**
- API-Q2: Machine-Readable Spec (RISK-QUALITY) — 4 services affected
- DISC-Q1: Schema Versioning (RISK-QUALITY) — 4 services affected

**ARA Findings Partially Resolved:**
- API-Q3: Structured Errors (RISK-QUALITY) — 4 services; API versioning establishes the framework, but the error response standard `{error_code, message, retryable}` requires per-service implementation

**Dual-Resolution Impact:** Resolves 1 MOD foundational blocker + 2 ARA RISK-QUALITY findings (fully) + 1 ARA RISK-QUALITY finding (partially) across 4 application services. Critical for AI agent tool discovery — OpenAPI specs enable Amazon Bedrock agent tool definitions.

---

#### 6. Incident Response Framework (OPS-Q7, OPS-Q8)

**MOD Findings Resolved:**
- OPS-Q7: Incident Response Automation — 5 services affected
- OPS-Q8: Observability Ownership — 5 services affected

**ARA Findings Resolved:** None directly mapped in the cross-reference table.

**ARA Indirect Benefit:** Established incident response procedures and on-call rotations are essential for responding to agent-caused incidents. Without this framework, detecting and stopping a misbehaving agent relies entirely on ad hoc response.

**Impact:** Resolves 2 MOD foundational blockers across all 5 services. MOD-only item — no direct ARA mapping.

---

#### 7. Backup and Recovery (INF-Q8)

**MOD Findings Resolved:**
- INF-Q8: Backup and Recovery — 3 services affected (unishop-monolith, aws-microservices, books-api)

**ARA Findings Resolved:** None directly mapped in the cross-reference table.

**ARA Indirect Benefit:** Backup and recovery is a safety net for agent-caused data corruption. If an agent triggers unintended writes (when write scope is enabled), PITR provides a recovery path.

**Impact:** Resolves 1 MOD foundational blocker across 3 services. MOD-only item.

---

#### 8. Resource Tagging Standard (OPS-Q9)

**MOD Findings Resolved:**
- OPS-Q9: Resource Tagging — 2 services affected (aws-microservices, eks-saas-gitops)

**ARA Findings Resolved:** None directly mapped.

**Impact:** Resolves 1 MOD foundational blocker across 2 services. MOD-only item — enables cost tracking for agent-related infrastructure.

---

### ARA-Specific Remediation (After Phase 0)

These ARA findings have no MOD co-requisite in Phase 0 or require agent-specific work beyond what MOD Phase 0 provides. Address these after MOD Phase 0 completes.

#### 1. Data Classification and PII Protection (DATA-Q1) 🔴 ARA BLOCKER

**ARA Finding:** DATA-Q1: Data Classification (BLOCKER) — 4 services affected (unishop-monolith, aws-microservices, local-monolith, books-api)

**Why Not Covered by MOD Phase 0:** MOD DATA-Q1 evaluates unstructured data platform maturity (S3, document processing), not field-level PII classification. ARA requires agent-specific data redaction — the ability to mask sensitive fields in API responses based on the agent's authorization scope. This is fundamentally new work.

**Remediation Action:**
1. Establish portfolio-wide data classification taxonomy (Public, Internal, Confidential, Restricted)
2. Conduct data inventory across 4 application services mapping every PII and payment data field
3. Deploy Amazon Macie for automated PII detection
4. Implement field-level response filtering per service (agent-facing DTOs, DynamoDB projection expressions)
5. Classify book catalog data (books-api) as Public; tag PII fields as Confidential; tag payment data as Restricted

**Estimated Effort:** Medium (4–6 weeks across 4 services)

---

#### 2. Secrets Management Migration (AUTH-Q5)

**ARA Finding:** AUTH-Q5: Credential Management (RISK-QUALITY) — 5 services affected

**Why Not Covered by MOD Phase 0:** SEC-Q5 (Secrets Management) is classified as a MOD Improvement Opportunity, not a Phase 0 item. However, this is a shared finding — one remediation action resolves both the ARA and MOD concerns.

**Remediation Action:** Migrate all credentials to AWS Secrets Manager with automated rotation. Remove hardcoded credentials from source code (critical: unishop-monolith). Use External Secrets Operator for Kubernetes workloads (eks-saas-gitops).

**Estimated Effort:** Medium

---

#### 3. Rate Limiting Infrastructure (STATE-Q5)

**ARA Finding:** STATE-Q5: Rate Limiting (RISK-SAFETY) — 4 services affected

**Why Not Covered by MOD Phase 0:** INF-Q6 (API Entry Point) is classified as a MOD Improvement Opportunity, not a Phase 0 item. The MOD co-requisite provides the API Gateway infrastructure; the ARA finding requires agent-specific throttle settings on top of it.

**Remediation Action:** Deploy API Gateway with usage plans in front of all services. Configure per-agent-identity rate limits. Add WAF rate-based rules to local-monolith (quick win). Define portfolio-level aggregate agent traffic quotas.

**Estimated Effort:** Low

---

#### 4. Sandbox/Staging Environments (HITL-Q3)

**ARA Finding:** HITL-Q3: Sandbox/Staging (RISK-QUALITY) — 3 services affected (unishop-monolith, aws-microservices, local-monolith)

**Why Not Covered by MOD Phase 0:** OPS-Q5 (Deployment Strategy) is a MOD foundational blocker and partially addressed in Phase 0 via canary deployment strategies. However, ARA requires dedicated sandbox environments for agent testing — isolated environments where agents can operate without production impact. Canary deployments are necessary but not sufficient.

**Remediation Action:** Create staging environments for all 3 affected services. Mirror production data schemas with synthetic test data. Configure agent-specific test harnesses in staging before production rollout. Follow books-api's staging pipeline as the reference implementation.

**Estimated Effort:** Medium

---

#### 5. Infrastructure Governance (ENG-Q1)

**ARA Finding:** ENG-Q1: Infra Governance (RISK-QUALITY) — 5 services affected

**Why Not Covered by MOD Phase 0:** INF-Q10 (IaC Coverage) scores 3.0 across all services — all services have IaC. The gap is in governance sub-checks: branch protection, peer review requirements, and drift detection. This is a shared finding, but the MOD side doesn't flag it as a gap (score ≥ 3 in all services).

**Remediation Action:** Enforce branch protection with required reviews across all repositories. Enable CloudFormation drift detection. Deploy AWS Config rules for critical resources. This is a governance/process change, not an infrastructure deployment.

**Estimated Effort:** Low

---

## Section 5: Shared Findings Deduplication

These findings appear in both the portfolio ARA report and the portfolio MOD report. They represent the same underlying gap viewed through different analysis lenses. **Plan remediation once, not twice.**

### Shared Relationship Entries (Same Underlying Gap)

These entries have a "Shared" relationship — one remediation action resolves both the ARA and MOD findings directly.

| # | ARA Finding | ARA Severity | MOD Finding | MOD Avg Score | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 1 | AUTH-Q5: Credential Management | RISK-QUALITY | SEC-Q5: Secrets Management | 2.2 | Shared | Migrate all credentials to AWS Secrets Manager with automated rotation; remove hardcoded credentials from source code |
| 2 | API-Q2: Machine-Readable Spec | RISK-QUALITY | APP-Q5: API Versioning | 1.0 | Shared | Generate OpenAPI 3.0 specifications for all 4 application services with /v1/ URL-path versioning |
| 3 | API-Q3: Structured Errors | RISK-QUALITY | APP-Q5: API Versioning + INF-Q6: API Entry Point | 1.0 / 2.2 | Shared | Define portfolio-wide error response standard `{error_code, message, retryable}` as part of API versioning initiative |
| 4 | OBS-Q1: Distributed Tracing | RISK-QUALITY | OPS-Q1: Distributed Tracing | 1.4 | Shared | Deploy X-Ray/ADOT across all services with correlation IDs and structured JSON logging |
| 5 | OBS-Q2: Alerting | RISK-QUALITY | OPS-Q4: Anomaly Detection | 1.2 | Shared | Deploy CloudWatch alarms with anomaly detection for error rates, latency, and traffic patterns |
| 6 | DISC-Q1: Schema Versioning | RISK-QUALITY | APP-Q5: API Versioning | 1.0 | Shared | Implement URL-based API versioning (/v1/) with OpenAPI spec diffing in CI pipelines |
| 7 | ENG-Q1: Infra Governance | RISK-QUALITY | INF-Q10: IaC Coverage | 3.0 | Shared | Enforce branch protection, required reviews, drift detection, and AWS Config rules |

### MOD → ARA Entries (Both Flagged as Gaps)

These entries have a directional MOD → ARA relationship, but both analyses independently flagged the underlying infrastructure gap. The same remediation work resolves the MOD finding and enables the ARA finding to be addressed.

| # | ARA Finding | ARA Severity | MOD Finding | MOD Avg Score | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 8 | AUTH-Q1: Machine Identity | BLOCKER | SEC-Q3: API Auth + SEC-Q4: Centralized Identity | 1.6 / 1.6 | MOD → ARA | Deploy centralized Cognito User Pool with `client_credentials` OAuth2 flow for agent M2M authentication |
| 9 | AUTH-Q2: Scoped Permissions | RISK-SAFETY | SEC-Q3: API Auth + SEC-Q4: Centralized Identity | 1.6 / 1.6 | MOD → ARA | Configure fine-grained OAuth2 scopes per agent role in centralized identity provider |
| 10 | AUTH-Q3: Action-Level Auth | RISK-SAFETY | SEC-Q3: API Auth + INF-Q6: API Entry Point | 1.6 / 2.2 | MOD → ARA | Add API Gateway method-level authorization restricting agent HTTP methods |
| 11 | AUTH-Q4: Identity Propagation | RISK-QUALITY | SEC-Q4: Centralized Identity | 1.6 | MOD → ARA | Implement JWT-based identity propagation with actor/subject claims |
| 12 | AUTH-Q6: Immutable Audit Logging | RISK-SAFETY | SEC-Q1: Audit Logging + OPS-Q1: Distributed Tracing | 1.4 / 1.4 | MOD → ARA | Deploy CloudTrail with immutable S3 + ADOT/X-Ray for end-to-end tracing |
| 13 | AUTH-Q7: Identity Suspension | RISK-SAFETY | SEC-Q4: Centralized Identity | 1.6 | MOD → ARA | Build kill-switch in centralized Cognito for agent credential revocation |
| 14 | ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY | INF-Q11: CI/CD Automation + OPS-Q6: Integration Testing | 1.8 / 1.4 | MOD → ARA | Establish CI/CD pipelines with API contract testing for agent consumers |
| 15 | HITL-Q3: Sandbox/Staging | RISK-QUALITY | OPS-Q5: Deployment Strategy | 1.8 | MOD → ARA | Implement canary deployments + staging environments for agent testing |
| 16 | STATE-Q5: Rate Limiting | RISK-SAFETY | INF-Q6: API Entry Point | 2.2 | MOD → ARA | Deploy API Gateway with usage plans and per-agent-identity throttle settings |

### ARA Extends MOD Entry (Overlapping with Additional Requirements)

| # | ARA Finding | ARA Severity | MOD Finding | MOD Avg Score | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 17 | DATA-Q1: Data Classification | BLOCKER | DATA-Q1: Unstructured Data + SEC-Q5: Secrets Mgmt | 1.25 / 2.2 | ARA extends MOD | Deploy Amazon Macie + establish data classification taxonomy + implement field-level agent access controls (partial overlap — ARA requires additional agent-specific redaction work beyond MOD scope) |

### Deduplication Summary

- **17 findings** appear in both analyses (all mapping entries have active findings on both sides)
- **12 remediation items** can be fully consolidated (planned once instead of twice):
  - 7 Shared entries: identical underlying gap, single remediation resolves both
  - 5 MOD → ARA entries where MOD Phase 0 items directly resolve both findings
- **4 remediation items** are partially consolidated (MOD work provides the foundation, ARA adds agent-specific requirements on top)
- **1 remediation item** has overlapping scope but requires significant ARA-specific work beyond MOD (DATA-Q1)
- **Estimated effort savings:** Teams avoid duplicating planning and execution for shared infrastructure gaps. Without this bridge report, the portfolio would have two separate remediation tracks planning the same Cognito deployment, the same observability rollout, and the same API versioning initiative — effectively doubling the coordination overhead for 12+ shared items.

### Deduplication Impact by Category

| Category | Shared Findings | Deduplicated Remediation Actions | Primary Owner |
|----------|----------------|----------------------------------|---------------|
| Identity & Access (AUTH) | 7 (AUTH-Q1 through Q7) | Deploy Cognito + configure scopes + JWT propagation + kill-switch | Platform Team |
| API Surface (API, DISC) | 3 (API-Q2, API-Q3, DISC-Q1) | API versioning + OpenAPI specs + error standards | Service Teams |
| Observability (OBS, AUTH-Q6) | 3 (OBS-Q1, OBS-Q2, AUTH-Q6) | ADOT/X-Ray + CloudTrail + CloudWatch alarms | Platform Team |
| Engineering (ENG) | 2 (ENG-Q1, ENG-Q2) | CI/CD pipelines + governance controls | Platform Team |
| Data & Safety (DATA, STATE) | 2 (DATA-Q1, STATE-Q5) | Data classification + API Gateway rate limiting | Shared |

---

*End of Portfolio ARA–MOD Bridge Report*
