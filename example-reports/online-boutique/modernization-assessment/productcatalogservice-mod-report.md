# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | productcatalogservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | go, grpc, catalog |
| **Context** | Go gRPC service serving product catalog from a JSON file. |
| **Overall Score** | 2.11 / 4.0 |

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.18 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.11 / 4.0** | **🟠 Needs Work** |

**Scoring Notes:**
- INF: (3+2+1+1+3+2+3+1+2+3+3) / 11 = 24/11 = 2.18
- APP: (4+3+1+3+1+3) / 6 = 15/6 = 2.50
- DATA: (2+3+2+4) / 4 = 11/4 = 2.75
- SEC: (1+1+2+1+2+3+1) / 7 = 11/7 = 1.57
- OPS: (3+1+1+1+2+3+1+1+1) / 9 = 14/9 = 1.56
- Overall: (2.18+2.50+2.75+1.57+1.56) / 5 = 10.56/5 = 2.11

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline | Vulnerabilities in dependencies or code reach production undetected; blocks secure modernization |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured | No audit trail for compliance, forensics, or incident investigation |
| 3 | INF-Q4: Async Messaging and Streaming | 1 | No messaging or streaming infrastructure; all communication is synchronous gRPC | Tight coupling between services; no event-driven patterns for decoupling or resilience |
| 4 | APP-Q3: Async vs Sync Communication | 1 | 100% synchronous gRPC with no async messaging patterns | Cascading failure risk across service boundaries; no decoupled communication |
| 5 | APP-Q5: API Versioning Strategy | 1 | No API versioning on gRPC service; package `hipstershop` with no version prefix | Breaking changes deployed directly; no backward compatibility guarantees for consumers |

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2). The centralized `catalog_loader.go` provides a clean data access layer with `loadCatalog()` abstracting data source, and `product_catalog.go` exposes `ListProducts`, `GetProduct`, and `SearchProducts` methods.
- **What it enables:** A natural language product query agent that translates user questions (e.g., "show me kitchen items under $10") into product catalog searches, leveraging the existing gRPC `SearchProducts` endpoint.
- **Additional steps:** Expose a REST or HTTP API wrapper around the gRPC service to simplify agent tool integration. Generate an OpenAPI spec for the HTTP wrapper. Consider using Amazon Bedrock (preferred) with tool-use to call the product catalog API.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). GitHub Actions CI pipeline exists with unit tests, deployment tests, and smoke tests (`.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`). Skaffold build/deploy automation is in place.
- **What it enables:** A DevOps agent that triggers CI builds, checks pipeline status, manages deployments via Skaffold, and reports build/test results — reducing manual CI/CD oversight.
- **Additional steps:** Configure GitHub Actions API access for agent invocation. Integrate with a GitOps controller (preferred: ArgoCD on EKS) for deployment management.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** README.md exists in the `productcatalogservice/` directory with service documentation covering dynamic catalog reloading, latency injection, and operational commands. Additional documentation exists in `helm-chart/README.md`, `kustomize/README.md`, and `terraform/README.md`.
- **What it enables:** A RAG-based knowledge agent that indexes existing documentation to answer developer questions about service configuration, deployment procedures, and debugging. Uses Amazon Bedrock (preferred) for retrieval-augmented generation.
- **Additional steps:** Aggregate and index all README files and inline code comments. Expand documentation to cover architecture decisions, runbooks, and troubleshooting guides. Set up Amazon OpenSearch Service or Amazon Kendra as the vector store.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3 (≥ 2). OpenTelemetry SDK is instrumented in `server.go` with OTLP trace exporter, gRPC server/client handlers (`otelgrpc.NewServerHandler()`, `otelgrpc.NewClientHandler()`), and trace context propagation (TraceContext + Baggage).
- **What it enables:** An observability agent that queries distributed traces to identify performance bottlenecks, correlate errors across service boundaries, and suggest root causes for latency spikes (e.g., detecting the known `parseCatalog` CPU issue when dynamic reloading is enabled).
- **Additional steps:** Deploy an OpenTelemetry Collector and configure a tracing backend (e.g., AWS X-Ray or Jaeger). Enable `ENABLE_TRACING=1` in production. Connect agent to trace query API.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (already microservices); primary trigger not met |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 (already containerized on managed K8s); Dockerfile and K8s manifests present |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no proprietary SQL); AlloyDB is PostgreSQL-compatible (open source engine) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 (primary data from local JSON file, optional AlloyDB); DATA-Q3 = 2 (no engine version pinning) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1, but contextual guard prevents: no data processing workloads exist (simple catalog CRUD) |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3 (both primary triggers ≥ 3); deployment strategy gaps noted but not sufficient |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks, no vector DB, no RAG, no agent eval framework detected |

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 Finding):**
The productcatalogservice's primary data source is a local JSON file (`products.json`) bundled into the container image at build time. This is the default deployment mode. An optional AlloyDB (GCP managed PostgreSQL) integration exists in `catalog_loader.go`, conditional on the `ALLOYDB_CLUSTER_NAME` environment variable. Memorystore Redis (for the cart service) is defined in `terraform/memorystore.tf`. There is no AWS managed database in use.

**Engine Versions and EOL Status (DATA-Q3 Finding):**
Redis version is pinned to `REDIS_7_0` in `memorystore.tf` (current, not EOL). AlloyDB engine version is not pinned in application configuration. The primary JSON file data source has no database engine.

**Data Access Patterns (DATA-Q2 Finding):**
The `catalog_loader.go` provides a centralized data access layer with `loadCatalog()` abstracting the data source. The `productCatalog` struct accesses data only through `parseCatalog()`. This clean abstraction makes database migration straightforward — only `catalog_loader.go` needs to change.

**Recommended Managed Database Targets:**
- **Amazon DynamoDB** (preferred per `preferences.prefer`): The product catalog is a key-value/document workload (products accessed by ID, listed, and searched by name/description). DynamoDB is ideal for this access pattern with single-digit millisecond latency, automatic scaling, and zero operational overhead. The 9-product catalog easily fits DynamoDB's free tier.
- **Migration approach:** Replace the JSON file loader and AlloyDB loader in `catalog_loader.go` with a DynamoDB client using the AWS SDK for Go v2. The existing `loadCatalog()` abstraction makes this a bounded change.

**Representative AWS Services:** DynamoDB, DynamoDB Streams (for cache invalidation), AWS SDK for Go v2

**Migration Tools:** Manual migration (small dataset — 9 products). For larger datasets: AWS DMS for ongoing replication from PostgreSQL to DynamoDB.

**Links to AWS Guidance:**
- [AWS DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [Move to Managed Databases Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI/agent frameworks, vector databases, RAG implementations, or agent evaluation frameworks were detected during the discovery scan. The `go.mod` contains no Bedrock SDK, LangChain, OpenAI, or other AI library imports. The service is a purely traditional CRUD catalog service.

**Application Domain and Potential AI Use Cases:**
The product catalog service is a natural fit for AI enhancement:
1. **Semantic product search** — Replace the simple `strings.Contains` search in `product_catalog.go` with vector-based semantic search using Amazon Bedrock embeddings, enabling natural language product queries (e.g., "something for outdoor dining" matching "Salt & Pepper Shakers").
2. **Product recommendations** — Use Amazon Bedrock (preferred) to generate personalized product recommendations based on catalog data and user context.
3. **Product description enrichment** — Generate enhanced product descriptions, SEO metadata, or multi-language translations using Bedrock foundation models.
4. **Catalog management agent** — An AI agent that helps manage the product catalog (add products, update descriptions, categorize items) using natural language instructions.

**Quick Wins:** See Quick Agent Wins section (Data Query Agent, RAG-Based Knowledge Agent).

**Recommended AI Services (respecting preferences — prefer Bedrock):**
- **Amazon Bedrock** — Foundation models for semantic search, recommendations, and content generation
- **Amazon Bedrock AgentCore** — Agent runtime for product catalog management agent
- **Amazon OpenSearch Service** (with vector engine) — Vector store for product embeddings enabling semantic search
- **Amazon Bedrock Knowledge Bases** — RAG pipeline for product documentation

**Foundation Requirements:**
Before AI integration, the following should be in place:
1. Migrate data to a managed database (DynamoDB — see Move to Managed Databases pathway) for reliable, queryable product data
2. Expose an HTTP/REST API alongside gRPC (or use gRPC-Gateway) for easier agent tool integration
3. Add API versioning to support concurrent AI and non-AI API versions

**Links to AWS Guidance:**
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Compute runs on GKE Autopilot — a fully managed Kubernetes platform. `terraform/main.tf` defines `google_container_cluster` with `enable_autopilot = true`. The productcatalogservice runs as a Kubernetes Deployment (`kubernetes-manifests/productcatalogservice.yaml`) with a multi-stage Dockerfile (`Dockerfile`) producing a distroless runtime image (`gcr.io/distroless/static`). All 12 microservices are containerized with individual Dockerfiles and K8s Deployments. However, this is GCP GKE, not AWS managed compute (no EKS, ECS, Fargate, or Lambda). |
| **Gap** | Infrastructure is on GCP, not AWS. No AWS managed compute resources exist. Migration to AWS EKS (preferred) required for AWS-native modernization. |
| **Recommendation** | Migrate from GKE Autopilot to Amazon EKS (preferred per `preferences.prefer`). The existing Kubernetes manifests and Helm charts are portable to EKS with minimal changes. Use Terraform (preferred) to provision EKS cluster with managed node groups. Adopt GitOps (preferred) with ArgoCD or Flux for deployment management. |
| **Evidence** | `terraform/main.tf` (google_container_cluster, enable_autopilot=true), `kubernetes-manifests/productcatalogservice.yaml` (Deployment), `Dockerfile` (multi-stage build, distroless) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The primary data source is a local JSON file (`products.json`) bundled into the container image — this is file-system storage with no database management. An optional AlloyDB (GCP managed PostgreSQL) integration exists in `catalog_loader.go`, conditional on `ALLOYDB_CLUSTER_NAME` env var. Memorystore Redis (`terraform/memorystore.tf`) is defined for the cart service with `redis_version = "REDIS_7_0"`. No AWS managed database resources exist. |
| **Gap** | Default deployment uses a local JSON file — no managed database. The AlloyDB integration is optional and GCP-specific. No AWS RDS, DynamoDB, or DocumentDB resources. |
| **Recommendation** | Migrate product catalog data to Amazon DynamoDB (preferred per `preferences.prefer`). The product catalog's key-value access pattern (get by ID, list all, search by text) is well-suited for DynamoDB. Replace `loadCatalogFromLocalFile` and `loadCatalogFromAlloyDB` in `catalog_loader.go` with a DynamoDB loader using AWS SDK for Go v2. Define DynamoDB table in Terraform (preferred). |
| **Evidence** | `products.json` (9 products, local file), `catalog_loader.go` (loadCatalogFromLocalFile, loadCatalogFromAlloyDB), `terraform/memorystore.tf` (google_redis_instance) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service found. No AWS Step Functions, Temporal, Camunda, or any orchestration framework. The service is a simple request/response catalog — no multi-step workflows exist in the current implementation. All business logic is in `product_catalog.go` (ListProducts, GetProduct, SearchProducts). |
| **Gap** | No workflow orchestration. While the current service scope (simple catalog lookup) may not require it, the broader microservices architecture (checkout, payment, shipping) would benefit from orchestration for order fulfillment workflows. |
| **Recommendation** | For the broader microservices-demo system, adopt AWS Step Functions to orchestrate the checkout → payment → shipping workflow currently handled by synchronous gRPC calls in the checkout service. For the productcatalogservice specifically, orchestration is lower priority given its simple read-only nature. Define Step Functions state machines in Terraform (preferred). |
| **Evidence** | Absence across all files — no `aws_sfn_*`, no Temporal imports, no workflow YAML definitions |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure found. All inter-service communication is synchronous gRPC. `server.go` registers a gRPC server; `product_catalog.go` handles synchronous ListProducts/GetProduct/SearchProducts calls. No SQS, SNS, EventBridge, MSK, Kinesis, Kafka, or RabbitMQ. No message queue producers or consumers in the codebase. |
| **Gap** | All communication is synchronous. No event-driven patterns for catalog change notifications, cache invalidation, or decoupled inter-service communication. |
| **Recommendation** | Introduce Amazon SNS/SQS for catalog change events. When the product catalog is updated (via the dynamic reload feature or future CRUD operations), publish a `CatalogUpdated` event to an SNS topic. Consumer services (recommendation, frontend) subscribe via SQS queues. This decouples catalog consumers from the catalog service. Define SNS/SQS resources in Terraform (preferred). |
| **Evidence** | `server.go` (gRPC only), `product_catalog.go` (synchronous handlers), `go.mod` (no messaging SDK imports) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong network security foundation in the Helm chart: fine-grained NetworkPolicies restrict ingress to productcatalogservice from only frontend, checkoutservice, and recommendationservice on port 3550 (`helm-chart/templates/productcatalogservice.yaml`). Istio AuthorizationPolicies limit access by service account principal. Istio Sidecars restrict egress. Kubernetes securityContext configured (runAsNonRoot, readOnlyRootFilesystem, drop ALL capabilities). However, NetworkPolicies are **disabled by default** (`values.yaml: networkPolicies.create: false`). Istio AuthorizationPolicies are also disabled by default. |
| **Gap** | Network security features exist but are disabled by default. NetworkPolicies and AuthorizationPolicies must be explicitly enabled. No VPC or subnet-level segmentation visible in the current GCP Terraform (GKE Autopilot handles this implicitly). |
| **Recommendation** | Enable NetworkPolicies by default (`networkPolicies.create: true` in `values.yaml`). Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true`). When migrating to AWS EKS (preferred), define VPC with private subnets in Terraform (preferred), and use Kubernetes NetworkPolicies with Calico or VPC CNI network policies. |
| **Evidence** | `helm-chart/templates/productcatalogservice.yaml` (NetworkPolicy, AuthorizationPolicy, Sidecar), `helm-chart/values.yaml` (networkPolicies.create: false), `kubernetes-manifests/productcatalogservice.yaml` (securityContext) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Istio Gateway serves as the entry point for the frontend service (`istio-manifests/frontend-gateway.yaml` — Gateway + VirtualService on port 80). The frontend is exposed via a LoadBalancer Service. However, the productcatalogservice is an internal service accessed only via Kubernetes ClusterIP — it has no direct external entry point. No API Gateway with throttling, authentication, or request validation exists. The Istio gateway handles HTTP only, no gRPC-specific routing or rate limiting. |
| **Gap** | No API Gateway with throttling, auth, or request validation. The Istio Gateway is basic (no rate limiting, no auth). Internal service communication has no gateway or throttling controls. |
| **Recommendation** | When migrating to AWS EKS (preferred), deploy an API Gateway (Amazon API Gateway or Kong on EKS) in front of the frontend. For internal gRPC services like productcatalogservice, use an Istio/App Mesh service mesh with rate limiting and mTLS. Define API Gateway resources in Terraform (preferred). |
| **Evidence** | `istio-manifests/frontend-gateway.yaml` (Gateway on port 80, VirtualService), `kubernetes-manifests/productcatalogservice.yaml` (ClusterIP Service) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GKE Autopilot (`terraform/main.tf`, `enable_autopilot = true`) provides automatic node scaling — it provisions and removes nodes based on workload demand. Resource requests and limits are defined for the productcatalogservice container (CPU: 100m request / 200m limit, Memory: 64Mi request / 128Mi limit). However, no Horizontal Pod Autoscaler (HPA) is configured for pod-level scaling. The Deployment does not specify `replicas`, defaulting to 1. |
| **Gap** | Node-level auto-scaling via GKE Autopilot, but no pod-level auto-scaling (HPA). Single replica by default — no horizontal scaling under load. |
| **Recommendation** | Configure HPA for the productcatalogservice Deployment targeting CPU utilization or custom metrics. Set minimum replicas ≥ 2 for availability. When migrating to EKS (preferred), use Karpenter for node auto-scaling and HPA/KEDA for pod auto-scaling. Define HPA in Kubernetes manifests or Helm chart. |
| **Evidence** | `terraform/main.tf` (enable_autopilot=true), `kubernetes-manifests/productcatalogservice.yaml` (resource requests/limits, no replicas spec, no HPA) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found anywhere in the repository. The primary data source (`products.json`) is a static file bundled into the container image — data recovery relies on rebuilding the container image. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning, no EBS snapshot policies. The AlloyDB integration (when enabled) has no backup configuration visible in the repo. Memorystore Redis has no backup configuration in `memorystore.tf`. |
| **Gap** | No backup or recovery strategy for any data store. Product catalog data is only in a JSON file in the container image or optionally in AlloyDB with no visible backup config. No point-in-time recovery. No documented restore procedures. |
| **Recommendation** | When migrating to DynamoDB (preferred), enable point-in-time recovery (PITR) and on-demand backups. Configure DynamoDB PITR in Terraform (preferred). For the broader system, implement AWS Backup plans covering all data stores. Store the products.json in a versioned S3 bucket as the source of truth. |
| **Evidence** | Absence across all IaC files — no backup_retention_period, no aws_backup_plan, no PITR config. `products.json` (static file in container), `terraform/memorystore.tf` (no backup config on Redis) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot distributes nodes across availability zones automatically. However, the productcatalogservice Deployment does not specify `replicas` (defaults to 1 — single pod). No pod disruption budgets (PDB) defined. No multi-AZ database configuration visible (primary data source is a local JSON file). Memorystore Redis is single-instance (`memory_size_gb = 1`) with no replica configuration. |
| **Gap** | Single replica by default — a pod failure means full service outage until Kubernetes reschedules. No pod disruption budget. No explicit multi-AZ data tier. |
| **Recommendation** | Set minimum replicas to 2+ with pod anti-affinity rules to spread across AZs. Add a PodDisruptionBudget (minAvailable: 1). When migrating to EKS (preferred), ensure the EKS cluster spans 2+ AZs and configure topology spread constraints. For DynamoDB (preferred), multi-AZ replication is automatic. Define availability configuration in Terraform (preferred). |
| **Evidence** | `terraform/main.tf` (GKE Autopilot — implicit AZ distribution), `kubernetes-manifests/productcatalogservice.yaml` (no replicas, no PDB), `terraform/memorystore.tf` (single instance Redis) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Good IaC coverage: Terraform defines GKE cluster and Memorystore Redis (`terraform/`). Kubernetes manifests (`kubernetes-manifests/`) define all 12 service Deployments, Services, and ServiceAccounts. Helm chart (`helm-chart/`) provides templated deployment with configurable values. Kustomize (`kustomize/`) provides composable overlays (alloydb, memorystore, service-mesh-istio, network-policies). However, deployment to the cluster uses `null_resource` with `kubectl apply` in Terraform (not fully declarative). Some infrastructure may be manually configured outside IaC. |
| **Gap** | Deployment mechanism (`null_resource` + `kubectl apply`) is imperative, not declarative. No GitOps controller. Some gaps in IaC coverage for monitoring, alerting, and security infrastructure. |
| **Recommendation** | Adopt GitOps (preferred per `preferences.prefer`) with ArgoCD or Flux on EKS to replace `null_resource` + `kubectl apply`. Migrate Terraform from GCP provider to AWS provider (preferred per `preferences.prefer`) for EKS, DynamoDB, and supporting infrastructure. Extend IaC to cover monitoring, alerting, and security scanning infrastructure. |
| **Evidence** | `terraform/` (main.tf, memorystore.tf, variables.tf, providers.tf), `kubernetes-manifests/` (12 service manifests), `helm-chart/` (Chart.yaml, values.yaml, templates/), `kustomize/` (base + 15 components), `terraform/main.tf` (null_resource with kubectl apply) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CI/CD automation exists across multiple pipelines: GitHub Actions PR CI (`.github/workflows/ci-pr.yaml`) runs Go unit tests, C# tests, deploys to a PR-specific GKE namespace, waits for pods, and runs smoke tests. Main branch CI (`.github/workflows/ci-main.yaml`) runs the same with deployment to staging. Additional CI for Helm chart validation, Kustomize build, and Terraform validate. Cloud Build (`cloudbuild.yaml`) with Skaffold provides an alternative deployment path. However, no automated rollback, no canary/blue-green deployment, no security scanning in pipeline. |
| **Gap** | CI/CD exists with build + test + deploy stages, but lacks automated rollback, security scanning (SAST/DAST/dependency), and advanced deployment strategies (canary/blue-green). Deployment is direct via `skaffold run` (not staged rollout). |
| **Recommendation** | Enhance CI/CD pipeline with: (1) Security scanning — add `govulncheck` for Go dependency vulnerabilities, Trivy for container image scanning, and Checkov/tfsec for IaC scanning. (2) Adopt GitOps (preferred) with ArgoCD on EKS for declarative, auditable deployments with automatic drift detection. (3) Implement progressive delivery with Argo Rollouts for canary deployments. Avoid manual deployments (per `preferences.avoid`). |
| **Evidence** | `.github/workflows/ci-pr.yaml` (code-tests + deployment-tests jobs), `.github/workflows/ci-main.yaml` (code-tests + deployment-tests), `cloudbuild.yaml` (skaffold run), `skaffold.yaml` (build + deploy config), `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The productcatalogservice is written in Go (version 1.25.0, toolchain 1.26.1 per `go.mod`). Go is a top-tier cloud-native language with excellent support for containers, Kubernetes, gRPC, and microservices. The broader microservices-demo uses Go, Python, Java, Node.js, and C# — all mature cloud-native languages. The Go ecosystem provides first-class support for AWS SDK, OpenTelemetry, and container-based deployments. |
| **Gap** | No gap — Go is an excellent choice for cloud-native microservices. |
| **Recommendation** | Continue with Go for this service. Ensure the Go version is kept current (currently 1.25+, which is modern). When integrating with AWS services, use the AWS SDK for Go v2 (`github.com/aws/aws-sdk-go-v2`). |
| **Evidence** | `go.mod` (go 1.25.0, toolchain go1.26.1), `*.go` files (server.go, product_catalog.go, catalog_loader.go) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application is part of a well-decomposed microservices architecture with 12 independently deployable services visible in `src/` (adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, loadgenerator, paymentservice, productcatalogservice, recommendationservice, shippingservice, shoppingassistantservice). Each service has its own Dockerfile, Kubernetes Deployment, and ClusterIP Service. The productcatalogservice is independently deployable with its own build, container, and service definition. However, services share a common protobuf definition (`protos/demo.proto` → `genproto/`), creating a coupling point — API changes require regenerating proto stubs across affected services. No shared database between services (each uses its own data source). |
| **Gap** | Shared protobuf contract creates coupling — API evolution requires coordinated proto regeneration across services. No API versioning to manage contract evolution gracefully. |
| **Recommendation** | Introduce gRPC API versioning (e.g., `hipstershop.v1.ProductCatalogService`) to enable backward-compatible API evolution. Consider per-service proto repositories or a contract testing approach (e.g., Buf) to manage the shared proto dependency. |
| **Evidence** | `src/` directory (12 services), `kubernetes-manifests/` (per-service YAML), `Dockerfile` (independent build), `genproto.sh` (proto generation from shared `../../protos/demo.proto`), `skaffold.yaml` (per-service build artifacts) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | 100% of inter-service communication is synchronous gRPC. The productcatalogservice exposes synchronous gRPC endpoints (ListProducts, GetProduct, SearchProducts) and is called synchronously by frontend, checkoutservice, and recommendationservice. No async messaging patterns (SQS, SNS, EventBridge, Kafka) exist. No message queue producers or consumers. No event-driven handlers. The `go.mod` contains no messaging SDK imports. |
| **Gap** | All communication is synchronous, creating tight coupling between services. A productcatalogservice outage cascades to all callers (frontend, checkout, recommendation). No event-driven patterns for catalog updates, cache invalidation, or decoupled processing. |
| **Recommendation** | Introduce Amazon SNS/SQS (avoiding serverless per preferences — use SQS with EKS-based consumers, not Lambda triggers) for event-driven catalog update notifications. Implement a cache layer with DynamoDB Streams or SNS to notify downstream services of catalog changes. Maintain gRPC for synchronous queries but add async for events. |
| **Evidence** | `server.go` (grpc.NewServer, no async), `product_catalog.go` (synchronous handlers only), `go.mod` (no SQS/SNS/Kafka SDK imports), `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy shows callers: frontend, checkout, recommendation — all synchronous) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The productcatalogservice is designed for fast catalog lookups — no operations inherently take > 30 seconds. `ListProducts` returns all 9 products, `GetProduct` does a linear scan, `SearchProducts` does a string match. The `EXTRA_LATENCY` env var is for testing/debugging only. The AlloyDB loader executes a single SELECT query. No background job processing exists, but none is needed for this service's scope. The service appropriately handles its workload synchronously. |
| **Gap** | No async job processing patterns exist, but the current service scope (read-only catalog) does not require them. If catalog management features (bulk import, image processing) are added, async handling will be needed. |
| **Recommendation** | If future features require long-running operations (e.g., bulk catalog import, product image processing), implement async job processing with SQS queues and EKS-based workers (avoiding serverless per preferences). Use Amazon SQS for job queuing rather than Lambda-based processing. |
| **Evidence** | `product_catalog.go` (fast synchronous handlers), `catalog_loader.go` (single SQL query), `server.go` (EXTRA_LATENCY is test-only) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The gRPC service is defined under package `hipstershop` with no version prefix (`/hipstershop.ProductCatalogService/GetProduct`). No `/v1/` URL patterns, no version headers, no versioning annotations. The proto file is shared across all services with no versioning scheme. Breaking changes to the proto would affect all consumers simultaneously. |
| **Gap** | No API versioning — breaking changes deployed directly to all consumers. No backward compatibility guarantees. |
| **Recommendation** | Adopt gRPC API versioning by introducing versioned packages (e.g., `hipstershop.v1.ProductCatalogService`). Use Buf for proto linting and breaking change detection. Maintain backward compatibility by supporting old and new versions concurrently during migration periods. |
| **Evidence** | `genproto/demo_grpc.pb.go` (package hipstershop — no version), `genproto.sh` (generates from unversioned demo.proto) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes DNS-based service discovery is the primary mechanism. The productcatalogservice is exposed as a ClusterIP Service (`kubernetes-manifests/productcatalogservice.yaml`) accessible via `productcatalogservice:3550` within the cluster. Other services discover it via Kubernetes DNS. Istio VirtualService provides additional traffic management capabilities (when enabled). However, the OpenTelemetry collector address is configured via environment variable (`COLLECTOR_SERVICE_ADDR` in `helm-chart/templates/productcatalogservice.yaml`), mixing K8s service discovery with env var-based endpoint configuration. |
| **Gap** | Mixed discovery patterns — Kubernetes DNS for service-to-service, but environment variables for supporting services (collector). No service mesh for dynamic routing enabled by default. No API catalog or service registry beyond K8s DNS. |
| **Recommendation** | When migrating to EKS (preferred), use Kubernetes DNS as the primary service discovery mechanism. Enable Istio or AWS App Mesh service mesh for advanced traffic management (canary, circuit breaking). Reduce reliance on environment variables for service endpoints — use Kubernetes DNS names consistently. |
| **Evidence** | `kubernetes-manifests/productcatalogservice.yaml` (ClusterIP Service on port 3550), `helm-chart/templates/productcatalogservice.yaml` (COLLECTOR_SERVICE_ADDR env var), `server.go` (mustMapEnv for collector address) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Product data is stored as a local JSON file (`products.json`) bundled into the container image via `COPY products.json .` in the Dockerfile. The `loadCatalogFromLocalFile` function in `catalog_loader.go` reads `products.json` from the container filesystem using `os.ReadFile("products.json")`. This is local file system storage — not managed object storage. The AlloyDB alternative stores structured data in PostgreSQL tables, not unstructured storage. Product images are referenced as URL paths (`/static/img/products/...`) but the actual images are served elsewhere (not in this service). |
| **Gap** | Product data is on local filesystem (container image). No S3 or managed object storage. Data updates require rebuilding and redeploying the container image (unless AlloyDB is enabled or dynamic reload is triggered). No parsing pipeline for product data. |
| **Recommendation** | Migrate product data to Amazon DynamoDB (preferred) for structured product records. Store product images in Amazon S3 with CloudFront CDN. If product descriptions need full-text search or AI processing, consider Amazon OpenSearch Service with vector capabilities. |
| **Evidence** | `products.json` (9 products as JSON), `catalog_loader.go` (os.ReadFile("products.json")), `Dockerfile` (COPY products.json .) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `catalog_loader.go` provides a well-structured centralized data access layer. The `loadCatalog()` function abstracts the data source — it checks `ALLOYDB_CLUSTER_NAME` env var and routes to either `loadCatalogFromLocalFile()` or `loadCatalogFromAlloyDB()`. The `productCatalog` struct in `product_catalog.go` accesses data only through `parseCatalog()`, which calls `loadCatalog()`. No other code in the service accesses product data directly. However, `loadCatalogFromAlloyDB` uses direct SQL queries (`pool.Query(context.Background(), query)`) rather than an ORM or repository abstraction. |
| **Gap** | Direct SQL in the AlloyDB loader bypasses an ORM layer. The `loadCatalog()` abstraction is good but the SQL query construction (string concatenation for table name) is a minor concern. |
| **Recommendation** | Maintain the clean `loadCatalog()` abstraction when migrating to DynamoDB (preferred). Implement a `loadCatalogFromDynamoDB()` function using the AWS SDK for Go v2 DynamoDB client. The existing abstraction pattern makes this migration straightforward — only `catalog_loader.go` needs to change. |
| **Evidence** | `catalog_loader.go` (loadCatalog, loadCatalogFromLocalFile, loadCatalogFromAlloyDB), `product_catalog.go` (parseCatalog → loadCatalog) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Redis version is explicitly pinned to `REDIS_7_0` in `terraform/memorystore.tf` — this is current and not approaching EOL. AlloyDB (when enabled) connects via `alloydbconn` client in `catalog_loader.go`, but no engine version is pinned in application configuration or IaC. The AlloyDB engine version is managed by GCP (AlloyDB is a managed PostgreSQL-compatible service), but the application has no visibility into or control over the engine version. The primary data source (JSON file) has no database engine. |
| **Gap** | No AlloyDB engine version pinning. No engine version visibility in application config. Only Redis version is explicitly managed. For the default deployment (JSON file), no database engine exists — version management is moot but data management is primitive. |
| **Recommendation** | When migrating to DynamoDB (preferred), engine version management becomes a non-concern (DynamoDB is fully managed with no user-facing engine versions). For any RDS/Aurora databases in the broader system, pin engine versions in Terraform (preferred) and set up EOL monitoring. |
| **Evidence** | `terraform/memorystore.tf` (redis_version = "REDIS_7_0"), `catalog_loader.go` (no version specification for AlloyDB connection), `go.mod` (alloydbconn v1.17.3, pgx v5.8.0) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL found anywhere in the repository. The single SQL query in `catalog_loader.go` is a simple, standard `SELECT` statement: `SELECT id, name, description, picture, price_usd_currency_code, price_usd_units, price_usd_nanos, categories FROM {table}`. All business logic resides in the Go application layer — `product_catalog.go` handles listing, getting, and searching products in Go code. No `.sql` migration files, no `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements. No ORM bypass patterns. |
| **Gap** | No gap — all business logic is in the application layer, not in the database. This is the ideal state for database migration flexibility. |
| **Recommendation** | Maintain this practice. Keep all business logic in the application layer. When migrating to DynamoDB (preferred), there is no stored procedure extraction needed — the migration is purely a data access layer change. |
| **Evidence** | `catalog_loader.go` (query = "SELECT id, name, description..." — simple standard SQL, no stored procedures), `product_catalog.go` (all business logic in Go: ListProducts, GetProduct, SearchProducts) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration found in the repository. The GCP Terraform enables `cloudtrace.googleapis.com` and `monitoring.googleapis.com` in `terraform/main.tf` (`local.base_apis`), but these are tracing and monitoring APIs, not audit logging. No `aws_cloudtrail` resources. No audit log file validation. No immutable log storage (S3 Object Lock). No CloudWatch log retention policies. Application logging uses `logrus` with JSON format (`server.go`), but this is application logging, not infrastructure audit logging. |
| **Gap** | No audit logging infrastructure. No trail of API calls, infrastructure changes, or access patterns. Compliance and forensic investigation capabilities are absent. |
| **Recommendation** | Enable AWS CloudTrail with log file validation and immutable storage (S3 bucket with Object Lock). Define CloudTrail resources in Terraform (preferred). Configure CloudWatch Logs for application log aggregation with defined retention periods. Integrate with AWS Security Hub for centralized security findings. |
| **Evidence** | `terraform/main.tf` (local.base_apis — cloudtrace, not audit), `server.go` (logrus JSON logging — app-level only), absence of any audit logging config |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration found anywhere in the repository. No `aws_kms_key` resources. No `kms_key_id` on any data stores. The `products.json` file is unencrypted in the container image. Memorystore Redis in `terraform/memorystore.tf` has no encryption configuration. AlloyDB connection in `catalog_loader.go` uses `sslmode=disable` in the DSN string — encryption in transit is also disabled for database connections. |
| **Gap** | No encryption at rest for any data store. No KMS key management. Database connections use `sslmode=disable` (no encryption in transit). |
| **Recommendation** | When migrating to AWS: (1) Enable encryption at rest on DynamoDB (preferred) with AWS-managed or customer-managed KMS keys. (2) Enable encryption at rest on all S3 buckets. (3) Use AWS KMS for key management. (4) Enable encryption in transit (TLS) for all database connections. Define KMS keys and encryption configuration in Terraform (preferred). |
| **Evidence** | Absence of KMS config across all files, `terraform/memorystore.tf` (no encryption settings), `catalog_loader.go` (sslmode=disable in DSN) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No per-request OAuth2/JWT authentication on gRPC endpoints. The productcatalogservice accepts all gRPC calls without application-level auth (`server.go` — no auth interceptor or middleware). However, Istio AuthorizationPolicies exist in the Helm chart (`helm-chart/templates/productcatalogservice.yaml`) that restrict access by service account principal — only frontend, checkoutservice, and recommendationservice can call the service. This provides mTLS-based service-to-service authentication at the mesh level, but not per-request token-based auth. AuthorizationPolicies are disabled by default. |
| **Gap** | No application-level authentication. Istio mTLS provides service identity but not per-request authorization. AuthorizationPolicies are disabled by default. No OAuth2/JWT token validation. |
| **Recommendation** | For internal microservice-to-microservice communication, enable Istio AuthorizationPolicies (`authorizationPolicies.create: true`) to enforce service identity. For any external API exposure, implement OAuth2/JWT validation using an API Gateway or gRPC interceptor. When migrating to EKS (preferred), use Amazon Cognito for user authentication and API Gateway authorizers. |
| **Evidence** | `server.go` (no auth middleware on grpc.NewServer), `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy with principal-based access, disabled by default), `product_catalog.go` (no auth checks in handlers) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration found. No Amazon Cognito, Okta, Ping, OIDC, or SAML configuration. Kubernetes ServiceAccounts are defined (`kubernetes-manifests/productcatalogservice.yaml`) but are not federated with an external IdP. The GCP Secret Manager client in `catalog_loader.go` uses application default credentials (GCP IAM), not a centralized application-level IdP. No SSO configuration. |
| **Gap** | No centralized identity provider. Application has no user authentication system (it's an internal service). Service identity relies on Kubernetes ServiceAccounts without external IdP federation. |
| **Recommendation** | When migrating to AWS EKS (preferred), implement IAM Roles for Service Accounts (IRSA) for fine-grained AWS IAM integration. For user-facing authentication in the broader system, deploy Amazon Cognito as the centralized IdP. Configure OIDC federation between EKS and AWS IAM. |
| **Evidence** | `kubernetes-manifests/productcatalogservice.yaml` (ServiceAccount — no IdP annotations), `catalog_loader.go` (GCP application default credentials), absence of Cognito/OIDC/SAML config |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GCP Secret Manager is used for AlloyDB password retrieval when the AlloyDB integration is enabled. The `getSecretPayload()` function in `catalog_loader.go` uses `cloud.google.com/go/secretmanager` to fetch the database password at runtime (`projects/{project}/secrets/{secret}/versions/latest`). This is a proper secrets management pattern. However, this is conditional (only when `ALLOYDB_CLUSTER_NAME` is set). Environment variables in the Helm chart are set directly in the template (`PORT`, `COLLECTOR_SERVICE_ADDR`, `EXTRA_LATENCY`). No secrets rotation configured. No `aws_secretsmanager_*` resources. |
| **Gap** | Secrets management exists but is conditional and GCP-specific. No rotation. Non-secret env vars are set directly (acceptable), but there's no AWS Secrets Manager integration. The DSN password is fetched securely but `sslmode=disable` weakens the overall posture. |
| **Recommendation** | When migrating to AWS: use AWS Secrets Manager for all credentials. Implement automatic secret rotation. Configure DynamoDB (preferred) access via IAM Roles for Service Accounts (IRSA) — no database passwords needed. For other secrets, define Secrets Manager resources in Terraform (preferred) with rotation schedules. Use ExternalSecrets Operator on EKS to sync secrets from AWS Secrets Manager into Kubernetes. |
| **Evidence** | `catalog_loader.go` (cloud.google.com/go/secretmanager, getSecretPayload function), `helm-chart/templates/productcatalogservice.yaml` (env vars set directly), absence of aws_secretsmanager |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong container hardening: The Dockerfile uses a distroless base image (`gcr.io/distroless/static`) — minimal attack surface with no shell, no package manager, no OS utilities. Kubernetes securityContext is well-configured: `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: ALL`, `privileged: false`. GKE Autopilot handles node-level patching. However, no vulnerability scanning (Inspector, Snyk, Trivy) is configured. No SSM Patch Manager (AWS-specific). |
| **Gap** | No vulnerability scanning for container images or dependencies. No automated patching pipeline for the application container. Hardening is excellent but monitoring for new vulnerabilities is absent. |
| **Recommendation** | Add Trivy or Amazon ECR image scanning to the CI/CD pipeline for container vulnerability scanning. Add `govulncheck` for Go dependency vulnerability detection. When migrating to EKS (preferred), use Bottlerocket AMIs for node hardening and Amazon Inspector for continuous vulnerability assessment. |
| **Evidence** | `Dockerfile` (FROM gcr.io/distroless/static), `kubernetes-manifests/productcatalogservice.yaml` (comprehensive securityContext), absence of vulnerability scanning tools |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning found in any CI/CD pipeline. The GitHub Actions workflows (`.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`) run only Go unit tests, C# unit tests, deployment tests, and smoke tests. No `govulncheck`, `gosec`, `staticcheck`, Snyk, Semgrep, CodeGuru, Dependabot, or Trivy steps. No `.snyk` policy file. No container image scanning. No IaC security scanning (Checkov, tfsec) in the CI pipeline (Terraform validate CI only checks syntax, not security). |
| **Gap** | No security scanning in the entire CI/CD pipeline. Dependencies are not scanned for known vulnerabilities. Container images are not scanned. IaC is not scanned for security misconfigurations. This is a critical gap for a P0 service. |
| **Recommendation** | Add to CI pipeline: (1) `govulncheck` for Go dependency CVE detection, (2) `gosec` for Go static security analysis, (3) Trivy for container image scanning, (4) Checkov or tfsec for IaC security scanning. Configure Dependabot or Renovate for automated dependency updates. Block merges on critical/high severity findings. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (only Go tests, C# tests, deployment tests — no security steps), `.github/workflows/ci-main.yaml` (same), `.github/workflows/terraform-validate-ci.yaml` (syntax validation only), absence of .snyk, Dependabot config |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry SDK is well-instrumented. `server.go` configures trace context propagation (`otel.SetTextMapPropagator` with `TraceContext{}` and `Baggage{}`), gRPC server handler (`otelgrpc.NewServerHandler()`), and gRPC client handler (`otelgrpc.NewClientHandler()`). OTLP trace exporter sends traces to a configurable collector (`otlptracegrpc.New`). The `go.mod` includes comprehensive OpenTelemetry dependencies (otelgrpc v0.67.0, otel v1.42.0, otlptracegrpc v1.42.0). Tracing samples all requests (`sdktrace.AlwaysSample()`). However, tracing is conditional on `ENABLE_TRACING=1` env var and disabled by default in the Helm chart (`googleCloudOperations.tracing: false`). |
| **Gap** | Tracing is disabled by default. Collector address must be manually configured. Tracing is conditional, not always-on. No trace-based alerting or SLO monitoring. The `initStats()` function has a TODO comment: "Implement OpenTelemetry stats" — metrics are not yet instrumented. |
| **Recommendation** | Enable tracing by default in production (`ENABLE_TRACING=1`). Deploy an OpenTelemetry Collector on EKS (preferred) that exports to AWS X-Ray. Implement OpenTelemetry metrics (address the TODO in `initStats()`). Configure trace-based alerting for latency SLOs. |
| **Evidence** | `server.go` (initTracing, otel.SetTextMapPropagator, otelgrpc.NewServerHandler, otelgrpc.NewClientHandler), `go.mod` (opentelemetry dependencies), `helm-chart/values.yaml` (googleCloudOperations.tracing: false) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking. No latency percentile alarms (p99, p95). Basic health checks exist — gRPC readiness and liveness probes are configured in `kubernetes-manifests/productcatalogservice.yaml` — but these are availability probes, not formal SLO definitions. No CloudWatch alarms. No SLO dashboards. No SLO configuration files. |
| **Gap** | No formal SLOs defined for the product catalog service. No error budget tracking. No way to measure whether the service meets user expectations. Health probes only detect binary up/down — not degraded performance or elevated error rates. |
| **Recommendation** | Define SLOs for the productcatalogservice: (1) Availability SLO: 99.9% of gRPC requests return non-error status, (2) Latency SLO: p99 latency < 200ms for GetProduct, < 500ms for ListProducts. Implement SLO monitoring using OpenTelemetry metrics exported to CloudWatch. Set up error budget alerts in CloudWatch Alarms. |
| **Evidence** | `kubernetes-manifests/productcatalogservice.yaml` (readinessProbe, livenessProbe — health only), absence of SLO definitions, CloudWatch alarms, or error budget configs |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. The `initStats()` function in `server.go` contains only a TODO comment: "Implement OpenTelemetry stats". No `cloudwatch.put_metric_data` or OpenTelemetry metrics instrumentation. Only infrastructure-level health probes (gRPC readiness/liveness) exist. No product search hit rates, catalog size metrics, or request distribution metrics. |
| **Gap** | No business metrics — cannot measure product search effectiveness, catalog access patterns, or conversion impact. Only binary health checks exist. The TODO in `initStats()` indicates intent but no implementation. |
| **Recommendation** | Implement OpenTelemetry metrics for: (1) Products listed per request, (2) Search hit rate (queries with results vs. empty results), (3) Product access frequency (which products are most viewed), (4) Catalog load time, (5) Catalog size. Export metrics to CloudWatch via OpenTelemetry Collector. Create CloudWatch dashboards for business visibility. |
| **Evidence** | `server.go` (initStats with TODO: "Implement OpenTelemetry stats"), absence of any custom metrics instrumentation |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured anywhere in the repository. No CloudWatch alarms, no CloudWatch anomaly detection, no PagerDuty/OpsGenie integration, no composite alarms. No error rate monitoring. No latency monitoring. The only monitoring is Kubernetes health probes (gRPC readiness/liveness), which detect crashes but not performance degradation. |
| **Gap** | No alerting infrastructure. Errors and performance degradation go undetected unless they cause a complete pod crash. No notification mechanism for on-call engineers. |
| **Recommendation** | Configure CloudWatch Alarms for: (1) Error rate > threshold on gRPC endpoints, (2) p99 latency exceeding SLO target, (3) Pod restart count, (4) CPU/memory utilization. Enable CloudWatch anomaly detection for error rate and latency. Integrate with PagerDuty or OpsGenie for on-call notification. |
| **Evidence** | Absence across all configuration files — no alarms, no anomaly detection, no alerting integration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployment uses `skaffold run` which executes `kubectl apply` of Kubernetes manifests (`skaffold.yaml` — `deploy: kubectl: {}`). This uses the default Kubernetes rolling update strategy (one-at-a-time pod replacement). The CI pipeline deploys to a PR-specific namespace for testing (`.github/workflows/ci-pr.yaml`), which is a staging pattern, but production deployments go straight via `skaffold run` with no canary or blue/green. Cloud Build (`cloudbuild.yaml`) also uses `skaffold run` for direct deployment. No Argo Rollouts, no CodeDeploy, no traffic shifting. |
| **Gap** | No canary or blue/green deployment strategy. Direct-to-production via kubectl apply. No traffic shifting or staged rollout. Kubernetes rolling update provides basic zero-downtime but no ability to detect regressions before full rollout. |
| **Recommendation** | Adopt GitOps (preferred) with ArgoCD on EKS (preferred) for declarative deployments. Implement progressive delivery with Argo Rollouts for canary deployments — shift 10% of traffic to new version, monitor error rate and latency, then gradually increase. Avoid manual deployments (per `preferences.avoid`). |
| **Evidence** | `skaffold.yaml` (deploy: kubectl: {}), `cloudbuild.yaml` (skaffold run), `.github/workflows/ci-pr.yaml` (deployment-tests to PR namespace), absence of canary/blue-green config |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CI pipeline includes deployment tests that deploy all 12 services to a staging GKE cluster, wait for all pods to be available, and run smoke tests (`.github/workflows/ci-pr.yaml` — `deployment-tests` job). Smoke tests use the load generator to send 50+ requests and verify zero errors. Go unit tests exist for the productcatalogservice (`product_catalog_test.go` — TestGetProductExists, TestGetProductNotFound, TestListProducts, TestSearchProducts). However, smoke tests are basic (only check error count, not response correctness), and there are no contract tests, no API-level integration tests, and no dedicated integration test suite. |
| **Gap** | Smoke tests are basic (error count only). No contract tests between services. No dedicated integration test suite with specific assertions. No load testing or performance benchmarks in CI. |
| **Recommendation** | Enhance testing: (1) Add gRPC contract tests using Buf or proto-based test generation, (2) Add API-level integration tests with specific assertions (e.g., verify ListProducts returns expected product IDs), (3) Add performance benchmarks in CI to catch latency regressions, (4) Use Testcontainers for local integration testing. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (deployment-tests job, smoke test with error count check), `product_catalog_test.go` (4 unit tests), `.github/workflows/ci-main.yaml` (similar deployment tests) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automated incident response, or self-healing patterns found beyond basic Kubernetes capabilities (pod restart on liveness probe failure). No Systems Manager Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. No runbook files (markdown, YAML, JSON). The README.md documents the dynamic catalog reload bug and how to trigger/fix it via `kubectl exec ... kill -USR1/USR2`, but this is ad hoc debugging, not automated incident response. |
| **Gap** | Incident response is entirely ad hoc. No documented runbooks. No automated remediation. The known catalog reload performance bug has no automated detection or remediation. |
| **Recommendation** | Create machine-readable runbooks for common incidents: (1) High latency due to catalog reload bug — automated detection via latency alarm + automated `USR2` signal to disable reload, (2) Pod crash loop — automated log collection and escalation, (3) Database connection failure — automated fallback to JSON file. Implement runbooks as Systems Manager Automation documents or Step Functions workflows. |
| **Evidence** | `README.md` (manual USR1/USR2 debugging instructions), absence of runbook files, automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-service dashboards, alarms with named owners, or SLO definitions with team attribution found. No CODEOWNERS for observability assets. The repository has no observability configuration files. Labels in Kubernetes manifests (`app: productcatalogservice`) provide service identification but no ownership, team, or cost center attribution. No team tags on any resources. |
| **Gap** | No observability ownership. No one is explicitly responsible for monitoring the productcatalogservice. No dashboards, no named alarm owners, no SLO ownership. |
| **Recommendation** | Define observability ownership: (1) Create a per-service CloudWatch dashboard for the productcatalogservice with key metrics (latency, error rate, catalog load time), (2) Assign named owners to all alarms, (3) Add team ownership labels to Kubernetes resources (e.g., `team: catalog-team`), (4) Add CODEOWNERS for observability configuration files. |
| **Evidence** | `kubernetes-manifests/productcatalogservice.yaml` (only `app` label, no team/owner labels), absence of dashboards, CODEOWNERS for observability |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging governance found. Kubernetes labels are minimal — only `app: productcatalogservice` on Deployments and Services. No cost allocation labels, no environment labels, no team/owner labels. Terraform resources in `terraform/main.tf` have no tags on the `google_container_cluster` or `google_redis_instance`. No tag enforcement policies. No `default_tags` in provider configuration. The Helm chart values have no tag configuration. |
| **Gap** | No tagging governance. Cannot track costs per workload, identify resource ownership during incidents, or enforce budget controls. No environment identification (dev/staging/prod). |
| **Recommendation** | Implement a tagging standard: (1) Add labels to all Kubernetes resources: `app`, `team`, `environment`, `cost-center`, `managed-by`, (2) When migrating to AWS, configure `default_tags` in the Terraform AWS provider with standard tags, (3) Enforce tagging via AWS Config `required-tags` rules, (4) Activate cost allocation tags in AWS Billing. Define tagging standards in Terraform (preferred). |
| **Evidence** | `kubernetes-manifests/productcatalogservice.yaml` (only app label), `terraform/main.tf` (no tags on GKE cluster), `helm-chart/values.yaml` (no tag configuration) |

## Learning Materials

Learning materials are included for triggered pathways only.

### Move to Managed Databases

- [Move to Managed Databases Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [AWS Database Migration Service Documentation](https://docs.aws.amazon.com/dms/)

### Move to AI

- [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)
- [Amazon Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/productcatalogservice/server.go` | INF-Q1, INF-Q4, APP-Q3, SEC-Q1, SEC-Q3, OPS-Q1, OPS-Q3 | gRPC server setup, OpenTelemetry tracing, JSON logging, no auth middleware, initStats TODO |
| `src/productcatalogservice/product_catalog.go` | INF-Q3, APP-Q2, APP-Q3, APP-Q4, DATA-Q4 | Business logic handlers (ListProducts, GetProduct, SearchProducts), synchronous processing |
| `src/productcatalogservice/catalog_loader.go` | INF-Q2, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q2, SEC-Q4, SEC-Q5 | Data access layer, AlloyDB integration, GCP Secret Manager, sslmode=disable, simple SQL |
| `src/productcatalogservice/Dockerfile` | INF-Q1, DATA-Q1, SEC-Q6 | Multi-stage build, golang:1.26.1-alpine builder, gcr.io/distroless/static runtime, COPY products.json |
| `src/productcatalogservice/products.json` | INF-Q2, DATA-Q1 | Static product catalog (9 products), local JSON file data source |
| `src/productcatalogservice/go.mod` | APP-Q1, APP-Q3, INF-Q4, OPS-Q1, DATA-Q3 | Go 1.25.0, OpenTelemetry deps, gRPC deps, AlloyDB/pgx deps, no messaging SDKs |
| `src/productcatalogservice/product_catalog_test.go` | OPS-Q6 | Unit tests (4 tests: GetProduct, GetProductNotFound, ListProducts, SearchProducts) |
| `src/productcatalogservice/genproto/demo_grpc.pb.go` | APP-Q2, APP-Q5 | Generated gRPC stubs, package hipstershop (no version prefix) |
| `src/productcatalogservice/genproto.sh` | APP-Q5 | Proto generation from shared ../../protos/demo.proto |
| `src/productcatalogservice/README.md` | OPS-Q7 | Service documentation, dynamic reload bug, USR1/USR2 debugging |
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q9, INF-Q10, SEC-Q1, OPS-Q9 | GKE Autopilot cluster, null_resource kubectl apply, base_apis, no tags |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2 | Google Memorystore Redis, REDIS_7_0, no backup, no encryption |
| `kubernetes-manifests/productcatalogservice.yaml` | INF-Q1, INF-Q5, INF-Q6, INF-Q7, INF-Q9, APP-Q6, SEC-Q3, SEC-Q4, OPS-Q2, OPS-Q8, OPS-Q9 | Deployment, Service, ServiceAccount, securityContext, health probes, resource limits, labels |
| `helm-chart/values.yaml` | INF-Q5, OPS-Q1, OPS-Q9 | networkPolicies.create:false, tracing:false, service configurations |
| `helm-chart/templates/productcatalogservice.yaml` | INF-Q5, APP-Q3, APP-Q6, SEC-Q3, SEC-Q5 | NetworkPolicy, AuthorizationPolicy, Sidecar, env vars, COLLECTOR_SERVICE_ADDR |
| `istio-manifests/frontend-gateway.yaml` | INF-Q6 | Istio Gateway on port 80, VirtualService for frontend |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | PR CI — Go tests, deployment tests, smoke tests, no security scanning |
| `.github/workflows/ci-main.yaml` | INF-Q11, SEC-Q7 | Main CI — code tests, deployment tests, no security scanning |
| `cloudbuild.yaml` | INF-Q11, OPS-Q5 | Google Cloud Build with Skaffold, direct deployment |
| `skaffold.yaml` | APP-Q2, INF-Q11, OPS-Q5 | Build config for 12 services, kubectl deploy, no canary |
| `src/` directory | APP-Q2 | 12 independently deployable microservices |
| `kustomize/` directory | INF-Q10 | Kustomize base + 15 components (alloydb, memorystore, istio, network-policies) |
| `helm-chart/` directory | INF-Q10 | Full Helm chart for all services |
| `.github/workflows/terraform-validate-ci.yaml` | SEC-Q7 | Terraform syntax validation only — no security scanning |
