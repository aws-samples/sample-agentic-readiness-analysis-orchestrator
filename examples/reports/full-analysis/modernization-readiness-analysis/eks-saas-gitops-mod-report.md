# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | eks-saas-gitops |
| **Date** | 2025-05-18 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | infrastructure-only |
| **Priority** | P1 |
| **Tags** | eks, gitops, terraform, saas, infrastructure |
| **Context** | EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings, everything that is not serverless will run here, EKS will be the centralized platform |
| **Overall Score** | 2.93 / 4.0 |

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true, has_iac_provisioning_aws_resources=true

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 3.09 / 4.0 | 🟡 Partial | Needs Work |
| Application Architecture (APP) | N/A | N/A — all questions not applicable for infrastructure-only | Ready |
| Data Platform (DATA) | 4.00 / 4.0 | ✅ Mature | Ready |
| Security Baseline (SEC) | 2.57 / 4.0 | 🟡 Partial | Needs Work |
| Operations & Observability (OPS) | 2.11 / 4.0 | 🟠 Needs Work | Needs Work |
| **Overall** | **2.93 / 4.0** | **🟡 Partial** | |

**Scoring Notes:**
- INF: (4+4+3+4+3+3+3+3+4+3+3) / 11 = 34/11 = 3.09
- APP: All 6 questions N/A (infrastructure-only repo) → N/A
- DATA: (4) / 1 = 4.00 (DATA-Q1, DATA-Q2, DATA-Q4 are N/A; only DATA-Q3 scored)
- SEC: (2+3+3+2+3+2+3) / 7 = 18/7 = 2.57
- OPS: (1+2+1+2+3+2+1+2+2) / 9 = 19/9 = 2.11
- Overall: (3.09 + 4.00 + 2.57 + 2.11) / 4 = 11.77/4 = 2.93 (APP excluded as N/A)

---

## Classification

**Tier: 🟡 Pilot-Ready**

This repo has 0 High findings, 11 Medium findings, 13 Low findings. The matched rule is: "0 High, ≥2 Medium → Pilot-Ready."

MOD classification note: Unlike ARA (Agentic Readiness Analysis) where "1 High" is an agent-deployment gate, MOD's classification is softer — a single High is a modernization gap, not a deployment blocker. This repo has no High findings because the score-1 questions (OPS-Q1, OPS-Q3, OPS-Q7) are all non-core P2 questions, which map to Medium severity per the unified severity rules.

**Classification Consistency Check:** consistent. Score 2.93 yields "Partial" band which maps to Pilot-Ready; count-based tier is also Pilot-Ready (0 High, ≥2 Medium).

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumented in the infrastructure or GitOps configuration | Cannot trace requests across multi-tenant services; debugging production issues requires manual log correlation |
| 2 | OPS-Q3: Business Metrics | 1 | No custom business metrics — only infrastructure-level monitoring via Kubecost/Prometheus | Cannot measure tenant SaaS outcomes (onboarding time, per-tenant resource usage trends) to inform modernization decisions |
| 3 | SEC-Q1: Audit Logging | 2 | No CloudTrail configuration in this IaC repository despite provisioning account-level resources | Cannot audit API calls to AWS resources provisioned by this infrastructure |
| 4 | SEC-Q5: Secrets Management | 2 | SSM SecureString used but no automated rotation configured; some SSM params are plaintext String type | Credentials may become stale; no rotation policy for Gitea admin password or Flux tokens |
| 5 | OPS-Q7: Incident Response Automation | 1 | No runbooks or automated incident response workflows defined | Incident response is entirely ad hoc; no self-healing or documented recovery procedures |

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 2 | Move to Containers | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 is N/A for infrastructure-only repos; no commercial database engines detected (DynamoDB is AWS-native). |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all databases are fully managed (DynamoDB with PITR). |
| 5 | Move to Managed Analytics | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3 — both meet threshold (≥ 3). |
| 7 | Move to AI | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All primary workloads run on EKS (v1.32) with Managed Node Groups (3x m5.large baseline) and Karpenter v1.4.0 for dynamic node provisioning. The architecture uses fully managed container orchestration with no raw EC2 for application workloads. Gitea runs on a single EC2 instance (m5.large) as an auxiliary development tool, not a production application workload. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `terraform/workshop/main.tf` (EKS module), `gitops/infrastructure/production/02-karpenter.yaml`, `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All persistent data stores are fully managed AWS services: DynamoDB (per-tenant tables with PAY_PER_REQUEST billing and PITR enabled) and SQS (per-tenant queues with SSE). No self-managed databases detected. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table, aws_sqs_queue resources) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Argo Workflows and Argo Events are deployed for tenant lifecycle automation (onboarding, deployment, offboarding) triggered via SQS events. WorkflowTemplates define multi-step processes with validation, Git operations, and Helm release management. However, application-level business workflow orchestration (e.g., Step Functions for payment processing) is not present. |
| **Gap** | Workflow orchestration covers infrastructure automation but not application business logic workflows. |
| **Recommendation** | Consider AWS Step Functions or extending Argo Workflows for business-critical multi-step operations as application services mature on this platform. Given preference for EKS, Argo Workflows is an appropriate choice for in-cluster orchestration. |
| **Evidence** | `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml`, `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Managed messaging infrastructure is fully in place: Amazon SQS (per-tenant queues with SSE) for inter-service communication, SQS for Karpenter interruption handling, and SQS-triggered Argo Events for tenant lifecycle workflows. EventBridge-like patterns implemented via Argo Events + NATS EventBus (3 replicas). All messaging uses managed AWS services or well-architected in-cluster components. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_sqs_queue), `terraform/modules/gitops-saas-infra/main.tf` (karpenter_interruption_queue), `gitops/control-plane/production/workflows/event-bus.yaml` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | VPC with 3 AZs, private subnets for EKS worker nodes, public subnets for load balancers. Karpenter nodes auto-discover subnets via tags. Security groups restrict Gitea access to VSCode VPC CIDR. However, EKS cluster endpoint is set to public access (`cluster_endpoint_public_access = true`), and no VPC endpoints or PrivateLink configurations are present. |
| **Gap** | EKS cluster API endpoint is publicly accessible. No VPC endpoints for AWS services (ECR, STS, S3) — all traffic routes through NAT Gateway. |
| **Recommendation** | Restrict EKS cluster endpoint to private access or add authorized IP ranges. Add VPC endpoints for frequently accessed AWS services (ECR, STS, S3, DynamoDB, SQS) to reduce NAT Gateway costs and improve security posture. |
| **Evidence** | `terraform/workshop/main.tf` (module "vpc", module "eks" with cluster_endpoint_public_access=true), `terraform/modules/gitea/main.tf` (security groups) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS Load Balancer Controller (v1.6.2) is deployed via Flux HelmRelease, providing ALB-based ingress for tenant workloads. Ingress templates in Helm charts reference ALB annotations. However, no API Gateway, AppSync, or CloudFront is configured. The ALB provides routing and health checks but limited throttling or request validation. |
| **Gap** | No throttling, authentication, or request validation at the entry point level. ALB provides basic routing only. |
| **Recommendation** | Consider adding AWS WAF rules on the ALB for rate limiting and request filtering. For tenant-facing APIs, evaluate API Gateway integration for throttling, API keys, and usage plans per tenant tier. |
| **Evidence** | `gitops/infrastructure/production/04-lb-controller.yaml`, `helm-charts/helm-tenant-chart/templates/ingress.yaml` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Karpenter provides node-level auto-scaling with consolidation policy (WhenEmptyOrUnderutilized, 1m cooldown), spot+on-demand instance selection, and CPU limits (4-32 per node, 1000 total). HPA templates exist in Helm charts but are disabled by default (`autoscaling.enabled: false`). DynamoDB uses PAY_PER_REQUEST (implicit scaling). Managed Node Group has min:3/max:5 static range. |
| **Gap** | HPA is not enabled by default for application workloads. No custom scaling metrics (business-metric-driven scaling). Node-level scaling is mature but pod-level scaling requires manual enablement per tenant. |
| **Recommendation** | Enable HPA by default in tenant Helm charts with sensible CPU/memory targets. Consider custom metrics (requests-per-second, queue depth) for scaling decisions as tenant load patterns mature. |
| **Evidence** | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml`, `helm-charts/application-chart/templates/hpa.yaml`, `helm-charts/application-chart/values.yaml` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB has point-in-time recovery (PITR) enabled on all tenant tables. S3 artifact bucket has public access blocked. EKS control plane is AWS-managed (inherent backup). However, no AWS Backup plans, no S3 versioning on artifact buckets, no cross-region backup replication, and no documented restore procedures. |
| **Gap** | No documented restore procedures. No cross-region backup replication. S3 artifact bucket lacks versioning. Gitea (self-hosted Git server) has no backup strategy — loss of Gitea data means loss of GitOps source of truth. |
| **Recommendation** | Add S3 versioning on artifact buckets. Implement Gitea backup strategy (periodic snapshots or migration to a managed Git service). Document DynamoDB PITR restore procedures. Consider AWS Backup for centralized backup management. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (point_in_time_recovery enabled), `terraform/modules/gitops-saas-infra/main.tf` (S3 bucket) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | EKS cluster spans 3 AZs with private subnets across all. Karpenter provisions nodes across multiple AZs. DynamoDB is inherently multi-AZ. NATS EventBus runs 3 replicas. However, single NAT Gateway creates a single point of failure for outbound connectivity. Gitea server is single-instance (no HA). |
| **Gap** | Single NAT Gateway — an AZ failure affecting the NAT Gateway disrupts all outbound traffic. Gitea is single-instance with no failover. |
| **Recommendation** | Deploy NAT Gateways in each AZ for production resilience. Evaluate migrating Gitea to a managed Git service or deploying it with HA (multi-replica with shared storage). |
| **Evidence** | `terraform/workshop/main.tf` (single_nat_gateway = true, azs = 3), `terraform/modules/gitea/main.tf` (single EC2 instance) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive IaC coverage across 5 Terraform modules covering: VPC, EKS, IAM roles/policies, DynamoDB, SQS, S3, ECR, security groups, and Karpenter configuration. GitOps layer (Flux CD) manages all Kubernetes resources declaratively. Helm charts define application deployment patterns. However, no IaC for monitoring (CloudWatch alarms, dashboards), no Route 53 health checks, no AWS Backup plans, and no WAF rules. |
| **Gap** | Operational/DR resources (monitoring alarms, backup plans, health checks, WAF) are not defined in IaC. Estimated 70-85% IaC coverage of total infrastructure. |
| **Recommendation** | Add Terraform resources for CloudWatch alarms, AWS Backup plans, Route 53 health checks, and WAF rules. Consider using Terraform modules for observability-as-code patterns. |
| **Evidence** | `terraform/workshop/`, `terraform/modules/`, `gitops/` (all Flux Kustomizations and HelmReleases) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multi-layered CI/CD: Gitea Actions for Docker build+push to ECR (triggered on main branch push), Flux CD for continuous GitOps reconciliation (1m interval), Flux Image Automation for automatic image tag updates, Argo Workflows for tenant lifecycle automation, and TF Controller for in-cluster Terraform execution. However, no automated testing in the pipeline (no unit tests, no integration tests, no linting), and no infrastructure validation (terraform validate/plan) in CI before merge. |
| **Gap** | No automated testing in CI pipeline. No terraform plan/validate in CI. No security scanning (SAST, container scanning) in the build pipeline. Deployment is automated via GitOps but quality gates are absent. |
| **Recommendation** | Add terraform validate and plan stages to CI. Add container image scanning (ECR scanning or Trivy) to the Docker build pipeline. Add linting (tflint, checkov) as CI gates. Consider adding integration tests for tenant onboarding workflows. |
| **Evidence** | `tenant-microservices/producer/.gitea/workflows/build-and-push.yml`, `gitops/infrastructure/production/07-tf-controller.yaml`, `terraform/modules/flux_cd/main.tf` |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

### Data Platform (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB is a fully managed, serverless database service with no engine version to manage — AWS handles all versioning, patching, and upgrades transparently. SQS is similarly versionless. No RDS or other versioned database engines are present. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table resources — no engine_version parameter needed) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No CloudTrail configuration found in this repository. The repository provisions account-level AWS resources (EKS cluster, VPC, IAM roles, DynamoDB tables) but does not configure CloudTrail for audit logging. EKS control plane logging is not explicitly enabled in the EKS module configuration. |
| **Gap** | No CloudTrail configuration. No EKS control plane audit logging enabled. No log file validation or immutable storage. |
| **Recommendation** | Add CloudTrail with log file validation and S3 Object Lock for immutable storage. Enable EKS control plane logging (api, audit, authenticator). Consider centralizing logs in a dedicated logging account. |
| **Evidence** | `terraform/workshop/main.tf` (EKS module — no cluster_enabled_log_types parameter), absence of aws_cloudtrail resource across all Terraform files |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | SQS queues use AWS-managed SSE (`sqs_managed_sse_enabled = true`). DynamoDB uses AWS-managed encryption by default. S3 bucket has public access blocked. EBS CSI driver is deployed (supports encrypted volumes). However, no customer-managed KMS keys are configured — all encryption uses AWS-managed keys. No explicit KMS key resources defined in Terraform. |
| **Gap** | No customer-managed KMS keys. All encryption relies on AWS-managed keys which provide less control over rotation policies and access auditing. |
| **Recommendation** | Create customer-managed KMS keys for sensitive data stores (DynamoDB, SQS, EBS volumes). Define key rotation policies. Consider a centralized key management strategy across tenant resources. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (sqs_managed_sse_enabled = true), `terraform/workshop/main.tf` (EBS CSI driver addon) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | EKS uses IRSA (IAM Roles for Service Accounts) for pod-level authentication to AWS services. All tenant workloads have scoped IRSA roles. Kubernetes RBAC is implicitly enforced. ALB ingress is configured but no explicit API authentication (OAuth2/JWT) is configured at the ingress level for tenant-facing endpoints. Internal service-to-service communication uses Kubernetes network policies implicitly. |
| **Gap** | No explicit API authentication (OAuth2/JWT/API Gateway authorizers) at the tenant-facing ingress level. Authentication relies on Kubernetes/ALB layer without application-level token validation. |
| **Recommendation** | Add authentication at the ALB level (Cognito integration or OIDC) for tenant-facing APIs. Consider adding an API Gateway in front of the ALB for per-tenant API key management and throttling aligned with the multi-tenancy tiers. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (IRSA roles), `helm-charts/helm-tenant-chart/templates/ingress.yaml`, `gitops/infrastructure/production/04-lb-controller.yaml` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No centralized identity provider (Cognito, Okta, Ping) integration detected. Authentication for tenant services relies on IRSA for AWS service access and Kubernetes service accounts for cluster access. Gitea uses its own local authentication (admin user/password stored in SSM). No SSO or federated identity configuration. |
| **Gap** | No centralized IdP integration. Each component (Gitea, EKS, tenant APIs) manages identity independently. |
| **Recommendation** | Integrate Amazon Cognito as a centralized IdP for tenant-facing applications. Federate EKS access with an organizational IdP via OIDC. Replace Gitea local auth with SSO. |
| **Evidence** | `terraform/workshop/main.tf` (gitea_admin_user/password), `terraform/modules/tenant-apps/main.tf` (IRSA only), absence of aws_cognito_* resources |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | SSM Parameter Store SecureString is used for the Gitea admin password. Kubernetes Secrets are used for Flux Git credentials. Per-tenant SSM parameters store resource ARNs (non-sensitive, String type). No plaintext credentials in source code. However, no AWS Secrets Manager usage and no automated rotation configured on any secret. The Gitea password is generated via `random_password` and stored in SSM but never rotated. |
| **Gap** | No automated rotation on secrets. SSM SecureString used but Secrets Manager (with rotation Lambda) would be more appropriate for credentials requiring rotation. |
| **Recommendation** | Migrate the Gitea admin password to AWS Secrets Manager with rotation. Add rotation for any long-lived credentials. Evaluate External Secrets Operator for Kubernetes to sync Secrets Manager values into cluster secrets automatically. |
| **Evidence** | `terraform/workshop/main.tf` (aws_ssm_parameter "gitea_password" type=SecureString), `terraform/modules/flux_cd/main.tf` (Kubernetes Secret for Git credentials), absence of aws_secretsmanager_* resources |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Karpenter nodes use `al2023@latest` AMI (Amazon Linux 2023 — reasonably hardened baseline). SSM Managed Instance Core policy is attached to Karpenter node role (enables SSM access). EKS managed node group uses default AMI. However, no SSM Patch Manager configuration, no vulnerability scanning (Inspector/Snyk/Trivy), no hardened AMI pipeline (EC2 Image Builder), and no ECR image scanning enabled. |
| **Gap** | No automated patching strategy beyond "latest AMI." No vulnerability scanning on container images or nodes. No hardened base image pipeline. |
| **Recommendation** | Enable ECR image scanning on push. Add Trivy or Snyk container scanning to the CI pipeline. Configure SSM Patch Manager for managed node group instances. Consider Bottlerocket AMIs for Karpenter nodes (minimal attack surface, immutable). |
| **Evidence** | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (al2023@latest), `terraform/modules/gitops-saas-infra/main.tf` (SSM policy attachment) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Checkov skip annotations are present in Terraform code (`# checkov:skip=CKV2_AWS_34`, `# checkov:skip=CKV_AWS_337`) indicating that Checkov IaC scanning is used (at least locally or in a separate pipeline). However, no SAST, DAST, or dependency scanning tools are configured in the Gitea Actions CI pipeline. No Dependabot equivalent, no container scanning, no security gates in the pipeline. |
| **Gap** | Checkov is referenced but not integrated into CI. No container image scanning. No dependency vulnerability scanning in the pipeline. No blocking security gates. |
| **Recommendation** | Add Checkov or tfsec to the Terraform CI pipeline as a blocking gate. Add Trivy container scanning to the Docker build workflow. Add pip-audit for Python dependency scanning. Enable ECR scan-on-push with severity-based deployment gates. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (checkov:skip annotations), `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` (no security scanning steps) |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No X-Ray, OpenTelemetry, or Jaeger configuration found in IaC, Helm charts, or GitOps manifests. No trace ID propagation between services. Kubecost provides cost metrics but not request tracing. |
| **Gap** | Complete absence of distributed tracing. In a multi-tenant, multi-service architecture, request tracing across producer → SQS → consumer → DynamoDB is critical for debugging tenant-specific issues. |
| **Recommendation** | Deploy AWS Distro for OpenTelemetry (ADOT) as a DaemonSet or sidecar on EKS. Instrument tenant microservices with OpenTelemetry SDK. Enable X-Ray integration for SQS and DynamoDB tracing. Consider Amazon Managed Grafana with Tempo for trace visualization. |
| **Evidence** | Absence of any tracing-related resources across all Terraform files, Helm charts, and Kustomize manifests. No OpenTelemetry, X-Ray, or Jaeger references found. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No formal SLO definitions found. However, implicit monitoring exists: Kubecost with embedded Prometheus (1m scrape interval, 32Gi storage) provides infrastructure metrics. Metrics Server is deployed for HPA signals. No CloudWatch alarms on latency or error rates. No error budget tracking. |
| **Gap** | No formal SLO definitions for tenant-facing services. No latency/error-rate alarms despite having Prometheus deployed. |
| **Recommendation** | Define SLOs for tenant onboarding latency, message processing latency (producer→consumer), and API availability per tier. Create Prometheus alerting rules or CloudWatch alarms based on SLO thresholds. Consider per-tier SLOs aligned with the basic/advanced/premium model. |
| **Evidence** | `gitops/infrastructure/production/05-kubecost.yaml` (Prometheus deployed), `gitops/infrastructure/production/01-metric-server.yaml`, absence of CloudWatch alarm resources or PrometheusRule CRDs |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. Kubecost tracks cost allocation (which is valuable) but no metrics for: tenant onboarding success rate, message throughput per tenant, consumer processing latency, or per-tier resource utilization trends. Only default infrastructure metrics from Prometheus/Metrics Server. |
| **Gap** | No business outcome metrics. Cannot measure SaaS platform health from a business perspective (tenant acquisition, processing volume, tier utilization). |
| **Recommendation** | Add custom Prometheus metrics in tenant microservices (messages_processed_total, onboarding_duration_seconds, tenant_api_requests_total by tier). Create Grafana dashboards for business KPIs. Consider CloudWatch custom metrics for cross-account visibility. |
| **Evidence** | `gitops/infrastructure/production/05-kubecost.yaml` (cost only), absence of custom metric exports or CloudWatch put_metric_data in any configuration |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus is deployed (via Kubecost) with 1-minute scrape interval and persistent storage, providing the foundation for alerting. However, no alerting rules (PrometheusRule CRDs), no CloudWatch anomaly detection, no PagerDuty/OpsGenie integration, and no composite alarms are configured. The alerting infrastructure exists but is not utilized. |
| **Gap** | Alerting infrastructure (Prometheus) exists but no alert rules defined. No anomaly detection. No incident notification integration. |
| **Recommendation** | Define PrometheusRule CRDs for critical metrics (node pressure, pod restarts, queue depth, SQS age). Add Alertmanager with PagerDuty/Slack integration. Consider CloudWatch anomaly detection for DynamoDB and SQS metrics. |
| **Evidence** | `gitops/infrastructure/production/05-kubecost.yaml` (Prometheus present), absence of PrometheusRule, Alertmanager, or aws_cloudwatch_metric_alarm resources |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitOps pull-based deployment via Flux CD with 1-minute reconciliation interval. Helm releases use semver ranges (e.g., "0.0.x") enabling automatic minor/patch upgrades. Flux Image Automation automatically updates image tags in Git when new images are pushed. Argo Workflows manages tenant lifecycle with structured onboarding/deployment/offboarding workflows. However, no canary or blue/green deployment strategy — Flux applies changes directly (rolling update default). |
| **Gap** | No canary or blue/green deployments. Changes are applied directly via Flux reconciliation with Kubernetes rolling update strategy. No traffic shifting or progressive delivery. |
| **Recommendation** | Add Flagger (Flux-native progressive delivery) for canary deployments of tenant workloads. Configure automated rollback on failed health checks. Consider per-tier deployment strategies (canary for premium, rolling for basic). |
| **Evidence** | `gitops/clusters/production/` (Flux Kustomizations), `gitops/infrastructure/base/sources/` (image automation), `helm-charts/helm-tenant-chart/templates/deployment.yaml` (default rolling update) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | A Helm test exists (`helm-charts/application-chart/templates/tests/test-connection.yaml`) for basic connectivity validation. The `scripts/tenant-control.sh` provides manual testing capabilities for tenant operations. Workflow scripts include a validation step (`00-validate-tenant.sh`). However, no automated integration test suites run in CI, no end-to-end tests for the tenant onboarding flow, and no contract tests between services. |
| **Gap** | No automated integration tests in CI. No end-to-end testing of the full tenant lifecycle (onboard → produce → consume → offboard). Manual testing via scripts only. |
| **Recommendation** | Create integration tests for the tenant onboarding workflow (trigger SQS → verify Argo Workflow completion → verify Helm release created → verify tenant can produce/consume). Add to CI pipeline or as a scheduled Argo Workflow. Consider using Helm test hooks for post-deployment validation. |
| **Evidence** | `helm-charts/application-chart/templates/tests/test-connection.yaml`, `scripts/tenant-control.sh`, `workflow-scripts/00-validate-tenant.sh`, absence of test suites in CI workflows |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no SSM Automation documents, no self-healing patterns, and no incident response workflows defined. The Argo Workflows infrastructure could support automated remediation but is only used for tenant lifecycle operations. No documented recovery procedures for common failure scenarios (node failure, tenant isolation breach, Flux desync). |
| **Gap** | Complete absence of incident response automation. No documented runbooks. No self-healing patterns despite having the automation infrastructure (Argo Workflows) available. |
| **Recommendation** | Create runbooks for common scenarios (tenant isolation failures, Flux reconciliation failures, node pressure events). Implement self-healing Argo Workflows triggered by Prometheus alerts (e.g., auto-restart stuck tenants, auto-scale on queue depth). Add SSM Automation documents for EC2-level recovery (Gitea). |
| **Evidence** | Absence of any runbook files, SSM Automation documents, or remediation workflows across the entire repository |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubecost provides per-namespace cost dashboards (implicit tenant cost attribution). No per-service dashboards, no named alarm owners, no CODEOWNERS for observability configs, and no team attribution on monitoring resources. The multi-tenant model creates a natural ownership boundary per namespace but this is not formalized in observability tooling. |
| **Gap** | No formalized observability ownership. No per-tenant SLO dashboards. No team/owner attribution on alarms or dashboards. |
| **Recommendation** | Define CODEOWNERS for observability configurations. Create per-tier Grafana dashboards with team ownership annotations. Add owner tags to CloudWatch resources. Consider Kubecost team/namespace allocation for cost ownership. |
| **Evidence** | `gitops/infrastructure/production/05-kubecost.yaml` (namespace-level cost tracking), absence of CODEOWNERS file, absence of owner annotations on any monitoring resource |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Basic tagging present: `Blueprint` tag set via `local.tags` in the workshop module, `Name` tags on tenant resources (DynamoDB, SQS), `karpenter.sh/discovery` and `kubernetes.io/role/*` tags for EKS/Karpenter discovery. However, no consistent tagging strategy across all resources — missing environment, cost-center, team, and service tags. No tag enforcement via AWS Config rules or Tag Policies. No `default_tags` in the AWS provider configuration. |
| **Gap** | Inconsistent tagging — only Name and Blueprint tags. No cost allocation tags, no ownership tags, no environment tags. No enforcement mechanism. No `default_tags` in Terraform AWS provider. |
| **Recommendation** | Add `default_tags` to the AWS provider block with standard tags (Environment, Team, Service, CostCenter). Add required-tags AWS Config rule. Implement Tag Policies via AWS Organizations for enforcement. Ensure all tenant resources inherit tier and tenant_id tags for cost attribution. |
| **Evidence** | `terraform/workshop/main.tf` (local.tags = {Blueprint = var.name}), `terraform/modules/tenant-apps/main.tf` (tags = {Name = var.tenant_id}), `terraform/workshop/providers.tf` (no default_tags block) |

---

## Learning Materials

No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

Relevant general resources for identified gaps:
- [EKS Workshop - Observability](https://www.eksworkshop.com/docs/observability/) — Distributed tracing, metrics, and logging on EKS
- [AWS Well-Architected Framework - Operational Excellence Pillar](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `terraform/workshop/main.tf` | INF-Q1, INF-Q5, INF-Q8, INF-Q9, SEC-Q1, SEC-Q4, SEC-Q5 | EKS cluster, VPC, Gitea, SSM parameters |
| `terraform/modules/tenant-apps/main.tf` | INF-Q2, INF-Q4, INF-Q8, DATA-Q3, SEC-Q2, SEC-Q3, SEC-Q7, OPS-Q9 | Per-tenant DynamoDB, SQS, IRSA, SSM params |
| `terraform/modules/gitops-saas-infra/main.tf` | INF-Q4, SEC-Q6 | Karpenter IAM, SQS interruption queue, S3, IRSA roles |
| `terraform/modules/flux_cd/main.tf` | INF-Q11, SEC-Q5 | Flux Operator, Git secrets |
| `terraform/modules/gitea/main.tf` | INF-Q5, INF-Q9 | Gitea EC2, security groups |
| `terraform/workshop/providers.tf` | OPS-Q9 | Provider configuration (no default_tags) |
| `gitops/infrastructure/production/02-karpenter.yaml` | INF-Q1 | Karpenter HelmRelease |
| `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` | INF-Q1, INF-Q7, SEC-Q6 | Karpenter NodePool, EC2NodeClass |
| `gitops/infrastructure/production/03-argo-workflows.yaml` | INF-Q3 | Argo Workflows HelmRelease |
| `gitops/infrastructure/production/04-lb-controller.yaml` | INF-Q6, SEC-Q3 | AWS LB Controller |
| `gitops/infrastructure/production/05-kubecost.yaml` | OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q8 | Kubecost with Prometheus |
| `gitops/infrastructure/production/06-argo-events.yaml` | INF-Q3 | Argo Events HelmRelease |
| `gitops/infrastructure/production/07-tf-controller.yaml` | INF-Q11 | TF Controller HelmRelease |
| `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml` | INF-Q3 | Tenant onboarding workflow |
| `gitops/control-plane/production/workflows/event-bus.yaml` | INF-Q4, INF-Q9 | NATS EventBus (3 replicas) |
| `gitops/clusters/production/` | OPS-Q5 | Flux Kustomization dependency chain |
| `gitops/infrastructure/base/sources/` | OPS-Q5, INF-Q11 | Image automation sources |
| `helm-charts/application-chart/values.yaml` | INF-Q7 | HPA disabled by default |
| `helm-charts/application-chart/templates/hpa.yaml` | INF-Q7 | HPA template |
| `helm-charts/helm-tenant-chart/templates/ingress.yaml` | INF-Q6, SEC-Q3 | ALB ingress template |
| `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` | INF-Q11, SEC-Q7 | CI pipeline (Docker build only) |
| `helm-charts/application-chart/templates/tests/test-connection.yaml` | OPS-Q6 | Helm test |
| `scripts/tenant-control.sh` | OPS-Q6 | Manual tenant testing |
| `workflow-scripts/00-validate-tenant.sh` | OPS-Q6 | Tenant validation |
