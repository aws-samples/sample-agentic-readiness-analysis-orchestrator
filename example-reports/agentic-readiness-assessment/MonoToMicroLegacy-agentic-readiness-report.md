# Agentic Readiness Assessment Report
**Target**: MonoToMicroLegacy (./services/unishop-monolith-to-microservices/MonoToMicroLegacy)
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

This legacy Java 8 monolith (Spring Boot 2.1.x) running on raw EC2 with a MySQL database represents a significant modernization challenge for agentic AI enablement. The application has **no API documentation** (blocking agent tool discovery), **no AI/agent frameworks**, **no vector database or RAG pipeline**, **no Infrastructure as Code**, **no CI/CD pipeline**, and **hardcoded database credentials** — all fundamental gaps for building customer-facing AI agents for support and order management. The strongest area is Data Foundations (2.0/4.0), where a clean MySQL schema with no stored procedures and a consistent repository pattern provide a foundation for data-layer modernization. Every other category scores below 1.5, indicating the application requires substantial foundational work before agents can reliably interact with it.

### Overall Score: 1.33 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.1 / 4.0 | ❌ |
| Application Architecture | 1.5 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.1 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

## Top Priorities (Critical Gaps)

### 1. APP-Q2 — API Documentation (Score: 1/4 ❌)
**What**: No OpenAPI/Swagger specs exist for any endpoint. No `springdoc` or `springfox` dependencies in `build.gradle`. No `@ApiOperation` annotations on controllers.
**Why it blocks agents**: AI agents discover and invoke APIs through machine-readable OpenAPI specifications. Without them, a customer support agent cannot programmatically understand what endpoints are available (`/unicorns`, `/unicorns/basket/{userUuid}`, `/user`, `/user/login`), what parameters they accept, or what responses they return. This is the single biggest blocker for agentic AI enablement.
**First step**: Add `springdoc-openapi-ui` dependency to `build.gradle` and annotate controllers with `@Operation` and `@Schema` to auto-generate OpenAPI specs.

### 2. APP-Q13 — AI/Agent Frameworks (Score: 1/4 ❌)
**What**: No AI or agent framework integration exists. No Amazon Bedrock SDK, no LangChain, no Spring AI, no Strands Agents SDK. The AWS SDK v1 (`1.11.567`) in `build.gradle` is used only for `EC2MetadataUtils` in `HealthController.java`.
**Why it blocks agents**: Customer-facing support and order management agents require an agent framework to orchestrate LLM reasoning, tool invocation, and conversation management. Without any framework, there is no foundation to build agent capabilities on.
**First step**: Add the Strands Agents SDK or Amazon Bedrock Agent Runtime SDK (requires AWS SDK v2 upgrade) as a dependency and create a proof-of-concept agent for order lookup.

### 3. DATA-Q1/Q2/Q3 — Vector Database & RAG Pipeline (Score: 1/4 ❌)
**What**: No vector database (OpenSearch, pgvector, Bedrock Knowledge Bases), no embedding generation, no RAG pipeline. The application only uses MySQL for structured e-commerce data.
**Why it blocks agents**: A customer support agent needs semantic search over product catalogs, order histories, and support documentation to provide accurate, context-aware responses. Without vector storage and RAG, agents cannot retrieve relevant knowledge and will hallucinate or provide incomplete answers.
**First step**: Deploy Amazon OpenSearch Service with k-NN plugin or enable Amazon Bedrock Knowledge Bases, and create an embedding pipeline for product catalog data from the `unicorns` table.

### 4. SEC-Q1 — Secret Management (Score: 1/4 ❌)
**What**: Database credentials are hardcoded in plaintext in `application.properties` (`username: MonoToMicroUser`, `password: MonoToMicroPassword`). No AWS Secrets Manager, no HashiCorp Vault, no encrypted configuration.
**Why it blocks agents**: Agents deployed in production require secure credential management. Hardcoded secrets prevent credential rotation, create security vulnerabilities, and block compliance requirements for AI systems handling customer data (PII in `unicorn_user` table includes email, first_name, last_name).
**First step**: Migrate credentials to AWS Secrets Manager and update `application.properties` to use environment variables or Spring Cloud AWS Secrets Manager integration.

### 5. INF-Q5/Q6 — Infrastructure as Code & CI/CD (Score: 1/4 ❌)
**What**: Zero IaC files (no Terraform, no CDK, no CloudFormation, no Helm). Zero CI/CD pipeline definitions (no GitHub Actions, no CodePipeline, no Jenkinsfile, no `buildspec.yml`).
**Why it blocks agents**: Safe agent deployment requires automated, repeatable infrastructure provisioning and deployment pipelines. Without IaC and CI/CD, agent model updates, prompt changes, and tool configurations cannot be safely tested, deployed, or rolled back. Manual deployments introduce unacceptable risk for autonomous systems.
**First step**: Create a Terraform configuration for the existing EC2 + MySQL infrastructure and a GitHub Actions workflow with build, test, and deploy stages.

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: The application runs on raw EC2 instances. `HealthController.java` explicitly calls `EC2MetadataUtils.getInstanceInfo()` to retrieve instance metadata (account ID, availability zone, instance ID, instance type, region). No ECS, EKS, Lambda, or Fargate definitions exist anywhere in the repository. No Dockerfile is present. The app runs as a standalone Spring Boot JAR on port 8080 (`server.port=8080` in `application.properties`).
- **Gap**: 100% of compute is raw EC2 with no container orchestration or managed compute.
- **Recommendation**: Containerize the application by creating a Dockerfile, then deploy to Amazon ECS on Fargate. Use Terraform to define the ECS service, task definition, and ECR repository. Avoid Lambda/serverless per stated preferences.

#### INF-Q2: Databases
- **Score**: 2/4 🟠
- **Finding**: `application.properties` configures a MySQL JDBC connection: `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The endpoint is environment-variable driven (`MONO_TO_MICRO_DB_ENDPOINT`), suggesting possible RDS usage, but no IaC exists to confirm managed database configuration, Multi-AZ failover, automated backups, or read replicas. `build.gradle` includes `mysql-connector-java:8.0.11`. The `create_tables.sql` schema uses InnoDB engine with UTF8MB4 charset.
- **Gap**: No IaC confirming managed RDS configuration. No evidence of automated failover, Multi-AZ deployment, or backup policies. Database management state is unknown.
- **Recommendation**: Define the MySQL database as Amazon RDS for MySQL (or Aurora MySQL) in Terraform with Multi-AZ enabled, automated backups, and encryption at rest. Pin the engine version explicitly.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service found. No AWS Step Functions (`aws_sfn_*`), no Temporal SDK, no Camunda, no workflow YAML definitions. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` consists of simple CRUD operations without multi-step workflows.
- **Gap**: No dedicated workflow orchestration. Agent workflows (multi-step order management, support escalation) have no orchestration infrastructure.
- **Recommendation**: Implement AWS Step Functions for multi-step agent workflows such as order processing, refund handling, and support ticket escalation. Define workflows in Terraform with `aws_sfn_state_machine`.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or any messaging infrastructure found. The full AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567`) is included in `build.gradle` but no messaging client is instantiated anywhere in the codebase. All operations are synchronous HTTP request/response.
- **Gap**: Zero async messaging capability. Agent-triggered operations (order updates, notifications) cannot be decoupled from the request path.
- **Recommendation**: Introduce Amazon SQS for order processing queues and Amazon EventBridge for domain event publishing (e.g., `OrderPlaced`, `BasketUpdated`). Use Amazon SNS for customer notifications. Define all resources in Terraform.

#### INF-Q5: Infrastructure as Code
- **Score**: 1/4 ❌
- **Finding**: Zero IaC files in the repository. No `.tf` files, no CDK stacks, no CloudFormation templates, no Helm charts, no Kustomize configs. The entire infrastructure (EC2 instances, database, networking) is presumably provisioned manually.
- **Gap**: 0% IaC coverage. Infrastructure changes are manual, unreproducible, and unauditable.
- **Recommendation**: Create a Terraform project to codify the existing infrastructure: VPC, subnets, security groups, EC2/ECS, RDS, and API Gateway. Start with the database and networking layers, then add compute. Adopt GitOps workflow with Helm for future ECS/EKS deployments.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/` directory, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`. The `build.gradle` defines a `bootJar` task and an `unpack` task, plus a commented-out Docker plugin, but no automated pipeline triggers build, test, or deploy.
- **Gap**: Zero deployment automation. No automated testing, building, or deployment. Manual deploys prevent safe, rapid iteration on agent capabilities.
- **Recommendation**: Create a GitHub Actions workflow with stages: lint → build → test → container image build → push to ECR → deploy to ECS. Use Terraform for infrastructure changes in a separate pipeline. Adopt GitOps practices per stated preferences.

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: No API Gateway, ALB, or CloudFront found. The application exposes HTTP endpoints directly on port 8080 (`server.port=8080` in `application.properties`). No throttling, no request validation, no auth at the gateway level. `ResourceServerConfig.java` permits all requests with `.authorizeRequests().anyRequest().permitAll()`.
- **Gap**: No managed API entry point. Direct service exposure without throttling, auth, or request validation. Agents making high-frequency API calls have no protection layer.
- **Recommendation**: Deploy Amazon API Gateway (REST or HTTP API) in front of the application. Configure throttling, request validation, and API key-based usage plans. Define in Terraform with `aws_apigatewayv2_api`.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or streaming infrastructure found. No streaming SDK imports. No event-driven data pipelines.
- **Gap**: No real-time streaming capability. Agent activity events, order events, and user interaction events cannot be streamed for analytics or real-time processing.
- **Recommendation**: Implement Amazon EventBridge for domain event streaming when the application is decomposed. Consider Amazon Kinesis Data Streams if real-time analytics on agent interactions are needed.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, or security group definitions in IaC. `ResourceServerConfig.java` permits all requests (`.authorizeRequests().anyRequest().permitAll()`). `Application.java` configures `WebSecurityConfigurerAdapter` to ignore all OPTIONS requests globally as a "workaround" (per code comment: "not recommended for production usage!").
- **Gap**: No evidence of network segmentation, private subnets, or least-privilege security groups. The application appears to be directly exposed without network-level protections.
- **Recommendation**: Define a VPC with public/private subnets in Terraform. Place the application in private subnets behind an ALB or API Gateway in the public subnet. Configure security groups with least-privilege ingress/egress rules.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No ASG, ECS service auto-scaling, or scaling policies found. Running on EC2 with no evidence of auto-scaling configuration.
- **Gap**: No auto-scaling. Agent traffic can be bursty (e.g., support inquiries during peak hours). Without auto-scaling, the application cannot handle demand spikes.
- **Recommendation**: When containerized on ECS, configure ECS Service Auto Scaling with target tracking on CPU/memory utilization. Define scaling policies in Terraform with `aws_appautoscaling_target` and `aws_appautoscaling_policy`.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`) with Spring Boot 2.1.x (`spring-boot-gradle-plugin:2.1.0.RELEASE`, Spring Boot plugin `2.1.6.RELEASE`). Java has a growing agent framework ecosystem (Spring AI requires Spring Boot 3.x+; Strands Agents SDK supports Java), but Java 8 is EOL and Spring Boot 2.1.x is unsupported.
- **Gap**: Java 8 and Spring Boot 2.1.x are EOL. Modern agent frameworks (Spring AI, Strands Agents) require Java 17+ and Spring Boot 3.x+. The outdated platform blocks adoption of current AI tooling.
- **Recommendation**: Upgrade to Java 17 and Spring Boot 3.2+. This unblocks Spring AI and modern AWS SDK v2 integration. Plan a phased upgrade: Java 11 → Java 17, Spring Boot 2.7 → 3.2.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI or Swagger specifications found. No `swagger.json`, no `openapi.yaml`. No `springdoc-openapi` or `springfox` dependencies in `build.gradle`. No `@ApiOperation`, `@Operation`, or `@Schema` annotations on any controller. API endpoints are only discoverable by reading source code: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`, `GET /data`.
- **Gap**: Complete absence of machine-readable API documentation. Agents cannot discover, validate, or invoke APIs without OpenAPI specs. This is the #1 blocker for agent tool integration.
- **Recommendation**: Add `springdoc-openapi-ui` dependency and annotate all controllers with `@Operation`, `@Parameter`, `@Schema`, and `@ApiResponse`. Generate OpenAPI 3.0 spec and publish at `/v3/api-docs`.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous HTTP communication. All controller methods in `UnicornController.java`, `BasketController.java`, `UserController.java`, and `DataReplicationController.java` use synchronous `@RequestMapping` with `ResponseEntity<>` returns. No message publishing, no event-driven handlers, no `@Async` annotations, no queue consumers.
- **Gap**: Zero async capability. All operations block the HTTP thread. Agent workflows requiring background processing (e.g., order fulfillment, email notifications) have no async path.
- **Recommendation**: Introduce Amazon SQS consumers for order processing and Amazon EventBridge for domain event publishing. Add `@Async` for non-critical operations. Keep REST APIs synchronous for agent tool calls but decouple downstream processing.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single deployable Spring Boot application. All domains share one codebase and one MySQL database (`unishop` schema with 3 tables). However, identifiable domain separation exists: `UnicornController`/`UnicornService`/`UnicornRepository` (product catalog), `BasketController`/`UnicornService` (shopping cart), `UserController`/`UserService`/`UserRepository` (user management), `HealthController`/`HealthService`/`HealthRepository` (health checks). Database coupling is moderate — `unicorns_basket` table links user UUIDs to unicorn UUIDs across domains via the `uuid` and `unicornUuid` columns.
- **Gap**: Monolith with identifiable modules but significant database coupling. Service boundaries are unclear — `BasketController` uses `UnicornService` rather than a dedicated `BasketService`. Shared `CoreModel` base class couples all domain models.
- **Recommendation**: For agent tool boundaries, extract the Basket/Order domain as the first microservice (highest business value for support agents). Use the Strangler Fig pattern with API Gateway routing.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: JSON responses via Spring Boot's Jackson auto-configuration. Models use `@JsonInclude(JsonInclude.Include.NON_NULL)` (in `Unicorn.java`, `User.java`) and `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` (in `CoreModel.java`). Controllers return typed `ResponseEntity<Collection<Unicorn>>`, `ResponseEntity<UnicornBasket>`, `ResponseEntity<User>`. The `@JsonIgnore` annotation on `CoreModel` fields (`id`, `creationDate`, `active`) hides internal fields from responses.
- **Gap**: JSON responses are consistent but lack standardized error response format. Error cases return empty `ResponseEntity` with HTTP status only (no error body). No HATEOAS or hypermedia links.
- **Recommendation**: Standardize error responses with a consistent JSON error schema (`{ "error": "...", "code": "...", "message": "..." }`). This helps agents parse and handle errors programmatically.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No dedicated workflow orchestration. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` consists of simple CRUD operations: get unicorns, add/remove from basket, create user, get user by email. No multi-step workflows, no state machines, no saga patterns.
- **Gap**: No workflow orchestration for complex agent operations like order processing, refund handling, or support escalation paths.
- **Recommendation**: Implement AWS Step Functions for multi-step agent workflows. Start with a "support ticket resolution" workflow that orchestrates order lookup, status check, and resolution actions.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: Partial idempotency via SQL `INSERT IGNORE` in `UnicornMapper.xml` (`addUnicornToBasket`) and `UserMapper.xml` (`create`). The `UNIQUE` constraints on `unicorns_basket(uuid, unicornUuid)` and `unicorn_user(email)` prevent duplicate inserts. However, no application-level idempotency keys exist — no `Idempotency-Key` headers, no deduplication IDs, no idempotent `DELETE` handling.
- **Gap**: Database-level deduplication only. No API-level idempotency for agent retries. Agents retrying failed HTTP calls may cause unintended side effects on endpoints without `INSERT IGNORE`.
- **Recommendation**: Add `Idempotency-Key` header support to all write endpoints. Implement an idempotency table or use DynamoDB for idempotency token storage when migrating to managed databases.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. No API Gateway throttling, no WAF rules, no application-level rate limiting middleware (no `spring-boot-starter-cache` with rate limit, no bucket4j, no resilience4j rate limiter). `ResourceServerConfig.java` permits all requests without any throttling.
- **Gap**: Zero rate limiting. Misbehaving agents or agent loops could overwhelm the application with unbounded requests.
- **Recommendation**: Deploy API Gateway with throttling (burst and rate limits per API key). Add application-level rate limiting with `bucket4j-spring-boot-starter` as a defense-in-depth measure.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry logic, or timeout configurations. No Resilience4j, Hystrix, or retry decorators in dependencies. Repository methods (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) catch all exceptions with `catch (Exception e) { e.printStackTrace(); return null/false; }` — silently swallowing errors and returning null.
- **Gap**: Error handling is fundamentally broken. Exceptions are swallowed, producing null responses that propagate as `BAD_REQUEST` HTTP responses without useful error information. Agents cannot distinguish between "not found" and "system error".
- **Recommendation**: Add Resilience4j for circuit breaker and retry patterns on database calls. Replace exception swallowing with proper error propagation and structured error responses. Configure timeouts on all external calls.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: All current operations are short-lived CRUD queries (SELECT, INSERT, DELETE). No operations appear to exceed 30 seconds. However, no async infrastructure exists for future long-running operations that agents may trigger (e.g., bulk order exports, report generation, data replication via `DataReplicationController.java`).
- **Gap**: No async job infrastructure. The `DataReplicationController.java` endpoint (`GET /data`) fetches all baskets synchronously — this could become a long-running operation at scale.
- **Recommendation**: Implement an async job pattern using Amazon SQS + ECS worker tasks for operations that may exceed 30 seconds. Add a job status polling API endpoint for agents to check progress.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy. Endpoints use unversioned paths: `/unicorns`, `/unicorns/basket`, `/user`, `/health`, `/data`. No `/v1/` prefix, no `Accept-Version` headers, no versioning annotations, no changelog.
- **Gap**: No versioning means breaking API changes will break existing agent tool configurations. Agents calling the API have no contract stability guarantees.
- **Recommendation**: Introduce URL path versioning (e.g., `/v1/unicorns`) via API Gateway routing. Document API contracts and publish a changelog. This enables safe evolution of APIs while agents continue using stable versions.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: No service discovery mechanism. The application is a single monolith with no inter-service communication. No AWS Cloud Map, App Mesh, Consul, or environment-variable-based service discovery.
- **Gap**: Not applicable in current monolithic architecture, but will be essential when decomposing into microservices for agent tool isolation.
- **Recommendation**: When decomposing, use AWS Cloud Map for service discovery and API Gateway as the unified entry point for agent tool invocation across services.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework usage found. No Amazon Bedrock SDK, no LangChain, no LangGraph, no CrewAI, no Strands Agents SDK, no Spring AI, no OpenAI client, no MCP SDK. The AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567`) in `build.gradle` is used only for `EC2MetadataUtils` in `HealthController.java`. No LLM-related imports anywhere in the codebase.
- **Gap**: Complete absence of AI/agent infrastructure. No foundation exists for building the customer-facing support and order management agents stated in the goal context.
- **Recommendation**: Integrate the Strands Agents SDK (Java-compatible) or Amazon Bedrock Agent Runtime. Build a proof-of-concept agent that uses the existing REST API as tools for order lookup (`GET /unicorns/basket/{userUuid}`) and product search (`GET /unicorns`).

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found anywhere in the repository. No OpenSearch with k-NN plugin, no Aurora pgvector extension, no S3 Vectors, no Bedrock Knowledge Bases, no Pinecone/Weaviate/Chroma imports. The only database is MySQL accessed via MyBatis.
- **Gap**: No vector store for semantic search. Customer support agents cannot perform similarity searches on product descriptions, support articles, or order histories.
- **Recommendation**: Deploy Amazon OpenSearch Service with the k-NN plugin for vector similarity search over product catalog and support knowledge. Alternatively, use Amazon Bedrock Knowledge Bases for a fully managed RAG solution.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists, so there is no management to evaluate.
- **Gap**: No vector database infrastructure of any kind.
- **Recommendation**: Use a fully managed vector database service — Amazon OpenSearch Service (managed) or Amazon Bedrock Knowledge Bases — to avoid self-management overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline found. No embedding model calls (Bedrock Titan, OpenAI ada), no document chunking/splitting code, no similarity search patterns, no Bedrock Knowledge Base integration.
- **Gap**: No RAG capability. Support agents cannot retrieve contextual product information or customer order context to generate accurate, grounded responses.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases: create embeddings for product catalog data (from `unicorns` table), support documentation, and order FAQs. Use Bedrock's managed chunking and indexing.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source — MySQL database (`unishop` schema) with 3 tables (`unicorns`, `unicorns_basket`, `unicorn_user`). Connection configured in `application.properties` via `spring.datasource.url`. All data access goes through one `DataSource` bean configured in `MyBatisConfig.java`.
- **Gap**: None. Minimal data source sprawl.
- **Recommendation**: Maintain this simplicity as the application evolves. When introducing additional data stores (vector DB, cache, DynamoDB), use a unified data access abstraction layer.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Data is accessed through a layered repository pattern: Controller → Service → Repository → MyBatis Mapper → MySQL. `UnicornRepositoryImpl.java` and `UserRepositoryImpl.java` encapsulate SQL execution. `MyBatisConfig.java` configures all three mappers centrally. However, this is direct database access — no API-mediated data layer.
- **Gap**: Direct DB connections from the application layer. When agents need data, they must go through the application's REST endpoints, but those endpoints directly couple to database operations with no abstraction for future data source changes.
- **Recommendation**: Maintain the repository pattern as-is during containerization. When decomposing, expose data access through well-defined API contracts per service domain, enabling agents to access data through stable API tools.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no Textract, no document parsing libraries. Only structured data in MySQL tables. Product images are stored as string references (`image` column in `unicorns` table stores names like `UnicornFloat`, `UnicornHipHop`) — likely referencing external image files, but no S3 integration is present.
- **Gap**: No unstructured data handling. Support agents cannot process uploaded documents, parse customer emails, or analyze product images.
- **Recommendation**: Implement S3 storage for product images and customer documents. Add Amazon Textract for document parsing in support workflows. Create an S3-triggered pipeline for indexing unstructured content into the RAG system.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `database/create_tables.sql` provides complete schema definitions for all 3 tables with column types, constraints (`UNIQUE`, `PRIMARY KEY`), and engine specifications (`InnoDB`, `UTF8MB4`). 10 seed data `INSERT` statements for the `unicorns` table. No Flyway, Liquibase, or Alembic migration framework. No JSON Schema files. No schema registry. No schema versioning.
- **Gap**: Schema is defined but not versioned or managed. Changes to the schema are untracked, making it risky for agents to rely on schema stability.
- **Recommendation**: Adopt Flyway or Liquibase for schema migration management. Document the schema in JSON Schema format for agent consumption. Version schema changes alongside application code.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Unified data access layer via MyBatis + Spring Repository pattern. `MyBatisConfig.java` centralizes all mapper configuration. `UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, and `HealthRepositoryImpl.java` provide a consistent interface pattern. All SQL is defined in XML mapper files (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`), not scattered across source code.
- **Gap**: Tightly coupled to MySQL/MyBatis. The mapper XMLs contain MySQL-specific SQL. Switching to DynamoDB or Aurora PostgreSQL would require rewriting all data access.
- **Recommendation**: When migrating to managed databases (RDS/Aurora or DynamoDB), replace MyBatis with a more portable ORM (Spring Data JPA) or implement a domain-specific data access interface that abstracts the underlying store.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist, so no freshness mechanism is relevant. No event-driven embedding refresh triggers, no scheduled re-indexing pipelines, no CDC patterns.
- **Gap**: No embedding infrastructure to keep fresh.
- **Recommendation**: When implementing RAG (DATA-Q3), include an event-driven embedding refresh pipeline. Use DynamoDB Streams or Amazon EventBridge to trigger re-embedding when product catalog data changes.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 2/4 🟠
- **Finding**: `build.gradle` includes `mysql-connector-java:8.0.11` (released April 2018). No IaC exists to specify the actual MySQL server engine version. The connector version suggests MySQL 8.x, but the actual server version is unknown from the repository alone. No explicit version pinning in any infrastructure configuration.
- **Gap**: Database engine version is not explicitly managed or pinned in IaC. MySQL 8.0 has an EOL date. Without version tracking, there is no proactive upgrade path.
- **Recommendation**: When creating Terraform for RDS, explicitly pin the engine version (`engine_version = "8.0.35"` or later). Set up a quarterly review of engine version support status. Consider migrating to Aurora MySQL for longer support windows.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: `create_tables.sql` contains only `CREATE TABLE` and `INSERT` statements. No stored procedures, no triggers, no functions, no views. MyBatis mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) contain standard SQL (SELECT, INSERT, DELETE, JOIN) with no proprietary MySQL constructs beyond `INSERT IGNORE` and `CURRENT_TIMESTAMP`. All business logic resides in the Java application layer.
- **Gap**: None. Clean schema with no stored procedure dependencies.
- **Recommendation**: Maintain this clean separation. The absence of stored procedures makes database migration (MySQL → Aurora MySQL, or to DynamoDB for the basket) straightforward.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded in plaintext in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. The database endpoint uses an environment variable (`${MONO_TO_MICRO_DB_ENDPOINT}`), but credentials are static plaintext. No AWS Secrets Manager, no HashiCorp Vault, no encrypted configuration. No `secretsmanager` client usage despite the full AWS SDK being included.
- **Gap**: Hardcoded credentials in source control. No secret rotation capability. Critical security vulnerability for any production deployment, especially for AI agents that may need to authenticate to multiple services.
- **Recommendation**: Migrate credentials to AWS Secrets Manager. Use Spring Cloud AWS Secrets Manager integration or environment variable injection from Secrets Manager at deployment time. Define the secret in Terraform.

#### SEC-Q2: IAM Least Privilege
- **Score**: 1/4 ❌
- **Finding**: No IAM policies defined in the repository. No IaC with IAM roles or policies. The full AWS SDK (`com.amazonaws:aws-java-sdk:1.11.567`) is bundled — the entire SDK including every service module — rather than importing only required service modules. No evidence of scoped IAM roles for the application.
- **Gap**: No defined IAM roles or policies. The application likely relies on an EC2 instance profile with unknown permissions. Agent workloads require precisely scoped IAM roles for each tool/service interaction.
- **Recommendation**: Create per-service IAM roles in Terraform with least-privilege policies. Scope permissions to only required actions (e.g., `rds-db:connect`, `sqs:SendMessage`, `bedrock:InvokeModel`). Replace the full AWS SDK with individual service modules.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: Spring Security OAuth2 libraries are included in `build.gradle` (`spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`, `spring-security-jwt:1.0.9.RELEASE`). `ResourceServerConfig.java` has `@EnableResourceServer` annotation. However, all requests are permitted (`.authorizeRequests().anyRequest().permitAll()`). `@PreAuthorize("permitAll()")` is on every controller method. JWT infrastructure exists but is completely non-enforcing.
- **Gap**: OAuth2/JWT libraries are present but authentication is disabled. User identity is not propagated — `UserController` identifies users by email in request body, not by authenticated token. Agent actions cannot be attributed to specific users.
- **Recommendation**: Enable OAuth2 resource server authentication by configuring a JWT issuer (Amazon Cognito). Replace `permitAll()` with role-based access control. Propagate user identity from JWT tokens through service calls.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration. No audit logging infrastructure. `HealthController.java` uses `System.out.println()` for logging. Repository implementations use `e.printStackTrace()`. No structured audit trail for any operations (user creation, basket modifications, data access).
- **Gap**: Zero audit capability. Agent actions (what the agent did, on behalf of which user, when) are completely untraceable. This is a compliance and safety risk for customer-facing AI agents.
- **Recommendation**: Implement CloudTrail for API-level auditing. Add structured application-level audit logging for all state-changing operations. Log agent decision chains with correlation IDs for traceability.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. No API Gateway throttle settings, no WAF rate rules, no application-level rate limiting. All endpoints are open to unlimited requests.
- **Gap**: No rate limits. AI agents can make rapid successive API calls; without rate limits, a single misbehaving agent could exhaust system resources.
- **Recommendation**: Deploy API Gateway with per-API-key usage plans and throttling (burst/rate limits). Configure WAF rate-based rules for DDoS protection. This is especially critical for agent-facing APIs.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction. `User.java` model exposes `email`, `firstName`, `lastName` directly in API responses (via `@JsonInclude`). `UserMapper.xml` returns `user.email`, `user.first_name`, `user.last_name` in SELECT queries. Exception stack traces are printed to stdout via `e.printStackTrace()` in all repository implementations, potentially exposing sensitive data in logs.
- **Gap**: PII is returned unredacted in API responses and potentially leaked in error logs. Support agents handling customer data must comply with PII protection requirements.
- **Recommendation**: Add PII masking in logging (replace `e.printStackTrace()` with a structured logger with PII filters). Consider field-level redaction in API responses for non-essential PII. Enable Amazon Macie for data classification.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows. No Step Functions with human approval tasks (`waitForTaskToken`), no approval Lambda patterns, no approval API endpoints. No manual approval stages in any pipeline (no CI/CD exists).
- **Gap**: No human-in-the-loop approval mechanism. Customer-facing AI agents performing high-risk actions (refunds, account modifications, order cancellations) have no safety gate requiring human review.
- **Recommendation**: Implement Step Functions with `waitForTaskToken` for high-risk agent actions. Create an approval dashboard where human reviewers can approve/reject agent-proposed actions (e.g., refunds above a threshold, account deletions).

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS configuration found. No `kms_key_id` on any resource. No encryption-at-rest settings in any configuration file. No IaC to verify data store encryption. The database stores customer PII (email, names) without confirmed encryption.
- **Gap**: No evidence of encryption at rest for customer data. Agent conversation logs, customer PII, and order data must be encrypted.
- **Recommendation**: When defining RDS in Terraform, enable encryption with a customer-managed KMS key. Apply KMS encryption to all data stores: RDS, S3 (for future unstructured data), DynamoDB (for future basket/session data), and agent conversation logs.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: OAuth2 resource server is configured but completely non-enforcing. `ResourceServerConfig.java` permits all requests (`.authorizeRequests().anyRequest().permitAll()`). Every controller method has `@PreAuthorize("permitAll()")`. The `/user/login` endpoint accepts a `User` object with `email` and returns user data without any authentication — effectively a user lookup by email with no password verification.
- **Gap**: Zero API authentication. Any client can access any endpoint. The "login" endpoint returns user data based on email without verifying identity. This is fundamentally insecure for agent access.
- **Recommendation**: Enable OAuth2/JWT authentication via Amazon Cognito. Remove `permitAll()` and enforce token-based auth on all endpoints. Implement separate auth scopes for human users and AI agents (agent-to-service authentication).

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: Spring Security OAuth2 libraries are present but no identity provider is configured. No Cognito user pool, no Okta configuration, no OIDC/SAML settings, no SSO configuration. `CoreConfig.java` defines a `BCryptPasswordEncoder` bean but it is not used anywhere — no password-based authentication is implemented.
- **Gap**: No centralized identity provider. Users are identified only by email address in request bodies. No SSO, no federated identity, no user pool management.
- **Recommendation**: Deploy Amazon Cognito as the centralized identity provider. Configure user pools for customer authentication and machine-to-machine credentials for agent authentication. Define in Terraform with `aws_cognito_user_pool`.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing found. No X-Ray SDK, no OpenTelemetry imports, no trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`). `spring-boot-starter-actuator` is included in `build.gradle` but no tracing configuration exists. No `logback.xml`, no `log4j2.xml`, no tracing auto-instrumentation config.
- **Gap**: Zero distributed tracing. Agent workflows spanning LLM calls, tool invocations, and database queries are completely invisible. Cannot reconstruct agent decision chains when failures occur.
- **Recommendation**: Add OpenTelemetry Java auto-instrumentation agent. Configure X-Ray as the tracing backend. Include `gen_ai.*` semantic conventions for future LLM span tracking. Define in Terraform with `aws_xray_group`.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: No structured logging. `HealthController.java` uses `System.out.println()` for output. All repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) use `e.printStackTrace()` for error logging. No JSON log formatters, no correlation IDs, no logging framework configuration files (no `logback.xml`, no `log4j2.xml`). Despite Spring Boot including Logback by default, it is not configured.
- **Gap**: Unstructured, unparseable logs with no correlation IDs. Agent interaction logs cannot be queried, correlated, or analyzed. CloudWatch Log Insights would be ineffective.
- **Recommendation**: Configure Logback with JSON format (use `logstash-logback-encoder`). Add correlation ID middleware (MDC-based). Replace all `System.out.println()` and `e.printStackTrace()` with proper SLF4J logger calls.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no golden dataset files. No test files of any kind exist in the repository.
- **Gap**: No agent evaluation capability. Customer support agent quality (accuracy, helpfulness, safety) cannot be measured or tracked over time.
- **Recommendation**: Create evaluation datasets with golden question-answer pairs for customer support scenarios (order status queries, product recommendations, return processing). Implement automated eval pipeline using Amazon Bedrock's evaluation capabilities or RAGAS framework.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions. No CloudWatch alarms. No latency or availability targets defined anywhere. `spring-boot-starter-actuator` is present but no custom metrics or health indicators beyond the default are configured.
- **Gap**: No SLOs for any API endpoint. Agent reliability cannot be measured against defined targets (e.g., "order lookup must respond within 500ms p99").
- **Recommendation**: Define SLOs for critical agent-facing endpoints: `/unicorns` GET (p99 < 500ms), `/unicorns/basket/{userUuid}` GET (p99 < 500ms), `/user/login` POST (p99 < 1s). Create CloudWatch alarms for SLO violations.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment automation of any kind. No blue/green, no canary deployments, no rollback triggers. No CodeDeploy, no Helm rollback, no feature flags. No prompt versioning (no AI/agent components to version).
- **Gap**: No rollback capability. Agent prompt changes, model updates, or tool configuration changes cannot be safely rolled back if they cause regressions.
- **Recommendation**: Implement blue/green deployments on ECS with CodeDeploy. Use Helm for Kubernetes rollback capability. Add feature flags (AWS AppConfig) for gradual rollout of agent features and prompt changes.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application, so no cost tracking exists. No token counting, no cost attribution, no usage metrics.
- **Gap**: No LLM cost tracking infrastructure. When agents are implemented, token usage per customer interaction, per agent type, and per workflow must be tracked to manage costs.
- **Recommendation**: When integrating Bedrock, implement per-request token usage logging with user/workflow attribution. Create CloudWatch custom metrics for token consumption. Establish tiered retention policies for agent telemetry data.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics published. `spring-boot-starter-actuator` is present but only default health/info endpoints are active (no custom Micrometer metrics, no CloudWatch integration configured).
- **Gap**: No business outcome tracking. Cannot measure agent effectiveness: order resolution rate, customer satisfaction, basket conversion rate, support ticket deflection.
- **Recommendation**: Add Micrometer metrics for business KPIs: basket additions/removals per hour, user registrations, API response times by endpoint. Publish to CloudWatch. When agents are deployed, add agent-specific metrics (task success rate, hallucination rate, escalation rate).

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection. No error rate alarms. No latency monitoring. No PagerDuty/OpsGenie integration. No monitoring infrastructure of any kind.
- **Gap**: No anomaly detection. Agent behavioral anomalies (reasoning loops, unexpected tool call patterns, elevated error rates) would go undetected.
- **Recommendation**: Enable CloudWatch anomaly detection on API latency and error rates. Create composite alarms for critical paths. When agents are deployed, add behavioral baseline monitoring for tool call frequency and reasoning step counts.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy defined. No CodeDeploy configuration, no Helm canary, no Argo Rollouts, no feature flags. The commented-out Docker plugin in `build.gradle` (`/*docker { ... }*/`) suggests containerization was planned but never implemented.
- **Gap**: No deployment strategy. All changes go directly to production with no gradual rollout or safety mechanisms.
- **Recommendation**: Implement blue/green deployments on ECS using CodeDeploy with automatic rollback on alarm trigger. Use GitOps practices with Helm charts for deployment management per stated preferences.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files exist. `spring-boot-starter-test` is listed as `testImplementation` in `build.gradle`, but no `src/test/` directory exists. No integration tests, no unit tests, no API tests, no contract tests.
- **Gap**: Zero test coverage. Agent tools (API endpoints) have no tests. Cannot verify that changes don't break agent functionality.
- **Recommendation**: Create integration tests for all API endpoints using Spring Boot Test + MockMvc. Add contract tests for API schemas. When agents are deployed, add end-to-end agent workflow tests. Run all tests in CI pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON). No Systems Manager Automation documents. No remediation Lambda functions. No incident response workflows. No self-healing patterns.
- **Gap**: No incident response automation. Agent failures (LLM timeouts, tool errors, data inconsistencies) have no automated response path. Mean-time-to-detect (MTTD) and mean-time-to-resolve (MTTR) are entirely human-paced.
- **Recommendation**: Create machine-readable runbooks for common failure scenarios: database connection failures, high error rates, agent timeout escalation. Implement SSM Automation documents for common remediations (restart service, scale up, failover).

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO definition files with named owners. No platform team tooling configuration. No observability stack configuration. No shared responsibility model documentation.
- **Gap**: No observability ownership model. When agents are deployed, there is no clarity on who owns agent quality metrics, safety monitoring, and operational response.
- **Recommendation**: Define observability ownership: product team owns agent-level SLOs (task success rate, safety metrics), platform team owns infrastructure SLOs (latency, availability). Create a CODEOWNERS file. Establish an observability-as-product mindset with SLO-driven operations.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 2/4, INF-Q1: 1/4, APP-Q3: 1/4, APP-Q10: 2/4 | High |
| Move to Containers | Triggered | Medium | High | INF-Q1: 1/4, No Dockerfile found | Medium |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Triggered | High | Medium | INF-Q2: 2/4 | Medium |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q5: 1/4, INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1 (Infrastructure Foundation)**: Move to Containers + Move to Modern DevOps — these can execute concurrently. Containerization creates the Dockerfile and ECS deployment while DevOps creates the CI/CD pipeline and IaC.

**Parallel Track 2 (Data & AI)**: Move to Managed Databases + Move to AI — database migration to RDS/Aurora can proceed in parallel with AI framework integration and vector DB setup.

**Sequential Dependencies**:
- Move to Containers must complete before Move to Cloud Native (must containerize before decomposing to microservices)
- Move to Modern DevOps (CI/CD) should be in place before Move to AI (need deployment pipeline for agent code)
- Move to Managed Databases should complete before Move to AI (agents need stable, managed data backends)

### Move to Containers

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q1: Score 1/4 — Application runs on raw EC2 (`HealthController.java` uses `EC2MetadataUtils.getInstanceInfo()`). No managed container orchestration or serverless compute.
  - No Dockerfile found — The repository contains no container definitions. A commented-out Docker plugin in `build.gradle` suggests containerization was planned but never implemented.
- **Current State**: Standalone Spring Boot JAR deployed directly on EC2 instances with no container runtime, no image registry, no orchestration.
- **Target State**: Application packaged as a Docker container image, stored in Amazon ECR, running on Amazon ECS with Fargate launch type and auto-scaling.
- **Key Activities**:
  1. Create a multi-stage Dockerfile for the Spring Boot application
  2. Set up Amazon ECR repository for container images
  3. Define ECS cluster, service, and task definition in Terraform
  4. Configure Fargate launch type with appropriate CPU/memory
  5. Set up ALB target group for ECS service health checks
- **Dependencies**: None — this is a foundational activity
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 — Agent Quick Wins (Days 1–30)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 2/4 — Monolith with identifiable modules but significant database coupling. All domains (Unicorn catalog, Basket, User) share a single MySQL database.
  - INF-Q1: Score 1/4 — Raw EC2 compute with no managed orchestration.
  - APP-Q3: Score 1/4 — 100% synchronous HTTP communication with zero async capability.
  - APP-Q10: Score 2/4 — No async infrastructure for future long-running operations.
- **Current State**: Tightly-coupled monolith with shared database, synchronous-only communication, no event-driven patterns.
- **Target State**: Modular services with clear domain boundaries (Catalog, Basket/Order, User), each independently deployable on ECS, communicating via API Gateway and EventBridge.
- **Key Activities**:
  1. Conduct domain modeling to identify bounded contexts (Catalog, Basket/Order, User)
  2. Extract Basket/Order service first (highest value for support agents)
  3. Implement API Gateway routing (Strangler Fig pattern)
  4. Introduce EventBridge for domain event publishing
  5. Add SQS for async order processing workflows
- **Dependencies**: Move to Containers must complete first (need container infrastructure before decomposition)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 — Agent Foundations (Months 1–3) and Phase 3 — Agent Scale & Optimization (Months 3–6)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Managed Databases

- **Priority**: Medium
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q2: Score 2/4 — MySQL database with no IaC confirming managed RDS configuration. No evidence of automated failover, Multi-AZ deployment, or backup policies.
- **Current State**: MySQL database accessed via JDBC with environment-variable-driven endpoint. No IaC confirms managed status. Credentials hardcoded.
- **Target State**: Amazon RDS for MySQL (or Aurora MySQL) with Multi-AZ, automated backups, encryption at rest, and explicit engine version pinning in Terraform. DynamoDB for the Basket domain (key-value access pattern) when service is extracted.
- **Key Activities**:
  1. Define RDS instance in Terraform with Multi-AZ, encryption, and version pinning
  2. Migrate credentials to AWS Secrets Manager
  3. Evaluate DynamoDB for the Basket service (simple key-value lookups by user UUID)
  4. Set up automated backup policies and monitoring
- **Dependencies**: None — can proceed in parallel with other tracks
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (IaC for existing DB) and Phase 2 (DynamoDB migration for Basket)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q5: Score 1/4 — Zero IaC coverage. No `.tf`, CDK, CloudFormation, or Helm files.
  - INF-Q6: Score 1/4 — Zero CI/CD pipeline definitions. No GitHub Actions, CodePipeline, or Jenkinsfile.
  - OPS-Q9: Score 1/4 — No deployment strategy. No blue/green, canary, or feature flags.
  - OPS-Q10: Score 1/4 — Zero test coverage. No test files despite `spring-boot-starter-test` dependency.
  - OPS-Q1: Score 1/4 — No distributed tracing. No X-Ray or OpenTelemetry.
- **Current State**: Manual infrastructure provisioning, manual deployments, no testing, no tracing, no observability.
- **Target State**: Full Terraform IaC, GitHub Actions CI/CD pipeline with build/test/deploy stages, blue/green ECS deployments, OpenTelemetry distributed tracing, structured JSON logging, and integration test suite.
- **Key Activities**:
  1. Create Terraform project for all infrastructure (VPC, ECS, RDS, API Gateway)
  2. Set up GitHub Actions CI/CD pipeline (build → test → container build → deploy)
  3. Add OpenTelemetry auto-instrumentation with X-Ray backend
  4. Configure structured JSON logging with correlation IDs
  5. Write integration tests for all API endpoints
  6. Implement blue/green deployments via ECS + CodeDeploy
  7. Adopt GitOps workflow with Helm per stated preferences
- **Dependencies**: None — this is a foundational enabler for all other pathways
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (IaC + CI/CD) and Phase 2 (advanced deployment strategies + observability)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent framework. No Bedrock SDK, no Spring AI, no Strands Agents SDK.
  - DATA-Q1: Score 1/4 — No vector database for semantic search.
  - DATA-Q3: Score 1/4 — No RAG pipeline for knowledge retrieval.
  - OPS-Q3: Score 1/4 — No automated evaluation framework for agent quality.
  - OPS-Q6: Score 1/4 — No LLM cost tracking infrastructure.
- **Current State**: Zero AI/agent capabilities. No LLM integration, no vector store, no RAG, no evaluation framework.
- **Target State**: Customer-facing support and order management agents powered by Amazon Bedrock, with vector-based knowledge retrieval (Bedrock Knowledge Bases or OpenSearch), automated evaluation pipeline, per-request cost tracking, and human approval workflows for high-risk actions.
- **Key Activities**:
  1. Integrate Strands Agents SDK or Amazon Bedrock Agent Runtime
  2. Generate OpenAPI specs for existing APIs (prerequisite for agent tool registration)
  3. Deploy managed vector database (OpenSearch or Bedrock Knowledge Bases)
  4. Build RAG pipeline for product catalog and support documentation
  5. Create agent evaluation datasets and automated eval pipeline
  6. Implement LLM cost tracking with per-user/per-workflow attribution
  7. Build human approval workflow (Step Functions) for high-risk agent actions
  8. Implement agent observability (tracing, logging, metrics)
- **Dependencies**: Move to Modern DevOps (CI/CD needed for agent deployment), Move to Managed Databases (stable data backend needed)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (foundations: vector DB, RAG, API docs) and Phase 3 (full agent deployment, evals, cost tracking)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

This monolith would benefit from service extraction to create clear agent tool boundaries. The application has identifiable domain modules (Catalog via `UnicornController`/`UnicornService`, Basket via `BasketController`/`UnicornService`, User via `UserController`/`UserService`) sharing a single MySQL database. For customer support agents, extracting the Basket/Order domain first would create a dedicated "order management" tool with clear API boundaries. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface (`GET /unicorns`, `GET /unicorns/basket/{userUuid}`, `POST /unicorns/basket`, `POST /user`, `POST /user/login`).

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Agent with JSON APIs** — Your existing REST APIs already return structured JSON responses (`@JsonInclude`, `@JsonSerialize` in `Unicorn.java`, `User.java`, `CoreModel.java`). An agent can use these endpoints as tools today by defining them manually in an agent tool configuration.
   - **Leverages**: Structured JSON responses from `GET /unicorns`, `GET /unicorns/basket/{userUuid}`, `POST /user/login`
   - **Effort**: Low
   - **Value**: Proves agent-API integration works; demonstrates value to stakeholders with a support agent that can look up products and check customer baskets

2. **Natural Language Order Query Agent** — The clean MySQL schema in `create_tables.sql` (3 tables, clear column naming, no stored procedures) is ideal for a text-to-SQL agent. A customer support agent could answer "What's in John's basket?" by translating to SQL against the `unicorns_basket` + `unicorns` tables.
   - **Leverages**: Clean schema in `database/create_tables.sql` with well-named tables (`unicorns`, `unicorns_basket`, `unicorn_user`) and clear relationships
   - **Effort**: Medium
   - **Value**: Enables natural language data queries for support agents handling order and inventory inquiries; directly addresses the goal of building customer-facing AI agents for support and order management

3. **Product Catalog Knowledge Agent** — The 10 seed products in `create_tables.sql` and the product data structure (`name`, `description`, `price`, `image`) provide a starting dataset for a product recommendation agent. Even without RAG, a simple agent can query the product catalog API and provide recommendations.
   - **Leverages**: `GET /unicorns` endpoint returning full product catalog with descriptions and prices
   - **Effort**: Low
   - **Value**: Customer-facing product recommendation capability; support agents can help customers find products by describing what they want

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

1. **Create Dockerfile and containerize the application** — Build a multi-stage Dockerfile for the Spring Boot JAR. Push to Amazon ECR. This unblocks all subsequent infrastructure work. *(Move to Containers)*
2. **Create Terraform project for core infrastructure** — Define VPC, subnets, security groups, ECS cluster, and ALB in Terraform. Codify the existing MySQL database as an RDS instance with Multi-AZ and encryption. *(Move to Modern DevOps + Move to Managed Databases)*
3. **Set up GitHub Actions CI/CD pipeline** — Create a basic pipeline: build Gradle project → run tests → build container image → push to ECR → deploy to ECS. Adopt GitOps practices. *(Move to Modern DevOps)*
4. **Migrate secrets to AWS Secrets Manager** — Move the hardcoded `MonoToMicroUser`/`MonoToMicroPassword` from `application.properties` to Secrets Manager. Update the application to read credentials from environment variables injected at deployment. *(Security Foundation)*
5. **Generate OpenAPI specification** — Add `springdoc-openapi-ui` to `build.gradle` and annotate controllers with OpenAPI annotations. Publish the spec at `/v3/api-docs`. This is the #1 prerequisite for agent tool registration. *(Move to AI prerequisite)*

### Phase 2 — Agent Foundations (Months 1–3)

1. **Upgrade Java and Spring Boot** — Upgrade from Java 8/Spring Boot 2.1.x to Java 17/Spring Boot 3.2+. This unblocks Spring AI, AWS SDK v2, and modern agent frameworks. *(Application Modernization)*
2. **Deploy API Gateway** — Place Amazon API Gateway in front of the ECS service. Configure throttling, API key-based usage plans, and request validation. Define in Terraform. *(Move to Cloud Native)*
3. **Implement authentication with Amazon Cognito** — Deploy Cognito user pool and configure OAuth2/JWT authentication. Replace `permitAll()` with role-based access control. Create machine-to-machine credentials for agent authentication. *(Security)*
4. **Add structured logging and distributed tracing** — Configure Logback with JSON format. Add OpenTelemetry auto-instrumentation with X-Ray backend. Replace all `System.out.println()` and `e.printStackTrace()` calls. *(Move to Modern DevOps)*
5. **Deploy vector database and build RAG pipeline** — Set up Amazon OpenSearch Service or Bedrock Knowledge Bases. Create embeddings for product catalog data. Build a RAG pipeline for product knowledge and support documentation. *(Move to AI)*
6. **Integrate agent framework** — Add Strands Agents SDK or Amazon Bedrock Agent Runtime. Register the OpenAPI-documented endpoints as agent tools. Build a proof-of-concept customer support agent for order lookup and product search. *(Move to AI)*
7. **Write integration test suite** — Create integration tests for all API endpoints using Spring Boot Test. Add to CI pipeline as a required gate. *(Move to Modern DevOps)*

### Phase 3 — Agent Scale & Optimization (Months 3–6)

1. **Extract Basket/Order service** — Using Strangler Fig pattern, extract the Basket domain from the monolith into a separate ECS service with its own DynamoDB data store. Route via API Gateway. *(Move to Cloud Native)*
2. **Implement event-driven architecture** — Add EventBridge for domain events (OrderPlaced, BasketUpdated, UserCreated) and SQS for async order processing. Connect agent actions to event streams. *(Move to Cloud Native)*
3. **Build human approval workflow** — Implement Step Functions with `waitForTaskToken` for high-risk agent actions (refunds, account modifications). Create an approval dashboard. *(Move to AI + Security)*
4. **Implement agent evaluation pipeline** — Create golden evaluation datasets for customer support scenarios. Implement automated eval pipeline with scoring metrics (accuracy, helpfulness, safety). Run evals in CI. *(Move to AI)*
5. **Add LLM cost tracking and agent observability** — Implement per-request token usage tracking with user/workflow attribution. Add agent-specific CloudWatch metrics (task success rate, tool error rate). Set up anomaly detection. *(Move to AI + Move to Modern DevOps)*
6. **Define SLOs and implement blue/green deployments** — Define SLOs for agent-facing endpoints. Implement blue/green deployments via ECS + CodeDeploy with automatic rollback on SLO violations. *(Move to Modern DevOps)*
7. **Scale agent capabilities** — Add additional agent tools per extracted service. Implement multi-agent orchestration for complex support scenarios. Add embedding freshness pipeline triggered by data change events. *(Move to AI)*

---

## Recommended Self-Paced Learning Materials

### Module 2: Move to Cloud Native (Containers and Serverless)
- **Cloud Design Patterns, Architectures, and Implementations** — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture — directly applicable to decomposing this monolith.
- **Modernize a Monolith to ECS and Fargate using Application Discovery** — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
  - Hands-on lab directly applicable to this assessment — walks through containerizing a monolith and deploying to ECS/Fargate.

### Module 3: Move to Containers with Amazon ECS and EKS
- **AWS Modernization Pathways: Move to Containers with Amazon ECS** — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
  - Comprehensive learning plan for ECS containerization — the preferred container orchestration per stated preferences.
- **Introduction to Containers** — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
  - Foundational knowledge for creating Dockerfiles and understanding container concepts.
- **AWS Fargate Getting Started** — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
  - Fargate-specific guidance for running containers without managing EC2 instances.
- **Amazon ECR Getting Started** — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
  - Setting up and managing container image registries for the CI/CD pipeline.
- **Working with Amazon Elastic Container Service (Lab)** — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
  - Hands-on lab for ECS service deployment.

### Module 4: Move to Managed Databases
- **AWS Modernization Pathways: Move to Managed Databases** — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
  - Comprehensive path for migrating from self-managed to managed database services.
- **Introduction to Building with AWS Databases** — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
  - Understanding AWS database portfolio — relevant for choosing between RDS MySQL, Aurora MySQL, and DynamoDB for different domains.
- **AWS Database Migration Service (DMS) Getting Started** — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
  - If migrating between database engines during decomposition.
- **AWS PartnerCast: Vector Databases for Generative AI Applications** — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Critical for understanding vector database options for RAG and agent knowledge retrieval.

### Module 6: Move to Modern DevOps
- **AWS Modernization Pathways: Move to Modern DevOps** — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Complete DevOps modernization learning path — covers IaC, CI/CD, deployment strategies, and observability.
- **Getting Started with DevOps on AWS** — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundational DevOps concepts for teams new to AWS DevOps practices.
- **Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS)** — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Directly applicable lab for setting up the CI/CD pipeline to ECS/Fargate.
- **AWS CloudFormation Getting Started** — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - Understanding IaC concepts (applicable to both CloudFormation and Terraform).
- **Advanced Testing Practices Using AWS DevOps Tools** — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Critical for building the integration test suite that is completely absent today.
- **AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions** — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
  - GitOps workflow guidance per stated preferences.

### Module 7: Move to AI
- **AWS Modernization Pathways: Move to AI** — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Comprehensive AI modernization learning plan — the primary pathway for this assessment's goal.
- **Amazon Bedrock Getting Started** — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundational Bedrock knowledge for LLM integration.
- **Essentials for Prompt Engineering** — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Essential for crafting effective agent prompts for customer support scenarios.
- **Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab)** — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Directly applicable lab for building the RAG pipeline identified as a critical gap.
- **Introduction to Agentic AI on AWS** — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core agentic AI concepts for the team building customer-facing agents.
- **Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab)** — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on lab for the recommended agent framework.
- **AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow** — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced agent observability — directly addresses the OPS-Q1, OPS-Q3, and OPS-Q6 gaps.
- **Planning a Generative AI Project** — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Project planning guidance for the agentic AI enablement initiative.

---

## Appendix: Evidence Index

| # | File | Key Finding |
|---|------|-------------|
| 1 | `build.gradle` | Java 8, Spring Boot 2.1.x, MySQL connector 8.0.11, AWS SDK v1 1.11.567, Spring Security OAuth2, MyBatis, spring-boot-starter-actuator, commented-out Docker plugin |
| 2 | `src/main/resources/application.properties` | Hardcoded DB credentials (MonoToMicroUser/MonoToMicroPassword), MySQL JDBC connection, port 8080 |
| 3 | `database/create_tables.sql` | 3 MySQL tables (unicorns, unicorns_basket, unicorn_user), clean schema, no stored procedures, 10 seed products |
| 4 | `src/main/java/com/monoToMicro/Application.java` | @SpringBootApplication entry point, CORS workaround, WebSecurity ignoring all OPTIONS |
| 5 | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | @EnableResourceServer with permitAll() — authentication completely disabled |
| 6 | `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | GET /unicorns — synchronous, @PreAuthorize("permitAll()"), returns JSON Collection<Unicorn> |
| 7 | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | POST/DELETE/GET /unicorns/basket — basket operations, no idempotency headers, JSON responses |
| 8 | `src/main/java/com/monoToMicro/rest/controller/UserController.java` | POST /user, POST /user/login — user creation and email-based login without auth, returns PII |
| 9 | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | EC2MetadataUtils.getInstanceInfo() confirming EC2 deployment, System.out.println() logging |
| 10 | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | GET /data — synchronous full basket replication, potential long-running operation |
| 11 | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | Unicorn service with CRUD operations, constructor injection, no async patterns |
| 12 | `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | User service with create and getByEmail, UUID generation, no validation |
| 13 | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | Repository pattern, e.printStackTrace() error handling, returns null on failure |
| 14 | `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | synchronized create(), e.printStackTrace(), returns null on failure |
| 15 | `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | Centralized MyBatis configuration, 3 mapper registrations, DataSource autowired |
| 16 | `src/main/java/com/monoToMicro/core/model/Unicorn.java` | @JsonInclude(NON_NULL), product model with uuid/name/description/price/image |
| 17 | `src/main/java/com/monoToMicro/core/model/User.java` | @JsonInclude(NON_NULL), PII fields: email, firstName, lastName exposed in API |
| 18 | `src/main/java/com/monoToMicro/core/model/CoreModel.java` | @JsonSerialize(NON_NULL), @JsonIgnore on internal fields, Joda DateTime dependency |
| 19 | `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | Standard SQL (SELECT, INSERT IGNORE, DELETE, JOIN), no stored procedures, MySQL-compatible |
| 20 | `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | INSERT IGNORE for user creation, email-based lookup, MyBatis cache enabled |
