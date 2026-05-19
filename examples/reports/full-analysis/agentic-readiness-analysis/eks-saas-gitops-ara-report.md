# Agentic Readiness Analysis Report

**Target**: services/eks-saas-gitops
**Date**: 2026-05-18
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: infrastructure-only
**Agent Scope**: read-only
**Priority**: P1
**Tags**: eks, gitops, terraform, saas, infrastructure
**Context**: EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings, everything that is not serverless will run here, EKS will be the centralized platform.

**Surface flags**:
- has_persistent_data_store: true (DynamoDB tables, SQS queues defined in Terraform)
- has_http_rpc_surface: true (Flask microservices with HTTP endpoints)
- has_auth_surface: true (IRSA roles, IAM policies defined)
- has_write_operations: true (DynamoDB PutItem, SQS SendMessage)
- has_logging_of_user_data: false (basic Python logging, no user data captured)

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 3 | **RISK-QUALITY**: 5 | **INFOs**: 1

This repo has 0 BLOCKER findings and 3 RISK-SAFETY findings. Rule matched: "0 BLOCKER, ≥3 RISK-SAFETY → Pilot-Ready (Safety Concerns)".

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 3 |
| RISK-QUALITY | 5 |
| INFO | 1 |
| N/A | 29 |
| Not Evaluated (extended) | 5 |
| **Total** | **43** |

**Core Questions Evaluated**: 14 (reduced from 25 by infrastructure-only N/A mapping)
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 5
**Questions N/A (repo_type: infrastructure-only)**: 29
**Service Archetype**: N/A (infrastructure-only repository — archetype classification applies only to application repos)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q5: Credential Management — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Credentials are stored in AWS SSM Parameter Store (SecureString) which is a valid secrets management service. Random password generation is used for Gitea admin credentials. However, no credential rotation is configured — SSM Parameter Store does not provide automatic rotation like AWS Secrets Manager. The `gitea-ci-test/variables.tf` contains a `sensitive = true` marked variable for passwords but relies on manual management.
- **Gap**: No automatic credential rotation mechanism. SSM Parameter Store lacks native rotation support (unlike Secrets Manager). No evidence of rotation schedules or Lambda-based rotation functions.
- **Compensating Controls**:
  - Use short-lived IRSA tokens (already in place for pod-level access) as the primary credential mechanism, limiting exposure of long-lived credentials
  - Implement manual rotation runbook with documented cadence until Secrets Manager migration
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate sensitive credentials (Gitea admin password, Flux tokens) from SSM Parameter Store to AWS Secrets Manager with automatic rotation enabled. Define rotation Lambda functions for non-IAM credentials.
- **Evidence**: `terraform/workshop/main.tf` (lines 168–180: random_password + SSM SecureString), `terraform/gitea-ci-test/variables.tf` (line 35: sensitive variable), `terraform/modules/gitea/main.tf` (SSM parameter reads)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (would be BLOCKER if write-enabled)
- **Finding**: No CloudTrail configuration found in any Terraform module. No `aws_cloudtrail` resources defined. No immutable log storage (S3 with Object Lock). No CloudWatch Logs retention policies for audit purposes. The only logging present is basic Python `logging` in microservices and Flux CD's internal reconciliation logs.
- **Gap**: No audit trail infrastructure defined. Cannot attribute actions to specific principals in an immutable, tamper-evident log store.
- **Compensating Controls**:
  - AWS CloudTrail may be enabled at the organization/account level outside this repository — verify with the platform team
  - EKS control plane logging (audit logs) may be enabled via the EKS module but is not explicitly configured in the code
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `aws_cloudtrail` resource with S3 bucket (Object Lock enabled), CloudTrail log file validation, and multi-region trail. Enable EKS control plane logging (audit, authenticator) in the EKS module configuration.
- **Evidence**: `terraform/` (all .tf files searched — no `aws_cloudtrail` resource found), `terraform/workshop/main.tf` (EKS module with no `cluster_enabled_log_types` parameter)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: IAM roles are defined in Terraform (IRSA roles for each service). While IAM inherently supports role deletion/policy detachment, there is no mechanism for immediate identity suspension without a full Terraform plan/apply cycle. No automated anomaly-triggered suspension, no API key revocation endpoint, no service account disable automation.
- **Gap**: No immediate suspension mechanism for agent identities. Revoking an IRSA role requires modifying Terraform state and re-applying, which is not an immediate response capability.
- **Compensating Controls**:
  - IAM inline deny policies can be manually attached to a role for immediate effect without Terraform
  - Kubernetes ServiceAccount deletion provides immediate pod-level credential revocation within the cluster
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a runbook or automation (Lambda + EventBridge) that can immediately attach a deny-all inline policy to any IRSA role upon anomaly detection. Consider AWS IAM Access Analyzer for continuous monitoring of role usage patterns.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (IRSA role definitions), `terraform/modules/tenant-apps/main.tf` (per-tenant IRSA roles)

### RISK-QUALITY — Address as Capacity Allows

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (X-Ray, OpenTelemetry) is configured in the repository. Microservices use basic Python `logging` module without structured JSON output or correlation IDs. No `traceparent` header propagation. Metrics Server is deployed for HPA but provides no request-level tracing. Flux Capacitor provides GitOps visibility but not request tracing.
- **Gap**: No distributed tracing infrastructure. No structured logging. No correlation ID propagation between services.
- **Compensating Controls**:
  - EKS supports AWS X-Ray daemon as a DaemonSet — can be added as an infrastructure add-on via Flux HelmRelease
  - OpenTelemetry Collector can be deployed as a Helm chart with minimal application changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy OpenTelemetry Collector as a Flux HelmRelease. Add ADOT (AWS Distro for OpenTelemetry) sidecar or DaemonSet. Update microservices to emit structured JSON logs with request_id correlation.
- **Evidence**: `gitops/infrastructure/production/` (no tracing HelmRelease), `tenant-microservices/consumer/consumer.py` (basic logging), `tenant-microservices/producer/producer.py` (basic logging)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting infrastructure configured. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. Kubecost provides cost metrics only. README references Amazon Managed Grafana and Prometheus but these are not defined in the repository's IaC or GitOps manifests.
- **Gap**: No alerting thresholds for error rates, latency, or availability. No anomaly detection.
- **Compensating Controls**:
  - Kubecost provides cost anomaly detection which may surface some operational issues indirectly
  - EKS provides basic CloudWatch metrics for node/pod health at the cluster level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy kube-prometheus-stack via Flux HelmRelease with pre-configured alerting rules for error rates (5xx), latency (p99), and pod restart counts. Integrate with SNS for alert routing.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml` (cost only), `gitops/infrastructure/production/` (no alerting HelmRelease)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is comprehensively defined as IaC (Terraform for AWS, Flux CD Kustomize/HelmReleases for Kubernetes). Drift detection is partially covered — Flux CD continuously reconciles Kubernetes state and TF Controller auto-applies tenant Terraform. However, no evidence of: (1) branch protection or PR review requirements for IaC changes in Gitea, (2) AWS Config rules for drift detection on AWS resources outside Kubernetes, (3) `terraform plan` review gates in CI.
- **Gap**: No peer review enforcement on IaC changes. No AWS Config drift detection. No plan-review gates in CI/CD.
- **Compensating Controls**:
  - Flux CD reconciliation provides self-healing for Kubernetes state drift
  - TF Controller applies Terraform continuously, detecting drift on managed resources
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure branch protection in Gitea requiring PR approval for main branch. Add a Terraform plan step to CI that must pass before merge. Deploy AWS Config with conformance packs for the EKS and IAM resources.
- **Evidence**: `gitops/clusters/production/` (Flux reconciliation), `gitops/infrastructure/production/07-tf-controller.yaml` (TF Controller), `tenant-microservices/*/.gitea/workflows/build-and-push.yml` (CI with no plan/review step)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI/CD pipelines exist via Gitea Actions for all three microservices (producer, consumer, payments). Pipelines build Docker images and push to ECR with immutable tags. However, pipelines contain zero automated tests — no unit tests, no integration tests, no contract tests, no API validation. Flux Image Automation handles deployment but with no quality gate.
- **Gap**: No automated testing in CI. No API contract testing. No breaking change detection. No quality gates before deployment.
- **Compensating Controls**:
  - ECR image immutability prevents tag overwriting, providing deployment artifact integrity
  - Flux CD reconciliation can be paused manually if a bad image is detected
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add pytest stages to Gitea Actions workflows with API endpoint tests. Implement smoke tests post-deployment via Flux health checks. Consider adding Pact contract tests for inter-service communication (producer→SQS→consumer).
- **Evidence**: `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml`, `tenant-microservices/producer/.gitea/workflows/build-and-push.yml`, `tenant-microservices/payments/.gitea/workflows/build-and-push.yml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No automated test suites found anywhere in the repository. The only test artifact is a Helm chart test template (`helm-charts/application-chart/templates/tests/test-connection.yaml`) that verifies HTTP connectivity — not functional correctness. No pytest, no unittest, no integration test directories. CI pipelines skip testing entirely.
- **Gap**: Zero automated test coverage for API endpoints or business logic.
- **Compensating Controls**:
  - Helm test-connection provides basic liveness verification post-deployment
  - Health check endpoints (`/readiness-probe`) verify service availability
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create test suites for each microservice (producer, consumer, payments) covering: endpoint response format, error handling, SQS/DynamoDB integration (using moto/localstack). Add test execution to CI pipelines as a required gate.
- **Evidence**: `helm-charts/application-chart/templates/tests/test-connection.yaml` (connectivity only), `tenant-microservices/` (no test files found)

---

## INFOs — Architecture and Design Inputs

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Kubecost provides cost-per-tenant metrics. Metrics Server provides resource utilization for HPA scaling decisions. No custom business outcome metrics are published (e.g., tenant onboarding success rate, message processing throughput, payment completion rate).
- **Implication**: When agents interact with this platform, business-level success metrics (tenant provisioning latency, message processing SLA adherence) would be the primary signal for agent effectiveness — these do not exist yet.
- **Recommendation**: Publish custom CloudWatch metrics for tenant lifecycle operations (onboarding duration, deployment success/failure rate) and per-tenant message throughput from the microservices.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml` (cost metrics only), `gitops/infrastructure/production/01-metric-server.yaml` (resource metrics only)

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
- **Severity**: Pass
- **Finding**: IRSA (IAM Roles for Service Accounts) provides machine identity authentication for all Kubernetes workloads. Each service has a dedicated IAM role with an OIDC trust policy scoped to a specific namespace and service account. Gitea Actions use EC2 instance role via IMDSv2 for AWS API authentication. The authenticated principal (IAM role ARN) is attributable in CloudTrail.
- **Gap**: None — machine identity is well-implemented via IRSA.
- **Recommendation**: No action required.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (IRSA role definitions with OIDC trust), `terraform/modules/tenant-apps/main.tf` (per-tenant IRSA roles), `terraform/modules/gitea/main.tf` (EC2 instance role with IMDSv2)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: Pass
- **Finding**: The authorization model supports scoped permissions. Per-tenant producer roles are limited to SQS:SendMessage + SSM:GetParameter. Per-tenant consumer roles are limited to SQS read/delete + DynamoDB:PutItem + SSM:GetParameter. LB Controller has a specific ELB/EC2 policy. Argo Workflows/Events have SQS-only access. Image Automation has ECR read-only. The system demonstrates clear capability to differentiate access levels per caller identity.
- **Gap**: TF Controller IRSA has `AdministratorAccess` (line 236 and 614 in `gitops-saas-infra/main.tf`). This is overly broad but is a single infrastructure-provisioning role, not a production-facing service role.
- **Recommendation**: Scope TF Controller's IAM policy to the specific AWS services it manages (SQS, DynamoDB, IAM, SSM) rather than AdministratorAccess.
- **Evidence**: `terraform/modules/tenant-apps/main.tf` (scoped per-tenant policies), `terraform/modules/gitops-saas-infra/main.tf` (line 236, 614: AdministratorAccess on TF Controller)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: Pass
- **Finding**: IAM policies demonstrate action-level authorization. Per-tenant producer role allows `sqs:SendMessage` but not `sqs:DeleteMessage`. Per-tenant consumer role allows `dynamodb:PutItem` but not `dynamodb:DeleteItem` or `dynamodb:DeleteTable`. Argo roles allow `sqs:ReceiveMessage` and `sqs:DeleteMessage` but no SQS management actions. The system enforces read vs write distinctions at the IAM action level.
- **Gap**: None — action-level authorization is implemented via IAM policy actions.
- **Recommendation**: No action required.
- **Evidence**: `terraform/modules/tenant-apps/main.tf` (action-specific IAM policies per tenant role)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q5: Credential Management
- **Severity**: RISK-SAFETY
- **Finding**: Credentials are stored in AWS SSM Parameter Store (SecureString) which is a valid secrets management service. Random password generation is used for Gitea admin credentials. However, no credential rotation is configured — SSM Parameter Store does not provide automatic rotation like AWS Secrets Manager. The `gitea-ci-test/variables.tf` contains a `sensitive = true` marked variable for passwords but relies on manual management.
- **Gap**: No automatic credential rotation mechanism. SSM Parameter Store lacks native rotation support (unlike Secrets Manager). No evidence of rotation schedules or Lambda-based rotation functions.
- **Recommendation**: Migrate sensitive credentials (Gitea admin password, Flux tokens) from SSM Parameter Store to AWS Secrets Manager with automatic rotation enabled.
- **Evidence**: `terraform/workshop/main.tf` (lines 168–180), `terraform/gitea-ci-test/variables.tf` (line 35), `terraform/modules/gitea/main.tf`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (would be BLOCKER if write-enabled)
- **Finding**: No CloudTrail configuration found in any Terraform module. No `aws_cloudtrail` resources defined. No immutable log storage (S3 with Object Lock). No CloudWatch Logs retention policies for audit purposes.
- **Gap**: No audit trail infrastructure defined. Cannot attribute actions to specific principals in an immutable, tamper-evident log store.
- **Recommendation**: Add `aws_cloudtrail` resource with S3 bucket (Object Lock enabled), CloudTrail log file validation, and multi-region trail. Enable EKS control plane logging.
- **Evidence**: `terraform/` (all .tf files — no `aws_cloudtrail` resource found)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: IAM roles are defined in Terraform (IRSA roles for each service). While IAM inherently supports role deletion/policy detachment, there is no mechanism for immediate identity suspension without a full Terraform plan/apply cycle. No automated anomaly-triggered suspension.
- **Gap**: No immediate suspension mechanism for agent identities. Revoking an IRSA role requires modifying Terraform state and re-applying.
- **Recommendation**: Implement automation (Lambda + EventBridge) that can immediately attach a deny-all inline policy to any IRSA role upon anomaly detection.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (IRSA role definitions), `terraform/modules/tenant-apps/main.tf` (per-tenant IRSA roles)

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

#### STATE-Q3: Concurrency Controls ⚡
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

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q7: Graceful Degradation Signaling
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### HITL-Q2: Configurable Approval Gates ⚡
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

#### DATA-Q1: Sensitive Data Classification ⚡
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

#### DATA-Q4: Input Validation and Schema Enforcement
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

#### DISC-Q1: Schema Versioning and API Contracts
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
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (X-Ray, OpenTelemetry) is configured. Microservices use basic Python `logging` module without structured JSON output or correlation IDs. No `traceparent` header propagation. Metrics Server and Kubecost provide resource/cost metrics only.
- **Gap**: No distributed tracing infrastructure. No structured logging. No correlation ID propagation.
- **Recommendation**: Deploy OpenTelemetry Collector as a Flux HelmRelease. Add ADOT DaemonSet. Update microservices to emit structured JSON logs with request_id correlation.
- **Evidence**: `gitops/infrastructure/production/` (no tracing HelmRelease), `tenant-microservices/consumer/consumer.py`, `tenant-microservices/producer/producer.py`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting infrastructure configured. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. README references Amazon Managed Grafana and Prometheus but these are not defined in the IaC or GitOps manifests.
- **Gap**: No alerting thresholds for error rates, latency, or availability.
- **Recommendation**: Deploy kube-prometheus-stack via Flux HelmRelease with pre-configured alerting rules. Integrate with SNS for alert routing.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml` (cost only), `gitops/infrastructure/production/` (no alerting HelmRelease)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Kubecost provides cost-per-tenant metrics. Metrics Server provides resource utilization for HPA. No custom business outcome metrics are published.
- **Implication**: Business-level success metrics (tenant provisioning latency, message processing SLA adherence) would be the primary signal for agent effectiveness.
- **Recommendation**: Publish custom CloudWatch metrics for tenant lifecycle operations and per-tenant message throughput.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml`, `gitops/infrastructure/production/01-metric-server.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is comprehensively defined as IaC (Terraform for AWS, Flux CD for Kubernetes). Drift detection is partially covered via Flux reconciliation and TF Controller. However, no branch protection, no PR review requirements, no AWS Config rules, and no terraform plan review gates in CI.
- **Gap**: No peer review enforcement on IaC changes. No AWS Config drift detection. No plan-review gates in CI/CD.
- **Recommendation**: Configure branch protection in Gitea. Add Terraform plan step to CI. Deploy AWS Config conformance packs.
- **Evidence**: `gitops/clusters/production/` (Flux reconciliation), `gitops/infrastructure/production/07-tf-controller.yaml`, `tenant-microservices/*/.gitea/workflows/build-and-push.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI/CD pipelines exist via Gitea Actions for all three microservices. Pipelines build Docker images and push to ECR with immutable tags. However, pipelines contain zero automated tests — no unit tests, no integration tests, no contract tests, no API validation.
- **Gap**: No automated testing in CI. No API contract testing. No breaking change detection.
- **Recommendation**: Add pytest stages to Gitea Actions workflows. Implement smoke tests post-deployment. Consider Pact contract tests.
- **Evidence**: `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml`, `tenant-microservices/producer/.gitea/workflows/build-and-push.yml`, `tenant-microservices/payments/.gitea/workflows/build-and-push.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: Pass
- **Finding**: Flux CD's GitOps model provides reliable rollback via git revert — reverting a commit triggers automatic reconciliation to the previous state. TF Controller provides Terraform state management with `destroyResourcesOnDeletion: true` for tenant cleanup. Helm releases managed by Flux support `helm rollback` semantics. The GitOps reconciliation loop ensures desired state convergence within minutes.
- **Gap**: No automated rollback triggers (no canary with automatic rollback on error rate increase). Rollback is manual (git revert) but reliable and fast.
- **Recommendation**: Consider adding Flagger for automated canary analysis and rollback.
- **Evidence**: `gitops/clusters/production/` (Flux Kustomization with reconciliation), `helm-charts/helm-tenant-chart/templates/terraform.yaml` (TF Controller with destroyResourcesOnDeletion)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: No automated test suites found. The only test artifact is a Helm chart test template (`test-connection.yaml`) that verifies HTTP connectivity. No pytest, no unittest, no integration test directories. CI pipelines skip testing entirely.
- **Gap**: Zero automated test coverage for API endpoints or business logic.
- **Recommendation**: Create test suites for each microservice covering endpoint response format, error handling, and SQS/DynamoDB integration. Add test execution to CI pipelines.
- **Evidence**: `helm-charts/application-chart/templates/tests/test-connection.yaml`, `tenant-microservices/` (no test files)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Pass
- **Finding**: Encryption at rest is configured across all data stores: ECR repositories (AES256 encryption + scan-on-push), SQS queues (`sqs_managed_sse_enabled = true`), EC2 root volumes (`encrypted = true`), S3 buckets (public access blocked, encryption configured), DynamoDB tables (point-in-time recovery enabled, default encryption). AWS-managed keys are used rather than customer-managed KMS keys.
- **Gap**: Customer-managed KMS keys (CMK) not used — AWS-managed keys provide encryption but less key management control.
- **Recommendation**: Consider migrating to customer-managed KMS keys for sensitive data stores (DynamoDB, SQS) if regulatory requirements demand key rotation control.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (ECR encryption, S3 config), `terraform/modules/tenant-apps/main.tf` (SQS SSE, DynamoDB PITR), `terraform/modules/gitea/main.tf` (EC2 encrypted EBS)

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| terraform/modules/gitops-saas-infra/main.tf | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q7, ENG-Q5 |
| terraform/modules/tenant-apps/main.tf | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, ENG-Q5 |
| terraform/modules/gitea/main.tf | AUTH-Q1, AUTH-Q5, ENG-Q5 |
| terraform/workshop/main.tf | AUTH-Q5, AUTH-Q6 |
| terraform/gitea-ci-test/variables.tf | AUTH-Q5 |
| gitops/clusters/production/ | ENG-Q1, ENG-Q3 |
| gitops/infrastructure/production/07-tf-controller.yaml | ENG-Q1 |
| gitops/infrastructure/production/05-kubecost.yaml | OBS-Q2, OBS-Q3 |
| gitops/infrastructure/production/01-metric-server.yaml | OBS-Q3 |
| helm-charts/helm-tenant-chart/templates/terraform.yaml | ENG-Q3 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| tenant-microservices/consumer/consumer.py | OBS-Q1 |
| tenant-microservices/producer/producer.py | OBS-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| tenant-microservices/consumer/.gitea/workflows/build-and-push.yml | ENG-Q1, ENG-Q2 |
| tenant-microservices/producer/.gitea/workflows/build-and-push.yml | ENG-Q1, ENG-Q2 |
| tenant-microservices/payments/.gitea/workflows/build-and-push.yml | ENG-Q1, ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| helm-charts/application-chart/templates/tests/test-connection.yaml | ENG-Q4 |
