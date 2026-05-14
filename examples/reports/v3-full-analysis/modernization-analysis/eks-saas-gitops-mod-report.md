# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | eks-saas-gitops |
| **Date** | 2025-07-15 |
| **Repo Type** | `infrastructure-only` |
| **Priority** | P1 |
| **Tags** | eks, gitops, terraform, saas, infrastructure |
| **Context** | EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings, everything that is not serverless will run here, EKS will be the centralized platform |
| **Overall Score** | **2.19 / 4.0** |

> Service archetype detection skipped — not applicable for `infrastructure-only` repo type.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.82 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | N/A | N/A — all questions not applicable for `infrastructure-only` |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.71 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **2.19 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail configuration in IaC — no audit trail for API activity | Compliance risk; inability to investigate security incidents or unauthorized access |
| 2 | SEC-Q3: API Authentication | 1 | Argo Workflows and Kubecost exposed internet-facing with no authentication | Critical security exposure; unauthenticated access to workflow orchestration and cost data |
| 3 | OPS-Q1: Distributed Tracing | 1 | No X-Ray, OpenTelemetry, or any tracing instrumentation | Cannot debug cross-service request flows or identify latency bottlenecks across tenant workloads |
| 4 | OPS-Q4: Anomaly Detection and Alerting | 1 | No CloudWatch alarms, anomaly detection, or alerting integration | No proactive incident detection; all failures discovered reactively |
| 5 | OPS-Q7: Incident Response Automation | 1 | No runbooks, SSM Automation, or self-healing patterns | Incident response is entirely ad hoc; no repeatable recovery procedures |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (CI/CD pipeline exists with Gitea Actions + Flux CD GitOps delivery)
- **What it enables:** An agent that triggers tenant deployments via SQS → Argo Workflows, checks build status in Gitea, monitors Flux CD reconciliation state, and manages tenant lifecycle operations (onboarding, offboarding, deployment) through natural language commands.
- **Additional steps:** Expose Argo Workflows API with proper authentication (currently `--auth-mode=server`). Generate OpenAPI spec for the SQS-triggered workflow interface. Configure Amazon Bedrock with tool definitions for Argo Workflows and Flux CD APIs.
- **Effort:** Medium — Argo Workflows API exists but needs auth; SQS integration is already in place for event-driven triggers.

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — `README.md` (comprehensive), `workflow-scripts/README.md`, `terraform/modules/flux_cd/README.md`, `terraform/modules/tenant-apps/README.md`, Helm chart `NOTES.txt`, and extensive inline comments throughout Terraform and GitOps manifests.
- **What it enables:** A knowledge agent using Amazon Bedrock that indexes all repository documentation, Terraform module docs, workflow scripts, and tier templates. Platform engineers can ask natural language questions about tenant onboarding procedures, Karpenter configuration, tier template differences, or Terraform module parameters.
- **Additional steps:** Index documentation into a vector store (Amazon OpenSearch with vector engine or Amazon Kendra). Chunk large files (README, Terraform modules) appropriately. Configure retrieval chain with Bedrock.
- **Effort:** Medium — documentation corpus exists but needs indexing infrastructure and embedding pipeline.

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 4 (Argo Workflows deployed with tenant onboarding, deployment, and offboarding workflow templates; SQS + Argo Events for event-driven triggers)
- **What it enables:** An agent using Amazon Bedrock that monitors Argo Workflow execution state, identifies failed workflow steps, retries failed tenant operations, and provides status updates on in-progress tenant provisioning. The agent can also validate tenant configurations before triggering workflows.
- **Additional steps:** Argo Workflows server needs authentication configured (currently unauthenticated). Agent needs read access to Argo Workflows API and SQS send permissions for triggering new workflows.
- **Effort:** Medium — workflow infrastructure is mature but API authentication is missing.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 2 | Move to Containers | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 is N/A for infrastructure-only. No commercial database engines detected (DynamoDB is AWS-native, Gitea uses SQLite which is open source). |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 — primary databases (DynamoDB) are fully managed. Gitea SQLite is auxiliary and self-managed but does not meet the threshold for triggering this pathway. |
| 5 | Move to Managed Analytics | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q11 = 2 (CI pipelines lack test stages and security scanning). Supporting: OPS-Q5 = 2 (no canary/blue-green), OPS-Q6 = 1 (no integration tests). |
| 7 | Move to AI | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 3):** Terraform covers VPC, EKS, IAM, ECR, SQS, S3, and SSM parameters comprehensively. Flux CD with Kustomize overlays manages all Kubernetes workloads via GitOps. TF Controller enables Terraform execution from within the cluster. However, operational resources (CloudWatch alarms, CloudTrail, backup plans, Route 53 health checks) are not defined in IaC.
- **CI/CD Automation (INF-Q11 = 2):** Gitea Actions workflows handle Docker image builds and ECR pushes for 3 microservices. Flux CD provides GitOps-based continuous reconciliation from Git to cluster. Argo Workflows automates tenant lifecycle (onboarding, deployment, offboarding). However, CI pipelines have **no test stages** (unit, integration, or E2E), **no security scanning** (SAST, dependency, container), and **no automated rollback**. Initial cluster setup relies on manual `install.sh` script execution.
- **Deployment Strategy (OPS-Q5 = 2):** Kubernetes rolling updates are the default deployment strategy via Helm. No canary, blue/green, or traffic-shifting patterns are configured. No Argo Rollouts or Flagger for progressive delivery.
- **Integration Testing (OPS-Q6 = 1):** No integration test suites exist. The only test artifact is a basic Helm test template (`test-connection.yaml`) that verifies pod connectivity — not a real integration test. CI pipelines skip testing entirely.

#### Recommendations

1. **Enhance CI Pipelines with Test and Security Stages:**
   - Add unit test execution to Gitea Actions workflows before the Docker build step.
   - Integrate `checkov` or `tfsec` scanning for Terraform modules in a dedicated pipeline (checkov is already partially used during development, as indicated by skip comments).
   - Add container image vulnerability scanning beyond ECR scan-on-push — integrate `trivy` or `grype` into the build pipeline with a blocking gate on critical findings.
   - Add `tflint` for Terraform linting and `kubeval`/`kubeconform` for Kubernetes manifest validation.

2. **Implement Progressive Delivery:**
   - Deploy [Flagger](https://flagger.app/) alongside Flux CD for automated canary deployments with metric-based promotion. Flagger integrates natively with Flux CD and supports EKS with ALB traffic shifting.
   - Define canary analysis metrics using Prometheus (already deployed via Kubecost) for error rate and latency thresholds.
   - Configure automated rollback on failed canary analysis.

3. **Add Integration Tests to CI Pipeline:**
   - Create integration test suites for tenant onboarding/offboarding workflows using a test tenant namespace.
   - Add Helm chart validation tests (`helm template` + `kubeconform`) to CI.
   - Implement contract tests for SQS message schemas used by Argo Events sensors.

4. **Expand IaC to Cover Operational Resources:**
   - Define CloudWatch alarms, dashboards, and log groups in Terraform.
   - Add CloudTrail configuration to IaC (addresses SEC-Q1 gap simultaneously).
   - Define AWS Backup plans for critical data stores in Terraform.

#### Representative AWS Services (respecting preferences)

- **CI/CD:** AWS CodeBuild (for hosted build agents as alternative to self-hosted Gitea runner), AWS CodePipeline (if migrating from Gitea Actions), or continue with Gitea Actions + enhanced stages
- **Progressive Delivery:** Flagger on EKS, Argo Rollouts on EKS
- **IaC Governance:** Terraform Cloud/Enterprise, or continue with TF Controller on EKS (already deployed)
- **Security Scanning:** Amazon Inspector, ECR Enhanced Scanning, AWS CodeGuru Reviewer

#### Learning Resources

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary compute runs on EKS with managed node groups (`m5.large`, min=3, max=5) deployed to private subnets across 3 AZs. Karpenter v1.4.0 is deployed via Flux CD HelmRelease for dynamic node provisioning with NodePools supporting `c`, `m`, `r` instance categories and both on-demand and spot capacity types. The Karpenter EC2NodeClass uses `al2023@latest` AMIs with consolidation policy (`WhenEmptyOrUnderutilized`). One auxiliary workload — Gitea — runs on a standalone EC2 instance (`m5.large`) outside EKS. |
| **Gap** | Gitea runs on a standalone EC2 instance rather than as a container on EKS. This is the only non-managed compute workload. |
| **Recommendation** | Migrate Gitea to run as a Helm chart on EKS to eliminate the standalone EC2 instance. Gitea has an official Helm chart that supports SQLite and can run on EKS with persistent volumes. This would consolidate all compute onto managed EKS. |
| **Evidence** | `terraform/workshop/main.tf` (module.eks, eks_managed_node_groups), `gitops/infrastructure/production/02-karpenter.yaml` (HelmRelease v1.4.0), `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (NodePool, EC2NodeClass), `terraform/modules/gitea/main.tf` (aws_instance.gitea) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB tables are defined in IaC (`aws_dynamodb_table.consumer_ddb`) with PAY_PER_REQUEST billing and PITR enabled — fully managed with automatic failover. SQS queues (4 total: 3 for Argo Workflows lifecycle events, 1 for Karpenter interruption) are fully managed with SSE enabled. Gitea uses SQLite embedded in a Docker container running on EC2 — this is a self-managed embedded database for an auxiliary service. |
| **Gap** | Gitea SQLite is self-managed — no automated backup, failover, or lifecycle management. It is auxiliary (Git server for the workshop) but represents a single point of failure for the source-of-truth Git repository. |
| **Recommendation** | For production use, migrate Gitea's database to Amazon Aurora PostgreSQL (preferred per technology preferences) or RDS PostgreSQL. Alternatively, migrate to a managed Git service (AWS CodeCommit, GitHub, GitLab SaaS) to eliminate the self-managed Gitea dependency entirely. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table.consumer_ddb with point_in_time_recovery), `terraform/modules/gitops-saas-infra/main.tf` (aws_sqs_queue resources), `terraform/modules/gitea/userdata.sh` (GITEA__database__DB_TYPE=sqlite3) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Argo Workflows is deployed as a dedicated workflow orchestration service via Flux CD HelmRelease (v0.40.11). Three WorkflowTemplates define multi-step tenant lifecycle processes: onboarding (`tenant-onboarding-workflow-template.yaml`), deployment (`tenant-deployment-workflow-template.yaml`), and offboarding (`tenant-offboarding-workflow-template.yaml`). Each template has properly sequenced steps (clone → validate → execute). SQS queues + Argo Events provide event-driven workflow triggering via Sensors and EventSources. Workflow synchronization uses mutex locks to prevent concurrent conflicting operations. The NATS EventBus provides reliable event delivery with 3 replicas for HA. |
| **Gap** | None — workflow orchestration is mature and well-implemented. |
| **Recommendation** | No action required. The Argo Workflows + Argo Events + SQS architecture is a best-practice implementation for event-driven workflow orchestration on EKS. Consider adding workflow retry policies and error handling templates for improved resilience. |
| **Evidence** | `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`, `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml`, `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml`, `gitops/control-plane/production/workflows/event-bus.yaml` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Managed SQS queues are used for all asynchronous messaging: `argoworkflows-onboarding-queue`, `argoworkflows-offboarding-queue`, `argoworkflows-deployment-queue` (tenant lifecycle events), and an SQS queue for Karpenter interruption handling. All SQS queues have `sqs_managed_sse_enabled = true`. Argo Events with SQS EventSource consumes messages and triggers corresponding Argo Workflows. No self-managed Kafka, RabbitMQ, or other message brokers are present. |
| **Gap** | None — messaging is fully managed via SQS with no self-managed brokers. |
| **Recommendation** | No action required. The SQS + Argo Events architecture is well-suited for the event-driven tenant lifecycle use case. If future workloads require event bus patterns with fan-out, consider Amazon EventBridge (preferred per technology preferences) for richer event routing and filtering. |
| **Evidence** | `terraform/modules/gitops-saas-infra/main.tf` (aws_sqs_queue.argoworkflows_onboarding_queue, aws_sqs_queue.argoworkflows_offboarding_queue, aws_sqs_queue.argoworkflows_deployment_queue, aws_sqs_queue.karpenter_interruption_queue), `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` (EventSource with SQS) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Custom VPC deployed with CIDR `10.35.0.0/16` across 3 AZs with separate public and private subnets. EKS nodes are deployed to private subnets with Karpenter-managed nodes also in private subnets (discovered via `karpenter.sh/discovery` tags). Security groups are configured for Gitea (scoped ingress from VPC CIDR and EKS SG). However: Gitea EC2 is in a **public subnet** with `associate_public_ip_address = true`. Gitea security group has egress `0.0.0.0/0` on all protocols. No VPC endpoints, PrivateLink, or VPC Lattice configured. Argo Workflows and Kubecost services are exposed via internet-facing LoadBalancers. |
| **Gap** | Gitea in public subnet with public IP. Egress `0.0.0.0/0` on Gitea security group. Internet-facing services (Argo Workflows, Kubecost) with no authentication. No VPC endpoints for AWS service access from private subnets. |
| **Recommendation** | Move Gitea to a private subnet (or migrate to EKS). Add VPC endpoints for ECR, SQS, S3, SSM, and STS to reduce NAT Gateway traffic and improve security posture. Restrict Argo Workflows and Kubecost to internal-only ALBs or add authentication. Tighten Gitea egress rules to specific CIDR ranges. |
| **Evidence** | `terraform/workshop/main.tf` (module.vpc with single_nat_gateway=true), `terraform/modules/gitea/main.tf` (aws_instance.gitea with associate_public_ip_address=true, aws_security_group.gitea with egress 0.0.0.0/0), `gitops/infrastructure/production/03-argo-workflows.yaml` (service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing") |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | AWS Load Balancer Controller (v1.6.2) is deployed via Flux CD HelmRelease and manages ALBs for Kubernetes Ingress resources. Tenant services can use ALB Ingress for HTTP routing. Argo Workflows server uses a LoadBalancer service with internet-facing annotation. Kubecost uses a LoadBalancer service with internet-facing annotation. No API Gateway, AppSync, or CloudFront is configured. |
| **Gap** | Load balancers are present but have minimal configuration — no authentication, no throttling, no request validation, no WAF integration. Argo Workflows and Kubecost are directly internet-facing with no protection layer. |
| **Recommendation** | Add Amazon API Gateway (preferred per technology preferences) as the entry point for tenant-facing APIs with throttling, authentication (Cognito or Lambda authorizers), and request validation. For internal services (Argo Workflows, Kubecost), switch to internal-only ALBs and use VPN or SSM Session Manager for access. Consider adding AWS WAF to ALBs for web application protection. |
| **Evidence** | `gitops/infrastructure/production/04-lb-controller.yaml` (HelmRelease aws-load-balancer-controller v1.6.2), `gitops/infrastructure/production/03-argo-workflows.yaml` (internet-facing LoadBalancer), `gitops/infrastructure/production/05-kubecost.yaml` (internet-facing LoadBalancer) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Karpenter provides dynamic node auto-scaling with consolidation policy (`WhenEmptyOrUnderutilized`, consolidateAfter: 1m). NodePool supports `c`, `m`, `r` instance categories with CPU limits of 1000 cores and 2000Gi memory. EKS managed node group has ASG with min=3, max=5. DynamoDB uses PAY_PER_REQUEST billing (implicit auto-scaling). Helm chart includes HPA template but it is **disabled by default** (`autoscaling.enabled: false`). |
| **Gap** | HPA is not enabled for application workloads — pod-level scaling relies on static replica counts. Karpenter handles node-level scaling but individual services cannot scale independently at the pod level. No scheduled scaling for predictable traffic patterns. |
| **Recommendation** | Enable HPA in Helm chart values for tenant workloads with appropriate CPU/memory thresholds. Consider KEDA (Kubernetes Event-Driven Autoscaling) for SQS-based scaling of consumer workloads. Add metrics-server custom metrics for business-metric-based scaling. |
| **Evidence** | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (NodePool with consolidation policy), `terraform/workshop/main.tf` (eks_managed_node_groups min=3, max=5), `helm-charts/application-chart/values.yaml` (autoscaling.enabled: false), `helm-charts/application-chart/templates/hpa.yaml` (HPA template exists) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DynamoDB tables have PITR enabled (`point_in_time_recovery { enabled = true }`). S3 buckets explicitly skip versioning (checkov skip: `CKV2_AWS_21: Versioning is not needed at this time`). EC2 root block devices are encrypted but have no snapshot lifecycle. No `aws_backup_plan` resources defined. No documented restore procedures. Gitea data (SQLite + Git repos) relies on Docker volumes on a single EC2 instance with no backup. |
| **Gap** | S3 versioning disabled. No AWS Backup plan for coordinated backup management. No Gitea data backup strategy. No documented or tested restore procedures. EBS volumes have no snapshot lifecycle policy. |
| **Recommendation** | Enable S3 versioning on the Argo artifacts bucket. Define an AWS Backup plan in Terraform covering DynamoDB, EBS volumes, and any future RDS instances. Implement Gitea backup via `gitea dump` scheduled job or migrate to a managed Git service. Document and test restore procedures for each data store. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (point_in_time_recovery enabled), `terraform/modules/gitops-saas-infra/apps_needs.tf` (checkov:skip=CKV2_AWS_21), `terraform/modules/gitops-saas-infra/main.tf` (S3 bucket without versioning) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | VPC spans 3 AZs with private and public subnets in each. EKS managed node group spans all private subnets (multi-AZ). Karpenter can provision nodes across all AZs via subnet selector tags. NATS EventBus has 3 replicas for HA. DynamoDB is inherently multi-AZ. However: Gitea is a **single EC2 instance** — single point of failure for the Git source-of-truth. NAT Gateway is **single** (`single_nat_gateway = true`) — an AZ failure affecting the NAT Gateway's AZ would disrupt egress for all private subnets. |
| **Gap** | Single NAT Gateway creates AZ-level failure risk for egress traffic. Gitea single instance is a SPOF for the entire GitOps pipeline (Flux CD sources from Gitea). |
| **Recommendation** | Enable multi-AZ NAT Gateways by setting `single_nat_gateway = false` and `one_nat_gateway_per_az = true` in the VPC module. Migrate Gitea to EKS with multiple replicas, or replace with a managed Git service. Consider Gitea's HA mode with PostgreSQL backend for a self-hosted HA solution. |
| **Evidence** | `terraform/workshop/main.tf` (module.vpc with azs = 3, single_nat_gateway = true), `terraform/modules/gitea/main.tf` (single aws_instance.gitea), `gitops/control-plane/production/workflows/event-bus.yaml` (nats replicas: 3) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive Terraform coverage for primary infrastructure: VPC, EKS cluster, managed node groups, IAM roles (IRSA for Karpenter, Argo Workflows, Argo Events, LB Controller, TF Controller, image automation), ECR repositories, SQS queues, S3 buckets, SSM parameters, EC2 instance (Gitea), security groups, VPC peering. Flux CD manages all Kubernetes resources via GitOps with HelmReleases and Kustomizations. TF Controller enables Terraform execution from within the cluster for tenant resource provisioning. |
| **Gap** | Missing from IaC: CloudWatch alarms and dashboards, CloudTrail configuration, AWS Backup plans, Route 53 health checks, and any monitoring/observability infrastructure. These operational and DR resources are not defined anywhere in the repository. |
| **Recommendation** | Extend Terraform modules to cover operational resources: CloudTrail (SEC-Q1), CloudWatch alarms and dashboards (OPS-Q4, OPS-Q8), AWS Backup plans (INF-Q8), and Route 53 health checks. Use Terraform modules or the Kubernetes CloudWatch agent Helm chart for monitoring. Consider defining a shared `monitoring` module that provisions all observability infrastructure. |
| **Evidence** | `terraform/workshop/main.tf`, `terraform/workshop/saas_gitops.tf`, `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/gitops-saas-infra/apps_needs.tf`, `terraform/modules/gitea/main.tf`, `terraform/modules/tenant-apps/main.tf`, `terraform/modules/flux_cd/main.tf`, `gitops/clusters/production/*.yaml`, `gitops/infrastructure/production/*.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Gitea Actions workflows exist for 3 microservices (consumer, producer, payments) — each builds a Docker image and pushes to ECR with timestamp-based tags. Flux CD provides GitOps-based continuous delivery with automatic reconciliation from Git to cluster. Argo Workflows automates tenant lifecycle operations (onboarding, deployment, offboarding) triggered by SQS messages via Argo Events. TF Controller enables Terraform plan/apply from within the cluster. |
| **Gap** | CI pipelines have **no test stages** — workflows go directly from checkout to Docker build with no unit tests, integration tests, linting, or validation. **No security scanning** in pipelines — no SAST, dependency scanning, or container scanning (only ECR scan-on-push which is post-push). **No automated rollback** configuration. Initial cluster setup relies on manual execution of `install.sh`. No pipeline for Terraform module validation or Helm chart linting. |
| **Recommendation** | Add test and security stages to Gitea Actions workflows: (1) linting/validation, (2) unit tests, (3) security scanning (checkov for Terraform, trivy for containers), (4) build, (5) push. Add a Terraform CI pipeline that runs `terraform validate`, `terraform plan`, `tflint`, and `checkov` on pull requests. Add Helm chart validation (`helm template | kubeconform`). Consider migrating initial setup from `install.sh` to a CI/CD pipeline for reproducibility. |
| **Evidence** | `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml`, `tenant-microservices/producer/.gitea/workflows/build-and-push.yml`, `tenant-microservices/payments/.gitea/workflows/build-and-push.yml`, `terraform/install.sh`, `gitops/clusters/production/infrastructure.yaml` (Flux Kustomization) |

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
| **Score** | 3 |
| **Finding** | DynamoDB is the primary database — it is a fully managed serverless service with no engine version to pin (AWS manages all versioning and upgrades transparently). No RDS, Aurora, or other versioned database engines are defined in IaC. Gitea uses SQLite embedded in the `gitea/gitea:latest` Docker image — the `:latest` tag is unpinned and could introduce breaking changes on container restart. No documented version-update procedure exists. |
| **Gap** | Gitea Docker image uses the unpinned `:latest` tag rather than a specific version (e.g., `gitea/gitea:1.21.0`). This creates a risk of unexpected version changes when the container is recreated. While Gitea is auxiliary, it is the source-of-truth for the GitOps pipeline. |
| **Recommendation** | Pin the Gitea Docker image to a specific version in `userdata.sh` (e.g., `gitea/gitea:1.22.0`). Document a version-update procedure for Gitea that includes testing the new version before production deployment. For DynamoDB, no version pinning is needed — the service is fully managed. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table — no engine version field, fully managed), `terraform/modules/gitea/userdata.sh` (image: gitea/gitea:latest — unpinned) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `infrastructure-only` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No `aws_cloudtrail` resource found in any Terraform file across the entire repository. No CloudTrail configuration in any IaC file, Helm chart, or Kubernetes manifest. No equivalent audit logging mechanism (e.g., Kubernetes audit logs forwarded to CloudWatch) is configured. |
| **Gap** | Complete absence of audit logging. No trail of API calls, no log file validation, no immutable log storage. This is a critical compliance and security gap — there is no forensic capability if a security incident occurs. |
| **Recommendation** | Add a `aws_cloudtrail` resource in Terraform with: (1) multi-region trail for complete API coverage, (2) log file validation enabled, (3) S3 bucket with Object Lock for immutable storage, (4) CloudWatch Logs integration for real-time alerting. Also enable EKS control plane logging (audit, authenticator, controllerManager) and forward to CloudWatch Logs. |
| **Evidence** | Searched all `.tf` files — no `aws_cloudtrail` resource. No `cloud_watch_logs_group_arn` or `enable_log_file_validation` anywhere in the codebase. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS-managed encryption is enabled across most data stores: ECR repositories use AES256 encryption (`encryption_type = "AES256"`). SQS queues use `sqs_managed_sse_enabled = true`. EC2 root block devices have `encrypted = true` (default AWS-managed keys). DynamoDB uses default AWS-owned encryption (no explicit `server_side_encryption` block but AWS encrypts DynamoDB at rest by default). S3 buckets explicitly skip KMS encryption with checkov skip comments (`CKV2_AWS_145: This S3 bucket does not required a KMS Encryption`). No `aws_kms_key` resources are defined anywhere in the repository. |
| **Gap** | No customer-managed KMS keys — all encryption uses AWS-managed or AWS-owned keys. This limits key rotation control, cross-account access management, and audit trail granularity. S3 bucket encryption relies on default S3 encryption (AES-256) rather than explicit KMS. |
| **Recommendation** | For production workloads, create customer-managed KMS keys for sensitive data stores (DynamoDB tables, S3 buckets with tenant data, SQS queues carrying tenant messages). Define a key rotation policy. For ECR, consider upgrading to KMS encryption for container images. Use a centralized KMS key module in Terraform for consistent key management. |
| **Evidence** | `terraform/modules/gitops-saas-infra/apps_needs.tf` (ECR encryption_type: AES256, S3 checkov skip), `terraform/modules/gitops-saas-infra/main.tf` (SQS sqs_managed_sse_enabled), `terraform/modules/gitea/main.tf` (EC2 root_block_device encrypted=true), `terraform/modules/tenant-apps/main.tf` (DynamoDB — no explicit encryption config, checkov skip CKV2_AWS_119) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Argo Workflows server uses `--auth-mode=server` which means **no authentication** — anyone with network access can view and trigger workflows. The source code explicitly notes this is "for demonstration purposes only." Kubecost is exposed via an internet-facing LoadBalancer on port 9090 with no authentication. Gitea uses basic username/password auth with the admin password stored in SSM Parameter Store. No API Gateway authorizers, OAuth2/JWT, Cognito, or external IdP integration for any exposed service. |
| **Gap** | Critical: Two internet-facing services (Argo Workflows, Kubecost) have **no authentication at all**. This allows unauthenticated access to workflow orchestration (can trigger tenant operations) and cost data. No token-based authentication (OAuth2/JWT) on any endpoint. |
| **Recommendation** | **Immediate:** Switch Argo Workflows to `--auth-mode=sso` with OIDC integration (Cognito or corporate IdP). Move Kubecost behind an internal-only ALB or add authentication via ingress annotations. **Near-term:** Deploy Amazon API Gateway (preferred) as the centralized entry point with Cognito user pools or Lambda authorizers. Implement per-request JWT validation for all tenant-facing APIs. |
| **Evidence** | `gitops/infrastructure/production/03-argo-workflows.yaml` (`--auth-mode=server`), `gitops/infrastructure/production/05-kubecost.yaml` (LoadBalancer type with internet-facing annotation, no auth), `terraform/modules/gitea/userdata.sh` (basic auth) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | IRSA (IAM Roles for Service Accounts) is used extensively for EKS workload identity — Karpenter, Argo Workflows, Argo Events, LB Controller, TF Controller, and image automation all use IRSA for AWS API authentication. This is AWS-native identity federation for service-to-service auth. However, no centralized IdP (Cognito, Okta, Ping) is configured for **user** authentication. Gitea manages its own admin credentials independently. Argo Workflows has no user auth. |
| **Gap** | IRSA provides good workload identity but no centralized user identity provider exists. Each service manages user auth independently or has none. No SSO, no federated identity. |
| **Recommendation** | Deploy Amazon Cognito as the centralized user identity provider. Integrate with Argo Workflows via OIDC SSO (`--auth-mode=sso`). Configure Gitea to use OIDC authentication via Cognito. For future tenant-facing APIs, use Cognito user pools with API Gateway authorizers. |
| **Evidence** | `terraform/modules/gitops-saas-infra/main.tf` (IRSA roles for karpenter, argo-workflows, argo-events, lb-controller, tf-controller), `terraform/workshop/main.tf` (IRSA for ebs-csi, image-automation), `terraform/modules/gitea/userdata.sh` (independent admin auth) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SSM Parameter Store SecureString is used for Gitea admin password (`/eks-saas-gitops/gitea-admin-password`) and Gitea tokens (`/eks-saas-gitops/gitea-flux-token`, `/eks-saas-gitops/gitea-cicd-token`). Flux system credentials are stored as a Kubernetes Secret (username/password). However: the `gitea_token` is exposed in clear text in the `saas-infra-outputs` ConfigMap (`kubernetes_config_map.saas_infra_outputs`), accessible to any pod in the `flux-system` namespace. Some SSM parameters skip advanced encryption validation (checkov skip CKV_AWS_337). No AWS Secrets Manager is used. No secret rotation configured anywhere. |
| **Gap** | Gitea token exposed in ConfigMap clear text — not a Kubernetes Secret. No Secrets Manager with rotation. SSM Parameter Store lacks advanced encryption for some parameters. Flux CD credentials in a Kubernetes Secret without external secrets management. |
| **Recommendation** | Move the gitea_token from ConfigMap to a Kubernetes Secret or use the External Secrets Operator with AWS Secrets Manager. Migrate primary credentials from SSM Parameter Store to AWS Secrets Manager with automated rotation enabled. Use sealed-secrets or external-secrets-operator for Kubernetes secret management integrated with AWS Secrets Manager. |
| **Evidence** | `terraform/workshop/main.tf` (aws_ssm_parameter.gitea_password SecureString), `terraform/workshop/saas_gitops.tf` (kubernetes_config_map.saas_infra_outputs with gitea_token in plain data), `terraform/modules/flux_cd/main.tf` (kubernetes_secret.flux_system), `terraform/modules/gitea/userdata.sh` (SSM put-parameter for tokens) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Several hardening measures are present: IMDSv2 required on Gitea instance (`http_tokens = "required"`), ECR scan-on-push enabled for container vulnerability scanning, AmazonSSMManagedInstanceCore policy attached to Karpenter node role (enables SSM access). EKS managed nodes use EKS-optimized AMIs (auto-patched by AWS). Karpenter uses `al2023@latest` (latest Amazon Linux 2023 AMIs). However: Gitea EC2 uses Amazon Linux 2 AMI (approaching EOL). No SSM Patch Manager baseline configured. No AWS Inspector enabled. No hardened AMI references (CIS, Bottlerocket). SSM policy on Gitea role is commented out (`# resource "aws_iam_role_policy_attachment" "ssm_instance_connect"`). |
| **Gap** | No SSM Patch Manager for automated patching. No AWS Inspector for vulnerability analysis. Gitea uses Amazon Linux 2 (approaching EOL). SSM access commented out for Gitea. No hardened base images (e.g., Bottlerocket for EKS nodes). |
| **Recommendation** | Enable SSM Patch Manager with baselines for all EC2 instances. Enable AWS Inspector for continuous vulnerability analysis across EC2 and ECR. Migrate Gitea from Amazon Linux 2 to Amazon Linux 2023 (or migrate Gitea to EKS). Consider Bottlerocket for Karpenter-managed nodes (add `amiFamily: Bottlerocket` to EC2NodeClass). Uncomment and configure SSM access for the Gitea instance. |
| **Evidence** | `terraform/modules/gitea/main.tf` (metadata_options http_tokens=required, AMI amzn2-ami-hvm, commented out SSM policy), `terraform/modules/gitops-saas-infra/main.tf` (AmazonSSMManagedInstanceCore on Karpenter role), `terraform/modules/gitops-saas-infra/apps_needs.tf` (ECR scan_on_push=true), `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (al2023@latest) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency scanning tools are integrated into the CI/CD pipeline. Gitea Actions workflows (`build-and-push.yml`) only perform Docker build and push — no security scanning steps. ECR scan-on-push is enabled (basic image scanning after push) but this is reactive, not preventive. Checkov skip comments throughout the Terraform code indicate checkov is used during development but is not integrated into the pipeline. No `.snyk` policy, no Dependabot configuration, no SonarQube, no `npm audit` or `pip-audit`. |
| **Gap** | Complete absence of security scanning in the CI/CD pipeline. No pre-push container scanning, no SAST, no dependency vulnerability scanning. Vulnerabilities in container images or Terraform configurations can reach production undetected. |
| **Recommendation** | Add security scanning stages to Gitea Actions workflows: (1) `checkov` for Terraform/Kubernetes manifest scanning (already partially used), (2) `trivy` or `grype` for container image scanning before ECR push with blocking gate on critical findings, (3) `tfsec` or `checkov` as a required pipeline step for IaC changes, (4) Enable ECR Enhanced Scanning (using Amazon Inspector) for continuous image vulnerability analysis. |
| **Evidence** | `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml` (no security scanning steps), `terraform/modules/gitops-saas-infra/apps_needs.tf` (ECR scan_on_push=true, checkov skip comments), `terraform/modules/tenant-apps/main.tf` (checkov skip comments) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found anywhere in the repository. No X-Ray daemon or agent configuration. No OpenTelemetry SDK imports or collector configuration. No `traceparent` or `X-Amzn-Trace-Id` header propagation. Metrics-server is deployed (HelmRelease `01-metric-server.yaml`) but provides resource utilization metrics (CPU, memory), not distributed tracing. |
| **Gap** | Complete absence of distributed tracing. Cannot trace requests across tenant workloads, Argo Workflows, or the control plane. Cross-service debugging is impossible without tracing, which is critical for a multi-tenant SaaS platform where tenant isolation issues need rapid diagnosis. |
| **Recommendation** | Deploy the AWS Distro for OpenTelemetry (ADOT) Collector as a DaemonSet on EKS via a Flux CD HelmRelease. Instrument tenant microservices with OpenTelemetry SDKs. Configure X-Ray as the tracing backend. Add trace ID propagation headers to all inter-service communication. For Argo Workflows, explore OpenTelemetry instrumentation for workflow step tracing. |
| **Evidence** | No tracing-related configuration found in any file. `gitops/infrastructure/production/01-metric-server.yaml` (metrics-server only, not tracing). |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in any configuration file, Helm values, or Terraform resource. No CloudWatch alarms on latency (p99, p95) or availability. No error budget tracking. Kubecost tracks cost metrics but not service-level objectives. No SLO definition files or dashboards. |
| **Gap** | No formal definition of acceptable service levels for the EKS platform or tenant workloads. Without SLOs, there is no objective measure of platform reliability, no basis for prioritizing operational improvements, and no error budget to balance velocity against stability. |
| **Recommendation** | Define SLOs for the EKS platform (cluster API server availability, node provisioning latency via Karpenter, Flux CD reconciliation success rate) and for tenant workloads (tenant onboarding latency, deployment success rate). Implement SLO monitoring using Prometheus with Kubecost's existing Prometheus deployment, or deploy the CloudWatch agent with Prometheus metric scraping. |
| **Evidence** | No SLO-related files or configurations found in any directory. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubecost (v2.1.0) is deployed with cost-analyzer providing per-namespace, per-workload cost attribution — this is a business-relevant metric for a multi-tenant SaaS platform. Prometheus is deployed alongside Kubecost for metric collection with network cost tracking enabled. However, no custom CloudWatch metrics are published for tenant-level business outcomes (e.g., tenant onboarding success rate, deployment duration, tenant resource utilization ratios). Infrastructure metrics only — no business KPIs. |
| **Gap** | No tenant-level business metrics. Kubecost provides cost visibility but no metrics for tenant onboarding time, deployment success rate, resource efficiency per tier (basic vs premium), or workflow completion rates. |
| **Recommendation** | Publish custom CloudWatch metrics for key SaaS business outcomes: tenant onboarding duration, deployment success/failure rate per tenant tier, Argo Workflow completion times, and tenant resource cost per tier. Leverage Kubecost's existing Prometheus for infrastructure metrics and add custom Prometheus metrics for business outcomes. Create CloudWatch dashboards for platform operators. |
| **Evidence** | `gitops/infrastructure/production/05-kubecost.yaml` (Kubecost with Prometheus, networkCosts enabled, etlStoreDurationDays: 120) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configuration found anywhere in the repository. No `aws_cloudwatch_metric_alarm` resources in Terraform. No CloudWatch anomaly detection. No PagerDuty, OpsGenie, or SNS alerting integration. No Prometheus AlertManager configuration in any Helm values. No composite alarms. Kubecost has alerting capabilities but none are configured in the values file. |
| **Gap** | Complete absence of alerting. No proactive notification for cluster health issues, node provisioning failures, workflow failures, or resource exhaustion. All failures are discovered reactively through manual observation. |
| **Recommendation** | Define CloudWatch alarms for critical platform metrics: EKS API server errors, Karpenter provisioning failures, node count anomalies, NAT Gateway errors, SQS dead-letter queue depth. Configure Prometheus AlertManager via the Kubecost Prometheus instance for Kubernetes-native alerts (pod crash loops, OOM kills, PVC capacity). Integrate with Amazon SNS for notification routing to email, Slack, or PagerDuty. |
| **Evidence** | No `aws_cloudwatch_metric_alarm` in any `.tf` file. No AlertManager configuration in `gitops/infrastructure/production/05-kubecost.yaml`. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Flux CD provides GitOps-based continuous delivery with automatic reconciliation from Git repository state to cluster state. Helm charts use standard Kubernetes rolling update strategy (default `maxSurge` and `maxUnavailable`). Argo Workflows manages tenant lifecycle operations with sequenced steps. However, no canary deployments, blue/green deployments, or traffic shifting are configured. No Argo Rollouts, Flagger, or feature flag system. No CodeDeploy integration. |
| **Gap** | No staged rollout strategy. All deployments go directly to production via Flux CD reconciliation with rolling updates. No canary analysis, no traffic shifting, no automated rollback based on metrics. A bad deployment affects all tenants simultaneously. |
| **Recommendation** | Deploy Flagger alongside Flux CD for automated canary deployments. Flagger integrates natively with Flux CD and supports EKS with ALB Ingress traffic shifting. Configure canary analysis using Prometheus metrics (already deployed). For tenant tier deployments, implement progressive delivery per-tier (deploy to basic tier first, then premium) using Flux CD's dependency ordering. |
| **Evidence** | `gitops/clusters/production/infrastructure.yaml` (Flux Kustomization with dependsOn), `helm-charts/application-chart/templates/deployment.yaml` (standard Deployment, no rollout strategy), `helm-charts/application-chart/values.yaml` (no canary/rollout configuration) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No integration test suites found in the repository. Gitea Actions workflows only build and push Docker images — no test step of any kind. A basic Helm test template exists (`application-chart/templates/tests/test-connection.yaml`) that runs a `wget` to verify pod connectivity — this is a Helm smoke test, not an integration test. No contract tests for SQS message schemas. No end-to-end tests for tenant onboarding workflows. No API test suites (Postman, Newman). |
| **Gap** | Complete absence of integration testing. No validation that tenant onboarding workflows complete successfully, no contract tests for SQS message schemas, no end-to-end tests for the Flux CD → Argo Workflows → Terraform pipeline. Regressions can reach production undetected. |
| **Recommendation** | Create integration test suites: (1) Tenant lifecycle tests — test onboarding/deployment/offboarding workflows end-to-end using a test tenant namespace, (2) SQS message contract tests — validate message schemas for Argo Events sensors, (3) Helm chart validation tests — `helm template | kubeconform` in CI, (4) Terraform validation — `terraform validate` + `terraform plan` on module changes. Add test stages to Gitea Actions workflows. |
| **Evidence** | `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml` (no test step), `helm-charts/application-chart/templates/tests/test-connection.yaml` (basic wget test only) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found in any format (markdown, YAML, JSON). No Systems Manager Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns. Argo Workflows handles tenant lifecycle but not incident response. No `runbook/` directory, no `incident-response/` directory. |
| **Gap** | Incident response is entirely ad hoc. No documented recovery procedures, no automated remediation, no self-healing. When tenant onboarding fails or a node becomes unhealthy, resolution depends entirely on manual investigation and intervention. |
| **Recommendation** | Create runbooks for common incidents: (1) Failed tenant onboarding workflow — diagnose and retry, (2) Karpenter node provisioning failure — check capacity, instance types, (3) Flux CD reconciliation failure — identify drift, manual sync, (4) NAT Gateway failure — impact analysis and failover. Implement SSM Automation documents for automated remediation of common issues. Consider defining incident response WorkflowTemplates in Argo Workflows for platform-level incidents. |
| **Evidence** | No runbook or incident response files found in any directory. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file in the repository. No per-service dashboards defined in IaC or Kubernetes manifests. No named alarm owners. No SLO definitions with team attribution. Kubecost provides cost visibility but has no ownership model configured. No observability-related Terraform modules or Helm charts beyond metrics-server and Kubecost. |
| **Gap** | No observability ownership structure. No one is formally responsible for monitoring, alerting, or SLO tracking. Observability gaps (tracing, alerting, SLOs) remain unaddressed because there is no ownership to drive improvement. |
| **Recommendation** | Create a `CODEOWNERS` file assigning observability config ownership to the platform team. Define per-component dashboards in Grafana (can use Kubecost's Prometheus as data source) or CloudWatch. Assign alarm ownership tags to all future CloudWatch alarms. Establish an observability charter defining who owns what metrics, dashboards, and alerting for the platform and tenant workloads. |
| **Evidence** | No `CODEOWNERS` file. No dashboard definitions. No alarm ownership configuration. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Minimal tagging present: a `Blueprint` tag in `local.tags` (`terraform/workshop/main.tf`) applied to VPC and EKS. `Name` tags on individual resources (Gitea EC2, Karpenter nodes, DynamoDB tables, SQS queues). Tenant ID used as `Name` tag on DynamoDB and SQS resources. No `default_tags` block in the AWS provider configuration. No required-tags AWS Config rules. No Tag Policies via AWS Organizations. No cost allocation tags. No environment, team, or service tags. |
| **Gap** | No tagging governance. Tags are ad hoc and inconsistent — some resources have `Blueprint` and `Name`, others only `Name`, and many have no cost-relevant tags. No `default_tags` in provider ensures that new resources are created without mandatory tags. Cannot perform cost attribution per tenant tier, per service, or per environment. |
| **Recommendation** | Add `default_tags` to the AWS provider in `providers.tf` with mandatory tags: `Environment`, `Project`, `Team`, `ManagedBy=terraform`. Add tenant-level tags to all tenant-provisioned resources (DynamoDB, SQS, IAM roles) including `TenantId`, `TenantTier`, and `CostCenter`. Deploy AWS Config rule `required-tags` to enforce tagging compliance. Activate cost allocation tags in AWS Billing for tenant cost attribution. |
| **Evidence** | `terraform/workshop/main.tf` (local.tags = { Blueprint = var.name }), `terraform/workshop/providers.tf` (no default_tags), `terraform/modules/tenant-apps/main.tf` (Name = var.tenant_id on DynamoDB/SQS) |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS — AWS SkillBuilder](https://skillbuilder.aws/learn/R4B13K95YQ)

No other pathways were triggered — no additional pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `terraform/workshop/main.tf` | INF-Q1, INF-Q2, INF-Q5, INF-Q7, INF-Q9, INF-Q10, SEC-Q4, SEC-Q5, OPS-Q9 | EKS cluster, VPC, managed node groups, SSM parameters, tags |
| `terraform/workshop/saas_gitops.tf` | INF-Q10, SEC-Q5 | GitOps infra module, Flux configuration, ConfigMap with gitea_token |
| `terraform/workshop/variables.tf` | INF-Q1, INF-Q9 | Cluster version (1.32), VPC CIDR |
| `terraform/workshop/providers.tf` | OPS-Q9 | AWS provider without default_tags |
| `terraform/modules/gitops-saas-infra/main.tf` | INF-Q4, INF-Q10, SEC-Q4, SEC-Q6 | SQS queues, IRSA roles, Karpenter, Argo, LB Controller |
| `terraform/modules/gitops-saas-infra/apps_needs.tf` | INF-Q8, INF-Q10, SEC-Q2, SEC-Q6, SEC-Q7 | ECR repositories (scan_on_push, AES256), S3 buckets (checkov skips) |
| `terraform/modules/gitea/main.tf` | INF-Q1, INF-Q5, INF-Q9, SEC-Q2, SEC-Q6 | Gitea EC2 instance, security group, public subnet, IMDSv2 |
| `terraform/modules/gitea/userdata.sh` | INF-Q2, DATA-Q3, SEC-Q3, SEC-Q5 | Gitea Docker setup, SQLite, admin auth, SSM tokens |
| `terraform/modules/tenant-apps/main.tf` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q2, OPS-Q9 | DynamoDB (PITR), SQS queues, IRSA, tenant tagging |
| `terraform/modules/flux_cd/main.tf` | INF-Q10, SEC-Q5 | Flux operator, kubernetes_secret, FluxInstance |
| `terraform/install.sh` | INF-Q11 | Manual install script |
| `gitops/clusters/production/infrastructure.yaml` | INF-Q11, OPS-Q5 | Flux Kustomization with postBuild substitution |
| `gitops/infrastructure/production/01-metric-server.yaml` | OPS-Q1 | Metrics-server (not tracing) |
| `gitops/infrastructure/production/02-karpenter.yaml` | INF-Q1, INF-Q7 | Karpenter HelmRelease v1.4.0 |
| `gitops/infrastructure/production/03-argo-workflows.yaml` | INF-Q3, INF-Q5, INF-Q6, SEC-Q3 | Argo Workflows HelmRelease, --auth-mode=server, internet-facing LB |
| `gitops/infrastructure/production/04-lb-controller.yaml` | INF-Q6 | AWS LB Controller HelmRelease v1.6.2 |
| `gitops/infrastructure/production/05-kubecost.yaml` | INF-Q6, OPS-Q3, OPS-Q4, SEC-Q3 | Kubecost with Prometheus, internet-facing LB |
| `gitops/infrastructure/production/06-argo-events.yaml` | INF-Q3 | Argo Events HelmRelease, IRSA |
| `gitops/infrastructure/production/07-tf-controller.yaml` | INF-Q10, INF-Q11 | TF Controller HelmRelease |
| `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` | INF-Q1, INF-Q7, SEC-Q6 | Karpenter NodePool, EC2NodeClass, al2023@latest |
| `gitops/control-plane/production/workflows/tenant-onboarding-workflow-template.yaml` | INF-Q3 | WorkflowTemplate with sequenced steps |
| `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | INF-Q3, INF-Q4 | SQS EventSource + Sensor for onboarding |
| `gitops/control-plane/production/workflows/event-bus.yaml` | INF-Q3, INF-Q9 | NATS EventBus with 3 replicas |
| `helm-charts/application-chart/values.yaml` | INF-Q7, OPS-Q5 | autoscaling.enabled: false, replicaCount: 1 |
| `helm-charts/application-chart/templates/hpa.yaml` | INF-Q7 | HPA template (disabled by default) |
| `helm-charts/application-chart/templates/deployment.yaml` | OPS-Q5 | Standard Deployment (no rollout strategy) |
| `helm-charts/application-chart/templates/tests/test-connection.yaml` | OPS-Q6 | Basic Helm test (wget only) |
| `tenant-microservices/consumer/.gitea/workflows/build-and-push.yml` | INF-Q11, SEC-Q7, OPS-Q6 | CI pipeline — build and push only, no tests or security |
| `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` | INF-Q11 | CI pipeline — build and push only |
| `tenant-microservices/payments/.gitea/workflows/build-and-push.yml` | INF-Q11 | CI pipeline — build and push only |
