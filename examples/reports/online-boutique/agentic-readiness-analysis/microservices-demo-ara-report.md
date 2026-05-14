# Agentic Readiness Analysis Report

**Target**: services/microservices-demo
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: infrastructure-only
**Service Archetype**: N/A — infrastructure-only
**Agent Scope**: read-only
**Tags**: kubernetes, helm, terraform, istio, cicd, iac
**Context**: Root-level deployment and infrastructure configuration.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISKs**: 9 | **INFOs**: 4

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 30–90 days. The single blocker (AUTH-Q1: Istio AuthorizationPolicies disabled in Helm values) must be resolved to establish machine identity authentication across all services. The 9 RISKs cover observability, engineering maturity, and remaining auth gaps that are manageable with compensating controls.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK | 9 |
| INFO | 4 |
| N/A | 29 |
| Not Evaluated (extended) | 0 |
| **Total** | **43** |

**Core Questions Evaluated**: 14
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 0
**Questions N/A (repo_type: infrastructure-only)**: 29

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Istio AuthorizationPolicies are disabled globally (`authorizationPolicies.create: false` in `helm-chart/values.yaml` — analysis uses original code with this value set to false). The Helm chart templates define fine-grained AuthorizationPolicies for every service (restricting callers by service account principal and RPC path), but none are deployed because the global flag is false. NetworkPolicies are also disabled (`networkPolicies.create: false`). Sidecars are disabled (`sidecars.create: false` — analysis uses original code). Without AuthorizationPolicies, there is no mesh-level machine identity enforcement. Any pod in the cluster can call any service without presenting credentials.
- **Gap**: No machine identity authentication at the infrastructure layer. All AuthorizationPolicy templates exist but are gated by a disabled flag. The entire service mesh security posture is disabled.
- **Remediation**:
  - **Immediate**: Set `authorizationPolicies.create: true` in `helm-chart/values.yaml`. This single change deploys AuthorizationPolicies for all 10 services, enforcing mTLS-based caller identity via Istio service account principals.
  - **Target State**: AuthorizationPolicies enabled with agent-specific service accounts added to each policy. NetworkPolicies enabled as defense-in-depth. Sidecars enabled for egress control.
  - **Estimated Effort**: Low (single Helm value change deploys all policies)
  - **Dependencies**: All per-service AUTH-Q1 blockers are resolved by this single infrastructure change
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `networkPolicies.create: false`), `helm-chart/templates/*.yaml` (AuthorizationPolicy templates for all services gated by flag)

---

## RISKs — Proceed with Compensating Controls

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: The Helm chart templates define per-service AuthorizationPolicies with fine-grained caller restrictions. For example, `paymentservice.yaml` restricts to `checkoutservice` principal, `recommendationservice.yaml` restricts to `frontend` principal, `shippingservice.yaml` restricts to `frontend` and `checkoutservice` principals. Each policy specifies allowed RPC paths, methods (POST), and ports. K8s ServiceAccounts are created per service (`serviceAccounts.create: true`). However, all policies are disabled (`authorizationPolicies.create: false`). No agent-specific service accounts are defined in any template.
- **Gap**: Well-designed least-privilege policies exist but are not deployed. No agent-specific service accounts.
- **Compensating Controls**:
  - Enabling `authorizationPolicies.create: true` immediately deploys all per-service policies
  - ServiceAccounts already exist per service for Istio principal-based identity
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable AuthorizationPolicies. Add agent-specific K8s ServiceAccounts to each policy's `principals` list.
- **Evidence**: `helm-chart/templates/paymentservice.yaml` (AuthorizationPolicy restricts to checkoutservice), `helm-chart/templates/recommendationservice.yaml` (restricts to frontend), `helm-chart/values.yaml` (`serviceAccounts.create: true`, `authorizationPolicies.create: false`)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The AuthorizationPolicy templates define per-RPC path restrictions. For example, `adservice.yaml` allows only `/hipstershop.AdService/GetAds`, `paymentservice.yaml` allows only `/hipstershop.PaymentService/Charge`. Each policy specifies exact paths, methods, and ports. This is action-level authorization at the mesh layer. However, all policies are disabled.
- **Gap**: Action-level authorization is well-designed in templates but not deployed.
- **Compensating Controls**:
  - Enabling AuthorizationPolicies deploys per-RPC restrictions for all services
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable AuthorizationPolicies. The per-RPC path restrictions are already defined.
- **Evidence**: `helm-chart/templates/adservice.yaml` (path: /hipstershop.AdService/GetAds), `helm-chart/templates/paymentservice.yaml` (path: /hipstershop.PaymentService/Charge)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: No secrets management infrastructure is defined. No AWS Secrets Manager, no HashiCorp Vault, no K8s External Secrets Operator. Service environment variables contain only service addresses, ports, and feature flags — no secrets. The `cartDatabase` section in `values.yaml` defines a Redis connection string (`redis-cart:6379`) without authentication. No TLS for Redis. Terraform files define GKE cluster and Memorystore (Redis) but no secrets management resources.
- **Gap**: No secrets management infrastructure. Redis connection without authentication or TLS. No credential rotation framework.
- **Compensating Controls**:
  - Current services have no secrets to manage (simulated backends)
  - Istio mTLS (when enabled) provides inter-service encryption
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement K8s External Secrets Operator or AWS Secrets Manager integration. Add Redis authentication and TLS. Establish credential rotation policies.
- **Evidence**: `helm-chart/values.yaml` (`cartDatabase.connectionString: "redis-cart:6379"` — no auth), `terraform/memorystore.tf` (Redis without auth config)

### AUTH-Q6: Immutable Audit Logging

- **Severity**: RISK
- **Finding**: No centralized audit logging infrastructure is defined. No CloudWatch Logs, no S3 log archival, no Elasticsearch/OpenSearch. The OpenTelemetry Collector is defined (`opentelemetryCollector.create: true`) which can forward traces and metrics, but log forwarding is not configured. Tracing is disabled (`googleCloudOperations.tracing: false` in analysis context). No log retention policies. No immutable storage configuration.
- **Gap**: No centralized, immutable audit logging infrastructure. Logs are ephemeral container stdout across all services.
- **Compensating Controls**:
  - OpenTelemetry Collector exists and can be configured for log forwarding
  - GKE cluster logging (if enabled) provides some log retention
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Configure OpenTelemetry Collector for log forwarding to immutable store. Enable tracing. Define log retention policies. Implement S3 with Object Lock or CloudWatch Logs with retention.
- **Evidence**: `helm-chart/values.yaml` (`opentelemetryCollector.create: true`, `googleCloudOperations.tracing: false`), `helm-chart/templates/opentelemetry-collector.yaml`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism exists at the infrastructure level. AuthorizationPolicies (when enabled) provide the mechanism — removing a service account principal from a policy blocks access. However, this requires a Helm values change and redeployment. No real-time suspension capability (no API key revocation, no dynamic policy updates).
- **Gap**: No real-time agent suspension. Policy changes require redeployment.
- **Compensating Controls**:
  - AuthorizationPolicy updates via Helm provide eventual suspension
  - K8s NetworkPolicy (when enabled) can block specific pods
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement dynamic AuthorizationPolicy management (e.g., via Istio API or custom controller) for real-time agent suspension without full redeployment.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/*.yaml` (AuthorizationPolicy templates)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: The OpenTelemetry Collector is defined and deployed (`opentelemetryCollector.create: true`). Collector service address is injected into all service deployments as `COLLECTOR_SERVICE_ADDR`. However, tracing is disabled (`googleCloudOperations.tracing: false` in analysis context — `ENABLE_TRACING` env var not set). Individual services have OpenTelemetry SDK integration (paymentservice, recommendationservice, frontend) but it is inactive. The collector configuration exists but the pipeline is not active.
- **Gap**: Tracing infrastructure exists but is disabled. The full OpenTelemetry pipeline (collector + per-service SDKs) is ready but inactive.
- **Compensating Controls**:
  - OpenTelemetry Collector is deployed and ready
  - Per-service SDK integration exists — enabling requires only config changes
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Set `googleCloudOperations.tracing: true` in `values.yaml`. This enables `ENABLE_TRACING: "1"` across all services, activating the existing OpenTelemetry pipeline.
- **Evidence**: `helm-chart/values.yaml` (`opentelemetryCollector.create: true`, `googleCloudOperations.tracing: false`), `helm-chart/templates/opentelemetry-collector.yaml`

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting infrastructure is defined. No Prometheus alerting rules, no CloudWatch alarms, no PagerDuty/OpsGenie integration. The `kubernetes-manifests/monitoring-alerts.yaml` file exists but is part of the raw K8s manifests (not Helm). The Helm chart has no alerting configuration. Individual services have health probes but no error rate or latency alerting.
- **Gap**: No alerting infrastructure. Health probes provide basic availability only.
- **Compensating Controls**:
  - `monitoring-alerts.yaml` in kubernetes-manifests may provide alerting if deployed separately
  - Istio sidecar metrics can feed Prometheus
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Prometheus alerting rules to the Helm chart. Configure alerting for all services' error rates and p99 latency.
- **Evidence**: `helm-chart/values.yaml` (no alerting config), `kubernetes-manifests/monitoring-alerts.yaml` (exists but not in Helm)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Infrastructure is defined as Helm charts (`helm-chart/`) and Terraform (`terraform/`). The Helm chart defines all K8s resources (Deployments, Services, NetworkPolicies, Sidecars, AuthorizationPolicies) with configurable values. Terraform defines GKE cluster and Memorystore. GitHub Actions CI includes `helm-chart-ci.yaml` and `terraform-validate-ci.yaml`. PR-based review enforced. However, no drift detection — no ArgoCD, no Flux, no AWS Config rules.
- **Gap**: IaC exists with PR review and CI validation, but no drift detection.
- **Compensating Controls**:
  - Helm chart provides declarative infrastructure
  - CI validates Helm and Terraform on PRs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement GitOps with ArgoCD or Flux for drift detection and reconciliation.
- **Evidence**: `helm-chart/` (full Helm chart), `terraform/` (GKE + Memorystore), `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: CI/CD exists via GitHub Actions (`.github/workflows/`) and Cloud Build (`cloudbuild.yaml`). The PR workflow runs unit tests for some services (Go, C#), deploys to staging GKE via Skaffold, and runs smoke tests via load generator. Helm chart CI validates chart syntax. Terraform CI validates configuration. However, no API contract tests across services, no proto compatibility checks, no consumer-driven contract tests (Pact).
- **Gap**: CI/CD exists but no cross-service API contract testing. No proto breaking change detection.
- **Compensating Controls**:
  - Staging deployment with smoke tests provides basic end-to-end validation
  - Per-service unit tests validate individual service logic
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI for proto compatibility. Add cross-service contract tests. Add Pact or similar consumer-driven contract testing.
- **Evidence**: `.github/workflows/ci-pr.yaml` (staging deploy, smoke tests), `cloudbuild.yaml` (Skaffold deploy)

---

## INFOs — Architecture and Design Inputs

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Deployment uses Helm (`helm rollback` natively supported) and Skaffold via Cloud Build. K8s Deployments use standard rolling update strategy. No canary deployments, no blue/green, no automatic rollback triggers. The Helm chart version is 0.10.5. Rollback requires manual `helm rollback` or Skaffold redeployment.
- **Implication**: Manual rollback is available and functional. Automated rollback would improve operational safety.
- **Recommendation**: Implement Flagger or Argo Rollouts for automated canary deployments with rollback.
- **Evidence**: `helm-chart/Chart.yaml` (version 0.10.5), `cloudbuild.yaml` (Skaffold deploy), `skaffold.yaml`

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: Test coverage varies by service. Shippingservice has comprehensive unit tests. Frontend has utility package tests. Most other services have no tests. The CI pipeline runs available tests and staging smoke tests. For an infrastructure-only analysis, the relevant metric is whether infrastructure changes are tested — Helm chart CI and Terraform validation provide this.
- **Implication**: Infrastructure changes are validated in CI. Per-service test coverage is assessed in individual service reports.
- **Recommendation**: Add infrastructure integration tests (e.g., test that AuthorizationPolicies are correctly applied after Helm deploy).
- **Evidence**: `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/ci-pr.yaml`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: INFO
- **Finding**: The only persistent data store is Redis (cartservice database). Redis is configured as in-cluster (`cartDatabase.inClusterRedis.create: true`) with no encryption at rest, no authentication, and no TLS. Terraform defines a Memorystore (managed Redis) instance but the Helm chart defaults to in-cluster Redis. GKE node disk encryption depends on GCP configuration (default is encrypted). No explicit encryption-at-rest configuration in the Helm chart or Terraform.
- **Implication**: Redis data (cart contents) is not encrypted at rest. GKE node disks may be encrypted by default.
- **Recommendation**: Enable Redis authentication and TLS. Use Memorystore (managed Redis) with encryption at rest. Verify GKE node disk encryption.
- **Evidence**: `helm-chart/values.yaml` (`cartDatabase.type: redis`, `connectionString: "redis-cart:6379"`), `terraform/memorystore.tf`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics infrastructure. The OpenTelemetry Collector can forward metrics but no custom business metrics are defined at the infrastructure level. `googleCloudOperations.metrics: true` is set but individual services have no custom metrics (all `initStats()` are TODO stubs).
- **Implication**: Metrics infrastructure exists (OTel Collector) but no business metrics are published.
- **Recommendation**: Define business outcome metrics at the infrastructure level. Configure OTel Collector to forward custom metrics.
- **Evidence**: `helm-chart/values.yaml` (`googleCloudOperations.metrics: true`), `helm-chart/templates/opentelemetry-collector.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### API-Q2: Machine-Readable API Specification
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### API-Q3: Structured Error Responses
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### API-Q5: Structured Response Format
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### API-Q6: Asynchronous Operation Support
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### API-Q7: Event Emission for State Changes
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: AuthorizationPolicies disabled globally. All service AuthorizationPolicy templates exist but gated by `authorizationPolicies.create: false`. No mesh-level identity enforcement.
- **Gap**: No machine identity authentication at infrastructure layer.
- **Recommendation**: Set `authorizationPolicies.create: true`.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/*.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Per-service AuthorizationPolicies with fine-grained caller restrictions exist but are disabled. ServiceAccounts created per service.
- **Gap**: Policies exist but not deployed. No agent-specific accounts.
- **Recommendation**: Enable AuthorizationPolicies. Add agent-specific ServiceAccounts.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/*.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Per-RPC path restrictions defined in AuthorizationPolicy templates but disabled.
- **Gap**: Action-level auth designed but not deployed.
- **Recommendation**: Enable AuthorizationPolicies.
- **Evidence**: `helm-chart/templates/*.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets management infrastructure. Redis without auth or TLS. No External Secrets Operator.
- **Gap**: No credential management infrastructure.
- **Recommendation**: Implement External Secrets Operator. Add Redis auth and TLS.
- **Evidence**: `helm-chart/values.yaml` (Redis connection), `terraform/memorystore.tf`

#### AUTH-Q6: Immutable Audit Logging
- **Severity**: RISK
- **Finding**: No centralized audit logging. OTel Collector exists but log forwarding not configured. Tracing disabled.
- **Gap**: No immutable audit logging infrastructure.
- **Recommendation**: Configure OTel Collector for log forwarding. Enable tracing. Define retention policies.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/opentelemetry-collector.yaml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No real-time suspension. Policy changes require redeployment.
- **Gap**: No real-time agent suspension capability.
- **Recommendation**: Implement dynamic AuthorizationPolicy management.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/*.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### STATE-Q2: Queryable Current State
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DATA-Q3: Selective Query Support
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DATA-Q4: System of Record Designations
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DATA-Q6: PII Redaction in Logs
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DATA-Q7: Data Quality Awareness
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OTel Collector deployed but tracing disabled. Full pipeline ready but inactive.
- **Gap**: Tracing infrastructure exists but disabled.
- **Recommendation**: Set `googleCloudOperations.tracing: true`.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/opentelemetry-collector.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting infrastructure in Helm chart. monitoring-alerts.yaml exists in raw K8s manifests only.
- **Gap**: No alerting infrastructure.
- **Recommendation**: Add Prometheus alerting rules to Helm chart.
- **Evidence**: `helm-chart/values.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: OTel Collector can forward metrics. `googleCloudOperations.metrics: true`. No custom business metrics defined.
- **Gap**: Metrics infrastructure exists but no business metrics.
- **Recommendation**: Define business outcome metrics. Configure OTel Collector.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/opentelemetry-collector.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Helm charts and Terraform with CI validation and PR review. No drift detection.
- **Gap**: No drift detection.
- **Recommendation**: Implement GitOps with ArgoCD or Flux.
- **Evidence**: `helm-chart/`, `terraform/`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI/CD with staging deploy and smoke tests. No cross-service contract tests. No proto compatibility checks.
- **Gap**: No API contract testing.
- **Recommendation**: Add buf breaking. Add cross-service contract tests.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `cloudbuild.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Helm rollback available. Skaffold deploy. No automated rollback.
- **Gap**: No automated rollback.
- **Recommendation**: Implement Flagger or Argo Rollouts.
- **Evidence**: `helm-chart/Chart.yaml`, `cloudbuild.yaml`, `skaffold.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Infrastructure CI validates Helm and Terraform. Per-service test coverage varies.
- **Gap**: No infrastructure integration tests.
- **Recommendation**: Add infrastructure integration tests.
- **Evidence**: `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: Redis without encryption, auth, or TLS. GKE node encryption depends on GCP defaults.
- **Gap**: Redis data not encrypted at rest.
- **Recommendation**: Enable Redis auth and TLS. Use Memorystore with encryption.
- **Evidence**: `helm-chart/values.yaml` (Redis config), `terraform/memorystore.tf`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1, ENG-Q5 |
| `helm-chart/templates/*.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7 |
| `helm-chart/templates/opentelemetry-collector.yaml` | AUTH-Q6, OBS-Q1, OBS-Q3 |
| `helm-chart/Chart.yaml` | ENG-Q3 |
| `terraform/` | AUTH-Q5, ENG-Q1, ENG-Q5 |
| `terraform/memorystore.tf` | AUTH-Q5, ENG-Q5 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/helm-chart-ci.yaml` | ENG-Q1, ENG-Q4 |
| `.github/workflows/terraform-validate-ci.yaml` | ENG-Q1, ENG-Q4 |
| `cloudbuild.yaml` | ENG-Q2, ENG-Q3 |
| `skaffold.yaml` | ENG-Q3 |

### Kubernetes Manifests
| File | Questions Referenced |
|------|---------------------|
| `kubernetes-manifests/monitoring-alerts.yaml` | OBS-Q2 |