# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | emailservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P2 |
| **Tags** | python, grpc, notifications |
| **Context** | Python gRPC service sending order confirmation emails. |
| **Overall Score** | 2.09 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.09 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.71 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.09 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q4: Async Messaging and Streaming | 1 | All inter-service communication is synchronous gRPC with no messaging or streaming infrastructure. | Tight coupling between services; cascading failure risk during email delivery; no event-driven decoupling for the checkout→email flow. |
| 2 | SEC-Q1: Audit Logging | 1 | No audit logging configuration (CloudTrail or equivalent) found in IaC or configuration. | No forensic audit trail for security incidents; compliance gaps for production workloads. |
| 3 | SEC-Q2: Encryption at Rest | 1 | No encryption-at-rest configuration with customer-managed keys for any data store. | Sensitive order data in transit through the email pipeline has no explicit at-rest encryption governance. |
| 4 | OPS-Q2: SLO Definitions | 1 | No SLO definitions for email delivery latency, success rate, or any critical user journey. | Cannot measure service reliability or make data-driven prioritization decisions for improvements. |
| 5 | OPS-Q4: Anomaly Detection and Alerting | 1 | No alerting or anomaly detection configured for error rates or latency. | Silent failures in email delivery; no proactive notification when the service degrades. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 — CI/CD pipeline exists with GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) that build, deploy to GKE via Skaffold, and run smoke tests.
- **What it enables:** An AI agent (powered by Amazon Bedrock) that triggers deployments, checks build status, monitors pipeline health, and manages release workflows through the existing CI/CD pipeline API. The agent can also enforce GitOps practices by validating manifest changes before merging.
- **Additional steps:** Expose GitHub Actions workflow dispatch API; create a Bedrock agent with tools for GitHub API integration; define guardrails for deployment approval workflows.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Comprehensive documentation exists in the repository — `README.md` with architecture diagrams and service descriptions, `protos/demo.proto` with full service contract definitions, Helm chart `README.md`, and Kustomize `README.md`.
- **What it enables:** A RAG-based knowledge agent (using Amazon Bedrock and Amazon OpenSearch Service as vector store) that indexes the repository documentation, proto definitions, and deployment guides. Developers can query the agent for architecture questions, service contract details, and deployment procedures.
- **Additional steps:** Index proto definitions and README files into an OpenSearch Service vector store; deploy a Bedrock Knowledge Base with the repository corpus; build a simple chat interface.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3 — OpenTelemetry is comprehensively instrumented in the emailservice with `opentelemetry-distro`, `opentelemetry-instrumentation-grpc`, `opentelemetry-exporter-otlp-proto-grpc`, and `opentelemetry-sdk`. TracerProvider with BatchSpanProcessor and OTLPSpanExporter is configured in `email_server.py`. Structured JSON logging is in place via `logger.py`.
- **What it enables:** An observability agent (powered by Amazon Bedrock) that queries distributed traces and structured logs, correlates trace spans to identify latency bottlenecks, and suggests root causes during incidents. The agent leverages the existing OpenTelemetry trace data and JSON-structured logs.
- **Additional steps:** Route OpenTelemetry data to AWS X-Ray or an OpenSearch Service observability backend; create a Bedrock agent with tools for trace and log querying; define incident correlation prompts.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — application is already a well-decomposed microservices architecture with clear service boundaries. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 — compute is already on managed container orchestration (GKE Autopilot); Dockerfile and K8s manifests exist. Contextual guard: already containerized. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected (Redis only). |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 — default deployment uses in-cluster Redis (self-managed). DATA-Q3 = 3 — version pinned but only for optional Memorystore. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but contextual guard: no data processing workloads exist — emailservice is a stateless notification service with no ETL, streaming, or analytics needs. |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3 — both primary conditions are >= 3. IaC coverage and CI/CD automation exist. |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent framework imports detected. No vector database, RAG implementation, or agent evaluation framework found in the repository. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
The platform's default deployment uses an in-cluster Redis instance (`redis-cart`) as a self-managed cache for the cart service. This is defined in `helm-chart/values.yaml` under `cartDatabase.inClusterRedis.create: true` with connection string `redis-cart:6379`. While Memorystore (managed Redis) is optionally available via `terraform/memorystore.tf`, it is disabled by default (`memorystore = false` in `terraform.tfvars`). The emailservice itself has no database dependency.

**Engine Versions and EOL Status:**
Redis 7.0 is explicitly pinned in `memorystore.tf` (`redis_version = "REDIS_7_0"`), which is current and not at EOL. However, the in-cluster Redis image tag is not explicitly pinned in Helm values, relying on the default image.

**Data Access Patterns:**
Cart data is accessed directly by the cartservice. No centralized data access layer exists across services.

**Recommended Migration Targets (respecting preferences):**
- Migrate the in-cluster Redis to **Amazon ElastiCache for Redis** or **Amazon MemoryDB for Redis** as a fully managed, multi-AZ cache with automatic failover and backups.
- For future data needs, consider **Amazon DynamoDB** (preferred per technology preferences) for any key-value or document storage needs that may arise as the platform evolves.
- Define the managed database infrastructure using **Terraform** (preferred) with the AWS provider.

**Representative AWS Services:** Amazon ElastiCache, Amazon MemoryDB, Amazon DynamoDB, Amazon RDS

**Migration Tools:** AWS Database Migration Service (DMS) for data migration if needed.

**Migration Approach:**
1. Provision ElastiCache or MemoryDB cluster via Terraform
2. Update `cartDatabase.connectionString` in Helm values to point to the managed endpoint
3. Deploy with GitOps workflow (preferred over manual deployment)
4. Validate cart functionality with existing smoke tests

**Learning Resources:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI or agent framework usage was detected in the repository. Specifically:
- No Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK imports found in any source code.
- No vector database infrastructure (OpenSearch with vector engine, Pinecone, pgvector, Weaviate, Qdrant).
- No RAG implementation patterns (embedding generation, vector store queries, retrieval chains).
- No agent evaluation frameworks (Ragas, DeepEval, custom eval harness).

**Application Domain and Potential AI Use Cases:**
The emailservice is a notification service that renders order confirmation emails from templates. AI integration opportunities include:
1. **Personalized email content** — Use Amazon Bedrock to generate personalized product recommendations or messaging within confirmation emails.
2. **Email template optimization** — Use AI to A/B test and optimize email templates for engagement.
3. **Anomaly detection in order patterns** — Use AI to flag unusual order patterns before confirmation emails are sent.
4. **Customer support integration** — Add AI-powered customer support context links in confirmation emails.

**Quick Wins:** See the Quick Agent Wins section above for immediate agent opportunities (DevOps Agent, RAG Knowledge Agent, Observability Agent).

**Recommended AI Services (respecting preferences):**
- **Amazon Bedrock** (preferred) — Foundation model access for email content generation and agent building.
- **Amazon Bedrock AgentCore** — For building agents that interact with the existing gRPC services and CI/CD pipelines.
- **Amazon OpenSearch Service** (vector engine) — For RAG-based knowledge retrieval over repository documentation.
- **Amazon Q Developer** — For developer productivity improvements across the microservices codebase.

**Foundation Requirements Before AI Integration:**
- API surface documentation (proto definitions exist but OpenAPI specs would broaden tool integration)
- Observability infrastructure (OpenTelemetry is in place — strong foundation)
- Data access layer for any training/fine-tuning data

**Learning Resources:** [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Compute runs on GKE Autopilot (managed Kubernetes) as defined in `terraform/main.tf` (`enable_autopilot = true`). All services are containerized with Dockerfiles (e.g., `src/emailservice/Dockerfile` using `python:3.14.3-alpine`) and deployed as Kubernetes Deployments with resource requests/limits (e.g., `kubernetes-manifests/emailservice.yaml`: cpu 100m-200m, memory 64Mi-128Mi). Skaffold (`skaffold.yaml`) manages the build-deploy lifecycle. This represents managed container orchestration, though on GCP rather than AWS EKS/ECS. |
| **Gap** | Infrastructure is GCP-native (GKE) rather than AWS. No AWS managed compute (EKS, ECS, Fargate) is present. While the architecture is sound, migrating to AWS would require re-provisioning the container orchestration platform. |
| **Recommendation** | Migrate to **Amazon EKS** (preferred per technology preferences) with Terraform. The existing Kubernetes manifests and Helm charts are portable to EKS with minimal changes. Use EKS managed node groups or Fargate profiles for compute. Deploy infrastructure definitions using Terraform with the AWS provider and adopt a GitOps workflow (e.g., ArgoCD or Flux) for manifest delivery. |
| **Evidence** | `terraform/main.tf` (GKE Autopilot), `src/emailservice/Dockerfile`, `kubernetes-manifests/emailservice.yaml`, `helm-chart/templates/emailservice.yaml`, `skaffold.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The only database is Redis for the cart service. The default deployment uses an in-cluster Redis instance (`cartDatabase.inClusterRedis.create: true` in `helm-chart/values.yaml`) with connection string `redis-cart:6379`. Google Cloud Memorystore (managed Redis) is optionally available via `terraform/memorystore.tf` (`google_redis_instance` with `redis_version = "REDIS_7_0"`) but is disabled by default (`memorystore = false` in `terraform.tfvars`). The emailservice itself has no database dependency. |
| **Gap** | Default deployment uses self-managed in-cluster Redis with no automated failover, backups, or patching. Managed option (Memorystore) exists but is not the default. |
| **Recommendation** | Migrate the in-cluster Redis to **Amazon ElastiCache for Redis** or **Amazon MemoryDB** using Terraform (preferred). Enable automatic failover with Multi-AZ replication. Update `cartDatabase.connectionString` in Helm values to point to the managed endpoint. |
| **Evidence** | `helm-chart/values.yaml` (cartDatabase section), `terraform/memorystore.tf`, `terraform/terraform.tfvars` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service (Step Functions, Temporal, Camunda) is used anywhere in the repository. The emailservice processes gRPC requests directly via a simple request-response pattern. The checkout service (`checkoutservice`) orchestrates the order flow (cart retrieval → payment → shipping → email) through direct synchronous gRPC calls, not through a dedicated workflow engine. |
| **Gap** | All workflow logic is hardcoded in the checkout service as sequential gRPC calls. No dedicated orchestration, no visual workflow management, no built-in retry/error handling beyond gRPC status codes. |
| **Recommendation** | Introduce AWS Step Functions to orchestrate the checkout workflow (cart → payment → shipping → email). Define the workflow as an ASL (Amazon States Language) state machine managed via Terraform (preferred). This would decouple the checkout service from direct knowledge of all downstream services and provide built-in retry logic, error handling, and workflow visibility. |
| **Evidence** | `src/emailservice/email_server.py` (direct gRPC handler), `protos/demo.proto` (service definitions showing synchronous contracts) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure exists. All inter-service communication is synchronous gRPC. The checkout service calls `emailservice.SendOrderConfirmation` synchronously. No SQS, SNS, EventBridge, Kafka, RabbitMQ, Kinesis, or any event-driven patterns were found in the codebase, IaC, or Kubernetes manifests. |
| **Gap** | All communication is synchronous. Email delivery (a non-critical, asynchronous operation by nature) blocks the checkout flow. No event-driven decoupling exists for any service-to-service communication. |
| **Recommendation** | Introduce Amazon SQS or Amazon SNS to decouple the checkout→email flow. The checkout service should publish an "order completed" event/message, and the emailservice should consume it asynchronously. Define the SQS queue or SNS topic via Terraform (preferred). This immediately decouples the checkout critical path from email delivery latency. |
| **Evidence** | `src/emailservice/email_server.py` (synchronous gRPC handler), `protos/demo.proto` (`SendOrderConfirmation` is a synchronous RPC), absence of any messaging SDK imports in `requirements.in` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes NetworkPolicies are defined in `helm-chart/templates/emailservice.yaml` but are disabled by default (`networkPolicies.create: false` in `values.yaml`). When enabled, emailservice ingress is restricted to only checkoutservice on port 8080. Istio AuthorizationPolicies are similarly available but disabled by default (`authorizationPolicies.create: false`). When enabled, they restrict calls to the `SendOrderConfirmation` path from checkoutservice's service account only. Pod security contexts enforce non-root user, read-only filesystem, and dropped capabilities. Istio ServiceEntry in `istio-manifests/allow-egress-googleapis.yaml` controls egress to Google APIs. No VPC-level configuration is present in the emailservice scope. |
| **Gap** | Network policies and authorization policies exist in the Helm chart but are disabled by default. The default deployment has no network segmentation — any pod in the namespace can reach emailservice. No VPC or subnet configuration in IaC. |
| **Recommendation** | Enable NetworkPolicies and AuthorizationPolicies by default in the Helm values. When migrating to AWS EKS (preferred), define VPC with private subnets and security groups using Terraform. Enable EKS Pod Identity and Calico or Cilium for network policy enforcement. |
| **Evidence** | `helm-chart/values.yaml` (networkPolicies.create: false, authorizationPolicies.create: false), `helm-chart/templates/emailservice.yaml` (NetworkPolicy and AuthorizationPolicy definitions), `kubernetes-manifests/emailservice.yaml` (securityContext), `istio-manifests/allow-egress-googleapis.yaml` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | An Istio Gateway is defined in `istio-manifests/frontend-gateway.yaml` as the ingress entry point for the frontend service, routing HTTP traffic via a VirtualService. Internal services communicate via Kubernetes ClusterIP Services (`kubernetes-manifests/emailservice.yaml` defines a ClusterIP Service on port 5000→8080). Istio VirtualServices (`istio-manifests/frontend.yaml`) provide additional routing. However, there is no dedicated API Gateway with throttling, rate limiting, or request validation for internal services. |
| **Gap** | Frontend has an Istio ingress gateway, but internal gRPC services lack throttling, rate limiting, or request validation at the gateway level. No API Gateway resource for internal service traffic management. |
| **Recommendation** | When migrating to AWS EKS, deploy an AWS Application Load Balancer (ALB) or API Gateway for the frontend ingress. For internal service mesh, consider AWS App Mesh or Istio on EKS to maintain service-level traffic management. Define via Terraform (preferred). |
| **Evidence** | `istio-manifests/frontend-gateway.yaml` (Istio Gateway), `istio-manifests/frontend.yaml` (VirtualService), `kubernetes-manifests/emailservice.yaml` (ClusterIP Service) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot (defined in `terraform/main.tf`) provides automatic node-level scaling. Kubernetes resource requests and limits are set for all services (e.g., emailservice: cpu 100m-200m, memory 64Mi-128Mi in `kubernetes-manifests/emailservice.yaml`). However, no HorizontalPodAutoscaler (HPA) is defined for any service. Deployment replicas default to 1 (no `replicas` field specified in the Deployment spec). |
| **Gap** | Node-level auto-scaling exists via GKE Autopilot, but no pod-level auto-scaling (HPA) is configured. All services run with a single replica, meaning they cannot scale horizontally in response to traffic spikes. |
| **Recommendation** | Define HorizontalPodAutoscalers for all services via Kubernetes manifests or Helm chart templates. When migrating to EKS (preferred), configure KEDA or the Kubernetes Metrics Server with HPA. Define scaling targets based on CPU utilization, request latency, or gRPC queue depth. Manage scaling configurations via GitOps. |
| **Evidence** | `terraform/main.tf` (enable_autopilot = true), `kubernetes-manifests/emailservice.yaml` (resources section, no replicas field), `helm-chart/templates/emailservice.yaml` (no HPA template) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration was found for any data store. The default in-cluster Redis has no backup mechanism. The optional Memorystore Redis in `terraform/memorystore.tf` does not configure any backup parameters (no `persistence_config` or snapshot settings). No AWS Backup plans, no `backup_retention_period` settings, no point-in-time recovery configuration exists anywhere in the repository. |
| **Gap** | No backup or recovery configuration for any data store. Redis cart data is ephemeral with no recovery capability. No documented or tested restore procedures. |
| **Recommendation** | When migrating to AWS managed databases (ElastiCache/MemoryDB via Terraform, preferred), enable automatic backups with defined retention periods. Configure AWS Backup for centralized backup management. For critical data stores, enable point-in-time recovery. Document and test restore procedures. |
| **Evidence** | `terraform/memorystore.tf` (no backup config), `helm-chart/values.yaml` (cartDatabase section — no backup settings), absence of any backup-related resources in IaC |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot is configured as regional (`var.region = "us-central1"` in `terraform/variables.tf`), which automatically spans multiple zones. However, no explicit multi-AZ configuration exists for individual services. All Kubernetes Deployments run with a default of 1 replica (no `replicas` field in `kubernetes-manifests/emailservice.yaml`). The optional Memorystore Redis in `terraform/memorystore.tf` does not configure `replica_count` or cross-zone replication. |
| **Gap** | While the GKE cluster is regional (multi-zone), individual services have only 1 replica each — a single pod failure takes down the service. No pod disruption budgets, no explicit multi-AZ replica distribution. |
| **Recommendation** | Set minimum replicas to 2+ for all production services. Define PodDisruptionBudgets to ensure availability during node maintenance. When migrating to EKS (preferred), configure pod topology spread constraints across availability zones. Use Terraform to define multi-AZ EKS node groups. |
| **Evidence** | `terraform/variables.tf` (region = us-central1), `terraform/main.tf` (regional GKE Autopilot), `kubernetes-manifests/emailservice.yaml` (no replicas field — defaults to 1), `terraform/memorystore.tf` (no replica_count) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Terraform covers the GKE cluster and optional Memorystore (`terraform/main.tf`, `terraform/memorystore.tf`). Kubernetes manifests in `kubernetes-manifests/` define all 11 service Deployments, Services, and ServiceAccounts. Helm chart (`helm-chart/`) provides parameterized deployment with support for network policies, sidecars, and authorization policies. Kustomize (`kustomize/`) provides composable overlays for variations (memorystore, network-policies, service-mesh-istio, etc.). Skaffold (`skaffold.yaml`) manages the build-deploy pipeline. CI workflows validate Terraform (`terraform-validate-ci.yaml`), Helm charts (`helm-chart-ci.yaml`), and Kustomize builds (`kustomize-build-ci.yaml`). |
| **Gap** | Some infrastructure operations use `null_resource` with `local-exec` provisioners in Terraform (`main.tf` and `memorystore.tf`), which reduces reproducibility. Istio manifests are separate from the main Kustomize/Helm pipeline. No AWS IaC present (GCP-only). |
| **Recommendation** | Migrate IaC to AWS Terraform modules (preferred). Replace `null_resource` provisioners with native Terraform resources or Kubernetes provider resources. Consolidate Istio/service mesh configuration into the Helm chart. Adopt GitOps (preferred — ArgoCD or Flux) for declarative, auditable deployment. |
| **Evidence** | `terraform/main.tf`, `terraform/memorystore.tf`, `kubernetes-manifests/emailservice.yaml`, `helm-chart/Chart.yaml`, `helm-chart/values.yaml`, `kustomize/kustomization.yaml`, `skaffold.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions workflows provide CI/CD automation: `ci-pr.yaml` runs Go and C# unit tests, builds all container images, deploys to a GKE PR cluster via Skaffold, waits for pod readiness, and executes smoke tests via the loadgenerator (checking for zero errors). `ci-main.yaml` runs the same pipeline on main/release branches. Additional workflows: `helm-chart-ci.yaml` validates Helm chart with multiple scenarios, `kustomize-build-ci.yaml` validates Kustomize builds, `terraform-validate-ci.yaml` runs `terraform validate`. Google Cloud Build (`cloudbuild.yaml`) provides an alternative deployment path. Renovate (`renovate.json5`) automates dependency updates. |
| **Gap** | No Python-specific tests for the emailservice (only Go and C# tests run). No automated rollback mechanism on deployment failure. No canary or blue/green deployment strategy. The pipeline deploys directly without traffic shifting. |
| **Recommendation** | Add Python unit tests for the emailservice. Implement automated rollback on smoke test failure. Adopt a GitOps deployment model (preferred — ArgoCD or Flux on EKS) with progressive delivery (Argo Rollouts for canary deployments). Define pipeline configuration via Terraform or committed YAML. |
| **Evidence** | `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/kustomize-build-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `cloudbuild.yaml`, `skaffold.yaml`, `.github/renovate.json5` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The emailservice is written in Python, a language with a mature cloud-native ecosystem. Dependencies in `requirements.in` demonstrate strong ecosystem support: `grpcio` for gRPC, `opentelemetry-*` for distributed tracing, `jinja2` for templating, `python-json-logger` for structured logging. The broader microservices-demo includes Go, C#, Java, Node.js, and Python — all modern languages with excellent cloud-native tooling. Python specifically has rich support for containers, serverless, AI/ML, and observability. |
| **Gap** | No gap. Python is a top-tier cloud-native language with extensive framework support. |
| **Recommendation** | No action needed. Python is well-suited for this service. Consider adopting Python type hints and async/await patterns for future enhancements. |
| **Evidence** | `src/emailservice/email_server.py` (Python source), `src/emailservice/requirements.in` (Python ecosystem dependencies), `src/` directory (Go, C#, Java, Node.js, Python services) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This is a well-decomposed microservices architecture. 11 independently deployable services are defined, each with its own source directory under `src/`, its own Dockerfile, Kubernetes Deployment, and Service. The proto file (`protos/demo.proto`) defines clear service boundaries: `EmailService`, `CartService`, `CheckoutService`, `CurrencyService`, `PaymentService`, `ShippingService`, `RecommendationService`, `ProductCatalogService`, `AdService`. Each service has a focused single responsibility — emailservice handles only order confirmation emails. No circular dependencies or shared databases between services (only Redis is used, exclusively by cartservice). `skaffold.yaml` lists all 11 services as independent build artifacts. |
| **Gap** | No gap. The architecture is already decomposed into well-defined microservices with clear boundaries and single responsibilities. |
| **Recommendation** | No decomposition needed. Focus on strengthening inter-service communication patterns (async messaging) and operational maturity (observability, deployment strategy). |
| **Evidence** | `protos/demo.proto` (service definitions), `skaffold.yaml` (11 independent build artifacts), `src/` directory (11 service directories), `kubernetes-manifests/` (per-service manifests), `README.md` (architecture description) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC. The proto file (`protos/demo.proto`) defines all service methods as standard unary RPCs (request-response). The checkout service calls `EmailService.SendOrderConfirmation` synchronously. The emailservice's `email_server.py` handles requests synchronously — `DummyEmailService.SendOrderConfirmation` logs the request and returns `demo_pb2.Empty()` directly. No message queues, event buses, pub/sub topics, or async communication patterns were found anywhere in the codebase or infrastructure. No SQS, SNS, EventBridge, Kafka, or RabbitMQ SDK imports exist in any service's dependency manifests. |
| **Gap** | 100% synchronous communication. Email delivery (inherently asynchronous) blocks the checkout flow. Cascading failure risk — if emailservice is slow or down, the checkout service call blocks. |
| **Recommendation** | Introduce Amazon SQS (or SNS+SQS) to decouple the checkout→email flow. The checkout service should publish an order event to an SQS queue, and the emailservice should consume messages asynchronously. Extend the pattern to other non-critical downstream calls (shipping notifications, ad tracking). Define messaging infrastructure via Terraform (preferred). |
| **Evidence** | `protos/demo.proto` (all unary RPCs), `src/emailservice/email_server.py` (synchronous handler), `src/emailservice/requirements.in` (no messaging SDK imports) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The emailservice handles requests synchronously. `DummyEmailService.SendOrderConfirmation` in `email_server.py` logs the request and returns immediately. The real `EmailService.SendOrderConfirmation` would render a Jinja2 template and send an email synchronously via a Google Cloud API call. While email rendering is fast, actual email delivery via external APIs can have variable latency. No background job processing framework (Celery, Bull, RQ) is used. No status polling APIs or callback patterns exist. The gRPC server uses a ThreadPoolExecutor with `max_workers=10`, providing basic concurrency but no async job management. |
| **Gap** | No async job processing for operations that could have variable latency (email delivery via external API). All operations are synchronous within the gRPC request lifecycle. The dummy mode masks the latency issue, but production email sending would block. |
| **Recommendation** | When implementing real email delivery, use an async pattern: accept the gRPC request, enqueue the email job to SQS (preferred over synchronous API calls), and return a success immediately. A separate worker process (or the same service polling SQS) handles the actual email send with retries. |
| **Evidence** | `src/emailservice/email_server.py` (synchronous handlers, ThreadPoolExecutor max_workers=10), `src/emailservice/requirements.in` (no background job framework) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The protobuf package is `hipstershop` with no version suffix (`protos/demo.proto`: `package hipstershop`). Service names (`EmailService`, `CartService`, etc.) have no version indicators. No `/v1/` or `/v2/` URL patterns exist (services use gRPC, not REST). No `Accept-Version` headers or versioning annotations. No API changelog files. While protobuf provides backward-compatible field additions (new fields are additive), there is no mechanism for breaking changes, no versioned service names (`EmailServiceV2`), and no versioned packages (`hipstershop.v1`). |
| **Gap** | No versioning strategy for API evolution. Breaking changes to proto definitions would require coordinated deployment of all consuming services simultaneously. |
| **Recommendation** | Adopt protobuf package versioning (e.g., `hipstershop.v1`, `hipstershop.v2`). Define API evolution guidelines: additive changes within a version, breaking changes require a new version. Document API contracts and maintain a changelog. Consider generating OpenAPI specs from proto definitions for broader tooling support. |
| **Evidence** | `protos/demo.proto` (package hipstershop — no version), service definitions with no version indicators |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes DNS-based service discovery is the primary mechanism. Each service has a ClusterIP Service resource (e.g., `kubernetes-manifests/emailservice.yaml` defines `emailservice` Service on port 5000→8080). Services reference each other by Kubernetes DNS names. Istio VirtualServices (`istio-manifests/frontend.yaml`) provide additional routing capabilities when the service mesh is enabled. The Helm chart supports Istio sidecars for advanced traffic management. However, `src/emailservice/email_client.py` hard-codes `[::]:8080` for local testing. Some services use environment variables for endpoint configuration. |
| **Gap** | Service discovery works well within the Kubernetes cluster, but the test client (`email_client.py`) hard-codes the endpoint. No API catalog or service registry beyond Kubernetes DNS. No service mesh enabled by default. |
| **Recommendation** | When migrating to EKS (preferred), maintain Kubernetes DNS-based service discovery. Enable Istio or AWS App Mesh by default for advanced traffic management, circuit breaking, and observability. Consider AWS Cloud Map for cross-cluster service discovery if the architecture spans multiple EKS clusters. Adopt GitOps (preferred) for service mesh configuration. |
| **Evidence** | `kubernetes-manifests/emailservice.yaml` (ClusterIP Service), `istio-manifests/frontend.yaml` (VirtualService), `src/emailservice/email_client.py` (hard-coded endpoint), `helm-chart/values.yaml` (sidecars.create: false) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The emailservice does not store or manage unstructured data. It renders HTML email templates from `src/emailservice/templates/confirmation.html` using Jinja2 and sends them via gRPC response. Templates are bundled in the container image, not stored in object storage. No S3 buckets, EFS volumes, or object storage references exist anywhere in the repository. No document parsing libraries (Textract, Tika) are used. The broader platform also shows no document or unstructured data management. |
| **Gap** | No object storage for unstructured data. Email templates are embedded in the container image rather than stored in managed storage. No capability for document parsing, search, or AI-accessible content. |
| **Recommendation** | For the emailservice scope, this is a low-priority gap — templates are simple HTML files. If the platform evolves to handle document attachments, receipts, or invoices, introduce Amazon S3 for storage with lifecycle policies. Define S3 buckets via Terraform (preferred). |
| **Evidence** | `src/emailservice/templates/confirmation.html` (embedded Jinja2 template), absence of any S3/storage resources in IaC |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The emailservice itself is stateless with no database access. The broader platform has Redis as the only data store, accessed directly by the cartservice. There is no centralized data access layer, repository pattern, or shared data service. Each service that needs data accesses it directly — cartservice accesses Redis, productcatalogservice reads from a local JSON file. No ORM or data access abstraction is used across services. |
| **Gap** | No unified data access layer. Each service accesses its data store directly without a shared abstraction. While acceptable in a microservices architecture (each service owns its data), there is no data access pattern consistency across services. |
| **Recommendation** | In a microservices architecture, each service should own its data, which this platform largely achieves. Improve by standardizing data access patterns within each service (e.g., repository pattern). If introducing DynamoDB (preferred) for new data needs, use the AWS SDK with a consistent access layer pattern across Python services. |
| **Evidence** | `src/emailservice/email_server.py` (no database imports), `helm-chart/values.yaml` (cartDatabase.connectionString: redis-cart:6379) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Redis version is explicitly pinned in the optional Memorystore configuration: `redis_version = "REDIS_7_0"` in `terraform/memorystore.tf`. Redis 7.0 is a current release and not at or approaching EOL. However, the default in-cluster Redis uses the standard `redis` Docker image defined in the Helm chart without an explicit version tag (`cartDatabase.inClusterRedis.publicRepository: true`), meaning it uses the latest image — which is unpredictable and not version-controlled. |
| **Gap** | In-cluster Redis image tag is not explicitly pinned in the Helm values. While the managed Memorystore version is pinned, the default deployment path (in-cluster) uses an unpinned image. |
| **Recommendation** | Pin the in-cluster Redis image to a specific version tag in the Helm chart. When migrating to AWS ElastiCache (via Terraform, preferred), explicitly pin the Redis engine version and establish a lifecycle policy for version upgrades. |
| **Evidence** | `terraform/memorystore.tf` (redis_version = REDIS_7_0), `helm-chart/values.yaml` (cartDatabase — no explicit Redis image tag) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No SQL databases are used anywhere in the platform. Redis is the only data store, used as a key-value cache by the cartservice. No stored procedures, triggers, proprietary SQL constructs, or database functions exist. All business logic resides in the application layer: Python (emailservice, recommendationservice), Go (frontend, checkoutservice, shippingservice, productcatalogservice), C# (cartservice), Java (adservice), Node.js (currencyservice, paymentservice). No `.sql` migration files, no ORM configurations, no raw SQL execution patterns found. |
| **Gap** | No gap. All business logic is in the application layer with no database coupling via stored procedures or proprietary SQL. |
| **Recommendation** | No action needed. This is best practice — business logic in application code, not in the database engine. Maintain this pattern when introducing new data stores. |
| **Evidence** | `protos/demo.proto` (all business operations as gRPC services), `src/emailservice/email_server.py` (business logic in Python), absence of any `.sql` files in repository |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No audit logging configuration was found in the IaC or configuration files. The Terraform configuration (`terraform/main.tf`) provisions a GKE cluster but does not configure any audit logging resources. No CloudTrail equivalent is defined. No log file validation or immutable storage (S3 Object Lock) configuration exists. The `main.tf` enables `monitoring.googleapis.com` and `cloudtrace.googleapis.com` APIs but not explicit audit logging. GKE may have default audit logging, but it is not explicitly configured or governed in the IaC. |
| **Gap** | No audit logging configuration. No immutable log storage. No log retention policies. Cannot trace security events or perform forensic analysis. |
| **Recommendation** | When migrating to AWS, enable AWS CloudTrail with log file validation and S3 Object Lock for immutable storage. Configure CloudWatch Logs with retention policies for application logs. Define audit logging infrastructure via Terraform (preferred). Enable Kubernetes audit logging on EKS with audit policy configuration. |
| **Evidence** | `terraform/main.tf` (no audit logging resources), absence of CloudTrail or equivalent configuration in any IaC file |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration was found. The Terraform configuration does not define any KMS keys or encryption settings. The optional Memorystore Redis in `terraform/memorystore.tf` does not configure `transit_encryption_mode` or customer-managed encryption keys. No `kms_key_id` references on any resources. While GKE and Memorystore may use default encryption, no customer-managed keys are defined and encryption governance is not explicit in IaC. |
| **Gap** | No explicit encryption-at-rest configuration. No customer-managed keys. No encryption governance for data stores or container images. |
| **Recommendation** | When migrating to AWS, create AWS KMS customer-managed keys via Terraform (preferred). Apply KMS encryption to all data stores (ElastiCache, DynamoDB, S3). Enable EKS envelope encryption for Kubernetes secrets. Define key rotation policies. |
| **Evidence** | `terraform/memorystore.tf` (no encryption config), absence of any KMS resources in IaC |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The emailservice gRPC server (`email_server.py`) does not implement any application-level authentication. The server uses `server.add_insecure_port('[::]:'+port)` — an insecure gRPC channel with no TLS or auth. However, the Helm chart provides infrastructure-level auth via Istio AuthorizationPolicy (`helm-chart/templates/emailservice.yaml`), which when enabled restricts `SendOrderConfirmation` calls to only the checkoutservice's service account. The AuthorizationPolicy is disabled by default (`authorizationPolicies.create: false` in `values.yaml`). Istio mTLS would provide transport-level authentication when the service mesh is enabled. |
| **Gap** | No application-level auth on gRPC endpoints. Infrastructure-level auth (Istio AuthorizationPolicy) exists but is disabled by default. gRPC channels are insecure (no TLS). |
| **Recommendation** | Enable Istio AuthorizationPolicies by default. When migrating to EKS (preferred), enable mTLS via Istio or AWS App Mesh for service-to-service authentication. Consider adding gRPC interceptor-based auth for defense-in-depth. Use SPIFFE/SPIRE for workload identity if not using a service mesh. |
| **Evidence** | `src/emailservice/email_server.py` (add_insecure_port), `helm-chart/templates/emailservice.yaml` (AuthorizationPolicy — disabled by default), `helm-chart/values.yaml` (authorizationPolicies.create: false) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider (Cognito, Okta, Ping) integration exists. Kubernetes ServiceAccounts are defined for each service (`kubernetes-manifests/emailservice.yaml`). The Helm chart supports annotations on ServiceAccounts for GKE Workload Identity (`serviceAccounts.annotations` in `values.yaml`), but this is for cloud API access, not application-level identity. The frontend does not require user login — it generates session IDs automatically (noted in `README.md`). No OIDC, SAML, or external IdP configuration found. |
| **Gap** | No centralized IdP integration. No user authentication. The application is designed as a demo without real user identity management. |
| **Recommendation** | When production-hardening this application, integrate Amazon Cognito for user authentication and authorization. Use OIDC with EKS (preferred) for workload identity. Implement Cognito user pools for the frontend and machine-to-machine OAuth2 for service-to-service communication. Define Cognito resources via Terraform (preferred). |
| **Evidence** | `kubernetes-manifests/emailservice.yaml` (ServiceAccount), `helm-chart/values.yaml` (serviceAccounts.annotations), `README.md` (no signup/login required) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated secrets management system is configured. The emailservice uses environment variables for configuration (`PORT`, `DISABLE_PROFILER`, `ENABLE_TRACING`, `COLLECTOR_SERVICE_ADDR`) defined in `kubernetes-manifests/emailservice.yaml`. No hardcoded passwords, API keys, or credentials were found in the source code. The `email_server.py` handles `DefaultCredentialsError` for GCP credentials, suggesting runtime credential injection via workload identity. The Redis connection string (`redis-cart:6379`) does not use authentication. No AWS Secrets Manager, HashiCorp Vault, or Kubernetes External Secrets references found. |
| **Gap** | No dedicated secrets management system. While no secrets are currently hardcoded, there is no infrastructure for secret rotation, audit, or centralized management. The Redis connection uses no authentication. |
| **Recommendation** | Integrate AWS Secrets Manager for all sensitive configuration via Terraform (preferred). Use the Kubernetes External Secrets Operator to sync secrets from Secrets Manager to Kubernetes. Enable automatic rotation for database credentials. When migrating Redis to ElastiCache, configure AUTH tokens stored in Secrets Manager. |
| **Evidence** | `kubernetes-manifests/emailservice.yaml` (env vars for config), `src/emailservice/email_server.py` (DefaultCredentialsError handling), `helm-chart/values.yaml` (cartDatabase.connectionString: redis-cart:6379 — no auth), absence of any secrets management resources |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong container hardening practices are in place. The Dockerfile (`src/emailservice/Dockerfile`) uses a multi-stage build with `python:3.14.3-alpine` — a minimal Alpine-based image with reduced attack surface. The image digest is pinned (`@sha256:faee120f...`). Kubernetes security contexts in `kubernetes-manifests/emailservice.yaml` enforce: `runAsNonRoot: true`, `runAsUser: 1000`, `runAsGroup: 1000`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `privileged: false`, and `capabilities.drop: [ALL]`. The Helm chart supports seccomp profiles (`seccompProfile.enable`). Renovate (`renovate.json5`) automates dependency updates including Docker image updates. However, no vulnerability scanning (AWS Inspector, Snyk, Trivy) is configured. |
| **Gap** | No vulnerability scanning for container images or runtime. No SSM Patch Manager equivalent. Hardening is excellent, but there's no continuous vulnerability analysis. |
| **Recommendation** | Add container image scanning (Amazon ECR image scanning or Trivy) to the CI/CD pipeline. When migrating to EKS (preferred), enable Amazon Inspector for runtime vulnerability scanning. Continue using Alpine-based images and maintain the strong security context configuration. |
| **Evidence** | `src/emailservice/Dockerfile` (python:3.14.3-alpine with digest pinning, multi-stage build), `kubernetes-manifests/emailservice.yaml` (securityContext), `helm-chart/values.yaml` (seccompProfile support), `.github/renovate.json5` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Renovate (`renovate.json5`) is configured for automated dependency updates, providing some supply chain security. CI pipelines (`.github/workflows/ci-pr.yaml`, `ci-main.yaml`) run code tests and smoke tests but contain no SAST, DAST, or dependency vulnerability scanning steps. No SonarQube, Semgrep, CodeGuru, `pip-audit`, `npm audit`, Snyk, or Trivy references in any CI workflow. No container image scanning is configured. The Helm chart CI (`helm-chart-ci.yaml`) validates templates but does not scan for security misconfigurations. |
| **Gap** | No SAST, DAST, or dependency vulnerability scanning in CI/CD. Renovate provides dependency updates but does not block builds on known vulnerabilities. No container image scanning. |
| **Recommendation** | Add `pip-audit` or Snyk to the CI pipeline for Python dependency vulnerability scanning. Add Trivy or ECR image scanning for container images. Add Semgrep or SonarQube for SAST. Configure security gates to block merges on critical findings. Define pipeline security stages in the GitHub Actions workflows. |
| **Evidence** | `.github/renovate.json5` (dependency updates), `.github/workflows/ci-pr.yaml` (no security scanning steps), `.github/workflows/ci-main.yaml` (no security scanning steps), `.github/workflows/helm-chart-ci.yaml` (no security scanning) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry is comprehensively instrumented in the emailservice. Dependencies in `requirements.in` include: `opentelemetry-distro`, `opentelemetry-instrumentation-grpc`, `opentelemetry-exporter-otlp-proto-grpc`, and `opentelemetry-sdk`. In `email_server.py`, the `__main__` block configures a `TracerProvider` with `BatchSpanProcessor` and `OTLPSpanExporter` targeting the collector endpoint (configured via `COLLECTOR_SERVICE_ADDR` env var, defaulting to `localhost:4317`). `GrpcInstrumentorServer` auto-instruments all gRPC server calls. The Helm chart (`values.yaml`) supports deploying an OpenTelemetry Collector (`opentelemetryCollector.create`). Google Cloud Trace is also available via `google-cloud-trace` dependency. However, tracing is conditionally enabled (`ENABLE_TRACING=1`), and the OTel collector is disabled by default. |
| **Gap** | Tracing is conditionally enabled and the collector is disabled by default. Trace propagation across all service boundaries is not verified. No confirmation that all 11 services propagate trace context consistently. |
| **Recommendation** | Enable tracing by default in the Helm values. When migrating to EKS (preferred), route traces to AWS X-Ray or an AWS-managed OpenTelemetry Collector. Enable the ADOT (AWS Distro for OpenTelemetry) collector as a DaemonSet on EKS. Verify trace propagation across all gRPC service boundaries. |
| **Evidence** | `src/emailservice/requirements.in` (opentelemetry-* dependencies), `src/emailservice/email_server.py` (TracerProvider, BatchSpanProcessor, OTLPSpanExporter, GrpcInstrumentorServer), `helm-chart/values.yaml` (opentelemetryCollector.create: false) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions were found anywhere in the repository. No error budget tracking, no SLO YAML files, no CloudWatch or GCP Monitoring SLO configurations. No p99/p95 latency targets defined. No availability targets documented. |
| **Gap** | No SLOs defined for any service. Cannot measure whether the emailservice (or any service) meets user expectations for latency, availability, or error rates. No data-driven reliability prioritization. |
| **Recommendation** | Define SLOs for the emailservice: email delivery success rate > 99.9%, p99 latency < 500ms. Implement SLO monitoring using CloudWatch (or Prometheus) with error budget tracking. Define SLOs as code in the repository, managed via GitOps (preferred). |
| **Evidence** | Absence of any SLO definitions, error budget configurations, or latency target files in the repository |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The emailservice uses JSON structured logging via `logger.py` (using `pythonjsonlogger.JsonFormatter`) to log request events, but does not publish metrics to any metrics backend (CloudWatch, Prometheus, StatsD). Only infrastructure-level resource requests/limits are defined in Kubernetes manifests. No `put_metric_data`, no Prometheus client library, no StatsD client in dependencies. |
| **Gap** | No business metrics. Cannot track email delivery rates, template rendering times, or confirmation email success/failure ratios. Only infrastructure metrics available. |
| **Recommendation** | Add Prometheus client library to publish business metrics: `emails_sent_total`, `email_rendering_duration_seconds`, `email_delivery_errors_total`. When migrating to EKS (preferred), use Amazon Managed Prometheus for metrics collection and Amazon Managed Grafana for visualization. |
| **Evidence** | `src/emailservice/logger.py` (JSON logging only), `src/emailservice/requirements.in` (no metrics client library), `kubernetes-manifests/emailservice.yaml` (resource limits only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found anywhere in the repository. No CloudWatch alarms, no Prometheus alerting rules, no GCP Monitoring alert policies, no PagerDuty/OpsGenie integration. No composite alarms or error rate monitoring. |
| **Gap** | No alerting of any kind. Service degradation, increased error rates, or latency spikes would go unnoticed without manual monitoring. |
| **Recommendation** | Implement CloudWatch alarms on key metrics: error rate, p99 latency, pod restart count. Enable anomaly detection on error rates for critical paths. Integrate with a paging system (PagerDuty, OpsGenie). Define alerts as code via Terraform (preferred) or Kubernetes Prometheus operator. |
| **Evidence** | Absence of any alerting configuration, alarm definitions, or monitoring alert resources in IaC or configuration files |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI/CD pipeline deploys via `skaffold run` which applies Kubernetes manifests via `kubectl apply` (`skaffold.yaml` uses `kustomize` paths). Kubernetes default rolling update strategy applies (no explicit `strategy` field in the Deployment spec in `kubernetes-manifests/emailservice.yaml`). The CI pipeline (`ci-pr.yaml`) includes smoke tests after deployment (loadgenerator checking for zero errors), which provides a basic validation gate. However, there is no canary, blue/green, or traffic shifting deployment strategy. No Argo Rollouts, CodeDeploy, or weighted target groups. No automated rollback on failure. |
| **Gap** | Basic rolling update only. No canary or blue/green deployment. No automated rollback. Failed deployments require manual intervention. |
| **Recommendation** | Adopt Argo Rollouts on EKS (preferred) for canary deployments with automated promotion/rollback based on metrics analysis. Define rollout strategy as code in the Kubernetes manifests. Integrate with the GitOps workflow (preferred — ArgoCD for progressive delivery). |
| **Evidence** | `skaffold.yaml` (kubectl apply via kustomize), `kubernetes-manifests/emailservice.yaml` (no explicit deployment strategy), `.github/workflows/ci-pr.yaml` (smoke tests after deploy but no rollback) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CI pipeline (`ci-pr.yaml`, `ci-main.yaml`) includes end-to-end integration testing: after deploying all services to a real GKE cluster, the loadgenerator sends realistic user traffic and the pipeline checks for zero errors across all endpoints (aggregated error count must be 0). This constitutes a comprehensive smoke/integration test suite that validates the entire microservices system works end-to-end. Additionally, Go unit tests run for shippingservice, productcatalogservice, and frontend/validator; C# unit tests run for cartservice. However, no Python-specific unit or integration tests exist for the emailservice. |
| **Gap** | No Python-specific tests for the emailservice. The emailservice is validated only through the end-to-end smoke test (indirectly, via the checkout flow). No unit tests for template rendering, gRPC handler logic, or error handling. |
| **Recommendation** | Add Python unit tests for the emailservice: test template rendering with various order payloads, test gRPC handler error paths, test the health check endpoint. Add these tests to the CI pipeline. Use pytest with grpcio-testing for gRPC handler tests. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (deployment-tests with smoke tests, Go/C# unit tests), `.github/workflows/ci-main.yaml` (same pipeline on main), absence of any Python test files in `src/emailservice/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation, runbooks, or self-healing patterns found in the repository. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files (markdown, YAML, JSON) in any directory. No documented incident response procedures. Kubernetes liveness/readiness probes in `kubernetes-manifests/emailservice.yaml` provide basic self-healing (pod restart on health check failure), but this is standard K8s behavior, not an incident response strategy. |
| **Gap** | No incident response automation. No documented runbooks. Incident response would be entirely ad hoc. |
| **Recommendation** | Create runbooks for common email service failures (gRPC endpoint unreachable, template rendering errors, high latency). Implement AWS Systems Manager Automation documents for common remediation actions. Define runbooks as code in the repository, managed via GitOps (preferred). |
| **Evidence** | `kubernetes-manifests/emailservice.yaml` (liveness/readiness probes — basic self-healing only), absence of any runbook files or incident response configurations |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The `CODEOWNERS` file (`.github/CODEOWNERS`) assigns all repository ownership to `@GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver` — a single global owner for the entire repo. No per-service observability ownership is defined. No team-attributed dashboards, alarms, or SLO definitions exist. No service-level CODEOWNERS for observability configs. |
| **Gap** | No per-service observability ownership. No named alarm owners. No team-attributed dashboards or SLOs. Global ownership does not provide accountability for individual service reliability. |
| **Recommendation** | Define per-service CODEOWNERS for observability configurations. Create per-service dashboards with named owners. When defining SLOs, attribute them to specific teams. Manage ownership definitions in the repository via GitOps (preferred). |
| **Evidence** | `.github/CODEOWNERS` (global ownership only), absence of per-service dashboards, alarm ownership, or SLO team attribution |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes labels are consistently applied across all resources. In `kubernetes-manifests/emailservice.yaml`, the Deployment, Service, and ServiceAccount all have `app: emailservice` labels. The Helm chart (`helm-chart/templates/emailservice.yaml`) generates consistent labels via templates. However, these are Kubernetes labels for service discovery and routing, not cloud resource tags for cost allocation or ownership. No `default_tags` in the Terraform provider. No `required-tags` config rules. No cost allocation tags or ownership tags on the GKE cluster or Memorystore resources. |
| **Gap** | Kubernetes labels are consistent but no cloud resource tagging for cost allocation, environment identification, or ownership. No tag enforcement policies. |
| **Recommendation** | When migrating to AWS with Terraform (preferred), define `default_tags` on the AWS provider for cost allocation (`team`, `service`, `environment`, `cost-center`). Add required-tags AWS Config rules for enforcement. Extend Kubernetes labels to include ownership and cost-center annotations. |
| **Evidence** | `kubernetes-manifests/emailservice.yaml` (app: emailservice labels), `helm-chart/templates/emailservice.yaml` (templated labels), `terraform/main.tf` (no default_tags), `terraform/providers.tf` (no default_tags on google provider) |

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
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q9, INF-Q10 | GKE Autopilot cluster definition with enable_autopilot = true |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, INF-Q9, DATA-Q3 | Optional managed Redis (Memorystore) with redis_version = REDIS_7_0 |
| `terraform/variables.tf` | INF-Q9 | Region variable (us-central1) for regional cluster |
| `terraform/terraform.tfvars` | INF-Q2 | memorystore = false (disabled by default) |
| `terraform/providers.tf` | INF-Q10 | Google provider with version pinning |
| `src/emailservice/email_server.py` | INF-Q3, INF-Q4, APP-Q3, APP-Q4, OPS-Q1, SEC-Q3 | Main entry point with gRPC server, OTel tracing, synchronous request handling |
| `src/emailservice/email_client.py` | APP-Q6 | Test client with hard-coded endpoint [::]:8080 |
| `src/emailservice/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage build with python:3.14.3-alpine base image |
| `src/emailservice/requirements.in` | APP-Q1, OPS-Q1, INF-Q4 | Direct dependencies including grpcio, opentelemetry-*, jinja2 |
| `src/emailservice/requirements.txt` | APP-Q1, SEC-Q7 | Full dependency tree compiled by uv |
| `src/emailservice/logger.py` | OPS-Q1, OPS-Q3 | JSON structured logging with pythonjsonlogger |
| `src/emailservice/templates/confirmation.html` | DATA-Q1 | Jinja2 email template for order confirmation |
| `kubernetes-manifests/emailservice.yaml` | INF-Q1, INF-Q5, INF-Q6, INF-Q7, INF-Q9, OPS-Q9 | K8s Deployment, Service, ServiceAccount with security contexts and resource limits |
| `helm-chart/Chart.yaml` | INF-Q10 | Helm chart metadata (onlineboutique v0.10.5) |
| `helm-chart/values.yaml` | INF-Q2, INF-Q5, OPS-Q1, SEC-Q3 | Default values with networkPolicies, authorizationPolicies, otelCollector disabled |
| `helm-chart/templates/emailservice.yaml` | INF-Q5, INF-Q7, SEC-Q3 | Templated Deployment with NetworkPolicy, Sidecar, AuthorizationPolicy |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | PR CI pipeline with code tests, GKE deploy, smoke tests |
| `.github/workflows/ci-main.yaml` | INF-Q11, OPS-Q5, OPS-Q6 | Main branch CI pipeline with code tests, GKE deploy, smoke tests |
| `.github/workflows/helm-chart-ci.yaml` | INF-Q10, INF-Q11 | Helm lint and template validation CI |
| `.github/workflows/kustomize-build-ci.yaml` | INF-Q10, INF-Q11 | Kustomize build validation CI |
| `.github/workflows/terraform-validate-ci.yaml` | INF-Q10, INF-Q11 | Terraform init and validate CI |
| `.github/renovate.json5` | INF-Q11, SEC-Q7 | Automated dependency updates via Renovate |
| `.github/CODEOWNERS` | OPS-Q8 | Global repo ownership by GoogleCloudPlatform/devrel-flagship-app-maintainers |
| `cloudbuild.yaml` | INF-Q11 | Alternative Google Cloud Build deployment path |
| `skaffold.yaml` | INF-Q1, INF-Q10, INF-Q11, OPS-Q5 | Build and deploy pipeline for all 11 services |
| `istio-manifests/frontend-gateway.yaml` | INF-Q6 | Istio Gateway and VirtualService for frontend ingress |
| `istio-manifests/frontend.yaml` | INF-Q6 | Istio VirtualService for frontend routing |
| `istio-manifests/allow-egress-googleapis.yaml` | INF-Q5 | Istio ServiceEntry controlling egress to Google APIs |
| `kustomize/kustomization.yaml` | INF-Q10 | Base kustomization with component overlays |
| `protos/demo.proto` | APP-Q2, APP-Q3, APP-Q5, INF-Q4 | Protocol buffer service definitions for all 11 microservices |
| `README.md` | APP-Q2 | Architecture documentation with service descriptions and diagram |
