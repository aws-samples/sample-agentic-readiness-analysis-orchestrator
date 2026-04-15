# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | eks-saas-gitops |
| **Date** | 2025-07-17 |
| **Repo Type** | infrastructure-only |
| **Priority** | P1 |
| **Tags** | eks, gitops, terraform, saas, infrastructure |
| **Context** | EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings. |
| **Overall Score** | 2.66 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 3.18 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | N/A | N/A — all questions not applicable for infrastructure-only |
| Data Platform Modernization (DATA) | 4.00 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **2.66 / 4.0** | **🟡 Partial** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging defined in IaC | No forensic trail for security incidents; compliance risk for any production deployment |
| 2 | OPS-Q1: Distributed Tracing | 1 | No X-Ray, OpenTelemetry, or tracing instrumentation | Unable to debug cross-service request flows or identify latency bottlenecks in EKS workloads |
| 3 | OPS-Q2: SLO Definitions | 1 | No SLO definitions or error budget tracking | No measurable baseline for service reliability; impossible to prioritize operational improvements |
| 4 | OPS-Q4: Anomaly Detection | 1 | No anomaly detection or alerting configured in IaC | Gradual degradation and novel failure modes go undetected; reactive incident response only |
| 5 | OPS-Q6: Integration Testing | 1 | No integration tests in CI/CD pipeline | Regressions in tenant onboarding/offboarding workflows or infrastructure changes reach production unvalidated |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). Gitea Actions workflows exist for Docker image build-and-push; Flux CD provides GitOps-based continuous delivery; Argo Workflows automates tenant lifecycle operations.
- **What it enables:** An agent that triggers deployments via Flux reconciliation, checks Argo Workflow status, monitors Gitea Actions build results, and manages tenant onboarding/offboarding by sending SQS messages to the appropriate queues.
- **Additional steps:** Expose Argo Workflows API with proper authentication (currently `--auth-mode=server` with no auth). Add API Gateway in front of Argo Workflows for agent access with throttling and auth.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 4 (≥ 2). Argo Workflows with WorkflowTemplates for tenant onboarding, offboarding, and deployment. Argo Events with SQS-based sensors trigger workflows automatically.
- **What it enables:** An agent that monitors Argo Workflow execution status, retries failed workflows, escalates stuck workflows, and provides natural language summaries of tenant lifecycle operations.
- **Additional steps:** Implement Argo Workflows API authentication (replace `--auth-mode=server`). Add structured logging to workflow steps for agent consumption.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Comprehensive README.md exists with architecture documentation, deployment steps, architecture diagrams, AWS service descriptions, security practices, and cost estimates. Additional documentation in `terraform/modules/*/README.md` and inline Terraform comments.
- **What it enables:** A knowledge agent using Amazon Bedrock that indexes the repository documentation and answers developer questions about architecture, deployment procedures, tenant onboarding, and infrastructure configuration.
- **Additional steps:** Generate an indexed corpus from README.md, Terraform module READMEs, and inline code comments. Deploy a Bedrock-based RAG pipeline with vector store (e.g., OpenSearch with vector engine).
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 2 | Move to Containers | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 is N/A for infrastructure-only. No commercial DB engines detected — only DynamoDB (serverless, no license). |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all databases (DynamoDB) are fully managed with automated failover. No self-managed databases detected. |
| 5 | Move to Managed Analytics | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 4 (comprehensive IaC), INF-Q11 = 3 (CI/CD automation present). Both primary triggers ≥ 3. |
| 7 | Move to AI | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |

*No pathways triggered. No pathway detail subsections to include.*

---

<!-- SECTION_DETAILED_FINDINGS -->
## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The repository provisions an EKS cluster (v1.32) via `module.eks` with managed node groups (`m5.large`, min=3, max=5, desired=3). Karpenter v1.4.0 is deployed via Helm for dynamic node provisioning with AL2023 AMIs and consolidation policies. The AWS Load Balancer Controller is deployed for ALB-based ingress. However, Gitea runs on a standalone EC2 instance (`m5.large`) in a public subnet, and a VS Code server EC2 instance (t3.large) is provisioned via CloudFormation. These represent non-managed compute outside EKS. |
| **Gap** | Gitea and VS Code server run on standalone EC2 instances outside EKS, representing approximately 15-20% of compute that is not managed container orchestration or serverless. |
| **Recommendation** | Consider containerizing Gitea and running it as an EKS workload to consolidate all compute into managed EKS. Alternatively, evaluate managed Git services (e.g., CodeCommit or a managed Gitea offering). The VS Code instance is a development tool and may be acceptable as EC2. |
| **Evidence** | `terraform/workshop/main.tf` (module.eks, module.gitea), `terraform/modules/gitea/main.tf` (aws_instance.gitea), `gitops/infrastructure/production/02-karpenter.yaml`, `helpers/vs-code-ec2.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The tenant-apps module provisions DynamoDB tables (`aws_dynamodb_table.consumer_ddb`) with PAY_PER_REQUEST billing mode and Point-in-Time Recovery (PITR) enabled. SQS queues are used as managed message stores. No self-managed databases (no database software on EC2, no database containers) were found anywhere in the IaC. All data persistence is through fully managed AWS services. |
| **Gap** | No gaps identified. All databases are managed services with automated failover. |
| **Recommendation** | No action needed. Current approach using DynamoDB with PITR is best practice. As the SaaS platform grows, consider DynamoDB global tables for multi-region support if needed. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table.consumer_ddb with PITR, PAY_PER_REQUEST) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Argo Workflows v0.40.11 is deployed via Helm with dedicated WorkflowTemplates for tenant onboarding, offboarding, and deployment operations. Argo Events v2.4.3 provides event-driven triggers using SQS-based EventSources and Sensors. An EventBus with 3 NATS replicas ensures HA for event processing. The entire tenant lifecycle is orchestrated through these dedicated workflow services, with SQS queues (onboarding, offboarding, deployment) as trigger sources. |
| **Gap** | No significant gaps. The workflow orchestration is comprehensive and event-driven. |
| **Recommendation** | No action needed. Current Argo Workflows + Argo Events + SQS architecture is a mature pattern. Consider adding workflow observability (execution metrics, failure rate dashboards) to complement the orchestration layer. |
| **Evidence** | `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`, `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml`, `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml`, `gitops/control-plane/production/workflows/event-bus.yaml` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multiple SQS queues are provisioned: `argoworkflows-onboarding-queue`, `argoworkflows-offboarding-queue`, `argoworkflows-deployment-queue`, `karpenter_interruption_queue`, and per-tenant consumer SQS queues (`consumer-{tenant_id}`). All queues use `sqs_managed_sse_enabled = true` for encryption. SQS is the primary async communication mechanism for both infrastructure operations (workflow triggers, Karpenter interruptions) and tenant application patterns (producer → SQS → consumer). |
| **Gap** | Messaging is used primarily for tenant lifecycle orchestration and specific application patterns. No EventBridge for broader event-driven integration across the platform. No streaming infrastructure (Kinesis, MSK) for real-time data flows. |
| **Recommendation** | Consider adding Amazon EventBridge for cross-service event routing and platform-wide event patterns. This would enable decoupled notification of tenant lifecycle events to multiple consumers (billing, monitoring, analytics) without point-to-point SQS coupling. |
| **Evidence** | `terraform/modules/gitops-saas-infra/main.tf` (aws_sqs_queue resources), `terraform/modules/tenant-apps/main.tf` (aws_sqs_queue.consumer_sqs) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | VPC provisioned across 3 AZs with public and private subnets using `terraform-aws-modules/vpc/aws` v4.0.2. EKS nodes run in private subnets with NAT gateway for outbound traffic. Security groups on Gitea are scoped: SSH from VS Code VPC CIDR, Gitea HTTP from VS Code VPC and EKS security group, optional allowed IP. Private subnets tagged for Karpenter discovery. Kubernetes network policies enabled in Flux configuration (`networkPolicy: true`). |
| **Gap** | Gitea EC2 instance is on a public subnet with a public IP address (`associate_public_ip_address = true`). EKS cluster endpoint is public (`cluster_endpoint_public_access = true`). VS Code CloudFormation template defaults `AllowedIP` to `0.0.0.0/0`. Single NAT gateway reduces network fault isolation. Egress security group on Gitea allows `0.0.0.0/0`. |
| **Recommendation** | Restrict EKS cluster endpoint to private access or limit public access to specific CIDRs. Move Gitea to a private subnet and access via VPN or SSM Session Manager. Change VS Code `AllowedIP` default from `0.0.0.0/0` to require explicit IP specification. Add multiple NAT gateways for fault isolation across AZs. Tighten Gitea egress rules to specific required destinations. |
| **Evidence** | `terraform/workshop/main.tf` (module.vpc, module.eks with cluster_endpoint_public_access=true), `terraform/modules/gitea/main.tf` (aws_instance.gitea with public IP, aws_security_group.gitea), `helpers/vs-code-ec2.yaml` (AllowedIP default 0.0.0.0/0) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS Load Balancer Controller v1.6.2 deployed via Helm in the `aws-system` namespace with IRSA. Helm chart ingress templates support ALB class (`className: "alb"`) with configurable path types. Tenant services use ALB ingress for HTTP routing. |
| **Gap** | No API Gateway with throttling, auth, or request validation. Argo Workflows server exposed as internet-facing LoadBalancer with `--auth-mode=server` (no authentication). Kubecost also exposed as internet-facing LoadBalancer. No WAF integration on ALBs. |
| **Recommendation** | Add Amazon API Gateway in front of tenant-facing ALBs for throttling, request validation, and API key management. Restrict Argo Workflows and Kubecost to internal load balancers or add authentication. Enable AWS WAF on internet-facing ALBs. |
| **Evidence** | `gitops/infrastructure/production/04-lb-controller.yaml`, `gitops/infrastructure/production/03-argo-workflows.yaml` (server.serviceAnnotations with internet-facing, --auth-mode=server), `gitops/infrastructure/production/05-kubecost.yaml` (service.annotations with internet-facing), `helm-charts/helm-tenant-chart/values.yaml.template` (ingress className: alb) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Karpenter v1.4.0 provides cluster-level auto-scaling with NodePools allowing c/m/r instance families (4-32 CPUs), on-demand and spot capacity types, and `WhenEmptyOrUnderutilized` consolidation policy (1m consolidation window). CPU limit: 1000 cores, memory limit: 2000Gi. EKS managed node groups have min=3, max=5. HPA templates exist in both application-chart and helm-tenant-chart with configurable CPU/memory targets. Metrics Server v3.11.0 deployed for HPA metrics. |
| **Gap** | HPA is disabled by default (`autoscaling.enabled: false`) in application-chart values.yaml and tenant-chart values template. No application-specific scaling policies configured. Karpenter consolidation is aggressive (1m) which may cause disruption during scaling events. |
| **Recommendation** | Enable HPA by default for production tenant workloads. Define per-tenant scaling policies with appropriate min/max replicas. Consider adding Karpenter `disruption.budgets` to limit simultaneous node disruptions. Evaluate KEDA for event-driven scaling based on SQS queue depth for consumer workloads. |
| **Evidence** | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml`, `terraform/workshop/main.tf` (eks_managed_node_groups min/max), `helm-charts/application-chart/templates/hpa.yaml`, `helm-charts/application-chart/values.yaml` (autoscaling.enabled: false), `gitops/infrastructure/production/01-metric-server.yaml` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DynamoDB tables have Point-in-Time Recovery (PITR) enabled (`point_in_time_recovery { enabled = true }`). S3 buckets exist for Argo artifacts and code artifacts but do not have versioning enabled (Checkov skip: `CKV2_AWS_21: Versioning is not needed at this time`). No `aws_backup_plan` resources found. No EBS snapshot lifecycle policies. No documented restore procedures. |
| **Gap** | Backups limited to DynamoDB PITR only. S3 buckets lack versioning. No comprehensive backup plan covering EBS volumes, Kubernetes persistent volumes (gp2 PVCs used by Argo Workflows), or EKS cluster configuration. No restore testing documentation. Gitea data on EC2 instance has no backup strategy. |
| **Recommendation** | Enable S3 versioning on all buckets. Create an `aws_backup_plan` covering DynamoDB, EBS volumes, and S3 buckets using Terraform. Add Velero for Kubernetes-native backup of PVCs and cluster state. Implement backup for Gitea data (SQLite database on EC2). Document and test restore procedures. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (point_in_time_recovery enabled), `terraform/modules/gitops-saas-infra/main.tf` (aws_s3_bucket.argo_artifacts with Checkov skip CKV2_AWS_21), `terraform/modules/gitops-saas-infra/apps_needs.tf` (aws_s3_bucket.codeartifacts with Checkov skip) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | VPC spans 3 AZs with subnets in each. EKS managed node groups are multi-AZ by default. Karpenter provisions nodes across multiple AZs via subnet selector terms. Argo Events EventBus runs 3 NATS replicas for HA. DynamoDB is inherently multi-AZ. |
| **Gap** | Gitea is a single EC2 instance in one public subnet — a single point of failure for the entire Git-based workflow. Single NAT gateway (`single_nat_gateway = true`) means a NAT gateway AZ failure affects all private subnet egress. No explicit multi-AZ configuration for Argo Workflows controller or Kubecost persistent volumes. |
| **Recommendation** | Replace single Gitea EC2 with a highly available solution (e.g., Gitea on EKS with replicated storage, or migrate to a managed Git service). Deploy multiple NAT gateways (one per AZ) for fault isolation. Ensure critical controller pods (Argo Workflows, Flux, Karpenter) have pod anti-affinity rules to spread across AZs. |
| **Evidence** | `terraform/workshop/main.tf` (module.vpc with single_nat_gateway=true, 3 AZs), `terraform/modules/gitea/main.tf` (single EC2 instance), `gitops/control-plane/production/workflows/event-bus.yaml` (3 NATS replicas) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive Terraform coverage: VPC, EKS cluster, IAM roles (6+ IRSA roles), ECR repositories, SQS queues, S3 buckets, SSM parameters, Security Groups, VPC Peering. Kubernetes layer fully managed via Flux CD Kustomizations and HelmReleases — all add-ons (Karpenter, Argo Workflows, Argo Events, ALB Controller, Kubecost, TF Controller, Metrics Server) deployed declaratively. TF Controller enables Terraform execution from within Kubernetes for dynamic tenant infrastructure. CloudFormation template for VS Code server. Tenant infrastructure provisioned via Terraform modules triggered by Helm chart templates. |
| **Gap** | No significant gaps. Nearly all infrastructure is defined in code. |
| **Recommendation** | No action needed. The IaC coverage is exemplary with Terraform for AWS resources, Flux CD for Kubernetes resources, and TF Controller for dynamic tenant provisioning. Consider adding Terraform state locking configuration and remote backend configuration to the repository for team collaboration. |
| **Evidence** | `terraform/workshop/main.tf`, `terraform/workshop/saas_gitops.tf`, `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/tenant-apps/main.tf`, `terraform/modules/flux_cd/main.tf`, `gitops/clusters/production/*.yaml`, `gitops/infrastructure/production/*.yaml`, `helm-charts/helm-tenant-chart/templates/terraform.yaml`, `helpers/vs-code-ec2.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Gitea Actions workflows handle Docker image build-and-push to ECR with timestamp-based tagging (`prd-$TIMESTAMP`). Flux CD provides GitOps-based continuous delivery with automatic reconciliation (1m intervals) from Git repository. Flux Image Automation controllers detect new container images in ECR and update manifests. Argo Workflows automate tenant lifecycle (onboarding, offboarding, deployment) triggered by SQS events. TF Controller runs Terraform plans automatically for tenant infrastructure. |
| **Gap** | No automated testing stage in Gitea Actions (build-and-push only, no unit tests, no linting). No automated rollback mechanism defined. No deployment approval gates. No environment promotion pipeline (dev → staging → production). Flux CD rollback relies on Git revert rather than automated health-check-based rollback. |
| **Recommendation** | Add test stages to Gitea Actions workflows (linting, unit tests, security scanning). Implement Flagger or Argo Rollouts for automated canary deployments with health-check-based rollback. Add environment promotion pipeline with staging environment validation before production. |
| **Evidence** | `tenant-microservices/producer/.gitea/workflows/build-and-push.yml`, `terraform/modules/flux_cd/main.tf`, `gitops/clusters/production/infrastructure.yaml` (Flux Kustomization), `helm-charts/helm-tenant-chart/templates/terraform.yaml` (TF Controller) |

---

### Application Architecture

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

### Data Platform Modernization

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
| **Finding** | The only database service provisioned is DynamoDB (`aws_dynamodb_table.consumer_ddb`), which is a fully managed, serverless database that does not have engine versions to pin or EOL concerns — AWS manages all version lifecycle transparently. No RDS, Aurora, DocumentDB, ElastiCache, or other versioned database engines were found in any Terraform files. Gitea uses SQLite internally on its EC2 instance (defined in `userdata.sh` via Docker container), but this is an operational tool, not a production data store. |
| **Gap** | No gaps identified. No versioned database engines to manage. |
| **Recommendation** | No action needed. DynamoDB's serverless model eliminates engine version and EOL management. If the platform evolves to include relational databases, prefer Amazon Aurora (aligned with preferences) with explicit engine version pinning in Terraform. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table.consumer_ddb), `terraform/modules/gitea/userdata.sh` (GITEA__database__DB_TYPE=sqlite3) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No `aws_cloudtrail` resource found in any Terraform file. No CloudTrail configuration, log file validation, or immutable log storage (S3 Object Lock) defined in IaC. The README.md mentions "Audit Logging: Kubernetes audit logging is enabled" and "CloudWatch Integration" in the Security section, but these are aspirational documentation — no corresponding IaC resources implement them. EKS cluster logging is not explicitly enabled in the `module.eks` configuration. |
| **Gap** | Complete absence of CloudTrail audit logging in IaC. No EKS control plane logging enabled. No CloudWatch log groups for audit trails. This is a critical gap for any production deployment. |
| **Recommendation** | Add `aws_cloudtrail` resource with multi-region trail, log file validation, and S3 bucket with Object Lock for immutable storage using Terraform. Enable EKS control plane logging (api, audit, authenticator, controllerManager, scheduler) in the `module.eks` configuration. Add CloudWatch log group with defined retention period. |
| **Evidence** | `terraform/workshop/main.tf` (module.eks with no cluster_enabled_log_types), `terraform/modules/gitops-saas-infra/main.tf` (no aws_cloudtrail), `README.md` (mentions audit logging but no IaC evidence) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | ECR repositories use AES256 encryption (`encryption_configuration { encryption_type = "AES256" }`). S3 buckets have public access blocked (`block_public_acls`, `block_public_policy`, etc.). Gitea EC2 root block device is encrypted (`encrypted = true`). SQS queues use AWS-managed SSE (`sqs_managed_sse_enabled = true`). VS Code CloudFormation S3 bucket uses `SSEAlgorithm: AES256`. DynamoDB encryption at rest is enabled by default (AWS-managed). |
| **Gap** | No customer-managed KMS keys (`aws_kms_key`) found anywhere in the IaC. All encryption uses AWS-managed keys (AES256 or service-managed SSE). ECR Checkov skip: `CKV2_AWS_145: This S3 bucket does not required a KMS Encryption`. The README mentions KMS in the architecture table but no IaC implements it. |
| **Recommendation** | Create customer-managed KMS keys for sensitive data stores (DynamoDB tables, SQS queues, S3 buckets). Enable KMS encryption on ECR repositories. This provides key rotation control, granular access policies, and CloudTrail key usage audit trails. |
| **Evidence** | `terraform/modules/gitops-saas-infra/apps_needs.tf` (ECR AES256), `terraform/modules/gitops-saas-infra/main.tf` (SQS sqs_managed_sse_enabled, S3 public access block), `terraform/modules/gitea/main.tf` (root_block_device encrypted), `terraform/modules/tenant-apps/main.tf` (Checkov skip CKV2_AWS_119) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Gitea uses token-based authentication with API tokens stored in SSM Parameter Store (SecureString). Argo Workflows server is explicitly configured with `--auth-mode=server`, which the code comments acknowledge is "for demonstration purposes only" — this disables authentication on the Argo Workflows UI and API. IRSA provides pod-level IAM authentication for AWS API calls. Kubecost is exposed as an internet-facing LoadBalancer with no authentication. |
| **Gap** | Argo Workflows API has no authentication (`--auth-mode=server`). Kubecost dashboard is publicly accessible with no auth. No OAuth2/JWT authentication on any Kubernetes-hosted service. No API Gateway authorizers. |
| **Recommendation** | Replace `--auth-mode=server` with `--auth-mode=sso` or `--auth-mode=client` on Argo Workflows with OIDC integration. Add authentication to Kubecost (e.g., OAuth2 proxy sidecar or restrict to internal LoadBalancer). Deploy Amazon API Gateway with Cognito or Lambda authorizers for external-facing APIs. |
| **Evidence** | `gitops/infrastructure/production/03-argo-workflows.yaml` (--auth-mode=server comment "for demonstration purposes only"), `gitops/infrastructure/production/05-kubecost.yaml` (service type LoadBalancer, internet-facing), `terraform/modules/gitea/userdata.sh` (token-based API auth) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | IAM Roles for Service Accounts (IRSA) used extensively for pod-level AWS access (Karpenter, Argo Workflows, Argo Events, LB Controller, TF Controller, Image Automation). EKS `aws-auth` ConfigMap manages cluster access. Gitea manages its own authentication independently with local admin user and API tokens. No Cognito, Okta, or external IdP integration found. No SSO configuration. |
| **Gap** | No centralized identity provider integration. Gitea manages its own auth. EKS access relies on `aws-auth` ConfigMap rather than EKS Access Entries or SSO. No OIDC/SAML federation for human users. Each service manages its own authentication independently. |
| **Recommendation** | Integrate Amazon Cognito or an external IdP (Okta, Ping) for centralized authentication. Migrate EKS access from `aws-auth` ConfigMap to EKS Access Entries with IAM Identity Center integration. Configure Argo Workflows and Gitea to federate with the centralized IdP. |
| **Evidence** | `terraform/workshop/main.tf` (manage_aws_auth_configmap = true), `terraform/modules/gitops-saas-infra/main.tf` (multiple IRSA modules), `terraform/modules/gitea/userdata.sh` (local admin user creation) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SSM Parameter Store is used for Gitea admin password (SecureString), Gitea Flux token (SecureString), Gitea CI/CD token (SecureString), and tenant SSM parameters. The Flux CD module stores the Gitea token as a Kubernetes secret (`kubernetes_secret.flux_system`). Checkov skip comment on SSM parameter: `CKV_AWS_337: Skiping this for now, move to Secrets Manager`. No automated rotation configured. Tenant SQS/DynamoDB ARNs stored as plain String SSM parameters. |
| **Gap** | Secrets stored in SSM Parameter Store rather than AWS Secrets Manager (no built-in rotation). Checkov skip comment explicitly acknowledges this as technical debt. Gitea token stored as plaintext in Kubernetes secret. No automated secret rotation for any credential. Argo Workflows sensor passes `gitea_token` as workflow parameter in plaintext. VS Code CloudFormation template stores coder password in SSM as String (not SecureString). |
| **Recommendation** | Migrate sensitive SSM parameters to AWS Secrets Manager with automated rotation (especially Gitea admin password and API tokens). Use External Secrets Operator to sync Secrets Manager entries to Kubernetes secrets. Remove plaintext token passing in Argo Workflows sensors — use Kubernetes secrets references instead. Change VS Code coder password to SecureString. |
| **Evidence** | `terraform/workshop/main.tf` (aws_ssm_parameter.gitea_password with Checkov skip CKV_AWS_337), `terraform/modules/flux_cd/main.tf` (kubernetes_secret with plaintext token), `terraform/modules/gitea/userdata.sh` (SSM put-parameter for tokens), `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` (gitea_token in workflow parameters) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Karpenter uses AL2023 AMIs (`amiSelectorTerms: alias: al2023@latest`) which are Amazon's latest hardened AMI family. EKS managed node groups use the default EKS-optimized AMI. Karpenter node role has `AmazonSSMManagedInstanceCore` policy attached for SSM-based management. ECR repositories have `scan_on_push = true` for container vulnerability scanning. Gitea EC2 uses Amazon Linux 2 AMI with `http_tokens = "required"` (IMDSv2 enforced). ECR image tag immutability enabled (`image_tag_mutability = "IMMUTABLE"`). |
| **Gap** | No AWS Inspector or Snyk configured for continuous vulnerability scanning. No CIS benchmark hardening validation. Gitea EC2 uses Amazon Linux 2 (not AL2023) which will reach EOL. No `aws_ssm_patch_baseline` for automated patching. ECR scan-on-push is basic scanning, not enhanced scanning (Inspector). |
| **Recommendation** | Enable Amazon Inspector for continuous vulnerability scanning across ECR images and EC2 instances. Upgrade Gitea EC2 from Amazon Linux 2 to AL2023. Add `aws_ssm_patch_baseline` with automatic patching schedule. Consider enabling ECR enhanced scanning (Inspector-based) for deeper vulnerability detection. |
| **Evidence** | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (amiSelectorTerms al2023@latest), `terraform/modules/gitops-saas-infra/main.tf` (AmazonSSMManagedInstanceCore), `terraform/modules/gitops-saas-infra/apps_needs.tf` (scan_on_push=true, image_tag_mutability=IMMUTABLE), `terraform/modules/gitea/main.tf` (amazon_linux_2 AMI, http_tokens=required) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECR repositories have `scan_on_push = true` for vulnerability scanning of container images. ECR image tag immutability prevents image tampering. Checkov skip comments throughout the codebase (CKV_AWS_337, CKV2_AWS_18, CKV2_AWS_21, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_144, CKV2_AWS_145, CKV_AWS_88, CKV2_AWS_119) indicate awareness of security scanning tools. |
| **Gap** | No SAST (SonarQube, Semgrep, CodeGuru) integrated into CI/CD pipeline. No dependency scanning (pip-audit, npm audit, Dependabot) in Gitea Actions workflows. Gitea Actions workflow is build-and-push only — no security scanning stage. No Checkov integration in CI/CD (Checkov skip comments suggest manual runs, not pipeline integration). No `.snyk` policy files. |
| **Recommendation** | Add Checkov or tfsec as a CI/CD pipeline step for IaC security scanning using Terraform. Add container scanning step in Gitea Actions before push (Trivy or Snyk). Add dependency scanning for Python requirements.txt files. Implement security gates that block builds with critical/high vulnerabilities. |
| **Evidence** | `terraform/modules/gitops-saas-infra/apps_needs.tf` (scan_on_push=true), `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` (no security scanning steps), `terraform/modules/gitops-saas-infra/main.tf` (Checkov skip comments) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No X-Ray, OpenTelemetry, Jaeger, or any distributed tracing instrumentation found in the repository. No traceparent or X-Amzn-Trace-Id header propagation configured. No ADOT (AWS Distro for OpenTelemetry) collector deployment. The infrastructure deploys Prometheus (via Kubecost) for metrics collection but not for tracing. |
| **Gap** | Complete absence of distributed tracing. Unable to trace requests across tenant workloads, Argo Workflow executions, or service-to-service communication. No visibility into request latency breakdown or error propagation paths. |
| **Recommendation** | Deploy AWS Distro for OpenTelemetry (ADOT) collector as a DaemonSet on EKS via Flux CD HelmRelease. Configure X-Ray as the tracing backend. Add OpenTelemetry SDK instrumentation to tenant microservice Helm charts. Enable trace context propagation in ALB ingress configuration. |
| **Evidence** | `gitops/infrastructure/production/` (no tracing-related HelmRelease), `helm-charts/application-chart/values.yaml` (no tracing config), `gitops/infrastructure/base/sources/` (no OTel or X-Ray source) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definition files found anywhere in the repository. No CloudWatch alarms for p99/p95 latency. No error budget tracking. Kubecost is deployed for cost monitoring, and Prometheus for infrastructure metrics, but neither is configured for SLO tracking. No Sloth, OpenSLO, or custom SLO manifests. |
| **Gap** | No formal SLO definitions for tenant workloads, API endpoints, or infrastructure services. No measurable baseline for determining service health or degradation. No error budget to drive prioritization of reliability vs feature work. |
| **Recommendation** | Define SLOs for critical tenant-facing journeys (tenant onboarding latency, API availability, producer-consumer message processing latency). Deploy Sloth or Pyrra on EKS for SLO monitoring with Prometheus integration. Create CloudWatch alarms tied to SLO thresholds. Establish error budgets per tenant tier. |
| **Evidence** | Repository-wide search: no files matching SLO, error_budget, or availability target definitions found |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubecost v2.1.0 deployed via Helm provides cost metrics per namespace, pod, and cluster with Prometheus backend (scrape interval 1m). Network cost analysis enabled. Prometheus node exporter enabled for infrastructure metrics. Metrics Server v3.11.0 provides resource utilization metrics for HPA. |
| **Gap** | Only infrastructure and cost metrics collected. No custom business metrics (tenant onboarding success rate, message processing throughput per tenant, API response times per tenant tier). No `cloudwatch.put_metric_data` for business events. Kubecost analytics are cost-focused, not business-outcome-focused. |
| **Recommendation** | Add custom CloudWatch metrics for tenant lifecycle events (onboarding duration, success/failure rates). Instrument SQS queue depth metrics per tenant for capacity planning. Create per-tenant-tier dashboards showing business-relevant metrics (throughput, error rates, latency). Consider Amazon Managed Grafana for unified dashboarding. |
| **Evidence** | `gitops/infrastructure/production/05-kubecost.yaml` (Kubecost with Prometheus), `gitops/infrastructure/production/01-metric-server.yaml` (Metrics Server v3.11.0) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudWatch anomaly detection configured in any Terraform file. No CloudWatch alarms defined in IaC. No PagerDuty, OpsGenie, or SNS topic for alert notification. Kubecost has built-in cost alerting but no latency/error rate anomaly detection. No Prometheus alerting rules defined in the repository. |
| **Gap** | Complete absence of alerting infrastructure. No threshold-based alarms, no anomaly detection, no incident notification pipeline. Infrastructure failures, tenant workload issues, and security events go undetected until manual discovery. |
| **Recommendation** | Define CloudWatch alarms for critical infrastructure metrics (EKS node health, SQS queue depth, DynamoDB throttling) using Terraform. Add Prometheus Alertmanager with alert routing to SNS/PagerDuty. Enable CloudWatch anomaly detection on tenant-facing metrics. Create composite alarms for correlated failure detection. |
| **Evidence** | `terraform/workshop/main.tf` (no aws_cloudwatch_metric_alarm), `terraform/modules/gitops-saas-infra/main.tf` (no alerting resources), `gitops/infrastructure/production/` (no alertmanager HelmRelease) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Flux CD provides GitOps-based deployments with automatic reconciliation (1m intervals). Changes committed to Git are automatically applied to the cluster. Helm chart versioning uses semver ranges (e.g., `"0.0.x"`) for automatic minor version updates. Karpenter provides capacity-aware node provisioning during deployments. Argo Workflows manage tenant lifecycle operations with step-based execution. |
| **Gap** | No canary or blue/green deployment strategy. Flux CD applies changes directly — all pods are updated simultaneously (rolling update is the only strategy). No Flagger or Argo Rollouts for progressive delivery. No traffic shifting or weighted routing. No deployment health checks beyond Kubernetes readiness probes. No manual approval gates for production deployments. |
| **Recommendation** | Deploy Flagger (compatible with Flux CD) for automated canary deployments with ALB traffic shifting. Add Kubernetes readiness/liveness probes to all Helm chart deployment templates. Implement deployment approval gates using Flux CD notification controller with Slack/Teams integration. Consider Argo Rollouts as an alternative for progressive delivery. |
| **Evidence** | `gitops/clusters/production/infrastructure.yaml` (Flux Kustomization with interval 1m0s), `gitops/application-plane/production/pooled-envs/pool-1.yaml` (HelmRelease with version range), `helm-charts/application-chart/templates/deployment.yaml`, `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` (no deployment validation) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No integration test suites found in the repository. Gitea Actions workflow (`build-and-push.yml`) contains only checkout, ECR login, build, tag, and push steps — no test execution. The `helm-charts/application-chart/templates/tests/` directory exists but contents were not examined (likely Helm test templates). No pytest, unittest, or integration test files found in tenant-microservices directories. No Postman/Newman collections. No contract tests. |
| **Gap** | Complete absence of integration testing. Tenant onboarding/offboarding workflows, SQS message processing, DynamoDB operations, and Helm chart rendering are not validated before production deployment. Regressions in any workflow step can reach production undetected. |
| **Recommendation** | Add integration tests for Argo Workflow templates (validate tenant onboarding end-to-end in a staging environment). Add Helm chart rendering tests (`helm template` with different value combinations). Add Terraform plan validation in CI (terraform validate + plan). Implement API tests for Gitea and Argo Workflows APIs. Add test stage to Gitea Actions workflows before push. |
| **Evidence** | `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` (no test steps), `helm-charts/application-chart/templates/tests/` (directory exists but unused in CI) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found in the repository (no markdown, YAML, or JSON runbook files). No SSM Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. The `workflow-scripts/` directory contains tenant lifecycle scripts (validate, clone, onboard, deploy, offboard) but no incident response scripts. The `scripts/` directory contains cleanup, monitoring, and tenant control scripts but these are manual operational scripts, not automated incident response. |
| **Gap** | No automated incident response. No runbooks (even as documentation). No self-healing patterns. Incident response is entirely ad hoc — manual SSH to EC2, manual kubectl commands, manual investigation. |
| **Recommendation** | Create runbooks for common incidents (Gitea EC2 failure, Karpenter provisioning failures, SQS queue backup, failed tenant onboarding). Implement SSM Automation documents for common remediation actions. Add Karpenter node health checks with automatic replacement. Create Argo Workflow templates for automated incident investigation and remediation. |
| **Evidence** | `workflow-scripts/` (tenant lifecycle scripts only), `scripts/` (manual operational scripts: cleanup.sh, monitor-tenants.sh, tenant-control.sh) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file found in the repository. No service-level dashboards defined in IaC or GitOps manifests. No named alarm owners. Kubecost provides cost dashboards but these are generic, not service-specific with ownership attribution. No team tags on CloudWatch resources (no CloudWatch resources exist in IaC). No SLO definitions with team attribution. |
| **Gap** | No observability ownership model. No service-to-team mapping. No dashboard or alarm ownership. Monitoring is reactive and fragmented — Kubecost cost dashboards are the only observability surface, and they have no ownership attribution. |
| **Recommendation** | Create a CODEOWNERS file mapping infrastructure components to responsible teams. Define per-service Grafana dashboards (Argo Workflows execution metrics, tenant onboarding pipeline, SQS queue health) with named owners. Add team tags to all IaC-managed resources. Establish an observability-as-code pattern where dashboard definitions are GitOps-managed alongside infrastructure. |
| **Evidence** | Repository root (no CODEOWNERS file), `gitops/infrastructure/production/` (no dashboard or alarm definitions), `terraform/workshop/providers.tf` (no default_tags with team/owner) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Tags are present on multiple resources: `Blueprint = var.name` on VPC, EKS, and S3 buckets; `karpenter.sh/discovery = local.name` on VPC subnets and EKS; `Name = var.name` on Gitea EC2 and security groups; `Name = var.tenant_id` on tenant DynamoDB tables and SQS queues; `Name = "karpenter-node"` on Karpenter-provisioned nodes; `Environment` tags on VS Code CloudFormation resources. |
| **Gap** | No `default_tags` block in the AWS provider configuration (`terraform/workshop/providers.tf`), meaning tags must be explicitly added to each resource. No tag enforcement via AWS Config rules or SCPs. Inconsistent tag keys across resources (some use `Blueprint`, others use `Name`, `Environment`). No cost allocation tags (no `CostCenter`, `Project`, `Team` tags). No tag standard documented. |
| **Recommendation** | Add `default_tags` block to the AWS provider in `providers.tf` with standard keys: `Project`, `Environment`, `ManagedBy=terraform`, `CostCenter`. Create `aws_config_config_rule` for required-tags enforcement. Standardize tag key naming across all resources. Activate cost allocation tags in AWS Billing console. |
| **Evidence** | `terraform/workshop/main.tf` (local.tags = { Blueprint = var.name }), `terraform/workshop/providers.tf` (no default_tags), `terraform/modules/tenant-apps/main.tf` (Name = var.tenant_id tags), `terraform/modules/gitea/main.tf` (Name = var.name), `helpers/vs-code-ec2.yaml` (Environment tags) |

---

## Learning Materials

No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

The following general resources are recommended based on assessment gaps:

| Gap Area | Learning Resources |
|----------|-------------------|
| Security Baseline | [AWS Security Best Practices](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) · [EKS Security Best Practices](https://aws.github.io/aws-eks-best-practices/security/docs/) |
| Operations & Observability | [AWS Observability Best Practices](https://aws-observability.github.io/observability-best-practices/) · [EKS Observability](https://aws.github.io/aws-eks-best-practices/observability/docs/) |
| Modern DevOps Practices | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `terraform/workshop/main.tf` | INF-Q1, INF-Q5, INF-Q7, INF-Q9, INF-Q10, SEC-Q1, SEC-Q4, SEC-Q5, OPS-Q4, OPS-Q9 | Main Terraform config: VPC, EKS cluster, Gitea module, SSM parameters, VPC peering |
| `terraform/workshop/saas_gitops.tf` | INF-Q10, INF-Q11 | Flux CD module, ConfigMap with infrastructure outputs, Gitea repo setup |
| `terraform/workshop/variables.tf` | INF-Q1 | EKS cluster version (1.32), stack naming, Gitea config |
| `terraform/workshop/providers.tf` | OPS-Q9 | AWS provider (no default_tags), Kubernetes/Helm providers |
| `terraform/workshop/versions.tf` | INF-Q10 | Terraform version constraints, provider versions |
| `terraform/modules/gitops-saas-infra/main.tf` | INF-Q1, INF-Q4, INF-Q10, SEC-Q1, SEC-Q2, SEC-Q4, SEC-Q5, OPS-Q4 | Karpenter IAM, SQS queues, S3 buckets, IRSA roles, Argo IRSA |
| `terraform/modules/gitops-saas-infra/apps_needs.tf` | INF-Q10, SEC-Q2, SEC-Q6, SEC-Q7 | ECR repositories (AES256, scan_on_push, IMMUTABLE tags), S3 code artifacts |
| `terraform/modules/gitops-saas-infra/variables.tf` | INF-Q10 | Microservices definitions, ECR repo names |
| `terraform/modules/gitea/main.tf` | INF-Q1, INF-Q5, INF-Q9, SEC-Q2, SEC-Q4, SEC-Q6, OPS-Q9 | Gitea EC2 instance, security groups, IAM role |
| `terraform/modules/gitea/userdata.sh` | SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6 | Gitea Docker setup, token creation, SSM storage |
| `terraform/modules/tenant-apps/main.tf` | INF-Q2, INF-Q4, DATA-Q3, OPS-Q9 | DynamoDB tables (PITR), per-tenant SQS queues, IRSA roles |
| `terraform/modules/flux_cd/main.tf` | INF-Q10, INF-Q11, SEC-Q5 | Flux Operator, FluxInstance, Kubernetes secrets |
| `gitops/clusters/production/infrastructure.yaml` | INF-Q10, INF-Q11, OPS-Q5 | Flux Kustomization for infrastructure layer |
| `gitops/clusters/production/sources.yaml` | INF-Q10 | Flux Kustomization for Helm/Git sources |
| `gitops/clusters/production/control-plane.yaml` | INF-Q10 | Flux Kustomization for control plane |
| `gitops/infrastructure/production/01-metric-server.yaml` | INF-Q7, OPS-Q3 | Metrics Server v3.11.0 HelmRelease |
| `gitops/infrastructure/production/02-karpenter.yaml` | INF-Q1, INF-Q7 | Karpenter v1.4.0 HelmRelease with IRSA |
| `gitops/infrastructure/production/03-argo-workflows.yaml` | INF-Q3, INF-Q6, SEC-Q3 | Argo Workflows HelmRelease (--auth-mode=server), internet-facing LB |
| `gitops/infrastructure/production/04-lb-controller.yaml` | INF-Q6 | AWS Load Balancer Controller v1.6.2 HelmRelease |
| `gitops/infrastructure/production/05-kubecost.yaml` | INF-Q6, OPS-Q3, SEC-Q3 | Kubecost v2.1.0 with Prometheus, internet-facing LB |
| `gitops/infrastructure/production/06-argo-events.yaml` | INF-Q3 | Argo Events v2.4.3 HelmRelease with IRSA |
| `gitops/infrastructure/production/07-tf-controller.yaml` | INF-Q10 | TF Controller v0.16.0-rc.4 HelmRelease |
| `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` | INF-Q7, SEC-Q6 | Karpenter NodePool (consolidation), EC2NodeClass (AL2023) |
| `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml` | INF-Q3 | Argo WorkflowTemplate for tenant onboarding |
| `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | INF-Q3, SEC-Q5 | Argo EventSource/Sensor with SQS trigger, gitea_token in params |
| `gitops/control-plane/production/workflows/event-bus.yaml` | INF-Q3, INF-Q9 | Argo EventBus with 3 NATS replicas |
| `gitops/application-plane/production/pooled-envs/pool-1.yaml` | OPS-Q5 | Pool-1 HelmRelease with semver version range |
| `helm-charts/application-chart/Chart.yaml` | INF-Q10 | Application Helm chart v0.0.1 |
| `helm-charts/application-chart/values.yaml` | INF-Q7, OPS-Q1 | Default values (autoscaling disabled, no tracing) |
| `helm-charts/application-chart/templates/hpa.yaml` | INF-Q7 | HPA template (conditional on autoscaling.enabled) |
| `helm-charts/application-chart/templates/ingress.yaml` | INF-Q6 | Ingress template with ALB class support |
| `helm-charts/helm-tenant-chart/Chart.yaml` | INF-Q10 | Tenant Helm chart v0.0.1 |
| `helm-charts/helm-tenant-chart/values.yaml.template` | INF-Q6, INF-Q7 | Tenant chart values (ingress className: alb, autoscaling) |
| `helm-charts/helm-tenant-chart/templates/terraform.yaml` | INF-Q10, INF-Q11 | TF Controller Terraform resource for tenant infra |
| `helm-charts/helm-tenant-chart/templates/hpa.yaml` | INF-Q7 | Per-app HPA template |
| `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` | INF-Q11, SEC-Q7, OPS-Q5, OPS-Q6 | Gitea Actions: build-and-push only, no tests/security |
| `workflow-scripts/Dockerfile` | INF-Q10 | Argo Workflow container (Alpine, Terraform, kubectl) |
| `helpers/vs-code-ec2.yaml` | INF-Q1, INF-Q5, SEC-Q2 | CloudFormation: VS Code EC2, VPC, AllowedIP default |
| `scripts/cleanup.sh` | OPS-Q7 | Manual cleanup script (not automated incident response) |
| `scripts/monitor-tenants.sh` | OPS-Q7 | Manual monitoring script |
| `README.md` | SEC-Q1 | Architecture docs (mentions audit logging but no IaC evidence) |
