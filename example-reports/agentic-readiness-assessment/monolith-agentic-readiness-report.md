# Agentic Readiness Assessment Report

**Target**: ./monolith
**Date**: 2026-03-11
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

This PHP monolith e-commerce application is in the early stages of agentic AI readiness. While it has a solid foundation of structured JSON APIs, a clean relational schema across 9 well-defined tables, and managed RDS MySQL infrastructure defined in CloudFormation, it lacks every core capability required for customer-facing AI agents: no API documentation for agent tool discovery, no AI/agent framework integration, no vector database for RAG, no async messaging for event-driven agent workflows, and no observability infrastructure for monitoring agent behavior. The strongest areas are data simplicity (single MySQL source, no stored procedures, standard SQL) and partial infrastructure-as-code coverage. The most critical gaps for building customer support and order management agents are the complete absence of API specs (agents cannot discover or invoke tools), no AI framework integration, and no workflow orchestration to coordinate multi-step agent actions like order fulfillment or returns processing.

### Overall Score: 1.5 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.0 / 4.0 | 🟠 |
| Application Architecture | 1.3 / 4.0 | ❌ |
| Data Foundations | 1.8 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.3 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

1. **APP-Q2 — No API Documentation (Score: 1/4)**: Zero OpenAPI/Swagger specs exist for the 20+ API endpoints in `index.php`. This is the single biggest blocker for agentic AI enablement — agents cannot discover, understand, or invoke your APIs without machine-readable documentation. **First step**: Generate an OpenAPI 3.0 spec from the existing route handlers in `index.php` (e.g., `/api/products`, `/api/orders`, `/api/orders/{orderId}/validation-data`, etc.).

2. **APP-Q13 — No AI/Agent Frameworks (Score: 1/4)**: No Bedrock SDK, no Strands Agents, no LangChain, no agent tooling of any kind is present. For the goal of building customer support and order management agents, this is a foundational gap. **First step**: Add Amazon Bedrock SDK integration and prototype a simple agent that can query order status via the existing `/api/orders/me` endpoint.

3. **DATA-Q1 — No Vector Database (Score: 1/4)**: No vector store exists for semantic search over product catalogs, order history, or support knowledge bases. Building a customer support agent that can answer questions about products, policies, or past orders requires RAG capabilities. **First step**: Deploy Amazon OpenSearch Service with k-NN plugin or use Amazon Bedrock Knowledge Bases backed by S3 for document ingestion.

4. **SEC-Q7 — No Human Approval Workflows (Score: 1/4)**: The monolith has manual admin review for returns (`/api/admin/approve-return`) but no formal human-in-the-loop pattern. When AI agents process refunds, cancel orders, or modify inventory, high-risk actions must be gated by human approval. **First step**: Design a Step Functions workflow with `waitForTaskToken` for return approvals, serving as the pattern for all future agent guardrails.

5. **OPS-Q3 — No Automated Agent Evaluation (Score: 1/4)**: No eval framework, no golden datasets, no LLM-as-judge scoring. Without automated evaluation, there is no way to measure agent accuracy for customer support responses or order management decisions before deployment. **First step**: Create a golden dataset of 50+ customer support scenarios with expected agent responses, then implement a scoring pipeline using Amazon Bedrock as evaluator.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 2/4 🟠
- **Finding**: CloudFormation template `infrastructure/monolith-apprunner.yaml` defines an `AWS::AppRunner::Service` resource with VPC connector, ECR image source, and auto-scaling. Locally, `docker-compose.yml` runs the PHP application in a raw container. No ECS, EKS, or Fargate definitions exist. Customer preference is for ECS-based container orchestration.
- **Gap**: App Runner is a managed compute service but lacks the fine-grained control of ECS/EKS for microservices orchestration, service mesh integration, and advanced deployment strategies needed for agentic workloads. No ECS task definitions, EKS manifests, or Fargate configurations exist.
- **Recommendation**: Migrate from App Runner to Amazon ECS on Fargate. Create ECS task definitions for the monolith first, then use ECS service discovery and ALB target groups as the foundation for future microservices decomposition. Use ECR (already defined in CloudFormation) for image storage.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::RDS::DBInstance` (`${ServiceName}-db`) with managed MySQL 8.4.8, `StorageEncrypted: true`, `BackupRetentionPeriod: 7`, automatic minor version upgrades, and private subnet placement. Locally, `docker-compose.yml` runs a self-managed `mysql:8.0` container with plaintext credentials.
- **Gap**: Production database is managed RDS (good), but it is a single-AZ `db.t3.micro` instance without Multi-AZ failover or read replicas. No Aurora for high availability. Agent workflows require high-availability backends for conversation state and tool execution.
- **Recommendation**: Upgrade to Amazon Aurora MySQL for automatic failover and read replicas. Consider Amazon DynamoDB for agent session state and conversation history (aligns with customer preference for DynamoDB).

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow engine found in the codebase or IaC. All business logic in `index.php` is implemented as procedural PHP if/else chains. The order fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) is entirely manual, driven by admin UI button clicks.
- **Gap**: No dedicated orchestration service exists. The 7-step fulfillment workflow is a prime candidate for Step Functions orchestration, especially for agent-driven automation.
- **Recommendation**: Implement AWS Step Functions to orchestrate the order fulfillment workflow. This enables agents to trigger and monitor multi-step processes with built-in error handling, retries, and human approval tasks (`waitForTaskToken`).

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, MSK, or any messaging service found in IaC or application code. All operations in `index.php` are synchronous request-response. No event-driven patterns exist.
- **Gap**: Complete absence of async messaging. Agent workflows require event-driven communication for order status updates, inventory changes, return processing notifications, and inter-service coordination.
- **Recommendation**: Introduce Amazon EventBridge as the central event bus for domain events (OrderCreated, OrderShipped, ReturnRequested). Add Amazon SQS for reliable work queues (e.g., fulfillment tasks) and Amazon SNS for fan-out notifications (aligns with customer preferences for EventBridge, SQS, SNS).

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` is a comprehensive CloudFormation template covering VPC, subnets, security groups, RDS, App Runner, ECR, WAF, IAM roles, and auto-scaling. Parameterized with `NoEcho` for sensitive values.
- **Gap**: IaC covers infrastructure but not CI/CD pipelines, monitoring alarms, or logging configuration. No separate IaC for networking or shared services. The deployment process (`deploy.sh`) is a manual shell script not defined in IaC.
- **Recommendation**: Extend IaC to include CI/CD pipeline (CodePipeline/CodeBuild), CloudWatch alarms, and structured logging configuration. Consider migrating to AWS CDK for type-safe infrastructure definitions that support the evolving microservices architecture.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No GitHub Actions workflows, no `buildspec.yml`, no Jenkinsfile, no CodePipeline definitions. The only deployment mechanism is `deploy.sh`, a 30-line bash script that runs `docker-compose build` and `docker-compose up -d` with a manual health check.
- **Gap**: Complete absence of automated CI/CD. No automated testing, building, or deployment pipeline exists. The CloudFormation output includes manual Docker build/tag/push instructions.
- **Recommendation**: Implement a CI/CD pipeline using AWS CodePipeline + CodeBuild. Define stages for: lint/test → build Docker image → push to ECR → deploy to ECS. This is a prerequisite for safe agent deployment with rollback capabilities.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: CloudFormation defines `AWS::WAFv2::WebACL` associated with the App Runner service for IP whitelisting. The WebACL blocks all traffic except from `AllowedIPAddress` parameter. No API Gateway, ALB, or CloudFront is configured.
- **Gap**: No API Gateway with throttling, request validation, or structured auth. WAF provides IP filtering only, not rate limiting or request transformation. Agents need an API Gateway for tool invocation with proper throttling and authentication.
- **Recommendation**: Deploy Amazon API Gateway (REST or HTTP API) in front of the application (aligns with customer preference for API Gateway). Configure throttling, request/response validation, API keys for agent access, and usage plans for rate limiting per agent client.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming service found in IaC or application code. No event stream patterns in the codebase.
- **Gap**: No real-time streaming capability. Agent workflows that need real-time order tracking, inventory updates, or customer interaction events have no streaming infrastructure.
- **Recommendation**: Evaluate Amazon EventBridge Pipes or Amazon Kinesis Data Streams for real-time order status and inventory change events. Start with EventBridge events before adding dedicated streaming if volume warrants it.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `VPC` (10.0.0.0/16) with two private subnets (`PrivateSubnet1`, `PrivateSubnet2`). `DBSecurityGroup` allows MySQL 3306 only from `AppRunnerSecurityGroup` (least-privilege). RDS is `PubliclyAccessible: false`. App Runner uses `VPCConnector` for private VPC egress.
- **Gap**: No public subnet tier defined (only private subnets). No NAT Gateway for outbound internet from private subnets. No NACLs explicitly defined. Security group rules are correctly scoped but network architecture is minimal.
- **Recommendation**: Add NAT Gateway for private subnet outbound access. Define explicit NACLs for defense-in-depth. Add VPC Flow Logs for network monitoring. When migrating to ECS, ensure container tasks run in private subnets with ALB in public subnets.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::AppRunner::AutoScalingConfiguration` with `MinSize: 1`, `MaxSize: 3`, `MaxConcurrency: 100`. Auto-scaling is configured for the App Runner compute tier.
- **Gap**: Only one compute tier has auto-scaling. No database auto-scaling (RDS is fixed `db.t3.micro`). When migrating to ECS, ECS Service auto-scaling will need separate configuration. Max of 3 instances may be insufficient for agent-driven traffic spikes.
- **Recommendation**: When migrating to ECS, configure Application Auto Scaling for ECS services with target tracking on CPU/request count. Consider RDS auto-scaling or Aurora Serverless v2 for database tier scaling. Increase max capacity to handle agent-generated request volume.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: PHP 8.2 is the sole programming language, as indicated by `Dockerfile` (`FROM php:8.2-apache`) and the single `index.php` file. No Python, TypeScript, Java, or Go files exist.
- **Gap**: PHP has a limited agent framework ecosystem compared to Python (Strands Agents, LangChain, LangGraph, CrewAI) or TypeScript (Vercel AI SDK). The PHP SDK for AWS exists but lacks dedicated agent tooling.
- **Recommendation**: Introduce a Python or TypeScript agent service alongside the PHP monolith. The agent layer can call the PHP APIs as tools while the monolith is gradually decomposed. This avoids a full rewrite while enabling agent development in a language with mature AI frameworks.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specs, no `openapi.yaml`, no `swagger.json`, no API documentation files found anywhere in the repository. The 20+ API endpoints in `index.php` (e.g., `GET /api/products`, `POST /api/orders`, `GET /api/orders/{orderId}/validation-data`, `GET /api/warehouses/assignment-options`, `POST /api/orders/{orderId}/validate`, `GET /api/carriers/shipping-options`, etc.) are undocumented PHP route handlers using `preg_match` for URL routing.
- **Gap**: Complete absence of machine-readable API documentation. This is the #1 blocker for agentic AI enablement — agents cannot discover, understand, or invoke tools without OpenAPI specs describing endpoints, parameters, request/response schemas, and authentication requirements.
- **Recommendation**: Generate an OpenAPI 3.0 specification documenting all existing API endpoints. Start with the order management and customer-facing endpoints most relevant to the customer support agent use case. Use the spec to auto-generate agent tool definitions.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% of operations in `index.php` are synchronous request-response. All database queries are inline synchronous PDO calls. Order creation involves synchronous inventory check → order insert → payment insert → status update in a single transaction. No message publishing, no event emission, no async patterns.
- **Gap**: All inter-component communication is synchronous. No async patterns for long-running operations like return processing, fulfillment workflows, or notification dispatch. Agent workflows benefit from async communication for non-blocking tool execution.
- **Recommendation**: Introduce EventBridge events for domain actions (OrderCreated, ReturnRequested, InventoryUpdated). Use SQS queues for fulfillment task processing. This enables agents to trigger workflows without waiting for synchronous completion.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: Single `index.php` file (~2000+ lines) contains all business domains: orders, inventory, payments, returns, interactions, warehousing, shipping, quality control, and user management. All 9 database tables share a single MySQL database with foreign keys across domains (`order_items.order_id → orders.id`, `payments.order_id → orders.id`, `returns.order_id → orders.id`). No module boundaries, no separate packages, no service directories. The `get_db()` function is called directly in every route handler.
- **Gap**: Tightly-coupled monolith with pervasive shared state. All domains (orders, inventory, payments, returns, shipping, warehousing, QC, users, interactions) are in a single file with shared database access. Circular data dependencies exist via foreign keys. Cannot scale domains independently or assign agent tools to specific domain boundaries.
- **Recommendation**: This monolith would benefit from service extraction to create clear agent tool boundaries. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API endpoints in `index.php` return structured JSON via `json_encode()`. The header `Content-Type: application/json` is set for all `/api/` routes. Response structures are consistent with nested objects (e.g., `{"order": {...}, "warehouses": [...]}`, `{"products": [...]}`, `{"success": true, "order_id": "..."}"`). No XML, no binary, no HTML in API responses.
- **Gap**: None — API responses are fully structured JSON.
- **Recommendation**: Maintain JSON response format. When generating OpenAPI specs, document the response schemas to enable automatic agent tool response parsing.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration framework. Business logic is hardcoded procedural PHP. The order fulfillment workflow is implicit: validate → assign warehouse → pick → pack → QC → ship → deliver. Each step is a separate API endpoint (`/api/orders/{orderId}/validate`, `/api/orders/{orderId}/assign-warehouse`, etc.) called manually by admin UI. The `update_order_status()` function logs state transitions but does not enforce workflow ordering.
- **Gap**: No workflow engine to enforce state transitions, handle errors, implement retries, or coordinate multi-step processes. The fulfillment workflow has no programmatic guard rails — any step can be called in any order.
- **Recommendation**: Implement AWS Step Functions for the fulfillment workflow. Define state machine with: Validate → AssignWarehouse → Pick → Pack → QualityCheck → Ship → Deliver. Include error handling, retries, and human approval tasks. Agents can then trigger and monitor the workflow via Step Functions API.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys, no idempotency tokens, no deduplication patterns. Order IDs are generated with PHP `uniqid('order-')` which is time-based and not collision-resistant. No `Idempotency-Key` header checking. Payment processing has no deduplication — resubmitting the same order could create duplicate payments.
- **Gap**: No idempotency support on any write endpoint. Agent tool calls may retry on failure, causing duplicate orders, payments, or return requests without idempotency guarantees.
- **Recommendation**: Add idempotency key support to all write endpoints (`POST /api/orders`, `POST /api/returns`, `POST /api/orders/{orderId}/validate`). Use DynamoDB as an idempotency store to track request keys. This is critical for agent safety — agents retry failed tool calls.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: CloudFormation `WebACL` provides IP-based allow/block list only — no rate-based rules. No application-level rate limiting middleware in `index.php`. No `express-rate-limit` equivalent for PHP. No API Gateway throttling.
- **Gap**: No rate limiting at any layer. Agent traffic can overwhelm the application. Agents executing tool calls in loops could exhaust database connections or cause cascading failures.
- **Recommendation**: Deploy API Gateway with throttling (burst/rate limits) and usage plans per agent client. Add application-level rate limiting middleware. Configure WAF rate-based rules as a secondary defense.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, no retry logic, no timeout configurations in `index.php`. Database connections via `get_db()` use `new PDO()` with no connection timeout, retry, or pool management. If the database is unavailable, the application calls `die()` immediately. No graceful degradation.
- **Gap**: Zero resilience patterns. Database failure causes immediate application crash. No retry with backoff, no circuit breaker, no timeout on external calls. Agent workflows that depend on this application will experience cascading failures.
- **Recommendation**: Implement connection pooling with retry logic for database access. Add timeout configurations on all external calls. Implement health check endpoint that returns degraded status when dependencies are unhealthy. Consider PHP circuit breaker library or handle resilience at the ECS/ALB layer.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All operations in `index.php` are synchronous inline processing. The return approval workflow (`/api/admin/approve-return`) performs inventory restoration + refund + status update in a single synchronous transaction. No background job framework (no Celery, no Bull, no SQS workers). No async/polling patterns.
- **Gap**: No async processing for operations that could take significant time. The return approval transaction touches 4 tables atomically — at scale, this blocks the PHP process. Agent tool calls that trigger long-running operations will time out.
- **Recommendation**: Move long-running operations to SQS-backed worker processes. Return approval should publish an event to EventBridge, trigger a Step Functions workflow, and return immediately with a status URL. Agents can poll for completion.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL path versioning (`/v1/`, `/v2/`), no `Accept-Version` headers, no versioning annotations in `index.php`. All endpoints are unversioned (e.g., `/api/products`, `/api/orders`). No changelog or API version documentation.
- **Gap**: No versioning strategy. When agent tool definitions are built from these APIs, breaking changes to request/response schemas will silently break agent behavior with no backward compatibility guarantees.
- **Recommendation**: Introduce URL path versioning (`/api/v1/products`) before agents are integrated. Define a versioning policy that guarantees backward compatibility within a major version. API Gateway can handle version routing.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith with no service discovery. Database host is hardcoded via environment variable (`DB_HOST` defaults to `'mysql'` in `index.php`). No AWS Service Discovery, no App Mesh, no Consul. No service catalog or API registry.
- **Gap**: No service discovery mechanism. When decomposing into microservices, services will need to discover each other. Agent tool registries need a service catalog to know which services expose which tools.
- **Recommendation**: When migrating to ECS, enable AWS Cloud Map (ECS Service Discovery) for automatic service registration. Implement an API catalog (e.g., API Gateway as service registry) for agent tool discovery.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI SDK imports, no Bedrock SDK, no Strands Agents, no LangChain, no OpenAI SDK, no Anthropic SDK, no MCP SDK in the codebase. No `requirements.txt`, `package.json`, or `composer.json` with AI dependencies. No AI-related code patterns in `index.php`.
- **Gap**: Complete absence of AI/agent framework integration. No foundation for building customer support or order management agents. No tool definitions, no prompt templates, no agent orchestration.
- **Recommendation**: Add a Python-based agent service using Strands Agents SDK or Amazon Bedrock AgentCore. Define tools that wrap the existing PHP API endpoints. Start with a customer support agent that can query order status (`/api/orders/me`), check product availability (`/api/products`), and submit return requests (`/api/returns`).

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database present anywhere in the codebase or IaC. No OpenSearch with k-NN, no Aurora pgvector, no S3 Vectors, no Bedrock Knowledge Bases, no Pinecone, no Weaviate, no Chroma imports or configurations.
- **Gap**: No vector store for semantic search. A customer support agent needs semantic search over product catalogs, order histories, FAQs, and support knowledge bases to answer customer questions accurately.
- **Recommendation**: Deploy Amazon Bedrock Knowledge Bases backed by Amazon OpenSearch Service for RAG. Ingest product descriptions, FAQ documents, and support policies. This enables the customer support agent to answer natural language questions with grounded, relevant responses.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1), so management is not applicable. No self-hosted or managed vector store configurations found.
- **Gap**: No vector DB to manage. When a vector store is introduced, it must be a managed service.
- **Recommendation**: Use Amazon Bedrock Knowledge Bases (fully managed) or Amazon OpenSearch Service (managed) for vector storage. Avoid self-hosted vector databases to minimize operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No embedding model calls, no document chunking/splitting code, no similarity search patterns, no Bedrock Knowledge Base integration. No RAG pipeline of any kind.
- **Gap**: No RAG capability. Customer support agents need RAG to ground responses in actual product data, order details, and support policies rather than hallucinating answers.
- **Recommendation**: Build a RAG pipeline using Amazon Bedrock Knowledge Bases. Chunk and embed product catalog data, support FAQs, and return policies from the existing MySQL data. Use Bedrock Titan Embeddings for vector generation and Claude/Nova for response generation.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database (`ecommerce`) is the only data source. All 9 tables (orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users) are in one database accessed via a single `get_db()` connection function in `index.php`. `docker-compose.yml` defines one MySQL service; CloudFormation defines one RDS instance.
- **Gap**: None — single data source with no sprawl. However, as the application is decomposed into microservices, data source sprawl may increase.
- **Recommendation**: Maintain data simplicity. When decomposing the monolith, consider database-per-service pattern but implement a unified data access layer or API gateway to prevent agent tool sprawl.

#### DATA-Q5: Data Access Pattern
- **Score**: 1/4 ❌
- **Finding**: Direct PDO database connections in every route handler. The `get_db()` function creates a new PDO connection per request. SQL queries are written inline throughout `index.php` — e.g., `$db->prepare('SELECT * FROM orders WHERE id = ?')` is repeated in nearly every endpoint. No repository pattern, no ORM, no data access layer abstraction.
- **Gap**: No data access layer. Business logic and data access are tightly coupled in every route handler. Agents should not need to understand database schemas — they should interact via well-defined APIs with clean data contracts.
- **Recommendation**: Extract a data access layer (DAO/Repository pattern) that encapsulates all SQL queries behind method calls. When decomposing to microservices, each service exposes its data through APIs. Agent tools should only call APIs, never access databases directly.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no Textract, no document parsing libraries. No file upload endpoints in `index.php`. Product images are referenced by URL (`image_url` column in inventory table) but no actual image storage or processing exists.
- **Gap**: No unstructured data storage or parsing. Customer support scenarios may involve uploaded documents (receipts, photos of damaged items), and knowledge base content for RAG needs document storage and parsing.
- **Recommendation**: Add S3 for document storage. Implement Amazon Textract for receipt/document parsing in return workflows. Store support knowledge base documents in S3 for ingestion into Bedrock Knowledge Bases.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: Database schema is defined via `CREATE TABLE` statements in the `init_db()` function in `index.php`. Tables have explicit column names, types, foreign keys, and indexes. However, there are no formal JSON Schema files, no Avro/Protobuf definitions, no database migration tool (no Flyway, Liquibase, or Alembic), and no separate schema documentation files.
- **Gap**: Schema exists only embedded in PHP code. No versioned schema migrations, no formal documentation, no change history. Schema changes are applied via `ALTER TABLE` try/catch blocks (e.g., adding `warehouse_location`, `weight_lbs`, `dimensions` columns to inventory).
- **Recommendation**: Extract schema definitions into versioned migration files (e.g., Flyway or Liquibase). Generate ERD documentation. When building agent tools, use the schema definitions to create data contracts and response models.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. Database queries are scattered across 30+ route handlers in `index.php`. Each endpoint creates its own SQL queries inline. The same tables are queried differently in different endpoints (e.g., orders table is queried in `/api/orders`, `/api/orders/me`, `/api/admin/orders/pending-fulfillment`, `/api/orders/{orderId}/validation-data`, etc.).
- **Gap**: No single point of data contract. Query logic is duplicated and inconsistent. When agents call different endpoints, they may get different representations of the same data.
- **Recommendation**: Consolidate all data access into repository classes (OrderRepository, InventoryRepository, etc.). Define consistent data contracts (DTOs) that are returned from all endpoints. This is a prerequisite for clean microservice extraction.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist, so no freshness pipeline exists. No event-driven embedding refresh triggers, no scheduled re-indexing, no CDC patterns.
- **Gap**: No embedding infrastructure to keep fresh. When a vector store and RAG pipeline are introduced, embedding freshness will be critical — product catalog changes, new orders, and policy updates must be reflected in real-time.
- **Recommendation**: When implementing RAG, use Amazon Bedrock Knowledge Base sync with scheduled or event-driven refresh. Trigger re-indexing when inventory or product data changes via EventBridge events.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 3/4 🟡
- **Finding**: CloudFormation specifies `EngineVersion: '8.4.8'` for RDS MySQL. MySQL 8.4 is a Long-Term Support (LTS) release with extended support through April 2032. `docker-compose.yml` specifies `mysql:8.0` image. Both versions are explicitly pinned and supported.
- **Gap**: Development environment uses MySQL 8.0 while production CloudFormation targets 8.4.8 — version mismatch between environments. Neither version is at EOL, but the mismatch could cause compatibility issues.
- **Recommendation**: Align docker-compose MySQL version with production (8.4). Consider Aurora MySQL for production for enhanced availability and managed scaling. Ensure agent development and testing environments match production database engine versions.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, functions, or proprietary SQL constructs found in `index.php`. All `CREATE TABLE` statements use standard InnoDB SQL. All business logic is in the PHP application layer. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements. SQL queries are standard ANSI SQL with MySQL-compatible syntax.
- **Gap**: None — all business logic is in the application layer with no database-level logic coupling.
- **Recommendation**: Maintain this pattern. Keeping business logic out of the database makes migration to different database engines (Aurora, DynamoDB) significantly easier and enables clean microservice extraction.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded as defaults in `index.php`: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. `docker-compose.yml` contains plaintext passwords: `MYSQL_ROOT_PASSWORD: rootpassword`, `MYSQL_PASSWORD: ecommerce_pass`. CloudFormation uses `NoEcho` parameters for `DBUsername` and `DBPassword` with a default value of `ChangeMe123!`. No AWS Secrets Manager, no Vault, no SSM Parameter Store integration.
- **Gap**: Secrets are hardcoded in source code and docker-compose. CloudFormation uses parameter defaults for passwords. No secret rotation. Agent service credentials and API keys will need secure management.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager. Remove hardcoded defaults from `index.php`. Use Secrets Manager dynamic references in CloudFormation. Enable automatic secret rotation for RDS credentials.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: CloudFormation defines two IAM roles: `AppRunnerInstanceRole` (for the running application) and `AppRunnerAccessRole` (for ECR image pull). `AppRunnerAccessRole` uses the scoped policy `AWSAppRunnerServicePolicyForECRAccess`. However, `AppRunnerInstanceRole` uses `arn:aws:iam::aws:policy/CloudWatchLogsFullAccess` which grants wildcard access to all CloudWatch Logs operations across all resources.
- **Gap**: `CloudWatchLogsFullAccess` is overly permissive — it includes `logs:*` on `Resource: *`. Per-service roles exist (good) but need tighter policies. No IAM policies for database access, Bedrock access, or agent service roles.
- **Recommendation**: Replace `CloudWatchLogsFullAccess` with a custom policy scoped to specific log groups. When adding agent services, create dedicated IAM roles with least-privilege policies for Bedrock, DynamoDB, and S3 access.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Authentication in `index.php` uses PHP sessions (`session_start()`, `$_SESSION['user']`). Login validates against the `users` table with `password_verify()`. API endpoints check `isset($_SESSION['user'])` for auth. No JWT, no OAuth2, no token exchange, no Cognito. Session cookies are not configured with secure flags.
- **Gap**: Session-based auth does not propagate identity across services. When agents call APIs on behalf of users, they need JWT/OAuth2 tokens that carry user identity and permissions. PHP sessions cannot be shared across microservices.
- **Recommendation**: Implement Amazon Cognito for centralized identity with JWT token issuance. Replace session-based auth with JWT bearer tokens. Agent services can obtain tokens via OAuth2 client credentials flow with user context propagation.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in IaC. No audit log storage (no S3 bucket with object lock). WAF has `CloudWatchMetricsEnabled: true` and `SampledRequestsEnabled: true` but no log delivery. The `order_status_history` table in `index.php` tracks order state changes with `changed_by` field — this is application-level audit logging but not infrastructure-level.
- **Gap**: No CloudTrail for API-level audit. No immutable log storage. When agents perform actions (approving returns, modifying orders), there must be an immutable audit trail of what the agent did and why.
- **Recommendation**: Enable CloudTrail with log file validation and S3 bucket with object lock for immutable storage. Add CloudWatch Logs for application audit events. Implement agent action logging that captures: which agent, what action, on behalf of which user, with what reasoning.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: WAF `WebACL` blocks all traffic except from the allowed IP address — this is IP whitelisting, not rate limiting. No `AWS::WAFv2::RateBasedStatement` rules. No application-level rate limiting in `index.php`. No API Gateway throttle settings.
- **Gap**: No rate limiting at any layer. Agent traffic is typically bursty (multiple tool calls per agent turn). Without rate limits, a malfunctioning agent could overwhelm the application.
- **Recommendation**: Add WAF rate-based rules (e.g., 1000 requests/5 minutes per IP). Deploy API Gateway with per-client usage plans and throttling. Configure agent-specific API keys with rate limits appropriate for expected agent traffic patterns.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction in logging. Customer names, emails, and addresses are included in JSON API responses without masking (e.g., `"customer_email": "john.doe@example.com"` in order data). PHP logging uses `error_log()` with no scrubbing. No Macie configuration. Seed data in `index.php` contains example PII (`John Doe`, `john.doe@example.com`).
- **Gap**: PII is exposed in API responses and logs. Agent interactions will process PII (customer names, emails, addresses, order details). Without redaction, agent logs and traces will contain unprotected PII.
- **Recommendation**: Implement PII masking middleware for log output. Add response-level PII filtering for agent-facing APIs. Enable Amazon Macie on S3 buckets. Define PII handling policies for agent conversation logs.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: Return approval is a manual admin process via the `/api/admin/approve-return` endpoint called from the admin UI. There is no formal human-in-the-loop (HITL) pattern — no Step Functions with `waitForTaskToken`, no approval Lambda, no approval queue. The admin UI button directly calls the approve endpoint.
- **Gap**: No formal approval workflow infrastructure. When AI agents process returns, refunds, or high-value order modifications, there must be a programmatic HITL gate. The current manual admin click is not an agent-compatible approval pattern.
- **Recommendation**: Implement Step Functions with `waitForTaskToken` for high-risk agent actions: return approvals over a threshold, refunds, order cancellations, and bulk inventory changes. Create an approval UI that completes the Step Functions task token. This is critical for safe agentic AI deployment.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: RDS instance has `StorageEncrypted: true` using AWS-managed encryption key (no explicit `KmsKeyId` specified). ECR repository uses `EncryptionType: AES256` (AWS-managed). No customer-managed KMS keys defined in CloudFormation.
- **Gap**: Encryption uses AWS-managed keys, not customer-managed KMS keys. No encryption configuration for CloudWatch Logs or future S3 buckets. Agent conversation data (which may contain sensitive customer information) needs customer-managed encryption.
- **Recommendation**: Create customer-managed KMS keys for RDS, ECR, CloudWatch Logs, S3, and DynamoDB. Apply KMS encryption to all data stores that will handle agent conversation data and customer PII.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: API endpoints in `index.php` check `isset($_SESSION['user'])` for authentication, returning 401 if not authenticated. Admin endpoints check `$_SESSION['user']['role'] !== 'admin'` for authorization, returning 403 if not admin. Login uses `password_verify()` with bcrypt hashes. However, this is PHP session-based — not OAuth2/JWT.
- **Gap**: Session-based auth is not suitable for agent API access. Agents need token-based authentication (JWT/OAuth2) with scoped permissions. Current auth provides no granular permissions beyond "customer" and "admin" roles.
- **Recommendation**: Implement Amazon Cognito with OAuth2/JWT for API authentication. Define scoped permissions for agent access (e.g., `orders:read`, `returns:write`, `inventory:read`). Use API Gateway authorizers for token validation.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: Custom `users` table in MySQL with bcrypt password hashes. No Amazon Cognito, no Okta, no OIDC/SAML configuration, no SSO. User management is built into the monolith with CRUD endpoints (`/api/admin/users`).
- **Gap**: No centralized identity provider. Each microservice will need its own auth logic without a centralized IdP. Agent services need a trusted identity source for user context and permissions.
- **Recommendation**: Deploy Amazon Cognito User Pool as the centralized identity provider. Migrate existing users from MySQL to Cognito. Enable SSO for admin users. Use Cognito groups for role-based access control (customer, admin, agent).

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray SDK, no OpenTelemetry imports, no trace context propagation in `index.php`. No `traceparent` or `X-Amzn-Trace-Id` header handling. No tracing SDK in any dependency manifest (no `composer.json` exists). No Datadog, Jaeger, or Zipkin instrumentation.
- **Gap**: Zero distributed tracing capability. Agent workflows span multiple components (LLM → agent → API → database). Without tracing, it is impossible to debug agent failures, understand tool call latency, or track the complete execution path of an agent interaction.
- **Recommendation**: Implement AWS X-Ray or OpenTelemetry for distributed tracing. Instrument the PHP application with X-Ray SDK. When adding the agent service (Python), use OpenTelemetry with `gen_ai.*` semantic conventions for LLM spans. Propagate trace IDs across all service boundaries.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: Logging in `index.php` uses `ini_set('log_errors', '1')` and `ini_set('display_errors', '0')`. Error handling uses `die("Database connection failed: " . $e->getMessage())`. No JSON log formatter, no structured logging library, no correlation IDs, no request IDs.
- **Gap**: No structured logging. Agent interactions need JSON logs with correlation IDs to trace a complete conversation: user request → agent reasoning → tool call → API response → agent response. Unstructured `error_log()` output cannot be searched or correlated.
- **Recommendation**: Implement structured JSON logging with a PHP logging library (Monolog with JSON formatter). Add correlation ID middleware that generates and propagates request IDs. Ship logs to CloudWatch Logs with Insights queries for agent interaction analysis.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no golden datasets, no LLM-as-judge patterns, no scoring scripts. No test files of any kind exist in the repository. No agent evaluation infrastructure.
- **Gap**: No automated evaluation capability. Before deploying customer support and order management agents, there must be a way to measure: response accuracy, tool selection correctness, hallucination rate, and task completion rate.
- **Recommendation**: Create a golden dataset of 50+ customer support scenarios (order status queries, return requests, product questions). Implement an eval pipeline using Amazon Bedrock as evaluator (LLM-as-judge). Score agent responses on accuracy, helpfulness, and safety. Run evals in CI pipeline before deploying agent updates.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions in any configuration file. App Runner health check is configured (HTTP path `/`, interval 10s, timeout 5s) but no p99/p95 latency targets, no availability targets, no error budget tracking. No CloudWatch alarms on application metrics.
- **Gap**: No SLOs defined. Agent-powered customer support needs SLOs for: response time (how fast the agent responds), task success rate, and availability. Without SLOs, there is no measurable quality bar.
- **Recommendation**: Define SLOs for critical customer journeys: API p99 latency < 500ms, availability > 99.9%, agent response time < 5 seconds, agent task success rate > 95%. Create CloudWatch dashboards and alarms for SLO tracking.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: `deploy.sh` runs `docker-compose up -d` with no rollback mechanism. No blue/green deployment, no canary deployment, no feature flags. CloudFormation supports rollback on stack update failure, but the application deployment itself has no staged rollout. No prompt versioning or configuration rollback.
- **Gap**: No rollback capability for code, configuration, or prompts. A bad agent deployment (wrong prompt, broken tool definition) cannot be quickly reverted. Direct-to-production deployment with no safety net.
- **Recommendation**: Implement blue/green deployment on ECS with CodeDeploy. Add feature flags for agent rollout (enable agent for 10% of traffic, then expand). Version all prompts and agent configurations in source control with rollback capability.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application, so no token tracking or cost attribution exists. No CloudWatch custom metrics for AI-related costs. No usage tracking infrastructure.
- **Gap**: When agents are introduced, LLM token usage must be tracked per request with user/feature attribution. Customer support agents can generate significant token costs, especially with RAG (embedding generation + retrieval + response generation).
- **Recommendation**: Implement token usage tracking from LLM responses (Bedrock provides usage metadata in API responses). Publish custom CloudWatch metrics for tokens per request, cost per conversation, and cost per user. Define observability data retention policies for agent telemetry.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics. No business outcome tracking. The `order_status_history` table captures order state transitions, but no metrics are published for order volume, fulfillment time, return rate, or customer satisfaction.
- **Gap**: No business metrics. Agent effectiveness must be measured by business outcomes: customer issue resolution rate, average handle time reduction, return processing time, and customer satisfaction scores.
- **Recommendation**: Publish custom CloudWatch metrics for: orders per hour, average fulfillment time, return approval time, and customer interaction sentiment. When agents are deployed, add metrics for: agent resolution rate, agent escalation rate, and agent-assisted vs manual resolution comparison.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection, no error rate alarms, no latency alarms. No PagerDuty/OpsGenie integration. No composite alarms. WAF metrics are enabled but no alarms are configured on them.
- **Gap**: No anomaly detection. Agents can silently degrade — responding slower, making more tool errors, or increasing hallucination rate. Without anomaly detection, these issues go unnoticed until customers complain.
- **Recommendation**: Enable CloudWatch anomaly detection on API error rates and response latency. Create composite alarms for critical paths (order creation, return processing). When agents are deployed, add anomaly detection on: tool call error rate, agent response time, and token usage per conversation.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: `deploy.sh` executes `docker-compose up -d` which is a direct-to-production deployment with no staged rollout. App Runner supports auto-deployment from ECR but no canary or blue/green configuration exists in CloudFormation. No traffic shifting, no weighted target groups.
- **Gap**: Direct-to-production deployment with no safety net. Agent updates (new prompts, tool changes, model upgrades) are high-risk — a bad deployment can cause the agent to give wrong answers to all customers simultaneously.
- **Recommendation**: Implement canary deployment on ECS using CodeDeploy with automatic rollback on error rate increase. Deploy agent updates to 10% of traffic first, validate with automated evals, then expand to 100%.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found anywhere in the repository. No PHPUnit tests, no integration tests, no API tests (Postman/Newman), no contract tests. No test directory, no `phpunit.xml`, no `tests/` folder.
- **Gap**: Zero test coverage. When agents are added, integration tests must verify: agent tool calls reach the correct endpoints, tool responses are correctly parsed, and end-to-end agent workflows complete successfully.
- **Recommendation**: Add PHPUnit tests for existing API endpoints. Create integration tests that verify the complete order workflow (create → validate → assign → pick → pack → QC → ship). Add agent-specific integration tests that verify tool call → API → response chain.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON). No SSM Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. No self-healing patterns (no auto-restart on failure, no auto-scaling on error events). App Runner health check restarts unhealthy instances, but this is basic platform behavior, not incident automation.
- **Gap**: No incident response automation. When an agent malfunctions (wrong recommendations, excessive token usage, data inconsistency), there are no automated remediation workflows to disable the agent, fallback to manual processing, or notify the operations team.
- **Recommendation**: Create machine-readable runbooks for common failure scenarios: agent down, database connection failure, high error rate. Implement SSM Automation documents for remediation actions. Add a circuit breaker that automatically disables the agent and falls back to manual processing when error rate exceeds threshold.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No team ownership files. No SLO definition files or dashboards with named owners. No platform team tooling or centralized observability stack configuration. No per-service dashboards or alarms.
- **Gap**: No observability ownership model. When agents are deployed, someone must own: agent quality SLOs (task success rate, hallucination rate), agent safety monitoring (PII exposure, unauthorized actions), and agent cost governance (token budget per agent).
- **Recommendation**: Define an observability ownership model: platform team owns infrastructure metrics, product team owns agent quality SLOs, security team owns agent safety monitoring. Create CODEOWNERS file and assign observability asset ownership.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 1/4, INF-Q1: 2/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Triggered | Medium | High | INF-Q1: 2/4, APP-Q4: 1/4 | Medium |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Triggered | High | Medium | DATA-Q10: 3/4 (dev/prod version mismatch) | Low |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1 — Foundations**: Move to Containers + Move to Modern DevOps (can execute simultaneously — containerize onto ECS while building CI/CD pipeline)

**Parallel Track 2 — Agent Enablement**: Move to AI + Move to Managed Databases (can execute simultaneously — build agent service while upgrading to Aurora and adding DynamoDB for agent state)

**Sequential Dependencies**:
- Move to Containers must complete (ECS deployment) before Move to Cloud Native (microservices decomposition requires container orchestration)
- Move to Modern DevOps should be in place before Move to AI (agents need CI/CD for safe deployment and rollback)
- Move to Managed Databases should precede or parallel Move to AI (agents need reliable database backends and vector stores)

### Move to Containers

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q1: Score 2/4 — App Runner defined in CloudFormation but customer prefers ECS for container orchestration
  - APP-Q4: Score 1/4 — Monolith needs containerization as the first step toward decomposition
- **Current State**: Application has a `Dockerfile` (PHP 8.2 Apache) and runs locally via `docker-compose.yml`. CloudFormation deploys to App Runner. ECR repository exists in IaC.
- **Target State**: Application deployed on Amazon ECS Fargate with ALB, service discovery, and auto-scaling. ECR used for image storage. Container-based deployment enables future microservice extraction.
- **Key Activities**:
  1. Create ECS task definition from existing Dockerfile
  2. Deploy ECS Fargate service with ALB (replaces App Runner)
  3. Configure ECS Service Discovery via AWS Cloud Map
  4. Set up Application Auto Scaling for ECS service
- **Dependencies**: None — this is a foundational pathway
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Tightly-coupled monolith with all 9 domains in single `index.php`
  - INF-Q1: Score 2/4 — No ECS/EKS for microservices orchestration
  - APP-Q3: Score 1/4 — 100% synchronous communication
  - APP-Q10: Score 1/4 — No async processing for long-running operations
- **Current State**: Single PHP monolith with all domains tightly coupled, shared MySQL database, synchronous request-response only.
- **Target State**: Domain-bounded microservices (Orders, Inventory, Payments, Returns, Fulfillment) deployed on ECS with event-driven communication via EventBridge/SQS. Each service has clear API boundaries suitable for agent tool definition.
- **Key Activities**:
  1. Identify bounded contexts via domain modeling (Orders, Inventory, Payments, Returns, Fulfillment, Users)
  2. Extract first service (e.g., Inventory) using Strangler Fig pattern with API Gateway routing
  3. Introduce EventBridge for domain events and SQS for async work queues
  4. Implement database-per-service pattern for extracted services
- **Dependencies**: Move to Containers must complete first (ECS infrastructure needed for service deployment)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Agent Foundations) and Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Managed Databases

- **Priority**: Medium
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - DATA-Q10: Score 3/4 — Dev/prod MySQL version mismatch (8.0 vs 8.4.8); single-AZ RDS without Aurora failover
- **Current State**: RDS MySQL 8.4.8 in CloudFormation (managed, encrypted, private subnet). Self-managed MySQL 8.0 in docker-compose for development. Single-AZ, no Multi-AZ failover.
- **Target State**: Amazon Aurora MySQL with automatic failover and read replicas for the application database. Amazon DynamoDB for agent session state and conversation history. Amazon OpenSearch Service for vector search (RAG).
- **Key Activities**:
  1. Upgrade RDS MySQL to Aurora MySQL for automatic failover
  2. Deploy DynamoDB table for agent session state and idempotency keys
  3. Deploy OpenSearch Service for vector search (Bedrock Knowledge Base backend)
  4. Align development MySQL version with production
- **Dependencies**: None — can execute in parallel with other pathways
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 1 (version alignment) and Phase 2 (Aurora migration, DynamoDB)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD automation, only manual `deploy.sh`
  - OPS-Q9: Score 1/4 — Direct-to-production deployment, no canary/blue-green
  - OPS-Q10: Score 1/4 — No integration tests
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: Manual deployment via `deploy.sh` (docker-compose). No CI/CD pipeline, no tests, no tracing, no structured logging.
- **Target State**: Full CI/CD pipeline with CodePipeline/CodeBuild → build → test → push to ECR → deploy to ECS with canary/blue-green. Distributed tracing with X-Ray/OpenTelemetry. Structured JSON logging. Integration tests in pipeline.
- **Key Activities**:
  1. Create CodePipeline + CodeBuild pipeline for automated build and deploy
  2. Add PHPUnit tests and agent integration tests to CI pipeline
  3. Implement distributed tracing (X-Ray/OpenTelemetry)
  4. Add structured JSON logging with correlation IDs
  5. Configure canary deployment with CodeDeploy and automatic rollback
- **Dependencies**: Move to Containers should be in progress (pipeline deploys to ECS)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (CI/CD, logging) and Phase 2 (tracing, canary deployment)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No agent frameworks or AI SDK integration
  - DATA-Q1: Score 1/4 — No vector database for RAG
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated eval framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: Zero AI/agent capability. No Bedrock SDK, no vector store, no RAG pipeline, no eval framework.
- **Target State**: Customer support agent powered by Amazon Bedrock with RAG over product catalog and support knowledge base. Order management agent with tool access to fulfillment APIs. Automated eval pipeline. LLM cost tracking and attribution.
- **Key Activities**:
  1. Generate OpenAPI spec from existing PHP API endpoints
  2. Build Python agent service using Strands Agents SDK with Bedrock
  3. Deploy Bedrock Knowledge Base with product and support data for RAG
  4. Implement agent tool definitions wrapping existing API endpoints
  5. Create golden dataset and automated eval pipeline
  6. Implement LLM token tracking and cost attribution
  7. Add human-in-the-loop approval for high-risk agent actions (returns, refunds)
- **Dependencies**: Move to Managed Databases (for vector store) and Move to Modern DevOps (for safe deployment) should be in progress
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (OpenAPI spec, initial agent), Phase 2 (RAG, tools), Phase 3 (evals, scaling)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

This monolith would benefit from service extraction to create clear agent tool boundaries. The 9 business domains currently coupled in `index.php` (Orders, Inventory, Payments, Returns, Interactions, Warehousing, Shipping, Quality Control, Users) represent natural bounded contexts for microservice extraction. Each extracted service would expose a focused API surface ideal for agent tool definitions — for example, an Order Service with `getOrder`, `createOrder`, `getOrderHistory` tools, or an Inventory Service with `checkStock`, `getProduct` tools. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface at `/api/*` endpoints, which already return structured JSON responses.

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Order Lookup Agent** — Build an agent that can look up customer orders, check order status, and provide tracking information by calling `/api/orders/me` and `/api/orders/{orderId}/history`.
   - **Leverages**: Existing JSON API endpoints for order queries, structured order status history in `order_status_history` table
   - **Effort**: Low
   - **Value**: Reduces customer service volume for "where is my order?" queries — the most common support request

2. **Product Catalog Agent** — Build an agent that answers product questions (pricing, availability, descriptions) by querying `/api/products` and the inventory table.
   - **Leverages**: Structured JSON product catalog via `GET /api/products` with 5 products including name, description, price, and stock quantity
   - **Effort**: Low
   - **Value**: Enables 24/7 automated product inquiries for customers, improving response time from hours to seconds

3. **Order Management Data Query Agent** — Build a natural language to SQL agent that queries the 9-table MySQL schema for business intelligence (order trends, inventory levels, return rates, customer history).
   - **Leverages**: Clean relational schema with 9 well-defined tables (`orders`, `order_items`, `inventory`, `payments`, `returns`, `interactions`, `order_status_history`, `warehouses`, `users`) — all documented in `init_db()` function
   - **Effort**: Medium
   - **Value**: Enables operations managers to query order and inventory data using natural language instead of writing SQL

4. **Return Request Intake Agent** — Build an agent that collects return reasons, validates order eligibility, and submits return requests via `POST /api/returns` — automating the intake process that currently requires manual form submission.
   - **Leverages**: Existing `POST /api/returns` endpoint that accepts `order_id` and `reason`, structured return workflow with `pending_review` status
   - **Effort**: Low
   - **Value**: Automates return intake from 24-48 hour manual review to instant submission, reducing customer wait time for the initial acknowledgment

5. **Fulfillment Decision Support Agent** — Build an agent that recommends warehouse assignments by analyzing `/api/warehouses/assignment-options` data (distance, load, delivery time) and shipping options from `/api/carriers/shipping-options` (carrier rates, delivery dates).
   - **Leverages**: Rich decision-support APIs already exist: warehouse assignment scoring (`recommendation_score`), carrier comparison with value scoring, and order validation data with fraud scoring
   - **Effort**: Medium
   - **Value**: Reduces fulfillment decision-making time from minutes (manual admin review) to seconds (agent recommendation)

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

1. **Generate OpenAPI 3.0 specification** from existing PHP API routes in `index.php`. Document all 20+ endpoints with request/response schemas, authentication requirements, and error responses. This unblocks agent tool definition. *(Addresses APP-Q2)*
2. **Migrate from App Runner to ECS Fargate** using the existing `Dockerfile` and ECR repository. Create ECS task definition, ALB, and target group. This aligns with customer preference for ECS and enables future service decomposition. *(Addresses INF-Q1)*
3. **Create CI/CD pipeline** using CodePipeline + CodeBuild: source → build Docker image → push to ECR → deploy to ECS. Replace manual `deploy.sh`. *(Addresses INF-Q6)*
4. **Migrate secrets to AWS Secrets Manager**: remove hardcoded credentials from `index.php` and `docker-compose.yml`. Use Secrets Manager dynamic references in CloudFormation. *(Addresses SEC-Q1)*
5. **Build initial customer support agent prototype** using Python + Strands Agents SDK + Amazon Bedrock. Define tools that call existing `/api/products`, `/api/orders/me`, and `/api/returns` endpoints. Deploy as a separate ECS service. *(Addresses APP-Q13)*

### Phase 2 — Agent Foundations (Months 1–3)

1. **Deploy Amazon Cognito** for centralized identity with JWT token issuance. Replace PHP session-based auth with bearer tokens. Configure OAuth2 scopes for agent access (`orders:read`, `returns:write`). *(Addresses SEC-Q3, SEC-Q9, SEC-Q10)*
2. **Deploy API Gateway** in front of ECS services with throttling, usage plans, and API key management for agent clients. Configure request validation and response caching. *(Addresses INF-Q7, SEC-Q5, APP-Q8)*
3. **Implement Amazon Bedrock Knowledge Base** backed by OpenSearch Service for RAG. Ingest product catalog, support FAQs, and return policies. Enable the customer support agent to answer knowledge-grounded questions. *(Addresses DATA-Q1, DATA-Q2, DATA-Q3)*
4. **Add EventBridge and SQS** for async domain events (OrderCreated, ReturnRequested, InventoryUpdated). Implement SQS workers for fulfillment task processing. *(Addresses INF-Q4, APP-Q3)*
5. **Implement Step Functions** for order fulfillment workflow (validate → assign → pick → pack → QC → ship) with `waitForTaskToken` for human approval on returns and high-value order modifications. *(Addresses INF-Q3, APP-Q6, SEC-Q7)*
6. **Add distributed tracing** with OpenTelemetry across PHP app and Python agent service. Implement structured JSON logging with Monolog. Ship all logs to CloudWatch. *(Addresses OPS-Q1, OPS-Q2)*
7. **Upgrade to Aurora MySQL** for automatic failover. Deploy DynamoDB for agent session state, conversation history, and idempotency keys. *(Addresses INF-Q2, APP-Q7)*
8. **Add PHPUnit tests** for API endpoints and agent integration tests. Run tests in CI pipeline. *(Addresses OPS-Q10)*

### Phase 3 — Agent Scale & Optimization (Months 3–6)

1. **Implement automated agent evaluation pipeline**: create golden dataset of 100+ customer support and order management scenarios. Run LLM-as-judge scoring in CI before every agent deployment. *(Addresses OPS-Q3)*
2. **Implement LLM cost tracking and attribution**: capture token usage per request from Bedrock response metadata. Publish CloudWatch metrics for cost per conversation, cost per user, and cost per agent tool. *(Addresses OPS-Q6)*
3. **Begin microservice extraction** using Strangler Fig pattern: extract Inventory service first (clear boundary, minimal coupling), then Orders, then Returns. Each service gets its own ECS task, database, and OpenAPI spec. Agent tools automatically map to service boundaries. *(Addresses APP-Q4)*
4. **Implement canary deployments** with CodeDeploy for both application services and agent updates. Auto-rollback on error rate increase. *(Addresses OPS-Q5, OPS-Q9)*
5. **Deploy anomaly detection**: CloudWatch anomaly detection on API error rates, response latency, agent tool call error rate, and token usage per conversation. Composite alarms for critical customer journeys. *(Addresses OPS-Q8)*
6. **Define SLOs and ownership model**: API p99 latency < 500ms, agent response time < 5s, agent task success rate > 95%, availability > 99.9%. Assign ownership across platform and product teams. *(Addresses OPS-Q4, OPS-Q12)*
7. **Implement PII redaction** in agent conversation logs and application logs. Enable Amazon Macie on S3 buckets. Define PII handling policies for agent interactions. *(Addresses SEC-Q6)*
8. **Enable CloudTrail** with log file validation and immutable S3 storage. Implement agent action audit trail: which agent, what action, on behalf of which user, with what reasoning. *(Addresses SEC-Q4)*

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

---

## Appendix: Evidence Index

| File | Key Findings |
|------|-------------|
| `index.php` | Single PHP monolith (~2000+ lines) containing all 9 business domains. 20+ API endpoints returning JSON. Session-based auth. Direct PDO database access. No idempotency, no retry logic, no circuit breakers. `get_db()` with hardcoded credential defaults. `init_db()` with 9 CREATE TABLE statements. `seed_data()` with sample data including PII. Fulfillment workflow endpoints (validate, assign-warehouse, pick, pack, quality-check, ship, deliver). |
| `Dockerfile` | PHP 8.2 Apache base image. Installs PDO MySQL extension. Copies `index.php` and `.htaccess`. Exposes port 80. Simple, production-usable container definition. |
| `docker-compose.yml` | Two services: `mysql:8.0` (self-managed) and `monolith` (PHP app). Plaintext database credentials. MySQL health check. Application health check on `/api/products`. Volume mount for persistent MySQL data. |
| `deploy.sh` | Manual deployment script. Runs `docker-compose build` and `docker-compose up -d`. Basic health check with `curl`. No CI/CD, no rollback, no staged deployment. |
| `infrastructure/monolith-apprunner.yaml` | Comprehensive CloudFormation template. Defines: VPC (10.0.0.0/16), 2 private subnets, RDS MySQL 8.4.8 (encrypted, private, backup enabled), App Runner service with VPC connector, ECR repository, WAF WebACL (IP whitelisting), auto-scaling (min 1, max 3), 2 IAM roles (instance + access). No API Gateway, no SQS/SNS/EventBridge, no Step Functions, no Secrets Manager, no CloudTrail. |
| `.htaccess` | Apache rewrite rules routing all requests to `index.php`. Standard single-entry-point pattern for PHP applications. |
| `.gitignore` | Excludes database files, logs, OS files, and IDE configurations. No `node_modules`, `vendor`, or build artifact exclusions (confirms no dependency management). |
