# Agentic Readiness Assessment Report

**Target**: services/eks-saas-gitops
**Date**: 2025-07-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: infrastructure-only
**Agent Scope**: write-enabled
**Priority**: P1
**Tags**: eks, gitops, terraform, saas, infrastructure
**Context**: EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 11 | **INFOs**: 2

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 11 |
| INFO | 2 |
| N/A | 34 |
| **Total** | **49** |

**Questions Evaluated**: 15
**Questions N/A (repo_type: infrastructure-only)**: 34

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No `aws_cloudtrail` resource is defined in any Terraform file across the entire repository. No CloudWatch Log Group resources are defined for audit logging. No S3 bucket with object lock for immutable log storage is configured. The infrastructure provisions an EKS cluster, IAM roles, SQS queues, S3 buckets, DynamoDB tables, and EC2 instances — none of which have audit trail configuration attached. Searched all `.tf` files for `cloudtrail`, `cloudwatch_log_group`, and `object_lock` — zero results.
- **Gap**: There is no immutable audit logging infrastructure defined. For a write-enabled agent scope, every write operation must be attributable to an authenticated principal with an immutable, tamper-evident log. Without CloudTrail, there is no record of API calls made by agent-assumed IRSA roles. Without CloudWatch log groups, there is no centralized log retention. Without S3 object lock, existing logs (if any) are mutable and could be tampered with.
- **Remediation**:
  - **Immediate**: Add an `aws_cloudtrail` resource to `terraform/workshop/main.tf` or a dedicated `audit.tf` file. Enable CloudTrail log file validation (`enable_log_file_validation = true`). Create an S3 bucket with object lock for trail storage. Enable EKS control plane logging (`cluster_enabled_log_types = ["api", "audit", "authenticator"]`).
  - **Target State**: CloudTrail trail active with log file validation, S3 bucket with object lock for immutable storage, EKS audit logging enabled, CloudWatch Log Groups with defined retention policies for all audit-relevant services.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: None — this is a standalone blocker that can be resolved independently.
- **Evidence**: `terraform/workshop/main.tf`, `terraform/modules/gitops-saas-infra/main.tf` — absence of any `aws_cloudtrail`, `aws_cloudwatch_log_group`, or object lock configuration across all IaC files.

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: Network security configurations are partially defined but have significant gaps. **Defined**: (1) Gitea security group in `terraform/modules/gitea/main.tf` has specific ingress rules — SSH from VS Code VPC, Gitea HTTP from VS Code VPC, Gitea HTTP from EKS cluster SG, and optional IP-based access. Egress is open (`0.0.0.0/0`). (2) Flux operator defines `networkPolicy = true` in `terraform/modules/flux_cd/main.tf`, enabling network policies for flux-system namespace. (3) VPC with public and private subnets, single NAT gateway. (4) VPC peering between VS Code and EKS VPCs. **Gaps**: (1) EKS cluster has `cluster_endpoint_public_access = true` in `terraform/workshop/main.tf` — the Kubernetes API server is internet-accessible. (2) Kubecost explicitly sets `networkPolicy.enabled: false` in `gitops/infrastructure/production/05-kubecost.yaml`. (3) Argo Workflows server is exposed via internet-facing LoadBalancer with `--auth-mode=server` (no authentication) in `gitops/infrastructure/production/03-argo-workflows.yaml`. (4) Kubecost service is exposed via internet-facing LoadBalancer in `gitops/infrastructure/production/05-kubecost.yaml`. (5) No WAF rules defined. (6) No CORS configuration exists (searched all files — zero results). (7) No API Gateway exists — services are exposed directly via LoadBalancers.
- **Gap**: Critical services (Argo Workflows, Kubecost) are exposed to the internet via LoadBalancers without authentication or WAF protection. EKS API server is publicly accessible. Kubecost network policies are disabled. No CORS configuration or API Gateway layer exists.
- **Remediation**:
  - **Immediate**: Change Argo Workflows and Kubecost service annotations from `internet-facing` to `internal`. Set `cluster_endpoint_public_access = false` on the EKS cluster and use a VPN or bastion for cluster access. Enable Kubecost network policies (`networkPolicy.enabled: true`).
  - **Target State**: All services accessible only via internal load balancers or VPN. EKS API endpoint private-only. Network policies enabled for all namespaces. WAF WebACL protecting any remaining public-facing endpoints. API Gateway layer for any services that must be externally accessible. CORS policies documented and configured.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: None — this can be resolved independently, though coordinating with AUTH-Q7 (audit logging) ensures network changes are audited.
- **Evidence**: `terraform/workshop/main.tf`, `terraform/modules/gitea/main.tf`, `terraform/modules/flux_cd/main.tf`, `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/05-kubecost.yaml`

## RISKs — Proceed with Compensating Controls

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: Two IRSA roles are attached to `arn:aws:iam::aws:policy/AdministratorAccess`: (1) `argo-workflows-irsa-${var.name}` in `module "argo_workflows_eks_role"` and (2) `tf-controller-${var.name}` in `module "tf_controller_irsa_role"`, both in `terraform/modules/gitops-saas-infra/main.tf`. The Karpenter policy uses `Resource: "*"` with condition-based restrictions on `ec2:TerminateInstances`. The VS Code EC2 CloudFormation role in `helpers/vs-code-ec2.yaml` also attaches `AdministratorAccess`. In contrast, tenant-level policies in `terraform/modules/tenant-apps/main.tf` are well-scoped: `producer-iampolicy` grants only `sqs:SendMessage` and `ssm:GetParameter` on specific resources; `consumer-iampolicy` grants specific SQS, DynamoDB, and SSM actions on specific resources.
- **Gap**: AdministratorAccess on argo-workflows and tf-controller IRSA roles violates least-privilege. Any agent assuming these roles has unrestricted AWS API access. The Karpenter policy's `Resource: "*"` is partially mitigated by condition keys but still broad.
- **Compensating Controls**:
  - Restrict agent identities to tenant-level IRSA roles only (producer/consumer roles), which are properly scoped.
  - Implement IAM Access Analyzer to continuously validate that agent-assumed roles do not have overly permissive policies.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `AdministratorAccess` on argo-workflows and tf-controller IRSA roles with custom IAM policies scoped to the specific actions and resources each controller actually needs (e.g., S3 for artifacts, SQS for queues, EKS for workflow management, Terraform state operations).
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (lines 236, 614), `helpers/vs-code-ec2.yaml` (line 51), `terraform/modules/tenant-apps/main.tf`

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: Two Kubernetes ClusterRoles grant unrestricted cluster access: (1) `full-permissions-cluster-role` in `gitops/infrastructure/production/03-argo-workflows.yaml` with `apiGroups: ["*"], resources: ["*"], verbs: ["*"]` bound to `argoworkflows-sa`; (2) `argo-events-cluster-role` in `gitops/infrastructure/production/06-argo-events.yaml` with identical wildcard permissions bound to `argo-events-sa`. At the IAM level, tenant-level policies in `terraform/modules/tenant-apps/main.tf` do enforce action-level control — `sqs:SendMessage` is granted separately from `sqs:ReceiveMessage`, and DynamoDB `PutItem` is granted independently.
- **Gap**: Kubernetes RBAC does not enforce action-level authorization for Argo Workflows and Argo Events service accounts. An agent using these service accounts can perform any Kubernetes API operation including delete, patch, and exec on any resource in any namespace.
- **Compensating Controls**:
  - Restrict agent access to namespaced Roles instead of ClusterRoles.
  - Use Kubernetes admission controllers (OPA/Gatekeeper or Kyverno) to deny destructive operations from agent-labeled service accounts.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `full-permissions-cluster-role` and `argo-events-cluster-role` with scoped ClusterRoles that list only the specific apiGroups, resources, and verbs required by Argo Workflows and Argo Events controllers.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`, `terraform/modules/tenant-apps/main.tf`

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: Credentials are managed through a mix of secure and insecure patterns. **Secure patterns**: Gitea admin password is generated via `random_password` and stored in SSM Parameter Store as `SecureString` (`terraform/workshop/main.tf`). Gitea tokens (flux-token, cicd-token) are stored in SSM as `SecureString` via `userdata.sh`. The `gitea_token` Terraform variable is marked `sensitive = true` in `terraform/modules/flux_cd/variables.tf`. **Insecure patterns**: The `kubernetes_secret "flux_system"` in `terraform/modules/flux_cd/main.tf` stores Gitea username and password token directly in a Kubernetes Opaque secret — the password value comes from the `var.gitea_token` variable and is stored in plaintext within the Kubernetes secret. Argo Workflow templates in `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` pass `GIT_TOKEN: "${gitea_token}"` as a workflow parameter — this token is substituted via Flux postBuild and passed through workflow steps as an environment variable. No credential rotation mechanism is defined.
- **Gap**: Kubernetes secrets store credentials in base64-encoded plaintext (not encrypted at the application layer). Git tokens are passed as plaintext workflow parameters, visible in Argo Workflows UI and logs. No rotation mechanism exists for any credential.
- **Compensating Controls**:
  - Enable Kubernetes secrets encryption at rest using AWS KMS via the EKS encryption configuration.
  - Restrict Argo Workflows UI access to prevent credential leakage through workflow parameter visibility.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate Kubernetes secrets to AWS Secrets Manager with the AWS Secrets Store CSI Driver. Implement automatic credential rotation for Gitea tokens. Replace workflow parameter-based credential passing with Kubernetes secret volume mounts.
- **Evidence**: `terraform/modules/flux_cd/main.tf`, `terraform/modules/flux_cd/variables.tf`, `terraform/workshop/main.tf`, `terraform/modules/gitea/userdata.sh`, `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml`

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: Agent identities in this infrastructure are IRSA roles (Karpenter, Argo Workflows, Argo Events, LB Controller, TF Controller, EBS CSI, Image Automation). These roles are defined in Terraform and associated with Kubernetes service accounts via OIDC provider annotations. There is no explicit suspension mechanism — disabling an agent identity requires either: (1) modifying the IRSA role's trust policy in Terraform and re-applying, (2) deleting the Kubernetes service account, or (3) removing the `eks.amazonaws.com/role-arn` annotation. None of these are instantaneous or automated. No runbook or automated procedure for identity suspension exists in the repository.
- **Gap**: No immediate, one-click suspension capability for individual agent identities. Suspension requires Terraform changes, which involve plan-apply cycles with potential for cascading effects on other resources.
- **Compensating Controls**:
  - Prepare pre-built Terraform override files that set IRSA trust policies to deny all, enabling faster suspension.
  - Use SCP (Service Control Policies) at the AWS Organizations level to immediately deny actions from specific roles.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement an operational runbook with pre-tested `kubectl` and `aws iam` commands for immediate identity suspension. Consider adding an IAM inline policy deny override that can be applied without full Terraform plan-apply.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/workshop/main.tf`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: No distributed tracing infrastructure is defined anywhere in the repository. Searched all IaC files and GitOps configurations for `opentelemetry`, `otel`, `x-ray`, `xray`, `tracing` — zero results. No CloudWatch Log Group resources are defined in any Terraform file. No Fluentd, Fluent Bit, or logging agent HelmRelease is defined in the GitOps configurations. The only observability tooling deployed is: (1) Kubernetes Metrics Server (`gitops/infrastructure/production/01-metric-server.yaml`) which provides CPU/memory metrics only, and (2) Kubecost (`gitops/infrastructure/production/05-kubecost.yaml`) with Prometheus for cost metrics. Neither provides distributed tracing or structured logging.
- **Gap**: No distributed tracing (X-Ray, OpenTelemetry) and no structured logging infrastructure. When an agent-initiated request fails within the infrastructure, there is no way to trace the request path across services or correlate log entries.
- **Compensating Controls**:
  - Deploy AWS Distro for OpenTelemetry (ADOT) as a DaemonSet via a Flux HelmRelease to enable distributed tracing for workloads on the cluster.
  - Deploy Fluent Bit as a DaemonSet to forward structured logs to CloudWatch Logs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a HelmRelease for ADOT Collector and Fluent Bit to the `gitops/infrastructure/production/` directory. Configure EKS control plane logging. Define CloudWatch Log Groups with appropriate retention in Terraform.
- **Evidence**: `gitops/infrastructure/production/01-metric-server.yaml`, `gitops/infrastructure/production/05-kubecost.yaml` — absence of tracing/logging infrastructure across all files.

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration exists in the repository. Searched all Terraform files for `aws_cloudwatch_metric_alarm`, `pagerduty`, `opsgenie` — zero results. The Prometheus instance deployed via Kubecost (`gitops/infrastructure/production/05-kubecost.yaml`) has a basic scrape configuration (`global.scrape_interval: 1m`) but no alerting rules defined. Kubecost itself tracks cost anomalies but does not provide infrastructure error rate or latency alerting. No Alertmanager configuration is present.
- **Gap**: No alerting thresholds for error rates, latency, or infrastructure health. Infrastructure degradation will not trigger notifications — issues will only be discovered when agents or operators observe failures directly.
- **Compensating Controls**:
  - Configure basic CloudWatch alarms for EKS cluster health, node count, and pod restart rates via Terraform.
  - Enable Prometheus Alertmanager through the Kubecost Helm values with critical alert rules.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `aws_cloudwatch_metric_alarm` resources to Terraform for critical infrastructure metrics (EKS API server latency, node not ready, SQS queue depth). Configure Alertmanager via the Kubecost Prometheus stack.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml`, `terraform/workshop/main.tf` — absence of `aws_cloudwatch_metric_alarm` and Alertmanager configuration.

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: **(1) IaC defined: YES.** The entire infrastructure is defined as Terraform IaC across `terraform/workshop/` (main entry point), `terraform/modules/gitops-saas-infra/` (IRSA roles, S3, SQS, ECR), `terraform/modules/gitea/` (Gitea server), `terraform/modules/flux_cd/` (Flux operator), and `terraform/modules/tenant-apps/` (per-tenant resources). GitOps layer defined in `gitops/` with Flux Kustomizations and HelmReleases. **(2) Change review: NOT EVIDENCED.** No `.github/CODEOWNERS`, no branch protection configuration, no PR review requirements found in the repository. The repo uses Gitea as the Git server, but no Gitea-side branch protection or review rules are defined in the IaC. **(3) Drift detection: NOT EVIDENCED.** No AWS Config rules, no `terraform plan` in CI, no Flux drift detection configuration found. Searched for `aws_config`, `drift`, `config_rule` — zero results.
- **Gap**: Only 1 of 3 governance sub-checks passes. Infrastructure is defined as code, but there is no evidence of mandatory peer review or drift detection. Changes to IAM roles, security groups, and network configurations could be applied without review.
- **Compensating Controls**:
  - Implement Gitea branch protection rules on the main branch requiring at least one reviewer.
  - Run `terraform plan` as a pre-merge check using Gitea Actions (runner is already configured in `userdata.sh`).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable branch protection on the Gitea repository's main branch. Create a Gitea Actions workflow that runs `terraform plan` on pull requests. Add AWS Config rules for critical resource drift detection.
- **Evidence**: `terraform/workshop/main.tf`, `terraform/modules/gitea/userdata.sh` (Gitea Actions runner is configured), absence of `.github/CODEOWNERS`, branch protection config, and AWS Config rules.

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions found in the repository. Searched for `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml` — none exist. The `terraform/gitea-ci-test/` directory contains a simplified Terraform configuration for testing the Gitea module but is not a CI/CD pipeline. The `terraform/install.sh` and `terraform/destroy.sh` scripts are manual deployment automation scripts — not CI/CD pipelines with automated testing. A Gitea Actions runner is provisioned in `terraform/modules/gitea/userdata.sh`, but no Gitea Actions workflow files (`.gitea/workflows/`) are found in the repository root. The only Gitea Actions workflows exist in `tenant-microservices/*/`.gitea/workflows/build-and-push.yml` — these are container build pipelines, not infrastructure CI/CD with contract testing.
- **Gap**: No CI/CD pipeline for infrastructure changes. No contract testing, no automated `terraform plan` validation, no breaking change detection. Infrastructure changes are applied manually via `install.sh` using targeted `terraform apply` commands.
- **Compensating Controls**:
  - Use the existing Gitea Actions runner to create a minimal CI pipeline that runs `terraform validate` and `terraform plan` on pushes.
  - Add `terraform fmt -check` and `tflint` to catch configuration errors before apply.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a `.gitea/workflows/terraform-ci.yml` workflow that runs `terraform validate`, `terraform plan`, and `tflint` on pull requests. Add Checkov or tfsec for security policy validation.
- **Evidence**: `terraform/install.sh`, `terraform/destroy.sh`, `terraform/gitea-ci-test/main.tf`, `terraform/modules/gitea/userdata.sh`, `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml`

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: Flux HelmRelease resources have implicit rollback capability — when a HelmRelease spec changes, Flux performs a Helm upgrade, and if the upgrade fails Helm's built-in rollback kicks in. However, no explicit rollback configuration is defined in any HelmRelease: no `remediation.retries`, no `rollback.enable: true`, no `upgrade.remediation.remediateLastFailure`. The Flux Kustomizations use `prune: true` (in `gitops/clusters/production/infrastructure.yaml`), which means resources are garbage-collected when removed from Git — this is a forward-only mechanism, not rollback. For Terraform-managed resources, the `terraform/destroy.sh` script provides a complete teardown but not a targeted rollback. No blue/green, canary, or traffic-shifting deployment patterns are defined. No CodeDeploy integration exists.
- **Gap**: No explicit rollback configuration for HelmReleases. No targeted infrastructure rollback procedure. The only recovery path is Git revert (which triggers Flux reconciliation) or complete teardown via `destroy.sh`.
- **Compensating Controls**:
  - Git revert on the GitOps repository triggers Flux reconciliation to the previous state — this serves as a de facto rollback mechanism for Kubernetes resources.
  - Terraform state allows `terraform apply` with previous variable values to revert infrastructure changes.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add explicit rollback configuration to HelmReleases (`spec.upgrade.remediation.remediateLastFailure: true`, `spec.upgrade.remediation.retries: 3`). Document a rollback runbook for Terraform-managed resources. Consider implementing Terraform workspace snapshots for point-in-time recovery.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/02-karpenter.yaml`, `gitops/clusters/production/infrastructure.yaml`, `terraform/destroy.sh`

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Minimal test coverage exists. The only test artifact is a Helm test in `helm-charts/application-chart/templates/tests/test-connection.yaml` — a basic connectivity test that uses `wget` to check if the Helm-deployed service responds on its port. This is a Helm lifecycle hook test (`helm.sh/hook: test`), not an API contract test. The `terraform/gitea-ci-test/` directory contains a simplified Terraform configuration for testing Gitea module deployment — this is infrastructure smoke testing, not API or contract testing. No Postman/Newman collections, pytest API tests, REST Assured tests, or integration test suites were found. No CI pipeline runs any tests.
- **Gap**: No automated API or infrastructure contract tests running in CI. The single Helm test validates service connectivity only, not behavior, error handling, or contract compliance.
- **Compensating Controls**:
  - Use `terraform validate` and `terraform plan` as lightweight contract validation for infrastructure definitions.
  - Implement `terratest` for infrastructure integration testing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement infrastructure integration tests using `terratest` or similar. Add `terraform validate` to a CI pipeline. For the tenant onboarding workflow, add end-to-end tests that validate the SQS → Argo Events → Argo Workflows → Terraform pipeline.
- **Evidence**: `helm-charts/application-chart/templates/tests/test-connection.yaml`, `terraform/gitea-ci-test/main.tf`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: Encryption at rest is inconsistently applied. **Encrypted resources**: (1) All ECR repositories use `encryption_type = "AES256"` in `terraform/modules/gitops-saas-infra/apps_needs.tf`. (2) SQS queues use `sqs_managed_sse_enabled = true` in `terraform/modules/gitops-saas-infra/main.tf` and `terraform/modules/tenant-apps/main.tf`. (3) Gitea EC2 root block device has `encrypted = true` in `terraform/modules/gitea/main.tf`. (4) CloudFormation VS Code S3 bucket uses `SSEAlgorithm: AES256` in `helpers/vs-code-ec2.yaml`. **Not encrypted with KMS**: (1) S3 bucket `argo_artifacts` has `checkov:skip=CKV2_AWS_145: This S3 bucket does not required a KMS Encryption`. (2) S3 bucket `codeartifacts` has the same skip. (3) DynamoDB table `consumer_ddb` has `checkov:skip=CKV2_AWS_119: Not using sensitive information` — explicitly skipping encryption. **No customer-managed KMS keys** are used anywhere — all encryption uses AWS-managed keys or S3-managed encryption.
- **Gap**: S3 buckets (argo_artifacts, codeartifacts) and DynamoDB tables lack KMS encryption. No customer-managed KMS keys are used. Checkov security checks are explicitly skipped for encryption requirements.
- **Compensating Controls**:
  - Enable default S3 bucket encryption with AWS-managed KMS keys as a quick win.
  - Scope agent access to encrypted resources only.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable KMS encryption on all S3 buckets and DynamoDB tables. Create a customer-managed KMS key for sensitive data stores. Remove Checkov skip annotations for encryption checks and address findings.
- **Evidence**: `terraform/modules/gitops-saas-infra/apps_needs.tf`, `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/tenant-apps/main.tf`, `terraform/modules/gitea/main.tf`, `helpers/vs-code-ec2.yaml`

## INFOs — Architecture and Design Inputs

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The infrastructure uses IRSA (IAM Roles for Service Accounts) extensively for machine identity authentication, which is the recommended pattern for EKS workloads. Seven IRSA roles are defined: (1) Karpenter Controller (`karpenter_controller`) in `terraform/modules/gitops-saas-infra/main.tf`, (2) Argo Workflows (`argo-workflows-irsa-${var.name}`) in `terraform/modules/gitops-saas-infra/main.tf`, (3) Argo Events (`argo-events-irsa`) in `terraform/modules/gitops-saas-infra/main.tf`, (4) LB Controller (`lb-controller-irsa-${var.name}`) in `terraform/modules/gitops-saas-infra/main.tf`, (5) TF Controller (`tf-controller-${var.name}`) in `terraform/modules/gitops-saas-infra/main.tf`, (6) EBS CSI (`ebs-csi-${local.name}`) in `terraform/workshop/main.tf`, (7) Image Automation (`image-automation-${local.name}`) in `terraform/workshop/main.tf`. All IRSA roles use the EKS OIDC provider for authentication and are scoped to specific namespace:serviceAccount pairs. Kubernetes service accounts in GitOps manifests carry `eks.amazonaws.com/role-arn` annotations linking them to their IRSA roles. Tenant-level IRSA roles (producer, consumer) in `terraform/modules/tenant-apps/main.tf` follow the same pattern with per-tenant scoping.
- **Implication**: Machine identity is well-established via IRSA. An agent assuming any of these IRSA roles would be authenticated with a unique, attributable identity. This is a strong foundation for agent integration. However, audit attribution depends on CloudTrail being enabled (see AUTH-Q7 BLOCKER).
- **Recommendation**: Ensure EKS control plane audit logging is enabled so that IRSA-based agent calls are logged with full principal attribution.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/workshop/main.tf`, `terraform/modules/tenant-apps/main.tf`, `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`, `gitops/infrastructure/production/07-tf-controller.yaml`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Kubecost is deployed via HelmRelease (`gitops/infrastructure/production/05-kubecost.yaml`) and provides infrastructure cost metrics — per-namespace, per-pod cost attribution, network cost tracking (`networkCosts.enabled: true`), and ETL storage for 120 days of cost data. Prometheus (bundled with Kubecost) scrapes infrastructure metrics at 1-minute intervals. Kubernetes Metrics Server provides CPU and memory utilization metrics. No custom CloudWatch metrics (`cloudwatch.put_metric_data`) are defined in any Terraform file. No business outcome dashboards (conversion rates, tenant onboarding success rates, workflow completion rates) are configured. Kubecost provides cost optimization insights but not business-level outcomes.
- **Implication**: Cost metrics provide a baseline for monitoring agent-induced infrastructure spend. However, there are no business outcome metrics to measure whether agent interactions produce good results (e.g., tenant onboarding success rate, workflow completion rate, infrastructure provisioning time).
- **Recommendation**: Define custom CloudWatch metrics for business outcomes: tenant onboarding success/failure rate, Argo Workflow completion rate, mean time to provision tenant infrastructure. These metrics will become the primary signal for evaluating agent effectiveness.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml`, `gitops/infrastructure/production/01-metric-server.yaml`

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
- **Finding**: The infrastructure uses IRSA (IAM Roles for Service Accounts) extensively for machine identity authentication. Seven IRSA roles are defined across `terraform/modules/gitops-saas-infra/main.tf` and `terraform/workshop/main.tf`: Karpenter Controller, Argo Workflows, Argo Events, LB Controller, TF Controller, EBS CSI, and Image Automation. All use EKS OIDC provider for authentication and are scoped to specific namespace:serviceAccount pairs. Tenant-level IRSA roles in `terraform/modules/tenant-apps/main.tf` follow the same pattern. Kubernetes service accounts carry `eks.amazonaws.com/role-arn` annotations. OIDC-based authentication provides per-principal attribution natively.
- **Gap**: Machine identity authentication is well-implemented. However, audit attribution requires CloudTrail to be enabled (see AUTH-Q7), which is not currently the case.
- **Recommendation**: Enable EKS control plane audit logging to ensure IRSA-based agent calls are recorded with full principal attribution.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/workshop/main.tf`, `terraform/modules/tenant-apps/main.tf`, `gitops/infrastructure/production/03-argo-workflows.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Two IRSA roles are attached to `arn:aws:iam::aws:policy/AdministratorAccess`: `argo-workflows-irsa` and `tf-controller` in `terraform/modules/gitops-saas-infra/main.tf`. The Karpenter policy uses `Resource: "*"` with condition-based restrictions. VS Code CloudFormation role in `helpers/vs-code-ec2.yaml` also uses AdministratorAccess. In contrast, tenant-level policies in `terraform/modules/tenant-apps/main.tf` are properly scoped with specific actions on specific resources.
- **Gap**: AdministratorAccess on argo-workflows and tf-controller IRSA roles violates least-privilege. Any agent assuming these roles has unrestricted AWS API access.
- **Recommendation**: Replace AdministratorAccess on argo-workflows and tf-controller IRSA roles with custom policies scoped to required actions and resources.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `helpers/vs-code-ec2.yaml`, `terraform/modules/tenant-apps/main.tf`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Two Kubernetes ClusterRoles grant wildcard permissions: `full-permissions-cluster-role` (bound to `argoworkflows-sa`) and `argo-events-cluster-role` (bound to `argo-events-sa`) both with `apiGroups: ["*"], resources: ["*"], verbs: ["*"]`. Tenant-level IAM policies do enforce action-level control with specific SQS, DynamoDB, and SSM actions.
- **Gap**: Kubernetes RBAC does not enforce action-level authorization for Argo Workflows and Argo Events service accounts.
- **Recommendation**: Replace wildcard ClusterRoles with scoped ClusterRoles listing only required apiGroups, resources, and verbs.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`, `terraform/modules/tenant-apps/main.tf`

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
- **Finding**: Mixed credential management patterns. Secure: Gitea admin password stored in SSM SecureString, Gitea tokens stored in SSM SecureString, `gitea_token` variable marked `sensitive = true`. Insecure: `kubernetes_secret "flux_system"` in `terraform/modules/flux_cd/main.tf` stores credentials in plaintext Kubernetes Opaque secret. Argo Workflow templates pass `GIT_TOKEN` as plaintext workflow parameters visible in UI and logs. No credential rotation mechanism defined.
- **Gap**: Kubernetes secrets store credentials in base64-encoded plaintext. Git tokens are passed as plaintext workflow parameters. No rotation mechanism exists.
- **Recommendation**: Migrate to AWS Secrets Manager with Secrets Store CSI Driver. Implement credential rotation. Replace workflow parameter-based credential passing with secret volume mounts.
- **Evidence**: `terraform/modules/flux_cd/main.tf`, `terraform/workshop/main.tf`, `terraform/modules/gitea/userdata.sh`, `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No `aws_cloudtrail` resource defined in any Terraform file. No CloudWatch Log Group resources defined. No S3 bucket with object lock for immutable log storage. No EKS control plane logging enabled. Searched all `.tf` files for `cloudtrail`, `cloudwatch_log_group`, `object_lock` — zero results.
- **Gap**: No immutable audit logging infrastructure. Write operations by agent-assumed IRSA roles will not be recorded in an immutable, tamper-evident trail.
- **Recommendation**: Add `aws_cloudtrail` with log file validation, S3 bucket with object lock, and EKS control plane logging (`cluster_enabled_log_types = ["api", "audit", "authenticator"]`).
- **Evidence**: All `.tf` files — absence of CloudTrail, CloudWatch Log Groups, and object lock configuration.

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: IRSA roles are defined in Terraform with Kubernetes service account associations. No explicit suspension mechanism exists. Disabling an agent identity requires modifying IRSA trust policies in Terraform or deleting Kubernetes service accounts — neither is instantaneous. No runbook or automated suspension procedure exists.
- **Gap**: No immediate suspension capability for individual agent identities.
- **Recommendation**: Implement an operational runbook for identity suspension. Consider IAM inline policy deny overrides for rapid suspension without full Terraform plan-apply.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/workshop/main.tf`

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
- **Finding**: No distributed tracing infrastructure defined. Searched all IaC and GitOps files for `opentelemetry`, `otel`, `x-ray`, `xray`, `tracing` — zero results. No CloudWatch Log Groups defined. No Fluentd or Fluent Bit logging agents deployed. Only observability tooling: Metrics Server (CPU/memory only) and Kubecost with Prometheus (cost metrics only).
- **Gap**: No distributed tracing and no structured logging infrastructure. Agent-initiated request failures cannot be traced across services.
- **Recommendation**: Add ADOT Collector and Fluent Bit HelmReleases. Enable EKS control plane logging. Define CloudWatch Log Groups with retention in Terraform.
- **Evidence**: `gitops/infrastructure/production/01-metric-server.yaml`, `gitops/infrastructure/production/05-kubecost.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration exists. Searched for `aws_cloudwatch_metric_alarm`, `pagerduty`, `opsgenie` — zero results. Prometheus has basic scrape config but no alerting rules or Alertmanager. Kubecost provides cost anomalies only.
- **Gap**: No alerting thresholds for error rates, latency, or infrastructure health.
- **Recommendation**: Add CloudWatch alarms for EKS health metrics. Configure Alertmanager via Kubecost Prometheus stack.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml`, `terraform/workshop/main.tf`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Kubecost provides infrastructure cost metrics with per-namespace cost attribution and network cost tracking. Prometheus scrapes at 1-minute intervals. No custom CloudWatch metrics for business outcomes. No dashboards for tenant onboarding success rates, workflow completion rates, or provisioning times.
- **Implication**: Cost metrics exist for monitoring agent-induced spend but no business outcome metrics to evaluate agent effectiveness.
- **Recommendation**: Define custom CloudWatch metrics for tenant onboarding success/failure rate, Argo Workflow completion rate, and mean provisioning time.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml`, `gitops/infrastructure/production/01-metric-server.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: (1) IaC defined: YES — Terraform across `terraform/workshop/`, `terraform/modules/`. GitOps layer in `gitops/` with Flux Kustomizations and HelmReleases. (2) Change review: NOT EVIDENCED — no CODEOWNERS, no branch protection, no PR review config. (3) Drift detection: NOT EVIDENCED — no AWS Config rules, no `terraform plan` in CI, no drift detection.
- **Gap**: 1 of 3 governance sub-checks passes. No mandatory peer review or drift detection for infrastructure changes.
- **Recommendation**: Enable Gitea branch protection. Create Gitea Actions workflow for `terraform plan` on PRs. Add AWS Config rules for drift detection.
- **Evidence**: `terraform/workshop/main.tf`, `terraform/modules/gitea/userdata.sh`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, or `buildspec.yml`. `terraform/gitea-ci-test/` is a test Terraform config, not a CI pipeline. `install.sh`/`destroy.sh` are manual scripts. Gitea Actions runner is provisioned but no workflow files exist in repo root. Only workflows are microservice build pipelines in `tenant-microservices/`.
- **Gap**: No CI/CD pipeline for infrastructure. No contract testing, no automated validation.
- **Recommendation**: Create `.gitea/workflows/terraform-ci.yml` with `terraform validate`, `plan`, `tflint`, and Checkov.
- **Evidence**: `terraform/install.sh`, `terraform/destroy.sh`, `terraform/gitea-ci-test/main.tf`, `terraform/modules/gitea/userdata.sh`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Flux HelmReleases have implicit rollback but no explicit configuration (`remediation.retries`, `rollback.enable`). Kustomizations use `prune: true` (forward-only). `destroy.sh` provides full teardown but not targeted rollback. No blue/green, canary, or traffic-shifting patterns. Git revert triggers Flux reconciliation as a de facto rollback.
- **Gap**: No explicit rollback configuration. Recovery depends on Git revert or complete teardown.
- **Recommendation**: Add explicit rollback config to HelmReleases (`spec.upgrade.remediation`). Document a rollback runbook.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/clusters/production/infrastructure.yaml`, `terraform/destroy.sh`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Minimal testing. Only `helm-charts/application-chart/templates/tests/test-connection.yaml` (basic wget connectivity test). `terraform/gitea-ci-test/` is infrastructure smoke testing. No Postman, pytest, REST Assured, or integration tests. No CI pipeline runs tests.
- **Gap**: No automated infrastructure contract or integration tests.
- **Recommendation**: Implement `terratest` for infrastructure integration testing. Add `terraform validate` to CI.
- **Evidence**: `helm-charts/application-chart/templates/tests/test-connection.yaml`, `terraform/gitea-ci-test/main.tf`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: Inconsistent encryption. Encrypted: ECR repos (AES256), SQS queues (SSE), Gitea EC2 EBS (encrypted=true), VS Code S3 bucket (AES256). Not encrypted with KMS: S3 buckets `argo_artifacts` and `codeartifacts` (Checkov skip CKV2_AWS_145), DynamoDB `consumer_ddb` (Checkov skip CKV2_AWS_119). No customer-managed KMS keys anywhere.
- **Gap**: S3 buckets and DynamoDB tables lack KMS encryption. Checkov checks explicitly skipped.
- **Recommendation**: Enable KMS encryption on all S3 buckets and DynamoDB tables. Create customer-managed KMS key. Remove Checkov skip annotations.
- **Evidence**: `terraform/modules/gitops-saas-infra/apps_needs.tf`, `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/tenant-apps/main.tf`, `terraform/modules/gitea/main.tf`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: Partially defined. Gitea SG has specific ingress rules. Flux `networkPolicy=true`. VPC with public/private subnets. Gaps: EKS `cluster_endpoint_public_access=true`. Kubecost `networkPolicy.enabled: false`. Argo Workflows exposed via internet-facing LB with `--auth-mode=server` (no auth). Kubecost exposed via internet-facing LB. No WAF. No CORS. No API Gateway.
- **Gap**: Critical services exposed to internet without auth or WAF. EKS API publicly accessible. Kubecost network policies disabled.
- **Recommendation**: Change LB annotations to `internal`. Set `cluster_endpoint_public_access=false`. Enable Kubecost network policies. Deploy WAF.
- **Evidence**: `terraform/workshop/main.tf`, `terraform/modules/gitea/main.tf`, `terraform/modules/flux_cd/main.tf`, `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/05-kubecost.yaml`

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/workshop/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q6, AUTH-Q7, AUTH-Q8, OBS-Q2, ENG-Q1, ENG-Q6 |
| `terraform/workshop/saas_gitops.tf` | AUTH-Q6 |
| `terraform/workshop/versions.tf` | ENG-Q1 |
| `terraform/workshop/variables.tf` | ENG-Q1 |
| `terraform/modules/gitops-saas-infra/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, AUTH-Q8, OBS-Q1, ENG-Q5 |
| `terraform/modules/gitops-saas-infra/apps_needs.tf` | ENG-Q5 |
| `terraform/modules/gitops-saas-infra/variables.tf` | AUTH-Q1 |
| `terraform/modules/tenant-apps/main.tf` | AUTH-Q2, AUTH-Q3, ENG-Q5 |
| `terraform/modules/gitea/main.tf` | AUTH-Q6, ENG-Q5, ENG-Q6 |
| `terraform/modules/flux_cd/main.tf` | AUTH-Q6, ENG-Q6 |
| `terraform/modules/flux_cd/variables.tf` | AUTH-Q6 |
| `terraform/gitea-ci-test/main.tf` | ENG-Q2, ENG-Q4 |
| `helpers/vs-code-ec2.yaml` | AUTH-Q2, ENG-Q5 |

### GitOps / Kubernetes Configurations
| File | Questions Referenced |
|------|---------------------|
| `gitops/infrastructure/production/03-argo-workflows.yaml` | AUTH-Q1, AUTH-Q3, ENG-Q3, ENG-Q6 |
| `gitops/infrastructure/production/06-argo-events.yaml` | AUTH-Q1, AUTH-Q3 |
| `gitops/infrastructure/production/07-tf-controller.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/01-metric-server.yaml` | OBS-Q1, OBS-Q3 |
| `gitops/infrastructure/production/02-karpenter.yaml` | AUTH-Q1, ENG-Q3 |
| `gitops/infrastructure/production/04-lb-controller.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/05-kubecost.yaml` | OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q6 |
| `gitops/clusters/production/infrastructure.yaml` | ENG-Q3 |
| `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | AUTH-Q6 |
| `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml` | AUTH-Q6 |

### Shell Scripts
| File | Questions Referenced |
|------|---------------------|
| `terraform/install.sh` | ENG-Q2 |
| `terraform/destroy.sh` | ENG-Q2, ENG-Q3 |
| `terraform/modules/gitea/userdata.sh` | AUTH-Q6, ENG-Q1, ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `workflow-scripts/Dockerfile` | AUTH-Q6 |

### Helm Charts
| File | Questions Referenced |
|------|---------------------|
| `helm-charts/application-chart/templates/tests/test-connection.yaml` | ENG-Q4 |
| `helm-charts/helm-tenant-chart/templates/terraform.yaml` | AUTH-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml` | ENG-Q2 |
