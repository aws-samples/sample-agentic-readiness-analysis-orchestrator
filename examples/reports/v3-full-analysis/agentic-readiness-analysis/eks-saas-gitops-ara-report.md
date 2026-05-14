# Agentic Readiness Analysis Report

**Target**: ./services/eks-saas-gitops
**Date**: 2025-07-14
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: infrastructure-only
**Service Archetype**: N/A (infrastructure-only)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: eks, gitops, terraform, saas, infrastructure
**Context**: EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings, everything that is not serverless will run here, EKS will be the centralized platform.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 4 | **RISK-QUALITY**: 8 | **INFOs**: 1

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 4 |
| RISK-QUALITY | 8 |
| INFO | 1 |
| N/A | 29 |
| Not Evaluated (extended) | 0 |
| **Total** | **43** |

**Core Questions Evaluated**: 14
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 0 (infrastructure-only has no extended questions)
**Questions N/A (repo_type: infrastructure-only)**: 29
**Service Archetype**: N/A (infrastructure-only)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The repository defines multiple IRSA (IAM Roles for Service Accounts) roles for infrastructure controllers — Karpenter (`karpenter_controller` in `terraform/modules/gitops-saas-infra/main.tf`), Argo Workflows (`argo-workflows-irsa-${var.name}`), Argo Events (`argo-events-irsa`), LB Controller (`lb-controller-irsa-${var.name}`), TF Controller (`tf-controller-${var.name}`), EBS CSI (`ebs-csi-${local.name}` in `terraform/workshop/main.tf`), and Image Automation (`image-automation-${local.name}`). The Gitea EC2 instance has its own IAM role (`terraform/modules/gitea/main.tf`). However, there is no dedicated agent identity mechanism — no Cognito user pool or app client, no API key authentication with principal attribution, no mTLS configuration, and no Bedrock AgentCore Identity configuration. The existing IRSA roles are purpose-built for infrastructure controllers and cannot be repurposed for agent authentication without conflating agent identity with controller identity.
- **Gap**: No machine identity authentication mechanism exists for autonomous AI agents. An agent calling infrastructure APIs provisioned by this repo would have no way to authenticate as a distinct principal with audit attribution.
- **Remediation**:
  - **Immediate**: Define a dedicated IRSA role for agent identities with OIDC-scoped namespace/service-account bindings. Alternatively, create Cognito app clients or API Gateway API keys with principal attribution for agent authentication.
  - **Target State**: Each agent identity is a distinct, auditable principal with its own IAM role or credential set. Agent actions are distinguishable from controller actions in audit logs.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q2 (scoped permissions must be defined for the new agent identity), AUTH-Q6 (audit logging must capture agent principal)
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (IRSA role definitions), `terraform/workshop/main.tf` (EBS CSI and image automation IRSA), `terraform/modules/gitea/main.tf` (Gitea IAM role)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Two IRSA roles are granted `AdministratorAccess` — the broadest possible AWS policy: (1) `argo_workflows_eks_role` in `terraform/modules/gitops-saas-infra/main.tf` (`role_policy_arns = { policy = "arn:aws:iam::aws:policy/AdministratorAccess" }`), and (2) `tf_controller_irsa_role` in the same file with identical `AdministratorAccess`. The `karpenter-policy` uses `"Resource": "*"` for 22 EC2/IAM actions. The `lb-controller-irsa-policy` uses `"Resource": "*"` for many ELB/EC2 actions. The `gitea` role's `ecr_access` policy uses `"Resource": "*"` for ECR actions. In contrast, tenant-level IAM policies in `terraform/modules/tenant-apps/main.tf` are well-scoped per tenant (producer-policy scoped to specific SQS ARNs, consumer-policy scoped to specific DynamoDB/SQS ARNs). The Argo Events IRSA has properly scoped SQS permissions (`argosensor-policy`).
- **Gap**: Platform-level IRSA roles (`argo_workflows_eks_role`, `tf_controller_irsa_role`) have unrestricted AWS access. An agent inheriting or operating alongside these roles would have blast radius equivalent to full account access.
- **Compensating Controls**:
  - Restrict any new agent identity role to a narrow set of IAM actions specific to the agent's use case (e.g., read-only EKS, read-only ECR)
  - Implement IAM permission boundaries on all IRSA roles to cap maximum privileges
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `AdministratorAccess` on `argo_workflows_eks_role` and `tf_controller_irsa_role` with purpose-scoped IAM policies enumerating only the specific actions each controller requires. Use IAM permission boundaries as a guardrail.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (lines: `argo_workflows_eks_role` role_policy_arns, `tf_controller_irsa_role` role_policy_arns, `karpenter-policy`, `lb-controller-irsa-policy`), `terraform/modules/gitea/main.tf` (`ecr_access` policy), `terraform/modules/tenant-apps/main.tf` (well-scoped tenant policies)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Two Kubernetes ClusterRoles grant full wildcard permissions: (1) `full-permissions-cluster-role` in `gitops/infrastructure/production/03-argo-workflows.yaml` with `apiGroups: ["*"], resources: ["*"], verbs: ["*"]`, bound to `argoworkflows-sa` via `full-permissions-cluster-role-binding`. (2) `argo-events-cluster-role` in `gitops/infrastructure/production/06-argo-events.yaml` with identical `apiGroups: ["*"], resources: ["*"], verbs: ["*"]`, bound to `argo-events-sa`. These ClusterRoles grant unrestricted cluster-wide access — any service account bound to them can create, delete, and modify any Kubernetes resource in any namespace.
- **Gap**: No action-level authorization exists. The ClusterRoles do not distinguish between read and write operations, nor between resource types. An agent operating through Argo Workflows or Argo Events would inherit full cluster administrative privileges.
- **Compensating Controls**:
  - Create separate, scoped ClusterRoles for agent use cases (e.g., read-only ClusterRole for monitoring, namespace-scoped Role for tenant operations)
  - Use Kubernetes admission controllers (OPA Gatekeeper, Kyverno) to restrict what the wildcard roles can actually do at runtime
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `full-permissions-cluster-role` and `argo-events-cluster-role` with purpose-scoped roles. Argo Workflows needs permissions to create Workflows and manage PVCs; Argo Events needs permissions to create Workflows from Sensors. Neither requires full cluster admin. Define explicit apiGroups, resources, and verbs for each.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml` (ClusterRole `full-permissions-cluster-role`), `gitops/infrastructure/production/06-argo-events.yaml` (ClusterRole `argo-events-cluster-role`)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No `aws_cloudtrail` resource is defined in any Terraform file across all modules (`terraform/workshop/`, `terraform/modules/gitops-saas-infra/`, `terraform/modules/gitea/`, `terraform/modules/flux_cd/`, `terraform/modules/tenant-apps/`). No CloudWatch log group definitions exist for audit trails. No S3 bucket with object lock is configured for immutable log storage. The README references "CloudWatch Integration" and "Audit Logging" in its security section, but no IaC provisions these capabilities. EKS cluster audit logging is not explicitly enabled in the EKS module configuration (`terraform/workshop/main.tf` — no `cluster_enabled_log_types` parameter).
- **Gap**: No audit logging infrastructure is provisioned. Agent actions (or any actions) cannot be traced, attributed, or forensically examined. There is no immutable log store.
- **Compensating Controls**:
  - Enable EKS control plane logging (`cluster_enabled_log_types = ["api", "audit", "authenticator"]`) as an immediate step — this provides Kubernetes API audit logs to CloudWatch
  - Enable AWS CloudTrail in the account (may exist at the organization level outside this repo)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `aws_cloudtrail` resource with S3 bucket (object lock enabled, log file validation enabled). Enable EKS control plane logging by adding `cluster_enabled_log_types` to the EKS module configuration. Configure CloudWatch log retention policies.
- **Evidence**: `terraform/workshop/main.tf` (EKS module — no `cluster_enabled_log_types`), `terraform/modules/gitops-saas-infra/main.tf` (no CloudTrail resource), all Terraform files (searched: no `aws_cloudtrail`, no `aws_cloudwatch_log_group` for audit)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No explicit mechanism for suspending or revoking individual agent identities is defined in the IaC. IRSA roles are bound to Kubernetes service accounts via OIDC, and while IAM roles can theoretically be deactivated by modifying the role's trust policy or detaching policies, no automation, runbook, or procedure is defined for this. The Argo Workflows server is configured with `--auth-mode=server` (noted as "for demonstration purposes only" in `gitops/infrastructure/production/03-argo-workflows.yaml`), meaning no authentication is required to access the Argo UI — there is no identity to suspend. Kubernetes service accounts can be deleted to revoke access, but no automated or documented procedure exists.
- **Gap**: No automated or documented mechanism to suspend a misbehaving agent identity without disrupting other services. The `--auth-mode=server` on Argo Workflows means the UI is unauthenticated, compounding the risk.
- **Compensating Controls**:
  - Document a runbook for IAM role deactivation (detach policies, modify trust policy) as an emergency procedure
  - Implement Kubernetes NetworkPolicy to isolate agent namespaces, allowing network-level suspension
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define agent identities as separate Kubernetes service accounts with dedicated IRSA roles. Create automation (Lambda, Step Functions, or kubectl scripts) to revoke agent access by deleting the service account or detaching the IAM policy. Change Argo Workflows auth-mode from `server` to a proper authentication mode (SSO or client).
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml` (`--auth-mode=server`), `terraform/modules/gitops-saas-infra/main.tf` (IRSA role definitions — no suspension mechanism)

### RISK-QUALITY — Address as Capacity Allows

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SSM Parameter Store is used for storing the Gitea admin password as `SecureString` type (`aws_ssm_parameter.gitea_password` in `terraform/workshop/main.tf`). The Gitea Flux token is also stored in SSM (`/eks-saas-gitops/gitea-flux-token`). However, the `GIT_TOKEN` is passed as a workflow parameter in plaintext through Argo Workflows templates (`gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` — `value: "${gitea_token}"` substituted from ConfigMap, then passed as environment variables to containers in `tenant-onboarding-workflow-template.yaml`). The `kubernetes_secret.flux_system` in `terraform/modules/flux_cd/main.tf` stores Gitea username and token in a Kubernetes Opaque secret. No AWS Secrets Manager is used anywhere. No secret rotation configuration exists for any credential. The `aws_ssm_parameter.gitea_password` has a checkov skip comment: `CKV_AWS_337: Skiping this for now, move to Secrets Manager`.
- **Gap**: Credentials are stored in SSM and K8s secrets without rotation. GIT_TOKEN is passed through workflow parameters and environment variables, visible in Argo Workflows UI and logs. No Secrets Manager integration. No rotation policy.
- **Compensating Controls**:
  - Migrate from SSM Parameter Store to AWS Secrets Manager with automatic rotation enabled
  - Use Kubernetes External Secrets Operator to sync secrets from Secrets Manager rather than hardcoding in Terraform
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate Gitea credentials to AWS Secrets Manager with rotation. Use Kubernetes External Secrets Operator for K8s secret management. Avoid passing tokens as workflow parameters — use mounted secrets or IRSA-based authentication instead.
- **Evidence**: `terraform/workshop/main.tf` (`aws_ssm_parameter.gitea_password` with CKV_AWS_337 skip), `terraform/modules/flux_cd/main.tf` (`kubernetes_secret.flux_system`), `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` (GIT_TOKEN as workflow parameter), `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml` (GIT_TOKEN as env var)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing is configured in any IaC file. No X-Ray daemon, OpenTelemetry collector, Jaeger, or Zipkin is defined in Terraform modules or GitOps manifests. The EKS cluster addons (`terraform/workshop/main.tf`) include only `aws-ebs-csi-driver`, `coredns`, `kube-proxy`, and `vpc-cni` — no observability addons. Kubecost (`gitops/infrastructure/production/05-kubecost.yaml`) deploys Prometheus for cost metrics collection, but this is purpose-built for cost analysis and does not provide distributed tracing or request correlation. Metrics-server (`gitops/infrastructure/production/01-metric-server.yaml`) provides HPA metrics only. No structured logging configuration (JSON log format, correlation IDs, `request_id` fields) exists anywhere in the repository. The README mentions "CloudWatch Integration" and "Amazon Managed Grafana" and "Amazon Managed Service for Prometheus" as architecture components, but no IaC provisions these services.
- **Gap**: No distributed tracing infrastructure. No structured logging configuration. Agent-initiated requests through infrastructure provisioned by this repo cannot be traced or correlated.
- **Compensating Controls**:
  - Deploy AWS Distro for OpenTelemetry (ADOT) as an EKS add-on via Terraform
  - Deploy an OpenTelemetry Collector as a DaemonSet via FluxCD HelmRelease
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add the ADOT EKS add-on to the cluster configuration. Deploy OpenTelemetry Collector via HelmRelease in the GitOps manifests. Configure X-Ray or CloudWatch as the tracing backend. Implement structured JSON logging as a platform standard.
- **Evidence**: `terraform/workshop/main.tf` (cluster_addons — no observability addon), `gitops/infrastructure/production/05-kubecost.yaml` (Kubecost — cost only), `gitops/infrastructure/production/01-metric-server.yaml` (metrics-server — HPA only), `gitops/infrastructure/production/kustomization.yaml` (no tracing component listed)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarm definitions (`aws_cloudwatch_metric_alarm`) exist in any Terraform file. No SNS alert topics are defined. No PagerDuty, OpsGenie, or other incident management integration is configured. Kubecost provides cost alerts but does not monitor API error rates, latency, or availability. The README lists Amazon Managed Grafana and Amazon Managed Service for Prometheus as architecture services, but no IaC provisions them or configures alert rules.
- **Gap**: No alerting infrastructure for error rates, latency, or availability of APIs running on this EKS platform. Degradation of agent-consumed services would not trigger alerts.
- **Compensating Controls**:
  - Deploy Amazon Managed Service for Prometheus (AMP) and configure Prometheus alerting rules via the Kubecost Prometheus instance
  - Configure CloudWatch Container Insights for EKS cluster monitoring with alarms
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Provision Amazon Managed Service for Prometheus and Amazon Managed Grafana via Terraform. Configure Prometheus alerting rules for error rates (5xx), latency (p99), and availability. Set up SNS topics with PagerDuty/OpsGenie integration for alert routing.
- **Evidence**: All Terraform files (searched: no `aws_cloudwatch_metric_alarm`, no `aws_sns_topic`), `gitops/infrastructure/production/05-kubecost.yaml` (Kubecost — cost alerts only), README.md (mentions AMP/AMG but no IaC)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sub-check evaluation: (1) **IaC Defined — PASS**: The infrastructure is comprehensively defined as code. Terraform modules cover VPC, EKS, IAM, ECR, S3, SQS, SSM, and Gitea (`terraform/workshop/`, `terraform/modules/`). Kubernetes resources are defined via Kustomize and HelmRelease manifests (`gitops/`). Helm charts define application templates (`helm-charts/`). (2) **Peer Review — FAIL**: No evidence of PR/code review requirements. Gitea is the Git server but no branch protection rules, required reviewers, or review policies are defined in IaC. The `install.sh` script applies Terraform directly with `--auto-approve`. (3) **Drift Detection — PARTIAL**: FluxCD Kustomizations reconcile Kubernetes resources at 1-minute intervals (`interval: 1m0s`) with `prune: true`, providing drift detection and correction for K8s resources. However, no drift detection exists for Terraform-managed AWS resources — no AWS Config rules, no `terraform plan` in CI, no drift detection tooling.
- **Gap**: Two of three governance sub-checks fail. Changes to infrastructure can be applied without peer review. AWS resource drift is not detected.
- **Compensating Controls**:
  - Configure Gitea branch protection rules requiring at least one reviewer for the main branch
  - Add `terraform plan` as a pre-apply gate (manual or automated)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Gitea branch protection with required reviews. Implement a CI pipeline that runs `terraform plan` on PRs. Deploy AWS Config rules for drift detection on critical resources (IAM roles, security groups, EKS configuration).
- **Evidence**: `terraform/install.sh` (`terraform apply --auto-approve`), `gitops/clusters/production/infrastructure.yaml` (`interval: 1m0s`, `prune: true`), all Terraform files (no AWS Config resources)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline definitions exist in the repository. Searched for: `.github/workflows/` — not found; `.gitlab-ci.yml` — not found; `Jenkinsfile` — not found; `buildspec.yml` — not found. Deployment is driven by manual shell scripts: `terraform/install.sh` (multi-stage Terraform apply with `--auto-approve`) and `terraform/destroy.sh` (cleanup and destroy). Argo Workflows handles tenant lifecycle operations (onboarding, deployment, offboarding) but these are operational workflows, not CI/CD pipelines with testing. FluxCD provides continuous deployment from Git (GitOps reconciliation loop) but not continuous integration with testing, linting, or validation. No contract tests, no OpenAPI validation, no schema comparison tools, no Terraform validation in pipeline exist.
- **Gap**: No CI/CD pipeline. No automated testing of infrastructure changes before deployment. No contract testing. Changes are applied directly via shell scripts without automated validation.
- **Compensating Controls**:
  - Implement `terraform validate` and `terraform plan` as manual pre-apply checks
  - Add `checkov` or `tfsec` scans before applying Terraform changes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a CI pipeline (GitHub Actions, GitLab CI, or CodePipeline) that runs `terraform validate`, `terraform plan`, `checkov` scan, and Kubernetes manifest validation (kubeconform, kustomize build) on every PR. Add policy-as-code checks for IAM policy changes.
- **Evidence**: Repository root (no `.github/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`), `terraform/install.sh` (manual deployment script), `terraform/destroy.sh` (manual destroy script)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: FluxCD/GitOps provides rollback capability for Kubernetes resources via git revert — the entire GitOps paradigm is built on declarative desired state stored in Git. FluxCD Kustomizations reconcile with `prune: true` and 1-minute intervals, meaning a git revert propagates to the cluster within minutes. Helm releases managed by FluxCD support Helm rollback. However, there are no explicit blue/green deployments, canary deployments, or CodeDeploy configurations. Terraform state allows `terraform apply` to roll back AWS infrastructure changes, but no automated rollback triggers exist — rollback requires manual intervention. Karpenter's disruption policy (`consolidationPolicy: WhenEmptyOrUnderutilized` in `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml`) handles node replacement but not application rollback.
- **Gap**: Rollback for Kubernetes resources is functional via GitOps. Rollback for Terraform-managed AWS resources is manual and not automated. No automated rollback triggers exist for either layer.
- **Compensating Controls**:
  - GitOps rollback via `git revert` is already functional for K8s resources (partial compensating control)
  - For Terraform, maintain state backups and document rollback procedures
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Flux notification alerts for failed reconciliations (auto-detect when rollback is needed). Add Terraform state versioning in S3 with automated `terraform plan` on rollback PRs. Consider Argo Rollouts for canary/blue-green deployment patterns for workloads.
- **Evidence**: `gitops/clusters/production/infrastructure.yaml` (`interval: 1m0s`, `prune: true`), `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (Karpenter disruption policy), `terraform/install.sh` (manual apply — no rollback automation)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No test suites exist in the repository. No pytest, Jest, Go test, JUnit, or other test framework files found. No Postman/Newman collections. No contract tests (Pact or similar). The only test artifact is `helm-charts/application-chart/templates/tests/test-connection.yaml` — a Helm test that uses `busybox` to run `wget` against the service endpoint. This is a basic connectivity smoke test, not API test coverage. No `terraform test` files. No `terratest` configurations. No Kubernetes manifest validation tests. No policy tests (OPA/Rego tests, Kyverno policy tests).
- **Gap**: No automated testing of infrastructure or API contracts. The single Helm connectivity test provides minimal validation.
- **Compensating Controls**:
  - Implement `terraform validate` and `terraform plan` as minimum validation
  - Add kubeconform/kubeval for Kubernetes manifest validation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add Terraform testing (terratest or native `terraform test`). Add Kubernetes manifest validation (kubeconform) in a CI pipeline. Add Helm chart unit tests (helm-unittest). Add policy tests for Karpenter NodePool and RBAC configurations.
- **Evidence**: `helm-charts/application-chart/templates/tests/test-connection.yaml` (basic connectivity test only), repository root (no test directories, no test files)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Encryption at rest is partially implemented. **Encrypted with AES256**: ECR repositories use `encryption_configuration { encryption_type = "AES256" }` (`terraform/modules/gitops-saas-infra/apps_needs.tf` — `tenant_helm_chart`, `application_helm_chart`, `argoworkflow_container`, and all microservice repositories). **Encrypted with SSE**: SQS queues use `sqs_managed_sse_enabled = true` (`terraform/modules/gitops-saas-infra/main.tf` — `karpenter_interruption_queue`, `argoworkflows_onboarding_queue`, `argoworkflows_offboarding_queue`, `argoworkflows_deployment_queue`; `terraform/modules/tenant-apps/main.tf` — `consumer_sqs`). **EC2 encrypted**: Gitea EC2 instance uses `root_block_device { encrypted = true }` (`terraform/modules/gitea/main.tf`). **NOT encrypted with KMS**: DynamoDB tables in `terraform/modules/tenant-apps/main.tf` have `# checkov:skip=CKV2_AWS_119: Not using sensitive information` — no KMS encryption. S3 buckets (`argo_artifacts`, `codeartifacts`) have `# checkov:skip=CKV2_AWS_145: This S3 bucket does not required a KMS Encryption` — no KMS encryption. **EKS secrets encryption**: Not configured — the EKS module in `terraform/workshop/main.tf` does not include `encryption_config` for Kubernetes secrets. **No customer-managed KMS keys** are defined anywhere in the repository.
- **Gap**: Encryption uses AWS-managed keys or AES256 throughout — no customer-managed KMS keys. DynamoDB tables and S3 buckets explicitly skip KMS encryption. EKS Kubernetes secrets are not encrypted at the envelope level.
- **Compensating Controls**:
  - AWS-managed encryption (AES256, SSE) provides baseline protection — data is encrypted, just not with customer-managed keys
  - For immediate improvement, enable EKS secrets encryption with a KMS key
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a customer-managed KMS key for the platform. Enable EKS envelope encryption for Kubernetes secrets (`encryption_config` block in EKS module). Migrate S3 buckets and DynamoDB tables to KMS encryption. Remove checkov skip comments and address the underlying findings.
- **Evidence**: `terraform/modules/gitops-saas-infra/apps_needs.tf` (ECR AES256 encryption), `terraform/modules/gitops-saas-infra/main.tf` (SQS SSE), `terraform/modules/tenant-apps/main.tf` (DynamoDB CKV2_AWS_119 skip, SQS SSE), `terraform/modules/gitea/main.tf` (EC2 encrypted root), `terraform/workshop/main.tf` (EKS module — no encryption_config)

---

## INFOs — Architecture and Design Inputs

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Kubecost (`gitops/infrastructure/production/05-kubecost.yaml`) is deployed with Prometheus for cost metrics collection, providing cost-per-tenant and cost-per-namespace visibility. This is a form of business metric but limited to cost efficiency. No custom CloudWatch metrics for business outcomes (tenant onboarding success rates, deployment frequency, MTTR, workflow completion rates) are defined. No custom dashboards exist. The Prometheus instance bundled with Kubecost scrapes kube-state-metrics and node metrics but no application-level business KPIs.
- **Implication**: When agents interact with infrastructure provisioned by this repo, there will be no visibility into business outcomes of agent actions. Cost metrics from Kubecost are useful for FinOps but insufficient for measuring agent effectiveness.
- **Recommendation**: Define custom Prometheus metrics for tenant lifecycle operations (onboarding duration, deployment success rate, offboarding completeness). Expose these via Amazon Managed Service for Prometheus and visualize in Amazon Managed Grafana.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml` (Kubecost with Prometheus)

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
- **Severity**: BLOCKER
- **Finding**: The repository defines multiple IRSA roles for infrastructure controllers: Karpenter (`karpenter_controller`), Argo Workflows (`argo-workflows-irsa-${var.name}`), Argo Events (`argo-events-irsa`), LB Controller (`lb-controller-irsa-${var.name}`), TF Controller (`tf-controller-${var.name}`), EBS CSI (`ebs-csi-${local.name}`), and Image Automation (`image-automation-${local.name}`). The Gitea EC2 instance has its own IAM role. IRSA provides OIDC-based service account identity — a strong foundation for machine identity. However, no dedicated agent identity mechanism exists: no Cognito user pool or app client, no API key authentication with principal attribution, no mTLS configuration, and no Bedrock AgentCore Identity configuration. The IRSA roles are purpose-built for infrastructure controllers and cannot serve as agent identities without conflating concerns.
- **Gap**: No machine identity for autonomous AI agents. Existing IRSA roles serve infrastructure controllers only.
- **Recommendation**: Create a dedicated IRSA role (or set of roles) for agent identities. Define OIDC bindings scoped to an agent-specific namespace and service account. Alternatively, deploy API Gateway with API keys for agent authentication.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf`, `terraform/workshop/main.tf`, `terraform/modules/gitea/main.tf`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Two IRSA roles use `AdministratorAccess`: `argo_workflows_eks_role` and `tf_controller_irsa_role` (both in `terraform/modules/gitops-saas-infra/main.tf`). The `karpenter-policy` uses `"Resource": "*"` for 22 EC2/IAM actions. The `lb-controller-irsa-policy` uses `"Resource": "*"` for many ELB/EC2 actions. In contrast, tenant-level policies in `terraform/modules/tenant-apps/main.tf` are well-scoped per tenant (specific SQS/DynamoDB ARNs). The `argosensor-policy` is scoped to specific SQS queue ARNs.
- **Gap**: Platform-level IRSA roles have unrestricted access. Agent identities inheriting or operating alongside these roles would have excessive blast radius.
- **Recommendation**: Replace `AdministratorAccess` with purpose-scoped policies. Implement IAM permission boundaries.
- **Evidence**: `terraform/modules/gitops-saas-infra/main.tf` (`argo_workflows_eks_role`, `tf_controller_irsa_role`, `karpenter-policy`, `lb-controller-irsa-policy`), `terraform/modules/tenant-apps/main.tf` (well-scoped tenant policies)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Two ClusterRoles grant full wildcard permissions: `full-permissions-cluster-role` in `gitops/infrastructure/production/03-argo-workflows.yaml` (`apiGroups: ["*"], resources: ["*"], verbs: ["*"]`) and `argo-events-cluster-role` in `gitops/infrastructure/production/06-argo-events.yaml` (identical wildcards). Both are bound to their respective service accounts via ClusterRoleBindings.
- **Gap**: No action-level authorization. Wildcard ClusterRoles grant full cluster admin to Argo Workflows and Argo Events service accounts.
- **Recommendation**: Replace wildcard ClusterRoles with scoped roles listing explicit apiGroups, resources, and verbs required by each controller.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: N/A
- **Finding**: This is a `infrastructure-only` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: SSM Parameter Store is used for Gitea password (`SecureString` type) and Gitea Flux token. `kubernetes_secret.flux_system` stores Gitea credentials as an Opaque K8s secret. `GIT_TOKEN` is passed as a workflow parameter through Argo Workflows templates and exposed as environment variables in workflow containers. No AWS Secrets Manager is used. No secret rotation is configured. The SSM parameter has a checkov skip noting `move to Secrets Manager`.
- **Gap**: No Secrets Manager integration, no secret rotation, GIT_TOKEN exposed in workflow parameters.
- **Recommendation**: Migrate to AWS Secrets Manager with rotation. Use External Secrets Operator. Avoid passing tokens as workflow parameters.
- **Evidence**: `terraform/workshop/main.tf` (`aws_ssm_parameter.gitea_password`), `terraform/modules/flux_cd/main.tf` (`kubernetes_secret.flux_system`), `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` (GIT_TOKEN parameter), `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml` (GIT_TOKEN env var)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No `aws_cloudtrail` resource in any Terraform file. No CloudWatch log groups for audit trails. No S3 bucket with object lock for immutable logs. EKS cluster audit logging is not explicitly enabled (no `cluster_enabled_log_types` in EKS module). README references CloudWatch and audit logging but no IaC evidence.
- **Gap**: No audit logging infrastructure. Agent actions cannot be traced or attributed.
- **Recommendation**: Add `aws_cloudtrail` with S3 object lock. Enable EKS control plane logging. Configure CloudWatch log retention.
- **Evidence**: `terraform/workshop/main.tf` (EKS module — no cluster_enabled_log_types), all Terraform modules (no aws_cloudtrail)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No explicit suspension mechanism. IRSA roles can be deactivated via IAM but no automation or runbook exists. Argo Workflows uses `--auth-mode=server` (unauthenticated access). No documented emergency revocation procedure.
- **Gap**: No automated mechanism to suspend agent identities. Argo Workflows UI is unauthenticated.
- **Recommendation**: Define agent identities as separate service accounts with IRSA. Create revocation automation. Change Argo Workflows auth-mode from `server` to SSO/client.
- **Evidence**: `gitops/infrastructure/production/03-argo-workflows.yaml` (`--auth-mode=server`), `terraform/modules/gitops-saas-infra/main.tf` (IRSA roles)

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

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
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
- **Finding**: No distributed tracing infrastructure (X-Ray, OpenTelemetry, Jaeger, Zipkin) in any Terraform module or GitOps manifest. EKS cluster addons include only `aws-ebs-csi-driver`, `coredns`, `kube-proxy`, `vpc-cni`. Kubecost deploys Prometheus for cost metrics only. Metrics-server provides HPA metrics only. No structured logging (JSON, correlation IDs) configured. README mentions CloudWatch, AMG, and AMP but no IaC provisions them.
- **Gap**: No tracing or structured logging. Agent-initiated requests cannot be traced.
- **Recommendation**: Deploy ADOT as EKS add-on. Deploy OpenTelemetry Collector via HelmRelease. Configure X-Ray/CloudWatch backend.
- **Evidence**: `terraform/workshop/main.tf` (cluster_addons), `gitops/infrastructure/production/05-kubecost.yaml`, `gitops/infrastructure/production/01-metric-server.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms, no SNS topics, no PagerDuty/OpsGenie integration in any Terraform file. Kubecost provides cost alerts only. README mentions AMG/AMP but no IaC.
- **Gap**: No alerting for error rates, latency, or availability.
- **Recommendation**: Provision AMP and AMG. Configure Prometheus alerting rules. Set up SNS with incident management integration.
- **Evidence**: All Terraform files (no `aws_cloudwatch_metric_alarm`, no `aws_sns_topic`), `gitops/infrastructure/production/05-kubecost.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Kubecost provides cost-per-tenant and cost-per-namespace metrics via Prometheus. No custom business outcome metrics (tenant onboarding success, deployment frequency, MTTR) are defined. No custom dashboards.
- **Implication**: No visibility into business outcomes of agent interactions with this infrastructure.
- **Recommendation**: Define custom Prometheus metrics for tenant lifecycle operations. Expose via AMP and visualize in AMG.
- **Evidence**: `gitops/infrastructure/production/05-kubecost.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: (1) IaC defined — PASS: Comprehensive Terraform modules and GitOps manifests. (2) Peer review — FAIL: No branch protection, no required reviewers. `install.sh` uses `--auto-approve`. (3) Drift detection — PARTIAL: FluxCD reconciles K8s resources at 1-minute intervals with `prune: true`. No AWS Config for Terraform-managed resources.
- **Gap**: No peer review enforcement. No AWS resource drift detection.
- **Recommendation**: Configure Gitea branch protection. Implement CI with `terraform plan`. Deploy AWS Config.
- **Evidence**: `terraform/install.sh`, `gitops/clusters/production/infrastructure.yaml`, all Terraform files (no AWS Config)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline definitions (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml` — all absent). Deployment via shell scripts (`install.sh`, `destroy.sh`). FluxCD provides CD but not CI with testing. No contract tests, no validation tools.
- **Gap**: No CI/CD pipeline. No automated testing before deployment.
- **Recommendation**: Create CI pipeline with `terraform validate`, `terraform plan`, `checkov`, and kubeconform on every PR.
- **Evidence**: Repository root (no CI/CD files), `terraform/install.sh`, `terraform/destroy.sh`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: GitOps provides K8s rollback via git revert (FluxCD reconciles in 1-minute intervals with `prune: true`). Helm releases support rollback. Terraform requires manual rollback. No automated rollback triggers. No blue/green or canary deployments.
- **Gap**: Terraform rollback is manual. No automated rollback triggers.
- **Recommendation**: Add Flux notification alerts for failed reconciliations. Implement Terraform state versioning. Consider Argo Rollouts for workloads.
- **Evidence**: `gitops/clusters/production/infrastructure.yaml`, `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml`, `terraform/install.sh`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: No test suites (pytest, Jest, Go test, terratest). Only a basic Helm test (`helm-charts/application-chart/templates/tests/test-connection.yaml` — busybox wget). No contract tests. No manifest validation tests.
- **Gap**: No automated testing of infrastructure APIs or contracts.
- **Recommendation**: Add terratest or `terraform test`. Add kubeconform. Add Helm unit tests. Add policy tests.
- **Evidence**: `helm-charts/application-chart/templates/tests/test-connection.yaml`, repository root (no test files)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: ECR: AES256 encryption. SQS: SSE enabled. Gitea EC2: encrypted root block device. DynamoDB: checkov skip CKV2_AWS_119 (no KMS). S3: checkov skip CKV2_AWS_145 (no KMS). EKS: no `encryption_config` for secrets. No customer-managed KMS keys.
- **Gap**: No customer-managed KMS keys. DynamoDB and S3 skip KMS. EKS secrets not encrypted.
- **Recommendation**: Create customer-managed KMS key. Enable EKS envelope encryption. Migrate S3/DynamoDB to KMS. Remove checkov skips.
- **Evidence**: `terraform/modules/gitops-saas-infra/apps_needs.tf` (ECR), `terraform/modules/gitops-saas-infra/main.tf` (SQS), `terraform/modules/tenant-apps/main.tf` (DynamoDB skip), `terraform/modules/gitea/main.tf` (EC2), `terraform/workshop/main.tf` (EKS — no encryption_config)

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/modules/gitops-saas-infra/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, OBS-Q1, ENG-Q5 |
| `terraform/modules/gitops-saas-infra/apps_needs.tf` | ENG-Q5 |
| `terraform/modules/gitops-saas-infra/variables.tf` | AUTH-Q1 |
| `terraform/workshop/main.tf` | AUTH-Q1, AUTH-Q5, AUTH-Q6, OBS-Q1, ENG-Q1, ENG-Q5 |
| `terraform/workshop/saas_gitops.tf` | AUTH-Q5 |
| `terraform/modules/gitea/main.tf` | AUTH-Q1, AUTH-Q2, ENG-Q5 |
| `terraform/modules/tenant-apps/main.tf` | AUTH-Q2, ENG-Q5 |
| `terraform/modules/flux_cd/main.tf` | AUTH-Q5 |

### Kubernetes / GitOps Manifests
| File | Questions Referenced |
|------|---------------------|
| `gitops/infrastructure/production/03-argo-workflows.yaml` | AUTH-Q3, AUTH-Q7 |
| `gitops/infrastructure/production/06-argo-events.yaml` | AUTH-Q3 |
| `gitops/infrastructure/production/05-kubecost.yaml` | OBS-Q1, OBS-Q2, OBS-Q3 |
| `gitops/infrastructure/production/01-metric-server.yaml` | OBS-Q1 |
| `gitops/infrastructure/production/kustomization.yaml` | OBS-Q1 |
| `gitops/infrastructure/production/07-tf-controller.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/02-karpenter.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/04-lb-controller.yaml` | AUTH-Q1 |
| `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` | ENG-Q3 |
| `gitops/clusters/production/infrastructure.yaml` | ENG-Q1, ENG-Q3 |
| `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | AUTH-Q5 |
| `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml` | AUTH-Q5 |

### Helm Charts
| File | Questions Referenced |
|------|---------------------|
| `helm-charts/application-chart/templates/tests/test-connection.yaml` | ENG-Q4 |

### Scripts
| File | Questions Referenced |
|------|---------------------|
| `terraform/install.sh` | ENG-Q1, ENG-Q2, ENG-Q3 |
| `terraform/destroy.sh` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `workflow-scripts/Dockerfile` | AUTH-Q1 (workflow container) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `README.md` | OBS-Q1, OBS-Q2 |
