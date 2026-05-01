# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | microservices-demo |
| **Date** | 2026-04-15 |
| **Repo Type** | infrastructure-only |
| **Priority** | — |
| **Tags** | kubernetes, helm, terraform, istio, cicd, iac |
| **Context** | Root-level deployment and infrastructure configuration — Kubernetes manifests, Helm charts, Kustomize overlays, Terraform IaC, Istio service mesh configs, Skaffold/Cloud Build CI/CD pipelines, and shared protobuf definitions. |
| **Preferences** | Prefer: EKS, DynamoDB, Bedrock, Terraform, GitOps · Avoid: Serverless, Manual Deployments |
| **Overall Score** | **1.74 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.09 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | N/A | N/A — all questions not applicable for infrastructure-only |
| Data Platform Modernization (DATA) | 2.00 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **1.74 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q5: Secrets Management | 1 | No secrets management — Redis and service addresses hardcoded in manifests; Memorystore connection string injected via sed. | Hardcoded credentials are a critical security vulnerability and block secure migration to managed services. |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or GCP Cloud Audit Logging configuration in Terraform or Kubernetes manifests. | Compliance and forensic analysis impossible without immutable audit trails. |
| 3 | SEC-Q2: Encryption at Rest | 1 | No KMS or CMEK configuration for any data store. Redis data on emptyDir is unencrypted and ephemeral. | Data at rest is unprotected; blocks compliance requirements for production workloads. |
| 4 | INF-Q8: Backup and Recovery | 1 | Redis uses emptyDir volume — data lost on pod restart. No backup configuration for any data store. | Data loss risk is high; no recovery path exists for cart data. Directly impacts Move to Managed Databases pathway. |
| 5 | INF-Q2: Managed Databases | 2 | Default deployment uses in-cluster Redis with emptyDir (self-managed, no persistence). Memorystore option exists but is disabled by default. | Self-managed Redis introduces operational burden and is a single point of failure. Triggers Move to Managed Databases pathway. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). CI/CD pipeline exists with 7 GitHub Actions workflows, Cloud Build, and Skaffold.
- **What it enables:** An agent that triggers deployments via Skaffold/Cloud Build, checks build status across PR and main CI pipelines, manages GKE cluster lifecycle, and validates Helm/Kustomize/Terraform changes before merge.
- **Additional steps:** Expose CI/CD pipeline status via GitHub API; create a structured interface for deployment triggers (e.g., GitHub Actions workflow dispatch).
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — `README.md` (comprehensive quickstart and architecture docs), `docs/development-guide.md`, `docs/purpose.md`, `docs/adding-new-microservice.md`, `docs/cloudshell-tutorial.md`, `protos/demo.proto` (gRPC API definitions for all 11 services).
- **What it enables:** A RAG-based knowledge agent using Amazon Bedrock that indexes the repository's documentation and protobuf definitions to answer developer questions about the architecture, deployment procedures, service APIs, and Kustomize component configuration.
- **Additional steps:** Index all Markdown docs and protobuf files; generate embeddings using Amazon Bedrock. Consider adding OpenAPI specs generated from the protobuf definitions for richer API knowledge.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 2 (≥ 2). OpenTelemetry Collector infrastructure exists as a Kustomize component (`kustomize/components/google-cloud-operations/`) with tracing support for 8 of 11 services. Helm chart supports `opentelemetryCollector.create` and `googleCloudOperations.tracing`.
- **What it enables:** An agent that queries distributed traces (once OTel is enabled), correlates service-to-service latency across the gRPC service mesh, and suggests root causes for degradation.
- **Additional steps:** Enable the google-cloud-operations Kustomize component by uncommenting it in `kustomize/kustomization.yaml`. Alternatively, set `opentelemetryCollector.create: true` and `googleCloudOperations.tracing: true` in Helm values.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 2 | Move to Containers | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 is N/A for infrastructure-only. No commercial database engines detected — Redis is open source. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 — default deployment uses self-managed in-cluster Redis with emptyDir. |
| 5 | Move to Managed Analytics | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3 — IaC coverage and CI/CD automation both meet threshold. |
| 7 | Move to AI | Not Applicable | — | — | This is a `infrastructure-only` repository. This pathway does not apply. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current Database Topology

The default deployment uses an **in-cluster Redis** instance (`redis-cart`) deployed as a single-replica Kubernetes Deployment using the `redis:alpine` image with an **emptyDir volume** (`kubernetes-manifests/cartservice.yaml`). This means:

- **Self-managed**: No automated patching, no managed backups, no automatic failover.
- **No persistence**: Data is lost on every pod restart (emptyDir is ephemeral).
- **Single point of failure**: Single replica with no replication.
- **No encryption**: Data in emptyDir is not encrypted at rest.

An optional **Google Memorystore Redis** managed instance is defined in `terraform/memorystore.tf` with `redis_version = "REDIS_7_0"`, but it is **disabled by default** (`memorystore = false` in `terraform/terraform.tfvars`).

#### Engine Versions and EOL Status

- **Memorystore**: `REDIS_7_0` pinned in Terraform — current and supported.
- **In-cluster Redis**: `redis:alpine` without version pinning — defaults to latest, which is a version management risk.

#### Recommended Managed Database Targets

Per stated preferences (prefer EKS, DynamoDB, Terraform):

1. **Amazon ElastiCache for Redis (Valkey)** — Direct replacement for the in-cluster Redis. Provides automatic failover, Multi-AZ replication, automated backups, encryption at rest and in transit, and managed patching. Define using Terraform `aws_elasticache_replication_group` resource.

2. **Amazon DynamoDB** (preferred) — Consider migrating the cart service's key-value data model from Redis to DynamoDB for a fully serverless, zero-ops data store with built-in Multi-AZ, automatic backups, encryption, and pay-per-request pricing. The cart data model (`user_id → CartItem[]`) maps naturally to a DynamoDB table with `user_id` as the partition key.

3. **Amazon MemoryDB for Redis** — If sub-millisecond latency with durability is required, MemoryDB provides Redis-compatible API with Multi-AZ durability and microsecond read latency.

#### Migration Approach

1. **Define managed database in Terraform** (aligned with IaC-first preference):
   - Create `aws_elasticache_replication_group` or `aws_dynamodb_table` resources
   - Configure Multi-AZ, encryption, automated backups
   - Use Terraform outputs to provide connection endpoints

2. **Update Kubernetes manifests**:
   - Replace the `redis-cart` Deployment and Service with a Kubernetes ExternalName Service or update `REDIS_ADDR` env var to point to the managed endpoint
   - Leverage the existing Kustomize memorystore component pattern (`kustomize/components/memorystore/`) as a template for the AWS managed database component

3. **Implement secrets management**:
   - Store database credentials in AWS Secrets Manager
   - Inject via Kubernetes External Secrets Operator or CSI Secrets Store Driver

#### Representative AWS Services

- Amazon ElastiCache for Redis (Valkey)
- Amazon DynamoDB
- Amazon MemoryDB for Redis
- AWS Database Migration Service (DMS)

#### References

- [AWS Database Migration Guide](https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html)
- [ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | `terraform/main.tf` defines a GKE Autopilot cluster (`google_container_cluster` with `enable_autopilot = true`). GKE Autopilot is fully managed container orchestration — Google manages the control plane, node pools, scaling, and node patching. All 11 application services are deployed as Kubernetes Deployments. `.github/terraform/main.tf` defines a second GKE Autopilot cluster (`prs-gke-cluster`) for PR staging. No raw VMs or EC2 instances are used. |
| **Gap** | 100% of compute is managed container orchestration (GKE Autopilot), which is excellent. Minor gap: the infrastructure is GCP-native. For AWS migration per preferences, equivalent would be EKS with managed node groups or Fargate. No explicit per-service resource tuning beyond pod requests/limits. |
| **Recommendation** | When migrating to AWS, adopt EKS with managed node groups (per EKS preference) or EKS with Fargate profiles for workloads that benefit from pod-level isolation. Use Terraform (per preference) to define `aws_eks_cluster` and `aws_eks_node_group` resources. Consider Karpenter for node auto-provisioning as the EKS equivalent of GKE Autopilot's auto-provisioning. |
| **Evidence** | `terraform/main.tf` (line: `enable_autopilot = true`), `.github/terraform/main.tf` (`enable_autopilot = true`), `kubernetes-manifests/*.yaml` (11 service Deployments) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The default deployment uses an in-cluster Redis (`redis-cart`) deployed via `kubernetes-manifests/cartservice.yaml` with `image: redis:alpine` and `emptyDir: {}` volume — this is self-managed with no persistence. An optional Google Memorystore Redis managed instance is defined in `terraform/memorystore.tf` (`google_redis_instance` with `redis_version = "REDIS_7_0"`), but it is conditionally created (`count = var.memorystore ? 1 : 0`) and **disabled by default** (`memorystore = false` in `terraform/terraform.tfvars`). The `kustomize/components/memorystore/` component patches the cartservice to use the managed instance when enabled. |
| **Gap** | The default deployment is self-managed Redis with no persistence, no backups, and no failover — significant operational risk. The managed option exists but is opt-in and disabled. |
| **Recommendation** | Enable managed database by default. For AWS migration, replace in-cluster Redis with Amazon ElastiCache for Redis (Valkey) or Amazon DynamoDB (per preference). Define using Terraform with Multi-AZ, automated backups, and encryption. Use the existing memorystore Kustomize component pattern as a template. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (redis-cart Deployment with emptyDir), `terraform/memorystore.tf` (Memorystore resource), `terraform/terraform.tfvars` (`memorystore = false`), `kustomize/components/memorystore/kustomization.yaml` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service found. Searched for Step Functions, Temporal, Camunda, Airflow, and GCP Workflows — none present in Terraform, Kubernetes manifests, Helm chart, or Kustomize components. The checkout flow (cart → payment → shipping → email) is orchestrated in application code (inferred from `protos/demo.proto` `CheckoutService.PlaceOrder` RPC and `kubernetes-manifests/checkoutservice.yaml` env vars referencing multiple downstream services). |
| **Gap** | All workflow logic is hardcoded in application code with no dedicated orchestration service. Error handling, retry logic, and state management are embedded in service implementations. |
| **Recommendation** | For AWS migration, adopt AWS Step Functions (per Terraform preference, define using `aws_sfn_state_machine`) to orchestrate the checkout flow. This provides visual workflow management, built-in retry/error handling, and state persistence. Define workflow definitions as IaC alongside existing Terraform. |
| **Evidence** | `protos/demo.proto` (CheckoutService definition), `kubernetes-manifests/checkoutservice.yaml` (env vars: PRODUCT_CATALOG_SERVICE_ADDR, SHIPPING_SERVICE_ADDR, PAYMENT_SERVICE_ADDR, EMAIL_SERVICE_ADDR, CURRENCY_SERVICE_ADDR, CART_SERVICE_ADDR) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure found. Searched for SQS, SNS, EventBridge, Kafka, RabbitMQ, GCP Pub/Sub, Kinesis — none present in any Terraform, Kubernetes, Helm, or Kustomize configuration. All inter-service communication is synchronous gRPC as defined in `protos/demo.proto` (9 gRPC services with request-response patterns). |
| **Gap** | All communication is synchronous gRPC with no async patterns. No messaging infrastructure for decoupled communication, event-driven patterns, or data streaming. |
| **Recommendation** | For AWS migration, introduce Amazon SQS for task queuing (e.g., order confirmation emails) and Amazon EventBridge for event-driven patterns (e.g., order placed → email notification). Define using Terraform. Start with the email notification flow — the `EmailService.SendOrderConfirmation` RPC is a natural candidate for async processing. |
| **Evidence** | `protos/demo.proto` (all 9 gRPC service definitions are synchronous request-response), absence of any messaging resources in `terraform/`, `kubernetes-manifests/`, `helm-chart/`, `kustomize/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Fine-grained Kubernetes NetworkPolicies exist as a Kustomize component (`kustomize/components/network-policies/`) with a deny-all baseline policy and per-service ingress/egress rules for all 13 workloads. The Helm chart supports `networkPolicies.create` and `authorizationPolicies.create` (Istio). Istio service mesh config includes `ServiceEntry` for egress control (`istio-manifests/allow-egress-googleapis.yaml`). However, **network policies are NOT enabled by default** — they are commented out in both `kustomize/kustomization.yaml` and `kubernetes-manifests/kustomization.yaml`. The Helm chart defaults are `networkPolicies.create: false` and `authorizationPolicies.create: false`. |
| **Gap** | Network policies are fully defined but not enabled by default. The default deployment has no network segmentation — all pods can communicate freely. Istio egress control is only active when the service-mesh-istio component is enabled. |
| **Recommendation** | Enable network policies by default by uncommenting the `network-policies` component in `kustomize/kustomization.yaml` and setting `networkPolicies.create: true` in Helm values. For AWS migration on EKS, use Calico or VPC CNI network policies. Enable Istio AuthorizationPolicies for service-level mTLS and RBAC. |
| **Evidence** | `kustomize/components/network-policies/kustomization.yaml` (13 NetworkPolicy resources), `kustomize/components/network-policies/network-policy-deny-all.yaml`, `helm-chart/values.yaml` (`networkPolicies.create: false`, `authorizationPolicies.create: false`), `kustomize/kustomization.yaml` (network-policies commented out), `istio-manifests/allow-egress-googleapis.yaml` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Two ingress paths exist: (1) `kubernetes-manifests/frontend.yaml` defines `frontend-external` as a `type: LoadBalancer` service exposing port 80 directly to the internet. (2) `istio-manifests/frontend-gateway.yaml` defines an Istio Gateway + VirtualService for frontend ingress, accepting all hosts (`"*"`) on port 80 (HTTP only). The Helm chart supports VirtualService creation (`frontend.virtualService.create: false` default). |
| **Gap** | Load balancer present but minimal configuration — no authentication, no throttling, no request validation, no TLS termination, no WAF. The Istio Gateway accepts all hosts on HTTP with no security controls. |
| **Recommendation** | For AWS migration, deploy an Application Load Balancer (ALB) with AWS WAF, or use Amazon API Gateway for API-level throttling, authentication, and request validation. Configure TLS termination at the load balancer. Use the AWS Load Balancer Controller on EKS to automatically provision ALBs from Kubernetes Ingress resources. Define using Terraform. |
| **Evidence** | `kubernetes-manifests/frontend.yaml` (`frontend-external` LoadBalancer), `istio-manifests/frontend-gateway.yaml` (Gateway accepting `"*"` on HTTP/80), `helm-chart/values.yaml` (`frontend.virtualService.create: false`) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GKE Autopilot automatically manages node auto-scaling based on pod resource requests. All 11 service Deployments define resource requests and limits (e.g., `cpu: 200m, memory: 64Mi` for cartservice). Node-level scaling is fully automated. However, no Horizontal Pod Autoscaler (HPA) or custom autoscaling policies are defined for individual services — pod-level scaling relies on manual replica count management. |
| **Gap** | Node-level auto-scaling is handled by GKE Autopilot, but pod-level auto-scaling (HPA) is not configured. Individual services cannot scale horizontally in response to traffic without manual intervention. |
| **Recommendation** | Add HPA configurations for traffic-sensitive services (frontend, checkoutservice, productcatalogservice). For AWS migration on EKS, use Karpenter for node auto-provisioning and define HPA resources targeting CPU/memory utilization or custom metrics. Define HPA resources in the Kustomize base or Helm chart. |
| **Evidence** | `terraform/main.tf` (`enable_autopilot = true`), `kubernetes-manifests/cartservice.yaml` (resource requests/limits defined), absence of HPA resources in `kubernetes-manifests/`, `helm-chart/templates/`, `kustomize/` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The in-cluster Redis (`redis-cart`) uses `emptyDir: {}` volume — all data is lost when the pod restarts. No backup configuration exists for any data store. No `aws_backup_plan`, no GCP backup config, no persistent volume claims, no Redis RDB/AOF persistence. The optional Memorystore instance (`terraform/memorystore.tf`) would provide managed backups if enabled, but it defaults to disabled. |
| **Gap** | No backup or recovery capability for any data store. Cart data is ephemeral and non-recoverable. No restore procedures documented. |
| **Recommendation** | For AWS migration: use Amazon ElastiCache with automatic backups and point-in-time recovery enabled, or DynamoDB with continuous backups (PITR). Define backup retention using Terraform `aws_elasticache_replication_group` with `snapshot_retention_limit` or DynamoDB `point_in_time_recovery`. Create an AWS Backup plan for comprehensive backup governance. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (`volumes: - name: redis-data, emptyDir: {}`), `terraform/memorystore.tf` (managed option disabled), `terraform/terraform.tfvars` (`memorystore = false`) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot with `location = var.region` (default `us-central1`) is a regional cluster that automatically distributes pods across multiple availability zones. The `.github/terraform/main.tf` PR cluster (`prs-gke-cluster`) also uses `location = "us-central1"` (regional). However, `redis-cart` is a single-replica Deployment with emptyDir — it is a single point of failure with no replication, no persistence, and no multi-AZ distribution. |
| **Gap** | Compute workloads span multiple AZs via GKE Autopilot, but the data tier (Redis) is a single-replica pod with no redundancy. An AZ failure affecting the Redis pod loses all cart data with no automatic recovery. |
| **Recommendation** | For AWS migration: deploy ElastiCache for Redis with Multi-AZ and automatic failover (`aws_elasticache_replication_group` with `automatic_failover_enabled = true` and `multi_az_enabled = true`), or use DynamoDB which is natively Multi-AZ. Ensure EKS node groups span at least 2 AZs. |
| **Evidence** | `terraform/main.tf` (`location = var.region`, regional cluster), `.github/terraform/main.tf` (`location = "us-central1"`), `kubernetes-manifests/cartservice.yaml` (redis-cart: single replica, emptyDir) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive IaC coverage: Terraform defines GKE cluster, Memorystore, GCP APIs, IAM service accounts, and GCS state bucket. Kubernetes manifests (`kubernetes-manifests/`) define all 11 services + Redis. Helm chart (`helm-chart/`) provides parameterized deployment for all services. Kustomize (`kustomize/`) provides base manifests + 15 composable components. Istio manifests define service mesh ingress. CI/CD Terraform (`.github/terraform/`) defines the PR staging cluster. All infrastructure is code-defined. |
| **Gap** | Good IaC coverage (90%+) for the defined scope. Minor gaps: no IaC for monitoring/alerting resources, no IaC for secrets management, no IaC for backup policies. The Terraform state bucket is hardcoded as `"cicd-terraform-state"` rather than parameterized. |
| **Recommendation** | For AWS migration, use Terraform (per preference) for all infrastructure: EKS cluster, VPC, ElastiCache/DynamoDB, IAM roles, and monitoring. Adopt a GitOps approach (per preference) with ArgoCD on EKS managing the Kubernetes manifests, Helm charts, and Kustomize overlays. Add IaC for monitoring (CloudWatch dashboards, alarms) and secrets management (AWS Secrets Manager). |
| **Evidence** | `terraform/main.tf`, `terraform/memorystore.tf`, `.github/terraform/main.tf`, `kubernetes-manifests/*.yaml` (12 files), `helm-chart/` (Chart.yaml + 14 templates), `kustomize/` (base + 15 components), `istio-manifests/` (3 files) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD with 7 GitHub Actions workflows: (1) `ci-pr.yaml` — PR pipeline with Go unit tests, C# unit tests, GKE deployment, pod readiness checks, and smoke tests. (2) `ci-main.yaml` — Main branch pipeline with same test/deploy/smoke cycle. (3) `helm-chart-ci.yaml` — Helm lint, template validation across multiple configurations. (4) `kustomize-build-ci.yaml` — Kustomize build validation for base and test combinations. (5) `terraform-validate-ci.yaml` — Terraform init and validate. (6) `kubevious-manifests-ci.yaml` — Kubernetes manifest validation using Kubevious for manifests, Helm chart, and Kustomize. (7) `cleanup.yaml` — Automated PR namespace cleanup. Additionally, `cloudbuild.yaml` provides GCP Cloud Build deployment, and `skaffold.yaml` provides multi-platform builds with profiles (gcb, debug, network-policies). |
| **Gap** | Strong CI/CD automation with build, test, and deploy stages. Missing: automated rollback mechanism (no Argo Rollouts or equivalent), no explicit security scanning gate, no GitOps continuous reconciliation. Deploys via `skaffold run` (imperative kubectl apply) rather than GitOps pull-based deployment. |
| **Recommendation** | For AWS migration, adopt a GitOps approach (per preference) with ArgoCD or Flux CD on EKS for pull-based continuous reconciliation. Replace Skaffold/kubectl deploy with ArgoCD Application resources syncing from the Git repository. Add automated rollback via Argo Rollouts. Migrate CI to GitHub Actions (already in place) with AWS CodeBuild for container builds if needed. Avoid manual deployments (per preference) by implementing full GitOps pipeline. |
| **Evidence** | `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/kubevious-manifests-ci.yaml`, `.github/workflows/cleanup.yaml`, `cloudbuild.yaml`, `skaffold.yaml` |

### Application Architecture

_All APP questions are N/A for this `infrastructure-only` repository. See findings below._

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
| **Score** | 2 |
| **Finding** | `terraform/memorystore.tf` pins `redis_version = "REDIS_7_0"` for the optional Memorystore instance — Redis 7.0 is current and supported. However, `kubernetes-manifests/cartservice.yaml` uses `image: redis:alpine` without an explicit version pin — this defaults to the latest redis:alpine image, which is a version management risk (unpredictable version drift, potential breaking changes). The Helm chart (`helm-chart/values.yaml`) sets `cartDatabase.inClusterRedis.publicRepository: true` and uses the `redis:alpine` image reference without version pinning. |
| **Gap** | Mixed version management: Terraform Memorystore is properly pinned, but the default in-cluster Redis image tag is unpinned. No mechanism to track when new Redis versions introduce breaking changes. The `kubevious-manifests-ci.yaml` workflow explicitly skips the `container-latest-image` rule for kubernetes-manifests validation. |
| **Recommendation** | Pin the Redis image version explicitly (e.g., `redis:7.2-alpine`) in `kubernetes-manifests/cartservice.yaml` and `kustomize/base/cartservice.yaml`. Use Renovate (already configured in `.github/renovate.json5`) to automate version updates with PR-based review. For AWS migration, use ElastiCache or DynamoDB where engine versions are managed by AWS. |
| **Evidence** | `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`), `kubernetes-manifests/cartservice.yaml` (`image: redis:alpine`), `helm-chart/values.yaml` (`cartDatabase.inClusterRedis.publicRepository: true`), `.github/workflows/kubevious-manifests-ci.yaml` (`skip_rules: container-latest-image`) |

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
| **Finding** | No audit logging configuration found. No `aws_cloudtrail` resources. No GCP Cloud Audit Logging configuration in Terraform. The `.github/terraform/main.tf` provisions a GCS bucket for Terraform state with versioning but no audit logging enabled on the bucket. No Kubernetes audit policy configuration. No CloudWatch log retention policies. |
| **Gap** | No audit logging exists for any component — infrastructure changes, API access, and Kubernetes API calls are not recorded in an immutable audit trail. |
| **Recommendation** | For AWS migration: enable AWS CloudTrail with log file validation and S3 Object Lock for immutable storage. Define using Terraform (`aws_cloudtrail`). Enable EKS control plane logging for API server, audit, and authenticator logs. Configure CloudWatch log retention for all services. |
| **Evidence** | `terraform/main.tf` (no audit logging), `.github/terraform/main.tf` (GCS bucket without audit logging), absence of any audit/logging resources in all Terraform files |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration found. No KMS key references in any Terraform or Kubernetes manifests. The Redis data is stored in emptyDir volume (no encryption). The GCS bucket for Terraform state (`.github/terraform/main.tf`) does not configure customer-managed encryption keys (CMEK). No `kms_key_id` on any resource. |
| **Gap** | No data store has encryption at rest configured. Redis data in emptyDir is unencrypted. Terraform state (which may contain sensitive values) is stored in a GCS bucket without CMEK. |
| **Recommendation** | For AWS migration: enable encryption at rest on all data stores using AWS KMS customer-managed keys. Configure EBS encryption by default, ElastiCache encryption at rest, S3 bucket encryption for Terraform state, and EKS secrets encryption. Define KMS keys using Terraform. |
| **Evidence** | `terraform/main.tf` (no encryption config), `.github/terraform/main.tf` (`google_storage_bucket` without CMEK), `kubernetes-manifests/cartservice.yaml` (emptyDir — no encryption), absence of any KMS/encryption resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication configured. The `frontend-external` LoadBalancer service (`kubernetes-manifests/frontend.yaml`) exposes port 80 directly with no auth. The Istio Gateway (`istio-manifests/frontend-gateway.yaml`) accepts all hosts (`"*"`) on HTTP with no authentication or authorization configuration. The Helm chart supports `authorizationPolicies.create` (Istio AuthorizationPolicies) but defaults to `false`. No OAuth2, JWT, API key, or Cognito configuration found. |
| **Gap** | All API endpoints are unauthenticated and open to the internet. No authentication middleware, no authorization policies enabled, no identity verification on any request. |
| **Recommendation** | For AWS migration: deploy Amazon API Gateway with Cognito authorizers or Lambda authorizers for JWT validation. Alternatively, use an ALB with OIDC authentication integration. Enable Istio AuthorizationPolicies (set `authorizationPolicies.create: true`) for internal service-to-service mTLS authentication. |
| **Evidence** | `kubernetes-manifests/frontend.yaml` (`frontend-external` LoadBalancer, no auth), `istio-manifests/frontend-gateway.yaml` (hosts: `"*"`, no auth), `helm-chart/values.yaml` (`authorizationPolicies.create: false`) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration found. No Cognito, Okta, Ping, OIDC, SAML, or SSO configuration in any Terraform, Kubernetes, or Helm files. The application's README states it "does not require signup/login and generates session IDs for all users automatically" — no identity system exists. |
| **Gap** | No identity provider integration exists. The application has no authentication system at all — all users are anonymous with auto-generated session IDs. |
| **Recommendation** | For AWS migration: integrate Amazon Cognito for user authentication and SSO. Define Cognito user pool and identity pool using Terraform. This is a lower priority for a demo/reference application but critical for any production deployment. |
| **Evidence** | `README.md` ("Does not require signup/login and generates session IDs for all users automatically"), absence of any IdP configuration in all files |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No secrets management system in use. `REDIS_ADDR` is hardcoded as `"redis-cart:6379"` in `kubernetes-manifests/cartservice.yaml` and `helm-chart/values.yaml` (`cartDatabase.connectionString: "redis-cart:6379"`). All inter-service addresses are hardcoded as environment variables in Kubernetes manifests (e.g., `PRODUCT_CATALOG_SERVICE_ADDR: "productcatalogservice:3550"`). The Memorystore connection string is injected via `sed` command in `terraform/memorystore.tf` — not through a secrets management system. No AWS Secrets Manager, HashiCorp Vault, Kubernetes Sealed Secrets, or External Secrets Operator. The `gcp_project_id` in `terraform/terraform.tfvars` is a placeholder (`"<project_id_here>"`). |
| **Gap** | All connection strings and service addresses are hardcoded in manifests. No secrets rotation. No secrets encryption beyond Kubernetes' base64 encoding. The Memorystore connection string injection via `sed` is fragile and not auditable. |
| **Recommendation** | For AWS migration: use AWS Secrets Manager for database credentials and sensitive configuration. Deploy the Kubernetes External Secrets Operator or CSI Secrets Store Driver on EKS to inject secrets from AWS Secrets Manager into pods. Define secrets using Terraform. Enable automatic rotation for database credentials. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (`REDIS_ADDR: "redis-cart:6379"`), `kubernetes-manifests/frontend.yaml` (hardcoded service addresses), `helm-chart/values.yaml` (`cartDatabase.connectionString: "redis-cart:6379"`), `terraform/memorystore.tf` (sed-based connection string injection), `terraform/terraform.tfvars` (placeholder project ID) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Excellent container hardening across all services. Every Deployment in `kubernetes-manifests/` configures: `runAsNonRoot: true`, `runAsUser: 1000`, `runAsGroup: 1000`, `fsGroup: 1000`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `privileged: false`, `readOnlyRootFilesystem: true`. The Helm chart supports `seccompProfile.enable` (RuntimeDefault) as an additional hardening option. Renovate (`.github/renovate.json5`) is configured for automated dependency updates on a weekly schedule (earlyMondays). GKE Autopilot manages node OS patching automatically. |
| **Gap** | Strong container hardening. Seccomp profile is available but not enabled by default (`seccompProfile.enable: false`). No explicit vulnerability scanning (no AWS Inspector, Snyk, or Trivy). No hardened base image enforcement (images are defined by names only — actual Dockerfiles are in `src/`, outside this repo's scope). |
| **Recommendation** | Enable seccomp profiles by default (`seccompProfile.enable: true` in Helm values). For AWS migration on EKS: use Bottlerocket or AL2023 managed node AMIs for hardened node OS. Add container image scanning via Amazon ECR image scanning or Trivy in CI/CD. Define pod security standards using EKS Pod Security Standards (PSS). |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (securityContext), `kubernetes-manifests/adservice.yaml` (securityContext), `kubernetes-manifests/frontend.yaml` (securityContext), `helm-chart/values.yaml` (`securityContext.enable: true`, `seccompProfile.enable: false`), `.github/renovate.json5` (automated dependency updates) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubevious manifest validation in CI (`.github/workflows/kubevious-manifests-ci.yaml`) validates Kubernetes manifests, Helm chart, and Kustomize for structural correctness. Renovate (`.github/renovate.json5`) automates dependency updates with PR-based review. However, no SAST tools (SonarQube, Semgrep, CodeGuru), no container image scanning (Trivy, Snyk, ECR scanning), no dependency vulnerability scanning (`npm audit`, `pip-audit`, `dotnet list package --vulnerable`) in any CI pipeline. No security gates blocking on critical findings. |
| **Gap** | Manifest validation and dependency updates exist, but no application security scanning (SAST), container scanning, or dependency vulnerability scanning is integrated into the CI/CD pipeline. |
| **Recommendation** | Add Trivy or Snyk container image scanning to the CI/CD pipeline (GitHub Actions step after `skaffold build`). Add `npm audit`, `pip-audit`, and `dotnet list package --vulnerable` to the code-tests job. Consider adding Semgrep or SonarQube for SAST. Add Amazon ECR image scanning when migrating container registry to AWS. Define security gates that block PRs with critical/high vulnerabilities. |
| **Evidence** | `.github/workflows/kubevious-manifests-ci.yaml` (Kubevious validation), `.github/renovate.json5` (dependency updates), `.github/workflows/ci-pr.yaml` (no security scanning steps), `.github/workflows/ci-main.yaml` (no security scanning steps) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | OpenTelemetry Collector infrastructure exists as an opt-in Kustomize component (`kustomize/components/google-cloud-operations/`). When enabled, it deploys an OTel Collector with OTLP receiver and Google Cloud exporter, and patches 8 services (checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice) with `ENABLE_TRACING=1`, `COLLECTOR_SERVICE_ADDR`, and `OTEL_SERVICE_NAME` environment variables. The Helm chart supports `opentelemetryCollector.create` and `googleCloudOperations.tracing`. However, **tracing is NOT enabled by default** — the component is commented out in `kustomize/kustomization.yaml`, and Helm defaults are `opentelemetryCollector.create: false` and `googleCloudOperations.tracing: false`. |
| **Gap** | Tracing infrastructure exists but is not enabled by default. The default deployment has no distributed tracing. When enabled, it covers 8 of 11 services (adservice, cartservice, and loadgenerator are not patched). No cross-service trace propagation configuration visible in infrastructure definitions. |
| **Recommendation** | Enable OTel tracing by default. For AWS migration: deploy the AWS Distro for OpenTelemetry (ADOT) Collector on EKS. Configure the OTel Collector to export traces to AWS X-Ray. Use the Kustomize component pattern (already established) to create an AWS-specific observability component. Ensure all services have trace ID propagation configured. |
| **Evidence** | `kustomize/components/google-cloud-operations/kustomization.yaml` (tracing patches for 8 services), `kustomize/components/google-cloud-operations/otel-collector.yaml` (OTel Collector deployment), `helm-chart/values.yaml` (`opentelemetryCollector.create: false`, `googleCloudOperations.tracing: false`), `kustomize/kustomization.yaml` (google-cloud-operations commented out) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in any configuration file. No error budget tracking. No GCP Monitoring SLO configs. No CloudWatch SLO configs. No Prometheus recording rules for SLI metrics. No SLO-related configuration in Terraform, Kubernetes manifests, Helm chart, or Kustomize components. |
| **Gap** | No formal SLO definitions exist. No measurable service level targets for availability, latency, or error rates. No error budget tracking. |
| **Recommendation** | Define SLOs for critical user journeys (e.g., homepage load latency p99 < 500ms, checkout success rate > 99.5%). For AWS migration: define SLOs using CloudWatch Synthetics and Service Level Objectives. Create CloudWatch dashboards tracking SLIs. Define SLO configuration as code alongside existing IaC. |
| **Evidence** | Absence of SLO definitions in `terraform/`, `kubernetes-manifests/`, `helm-chart/`, `kustomize/` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics publishing found. No CloudWatch `putMetric` calls, no GCP custom metrics, no Prometheus custom metrics exporters. The infrastructure defines only basic container resource requests/limits. No business KPI dashboards or alarms. |
| **Gap** | No business outcome metrics are tracked. Infrastructure metrics (CPU, memory) may be available via GKE, but no business metrics (conversion rates, cart abandonment, order processing time) are instrumented. |
| **Recommendation** | Define business metric collection as part of the observability stack. For AWS migration: use CloudWatch custom metrics for business events (orders placed, cart additions, payment failures). Create CloudWatch dashboards tracking business KPIs alongside infrastructure metrics. Instrument via the OTel Collector metrics pipeline (already partially defined in the google-cloud-operations component). |
| **Evidence** | Absence of custom metric definitions in `kubernetes-manifests/`, `helm-chart/`, `kustomize/components/google-cloud-operations/` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found. No CloudWatch alarms, no GCP Monitoring alert policies, no PagerDuty or OpsGenie integration, no Prometheus AlertManager rules. No alerting configuration in any Terraform, Kubernetes, Helm, or Kustomize file. |
| **Gap** | No alerting exists. Failures and degradation can only be detected through manual observation or loadgenerator smoke test failures. |
| **Recommendation** | For AWS migration: define CloudWatch alarms for critical metrics (error rate, latency p99, pod restart count) using Terraform. Enable CloudWatch anomaly detection on key metrics. Integrate with Amazon SNS for alert notifications. Define alerting as IaC alongside existing Terraform infrastructure definitions. |
| **Evidence** | Absence of alerting configuration in all files |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployment uses `skaffold run` which performs `kubectl apply` — this triggers Kubernetes' default rolling update strategy. The PR CI pipeline (`.github/workflows/ci-pr.yaml`) deploys to a dedicated PR namespace, waits for pod readiness, and runs smoke tests. The main CI pipeline (`.github/workflows/ci-main.yaml`) follows the same pattern. Health checks (readiness and liveness probes) are defined on all services. However, no canary, blue/green, or traffic shifting is configured. No Argo Rollouts, Flagger, or CodeDeploy. |
| **Gap** | Rolling deployment with health checks and smoke tests, but no staged rollout. All traffic shifts to new pods simultaneously during the rolling update. No ability to detect regressions before full rollout. |
| **Recommendation** | For AWS migration: adopt a GitOps approach (per preference) with ArgoCD and Argo Rollouts on EKS for canary deployments. Define `AnalysisTemplate` and `Rollout` resources that automatically promote or rollback based on metric analysis. Avoid manual deployments (per preference) — implement full automated canary pipeline with traffic shifting. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (skaffold run → kubectl apply, pod wait, smoke test), `.github/workflows/ci-main.yaml` (same pattern), `skaffold.yaml` (deploy: kubectl: {}), `kubernetes-manifests/frontend.yaml` (readiness/liveness probes defined) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration testing in CI: (1) `ci-pr.yaml` code-tests job runs Go unit tests for 3 packages (shippingservice, productcatalogservice, frontend/validator) and C# unit tests for cartservice. (2) `ci-pr.yaml` deployment-tests job builds all services, deploys to a dedicated GKE namespace, waits for all 12 deployments to be available, and runs smoke tests — the loadgenerator sends realistic traffic and the pipeline asserts zero errors after 50+ requests. (3) `ci-main.yaml` mirrors the same test/deploy/smoke pattern for main branch. (4) `helm-chart-ci.yaml` validates Helm templates across 5 configurations (default, gRPC health probes, Spanner, ASM, Memorystore). (5) `kustomize-build-ci.yaml` validates Kustomize builds for base and all test combinations. |
| **Gap** | Strong integration testing with live deployment and smoke tests. Minor gaps: no contract testing between services (gRPC contract validation), no load testing in CI (loadgenerator is used for smoke testing, not performance testing), no chaos testing. |
| **Recommendation** | Add gRPC contract testing using the protobuf definitions in `protos/demo.proto` to validate service API compatibility. For AWS migration: maintain the same integration test pattern on EKS. Consider adding contract tests using tools like Buf for protobuf validation. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (code-tests: Go + C# unit tests; deployment-tests: GKE deploy + smoke test), `.github/workflows/ci-main.yaml` (same pattern), `.github/workflows/helm-chart-ci.yaml` (5 Helm template validations), `.github/workflows/kustomize-build-ci.yaml` (Kustomize build validation) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns found. No SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files in Markdown, YAML, or JSON format. The `.github/SECURITY.md` provides a vulnerability reporting process but no operational incident response procedures. |
| **Gap** | Incident response is entirely ad hoc with no documented procedures or automated remediation. |
| **Recommendation** | Create structured runbooks for common failure modes (pod crash loops, Redis connection failures, high latency). For AWS migration: use AWS Systems Manager Automation documents for self-healing patterns (e.g., automatic pod restart on health check failures). Define incident response workflows using Step Functions. |
| **Evidence** | `.github/SECURITY.md` (vulnerability reporting only), absence of runbook files in entire repository |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | `.github/CODEOWNERS` assigns `@GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver` as default owners for all files — no per-service or per-observability-asset ownership. No per-service dashboards defined in IaC. No alarm ownership attribution. No team-specific observability configurations. |
| **Gap** | No observability ownership model. A single team owns all files with no distinction between service owners, observability assets, or infrastructure components. |
| **Recommendation** | Define per-service observability ownership in CODEOWNERS (e.g., assign specific teams to specific service directories and their monitoring configs). Create per-service CloudWatch dashboards with named owners. Tag alarms and dashboards with owner metadata. |
| **Evidence** | `.github/CODEOWNERS` (`* @GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver`), absence of per-service dashboard or alarm ownership in any file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Kubernetes labels are minimal — only `app: {service-name}` label on each Deployment, Service, and ServiceAccount. No cost allocation labels, no environment labels, no ownership labels, no version labels. Terraform resources have no tags/labels beyond the `project` setting. No `default_tags` in Terraform provider. No tag enforcement policies. |
| **Gap** | No resource tagging governance. Cannot track costs per service, identify resource ownership, or enforce tagging standards. |
| **Recommendation** | Add standardized labels to all Kubernetes resources: `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/component`, `app.kubernetes.io/managed-by`, `team`, `environment`, `cost-center`. For AWS migration: define `default_tags` in the Terraform AWS provider. Implement AWS Config rules for required tags. Add cost allocation tags to all AWS resources. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (labels: `app: cartservice` only), `kubernetes-manifests/frontend.yaml` (labels: `app: frontend` only), `terraform/main.tf` (no tags on GKE cluster), `.github/terraform/main.tf` (no tags on GKE cluster or GCS bucket) |



---

## Learning Materials

The following learning resources are mapped to the triggered pathway:

### Move to Managed Databases

- [Move to Managed Databases — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [Amazon ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)
- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [Migrating from Redis to Amazon ElastiCache](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Migration.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q9, INF-Q10, SEC-Q1, SEC-Q2, OPS-Q9 | GKE Autopilot cluster definition, enable_autopilot=true, regional cluster |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q5, Pathway: Managed Databases | Optional Memorystore Redis instance, redis_version=REDIS_7_0, conditional creation |
| `terraform/variables.tf` | INF-Q2 | Variable definitions including memorystore boolean |
| `terraform/terraform.tfvars` | INF-Q2, INF-Q8, SEC-Q5 | Default values: memorystore=false, placeholder project_id |
| `terraform/providers.tf` | INF-Q10 | Google provider version 7.16.0 |
| `terraform/output.tf` | INF-Q10 | Cluster name and location outputs |
| `.github/terraform/main.tf` | INF-Q1, INF-Q9, INF-Q10, SEC-Q1, SEC-Q2, OPS-Q9 | PR staging GKE cluster, GCS state bucket, IAM service accounts |
| `.github/terraform/variables.tf` | INF-Q10 | CI/CD Terraform variable definitions |
| `.github/terraform/versions.tf` | INF-Q10 | Terraform version constraints |
| `kubernetes-manifests/cartservice.yaml` | INF-Q2, INF-Q7, INF-Q8, INF-Q9, DATA-Q3, SEC-Q5, SEC-Q6, OPS-Q9, Pathway: Managed Databases | Redis-cart Deployment (emptyDir, redis:alpine), cartservice Deployment (hardcoded REDIS_ADDR), securityContext |
| `kubernetes-manifests/frontend.yaml` | INF-Q6, SEC-Q3, SEC-Q5, SEC-Q6, OPS-Q5, OPS-Q9 | Frontend Deployment, frontend-external LoadBalancer, hardcoded service addresses, securityContext |
| `kubernetes-manifests/checkoutservice.yaml` | INF-Q3, SEC-Q6 | Checkout service with hardcoded downstream service addresses |
| `kubernetes-manifests/adservice.yaml` | SEC-Q6, OPS-Q9 | Ad service Deployment with securityContext |
| `kubernetes-manifests/kustomization.yaml` | INF-Q5, INF-Q10 | Base Kustomization with commented-out components |
| `helm-chart/Chart.yaml` | INF-Q10 | Helm chart metadata, version 0.10.5 |
| `helm-chart/values.yaml` | INF-Q2, INF-Q5, INF-Q6, INF-Q7, OPS-Q1, SEC-Q3, SEC-Q5, SEC-Q6, DATA-Q3 | Helm defaults: networkPolicies=false, authorizationPolicies=false, otelCollector=false, securityContext=true, seccompProfile=false, cartDatabase config |
| `helm-chart/templates/common.yaml` | INF-Q5, SEC-Q3 | Conditional NetworkPolicy deny-all and AuthorizationPolicy deny-all |
| `helm-chart/templates/frontend.yaml` | INF-Q6, SEC-Q3 | Frontend service with conditional VirtualService, NetworkPolicy, AuthorizationPolicy |
| `istio-manifests/frontend-gateway.yaml` | INF-Q6, SEC-Q3 | Istio Gateway accepting all hosts on HTTP/80, VirtualService routing |
| `istio-manifests/frontend.yaml` | INF-Q6 | Frontend VirtualService for internal routing |
| `istio-manifests/allow-egress-googleapis.yaml` | INF-Q5 | ServiceEntry for egress to Google APIs |
| `kustomize/kustomization.yaml` | INF-Q5, OPS-Q1, INF-Q10 | Root Kustomization with all components commented out |
| `kustomize/base/kustomization.yaml` | INF-Q10 | Base Kustomization listing all 11 services |
| `kustomize/components/network-policies/kustomization.yaml` | INF-Q5 | NetworkPolicy component with 13 per-service policies |
| `kustomize/components/network-policies/network-policy-deny-all.yaml` | INF-Q5 | Deny-all baseline NetworkPolicy |
| `kustomize/components/google-cloud-operations/kustomization.yaml` | OPS-Q1 | OTel tracing patches for 8 services |
| `kustomize/components/google-cloud-operations/otel-collector.yaml` | OPS-Q1 | OpenTelemetry Collector Deployment and ConfigMap |
| `kustomize/components/memorystore/kustomization.yaml` | INF-Q2, Pathway: Managed Databases | Kustomize component to switch from in-cluster Redis to Memorystore |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | PR CI pipeline: unit tests, GKE deployment, smoke tests |
| `.github/workflows/ci-main.yaml` | INF-Q11, OPS-Q5, OPS-Q6 | Main CI pipeline: unit tests, GKE deployment, smoke tests |
| `.github/workflows/helm-chart-ci.yaml` | INF-Q11, OPS-Q6 | Helm lint and template validation across 5 configs |
| `.github/workflows/kustomize-build-ci.yaml` | INF-Q11, OPS-Q6 | Kustomize build validation for base and test combinations |
| `.github/workflows/terraform-validate-ci.yaml` | INF-Q11 | Terraform init and validate |
| `.github/workflows/kubevious-manifests-ci.yaml` | INF-Q11, SEC-Q7, DATA-Q3 | Kubevious manifest validation, skip_rules for container-latest-image |
| `.github/workflows/cleanup.yaml` | INF-Q11 | PR namespace cleanup automation |
| `cloudbuild.yaml` | INF-Q11 | GCP Cloud Build deployment config |
| `skaffold.yaml` | INF-Q11, OPS-Q5 | Multi-platform build config, kubectl deploy, profiles |
| `.github/CODEOWNERS` | OPS-Q8 | Default ownership for all files |
| `.github/SECURITY.md` | OPS-Q7 | Vulnerability reporting process (no incident runbooks) |
| `.github/renovate.json5` | SEC-Q6, SEC-Q7 | Automated dependency updates, weekly schedule |
| `protos/demo.proto` | INF-Q3, INF-Q4, OPS-Q6 | gRPC service definitions for all 9 application services |
| `README.md` | SEC-Q4, Quick Agent Wins | Architecture documentation, quickstart guide, service descriptions |
| `docs/development-guide.md` | Quick Agent Wins | Development and local deployment guide |
| `docs/purpose.md` | Quick Agent Wins | Repository purpose documentation |
