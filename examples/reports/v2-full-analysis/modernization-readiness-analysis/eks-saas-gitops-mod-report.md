# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | eks-saas-gitops |
| **Date** | 2025-07-17 |
| **Repo Type** | `infrastructure-only` |
| **Priority** | P1 |
| **Tags** | eks, gitops, terraform, saas, infrastructure |
| **Context** | EKS SaaS GitOps monorepo with Terraform IaC, Karpenter, and multi-tenant infrastructure. Classified as infrastructure-only to test N/A mappings, everything that is not serverless will run here, EKS will be the centralized platform |
| **Overall Score** | **2.49 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 3.00 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | N/A | N/A — all questions not applicable for `infrastructure-only` |
| Data Platform Modernization (DATA) | 4.00 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **2.49 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail configuration in IaC — zero audit trail for API actions | Compliance blocker; impossible to investigate security incidents or meet regulatory requirements |
| 2 | SEC-Q3: API Authentication | 1 | Argo Workflows server exposed internet-facing with `--auth-mode=server` (no authentication) | Critical security risk; unauthenticated access to workflow orchestration and cluster operations |
| 3 | OPS-Q1: Distributed Tracing | 1 | No X-Ray, OpenTelemetry, or any tracing instrumentation across the platform | Cannot diagnose cross-service failures or understand request flows through the multi-tenant platform |
| 4 | OPS-Q4: Anomaly Detection and Alerting | 1 | No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration | Platform outages or degradation go undetected until user-reported; no proactive incident detection |
| 5 | OPS-Q9: Resource Tagging Governance | 1 | Only Name and Blueprint tags; no cost allocation, no ownership, no tag enforcement | Cannot attribute costs per tenant or workload; ownership ambiguous during incidents; FinOps impossible |

---

## Quick Agent Wins

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 >= 2 — Score: 4. Argo Workflows (v0.40.11) and Argo Events (v2.4.3) are deployed with SQS-triggered sensors for tenant onboarding, offboarding, and deployment workflows (`gitops/control-plane/production/workflows/`).
- **What it enables:** An agent that monitors Argo Workflow execution status, detects failed tenant onboarding/offboarding workflows, retries or escalates automatically, and provides natural-language status summaries of in-progress tenant lifecycle operations.
- **Additional steps:** Expose Argo Workflows API with proper authentication (currently `--auth-mode=server` with no auth). Add structured logging to workflow steps to provide richer context for agent consumption.
- **Effort:** Medium — Argo Workflows API exists but requires authentication before agent access is safe.

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in repo — `README.md` (343 lines) provides comprehensive architecture documentation, deployment steps, features, use cases, and AWS service descriptions. Helm chart templates and tier-template YAML files document the multi-tenant architecture patterns.
- **What it enables:** A RAG-based knowledge agent that indexes the repository documentation, Terraform module structure, Helm chart configurations, and workflow definitions to answer developer questions about the platform architecture, tenant onboarding process, and infrastructure configuration.
- **Additional steps:** Index `README.md`, Helm chart `values.yaml.template`, tier-template YAML files, and workflow scripts as the knowledge corpus. Consider generating API documentation for the Argo Workflows and Argo Events sensor configurations.
- **Effort:** Low — documentation corpus exists and is well-structured; standard RAG indexing pipeline applies.

### DevOps Agent

- **Prerequisite:** INF-Q11 >= 2 — Score: 2. Gitea Actions workflows exist in `tenant-microservices/*/.gitea/workflows/build-and-push.yml` for building and pushing Docker images. Flux CD handles GitOps deployments via HelmRelease reconciliation. Argo Workflows automates tenant lifecycle operations.
- **What it enables:** An agent that triggers Gitea Actions builds, monitors Flux reconciliation status, checks HelmRelease health, and manages tenant onboarding by sending SQS messages to trigger Argo Workflows.
- **Additional steps:** Formalize the Gitea Actions CI pipeline with test stages. Expose Flux and Argo APIs with authentication for agent consumption. Consider adding Terraform plan/apply automation via the TF Controller API.
- **Effort:** Medium — CI pipeline exists but needs hardening; multiple automation surfaces (Gitea, Flux, Argo) need secure API access.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 2 | Move to Containers | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 is N/A; no commercial database engines detected — all databases are DynamoDB. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all databases are fully managed DynamoDB with PITR. |
| 5 | Move to Managed Analytics | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q11 = 2 (no formal CI/CD pipeline definitions in repo); OPS-Q5 = 2 (no canary/blue-green); OPS-Q6 = 1 (no integration tests). |
| 7 | Move to AI | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

**IaC Coverage (INF-Q10 = 4):** Infrastructure as Code coverage is excellent. Terraform defines the full platform stack — VPC, EKS cluster, IAM roles, ECR repositories, SQS queues, DynamoDB tables, S3 buckets, and all supporting IAM policies. Flux CD provides GitOps-based continuous delivery with Kustomizations and HelmReleases managing the Kubernetes layer. The TF Controller enables Terraform execution from within the cluster for tenant-specific infrastructure provisioning.

**CI/CD Gaps (INF-Q11 = 2):** While Flux CD provides excellent GitOps-based *deployment* automation, there is no formalized CI pipeline for building, testing, and validating changes before they reach the GitOps repository. Gitea Actions workflows exist for tenant microservices (`tenant-microservices/*/.gitea/workflows/build-and-push.yml`) but these are sample application pipelines — not infrastructure validation pipelines. There is no Terraform validation pipeline (plan, validate, security scan) and no Helm chart linting/testing pipeline.

**Deployment Strategy Gaps (OPS-Q5 = 2):** Flux provides rolling updates by default via HelmRelease reconciliation, but there is no canary, blue/green, or progressive delivery configuration. All changes to HelmReleases are applied directly. For a multi-tenant platform where infrastructure changes affect all tenants, progressive delivery is critical to limit blast radius.

**Testing Gaps (OPS-Q6 = 1):** No integration tests exist in the repository. The Helm chart has a standard `test-connection.yaml` template but no meaningful validation of platform functionality after deployment.

#### Recommended DevOps Toolchain (respecting preferences: prefer Terraform, GitOps; avoid manual-deployments)

1. **Terraform CI Pipeline via Gitea Actions or AWS CodePipeline:**
   - Add a Gitea Actions workflow (or AWS CodeBuild `buildspec.yml`) that runs `terraform fmt -check`, `terraform validate`, `terraform plan`, and `checkov` on every pull request targeting the `terraform/` directory.
   - Use the existing TF Controller for GitOps-driven Terraform applies, but gate them behind validated plans.

2. **Helm Chart Validation Pipeline:**
   - Add `helm lint`, `helm template`, and `kubeval`/`kubeconform` validation for both `helm-tenant-chart` and `application-chart`.
   - Run chart tests against a kind/k3d cluster in CI before pushing to ECR.

3. **Progressive Delivery with Flagger:**
   - Deploy [Flagger](https://flagger.app/) alongside the existing AWS Load Balancer Controller to enable canary deployments for tenant workloads.
   - Flagger integrates natively with Flux CD and supports ALB-based traffic shifting.

4. **Integration Testing:**
   - Add post-deployment smoke tests triggered by Flux notification controller webhooks.
   - Test tenant onboarding workflows end-to-end by sending test SQS messages and validating namespace/HelmRelease creation.

5. **Observability-Driven Delivery:**
   - Integrate Prometheus metrics (already deployed via Kubecost) with Flagger for automated canary analysis.
   - Add CloudWatch alarms for critical platform components and wire them to Flux health checks.

#### Representative AWS Services
- **AWS CodeBuild** — Terraform plan validation, Helm chart linting, container image builds
- **AWS CodePipeline** — Orchestrate multi-stage CI/CD pipelines
- **Amazon ECR** (already in use) — Container image and Helm chart OCI registry with scan-on-push
- **AWS CloudWatch** — Metrics, alarms, and dashboards for observability-driven delivery
- **Flux CD** (already in use) — GitOps continuous delivery
- **Flagger** — Progressive delivery (canary/blue-green) integrated with Flux

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
| **Finding** | Primary compute runs on Amazon EKS (v1.32) via `module.eks` in `terraform/workshop/main.tf` with managed node groups (m5.large, min 3 / max 5). Karpenter (v1.4.0) is deployed via HelmRelease (`gitops/infrastructure/production/02-karpenter.yaml`) with two NodePools: `default` and `application` (`gitops/infrastructure/production/dependencies/`). Karpenter provisions on-demand and spot instances across c/m/r families with consolidation policies. However, Gitea runs on a raw EC2 instance (`aws_instance.gitea` in `terraform/modules/gitea/main.tf`) — an m5.large in a public subnet with no managed orchestration. |
| **Gap** | Gitea server runs on unmanaged EC2 with no auto-scaling, no health-check-based recovery, and no container orchestration. This is a single point of failure for the Git repository backing the entire GitOps platform. |
| **Recommendation** | Migrate the Gitea server to run as a Kubernetes deployment on the existing EKS cluster, or replace it with a managed Git service (e.g., AWS CodeCommit, or a Gitea Helm chart running on EKS with persistent storage). This eliminates the raw EC2 dependency and brings Gitea under the same operational model as all other platform components. |
| **Evidence** | `terraform/workshop/main.tf` (module.eks, module.gitea), `terraform/modules/gitea/main.tf` (aws_instance.gitea), `gitops/infrastructure/production/02-karpenter.yaml`, `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All databases are fully managed DynamoDB tables provisioned via `terraform/modules/tenant-apps/main.tf`. Tables use `PAY_PER_REQUEST` billing mode with `point_in_time_recovery` enabled. Each tenant gets a dedicated DynamoDB table (`consumer-{tenant_id}-{suffix}`) with hash key `tenant_id` and range key `message_id`. No self-managed databases (no RDS on EC2, no database containers, no on-premises references). Gitea uses SQLite3 internally (configured in `userdata.sh`), which is ephemeral to the Gitea container. |
| **Gap** | No significant gaps. DynamoDB is fully managed with automated failover and no patching requirements. |
| **Recommendation** | No action needed for database management. Consider adding DynamoDB auto-scaling if workload patterns become predictable (currently PAY_PER_REQUEST handles this automatically). |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table.consumer_ddb), `terraform/modules/gitea/userdata.sh` (GITEA__database__DB_TYPE=sqlite3) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Argo Workflows (v0.40.11) is deployed via HelmRelease (`gitops/infrastructure/production/03-argo-workflows.yaml`) with S3 artifact storage and IRSA-based AWS authentication. Argo Events (v2.4.3) is deployed via HelmRelease (`gitops/infrastructure/production/06-argo-events.yaml`) with EventBus (NATS, 3 replicas). Three SQS-triggered EventSources and Sensors orchestrate tenant lifecycle: onboarding (`tenant-onboarding-sensor.yaml`), deployment (`tenant-deployment-sensor.yaml`), and offboarding (`tenant-offboarding-sensor.yaml`). WorkflowTemplates define multi-step workflows with Git clone, validation, and Helm release creation/update/deletion. The TF Controller (v0.16.0-rc.4) enables Terraform-based infrastructure provisioning from within Kubernetes workflows. |
| **Gap** | No significant gaps for workflow orchestration. The Argo Workflows + Events + SQS pattern is a well-architected, event-driven orchestration approach. |
| **Recommendation** | Consider adding workflow retries and dead-letter queues for failed SQS messages. The current SQS queues have no DLQ configured, meaning failed messages may be lost. |
| **Evidence** | `gitops/infrastructure/production/03-argo-workflows.yaml`, `gitops/infrastructure/production/06-argo-events.yaml`, `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml`, `gitops/control-plane/production/workflows/tenant-deployment-sensor.yaml`, `gitops/control-plane/production/workflows/tenant-offboarding-sensor.yaml`, `terraform/modules/gitops-saas-infra/main.tf` (SQS queues) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Managed SQS queues are used extensively: `karpenter_interruption_queue` for Karpenter spot interruption handling, three Argo Workflows queues (`argoworkflows-onboarding-queue`, `argoworkflows-offboarding-queue`, `argoworkflows-deployment-queue`) for event-driven tenant lifecycle, and per-tenant `consumer-{tenant_id}` SQS queues for application messaging. All queues use `sqs_managed_sse_enabled = true`. Argo Events sensors consume SQS messages to trigger Kubernetes workflows. |
| **Gap** | Messaging is SQS-only. No event bus pattern (e.g., EventBridge) for platform-wide event routing. No streaming infrastructure (Kinesis, MSK) for real-time data flows. For a multi-tenant SaaS platform, an event bus pattern would enable decoupled communication between platform services. |
| **Recommendation** | Add Amazon EventBridge as a central event bus for platform-level events (tenant created, tenant deleted, deployment completed, scaling event). This complements the existing SQS queues (which are point-to-point) with a pub/sub pattern that enables multiple consumers per event. EventBridge aligns with the `prefer: ["eventbridge"]` technology preference. |
| **Evidence** | `terraform/modules/gitops-saas-infra/main.tf` (aws_sqs_queue.karpenter_interruption_queue, argoworkflows_*_queue), `terraform/modules/tenant-apps/main.tf` (aws_sqs_queue.consumer_sqs), `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | VPC is configured with 3 AZs, private and public subnets, and a NAT gateway (`terraform/workshop/main.tf` using `terraform-aws-modules/vpc/aws` v4.0.2). EKS worker nodes run in private subnets. However: (1) `cluster_endpoint_public_access = true` exposes the EKS API server to the internet. (2) Gitea EC2 instance is in a public subnet with `associate_public_ip_address = true`. (3) Gitea security group has egress `0.0.0.0/0` on all ports. (4) Argo Workflows server uses `service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"` with `--auth-mode=server` (no authentication). (5) Kubecost and Capacitor services also use internet-facing LoadBalancers. |
| **Gap** | Multiple services exposed to the internet without authentication or proper network segmentation. EKS API server publicly accessible. Argo Workflows dashboard is internet-facing with no authentication — this provides unauthenticated access to execute workflows that have full cluster admin (ClusterRole `full-permissions-cluster-role` with `*/*` permissions). |
| **Recommendation** | (1) Set `cluster_endpoint_public_access = false` and access the EKS API via VPN or bastion. (2) Move Gitea to a private subnet and access via VPN/peering. (3) Add authentication to Argo Workflows (e.g., SSO via Dex or OIDC). (4) Switch all management UIs (Argo, Kubecost, Capacitor) to `internal` load balancer scheme and access via VPN. (5) Restrict Gitea SG egress to required destinations only. |
| **Evidence** | `terraform/workshop/main.tf` (cluster_endpoint_public_access=true, single_nat_gateway=true), `terraform/modules/gitea/main.tf` (aws_instance.gitea, aws_security_group.gitea), `gitops/infrastructure/production/03-argo-workflows.yaml` (--auth-mode=server, internet-facing LB), `gitops/infrastructure/production/05-kubecost.yaml` (internet-facing LB) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS Load Balancer Controller (v1.6.2) is deployed via HelmRelease (`gitops/infrastructure/production/04-lb-controller.yaml`) with IRSA. Tenant workloads use ALB Ingress with path-based routing, health checks, and HTTP header-based tenant isolation (`alb.ingress.kubernetes.io/conditions` in `helm-charts/helm-tenant-chart/templates/ingress.yaml`). The ingress uses `alb.ingress.kubernetes.io/group.name: "tenants-lb"` to share an ALB across tenants. |
| **Gap** | No API Gateway in front of the ALB. The ALB provides basic routing and health checks but lacks throttling, request validation, API key management, and usage plans. For a multi-tenant SaaS platform, API Gateway provides per-tenant rate limiting and API key isolation. |
| **Recommendation** | Add Amazon API Gateway in front of the ALB for tenant-facing API endpoints. This provides per-tenant API keys, throttling (per-tenant rate limits), request validation, and usage plans — all critical for multi-tenant SaaS. API Gateway aligns with the `prefer: ["api-gateway"]` technology preference. |
| **Evidence** | `gitops/infrastructure/production/04-lb-controller.yaml`, `helm-charts/helm-tenant-chart/templates/ingress.yaml` (ALB ingress annotations), `terraform/modules/gitops-saas-infra/main.tf` (lb_controller_irsa) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Karpenter provides node-level auto-scaling with two NodePools: `default` (1000 CPU, 2000Gi limits) and `application` (same limits, with taints for isolation). Consolidation policy is `WhenEmptyOrUnderutilized` with 1m consolidation delay. EKS managed node group has min 3 / max 5 nodes. HPA templates exist in both Helm charts (`helm-charts/helm-tenant-chart/templates/hpa.yaml` and `helm-charts/application-chart/templates/hpa.yaml`) but `autoscaling.enabled = false` by default in values. |
| **Gap** | Node-level scaling is excellent via Karpenter, but application-level scaling (HPA) is disabled by default. Tenants on the `premium` and `advanced` tiers get dedicated deployments but no auto-scaling — they rely on fixed replica counts (3 replicas). The metrics-server is deployed (`gitops/infrastructure/production/01-metric-server.yaml`) so HPA infrastructure is ready but unused. |
| **Recommendation** | Enable HPA by default in the tenant tier templates, at least for `premium` tier. Set `autoscaling.enabled: true` with appropriate min/max replicas based on tier. The metrics-server is already deployed, so HPA will work immediately. Consider adding KEDA for SQS-based scaling of the consumer workload. |
| **Evidence** | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (NodePool limits), `helm-charts/helm-tenant-chart/templates/hpa.yaml`, `helm-charts/helm-tenant-chart/values.yaml.template` (autoscaling.enabled: false), `terraform/workshop/main.tf` (eks_managed_node_groups min/max) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DynamoDB tables have `point_in_time_recovery` enabled (`terraform/modules/tenant-apps/main.tf`), providing continuous backup with 35-day retention. However, S3 buckets explicitly skip versioning and lifecycle policies (checkov skip comments: `CKV2_AWS_21: Versioning is not needed at this time`, `CKV2_AWS_61: This S3 bucket has no lifecycle requirements`). No `aws_backup_plan` resources found. No EBS snapshot lifecycle policies. Gitea's SQLite database has no backup mechanism. |
| **Gap** | S3 buckets (Argo artifacts, code artifacts) have no versioning or backup. Gitea's data (including all Git repositories that back the GitOps platform) resides on an EC2 instance with no backup configuration. No centralized backup plan via AWS Backup. |
| **Recommendation** | (1) Enable S3 versioning on `argo_artifacts` and `codeartifacts` buckets. (2) Create an `aws_backup_plan` using Terraform covering DynamoDB tables, S3 buckets, and EBS volumes. (3) Add a Velero deployment to the EKS cluster for Kubernetes resource and persistent volume backup. (4) Critical: implement Gitea data backup (snapshot the EBS volume or migrate Gitea to EKS with persistent volume backup). |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (point_in_time_recovery enabled), `terraform/modules/gitops-saas-infra/main.tf` (aws_s3_bucket.argo_artifacts — checkov skip CKV2_AWS_21), `terraform/modules/gitops-saas-infra/apps_needs.tf` (aws_s3_bucket.codeartifacts — checkov skip CKV2_AWS_21) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | VPC spans 3 AZs with private and public subnets across all AZs (`terraform/workshop/main.tf`). EKS managed node group spans private subnets across AZs. Karpenter provisions nodes across AZs via subnet discovery tags (`karpenter.sh/discovery`). Argo Events EventBus uses NATS with 3 replicas for HA. DynamoDB is inherently multi-AZ. |
| **Gap** | Single NAT gateway (`single_nat_gateway = true`) is a single point of failure — if the NAT gateway's AZ goes down, all private subnet outbound traffic is disrupted. Gitea is a single EC2 instance with no redundancy. EKS managed node group does not specify `subnet_ids` per AZ explicitly (relies on VPC module output). |
| **Recommendation** | (1) Set `single_nat_gateway = false` and `one_nat_gateway_per_az = true` in the VPC module for AZ-level NAT redundancy. (2) Migrate Gitea to a HA configuration (e.g., running on EKS with multiple replicas and persistent storage, or using a managed Git service). (3) Add pod disruption budgets (PDBs) for critical platform components (Argo Workflows controller, Flux controllers). |
| **Evidence** | `terraform/workshop/main.tf` (single_nat_gateway=true, azs=3), `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (subnet discovery), `gitops/control-plane/production/workflows/event-bus.yaml` (NATS replicas: 3) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive Terraform coverage defining: VPC with subnets and NAT (`terraform/workshop/main.tf`), EKS cluster with managed node groups and cluster addons, IAM roles/policies with IRSA for 6 service accounts, ECR repositories for Helm charts and microservices, SQS queues for platform and tenant messaging, S3 buckets for artifacts, DynamoDB tables per tenant, SSM parameters, and security groups. GitOps layer via Flux CD manages all Kubernetes resources: 7 HelmReleases (metrics-server, Karpenter, Argo Workflows, LB Controller, Kubecost, Argo Events, TF Controller), Kustomizations, HelmRepositories, image automation policies, and tenant-specific HelmReleases. The TF Controller enables in-cluster Terraform execution for tenant infrastructure provisioning. |
| **Gap** | Minor: CloudFormation template for VSCode server (`helpers/vs-code-ec2.yaml`) is a manual helper, not integrated into the Terraform workflow. The Gitea setup relies on `userdata.sh` with imperative scripting rather than declarative configuration. |
| **Recommendation** | No major action needed. Consider migrating the VSCode CloudFormation template to Terraform for consistency. Replace the Gitea `userdata.sh` imperative setup with a declarative approach (e.g., Helm chart on EKS or a Packer-built AMI). |
| **Evidence** | `terraform/workshop/main.tf`, `terraform/workshop/saas_gitops.tf`, `terraform/modules/gitops-saas-infra/main.tf`, `terraform/modules/tenant-apps/main.tf`, `gitops/clusters/production/infrastructure.yaml`, `gitops/infrastructure/production/*.yaml`, `gitops/infrastructure/base/sources/*.yaml`, `terraform/modules/flux_cd/main.tf` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Flux CD provides GitOps-based continuous delivery — changes committed to the Git repository are automatically reconciled to the EKS cluster via Kustomizations and HelmReleases (1m reconciliation interval). Image automation controllers detect new container image tags and update HelmRelease values automatically. Gitea Actions runner is installed on the Gitea EC2 instance (`terraform/modules/gitea/userdata.sh`), and sample CI workflows exist for tenant microservices (`tenant-microservices/*/. gitea/workflows/build-and-push.yml`) that build and push Docker images to ECR. However, there are no CI pipeline definitions for the infrastructure code itself — no Terraform validation pipeline, no Helm chart linting, no security scanning, and no automated testing before deployment. |
| **Gap** | No CI pipeline for infrastructure validation. Terraform changes are applied via TF Controller without prior plan review or automated validation. No Helm chart testing. The Gitea Actions workflows are sample application pipelines, not infrastructure pipelines. The deployment side (CD) is well-automated via Flux, but the build/validate side (CI) is missing. |
| **Recommendation** | Add Terraform CI pipelines (via Gitea Actions or AWS CodeBuild) that run `terraform validate`, `terraform plan`, `checkov`, and `tflint` on pull requests. Add Helm chart CI with `helm lint`, `helm template`, and `kubeconform`. Gate Terraform applies behind approved plans. This is the primary trigger for the **Move to Modern DevOps** pathway. |
| **Evidence** | `terraform/modules/flux_cd/main.tf` (Flux operator), `gitops/clusters/production/infrastructure.yaml` (Flux Kustomization), `terraform/modules/gitea/userdata.sh` (Gitea Actions runner setup), `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` |

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
| **Score** | 4 |
| **Finding** | All databases are Amazon DynamoDB, which is a fully managed, serverless, versionless database service. DynamoDB has no engine version concept — AWS manages all upgrades transparently with no customer action required. There are no RDS, Aurora, DocumentDB, ElastiCache, or other versioned database engines in the infrastructure. DynamoDB is never end-of-life. |
| **Gap** | No gaps. DynamoDB eliminates all database engine version management concerns. |
| **Recommendation** | No action needed. If relational database needs arise in the future, use Amazon Aurora (aligning with `prefer: ["aurora"]`) with explicit engine version pinning in Terraform. |
| **Evidence** | `terraform/modules/tenant-apps/main.tf` (aws_dynamodb_table.consumer_ddb — no engine_version parameter exists for DynamoDB) |

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
| **Finding** | No `aws_cloudtrail` resource found in any Terraform file. No CloudTrail configuration in the IaC. No CloudWatch log retention policies for API audit trails. The README mentions CloudWatch for monitoring but no audit logging implementation exists. |
| **Gap** | Complete absence of audit logging. No trail exists to track API calls, IAM actions, or resource changes. This is a compliance blocker for any production SaaS platform. For a multi-tenant platform with tenant data isolation requirements, audit logging is critical. |
| **Recommendation** | Add `aws_cloudtrail` resource in Terraform with: (1) Multi-region trail enabled, (2) Log file validation enabled, (3) S3 bucket with Object Lock for immutable storage, (4) CloudWatch Logs integration with defined retention period, (5) Management events and data events for S3/DynamoDB. Use Terraform to define the trail consistent with the existing IaC approach. |
| **Evidence** | Searched all files in `terraform/` — no `aws_cloudtrail` resource found. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS-managed encryption is enabled on most data stores: ECR repositories use AES256 (`encryption_configuration { encryption_type = "AES256" }` in `apps_needs.tf`), SQS queues use `sqs_managed_sse_enabled = true`, Gitea EC2 root volume has `encrypted = true`, DynamoDB uses default encryption. S3 buckets use default encryption (AES256). |
| **Gap** | No customer-managed KMS keys (`aws_kms_key` resources). Checkov skip comments explicitly note this: `CKV2_AWS_145: This S3 bucket does not require KMS Encryption`. AWS-managed encryption provides baseline protection but does not offer customer-controlled key rotation, cross-account key policies, or granular access control via key policies. |
| **Recommendation** | Create a customer-managed KMS key in Terraform and apply it to: (1) S3 buckets (Argo artifacts, code artifacts), (2) SQS queues, (3) ECR repositories, (4) EBS volumes. This provides key rotation control, audit trail via CloudTrail, and the ability to revoke access by disabling the key. |
| **Evidence** | `terraform/modules/gitops-saas-infra/apps_needs.tf` (encryption_configuration AES256), `terraform/modules/gitops-saas-infra/main.tf` (sqs_managed_sse_enabled), `terraform/modules/gitea/main.tf` (root_block_device encrypted=true) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Argo Workflows server is configured with `--auth-mode=server` (`gitops/infrastructure/production/03-argo-workflows.yaml`), which disables authentication entirely. The comment reads "This is for demonstration purposes only." This service is exposed via an internet-facing LoadBalancer, meaning anyone can access the Argo Workflows UI and execute workflows that have full cluster admin permissions (`full-permissions-cluster-role` with `apiGroups: ["*"], resources: ["*"], verbs: ["*"]`). Kubecost and Capacitor are also internet-facing with no authentication. Gitea uses basic password authentication stored in SSM. No API Gateway authorizers, no Cognito, no OAuth2/JWT. |
| **Gap** | Critical: The Argo Workflows dashboard is internet-accessible with no authentication AND full cluster admin permissions. This is a production-blocking security vulnerability. No API endpoints in the platform have token-based or OAuth2 authentication. |
| **Recommendation** | (1) Immediately: Remove `--auth-mode=server` from Argo Workflows and configure SSO authentication via Dex or OIDC. (2) Switch all management UIs to internal LoadBalancers. (3) Add Amazon API Gateway with Cognito authorizers for tenant-facing API endpoints. (4) Implement RBAC in Argo Workflows to limit workflow execution permissions per namespace. |
| **Evidence** | `gitops/infrastructure/production/03-argo-workflows.yaml` (--auth-mode=server, internet-facing LB), `gitops/infrastructure/production/03-argo-workflows.yaml` (full-permissions-cluster-role) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service-level identity is well-implemented via IRSA (IAM Roles for Service Accounts) using OIDC: Karpenter, Argo Workflows, Argo Events, LB Controller, TF Controller, and image automation controllers all use IRSA for AWS API access. EKS uses `aws_auth_configmap` for Kubernetes RBAC mapping. However, there is no centralized human-user identity: no Cognito user pools, no OIDC/SAML federation for platform administrators, no SSO configuration. Gitea manages its own authentication with local users. |
| **Gap** | Human-user authentication is fragmented — EKS access via IAM roles, Gitea via local password, Argo Workflows with no auth. No centralized IdP for platform operators or tenant administrators. |
| **Recommendation** | Integrate with a centralized IdP (e.g., AWS IAM Identity Center/SSO, Cognito, or Okta). Configure EKS OIDC authentication for `kubectl` access. Add Dex or direct OIDC integration to Argo Workflows. Federate Gitea with the centralized IdP. |
| **Evidence** | `terraform/modules/gitops-saas-infra/main.tf` (IRSA modules for karpenter, argo_workflows, argo_events, lb_controller, tf_controller), `terraform/workshop/main.tf` (manage_aws_auth_configmap=true) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | AWS SSM Parameter Store is used for secrets: Gitea admin password (`SecureString` in `terraform/workshop/main.tf`), Gitea Flux token, Gitea CI/CD token, and per-tenant SQS/DDB ARNs (non-sensitive `String` type). Kubernetes secrets store Flux system credentials (`terraform/modules/flux_cd/main.tf`). Checkov skip comment notes `CKV_AWS_337: Skiping this for now, move to Secrets Manager` — acknowledging the gap. |
| **Gap** | No AWS Secrets Manager usage. No secret rotation configured. Git tokens are passed as workflow parameters in Argo Workflows sensors (`GIT_TOKEN` as plain-text parameter in `tenant-onboarding-sensor.yaml`). The `kubernetes_secret.flux_system` stores the Gitea token directly in a Kubernetes secret created by Terraform. The Gitea admin password is generated by `random_password` and stored in SSM but never rotated. |
| **Recommendation** | (1) Migrate from SSM Parameter Store to AWS Secrets Manager for all sensitive values (passwords, tokens). (2) Enable automatic rotation for the Gitea admin password and API tokens. (3) Replace plain-text `GIT_TOKEN` workflow parameters with Kubernetes secret references or AWS Secrets Manager integration. (4) Use External Secrets Operator on EKS to sync AWS Secrets Manager secrets to Kubernetes secrets. |
| **Evidence** | `terraform/workshop/main.tf` (aws_ssm_parameter.gitea_password, CKV_AWS_337 skip), `terraform/modules/flux_cd/main.tf` (kubernetes_secret.flux_system), `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` (GIT_TOKEN parameter) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Karpenter EC2NodeClass uses `al2023@latest` AMI selector (Amazon Linux 2023 — current generation, reasonable default). `AmazonSSMManagedInstanceCore` is attached to the Karpenter node role, enabling SSM Agent access. ECR repositories have `scan_on_push = true` for container image vulnerability scanning. EKS managed node groups use default AMIs (no hardened AMI specification). Gitea EC2 uses Amazon Linux 2 AMI (`amzn2-ami-hvm-*-x86_64-gp2`), which is older generation. |
| **Gap** | No SSM Patch Manager configuration for automated OS patching. No AWS Inspector for continuous vulnerability analysis. No hardened AMI references (CIS benchmarks, Bottlerocket). Karpenter uses `al2023@latest` which is regularly updated but there's no automated node rotation to pick up new AMIs. Gitea uses AL2 (older) rather than AL2023. No container image signing or verification. |
| **Recommendation** | (1) Switch Karpenter AMI to Bottlerocket (`alias: bottlerocket@latest`) for a hardened, immutable OS. (2) Configure Karpenter `drift` detection to automatically rotate nodes when new AMIs are available. (3) Add AWS Inspector for continuous vulnerability scanning of EC2 instances and container images. (4) Add SSM Patch Manager baselines for the Gitea EC2 instance. (5) Migrate Gitea to AL2023 or containerize it on EKS. |
| **Evidence** | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (amiSelectorTerms al2023@latest), `terraform/modules/gitops-saas-infra/main.tf` (AmazonSSMManagedInstanceCore), `terraform/modules/gitops-saas-infra/apps_needs.tf` (scan_on_push=true), `terraform/modules/gitea/main.tf` (amzn2-ami-hvm) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECR `scan_on_push = true` provides container image vulnerability scanning on all ECR repositories. Checkov skip comments throughout the Terraform code indicate security awareness (e.g., `CKV_AWS_337`, `CKV2_AWS_145`, `CKV2_AWS_21`) but Checkov is not integrated into any CI pipeline — the skips are manual annotations. Gitea Actions workflows (`build-and-push.yml`) build and push images but include no security scanning steps. No Dependabot, Snyk, SonarQube, Semgrep, or CodeGuru Reviewer configuration. |
| **Gap** | ECR scan-on-push is the only automated security scanning. No SAST, DAST, or dependency scanning in any CI pipeline. Checkov is referenced in skip comments but not executed as a pipeline step. The Gitea Actions workflows are build-only with no security gates. |
| **Recommendation** | (1) Add `checkov` as a pipeline step in the Terraform CI workflow (when created per INF-Q11 recommendation). (2) Add `trivy` or `snyk` container scanning in the Gitea Actions workflows before pushing to ECR. (3) Add `tfsec` or `checkov` as a pre-commit hook or CI step for Terraform code. (4) Configure Dependabot-equivalent for Python dependencies in tenant-microservices. (5) Add `kubeaudit` or `kube-linter` for Kubernetes manifest validation. |
| **Evidence** | `terraform/modules/gitops-saas-infra/apps_needs.tf` (scan_on_push=true), `terraform/modules/gitops-saas-infra/main.tf` (checkov skip comments), `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` (no security steps) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found anywhere in the repository. No X-Ray SDK, OpenTelemetry Collector, or Jaeger deployments in the GitOps manifests. No `traceparent` or `X-Amzn-Trace-Id` header propagation in the Helm chart templates or workflow definitions. No tracing-related HelmRelease or addon configuration. |
| **Gap** | Complete absence of distributed tracing. For a multi-tenant SaaS platform where tenant workloads share infrastructure, tracing is critical to diagnose cross-tenant performance issues, isolate per-tenant latency, and understand request flows through the producer → SQS → consumer pipeline. |
| **Recommendation** | Deploy OpenTelemetry Collector as a DaemonSet via HelmRelease in the GitOps infrastructure layer. Configure ADOT (AWS Distro for OpenTelemetry) to send traces to X-Ray. Instrument the Argo Workflows and tenant workloads with trace context propagation. Add X-Ray as an EKS addon in Terraform. |
| **Evidence** | Searched all files in `gitops/`, `terraform/`, `helm-charts/` — no tracing-related configuration found. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No error budget tracking, no p99/p95 latency targets, no availability targets. Kubecost (v2.1.0) is deployed for cost visibility but does not provide SLO management. Prometheus is deployed via Kubecost with basic scraping (1m interval) but no SLO-based alerting rules are configured. |
| **Gap** | No formal SLO definitions for the platform or tenant workloads. Without SLOs, there is no objective measure of whether the multi-tenant platform is meeting performance and availability expectations. |
| **Recommendation** | Define SLOs for critical platform operations: (1) Tenant onboarding latency (e.g., 95th percentile < 5 minutes), (2) Flux reconciliation success rate (e.g., 99.9%), (3) Argo Workflow success rate (e.g., 99%), (4) Tenant API availability (e.g., 99.9%). Implement SLO monitoring using Prometheus recording rules and Sloth (SLO generator for Prometheus). |
| **Evidence** | Searched all files — no SLO definitions, error budgets, or latency targets found. `gitops/infrastructure/production/05-kubecost.yaml` (Kubecost for cost, not SLOs). |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Kubecost provides cost metrics with Prometheus integration (1m scrape interval, 120-day ETL storage). Prometheus `node_exporter` is enabled for node-level metrics. No custom business metrics: no tenant onboarding counts, no per-tenant resource utilization, no workflow success/failure rates published to CloudWatch, no SaaS-specific KPIs. |
| **Gap** | Only infrastructure metrics (CPU, memory, cost) are available. No business outcome metrics for the SaaS platform — cannot measure tenant growth, onboarding velocity, resource efficiency per tier, or platform health from a business perspective. |
| **Recommendation** | Publish custom metrics via CloudWatch or Prometheus: (1) Tenant count by tier (basic/advanced/premium), (2) Onboarding/offboarding workflow success/failure rates, (3) Per-tenant resource utilization and cost, (4) Flux reconciliation metrics, (5) SQS queue depth per tenant. Kubecost already provides per-namespace cost allocation — surface this as a business metric. |
| **Evidence** | `gitops/infrastructure/production/05-kubecost.yaml` (cost metrics only), no `cloudwatch.put_metric_data` or custom Prometheus rules found. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudWatch alarms found in any Terraform file. No Prometheus alerting rules configured. No PagerDuty, OpsGenie, or SNS topic integration for alerting. No anomaly detection configuration. Kubecost provides cost anomaly detection natively but it's not configured with alerting targets. |
| **Gap** | Complete absence of alerting. Platform outages, Argo Workflow failures, Flux reconciliation errors, Karpenter provisioning issues, and tenant service degradation all go undetected until manually observed. |
| **Recommendation** | (1) Add Prometheus AlertManager as a HelmRelease in the GitOps infrastructure layer. (2) Configure critical alerts: Flux reconciliation failures, Argo Workflow failures, Karpenter provisioning errors, node not-ready, pod crash loops, SQS DLQ message count > 0. (3) Add CloudWatch alarms via Terraform for SQS queue metrics, DynamoDB throttling, and NAT gateway errors. (4) Integrate with PagerDuty or OpsGenie for on-call notification. |
| **Evidence** | Searched all files in `terraform/`, `gitops/` — no `aws_cloudwatch_metric_alarm`, no Prometheus alerting rules, no PagerDuty/OpsGenie integration found. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Flux CD provides GitOps-based rolling deployments via HelmRelease reconciliation (1m interval). Image automation controllers automatically update HelmRelease values when new container images are detected. Argo Workflows handles tenant onboarding/deployment with SQS-triggered, sequentially-executed workflow steps. Tenant tier templates define deployment configurations per tier (basic=pooled, premium=silo, advanced=hybrid). |
| **Gap** | No canary, blue/green, or progressive delivery strategy. All HelmRelease updates are applied directly as rolling updates. For a multi-tenant platform, a bad deployment to the `pool-1` environment would affect all basic-tier tenants simultaneously. No rollback automation beyond Flux's built-in reconciliation. |
| **Recommendation** | Deploy Flagger alongside the existing AWS LB Controller for progressive delivery. Configure canary deployments for tenant workloads with automated analysis using Prometheus metrics. Implement pre-deployment validation via Flux health checks. Consider using Argo Rollouts as an alternative, which integrates with the existing Argo ecosystem. |
| **Evidence** | `gitops/clusters/production/infrastructure.yaml` (Flux Kustomization), `gitops/application-plane/production/tier-templates/` (no canary annotations), `gitops/infrastructure/base/sources/consumer-image-automation.yaml` (ImageUpdateAutomation) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No integration tests found. The `helm-charts/application-chart/templates/tests/test-connection.yaml` is a standard Helm test template that verifies basic connectivity with `wget` — not a meaningful integration test. No test containers, no pytest-integration, no Postman/Newman collections, no end-to-end tenant onboarding tests. No contract tests between producer and consumer services. |
| **Gap** | Complete absence of integration testing. Cannot validate that: (1) tenant onboarding workflow creates the correct Kubernetes resources, (2) Flux reconciles HelmReleases successfully, (3) producer → SQS → consumer pipeline works end-to-end, (4) per-tenant DynamoDB isolation is correct. |
| **Recommendation** | Add integration tests: (1) Tenant lifecycle tests — send SQS messages to trigger onboarding, validate namespace and HelmRelease creation, validate DynamoDB table creation, then trigger offboarding and validate cleanup. (2) Platform smoke tests triggered post-Flux-reconciliation via notification controller webhooks. (3) Add `helm test` with meaningful assertions in the tenant Helm chart. |
| **Evidence** | `helm-charts/application-chart/templates/tests/test-connection.yaml` (basic wget test only), no integration test directories or frameworks found. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, SSM Automation documents, or Lambda-based remediation found. Argo Workflows provides workflow automation capability but is used exclusively for tenant lifecycle operations (onboarding/offboarding/deployment), not for incident response. No self-healing automation patterns detected. |
| **Gap** | No incident response automation. When platform issues occur (failed Flux reconciliation, Karpenter provisioning failures, SQS DLQ accumulation, tenant namespace issues), resolution is entirely manual. |
| **Recommendation** | (1) Create runbooks in Markdown for common incident types (Flux reconciliation failure, Argo Workflow failure, Karpenter capacity issues, tenant onboarding failure). (2) Add SSM Automation documents for automated remediation (e.g., restart stuck Flux controllers, drain problematic nodes). (3) Leverage the existing Argo Workflows infrastructure to create incident-response workflow templates triggered by alerting. |
| **Evidence** | Searched all files — no runbook files, SSM Automation documents, or self-healing patterns found. Argo Workflows used only for tenant lifecycle (`gitops/control-plane/production/workflows/`). |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file found in the repository. No SLO definitions with team attribution. No per-service dashboards or alarm configurations with named owners. No team tags on any resources. Kubecost provides cost dashboards but with no ownership attribution. |
| **Gap** | No observability ownership structure. It's unclear who is responsible for monitoring the platform's health, responding to alerts (which don't exist), or maintaining observability assets. For a multi-tenant SaaS platform, ownership of per-tenant monitoring is critical. |
| **Recommendation** | (1) Add a CODEOWNERS file that maps `gitops/infrastructure/` to the platform team and `gitops/application-plane/` to the application team. (2) Define dashboard ownership tags in Prometheus/Grafana. (3) Assign named owners to critical alarms (when created per OPS-Q4). (4) Add team tags to Terraform resources for ownership attribution. |
| **Evidence** | No CODEOWNERS file found. No team attribution in any configuration file. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Tags are minimal and inconsistent: `Blueprint = var.name` in `terraform/workshop/main.tf` locals (applied via `tags = local.tags` to VPC and EKS), `Name` tags on Gitea EC2, Karpenter nodes, and ECR repositories, `karpenter.sh/discovery` for subnet/SG auto-discovery, `Name = var.tenant_id` on per-tenant SQS and DynamoDB resources. No `default_tags` block in the AWS provider configuration (`terraform/workshop/providers.tf`). No `required-tags` AWS Config rules. No cost allocation tags. No environment, team, or application tags. |
| **Gap** | No tagging governance. Cannot attribute costs per tenant tier (basic/advanced/premium), per platform component, or per team. No tag enforcement mechanism. The `Blueprint` tag provides minimal identification but is not sufficient for FinOps, ownership, or environment management. |
| **Recommendation** | (1) Add `default_tags` to the AWS provider in `providers.tf` with: `Environment`, `Project`, `Team`, `ManagedBy=terraform`. (2) Add per-tenant tags: `TenantId`, `TenantTier`. (3) Add AWS Config rule `required-tags` to enforce the tagging standard. (4) Activate cost allocation tags in AWS Billing. (5) Add tags to all Karpenter-provisioned nodes via EC2NodeClass `tags` (currently only `Name: karpenter-node`). |
| **Evidence** | `terraform/workshop/main.tf` (locals.tags = { Blueprint = var.name }), `terraform/workshop/providers.tf` (no default_tags), `terraform/modules/tenant-apps/main.tf` (Name = var.tenant_id only), `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` (tags: Name: karpenter-node only) |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

| Resource | Link |
|----------|------|
| Move to Modern DevOps Learning Plan | [AWS SkillBuilder](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) |
| Getting Started with DevOps on AWS | [AWS SkillBuilder](https://skillbuilder.aws/learn/R4B13K95YQ) |
| Flux CD Documentation | [fluxcd.io](https://fluxcd.io/docs/) |
| Flagger Progressive Delivery | [flagger.app](https://flagger.app/) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `terraform/workshop/main.tf` | INF-Q1, INF-Q5, INF-Q7, INF-Q8, INF-Q9, INF-Q10, SEC-Q1, SEC-Q4, SEC-Q5, OPS-Q9 | VPC, EKS cluster, managed node groups, Gitea module, SSM parameter, local tags |
| `terraform/workshop/saas_gitops.tf` | INF-Q10 | GitOps SaaS infra module, Flux CD module, ConfigMaps |
| `terraform/workshop/variables.tf` | INF-Q1 | Cluster version 1.32, VPC CIDR |
| `terraform/workshop/providers.tf` | OPS-Q9 | AWS provider — no default_tags |
| `terraform/workshop/versions.tf` | INF-Q10 | Provider version constraints |
| `terraform/modules/gitops-saas-infra/main.tf` | INF-Q1, INF-Q3, INF-Q4, INF-Q10, SEC-Q2, SEC-Q4, SEC-Q6, SEC-Q7 | Karpenter IRSA, Argo Workflows IRSA, SQS queues, S3 buckets, LB Controller IRSA, TF Controller IRSA |
| `terraform/modules/gitops-saas-infra/apps_needs.tf` | INF-Q10, SEC-Q2, SEC-Q7 | ECR repositories with scan_on_push, S3 code artifacts, AES256 encryption |
| `terraform/modules/gitea/main.tf` | INF-Q1, INF-Q5, SEC-Q2, SEC-Q6 | Gitea EC2 instance, security group, AMI (AL2), EBS encryption |
| `terraform/modules/gitea/userdata.sh` | INF-Q11, SEC-Q5 | Gitea setup, Gitea Actions runner, token generation/SSM storage |
| `terraform/modules/tenant-apps/main.tf` | INF-Q2, INF-Q4, INF-Q8, DATA-Q3, OPS-Q9 | DynamoDB tables with PITR, per-tenant SQS queues, IRSA roles |
| `terraform/modules/flux_cd/main.tf` | INF-Q10, INF-Q11, SEC-Q5 | Flux operator Helm release, FluxInstance CRD, kubernetes_secret |
| `gitops/clusters/production/infrastructure.yaml` | INF-Q10, OPS-Q5 | Flux Kustomization for infrastructure layer |
| `gitops/infrastructure/production/01-metric-server.yaml` | INF-Q7 | Metrics server HelmRelease (enables HPA) |
| `gitops/infrastructure/production/02-karpenter.yaml` | INF-Q1, INF-Q7 | Karpenter HelmRelease v1.4.0 |
| `gitops/infrastructure/production/03-argo-workflows.yaml` | INF-Q3, INF-Q5, SEC-Q3 | Argo Workflows HelmRelease, --auth-mode=server, internet-facing LB, full-permissions ClusterRole |
| `gitops/infrastructure/production/04-lb-controller.yaml` | INF-Q6 | AWS LB Controller HelmRelease v1.6.2 |
| `gitops/infrastructure/production/05-kubecost.yaml` | OPS-Q2, OPS-Q3 | Kubecost HelmRelease v2.1.0, Prometheus config |
| `gitops/infrastructure/production/06-argo-events.yaml` | INF-Q3 | Argo Events HelmRelease v2.4.3 |
| `gitops/infrastructure/production/07-tf-controller.yaml` | INF-Q10 | TF Controller HelmRelease v0.16.0-rc.4 |
| `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` | INF-Q1, INF-Q7, INF-Q9, SEC-Q6, OPS-Q9 | Karpenter NodePool (default), EC2NodeClass (al2023@latest), consolidation policy |
| `gitops/infrastructure/production/dependencies/02-application-karpenter-config.yaml` | INF-Q7 | Application NodePool with taints |
| `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | INF-Q3, INF-Q4, SEC-Q5 | SQS EventSource and Sensor for tenant onboarding, GIT_TOKEN parameter |
| `gitops/control-plane/production/workflows/tenant-deployment-sensor.yaml` | INF-Q3, OPS-Q5 | SQS EventSource and Sensor for tenant deployment |
| `gitops/control-plane/production/workflows/tenant-offboarding-sensor.yaml` | INF-Q3 | SQS EventSource and Sensor for tenant offboarding |
| `gitops/control-plane/production/workflows/event-bus.yaml` | INF-Q9 | Argo Events EventBus (NATS, 3 replicas) |
| `gitops/application-plane/production/tier-templates/premium_tenant_template.yaml` | OPS-Q5 | Premium tier template — silo deployment, no canary |
| `gitops/application-plane/production/tier-templates/basic_tenant_template.yaml` | OPS-Q5 | Basic tier template — pooled deployment |
| `gitops/infrastructure/base/sources/consumer-image-automation.yaml` | OPS-Q5 | Flux ImageUpdateAutomation for consumer |
| `helm-charts/helm-tenant-chart/templates/deployment.yaml` | INF-Q7 | Tenant deployment template with replica count |
| `helm-charts/helm-tenant-chart/templates/hpa.yaml` | INF-Q7 | HPA template (disabled by default) |
| `helm-charts/helm-tenant-chart/templates/ingress.yaml` | INF-Q6 | ALB ingress with tenant header routing |
| `helm-charts/helm-tenant-chart/values.yaml.template` | INF-Q7 | Default values — autoscaling.enabled=false |
| `helm-charts/application-chart/templates/tests/test-connection.yaml` | OPS-Q6 | Basic Helm test (wget only) |
| `helm-charts/application-chart/values.yaml` | INF-Q7 | Application chart defaults — autoscaling disabled |
| `tenant-microservices/producer/.gitea/workflows/build-and-push.yml` | INF-Q11, SEC-Q7 | Gitea Actions workflow — build and push, no security scanning |
| `README.md` | Quick Agent Wins | Architecture documentation, deployment steps, multi-tenant patterns |
