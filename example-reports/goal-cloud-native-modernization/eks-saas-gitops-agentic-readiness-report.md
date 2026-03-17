# Agentic Readiness Assessment Report
**Target**: ./services/eks-saas-gitops
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: cloud-native-modernization
**Goal Context**: Decomposing monoliths into containerized microservices on EKS with GitOps deployment
**Repository Type**: monorepo (auto-detected)

---

## Table of Contents

1. Executive Summary
2. Score Table
3. Top Priorities (Critical Gaps)
4. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
5. Recommended Modernization Pathways
   - Pathway Summary Table
   - Pathway Details (for Triggered pathways)
6. Readiness Roadmap
   - Phase 1 — Containerize & Automate (Days 1–30)
   - Phase 2 — Decompose & Decouple (Months 1–3)
   - Phase 3 — Optimize & Scale (Months 3–6)
7. Recommended Self-Paced Learning Materials
8. Appendix: Evidence Index

---

## Executive Summary

This EKS SaaS GitOps monorepo represents a **strong cloud-native foundation** with EKS, Karpenter, Terraform IaC, Flux CD GitOps, and a well-decomposed microservices architecture (producer, consumer, payments). The infrastructure layer scores well — containerized workloads on EKS with managed DynamoDB, SQS messaging, and Argo Workflows for orchestration demonstrate mature cloud-native patterns. However, **critical gaps in DevOps maturity, security posture, and operational observability** undermine production readiness. There are no integration tests, no canary/blue-green deployments, no distributed tracing, no API authentication, and multiple IAM policies grant `AdministratorAccess`. The application microservices lack resilience patterns, rate limiting, idempotency, and API documentation — all essential for production-grade cloud-native systems. Addressing the Modern DevOps and security gaps will unlock the full potential of this already-containerized, GitOps-managed platform.

### Overall Score: 1.9 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 3.1 / 4.0 | 🟡 |
| Application Architecture | 2.2 / 4.0 | 🟡 |
| Data Foundations | 1.8 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.3 / 4.0 | 🟠 |
| Operations & Observability | 1.1 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

### 1. OPS-Q9: Deployment Strategy — Score 1/4 ❌
**Why it matters for cloud-native modernization**: Flux CD reconciles changes directly to production with no canary, blue-green, or progressive delivery. In a multi-tenant SaaS environment, a bad deployment affects all tenants simultaneously. Cloud-native systems require safe deployment strategies to minimize blast radius.
**First step**: Integrate [Flagger](https://flagger.app/) with Flux CD to enable automated canary deployments for the tenant microservices, using the existing ALB for traffic shifting.

### 2. OPS-Q10: Integration Testing — Score 1/4 ❌
**Why it matters for cloud-native modernization**: Zero test files exist in the repository. Without integration tests, there is no safety net for refactoring, service extraction, or dependency upgrades — all fundamental activities in cloud-native modernization. Every change to producer-consumer-SQS-DynamoDB flows is untested.
**First step**: Add pytest integration tests for the producer→SQS→consumer→DynamoDB flow using localstack or moto for AWS service mocking, and wire them into a CI pipeline.

### 3. OPS-Q1: Distributed Tracing — Score 1/4 ❌
**Why it matters for cloud-native modernization**: The microservices communicate via SQS (async) and HTTP (sync) with no trace context propagation. When a message is lost between producer and consumer, there is no way to trace the request path. Distributed tracing is the foundation of observability for decomposed systems.
**First step**: Add OpenTelemetry SDK to the Flask microservices (`opentelemetry-instrumentation-flask`, `opentelemetry-instrumentation-boto3`) and export traces to AWS X-Ray or an ADOT Collector deployed via Helm.

### 4. SEC-Q9: API Authentication — Score 1/4 ❌
**Why it matters for cloud-native modernization**: Microservice endpoints (`/producer`, `/consumer`, `/payments`) have zero authentication. The ALB Ingress routes by `TenantID` HTTP header, which can be trivially spoofed. Any client can impersonate any tenant. This is a critical security gap for a multi-tenant SaaS system.
**First step**: Deploy Amazon API Gateway or add JWT validation middleware to the Flask apps. Integrate with Amazon Cognito for tenant-scoped JWT tokens with `tenantID` claims.

### 5. SEC-Q2: IAM Least Privilege — Score 2/4 🟠
**Why it matters for cloud-native modernization**: The `argo-workflows` and `tf-controller` IRSA roles are attached to `arn:aws:iam::aws:policy/AdministratorAccess`. The Argo Workflows and Argo Events ClusterRoles grant `*` verbs on `*` resources. These wildcard permissions violate least privilege and create a significant blast radius if any workflow is compromised.
**First step**: Replace `AdministratorAccess` on `argo-workflows-irsa` and `tf-controller` roles with scoped policies that list only the specific AWS actions and resources each service needs (e.g., SQS, DynamoDB, ECR, S3, EKS for Argo; Terraform state S3, DynamoDB lock, and target resources for TF controller).

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: EKS cluster v1.32 defined in `terraform/workshop/main.tf` with managed node group (`m5.large`, min=3/max=5). Karpenter v1.4.0 configured via `gitops/infrastructure/production/02-karpenter.yaml` with two NodePools (`default` and `application`) defined in `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` and `02-application-karpenter-config.yaml`. All tenant microservices run as containerized workloads on EKS. However, Gitea runs on a raw EC2 instance (`terraform/modules/gitea/main.tf`) as an `m5.large` with `aws_instance`.
- **Gap**: Gitea on raw EC2 is the sole non-containerized compute workload. This creates operational overhead for patching, scaling, and monitoring outside the Kubernetes ecosystem.
- **Recommendation**: Migrate Gitea to a Helm-based deployment on EKS or replace with a managed Git service (AWS CodeCommit or GitHub). Alternatively, containerize Gitea and deploy via Flux CD HelmRelease.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: DynamoDB tables are defined per-tenant in `terraform/modules/tenant-apps/main.tf` (`consumer_ddb` with `tenant_id` hash key, `message_id` range key, PAY_PER_REQUEST billing, point-in-time recovery enabled). DynamoDB is fully managed with no engine version concern. However, Gitea runs an embedded SQLite database on the EC2 instance (`terraform/modules/gitea/userdata.sh`), which is self-managed and not backed up through IaC.
- **Gap**: Gitea's embedded SQLite is self-managed with no automated backup, failover, or version pinning. This is a minor gap since Gitea is a supporting service, not a business-critical database.
- **Recommendation**: If Gitea persistence is important, migrate its data layer to Amazon RDS for PostgreSQL or move to a managed Git hosting solution.

#### INF-Q3: Workflow Orchestration
- **Score**: 4/4 ✅
- **Finding**: Argo Workflows v0.40.11 deployed via `gitops/infrastructure/production/03-argo-workflows.yaml`. Argo Events v2.4.3 deployed via `gitops/infrastructure/production/06-argo-events.yaml`. Workflow templates for tenant onboarding, offboarding, and deployment defined in `gitops/control-plane/production/workflows/`. SQS-based event sources trigger workflows automatically. Mutex-based synchronization prevents concurrent tenant operations.
- **Gap**: None. Dedicated workflow orchestration is fully in use.
- **Recommendation**: Continue leveraging Argo Workflows. Consider adding Step Functions for AWS-native orchestration of longer-running infrastructure provisioning workflows.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: SQS queues extensively used throughout: `argoworkflows-onboarding-queue`, `argoworkflows-offboarding-queue`, `argoworkflows-deployment-queue` defined in `terraform/modules/gitops-saas-infra/main.tf`. Per-tenant SQS queues (`consumer-{tenant_id}`) for producer-to-consumer communication defined in `terraform/modules/tenant-apps/main.tf`. All queues use `sqs_managed_sse_enabled = true`. Argo Events uses SQS as event source for workflow triggers.
- **Gap**: None. Managed SQS messaging is used for all async communication.
- **Recommendation**: Maintain current SQS-based architecture. Consider adding dead-letter queues (DLQ) for unprocessable messages to improve reliability.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: Comprehensive Terraform covers VPC, EKS, IAM roles, ECR repositories, SQS queues, DynamoDB tables, S3 buckets, SSM parameters, and Gitea EC2 in `terraform/workshop/` and `terraform/modules/`. Flux CD GitOps manages Kubernetes infrastructure (Karpenter, Argo, ALB Controller, Kubecost, TF Controller, Metrics Server) in `gitops/infrastructure/production/`. Helm charts define application deployments in `helm-charts/`. TF Controller enables in-cluster Terraform execution for tenant provisioning.
- **Gap**: None. >90% of infrastructure is IaC-managed.
- **Recommendation**: Continue current practices. Consider adding Terraform state locking and remote backend configuration documentation.

#### INF-Q6: CI/CD
- **Score**: 3/4 🟡
- **Finding**: Flux CD provides continuous deployment via GitOps reconciliation configured in `terraform/modules/flux_cd/main.tf` (Flux Operator with FluxInstance, distribution v2.7.5). Image automation controllers watch ECR for new image tags and auto-commit updates. Argo Workflows automate tenant lifecycle. However, no CI pipeline exists — there are no GitHub Actions workflows, no `buildspec.yml`, no Jenkinsfile, no CodePipeline definitions. Container images are built externally and pushed to ECR without a defined build/test pipeline in the repo.
- **Gap**: No continuous integration pipeline for build, test, and image creation. Deployment automation (CD) is strong via Flux, but the build and test phases are undefined.
- **Recommendation**: Add a CI pipeline using AWS CodeBuild/CodePipeline or GitHub Actions that builds Docker images, runs unit/integration tests, and pushes to ECR. The Flux image automation will handle deployment from there.

#### INF-Q7: API Entry Point
- **Score**: 3/4 🟡
- **Finding**: AWS ALB deployed via ALB Ingress Controller (`gitops/infrastructure/production/04-lb-controller.yaml`, aws-load-balancer-controller v1.6.2). Ingress resources defined in `helm-charts/helm-tenant-chart/templates/ingress.yaml` with ALB annotations: `internet-facing` scheme, `ip` target type, `group.name: tenants-lb`, and HTTP header-based tenant routing via `alb.ingress.kubernetes.io/conditions`.
- **Gap**: No API Gateway with throttling, authentication, or request validation. ALB provides routing but not API management. No WAF integration.
- **Recommendation**: Deploy Amazon API Gateway in front of the ALB for request validation, throttling, authentication, and API key management. Alternatively, add AWS WAF to the ALB with rate-limiting rules and managed rule groups.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, MSK, or managed streaming services detected in any Terraform module or GitOps manifest. SQS is used for point-to-point async messaging, not streaming. No stream consumer patterns found in application code.
- **Gap**: No real-time streaming capability. If the SaaS platform needs event-driven analytics, real-time dashboards, or event replay, there is no streaming infrastructure.
- **Recommendation**: If real-time event processing is needed, deploy Amazon Kinesis Data Streams or MSK Serverless via Terraform. For event replay and fan-out, consider Amazon EventBridge.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: VPC with public and private subnets across 3 AZs defined in `terraform/workshop/main.tf` (CIDR `10.35.0.0/16`). EKS runs in private subnets. Gitea security group in `terraform/modules/gitea/main.tf` has specific ingress rules for SSH (port 22), HTTP (port 3000), and Gitea SSH (port 222) restricted to VS Code VPC CIDR and EKS security group. However, egress rule allows `0.0.0.0/0` on all ports. EKS cluster endpoint is public (`cluster_endpoint_public_access = true`). Single NAT gateway for cost optimization.
- **Gap**: Overly permissive egress on Gitea SG. EKS cluster API endpoint is publicly accessible. Single NAT gateway is a single point of failure.
- **Recommendation**: Restrict Gitea egress to required destinations. Set `cluster_endpoint_public_access = false` and access the cluster via VPN or bastion. Consider multi-AZ NAT gateways for production.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Karpenter v1.4.0 provides cluster-level autoscaling with two NodePools: `default` (cpu limit 1000, memory limit 2000Gi) and `application` (same limits, with `applications` taint). Disruption policy is `WhenEmptyOrUnderutilized` with 1m consolidation. EKS managed node group has min=3/max=5. HPA template exists in `helm-charts/helm-tenant-chart/templates/hpa.yaml` but `autoscaling.enabled: false` in `values.yaml.template`.
- **Gap**: HPA is disabled by default for all tenant microservices. Pod-level autoscaling is not active. Karpenter handles node-level scaling but individual service replicas remain static.
- **Recommendation**: Enable HPA for tenant microservices in values.yaml defaults (set `autoscaling.enabled: true` with appropriate CPU/memory thresholds). Consider KEDA for SQS-based autoscaling of the consumer service.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: All 3 tenant microservices (producer, consumer, payments) are Python 3.9 Flask applications. Dockerfiles use `python:3.9.17-slim` base image. Dependencies include Flask 3.0.0, boto3 ~1.28.59, botocore ~1.31.59. Workflow automation scripts are shell scripts (bash). Terraform uses HCL.
- **Gap**: Python 3.9 is approaching end-of-life (October 2025). The Python version is pinned to a specific patch (3.9.17-slim) in Dockerfiles rather than a supported minor version.
- **Recommendation**: Upgrade Dockerfiles to `python:3.12-slim` or later. Python has an excellent cloud-native and agent ecosystem, so this is a good language choice.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specifications found anywhere in the repository. Flask routes in `producer.py`, `consumer.py`, and `payments.py` define endpoints (`/producer`, `/consumer`, `/payments`) without any API documentation annotations, docstrings, or auto-generation configuration. No `openapi.yaml`, `swagger.json`, or API spec files exist.
- **Gap**: Complete absence of API documentation. No programmatic way for tools, agents, or external systems to discover available endpoints, request/response schemas, or authentication requirements.
- **Recommendation**: Add `flask-smorest` or `flasgger` to generate OpenAPI specs from Flask routes. Alternatively, create manual OpenAPI 3.0 specs for each microservice and serve them via Swagger UI.

#### APP-Q3: Async vs Sync Communication
- **Score**: 3/4 🟡
- **Finding**: Producer→Consumer communication is async via SQS (`producer.py` calls `sqs_client.send_message()`). Consumer polls SQS in a background thread and writes to DynamoDB (`consumer.py` `process_messages()`). Argo Events uses SQS for event-driven workflow triggers. However, HTTP endpoints (`/producer GET`, `/consumer GET`, `/payments GET`) are synchronous. No async HTTP patterns (webhooks, callbacks) exist.
- **Gap**: HTTP endpoints are purely synchronous. The payments service has no async capability at all — it only serves a sync GET endpoint.
- **Recommendation**: Maintain the strong async SQS patterns. For any future long-running HTTP operations, add async job submission with polling/callback patterns.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Already decomposed into 3 independently deployable microservices: `producer` (sends messages to SQS), `consumer` (reads SQS, writes DynamoDB), and `payments` (stub service). Each has its own Dockerfile, `requirements.txt`, Helm release, service account, and IRSA role. Multi-tenant isolation is implemented with per-tenant namespaces (premium), shared namespaces (basic/pool-1), and per-tenant SQS/DynamoDB resources. Tier templates in `gitops/application-plane/production/tier-templates/` define `basic`, `advanced`, and `premium` isolation patterns.
- **Gap**: None. Clear microservices architecture with well-defined boundaries.
- **Recommendation**: Continue the current microservices pattern. Consider extracting the tenant onboarding logic (currently in shell scripts) into a dedicated microservice with a proper API.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All Flask endpoints return Python dictionaries, which Flask automatically serializes to JSON. Examples: `producer.py` returns `{"tenant_id": ..., "environment": ..., "version": ..., "microservice": ...}`. Consumer and payments follow the same JSON response pattern. Health probes return `{"Status": "OK"}`.
- **Gap**: None. All APIs return structured JSON.
- **Recommendation**: Consider adding standardized error response schemas across all services for consistency.

#### APP-Q6: Workflow Logic
- **Score**: 4/4 ✅
- **Finding**: Argo Workflows handles all complex tenant lifecycle operations: onboarding (`tenant-onboarding-workflow-template.yaml`), offboarding (`tenant-offboarding-workflow-template.yaml`), and deployment (`tenant-deployment-workflow-template.yaml`). Workflows are triggered by SQS events via Argo Events sensors. No hardcoded state machines in application code. TF Controller manages Terraform execution for infrastructure provisioning triggered by Helm releases (`helm-charts/helm-tenant-chart/templates/terraform.yaml` with `approvePlan: auto`).
- **Gap**: None. Dedicated workflow orchestration via Argo Workflows.
- **Recommendation**: Continue leveraging Argo Workflows for operational automation.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: The `POST /producer` endpoint in `producer.py` sends a message to SQS without any idempotency key. SQS `send_message()` is called without `MessageDeduplicationId`. Consumer's `process_messages()` in `consumer.py` calls `ddb_client.put_item()` (which is an upsert by default on DynamoDB), but there is no application-level deduplication — if a message is received twice (SQS at-least-once delivery), it will be processed twice. No idempotency-key headers in API schemas.
- **Gap**: No idempotency patterns anywhere. SQS standard queues provide at-least-once delivery, making deduplication essential. Duplicate message processing is possible.
- **Recommendation**: Add `MessageDeduplicationId` to SQS sends (switch to FIFO queues or add application-level dedup). Implement idempotency keys for the producer POST API. Use DynamoDB conditional writes to prevent duplicate processing in the consumer.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting middleware found in any Flask application (`producer.py`, `consumer.py`, `payments.py`). No `flask-limiter` or `flask-ratelimit` in `requirements.txt`. ALB Ingress has no WAF rules. No API Gateway with throttling. No `aws_wafv2_web_acl` in Terraform.
- **Gap**: Complete absence of rate limiting. Any client can send unlimited requests to the producer API, potentially flooding SQS queues and DynamoDB tables across tenants.
- **Recommendation**: Add `flask-limiter` to each microservice for application-level rate limiting. Deploy AWS WAF with rate-based rules on the ALB. Consider per-tenant rate limits tied to tenant tier (basic/advanced/premium).

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: Flask applications make bare boto3 calls without retry configuration, circuit breakers, or timeout settings. `producer.py` has a generic `except Exception` catch-all that returns a 500 error. `consumer.py` has a bare `except Exception` in the message processing loop that just logs the error and continues. No retry decorators, no exponential backoff, no `tenacity` or `resilience4j` equivalent. No timeout configuration on boto3 clients.
- **Gap**: No resilience patterns. A temporary SQS or DynamoDB outage will cause cascading failures without retries. No circuit breakers to prevent upstream overload.
- **Recommendation**: Add `tenacity` for retry with exponential backoff on boto3 calls. Configure boto3 client retry settings. Add request timeouts to all external calls. Implement circuit breaker patterns for the producer→SQS and consumer→DynamoDB paths.

#### APP-Q10: Long-running Processes
- **Score**: 3/4 🟡
- **Finding**: Consumer uses a background thread (`Thread(target=process_messages).start()` in `consumer.py` readiness probe) for long-polling SQS with `WaitTimeSeconds=20`. Argo Workflows handle long-running tenant onboarding/offboarding/deployment operations asynchronously with SQS-triggered workflows. Mutex-based synchronization prevents concurrent workflow execution.
- **Gap**: The background thread approach in the consumer is fragile — if the thread crashes, there is no supervisor to restart it. No async job status API for long-running operations.
- **Recommendation**: Consider moving the SQS consumer logic out of the Flask app thread model into a dedicated worker (e.g., a separate Kubernetes deployment without an HTTP server) or use KEDA to scale consumer pods based on SQS queue depth.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL versioning (`/v1/`, `/v2/`) in any Flask route. Routes are unversioned: `/producer`, `/consumer`, `/payments`. No `Accept-Version` headers. Helm chart version is `0.0.1`. Application `ms_version` is hardcoded as a string (`"0.0.1"` in producer/consumer, `"1.0.0"` in payments) but not used for API routing.
- **Gap**: No API versioning strategy. Breaking changes to the producer API will affect all tenants simultaneously with no backward compatibility path.
- **Recommendation**: Adopt URL path versioning (e.g., `/v1/producer`) for all microservice endpoints. Update Helm chart ingress rules to support versioned routes.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Kubernetes DNS-based service discovery via Helm `service.yaml` templates. Services use `ClusterIP` type. SSM Parameter Store is used for cross-service resource discovery (SQS queue ARNs and DynamoDB table ARNs stored as SSM parameters per tenant in `terraform/modules/tenant-apps/main.tf`). No dedicated service mesh (Istio, App Mesh), no API catalog, no service registry.
- **Gap**: No service mesh for mTLS, traffic management, or observability. SSM-based discovery works but is not a proper service discovery mechanism. Hard-coded Gitea URL patterns in workflow templates.
- **Recommendation**: Consider AWS App Mesh or Istio for mTLS, traffic shifting (canary deployments), and observability injection. At minimum, use Kubernetes-native service discovery consistently.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent frameworks detected. `requirements.txt` files contain only Flask, boto3, and basic dependencies. No Bedrock, LangChain, LangGraph, OpenAI, Anthropic, Strands Agents, or MCP SDK references. No embedding models, no vector database integrations.
- **Gap**: No AI/agent capabilities exist in the current application.
- **Recommendation**: When ready to add AI capabilities, start with Amazon Bedrock integration via boto3 for the simplest path. Consider building a tenant support agent using Strands Agents SDK with the existing SQS/DynamoDB data.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database detected in any Terraform module, Helm chart, or application dependency. No OpenSearch with k-NN, Aurora pgvector, Pinecone, Weaviate, Chroma, or Bedrock Knowledge Base references found.
- **Gap**: No vector search capability exists.
- **Recommendation**: When AI use cases are prioritized, deploy Amazon OpenSearch Service with k-NN plugin or use Amazon Bedrock Knowledge Bases for managed vector storage.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists to assess management of (see DATA-Q1).
- **Gap**: N/A — no vector DB present.
- **Recommendation**: When adding a vector database, choose a managed option (OpenSearch Service, Bedrock Knowledge Bases) over self-hosted alternatives.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No embedding model calls, document chunking, semantic search, or RAG pipeline components found in any microservice or dependency manifest. No Bedrock Titan, OpenAI ada, or similar embedding model references.
- **Gap**: No RAG implementation exists.
- **Recommendation**: Consider RAG implementation when building AI-powered tenant support or documentation search features. Use Bedrock Knowledge Bases for a managed RAG pipeline.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Per-service data sources are well-bounded: Producer accesses SQS (send) and SSM (read). Consumer accesses SQS (receive/delete), DynamoDB (write), and SSM (read). Payments service has no data access. 3 distinct AWS data services used (SQS, DynamoDB, SSM Parameter Store). Per-tenant isolation via separate SQS queues and DynamoDB tables.
- **Gap**: Minor sprawl — 3 data sources per service is manageable. SSM Parameter Store is used as a lightweight service discovery mechanism rather than a data store.
- **Recommendation**: Maintain current bounded data access patterns. Consider consolidating SSM parameter lookups with caching to reduce API calls.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Direct boto3 client calls in application code. `producer.py` directly calls `sqs_client.send_message()` and `ssm_client.get_parameter()`. `consumer.py` directly calls `sqs_client.receive_message()`, `ddb_client.put_item()`, `ssm_client.get_parameter()`. No repository pattern, no data access layer, no ORM or abstraction.
- **Gap**: Business logic is directly coupled to AWS SDK calls. No abstraction layer for testability or portability.
- **Recommendation**: Extract boto3 calls into a data access layer (e.g., a `repositories/` module) with interface abstractions. This enables unit testing with mocks and potential migration to different backends.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: S3 buckets exist for Argo workflow artifacts (`saasgitops-argo-*` in `terraform/modules/gitops-saas-infra/main.tf`) and code artifacts (`codestack-artifacts-bucket-*`). Both have public access blocked. However, no document parsing capability (Textract, Tika, PDF processing) exists.
- **Gap**: S3 is used for operational artifacts only, not for business-relevant unstructured data. No parsing pipeline.
- **Recommendation**: If document processing is needed, integrate Amazon Textract for OCR/document extraction and store results in DynamoDB.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table schema is defined in Terraform (`terraform/modules/tenant-apps/main.tf`): `tenant_id` (String, hash key), `message_id` (String, range key). Additional attributes (`producer_environment`, `consumer_environment`, `timestamp`) are added in application code (`consumer.py`) but not documented in schema definitions. No JSON Schema files, no Avro/Protobuf schemas, no migration files.
- **Gap**: Schema is partially defined in IaC but attribute documentation is incomplete. DynamoDB's schemaless nature means the full data model is only visible in application code.
- **Recommendation**: Create a data model document or JSON Schema file that describes all DynamoDB attributes, their types, and expected values. Version this alongside the Terraform modules.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. boto3 clients are instantiated at the module level in each microservice (`producer.py`, `consumer.py`). DynamoDB `put_item()` calls include raw attribute definitions. SQS `send_message()` and `receive_message()` calls are inline in request handlers.
- **Gap**: Scattered, duplicated data access patterns across microservices with no abstraction or contract enforcement.
- **Recommendation**: Create a shared Python package or per-service repository module that encapsulates DynamoDB, SQS, and SSM interactions behind clean interfaces.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings or vector indexes exist to refresh. No event-driven embedding refresh triggers, no scheduled re-indexing pipelines.
- **Gap**: N/A — no embeddings exist.
- **Recommendation**: When implementing RAG, use DynamoDB Streams or SQS-based triggers to incrementally update embeddings when data changes.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 3/4 🟡
- **Finding**: DynamoDB is a serverless, fully managed service with no engine version to pin — it is always up-to-date. No RDS, Aurora, or ElastiCache instances exist. Gitea uses an embedded SQLite database on EC2 with no version pinning in IaC. EKS cluster version is explicitly pinned to `1.32` in `terraform/workshop/variables.tf`.
- **Gap**: Minor gap — Gitea's embedded SQLite has no version management. Main business databases (DynamoDB) have no version concerns.
- **Recommendation**: If Gitea persistence matters, migrate to a managed database with version pinning. The DynamoDB approach is ideal — no EOL concerns.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No SQL files, stored procedures, triggers, or proprietary SQL constructs detected anywhere in the repository. DynamoDB is a NoSQL service with no stored procedure capability. No `.sql` files, no `CREATE PROCEDURE`, no `CREATE TRIGGER` patterns.
- **Gap**: None. Clean NoSQL architecture with all business logic in the application layer.
- **Recommendation**: Maintain this pattern. Keep business logic in application code, not in the data layer.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: Gitea admin password stored in SSM Parameter Store SecureString (`terraform/workshop/main.tf`, `aws_ssm_parameter.gitea_password` with `checkov:skip=CKV_AWS_337`). Gitea Flux token stored in SSM (`/eks-saas-gitops/gitea-flux-token`). Flux system secret created as Kubernetes Secret in `terraform/modules/flux_cd/main.tf` with username/password in plaintext Terraform. Git tokens passed as Argo Workflow parameters in `tenant-onboarding-sensor.yaml` (`GIT_TOKEN` value: `${gitea_token}`), visible in workflow YAML.
- **Gap**: Git tokens are exposed as workflow parameters in sensor definitions. Kubernetes Secret for Flux is created via Terraform with plaintext values in state. SSM is used but not Secrets Manager. Checkov skip annotation acknowledges the gap.
- **Recommendation**: Migrate secrets to AWS Secrets Manager. Use External Secrets Operator to sync secrets from Secrets Manager into Kubernetes. Pass Git tokens via Kubernetes Secrets references in Argo Workflows instead of inline parameters.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: Per-service IRSA roles are well-designed: producer role with scoped SQS/SSM permissions (`terraform/modules/tenant-apps/main.tf`), consumer role with scoped SQS/DynamoDB/SSM permissions, Argo Events role with scoped SQS permissions. However: `argo_workflows_eks_role` uses `AdministratorAccess` policy (`terraform/modules/gitops-saas-infra/main.tf`). `tf_controller_irsa_role` uses `AdministratorAccess` policy. Argo Workflows ClusterRole `full-permissions-cluster-role` grants `*` verbs on `*` resources (`gitops/infrastructure/production/03-argo-workflows.yaml`). Argo Events ClusterRole `argo-events-cluster-role` grants `*` verbs on `*` resources (`06-argo-events.yaml`). Karpenter policy uses `Resource: "*"` for EC2 actions.
- **Gap**: Two IRSA roles with `AdministratorAccess` and two ClusterRoles with unrestricted Kubernetes permissions. This violates least privilege and creates a critical blast radius for compromised workloads.
- **Recommendation**: Replace `AdministratorAccess` with scoped policies. For Argo Workflows: scope to SQS, ECR, S3 (artifact bucket), and necessary EKS/K8s API calls. For TF Controller: scope to Terraform state S3 bucket, DynamoDB lock table, and target resource types (SQS, DynamoDB, SSM, IAM roles for tenant resources). Restrict ClusterRoles to specific API groups and resources needed.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: TenantID is passed via HTTP headers (`request.headers.get("tenantID")` in `producer.py`, `consumer.py`, `payments.py`). ALB Ingress routes requests based on `TenantID` header matching. No JWT, OAuth2, OIDC, or token exchange mechanism. Tenant identity is a plain string header with no cryptographic verification.
- **Gap**: No identity propagation. TenantID header can be spoofed by any client. No user-level identity exists. No end-to-end identity chain.
- **Recommendation**: Implement JWT-based authentication with `tenantID` as a signed claim. Use Amazon Cognito user pools with per-tenant app clients. Validate JWT tokens in Flask middleware or at the API Gateway layer.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No `aws_cloudtrail` resource in any Terraform module. EKS cluster does not explicitly enable control plane logging (no `cluster_enabled_log_types` in EKS module). README mentions CloudWatch integration but no logging configuration exists in IaC. No CloudWatch log groups with retention policies defined.
- **Gap**: No audit logging infrastructure defined in IaC. EKS API server audit logs, controller manager logs, and authenticator logs are not enabled.
- **Recommendation**: Enable EKS control plane logging by adding `cluster_enabled_log_types = ["api", "audit", "authenticator"]` to the EKS module. Deploy AWS CloudTrail with log file validation and S3 storage.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. ALB has no WAF association. No `aws_wafv2_web_acl` in Terraform. No `flask-limiter` in requirements.txt. No API Gateway with usage plans or throttling. No per-tenant rate differentiation.
- **Gap**: Complete absence of rate limiting. A single tenant or external attacker could overwhelm the system.
- **Recommendation**: Deploy AWS WAF with rate-based rules on the ALB. Implement per-tenant rate limits at the application layer using `flask-limiter` with tenant-tier-based quotas (basic: 100 req/min, premium: 1000 req/min).

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Flask apps use basic Python logging. `producer.py` logs `f"Message produced: {message}"` which includes tenant_id and message_id. `consumer.py` logs message IDs and DynamoDB table names. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters. No Macie integration.
- **Gap**: No PII awareness in logging. While current data (tenant_id, message_id) may not be PII, there is no framework to prevent PII logging as the application grows.
- **Recommendation**: Add a structured logging library (e.g., `structlog`) with PII redaction middleware. Define a logging policy that specifies which fields must be redacted.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: All automations run without human approval. Argo Workflows execute automatically on SQS events. TF Controller uses `approvePlan: auto` in `helm-charts/helm-tenant-chart/templates/terraform.yaml`, meaning Terraform changes are auto-applied. Flux CD reconciles changes on push to main. No manual approval gates in any workflow or deployment pipeline.
- **Gap**: No human-in-the-loop for any operation including infrastructure provisioning (Terraform), tenant onboarding, or application deployment. A malicious SQS message could trigger full tenant provisioning automatically.
- **Recommendation**: Change TF Controller to `approvePlan: disable` for production workloads (require manual approval for Terraform plans). Add an approval step to the Argo Workflows tenant onboarding workflow. Implement branch protection with required reviews before merging to main.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: ECR repositories use `AES256` encryption (`encryption_type = "AES256"` in `terraform/modules/gitops-saas-infra/apps_needs.tf`). S3 buckets have public access blocked but `checkov:skip=CKV2_AWS_145` (no KMS). Gitea EC2 root volume is encrypted (`encrypted = true` in `terraform/modules/gitea/main.tf`). SQS queues use `sqs_managed_sse_enabled = true`. DynamoDB table has `checkov:skip=CKV2_AWS_119` (no KMS). EKS addon `aws-ebs-csi-driver` is deployed.
- **Gap**: Default AWS-managed encryption only. No customer-managed KMS keys (CMK) for any service. Multiple checkov skip annotations acknowledge this gap.
- **Recommendation**: Create an AWS KMS CMK and apply it to S3 buckets, DynamoDB tables, SQS queues, and ECR repositories. Remove checkov skip annotations once KMS encryption is enabled.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No authentication on any microservice endpoint. `producer.py`, `consumer.py`, and `payments.py` have no auth middleware, no JWT validation, no API key checks. ALB Ingress uses TenantID header for routing (not authentication). Argo Workflows server is configured with `--auth-mode=server` (no authentication) in `03-argo-workflows.yaml`.
- **Gap**: All APIs are completely unauthenticated. Any network-reachable client can access all endpoints. Argo Workflows UI is publicly accessible without auth. This is the most critical security gap.
- **Recommendation**: Implement JWT authentication middleware in Flask. Deploy Amazon Cognito with tenant-scoped user pools. Change Argo Workflows to `--auth-mode=client` or `--auth-mode=sso`. Add ALB authentication action with Cognito integration.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider detected. No `aws_cognito_*` resources in Terraform. No OIDC, SAML, or SSO configuration. IRSA provides service-to-AWS authentication only (not user-level). Gitea has its own local user management.
- **Gap**: No centralized identity provider for application users or administrators. Each component manages its own authentication separately.
- **Recommendation**: Deploy Amazon Cognito as the centralized identity provider for all tenant users. Configure OIDC federation for Argo Workflows and Gitea. Implement SSO across all platform components.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, or tracing SDK in any `requirements.txt`. No trace context propagation in Flask apps — no `traceparent`, `X-Amzn-Trace-Id`, or correlation headers. README mentions Amazon Managed Service for Prometheus (AMP) and Amazon Managed Grafana (AMG) but these are not deployed in the IaC. Kubecost deployed for cost analysis with Prometheus (`gitops/infrastructure/production/05-kubecost.yaml`) — this provides metric collection but not distributed tracing. Metrics Server deployed (`01-metric-server.yaml`) for basic Kubernetes metrics.
- **Gap**: No distributed tracing across the producer→SQS→consumer→DynamoDB flow. When a message fails, there is no way to correlate the producer request with the consumer processing.
- **Recommendation**: Add OpenTelemetry SDK to Flask microservices. Deploy AWS Distro for OpenTelemetry (ADOT) Collector as a DaemonSet via Flux HelmRelease. Export traces to X-Ray. Instrument boto3 calls with `opentelemetry-instrumentation-botocore`.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: `producer.py` uses `app.logger.info(f"Message produced: {message}")` — basic Python f-string logging. `consumer.py` uses `logging.basicConfig(stream=sys.stdout)` with `logger.info()` — unstructured text output. No JSON log formatters, no `structlog`, no `python-json-logger` in requirements.txt. No correlation IDs in log output.
- **Gap**: All logs are unstructured text with no correlation IDs. CloudWatch Log Insights queries will be difficult. Cross-service log correlation is impossible.
- **Recommendation**: Add `python-json-logger` or `structlog` to all microservices. Include tenant_id, correlation_id, and trace_id in every log entry. Configure Kubernetes log collection with Fluent Bit for centralized log management.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, golden datasets, scoring scripts, or LLM-as-judge patterns found. No `pytest` with LLM assertions. No RAGAS or eval infrastructure.
- **Gap**: No automated evaluation capability. Not applicable until AI/agent features are added.
- **Recommendation**: Establish an eval framework when adding AI capabilities. Use Amazon Bedrock evaluation APIs or open-source tools like RAGAS.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms for latency or availability. No error budget tracking. No SLO dashboards. No `aws_cloudwatch_metric_alarm` resources in Terraform. Kubecost provides cost metrics but not SLO metrics.
- **Gap**: No SLOs defined for any tenant-facing service. No alerting on degraded performance or availability.
- **Recommendation**: Define SLOs for critical paths: producer API latency (p99 < 500ms), consumer processing latency (message-to-DynamoDB < 5s), tenant onboarding workflow completion time. Create CloudWatch alarms via Terraform.

#### OPS-Q5: Rollback Capability
- **Score**: 2/4 🟠
- **Finding**: Flux CD supports GitOps rollback via `git revert` on the main branch — reverting a commit will trigger Flux reconciliation to the previous state. Helm releases versioned at `0.0.1`. ECR images tagged with version numbers and `IMMUTABLE` tag policy. However, no automated rollback triggers, no health-check-based rollback, no feature flags, no prompt versioning.
- **Gap**: Rollback is manual (requires git revert). No automated rollback on deployment failure. No canary analysis to trigger rollback.
- **Recommendation**: Integrate Flagger with Flux CD for automated rollback based on canary analysis (error rate, latency). Add Helm rollback annotations. Consider implementing feature flags for gradual rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, cost attribution, or usage metrics. Kubecost provides infrastructure cost analysis but not LLM-specific tracking.
- **Gap**: Not applicable until LLM/AI features are added.
- **Recommendation**: When adding AI capabilities, implement token usage tracking per request with tenant attribution. Use CloudWatch custom metrics for cost monitoring.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: Kubecost deployed for infrastructure cost analysis (`gitops/infrastructure/production/05-kubecost.yaml`). No custom business metrics — no `cloudwatch.put_metric_data()`, no custom dashboards tracking message throughput, tenant activity, or SaaS business KPIs. No business outcome tracking.
- **Gap**: Only infrastructure cost metrics exist. No visibility into business-level metrics like messages processed per tenant, tenant onboarding success rate, or API error rates by tenant.
- **Recommendation**: Add CloudWatch custom metrics for: messages produced per tenant, messages consumed per tenant, consumer processing latency, tenant onboarding duration, API error rates by tenant tier.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection. No error rate alarms. No latency p99 alarms. No PagerDuty or OpsGenie integration. Metrics Server provides basic Kubernetes metrics (CPU, memory) but no application-level anomaly detection.
- **Gap**: No alerting on any application or infrastructure anomalies. Issues will only be discovered reactively.
- **Recommendation**: Enable CloudWatch anomaly detection on key metrics. Set up composite alarms for error rate + latency correlation. Integrate with PagerDuty or OpsGenie for incident notification.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Flux CD reconciles GitOps manifests directly to production. Changes pushed to the main branch are automatically applied by Flux within the reconciliation interval (1 minute). Image automation controller auto-commits new ECR image tags. No canary deployments, no blue-green deployments, no traffic shifting, no deployment health checks. No Flagger, no Argo Rollouts.
- **Gap**: All deployments go straight to production with no progressive delivery. A broken image or misconfigured Helm values affects all tenants immediately.
- **Recommendation**: Deploy Flagger alongside Flux CD for automated canary analysis. Configure ALB target group traffic shifting for gradual rollout. Add deployment health checks with automatic rollback on failure.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found in the entire repository. No `tests/` directories, no `test_*.py` files, no `pytest.ini` or `conftest.py`, no `pytest` in requirements.txt. Helm chart `application-chart/templates/tests/` directory exists but contains only `NOTES.txt`. No API test suites, no contract tests, no end-to-end tests. No test stage in any CI/CD pipeline.
- **Gap**: Complete absence of any testing. The producer→SQS→consumer→DynamoDB integration path is untested. Helm chart rendering is untested.
- **Recommendation**: Add pytest with moto/localstack for AWS service mocking. Create integration tests for: producer API → SQS message delivery, consumer SQS polling → DynamoDB write, Helm chart template rendering. Wire tests into a CI pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON) found. No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. `scripts/monitor-tenants.sh` is a manual monitoring script that polls tenant endpoints in a loop — it is not automated incident response.
- **Gap**: No incident response automation or self-healing patterns. Manual monitoring script requires human to watch output and react.
- **Recommendation**: Create structured runbooks (markdown in `/runbooks/` directory) for common incidents: tenant onboarding failure, SQS message backlog, DynamoDB throttling. Implement SSM Automation documents for self-healing (e.g., restart consumer pods on SQS backlog).

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO definition files with named owners. No observability governance documentation. No platform team tooling documentation. No per-service dashboards or alarms with ownership metadata.
- **Gap**: No ownership model for observability. No accountability for service-level or platform-level monitoring.
- **Recommendation**: Add a CODEOWNERS file mapping service directories to team owners. Create per-service SLO definitions with named owners. Document the observability stack ownership model (platform team vs. service teams).

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Not Triggered | High | — | — | — |
| Move to Containers | Not Triggered | High | — | — | — |
| Move to Open Source | Not Triggered | Medium | — | — | — |
| Move to Managed Databases | Not Triggered | Medium | — | — | — |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Low | Low | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps — standalone, no dependencies on other pathways. This is the highest priority and can begin immediately.

**Parallel Track 2**: Move to AI — can start foundational work (vector DB, embeddings) in parallel with DevOps improvements. However, full AI integration benefits from observability and testing foundations established by Modern DevOps.

**Sequential Dependencies**: Move to Modern DevOps should be prioritized first (especially CI/CD, testing, and deployment strategies) as it provides the operational foundation needed for safe AI integration. Tracing and structured logging should be in place before adding AI/LLM components.

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - OPS-Q9: Score 1/4 — Flux CD reconciles straight-to-production with no canary/blue-green deployment strategy
  - OPS-Q10: Score 1/4 — Zero test files in the entire repository; no integration, unit, or contract tests
  - OPS-Q1: Score 1/4 — No distributed tracing; no OpenTelemetry, X-Ray, or trace context propagation
- **Current State**: Strong GitOps CD foundation with Flux CD and Argo Workflows, but CI (build/test) is missing. Deployments go straight to production. No observability beyond basic Kubernetes metrics and Kubecost.
- **Target State**: Full CI/CD with build, test, canary deployment, and automated rollback. Distributed tracing across all services. Structured logging with correlation IDs. SLOs defined and monitored.
- **Key Activities**:
  1. Create a CI pipeline (CodeBuild/GitHub Actions) for building Docker images and running tests
  2. Deploy Flagger with Flux CD for canary deployments using ALB traffic shifting
  3. Add OpenTelemetry SDK to Flask microservices and deploy ADOT Collector
  4. Implement structured JSON logging with `python-json-logger` or `structlog`
  5. Add pytest integration tests with moto for AWS service mocking
  6. Define SLOs and create CloudWatch alarms for critical paths
- **Dependencies**: None — this pathway can start immediately
- **Estimated Effort**: High — involves CI pipeline creation, testing infrastructure, observability stack, and deployment strategy changes across all services
- **Roadmap Phase Alignment**: Phase 1 (CI pipeline, structured logging, basic tests) → Phase 2 (canary deployments, tracing, SLOs) → Phase 3 (anomaly detection, advanced observability)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: Low
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks or SDKs in any microservice
  - DATA-Q1: Score 1/4 — No vector database present
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI capabilities exist. Application is a traditional SaaS platform with no LLM, embedding, or agent integration.
- **Target State**: AI-powered features for tenant support, data insights, or operational automation. Vector database for semantic search. Evaluation framework for AI quality assurance.
- **Key Activities**:
  1. Add Amazon Bedrock boto3 integration for LLM capabilities
  2. Deploy a managed vector database (OpenSearch Service or Bedrock Knowledge Bases)
  3. Implement a basic RAG pipeline using tenant DynamoDB data
  4. Add evaluation framework for AI output quality
  5. Implement token usage tracking per tenant for cost attribution
- **Dependencies**: Modern DevOps foundations (observability, testing) should be in place before adding AI components for safe experimentation
- **Estimated Effort**: High — requires new data infrastructure (vector DB), new SDKs, evaluation framework, and cost tracking
- **Roadmap Phase Alignment**: Phase 3 (AI capabilities are an advanced feature built on solid foundations)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Readiness Roadmap

### Phase 1 — Containerize & Automate (Days 1–30)

Low-effort, high-impact improvements that can be completed in a single sprint:

1. **Create a CI pipeline**: Add a GitHub Actions workflow or AWS CodeBuild project for each microservice that builds Docker images, runs linting (`flake8`), and pushes to ECR. Flux image automation already handles the CD side.
2. **Add structured JSON logging**: Replace `app.logger` and `logging.basicConfig` in all microservices with `python-json-logger`. Include `tenant_id`, `service_name`, and `timestamp` in every log entry. This is a ~30-line change per service.
3. **Write initial integration tests**: Add `pytest` and `moto` to requirements.txt. Create tests for producer→SQS message sending and consumer→DynamoDB writes. Target 3-5 tests per service covering the critical paths.
4. **Enable EKS control plane logging**: Add `cluster_enabled_log_types = ["api", "audit", "authenticator"]` to the EKS module in Terraform. This is a single line change with immediate security and debugging benefits.
5. **Scope IAM policies**: Replace `AdministratorAccess` on `argo-workflows-irsa` and `tf-controller-irsa` with scoped policies listing only required actions and resources. This is the highest-impact security improvement.

### Phase 2 — Decompose & Decouple (Months 1–3)

Structural improvements that require more planning but deliver substantial value:

1. **Deploy canary deployments with Flagger**: Add Flagger HelmRelease to the Flux infrastructure manifests. Configure canary analysis for the producer and consumer services using ALB traffic shifting. Define success criteria (error rate < 1%, p99 latency < 500ms).
2. **Implement distributed tracing**: Add `opentelemetry-instrumentation-flask` and `opentelemetry-instrumentation-botocore` to all microservices. Deploy ADOT Collector as a Flux-managed HelmRelease. Configure X-Ray exporter. This enables cross-service trace correlation across the producer→SQS→consumer→DynamoDB flow.
3. **Add API authentication**: Deploy Amazon Cognito with tenant-scoped user pools. Add JWT validation middleware to Flask apps. Configure ALB authentication action with Cognito. This closes the most critical security gap.
4. **Define and monitor SLOs**: Create CloudWatch alarms for producer API latency (p99 < 500ms), consumer processing latency (message-to-DynamoDB < 5s), and tenant onboarding duration. Deploy dashboards via Terraform or Grafana.
5. **Add rate limiting**: Deploy AWS WAF with rate-based rules on the ALB. Add `flask-limiter` to microservices with per-tenant-tier rate limits.
6. **Implement resilience patterns**: Add `tenacity` for retry with exponential backoff on all boto3 calls. Configure boto3 client timeouts. Add circuit breaker patterns for external service calls.

### Phase 3 — Optimize & Scale (Months 3–6)

Advanced capabilities that unlock the full potential of the cloud-native platform:

1. **Enable HPA for all microservices**: Set `autoscaling.enabled: true` in Helm chart defaults. Deploy KEDA for SQS-based autoscaling of consumer pods. This complements Karpenter's node-level autoscaling with pod-level scaling.
2. **Deploy anomaly detection**: Enable CloudWatch anomaly detection on key metrics. Set up composite alarms. Integrate with PagerDuty/OpsGenie for incident notification.
3. **Add API versioning and documentation**: Adopt URL path versioning (`/v1/producer`). Generate OpenAPI specs from Flask routes. Publish API documentation via Swagger UI.
4. **Implement KMS encryption**: Create customer-managed KMS keys. Apply to DynamoDB tables, SQS queues, S3 buckets, and ECR repositories. Remove checkov skip annotations.
5. **Deploy service mesh (optional)**: If multi-tenant isolation and mTLS are priorities, deploy AWS App Mesh or Istio for traffic management and zero-trust networking between services.
6. **Explore AI capabilities (if prioritized)**: Begin with Amazon Bedrock integration for a tenant support agent. Deploy a managed vector database. Build a RAG pipeline using tenant DynamoDB data.

---

## Recommended Self-Paced Learning Materials

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive learning plan covering CI/CD, IaC, testing, and observability — directly addresses the top gaps in this assessment.
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundational course for building CI/CD pipelines with AWS services.
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Hands-on lab for CI/CD pipeline creation — applicable patterns for EKS with Flux CD.
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Directly addresses the OPS-Q10 gap (no integration tests) with AWS-native testing approaches.
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Directly relevant for adding observability to the Python Flask microservices.
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
  - Deep dive into CI/CD automation patterns applicable to the missing CI pipeline.
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
  - Relevant GitOps deployment automation patterns for EKS.
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
  - Advanced platform engineering patterns combining EKS and GitOps — directly relevant to this repo's architecture.
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
  - Hands-on EKS automation practices applicable to deployment strategy improvements.
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1
  - The companion workshop for this very repository — essential for understanding the architecture.

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Comprehensive AI learning path for when the Move to AI pathway is pursued.
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for adding AI capabilities to the Flask microservices via boto3.
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Relevant when exploring agent-based features for the SaaS platform.
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on RAG implementation — directly addresses DATA-Q1 and DATA-Q3 gaps.

---

## Appendix: Evidence Index

| # | File | Key Finding |
|---|------|-------------|
| 1 | `terraform/workshop/main.tf` | EKS cluster v1.32, VPC with 3 AZs, Gitea on EC2, SSM parameter for secrets, public cluster endpoint |
| 2 | `terraform/workshop/saas_gitops.tf` | Flux CD module, ConfigMap with IRSA roles, SQS queue URLs, ECR URLs, Gitea token in ConfigMap |
| 3 | `terraform/workshop/variables.tf` | Cluster version 1.32 pinned, VPC CIDR 10.35.0.0/16, Gitea config variables |
| 4 | `terraform/modules/gitops-saas-infra/main.tf` | Karpenter IRSA, Argo Workflows IRSA with AdministratorAccess, SQS queues, LB Controller IRSA, TF Controller IRSA with AdministratorAccess |
| 5 | `terraform/modules/gitops-saas-infra/apps_needs.tf` | ECR repositories with AES256 encryption, S3 buckets with public access block, microservice ECR repos |
| 6 | `terraform/modules/gitea/main.tf` | EC2 instance for Gitea, security group with specific ingress and open egress, IAM role with scoped SSM/ECR policies |
| 7 | `terraform/modules/tenant-apps/main.tf` | Per-tenant DynamoDB tables, SQS queues, IRSA roles with scoped policies, SSM parameters for service discovery |
| 8 | `terraform/modules/flux_cd/main.tf` | Flux Operator deployment, FluxInstance configuration, Kubernetes Secret with Git credentials |
| 9 | `tenant-microservices/producer/producer.py` | Flask app, SQS send_message, no auth, no rate limiting, no retry, no idempotency, unstructured logging |
| 10 | `tenant-microservices/consumer/consumer.py` | Flask app, SQS polling in background thread, DynamoDB put_item, no retry, no tracing, unstructured logging |
| 11 | `tenant-microservices/payments/payments.py` | Minimal Flask stub service, no data access, no auth, JSON responses |
| 12 | `tenant-microservices/producer/requirements.txt` | Flask 3.0.0, boto3 ~1.28.59 — no testing, tracing, or security libraries |
| 13 | `helm-charts/helm-tenant-chart/templates/ingress.yaml` | ALB Ingress with TenantID header routing, internet-facing, no WAF, no auth |
| 14 | `helm-charts/helm-tenant-chart/templates/hpa.yaml` | HPA template exists but disabled by default (autoscaling.enabled: false) |
| 15 | `helm-charts/helm-tenant-chart/templates/terraform.yaml` | TF Controller with approvePlan: auto — no human approval for infrastructure changes |
| 16 | `gitops/infrastructure/production/03-argo-workflows.yaml` | Argo Workflows with full-permissions ClusterRole, auth-mode=server (no auth), IRSA |
| 17 | `gitops/infrastructure/production/06-argo-events.yaml` | Argo Events with wildcard ClusterRole, SQS event sources for workflow triggers |
| 18 | `gitops/infrastructure/production/02-karpenter.yaml` | Karpenter v1.4.0 HelmRelease with IRSA and interruption queue |
| 19 | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` | Default NodePool with cpu/memory limits, spot + on-demand capacity types |
| 20 | `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | SQS event source, Argo Sensor triggering onboarding workflow, Git token passed as parameter |
