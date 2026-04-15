# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | currencyservice |
| **Date** | 2026-04-15 |
| **Repo Type** | `application` |
| **Priority** | P1 |
| **Tags** | cpp, grpc, utility |
| **Context** | C++ gRPC service converting between currencies. (Note: Actual implementation is JavaScript/Node.js, not C++. The context description is inaccurate.) |
| **Overall Score** | **1.67 / 4.0** |

> **Note:** The `context` field states "C++ gRPC service" but the repository contains JavaScript/Node.js source code (`server.js`, `client.js`, `package.json`). Findings and recommendations reflect the actual technology stack.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.09 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.25 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.67 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found — zero infrastructure-as-code coverage | Blocks repeatable deployments, disaster recovery, and environment parity; triggers Modern DevOps pathway |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline definitions found — all deployments are manual | Blocks automated testing, safe deployments, and rapid iteration; triggers Modern DevOps pathway |
| 3 | SEC-Q3: API Authentication | 1 | gRPC server uses `createInsecure()` — no TLS, no authentication | All endpoints exposed without authentication or encryption; critical security gap |
| 4 | OPS-Q6: Integration Testing | 1 | No test suite exists — `scripts.test` echoes "Error: no test specified" | No regression safety net; any change risks breaking currency conversion for all downstream services |
| 5 | INF-Q5: Network Security | 1 | No VPC, subnet, security group, or network policy definitions | Service has no defined network boundary; cannot limit blast radius of security incidents |

---

## Quick Agent Wins

### Observability Agent

- **Prerequisite:** OPS-Q1 ≥ 2 — OpenTelemetry distributed tracing is instrumented with gRPC auto-instrumentation (`@opentelemetry/instrumentation-grpc`, `@opentelemetry/sdk-node`, `@opentelemetry/exporter-otlp-grpc` in `package.json`). Tracing is conditionally enabled via `ENABLE_TRACING` environment variable and exports to an OTLP-compatible collector.
- **What it enables:** An observability agent that queries distributed traces, correlates gRPC call failures across the hipstershop service mesh, and suggests root causes when currency conversion errors spike. The agent can identify slow conversion paths and trace latency propagation from CurrencyService to downstream consumers (CheckoutService, Frontend).
- **Additional steps:** Deploy a tracing backend (e.g., AWS X-Ray via ADOT collector or Grafana Tempo on EKS per preferences). Ensure `ENABLE_TRACING=1` is set in all environments. Add structured error codes to conversion failures for better agent correlation.
- **Effort:** Medium — tracing instrumentation exists but requires a collector endpoint, tracing backend, and agent configuration to operationalize.

> **Note:** Other Quick Agent Win prerequisites are not met:
> - **API-aware agent:** APP-Q5 = 1 (no API versioning). Proto file defines structured messages but no OpenAPI spec exists for REST-based agent tool discovery.
> - **DevOps agent:** INF-Q11 = 1 (no CI/CD pipeline to orchestrate).
> - **RAG knowledge agent:** No documentation beyond code comments and proto definitions.
> - **Workflow agent:** INF-Q3 = 1 (no workflow orchestration).
> - **Data query agent:** DATA-Q2 = 3 (meets threshold), but the data is a static JSON file with 33 currency rates — too simple for a natural language query agent to add value.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — service is already an independently deployable microservice with well-defined boundary |
| 2 | Move to Containers | Not Triggered | — | — | Dockerfile exists (`Dockerfile`) — containerization already in place; contextual guard prevents triggering |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or commercial DB; no database engine to migrate |
| 4 | Move to Managed Databases | Not Triggered | — | — | No database exists — service reads static JSON file; no self-managed database to migrate |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads — simple currency conversion with no ETL, streaming, or analytics; contextual guard prevents triggering |
| 6 | Move to Modern DevOps | **Triggered** | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 1 (no CI/CD), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 1 (no integration tests) |
| 7 | Move to AI | **Triggered** | Medium | Medium | No AI/agent frameworks detected — no Bedrock SDK, LangChain, Strands, or vector DB infrastructure |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 1):** No infrastructure-as-code files found anywhere in the repository. No Terraform (`.tf`), CloudFormation, CDK, Helm charts, or Kustomize manifests. The Dockerfile is the only deployment-related artifact. All infrastructure supporting this service is presumed to be manually created (ClickOps) or managed outside this repository.
- **CI/CD Automation (INF-Q11 = 1):** No CI/CD pipeline definitions found. No `.github/workflows/`, no `Jenkinsfile`, no `buildspec.yml`, no CodePipeline definitions. Deployments are manual.
- **Deployment Strategy (OPS-Q5 = 1):** No canary, blue/green, or rolling deployment strategy. With no CI/CD pipeline, all releases go directly to production manually.
- **Integration Testing (OPS-Q6 = 1):** No automated tests exist. `package.json` defines `"test": "echo \"Error: no test specified\" && exit 1"`. No unit tests, integration tests, or contract tests.

#### Recommendations

Per user preferences (prefer: Terraform, GitOps, EKS; avoid: serverless, manual-deployments):

1. **Define Infrastructure with Terraform:**
   - Create Terraform modules for the EKS cluster, VPC, security groups, and IAM roles that host this service.
   - Define the CurrencyService Kubernetes deployment, service, and ingress as Terraform-managed Kubernetes resources or as Helm chart references.
   - Store Terraform state in S3 with DynamoDB state locking.
   - Estimated effort: 2–4 weeks for initial Terraform module creation.

2. **Adopt GitOps with ArgoCD or Flux:**
   - Deploy ArgoCD or Flux CD on EKS to manage Kubernetes manifests declaratively from Git.
   - Create Kubernetes manifests (Deployment, Service, HPA) for CurrencyService.
   - Configure ArgoCD Application pointing to the CurrencyService manifest directory.
   - All deployments triggered by Git commits — no manual `kubectl apply`.
   - Estimated effort: 1–2 weeks for GitOps setup.

3. **Build CI/CD Pipeline:**
   - Create a GitHub Actions workflow (or AWS CodePipeline + CodeBuild) with stages:
     - **Lint & Test:** Run unit and integration tests (once created).
     - **Build:** `docker build` the CurrencyService image.
     - **Scan:** Trivy or Snyk container image scanning.
     - **Push:** Push to Amazon ECR.
     - **Deploy:** Update Kubernetes manifests in Git (triggering GitOps sync).
   - Estimated effort: 1–2 weeks for pipeline creation.

4. **Add Testing:**
   - Add unit tests for `_carry()` and `convert()` functions using Jest or Mocha.
   - Add gRPC integration tests using `@grpc/grpc-js` test client (similar to existing `client.js`).
   - Add contract tests to validate proto compatibility.
   - Estimated effort: 1–2 weeks for initial test suite.

#### Representative AWS Services
- **Amazon EKS** — Managed Kubernetes for container orchestration (preferred)
- **Amazon ECR** — Container image registry
- **AWS CodeBuild** — Build and test automation
- **AWS CodePipeline** — Pipeline orchestration (alternative to GitHub Actions)
- **Terraform** — Infrastructure as Code (preferred)
- **ArgoCD on EKS** — GitOps deployment (preferred)

#### AWS Prescriptive Guidance
- [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-modernization-devops/welcome.html)
- [GitOps model for Amazon EKS](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/set-up-a-gitops-pipeline-with-argocd.html)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

No AI or agent framework usage detected in the repository:
- **AI/Agent Frameworks:** No imports of Amazon Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK in `package.json` or source files.
- **Vector Database:** No OpenSearch, Pinecone, pgvector, Weaviate, or Qdrant infrastructure.
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns.
- **Agent Evaluation:** No Ragas, DeepEval, or custom eval harnesses.

#### Potential AI Use Cases

Based on the CurrencyService domain (currency conversion for an e-commerce platform):

1. **Dynamic Exchange Rate Agent:** Replace the static `currency_conversion.json` file with an Amazon Bedrock-powered agent that fetches real-time exchange rates, detects anomalous rate movements, and provides rate forecasts. Store rate history in DynamoDB (preferred) for trend analysis.

2. **Fraud Detection Enhancement:** Integrate Bedrock for real-time analysis of currency conversion patterns to detect unusual conversion volumes or suspicious currency pairs that might indicate fraud.

3. **Operational AI:** Use Amazon Bedrock to analyze OpenTelemetry traces (already instrumented) and automatically generate incident summaries, identify conversion error patterns, and suggest root causes.

#### Foundation Requirements Before AI Integration

The following gaps must be addressed before AI integration is viable:
- **CI/CD Pipeline** (INF-Q11 = 1): Needed to safely deploy AI-enhanced versions.
- **IaC** (INF-Q10 = 1): Needed to provision Bedrock endpoints, DynamoDB tables, and IAM roles.
- **Testing** (OPS-Q6 = 1): Needed to validate AI-augmented conversion accuracy.
- **Authentication** (SEC-Q3 = 1): Needed to secure Bedrock API calls and protect agent endpoints.

#### Recommended Approach

1. Address Modern DevOps pathway first (IaC + CI/CD foundation).
2. Start with a single AI use case: replace static exchange rates with a DynamoDB-backed rate service, using Bedrock for anomaly detection on rate changes.
3. Instrument with evaluation metrics to measure AI accuracy.

#### Representative AWS Services
- **Amazon Bedrock** — Foundation model access (preferred)
- **Amazon DynamoDB** — Rate history storage (preferred)
- **Amazon Bedrock AgentCore** — Agent runtime
- **Amazon Q** — Developer productivity

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | A multi-stage `Dockerfile` is present using `node:20.20.1-alpine` as the builder and `alpine:3.23.3` as the runtime base. The image is pinned by SHA256 digest, which is a best practice. The application runs as `node server.js` inside the container. However, no IaC defines where this container runs — no Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources exist in the repository. The service is containerized but the hosting model (ECS, EKS, EC2, Fargate) is undefined within this repo. |
| **Gap** | No managed compute infrastructure defined. The Dockerfile exists but there's no IaC to provision EKS, ECS, or any compute platform. The actual deployment target is unknown from this repository alone. |
| **Recommendation** | Define Terraform modules for an EKS cluster (preferred per user preferences) with a Kubernetes Deployment for the CurrencyService. Create a Helm chart or Kustomize overlay for the service's Kubernetes manifests (Deployment, Service, HPA). Avoid serverless (Lambda) per user preferences. |
| **Evidence** | `Dockerfile` (multi-stage build with node:20-alpine), absence of any `.tf`, `.cfn`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database artifacts found. The CurrencyService reads exchange rates from a static JSON file (`data/currency_conversion.json`) bundled within the container image. There are no `aws_rds_*`, `aws_dynamodb_*`, or database connection strings in any source file. The service has no persistent data store — currency rates are hardcoded. |
| **Gap** | Exchange rates are static and embedded in the application. No managed database or external data source provides dynamic rate updates. While this is a simplistic data model, it means rate changes require a new container build and deployment. |
| **Recommendation** | Consider migrating exchange rate data to Amazon DynamoDB (preferred per user preferences) for dynamic rate updates without redeployment. DynamoDB's on-demand capacity mode would suit the low-volume read pattern of this service. Define the DynamoDB table in Terraform. |
| **Evidence** | `data/currency_conversion.json` (33 static exchange rates), `server.js` line `require('./data/currency_conversion.json')`, absence of any database dependencies in `package.json` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration found. The CurrencyService is a simple request/response gRPC service with two RPC methods: `getSupportedCurrencies` and `convert`. Both are synchronous, stateless operations that complete in single function calls. No Step Functions, Temporal, or workflow YAML definitions exist. |
| **Gap** | No workflow orchestration is present. Given the simplicity of this service (stateless currency conversion), dedicated workflow orchestration may not be necessary for the current scope. |
| **Recommendation** | Workflow orchestration is not a high priority for this stateless utility service. If the service evolves to include rate refresh workflows, batch conversion jobs, or multi-step validation, consider AWS Step Functions for orchestration. Define workflows in Terraform. |
| **Evidence** | `server.js` (two simple RPC handlers), absence of `aws_sfn_*` in IaC, absence of Temporal SDK in `package.json` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure found. All communication is synchronous gRPC request/response. The `proto/demo.proto` defines `GetSupportedCurrencies` and `Convert` as unary RPCs (not streaming). No SQS, SNS, EventBridge, Kinesis, or Kafka references exist in the codebase or dependencies. |
| **Gap** | All communication is synchronous. There's no event-driven pattern for rate change notifications to downstream services or for decoupled communication. |
| **Recommendation** | Consider publishing rate change events via Amazon SNS or EventBridge when exchange rates are updated (once rates are externalized to DynamoDB). This would enable downstream services (e.g., ProductCatalogService, CheckoutService) to react to rate changes asynchronously. Define messaging resources in Terraform. |
| **Evidence** | `proto/demo.proto` (unary RPCs only), `server.js` (synchronous handlers), absence of messaging SDK imports in `package.json` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network policy definitions found. The gRPC server binds to `[::]:${PORT}` with no network restrictions. No Terraform `aws_vpc`, `aws_subnet`, `aws_security_group` resources, and no Kubernetes NetworkPolicy manifests exist in the repository. |
| **Gap** | No network security boundary is defined. The service has no network segmentation, no ingress/egress rules, and no blast radius containment. |
| **Recommendation** | Define Terraform VPC modules with private subnets for EKS worker nodes. Create Kubernetes NetworkPolicies to restrict CurrencyService ingress to only the services that call it (CheckoutService, Frontend). Implement security groups on EKS node groups limiting traffic to the cluster VPC. |
| **Evidence** | `server.js` line `server.bindAsync('[::]:${PORT}', ...)`, absence of any network infrastructure definitions |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront entry point found. The gRPC server exposes itself directly on `PORT` with no intermediary. The `Dockerfile` exposes port 7000 directly. No `aws_api_gateway_*`, `aws_apigatewayv2_*`, or `aws_lb_*` resources exist. |
| **Gap** | Service is directly exposed with no gateway providing throttling, authentication, or request validation. In a Kubernetes context, there's no Ingress controller or service mesh routing defined. |
| **Recommendation** | Deploy an EKS-based ingress controller (e.g., AWS ALB Ingress Controller) or adopt a gRPC-aware service mesh (Istio, AWS App Mesh) on EKS to provide traffic management, mTLS, and rate limiting for gRPC traffic. Define in Terraform. |
| **Evidence** | `server.js` (direct gRPC bind), `Dockerfile` (EXPOSE 7000), absence of gateway/LB definitions |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*`, `aws_appautoscaling_*`, HPA (Horizontal Pod Autoscaler), or scaling policies exist. No Kubernetes resource requests/limits are defined (no Kubernetes manifests in this repo). |
| **Gap** | Service cannot automatically scale in response to traffic changes. During high-traffic periods (e.g., checkout surges), the service may become a bottleneck. |
| **Recommendation** | Create a Kubernetes HPA for the CurrencyService based on gRPC request rate or CPU utilization. Define resource requests and limits in Kubernetes manifests. Manage the HPA and resource definitions in Terraform or Helm. Target 2–5 replicas for normal traffic with auto-scaling to 10+ during peaks. |
| **Evidence** | Absence of any scaling configuration, absence of Kubernetes manifests |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup or recovery configuration found. The service has no persistent data stores — exchange rates are embedded in the container image as `data/currency_conversion.json`. No `aws_backup_plan`, no RDS `backup_retention_period`, no DynamoDB PITR configuration. |
| **Gap** | While the current service is stateless (no persistent data), there is no disaster recovery plan for the service itself. If the container image registry is unavailable, the service cannot be redeployed. |
| **Recommendation** | Once exchange rates are externalized to DynamoDB (per INF-Q2 recommendation), enable DynamoDB Point-in-Time Recovery (PITR) and automated backups via Terraform. Replicate container images to a secondary ECR repository for DR. |
| **Evidence** | `data/currency_conversion.json` (static data bundled in image), absence of any backup configuration |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ or high availability configuration found. No EKS node groups spanning AZs, no RDS `multi_az = true`, no cross-AZ load balancing. The repository defines no infrastructure topology. |
| **Gap** | The service has no defined HA posture. If deployed to a single AZ, an AZ failure takes down currency conversion for the entire e-commerce platform, blocking checkout. |
| **Recommendation** | Deploy EKS node groups across 2+ AZs. Use Kubernetes pod anti-affinity rules to spread CurrencyService replicas across AZs. Define this in Terraform. Given this is a P1 service, HA is critical — currency conversion failure blocks all purchases. |
| **Evidence** | Absence of any HA/multi-AZ configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform files (`.tf`, `.tfvars`), no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize manifests found. The only deployment artifact is the `Dockerfile`. All supporting infrastructure (compute, networking, IAM, monitoring) is either undefined or managed outside this repository. |
| **Gap** | Complete absence of infrastructure-as-code. Infrastructure changes are manual, non-reproducible, and non-auditable. This is the most critical gap for modernization — without IaC, no other pathway can be implemented safely. |
| **Recommendation** | Adopt Terraform (preferred per user preferences) to define all infrastructure: EKS cluster, VPC, security groups, IAM roles, ECR repository, and Kubernetes manifests. Use a Terraform module structure with separate modules for networking, compute, and application. Store state in S3 with DynamoDB locking. Adopt GitOps (preferred) with ArgoCD for Kubernetes resource management. |
| **Evidence** | Absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline definitions found. No `.github/workflows/` directory, no `Jenkinsfile`, no `buildspec.yml`, no CodePipeline definitions. The `package.json` test script is a placeholder: `"test": "echo \"Error: no test specified\" && exit 1"`. Deployments are presumed to be entirely manual. |
| **Gap** | Complete absence of CI/CD automation. Builds, tests, and deployments are all manual. This blocks automated quality gates, security scanning, and consistent release processes. |
| **Recommendation** | Create a CI/CD pipeline (GitHub Actions or AWS CodePipeline + CodeBuild) with stages: lint → test → build → scan → push → deploy. Adopt GitOps (preferred) — the deploy stage updates Kubernetes manifests in a Git repo, triggering ArgoCD sync. Avoid manual deployments (per user preferences). |
| **Evidence** | `package.json` (`"test": "echo \"Error: no test specified\" && exit 1"`), absence of `.github/workflows/`, `Jenkinsfile`, `buildspec.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The service is implemented in JavaScript (Node.js). `package.json` declares the project as `grpc-currency-service` version `0.1.0`. Dependencies include modern, well-maintained packages: `@grpc/grpc-js` (1.14.3), `@grpc/proto-loader` (0.8.0), `@opentelemetry/*` suite, and `pino` (10.3.1) for structured logging. Node.js has a mature cloud-native ecosystem with extensive AWS SDK support, container optimization, and Kubernetes-native tooling. |
| **Gap** | No significant gap. JavaScript/Node.js is a mature choice for cloud-native microservices. |
| **Recommendation** | Continue with Node.js. Consider upgrading the Node.js runtime in the Dockerfile to LTS versions as they become available. The current `node:20.20.1-alpine` is on the active LTS track. |
| **Evidence** | `package.json` (Node.js project), `server.js` (JavaScript source), `Dockerfile` (node:20-alpine runtime) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CurrencyService is an independently deployable microservice within the larger `microservices-demo` (hipstershop) architecture. The `proto/demo.proto` file defines 9 distinct services (CartService, RecommendationService, ProductCatalogService, ShippingService, CurrencyService, PaymentService, EmailService, CheckoutService, AdService), confirming a microservices architecture. This repository contains only the CurrencyService, with a clear boundary: it owns two RPC methods (`GetSupportedCurrencies`, `Convert`), its own data (`currency_conversion.json`), and its own Dockerfile. No circular dependencies with other services. |
| **Gap** | While the service has well-defined boundaries, there is a shared proto file (`demo.proto`) that contains definitions for all 9 services. Changes to any service's proto may affect the shared file. The `genproto.sh` script copies protos from a shared `../../protos/` directory, indicating tight coupling at the interface definition level. |
| **Recommendation** | Consider splitting `demo.proto` into per-service proto files (e.g., `currency.proto`) to reduce coupling. Each service should own its proto definition independently. Use proto package versioning for backward compatibility. |
| **Evidence** | `proto/demo.proto` (9 services defined in single file), `server.js` (only CurrencyService implemented), `genproto.sh` (copies from shared proto directory), `Dockerfile` (independent build) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All communication is synchronous gRPC request/response. Both RPC methods in `proto/demo.proto` for CurrencyService are unary (not streaming): `GetSupportedCurrencies(Empty) returns (GetSupportedCurrenciesResponse)` and `Convert(CurrencyConversionRequest) returns (Money)`. The `server.js` handlers (`getSupportedCurrencies`, `convert`) are synchronous callback-based functions with no async messaging patterns. No SQS, SNS, EventBridge, or event publishing patterns exist. |
| **Gap** | 100% synchronous communication. No async patterns for any operation. Downstream services that need exchange rates must make synchronous calls, creating tight coupling. |
| **Recommendation** | For this utility service, synchronous gRPC is appropriate for real-time conversion requests. However, consider adding an async rate-update event (via SNS or EventBridge) when exchange rates change, so downstream services can cache rates locally and reduce synchronous call volume. |
| **Evidence** | `proto/demo.proto` (unary RPCs only), `server.js` (synchronous callback handlers), absence of messaging SDK imports in `package.json` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Currency conversion is a near-instant, in-memory calculation. The `convert` function in `server.js` performs arithmetic on exchange rates from the static JSON file — no I/O, no external API calls, no database queries. The `_carry` function handles decimal arithmetic. No operations in this service exceed milliseconds, let alone 30 seconds. There are no long-running processes that need async handling. |
| **Gap** | No gap — the service has no long-running operations. The scoring criteria for this question do not penalize services without long-running processes; rather, they assess how such processes are handled when they exist. |
| **Recommendation** | No action needed. If the service evolves to fetch live exchange rates from external APIs (which could introduce latency), implement async patterns with caching to prevent blocking. |
| **Evidence** | `server.js` (`convert` function — in-memory arithmetic only), `data/currency_conversion.json` (local static data) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy found. The proto file uses `proto3` syntax and the package namespace is `hipstershop` with no version component. RPC method names have no version prefix. There are no `/v1/`, `/v2/` URL patterns (gRPC does not use URL paths in the same way as REST, but proto package versioning is the gRPC equivalent). No changelog or API versioning documentation exists. The `package.json` version is `0.1.0`, suggesting pre-release status. |
| **Gap** | No versioning strategy. Breaking changes to `CurrencyConversionRequest` or `Money` message types would affect all consumers simultaneously with no graceful migration path. Since `Money` is used by 6+ other services (Payment, Shipping, Checkout, Product Catalog), breaking changes have wide blast radius. |
| **Recommendation** | Adopt proto package versioning: rename package to `hipstershop.currency.v1`. Use proto field numbering discipline (never reuse or remove field numbers). Maintain backward compatibility — add new fields rather than modifying existing ones. Document breaking changes in a changelog. |
| **Evidence** | `proto/demo.proto` (package `hipstershop` — no version), `package.json` (version `0.1.0`), absence of any changelog or versioning documentation |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The service listens on a port configured via the `PORT` environment variable (`server.js`: `const PORT = process.env.PORT`). The test client (`client.js`) connects to `localhost:7000`, which is hardcoded. No service discovery mechanism is visible — no AWS Cloud Map, Consul, Istio, or Kubernetes Service definitions exist in this repository. However, the use of environment variables for port configuration suggests the service is designed to run in an environment (e.g., Kubernetes) where service discovery is handled externally. |
| **Gap** | No service discovery is defined within this repository. Other services must know the CurrencyService endpoint through external configuration. The `client.js` hardcodes `localhost:7000`. |
| **Recommendation** | When deployed on EKS (preferred), use Kubernetes Services for DNS-based service discovery (`currencyservice.namespace.svc.cluster.local`). Consider AWS Cloud Map for cross-cluster discovery. For service mesh, adopt Istio on EKS for advanced traffic management and mTLS between services. Define Kubernetes Service manifests in Terraform or Helm. |
| **Evidence** | `server.js` (`const PORT = process.env.PORT`), `client.js` (`localhost:7000` hardcoded), absence of Kubernetes Service or service mesh definitions |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Exchange rate data is stored as a static JSON file (`data/currency_conversion.json`) bundled directly in the container image. The file contains 33 currency exchange rates relative to EUR. This is local file storage within the application — not managed object storage. No S3 buckets, no Textract, no document parsing pipelines. |
| **Gap** | Data is embedded in the application, requiring a new container build and deployment for any rate update. There's no managed storage layer that could serve as a source of truth for exchange rates across the platform. |
| **Recommendation** | Migrate exchange rate data to Amazon DynamoDB (preferred per user preferences) with a single-table design (partition key: currency_code, attributes: rate, last_updated). Alternatively, store rate snapshots in S3 for historical analysis and audit. Define DynamoDB table and S3 bucket in Terraform. |
| **Evidence** | `data/currency_conversion.json` (33 currencies, static file), `server.js` (`require('./data/currency_conversion.json')`) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `_getCurrencyData` function in `server.js` provides a single centralized access point for all exchange rate data. Both `getSupportedCurrencies` and `convert` call `_getCurrencyData` — there are no scattered data access patterns. While it is a simple `require()` call (not a proper repository/DAO pattern), it serves as a unified entry point. |
| **Gap** | The data access function is a simple inline `require()` with no abstraction for switching data sources. If exchange rates move to DynamoDB, the entire data access implementation must change. |
| **Recommendation** | Refactor `_getCurrencyData` into a proper data access module with an interface that can be backed by either the static JSON file (for testing) or DynamoDB (for production). This enables the DynamoDB migration recommended in INF-Q2 without changing business logic. |
| **Evidence** | `server.js` (`_getCurrencyData` function called by both RPC handlers, single `require('./data/currency_conversion.json')`) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine is used. The service reads from a static JSON file with no database dependency. No RDS, DynamoDB, or any database engine version is defined in IaC or configuration. There is nothing to pin or evaluate for EOL. |
| **Gap** | No database version management exists because no database exists. While this means no EOL risk from databases, it also means the data model has not matured beyond a flat file. |
| **Recommendation** | When adopting DynamoDB (per INF-Q2 recommendation), no engine version management is needed (DynamoDB is fully managed, versionless). If RDS is later considered for relational needs, ensure engine versions are explicitly pinned in Terraform with automated upgrade paths. |
| **Evidence** | `data/currency_conversion.json` (static file, no database), absence of any database engine references |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All business logic is implemented in the application layer. The `convert` function in `server.js` performs currency conversion arithmetic entirely in JavaScript. The `_carry` function handles decimal precision. No stored procedures, triggers, or proprietary SQL constructs exist — there is no database at all. All logic is portable and not coupled to any database engine. |
| **Gap** | No gap — all business logic is cleanly in the application layer. |
| **Recommendation** | Maintain this pattern. When migrating to DynamoDB, ensure that conversion logic remains in the application layer — do not introduce DynamoDB Streams triggers for business logic that belongs in the service. |
| **Evidence** | `server.js` (`convert` function, `_carry` function — all business logic in JavaScript), absence of any `.sql` files or database procedures |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration found. The service uses `pino` for structured application logging (JSON format with severity levels), but this is application-level logging, not infrastructure audit logging. No `aws_cloudtrail` resources, no CloudWatch log retention policies, no S3 log buckets with object lock. |
| **Gap** | No audit trail for infrastructure or API operations. Application logs exist via pino but are not configured for immutable storage or compliance retention. |
| **Recommendation** | Enable CloudTrail in the AWS account (if not already enabled at the organization level). Configure CloudWatch Logs with defined retention periods for CurrencyService logs. Use Terraform to define CloudTrail trail with S3 bucket for immutable log storage. Ensure pino logs are collected by a Fluentd/Fluent Bit sidecar on EKS and forwarded to CloudWatch Logs. |
| **Evidence** | `server.js` (pino logger configured with structured JSON output), absence of any `aws_cloudtrail` or CloudWatch configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration found. The service has no persistent data stores to encrypt — exchange rates are embedded in the container image as a static JSON file. No KMS keys, no S3 bucket encryption, no EBS volume encryption is defined. |
| **Gap** | No encryption at rest is configured. While the current data (exchange rates) is publicly available, the lack of encryption infrastructure means any future sensitive data would be unprotected. |
| **Recommendation** | When provisioning DynamoDB (per INF-Q2 recommendation) and ECR, enable encryption with AWS-managed KMS keys as a baseline. For sensitive data, use customer-managed KMS keys. Define KMS key resources and encryption settings in Terraform. |
| **Evidence** | Absence of any `aws_kms_key` resources, absence of encryption configuration on any storage resource |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The gRPC server uses insecure credentials: `grpc.ServerCredentials.createInsecure()` in `server.js`. No TLS, no mTLS, no authentication, and no authorization on any endpoint. Both `getSupportedCurrencies` and `convert` are accessible without any credentials. The health check endpoint (`check`) is also unauthenticated. |
| **Gap** | All endpoints are completely unauthenticated and unencrypted. Any network-reachable client can invoke currency conversion. In a shared cluster, this is a security risk — other tenants or compromised services could abuse the endpoint. |
| **Recommendation** | Adopt mTLS between services via a service mesh (Istio on EKS, preferred). Replace `createInsecure()` with TLS credentials using certificates managed by the service mesh or cert-manager. For external access, require JWT-based authentication via an API gateway. |
| **Evidence** | `server.js` (`grpc.ServerCredentials.createInsecure()`), absence of any auth middleware, token validation, or TLS configuration |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration found. No Cognito user pools, no OIDC configuration, no SAML federation, no IAM role-based service identity. The service has no concept of caller identity — all requests are anonymous. |
| **Gap** | No identity integration. The service cannot attribute requests to specific callers, which limits audit capability and access control. |
| **Recommendation** | Implement service identity via Kubernetes service accounts with IAM Roles for Service Accounts (IRSA) on EKS. This provides the CurrencyService with an AWS IAM identity for accessing AWS resources (DynamoDB, Secrets Manager) without hardcoded credentials. For service-to-service identity, use Istio's SPIFFE-based workload identity. |
| **Evidence** | Absence of any identity provider references in source code, configuration, or dependencies |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The service uses environment variables for configuration (`PORT`, `ENABLE_TRACING`, `COLLECTOR_SERVICE_ADDR`, `DISABLE_PROFILER`, `OTEL_SERVICE_NAME`). No hardcoded secrets (passwords, API keys, tokens) were found in the source code. However, there is no dedicated secrets management system — no AWS Secrets Manager, no HashiCorp Vault, no Kubernetes Secrets references. The `@google-cloud/profiler` and `@google-cloud/trace-agent` libraries may implicitly use GCP credentials via environment or metadata, but this is not explicitly configured. |
| **Gap** | While no secrets are currently hardcoded (positive), there is also no secrets management infrastructure in place. When the service evolves to use DynamoDB or external APIs, credentials will need proper management. |
| **Recommendation** | Adopt AWS Secrets Manager for any credentials needed by the service. Use Kubernetes External Secrets Operator on EKS to sync Secrets Manager values to Kubernetes Secrets. Define secrets infrastructure in Terraform. Implement IRSA for AWS service access to avoid credentials entirely. |
| **Evidence** | `server.js` (environment variable references: `PORT`, `ENABLE_TRACING`, `COLLECTOR_SERVICE_ADDR`), absence of hardcoded secrets, absence of Secrets Manager or Vault references |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Dockerfile uses Alpine-based images which are minimal and have a small attack surface: `node:20.20.1-alpine` for building and `alpine:3.23.3` for runtime. Both images are pinned by SHA256 digest, which prevents supply-chain attacks from tag mutation. The build stage installs build tools (`python3`, `make`, `g++`) but these are discarded in the multi-stage build (only `node_modules` are copied to the runtime image). However, there is no evidence of vulnerability scanning (no Trivy, Snyk, or AWS Inspector), no patching automation (no dependabot, no renovate), and no hardened base image verification. |
| **Gap** | Good base image hygiene (Alpine + SHA256 pinning + multi-stage build) but no automated vulnerability scanning or patching lifecycle. Image vulnerabilities may accumulate over time without scanning. |
| **Recommendation** | Add container image scanning (Trivy or Amazon ECR image scanning) to the CI/CD pipeline. Enable Amazon Inspector for continuous vulnerability monitoring. Consider using Bottlerocket OS for EKS node groups (hardened, purpose-built for containers). Add Dependabot or Renovate for automated dependency updates. |
| **Evidence** | `Dockerfile` (multi-stage build, `node:20.20.1-alpine@sha256:...`, `alpine:3.23.3@sha256:...`), absence of `.snyk`, `dependabot.yml`, or scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No application security scanning found. No SAST (SonarQube, Semgrep, CodeGuru), no DAST, no dependency scanning (npm audit, Snyk), no container scanning. No CI/CD pipeline exists to integrate security scanning into. No `.snyk` policy file, no `dependabot.yml`, no CodeGuru reviewer configuration. |
| **Gap** | Complete absence of security scanning. Dependency vulnerabilities in the 15 npm packages (including `xml2js` which has had historical CVEs) may exist undetected. No automated security gates exist. |
| **Recommendation** | Add security scanning stages to the CI/CD pipeline (once created): (1) `npm audit` for dependency vulnerabilities, (2) Trivy/Snyk for container image scanning, (3) Semgrep or CodeGuru Reviewer for SAST. Configure `dependabot.yml` for automated dependency update PRs. Block deployments on critical/high severity findings. |
| **Evidence** | Absence of `.github/dependabot.yml`, `.snyk`, any security scanning in CI/CD (no CI/CD exists), `package.json` (15 dependencies with no audit configuration) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry distributed tracing is instrumented with gRPC auto-instrumentation. The `package.json` includes `@opentelemetry/instrumentation-grpc` (0.213.0), `@opentelemetry/sdk-node` (0.213.0), `@opentelemetry/exporter-otlp-grpc` (0.26.0), `@opentelemetry/resources` (2.6.0), and `@opentelemetry/semantic-conventions` (1.40.0). In `server.js`, gRPC instrumentation is registered unconditionally (`registerInstrumentations`), enabling trace context propagation on all gRPC calls regardless of whether tracing export is enabled. When `ENABLE_TRACING=1`, the OTLP trace exporter sends traces to `COLLECTOR_SERVICE_ADDR`. The service name is configurable via `OTEL_SERVICE_NAME` (defaults to `currencyservice`). |
| **Gap** | Tracing is conditionally enabled via `ENABLE_TRACING` environment variable — if not set, traces are not exported. The gRPC instrumentation is registered for propagation regardless, but without export, traces cannot be analyzed. No tracing backend (X-Ray, Jaeger, Tempo) is defined in IaC. The `@opentelemetry/exporter-otlp-grpc` version (0.26.0) is significantly older than the other OTel packages, suggesting potential compatibility issues. |
| **Recommendation** | Ensure `ENABLE_TRACING=1` is set in all production environments. Deploy the AWS Distro for OpenTelemetry (ADOT) collector on EKS to forward traces to AWS X-Ray. Upgrade `@opentelemetry/exporter-otlp-grpc` to match the version of other OTel packages. Define the ADOT collector deployment in Terraform/Helm. |
| **Evidence** | `package.json` (6 OpenTelemetry packages), `server.js` (gRPC instrumentation registration, conditional OTLP exporter configuration) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No SLO configuration files, no error budget tracking, no CloudWatch dashboards with latency targets. The service has basic structured logging via pino but no formal definition of acceptable service levels (e.g., p99 conversion latency < 10ms, availability > 99.99%). |
| **Gap** | No SLOs defined. For a P1 utility service that blocks checkout, there should be explicit availability and latency SLOs with error budget tracking. |
| **Recommendation** | Define SLOs for CurrencyService: (1) Availability: 99.99% of gRPC requests return non-error status. (2) Latency: p99 conversion latency < 50ms. (3) Error budget: 0.01% error budget per 30-day window. Implement SLO monitoring with CloudWatch ServiceLevelObjective (if available) or Grafana SLO on EKS. |
| **Evidence** | Absence of any SLO definitions, dashboards, or error budget configuration |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. The service logs conversion requests via pino (`logger.info('conversion request successful')`) but does not emit structured metrics for business outcomes. No `cloudwatch.put_metric_data`, no OpenTelemetry metrics instrumentation, no Prometheus exposition. Only application log lines exist. |
| **Gap** | No business metrics. There is no visibility into: conversion volume by currency pair, most-requested currencies, conversion error rates by currency, or conversion value distribution. These metrics would inform business decisions and detect anomalies. |
| **Recommendation** | Add OpenTelemetry Metrics SDK to publish custom business metrics: (1) `currency_conversions_total` (counter, by from_currency and to_currency), (2) `currency_conversion_value_euros` (histogram), (3) `supported_currencies_requests_total` (counter). Export to CloudWatch via ADOT collector. |
| **Evidence** | `server.js` (pino log statements only — `logger.info('conversion request successful')`, no metrics SDK usage) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no composite alarms, no anomaly detection models. The service has no mechanism to detect or alert on increased error rates, latency spikes, or traffic anomalies. |
| **Gap** | No alerting of any kind. If the CurrencyService begins returning errors or experiences latency degradation, no one is notified. For a P1 service, this is a critical gap. |
| **Recommendation** | Create CloudWatch alarms for: (1) gRPC error rate > 1% (critical), (2) p99 latency > 100ms (warning), (3) conversion failures > 0 in 5-minute window. Enable CloudWatch anomaly detection on conversion volume for detecting unusual traffic patterns. Route alarms to SNS → PagerDuty/OpsGenie for on-call notification. Define in Terraform. |
| **Evidence** | Absence of any alerting configuration, CloudWatch alarms, or monitoring integration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. No CI/CD pipeline exists, so there is no canary, blue/green, or rolling deployment mechanism. No CodeDeploy configuration, no Argo Rollouts, no Kubernetes rolling update strategy defined, no feature flags. Deployments are presumed to be direct-to-production (manual). |
| **Gap** | All releases go directly to production with no staged rollout, no traffic shifting, and no automated rollback. A bad deployment could break currency conversion for the entire platform with no recovery path except manual rollback. |
| **Recommendation** | Adopt GitOps-based rolling deployments on EKS (preferred). Configure Kubernetes Deployment with `RollingUpdate` strategy (maxSurge: 1, maxUnavailable: 0) as baseline. For higher safety, adopt Argo Rollouts with canary analysis — shift 10% traffic to new version, validate metrics for 5 minutes, then promote. Define in Helm or Kustomize managed by ArgoCD. |
| **Evidence** | Absence of any CI/CD pipeline, deployment configuration, or rollout strategy |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated tests exist. The `package.json` defines `"test": "echo \"Error: no test specified\" && exit 1"` — an explicit declaration that no tests have been created. No test directories, no Jest/Mocha/Vitest configuration, no gRPC test utilities, no contract tests. The `client.js` file is a manual test client, not an automated test. |
| **Gap** | Zero test coverage. There is no regression safety net for the `convert` or `_carry` functions. The `client.js` manual test connects to `localhost:7000` and must be run manually — it is not integrated into any test framework or CI pipeline. |
| **Recommendation** | Create automated tests: (1) Unit tests (Jest) for `_carry()` function edge cases (negative values, overflow, precision). (2) Unit tests for `convert()` function (known currency pairs, boundary values, invalid currencies). (3) gRPC integration tests using `@grpc/grpc-js` to start the server and call endpoints programmatically. (4) Contract tests to validate proto compatibility. Run all tests in CI pipeline. |
| **Evidence** | `package.json` (`"test": "echo \"Error: no test specified\" && exit 1"`), `client.js` (manual test client, not automated), absence of any test framework in dependencies |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks found. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions incident workflows, no runbook files (markdown, YAML, JSON). No documentation on how to respond to CurrencyService failures. |
| **Gap** | Incident response is entirely ad hoc. When the CurrencyService fails, there is no documented procedure for diagnosis, mitigation, or recovery. Given this service blocks checkout, the mean-time-to-recovery (MTTR) for incidents is unpredictable. |
| **Recommendation** | Create runbooks for common scenarios: (1) Service unresponsive — check pod status, restart deployment. (2) High error rate — check OpenTelemetry traces for failing currency pairs. (3) Stale exchange rates — verify data source and trigger rate refresh. Store runbooks as markdown in the repository. For automation, create SSM Automation documents or Kubernetes-native self-healing (liveness/readiness probes are partially addressed by the health check endpoint). |
| **Evidence** | Absence of any runbook files, SSM documents, or incident response automation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file referencing observability assets, no per-service dashboards, no named alarm owners, no team attribution on monitoring resources. The OpenTelemetry instrumentation exists but there is no definition of who owns and maintains the observability stack for this service. |
| **Gap** | No observability ownership. The tracing instrumentation exists but no one is explicitly responsible for maintaining it, reviewing traces, or responding to observability gaps. |
| **Recommendation** | Create a CODEOWNERS file assigning ownership of observability configuration. Define per-service dashboards in Grafana (on EKS) or CloudWatch with named team owners. Tag all monitoring resources with `team` and `service` tags. |
| **Evidence** | Absence of CODEOWNERS file, absence of dashboard definitions, absence of team attribution |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging found. There are no IaC resources to tag — no Terraform `tags` blocks, no `default_tags` in provider configuration, no `required-tags` Config rules. The only deployment artifact is the Dockerfile, which does not define AWS resource tags. |
| **Gap** | No tagging governance. When infrastructure is created (EKS, DynamoDB, ECR, etc.), there is no tagging standard to ensure cost allocation, ownership identification, and environment classification. |
| **Recommendation** | Define a tagging standard in Terraform using `default_tags` in the AWS provider: `service=currencyservice`, `team={team-name}`, `environment={env}`, `cost-center={cc}`, `priority=P1`. Enforce with AWS Config `required-tags` rule. Define in Terraform. |
| **Evidence** | Absence of any IaC resources, absence of any tagging configuration |

---

## Learning Materials

Based on the two triggered pathways (Move to Modern DevOps, Move to AI):

### Move to Modern DevOps
- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [GitOps model for provisioning and bootstrapping Amazon EKS clusters using Crossplane and Argo CD](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/set-up-a-gitops-pipeline-with-argocd.html)
- [EKS Workshop — CI/CD](https://www.eksworkshop.com/)

### Move to AI
- [Move to AI — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `server.js` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q1, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q3, OPS-Q6 | Main gRPC server — contains RPC handlers (`getSupportedCurrencies`, `convert`), data access (`_getCurrencyData`), business logic (`_carry`), OpenTelemetry instrumentation, pino logging, and insecure server credentials |
| `client.js` | APP-Q2, APP-Q6, OPS-Q6 | Manual test client — connects to `localhost:7000`, demonstrates gRPC call patterns, not an automated test |
| `package.json` | INF-Q2, INF-Q11, APP-Q1, APP-Q3, OPS-Q1, OPS-Q6, SEC-Q6, SEC-Q7 | Node.js dependency manifest — declares 15 dependencies including @grpc/grpc-js, OpenTelemetry suite, pino, google-cloud profiler/trace; test script is placeholder |
| `Dockerfile` | INF-Q1, INF-Q6, APP-Q1, SEC-Q6 | Multi-stage build using `node:20.20.1-alpine` (builder) and `alpine:3.23.3` (runtime), both pinned by SHA256 digest; exposes port 7000 |
| `proto/demo.proto` | APP-Q2, APP-Q3, APP-Q5, INF-Q4 | Protocol Buffers definition for 9 hipstershop services including CurrencyService; defines `GetSupportedCurrencies` and `Convert` RPCs with `Money`, `CurrencyConversionRequest` messages |
| `proto/grpc/health/v1/health.proto` | APP-Q2 | Standard gRPC health check proto — enables liveness/readiness probes |
| `data/currency_conversion.json` | INF-Q2, INF-Q8, DATA-Q1, DATA-Q2, DATA-Q3, APP-Q4 | Static exchange rates for 33 currencies relative to EUR; embedded in container image |
| `genproto.sh` | APP-Q2 | Shell script copying proto files from shared `../../protos/` directory — indicates shared proto repository pattern |
| `.dockerignore` | INF-Q1 | Excludes `client.js` and `node_modules/` from Docker build context |
| `.gitignore` | — | Excludes `node_modules/` from version control |
| `.atx-config-currencyservice-mod.yaml` | Metadata | Assessment configuration — defines repo_type, context, preferences, priority, and tags |
