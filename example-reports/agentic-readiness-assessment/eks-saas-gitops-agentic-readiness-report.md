# Agentic Readiness Assessment Report
**Target**: ./services/eks-saas-gitops
**Date**: 2026-03-12
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: agentic-ai-enablement
**Goal Context**: Building customer-facing AI agents for support and order management
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
   - Phase 1 — Agent Quick Wins (Days 1–30)
   - Phase 2 — Agent Foundations (Months 1–3)
   - Phase 3 — Agent Scale & Optimization (Months 3–6)
8. Recommended Self-Paced Learning Materials
9. Appendix: Evidence Index

---

## Executive Summary

This EKS SaaS GitOps monorepo demonstrates strong infrastructure foundations — EKS with Karpenter auto-scaling, DynamoDB per-tenant isolation, SQS-driven async messaging, and comprehensive Terraform IaC — but is **not yet ready for agentic AI enablement** targeting customer support and order management agents. The critical blockers are: zero AI/agent framework integration, no API documentation for agent tool discovery, no vector database or RAG pipeline for knowledge retrieval, no API authentication or identity propagation for secure agent actions, and no observability infrastructure (tracing, structured logging, eval frameworks) required to monitor autonomous agent behavior. The microservices architecture (producer, consumer, payments) provides clean service boundaries that agents could leverage as tools, but the services lack the resilience patterns, idempotency, and security controls necessary for safe autonomous operation.

### Overall Score: 1.8 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.8 / 4.0 | 🟡 |
| Application Architecture | 2.2 / 4.0 | 🟠 |
| Data Foundations | 1.8 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.3 / 4.0 | ❌ |
| Operations & Observability | 1.2 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

The following 5 gaps are the highest-impact blockers for enabling customer-facing AI agents for support and order management, weighted by agentic-ai-enablement priority criteria:

### 1. 🔴 No AI/Agent Frameworks (APP-Q13: 1/4)
**Why it blocks agents**: Without agent frameworks (Strands Agents SDK, LangChain, Bedrock Agents), there is no foundation to build customer support or order management agents. No AI-related imports exist in any `requirements.txt`.
**First step**: Add `strands-agents` and `boto3` Bedrock dependencies to the producer service's `requirements.txt` and create a proof-of-concept agent that wraps the existing `/producer` POST endpoint as a tool.

### 2. 🔴 No API Documentation (APP-Q2: 1/4)
**Why it blocks agents**: Agents discover and invoke tools via OpenAPI specs. Without documented API contracts, an agent cannot autonomously determine which endpoints exist, what parameters they accept, or what responses to expect. The Flask routes in `producer.py`, `consumer.py`, and `payments.py` have no accompanying OpenAPI/Swagger specs.
**First step**: Add `flask-smorest` or `flasgger` to each microservice to auto-generate OpenAPI specs from existing Flask routes. This is a low-effort, high-value enabler for agent tool integration.

### 3. 🔴 No Vector Database or RAG Pipeline (DATA-Q1: 1/4, DATA-Q3: 1/4)
**Why it blocks agents**: A customer support agent for order management needs to retrieve relevant knowledge (FAQs, product docs, order policies) via semantic search. No vector database (OpenSearch, pgvector, S3 Vectors) or RAG pipeline (embeddings, chunking, similarity search) exists anywhere in the codebase.
**First step**: Deploy an Amazon Bedrock Knowledge Base backed by S3 for document ingestion. Leverage the existing S3 buckets and DynamoDB data as knowledge sources. Use Bedrock Titan Embeddings for vectorization.

### 4. 🔴 No API Authentication or Identity Propagation (SEC-Q9: 1/4, SEC-Q3: 1/4)
**Why it blocks agents**: Agents acting on behalf of customers must propagate authenticated user identity end-to-end. Currently, the Flask APIs have zero authentication — the `tenantID` header is trusted without verification. An agent invoking `/producer` POST could impersonate any tenant. No JWT, OAuth2, or Cognito integration exists.
**First step**: Deploy Amazon Cognito for tenant authentication. Add JWT validation middleware to each Flask service. Use Amazon API Gateway (preferred per your preferences) as the API entry point with Cognito authorizer to enforce per-request auth before traffic reaches the ALB.

### 5. 🔴 No Automated Agent Evaluation Framework (OPS-Q3: 1/4)
**Why it blocks agents**: Autonomous agents require continuous evaluation to prevent hallucination, incorrect tool invocations, and quality degradation. No eval datasets, scoring scripts, or LLM-as-judge patterns exist. Without eval infrastructure, deploying a customer-facing agent is high-risk.
**First step**: Create a golden test dataset of 50+ customer support queries with expected agent actions and responses. Implement a pytest-based eval harness that measures tool selection accuracy, response quality, and task completion rate.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: The primary workloads run on Amazon EKS (`terraform/workshop/main.tf`) with managed node groups (`baseline-infra`, 3x `m5.large`, min 3/max 5) and Karpenter for dynamic node provisioning (`gitops/infrastructure/production/02-karpenter.yaml`). Application pods are deployed via Helm charts onto Karpenter-managed nodes. However, Gitea runs as a Docker container on a standalone EC2 instance (`terraform/modules/gitea/main.tf`, `aws_instance.gitea`), and a VSCode IDE runs on a separate EC2 instance (`helpers/vs-code-ec2.yaml`).
- **Gap**: Gitea (self-managed git server) and VSCode IDE are raw EC2 workloads, not managed container orchestration. These are supporting infrastructure, not application compute, but still represent non-managed compute.
- **Recommendation**: Gitea and VSCode are workshop/dev tooling. For production, consider replacing Gitea with a managed Git service (e.g., CodeCommit, GitHub) or running Gitea on EKS. The core application compute (producer, consumer, payments) is fully EKS-based.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: Per-tenant DynamoDB tables are provisioned dynamically via Terraform (`terraform/modules/tenant-apps/main.tf`, `aws_dynamodb_table.consumer_ddb`) with PAY_PER_REQUEST billing and point-in-time recovery enabled. DynamoDB is fully managed with automatic failover. Gitea uses SQLite3 embedded in its Docker container on EC2 (`terraform/modules/gitea/userdata.sh`, `GITEA__database__DB_TYPE=sqlite3`).
- **Gap**: Gitea's SQLite3 is self-managed — no automated backups, no failover, no managed lifecycle. While Gitea is supporting infrastructure (not application data), it represents a self-managed database instance.
- **Recommendation**: For the application databases (DynamoDB), the setup is fully managed and agent-ready. For Gitea, consider migrating to a managed Git service or backing Gitea with RDS PostgreSQL (preferred per your preferences) instead of SQLite.

#### INF-Q3: Workflow Orchestration
- **Score**: 3/4 🟡
- **Finding**: Argo Workflows provides dedicated workflow orchestration for tenant lifecycle operations: onboarding (`tenant-onboarding-workflow-template.yaml`), deployment (`tenant-deployment-workflow-template.yaml`), and offboarding (`tenant-offboarding-workflow-template.yaml`). Argo Events with SQS event sources trigger workflows automatically. NATS EventBus (`event-bus.yaml`) provides event routing.
- **Gap**: Workflow orchestration covers infrastructure/tenant operations but not business workflow logic within the microservices themselves. No Step Functions or application-level workflow orchestration for order management or support flows.
- **Recommendation**: Add AWS Step Functions (or extend Argo Workflows) for business-level workflows such as order processing, customer support escalation, and agent task orchestration. Step Functions with `.waitForTaskToken` enables human-in-the-loop patterns critical for customer-facing agents.

#### INF-Q4: Async Messaging
- **Score**: 3/4 🟡
- **Finding**: SQS queues are used extensively: per-tenant consumer queues (`terraform/modules/tenant-apps/main.tf`, `aws_sqs_queue.consumer_sqs`), and Argo workflow trigger queues (`argoworkflows-onboarding-queue`, `argoworkflows-offboarding-queue`, `argoworkflows-deployment-queue` in `terraform/modules/gitops-saas-infra/main.tf`). All SQS queues have managed SSE enabled. NATS EventBus is used for Argo Events internal messaging.
- **Gap**: No EventBridge for event-driven integration across services. No SNS for fan-out patterns. The messaging is SQS-only, which limits event routing flexibility. NATS is self-managed within the cluster.
- **Recommendation**: Add Amazon EventBridge (preferred per your preferences) for cross-service event routing. This enables agent event-driven architectures where agent actions can trigger downstream workflows via EventBridge rules.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: Comprehensive Terraform coverage: VPC (`terraform/workshop/main.tf` via `terraform-aws-modules/vpc/aws`), EKS cluster and node groups, IAM roles (IRSA for 6+ services), ECR repositories, SQS queues, DynamoDB tables, S3 buckets, SSM parameters, Gitea EC2 instance, and VPC peering. Helm charts define all Kubernetes workloads (`helm-charts/helm-tenant-chart/`, `helm-charts/application-chart/`). Flux CD manages GitOps-based continuous delivery. TF Controller enables Terraform execution from within Kubernetes (`gitops/infrastructure/production/07-tf-controller.yaml`). CloudFormation is used for the VSCode IDE stack (`helpers/vs-code-ec2.yaml`).
- **Gap**: None significant. IaC coverage is comprehensive across compute, networking, databases, messaging, and application deployments.
- **Recommendation**: Maintain this excellent IaC foundation. Consider adding Terraform state locking documentation and remote state backend configuration visibility.

#### INF-Q6: CI/CD
- **Score**: 3/4 🟡
- **Finding**: Flux CD provides GitOps-based continuous delivery with image automation (`producer-image-automation.yaml`, `consumer-image-automation.yaml`) that automatically detects new ECR images and updates deployment manifests. Gitea CI runner is configured (`terraform/modules/gitea/userdata.sh`) for build pipelines. Argo Workflows orchestrates tenant lifecycle operations triggered by SQS messages.
- **Gap**: No explicit automated test stage in the CI/CD pipeline. Image automation detects new images and deploys them directly — there is no test gate between build and deploy. No buildspec.yml, Jenkinsfile, or GitHub Actions workflow defining a multi-stage pipeline with test/build/deploy.
- **Recommendation**: Add a Gitea Actions workflow (or Argo Workflow step) that runs unit tests and integration tests before pushing images to ECR. Gate the image automation on test passage. This is critical before deploying agent-powered services.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: An ALB is provisioned via AWS Load Balancer Controller (`gitops/infrastructure/production/04-lb-controller.yaml`) with Kubernetes Ingress resources (`helm-charts/helm-tenant-chart/templates/ingress.yaml`). The ALB routes traffic based on `TenantID` HTTP header matching (`alb.ingress.kubernetes.io/conditions`). ALB is internet-facing (`alb.ingress.kubernetes.io/scheme: internet-facing`).
- **Gap**: No API Gateway with throttling, request validation, or auth integration. No WAF rules on the ALB. The ALB provides basic load balancing but lacks the agent-ready features: throttling (critical for agents making rapid API calls), request validation, usage plans, and centralized auth.
- **Recommendation**: Deploy Amazon API Gateway (preferred per your preferences) in front of the ALB. Configure throttling, usage plans, request validation, and Cognito authorizer. API Gateway is the natural entry point for agent tool invocations — it provides the rate limiting, auth, and request shaping that agents require.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or managed streaming services detected in Terraform or GitOps configurations. SQS is used for async messaging (queue-based), not streaming. No stream consumer patterns, no event stream processing.
- **Gap**: No real-time streaming infrastructure. For customer support and order management agents, real-time event streams enable live order status tracking, real-time agent activity monitoring, and event-driven agent triggers.
- **Recommendation**: Evaluate whether real-time streaming is needed for the agent use case. If agents need live order updates or real-time customer interaction events, consider Amazon Kinesis Data Streams or EventBridge Pipes for event streaming.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: VPC with 3 AZs, private subnets for EKS nodes, public subnets for ALB and Gitea. Security groups with specific ingress rules: Gitea SG restricts access to VSCode VPC CIDR, EKS cluster SG, and optional allowed IP (`terraform/modules/gitea/main.tf`). Karpenter node classes use subnet/SG selectors with discovery tags (`gitops/infrastructure/production/dependencies/01-default-karpenter-config.yaml`). EKS cluster endpoint is public (`cluster_endpoint_public_access = true`).
- **Gap**: Broad egress rules (`0.0.0.0/0` on Gitea SG). EKS cluster endpoint is publicly accessible. No NACLs explicitly defined. Argo Workflows server is internet-facing with no auth (`--auth-mode=server`).
- **Recommendation**: Restrict EKS cluster endpoint to private access or limit public access to specific CIDRs. Add egress restrictions on security groups. Enable Argo Workflows authentication. For agent workloads, ensure agent-to-service communication stays within private subnets.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Karpenter provides node-level auto-scaling with two NodePools: `default` (general workloads) and `application` (tenant applications with taints) in `gitops/infrastructure/production/dependencies/`. Both NodePools have CPU limit 1000 and memory limit 2000Gi with consolidation policies. EKS managed node group has min_size=3, max_size=5. HPA template exists in `helm-charts/helm-tenant-chart/templates/hpa.yaml` with CPU-based scaling.
- **Gap**: HPA is disabled by default (`autoscaling.enabled: false` in `values.yaml.template`). Pod-level auto-scaling is not active, only node-level (Karpenter). No Lambda concurrency limits (no Lambda functions exist).
- **Recommendation**: Enable HPA for the producer and consumer services, especially as agent-driven traffic will be bursty and unpredictable. Set appropriate min/max replicas and CPU/memory thresholds. Consider Karpenter's provisioner limits to handle agent-scale workloads.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 4/4 ✅
- **Finding**: All three microservices (producer, consumer, payments) are written in Python 3.9 with Flask framework. Python has the best agent framework ecosystem: `strands-agents`, `langchain`, `langraph`, `crewai`, and native `boto3` Bedrock integration. `requirements.txt` files show Flask 3.0.0, boto3 ~1.28.59, and standard web dependencies.
- **Gap**: None. Python is the optimal language for agent development.
- **Recommendation**: Leverage the Python ecosystem to rapidly integrate agent frameworks. The existing Flask services can be extended with agent endpoints or wrapped as agent tools with minimal friction.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specification files found in the repository. No `openapi.yaml`, `swagger.json`, or API documentation files. Flask routes in `producer.py`, `consumer.py`, and `payments.py` define endpoints (`/producer`, `/consumer`, `/payments`) but have no auto-generated documentation. No `@ApiOperation`, `flasgger`, `flask-smorest`, or `flask-restx` annotations.
- **Gap**: Complete absence of machine-readable API documentation. Agents cannot discover or validate API contracts without OpenAPI specs.
- **Recommendation**: Add `flask-smorest` or `flasgger` to each microservice to auto-generate OpenAPI 3.0 specs. Document request/response schemas, required headers (tenantID, tier), and error responses. This is a prerequisite for agent tool integration.

#### APP-Q3: Async vs Sync Communication
- **Score**: 3/4 🟡
- **Finding**: The producer service sends messages to SQS asynchronously (`sqs_client.send_message` in `producer.py`). The consumer service polls SQS in a background thread (`Thread(target=process_messages)` in `consumer.py`) and writes to DynamoDB. The producer's HTTP POST endpoint is synchronous but triggers async downstream processing. Argo Workflows are triggered asynchronously via SQS event sources.
- **Gap**: The payments service has no async patterns — it's a purely synchronous GET endpoint. Producer's GET endpoint is synchronous. No event-driven patterns between the three microservices directly; all async communication flows through SQS.
- **Recommendation**: The async/sync mix is appropriate for the current architecture. For agent integration, ensure agent tool invocations return quickly (sync response with async processing). Consider adding EventBridge for agent-triggered events that need fan-out to multiple services.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three independently deployable microservices: `producer` (sends messages to SQS), `consumer` (reads SQS, writes to DynamoDB), and `payments` (payment service stub). Each has its own `Dockerfile`, `requirements.txt`, Kubernetes Deployment, Service, Ingress, and ServiceAccount via the Helm tenant chart (`helm-charts/helm-tenant-chart/templates/`). Per-tenant IRSA roles provide service-level IAM isolation (`terraform/modules/tenant-apps/main.tf`). Clear service boundaries with no shared state between services.
- **Gap**: None. The architecture is already decomposed into independently deployable microservices with clear boundaries.
- **Recommendation**: These clean service boundaries are ideal for agent tool mapping. Each microservice can become an independent agent tool: producer tool (send messages), consumer tool (query order data), payments tool (process payments).

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All microservices return structured JSON responses. Flask automatically serializes Python dictionaries to JSON. Examples: `producer.py` returns `{ "tenant_id": ..., "environment": ..., "version": ..., "microservice": ..., "message_id": ... }`. `consumer.py` returns similar JSON. `payments.py` returns `{ "tenant_id": ..., "environment": ..., "version": ..., "microservice": ... }`.
- **Gap**: None. All APIs return structured JSON.
- **Recommendation**: JSON responses are agent-ready. Consider adding consistent error response schemas (e.g., `{ "error": ..., "code": ..., "message": ... }`) for agents to handle errors gracefully.

#### APP-Q6: Workflow Logic
- **Score**: 3/4 🟡
- **Finding**: Argo Workflows provides dedicated orchestration for tenant lifecycle: onboarding (clone repo → validate → create Helm release), deployment (clone repo → update Helm release), offboarding (clone repo → validate → remove Helm release). Workflow templates in `gitops/control-plane/production/workflows/` define multi-step workflows with volume mounts and parameterized inputs.
- **Gap**: No business-level workflow orchestration (order processing, support ticket routing, agent task coordination). Argo Workflows handles infrastructure operations, not application business logic.
- **Recommendation**: Add Step Functions for customer support and order management workflows. Define agent orchestration workflows: customer query → intent classification → tool selection → action execution → response generation. Step Functions' Express Workflows are ideal for synchronous agent interactions.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys in any API. The producer's POST endpoint (`producer.py`) sends a new SQS message on every call with no deduplication. SQS queues are standard queues (not FIFO), so no message deduplication ID is configured. The consumer's `put_item` to DynamoDB uses `tenant_id` + `message_id` as keys, but `message_id` is SQS-generated, not client-provided — so duplicate sends create duplicate records.
- **Gap**: Complete absence of idempotency patterns. Agents retrying failed API calls will produce duplicate messages and database records.
- **Recommendation**: Add an `Idempotency-Key` header to the producer POST endpoint. Use DynamoDB conditional writes for deduplication. Consider SQS FIFO queues with deduplication IDs for critical operations. This is critical for agent reliability — agents will retry failed calls.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. Flask apps have no rate-limiting middleware (no `flask-limiter`). ALB ingress has no WAF rules. No API Gateway usage plans or throttling configuration. The ALB routes all traffic directly to services.
- **Gap**: Complete absence of rate limiting. An agent making rapid API calls could overwhelm services. No protection against abuse or runaway agent loops.
- **Recommendation**: Deploy Amazon API Gateway (preferred) with per-client throttling and usage plans. As a quick win, add `flask-limiter` to each microservice. For agent workloads, configure per-agent rate limits to prevent runaway loops from overwhelming the system.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry with backoff, or timeout configurations. `producer.py` has a basic `try/except` with a generic error return (`{ "msg": "Oops - please check application logs" }, 500`). `consumer.py` has a bare `except Exception` in its message processing loop with `logger.error`. No `tenacity`, `retry`, `backoff`, `resilience4j` equivalent, or AWS SDK retry configuration overrides in the code.
- **Gap**: Complete absence of resilience patterns. SQS client calls, SSM parameter lookups, and DynamoDB writes have no explicit retry logic, timeouts, or circuit breakers. The consumer's infinite polling loop (`while True`) has no backoff on repeated failures.
- **Recommendation**: Add `tenacity` for retry with exponential backoff on all AWS SDK calls. Configure boto3 retry configuration. Add request timeouts to all outbound calls. Implement circuit breaker pattern for external dependencies. For agent workloads, resilience is critical — agent tool calls must degrade gracefully, not cascade failures.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: Argo Workflows handles long-running tenant operations (onboarding, deployment, offboarding) asynchronously via SQS-triggered workflows. The consumer service runs a background thread (`Thread(target=process_messages)`) for continuous SQS polling. However, the Flask web server runs synchronously with no async task framework.
- **Gap**: No explicit async job framework for application-level long-running operations. If an agent triggers a complex order management operation, there's no mechanism to handle it asynchronously with status polling. The background thread in consumer is a workaround, not a pattern.
- **Recommendation**: Add an async task pattern for agent-initiated long-running operations: accept the request, return a job ID, process asynchronously (via SQS + Lambda or Argo Workflows), and provide a status polling endpoint. This enables agents to initiate operations and check status without blocking.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning. Routes are `/producer`, `/consumer`, `/payments` — no `/v1/` prefix, no `Accept-Version` header handling, no versioning annotations. No changelog files for API changes.
- **Gap**: Complete absence of versioning. Breaking API changes would disrupt agent integrations with no backward compatibility guarantee.
- **Recommendation**: Add `/v1/` prefix to all routes immediately (e.g., `/v1/producer`, `/v1/consumer`). This is a low-effort change that prevents future breaking changes from disrupting agent tool configurations.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Services are accessed via Kubernetes ClusterIP Services and ALB Ingress. Service names are templated via Helm (`{{ $.Values.tenantId }}-{{ $appName }}`). The `ENVIRONMENT` environment variable is injected into pods for SQS queue/DynamoDB table discovery via SSM Parameter Store lookups.
- **Gap**: No formal service discovery mechanism (AWS Cloud Map, Consul). No service mesh (App Mesh, Istio). Service-to-service communication relies on hardcoded SSM parameter naming conventions. No API catalog or service registry for agent tool discovery.
- **Recommendation**: The current Kubernetes-native service discovery is adequate for the microservices. For agent integration, create an API catalog (even a static JSON registry) listing all available services, their endpoints, and OpenAPI specs. This enables agent tool discovery without a full service mesh.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports in any `requirements.txt`. No `langchain`, `strands-agents`, `openai`, `anthropic`, `boto3` Bedrock calls, `crewai`, or MCP SDK. No Spring AI or equivalent. The services use only Flask, boto3 (for SQS/DynamoDB/SSM), and standard Python libraries.
- **Gap**: Complete absence of AI/agent framework integration. No agent SDK, no LLM calls, no tool definitions, no agent orchestration. This is the fundamental gap for agentic AI enablement.
- **Recommendation**: Start with the Strands Agents SDK (Python-native, integrates with Bedrock). Create a new `agent-service` microservice that uses the existing producer/consumer/payments APIs as tools. Deploy Amazon Bedrock with Claude or Titan models for LLM inference. Leverage the existing EKS infrastructure and GitOps pipeline for agent service deployment.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database detected. No OpenSearch domains, pgvector extensions, S3 Vectors, Bedrock Knowledge Bases, Pinecone, Weaviate, or Chroma imports found in Terraform, Helm charts, or Python dependencies.
- **Gap**: Complete absence of vector search capabilities. Customer support agents need semantic search over knowledge bases (product docs, FAQs, order policies) to provide accurate, contextual responses.
- **Recommendation**: Deploy an Amazon Bedrock Knowledge Base with S3 as the document source and Amazon OpenSearch Serverless as the vector store. Alternatively, use S3 Vectors (preferred for simplicity with DynamoDB-heavy architectures). Ingest existing documentation and order data schemas.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1), so there is no managed or self-hosted vector DB to evaluate.
- **Gap**: No vector DB present at all. When a vector DB is introduced, it must be a managed service to maintain agent reliability.
- **Recommendation**: When deploying a vector store, use a fully managed option: Amazon Bedrock Knowledge Bases (fully managed RAG), Amazon OpenSearch Serverless, or S3 Vectors. Avoid self-hosted Chroma or Weaviate on EKS to minimize operational burden.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components detected. No embedding model calls, no document chunking/splitting logic, no similarity search patterns, no Bedrock Knowledge Base integration. No references to Titan Embeddings, OpenAI ada, or any embedding model in the codebase.
- **Gap**: Complete absence of RAG. For customer support agents, RAG is essential — agents must retrieve relevant context (order history, product information, support policies) before generating responses.
- **Recommendation**: Implement a RAG pipeline: (1) Ingest support documentation and product catalogs into S3, (2) Configure Bedrock Knowledge Base with Titan Embeddings for chunking and vectorization, (3) Integrate the agent service with Bedrock Knowledge Base `RetrieveAndGenerate` API for contextual responses.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Three primary data sources: DynamoDB (per-tenant consumer data tables), SQS (message queues per-tenant), and SSM Parameter Store (configuration discovery — queue URLs, table names). The data architecture is relatively contained and well-organized by tenant.
- **Gap**: No unified data access layer, but the number of data sources is manageable. Adding a vector DB and potentially RDS for order management will increase sprawl.
- **Recommendation**: Create a data access abstraction layer before adding new data sources for agents. Define clear data contracts per service. Consider DynamoDB Streams + EventBridge for agent-accessible data change events.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: The consumer service directly uses `boto3` DynamoDB client (`ddb_client.put_item`) in `consumer.py`. The producer directly uses `sqs_client.send_message` in `producer.py`. Both services directly use `ssm_client.get_parameter` for configuration discovery. No repository pattern, no data access layer abstraction.
- **Gap**: Direct SDK calls scattered across application logic. No abstraction between business logic and data access. This makes it difficult for agents to access data through well-defined APIs — agents would need to call AWS SDKs directly, bypassing API boundaries.
- **Recommendation**: Create a data access API layer (e.g., a `/v1/orders` REST API wrapping DynamoDB queries) so agents interact with data via APIs, not direct database connections. This is essential for secure, auditable agent data access.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: S3 buckets exist for Argo artifacts (`aws_s3_bucket.argo_artifacts`) and code artifacts (`aws_s3_bucket.codeartifacts`), but these are operational stores. No Textract, Tika, or document parsing pipeline. No unstructured data processing for customer support knowledge.
- **Gap**: No capability to parse or process unstructured documents (PDFs, emails, support tickets). Customer support agents need access to unstructured knowledge.
- **Recommendation**: Add an S3 bucket for support documentation and product catalogs. Configure Amazon Textract for document extraction if needed. Bedrock Knowledge Base can handle document parsing automatically when ingesting from S3.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table schema is defined in Terraform (`terraform/modules/tenant-apps/main.tf`): `hash_key = "tenant_id"`, `range_key = "message_id"`, with additional attributes (`producer_environment`, `consumer_environment`, `timestamp`) visible in `consumer.py`. No JSON Schema files, no Avro/Protobuf schemas, no formal data documentation.
- **Gap**: Schema is defined implicitly through code (Terraform attributes + Python `put_item` calls) rather than explicit documentation. No versioned schema registry. Agents need documented schemas to generate correct queries.
- **Recommendation**: Document DynamoDB table schemas as JSON Schema files. Include attribute types, required fields, and index definitions. This documentation enables agents to construct valid DynamoDB queries autonomously.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No centralized data access layer. Consumer imports `boto3` and creates clients directly at module level (`ddb_client = boto3.client("dynamodb")`). Producer creates `sqs_client = boto3.client("sqs")` at module level. Each service manages its own connections independently with no shared patterns.
- **Gap**: Scattered data access with no abstraction. Adding an agent service would require duplicating all data access patterns or directly calling boto3 SDK.
- **Recommendation**: Create a shared data access module or, better, expose DynamoDB data through REST APIs on the consumer service (e.g., `GET /v1/consumer/orders?tenant_id=X`). Agents should access data through APIs, not direct database connections.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embedding pipeline exists (no vector DB, no embeddings — see DATA-Q1 and DATA-Q3).
- **Gap**: When RAG is implemented, embedding refresh must be automated to keep knowledge current.
- **Recommendation**: When deploying Bedrock Knowledge Base, configure automatic sync schedules or event-driven sync via S3 event notifications. Use DynamoDB Streams to trigger re-indexing when order data changes.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 3/4 🟡
- **Finding**: DynamoDB is serverless — no engine version to pin, no EOL concern. Gitea uses SQLite3 embedded in the `gitea/gitea:latest` Docker image (`terraform/modules/gitea/userdata.sh`). The `:latest` tag means the SQLite version is not pinned and changes with Gitea image updates.
- **Gap**: Gitea's SQLite is implicitly using whatever version ships with the Gitea Docker image (`:latest` tag). No explicit version pinning for the Gitea database component.
- **Recommendation**: Pin the Gitea Docker image to a specific version tag instead of `:latest` for reproducibility. For production, migrate Gitea to a managed Git service or back it with RDS. DynamoDB has no EOL concerns.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs detected. DynamoDB is NoSQL with simple key-value access patterns (`put_item` in `consumer.py`). No `.sql` files in the repository. No ORM bypass patterns or raw SQL execution.
- **Gap**: None. The DynamoDB-based data layer has no stored procedure complexity.
- **Recommendation**: Maintain this clean separation of business logic in the application layer. When adding databases for order management, prefer DynamoDB (preferred per your preferences) or RDS PostgreSQL without stored procedures — keep all business logic in Python.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: SSM Parameter Store with `SecureString` type is used for Gitea admin password (`terraform/workshop/main.tf`, `aws_ssm_parameter.gitea_password`), Flux token, and CI/CD token (`terraform/modules/gitea/userdata.sh`). Tokens are stored via `aws ssm put-parameter --type SecureString`. Non-sensitive parameters (SQS ARNs, DDB ARNs) use plain `String` type in SSM.
- **Gap**: No AWS Secrets Manager usage. SSM SecureString is acceptable but lacks automatic rotation. The Gitea admin password is generated via `random_password` in Terraform and stored in state file. Git tokens are passed as workflow parameters through Argo Workflow definitions — visible in YAML templates (`tenant-onboarding-sensor.yaml`, `GIT_TOKEN` parameter). No hardcoded secrets in application code, but tokens flow through Argo Workflow parameters.
- **Recommendation**: Migrate sensitive tokens to AWS Secrets Manager with automatic rotation. Remove `GIT_TOKEN` from Argo Workflow parameter definitions and use Kubernetes Secrets with ExternalSecrets Operator instead. Encrypt Terraform state at rest.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: Per-service IRSA roles are implemented: karpenter (`karpenter_controller`), argo-workflows (`argo-workflows-irsa`), argo-events (`argo-events-irsa`), lb-controller (`lb-controller-irsa`), tf-controller (`tf-controller`), and per-tenant producer/consumer roles (`terraform/modules/tenant-apps/main.tf`). Per-tenant producer policies scope `sqs:SendMessage` and `ssm:GetParameter` to specific resource ARNs. Per-tenant consumer policies scope DynamoDB, SQS, and SSM access to specific resource ARNs.
- **Gap**: Three critical AdministratorAccess violations: `argo_workflows_eks_role` uses `AdministratorAccess` (`terraform/modules/gitops-saas-infra/main.tf`), `tf_controller_irsa_role` uses `AdministratorAccess`, and `EC2Role` in `helpers/vs-code-ec2.yaml` uses `AdministratorAccess`. Karpenter policy has `"Resource": "*"` for EC2 operations. Argo Events/Workflows ClusterRoles use `apiGroups: ["*"]`, `resources: ["*"]`, `verbs: ["*"]`.
- **Recommendation**: Replace `AdministratorAccess` on Argo Workflows and TF Controller roles with scoped policies. Restrict Kubernetes ClusterRoles to specific API groups and resources. For agent service roles, define minimal permissions: only Bedrock InvokeModel, specific DynamoDB tables, and specific SQS queues.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Tenant identification relies on an `tenantID` HTTP header set by the client (`request.headers.get("tenantID")` in `producer.py`, `consumer.py`, `payments.py`). The ALB ingress uses header-based routing (`httpHeaderConfig: httpHeaderName: TenantID`) to route requests. No JWT, OAuth2, OIDC, or Cognito integration. No token exchange between services.
- **Gap**: Complete absence of authenticated identity propagation. The `tenantID` header is trusted without any verification — any client can set any tenant ID. No user identity flows through service calls. Agents acting on behalf of customers cannot prove which customer they represent.
- **Recommendation**: Deploy Amazon Cognito with per-tenant user pools or a shared pool with tenant-scoped claims. Implement JWT validation middleware in each Flask service. Propagate JWT tokens through service calls. For agents, use Cognito Machine-to-Machine (M2M) credentials with tenant-scoped access tokens.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in Terraform or CloudFormation. CloudWatch is mentioned in `README.md` as a monitoring service, but no `aws_cloudtrail`, `aws_cloudwatch_log_group`, or CloudTrail log file validation is configured in IaC. EKS audit logging is not explicitly enabled in the EKS module configuration (`terraform/workshop/main.tf`).
- **Gap**: No audit trail for API actions, infrastructure changes, or tenant operations. Agent actions (API calls, data modifications) cannot be traced or audited.
- **Recommendation**: Enable CloudTrail with log file validation and immutable S3 storage. Enable EKS audit logging via the `cluster_enabled_log_types` parameter. For agent operations, implement application-level audit logging that records every agent action with tenant context, tool invoked, and outcome.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting enforced at any layer. No API Gateway, no WAF rules on ALB, no `flask-limiter` middleware in Python code. The ALB passes all requests directly to services without throttling.
- **Gap**: Zero rate limiting. Agents making rapid API calls will not be throttled. No protection against denial-of-service or runaway agent loops.
- **Recommendation**: Deploy API Gateway (preferred) with per-client usage plans and burst/rate limits. Configure WAF rate rules on the ALB. Add `flask-limiter` to each service as defense-in-depth.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Application logs include tenant_id and message_id without redaction (`app.logger.info(f"Message produced: {message}")` in `producer.py`, `logger.info(f"Message [{message_id}] persisted in DDB table: {ddb_table_name}")` in `consumer.py`). No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters.
- **Gap**: If customer PII (names, emails, order details) is added to message payloads, it will be logged in plaintext. No automated PII detection or redaction. For customer support agents handling personal data, this is a compliance risk.
- **Recommendation**: Add structured logging with PII masking before deploying customer-facing agents. Use a logging library that supports field-level redaction. Consider Amazon Macie for S3 data classification and CloudWatch Logs data protection policies.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval gates in any workflow. Argo Workflows execute automatically on SQS trigger with no approval step. TF Controller uses `approvePlan: auto` (`helm-charts/helm-tenant-chart/templates/terraform.yaml`). No CI/CD production approval gates.
- **Gap**: Complete absence of human-in-the-loop patterns. For customer-facing agents handling order management (refunds, cancellations, modifications), high-risk actions must have human approval gates. An agent approving its own refund request is a security and business risk.
- **Recommendation**: Add Step Functions with `.waitForTaskToken` for human approval on high-risk agent actions (refunds > threshold, account modifications, bulk operations). Implement an approval queue (SQS + SNS notification to support staff). This is a critical safety requirement for customer-facing agents.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: Gitea EC2 root volume is encrypted (`encrypted = true` in `terraform/modules/gitea/main.tf`). S3 buckets have public access blocked. ECR repositories use AES256 encryption. SQS queues use managed SSE (`sqs_managed_sse_enabled = true`). DynamoDB has no explicit encryption configuration (uses default AWS-managed encryption). VSCode S3 bucket uses AES256.
- **Gap**: No customer-managed KMS keys (CMKs) for any resource. DynamoDB encryption relies on AWS defaults (AWS-managed keys). S3 buckets skip KMS encryption (checkov skip comments: `CKV2_AWS_145: This S3 bucket does not required a KMS Encryption`). ECR uses AES256 instead of KMS.
- **Recommendation**: Create customer-managed KMS keys for DynamoDB tables, S3 buckets storing agent data, and SQS queues handling customer data. For agent workloads handling customer PII, CMK encryption is a compliance requirement.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No authentication on any API endpoint. Flask routes have no auth middleware, no `@login_required`, no Bearer token validation. The ALB ingress routes based on `TenantID` header matching but does not authenticate the caller. Argo Workflows server runs with `--auth-mode=server` (`03-argo-workflows.yaml`), which disables authentication entirely (noted as "for demonstration purposes only").
- **Gap**: Complete absence of API authentication. Any caller with network access can invoke any endpoint. Argo Workflows server is publicly accessible without authentication. For customer-facing agents, unauthenticated APIs are a critical security risk.
- **Recommendation**: Add JWT validation middleware to all Flask services. Deploy API Gateway with Cognito authorizer. Replace Argo Workflows `--auth-mode=server` with `--auth-mode=sso` or `--auth-mode=client`. For agent endpoints, require OAuth2 client credentials or API key authentication.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider. No Amazon Cognito, Okta, Ping, or OIDC configuration for end-user authentication. IAM roles are used for service-to-service (IRSA) but not for user identity. No SSO configuration.
- **Gap**: No centralized identity for customers, support staff, or agents. Cannot implement role-based access control for agent actions or customer authentication for support interactions.
- **Recommendation**: Deploy Amazon Cognito as the centralized identity provider. Configure tenant-scoped user pools or a shared pool with custom claims. Implement SSO for support staff. For agents, use Cognito Machine-to-Machine credentials with scoped permissions.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing. No X-Ray SDK, OpenTelemetry, Jaeger, or Zipkin in any `requirements.txt`. No trace ID propagation in HTTP headers. No `traceparent` or `X-Amzn-Trace-Id` header handling. Amazon Managed Grafana (AMG) and Amazon Managed Service for Prometheus (AMP) are mentioned in `README.md` as observability services but are not configured in the IaC. No `gen_ai.*` semantic conventions for LLM spans.
- **Gap**: Complete absence of distributed tracing. Agentic workflows span multiple components (LLM → tool selection → API call → database → response). Without trace propagation, diagnosing agent failures is impossible — you cannot see which tool the agent called, what parameters it sent, or where the chain broke.
- **Recommendation**: Add OpenTelemetry SDK to all microservices. Configure ADOT (AWS Distro for OpenTelemetry) collector on EKS. Send traces to X-Ray or Grafana Tempo. Implement `gen_ai.*` semantic conventions for LLM call tracing once agents are deployed. This is foundational for agent observability.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: Flask default logging is used throughout. `producer.py` uses `app.logger.info(f"Message produced: {message}")`. `consumer.py` uses `logging.basicConfig(stream=sys.stdout)` with `logger.info`. No JSON formatters, no `structlog`, no `python-json-logger`. No correlation IDs in log output.
- **Gap**: Unstructured, text-based logs with no correlation IDs. Cannot correlate log entries across producer → SQS → consumer → DynamoDB flows. Cannot search logs by tenant_id, request_id, or trace_id. For agents, this means you cannot reconstruct what the agent did from logs alone.
- **Recommendation**: Replace `logging.basicConfig` with `structlog` or `python-json-logger` for JSON-formatted logs. Add correlation ID middleware that generates a `request_id` per inbound request and propagates it through SQS message attributes. Include `tenant_id`, `request_id`, and `service_name` in every log entry.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, golden datasets, scoring scripts, or LLM-as-judge patterns. No `pytest` files in the microservices directories. No RAGAS, no A/B test infrastructure for prompts. No `tests/` directories in any microservice.
- **Gap**: Complete absence of automated evaluation. For customer support agents, evaluation is critical: measuring response accuracy, tool selection correctness, hallucination rate, and customer satisfaction. Deploying without evals is deploying blind.
- **Recommendation**: Create an eval framework using `pytest` with custom fixtures: define golden test cases (customer query → expected agent action → expected response), implement automated scoring (exact match, semantic similarity, LLM-as-judge), and run evals in the CI/CD pipeline before deploying agent changes.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms on latency or availability. Kubecost is deployed (`gitops/infrastructure/production/05-kubecost.yaml`) for cost tracking, but provides no SLO monitoring. No `aws_cloudwatch_metric_alarm` resources in Terraform.
- **Gap**: No SLOs for any service. Cannot measure or alert on service availability, latency percentiles, or error rates. For agents, SLOs on task success rate, response latency, and tool error rate are essential for reliability management.
- **Recommendation**: Define SLOs for each microservice (e.g., p99 latency < 500ms, error rate < 1%). Create CloudWatch alarms and dashboards. For agent services, define agent-specific SLOs: task completion rate > 90%, hallucination rate < 5%, tool error rate < 2%.

#### OPS-Q5: Rollback Capability
- **Score**: 2/4 🟠
- **Finding**: Flux CD supports GitOps-based rollback by reverting Git commits. Helm releases inherently support `helm rollback`. Image automation updates deployment manifests automatically on new ECR image pushes. However, no automated rollback triggers (e.g., rollback on error rate spike).
- **Gap**: Rollback is manual (requires Git revert). No automated rollback on health check failure or error rate threshold. No prompt versioning (relevant once agents are deployed). No feature flag system for gradual rollout.
- **Recommendation**: Add Flux CD health checks with automatic rollback on deployment failure. Implement Flagger for progressive delivery with automated rollback. For agent deployments, add prompt versioning and feature flags to roll back agent behavior changes independently of code changes.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage exists in the codebase, so no LLM cost tracking. No token counting, no cost attribution, no per-user/feature metrics. Kubecost tracks infrastructure costs but not LLM API costs.
- **Gap**: When agents are deployed, LLM inference costs will be a significant operational expense. Without per-request token tracking and cost attribution by tenant/feature, costs will be opaque and uncontrollable.
- **Recommendation**: Implement per-request token tracking from day one of agent deployment. Log Bedrock response `usage` objects (input_tokens, output_tokens) to CloudWatch custom metrics. Attribute costs by tenant_id, agent_type, and workflow. Define tiered retention policies for agent telemetry data.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: Kubecost provides infrastructure cost metrics. No custom business metrics published. No `cloudwatch.put_metric_data` calls in application code. No business KPI dashboards tracking message throughput, tenant activity, or order processing rates.
- **Gap**: Only infrastructure metrics (cost, CPU, memory). No business outcome tracking. For agents, business metrics (customer satisfaction scores, resolution rates, escalation rates) are essential for measuring agent value.
- **Recommendation**: Add custom CloudWatch metrics for message throughput, tenant activity, and response times. For agents, publish metrics for task success rate, customer satisfaction (CSAT), first-contact resolution rate, and average handle time.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection. No error rate alarms. No latency monitoring. No PagerDuty, OpsGenie, or SNS alerting integration. No composite alarms.
- **Gap**: No anomaly detection on any metric. Agents can silently degrade — calling more tools than necessary (reasoning loops), responding with lower quality, or experiencing higher latency. Without behavioral baseline monitoring, silent degradation goes undetected.
- **Recommendation**: Enable CloudWatch anomaly detection on error rates and latency for all services. Configure SNS-based alerting. For agents, add anomaly detection on tool call counts, token usage, and task completion rates to detect reasoning loops and quality degradation.

#### OPS-Q9: Deployment Strategy
- **Score**: 2/4 🟠
- **Finding**: GitOps via Flux CD provides continuous deployment. Image automation detects new ECR images and updates deployment manifests, which Flux CD reconciles to the cluster. No canary, blue/green, or traffic shifting deployment strategy. Deployments are direct — new image → updated manifest → Flux reconciles all pods.
- **Gap**: No progressive delivery. All deployments go directly to production. No canary deployments, no traffic splitting, no A/B testing. For agent deployments, this is risky — a bad agent prompt change affects 100% of traffic immediately.
- **Recommendation**: Implement Flagger with Flux CD for canary deployments. Configure progressive traffic shifting with success rate and latency gates. For agent services, canary deployments are critical — route 5% of traffic to the new agent version, validate eval metrics, then promote.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files in any microservice directory. No `tests/` directory, no `test_*.py` files, no `pytest.ini` or `conftest.py`. No integration test suites, no contract tests, no Postman/Newman collections. No test stage in the CI/CD pipeline.
- **Gap**: Complete absence of automated testing. No unit tests, integration tests, or end-to-end tests. Code changes are deployed to production without any test gate.
- **Recommendation**: Add pytest-based unit tests for each microservice. Create integration tests that validate producer → SQS → consumer → DynamoDB flow. For agents, create end-to-end tests that validate the complete agent interaction: customer query → agent processing → tool invocation → response generation.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files (markdown, YAML, or JSON) in the repository. No SSM Automation documents. No Lambda-based remediation functions. No self-healing patterns. No incident response workflows.
- **Gap**: No automated incident response. When agent services fail, response is entirely manual. No self-healing, no auto-restart, no automated escalation.
- **Recommendation**: Create machine-readable runbooks for common failure scenarios (SQS queue overflow, DynamoDB throttling, pod crash loops). Implement SSM Automation documents for automated remediation. For agents, create runbooks for agent-specific failures: reasoning loops, tool errors, and quality degradation.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO definitions with named owners. No observability ownership model. AMP and AMG are mentioned in README but not deployed or configured in IaC. Kubecost is deployed but has no documented ownership.
- **Gap**: No observability governance. No defined ownership for service-level monitoring, alerting, or incident response. When agents are deployed, it's unclear who owns agent quality, reliability, and safety monitoring.
- **Recommendation**: Create a CODEOWNERS file mapping teams to services. Define SLOs with named owners for each microservice. Establish an observability-as-a-product model where a platform team provides monitoring infrastructure and product teams own service-level and agent-level SLOs.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Not Triggered | Medium | — | — | — |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Not Triggered | High | — | — | — |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q6: 3/4, OPS-Q9: 2/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps + Move to AI — These two pathways can execute in parallel because DevOps improvements (tracing, testing, deployment strategies) are foundational and do not depend on AI-specific changes. AI enablement (agent frameworks, vector DB, RAG) can proceed concurrently.

**Sequential Dependencies**: Observability (OPS-Q1, OPS-Q2 — part of Modern DevOps) should be deployed before agent services go to production (Move to AI Phase 3). API authentication (SEC-Q9 — addressed as part of infrastructure hardening) should be complete before agents access APIs.

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - OPS-Q9: Score 2/4 — No canary or blue/green deployments; direct-to-production via Flux CD image automation
  - OPS-Q10: Score 1/4 — No integration tests; zero test coverage across all microservices
  - OPS-Q1: Score 1/4 — No distributed tracing; no OpenTelemetry or X-Ray integration
  - INF-Q6: Score 3/4 — GitOps CI/CD exists but lacks test gates between build and deploy
- **Current State**: Flux CD provides GitOps-based continuous deployment with image automation. Argo Workflows handles tenant lifecycle. However, there are no test gates, no distributed tracing, no progressive delivery, and no automated testing infrastructure.
- **Target State**: Full CI/CD with test gates, canary deployments via Flagger, distributed tracing with OpenTelemetry, integration test suites running in pipeline, and structured JSON logging with correlation IDs.
- **Key Activities**:
  1. Add OpenTelemetry SDK and ADOT collector to all microservices for distributed tracing
  2. Implement structured JSON logging with correlation IDs using `structlog`
  3. Create pytest-based unit and integration test suites for each microservice
  4. Add test stage to Gitea CI pipeline — gate image pushes on test passage
  5. Implement Flagger for canary deployments with automated rollback
  6. Define SLOs and create CloudWatch alarms for latency and error rate
- **Dependencies**: None — can start immediately
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (tracing + logging), Phase 2 (testing + canary), Phase 3 (SLOs + governance)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in any microservice
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG pipeline for knowledge retrieval
  - OPS-Q3: Score 1/4 — No automated evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: Zero AI/agent integration. No Bedrock, no agent frameworks, no vector DB, no RAG pipeline, no eval framework. The microservices are pure REST APIs with no AI capabilities.
- **Target State**: Customer-facing AI agents for support and order management built with Strands Agents SDK, powered by Amazon Bedrock, using RAG over customer documentation, with comprehensive evaluation and cost tracking.
- **Key Activities**:
  1. Deploy Amazon Bedrock with Claude/Titan models for LLM inference
  2. Create a new `agent-service` microservice using Strands Agents SDK
  3. Wrap existing producer/consumer/payments APIs as agent tools
  4. Deploy Bedrock Knowledge Base with S3 document source for RAG
  5. Build golden evaluation dataset and automated eval pipeline
  6. Implement per-request token tracking and cost attribution by tenant
  7. Add human approval workflow (Step Functions) for high-risk agent actions
- **Dependencies**: API authentication (SEC-Q9) should be in place before agents access APIs. OpenAPI specs (APP-Q2) needed for agent tool discovery.
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Bedrock setup + first agent), Phase 2 (RAG + eval), Phase 3 (scale + optimization)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Agent with SQS Order Submission** — Build a customer support agent that accepts natural-language order requests and translates them into producer API calls, sending messages to tenant-specific SQS queues.
   - **Leverages**: Existing `/producer` POST endpoint with SQS integration and tenant-aware routing
   - **Effort**: Medium
   - **Value**: Enables natural-language order submission for customers, demonstrating immediate agent value

2. **Order Data Query Agent** — Build a natural-language-to-DynamoDB query agent that lets customers ask "What are my recent orders?" and translates to DynamoDB queries against per-tenant tables.
   - **Leverages**: DynamoDB per-tenant tables with `tenant_id`/`message_id` schema (`terraform/modules/tenant-apps/main.tf`)
   - **Effort**: Medium
   - **Value**: Enables customers to query order status and history via conversational interface

3. **RAG Knowledge Agent from README and Documentation** — Build a knowledge agent that answers questions about the SaaS platform using the repository's existing documentation (README.md, architecture docs, workflow scripts).
   - **Leverages**: Existing `README.md` with comprehensive architecture documentation and workflow scripts
   - **Effort**: Low
   - **Value**: Demonstrates RAG capability and provides internal team support agent

4. **Agent-Driven JSON APIs** — Agent tool integration is straightforward with your structured JSON APIs — all three services return clean JSON responses that agents can parse without transformation.
   - **Leverages**: All microservices return structured JSON (`producer.py`, `consumer.py`, `payments.py`)
   - **Effort**: Low
   - **Value**: Agent tool wrappers can be built directly against existing API contracts

5. **DevOps Agent for Tenant Operations** — Build a DevOps agent that triggers tenant onboarding/offboarding by sending messages to the existing Argo Workflow SQS queues, enabling natural-language infrastructure operations.
   - **Leverages**: Existing SQS-triggered Argo Workflows for tenant lifecycle (`argoworkflows-onboarding-queue`, `argoworkflows-offboarding-queue`)
   - **Effort**: Medium
   - **Value**: Enables non-technical staff to onboard tenants via natural language: "Onboard tenant-15 at premium tier"

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

Low-effort, high-impact items that can be completed in 1-2 sprints:

1. **Add OpenAPI specs to all microservices**: Install `flask-smorest` or `flasgger` and auto-generate OpenAPI 3.0 specs for producer, consumer, and payments services. This unlocks agent tool discovery.
2. **Add structured logging**: Replace `logging.basicConfig` with `structlog` for JSON-formatted logs with `tenant_id`, `request_id`, and `service_name` fields in every entry.
3. **Deploy OpenTelemetry**: Add `opentelemetry-sdk` and `opentelemetry-instrumentation-flask` to each microservice. Configure ADOT collector on EKS to send traces to X-Ray.
4. **Add API versioning**: Prefix all routes with `/v1/` (e.g., `/v1/producer`, `/v1/consumer`). This is a one-line change per route.
5. **Create proof-of-concept agent**: Add a new `agent-service` directory with Strands Agents SDK wrapping the producer POST endpoint as a tool. Deploy to EKS using the existing Helm chart pattern. Use Amazon Bedrock Claude for LLM inference.
6. **Enable HPA**: Set `autoscaling.enabled: true` for producer and consumer in Helm values with appropriate min/max replicas.

### Phase 2 — Agent Foundations (Months 1–3)

Structural improvements that establish the agent infrastructure:

1. **Deploy Amazon API Gateway**: Configure API Gateway (preferred) in front of the ALB with throttling (1000 req/s default), usage plans per tenant, request validation, and Cognito authorizer. Route agent traffic through API Gateway.
2. **Deploy Amazon Cognito**: Create user pools for tenant authentication. Add JWT validation middleware to all Flask services. Implement tenant-scoped access tokens for agents.
3. **Deploy Bedrock Knowledge Base**: Create S3 bucket for support documentation. Configure Bedrock Knowledge Base with Titan Embeddings. Ingest product catalogs, order policies, and FAQ documents. Integrate with agent service for RAG.
4. **Build evaluation framework**: Create golden test dataset of 50+ customer support scenarios. Implement pytest-based eval harness with LLM-as-judge scoring. Integrate evals into Gitea CI pipeline.
5. **Add integration test suite**: Create pytest-based integration tests for producer → SQS → consumer → DynamoDB flow. Add test stage to CI pipeline gating image pushes.
6. **Implement idempotency**: Add `Idempotency-Key` header support to producer POST. Use DynamoDB conditional writes for deduplication.
7. **Add resilience patterns**: Implement `tenacity` retry with exponential backoff for all boto3 calls. Add request timeouts and circuit breaker patterns.
8. **Implement LLM cost tracking**: Log Bedrock response token usage to CloudWatch custom metrics. Create per-tenant cost attribution dashboards.
9. **Scope down IAM roles**: Replace `AdministratorAccess` on Argo Workflows and TF Controller roles with least-privilege policies. Create agent-specific IRSA role with only Bedrock InvokeModel and scoped DynamoDB/SQS access.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

Advanced capabilities that enable production-scale agent operations:

1. **Implement progressive delivery**: Deploy Flagger for canary deployments of agent services. Configure 5% → 25% → 50% → 100% traffic shifting with automated rollback on eval metric degradation.
2. **Add human approval workflows**: Deploy Step Functions with `.waitForTaskToken` for high-risk agent actions (refunds, order cancellations). Integrate with SNS for support staff notification.
3. **Define and enforce SLOs**: Create agent-specific SLOs: task completion rate > 90%, p99 latency < 2s, hallucination rate < 5%. Configure CloudWatch alarms and error budget tracking.
4. **Enable CloudTrail and audit logging**: Deploy CloudTrail with log file validation. Enable EKS audit logging. Implement application-level audit logging for all agent actions.
5. **Add anomaly detection**: Enable CloudWatch anomaly detection on agent tool call counts, token usage, and error rates. Configure alerting for reasoning loops (abnormally high tool calls per request).
6. **Optimize RAG pipeline**: Configure event-driven embedding refresh via DynamoDB Streams. Add document versioning. Implement embedding quality evaluation metrics.
7. **Add EventBridge integration**: Deploy EventBridge (preferred) for cross-service event routing. Enable agent actions to trigger downstream workflows (order status changes → EventBridge → notification service).
8. **Implement observability governance**: Create CODEOWNERS file. Define SLO ownership per service and agent. Establish shared responsibility model for agent quality monitoring.

---

## Recommended Self-Paced Learning Materials

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive DevOps modernization learning path covering CI/CD, IaC, testing, and deployment strategies
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundational DevOps concepts and AWS tooling overview
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Hands-on CI/CD pipeline creation relevant to your EKS/container architecture
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Testing strategies for CI/CD pipelines — directly addresses the OPS-Q10 gap
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Python-specific observability monitoring — directly applicable to your Flask microservices
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
  - GitOps deployment automation patterns relevant to your Flux CD + Argo Workflows setup
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
  - EKS-specific automation patterns including progressive delivery and GitOps
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1
  - Directly related workshop for your exact repository and architecture pattern

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Complete AI modernization learning path covering Bedrock, agents, and RAG
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
  - Overview of generative AI use cases including customer support agents
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundational Bedrock skills — prerequisite for agent development
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Prompt engineering for customer support agents
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on RAG implementation — directly addresses DATA-Q1 and DATA-Q3 gaps
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Agentic AI concepts and patterns — core to your agentic-ai-enablement goal
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on Strands Agents SDK lab — directly applicable to building your customer support agent
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Observable AI agent patterns — addresses the OPS-Q1 and OPS-Q3 gaps for agent observability
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Anomaly detection for AI workloads — directly relevant to OPS-Q8 gap

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `terraform/workshop/main.tf` | EKS cluster (v1.32), VPC with 3 AZs, managed node groups (m5.large), Gitea EC2 instance, SSM SecureString for secrets |
| 2 | `terraform/workshop/saas_gitops.tf` | Flux CD GitOps setup, ConfigMap with IRSA roles, SQS queue URLs, ECR URLs, Gitea integration |
| 3 | `terraform/modules/gitops-saas-infra/main.tf` | Karpenter IRSA, Argo Workflows IRSA (AdministratorAccess), TF Controller IRSA (AdministratorAccess), SQS queues for workflow triggers, S3 buckets |
| 4 | `terraform/modules/gitops-saas-infra/apps_needs.tf` | ECR repositories for microservices and Helm charts, S3 code artifacts bucket |
| 5 | `terraform/modules/tenant-apps/main.tf` | Per-tenant DynamoDB tables, SQS queues, IRSA roles with scoped policies, SSM parameters |
| 6 | `terraform/modules/gitea/main.tf` | Gitea EC2 instance with encrypted EBS, security groups with specific ingress rules, IAM role with SSM/ECR access |
| 7 | `terraform/modules/gitea/userdata.sh` | Gitea Docker setup with SQLite3, token generation, SSM SecureString storage, Gitea CI runner |
| 8 | `tenant-microservices/producer/producer.py` | Flask API with SQS send_message, tenantID header routing, no auth/rate-limiting/resilience |
| 9 | `tenant-microservices/consumer/consumer.py` | SQS polling thread, DynamoDB put_item, direct boto3 client usage, no retry/timeout patterns |
| 10 | `tenant-microservices/payments/payments.py` | Minimal Flask service stub, no AWS SDK integration, no auth |
| 11 | `tenant-microservices/producer/requirements.txt` | Flask 3.0.0, boto3 ~1.28.59 — no AI/agent/tracing/testing dependencies |
| 12 | `helm-charts/helm-tenant-chart/templates/ingress.yaml` | ALB ingress with TenantID header routing, internet-facing, no WAF/throttling |
| 13 | `helm-charts/helm-tenant-chart/templates/hpa.yaml` | HPA template exists but disabled by default (autoscaling.enabled: false) |
| 14 | `helm-charts/helm-tenant-chart/templates/terraform.yaml` | TF Controller with approvePlan: auto (no human approval gate) |
| 15 | `gitops/infrastructure/production/03-argo-workflows.yaml` | Argo Workflows with --auth-mode=server (no auth), internet-facing LB |
| 16 | `gitops/infrastructure/production/02-karpenter.yaml` | Karpenter v1.4.0 with IRSA, EKS cluster integration |
| 17 | `gitops/infrastructure/production/05-kubecost.yaml` | Kubecost for infrastructure cost tracking, Prometheus metrics |
| 18 | `gitops/control-plane/production/workflows/tenant-onboarding-sensor.yaml` | SQS EventSource triggering Argo Workflow for tenant onboarding |
| 19 | `gitops/infrastructure/base/sources/producer-image-automation.yaml` | Flux CD image automation for continuous deployment |
| 20 | `helpers/vs-code-ec2.yaml` | CloudFormation stack with EC2 instance using AdministratorAccess IAM role |
