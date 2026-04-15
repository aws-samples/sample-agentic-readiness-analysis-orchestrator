# Agentic Readiness Assessment Report

**Target**: ./services/microservices-demo
**Date**: 2025-07-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: infrastructure-only
**Agent Scope**: read-only
**Tags**: kubernetes, helm, terraform, istio, cicd, iac
**Context**: Root-level deployment and infrastructure configuration — Kubernetes manifests, Helm charts, Kustomize overlays, Terraform IaC, Istio service mesh configs, Skaffold/Cloud Build CI/CD pipelines, and shared protobuf definitions.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISKs**: 12 | **INFOs**: 2

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK | 12 |
| INFO | 2 |
| N/A | 34 |
| **Total** | **49** |

**Questions Evaluated**: 15
**Questions N/A (repo_type: infrastructure-only)**: 34

---

## BLOCKERs — Must Resolve Before Agent Deployment

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: Comprehensive NetworkPolicy definitions exist in `kustomize/components/network-policies/`: a `deny-all` baseline policy and 13 per-service policies with specific pod selectors, ingress sources, and port restrictions (e.g., `network-policy-cartservice.yaml` allows ingress only from `frontend` and `checkoutservice` on port 7070). The Helm chart supports `networkPolicies.create` which generates equivalent policies. Istio service mesh configs define Gateway (`istio-manifests/frontend-gateway.yaml`), VirtualService (`istio-manifests/frontend.yaml`), ServiceEntry (`istio-manifests/allow-egress-googleapis.yaml`), and AuthorizationPolicy (in Helm templates). **However**, network policies are disabled by default: `networkPolicies.create: false` in `helm-chart/values.yaml` and `# - components/network-policies` is commented out in `kustomize/kustomization.yaml`. The Istio Gateway accepts `hosts: ["*"]` on HTTP port 80 with no TLS. No CORS configuration was found anywhere. While the policies are documented and discoverable in IaC, the disabled-by-default state combined with a permissive Gateway and absent CORS means the agent-facing integration surface has no network security enforcement in place.
- **Gap**: Network policies are comprehensively defined but disabled by default — no enforcement without explicit opt-in. No CORS configuration. Istio Gateway is permissive (HTTP, wildcard hosts, no TLS). The integration surface agents would traverse is unsecured.
- **Remediation**:
  - **Immediate**: Enable network policies by uncommenting `components/network-policies` in `kustomize/kustomization.yaml` or setting `networkPolicies.create: true` in Helm values. Configure TLS on the Istio Gateway.
  - **Target State**: Network policies enabled as mandatory baseline for all environments. Istio Gateway configured with TLS and specific host restrictions. CORS policy defined for agent-facing endpoints.
  - **Estimated Effort**: Low (14–30 days — policies already exist, only need enablement and TLS/CORS additions)
  - **Dependencies**: AUTH-Q3 (Istio AuthorizationPolicies are also disabled by default — enable together)
- **Evidence**: `kustomize/components/network-policies/kustomization.yaml`, `kustomize/components/network-policies/network-policy-deny-all.yaml`, `kustomize/components/network-policies/network-policy-cartservice.yaml`, `helm-chart/values.yaml` (networkPolicies.create: false), `istio-manifests/frontend-gateway.yaml` (hosts: *, HTTP), `.github/workflows/ci-pr.yaml` (skaffold -p network-policies)

---

## RISKs — Proceed with Compensating Controls

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: The GKE service account (`gke-clusters-service-account`) defined in `.github/terraform/main.tf` has four scoped IAM roles: `roles/monitoring.metricWriter`, `roles/logging.logWriter`, `roles/monitoring.viewer`, and `roles/stackdriver.resourceMetadata.writer`. These follow least-privilege principles for the GKE node identity. No wildcard `Action: "*"` or `Resource: "*"` patterns were found. However, no agent-specific IAM role or policy is defined — an agent would need its own dedicated service account with separately scoped permissions.
- **Gap**: No agent-specific IAM role or policy is provisioned. The current service account is scoped for GKE workload operations (monitoring, logging), not for agent-initiated API access to the deployed services.
- **Compensating Controls**:
  - Create a dedicated GCP IAM service account for agent access with read-only permissions scoped to the specific APIs the agent will consume
  - Use GKE Workload Identity to bind agent Kubernetes ServiceAccounts to minimal GCP IAM roles
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a Terraform module for agent-specific service accounts with narrowly scoped IAM roles. Use the existing per-service K8s ServiceAccount pattern as a model.
- **Evidence**: `.github/terraform/main.tf` (IAM roles), `kubernetes-manifests/frontend.yaml` (ServiceAccount), `helm-chart/values.yaml` (serviceAccounts.create)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy resources are defined in the Helm chart (`helm-chart/templates/common.yaml`, `helm-chart/templates/frontend.yaml`) with method-level controls (methods: GET, POST) and port-level restrictions (ports: "8080"). A deny-all baseline AuthorizationPolicy is defined in `helm-chart/templates/common.yaml`. However, `authorizationPolicies.create` is set to `false` by default in `helm-chart/values.yaml`. When enabled, the policies enforce principal-based access with specific service account identities (e.g., `cluster.local/ns/<namespace>/sa/loadgenerator`).
- **Gap**: Action-level authorization via Istio is available as infrastructure configuration but disabled by default. No enforcement without explicit opt-in.
- **Compensating Controls**:
  - Enable `authorizationPolicies.create: true` in Helm chart values for environments where agents will operate
  - Use the Kustomize `service-mesh-istio` component to enforce Istio policies alongside network policies
- **Remediation Timeline**: 30 days (enable existing policies)
- **Recommendation**: Enable Istio AuthorizationPolicies as a mandatory baseline for agent-facing environments. Set `authorizationPolicies.create: true` in production values.
- **Evidence**: `helm-chart/values.yaml` (authorizationPolicies.create: false), `helm-chart/templates/common.yaml` (deny-all AuthorizationPolicy), `helm-chart/templates/frontend.yaml` (method/port-level AuthorizationPolicy)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No secrets management system (GCP Secret Manager, HashiCorp Vault) is configured in any Terraform or Kubernetes manifest. The `terraform/terraform.tfvars` file contains a placeholder `gcp_project_id = "<project_id_here>"` — not a hardcoded credential. No hardcoded passwords, API keys, or secrets were detected. The GCS bucket for Terraform state in `.github/terraform/main.tf` uses `public_access_prevention: "enforced"` and `versioning.enabled: true` but has no encryption configuration. The Redis instance in `terraform/memorystore.tf` has no `auth_enabled` setting. Credentials rely on GCP IAM workload identity implicitly.
- **Gap**: No formal secrets management system is provisioned in IaC. No credential rotation mechanism is defined. Redis (Memorystore) does not have authentication enabled.
- **Compensating Controls**:
  - Use GCP Workload Identity for service-to-service authentication (avoiding static credentials)
  - Enable Memorystore AUTH for Redis connections
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add GCP Secret Manager resources to Terraform for any credentials that agents would require. Enable `auth_enabled = true` on `google_redis_instance`. Define rotation schedules for any static credentials.
- **Evidence**: `terraform/terraform.tfvars` (placeholder project ID), `terraform/memorystore.tf` (no auth_enabled), `.github/terraform/main.tf` (GCS bucket without encryption block)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Finding**: No Cloud Audit Logs, CloudTrail, or immutable log storage configuration was found in any Terraform file or Kubernetes manifest. The GKE service account has `roles/logging.logWriter` enabling application log ingestion to Cloud Logging, but no explicit audit log configuration or retention policies are defined. The GCS bucket for Terraform state has `versioning.enabled: true` but this is for state management, not audit log immutability. No log sink, log retention, or tamper-evident logging resources are provisioned.
- **Gap**: No audit logging configuration for agent actions. No immutable log storage. No log retention policies.
- **Compensating Controls**:
  - GCP Cloud Audit Logs are enabled by default for GKE Admin Activity — verify this is active at the project level
  - Add Terraform resources for explicit Cloud Logging sinks with locked retention policies
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Terraform resources for: (1) Cloud Logging log sink with retention lock, (2) Cloud Storage bucket with retention policy for audit log archival, (3) Organization policy to enforce audit log retention.
- **Evidence**: `.github/terraform/main.tf` (logging.logWriter role but no audit config), `terraform/main.tf` (no logging resources), absence of any audit log resources across all Terraform files

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: Individual Kubernetes ServiceAccounts can be deleted or modified per-service (each microservice has its own SA in `kubernetes-manifests/*.yaml`). The GCP IAM service account in `.github/terraform/main.tf` can be disabled via the GCP IAM API. However, no automated kill-switch, suspension runbook, or emergency revocation mechanism is defined in the IaC or CI/CD pipelines.
- **Gap**: No automated agent identity suspension mechanism. Revocation requires manual IAM or kubectl intervention.
- **Compensating Controls**:
  - Document a runbook for disabling agent ServiceAccounts via `kubectl delete serviceaccount` and `gcloud iam service-accounts disable`
  - Pre-provision a script or CI/CD step that can be triggered to revoke agent access
- **Remediation Timeline**: 30 days
- **Recommendation**: Create an IaC-managed emergency revocation mechanism — e.g., a Terraform variable `agent_enabled` that controls the agent's ServiceAccount and IAM bindings, allowing a single `terraform apply` to suspend agent access.
- **Evidence**: `kubernetes-manifests/frontend.yaml` (ServiceAccount per service), `.github/terraform/main.tf` (google_service_account resource)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: An OpenTelemetry Collector is defined in `kustomize/components/google-cloud-operations/otel-collector.yaml` with OTLP receiver → Google Cloud exporter pipelines for both traces and metrics. The `kustomize/components/google-cloud-operations/kustomization.yaml` patches `COLLECTOR_SERVICE_ADDR`, `OTEL_SERVICE_NAME`, and `ENABLE_TRACING` environment variables into 7 service deployments (checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice). The Helm chart supports this via `opentelemetryCollector.create` and `googleCloudOperations.tracing` flags. Terraform enables `monitoring.googleapis.com`, `cloudtrace.googleapis.com`, and `cloudprofiler.googleapis.com` APIs. **However**, the google-cloud-operations component is commented out in `kustomize/kustomization.yaml` and `opentelemetryCollector.create: false` / `googleCloudOperations.tracing: false` in `helm-chart/values.yaml`. No structured logging (JSON format) or correlation ID configuration was found.
- **Gap**: Distributed tracing infrastructure exists but is disabled by default. No structured logging configuration. No correlation ID propagation.
- **Compensating Controls**:
  - Enable the `google-cloud-operations` Kustomize component by uncommenting it in `kustomize/kustomization.yaml`
  - Set `opentelemetryCollector.create: true` and `googleCloudOperations.tracing: true` in Helm values for agent-facing environments
- **Remediation Timeline**: 14–30 days (enable existing infrastructure)
- **Recommendation**: Enable the existing OpenTelemetry Collector configuration as a mandatory component for agent-facing environments. Add structured logging configuration to service deployments.
- **Evidence**: `kustomize/components/google-cloud-operations/otel-collector.yaml`, `kustomize/components/google-cloud-operations/kustomization.yaml`, `helm-chart/values.yaml` (opentelemetryCollector.create: false), `terraform/main.tf` (API enablement)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No Cloud Monitoring alert policies, alerting thresholds, PagerDuty/OpsGenie integration, or SLO-based alerting configuration was found in any Terraform file, Kubernetes manifest, or CI/CD pipeline. The `monitoring.googleapis.com` API is enabled in `terraform/main.tf` but no alerting resources (e.g., `google_monitoring_alert_policy`) are provisioned. The Helm chart and Kustomize overlays contain no alerting definitions.
- **Gap**: Complete absence of alerting configuration. No error rate or latency alerts for any service.
- **Compensating Controls**:
  - Create Cloud Monitoring alert policies manually in the GCP Console while IaC alerting is being developed
  - Use GKE Autopilot built-in metrics for basic uptime monitoring
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Terraform resources for `google_monitoring_alert_policy` covering: (1) 5xx error rate > threshold per service, (2) P95 latency > threshold per service, (3) pod restart count anomaly. Configure notification channels (email, PagerDuty, or Cloud Pub/Sub).
- **Evidence**: `terraform/main.tf` (monitoring API enabled, no alert resources), absence of `google_monitoring_alert_policy` across all Terraform files

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: (1) **IaC Defined**: ✅ Yes — Infrastructure is comprehensively defined as code: Terraform in `terraform/` (GKE cluster, Memorystore) and `.github/terraform/` (CI/CD infrastructure, IAM, GCS), Kubernetes manifests, Helm chart, and Kustomize overlays. (2) **Peer Review**: ✅ Yes — `.github/CODEOWNERS` assigns `@GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver` as default code owners for all files. CI validates Terraform (`terraform-validate-ci.yaml`), Helm (`helm-chart-ci.yaml`), Kustomize (`kustomize-build-ci.yaml`), and manifests (`kubevious-manifests-ci.yaml`) on PRs. (3) **Drift Detection**: ❌ No — No drift detection mechanism found. No Terraform Cloud, no `google_organization_policy`, no Config Connector, no scheduled `terraform plan` comparison.
- **Gap**: Drift detection is absent. 2 of 3 governance sub-checks pass.
- **Compensating Controls**:
  - Run `terraform plan` on a schedule (e.g., daily cron via GitHub Actions) and alert on drift
  - Use GCP Config Connector or Config Validator for continuous compliance checks
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a scheduled GitHub Actions workflow that runs `terraform plan` against production state and creates an issue or alert if drift is detected.
- **Evidence**: `terraform/main.tf`, `.github/terraform/main.tf`, `.github/CODEOWNERS`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml`, `.github/workflows/kubevious-manifests-ci.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: Comprehensive CI/CD pipelines exist: `ci-pr.yaml` runs Go unit tests (shippingservice, productcatalogservice, frontend/validator), C# unit tests (cartservice), GKE deployment tests, and smoke tests (loadgenerator-based end-to-end verification). `helm-chart-ci.yaml` runs `helm lint --strict` and template rendering tests for multiple configurations (default, gRPC health probes, Spanner, ASM, Memorystore TLS). `kustomize-build-ci.yaml` validates Kustomize builds. `terraform-validate-ci.yaml` runs `terraform init` and `terraform validate`. `kubevious-manifests-ci.yaml` validates kubernetes-manifests, helm-chart, and kustomize using Kubevious CLI. However, no API contract testing (Pact, OpenAPI validation), schema comparison, or breaking change detection was found.
- **Gap**: No API contract testing or breaking change detection. CI/CD validates infrastructure configuration but does not catch API contract regressions.
- **Compensating Controls**:
  - The loadgenerator-based smoke test catches gross functional regressions (non-zero error count fails the build)
  - Protobuf schema in `protos/demo.proto` can be used to implement proto-level breaking change detection
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add proto breaking change detection (e.g., `buf breaking`) to CI pipelines for the `protos/demo.proto` schema. Consider adding API contract tests using the protobuf definitions.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/kubevious-manifests-ci.yaml`, `protos/demo.proto`

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: Deployments use `skaffold run` (`skaffold.yaml`, `cloudbuild.yaml`) which performs forward-only deployment via `kubectl apply`. No automated rollback mechanism was found: no blue/green deployment, no canary configuration, no `helm rollback` steps, no CodeDeploy triggers, no feature flags, and no traffic shifting configuration. The CI/CD cleanup workflow (`.github/workflows/cleanup.yaml`) deletes PR namespaces on PR close but this is environment cleanup, not rollback. GKE Autopilot supports `kubectl rollout undo` natively but this is not automated in any pipeline.
- **Gap**: No automated rollback mechanism in deployment pipelines. Recovery relies on manual `kubectl rollout undo` or re-running Skaffold with a previous image tag.
- **Compensating Controls**:
  - Use `kubectl rollout undo deployment/<name>` as a manual rollback procedure
  - The Helm chart supports `helm rollback` if Helm-based deployment is used instead of Skaffold
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add rollback steps to CI/CD pipelines. Options: (1) Add `skaffold run` with the previous git commit's images as a rollback step, (2) Switch to Helm-based deployment with `helm upgrade --atomic` for automatic rollback on failure, (3) Implement canary deployment using Istio VirtualService traffic splitting.
- **Evidence**: `skaffold.yaml` (skaffold run, no rollback), `cloudbuild.yaml` (forward-only deploy), `.github/workflows/cleanup.yaml` (namespace cleanup only)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: CI pipelines include: Go unit tests for `shippingservice`, `productcatalogservice`, and `frontend/validator` (`ci-pr.yaml`); C# unit tests for `cartservice` (`ci-pr.yaml`); and loadgenerator-based smoke tests that deploy the full stack to GKE, wait for pods, and verify the loadgenerator produces 50+ requests with 0 errors. Helm chart CI tests template rendering for multiple configurations. No dedicated API test suites (Postman/Newman, pytest API tests, REST Assured, gRPC-specific test frameworks), no contract tests, and no integration test directories were found.
- **Gap**: No dedicated API-level test coverage. Smoke tests validate end-to-end availability but do not test individual API endpoints, error responses, or edge cases.
- **Compensating Controls**:
  - The loadgenerator smoke test provides basic end-to-end coverage verifying all services are reachable and functional
  - Unit tests in service source code (referenced by CI pipelines) cover internal logic
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add gRPC-level API tests using the protobuf service definitions in `protos/demo.proto`. Use tools like `grpcurl` or `ghz` for endpoint-level validation in CI.
- **Evidence**: `.github/workflows/ci-pr.yaml` (Go tests, C# tests, smoke tests), `.github/workflows/ci-main.yaml`, `protos/demo.proto` (service definitions)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: The `google_redis_instance.redis-cart` in `terraform/memorystore.tf` has no encryption configuration — no `customer_managed_key`, no `transit_encryption_mode`. The `google_storage_bucket.terraform_state_storage_bucket` in `.github/terraform/main.tf` has no `encryption` block or `default_kms_key_name`. The `google_container_cluster` in both Terraform directories has no database encryption configuration. The in-cluster Redis (`kubernetes-manifests/cartservice.yaml`) uses an `emptyDir` volume with no encryption. GCP provides Google-managed encryption by default for GCS and Memorystore, but no customer-managed KMS keys (CMEK) are configured.
- **Gap**: No customer-managed encryption at rest (CMEK). Relies entirely on GCP Google-managed default encryption. No explicit encryption configuration in IaC.
- **Compensating Controls**:
  - GCP provides Google-managed encryption by default for GCS, Memorystore, and GKE persistent volumes — data is encrypted at rest, but with Google-managed keys
  - For most non-regulated workloads, Google-managed encryption meets baseline requirements
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For regulated data or enhanced security posture, add CMEK configuration: (1) Create `google_kms_key_ring` and `google_kms_crypto_key` in Terraform, (2) Add `encryption { default_kms_key_name }` to the GCS bucket, (3) Add `customer_managed_key` to the Memorystore instance, (4) Configure GKE application-layer secrets encryption.
- **Evidence**: `terraform/memorystore.tf` (no encryption config), `.github/terraform/main.tf` (GCS bucket without encryption block), `kubernetes-manifests/cartservice.yaml` (emptyDir volume)

---

## INFOs — Architecture and Design Inputs

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: Machine identity authentication is well-supported through the existing infrastructure patterns. A dedicated GCP IAM service account (`gke-clusters-service-account`) is defined in `.github/terraform/main.tf` with scoped IAM role bindings. Per-microservice Kubernetes ServiceAccounts are provisioned for all 11 services (adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, loadgenerator, paymentservice, productcatalogservice, recommendationservice, shippingservice) in `kubernetes-manifests/*.yaml`. The Helm chart supports `serviceAccounts.create: true` with customizable annotations (for Workload Identity binding). The GKE Autopilot cluster uses the custom service account via `cluster_autoscaling.auto_provisioning_defaults.service_account`. An agent would follow this established pattern — creating its own GCP IAM service account and Kubernetes ServiceAccount with Workload Identity Federation.
- **Implication**: The machine identity pattern is established and extensible. Creating an agent-specific service account requires minimal effort — add a `google_service_account` resource to Terraform and a K8s ServiceAccount to the manifests. Workload Identity Federation can bind them for seamless authentication.
- **Recommendation**: When provisioning agent access, create a dedicated `google_service_account` for the agent with Workload Identity annotation on a corresponding Kubernetes ServiceAccount. Follow the existing per-service pattern.
- **Evidence**: `.github/terraform/main.tf` (google_service_account, IAM member bindings), `kubernetes-manifests/frontend.yaml` (ServiceAccount), `kubernetes-manifests/cartservice.yaml` (ServiceAccount), `helm-chart/values.yaml` (serviceAccounts.create: true)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics, business KPI dashboards, or custom metric publishing configuration was found in any IaC or Kubernetes manifest. The OpenTelemetry Collector pipeline (when enabled) exports infrastructure traces and system-level metrics to Google Cloud, but no business-specific metrics (e.g., order completion rate, cart conversion rate, payment success rate) are defined. The `monitoring.googleapis.com` API is enabled in Terraform but only infrastructure metrics are collected.
- **Implication**: Without business outcome metrics, there is no way to measure whether agent-initiated interactions produce positive business results. When agents begin consuming these services, business-level metrics should be defined to measure agent effectiveness.
- **Recommendation**: Define custom Cloud Monitoring metrics for key business outcomes: order completion rate, cart abandonment rate, payment success rate, and recommendation click-through rate. These can be published via the OTel Collector's metrics pipeline.
- **Evidence**: `terraform/main.tf` (monitoring API enabled), `kustomize/components/google-cloud-operations/otel-collector.yaml` (infrastructure metrics only)

---

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

#### API-Q5: API Versioning and Deprecation
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q6: Structured Response Format
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q7: Asynchronous Operation Support
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q8: Event Emission for State Changes
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q10: API Latency Profile
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Machine identity authentication is well-supported. A dedicated GCP IAM service account (`gke-clusters-service-account`) is defined in `.github/terraform/main.tf` with scoped IAM role bindings (`roles/monitoring.metricWriter`, `roles/logging.logWriter`, `roles/monitoring.viewer`, `roles/stackdriver.resourceMetadata.writer`). Per-microservice Kubernetes ServiceAccounts are provisioned for all 11 services in `kubernetes-manifests/*.yaml`. The Helm chart supports `serviceAccounts.create: true` with customizable annotations. The GKE Autopilot cluster uses the custom SA via `cluster_autoscaling.auto_provisioning_defaults.service_account`. The service account email provides principal attribution in IAM audit logs.
- **Gap**: No agent-specific service account is pre-provisioned. No Workload Identity Federation binding is configured. However, the infrastructure pattern is established and extensible.
- **Recommendation**: Create a dedicated `google_service_account` for agent access with Workload Identity annotation on a corresponding Kubernetes ServiceAccount. Follow the existing per-service pattern.
- **Evidence**: `.github/terraform/main.tf` (google_service_account, IAM member bindings), `kubernetes-manifests/frontend.yaml` (ServiceAccount), `helm-chart/values.yaml` (serviceAccounts.create: true)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: The GKE service account has four scoped IAM roles: `roles/monitoring.metricWriter`, `roles/logging.logWriter`, `roles/monitoring.viewer`, `roles/stackdriver.resourceMetadata.writer`. No wildcard permissions. Per-service K8s ServiceAccounts provide namespace-scoped identity. No agent-specific IAM role or policy is defined.
- **Gap**: No agent-specific IAM role or policy provisioned. Agent would need its own scoped permissions.
- **Recommendation**: Define a Terraform module for agent-specific service accounts with narrowly scoped IAM roles.
- **Evidence**: `.github/terraform/main.tf` (IAM roles), `kubernetes-manifests/frontend.yaml` (ServiceAccount)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy resources with method-level controls (methods: GET, POST) and port-level restrictions are defined in Helm chart templates. Deny-all baseline AuthorizationPolicy in `helm-chart/templates/common.yaml`. However, `authorizationPolicies.create` is `false` by default.
- **Gap**: Action-level authorization available but disabled by default.
- **Recommendation**: Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true`) for agent-facing environments.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/common.yaml`, `helm-chart/templates/frontend.yaml`

#### AUTH-Q4: Identity Propagation
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No secrets management system (GCP Secret Manager, Vault) configured. No hardcoded credentials detected. `terraform/terraform.tfvars` uses placeholder values. Redis Memorystore has no `auth_enabled`. Credentials rely on implicit GCP IAM workload identity.
- **Gap**: No formal secrets management or credential rotation mechanism in IaC. Redis without authentication.
- **Recommendation**: Add GCP Secret Manager resources. Enable `auth_enabled = true` on Memorystore. Define rotation schedules.
- **Evidence**: `terraform/terraform.tfvars`, `terraform/memorystore.tf`, `.github/terraform/main.tf`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No Cloud Audit Logs configuration, immutable log storage, or log retention policies found in Terraform or Kubernetes manifests. GKE SA has `roles/logging.logWriter` for application logs but no explicit audit configuration. GCS bucket has `versioning.enabled: true` for Terraform state only.
- **Gap**: No audit logging configuration. No immutable log storage. No log retention policies.
- **Recommendation**: Add Terraform resources for Cloud Logging sinks with retention lock and GCS buckets with retention policies for audit archival.
- **Evidence**: `.github/terraform/main.tf` (logging.logWriter role), `terraform/main.tf` (no logging resources)

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: K8s ServiceAccounts can be individually deleted. GCP IAM service accounts can be disabled via API. No automated kill-switch or suspension mechanism in IaC or CI/CD.
- **Gap**: No automated agent identity suspension mechanism. Requires manual intervention.
- **Recommendation**: Create an IaC-managed emergency revocation mechanism (e.g., Terraform variable `agent_enabled`).
- **Evidence**: `kubernetes-manifests/frontend.yaml` (ServiceAccount), `.github/terraform/main.tf` (google_service_account)

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

#### DATA-Q5: Reliable Timestamps
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q6: Data Freshness Signaling
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q7: PII Redaction in Logs
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q8: Data Quality Awareness
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

#### DISC-Q4: Data Lineage
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry Collector defined in `kustomize/components/google-cloud-operations/otel-collector.yaml` with OTLP → Google Cloud exporter for traces and metrics. Kustomize patches enable tracing for 7 services. Helm chart supports `opentelemetryCollector.create` and `googleCloudOperations.tracing`. Terraform enables `cloudtrace.googleapis.com` API. **Disabled by default**: component is commented out in `kustomize/kustomization.yaml`; `opentelemetryCollector.create: false` in Helm values. No structured logging or correlation ID configuration.
- **Gap**: Tracing infrastructure exists but disabled by default. No structured logging. No correlation IDs.
- **Recommendation**: Enable the google-cloud-operations Kustomize component and set `opentelemetryCollector.create: true` for agent-facing environments.
- **Evidence**: `kustomize/components/google-cloud-operations/otel-collector.yaml`, `kustomize/components/google-cloud-operations/kustomization.yaml`, `helm-chart/values.yaml`, `terraform/main.tf`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No Cloud Monitoring alert policies, alerting thresholds, or notification channels found in any Terraform or Kubernetes manifest. `monitoring.googleapis.com` API is enabled but no `google_monitoring_alert_policy` resources are provisioned.
- **Gap**: Complete absence of alerting configuration.
- **Recommendation**: Add Terraform `google_monitoring_alert_policy` for 5xx error rates, P95 latency, and pod restart anomalies per service.
- **Evidence**: `terraform/main.tf` (monitoring API enabled), absence of alert policy resources

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics, KPI dashboards, or business metric publishing found. OTel pipeline (when enabled) exports infrastructure metrics only.
- **Gap**: No business outcome metrics defined.
- **Recommendation**: Define custom Cloud Monitoring metrics for business outcomes (order completion, cart conversion, payment success rates).
- **Evidence**: `terraform/main.tf`, `kustomize/components/google-cloud-operations/otel-collector.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: (1) IaC: ✅ Terraform, K8s manifests, Helm, Kustomize. (2) Peer Review: ✅ CODEOWNERS + CI validation (terraform validate, helm lint, kustomize build, kubevious). (3) Drift Detection: ❌ Not configured.
- **Gap**: Drift detection absent. 2 of 3 sub-checks pass.
- **Recommendation**: Add scheduled `terraform plan` GitHub Action for drift detection.
- **Evidence**: `terraform/main.tf`, `.github/terraform/main.tf`, `.github/CODEOWNERS`, `.github/workflows/terraform-validate-ci.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: Comprehensive CI/CD: Go/C# unit tests, GKE deployment tests, loadgenerator smoke tests, helm lint, kustomize build, terraform validate, kubevious manifests validation. No API contract testing (Pact, OpenAPI validation) or breaking change detection.
- **Gap**: No API contract testing or breaking change detection.
- **Recommendation**: Add proto breaking change detection (`buf breaking`) for `protos/demo.proto`.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `protos/demo.proto`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Forward-only deployment via `skaffold run`. No automated rollback: no blue/green, no canary, no helm rollback, no feature flags. Manual `kubectl rollout undo` is possible but not automated.
- **Gap**: No automated rollback mechanism.
- **Recommendation**: Implement `helm upgrade --atomic` or Istio canary deployment for automatic rollback on failure.
- **Evidence**: `skaffold.yaml`, `cloudbuild.yaml`, `.github/workflows/cleanup.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Go unit tests (3 services), C# unit tests (cartservice), loadgenerator smoke tests. No dedicated API test suites, no contract tests.
- **Gap**: No API-level test coverage beyond smoke tests.
- **Recommendation**: Add gRPC API tests using `protos/demo.proto` service definitions with `grpcurl` or `ghz`.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `protos/demo.proto`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No CMEK configuration. Memorystore Redis has no encryption config. GCS bucket has no encryption block. GKE has no database encryption. In-cluster Redis uses `emptyDir`. GCP provides Google-managed default encryption.
- **Gap**: No customer-managed encryption at rest. Relies on GCP Google-managed encryption.
- **Recommendation**: Add CMEK via `google_kms_key_ring` and `google_kms_crypto_key` in Terraform for GCS, Memorystore, and GKE secrets.
- **Evidence**: `terraform/memorystore.tf`, `.github/terraform/main.tf`, `kubernetes-manifests/cartservice.yaml`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: Comprehensive NetworkPolicies defined in `kustomize/components/network-policies/` (deny-all baseline + 13 per-service policies). Helm chart supports `networkPolicies.create`. Istio configs define Gateway, VirtualService, ServiceEntry, AuthorizationPolicy. **Disabled by default** (`networkPolicies.create: false`, component commented out). Istio Gateway accepts `hosts: ["*"]` on HTTP port 80 with no TLS. No CORS configuration. CI deploys with `-p network-policies` validating policies work. While the policies are documented and discoverable in IaC, the disabled-by-default state combined with a permissive Gateway and absent CORS means the agent-facing integration surface has no network security enforcement in place.
- **Gap**: Network policies disabled by default — no enforcement. No CORS. Permissive Gateway (HTTP, wildcard hosts, no TLS). The integration surface agents would traverse is unsecured.
- **Recommendation**: (1) Enable network policies as mandatory baseline for all environments. (2) Configure TLS on Istio Gateway with specific host restrictions. (3) Add CORS configuration for agent-facing endpoints.
- **Evidence**: `kustomize/components/network-policies/`, `helm-chart/values.yaml`, `istio-manifests/frontend-gateway.yaml`, `.github/workflows/ci-pr.yaml`

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/main.tf` | AUTH-Q1, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1 |
| `terraform/providers.tf` | ENG-Q1 |
| `terraform/variables.tf` | AUTH-Q6 |
| `terraform/memorystore.tf` | AUTH-Q6, ENG-Q5 |
| `terraform/terraform.tfvars` | AUTH-Q6 |
| `.github/terraform/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q6, AUTH-Q7, AUTH-Q8, ENG-Q1, ENG-Q5 |
| `.github/terraform/variables.tf` | ENG-Q1 |
| `.github/terraform/versions.tf` | ENG-Q1 |

### Kubernetes Manifests
| File | Questions Referenced |
|------|---------------------|
| `kubernetes-manifests/frontend.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q8 |
| `kubernetes-manifests/cartservice.yaml` | AUTH-Q1, ENG-Q5 |
| `kubernetes-manifests/checkoutservice.yaml` | AUTH-Q1 |
| `kubernetes-manifests/kustomization.yaml` | ENG-Q1 |
| `kustomize/kustomization.yaml` | OBS-Q1, ENG-Q6 |
| `kustomize/base/kustomization.yaml` | ENG-Q1 |

### Helm Chart
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/Chart.yaml` | ENG-Q1 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q3, AUTH-Q6, OBS-Q1, ENG-Q6 |
| `helm-chart/templates/common.yaml` | AUTH-Q3, ENG-Q6 |
| `helm-chart/templates/frontend.yaml` | AUTH-Q3, ENG-Q6 |
| `helm-chart/templates/opentelemetry-collector.yaml` | OBS-Q1 |

### Istio Service Mesh
| File | Questions Referenced |
|------|---------------------|
| `istio-manifests/frontend-gateway.yaml` | AUTH-Q3, ENG-Q6 |
| `istio-manifests/allow-egress-googleapis.yaml` | ENG-Q6 |
| `istio-manifests/frontend.yaml` | AUTH-Q3 |
| `kustomize/components/service-mesh-istio/kustomization.yaml` | AUTH-Q3, ENG-Q6 |

### Network Policies
| File | Questions Referenced |
|------|---------------------|
| `kustomize/components/network-policies/kustomization.yaml` | ENG-Q6 |
| `kustomize/components/network-policies/network-policy-deny-all.yaml` | ENG-Q6 |
| `kustomize/components/network-policies/network-policy-cartservice.yaml` | ENG-Q6 |
| `kustomize/components/network-policies/network-policy-frontend.yaml` | ENG-Q6 |
| `kustomize/components/network-policies/network-policy-checkoutservice.yaml` | ENG-Q6 |

### Observability
| File | Questions Referenced |
|------|---------------------|
| `kustomize/components/google-cloud-operations/kustomization.yaml` | OBS-Q1 |
| `kustomize/components/google-cloud-operations/otel-collector.yaml` | OBS-Q1, OBS-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q6 |
| `.github/workflows/ci-main.yaml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/helm-chart-ci.yaml` | ENG-Q1, ENG-Q2 |
| `.github/workflows/kustomize-build-ci.yaml` | ENG-Q1, ENG-Q2 |
| `.github/workflows/terraform-validate-ci.yaml` | ENG-Q1, ENG-Q2 |
| `.github/workflows/kubevious-manifests-ci.yaml` | ENG-Q1, ENG-Q2 |
| `.github/workflows/cleanup.yaml` | ENG-Q3 |
| `cloudbuild.yaml` | ENG-Q3 |
| `skaffold.yaml` | ENG-Q3 |
| `.github/CODEOWNERS` | ENG-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | ENG-Q2, ENG-Q4 |
