# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | checkoutservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | go, grpc, orchestrator, critical-path |
| **Context** | Go gRPC service orchestrating the checkout workflow — calls cart, product, shipping, currency, payment, and email services. |
| **Overall Score** | 2.16 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.27 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 3.50 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **2.16 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No audit logging (CloudTrail or equivalent) configured in IaC or application | No forensic analysis capability; compliance gap for production workloads |
| 2 | SEC-Q3: API Authentication | 1 | All gRPC connections use `insecure.NewCredentials()` — no TLS, no per-request auth | Any service in the cluster can call checkoutservice without authentication; lateral movement risk |
| 3 | INF-Q3: Workflow Orchestration | 1 | PlaceOrder is a hardcoded sequential workflow with no orchestration service | No visibility into workflow state; no retry/compensation logic; difficult to modify checkout flow |
| 4 | INF-Q4: Async Messaging | 1 | 100% synchronous gRPC — no async messaging or event-driven patterns | Tight coupling between all 6 downstream services; cascading failure risk on any service timeout |
| 5 | OPS-Q5: Deployment Strategy | 1 | Skaffold + kubectl apply = direct-to-production with no staged rollout | No ability to catch regressions before full user impact; high-risk deployments for P0 critical-path service |

---

## Quick Agent Wins

### API-Aware Agent (gRPC Tool Discovery)

- **Prerequisite:** APP-Q5 = 2 (≥ 2). Protobuf service definitions exist in `protos/demo.proto` with well-typed request/response schemas for 9 gRPC services including CheckoutService.PlaceOrder.
- **What it enables:** An Amazon Bedrock-powered agent that discovers and invokes existing gRPC endpoints as tools, using protobuf definitions as the tool interface schema. The agent can orchestrate test orders, query product catalogs, and validate checkout flows through natural language.
- **Additional steps:** Generate gRPC reflection metadata or OpenAPI transcoding from proto definitions. Consider deploying gRPC-gateway to expose REST endpoints for easier agent integration.
- **Effort:** Medium

### DevOps Agent (GitOps Pipeline Integration)

- **Prerequisite:** INF-Q11 = 3 (≥ 2). GitHub Actions CI/CD pipeline exists with code-tests, deployment-tests, and smoke tests across multiple workflows (ci-pr.yaml, ci-main.yaml, helm-chart-ci.yaml, terraform-validate-ci.yaml).
- **What it enables:** An Amazon Bedrock-powered DevOps agent that triggers deployments, checks build status, manages releases, and automates GitOps workflows. Aligns with the `prefer: ["gitops"]` preference for declarative, agent-orchestrated deployment pipelines.
- **Additional steps:** Migrate from Skaffold+kubectl to a GitOps operator (Argo CD or Flux) on EKS to provide a declarative API surface the agent can interact with.
- **Effort:** Medium

### Observability Agent (Trace Correlation and Root Cause Analysis)

- **Prerequisite:** OPS-Q1 = 3 (≥ 2). OpenTelemetry SDK v1.42.0 instrumented with OTLP gRPC exporter, both server and client gRPC handlers instrumented via `otelgrpc.NewServerHandler()` and `otelgrpc.NewClientHandler()`. TraceContext + Baggage propagation configured. Structured JSON logging via logrus with timestamp, severity, and message fields.
- **What it enables:** An Amazon Bedrock-powered observability agent that queries traces across the checkout workflow's 6 downstream service calls, correlates trace spans with structured logs, and suggests root causes for latency spikes or failures in the PlaceOrder flow.
- **Additional steps:** Enable tracing by default (currently gated behind `ENABLE_TRACING=1` env var). Export traces to AWS X-Ray or an OpenTelemetry-compatible backend. Add trace ID to log entries for full correlation.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — already a microservices architecture with independently deployable services |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3, Dockerfile and Kubernetes manifests exist — compute is already containerized on managed Kubernetes |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4, no commercial DB engines detected — Redis is open source |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 — Memorystore (managed Redis) option exists in Terraform |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but contextual guard: no data processing workloads exist in checkoutservice |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3 — IaC and CI/CD automation exist at sufficient levels |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks detected in go.mod or source code; no vector DB, RAG, or agent eval infrastructure |

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

No AI or agent framework usage was detected in the checkoutservice codebase:

- **AI/Agent Frameworks:** No imports of Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK found in `go.mod` or source code.
- **Vector Database Infrastructure:** No OpenSearch with vector engine, Pinecone, pgvector, Weaviate, or Qdrant detected.
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns found.
- **Agent Evaluation Frameworks:** No Ragas, DeepEval, or custom eval harness detected.

#### Application Domain and Potential AI Use Cases

As a P0 critical-path checkout orchestrator calling 6 downstream services, checkoutservice presents several high-value AI integration opportunities:

1. **Intelligent Order Validation** — Use Amazon Bedrock to detect anomalous orders (unusual quantities, suspicious patterns) before processing payment.
2. **Dynamic Shipping Optimization** — Use Bedrock to recommend optimal shipping options based on order characteristics and delivery preferences.
3. **Checkout Flow Observability Agent** — Use Bedrock-powered agents to monitor the PlaceOrder trace spans and auto-diagnose latency degradation across the 6-service call chain.
4. **Conversational Commerce** — The existing `shoppingAssistantService` (disabled in Helm) suggests intent for AI-powered shopping assistance.

#### Quick Wins

See the [Quick Agent Wins](#quick-agent-wins) section above for three immediately actionable agent opportunities based on existing infrastructure (gRPC APIs, CI/CD pipeline, OpenTelemetry tracing).

#### Recommended AI Services (aligned with preferences)

- **Amazon Bedrock** (preferred) — Foundation model access for intelligent order validation, anomaly detection, and conversational agents
- **Amazon Bedrock AgentCore** — Agent orchestration for multi-step checkout workflow monitoring and incident triage
- **Amazon Q Developer** — AI-powered development assistance for the Go codebase
- **Amazon OpenSearch Service** (vector engine) — If product search or recommendation enhancement is pursued

#### Foundation Requirements Before AI Integration

1. **API Surface** — Proto definitions exist but need REST transcoding or gRPC reflection for agent tool discovery
2. **Data Access** — Clean gRPC service interfaces (DATA-Q2 = 4) provide a solid foundation for agent-mediated data queries
3. **Observability** — OpenTelemetry tracing (OPS-Q1 = 3) enables AI-powered trace analysis, but must be enabled by default
4. **Security** — API authentication (SEC-Q3 = 1) must be addressed before agent integration — agents need authenticated, auditable access

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
| **Finding** | Compute runs on GKE Autopilot (managed Kubernetes) provisioned via Terraform (`terraform/main.tf`: `enable_autopilot = true`). The checkoutservice is containerized with a multi-stage Dockerfile using a distroless runtime image (`gcr.io/distroless/static`). Kubernetes Deployment manifests define the workload with resource requests/limits (100m/200m CPU, 64Mi/128Mi memory). Helm chart provides templated deployment. All 11+ services run as independent Kubernetes Deployments. |
| **Gap** | Infrastructure is GCP-native (GKE Autopilot). Migration to AWS would require re-platforming to EKS. No Fargate or Lambda usage. GKE Autopilot abstracts node management but the Terraform is GCP-specific. |
| **Recommendation** | Migrate to Amazon EKS (preferred per preferences) with Terraform EKS modules. Leverage EKS managed node groups or Fargate profiles for reduced ops overhead. Use existing Kubernetes manifests and Helm chart as-is with EKS — application layer is cloud-agnostic. Adopt GitOps (Argo CD or Flux on EKS) per preferences to replace Skaffold+kubectl. |
| **Evidence** | `terraform/main.tf` (GKE Autopilot), `src/checkoutservice/Dockerfile` (distroless), `kubernetes-manifests/checkoutservice.yaml` (Deployment+Service), `helm-chart/templates/checkoutservice.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The checkoutservice itself is stateless — no direct database. The broader system uses Redis for cart persistence. Terraform provides a managed option via Google Cloud Memorystore (`terraform/memorystore.tf`: `google_redis_instance` with `redis_version = "REDIS_7_0"`), conditionally enabled via `var.memorystore`. The default configuration uses in-cluster Redis (`helm-chart/values.yaml`: `cartDatabase.inClusterRedis.create: true`). |
| **Gap** | Default deployment uses in-cluster Redis (self-managed). Managed Memorystore is optional and requires explicit opt-in. In-cluster Redis lacks automated failover, backups, and patching. |
| **Recommendation** | When migrating to AWS, use Amazon ElastiCache for Redis or Amazon MemoryDB (preferred for durability). Use Terraform to provision with Multi-AZ and automated failover. For the checkoutservice specifically, consider DynamoDB (preferred per preferences) for order persistence if order history is needed. |
| **Evidence** | `terraform/memorystore.tf` (managed Redis option), `helm-chart/values.yaml` (cartDatabase section), `src/checkoutservice/go.mod` (no database drivers) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The PlaceOrder workflow in `main.go` is a hardcoded sequential chain: `getUserCart` → `prepOrderItems` (with `getProduct` + `convertCurrency` per item) → `quoteShipping` → `convertCurrency` (shipping) → `chargeCard` → `shipOrder` → `emptyUserCart` → `sendOrderConfirmation`. All orchestration logic is embedded directly in Go application code with no dedicated workflow service. There is no error compensation — if `shipOrder` fails after `chargeCard` succeeds, the payment is not reversed. |
| **Gap** | No dedicated workflow orchestration service. All checkout flow logic is hardcoded. No state management, no retry policies, no compensation/saga logic. If payment succeeds but shipping fails, there is no automated rollback or compensation. This is a significant gap for a P0 critical-path service handling financial transactions. |
| **Recommendation** | Migrate the PlaceOrder workflow to AWS Step Functions using Terraform (preferred). Model the checkout as a state machine with explicit error handling, compensation steps (refund on shipping failure), and retry policies. Step Functions provides visual workflow monitoring, audit trails, and built-in error handling. Alternatively, use Temporal on EKS for code-first workflow orchestration. |
| **Evidence** | `src/checkoutservice/main.go` (PlaceOrder method, lines ~170-215), `src/checkoutservice/main.go` (chargeCard, shipOrder, sendOrderConfirmation methods) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC. The checkoutservice makes 6 synchronous gRPC calls to downstream services (cart, product catalog, currency, payment, shipping, email) during a single PlaceOrder request. No SQS, SNS, EventBridge, Kafka, or any messaging infrastructure was found in the repository. The `sendOrderConfirmation` email call is synchronous despite being non-critical to the order response. |
| **Gap** | No async messaging or event-driven patterns. All communication is tightly coupled synchronous gRPC. A failure or latency spike in any of the 6 downstream services cascades directly to the PlaceOrder response. Email confirmation is synchronous despite being fire-and-forget. |
| **Recommendation** | Introduce Amazon SQS or Amazon EventBridge (via Terraform) for non-critical operations: email confirmation should be published as an event rather than called synchronously. Consider SNS for order event fan-out (order placed → email, analytics, inventory). For the checkout workflow, Step Functions integration (INF-Q3) would naturally introduce async patterns. Use GitOps to manage messaging infrastructure alongside application deployments. |
| **Evidence** | `src/checkoutservice/main.go` (all gRPC client calls use synchronous patterns), `go.mod` (no messaging SDK imports) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes ClusterIP services provide internal-only access. Network policies are available as a Kustomize component (`kustomize/components/network-policies/`) with per-service policies including a deny-all baseline. The Helm chart supports `networkPolicies.create`, `sidecars.create` (Istio), and `authorizationPolicies.create` for fine-grained access control. Istio service mesh manifests exist for ingress routing. Security contexts enforce non-root, read-only filesystem, and dropped capabilities. |
| **Gap** | Network policies are disabled by default (`networkPolicies.create: false` in values.yaml). Istio mTLS and authorization policies are also disabled by default. No VPC/subnet configuration in Terraform (GKE Autopilot uses default VPC). The actual network segmentation depends on opt-in Helm values. |
| **Recommendation** | On AWS EKS, deploy into private subnets with NAT gateway. Enable Kubernetes NetworkPolicies by default (set `networkPolicies.create: true`). Consider AWS App Mesh or Istio on EKS for mTLS between services. Use Terraform to define VPC, private subnets, and security groups with least-privilege rules. Enable AuthorizationPolicies for service-to-service access control. |
| **Evidence** | `kubernetes-manifests/checkoutservice.yaml` (ClusterIP, securityContext), `helm-chart/values.yaml` (networkPolicies, sidecars, authorizationPolicies toggles), `kustomize/components/network-policies/` (per-service policies), `istio-manifests/` (Gateway, VirtualService) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The frontend service has a LoadBalancer type Service (`frontend-external`) exposing the application externally. Istio Gateway (`istio-manifests/frontend-gateway.yaml`) provides ingress routing to the frontend with VirtualService rules. The checkoutservice is internal-only (ClusterIP on port 5050) — it is not directly exposed. |
| **Gap** | No API Gateway with throttling, authentication, or request validation. The Istio Gateway provides basic HTTP routing but no rate limiting or auth enforcement at the ingress layer. No request validation before traffic reaches the frontend. |
| **Recommendation** | On AWS, deploy an Application Load Balancer (ALB) with AWS WAF for DDoS protection and rate limiting. For API management, consider Amazon API Gateway with gRPC support or use an Istio ingress gateway on EKS with rate limiting policies. Add request validation at the ingress layer before traffic reaches the frontend service. |
| **Evidence** | `istio-manifests/frontend-gateway.yaml` (Gateway + VirtualService), `kubernetes-manifests/checkoutservice.yaml` (ClusterIP Service), `helm-chart/values.yaml` (frontend.externalService: true) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot provides automatic node scaling based on pod resource requests. Resource requests and limits are defined for all services in Kubernetes manifests and Helm values (checkoutservice: 100m-200m CPU, 64Mi-128Mi memory). However, no Horizontal Pod Autoscaler (HPA) is configured for any service — all deployments use the default replica count of 1. |
| **Gap** | No HPA configured — pod count is static at 1 replica. GKE Autopilot scales nodes, not pods. For a P0 critical-path service handling checkout transactions, a single replica with no auto-scaling is a significant availability risk during traffic spikes. |
| **Recommendation** | On EKS (preferred), configure HPA for checkoutservice based on CPU utilization or custom metrics (e.g., gRPC request rate). Set minimum replicas to 2+ for the P0 checkout service. Use Karpenter on EKS for efficient node auto-scaling. Define scaling policies in Terraform/Helm values and manage via GitOps. |
| **Evidence** | `kubernetes-manifests/checkoutservice.yaml` (resource requests/limits, no HPA), `helm-chart/values.yaml` (checkoutService.resources), `terraform/main.tf` (GKE Autopilot) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration was found for any data store. The in-cluster Redis (default deployment) has no persistence configuration, backup schedule, or snapshot policy. The Memorystore Redis instance (when enabled) does not have backup configuration in Terraform. No AWS Backup plans, no S3 versioning, no EBS snapshot policies. No documented restore procedures. |
| **Gap** | No backup or recovery configuration. Cart data in Redis is volatile — a Redis pod restart loses all cart state. For a P0 service, this means customer checkout sessions can be lost during any infrastructure event. No disaster recovery plan. |
| **Recommendation** | On AWS, configure automated backups for ElastiCache/MemoryDB with defined retention periods. Enable PITR where supported. Use AWS Backup for centralized backup management via Terraform. Document and test restore procedures. For cart data specifically, consider DynamoDB (preferred per preferences) which provides automated backups and PITR natively. |
| **Evidence** | `terraform/memorystore.tf` (no backup config), `helm-chart/values.yaml` (cartDatabase: no persistence config), absence of any backup-related resources in IaC |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot is regional by default (spans multiple zones in `us-central1`). However, all Kubernetes Deployments default to 1 replica — a single pod failure takes down the service. The in-cluster Redis is a single replica with no replication or failover. No explicit pod disruption budgets (PDBs) are defined. Memorystore Redis (when enabled) is single-zone (`memory_size_gb = 1`, no `replica_count`). |
| **Gap** | Single replica deployments for all services including the P0 checkout service. No pod disruption budgets. Redis has no replication. A single AZ failure or pod eviction takes down checkout capability. |
| **Recommendation** | On EKS, set minimum 2 replicas for checkoutservice with pod anti-affinity to spread across AZs. Add PodDisruptionBudgets (minAvailable: 1). Use ElastiCache with Multi-AZ and automatic failover. Define topology spread constraints in Helm values. Manage all HA configuration via Terraform and GitOps. |
| **Evidence** | `kubernetes-manifests/checkoutservice.yaml` (no replicas specified = default 1), `terraform/main.tf` (regional GKE), `terraform/memorystore.tf` (single instance, no replica) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Terraform defines the GKE cluster, Memorystore Redis, and GCP API enablement (`terraform/main.tf`, `memorystore.tf`, `providers.tf`, `variables.tf`). Kubernetes manifests define all application deployments, services, and service accounts. Helm chart provides templated, parameterized deployment. Kustomize overlays support environment-specific customization (memorystore, network-policies, service-mesh, branding). Skaffold orchestrates build+deploy. Multiple CI workflows validate Terraform, Helm, and Kustomize. |
| **Gap** | Terraform uses `null_resource` with `local-exec` for `kubectl apply` — this is an anti-pattern that breaks Terraform state management. No Terraform state backend configuration (no S3/GCS backend). Deployment relies on Skaffold imperative commands rather than GitOps declarative reconciliation. Some infrastructure aspects (monitoring, alerting, backup) are not in IaC. |
| **Recommendation** | Migrate to AWS with Terraform EKS modules (preferred). Replace `null_resource` kubectl commands with proper Kubernetes provider or ArgoCD/Flux GitOps (preferred per preferences). Configure Terraform state backend (S3 + DynamoDB for locking). Extend IaC to cover monitoring, alerting, and backup configuration. |
| **Evidence** | `terraform/` (main.tf, memorystore.tf, providers.tf, variables.tf), `kubernetes-manifests/` (12 YAML files), `helm-chart/` (Chart.yaml, values.yaml, 14 templates), `kustomize/` (base + 15 components), `skaffold.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides CI/CD automation with multiple workflows: `ci-pr.yaml` (code tests → deployment tests → smoke tests on PR), `ci-main.yaml` (same for main/release branches), `helm-chart-ci.yaml` (helm lint + template validation), `terraform-validate-ci.yaml` (terraform init + validate), `kustomize-build-ci.yaml` (kustomize build validation). PR workflow deploys to isolated GKE namespace, runs loadgenerator smoke tests checking for zero errors, and comments external IP on PR. Renovate (`renovate.json5`) automates dependency updates. |
| **Gap** | No automated rollback mechanism. Deployment uses Skaffold + kubectl apply — no canary, blue/green, or progressive rollout. No security scanning in CI pipeline (no SAST, no container scanning). Go unit tests run for shippingservice and productcatalogservice but NOT for checkoutservice specifically. Smoke tests are coarse-grained (zero-error check) not targeted. |
| **Recommendation** | On AWS, adopt GitOps with Argo CD on EKS (preferred per preferences) for declarative deployments with automated rollback. Add Argo Rollouts for canary/blue-green deployment strategy. Integrate security scanning (Amazon CodeGuru, Snyk, or Trivy for container scanning) into CI pipeline. Add checkoutservice-specific unit and integration tests to the Go test suite. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (code-tests, deployment-tests, smoke-test), `.github/workflows/ci-main.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `skaffold.yaml`, `.github/renovate.json5` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The checkoutservice is written in Go 1.25.0 (`go.mod`: `go 1.25.0`, `toolchain go1.26.1`). Go is a first-class cloud-native language with excellent support for containers (minimal binary size, static compilation), gRPC, Kubernetes, and microservices patterns. The broader microservices-demo uses multiple languages (Go, Python, C#, Java, Node.js) — each service uses the most appropriate language. |
| **Gap** | No significant gap. Go is a mature, well-supported language for cloud-native development with a rich ecosystem. |
| **Recommendation** | Continue with Go. When migrating to AWS, leverage Go's native AWS SDK v2 for service integrations. The static binary compilation and distroless container pattern are ideal for EKS workloads. |
| **Evidence** | `src/checkoutservice/go.mod` (Go 1.25.0), `src/checkoutservice/main.go` (Go source), `src/checkoutservice/Dockerfile` (golang:1.26.1-alpine builder) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application is a genuine microservices architecture with 11+ independently deployable services, each with its own Dockerfile, Kubernetes Deployment, Service, and ServiceAccount. The protobuf definitions in `protos/demo.proto` define 9 gRPC service interfaces (CartService, RecommendationService, ProductCatalogService, ShippingService, CurrencyService, PaymentService, EmailService, CheckoutService, AdService). Each service has separate source code directories, dependency manifests, and deployment configurations. |
| **Gap** | The checkoutservice as an orchestrator has inherent coupling to 6 downstream services — it cannot function if any dependency is unavailable. The `PlaceOrder` method creates a synchronous dependency chain. Services share a common protobuf definition file (`demo.proto`) rather than owning their own API contracts. The cart service shares a Redis database (not service-owned). |
| **Recommendation** | Evolve toward service-owned API contracts — each service should own its proto definitions rather than sharing a monolithic `demo.proto`. Consider introducing a Saga pattern (via Step Functions) for the checkout workflow to handle partial failures gracefully. Add circuit breakers (e.g., Go `hystrix-go` or built-in gRPC retry policies) to protect against cascading failures from downstream services. |
| **Evidence** | `protos/demo.proto` (9 service definitions), `kubernetes-manifests/` (12 separate deployment YAMLs), `skaffold.yaml` (11 build artifacts), `src/checkoutservice/main.go` (6 gRPC client connections) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | 100% of inter-service communication is synchronous gRPC. The PlaceOrder method makes 6+ synchronous gRPC calls in sequence: `getUserCart` (CartService), `prepOrderItems` (ProductCatalogService per item + CurrencyService per item), `quoteShipping` (ShippingService), `convertCurrency` (CurrencyService), `chargeCard` (PaymentService), `shipOrder` (ShippingService), `emptyUserCart` (CartService), `sendOrderConfirmation` (EmailService). No async patterns, no message queues, no event-driven communication anywhere in the codebase. |
| **Gap** | All communication is synchronous. A latency spike or failure in any downstream service directly impacts the PlaceOrder response time and availability. The email confirmation call is synchronous despite being non-critical to the order response — it blocks the response while sending a confirmation email. The `prepOrderItems` loop makes N synchronous calls (one per cart item) to ProductCatalogService and CurrencyService. |
| **Recommendation** | Introduce async patterns for non-critical operations: publish an "OrderPlaced" event to Amazon EventBridge or SNS (via Terraform/GitOps) and let email/analytics/inventory subscribers react asynchronously. For the cart item loop, consider batch gRPC calls or parallel goroutines. For the full checkout workflow, AWS Step Functions (INF-Q3) would naturally introduce async orchestration with retry and compensation. |
| **Evidence** | `src/checkoutservice/main.go` (PlaceOrder method — all synchronous gRPC calls), `go.mod` (no messaging SDK imports) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The PlaceOrder operation is fully synchronous end-to-end. The client blocks until all 6+ downstream service calls complete sequentially. There is no async job processing, no status polling, no callbacks. The operation involves financial transactions (payment charging) and physical fulfillment (shipping) — operations that can take variable time. The `prepOrderItems` loop makes N sequential calls for N cart items, creating O(N) latency scaling. |
| **Gap** | No async patterns for long-running operations. The PlaceOrder endpoint blocks for the entire checkout workflow duration. No job queue, no status tracking, no webhook callbacks. For large carts, latency scales linearly with item count due to sequential per-item calls. |
| **Recommendation** | Implement async order processing: PlaceOrder should return an order ID immediately and process the order asynchronously via AWS Step Functions or SQS workers. Provide a GetOrderStatus endpoint for status polling. Use DynamoDB (preferred) to track order state transitions. The `prepOrderItems` loop should use Go goroutines for parallel item processing. |
| **Evidence** | `src/checkoutservice/main.go` (PlaceOrder — sequential synchronous flow), `src/checkoutservice/main.go` (prepOrderItems — sequential loop with per-item gRPC calls) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | APIs are defined using Protocol Buffers (`protos/demo.proto`) which provide strong contract typing and backward-compatible field addition. The protobuf package is `hipstershop` with no version qualifier. The generated gRPC code includes full method names (e.g., `/hipstershop.CheckoutService/PlaceOrder`). Protobuf's field numbering provides implicit backward compatibility for additive changes. |
| **Gap** | No explicit versioning strategy. The protobuf package name (`hipstershop`) has no version suffix (no `v1`, `v2`). No API versioning scheme documented. Breaking changes (field renaming, type changes, message restructuring) would affect all consumers simultaneously. No API changelog or deprecation process. |
| **Recommendation** | Adopt explicit API versioning in protobuf package names (e.g., `hipstershop.checkout.v1`). Maintain backward compatibility guarantees within a version. Document a deprecation policy for API versions. Use buf.build for protobuf linting, breaking change detection, and API governance. |
| **Evidence** | `protos/demo.proto` (package `hipstershop`, no version), `src/checkoutservice/genproto/demo_grpc.pb.go` (generated method names) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service addresses are resolved through Kubernetes DNS via environment variables. The checkoutservice reads 6 service addresses from environment variables (`SHIPPING_SERVICE_ADDR`, `PRODUCT_CATALOG_SERVICE_ADDR`, `CART_SERVICE_ADDR`, `CURRENCY_SERVICE_ADDR`, `EMAIL_SERVICE_ADDR`, `PAYMENT_SERVICE_ADDR`) set to Kubernetes DNS names (e.g., `productcatalogservice:3550`) in the Kubernetes manifest. Kubernetes DNS provides basic service discovery within the cluster. |
| **Gap** | Service addresses are configured as static environment variables — not truly dynamic service discovery. Adding a new service or changing a port requires updating environment variables in the Kubernetes manifest and redeploying. No service registry, no API catalog, no service mesh-based discovery. Istio sidecars (when enabled) would provide dynamic routing but are disabled by default. |
| **Recommendation** | On EKS, enable a service mesh (Istio or AWS App Mesh) for dynamic service discovery, traffic management, and mTLS. Use Helm values to configure service names dynamically. Consider AWS Cloud Map for service discovery across namespaces. Enable Istio sidecars by default (`sidecars.create: true`) to leverage existing service mesh configurations in the Helm chart. |
| **Evidence** | `src/checkoutservice/main.go` (mustMapEnv for 6 service addresses), `kubernetes-manifests/checkoutservice.yaml` (env vars with Kubernetes DNS names), `helm-chart/templates/checkoutservice.yaml` (Helm-templated service names), `helm-chart/values.yaml` (sidecars.create: false) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The checkoutservice is a stateless orchestrator with no direct data storage. It delegates all data operations to downstream services via gRPC (cart items from CartService, product data from ProductCatalogService). The broader system stores product images referenced by URL in the product catalog. No unstructured data (documents, files, images) is directly managed by checkoutservice. |
| **Gap** | No order history or order document storage. Completed orders are not persisted — the OrderResult is returned to the caller and sent via email but not stored in any data store. No S3 or object storage for order receipts, invoices, or audit records. |
| **Recommendation** | On AWS, store order records in DynamoDB (preferred per preferences) for structured order data. Store order receipts and invoices in S3 with intelligent tiering. Consider Amazon Textract for any future document processing needs (e.g., parsing uploaded shipping labels). |
| **Evidence** | `src/checkoutservice/main.go` (PlaceOrder returns OrderResult but does not persist it), `go.mod` (no storage SDK imports) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All data access is through well-defined gRPC service interfaces. The checkoutservice has zero direct database connections — it uses gRPC clients to CartService (cart data), ProductCatalogService (product data), CurrencyService (exchange rates), PaymentService (payment processing), ShippingService (shipping quotes), and EmailService (notifications). Each service owns its data and exposes it through typed protobuf contracts. |
| **Gap** | No significant gap. The checkoutservice follows a clean pattern of delegating data access to service-owned APIs. |
| **Recommendation** | Maintain this pattern when migrating to AWS. The clean gRPC interfaces make it straightforward to replace backend implementations (e.g., CartService can switch from Redis to DynamoDB) without changes to checkoutservice. Consider adding an API catalog (e.g., Amazon API Gateway with gRPC) for discoverability. |
| **Evidence** | `src/checkoutservice/main.go` (6 gRPC client connections, no database imports), `go.mod` (no database driver dependencies), `protos/demo.proto` (typed service contracts) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Redis version is explicitly pinned at `REDIS_7_0` in Terraform's Memorystore configuration (`terraform/memorystore.tf`). Redis 7.0 is a current, supported version (not EOL). The in-cluster Redis deployment uses the public Docker Hub Redis image (`helm-chart/values.yaml`: `cartDatabase.inClusterRedis.publicRepository: true`) but the specific version tag is not pinned in the Helm values. |
| **Gap** | In-cluster Redis image version is not explicitly pinned — it may pull `latest` which introduces unpredictability. Only the Memorystore (managed) path has an explicit version pin. The in-cluster Redis (default path) lacks version governance. |
| **Recommendation** | Pin the in-cluster Redis image to a specific version tag in Helm values. On AWS, use ElastiCache or MemoryDB with explicit engine version pinning in Terraform. Monitor Redis EOL timelines and plan upgrades proactively. |
| **Evidence** | `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`), `helm-chart/values.yaml` (cartDatabase.inClusterRedis — no version pin) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found anywhere in the codebase. All business logic resides in Go application code. The checkoutservice has no direct database interaction — all data access is through gRPC service interfaces. The money calculation logic (`money/money.go`) is implemented in Go, not as database functions. Redis (used by CartService) is a key-value store with no stored procedure capability. |
| **Gap** | No gap. All business logic is in the application layer. |
| **Recommendation** | Maintain this pattern. When designing new data stores on AWS (e.g., DynamoDB for order history), keep all business logic in the application layer. Avoid DynamoDB transactions that embed business rules in conditional expressions. |
| **Evidence** | `src/checkoutservice/main.go` (all business logic in Go), `src/checkoutservice/money/money.go` (money calculations in Go), `go.mod` (no database drivers), absence of any .sql files |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration found in Terraform or Kubernetes manifests. The Terraform configuration provisions a GKE cluster and Redis but does not configure GCP Cloud Audit Logs or any equivalent. No AWS CloudTrail resources. No application-level audit logging for financial transactions (payment charges, order placements). The application uses structured JSON logging via logrus but only for operational messages, not audit events. |
| **Gap** | No audit logging for infrastructure actions or application transactions. For a P0 service processing financial transactions (chargeCard), the absence of audit logging is a critical compliance and security gap. No immutable log storage. No ability to trace who did what or reconstruct events after an incident. |
| **Recommendation** | On AWS, enable CloudTrail with log file validation and immutable storage (S3 Object Lock) via Terraform. Add application-level audit logging for financial transactions: log every PlaceOrder request with user_id, amount, transaction_id, and outcome to a dedicated audit log stream. Send audit logs to CloudWatch Logs with defined retention. Consider Amazon EventBridge for audit event streaming. |
| **Evidence** | `terraform/` (no audit logging resources), `src/checkoutservice/main.go` (logrus operational logging only — no structured audit events for transactions) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration found in Terraform or Kubernetes manifests. The Terraform Memorystore Redis instance does not configure `transit_encryption_mode` or customer-managed encryption keys. The in-cluster Redis has no encryption. No KMS keys defined. No encryption configuration on any data store. |
| **Gap** | No encryption at rest for any data store. Cart data (which may include user identifiers) is stored unencrypted in Redis. For a P0 service handling payment information (credit card data passes through this service), the absence of encryption is a significant security gap. |
| **Recommendation** | On AWS, enable encryption at rest on all data stores: ElastiCache with customer-managed KMS keys, DynamoDB with AWS-managed or customer-managed KMS keys (preferred per preferences), S3 with SSE-KMS. Define KMS keys in Terraform with appropriate key policies and rotation. Enable EKS secrets encryption with KMS envelope encryption. |
| **Evidence** | `terraform/memorystore.tf` (no encryption config), `helm-chart/values.yaml` (no encryption settings), absence of KMS key resources in IaC |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All gRPC connections use `grpc.WithTransportCredentials(insecure.NewCredentials())` in `main.go` — no TLS, no mTLS, no encryption in transit. No authentication middleware on the server side. No OAuth2, JWT, or API key validation. The gRPC health check server is registered without any authentication. Istio AuthorizationPolicies are available in the Helm chart (`authorizationPolicies.create`) but disabled by default. When enabled, the AuthorizationPolicy restricts `/hipstershop.CheckoutService/PlaceOrder` to the frontend service account — but this is opt-in. |
| **Gap** | All inter-service communication is unencrypted and unauthenticated. Any pod in the cluster can call any gRPC endpoint without identity verification. Credit card information passes through insecure gRPC channels from frontend → checkoutservice → paymentservice. This is a critical security gap for a payment-processing service. |
| **Recommendation** | On EKS, enable Istio mTLS (STRICT mode) for all service-to-service communication — this provides both encryption in transit and mutual authentication. Enable AuthorizationPolicies by default (`authorizationPolicies.create: true`) to enforce service identity-based access control. For external API access, use Amazon API Gateway with Cognito authorizers or JWT validation. Replace `insecure.NewCredentials()` with proper TLS credentials. |
| **Evidence** | `src/checkoutservice/main.go` (`grpc.WithTransportCredentials(insecure.NewCredentials())`), `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy — disabled by default) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration found. Kubernetes ServiceAccounts are created for each service (`kubernetes-manifests/checkoutservice.yaml`: ServiceAccount), but these are Kubernetes-internal identities with no external IdP federation. No Cognito, Okta, OIDC, or SAML configuration. The Helm chart supports ServiceAccount annotations for GKE Workload Identity (`serviceAccounts.annotations` — for cloud provider IAM binding) but this is not configured for checkoutservice. |
| **Gap** | No centralized identity management. Service identities are Kubernetes-internal only. No SSO, no federated identity, no external IdP. For a P0 critical-path service, the lack of strong identity management means there is no centralized audit trail of which services are calling which endpoints. |
| **Recommendation** | On AWS EKS, configure IAM Roles for Service Accounts (IRSA) to bind Kubernetes ServiceAccounts to AWS IAM roles. Use Amazon Cognito for user identity if user authentication is needed at the frontend. For service-to-service identity, use Istio's SPIFFE-based identity with mTLS. Define IRSA configurations in Terraform. |
| **Evidence** | `kubernetes-manifests/checkoutservice.yaml` (ServiceAccount — no annotations), `helm-chart/values.yaml` (serviceAccounts — annotations empty), absence of any IdP configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Service addresses are configured via plain environment variables in Kubernetes manifests. No AWS Secrets Manager, no HashiCorp Vault, no external secrets management. The Memorystore Redis connection string is injected via a sed command in a `null_resource` (`terraform/memorystore.tf`) — not through a secrets manager. No secret rotation configured. No sensitive data (API keys, database credentials) is managed through a dedicated secrets system. The `COLLECTOR_SERVICE_ADDR` is also a plain environment variable. |
| **Gap** | No secrets management system. While the current configuration uses only service addresses (not truly secret), there is no infrastructure in place for managing actual secrets (API keys, database credentials, encryption keys) when they are introduced during AWS migration. No rotation, no access audit, no encryption of secrets at rest. |
| **Recommendation** | On AWS, adopt AWS Secrets Manager with automatic rotation via Terraform. Use External Secrets Operator on EKS to sync Secrets Manager values into Kubernetes Secrets. Store database credentials, API keys, and encryption keys in Secrets Manager. Enable audit logging for all secret access. Manage secrets infrastructure via GitOps. |
| **Evidence** | `kubernetes-manifests/checkoutservice.yaml` (plain env vars), `terraform/memorystore.tf` (sed-based connection string injection), `helm-chart/templates/checkoutservice.yaml` (env vars from Helm values) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Dockerfile uses a distroless base image (`gcr.io/distroless/static`) which has minimal attack surface — no shell, no package manager, no unnecessary binaries. Kubernetes security contexts are comprehensive: `runAsNonRoot: true`, `runAsUser: 1000`, `runAsGroup: 1000`, `fsGroup: 1000`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: ALL`, `privileged: false`. The Helm chart supports seccomp profiles (`seccompProfile.type: RuntimeDefault`). The builder image uses a pinned Go version with SHA256 digest (`golang:1.26.1-alpine@sha256:...`). |
| **Gap** | No vulnerability scanning (no AWS Inspector, no Snyk, no Trivy) on container images. No patching automation for the base image. Seccomp profiles are disabled by default (`seccompProfile.enable: false`). GKE Autopilot handles node patching but there is no explicit patching strategy for application containers. Renovate handles dependency updates but does not scan for known CVEs. |
| **Recommendation** | On AWS, enable Amazon ECR image scanning with enhanced scanning (Inspector). Integrate Trivy or Snyk container scanning into the CI pipeline. Enable seccomp profiles by default. Use ECR lifecycle policies for image cleanup. Consider Bottlerocket nodes on EKS for hardened node OS. Add a CVE scanning step to CI before deployment. |
| **Evidence** | `src/checkoutservice/Dockerfile` (distroless base, pinned digest), `kubernetes-manifests/checkoutservice.yaml` (securityContext), `helm-chart/values.yaml` (seccompProfile, securityContext settings), `.github/renovate.json5` (dependency updates) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Renovate (`renovate.json5`) is configured for automated dependency updates across Go, Python, pip-compile, and Kubernetes manifests — this provides passive dependency vulnerability management by keeping dependencies current. GitHub Actions runs unit tests and deployment tests. However, no active security scanning tools are integrated: no SAST (SonarQube, Semgrep, CodeGuru), no DAST, no container image scanning (Trivy, Snyk), no dependency vulnerability scanning (`govulncheck`, `nancy`). No security gates that block deployments on critical findings. |
| **Gap** | No active security scanning in CI/CD. Renovate keeps dependencies updated but does not detect known CVEs in current versions. No SAST for Go code (potential injection vulnerabilities, hardcoded secrets). No container scanning for the distroless image. No security gate to prevent vulnerable code from reaching production. |
| **Recommendation** | Add `govulncheck` to the Go test pipeline for dependency vulnerability detection. Integrate Amazon CodeGuru Reviewer for Go code analysis. Add Trivy container scanning as a CI step before image push. Add a security gate: fail the pipeline on critical or high severity findings. Consider OWASP ZAP for DAST if REST endpoints are added. Manage security tool configuration via GitOps. |
| **Evidence** | `.github/renovate.json5` (dependency updates), `.github/workflows/ci-pr.yaml` (tests but no security scanning), `.github/workflows/ci-main.yaml` (tests but no security scanning), absence of .snyk, .trivyignore, or security scanning configuration |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry is instrumented with comprehensive coverage. The go.mod includes OpenTelemetry SDK v1.42.0 (`go.opentelemetry.io/otel`), OTLP trace exporter (`otlptracegrpc`), and gRPC instrumentation (`otelgrpc v0.67.0`). Both server-side (`otelgrpc.NewServerHandler()`) and client-side (`otelgrpc.NewClientHandler()`) gRPC handlers are instrumented, providing automatic span creation for all incoming and outgoing gRPC calls. Trace context propagation is configured with `propagation.TraceContext{}` and `propagation.Baggage{}`. Traces are exported to an OTLP collector via gRPC (`COLLECTOR_SERVICE_ADDR`). The Helm chart supports enabling tracing via `googleCloudOperations.tracing`. |
| **Gap** | Tracing is disabled by default — it requires `ENABLE_TRACING=1` environment variable. The OpenTelemetry collector (`opentelemetryCollector.create: false`) is also disabled by default in Helm values. When disabled, no traces are generated. Stats/metrics are not yet implemented (TODO comment in `initStats()`). The sampler is `AlwaysSample()` which may cause overhead in production — no sampling strategy configured. |
| **Recommendation** | Enable tracing by default in production (set `ENABLE_TRACING=1` and `opentelemetryCollector.create: true`). On AWS, export traces to AWS X-Ray via the ADOT (AWS Distro for OpenTelemetry) collector on EKS. Configure a production-appropriate sampling strategy (e.g., 10% or parent-based sampling). Implement the TODO for OpenTelemetry metrics. Add trace ID to logrus log entries for log-trace correlation. |
| **Evidence** | `src/checkoutservice/main.go` (OpenTelemetry imports, initTracing(), otelgrpc handlers), `go.mod` (OpenTelemetry SDK v1.42.0), `helm-chart/values.yaml` (googleCloudOperations.tracing: false, opentelemetryCollector.create: false) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budgets, no SLO configuration files, no CloudWatch alarm definitions for latency percentiles. No formal definition of acceptable service levels for the checkout workflow. The readiness/liveness probes on the gRPC health check provide basic availability detection but not SLO measurement. |
| **Gap** | No SLOs defined for the P0 critical-path checkout service. Without SLOs, there is no objective measure of whether the checkout experience meets user expectations. No error budget tracking means no data-driven decision-making about reliability vs feature velocity trade-offs. |
| **Recommendation** | Define SLOs for checkoutservice: availability SLO (e.g., 99.95% successful PlaceOrder requests), latency SLO (e.g., p99 < 2s for PlaceOrder). On AWS, implement SLO monitoring using CloudWatch Metrics, Alarms, and SLO dashboards. Use the Application Signals feature in CloudWatch for automatic SLO tracking. Track error budgets and alert when budget consumption rate is high. Define SLOs in IaC via Terraform. |
| **Evidence** | Absence of SLO definitions in repository, absence of latency/error rate alarms, `kubernetes-manifests/checkoutservice.yaml` (health probes only) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application uses structured JSON logging via logrus with timestamp, severity, and message fields. Log messages include operational data like `user_id`, `user_currency`, and `transaction_id`. However, no custom metrics are published — no CloudWatch put_metric_data, no Prometheus metrics, no OpenTelemetry metrics (the `initStats()` function has a TODO comment). No business outcome tracking (order volume, conversion rate, average order value, payment success rate). |
| **Gap** | No business metrics. For a P0 checkout service, there is no visibility into business outcomes: order volume trends, payment success/failure rates, average order value, or revenue. Operations can only detect issues through log analysis, not metric-based monitoring. The OpenTelemetry metrics integration is explicitly marked as TODO. |
| **Recommendation** | Implement OpenTelemetry metrics (complete the TODO in `initStats()`): publish custom metrics for orders_placed, payment_success_rate, payment_failure_count, order_total_value, checkout_latency_by_step. On AWS, export metrics to CloudWatch via ADOT collector. Create CloudWatch dashboards for business KPIs. Use CloudWatch Contributor Insights for top-N analysis (top currencies, top error types). |
| **Evidence** | `src/checkoutservice/main.go` (`initStats()` — TODO comment, logrus JSON logging), `go.mod` (`go.opentelemetry.io/otel/metric v1.42.0` — imported but unused) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. No error rate monitoring, no latency percentile tracking. The liveness and readiness probes provide pod-level health checks but no application-level anomaly detection. |
| **Gap** | No alerting means that failures in the P0 checkout service may go undetected until users report issues. No anomaly detection for error rate spikes, latency degradation, or unusual traffic patterns. No integration with incident management systems. |
| **Recommendation** | On AWS, configure CloudWatch Alarms for checkoutservice: error rate > 1% for 5 minutes, p99 latency > 2s for 5 minutes, pod restart count > 0. Enable CloudWatch Anomaly Detection on error rates and latency. Integrate with Amazon EventBridge and PagerDuty/OpsGenie for incident notification. Define all alerting in Terraform and manage via GitOps. |
| **Evidence** | Absence of alerting configuration in repository, absence of CloudWatch alarm resources in IaC, absence of alerting integration (PagerDuty, OpsGenie, SNS) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Deployment uses Skaffold + `kubectl apply` (`skaffold.yaml`: `deploy.kubectl: {}`), which performs a straight-to-production rolling update with Kubernetes default settings. The CI pipeline deploys directly to a GKE namespace using `skaffold run`. No canary deployments, no blue/green, no traffic shifting. No Argo Rollouts, no CodeDeploy, no Flagger. The PR pipeline deploys to isolated namespaces for testing, but the main branch pipeline deploys directly to the target cluster. |
| **Gap** | Direct-to-production deployment with no staged rollout for a P0 critical-path service. A bad deployment affects 100% of checkout traffic immediately. No automated rollback — if smoke tests fail, manual intervention is required. No traffic shifting or gradual rollout. |
| **Recommendation** | On EKS, adopt Argo CD (preferred per GitOps preference) with Argo Rollouts for canary deployments. Configure canary strategy: 10% traffic → automated analysis (error rate, latency) → promote or rollback. Use Kubernetes-native progressive delivery. Alternatively, use AWS App Mesh with traffic shifting for canary deployments. Define rollout strategies in Helm values and manage via GitOps. |
| **Evidence** | `skaffold.yaml` (`deploy.kubectl: {}`), `.github/workflows/ci-pr.yaml` (skaffold run for deployment), `.github/workflows/ci-main.yaml` (skaffold run for deployment), absence of Argo Rollouts, Flagger, or CodeDeploy configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline includes smoke tests: the loadgenerator sends traffic to the frontend, and the pipeline checks for zero errors in the aggregated results. This provides a coarse-grained end-to-end validation. Unit tests exist for the money package (`money/money_test.go` — comprehensive tests for Sum, IsValid, Negate, etc.). The PR pipeline deploys the full application stack to an isolated GKE namespace and runs the loadgenerator smoke test. |
| **Gap** | No dedicated integration tests for the checkout workflow. The smoke tests use the loadgenerator which sends generic traffic — it does not specifically test the PlaceOrder flow with various edge cases (empty cart, invalid payment, currency conversion failures). Checkoutservice does not have its own Go test file (no `main_test.go`). Unit tests exist only for the money package utility functions. No contract tests between checkoutservice and its 6 downstream dependencies. |
| **Recommendation** | Add checkoutservice-specific integration tests: test PlaceOrder with mock gRPC services, test error handling for each downstream failure (cart unavailable, payment declined, shipping failed). Use Go testing with testcontainers or gRPC mock servers. Add contract tests (Pact or buf breaking change detection) between checkoutservice and downstream services. Run integration tests in CI before deployment. |
| **Evidence** | `src/checkoutservice/money/money_test.go` (unit tests), `.github/workflows/ci-pr.yaml` (smoke test via loadgenerator), absence of `main_test.go` or integration test directory |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns found in the repository. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The Kubernetes liveness probe provides basic pod restart on failure (crash loop), but this is default Kubernetes behavior, not explicit incident response. No documented escalation procedures. |
| **Gap** | No incident response infrastructure. For a P0 service processing financial transactions, the absence of runbooks and automated remediation means incidents rely entirely on human response. No automated rollback on deployment failure. No circuit breakers or bulkhead patterns for downstream service failures. |
| **Recommendation** | On AWS, create runbooks as SSM Automation documents for common incidents: pod crash loops (auto-rollback deployment), downstream service unavailability (circuit breaker activation), high error rate (auto-scale and alert). Implement circuit breakers in the checkout workflow using Go middleware. Use Amazon EventBridge rules with Step Functions for automated incident response workflows. Store runbooks in the repository and manage via GitOps. |
| **Evidence** | Absence of runbook files, absence of SSM documents, absence of incident response automation, `kubernetes-manifests/checkoutservice.yaml` (liveness probe — default K8s behavior only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS exists (`.github/CODEOWNERS`) but covers the entire repository with a single team (`@GoogleCloudPlatform/devrel-flagship-app-maintainers`). No per-service observability ownership. No per-service dashboards. No alarm ownership attribution. No SLO definitions with team attribution. No observability-specific CODEOWNERS entries. |
| **Gap** | No observability ownership model. No team is explicitly responsible for checkoutservice dashboards, alarms, or SLOs. Without ownership, monitoring gaps emerge and alarms become noise without clear response paths. For a P0 service, this means no one is explicitly accountable for checkout observability. |
| **Recommendation** | Define observability ownership: add CODEOWNERS entries for observability configs (e.g., `monitoring/ @checkout-team`). Create per-service CloudWatch dashboards with named owners. Tag all CloudWatch alarms and dashboards with team ownership. Define SLOs with explicit team attribution. On AWS, use CloudWatch cross-account observability for centralized visibility with team-level access. |
| **Evidence** | `.github/CODEOWNERS` (single global owner), absence of per-service dashboards, absence of team-attributed alarms or SLOs |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes resources have consistent labels (`app: checkoutservice`) applied across Deployments, Services, and ServiceAccounts. The Helm chart templates apply these labels consistently. Terraform resources do not have explicit tags (no `labels` block on the GKE cluster or Memorystore instance). No cost allocation labels, no environment labels, no ownership labels beyond the `app` label. |
| **Gap** | Kubernetes labels exist but are limited to `app` name — no environment (dev/staging/prod), no team ownership, no cost center, no version tagging. Terraform resources have no labels. No tag enforcement policies. No cost allocation tag activation. For AWS migration, a comprehensive tagging strategy is needed from day one. |
| **Recommendation** | On AWS, implement a tagging standard: `Environment`, `Team`, `CostCenter`, `Application`, `ManagedBy` as mandatory tags. Use Terraform `default_tags` in the AWS provider block. Enable AWS Config rules for tag compliance enforcement (`required-tags`). Apply Kubernetes labels consistently via Helm `commonLabels`. Define tag policies in AWS Organizations. Manage all tagging via Terraform and GitOps. |
| **Evidence** | `kubernetes-manifests/checkoutservice.yaml` (labels: app: checkoutservice), `helm-chart/templates/checkoutservice.yaml` (Helm-templated labels), `terraform/main.tf` (no labels on GKE cluster) |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to AI** | [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/checkoutservice/main.go` | INF-Q1, INF-Q3, INF-Q4, APP-Q2, APP-Q3, APP-Q4, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q1, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q3 | Primary application source: PlaceOrder workflow, gRPC client connections, OpenTelemetry instrumentation, insecure credentials |
| `src/checkoutservice/go.mod` | INF-Q2, APP-Q1, APP-Q3, DATA-Q2, DATA-Q4, OPS-Q1, OPS-Q3 | Go 1.25.0, OpenTelemetry SDK v1.42.0, gRPC, no database drivers, no messaging SDKs |
| `src/checkoutservice/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage build, distroless base image, pinned Go version with SHA256 digest |
| `src/checkoutservice/money/money.go` | DATA-Q4 | Money calculations in Go application code (not stored procedures) |
| `src/checkoutservice/money/money_test.go` | OPS-Q6 | Unit tests for money package (Sum, IsValid, Negate) |
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q9, INF-Q10 | GKE Autopilot cluster, regional deployment, null_resource kubectl apply |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2, SEC-Q5 | Managed Redis option (REDIS_7_0), no backup config, no encryption, sed-based connection injection |
| `terraform/providers.tf` | INF-Q10 | Google provider v7.16.0 |
| `terraform/variables.tf` | INF-Q2, INF-Q10 | GCP project, region, namespace, memorystore toggle |
| `kubernetes-manifests/checkoutservice.yaml` | INF-Q1, INF-Q5, INF-Q6, INF-Q7, INF-Q9, APP-Q6, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6, OPS-Q2, OPS-Q7, OPS-Q9 | Deployment, Service, ServiceAccount, securityContext, env vars, resource limits, health probes |
| `helm-chart/Chart.yaml` | INF-Q10 | Helm chart v0.10.5, application type |
| `helm-chart/values.yaml` | INF-Q2, INF-Q5, INF-Q7, INF-Q8, DATA-Q3, SEC-Q3, SEC-Q6, OPS-Q1, OPS-Q9 | Service configs, networkPolicies, securityContext, seccompProfile, cartDatabase, opentelemetryCollector |
| `helm-chart/templates/checkoutservice.yaml` | INF-Q1, INF-Q5, APP-Q6, SEC-Q3, SEC-Q5, OPS-Q9 | Helm-templated deployment with NetworkPolicy, Sidecar, AuthorizationPolicy |
| `.github/workflows/ci-pr.yaml` | INF-Q11, SEC-Q7, OPS-Q5, OPS-Q6 | CI pipeline: code-tests, deployment-tests, smoke tests, no security scanning |
| `.github/workflows/ci-main.yaml` | INF-Q11, SEC-Q7, OPS-Q5 | Main branch CI: code-tests, deployment-tests, smoke tests |
| `.github/workflows/helm-chart-ci.yaml` | INF-Q11 | Helm lint and template validation |
| `.github/workflows/terraform-validate-ci.yaml` | INF-Q11 | Terraform init and validate |
| `.github/renovate.json5` | INF-Q11, SEC-Q7 | Automated dependency updates for Go, Python, Kubernetes |
| `skaffold.yaml` | INF-Q10, INF-Q11, OPS-Q5 | Build and deploy configuration: Skaffold + kubectl apply, 11 service artifacts |
| `cloudbuild.yaml` | INF-Q11 | Google Cloud Build alternative pipeline with Skaffold |
| `protos/demo.proto` | APP-Q2, APP-Q5, DATA-Q2 | 9 gRPC service definitions, protobuf contracts, package hipstershop (no version) |
| `src/checkoutservice/genproto/demo_grpc.pb.go` | APP-Q2, APP-Q5 | Generated gRPC code with full method names |
| `istio-manifests/frontend-gateway.yaml` | INF-Q5, INF-Q6 | Istio Gateway and VirtualService for frontend ingress |
| `istio-manifests/frontend.yaml` | INF-Q6 | Frontend VirtualService routing |
| `istio-manifests/allow-egress-googleapis.yaml` | INF-Q5 | ServiceEntry for googleapis egress |
| `kustomize/components/network-policies/` | INF-Q5 | Per-service NetworkPolicies including deny-all baseline |
| `.github/CODEOWNERS` | OPS-Q8 | Single global owner — no per-service observability ownership |
| `src/checkoutservice/README.md` | Quick Agent Wins | Minimal documentation (dep ensure instructions only) |
