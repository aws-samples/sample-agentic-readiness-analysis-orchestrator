# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | frontend |
| **Date** | 2026-04-15 |
| **Repo Type** | `application` |
| **Priority** | P0 |
| **Tags** | go, frontend, grpc |
| **Context** | Go web frontend serving the Online Boutique UI. Calls all backend services via gRPC. |
| **Preferences** | Prefer: EKS, DynamoDB, Bedrock, Terraform, GitOps · Avoid: Serverless, Manual Deployments |
| **Overall Score** | **2.05 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.09 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.05 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q3: API Authentication | 1 | No authentication on any API endpoint; all user-facing routes are open | Critical security vulnerability; blocks any modernization that exposes services externally |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging infrastructure | No forensic capability; compliance blocker for regulated workloads |
| 3 | APP-Q3: Async vs Sync Communication | 1 | All inter-service communication is synchronous gRPC with no async patterns | Tight coupling creates cascading failure risk; limits resilience and scalability |
| 4 | INF-Q4: Async Messaging/Streaming | 1 | No messaging or streaming infrastructure; all communication is synchronous | No event-driven architecture foundation; limits decoupling and fault tolerance |
| 5 | INF-Q8: Backup and Recovery | 1 | No backup configuration for any data store; Redis is ephemeral | Data loss risk; no recovery capability for cart or session state |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 ≥ 2 — DATA-Q2 = 4. All backend service interactions are centralized in `rpc.go`, providing a unified data access layer via gRPC (product catalog, cart, currency, recommendations, shipping, checkout, ads).
- **What it enables:** A natural-language agent that queries product catalog, checks cart contents, fetches shipping quotes, and retrieves recommendations by wrapping the existing gRPC service layer as agent tools. Users or internal teams could ask "What products are in stock under $50?" and the agent invokes existing service calls.
- **Additional steps:** Generate OpenAPI specifications from the gRPC proto definitions to create tool descriptions. Wrap gRPC calls with REST adapters or use Amazon Bedrock's tool-use capability to invoke gRPC directly.
- **Effort:** Medium — gRPC tool interface needs HTTP/REST wrapping for agent compatibility.

### DevOps Agent

- **Prerequisite:** INF-Q11 ≥ 2 — INF-Q11 = 3. Automated CI/CD pipeline exists via GitHub Actions with build, deploy (Skaffold), and smoke test stages.
- **What it enables:** An agent that triggers CI/CD pipeline runs, checks build/deployment status, queries deployment history, and manages releases via the GitHub Actions API. Teams could ask "Deploy the latest frontend to staging" or "What's the status of the last PR deployment?"
- **Additional steps:** Configure GitHub API tokens for agent access. Define deployment approval workflows if human-in-the-loop is needed. Integrate with Amazon Bedrock for natural language interface.
- **Effort:** Low — existing GitHub Actions API provides the automation surface; agent orchestrates via API calls.

### Observability Agent

- **Prerequisite:** OPS-Q1 ≥ 2 — OPS-Q1 = 3. OpenTelemetry distributed tracing is instrumented with OTLP gRPC exporter, HTTP handler wrapping (`otelhttp.NewHandler`), and gRPC client instrumentation (`otelgrpc.NewClientHandler`). Structured JSON logging via logrus with request ID correlation.
- **What it enables:** An agent that queries distributed traces, correlates trace IDs across service boundaries, identifies slow gRPC calls (e.g., ad service with 100ms timeout), and suggests root causes for latency spikes. Teams could ask "Why were checkout requests slow yesterday?" and the agent traces the request flow across all 7 backend services.
- **Additional steps:** Ensure trace data is exported to a queryable backend (e.g., AWS X-Ray or Grafana Tempo via OTLP). Create agent tools that query the trace backend's API. Index structured logs for log-trace correlation.
- **Effort:** Medium — requires trace backend API integration and log indexing setup.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (microservices architecture with well-defined boundaries); primary trigger not met |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 (already on managed K8s with Dockerfiles); contextual guard: compute is already containerized |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures); no commercial DB engines detected (Redis is open source) |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 (Memorystore managed option available); primary trigger not met |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but contextual guard prevents trigger: no data processing workloads exist in this frontend service |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3; neither primary trigger met |
| 7 | Move to AI | **Triggered** | Medium | Medium | No AI/agent framework imports detected; no vector DB; no RAG patterns; no agent eval framework |

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

No AI or agent framework usage was detected in the frontend codebase:

- **AI/Agent Frameworks:** No imports of Amazon Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK found in any Go source file or `go.mod`.
- **Vector Database:** No OpenSearch vector engine, Pinecone, pgvector, Weaviate, or Qdrant infrastructure detected in Terraform or Helm values.
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns found.
- **Agent Evaluation:** No Ragas, DeepEval, or custom evaluation harness detected.
- **Shopping Assistant:** The `shoppingAssistantService` is referenced in `main.go` and `handlers.go` as an external HTTP service (`chatBotHandler` proxies requests to `SHOPPING_ASSISTANT_SERVICE_ADDR`), but this is a separate microservice — no AI framework is embedded in the frontend itself. The shopping assistant service is disabled by default in Helm values (`shoppingAssistantService.create: false`).

#### Application Domain and Potential AI Use Cases

As an e-commerce frontend serving the Online Boutique UI, the application has strong potential for AI integration:

1. **Product Recommendations Enhancement** — The current recommendation service returns basic product suggestions. An Amazon Bedrock-powered agent could provide personalized, context-aware recommendations using natural language understanding of user browsing patterns.
2. **Shopping Assistant (Native)** — Rather than proxying to an external service, embed Amazon Bedrock directly into the frontend to power the existing `/assistant` and `/bot` chat endpoints with a native Go integration.
3. **Product Search** — Enable natural language product search ("I need a warm hat for winter hiking") by indexing the product catalog into a vector database and using Amazon Bedrock for semantic search.
4. **Customer Support Agent** — Build an agent that handles common customer queries (order status, shipping estimates, returns) by composing the existing gRPC service calls as tools.

#### Recommended AI Services

Based on preferences (prefer: Bedrock, EKS):

- **Amazon Bedrock** — Foundation model access for the shopping assistant, product recommendations, and natural language search. Use Bedrock's tool-use capability to invoke existing gRPC services as agent tools.
- **Amazon Bedrock AgentCore** — Managed agent runtime for deploying AI agents alongside the frontend on EKS.
- **Amazon OpenSearch Service** (vector engine) — Vector database for product catalog embeddings, enabling semantic product search.
- **Amazon Bedrock Knowledge Bases** — RAG infrastructure for indexing product documentation, FAQs, and store policies.

#### Foundation Requirements

Before AI integration, the following should be in place:

1. **API Surface** — Generate OpenAPI specs from the existing gRPC proto definitions (APP-Q5 gap). This enables AI agents to discover and invoke service endpoints as tools.
2. **Authentication** — Implement API authentication (SEC-Q3 gap) before exposing any AI-powered endpoints to users.
3. **Observability** — The existing OpenTelemetry tracing (OPS-Q1 = 3) provides a strong foundation. Extend it to capture AI agent interactions (model latency, token usage, tool invocations).

#### Learning Resources

- [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GKE Autopilot cluster is provisioned via Terraform (`google_container_cluster` with `enable_autopilot = true` in `terraform/main.tf`). The frontend is containerized using a multi-stage Dockerfile (golang:1.26.1-alpine builder → gcr.io/distroless/static runtime). Kubernetes Deployments define the workload in `kubernetes-manifests/frontend.yaml`. Helm chart provides templated deployment (`helm-chart/`). Skaffold orchestrates build and deploy. This is managed container orchestration — GKE Autopilot handles node provisioning, scaling, and patching. Currently GCP-native; migration to EKS would align with AWS preferences. |
| **Gap** | Infrastructure is GCP GKE, not AWS-native (EKS/ECS). No AWS managed compute resources defined. |
| **Recommendation** | Migrate from GKE Autopilot to Amazon EKS with managed node groups or Fargate profiles. Rewrite Terraform from `google_container_cluster` to `aws_eks_cluster` using Terraform (preferred). Use GitOps (ArgoCD or Flux) for deployment to EKS. |
| **Evidence** | `terraform/main.tf` (google_container_cluster), `kubernetes-manifests/frontend.yaml` (Deployment), `src/frontend/Dockerfile` (distroless base), `skaffold.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Redis is used for cart storage. Two modes exist: (1) In-cluster Redis deployed as a K8s Deployment (default, `cartDatabase.inClusterRedis.create: true` in Helm values), which is self-managed. (2) Google Cloud Memorystore (`google_redis_instance` in `terraform/memorystore.tf`), which is a managed Redis service — conditionally enabled via `var.memorystore`. When Memorystore is enabled, Redis version is pinned to `REDIS_7_0` with 1GB memory. The default configuration uses in-cluster self-managed Redis. |
| **Gap** | Default deployment uses in-cluster self-managed Redis. Managed Memorystore is optional, not the default. No AWS managed cache service (ElastiCache/MemoryDB) is configured. |
| **Recommendation** | Replace in-cluster Redis with Amazon ElastiCache for Redis (or Amazon MemoryDB for Redis for durability). Define via Terraform (preferred). Make managed cache the default, not optional. Consider Amazon DynamoDB (preferred) for cart storage to eliminate cache management entirely. |
| **Evidence** | `terraform/memorystore.tf` (google_redis_instance), `helm-chart/values.yaml` (cartDatabase section) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service is used. All request handling is linear: HTTP handler → gRPC calls → response rendering. The checkout flow (`placeOrderHandler` in `handlers.go`) calls the checkout service synchronously in a single request-response cycle. No Step Functions, Temporal, Camunda, or any workflow definition files found. |
| **Gap** | No workflow orchestration — all orchestration logic is hardcoded in HTTP handlers. The checkout flow is a synchronous chain of calls with no compensation, retry, or state management. |
| **Recommendation** | For the frontend BFF pattern, synchronous orchestration may be acceptable. However, as the application grows, consider AWS Step Functions for multi-step workflows like checkout (order → payment → inventory → shipping → notification). Define workflows in Terraform (preferred). |
| **Evidence** | `src/frontend/handlers.go` (placeOrderHandler — synchronous checkout), absence of workflow definitions in entire repository |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC. The frontend connects to 7 backend services via gRPC (`mustConnGRPC` in `main.go`). Every service call in `rpc.go` is a blocking request-response call. The ad service call has a 100ms timeout (`context.WithTimeout` in `getAd()`), but it's still synchronous. No SQS, SNS, EventBridge, Kafka, Kinesis, or any messaging/streaming infrastructure found in Terraform, K8s manifests, or Helm values. |
| **Gap** | No async messaging or streaming infrastructure. All communication is synchronous, creating tight coupling between the frontend and all 7 backend services. A slow or failing backend causes cascading delays in the frontend. |
| **Recommendation** | Introduce Amazon SQS or Amazon SNS for non-critical operations (ad fetching, recommendations). Use Amazon EventBridge for event-driven patterns between services. The ad service call (already has 100ms timeout) is an ideal candidate for async — fetch ads asynchronously and render when available. Define messaging infrastructure in Terraform (preferred). |
| **Evidence** | `src/frontend/main.go` (7 synchronous gRPC connections), `src/frontend/rpc.go` (all sync gRPC calls), absence of messaging infrastructure |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Network policies exist in `kustomize/components/network-policies/`. A default deny-all policy (`network-policy-deny-all.yaml`) blocks all ingress/egress by default — this is good baseline. However, the frontend-specific policy (`network-policy-frontend.yaml`) allows ALL ingress and ALL egress with empty `{}` rules, effectively bypassing the deny-all for the frontend pod. SecurityContext is well-configured: non-root user (UID 1000), `readOnlyRootFilesystem: true`, `drop: ALL` capabilities, `allowPrivilegeEscalation: false`. Network policies are an optional Skaffold profile (`network-policies`), not enabled by default. |
| **Gap** | Frontend network policy is overly permissive (allows all ingress/egress). Network policies are not enabled by default — they require explicit Skaffold profile activation. No VPC/subnet segmentation in Terraform (GKE manages this, but no explicit private networking config). |
| **Recommendation** | Tighten the frontend network policy: restrict ingress to only port 8080, restrict egress to only the specific backend service ports (3550, 7000, 7070, 8080, 50051, 5050, 9555). Enable network policies by default. When migrating to EKS, define VPC with private subnets, security groups, and network policies via Terraform (preferred). |
| **Evidence** | `kustomize/components/network-policies/network-policy-frontend.yaml` (permissive rules), `kustomize/components/network-policies/network-policy-deny-all.yaml` (good baseline), `kubernetes-manifests/frontend.yaml` (securityContext) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The frontend is exposed via a Kubernetes `LoadBalancer` Service (`frontend-external` in `kubernetes-manifests/frontend.yaml`) on port 80. No API Gateway, no Ingress controller with auth/throttling, no CloudFront distribution. The Helm chart supports an optional Istio VirtualService (`frontend.virtualService.create: false` by default), which would provide traffic management if enabled. The load balancer has no authentication, no rate limiting, no request validation. |
| **Gap** | Direct service exposure via raw LoadBalancer with no throttling, authentication, or request validation at the entry point. Istio VirtualService is available but disabled by default. |
| **Recommendation** | When migrating to EKS, deploy an AWS Application Load Balancer (ALB) with the AWS Load Balancer Controller. Add an API Gateway (Amazon API Gateway or Kong on EKS) for throttling, authentication, and request validation. Use GitOps (preferred) to manage ingress configuration. Avoid exposing services directly via LoadBalancer. |
| **Evidence** | `kubernetes-manifests/frontend.yaml` (Service type: LoadBalancer), `helm-chart/values.yaml` (frontend.virtualService.create: false) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No HorizontalPodAutoscaler (HPA) is defined in Kubernetes manifests, Helm templates, or Kustomize overlays. GKE Autopilot provides node-level auto-scaling automatically, but pod-level scaling is not configured. The frontend Deployment has static resource requests (CPU: 100m, Memory: 64Mi) and limits (CPU: 200m, Memory: 128Mi) but no replica count or scaling policy. |
| **Gap** | No pod-level auto-scaling. The frontend cannot automatically scale up during traffic spikes or scale down during low demand. Relies entirely on GKE Autopilot's node-level scaling. |
| **Recommendation** | Add HPA to the frontend Deployment targeting CPU utilization (e.g., 70% target, min 2 replicas, max 10). When migrating to EKS, configure Kubernetes Metrics Server and HPA. Consider KEDA for event-driven scaling. Define scaling policies in Terraform/Helm (preferred). |
| **Evidence** | `kubernetes-manifests/frontend.yaml` (no HPA), `helm-chart/values.yaml` (static resource requests/limits), absence of HPA in any manifest |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found for any data store. The default in-cluster Redis is an ephemeral deployment with no persistence configured. The optional Memorystore Redis instance (`terraform/memorystore.tf`) has no explicit backup or PITR configuration. No AWS Backup plans, no S3 versioning, no EBS snapshot policies. Cart data stored in Redis is at risk of loss on pod restart or instance failure. |
| **Gap** | No backup or recovery capability for any data store. Cart state is ephemeral and will be lost on Redis restart. No documented or tested restore procedures. |
| **Recommendation** | When migrating to AWS, enable automated backups: use Amazon ElastiCache with automatic backups enabled, or Amazon MemoryDB (which provides durability by default). For the broader system, implement AWS Backup plans for all data stores. If using DynamoDB (preferred) for cart, PITR is built-in. Define backup configuration in Terraform (preferred). |
| **Evidence** | `terraform/memorystore.tf` (no backup_retention config), `helm-chart/values.yaml` (cartDatabase.inClusterRedis — no persistence), absence of backup configuration |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot is configured as a regional cluster (`var.region = "us-central1"` in `terraform/variables.tf`), which provides multi-AZ compute. However, the in-cluster Redis is a single Deployment with no replication — single point of failure. The optional Memorystore instance has no HA configuration (no `tier = "STANDARD_HA"` or `replica_count` in `terraform/memorystore.tf`). The frontend Deployment has no `topologySpreadConstraints` or pod anti-affinity rules. |
| **Gap** | Redis (in-cluster default) is single-instance with no replication. Memorystore has no HA tier. Frontend pods have no topology spread constraints for even AZ distribution. |
| **Recommendation** | When migrating to EKS, configure multi-AZ: use Amazon ElastiCache for Redis with Multi-AZ enabled, or DynamoDB (preferred — inherently multi-AZ). Add `topologySpreadConstraints` to the frontend Deployment for even AZ distribution. Deploy EKS across 3 AZs. Define HA configuration in Terraform (preferred). |
| **Evidence** | `terraform/main.tf` (regional GKE cluster), `terraform/memorystore.tf` (no HA config), `kubernetes-manifests/frontend.yaml` (no topology constraints) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Good IaC coverage across multiple tools: Terraform defines the GKE cluster and Memorystore (`terraform/`); Kubernetes manifests define all service deployments (`kubernetes-manifests/`); Helm chart provides templated, parameterized deployment (`helm-chart/`); Kustomize provides component overlays for optional features (network policies, Memorystore, Istio, etc.); Skaffold orchestrates build and deploy (`skaffold.yaml`). Primary infrastructure and application deployment are fully defined in code. |
| **Gap** | IaC is GCP-focused. No AWS Terraform modules exist. Some features are optional overlays (network policies, Memorystore) rather than default configuration. No Terraform state management configuration (backend, locking). |
| **Recommendation** | When migrating to AWS, rewrite Terraform to target AWS resources (EKS, ElastiCache/DynamoDB, VPC). Use Terraform with remote state backend (S3 + DynamoDB locking). Adopt GitOps (preferred) with ArgoCD or Flux for K8s manifest deployment to EKS. Convert optional overlays to default configuration. |
| **Evidence** | `terraform/` (6 files), `kubernetes-manifests/` (13 manifests), `helm-chart/` (Chart.yaml, values.yaml, templates/), `kustomize/` (15 component overlays), `skaffold.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides automated CI/CD: (1) PR workflow (`ci-pr.yaml`): Go unit tests → C# unit tests → Skaffold build + deploy to staging GKE → wait for pods → smoke test (load generator with zero-error check) → comment staging URL on PR. (2) Main branch workflow (`ci-main.yaml`): same test + deploy pipeline for pushes to main/release branches. Additional CI workflows: Helm chart validation, Terraform validation, Kustomize build validation, Kubevious manifest analysis. Concurrency control prevents duplicate PR runs. |
| **Gap** | No automated rollback on deployment failure. No canary or blue/green deployment strategy (direct kubectl apply via Skaffold). No security scanning in CI pipeline. Smoke test is basic (zero-error check on load generator, no specific endpoint validation). |
| **Recommendation** | Enhance CI/CD: add security scanning (Trivy for container images, govulncheck for Go dependencies). Implement GitOps (preferred) deployment with ArgoCD for automated rollback and drift detection. Add canary deployment strategy via Argo Rollouts on EKS. Avoid manual deployments (per preferences). |
| **Evidence** | `.github/workflows/ci-pr.yaml` (PR pipeline), `.github/workflows/ci-main.yaml` (main pipeline), `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Go (1.25.0, toolchain 1.26.1) — one of the most mature cloud-native languages. Excellent container support (small static binaries), first-class gRPC support (`google.golang.org/grpc`), built-in concurrency (goroutines), strong standard library, and extensive cloud SDK ecosystem. The frontend uses Go with gorilla/mux for routing, logrus for structured logging, and OpenTelemetry for observability. |
| **Gap** | None — Go is a tier-1 cloud-native language. |
| **Recommendation** | No change needed. Go is well-suited for containerized microservices on EKS (preferred). Ensure Go version stays current (currently on 1.25/1.26, which is modern). |
| **Evidence** | `src/frontend/go.mod` (module definition, Go 1.25.0, toolchain go1.26.1), all `.go` source files |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The frontend is part of the Online Boutique microservices architecture. It communicates with 7+ independently deployable backend services via gRPC: `productcatalogservice`, `currencyservice`, `cartservice`, `recommendationservice`, `checkoutservice`, `shippingservice`, `adservice`, plus the optional `shoppingassistantservice`. Each service has its own Dockerfile, K8s Deployment, and build artifact in `skaffold.yaml` (11 total artifacts). The frontend itself serves as a Backend-For-Frontend (BFF) — it's a single deployable unit that aggregates backend calls and renders HTML. Internally, the frontend has reasonable module separation (`handlers.go`, `rpc.go`, `middleware.go`, `money/`, `validator/`), but no sub-service decomposition. |
| **Gap** | The frontend BFF aggregates all UI concerns into a single service. While this is appropriate for the current scale, the frontend combines product browsing, cart management, checkout, recommendations, and ad rendering in one deployable. No shared database coupling — all data access is via gRPC. |
| **Recommendation** | The current BFF pattern is appropriate for this frontend. No decomposition is needed. If the frontend grows significantly, consider splitting into domain-specific micro-frontends. The microservices architecture is well-structured — maintain clear service boundaries and independent deployability. |
| **Evidence** | `src/frontend/main.go` (7 gRPC service connections), `src/frontend/rpc.go` (centralized service calls), `kubernetes-manifests/` (13 separate service manifests), `skaffold.yaml` (11 build artifacts) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC request-response. Every call in `rpc.go` blocks until the backend responds. The frontend makes sequential synchronous calls for each page render (e.g., `homeHandler` calls `getCurrencies()`, then `getProducts()`, then `getCart()`, then `chooseAd()` sequentially). The ad service call has a 100ms timeout via `context.WithTimeout`, but it's still a synchronous blocking call. No message queues, no event publishing, no async patterns detected. |
| **Gap** | 100% synchronous communication. No async patterns for any inter-service interaction. Sequential blocking calls increase page load latency — a slow currency service delays the entire home page render. Cascading failure risk: if any backend service is slow, the frontend blocks. |
| **Recommendation** | Introduce async patterns for non-critical calls: (1) Fetch ads and recommendations asynchronously using Go goroutines (within the same request). (2) For cross-request async, use Amazon SQS for operations that don't need immediate responses. (3) Use Amazon EventBridge for event-driven patterns between backend services. The existing gRPC framework supports streaming — consider server-side streaming for real-time updates. |
| **Evidence** | `src/frontend/rpc.go` (all sync gRPC calls), `src/frontend/handlers.go` (sequential blocking calls in homeHandler, productHandler), `src/frontend/main.go` (no message consumers) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All operations are synchronous request-response with no background processing. The checkout flow (`placeOrderHandler` in `handlers.go`) makes a single synchronous gRPC call to `checkoutservice.PlaceOrder()` and blocks until the order is complete. This call presumably orchestrates payment, inventory, and shipping — all while the user's HTTP request is waiting. No background job framework (no Celery, Bull, SQS workers), no async job queues, no status polling endpoints. |
| **Gap** | The checkout operation — which involves payment processing, inventory updates, and shipping setup — is handled as a synchronous HTTP request. If the checkout service is slow (payment gateway latency, inventory contention), the user's browser blocks. No async job processing for any operation. |
| **Recommendation** | Implement async checkout: (1) Submit order to Amazon SQS queue, (2) return immediately with order ID, (3) provide `/order/{id}/status` polling endpoint. Use AWS Step Functions for checkout workflow orchestration (payment → inventory → shipping → notification). For the frontend, this means adding a status polling UI component. Avoid blocking HTTP calls for operations that may exceed 5 seconds. |
| **Evidence** | `src/frontend/handlers.go` (placeOrderHandler — synchronous `PlaceOrder` gRPC call), absence of background workers or job queues |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. All routes are unversioned: `/`, `/product/{id}`, `/cart`, `/cart/empty`, `/setCurrency`, `/logout`, `/cart/checkout`, `/assistant`, `/product-meta/{ids}`, `/bot`. No `/v1/` or `/v2/` URL prefixes. No `Accept-Version` or custom version headers. No changelog or API compatibility documentation. The `baseUrl` environment variable allows a path prefix (e.g., `/shop/`) but this is for deployment path configuration, not versioning. |
| **Gap** | No versioning — any API change will break all consumers simultaneously. The `/product-meta/{ids}` and `/bot` endpoints return JSON and could be consumed by external clients or agents, making versioning important for backward compatibility. |
| **Recommendation** | Implement URL-based versioning: prefix all API routes with `/v1/` (e.g., `/v1/product/{id}`, `/v1/bot`). Document the API contract — generate OpenAPI specs from the gRPC proto definitions and HTTP routes. This is a prerequisite for the Move to AI pathway (agents need stable API contracts to use as tools). |
| **Evidence** | `src/frontend/main.go` (unversioned route definitions in `r.HandleFunc()` calls) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Service addresses are configured via environment variables (`PRODUCT_CATALOG_SERVICE_ADDR`, `CURRENCY_SERVICE_ADDR`, etc.) using `mustMapEnv()` in `main.go`. In Kubernetes deployment, these point to K8s DNS names (e.g., `productcatalogservice:3550`, `currencyservice:7000`). This is Kubernetes-native service discovery via CoreDNS — not hard-coded IPs, and addresses are dynamically resolved by the cluster DNS. The Helm chart supports optional Istio service mesh integration (`sidecars.create`, `frontend.virtualService`), which would provide advanced traffic management and service discovery. Istio Sidecar injection is annotated in the Deployment (`sidecar.istio.io/rewriteAppHTTPProbers: "true"`). |
| **Gap** | No full service mesh in default deployment (Istio is optional). Environment variables with K8s DNS names are functional but don't provide circuit breaking, retry policies, or traffic splitting at the mesh level. Service addresses are configuration-driven, not dynamically registered. |
| **Recommendation** | When migrating to EKS, deploy AWS App Mesh or Istio on EKS for service mesh capabilities (circuit breaking, retries, traffic splitting, mTLS). Use Kubernetes DNS for basic discovery and layer service mesh on top. The existing Istio annotations make migration to a mesh straightforward. |
| **Evidence** | `src/frontend/main.go` (mustMapEnv for 8 service addresses), `kubernetes-manifests/frontend.yaml` (env vars with K8s DNS names, Istio annotation), `helm-chart/values.yaml` (sidecars.create, virtualService) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The frontend serves static assets (images, CSS, icons) from the local filesystem (`./static/`) via `http.FileServer` in `main.go`. HTML templates are loaded from `./templates/` and compiled at startup. Both `static/` and `templates/` directories are copied into the container image via `COPY` commands in the Dockerfile. No S3 or managed object storage for unstructured data. No document parsing capabilities (Textract, Tika). |
| **Gap** | Static assets are bundled in the container image — not stored in managed object storage. Every deployment rebuilds the image even for static asset changes. No CDN for static content delivery. No document parsing pipeline. |
| **Recommendation** | Move static assets to Amazon S3 with CloudFront CDN for global delivery and cache optimization. This decouples static content from application deployments. Use S3 for any future unstructured data (product images, user uploads). Define S3 buckets and CloudFront distribution in Terraform (preferred). |
| **Evidence** | `src/frontend/main.go` (`http.FileServer(http.Dir("./static/"))`), `src/frontend/Dockerfile` (`COPY ./static ./static`, `COPY ./templates ./templates`) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The frontend has an excellent unified data access layer. All backend service interactions are centralized in a single file: `rpc.go`. This file defines all gRPC client functions: `getCurrencies()`, `getProducts()`, `getProduct()`, `getCart()`, `emptyCart()`, `insertCart()`, `convertCurrency()`, `getShippingQuote()`, `getRecommendations()`, `getAd()`. The `handlers.go` file calls only `rpc.go` functions — it never makes direct gRPC calls or accesses databases. The `frontendServer` struct in `main.go` holds all gRPC connections as fields, providing a clean dependency injection pattern. |
| **Gap** | None — the data access pattern is well-structured. One exception: `placeOrderHandler` in `handlers.go` directly creates a `CheckoutServiceClient` and calls `PlaceOrder()` instead of routing through `rpc.go`. This is a minor inconsistency. |
| **Recommendation** | Move the `PlaceOrder` call in `placeOrderHandler` to `rpc.go` for consistency. The existing unified data access pattern is excellent — maintain it as the application evolves. This pattern is ideal for wrapping service calls as AI agent tools. |
| **Evidence** | `src/frontend/rpc.go` (all service calls centralized), `src/frontend/handlers.go` (calls rpc.go functions), `src/frontend/main.go` (frontendServer struct with all gRPC connections) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Memorystore Redis instance explicitly pins `redis_version = "REDIS_7_0"` in `terraform/memorystore.tf`. Redis 7.0 is a current, supported version — not at or approaching EOL. However, the in-cluster Redis (default deployment mode) uses a public Docker Hub Redis image with no version pinning in the Helm values (`cartDatabase.inClusterRedis` — version depends on the `latest` tag or image repository default). |
| **Gap** | In-cluster Redis (default mode) has no explicit version pinning. The Helm values reference a public Redis image without specifying a tag, which could pull different versions across deployments. Version consistency is only guaranteed when using the optional Memorystore deployment. |
| **Recommendation** | Pin the in-cluster Redis image version in Helm values. When migrating to AWS, use Amazon ElastiCache for Redis with explicit engine version or DynamoDB (preferred — version management is automatic). Define database configuration in Terraform (preferred). |
| **Evidence** | `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`), `helm-chart/values.yaml` (cartDatabase.inClusterRedis — no version pin) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. The frontend does not directly interact with any SQL database. All data access is via gRPC service calls (`rpc.go`) which abstract the underlying data stores. Redis is used for cart storage (key-value operations only). No `.sql` files, no ORM configurations, no raw SQL execution anywhere in the frontend codebase. All business logic resides in the Go application layer. |
| **Gap** | None — the application is completely free of stored procedures and proprietary database coupling. |
| **Recommendation** | No change needed. Maintain all business logic in the application layer. This clean separation makes database migration straightforward — the frontend doesn't care what database backend services use. |
| **Evidence** | `src/frontend/rpc.go` (all data access via gRPC), absence of `.sql` files, absence of database driver imports in `go.mod` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent infrastructure-level audit logging is configured. Terraform contains no `aws_cloudtrail` or GCP Cloud Audit Logs resources. Application-level logging exists via logrus with JSON formatting (`JSONFormatter` in `main.go` and `deployment_details.go`), including request path, method, request ID, session ID, response status, and latency. However, this is application request logging, not infrastructure audit logging. |
| **Gap** | No infrastructure audit logging. No immutable log storage. No ability to trace administrative actions or API calls at the platform level. Application logs cover HTTP request flow but not infrastructure changes or security events. |
| **Recommendation** | When migrating to AWS, enable AWS CloudTrail with log file validation and S3 Object Lock for immutable storage. Configure CloudWatch Logs for centralized log aggregation. Define audit logging infrastructure in Terraform (preferred). Enable VPC Flow Logs for network traffic analysis on EKS. |
| **Evidence** | `terraform/main.tf` (no audit logging resources), `src/frontend/main.go` (logrus JSON logging — application level only), `src/frontend/deployment_details.go` (logger initialization) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured for any data store. The Memorystore Redis instance (`terraform/memorystore.tf`) has no `transit_encryption_mode` or `auth_enabled` parameters. The in-cluster Redis has no TLS or encryption configuration. No KMS keys (`aws_kms_key`) or encryption settings found in any Terraform file. No S3 buckets with encryption to evaluate. |
| **Gap** | No encryption at rest for cart data in Redis. No transit encryption for Redis connections. No KMS key management infrastructure. Cart data (product IDs, quantities, session IDs) is stored unencrypted. |
| **Recommendation** | When migrating to AWS, enable encryption at rest on all data stores: Amazon ElastiCache with at-rest encryption using customer-managed KMS keys, or DynamoDB (preferred — encryption at rest is enabled by default with AWS-managed keys). Enable in-transit encryption for all Redis/cache connections. Define KMS keys and encryption configuration in Terraform (preferred). |
| **Evidence** | `terraform/memorystore.tf` (no encryption config on google_redis_instance), absence of KMS resources in terraform/ |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No authentication on any API endpoint. The middleware chain in `main.go` applies only: (1) `otelhttp.NewHandler` — OpenTelemetry tracing, (2) `ensureSessionID` — cookie-based session ID assignment (UUID, not authentication), (3) `logHandler` — request logging. No auth middleware, no OAuth2, no JWT validation, no API key checks. All endpoints including `/cart/checkout` (which handles credit card data), `/bot` (AI chat), and `/product-meta/{ids}` (JSON API) are completely unauthenticated. The `sessionID` is a random UUID set via cookie — it identifies sessions but does not authenticate users. |
| **Gap** | All endpoints are open — anyone can place orders, modify carts, and access the chatbot without authentication. Credit card data is submitted over unauthenticated endpoints. No rate limiting prevents abuse. |
| **Recommendation** | Implement authentication: integrate with Amazon Cognito for user authentication (OAuth2/OIDC). Add JWT validation middleware to the Go handler chain. At minimum, add rate limiting via API Gateway. For the EKS migration, use ALB with Cognito integration for authentication at the entry point. Define Cognito user pool in Terraform (preferred). |
| **Evidence** | `src/frontend/main.go` (handler chain: otelhttp → ensureSessionID → logHandler — no auth), `src/frontend/middleware.go` (ensureSessionID — cookie UUID, not authentication) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. Session management is entirely cookie-based: `ensureSessionID` in `middleware.go` creates a random UUID and stores it in a `shop_session-id` cookie with 48-hour expiry. No Cognito, Okta, Ping, or any OIDC/SAML configuration. No user database or authentication flow. The application has no concept of "logged-in user" — all carts are tied to anonymous session IDs. An `ENABLE_SINGLE_SHARED_SESSION` env var exists for demo purposes, hardcoding a single session ID across all users. |
| **Gap** | No identity provider. No user accounts. No SSO capability. All sessions are anonymous. This prevents personalization, order history, and any authenticated user experience. |
| **Recommendation** | Integrate with Amazon Cognito as the centralized identity provider. Implement OIDC authentication flow (Cognito Hosted UI or custom UI). Map authenticated users to sessions for personalized cart, order history, and recommendations. Define Cognito resources in Terraform (preferred). |
| **Evidence** | `src/frontend/middleware.go` (ensureSessionID — random UUID cookie), `src/frontend/main.go` (cookieSessionID, cookieMaxAge), absence of identity provider configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated secrets management system is used. Configuration is via environment variables (`mustMapEnv()` in `main.go`) — these contain service addresses, not secrets. No hardcoded passwords, API keys, or tokens were found in the source code. However, gRPC connections use `insecure.NewCredentials()` — no TLS, no mutual authentication. No AWS Secrets Manager, HashiCorp Vault, or Kubernetes Secrets with external secret operator detected. The Kubernetes manifests define service addresses as plain-text env vars in the Deployment spec. |
| **Gap** | No secrets management system. gRPC connections are unencrypted (`insecure.NewCredentials()`). While no secrets currently need rotation (no API keys or database passwords in the frontend), the lack of a secrets management foundation means any future secrets (API keys for Bedrock, database credentials) would need to be added without infrastructure in place. |
| **Recommendation** | Implement AWS Secrets Manager for any sensitive configuration. Enable mTLS for gRPC connections (replace `insecure.NewCredentials()` with TLS credentials). Use the Kubernetes External Secrets Operator to sync AWS Secrets Manager into K8s Secrets on EKS. Define secrets infrastructure in Terraform (preferred). |
| **Evidence** | `src/frontend/main.go` (`grpc.WithTransportCredentials(insecure.NewCredentials())`), `kubernetes-manifests/frontend.yaml` (plain-text env vars), absence of secrets management tools |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong container hardening is in place: (1) Dockerfile uses `gcr.io/distroless/static` base image — minimal attack surface with no shell, no package manager, no unnecessary binaries. (2) Multi-stage build ensures build tools don't leak into the runtime image. (3) Kubernetes SecurityContext is comprehensive: `runAsNonRoot: true`, `runAsUser: 1000`, `fsGroup: 1000`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, `drop: ALL` capabilities, `privileged: false`. (4) Dedicated ServiceAccount (`frontend`) instead of default. However, no container image scanning (Trivy, ECR scanning) is configured. |
| **Gap** | No container image vulnerability scanning in CI/CD or at runtime. No automated patching strategy for base images. The Go builder image (`golang:1.26.1-alpine`) is pinned by digest (good), but there's no automated process to update it when security patches are released. |
| **Recommendation** | Add Trivy or Snyk container scanning to the CI/CD pipeline. When migrating to EKS, enable Amazon ECR image scanning. Consider using Bottlerocket OS for EKS worker nodes. Implement automated base image updates via Dependabot or Renovate (Renovate is already configured: `.github/renovate.json5`). |
| **Evidence** | `src/frontend/Dockerfile` (distroless/static base, multi-stage build, digest pinning), `kubernetes-manifests/frontend.yaml` (comprehensive securityContext), `.github/renovate.json5` (dependency update automation) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into the CI/CD pipeline. The GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) run only Go unit tests, C# tests, Skaffold build/deploy, and smoke tests. No SAST (SonarQube, Semgrep, CodeGuru), no DAST, no dependency vulnerability scanning (`govulncheck`, `nancy`), no container image scanning (Trivy, Snyk). No `.snyk` policy file. The `.github/renovate.json5` file provides dependency version updates but not vulnerability scanning. A `.github/SECURITY.md` file exists (security policy), but no automated enforcement. |
| **Gap** | No automated security scanning at any stage of the pipeline. Vulnerabilities in Go dependencies or in the distroless base image could reach production undetected. No security gate blocking deployments on critical findings. |
| **Recommendation** | Add security scanning to CI/CD: (1) `govulncheck` for Go vulnerability scanning in the code-tests job. (2) Trivy for container image scanning after Skaffold build. (3) Semgrep or CodeGuru Reviewer for SAST. (4) Configure security gates — block deployment if critical vulnerabilities are found. When migrating to AWS, integrate Amazon CodeGuru and Amazon Inspector. Define security scanning in GitHub Actions workflows. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (no security scanning steps), `.github/workflows/ci-main.yaml` (no security scanning), `.github/SECURITY.md` (policy exists but not automated) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry distributed tracing is well-implemented: (1) `otelhttp.NewHandler` wraps the entire HTTP handler chain, creating spans for every incoming request. (2) `otelgrpc.NewClientHandler()` instruments all outbound gRPC calls via `grpc.WithStatsHandler()`. (3) Trace context propagation is configured with `propagation.TraceContext{}` and `propagation.Baggage{}`. (4) OTLP gRPC exporter sends traces to a collector service (`COLLECTOR_SERVICE_ADDR`). (5) `AlwaysSample()` sampler ensures all requests are traced. Dependencies in `go.mod`: OpenTelemetry v1.42.0, otelgrpc v0.67.0, otelhttp v0.67.0. Tracing is conditional on `ENABLE_TRACING=1` env var. |
| **Gap** | Tracing is disabled by default (`ENABLE_TRACING` must be explicitly set to "1"). When disabled, no traces are exported. The `initStats()` function is a TODO stub — OpenTelemetry metrics are not implemented. |
| **Recommendation** | Enable tracing by default in production deployments. When migrating to AWS, export traces to AWS X-Ray via the ADOT (AWS Distro for OpenTelemetry) Collector on EKS. Implement the `initStats()` TODO to add OpenTelemetry metrics alongside traces. Define ADOT Collector as a DaemonSet on EKS via Helm/GitOps (preferred). |
| **Evidence** | `src/frontend/main.go` (initTracing, otelhttp.NewHandler, otelgrpc.NewClientHandler, propagation config), `src/frontend/go.mod` (OpenTelemetry dependencies) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking, no SLO monitoring configuration, no latency targets defined in code or configuration. The health check endpoint (`/_healthz`) returns "ok" with no SLO-aware health analysis. No CloudWatch composite alarms or SLO dashboards. |
| **Gap** | No formal definition of acceptable service levels. Without SLOs, there's no objective measure of whether the frontend is meeting user expectations for availability and latency. No error budget to guide the pace of change vs. reliability investment. |
| **Recommendation** | Define SLOs for the frontend: (1) Availability SLO: 99.9% of requests return non-5xx responses. (2) Latency SLO: p99 response time < 500ms for home page, < 1s for checkout. (3) Error budget: 0.1% of requests can fail per 30-day window. Implement SLO monitoring using Amazon CloudWatch SLO or Prometheus + Grafana on EKS. |
| **Evidence** | Absence of SLO definitions in any configuration, code, or documentation file |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The application logs contain structured request data (path, method, status, latency), but no custom metric emission for business events (orders placed, carts created, products viewed, conversion rates). The `initStats()` function in `main.go` is a TODO stub with comment "TODO(arbrown) Implement OpenTelemtry stats". OpenTelemetry metrics dependencies are in `go.mod` (`otel/metric v1.42.0`) but not used in code. |
| **Gap** | No business outcome metrics. Infrastructure metrics (CPU, memory) are available via K8s, but business metrics (orders per minute, cart abandonment rate, product view to purchase conversion) are not tracked. Decision-making about modernization investments lacks data. |
| **Recommendation** | Implement OpenTelemetry metrics (complete the `initStats()` TODO): (1) Counter for orders placed, carts created, products viewed. (2) Histogram for checkout duration. (3) Gauge for active sessions. Export metrics to Amazon CloudWatch via ADOT Collector on EKS. Build business dashboards in CloudWatch or Grafana. |
| **Evidence** | `src/frontend/main.go` (`initStats()` — TODO stub), `src/frontend/go.mod` (`otel/metric v1.42.0` — dependency present but unused) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configuration found. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration, no alert definitions in any configuration file. The application logs errors but does not trigger alerts. No composite alarms, no anomaly detection on error rates or latency. |
| **Gap** | No alerting at all. If the frontend starts returning errors or experiencing high latency, no one is notified. Issues are only discovered when users report problems or through manual log inspection. |
| **Recommendation** | Implement alerting: (1) CloudWatch alarms on EKS pod restart count, error rate, and p99 latency. (2) CloudWatch anomaly detection on request count and error rate. (3) PagerDuty or OpsGenie integration for on-call notification. (4) Composite alarms for SLO breach detection. Define alarms in Terraform (preferred). |
| **Evidence** | Absence of alerting configuration in any file (Terraform, K8s manifests, Helm, or CI/CD) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Skaffold deploys directly to GKE via `kubectl apply` (`deploy: kubectl: {}` in `skaffold.yaml`). This results in Kubernetes default rolling update behavior (25% maxUnavailable, 25% maxSurge by default). The CI pipeline (`ci-pr.yaml`, `ci-main.yaml`) runs `skaffold run` which builds images and applies manifests. No canary deployment, no blue/green, no traffic shifting. The Helm chart supports optional Istio VirtualService which could enable traffic splitting, but it's disabled by default. No Argo Rollouts, no CodeDeploy, no feature flags. |
| **Gap** | Direct-to-production rolling update with no staged rollout. All users get the new version simultaneously. No ability to detect regressions before full rollout. No automated rollback on failure. |
| **Recommendation** | Implement canary deployments: (1) Adopt ArgoCD with Argo Rollouts on EKS for canary analysis. (2) Route 5% of traffic to the new version, analyze error rates and latency, then progressively increase. (3) Automate rollback when canary metrics degrade. Use GitOps (preferred) for deployment — commit desired state to Git, ArgoCD reconciles. Avoid manual deployments (per preferences). |
| **Evidence** | `skaffold.yaml` (`deploy: kubectl: {}`), `.github/workflows/ci-pr.yaml` (`skaffold run`), `helm-chart/values.yaml` (virtualService.create: false) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Partial testing coverage: (1) Unit tests exist for `validator` package (`validator_test.go` — 22 test cases covering input validation for add-to-cart, place-order, and set-currency) and `money` package (`money_test.go`). (2) Integration/smoke testing: CI deploys the entire application stack to GKE, runs the load generator (Locust), waits for 50+ requests, and checks for zero errors. This validates basic end-to-end functionality but doesn't test specific workflows or edge cases. No contract tests (e.g., gRPC contract testing between frontend and backend services). No specific endpoint validation beyond the load generator's generic traffic. |
| **Gap** | No targeted integration tests for critical user journeys (add to cart, checkout, currency conversion). Smoke test only checks for zero errors in aggregate — a specific endpoint could fail while others succeed, masking the issue. No gRPC contract tests to validate frontend-backend compatibility. |
| **Recommendation** | Add integration tests: (1) gRPC contract tests validating frontend ↔ backend proto compatibility. (2) HTTP endpoint tests for critical workflows (home → product → cart → checkout). (3) Use test containers for local integration testing. Run integration tests in CI before deployment. Consider Newman (Postman) collections for API endpoint testing. |
| **Evidence** | `src/frontend/validator/validator_test.go` (22 unit test cases), `src/frontend/money/money_test.go`, `.github/workflows/ci-pr.yaml` (smoke test via load generator) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no self-healing patterns found. No SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No markdown runbooks or YAML playbooks in the repository. Kubernetes liveness and readiness probes provide basic self-healing (pod restart on health check failure), but no application-level incident response automation. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common incidents (frontend unresponsive, backend service unavailable, Redis connection failure). No automated remediation. |
| **Recommendation** | Create runbooks for common incidents: (1) Frontend pod crash loop — check logs, verify backend connectivity, restart. (2) Backend service timeout — circuit breaker, fallback response. (3) Redis connection failure — fallback to degraded mode. Implement AWS Systems Manager runbooks in Terraform (preferred). Add self-healing: circuit breakers for gRPC calls, graceful degradation for non-critical services (ads, recommendations). |
| **Evidence** | `kubernetes-manifests/frontend.yaml` (liveness/readiness probes — basic self-healing), absence of runbook files, absence of incident automation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS file exists (`.github/CODEOWNERS`) but defines a single generic owner for the entire repository (`* @GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver`). No per-service observability ownership. No service-specific dashboards, no named alarm owners, no team-specific monitoring. No SLO definitions with team attribution. No CODEOWNERS entries for observability-specific files. |
| **Gap** | No observability ownership model. No one is specifically responsible for frontend service health, monitoring, or alerting. Without ownership, monitoring gaps emerge and alarms go unattended. |
| **Recommendation** | Define observability ownership: (1) Add CODEOWNERS entries for monitoring configurations (e.g., `monitoring/ @frontend-team`). (2) Create per-service CloudWatch dashboards with named team owners. (3) Define alarm ownership — each alarm maps to a team with on-call rotation. (4) Attribute SLOs to specific teams. |
| **Evidence** | `.github/CODEOWNERS` (generic owners for entire repo), absence of per-service observability configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes labels are present but minimal: `app: frontend` label on Deployments, Services, and ServiceAccounts. No cost allocation labels, no ownership labels, no environment labels in K8s manifests. Terraform resources have no tags — no `default_tags` in provider config, no tags on `google_container_cluster` or `google_redis_instance`. No tag enforcement policies. The Helm chart uses template-generated labels from Chart metadata, but no custom business tags. |
| **Gap** | No cost allocation tags for tracking per-service spend. No ownership tags for identifying responsible teams during incidents. No environment tags for distinguishing production/staging. When migrating to AWS, untagged resources make cost attribution and blast radius analysis impossible. |
| **Recommendation** | Implement tagging strategy: (1) Add `default_tags` in Terraform AWS provider with `Environment`, `Team`, `Service`, `CostCenter`. (2) Add corresponding Kubernetes labels to all resources. (3) Enforce tagging via AWS Config required-tags rule. (4) Activate cost allocation tags in AWS Billing. Define tagging governance in Terraform (preferred). |
| **Evidence** | `kubernetes-manifests/frontend.yaml` (only `app: frontend` label), `terraform/main.tf` (no tags on resources), `helm-chart/values.yaml` (no custom tags) |

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to AI** (Triggered) | [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

No other pathways were triggered. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/frontend/main.go` | INF-Q1, INF-Q4, INF-Q6, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, SEC-Q1, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q3 | Main application entry point: gRPC connections, HTTP router, middleware chain, tracing config, env var mapping |
| `src/frontend/rpc.go` | INF-Q4, APP-Q2, APP-Q3, DATA-Q2, DATA-Q4 | Centralized gRPC service call layer — all backend interactions |
| `src/frontend/handlers.go` | INF-Q3, APP-Q3, APP-Q4, DATA-Q2 | HTTP request handlers: home, product, cart, checkout, assistant, bot |
| `src/frontend/middleware.go` | SEC-Q3, SEC-Q4 | Session management (cookie UUID), request logging middleware |
| `src/frontend/Dockerfile` | INF-Q1, DATA-Q1, SEC-Q6 | Multi-stage build: golang:1.26.1-alpine → distroless/static |
| `src/frontend/go.mod` | APP-Q1, OPS-Q1, OPS-Q3 | Go module definition, dependencies (OpenTelemetry, gRPC, logrus) |
| `src/frontend/deployment_details.go` | SEC-Q1 | Logger initialization, GCP metadata server integration |
| `src/frontend/validator/validator_test.go` | OPS-Q6 | 22 unit test cases for input validation |
| `src/frontend/money/money_test.go` | OPS-Q6 | Unit tests for money arithmetic operations |
| `terraform/main.tf` | INF-Q1, INF-Q9, INF-Q10, SEC-Q1, OPS-Q9 | GKE Autopilot cluster, kubectl apply deployment |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2 | Google Cloud Memorystore Redis instance (conditional) |
| `terraform/variables.tf` | INF-Q9 | Region, cluster name, Memorystore toggle variables |
| `kubernetes-manifests/frontend.yaml` | INF-Q1, INF-Q5, INF-Q6, INF-Q7, INF-Q9, APP-Q6, SEC-Q5, SEC-Q6, OPS-Q7, OPS-Q9 | Deployment, Service, ServiceAccount with securityContext |
| `helm-chart/values.yaml` | INF-Q2, INF-Q6, INF-Q7, APP-Q6, DATA-Q3, OPS-Q5 | Helm values: service configs, cart database, feature toggles |
| `skaffold.yaml` | INF-Q1, INF-Q10, APP-Q2, OPS-Q5 | Multi-service build and deploy orchestration |
| `.github/workflows/ci-pr.yaml` | INF-Q11, SEC-Q7, OPS-Q5, OPS-Q6 | PR CI pipeline: tests, deploy, smoke test |
| `.github/workflows/ci-main.yaml` | INF-Q11, SEC-Q7 | Main branch CI pipeline: tests, deploy, smoke test |
| `.github/workflows/helm-chart-ci.yaml` | INF-Q11 | Helm chart validation CI |
| `.github/workflows/terraform-validate-ci.yaml` | INF-Q11 | Terraform validation CI |
| `.github/CODEOWNERS` | OPS-Q8 | Generic repository ownership (no per-service owners) |
| `.github/SECURITY.md` | SEC-Q7 | Security policy (not automated) |
| `.github/renovate.json5` | SEC-Q6 | Dependency update automation configuration |
| `kustomize/components/network-policies/network-policy-frontend.yaml` | INF-Q5 | Frontend network policy (overly permissive) |
| `kustomize/components/network-policies/network-policy-deny-all.yaml` | INF-Q5 | Default deny-all network policy (good baseline) |
