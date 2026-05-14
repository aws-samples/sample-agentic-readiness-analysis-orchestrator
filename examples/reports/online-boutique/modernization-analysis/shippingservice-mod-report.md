# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | shippingservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P1 |
| **Tags** | go, grpc, shipping |
| **Context** | Go gRPC service providing shipping cost estimates and tracking. |
| **Overall Score** | 2.39 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.55 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.50 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.71 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **2.39 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | OPS-Q1: Distributed Tracing | 1 | Tracing is a TODO stub; no OpenTelemetry or X-Ray instrumentation despite indirect dependency | Impossible to debug cross-service failures in a 12-service microservices architecture; blocks effective incident response |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured in IaC | No forensic capability; compliance risk; cannot trace infrastructure changes or security events |
| 3 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption-at-rest configuration on any data store | Data protection gap; compliance risk for any regulated workload |
| 4 | INF-Q4: Async Messaging/Streaming | 1 | All inter-service communication is synchronous gRPC with no messaging infrastructure | Tight coupling between services; cascading failure risk; no event-driven patterns for decoupled processing |
| 5 | OPS-Q2: SLO Definitions | 1 | No SLO definitions, error budgets, or service-level monitoring | Cannot measure service quality or make data-driven modernization investment decisions |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 1, but proto definitions in `protos/demo.proto` provide structured API contracts with `GetQuote` and `ShipOrder` RPCs, and gRPC reflection is enabled in `main.go`). The gRPC reflection service registration (`reflection.Register(srv)`) enables runtime API discovery.
- **What it enables:** An Amazon Bedrock-powered agent that discovers and invokes the ShippingService gRPC endpoints as tools — generating shipping quotes and tracking IDs through natural language requests. The protobuf schema provides the structured contract needed for tool definition.
- **Additional steps:** Generate an OpenAPI-compatible specification from the proto definitions (e.g., using `grpc-gateway` or proto-to-OpenAPI tooling) to enable broader agent tool discovery. Consider adding gRPC-JSON transcoding for HTTP-based agent invocation.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) with unit tests, deployment tests, and smoke tests provide an automated pipeline surface.
- **What it enables:** An Amazon Bedrock-powered DevOps agent that triggers builds, checks CI/CD pipeline status, initiates deployments via Skaffold, and monitors deployment health across the GKE namespaces. The agent can orchestrate the existing GitHub Actions workflows and Cloud Build pipelines.
- **Additional steps:** Expose pipeline status via API (GitHub Actions API is already available). Add GitOps-based deployment triggers (ArgoCD or Flux) aligned with `prefer: gitops` to provide a cleaner agent interface than direct `skaffold run`.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` (root and `src/shippingservice/README.md`), `protos/demo.proto` (full API contract with comments), `helm-chart/README.md`, `kustomize/README.md`, and inline code documentation provide a documentation corpus.
- **What it enables:** An Amazon Bedrock-powered RAG agent using the repository documentation, protobuf definitions, and Helm chart configuration as a knowledge base. Developers can ask questions about the shipping service API contract, deployment configuration, Helm chart values, and Kustomize component options.
- **Additional steps:** Index the documentation corpus into an Amazon OpenSearch Service vector store or Amazon Kendra. Enrich with generated API documentation from proto definitions.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — application is already a microservices architecture with independently deployable services |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute already on managed Kubernetes (GKE Autopilot) with Dockerfiles and K8s manifests |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures; no commercial DB engines detected (only open-source Redis) |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 — databases already use managed services (Google Cloud Memorystore for Redis) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: no data processing workloads detected; shipping service is purely computational |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3 — IaC coverage and CI/CD automation meet the threshold (≥ 3) |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent framework imports detected in source code; no vector DB, RAG, or agent eval infrastructure |

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

The shipping service and the broader Online Boutique platform have **no AI/agent infrastructure**:

- **AI/Agent Frameworks:** No imports of Amazon Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK found in any source files. The Go dependencies (`go.mod`) include only gRPC, protobuf, logrus, and GCP profiler.
- **Vector Database Infrastructure:** No OpenSearch with vector engine, no Pinecone, pgvector, Weaviate, or Qdrant. The only data store is Redis (for cart, not shipping).
- **RAG Implementation:** No embedding generation, vector store queries, retrieval chains, or document processing pipelines.
- **Agent Evaluation Frameworks:** No Ragas, DeepEval, or custom evaluation harnesses.

#### Application Domain and Potential AI Use Cases

The shipping service provides quote estimation and tracking ID generation. AI integration opportunities include:

1. **Intelligent Shipping Quote Engine** — Replace the static `$8.99` flat-rate quote logic (`quote.go`) with an Amazon Bedrock-powered dynamic pricing model that considers item weight, dimensions, destination, carrier rates, and delivery speed options.
2. **Shipping Tracking Intelligence** — Enhance the mock tracking system (`tracker.go`) with Bedrock-powered natural language shipping status updates and delivery time predictions.
3. **Customer Support Agent** — Deploy an Amazon Bedrock agent that handles shipping-related customer inquiries (quote questions, tracking status, delivery estimates) using the existing gRPC API as tool endpoints.

#### Quick Wins

See the [Quick Agent Wins](#quick-agent-wins) section for immediate opportunities. The existing protobuf API contracts and CI/CD pipeline provide a foundation for agent integration.

#### Recommended AI Services (aligned with preferences)

- **Amazon Bedrock** (preferred) — Foundation model access for shipping intelligence, customer support agents, and dynamic pricing
- **Amazon Bedrock AgentCore** — Agent runtime for deploying shipping support agents with tool use capabilities
- **Amazon OpenSearch Service** (vector engine) — Vector store for RAG-based knowledge retrieval from shipping documentation and product catalogs
- **Amazon Kendra** — Enterprise search over shipping policies and documentation

#### Foundation Requirements Before AI Integration

1. **API Surface:** Protobuf definitions exist (`protos/demo.proto`) and gRPC reflection is enabled. Generate OpenAPI specs for broader tool discovery.
2. **Observability:** Implement distributed tracing (OPS-Q1 gap) — critical for monitoring AI agent interactions and latency.
3. **Data Access:** The shipping service is stateless. For AI-powered pricing, a data layer (e.g., Amazon DynamoDB for shipping rate tables, aligned with `prefer: dynamodb`) would need to be introduced.
4. **Security:** Implement API authentication (SEC-Q3 gap) before exposing endpoints as agent tools.

#### AWS Prescriptive Guidance

- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)
- [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All compute workloads run on GKE Autopilot (`google_container_cluster` with `enable_autopilot = true` in `terraform/main.tf`). Every service is containerized with a Dockerfile (shipping service uses multi-stage build with `golang:1.26.1-alpine` builder and `gcr.io/distroless/static` runtime in `src/shippingservice/Dockerfile`). Kubernetes Deployments are defined for all 12 services in `kubernetes-manifests/` with resource requests and limits. Helm chart (`helm-chart/`) provides templated deployment. No raw EC2 or VM instances. |
| **Gap** | None — 100% managed container orchestration. Platform is GCP (GKE) rather than AWS (EKS), which is relevant for an AWS migration but does not reduce the maturity score. |
| **Recommendation** | When migrating to AWS, adopt Amazon EKS (aligned with `prefer: eks`) with managed node groups or Fargate profiles. Leverage Terraform EKS modules (aligned with `prefer: terraform`) for infrastructure definition. |
| **Evidence** | `terraform/main.tf` (GKE Autopilot), `src/shippingservice/Dockerfile`, `kubernetes-manifests/shippingservice.yaml`, `helm-chart/templates/shippingservice.yaml`, `skaffold.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The platform uses Google Cloud Memorystore for Redis (`google_redis_instance` with `redis_version = "REDIS_7_0"` in `terraform/memorystore.tf`) as a managed database for the cart service. The shipping service itself is stateless with no database. The Redis instance is conditionally created (`count = var.memorystore ? 1 : 0`), meaning the default deployment uses an in-cluster Redis pod (`cartDatabase.inClusterRedis.create: true` in `helm-chart/values.yaml`). |
| **Gap** | The default configuration uses an in-cluster Redis pod (not managed). Memorystore is only enabled via Terraform variable. No automated failover configuration on the Memorystore instance (single-AZ by default). |
| **Recommendation** | When migrating to AWS, use Amazon ElastiCache for Redis or Amazon MemoryDB with Multi-AZ enabled. If the shipping service evolves to need state (e.g., shipping rate tables), consider Amazon DynamoDB (aligned with `prefer: dynamodb`) for low-latency key-value access. |
| **Evidence** | `terraform/memorystore.tf`, `helm-chart/values.yaml` (`cartDatabase` section) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service detected. No Step Functions, Temporal, Camunda, or any orchestration framework found in IaC, dependencies, or source code. The shipping service logic is simple in-process code: `GetQuote` calculates a flat-rate quote and `ShipOrder` generates a tracking ID — both are single-step operations in `main.go`. The broader `CheckoutService` orchestrates the order flow (calling Shipping, Payment, Email services) but this orchestration is hardcoded in application code. |
| **Gap** | No dedicated workflow orchestration for multi-service business workflows. The checkout flow (order → payment → shipping → email) is hardcoded orchestration logic. |
| **Recommendation** | Introduce AWS Step Functions (aligned with `prefer: terraform` for IaC definition) to orchestrate the checkout workflow. This provides visual workflow management, error handling, retry logic, and state management. Define Step Functions state machines in Terraform. |
| **Evidence** | `src/shippingservice/main.go` (simple in-process logic), `protos/demo.proto` (CheckoutService.PlaceOrder orchestrates multiple services), absence of any orchestration framework in `go.mod` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure detected. All inter-service communication is synchronous gRPC as defined in `protos/demo.proto`. The `CheckoutService` calls `ShippingService.GetQuote` and `ShippingService.ShipOrder` synchronously. No SQS, SNS, EventBridge, Kafka, RabbitMQ, Kinesis, or any message broker references found in IaC, source code, or Kubernetes manifests. |
| **Gap** | All communication is synchronous — no event-driven patterns, no message queues, no async processing. Cascading failure risk if any synchronous service call fails or is slow. |
| **Recommendation** | Introduce Amazon SQS or Amazon SNS for asynchronous workflows (e.g., order shipping notifications via SNS → SQS). For the shipping event flow, publish `ShipOrderCompleted` events to SNS/EventBridge so downstream services (email, tracking) can react asynchronously. Define messaging infrastructure in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `protos/demo.proto` (all RPC definitions are unary synchronous), `src/shippingservice/main.go` (synchronous gRPC handlers), `go.mod` (no messaging SDK imports) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes NetworkPolicy support exists in the Helm chart (`helm-chart/templates/shippingservice.yaml`) with fine-grained ingress rules limiting access to shipping service from `frontend` and `checkoutservice` only on port 50051. A default deny-all NetworkPolicy is defined in `helm-chart/templates/common.yaml`. Istio AuthorizationPolicies restrict access by service account principal (`cluster.local/ns/.../sa/frontend`, `cluster.local/ns/.../sa/checkoutservice`). Pod SecurityContext enforces `runAsNonRoot`, `readOnlyRootFilesystem`, and drops all capabilities. However, NetworkPolicies and AuthorizationPolicies are **disabled by default** (`networkPolicies.create: false`, `authorizationPolicies.create: false` in `values.yaml`). No VPC/subnet configuration in Terraform. |
| **Gap** | Network security controls exist but are disabled by default. No explicit VPC/subnet definition — GKE Autopilot uses a default VPC. No evidence that NetworkPolicies or Istio AuthorizationPolicies are enabled in production. |
| **Recommendation** | Enable NetworkPolicies and AuthorizationPolicies by default (`networkPolicies.create: true`, `authorizationPolicies.create: true` in `values.yaml`). When migrating to AWS EKS (aligned with `prefer: eks`), define VPC with private subnets using Terraform VPC modules, and configure security groups with least-privilege rules. |
| **Evidence** | `helm-chart/templates/shippingservice.yaml` (NetworkPolicy, AuthorizationPolicy), `helm-chart/templates/common.yaml` (deny-all), `helm-chart/values.yaml` (disabled by default), `kubernetes-manifests/shippingservice.yaml` (SecurityContext) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Istio Gateway (`istio-manifests/frontend-gateway.yaml`) serves as the external entry point routing HTTP traffic to the frontend service. Istio VirtualService provides routing rules. Internal services (including shipping) are exposed via ClusterIP Kubernetes Services, routed through the Istio service mesh. The Istio Sidecar configuration in Helm limits egress visibility per service. |
| **Gap** | The Istio Gateway handles basic routing on port 80 with no TLS, no throttling, no request validation, and no per-request authentication. Only the frontend is exposed through the gateway — internal gRPC services lack API gateway controls. |
| **Recommendation** | When migrating to AWS, deploy an Amazon API Gateway or AWS App Mesh for service-to-service communication with EKS (aligned with `prefer: eks`). Add rate limiting, request validation, and mutual TLS. For the frontend, use Amazon CloudFront + API Gateway with WAF rules. |
| **Evidence** | `istio-manifests/frontend-gateway.yaml` (Gateway, VirtualService), `istio-manifests/frontend.yaml`, `kubernetes-manifests/shippingservice.yaml` (ClusterIP Service) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GKE Autopilot (`enable_autopilot = true` in `terraform/main.tf`) automatically manages node scaling and pod scheduling. Resource requests and limits are defined for every service in both raw manifests (`kubernetes-manifests/shippingservice.yaml`: 100m/200m CPU, 64Mi/128Mi memory) and Helm templates (`helm-chart/values.yaml`). GKE Autopilot scales nodes based on resource requests automatically. |
| **Gap** | No explicit Horizontal Pod Autoscaler (HPA) definitions. Autopilot handles node-level scaling but pod replica scaling is not configured — the Deployment does not specify `replicas` or reference an HPA. Scaling responds to resource pressure but not to custom metrics (e.g., request rate, queue depth). |
| **Recommendation** | When migrating to AWS EKS (aligned with `prefer: eks`), configure Kubernetes HPA with custom metrics (gRPC request rate, latency). Use Karpenter for efficient node auto-scaling. Define HPA resources in Terraform/Helm (aligned with `prefer: terraform`). |
| **Evidence** | `terraform/main.tf` (`enable_autopilot = true`), `kubernetes-manifests/shippingservice.yaml` (resource requests/limits), `helm-chart/values.yaml` (resource definitions) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found anywhere in the repository. The Memorystore Redis instance (`terraform/memorystore.tf`) has no `persistence_config` or backup settings. No `aws_backup_plan`, no S3 versioning, no snapshot lifecycle policies. The shipping service is stateless, but the platform's only data store (Redis for cart) has no backup strategy. |
| **Gap** | No automated backups for any data store. No point-in-time recovery. No documented restore procedures. A Redis failure would result in complete cart data loss. |
| **Recommendation** | When migrating to AWS, configure Amazon ElastiCache for Redis with automatic backups and PITR. If introducing DynamoDB (aligned with `prefer: dynamodb`), enable point-in-time recovery and on-demand backups. Define backup policies in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `terraform/memorystore.tf` (no backup config), absence of any backup plan resources in `terraform/` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GKE Autopilot is regional by default (`region = var.region` with default `us-central1` in `terraform/variables.tf`), meaning the Kubernetes cluster spans multiple availability zones within the region. Pod scheduling is distributed across zones automatically. However, the Memorystore Redis instance has no Multi-AZ configuration — no `replica_count`, no `read_replicas_mode`. |
| **Gap** | Compute is multi-AZ (regional GKE Autopilot). The Redis data store is single-AZ with no failover replica — an AZ failure affecting the Redis instance would take down the cart service. |
| **Recommendation** | When migrating to AWS, configure Amazon ElastiCache for Redis with Multi-AZ enabled and automatic failover. Deploy EKS (aligned with `prefer: eks`) across 3+ AZs with pod anti-affinity rules. Define multi-AZ configuration in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `terraform/main.tf` (`location = var.region`), `terraform/variables.tf` (`region` default `us-central1`), `terraform/memorystore.tf` (no HA config) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Terraform (`terraform/`) defines the GKE cluster and Memorystore Redis. Kubernetes manifests (`kubernetes-manifests/`) define all 12 service Deployments, Services, and ServiceAccounts via Kustomize. Helm chart (`helm-chart/`) provides templated deployment with configurable values for all services. Skaffold (`skaffold.yaml`) orchestrates build and deploy. Terraform validation CI exists (`.github/workflows/terraform-validate-ci.yaml`). Helm chart linting CI exists (`.github/workflows/helm-chart-ci.yaml`). |
| **Gap** | Deployment to the cluster uses `null_resource` with `kubectl apply -k` (`terraform/main.tf`), which is not idempotent and mixes Terraform lifecycle with imperative kubectl commands. No Terraform state backend configuration. Istio manifests are standalone YAML files not managed by Helm or Kustomize. No GitOps tool (ArgoCD, Flux) despite complex multi-service deployment. |
| **Recommendation** | Adopt a GitOps approach (aligned with `prefer: gitops`) using ArgoCD or Flux CD to manage Kubernetes manifests declaratively. Replace `null_resource` kubectl commands with proper GitOps-based deployment. Add Terraform backend configuration for state management. Define all infrastructure in Terraform (aligned with `prefer: terraform`) with remote state in S3. |
| **Evidence** | `terraform/main.tf` (cluster + null_resource deploy), `terraform/memorystore.tf`, `kubernetes-manifests/`, `helm-chart/`, `skaffold.yaml`, `.github/workflows/terraform-validate-ci.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides CI/CD with two main workflows: PR (`ci-pr.yaml`) and Main/Release (`ci-main.yaml`). Both include: (1) Code tests — Go unit tests for shippingservice, productcatalogservice, and C# tests for cartservice; (2) Deployment tests — build images, deploy to GKE PR namespace via Skaffold, wait for pods, run smoke tests with loadgenerator checking for zero errors. Cloud Build (`cloudbuild.yaml`) provides an alternative deployment path using `skaffold run`. Separate CI workflows exist for Helm chart linting, Kustomize build validation, and Terraform validation. |
| **Gap** | No automated rollback mechanism. Deployment is direct `skaffold run` (kubectl apply) with no canary or blue/green strategy. Smoke tests verify zero errors but there is no gate to prevent bad deployments from reaching production. No artifact signing or provenance tracking. |
| **Recommendation** | Adopt GitOps-based deployment (aligned with `prefer: gitops`) with ArgoCD or Flux CD for declarative, auditable deployments with automated rollback. Add progressive delivery using Argo Rollouts or Flagger for canary deployments on EKS (aligned with `prefer: eks`). Integrate container image signing with AWS Signer. |
| **Evidence** | `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `cloudbuild.yaml`, `skaffold.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The shipping service is written in Go (1.25.0 with toolchain 1.26.1 per `go.mod`). Go has a mature cloud-native ecosystem with excellent support for containers (compiles to static binaries), gRPC (first-class support via `google.golang.org/grpc`), and Kubernetes. The broader Online Boutique uses Go (shipping, productcatalog, frontend, checkout), Python (recommendation, email), C# (cart), Java (ad, currency), and Node.js (payment). |
| **Gap** | None — Go is a tier-1 cloud-native language with excellent tooling, container support, and ecosystem maturity. |
| **Recommendation** | Go is well-suited for AWS EKS workloads. When migrating, leverage the AWS SDK for Go v2 for native AWS service integration. The static binary compilation and `distroless` base image pattern is directly portable to EKS. |
| **Evidence** | `src/shippingservice/go.mod` (Go 1.25.0), `src/shippingservice/main.go` (gRPC server), `src/shippingservice/Dockerfile` (multi-stage build) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The Online Boutique is a well-decomposed microservices architecture with 12+ independently deployable services: shippingservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, adservice, loadgenerator, and shoppingassistantservice. Each service has its own Dockerfile, Kubernetes Deployment, Service, and ServiceAccount (`kubernetes-manifests/`). Services communicate via gRPC with well-defined protobuf contracts (`protos/demo.proto`). The shipping service is a focused, single-purpose microservice with two RPCs: `GetQuote` and `ShipOrder`. |
| **Gap** | None — the architecture is already decomposed into independently deployable microservices with clear service boundaries and well-defined API contracts. |
| **Recommendation** | Maintain the microservices architecture. When migrating to EKS (aligned with `prefer: eks`), deploy each service as a separate Kubernetes Deployment with dedicated ServiceAccounts. |
| **Evidence** | `skaffold.yaml` (12 build artifacts), `kubernetes-manifests/` (12 service manifests), `protos/demo.proto` (service contracts), `src/shippingservice/main.go` (focused single-service) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC. The `protos/demo.proto` defines 10 gRPC services, all using unary (request-response) RPCs. The `CheckoutService.PlaceOrder` RPC synchronously calls `CartService`, `ProductCatalogService`, `CurrencyService`, `ShippingService`, `PaymentService`, and `EmailService` in sequence. No message queues, event buses, pub/sub patterns, or async communication mechanisms found anywhere in the codebase. |
| **Gap** | 100% synchronous communication. No async patterns for any workflow. The checkout flow is a synchronous chain of 6+ service calls — a failure or slowdown in any service blocks the entire checkout. |
| **Recommendation** | Introduce event-driven patterns using Amazon SNS/SQS or Amazon EventBridge for fire-and-forget operations (e.g., email notifications, shipping events). Convert the checkout orchestration to use AWS Step Functions for resilient multi-service coordination. Keep latency-sensitive calls (GetQuote) synchronous but make fire-and-forget operations (ShipOrder → email notification) asynchronous. |
| **Evidence** | `protos/demo.proto` (all unary RPCs), `src/shippingservice/main.go` (synchronous handlers), `go.mod` (no messaging libraries) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The shipping service operations are inherently fast: `GetQuote` performs an in-memory flat-rate calculation (`quote.go` — returns `$8.99` for any non-empty cart) and `ShipOrder` generates a random tracking ID (`tracker.go` — string formatting with random numbers). Both complete in microseconds. No operations exceed 30 seconds. The service design naturally avoids long-running process issues. |
| **Gap** | While current operations are fast, there are no async processing patterns in place if the service evolves to include real shipping carrier API calls, rate comparisons, or label generation — which would be long-running operations. |
| **Recommendation** | As the shipping service evolves beyond mock functionality, implement async job processing using Amazon SQS with a worker pattern for operations like carrier rate comparison and label generation. Use AWS Step Functions for multi-step shipping workflows (rate quote → carrier selection → label generation → tracking). |
| **Evidence** | `src/shippingservice/quote.go` (simple math), `src/shippingservice/tracker.go` (random string generation), `src/shippingservice/main.go` (GetQuote, ShipOrder handlers) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy detected. The gRPC service is defined in `protos/demo.proto` under the `hipstershop` package with no version indicator. No `/v1/` URL patterns, no `Accept-Version` headers, no versioned proto package names (e.g., `hipstershop.v1`), no changelog files. The `go_package` option is `github.com/GoogleCloudPlatform/microservices-demo/hipstershop` — unversioned. |
| **Gap** | No versioning — any breaking change to the protobuf contract (`GetQuoteRequest`, `ShipOrderRequest`, `GetQuoteResponse`, `ShipOrderResponse`) would break all consumers simultaneously. No backward compatibility guarantees. |
| **Recommendation** | Adopt protobuf package versioning (e.g., `package hipstershop.shipping.v1`). Use protobuf's built-in evolution rules (additive-only changes, reserved fields) for backward compatibility. When migrating to AWS, consider API Gateway with versioned routes for HTTP-transcoded endpoints. |
| **Evidence** | `protos/demo.proto` (`package hipstershop` — no version), `src/shippingservice/genproto/` (generated code, unversioned) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Kubernetes DNS-based service discovery is in use. Services reference each other by Kubernetes Service names (e.g., `shippingservice:50051`). ClusterIP Services (`kubernetes-manifests/shippingservice.yaml`) provide stable DNS endpoints within the cluster. Istio VirtualServices (`istio-manifests/frontend.yaml`) provide additional service mesh routing with explicit host references (`frontend.default.svc.cluster.local`). No hard-coded IP addresses found. The Helm chart Istio Sidecar configuration limits egress scope per service. |
| **Gap** | None — service discovery is fully implemented via Kubernetes DNS and Istio service mesh. No hard-coded endpoints. |
| **Recommendation** | When migrating to AWS EKS (aligned with `prefer: eks`), Kubernetes DNS service discovery is directly portable. Consider AWS Cloud Map for cross-cluster service discovery if services span multiple EKS clusters. |
| **Evidence** | `kubernetes-manifests/shippingservice.yaml` (ClusterIP Service), `istio-manifests/frontend.yaml` (VirtualService with DNS), `helm-chart/templates/shippingservice.yaml` (Service definition) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The shipping service is stateless and does not store any data — no unstructured documents, no file uploads, no binary data. The broader platform does not use S3 or any equivalent object storage. The only data persistence is the Redis cache for the cart service. No document processing, PDF generation, or image handling detected in the shipping service or broader platform. |
| **Gap** | No managed object storage (S3 equivalent) is provisioned in the platform. If unstructured data needs arise (e.g., shipping labels, invoices, tracking documents), there is no storage or parsing infrastructure in place. |
| **Recommendation** | If the shipping service evolves to generate shipping labels or tracking documents, provision Amazon S3 for object storage with Amazon Textract for document parsing. Define S3 buckets in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `src/shippingservice/main.go` (stateless service), `src/shippingservice/quote.go` (in-memory calculation), `src/shippingservice/tracker.go` (random ID generation), `terraform/` (no S3 or object storage resources) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The shipping service has no database connections at all. It is a pure computation service: `GetQuote` calculates a flat-rate shipping quote based on item count (`quote.go`), and `ShipOrder` generates a random tracking ID (`tracker.go`). No ORM, no database driver imports, no connection strings, no SQL queries. The `go.mod` dependencies confirm no database libraries. The service's "data access" is entirely through the gRPC protobuf contract. |
| **Gap** | None — the service has no data access layer because it requires none. The design is clean and stateless. |
| **Recommendation** | If the service evolves to need shipping rate data, introduce a unified data access layer using Amazon DynamoDB (aligned with `prefer: dynamodb`) with a repository pattern in Go. Keep the current stateless design for the quote calculation and add a separate DynamoDB-backed rate lookup. |
| **Evidence** | `src/shippingservice/main.go` (no DB imports), `src/shippingservice/go.mod` (no DB driver dependencies), `src/shippingservice/quote.go`, `src/shippingservice/tracker.go` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The only database engine in the platform is Redis, explicitly pinned to version `REDIS_7_0` in `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`). Redis 7.0 is a current, supported version and not at or approaching EOL. The shipping service has no database of its own. The Redis version pin in Terraform ensures reproducible infrastructure. |
| **Gap** | Only one database engine to track. The Redis instance is conditionally created (`count = var.memorystore ? 1 : 0`), meaning the default in-cluster Redis pod (`helm-chart/values.yaml`) has no version pinning — it uses the `redis:alpine` default image from Docker Hub. |
| **Recommendation** | Pin the in-cluster Redis image version in the Helm chart values to avoid drift. When migrating to AWS, specify the exact ElastiCache Redis engine version in Terraform. |
| **Evidence** | `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`), `helm-chart/values.yaml` (`cartDatabase.inClusterRedis` — no version pin) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs detected anywhere in the repository. All business logic resides in the application layer: shipping quote calculation in `quote.go` (Go math operations), tracking ID generation in `tracker.go` (Go string formatting). No `.sql` migration files, no `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements. The Redis data store (for cart service) is key-value only with no stored procedures. |
| **Gap** | None — all business logic is in the application layer with no database-coupled logic. |
| **Recommendation** | Maintain this pattern. Keep business logic in the Go application layer as the service evolves. Avoid introducing stored procedures even if SQL databases are added. |
| **Evidence** | `src/shippingservice/quote.go` (app-layer business logic), `src/shippingservice/tracker.go` (app-layer logic), absence of `.sql` files in repository |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No audit logging configuration found in the repository. No CloudTrail, no GCP Cloud Audit Logs configuration in Terraform, no logging pipeline definitions. The Terraform (`terraform/main.tf`) enables `monitoring.googleapis.com` and `cloudtrace.googleapis.com` APIs but does not configure audit logging. No log retention policies, no immutable log storage. |
| **Gap** | No audit logging infrastructure. Infrastructure changes, API access, and security events cannot be traced or investigated forensically. |
| **Recommendation** | When migrating to AWS, enable AWS CloudTrail with log file validation and S3 storage with Object Lock for immutability. Configure CloudTrail to log all management events and data events for critical services. Define CloudTrail in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `terraform/main.tf` (no audit logging resources), `terraform/providers.tf` (no logging config), absence of any logging pipeline definition |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration found anywhere in the repository. The Memorystore Redis instance (`terraform/memorystore.tf`) has no `transit_encryption_mode` or `auth_enabled` settings. No KMS key definitions, no encryption configuration on any resource. The GKE Autopilot cluster relies on Google-managed encryption by default but no customer-managed keys are configured. |
| **Gap** | No explicit encryption-at-rest configuration. No customer-managed encryption keys. Reliance on default provider encryption without explicit configuration is a gap — encryption should be intentional and verifiable. |
| **Recommendation** | When migrating to AWS, configure AWS KMS customer-managed keys for all data stores. Enable encryption-at-rest on ElastiCache, EBS volumes, S3 buckets, and any DynamoDB tables (aligned with `prefer: dynamodb`). Define KMS keys and encryption configuration in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `terraform/memorystore.tf` (no encryption settings), `terraform/main.tf` (no KMS resources), absence of any encryption configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No per-request OAuth2/JWT authentication on the gRPC endpoints. The shipping service (`main.go`) registers the gRPC server with no authentication interceptors — `grpc.NewServer()` with no options. However, Istio AuthorizationPolicies (`helm-chart/templates/shippingservice.yaml`) provide service-to-service authentication via mTLS identity — restricting access to `frontend` and `checkoutservice` service accounts only on specific gRPC paths (`/hipstershop.ShippingService/GetQuote`, `/hipstershop.ShippingService/ShipOrder`). This is network-layer auth, not application-layer per-request auth. AuthorizationPolicies are disabled by default. |
| **Gap** | No application-level API authentication (OAuth2/JWT). Service mesh mTLS provides transport-level identity but is disabled by default. No token validation, no API keys, no authorization middleware in the gRPC server. |
| **Recommendation** | Implement gRPC interceptors for JWT/OAuth2 token validation. When migrating to AWS EKS (aligned with `prefer: eks`), integrate with Amazon Cognito or an external IdP for token issuance. Enable service mesh mTLS (Istio or AWS App Mesh) as a defense-in-depth layer. |
| **Evidence** | `src/shippingservice/main.go` (`grpc.NewServer()` — no auth interceptors), `helm-chart/templates/shippingservice.yaml` (AuthorizationPolicy — disabled by default), `helm-chart/values.yaml` (`authorizationPolicies.create: false`) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes ServiceAccounts are created per service (`kubernetes-manifests/shippingservice.yaml` — `ServiceAccount` named `shippingservice`). Istio mTLS provides service mesh identity based on Kubernetes ServiceAccount principals. The Helm chart supports GCP Workload Identity annotations (`serviceAccounts.annotations` in `values.yaml`) for cartservice's database access. However, there is no centralized identity provider (Cognito, Okta, Ping) integration. No OIDC/SAML configuration. No SSO. |
| **Gap** | Service-level identity exists via Kubernetes ServiceAccounts and Istio mTLS, but no centralized human identity provider. No federated identity. Applications manage their own identity context. |
| **Recommendation** | When migrating to AWS, integrate with Amazon Cognito for user authentication and AWS IAM Roles for Service Accounts (IRSA) on EKS (aligned with `prefer: eks`) for service-level identity. Define Cognito and IRSA configuration in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `kubernetes-manifests/shippingservice.yaml` (ServiceAccount), `helm-chart/values.yaml` (`serviceAccounts` section), `helm-chart/templates/shippingservice.yaml` (AuthorizationPolicy with SA principals) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The shipping service uses only non-sensitive environment variables: `PORT`, `DISABLE_PROFILER`, `DISABLE_TRACING` (`kubernetes-manifests/shippingservice.yaml`). No database credentials, API keys, or tokens are required by the shipping service. However, the broader platform has no secrets management strategy — the Redis connection string is managed via Kustomize sed replacement (`terraform/memorystore.tf` — `null_resource` that sed-replaces `REDIS_CONNECTION_STRING`). No Secrets Manager, Vault, or External Secrets Operator integration found. No `.env` files committed. |
| **Gap** | No secrets management infrastructure. The Redis connection string is injected via sed replacement in Kustomize, not through a secrets management system. As the platform evolves with more services needing credentials, this becomes a scaling problem. |
| **Recommendation** | When migrating to AWS, adopt AWS Secrets Manager for all credentials with automated rotation. Use External Secrets Operator on EKS (aligned with `prefer: eks`) to sync secrets from AWS Secrets Manager into Kubernetes Secrets. Define Secrets Manager resources in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `kubernetes-manifests/shippingservice.yaml` (env vars — non-sensitive only), `terraform/memorystore.tf` (sed-based connection string injection), `helm-chart/values.yaml` (`cartDatabase.connectionString: "redis-cart:6379"`) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong container hardening practices: Dockerfile uses `gcr.io/distroless/static` base image (minimal attack surface, no shell, no package manager). Kubernetes SecurityContext enforces `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, and drops ALL capabilities (`kubernetes-manifests/shippingservice.yaml`). Seccomp profile support is available in the Helm chart (`seccompProfile.enable`). GKE Autopilot manages node-level patching automatically. |
| **Gap** | No vulnerability scanning in the pipeline — no Amazon Inspector, Snyk, Trivy, or ECR image scanning. No evidence of SBOM generation. Renovate (`renovate.json5`) handles dependency version updates but does not scan for known vulnerabilities. |
| **Recommendation** | Add container image scanning (Amazon ECR image scanning or Trivy) in the CI/CD pipeline. Enable Amazon Inspector for runtime vulnerability detection on EKS (aligned with `prefer: eks`). Generate SBOMs for supply chain transparency. |
| **Evidence** | `src/shippingservice/Dockerfile` (distroless base), `kubernetes-manifests/shippingservice.yaml` (SecurityContext), `helm-chart/templates/shippingservice.yaml` (SecurityContext, seccompProfile), `.github/renovate.json5` (dependency updates only) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning integrated into the CI/CD pipeline. The GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) run unit tests and deployment smoke tests but include no security scanning steps. No SonarQube, Semgrep, CodeGuru Reviewer, `go vet` security checks, `govulncheck`, or `gosec` in the pipeline. Renovate (`renovate.json5`) provides automated dependency updates on a schedule but is not vulnerability scanning. No Dependabot, `.snyk` policy, or `npm audit`/`pip-audit` equivalent for Go. |
| **Gap** | No security scanning in the CI/CD pipeline. Vulnerabilities in Go dependencies or source code reach production undetected. No security gate to block deployments with critical findings. |
| **Recommendation** | Add `govulncheck` and `gosec` to the GitHub Actions CI pipeline for Go vulnerability and security scanning. Integrate Amazon CodeGuru Reviewer or Snyk for SAST. Add ECR image scanning as a deployment gate. When migrating to AWS, use Amazon CodePipeline with security scanning stages. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (no security steps), `.github/workflows/ci-main.yaml` (no security steps), `.github/renovate.json5` (update-only, not scanning), absence of `.snyk`, `gosec`, or `govulncheck` in pipeline |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Distributed tracing is a TODO stub. In `main.go`, the `initTracing()` function contains only `// TODO(arbrown) Implement OpenTelemetry tracing`. The `initStats()` function similarly contains `//TODO(arbrown) Implement OpenTelemetry stats`. The log message states "Tracing enabled, but temporarily unavailable" with a link to a GitHub issue. OpenTelemetry libraries (`go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc`) are indirect dependencies in `go.mod` (pulled in by the Google Cloud profiler) but are not instrumented in the application code. No X-Ray, no trace ID propagation. |
| **Gap** | No distributed tracing despite being a 12-service microservices architecture. Debugging cross-service failures (e.g., a failed checkout involving cart → currency → shipping → payment → email) is guesswork without trace propagation. |
| **Recommendation** | Implement OpenTelemetry SDK instrumentation in the shipping service using `otelgrpc` interceptors for automatic gRPC tracing. When migrating to AWS, configure the OpenTelemetry Collector to export traces to AWS X-Ray. Enable the `opentelemetryCollector` in the Helm chart (`opentelemetryCollector.create: true`). Define observability infrastructure in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | `src/shippingservice/main.go` (`initTracing()` TODO stub), `go.mod` (`otelgrpc` as indirect dependency), `helm-chart/values.yaml` (`opentelemetryCollector.create: false`) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budgets, no SLO monitoring configuration, no SLI (Service Level Indicator) definitions. No CloudWatch alarms, no Prometheus alerting rules, no SLO dashboard definitions. The shipping service has health check probes (`readinessProbe`, `livenessProbe` in `kubernetes-manifests/shippingservice.yaml`) for Kubernetes liveness, but these are not SLOs. |
| **Gap** | No formal definition of acceptable service levels (latency, availability, error rate). Without SLOs, there is no objective measure of whether the shipping service is meeting user expectations or degrading over time. |
| **Recommendation** | Define SLOs for the shipping service: target p99 latency for `GetQuote` (e.g., < 100ms), availability (e.g., 99.9%), error rate (e.g., < 0.1%). When migrating to AWS, use Amazon CloudWatch SLO monitoring with composite alarms. Implement error budget tracking. |
| **Evidence** | Absence of SLO definitions, alerting rules, or monitoring configuration in the entire repository. `kubernetes-manifests/shippingservice.yaml` (health probes only) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. The shipping service uses `logrus` for structured JSON logging (`main.go` — JSON formatter with timestamp, severity, message fields) but publishes no metrics. No `cloudwatch.put_metric_data`, no Prometheus metrics endpoint (`/metrics`), no StatsD client, no custom CloudWatch metrics. Only request-level logging (`[GetQuote] received request`, `[ShipOrder] received request`). |
| **Gap** | No business outcome metrics. Cannot track quotes generated per minute, average quote value, shipping orders processed, or tracking ID generation rate. Only log lines exist, which require log parsing for any analytics. |
| **Recommendation** | Add Prometheus metrics (using the Go Prometheus client library) or OpenTelemetry metrics for business KPIs: `shipping_quotes_total`, `shipping_orders_total`, `shipping_quote_value_usd`. When migrating to AWS, export metrics to Amazon CloudWatch via the OpenTelemetry Collector or CloudWatch agent. |
| **Evidence** | `src/shippingservice/main.go` (logrus logging only, no metrics), `go.mod` (no metrics library dependencies) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie/Slack integration. No alert definitions in IaC, Helm values, or Kubernetes manifests. The `helm-chart/values.yaml` has `googleCloudOperations.metrics: false` — GCP metrics are disabled by default. |
| **Gap** | No alerting of any kind. Failures, elevated error rates, or latency degradation in the shipping service would go unnoticed until user-reported. |
| **Recommendation** | When migrating to AWS, configure Amazon CloudWatch alarms for error rate, p99 latency, and availability on the shipping service. Enable CloudWatch anomaly detection for adaptive thresholds. Integrate with Amazon SNS for alert notifications. Define alarms in Terraform (aligned with `prefer: terraform`). |
| **Evidence** | Absence of any alerting configuration in the repository. `helm-chart/values.yaml` (`googleCloudOperations.metrics: false`) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployment uses Skaffold (`skaffold.yaml`) with `kubectl apply` via Kustomize — this is a rolling deployment with Kubernetes' default rolling update strategy. The Deployment in `kubernetes-manifests/shippingservice.yaml` does not specify a `strategy` field, so Kubernetes defaults to `RollingUpdate` with 25% `maxUnavailable` and 25% `maxSurge`. Health checks (readiness and liveness probes) gate traffic to new pods. The CI pipeline deploys to a PR namespace for testing (`ci-pr.yaml`), which is a good practice. Cloud Build (`cloudbuild.yaml`) uses `skaffold run` for direct deployment. |
| **Gap** | No canary, blue/green, or traffic-shifting deployment strategy. Direct rolling deployment means all pods are updated simultaneously — a bad deployment affects all traffic with no gradual rollout or automated rollback. |
| **Recommendation** | Adopt GitOps-based progressive delivery (aligned with `prefer: gitops`). Use ArgoCD with Argo Rollouts for canary or blue/green deployments on EKS (aligned with `prefer: eks`). Define rollout strategies in Kubernetes manifests with traffic shifting based on success metrics. |
| **Evidence** | `skaffold.yaml` (kubectl deploy), `kubernetes-manifests/shippingservice.yaml` (no deployment strategy specified), `.github/workflows/ci-pr.yaml` (PR namespace deployment), `cloudbuild.yaml` (`skaffold run`) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration testing exists at two levels: (1) Unit tests in `shippingservice_test.go` — 10 test functions covering `GetQuote`, `ShipOrder`, `CreateTrackingId`, `CreateQuoteFromFloat`, `CreateQuoteFromCount`, and helper functions. (2) Full deployment smoke tests in CI — `ci-pr.yaml` deploys the entire 12-service application to a GKE PR namespace, waits for all pods to be available, runs the loadgenerator with 50+ requests, and asserts zero errors. This validates the shipping service in the context of the full application. |
| **Gap** | No contract tests (e.g., gRPC contract testing between checkoutservice and shippingservice). No API-level integration tests for specific gRPC endpoints. The smoke test is coarse-grained — it catches catastrophic failures but not subtle regressions in specific API behaviors. |
| **Recommendation** | Add gRPC contract tests using `grpcurl` or Go test clients that validate specific request/response scenarios against the live shipping service. Add protobuf backward compatibility checks (e.g., `buf breaking`) to prevent API contract regressions. |
| **Evidence** | `src/shippingservice/shippingservice_test.go` (10 unit tests), `.github/workflows/ci-pr.yaml` (deployment smoke tests with loadgenerator), `.github/workflows/ci-main.yaml` (same smoke test pattern) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response workflows, or self-healing automation found. No SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No `runbooks/` directory, no incident response documentation. No auto-restart configurations beyond Kubernetes' built-in liveness probe restart. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (service crash, high latency, dependency failure). No automated remediation for any failure mode. |
| **Recommendation** | Create runbooks for common shipping service failure scenarios (pod crashes, gRPC timeout spikes, dependency unavailability). When migrating to AWS, use AWS Systems Manager Automation for self-healing (e.g., automatic pod restart, scaling adjustments). Store runbooks as machine-readable YAML in the repository. |
| **Evidence** | Absence of runbooks, incident response documentation, or automation scripts in the repository |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS file (`.github/CODEOWNERS`) defines `@GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver` as default owners for the entire repo — no per-service or per-observability-asset ownership. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution. No observability-specific ownership for the shipping service. |
| **Gap** | No observability ownership model. No one is explicitly responsible for monitoring the shipping service's health, maintaining dashboards, or responding to alerts. In a 12-service architecture, this means monitoring gaps and fragmented incident response. |
| **Recommendation** | Define per-service observability ownership in CODEOWNERS (e.g., `kubernetes-manifests/shippingservice.yaml @shipping-team`). Create per-service dashboards with named owners. When migrating to AWS, use CloudWatch dashboards with team tags on monitoring resources. |
| **Evidence** | `.github/CODEOWNERS` (repo-level ownership only), absence of per-service dashboards or observability configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tags found on Terraform resources. The Google provider in `terraform/providers.tf` has no `default_tags` equivalent (Google uses `default_labels` but none are configured). The GKE cluster (`terraform/main.tf`) has no labels. The Memorystore Redis instance has no labels. Kubernetes resources have basic `app: shippingservice` labels for service selection but no cost allocation, environment, or ownership labels. |
| **Gap** | No tagging governance. Cannot track costs per service, identify resource ownership during incidents, or enforce environment identification (dev/staging/prod). Kubernetes labels are functional (for selectors) but not operational (no cost/ownership/environment tags). |
| **Recommendation** | When migrating to AWS, implement a tagging standard with `default_tags` in the Terraform AWS provider (aligned with `prefer: terraform`). Required tags: `Environment`, `Service`, `Owner`, `CostCenter`. Enforce via AWS Config required-tags rule. Add Kubernetes labels: `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/managed-by`, `team`. |
| **Evidence** | `terraform/providers.tf` (no default_tags/labels), `terraform/main.tf` (no labels on GKE cluster), `terraform/memorystore.tf` (no labels), `kubernetes-manifests/shippingservice.yaml` (only `app:` label) |

---

## Learning Materials

The following learning materials correspond to the triggered pathway (**Move to AI**):

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

### Additional Recommended Learning (Based on Analysis Gaps)

While the following pathways were not triggered, significant gaps in Security (SEC: 1.71) and Operations (OPS: 1.33) warrant foundational learning:

- **Security Best Practices:** [AWS Security Fundamentals](https://skillbuilder.aws/learn/LNZ1TZQVDB) — addresses SEC-Q1 through SEC-Q7 gaps
- **Observability:** [AWS Observability Best Practices](https://aws-observability.github.io/observability-best-practices/) — addresses OPS-Q1 through OPS-Q4 gaps
- **GitOps on EKS:** [EKS Workshop - GitOps](https://www.eksworkshop.com/) — addresses deployment strategy and GitOps adoption (aligned with `prefer: gitops`, `prefer: eks`)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/shippingservice/main.go` | INF-Q1, INF-Q3, INF-Q4, APP-Q3, APP-Q4, SEC-Q3, OPS-Q1, OPS-Q3 | gRPC server entry point; tracing TODO stub; synchronous handlers; no auth interceptors |
| `src/shippingservice/quote.go` | APP-Q4, DATA-Q1, DATA-Q2, DATA-Q4 | Flat-rate shipping quote calculation; pure in-memory business logic |
| `src/shippingservice/tracker.go` | APP-Q4, DATA-Q1, DATA-Q2, DATA-Q4 | Random tracking ID generation; stateless computation |
| `src/shippingservice/go.mod` | APP-Q1, APP-Q3, INF-Q4, OPS-Q1, OPS-Q3 | Go module dependencies; gRPC, logrus, GCP profiler; indirect OpenTelemetry deps |
| `src/shippingservice/Dockerfile` | INF-Q1, APP-Q1, SEC-Q6 | Multi-stage build; distroless base image; static binary compilation |
| `src/shippingservice/shippingservice_test.go` | OPS-Q6 | 10 unit tests covering GetQuote, ShipOrder, tracking ID, quote generation |
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q8, INF-Q9, INF-Q10, SEC-Q1 | GKE Autopilot cluster; null_resource kubectl deploy; no audit logging |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2, SEC-Q5 | Managed Redis (conditional); no backup config; no encryption; sed-based connection string |
| `terraform/providers.tf` | INF-Q10, SEC-Q1, OPS-Q9 | Google provider; no default_tags/labels |
| `terraform/variables.tf` | INF-Q9 | Region default (us-central1); memorystore toggle |
| `kubernetes-manifests/shippingservice.yaml` | INF-Q1, INF-Q5, INF-Q7, APP-Q2, APP-Q6, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6, OPS-Q2, OPS-Q5 | Deployment, Service, ServiceAccount; SecurityContext; resource limits; health probes |
| `helm-chart/values.yaml` | INF-Q2, INF-Q5, INF-Q7, OPS-Q1, OPS-Q4, SEC-Q5 | Service configuration; NetworkPolicy/AuthorizationPolicy toggles; OTel disabled |
| `helm-chart/templates/shippingservice.yaml` | INF-Q5, APP-Q6, SEC-Q3, SEC-Q4, SEC-Q6 | NetworkPolicy; AuthorizationPolicy; Istio Sidecar; SecurityContext |
| `helm-chart/templates/common.yaml` | INF-Q5 | Default deny-all NetworkPolicy and AuthorizationPolicy |
| `helm-chart/Chart.yaml` | APP-Q2 | Chart version; application chart type |
| `istio-manifests/frontend-gateway.yaml` | INF-Q6 | Istio Gateway; VirtualService for frontend routing |
| `istio-manifests/frontend.yaml` | INF-Q6, APP-Q6 | VirtualService with DNS-based service reference |
| `istio-manifests/allow-egress-googleapis.yaml` | INF-Q5 | ServiceEntry for Google API egress |
| `protos/demo.proto` | INF-Q3, INF-Q4, APP-Q2, APP-Q3, APP-Q5 | gRPC service definitions; 10 services; unversioned package |
| `skaffold.yaml` | INF-Q1, INF-Q10, INF-Q11, APP-Q2, OPS-Q5 | Build config for 12 services; Kustomize deploy; kubectl deploy |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | PR CI: unit tests, GKE deploy, smoke tests; no security scanning |
| `.github/workflows/ci-main.yaml` | INF-Q11, OPS-Q6, SEC-Q7 | Main CI: unit tests, deploy, smoke tests; no security scanning |
| `cloudbuild.yaml` | INF-Q11, OPS-Q5 | Google Cloud Build; skaffold run deployment |
| `.github/workflows/helm-chart-ci.yaml` | INF-Q10, INF-Q11 | Helm lint and template validation CI |
| `.github/workflows/terraform-validate-ci.yaml` | INF-Q10, INF-Q11 | Terraform init and validate CI |
| `.github/CODEOWNERS` | OPS-Q8 | Repo-level ownership only; no per-service observability ownership |
| `.github/renovate.json5` | SEC-Q6, SEC-Q7 | Dependency update automation; not vulnerability scanning |
| `src/shippingservice/README.md` | Quick Agent Wins | Service documentation; build and test instructions |
