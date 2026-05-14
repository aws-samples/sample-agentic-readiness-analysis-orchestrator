# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | recommendationservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P1 |
| **Tags** | python, grpc, ml, recommendations |
| **Context** | Python gRPC service providing product recommendations based on cart contents. |
| **Preferences** | Prefer: EKS, DynamoDB, Bedrock, Terraform, GitOps · Avoid: Serverless, Manual Deployments |
| **Overall Score** | 2.04 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.27 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **2.04 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q3: API Authentication | 1 | No authentication on gRPC endpoints; uses `grpc.insecure_channel` with no mTLS, JWT, or OAuth2 | Unauthenticated services are vulnerable to unauthorized access; blocks secure inter-service communication and any external API exposure |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured; Terraform is GCP-focused with no audit trail resources | No forensic capability for security incidents; compliance gap for production workloads |
| 3 | OPS-Q5: Deployment Strategy | 1 | Direct-to-production deployment via `skaffold run` / `kubectl apply` with no canary or blue/green rollout | Regressions affect 100% of users immediately; no safe rollback mechanism |
| 4 | APP-Q3: Async vs Sync Communication | 1 | All inter-service communication is synchronous gRPC; no async patterns, no message queues | Tight coupling between services; cascading failures when downstream services are slow or unavailable |
| 5 | INF-Q8: Backup and Recovery | 1 | No backup configuration for any data store; Memorystore Redis has no backup plan | Data loss risk with no recovery capability; no disaster recovery posture |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3 ≥ 2). GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) automate build, deploy, and smoke tests via Skaffold. Cloud Build (`cloudbuild.yaml`) provides an alternative deployment path.
- **What it enables:** An Amazon Bedrock-powered DevOps agent that triggers deployments, checks build status, queries deployment logs, and manages releases through the existing CI/CD pipeline. The agent can monitor GitHub Actions workflow runs, report on deployment status, and initiate rollbacks.
- **Additional steps:** Expose CI/CD pipeline status via GitHub Actions API. Consider migrating CI/CD to AWS CodePipeline with Terraform (per preferences) and integrating with Amazon Bedrock AgentCore for agent orchestration. Adopt GitOps (Flux or ArgoCD on EKS) to provide a declarative deployment surface for the agent.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and distributed tracing in place (OPS-Q1 = 3 ≥ 2). OpenTelemetry is instrumented in `recommendation_server.py` with `GrpcInstrumentorClient`, `GrpcInstrumentorServer`, `OTLPSpanExporter`, and `BatchSpanProcessor`. Structured JSON logging is implemented via `python-json-logger` in `logger.py`.
- **What it enables:** An Amazon Bedrock-powered observability agent that queries OpenTelemetry traces and structured logs, correlates trace spans across gRPC service boundaries, identifies latency bottlenecks in the recommendation pipeline, and suggests root causes for failures.
- **Additional steps:** Configure OTLP exporter to send traces to AWS X-Ray (via ADOT collector on EKS). Index structured logs in CloudWatch Logs Insights or OpenSearch Service for agent querying. Enable `ENABLE_TRACING=1` in production deployments.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` (170 lines) describes the full Online Boutique architecture including all 11 microservices, deployment instructions, and architecture diagrams. `protos/demo.proto` provides complete API contract definitions for all services. Helm chart `values.yaml` documents all configuration options.
- **What it enables:** An Amazon Bedrock-powered RAG knowledge agent that indexes existing documentation, protobuf definitions, and Helm values to answer developer questions about the recommendation service architecture, deployment configuration, API contracts, and inter-service dependencies.
- **Additional steps:** Generate embeddings from README.md, demo.proto, and Helm values.yaml using Amazon Bedrock Titan Embeddings. Store embeddings in Amazon OpenSearch Service (vector engine) or pgvector on Aurora PostgreSQL (per DynamoDB preference, consider DynamoDB with embedding storage). Build retrieval chain using Bedrock Knowledge Bases.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 3 ≥ 2). The recommendationservice accesses product catalog data through a well-defined gRPC API (`ProductCatalogService.ListProducts`). The protobuf schema (`demo.proto`) defines structured `Product` messages with fields: `id`, `name`, `description`, `picture`, `price_usd`, `categories`.
- **What it enables:** An Amazon Bedrock-powered data query agent that translates natural language queries into gRPC calls against the ProductCatalogService — e.g., "find all products under $50 in the clothing category" — and returns structured results.
- **Additional steps:** Expose product catalog data via a REST API layer (or gRPC-Web gateway) that the agent can invoke as a tool. Consider indexing product data in DynamoDB (per preferences) with Amazon Bedrock AgentCore for tool orchestration.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (not < 3) — microservices architecture already in place with independently deployable services |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 (not < 3) — containerized with Dockerfile, K8s manifests, Helm charts; already running on managed container orchestration (GKE Autopilot) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (not < 3) — no commercial DB engines detected; Redis is open source |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 (not < 3) — Redis is managed via Google Cloud Memorystore |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 (< 3) but contextual guard prevents trigger — no data processing workloads, no ETL, no streaming, no analytics artifacts found |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3 (not < 3) and INF-Q11 = 3 (not < 3) — primary trigger conditions not met; IaC and CI/CD are established |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent framework imports detected in source code; no vector DB, no RAG, no agent eval framework |

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

The repository contains **no AI/agent framework usage**:
- No Amazon Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK imports in `recommendation_server.py` or any other source file.
- No vector database infrastructure (no OpenSearch vector engine, no Pinecone, no pgvector, no Weaviate, no Qdrant).
- No RAG implementation patterns (no embedding generation, no vector store queries, no retrieval chains).
- No agent evaluation frameworks (no Ragas, no DeepEval, no custom eval harness).

The current recommendation algorithm in `recommendation_server.py` is a **simple random sampling** approach: it fetches all products from `ProductCatalogService.ListProducts`, filters out products already in the cart, and randomly selects up to 5 products. There is no personalization, no ML model, and no AI-driven recommendations.

#### Application Domain and Potential AI Use Cases

The recommendationservice is an ideal candidate for AI modernization given its domain:

1. **AI-Powered Product Recommendations** — Replace random sampling with Amazon Bedrock-powered personalized recommendations based on user behavior, product descriptions, and purchase history. Use Amazon Personalize or Bedrock foundation models to generate contextual recommendations.
2. **Semantic Product Search** — Use Amazon Bedrock Titan Embeddings to create vector representations of products (name, description, categories from `demo.proto` schema). Store in Amazon OpenSearch Service (vector engine) for semantic similarity search.
3. **Natural Language Product Discovery** — Build a conversational recommendation agent using Amazon Bedrock AgentCore that understands natural language queries like "find me something warm for winter under $50" and invokes the product catalog API as a tool.
4. **Recommendation Explanation** — Use Amazon Bedrock to generate natural language explanations for why products were recommended, improving user trust and engagement.

#### Quick Wins

See the **Quick Agent Wins** section above for immediate AI integration opportunities that leverage existing infrastructure (DevOps agent, Observability agent, RAG knowledge agent, Data query agent).

#### Recommended AI Services (per preferences: prefer Bedrock)

- **Amazon Bedrock** — Foundation model access for recommendation generation, product description understanding, and conversational agents
- **Amazon Bedrock AgentCore** — Agent orchestration for multi-step recommendation workflows (e.g., retrieve user context → query product catalog → generate personalized recommendations)
- **Amazon Bedrock Knowledge Bases** — RAG over product documentation and service architecture docs
- **Amazon OpenSearch Service** (vector engine) — Vector storage for product embeddings enabling semantic search
- **Amazon Personalize** — Purpose-built recommendation engine for user-item interaction data

#### Foundation Requirements

Before AI integration, the following foundations need to be in place:

1. **User behavior data collection** — Currently, no user behavior is tracked. Implement event capture for product views, cart additions, and purchases to feed recommendation models.
2. **Product embedding pipeline** — Generate and maintain vector embeddings for the product catalog using Bedrock Titan Embeddings.
3. **API surface for agent tools** — Expose ProductCatalogService and RecommendationService via gRPC-Web or REST gateway so Bedrock agents can invoke them as tools.
4. **AWS infrastructure** — Migrate from GCP to AWS (EKS per preferences) with Terraform to deploy Bedrock-integrated recommendation service.

#### Learning Resources

- [Move to AI — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The recommendationservice is fully containerized with a multi-stage `Dockerfile` (Python 3.14-alpine base). Kubernetes Deployment and Service manifests deploy it as a container workload. Terraform in `main.tf` provisions a GKE Autopilot cluster (`enable_autopilot = true`), which is fully managed container orchestration. Skaffold (`skaffold.yaml`) builds and deploys all 12 services as container images. No raw EC2/VM compute detected. The Helm chart (`helm-chart/templates/recommendationservice.yaml`) provides templated Kubernetes resources with resource requests/limits (100m–200m CPU, 220Mi–450Mi memory). |
| **Gap** | Infrastructure is GCP-native (GKE Autopilot), not AWS. Migration to AWS managed container orchestration (EKS per preferences) is needed for AWS modernization. No Fargate or ECS resources defined. |
| **Recommendation** | Migrate to Amazon EKS with Terraform (per preferences). Reuse existing Dockerfile and Helm charts — they are cloud-agnostic. Define EKS cluster, node groups, and IAM roles in Terraform. Consider EKS with Graviton-based node groups for cost optimization. Adopt GitOps (ArgoCD or Flux on EKS) for declarative deployments. |
| **Evidence** | `src/recommendationservice/Dockerfile`, `terraform/main.tf` (GKE Autopilot), `kubernetes-manifests/recommendationservice.yaml`, `helm-chart/templates/recommendationservice.yaml`, `skaffold.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | `terraform/memorystore.tf` provisions Google Cloud Memorystore Redis 7.0 (`google_redis_instance.redis-cart`), a fully managed Redis instance for the cart service. The recommendationservice itself has no direct database dependency — it fetches data from ProductCatalogService via gRPC. Helm values (`cartDatabase.type: redis`, `connectionString: "redis-cart:6379"`) configure the cart database. An in-cluster Redis option exists as fallback. |
| **Gap** | Database management is managed for what exists (Redis via Memorystore), but the infrastructure is GCP-native. No AWS managed database resources (RDS, ElastiCache, DynamoDB) are defined. Memorystore Redis is single-instance with no replica configuration. |
| **Recommendation** | When migrating to AWS, replace Memorystore Redis with Amazon ElastiCache for Redis or Amazon MemoryDB. Define with Terraform (per preferences). For the recommendation service specifically, consider DynamoDB (per preferences) for storing user behavior data and recommendation model outputs when implementing AI-powered recommendations. |
| **Evidence** | `terraform/memorystore.tf`, `helm-chart/values.yaml` (cartDatabase section) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service detected. No Step Functions, Temporal, Camunda, Airflow, or equivalent. The recommendation logic in `recommendation_server.py` is a single synchronous function (`ListRecommendations`) that fetches products, filters, samples, and returns. The checkout flow (orchestrated by `checkoutservice`) uses direct synchronous gRPC calls, not a workflow engine. |
| **Gap** | All orchestration logic is hardcoded in application code. The checkout flow (payment → shipping → email → recommendations) has no dedicated workflow engine for error handling, retries, or state management. |
| **Recommendation** | Introduce AWS Step Functions (defined in Terraform per preferences) for the checkout orchestration workflow. This would provide visual workflow management, automatic retry logic, error handling, and state persistence. The recommendation service could be invoked as a Step Functions task. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (inline logic), `protos/demo.proto` (synchronous RPC definitions) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure detected. No SQS, SNS, EventBridge, Kafka, RabbitMQ, Kinesis, or MSK. All inter-service communication is synchronous gRPC. The `recommendation_server.py` makes a synchronous `product_catalog_stub.ListProducts(demo_pb2.Empty())` call. The protobuf definitions in `demo.proto` define only unary RPCs with no streaming RPCs. |
| **Gap** | All communication is synchronous HTTP/gRPC with no async patterns. No event-driven architecture. No decoupling between services for resilience. |
| **Recommendation** | Introduce Amazon SNS/SQS (defined in Terraform per preferences) for event-driven communication. For example, product catalog updates could be published as events, and the recommendation service could consume them asynchronously to pre-compute recommendations. Consider Amazon EventBridge for event routing across services. |
| **Evidence** | `src/recommendationservice/recommendation_server.py`, `protos/demo.proto` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes NetworkPolicy support is available via Helm chart (`networkPolicies.create` option in `values.yaml`). When enabled, fine-grained NetworkPolicies restrict ingress to recommendationservice to only the frontend pod on port 8080. Istio service mesh manifests (`istio-manifests/`) provide Sidecar egress restrictions and AuthorizationPolicy (when `authorizationPolicies.create` is enabled). Pod security context is well-configured: `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities: drop ALL`. GKE Autopilot manages VPC/subnet configuration. |
| **Gap** | NetworkPolicies and AuthorizationPolicies are available but **not enabled by default** (`networkPolicies.create: false`, `authorizationPolicies.create: false` in `values.yaml`). No explicit VPC/subnet configuration in the repo (managed by GKE Autopilot). |
| **Recommendation** | Enable NetworkPolicies and Istio AuthorizationPolicies by default in production Helm values. When migrating to EKS (per preferences), define VPC with private subnets, security groups, and NACLs in Terraform. Use Calico or Cilium for network policies on EKS. |
| **Evidence** | `helm-chart/values.yaml` (networkPolicies, authorizationPolicies, securityContext), `helm-chart/templates/recommendationservice.yaml` (NetworkPolicy, AuthorizationPolicy, Sidecar), `kubernetes-manifests/recommendationservice.yaml` (securityContext), `istio-manifests/` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Istio Gateway (`istio-manifests/frontend-gateway.yaml`) provides an ingress point for the frontend service on port 80. The recommendationservice is an internal ClusterIP service (`kubernetes-manifests/recommendationservice.yaml`, type: ClusterIP) — not directly exposed externally. The frontend service has a LoadBalancer-type Service for external access. No API Gateway with throttling, authentication, or request validation is configured for any service. |
| **Gap** | No API Gateway with throttling, auth, or request validation. The Istio Gateway is minimal (port 80, HTTP, no TLS, no rate limiting). Internal gRPC services have no per-service traffic management beyond Kubernetes Service load balancing. |
| **Recommendation** | When migrating to EKS (per preferences), deploy AWS Application Load Balancer with gRPC support as the entry point. Use AWS App Mesh or Istio on EKS for internal service mesh with mTLS, traffic management, and circuit breaking. Define ALB and App Mesh resources in Terraform. |
| **Evidence** | `istio-manifests/frontend-gateway.yaml`, `kubernetes-manifests/recommendationservice.yaml` (ClusterIP), `helm-chart/values.yaml` (frontend.externalService) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GKE Autopilot (`terraform/main.tf`, `enable_autopilot = true`) automatically manages node provisioning and scaling based on pod resource requests. The recommendation service has defined resource requests (CPU: 100m, Memory: 220Mi) and limits (CPU: 200m, Memory: 450Mi) in both `kubernetes-manifests/recommendationservice.yaml` and Helm chart, which GKE Autopilot uses for scheduling and scaling decisions. |
| **Gap** | No explicit Horizontal Pod Autoscaler (HPA) configured for the recommendationservice. Auto-scaling is entirely dependent on GKE Autopilot's node-level scaling — there is no pod-level scaling based on CPU/memory utilization or custom metrics. |
| **Recommendation** | Add HPA configuration to the Helm chart for the recommendationservice targeting CPU utilization or gRPC request rate. When migrating to EKS (per preferences), configure Karpenter for node auto-scaling and HPA for pod-level scaling. Define min/max replicas appropriate for the workload. |
| **Evidence** | `terraform/main.tf` (enable_autopilot), `kubernetes-manifests/recommendationservice.yaml` (resources), `helm-chart/templates/recommendationservice.yaml` (resources) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found for any data store. The Memorystore Redis instance in `memorystore.tf` has no backup, snapshot, or persistence configuration. No `aws_backup_plan`, no S3 versioning, no EBS snapshot policies. The Redis instance is configured with `memory_size_gb = 1` and no RDB/AOF persistence settings. |
| **Gap** | Zero backup and recovery capability. If the Redis instance fails or is deleted, all cart data is lost with no recovery option. No documented restore procedures. |
| **Recommendation** | When migrating to AWS, configure Amazon ElastiCache for Redis with automatic backups, snapshot retention, and point-in-time recovery. Use AWS Backup for centralized backup management. Define backup plans in Terraform (per preferences). For the recommendationservice, if user behavior data is introduced (for AI recommendations), ensure DynamoDB (per preferences) has point-in-time recovery enabled. |
| **Evidence** | `terraform/memorystore.tf` (no backup config) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot is deployed as a regional cluster in `us-central1` (`terraform/variables.tf`, `region = "us-central1"`), which spans multiple availability zones by default. However, the Memorystore Redis instance (`memorystore.tf`) is a single-instance configuration (`memory_size_gb = 1`) with no replica, no failover, and no explicit multi-AZ configuration. The Kubernetes Deployment for recommendationservice has no `replicas` field specified (defaults to 1). |
| **Gap** | Redis is single-instance with no failover. Recommendation service defaults to a single replica with no explicit multi-AZ pod distribution (no topology spread constraints or pod anti-affinity rules). |
| **Recommendation** | When migrating to EKS (per preferences), configure at least 2 replicas for the recommendationservice with pod anti-affinity rules across availability zones. Use ElastiCache for Redis with Multi-AZ and automatic failover. Define topology spread constraints in Helm chart. |
| **Evidence** | `terraform/variables.tf` (region: us-central1), `terraform/memorystore.tf` (single instance), `kubernetes-manifests/recommendationservice.yaml` (no replicas specified) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Terraform (`terraform/`) defines GKE cluster and Memorystore Redis. Kubernetes manifests (`kubernetes-manifests/`) define all 12 service deployments. Helm chart (`helm-chart/`) provides templated, parameterized Kubernetes resources with extensive configuration options. Kustomize (`kustomize/`) provides base/overlay composition. Skaffold (`skaffold.yaml`) orchestrates build and deployment. CI validates Terraform (`terraform-validate-ci.yaml`), Helm (`helm-chart-ci.yaml`), and Kustomize (`kustomize-build-ci.yaml`). |
| **Gap** | IaC covers compute (GKE) and one data store (Redis), but networking, monitoring, alerting, DNS, and secrets management are not defined in IaC. Multiple deployment tools (Terraform + kubectl + Skaffold + Helm + Kustomize) without clear separation of concerns. |
| **Recommendation** | Consolidate IaC strategy. When migrating to AWS, use Terraform (per preferences) for all infrastructure (EKS, VPC, ElastiCache, IAM, CloudWatch) and Helm + GitOps (ArgoCD/Flux on EKS per preferences) for application deployment. Avoid manual-deployments (per preferences) by ensuring all resources are in Terraform. |
| **Evidence** | `terraform/main.tf`, `terraform/memorystore.tf`, `kubernetes-manifests/`, `helm-chart/`, `kustomize/`, `skaffold.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides comprehensive CI/CD. PR pipeline (`ci-pr.yaml`): code-tests (Go unit tests for shippingservice/productcatalogservice/frontend, C# unit tests for cartservice) → deployment-tests (Skaffold build + deploy to GKE PR namespace → wait for pods → smoke test via loadgenerator). Main pipeline (`ci-main.yaml`): same structure for pushes to main/release branches. Cloud Build (`cloudbuild.yaml`) provides an alternative deployment path via Skaffold. Separate CI workflows validate Terraform, Helm charts, and Kustomize builds. |
| **Gap** | No automated rollback mechanism. No Python-specific tests for the recommendationservice (CI only runs Go and C# tests). Smoke tests check for zero errors but don't validate recommendation quality. No security scanning stage in the pipeline. Deployment is `kubectl apply` / `skaffold run` — not canary or blue/green. |
| **Recommendation** | Add Python unit tests for recommendationservice to the CI pipeline. Integrate security scanning (SAST, dependency scanning). When migrating to AWS, consider AWS CodePipeline + CodeBuild with Terraform (per preferences), or maintain GitHub Actions with GitOps (ArgoCD/Flux on EKS per preferences) for automated, declarative deployments with automatic rollback. Avoid manual-deployments (per preferences). |
| **Evidence** | `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `cloudbuild.yaml`, `skaffold.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The recommendationservice is written in **Python** (3.14, based on the Dockerfile `python:3.14.3-alpine` base image). Python has a mature cloud-native ecosystem with extensive library support for gRPC (`grpcio`), OpenTelemetry instrumentation (`opentelemetry-distro`, `opentelemetry-instrumentation-grpc`), structured logging (`python-json-logger`), and protocol buffers (`protobuf`). The broader microservices demo uses Go, C#, Java, Node.js, and Python — all tier-1 cloud-native languages. |
| **Gap** | No gap. Python is a mature cloud-native language with extensive AWS SDK support (`boto3`), Bedrock integration, and rich ecosystem for AI/ML workloads — which aligns well with the recommendation service's domain. |
| **Recommendation** | No immediate action needed. When integrating AI capabilities (per Move to AI pathway), Python is the ideal language for Amazon Bedrock SDK integration, LangChain, and ML model inference. |
| **Evidence** | `src/recommendationservice/Dockerfile` (python:3.14.3-alpine), `src/recommendationservice/requirements.txt`, `src/recommendationservice/recommendation_server.py` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application follows a **microservices architecture** with 12 independently deployable services visible in `src/` (adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, loadgenerator, paymentservice, productcatalogservice, recommendationservice, shippingservice, shoppingassistantservice). Each service has its own Dockerfile, Kubernetes Deployment, Service, and ServiceAccount. The `protos/demo.proto` file defines clear service boundaries with well-defined RPC interfaces. The recommendationservice has a single dependency on ProductCatalogService via gRPC. |
| **Gap** | The protobuf definition is a **monolithic proto file** (`demo.proto`) shared across all 12 services — all service definitions and message types are in a single file. This creates coupling: changes to any service's proto definition require regeneration for all services. No per-service proto files. Shared ServiceAccount naming convention but no explicit module boundary enforcement. |
| **Recommendation** | Split `demo.proto` into per-service proto files (e.g., `recommendation.proto`, `product_catalog.proto`) to decouple service interface definitions. Adopt proto package versioning (e.g., `hipstershop.recommendation.v1`). This reduces blast radius of proto changes and enables independent service evolution. |
| **Evidence** | `src/` (12 service directories), `protos/demo.proto` (monolithic proto), `kubernetes-manifests/recommendationservice.yaml` (independent Deployment), `helm-chart/templates/recommendationservice.yaml` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **All** inter-service communication is synchronous gRPC. The `recommendation_server.py` makes a synchronous call: `cat_response = product_catalog_stub.ListProducts(demo_pb2.Empty())`. The `demo.proto` defines only unary (request/response) RPCs — no server streaming, client streaming, or bidirectional streaming RPCs. No message queues, no event-driven patterns, no pub/sub, no async communication infrastructure anywhere in the repository. |
| **Gap** | 100% synchronous communication. If ProductCatalogService is slow or unavailable, the recommendation request blocks and eventually times out. No circuit breaker, no fallback, no async pre-computation of recommendations. |
| **Recommendation** | Introduce async patterns for the recommendation pipeline: (1) Use Amazon SNS/SQS to publish product catalog change events and pre-compute recommendations asynchronously. (2) Cache recommendation results in ElastiCache/DynamoDB (per preferences) to avoid synchronous calls on every request. (3) Implement circuit breaker pattern (e.g., using `tenacity` library in Python) for the ProductCatalogService call. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (synchronous gRPC call), `protos/demo.proto` (unary RPCs only) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `ListRecommendations` RPC in `recommendation_server.py` is a quick operation: fetch all products from ProductCatalogService, filter out cart items, randomly sample up to 5 products, and return. This completes in milliseconds under normal conditions. No long-running operations (>30s) are detected in the recommendationservice. No background job frameworks (Celery, Bull, SQS workers) are present. |
| **Gap** | While no long-running operations currently exist, there is no async infrastructure available if needed in the future. When AI-powered recommendations are introduced (per Move to AI pathway), model inference may take longer and would benefit from async handling. The gRPC server uses a thread pool (`max_workers=10`) which could exhaust under load. |
| **Recommendation** | As AI capabilities are introduced, implement async job processing for recommendation generation. Use Amazon SQS workers or Step Functions (defined in Terraform per preferences) for model inference operations that may exceed request timeouts. Add status polling endpoints for long-running recommendation computations. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (ListRecommendations method, ThreadPoolExecutor max_workers=10) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. The protobuf package is `hipstershop` with no version prefix (`package hipstershop;` in `demo.proto`). No `/v1/` URL patterns, no `Accept-Version` headers, no versioning annotations. The gRPC service path is `/hipstershop.RecommendationService/ListRecommendations` (visible in the Istio AuthorizationPolicy in the Helm chart). No changelog or API evolution documentation. |
| **Gap** | Breaking changes to the proto schema affect all consumers simultaneously. No backward compatibility guarantees. No deprecation strategy for old fields or RPCs. |
| **Recommendation** | Adopt protobuf versioning: rename package to `hipstershop.recommendation.v1` and create per-service proto files. Follow protobuf backward compatibility rules (never reuse field numbers, only add optional fields). Add API version metadata to gRPC service reflection. Document breaking change policy. |
| **Evidence** | `protos/demo.proto` (package hipstershop, no version), `helm-chart/templates/recommendationservice.yaml` (AuthorizationPolicy path) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes DNS-based service discovery is used. The recommendationservice connects to ProductCatalogService via environment variable `PRODUCT_CATALOG_SERVICE_ADDR` set to `"productcatalogservice:3550"` in both `kubernetes-manifests/recommendationservice.yaml` and the Helm chart. This leverages Kubernetes ClusterIP Service DNS resolution. Istio VirtualService and Sidecar resources (optional) provide additional service mesh-level discovery. The `recommendation_server.py` reads the address from `os.environ.get('PRODUCT_CATALOG_SERVICE_ADDR', '')`. |
| **Gap** | Service endpoints are configured via static environment variables in Kubernetes manifests rather than dynamic service discovery. Changing a service endpoint requires redeploying manifests. No service registry or API catalog. When Istio is not enabled, there is no mTLS, circuit breaking, or advanced traffic management for service-to-service calls. |
| **Recommendation** | When migrating to EKS (per preferences), maintain Kubernetes DNS service discovery and add AWS App Mesh or Istio on EKS for mTLS, circuit breaking, and traffic management. Consider deploying AWS Cloud Map for service discovery across namespaces or clusters. |
| **Evidence** | `kubernetes-manifests/recommendationservice.yaml` (PRODUCT_CATALOG_SERVICE_ADDR env var), `helm-chart/templates/recommendationservice.yaml` (env var), `src/recommendationservice/recommendation_server.py` (os.environ.get), `istio-manifests/` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage detected in the repository. The recommendationservice does not store any data — it fetches product catalog data from ProductCatalogService via synchronous gRPC call (`product_catalog_stub.ListProducts`). No S3 buckets, no file storage, no document management, no Textract, no document parsing libraries in `requirements.txt`. The product catalog data itself is served from a JSON file in the productcatalogservice (Go service), not from object storage. |
| **Gap** | No unstructured data storage capability. Product images (referenced in `demo.proto` as `Product.picture`) are not managed through a parsing pipeline. No capability to process or analyze unstructured data such as product reviews, images, or user-generated content. |
| **Recommendation** | When implementing AI-powered recommendations, store product images and descriptions in Amazon S3 with metadata. Use Amazon Bedrock for multimodal product understanding (image + text). Consider Amazon Textract or Bedrock for parsing product catalogs if migrating from static JSON to dynamic content. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (no file storage), `src/recommendationservice/requirements.txt` (no storage SDKs), `protos/demo.proto` (Product.picture field) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The recommendationservice accesses product data exclusively through the ProductCatalogService gRPC API — a clean, service-level data access pattern. The gRPC stub (`product_catalog_stub`) is created once at startup and reused for all requests. The `demo.proto` defines the data contract (`ListProducts`, `GetProduct`, `SearchProducts` RPCs). The cart service accesses Redis through a dedicated cart service layer. No scattered database connections. |
| **Gap** | While the service-level data access pattern is clean, it is incidental to the simple architecture rather than an explicit architectural decision with a unified data access layer. There is no data access abstraction, no repository pattern, no caching layer. The `product_catalog_stub` is a global variable, not injected via dependency injection. |
| **Recommendation** | Introduce a data access abstraction layer with caching (ElastiCache/DynamoDB per preferences) to reduce synchronous dependency on ProductCatalogService. Implement dependency injection for the product catalog client to improve testability. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (product_catalog_stub global), `protos/demo.proto` (ProductCatalogService RPCs) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Memorystore Redis instance in `terraform/memorystore.tf` explicitly pins the engine version to `REDIS_7_0` (`redis_version = "REDIS_7_0"`). Redis 7.0 is actively maintained and not approaching EOL. The Helm chart `values.yaml` references an in-cluster Redis with the public Docker Hub image (`cartDatabase.inClusterRedis.publicRepository: true`) but does not pin the Redis container image version explicitly. |
| **Gap** | Only one database engine exists (Redis), and its version is pinned in Terraform. However, the in-cluster Redis fallback (used when Memorystore is not enabled) does not pin a specific Redis version — it pulls the latest public image. |
| **Recommendation** | Pin the in-cluster Redis container image version in Helm values to prevent unexpected version changes. When migrating to AWS, use Amazon ElastiCache for Redis with explicit engine version pinning (Redis 7.x) in Terraform. |
| **Evidence** | `terraform/memorystore.tf` (redis_version = "REDIS_7_0"), `helm-chart/values.yaml` (cartDatabase section) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, no SQL, no proprietary database constructs detected anywhere in the repository. The recommendationservice has zero direct database access — all business logic is in the Python application layer (`recommendation_server.py`). The recommendation algorithm (fetch products, filter, random sample) is entirely in-code. No `.sql` files, no `CREATE PROCEDURE`, no ORM bypass patterns, no raw SQL execution in the codebase. Redis (the only database) is used as a key-value cache by the cart service with no stored procedures. |
| **Gap** | No gap. All business logic is in the application layer, which is the ideal pattern for modernization flexibility. |
| **Recommendation** | No action needed. Maintain this pattern as the application evolves — keep business logic in the application layer, not in database-specific constructs. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (all logic in Python), `protos/demo.proto` (no SQL references) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configured in the repository. The Terraform in `terraform/main.tf` is GCP-focused (GKE Autopilot, Memorystore) with no audit logging resources. The GCP APIs enabled include `monitoring.googleapis.com` and `cloudtrace.googleapis.com` but no explicit audit logging configuration. No `aws_cloudtrail` resources, no S3 bucket for log storage, no log file validation. |
| **Gap** | No audit logging infrastructure. No ability to trace who made what changes, no forensic capability for security incidents, and no compliance posture for production workloads. |
| **Recommendation** | When migrating to AWS, define AWS CloudTrail with log file validation and immutable storage (S3 with Object Lock) in Terraform (per preferences). Enable CloudTrail for all management events and data events on sensitive resources. Integrate with CloudWatch Logs for real-time alerting. |
| **Evidence** | `terraform/main.tf` (no audit logging), `terraform/` (no CloudTrail resources) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration found. The Memorystore Redis instance in `terraform/memorystore.tf` has no `transit_encryption_mode` or `auth_enabled` configuration. No KMS key resources defined anywhere in the Terraform. No encryption configuration on any data store or storage resource. |
| **Gap** | No encryption at rest for any data store. Cart data in Redis is unencrypted. No KMS key management infrastructure. |
| **Recommendation** | When migrating to AWS, configure encryption at rest on all data stores. Use AWS KMS customer-managed keys for ElastiCache (Redis), DynamoDB (per preferences), and S3. Define KMS keys and encryption configuration in Terraform (per preferences). Enable encryption for all new resources by default. |
| **Evidence** | `terraform/memorystore.tf` (no encryption config) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No authentication on gRPC endpoints. The `recommendation_server.py` creates an insecure gRPC channel to ProductCatalogService: `channel = grpc.insecure_channel(catalog_addr)`. The gRPC server listens on an insecure port: `server.add_insecure_port('[::]:'+port)`. No auth middleware, no JWT/OAuth2 validation, no mTLS. The Istio AuthorizationPolicy in the Helm chart (`authorizationPolicies.create: false` in `values.yaml`) is available but disabled by default. When enabled, it restricts calls to specific Kubernetes ServiceAccount principals — but this is L4/L7 authorization, not per-request authentication with tokens. |
| **Gap** | All gRPC endpoints are unauthenticated. Any pod in the cluster can call the recommendation service. No per-request identity verification, no token validation, no audit trail of who called what. |
| **Recommendation** | Enable Istio AuthorizationPolicies as a first step for service-to-service authorization. When migrating to EKS (per preferences), implement mTLS via Istio or App Mesh for service identity. For external-facing APIs, add gRPC interceptor-based JWT/OAuth2 authentication. Define authentication infrastructure in Terraform. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (grpc.insecure_channel, add_insecure_port), `helm-chart/values.yaml` (authorizationPolicies.create: false), `helm-chart/templates/recommendationservice.yaml` (AuthorizationPolicy) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, Okta, Auth0, Ping, or SAML/OIDC configuration. The frontend generates session IDs for all users automatically with no login required (per README: "Does not require signup/login"). Kubernetes ServiceAccounts are used for pod identity (`serviceAccountName: recommendationservice`) but these are cluster-level, not application-level identity. |
| **Gap** | No centralized identity provider. No user authentication, no SSO, no federated identity. The application operates with anonymous sessions only. |
| **Recommendation** | When migrating to AWS, integrate Amazon Cognito for user authentication and SSO. Use Cognito User Pools for sign-up/login and Cognito Identity Pools for federated access. Define Cognito resources in Terraform (per preferences). For service-to-service identity, use IAM Roles for Service Accounts (IRSA) on EKS. |
| **Evidence** | `README.md` ("Does not require signup/login"), `kubernetes-manifests/recommendationservice.yaml` (ServiceAccount), `helm-chart/values.yaml` (serviceAccounts section) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Environment variables are used for service configuration: `PORT`, `PRODUCT_CATALOG_SERVICE_ADDR`, `ENABLE_TRACING`, `DISABLE_PROFILER`, `COLLECTOR_SERVICE_ADDR`, `GCP_PROJECT_ID`. These are non-sensitive configuration values (service addresses, feature flags). No hardcoded secrets (passwords, API keys, tokens) found in `recommendation_server.py` or any other source file. No Secrets Manager, Vault, or sealed secrets configuration. The Redis connection string (`redis-cart:6379`) in Helm values is a service address, not a credential. |
| **Gap** | No secrets management infrastructure exists. While the current service has minimal secrets to manage, there is no foundation for secrets management when credentials are introduced (e.g., database passwords for AI model endpoints, API keys for Bedrock). No rotation, no audit trail for secret access. |
| **Recommendation** | When migrating to AWS, configure AWS Secrets Manager with automatic rotation for all credentials. Define secrets resources and IAM policies in Terraform (per preferences). Use External Secrets Operator on EKS (per preferences) to sync AWS Secrets Manager secrets to Kubernetes Secrets. Ensure all future credentials (Bedrock API keys, DynamoDB access) are managed through Secrets Manager, not environment variables. |
| **Evidence** | `kubernetes-manifests/recommendationservice.yaml` (env vars), `src/recommendationservice/recommendation_server.py` (os.environ.get), `helm-chart/values.yaml` (cartDatabase.connectionString) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Container security context is well-configured in both Kubernetes manifests and Helm chart: `runAsNonRoot: true`, `runAsUser: 1000`, `runAsGroup: 1000`, `fsGroup: 1000`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities: drop ALL`, `privileged: false`. The Dockerfile uses a multi-stage build with Alpine base image (`python:3.14.3-alpine`) with a specific SHA256 digest pin. Seccomp profile support is available but disabled by default (`seccompProfile.enable: false` in `values.yaml`). |
| **Gap** | No vulnerability scanning (no AWS Inspector, no Snyk, no Trivy, no ECR image scanning). No patching strategy — the Alpine base image is pinned to a digest but there is no automated process to detect and update when CVEs are found in the base image. Renovate updates Python dependencies but does not scan for security vulnerabilities. |
| **Recommendation** | Integrate container image scanning into the CI/CD pipeline (Amazon ECR image scanning, Trivy, or Snyk). Enable seccomp profiles by default. When migrating to EKS (per preferences), use Bottlerocket OS for nodes and enable Amazon Inspector for runtime vulnerability detection. Configure Renovate or Dependabot to flag security-critical dependency updates. |
| **Evidence** | `kubernetes-manifests/recommendationservice.yaml` (securityContext), `helm-chart/templates/recommendationservice.yaml` (securityContext), `src/recommendationservice/Dockerfile` (alpine, digest pin), `helm-chart/values.yaml` (seccompProfile.enable: false) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools in the CI/CD pipeline. The CI workflows (`ci-pr.yaml`, `ci-main.yaml`) run unit tests and smoke tests but have no security scanning stage. No SonarQube, Semgrep, CodeGuru, Snyk, or `pip-audit` integration. However, Renovate (`renovate.json5`) is configured for automated dependency updates with `pip-compile` enabled — this provides some dependency freshness but is not security-focused scanning. No `.snyk` policy file, no `npm audit`, no container scanning in CI. |
| **Gap** | No automated security scanning in the CI/CD pipeline. Vulnerabilities in Python dependencies (`requirements.txt`) are not detected before deployment. No container image scanning. No blocking gate for critical security findings. |
| **Recommendation** | Add security scanning stages to the CI pipeline: (1) `pip-audit` or Snyk for Python dependency vulnerability scanning. (2) Trivy or Amazon ECR image scanning for container images. (3) Semgrep or SonarQube for SAST. Configure security gates to block deployment on critical/high findings. When migrating to AWS, integrate Amazon CodeGuru Reviewer and Amazon Inspector. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (no security scanning), `.github/workflows/ci-main.yaml` (no security scanning), `.github/renovate.json5` (dependency updates, not security scanning) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry is instrumented in `recommendation_server.py` with comprehensive gRPC instrumentation: `GrpcInstrumentorClient()` and `GrpcInstrumentorServer()` instrument both outgoing calls to ProductCatalogService and incoming recommendation requests. `OTLPSpanExporter` exports traces via OTLP protocol to a configurable collector endpoint (`COLLECTOR_SERVICE_ADDR`, defaulting to `localhost:4317`). `BatchSpanProcessor` batches spans for efficient export. Dependencies in `requirements.txt` include `opentelemetry-distro`, `opentelemetry-instrumentation-grpc`, `opentelemetry-exporter-otlp-proto-grpc`, and `opentelemetry-sdk`. The Helm chart conditionally enables tracing (`ENABLE_TRACING=1`) and configures the collector endpoint when `opentelemetryCollector.create` is true. |
| **Gap** | Tracing is **conditional** — requires `ENABLE_TRACING=1` environment variable to be set, which is only enabled when `googleCloudOperations.tracing: true` in Helm values (defaults to `false`). If `ENABLE_TRACING` is not set, the tracing setup is silently skipped via `KeyError` exception handling. The OpenTelemetry collector (`opentelemetryCollector.create: false` in values.yaml) is not deployed by default. |
| **Recommendation** | Enable tracing by default in production Helm values. When migrating to EKS (per preferences), deploy AWS Distro for OpenTelemetry (ADOT) collector as a DaemonSet and configure OTLP exporter to send traces to AWS X-Ray. The existing OpenTelemetry instrumentation is cloud-agnostic and will work with AWS X-Ray via ADOT. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (OpenTelemetry setup), `src/recommendationservice/requirements.txt` (OTel dependencies), `helm-chart/values.yaml` (opentelemetryCollector, googleCloudOperations.tracing), `helm-chart/templates/recommendationservice.yaml` (ENABLE_TRACING env var) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No latency targets (p99, p95) for the recommendation gRPC endpoint. No error rate thresholds. No error budget tracking. No CloudWatch alarms, no Prometheus alerting rules, no GCP monitoring configuration beyond the `monitoring.googleapis.com` API being enabled. No SLO definition files, no SLO dashboards referenced. |
| **Gap** | No formal definition of acceptable service levels. Cannot measure whether the recommendation service is meeting user expectations. No data-driven basis for prioritizing improvements or modernization investments. |
| **Recommendation** | Define SLOs for the recommendationservice: (1) Availability SLO: 99.9% of ListRecommendations calls succeed. (2) Latency SLO: p99 latency < 200ms. (3) Error budget: 0.1% monthly. When migrating to AWS, implement SLOs using CloudWatch SLIs with custom metrics from OpenTelemetry. Define in Terraform (per preferences). |
| **Evidence** | No SLO files found in repository. `terraform/main.tf` (monitoring API enabled but no SLOs defined), `helm-chart/values.yaml` (no SLO configuration) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. The recommendation service logs a single info-level message per request: `logger.info("[Recv ListRecommendations] product_ids={}".format(prod_list))`. Structured JSON logging is configured via `python-json-logger` in `logger.py` with timestamp and severity fields. However, no custom metrics are emitted for: number of recommendations served, recommendation diversity, products filtered out, cache hit/miss rates, or user engagement with recommendations. |
| **Gap** | Only infrastructure metrics (if GKE monitoring is enabled). No business outcome metrics. Cannot measure recommendation quality, user engagement, or business impact of the service. |
| **Recommendation** | Add custom metrics using OpenTelemetry Metrics SDK: (1) `recommendations.served` counter. (2) `recommendations.filtered_products` histogram. (3) `recommendations.latency` histogram. (4) `recommendations.catalog_size` gauge. When migrating to AWS, export metrics to CloudWatch via ADOT collector. Consider using CloudWatch Embedded Metric Format for business metrics in structured logs. |
| **Evidence** | `src/recommendationservice/recommendation_server.py` (single log line, no metrics), `src/recommendationservice/logger.py` (JSON logging only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. No error rate monitoring, no latency monitoring, no health check alerting beyond the Kubernetes liveness/readiness probes (which restart the pod but don't alert humans). |
| **Gap** | No alerting for degraded performance, elevated error rates, or unexpected behavior. The only failure detection is Kubernetes liveness probes, which auto-restart pods but don't notify operators. |
| **Recommendation** | When migrating to AWS, configure CloudWatch Alarms for: (1) p99 latency exceeding SLO threshold. (2) Error rate exceeding error budget burn rate. (3) Pod restart count. Integrate with Amazon SNS for notification routing to PagerDuty/OpsGenie. Consider CloudWatch Anomaly Detection for adaptive thresholds. Define alarms in Terraform (per preferences). |
| **Evidence** | `kubernetes-manifests/recommendationservice.yaml` (liveness/readiness probes only), No alerting configuration found in repository |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Deployment is direct-to-production via `skaffold run` (which uses `kubectl apply`). The CI/CD pipeline (`ci-pr.yaml`) deploys to a PR-specific namespace for testing, but the main pipeline (`ci-main.yaml`) deploys directly. Cloud Build (`cloudbuild.yaml`) also uses `skaffold run` for direct deployment. No canary deployments, no blue/green, no traffic shifting, no feature flags, no progressive delivery tools (Argo Rollouts, Flagger). The Skaffold deploy strategy is `kubectl: {}` — plain kubectl apply. |
| **Gap** | Direct-to-production deployment with no staged rollout. A regression affects 100% of users immediately. No automated rollback. No traffic shifting to validate new versions before full rollout. |
| **Recommendation** | Implement progressive delivery. When migrating to EKS (per preferences), use ArgoCD with Argo Rollouts for canary deployments (aligned with GitOps preference). Define canary analysis with success criteria based on OpenTelemetry metrics. Alternatively, use Flagger with Istio for automated canary promotion. Avoid manual-deployments (per preferences) by automating the entire promotion pipeline. |
| **Evidence** | `skaffold.yaml` (deploy: kubectl: {}), `.github/workflows/ci-pr.yaml` (skaffold run), `.github/workflows/ci-main.yaml` (skaffold run), `cloudbuild.yaml` (skaffold run) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline includes deployment-level smoke tests: the loadgenerator pod sends realistic user traffic to all services, waits for 50+ requests, and checks for zero errors (`ci-pr.yaml`, `ci-main.yaml`). This validates that the entire system works end-to-end. Go unit tests run for shippingservice, productcatalogservice, and frontend/validator. C# unit tests run for cartservice. |
| **Gap** | No Python-specific tests for the recommendationservice — not unit tests, not integration tests. The smoke test validates the overall system but doesn't specifically test recommendation quality, edge cases, or error handling. No contract tests between recommendationservice and ProductCatalogService. No test containers or mock gRPC services for isolated integration testing. |
| **Recommendation** | Add Python test suite for recommendationservice: (1) Unit tests for `ListRecommendations` logic (filtering, sampling). (2) Integration tests using `grpc_testing` or testcontainers-python. (3) Contract tests against the `demo.proto` to validate compatibility. Add `pytest` to CI pipeline alongside existing Go and C# tests. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (Go/C# tests, smoke tests, no Python tests), `.github/workflows/ci-main.yaml` (same), `src/recommendationservice/` (no test files) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no self-healing patterns beyond Kubernetes liveness probes. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files (markdown, YAML, JSON) in the repository. `SECURITY.md` provides a vulnerability reporting policy but no operational runbooks. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (ProductCatalogService down, high latency, memory pressure). No automated remediation. |
| **Recommendation** | Create operational runbooks for the recommendationservice: (1) ProductCatalogService dependency failure. (2) High latency / timeout. (3) Memory pressure / OOM. (4) Pod crash loop. When migrating to AWS, implement runbooks as SSM Automation documents (defined in Terraform per preferences). Add self-healing patterns: if ProductCatalogService is unavailable, serve cached recommendations from DynamoDB (per preferences). |
| **Evidence** | No runbook files found in repository. `.github/SECURITY.md` (vulnerability reporting only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS file exists (`.github/CODEOWNERS`) but assigns all files to `@GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver` — a single ownership group for the entire repository. No per-service observability ownership. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution. No observability config files with team tags. |
| **Gap** | No observability ownership model. No per-service dashboards or alarms. No named owners for monitoring. Cannot determine who is responsible for the recommendation service's health and performance. |
| **Recommendation** | Establish per-service observability ownership: (1) Create CloudWatch dashboards per service (defined in Terraform per preferences). (2) Tag alarms with owner team. (3) Add CODEOWNERS entries for observability configs. (4) Define SLOs with team attribution. When migrating to EKS (per preferences), use CloudWatch Container Insights for EKS and create per-service dashboards. |
| **Evidence** | `.github/CODEOWNERS` (single ownership group), No per-service dashboards found |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes labels are consistently applied: `app: recommendationservice` on Deployment, Service, ServiceAccount, and pod template across both `kubernetes-manifests/recommendationservice.yaml` and `helm-chart/templates/recommendationservice.yaml`. All services follow the same labeling convention. However, there are no AWS resource tags, no cost allocation tags, no environment tags, and no tag enforcement policies. The Terraform resources (GKE cluster, Memorystore) have no tags/labels defined. |
| **Gap** | Basic Kubernetes labels exist for service identification, but no cost allocation, environment, or ownership tagging. No tag enforcement policies. When migrating to AWS, resources will need comprehensive tagging for cost tracking, ownership, and environment identification. |
| **Recommendation** | When migrating to AWS, implement a comprehensive tagging strategy in Terraform (per preferences): (1) Add `default_tags` to the AWS provider for environment, team, project. (2) Tag all resources with `Environment`, `Team`, `CostCenter`, `Service`. (3) Enforce tagging via AWS Config rules or SCPs. (4) Activate cost allocation tags in AWS Billing. |
| **Evidence** | `kubernetes-manifests/recommendationservice.yaml` (app label), `helm-chart/templates/recommendationservice.yaml` (app label), `terraform/main.tf` (no tags), `terraform/memorystore.tf` (no labels) |

---

## Learning Materials

The following learning resources are mapped to the triggered pathway (**Move to AI**):

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to AI** | [Move to AI — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

Additional resources relevant to the analysis findings (not pathway-triggered, but useful for closing gaps):

| Topic | Learning Resources |
|-------|-------------------|
| **Containers on AWS** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |
| **Cloud Architecture** | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) · [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/recommendationservice/recommendation_server.py` | INF-Q1, INF-Q3, INF-Q4, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q3, OPS-Q6 | Main application source — gRPC server, recommendation logic, OpenTelemetry instrumentation, insecure channel usage |
| `src/recommendationservice/Dockerfile` | INF-Q1, APP-Q1, SEC-Q6 | Multi-stage Docker build, Python 3.14 Alpine base with SHA256 digest pin |
| `src/recommendationservice/requirements.txt` | APP-Q1, DATA-Q1, OPS-Q1 | Python dependencies — grpcio, OpenTelemetry, python-json-logger |
| `src/recommendationservice/requirements.in` | APP-Q1 | Direct Python dependencies (pip-compile input) |
| `src/recommendationservice/logger.py` | OPS-Q3 | Structured JSON logging configuration |
| `protos/demo.proto` | INF-Q3, INF-Q4, APP-Q2, APP-Q3, APP-Q5, DATA-Q1, DATA-Q2, DATA-Q4 | Protobuf service definitions — all 11 services, message types, RPC definitions |
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q10, SEC-Q1, OPS-Q2, OPS-Q9 | GKE Autopilot cluster, GCP API enablement, kubectl deployment |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2 | Google Cloud Memorystore Redis 7.0, single instance, no backup/encryption |
| `terraform/variables.tf` | INF-Q9 | GKE region (us-central1), cluster configuration variables |
| `kubernetes-manifests/recommendationservice.yaml` | INF-Q1, INF-Q5, INF-Q6, INF-Q7, INF-Q9, APP-Q2, APP-Q6, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6, OPS-Q4, OPS-Q9 | Kubernetes Deployment, Service, ServiceAccount — security context, resource limits, env vars |
| `helm-chart/templates/recommendationservice.yaml` | INF-Q1, INF-Q5, INF-Q7, APP-Q2, APP-Q5, APP-Q6, SEC-Q3, SEC-Q6, OPS-Q1, OPS-Q9 | Helm-templated Deployment, Service, NetworkPolicy, AuthorizationPolicy, Sidecar |
| `helm-chart/values.yaml` | INF-Q2, INF-Q5, INF-Q6, INF-Q7, DATA-Q3, SEC-Q3, SEC-Q6, OPS-Q1, OPS-Q2 | Helm default values — network policies, auth policies, security context, OTel collector, cart database config |
| `helm-chart/Chart.yaml` | INF-Q10 | Helm chart version (0.10.5), app version (v0.10.5) |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | PR CI pipeline — Go/C# tests, deployment tests with smoke tests, no security scanning |
| `.github/workflows/ci-main.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | Main CI pipeline — same structure as PR pipeline |
| `cloudbuild.yaml` | INF-Q11, OPS-Q5 | Google Cloud Build deployment via Skaffold |
| `skaffold.yaml` | INF-Q1, INF-Q10, INF-Q11, OPS-Q5 | Build and deployment orchestration — 12 service artifacts, kubectl deploy |
| `istio-manifests/frontend-gateway.yaml` | INF-Q6 | Istio Gateway for frontend ingress (port 80, HTTP) |
| `istio-manifests/frontend.yaml` | INF-Q6 | Istio VirtualService for frontend routing |
| `istio-manifests/allow-egress-googleapis.yaml` | INF-Q5 | Istio ServiceEntry for GCP API egress |
| `.github/renovate.json5` | SEC-Q7 | Renovate dependency update configuration |
| `.github/CODEOWNERS` | OPS-Q8 | Single ownership group for entire repository |
| `.github/SECURITY.md` | OPS-Q7 | Vulnerability reporting policy |
| `README.md` | SEC-Q4, Quick Agent Wins | Architecture documentation, 11 microservices description |
| `.github/workflows/terraform-validate-ci.yaml` | INF-Q10, INF-Q11 | Terraform validation CI workflow |
| `.github/workflows/helm-chart-ci.yaml` | INF-Q10, INF-Q11 | Helm chart validation CI workflow |
| `.github/workflows/kustomize-build-ci.yaml` | INF-Q10, INF-Q11 | Kustomize build validation CI workflow |
| `kustomize/` | INF-Q10 | Kustomize base/overlay/component configuration |
