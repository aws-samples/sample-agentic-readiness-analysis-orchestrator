# Portfolio ARA–MOD Bridge Report

**Portfolio**: zg-cmp-atx-testing
**Date**: 2026-05-01
**ARA Report**: agentic-readiness-analysis/zg-cmp-atx-testing-portfolio-ara-report.md
**MOD Report**: modernization-readiness-analysis/zg-cmp-atx-testing-portfolio-mod-report.md

---

## Bridge Summary

| Metric | Value |
|--------|-------|
| Shared Remediation Mappings | 17 |
| ARA BLOCKERs Resolvable by MOD Phase 0 | 11 of 20 (55%) |
| MOD Readiness Gates Triggered | 2 (SEC + OPS) |
| Unified Remediation Items | 8 (6 Phase 0 + 2 ARA-specific) |
| Deduplicated Shared Findings | 17 |
| BPMN Agent Opportunities (Ready / Blocked / Unassessed) | N/A |

> **v5.1 update**: ARA DATA-Q1 was revised from a binary BLOCKER (for any repo storing sensitive data without formal classification) to a tiered model (B1: API response scoping / B2: access control differentiation / B3: formal classification metadata). DATA-Q1 BLOCKERs dropped from 14 → 7 services. Total ARA BLOCKERs dropped from 27 → 20. The AUTH-Q1 → MOD Security Foundation dividend remains 11 BLOCKERs; the MOD Phase 0 resolution percentage therefore rises from 41% → 55%.

---

## Section 1: Shared Remediation Mapping

This section maps ARA findings to their MOD co-requisites using the built-in cross-reference mapping.
Each row shows an ARA finding, its MOD dependency, and the shared remediation action that resolves both.

| # | ARA Finding | ARA Severity | Affected Services | MOD Co-Requisite(s) | MOD Gap Services | Relationship | Shared Remediation Action |
|---|---|---|---|---|---|---|---|
| 1 | AUTH-Q1: Machine Identity | BLOCKER | 11 of 34 | SEC-Q3: Encryption in Transit (14 svc <2) + SEC-Q4: Dependency Vuln Mgmt (20 svc <2) | 20 | MOD → ARA | Deploy centralized identity provider with API authentication and dependency scanning to enable per-agent machine identity |
| 2 | AUTH-Q2: Scoped Permissions | RISK-SAFETY | 14 of 34 | SEC-Q3: Encryption in Transit (14 svc <2) + SEC-Q4: Dependency Vuln Mgmt (20 svc <2) | 20 | MOD → ARA | Configure fine-grained OAuth2 scopes in centralized identity provider; enforce TLS for secure credential exchange |
| 3 | AUTH-Q3: Action-Level Auth | RISK-SAFETY | 12 of 34 | SEC-Q3: Encryption in Transit (14 svc <2) + INF-Q6: Container-Readiness (31 svc <2) | 31 | MOD → ARA | Implement API Gateway with per-action authorization policies; requires container-ready stateless services |
| 4 | AUTH-Q4: Identity Propagation | RISK-QUALITY | 8 of 34 | SEC-Q4: Dependency Vuln Mgmt (20 svc <2) | 20 | MOD → ARA | Establish centralized identity with token propagation across service boundaries |
| 5 | AUTH-Q5: Credential Management | RISK-QUALITY | 10 of 34 | SEC-Q5: Secrets Management (6 svc <2) | 6 | Shared | Migrate all credentials to AWS Secrets Manager with automated rotation |
| 6 | AUTH-Q6: Immutable Audit Logging | RISK-SAFETY | 17 of 34 | SEC-Q1: IAM & Access Control (30 svc <2) + OPS-Q1: Distributed Tracing (20 svc <2) | 30 | MOD → ARA | Deploy centralized IAM with audit trail and distributed tracing for immutable agent action logging |
| 7 | AUTH-Q7: Identity Suspension | RISK-SAFETY | 14 of 34 | SEC-Q4: Dependency Vuln Mgmt (20 svc <2) | 20 | MOD → ARA | Centralized identity registry with per-agent credential revocation capability |
| 8 | API-Q2: Machine-Readable Spec | RISK-QUALITY | 13 of 34 | APP-Q5: Config Externalization (8 svc <2) | 8 | Shared | Generate OpenAPI specifications; externalize API configuration for versioned, machine-readable endpoints |
| 9 | API-Q3: Structured Errors | RISK-QUALITY | 16 of 34 | APP-Q5: Config Externalization (8 svc <2) + INF-Q6: Container-Readiness (31 svc <2) | 31 | Shared | Standardize on RFC 7807 error responses; deploy API Gateway for consistent error handling |
| 10 | STATE-Q5: Rate Limiting | RISK-SAFETY | 14 of 34 | INF-Q6: Container-Readiness (31 svc <2) | 31 | MOD → ARA | Deploy API Gateway with per-agent rate limiting; requires containerized stateless services behind load balancer |
| 11 | OBS-Q1: Distributed Tracing | RISK-QUALITY | 18 of 34 | OPS-Q1: Distributed Tracing (20 svc <2) | 20 | Shared | Deploy AWS X-Ray / ADOT across all services for end-to-end distributed tracing |
| 12 | OBS-Q2: Alerting | RISK-QUALITY | 17 of 34 | OPS-Q4: Log Aggregation (28 svc <2) | 28 | Shared | Deploy centralized CloudWatch Logs with alerting on error rates and latency thresholds |
| 13 | DISC-Q1: Schema Versioning | RISK-QUALITY | 32 of 34 | APP-Q5: Config Externalization (8 svc <2) | 8 | Shared | Implement semantic versioning with breaking-change detection in CI; externalize API versioning configuration |
| 14 | ENG-Q1: Infra Governance | RISK-QUALITY | 15 of 25 | INF-Q10: IaC Coverage (31 svc <2) | 31 | Shared | Standardize on AWS CDK or Terraform for all agent-facing infrastructure with drift detection |
| 15 | ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY | 18 of 25 | INF-Q11: CI/CD Automation (16 svc <3) + OPS-Q6: Integration Testing (3 svc <2) | 16 | MOD → ARA | Extend GitHub Actions workflows with deployment automation and API contract testing |
| 16 | DATA-Q1: Data Classification ⚡ (Tiered) | BLOCKER (7 svc) + RISK-SAFETY (2 svc) + INFO (5 svc) | 7 BLOCKER / 34 total | DATA-Q1: Data Classification (20 svc <2) + SEC-Q5: Secrets Mgmt (6 svc <2) | 20 | ARA extends MOD | Per-service masking fixes for credential-leak endpoints (Servarr HostConfigResource, thingsboard DeviceCredentials, druid supervisor specs, conductor HTTP-task output); MOD data governance remains relevant but is no longer a hard prerequisite for the tiered B1 fix |
| 17 | HITL-Q3: Sandbox/Staging | RISK-QUALITY | 16 of 34 | OPS-Q5: Deployment Strategy (26 svc <2) | 26 | MOD → ARA | Standardize deployment strategy with staging environments for agent testing |

### Relationship Narratives

**MOD → ARA prerequisite** (entries 1–4, 6–7, 10, 15, 17): The MOD gap must be resolved before the ARA finding can be addressed. ARA remediation is blocked until MOD co-requisite scores improve. For example, AUTH-Q1 (Machine Identity) cannot be implemented without the security infrastructure baseline that SEC-Q3 and SEC-Q4 evaluate. Similarly, STATE-Q5 (Rate Limiting) requires the API entry point infrastructure that INF-Q6 evaluates.

**Shared** (entries 5, 8–9, 11–14): Same underlying gap viewed through different analysis lenses. One remediation action resolves both the MOD and ARA findings. For example, OBS-Q1 (ARA Distributed Tracing) and OPS-Q1 (MOD Distributed Tracing) are the same capability gap — deploying X-Ray/ADOT resolves both. AUTH-Q5 (ARA Credential Management) and SEC-Q5 (MOD Secrets Management) both require migrating to AWS Secrets Manager.

**ARA extends MOD** (entry 16): ARA adds agent-specific requirements on top of what MOD already evaluates. Under the revised tiered DATA-Q1 model, the ARA finding is now about **concrete code-level credential leakage in agent-facing API endpoints** (B1 sub-check) rather than generic "classification framework absent". MOD remediation (portfolio data classification framework, secrets management) remains complementary but is not a blocking prerequisite for the tiered B1 fix — masking specific endpoints (Servarr `HostConfigResource`, thingsboard `DeviceCredentials`, druid supervisor specs, conductor HTTP-task output) can proceed independently of MOD Phase 0.

---

## Section 2: Agentic Readiness Delta

**If MOD Phase 0 were completed, 11 of 20 ARA BLOCKERs would be resolved.**

This means **55%** of the portfolio's agentic readiness blockers are actually modernization prerequisites —
completing MOD Phase 0 delivers an agentic readiness dividend without any ARA-specific remediation work. (The percentage rose from 41% to 55% after the v5.1 DATA-Q1 rubric revision reduced the DATA-Q1 BLOCKER count from 14 to 7, while the 11 AUTH-Q1 BLOCKERs resolved by MOD Phase 0 remained constant.)

### ARA BLOCKER Inventory

| ARA BLOCKER | Question ID | Instances | % of Total BLOCKERs |
|---|---|---|---|
| Machine Identity Authentication | AUTH-Q1 | 11 | 55% |
| Sensitive Data Classification (tiered B1) | DATA-Q1 | 7 | 35% |
| Documented API Interface | API-Q1 | 2 | 10% |
| **Total** | | **20** | **100%** |

### BLOCKERs Resolved by MOD Phase 0

| ARA BLOCKER | Affected Services | MOD Phase 0 Item | How It Resolves |
|---|---|---|---|
| AUTH-Q1: Machine Identity (11 services) | conductor-oss--conductor, greenshot--greenshot, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, umami-software--umami | **Security Foundation** (SEC-Q1, SEC-Q4, SEC-Q5) | The Phase 0 Security Foundation deploys shared IAM role templates, enables centralized identity management (SEC-Q4), and deploys AWS Secrets Manager (SEC-Q5). This creates the identity infrastructure required for per-agent machine identity authentication. Combined with the API Gateway deployment from EKS Cluster Setup, services gain the authentication layer needed to issue and validate per-agent credentials. |

**Total resolved**: 11 BLOCKERs (11 AUTH-Q1 instances across 11 services)

### BLOCKERs Requiring ARA-Specific Remediation

| ARA BLOCKER | Affected Services | Why MOD Phase 0 Doesn't Resolve |
|---|---|---|
| DATA-Q1: Data Classification (7 services, down from 14 under tiered model) | apache--druid, conductor-oss--conductor, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, thingsboard--thingsboard | Under the v5.1 tiered DATA-Q1 model, these 7 BLOCKER services each have a concrete B1 (API response scoping) finding — a specific endpoint that returns credentials, access tokens, or auth headers in plaintext. **MOD Phase 0 data governance (DATA-Q1 MOD, SEC-Q5) does not fix the specific leakage paths**: the Servarr family's `HostConfigResource` leaks the master ApiKey via `GET /config/host`, thingsboard's `/device/{id}/credentials` endpoint returns access tokens unmasked, druid's `SupervisorResource` serializes Kafka/Kinesis credentials, and conductor's `HttpTask.java:138` persists Authorization headers into task output. These are per-service code changes (add `@JsonIgnore`, extend masking to non-provider resources, filter `consumerProperties` keys) that can proceed in parallel with or independently of MOD Phase 0. 5 additional services (Alluxio, Graylog, scality/cloudserver, umami, ToolJet) moved to DATA-Q1 = INFO and are no longer blockers; 2 services (Flowise, hapi-fhir) moved to DATA-Q1 = RISK-SAFETY. |
| API-Q1: Documented API Interface (2 services) | greenshot--greenshot, ToolJet--ToolJet | API-Q1 has **no MOD co-requisite** in the cross-reference mapping table. This is a purely ARA-specific requirement — the service must expose a documented, machine-discoverable API for agents to interact with. Greenshot is a desktop GUI with no programmatic API; ToolJet has an API but no OpenAPI specification. MOD Phase 0 does not create API documentation for individual services. |

**Total requiring ARA-specific remediation**: 9 BLOCKERs (7 DATA-Q1 + 2 API-Q1)

### Delta Visualization

```
Total ARA BLOCKERs:          20 (100%)  ← down from 27 after v5.1 DATA-Q1 tiered rubric
├── Resolved by MOD Phase 0: 11 ( 55%)  ← AUTH-Q1 instances
└── Require ARA remediation:  9 ( 45%)  ← DATA-Q1 (7) + API-Q1 (2)
```

> **Key Insight (updated)**: The modernization dividend is concentrated entirely in the AUTH-Q1 (Machine Identity) BLOCKER. All 11 instances of AUTH-Q1 can be resolved as a side effect of MOD Phase 0 Security Foundation work, and their share of total BLOCKERs rose from 41% to 55% after the DATA-Q1 rubric revision. The remaining 7 DATA-Q1 BLOCKERs (down from 14) all have concrete code-level findings: four Servarr apps leak their master ApiKey via the same `HostConfigResource` pattern, ThingsBoard returns device credentials plaintext, Druid exposes Kafka/Kinesis ingestion credentials, and Conductor embeds HTTP-task Authorization headers in workflow task output. These are localized masking fixes (not classification frameworks) and can proceed in parallel with MOD Phase 0.

---

## Section 3: MOD Readiness Gate

This section provides informational advisories when MOD category averages indicate foundational gaps
that will block ARA remediation efforts. These are not hard gates — they are sequencing guidance.

### ⚠️ Security Baseline Gap

**MOD SEC category average: 1.61 / 4.0**

ARA identity and access remediation (AUTH-Q1 through AUTH-Q7) will be blocked by MOD security baseline gaps.

**What this means:** The portfolio's security infrastructure (API authentication, centralized identity, secrets management,
audit logging) scores below the minimum 2.0 threshold for ARA remediation to be effective. The SEC category has 7 foundational blockers:
- SEC-Q1: IAM & Access Control — 30 of 34 services score <2
- SEC-Q2: Encryption at Rest — 13 of 14 applicable services score <2
- SEC-Q3: Encryption in Transit — 14 of 34 services score <2
- SEC-Q4: Dependency Vulnerability Mgmt — 20 of 34 services score <2
- SEC-Q5: Secrets Management — 6 of 34 services score <2
- SEC-Q6: Least-Privilege IAM — 25 of 34 services score <2
- SEC-Q7: Application Security Pipeline — 13 of 34 services score <2

Teams should prioritize MOD SEC remediation (especially the Phase 0 Security Foundation) before attempting ARA AUTH remediation.

**Affected ARA findings:**
- AUTH-Q1: Machine Identity Authentication (BLOCKER — 11 services)
- AUTH-Q2: Scoped Permissions (RISK-SAFETY — 14 services)
- AUTH-Q3: Action-Level Authorization (RISK-SAFETY — 12 services)
- AUTH-Q4: Identity Propagation (RISK-QUALITY — 8 services)
- AUTH-Q5: Credential Management (RISK-QUALITY — 10 services)
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY — 17 services)
- AUTH-Q7: Agent Identity Suspension (RISK-SAFETY — 14 services)

### ⚠️ Operational Baseline Gap

**MOD OPS category average: 1.53 / 4.0**

ARA observability remediation (AUTH-Q6, OBS-Q1, OBS-Q2) will be blocked by MOD operational gaps.

**What this means:** The portfolio's operational infrastructure (distributed tracing, anomaly detection, deployment strategies)
scores below the minimum 2.0 threshold for ARA observability remediation to be effective. The OPS category has 9 foundational blockers:
- OPS-Q1: Distributed Tracing — 20 of 34 services score <2
- OPS-Q2: SLO/SLA Definition — 16 of 18 applicable services score <2
- OPS-Q3: Centralized Metrics — 19 of 34 services score <2
- OPS-Q4: Log Aggregation — 28 of 34 services score <2
- OPS-Q5: Deployment Strategy — 26 of 34 services score <2
- OPS-Q6: Integration Testing — 3 of 34 services score <2
- OPS-Q7: Runbook / Incident Response — 32 of 34 services score <2
- OPS-Q8: Capacity Planning — 22 of 34 services score <2
- OPS-Q9: Chaos Engineering — 32 of 34 services score <2

Teams should prioritize MOD OPS remediation (especially the Phase 0 Observability Platform) before attempting ARA observability remediation.

**Affected ARA findings:**
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY — 17 services)
- OBS-Q1: Distributed Tracing (RISK-QUALITY — 18 services)
- OBS-Q2: Alerting on Error Rates and Latency (RISK-QUALITY — 17 services)

> **Note**: AUTH-Q6 (Immutable Audit Logging) is blocked by **both** the SEC and OPS gates. It requires both IAM/access control infrastructure (SEC-Q1) and distributed tracing infrastructure (OPS-Q1) to be in place before agent audit logging can be implemented effectively.

---

## Section 4: Unified Remediation Sequence

This section merges the ARA remediation guidance and MOD Phase 0 roadmap into a single sequence.
Items that resolve findings in both analyses are marked as **dual-resolution** — completing them
delivers value for both modernization and agentic readiness simultaneously.

### Phase 0: Cross-Cutting Foundation (MOD + ARA)

These items come from the MOD Phase 0 roadmap. Each item shows which MOD findings AND which ARA findings
it resolves. Complete these first — they unblock ARA remediation.

#### 1. IaC Foundation

**MOD Findings Resolved:**
- INF-Q10: IaC Coverage — 31 services affected
- INF-Q7: Multi-AZ Resilience — 34 services affected

**ARA Findings Resolved:**
- ENG-Q1: Infrastructure Governance (RISK-QUALITY) — 15 services affected

**ARA Findings Unblocked** (can be addressed after this item completes):
- ENG-Q2: CI/CD + Contract Tests (RISK-QUALITY) — partially, IaC enables reproducible test environments

**Dual-Resolution Impact:** This single item resolves 2 MOD findings and 1 ARA finding across 34 services. Standardizing on AWS CDK or Terraform provides both the MOD infrastructure-as-code capability and the ARA infrastructure governance for agent-facing surfaces.

---

#### 2. Shared VPC Architecture

**MOD Findings Resolved:**
- INF-Q5: Network Security Architecture — 33 services affected

**ARA Findings Resolved:**
- None directly mapped

**ARA Findings Unblocked:**
- STATE-Q5: Rate Limiting (RISK-SAFETY) — VPC with security groups enables network-level traffic controls
- AUTH-Q3: Action-Level Auth (RISK-SAFETY) — network segmentation supports authorization enforcement

**Dual-Resolution Impact:** This item resolves 1 MOD finding across 33 services. While no ARA finding is directly resolved, the VPC architecture is a prerequisite for deploying API Gateway and other infrastructure that ARA findings depend on.

---

#### 3. EKS Cluster Setup

**MOD Findings Resolved:**
- INF-Q1: Managed Compute — 32 services affected
- INF-Q8: Auto-Scaling — 10 services affected

**ARA Findings Resolved:**
- None directly mapped

**ARA Findings Unblocked:**
- STATE-Q5: Rate Limiting (RISK-SAFETY) — EKS with API Gateway enables per-agent rate limiting
- API-Q3: Structured Errors (RISK-QUALITY) — API Gateway provides consistent error handling
- AUTH-Q3: Action-Level Auth (RISK-SAFETY) — API Gateway enables per-action authorization policies

**Dual-Resolution Impact:** This item resolves 2 MOD findings across 32 services. EKS provides the managed compute foundation that multiple ARA findings depend on for deployment of API Gateway, load balancers, and service mesh components.

---

#### 4. Security Foundation

**MOD Findings Resolved:**
- SEC-Q1: IAM & Access Control — 30 services affected
- SEC-Q4: Dependency Vulnerability Management — 20 services affected
- SEC-Q5: Secrets Management — 6 services affected

**ARA Findings Resolved:**
- AUTH-Q1: Machine Identity Authentication (BLOCKER) — 11 services affected
- AUTH-Q5: Credential Management (RISK-QUALITY) — 10 services affected
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY) — 17 services affected (partially — IAM component)

**ARA Findings Unblocked** (can be addressed after this item completes):
- AUTH-Q2: Scoped Permissions (RISK-SAFETY) — centralized identity enables scoped OAuth2 permissions
- AUTH-Q3: Action-Level Auth (RISK-SAFETY) — IAM provides authorization enforcement layer
- AUTH-Q4: Identity Propagation (RISK-QUALITY) — centralized identity enables token propagation
- AUTH-Q7: Identity Suspension (RISK-SAFETY) — centralized identity enables per-agent revocation

**Dual-Resolution Impact:** This single item resolves 3 MOD findings and 3 ARA findings (including 1 BLOCKER) across 30 services. This is the **highest-value dual-resolution item** in the portfolio — the Security Foundation simultaneously addresses the MOD security baseline gap and the ARA machine identity BLOCKER. Completing this item alone resolves 11 of 20 ARA BLOCKERs (55%) under the v5.1 tiered DATA-Q1 rubric.

---

#### 5. Observability Platform

**MOD Findings Resolved:**
- OPS-Q4: Log Aggregation — 28 services affected
- OPS-Q1: Distributed Tracing — 20 services affected

**ARA Findings Resolved:**
- OBS-Q1: Distributed Tracing (RISK-QUALITY) — 18 services affected
- OBS-Q2: Alerting on Error Rates (RISK-QUALITY) — 17 services affected
- AUTH-Q6: Immutable Audit Logging (RISK-SAFETY) — 17 services affected (partially — tracing component)

**ARA Findings Unblocked:**
- None — OBS findings are directly resolved

**Dual-Resolution Impact:** This single item resolves 2 MOD findings and 3 ARA findings across 28 services. Deploying centralized CloudWatch Logs, X-Ray/ADOT, and alerting simultaneously provides the MOD operational visibility and the ARA agent observability that both analyses require.

---

#### 6. CI/CD Enhancement

**MOD Findings Resolved:**
- INF-Q11: CI/CD Automation — 16 services affected
- SEC-Q7: Application Security Pipeline — 13 services affected

**ARA Findings Resolved:**
- ENG-Q2: CI/CD + Contract Tests (RISK-QUALITY) — 18 services affected

**ARA Findings Unblocked:**
- DISC-Q1: Schema Versioning (RISK-QUALITY) — CI/CD enables breaking-change detection in pipelines

**Dual-Resolution Impact:** This single item resolves 2 MOD findings and 1 ARA finding across 18 services. Adding deployment automation and API contract testing to GitHub Actions workflows addresses both the MOD CI/CD gap and the ARA engineering quality requirement simultaneously.

---

### ARA-Specific Remediation (After Phase 0)

These ARA findings have no MOD co-requisite or require agent-specific work beyond what MOD Phase 0 provides.
Address these after MOD Phase 0 completes.

#### 7. Credential Leakage in Agent-Facing API Endpoints (DATA-Q1, tiered)

**ARA Finding:** DATA-Q1: Sensitive Data Classification (BLOCKER) — 7 services affected under the v5.1 tiered rubric (down from 14 under the old binary rubric). Trigger is B1 (API response scoping), not B3 (formal classification metadata).
**Why Not Fully Covered by MOD Phase 0:** MOD Phase 0 establishes a data classification framework (DATA-Q1 MOD) and secrets management (SEC-Q5) at the *platform* level. The 7 remaining ARA BLOCKERs are specific *code-level leaks* in agent-facing API endpoints — a different class of problem that is not resolved by portfolio data governance.

| Service | Specific Code-Level Leak |
|---|---|
| Lidarr, Prowlarr, Radarr, Sonarr | `GET /api/v{1,3}/config/host` returns master `ApiKey`, admin `Password`, `SslCertPassword`, `ProxyPassword` unmasked. `HostConfigResource` bypasses the working `PrivacyLevel`/`SchemaBuilder` masking that correctly protects provider settings. |
| thingsboard | `GET /api/device/{deviceId}/credentials` returns `DeviceCredentials.credentialsValue` (access tokens, MQTT passwords, X.509 PEM) plaintext to CUSTOMER_USER or TENANT_ADMIN. No `@JsonIgnore`. |
| apache/druid | `GET /druid/indexer/v1/supervisor?full=true` serializes Kafka `consumerProperties` (SASL/SSL credentials) and Kinesis AWS credentials verbatim via `@JsonProperty`. No `PasswordProvider`-style abstraction. |
| conductor-oss/conductor | `HttpTask.java:138` persists request `Authorization` headers into task output via `task.addOutput("response", response.asMap())`. `WorkflowResource.getExecutionStatus()` returns full `input`/`output` payloads unredacted. |

**Remediation Action:**
1. **Servarr family (4 services, shared fix)**: Extend the existing `SchemaBuilder`/`PrivacyLevel` masking to `HostConfigResource` (plain C# properties today). A single multi-repo code change applies to all four apps. Estimated 1–2 weeks.
2. **thingsboard**: Apply `@JsonIgnore` to `DeviceCredentials.credentialsValue`; introduce a `DeviceCredentialsSummary` DTO that returns `credentialsType` only. Gate any value-revealing endpoint to TENANT_ADMIN + explicit "reveal" intent. Estimated 2–4 weeks.
3. **apache/druid**: Filter sensitive `consumerProperties` keys in Kafka/Kinesis supervisor spec serialization; annotate `awsAssumedRoleArn`/`awsExternalId` with `@JsonIgnore`. Longer-term: integrate with a secrets manager. Estimated 3–6 weeks.
4. **conductor**: Mask sensitive HTTP headers in `HttpTask.java:138` before `addOutput`; apply response-level field redaction on Task/Workflow REST DTOs via a Jackson `@JsonFilter`; enforce `WorkflowDef.maskedFields` at validation time. Estimated 3–6 weeks.

**Estimated Effort:** Low-to-Medium per service (1–6 weeks). Cumulative across all 7 BLOCKER repos: ~15–25 weeks of engineering time, parallelizable.
**Dependencies:** None — these are localized code changes, independent of MOD Phase 0. Resolution can proceed in parallel with MOD Security Foundation work.

**Additional services (not BLOCKER but related)**: FlowiseAI/Flowise and hapifhir/hapi-fhir resolve to DATA-Q1 = RISK-SAFETY under the tiered model — follow-up after BLOCKER remediation. Alluxio, Graylog2, scality/cloudserver, umami-software/umami, and ToolJet resolve to DATA-Q1 = INFO — no remediation required; formal classification metadata remains aspirational.

#### 8. API Documentation for Agent Discovery (API-Q1)

**ARA Finding:** API-Q1: Documented API Interface (BLOCKER) — 2 services affected (greenshot--greenshot, ToolJet--ToolJet)
**Why Not Covered by MOD Phase 0:** API-Q1 has no MOD co-requisite. This is a purely ARA-specific requirement for machine-discoverable API documentation.
**Remediation Action:**
1. **ToolJet**: Enable `@nestjs/swagger` module to auto-generate OpenAPI spec from existing NestJS controller decorators. Add `@ApiOperation` and `@ApiResponse` decorators. Publish spec at `/api/docs`. Estimated 1–2 weeks.
2. **Greenshot**: Evaluate agent integration requirements. If agent access is needed, build a CLI or local REST API wrapper around screenshot/annotation capabilities. Otherwise, descope from agent integration. Estimated 8–12 weeks if pursued.
**Estimated Effort:** Low for ToolJet, High for Greenshot
**Dependencies:** None

### Unified Sequence Summary

| # | Item | Source | MOD Findings Resolved | ARA Findings Resolved | ARA Findings Unblocked | Type |
|---|---|---|---|---|---|---|
| 1 | IaC Foundation | MOD Phase 0 | INF-Q10, INF-Q7 | ENG-Q1 | ENG-Q2 | Dual-resolution |
| 2 | Shared VPC Architecture | MOD Phase 0 | INF-Q5 | — | STATE-Q5, AUTH-Q3 | MOD only |
| 3 | EKS Cluster Setup | MOD Phase 0 | INF-Q1, INF-Q8 | — | STATE-Q5, API-Q3, AUTH-Q3 | MOD only |
| 4 | Security Foundation | MOD Phase 0 | SEC-Q1, SEC-Q4, SEC-Q5 | AUTH-Q1, AUTH-Q5, AUTH-Q6 | AUTH-Q2, Q3, Q4, Q7 | **Dual-resolution (highest value)** |
| 5 | Observability Platform | MOD Phase 0 | OPS-Q4, OPS-Q1 | OBS-Q1, OBS-Q2, AUTH-Q6 | — | Dual-resolution |
| 6 | CI/CD Enhancement | MOD Phase 0 | INF-Q11, SEC-Q7 | ENG-Q2 | DISC-Q1 | Dual-resolution |
| 7 | Data Classification | ARA-specific | — | DATA-Q1 | — | ARA only (BLOCKER) |
| 8 | API Documentation | ARA-specific | — | API-Q1 | — | ARA only (BLOCKER) |

**Total unified remediation items: 8** (6 Phase 0 dual/MOD + 2 ARA-specific)

---

## Section 5: Shared Findings Deduplication

These findings appear in both the portfolio ARA report and the portfolio MOD report.
They represent the same underlying gap viewed through different analysis lenses.
**Plan remediation once, not twice.**

### Shared Relationship Findings

These findings have a "Shared" relationship — one remediation action resolves both the ARA and MOD finding.

| # | ARA Finding | ARA Severity | MOD Finding | MOD Gap Services | Relationship | Deduplicated Remediation |
|---|---|---|---|---|---|---|
| 1 | AUTH-Q5: Credential Management | RISK-QUALITY (10 svc) | SEC-Q5: Secrets Management | 6 svc <2 | Shared | Migrate to AWS Secrets Manager with automated rotation — resolves both ARA credential management and MOD secrets management |
| 2 | API-Q2: Machine-Readable Spec | RISK-QUALITY (13 svc) | APP-Q5: Config Externalization | 8 svc <2 | Shared | Generate OpenAPI specs and externalize API configuration — resolves both ARA machine-readable API requirement and MOD configuration externalization |
| 3 | API-Q3: Structured Errors | RISK-QUALITY (16 svc) | APP-Q5: Config Externalization + INF-Q6: Container-Readiness | 31 svc <2 | Shared | Standardize RFC 7807 error responses via API Gateway — resolves ARA structured errors and MOD container-readiness/config gaps |
| 4 | OBS-Q1: Distributed Tracing | RISK-QUALITY (18 svc) | OPS-Q1: Distributed Tracing | 20 svc <2 | Shared | Deploy AWS X-Ray / ADOT across all services — identical finding in both analyses |
| 5 | OBS-Q2: Alerting | RISK-QUALITY (17 svc) | OPS-Q4: Log Aggregation | 28 svc <2 | Shared | Deploy centralized CloudWatch Logs with alerting — resolves both ARA alerting and MOD log aggregation |
| 6 | DISC-Q1: Schema Versioning | RISK-QUALITY (32 svc) | APP-Q5: Config Externalization | 8 svc <2 | Shared | Implement semantic versioning with breaking-change detection in CI — resolves both ARA schema versioning and MOD config externalization |
| 7 | ENG-Q1: Infra Governance | RISK-QUALITY (15 svc) | INF-Q10: IaC Coverage | 31 svc <2 | Shared | Standardize on AWS CDK or Terraform — identical finding in both analyses |

### MOD → ARA Prerequisite Findings

These findings have directional MOD → ARA relationships where both sides are flagged. The MOD finding must be resolved first, which then enables ARA remediation. While not "shared" in the same way, teams should recognize that MOD work directly enables ARA progress.

| # | ARA Finding | ARA Severity | MOD Finding | MOD Gap Services | Relationship | Sequencing Guidance |
|---|---|---|---|---|---|---|
| 8 | AUTH-Q1: Machine Identity | BLOCKER (11 svc) | SEC-Q3: Encryption in Transit + SEC-Q4: Dependency Vuln Mgmt | 20 svc <2 | MOD → ARA | Complete MOD Security Foundation first → then implement per-agent machine identity |
| 9 | AUTH-Q2: Scoped Permissions | RISK-SAFETY (14 svc) | SEC-Q3 + SEC-Q4 | 20 svc <2 | MOD → ARA | Complete MOD Security Foundation first → then configure fine-grained OAuth2 scopes |
| 10 | AUTH-Q3: Action-Level Auth | RISK-SAFETY (12 svc) | SEC-Q3 + INF-Q6: Container-Readiness | 31 svc <2 | MOD → ARA | Complete MOD Security Foundation + containerization → then implement per-action authorization |
| 11 | AUTH-Q4: Identity Propagation | RISK-QUALITY (8 svc) | SEC-Q4: Dependency Vuln Mgmt | 20 svc <2 | MOD → ARA | Complete MOD centralized identity → then implement token propagation headers |
| 12 | AUTH-Q6: Immutable Audit Logging | RISK-SAFETY (17 svc) | SEC-Q1: IAM + OPS-Q1: Distributed Tracing | 30 svc <2 | MOD → ARA | Complete MOD Security Foundation + Observability Platform → then implement immutable audit logs |
| 13 | AUTH-Q7: Identity Suspension | RISK-SAFETY (14 svc) | SEC-Q4: Dependency Vuln Mgmt | 20 svc <2 | MOD → ARA | Complete MOD centralized identity → then implement per-agent revocation capability |
| 14 | STATE-Q5: Rate Limiting | RISK-SAFETY (14 svc) | INF-Q6: Container-Readiness | 31 svc <2 | MOD → ARA | Complete MOD containerization + API Gateway → then configure per-agent rate limits |
| 15 | ENG-Q2: CI/CD + Contract Tests | RISK-QUALITY (18 svc) | INF-Q11: CI/CD Automation + OPS-Q6: Integration Testing | 16 svc <3 | MOD → ARA | Enhance MOD CI/CD pipelines → then add API contract testing for agent tool bindings |
| 16 | HITL-Q3: Sandbox/Staging | RISK-QUALITY (16 svc) | OPS-Q5: Deployment Strategy | 26 svc <2 | MOD → ARA | Implement MOD deployment strategy → then provision staging environments for agent testing |

### ARA Extends MOD Findings

| # | ARA Finding | ARA Severity | MOD Finding | MOD Gap Services | Relationship | Sequencing Guidance |
|---|---|---|---|---|---|---|
| 17 | DATA-Q1: Data Classification ⚡ (Tiered) | BLOCKER (7 svc, down from 14 under binary rubric) + RISK-SAFETY (2 svc) + INFO (5 svc) | DATA-Q1: Data Classification + SEC-Q5: Secrets Mgmt | 20 svc <2 | ARA extends MOD | For the 7 BLOCKER services, apply per-service masking fixes (Servarr `HostConfigResource`, thingsboard `DeviceCredentials`, druid supervisor specs, conductor HTTP-task output) — independent of MOD Phase 0. MOD data governance remains complementary but not blocking. |

### Deduplication Summary

- **17 findings** appear in both analyses (7 Shared + 9 MOD→ARA + 1 ARA extends MOD)
- **7 remediation items** can be fully consolidated (Shared relationship — plan once, not twice)
- **10 remediation items** have directional dependencies (MOD→ARA or ARA extends MOD — plan as a sequence, not as duplicates)
- **Estimated effort savings:** Teams avoid duplicating planning and execution for 7 shared infrastructure gaps. The 10 directional findings benefit from coordinated sequencing rather than independent planning.

> **Key Insight**: Every one of the 17 MOD-ARA mapping entries has both sides flagged in this portfolio. This is consistent with the portfolio's overall low maturity scores (MOD portfolio score: 1.99/4.0, SEC: 1.61, OPS: 1.53) — foundational gaps in modernization directly manifest as agentic readiness gaps. Addressing modernization is not optional for agentic AI adoption; it is a prerequisite.
