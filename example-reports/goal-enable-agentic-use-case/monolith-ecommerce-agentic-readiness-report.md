# Agentic Readiness Assessment Report
**Target**: ./monolith
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: enable-agentic-use-case
**Goal Context**: Building an AI agent that handles order status inquiries, processes returns, and manages inventory restocking across the e-commerce platform
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

This PHP monolith e-commerce application has **significant gaps** that must be addressed before an AI agent can reliably handle order status inquiries, process returns, and manage inventory restocking. The entire application — orders, inventory, payments, returns, warehousing, and user management — is tightly coupled in a single `index.php` file (~1,800 lines) backed by a shared MySQL database. There is no API documentation, no async messaging, no CI/CD pipeline, and no observability infrastructure. The strongest areas are the managed compute (AWS App Runner) and managed database (RDS MySQL 8.4.8) defined in the CloudFormation template, along with structured JSON API responses that agents can consume. The most critical blockers for the agentic use case are the complete absence of API documentation (agents need OpenAPI specs to discover and invoke tools), no AI/agent framework integration, no vector database or RAG pipeline, and no automated evaluation or cost tracking infrastructure.

### Overall Score: 1.6 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.1 / 4.0 | 🟠 |
| Application Architecture | 1.3 / 4.0 | 🟠 |
| Data Foundations | 1.9 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.5 / 4.0 | 🟠 |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

**1. APP-Q2 — No API Documentation (Score: 1/4)** *(Goal-priority criterion)*
The agent being built to handle order status, returns, and inventory restocking needs OpenAPI specifications to discover and invoke API endpoints. Currently, all routes are defined inline via regex matching in `index.php` with zero documentation. **First step:** Generate OpenAPI 3.0 specs for the existing `/api/*` endpoints — at minimum the order status, returns, and inventory endpoints the agent will need.

**2. APP-Q13 — No AI/Agent Frameworks (Score: 1/4)** *(Goal-priority criterion)*
No AI/agent SDK is present (no Bedrock, LangChain, Strands, or MCP integration). The agent cannot interact with this application without an integration layer. **First step:** Add a Python or TypeScript agent service (outside the PHP monolith) using Strands Agents SDK or Amazon Bedrock Agents that calls the monolith's existing JSON APIs as tools.

**3. DATA-Q1 — No Vector Database (Score: 1/4)** *(Goal-priority criterion)*
The order status inquiry agent will need semantic search over product catalogs, order histories, and return policies. No vector database (OpenSearch, pgvector, Bedrock Knowledge Bases) exists. **First step:** Create an Amazon Bedrock Knowledge Base backed by OpenSearch Serverless, indexed with product catalog data and return policy documents.

**4. OPS-Q3 — No Automated Evals (Score: 1/4)** *(Goal-priority criterion)*
There is no evaluation framework, no test files of any kind, and no golden datasets. Without evals, you cannot measure whether the agent correctly answers order status queries or processes returns accurately. **First step:** Create a golden dataset of 50+ order status inquiries with expected responses and implement automated scoring.

**5. INF-Q6 — No CI/CD Pipeline (Score: 1/4)**
Deployment is manual via `deploy.sh` using `docker-compose`. There is no GitHub Actions, CodePipeline, or any automated build/test/deploy pipeline. Agent deployments require automated, repeatable pipelines with rollback capability. **First step:** Create a GitHub Actions workflow or AWS CodePipeline that builds the Docker image, pushes to ECR, and deploys to App Runner.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: The CloudFormation template (`infrastructure/monolith-apprunner.yaml`) defines an `AWS::AppRunner::Service` resource — a fully managed container compute platform. A `Dockerfile` (PHP 8.2-apache) is present for containerization. `docker-compose.yml` is used for local development only. No EC2 instances are defined anywhere.
- **Gap**: App Runner is managed but provides limited control compared to ECS/EKS. The customer preference is for ECS/EKS with container orchestration, Helm, and GitOps — App Runner does not support these patterns.
- **Recommendation**: Migrate from App Runner to Amazon ECS on Fargate (preferred per customer preferences) to gain ECS Service Connect, Helm-compatible deployment via Copilot or CDK, and tighter integration with ALB for API Gateway routing. Define ECS task definitions and services in Terraform (preferred IaC).

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::RDS::DBInstance` (MySQL 8.4.8) — a fully managed database with automated backups (7-day retention), encrypted storage, and private subnet placement. `docker-compose.yml` runs self-managed `mysql:8.0` for local development with hardcoded credentials.
- **Gap**: Local development uses a self-managed MySQL container with credentials in plaintext. Production RDS is managed but uses a single-AZ `db.t3.micro` instance with no Multi-AZ failover. No read replicas configured.
- **Recommendation**: Enable Multi-AZ on the RDS instance for high availability (critical for agent uptime). Consider Amazon Aurora MySQL for automatic failover and read replicas that the agent can use for read-heavy order status queries. Align local dev with production using RDS-compatible patterns.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service found. No `aws_sfn_*`, Temporal SDK, or workflow engine references in any file. The order fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) is implemented as separate API endpoints in `index.php` called manually via the admin UI.
- **Gap**: The entire fulfillment workflow is manual and unorchestrated. Each step requires an admin to click a button. There is no state machine, no retry logic, no timeout handling, and no error recovery.
- **Recommendation**: Implement AWS Step Functions to orchestrate the order fulfillment workflow. This enables the agent to trigger and monitor multi-step workflows (e.g., processing a return involves validating the order, approving the refund, restocking inventory, and notifying the customer — all as a single orchestrated flow). Use EventBridge (preferred) to trigger workflows from order events.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, MSK, or any messaging service found in the CloudFormation template or application code. All communication is synchronous HTTP requests handled within `index.php`. No event-driven patterns detected.
- **Gap**: No async messaging of any kind. All operations are synchronous, which means the agent must wait for each operation to complete before proceeding. Return processing, inventory restocking, and order fulfillment all block the caller.
- **Recommendation**: Introduce Amazon SQS for decoupling long-running operations (return processing, inventory restocking), Amazon SNS for notifications (order status updates to customers), and Amazon EventBridge (preferred) for event-driven orchestration. The agent can publish events (e.g., "return-requested") and SQS workers process them asynchronously.

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` is a comprehensive CloudFormation template covering VPC, subnets, security groups, RDS, App Runner, ECR, WAF, IAM roles, and auto-scaling — approximately 90% of the infrastructure is codified. Only the initial Docker build/push and stack parameter updates are manual.
- **Gap**: Single monolithic CloudFormation template (not modularized). Customer prefers Terraform and GitOps patterns, which are not in use. No remote state management, no module reuse, no environment separation.
- **Recommendation**: Migrate IaC to Terraform (preferred) with separate modules for VPC/networking, compute (ECS), database (RDS/Aurora), and messaging (SQS/EventBridge). Implement GitOps using ArgoCD or Flux for declarative deployments via Helm charts.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline found. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline definitions. The only deployment mechanism is `deploy.sh`, a 30-line bash script that runs `docker-compose build` and `docker-compose up -d`. The CloudFormation output includes manual instructions for ECR push.
- **Gap**: Entirely manual deployment process. No automated testing, no automated builds, no deployment automation. Agent iterations require rapid deployment cycles that manual processes cannot support.
- **Recommendation**: Create a GitHub Actions pipeline (or AWS CodePipeline) that: (1) builds the Docker image, (2) pushes to ECR, (3) runs integration tests, (4) deploys to ECS via Helm/GitOps. Implement separate pipelines for the agent service and the monolith.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: App Runner provides a public URL endpoint. A WAFv2 Web ACL (`WebACL` resource in CloudFormation) is associated with the App Runner service, configured with IP whitelisting via an `IPSet`. No API Gateway is defined. No throttling, request validation, or API key management.
- **Gap**: No API Gateway with throttling, auth middleware, or request validation. The WAF only performs IP whitelisting — it does not provide API management capabilities. The agent will need rate-limited, authenticated API endpoints.
- **Recommendation**: Add Amazon API Gateway (REST or HTTP API) in front of the application to provide throttling, API key management, request/response validation, and usage plans. This gives the agent a well-defined, rate-limited entry point with per-client quotas. Use ALB (preferred) as the integration target for ECS.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming service found in the CloudFormation template or application code. No stream consumer patterns detected.
- **Gap**: No real-time streaming infrastructure. Order status changes, inventory updates, and return events are only persisted to MySQL — they are not streamed for real-time consumption by the agent or other services.
- **Recommendation**: Introduce Amazon EventBridge (preferred) for domain events (order-created, return-requested, inventory-low). For high-throughput scenarios, consider Amazon Kinesis Data Streams. The agent can subscribe to EventBridge events to proactively handle inventory restocking when stock levels drop.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines a VPC (`10.0.0.0/16`) with two private subnets (`PrivateSubnet1`, `PrivateSubnet2`). RDS is in private subnets only (`PubliclyAccessible: false`). Security groups restrict MySQL access to App Runner's security group only (`DBSecurityGroup` ingress from `AppRunnerSecurityGroup`). WAFv2 provides IP whitelisting.
- **Gap**: No public subnets or NAT gateway defined (may limit outbound access for ECS tasks). No NACLs defined beyond VPC defaults. Security group rules are reasonable but could be further tightened. No VPC flow logs configured.
- **Recommendation**: Add VPC Flow Logs for network traffic monitoring. When migrating to ECS, add public subnets with NAT Gateway for outbound access. Add NACLs for defense-in-depth. Enable VPC endpoints for ECR, S3, and other AWS services to keep traffic private.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::AppRunner::AutoScalingConfiguration` with configurable `MinSize` (default: 1), `MaxSize` (default: 3), and `MaxConcurrency` (100). Auto-scaling is configured for the compute layer.
- **Gap**: Database (RDS `db.t3.micro`) has no auto-scaling. No read replicas to handle agent read-heavy traffic for order status queries. Auto-scaling parameters are conservative (max 3 instances).
- **Recommendation**: When migrating to ECS, configure ECS Service Auto Scaling with target tracking on CPU/memory and request count. Enable RDS Storage Auto Scaling. Consider Aurora Serverless v2 for automatic database scaling during peak agent activity.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: PHP 8.2 is the sole programming language, as identified in `Dockerfile` (`FROM php:8.2-apache`) and the single `index.php` application file. PHP extensions installed are `pdo` and `pdo_mysql`.
- **Gap**: PHP has a limited AI/agent framework ecosystem compared to Python or TypeScript. There is no native Bedrock SDK for PHP (AWS SDK for PHP exists but Bedrock agent support is minimal). Major agent frameworks (LangChain, Strands, CrewAI) are Python/TypeScript-first.
- **Recommendation**: Build the agent service in Python or TypeScript (separate from the PHP monolith) using Strands Agents SDK or Amazon Bedrock Agents. The agent service calls the PHP monolith's JSON APIs as tools. Over time, extract PHP services into Python/TypeScript microservices on ECS (preferred).

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specifications found in the repository. No `openapi.yaml`, `swagger.json`, or API documentation files. All API routes are defined inline in `index.php` using regex pattern matching (e.g., `preg_match('#^/api/orders/([^/]+)/history$#', ...)`). No annotations or auto-generation framework.
- **Gap**: Complete absence of API documentation. The agent has no way to programmatically discover available endpoints, required parameters, or response schemas. This is the single biggest blocker for the agentic use case.
- **Recommendation**: Generate OpenAPI 3.0 specifications for all `/api/*` endpoints. Prioritize the endpoints the agent needs: `GET /api/orders/me`, `GET /api/orders/{id}/history`, `POST /api/returns`, `GET /api/products`, `POST /api/orders/{id}/assign-warehouse`, `GET /api/warehouses/assignment-options`. Use these specs to define agent tools.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous communication. Every API endpoint in `index.php` executes synchronously — database queries, order processing, return creation, and inventory updates all complete within the HTTP request/response cycle. No message queue publishing, no event emission, no async handlers detected.
- **Gap**: All operations block the caller. Return approval (`/api/admin/approve-return`) involves a multi-step transaction (update return, restore inventory, issue refund, update order) executed synchronously. If any step is slow, the entire request blocks.
- **Recommendation**: Introduce Amazon SQS (preferred) for decoupling write operations. The agent can submit a return request and receive an immediate acknowledgment, then poll for completion or receive an EventBridge notification. Implement async workers on ECS for inventory restocking and return processing.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: Single `index.php` file (~1,800 lines) containing ALL business domains: Orders (order creation, fulfillment workflow with 8 steps), Inventory (product listing, stock management), Payments (payment processing, refunds), Returns (return requests, admin approval), Warehouses (assignment, capacity tracking), Users (authentication, CRUD), Customer Interactions (logging), and Order Status History (tracking). All domains share a single MySQL database via a `get_db()` PDO connection. Foreign key relationships cross domain boundaries (e.g., `returns.order_id → orders.id`, `payments.order_id → orders.id`, `order_items.order_id → orders.id`).
- **Gap**: Tightly coupled monolith with no module boundaries, no separation of concerns, and pervasive database coupling. All domains are interleaved in a single file. Cannot independently scale, deploy, or assign agent tools to specific domains.
- **Recommendation**: This monolith would benefit from service extraction to create clear agent tool boundaries. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API endpoints return structured JSON via `json_encode()`. The `Content-Type: application/json` header is set at the top of the API routing section in `index.php` (`header('Content-Type: application/json')`). Response structures include typed fields (strings, numbers, booleans, arrays, nested objects). Examples: `/api/products` returns `{"products": [...]}`, `/api/orders/{id}/validation-data` returns nested objects with risk factors and recommendation scores.
- **Gap**: None — JSON responses are well-structured and agent-consumable.
- **Recommendation**: Maintain structured JSON. When adding OpenAPI specs, formally document these response schemas. Consider adding standard envelope patterns (e.g., `{"data": ..., "meta": {...}}`) for pagination and error consistency.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration framework. The order fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) is implemented as 7 separate POST endpoints in `index.php`, each updating the order status in MySQL via `update_order_status()`. State transitions are simple database status string updates with no guard conditions, no rollback logic, and no timeout handling.
- **Gap**: No orchestrated workflow. Each step is an independent API call with no coordination. If the admin skips a step or an error occurs mid-workflow, there is no recovery mechanism. The agent needs orchestrated workflows to reliably process returns and manage fulfillment.
- **Recommendation**: Implement AWS Step Functions for the fulfillment and returns workflows. Define state machines that the agent can invoke as a single tool (e.g., "process-return" tool triggers a Step Function that handles the full return lifecycle). Use EventBridge (preferred) to connect workflow events.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys or deduplication mechanisms found. Order IDs are generated via `uniqid('order-')` which is time-based and not idempotent — calling the same create order endpoint twice with the same data produces two separate orders. Payment IDs, return IDs, and all entity IDs use the same `uniqid()` pattern. No `Idempotency-Key` headers checked.
- **Gap**: Critical gap for agent operations. If the agent retries a failed return request or order creation (due to network timeout), it will create duplicate records. Agents inherently need retry capability, making idempotency essential.
- **Recommendation**: Implement idempotency keys for all write endpoints. Accept an `Idempotency-Key` header, store it with a TTL in DynamoDB (preferred), and return the cached response for duplicate requests. Prioritize the return and order creation endpoints the agent will use.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: WAFv2 is configured for IP whitelisting only (allow specific IPs, block all others). No rate limiting rules in the WAF configuration. No application-level rate limiting middleware in `index.php`. No throttling of any kind.
- **Gap**: No rate limiting at any layer. An agent making rapid API calls could overwhelm the application. Conversely, a misconfigured agent in a retry loop could generate unbounded requests.
- **Recommendation**: Add API Gateway (preferred) with usage plans, throttling (burst/rate limits), and per-API-key quotas. Configure WAF rate-based rules as a secondary defense. This protects the backend from runaway agent behavior.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry logic, or timeout configurations found. The only error handling is basic `try/catch` blocks around database operations that return HTTP 400/500 errors with `json_encode(['error' => $e->getMessage()])`. The `get_db()` function calls `die()` on connection failure. No exponential backoff, no fallback patterns.
- **Gap**: No resilience patterns of any kind. A database timeout causes the application to crash (`die()`). The agent will encounter unrecoverable failures with no retry guidance from the API.
- **Recommendation**: Implement retry-after headers on 429/503 responses. Add circuit breaker patterns for database connections. When migrating to ECS microservices, implement Resilience4j (Java) or equivalent patterns. Configure health checks with graceful degradation.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: No async job processing. The return approval flow (`/api/admin/approve-return`) performs a multi-step transaction synchronously: fetch return, fetch order, fetch items, update return status, restore inventory for each item, issue refund payment, update order status — all within a single HTTP request. No background workers, no job queues, no status polling endpoints.
- **Gap**: Return processing and inventory restocking — the core agent operations — execute synchronously. If the agent triggers a complex return, it blocks until the entire transaction completes. No timeout protection.
- **Recommendation**: Extract long-running operations into SQS-backed ECS workers (preferred). The agent calls a "submit return" endpoint that returns immediately with a job ID, then polls a status endpoint or receives an EventBridge callback when processing completes.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning detected. No `/v1/` or `/v2/` URL patterns. No `Accept-Version` or `API-Version` headers. No changelog or migration documentation. All endpoints are unversioned (e.g., `/api/products`, `/api/orders`, `/api/returns`).
- **Gap**: When the agent is built against specific API contracts and those contracts change (e.g., new fields, changed response shapes), the agent will break with no backward compatibility guarantee.
- **Recommendation**: Introduce URL-path versioning (e.g., `/api/v1/products`) before the agent is built. This allows safe API evolution without breaking the agent's tool definitions. Document a deprecation policy.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith — no inter-service communication exists. No service registry, no API catalog, no service mesh. The agent service (when built) will need to discover the monolith's API endpoint. Currently, endpoints would need to be hardcoded.
- **Gap**: No service discovery mechanism. When decomposing into microservices, services will need to discover each other dynamically. The agent needs a service catalog to know which tools are available.
- **Recommendation**: When migrating to ECS, use ECS Service Connect or AWS Cloud Map for service discovery. Implement an API catalog (API Gateway as registry) so the agent can dynamically discover available tools. Avoid hardcoded endpoints.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports found. No Bedrock SDK calls, no LangChain, no Strands Agents, no OpenAI, no Anthropic SDK references. No MCP (Model Context Protocol) server or client. The application is purely a traditional PHP web application with no AI integration points.
- **Gap**: Complete absence of AI/agent capability. The agent for order status, returns, and inventory restocking has zero integration surface with this codebase today.
- **Recommendation**: Build a separate agent service in Python using Strands Agents SDK (or Amazon Bedrock Agents) deployed on ECS (preferred). Define MCP tools that wrap the monolith's existing JSON APIs. Start with three tools: (1) get-order-status, (2) submit-return, (3) check-inventory. The agent service runs alongside the monolith on ECS and calls it via HTTP.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch, pgvector, Pinecone, Chroma, Weaviate, or Bedrock Knowledge Base references in any file. No embedding-related imports or configurations.
- **Gap**: The agent needs semantic search for order status inquiries (e.g., "What happened to my blue shirt order?") and inventory lookups (e.g., "Do you have anything similar to running shoes?"). Without a vector database, the agent cannot perform natural language search over products or orders.
- **Recommendation**: Create an Amazon Bedrock Knowledge Base backed by OpenSearch Serverless for product catalog semantic search. Index product descriptions, return policies, and FAQ content. The agent uses this for customer inquiry resolution and inventory recommendations.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (as established in DATA-Q1), so there is no management status to assess.
- **Gap**: No vector database to manage.
- **Recommendation**: When implementing the vector database (DATA-Q1), use a fully managed service: Amazon Bedrock Knowledge Bases (preferred — fully managed RAG pipeline) or Amazon OpenSearch Serverless (managed vector store). Avoid self-hosted solutions.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline found. No embedding model calls, no document chunking code, no similarity search patterns. No Bedrock Titan embedding calls, no langchain chunking utilities.
- **Gap**: The customer support agent needs RAG to answer questions about return policies, shipping timelines, and product details. Without RAG, the agent can only query structured database records — it cannot reason over unstructured knowledge.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases: (1) Store product documentation, return policies, and FAQ in S3, (2) Configure Bedrock to chunk, embed, and index into OpenSearch Serverless, (3) The agent queries the Knowledge Base for context before responding to customer inquiries.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database with 9 tables (orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users). All data accessed through a single PDO connection via `get_db()` in `index.php`. No external API calls, no secondary databases, no third-party data sources.
- **Gap**: None — single data source is clean for agent integration.
- **Recommendation**: Maintain the single data source advantage as you decompose. When extracting microservices, use a shared RDS instance initially (with schema-per-service), then migrate to per-service databases (e.g., DynamoDB for inventory, RDS for orders) with clear data ownership boundaries.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Direct SQL queries via PDO are scattered throughout `index.php`. Every API handler directly constructs and executes SQL statements (e.g., `$db->prepare('SELECT * FROM orders WHERE id = ?')`). The `get_db()` function provides a shared database connection, but there is no repository pattern, no ORM, and no data access abstraction layer.
- **Gap**: SQL logic is mixed into business logic. The agent cannot safely call data access functions without going through the full HTTP API. If direct database access were needed (e.g., for a data query agent), there are no safe abstraction boundaries.
- **Recommendation**: Before decomposition, extract data access into a repository pattern (OrderRepository, InventoryRepository, etc.). This creates clean interfaces that can later become microservice APIs. The agent always accesses data through the HTTP API layer — never direct database queries.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing, no Textract or Tika usage. No file upload handling in the application. Product images are referenced as URLs (`image_url` field) but no actual image/document processing exists.
- **Gap**: No unstructured data handling. Return policies, product manuals, and shipping guides that the agent could use for RAG are not stored or parseable.
- **Recommendation**: Store return policies, FAQ documents, and product specifications in S3. Use Amazon Textract for any scanned documents. Feed these into the Bedrock Knowledge Base (DATA-Q3) for the agent's RAG pipeline.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No JSON Schema files, no database migration tools (Flyway, Liquibase, Alembic), no schema registry. The database schema is defined inline in `index.php` via `CREATE TABLE IF NOT EXISTS` statements in the `init_db()` function. Schema changes are applied via `ALTER TABLE` with try/catch to ignore duplicate column errors. No schema version tracking.
- **Gap**: Schema is undocumented and unversioned. The agent's data query tool cannot validate queries against a formal schema. Schema changes risk breaking the agent without warning.
- **Recommendation**: Extract schema definitions into versioned migration files using Flyway or Liquibase. Document the schema as JSON Schema or in the OpenAPI specification's `components/schemas` section. This gives the agent formal data contracts.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. Every API handler directly constructs SQL queries inline. The `get_db()` function returns a raw PDO connection — it is a connection factory, not a data access layer. Example: the return approval endpoint directly queries `returns`, `orders`, `order_items`, `inventory`, and `payments` tables in a single handler.
- **Gap**: No abstraction between business logic and data storage. Extracting services requires rewriting every SQL query. The agent cannot interact with a clean data interface — it must go through the HTTP API.
- **Recommendation**: Introduce a repository pattern with interfaces: `OrderRepository`, `InventoryRepository`, `ReturnRepository`. Each repository encapsulates all SQL for its domain. This is a prerequisite for microservice extraction and enables clean agent tool boundaries.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist to refresh. No embedding generation pipeline, no scheduled re-indexing, no CDC (Change Data Capture) patterns.
- **Gap**: When vector database and RAG are implemented, there will be no mechanism to keep embeddings fresh as products and policies change.
- **Recommendation**: When implementing the vector database, configure automated sync via Bedrock Knowledge Base data source sync (scheduled or event-driven). Use EventBridge to trigger re-indexing when products are added/updated or return policies change.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: CloudFormation `infrastructure/monolith-apprunner.yaml` explicitly pins `EngineVersion: '8.4.8'` for the RDS MySQL instance. MySQL 8.4 is the current LTS release with support through 2032. `docker-compose.yml` uses `mysql:8.0` for local development, which is supported through 2026. `AutoMinorVersionUpgrade: true` is enabled for automatic patching.
- **Gap**: None — database engine versions are explicitly pinned and current.
- **Recommendation**: Maintain explicit version pinning. Monitor MySQL 8.0 EOL (April 2026) for the local development environment and upgrade docker-compose to mysql:8.4 for consistency with production.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs detected. All SQL in `index.php` uses standard ANSI SQL (SELECT, INSERT, UPDATE, DELETE with prepared statements). Business logic is entirely in the PHP application layer. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements. No PL/SQL or T-SQL syntax.
- **Gap**: None — all business logic is in the application layer, which is ideal for migration and agent integration.
- **Recommendation**: Maintain this clean separation. When migrating to microservices, the absence of stored procedures means database migration (e.g., to Aurora or DynamoDB) will not require SQL logic extraction.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded as fallback defaults in `index.php`: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. `docker-compose.yml` contains plaintext credentials: `MYSQL_ROOT_PASSWORD: rootpassword`, `MYSQL_USER: ecommerce_user`, `MYSQL_PASSWORD: ecommerce_pass`. CloudFormation template uses `NoEcho: true` for DB credentials but includes default values (`DBUsername: ecommerce_user`, `DBPassword: ChangeMe123!`).
- **Gap**: Credentials hardcoded in source code and committed to version control. No AWS Secrets Manager, no HashiCorp Vault, no secure credential storage of any kind.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager. Update the CloudFormation template to create a Secrets Manager secret and reference it via `{{resolve:secretsmanager:...}}`. Update the PHP application to fetch credentials from Secrets Manager at startup (or inject via ECS task definition secrets). Remove all hardcoded defaults from `index.php`.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: CloudFormation defines two IAM roles: `AppRunnerInstanceRole` with `arn:aws:iam::aws:policy/CloudWatchLogsFullAccess` (AWS-managed policy granting full CloudWatch Logs access), and `AppRunnerAccessRole` with `arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess` (scoped to ECR access for App Runner).
- **Gap**: `CloudWatchLogsFullAccess` is an overly broad managed policy that grants `logs:*` on all resources. It should be scoped to the specific log group for this service. No per-service role isolation — a single role covers all application functionality.
- **Recommendation**: Replace `CloudWatchLogsFullAccess` with a custom policy scoped to the specific log group (e.g., `arn:aws:logs:*:*:log-group:/aws/apprunner/${ServiceName}*`). When migrating to ECS microservices, create per-service IAM roles with minimum required permissions. Add IAM policies for Secrets Manager access (read-only for the DB secret).

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: PHP session-based authentication only. `session_start()` is called at the top of `index.php`. Login checks username/password against the `users` table and stores user data in `$_SESSION['user']`. API authentication checks `$_SESSION['user']` existence. No JWT tokens, no OAuth2 flows, no token exchange.
- **Gap**: Session-based auth is not suitable for agent-to-service communication. The agent cannot maintain PHP sessions. No user identity propagation across service boundaries (critical when the agent acts on behalf of a customer).
- **Recommendation**: Implement Amazon Cognito for centralized authentication. Issue JWT tokens that the agent can use for API authentication. Implement token-based auth on all API endpoints with user context (customer_id, role) embedded in the JWT. This enables the agent to act on behalf of specific customers with proper authorization.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in the CloudFormation template. No audit logging infrastructure. WAFv2 has `CloudWatchMetricsEnabled: true` for request sampling, but this is WAF metrics, not audit logging. Application-level actions (order creation, return approval, etc.) are logged only as status history records in the `order_status_history` MySQL table.
- **Gap**: No immutable audit trail. Agent actions (processing returns, restocking inventory) must be auditable. If the agent makes an incorrect decision, there is no way to reconstruct what happened beyond the database status fields.
- **Recommendation**: Enable AWS CloudTrail with log file validation and S3 with object lock for immutable storage. Implement application-level audit logging to CloudWatch Logs with structured events: who (agent/user), what (action), when (timestamp), outcome (success/failure). This is critical for agent governance.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: WAFv2 Web ACL is configured with a single rule for IP whitelisting. No rate-based rules (`AWS::WAFv2::WebACL` Rules section only contains `AllowSpecificIP`). No application-level rate limiting.
- **Gap**: No rate limiting at any level. The agent could inadvertently overwhelm the API, or a malicious actor could perform denial-of-service through the whitelisted IP.
- **Recommendation**: Add WAF rate-based rules (e.g., 1000 requests per 5 minutes per IP). When adding API Gateway, configure per-API-key throttling with usage plans. Define separate rate limits for the agent (higher) vs. human users (standard).

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction or masking found. Customer PII (names, emails, addresses) is returned in full in API responses (e.g., `/api/orders/{id}/validation-data` returns customer email, name, address, and account age). Error messages expose internal details via `$e->getMessage()`. PHP error logging is configured (`ini_set('log_errors', '1')`) without any log scrubbing.
- **Gap**: The agent will process and potentially log customer PII (emails, addresses, phone numbers) without any masking. This creates compliance risk (GDPR, CCPA) and data leakage risk if agent logs are stored or used for training.
- **Recommendation**: Implement PII redaction middleware that masks sensitive fields in log output. Use Amazon Macie on S3 to detect PII in stored data. Configure the agent service to redact PII before logging conversation turns. Add data classification tags to database fields.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: Return approval requires manual admin action via `/api/admin/approve-return` endpoint (admin role check enforced). Order fulfillment steps (validate, assign warehouse, pick, pack, QC, ship) each require manual admin action through the UI. However, these are manual UI button clicks, not formal approval workflows — no Step Functions `waitForTaskToken`, no approval Lambda, no approval queue.
- **Gap**: Manual approval exists as a UI flow but is not formalized as a machine-invocable approval workflow. The agent cannot request human approval for high-risk actions (e.g., processing a high-value return) without a structured approval mechanism.
- **Recommendation**: Implement AWS Step Functions with human approval tasks (`waitForTaskToken`) for high-risk agent actions. Define approval rules: returns over $100 require human approval, bulk inventory restocking requires manager sign-off. The agent triggers the workflow and pauses at the approval step until a human approves via SNS notification + approval endpoint.

#### SEC-Q8: Encryption at Rest
- **Score**: 3/4 🟡
- **Finding**: RDS `StorageEncrypted: true` in CloudFormation — data encrypted at rest using AWS-managed keys (default). ECR `EncryptionConfiguration: EncryptionType: AES256`. No customer-managed KMS keys (CMK) defined.
- **Gap**: Uses AWS-managed encryption, not customer-managed KMS keys. No control over key rotation, key policies, or cross-account access. ECR uses AES256 (S3-managed), not KMS.
- **Recommendation**: Create a customer-managed KMS key and apply it to RDS (`KmsKeyId`), ECR (`KMS` encryption type), and any future S3 buckets. This provides key rotation control and audit trail via CloudTrail KMS events.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: All `/api/*` endpoints check for `$_SESSION['user']` — unauthenticated requests receive HTTP 401. Admin endpoints additionally check `$_SESSION['user']['role'] !== 'admin'` and return 403. User passwords are hashed with `password_hash($password, PASSWORD_BCRYPT)`. However, this is session-based authentication, not OAuth2/JWT.
- **Gap**: Session-based auth is not agent-compatible. The agent cannot maintain PHP sessions across requests (sessions are tied to browser cookies). No API key mechanism for programmatic access. No OAuth2/JWT for stateless authentication.
- **Recommendation**: Implement OAuth2/JWT authentication via Amazon Cognito. Issue access tokens with scopes (e.g., `orders:read`, `returns:write`, `inventory:manage`). The agent authenticates with client credentials and receives a JWT for API calls. Maintain backward-compatible session auth for the existing UI.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: Custom authentication implemented in `index.php`. Users stored in the `users` MySQL table with bcrypt-hashed passwords. Login handled via `/login` POST route. No Amazon Cognito, no Okta, no OIDC/SAML configuration. No SSO. No MFA.
- **Gap**: Custom identity management with no centralized provider. Cannot federate identity across services when decomposing. The agent service cannot share authentication context with the monolith without a centralized IdP.
- **Recommendation**: Migrate to Amazon Cognito as the centralized identity provider. Create a Cognito User Pool, migrate existing users, and implement OAuth2 authorization code flow for the UI and client credentials flow for the agent. Enable MFA for admin users. This provides SSO across the monolith and future microservices.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing of any kind. No X-Ray SDK, no OpenTelemetry imports, no trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`). No tracing-related dependencies in the Dockerfile. No Datadog, Jaeger, or Zipkin configuration.
- **Gap**: When the agent calls the monolith's APIs, there is no way to trace the full execution path from agent request → API handler → database queries → response. Debugging agent failures will be impossible without tracing.
- **Recommendation**: Instrument the application with AWS X-Ray or OpenTelemetry. For PHP, use the OpenTelemetry PHP SDK or X-Ray daemon. When migrating to ECS, add the X-Ray sidecar container. Propagate trace IDs from the agent service through all API calls. Add `gen_ai.*` semantic conventions for LLM spans in the agent service.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: PHP error logging configured via `ini_set('log_errors', '1')` and `ini_set('display_errors', '0')` in `index.php`. Errors go to the PHP default error log (Apache error_log). No JSON log formatters, no structured logging library (e.g., monolog with JSON handler), no correlation IDs, no request context in logs.
- **Gap**: Unstructured PHP error logs cannot be queried or correlated. When the agent processes a return and it fails, there is no way to find the related log entries. No correlation between agent requests and application logs.
- **Recommendation**: Implement structured JSON logging using monolog (PHP logging library) with a JSON formatter. Add correlation IDs (trace_id, request_id) to every log entry. Ship logs to CloudWatch Logs via the ECS logging driver. Enable CloudWatch Log Insights for query-based debugging.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework found. No test files of any kind in the repository (no `tests/` directory, no `*_test.php`, no `*.test.js`). No golden datasets, no scoring scripts, no LLM-as-judge patterns. No RAGAS or eval configuration.
- **Gap**: Without automated evals, there is no way to measure whether the agent correctly handles order status inquiries, accurately processes returns, or makes appropriate inventory restocking decisions. Agent quality will be unmeasurable.
- **Recommendation**: Create a golden dataset of 50+ evaluation cases covering: order status inquiries (various statuses, edge cases), return processing (valid/invalid returns, high-value returns), and inventory restocking decisions. Implement automated scoring using LLM-as-judge or deterministic checks. Run evals in CI before every agent deployment.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms on latency, availability, or error rate. App Runner has a health check configured (`HealthCheckConfiguration` in CloudFormation) with `Path: /`, `Interval: 10`, `Timeout: 5`, but this is a health check, not an SLO. No dashboards, no error budget tracking.
- **Gap**: No SLOs mean no way to measure whether the platform meets the reliability needs of the agentic use case. The agent needs sub-second response times for order status queries — without SLOs, degradation goes undetected.
- **Recommendation**: Define SLOs for the agent-critical paths: order status query p99 latency < 500ms, return submission success rate > 99.5%, API availability > 99.9%. Create CloudWatch alarms and dashboards. Implement error budget tracking to gate agent feature releases.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback mechanism. `deploy.sh` runs `docker-compose up -d` with no rollback command. No blue/green deployment, no canary, no feature flags. No CodeDeploy rollback triggers. App Runner supports automatic rollback on failed deployments, but no explicit configuration is set.
- **Gap**: If a broken deployment is pushed (e.g., an API change that breaks the agent's tools), there is no way to automatically roll back. Manual intervention is required.
- **Recommendation**: When migrating to ECS, implement blue/green deployments via CodeDeploy with automatic rollback on CloudWatch alarm triggers. Implement feature flags for agent features (e.g., gradually enable agent return processing). Version agent prompts and configurations with rollback capability.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage exists in the application. No token counting, no cost attribution, no usage tracking of any kind.
- **Gap**: When the agent is built, LLM API calls (Bedrock) will incur per-token costs. Without cost tracking, the agent's operational cost is invisible. A misconfigured agent could generate thousands of dollars in LLM costs before detection.
- **Recommendation**: Implement per-request token usage tracking in the agent service. Log input/output token counts per conversation turn. Create CloudWatch custom metrics for `bedrock_input_tokens`, `bedrock_output_tokens`, and `bedrock_cost_usd`. Set up billing alerts. Implement tiered retention for agent conversation logs.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics. No business outcome tracking. Order counts, return rates, and inventory levels are stored in MySQL but not published as metrics. No dashboards tracking resolution rates, customer satisfaction, or agent accuracy.
- **Gap**: When the agent is processing returns and restocking inventory, there are no business metrics to measure its impact. Cannot track: returns processed per hour, agent resolution rate, inventory restocking accuracy, customer satisfaction scores.
- **Recommendation**: Publish custom CloudWatch metrics for: orders_created, returns_processed, returns_approved, inventory_restocked, agent_conversations_completed. Create a CloudWatch dashboard tracking agent business impact alongside infrastructure metrics.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection configured. No CloudWatch anomaly detection, no error rate alarms, no latency monitoring. No PagerDuty, OpsGenie, or any alerting integration.
- **Gap**: An agent in a reasoning loop (calling the same API repeatedly) or hallucinating (processing invalid returns) will go undetected. No behavioral baseline monitoring for agent patterns.
- **Recommendation**: Enable CloudWatch anomaly detection on API error rates and latency. Set up alerts for unusual patterns: spike in return requests (agent may be auto-approving incorrectly), unusually high API call volume from the agent, sudden inventory changes. Implement behavioral baseline monitoring specific to agent call patterns.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Manual deployment via `deploy.sh` which runs `docker-compose build` and `docker-compose up -d`. No canary, no blue/green, no rolling deployment strategy. App Runner supports rolling deployments natively, but the local deployment path has no strategy.
- **Gap**: Direct-to-production deployment with no gradual rollout. Agent deployments (new prompts, new tools, model upgrades) are high-risk without canary/blue-green capability.
- **Recommendation**: When migrating to ECS, implement blue/green deployments via CodeDeploy with ALB target group switching. Use canary deployments for agent changes: route 10% of agent traffic to the new version, monitor eval metrics, then promote. Implement GitOps with ArgoCD (preferred) for declarative deployment.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found anywhere in the repository. No `tests/` directory, no PHPUnit configuration, no integration test suites, no API test collections (Postman/Newman), no contract tests. Zero test coverage.
- **Gap**: No way to verify that API changes don't break the agent's tools. When the agent is built, changes to the PHP API could silently break agent functionality with no test to catch it.
- **Recommendation**: Create integration test suites covering all API endpoints the agent will use. Implement contract tests (Pact or similar) between the agent service and the monolith API. Run these in CI on every commit. Prioritize: order status query, return submission, inventory check, warehouse assignment.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, no SSM Automation documents, no Lambda remediation functions, no Step Functions for incident workflows. No self-healing patterns. No incident response documentation of any kind.
- **Gap**: When the agent encounters errors (database timeouts, API failures), there is no automated response. The agent will retry blindly without guidance, and operators have no automated remediation path.
- **Recommendation**: Create machine-readable runbooks (YAML/JSON) for common incidents: database connection failure, high error rate, agent timeout. Implement SSM Automation documents for automated remediation (e.g., restart ECS task, failover RDS). Define escalation paths for agent-specific incidents (agent processing incorrect returns).

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file, no team ownership documentation, no observability governance framework. No SLO ownership model. No platform team tooling for centralized observability. No evidence of shared responsibility model.
- **Gap**: No one owns the observability of this application. When the agent is deployed, there will be no clear owner for agent-level SLOs (task success rate, hallucination rate, tool error rate). Accountability for agent failures will be undefined.
- **Recommendation**: Define ownership: platform team owns infrastructure observability (ECS, RDS, networking), product team owns agent observability (eval metrics, conversation quality, tool success rate). Create CODEOWNERS file mapping alert ownership. Implement observability-as-a-product with shared dashboards and SLO contracts between teams.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Not Triggered | High | — | — | — |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps + Move to AI — CI/CD pipeline and agent service can be built simultaneously with no dependencies.

**Parallel Track 2**: Move to Cloud Native — begins after initial containerization foundations are established in the DevOps track.

**Sequential Dependencies**: Move to Modern DevOps (CI/CD pipeline) should be established before Move to Cloud Native (decomposition requires automated deployment). Move to AI agent service can start immediately by calling the existing monolith APIs.

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Tightly coupled monolith in single `index.php` with 8 domains sharing one database
  - APP-Q3: Score 1/4 — 100% synchronous communication, no async patterns
  - APP-Q10: Score 1/4 — No async handling for long-running processes (return approval is synchronous multi-step transaction)
- **Contextual Guard**: APP-Q4 = 1 (< 3), guard passes — monolith requires decomposition
- **Current State**: Single PHP monolith (`index.php`) with all domains (orders, inventory, payments, returns, warehouses, users) tightly coupled via shared MySQL database and foreign key relationships across domain boundaries.
- **Target State**: Modular services on ECS (preferred) with clear domain boundaries. Orders Service, Inventory Service, Returns Service each independently deployable with their own data stores. Agent interacts with each service as a distinct tool.
- **Key Activities**:
  1. Conduct domain modeling to identify bounded contexts (Orders, Inventory, Returns as priority services for the agent)
  2. Extract Inventory Service first (loosest coupling, clear domain, critical for agent restocking decisions)
  3. Implement API Gateway routing to gradually shift traffic from monolith to extracted services (Strangler Fig pattern)
  4. Introduce EventBridge for async communication between services (preferred over direct HTTP)
  5. Migrate to per-service databases (DynamoDB for inventory, RDS for orders)
- **Dependencies**: Move to Modern DevOps (CI/CD pipeline needed before service extraction)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Agent Foundations) and Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline, only manual `deploy.sh`
  - OPS-Q9: Score 1/4 — Manual deployment, no canary/blue-green
  - OPS-Q10: Score 1/4 — Zero test coverage
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: Manual deployment via `deploy.sh`, no CI/CD pipeline, no tests, no tracing, no structured logging. Infrastructure defined in CloudFormation but no GitOps workflow.
- **Target State**: Automated CI/CD pipeline with build, test, deploy stages. GitOps-driven deployment to ECS via Helm/ArgoCD (preferred). Blue/green deployments with automatic rollback. Full observability with tracing and structured logging.
- **Key Activities**:
  1. Create GitHub Actions CI/CD pipeline: build Docker image → push to ECR → run integration tests → deploy to ECS
  2. Implement structured JSON logging with correlation IDs
  3. Add X-Ray/OpenTelemetry distributed tracing
  4. Create integration test suites for agent-critical API endpoints
  5. Implement blue/green deployments via CodeDeploy with ALB
  6. Migrate IaC to Terraform (preferred) with GitOps workflow via ArgoCD
- **Dependencies**: None — this is the foundational track
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins) for CI/CD and logging, Phase 2 for advanced deployment strategies
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in the codebase
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG pipeline for knowledge retrieval
  - OPS-Q3: Score 1/4 — No evaluation framework for agent quality measurement
  - OPS-Q6: Score 1/4 — No LLM cost tracking infrastructure
- **Current State**: Pure PHP web application with zero AI integration. No agent framework, no vector database, no RAG pipeline, no eval framework, no LLM cost tracking.
- **Target State**: AI agent service on ECS (Python/Strands Agents SDK) that handles order status inquiries, processes returns, and manages inventory restocking. Bedrock Knowledge Base for RAG. Automated eval pipeline. Full LLM cost attribution.
- **Key Activities**:
  1. Build agent service in Python using Strands Agents SDK deployed on ECS
  2. Define MCP tools wrapping the monolith's existing JSON APIs (get-order-status, submit-return, check-inventory)
  3. Create Amazon Bedrock Knowledge Base with product catalog and return policy documents
  4. Implement RAG pipeline for customer inquiry resolution
  5. Build automated eval framework with golden datasets for order/return/inventory scenarios
  6. Implement LLM cost tracking with per-request token usage and CloudWatch custom metrics
- **Dependencies**: None for initial agent service (calls existing APIs). Knowledge Base and RAG depend on S3 content being created.
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins) for initial agent tools, Phase 2 for RAG and evals, Phase 3 for advanced capabilities
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

> This monolith would benefit from service extraction to create clear agent tool boundaries. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface — the JSON APIs at `/api/products`, `/api/orders/me`, `/api/orders/{id}/history`, `/api/returns`, and `/api/warehouses/assignment-options` provide sufficient coverage for the initial order status, returns, and inventory agent use case.

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Order Status Inquiry Agent** — Build an agent that queries order status, tracks shipments, and provides delivery estimates using the existing `/api/orders/me`, `/api/orders/{id}/history`, and `/api/carriers/shipping-options` endpoints.
   - **Leverages**: Existing JSON APIs return structured order data with status, tracking numbers, carrier info, and full status history via `order_status_history` table
   - **Effort**: Low
   - **Value**: Eliminates manual customer service inquiries about "where is my order?" — the most common support request. The agent can provide real-time status, tracking info, and estimated delivery dates.

2. **Inventory Lookup & Restocking Agent** — Build an agent that checks stock levels and recommends restocking using `/api/products` (returns `stock_quantity` per product) and warehouse capacity data from `/api/warehouses/assignment-options`.
   - **Leverages**: JSON API at `/api/products` returns complete inventory data including stock quantities, categories, and warehouse locations
   - **Effort**: Low
   - **Value**: Enables proactive inventory management. The agent can alert when stock drops below thresholds and recommend restocking quantities based on order velocity and warehouse capacity.

3. **Return Request Assistant Agent** — Build an agent that guides customers through the return process and submits return requests via `/api/returns` (POST endpoint accepts `order_id` and `reason`).
   - **Leverages**: Existing `/api/returns` endpoint with structured JSON response including return ID and status
   - **Effort**: Medium
   - **Value**: Reduces the 24-48 hour manual review cycle by automating the return intake process. The agent can validate return eligibility, explain the process, and submit the request — reducing time-to-resolution from days to minutes for the initial submission.

4. **Natural Language Data Query Agent** — Build a data query agent that translates customer questions into SQL queries against the MySQL database with its clearly defined 9-table schema (orders, inventory, payments, returns, etc.).
   - **Leverages**: Clean relational schema with no stored procedures — all tables defined in `init_db()` with clear column names and relationships
   - **Effort**: Medium
   - **Value**: Enables customer service reps to ask questions like "How many returns did we process last week?" or "What's the average order value for customer X?" without writing SQL.

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

1. **Generate OpenAPI specs for agent-critical endpoints** — Document the `/api/orders/me`, `/api/orders/{id}/history`, `/api/returns`, `/api/products`, `/api/warehouses/assignment-options` endpoints as OpenAPI 3.0. This unblocks agent tool definitions.
2. **Build initial agent service on ECS** — Create a Python agent service using Strands Agents SDK with three tools: get-order-status, submit-return, check-inventory. Deploy as a separate ECS service (preferred) alongside the monolith. The agent calls the monolith's existing JSON APIs via HTTP.
3. **Create CI/CD pipeline** — Implement GitHub Actions workflow that builds Docker images, pushes to ECR, and deploys to ECS. Separate pipelines for monolith and agent service.
4. **Migrate secrets to AWS Secrets Manager** — Move database credentials out of `index.php` and `docker-compose.yml`. Update CloudFormation to create Secrets Manager secrets and inject via ECS task definition.
5. **Implement structured JSON logging** — Add monolog with JSON formatter to the PHP application. Include request_id, timestamp, and response status in every log entry. Ship to CloudWatch Logs via ECS logging driver.

### Phase 2 — Agent Foundations (Months 1–3)

1. **Implement Amazon Cognito for authentication** — Replace PHP session auth with JWT/OAuth2. Create a Cognito User Pool, migrate existing users. Issue client credentials tokens for the agent service. Add API Gateway (preferred) with Cognito authorizer in front of the ECS services.
2. **Create Amazon Bedrock Knowledge Base** — Store product documentation, return policies, and FAQ in S3. Configure Bedrock to index into OpenSearch Serverless for semantic search. Integrate with the agent for RAG-powered customer inquiry resolution.
3. **Build automated evaluation framework** — Create golden datasets for order status inquiries (50+ test cases), return processing (30+ test cases), and inventory restocking decisions (20+ test cases). Implement automated scoring in CI pipeline.
4. **Add distributed tracing (X-Ray/OpenTelemetry)** — Instrument the PHP application and agent service. Propagate trace IDs across agent → API → database calls. Enable end-to-end visibility for debugging agent failures.
5. **Introduce EventBridge for domain events** — Publish events for order-created, order-status-changed, return-requested, inventory-low. The agent subscribes to inventory-low events for proactive restocking recommendations.
6. **Migrate IaC to Terraform** — Convert CloudFormation template to Terraform modules (VPC, ECS, RDS, API Gateway). Implement GitOps with ArgoCD for deployment automation.
7. **Implement blue/green deployments** — Configure CodeDeploy with ALB for ECS services. Add CloudWatch alarm-based automatic rollback. Enable canary deployments for agent prompt/model changes.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

1. **Begin microservice extraction** — Extract Inventory Service first (loosest coupling, critical for agent restocking). Use Strangler Fig pattern with API Gateway routing. Deploy on ECS with its own DynamoDB (preferred) data store.
2. **Implement Step Functions workflows** — Orchestrate the return processing workflow (validate → approve → restock → refund → notify) and the fulfillment workflow. The agent triggers workflows as single tools instead of calling multiple endpoints sequentially.
3. **Add human approval workflows** — Implement Step Functions with `waitForTaskToken` for high-value return approvals (>$100). The agent submits the request, Step Functions pauses for human approval via SNS notification, then continues.
4. **Implement LLM cost tracking and anomaly detection** — Track per-request Bedrock token usage. Create CloudWatch dashboards for agent costs. Enable anomaly detection on API error rates, agent call patterns, and return processing volume.
5. **Deploy agent evaluation pipeline in CI** — Run golden dataset evaluations automatically before every agent deployment. Block deployments that decrease eval scores below threshold. Track eval metrics over time.
6. **Define SLOs and observability governance** — Set agent-level SLOs: order status query p99 < 500ms, return submission success rate > 99.5%, agent resolution rate > 85%. Assign ownership: platform team for infrastructure, product team for agent quality.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
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
- EKS Workshop — https://www.eksworkshop.com/

**Module 4: Move to Managed Databases:**
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

---

## Appendix: Evidence Index

| # | File | Key Findings |
|---|------|-------------|
| 1 | `index.php` | Main monolith application (~1,800 lines PHP). Contains all 8 business domains, 20+ API endpoints returning JSON, session-based auth, direct SQL via PDO, `init_db()` schema definitions, `seed_data()` sample data, order fulfillment workflow (7 steps), return processing, user management, hardcoded credential defaults. |
| 2 | `Dockerfile` | PHP 8.2-apache base image. Installs `pdo` and `pdo_mysql` extensions. Copies `index.php` and `.htaccess`. Exposes port 80. |
| 3 | `docker-compose.yml` | Defines two services: `mysql` (mysql:8.0 with plaintext credentials) and `monolith` (built from Dockerfile). Health checks configured. Local development only. |
| 4 | `deploy.sh` | Manual deployment script. Runs `docker-compose build` and `docker-compose up -d`. No CI/CD, no rollback, no testing. |
| 5 | `.htaccess` | Apache rewrite rules routing all requests to `index.php`. |
| 6 | `.gitignore` | Standard ignores for database files, logs, OS files, and IDE configs. |
| 7 | `infrastructure/monolith-apprunner.yaml` | CloudFormation template (~350 lines). Defines: VPC (10.0.0.0/16), 2 private subnets, RDS MySQL 8.4.8 (encrypted, 7-day backup retention), App Runner service, ECR repository, WAFv2 (IP whitelisting), IAM roles (CloudWatchLogsFullAccess + ECR access), AutoScaling (min 1, max 3), VPC Connector. |
| 8 | *(absent)* `.github/workflows/` | No CI/CD pipeline definitions found. |
| 9 | *(absent)* `openapi.yaml` / `swagger.json` | No API documentation found. |
| 10 | *(absent)* `tests/` | No test directory or test files of any kind found. |
| 11 | *(absent)* `requirements.txt` / `package.json` / `composer.json` | No dependency manifests found (PHP has no package manager config). |
| 12 | *(absent)* `*.tf` files | No Terraform files found. IaC is CloudFormation only. |
| 13 | *(absent)* `CODEOWNERS` | No code ownership file found. |
| 14 | *(absent)* Any AI/ML files | No Bedrock, LangChain, OpenAI, or agent framework references found. |
