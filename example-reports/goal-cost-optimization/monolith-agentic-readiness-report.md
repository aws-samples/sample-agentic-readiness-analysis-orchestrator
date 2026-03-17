# Agentic Readiness Assessment Report
**Target**: ./monolith
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: cost-optimization
**Goal Context**: Reducing licensing costs and migrating to managed and open-source services
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
6. Readiness Roadmap
   - Phase 1 — License & Quick Savings (Days 1–30)
   - Phase 2 — Managed Service Migration (Months 1–3)
   - Phase 3 — Optimization & Governance (Months 3–6)
7. Recommended Self-Paced Learning Materials
8. Appendix: Evidence Index

---

## Executive Summary

This PHP monolithic e-commerce application scores **1.5 / 4.0** overall, reflecting a codebase with foundational managed-service choices already in place but significant gaps in operational maturity, application architecture, and security that directly increase operational costs. The strongest area is Infrastructure & Platform (2.1/4.0): production compute runs on AWS App Runner (managed, auto-scaling) and the database is RDS MySQL (managed, encrypted). However, the application is a single tightly-coupled `index.php` monolith with zero CI/CD automation, no observability, no structured logging, and no testing — meaning operational incidents are expensive to diagnose and recover from. The most impactful cost-optimization opportunities are: (1) migrating RDS MySQL to Aurora MySQL or Aurora PostgreSQL for better cost/performance ratio with Serverless v2 auto-scaling, (2) establishing CI/CD automation to reduce manual deployment overhead, and (3) implementing observability to reduce mean-time-to-resolution and associated labor costs.

### Overall Score: 1.5 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.1 / 4.0 | 🟠 |
| Application Architecture | 1.3 / 4.0 | 🟠 |
| Data Foundations | 1.5 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | 🟠 |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

### 1. No CI/CD Automation (INF-Q6: 1/4) ❌
**Why it matters for cost optimization**: Manual deployments via `deploy.sh` (docker-compose up) waste engineering hours on every release and increase the risk of costly production incidents from human error. Automating the pipeline with AWS CodePipeline or GitHub Actions reduces per-deployment cost to near zero and enables faster, safer releases.
**First step**: Create a GitHub Actions workflow or AWS CodePipeline that builds the Docker image, pushes to ECR, and triggers an App Runner deployment on merge to main.

### 2. Zero Observability (OPS-Q1: 1/4, OPS-Q2: 1/4) ❌
**Why it matters for cost optimization**: Without distributed tracing or structured logging, every production issue requires expensive manual investigation. The application uses `ini_set('log_errors', '1')` — basic PHP error logging with no JSON formatting, no correlation IDs, and no CloudWatch integration. Mean-time-to-resolution (MTTR) for incidents is high, driving up labor costs.
**First step**: Add a structured logging library (e.g., Monolog with JSON formatter) and enable AWS X-Ray or OpenTelemetry tracing in the App Runner service.

### 3. No Deployment Strategy or Rollback (OPS-Q9: 1/4, OPS-Q5: 1/4) ❌
**Why it matters for cost optimization**: A failed deployment with no rollback capability means extended downtime and lost revenue. The current `deploy.sh` runs `docker-compose up -d` with no health checks, no canary, and no rollback. App Runner supports automatic rollbacks — this feature is not configured.
**First step**: Configure App Runner's automatic rollback on failed deployments and implement blue/green or canary deployment via CloudFormation deployment preferences.

### 4. No Testing (OPS-Q10: 1/4) ❌
**Why it matters for cost optimization**: Zero test coverage means every code change risks introducing regressions that cost money to find and fix in production. No test files, no test directories, and no test frameworks exist in the repository.
**First step**: Add PHPUnit with integration tests for the critical order-creation and payment-processing API endpoints. Run tests in CI before deployment.

### 5. Tightly-Coupled Monolith (APP-Q4: 1/4) ❌
**Why it matters for cost optimization**: The entire application is a single `index.php` file with all 6 business domains (orders, inventory, payments, returns, users, fulfillment) tightly coupled and sharing one MySQL database. This prevents independent scaling — over-provisioning the entire application to handle spikes in one domain wastes compute resources. It also makes any change risky and expensive to test.
**First step**: Identify bounded contexts (orders, inventory, payments, returns, users, fulfillment) and begin extracting the most independent domain as a separate service behind an API Gateway.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: Production compute uses AWS App Runner (`AWS::AppRunner::Service` in `infrastructure/monolith-apprunner.yaml`), a fully managed container service comparable to Fargate. The `Dockerfile` defines a PHP 8.2 Apache image. App Runner handles load balancing, TLS termination, and auto-scaling automatically. Local development uses docker-compose.
- **Gap**: App Runner is managed but offers less orchestration flexibility than ECS/EKS. No multi-service orchestration capability since this is a single monolith deployment.
- **Recommendation**: App Runner is a cost-effective choice for this single-service workload. If service decomposition occurs in the future, evaluate migrating to ECS on Fargate for richer orchestration and service-mesh capabilities.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: Production database is RDS MySQL (`AWS::RDS::DBInstance` in `infrastructure/monolith-apprunner.yaml`) — engine `mysql`, version `8.4.8`, instance class `db.t3.micro`, 20 GB gp3 storage, encrypted at rest (`StorageEncrypted: true`), 7-day backup retention. Local development uses `mysql:8.0` via docker-compose. RDS is in private subnets with security group restricting access to App Runner only.
- **Gap**: Single-AZ deployment with `db.t3.micro` instance — no Multi-AZ failover, no read replicas. This is a cost risk: a single-AZ failure causes downtime and potential data loss beyond the RPO window.
- **Recommendation**: Migrate to Aurora MySQL or Aurora PostgreSQL Serverless v2 for cost-optimized auto-scaling. Aurora Serverless v2 scales capacity in fine-grained increments (0.5 ACU) so you pay only for actual usage, eliminating the need to right-size a fixed instance class. Aurora also provides built-in Multi-AZ with no additional configuration cost.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service found. The fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) is implemented as sequential manual HTTP API calls in `index.php`. Each step is a separate endpoint (e.g., `/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`) with no state machine or orchestration layer.
- **Gap**: No Step Functions, Temporal, or any workflow engine. Workflow state is tracked only by the `status` column in the `orders` table.
- **Recommendation**: Implement AWS Step Functions for the fulfillment workflow. Step Functions Standard Workflows cost $0.025 per 1,000 state transitions — far cheaper than manual human coordination of the 7-step fulfillment process.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or any messaging service detected. All operations in `index.php` are synchronous request-response. Order creation, payment processing, inventory updates, and return processing all happen in a single synchronous database transaction.
- **Gap**: No async messaging infrastructure. Every operation blocks the HTTP request until completion, tying up App Runner instances unnecessarily.
- **Recommendation**: Introduce SQS for decoupling long-running operations (return processing, fulfillment steps). SQS is serverless and costs $0.40 per million requests — minimal cost to significantly improve reliability and reduce instance utilization.

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` is a comprehensive CloudFormation template covering: VPC, 2 private subnets, DB subnet group, security groups, RDS MySQL, VPC Connector, ECR Repository, IAM roles, App Runner Service, Auto-scaling configuration, WAF Web ACL, and IP Set. Parameterized with sensible defaults.
- **Gap**: No separate environment definitions (staging vs production). No CloudFormation StackSets or CDK for multi-environment management. The `deploy.sh` script uses docker-compose, not CloudFormation, for local deployment.
- **Recommendation**: Add a staging environment definition using CloudFormation parameters or a separate parameter file. Consider migrating to AWS CDK for type-safe IaC that enables environment-specific configurations with less duplication.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`. The only deployment mechanism is `deploy.sh`, which runs `docker-compose build` and `docker-compose up -d`. The CloudFormation `Outputs.DeploymentInstructions` describes a manual 6-step process: build image → authenticate ECR → tag → push → update stack.
- **Gap**: Entirely manual deployment process. No automated testing, building, or deployment pipeline.
- **Recommendation**: Create a GitHub Actions workflow with stages: lint → test → build Docker image → push to ECR → deploy via CloudFormation update. This eliminates manual deployment labor costs and reduces human error risk.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: App Runner provides a built-in HTTPS endpoint with automatic TLS. WAF Web ACL (`AWS::WAFv2::WebACL`) is configured with IP whitelisting via an IP Set, blocking all traffic not from the allowed IP range. WAF metrics are enabled (`CloudWatchMetricsEnabled: true`).
- **Gap**: No API Gateway with throttling, request validation, or per-client usage plans. WAF provides IP-based access control but not rate limiting or request schema validation. No usage plans or API keys for external consumers.
- **Recommendation**: For cost optimization, the current WAF + App Runner setup is sufficient for a single-client application. If external API consumers are added, implement API Gateway with usage plans to enforce quotas and prevent abuse-driven cost overruns.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming service detected in IaC or application code. No event-driven data patterns. All data flows are synchronous database writes.
- **Gap**: No streaming infrastructure for real-time event processing or analytics.
- **Recommendation**: Not an immediate priority for cost optimization. Evaluate Kinesis Data Streams or EventBridge only when event-driven architecture is needed for service decomposition.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: VPC (`10.0.0.0/16`) with two private subnets (`10.0.1.0/24`, `10.0.2.0/24`) for RDS. DB security group restricts MySQL port 3306 to traffic only from the App Runner security group (`SourceSecurityGroupId: !Ref AppRunnerSecurityGroup`). RDS is not publicly accessible (`PubliclyAccessible: false`). App Runner connects to VPC via VPC Connector.
- **Gap**: No NACLs explicitly defined (uses default allow-all). No public subnet/NAT Gateway for outbound internet from VPC (may limit App Runner's ability to reach external services if configured with VPC egress). Security groups are properly restrictive.
- **Recommendation**: Network security is adequate for the current architecture. Add NACLs for defense-in-depth if required by compliance. No immediate cost optimization action needed.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: App Runner Auto-scaling configured (`AWS::AppRunner::AutoScalingConfiguration`) with `MinSize: 1`, `MaxSize: 3`, and `MaxConcurrency: 100`. Parameters allow customization of min/max at deployment time.
- **Gap**: No database auto-scaling. RDS `db.t3.micro` is a fixed instance class with no auto-scaling policy. No scaling alarms or policies based on CPU/memory utilization.
- **Recommendation**: Migrate to Aurora Serverless v2 to gain automatic database scaling (0.5 to 128 ACUs). This directly reduces cost: you pay only for the capacity used rather than provisioning for peak load on a fixed instance.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: PHP 8.2 is the sole language, as defined in the `Dockerfile` (`FROM php:8.2-apache`). The application uses PDO for MySQL access, PHP sessions for authentication, and built-in `json_encode()` for API responses. No `composer.json` or dependency manifest found — all functionality is implemented with PHP built-in functions.
- **Gap**: PHP has a limited AI/agent framework ecosystem compared to Python or TypeScript. No major agent frameworks (LangChain, Strands, CrewAI) have PHP SDKs. However, PHP 8.2 is a modern, supported version with good performance.
- **Recommendation**: For cost optimization, PHP 8.2 is adequate. If AI agent integration becomes a priority, consider adding a Python or Node.js sidecar service for agent orchestration while keeping the PHP monolith as the backend API.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI, Swagger, or any API specification files found in the repository. No `openapi.yaml`, `swagger.json`, or API documentation directory. No PHP annotations for API documentation (e.g., no swagger-php or OpenAPI annotations). API routes are defined via `preg_match` and `if` statements in `index.php`.
- **Gap**: Zero API documentation. The only way to understand the API surface is by reading the source code. This increases onboarding cost and makes external integration expensive.
- **Recommendation**: Generate an OpenAPI 3.0 spec documenting all 25+ API endpoints. This is a low-cost investment that significantly reduces integration labor costs and enables automated client SDK generation.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous HTTP request-response within a single PHP process. Order creation (`POST /api/orders`) performs inventory check, order insertion, item insertion, inventory update, payment insertion, and status update all in a single synchronous database transaction (`$db->beginTransaction()` / `$db->commit()`). No message queues, no event publishing, no async patterns.
- **Gap**: 100% synchronous. Every request blocks the PHP process and App Runner instance until the entire transaction completes. Return processing is described as a "manual 24-48 hour process" but still initiated synchronously.
- **Recommendation**: Introduce SQS for decoupling non-critical operations (return processing, fulfillment notifications). This reduces App Runner instance hold time and improves cost efficiency.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: Single `index.php` file (~1500 lines including HTML/JS) contains ALL business domains: orders, inventory, payments, returns, users, fulfillment, and warehouse management. Nine database tables share foreign keys across domains (e.g., `order_items.order_id → orders.id`, `payments.order_id → orders.id`, `returns.order_id → orders.id`). The `get_db()` function returns a single shared PDO connection used by all domains. There are no module boundaries, no separate classes, no namespaces.
- **Gap**: Tightly-coupled monolith with no clear module boundaries. Shared mutable state everywhere. All domains share the same MySQL database with cross-domain foreign keys. Any change to any domain risks breaking all other domains.
- **Recommendation**: Begin identifying bounded contexts for future decomposition. For cost optimization, the monolith itself is not the primary cost driver — the lack of independent scaling is. Consider containerizing domain-specific workloads on Fargate with weighted scaling.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API endpoints return structured JSON responses. The API section of `index.php` sets `header('Content-Type: application/json')` at the top of the API routing block. All responses use `json_encode()` with consistent structure (e.g., `{'products': [...]}`, `{'success': true, 'order_id': '...'}`, `{'error': '...'}` for errors). HTTP status codes are used correctly (200, 400, 401, 403, 404, 500).
- **Gap**: None. JSON responses are well-structured and consistent.
- **Recommendation**: No action needed. This is agent-ready.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: All workflow logic is hardcoded as sequential if/else URL routing in `index.php`. The fulfillment workflow has 7 explicit steps, each implemented as a separate endpoint: `/api/orders/{id}/validate` → `/api/orders/{id}/assign-warehouse` → `/api/orders/{id}/pick` → `/api/orders/{id}/pack` → `/api/orders/{id}/quality-check` → `/api/orders/{id}/ship` → `/api/orders/{id}/deliver`. No orchestration — each step must be triggered manually by an admin.
- **Gap**: No workflow orchestration service. The fulfillment workflow state is tracked only by the `status` column in the `orders` table. There is no mechanism to automatically advance through steps, handle failures, or implement retries.
- **Recommendation**: Implement AWS Step Functions to orchestrate the fulfillment workflow. This reduces manual labor cost and provides built-in error handling, retries, and state persistence.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency mechanisms detected. Order IDs are generated with `uniqid('order-')`, which is not idempotent — calling the same endpoint twice creates two different orders. Payment IDs use `uniqid('pay-')`. No idempotency key headers, no deduplication logic, no upsert patterns. The return approval endpoint has no guard against double-processing.
- **Gap**: No idempotency on any write endpoint. Duplicate submissions will create duplicate records and potentially double-charge or double-refund.
- **Recommendation**: Add idempotency keys to the order creation and payment processing endpoints. This prevents costly duplicate transactions and is a prerequisite for reliable async processing.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. WAF (`infrastructure/monolith-apprunner.yaml`) provides IP whitelisting (allow/block by IP) but no rate-based rules. No application-level rate limiting middleware in `index.php`. No `express-rate-limit` equivalent for PHP. App Runner's `MaxConcurrency: 100` controls concurrent requests per instance but is not a rate limit.
- **Gap**: No rate limiting. A compromised or misconfigured client could send unlimited requests, driving up App Runner instance costs.
- **Recommendation**: Add a WAF rate-based rule (e.g., 2,000 requests per 5 minutes per IP) to prevent abuse-driven cost overruns. This is a low-effort, high-impact cost protection measure.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No resilience patterns implemented. The `get_db()` function in `index.php` uses `die("Database connection failed: " . $e->getMessage())` on connection failure — killing the process with an unstructured error message. No circuit breakers, no retries with exponential backoff, no timeout configurations. No try/catch around external service calls (all calls are to the local database).
- **Gap**: Zero resilience patterns. A database connection failure crashes the entire request with `die()`, potentially leaking error details.
- **Recommendation**: Replace `die()` with proper error handling that returns a JSON error response. Add connection retry logic with exponential backoff. These changes are low-cost and reduce incident-driven operational expenses.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: No async job processing. All operations are synchronous within the HTTP request lifecycle. The return processing workflow is documented as requiring "manual CS review (24-48 hours)" but the submission itself is synchronous. No background job frameworks (no Celery, no Bull, no PHP-based job queues like Laravel Queue).
- **Gap**: No mechanism for handling operations that exceed typical HTTP request timeouts. The fulfillment workflow's 7-step process is entirely human-driven with no automation.
- **Recommendation**: Introduce SQS-based async processing for return approvals and fulfillment steps. This reduces manual labor costs and improves throughput.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning. All endpoints are at `/api/` with no version prefix (e.g., `/api/products`, `/api/orders`, `/api/returns`). No Accept-Version headers. No changelog or version documentation.
- **Gap**: No versioning strategy. Any breaking API change will affect all consumers simultaneously, increasing the risk and cost of API evolution.
- **Recommendation**: Adopt URL-path versioning (e.g., `/api/v1/`) as a low-effort first step. This enables backward-compatible API evolution and reduces the blast radius of changes.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith with no inter-service communication. The database host is configured via the `DB_HOST` environment variable (hardcoded default: `'mysql'` in `index.php`, overridden by CloudFormation's `!GetAtt DBInstance.Endpoint.Address`). No AWS Service Discovery, App Mesh, or Consul.
- **Gap**: No service discovery mechanism. As a monolith, inter-service discovery is not immediately needed, but there is no foundation for future decomposition.
- **Recommendation**: No immediate action needed for cost optimization. When services are extracted, use AWS Cloud Map for service discovery.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent frameworks detected. No boto3, no LangChain, no Strands Agents, no OpenAI SDK, no Anthropic SDK, no Spring AI, no MCP imports. The application has no AI capabilities whatsoever. PHP has very limited AI framework support.
- **Gap**: No AI integration. The application is entirely traditional request-response with manual decision-making at every step.
- **Recommendation**: Not a priority for cost optimization. When AI capabilities are needed, add a Python or Node.js microservice for agent orchestration that calls the monolith's existing JSON APIs.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database present in the repository. No OpenSearch, pgvector, Pinecone, Weaviate, Chroma, or Bedrock Knowledge Bases detected in IaC or application code.
- **Gap**: No vector search capability for semantic queries over product catalog or customer interactions.
- **Recommendation**: Not a priority for cost optimization. When AI/RAG capabilities are needed, consider Amazon OpenSearch Service with k-NN plugin or Aurora PostgreSQL with pgvector extension (aligns with preference for managed open-source services).

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists to evaluate management of.
- **Gap**: N/A — no vector DB to manage.
- **Recommendation**: When a vector DB is needed, deploy a managed service (OpenSearch Service or Aurora PostgreSQL with pgvector) to avoid self-managed operational costs.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline. No embedding model calls, no document chunking, no similarity search, no Bedrock Knowledge Base integration. The application has no AI capabilities.
- **Gap**: No semantic search or document retrieval capability.
- **Recommendation**: Not a priority for cost optimization. Future consideration when AI use cases are pursued.

#### DATA-Q4: Data Source Sprawl
- **Score**: 2/4 🟠
- **Finding**: Single MySQL database (`ecommerce`) with 9 tables: `orders`, `order_items`, `inventory`, `payments`, `returns`, `interactions`, `order_status_history`, `warehouses`, `users`. All accessed via a single `get_db()` PDO connection in `index.php`. Only one data source, but no unified data access layer — raw SQL queries are scattered across 30+ locations in the file.
- **Gap**: Single data source (good), but no abstraction layer (bad). The tight coupling between all 9 tables via foreign keys means any schema change affects the entire application. Cross-domain queries are common (e.g., joining `returns` with `orders` with `order_items` with `inventory` in the return approval flow).
- **Recommendation**: Create a data access layer with repository classes per domain. This is a prerequisite for future database decomposition and reduces the risk and cost of schema changes.

#### DATA-Q5: Data Access Pattern
- **Score**: 1/4 ❌
- **Finding**: Direct PDO database queries scattered throughout `index.php`. The `get_db()` function returns a raw PDO connection, and every API endpoint constructs and executes SQL directly: `$db->prepare('SELECT * FROM orders WHERE id = ?')`. No repository pattern, no ORM, no data access layer. Over 50 distinct SQL statements are embedded directly in API handler code.
- **Gap**: Business logic and data access are completely interleaved. No separation of concerns. This makes database migration (e.g., MySQL to Aurora PostgreSQL) extremely expensive because every SQL statement must be individually reviewed and potentially modified.
- **Recommendation**: Refactor to a repository pattern where each domain (orders, inventory, payments, etc.) has a dedicated data access class. This is a cost-reduction prerequisite: it centralizes SQL statements, making future database engine migration a single-class change per domain instead of a scattered multi-hundred-line change.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing capabilities. No Textract, Tika, or any document processing. Product images are referenced by URL (`image_url` column in `inventory` table) but no image storage or processing infrastructure exists.
- **Gap**: No unstructured data management.
- **Recommendation**: Not a priority for cost optimization. If document processing is needed, use S3 for storage and Textract for parsing.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: Database schema is defined inline in PHP code via `CREATE TABLE IF NOT EXISTS` statements in the `init_db()` function in `index.php`. Schema changes are applied by adding `ALTER TABLE` statements wrapped in try/catch blocks (e.g., adding `warehouse_location`, `weight_lbs`, `dimensions` columns to the `inventory` table). No migration tool (Flyway, Liquibase, Alembic, Phinx). No JSON Schema files. No schema documentation.
- **Gap**: Schema management is ad-hoc and fragile. The `CREATE TABLE IF NOT EXISTS` pattern cannot handle column additions or modifications — those require separate `ALTER TABLE` statements. No version history or rollback capability for schema changes.
- **Recommendation**: Adopt a PHP migration tool (Phinx or Doctrine Migrations) for versioned, reversible schema changes. This reduces the cost and risk of database evolution and is essential for future Aurora migration.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. The `get_db()` function returns a raw PDO connection. All 50+ SQL queries are direct prepared statements scattered across the monolithic `index.php`. Example: order creation executes 6 separate SQL statements in sequence, payment processing executes 2, return approval executes 5.
- **Gap**: Complete absence of a data access abstraction. Every database interaction is a raw SQL call. This makes the application extremely rigid and expensive to modify.
- **Recommendation**: Implement a repository pattern with a class per aggregate root (OrderRepository, InventoryRepository, PaymentRepository, etc.). This centralizes data access, reduces duplication, and makes database engine migration feasible.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist in the application. No vector store, no embedding model integration, no indexing pipeline.
- **Gap**: N/A — no embeddings to keep fresh.
- **Recommendation**: Not applicable until a vector database and RAG pipeline are implemented.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 3/4 🟡
- **Finding**: RDS MySQL engine version is explicitly pinned to `8.4.8` in `infrastructure/monolith-apprunner.yaml` (`EngineVersion: '8.4.8'`). MySQL 8.4 is the current LTS release with active support. `AutoMinorVersionUpgrade: true` is enabled for automatic patch updates. Local development uses `mysql:8.0` via `docker-compose.yml` — a different major version than production.
- **Gap**: Version mismatch between development (8.0) and production (8.4.8) environments could cause subtle SQL compatibility issues. No formal EOL tracking or version governance process.
- **Recommendation**: Align docker-compose MySQL version to 8.4 to match production. When migrating to Aurora, pin to Aurora MySQL 3.x (MySQL 8.0-compatible) or Aurora PostgreSQL 16.x for long-term support and cost optimization via Serverless v2.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, functions, or proprietary SQL constructs detected. All 9 `CREATE TABLE` statements in `index.php` use standard SQL with InnoDB engine. All business logic is in the PHP application layer. SQL statements use only standard DML (SELECT, INSERT, UPDATE, DELETE) with prepared statements. No T-SQL, PL/SQL, or MySQL-specific stored routines.
- **Gap**: None. The absence of stored procedures and proprietary SQL significantly reduces the cost and complexity of database engine migration.
- **Recommendation**: No action needed. This is a positive finding for cost optimization — migrating from MySQL to Aurora MySQL or Aurora PostgreSQL will require minimal SQL translation effort since all logic is in the application layer.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are passed as environment variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`) with hardcoded defaults in `index.php`: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. CloudFormation uses `NoEcho: true` parameters for `DBUsername` and `DBPassword` but passes them directly as runtime environment variables to App Runner — not via Secrets Manager. `docker-compose.yml` has hardcoded credentials: `MYSQL_PASSWORD: ecommerce_pass`, `MYSQL_ROOT_PASSWORD: rootpassword`.
- **Gap**: No AWS Secrets Manager, no Vault, no encrypted secret store. Credentials are in plaintext in docker-compose.yml and as default values in PHP code. The CloudFormation default password `ChangeMe123!` is visible in the template.
- **Recommendation**: Store database credentials in AWS Secrets Manager and configure App Runner to retrieve them at runtime. Remove hardcoded defaults from `index.php`. This eliminates a security risk that could lead to costly data breaches.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: CloudFormation defines two separate IAM roles: `AppRunnerInstanceRole` (for the running service, assumes `tasks.apprunner.amazonaws.com`) and `AppRunnerAccessRole` (for ECR image pulls, assumes `build.apprunner.amazonaws.com`). However, `AppRunnerInstanceRole` uses the `CloudWatchLogsFullAccess` managed policy, which grants `logs:*` on all resources — a wildcard permission.
- **Gap**: Overly broad `CloudWatchLogsFullAccess` managed policy. The instance role should only have permissions to write to specific log groups, not full access to all CloudWatch Logs operations.
- **Recommendation**: Replace `CloudWatchLogsFullAccess` with a custom policy scoped to `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` on the specific App Runner log group ARN. This is a low-cost security improvement.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Authentication uses PHP sessions (`session_start()` in `index.php`). User identity is stored in `$_SESSION['user']` after login. API endpoints check `if (!isset($_SESSION['user']))` for authentication. No JWT, no OAuth2, no token exchange. User context is available only within the single monolith — no mechanism to propagate identity to other services.
- **Gap**: Session-based auth cannot propagate across services. No token-based identity flow.
- **Recommendation**: Not an immediate cost optimization priority. When services are decomposed, implement Amazon Cognito for centralized identity with JWT tokens that propagate across services.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in the CloudFormation template. No application-level audit logging. The `order_status_history` table tracks order status changes with `changed_by` field, but this is operational logging, not security audit logging. No log file validation, no immutable storage.
- **Gap**: No security audit trail. Cannot determine who accessed what data or made what changes.
- **Recommendation**: Enable CloudTrail in the CloudFormation template. Add it as a resource with log file validation and S3 bucket with object lock. Cost is minimal (~$2/month for management events) but provides essential compliance and incident investigation capability.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: WAF Web ACL (`infrastructure/monolith-apprunner.yaml`) is configured with IP whitelisting only — a single `AllowSpecificIP` rule that allows traffic from a specific IP range and blocks everything else. No rate-based rules in the WAF configuration. No application-level rate limiting in `index.php`.
- **Gap**: No rate limiting at any layer. While IP whitelisting restricts access, an authorized client can send unlimited requests.
- **Recommendation**: Add a WAF rate-based rule to limit requests per IP. This prevents accidental or intentional denial-of-service that would scale up App Runner instances and increase costs.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction in logging or error responses. Customer names and emails are returned in API responses (e.g., the validation-data endpoint returns `customer.name`, `customer.email`). Error logging via `ini_set('log_errors', '1')` has no PII filtering. The `die("Database connection failed: " . $e->getMessage())` in `get_db()` could leak database connection details.
- **Gap**: No PII detection, masking, or redaction. Customer data flows freely through logs and error messages.
- **Recommendation**: Add PII redaction to error logging. Mask email addresses and customer names in log output. This reduces the risk and cost of data breach compliance violations.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: Manual return approval exists via the `POST /api/admin/approve-return` endpoint in `index.php`. This endpoint requires admin role (`$_SESSION['user']['role'] !== 'admin'`), processes the refund, restores inventory, and updates order status. The fulfillment workflow also has manual approval at each step (validate, assign warehouse, pick, pack, QC, ship).
- **Gap**: Human approval exists but is not formalized as a structured workflow. No Step Functions with `waitForTaskToken`, no approval Lambda patterns. The approval process is a simple API call with no audit trail beyond the `order_status_history` table.
- **Recommendation**: Formalize approval workflows with Step Functions human approval tasks. This provides audit trails and timeout handling while reducing the cost of missed or delayed approvals.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: RDS has `StorageEncrypted: true` in `infrastructure/monolith-apprunner.yaml` (uses AWS-managed key by default — no `KmsKeyId` specified). ECR has `EncryptionConfiguration.EncryptionType: AES256`. No customer-managed KMS keys defined anywhere in the template.
- **Gap**: Encryption at rest is enabled but uses AWS-managed keys, not customer-managed KMS keys. This limits key rotation control and audit capability.
- **Recommendation**: For cost optimization, AWS-managed encryption is adequate and cheaper than customer-managed KMS keys ($1/month per key + $0.03/10,000 API calls). Only upgrade to CMK if compliance requirements demand it.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: All API endpoints require authentication via session check: `if (!isset($_SESSION['user']))` returns HTTP 401. Admin endpoints additionally check `$_SESSION['user']['role'] !== 'admin'` and return HTTP 403. Login uses `password_verify()` with bcrypt-hashed passwords (`PASSWORD_BCRYPT`). Passwords are not stored in sessions (`unset($user['password'])`).
- **Gap**: Session-based authentication only. No OAuth2, no JWT, no API keys for programmatic access. Sessions are tied to cookies and cannot be used for service-to-service or agent-to-API authentication.
- **Recommendation**: For cost optimization, session-based auth is adequate for the current monolith. When external API consumers or agents are added, implement Cognito-backed JWT authentication.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider. Users are stored in a local MySQL `users` table with bcrypt passwords. No Cognito, no Okta, no OIDC/SAML federation. No SSO configuration. User management is done via admin API endpoints (`POST /api/admin/users`, `PUT /api/admin/users/{id}`, `DELETE /api/admin/users/{id}`).
- **Gap**: Local user store with no centralized identity management. This is a security risk (no MFA, no password policies, no session expiration beyond PHP defaults) and an operational cost (manual user management).
- **Recommendation**: Migrate to Amazon Cognito for centralized identity management. Cognito's free tier covers 50,000 MAU — likely more than sufficient. This eliminates the operational cost of managing a custom auth system and adds MFA, password policies, and social login at no additional cost.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing of any kind. No AWS X-Ray, no OpenTelemetry, no Jaeger, no Zipkin. No trace ID propagation in HTTP headers. No instrumentation wrappers. No tracing SDK in the codebase (no `composer.json` to check for dependencies, but no tracing imports in `index.php`).
- **Gap**: Zero observability into request flow. Every production issue requires manual code reading and log parsing to diagnose. This directly increases operational labor costs.
- **Recommendation**: Enable AWS X-Ray tracing for App Runner (supported natively). Add the X-Ray SDK for PHP or OpenTelemetry PHP auto-instrumentation. This provides request-level visibility at minimal cost ($5.00 per million traces recorded).

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: PHP error logging is configured with `ini_set('display_errors', '0')` and `ini_set('log_errors', '1')` in `index.php`. This sends PHP errors to the default error log (Apache error_log, which App Runner forwards to CloudWatch). No JSON log formatter, no structured logging library (no Monolog), no correlation IDs, no request context in log entries.
- **Gap**: Unstructured plain-text logs with no correlation IDs. Cannot trace a request across log entries. CloudWatch Log Insights queries are limited without JSON-structured logs.
- **Recommendation**: Add Monolog with a JSON formatter and inject a correlation ID (e.g., UUID) into every request. Forward structured logs to CloudWatch. This dramatically reduces the time (and cost) to diagnose production issues.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no test datasets, no scoring scripts, no LLM-as-judge patterns, no golden datasets. The application has no AI capabilities, so agent evaluation is not applicable in its current state.
- **Gap**: No automated evaluation infrastructure.
- **Recommendation**: Not a priority for cost optimization. Implement when AI/agent capabilities are added.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found in any file. No CloudWatch alarms in the CloudFormation template. No latency or error rate monitoring. No dashboards. WAF has `CloudWatchMetricsEnabled: true` for request counting, but no alarms or SLO targets are defined based on these metrics.
- **Gap**: No SLOs, no alarms, no proactive monitoring. Issues are only discovered when users report them, which is expensive (customer churn, reputation damage, reactive engineering time).
- **Recommendation**: Define SLOs for p99 API latency (<500ms) and error rate (<1%). Create CloudWatch alarms that trigger on SLO breaches. Cost is minimal (CloudWatch alarms: $0.10/alarm/month) but provides early warning that prevents expensive outages.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback mechanism for code or configuration. `deploy.sh` runs `docker-compose build` and `docker-compose up -d` with no rollback capability. CloudFormation has `DeletionPolicy: Snapshot` and `UpdateReplacePolicy: Snapshot` on the RDS instance (preserving data on deletion/replacement), but no code deployment rollback. App Runner supports automatic rollback but it is not configured in the template.
- **Gap**: No ability to quickly revert a bad deployment. A failed deployment requires manual intervention to rebuild and redeploy the previous version.
- **Recommendation**: Configure App Runner's automatic rollback on failed health checks. Add a deployment script that tags Docker images with version numbers so previous versions can be quickly redeployed.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token tracking, no cost attribution, no usage metrics.
- **Gap**: No LLM cost tracking infrastructure. Not currently needed.
- **Recommendation**: Not a priority for cost optimization. Implement when AI/LLM services are integrated.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics published. No `cloudwatch.put_metric_data`, no custom dashboards, no business KPI tracking. The application tracks order status in the database (`order_status_history` table) but does not publish these as operational metrics.
- **Gap**: No visibility into business outcomes (order completion rate, return rate, fulfillment time, revenue). Without business metrics, cost optimization decisions are uninformed.
- **Recommendation**: Publish key business metrics to CloudWatch: orders per hour, average fulfillment time, return rate, revenue per day. Use CloudWatch dashboards for real-time visibility. This enables data-driven cost optimization decisions.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection, no error rate alarms, no latency monitoring, no alerting integration. No PagerDuty, OpsGenie, or SNS topic for alerts. WAF metrics are collected but no alarms are defined on them.
- **Gap**: No proactive alerting. Issues are only discovered reactively.
- **Recommendation**: Enable CloudWatch anomaly detection on App Runner metrics (request count, latency, error rate). Create composite alarms that trigger SNS notifications. Cost is minimal but prevents extended outages that cause revenue loss.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy. `deploy.sh` runs `docker-compose build` and `docker-compose up -d` — a direct in-place deployment with no blue/green, no canary, no traffic shifting. The CloudFormation template does not configure App Runner deployment preferences. No feature flags.
- **Gap**: Straight-to-production deployment. Any deployment failure causes immediate downtime for all users.
- **Recommendation**: App Runner supports automatic rollback on deployment failures — enable this in the CloudFormation template. For canary deployments, consider migrating to ECS on Fargate with CodeDeploy for blue/green deployment capability.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files of any kind in the repository. No test directories, no PHPUnit, no test frameworks, no integration tests, no unit tests, no end-to-end tests. The `docker-compose.yml` health check (`curl -f http://localhost/api/products`) is the only automated verification.
- **Gap**: Zero test coverage. Every code change is deployed without automated verification, increasing the risk and cost of production defects.
- **Recommendation**: Add PHPUnit with integration tests for the critical API endpoints (order creation, payment processing, return flow). Run tests in CI before deployment. This is the single highest-ROI investment for reducing production incident costs.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, no SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No self-healing patterns. No links to runbooks in any configuration. The only "recovery" mechanism is the RDS snapshot DeletionPolicy.
- **Gap**: Entirely manual incident response. No automated remediation for any failure scenario.
- **Recommendation**: Create markdown runbooks for common failure scenarios (database connection failures, App Runner deployment failures, high error rates). Store them in the repository. This is a low-cost investment that reduces MTTR and associated labor costs.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file, no team ownership definitions, no SLO files, no observability governance documentation. No platform team tooling configuration. No per-service dashboards or alarms.
- **Gap**: No observability ownership model. No one is explicitly responsible for monitoring the application's health.
- **Recommendation**: Create a CODEOWNERS file and define SLO ownership. Establish basic on-call rotation. This organizational investment reduces the hidden cost of unowned operational responsibilities.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Low | High | APP-Q4: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | High | — | — | — |
| Move to Managed Databases | Not Triggered | High | — | — | — |
| Move to Managed Analytics | Not Triggered | High | — | — | — |
| Move to Modern DevOps | Triggered | Medium | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Low | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | Medium |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps — CI/CD, testing, observability, and deployment strategy improvements can begin immediately with no dependencies on other pathways.

**Parallel Track 2**: Move to Cloud Native — Architecture decomposition work can proceed in parallel with DevOps improvements. The CI/CD pipeline from Track 1 will support deployment of extracted services.

**Sequential Dependencies**: Move to AI depends on Move to Modern DevOps (need CI/CD and observability before deploying AI services) and benefits from Move to Cloud Native (extracted services provide cleaner tool boundaries for agents).

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Single `index.php` monolith with all 6 business domains tightly coupled, shared MySQL database with cross-domain foreign keys
  - APP-Q3: Score 1/4 — 100% synchronous communication, no async patterns
  - APP-Q10: Score 1/4 — No async job processing, all operations synchronous within HTTP request lifecycle
- **Current State**: Tightly-coupled monolith in a single PHP file. All domains (orders, inventory, payments, returns, users, fulfillment) share one MySQL database. No module boundaries, no async capabilities, no independent scaling.
- **Target State**: Loosely-coupled services with independent scaling, async communication via SQS/EventBridge, and independent data stores per domain.
- **Key Activities**:
  1. Identify bounded contexts (orders, inventory, payments, returns, users, fulfillment) through domain analysis
  2. Extract the highest-value, most independent domain as a separate service using Strangler Fig pattern
  3. Introduce SQS/EventBridge for async communication between services
  4. Implement API Gateway routing to direct traffic to the new service while maintaining the monolith as fallback
- **Dependencies**: Benefits from Move to Modern DevOps (CI/CD pipeline for deploying new services)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Managed Service Migration) and Phase 3 (Optimization & Governance)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline. Only manual `deploy.sh` with docker-compose
  - OPS-Q9: Score 1/4 — No deployment strategy. Direct docker-compose up with no rollback
  - OPS-Q10: Score 1/4 — Zero test files in the repository. No PHPUnit, no test framework
  - OPS-Q1: Score 1/4 — No distributed tracing. No X-Ray, no OpenTelemetry
- **Current State**: Manual deployment via `deploy.sh`, no CI/CD pipeline, no tests, no observability, no rollback capability. Every deployment is a manual, risky process.
- **Target State**: Automated CI/CD pipeline with test, build, deploy stages; structured logging with correlation IDs; distributed tracing; SLO-based monitoring; automated rollback on failures.
- **Key Activities**:
  1. Create a CI/CD pipeline (GitHub Actions or CodePipeline) with lint → test → build → deploy stages
  2. Add PHPUnit integration tests for critical API endpoints
  3. Implement structured JSON logging with Monolog and correlation IDs
  4. Enable X-Ray tracing in App Runner
  5. Define SLOs and create CloudWatch alarms
  6. Configure App Runner automatic rollback on deployment failures
- **Dependencies**: None — this is the foundational pathway that enables all others
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (License & Quick Savings) and Phase 2 (Managed Service Migration)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks, no Bedrock, LangChain, or Strands SDK
  - DATA-Q1: Score 1/4 — No vector database
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated eval framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI capabilities whatsoever. The fulfillment workflow is entirely manual (7-step human-driven process). Return processing requires manual CS review (24-48 hours). PHP has limited AI framework ecosystem.
- **Target State**: AI-assisted decision-making for fulfillment (warehouse assignment, carrier selection, quality checks) and automated return processing via agent workflows.
- **Key Activities**:
  1. Add a Python or Node.js sidecar service for AI agent orchestration
  2. Implement Amazon Bedrock integration for intelligent fulfillment decisions
  3. Build an agent that calls the monolith's existing JSON APIs as tools
  4. Add OpenSearch Service with k-NN for product semantic search (if needed)
- **Dependencies**: Benefits from Move to Modern DevOps (CI/CD for deploying agent service) and Move to Cloud Native (cleaner service boundaries for agent tools)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 3 (Optimization & Governance)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Readiness Roadmap

### Phase 1 — License & Quick Savings (Days 1–30)

These are low-effort, high-impact improvements that reduce operational costs immediately:

1. **Create a CI/CD pipeline** — Set up GitHub Actions or AWS CodePipeline to automate the build → push to ECR → deploy to App Runner workflow. Eliminates manual deployment labor (estimated savings: 2-4 engineering hours per deployment).
2. **Add WAF rate-based rules** — Add a rate-based rule to the existing WAF Web ACL to prevent abuse-driven App Runner auto-scaling costs. Low effort (single CloudFormation resource addition).
3. **Store secrets in Secrets Manager** — Move database credentials from environment variables and hardcoded defaults to AWS Secrets Manager. Eliminates the risk of credential exposure and associated breach costs.
4. **Add basic integration tests** — Create PHPUnit tests for the 3 most critical endpoints (order creation, payment processing, return submission). Run in CI pipeline. Reduces the cost of production regressions.
5. **Implement structured logging** — Add Monolog with JSON formatter to `index.php`. Inject correlation IDs into all request processing. This reduces mean-time-to-resolution for production incidents.
6. **Replace `die()` with proper error handling** — Replace the `die("Database connection failed...")` in `get_db()` with a JSON error response and connection retry logic. Prevents information leakage and improves resilience.

### Phase 2 — Managed Service Migration (Months 1–3)

Structural improvements that reduce ongoing infrastructure and operational costs:

1. **Migrate RDS MySQL to Aurora MySQL Serverless v2** — Aurora Serverless v2 auto-scales from 0.5 to 128 ACUs based on demand, eliminating the need to right-size a fixed `db.t3.micro` instance. Built-in Multi-AZ provides automatic failover. Use AWS DMS for zero-downtime migration. Expected cost benefit: pay-per-use instead of fixed instance, plus improved resilience reduces downtime costs.
2. **Enable distributed tracing** — Configure AWS X-Ray tracing for App Runner. Add X-Ray SDK or OpenTelemetry instrumentation. This provides request-level visibility for diagnosing performance issues and optimizing resource usage.
3. **Define SLOs and create CloudWatch alarms** — Set p99 latency and error rate targets. Create alarms that trigger SNS notifications. This provides early warning of issues before they become expensive outages.
4. **Implement a data access layer** — Refactor raw PDO queries into repository classes per domain (OrderRepository, InventoryRepository, PaymentRepository, etc.). This is a prerequisite for future database engine migration (MySQL → Aurora PostgreSQL) and reduces the cost of schema changes.
5. **Add CloudTrail for audit logging** — Enable CloudTrail with log file validation and S3 storage. Minimal cost (~$2/month) for essential compliance and incident investigation capability.
6. **Migrate to Cognito for identity management** — Replace the custom MySQL-based user store with Amazon Cognito. Free tier covers 50,000 MAU. Eliminates the operational cost of managing password policies, MFA, and session management.

### Phase 3 — Optimization & Governance (Months 3–6)

Capabilities that unlock long-term cost optimization once foundations are solid:

1. **Evaluate Aurora PostgreSQL migration** — If the data access layer is in place, assess migrating from Aurora MySQL to Aurora PostgreSQL for access to pgvector (enabling future AI/RAG capabilities without a separate vector database), richer extension ecosystem, and potentially better cost/performance for complex queries. Use AWS SCT for schema assessment.
2. **Implement business metrics dashboards** — Publish order throughput, fulfillment time, return rate, and revenue metrics to CloudWatch. Use dashboards for data-driven cost optimization decisions (e.g., identify over-provisioned resources, optimize fulfillment routing).
3. **Begin service decomposition** — Extract the first independent domain (candidate: inventory or user management) as a separate Fargate service. This enables independent scaling and reduces the blast radius of changes.
4. **Implement anomaly detection** — Enable CloudWatch anomaly detection on key metrics. Create composite alarms for multi-signal alerting. This prevents costly extended outages through early detection.
5. **Create operational runbooks** — Document recovery procedures for common failure scenarios. Store in the repository as versioned markdown. This reduces MTTR and enables junior engineers to handle incidents without escalation.
6. **Evaluate Step Functions for fulfillment** — Implement the 7-step fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) as a Step Functions state machine. This automates manual coordination work and reduces labor costs in the fulfillment process.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
  - Relevant for Aurora MySQL/PostgreSQL Serverless v2 migration planning
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY

---

## Appendix: Evidence Index

| # | File | What It Revealed |
|---|------|-----------------|
| 1 | `index.php` | Single-file PHP monolith containing all 6 business domains (orders, inventory, payments, returns, users, fulfillment), 9 database table schemas (CREATE TABLE IF NOT EXISTS), 25+ API endpoints, session-based auth, direct PDO queries, `die()` error handling, no resilience patterns, JSON API responses, hardcoded credential defaults |
| 2 | `infrastructure/monolith-apprunner.yaml` | CloudFormation template: App Runner service, RDS MySQL 8.4.8 (db.t3.micro, encrypted, private subnet), VPC with 2 private subnets, security groups, ECR repository, WAF with IP whitelisting, auto-scaling (min 1, max 3), IAM roles with CloudWatchLogsFullAccess, NoEcho DB credentials passed as environment variables |
| 3 | `Dockerfile` | PHP 8.2 Apache base image, installs PDO MySQL extension, copies index.php and .htaccess, exposes port 80. No dependency manager (no composer install) |
| 4 | `docker-compose.yml` | MySQL 8.0 (different from production 8.4.8), hardcoded credentials (MYSQL_PASSWORD: ecommerce_pass, MYSQL_ROOT_PASSWORD: rootpassword), health check on MySQL, volume for data persistence |
| 5 | `deploy.sh` | Manual deployment script: checks Docker running, runs docker-compose build and docker-compose up -d, waits 5 seconds, checks health via curl. No rollback, no CI/CD integration |
| 6 | `.htaccess` | Apache URL rewriting — routes all requests to index.php (single entry point pattern) |
| 7 | `.gitignore` | Excludes database files, logs, OS files, and IDE files. No reference to test output, build artifacts, or dependency directories |
