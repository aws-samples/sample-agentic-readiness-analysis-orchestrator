# Agentic Readiness Assessment Report
**Target**: ./monolith
**Date**: 2026-03-12
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: agentic-ai-enablement
**Goal Context**: Building customer-facing AI agents for support and order management
**Repository Type**: application (auto-detected)

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
6. Microservices Decomposition Strategy
7. Quick Agent Wins
8. Readiness Roadmap
   - Phase 1 — Agent Quick Wins (Days 1–30)
   - Phase 2 — Agent Foundations (Months 1–3)
   - Phase 3 — Agent Scale & Optimization (Months 3–6)
9. Recommended Self-Paced Learning Materials
10. Appendix: Evidence Index

---

## Executive Summary

This PHP monolith e-commerce application is in the early stages of agentic AI readiness. While the application has useful foundations — structured JSON API responses, a managed RDS MySQL database defined in CloudFormation, VPC network segmentation with WAF, and auto-scaling via App Runner — it lacks nearly all capabilities required to support customer-facing AI agents for support and order management. The most critical blockers are the complete absence of AI/agent frameworks, vector databases, RAG pipelines, API documentation (which agents need to discover and invoke tools), and CI/CD automation. The tightly coupled monolithic architecture in a single `index.php` file, combined with zero observability infrastructure, means that deploying agents against this application today would be unreliable, unmonitorable, and unsafe.

### Overall Score: 1.5 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.9 / 4.0 | 🟠 |
| Application Architecture | 1.3 / 4.0 | ❌ |
| Data Foundations | 1.8 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.5 / 4.0 | 🟠 |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

These are the 5 most impactful gaps blocking agentic AI enablement for customer support and order management, weighted by agentic-ai-enablement priority criteria:

### 1. APP-Q13: No AI/Agent Frameworks (Score: 1/4)
**Why it matters for agents**: Without any AI SDK (Bedrock, LangChain, Strands Agents, OpenAI) or MCP integration, there is no mechanism to build, deploy, or orchestrate customer-facing AI agents. This is the single largest blocker for the stated goal of building AI agents for support and order management.
**First step**: Add the Strands Agents SDK (Python) or Amazon Bedrock Agent integration alongside the PHP monolith. Create a thin Python/TypeScript agent service that calls the existing JSON APIs as tools. This can be developed in parallel without modifying the monolith.

### 2. APP-Q2: No API Documentation (Score: 1/4)
**Why it matters for agents**: Agents need machine-readable API specifications (OpenAPI/Swagger) to discover, understand, and invoke tools. Without API docs, agents cannot programmatically learn what endpoints exist, what parameters they accept, or what responses to expect — every tool invocation must be manually hardcoded.
**First step**: Generate an OpenAPI 3.0 spec for the 20+ existing `/api/*` endpoints in `index.php`. This can be done manually or by using API documentation tools that inspect the route definitions.

### 3. DATA-Q1: No Vector Database (Score: 1/4)
**Why it matters for agents**: Customer support agents need semantic search to find relevant order history, product information, and past interactions. Without a vector database, agents cannot perform similarity search or retrieve contextually relevant information — they are limited to exact-match SQL queries.
**First step**: Deploy Amazon OpenSearch Service with k-NN plugin or enable pgvector on Aurora PostgreSQL. Start by vectorizing the product catalog and customer interaction history from the `interactions` table.

### 4. DATA-Q3: No RAG Implementation (Score: 1/4)
**Why it matters for agents**: A customer support agent needs to retrieve relevant context (order details, return policies, product specs) before generating responses. Without a RAG pipeline (embeddings + chunking + retrieval), agents will hallucinate or provide generic answers instead of grounded, accurate responses about specific orders and products.
**First step**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases backed by OpenSearch. Ingest product descriptions, order history patterns, and any existing support documentation.

### 5. OPS-Q3: No Automated Agent Evaluation Framework (Score: 1/4)
**Why it matters for agents**: Customer-facing AI agents for support and order management will make decisions that directly impact customers (processing returns, providing order status, recommending products). Without automated evaluation (golden datasets, scoring, LLM-as-judge), there is no way to measure agent accuracy, detect regressions, or validate that agents are providing correct information before deploying them to customers.
**First step**: Create a golden dataset of 50–100 representative customer support queries with expected responses. Set up an automated eval pipeline using RAGAS or a custom LLM-as-judge scorer that runs on every agent change.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: CloudFormation template `infrastructure/monolith-apprunner.yaml` defines `AWS::AppRunner::Service` (resource: `AppRunnerService`) — a fully managed compute platform. App Runner handles provisioning, scaling, and TLS termination automatically. Locally, `docker-compose.yml` runs the PHP app in a Docker container built from `Dockerfile` (PHP 8.2-apache). A `Dockerfile` exists confirming containerization readiness.
- **Gap**: App Runner is managed compute but does not provide the container orchestration capabilities (task definitions, service mesh, sidecar injection, custom networking) that ECS or EKS offer. Customer preference specifies ECS/container orchestration, which App Runner does not support. App Runner also limits observability integration options compared to ECS/EKS.
- **Recommendation**: Migrate from App Runner to Amazon ECS on Fargate using the existing `Dockerfile`. Define ECS task definitions in Terraform (per customer preference), configure an ALB for traffic routing, and leverage ECS service discovery for future microservices decomposition.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::RDS::DBInstance` (resource: `DBInstance`) with engine `mysql`, version `8.4.8`, instance class `db.t3.micro`, storage encrypted, backup retention of 7 days, and `PubliclyAccessible: false`. This is a fully managed database. Locally, `docker-compose.yml` runs a self-managed `mysql:8.0` container for development.
- **Gap**: RDS is managed but uses a single-AZ `db.t3.micro` instance with no Multi-AZ failover or read replicas configured. For agent workflows that require high availability for conversation history and state recovery, single-AZ introduces a single point of failure. No DynamoDB or purpose-built databases are used despite customer preference for DynamoDB.
- **Recommendation**: Enable Multi-AZ on the RDS instance for automatic failover. Consider adding DynamoDB (per customer preference) for session state, agent conversation history, and high-throughput key-value access patterns that agents will generate. Upgrade instance class for production agent workloads.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service found in the repository. The order fulfillment workflow (validate → assign warehouse → pick → pack → quality check → ship → deliver) in `index.php` is implemented as separate API endpoints (`/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, etc.) that must be called sequentially by a human operator through the admin UI. There is no state machine or workflow engine managing the transitions.
- **Gap**: Agent-driven order fulfillment requires a workflow orchestrator to manage multi-step processes with retries, error handling, and state persistence. Without orchestration, an agent calling these endpoints sequentially has no way to recover from mid-workflow failures or handle compensating transactions.
- **Recommendation**: Implement AWS Step Functions to orchestrate the order fulfillment workflow. Define the validate → assign → pick → pack → QC → ship → deliver state machine with error handling, retries, and human approval gates. Agents can then trigger and monitor Step Functions executions rather than making individual API calls. Integrate with EventBridge (per customer preference) for event-driven triggers.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, MSK, or any messaging infrastructure found in the repository. All operations in `index.php` are synchronous HTTP request/response. Order creation, return processing, warehouse assignment, and shipping are all synchronous.
- **Gap**: Agent workflows generate high volumes of asynchronous events (tool invocations, status updates, notifications). Without messaging infrastructure, agents cannot trigger background processing, receive event notifications, or decouple from slow downstream operations. The return processing workflow (currently 24-48 hours manual review) cannot be automated asynchronously.
- **Recommendation**: Deploy Amazon SQS for task queuing and Amazon EventBridge (per customer preference) for event-driven workflows. Start with: (1) SQS queue for return processing requests so agents can submit returns and poll for results, (2) SNS for order status change notifications, (3) EventBridge for cross-domain events (order placed → inventory reserved → warehouse notified).

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` is a comprehensive CloudFormation template covering: VPC (`AWS::EC2::VPC`), private subnets (2 AZs), DB subnet group, security groups (DB and App Runner), RDS instance, VPC connector, ECR repository, IAM roles (instance and access), App Runner service, auto-scaling configuration, WAF Web ACL, and IP set. This covers compute, networking, database, container registry, security, and auto-scaling.
- **Gap**: IaC is in CloudFormation but customer preference specifies Terraform. No Terraform files exist. Some infrastructure components are missing from IaC: no CloudTrail, no CloudWatch alarms, no monitoring stack, no Secrets Manager resources. The deploy.sh script is manual and not integrated with IaC.
- **Recommendation**: Migrate IaC from CloudFormation to Terraform (per customer preference). Add missing resources: AWS Secrets Manager for credential management, CloudWatch alarms, CloudTrail, and CI/CD pipeline resources. Adopt a GitOps workflow (per customer preference) with Helm charts for ECS/EKS deployment.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`, no CodePipeline in IaC. Deployment is performed via `deploy.sh`, which is a manual bash script that runs `docker-compose build` and `docker-compose up -d` locally. The CloudFormation output `DeploymentInstructions` documents a manual 6-step process: build image → authenticate to ECR → tag → push → update stack.
- **Gap**: No automated build, test, or deployment pipeline. Manual deployments are error-prone, slow, and incompatible with the rapid iteration cycles required for agent development (prompt tuning, tool updates, eval runs). Without CI/CD, there is no automated testing gate, no deployment safety net, and no audit trail of what was deployed.
- **Recommendation**: Implement a CI/CD pipeline using GitHub Actions or AWS CodePipeline with GitOps (per customer preference). Pipeline stages: lint → test → build Docker image → push to ECR → deploy to ECS via Helm. Add automated testing gates (unit tests, integration tests, agent eval suite) before production deployment.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: App Runner provides a built-in HTTPS endpoint with auto-TLS (output: `AppRunnerServiceUrl`). WAF Web ACL (`WebACL`) is configured with IP whitelisting via IP set, providing basic access control. WAF has CloudWatch metrics enabled for request monitoring.
- **Gap**: No Amazon API Gateway is configured. The App Runner endpoint lacks: request throttling/rate limiting, request/response validation, API key management, usage plans, request transformation, and caching. For agent workflows, API Gateway provides critical capabilities like per-client throttling (preventing a misconfigured agent from overwhelming the API) and request validation (rejecting malformed agent requests before they hit the application).
- **Recommendation**: Deploy Amazon API Gateway (per customer preference) in front of the application. Configure: throttling limits (per-client and global), request validation against OpenAPI spec, API key management for agent clients, and usage plans to track agent API consumption. Use ALB (per customer preference) as the internal routing layer between API Gateway and ECS.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming infrastructure found. No stream consumer patterns, no event sourcing, no CDC (Change Data Capture) patterns.
- **Gap**: Agent systems benefit from real-time event streams for: monitoring agent actions in real-time, streaming order status updates to agents, and feeding embedding refresh pipelines. Without streaming, agents must poll for updates and cannot react to events in real-time.
- **Recommendation**: Evaluate Amazon EventBridge (per customer preference) for event-driven integration. For higher-throughput needs (embedding refresh, audit streams), consider Amazon Kinesis Data Streams. Start with EventBridge for domain events and add Kinesis if real-time analytics requirements emerge.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines: VPC (`10.0.0.0/16`), 2 private subnets in separate AZs (`PrivateSubnet1`, `PrivateSubnet2`), DB security group (`DBSecurityGroup`) allowing MySQL 3306 only from `AppRunnerSecurityGroup`, App Runner security group (`AppRunnerSecurityGroup`), VPC connector for App Runner egress, and RDS set to `PubliclyAccessible: false`. WAF provides IP-based access control.
- **Gap**: No public subnets or NAT gateway defined (App Runner handles egress via VPC connector). Security groups follow least-privilege for database access. However, no NACLs are explicitly configured (relying on default allow-all), and WAF rules are limited to IP whitelisting without rate limiting or bot protection rules.
- **Recommendation**: Add explicit NACLs for defense-in-depth. Add WAF rate limiting rules to protect against agent-driven request floods. When migrating to ECS, ensure services are placed in private subnets with ALB in public subnets. Add AWS Shield Standard (included) and consider Shield Advanced for DDoS protection.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::AppRunner::AutoScalingConfiguration` (resource: `AutoScalingConfiguration`) with `MinSize` (default 1), `MaxSize` (default 3), and `MaxConcurrency: 100`. These values are parameterized via CloudFormation parameters `AutoScalingMinSize` and `AutoScalingMaxSize`.
- **Gap**: Auto-scaling is configured for App Runner but with conservative defaults (max 3 instances). No scaling policies based on custom metrics (latency, queue depth). When migrating to ECS, auto-scaling will need to be reconfigured with ECS Service Auto Scaling and Application Auto Scaling policies. Agent workloads can be bursty and require faster scale-out.
- **Recommendation**: When migrating to ECS, configure Application Auto Scaling with target tracking policies on CPU, memory, and request count. Set appropriate min/max based on expected agent traffic patterns. Consider separate scaling policies for agent-facing services vs. user-facing services.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: The application is written entirely in PHP 8.2, as specified in `Dockerfile` (`FROM php:8.2-apache`). The single file `index.php` contains all application logic (~2,600 lines). No `composer.json` dependency manifest exists — the only PHP extensions are PDO and pdo_mysql installed in the Dockerfile.
- **Gap**: PHP has a significantly limited AI/agent framework ecosystem compared to Python or TypeScript. There are no mature equivalents of LangChain, Strands Agents, or CrewAI for PHP. Building customer-facing AI agents in PHP would require building framework-level capabilities from scratch or maintaining a polyglot architecture.
- **Recommendation**: Introduce a Python or TypeScript agent service alongside the PHP monolith. The agent service would call the PHP monolith's JSON APIs as tools. This polyglot approach lets the team use the best language for agents (Python: Strands Agents, LangChain, Bedrock SDK) while preserving the existing PHP application. Over time, as services are extracted from the monolith, they can be written in Python/TypeScript.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specifications found. No `openapi.yaml`, `swagger.json`, or any API documentation files exist in the repository. The 20+ API endpoints in `index.php` are defined inline using `preg_match` route patterns with no annotations, docblocks, or schema definitions. Endpoints include: `GET /api/products`, `POST /api/orders`, `GET /api/orders/{id}/validation-data`, `GET /api/warehouses/assignment-options`, `POST /api/orders/{id}/validate`, `POST /api/orders/{id}/assign-warehouse`, `POST /api/orders/{id}/pick`, `POST /api/orders/{id}/pack`, `POST /api/orders/{id}/quality-check`, `POST /api/orders/{id}/ship`, `POST /api/returns`, and more.
- **Gap**: This is a critical blocker for agentic AI. Agents need machine-readable API specifications to discover and invoke tools. Without OpenAPI specs, each agent tool must be manually hardcoded with endpoint details, parameter schemas, and response formats. Any API change will silently break agent tool definitions.
- **Recommendation**: Create an OpenAPI 3.0 specification documenting all 20+ `/api/*` endpoints with request/response schemas, parameter types, authentication requirements, and error responses. Publish this spec at a well-known endpoint (e.g., `/api/docs/openapi.json`) so agents can dynamically discover available tools.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All API operations in `index.php` are synchronous HTTP request/response. Order creation (line ~200: `POST /api/orders`) performs inventory check, order insert, item insert, payment insert, and status update all within a single synchronous database transaction. Return processing (`POST /api/returns`) is synchronous with a message stating "24-48 hours" manual review. There are no message publishing patterns, no event-driven handlers, no queue consumers, no async invocations anywhere in the codebase.
- **Gap**: 100% synchronous communication is incompatible with agent workflows. Agents need to initiate long-running operations (return processing, warehouse assignment, shipping) and receive results asynchronously. Synchronous operations block the agent thread and create timeout risks for operations that take longer than typical HTTP timeouts.
- **Recommendation**: Introduce async patterns using SQS (per customer preference) for long-running operations. Implement a job-status API pattern: agent submits a request → receives a job ID → polls for completion. Start with return processing (currently 24-48 hours) and order fulfillment workflow steps as async candidates.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: The entire application is a single `index.php` file (~2,600 lines) containing all business domains tightly coupled together: orders, order items, inventory, payments, returns, customer interactions, warehouses, shipping, user management, and the HTML/CSS/JavaScript frontend. All domains share a single MySQL database with foreign key relationships across tables (e.g., `order_items.order_id REFERENCES orders(id)`, `payments.order_id REFERENCES orders(id)`, `returns.order_id REFERENCES orders(id)`). Business logic is interleaved with routing (`preg_match` for URL patterns), presentation (embedded HTML/CSS/JS), and data access (inline PDO queries). There are no module boundaries, no interfaces, no separation of concerns. A change to the return processing logic risks breaking order creation, inventory management, or payment processing.
- **Gap**: A tightly coupled monolith prevents: (1) assigning agent tools to specific domains (an order agent shouldn't need access to user management code), (2) independent scaling of agent-heavy vs. user-heavy services, (3) failure isolation (a bug in shipping logic could take down the entire application), (4) incremental modernization (can't upgrade one domain without deploying everything).
- **Recommendation**: See the Microservices Decomposition Strategy section for a condensed approach. For now, agents can interact with the monolith via its existing API surface while planning service extraction.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API endpoints in `index.php` return structured JSON responses via `json_encode()`. The `Content-Type: application/json` header is set for all `/api/` routes (line ~170). Response structures are consistent and well-organized. Examples: `GET /api/products` returns `{"products": [...]}`, `POST /api/orders` returns `{"success": true, "order_id": "...", "total_amount": ...}`, `GET /api/orders/{id}/validation-data` returns a rich structured response with `order`, `customer`, `risk_factors`, `fraud_score`, and `recommendation` fields.
- **Gap**: None — JSON API responses are agent-friendly and well-structured.
- **Recommendation**: Maintain JSON response format. When creating OpenAPI specs (APP-Q2), define JSON Schema for all response types to enable agent response validation.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration engine is used. The order fulfillment workflow (validate → assign warehouse → pick → pack → quality check → ship → deliver) is implemented as 7 separate API endpoints in `index.php` that must be called manually in sequence by a human admin via the UI. The `update_order_status()` helper function logs status transitions to `order_status_history`, but there is no state machine enforcing valid transitions. For example, nothing prevents calling `/api/orders/{id}/ship` before `/api/orders/{id}/quality-check`.
- **Gap**: Without a workflow engine, an agent orchestrating order fulfillment has no guardrails: it could skip steps, repeat steps, or call steps out of order. There is no automatic retry on failure, no compensation logic, and no timeout handling. The 7-step fulfillment workflow is a prime candidate for Step Functions orchestration.
- **Recommendation**: Implement AWS Step Functions for the order fulfillment workflow. Define allowed state transitions, add retry policies with exponential backoff, implement compensation (rollback) for failed steps, and add human-in-the-loop approval gates where needed (e.g., high-value orders). Agents would trigger Step Functions executions and monitor their progress.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency mechanisms found. IDs are generated using PHP's `uniqid()` function (e.g., `uniqid('order-')`, `uniqid('pay-')`, `uniqid('return-')` in `index.php`), which generates a new unique ID on every call — making retried requests create duplicate records. No `Idempotency-Key` headers, no deduplication tokens, no upsert patterns. The order creation endpoint (`POST /api/orders`) will create duplicate orders if called twice with the same data.
- **Gap**: Agents will retry failed API calls. Without idempotency, each retry creates duplicate orders, duplicate payments, duplicate returns. This is a data integrity risk that makes agent automation unsafe. A customer support agent retrying a return request could issue duplicate refunds.
- **Recommendation**: Add idempotency key support to all write endpoints. Accept an `Idempotency-Key` header, store it in a DynamoDB table (per customer preference) with a TTL, and return the cached response for duplicate requests. Prioritize: `POST /api/orders`, `POST /api/returns`, `POST /api/admin/approve-return`, and all fulfillment action endpoints.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: WAF Web ACL (`WebACL` in `monolith-apprunner.yaml`) provides IP-based access control via IP whitelisting, but contains no rate limiting rules. No application-level rate limiting middleware exists in `index.php`. No API Gateway throttling is configured. No `express-rate-limit` equivalent for PHP.
- **Gap**: Without rate limiting, a misconfigured agent could send thousands of requests per second, overwhelming the application and database. Agent systems are particularly vulnerable to runaway loops where an agent repeatedly calls the same tool. Rate limiting is a critical safety mechanism for agent deployments.
- **Recommendation**: Deploy Amazon API Gateway (per customer preference) with throttling configured: global rate limit (e.g., 100 req/sec) and per-client rate limits (e.g., 10 req/sec per agent). Add WAF rate-based rules as a secondary layer. Consider adding application-level rate limiting middleware for defense-in-depth.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retries with backoff, or timeout configurations found in `index.php`. The database connection in `get_db()` has no timeout setting — it uses default PDO timeouts. API error handling consists of try/catch blocks that return generic error JSON (`{"error": $e->getMessage()}`), but there are no retry mechanisms, no circuit breaker patterns, and no timeout configurations on any operations.
- **Gap**: Agent workflows amplify failure modes. When the database is slow or unavailable, every agent request will hang until PHP's default timeout. Without circuit breakers, a cascade failure from one slow dependency (e.g., RDS) will block all agent operations. Without retries with exponential backoff, transient failures become permanent failures.
- **Recommendation**: Add resilience patterns before agent deployment: (1) PDO connection timeout and query timeout settings, (2) retry with exponential backoff for database operations, (3) circuit breaker pattern for external service calls (when services are extracted). When migrating to ECS, use a service mesh (App Mesh) or sidecar proxy for cross-service resilience.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All operations in `index.php` are synchronous with no background job processing. The return processing flow explicitly states it requires "24-48 hours" manual review (response message in `POST /api/returns`). No background job framework (no Celery, no Bull, no PHP queue workers, no SQS consumers). No async/polling patterns. No job status APIs.
- **Gap**: Customer support agents need to initiate operations that take longer than HTTP timeout windows: return processing, order fulfillment multi-step workflows, bulk inventory updates. Without async job handling, agents will time out waiting for these operations.
- **Recommendation**: Implement SQS-backed (per customer preference) async job processing. Pattern: agent submits request → API returns job ID immediately → agent polls `/api/jobs/{id}/status` for completion. Start with return processing as the first async job, then extend to order fulfillment steps.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning found. All endpoints use unversioned paths (e.g., `/api/orders`, `/api/products`, `/api/returns`). No `/v1/`, `/v2/` URL patterns, no `Accept-Version` headers, no versioning annotations, no API changelog.
- **Gap**: Agent tool definitions are tightly coupled to API contracts. When API response formats change, agent tools break. Without versioning, there is no way to evolve APIs while maintaining backward compatibility for existing agent tool definitions. A change to the order response structure could break every agent in production simultaneously.
- **Recommendation**: Adopt URL path versioning (e.g., `/api/v1/orders`). Implement a deprecation policy: new versions are released alongside old ones, agents are migrated to new versions, old versions are deprecated with advance notice. Use API Gateway (per customer preference) for version routing.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith with no inter-service communication. The database connection uses environment variables (`DB_HOST` in `index.php` `get_db()` function, set via `docker-compose.yml` and CloudFormation). No AWS Service Discovery, no App Mesh, no Consul, no API catalog. No service registry.
- **Gap**: As services are extracted from the monolith, agents will need to discover and route to individual service endpoints. Without service discovery, agents would need hardcoded endpoints for each service, creating fragile configurations that break when services move or scale.
- **Recommendation**: When migrating to ECS, enable AWS Cloud Map for service discovery. Register each extracted service in a service registry. Use API Gateway (per customer preference) as the unified API catalog that agents interact with, routing to individual services behind the scenes.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework usage found anywhere in the repository. No Bedrock SDK (`boto3` with `bedrock-runtime`), no LangChain, no LangGraph, no CrewAI, no Strands Agents, no OpenAI SDK, no Anthropic SDK, no MCP (Model Context Protocol) SDK or server. No `composer.json` exists, so no PHP AI packages either. No embedding model calls, no LLM invocations, no prompt templates.
- **Gap**: This is the most fundamental blocker for the stated goal of "Building customer-facing AI agents for support and order management." Without any AI framework, there is zero agent capability — no way to process natural language queries, no way to orchestrate multi-step agent workflows, no way to invoke LLMs for reasoning.
- **Recommendation**: Deploy a Python-based agent service using Strands Agents SDK or Amazon Bedrock Agents. The agent service would: (1) accept natural language queries from customers, (2) use the existing PHP JSON APIs as tools (order lookup, return processing, product search), (3) leverage Bedrock foundation models for reasoning, (4) implement MCP for standardized tool definitions. This can be built as a separate ECS service (per customer preference) that calls the monolith's APIs.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No Amazon OpenSearch with k-NN plugin, no Aurora pgvector extension, no S3 Vectors, no Bedrock Knowledge Bases, no Pinecone, no Weaviate, no Chroma. The only database is MySQL (RDS in IaC, MySQL 8.0 in docker-compose), which does not support vector similarity search natively.
- **Gap**: Customer support agents for order management need semantic search to find relevant orders, products, and past interactions based on natural language queries. Without a vector database, agents cannot perform similarity search — they are limited to exact-match SQL queries (e.g., `WHERE order_id = ?`). A customer asking "I ordered some blue shoes last month" cannot be matched to the correct order without semantic search.
- **Recommendation**: Deploy Amazon OpenSearch Service with k-NN plugin for vector similarity search. Alternatively, consider Amazon Bedrock Knowledge Bases for a fully managed RAG solution. Start by vectorizing: product descriptions (`inventory.description`), customer interaction notes (`interactions.notes`), and order history for semantic order lookup.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1), so there is no vector DB management to evaluate. No managed or self-hosted vector store of any kind.
- **Gap**: When a vector database is deployed (DATA-Q1), it must be a managed service to avoid operational overhead that would slow agent development.
- **Recommendation**: Use a fully managed vector store: Amazon OpenSearch Serverless (for zero operational overhead) or Amazon Bedrock Knowledge Bases (for turnkey RAG). Avoid self-hosted vector databases that require cluster management, scaling, and patching.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG (Retrieval-Augmented Generation) pipeline found. No document chunking, no embedding generation, no similarity search patterns, no Bedrock Knowledge Base integration. No embedding model calls (no Bedrock Titan Embeddings, no OpenAI ada). No chunking/splitting code.
- **Gap**: A customer support agent must ground its responses in actual data — order details, product specifications, return policies, interaction history. Without RAG, agents will either hallucinate answers or be limited to simple database lookups that don't understand natural language context.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases: (1) Create an S3 bucket for knowledge documents (product catalogs, return policies, FAQ), (2) Configure Bedrock Knowledge Base with OpenSearch Serverless as the vector store, (3) Ingest and chunk documents, (4) Generate embeddings using Bedrock Titan Embeddings, (5) Query the knowledge base from the agent service for grounded responses.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Single MySQL database with 9 tables: `orders`, `order_items`, `inventory`, `payments`, `returns`, `interactions`, `order_status_history`, `warehouses`, `users`. All data access goes through a single PDO connection in `get_db()` function in `index.php`. No external API calls, no secondary databases, no third-party data integrations.
- **Gap**: While a single data source is simple, the tables serve multiple business domains (orders, inventory, payments, returns, users, warehouses) with cross-table foreign key dependencies. When services are extracted, data source sprawl will increase. Additionally, agent capabilities will require new data sources (vector DB, knowledge base, conversation history store).
- **Recommendation**: Maintain the single RDS MySQL as the transactional data store for now. When extracting services, use the database-per-service pattern. Plan for additional data sources: DynamoDB (per customer preference) for agent conversation history, OpenSearch for vector search, S3 for document storage.

#### DATA-Q5: Data Access Pattern
- **Score**: 1/4 ❌
- **Finding**: All database access in `index.php` is via direct PDO queries inline in API route handlers. Examples: `$stmt = $db->prepare('SELECT * FROM orders WHERE id = ?')` appears in multiple route handlers, `$db->query('SELECT * FROM inventory')` in the products endpoint, `$db->prepare('INSERT INTO orders VALUES ...')` in the order creation handler. There is no data access layer, no repository pattern, no ORM (no Doctrine, no Eloquent). SQL queries are mixed directly with business logic and routing.
- **Gap**: Direct database access from API handlers means agents cannot access data through a clean API layer — they must go through the monolith's endpoints. When services are extracted, scattered database queries make it difficult to identify and migrate data access patterns. There is no single point of data contract that agents can rely on.
- **Recommendation**: Refactor data access into a repository/DAO layer before service extraction. Group queries by domain (OrderRepository, InventoryRepository, PaymentRepository). This creates clear data contracts that will become service APIs. In the agent architecture, all agent data access should go through service APIs, never direct database connections.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing, no Textract integration, no unstructured data handling. All data is structured in MySQL tables. Product images are referenced by URL (`image_url` column in `inventory` table) but not stored or processed by the application. No PDF processing, no image analysis, no document extraction.
- **Gap**: Customer support agents often need to process unstructured data: customer-uploaded photos of damaged products, PDF invoices, email threads, chat transcripts. Without unstructured data handling, agents cannot process these inputs.
- **Recommendation**: Deploy S3 (with versioning and lifecycle policies) for unstructured data storage. Add Amazon Textract for document extraction (invoices, receipts). Integrate with the RAG pipeline (DATA-Q3) to make unstructured documents searchable by agents.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: Database schema is defined in the `init_db()` function in `index.php` using `CREATE TABLE IF NOT EXISTS` statements. The schema includes column types, constraints, foreign keys, and indexes. Schema evolution is handled via `ALTER TABLE` with try/catch blocks (e.g., adding `warehouse_location`, `weight_lbs`, `dimensions` columns to `inventory`). No dedicated migration tool (no Flyway, no Liquibase, no Alembic), no JSON Schema files, no Avro/Protobuf definitions.
- **Gap**: Schema is documented in code but not in a machine-readable format that agents can consume. Schema changes via ALTER TABLE with try/catch are fragile and not version-tracked. There is no way for an agent to programmatically discover the data model.
- **Recommendation**: Extract schema definitions into a proper database migration tool (Flyway or Liquibase for MySQL). Create JSON Schema definitions for all API request/response payloads as part of the OpenAPI spec (APP-Q2). Consider generating ER diagrams for agent context.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer exists. PDO queries are scattered across 20+ route handlers in `index.php`. The same tables are queried from multiple locations: `orders` is queried in at least 15 different route handlers, `inventory` is queried in 5+ handlers, `order_items` in 8+ handlers. There is no centralized repository, no query builder abstraction, no consistent error handling for data operations.
- **Gap**: Without a data access layer, there is no single point of data contract. When agents need to access data, they must go through individual API endpoints rather than a consistent data interface. Database query logic is duplicated across handlers, making it difficult to add cross-cutting concerns like caching, audit logging, or access control.
- **Recommendation**: Create domain-specific repository classes (OrderRepository, InventoryRepository, PaymentRepository, ReturnRepository) that encapsulate all database queries. Each repository becomes the single source of truth for data access in its domain. When services are extracted, repositories become the data access layer of each microservice.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1, DATA-Q3), so there is no embedding refresh pipeline. No event-driven embedding triggers, no scheduled re-indexing, no CDC (Change Data Capture) patterns, no Bedrock Knowledge Base sync configuration.
- **Gap**: When embeddings are created (DATA-Q1, DATA-Q3), they must be kept fresh as products, orders, and interactions change. Stale embeddings cause agents to return outdated information — a customer asking about a product that was updated yesterday would get old information.
- **Recommendation**: Implement event-driven embedding refresh: (1) use EventBridge (per customer preference) to emit events when data changes (order created, product updated, interaction logged), (2) trigger an embedding update function that re-vectorizes the changed records, (3) update the vector store. For Bedrock Knowledge Bases, configure automatic sync schedules.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: CloudFormation template `monolith-apprunner.yaml` explicitly pins `EngineVersion: '8.4.8'` on the `DBInstance` resource. MySQL 8.4 is a current, actively supported LTS (Long Term Support) release with end of support in April 2032. The `docker-compose.yml` uses `mysql:8.0` for local development, which is also a supported version (end of support April 2026, with extended support available). `AutoMinorVersionUpgrade: true` is enabled in CloudFormation.
- **Gap**: None — database engine versions are explicitly pinned and current.
- **Recommendation**: Monitor MySQL 8.0 EOL for the local development environment (April 2026). Consider updating `docker-compose.yml` to `mysql:8.4` to match production. Continue using `AutoMinorVersionUpgrade: true` for automatic security patches.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs found. All database operations in `index.php` use standard SQL (SELECT, INSERT, UPDATE, DELETE) via PDO prepared statements. No `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` statements. No PL/SQL or T-SQL patterns. The `init_db()` function uses only standard DDL (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE`). All business logic is in the PHP application layer. The database engine is MySQL with InnoDB — an open-source engine.
- **Gap**: None — clean separation of business logic from database layer.
- **Recommendation**: Maintain this pattern. Keep all business logic in the application layer. This makes future database migration (e.g., to Aurora MySQL or DynamoDB for specific use cases) significantly easier.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded in multiple locations. `docker-compose.yml` contains plaintext credentials: `MYSQL_ROOT_PASSWORD: rootpassword`, `MYSQL_USER: ecommerce_user`, `MYSQL_PASSWORD: ecommerce_pass`. CloudFormation template uses `Parameters` with `NoEcho: true` but includes insecure defaults: `Default: ChangeMe123!` for `DBPassword` and `Default: ecommerce_user` for `DBUsername`. In `index.php`, the `get_db()` function has fallback credentials: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. No AWS Secrets Manager, no HashiCorp Vault, no SSM Parameter Store.
- **Gap**: Hardcoded credentials are a critical security risk, especially for agent workloads that will need credentials for multiple services (database, Bedrock, OpenSearch, API keys). Secrets in source control are visible to anyone with repo access.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager. Reference secrets in CloudFormation via `{{resolve:secretsmanager:...}}`. In ECS (per customer preference), inject secrets via task definition secret references. Remove all hardcoded credentials from `docker-compose.yml` and `index.php` fallbacks. Use `.env` files (gitignored) for local development only.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: CloudFormation defines two IAM roles. `AppRunnerInstanceRole` uses the managed policy `arn:aws:iam::aws:policy/CloudWatchLogsFullAccess` — an overly broad policy granting full CloudWatch Logs access (including actions like `CreateLogGroup`, `DeleteLogGroup`, `PutRetentionPolicy` on all resources). `AppRunnerAccessRole` uses `AWSAppRunnerServicePolicyForECRAccess` — an appropriate, scoped policy for ECR image pulling. No wildcard `Action: "*"` or `Resource: "*"` is used, but the FullAccess managed policy grants more permissions than needed.
- **Gap**: `CloudWatchLogsFullAccess` includes destructive actions (delete log groups, modify retention) that the application does not need. For agent workloads, additional IAM roles will be needed for Bedrock, OpenSearch, DynamoDB, S3, and SQS access — each must follow least privilege.
- **Recommendation**: Replace `CloudWatchLogsFullAccess` with a custom policy granting only `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` on the specific log group. When adding agent infrastructure, create per-service IAM roles with scoped policies: Bedrock invoke-model only, DynamoDB read/write on specific tables, SQS send/receive on specific queues.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Authentication is PHP session-based using `$_SESSION['user']` (set during `POST /login` in `index.php`). Session data includes user ID, name, email, and role. API routes check `if (!isset($_SESSION['user']))` for auth and `$_SESSION['user']['role'] !== 'admin'` for admin authorization. No JWT/OAuth token exchange, no Cognito integration, no OIDC/SAML. The login form authenticates with username/password against the `users` table in MySQL using `password_verify()` with bcrypt.
- **Gap**: PHP sessions cannot propagate user identity to external agent services. When an AI agent makes API calls on behalf of a customer, the session-based auth model has no mechanism to attach customer context to agent requests. Agents need token-based identity (JWT/OAuth2) to carry user context across service boundaries.
- **Recommendation**: Implement Amazon Cognito (or another centralized IdP) for authentication. Issue JWTs on login, validate JWTs on API requests. Include user context (customer_id, role, permissions) in JWT claims. Agent services can then propagate customer identity end-to-end by forwarding the JWT in API calls.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in IaC. No audit logging infrastructure. The only logging is PHP's `ini_set('log_errors', '1')` in `index.php`, which logs to Apache's default error log. WAF has `CloudWatchMetricsEnabled: true` for request metrics, but this is metric data, not audit logs. The `order_status_history` table records order status changes with `changed_by` field, which provides application-level audit for order workflows but not infrastructure-level auditing.
- **Gap**: Agent actions must be auditable. When an AI agent processes a return, approves a refund, or ships an order, there must be an immutable audit trail of what the agent did, when, and on whose behalf. Without CloudTrail and structured application audit logs, there is no way to investigate agent behavior or satisfy compliance requirements.
- **Recommendation**: Enable AWS CloudTrail with log file validation and immutable S3 storage (Object Lock). Implement structured application-level audit logging that records every agent action with: timestamp, agent ID, user context, action taken, resources modified, and outcome. Store audit logs in CloudWatch Logs with long retention.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: WAF Web ACL (`WebACL`) provides IP whitelisting but no rate limiting rules. No `AWS::WAFv2::RateBasedRule` in CloudFormation. No API Gateway with usage plans or throttling. No application-level rate limiting middleware in `index.php`.
- **Gap**: Agent workloads can generate significantly higher request volumes than human users. Without rate limits, a single misconfigured or runaway agent can overwhelm the application. Per-client rate limiting is essential to prevent one agent from consuming all available capacity.
- **Recommendation**: Deploy API Gateway (per customer preference) with: global rate limit (1000 req/sec), per-API-key throttling (50 req/sec per agent), usage plans with quotas, and burst limits. Add WAF rate-based rules (100 requests per 5 minutes per IP) as a secondary layer.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction or masking found. Customer PII (names, emails, addresses) is stored in multiple tables (`orders.customer_name`, `orders.customer_email`, `orders.shipping_address`, `users.email`, `users.name`) and returned directly in API responses without any masking. The `GET /api/orders/{id}/validation-data` endpoint returns full customer name, email, account history, and address. PHP error logging (`ini_set('log_errors', '1')`) may log PII in error messages. No Amazon Macie, no log scrubbing middleware.
- **Gap**: AI agents will process and potentially log PII during customer support interactions. Without PII redaction, sensitive customer data may appear in agent logs, LLM provider logs (prompt/response pairs), and observability tools. This creates compliance risks (GDPR, CCPA) and data leakage risks.
- **Recommendation**: Implement PII redaction: (1) Add middleware that masks PII in API responses for agent consumers (e.g., email → j***@example.com), (2) Configure log scrubbing to detect and redact PII patterns (email, phone, SSN, credit card), (3) Enable Amazon Macie for S3 bucket PII scanning, (4) Use Bedrock Guardrails to filter PII from agent prompts and responses.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: The application has manual approval patterns: the return approval flow (`POST /api/admin/approve-return`) requires admin role verification (`$_SESSION['user']['role'] !== 'admin'`), and the fulfillment workflow has manual steps in the admin UI (validate, assign warehouse, pick, pack, QC, ship). The order validation endpoint (`POST /api/orders/{id}/validate`) accepts an `approved` boolean from admin review. However, these are simple UI-driven manual processes — no formal approval workflow engine, no Step Functions with `waitForTaskToken`, no approval queues, no escalation paths.
- **Gap**: When agents automate these workflows, high-risk actions (return approvals, refunds, high-value order validation) need formal human-in-the-loop gates — not just manual UI buttons. Agents need a programmatic way to request human approval, pause execution, and resume after approval.
- **Recommendation**: Implement Step Functions with `waitForTaskToken` for human approval workflows. Define which actions require human approval: refunds above a threshold, bulk operations, account modifications. Create an approval queue (SQS per customer preference) with SNS notifications to approvers. Integrate with the agent workflow so agents can request approval and resume execution after it's granted.

#### SEC-Q8: Encryption at Rest
- **Score**: 3/4 🟡
- **Finding**: RDS instance has `StorageEncrypted: true` in CloudFormation (`DBInstance` resource), using the default AWS-managed KMS key (no `KmsKeyId` specified). ECR repository uses `EncryptionType: AES256` for container image encryption. No customer-managed KMS keys are defined anywhere in the IaC.
- **Gap**: AWS-managed encryption keys provide basic encryption at rest but do not allow key rotation control, cross-account sharing, or granular access policies. For agent workloads handling customer PII, customer-managed KMS keys provide better control over encryption and access auditing.
- **Recommendation**: Create customer-managed KMS keys for sensitive data stores (RDS, S3 for knowledge base, DynamoDB for conversation history). Define KMS key policies that restrict access to specific IAM roles. Enable automatic key rotation.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: All `/api/*` routes in `index.php` check for session-based authentication: `if (!isset($_SESSION['user'])) { http_response_code(401); echo json_encode(['error' => 'Unauthorized']); exit; }`. Admin endpoints additionally check `$_SESSION['user']['role'] !== 'admin'`. Login authenticates via username/password against the `users` table using `password_verify()` with bcrypt. However, no OAuth2, no JWT, no API keys, no Bearer token validation.
- **Gap**: Session-based auth requires the client to manage cookies, which is not compatible with agent-to-API communication. Agents need stateless token-based authentication (JWT/OAuth2) or API keys. Sessions also cannot carry scoped permissions (e.g., agent can read orders but not delete users).
- **Recommendation**: Implement JWT-based API authentication using Amazon Cognito. Issue JWTs with scoped claims (permissions, customer context). Create separate authentication flows for: human users (Cognito hosted UI), agent services (machine-to-machine OAuth2 client credentials), and API consumers (API keys via API Gateway).

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider. User accounts are stored in the `users` table in MySQL with columns: `id`, `username`, `password` (bcrypt hash), `name`, `email`, `role`, `created_at`. Authentication is handled by the monolith itself via `POST /login`. No Cognito, no Okta, no Ping, no SAML/OIDC federation, no SSO.
- **Gap**: A MySQL users table cannot serve as an identity provider for a multi-service agent architecture. Agent services, API Gateway, and extracted microservices all need a centralized identity provider for consistent authentication and authorization. Without centralized identity, each service would need its own auth implementation.
- **Recommendation**: Deploy Amazon Cognito as the centralized identity provider. Migrate existing users from MySQL to Cognito User Pool. Configure: (1) Cognito hosted UI for human user login, (2) Machine-to-machine authentication for agent services (OAuth2 client credentials), (3) API Gateway Cognito authorizers, (4) JWT validation in all services.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing found. No AWS X-Ray SDK, no OpenTelemetry SDK, no Datadog/Jaeger/Zipkin agents. No trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`). No instrumentation wrappers. App Runner provides basic CloudWatch logging but no trace correlation. No `gen_ai.*` semantic conventions. No service mesh or APM configuration.
- **Gap**: Agent workflows span multiple components — LLM calls, tool invocations, database queries, and potentially multiple service calls. Without distributed tracing, when an agent fails to process a customer request, there is no way to reconstruct the execution path: which tools were called, in what order, what parameters were used, and where the failure occurred. This makes debugging agent issues impossible in production.
- **Recommendation**: Implement OpenTelemetry SDK with AWS X-Ray exporter. Instrument: (1) all API endpoints with trace context, (2) database queries with span attributes, (3) agent LLM calls with `gen_ai.*` semantic conventions, (4) tool invocations with input/output correlation. When deploying on ECS, use the AWS Distro for OpenTelemetry (ADOT) sidecar.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: PHP error logging is configured via `ini_set('log_errors', '1')` and `ini_set('display_errors', '0')` in `index.php`. Logs go to Apache's default error log format (not JSON). No structured logging library (no Monolog JSON formatter, no structlog). No correlation IDs in log output. No CloudWatch Log Insights queries. Error responses use `json_encode(['error' => $e->getMessage()])` but these are API responses, not logs.
- **Gap**: Unstructured logs cannot be efficiently queried, correlated, or analyzed. When investigating agent issues, structured JSON logs with correlation IDs (trace_id, request_id, user_id, agent_id) are essential for filtering and correlating events across the request lifecycle.
- **Recommendation**: Implement structured JSON logging using Monolog with a JSON formatter. Add correlation ID middleware that generates a request_id for each request and includes it in all log entries. Include structured fields: timestamp, level, message, request_id, user_id, endpoint, duration_ms, and error details. Ship logs to CloudWatch Logs for CloudWatch Log Insights querying.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework found. No eval datasets, no golden test files, no scoring scripts, no LLM-as-judge patterns, no RAGAS configuration, no A/B test infrastructure for prompts. No test files of any kind exist in the repository (no PHPUnit, no integration tests).
- **Gap**: Customer-facing AI agents for support and order management will make consequential decisions (processing returns, providing order information). Without automated evaluation, there is no way to measure agent quality (accuracy, helpfulness, safety), detect regressions when prompts or tools change, or validate that agents meet quality thresholds before deployment.
- **Recommendation**: Build an automated evaluation pipeline: (1) Create a golden dataset of 50-100 customer support scenarios with expected agent responses, (2) Implement scoring using RAGAS metrics (faithfulness, answer relevancy, context precision) or a custom LLM-as-judge, (3) Run evals in CI/CD before deploying agent changes, (4) Track eval scores over time with CloudWatch custom metrics.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms defined in the CloudFormation template. App Runner has a health check (`HealthCheckConfiguration` with HTTP path `/`, interval 10s, timeout 5s), but this is a basic liveness check, not an SLO. No p99/p95 latency targets, no error rate thresholds, no availability targets, no SLO dashboards.
- **Gap**: Without SLOs, there is no definition of "good enough" for agent performance. How fast should an agent respond? What error rate is acceptable? Without these targets, degradations go unnoticed until customers complain.
- **Recommendation**: Define SLOs for critical agent-facing journeys: (1) API latency p99 < 500ms for order lookups, (2) Agent response time p95 < 5s for customer queries, (3) Error rate < 1% for all API endpoints, (4) Agent task success rate > 95%. Implement CloudWatch alarms for each SLO with SNS notifications.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback mechanism. App Runner deployments replace the running service with no automatic rollback. `deploy.sh` runs `docker-compose up -d` which overwrites the current deployment. CloudFormation updates replace resources in-place. No blue/green deployment, no canary releases, no feature flags, no prompt versioning. The RDS instance has `DeletionPolicy: Snapshot` and `UpdateReplacePolicy: Snapshot` for database protection, but no application-level rollback.
- **Gap**: Agent deployments include code changes, prompt changes, and tool definition changes — all of which can cause regressions. Without rollback capability, a bad agent deployment stays in production until a manual fix is deployed. For customer-facing agents, this means customers experience degraded service with no quick recovery path.
- **Recommendation**: When migrating to ECS (per customer preference), configure blue/green deployments via AWS CodeDeploy. Implement feature flags for agent capabilities (LaunchDarkly or a simple DynamoDB-backed flag system). Version all prompts and tool definitions in source control with the ability to roll back to any previous version.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application, so no token tracking or cost attribution exists. No Bedrock calls, no OpenAI calls, no custom metrics for token usage. No observability data retention policies.
- **Gap**: When AI agents are deployed, LLM costs can be significant and unpredictable. Without per-request token tracking with user/feature/workflow attribution, it is impossible to: identify cost-inefficient agent behaviors, set budgets per agent use case, detect runaway agents generating excessive tokens, or forecast costs.
- **Recommendation**: Implement token usage tracking from day one of agent deployment: (1) Log Bedrock response `usage` objects (input_tokens, output_tokens) for every LLM call, (2) Attribute costs to: user_id, agent_type (support vs. order management), workflow_step, (3) Publish CloudWatch custom metrics for token usage, (4) Set CloudWatch alarms for token budget thresholds, (5) Define retention policies for observability data (30-day hot, 90-day warm, 1-year cold).

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics found. No business outcome tracking. The application does not publish metrics for: order conversion rates, return rates, customer satisfaction scores, fulfillment cycle times, or resolution rates. The `order_status_history` table provides raw data for workflow timing analysis, but no metrics are derived from it.
- **Gap**: Agent effectiveness must be measured by business outcomes, not just technical metrics. Without business metrics, there is no way to determine whether agents are actually improving customer support (faster resolution, higher satisfaction) or degrading it (more escalations, incorrect information).
- **Recommendation**: Publish CloudWatch custom metrics for: (1) Agent resolution rate (resolved without escalation), (2) Average agent response time, (3) Order fulfillment cycle time (time from order to delivery), (4) Return processing time (currently 24-48 hours — track improvement), (5) Customer satisfaction scores (post-interaction surveys). Create CloudWatch dashboards for business stakeholders.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection configured. No CloudWatch alarms of any kind in the IaC. No error rate monitoring, no latency alerting, no PagerDuty/OpsGenie integration, no composite alarms. WAF metrics exist but have no alarms attached.
- **Gap**: Agents can silently degrade — hallucinating more, slowing down, or dropping below quality thresholds — without crossing a simple threshold. An agent suddenly calling 15 tools instead of 3 may indicate a reasoning loop. Static thresholds cannot detect this behavioral anomaly. Without anomaly detection, harmful agent behavior can persist at machine speed.
- **Recommendation**: Enable CloudWatch anomaly detection on: (1) API error rates (5xx, 4xx), (2) API latency (p50, p95, p99), (3) Agent tool invocation counts (detect reasoning loops), (4) Token usage per request (detect verbose agent behavior), (5) Database connection count (detect connection leaks). Integrate with SNS/PagerDuty for alerting.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Deployment is manual via `deploy.sh`, which runs `docker-compose build` and `docker-compose up -d`. The CloudFormation output `DeploymentInstructions` documents a manual 6-step process involving Docker CLI commands. No blue/green, no canary, no rolling updates, no traffic shifting, no feature flags. Every deployment is direct-to-production with immediate full traffic switchover.
- **Gap**: Direct-to-production deployments are high risk for agent workloads. A bad prompt change or tool misconfiguration immediately affects all customers. Canary deployments allow testing agent changes with a small percentage of traffic before full rollout.
- **Recommendation**: When migrating to ECS (per customer preference), implement canary deployments using AWS CodeDeploy with ECS. Configure: (1) 10% traffic canary for 10 minutes, (2) automated rollback on error rate increase, (3) CloudWatch alarm integration for canary health, (4) Helm-based deployment (per customer preference) with rollback support.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found anywhere in the repository. No `tests/` directory, no PHPUnit configuration, no `phpunit.xml`, no integration test suites, no contract tests, no API test collections (no Postman/Newman), no end-to-end tests. The `docker-compose.yml` health check (`curl -f http://localhost/api/products`) is the only automated verification.
- **Gap**: Agent tool reliability depends on API reliability. Without integration tests, API changes can silently break agent tools. Without contract tests, API response format changes go undetected. The existing health check only verifies that `/api/products` returns a 200 — it doesn't validate response structure.
- **Recommendation**: Build a comprehensive test suite: (1) PHPUnit integration tests for all API endpoints, (2) API contract tests that validate response schemas against OpenAPI spec (APP-Q2), (3) Agent tool integration tests that verify agent-to-API communication, (4) End-to-end tests for critical workflows (order creation → fulfillment → delivery, return processing → approval → refund). Run all tests in CI/CD pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks found (no markdown, YAML, or JSON runbooks in the repository). No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns (no auto-restart on failure events). No links to runbooks in any configuration. The App Runner health check provides automatic instance replacement on failure, but this is basic platform-level recovery, not application-level incident response.
- **Gap**: When AI agents fail in production (hallucinating, returning incorrect information, stuck in loops), there must be automated incident response: detect the issue, mitigate it (circuit breaker, disable the agent, route to human), and notify on-call. Manual incident response is too slow for autonomous systems that can cause harm at machine speed.
- **Recommendation**: Build incident response automation: (1) Create machine-readable runbooks for common agent failures (high error rate, hallucination detection, cost spike), (2) Implement automated mitigation: circuit breaker to disable agents above error threshold, automatic fallback to human support queue, (3) SSM Automation documents for infrastructure recovery, (4) SNS/PagerDuty integration for on-call notification.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No observability governance found. No `CODEOWNERS` file, no team ownership definitions, no SLO ownership documentation, no platform team tooling, no centralized observability stack configuration. No per-service dashboards, no per-service alarms, no shared responsibility model documentation.
- **Gap**: Agentic transformation requires clear ownership of agent quality, reliability, and safety. Without observability governance, it is unclear who owns agent SLOs, who responds to agent incidents, and who is accountable for agent behavior in production. This organizational gap will prevent effective agent deployment.
- **Recommendation**: Establish observability ownership model: (1) Define platform team responsibilities (centralized observability stack, shared dashboards, alerting infrastructure), (2) Define product team responsibilities (per-service SLOs, service-level instrumentation, agent-level SLOs), (3) Create CODEOWNERS file assigning ownership of observability assets, (4) Define agent-specific SLOs (task success rate, hallucination rate, tool error rate) with named owners.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Triggered | Medium | Medium | INF-Q1: 3/4 (App Runner, not ECS/EKS) | Medium |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Not Triggered | High | — | — | — |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q1: 1/4, OPS-Q10: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to AI + Move to Modern DevOps — These pathways have no dependencies between them. AI agent development (Python service, Bedrock integration, vector DB) can proceed while CI/CD pipelines and observability are being built.

**Parallel Track 2**: Move to Containers + Move to Cloud Native — These are sequential. Container migration (App Runner → ECS) must complete before microservices decomposition begins.

**Sequential Dependencies**:
- Move to Containers must complete before Move to Cloud Native (need ECS infrastructure before service extraction)
- Move to Modern DevOps should be prioritized early — CI/CD and observability are prerequisites for safely deploying agents and extracted services

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks, SDKs, or LLM integrations found
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG pipeline for grounded agent responses
  - OPS-Q3: Score 1/4 — No automated agent evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking infrastructure
- **Current State**: Zero AI/agent capability. No LLM integration, no vector search, no embeddings, no agent frameworks. The application has structured JSON APIs that are agent-tool-ready, but no agent layer exists to invoke them.
- **Target State**: Customer-facing AI agents for support and order management powered by Amazon Bedrock, with RAG-grounded responses, automated evaluation, and cost tracking.
- **Key Activities**:
  1. Deploy a Python-based agent service using Strands Agents SDK on ECS
  2. Create MCP tool definitions for existing PHP JSON APIs
  3. Deploy Amazon OpenSearch Service for vector similarity search
  4. Implement RAG pipeline using Bedrock Knowledge Bases
  5. Build automated eval pipeline with golden datasets
  6. Implement LLM token usage tracking with cost attribution
- **Dependencies**: Move to Modern DevOps (need CI/CD to deploy agent service), Move to Containers (need ECS for agent service hosting)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (quick wins — OpenAPI spec, first agent prototype), Phase 2 (foundations — vector DB, RAG, eval), Phase 3 (scale — production agents, cost optimization)
- **Relevant Learning Materials**: Module 7 — Move to AI

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline; manual deploy.sh
  - OPS-Q9: Score 1/4 — Manual direct-to-production deployments
  - OPS-Q1: Score 1/4 — No distributed tracing
  - OPS-Q10: Score 1/4 — No integration tests
  - INF-Q5: Score 3/4 — IaC exists but in CloudFormation (customer prefers Terraform)
- **Current State**: Manual deployment via shell script, no CI/CD, no testing, no observability, no rollback. CloudFormation IaC exists but is not automated.
- **Target State**: Fully automated CI/CD with GitOps, comprehensive testing (unit, integration, agent evals), distributed tracing, structured logging, canary deployments, and automated rollback.
- **Key Activities**:
  1. Implement CI/CD pipeline (GitHub Actions) with GitOps workflow
  2. Migrate IaC from CloudFormation to Terraform (per customer preference)
  3. Add OpenTelemetry distributed tracing with X-Ray
  4. Implement structured JSON logging with correlation IDs
  5. Build integration test suite for API endpoints
  6. Configure canary deployments with automated rollback on ECS
- **Dependencies**: None — this pathway enables all other pathways
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (CI/CD pipeline, structured logging), Phase 2 (tracing, testing, canary), Phase 3 (advanced observability, SLOs)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Tightly coupled monolith in single index.php file (contextual guard passes: APP-Q4 < 3)
  - APP-Q3: Score 1/4 — 100% synchronous communication
  - APP-Q10: Score 1/4 — No async for long-running operations
- **Current State**: Single monolithic PHP application with all business domains (orders, inventory, payments, returns, shipping, users) in one file sharing one database. No async messaging, no event-driven patterns.
- **Target State**: Modular services with clear domain boundaries, async communication via EventBridge/SQS, and independent scaling per domain.
- **Key Activities**:
  1. Conduct domain modeling to identify bounded contexts (Orders, Inventory, Payments, Returns, Shipping)
  2. Extract first service (Returns domain — high agent value, relatively low coupling)
  3. Implement EventBridge (per customer preference) for cross-domain events
  4. Add SQS (per customer preference) for async task processing
  5. Implement API Gateway (per customer preference) for unified routing
- **Dependencies**: Move to Containers (need ECS infrastructure first)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (domain modeling, first extraction), Phase 3 (continued extraction, event-driven architecture)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

### Move to Containers

- **Priority**: Medium
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q1: Score 3/4 — App Runner is managed compute but not ECS/EKS (contextual guard: compute is not yet ECS/EKS, though a Dockerfile exists)
- **Current State**: Application containerized with Dockerfile (PHP 8.2-apache). Running on App Runner in production and Docker Compose locally. Customer preference explicitly specifies ECS/container orchestration.
- **Target State**: Application running on Amazon ECS with Fargate, managed via Helm charts, with ECR for image registry, ALB for routing, and ECS service discovery for future microservices.
- **Key Activities**:
  1. Define ECS task definitions in Terraform
  2. Configure ALB (per customer preference) for traffic routing
  3. Set up ECR (per customer preference) image registry (already in IaC)
  4. Implement Helm charts (per customer preference) for deployment
  5. Configure ECS Service Auto Scaling
- **Dependencies**: None — Dockerfile already exists
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (ECS migration from App Runner)
- **Relevant Learning Materials**: Module 3 — Move to Containers

---

## Microservices Decomposition Strategy

This monolith would benefit from service extraction to create clear agent tool boundaries. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface — the 20+ JSON endpoints cover orders, inventory, payments, returns, warehouses, and shipping. The well-structured JSON responses (APP-Q5: score 4/4) mean agents can immediately use these endpoints as tools while planning incremental service extraction prioritized by agent value (Returns and Orders domains first).

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Order Lookup Agent** — Build an agent that queries customer order data via the existing `/api/orders/me` and `/api/orders/{id}/history` JSON APIs to answer customer questions like "Where is my order?" or "What did I order last week?"
   - **Leverages**: Structured JSON APIs at `/api/orders/me`, `/api/orders/{id}/history` (APP-Q5: 4/4)
   - **Effort**: Low
   - **Value**: Immediate customer self-service for the most common support query (order status), reducing manual CS workload

2. **Order Fulfillment Decision Agent** — Build an agent that uses the rich decision-context endpoints (`/api/orders/{id}/validation-data`, `/api/warehouses/assignment-options`, `/api/orders/{id}/picking-details`, `/api/carriers/shipping-options`) to recommend fulfillment decisions that humans currently make manually
   - **Leverages**: Decision-context APIs with structured risk scores, warehouse recommendations, carrier comparisons (APP-Q5: 4/4)
   - **Effort**: Medium
   - **Value**: Accelerates the 7-step manual fulfillment workflow by having an agent pre-analyze and recommend decisions for each step

3. **Product Search and Recommendation Agent** — Build a natural-language product search agent using the `/api/products` endpoint. Customers can ask "Do you have any running shoes under $100?" instead of browsing the catalog
   - **Leverages**: `/api/products` JSON API returning product names, descriptions, prices, stock levels
   - **Effort**: Low
   - **Value**: Natural language product discovery improves customer experience and conversion

4. **Return Processing Triage Agent** — Build an agent that accepts return requests via natural language, calls `POST /api/returns`, and provides immediate status updates instead of the current "24-48 hour wait for manual review"
   - **Leverages**: `POST /api/returns` endpoint, `GET /api/admin/pending-returns` for admin review
   - **Effort**: Medium
   - **Value**: Transforms the highest-friction customer experience (48-hour return wait) into instant acknowledgment with intelligent triage

5. **Database Query Agent for Support Staff** — Build an internal agent that helps support staff query order and customer data using natural language. "Show me all orders from customer John Doe" → SQL query via the existing database schema (DATA-Q7: 2/4, schema documented in code)
   - **Leverages**: Well-defined MySQL schema with 9 tables, clear column names and relationships
   - **Effort**: Medium
   - **Value**: Empowers support staff to investigate issues faster without writing SQL

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

1. **Generate OpenAPI 3.0 specification** for all 20+ existing `/api/*` endpoints in `index.php`. This is the single most impactful quick win — it enables agents to discover and invoke tools programmatically. (APP-Q2)
2. **Implement CI/CD pipeline** using GitHub Actions with GitOps workflow: lint → build Docker image → push to ECR → deploy. Remove reliance on manual `deploy.sh`. (INF-Q6, OPS-Q9)
3. **Migrate from App Runner to ECS on Fargate** using the existing `Dockerfile`. Define ECS task definitions and ALB in Terraform (per customer preference). This enables sidecar containers (ADOT for tracing, agent service co-location). (INF-Q1, Move to Containers)
4. **Deploy first agent prototype** — Create a Python-based agent service using Strands Agents SDK that calls the monolith's JSON APIs as tools. Start with the Order Lookup Agent (Quick Win #1). Deploy as a separate ECS task. (APP-Q13)
5. **Migrate secrets to AWS Secrets Manager** — Remove hardcoded credentials from `docker-compose.yml` and CloudFormation defaults. Reference secrets in ECS task definitions. (SEC-Q1)
6. **Add structured JSON logging** using Monolog with correlation IDs. Ship logs to CloudWatch Logs. (OPS-Q2)

### Phase 2 — Agent Foundations (Months 1–3)

1. **Deploy vector database** — Set up Amazon OpenSearch Service with k-NN plugin or Amazon Bedrock Knowledge Bases. Vectorize product catalog, customer interactions, and order history. (DATA-Q1, DATA-Q2)
2. **Implement RAG pipeline** — Configure Bedrock Knowledge Bases with chunking, embedding (Titan Embeddings), and retrieval. Integrate with the agent service for grounded customer support responses. (DATA-Q3)
3. **Build automated agent evaluation pipeline** — Create golden dataset of 50-100 customer support scenarios. Implement RAGAS scoring. Run evals in CI/CD before agent deployments. (OPS-Q3)
4. **Implement distributed tracing** — Deploy ADOT sidecar on ECS. Instrument PHP application and Python agent service with OpenTelemetry. Propagate trace context across service boundaries. Add `gen_ai.*` spans for LLM calls. (OPS-Q1)
5. **Deploy Amazon API Gateway** (per customer preference) with throttling, rate limiting, request validation, and API key management for agent clients. (INF-Q7, APP-Q8, SEC-Q5)
6. **Implement JWT-based authentication** via Amazon Cognito. Migrate from PHP sessions to token-based auth. Create machine-to-machine auth for agent services. (SEC-Q3, SEC-Q9, SEC-Q10)
7. **Add EventBridge and SQS** (per customer preference) for async messaging. Start with return processing as the first async workflow. (INF-Q4, APP-Q3)
8. **Implement idempotency** on critical write endpoints using DynamoDB (per customer preference) for idempotency key storage. (APP-Q7)
9. **Build integration test suite** for all API endpoints. Add API contract tests against OpenAPI spec. (OPS-Q10)
10. **Begin domain modeling** for microservices decomposition. Identify bounded contexts and plan first service extraction (Returns domain). (APP-Q4)

### Phase 3 — Agent Scale & Optimization (Months 3–6)

1. **Deploy production customer support agent** — Full-featured agent with RAG-grounded responses, multi-tool orchestration (order lookup, return processing, product search), and human-in-the-loop approval for high-risk actions. (APP-Q13, SEC-Q7)
2. **Deploy order management agent** — Agent that orchestrates the fulfillment workflow using Step Functions, making recommendations for warehouse assignment, picking, packing, QC, and shipping. (INF-Q3, APP-Q6)
3. **Implement LLM cost tracking** — Per-request token usage logging with attribution to user, agent type, and workflow step. CloudWatch dashboards for cost visibility. Budget alarms. (OPS-Q6)
4. **Extract first microservice** (Returns domain) from the monolith using Strangler Fig pattern. Deploy as independent ECS service with its own database. Route via API Gateway. (APP-Q4, Move to Cloud Native)
5. **Implement anomaly detection** — CloudWatch anomaly detection on API error rates, latency, agent tool invocation counts, and token usage. Alert on behavioral anomalies. (OPS-Q8)
6. **Define and implement SLOs** — API latency targets, agent task success rates, error budgets. CloudWatch dashboards with SLO tracking. (OPS-Q4)
7. **Build incident response automation** — Machine-readable runbooks for agent failures, automated circuit breakers, fallback to human support queue. (OPS-Q11)
8. **Implement canary deployments** for both application and agent changes. Automated rollback on SLO violation. (OPS-Q5, OPS-Q9)
9. **Continue service extraction** based on business priorities. Implement event-driven architecture with EventBridge for cross-service communication. (APP-Q3, APP-Q4)
10. **Establish observability governance** — Define ownership model for agent SLOs, create CODEOWNERS for observability assets, implement shared responsibility model. (OPS-Q12)

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, and Hexagonal Architecture
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
  - Directly relevant: your migration path from App Runner to ECS on Fargate
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Critical for establishing CI/CD, GitOps, and observability foundations
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Directly relevant: building CI/CD for ECS deployment
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Core learning path for your agentic AI enablement goal
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Essential: the foundation model service your agents will use
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Directly relevant: building the RAG pipeline for customer support agents
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Directly relevant: understanding agentic AI patterns for your use case
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on experience with the recommended agent framework
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced: observable agent architecture patterns
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Relevant: understanding vector databases for your RAG pipeline

---

## Appendix: Evidence Index

| # | File | What It Revealed |
|---|------|-----------------|
| 1 | `index.php` | Entire application source: ~2,600 lines of PHP containing all business domains (orders, inventory, payments, returns, shipping, users), 20+ API endpoints returning JSON, PHP session-based auth, inline PDO queries, `init_db()` with 9-table schema, `seed_data()` with sample data, embedded HTML/CSS/JS frontend |
| 2 | `infrastructure/monolith-apprunner.yaml` | CloudFormation template: VPC (10.0.0.0/16), 2 private subnets, RDS MySQL 8.4.8 (db.t3.micro, encrypted), App Runner service, ECR repository, WAF with IP whitelisting, auto-scaling (min 1, max 3, concurrency 100), IAM roles (CloudWatchLogsFullAccess + ECR access), DB credentials with insecure defaults |
| 3 | `Dockerfile` | PHP 8.2-apache base image, PDO MySQL extension installed, Apache mod_rewrite enabled, copies index.php and .htaccess, exposes port 80 |
| 4 | `docker-compose.yml` | Local development setup: MySQL 8.0 with hardcoded credentials (rootpassword, ecommerce_user/ecommerce_pass), PHP app on port 8080, health checks, volume mount for live code reload |
| 5 | `deploy.sh` | Manual deployment script: checks Docker, runs docker-compose build/up, waits 5 seconds, curls health check. No CI/CD, no automated testing, no production deployment safety |
| 6 | `.htaccess` | Apache rewrite rules routing all requests to index.php (front controller pattern) |
| 7 | `.gitignore` | Ignores data/, logs, OS files, IDE files. No .env in gitignore (but no .env file exists). No node_modules, no vendor/ — confirming no dependency manifest |
| 8 | `index.php` — `get_db()` function | Database connection with environment variable fallbacks to hardcoded credentials. No connection timeout, no retry logic |
| 9 | `index.php` — `init_db()` function | Schema definition: 9 tables (orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users) with InnoDB engine, foreign keys, indexes. ALTER TABLE with try/catch for schema evolution |
| 10 | `index.php` — API routes | 20+ endpoints: products, orders (CRUD + fulfillment workflow), returns (submit + admin approve), warehouses, carriers, users (CRUD). All return JSON via json_encode() |
| 11 | `index.php` — Fulfillment workflow | 7-step workflow: validate → assign warehouse → pick → pack → quality check → ship → deliver. Each step is a separate POST endpoint. Manual sequential execution via admin UI |
| 12 | `index.php` — Decision endpoints | Rich context APIs: /api/orders/{id}/validation-data (fraud scoring), /api/warehouses/assignment-options (distance/load/cost), /api/orders/{id}/picking-details (picker availability), /api/carriers/shipping-options (carrier comparison) |
| 13 | `index.php` — Authentication | PHP session-based: `$_SESSION['user']`, password_verify with bcrypt, role-based access (customer vs admin). Login form at POST /login |
| 14 | `monolith-apprunner.yaml` — VPC/Security | VPC with private subnets, DB security group (MySQL 3306 from App Runner SG only), App Runner security group, VPC connector, RDS PubliclyAccessible: false |
| 15 | `monolith-apprunner.yaml` — WAF | WAFv2 Web ACL with IP whitelisting (block-all default, allow specific IP set). CloudWatch metrics enabled. No rate limiting rules |
| 16 | `monolith-apprunner.yaml` — IAM | AppRunnerInstanceRole with CloudWatchLogsFullAccess (overly broad), AppRunnerAccessRole with ECR access policy (appropriate scope) |
| 17 | `monolith-apprunner.yaml` — RDS | MySQL 8.4.8, db.t3.micro, gp3 storage, StorageEncrypted: true (AWS-managed key), backup 7 days, auto minor version upgrade, deletion policy: snapshot |
| 18 | `monolith-apprunner.yaml` — ECR | Repository with scan-on-push enabled, AES256 encryption, lifecycle policy keeping last 10 images |
| 19 | Repository root — Missing files | No composer.json, no tests/, no .github/workflows/, no openapi.yaml, no swagger.json, no CODEOWNERS, no runbooks, no .env, no terraform files |
| 20 | `index.php` — Return processing | POST /api/returns creates return with status pending_review. Admin approval via POST /api/admin/approve-return processes refund, restores inventory, updates order. Response states "24-48 hours" manual review — prime agent automation candidate |
