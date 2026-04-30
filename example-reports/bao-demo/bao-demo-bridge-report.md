# Portfolio ARA–MOD Bridge Report

**Portfolio**: bao-demo
**Date**: 2026-04-28
**ARA Report**: portfolio-ara-report.md
**MOD Report**: portfolio-mod-report.md
**BAO Report**: example-reports/bao-demo/bpmn-opportunity-assessment/bao-demo-portfolio-bao-report.md

---

## Bridge Summary

| Metric | Value |
|--------|-------|
| Shared Remediation Mappings | 17 |
| ARA BLOCKERs Resolvable by MOD Phase 0 | 0 of 12 (0%) |
| MOD Readiness Gates Triggered | 2 (SEC and OPS) |
| Unified Remediation Items | 13 (6 Phase 0 + 7 ARA-specific) |
| Deduplicated Shared Findings | 17 |
| BPMN Agent Opportunities (Ready / Blocked / Unassessed) | 0 / 64 / 0 |

---

## Section 1: Shared Remediation Mapping

This section maps ARA findings to their MOD co-requisites using the built-in cross-reference mapping.
Each row shows an ARA finding, its MOD dependency, and the shared remediation action that resolves both.

| # | ARA Finding | ARA Severity | Affected Services | MOD Co-Requisite(s) | MOD Avg Score | MOD Gap Services | Relationship | Shared Remediation Action |
|---|---|---|---|---|---|---|---|---|
| 1 | AUTH-Q1: Machine Identity | BLOCKER | 4 of 5 | SEC-Q3: API Auth (avg 1.20) + SEC-Q4: Centralized Identity (avg 1.00) | 1.10 | 4 + 5 | MOD → ARA | Deploy centralized identity provider (Amazon Cognito) with OAuth2 client_credentials grant for per-agent machine identity |
| 2 | AUTH-Q2: Scoped Permissions | RISK-SAFETY | 5 of 5 | SEC-Q3: API Auth (avg 1.20) + SEC-Q4: Centralized Identity (avg 1.00) | 1.10 | 4 + 5 | MOD → ARA | Configure fine-grained OAuth2 scopes in centralized identity provider with per-agent RBAC roles |
| 3 | AUTH-Q3: Action-Level Auth | RISK-SAFETY | 5 of 5 | SEC-Q3: API Auth (avg 1.20) + INF-Q6: API Entry Point (avg 1.00) | 1.10 | 4 + 5 | MOD → ARA | Implement API Gateway authorizers with method-level access control per agent identity |
| 4 | AUTH-Q4: Identity Propagation | RISK-QUALITY | 2 of 5 | SEC-Q4: Centralized Identity (avg 1.00) | 1.00 | 5 | MOD → ARA | Configure JWT token propagation through centralized IdP across service boundaries |
| 5 | AUTH-Q5: Credential Management | RISK-SAFETY | 5 of 5 | SEC-Q5: Secrets Management (avg 1.40) | 1.40 | 4 | Shared | Migrate all credentials to AWS Secrets Manager with automated rotation; eliminate hardcoded secrets |
| 6 | AUTH-Q6: Immutable Audit Logging | RISK-SAFETY | 5 of 5 | SEC-Q1: Audit Logging (avg 1.00) + OPS-Q1: Distributed Tracing (avg 1.00) | 1.00 | 5 + 5 | MOD → ARA | Deploy centralized immutable log aggregation (CloudWatch Logs with retention lock + S3 Object Lock) with OpenTelemetry correlation |
| 7 | AUTH-Q7: Identity Suspension | RISK-SAFETY | 5 of 5 | SEC-Q4: Centralized Identity (avg 1.00) | 1.00 | 5 | MOD → ARA | Implement centralized agent identity registry in Cognito with portfolio-wide suspension capability |
| 8 | API-Q2: Machine-Readable Spec | RISK-QUALITY | 5 of 5 | APP-Q5: API Versioning (avg 1.20) | 1.20 | 4 | Shared | Standardize on OpenAPI 3.0+ specifications co-located with each service; implement API versioning standard |
| 9 | API-Q3: Structured Errors | RISK-QUALITY | 5 of 5 | APP-Q5: API Versioning (avg 1.20) + INF-Q6: API Entry Point (avg 1.00) | 1.10 | 4 + 5 | Shared | Define portfolio-wide structured error response format with API Gateway error transformation |
| 10 | STATE-Q5: Rate Limiting | RISK-SAFETY | 5 of 5 | INF-Q6: API Entry Point (avg 1.00) | 1.00 | 5 | MOD → ARA | Deploy shared API Gateway with per-agent usage plans and rate limiting policies |
| 11 | OBS-Q1: Distributed Tracing | RISK-QUALITY | 5 of 5 | OPS-Q1: Distributed Tracing (avg 1.00) | 1.00 | 5 | Shared | Deploy OpenTelemetry Java agent across all services with X-Ray as trace exporter |
| 12 | OBS-Q2: Alerting | RISK-QUALITY | 5 of 5 | OPS-Q4: Anomaly Detection (avg 1.00) | 1.00 | 5 | Shared | Configure CloudWatch alarms with anomaly detection on error rates and latency for all services |
| 13 | DISC-Q1: Schema Versioning | RISK-QUALITY | 5 of 5 | APP-Q5: API Versioning (avg 1.20) | 1.20 | 4 | Shared | Implement API versioning standard with consumer-driven contract testing (Pact) |
| 14 | ENG-Q1: Infra Governance | RISK-QUALITY | 5 of 5 | INF-Q10: IaC Coverage (avg 1.00) | 1.00 | 5 | Shared | Adopt single IaC tool (CDK for Java teams) with shared infrastructure repository and reusable modules |
| 15 | ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY | 5 of 5 | INF-Q11: CI/CD Automation (avg 1.80) + OPS-Q6: Integration Testing (avg 2.00) | 1.90 | 3 + 1 | MOD → ARA | Create shared GitHub Actions CI/CD pipeline template with build, test, security scan, and API contract testing stages |
| 16 | DATA-Q1: Data Classification | BLOCKER | 5 of 5 | DATA-Q1: Unstructured Data (avg 1.00) + SEC-Q5: Secrets Mgmt (avg 1.40) | 1.20 | 5 + 4 | ARA extends MOD | Data platform modernization (S3 for unstructured data, Secrets Manager for credentials) + ARA-specific field-level PII classification taxonomy and agent redaction rules |
| 17 | HITL-Q3: Sandbox/Staging | RISK-QUALITY | 5 of 5 | OPS-Q5: Deployment Strategy (avg 1.00) | 1.00 | 5 | MOD → ARA | Implement blue/green deployments with CodeDeploy + staging environments via Docker Compose |

### Relationship Narrative

**MOD → ARA prerequisite (entries 1–4, 6–7, 10, 15, 17):** The MOD gap must be resolved before the ARA finding can be addressed. ARA remediation is blocked until MOD co-requisite scores improve. For this portfolio, 9 of 17 mapping entries have this relationship — the modernization infrastructure is a hard prerequisite for agentic readiness.

**Shared (entries 5, 8–9, 11–14):** Same underlying gap viewed through different lenses. One remediation action resolves both the MOD and ARA findings. For this portfolio, 7 of 17 mapping entries are shared findings — these represent the strongest deduplication opportunities where teams should plan remediation once, not twice.

**ARA extends MOD (entry 16):** ARA adds agent-specific requirements on top of what MOD evaluates. MOD remediation partially addresses the ARA finding, but additional agent-specific work is needed. DATA-Q1 is the sole entry with this relationship — MOD addresses unstructured data storage (S3) while ARA requires field-level data classification and agent-specific redaction, which is fundamentally different work.

---

## Section 2: Agentic Readiness Delta

**If MOD Phase 0 were completed, 0 of 12 ARA BLOCKERs would be fully resolved (0%).**

This means none of the portfolio's agentic readiness blockers are directly resolvable by MOD Phase 0 alone. However, MOD Phase 0 delivers **partial progress** on 5 DATA-Q1 BLOCKER instances through secrets remediation (SEC-Q5) and establishes infrastructure foundations that **unblock** subsequent ARA remediation.

> **Why 0%?** The MOD Phase 0 roadmap focuses on infrastructure foundations (IaC, CI/CD, networking, observability, secrets, security scanning). The ARA BLOCKERs require **identity infrastructure** (SEC-Q3 + SEC-Q4 → AUTH-Q1), **data governance** (DATA-Q1), and **API surface development** (API-Q1) — none of which are fully addressed by the Phase 0 items. Identity federation (SEC-Q3/SEC-Q4) is scheduled for MOD Phase 3, not Phase 0.

### ARA BLOCKERs Analysis

| ARA BLOCKER | Finding | Affected Services | Instances | MOD Mapping | MOD Phase 0 Coverage | Resolution Status |
|---|---|---|---|---|---|---|
| AUTH-Q1 | Machine Identity Authentication | camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | 4 | SEC-Q3 + SEC-Q4 (MOD → ARA) | ❌ Not in Phase 0 — SEC-Q3/SEC-Q4 are in Phase 3 (Identity Federation) | Not resolved |
| DATA-Q1 | Sensitive Data Classification | camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | 5 | DATA-Q1 + SEC-Q5 (ARA extends MOD) | ⚠️ Partially — SEC-Q5 (Secrets Remediation) IS in Phase 0, but ARA requires field-level PII classification beyond MOD scope | Partially addressed |
| API-Q1 | Documented API Interface | camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite | 3 | No MOD co-requisite in mapping | ❌ Not mapped — ARA-specific finding | Not resolved |
| **Total** | | | **12** | | | **0 fully resolved** |

### BLOCKERs Resolved by MOD Phase 0

No ARA BLOCKERs are fully resolved by MOD Phase 0. The three BLOCKER types require work beyond what Phase 0 provides:

- **AUTH-Q1 (4 instances)**: MOD co-requisites SEC-Q3 (API Authentication) and SEC-Q4 (Centralized Identity) are scheduled for **MOD Phase 3** (Identity Federation — Amazon Cognito integration), not Phase 0. Phase 0 establishes security pipeline (SEC-Q7) and secrets management (SEC-Q5), but not the centralized identity provider needed for machine identity.
- **DATA-Q1 (5 instances)**: MOD Phase 0 includes Secrets Remediation (SEC-Q5), which addresses one of the two MOD co-requisites. However, the ARA extends MOD relationship means ARA requires field-level PII classification, data dictionaries, and agent-specific redaction — work that goes fundamentally beyond MOD's unstructured data storage (DATA-Q1) scope.
- **API-Q1 (3 instances)**: No MOD co-requisite exists in the mapping table. This is a pure ARA finding requiring per-service API surface development (REST API layers for Zeebe workers, business facades for generic engine APIs, read-only APIs for data archives).

### BLOCKERs Requiring ARA-Specific Remediation

| ARA BLOCKER | Affected Services | Why MOD Phase 0 Doesn't Resolve | Required ARA-Specific Work |
|---|---|---|---|
| AUTH-Q1: Machine Identity | 4 services | SEC-Q3 (API Auth) and SEC-Q4 (Centralized Identity) are in MOD Phase 3, not Phase 0. Phase 0 builds infrastructure but not identity. | Deploy centralized identity provider (Cognito) with per-agent OAuth2 client credentials. Can be accelerated by pulling SEC-Q3/SEC-Q4 into Phase 0. |
| DATA-Q1: Data Classification | 5 services | SEC-Q5 (Secrets Remediation) in Phase 0 addresses credential exposure but not data classification. ARA requires field-level PII tags, data dictionaries, and classification-based access controls. | Establish portfolio-wide data classification taxonomy (Public, Internal, Confidential, Restricted). Inventory all data fields across 5 services. Apply field-level classification metadata. |
| API-Q1: Documented API Interface | 3 services | No MOD co-requisite exists. API-Q1 is architecturally specific — 2 services have no API surface at all (Zeebe worker, static archive), 1 has only generic engine API. | Per-service API development: REST wrappers for Zeebe operations, business facade APIs abstracting engine internals, read-only APIs over reference data. |

### Modernization Dividend: Indirect Benefits

While MOD Phase 0 resolves 0 BLOCKERs directly, it delivers significant **indirect benefits** for ARA remediation:

1. **IaC Foundation (INF-Q10)** → Enables reproducible deployment of identity providers, API Gateways, and data classification tooling
2. **CI/CD Template (INF-Q11)** → Enables automated testing of ARA remediation (contract tests, security scans)
3. **Observability Platform (OPS-Q1)** → Enables audit logging infrastructure needed for AUTH-Q6 remediation
4. **Secrets Remediation (SEC-Q5)** → Directly addresses AUTH-Q5 and partially addresses DATA-Q1
5. **Network Architecture (INF-Q5)** → Provides VPC/subnet foundation for deploying identity providers and API Gateways

**Recommendation**: Consider pulling SEC-Q3 (API Authentication) and SEC-Q4 (Centralized Identity) from Phase 3 into Phase 0. This would resolve AUTH-Q1 (4 BLOCKER instances) during the foundation phase, increasing the agentic readiness delta from 0% to 33% (4 of 12 BLOCKERs).

---

## Section 3: MOD Readiness Gate

This section provides informational advisories when MOD category averages indicate foundational gaps
that will block ARA remediation efforts. These are not hard gates — they are sequencing guidance.

### ⚠️ Security Baseline Gap

**MOD SEC category average: 1.17 / 4.0**

ARA identity and access remediation (AUTH-Q1 through AUTH-Q7) will be blocked by MOD security baseline gaps.

**What this means:** The portfolio's security infrastructure scores well below the 2.0 minimum threshold for ARA remediation to be effective. Every security-related MOD question is a foundational blocker:

| MOD Security Question | Portfolio Avg | Gap Services | Status |
|---|---|---|---|
| SEC-Q1: Audit Logging | 1.00 | 5 of 5 | All services at minimum |
| SEC-Q2: Encryption at Rest | 1.00 | 5 of 5 | All services at minimum |
| SEC-Q3: API Authentication | 1.20 | 4 of 5 | Only camunda-bpm-examples scores 2 |
| SEC-Q4: Centralized Identity | 1.00 | 5 of 5 | All services at minimum |
| SEC-Q5: Secrets Management | 1.40 | 4 of 5 | Only bpmn-miwg-test-suite scores 3 |
| SEC-Q6: Compute Hardening | 1.00 | 5 of 5 | All services at minimum |
| SEC-Q7: Security Pipeline | 1.00 | 5 of 5 | All services at minimum |

**Affected ARA findings:** AUTH-Q1 (Machine Identity — BLOCKER), AUTH-Q2 (Scoped Permissions), AUTH-Q3 (Action-Level Auth), AUTH-Q4 (Identity Propagation), AUTH-Q5 (Credential Management), AUTH-Q6 (Immutable Audit Logging), AUTH-Q7 (Identity Suspension)

**Sequencing guidance:** Teams should prioritize MOD SEC remediation before attempting ARA AUTH remediation. Specifically:
1. Complete SEC-Q5 (Secrets Remediation) in Phase 0 — this unblocks AUTH-Q5
2. Deploy SEC-Q3 + SEC-Q4 (API Auth + Centralized Identity) — this unblocks AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q7
3. Deploy SEC-Q1 (Audit Logging) — this unblocks AUTH-Q6

### ⚠️ Operational Baseline Gap

**MOD OPS category average: 1.13 / 4.0**

ARA observability remediation (AUTH-Q6, OBS-Q1, OBS-Q2) will be blocked by MOD operational gaps.

**What this means:** The portfolio's operational infrastructure scores at near-minimum levels. Every OPS question is a foundational blocker:

| MOD Operations Question | Portfolio Avg | Gap Services | Status |
|---|---|---|---|
| OPS-Q1: Distributed Tracing | 1.00 | 5 of 5 | All services at minimum |
| OPS-Q2: SLO Definitions | 1.00 | 5 of 5 | All services at minimum |
| OPS-Q3: Business Metrics | 1.00 | 5 of 5 | All services at minimum |
| OPS-Q4: Anomaly Detection | 1.00 | 5 of 5 | All services at minimum |
| OPS-Q5: Deployment Strategy | 1.00 | 5 of 5 | All services at minimum |
| OPS-Q6: Integration Testing | 2.00 | 1 of 5 | Most services near threshold |
| OPS-Q7: Incident Response | 1.00 | 5 of 5 | All services at minimum |
| OPS-Q8: Observability Ownership | 1.00 | 5 of 5 | All services at minimum |
| OPS-Q9: Resource Tagging | 1.00 | 5 of 5 | All services at minimum |

**Affected ARA findings:** AUTH-Q6 (Immutable Audit Logging), OBS-Q1 (Distributed Tracing), OBS-Q2 (Alerting)

**Sequencing guidance:** Teams should prioritize MOD OPS remediation before attempting ARA observability remediation. Specifically:
1. Deploy OPS-Q1 (Observability Platform) in Phase 0 — this unblocks OBS-Q1 and partially unblocks AUTH-Q6
2. Configure OPS-Q4 (Anomaly Detection/Alerting) — this unblocks OBS-Q2
3. Implement OPS-Q5 (Deployment Strategy) — this unblocks HITL-Q3

### Combined Impact

Both MOD readiness gates are triggered, affecting a total of **10 unique ARA findings** (AUTH-Q1 through AUTH-Q7, OBS-Q1, OBS-Q2, HITL-Q3). AUTH-Q6 appears in both gates (requires both SEC audit logging and OPS distributed tracing).

This means **the majority of ARA remediation cannot proceed** until MOD security and operations baselines are established. The recommended sequencing is:
1. **MOD Phase 0** → Establish infrastructure, CI/CD, secrets, observability, security pipeline
2. **MOD SEC-Q3/SEC-Q4 acceleration** → Pull identity infrastructure from Phase 3 to Phase 0/1
3. **ARA BLOCKER remediation** → Address AUTH-Q1, DATA-Q1, API-Q1 with MOD foundations in place
4. **ARA RISK remediation** → Address remaining RISKs with full MOD infrastructure available

---

## Section 4: Unified Remediation Sequence

This section merges the ARA remediation guidance and MOD Phase 0 roadmap into a single sequence.
Items that resolve findings in both assessments are marked as **dual-resolution** — completing them
delivers value for both modernization and agentic readiness simultaneously.

### Phase 0: Cross-Cutting Foundation (MOD + ARA)

These items come from the MOD Phase 0 roadmap. Each item shows which MOD findings AND which ARA findings
it resolves. Complete these first — they unblock ARA remediation.

#### 1. Secrets Remediation (SEC-Q5) — 🔄 Dual-Resolution

**MOD Findings Resolved:**
- SEC-Q5: Secrets Management — 4 services affected (camunda-invoice, camunda8-order-process, camunda-rest-service, camunda-bpm-examples)

**ARA Findings Resolved:**
- AUTH-Q5: Credential Management (RISK-SAFETY) — 5 services affected (Shared relationship: same finding, different lens)

**ARA Findings Unblocked** (can be addressed after this item completes):
- DATA-Q1: Data Classification (BLOCKER) — partially unblocked (SEC-Q5 is one of two MOD co-requisites)

**Dual-Resolution Impact:** This single item resolves 1 MOD finding and 1 ARA finding across 5 services. **Immediate priority** due to hardcoded credentials in 4 services committed to version control.

---

#### 2. IaC Foundation (INF-Q10) — 🔄 Dual-Resolution

**MOD Findings Resolved:**
- INF-Q10: Infrastructure as Code Coverage — 5 services affected (0% IaC coverage portfolio-wide)

**ARA Findings Resolved:**
- ENG-Q1: Infra Governance (RISK-QUALITY) — 5 services affected (Shared relationship: same finding, different lens)

**ARA Findings Unblocked** (can be addressed after this item completes):
- All subsequent infrastructure deployments (identity providers, API Gateways, databases, observability) depend on IaC foundation

**Dual-Resolution Impact:** This single item resolves 1 MOD finding and 1 ARA finding across 5 services. **Foundation enabler** — this is the #1 prerequisite for all other modernization and ARA remediation work.

---

#### 3. CI/CD Template (INF-Q11) — 🔄 Dual-Resolution

**MOD Findings Resolved:**
- INF-Q11: CI/CD Automation — 3 services affected (camunda8-order-process, camunda-rest-service, camunda-bpm-examples have zero CI/CD)

**ARA Findings Resolved:**
- ENG-Q2: CI/CD + Contract Tests (RISK-QUALITY) — 5 services affected (MOD → ARA: MOD is prerequisite for API contract testing)

**ARA Findings Unblocked** (can be addressed after this item completes):
- Automated security scanning, API contract testing, and deployment automation for all ARA remediation

**Dual-Resolution Impact:** This single item resolves 1 MOD finding and 1 ARA finding across 5 services. Creates the shared GitHub Actions pipeline template that accelerates all subsequent work.

---

#### 4. Network Architecture (INF-Q5) — MOD Only

**MOD Findings Resolved:**
- INF-Q5: Network Security — 5 services affected (no VPC, subnet, or security group configuration exists)

**ARA Findings:** No direct ARA mapping in the cross-reference table.

**ARA Findings Unblocked:** Provides VPC/subnet foundation required for deploying API Gateways (needed for STATE-Q5: Rate Limiting and AUTH-Q3: Action-Level Auth).

**Impact:** MOD-only item, but it enables ARA remediation infrastructure. No dual-resolution.

---

#### 5. Security Pipeline (SEC-Q7) — MOD Only

**MOD Findings Resolved:**
- SEC-Q7: Application Security Pipeline — 5 services affected (zero SAST, DAST, or dependency scanning)

**ARA Findings:** No direct ARA mapping in the cross-reference table.

**ARA Findings Unblocked:** Security scanning validates ARA remediation code quality and catches vulnerabilities in new API surfaces (API-Q1) and identity integrations (AUTH-Q1).

**Impact:** MOD-only item. Adds Dependabot to all 5 repositories and OWASP dependency-check to Maven builds.

---

#### 6. Observability Platform (OPS-Q1) — 🔄 Dual-Resolution

**MOD Findings Resolved:**
- OPS-Q1: Distributed Tracing — 5 services affected (zero tracing across entire portfolio)

**ARA Findings Resolved:**
- OBS-Q1: Distributed Tracing (RISK-QUALITY) — 5 services affected (Shared relationship: same finding)

**ARA Findings Unblocked** (can be addressed after this item completes):
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY) — partially unblocked (OPS-Q1 is one of two MOD co-requisites)
- OBS-Q2: Alerting (RISK-QUALITY) — anomaly detection can build on the observability platform

**Dual-Resolution Impact:** This single item resolves 1 MOD finding and 1 ARA finding across 5 services. Deploys OpenTelemetry Collector with X-Ray and CloudWatch as backends.

---

### Phase 0 Summary

| # | Foundation Item | Dual-Resolution? | MOD Findings | ARA Findings | Services |
|---|---|---|---|---|---|
| 1 | Secrets Remediation (SEC-Q5) | ✅ Yes | 1 | 1 (AUTH-Q5) | 5 |
| 2 | IaC Foundation (INF-Q10) | ✅ Yes | 1 | 1 (ENG-Q1) | 5 |
| 3 | CI/CD Template (INF-Q11) | ✅ Yes | 1 | 1 (ENG-Q2) | 5 |
| 4 | Network Architecture (INF-Q5) | ❌ No | 1 | 0 | 5 |
| 5 | Security Pipeline (SEC-Q7) | ❌ No | 1 | 0 | 5 |
| 6 | Observability Platform (OPS-Q1) | ✅ Yes | 1 | 1 (OBS-Q1) | 5 |
| | **Total** | **4 of 6** | **6** | **4** | |

**4 of 6 MOD Phase 0 items are dual-resolution** — they resolve findings in both assessments simultaneously.

### ARA-Specific Remediation (After Phase 0)

These ARA findings have no MOD co-requisite in Phase 0 or require agent-specific work beyond what MOD Phase 0 provides.
Address these after MOD Phase 0 completes, ordered by severity (BLOCKER → RISK-SAFETY → RISK-QUALITY).

#### 1. AUTH-Q1: Machine Identity Authentication (BLOCKER)

**ARA Finding:** AUTH-Q1: Machine Identity (BLOCKER) — 4 services affected
**Why Not Covered by MOD Phase 0:** MOD co-requisites SEC-Q3 (API Auth) and SEC-Q4 (Centralized Identity) are scheduled for MOD Phase 3, not Phase 0. Phase 0 builds infrastructure foundations but not the identity provider itself.
**Remediation Action:** Deploy centralized identity provider (Amazon Cognito User Pool) with per-agent OAuth2 client credentials. Configure Spring Security OAuth2 resource server for Camunda 7 services. Integrate with new REST API layers for camunda8-order-process and bpmn-miwg-test-suite.
**Dependencies:** API-Q1 (new API surfaces need auth from the start), INF-Q5 (VPC for identity provider), INF-Q10 (IaC for Cognito deployment)

#### 2. DATA-Q1: Sensitive Data Classification (BLOCKER)

**ARA Finding:** DATA-Q1: Data Classification (BLOCKER) — 5 services affected
**Why Not Covered by MOD Phase 0:** MOD Phase 0 addresses SEC-Q5 (Secrets Remediation) which is one of two MOD co-requisites. The ARA extends MOD relationship means MOD handles data storage (S3) while ARA requires field-level PII classification, data dictionaries, and agent-specific redaction — fundamentally different work.
**Remediation Action:** Establish portfolio-wide data classification taxonomy (Public, Internal, Confidential, Restricted). Inventory all data fields across 5 services: process variables, API response fields, database columns, configuration files. Apply field-level classification metadata and build classification-based access controls.
**Dependencies:** AUTH-Q2 (scoped permissions needed to enforce classification-based access)

#### 3. API-Q1: Documented API Interface (BLOCKER)

**ARA Finding:** API-Q1: Documented API Interface (BLOCKER) — 3 services affected
**Why Not Covered by MOD Phase 0:** No MOD co-requisite exists in the mapping table. This is architecturally specific — two services have no API surface at all, one has only a generic engine API.
**Remediation Action:** Per-service API development: (1) camunda8-order-process: Spring `@RestController` wrapping Zeebe operations with OpenAPI spec, (2) camunda-rest-service: business facade REST API abstracting Camunda internals, (3) bpmn-miwg-test-suite: evaluate need; if needed, build lightweight read-only API.
**Dependencies:** AUTH-Q1 (new APIs need machine identity from the start), INF-Q10 (IaC for deployment)

#### 4. AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7: Identity Infrastructure (RISK-SAFETY)

**ARA Findings:** AUTH-Q2 (Scoped Permissions), AUTH-Q3 (Action-Level Auth), AUTH-Q6 (Audit Logging), AUTH-Q7 (Identity Suspension) — all RISK-SAFETY in 5/5 services
**Why Not Covered by MOD Phase 0:** All depend on AUTH-Q1 resolution first, plus MOD security infrastructure improvements (SEC-Q3, SEC-Q4, SEC-Q1) not in Phase 0.
**Remediation Action:** After AUTH-Q1 is resolved: configure fine-grained RBAC with per-agent scopes (AUTH-Q2), implement API Gateway authorizers with method-level access (AUTH-Q3), deploy immutable audit logging with principal attribution (AUTH-Q6), implement portfolio-wide agent suspension capability (AUTH-Q7).
**Dependencies:** AUTH-Q1, SEC-Q3, SEC-Q4, SEC-Q1, OPS-Q1

#### 5. STATE-Q5: Rate Limiting (RISK-SAFETY)

**ARA Finding:** STATE-Q5: Rate Limiting (RISK-SAFETY) — 5 services affected
**Why Not Covered by MOD Phase 0:** MOD co-requisite INF-Q6 (API Entry Point) is a foundational blocker but not a named Phase 0 item. INF-Q6 scores 1.00 across all 5 services.
**Remediation Action:** Deploy shared API Gateway (AWS API Gateway) with per-agent usage plans, portfolio-level WAF rules, and burst/steady-state rate limits per agent identity.
**Dependencies:** INF-Q5 (Network Architecture — Phase 0), INF-Q6 (API Entry Point — not in Phase 0)

#### 6. OBS-Q2: Alerting (RISK-QUALITY)

**ARA Finding:** OBS-Q2: Alerting (RISK-QUALITY) — 5 services affected
**Why Not Covered by MOD Phase 0:** MOD co-requisite OPS-Q4 (Anomaly Detection) is a foundational blocker but not explicitly a named Phase 0 item. However, the Observability Platform (OPS-Q1) in Phase 0 provides the foundation for alerting.
**Remediation Action:** Configure CloudWatch alarms with anomaly detection on error rates and latency. Integrate with PagerDuty/OpsGenie for on-call notification. Define standard alerting thresholds for agent-specific metrics.
**Dependencies:** OPS-Q1 (Observability Platform — Phase 0)

#### 7. HITL-Q3: Sandbox/Staging Environment (RISK-QUALITY)

**ARA Finding:** HITL-Q3: Sandbox/Staging (RISK-QUALITY) — 5 services affected
**Why Not Covered by MOD Phase 0:** MOD co-requisite OPS-Q5 (Deployment Strategy) is a foundational blocker but not a Phase 0 item. OPS-Q5 scores 1.00 across all services.
**Remediation Action:** Implement blue/green deployments via CodeDeploy with ECS. Create Docker Compose-based staging environments for each service. Build shared seed data framework for Camunda process engines.
**Dependencies:** INF-Q1 (Managed Compute), INF-Q10 (IaC Foundation — Phase 0)

---

## Section 5: Shared Findings Deduplication

These findings appear in both the portfolio ARA report and the portfolio MOD report.
They represent the same underlying gap viewed through different assessment lenses.
**Plan remediation once, not twice.**

| # | ARA Finding | ARA Severity | MOD Finding | MOD Avg Score | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 1 | AUTH-Q1: Machine Identity | BLOCKER | SEC-Q3: API Auth + SEC-Q4: Centralized Identity | 1.20 / 1.00 | MOD → ARA | Deploy centralized identity provider (Amazon Cognito) with OAuth2 client_credentials grant |
| 2 | AUTH-Q2: Scoped Permissions | RISK-SAFETY | SEC-Q3: API Auth + SEC-Q4: Centralized Identity | 1.20 / 1.00 | MOD → ARA | Configure fine-grained OAuth2 scopes with per-agent RBAC roles in centralized IdP |
| 3 | AUTH-Q3: Action-Level Auth | RISK-SAFETY | SEC-Q3: API Auth + INF-Q6: API Entry Point | 1.20 / 1.00 | MOD → ARA | Implement API Gateway authorizers with method-level access control |
| 4 | AUTH-Q4: Identity Propagation | RISK-QUALITY | SEC-Q4: Centralized Identity | 1.00 | MOD → ARA | Configure JWT token propagation through centralized IdP |
| 5 | AUTH-Q5: Credential Management | RISK-SAFETY | SEC-Q5: Secrets Management | 1.40 | Shared | Migrate to AWS Secrets Manager with automated rotation |
| 6 | AUTH-Q6: Immutable Audit Logging | RISK-SAFETY | SEC-Q1: Audit Logging + OPS-Q1: Distributed Tracing | 1.00 / 1.00 | MOD → ARA | Deploy centralized immutable log aggregation (CloudWatch + S3 Object Lock) |
| 7 | AUTH-Q7: Identity Suspension | RISK-SAFETY | SEC-Q4: Centralized Identity | 1.00 | MOD → ARA | Implement centralized agent identity registry with portfolio-wide suspension |
| 8 | API-Q2: Machine-Readable Spec | RISK-QUALITY | APP-Q5: API Versioning | 1.20 | Shared | Standardize on OpenAPI 3.0+ with versioned API specifications |
| 9 | API-Q3: Structured Errors | RISK-QUALITY | APP-Q5: API Versioning + INF-Q6: API Entry Point | 1.20 / 1.00 | Shared | Define portfolio-wide structured error response format with API Gateway |
| 10 | STATE-Q5: Rate Limiting | RISK-SAFETY | INF-Q6: API Entry Point | 1.00 | MOD → ARA | Deploy shared API Gateway with per-agent rate limiting and WAF rules |
| 11 | OBS-Q1: Distributed Tracing | RISK-QUALITY | OPS-Q1: Distributed Tracing | 1.00 | Shared | Deploy OpenTelemetry/X-Ray across all services |
| 12 | OBS-Q2: Alerting | RISK-QUALITY | OPS-Q4: Anomaly Detection | 1.00 | Shared | Configure CloudWatch alarms with anomaly detection |
| 13 | DISC-Q1: Schema Versioning | RISK-QUALITY | APP-Q5: API Versioning | 1.20 | Shared | Implement API versioning standard with consumer-driven contract testing |
| 14 | ENG-Q1: Infra Governance | RISK-QUALITY | INF-Q10: IaC Coverage | 1.00 | Shared | Adopt single IaC tool (CDK/Terraform) for all services |
| 15 | ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY | INF-Q11: CI/CD Automation + OPS-Q6: Integration Testing | 1.80 / 2.00 | MOD → ARA | Create shared GitHub Actions CI/CD template with contract testing |
| 16 | DATA-Q1: Data Classification | BLOCKER | DATA-Q1: Unstructured Data + SEC-Q5: Secrets Mgmt | 1.00 / 1.40 | ARA extends MOD | Data platform modernization (S3 + Secrets Manager) + field-level PII classification taxonomy |
| 17 | HITL-Q3: Sandbox/Staging | RISK-QUALITY | OPS-Q5: Deployment Strategy | 1.00 | MOD → ARA | Implement blue/green deployments with staging environments |

### Deduplication Summary

- **17 findings** appear in both assessments (all 17 entries in the MOD-ARA mapping have both an active ARA finding and a MOD co-requisite scoring below 2.0)
- **13 unique remediation items** can be consolidated (some MOD co-requisites like SEC-Q3, SEC-Q4, APP-Q5, and INF-Q6 appear in multiple mapping entries — resolving them once addresses multiple ARA findings)
- **Estimated effort savings:** Teams avoid duplicating planning and execution for 17 shared infrastructure gaps across 5 services. Without deduplication, teams would plan ~34 separate work items (17 from each assessment); with deduplication, they plan 13 consolidated items — a **62% reduction** in planning overhead.

### Consolidation Detail

The 17 mapping entries consolidate to 13 unique remediation actions because several MOD co-requisites serve multiple ARA findings:

| MOD Co-Requisite | ARA Findings Served | Consolidated Action |
|---|---|---|
| SEC-Q3 + SEC-Q4 (Centralized Identity) | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q7 | One Cognito deployment resolves 5 ARA findings |
| SEC-Q5 (Secrets Management) | AUTH-Q5, DATA-Q1 (partial) | One Secrets Manager migration resolves 2 ARA findings |
| APP-Q5 (API Versioning) | API-Q2, API-Q3, DISC-Q1 | One API versioning standard resolves 3 ARA findings |
| INF-Q6 (API Entry Point) | AUTH-Q3, API-Q3, STATE-Q5 | One API Gateway deployment resolves 3 ARA findings |
| OPS-Q1 (Distributed Tracing) | OBS-Q1, AUTH-Q6 (partial) | One observability platform resolves 2 ARA findings |
| SEC-Q1 (Audit Logging) | AUTH-Q6 | One audit logging deployment resolves 1 ARA finding |
| OPS-Q4 (Anomaly Detection) | OBS-Q2 | One alerting configuration resolves 1 ARA finding |
| INF-Q10 (IaC Coverage) | ENG-Q1 | One IaC adoption resolves 1 ARA finding |
| INF-Q11 + OPS-Q6 (CI/CD + Testing) | ENG-Q2 | One CI/CD template resolves 1 ARA finding |
| DATA-Q1 (Unstructured Data) | DATA-Q1 (ARA, partial) | Data platform + classification resolves 1 ARA finding |
| OPS-Q5 (Deployment Strategy) | HITL-Q3 | One deployment strategy resolves 1 ARA finding |

---

## Section 6: BAO + ARA Readiness Matrix

> This section cross-references BAO-identified agent opportunities with ARA readiness
> findings for their target systems. It answers: "Which agent opportunities can we build
> today, which are blocked by ARA findings, and which need ARA assessment first?"

### Readiness Matrix

| BPMN Process | Agent Task | Instances | Target System | ARA Profile | BLOCKERs | Status |
|---|---|---|---|---|---|---|
| process (camunda-invoice) | Check decision | 1 | camunda-invoice | 🟠 Remediation Required | 1 (DATA-Q1) | Blocked |
| Process (camunda-invoice) | evaluate decision table | 1 | camunda-invoice | 🟠 Remediation Required | 1 (DATA-Q1) | Blocked |
| failingTimer (camunda-invoice) | Analyze report | 1 | camunda-invoice | 🟠 Remediation Required | 1 (DATA-Q1) | Blocked |
| Review Invoice (camunda-invoice) | Review Invoice | 1 | camunda-invoice | 🟠 Remediation Required | 1 (DATA-Q1) | Blocked |
| Review Invoice (camunda-invoice) | Assign Reviewer | 1 | camunda-invoice | 🟠 Remediation Required | 1 (DATA-Q1) | Blocked |
| C.4.0 Employee Onboarding (bpmn-miwg-test-suite) | Review terms of contract | 23 | bpmn-miwg-test-suite | ❌ Not Agent-Integrable | 3 (API-Q1, AUTH-Q1, DATA-Q1) | Blocked |
| C.1.0 Invoice Team-Assistant (bpmn-miwg-test-suite) | Review and document result | 36 | bpmn-miwg-test-suite | ❌ Not Agent-Integrable | 3 (API-Q1, AUTH-Q1, DATA-Q1) | Blocked |

### Summary

| Status | Agent Opportunities | Description |
|--------|--------------------:|-------------|
| Ready | 0 | No target systems are Agent-Ready or Pilot-Ready |
| Blocked | 64 | All target systems have 1+ ARA BLOCKERs preventing agent deployment |
| Unassessed | 0 | All target systems have been evaluated by ARA |
| **Total** | **64** | |

> **Key finding**: All 64 agent opportunities identified by BAO are blocked by ARA findings on their target systems. Zero agents can be deployed today. The most common blocker is DATA-Q1 (Sensitive Data Classification), which affects both target systems and all 64 agent tasks.

### Blocked Opportunities Detail

For each blocked agent opportunity, the specific ARA BLOCKERs on the target system
are listed with cross-references to MOD co-requisites from Section 1:

| Agent Task | Target System | ARA BLOCKER(s) | MOD Co-Requisite | In MOD Phase 0? |
|---|---|---|---|---|
| Check decision (1 instance) | camunda-invoice | DATA-Q1: Data Classification | DATA-Q1 (Unstructured Data) + SEC-Q5 (Secrets Mgmt) | ⚠️ Partial — SEC-Q5 is in Phase 0; DATA-Q1 is not a named Phase 0 item |
| evaluate decision table (1 instance) | camunda-invoice | DATA-Q1: Data Classification | DATA-Q1 (Unstructured Data) + SEC-Q5 (Secrets Mgmt) | ⚠️ Partial — SEC-Q5 is in Phase 0; DATA-Q1 is not a named Phase 0 item |
| Analyze report (1 instance) | camunda-invoice | DATA-Q1: Data Classification | DATA-Q1 (Unstructured Data) + SEC-Q5 (Secrets Mgmt) | ⚠️ Partial — SEC-Q5 is in Phase 0; DATA-Q1 is not a named Phase 0 item |
| Review Invoice (1 instance) | camunda-invoice | DATA-Q1: Data Classification | DATA-Q1 (Unstructured Data) + SEC-Q5 (Secrets Mgmt) | ⚠️ Partial — SEC-Q5 is in Phase 0; DATA-Q1 is not a named Phase 0 item |
| Assign Reviewer (1 instance) | camunda-invoice | DATA-Q1: Data Classification | DATA-Q1 (Unstructured Data) + SEC-Q5 (Secrets Mgmt) | ⚠️ Partial — SEC-Q5 is in Phase 0; DATA-Q1 is not a named Phase 0 item |
| Review terms of contract (23 instances) | bpmn-miwg-test-suite | API-Q1: Documented API Interface | None (ARA-specific) | N/A — No MOD co-requisite |
| Review terms of contract (23 instances) | bpmn-miwg-test-suite | AUTH-Q1: Machine Identity | SEC-Q3 (API Auth) + SEC-Q4 (Centralized Identity) | ❌ No — SEC-Q3/SEC-Q4 are in Phase 3 (Identity Federation) |
| Review terms of contract (23 instances) | bpmn-miwg-test-suite | DATA-Q1: Data Classification | DATA-Q1 (Unstructured Data) + SEC-Q5 (Secrets Mgmt) | ⚠️ Partial — SEC-Q5 is in Phase 0; DATA-Q1 is not a named Phase 0 item |
| Review and document result (36 instances) | bpmn-miwg-test-suite | API-Q1: Documented API Interface | None (ARA-specific) | N/A — No MOD co-requisite |
| Review and document result (36 instances) | bpmn-miwg-test-suite | AUTH-Q1: Machine Identity | SEC-Q3 (API Auth) + SEC-Q4 (Centralized Identity) | ❌ No — SEC-Q3/SEC-Q4 are in Phase 3 (Identity Federation) |
| Review and document result (36 instances) | bpmn-miwg-test-suite | DATA-Q1: Data Classification | DATA-Q1 (Unstructured Data) + SEC-Q5 (Secrets Mgmt) | ⚠️ Partial — SEC-Q5 is in Phase 0; DATA-Q1 is not a named Phase 0 item |

> **Interpretation**: No blocked opportunities have ARA BLOCKERs that are fully resolved by MOD Phase 0 co-requisites. The 5 camunda-invoice agent tasks are blocked solely by DATA-Q1, which requires ARA-specific data classification work beyond MOD scope. The 59 bpmn-miwg-test-suite agent tasks face 3 BLOCKERs — API-Q1 has no MOD co-requisite at all, AUTH-Q1's co-requisites are in MOD Phase 3, and DATA-Q1 is only partially addressed.

### Unblocking Sequence for Agent Deployment

To unblock the 64 agent opportunities, the following work must be completed in order:

**For camunda-invoice (5 agent tasks):**
1. Complete DATA-Q1 remediation: Establish data classification taxonomy, classify all invoice data fields (creditor names, amounts, invoice numbers, user emails)
2. All 5 agent tasks become buildable

**For bpmn-miwg-test-suite (59 agent tasks):**
1. Complete API-Q1 remediation: Build read-only REST API over BPMN reference data (or determine if agentic access is needed)
2. Complete AUTH-Q1 remediation: Deploy centralized identity provider and integrate with new API
3. Complete DATA-Q1 remediation: Classify maintainer PII, create redacted views
4. All 59 agent tasks become buildable (though 59 tasks represent only 2 unique patterns across vendor exports)

**Fastest path to first agent deployment:** Focus on camunda-invoice — it requires only DATA-Q1 remediation (1 BLOCKER) to unblock 5 agent tasks. bpmn-miwg-test-suite requires 3 BLOCKER resolutions and may not warrant the investment given its nature as a test data archive.

---

*Report generated by Portfolio ARA–MOD Bridge Assessment. This report cross-references the portfolio ARA report, portfolio MOD report, and portfolio BAO report to produce unified planning guidance. All numeric totals have been cross-validated against source reports.*
