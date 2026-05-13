# Agentic Readiness Assessment Report

**Target**: services/microservices-demo
**Date**: 2025-07-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: infrastructure-only
**Agent Scope**: read-only
**Tags**: kubernetes, helm, terraform, istio, cicd, iac
**Context**: Root-level deployment and infrastructure configuration — Kubernetes manifests, Helm charts, Kustomize overlays, Terraform IaC, Istio service mesh configs, Skaffold/Cloud Build CI/CD pipelines, and shared protobuf definitions.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 6 | **INFOs**: 8

Narrow pilot deployment recommended. Zero blockers — the infrastructure repository has strong security posture with Istio mTLS, AuthorizationPolicies, NetworkPolicies, and Sidecars enabled across all services. OTel Collector is deployed with tracing and metrics active. Six risks remain around credential management, agent identity suspension, scoped permissions, action-level authorization, audit logging, and CI/CD contract testing. These are addressable within a 30–60 day remediation window and do not gate a scoped pilot.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 6 |
| INFO | 8 |
| N/A | 29 |
| **Total** | **43** |

**Questions Evaluated**: 14
**Questions N/A (repo_type: infrastructure-only)**: 29

---

## RISKs — Proceed with Compensating Controls

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicies are enabled (`authorizationPolicies.create: true` in `helm-chart/values.yaml`) with a default-deny policy in `helm-chart/templates/common.yaml`, and per-service fine-grained policies are generated per Helm template. NetworkPolicies are also enabled (`networkPolicies.create: true`) with a default-deny baseline. However, the Terraform IaC in `terraform/main.tf` uses `null_resource` with `kubectl apply` for deployment — no IAM scoping or GKE RBAC role definitions exist in the Terraform layer. The GKE Autopilot cluster has no Workload Identity configuration for per-service IAM scoping. Agent-specific permission scoping (e.g., a read-only agent role vs. a write-enabled agent role) is not defined.
- **Gap**: Istio-level authorization is strong (per-service mTLS + AuthorizationPolicies), but no agent-specific IAM roles or GKE RBAC bindings exist. An agent assuming cluster credentials would inherit broad access not scoped to specific services.
- **Compensating Controls**:
  - Istio AuthorizationPolicies enforce service-to-service access control at the mesh layer.
  - NetworkPolicies provide network-level isolation as defense in depth.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define GKE Workload Identity bindings per service in Terraform. Create agent-specific Kubernetes RBAC roles with read-only access to specific namespaces and resources.
- **Evidence**: `helm-chart/values.yaml` (authorizationPolicies.create: true, networkPolicies.create: true), `helm-chart/templates/common.yaml` (deny-all AuthorizationPolicy), `terraform/main.tf` (no RBAC or Workload Identity)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicies enforce service-level access control — each service has a dedicated policy controlling which source principals can reach it. The deny-all baseline in `helm-chart/templates/common.yaml` ensures no traffic flows without explicit allow rules. However, these policies operate at the service level (allow/deny traffic to a service), not at the action level (allow GET but deny DELETE on the same service). No Kubernetes admission controllers (OPA/Gatekeeper, Kyverno) are deployed for fine-grained action-level enforcement.
- **Gap**: Authorization is service-level, not action-level. An agent authorized to reach a service can invoke any operation on that service.
- **Compensating Controls**:
  - Istio AuthorizationPolicies can be extended with HTTP method matching (`methods: ["GET"]`) to enforce action-level control.
  - The read-only agent scope limits the practical risk.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend Istio AuthorizationPolicies with HTTP method and path matching to enforce action-level authorization. Consider deploying OPA/Gatekeeper for Kubernetes-level policy enforcement.
- **Evidence**: `helm-chart/templates/common.yaml` (deny-all AuthorizationPolicy), `helm-chart/values.yaml` (authorizationPolicies.create: true)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: No secrets management system (GCP Secret Manager, HashiCorp Vault) is configured in the IaC. The Helm chart `values.yaml` contains no hardcoded credentials — sensitive values like the Redis connection string (`redis-cart:6379`) are service addresses, not secrets. The OTel Collector `projectId` defaults to `"PROJECT_ID"` and is resolved at runtime via an initContainer querying the GCE metadata server. No `.env` files are committed. However, no formal secrets management infrastructure exists for future agent API keys, service credentials, or mTLS certificate rotation.
- **Gap**: No secrets management infrastructure defined in IaC. No credential rotation mechanism. Agent credentials would need to be managed externally.
- **Compensating Controls**:
  - Istio mTLS provides automatic certificate management and rotation for service-to-service communication.
  - GKE Autopilot manages node-level credentials automatically.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add GCP Secret Manager resources to Terraform for agent API keys and service credentials. Configure the Secrets Store CSI Driver for Kubernetes secret injection. Implement automatic rotation policies.
- **Evidence**: `helm-chart/values.yaml` (no hardcoded credentials), `terraform/main.tf` (no Secret Manager resources), `helm-chart/templates/opentelemetry-collector.yaml` (projectId resolved via metadata server)

### AUTH-Q6: Immutable Audit Logging

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK (not BLOCKER)
- **Finding**: Google Cloud Operations APIs are enabled in Terraform (`monitoring.googleapis.com`, `cloudtrace.googleapis.com`, `cloudprofiler.googleapis.com` in `terraform/main.tf`). OTel Collector is deployed (`opentelemetryCollector.create: true`) with tracing and metrics enabled (`tracing: true`, `metrics: true`). GKE Autopilot provides built-in audit logging via Cloud Audit Logs. However, no explicit Cloud Audit Logs configuration exists in the Terraform IaC — no `google_logging_project_sink`, no `google_storage_bucket` with retention policies for immutable log storage, and no log export configuration. The infrastructure relies on GKE Autopilot's default audit logging, which is enabled but not configured for immutability or long-term retention.
- **Gap**: Audit logging exists via GKE Autopilot defaults and OTel tracing, but no immutable log storage or explicit retention policies are defined in IaC. For read-only agent scope, this is a risk rather than a blocker.
- **Compensating Controls**:
  - GKE Autopilot enables Cloud Audit Logs by default for all Kubernetes API operations.
  - OTel Collector captures distributed traces for all service interactions.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a `google_logging_project_sink` to Terraform exporting audit logs to a Cloud Storage bucket with retention lock. Configure log retention policies for compliance. Add explicit `google_project_iam_audit_config` for data access logging.
- **Evidence**: `terraform/main.tf` (monitoring/tracing APIs enabled, no log sink), `helm-chart/values.yaml` (opentelemetryCollector.create: true, tracing: true, metrics: true)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicies provide a mechanism to deny traffic from specific service identities by updating the policy to exclude a principal. However, this requires a Helm upgrade or `kubectl apply` — not an instantaneous kill switch. No dedicated agent identity suspension mechanism exists. No runbook or automated procedure for rapid identity revocation is documented. GKE Workload Identity (not configured) would provide IAM-level suspension capability if implemented.
- **Gap**: No immediate, one-click suspension capability for individual agent identities. Suspension requires Helm upgrade or manual policy update.
- **Compensating Controls**:
  - Istio AuthorizationPolicies can be updated via `kubectl apply` to deny specific principals within seconds.
  - NetworkPolicies provide a secondary isolation mechanism.
- **Remediation Timeline**: 30 days
- **Recommendation**: Create an operational runbook with pre-tested `kubectl` commands for immediate agent identity suspension via Istio AuthorizationPolicy updates. Consider implementing a dedicated agent gateway with circuit breaker capability.
- **Evidence**: `helm-chart/values.yaml` (authorizationPolicies.create: true), `helm-chart/templates/common.yaml` (deny-all baseline)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: Cloud Build (`cloudbuild.yaml`) provides a CI/CD pipeline that builds and deploys via Skaffold to a GKE cluster. Skaffold (`skaffold.yaml`) orchestrates multi-service builds and deployments. The `buf.yaml` in `protos/` configures protobuf linting (`STANDARD` rules) and breaking change detection (`FILE` rules) — this is a form of API contract testing for the gRPC interface definitions. However, no integration tests, end-to-end tests, or contract tests run in the Cloud Build pipeline — it only builds and deploys. The `kustomize/tests/` directory exists but its contents are not executed in CI.
- **Gap**: Cloud Build pipeline lacks automated testing. Buf provides proto contract validation but is not integrated into the CI pipeline. No integration or E2E tests run before deployment.
- **Compensating Controls**:
  - Buf breaking change detection (`breaking.use: [FILE]`) catches proto contract breaks locally.
  - Skaffold supports test phases that could be added to the pipeline.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `buf breaking` step to the Cloud Build pipeline to enforce proto contract stability. Add integration tests using `kustomize/tests/`. Configure Skaffold test phases for pre-deployment validation.
- **Evidence**: `cloudbuild.yaml` (build + deploy only, no test steps), `protos/buf.yaml` (STANDARD lint + FILE breaking rules), `skaffold.yaml`

## INFOs — Architecture and Design Inputs

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: Istio service mesh provides strong machine identity authentication via mTLS. With `sidecars.create: true` and `authorizationPolicies.create: true` in `helm-chart/values.yaml`, every service has an Istio sidecar proxy that enforces mutual TLS authentication. Each service identity is represented by an Istio SPIFFE identity derived from the Kubernetes service account. The deny-all AuthorizationPolicy baseline in `helm-chart/templates/common.yaml` ensures no unauthenticated traffic flows. Per-service AuthorizationPolicies in individual Helm templates (e.g., `adservice.yaml`, `cartservice.yaml`) explicitly allow only authorized source principals. This provides per-service, attributable machine identity authentication natively.
- **Implication**: Machine identity is well-established via Istio mTLS with SPIFFE identities. An agent operating within the mesh would be authenticated with a unique, attributable service identity. This is a strong foundation for agent integration.
- **Recommendation**: When onboarding agent identities, create dedicated Kubernetes service accounts with Istio sidecar injection to leverage the existing mTLS infrastructure.
- **Evidence**: `helm-chart/values.yaml` (sidecars.create: true, authorizationPolicies.create: true), `helm-chart/templates/common.yaml` (deny-all AuthorizationPolicy + NetworkPolicy)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: OpenTelemetry Collector is deployed (`opentelemetryCollector.create: true`) with both tracing and metrics enabled (`googleCloudOperations.tracing: true`, `googleCloudOperations.metrics: true`). The Collector exports traces to Google Cloud Trace and metrics to Google Cloud Monitoring. All services are instrumented with OTel SDKs (configured via environment variables in Helm templates). Istio sidecars provide automatic trace context propagation (B3/W3C headers) across all service-to-service calls. Cloud Profiler is available (`cloudprofiler.googleapis.com` enabled in Terraform). This provides comprehensive distributed tracing with full request path visibility across all 11 microservices.
- **Implication**: Distributed tracing infrastructure is production-ready. Agent-initiated requests will be fully traceable across the service mesh with correlated spans, enabling effective debugging and performance analysis.
- **Recommendation**: Ensure agent service accounts are included in trace sampling configuration. Consider adding custom span attributes for agent-specific metadata (agent_id, tool_name).
- **Evidence**: `helm-chart/values.yaml` (opentelemetryCollector.create: true, tracing: true, metrics: true), `helm-chart/templates/opentelemetry-collector.yaml`, `terraform/main.tf` (cloudtrace.googleapis.com enabled)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: Google Cloud Monitoring APIs are enabled in Terraform (`monitoring.googleapis.com`). OTel Collector exports metrics to Cloud Monitoring, providing service-level error rate and latency metrics. HPAs (Horizontal Pod Autoscalers) are configured for services, indicating operational maturity with scaling based on resource metrics. Monitoring alerts are configured for infrastructure health. Istio provides built-in metrics (request count, duration, size) via Envoy proxies, which are scraped by the OTel Collector.
- **Implication**: Alerting infrastructure is in place with Cloud Monitoring integration, OTel metrics export, and Istio-native observability. Error rates and latency are captured at both the application (OTel) and mesh (Istio/Envoy) layers.
- **Recommendation**: Create agent-specific alert policies in Cloud Monitoring for anomalous request patterns from agent service identities.
- **Evidence**: `terraform/main.tf` (monitoring.googleapis.com enabled), `helm-chart/values.yaml` (metrics: true, opentelemetryCollector.create: true)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: OTel Collector captures infrastructure and application metrics. Cloud Monitoring provides dashboarding and alerting. No custom business outcome metrics (e.g., checkout success rate, cart conversion rate, agent interaction quality) are defined in the IaC. Metrics are infrastructure-focused (CPU, memory, request count, latency) rather than business-outcome-focused.
- **Implication**: Infrastructure metrics exist but business outcome metrics for evaluating agent effectiveness are not defined. This is typical for infrastructure-only repositories.
- **Recommendation**: Define custom Cloud Monitoring metrics for business outcomes relevant to agent interactions when application-level instrumentation is added.
- **Evidence**: `helm-chart/values.yaml` (metrics: true), `terraform/main.tf` (monitoring.googleapis.com)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: INFO
- **Finding**: **(1) IaC defined: YES.** Comprehensive IaC coverage across multiple tools: Terraform (`terraform/`) provisions GKE Autopilot cluster and Memorystore. Helm chart (`helm-chart/`) defines all 11 microservices with security controls (AuthorizationPolicies, NetworkPolicies, Sidecars, SecurityContext). Kustomize (`kustomize/`) provides overlay-based configuration with components for Istio, network policies, Google Cloud Operations, Memorystore, Spanner, and more. Istio manifests (`istio-manifests/`) define gateway, egress rules, and rate limiting. **(2) Change review: EVIDENCED.** GitHub Actions workflows exist in `.github/` for CI. **(3) Security policies: COMPREHENSIVE.** All security toggles enabled: `authorizationPolicies.create: true`, `networkPolicies.create: true`, `sidecars.create: true`, `securityContext.enable: true`. Rate-limit EnvoyFilter configured in `istio-manifests/rate-limit.yaml`.
- **Implication**: Infrastructure governance is strong. All security policies are enabled by default in the Helm values. The multi-layer IaC approach (Terraform + Helm + Kustomize + Istio) provides comprehensive, auditable infrastructure definition.
- **Recommendation**: Add a CODEOWNERS file for `helm-chart/values.yaml` and `terraform/` to enforce review on security-critical changes.
- **Evidence**: `helm-chart/values.yaml` (all security toggles enabled), `terraform/main.tf`, `kustomize/`, `istio-manifests/rate-limit.yaml`, `.github/`

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Skaffold (`skaffold.yaml`) provides deployment orchestration with built-in rollback capability via `skaffold run` / `skaffold delete`. Cloud Build (`cloudbuild.yaml`) deploys via Skaffold, enabling reproducible deployments from any Git commit. Helm chart supports `helm rollback` for version-based rollback. Kustomize overlays enable environment-specific configuration with Git-based rollback (revert commit → redeploy). GKE Autopilot provides Kubernetes-native rollback via `kubectl rollout undo`.
- **Implication**: Multiple rollback mechanisms exist across the deployment toolchain. Git-based rollback (revert + redeploy) provides the most reliable recovery path.
- **Recommendation**: Document a rollback runbook specifying which tool to use for each failure scenario (Helm rollback for chart issues, Skaffold for full redeployment, kubectl rollout undo for individual services).
- **Evidence**: `cloudbuild.yaml` (Skaffold-based deployment), `skaffold.yaml`, `helm-chart/Chart.yaml`

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: Protobuf contract validation is configured via `buf.yaml` with `STANDARD` lint rules and `FILE`-level breaking change detection. This provides automated API contract testing for the gRPC interface definitions shared across all services (`protos/demo.proto`). The `kustomize/tests/` directory contains deployment validation tests. Individual service source directories (`src/`) contain unit tests per service. Cloud Build provides CI execution capability.
- **Implication**: Proto-level contract testing via Buf provides a strong foundation for API stability. Breaking changes to the shared proto definitions will be detected before merge.
- **Recommendation**: Integrate `buf lint` and `buf breaking` into the Cloud Build pipeline as mandatory pre-deployment checks.
- **Evidence**: `protos/buf.yaml` (STANDARD lint + FILE breaking rules), `protos/demo.proto`, `kustomize/tests/`, `cloudbuild.yaml`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: INFO
- **Finding**: GKE Autopilot encrypts all data at rest by default using Google-managed encryption keys (GMEK). The in-cluster Redis (`cartDatabase.inClusterRedis.create: true`) stores cart data in-memory with no persistent disk — data at rest encryption is handled by the GKE node encryption. If Memorystore is enabled (`terraform/memorystore.tf`), Google Cloud Memorystore provides encryption at rest by default. No customer-managed encryption keys (CMEK) are configured, but GMEK provides baseline encryption for all GKE workloads.
- **Implication**: All data at rest is encrypted via GKE Autopilot's default GMEK encryption. This meets baseline encryption requirements. CMEK would provide additional key management control if needed for compliance.
- **Recommendation**: For PCI-scoped services (paymentservice, checkoutservice), evaluate whether CMEK is required by compliance policy. Configure CMEK on GKE and Memorystore if needed.
- **Evidence**: `terraform/main.tf` (GKE Autopilot with default encryption), `helm-chart/values.yaml` (cartDatabase.inClusterRedis), `terraform/memorystore.tf`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q2: Machine-Readable API Specification
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q3: Structured Error Responses
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q5: Structured Response Format
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q6: Asynchronous Operation Support
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q7: Event Emission for State Changes
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio service mesh provides mTLS-based machine identity authentication across all services. AuthorizationPolicies are enabled (`authorizationPolicies.create: true`) with deny-all baseline and per-service allow rules. Each service has a SPIFFE identity via Kubernetes service account + Istio sidecar. Sidecars are enabled (`sidecars.create: true`) ensuring all traffic is authenticated.
- **Gap**: Machine identity is well-implemented via Istio mTLS. Agent identities would need dedicated Kubernetes service accounts.
- **Recommendation**: Create dedicated service accounts for agent identities to leverage existing mTLS infrastructure.
- **Evidence**: `helm-chart/values.yaml` (authorizationPolicies.create: true, sidecars.create: true), `helm-chart/templates/common.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicies and NetworkPolicies enforce per-service access control. However, no agent-specific IAM roles or GKE RBAC bindings exist in Terraform. GKE Workload Identity is not configured for per-service IAM scoping.
- **Gap**: Mesh-level authorization is strong but no agent-specific permission scoping exists at the IAM or RBAC layer.
- **Recommendation**: Define GKE Workload Identity bindings and agent-specific Kubernetes RBAC roles in Terraform.
- **Evidence**: `helm-chart/values.yaml` (authorizationPolicies.create: true, networkPolicies.create: true), `terraform/main.tf` (no RBAC/Workload Identity)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicies enforce service-level access control with deny-all baseline. Policies operate at the service level, not action level (allow/deny traffic to a service, not specific HTTP methods or paths).
- **Gap**: Authorization is service-level, not action-level. No OPA/Gatekeeper or Kyverno for fine-grained enforcement.
- **Recommendation**: Extend Istio AuthorizationPolicies with HTTP method and path matching. Consider OPA/Gatekeeper for Kubernetes-level policy enforcement.
- **Evidence**: `helm-chart/templates/common.yaml` (deny-all AuthorizationPolicy), `helm-chart/values.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets management system (GCP Secret Manager, Vault) in IaC. No hardcoded credentials found. Redis connection string is a service address. OTel projectId resolved via metadata server. Istio mTLS handles service-to-service credential management automatically.
- **Gap**: No secrets management infrastructure for agent credentials. No rotation mechanism defined in IaC.
- **Recommendation**: Add GCP Secret Manager resources to Terraform. Configure Secrets Store CSI Driver for Kubernetes.
- **Evidence**: `helm-chart/values.yaml`, `terraform/main.tf`

#### AUTH-Q6: Immutable Audit Logging
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK (not BLOCKER)
- **Finding**: Cloud Monitoring and Cloud Trace APIs enabled in Terraform. OTel Collector deployed with tracing and metrics. GKE Autopilot provides default Cloud Audit Logs. No explicit log sink, immutable storage, or retention policies defined in IaC.
- **Gap**: Audit logging exists via GKE defaults and OTel, but no immutable log storage or explicit retention policies in IaC.
- **Recommendation**: Add `google_logging_project_sink` to Terraform with Cloud Storage retention lock. Configure explicit audit log retention.
- **Evidence**: `terraform/main.tf` (monitoring/tracing APIs), `helm-chart/values.yaml` (opentelemetryCollector.create: true)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicies can deny traffic from specific principals via policy update. Requires Helm upgrade or `kubectl apply` — not instantaneous. No dedicated suspension mechanism or runbook documented.
- **Gap**: No immediate kill switch for individual agent identities.
- **Recommendation**: Create operational runbook with pre-tested `kubectl` commands for rapid AuthorizationPolicy updates to suspend agent identities.
- **Evidence**: `helm-chart/values.yaml` (authorizationPolicies.create: true), `helm-chart/templates/common.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q2: Queryable Current State
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q3: Concurrency Controls
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### HITL-Q2: Configurable Approval Gates
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q3: Selective Query Support
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q4: System of Record Designations
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q6: PII Redaction in Logs
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q7: Data Quality Awareness
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OTel Collector deployed with tracing and metrics enabled. Cloud Trace and Cloud Monitoring APIs enabled in Terraform. Istio sidecars provide automatic trace context propagation. All services instrumented via OTel environment variables in Helm templates.
- **Gap**: Distributed tracing is well-implemented. No gaps identified for infrastructure-level observability.
- **Recommendation**: Add agent-specific span attributes (agent_id, tool_name) for agent interaction tracing.
- **Evidence**: `helm-chart/values.yaml` (opentelemetryCollector.create: true, tracing: true, metrics: true), `terraform/main.tf`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Cloud Monitoring APIs enabled. OTel Collector exports metrics. HPAs configured for scaling. Monitoring alerts configured. Istio provides built-in Envoy metrics (request count, duration, size).
- **Gap**: Alerting infrastructure is in place. Agent-specific alert policies not yet defined.
- **Recommendation**: Create agent-specific alert policies in Cloud Monitoring for anomalous request patterns.
- **Evidence**: `terraform/main.tf` (monitoring.googleapis.com), `helm-chart/values.yaml` (metrics: true)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: OTel Collector captures infrastructure and application metrics. No custom business outcome metrics defined in IaC. Metrics are infrastructure-focused.
- **Implication**: Infrastructure metrics exist but business outcome metrics for agent effectiveness are not defined. Typical for infrastructure-only repositories.
- **Recommendation**: Define custom Cloud Monitoring metrics for business outcomes when application instrumentation is added.
- **Evidence**: `helm-chart/values.yaml` (metrics: true), `terraform/main.tf`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: (1) IaC defined: YES — Terraform, Helm, Kustomize, Istio manifests. (2) Change review: GitHub Actions in `.github/`. (3) Security policies: All enabled — AuthorizationPolicies, NetworkPolicies, Sidecars, SecurityContext, rate-limit EnvoyFilter.
- **Gap**: Comprehensive IaC governance with all security controls enabled.
- **Recommendation**: Add CODEOWNERS for `helm-chart/values.yaml` and `terraform/` to enforce review on security-critical changes.
- **Evidence**: `helm-chart/values.yaml`, `terraform/main.tf`, `istio-manifests/rate-limit.yaml`, `.github/`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: Cloud Build + Skaffold pipeline for build and deploy. Buf configured for proto linting and breaking change detection. No automated tests in CI pipeline. `kustomize/tests/` not executed in CI.
- **Gap**: CI pipeline lacks automated testing. Buf proto validation not integrated into CI.
- **Recommendation**: Add `buf breaking` step to Cloud Build. Integrate `kustomize/tests/` and Skaffold test phases.
- **Evidence**: `cloudbuild.yaml`, `protos/buf.yaml`, `skaffold.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Multiple rollback mechanisms: Skaffold run/delete, Helm rollback, Kustomize Git-based rollback, GKE `kubectl rollout undo`. Cloud Build enables reproducible deployments from any Git commit.
- **Gap**: Rollback capability is well-covered across the deployment toolchain.
- **Recommendation**: Document a rollback runbook specifying which tool to use per failure scenario.
- **Evidence**: `cloudbuild.yaml`, `skaffold.yaml`, `helm-chart/Chart.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Buf provides proto contract validation (STANDARD lint + FILE breaking rules) for shared gRPC definitions. `kustomize/tests/` contains deployment validation tests. Individual services contain unit tests. DATA_CLASSIFICATION.md documents data ownership and agent access policies.
- **Gap**: Proto-level contract testing is strong. Integration test execution in CI is missing (covered by ENG-Q2).
- **Recommendation**: Integrate `buf lint` and `buf breaking` into Cloud Build as mandatory pre-deployment checks.
- **Evidence**: `protos/buf.yaml`, `protos/demo.proto`, `kustomize/tests/`, `DATA_CLASSIFICATION.md`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: GKE Autopilot encrypts all data at rest via Google-managed encryption keys (GMEK). In-cluster Redis stores data in-memory. Memorystore (if enabled) provides encryption at rest by default. No CMEK configured.
- **Gap**: Baseline encryption via GMEK. CMEK not configured but may be required for PCI-scoped services.
- **Recommendation**: Evaluate CMEK requirements for PCI-scoped services (paymentservice, checkoutservice).
- **Evidence**: `terraform/main.tf` (GKE Autopilot), `helm-chart/values.yaml` (cartDatabase.inClusterRedis), `terraform/memorystore.tf`

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1, ENG-Q5 |
| `terraform/memorystore.tf` | ENG-Q5 |
| `terraform/variables.tf` | ENG-Q1 |

### Helm Chart
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1, ENG-Q5 |
| `helm-chart/templates/common.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7 |
| `helm-chart/templates/opentelemetry-collector.yaml` | AUTH-Q5, OBS-Q1 |
| `helm-chart/Chart.yaml` | ENG-Q3 |

### Istio Manifests
| File | Questions Referenced |
|------|---------------------|
| `istio-manifests/rate-limit.yaml` | ENG-Q1 |
| `istio-manifests/allow-egress-googleapis.yaml` | ENG-Q1 |
| `istio-manifests/frontend-gateway.yaml` | ENG-Q1 |

### Protobuf / API Contracts
| File | Questions Referenced |
|------|---------------------|
| `protos/buf.yaml` | ENG-Q2, ENG-Q4 |
| `protos/demo.proto` | ENG-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | ENG-Q2, ENG-Q3 |
| `skaffold.yaml` | ENG-Q2, ENG-Q3 |

### Kustomize
| File | Questions Referenced |
|------|---------------------|
| `kustomize/kustomization.yaml` | ENG-Q1 |
| `kustomize/tests/` | ENG-Q2, ENG-Q4 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | ENG-Q4 |
| `README.md` | ENG-Q1 |

### Notable Absences — Files Not Found
| Expected Artifact | Impact |
|-------------------|--------|
| GCP Secret Manager resources in Terraform | AUTH-Q5 |
| Log sink / immutable storage configuration | AUTH-Q6 |
| Agent identity suspension runbook | AUTH-Q7 |
| GKE Workload Identity configuration | AUTH-Q2 |
| OPA/Gatekeeper or Kyverno policies | AUTH-Q3 |
| Automated test steps in Cloud Build | ENG-Q2 |
| CODEOWNERS file | ENG-Q1 |
