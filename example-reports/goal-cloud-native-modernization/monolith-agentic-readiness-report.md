# Agentic Readiness Assessment Report
**Target**: ./monolith
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: cloud-native-modernization
**Goal Context**: Decomposing monoliths into containerized microservices on EKS with GitOps deployment
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
7. Readiness Roadmap
   - Phase 1 — Containerize & Automate (Days 1–30)
   - Phase 2 — Decompose & Decouple (Months 1–3)
   - Phase 3 — Optimize & Scale (Months 3–6)
8. Recommended Self-Paced Learning Materials
9. Appendix: Evidence Index

---

## Executive Summary

This PHP monolith e-commerce application has a solid foundation of managed AWS infrastructure — App Runner for compute, RDS MySQL for the database, VPC networking with private subnets, and CloudFormation-based IaC — but is critically unprepared for cloud-native modernization. The entire application exists as a single tightly-coupled `index.php` file (~2000+ lines) containing all business domains (orders, inventory, payments, returns, fulfillment, users), with direct database queries scattered throughout and zero service boundaries. There is no CI/CD pipeline, no testing, no observability, no API documentation, and no resilience patterns — making decomposition into containerized microservices on EKS a significant but achievable effort. The strongest areas are the existing managed infrastructure (App Runner, RDS, VPC) and the clean data layer (no stored procedures, no proprietary SQL, current MySQL version). The most critical gaps are the monolithic architecture itself, absence of CI/CD automation, lack of observability, and missing API documentation — all of which must be addressed to enable the EKS-based microservices target state.

### Overall Score: 1.4 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.9 / 4.0 | 🟡 |
| Application Architecture | 1.2 / 4.0 | 🟠 |
| Data Foundations | 1.7 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | 🟠 |
| Operations & Observability | 1.0 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

**1. APP-Q4 — Monolith Architecture (Score: 1/4)** — The entire application is a single `index.php` file with all business domains (orders, inventory, payments, returns, fulfillment, warehouse, users) tightly coupled via shared MySQL tables with cross-domain foreign keys. This is the #1 blocker for cloud-native modernization because decomposition into independently deployable services on EKS cannot begin until domain boundaries are identified and decoupled. **First step:** Conduct a domain modeling workshop to map bounded contexts and identify the first service extraction candidate.

**2. INF-Q6 — No CI/CD Pipeline (Score: 1/4)** — The only deployment mechanism is `deploy.sh`, a manual shell script that runs `docker-compose up -d` locally. There is no GitHub Actions, CodePipeline, or any automated pipeline for testing, building, or deploying. This blocks the GitOps deployment model required for EKS microservices. **First step:** Create a GitHub Actions workflow with build, test, and push-to-ECR stages using the existing `Dockerfile`.

**3. APP-Q3 — 100% Synchronous Communication (Score: 1/4)** — All inter-domain calls are synchronous within the monolith's single request cycle. The order creation flow directly calls inventory checks, payment processing, and status updates in a single transaction. Microservices decomposition requires async patterns for cross-service communication. **First step:** Introduce SQS or EventBridge for the fulfillment workflow (validate → warehouse → pick → pack → QC → ship) as the first async decoupling.

**4. OPS-Q9 — Manual Deployment Strategy (Score: 1/4)** — Deployments are manual `docker-compose` commands with no blue/green, canary, or progressive rollout capability. EKS-based microservices demand automated deployment strategies (ArgoCD + Helm for GitOps) to safely deploy independent services. **First step:** Set up ArgoCD on the target EKS cluster and define the first Helm chart for the monolith container as a starting point.

**5. OPS-Q1 — No Distributed Tracing (Score: 1/4)** — No X-Ray, OpenTelemetry, or any tracing is present. As services are extracted from the monolith, cross-service visibility becomes critical for debugging distributed failures. Without tracing, decomposition will produce an unmaintainable system. **First step:** Add OpenTelemetry auto-instrumentation to the PHP monolith container before decomposition begins, establishing a tracing baseline.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: The production compute is AWS App Runner (`AWS::AppRunner::Service` in `infrastructure/monolith-apprunner.yaml`), a fully managed container service that auto-provisions, scales, and load-balances containers — functionally equivalent to ECS Fargate. The `Dockerfile` defines a PHP 8.2 Apache container image. Local development uses `docker-compose.yml` with a self-built container.
- **Gap**: App Runner is managed but not EKS, which is the preferred container orchestration platform per customer preferences. App Runner lacks Kubernetes-native features (Helm, Ingress, service mesh, GitOps with ArgoCD) that are required for the microservices target state.
- **Recommendation**: Migrate from App Runner to Amazon EKS with Fargate node groups. Create Helm charts for the monolith container first, then for each extracted microservice. Use the existing `Dockerfile` as the starting point for EKS deployment.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: Production uses `AWS::RDS::DBInstance` (MySQL 8.4.8, `db.t3.micro`) in `infrastructure/monolith-apprunner.yaml` — a fully managed database with automated backups (7-day retention), encryption at rest, and private subnet placement. `docker-compose.yml` runs self-managed `mysql:8.0` for local development.
- **Gap**: Using single-instance RDS, not Aurora. No Multi-AZ failover configured. The `db.t3.micro` instance class is undersized for production workloads. No read replicas for scaling.
- **Recommendation**: Upgrade to Aurora MySQL for automatic failover, read replicas, and better performance. Per customer preference for `rds-aurora`, migrate using AWS DMS or Aurora read replica promotion. Size appropriately for production workloads.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service is present in the IaC or application code. The fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) is implemented as sequential manual API calls from the admin UI in `index.php`.
- **Gap**: No dedicated orchestration for multi-step business workflows. The fulfillment workflow is entirely manual and has no automated state machine, retry logic, or failure handling.
- **Recommendation**: Implement AWS Step Functions for the fulfillment workflow. Each step (validate, assign-warehouse, pick, pack, quality-check, ship, deliver) maps directly to a Step Functions state with retry and error handling.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or any messaging service is defined in `infrastructure/monolith-apprunner.yaml` or referenced in `index.php`. All communication is synchronous HTTP within the monolith's single PHP process.
- **Gap**: No event-driven patterns. All domain interactions (order creation triggers inventory update, payment, status update) happen in a single synchronous database transaction in `index.php`.
- **Recommendation**: Introduce Amazon EventBridge as the event bus for domain events (OrderCreated, PaymentProcessed, InventoryUpdated). Start by publishing events from the monolith before extracting consumers into separate services.

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` is a comprehensive CloudFormation template covering VPC, private subnets, RDS, App Runner, WAF, IAM roles, ECR, and auto-scaling configuration. All production infrastructure is defined in IaC.
- **Gap**: Using CloudFormation rather than Terraform (customer preference). No Helm charts or Kubernetes manifests for the EKS target state. No IaC for observability (CloudWatch dashboards, alarms, X-Ray).
- **Recommendation**: Migrate IaC from CloudFormation to Terraform per customer preference. Define EKS cluster, node groups, and supporting infrastructure in Terraform. Create Helm charts for application deployments managed via GitOps.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: The only deployment mechanism is `deploy.sh`, a 30-line bash script that runs `docker-compose build` and `docker-compose up -d` for local deployment. No GitHub Actions workflows, no `buildspec.yml`, no Jenkinsfile, no CodePipeline definitions found anywhere in the repository.
- **Gap**: No automated CI/CD pipeline. No automated testing, building, or deployment to AWS. The CloudFormation output includes manual `docker build`, `docker tag`, and `docker push` instructions.
- **Recommendation**: Create a GitHub Actions pipeline with stages: lint → test → build Docker image → push to ECR → deploy to EKS via ArgoCD. Implement GitOps with ArgoCD syncing Helm charts from the Git repository.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: App Runner provides a managed HTTPS endpoint URL (`ServiceUrl` output in `infrastructure/monolith-apprunner.yaml`). WAF (`AWS::WAFv2::WebACL`) is configured for IP-based access control (block all, allow specific IP via IPSet). No API Gateway is present.
- **Gap**: No API Gateway with throttling, request validation, or API key management. WAF only provides IP whitelisting, not rate limiting or request shaping. No centralized API management for the future microservices.
- **Recommendation**: Deploy Amazon API Gateway as the unified entry point for all microservices. Configure throttling, request validation, and API key management. Use API Gateway + ALB Ingress on EKS for routing to individual services.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming service found in `infrastructure/monolith-apprunner.yaml` or `index.php`. No event streaming patterns detected.
- **Gap**: No real-time event streaming capability. Order status changes, inventory updates, and fulfillment events are all synchronous database writes with no streaming for real-time visibility.
- **Recommendation**: Evaluate need for real-time streaming as services are extracted. Consider Amazon EventBridge for event routing and Kinesis Data Streams if real-time order/inventory analytics are required.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` defines a VPC (`10.0.0.0/16`) with two private subnets for RDS (`10.0.1.0/24`, `10.0.2.0/24`). `DBSecurityGroup` restricts MySQL port 3306 to only the `AppRunnerSecurityGroup`. WAF provides IP whitelisting. RDS is not publicly accessible (`PubliclyAccessible: false`).
- **Gap**: No public subnets or NAT gateway defined (App Runner VPC connector handles egress). No NACLs configured beyond VPC defaults. No network segmentation beyond public/private split. WAF rules are minimal (IP whitelist only).
- **Recommendation**: For EKS deployment, define public and private subnet tiers with NAT gateways. Implement network policies in EKS for pod-to-pod traffic control. Expand WAF rules to include rate limiting, SQL injection, and XSS protection.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: `AWS::AppRunner::AutoScalingConfiguration` in `infrastructure/monolith-apprunner.yaml` defines auto-scaling with `MinSize: 1`, `MaxSize: 3`, `MaxConcurrency: 100`.
- **Gap**: Scaling is basic (min 1, max 3) with concurrency-based triggers only. No per-service scaling policies for the future microservices architecture. No database scaling (single `db.t3.micro` instance).
- **Recommendation**: For EKS, implement Horizontal Pod Autoscaler (HPA) per service with CPU/memory and custom metrics. Use Karpenter for node-level auto-scaling. Upgrade RDS to Aurora with auto-scaling read replicas.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: PHP 8.2 is the sole language (`FROM php:8.2-apache` in `Dockerfile`). The application uses built-in PHP functions, PDO for database access, and no external dependencies (no `composer.json` found). PHP has a limited but growing agent framework ecosystem compared to Python or TypeScript.
- **Gap**: PHP has fewer mature agent and AI framework options than Python (LangChain, Strands Agents) or TypeScript (LangChain.js). No dependency management via Composer is present, limiting extensibility.
- **Recommendation**: For extracted microservices, consider Python or TypeScript for services that will integrate with AI/agent frameworks. The fulfillment service is a strong candidate for Python (Step Functions + Bedrock). Keep PHP for services where the existing business logic is complex and rewriting would be high-risk.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No `openapi.yaml`, `swagger.json`, or API documentation files found in the repository. API routes are defined inline in `index.php` using regex-based routing (e.g., `preg_match('#^/api/orders/([^/]+)/validate$#', $request_uri, $matches)`). No annotations or auto-generation of API specs.
- **Gap**: 20+ API endpoints exist with no documentation. Endpoints include `/api/products`, `/api/orders`, `/api/orders/{id}/validate`, `/api/warehouses/assignment-options`, `/api/carriers/shipping-options`, `/api/admin/users`, and more — all undocumented.
- **Recommendation**: Generate OpenAPI specs for all existing endpoints before decomposition. Each extracted microservice must have its own OpenAPI spec. Use tools like `swagger-php` for the monolith or manually document the API contract for each bounded context.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% of communication is synchronous. In `index.php`, the order creation endpoint (`/api/orders` POST) performs inventory check, order insert, item inserts, inventory deduction, payment insert, and status update all within a single `$db->beginTransaction()` / `$db->commit()` block. All fulfillment steps are synchronous API calls from the admin UI.
- **Gap**: No message queues, event buses, or async processing. The tightly-coupled synchronous transaction model means a failure in payment processing will roll back inventory changes. Decomposed services cannot share database transactions.
- **Recommendation**: Introduce event-driven patterns using Amazon EventBridge. The fulfillment workflow is the first candidate: publish `OrderConfirmed` events and let downstream services (warehouse, picking, shipping) subscribe asynchronously. Implement the Saga pattern for distributed transactions.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: A single `index.php` file (~2000+ lines) contains ALL business domains: Orders (CRUD, status management), Inventory (product catalog, stock management), Payments (processing, refunds), Returns (request, approval), Users (authentication, CRUD), Fulfillment (validation, warehouse assignment, picking, packing, QC, shipping, delivery), and Warehouses (assignment, capacity). All domains share a single MySQL database with cross-domain foreign keys (`order_items.order_id → orders.id`, `payments.order_id → orders.id`, `returns.order_id → orders.id`). There are no module boundaries, no separate classes, no namespace separation. Every route handler directly executes SQL queries against shared tables.
- **Gap**: This is a maximally tightly-coupled monolith — single file, single database, shared state, circular domain dependencies (orders reference payments, returns reference orders, inventory referenced by order_items). No clear module interfaces. Shared mutable state throughout. Database coupling via foreign keys across all domains. Independent scaling, deployment, or failure isolation is impossible.
- **Recommendation**: See Microservices Decomposition Strategy section below. Begin with domain modeling to identify bounded contexts: Orders, Inventory, Payments, Returns, Fulfillment, Users. Extract the Fulfillment service first (high business value, most complex workflow, clearest domain boundary).

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: All API endpoints in `index.php` return structured JSON via `json_encode()` with `header('Content-Type: application/json')`. Response shapes include `{'products': [...]}`, `{'success': true, 'order_id': '...'}`, `{'error': '...'}`, `{'warehouses': [...]}`, etc. The frontend renders HTML separately.
- **Gap**: No standardized response envelope (no consistent error format, pagination metadata, or HATEOAS links). Some responses use `{'success': true}` while errors use `{'error': '...'}` — inconsistent patterns.
- **Recommendation**: Standardize API response format across all endpoints before decomposition. Adopt a consistent envelope: `{data: {...}, error: null, meta: {pagination: {...}}}`. This becomes the contract for each microservice.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: The fulfillment workflow in `index.php` is implemented as 7 separate API endpoints that must be called manually in sequence: `/api/orders/{id}/validate` → `/api/orders/{id}/assign-warehouse` → `/api/orders/{id}/pick` → `/api/orders/{id}/pack` → `/api/orders/{id}/quality-check` → `/api/orders/{id}/ship` → `/api/orders/{id}/deliver`. Each endpoint updates the order status directly in the database. No orchestration engine manages the sequence.
- **Gap**: No state machine, no retry on failure, no timeout handling, no parallel execution. If the admin skips a step or a step fails silently, the order enters an inconsistent state. The workflow is entirely dependent on manual human execution in the correct sequence.
- **Recommendation**: Model the fulfillment workflow as an AWS Step Functions state machine. Each step becomes a Lambda or EKS service task. Step Functions provides built-in retry, timeout, error handling, and visual workflow monitoring.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys found in any API endpoint in `index.php`. Order IDs are generated using `uniqid('order-')`, payment IDs with `uniqid('pay-')`, and return IDs with `uniqid('return-')` — all non-deterministic. No deduplication patterns, no `Idempotency-Key` header handling. Duplicate POST requests to `/api/orders` will create duplicate orders.
- **Gap**: No idempotency for any write operation. This is a critical gap for microservices where network retries are common and agent workflows may retry failed tool calls.
- **Recommendation**: Implement idempotency keys for all write endpoints. Use a client-provided `Idempotency-Key` header with server-side deduplication (store keys in DynamoDB or Redis with TTL). Critical for the Orders and Payments services.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: WAF in `infrastructure/monolith-apprunner.yaml` provides IP-based allow/block but no rate limiting rules. No rate limiting middleware in `index.php`. No `express-rate-limit` equivalent for PHP. No API Gateway usage plans or throttling configuration.
- **Gap**: No rate limiting at any layer. A single client can make unlimited API calls. Critical for microservices where individual services need protection from cascading load.
- **Recommendation**: Implement rate limiting at the API Gateway level with per-client throttling policies. For EKS, use Istio or AWS App Mesh with rate limiting. Add application-level rate limiting middleware for critical endpoints (order creation, payment processing).

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: `index.php` uses basic `try/catch` blocks around database operations but has no retry logic, no circuit breakers, no timeouts, and no fallback patterns. The `get_db()` function calls `die()` on connection failure — a hard crash with no recovery. External service calls (none present, but the pattern is set) have no resilience.
- **Gap**: No resilience patterns whatsoever. `die()` on database failure means the entire application crashes. No retry with exponential backoff. No circuit breakers for downstream service protection (critical when decomposing into microservices).
- **Recommendation**: Before decomposition, implement resilience patterns in the monolith. Replace `die()` with graceful error handling. For extracted services, use a resilience library (Polly for .NET, Resilience4j for Java, or tenacity for Python). Configure circuit breakers, retries with exponential backoff, and timeouts for all inter-service calls.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All operations in `index.php` execute synchronously within the HTTP request/response cycle. The order creation flow (inventory check + order insert + item inserts + inventory update + payment insert + status update) executes as a single synchronous database transaction. No background job framework (no Celery, no Bull, no SQS workers).
- **Gap**: No async processing for any operation. The fulfillment workflow (validate → warehouse → pick → pack → QC → ship → deliver) is manual but could take hours or days in reality. No job queue, no status polling, no callback patterns.
- **Recommendation**: Implement async processing with SQS + worker containers on EKS. The fulfillment workflow should be orchestrated by Step Functions with each step as an async task. Return job IDs for long-running operations and provide status polling endpoints.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning found in `index.php`. All routes use unversioned paths: `/api/products`, `/api/orders`, `/api/returns`, `/api/admin/users`. No `/v1/` prefix, no `Accept-Version` headers, no version parameters. No changelog.
- **Gap**: No versioning strategy. Breaking changes to API contracts will affect all consumers simultaneously. Critical when microservices evolve independently and agents depend on stable API contracts.
- **Recommendation**: Adopt URL path versioning (`/v1/api/products`) for all services before extraction. Each microservice manages its own API version independently. Use API Gateway to route versioned requests to the correct service deployment.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith with no inter-service communication. The only external dependency is the MySQL database, accessed via the `DB_HOST` environment variable set in `infrastructure/monolith-apprunner.yaml` (pointing to the RDS endpoint). No service registry, no API catalog, no service mesh.
- **Gap**: No service discovery mechanism. As services are extracted, they will need to locate each other. Environment variable-based configuration does not scale to a microservices architecture.
- **Recommendation**: Implement Kubernetes-native service discovery (CoreDNS) on EKS. Use AWS Cloud Map for cross-namespace or cross-cluster discovery. Consider AWS App Mesh or Istio service mesh for advanced traffic management as the service count grows.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework references found in `index.php`. No `composer.json` with AI library dependencies. No Bedrock SDK, no LangChain, no OpenAI SDK, no MCP SDK. No embedding generation, no LLM calls, no agent patterns.
- **Gap**: No AI/agent integration whatsoever. The application has no foundation for agentic workflows.
- **Recommendation**: After decomposition, add Bedrock integration to the Fulfillment service for AI-assisted decision-making (warehouse selection, fraud detection, carrier optimization). Use Strands Agents SDK (Python) or Amazon Bedrock AgentCore for building agent workflows that interact with the extracted microservice APIs.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch with k-NN, no Aurora pgvector, no S3 Vectors, no Bedrock Knowledge Bases, no Pinecone/Weaviate/Chroma references in `index.php` or `infrastructure/monolith-apprunner.yaml`.
- **Gap**: No vector storage capability. Semantic search, RAG, and agent memory are not possible without a vector store.
- **Recommendation**: Deploy Amazon OpenSearch Service with k-NN plugin or Aurora PostgreSQL with pgvector extension as part of the Phase 3 AI enablement. Per customer preference for `rds-aurora`, pgvector on Aurora PostgreSQL is the recommended path.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists to evaluate management status. No self-hosted or managed vector DB detected.
- **Gap**: No vector DB present at all.
- **Recommendation**: When implementing a vector DB, use a managed service (Aurora PostgreSQL with pgvector, or OpenSearch Service) to avoid operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No document chunking, embedding generation, or semantic search patterns found in `index.php`. No Bedrock Titan/OpenAI embedding calls. No similarity search or k-NN query patterns. No Bedrock Knowledge Base configuration.
- **Gap**: No RAG pipeline. The application cannot perform semantic search over product catalogs, order history, or documentation.
- **Recommendation**: Implement RAG in Phase 3 using Amazon Bedrock Knowledge Bases with Aurora PostgreSQL (pgvector) as the vector store. Start with product catalog and order documentation as the knowledge base.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Single MySQL database is the only data source. All 9 tables (orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users) reside in one `ecommerce` database. The `get_db()` function in `index.php` is the single connection point.
- **Gap**: While having a single data source is simple, all domains share the same database with foreign keys, making database-per-service decomposition complex. The shared database will become a bottleneck during microservices extraction.
- **Recommendation**: Plan database decomposition alongside service extraction. Each microservice should own its data. Use the Strangler Fig pattern: new services read/write to their own database while maintaining sync with the shared database during transition.

#### DATA-Q5: Data Access Pattern
- **Score**: 1/4 ❌
- **Finding**: Direct PDO queries are scattered throughout `index.php`. Every API route handler directly constructs and executes SQL queries — e.g., `$db->prepare('SELECT * FROM orders WHERE id = ?')`. No repository pattern, no ORM, no data access layer abstraction. The `get_db()` function returns a raw PDO connection used everywhere.
- **Gap**: No abstraction layer between business logic and database queries. SQL is embedded in route handlers. This makes database-per-service migration extremely difficult because every query must be refactored.
- **Recommendation**: Before extracting services, refactor data access into domain-specific repository classes (OrderRepository, InventoryRepository, etc.). This creates clear data ownership boundaries and makes it straightforward to replace direct DB access with API calls when services are extracted.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing (Textract, Tika), no file upload handling. Product images reference URL paths (`/images/tshirt.jpg`) in the inventory seed data, but no actual image storage or retrieval is implemented in `index.php`.
- **Gap**: No unstructured data handling capability. Product images are referenced but not stored or served.
- **Recommendation**: Implement S3 for product images and document storage. Add CloudFront CDN for image delivery. This is a Phase 2 activity during service extraction.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: Database schema is defined inline in the `init_db()` function in `index.php` using `CREATE TABLE IF NOT EXISTS` statements. Schema modifications use `ALTER TABLE` wrapped in try/catch blocks that silently ignore failures. No migration files (Flyway, Liquibase, Alembic), no JSON Schema, no schema registry. No ERD documentation.
- **Gap**: No versioned schema management. Schema changes are ad-hoc and error-prone. No way to track which schema version is deployed. The `ALTER TABLE` try/catch pattern means schema drift is undetectable.
- **Recommendation**: Implement a database migration tool (Flyway for MySQL) before decomposition. Version all schema changes. Generate ERD documentation. Each microservice's database must have its own migration history.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. `get_db()` returns a PDO connection, and every route handler writes raw SQL. For example, the `/api/orders` POST handler has 6 separate SQL queries inline. The `/api/admin/approve-return` handler has 5 inline queries spanning orders, returns, order_items, inventory, and payments tables — crossing 5 domain boundaries in a single handler.
- **Gap**: Complete absence of data access abstraction. Scattered SQL queries make it impossible to audit data dependencies, enforce access policies, or safely extract services.
- **Recommendation**: Create domain repository classes as the first refactoring step. Map each query to its owning domain. Identify cross-domain queries (like the approve-return flow) that must become inter-service API calls after decomposition.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist. No embedding generation, no index refresh, no CDC patterns found.
- **Gap**: No embedding infrastructure to evaluate freshness.
- **Recommendation**: When RAG is implemented in Phase 3, configure event-driven embedding refresh triggered by product catalog updates or order documentation changes. Use Aurora CDC with EventBridge for real-time trigger.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: `infrastructure/monolith-apprunner.yaml` explicitly specifies `EngineVersion: '8.4.8'` for the RDS MySQL instance. MySQL 8.4 is the current LTS (Long-Term Support) release with support through 2032. `AutoMinorVersionUpgrade: true` is enabled for automatic patching. The `docker-compose.yml` uses `mysql:8.0` for local development, which is also currently supported.
- **Gap**: None — the database engine version is current and explicitly pinned.
- **Recommendation**: Maintain current version pinning practice. When migrating to Aurora MySQL, target the compatible Aurora version for MySQL 8.4.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs found in `index.php`. All `CREATE TABLE` statements use standard MySQL/InnoDB DDL. All business logic is in the PHP application layer. No `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION`. No PL/SQL or T-SQL detected.
- **Gap**: None — all business logic is in the application layer, making database migration straightforward.
- **Recommendation**: Maintain this pattern. Keeping business logic out of the database simplifies migration to Aurora MySQL and enables per-service database ownership during decomposition.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are passed via environment variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`) in `index.php`. The `infrastructure/monolith-apprunner.yaml` CloudFormation template defines the DB password as a parameter with `NoEcho: true` but includes a default value of `ChangeMe123!`. `docker-compose.yml` has hardcoded credentials (`MYSQL_ROOT_PASSWORD: rootpassword`, `MYSQL_PASSWORD: ecommerce_pass`). `index.php` has fallback defaults (`$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`). No AWS Secrets Manager or HashiCorp Vault usage.
- **Gap**: Secrets are hardcoded in multiple files with insecure defaults. The CloudFormation default password is a critical security risk. No dynamic secret rotation.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager. Use Secrets Manager dynamic references in CloudFormation/Terraform. Remove all hardcoded credentials from `docker-compose.yml` and `index.php`. Enable automatic rotation for the RDS password.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: `infrastructure/monolith-apprunner.yaml` defines two IAM roles: `AppRunnerInstanceRole` with `arn:aws:iam::aws:policy/CloudWatchLogsFullAccess` (overly broad — grants full access to all CloudWatch Logs operations), and `AppRunnerAccessRole` with `arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess` (appropriately scoped).
- **Gap**: `CloudWatchLogsFullAccess` grants permissions far beyond what the application needs (includes CreateLogGroup, DeleteLogGroup, PutLogEvents on all resources). The instance role has no additional policies for RDS, S3, or other services.
- **Recommendation**: Replace `CloudWatchLogsFullAccess` with a custom policy scoped to specific log groups (`logs:CreateLogStream`, `logs:PutLogEvents` on `arn:aws:logs:*:*:log-group:/aws/apprunner/*`). For EKS, implement IRSA (IAM Roles for Service Accounts) with per-service least-privilege policies.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: `index.php` uses PHP session-based authentication (`session_start()`, `$_SESSION['user']`). Login sets `$_SESSION['user']` with the user object. API endpoints check `if (!isset($_SESSION['user']))` for authentication. No JWT, no OAuth2, no token exchange patterns. User identity is stored in a PHP session cookie.
- **Gap**: Session-based auth does not propagate identity across services. In a microservices architecture, each service must independently verify the caller's identity. PHP sessions are not portable across service boundaries.
- **Recommendation**: Replace PHP sessions with JWT-based authentication. Implement Amazon Cognito as the identity provider. Issue JWTs on login and validate them in each microservice. Propagate user context via `Authorization: Bearer <token>` headers.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in `infrastructure/monolith-apprunner.yaml`. WAF has `CloudWatchMetricsEnabled: true` for basic request metrics. The `order_status_history` table in `index.php` logs order status changes with `changed_by` field — this is application-level audit logging for a single domain (orders), not comprehensive audit logging.
- **Gap**: No AWS CloudTrail for API-level audit logging. No immutable log storage. Application-level audit logging is limited to order status changes only. No audit trail for user management, inventory changes, or payment operations.
- **Recommendation**: Enable CloudTrail with log file validation and S3 bucket with object lock for immutable storage. Extend application-level audit logging to all domain operations (user CRUD, inventory changes, payment processing). Centralize logs in CloudWatch Logs with retention policies.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: WAF in `infrastructure/monolith-apprunner.yaml` is configured for IP whitelisting only (block all, allow specific IP via IPSet). No rate limit rules in WAF. No application-level rate limiting in `index.php`. No API Gateway with throttling.
- **Gap**: No rate limiting at any layer. The application is vulnerable to abuse, brute-force attacks, and resource exhaustion.
- **Recommendation**: Add WAF rate-based rules immediately (e.g., limit 1000 requests per 5-minute window per IP). For EKS, implement API Gateway with per-client usage plans and throttling. Add rate limiting middleware to critical endpoints.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: `index.php` stores and returns PII in API responses without redaction: customer names (`customer_name`), emails (`customer_email`), shipping addresses, and order details. The validation-data endpoint returns full customer profiles including email, order history, and spending patterns. `error_reporting(E_ALL)` is set with `log_errors` enabled but no PII filtering on log output.
- **Gap**: No PII masking, no log scrubbing, no Macie integration. Customer data is freely accessible in API responses and potentially in logs.
- **Recommendation**: Implement PII redaction middleware that masks email addresses and addresses in logs. Use Amazon Macie for S3-stored data classification. Apply field-level encryption for sensitive data. Implement response filtering based on caller role.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: Return approval in `index.php` requires admin role (`$_SESSION['user']['role'] !== 'admin'` check on `/api/admin/approve-return`). Order validation requires manual admin review via `/api/orders/{id}/validate`. These are role-based access controls, not formal human-in-the-loop approval workflows.
- **Gap**: No Step Functions with human approval tasks, no waitForTaskToken patterns, no approval queues. The "approval" is just a manual API call with an admin session — there's no workflow engine enforcing the approval sequence or escalation.
- **Recommendation**: Implement Step Functions with human approval tasks for high-risk operations (return processing, large order validation, refund authorization). Use `waitForTaskToken` pattern with SNS/SES notifications for approval requests.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: RDS MySQL has `StorageEncrypted: true` in `infrastructure/monolith-apprunner.yaml` (uses AWS-managed KMS key by default — no explicit `KmsKeyId` specified). ECR uses `EncryptionType: AES256` (server-side encryption). No customer-managed KMS keys are defined.
- **Gap**: Using AWS-managed encryption keys, not customer-managed KMS keys. No control over key rotation schedule. No KMS key policy for fine-grained access control.
- **Recommendation**: Create customer-managed KMS keys for RDS, ECR, and future S3 buckets. Define key policies restricting usage to specific IAM roles. Enable automatic key rotation. This is important for compliance and audit requirements.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: All API endpoints in `index.php` require a valid PHP session (`if (!isset($_SESSION['user']))`). Admin endpoints additionally check `$_SESSION['user']['role'] !== 'admin'`. Login uses `password_verify()` with bcrypt-hashed passwords. The authentication is functional but uses session cookies rather than OAuth2/JWT.
- **Gap**: No OAuth2, no JWT, no API keys for machine-to-machine communication. Session-based auth is not suitable for microservices or API-first architectures. No token expiration beyond session timeout.
- **Recommendation**: Migrate to Amazon Cognito with OAuth2/OIDC. Issue JWTs with appropriate claims (user_id, role, permissions). Implement API key authentication for service-to-service calls. Each microservice validates JWTs independently.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: User management is entirely internal — the `users` table in MySQL stores usernames, bcrypt password hashes, emails, and roles. Login/registration is handled in `index.php`. No Amazon Cognito, no Okta, no SAML/OIDC federation. No SSO.
- **Gap**: No centralized identity provider. User credentials are stored directly in the application database. No SSO, no federation, no external identity provider integration.
- **Recommendation**: Migrate to Amazon Cognito as the centralized identity provider. Migrate existing users to Cognito user pool. Implement OIDC federation for enterprise SSO. Each microservice authenticates via Cognito JWT validation.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, Datadog, Jaeger, or any tracing SDK found in `index.php`, `Dockerfile`, or `infrastructure/monolith-apprunner.yaml`. No trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`). No auto-instrumentation configuration. No dependency manifests (no `composer.json`) that could contain tracing libraries.
- **Gap**: No distributed tracing capability. As services are extracted from the monolith, cross-service request tracing becomes essential for debugging distributed failures. Without tracing, decomposition will produce an opaque, unmaintainable system.
- **Recommendation**: Add OpenTelemetry PHP auto-instrumentation to the monolith container before decomposition. For EKS, deploy OpenTelemetry Collector as a DaemonSet. Configure AWS X-Ray as the tracing backend. Ensure trace context propagation in all inter-service HTTP headers.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: `index.php` configures `error_reporting(E_ALL)` and `ini_set('log_errors', '1')` — standard PHP error logging to Apache error log. No JSON log formatters, no structured logging library (Monolog), no correlation IDs, no request ID tracking. Error output goes to Apache's default error log format.
- **Gap**: No structured JSON logging. No correlation IDs for request tracing. Logs are unstructured text, making CloudWatch Log Insights queries difficult. No way to correlate logs across services during decomposition.
- **Recommendation**: Implement Monolog with JSON formatter for structured logging in PHP. Add a correlation ID middleware that generates/propagates a request ID. For EKS, configure Fluent Bit as a DaemonSet to ship structured JSON logs to CloudWatch Logs.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no test datasets, no scoring scripts, no LLM-as-judge patterns found anywhere in the repository. No AI/agent code exists to evaluate.
- **Gap**: No agent evaluation capability. This will be needed in Phase 3 when AI/agent features are added.
- **Recommendation**: Implement an eval framework when AI features are added in Phase 3. Use RAGAS for RAG evaluation, golden datasets for agent tool-use accuracy, and automated regression testing for prompt changes.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions in `infrastructure/monolith-apprunner.yaml` or anywhere in the repository. No CloudWatch alarms defined. App Runner has a health check configuration (HTTP check on `/`, interval 10s, timeout 5s) but no SLO monitoring, no latency tracking, no error budget.
- **Gap**: No SLOs defined for any user journey. No alerting on latency or error rates. No way to measure service reliability objectively.
- **Recommendation**: Define SLOs for critical user journeys: order placement (p99 < 2s, 99.9% availability), product listing (p99 < 500ms, 99.95% availability). Implement CloudWatch alarms for SLO breaches. Use CloudWatch Synthetics for canary monitoring.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: `deploy.sh` runs `docker-compose up -d` with no rollback mechanism. CloudFormation stack supports rollback on failure but no automated deployment rollback is configured. No blue/green deployment, no canary, no feature flags. No prompt versioning (no AI features).
- **Gap**: No automated rollback for code or configuration. A bad deployment requires manual intervention to revert.
- **Recommendation**: For EKS with ArgoCD, implement automatic rollback on failed health checks. Use Helm rollback for quick revert. Implement Argo Rollouts for progressive delivery with automatic rollback on error rate thresholds.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no usage tracking. No observability data retention policies.
- **Gap**: No LLM cost tracking infrastructure. Will be needed when AI features are added.
- **Recommendation**: When AI features are added in Phase 3, implement per-request token tracking with CloudWatch custom metrics. Tag costs by feature/user/workflow. Define retention policies for LLM prompt/response logs.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics in `index.php` or `infrastructure/monolith-apprunner.yaml`. No business outcome tracking (order conversion rates, fulfillment times, return rates). The `order_status_history` table captures status transitions but is not published as metrics.
- **Gap**: No business metrics beyond basic infrastructure monitoring. No dashboards for order volume, fulfillment pipeline throughput, or customer satisfaction.
- **Recommendation**: Publish custom CloudWatch metrics for: orders per hour, fulfillment pipeline stage durations, return rate, average order value. Create CloudWatch dashboards for business visibility. Each microservice should publish its own domain-specific metrics.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection configured. No CloudWatch alarms. WAF has `CloudWatchMetricsEnabled: true` but no alerting rules. No PagerDuty/OpsGenie integration. No composite alarms.
- **Gap**: No alerting on error rates, latency spikes, or traffic anomalies. The application could fail silently with no notification.
- **Recommendation**: Enable CloudWatch anomaly detection on key metrics (error rate, latency, request count). Configure SNS alerting for anomaly breaches. Integrate with PagerDuty or OpsGenie for incident management. For EKS, use CloudWatch Container Insights.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Deployment is via `deploy.sh`, which runs `docker-compose build` and `docker-compose up -d` — a direct-to-production deployment with no rollout strategy. No blue/green, no canary, no traffic shifting. No CodeDeploy, no Argo Rollouts, no feature flags.
- **Gap**: All deployments are all-or-nothing. No ability to gradually shift traffic to new versions. No automated health check gating before full rollout.
- **Recommendation**: Implement GitOps with ArgoCD on EKS. Use Argo Rollouts for canary deployments with automatic analysis and rollback. Define progressive delivery steps: 10% → 25% → 50% → 100% with health check gates at each step.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found in the repository. No test framework (no PHPUnit, no Pest). No integration test suites, no API test collections (no Postman/Newman), no contract tests. No test stage in the (non-existent) CI/CD pipeline.
- **Gap**: Zero tests. No way to verify that changes don't break existing functionality. Critical blocker for safe decomposition — every service extraction must be validated by tests.
- **Recommendation**: Start with API integration tests for all existing endpoints (use PHPUnit or Pest for PHP, or Postman/Newman for API-level tests). Add contract tests for each domain's API. Run tests in CI pipeline before every deployment. Target 80% coverage for critical paths before first service extraction.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files found in the repository. No SSM Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. No self-healing patterns. No alert-to-runbook linking.
- **Gap**: No incident response automation. All incident handling is manual. No machine-readable runbooks for future agent-based operations.
- **Recommendation**: Create markdown runbooks for common incidents (database connection failures, high latency, deployment failures). Store in the repository. Implement SSM Automation documents for auto-remediation of known issues. Link runbooks to CloudWatch alarm actions.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO definition files or dashboards. No team ownership files referencing observability assets. No platform team tooling configuration. The only observability-related resource is the `CloudWatchLogsFullAccess` policy on the App Runner instance role.
- **Gap**: No observability ownership model. No SLO culture. No shared responsibility model for monitoring.
- **Recommendation**: Define CODEOWNERS for the repository. Assign observability ownership per service as services are extracted. Establish SLO-driven culture with defined owners for each service's SLOs. Create a platform engineering team responsible for centralized observability infrastructure on EKS.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | High | High | APP-Q4: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Not Triggered | High | — | — | — |
| Move to Open Source | Not Triggered | Medium | — | — | — |
| Move to Managed Databases | Not Triggered | Medium | — | — | — |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Low | Low | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps — CI/CD pipeline, IaC migration to Terraform, testing framework, observability foundation. Can start immediately and runs independently.

**Parallel Track 2**: Move to Cloud Native — Domain modeling, service extraction planning, Helm chart creation. Can start in parallel with Track 1. Benefits from Track 1's CI/CD and testing infrastructure.

**Sequential Dependencies**: Move to Modern DevOps should establish CI/CD and testing foundations (Phase 1) before Move to Cloud Native begins service extraction (Phase 2). Move to AI depends on both Cloud Native decomposition and Modern DevOps observability (Phase 3).

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Tightly-coupled monolith with all business domains in a single `index.php` file, shared MySQL database with cross-domain foreign keys
  - APP-Q3: Score 1/4 — 100% synchronous communication within the monolith; no async patterns
  - APP-Q10: Score 1/4 — No async processing for long-running operations; all operations are synchronous HTTP request/response
- **Current State**: Single PHP monolith (`index.php`) deployed on App Runner. All 7 business domains (Orders, Inventory, Payments, Returns, Users, Fulfillment, Warehouses) are in one file with a shared MySQL database. No service boundaries, no module interfaces, no async communication.
- **Target State**: 4-6 independently deployable microservices on EKS (Fargate), each with its own database, communicating via EventBridge events and API Gateway. Fulfillment orchestrated by Step Functions. Each service has its own Helm chart, CI/CD pipeline, and API documentation.
- **Key Activities**:
  1. Conduct domain modeling / EventStorming workshop to identify bounded contexts
  2. Map data dependencies and identify database decomposition strategy
  3. Extract Fulfillment service as first microservice (Strangler Fig pattern)
  4. Implement API Gateway for routing between monolith and new services
  5. Introduce EventBridge for domain events (OrderCreated, PaymentProcessed)
  6. Implement Saga pattern for distributed transactions across services
- **Dependencies**: Move to Modern DevOps must establish CI/CD and testing before extraction begins
- **Estimated Effort**: High — 3-6 months for full decomposition
- **Roadmap Phase Alignment**: Phase 2 (Decompose & Decouple) and Phase 3 (Optimize & Scale)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline; only manual `deploy.sh` script
  - OPS-Q9: Score 1/4 — Manual deployment via `docker-compose up -d`; no progressive delivery
  - OPS-Q10: Score 1/4 — Zero tests; no test framework, no integration tests, no CI test stage
  - OPS-Q1: Score 1/4 — No distributed tracing; no OpenTelemetry, no X-Ray
- **Current State**: Manual deployment via `deploy.sh` (docker-compose). No CI/CD pipeline. No testing framework. No observability (no tracing, no structured logging, no metrics, no alerting). CloudFormation IaC exists but needs migration to Terraform per preferences.
- **Target State**: Full GitOps deployment pipeline with GitHub Actions → ECR → ArgoCD → EKS. Automated testing (unit, integration, contract). OpenTelemetry tracing and structured logging. SLO-based monitoring with CloudWatch. Progressive delivery with Argo Rollouts.
- **Key Activities**:
  1. Create GitHub Actions CI/CD pipeline (lint → test → build → push to ECR)
  2. Set up ArgoCD on EKS for GitOps deployments
  3. Write integration tests for existing API endpoints
  4. Add OpenTelemetry instrumentation to the monolith
  5. Implement structured JSON logging with correlation IDs
  6. Define SLOs and configure CloudWatch alarms
  7. Migrate IaC from CloudFormation to Terraform
- **Dependencies**: None — can start immediately
- **Estimated Effort**: High — 2-4 weeks for foundation, ongoing for maturity
- **Roadmap Phase Alignment**: Phase 1 (Containerize & Automate) — immediate priority
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: Low
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks; no Bedrock, LangChain, or agent SDK
  - DATA-Q1: Score 1/4 — No vector database for semantic search or agent memory
  - DATA-Q3: Score 1/4 — No RAG implementation; no embeddings, no chunking, no semantic search
  - OPS-Q3: Score 1/4 — No evaluation framework for AI/agent quality
  - OPS-Q6: Score 1/4 — No LLM cost tracking (no LLM usage exists)
- **Current State**: No AI or agent capabilities. No vector database. No RAG pipeline. No LLM integration. The application has decision-support endpoints (fraud validation, warehouse recommendation, carrier optimization) that could benefit from AI but are currently rule-based.
- **Target State**: AI-assisted decision-making in the Fulfillment service (automated warehouse selection, fraud detection, carrier optimization). RAG over product catalog and order documentation. Agent evaluation framework.
- **Key Activities**:
  1. Add Aurora PostgreSQL with pgvector for vector storage
  2. Implement Bedrock integration for fulfillment decisions
  3. Build RAG pipeline with Bedrock Knowledge Bases
  4. Create agent evaluation framework with golden datasets
  5. Implement LLM cost tracking with CloudWatch custom metrics
- **Dependencies**: Move to Cloud Native (service boundaries needed for agent tool isolation) and Move to Modern DevOps (observability needed for agent monitoring)
- **Estimated Effort**: High — 2-3 months after Phase 2 foundations are in place
- **Roadmap Phase Alignment**: Phase 3 (Optimize & Scale)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

The monolith contains 7 identifiable bounded contexts based on analysis of `index.php`:

| Domain | Tables Owned | Key Endpoints | Coupling Level |
|--------|-------------|---------------|----------------|
| **Orders** | orders, order_items, order_status_history | `/api/orders`, `/api/orders/{id}/history` | High (FK to inventory, payments, returns) |
| **Inventory** | inventory | `/api/products` | Medium (referenced by order_items FK) |
| **Payments** | payments | (embedded in order creation) | High (FK to orders) |
| **Returns** | returns, interactions | `/api/returns`, `/api/admin/pending-returns`, `/api/admin/approve-return` | High (FK to orders, touches inventory + payments) |
| **Fulfillment** | (uses orders, warehouses) | `/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, `/api/orders/{id}/pick`, `/api/orders/{id}/pack`, `/api/orders/{id}/quality-check`, `/api/orders/{id}/ship`, `/api/orders/{id}/deliver` | High (reads/writes orders, uses warehouses) |
| **Warehouses** | warehouses | `/api/warehouses/assignment-options`, `/api/carriers/shipping-options` | Low (referenced by fulfillment) |
| **Users** | users | `/api/admin/users`, `/login`, `/logout` | Low (only authentication dependency) |

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure while incrementally extracting services
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract the **Fulfillment** service first — it has the highest business value (automates the manual 7-step workflow), the most complex domain logic, and clear API boundaries (7 dedicated endpoints). The Fulfillment service has read-only dependencies on Orders and Warehouses, making it a clean extraction target.
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently, containerize modular components as-is, refactor tightly-coupled ones
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Containerize **Users** service first (lowest coupling — only username/password verification, no domain data dependencies). Then **Warehouses** (low coupling — standalone data). Defer tightly-coupled **Orders** + **Payments** + **Returns** for later.
- **When to Use**: Modular monolith with mixed coupling levels; want fastest path to containers

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

**Pattern Recommendations Based on Your Architecture:**

- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extraction
  - **Why**: Without idempotency (APP-Q7 = 1/4), service extraction risks data inconsistency. The current `$db->beginTransaction()` approach in the order creation flow spans 5 tables across 3 domains (orders, inventory, payments) — these become distributed transactions after extraction. The Transactional Outbox pattern ensures events are published reliably during database writes.

- **Distributed Transactions**: Use [Saga Orchestration](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html) for cross-service transactions
  - **Why**: The order creation flow in `index.php` performs inventory check → order insert → inventory deduction → payment insert in a single transaction. After decomposition, this becomes a distributed transaction across Order, Inventory, and Payment services. Step Functions Saga Orchestration manages the sequence with compensating transactions on failure.

- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (hostname, path, or header-based)
  - **Why**: API Gateway provides routing, throttling, and auth without requiring service mesh infrastructure upfront. Route `/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, etc. to the new Fulfillment service while keeping everything else in the monolith.

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition
  - **Why**: Microservices amplify failure modes. The current `die()` on database failure and absence of any retry logic (APP-Q9 = 1/4) means resilience patterns must be in place before increasing system distribution. Every inter-service call must have circuit breaker + retry + timeout.

**Recommended Extraction Sequence (per customer EKS + Helm + GitOps preferences):**

1. **Users Service** (Week 2-4) — Extract user management and authentication to a dedicated service backed by Amazon Cognito. Create Helm chart. Deploy to EKS via ArgoCD. Lowest risk, lowest coupling.
2. **Fulfillment Service** (Week 4-8) — Extract the 7-step fulfillment workflow to a Step Functions-orchestrated service on EKS. Implement as Python/FastAPI for Bedrock integration potential. Create Helm chart.
3. **Inventory Service** (Week 8-12) — Extract product catalog and stock management. Own the `inventory` table in a dedicated Aurora MySQL instance. Publish `InventoryUpdated` events to EventBridge.
4. **Orders + Payments** (Week 12-20) — Extract together due to tight coupling. Implement Saga pattern for the order creation flow. Each owns its database. Use EventBridge for domain events.
5. **Returns Service** (Week 20-24) — Extract with anti-corruption layer to the Orders service. Implement approval workflow via Step Functions.

---

## Readiness Roadmap

### Phase 1 — Containerize & Automate (Days 1–30)

Low-effort, high-impact actions that establish the foundation for decomposition:

1. **Create GitHub Actions CI/CD Pipeline** — Set up a workflow that lints, builds the Docker image from the existing `Dockerfile`, pushes to ECR, and deploys to the target EKS cluster. This replaces the manual `deploy.sh` script immediately. *(Addresses INF-Q6, OPS-Q9)*

2. **Provision EKS Cluster with Terraform** — Define the EKS cluster (with Fargate profiles per customer preference), VPC networking, and supporting infrastructure in Terraform. Deploy ArgoCD for GitOps. Create the first Helm chart for the monolith container. *(Addresses INF-Q1, INF-Q5)*

3. **Write API Integration Tests** — Create a Postman/Newman test collection for all 20+ API endpoints in `index.php`. Run tests in the CI pipeline. This provides a safety net for all subsequent changes. *(Addresses OPS-Q10)*

4. **Add OpenTelemetry Instrumentation** — Add OpenTelemetry PHP auto-instrumentation to the monolith container. Deploy the OTel Collector as an EKS DaemonSet. Configure X-Ray as the backend. Establish tracing baseline before decomposition. *(Addresses OPS-Q1)*

5. **Migrate Secrets to Secrets Manager** — Move database credentials from environment variables / CloudFormation defaults to AWS Secrets Manager. Remove hardcoded credentials from `docker-compose.yml` and `index.php`. *(Addresses SEC-Q1)*

6. **Conduct EventStorming or domain modeling workshop** — Identify bounded contexts and service candidates by mapping the domains discovered in `index.php`: Orders, Inventory, Payments, Returns, Fulfillment, Warehouses, Users. *(Addresses APP-Q4)*

7. **Map current module dependencies and data coupling** — Analyze cross-domain foreign keys and shared table access patterns in `index.php` to understand extraction complexity. *(Addresses APP-Q4)*

### Phase 2 — Decompose & Decouple (Months 1–3)

Structural improvements that decompose the monolith into independent services:

1. **Extract Users Service** — Migrate authentication from PHP sessions to Amazon Cognito (JWT-based). Deploy as a dedicated service on EKS with its own Helm chart. This decouples identity from the monolith and enables service-to-service authentication. *(Addresses SEC-Q3, SEC-Q10, APP-Q12)*

2. **Extract Fulfillment Service (Strangler Fig)** — Implement the 7-step fulfillment workflow as a Step Functions state machine backed by an EKS service (Python/FastAPI). Use API Gateway path-based routing to redirect `/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, etc. to the new service while keeping other endpoints in the monolith. *(Addresses APP-Q4, APP-Q6, INF-Q3)*

3. **Introduce EventBridge for Domain Events** — Publish `OrderCreated`, `OrderValidated`, `WarehouseAssigned`, `OrderShipped` events from the monolith. New services subscribe to events instead of making synchronous calls. *(Addresses APP-Q3, INF-Q4)*

4. **Deploy API Gateway** — Set up Amazon API Gateway as the unified entry point. Configure throttling, request validation, and JWT authorization. Route requests to EKS services via ALB Ingress. *(Addresses INF-Q7, APP-Q8, SEC-Q5)*

5. **Implement Structured Logging & SLOs** — Add Monolog JSON logging with correlation IDs. Define SLOs for order placement and product listing. Configure CloudWatch alarms and dashboards. *(Addresses OPS-Q2, OPS-Q4, OPS-Q7, OPS-Q8)*

6. **Generate OpenAPI Specs** — Document all API endpoints for both the monolith and extracted services. Each service maintains its own OpenAPI spec. *(Addresses APP-Q2)*

7. **Upgrade RDS to Aurora MySQL** — Migrate from single-instance RDS MySQL to Aurora MySQL with read replicas and automatic failover per customer preference for `rds-aurora`. *(Addresses INF-Q2)*

### Phase 3 — Optimize & Scale (Months 3–6)

Advanced capabilities that complete the modernization and unlock AI potential:

1. **Continue Service Extraction** — Extract Inventory, Orders+Payments, and Returns services following the decomposition sequence. Each service gets its own database, Helm chart, and CI/CD pipeline. Implement Saga Orchestration for distributed transactions. *(Addresses APP-Q4, DATA-Q4, DATA-Q5, DATA-Q8)*

2. **Implement Progressive Delivery** — Configure Argo Rollouts for canary deployments with automatic analysis and rollback. Define progressive rollout steps with health check gates. *(Addresses OPS-Q5, OPS-Q9)*

3. **Add Resilience Patterns** — Implement circuit breakers, retries with exponential backoff, and timeouts for all inter-service calls. Use Istio/App Mesh or library-level resilience (Resilience4j, tenacity). *(Addresses APP-Q9)*

4. **Implement API Versioning** — Adopt URL path versioning (`/v1/`) for all microservice APIs. Configure API Gateway to route versioned requests. *(Addresses APP-Q11)*

5. **Implement Database Schema Management** — Adopt Flyway for each service's database. Version all schema changes. Generate ERD documentation. *(Addresses DATA-Q7)*

6. **Enable CloudTrail & Audit Logging** — Configure CloudTrail with log file validation and immutable S3 storage. Extend application-level audit logging to all domains. *(Addresses SEC-Q4)*

7. **Establish Observability Governance** — Define CODEOWNERS, assign per-service SLO ownership, create platform engineering team for centralized EKS observability. Implement service-level dashboards. *(Addresses OPS-Q12)*

8. **AI Foundation (if proceeding to agentic capabilities)** — Deploy Aurora PostgreSQL with pgvector. Integrate Bedrock for fulfillment decision-making. Build evaluation framework. *(Addresses APP-Q13, DATA-Q1, DATA-Q3, OPS-Q3)*

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `index.php` | Single PHP file (~2000+ lines) containing ALL business domains: Orders, Inventory, Payments, Returns, Users, Fulfillment, Warehouses. 20+ API endpoints. Direct PDO SQL queries. PHP session authentication. Schema definition inline. No tests, no resilience, no tracing. |
| 2 | `infrastructure/monolith-apprunner.yaml` | CloudFormation template: App Runner service, RDS MySQL 8.4.8 (db.t3.micro), VPC with private subnets, WAF (IP whitelisting), ECR repository, auto-scaling (min 1, max 3), IAM roles (CloudWatchLogsFullAccess). No API Gateway, no CloudTrail, no KMS keys. |
| 3 | `Dockerfile` | PHP 8.2 Apache container. Installs PDO MySQL extension. Copies `index.php` and `.htaccess`. Exposes port 80. No multi-stage build, no security scanning, no health check. |
| 4 | `docker-compose.yml` | Local development: self-managed MySQL 8.0 + PHP monolith. Hardcoded credentials (rootpassword, ecommerce_pass). Health checks configured. Volume mount for live reload. |
| 5 | `deploy.sh` | Manual deployment script: `docker-compose build` + `docker-compose up -d`. No CI/CD, no rollback, no progressive delivery. Includes basic health check via curl. |
| 6 | `.htaccess` | Apache rewrite rules routing all requests to `index.php`. Confirms single-entry-point monolith architecture. |
| 7 | `.gitignore` | Excludes database files, logs, OS files, and IDE configs. No test output, no build artifacts, no coverage reports referenced — confirms absence of testing. |
| 8 | `index.php` — `init_db()` | 9 CREATE TABLE statements defining the complete schema: orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users. Foreign keys cross domains. ALTER TABLE try/catch for migrations. |
| 9 | `index.php` — `get_db()` | Database connection with environment variable fallbacks. `die()` on failure — no retry, no graceful degradation. Single connection function shared by all domains. |
| 10 | `index.php` — `/api/orders POST` | Order creation: single transaction spanning inventory check, order insert, item inserts, inventory deduction, payment processing, and status update. Peak coupling across 3 domains. |
| 11 | `index.php` — `/api/admin/approve-return` | Return approval: crosses 5 domains (returns, orders, order_items, inventory, payments) in a single transaction. Highest coupling point in the monolith. |
| 12 | `index.php` — Fulfillment endpoints | 7 sequential endpoints (/validate, /assign-warehouse, /pick, /pack, /quality-check, /ship, /deliver) implementing manual fulfillment workflow. No orchestration engine. |
| 13 | `index.php` — `/api/orders/{id}/validation-data` | Fraud/validation context endpoint with risk scoring, customer history analysis, and recommendation logic. Decision-support data currently rule-based — AI candidate. |
| 14 | `index.php` — `/api/warehouses/assignment-options` | Warehouse comparison with distance calculation (Haversine), load scoring, and recommendation. Rule-based optimization — AI candidate. |
| 15 | `index.php` — `/api/carriers/shipping-options` | Carrier comparison with cost calculation, delivery estimates, and value scoring with configurable priorities. Rule-based — AI candidate. |
| 16 | `infrastructure/monolith-apprunner.yaml` — `DBInstance` | RDS MySQL: engine 8.4.8, db.t3.micro, 20GB gp3, encrypted, private subnets, 7-day backups. No Aurora, no Multi-AZ, no read replicas. |
| 17 | `infrastructure/monolith-apprunner.yaml` — `WebACL` | WAF configuration: block all traffic by default, allow only specific IP via IPSet. No rate limiting rules. No SQL injection or XSS protection. |
| 18 | `infrastructure/monolith-apprunner.yaml` — `AppRunnerInstanceRole` | IAM role with `CloudWatchLogsFullAccess` managed policy — overly permissive. |
| 19 | `infrastructure/monolith-apprunner.yaml` — `AutoScalingConfiguration` | App Runner auto-scaling: min 1, max 3, max concurrency 100. Basic scaling configuration. |
| 20 | `index.php` — Login/session handling | PHP `session_start()`, bcrypt password hashing, session-based auth checks. No JWT, no OAuth2, no Cognito. Internal users table. |
