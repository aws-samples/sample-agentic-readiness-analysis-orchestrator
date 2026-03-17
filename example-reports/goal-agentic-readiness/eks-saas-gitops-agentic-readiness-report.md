# Agentic Readiness Assessment Report
**Target**: goal-agentic-readiness/services/eks-saas-gitops
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: agentic-readiness
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
6. Quick Agent Wins
7. Readiness Roadmap
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Advanced Capabilities (Months 3–6)
8. Recommended Self-Paced Learning Materials
9. Appendix: Evidence Index

---

## Executive Summary

This EKS SaaS GitOps monorepo demonstrates a strong infrastructure foundation — with comprehensive Terraform IaC, Flux CD GitOps automation, Karpenter auto-scaling, Argo Workflows orchestration, and a well-decomposed microservices architecture running on EKS. However, the platform has critical gaps in security (1.3/4.0), observability (1.2/4.0), and data foundations (1.9/4.0) that must be addressed before agentic workloads can be safely deployed. API endpoints lack authentication, there is no distributed tracing or structured logging, and no AI/agent frameworks are present. The most impactful modernization paths are **Move to Modern DevOps** (adding CI pipelines, progressive delivery, and observability) and **Move to AI** (introducing agent frameworks, vector databases, and RAG capabilities).

### Overall Score: 1.9 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.7 / 4.0 | 🟡 |
| Application Architecture | 2.2 / 4.0 | 🟡 |
| Data Foundations | 1.9 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.3 / 4.0 | 🟠 |
| Operations & Observability | 1.2 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

### 1. API Authentication (SEC-Q9) — Score: 1/4 ❌
**Why it matters**: Agentic workflows make autonomous API calls. Without per-request authentication, any process — including a misconfigured agent — can access any tenant's data. The current header-based tenant routing (`tenantID` header in `ingress.yaml`) can be trivially spoofed.
**First step**: Integrate Amazon Cognito as an identity provider and add a JWT authorizer to the ALB ingress or deploy API Gateway in front of the ALB with OAuth2/JWT validation.

### 2. Identity Propagation (SEC-Q3) — Score: 1/4 ❌
**Why it matters**: Agents acting on behalf of users must carry verifiable identity tokens end-to-end. Currently, `tenantID` is passed as an unverified HTTP header (`request.headers.get('tenantID')` in `producer.py`), meaning any caller can impersonate any tenant. Without JWT/OAuth token exchange, there is no way to establish trust in agent-to-service calls.
**First step**: Issue JWTs from a centralized identity provider (Cognito) and validate tokens in Flask middleware before extracting tenant context.

### 3. Distributed Tracing (OPS-Q1) — Score: 1/4 ❌
**Why it matters**: Agentic workflows span multiple services and tool calls. Without distributed tracing, you cannot reconstruct agent execution paths when failures occur. No X-Ray, OpenTelemetry, or tracing SDK was found in any `requirements.txt` or application code.
**First step**: Add `opentelemetry-api`, `opentelemetry-sdk`, and `opentelemetry-instrumentation-flask` to all microservice `requirements.txt` files and configure the ADOT collector as a DaemonSet on EKS.

### 4. API Documentation (APP-Q2) — Score: 1/4 ❌
**Why it matters**: Agents discover and invoke APIs through OpenAPI specifications. Without them, agents cannot auto-discover available operations, parameter schemas, or response formats. No OpenAPI/Swagger specs exist for any of the three microservices.
**First step**: Add `flask-smorest` or `flask-apispec` to generate OpenAPI 3.0 specs from the existing Flask routes in `producer.py`, `consumer.py`, and `payments.py`.

### 5. Resilience Patterns (APP-Q9) — Score: 1/4 ❌
**Why it matters**: Agents retry failed tool calls. Without circuit breakers, timeouts, and explicit retry policies, a failing downstream service can cascade through the entire agent workflow. Currently, all boto3 clients in the microservices use default retry config with no application-level resilience patterns.
**First step**: Add `tenacity` for retry with exponential backoff and configure explicit timeouts on all boto3 client calls (SQS, DynamoDB, SSM) in each microservice.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: EKS cluster defined in `terraform/workshop/main.tf` with managed node groups (`m5.large`, min 3, max 5). Karpenter v1.4.0 deployed via `gitops/infrastructure/production/02-karpenter.yaml` with two NodePools (`default` and `application`) in `gitops/infrastructure/production/dependencies/`. All three microservices (producer, consumer, payments) run as containers on EKS. However, Gitea runs on a standalone EC2 instance (`terraform/modules/gitea/main.tf` — `aws_instance.gitea`, m5.large).
- **Gap**: Gitea server runs on a single EC2 instance rather than a managed container or managed service. This is the only non-containerized compute.
- **Recommendation**: Migrate Gitea to run as a container on EKS or evaluate AWS CodeCommit/CodeCatalyst as a managed replacement for the self-hosted Git server.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: DynamoDB used as the primary data store for consumer microservice, defined in `terraform/modules/tenant-apps/main.tf` (`aws_dynamodb_table.consumer_ddb` with PAY_PER_REQUEST billing and point-in-time recovery enabled). DynamoDB is fully managed with automated failover. Gitea uses embedded SQLite internally (via docker-compose in userdata.sh). No RDS, Aurora, or self-managed database engines detected on EC2 or containers.
- **Gap**: Gitea's embedded SQLite is a self-managed database running on EC2, though it serves infrastructure tooling rather than application workloads.
- **Recommendation**: For production, consider migrating Gitea to use Amazon RDS (PostgreSQL) as its backend database, or move to a managed Git service to eliminate the self-managed database dependency entirely.

#### INF-Q3: Workflow Orchestration
- **Score**: 4/4 ✅
- **Finding**: Argo Workflows v0.40.11 deployed via `gitops/infrastructure/production/03-argo-workflows.yaml` with dedicated service account and IRSA. Three WorkflowTemplates defined for tenant operations: `tenant-onboarding-workflow-template.yaml`, `tenant-offboarding-workflow-template.yaml`, `tenant-deployment-workflow-template.yaml` in `gitops/control-plane/production/workflows/`. Multi-step orchestration with sequential steps (clone → validate → create/update/remove). Argo Events v2.4.3 deployed via `06-argo-events.yaml` with SQS EventSources and Sensors for event-driven workflow triggering. EventBus with NATS (3 replicas) in `event-bus.yaml`.
- **Gap**: None. Dedicated workflow orchestration is in place.
- **Recommendation**: Consider adding Step Functions for AWS-native workflow orchestration alongside Argo Workflows to provide additional resilience for cross-account operations.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: SQS queues extensively used: control-plane queues (`argoworkflows-onboarding-queue`, `argoworkflows-offboarding-queue`, `argoworkflows-deployment-queue`) in `terraform/modules/gitops-saas-infra/main.tf`; per-tenant consumer queues (`consumer-{tenant_id}`) in `terraform/modules/tenant-apps/main.tf`. All queues have `sqs_managed_sse_enabled = true`. Producer sends to SQS (`producer.py`), consumer polls from SQS (`consumer.py`). Argo Events EventBus uses NATS for internal eventing.
- **Gap**: None. Managed messaging (SQS) is the primary inter-service communication pattern.
- **Recommendation**: Maintain current SQS-based architecture. Consider adding dead-letter queues (DLQ) for all SQS queues to capture failed messages.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: Comprehensive Terraform coverage across four modules: `terraform/workshop/` (VPC, EKS, Gitea), `terraform/modules/gitops-saas-infra/` (IAM, SQS, S3, ECR, Karpenter IRSA), `terraform/modules/tenant-apps/` (per-tenant SQS, DynamoDB, IAM), `terraform/modules/flux_cd/` (Flux operator). GitOps layer via Flux CD (Kustomize + HelmReleases) in `gitops/`. TF Controller (`07-tf-controller.yaml`) enables Kubernetes-native Terraform provisioning for per-tenant infrastructure. Helm charts in `helm-charts/` for application and tenant deployments.
- **Gap**: None. >90% of infrastructure is defined in IaC (Terraform + GitOps).
- **Recommendation**: Consider adding Terraform state locking documentation and establish module versioning strategy for the custom Terraform modules.

#### INF-Q6: CI/CD
- **Score**: 2/4 🟠
- **Finding**: Strong CD automation via Flux CD image automation — `producer-image-automation.yaml`, `consumer-image-automation.yaml`, `payments-image-automation.yaml` in `gitops/infrastructure/base/sources/` — which automatically update image tags in Git when new images are pushed to ECR. Argo Workflows automate tenant lifecycle operations. However, no CI pipeline definitions found: no GitHub Actions workflows, no Jenkinsfile, no `buildspec.yml`, no CodePipeline. The Gitea Actions runner is configured in `userdata.sh` but no workflow definitions (`.gitea/workflows/`) with build/test stages were found in the microservice directories.
- **Gap**: No automated build or test pipeline. Container images must be built and pushed manually or via an undefined external process. The `.gitea/` directories in each microservice exist but contain no workflow definitions with test stages.
- **Recommendation**: Create Gitea Actions workflows or AWS CodeBuild/CodePipeline definitions that build, run tests, scan images, and push to ECR. Define CI pipeline as code alongside the existing CD automation.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: AWS ALB Ingress Controller v1.6.2 deployed via `gitops/infrastructure/production/04-lb-controller.yaml`. Per-tenant ALB ingress rules with header-based routing defined in `helm-charts/helm-tenant-chart/templates/ingress.yaml` — routes requests based on `TenantID` HTTP header. ALB configured with health checks (`alb.ingress.kubernetes.io/healthcheck-path`). All tenants share a single ALB group (`tenants-lb`).
- **Gap**: No throttling, authentication, or request validation at the gateway level. No API Gateway (HTTP API or REST API) deployed. No WAF rules attached to the ALB. ALB only performs routing, not API management.
- **Recommendation**: Deploy Amazon API Gateway (HTTP API) in front of the ALB with JWT authorizer, throttling, and request validation. Alternatively, attach AWS WAF to the ALB with rate limiting rules as a quick win.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, MSK (Managed Streaming for Apache Kafka), or managed streaming services detected in Terraform IaC or GitOps configurations. SQS is used for messaging (point-to-point), not streaming. No Kafka, Flink, or streaming consumer patterns in application code.
- **Gap**: No real-time streaming capability exists. If real-time event processing is needed for agentic workloads (e.g., streaming tenant activity for agent context), there is no infrastructure to support it.
- **Recommendation**: If real-time streaming is required for agent context (e.g., live tenant activity feeds), add Amazon Kinesis Data Streams or MSK Serverless. If not needed, this gap is low priority.

#### INF-Q9: Network Security
- **Score**: 2/4 🟠
- **Finding**: VPC with public and private subnets across 3 AZs defined in `terraform/workshop/main.tf` using `terraform-aws-modules/vpc/aws` v4.0.2. EKS nodes run in private subnets. Gitea security group (`terraform/modules/gitea/main.tf`) has specific CIDR-based ingress rules for SSH, HTTP, and EKS access. VPC peering configured for VSCode access. However: EKS cluster endpoint is public (`cluster_endpoint_public_access = true` in main.tf). Gitea SG egress rule allows all traffic to `0.0.0.0/0`. Single NAT Gateway (`single_nat_gateway = true`) creates a single point of failure.
- **Gap**: Public EKS API endpoint, overly broad egress rules, and single NAT Gateway. No NACLs configured explicitly. No PrivateLink endpoints for AWS services.
- **Recommendation**: Set `cluster_endpoint_public_access = false` and use VPC endpoints or bastion host for cluster access. Restrict Gitea egress to required destinations. Add VPC endpoints for SQS, DynamoDB, ECR, and S3 to keep traffic within the VPC.

#### INF-Q10: Auto-scaling
- **Score**: 2/4 🟠
- **Finding**: Karpenter v1.4.0 provides node-level auto-scaling with two NodePools: `default` (general workloads) and `application` (with taints for application pods) in `gitops/infrastructure/production/dependencies/`. Both have `consolidationPolicy: WhenEmptyOrUnderutilized` with 1-minute consolidation. EKS managed node group has min 3, max 5. HPA templates exist in both Helm charts (`helm-charts/helm-tenant-chart/templates/hpa.yaml` and `helm-charts/application-chart/templates/hpa.yaml`), but `autoscaling.enabled: false` in `values.yaml.template`.
- **Gap**: Pod-level auto-scaling (HPA) is disabled for all application deployments despite templates being defined. Node-level scaling via Karpenter is well-configured but without HPA, pods cannot scale independently.
- **Recommendation**: Enable HPA for producer and consumer deployments by setting `autoscaling.enabled: true` in Helm values. Consider VPA (Vertical Pod Autoscaler) for right-sizing resource requests. Set appropriate CPU/memory targets based on load testing.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 4/4 ✅
- **Finding**: Python (Flask 3.0.0) is the primary language for all three microservices: `producer.py`, `consumer.py`, `payments.py`. Dependencies managed via `requirements.txt` in each service directory. Python 3.9.17-slim base image used in all Dockerfiles. Python has the best agent framework ecosystem (boto3 Bedrock, langchain, strands-agents, crewai).
- **Gap**: None. Python is an ideal language for agentic workloads.
- **Recommendation**: Consider upgrading base Docker images from Python 3.9 (approaching end of security support) to Python 3.11 or 3.12 for performance improvements and continued security patches.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI or Swagger specifications found anywhere in the repository. No API documentation annotations in Flask code. Flask apps expose simple routes (`/producer`, `/consumer`, `/payments`) without any documentation generation library. No `openapi.yaml`, `swagger.json`, or API spec files detected.
- **Gap**: Agents cannot auto-discover API capabilities. All three microservices lack machine-readable API documentation.
- **Recommendation**: Add `flask-smorest` or `apiflask` to generate OpenAPI 3.0 specs from existing Flask routes. Document request/response schemas, authentication requirements, and error codes.

#### APP-Q3: Async vs Sync Communication
- **Score**: 3/4 🟡
- **Finding**: Strong async patterns for inter-service communication: producer sends messages to SQS (`sqs_client.send_message` in `producer.py`), consumer polls SQS and writes to DynamoDB (`consumer.py`). Tenant onboarding is fully event-driven: SQS → Argo Events Sensor → Argo Workflows. However, Flask HTTP endpoints (GET/POST) are synchronous request/response. The consumer runs a background thread (`Thread(target=process_messages).start()`) for async message processing.
- **Gap**: HTTP endpoints are synchronous. No async web framework (e.g., FastAPI with async/await) used.
- **Recommendation**: Consider migrating from Flask to FastAPI for async HTTP handling and built-in OpenAPI generation. The SQS-based async patterns are already well-established.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three independent microservices (producer, consumer, payments), each with its own Dockerfile, `requirements.txt`, deployment manifest, service account (IRSA), and ingress rules. Per-tenant isolation via Kubernetes namespaces (premium tenants) or shared pool (basic tenants). Clear service boundaries: producer handles message publishing, consumer handles message processing and DynamoDB persistence, payments handles payment operations. Services communicate via SQS (async), not direct HTTP calls.
- **Gap**: None. Well-decomposed microservices with clear boundaries and independent deployment.
- **Recommendation**: Maintain current microservice architecture. Document service boundaries and ownership as the number of services grows.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All Flask endpoints return Python dictionaries, which Flask automatically serializes to JSON. Examples: `producer.py` returns `{"tenant_id": ..., "environment": ..., "version": ..., "microservice": ...}`. `consumer.py` returns similar JSON structures. `payments.py` returns JSON dict. All responses are structured JSON.
- **Gap**: None. All APIs return structured JSON responses.
- **Recommendation**: Define explicit JSON schemas for response objects to enable agent validation of responses.

#### APP-Q6: Workflow Logic
- **Score**: 3/4 🟡
- **Finding**: Argo Workflows with WorkflowTemplates handle tenant lifecycle operations: onboarding (`tenant-onboarding-workflow-template.yaml`), offboarding (`tenant-offboarding-workflow-template.yaml`), and deployment (`tenant-deployment-workflow-template.yaml`). Multi-step orchestration with sequential steps and shared volume mounts. Workflow mutex synchronization (`synchronization.mutex.name: workflow`) prevents concurrent conflicting operations.
- **Gap**: Business logic within microservices (message processing, data persistence) is not orchestrated — it uses direct imperative code. Only control-plane operations use workflow orchestration.
- **Recommendation**: Consider using Step Functions or Argo Workflows for complex business logic that may emerge as the application grows. Current approach is acceptable for the existing simple business logic.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys, deduplication IDs, or safe retry patterns found. `producer.py` calls `sqs_client.send_message()` without `MessageDeduplicationId`. `consumer.py` performs `ddb_client.put_item()` without conditional writes or idempotency checks — if the same message is processed twice, it will overwrite silently. No idempotency-key headers in API specs.
- **Gap**: Critical write APIs lack idempotency protection. SQS standard queues can deliver messages more than once, and without idempotency in the consumer, duplicate processing will occur.
- **Recommendation**: Add `MessageDeduplicationId` to SQS send calls (or switch to FIFO queues). Implement conditional writes in DynamoDB using `ConditionExpression` to prevent duplicate processing. Add idempotency-key support in producer POST endpoint.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting middleware in any Flask application. No `flask-limiter` or equivalent in `requirements.txt`. ALB ingress annotations in `helm-charts/helm-tenant-chart/templates/ingress.yaml` contain no throttling configuration. No WAF rules configured in Terraform. No API Gateway with usage plans or throttling.
- **Gap**: APIs are completely unprotected against abuse. An agent making rapid-fire calls could overwhelm downstream services.
- **Recommendation**: Add `flask-limiter` middleware to all Flask apps with per-tenant rate limits. Attach AWS WAF with rate-based rules to the ALB. Long-term, deploy API Gateway with usage plans and per-client throttling.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, explicit retry policies, or timeout configurations in any microservice code. `producer.py` and `consumer.py` use default boto3 retry config (standard mode, 3 retries). No `tenacity`, `backoff`, or similar retry libraries in `requirements.txt`. No explicit timeouts on SQS `receive_message` calls (only `WaitTimeSeconds=20` for long polling, not a timeout). Flask runs without request timeout configuration. Exception handling is generic `except Exception as e` with logging only.
- **Gap**: No resilience patterns implemented. All external dependency calls (SQS, DynamoDB, SSM) rely on boto3 defaults with no application-level protection.
- **Recommendation**: Add `tenacity` for retry with exponential backoff on all AWS service calls. Configure explicit timeouts on boto3 clients. Implement circuit breaker pattern using `pybreaker` for external service calls. Add health check degradation when dependencies fail.

#### APP-Q10: Long-running Processes
- **Score**: 3/4 🟡
- **Finding**: Tenant onboarding/offboarding is handled asynchronously via SQS → Argo Events → Argo Workflows pipeline. Consumer runs a background thread (`Thread(target=process_messages)`) for continuous SQS polling and DynamoDB writes, keeping HTTP handlers lightweight. No long-running synchronous operations detected in Flask request handlers — POST `/producer` only performs a single SQS send and returns.
- **Gap**: The consumer's background thread approach is basic — no task queue framework (Celery, Bull) for more complex async processing.
- **Recommendation**: Current approach is acceptable for the simple workload. If async processing complexity grows, consider migrating to a proper task queue framework or Lambda-based event processing.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL path versioning (`/v1/`, `/v2/`) in any Flask route definitions. No version headers or query parameters. `ms_version = "0.0.1"` is defined as a variable in `producer.py` and `consumer.py` (returned in GET responses) but not used for routing or compatibility. `payments.py` uses `ms_version = "1.0.0"`. No changelog files or versioning strategy documentation.
- **Gap**: No API versioning strategy. Breaking changes to API contracts will affect all consumers simultaneously.
- **Recommendation**: Implement URL path versioning (e.g., `/v1/producer`, `/v1/consumer`) and document backward compatibility guarantees. This is critical for agent integration — agents depend on stable API contracts.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Services communicate via SQS (not direct HTTP), so traditional service discovery is less critical. Kubernetes ClusterIP services provide internal DNS resolution. SSM Parameter Store used for dynamic configuration (`/{tenant_id}/consumer_sqs`, `/{tenant_id}/consumer_ddb` parameters looked up at runtime in `producer.py` and `consumer.py`). No service mesh (App Mesh, Istio) deployed. No API catalog or service registry.
- **Gap**: No service mesh for observability, traffic management, or mTLS. No centralized API catalog for agent tool discovery.
- **Recommendation**: Deploy AWS App Mesh or Istio for mTLS, traffic management, and observability. Create a centralized API catalog (e.g., using API Gateway) that agents can query to discover available services.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports found in any microservice. `requirements.txt` files contain only Flask, boto3/botocore, and standard utilities. No `langchain`, `langgraph`, `strands-agents`, `openai`, `anthropic`, or `bedrock` SDK imports. No MCP server/client patterns. No Bedrock API calls.
- **Gap**: No AI or agent framework integration exists anywhere in the codebase.
- **Recommendation**: Start with Amazon Bedrock integration via boto3 (`bedrock-runtime` client). Evaluate `strands-agents` SDK for building agents that interact with existing microservices as tools. The Python-based architecture makes this straightforward.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database detected in Terraform IaC or GitOps configurations. No OpenSearch with k-NN plugin, no Aurora pgvector, no S3 Vectors, no Bedrock Knowledge Bases. No Pinecone, Weaviate, or Chroma imports in `requirements.txt` files.
- **Gap**: No vector storage capability exists. Agents requiring semantic search or RAG cannot function.
- **Recommendation**: Deploy Amazon OpenSearch Service with k-NN plugin or use Amazon Bedrock Knowledge Bases for managed vector storage. For quick experimentation, start with Bedrock Knowledge Bases backed by S3.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database present (managed or self-hosted). No references to any vector store infrastructure.
- **Gap**: No vector DB to manage.
- **Recommendation**: When deploying a vector database (per DATA-Q1), use a fully managed service (OpenSearch Service, Bedrock Knowledge Bases) to avoid operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No embedding model calls (Bedrock Titan, OpenAI ada), no chunking/splitting code, no similarity search or knn_search patterns found in any Python file. No Bedrock Knowledge Base integration. No document processing pipeline.
- **Gap**: No RAG pipeline exists. Agents cannot perform semantic search over knowledge bases.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases with S3 as the data source. Use Titan Embeddings for vector generation and OpenSearch Service for retrieval.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Two primary data sources per tenant: SQS queues (message transport) and DynamoDB tables (message persistence), both defined in `terraform/modules/tenant-apps/main.tf`. SSM Parameter Store serves as configuration storage for queue URLs and table ARNs. Data sources are well-contained and consistent across tenants.
- **Gap**: While data sources are contained, each tenant gets dedicated resources (SQS + DynamoDB), which creates operational multiplicity as tenants scale. No unified data access abstraction.
- **Recommendation**: Maintain current contained data source approach. Consider a unified data access layer as the number of data sources grows.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Direct AWS SDK calls throughout microservice code. `producer.py` directly calls `sqs_client.send_message()` and `ssm_client.get_parameter()`. `consumer.py` directly calls `sqs_client.receive_message()`, `ddb_client.put_item()`, and `sqs_client.delete_message()`. No repository pattern, no data access abstraction layer, no ORM.
- **Gap**: Database clients instantiated and used directly in business logic. No abstraction between business logic and data access.
- **Recommendation**: Implement a repository/DAO pattern to abstract DynamoDB and SQS access. This creates clean tool interfaces for agents to interact with data through well-defined APIs rather than direct database connections.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: S3 buckets exist for Argo artifacts (`terraform/modules/gitops-saas-infra/main.tf` — `aws_s3_bucket.argo_artifacts`) and code artifacts (`aws_s3_bucket.codeartifacts`). Both have public access blocked. However, no document parsing libraries (Textract, Tika, PyPDF) detected. No unstructured data processing pipeline.
- **Gap**: S3 storage exists but only for operational artifacts. No unstructured data processing capability for agent knowledge bases.
- **Recommendation**: If tenant documents need to be processed for agent context, add Amazon Textract integration and S3 event-driven processing (Lambda or Step Functions) to extract and index document content.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table schema defined in Terraform (`terraform/modules/tenant-apps/main.tf`): `consumer_ddb` with `tenant_id` (String, hash key) and `message_id` (String, range key). Additional attributes (`producer_environment`, `consumer_environment`, `timestamp`) are written in code but not in the schema definition. No JSON Schema files, no Avro/Protobuf definitions, no schema registry.
- **Gap**: Schema is partially documented in IaC but not versioned independently. Additional item attributes are only discoverable by reading application code.
- **Recommendation**: Create explicit JSON Schema definitions for all DynamoDB item structures. Version schema definitions alongside the Terraform modules. Document the full attribute set including non-key attributes.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. DynamoDB calls in `consumer.py` (`ddb_client.put_item()`), SQS calls scattered across `producer.py` (`sqs_client.send_message()`) and `consumer.py` (`sqs_client.receive_message()`, `sqs_client.delete_message()`). SSM Parameter Store calls in both services. Each service directly instantiates boto3 clients at module level.
- **Gap**: No centralized data access abstraction. Each service implements its own data access patterns independently.
- **Recommendation**: Create a shared data access module (Python package) with repository classes for DynamoDB, SQS, and SSM operations. This becomes the foundation for agent tool definitions — each repository method maps to an agent tool.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings or vector data present in the system. No embedding refresh triggers, no scheduled re-indexing pipelines, no CDC (Change Data Capture) patterns for DynamoDB streams.
- **Gap**: No embedding infrastructure exists to maintain or refresh.
- **Recommendation**: When implementing RAG (per DATA-Q3), enable DynamoDB Streams to trigger Lambda functions that update embeddings when data changes. Use Bedrock Knowledge Base sync for automated embedding refresh.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is the only application database, defined in `terraform/modules/tenant-apps/main.tf`. DynamoDB is serverless and fully managed — no engine version to pin, no EOL concerns. No RDS, Aurora, or ElastiCache instances detected in any Terraform module.
- **Gap**: None. DynamoDB has no version/EOL concerns.
- **Recommendation**: No action required. Continue using DynamoDB serverless.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No SQL files, stored procedures, triggers, or proprietary SQL constructs detected in the repository. DynamoDB is NoSQL — no stored procedures or triggers at the database level. All business logic resides in application code (`producer.py`, `consumer.py`, `payments.py`).
- **Gap**: None. All business logic is in the application layer.
- **Recommendation**: No action required. Continue keeping business logic in application code.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: SSM Parameter Store `SecureString` used for Gitea admin password (`terraform/workshop/main.tf` — `aws_ssm_parameter.gitea_password`) and Gitea Flux token (`/eks-saas-gitops/gitea-flux-token`). Kubernetes secrets used for Flux Git credentials (`terraform/modules/flux_cd/main.tf` — `kubernetes_secret.flux_system`). Code comment explicitly notes: `# checkov:skip=CKV_AWS_337: Skiping this for now, move to Secrets Manager.` Git tokens passed as workflow parameters in Argo Workflow templates (`GIT_TOKEN` env var in all workflow templates).
- **Gap**: No AWS Secrets Manager usage. Git tokens passed as plaintext environment variables in Argo Workflow containers. Team has acknowledged need to migrate to Secrets Manager but has not done so.
- **Recommendation**: Migrate secrets from SSM SecureString to AWS Secrets Manager with automatic rotation. Replace plaintext `GIT_TOKEN` workflow parameters with Kubernetes External Secrets Operator pulling from Secrets Manager.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: Good per-tenant IRSA roles with specific action lists: `producer-policy-{tenant_id}` with only `sqs:SendMessage` and `ssm:GetParameter` (`terraform/modules/tenant-apps/main.tf`); `consumer-policy-{tenant_id}` with specific SQS and DynamoDB actions. However, multiple overly permissive policies: `argo_workflows_eks_role` uses `AdministratorAccess` (`terraform/modules/gitops-saas-infra/main.tf`); `tf_controller_irsa_role` uses `AdministratorAccess`; `karpenter-policy` has `Resource: "*"` on 20+ EC2/IAM actions; `lb-controller-irsa-policy` has `Resource: "*"` on many statements; Kubernetes ClusterRoles for Argo Workflows and Argo Events grant `apiGroups: ["*"], resources: ["*"], verbs: ["*"]` (`03-argo-workflows.yaml`, `06-argo-events.yaml`).
- **Gap**: Control-plane IAM policies are excessively permissive. Two AdministratorAccess policies and wildcard Kubernetes ClusterRoles create significant blast radius.
- **Recommendation**: Replace `AdministratorAccess` on Argo Workflows and TF Controller roles with least-privilege policies scoped to specific resources. Scope Kubernetes ClusterRoles to only the API groups and resources needed. Use IAM Access Analyzer to identify minimum required permissions.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Tenant identity passed via unverified HTTP header (`request.headers.get("tenantID")` in `producer.py`, `consumer.py`, `payments.py`). ALB ingress routes based on `TenantID` header value (`helm-charts/helm-tenant-chart/templates/ingress.yaml`). No JWT/OAuth token exchange. No Cognito, Okta, or OIDC integration for end-user identity. Headers are not validated for authenticity — any caller can set any `tenantID` header.
- **Gap**: Tenant identity is trivially spoofable. No cryptographic verification of caller identity. No user context propagated across service boundaries.
- **Recommendation**: Implement Amazon Cognito user pools with per-tenant JWT tokens. Validate JWTs at the ALB (using OIDC action) or API Gateway. Extract tenant context from verified JWT claims instead of raw headers.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No `aws_cloudtrail` resource in any Terraform module. No CloudTrail configuration detected. No S3 bucket designated for audit logs. No log file validation. README mentions CloudWatch integration but no CloudWatch log groups or retention policies defined in IaC. EKS audit logging configuration not found in the EKS module.
- **Gap**: No audit trail for API calls, infrastructure changes, or data access. Critical for compliance and incident investigation with agentic workloads.
- **Recommendation**: Enable AWS CloudTrail with log file validation and S3 bucket with object lock for immutable storage. Enable EKS audit logging via cluster `logging` configuration. Set CloudWatch log retention policies.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. No API Gateway throttle settings. No WAF rate-based rules. No `flask-limiter` or equivalent middleware in any microservice. ALB ingress annotations contain no rate limiting configuration. No per-tenant or per-client quotas.
- **Gap**: APIs are completely unprotected against abuse, denial-of-service, or runaway agent loops.
- **Recommendation**: Attach AWS WAF with rate-based rules to the ALB as an immediate fix. Deploy API Gateway with usage plans for per-tenant throttling. Add `flask-limiter` as a defense-in-depth measure.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII masking or scrubbing in application logging. `producer.py` logs full message content: `app.logger.info(f"Message produced: {message}")`. `consumer.py` logs message IDs and table names: `logger.info(f"Message [{message_id}] persisted in DDB table: {ddb_table_name}")`. Tenant IDs logged in plaintext. No log scrubbing middleware. No Amazon Macie enabled.
- **Gap**: Tenant identifiers and message content logged without redaction. No PII detection or masking pipeline.
- **Recommendation**: Implement structured logging with PII field masking. Add a log scrubbing middleware that redacts sensitive fields before output. Enable Amazon Macie for S3-stored data. Consider CloudWatch log data protection policies.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval gates in any workflow. Argo Workflows execute automatically upon SQS trigger — tenant onboarding, offboarding, and deployment proceed without human review. TF Controller has `approvePlan: auto` in `helm-charts/helm-tenant-chart/templates/terraform.yaml`, meaning Terraform plans auto-apply without approval. No manual approval stages in CI/CD.
- **Gap**: High-risk operations (tenant deletion, infrastructure changes, deployments) execute without human approval. An agent triggering these workflows could cause unintended damage.
- **Recommendation**: Add human approval steps for destructive operations: change TF Controller to `approvePlan: manual` for production. Add Argo Workflows `suspend` step before offboarding. Implement approval gates for production deployments.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: SQS queues encrypted with SSE (`sqs_managed_sse_enabled = true` in `terraform/modules/tenant-apps/main.tf` and `gitops-saas-infra/main.tf`). ECR repositories use AES256 encryption (`apps_needs.tf`). Gitea EC2 root EBS encrypted (`encrypted = true` in `terraform/modules/gitea/main.tf`). S3 buckets use default encryption. DynamoDB has no explicit encryption config (uses AWS-managed encryption by default). No customer-managed KMS keys (`aws_kms_key`) anywhere.
- **Gap**: All encryption uses AWS-managed keys rather than customer-managed KMS keys. Checkov skip comments acknowledge: `# checkov:skip=CKV2_AWS_145: This S3 bucket does not required a KMS Encryption`.
- **Recommendation**: Create customer-managed KMS keys for sensitive data stores (DynamoDB, S3, SQS). Enable KMS encryption on DynamoDB tables and S3 buckets used for data. Implement key rotation policies.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No authentication mechanism on any Flask endpoint. No OAuth2, JWT validation, API keys, or Bearer token middleware. Argo Workflows server explicitly configured with `--auth-mode=server` (unauthenticated access) with comment "This is for demonstration purposes only" in `03-argo-workflows.yaml`. ALB ingress performs header-based routing but no authentication. Any HTTP client can access all APIs.
- **Gap**: Critical security gap — all APIs are unauthenticated. The Argo Workflows UI/API is internet-facing (LoadBalancer service type with `internet-facing` annotation) and unauthenticated.
- **Recommendation**: Immediately restrict Argo Workflows server to internal access (`service.beta.kubernetes.io/aws-load-balancer-scheme: "internal"`). Implement JWT authentication on all Flask endpoints using Flask-JWT-Extended or a custom middleware. Deploy API Gateway with Cognito authorizer for external-facing APIs.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider configured. No Amazon Cognito user pools, no Okta, no OIDC federation, no SAML. IRSA (IAM Roles for Service Accounts) is used for service-to-AWS authentication, which is good for workload identity, but no end-user identity management exists. No SSO configuration.
- **Gap**: No centralized identity management for end users or tenant administrators. Each tenant is identified only by an unverified HTTP header.
- **Recommendation**: Deploy Amazon Cognito with user pools per tenant (or a single pool with custom attributes for tenant isolation). Implement OIDC federation for the ALB. This becomes the foundation for agent-level identity and authorization.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, or any tracing SDK found in any `requirements.txt` file. No trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`) in application code. No ADOT collector, Jaeger, or Zipkin deployment in GitOps configurations. No `gen_ai.*` semantic conventions. No service mesh providing automatic tracing.
- **Gap**: Complete absence of distributed tracing. Cannot trace requests across producer → SQS → consumer → DynamoDB flow. Agent execution paths will be invisible.
- **Recommendation**: Add OpenTelemetry SDK to all microservices: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-flask`, `opentelemetry-instrumentation-boto3`, `opentelemetry-instrumentation-botocore`. Deploy ADOT collector as a DaemonSet on EKS. Export traces to AWS X-Ray.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: Consumer uses `logging.basicConfig(stream=sys.stdout)` with default text format (`consumer.py`). Producer uses Flask's built-in logger (`app.logger.info`). No JSON log formatters (no `structlog`, no `python-json-logger`). No correlation IDs passed between services. No request IDs in log output. Logs are unstructured text.
- **Gap**: Logs cannot be efficiently queried or correlated across services. No correlation IDs link producer messages to consumer processing.
- **Recommendation**: Add `python-json-logger` or `structlog` to all microservices. Include correlation IDs (SQS message ID), tenant ID, and trace ID in every log entry. Configure CloudWatch Log Insights queries for multi-service debugging.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No eval datasets, scoring scripts, or LLM evaluation framework found anywhere in the repository. No AI testing infrastructure. No golden datasets. No A/B testing for prompts. No RAGAS or similar eval tools.
- **Gap**: No agent evaluation pipeline exists. When agents are introduced, there will be no way to measure their quality or prevent regressions.
- **Recommendation**: When implementing AI agents (per Move to AI pathway), establish an evaluation framework from day one. Use RAGAS for RAG evaluation. Create golden datasets for expected agent behaviors. Integrate eval runs into CI/CD pipeline.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found in code, configuration, or IaC. No CloudWatch alarms on latency or error rates. Kubecost deployed via `gitops/infrastructure/production/05-kubecost.yaml` provides cost visibility but no SLO monitoring. Prometheus deployed within Kubecost for infrastructure metrics scraping (1-minute intervals) but no custom alerting rules defined.
- **Gap**: No SLOs defined for any service. No availability or latency targets. No error budget tracking.
- **Recommendation**: Define SLOs for all three microservices: availability (99.9%), p99 latency (<500ms), error rate (<1%). Create CloudWatch alarms or Prometheus alerting rules to monitor SLO compliance. Use CloudWatch Synthetics for synthetic monitoring.

#### OPS-Q5: Rollback Capability
- **Score**: 2/4 🟠
- **Finding**: Flux CD GitOps provides git-based rollback (revert commits to roll back deployments). Helm charts versioned in ECR with immutable tags. Flux image automation updates tags in Git, creating an auditable deployment history. However, no automated rollback triggers (no health-check-based rollback). No canary or blue/green deployment config. No feature flags for gradual rollout.
- **Gap**: Rollback is possible but manual (requires git revert). No automated rollback on deployment failure. No progressive delivery mechanism.
- **Recommendation**: Implement Flagger or Argo Rollouts for automated canary deployments with rollback triggers. Define health check criteria that trigger automatic rollback on failure. Consider feature flags (AWS AppConfig) for controlled rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage anywhere in the codebase. No token counting, no cost attribution, no usage tracking. No CloudWatch custom metrics for LLM-related operations. No tiered retention policies for observability data.
- **Gap**: No LLM cost tracking infrastructure. When agents are introduced, there will be no way to track token usage or attribute costs.
- **Recommendation**: When implementing AI agents, add per-request token counting from LLM response `usage` objects. Publish CloudWatch custom metrics for tokens consumed per tenant/workflow. Implement tiered log retention policies.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics for business outcomes. No `cloudwatch.put_metric_data` calls in any microservice code. Kubecost provides infrastructure cost metrics only (CPU, memory, network costs per pod/namespace). No business KPI dashboards (messages produced per tenant, onboarding success rate, processing latency).
- **Gap**: Only infrastructure metrics are tracked. No visibility into business outcomes or tenant-level performance.
- **Recommendation**: Add CloudWatch custom metrics for: messages produced per tenant (producer), messages processed per tenant (consumer), tenant onboarding/offboarding success rate (Argo Workflows), end-to-end message processing latency. Build CloudWatch dashboards for tenant-level visibility.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection configured. No alerting rules in Terraform or GitOps. Prometheus is deployed via Kubecost but no custom alert rules defined (only default Kubecost metrics). No PagerDuty, OpsGenie, or SNS notification integration for alerts.
- **Gap**: No anomaly detection or alerting. Service degradation will go unnoticed until users report issues.
- **Recommendation**: Enable CloudWatch anomaly detection on SQS queue depth, DynamoDB throttle events, and ALB error rates. Create composite alarms for multi-signal detection. Integrate with SNS/PagerDuty for notification.

#### OPS-Q9: Deployment Strategy
- **Score**: 2/4 🟠
- **Finding**: Flux CD GitOps provides Kubernetes default rolling update strategy for all Deployments (`helm-charts/application-chart/templates/deployment.yaml`, `helm-charts/helm-tenant-chart/templates/deployment.yaml`). No explicit deployment strategy is defined in the Helm templates, so Kubernetes defaults to `RollingUpdate`. Flux image automation (`producer-image-automation.yaml`, `consumer-image-automation.yaml`, `payments-image-automation.yaml`) automatically updates image tags in Git when new images are pushed to ECR, triggering rolling updates. Karpenter node provisioning supports graceful node rollout via `disruption` policies. However, no canary deployments, no blue/green strategy, no Flagger, no Argo Rollouts, no Lambda traffic shifting, no ALB weighted target groups, and no feature flags for gradual rollout.
- **Gap**: No progressive delivery mechanism. All deployments go straight to production via rolling update — there is no canary analysis, no traffic splitting, no automated rollback based on error rate or latency thresholds. No feature flags for controlled rollout of new functionality.
- **Recommendation**: Deploy Flagger or Argo Rollouts alongside Flux CD for canary deployments with automatic rollback. Configure canary analysis using Prometheus metrics (error rate, latency p99) with progressive traffic shifting (10% → 25% → 50% → 100%). Add AWS AppConfig for feature flags to decouple deployment from release.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test directories found in any microservice directory. No `pytest`, `unittest`, or test framework imports. No `tests/` directory. No Postman/Newman collections. No contract tests. `terraform/gitea-ci-test/` exists but contains infrastructure for CI testing, not application test suites. No test stage in any CI/CD pipeline definition.
- **Gap**: Zero test coverage. No unit tests, integration tests, or end-to-end tests for any microservice.
- **Recommendation**: Create `tests/` directories in each microservice with pytest test suites. Add integration tests that validate the producer → SQS → consumer → DynamoDB flow using localstack or testcontainers. Include tests in CI pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks found in the repository (markdown, YAML, or JSON). No SSM Automation documents. No Lambda remediation functions. No Step Functions for incident workflows. Argo Workflows handle tenant lifecycle but not incident response. No self-healing patterns (auto-restart on failure events beyond Kubernetes default restartPolicy).
- **Gap**: No incident response automation. Manual intervention required for all operational issues.
- **Recommendation**: Create machine-readable runbooks (Markdown with structured sections) for common failure scenarios: SQS queue backlog, DynamoDB throttling, node scaling failures. Implement SSM Automation documents for common remediation actions. Add PagerDuty/OpsGenie integration.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file referencing observability assets. No SLO ownership files or dashboards with named owners. No evidence of platform team tooling for centralized observability. Kubecost provides infrastructure cost visibility. README mentions Amazon Managed Grafana (AMG) and Amazon Managed Prometheus (AMP) as supported services but these are not deployed in the IaC.
- **Gap**: No observability ownership model. No SLO-driven culture. No shared responsibility model between platform and product teams.
- **Recommendation**: Establish an observability ownership model: define who owns SLOs, dashboards, and alerts for each service. Deploy AMP and AMG as mentioned in the README. Create CODEOWNERS entries for observability configurations. Assign per-service observability ownership.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Not Triggered | Medium | — | — | — |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | Medium | — | — | — |
| Move to Managed Databases | Not Triggered | Medium | — | — | — |
| Move to Managed Analytics | Not Triggered | Medium | — | — | — |
| Move to Modern DevOps | Triggered | Medium | High | INF-Q6: 2/4, OPS-Q9: 2/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Medium | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps + Move to AI can execute in parallel as they target different aspects of the platform — DevOps focuses on CI/CD, observability, and deployment strategy; AI focuses on agent frameworks, vector databases, and RAG.

**Sequential Dependencies**: Move to Modern DevOps should establish observability foundations (OPS-Q1, OPS-Q2) before Move to AI deploys agents, since agent workloads require tracing and structured logging to debug.

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q6: Score 2/4 — No CI pipeline definitions found; only CD automation via Flux CD image automation
  - OPS-Q9: Score 2/4 — Rolling updates only via Flux CD; no canary or blue/green deployments
  - OPS-Q10: Score 1/4 — Zero test coverage; no unit, integration, or end-to-end tests
  - OPS-Q1: Score 1/4 — No distributed tracing; no OpenTelemetry, X-Ray, or tracing SDK
- **Current State**: Strong GitOps CD foundation with Flux CD and Argo Workflows. Comprehensive IaC with Terraform. However, no CI pipeline for building/testing, no progressive delivery, no test suites, and no observability stack.
- **Target State**: Full CI/CD pipeline with automated build, test, scan, and deploy stages. Progressive delivery with canary deployments. End-to-end distributed tracing. Comprehensive test coverage. SLO-driven observability.
- **Key Activities**:
  1. Create CI pipeline definitions (Gitea Actions or CodeBuild/CodePipeline) for build, test, and image scan
  2. Add OpenTelemetry instrumentation to all microservices and deploy ADOT collector
  3. Implement structured JSON logging with correlation IDs across all services
  4. Create pytest test suites for each microservice with integration tests
  5. Deploy Flagger for canary deployments with automatic rollback
  6. Define SLOs and create CloudWatch alarms for monitoring
  7. Deploy Amazon Managed Prometheus (AMP) and Amazon Managed Grafana (AMG)
- **Dependencies**: None — this pathway can start immediately
- **Estimated Effort**: High (4-6 months for complete implementation)
- **Roadmap Phase Alignment**: Phase 1 (structured logging, basic CI) → Phase 2 (tracing, testing, canary) → Phase 3 (SLOs, anomaly detection)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI or agent framework imports; no Bedrock, langchain, or strands-agents
  - DATA-Q1: Score 1/4 — No vector database detected (no OpenSearch, pgvector, Bedrock Knowledge Bases)
  - DATA-Q3: Score 1/4 — No RAG implementation (no embeddings, chunking, or semantic search)
  - OPS-Q3: Score 1/4 — No agent evaluation framework or datasets
  - OPS-Q6: Score 1/4 — No LLM cost tracking or token usage metrics
- **Current State**: Python (Flask) microservices with boto3 — strong language foundation for AI. Well-structured SQS/DynamoDB data patterns. No AI or agent frameworks, vector databases, or RAG pipelines.
- **Target State**: AI-capable platform with Amazon Bedrock integration, agent frameworks (strands-agents), vector database for semantic search, RAG pipeline for knowledge retrieval, evaluation framework, and LLM cost tracking.
- **Key Activities**:
  1. Integrate Amazon Bedrock via boto3 (`bedrock-runtime` client) in a new agent microservice
  2. Deploy Amazon Bedrock Knowledge Bases with S3 data source for RAG
  3. Implement `strands-agents` SDK for building agents that use existing microservices as tools
  4. Create OpenAPI specs for existing APIs (prerequisite for agent tool discovery)
  5. Build evaluation framework with golden datasets and scoring
  6. Implement per-tenant LLM token tracking with CloudWatch metrics
  7. Add human-in-the-loop approval for high-risk agent actions
- **Dependencies**: Move to Modern DevOps should provide observability (tracing, logging) before deploying agents to production
- **Estimated Effort**: High (3-6 months for initial agent capabilities)
- **Roadmap Phase Alignment**: Phase 2 (Bedrock integration, vector DB, RAG) → Phase 3 (agent deployment, eval framework, cost tracking)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Agent Tool Integration via JSON APIs** — Your microservices already return structured JSON responses from all endpoints (`/producer`, `/consumer`, `/payments`). Agent frameworks can immediately wrap these endpoints as tools with minimal effort.
   - **Leverages**: Structured JSON responses (APP-Q5: 4/4) across all three microservices
   - **Effort**: Low
   - **Value**: Enables rapid prototyping of agents that interact with existing services

2. **RAG-Based Knowledge Agent from Documentation** — Your repository contains extensive documentation (`README.md`, architecture descriptions, workflow scripts documentation) that can be indexed for a knowledge agent.
   - **Leverages**: README.md with architecture overview, deployment steps, and service descriptions; `workflow-scripts/README.md`
   - **Effort**: Low-Medium
   - **Value**: Build a knowledge base agent that answers questions about the SaaS platform architecture, tenant onboarding process, and operational procedures

3. **Data Query Agent via DynamoDB** — Your DynamoDB table schema (`consumer_ddb` with `tenant_id` hash key, `message_id` range key) is well-defined in Terraform, enabling a natural language query agent.
   - **Leverages**: DynamoDB schema in `terraform/modules/tenant-apps/main.tf` (DATA-Q7: 2/4)
   - **Effort**: Medium
   - **Value**: Build an agent that can query tenant message data using natural language (e.g., "Show me all messages for tenant-01 from today")

4. **DevOps Agent for Tenant Operations** — Your Argo Workflows and SQS-based tenant lifecycle automation provides a clear API for a DevOps agent to trigger tenant onboarding, deployment, and offboarding.
   - **Leverages**: SQS queues for tenant operations, Argo Workflows automation, Flux CD GitOps (INF-Q6: 2/4)
   - **Effort**: Medium
   - **Value**: Build an agent that can onboard tenants, trigger deployments, and check deployment status via natural language commands

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Quick Wins (Days 1–30)

1. **Secure the Argo Workflows server**: Change `--auth-mode=server` to `--auth-mode=client` and switch the service annotation to `internal` in `03-argo-workflows.yaml`. This is a critical security fix — the Argo Workflows UI/API is currently internet-facing and unauthenticated.

2. **Implement structured JSON logging**: Add `python-json-logger` to all three microservices' `requirements.txt` and configure JSON formatters. Include `tenant_id`, `message_id`, and request metadata in every log entry. This is a low-effort, high-impact change.

3. **Add OpenAPI specs to all microservices**: Add `flask-smorest` or `apiflask` to generate OpenAPI 3.0 specs. This enables agent tool discovery and is a prerequisite for the Move to AI pathway.

4. **Enable HPA for application pods**: Set `autoscaling.enabled: true` in Helm chart values for producer and consumer services. The HPA templates already exist — this is a configuration change only.

5. **Add basic CI pipeline**: Create a Gitea Actions workflow (`.gitea/workflows/build.yaml`) or AWS CodeBuild `buildspec.yml` for each microservice that builds the Docker image, runs basic linting, and pushes to ECR.

### Phase 2 — Foundation (Months 1–3)

1. **Deploy API authentication**: Implement Amazon Cognito user pools with per-tenant configuration. Add JWT validation middleware to all Flask endpoints. Configure ALB OIDC authentication action. Replace raw `tenantID` header with verified JWT claims.

2. **Add distributed tracing**: Integrate OpenTelemetry SDK into all microservices with Flask, boto3, and botocore instrumentation. Deploy ADOT collector as DaemonSet. Configure X-Ray as the trace backend. Propagate trace context across SQS messages.

3. **Create test suites**: Build pytest unit and integration tests for each microservice. Add integration tests for the producer → SQS → consumer → DynamoDB flow using localstack. Integrate test execution into the CI pipeline.

4. **Implement resilience patterns**: Add `tenacity` for retry with exponential backoff, `pybreaker` for circuit breakers, and explicit timeouts on all boto3 clients. Add idempotency keys to SQS messages and conditional writes to DynamoDB.

5. **Harden IAM policies**: Replace `AdministratorAccess` on Argo Workflows and TF Controller roles with least-privilege policies. Scope Kubernetes ClusterRoles. Enable CloudTrail with log file validation.

6. **Begin Bedrock integration**: Add Amazon Bedrock boto3 client to a new agent microservice. Deploy Bedrock Knowledge Bases with S3 data source. Create a proof-of-concept RAG agent for SaaS documentation.

### Phase 3 — Advanced Capabilities (Months 3–6)

1. **Deploy progressive delivery**: Implement Flagger or Argo Rollouts for canary deployments with automatic rollback. Define success metrics (error rate, latency) for canary analysis. Integrate with ALB traffic shifting.

2. **Establish SLO-driven observability**: Define SLOs for all microservices. Deploy Amazon Managed Prometheus (AMP) and Amazon Managed Grafana (AMG). Create dashboards with SLO burn-rate alerts. Implement CloudWatch anomaly detection.

3. **Deploy production agents**: Build agents using `strands-agents` SDK that interact with existing microservices as tools. Implement per-tenant agent isolation. Add human-in-the-loop approval for high-risk actions (tenant offboarding, infrastructure changes).

4. **Implement agent evaluation framework**: Create golden datasets for expected agent behaviors. Build automated eval pipeline that runs on CI/CD. Track agent quality metrics (task success rate, hallucination rate).

5. **Add LLM cost tracking and business metrics**: Implement per-tenant token tracking with CloudWatch custom metrics. Build business outcome dashboards (messages processed, tenant onboarding time, agent task success rate). Establish cost attribution per tenant and per agent workflow.

---

## Recommended Self-Paced Learning Materials

### Module 6: Move to Modern DevOps
*Recommended because: Move to Modern DevOps pathway is triggered — CI/CD, observability, and deployment strategy gaps detected.*

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive learning plan covering CI/CD, IaC, observability, and modern deployment practices
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundation course for establishing DevOps practices on AWS
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Hands-on lab for creating CI/CD pipelines relevant to your containerized microservices
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Addresses your zero test coverage gap with advanced testing patterns
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Directly applicable to your Python/Flask microservices for observability
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
  - Relevant to enhancing your existing GitOps workflow with CI automation
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
  - Combines your EKS + GitOps stack with AI-powered DevOps capabilities
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
  - Hands-on EKS automation patterns directly applicable to your architecture
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1
  - The workshop for your specific architecture — build on this foundation

### Module 7: Move to AI
*Recommended because: Move to AI pathway is triggered — no agent frameworks, vector databases, or RAG implementation.*

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Complete learning plan for adding AI capabilities to existing applications
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
  - Overview of what's possible with generative AI — helps frame your Quick Agent Wins
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Essential for integrating Bedrock into your Python microservices
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Foundation for building effective agent prompts
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on lab for implementing RAG — directly addresses your DATA-Q1, DATA-Q2, DATA-Q3 gaps
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Foundation for understanding agentic AI patterns on AWS
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Directly relevant — build a DevOps agent similar to your Quick Agent Win #4
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced agent observability — addresses your OPS-Q3 and OPS-Q6 gaps

### Module 3: Move to Containers with Amazon ECS and EKS
*Recommended because: Your platform already runs on EKS — these resources help deepen EKS expertise.*

- EKS Workshop — https://www.eksworkshop.com/
  - Comprehensive hands-on workshop for EKS — relevant to your existing architecture
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4
  - Explore EKS Auto Mode for simplified cluster management

### Module 4: Move to Managed Databases
*Recommended because: Your DynamoDB usage is solid but vector database knowledge is needed for AI readiness.*

- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Essential for understanding vector database options for your RAG implementation

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `terraform/workshop/main.tf` | EKS cluster definition (v19.12), VPC with 3 AZs, Gitea EC2 instance, SSM SecureString for secrets, public EKS endpoint |
| 2 | `terraform/modules/tenant-apps/main.tf` | Per-tenant IRSA roles (least-privilege), SQS queues, DynamoDB tables, SSM parameters |
| 3 | `terraform/modules/gitops-saas-infra/main.tf` | AdministratorAccess on Argo Workflows and TF Controller roles, Karpenter IRSA with Resource: *, SQS control-plane queues, S3 buckets |
| 4 | `terraform/modules/gitea/main.tf` | EC2 instance for Gitea, security group with 0.0.0.0/0 egress, EBS encryption enabled |
| 5 | `terraform/modules/flux_cd/main.tf` | Flux operator deployment, Git credentials as Kubernetes secrets, FluxInstance configuration |
| 6 | `tenant-microservices/producer/producer.py` | Flask app with unauthenticated endpoints, unverified tenantID header, SQS send without deduplication, no rate limiting |
| 7 | `tenant-microservices/consumer/consumer.py` | Background thread SQS polling, DynamoDB direct writes without idempotency, basicConfig logging (unstructured) |
| 8 | `tenant-microservices/payments/payments.py` | Minimal Flask app, no authentication, no AWS service integration |
| 9 | `tenant-microservices/producer/requirements.txt` | Flask 3.0.0, boto3 ~1.28.59, no tracing/resilience/AI libraries |
| 10 | `tenant-microservices/producer/Dockerfile` | Python 3.9.17-slim base image (approaching EOL) |
| 11 | `gitops/infrastructure/production/03-argo-workflows.yaml` | Argo Workflows v0.40.11, --auth-mode=server (unauthenticated), internet-facing LB, ClusterRole with apiGroups: ["*"] |
| 12 | `gitops/infrastructure/production/06-argo-events.yaml` | Argo Events v2.4.3, ClusterRole with wildcard permissions |
| 13 | `gitops/infrastructure/production/02-karpenter.yaml` | Karpenter v1.4.0 with IRSA |
| 14 | `gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml` | Default NodePool with consolidation policy, spot + on-demand instances |
| 15 | `gitops/infrastructure/production/dependencies/02-application-karpenter-config.yaml` | Application NodePool with taints for application isolation |
| 16 | `gitops/infrastructure/production/05-kubecost.yaml` | Kubecost v2.1.0 with Prometheus, no custom alerting rules |
| 17 | `helm-charts/helm-tenant-chart/templates/ingress.yaml` | ALB ingress with header-based routing (TenantID), no auth/throttling |
| 18 | `helm-charts/helm-tenant-chart/templates/hpa.yaml` | HPA template defined but disabled (autoscaling.enabled: false) |
| 19 | `helm-charts/helm-tenant-chart/templates/terraform.yaml` | TF Controller with approvePlan: auto (no human approval) |
| 20 | `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | SQS EventSource → Argo Sensor → Workflow trigger with GIT_TOKEN as plaintext parameter |
