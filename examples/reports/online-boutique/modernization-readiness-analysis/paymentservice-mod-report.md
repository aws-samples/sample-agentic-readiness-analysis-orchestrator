# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | paymentservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | nodejs, grpc, payment |
| **Context** | Node.js gRPC service handling payment processing (simulated). |
| **Overall Score** | 1.92 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.18 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.25 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work |
| **Overall** | **1.92 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No audit logging (CloudTrail or equivalent) configured anywhere in IaC or application | Compliance risk; no forensic trail for security incidents affecting payment processing |
| 2 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption-at-rest configuration for any data store | Sensitive payment-adjacent data (cart, session) stored without encryption; compliance gap |
| 3 | SEC-Q5: Secrets Management | 1 | No secrets management system (Secrets Manager, Vault); environment variables only | When real payment credentials are introduced, hardcoded or env-var secrets create critical vulnerability |
| 4 | APP-Q3: Async vs Sync Communication | 1 | All inter-service communication is synchronous gRPC with no async patterns | Tight coupling between checkout and payment; cascading failure risk; no decoupling for resilience |
| 5 | OPS-Q2: SLO Definitions | 1 | No SLOs, error budgets, or service-level targets defined for payment processing | Cannot measure payment reliability or justify modernization investments with data |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3 ≥ 2). GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) with build, deploy, and smoke test stages, plus Cloud Build (`cloudbuild.yaml`) and Skaffold (`skaffold.yaml`).
- **What it enables:** An agent that triggers deployments, checks build status, manages PR environments, and monitors deployment health across the Skaffold/GKE pipeline.
- **Additional steps:** Expose CI/CD pipeline status via API (GitHub Actions API already available). Consider adding a GitOps workflow (e.g., ArgoCD on EKS per preferences) to provide a declarative deployment surface the agent can interact with.
- **Effort:** Low

### Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 3 ≥ 2). OpenTelemetry SDK with gRPC auto-instrumentation (`@opentelemetry/instrumentation-grpc`) and OTLP exporter configured in `index.js`. Pino structured JSON logging in `logger.js` and `charge.js`.
- **What it enables:** An agent that queries traces, correlates payment transaction logs, identifies slow or failed charge requests, and suggests root causes based on trace data.
- **Additional steps:** Enable tracing by default (currently requires `ENABLE_TRACING=1`). Deploy an OpenTelemetry Collector and configure trace storage (e.g., AWS X-Ray or Jaeger). Index Pino logs into a searchable store.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` (170 lines) describes the full architecture, all 11 microservices, deployment instructions, and inter-service communication patterns. Proto file `demo.proto` documents all gRPC service contracts. Helm chart `values.yaml` documents all configuration options.
- **What it enables:** A RAG-based agent using Amazon Bedrock (per preferences) that indexes repository documentation, proto definitions, and Helm values to answer developer questions about the payment service architecture, deployment, and configuration.
- **Additional steps:** Generate embeddings from README.md, demo.proto, and Helm values. Set up a vector store (e.g., OpenSearch Service with vector engine) and a Bedrock-powered retrieval chain.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — already a microservices architecture with independently deployable services |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 — already containerized on managed Kubernetes (GKE Autopilot); contextual guard: compute is already on managed container orchestration |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no commercial database engines detected; Redis is already open source |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 — in-cluster Redis is self-managed by default; DATA-Q3 = 2 — mixed version pinning |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1, but contextual guard prevents: no data processing, ETL, streaming, or analytics workloads detected |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3, INF-Q11 = 3 — both primary triggers at threshold; CI/CD and IaC coverage are adequate |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks, no vector DB, no RAG patterns, no agent eval frameworks detected |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
The application uses Redis as its sole database, deployed in two modes:
- **Default (in-cluster Redis):** A self-managed Redis instance (`redis-cart`) deployed as a Kubernetes Deployment within the GKE cluster (`helm-chart/values.yaml`: `cartDatabase.inClusterRedis.create: true`). This is the active configuration (`terraform.tfvars`: `memorystore = false`).
- **Optional (Google Memorystore):** A managed Redis instance (`google_redis_instance.redis-cart` in `terraform/memorystore.tf`) with `redis_version = "REDIS_7_0"`, conditionally enabled via the `memorystore` variable. Currently disabled.

The paymentservice itself is stateless — it does not access any database. However, the broader application relies on Redis for cart persistence.

**Engine Versions and EOL Status (DATA-Q3):**
- Memorystore: Explicitly pinned to `REDIS_7_0` (supported, not EOL).
- In-cluster Redis: No explicit version pin in Helm values or Kubernetes manifests. Uses public Docker Hub image with no tag specification, risking version drift.

**Data Access Patterns (DATA-Q2):**
- Cart service accesses Redis directly with no unified data access layer. Connection string is hardcoded in Helm values: `redis-cart:6379`.

**Recommended Migration Target:**
Migrate the in-cluster self-managed Redis to **Amazon ElastiCache for Redis** or **Amazon MemoryDB for Redis** on EKS (per preferences favoring EKS). This provides:
- Automatic failover with Multi-AZ replication
- Automated backups with point-in-time recovery
- Managed patching and version upgrades
- Encryption at rest and in transit

If the application evolves to require a primary database, consider **Amazon DynamoDB** (per preferences) for its serverless scaling and operational simplicity.

**Representative AWS Services:** ElastiCache, MemoryDB, DynamoDB, RDS, Aurora

**Migration Approach:**
1. Provision ElastiCache Redis cluster via Terraform (per preferences)
2. Update connection strings in Helm values / Kustomize components
3. Enable encryption in transit (TLS) — the Helm chart already supports TLS origination (`cartDatabase.externalRedisTlsOrigination`)
4. Validate cart persistence with integration smoke tests (existing CI pipeline supports this)
5. Decommission in-cluster Redis Deployment

**Links to AWS Guidance:**
- [AWS ElastiCache Migration Guide](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Migration.html)
- [AWS Database Migration Service](https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI or agent framework usage was detected during the discovery scan:
- No Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK imports in source code
- No vector database infrastructure (no OpenSearch vector engine, Pinecone, pgvector, Weaviate, or Qdrant)
- No RAG implementation patterns (no embedding generation, vector store queries, or retrieval chains)
- No agent evaluation frameworks (no Ragas, DeepEval, or custom eval harnesses)

**Application Domain and Potential AI Use Cases:**
The paymentservice handles simulated credit card payment processing. AI integration opportunities include:

1. **Fraud Detection Agent:** Use Amazon Bedrock to analyze transaction patterns and flag anomalous charges based on card type, amount, frequency, and geographic patterns. The structured `ChargeRequest` (amount, credit card info) provides clean input for anomaly classification.
2. **Payment Operations Assistant:** A Bedrock-powered agent that helps operations teams diagnose payment failures, analyze transaction logs (Pino structured logging already in place), and suggest remediation steps.
3. **Developer Documentation Agent:** RAG-based agent (see Quick Agent Wins) using the existing proto definitions and README to answer developer questions about the payment API.

**Quick Wins:** See the Quick Agent Wins section above — DevOps agent, observability agent, and RAG knowledge agent can be pursued immediately.

**Recommended AI Services (per preferences favoring Bedrock):**
- **Amazon Bedrock** — Foundation model access for fraud detection, operations assistance, and documentation Q&A
- **Amazon Bedrock AgentCore** — Agent runtime for building payment operations agents
- **Amazon OpenSearch Service** (vector engine) — Vector store for RAG-based knowledge retrieval
- **Amazon Q Developer** — AI-assisted development for the paymentservice codebase

**Foundation Requirements (before AI integration):**
- Enable OpenTelemetry tracing by default (currently optional) to provide data for observability agents
- Implement structured business metrics (OPS-Q3 gap) to feed fraud detection models
- Set up secrets management (SEC-Q5 gap) before storing API keys for AI services
- Deploy an OpenTelemetry Collector with trace export to a searchable store

**Links to AWS AI/ML Guidance:**
- [Amazon Bedrock Getting Started](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html)
- [Building AI Agents with Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application is fully containerized (multi-stage `Dockerfile` using `node:20.20.1-alpine` with SHA256 digest pinning) and deployed on GKE Autopilot (`terraform/main.tf`: `enable_autopilot = true`), which is a fully managed Kubernetes orchestration platform. Each of the 12 microservices has its own Dockerfile and Kubernetes Deployment (`kubernetes-manifests/paymentservice.yaml`). Skaffold (`skaffold.yaml`) orchestrates multi-platform builds (`linux/amd64`, `linux/arm64`). No raw EC2 or VM instances detected. The Helm chart (`helm-chart/templates/paymentservice.yaml`) provides production-grade templating with resource limits. |
| **Gap** | Infrastructure is GCP-native (GKE Autopilot) rather than AWS. For an AWS migration, the containerized workloads would need to target EKS. The containerization patterns are mature and portable — the gap is cloud provider, not compute model. |
| **Recommendation** | Migrate to Amazon EKS (per preferences) using the existing Helm charts and Kustomize overlays. The multi-platform Docker builds already support ARM64, enabling Graviton-based EKS node groups for cost optimization. Adopt a GitOps model (e.g., ArgoCD on EKS per preferences) to replace the Skaffold-based deployment. |
| **Evidence** | `src/paymentservice/Dockerfile`, `terraform/main.tf`, `kubernetes-manifests/paymentservice.yaml`, `helm-chart/templates/paymentservice.yaml`, `skaffold.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses Redis for cart persistence in two modes: (1) **In-cluster Redis** deployed as a Kubernetes pod (`helm-chart/values.yaml`: `cartDatabase.inClusterRedis.create: true`, `cartDatabase.connectionString: "redis-cart:6379"`), which is the active default; (2) **Google Memorystore Redis** (`terraform/memorystore.tf`: `google_redis_instance.redis-cart`) as an optional managed alternative, currently disabled (`terraform.tfvars`: `memorystore = false`). The paymentservice itself is stateless and uses no database. |
| **Gap** | The default deployment uses self-managed in-cluster Redis with no automated failover, no backups, and no encryption. The managed option (Memorystore) exists but is disabled. This represents a primarily self-managed database posture. |
| **Recommendation** | Migrate to Amazon ElastiCache for Redis or Amazon MemoryDB for Redis (on EKS per preferences). Enable Multi-AZ replication, automated backups, and encryption in transit. The Helm chart's `externalRedisTlsOrigination` configuration already supports external Redis with TLS, reducing migration effort. |
| **Evidence** | `terraform/memorystore.tf`, `terraform/terraform.tfvars`, `helm-chart/values.yaml` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service is used. The checkout flow (cart → payment → shipping → email) is orchestrated directly by the `checkoutservice` via synchronous gRPC calls. The payment charge logic in `charge.js` is inline validation and UUID generation with no state machine or orchestration layer. No Step Functions, Temporal, Camunda, or equivalent detected. |
| **Gap** | All workflow logic is hardcoded in application code. The checkout flow has no durable execution, no automatic retry with backoff, and no visual workflow management. A failure in any step leaves the transaction in an inconsistent state. |
| **Recommendation** | Introduce AWS Step Functions for the checkout orchestration flow (cart retrieval → payment charge → shipping → email notification). This provides built-in retry logic, error handling, and visual workflow monitoring. Each existing gRPC service maps cleanly to a Step Functions task. |
| **Evidence** | `src/paymentservice/charge.js`, `proto/demo.proto` (CheckoutService.PlaceOrder orchestrates Payment, Shipping, Email) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC. The `demo.proto` defines 10 gRPC services, all with unary (request-response) RPCs. No SQS, SNS, EventBridge, Kafka, RabbitMQ, Kinesis, or any messaging/streaming infrastructure detected in IaC, Kubernetes manifests, or source code. No event-driven patterns found. |
| **Gap** | The absence of async messaging means all services are tightly coupled through synchronous calls. A failure or latency spike in the payment service cascades directly to the checkout service and ultimately to the frontend. No event-driven decoupling exists for any flow. |
| **Recommendation** | Introduce Amazon SQS or Amazon EventBridge for decoupling non-critical flows (e.g., email notifications after payment). For payment specifically, consider an async charge pattern with SQS: checkout submits charge request to a queue, payment service processes asynchronously, and checkout polls for completion. This improves resilience without blocking the user. |
| **Evidence** | `proto/demo.proto` (all unary RPCs), `src/paymentservice/server.js` (synchronous ChargeServiceHandler) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The paymentservice is deployed as a `ClusterIP` service (not publicly exposed) in `kubernetes-manifests/paymentservice.yaml`. The Helm chart (`helm-chart/templates/paymentservice.yaml`) supports conditional NetworkPolicy creation that restricts ingress to only the `checkoutservice` on port 50051. Istio service mesh artifacts (`istio-manifests/`) provide Gateway, VirtualService, and ServiceEntry for network segmentation. AuthorizationPolicy restricts the `/hipstershop.PaymentService/Charge` endpoint to only the `checkoutservice` service account principal. GKE Autopilot runs in a VPC with `ip_allocation_policy`. |
| **Gap** | Network policies and Istio AuthorizationPolicies are optional and disabled by default (`values.yaml`: `networkPolicies.create: false`, `authorizationPolicies.create: false`). The default deployment has no fine-grained network restrictions — any pod in the namespace can reach the payment service. |
| **Recommendation** | Enable NetworkPolicies and AuthorizationPolicies by default in the Helm values. When migrating to EKS (per preferences), implement Kubernetes NetworkPolicies with a CNI that supports them (e.g., Calico on EKS) and consider AWS App Mesh or Istio on EKS for service-level authorization. |
| **Evidence** | `kubernetes-manifests/paymentservice.yaml`, `helm-chart/templates/paymentservice.yaml` (NetworkPolicy, AuthorizationPolicy), `helm-chart/values.yaml`, `istio-manifests/frontend-gateway.yaml` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The frontend service is exposed through an Istio Gateway (`istio-manifests/frontend-gateway.yaml`) with a VirtualService routing to the frontend on port 80. The paymentservice is properly internal-only (`ClusterIP`), accessible only within the cluster. The Helm chart supports configuring a VirtualService for the frontend with gateway references (`values.yaml`: `frontend.virtualService`). |
| **Gap** | The Istio Gateway handles basic HTTP routing but has no throttling, request validation, or authentication configuration. The gateway accepts all hosts (`hosts: ["*"]`) on port 80 (HTTP, not HTTPS). No API Gateway with rate limiting or request validation exists for the external entry point. |
| **Recommendation** | When migrating to AWS, use an Application Load Balancer (ALB) with AWS WAF for the frontend, or API Gateway for API endpoints. Configure rate limiting, request validation, and TLS termination. The paymentservice should remain internal-only, accessible via service mesh or internal ALB. |
| **Evidence** | `istio-manifests/frontend-gateway.yaml`, `istio-manifests/frontend.yaml`, `kubernetes-manifests/paymentservice.yaml` (ClusterIP), `helm-chart/values.yaml` (frontend.virtualService) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot (`terraform/main.tf`: `enable_autopilot = true`) automatically manages node-level scaling based on workload resource requests. The paymentservice Deployment specifies resource requests (`cpu: 100m`, `memory: 64Mi`) and limits (`cpu: 200m`, `memory: 128Mi`) in `kubernetes-manifests/paymentservice.yaml`. However, no HorizontalPodAutoscaler (HPA) is configured for application-level scaling. The Deployment defaults to 1 replica (no `replicas` field specified). |
| **Gap** | While GKE Autopilot handles node provisioning, there is no application-level auto-scaling. The paymentservice runs a single replica by default and cannot scale horizontally in response to traffic spikes. No HPA, KEDA, or custom scaling metrics are configured. |
| **Recommendation** | Add HPA configuration targeting CPU utilization or custom gRPC metrics. On EKS (per preferences), deploy KEDA for event-driven auto-scaling or use the Kubernetes Metrics Server with HPA. Set minimum replicas to 2 for high availability and maximum replicas based on expected peak load. |
| **Evidence** | `terraform/main.tf` (enable_autopilot), `kubernetes-manifests/paymentservice.yaml` (resource requests/limits, no HPA), `helm-chart/values.yaml` (paymentService.resources) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found anywhere in the repository. The optional Memorystore Redis (`terraform/memorystore.tf`) has no `persistence_config` or `maintenance_policy` configured. The in-cluster Redis has no backup mechanism. No AWS Backup plans, no EBS snapshot policies, no S3 versioning — and no GCP equivalents configured either. |
| **Gap** | Cart data stored in Redis has no backup or recovery capability. A Redis failure results in complete cart data loss with no recovery path. The paymentservice is stateless (no data to back up), but the broader application has unprotected data stores. |
| **Recommendation** | When migrating to AWS, enable automated backups on ElastiCache with a 7-day retention period and point-in-time recovery. Implement AWS Backup for centralized backup management across all data stores. Define and test a restore runbook. |
| **Evidence** | `terraform/memorystore.tf` (no backup config), `helm-chart/values.yaml` (cartDatabase with no backup settings) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot is a regional cluster (`terraform/main.tf`: `location = var.region`, default `us-central1`), which inherently distributes workloads across multiple availability zones. However, the paymentservice Deployment has no explicit replica count (defaults to 1 replica), meaning a single pod failure takes down the service entirely. No pod disruption budgets are configured. The in-cluster Redis is also a single-replica deployment. |
| **Gap** | While the platform supports multi-AZ distribution, the application does not leverage it. A single replica per service means no fault isolation at the application level. No PodDisruptionBudgets protect against voluntary disruptions (e.g., node upgrades). |
| **Recommendation** | Set `replicas: 2` minimum for all production services. Add `topologySpreadConstraints` to distribute pods across AZs. Configure PodDisruptionBudgets to maintain minimum availability during rolling updates. On EKS (per preferences), use managed node groups across multiple AZs with pod topology spread. |
| **Evidence** | `terraform/main.tf` (regional cluster), `kubernetes-manifests/paymentservice.yaml` (no replicas field, no PDB), `helm-chart/templates/paymentservice.yaml` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Infrastructure is extensively defined in code: Terraform (`terraform/`) provisions the GKE cluster and optional Memorystore. Kubernetes manifests (`kubernetes-manifests/`) define all 12 service Deployments, Services, and ServiceAccounts. Helm chart (`helm-chart/`) provides parameterized templating with NetworkPolicies, Sidecars, and AuthorizationPolicies. Kustomize (`kustomize/`) provides base + component overlays for network policies, service mesh, Memorystore, Spanner, and AlloyDB. Skaffold (`skaffold.yaml`) orchestrates build and deploy. CI pipelines validate Terraform (`terraform-validate-ci.yaml`), Helm (`helm-chart-ci.yaml`), and Kustomize (`kustomize-build-ci.yaml`). |
| **Gap** | Monitoring, alerting, dashboards, SLO definitions, and observability infrastructure are not defined in IaC. No Terraform for CloudWatch, Prometheus, Grafana, or equivalent. The OpenTelemetry Collector is optionally defined in Helm but not the backend trace/metrics storage. |
| **Recommendation** | Extend Terraform (per preferences) to cover observability infrastructure: EKS cluster, ElastiCache, CloudWatch dashboards, alarms, and X-Ray configuration. Adopt a GitOps workflow (per preferences) with ArgoCD to manage Kubernetes manifests declaratively from Git. |
| **Evidence** | `terraform/main.tf`, `terraform/memorystore.tf`, `kubernetes-manifests/`, `helm-chart/`, `kustomize/`, `skaffold.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/helm-chart-ci.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD pipelines exist: GitHub Actions (`ci-pr.yaml`) runs code tests (Go, C# unit tests), deploys to a PR-specific GKE namespace, waits for pod readiness, and runs smoke tests (loadgenerator error count check). `ci-main.yaml` runs the same pipeline on main/release branches. Supplementary pipelines validate Helm charts, Terraform, and Kustomize builds. Cloud Build (`cloudbuild.yaml`) provides an alternative Skaffold-based deployment path. Build concurrency management prevents parallel PR deployments. |
| **Gap** | No automated rollback on failed deployments. No security scanning gates (no SAST, DAST, dependency scanning). No explicit deploy-to-production stage — CI deploys directly via Skaffold. No canary or blue/green deployment strategy in the pipeline. No paymentservice-specific tests (test script is placeholder: `"test": "echo \"Error: no test specified\" && exit 1"`). |
| **Recommendation** | Add security scanning steps (Trivy for container images, npm audit for dependencies). Implement a GitOps-based deployment (per preferences) with ArgoCD for automated sync and rollback. Add paymentservice-specific unit tests and gRPC contract tests. Avoid manual deployments (per preferences) — ensure all environments are deployed via pipeline only. |
| **Evidence** | `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml`, `cloudbuild.yaml`, `skaffold.yaml`, `src/paymentservice/package.json` (placeholder test script) |


### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The paymentservice is written in Node.js (JavaScript), as evidenced by `package.json` (`"main": "index.js"`) and `.js` source files (`index.js`, `server.js`, `charge.js`, `logger.js`). The Dockerfile uses `node:20.20.1-alpine` — Node.js 20 is the current LTS with active support. Dependencies are managed via npm (`package.json`, `package-lock.json`). The broader microservices-demo uses Go, C#, Python, Java, and Node.js across its 12 services, demonstrating polyglot maturity. JavaScript/Node.js has a mature cloud-native ecosystem with extensive AWS SDK support, container-native tooling, and serverless compatibility. |
| **Gap** | No significant gap. Node.js 20 LTS is well-supported with a rich ecosystem. Minor note: the codebase uses CommonJS (`require()`) rather than ES Modules, which is functional but not the modern default. |
| **Recommendation** | Consider migrating to TypeScript for improved type safety and developer productivity, especially as the service evolves to handle real payment processing. Ensure Node.js version stays on active LTS releases. |
| **Evidence** | `src/paymentservice/package.json`, `src/paymentservice/index.js`, `src/paymentservice/Dockerfile` (node:20.20.1-alpine) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This is a well-decomposed microservices architecture. The `src/` directory contains 12 independently deployable services: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, loadgenerator, paymentservice, productcatalogservice, recommendationservice, shippingservice, and shoppingassistantservice. Each service has its own Dockerfile, Kubernetes Deployment, Service, and ServiceAccount (`kubernetes-manifests/`). The paymentservice is a single-purpose service with one RPC endpoint (`Charge`) and a clear bounded context (payment processing). Inter-service contracts are defined via Protocol Buffers (`proto/demo.proto`). Skaffold builds each service independently. |
| **Gap** | No significant gap. The services are independently deployable with clear boundaries. Minor consideration: all services share a single proto file (`demo.proto`), which could become a coordination bottleneck as the number of services grows. |
| **Recommendation** | Split the monolithic `demo.proto` into per-service proto files to enable independent API evolution. Maintain backward compatibility via protobuf's field numbering. The microservices architecture is mature — focus modernization effort on the infrastructure and operations gaps. |
| **Evidence** | `src/` (12 service directories), `kubernetes-manifests/` (per-service YAML), `proto/demo.proto` (all service contracts), `skaffold.yaml` (per-service build artifacts), `helm-chart/templates/` (per-service templates) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC. The `demo.proto` defines 10 gRPC services with exclusively unary (request-response) RPCs — no server streaming, client streaming, or bidirectional streaming. The paymentservice's `ChargeServiceHandler` in `server.js` processes charges synchronously and returns via callback. The checkout flow calls payment, shipping, and email services sequentially via synchronous gRPC. No message queues, event buses, pub/sub patterns, or async communication infrastructure detected anywhere. |
| **Gap** | 100% synchronous communication creates tight temporal coupling. The checkout service blocks while waiting for payment, shipping, and email responses. A slow or failing payment service directly impacts checkout latency and availability. Email notifications (non-critical) block the checkout response unnecessarily. |
| **Recommendation** | Introduce Amazon SQS for decoupling non-critical post-payment flows (email notifications, analytics events). Consider Amazon EventBridge for publishing domain events (PaymentProcessed, OrderShipped) that multiple services can subscribe to. Keep the payment charge itself synchronous (latency-sensitive) but decouple downstream effects. |
| **Evidence** | `proto/demo.proto` (all unary RPCs), `src/paymentservice/server.js` (synchronous callback: `callback(null, response)`), `src/paymentservice/charge.js` (synchronous processing) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All operations in the paymentservice are synchronous and return immediately. The `charge()` function in `charge.js` performs credit card validation and UUID generation — entirely CPU-bound and sub-millisecond. No background job processing, no async job frameworks (Celery, Bull, SQS workers), no status polling APIs, no webhook callbacks. The broader architecture has no long-running process handling either — the checkout orchestration is a synchronous chain of gRPC calls. |
| **Gap** | While current operations are fast (simulated), the architecture has no pattern for handling operations that might take longer (e.g., real payment gateway integration with 3D Secure authentication, fraud checks, or retry logic). All operations are assumed to complete within a single request-response cycle. |
| **Recommendation** | For real payment processing, implement an async charge pattern: accept the charge request, return a pending transaction ID immediately, process the charge asynchronously (via SQS worker), and provide a status polling endpoint. Use AWS Step Functions for multi-step payment workflows (authorize → capture → confirm). |
| **Evidence** | `src/paymentservice/charge.js` (synchronous `return { transaction_id: uuidv4() }`), `src/paymentservice/server.js` (synchronous callback pattern) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The gRPC service is defined in `proto/demo.proto` under package `hipstershop` with no version identifier in the package name, service name, or method definitions. The `PaymentService.Charge` RPC has no version prefix. No `/v1/`, `/v2/` patterns, no `Accept-Version` headers, no changelog file, and no version migration documentation. All 10 gRPC services in `demo.proto` share the same unversioned package. |
| **Gap** | Any change to the `ChargeRequest` or `ChargeResponse` protobuf messages could break all consumers (primarily `checkoutservice`). Protobuf provides backward-compatible field additions but has no mechanism for breaking changes without explicit versioning. No deprecation policy or migration path exists. |
| **Recommendation** | Adopt protobuf package versioning: rename package from `hipstershop` to `hipstershop.v1`. Create `v2` packages for breaking changes. Document a deprecation timeline for older versions. For per-service proto files (see APP-Q2 recommendation), version each service's API independently. |
| **Evidence** | `proto/demo.proto` (package `hipstershop` — no version), `src/paymentservice/server.js` (loads `hipstershop.PaymentService.service`) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes provides DNS-based service discovery. Each service is exposed via a `ClusterIP` Service resource (`kubernetes-manifests/paymentservice.yaml`) with a stable DNS name (`paymentservice:50051`). Services communicate using these Kubernetes DNS names — no hard-coded IP addresses. Istio VirtualService (`istio-manifests/frontend.yaml`) provides additional routing capabilities including traffic splitting and fault injection. The Helm chart supports Istio Sidecar configuration for egress control per service. Kubernetes ServiceAccounts are used for workload identity. |
| **Gap** | Service discovery is Kubernetes-native DNS, which is functional but not a full service registry. No service catalog, API registry, or centralized endpoint management exists. When Istio is not enabled, there is no advanced traffic management (canary routing, circuit breaking). Service endpoints are environment-specific (Kubernetes DNS names) with no abstraction layer for cross-environment discovery. |
| **Recommendation** | On EKS (per preferences), use AWS Cloud Map for service discovery or Istio on EKS for advanced traffic management. Consider publishing the gRPC service contracts to an API catalog for discoverability across teams. |
| **Evidence** | `kubernetes-manifests/paymentservice.yaml` (ClusterIP Service), `istio-manifests/frontend.yaml` (VirtualService), `helm-chart/templates/paymentservice.yaml` (Sidecar), `helm-chart/values.yaml` (service names used as DNS references) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The paymentservice processes only structured data: `ChargeRequest` containing `Money` (currency_code, units, nanos) and `CreditCardInfo` (credit_card_number, cvv, expiration). No unstructured data (documents, files, images, PDFs) is handled by the paymentservice or the broader application. No S3 buckets, GCS buckets, or object storage configured in IaC. No document parsing libraries (Textract, Tika, PDF processors) in any dependency manifest. Product images are referenced by URL path only (`product.picture` in `demo.proto`) with no storage management. |
| **Gap** | No capability to store or process unstructured data. For a payment service, this is a lower-priority gap, but the broader e-commerce application has no document storage for receipts, invoices, or compliance documents. |
| **Recommendation** | Introduce Amazon S3 for storing payment receipts, order confirmations, and compliance documents. Enable S3 intelligent tiering for cost optimization. For document parsing needs (e.g., receipt OCR), integrate Amazon Textract. |
| **Evidence** | `proto/demo.proto` (structured protobuf messages only), `src/paymentservice/charge.js` (structured input/output), `terraform/` (no object storage resources) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The paymentservice is stateless — it performs no database operations. The `charge()` function validates credit card data in memory and returns a UUID without any persistence. For the broader application, the cartservice connects to Redis directly via connection string (`helm-chart/values.yaml`: `cartDatabase.connectionString: "redis-cart:6379"`). Kustomize components support alternative databases (Spanner via `kustomize/components/spanner/`, AlloyDB via `kustomize/components/alloydb/`), but these are optional and the switch is done via infrastructure configuration, not through an abstraction layer. |
| **Gap** | No unified data access layer exists across the application. The cart service uses direct Redis connections. If the database backend changes (Redis → Spanner → AlloyDB), the switch is handled via Kustomize component overlays and environment variables rather than a code-level abstraction layer. There is no repository pattern, DAO layer, or data contract enforcement. |
| **Recommendation** | Implement a repository/DAO pattern for the cart service's data access. Introduce a data access abstraction that supports multiple backends (Redis, DynamoDB per preferences) behind a consistent interface. For the paymentservice, no action needed — stateless is the correct pattern. |
| **Evidence** | `src/paymentservice/charge.js` (no database access), `helm-chart/values.yaml` (cartDatabase.connectionString), `kustomize/components/` (spanner, alloydb, memorystore alternatives) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The optional Memorystore Redis instance explicitly pins the engine version: `redis_version = "REDIS_7_0"` in `terraform/memorystore.tf`. Redis 7.0 is actively supported (GA October 2022, community support ongoing). However, the default in-cluster Redis deployment (`helm-chart/values.yaml`: `cartDatabase.inClusterRedis`) uses the public Docker Hub Redis image with no version tag specified in the Helm values or Kubernetes manifests, meaning it pulls `latest` — an unpinned, drifting version. |
| **Gap** | Mixed version management: Memorystore is explicitly pinned (good), but the default in-cluster Redis has no version pin (risk). Running an unpinned Redis image means builds may get different Redis versions over time, and there is no EOL tracking or upgrade planning for the in-cluster instance. |
| **Recommendation** | Pin the in-cluster Redis image to a specific version tag (e.g., `redis:7.2-alpine`). When migrating to AWS ElastiCache (per preferences), explicitly pin the engine version in Terraform and establish a version lifecycle policy. Monitor Redis version EOL dates and plan upgrades 6 months before end-of-support. |
| **Evidence** | `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`), `helm-chart/values.yaml` (cartDatabase.inClusterRedis — no version pin) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs detected anywhere in the repository. The paymentservice has no database interaction — all business logic (credit card validation, charge processing) is in the application layer (`charge.js`). The cart service uses Redis key-value operations (no SQL at all). The optional Spanner and AlloyDB backends (via Kustomize components) are configured at the infrastructure level with no stored procedure usage detected. No `.sql` migration files, no `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements found. |
| **Gap** | No gap — all business logic resides in the application layer. This is the ideal state for database portability and modernization flexibility. |
| **Recommendation** | Maintain this pattern. As the application evolves, ensure business logic stays in the application layer rather than migrating to database-level stored procedures. This preserves database engine flexibility and simplifies any future database migration. |
| **Evidence** | `src/paymentservice/charge.js` (all logic in application), `proto/demo.proto` (no database-specific types), `terraform/memorystore.tf` (no stored procedure config), `kustomize/components/` (Spanner/AlloyDB infra-only config) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No audit logging infrastructure configured. No CloudTrail, no GCP Cloud Audit Logs configuration in Terraform or any IaC. The `terraform/main.tf` enables `monitoring.googleapis.com` and `cloudtrace.googleapis.com` APIs but does not configure audit log collection, retention, or immutable storage. The `helm-chart/values.yaml` has `googleCloudOperations` flags (profiler, tracing, metrics) but no audit logging configuration. Application-level logging via Pino (`logger.js`, `charge.js`) outputs structured JSON to stdout but there is no centralized log collection, retention policy, or immutable log storage. |
| **Gap** | No audit trail for API calls, infrastructure changes, or data access. Payment processing actions are logged to stdout but not collected into an immutable audit store. No log retention policies. No forensic investigation capability for security incidents. |
| **Recommendation** | When migrating to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Configure CloudWatch Logs for application log collection from EKS pods with defined retention periods. Implement AWS Config for infrastructure change tracking. For the paymentservice specifically, ensure all charge transactions are logged with correlation IDs to a centralized, tamper-proof audit log. |
| **Evidence** | `terraform/main.tf` (no audit logging resources), `helm-chart/values.yaml` (googleCloudOperations — no audit config), `src/paymentservice/logger.js` (stdout logging only) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration found for any data store. The optional Memorystore Redis (`terraform/memorystore.tf`) has no `auth_enabled`, `transit_encryption_mode`, or customer-managed encryption key configuration. The in-cluster Redis runs with default settings (no encryption). No KMS keys, no `encryption_configuration` blocks, and no `kms_key_id` references in any Terraform resource. No encryption settings in Kubernetes manifests or Helm values for data stores. |
| **Gap** | Cart data containing user session information is stored unencrypted in Redis. While the paymentservice itself is stateless, the broader application stores user data without encryption at rest. No customer-managed or AWS-managed encryption keys are configured for any resource. |
| **Recommendation** | When migrating to AWS, enable encryption at rest on all data stores: ElastiCache with AWS-managed or customer-managed KMS keys, S3 with SSE-KMS for any object storage, and EBS encryption for any persistent volumes. Use AWS KMS for centralized key management. For a P0 payment-related service, customer-managed KMS keys are recommended for audit control over key access. |
| **Evidence** | `terraform/memorystore.tf` (no encryption config), `helm-chart/values.yaml` (no encryption settings on cartDatabase), `kubernetes-manifests/paymentservice.yaml` (no volume encryption) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The paymentservice gRPC server uses insecure credentials: `grpc.ServerCredentials.createInsecure()` in `server.js`. No TLS, no mTLS, no OAuth2/JWT, and no authentication middleware at the application level. However, the Helm chart provides an optional Istio `AuthorizationPolicy` (`helm-chart/templates/paymentservice.yaml`) that restricts the `/hipstershop.PaymentService/Charge` endpoint to only the `checkoutservice` service account principal — this is network-level identity-based authorization. Additionally, the `NetworkPolicy` restricts ingress to the `checkoutservice` pod on port 50051. Both security mechanisms are disabled by default (`authorizationPolicies.create: false`, `networkPolicies.create: false`). |
| **Gap** | No application-level authentication — any process that can reach port 50051 can invoke the Charge RPC. The Istio AuthorizationPolicy and NetworkPolicy provide defense-in-depth but are optional and disabled by default. gRPC channel is unencrypted (no TLS). |
| **Recommendation** | Enable mTLS between services via Istio on EKS (per preferences) or implement gRPC TLS with client certificates. Enable NetworkPolicies and AuthorizationPolicies by default. For a payment service, consider adding application-level authentication tokens (e.g., signed JWTs) to verify caller identity independent of the service mesh. |
| **Evidence** | `src/paymentservice/server.js` (`grpc.ServerCredentials.createInsecure()`), `helm-chart/templates/paymentservice.yaml` (AuthorizationPolicy, NetworkPolicy — both conditional), `helm-chart/values.yaml` (`authorizationPolicies.create: false`) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration detected. No Cognito, Okta, Ping, or any OIDC/SAML configuration. The frontend generates session IDs for all users automatically with no signup or login required (per `README.md`: "Does not require signup/login and generates session IDs for all users automatically"). Kubernetes ServiceAccounts are used for workload identity (`kubernetes-manifests/paymentservice.yaml`: `serviceAccountName: paymentservice`), but there is no user-facing authentication system. The Helm chart supports ServiceAccount annotations for GCP Workload Identity (`serviceAccounts.annotations`) but no external IdP federation. |
| **Gap** | The application manages its own (trivial) session system with no external identity provider. No SSO, no federated identity, no centralized access policies. For a payment-processing context, the absence of user identity verification before processing charges is a significant gap. |
| **Recommendation** | Integrate Amazon Cognito for user authentication and session management. Implement OIDC-based identity federation for the frontend. For service-to-service identity, leverage EKS Pod Identity (per preferences) with IAM Roles for Service Accounts (IRSA). |
| **Evidence** | `README.md` ("Does not require signup/login"), `kubernetes-manifests/paymentservice.yaml` (ServiceAccount — no IdP), `helm-chart/values.yaml` (serviceAccounts config — GCP-specific) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No secrets management system detected. The paymentservice uses environment variables for configuration (`PORT`, `ENABLE_TRACING`, `DISABLE_PROFILER`, `COLLECTOR_SERVICE_ADDR`) set via Kubernetes Deployment env blocks. No AWS Secrets Manager, no HashiCorp Vault, no GCP Secret Manager references. No `secretKeyRef` in Kubernetes manifests. No hardcoded credentials found in source code (payment processing is simulated), but there is also no infrastructure for managing secrets when real credentials are needed. The `terraform.tfvars` contains a placeholder `gcp_project_id = "<project_id_here>"`, and the Helm chart Memorystore TLS certificate value is configured inline (`cartDatabase.externalRedisTlsOrigination.certificate`). |
| **Gap** | No secrets management infrastructure exists. When the service evolves to use real payment gateways (Stripe, Adyen), API keys and credentials will need secure storage, rotation, and audit. Currently, there is no pattern or infrastructure for this. Environment variables in Kubernetes are stored in plaintext in etcd. |
| **Recommendation** | Deploy AWS Secrets Manager with automatic rotation for all credentials. Use EKS Secrets Store CSI Driver to mount secrets as files or environment variables in pods. Implement external-secrets-operator for GitOps-compatible secrets management (per preferences). Establish a policy that prohibits hardcoded credentials and requires all secrets to be managed via Secrets Manager. |
| **Evidence** | `kubernetes-manifests/paymentservice.yaml` (env vars — no secretKeyRef), `helm-chart/templates/paymentservice.yaml` (env vars from values), `terraform/terraform.tfvars` (placeholder project ID), `helm-chart/values.yaml` (inline TLS certificate value) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Strong container hardening practices are in place. The Dockerfile uses a multi-stage build with `alpine:3.23.3` as the production base image, pinned by SHA256 digest for reproducibility. The Kubernetes security context (`kubernetes-manifests/paymentservice.yaml`) enforces: `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: ALL`, `privileged: false`. The Helm chart supports `seccompProfile` (optional, `type: RuntimeDefault`). GKE Autopilot provides automatic node upgrades and security patching at the node level. Renovate (`renovate.json5`) is configured for dependency update automation. |
| **Gap** | No container image vulnerability scanning (no Trivy, Snyk, or ECR image scanning). No runtime vulnerability scanning (no AWS Inspector or equivalent). Container hardening is excellent but there is no proactive vulnerability detection. Renovate helps with dependency freshness but does not scan for CVEs. |
| **Recommendation** | Integrate container image scanning (Trivy or Amazon ECR image scanning) into the CI/CD pipeline. Enable Amazon Inspector for runtime vulnerability analysis on EKS (per preferences). Consider Bottlerocket-based AMIs for EKS nodes for additional OS-level hardening. The existing container security context is well-configured — maintain these practices. |
| **Evidence** | `src/paymentservice/Dockerfile` (multi-stage, Alpine, SHA256 digest pin), `kubernetes-manifests/paymentservice.yaml` (comprehensive securityContext), `helm-chart/values.yaml` (seccompProfile option), `.github/renovate.json5` (dependency updates) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning is integrated into the CI/CD pipeline. The GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) run code tests and deployment smoke tests but no security scanning steps. No SonarQube, Semgrep, CodeGuru Reviewer, Snyk, or equivalent. No `npm audit` in the pipeline. No Dependabot configuration (Renovate handles dependency updates but not security scanning). No `.snyk` policy file. No container image scanning step. The CI pipeline has no security gates that could block deployments on critical findings. |
| **Gap** | The pipeline has zero security scanning coverage. Vulnerabilities in npm dependencies (the paymentservice has 13 direct dependencies), container base images, or application code reach production undetected. For a P0 payment-related service, this is a critical gap. |
| **Recommendation** | Add `npm audit --audit-level=high` to the CI pipeline for dependency vulnerability scanning. Integrate Amazon CodeGuru Reviewer or Semgrep for SAST. Add Trivy or Amazon ECR scanning for container images. Configure security gates to block merges on critical/high severity findings. Implement GitHub Advanced Security or Snyk for comprehensive security coverage across the pipeline. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (no security scanning steps), `.github/workflows/ci-main.yaml` (no security scanning steps), `src/paymentservice/package.json` (13 dependencies — not scanned), `.github/renovate.json5` (dependency updates only, not security scanning) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry is integrated in the paymentservice (`index.js`) with comprehensive instrumentation: `@opentelemetry/sdk-node` for the Node SDK, `@opentelemetry/instrumentation-grpc` for automatic gRPC tracing, `@opentelemetry/exporter-otlp-grpc` for OTLP export, and `@opentelemetry/resources` with `@opentelemetry/semantic-conventions` for standard resource attributes. When `ENABLE_TRACING=1`, the SDK initializes with `GrpcInstrumentation` and exports traces to a configurable collector (`COLLECTOR_SERVICE_ADDR`). The Helm chart configures `OTEL_SERVICE_NAME` and `COLLECTOR_SERVICE_ADDR` when the OpenTelemetry Collector is enabled. |
| **Gap** | Tracing is disabled by default (`ENABLE_TRACING` not set in `kubernetes-manifests/paymentservice.yaml`; requires `googleCloudOperations.tracing: true` in Helm values). The OpenTelemetry Collector deployment is optional (`opentelemetryCollector.create: false`). No trace backend storage (Jaeger, X-Ray) is provisioned. Trace propagation across all 12 services is not guaranteed — each service must independently enable tracing. |
| **Recommendation** | Enable tracing by default for all services. On EKS (per preferences), deploy the AWS Distro for OpenTelemetry (ADOT) collector and configure export to AWS X-Ray. Use the ADOT auto-instrumentation operator to ensure consistent trace propagation across all services without per-service configuration. |
| **Evidence** | `src/paymentservice/index.js` (OpenTelemetry SDK setup), `src/paymentservice/package.json` (@opentelemetry/* dependencies), `helm-chart/values.yaml` (opentelemetryCollector config, googleCloudOperations.tracing), `helm-chart/templates/paymentservice.yaml` (COLLECTOR_SERVICE_ADDR, ENABLE_TRACING env vars) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budgets, no service-level targets, no latency or availability objectives. No CloudWatch alarms, no GCP monitoring alerts, no Prometheus PrometheusRule or ServiceLevelObjective custom resources. No SLO configuration files, no SLI definitions. The Kubernetes manifests include `readinessProbe` and `livenessProbe` (gRPC health checks on port 50051), but these are operational health checks, not SLO definitions. |
| **Gap** | Without SLOs, there is no measurable definition of "good enough" for the payment service. No data-driven basis for prioritizing reliability investments or evaluating whether modernization improves service quality. For a P0 payment service, this is a critical operational gap. |
| **Recommendation** | Define SLOs for the paymentservice: availability target (e.g., 99.95% of Charge RPCs succeed), latency target (e.g., p99 < 200ms), and error rate target. On EKS with CloudWatch (per preferences), create CloudWatch ServiceLevelObjective resources or use CloudWatch Synthetics for SLI measurement. Implement error budget tracking and alerting when the budget is exhausted. |
| **Evidence** | `kubernetes-manifests/paymentservice.yaml` (health probes only — no SLO), `helm-chart/values.yaml` (no SLO config), `terraform/` (no monitoring/alerting resources) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The paymentservice logs transaction details via Pino (`charge.js`: `logger.info("Transaction processed: ${cardType} ending ${cardNumber.substr(-4)} Amount: ${amount.currency_code}${amount.units}.${amount.nanos}")`), which includes card type, last 4 digits, and amount. However, these are log lines, not structured metrics. No `cloudwatch.put_metric_data`, no Prometheus client library, no custom metric counters for business outcomes (successful charges, declined cards, charge amounts by currency). |
| **Gap** | No business metrics visibility. Cannot answer questions like: "How many charges processed per minute?", "What is the decline rate?", "What is the average charge amount?" Without business metrics, operational decisions rely on infrastructure metrics (CPU, memory) that don't reflect payment processing health. |
| **Recommendation** | Instrument the paymentservice with custom CloudWatch metrics (per preferences) or Prometheus client metrics: `payment_charges_total` (counter, by status/card_type), `payment_charge_amount` (histogram, by currency), `payment_charge_duration_seconds` (histogram). Publish via ADOT collector to CloudWatch Metrics on EKS. Create a payment-specific dashboard with these business KPIs. |
| **Evidence** | `src/paymentservice/charge.js` (log lines only — no metrics), `src/paymentservice/package.json` (no metrics client library), `helm-chart/values.yaml` (googleCloudOperations.metrics: false) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms, no GCP monitoring alerts, no Prometheus AlertManager rules, no PagerDuty/OpsGenie integration. No composite alarms, no threshold-based alerts, no anomaly detection on error rates or latency. The Kubernetes liveness and readiness probes provide basic pod-level health detection, but Kubernetes restarts are not alerting — they are self-healing without notification. |
| **Gap** | A payment processing outage or degradation would go undetected until users report issues. No proactive alerting exists for error rate spikes, latency increases, or pod restart loops. For a P0 payment service, silent failures are a critical risk. |
| **Recommendation** | Configure CloudWatch alarms (per preferences) for: payment error rate > 1%, p99 latency > 500ms, pod restart count > 0 in 5 minutes. Enable CloudWatch anomaly detection for error rate and latency baselines. Integrate with PagerDuty or OpsGenie for on-call notification. Deploy Amazon DevOps Guru for anomaly detection across the EKS cluster. |
| **Evidence** | `kubernetes-manifests/paymentservice.yaml` (health probes — not alerting), `terraform/` (no alerting resources), `helm-chart/` (no alerting config) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployments use Kubernetes `RollingUpdate` strategy by default (no explicit `strategy` field in `kubernetes-manifests/paymentservice.yaml`, which defaults to `RollingUpdate`). The CI pipeline deploys via Skaffold (`skaffold run`) which applies Kubernetes manifests directly. Cloud Build (`cloudbuild.yaml`) also uses Skaffold for deployment. PR deployments go to isolated namespaces (`pr${PR_NUMBER}`), which provides staging isolation. However, production deployments go directly to the target namespace with no canary traffic splitting, no blue/green cutover, and no automated rollback. |
| **Gap** | No progressive delivery strategy. Production deployments are all-at-once rolling updates with no ability to detect regressions before full rollout. No traffic shifting, no canary analysis, no automated rollback on failure metrics. With a single default replica, the rolling update is effectively a big-bang deployment. |
| **Recommendation** | Implement GitOps-based progressive delivery (per preferences) with ArgoCD Rollouts for canary deployments on EKS. Configure canary analysis with CloudWatch metrics (error rate, latency) to automatically promote or rollback. Avoid manual deployments (per preferences) — all environments should be deployed via GitOps with automated promotion gates. |
| **Evidence** | `kubernetes-manifests/paymentservice.yaml` (no strategy field — defaults to RollingUpdate), `skaffold.yaml` (direct kubectl deploy), `cloudbuild.yaml` (Skaffold-based deploy), `.github/workflows/ci-pr.yaml` (PR namespace isolation) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CI pipeline includes a comprehensive integration/smoke test flow. `ci-pr.yaml` deploys the entire application to a PR-specific GKE namespace, waits for all 12 deployments to become available, queries the frontend external IP, restarts the loadgenerator, waits for 50+ requests, and then checks for zero errors (`ERROR_COUNT` from loadgenerator logs). This validates the entire end-to-end flow including the paymentservice (loadgenerator simulates checkout flows that hit payment). Supplementary CI pipelines validate Helm templates (`helm-chart-ci.yaml`) and Terraform (`terraform-validate-ci.yaml`). |
| **Gap** | Integration testing is end-to-end (loadgenerator-driven) but not service-specific. No gRPC contract tests for the PaymentService.Charge endpoint. The paymentservice has no unit tests (`package.json`: `"test": "echo \"Error: no test specified\" && exit 1"`). Smoke tests check for zero errors but don't validate specific payment scenarios (valid card, expired card, unsupported card type). |
| **Recommendation** | Add paymentservice-specific unit tests for `charge.js` covering: valid VISA/MasterCard charges, expired card rejection, unsupported card type rejection (AMEX, Diners Club), invalid card number rejection. Add gRPC contract tests using grpc-testing or buf to validate proto compatibility. Keep the end-to-end smoke tests but supplement with service-level tests. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (deployment-tests with smoke testing), `.github/workflows/ci-main.yaml` (same pattern), `src/paymentservice/package.json` (placeholder test script), `.github/workflows/helm-chart-ci.yaml` (Helm template validation) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation found. No runbooks (markdown, YAML, or JSON). No SSM Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. No self-healing patterns beyond Kubernetes pod restart on liveness probe failure. The `SECURITY.md` file provides a vulnerability reporting process (Google's g.co/vulnz) but no operational incident response procedures. No PagerDuty/OpsGenie integration for escalation. |
| **Gap** | Incident response is entirely ad hoc. When a payment processing issue occurs, there is no documented procedure, no automated remediation, and no escalation path. Kubernetes restarts failed pods (basic self-healing) but does not address root causes or notify operators. |
| **Recommendation** | Create machine-readable runbooks for common payment service incidents (pod CrashLoopBackOff, high error rate, latency spike, Redis connection failure). On AWS (per preferences), implement SSM Automation documents for common remediation actions. Integrate CloudWatch alarms with SNS → Lambda for automated incident response (e.g., auto-scale on high latency, restart pods on high error rate). |
| **Evidence** | `.github/SECURITY.md` (vulnerability reporting only), `kubernetes-manifests/paymentservice.yaml` (liveness probe — basic self-healing only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The `CODEOWNERS` file assigns the entire repository to a single team: `* @GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver`. No per-service observability ownership. No service-level dashboards. No alarm ownership. No team attribution on monitoring resources. The paymentservice has no dedicated observability configuration — it inherits the global Helm chart's optional OTel collector and Google Cloud Operations settings. |
| **Gap** | No observability ownership model. No one is explicitly responsible for the paymentservice's health metrics, dashboards, or alarms. In a microservices architecture with 12 services, shared ownership leads to monitoring gaps. |
| **Recommendation** | Establish per-service observability ownership. Add CODEOWNERS entries for observability assets (e.g., `helm-chart/templates/paymentservice.yaml @payment-team`). Create per-service CloudWatch dashboards (per preferences) with named owners. Tag alarms with owner metadata. Define on-call rotations per service domain. |
| **Evidence** | `.github/CODEOWNERS` (single team for entire repo), `helm-chart/values.yaml` (no per-service observability config) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging governance found. Terraform resources (`terraform/main.tf`, `terraform/memorystore.tf`) have no `tags` or `labels` blocks. The Terraform provider (`providers.tf`) has no `default_tags` configuration. Kubernetes resources have basic `app` labels (`app: paymentservice`) for selector matching but no cost allocation, ownership, or environment tags. No tag enforcement rules, no AWS Config required-tags rules, no GCP label policies. |
| **Gap** | Cannot track costs per service, identify resource ownership during incidents, or enforce budget controls. Kubernetes labels are minimal (app name only) — missing: `environment`, `team`, `cost-center`, `version`, `managed-by`. |
| **Recommendation** | Implement a tagging standard with mandatory tags: `environment`, `service`, `team`, `cost-center`. Add `default_tags` to the Terraform provider (per preferences) for all infrastructure resources. Add standard Kubernetes labels following the [recommended labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/): `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/component`, `app.kubernetes.io/managed-by`. Enforce tagging via AWS Config rules or OPA policies. |
| **Evidence** | `terraform/main.tf` (no tags), `terraform/providers.tf` (no default_tags), `terraform/memorystore.tf` (no labels), `kubernetes-manifests/paymentservice.yaml` (only `app: paymentservice` label) |

---

## Learning Materials

### Move to Managed Databases
- [Move to Managed Databases — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [Amazon ElastiCache for Redis Migration Guide](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Migration.html)

### Move to AI
- [Move to AI — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/paymentservice/index.js` | OPS-Q1, APP-Q1 | OpenTelemetry tracing setup, application entry point |
| `src/paymentservice/server.js` | SEC-Q3, APP-Q3, APP-Q4, INF-Q4 | gRPC server with insecure credentials, synchronous handler |
| `src/paymentservice/charge.js` | INF-Q3, APP-Q3, APP-Q4, DATA-Q4, OPS-Q3 | Payment charge logic — synchronous, stateless, application-layer only |
| `src/paymentservice/logger.js` | SEC-Q1, OPS-Q3 | Pino structured logging configuration |
| `src/paymentservice/package.json` | APP-Q1, OPS-Q1, OPS-Q6, INF-Q11, SEC-Q7 | Dependencies (13 packages), placeholder test script |
| `src/paymentservice/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage build, Alpine base, SHA256 digest pinning |
| `proto/demo.proto` | APP-Q2, APP-Q3, APP-Q5, INF-Q4, DATA-Q1 | All gRPC service contracts, unary RPCs, unversioned package |
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q9, INF-Q10, OPS-Q9 | GKE Autopilot cluster, regional deployment |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q2 | Optional Memorystore Redis, version pin, no encryption/backup |
| `terraform/providers.tf` | OPS-Q9 | Google provider — no default_tags |
| `terraform/terraform.tfvars` | INF-Q2, SEC-Q5 | memorystore=false, placeholder project ID |
| `terraform/variables.tf` | INF-Q2 | Variable definitions for cluster and memorystore |
| `kubernetes-manifests/paymentservice.yaml` | INF-Q1, INF-Q5, INF-Q7, INF-Q9, SEC-Q3, SEC-Q5, SEC-Q6, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q7, OPS-Q9, APP-Q6 | Deployment, Service, ServiceAccount with security context |
| `helm-chart/Chart.yaml` | INF-Q10 | Helm chart metadata, version 0.10.5 |
| `helm-chart/values.yaml` | INF-Q2, INF-Q5, INF-Q10, SEC-Q1, SEC-Q2, SEC-Q4, OPS-Q1, OPS-Q2, OPS-Q8, APP-Q6, DATA-Q2, DATA-Q3 | Global configuration, cartDatabase, optional features |
| `helm-chart/templates/paymentservice.yaml` | INF-Q1, INF-Q5, INF-Q9, SEC-Q3, OPS-Q1 | Templated deployment with NetworkPolicy, Sidecar, AuthorizationPolicy |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | PR CI pipeline — tests, deploy, smoke tests |
| `.github/workflows/ci-main.yaml` | INF-Q11, OPS-Q5, SEC-Q7 | Main branch CI pipeline |
| `.github/workflows/helm-chart-ci.yaml` | INF-Q10, INF-Q11, OPS-Q6 | Helm chart validation pipeline |
| `.github/workflows/terraform-validate-ci.yaml` | INF-Q10, INF-Q11 | Terraform validation pipeline |
| `cloudbuild.yaml` | INF-Q11, OPS-Q5 | Cloud Build deployment via Skaffold |
| `skaffold.yaml` | INF-Q1, INF-Q10, INF-Q11, OPS-Q5 | Build orchestration for all 12 services |
| `istio-manifests/frontend-gateway.yaml` | INF-Q5, INF-Q6 | Istio Gateway and VirtualService for frontend |
| `istio-manifests/frontend.yaml` | INF-Q6, APP-Q6 | VirtualService for frontend routing |
| `istio-manifests/allow-egress-googleapis.yaml` | INF-Q5 | ServiceEntry for Google API egress |
| `kustomize/kustomization.yaml` | INF-Q10, DATA-Q2, DATA-Q4 | Base + optional components |
| `.github/CODEOWNERS` | OPS-Q8 | Single team ownership for entire repo |
| `.github/SECURITY.md` | OPS-Q7 | Vulnerability reporting process only |
| `.github/renovate.json5` | SEC-Q6, SEC-Q7 | Dependency update automation (not security scanning) |
| `README.md` | SEC-Q4, APP-Q2, Quick Agent Wins | Architecture documentation, 11 microservices description |