# Agentic Readiness Assessment Report

**Target**: goal-agentic-readiness/monolith
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: agentic-readiness
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
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Advanced Capabilities (Months 3–6)
9. Recommended Self-Paced Learning Materials
10. Appendix: Evidence Index

---

## Executive Summary

This PHP monolith e-commerce application has foundational cloud infrastructure in place — managed compute via AWS App Runner, a managed RDS MySQL database, comprehensive CloudFormation IaC, and network security with VPC private subnets — but is significantly unprepared for agentic AI workloads. The application is a tightly-coupled single-file monolith (`index.php`) containing all business domains (orders, inventory, payments, returns, fulfillment, users) with no service boundaries, no API documentation, no CI/CD pipeline, and zero observability instrumentation. The entire operations and observability category scores 1.0/4.0 — every criterion is missing. Security posture is weak with hardcoded credentials, no centralized identity, and no PII redaction. While the JSON API response format and clean SQL schema provide a starting point, substantial modernization across all five categories is required before this application can support agent-driven workflows.

### Overall Score: 1.5 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.1 / 4.0 | 🟠 |
| Application Architecture | 1.3 / 4.0 | ❌ |
| Data Foundations | 1.7 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.5 / 4.0 | 🟠 |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

**1. Tightly-Coupled Monolith (APP-Q4: 1/4)**
All business domains — orders, inventory, payments, returns, fulfillment, users, and warehouse management — are packed into a single `index.php` file with shared MySQL database tables and cross-domain foreign keys. There are no module boundaries, no service interfaces, and no way to isolate agent tools to specific domains. **Why it matters:** Agents need clear tool boundaries to reason about which actions to take. A monolith with no service boundaries makes it impossible to define scoped, safe agent tools. **First step:** Conduct domain modeling to identify bounded contexts (Orders, Inventory, Payments, Returns, Fulfillment) and begin extracting a first service using the Strangler Fig pattern.

**2. No CI/CD Pipeline (INF-Q6: 1/4)**
Deployment is entirely manual via `deploy.sh`, which simply runs `docker-compose build` and `docker-compose up -d`. There are no GitHub Actions workflows, no buildspec.yml, no CodePipeline, and no automated testing, building, or deployment stages. **Why it matters:** Agents operating autonomously require rapid, safe deployment cycles with automated testing and rollback. Manual deployment creates a bottleneck that blocks iterative agent development. **First step:** Create a GitHub Actions workflow with build, test, and deploy stages targeting AWS App Runner via ECR push.

**3. Zero Observability (OPS-Q1: 1/4)**
No distributed tracing (no X-Ray, no OpenTelemetry), no structured logging (PHP `error_reporting` only), no SLOs, no alarms, no anomaly detection, and no business metrics. The IAM role grants `CloudWatchLogsFullAccess` but no observability tooling is actually configured. **Why it matters:** Agentic workflows span multiple steps and can fail silently. Without tracing and structured logging, you cannot debug agent tool invocations, detect degraded performance, or measure agent success rates. **First step:** Add OpenTelemetry PHP SDK for distributed tracing and implement structured JSON logging with correlation IDs.

**4. Hardcoded Secrets (SEC-Q1: 1/4)**
`docker-compose.yml` contains plaintext credentials (`MYSQL_ROOT_PASSWORD: rootpassword`, `MYSQL_PASSWORD: ecommerce_pass`). The CloudFormation template uses `NoEcho` parameters but with default values (`ChangeMe123!`). Database credentials are passed as plaintext environment variables to App Runner. No Secrets Manager integration exists. **Why it matters:** Agents interacting with databases and APIs need secure credential access. Hardcoded secrets are a critical security vulnerability that blocks production-grade agent deployments. **First step:** Migrate database credentials to AWS Secrets Manager and reference them via dynamic resolution in CloudFormation.

**5. No AI/Agent Frameworks (APP-Q13: 1/4)**
No AI or agent framework integration exists anywhere in the codebase. There are no imports for Bedrock, LangChain, Strands Agents, OpenAI, or any AI SDK. No embedding models, no vector databases, no RAG pipelines, and no eval frameworks are present. **Why it matters:** This is the fundamental capability gap — without any AI framework integration, agentic use cases cannot be built. **First step:** Identify the first agent use case (e.g., order fulfillment automation) and integrate the Strands Agents SDK or Amazon Bedrock Agent to interact with existing JSON APIs.

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: CloudFormation template (`infrastructure/monolith-apprunner.yaml`) defines an `AWS::AppRunner::Service` resource with ECR-based image deployment. App Runner is a fully managed compute service similar to Fargate — no EC2 instances are provisioned. The `Dockerfile` builds a PHP 8.2 Apache image. Local development uses `docker-compose.yml` with a separate container for the app.
- **Gap**: App Runner is managed compute, but the application runs as a single monolithic container. There is no Lambda or multi-service compute architecture. App Runner does not support advanced deployment strategies (canary/blue-green) natively.
- **Recommendation**: App Runner is sufficient for the current monolith. As services are extracted, evaluate ECS Fargate or Lambda for individual microservices to enable independent scaling and deployment strategies.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: Production database is `AWS::RDS::DBInstance` (resource `DBInstance` in `monolith-apprunner.yaml`) with MySQL engine version 8.4.8, `db.t3.micro` instance class, `StorageEncrypted: true`, 7-day backup retention, and `PubliclyAccessible: false`. Local development uses self-managed `mysql:8.0` in `docker-compose.yml`.
- **Gap**: RDS is managed, but the instance is a single-AZ `db.t3.micro` with no Multi-AZ failover configured. No read replicas. Not Aurora (which provides automated failover). The `DeletionPolicy: Snapshot` is good for data protection but doesn't address HA.
- **Recommendation**: Enable Multi-AZ deployment for the RDS instance. For agentic workloads requiring high availability, consider migrating to Aurora MySQL which provides automatic failover and read replicas.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No dedicated workflow orchestration service found. No `aws_sfn_*` resources in CloudFormation, no Temporal SDK imports, no workflow YAML definitions. The fulfillment workflow in `index.php` is implemented as manual HTTP endpoint transitions: `/api/orders/{id}/validate` → `/api/orders/{id}/assign-warehouse` → `/api/orders/{id}/pick` → `/api/orders/{id}/pack` → `/api/orders/{id}/quality-check` → `/api/orders/{id}/ship` → `/api/orders/{id}/deliver`. Each step requires a separate manual API call.
- **Gap**: The entire order fulfillment workflow is hardcoded as sequential HTTP endpoints with no orchestration. There is no saga pattern, no compensation logic, and no workflow state management beyond database status fields.
- **Recommendation**: Implement AWS Step Functions to orchestrate the fulfillment workflow. This is critical for agentic use cases — Step Functions can coordinate agent tool calls, handle retries, implement human-in-the-loop approval, and manage long-running workflows with built-in state management.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No messaging infrastructure found. No SQS, SNS, EventBridge, or MSK resources in CloudFormation. No messaging SDK imports in `index.php`. All operations are synchronous HTTP request-response cycles. Return processing comments in `index.php` note "manual review and approval" with "24-48 hours" turnaround — but this is human delay, not async processing.
- **Gap**: No event-driven architecture. All inter-domain communication is tightly coupled through shared database transactions. No pub/sub, no event bus, no message queues.
- **Recommendation**: Introduce Amazon SQS for decoupling order processing steps and Amazon EventBridge for domain event publication. This enables agent workflows to trigger asynchronous operations and receive completion callbacks.

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` is a comprehensive CloudFormation template covering: VPC (`AWS::EC2::VPC`), 2 private subnets, DB subnet group, 2 security groups, RDS instance, VPC connector, ECR repository, 2 IAM roles, App Runner service, auto-scaling configuration, WAF Web ACL, IP Set, and WAF association. Parameters are well-defined with constraints and defaults.
- **Gap**: No networking resources for public subnets, NAT gateways, or internet gateways (App Runner handles egress via VPC connector). CI/CD pipeline is not defined in IaC. No CloudWatch alarms or dashboards defined. Secrets are not managed via IaC (no Secrets Manager resources).
- **Recommendation**: Add Secrets Manager resources, CloudWatch alarms, and CI/CD pipeline definitions (CodePipeline/CodeBuild) to the CloudFormation template to reach 90%+ IaC coverage.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: The only deployment mechanism is `deploy.sh`, a 25-line bash script that runs `docker-compose build` and `docker-compose up -d` with a basic health check (`curl -f http://localhost:8080/api/products`). No `.github/workflows/` directory, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`, no CodePipeline defined in CloudFormation.
- **Gap**: Completely manual deployment with no automated testing, building, or deployment pipeline. No automated quality gates, no security scanning, no deployment approvals.
- **Recommendation**: Create a CI/CD pipeline using GitHub Actions or AWS CodePipeline with stages for: lint/static analysis, unit tests, Docker build, ECR push, and App Runner deployment. Add automated security scanning (ECR image scanning is already enabled with `ScanOnPush: true`).

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: App Runner provides a managed HTTPS endpoint (output `AppRunnerServiceUrl`). WAF Web ACL (`WebACL` resource) is associated with the App Runner service for IP whitelisting via an IP Set. WAF has `CloudWatchMetricsEnabled: true` and `SampledRequestsEnabled: true`.
- **Gap**: No API Gateway with request throttling, request validation, or API key management. WAF only implements IP whitelisting (allow specific IP, block everything else) — no rate limiting rules. No request/response transformation. No API usage plans or quotas.
- **Recommendation**: Add WAF rate-based rules for DDoS protection. For agentic use cases, consider placing Amazon API Gateway in front of App Runner to provide request validation, throttling, API keys for agent authentication, and usage plans for cost control.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No streaming infrastructure found. No Kinesis, MSK, or any streaming SDK imports. No event streaming patterns in code. All data access is request-response via direct database queries.
- **Gap**: No real-time event streaming capability. Order status changes, inventory updates, and fulfillment events are not published to any event stream.
- **Recommendation**: Introduce Amazon EventBridge or Kinesis Data Streams for real-time event streaming. This enables agents to react to events (e.g., new order placed, inventory low) rather than polling for changes.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines a VPC (`10.0.0.0/16`) with 2 private subnets (`10.0.1.0/24`, `10.0.2.0/24`). RDS security group (`DBSecurityGroup`) restricts MySQL port 3306 ingress to only the App Runner security group (`AppRunnerSecurityGroup`). RDS is `PubliclyAccessible: false`. App Runner connects to the VPC via `VPCConnector`. WAF provides IP-based access control.
- **Gap**: No NACLs defined (using VPC defaults). No explicit egress rules on security groups. No VPC Flow Logs configured. WAF only has IP whitelisting — no bot protection or SQL injection rules.
- **Recommendation**: Add VPC Flow Logs for network monitoring. Add WAF managed rule groups (AWS Core Rule Set, SQL injection protection). Define explicit NACL rules for defense in depth.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: `AWS::AppRunner::AutoScalingConfiguration` resource (`AutoScalingConfiguration`) is configured with `MinSize` (default 1), `MaxSize` (default 3), and `MaxConcurrency: 100`. Parameters allow customization of min/max values.
- **Gap**: Auto-scaling is only configured for the App Runner compute tier. RDS has no auto-scaling (fixed `db.t3.micro`). No scaling policies based on custom metrics or predictive scaling. Default max of 3 instances may be insufficient for production load.
- **Recommendation**: Consider RDS storage auto-scaling and instance right-sizing. Evaluate increasing `MaxSize` for production workloads. Add CloudWatch alarms to monitor scaling events.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: The application is written entirely in PHP 8.2 (`Dockerfile`: `FROM php:8.2-apache`). The single source file is `index.php`. No dependency manifest (`composer.json`) exists — all functionality uses PHP built-in extensions (PDO, session, json).
- **Gap**: PHP has a limited agent framework ecosystem compared to Python or TypeScript. There are no PHP equivalents to LangChain, Strands Agents, or CrewAI. PHP can consume REST APIs but lacks first-class agent SDK support.
- **Recommendation**: For agent development, introduce a Python or TypeScript service layer that interacts with the PHP application via its JSON APIs. Alternatively, build agents using Amazon Bedrock Agents which can call the existing HTTP endpoints as tools.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specification files found in the repository. No `openapi.yaml`, `swagger.json`, or API documentation files. No API documentation annotations in `index.php`. API routes are defined via string matching with `preg_match()` and `strpos()` — routes include `/api/products`, `/api/orders`, `/api/returns`, `/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, `/api/orders/{id}/picking-details`, `/api/carriers/shipping-options`, and 15+ more endpoints.
- **Gap**: Over 20 API endpoints exist with no documentation. Agents cannot discover or understand API capabilities without OpenAPI specs. No request/response schema definitions.
- **Recommendation**: Generate an OpenAPI 3.0 specification documenting all API endpoints, request parameters, response schemas, and authentication requirements. This is a prerequisite for agent tool definition — agents use OpenAPI specs to understand what tools are available and how to invoke them.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous HTTP request-response. Every API endpoint in `index.php` performs direct database queries within the request lifecycle and returns a response immediately. Order creation (`POST /api/orders`) performs inventory check, order insert, item inserts, inventory decrement, payment creation, and status update — all in a single synchronous database transaction (`$db->beginTransaction()`).
- **Gap**: 100% synchronous. No message queues, no event-driven patterns, no webhook callbacks. The return processing flow requires 24-48 hours of human review but is not implemented as an async job — it simply returns a "pending_review" status.
- **Recommendation**: Introduce async patterns starting with the fulfillment workflow. Use SQS to decouple order validation from warehouse assignment, and EventBridge to publish domain events (order.created, order.shipped, return.requested).

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: The entire application is a single `index.php` file (~2000 lines) containing all business domains: **Orders** (create, validate, fulfill), **Inventory** (product catalog, stock management), **Payments** (processing, refunds), **Returns** (request, approval), **Users** (authentication, CRUD), **Fulfillment** (warehouse assignment, picking, packing, QC, shipping), and **Warehouse** management. All domains share a single MySQL database with cross-domain foreign keys (`order_items.order_id REFERENCES orders(id)`, `payments.order_id REFERENCES orders(id)`, `returns.order_id REFERENCES orders(id)`). The `get_db()` function returns a single PDO connection used everywhere.
- **Gap**: Tightly-coupled monolith with no module boundaries, no service interfaces, pervasive shared state via direct database access, cross-domain foreign keys, and a single deployable unit. Cannot scale domains independently. Cannot assign agent tools to specific domain boundaries.
- **Recommendation**: Begin domain modeling to identify bounded contexts: Orders, Inventory, Payments, Returns, Fulfillment. Use the Strangler Fig pattern to incrementally extract services, starting with the highest-value, loosest-coupled domain (likely Inventory or Returns).

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API endpoints return structured JSON responses via `json_encode()`. The response header is explicitly set: `header('Content-Type: application/json')`. Responses use consistent patterns: success responses include typed fields (`{'success': true, 'order_id': '...', 'total_amount': 109.98}`), error responses use `{'error': 'message'}`, and list responses use named arrays (`{'products': [...]}`, `{'orders': [...]}`, `{'history': [...]}`).
- **Gap**: None — JSON response format is agent-ready. Responses are structured and predictable.
- **Recommendation**: Maintain this JSON-first approach. When adding OpenAPI specs, document the exact response schemas to enable agent type-safe parsing.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: The fulfillment workflow is hardcoded as a sequence of independent HTTP endpoints, each performing a single status transition in the database via `update_order_status()`. The workflow sequence is: confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered. There is no workflow engine, no state machine definition, and no orchestration service. Each step is manually triggered by admin users through the UI.
- **Gap**: No orchestration service or framework. Business workflow logic is scattered across 8+ separate API endpoints with no central definition. No compensation logic for failed steps. No timeout handling between steps.
- **Recommendation**: Define the fulfillment workflow in AWS Step Functions with explicit states, transitions, error handling, and timeouts. This provides the orchestration backbone that agents need to execute multi-step workflows reliably.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency mechanisms found. Order IDs are generated with `uniqid('order-')`, return IDs with `uniqid('return-')`, and payment IDs with `uniqid('pay-')` — all based on microsecond timestamps with no deduplication. The `POST /api/orders` endpoint has no idempotency key header or parameter. Duplicate POST requests will create duplicate orders.
- **Gap**: No idempotency keys, no deduplication IDs, no upsert patterns. All write endpoints are vulnerable to duplicate submissions. This is critical for agent safety — agents may retry failed API calls, creating duplicate orders or payments.
- **Recommendation**: Add idempotency key support to all write endpoints (POST /api/orders, POST /api/returns, POST /api/orders/{id}/ship). Use a database-backed idempotency store to detect and reject duplicate requests. This is a prerequisite for safe agent tool invocation.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: WAF Web ACL in CloudFormation implements IP whitelisting only — no rate-based rules. No application-level rate limiting middleware in `index.php`. No `express-rate-limit`, no throttle decorators, no request counting. The WAF `DefaultAction` is `Block` with an allow rule only for whitelisted IPs, but within that allowlist there are no rate limits.
- **Gap**: No rate limiting at any layer. An agent making rapid API calls could overwhelm the database or exhaust App Runner instance capacity. No per-client throttling, no burst limits, no usage quotas.
- **Recommendation**: Add WAF rate-based rules (e.g., 1000 requests per 5 minutes per IP). For agent access, implement API Gateway with usage plans that provide per-API-key throttling and quota management.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No resilience patterns implemented. The `get_db()` function has a `try/catch` that calls `die("Database connection failed: " . $e->getMessage())` — a hard failure with no retry. No circuit breakers, no exponential backoff, no timeout configurations. No health check beyond App Runner's built-in HTTP check. Exception handling in API endpoints returns 500 errors with raw exception messages (`$e->getMessage()`).
- **Gap**: No retry logic, no circuit breakers, no timeout configurations, no graceful degradation. A database connection failure crashes the entire application. Error messages may leak internal details.
- **Recommendation**: Implement retry with exponential backoff for database connections. Add circuit breaker pattern for external dependencies. Configure connection timeouts. Sanitize error messages in API responses.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All operations complete synchronously within the HTTP request lifecycle. The order creation flow (`POST /api/orders`) performs inventory checks, order creation, item creation, inventory updates, payment processing, and status updates — all in a single synchronous transaction. Return processing states "24-48 hours" but this is human processing time, not an async job. No background job framework, no queue workers, no async polling patterns.
- **Gap**: No async job handling. If any operation takes longer than PHP's execution timeout (typically 30-60 seconds), it will fail. No status polling endpoints for long-running operations.
- **Recommendation**: Extract long-running operations (return processing, bulk fulfillment) into SQS-backed workers. Implement a job status API pattern where clients receive a job ID and poll for completion.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning found. All endpoints use unversioned paths: `/api/products`, `/api/orders`, `/api/returns`, `/api/orders/{id}/validate`. No `/v1/` prefix, no `Accept-Version` headers, no versioning annotations.
- **Gap**: No versioning strategy. API changes will break existing clients. Agents built against current API schemas will fail if endpoints change without version management.
- **Recommendation**: Introduce URL path versioning (`/api/v1/products`) for all endpoints. Maintain backward compatibility for at least one previous version. Document deprecation policies.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith with no inter-service communication. The database host is configured via environment variable (`DB_HOST` in `index.php` via `getenv('DB_HOST') ?: 'mysql'`). No service discovery mechanism, no API catalog, no service mesh.
- **Gap**: No service discovery infrastructure. When services are extracted from the monolith, they will need a discovery mechanism to find each other. Currently, the monolith hardcodes the database host and has no concept of other services.
- **Recommendation**: As services are extracted, implement AWS Cloud Map or App Runner service URLs with environment-based configuration. Avoid hardcoding service endpoints.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework integration found anywhere in the codebase. No Bedrock SDK calls, no LangChain imports, no Strands Agents, no OpenAI SDK, no Spring AI. No `composer.json` file exists, so there are no declared dependencies at all. The application uses only PHP built-in extensions (PDO, session, json).
- **Gap**: Complete absence of AI/agent capabilities. No embedding models, no vector databases, no RAG pipelines, no agent orchestration. The application has no integration points for AI services.
- **Recommendation**: Start with Amazon Bedrock Agents, which can invoke the existing JSON API endpoints as tools without modifying the PHP application. Build an agent that uses the existing fulfillment API endpoints (`/api/orders/{id}/validation-data`, `/api/warehouses/assignment-options`, `/api/orders/{id}/picking-details`, `/api/carriers/shipping-options`) as decision-support tools.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch, pgvector, Pinecone, Weaviate, Chroma, or S3 Vectors references in any file. No Bedrock Knowledge Base configuration. The only data store is MySQL via RDS.
- **Gap**: No vector storage capability. Cannot perform semantic search, similarity matching, or RAG-based retrieval.
- **Recommendation**: Deploy Amazon OpenSearch Service with k-NN plugin or enable pgvector extension on Aurora PostgreSQL for vector storage. For a quick start, use Amazon Bedrock Knowledge Bases which provides managed vector storage and RAG.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). No managed or self-hosted vector store of any kind.
- **Gap**: No vector database to manage. This criterion cannot be satisfied until a vector database is introduced.
- **Recommendation**: When introducing a vector database, use a fully managed service (OpenSearch Service, Bedrock Knowledge Bases) rather than self-hosting.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components found. No embedding model calls, no document chunking/splitting code, no `similarity_search` or `knn_search` patterns. No Bedrock Titan, OpenAI ada, or any embedding model references.
- **Gap**: No RAG capability. The application cannot perform semantic search over product descriptions, order history, or knowledge base content.
- **Recommendation**: Implement a RAG pipeline using Bedrock Knowledge Bases. Index product catalog data, fulfillment procedures, and return policies to enable a customer support agent that can answer questions using company knowledge.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database is the only data source. All 9 tables (orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users) are in one `ecommerce` database defined in `init_db()` in `index.php`. The `get_db()` function returns a single PDO connection. No external API calls, no third-party data sources, no secondary databases.
- **Gap**: None — low data source sprawl. All data is centralized in one database.
- **Recommendation**: Maintain centralized data access as long as possible. When decomposing the monolith, ensure each microservice owns its data and exposes it via APIs rather than sharing database tables.

#### DATA-Q5: Data Access Pattern
- **Score**: 1/4 ❌
- **Finding**: All data access is via direct PDO database queries scattered throughout API route handlers in `index.php`. There are approximately 50+ inline SQL queries (SELECT, INSERT, UPDATE, DELETE) executed directly in route handler code. Examples: `$db->prepare('SELECT * FROM orders WHERE id = ?')`, `$db->prepare('INSERT INTO orders VALUES (?, ?, ...)')`. No repository pattern, no data access objects, no ORM (no Doctrine, no Eloquent).
- **Gap**: No data access abstraction. SQL queries are tightly coupled to business logic. Agent code would need to either duplicate these queries or call the HTTP endpoints.
- **Recommendation**: Extract data access into a repository/DAO layer as a first step toward decomposition. This creates clear data contracts that agents can interact with via well-defined APIs.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing, no Textract integration. No file upload endpoints. Product images reference URL paths (`/images/tshirt.jpg`, `/images/jeans.jpg`) but these are placeholder strings — no actual file storage or retrieval mechanism exists. No PDF processing, no OCR.
- **Gap**: No unstructured data handling capability. Cannot process documents, images, or other non-structured content.
- **Recommendation**: Introduce S3 for product images and document storage. Add Amazon Textract for document processing if return documentation or invoices need to be parsed by agents.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: Database schema is defined inline in the `init_db()` function in `index.php` as raw `CREATE TABLE IF NOT EXISTS` SQL statements. 9 tables are defined with columns, types, indexes, and foreign keys. Schema changes are handled via `ALTER TABLE` with try/catch for idempotency (e.g., adding `warehouse_location`, `weight_lbs`, `dimensions` columns to inventory). No migration tool (Flyway, Liquibase, Alembic), no JSON Schema files, no schema registry.
- **Gap**: Schema is only documented as inline PHP code. No versioned migrations, no schema changelog, no external schema documentation. Schema evolution is ad-hoc via ALTER TABLE statements with exception suppression.
- **Recommendation**: Extract schema into versioned migration files using a migration tool (e.g., Phinx for PHP, or Flyway). Document table schemas in a machine-readable format that agents can reference.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. The `get_db()` function provides a raw PDO connection but all queries are written inline in route handlers. There is no centralized repository layer, no query builder abstraction, no data access objects. The same database connection is used by all domains without any separation.
- **Gap**: No single point of data contract. Data access logic is duplicated and scattered across 50+ inline queries. Changing a table schema requires updating every query that references it.
- **Recommendation**: Create a data access layer with per-domain repositories (OrderRepository, InventoryRepository, etc.). This is a prerequisite for service extraction — each repository becomes the foundation for a microservice's data access.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1 and DATA-Q3). No embedding refresh triggers, no scheduled re-indexing, no CDC patterns.
- **Gap**: No embeddings to refresh. This criterion cannot be satisfied until vector storage and embeddings are introduced.
- **Recommendation**: When implementing RAG, design the embedding pipeline with incremental updates from the start. Use DynamoDB Streams or RDS event notifications to trigger re-indexing when product or order data changes.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 3/4 🟡
- **Finding**: CloudFormation (`monolith-apprunner.yaml`) explicitly pins the RDS engine version to `EngineVersion: '8.4.8'` with `Engine: mysql`. MySQL 8.4.x is a current, supported LTS version (GA released 2024, with support through 2032). `AutoMinorVersionUpgrade: true` is enabled for automatic patching. `docker-compose.yml` uses `mysql:8.0` which is also still supported.
- **Gap**: While versions are pinned and current, the production RDS instance uses `db.t3.micro` which provides minimal performance headroom. No explicit upgrade strategy documented.
- **Recommendation**: Document a database engine upgrade strategy. Monitor MySQL EOL dates and plan upgrades in advance. Consider Aurora MySQL for automatic version management.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs found. All 9 `CREATE TABLE` statements in `init_db()` use standard SQL DDL. All business logic is in the PHP application layer. Queries use standard SQL (SELECT, INSERT, UPDATE with prepared statements). No `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` statements. No T-SQL or PL/SQL constructs.
- **Gap**: None — all business logic is in the application layer, which makes database engine migration straightforward.
- **Recommendation**: Maintain this clean separation of business logic from the database layer. This is a strength that simplifies future database engine changes (e.g., migrating to Aurora PostgreSQL with pgvector for RAG support).

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: `docker-compose.yml` contains plaintext credentials: `MYSQL_ROOT_PASSWORD: rootpassword`, `MYSQL_PASSWORD: ecommerce_pass`, `DB_PASS: ecommerce_pass`. CloudFormation uses `NoEcho: true` on `DBUsername` and `DBPassword` parameters but provides insecure defaults (`Default: ecommerce_user`, `Default: ChangeMe123!`). App Runner environment variables pass DB credentials in plaintext (`Value: !Ref DBPassword`). `index.php` reads credentials from environment variables with hardcoded fallbacks (`getenv('DB_PASS') ?: 'ecommerce_pass'`). No AWS Secrets Manager, no Vault integration.
- **Gap**: Credentials are hardcoded in docker-compose.yml, defaulted in CloudFormation parameters, and passed as plaintext environment variables. No secret rotation, no encryption of credentials at rest in configuration.
- **Recommendation**: Migrate all credentials to AWS Secrets Manager. Reference secrets dynamically in CloudFormation using `{{resolve:secretsmanager:...}}`. Remove all hardcoded credentials from docker-compose.yml and index.php fallback values. Enable automatic secret rotation.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: CloudFormation defines two IAM roles. `AppRunnerInstanceRole` uses managed policy `arn:aws:iam::aws:policy/CloudWatchLogsFullAccess` — this grants `logs:*` on all resources, which is overly broad. `AppRunnerAccessRole` uses `arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess` — this is appropriately scoped for ECR image pulling. No custom IAM policies with specific action/resource pairs.
- **Gap**: `CloudWatchLogsFullAccess` grants permissions to create, delete, and modify log groups across the entire account — far more than needed. The instance role should only have permissions to write logs to specific log groups. No IAM condition keys are used.
- **Recommendation**: Replace `CloudWatchLogsFullAccess` with a custom IAM policy that grants only `logs:CreateLogGroup`, `logs:CreateLogStream`, and `logs:PutLogEvents` on the specific App Runner log group resource. Add condition keys to restrict to the service's own resources.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Authentication uses PHP sessions (`session_start()` in `index.php`). Login validates username/password against the `users` table using `password_verify()`. The session stores the user object: `$_SESSION['user'] = $user`. API endpoints check `$_SESSION['user']` for authentication. No JWT tokens, no OAuth2 flows, no token exchange, no Cognito integration.
- **Gap**: Session-based authentication does not propagate across services. When the monolith is decomposed, sessions cannot be shared between microservices. No user context is passed in API calls — only session cookies.
- **Recommendation**: Migrate to JWT-based authentication using Amazon Cognito. Issue JWTs on login and validate them in each service. This enables user identity to propagate across service boundaries, which is essential for agent-initiated requests that need user context.

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: No CloudTrail resource in CloudFormation. However, the application has a basic audit trail: the `order_status_history` table records status changes with `changed_by` field via the `update_order_status()` function. Each fulfillment step records who made the change and when. No CloudWatch log retention policies defined. No immutable log storage.
- **Gap**: Application-level audit logging exists for order status changes but is limited to the `order_status_history` table. No CloudTrail for AWS API calls. No structured audit events. No immutable log storage. No audit logging for user management operations (create, update, delete).
- **Recommendation**: Enable CloudTrail with log file validation and S3 bucket with object lock. Extend application audit logging to cover all state-changing operations (user management, return approvals, inventory changes). Emit structured audit events to CloudWatch Logs.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: WAF Web ACL (`WebACL` resource) implements IP whitelisting via IP Set but no rate-based rules. The WAF rules consist of a single `IPSetReferenceStatement` that allows specific IPs and blocks everything else. No `AWS::WAFv2::RuleGroup` with rate-based rules. No application-level rate limiting in `index.php`.
- **Gap**: No rate limiting protection. Within the allowed IP set, there are no limits on request frequency. Agents or automated clients could flood the API with unlimited requests.
- **Recommendation**: Add a WAF rate-based rule (e.g., `RateBasedStatement` with limit of 2000 requests per 5 minutes per IP). For production agent deployments, implement API Gateway with per-API-key usage plans.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Customer PII (names, emails) is stored and returned in API responses without redaction. `POST /api/orders` returns customer data in order objects. `GET /api/orders/{id}/validation-data` returns customer email, name, account age, total orders, and total spend. `GET /api/admin/users` returns all user details including emails. Error logging uses `ini_set('log_errors', '1')` but with no PII scrubbing — exception messages could contain customer data. `ini_set('display_errors', '0')` prevents browser display but not log contamination.
- **Gap**: No PII detection or redaction in any layer. Customer data flows freely through API responses and potentially into logs. No Macie integration, no log scrubbing middleware.
- **Recommendation**: Implement PII masking in API responses (e.g., mask email as `j***@example.com`). Add log scrubbing middleware to redact PII before writing to logs. Consider Amazon Macie for automated PII detection in stored data.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: The application has manual approval workflows: return requests require admin approval via `POST /api/admin/approve-return` (admin role check enforced). The fulfillment workflow requires manual admin actions at each step (validate, assign warehouse, pick, pack, QC, ship). The quality check endpoint (`POST /api/orders/{id}/quality-check`) has a pass/fail decision gate.
- **Gap**: These are manual human processes, not structured human-in-the-loop patterns. No Step Functions with `waitForTaskToken`, no approval Lambda patterns, no escalation workflows. No timeout on pending approvals. No audit trail of who approved what beyond the `changed_by` field.
- **Recommendation**: Formalize approval workflows using Step Functions with human task tokens. Implement timeout-based escalation for pending approvals. This is essential for agentic systems where agents handle routine cases but escalate high-risk decisions to humans.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: RDS instance has `StorageEncrypted: true` using AWS-managed encryption key (no explicit `KmsKeyId` specified). ECR repository uses `EncryptionConfiguration: EncryptionType: AES256` (AWS-managed). No explicit KMS key resources defined in CloudFormation.
- **Gap**: Encryption at rest is enabled but uses AWS-managed keys, not customer-managed KMS keys. No key rotation policy control. No KMS key for S3 or other future data stores.
- **Recommendation**: Create customer-managed KMS keys for RDS and ECR. Define key rotation policies. Use KMS keys for any additional data stores (S3, DynamoDB) added during modernization.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: All API endpoints are protected by session-based authentication: `if (!isset($_SESSION['user'])) { http_response_code(401); echo json_encode(['error' => 'Unauthorized']); exit; }`. Admin endpoints additionally check role: `if ($_SESSION['user']['role'] !== 'admin') { http_response_code(403); ... }`. Login uses `password_verify()` against bcrypt-hashed passwords (`PASSWORD_BCRYPT`). Password hashing is secure.
- **Gap**: Session-based auth is not suitable for API consumers or agents. No OAuth2/JWT standard. No API keys. No token expiration. Sessions are vulnerable to CSRF (no CSRF protection found). No MFA support.
- **Recommendation**: Implement OAuth2/JWT authentication using Amazon Cognito. Issue access tokens with defined scopes and expiration. Add API key support for agent clients. Implement CSRF protection for browser-based interactions.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: Custom user management with a `users` table in MySQL. Users are created via `POST /api/admin/users` with fields: id, username, password (bcrypt), name, email, role. No Cognito, no Okta, no SAML/OIDC federation, no SSO. Default users seeded in `seed_data()`: `customer/customer123` and `admin/admin123` with hardcoded bcrypt passwords.
- **Gap**: No centralized identity provider. User identities are isolated in the application database. Cannot federate with corporate identity systems. No SSO capability. Default user credentials are seeded in code.
- **Recommendation**: Migrate to Amazon Cognito User Pools as the centralized identity provider. Implement OIDC federation for corporate SSO. Remove hardcoded default user seeding from production code.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing found. No X-Ray SDK, no OpenTelemetry imports, no trace ID propagation headers (`traceparent`, `X-Amzn-Trace-Id`). No tracing configuration in CloudFormation. No Datadog, Jaeger, or Zipkin SDKs. `index.php` has no instrumentation wrappers around API handlers or database calls.
- **Gap**: Zero tracing capability. Cannot trace request flows through the application. Cannot correlate database queries to specific API calls. When agents invoke multiple API endpoints in sequence, there is no way to reconstruct the full execution path.
- **Recommendation**: Integrate OpenTelemetry PHP SDK for automatic instrumentation of HTTP requests and PDO database calls. Configure trace export to AWS X-Ray. Add trace context propagation for future multi-service architecture.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: Logging configuration in `index.php` is limited to PHP defaults: `error_reporting(E_ALL)`, `ini_set('display_errors', '0')`, `ini_set('log_errors', '1')`. No JSON log formatter, no structured logging library (Monolog, PSR-3), no correlation IDs, no request context in logs. Error output goes to PHP's default error log.
- **Gap**: No structured logging. Cannot query logs by request ID, user ID, or order ID. No correlation between logs and traces. App Runner sends PHP error log output to CloudWatch, but without structure it is unqueryable.
- **Recommendation**: Implement Monolog with JSON formatter for structured logging. Add request correlation IDs generated at the entry point. Include context fields (user_id, order_id, request_path) in every log entry. Configure CloudWatch Log Insights queries for operational visibility.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework found. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no golden dataset files. No A/B testing infrastructure. No test infrastructure of any kind (see OPS-Q10).
- **Gap**: No evaluation capability for AI/agent performance. When agents are introduced, there will be no mechanism to measure accuracy, hallucination rates, or task completion rates.
- **Recommendation**: Create evaluation datasets for the target agent use case (e.g., fulfillment decisions). Implement automated eval pipelines using RAGAS or custom scoring scripts that compare agent decisions against human expert baselines.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms in CloudFormation. App Runner has a health check (`HealthCheckConfiguration` with HTTP check on `/`, 10s interval, 5s timeout) but this is a liveness check, not an SLO. No p99/p95 latency targets, no error budget tracking, no SLO dashboards.
- **Gap**: No SLOs defined for any user journey. No way to measure service reliability against defined targets. No error budgets to manage deployment risk.
- **Recommendation**: Define SLOs for critical user journeys: order creation latency (p99 < 2s), API availability (99.9%), fulfillment workflow completion time (< 24h). Create CloudWatch alarms and dashboards to track these SLOs.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback capability. `deploy.sh` runs `docker-compose up -d` with no rollback mechanism. CloudFormation has `DeletionPolicy: Snapshot` and `UpdateReplacePolicy: Snapshot` on the RDS instance (protecting data), but no code deployment rollback. App Runner does not natively support blue/green or canary deployments. No feature flags.
- **Gap**: No automated rollback for code, configuration, or prompt changes. A bad deployment requires manual intervention to fix or redeploy. No code versioning in the deployment process (no image tagging strategy).
- **Recommendation**: Implement image tagging with git SHA in ECR. Configure deployment scripts to tag releases and enable rollback to previous image tags. Consider migrating to ECS Fargate for built-in blue/green deployment with CodeDeploy rollback triggers.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No Bedrock, OpenAI, or any AI service calls. Therefore, no token usage tracking, no cost attribution, no usage metrics.
- **Gap**: No LLM cost tracking infrastructure. When agents are introduced, there will be no mechanism to track token usage, attribute costs to features, or manage spending.
- **Recommendation**: When introducing AI services, implement per-request token counting using Bedrock response metadata. Publish custom CloudWatch metrics for token usage by user, feature, and workflow. Set up billing alerts and usage quotas.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics published. No `cloudwatch.put_metric_data` calls. No custom dashboards. Business data exists in database tables (orders, payments, returns) but is not published as operational metrics. No order completion rate, no return rate, no revenue tracking as CloudWatch metrics.
- **Gap**: No operational visibility into business outcomes. Cannot correlate infrastructure metrics with business performance. Cannot set alerts on business KPIs (e.g., spike in return rates).
- **Recommendation**: Publish key business metrics to CloudWatch: order creation rate, fulfillment completion time, return request rate, payment success rate. Create a business dashboard that combines infrastructure and business metrics.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection configured. No CloudWatch anomaly detection, no error rate alarms, no latency alarms. No PagerDuty, OpsGenie, or SNS notification integration. No composite alarms. WAF has `CloudWatchMetricsEnabled: true` for request metrics but no alarms configured on those metrics.
- **Gap**: No alerting on any operational condition. Application failures, latency spikes, or error rate increases will go undetected. No behavioral baseline monitoring.
- **Recommendation**: Configure CloudWatch anomaly detection on App Runner metrics (request count, latency, error rate). Set up SNS-based alerting for operations team. Add composite alarms for critical scenarios (high error rate + high latency).

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Deployment is direct-to-production via `deploy.sh` running `docker-compose up -d`. No blue/green deployments, no canary releases, no traffic shifting. CloudFormation does not define CodeDeploy, Argo Rollouts, or any progressive delivery mechanism. App Runner performs in-place deployments when a new image is pushed.
- **Gap**: All deployments are all-or-nothing with no gradual rollout. No traffic splitting, no automated rollback on error detection. High blast radius for any deployment failure.
- **Recommendation**: Implement a CI/CD pipeline with staged deployments. For App Runner, use image-based deployments with health check validation. For future ECS migration, implement blue/green deployments with CodeDeploy and automatic rollback triggers.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found in the repository. No test directory, no PHPUnit configuration, no test runner, no integration test suites. No Postman/Newman collections. No contract tests. The `docker-compose.yml` health check (`curl -f http://localhost/api/products`) is the only automated verification, and it only checks if the endpoint responds — not correctness.
- **Gap**: Zero test coverage. No unit tests, no integration tests, no end-to-end tests. Cannot verify application correctness after changes. No test infrastructure in CI pipeline (because there is no CI pipeline).
- **Recommendation**: Implement PHPUnit for unit and integration tests. Create API integration tests that validate critical workflows (order creation, fulfillment flow, return processing). Add tests to the CI pipeline as a deployment gate.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files in the repository. No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns. No links to runbooks in alert configurations (because no alerts exist).
- **Gap**: No incident response automation. All incident response is manual and undocumented. No machine-readable runbooks for agents to execute.
- **Recommendation**: Create structured runbooks for common incidents (database connection failure, high error rate, deployment failure). Implement SSM Automation documents for automated remediation. Add self-healing patterns like automatic App Runner instance restart on health check failure.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No team ownership definitions for observability. No SLO definitions with named owners. No platform engineering tooling. No per-service dashboards or alarms. The `CloudWatchLogsFullAccess` IAM policy suggests an intent to use CloudWatch but no structured observability is implemented.
- **Gap**: No observability ownership model. No shared responsibility between platform and product teams. No SLO-driven culture. No observability-as-a-product mindset.
- **Recommendation**: Define observability ownership in a CODEOWNERS file. Establish SLOs with named owners. Create a platform observability baseline (centralized logging, tracing, dashboards) that all services inherit.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | Medium | — | — | — |
| Move to Managed Databases | Not Triggered | Medium | — | — | — |
| Move to Managed Analytics | Not Triggered | Medium | — | — | — |
| Move to Modern DevOps | Triggered | Medium | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Medium | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps + Move to Cloud Native — CI/CD pipeline creation, IaC expansion, and monolith decomposition planning can proceed in parallel. CI/CD infrastructure must be in place before advanced deployment strategies can be implemented for extracted services.

**Parallel Track 2**: Move to AI — Agent framework integration and data foundations (vector DB, RAG) can begin in parallel with Track 1, using the existing monolith's JSON APIs as initial agent tools.

**Sequential Dependencies**: Move to Cloud Native depends on having CI/CD in place (Move to Modern DevOps Phase 1). Service extraction requires automated testing and deployment before it can proceed safely.

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Tightly-coupled monolith with all 7 business domains in a single `index.php` file, shared MySQL database with cross-domain foreign keys, no module boundaries
  - APP-Q3: Score 1/4 — 100% synchronous communication with no async patterns, no message queues, no event-driven architecture
  - APP-Q10: Score 1/4 — All operations synchronous within HTTP request lifecycle, no background job processing, no async polling patterns
- **Current State**: Single-file PHP monolith running as one App Runner container. All business domains tightly coupled with shared state. All communication synchronous.
- **Target State**: Modular architecture with clearly bounded services (Orders, Inventory, Payments, Returns, Fulfillment), async communication via SQS/EventBridge, independent scaling per domain. Agent tools scoped to specific service boundaries.
- **Key Activities**:
  1. Conduct domain modeling workshop to identify bounded contexts
  2. Extract first service using Strangler Fig pattern behind API Gateway routing
  3. Introduce EventBridge for domain event publication
  4. Implement async processing for long-running operations (return processing, bulk fulfillment)
- **Dependencies**: Move to Modern DevOps (CI/CD pipeline must exist before service extraction)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (domain modeling), Phase 2 (first service extraction), Phase 3 (continued decomposition)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline; only manual `deploy.sh` script
  - OPS-Q9: Score 1/4 — Direct-to-production deployments with no canary/blue-green strategy
  - OPS-Q10: Score 1/4 — Zero test coverage; no unit, integration, or end-to-end tests
  - OPS-Q1: Score 1/4 — No distributed tracing; no OpenTelemetry, no X-Ray
- **Current State**: Manual deployment via bash script. No automated testing. No observability. No deployment safety mechanisms.
- **Target State**: Full CI/CD pipeline with automated tests, staged deployments, distributed tracing, structured logging, and alerting. Deployment confidence that enables rapid iteration on agent features.
- **Key Activities**:
  1. Create CI/CD pipeline (GitHub Actions or CodePipeline) with build, test, and deploy stages
  2. Implement PHPUnit test framework and create integration test suites
  3. Add OpenTelemetry PHP SDK for distributed tracing
  4. Implement structured JSON logging with Monolog
  5. Configure CloudWatch alarms and SLOs
- **Dependencies**: None — this is the foundational pathway
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (CI/CD and basic testing), Phase 2 (observability and advanced deployment strategies)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in use; no Bedrock, LangChain, or any AI SDK
  - DATA-Q1: Score 1/4 — No vector database; no semantic search capability
  - DATA-Q3: Score 1/4 — No RAG implementation; no embeddings, no document chunking
  - OPS-Q3: Score 1/4 — No automated eval framework for agent performance measurement
  - OPS-Q6: Score 1/4 — No LLM cost tracking (no LLM usage at all)
- **Current State**: No AI capabilities. The application has JSON APIs and structured data that agents could leverage, but no agent framework integration, no vector storage, and no evaluation infrastructure.
- **Target State**: AI agent(s) that can automate order fulfillment decisions (validation, warehouse assignment, picking, packing, QC, shipping carrier selection) using the existing JSON APIs as tools. RAG pipeline for customer support. Automated eval framework measuring agent accuracy.
- **Key Activities**:
  1. Generate OpenAPI spec for existing API endpoints (prerequisite for agent tool definition)
  2. Build first agent using Strands Agents SDK or Amazon Bedrock Agents targeting the fulfillment workflow
  3. Deploy Bedrock Knowledge Base with product catalog and fulfillment procedures for RAG
  4. Create eval datasets from historical fulfillment decisions
  5. Implement token usage tracking and cost attribution
- **Dependencies**: APP-Q2 (OpenAPI spec) must be created first. DATA-Q1 (vector DB) needed for RAG.
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (data foundations and first agent), Phase 3 (advanced agent capabilities and eval)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure while incrementally extracting services
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract the **Inventory** service first — it has the clearest domain boundary (product catalog + stock management), the fewest cross-domain dependencies, and its API endpoints (`GET /api/products`) are read-heavy with minimal write contention. The `inventory` table has no inbound foreign keys from other tables, making data extraction straightforward.
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently, containerize modular components as-is, refactor tightly-coupled ones
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Containerize the monolith as-is on App Runner (already done), then extract loosest-coupled domains first (Inventory, Warehouses) while deferring tightly-coupled ones (Orders+Payments+Returns which share foreign keys)
- **When to Use**: Modular monolith with mixed coupling levels; want fastest path to containers

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

**Pattern Recommendations Based on Your Architecture:**

- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (hostname, path, or header-based). The monolith (APP-Q4: 1/4) has no service discovery (APP-Q12: 1/4), so API Gateway provides routing, throttling, and auth without requiring service mesh infrastructure upfront.

- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extraction. Without idempotency (APP-Q7: 1/4), service extraction risks data inconsistency; these patterns provide safety during transition.

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition. Microservices amplify failure modes — the current application has no resilience patterns (APP-Q9: 1/4), and these must be in place before increasing system distribution.

**Identified Bounded Contexts for Extraction:**

| Domain | Tables | Coupling Level | Extraction Priority | Agent Tool Potential |
|--------|--------|---------------|-------------------|---------------------|
| Inventory | `inventory` | Low — no inbound FKs | 1st (easiest) | Product search, stock check |
| Warehouses | `warehouses` | Low — referenced by orders but no FK | 2nd | Warehouse assignment decisions |
| Users/Auth | `users` | Low — no FK relationships | 3rd | Auth service, user context |
| Returns | `returns`, `interactions` | Medium — FK to orders | 4th | Return approval agent |
| Fulfillment | `order_status_history` | Medium — FK to orders | 5th | Fulfillment orchestration agent |
| Orders/Payments | `orders`, `order_items`, `payments` | High — central FK hub | Last | Order management agent |

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Fulfillment Decision Agent** — Build an agent that automates the order fulfillment workflow by calling the existing decision-support APIs. The application already has rich context endpoints: `/api/orders/{id}/validation-data` (fraud scoring), `/api/warehouses/assignment-options` (warehouse comparison), `/api/orders/{id}/picking-details` (picker assignment), `/api/orders/{id}/packing-options` (box selection), `/api/carriers/shipping-options` (carrier comparison).
   - **Leverages**: Structured JSON APIs returning decision context data with recommendation scores (APP-Q5: 4/4)
   - **Effort**: Medium
   - **Value**: Automates a 6-step manual workflow that currently requires admin intervention at each stage

2. **Data Query Agent** — Build a natural language to SQL agent that queries order, inventory, and fulfillment data. The database schema is clean (9 well-defined tables in `init_db()`), uses standard SQL (DATA-Q11: 4/4), and has a single data source (DATA-Q4: 4/4).
   - **Leverages**: Clean MySQL schema with 9 well-defined tables, standard SQL, single data source
   - **Effort**: Medium
   - **Value**: Enables natural language business queries (e.g., "How many orders were returned last week?" or "Which warehouse has the most capacity?")

3. **Customer Support Agent Using Documentation** — Build a RAG-based knowledge agent using the application's domain knowledge embedded in code comments and the UI warning boxes. The `index.php` file contains detailed comments about business rules, manual processes, and workflow constraints that can be extracted and indexed.
   - **Leverages**: Business rule documentation in code comments and UI text within `index.php`
   - **Effort**: Low
   - **Value**: Provides instant answers about fulfillment procedures, return policies, and warehouse operations

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Quick Wins (Days 1–30)

1. **Create CI/CD Pipeline**: Set up GitHub Actions workflow with Docker build, ECR push, and App Runner deployment. Add PHPUnit framework and create basic smoke tests for critical API endpoints (`/api/products`, `POST /api/orders`). *[Addresses INF-Q6, OPS-Q10]*
2. **Migrate Secrets to AWS Secrets Manager**: Move database credentials from plaintext environment variables and CloudFormation defaults to Secrets Manager. Update CloudFormation to use dynamic references. Remove hardcoded credentials from `docker-compose.yml` (use `.env` file for local dev). *[Addresses SEC-Q1]*
3. **Generate OpenAPI Specification**: Document all 20+ API endpoints in an OpenAPI 3.0 spec file. This is the prerequisite for agent tool definition and enables API-first development. *[Addresses APP-Q2]*
4. **Add Structured Logging**: Integrate Monolog with JSON formatter. Add request correlation IDs. Include user_id, order_id, and request_path in log context. *[Addresses OPS-Q2]*
5. **Conduct Domain Modeling Workshop**: Map bounded contexts (Orders, Inventory, Payments, Returns, Fulfillment, Warehouses, Users). Identify first extraction candidate. Document current API contracts and data flows. *[Prepares for APP-Q4 decomposition]*

### Phase 2 — Foundation (Months 1–3)

1. **Implement Distributed Tracing**: Add OpenTelemetry PHP SDK with X-Ray exporter. Instrument all API endpoints and database calls. Enable trace context propagation. *[Addresses OPS-Q1]*
2. **Extract First Service (Inventory)**: Use Strangler Fig pattern to extract the Inventory service. Place API Gateway in front of both the monolith and the new service for routing. Implement service-to-service authentication. *[Addresses APP-Q4]*
3. **Deploy Cognito for Authentication**: Migrate from PHP session-based auth to JWT-based authentication via Amazon Cognito. Implement OAuth2 flows for both browser and API clients (agent access). *[Addresses SEC-Q3, SEC-Q9, SEC-Q10]*
4. **Introduce Event-Driven Architecture**: Deploy Amazon EventBridge for domain event publication. Start publishing order lifecycle events (order.created, order.shipped, return.requested). *[Addresses INF-Q4, APP-Q3]*
5. **Set Up Data Foundations for AI**: Deploy Bedrock Knowledge Base with product catalog and fulfillment procedure documentation. Create vector index for semantic search. *[Addresses DATA-Q1, DATA-Q2, DATA-Q3]*
6. **Define SLOs and Configure Alerting**: Define SLOs for critical user journeys. Create CloudWatch alarms and dashboards. Set up SNS-based alerting. *[Addresses OPS-Q4, OPS-Q8]*

### Phase 3 — Advanced Capabilities (Months 3–6)

1. **Build Fulfillment Agent**: Implement an AI agent using Strands Agents SDK or Amazon Bedrock Agents that automates the fulfillment workflow using existing decision-support APIs as tools. Integrate with Step Functions for workflow orchestration. *[Addresses APP-Q13, INF-Q3]*
2. **Continue Service Extraction**: Extract Warehouses, Returns, and Fulfillment services. Implement async communication via SQS between services. Add idempotency keys to all write endpoints. *[Addresses APP-Q4, APP-Q7, APP-Q10]*
3. **Implement Agent Eval Framework**: Create golden datasets from historical fulfillment decisions. Build automated eval pipeline measuring agent accuracy, latency, and cost. *[Addresses OPS-Q3]*
4. **Add LLM Cost Tracking and Observability**: Implement per-request token counting. Publish cost attribution metrics. Add `gen_ai.*` semantic conventions to OpenTelemetry spans. Set up tiered retention policies. *[Addresses OPS-Q6]*
5. **Implement Advanced Deployment Strategies**: Migrate to ECS Fargate for blue/green deployments with CodeDeploy. Implement feature flags for gradual agent feature rollout. *[Addresses OPS-Q9, OPS-Q5]*
6. **Establish Observability Governance**: Define service ownership in CODEOWNERS. Create agent-level SLOs (task success rate, tool error rate). Implement observability-as-a-product with shared dashboards. *[Addresses OPS-Q12]*

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

---

## Appendix: Evidence Index

| # | File | Key Finding |
|---|------|-------------|
| 1 | `index.php` | Single-file monolith containing all business logic, ~2000 lines, 7 business domains, 20+ API endpoints, 9 database tables defined in `init_db()`, session-based auth, direct PDO queries |
| 2 | `infrastructure/monolith-apprunner.yaml` | CloudFormation template with App Runner, RDS MySQL 8.4.8, VPC with 2 private subnets, WAF IP whitelisting, ECR, 2 IAM roles (one with overly broad CloudWatchLogsFullAccess), auto-scaling config |
| 3 | `Dockerfile` | PHP 8.2 Apache image, installs PDO MySQL extension, enables mod_rewrite, copies index.php and .htaccess |
| 4 | `docker-compose.yml` | Local dev setup with MySQL 8.0 and app container, hardcoded credentials (rootpassword, ecommerce_pass), health checks defined |
| 5 | `deploy.sh` | Manual deployment script — `docker-compose build` + `docker-compose up -d` with basic curl health check, no rollback, no CI/CD |
| 6 | `.htaccess` | Apache URL rewrite rules routing all requests to index.php |
| 7 | `.gitignore` | Standard ignore patterns for database files, logs, OS files, IDE configs |
| 8 | `index.php:get_db()` | Database connection with hardcoded fallback credentials, `die()` on connection failure — no retry, no circuit breaker |
| 9 | `index.php:init_db()` | 9 CREATE TABLE statements with standard SQL DDL, no stored procedures, no triggers, ALTER TABLE for schema migration |
| 10 | `index.php:seed_data()` | Default user credentials seeded (customer/customer123, admin/admin123) with bcrypt hashing |
| 11 | `index.php:/api/orders POST` | Order creation with synchronous transaction — inventory check, insert, payment, status update all in one transaction |
| 12 | `index.php:/api/orders/{id}/validation-data` | Fraud scoring endpoint returning customer history, risk factors, and recommendation — ready for agent consumption |
| 13 | `index.php:/api/warehouses/assignment-options` | Warehouse comparison endpoint with distance calculation, load percentage, recommendation scores — agent-ready data |
| 14 | `index.php:/api/orders/{id}/picking-details` | Picker assignment context with item locations, estimated times, picker availability — agent-ready data |
| 15 | `index.php:/api/carriers/shipping-options` | Carrier comparison with dynamic pricing, delivery estimates, value scores — agent-ready data |
| 16 | `index.php:/api/admin/approve-return` | Manual return approval workflow — admin role check, refund processing, inventory restoration in single transaction |
| 17 | `monolith-apprunner.yaml:DBInstance` | RDS MySQL with StorageEncrypted:true, BackupRetentionPeriod:7, AutoMinorVersionUpgrade:true, PubliclyAccessible:false |
| 18 | `monolith-apprunner.yaml:WebACL` | WAF with IP whitelisting only, no rate-based rules, CloudWatch metrics enabled |
| 19 | `monolith-apprunner.yaml:AppRunnerInstanceRole` | IAM role with CloudWatchLogsFullAccess managed policy (overly broad) |
| 20 | `monolith-apprunner.yaml:AutoScalingConfiguration` | App Runner auto-scaling with MinSize:1, MaxSize:3, MaxConcurrency:100 |
