# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | adservice |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P2 |
| **Tags** | java, grpc, ads |
| **Context** | Java gRPC service serving contextual ads based on product categories. |
| **Overall Score** | 2.07 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.27 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **2.07 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | OPS-Q1: Distributed Tracing | 1 | OpenTelemetry tracing is stubbed with TODO comments but not implemented; no tracing SDK in dependencies. | Cannot trace requests across service boundaries; debugging production issues in the microservices mesh is guesswork. |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured in IaC. | No forensic capability; compliance risk for production workloads; cannot trace infrastructure changes. |
| 3 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption-at-rest configuration found for any data store. | Sensitive data exposure risk; fails compliance baselines for regulated workloads. |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline. | Vulnerabilities in dependencies or code reach production undetected; adservice Java deps are not scanned. |
| 5 | APP-Q3: Async vs Sync Communication | 1 | All inter-service communication is synchronous gRPC with no async patterns. | Tight coupling, cascading failure risk; no event-driven decoupling for resilience. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists with GitHub Actions, Skaffold, and Cloud Build).
- **What it enables:** An AI agent that triggers deployments via Skaffold/Cloud Build, checks build status across GitHub Actions workflows, manages release tagging, and monitors deployment pod readiness — all through natural language commands.
- **Evidence:** `.github/workflows/ci-pr.yaml` and `ci-main.yaml` define automated CI pipelines; `cloudbuild.yaml` provides Cloud Build deployment; `skaffold.yaml` orchestrates builds for all 12 services. These surfaces are already API-accessible.
- **Additional steps:** Expose GitHub Actions and Cloud Build status via API tokens; create a thin wrapper for Skaffold CLI invocation. Consider integrating with a GitOps tool (e.g., Flux or ArgoCD, per `gitops` preference) to provide a declarative deployment surface for the agent.
- **Effort:** Low — existing pipeline provides the automation surface; agent orchestrates pipeline actions via API.

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — `README.md` in adservice, `demo.proto` with full service API definitions for all 12 microservices, Helm chart `README.md`, Kustomize `README.md`, and workflow `README.md`.
- **What it enables:** A Retrieval-Augmented Generation agent using Amazon Bedrock (per preferences) that indexes the repository documentation, protobuf API specs, Helm values, and Kustomize component docs. Developers can ask natural language questions about service contracts, deployment options, and configuration parameters.
- **Evidence:** `src/adservice/README.md` (build instructions), `src/main/proto/demo.proto` (complete API contract for all services), `helm-chart/README.md`, `kustomize/README.md`, `.github/workflows/README.md`.
- **Additional steps:** Index documentation into a vector store (e.g., Amazon OpenSearch Service with vector engine or Amazon Bedrock Knowledge Bases). Generate embeddings from proto files and configuration docs. The proto file is particularly valuable as it contains the full API contract for the entire microservices ecosystem.
- **Effort:** Medium — documentation corpus exists but needs embedding and indexing; proto files need parsing for structured extraction.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — application is already a microservices architecture with well-defined service boundaries. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 — compute is already containerized on GKE Autopilot with Dockerfiles and Kubernetes manifests. Contextual guard: containers already in use. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected (Redis is open source). |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 — databases are already managed (Memorystore Redis option). AdService has no database. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected for adservice. Contextual guard prevents triggering. |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3 and INF-Q11 = 3 — IaC coverage and CI/CD automation meet the threshold (both ≥ 3). |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent framework usage detected — no Bedrock SDK, LangChain, Strands, OpenAI, or any AI imports in source code. No vector DB, no RAG, no agent eval framework. |

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

The adservice repository contains **no AI or agent framework usage** across all scanned files:

- **AI/Agent Frameworks:** No imports of Bedrock SDK, LangChain, Strands SDK, OpenAI, Spring AI, HuggingFace, or SageMaker SDK found in `build.gradle` or Java source files.
- **Vector Database Infrastructure:** No OpenSearch vector engine, Pinecone, pgvector, Weaviate, or Qdrant detected in IaC or dependencies.
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns found.
- **Agent Evaluation Frameworks:** No Ragas, DeepEval, or custom evaluation harness detected.

#### Application Domain and Potential AI Use Cases

The adservice currently serves ads based on a hardcoded in-memory map of product categories to ad content (`createAdsMap()` in `AdService.java`). This is a prime candidate for AI enhancement:

1. **AI-Powered Ad Targeting:** Replace the static `ImmutableListMultimap<String, Ad>` with a Bedrock-powered recommendation engine that generates contextual ads based on product descriptions, user browsing patterns, and real-time context. The `AdRequest.context_keys` field already provides the hook for context-aware ad selection.

2. **Dynamic Ad Content Generation:** Use Amazon Bedrock foundation models to dynamically generate ad copy (`Ad.text` field) tailored to product categories, seasonal promotions, and user segments — replacing the hardcoded text strings like "Hairdryer for sale. 50% off."

3. **Ad Relevance Scoring:** Implement an AI-based relevance scoring model that ranks ad candidates by predicted engagement, replacing the current `random.nextInt(allAds.size())` random selection in `getRandomAds()`.

#### Quick Wins

See the [Quick Agent Wins](#quick-agent-wins) section above for immediate AI integration opportunities (DevOps Agent, RAG-Based Knowledge Agent) that can be pursued while building the broader AI infrastructure.

#### Recommended AI Services (Per Preferences)

Per the technology preferences (`prefer: ["bedrock"]`), the recommended AWS AI services are:

- **Amazon Bedrock** — Foundation model access for ad content generation and relevance scoring. Bedrock's serverless inference eliminates model hosting overhead.
- **Amazon Bedrock Knowledge Bases** — RAG implementation for the knowledge agent quick win, using repository documentation as the corpus.
- **Amazon Bedrock AgentCore** — For building and deploying the DevOps agent and knowledge agent identified in Quick Agent Wins.
- **Amazon OpenSearch Service** (vector engine) — Vector store for ad embeddings and similarity search, enabling context-aware ad retrieval.
- **Amazon DynamoDB** (per preferences: `prefer: ["dynamodb"]`) — Replace the in-memory ad store with DynamoDB for persistent, scalable ad catalog storage with vector embeddings.

#### Foundation Requirements

Before AI integration, the following foundations should be in place:

1. **Externalize ad data** — Move ad catalog from hardcoded `createAdsMap()` to an external data store (DynamoDB per preferences). This is a prerequisite for any dynamic ad serving.
2. **Implement observability** — Complete the TODO OpenTelemetry instrumentation (`initTracing()`, `initStats()`) to monitor AI inference latency and ad serving performance.
3. **Add API versioning** — Version the gRPC `AdService` API (e.g., `hipstershop.v1.AdService`) before adding AI-powered endpoints to maintain backward compatibility.
4. **Establish secrets management** — AI service credentials (Bedrock API keys, DynamoDB access) require a secrets management pattern that doesn't currently exist.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The adservice runs on GKE Autopilot, a fully managed Kubernetes service. Terraform in `terraform/main.tf` provisions `google_container_cluster` with `enable_autopilot = true`. The service is containerized via a multi-stage `Dockerfile` (eclipse-temurin base) and deployed as a Kubernetes Deployment (`kubernetes-manifests/adservice.yaml`). Helm chart (`helm-chart/templates/adservice.yaml`) provides templated deployment. This is managed container orchestration equivalent to EKS/ECS. |
| **Gap** | Infrastructure is GCP-native (GKE), not AWS. To align with AWS modernization, migration to EKS (per `prefer: ["eks"]`) would be needed. No raw EC2/VM usage detected — all compute is containerized. |
| **Recommendation** | Migrate to Amazon EKS with managed node groups or EKS Autopilot (per `prefer: ["eks"]`). The existing Kubernetes manifests, Helm charts, and Kustomize overlays are portable to EKS with minimal changes. Use Terraform (per `prefer: ["terraform"]`) for EKS cluster provisioning. |
| **Evidence** | `terraform/main.tf` (google_container_cluster), `src/adservice/Dockerfile`, `kubernetes-manifests/adservice.yaml`, `helm-chart/templates/adservice.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The adservice itself uses no database — ad data is hardcoded in-memory via `ImmutableListMultimap` in `AdService.java`. The broader platform offers managed Redis via Google Cloud Memorystore (`terraform/memorystore.tf`: `google_redis_instance` with `redis_version = "REDIS_7_0"`), used by cartservice. The default configuration uses in-cluster Redis (`helm-chart/values.yaml`: `cartDatabase.inClusterRedis.create: true`). |
| **Gap** | The adservice has no persistent data store, which is a limitation for dynamic ad content. The platform's Redis is offered as managed (Memorystore) but defaults to in-cluster (self-managed). |
| **Recommendation** | When externalizing ad data, use Amazon DynamoDB (per `prefer: ["dynamodb"]`) for the ad catalog. DynamoDB provides single-digit millisecond latency suitable for ad serving. For the platform's Redis, migrate to Amazon ElastiCache or MemoryDB. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (createAdsMap), `terraform/memorystore.tf`, `helm-chart/values.yaml` (cartDatabase section) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service detected. The adservice is a simple request-response gRPC service with no multi-step workflows. No Step Functions, Temporal, Camunda, or Airflow configurations found. No state machine patterns in the Java source code. |
| **Gap** | No orchestration capability exists. If the service evolves to include multi-step ad bidding, campaign management, or A/B testing workflows, there is no infrastructure to support them. |
| **Recommendation** | Evaluate AWS Step Functions for future workflow needs (e.g., ad campaign lifecycle management, A/B test orchestration). For the current simple request-response pattern, this is low priority. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (simple getAds RPC, no workflow logic) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure detected. All inter-service communication is synchronous gRPC. The `demo.proto` defines only unary RPCs for all services. No SQS, SNS, EventBridge, Kafka, Kinesis, or RabbitMQ references found in IaC, source code, or Kubernetes manifests. |
| **Gap** | The absence of async messaging means the adservice cannot decouple from its consumers, cannot buffer requests during load spikes, and has no event-driven integration path. |
| **Recommendation** | Introduce Amazon SNS/SQS for event-driven patterns — e.g., ad impression tracking events, campaign update notifications. For real-time ad event streaming (clicks, impressions), evaluate Amazon Kinesis Data Streams. Avoid self-managed Kafka per `avoid: ["manual-deployments"]`. |
| **Evidence** | `src/main/proto/demo.proto` (unary RPCs only), absence of messaging imports in `build.gradle`, absence of messaging resources in `terraform/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes NetworkPolicy in Helm chart (`helm-chart/templates/adservice.yaml`) restricts ingress to frontend only on port 9555 with TCP protocol. Istio AuthorizationPolicy restricts access to the `hipstershop.AdService/GetAds` path from the frontend service principal via mTLS. Sidecar resource limits egress to `istio-system/*`. Pod security context enforces `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, and drops ALL capabilities. However, these features are **optional** — `networkPolicies.create: false`, `authorizationPolicies.create: false`, and `sidecars.create: false` in `values.yaml` defaults. |
| **Gap** | Network security features are well-defined but disabled by default. In the base Kubernetes manifests (`kubernetes-manifests/adservice.yaml`), no NetworkPolicy is defined. The adservice ClusterIP Service is accessible to any pod in the namespace without network policies enabled. |
| **Recommendation** | Enable NetworkPolicies and AuthorizationPolicies by default in Helm values. When migrating to EKS, implement VPC subneting with private subnets, security groups, and AWS VPC CNI network policies. Consider EKS Pod Identity for fine-grained IAM. |
| **Evidence** | `helm-chart/templates/adservice.yaml` (NetworkPolicy, AuthorizationPolicy, Sidecar), `helm-chart/values.yaml` (defaults: false), `kubernetes-manifests/adservice.yaml` (security context) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The frontend service acts as the API entry point for external users. Istio Gateway (`istio-manifests/frontend-gateway.yaml`) provides ingress routing via `istio: ingressgateway` to the frontend on port 80. The adservice is internal-only (ClusterIP Service on port 9555), not directly exposed externally. Istio VirtualService provides routing and traffic management. |
| **Gap** | The Istio Gateway lacks TLS configuration (HTTP only on port 80). No API throttling, request validation, or WAF protection on the ingress. The adservice itself has no rate limiting. |
| **Recommendation** | When migrating to AWS, use an Application Load Balancer with AWS WAF, or Amazon API Gateway for external ingress. For the internal gRPC adservice, EKS with App Mesh or Istio on EKS provides equivalent service mesh routing. Implement TLS termination at the ingress layer. |
| **Evidence** | `istio-manifests/frontend-gateway.yaml` (Gateway, VirtualService), `kubernetes-manifests/adservice.yaml` (ClusterIP Service) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot automatically manages node scaling based on pod resource requests. The adservice Deployment defines resource requests (cpu: 200m, memory: 180Mi) and limits (cpu: 300m, memory: 300Mi) in both `kubernetes-manifests/adservice.yaml` and `helm-chart/values.yaml`. However, no HorizontalPodAutoscaler (HPA) is defined for the adservice — the Deployment defaults to 1 replica with no pod-level autoscaling. |
| **Gap** | While GKE Autopilot scales nodes, the adservice cannot scale pods in response to traffic changes. A single replica creates a single point of failure during pod restarts or node evictions. |
| **Recommendation** | Define a HorizontalPodAutoscaler for adservice targeting CPU utilization or gRPC request rate. On EKS (per preferences), use KEDA or Kubernetes Metrics Server with HPA. Set minimum replicas ≥ 2 for availability. |
| **Evidence** | `kubernetes-manifests/adservice.yaml` (resource requests/limits, no HPA), `helm-chart/values.yaml` (adService.resources), `terraform/main.tf` (enable_autopilot = true) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup or recovery configuration found. The adservice is stateless (in-memory data), so there is no persistent data to back up. However, no formal backup strategy exists for the platform's data stores. The Memorystore Redis instance (`terraform/memorystore.tf`) does not configure backup retention or persistence. No `aws_backup_plan`, S3 versioning, or equivalent GCP backup configuration found. |
| **Gap** | No backup strategy exists for any data tier. If the adservice evolves to use persistent storage (e.g., DynamoDB for ad catalog), backups must be established from the start. The platform Redis has no configured persistence or backup. |
| **Recommendation** | Establish a backup strategy before introducing persistent storage. For DynamoDB (per preferences), enable point-in-time recovery (PITR) and on-demand backups. For EKS, consider Velero for cluster-level backup. Document recovery procedures. |
| **Evidence** | `terraform/memorystore.tf` (no backup config), absence of backup resources in Terraform, `src/adservice/src/main/java/hipstershop/AdService.java` (stateless in-memory) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GKE Autopilot in `us-central1` region supports multi-zone scheduling. However, the adservice Deployment specifies no replica count (defaults to 1) and no pod disruption budget. No topology spread constraints are defined. The Memorystore Redis does not show multi-zone configuration. The GKE cluster does not specify multi-zone in `ip_allocation_policy`. |
| **Gap** | A single-replica deployment means any pod failure results in downtime until rescheduling. No explicit multi-AZ pod distribution ensures fault isolation. No PodDisruptionBudget protects against voluntary disruptions. |
| **Recommendation** | Set replica count ≥ 2 with `topologySpreadConstraints` for zone distribution. Add a PodDisruptionBudget (`minAvailable: 1`). On EKS (per preferences), deploy across multiple AZs with managed node groups in different subnets. |
| **Evidence** | `kubernetes-manifests/adservice.yaml` (no replicas specified, no PDB), `terraform/main.tf` (GKE Autopilot, us-central1) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Terraform provisions the GKE cluster (`terraform/main.tf`) and optional Memorystore Redis (`terraform/memorystore.tf`). Variables, outputs, and provider configs are defined (`variables.tf`, `providers.tf`). Kubernetes manifests define all 12 service deployments (`kubernetes-manifests/`). Helm chart provides templated deployment with configurable features (`helm-chart/`). Kustomize provides base + 15 components for configuration layering (`kustomize/`). Skaffold orchestrates builds and deployments (`skaffold.yaml`). |
| **Gap** | Terraform covers only GKE cluster and Redis — not networking, IAM, monitoring, or security infrastructure. The `null_resource` with `kubectl apply` in `main.tf` is a pattern that bypasses Terraform state management. CI/CD infrastructure (GitHub Actions runners, Cloud Build) is not managed via IaC. |
| **Recommendation** | Expand Terraform (per `prefer: ["terraform"]`) to cover networking (VPC), IAM, monitoring, and security infrastructure. Replace `null_resource` kubectl commands with Terraform Kubernetes provider or Helm provider. When migrating to AWS, define EKS, VPC, IAM roles, and supporting services in Terraform modules. |
| **Evidence** | `terraform/main.tf`, `terraform/memorystore.tf`, `terraform/variables.tf`, `kubernetes-manifests/adservice.yaml`, `helm-chart/`, `kustomize/kustomization.yaml`, `skaffold.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions workflows provide CI automation: `ci-pr.yaml` (PR pipeline with code tests + deployment tests + smoke tests) and `ci-main.yaml` (main branch pipeline). Separate CI workflows exist for Helm chart validation, Terraform validation, Kustomize build, and Kubevious manifest validation. Cloud Build (`cloudbuild.yaml`) provides deployment via Skaffold. The pipeline includes: code tests (Go, C#), image builds, GKE deployment, pod readiness wait, and smoke tests (loadgenerator error count). |
| **Gap** | No Java/adservice-specific tests in the CI pipeline — only Go and C# services have unit tests. No automated rollback on deployment failure. No security scanning stage. Smoke tests are basic (error count > 0 check). No canary or staged deployment. Deployment uses `skaffold run` (direct replace). |
| **Recommendation** | Add Java unit tests for adservice in CI pipeline. Implement automated rollback (e.g., Argo Rollouts or Flux with GitOps per `prefer: ["gitops"]`). Add SAST and dependency scanning stages. Adopt GitOps-based deployment (Flux or ArgoCD per `prefer: ["gitops"]`) to replace `skaffold run` direct deployments. |
| **Evidence** | `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `cloudbuild.yaml`, `skaffold.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/workflows/terraform-validate-ci.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The adservice is written in Java 21 (`build.gradle`: `sourceCompatibility = JavaVersion.VERSION_21`). Java has one of the most mature cloud-native ecosystems with frameworks like Spring Boot, Quarkus, and Micronaut. The service uses gRPC 1.79.0 (`grpcVersion = "1.79.0"`), Protocol Buffers 4.34.0, and Log4j 2.25.3 — all current, well-maintained libraries. The eclipse-temurin JDK/JRE images in the Dockerfile are official, well-supported base images. |
| **Gap** | None — Java 21 is a modern LTS version with excellent cloud-native support, containerization tooling, and GraalVM native-image capability for future optimization. |
| **Recommendation** | Consider GraalVM native image compilation for faster startup times in Kubernetes (reduces cold-start from ~5s to <1s). This would improve pod scaling responsiveness. |
| **Evidence** | `src/adservice/build.gradle` (JavaVersion.VERSION_21, gRPC 1.79.0), `src/adservice/Dockerfile` (eclipse-temurin:24-jdk, eclipse-temurin:25-jre-alpine) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The adservice is one of 12 independently deployable microservices in the Online Boutique platform. Each service has its own: Dockerfile, Kubernetes Deployment, Helm template, Skaffold build artifact, and source directory. The `demo.proto` defines clear service boundaries with distinct gRPC service definitions (AdService, CartService, CheckoutService, CurrencyService, EmailService, PaymentService, ProductCatalogService, RecommendationService, ShippingService). Each service owns its own data (adservice: in-memory ads, cartservice: Redis). No shared database, no circular dependencies, clear interfaces via protobuf contracts. |
| **Gap** | None — this is a well-structured microservices architecture with clear service boundaries, independent deployability, and service-specific data ownership. |
| **Recommendation** | Maintain the microservices architecture. When migrating to AWS/EKS, each service can be independently migrated, scaled, and evolved. Consider adding service mesh (App Mesh or Istio on EKS) for cross-cutting concerns. |
| **Evidence** | `src/main/proto/demo.proto` (12 service definitions), `skaffold.yaml` (12 build artifacts), `kubernetes-manifests/adservice.yaml` (independent Deployment), `helm-chart/templates/` (per-service templates) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous gRPC. The `demo.proto` defines only unary RPCs — no streaming RPCs, no message queues, no event-driven patterns. The adservice's `getAds` RPC is a blocking request-response call. `AdServiceClient.java` uses `AdServiceGrpc.newBlockingStub(channel)` for synchronous invocation. No imports of messaging libraries (SQS, SNS, Kafka, RabbitMQ) in `build.gradle`. |
| **Gap** | 100% synchronous communication creates tight coupling. If the frontend's call to adservice times out, the frontend experiences degraded user experience. No event-driven patterns exist for decoupling. No pub/sub for ad impression tracking or campaign events. |
| **Recommendation** | Introduce async patterns for non-critical flows: ad impression events via Amazon SNS/SQS, campaign updates via EventBridge. The core ad serving RPC can remain synchronous (latency-sensitive), but side effects (logging impressions, updating analytics) should be async. Evaluate gRPC server-side streaming for real-time ad updates. |
| **Evidence** | `src/main/proto/demo.proto` (unary RPCs only), `src/adservice/src/main/java/hipstershop/AdServiceClient.java` (newBlockingStub), `src/adservice/build.gradle` (no messaging dependencies) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The adservice has no long-running operations — `getAds` serves ads from an in-memory `ImmutableListMultimap` in sub-millisecond time. There are no database queries, external API calls, or computations exceeding 30 seconds. The service is purpose-built for low-latency ad serving. The question of async handling for long-running operations is not currently applicable to this service's workload. |
| **Gap** | While the current workload has no long-running operations, no async job processing pattern is established. If AI-powered ad generation is added (per Move to AI pathway), inference calls to Bedrock could exceed 30 seconds and would need async handling. |
| **Recommendation** | When adding AI capabilities (Bedrock inference), implement async request-reply pattern: accept ad generation request, return a job ID, and provide a status polling endpoint. Use SQS for job queuing and Step Functions for orchestration. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (getAds reads from static in-memory map, getAdsByCategory, getRandomAds) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The protobuf package is `hipstershop` with no version suffix (not `hipstershop.v1`). The gRPC service path is `/hipstershop.AdService/GetAds` with no version component. No version headers, no changelog, no backward compatibility guarantees documented. The Helm chart AuthorizationPolicy hardcodes the path `/hipstershop.AdService/GetAds`. |
| **Gap** | Any breaking change to the AdService API (adding required fields, changing response structure) would break all consumers simultaneously. With 12 microservices sharing `demo.proto`, a single proto change propagates to all services. No independent API evolution path. |
| **Recommendation** | Adopt protobuf package versioning: rename `package hipstershop` to `package hipstershop.v1`. Use proto3's backward-compatible evolution rules (additive-only changes within a version). For breaking changes, create `hipstershop.v2.AdService` and run both versions concurrently. |
| **Evidence** | `src/main/proto/demo.proto` (package hipstershop — no version), `helm-chart/templates/adservice.yaml` (hardcoded path /hipstershop.AdService/GetAds) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes Service objects provide DNS-based service discovery. The adservice is accessible at `adservice:9555` (ClusterIP Service) within the cluster. Istio VirtualService (`istio-manifests/frontend.yaml`) provides additional routing. Pod configuration uses environment variables for the PORT (`env: PORT=9555`). The frontend discovers adservice via Kubernetes DNS, not hardcoded IPs. |
| **Gap** | Service discovery is Kubernetes-native (DNS) but no service registry or API catalog exists beyond the Kubernetes Service definitions. No centralized API catalog documents available services and their contracts. Istio service mesh features (VirtualService, traffic management) are available but not consistently enabled. |
| **Recommendation** | On EKS, leverage Kubernetes DNS for service discovery (built-in). For advanced routing and traffic management, deploy Istio on EKS or AWS App Mesh. Consider AWS Cloud Map for service discovery across EKS and non-Kubernetes workloads. Publish the proto-based API catalog as documentation. |
| **Evidence** | `kubernetes-manifests/adservice.yaml` (Service ClusterIP), `istio-manifests/frontend.yaml` (VirtualService), `helm-chart/values.yaml` (service names) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The adservice stores all ad data as hardcoded Java objects in a static `ImmutableListMultimap<String, Ad>` built by `createAdsMap()` in `AdService.java`. Ad content (redirect URLs and text) is compiled directly into the application binary. No S3, GCS, file storage, document management, or any external data persistence found. No parsing pipelines, no document extraction (Textract, Tika). |
| **Gap** | Ad data is locked inside the application binary. Any ad content change requires a code change, rebuild, and redeployment. No ability to dynamically add, remove, or update ads without a full deployment cycle. No support for rich media ads (images, videos) or document-based ad content. |
| **Recommendation** | Externalize ad data to Amazon DynamoDB (per `prefer: ["dynamodb"]`) with ad content stored as items. For rich media assets (ad images, videos), use Amazon S3. This enables dynamic ad management without code changes and supports future AI-powered ad content generation. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (createAdsMap — 7 hardcoded Ad objects, ImmutableListMultimap), absence of any storage client libraries in `build.gradle` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Ad data access is centralized through two methods in `AdService.java`: `getAdsByCategory(String category)` which queries `adsMap.get(category)`, and `getRandomAds()` which selects random ads from `adsMap.values()`. This is a centralized access pattern — all ad data flows through the static `adsMap`. However, this is a trivial in-memory map lookup, not a proper data access layer with abstraction over external persistence. |
| **Gap** | The data access pattern is centralized but tightly coupled to the in-memory implementation. No repository/DAO interface exists that could be swapped from in-memory to DynamoDB. No data contract or schema validation. If external persistence is introduced, the access pattern would need refactoring. |
| **Recommendation** | Extract an `AdRepository` interface from the current `getAdsByCategory`/`getRandomAds` methods. Implement the interface with the current in-memory map for backward compatibility, then add a DynamoDB implementation. This decouples the service logic from the storage mechanism. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (getAdsByCategory, getRandomAds, adsMap field) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The adservice does not use a database directly. The broader platform defines Redis 7.0 via `google_redis_instance` in `terraform/memorystore.tf` (`redis_version = "REDIS_7_0"`), used by cartservice. Redis 7.0 is a current, supported version (GA April 2022, actively maintained). The version is explicitly pinned in Terraform, which is good practice. No other database engines are configured. |
| **Gap** | While the Redis version is pinned and current, there is no formal EOL tracking process documented. No database lifecycle management policy. The adservice has no database to evaluate, but if one is introduced, version pinning and EOL tracking should be established from the start. |
| **Recommendation** | Establish a database engine lifecycle policy. When introducing DynamoDB (per preferences), DynamoDB is a fully managed service with no engine versioning concern. For Redis, migrate to Amazon ElastiCache with automatic minor version upgrades enabled. |
| **Evidence** | `terraform/memorystore.tf` (redis_version = "REDIS_7_0"), absence of database configuration in adservice |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found. All business logic resides in the Java application layer (`AdService.java`). The `getAds` method performs category-based lookup and random selection entirely in Java. No SQL files, no ORM configurations, no database driver imports in `build.gradle`. No migration files (Flyway, Liquibase) found. |
| **Gap** | None — the complete absence of database coupling means there are no stored procedure migration blockers. When introducing an external database, maintaining this pattern (all logic in application layer) is recommended. |
| **Recommendation** | Maintain the pattern of keeping all business logic in the application layer when introducing DynamoDB. Avoid stored procedures or DynamoDB triggers for business logic — use the application layer for ad selection, ranking, and filtering. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (all logic in Java), `src/adservice/build.gradle` (no database driver dependencies), absence of .sql files |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration found in any IaC file. Terraform `main.tf` enables `cloudtrace.googleapis.com` and `cloudprofiler.googleapis.com` APIs but these are application-level telemetry, not audit logging. No GCP Cloud Audit Logs configuration. No log file validation or immutable storage for audit logs. Application-level logging uses Log4j with JSON format to stdout (`log4j2.xml`), but this captures application events, not infrastructure audit trails. |
| **Gap** | No infrastructure audit trail exists. Cannot trace who made infrastructure changes, when APIs were called, or what resources were modified. This is a compliance gap for any production workload. |
| **Recommendation** | On AWS, enable CloudTrail in all regions with log file validation and S3 bucket with Object Lock for immutable storage. Use Terraform (per preferences) to provision CloudTrail. For application audit events, ship structured logs to CloudWatch Logs with defined retention policies. |
| **Evidence** | `terraform/main.tf` (cloudtrace, cloudprofiler APIs — not audit logging), absence of audit logging resources in Terraform, `src/adservice/src/main/resources/log4j2.xml` (application logging only) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration found in any IaC file. The Memorystore Redis instance (`terraform/memorystore.tf`) does not configure `transit_encryption_mode` or `auth_enabled`. No KMS keys defined. No encryption settings on any Kubernetes PersistentVolumes (none exist for adservice — it is stateless). The adservice stores data only in-memory, but no encryption strategy is established for future persistent storage. |
| **Gap** | No encryption-at-rest baseline exists. When persistent storage is introduced (DynamoDB, S3), encryption configuration must be established from scratch. No KMS key management pattern or policy exists. |
| **Recommendation** | On AWS, enable encryption at rest by default: DynamoDB (per preferences) uses encryption at rest by default with AWS-owned keys; upgrade to customer-managed KMS keys for sensitive data. Enable EBS encryption for EKS node volumes. Establish a KMS key policy in Terraform. |
| **Evidence** | `terraform/memorystore.tf` (no encryption config), absence of KMS resources in Terraform |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The gRPC adservice has no application-level authentication middleware. `AdServiceClient.java` connects with `usePlaintext()` — no TLS, no authentication. However, the Helm chart defines an Istio `AuthorizationPolicy` (`helm-chart/templates/adservice.yaml`) that restricts access to the `/hipstershop.AdService/GetAds` path from the frontend service principal only, using mTLS via SPIFFE identity (`cluster.local/ns/{namespace}/sa/{frontend}`). This is service-to-service auth at the mesh level, but it is disabled by default (`authorizationPolicies.create: false`). |
| **Gap** | No per-request authentication at the application level. The Istio mTLS provides transport-level service identity but is optional. Without Istio enabled, any pod in the namespace can call the adservice without authentication. No OAuth2/JWT token validation. |
| **Recommendation** | Enable Istio AuthorizationPolicies by default. When migrating to EKS, implement mTLS via Istio on EKS or App Mesh. For external-facing APIs, add JWT validation via an API Gateway authorizer. Consider adding gRPC interceptors for per-request authentication in the Java service. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdServiceClient.java` (usePlaintext()), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy — disabled by default), `helm-chart/values.yaml` (authorizationPolicies.create: false) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes ServiceAccount (`adservice`) is created for the pod (`kubernetes-manifests/adservice.yaml`). With Istio enabled, SPIFFE-based identity (`spiffe://cluster.local/ns/{namespace}/sa/adservice`) provides service-level identity for mTLS. The Helm chart supports ServiceAccount annotations for workload identity (`helm-chart/values.yaml`: `serviceAccounts.annotations`). However, no centralized IdP (Cognito, Okta, Ping) integration exists. No OIDC, SAML, or SSO configuration. |
| **Gap** | Service identity exists at the Kubernetes/Istio level but no centralized identity provider integration. The adservice cannot participate in federated identity flows. No user-level authentication (the service serves ads, not user-authenticated content). |
| **Recommendation** | On EKS, use EKS Pod Identity or IRSA (IAM Roles for Service Accounts) for fine-grained AWS IAM integration. For service-to-service auth, maintain mTLS via service mesh. If user-level auth is needed, integrate with Amazon Cognito. |
| **Evidence** | `kubernetes-manifests/adservice.yaml` (ServiceAccount), `helm-chart/values.yaml` (serviceAccounts.annotations), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy with service principal) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The adservice currently has no secrets to manage — no database credentials, no API keys, no tokens. The only environment variable is `PORT=9555` (not a secret). No AWS Secrets Manager, HashiCorp Vault, or GCP Secret Manager integration found. No hardcoded credentials detected in source code. The `helm-chart/values.yaml` contains a `cartDatabase.connectionString: "redis-cart:6379"` — not a secret (host:port only, no auth). |
| **Gap** | While no secrets are currently needed, no secrets management pattern is established. When the adservice is enhanced with AI capabilities (Bedrock API access), database connections (DynamoDB), or external integrations, a secrets management solution will be required. No `.env` files found committed to git, which is good practice. |
| **Recommendation** | Establish AWS Secrets Manager integration via Terraform before introducing secrets. Use the Kubernetes Secrets Store CSI Driver with AWS Secrets Manager provider for EKS. Enable automatic rotation for database credentials. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (PORT env var only), `kubernetes-manifests/adservice.yaml` (env: PORT=9555), `helm-chart/values.yaml` (cartDatabase.connectionString — no auth), absence of secrets management config |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Container security is well-configured: pod `securityContext` enforces `runAsNonRoot: true`, `runAsUser: 1000`, `fsGroup: 1000`. Container `securityContext` sets `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, `privileged: false`, and `capabilities.drop: [ALL]`. Base images use official eclipse-temurin with pinned SHA digests (`@sha256:...`) in the Dockerfile. Renovate (`renovate.json5`) automates dependency update PRs on a weekly schedule (earlyMondays). Optional seccomp profile support in Helm values (`seccompProfile.enable: false`). |
| **Gap** | No vulnerability scanning detected — no AWS Inspector, Snyk, Trivy, or Grype in the pipeline or configuration. Renovate updates dependencies but does not scan for known vulnerabilities. No hardened base image (CIS benchmark, Bottlerocket). Seccomp profile is disabled by default. |
| **Recommendation** | Add Trivy or Snyk container scanning to the CI pipeline. On EKS, use Bottlerocket for node OS (hardened, minimal). Enable seccomp profiles by default. Consider AWS Inspector for continuous vulnerability monitoring of container images in ECR. |
| **Evidence** | `kubernetes-manifests/adservice.yaml` (securityContext), `src/adservice/Dockerfile` (pinned SHA digests), `.github/renovate.json5` (weekly updates), `helm-chart/values.yaml` (seccompProfile.enable: false) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning found in the CI/CD pipeline. The GitHub Actions workflows (`ci-pr.yaml`, `ci-main.yaml`) run code tests and deployment smoke tests but no security scanning steps. No SonarQube, Semgrep, CodeGuru, Snyk, or Checkmarx integration. No `npm audit`, `pip-audit`, or Gradle dependency check plugin. Renovate manages dependency updates but does not scan for CVEs. No `.snyk` policy file, no `dependabot.yml`. |
| **Gap** | Vulnerabilities in Java dependencies (gRPC, Netty, Log4j, Jackson, Protobuf) could reach production undetected. No security gates prevent merging code with known vulnerabilities. The adservice is the only Java service in the platform — it lacks even the basic test coverage that Go and C# services have. |
| **Recommendation** | Add Gradle dependency-check plugin (`org.owasp.dependencycheck`) to the build. Integrate Amazon CodeGuru Reviewer or SonarQube for SAST. Add a security scanning step in GitHub Actions CI pipeline. Enable ECR image scanning when migrating to AWS. Establish a security gate that blocks PRs with critical/high findings. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (no security scanning steps), `.github/workflows/ci-main.yaml` (no security scanning steps), `src/adservice/build.gradle` (no security plugins), `.github/renovate.json5` (dependency updates, not CVE scanning) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The `log4j2.xml` configures JSON structured logging with trace context fields (`logging.googleapis.com/trace`, `logging.googleapis.com/spanId`, `logging.googleapis.com/traceSampled`) for Stackdriver integration. However, these fields are populated from MDC context (`${ctx:traceId}`, `${ctx:spanId}`) which is **never set** — the `initTracing()` and `initStats()` methods in `AdService.java` contain only TODO comments: `// TODO(arbrown) Implement OpenTelemetry tracing` and `// TODO(arbrown) Implement OpenTelemetry stats`. No OpenTelemetry SDK, X-Ray SDK, or any tracing library exists in `build.gradle` dependencies. The `grpc-census` dependency is present but the OpenCensus bridge is not configured. |
| **Gap** | No distributed tracing is implemented. Trace IDs are not propagated across gRPC calls. The log4j2 configuration is a skeleton that outputs empty trace fields. Cannot trace requests from frontend → adservice or correlate logs across service boundaries. |
| **Recommendation** | Implement OpenTelemetry Java agent or SDK. Add `opentelemetry-javaagent` to the Dockerfile as a JVM agent. On AWS, export traces to AWS X-Ray via the OpenTelemetry Collector. The existing log4j2 JSON format can be enhanced with OpenTelemetry trace context injection. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (initTracing TODO, initStats TODO), `src/adservice/src/main/resources/log4j2.xml` (trace fields in JSON layout, ctx:traceId placeholder), `src/adservice/build.gradle` (no OpenTelemetry dependency) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in any configuration file, IaC resource, or documentation. No error budget tracking. No p99/p95 latency targets defined. No CloudWatch alarms, no GCP Cloud Monitoring SLOs. The `helm-chart/values.yaml` has `googleCloudOperations.metrics: false` disabled by default. |
| **Gap** | Without SLOs, there is no way to measure whether the adservice is meeting user expectations. No formal definition of acceptable latency, availability, or error rate exists. Cannot prioritize operational improvements based on error budgets. |
| **Recommendation** | Define SLOs for the adservice: availability target (e.g., 99.9%), p99 latency target (e.g., <100ms for ad serving), error rate target (e.g., <0.1%). On AWS, use CloudWatch Service Level Objectives or implement SLO monitoring via Prometheus/Grafana on EKS. |
| **Evidence** | Absence of SLO definitions in any file, `helm-chart/values.yaml` (googleCloudOperations.metrics: false) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. No `putMetricData` or equivalent metric emission calls in the Java source code. The adservice logs `received ad request (context_words=...)` but does not publish metrics on: ads served per category, ad impressions, click-through rates, empty response rates, or context key distribution. The `google-cloud-operations` Kustomize component is commented out in `kustomize/kustomization.yaml`. The OpenTelemetry Collector is disabled (`opentelemetryCollector.create: false`). |
| **Gap** | No business outcome visibility. Cannot measure ad serving effectiveness, identify popular categories, or detect declining ad engagement. Only infrastructure-level signals (pod CPU/memory via Kubernetes metrics) are available. |
| **Recommendation** | Publish custom metrics via OpenTelemetry SDK: ads_served_total (by category), ads_served_empty_total (no ads found), ad_request_latency_ms, context_keys_distribution. On AWS, export to CloudWatch Metrics via OpenTelemetry Collector with AWS CloudWatch exporter. |
| **Evidence** | `src/adservice/src/main/java/hipstershop/AdService.java` (logger.info only, no metric emission), `kustomize/kustomization.yaml` (google-cloud-operations commented out), `helm-chart/values.yaml` (opentelemetryCollector.create: false) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configuration found. No CloudWatch alarms, no GCP Alert Policies, no PagerDuty/OpsGenie integration. No Prometheus AlertManager rules. No alerting thresholds defined in any IaC or configuration file. The `helm-chart/values.yaml` disables all observability features by default. |
| **Gap** | No automated alerting exists. If the adservice starts returning errors, experiences increased latency, or goes down entirely, no one is notified. Incident detection is entirely reactive and manual. |
| **Recommendation** | On EKS with CloudWatch: create alarms for pod restart count, error rate (4xx/5xx on gRPC), p99 latency, and memory utilization. Enable CloudWatch anomaly detection on error rate and latency metrics. Integrate with SNS → PagerDuty/OpsGenie for on-call notification. |
| **Evidence** | Absence of alerting resources in Terraform, absence of alerting configuration in Helm chart, `helm-chart/values.yaml` (all observability disabled) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployments use `skaffold run` which applies Kubernetes manifests directly via `kubectl apply`. The Kubernetes Deployment uses the default `RollingUpdate` strategy with no explicit configuration for `maxSurge` or `maxUnavailable`. No canary deployment, no blue/green deployment, no traffic shifting. Cloud Build (`cloudbuild.yaml`) runs `skaffold run` with no staged rollout. The CI pipeline (`ci-pr.yaml`) does deploy to a separate namespace for PR testing, which provides pre-production validation. |
| **Gap** | No staged rollout to production. Every deployment is a full replace. If a bad version is deployed, all users are affected simultaneously. No automated rollback on health check failure. Rolling update with 1 replica means brief downtime during deployments. |
| **Recommendation** | Adopt GitOps-based deployment (per `prefer: ["gitops"]`) using Flux or ArgoCD on EKS. Implement canary deployments with Argo Rollouts or Flux Flagger. Define automated rollback on gRPC health check failure. Increase replica count to ≥ 2 for zero-downtime rolling updates. |
| **Evidence** | `cloudbuild.yaml` (skaffold run), `skaffold.yaml` (kubectl deploy), `.github/workflows/ci-pr.yaml` (skaffold run per-PR namespace), `kubernetes-manifests/adservice.yaml` (no deployment strategy specified) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline includes deployment-level smoke tests: after deploying all services to a PR namespace on GKE, the pipeline waits for all pods to be ready, then runs a loadgenerator that sends traffic and checks for zero errors (`ERROR_COUNT > 0` triggers failure). This validates end-to-end system health. However: (1) No Java/adservice-specific unit or integration tests exist — only Go (`shippingservice`, `productcatalogservice`) and C# (`cartservice`) services have unit tests. (2) Smoke tests are binary (any error = failure) with no assertion on specific ad-serving behavior. (3) No gRPC contract tests or API tests for the AdService. |
| **Gap** | The adservice Java code has zero automated tests. No unit tests for `getAdsByCategory()`, `getRandomAds()`, or `createAdsMap()`. No integration tests verifying gRPC request/response behavior. The smoke test validates the whole system, not adservice specifically. |
| **Recommendation** | Add JUnit 5 tests for adservice: unit tests for ad selection logic, gRPC integration tests using `grpc-testing` library. Add gRPC contract tests that validate AdRequest/AdResponse behavior. Include Java tests in the CI pipeline alongside existing Go and C# tests. |
| **Evidence** | `.github/workflows/ci-pr.yaml` (Go and C# tests only, smoke tests), `.github/workflows/ci-main.yaml` (same), absence of test files in `src/adservice/src/test/`, `src/adservice/build.gradle` (no test dependencies) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automated incident response workflows, or self-healing patterns found. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files (markdown, YAML, JSON) in the repository. No auto-restart beyond Kubernetes liveness probe. The liveness probe (`grpc: port: 9555`, `periodSeconds: 15`) restarts the pod on health check failure — this is basic self-healing but not an incident response strategy. |
| **Gap** | Incident response is entirely ad hoc. If the adservice experiences issues beyond pod-level restarts (e.g., upstream dependency failure, data corruption, capacity exhaustion), there are no automated remediation steps. No escalation path defined. |
| **Recommendation** | Create runbooks for common adservice incidents (pod crash loop, high latency, gRPC errors). On AWS, implement Systems Manager Automation documents for common remediation actions. Consider Step Functions for incident response workflows. Start with basic markdown runbooks, then evolve to automated SSM Runbooks. |
| **Evidence** | Absence of runbook files, `kubernetes-manifests/adservice.yaml` (livenessProbe — basic self-healing only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The `CODEOWNERS` file (`.github/CODEOWNERS`) assigns `@GoogleCloudPlatform/devrel-flagship-app-maintainers @yoshi-approver` as owners for the entire repository (`*`). No per-service observability ownership. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution. No service-specific CODEOWNERS entries for monitoring or observability configuration. |
| **Gap** | Observability ownership is undefined at the service level. No team is explicitly responsible for adservice monitoring, alerting, or SLO compliance. The repo-wide CODEOWNERS covers code changes but not operational responsibility. |
| **Recommendation** | Define per-service CODEOWNERS entries for observability assets. Create per-service CloudWatch dashboards on EKS. Assign named owners for each service's SLOs and alarms. Tag observability resources with team ownership. |
| **Evidence** | `.github/CODEOWNERS` (repo-wide ownership only: `* @GoogleCloudPlatform/devrel-flagship-app-maintainers`), absence of per-service dashboards or alarm definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes labels are consistently applied: `app: adservice` on Deployment, Service, and pod template (`kubernetes-manifests/adservice.yaml`). Helm chart uses templated labels (`app: {{ .Values.adService.name }}`). However, no AWS resource tagging, no GCP labels on infrastructure resources, no tag enforcement policies. No `default_tags` in Terraform provider. No cost allocation tags. The Terraform resources (`google_container_cluster`, `google_redis_instance`) have no labels configured. |
| **Gap** | Kubernetes labels are present but cloud infrastructure resources have no tags. Cannot attribute costs, identify ownership, or enforce compliance at the infrastructure level. No tag enforcement mechanism. |
| **Recommendation** | Add `default_tags` to the Terraform AWS provider when migrating to AWS. Tag all resources with: `environment`, `service`, `team`, `cost-center`. Enable AWS Config required-tags rule for enforcement. Use Terraform `merge()` for consistent tagging across all resources. |
| **Evidence** | `kubernetes-manifests/adservice.yaml` (labels: app: adservice), `helm-chart/templates/adservice.yaml` (templated labels), `terraform/main.tf` (no labels on google_container_cluster), `terraform/memorystore.tf` (no labels on google_redis_instance) |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

Only the Move to AI pathway was triggered. For general cloud architecture training, refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| **src/adservice/** | | |
| `src/adservice/build.gradle` | APP-Q1, APP-Q3, OPS-Q1, SEC-Q7 | Java 21, gRPC 1.79.0 dependencies; no OpenTelemetry, no security plugins, no messaging deps |
| `src/adservice/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage build, eclipse-temurin base with pinned SHA digests |
| `src/adservice/README.md` | Quick Agent Wins | Build instructions, documentation corpus for RAG agent |
| `src/adservice/src/main/java/hipstershop/AdService.java` | INF-Q2, INF-Q3, INF-Q8, APP-Q2, APP-Q3, APP-Q4, DATA-Q1, DATA-Q2, DATA-Q4, OPS-Q1, OPS-Q3, SEC-Q5 | Main service class; createAdsMap, getAds, initTracing TODO, initStats TODO |
| `src/adservice/src/main/java/hipstershop/AdServiceClient.java` | APP-Q3, SEC-Q3 | Blocking gRPC stub, usePlaintext() connection |
| `src/adservice/src/main/proto/demo.proto` | APP-Q2, APP-Q3, APP-Q5, INF-Q4, Quick Agent Wins | Protobuf definitions for all 12 services, unversioned package |
| `src/adservice/src/main/resources/log4j2.xml` | OPS-Q1, SEC-Q1 | JSON structured logging with trace context placeholders |
| **terraform/** | | |
| `terraform/main.tf` | INF-Q1, INF-Q7, INF-Q9, INF-Q10, SEC-Q1 | GKE Autopilot cluster, GCP API enablement, null_resource kubectl |
| `terraform/memorystore.tf` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q2 | Redis 7.0 Memorystore, no backup, no encryption |
| `terraform/variables.tf` | INF-Q10 | Variable definitions for GKE cluster |
| **kubernetes-manifests/** | | |
| `kubernetes-manifests/adservice.yaml` | INF-Q1, INF-Q5, INF-Q7, INF-Q9, APP-Q2, APP-Q6, OPS-Q5, OPS-Q7, OPS-Q9, SEC-Q4, SEC-Q5, SEC-Q6 | Deployment, Service, ServiceAccount; security context; resource requests |
| **helm-chart/** | | |
| `helm-chart/templates/adservice.yaml` | INF-Q1, INF-Q5, APP-Q5, SEC-Q3, SEC-Q4, SEC-Q6 | Templated deployment; NetworkPolicy, AuthorizationPolicy, Sidecar |
| `helm-chart/values.yaml` | INF-Q2, INF-Q5, INF-Q7, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q9, SEC-Q3, SEC-Q5, SEC-Q6 | Default values; observability disabled; security features disabled by default |
| `helm-chart/Chart.yaml` | APP-Q2 | Helm chart metadata, version 0.10.5 |
| **istio-manifests/** | | |
| `istio-manifests/frontend-gateway.yaml` | INF-Q6 | Istio Gateway and VirtualService for frontend ingress |
| `istio-manifests/frontend.yaml` | APP-Q6 | VirtualService for frontend routing |
| `istio-manifests/allow-egress-googleapis.yaml` | INF-Q5 | ServiceEntry for egress to Google APIs |
| **kustomize/** | | |
| `kustomize/kustomization.yaml` | INF-Q10, OPS-Q3 | Kustomize base + components (observability commented out) |
| **.github/** | | |
| `.github/workflows/ci-pr.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | PR CI pipeline: code tests, deployment tests, smoke tests |
| `.github/workflows/ci-main.yaml` | INF-Q11, OPS-Q6, SEC-Q7 | Main branch CI pipeline |
| `.github/renovate.json5` | SEC-Q6 | Dependency update automation (weekly) |
| `.github/CODEOWNERS` | OPS-Q8 | Repo-wide ownership only |
| **Root files** | | |
| `cloudbuild.yaml` | INF-Q11, OPS-Q5 | Cloud Build deployment via Skaffold |
| `skaffold.yaml` | INF-Q11, OPS-Q5, Quick Agent Wins | Build orchestration for all 12 services |
