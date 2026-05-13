# Agentic Readiness Assessment Report

**Target**: ./services/eks-saas-gitops
**Date**: 2026-04-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: infrastructure-only
**Agent Scope**: read-only
**Priority**: P1
**Tags**: eks, gitops, terraform, saas, infrastructure
**Context**: EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings, everything that is not serverless will run here, EKS will be the centralized platform.

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 4 | **RISK-QUALITY**: 9 | **INFOs**: 1

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 4 |
| RISK-QUALITY | 9 |
| INFO | 1 |
| N/A | 29 |
| Not Evaluated (extended) | 0 |
| **Total** | **43** |

**Core Questions Evaluated**: 14
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 0
**Questions N/A (repo_type: infrastructure-only)**: 29
**Service Archetype**: N/A (infrastructure-only repo — archetype applies only to application repos)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Two critical IRSA roles are granted `AdministratorAccess` — the most permissive AWS managed policy. The `argo_workflows_eks_role` (bound to `argo-workflows:argoworkflows-sa` and `argo-workflows:argo-workflows-server`) and `tf_controller_irsa_role` (bound to `flux-system:tf-runner` and `flux-system:tf-controller`) both use `arn:aws:iam::aws:policy/AdministratorAccess`. Additionally, Kubernetes ClusterRoles `full-permissions-cluster-role` and `argo-events-cluster-role` grant `apiGroups: ["*"], resources: ["*"], verbs: ["*"]` — full cluster admin access. In contrast, scoped policies exist for tenant workloads (e.g., `producer-policy` scoped to specific SQS/SSM ARNs, `consumer-policy` scoped to SQS/DynamoDB/SSM ARNs) and for Argo Events sensor (`argosensor-policy` scoped to specific SQS queues).
- **Gap**: Agent identities inheriting these roles would have unrestricted AWS and Kubernetes access. The blast radius of a compromised or misconfigured agent identity is the entire AWS account and Kubernetes cluster. No scoping exists for the Argo Workflows or TF Controller identities.
- **Compensating Controls**:
  - Restrict any agent pilot to use tenant-level IRSA roles (producer/consumer) which are properly scoped, not the Argo Workflows or TF Controller roles.
  - Define a dedicated agent IRSA role with a custom IAM policy listing only the specific API actions and resource ARNs the agent needs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `AdministratorAccess` on `argo_workflows_eks_role` and `tf_controller_irsa_role` with custom policies scoped to the specific AWS services and actions each component needs. Replace wildcard Kubernetes ClusterRoles with namespace-scoped Roles granting only required verbs on required resources.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (lines: argo_workflows_eks_role, tf_controller_irsa_role), `gitops/infrastructure/production/03-argo-workflows.yaml` (full-permissions-cluster-role), `gitops/infrastructure/production/06-argo-events.yaml` (argo-events-cluster-role)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Action-level authorization is inconsistently implemented. Tenant-level IAM policies demonstrate proper action-level scoping: `producer-policy` grants only `sqs:SendMessage` and `ssm:GetParameter`; `consumer-policy` grants specific SQS read/delete and DynamoDB write actions; `argosensor-policy` grants specific SQS actions on specific queue ARNs. However, the Argo Workflows and TF Controller IRSA roles use `AdministratorAccess` which grants all actions on all resources, completely bypassing action-level authorization. The Kubernetes ClusterRoles (`full-permissions-cluster-role`, `argo-events-cluster-role`) grant all verbs on all resources — no action-level restriction exists at the Kubernetes layer for these components.
- **Gap**: An agent bound to the Argo Workflows service account could delete Kubernetes resources, modify IAM policies, or access any AWS service — there is no action-level enforcement to prevent unintended operations. The tenant-level scoping pattern exists but is not applied to the infrastructure control plane components.
- **Compensating Controls**:
  - Ensure agents only use tenant-scoped IRSA roles that already enforce action-level authorization.
  - Create separate Kubernetes Roles (not ClusterRoles) for agent operations, granting only `get`, `list`, and `watch` verbs for read-only agent use cases.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Apply the same action-level scoping pattern used for tenant workloads to the Argo Workflows and TF Controller roles. Create Kubernetes Roles with explicit action lists (verbs) for each service account instead of wildcard ClusterRoles.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (argo_workflows_eks_role, tf_controller_irsa_role), `terraform/modules/tenant-apps/main.tf` (producer-iampolicy, consumer-iampolicy — positive examples), `gitops/infrastructure/production/03-argo-workflows.yaml` (full-permissions-cluster-role)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No CloudTrail configuration exists in any Terraform file in this repository. No `aws_cloudtrail` resource is defined. No CloudWatch log group retention policies are configured for audit purposes. The EKS cluster module (`module.eks` using `terraform-aws-modules/eks/aws` v19.12) does not configure `cluster_enabled_log_types` — which means EKS control plane audit logging (API server, authenticator, controller manager, scheduler) is not enabled. No S3 bucket with object lock for immutable log storage is defined. No Kubernetes audit policy is configured.
- **Gap**: There is no infrastructure-defined audit trail for API calls to AWS resources or Kubernetes API server actions. If an agent identity makes API calls, those calls are not logged in a dedicated, immutable audit trail defined by this IaC. AWS account-level CloudTrail may exist outside this repo, but it is not defined or referenced here.
- **Compensating Controls**:
  - Verify whether an organization-level CloudTrail trail exists in the AWS account (outside this repo's scope). If yes, confirm it captures EKS API calls and IAM role assumption events.
  - Enable EKS control plane logging by adding `cluster_enabled_log_types = ["api", "audit", "authenticator"]` to the EKS module configuration.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `aws_cloudtrail` resource with S3 bucket (object lock enabled) and CloudWatch Logs integration to this Terraform configuration. Enable EKS audit logging via `cluster_enabled_log_types` in the EKS module. Configure log retention policies (minimum 90 days for compliance).
- **Evidence**: `terraform/workshop/main.tf` (module.eks — no cluster_enabled_log_types), all `terraform/**/*.tf` files (no aws_cloudtrail resource found)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: IRSA roles are defined as individual Terraform resources (`argo_workflows_eks_role`, `tf_controller_irsa_role`, `karpenter_irsa_role`, `lb_controller_irsa`, `argo_events_eks_role`, `ebs_csi_irsa_role`, `image_automation_irsa_role`), and tenant-level roles are created per-tenant (`producer_irsa_role`, `consumer_irsa_role`). Each role is bound to specific Kubernetes service accounts via OIDC. In principle, an individual IRSA role can be deactivated by removing its trust policy or detaching its policies. However, no automated suspension mechanism exists — no Lambda function, no runbook, no API endpoint, and no tooling to immediately revoke a specific agent identity without modifying Terraform state and reapplying.
- **Gap**: Suspending an agent identity requires modifying Terraform code, running `terraform apply`, and waiting for the change to propagate. This is too slow for incident response (minutes to hours vs. seconds). No out-of-band revocation mechanism exists.
- **Compensating Controls**:
  - Define an IAM deny policy that can be attached to any IRSA role via a manual AWS CLI command to immediately block all actions — this is faster than modifying Terraform.
  - Pre-create a "kill switch" IAM policy (`arn:aws:iam::ACCOUNT:policy/agent-emergency-deny`) with `Effect: Deny, Action: *, Resource: *` that can be attached via CLI in seconds.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create an operational runbook for agent identity suspension. Pre-provision an IAM deny-all policy. Consider implementing a Lambda-backed API that can attach the deny policy to any IAM role by name within seconds. For Kubernetes, create a script to delete or annotate the service account to break the IRSA binding immediately.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (IRSA role definitions), `terraform/modules/tenant-apps/main.tf` (tenant IRSA roles), `terraform/workshop/main.tf` (EBS CSI, image automation IRSA roles)

### RISK-QUALITY — Address as Capacity Allows

#### AUTH-Q1: Machine Identity Authentication — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The infrastructure defines a robust IRSA (IAM Roles for Service Accounts) pattern for machine identity authentication. Seven IRSA roles are defined across the Terraform modules, each bound to specific Kubernetes service accounts via OIDC federation. The Karpenter IRSA is bound to `karpenter:karpenter`, Argo Workflows to `argo-workflows:argoworkflows-sa`, Argo Events to `argo-events:argo-events-sa`, LB Controller to `aws-system:aws-load-balancer-controller`, TF Controller to `flux-system:tf-runner`, EBS CSI to `kube-system:ebs-csi-controller-sa`, and image automation to `flux-system:image-automation-controller`. Tenant-level IRSA roles are created per-tenant for producer and consumer workloads. Gitea uses API tokens stored in SSM SecureString parameters for authentication.
- **Gap**: No agent-specific IRSA role is defined. While the IRSA mechanism fully supports creating agent identities with OIDC-bound service accounts and attributable IAM role ARNs (visible in CloudTrail), no such identity has been provisioned for agent use cases. There is no documentation or template for creating agent-specific identities.
- **Compensating Controls**:
  - Use the existing tenant-level IRSA pattern as a template for creating agent-specific IRSA roles.
  - The IRSA mechanism is ready — creating an agent identity requires only adding a new Terraform module block following the established pattern.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Create a dedicated agent IRSA role following the existing pattern in `terraform/modules/gitops-saas-infra/main.tf`. Bind it to a dedicated Kubernetes service account in a new `agent-system` namespace. Document the process for creating and managing agent identities.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (7 IRSA roles), `terraform/modules/tenant-apps/main.tf` (tenant IRSA roles), `terraform/workshop/main.tf` (ebs_csi_irsa_role, image_automation_irsa_role)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Credentials are managed via AWS SSM Parameter Store with `SecureString` type. The Gitea admin password is generated via `random_password` and stored in SSM (`/eks-saas-gitops/gitea-admin-password`). The Gitea Flux token and CI/CD token are generated at runtime and stored in SSM (`/eks-saas-gitops/gitea-flux-token`, `/eks-saas-gitops/gitea-cicd-token`). The Flux CD Kubernetes secret stores the Gitea username and token in a `kubernetes_secret` resource. No AWS Secrets Manager or HashiCorp Vault usage is present.
- **Gap**: (1) No credential rotation is configured — SSM parameters are static once created. (2) The `gitea-ci-test/variables.tf` file contains a hardcoded default password `AdminPassword123!` for the `gitea_admin_password` variable. Although marked `sensitive = true` and annotated "Change this in production," it is a plaintext default in version control. (3) SSM Parameter Store lacks automatic rotation capabilities that Secrets Manager provides. (4) The checkov skip annotation `CKV_AWS_337` on SSM parameters acknowledges the gap: "Skiping this for now, move to Secrets Manager."
- **Compensating Controls**:
  - The hardcoded default password in `gitea-ci-test/` is in a test directory — ensure it is never used in production deployments.
  - SSM SecureString with KMS encryption provides encryption at rest — the immediate risk is credential staleness, not exposure.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate credentials from SSM Parameter Store to AWS Secrets Manager with automatic rotation enabled. Remove the hardcoded default password from `gitea-ci-test/variables.tf`. Implement a rotation Lambda for the Gitea admin password and API tokens.
- **Evidence**: `terraform/workshop/main.tf` (aws_ssm_parameter.gitea_password), `terraform/modules/flux_cd/main.tf` (kubernetes_secret.flux_system), `terraform/modules/gitea/userdata.sh` (SSM get/put for tokens), `terraform/gitea-ci-test/variables.tf` (hardcoded default password `AdminPassword123!`)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing or structured logging infrastructure is defined in this repository. There is no X-Ray instrumentation, no OpenTelemetry Collector deployment, no Fluent Bit or CloudWatch agent configuration, and no trace ID propagation configuration. The EKS cluster module does not configure `cluster_enabled_log_types`, meaning EKS control plane logging is disabled. The only observability tooling deployed is metrics-server (for Kubernetes resource metrics used by HPA) and Kubecost (for cost analysis with Prometheus for metrics scraping). Neither provides distributed tracing or structured logging for agent-initiated requests.
- **Gap**: If an agent calls infrastructure APIs (e.g., triggers Argo Workflows, interacts with TF Controller), there is no way to trace the request through the system or correlate log entries across components. Debugging agent-initiated failures would require manual log collection across multiple pods and AWS services.
- **Compensating Controls**:
  - Deploy OpenTelemetry Collector via a Flux HelmRelease in the GitOps infrastructure layer.
  - Enable EKS control plane logging as an interim measure for API server audit events.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenTelemetry Collector HelmRelease to the GitOps infrastructure manifests. Configure Fluent Bit or CloudWatch agent for structured log collection. Enable `cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]` in the EKS module. Ensure all Helm chart deployments include sidecar or library instrumentation.
- **Evidence**: `terraform/workshop/main.tf` (module.eks — no cluster_enabled_log_types), `gitops/infrastructure/production/kustomization.yaml` (no tracing/logging components), `gitops/infrastructure/production/01-metric-server.yaml` (resource metrics only), `gitops/infrastructure/production/05-kubecost.yaml` (cost metrics only)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists in this repository. There are no `aws_cloudwatch_metric_alarm` resources, no SNS topics for alert notifications, no PagerDuty/OpsGenie integrations, no composite alarms, and no SLO-based alerting defined in any Terraform file or GitOps manifest. Kubecost includes Prometheus for metrics scraping, but no Prometheus alerting rules (`PrometheusRule` CRDs) are defined.
- **Gap**: If the EKS cluster, its workloads, or the infrastructure components (Argo Workflows, Karpenter, Flux) experience errors or latency degradation, there are no automated alerts to notify operators. Agent-initiated traffic anomalies would go undetected.
- **Compensating Controls**:
  - Leverage Kubecost's built-in Prometheus to define PrometheusRule alert rules for key infrastructure metrics.
  - Add CloudWatch alarms for EKS cluster metrics via Terraform as a quick-win.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Define CloudWatch alarms for EKS cluster CPU/memory utilization, pod restart counts, and API server error rates. Deploy Prometheus alerting rules via GitOps for application-level metrics. Configure an SNS topic with operator email/Slack integration for alert delivery.
- **Evidence**: All `terraform/**/*.tf` files (no aws_cloudwatch_metric_alarm found), `gitops/infrastructure/production/` (no alerting components), `gitops/infrastructure/production/05-kubecost.yaml` (Prometheus without alerting rules)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sub-check results: (1) **IaC definition: YES** — All infrastructure is comprehensively defined in Terraform: VPC, EKS cluster, IAM roles, security groups, S3 buckets, SQS queues, ECR repositories, Gitea instance, and GitOps components. (2) **Peer review: PARTIAL** — The repo uses Gitea (self-hosted Git) rather than GitHub/GitLab. No branch protection rules are defined in the IaC. The `install.sh` script applies Terraform directly with `--auto-approve` flags, bypassing any plan review. (3) **Drift detection: NO** — No AWS Config rules, no `terraform plan` drift detection schedules, and no configuration monitoring are defined.
- **Gap**: While the IaC definition is comprehensive, changes can be applied without review (direct `terraform apply --auto-approve` in install.sh), and there is no mechanism to detect drift between the Terraform state and the actual AWS resources.
- **Compensating Controls**:
  - Require manual `terraform plan` review before `terraform apply` for any infrastructure changes — remove `--auto-approve` from operational scripts.
  - Enable AWS Config with managed rules to detect configuration drift on critical resources (IAM roles, security groups, EKS).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure Gitea branch protection on the main branch to require pull request reviews. Remove `--auto-approve` from `install.sh` or gate it behind a confirmation step. Add AWS Config rules via Terraform for drift detection on IAM roles, security groups, and EKS cluster configuration.
- **Evidence**: `terraform/workshop/main.tf` (comprehensive IaC), `terraform/install.sh` (--auto-approve on all terraform apply calls), all `terraform/**/*.tf` files (no aws_config_rule resources)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Gitea Actions CI pipelines exist for the three tenant microservices (`producer`, `consumer`, `payments`) in `.gitea/workflows/build-and-push.yml`. These pipelines build Docker images and push them to ECR on push to `main` — they are build-and-push only with no testing steps. The `workflow-scripts/Dockerfile` packages Terraform, kubectl, git, and jq into a container used by Argo Workflows for tenant onboarding/offboarding operations. There is no CI/CD pipeline for the Terraform IaC itself — no `terraform validate`, `terraform plan`, `checkov` or `tfsec` runs in CI.
- **Gap**: (1) No API contract testing exists in any CI pipeline. (2) No Terraform validation or security scanning runs in CI. (3) The microservice CI pipelines have no test steps — they build and push without any validation. (4) No consumer-driven contract tests (Pact) or OpenAPI spec validation.
- **Compensating Controls**:
  - Run `terraform validate` and `terraform plan` manually before applying changes.
  - Checkov annotations in the codebase suggest checkov has been run manually at some point — formalize this into a CI step.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a Terraform CI pipeline (via Gitea Actions or external CI) that runs `terraform fmt -check`, `terraform validate`, `terraform plan`, and `checkov` on every pull request. Add test steps to the microservice CI pipelines. If the infrastructure will expose APIs to agents, add contract testing for those API endpoints.
- **Evidence**: `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` (build-only CI), `workflow-scripts/Dockerfile` (operational tooling), all `terraform/**/*.tf` files (checkov skip annotations indicate prior manual runs)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Flux CD manages all Kubernetes deployments via HelmRelease resources, which inherently support rollback through Flux's reconciliation model. If a bad HelmRelease is committed, reverting the Git commit triggers Flux to reconcile back to the previous state. The HelmRelease resources define `interval: 1m0s` (or `10m0s` for some), meaning reconciliation happens frequently. Additionally, Helm itself maintains release history, enabling `helm rollback` commands. However, no explicit rollback triggers, canary deployments, or blue/green configurations are defined. Terraform changes have no automated rollback — `install.sh` applies directly and `destroy.sh` is a full teardown, not a rollback.
- **Gap**: (1) No automated rollback triggers based on health checks or metrics (e.g., Flagger for canary deployments). (2) Terraform changes are not reversible without manual intervention — no state snapshots or rollback procedures. (3) No feature flags for gradual rollout.
- **Compensating Controls**:
  - Git revert on the GitOps repository effectively triggers Flux-based rollback within the reconciliation interval (1–10 minutes).
  - Terraform state is stored (implicitly local or remote) — `terraform apply` with a previous commit's code achieves rollback.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy Flagger alongside Flux for automated canary analysis and rollback on Helm releases. Configure Flux `HelmRelease` resources with `remediation.retries` and `rollback.enable` settings. Implement Terraform state snapshots before each apply. Document rollback procedures for both Kubernetes (GitOps) and Terraform changes.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml` (HelmRelease with interval: 1m0s), `terraform/modules/flux_cd/main.tf` (FluxInstance configuration), `terraform/install.sh` (no rollback procedures), `terraform/destroy.sh` (full teardown, not rollback)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No automated test suites exist anywhere in this repository. No test files (`.test.`, `_test.`, `_spec.`, `test_`) were found. The Gitea Actions CI pipelines for microservices contain only build-and-push steps with no test execution. No Terraform test files (`.tftest.hcl`), no integration tests, no API test collections (Postman/Newman), and no end-to-end test frameworks are present. The only "test" artifact is the Helm chart test template (`helm-charts/application-chart/templates/tests/test-connection.yaml`) which is a basic connectivity test (wget to the service port).
- **Gap**: No test coverage for any infrastructure, API, or deployment behavior. Changes to Terraform modules, Helm charts, or Kubernetes manifests cannot be validated automatically before deployment.
- **Compensating Controls**:
  - The checkov skip annotations suggest some level of manual security scanning — capture these as automated checks.
  - Helm test template provides minimal post-deployment connectivity validation.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add Terraform tests using the native `terraform test` framework for critical modules (EKS, IAM, VPC). Add integration tests for the tenant onboarding workflow. Add API tests for any agent-facing endpoints. Add Helm chart tests using `helm test` with more comprehensive validation beyond connectivity.
- **Evidence**: All repository files searched (no test files found), `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` (no test steps), `helm-charts/application-chart/templates/tests/test-connection.yaml` (minimal connectivity test only)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Encryption at rest is partially implemented: **Encrypted**: SQS queues use `sqs_managed_sse_enabled = true` (4 queues). ECR repositories use `encryption_type = "AES256"` (7 repos). EBS root block device for Gitea uses `encrypted = true`. SSM parameters use `SecureString` type (KMS-encrypted). **Not KMS-encrypted**: S3 buckets `argo_artifacts` and `codeartifacts` explicitly skip KMS encryption with checkov skip `CKV2_AWS_145: "This S3 bucket does not required a KMS Encryption"` — they use default SSE (AES-256) but not customer-managed KMS. DynamoDB tables skip KMS encryption with checkov skip `CKV2_AWS_119: "Not using sensitive information"`. No customer-managed KMS keys (`aws_kms_key`) are defined anywhere in the repository.
- **Gap**: (1) No customer-managed KMS keys — all encryption uses AWS-managed keys or service-default encryption. This means no cross-account key sharing, no custom key rotation policies, and no key access logging beyond CloudTrail. (2) S3 buckets storing Argo workflow artifacts lack KMS encryption. (3) DynamoDB tables storing tenant data lack KMS encryption (despite point-in-time recovery being enabled). The checkov skip annotations indicate these are acknowledged gaps.
- **Compensating Controls**:
  - AWS-managed SSE (AES-256) on S3 and SQS provides encryption at rest — the data is encrypted, just not with customer-managed keys.
  - DynamoDB point-in-time recovery is enabled, providing data recovery capability.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a customer-managed KMS key in Terraform. Apply it to S3 buckets (`server_side_encryption_configuration` with `aws:kms`), DynamoDB tables (`server_side_encryption` with `kms_key_arn`), and SQS queues (`kms_master_key_id`). This enables key rotation control, access policies, and audit logging via CloudTrail.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (S3 argo_artifacts — no KMS, SQS with sqs_managed_sse_enabled), `terraform/modules/gitops-saas-infra/apps_needs.tf` (S3 codeartifacts — no KMS, ECR with AES256), `terraform/modules/tenant-apps/main.tf` (DynamoDB — CKV2_AWS_119 skip, SQS with sqs_managed_sse_enabled), `terraform/modules/gitea/main.tf` (EBS encrypted = true)

---

## INFOs — Architecture and Design Inputs

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Kubecost is deployed via Flux HelmRelease, providing cost analysis metrics with a built-in Prometheus instance for metrics scraping. Kubecost tracks pod/namespace/cluster cost allocation, network costs, and resource utilization — these are infrastructure cost metrics, not business outcome metrics. No custom CloudWatch metrics (`cloudwatch.put_metric_data`), no business KPI dashboards, and no application-level business metrics (e.g., tenant onboarding success rate, workflow completion rate, deployment frequency) are defined.
- **Implication**: When agents interact with the infrastructure (e.g., triggering tenant onboarding workflows), there are no business metrics to measure whether agent-initiated operations produce successful outcomes. Kubecost can inform cost impact of agent operations but not business effectiveness.
- **Recommendation**: Define custom metrics for key business outcomes: tenant onboarding success/failure rate, workflow execution duration, deployment success rate. Publish these to CloudWatch or Prometheus. Create dashboards correlating agent activity with business outcomes.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml` (cost metrics only, Grafana disabled), all `terraform/**/*.tf` files (no custom CloudWatch metrics)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q2: Machine-Readable API Specification
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q3: Structured Error Responses
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q5: Structured Response Format
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q6: Asynchronous Operation Support
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q7: Event Emission for State Changes
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: RISK-QUALITY
- **Finding**: The infrastructure defines a robust IRSA (IAM Roles for Service Accounts) pattern for machine identity authentication. Seven IRSA roles are defined across Terraform modules, each bound to specific Kubernetes service accounts via OIDC federation: Karpenter (`karpenter:karpenter`), Argo Workflows (`argo-workflows:argoworkflows-sa`), Argo Events (`argo-events:argo-events-sa`), LB Controller (`aws-system:aws-load-balancer-controller`), TF Controller (`flux-system:tf-runner`), EBS CSI (`kube-system:ebs-csi-controller-sa`), and Image Automation (`flux-system:image-automation-controller`). Tenant-level IRSA roles are dynamically created per-tenant. Gitea uses API tokens stored in SSM SecureString.
- **Gap**: No agent-specific IRSA role is defined. The IRSA mechanism fully supports creating agent identities with attributable IAM role ARNs, but no such identity has been provisioned. No documentation exists for creating agent-specific identities.
- **Recommendation**: Create a dedicated agent IRSA role following the existing pattern. Bind it to a dedicated Kubernetes service account in a new `agent-system` namespace. Document the agent identity creation process.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/tenant-apps/main.tf`, `terraform/workshop/main.tf`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Two IRSA roles use `AdministratorAccess`: `argo_workflows_eks_role` and `tf_controller_irsa_role`. Kubernetes ClusterRoles `full-permissions-cluster-role` and `argo-events-cluster-role` grant wildcard access (`apiGroups: ["*"], resources: ["*"], verbs: ["*"]`). In contrast, tenant workload policies (producer, consumer, argosensor) are properly scoped to specific actions and resource ARNs.
- **Gap**: AdministratorAccess and wildcard ClusterRoles create maximum blast radius — any identity inheriting these roles has unrestricted AWS account and Kubernetes cluster access.
- **Recommendation**: Replace `AdministratorAccess` with custom scoped policies. Replace wildcard ClusterRoles with namespace-scoped Roles.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Action-level authorization is inconsistently implemented. Tenant-level policies demonstrate proper scoping (e.g., `producer-policy` with `sqs:SendMessage`, `consumer-policy` with specific SQS/DynamoDB actions). However, AdministratorAccess on Argo Workflows and TF Controller bypasses all action-level restrictions. Wildcard Kubernetes ClusterRoles grant all verbs on all resources.
- **Gap**: No action-level enforcement for Argo Workflows or TF Controller identities. An agent bound to these service accounts could perform any action.
- **Recommendation**: Apply the tenant-level scoping pattern to infrastructure control plane roles. Create Kubernetes Roles with explicit verb lists.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/tenant-apps/main.tf`, `gitops/infrastructure/production/03-argo-workflows.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Credentials managed via AWS SSM Parameter Store with `SecureString` type. Gitea admin password generated via `random_password` and stored in SSM. Gitea tokens generated at runtime and stored in SSM. Flux CD Kubernetes secret stores Gitea credentials. No Secrets Manager or Vault usage.
- **Gap**: No credential rotation. Hardcoded default password `AdminPassword123!` in `gitea-ci-test/variables.tf`. Checkov skip `CKV_AWS_337` acknowledges need to migrate to Secrets Manager.
- **Recommendation**: Migrate to AWS Secrets Manager with automatic rotation. Remove hardcoded default password from test variables.
- **Evidence**: `terraform/workshop/main.tf`, `terraform/modules/flux_cd/main.tf`, `terraform/modules/gitea/userdata.sh`, `terraform/gitea-ci-test/variables.tf`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No CloudTrail configuration in any Terraform file. No `aws_cloudtrail` resource. EKS module does not configure `cluster_enabled_log_types`. No CloudWatch log retention policies for audit. No immutable log storage (S3 object lock). No Kubernetes audit policy.
- **Gap**: No infrastructure-defined audit trail for AWS API calls or Kubernetes API server actions. Agent actions would not be logged in a dedicated, immutable trail defined by this IaC.
- **Recommendation**: Add `aws_cloudtrail` with S3 object lock. Enable EKS audit logging via `cluster_enabled_log_types`. Configure 90-day minimum log retention.
- **Evidence**: `terraform/workshop/main.tf` (module.eks — no cluster_enabled_log_types), all `terraform/**/*.tf` (no aws_cloudtrail)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: IRSA roles are individually defined Terraform resources. Each can theoretically be deactivated by modifying trust policy or detaching policies. However, no automated suspension mechanism exists — no Lambda, no runbook, no out-of-band revocation tooling.
- **Gap**: Suspending an agent identity requires Terraform code changes and `terraform apply` — too slow for incident response. No emergency kill switch exists.
- **Recommendation**: Create operational runbook. Pre-provision IAM deny-all policy. Implement Lambda-backed API for immediate role suspension.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/tenant-apps/main.tf`, `terraform/workshop/main.tf`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q2: Queryable Current State
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q3: Selective Query Support
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q4: System of Record Designations
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q6: PII Redaction in Logs
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DATA-Q7: Data Quality Awareness
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: N/A
- **Finding**: This is an `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing or structured logging infrastructure is defined. No X-Ray, OpenTelemetry, Fluent Bit, or CloudWatch agent configuration. EKS cluster does not configure `cluster_enabled_log_types`. Only metrics-server (resource metrics for HPA) and Kubecost (cost analysis with Prometheus) are deployed — neither provides tracing or structured logging.
- **Gap**: No way to trace agent-initiated requests through the system. Debugging agent failures requires manual cross-pod, cross-service log collection.
- **Recommendation**: Add OpenTelemetry Collector HelmRelease. Configure Fluent Bit for structured log collection. Enable EKS control plane logging.
- **Evidence**: `terraform/workshop/main.tf` (module.eks), `gitops/infrastructure/production/kustomization.yaml`, `gitops/infrastructure/production/01-metric-server.yaml`, `gitops/infrastructure/production/05-kubecost.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists. No `aws_cloudwatch_metric_alarm`, no SNS topics, no PagerDuty/OpsGenie integrations, no PrometheusRule CRDs. Kubecost includes Prometheus but no alerting rules are defined.
- **Gap**: Infrastructure errors, latency degradation, and agent traffic anomalies go undetected. No automated notification system.
- **Recommendation**: Define CloudWatch alarms for EKS metrics. Deploy Prometheus alerting rules. Configure SNS for alert delivery.
- **Evidence**: All `terraform/**/*.tf` (no CloudWatch alarms), `gitops/infrastructure/production/` (no alerting components), `gitops/infrastructure/production/05-kubecost.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Kubecost deployed for infrastructure cost metrics with Prometheus. No custom CloudWatch metrics, no business KPI dashboards, no application-level outcome metrics. Kubecost tracks cost allocation and resource utilization — infrastructure metrics, not business outcomes.
- **Implication**: No metrics to measure whether agent-initiated operations produce successful business outcomes. Kubecost can inform cost impact but not effectiveness.
- **Recommendation**: Define custom metrics for tenant onboarding success rate, workflow execution duration, deployment success rate.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml`, all `terraform/**/*.tf`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: (1) **IaC definition: YES** — Comprehensive Terraform IaC defines VPC, EKS, IAM, security groups, S3, SQS, ECR, Gitea, and GitOps components. (2) **Peer review: PARTIAL** — Self-hosted Gitea for Git; no branch protection defined in IaC; `install.sh` uses `--auto-approve` bypassing plan review. (3) **Drift detection: NO** — No AWS Config rules, no scheduled `terraform plan`, no configuration monitoring.
- **Gap**: Changes can be applied without review. No drift detection between Terraform state and actual resources.
- **Recommendation**: Configure Gitea branch protection. Remove `--auto-approve`. Add AWS Config rules for drift detection.
- **Evidence**: `terraform/workshop/main.tf`, `terraform/install.sh`, all `terraform/**/*.tf`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Gitea Actions CI pipelines for three microservices (`producer`, `consumer`, `payments`) perform build-and-push to ECR only — no test steps. `workflow-scripts/Dockerfile` packages operational tools (Terraform, kubectl). No CI pipeline for Terraform IaC. No `terraform validate`, `checkov`, or `tfsec` in CI. No contract testing, no Pact, no OpenAPI validation.
- **Gap**: No automated testing in any CI pipeline. No Terraform validation in CI. No API contract testing.
- **Recommendation**: Add Terraform CI pipeline with `fmt`, `validate`, `plan`, and `checkov`. Add test steps to microservice pipelines. Add contract testing if agents will consume APIs.
- **Evidence**: `tenant-microservices/producer/.gitea/workflows/build-and-push.yml`, `workflow-scripts/Dockerfile`, all `terraform/**/*.tf` (checkov skip annotations)

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Flux CD manages Kubernetes deployments via HelmRelease resources with GitOps reconciliation. Reverting a Git commit triggers Flux to reconcile to the previous state (interval: 1m–10m). Helm maintains release history for rollback. However, no automated rollback triggers (Flagger), no canary deployments, no blue/green configurations. Terraform changes have no automated rollback — `install.sh` applies directly, `destroy.sh` is full teardown.
- **Gap**: No automated health-based rollback triggers. Terraform changes require manual intervention to reverse. No feature flags.
- **Recommendation**: Deploy Flagger for automated canary rollback. Configure HelmRelease `remediation.retries` and `rollback.enable`. Implement Terraform state snapshots.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml`, `terraform/modules/flux_cd/main.tf`, `terraform/install.sh`, `terraform/destroy.sh`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: No automated test suites found in the repository. No test files of any kind (`.test.`, `_test.`, `_spec.`, `test_`). No Terraform tests (`.tftest.hcl`), no integration tests, no API test collections. Microservice CI pipelines have no test steps. Only artifact: Helm chart test template (`test-connection.yaml`) — a basic wget connectivity test.
- **Gap**: Zero test coverage for infrastructure, APIs, or deployment behavior. No automated validation before deployment.
- **Recommendation**: Add Terraform tests for critical modules. Add integration tests for tenant workflows. Add Helm chart tests beyond connectivity.
- **Evidence**: All repository files (no test files), `tenant-microservices/producer/.gitea/workflows/build-and-push.yml`, `helm-charts/application-chart/templates/tests/test-connection.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: **Encrypted**: SQS queues — `sqs_managed_sse_enabled = true` (4 queues). ECR — `encryption_type = "AES256"` (7 repos). EBS — `encrypted = true` (Gitea). SSM — `SecureString` (KMS-encrypted). **Not KMS-encrypted**: S3 buckets `argo_artifacts` and `codeartifacts` skip KMS (checkov skip CKV2_AWS_145). DynamoDB tables skip KMS (checkov skip CKV2_AWS_119). No customer-managed KMS keys (`aws_kms_key`) defined anywhere.
- **Gap**: No customer-managed KMS. S3 Argo artifacts and DynamoDB tenant data lack KMS encryption. All encryption uses AWS-managed keys or service defaults.
- **Recommendation**: Create customer-managed KMS key. Apply to S3, DynamoDB, and SQS. Enable key rotation and access logging.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/gitops-saas-infra/apps_needs.tf`, `terraform/modules/tenant-apps/main.tf`, `terraform/modules/gitea/main.tf`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/workshop/main.tf` | AUTH-Q1, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, ENG-Q1 |
| `terraform/workshop/saas_gitops.tf` | AUTH-Q1 |
| `terraform/workshop/variables.tf` | ENG-Q1 |
| `terraform/workshop/versions.tf` | ENG-Q2 |
| `terraform/modules/gitops-saas-infra/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, ENG-Q5 |
| `terraform/modules/gitops-saas-infra/apps_needs.tf` | ENG-Q5 |
| `terraform/modules/gitops-saas-infra/variables.tf` | AUTH-Q1 |
| `terraform/modules/gitops-saas-infra/outputs.tf` | AUTH-Q1 |
| `terraform/modules/tenant-apps/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, ENG-Q5 |
| `terraform/modules/flux_cd/main.tf` | AUTH-Q5, ENG-Q3 |
| `terraform/modules/gitea/main.tf` | AUTH-Q5, ENG-Q5 |
| `terraform/modules/gitea/userdata.sh` | AUTH-Q5 |
| `terraform/gitea-ci-test/main.tf` | ENG-Q5 |
| `terraform/gitea-ci-test/variables.tf` | AUTH-Q5 |

### GitOps Manifests
| File | Questions Referenced |
|------|---------------------|
| `gitops/infrastructure/production/01-metric-server.yaml` | OBS-Q1 |
| `gitops/infrastructure/production/02-karpenter.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/03-argo-workflows.yaml` | AUTH-Q2, AUTH-Q3, ENG-Q3 |
| `gitops/infrastructure/production/04-lb-controller.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/05-kubecost.yaml` | OBS-Q1, OBS-Q2, OBS-Q3 |
| `gitops/infrastructure/production/06-argo-events.yaml` | AUTH-Q2, AUTH-Q3 |
| `gitops/infrastructure/production/07-tf-controller.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/kustomization.yaml` | OBS-Q1 |

### Shell Scripts
| File | Questions Referenced |
|------|---------------------|
| `terraform/install.sh` | ENG-Q1, ENG-Q3 |
| `terraform/destroy.sh` | ENG-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` | ENG-Q2, ENG-Q4 |
| `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml` | ENG-Q2 |
| `tenant-microservices/payments/.gitea/workflows/build-and-push.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `workflow-scripts/Dockerfile` | ENG-Q2 |

### Helm Charts
| File | Questions Referenced |
|------|---------------------|
| `helm-charts/application-chart/templates/tests/test-connection.yaml` | ENG-Q4 |
| `helm-charts/application-chart/Chart.yaml` | ENG-Q3 |
| `helm-charts/helm-tenant-chart/templates/serviceaccount.yaml` | AUTH-Q1 |
| `helm-charts/helm-tenant-chart/templates/terraform.yaml` | ENG-Q3 |
