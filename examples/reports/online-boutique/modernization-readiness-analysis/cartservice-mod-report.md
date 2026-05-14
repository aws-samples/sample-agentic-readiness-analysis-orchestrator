# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | cartservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | csharp, grpc, redis, stateful |
| **Context** | C# gRPC service managing shopping carts with Redis backing store. |
| **Overall Score** | 2.11 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.91 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **2.11 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q8: Backup and Recovery | 1 | Redis uses emptyDir volume — all cart data is lost on pod restart. No backup or recovery mechanism exists. | Data loss on any pod disruption; no disaster recovery capability for stateful cart data. |
| 2 | SEC-Q1: Audit Logging | 1 | No audit logging (CloudTrail or equivalent) configured. No log immutability. | Compliance risk; no forensic capability for security incident investigation. |
| 3 | SEC-Q2: Encryption at Rest | 1 | No encryption at rest on any data store. No KMS configuration. | Sensitive cart data (user IDs, product selections) stored unencrypted. |
| 4 | OPS-Q5: Deployment Strategy | 1 | Direct-to-production deployment via `kubectl apply` / `skaffold run`. No canary, blue/green, or traffic shifting. | No safety net for bad deployments; regressions immediately affect all users. |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumentation. No OpenTelemetry SDK, no X-Ray. Cannot trace requests across service boundaries. | Debugging production issues across frontend → cartservice → Redis is guesswork without trace correlation. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (≥ 2). The `ICartStore` interface provides a clean, well-abstracted data access layer with three implementations (Redis, Spanner, AlloyDB). Cart data model is structured protobuf (userId, productId, quantity).
- **What it enables:** A natural language query agent powered by Amazon Bedrock that can query cart state, look up user carts, and report on cart contents without writing code. The clean `ICartStore` interface provides a well-defined tool boundary.
- **Additional steps:** Expose `ICartStore` operations as a lightweight REST or gRPC gateway for agent tool invocation. Generate an OpenAPI spec from the proto definition to enable automated tool discovery. Consider using Amazon Bedrock Agents with an action group that calls the cartservice gRPC endpoints.
- **Effort:** Medium — requires building a thin API wrapper and Bedrock agent configuration.

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). GitHub Actions CI/CD pipeline exists with code-tests (dotnet test) and deployment-tests (Skaffold build + deploy to GKE + smoke tests). Cloud Build configuration also available.
- **What it enables:** A DevOps agent powered by Amazon Bedrock that can trigger builds, check pipeline status, monitor deployment health, and manage release workflows through the existing CI/CD automation surface.
- **Additional steps:** Expose GitHub Actions workflow dispatch API as an agent tool. Add structured build status reporting (JSON output) for agent consumption. Migrate CI/CD to AWS CodePipeline with Terraform (per preferences) and expose pipeline APIs as Bedrock agent action groups.
- **Effort:** Medium — pipeline APIs exist; agent needs action group configuration and IAM permissions.

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository: `README.md` (170 lines covering architecture, service descriptions, deployment instructions), `Cart.proto` (gRPC API contract), `.github/CONTRIBUTING.md`, `.github/SECURITY.md`, `.github/CODE_OF_CONDUCT.md`. The README includes a full architecture diagram reference and service-level descriptions for all 11 microservices.
- **What it enables:** A RAG-based knowledge agent powered by Amazon Bedrock Knowledge Bases that indexes existing documentation and proto definitions. Developers can ask questions about the cartservice architecture, API contract, deployment process, and inter-service dependencies without reading source code.
- **Additional steps:** Index the repository documentation into an Amazon Bedrock Knowledge Base backed by Amazon OpenSearch Service (vector engine). Generate additional documentation from proto files (e.g., gRPC API reference). Add architecture decision records (ADRs) to enrich the knowledge base over time.
- **Effort:** Low — documentation corpus already exists; Bedrock Knowledge Base setup is straightforward.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — service is already a well-decomposed microservice with clean boundaries. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 — compute already runs on managed Kubernetes (GKE Autopilot) with Dockerfiles and K8s Deployments. Contextual guard: already containerized. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected (Redis=OSS, AlloyDB=PostgreSQL-compatible). |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 — default Redis is self-managed in-cluster container with emptyDir (ephemeral). DATA-Q3 = 3 — version pinning partial. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but contextual guard prevents: no data processing workloads exist. CartService is a simple CRUD service with no analytics or streaming needs. |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3 and INF-Q11 = 3 — both primary triggers are ≥ 3. IaC and CI/CD foundations exist. Supporting gaps in OPS-Q5 (deployment strategy = 1) noted but insufficient alone. |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent framework imports detected in source code. No vector DB, no RAG patterns, no agent evaluation frameworks found. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
The cartservice's default configuration runs Redis as an in-cluster container (`redis-cart` Deployment in `kubernetes-manifests/cartservice.yaml`) with an `emptyDir` volume — meaning all cart data is ephemeral and lost on pod restart. This is a self-managed database with no persistence, no backups, no failover, and no encryption. The Terraform configuration includes a conditional Google Cloud Memorystore option (`terraform/memorystore.tf`) but it is disabled by default (`memorystore = false` in `terraform.tfvars`).

Alternative data store implementations exist for Google Cloud Spanner (`SpannerCartStore.cs`) and AlloyDB (`AlloyDBCartStore.cs`), but these are GCP-specific managed services.

**Engine Versions and EOL Status:**
- Memorystore: `redis_version = "REDIS_7_0"` — pinned, not at EOL.
- In-cluster Redis: `redis:alpine` tag without explicit version pin in K8s manifest; Helm chart pins `redis:alpine@sha256:2afb...` via digest — partially pinned.
- Redis 7.0 is current and supported.

**Data Access Patterns:**
The `ICartStore` interface provides a clean abstraction that decouples the application from the underlying database engine. Switching to a new data store implementation requires only a new `ICartStore` implementation and configuration change — the adapter pattern makes database migration significantly easier.

**Recommended Migration Target (respecting preferences: prefer DynamoDB):**
Migrate from in-cluster Redis to **Amazon DynamoDB** for the cart data store. DynamoDB is an excellent fit because:
- Cart data is key-value (userId → cart items) — a natural DynamoDB access pattern.
- DynamoDB provides built-in persistence, automatic backups, point-in-time recovery, encryption at rest, and global tables for HA.
- DynamoDB On-Demand pricing aligns with variable cart workloads.
- The existing `ICartStore` interface pattern means a new `DynamoDBCartStore` implementation can be added alongside existing implementations.

**Alternatively**, if Redis caching semantics are preferred for session-like cart data, migrate to **Amazon ElastiCache for Redis** with:
- Multi-AZ replication for high availability.
- Automatic failover.
- Encryption at rest and in transit.
- Automated backups with configurable retention.

**Migration Approach:**
1. Create a new `DynamoDBCartStore : ICartStore` implementation using the AWS SDK for .NET.
2. Define the DynamoDB table in Terraform (per preferences: use Terraform for IaC).
3. Update `Startup.cs` to select `DynamoDBCartStore` based on a new environment variable (e.g., `DYNAMODB_TABLE_NAME`).
4. Deploy using GitOps workflow (per preferences: prefer GitOps, avoid manual deployments).
5. Test with the existing `CartServiceTests.cs` test suite.
6. Remove the in-cluster `redis-cart` Deployment once migration is validated.

**Representative AWS Services:** Amazon DynamoDB, Amazon ElastiCache for Redis, Amazon MemoryDB for Redis.

**Migration Tools:** For data migration from Redis, use application-level data rehydration (cart data is transient). No DMS needed for cache migration.

**Learning Resources:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI/agent framework usage was detected in the cartservice repository:
- **AI/Agent Frameworks:** No Bedrock SDK, LangChain, Strands, OpenAI, or SageMaker imports in `cartservice.csproj` or source code.
- **Vector Database:** No OpenSearch vector engine, Pinecone, pgvector, or other vector DB infrastructure.
- **RAG Implementation:** No embedding generation, retrieval chains, or document processing patterns.
- **Agent Evaluation:** No Ragas, DeepEval, or custom eval framework.

**Application Domain and Potential AI Use Cases:**
The cartservice is a stateful shopping cart service in an e-commerce platform. AI opportunities include:
- **Shopping assistant agent:** Leverage Amazon Bedrock to build a conversational shopping assistant that can query cart contents, suggest complementary products, and help with checkout (the `shoppingAssistantService` placeholder exists in the Helm chart but is not implemented).
- **Cart analytics agent:** Analyze cart patterns (abandonment, popular items, conversion) using Bedrock for natural language business intelligence.
- **Operational AI:** Use Amazon Q Developer for code review, vulnerability detection, and test generation for the cartservice codebase.

**Quick Wins:** See the Quick Agent Wins section above — Data Query Agent, DevOps Agent, and RAG-Based Knowledge Agent are immediately actionable.

**Recommended AI Services (respecting preferences: prefer Bedrock):**
- **Amazon Bedrock** — Foundation model access for conversational AI and agent capabilities.
- **Amazon Bedrock Agents** — Build agents that can call cartservice gRPC endpoints as tools.
- **Amazon Bedrock Knowledge Bases** — Index documentation for RAG-based developer assistant.
- **Amazon Q Developer** — AI-powered code review and modernization assistance.

**Foundation Requirements Before AI Integration:**
1. Expose cart operations via a REST/gRPC gateway with API documentation (currently proto-only, no OpenAPI).
2. Instrument observability (OPS-Q1 gap) to monitor AI agent interactions.
3. Implement API authentication (SEC-Q3 gap) before exposing endpoints as agent tools.

**Learning Resources:** [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Compute runs on GKE Autopilot (`terraform/main.tf`: `enable_autopilot = true`), a fully managed Kubernetes orchestration platform. The cartservice is containerized with a multi-stage Dockerfile (`src/cartservice/src/Dockerfile`) and deployed as a Kubernetes Deployment (`kubernetes-manifests/cartservice.yaml`). Redis runs as a separate container pod. Helm chart (`helm-chart/templates/cartservice.yaml`) provides templated deployment. This is managed container orchestration — not raw VMs. |
| **Gap** | Infrastructure is GCP-specific (GKE). No AWS managed compute (EKS, ECS, Fargate) defined. Migration to AWS would require re-platforming the Kubernetes deployment. |
| **Recommendation** | Migrate to Amazon EKS (per preferences) with Terraform-defined EKS cluster. The existing Kubernetes manifests and Helm charts are portable — only the cluster provisioning IaC needs replacement. Consider EKS with Karpenter for node auto-scaling. |
| **Evidence** | `terraform/main.tf` (GKE Autopilot), `src/cartservice/src/Dockerfile` (containerized), `kubernetes-manifests/cartservice.yaml` (K8s Deployment), `helm-chart/templates/cartservice.yaml` (Helm chart) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Default configuration deploys Redis as an in-cluster container (`kubernetes-manifests/cartservice.yaml`: `redis-cart` Deployment with `emptyDir: {}` volume). Data is ephemeral — lost on pod restart. A managed option exists via Google Cloud Memorystore (`terraform/memorystore.tf`: `google_redis_instance`) but is disabled by default (`terraform.tfvars`: `memorystore = false`). Alternative managed GCP stores (Spanner, AlloyDB) are supported through code but not the default. |
| **Gap** | Primary database (Redis) is self-managed with no persistence, no failover, no backups. Managed option exists but is not the default deployment. |
| **Recommendation** | Migrate to Amazon DynamoDB (per preferences) for the cart data store, or Amazon ElastiCache for Redis with Multi-AZ, automatic failover, encryption, and automated backups. Define the managed database in Terraform. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (redis-cart Deployment, emptyDir volume), `terraform/memorystore.tf` (Memorystore, conditional), `terraform/terraform.tfvars` (`memorystore = false`), `src/cartservice/src/Startup.cs` (data store selection logic) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service (Step Functions, Temporal, Camunda) detected anywhere in the repository. Business logic in `CartService.cs` is straightforward CRUD: `AddItem`, `GetCart`, `EmptyCart` — all direct database operations with no multi-step workflows. |
| **Gap** | No workflow orchestration capability. While current operations are simple CRUD, any future complex workflows (e.g., cart expiration, cart-to-order transitions, promotional rule chains) would be hardcoded in application logic. |
| **Recommendation** | For the current cart CRUD use case, workflow orchestration is low priority. If cart operations evolve to include multi-step workflows (cart reservation, payment integration), adopt AWS Step Functions defined in Terraform for state machine management. |
| **Evidence** | `src/cartservice/src/services/CartService.cs` (simple CRUD), no `aws_sfn_*` or workflow definitions found |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure detected. All inter-service communication is synchronous gRPC. The cartservice exposes three synchronous gRPC methods (`AddItem`, `GetCart`, `EmptyCart` in `Cart.proto`). No SQS, SNS, EventBridge, Kafka, or RabbitMQ references found in IaC, source code, or configuration. |
| **Gap** | Entirely synchronous architecture. No event-driven patterns. Cart events (item added, cart emptied) are not published for downstream consumers. |
| **Recommendation** | Introduce Amazon SNS or Amazon EventBridge (defined in Terraform) to publish cart events (cart-updated, cart-emptied) for downstream services (recommendations, analytics, checkout). This decouples the cart service from consumers and enables event-driven workflows. Avoid self-managed Kafka. |
| **Evidence** | `src/cartservice/src/protos/Cart.proto` (synchronous gRPC only), `src/cartservice/src/services/CartService.cs` (no event publishing), no messaging resources in `terraform/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Pod-level security is strong: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `capabilities: drop: ALL`, `allowPrivilegeEscalation: false` (in `kubernetes-manifests/cartservice.yaml`). Kubernetes NetworkPolicies are available in the Helm chart (`networkPolicies.create` in `values.yaml`) but disabled by default (`create: false`). Istio service mesh with Sidecars and AuthorizationPolicies are available but also disabled by default. No VPC-level network controls in Terraform — GKE Autopilot uses default VPC configuration. |
| **Gap** | Network segmentation is optional and disabled by default. No fine-grained NetworkPolicies active. No VPC-level controls defined in IaC. Istio service mesh is optional. |
| **Recommendation** | Enable Kubernetes NetworkPolicies by default (`networkPolicies.create: true`). When migrating to EKS, define VPC with private subnets, security groups, and network segmentation in Terraform. Enable Istio or AWS App Mesh for service-level mTLS and authorization. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (securityContext), `helm-chart/values.yaml` (`networkPolicies.create: false`, `authorizationPolicies.create: false`, `sidecars.create: false`), `helm-chart/templates/cartservice.yaml` (NetworkPolicy template) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Istio IngressGateway is defined in `istio-manifests/frontend-gateway.yaml` for the frontend service (HTTP port 80, host: *). The cartservice uses ClusterIP (`kubernetes-manifests/cartservice.yaml`) and is internal only — accessed by frontend and checkoutservice via gRPC. No API Gateway with throttling, authentication, or request validation for the cartservice specifically. The Istio gateway provides basic routing but no advanced traffic management for cart endpoints. |
| **Gap** | No throttling or rate limiting on cart endpoints. No request validation at the gateway level. API entry point is a basic load balancer / ingress without advanced controls. |
| **Recommendation** | When migrating to AWS, deploy an Amazon API Gateway or AWS App Mesh for the cartservice with throttling, authentication, and request validation. For internal gRPC services on EKS, configure an internal Application Load Balancer with gRPC support. |
| **Evidence** | `istio-manifests/frontend-gateway.yaml` (Istio Gateway), `kubernetes-manifests/cartservice.yaml` (ClusterIP Service), `helm-chart/values.yaml` (`frontend.virtualService` config) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No HorizontalPodAutoscaler (HPA) configured for cartservice or redis-cart. Resource requests and limits are set (`kubernetes-manifests/cartservice.yaml`: cpu 200m-300m, memory 64Mi-128Mi; redis-cart: cpu 70m-125m, memory 200Mi-256Mi). GKE Autopilot handles node-level auto-scaling, but no application-level scaling policies exist. Pod count is static (single replica, no `replicas` field = default 1). |
| **Gap** | No application-level auto-scaling. Single replica for both cartservice and redis-cart. Cannot respond to traffic spikes. |
| **Recommendation** | Add HorizontalPodAutoscaler for the cartservice targeting CPU utilization or gRPC request rate. Define minimum 2 replicas for availability and maximum based on expected peak load. When migrating to EKS, use KEDA or native HPA with custom metrics. Define scaling configuration in Terraform or Helm values. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (no HPA, resource limits only), `helm-chart/values.yaml` (no autoscaling config), `helm-chart/templates/cartservice.yaml` (no HPA template) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Redis uses `emptyDir: {}` volume (`kubernetes-manifests/cartservice.yaml`) — all data is stored in ephemeral pod storage and lost on any pod restart, eviction, or node failure. No backup configuration exists. Memorystore (`terraform/memorystore.tf`) has no backup settings when enabled. No AWS Backup plans, no snapshot policies, no PITR configuration. Cart data has zero durability guarantee. |
| **Gap** | Complete absence of backup and recovery. Cart data is ephemeral with no persistence or durability. |
| **Recommendation** | Migrating to Amazon DynamoDB (per preferences) automatically provides continuous backups, point-in-time recovery (PITR), and on-demand backup/restore. If using ElastiCache for Redis, enable automatic daily snapshots with retention period. Define backup configuration in Terraform. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (`emptyDir: {}`), `terraform/memorystore.tf` (no backup config), no `aws_backup_plan` resources |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot in region `us-central1` (`terraform/variables.tf`) is inherently multi-zone for compute — pods are distributed across availability zones automatically. However, the redis-cart pod is a single replica with `emptyDir` storage — if the pod or node fails, cart data is lost with no automatic failover. No Multi-AZ database configuration exists for the default Redis deployment. |
| **Gap** | Compute is multi-zone (via GKE Autopilot) but the data layer (Redis) is single-replica with no replication or failover. A single Redis pod failure causes data loss for all users. |
| **Recommendation** | Migrate to Amazon DynamoDB (per preferences) which provides automatic Multi-AZ replication. If using ElastiCache for Redis, configure Multi-AZ with automatic failover. Increase cartservice replicas to ≥2 with pod anti-affinity rules for zone distribution. |
| **Evidence** | `terraform/variables.tf` (`region = "us-central1"`), `terraform/main.tf` (GKE Autopilot), `kubernetes-manifests/cartservice.yaml` (single redis-cart replica, emptyDir) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Good IaC coverage across multiple layers: Terraform defines the GKE cluster and optional Memorystore (`terraform/main.tf`, `terraform/memorystore.tf`). Kubernetes manifests define workload deployments (`kubernetes-manifests/cartservice.yaml`). Helm chart provides templated, parameterized deployment (`helm-chart/`). Kustomize provides overlay-based customization (`kustomize/` with components for memorystore, network-policies, alloydb, spanner, istio). Skaffold orchestrates build and deploy (`skaffold.yaml`). |
| **Gap** | IaC covers compute and workloads but does not define networking security controls, monitoring/alerting, encryption, or backup infrastructure. Key operational concerns are absent from IaC. |
| **Recommendation** | Extend Terraform to cover VPC networking, security groups, encryption (KMS), monitoring (CloudWatch alarms), and backup policies when migrating to AWS. Adopt GitOps (per preferences) with ArgoCD or Flux for Kubernetes manifest management on EKS. |
| **Evidence** | `terraform/main.tf`, `terraform/memorystore.tf`, `kubernetes-manifests/cartservice.yaml`, `helm-chart/Chart.yaml`, `helm-chart/values.yaml`, `kustomize/kustomization.yaml`, `skaffold.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides CI/CD automation: `ci-pr.yaml` runs code-tests (C# unit tests via `dotnet test`, Go unit tests) and deployment-tests (Skaffold build + deploy to GKE + smoke tests). `ci-main.yaml` provides similar automation for main/release branches. Cloud Build (`cloudbuild.yaml`) provides an alternative build+deploy path. Renovate (`renovate.json5`) automates dependency updates. Concurrency controls prevent duplicate PR runs. |
| **Gap** | No automated rollback mechanism. No canary or blue/green deployment strategy. Deployment is direct `skaffold run` (effectively `kubectl apply`). No security scanning gates in the pipeline. |
| **Recommendation** | Add ArgoCD or Flux for GitOps-based deployment (per preferences: prefer GitOps, avoid manual-deployments). Implement progressive delivery with Argo Rollouts for canary deployments on EKS. Add automated rollback on failed health checks. Integrate security scanning (see SEC-Q7). |
| **Evidence** | `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `cloudbuild.yaml`, `skaffold.yaml`, `.github/renovate.json5` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | C# on .NET 10.0 (`cartservice.csproj`: `<TargetFramework>net10.0</TargetFramework>`). .NET has a solid cloud-native ecosystem with first-class gRPC support (`Grpc.AspNetCore 2.76.0`), container support (chiseled images), Kubernetes integration, and strong AWS SDK support. .NET 10.0 is the latest version — modern and actively supported. |
| **Gap** | .NET is a solid but not tier-1 cloud-native ecosystem compared to Python, TypeScript, Go, or Java/Kotlin. Smaller community for cloud-native patterns and fewer serverless-optimized runtimes (though serverless is in the avoid list). |
| **Recommendation** | Continue with C# / .NET — it is well-suited for gRPC microservices on EKS. Leverage the AWS SDK for .NET for DynamoDB, Bedrock, and other AWS service integrations. No language migration needed. |
| **Evidence** | `src/cartservice/src/cartservice.csproj` (net10.0, Grpc.AspNetCore), `src/cartservice/src/Dockerfile` (.NET SDK 10.0.100) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The cartservice is an independently deployable microservice with well-defined boundaries. It is one of 11 services in the Online Boutique architecture (`README.md`, `skaffold.yaml` lists 11 build artifacts). It has: a clean `ICartStore` interface (`ICartStore.cs`) with three implementations, a dedicated Dockerfile, its own Kubernetes Deployment and ServiceAccount, a single-purpose gRPC API (`Cart.proto`: AddItem, GetCart, EmptyCart), and no shared database with other services. Dependencies are injected via DI in `Startup.cs`. No circular dependencies or shared mutable state. |
| **Gap** | None — this is a well-decomposed microservice with clean module boundaries and interface-based abstractions. |
| **Recommendation** | Maintain current microservice architecture. The `ICartStore` adapter pattern is exemplary and enables easy data store migration. |
| **Evidence** | `src/cartservice/src/cartstore/ICartStore.cs`, `src/cartservice/src/Startup.cs` (DI), `src/cartservice/src/services/CartService.cs`, `src/cartservice/src/Dockerfile`, `kubernetes-manifests/cartservice.yaml`, `skaffold.yaml` (11 services) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC request/response. `Cart.proto` defines three RPC methods — all synchronous unary calls. No message queues, event publishing, or async communication patterns found. The cartservice is called synchronously by the frontend and checkoutservice (visible in Helm AuthorizationPolicy). No event-driven patterns detected anywhere in the cartservice codebase. |
| **Gap** | Entirely synchronous. No async patterns for cart events. Tight coupling between caller and cartservice — callers block waiting for responses. No event publishing for downstream consumers. |
| **Recommendation** | Introduce Amazon SNS or EventBridge to publish cart domain events (CartUpdated, CartEmptied) after successful operations. This enables downstream services (recommendations, analytics) to react to cart changes without synchronous coupling. Keep the gRPC interface for direct queries (GetCart) but add event publication for state changes. |
| **Evidence** | `src/cartservice/src/protos/Cart.proto` (3 synchronous RPCs), `src/cartservice/src/services/CartService.cs` (no event publishing), `helm-chart/templates/cartservice.yaml` (AuthorizationPolicy shows frontend + checkoutservice as callers) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Cart operations (AddItem, GetCart, EmptyCart) are inherently short-running — sub-second Redis cache lookups or simple SQL operations. No operations exceed 30 seconds by design. All methods in `RedisCartStore.cs`, `SpannerCartStore.cs`, and `AlloyDBCartStore.cs` are async (`Task`-based) at the code level, which is appropriate for I/O-bound operations. No long-running batch jobs or complex processing detected. |
| **Gap** | While current operations are appropriately short-running, there is no explicit timeout handling or circuit-breaking for database calls. If Redis/Spanner/AlloyDB becomes slow, gRPC calls will hang until the default timeout. |
| **Recommendation** | Add explicit timeout policies on database calls (e.g., `DistributedCacheEntryOptions` with expiry for Redis, connection timeouts for AlloyDB). Consider implementing circuit-breaker patterns using Polly for .NET to handle backend degradation gracefully. |
| **Evidence** | `src/cartservice/src/cartstore/RedisCartStore.cs` (async, sub-second cache operations), `src/cartservice/src/cartstore/AlloyDBCartStore.cs` (simple SQL), `src/cartservice/src/cartstore/SpannerCartStore.cs` (simple queries) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. The protobuf package is `hipstershop` (`Cart.proto`: `package hipstershop;`) with no version prefix (e.g., `hipstershop.v1`). No `/v1/`, `/v2/` URL patterns. No `Accept-Version` headers. The gRPC service name is `CartService` with no version qualifier. No API changelog or compatibility guarantees documented. |
| **Gap** | Any breaking changes to `Cart.proto` (adding required fields, removing methods, changing types) will break all consumers simultaneously. No mechanism for backward-compatible evolution. |
| **Recommendation** | Adopt protobuf versioning: rename package to `hipstershop.cart.v1`, create versioned service definitions (`CartService` → `CartServiceV1`). For new versions, create `hipstershop.cart.v2` alongside v1 and implement both in the server until consumers migrate. Document API compatibility policy. |
| **Evidence** | `src/cartservice/src/protos/Cart.proto` (`package hipstershop` — no version) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes DNS provides service discovery: the cartservice is accessible via `cartservice:7070` (ClusterIP Service in `kubernetes-manifests/cartservice.yaml`). Redis endpoint is configured via environment variable (`REDIS_ADDR: "redis-cart:6379"` in the Deployment spec) using Kubernetes DNS name. Istio VirtualServices and DestinationRules provide advanced service routing when enabled. Service-to-service communication uses Kubernetes-native DNS resolution — no hard-coded IP addresses. |
| **Gap** | Service discovery relies on Kubernetes DNS and environment variables. No dedicated service registry or API catalog. Redis endpoint is set via static environment variable rather than dynamic discovery. |
| **Recommendation** | Kubernetes DNS is adequate for intra-cluster discovery on EKS. For cross-cluster or external service discovery, consider AWS Cloud Map. Maintain the environment variable pattern for database endpoints but source them from AWS Secrets Manager or SSM Parameter Store. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (ClusterIP Service, `REDIS_ADDR` env var), `helm-chart/templates/cartservice.yaml` (Service definition), `istio-manifests/frontend.yaml` (VirtualService) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The cartservice stores structured cart data: protobuf-serialized bytes in Redis (`RedisCartStore.cs` uses `IDistributedCache` with `cart.ToByteArray()`), or relational rows in Spanner/AlloyDB (userId, productId, quantity columns). No unstructured document storage, no S3/object storage, no file system access, no document parsing pipelines. The service deals exclusively with structured key-value and tabular data. |
| **Gap** | Data is stored in ephemeral in-cluster Redis (emptyDir) with limited accessibility. No managed object storage for any data tier. While the service doesn't inherently need unstructured data storage, the data persistence model itself is fragile. |
| **Recommendation** | Migrate to Amazon DynamoDB (per preferences) for persistent, accessible structured data. If unstructured data needs arise (e.g., cart session replays, audit logs), use Amazon S3 with appropriate lifecycle policies defined in Terraform. |
| **Evidence** | `src/cartservice/src/cartstore/RedisCartStore.cs` (protobuf bytes in cache), `src/cartservice/src/cartstore/AlloyDBCartStore.cs` (SQL tables), `src/cartservice/src/cartstore/SpannerCartStore.cs` (Spanner tables) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Excellent data access layer design. The `ICartStore` interface (`ICartStore.cs`) defines 4 methods: `AddItemAsync`, `EmptyCartAsync`, `GetCartAsync`, `Ping`. Three implementations exist: `RedisCartStore` (Redis/distributed cache), `SpannerCartStore` (Google Cloud Spanner), `AlloyDBCartStore` (PostgreSQL-compatible via Npgsql). Dependency injection in `Startup.cs` selects the implementation based on environment variables (`REDIS_ADDR`, `SPANNER_PROJECT`, `ALLOYDB_PRIMARY_IP`). `CartService.cs` depends only on the interface — zero coupling to any specific data store. |
| **Gap** | None — this is a textbook repository/adapter pattern with clean separation of concerns. |
| **Recommendation** | Maintain this pattern. Adding a new `DynamoDBCartStore : ICartStore` implementation for AWS migration will be straightforward due to this clean abstraction. |
| **Evidence** | `src/cartservice/src/cartstore/ICartStore.cs` (interface), `src/cartservice/src/cartstore/RedisCartStore.cs`, `src/cartservice/src/cartstore/SpannerCartStore.cs`, `src/cartservice/src/cartstore/AlloyDBCartStore.cs`, `src/cartservice/src/Startup.cs` (DI selection), `src/cartservice/src/services/CartService.cs` (depends only on ICartStore) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Memorystore pins `redis_version = "REDIS_7_0"` (`terraform/memorystore.tf`). Helm chart pins the in-cluster Redis image via SHA256 digest: `redis:alpine@sha256:2afb...` (`helm-chart/templates/cartservice.yaml`). The Kubernetes manifest uses `redis:alpine` tag without explicit version pin (`kubernetes-manifests/cartservice.yaml`). Redis 7.0 is current and supported — not at or approaching EOL. Spanner and AlloyDB versions are managed by GCP (no explicit pins needed). |
| **Gap** | The Kubernetes manifest (`cartservice.yaml`) uses `redis:alpine` without a version pin — the actual Redis version depends on the latest `alpine` tag at pull time. Only the Helm chart has digest pinning. Inconsistent versioning between deployment methods. |
| **Recommendation** | Pin Redis version explicitly in all deployment manifests (e.g., `redis:7.0-alpine` or use SHA256 digest everywhere). When migrating to ElastiCache or DynamoDB, pin engine versions in Terraform. Establish a version lifecycle policy. |
| **Evidence** | `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`), `helm-chart/templates/cartservice.yaml` (`redis:alpine@sha256:...`), `kubernetes-manifests/cartservice.yaml` (`image: redis:alpine` — no version pin) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL. `RedisCartStore.cs` uses `IDistributedCache` (get/set operations). `SpannerCartStore.cs` uses the Spanner client SDK with parameterized queries (`CreateSelectCommand`, `CreateInsertOrUpdateCommand`, `CreateDmlCommand`). `AlloyDBCartStore.cs` uses standard SQL (`INSERT INTO ... ON CONFLICT DO UPDATE`, `SELECT`, `DELETE`) via Npgsql — ANSI SQL compatible with any PostgreSQL-compatible engine. All business logic resides in the C# application layer. No `.sql` migration files found. |
| **Gap** | None — all business logic is in the application layer with standard SQL. |
| **Recommendation** | Maintain this pattern. The absence of stored procedures and proprietary SQL makes database migration straightforward. The `AlloyDBCartStore` SQL is PostgreSQL-compatible and would work with Amazon Aurora PostgreSQL or RDS PostgreSQL with minimal changes. |
| **Evidence** | `src/cartservice/src/cartstore/RedisCartStore.cs` (IDistributedCache), `src/cartservice/src/cartstore/SpannerCartStore.cs` (Spanner SDK), `src/cartservice/src/cartstore/AlloyDBCartStore.cs` (standard SQL via Npgsql), no `.sql` files found |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No audit logging configuration found. Terraform enables GCP APIs (`monitoring.googleapis.com`, `cloudtrace.googleapis.com`, `cloudprofiler.googleapis.com` in `terraform/main.tf`) but no dedicated audit logging (no CloudTrail equivalent, no GCP Cloud Audit Logs configuration). No log immutability configuration (no S3 Object Lock, no write-once storage). Application logging is limited to `Console.WriteLine` statements in cart store implementations. |
| **Gap** | Complete absence of audit logging. No ability to trace who did what, when. No forensic capability for security incident investigation. |
| **Recommendation** | When migrating to AWS, enable AWS CloudTrail with log file validation and immutable storage (S3 with Object Lock) defined in Terraform. Configure CloudWatch Logs for application logs with appropriate retention policies. Add structured logging (e.g., Serilog with JSON output) to replace Console.WriteLine. |
| **Evidence** | `terraform/main.tf` (API enables only), `src/cartservice/src/cartstore/RedisCartStore.cs` (Console.WriteLine logging), no audit log configuration found |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured on any data store. In-cluster Redis uses `emptyDir` volume with no encryption. Memorystore (`terraform/memorystore.tf`) has no `transit_encryption_mode` or encryption settings. No KMS key definitions found in Terraform. No `kms_key_id` on any resource. Application configuration (`appsettings.json`) has no encryption settings. Cart data (user IDs, product selections) is stored unencrypted. |
| **Gap** | No encryption at rest. Sensitive cart data is unprotected. No KMS key management. |
| **Recommendation** | When migrating to AWS, enable encryption at rest with AWS KMS customer-managed keys defined in Terraform. DynamoDB encrypts at rest by default (AWS-managed key) — upgrade to CMK for full control. If using ElastiCache, enable at-rest encryption with KMS. Add KMS key definitions to Terraform with key rotation policies. |
| **Evidence** | `terraform/memorystore.tf` (no encryption settings), `kubernetes-manifests/cartservice.yaml` (emptyDir — no encryption), `src/cartservice/src/appsettings.json` (no encryption config), no `aws_kms_key` resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | gRPC endpoints have no per-request JWT/OAuth2 authentication middleware. No `[Authorize]` attributes in `CartService.cs`. Istio AuthorizationPolicies are available in the Helm chart (`authorizationPolicies.create` in `values.yaml`) and when enabled, restrict which Kubernetes service accounts can call specific gRPC methods (`helm-chart/templates/cartservice.yaml`: frontend + checkoutservice SAs only). However, this is service-to-service authorization at the mesh level, not per-request user authentication. Default deployment has `authorizationPolicies.create: false`. |
| **Gap** | No per-request authentication. Istio AuthorizationPolicies provide service-level mTLS auth but are disabled by default. Any pod in the namespace can call the cartservice. No user identity propagation. |
| **Recommendation** | Enable Istio AuthorizationPolicies by default for service-to-service mTLS. When migrating to AWS, implement JWT validation middleware in the gRPC pipeline using Amazon Cognito or integrate with AWS App Mesh for mTLS. Add `[Authorize]` attributes to gRPC endpoints. |
| **Evidence** | `src/cartservice/src/services/CartService.cs` (no auth middleware), `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/cartservice.yaml` (AuthorizationPolicy template), `src/cartservice/src/Startup.cs` (no auth configuration) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, Okta, Ping, or OIDC/SAML configuration. Kubernetes ServiceAccounts are defined (`kubernetes-manifests/cartservice.yaml`) for pod identity. Google Cloud Secret Manager is used in `AlloyDBCartStore.cs` for database credential retrieval, but this is secret management, not identity integration. The cartservice has no concept of user authentication — it accepts a `userId` string parameter directly from callers with no identity verification. |
| **Gap** | No centralized identity integration. The cartservice trusts whatever `userId` is passed by callers. No SSO, no federated identity. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity when migrating to AWS. Use IRSA (IAM Roles for Service Accounts) on EKS for pod-level AWS identity. Extract `userId` from validated JWT tokens rather than trusting caller-provided strings. |
| **Evidence** | `src/cartservice/src/protos/Cart.proto` (`userId` as plain string), `kubernetes-manifests/cartservice.yaml` (ServiceAccount), `src/cartservice/src/cartstore/AlloyDBCartStore.cs` (Secret Manager — secrets, not identity) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Mixed approach. `AlloyDBCartStore.cs` uses Google Cloud Secret Manager to retrieve the AlloyDB database password (`SecretManagerServiceClient.Create()`, `client.AccessSecretVersion(secretVersionName)`). However, the Redis connection address is passed as a plain environment variable (`REDIS_ADDR: "redis-cart:6379"` in `kubernetes-manifests/cartservice.yaml`). Spanner configuration uses environment variables (`SPANNER_PROJECT`, `SPANNER_INSTANCE`, `SPANNER_DATABASE`, `SPANNER_CONNECTION_STRING`). No automated secret rotation configured. |
| **Gap** | Inconsistent secrets management. One store (AlloyDB) uses managed secrets; others use plain environment variables. No rotation. Redis credentials (if authentication were added) would need secret management. |
| **Recommendation** | Migrate to AWS Secrets Manager for all database credentials, defined in Terraform. Use the AWS Secrets Manager CSI driver on EKS to inject secrets as mounted volumes. Enable automatic rotation for database credentials. Replace plain environment variables with Secrets Manager references. |
| **Evidence** | `src/cartservice/src/cartstore/AlloyDBCartStore.cs` (GCP Secret Manager), `kubernetes-manifests/cartservice.yaml` (`REDIS_ADDR` env var), `src/cartservice/src/Startup.cs` (Configuration["REDIS_ADDR"], Configuration["SPANNER_PROJECT"]) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Excellent container hardening. Dockerfile uses a chiseled runtime image (`mcr.microsoft.com/dotnet/runtime-deps:10.0.0-noble-chiseled`) with SHA256 digest pinning — chiseled images have no shell, no package manager, minimal attack surface. Runs as non-root user (`USER 1000`). Pod securityContext enforces: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `capabilities: drop: ALL`, `allowPrivilegeEscalation: false`, `privileged: false`. Build uses self-contained publish with trimming (`PublishTrimmed=true`, `TrimMode=full`). |
| **Gap** | No vulnerability scanning (no Inspector, Snyk, or Trivy). No automated patching pipeline for base images. Renovate handles dependency updates but not OS-level patches. No seccomp profile enabled by default (`seccompProfile.enable: false` in Helm values). |
| **Recommendation** | Integrate Amazon ECR image scanning or Trivy for container vulnerability scanning in CI/CD. Enable seccomp profiles (`seccompProfile.enable: true`, `type: RuntimeDefault`). Add automated base image rebuild triggers when upstream images are updated. |
| **Evidence** | `src/cartservice/src/Dockerfile` (chiseled image, SHA256 pin, USER 1000, trimmed), `kubernetes-manifests/cartservice.yaml` (securityContext), `helm-chart/values.yaml` (`seccompProfile.enable: false`) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning in CI/CD workflows. `.github/workflows/ci-pr.yaml` and `ci-main.yaml` run only unit tests (`dotnet test`) and deployment smoke tests. No SonarQube, Semgrep, CodeGuru, Snyk, or Trivy steps. Renovate (`renovate.json5`) automates dependency version updates but does not scan for or block on vulnerabilities. No `.snyk` policy file. No `dotnet audit` in pipeline. No container image scanning step. |
| **Gap** | Complete absence of security scanning in the CI/CD pipeline. Dependencies are updated by Renovate but not scanned for known vulnerabilities before deployment. |
| **Recommendation** | Add `dotnet list package --vulnerable` and Snyk/Trivy to CI/CD pipeline steps. Integrate Amazon CodeGuru Reviewer for C# SAST. Add ECR image scanning for container vulnerabilities. Configure security gates that block deployment on critical/high findings. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (no security scanning steps), `.github/workflows/ci-main.yaml` (no security scanning steps), `.github/renovate.json5` (dependency updates only, no vulnerability scanning) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation in the cartservice. `cartservice.csproj` has no OpenTelemetry SDK packages (no `OpenTelemetry.Instrumentation.AspNetCore`, no `OpenTelemetry.Exporter.*`). No X-Ray SDK. The Helm chart offers optional OpenTelemetry Collector (`opentelemetryCollector.create: false`) and Google Cloud Operations tracing (`googleCloudOperations.tracing: false`) but both are disabled by default. Terraform enables `cloudtrace.googleapis.com` API but no trace instrumentation exists in code. |
| **Gap** | No distributed tracing. Cannot trace requests across service boundaries (frontend → cartservice → redis). Debugging production issues requires log correlation without trace IDs. |
| **Recommendation** | Add OpenTelemetry SDK for .NET (`OpenTelemetry.Instrumentation.AspNetCore`, `OpenTelemetry.Instrumentation.GrpcNetClient`) to `cartservice.csproj`. Configure the OTLP exporter to send traces to AWS X-Ray via the ADOT collector on EKS. Propagate `traceparent` headers across gRPC calls. |
| **Evidence** | `src/cartservice/src/cartservice.csproj` (no OTEL packages), `helm-chart/values.yaml` (`opentelemetryCollector.create: false`, `googleCloudOperations.tracing: false`), `terraform/main.tf` (`cloudtrace.googleapis.com` API enabled but unused by cartservice) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking. No CloudWatch/GCP monitoring alarms for latency, availability, or error rate. No SLO configuration files. No monitoring dashboards defined in IaC. gRPC health check is implemented (`HealthCheckService.cs`) but this is a liveness/readiness probe, not an SLO definition. |
| **Gap** | No formal SLO definitions. Cannot measure whether the cartservice meets user expectations for availability or latency. No data-driven basis for prioritizing reliability improvements. |
| **Recommendation** | Define SLOs for the cartservice: availability target (e.g., 99.9%), gRPC latency P99 target (e.g., < 200ms), error rate target. Implement SLO monitoring with Amazon CloudWatch on EKS. Configure error budget alerting. |
| **Evidence** | `src/cartservice/src/services/HealthCheckService.cs` (health probe, not SLO), no SLO files found, no monitoring alarm resources in `terraform/` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metric publishing. Application logging is limited to `Console.WriteLine` in cart store implementations (e.g., `"AddItemAsync called with userId={userId}, productId={productId}, quantity={quantity}"` in `RedisCartStore.cs`). No CloudWatch `put_metric_data` calls. No Prometheus metric exports. No business outcome metrics (cart conversion rates, items per cart, cart abandonment). |
| **Gap** | Only basic console logging. No business metrics. Cannot measure cart usage patterns, conversion impact, or service value delivery. |
| **Recommendation** | Add custom CloudWatch metrics for business outcomes: items added per minute, carts created, carts emptied (potential abandonment signal), average items per cart. Use the AWS SDK for .NET CloudWatch client or OpenTelemetry metrics exporter. |
| **Evidence** | `src/cartservice/src/cartstore/RedisCartStore.cs` (Console.WriteLine only), `src/cartservice/src/services/CartService.cs` (no metric calls), `src/cartservice/src/cartservice.csproj` (no metrics SDK) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. Terraform enables `monitoring.googleapis.com` API (`terraform/main.tf`) but defines no monitoring resources (no alarms, no dashboards, no notification channels). No PagerDuty, OpsGenie, or SNS topic integration. Kubernetes liveness and readiness probes exist but these are pod health checks, not operational alerting. |
| **Gap** | No alerting. Service degradation or failure would go unnoticed until users report issues or the pod restarts from a failed health check. |
| **Recommendation** | Configure Amazon CloudWatch alarms for: gRPC error rate > threshold, P99 latency > target, Redis connection failures, pod restart count. Integrate with Amazon SNS for alert notifications. Add CloudWatch anomaly detection for error rates and latency patterns. Define all alerts in Terraform. |
| **Evidence** | `terraform/main.tf` (`monitoring.googleapis.com` — API only, no alarm resources), `kubernetes-manifests/cartservice.yaml` (probes only), no alerting configuration found |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Deployment is direct-to-production via `skaffold run` which executes `kubectl apply` (`skaffold.yaml`: `deploy: kubectl: {}`). CI pipeline in `.github/workflows/ci-pr.yaml` deploys all services simultaneously to a PR namespace — there is no staged rollout, traffic shifting, or canary deployment. No CodeDeploy configuration. No Argo Rollouts. No feature flags. No weighted target groups. Deployment is immediate and applies to all pods at once. |
| **Gap** | No progressive delivery. Bad deployments immediately affect all users. No rollback mechanism beyond manual `kubectl rollout undo`. |
| **Recommendation** | Adopt ArgoCD for GitOps-based deployment (per preferences: prefer GitOps) with Argo Rollouts for canary deployments on EKS. Define rollout strategy (e.g., 10% → 25% → 50% → 100% with automated analysis). Implement automated rollback on degraded gRPC health check or elevated error rate. Avoid manual deployments (per preferences). |
| **Evidence** | `skaffold.yaml` (`deploy: kubectl: {}`), `.github/workflows/ci-pr.yaml` (`skaffold run`), `.github/workflows/ci-main.yaml` (`skaffold run`), `cloudbuild.yaml` (`skaffold run`) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Good integration test coverage. `CartServiceTests.cs` contains 3 gRPC integration tests using `Microsoft.AspNetCore.TestHost`: `GetItem_NoAddItemBefore_EmptyCartReturned`, `AddItem_ItemExists_Updated`, `AddItem_New_Inserted`. Tests use in-memory cache (fallback when `REDIS_ADDR` is not set). CI pipeline (`ci-pr.yaml`) runs `dotnet test` for unit/integration tests, then deploys to GKE and runs smoke tests using the loadgenerator (verifies >50 requests with 0 errors). |
| **Gap** | Integration tests use in-memory cache, not a real Redis instance — they don't test actual Redis behavior (serialization edge cases, connection failures). Smoke tests check only basic health, not specific cart operation correctness in a deployed environment. No contract tests with consumer services (frontend, checkoutservice). |
| **Recommendation** | Add integration tests with a real Redis instance using Testcontainers for .NET. Add gRPC contract tests to validate proto compatibility with consumer services. Extend CI smoke tests to verify specific cart operations (add item, get cart, empty cart) against the deployed service. |
| **Evidence** | `src/cartservice/tests/CartServiceTests.cs` (3 gRPC integration tests), `src/cartservice/tests/cartservice.tests.csproj` (test dependencies), `.github/workflows/ci-pr.yaml` (dotnet test + smoke test) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automation documents, or self-healing patterns found. No Systems Manager Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. `.github/SECURITY.md` documents vulnerability reporting process but not incident response. Kubernetes liveness probes provide automatic pod restart (basic self-healing), but no application-level incident automation. |
| **Gap** | No incident response automation. Response is entirely manual and ad hoc. No documented runbooks for common failure scenarios (Redis down, high latency, pod crash loops). |
| **Recommendation** | Create runbooks for common incidents: Redis unavailable, elevated gRPC error rate, pod crash loops, memory pressure. Implement as AWS Systems Manager Automation documents or Step Functions defined in Terraform. Add PagerDuty/OpsGenie integration for incident notification. |
| **Evidence** | `.github/SECURITY.md` (vulnerability reporting only), `kubernetes-manifests/cartservice.yaml` (liveness probes — basic self-healing), no runbook files found |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS file exists (`.github/CODEOWNERS`: `@GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver`) but applies to the entire repository, not per-service observability. No per-service dashboards. No alarm ownership attribution. No SLO definitions with team names. No observability configuration files with named owners. |
| **Gap** | No observability ownership. No one is explicitly responsible for cartservice monitoring, alerting, or SLO compliance. |
| **Recommendation** | Define a CODEOWNERS entry for observability assets (e.g., `monitoring/ @cart-team`). Create per-service CloudWatch dashboards with team ownership tags. Assign SLO ownership to specific team members. Define alert escalation paths. |
| **Evidence** | `.github/CODEOWNERS` (repo-level only), no per-service dashboards, no SLO ownership files |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes labels are applied consistently: `app: cartservice` on Deployment, Service, and ServiceAccount; `app: redis-cart` on Redis resources (`kubernetes-manifests/cartservice.yaml`). Helm chart adds labels dynamically from values. However, no AWS resource tags exist (no `default_tags` in Terraform provider, no `tags` on Terraform resources). No cost allocation tags. No tag enforcement policies. No environment, team, or cost-center tags. |
| **Gap** | Kubernetes labels exist but no cloud resource tagging strategy. Cannot track costs per service, identify resource ownership, or enforce tagging governance. |
| **Recommendation** | When migrating to AWS, add `default_tags` in the Terraform AWS provider with standard tags (Environment, Service, Team, CostCenter). Add `required-tags` AWS Config rule for enforcement. Tag all AWS resources (DynamoDB tables, EKS clusters, ECR repos) consistently. |
| **Evidence** | `kubernetes-manifests/cartservice.yaml` (Kubernetes labels: `app: cartservice`, `app: redis-cart`), `terraform/providers.tf` (no `default_tags`), `terraform/main.tf` (no tags on GKE resources) |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `terraform/main.tf` | INF-Q1, INF-Q5, INF-Q9, INF-Q10, SEC-Q1, OPS-Q1, OPS-Q4 | GKE Autopilot cluster definition, GCP API enables (monitoring, cloudtrace, cloudprofiler) |
| `terraform/memorystore.tf` | INF-Q2, DATA-Q3, SEC-Q2 | Conditional Google Cloud Memorystore (Redis) instance, redis_version=REDIS_7_0 |
| `terraform/variables.tf` | INF-Q9 | Region configuration (us-central1), memorystore variable |
| `terraform/terraform.tfvars` | INF-Q2 | memorystore=false (disabled by default) |
| `terraform/providers.tf` | OPS-Q9 | Google provider, no default_tags |
| `kubernetes-manifests/cartservice.yaml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, APP-Q2, APP-Q3, SEC-Q3, SEC-Q5, SEC-Q6, OPS-Q4, OPS-Q7, OPS-Q9, DATA-Q3 | CartService + Redis Deployments, Services, ServiceAccount, securityContext, emptyDir volume, resource limits, probes, labels |
| `helm-chart/Chart.yaml` | INF-Q10 | Helm chart metadata (onlineboutique v0.10.5) |
| `helm-chart/values.yaml` | INF-Q5, INF-Q7, OPS-Q1, SEC-Q3, SEC-Q6 | Default values: networkPolicies, authorizationPolicies, sidecars, opentelemetryCollector, seccompProfile (all disabled by default) |
| `helm-chart/templates/cartservice.yaml` | INF-Q5, INF-Q6, APP-Q3, APP-Q6, SEC-Q3, SEC-Q6, DATA-Q3 | Templated cartservice + redis-cart deployment with NetworkPolicy, AuthorizationPolicy, Sidecar, redis digest pin |
| `src/cartservice/src/cartservice.csproj` | APP-Q1, OPS-Q1, OPS-Q3 | .NET 10.0 target, NuGet packages (Grpc.AspNetCore, Redis cache, Spanner, Npgsql, Secret Manager) |
| `src/cartservice/src/Program.cs` | APP-Q2 | Application entry point |
| `src/cartservice/src/Startup.cs` | INF-Q2, APP-Q2, DATA-Q2, SEC-Q3, SEC-Q5 | DI configuration, data store selection, gRPC service registration |
| `src/cartservice/src/Dockerfile` | INF-Q1, APP-Q1, SEC-Q6 | Multi-stage build, chiseled runtime image, SHA256 pin, USER 1000, trimmed publish |
| `src/cartservice/src/protos/Cart.proto` | APP-Q2, APP-Q3, APP-Q5, SEC-Q4 | gRPC service definition (3 RPCs), package hipstershop (no version) |
| `src/cartservice/src/cartstore/ICartStore.cs` | APP-Q2, DATA-Q2 | Data access interface (AddItemAsync, EmptyCartAsync, GetCartAsync, Ping) |
| `src/cartservice/src/cartstore/RedisCartStore.cs` | DATA-Q1, DATA-Q2, DATA-Q4, OPS-Q3 | Redis implementation via IDistributedCache, protobuf serialization, Console.WriteLine logging |
| `src/cartservice/src/cartstore/SpannerCartStore.cs` | DATA-Q1, DATA-Q2, DATA-Q4, APP-Q4 | Spanner implementation via SDK, parameterized queries |
| `src/cartservice/src/cartstore/AlloyDBCartStore.cs` | DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q4, SEC-Q5, APP-Q4 | AlloyDB (PostgreSQL) via Npgsql, GCP Secret Manager for password, standard SQL |
| `src/cartservice/src/services/CartService.cs` | APP-Q2, APP-Q3, OPS-Q3, SEC-Q3 | gRPC service implementation, delegates to ICartStore |
| `src/cartservice/src/services/HealthCheckService.cs` | OPS-Q2 | gRPC health check implementation |
| `src/cartservice/src/appsettings.json` | SEC-Q2 | Kestrel HTTP2 config, logging levels |
| `src/cartservice/tests/CartServiceTests.cs` | OPS-Q6 | 3 gRPC integration tests using TestHost |
| `src/cartservice/tests/cartservice.tests.csproj` | OPS-Q6 | Test project: xunit, Grpc.Net.Client, TestHost |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | CI/CD: code-tests (dotnet test), deployment-tests (skaffold run + smoke test) |
| `.github/workflows/ci-main.yaml` | INF-Q11, OPS-Q5, SEC-Q7 | CI/CD for main/release branches |
| `cloudbuild.yaml` | INF-Q11, OPS-Q5 | Google Cloud Build: skaffold run deployment |
| `skaffold.yaml` | INF-Q10, INF-Q11, APP-Q2, OPS-Q5 | Build orchestration for 11 services, kubectl deploy |
| `.github/renovate.json5` | INF-Q11, SEC-Q7 | Automated dependency updates (not vulnerability scanning) |
| `.github/CODEOWNERS` | OPS-Q8 | Repo-level ownership: GoogleCloudPlatform/devrel-flagship-app-maintainers |
| `.github/SECURITY.md` | OPS-Q7 | Vulnerability reporting process only |
| `istio-manifests/frontend-gateway.yaml` | INF-Q6 | Istio IngressGateway for frontend (HTTP port 80) |
| `istio-manifests/frontend.yaml` | APP-Q6 | Istio VirtualService for frontend service routing |
| `kustomize/kustomization.yaml` | INF-Q10 | Kustomize base + component overlays (memorystore, network-policies, etc.) |
| `README.md` | APP-Q2 | Architecture description: 11 microservices, service descriptions |
