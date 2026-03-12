# Agentic Readiness Assessment Report

**Target**: MonoToMicroLegacy (Unishop e-commerce application)
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

The MonoToMicroLegacy Unishop application is a legacy Java 8 / Spring Boot 2.1 monolith deployed on EC2 with a MySQL backend and zero infrastructure-as-code, CI/CD, observability, or security controls. It is fundamentally unprepared for agentic AI workloads — there are no API specifications for agent tool discovery, no vector database or RAG pipeline for knowledge retrieval, no AI/agent frameworks integrated, and no authentication or rate limiting to safely expose capabilities to autonomous agents. The strongest aspects are a clean data access layer (centralized repository pattern with MyBatis), structured JSON responses (Jackson serialization), and a simple schema with no stored procedures — all of which reduce migration friction. To build customer-facing AI agents for support and order management, the immediate priorities are containerizing the application, creating OpenAPI specs for agent tool integration, standing up a managed database, and establishing CI/CD and observability foundations.

### Overall Score: 1.3 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.0 / 4.0 | ❌ |
| Application Architecture | 1.4 / 4.0 | ❌ |
| Data Foundations | 1.9 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.0 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

1. **APP-Q2 — No API Documentation (Score: 1/4)**: There are no OpenAPI or Swagger specifications anywhere in the repository. Without machine-readable API specs, AI agents cannot discover or invoke the Unishop endpoints for order management and customer support. **First step**: Add `springdoc-openapi-ui` to `build.gradle` to auto-generate OpenAPI 3.0 specs from the existing Spring MVC controllers (`UnicornController`, `BasketController`, `UserController`).

2. **APP-Q13 — No AI/Agent Frameworks (Score: 1/4)**: No agent SDK, Bedrock client, LangChain, or MCP integration exists. The AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567` in `build.gradle`) predates Bedrock entirely. Without agent framework integration, there is no path to autonomous customer support or order management agents. **First step**: Add the AWS SDK v2 Bedrock Runtime dependency and create a proof-of-concept agent that queries the `/unicorns` and `/unicorns/basket/{userUuid}` endpoints as tools.

3. **DATA-Q1 — No Vector Database (Score: 1/4)**: No vector store (OpenSearch, pgvector, Pinecone, Chroma) is present. Customer support agents need semantic search over product catalogs, order history, and support documentation to provide accurate, context-aware responses. **First step**: Provision Amazon OpenSearch Service with the k-NN plugin or enable `pgvector` on an Aurora PostgreSQL instance to store product and order embeddings.

4. **DATA-Q3 — No RAG Implementation (Score: 1/4)**: No document chunking, embedding generation, or semantic search pipeline exists. A customer support agent for order management requires RAG to ground responses in actual product data, order details, and support policies. **First step**: Build a RAG pipeline using Amazon Bedrock Knowledge Bases backed by the product catalog from the `unicorns` table and any customer support documentation.

5. **SEC-Q7 — No Human Approval Workflows (Score: 1/4)**: There are no human-in-the-loop approval gates for any operations. When AI agents handle order management (refunds, cancellations, basket modifications), high-risk actions must be gated by human approval to prevent autonomous agents from executing harmful operations at machine speed. **First step**: Implement an approval workflow using AWS Step Functions with `waitForTaskToken` for operations like order cancellations and refunds before agents can execute them autonomously.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: The application runs on EC2 instances. `HealthController.java` imports `com.amazonaws.util.EC2MetadataUtils` and calls `EC2MetadataUtils.getInstanceInfo()` to retrieve instance ID, instance type, availability zone, and region — confirming direct EC2 deployment. No ECS, EKS, Fargate, or container orchestration configuration was found. No Dockerfile exists in the repository. The `build.gradle` has a commented-out `docker` task block, indicating containerization was considered but never implemented.
- **Gap**: 100% of compute is raw EC2 with no container orchestration or managed compute. No Dockerfile exists to containerize the application.
- **Recommendation**: Create a Dockerfile for the Spring Boot application (multi-stage build using Gradle to produce a JAR, then run on a JRE base image). Deploy to Amazon ECS on Fargate for managed container orchestration, aligning with the preference for ECS and containers.

#### INF-Q2: Databases
- **Score**: 1/4 ❌
- **Finding**: `application.properties` defines a MySQL JDBC connection: `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The database endpoint is parameterized via environment variable `MONO_TO_MICRO_DB_ENDPOINT`, but there is no IaC (Terraform, CloudFormation, CDK) defining an RDS instance, Aurora cluster, or any managed database. The MySQL connector version is `mysql:mysql-connector-java:8.0.11` in `build.gradle`. Without IaC evidence, the database is assumed to be self-managed or manually provisioned.
- **Gap**: No IaC-managed database. Cannot verify managed vs. self-managed MySQL. No automated failover, backups, or scaling configuration.
- **Recommendation**: Define an Amazon RDS for MySQL (or Amazon Aurora MySQL-Compatible) instance in IaC (CDK or Terraform). Consider migrating to Amazon DynamoDB for the basket service (key-value access pattern) to align with preferences, using AWS DMS for migration.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service detected. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` is implemented as direct synchronous method calls without state management or workflow coordination.
- **Gap**: No dedicated workflow orchestration. All business logic is hardcoded in service implementations.
- **Recommendation**: Introduce AWS Step Functions for multi-step operations like order processing, basket checkout, and customer support escalation workflows. Step Functions will also be critical for agent orchestration with human-in-the-loop approval gates.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, Kafka, or RabbitMQ dependencies or configurations found in `build.gradle` or any source file. All inter-component communication is synchronous (controller → service → repository → DB). The `DataReplicationController.java` fetches all baskets synchronously with no event-driven replication.
- **Gap**: Zero asynchronous messaging capability. All operations are synchronous request-response.
- **Recommendation**: Introduce Amazon SQS for decoupling write operations (basket updates, user registration) and Amazon EventBridge for domain event publishing. Add Amazon SNS for notification fanout (order confirmations, support ticket updates). This aligns with preferences for SQS, EventBridge, and SNS.

#### INF-Q5: Infrastructure as Code
- **Score**: 1/4 ❌
- **Finding**: No Terraform (.tf), CloudFormation, CDK, Helm, or Kustomize files exist in the repository. Infrastructure is entirely manually provisioned. The `build.gradle` only covers application build, not infrastructure.
- **Gap**: 0% IaC coverage. All infrastructure (EC2, database, networking) is manually managed.
- **Recommendation**: Adopt AWS CDK (TypeScript or Java) to define all infrastructure: ECS cluster, RDS/DynamoDB, VPC, API Gateway, SQS queues, and EventBridge rules. CDK provides type-safe infrastructure definitions that integrate well with CI/CD pipelines.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No GitHub Actions workflows (`.github/workflows/`), Jenkinsfile, `buildspec.yml`, `.gitlab-ci.yml`, or any CI/CD pipeline definition exists in the repository. Deployments are presumed to be manual.
- **Gap**: No automated build, test, or deployment pipeline.
- **Recommendation**: Create a CI/CD pipeline using AWS CodePipeline with CodeBuild for build/test and CodeDeploy for ECS deployment. Include stages for unit tests, integration tests, container image build/push to ECR, and ECS service deployment.

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: The application exposes its API directly on port 8080 (`server.port=8080` in `application.properties`). No API Gateway, ALB, or CloudFront configuration exists. CORS is configured application-side in `MVCConfig.java` (`registry.addMapping("/**").allowedMethods(...)`) and `Application.java`.
- **Gap**: No API Gateway with throttling, authentication, or request validation. Direct service exposure without a managed entry point.
- **Recommendation**: Deploy Amazon API Gateway (REST API) in front of the application, with VPC Link to the ECS service. Configure throttling, request validation, API keys, and usage plans. This is essential for agent-safe API exposure and aligns with API Gateway preference.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, MSK, or any streaming service configuration found. No stream consumer/producer patterns in the codebase.
- **Gap**: No event streaming capability for real-time data flow.
- **Recommendation**: Evaluate Amazon EventBridge for event-driven architecture as a first step (preferred). Add Amazon Kinesis Data Streams if real-time analytics on customer behavior and order events is needed for agent decision-making.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions found in the repository. No IaC means network configuration is unknown or manually managed. The `Application.java` disables CORS OPTIONS request security (`web.ignoring().antMatchers(HttpMethod.OPTIONS, "/**")`) with a comment stating "workaround to get CORS working with this old version, not recommended for production usage!"
- **Gap**: No verifiable network security configuration. CORS security is explicitly bypassed.
- **Recommendation**: Define a VPC with public and private subnets in IaC. Place the ECS service in private subnets with ALB/API Gateway in public subnets. Implement least-privilege security groups. Remove the CORS security bypass.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No Auto Scaling Groups, ECS Service auto-scaling, or any scaling configuration found. The EC2 deployment has no scaling policies defined in the repository.
- **Gap**: No auto-scaling capability. Cannot handle traffic spikes from agent workloads.
- **Recommendation**: When migrating to ECS, configure ECS Service Auto Scaling with target tracking policies on CPU/memory utilization. Agent workloads can generate bursty traffic patterns that require elastic scaling.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`) with Spring Boot 2.1.6.RELEASE. Java has a growing but not leading agent framework ecosystem compared to Python and TypeScript. Spring AI exists but requires Spring Boot 3.x+ and Java 17+. The current Java 8 / Spring Boot 2.1 stack cannot use modern agent frameworks without a major upgrade.
- **Gap**: Java 8 is at end of life. Spring Boot 2.1 is no longer supported. The Java version blocks adoption of modern agent frameworks (Spring AI, Langchain4j) which require Java 17+.
- **Recommendation**: Upgrade to Java 17+ and Spring Boot 3.x to unlock Spring AI and Langchain4j for agent framework integration. Alternatively, build the agent layer as a separate service in Python (using Strands Agents SDK or LangChain) that calls the Unishop APIs as tools.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI, Swagger, or any API specification files exist in the repository. No `@OpenAPIDefinition`, `@ApiOperation`, `@Schema`, or `springdoc` annotations found in any controller. The REST endpoints (`/unicorns`, `/unicorns/basket`, `/user`, `/health`, `/data`) are defined only in Java code via `@RequestMapping` annotations in `UnicornController.java`, `BasketController.java`, `UserController.java`, `HealthController.java`, and `DataReplicationController.java`.
- **Gap**: Zero API documentation. Agents cannot discover available endpoints, request/response schemas, or operation semantics without manual specification.
- **Recommendation**: Add `springdoc-openapi-ui` dependency to `build.gradle` to auto-generate OpenAPI 3.0 specs from existing controllers. Annotate controllers with `@Operation`, `@Parameter`, and `@Schema` annotations for rich agent-consumable API descriptions.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous communication. All controllers make direct synchronous calls to services (`unicornService.getUnicorns()`, `unicornService.addUnicornToBasket()`, `userService.create()`), which in turn make synchronous database calls via MyBatis mappers. No message queues, event publishers, or async handlers exist. The `DataReplicationController.java` performs a synchronous full-table scan of baskets.
- **Gap**: No asynchronous communication patterns. All operations are blocking request-response.
- **Recommendation**: Introduce Amazon SQS for basket write operations and Amazon EventBridge for publishing domain events (user registered, item added to basket). This enables event-driven agent reactions and decouples the monolith for future service extraction.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single deployable Spring Boot application with a layered architecture: controllers (`UnicornController`, `BasketController`, `UserController`) → services (`UnicornServiceImpl`, `UserServiceImpl`) → repositories (`UnicornRepositoryImpl`, `UserRepositoryImpl`) → MyBatis mappers. The domains (Unicorn/Product, Basket/Cart, User) have separate service and repository interfaces, indicating some modularity. However, all domains share a single MySQL database (`unishop` schema), are deployed as one unit, and share the `CoreModel` base class and `CoreController` base class.
- **Gap**: Monolith with identifiable modules but shared database coupling. Single deployable unit prevents independent scaling or failure isolation.
- **Recommendation**: The monolith's existing layered structure (controller → service → repository) provides natural extraction boundaries. The Unicorn (product catalog), Basket (shopping cart), and User domains can be extracted into separate services over time.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: All API responses use JSON serialization via Jackson. Model classes (`Unicorn.java`, `User.java`) are annotated with `@JsonInclude(JsonInclude.Include.NON_NULL)`. `CoreModel.java` uses `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` and `@JsonIgnore` on internal fields. Controllers return `ResponseEntity<>` with typed response bodies. However, there is no standardized error response format — failures return raw HTTP status codes (e.g., `HttpStatus.BAD_REQUEST`) without error bodies.
- **Gap**: No standardized error response format. Missing error codes, messages, and details in error responses.
- **Recommendation**: Implement a standardized JSON error response format (e.g., RFC 7807 Problem Details) across all endpoints. Agent tools need structured error information to understand failures and decide on retry strategies.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration. Business logic is implemented directly in service methods: `UnicornServiceImpl.addUnicornToBasket()` directly calls `unicornRepository.addUnicornToBasket()`, `UserServiceImpl.create()` directly calls `userRepository.create()`. No state machines, saga patterns, or process orchestration.
- **Gap**: All business logic is hardcoded procedural code in service implementations. No workflow orchestration for multi-step operations.
- **Recommendation**: Introduce AWS Step Functions for checkout flows, order processing, and agent orchestration workflows. Step Functions are essential for the customer support agent use case — handling escalation paths, approval gates, and multi-step resolution workflows.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: Basic idempotency exists via MySQL `INSERT IGNORE` statements in MyBatis mappers. `UnicornMapper.xml` uses `INSERT IGNORE INTO unicorns_basket` with a UNIQUE constraint on `(uuid, unicornUuid)`. `UserMapper.xml` uses `insert ignore into unicorn_user` with a UNIQUE constraint on `email`. This prevents duplicate basket entries and duplicate user registrations at the database level. However, there are no explicit idempotency keys in the API layer (no `Idempotency-Key` header support).
- **Gap**: Database-level deduplication only. No API-level idempotency keys. Agents retrying failed requests could cause unintended side effects for operations not covered by UNIQUE constraints.
- **Recommendation**: Add `Idempotency-Key` header support to all write endpoints (`POST /unicorns/basket`, `POST /user`, `DELETE /unicorns/basket`). Use DynamoDB or a cache for idempotency token storage when migrating to the target architecture.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting middleware, API Gateway throttling, or WAF rules found. All endpoints are unprotected against abuse. No `express-rate-limit`, Spring `@RateLimiter`, or any throttling annotation detected.
- **Gap**: Zero rate limiting. Agent loops or misconfigured agents could overwhelm the API with unbounded requests.
- **Recommendation**: Implement rate limiting at the API Gateway level (throttle settings with burst/rate limits per API key). This is critical for agent safety — agents can generate high-frequency requests if reasoning loops occur. Use API Gateway usage plans aligned with the API Gateway preference.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry policies, or timeout configurations. Error handling in repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`) consists of `try/catch` blocks that call `e.printStackTrace()` and return `null` or `false`. No Resilience4j, Hystrix, Spring Retry, or AWS SDK retry configuration.
- **Gap**: No resilience patterns. Database failures result in silent null returns with stack traces to stdout. No retry logic, no circuit breaking, no graceful degradation.
- **Recommendation**: Add Spring Retry with exponential backoff for database operations. Implement circuit breaker pattern for external dependencies. Replace `e.printStackTrace()` with structured error handling and logging. These patterns are prerequisite for reliable agent tool invocations.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: No background job framework (Celery, Bull, Spring Batch). All operations are synchronous database queries that are likely short-lived. The `DataReplicationController.java` performs a synchronous `getAllBaskets()` operation that could become long-running at scale but has no async handling.
- **Gap**: No asynchronous processing for potentially long-running operations. Agent interactions that trigger data-heavy operations could timeout.
- **Recommendation**: Implement SQS-based async processing for data replication and batch operations. Use Step Functions for orchestrated multi-step agent workflows. Return job status IDs for polling-based completion tracking.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy. Endpoints use unversioned paths: `/unicorns`, `/unicorns/basket`, `/user`, `/health`, `/data`. No `/v1/` prefix, no `Accept-Version` headers, no versioning annotations.
- **Gap**: No versioning strategy. API changes will break agent tool configurations without a deprecation/migration path.
- **Recommendation**: Adopt URL path versioning (e.g., `/v1/unicorns`, `/v1/user`) for all API endpoints. This provides clear version boundaries when agent tool definitions reference specific API versions.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: No service discovery mechanism. The only external dependency endpoint is the database, configured via environment variable `MONO_TO_MICRO_DB_ENDPOINT` in `application.properties`. As a monolith, internal service discovery is not applicable, but there is no API catalog or service registry for external consumers.
- **Gap**: No service registry, API catalog, or service mesh. Hard-coded database endpoint via environment variable.
- **Recommendation**: When decomposing into microservices, implement AWS Cloud Map for service discovery and API Gateway as the service catalog. Agent frameworks need to discover available tools/services dynamically.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework dependencies. `build.gradle` includes AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567`) which predates Amazon Bedrock and has no agent capabilities. No LangChain, LangGraph, CrewAI, Strands Agents, OpenAI, Anthropic, Spring AI, or MCP SDK imports found in any source file.
- **Gap**: Zero AI/agent integration. No foundation for building customer support or order management agents.
- **Recommendation**: Build the agent layer as a separate containerized service (Python with Strands Agents SDK or Amazon Bedrock Agents) that calls the Unishop REST APIs as tools. This avoids the Java 8 limitation and leverages the richer Python agent ecosystem. Deploy the agent service on ECS alongside the Unishop monolith.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database detected. No OpenSearch, pgvector, Pinecone, Weaviate, Chroma, or Bedrock Knowledge Base references in `build.gradle`, source code, or configuration files. No vector similarity search capabilities exist.
- **Gap**: No vector store for semantic search. Customer support agents cannot perform similarity-based product lookup or knowledge retrieval.
- **Recommendation**: Provision Amazon OpenSearch Service with the k-NN plugin for vector storage of product embeddings and customer support knowledge. Alternatively, use Amazon Bedrock Knowledge Bases for a fully managed RAG solution backed by S3 data sources.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). No managed or self-hosted vector store detected.
- **Gap**: No vector database at all — managed or otherwise.
- **Recommendation**: When implementing a vector store, use a fully managed service (Amazon OpenSearch Service or Amazon Bedrock Knowledge Bases) to avoid operational overhead. Managed vector stores provide automatic scaling and maintenance required for production agent workloads.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No document chunking, embedding generation, or semantic search pipeline exists. No Bedrock Titan Embeddings, OpenAI ada, or any embedding model calls found. No `similarity_search`, `knn_search`, or retrieval patterns in the codebase.
- **Gap**: No RAG pipeline. Customer support agents have no mechanism to retrieve relevant product information, policies, or order context from knowledge bases.
- **Recommendation**: Build a RAG pipeline using Amazon Bedrock Knowledge Bases. Ingest product catalog data (from the `unicorns` table), customer support policies, and order management documentation. Use Bedrock Titan Embeddings for vectorization and OpenSearch Service for retrieval.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Single MySQL database with the `unishop` schema containing 3 tables: `unicorns` (product catalog), `unicorns_basket` (shopping cart), and `unicorn_user` (users). All data access goes through one JDBC connection defined in `application.properties`. This is a clean, simple data architecture with no sprawl.
- **Gap**: Minor — single data source is good, but adding vector stores and event streams for agent capabilities will introduce new data sources that need unified access.
- **Recommendation**: Maintain the simplicity by implementing a unified data access layer as new data sources (DynamoDB for baskets, OpenSearch for vectors) are introduced. Use API Gateway as a single entry point for all data access.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: A repository pattern is in use: `UnicornRepository` / `UnicornRepositoryImpl` and `UserRepository` / `UserRepositoryImpl` provide interfaces that abstract database access. MyBatis mappers (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) handle SQL execution. Controllers do not access the database directly — they call services which call repositories. However, data is accessed via direct JDBC connections, not through APIs.
- **Gap**: Repository pattern provides internal abstraction, but data is not accessible via well-defined APIs for external consumers (agents). The Basket domain's data access is coupled through the `UnicornRepository` rather than having its own dedicated repository.
- **Recommendation**: Expose data access through well-defined REST APIs with OpenAPI specs. For the agent layer, all data access should go through the API layer — agents should never connect directly to the database. This also supports the future decomposition into separate microservices.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, document parsing (Textract, Tika), or unstructured data handling detected. The `build.gradle` includes `com.amazonaws:aws-java-sdk-s3:1.11.567` but no S3 operations are implemented in any source file. Product images are referenced by name only (`image` field in `Unicorn.java`) without actual file storage.
- **Gap**: No unstructured data storage or processing pipeline. Customer support documentation, product manuals, and policy documents cannot be ingested for agent knowledge.
- **Recommendation**: Create an S3 bucket for customer support documents, product documentation, and policy files. Integrate with Amazon Textract for document parsing and feed into the RAG pipeline via Bedrock Knowledge Bases.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `database/create_tables.sql` provides explicit schema definitions for all 3 tables with column types, constraints (PRIMARY KEY, UNIQUE, NOT NULL), and seed data (10 unicorn products). MyBatis mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`) define SQL query contracts with parameterized queries. However, there is no schema migration framework (Flyway, Liquibase, Alembic), no schema versioning, and no data dictionary documenting field semantics.
- **Gap**: Schema exists but is not versioned or migration-managed. No documentation of field semantics, relationships, or business rules beyond the raw DDL.
- **Recommendation**: Adopt Flyway or Liquibase for schema migration management. Document the data model with field descriptions and business rules. This documentation will feed directly into agent tool descriptions and natural-language-to-SQL capabilities.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Centralized repository layer with consistent patterns. Both `UnicornRepositoryImpl` and `UserRepositoryImpl` use the same MyBatis-based data access pattern: `@Repository` + `@Transactional` annotations, `@Autowired` mappers, and consistent try/catch error handling. `MyBatisConfig.java` centralizes all mapper bean definitions and SqlSessionFactory configuration. The pattern is consistent across both User and Unicorn domains.
- **Gap**: Minor — the Basket domain's data access is merged into `UnicornRepository` rather than being a separate repository, creating a coupling between product and basket concerns.
- **Recommendation**: When decomposing, extract Basket data access into its own `BasketRepository`. The existing centralized pattern is a good foundation — maintain it as services are extracted.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist, so there is no refresh mechanism. No CDC (Change Data Capture) patterns, no event-driven re-indexing, no scheduled embedding refresh pipelines.
- **Gap**: No embedding pipeline at all, let alone incremental updates.
- **Recommendation**: When implementing the vector store and RAG pipeline, set up DynamoDB Streams or RDS event notifications to trigger embedding regeneration when product data changes. Use EventBridge Scheduler for periodic full re-indexing as a fallback.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 2/4 🟠
- **Finding**: MySQL connector version `8.0.11` is specified in `build.gradle` (`mysql:mysql-connector-java:8.0.11`), indicating MySQL 8.0 compatibility. MySQL 8.0.11 was released in April 2018. No IaC specifies the actual database engine version. MySQL 8.0 is currently supported by Oracle (EOL expected ~April 2026), but the connector version is significantly outdated (8+ years old) and may have known security vulnerabilities.
- **Gap**: No IaC pinning of database engine version. MySQL connector is 8+ years old. Approaching MySQL 8.0 EOL.
- **Recommendation**: Pin the MySQL engine version explicitly in IaC when defining the managed RDS instance. Upgrade the MySQL connector to the latest 8.x version. Plan migration to Aurora MySQL or consider DynamoDB (preferred) for the basket service before MySQL 8.0 reaches EOL.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: `database/create_tables.sql` contains only `CREATE SCHEMA`, `CREATE TABLE`, and `INSERT INTO` statements. No stored procedures (`CREATE PROCEDURE`), triggers (`CREATE TRIGGER`), functions (`CREATE FUNCTION`), or proprietary SQL constructs detected. All business logic resides in the Java application layer via MyBatis mappers. SQL in mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) uses standard ANSI SQL (SELECT, INSERT IGNORE, DELETE, JOIN).
- **Gap**: None. Clean separation of business logic from the database layer.
- **Recommendation**: Maintain this pattern. The absence of stored procedures significantly reduces database migration complexity — the application can be migrated to Aurora, DynamoDB, or another managed database without extracting embedded business logic from the database engine.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded in plaintext in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. The database endpoint is parameterized via environment variable `MONO_TO_MICRO_DB_ENDPOINT`, but the actual credentials are committed to the repository in clear text.
- **Gap**: Secrets are committed to source control in plaintext. No Secrets Manager, Parameter Store, or Vault integration.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager. Replace hardcoded credentials in `application.properties` with Secrets Manager references. Use Spring Cloud AWS Secrets Manager integration or ECS task definition secret references.

#### SEC-Q2: IAM Least Privilege
- **Score**: 1/4 ❌
- **Finding**: No IAM policies defined in the repository. The `build.gradle` includes `com.amazonaws:aws-java-sdk:1.11.567` (the full SDK bundle), suggesting potential broad AWS access. No IAM role definitions, no policy documents, no trust relationships configured in code.
- **Gap**: No IAM policies. The full AWS SDK dependency suggests the application may run with broad permissions rather than least-privilege scoped roles.
- **Recommendation**: Define per-service IAM roles in IaC with specific action/resource permissions. Replace the full SDK bundle (`aws-java-sdk`) with only required SDK modules. When running on ECS, use ECS task roles with least-privilege policies.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Spring Security OAuth2 is configured — `ResourceServerConfig.java` has `@EnableResourceServer` annotation and `build.gradle` includes `spring-security-oauth2-autoconfigure`, `spring-security-jwt`, and `spring-cloud-starter-oauth2`. However, the security configuration in `ResourceServerConfig.java` sets `authorizeRequests().anyRequest().permitAll()`, effectively disabling all authentication. No JWT validation, no token exchange, no user identity propagation.
- **Gap**: OAuth2 infrastructure is present but completely disabled. No user identity is validated or propagated. Agent actions cannot be attributed to specific users.
- **Recommendation**: Enable JWT validation in `ResourceServerConfig.java` by removing `permitAll()` and configuring a proper JWT token verification (e.g., with Amazon Cognito as the issuer). Propagate user identity through all API calls so agent actions are attributable.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No audit logging. No CloudTrail configuration. Application logging uses `System.out.println()` in `HealthController.java` (e.g., `System.out.println(infoStr)`) and `e.printStackTrace()` in repository implementations. No structured audit log of API operations, data modifications, or user actions.
- **Gap**: Zero audit trail. When agents perform actions (basket modifications, user operations), there is no record of what was done, by whom, or when.
- **Recommendation**: Implement structured audit logging for all API operations using a logging framework (SLF4J + Logback with JSON output). Enable CloudTrail for AWS API calls. Log agent actions with full context (user ID, action, parameters, outcome) for compliance and debugging.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. No API Gateway throttling, no WAF rules, no application-level rate limiting middleware. All endpoints accept unlimited requests.
- **Gap**: No protection against API abuse. Autonomous agents could generate unlimited request volume without throttling.
- **Recommendation**: Deploy API Gateway with throttling (burst/rate limits per API key and per-client quotas). Configure WAF rate rules for additional protection. Essential for agent safety — prevents runaway agent loops from overwhelming the service.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: `User.java` stores and exposes `email`, `firstName`, and `lastName` fields. The `UserMapper.xml` `getByEmail` query returns all user fields including email. `UserController.java` returns the full `User` object in responses. No PII masking, redaction, or filtering in logging or API responses. `e.printStackTrace()` could expose user data in error logs.
- **Gap**: PII (email, name) is returned unredacted in API responses and could be logged in stack traces. No automated PII detection or redaction.
- **Recommendation**: Implement PII redaction in logs (mask email addresses and names). Consider field-level access control in API responses. Add Amazon Macie for S3-based PII detection when document storage is added. Critical for customer support agents that handle personal customer data.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human-in-the-loop approval gates for any operation. All API endpoints (`POST /unicorns/basket`, `DELETE /unicorns/basket`, `POST /user`) execute immediately without approval. No Step Functions with `waitForTaskToken`, no approval Lambda patterns, no manual approval stages.
- **Gap**: No human approval workflow. AI agents for order management could execute destructive operations (removing items from baskets, modifying user data) without human oversight.
- **Recommendation**: Implement AWS Step Functions with `waitForTaskToken` for high-risk agent actions: basket modifications above a threshold, user account changes, and any future order cancellation/refund flows. This is a critical safety requirement for agentic-ai-enablement.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS keys, no encryption configuration found in the repository. No `kms_key_id` references. Database encryption status is unknown (no IaC to verify). No encryption settings on any data store.
- **Gap**: No verifiable encryption at rest. Customer data (emails, names, order history) may be stored unencrypted.
- **Recommendation**: Enable encryption at rest with customer-managed KMS keys for all data stores (RDS/Aurora, DynamoDB, S3, OpenSearch). Define KMS key policies in IaC. Essential for protecting customer data that agents will access.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: Despite OAuth2 dependencies in `build.gradle` and `@EnableResourceServer` in `ResourceServerConfig.java`, authentication is disabled: `authorizeRequests().anyRequest().permitAll()`. Additionally, `Application.java` ignores all OPTIONS requests: `web.ignoring().antMatchers(HttpMethod.OPTIONS, "/**")` with a comment "not recommended for production usage!" Every endpoint is publicly accessible without any credentials.
- **Gap**: All endpoints are unauthenticated. Any client (or agent) can access all operations without credentials.
- **Recommendation**: Enable OAuth2/JWT authentication by configuring Amazon Cognito as the authorization server. Remove `permitAll()` from `ResourceServerConfig.java`. Issue per-agent API keys or JWT tokens with scoped permissions for different agent capabilities.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider configured. No Amazon Cognito, Okta, Auth0, or Ping integration. The OAuth2 dependencies exist in `build.gradle` but no issuer URL, JWKS endpoint, or OIDC configuration is defined in `application.properties` or any configuration class. The `CoreConfig.java` defines a `BCryptPasswordEncoder` bean, suggesting local password management was intended but never fully implemented.
- **Gap**: No identity provider. No SSO. User authentication is handled by a simple email lookup (`POST /user/login` calls `userMapper.getByEmail`) without any password verification.
- **Recommendation**: Integrate Amazon Cognito as the centralized identity provider. Configure Cognito User Pools for customer authentication and Cognito Identity Pools for federated agent access. This provides JWT tokens for API authentication and user identity propagation.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, Jaeger, Zipkin, or any distributed tracing SDK found in `build.gradle` or any source file. No trace ID propagation (no `traceparent`, `X-Amzn-Trace-Id`, or correlation headers). No instrumentation wrappers around HTTP calls or database operations.
- **Gap**: Zero distributed tracing. When agents invoke multiple tools in sequence, there is no way to reconstruct the execution path or diagnose failures across the call chain.
- **Recommendation**: Add AWS X-Ray SDK for Java to `build.gradle` and instrument the Spring Boot application. Alternatively, adopt OpenTelemetry Java agent for automatic instrumentation. This is essential for debugging agent tool invocations and understanding end-to-end latency.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: Logging uses `System.out.println()` in `HealthController.java` and `e.printStackTrace()` in `UnicornRepositoryImpl.java` and `UserRepositoryImpl.java`. No logging framework (SLF4J, Logback, Log4j2) is explicitly configured. No JSON log format. No correlation IDs or trace IDs in log output. No structured fields.
- **Gap**: Unstructured logging via stdout/stderr. No correlation between logs and requests. Agent interactions cannot be traced through logs.
- **Recommendation**: Configure SLF4J with Logback (already on classpath via Spring Boot) with JSON encoder output. Add MDC (Mapped Diagnostic Context) for request IDs and user IDs. Pipe logs to CloudWatch Logs for centralized log management and CloudWatch Log Insights queries.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, golden datasets, scoring scripts, or LLM-as-judge patterns found. No AI/agent capabilities exist (see APP-Q13), so there is nothing to evaluate.
- **Gap**: No agent evaluation pipeline. When customer support agents are built, there will be no way to measure response quality, accuracy, or safety.
- **Recommendation**: Before deploying customer support agents, establish an evaluation framework: create golden datasets of customer support queries with expected responses, implement automated scoring (relevance, accuracy, helpfulness), and set up regression testing for prompt/model changes.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms, no p99/p95 latency targets, no error budget tracking, no availability targets. Spring Boot Actuator is included in `build.gradle` (`spring-boot-starter-actuator`) but no custom metric endpoints or SLO dashboards are configured.
- **Gap**: No SLO definitions or monitoring. Cannot measure whether the application meets reliability requirements for agent-driven workloads.
- **Recommendation**: Define SLOs for critical API endpoints: p99 latency < 500ms, availability > 99.9%, error rate < 0.1%. Create CloudWatch alarms and dashboards. Extend SLOs to agent-specific metrics once agents are deployed (task success rate, hallucination rate).

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment rollback mechanism. No blue/green, canary, feature flags, prompt versioning, or configuration rollback capability found. No CodeDeploy, Argo Rollouts, or Helm rollback configuration.
- **Gap**: No rollback capability for code, configuration, or (future) prompts. Failed deployments or agent prompt regressions cannot be quickly reversed.
- **Recommendation**: Implement ECS rolling deployments with automatic rollback on CloudWatch alarm triggers. Add feature flags (AWS AppConfig or LaunchDarkly) for gradual agent feature rollout. Version all agent prompts in a separate configuration store with instant rollback capability.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage exists and no token tracking infrastructure. No custom CloudWatch metrics for AI/LLM costs. No usage attribution by user, feature, or workflow.
- **Gap**: No LLM cost tracking. When agents are deployed for customer support, token usage could become a significant cost driver without visibility.
- **Recommendation**: Implement per-request token tracking from the start of agent development. Log input/output token counts with user ID, conversation ID, and workflow type attribution. Create CloudWatch dashboards for cost monitoring. Set up cost anomaly alerts. Implement tiered retention policies for observability data.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics. Spring Boot Actuator is a dependency in `build.gradle` but no `@Timed`, `@Counted`, or custom metric registrations found. No CloudWatch `put_metric_data` calls. No dashboards tracking business outcomes (orders placed, baskets converted, user registrations).
- **Gap**: No business outcome metrics. Cannot measure whether agent interactions improve customer support resolution or order management efficiency.
- **Recommendation**: Publish custom CloudWatch metrics for key business events: baskets created, items added/removed, user registrations, login attempts. When agents are added, track agent-specific business metrics: support tickets resolved, order issues handled, customer satisfaction scores.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection, no error rate alarms, no latency monitoring, no PagerDuty/OpsGenie integration. No alerting infrastructure of any kind found.
- **Gap**: No anomaly detection or alerting. Agent reasoning loops, sudden latency increases, or elevated error rates would go unnoticed.
- **Recommendation**: Enable CloudWatch anomaly detection on API error rates and latency. Create composite alarms for critical paths. When agents are deployed, add behavioral anomaly detection: alert on unusual tool call patterns (e.g., agent calling 15 tools instead of 3, indicating a reasoning loop).

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment configuration found in the repository. No CodeDeploy, Helm, Argo, or any deployment tool configuration. Deployments are presumed manual.
- **Gap**: No automated deployment strategy. Changes go directly to production with no canary or blue/green safety net.
- **Recommendation**: Implement ECS rolling deployments with health check gates. Progress to blue/green deployments using CodeDeploy with ECS for zero-downtime releases. Add canary analysis for agent prompt/model changes.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files exist in the repository. No `src/test/` directory. No JUnit, Mockito, TestContainers, or any testing framework configuration beyond the `spring-boot-starter-test` dependency in `build.gradle`. No Postman/Newman collections. No contract tests.
- **Gap**: Zero test coverage. No integration tests, no unit tests, no API contract tests. Cannot verify agent tool behavior or regression-test API changes.
- **Recommendation**: Create a `src/test/` directory with JUnit 5 integration tests for all API endpoints. Add API contract tests that validate request/response schemas. These tests are essential before agents start using the APIs as tools — any breaking change could cause agent failures.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON), no SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No self-healing patterns (auto-restart, auto-scaling on failure). The `HealthController.java` provides basic health check endpoints (`/health/ping`, `/health/ishealthy`, `/health/dbping`) but these are not connected to any automated response.
- **Gap**: No incident response automation. Health checks exist but are not connected to remediation workflows. Agent failures would require manual investigation and resolution.
- **Recommendation**: Create machine-readable runbooks for common failure scenarios (database connectivity loss, high latency, agent reasoning loops). Connect ECS health checks to automatic task replacement. Implement EventBridge rules for automated incident notification and initial triage.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No SLO definition files, no CODEOWNERS files, no team ownership assignments for observability assets. No platform team tooling configuration. No per-service dashboards or alarms. No observability-as-a-product evidence.
- **Gap**: No observability ownership model. No clarity on who would own agent-level SLOs (task success rate, hallucination rate, tool error rate) once agents are deployed.
- **Recommendation**: Establish an observability ownership model: define service-level SLOs with named owners, create per-service dashboards, and document the shared responsibility between platform and product teams. Plan for agent-level SLO ownership from the start.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 2/4, INF-Q1: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Triggered | Medium | High | INF-Q1: 1/4, No Dockerfile found | High |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Triggered | High | High | INF-Q2: 1/4, DATA-Q10: 2/4 | Medium |
| Move to Managed Analytics | Triggered | Low | Medium | INF-Q8: 1/4 | Low |
| Move to Modern DevOps | Triggered | High | High | INF-Q5: 1/4, INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Containers + Move to Modern DevOps — Containerize the application and establish CI/CD simultaneously. These have no dependencies on each other and both produce immediate value.

**Parallel Track 2**: Move to Managed Databases — Can proceed in parallel with Track 1. Migrate MySQL to Amazon RDS/Aurora and plan DynamoDB adoption for the basket service.

**Parallel Track 3**: Move to AI — Begin data foundations (vector store, RAG pipeline) and agent framework integration in parallel with infrastructure modernization.

**Sequential Dependencies**: Move to Containers must complete before Move to Cloud Native (must containerize before decomposing into microservices). Move to Managed Databases should precede full Move to Cloud Native (database per service pattern requires managed databases). Move to AI depends on Move to Modern DevOps (need CI/CD for agent deployment pipeline) and partially on Move to Managed Databases (vector store requires managed infrastructure).

### Move to Containers

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q1: Score 1/4 — Application runs on raw EC2 (`HealthController.java` uses `EC2MetadataUtils`). No Dockerfile or container orchestration found.
  - APP-Q4: Score 2/4 — Monolith needs containerization as the first step toward decomposition.
- **Current State**: Java Spring Boot application deployed directly on EC2 instances. No Dockerfile, no container image, no container orchestration. Commented-out Docker task in `build.gradle` suggests containerization was considered but never implemented.
- **Target State**: Application packaged as a Docker container image, stored in Amazon ECR, and deployed on Amazon ECS with Fargate. Container health checks connected to load balancer.
- **Key Activities**:
  1. Create a multi-stage Dockerfile (Gradle build → JRE runtime)
  2. Set up Amazon ECR repository for container images
  3. Deploy to Amazon ECS on Fargate with task definitions and service configuration
  4. Configure Application Load Balancer with health checks pointing to `/health/ishealthy`
- **Dependencies**: None — this is foundational and should start immediately
- **Estimated Effort**: High (new Dockerfile, ECS cluster, task definitions, ALB, service config)
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Managed Databases

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q2: Score 1/4 — MySQL database with no IaC evidence of managed service. Connection via JDBC in `application.properties`.
  - DATA-Q10: Score 2/4 — MySQL connector 8.0.11 (2018) in `build.gradle`, no engine version pinned in IaC.
- **Current State**: MySQL database accessed via JDBC (`jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`). No IaC defining the database. No automated failover, backups, or version pinning.
- **Target State**: Product catalog on Amazon Aurora MySQL-Compatible with automated failover. Shopping basket data on Amazon DynamoDB (key-value access pattern: lookup by user UUID). All databases defined in IaC with pinned engine versions and automated backups.
- **Key Activities**:
  1. Define Amazon RDS for MySQL (or Aurora MySQL-Compatible) in IaC with explicit engine version
  2. Migrate database using AWS DMS with Schema Conversion Tool
  3. Evaluate DynamoDB migration for the basket service (key-value pattern with `uuid` as partition key)
  4. Move database credentials to AWS Secrets Manager
  5. Update MySQL connector to latest 8.x version
- **Dependencies**: None — can proceed in parallel with containerization
- **Estimated Effort**: Medium (schema is simple, no stored procedures, standard MySQL)
- **Roadmap Phase Alignment**: Phase 1 (version pinning) and Phase 2 (managed migration)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 2/4 — Monolith with identifiable modules (Unicorn, Basket, User domains) but shared database
  - INF-Q1: Score 1/4 — EC2-based compute
  - APP-Q3: Score 1/4 — 100% synchronous communication
  - APP-Q10: Score 1/4 — No async processing for long-running operations
- **Current State**: Monolithic Spring Boot application with synchronous HTTP communication. All domains (product catalog, basket, user) deployed as a single unit sharing one MySQL database.
- **Target State**: Decomposed into independently deployable containerized services (Product Service, Basket Service, User Service) communicating via Amazon SQS and EventBridge, each with its own data store. Agent tools map to individual service APIs.
- **Key Activities**:
  1. Introduce Amazon SQS for asynchronous basket operations
  2. Add Amazon EventBridge for domain event publishing (user registered, item added to basket)
  3. Extract Basket service as the first microservice (clear domain boundary, key-value data pattern ideal for DynamoDB)
  4. Implement API Gateway routing to direct traffic between monolith and extracted services
- **Dependencies**: Move to Containers (must containerize before decomposing), Move to Managed Databases (database-per-service pattern)
- **Estimated Effort**: High (service extraction, data separation, messaging infrastructure)
- **Roadmap Phase Alignment**: Phase 2 (Agent Foundations) and Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q5: Score 1/4 — No IaC (zero Terraform, CloudFormation, CDK, or Helm files)
  - INF-Q6: Score 1/4 — No CI/CD pipeline definitions
  - OPS-Q9: Score 1/4 — No deployment strategy
  - OPS-Q10: Score 1/4 — No test files exist in the repository
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: Zero automation. No IaC, no CI/CD, no testing, no tracing, no deployment strategy. All infrastructure and deployments are manual.
- **Target State**: Full CI/CD pipeline (CodePipeline → CodeBuild → ECR → ECS deploy) with automated testing, IaC-defined infrastructure (CDK), distributed tracing (X-Ray), and blue/green deployment strategy.
- **Key Activities**:
  1. Adopt AWS CDK for infrastructure definitions (VPC, ECS, RDS, API Gateway)
  2. Create CI/CD pipeline with CodePipeline and CodeBuild
  3. Add unit and integration tests to the project
  4. Implement distributed tracing with AWS X-Ray
  5. Configure structured JSON logging with CloudWatch Logs
  6. Set up blue/green deployments with CodeDeploy for ECS
- **Dependencies**: Move to Containers (CI/CD pipeline deploys container images)
- **Estimated Effort**: High (building from zero across IaC, CI/CD, testing, observability)
- **Roadmap Phase Alignment**: Phase 1 (IaC and CI/CD basics) and Phase 2 (advanced observability and deployment)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks. AWS SDK v1 in `build.gradle` predates Bedrock.
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: Zero AI/agent capabilities. No vector store, no RAG pipeline, no agent framework, no evaluation infrastructure. The application has REST APIs that return JSON but no mechanism for AI-powered interaction.
- **Target State**: Customer-facing AI agents for support and order management built with Strands Agents SDK or Amazon Bedrock Agents. Product catalog and support knowledge accessible via RAG (Bedrock Knowledge Bases + OpenSearch). Agent tool invocations through OpenAPI-documented APIs. Automated evaluation pipeline for agent quality.
- **Key Activities**:
  1. Create OpenAPI specs for all existing REST endpoints (agent tool discovery)
  2. Provision Amazon OpenSearch Service for vector storage
  3. Build RAG pipeline using Amazon Bedrock Knowledge Bases (product catalog + support docs)
  4. Build customer support agent using Strands Agents SDK or Amazon Bedrock Agents
  5. Implement agent evaluation framework with golden datasets
  6. Add LLM cost tracking with per-request token attribution
  7. Implement human approval workflows via Step Functions for high-risk agent actions
- **Dependencies**: Move to Modern DevOps (CI/CD for agent deployment), Move to Managed Databases (vector store infrastructure)
- **Estimated Effort**: High (new capability built from scratch)
- **Roadmap Phase Alignment**: Phase 1 (OpenAPI specs, initial agent PoC), Phase 2 (RAG pipeline, vector store), Phase 3 (production agents with evals)
- **Relevant Learning Materials**: Module 7 — Move to AI

### Move to Managed Analytics

- **Priority**: Medium
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - INF-Q8: Score 1/4 — No managed streaming service for event-driven data
- **Current State**: No streaming, analytics, or event-driven data infrastructure. The `DataReplicationController.java` performs synchronous full-table reads.
- **Target State**: Amazon EventBridge for domain event streaming. Event-driven analytics on customer behavior and agent interactions for continuous improvement.
- **Key Activities**:
  1. Implement EventBridge for domain events (aligned with Move to Cloud Native)
  2. Add event-driven analytics for agent interaction patterns
- **Dependencies**: Move to Cloud Native (event-driven architecture is a prerequisite)
- **Estimated Effort**: Low (EventBridge is lightweight; analytics can be added incrementally)
- **Roadmap Phase Alignment**: Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

---

## Microservices Decomposition Strategy

This monolith would benefit from service extraction to create clear agent tool boundaries. The Unishop application has three identifiable domains — Product Catalog (Unicorn), Shopping Basket, and User Management — each with separate controllers, services, and repository interfaces. The Basket domain is the strongest extraction candidate: it has a clear key-value access pattern (lookup by user UUID) ideal for DynamoDB, a well-defined API surface (`POST/DELETE/GET /unicorns/basket`), and would map directly to an "Order Management" agent tool. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing REST API surface (`/unicorns`, `/unicorns/basket/{userUuid}`, `/user`) once OpenAPI specifications are generated.

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Product Query Agent** — Build an API-aware agent that can discover and invoke the existing `/unicorns` endpoint to answer customer questions about product availability, descriptions, and pricing. A customer support agent can query the full product catalog and provide natural language responses about unicorn products.
   - **Leverages**: Existing `GET /unicorns` REST endpoint returning structured JSON (Jackson-serialized `Unicorn` objects with uuid, name, description, price, image fields)
   - **Effort**: Low
   - **Value**: Immediate customer support capability — agents can answer "What unicorn products do you have?" and "How much does the UnicornFloat cost?"

2. **Order Management Basket Agent** — Build a customer support agent that can check order/basket status by querying the `/unicorns/basket/{userUuid}` endpoint. Agents can look up what items a customer has in their basket and help with order-related inquiries.
   - **Leverages**: Existing `GET /unicorns/basket/{userUuid}` endpoint returning structured JSON basket contents
   - **Effort**: Low
   - **Value**: Enables "What's in my basket?" and "Can you check my order?" agent interactions for customer support

3. **Knowledge Base Agent from Schema Documentation** — Build a RAG-based knowledge agent using the existing database schema (`database/create_tables.sql`) and product seed data as initial knowledge. The 10 pre-loaded unicorn products provide a starting dataset for semantic search.
   - **Leverages**: SQL schema file with table definitions and 10 product records with names, descriptions, and prices
   - **Effort**: Medium
   - **Value**: Demonstrates RAG capability with real product data; foundation for expanding to support documentation and policies

4. **Natural Language to SQL Query Agent** — Build a data query agent that translates natural language customer support questions into SQL queries against the `unishop` schema. The clean 3-table schema (unicorns, unicorns_basket, unicorn_user) with clear column names is ideal for text-to-SQL.
   - **Leverages**: Well-documented database schema in `database/create_tables.sql` with clear table/column naming and UNIQUE constraints
   - **Effort**: Medium
   - **Value**: Enables support agents to answer complex queries like "Show me all baskets containing UnicornFloat" without writing SQL

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.
> All wins are framed around customer support and order management to align with the goal context.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

These items deliver immediate value and establish the foundation for agent development:

1. **Generate OpenAPI specs** — Add `springdoc-openapi-ui` to `build.gradle` and annotate controllers to auto-generate OpenAPI 3.0 specifications. This is the single most impactful action for agent enablement — agents need machine-readable API descriptions to discover and invoke tools.
2. **Containerize the application** — Create a Dockerfile for the Spring Boot application. Push images to Amazon ECR. Deploy to Amazon ECS on Fargate. This moves off EC2 and enables scalable, repeatable deployments.
3. **Move secrets to Secrets Manager** — Remove hardcoded credentials from `application.properties` (`MonoToMicroUser`/`MonoToMicroPassword`). Store in AWS Secrets Manager and reference via ECS task definition secrets.
4. **Establish IaC with CDK** — Define the ECS cluster, VPC, ALB, and RDS instance in AWS CDK. This enables repeatable infrastructure provisioning and is prerequisite for CI/CD.
5. **Create CI/CD pipeline** — Set up CodePipeline with CodeBuild for automated build, test, container image push, and ECS deployment. Add basic health check verification post-deploy.
6. **Build first agent PoC** — Create a simple customer support agent (Python with Strands Agents SDK) that calls `GET /unicorns` and `GET /unicorns/basket/{userUuid}` as tools. Deploy on ECS alongside the Unishop monolith. Demonstrates agent value immediately.

### Phase 2 — Agent Foundations (Months 1–3)

Structural improvements that establish the data and security foundations for production agents:

1. **Migrate to managed database** — Define Amazon RDS for MySQL (or Aurora MySQL-Compatible) in CDK with explicit engine version pinning. Migrate using AWS DMS. Evaluate DynamoDB for the basket service (key-value pattern).
2. **Deploy API Gateway** — Place Amazon API Gateway in front of the ECS service. Configure throttling, request validation, and API keys. This is critical for agent safety — prevents runaway agent loops from overwhelming the backend.
3. **Implement authentication** — Configure Amazon Cognito as the identity provider. Enable JWT validation in the Spring Security configuration. Issue scoped API keys for agent access. Remove the `permitAll()` configuration.
4. **Build RAG pipeline** — Provision Amazon OpenSearch Service for vector storage. Set up Amazon Bedrock Knowledge Bases with product catalog data and customer support documentation. Implement embedding generation and semantic search.
5. **Add structured logging and tracing** — Configure SLF4J/Logback with JSON output. Add AWS X-Ray instrumentation. Implement correlation IDs across all requests. Essential for debugging agent tool invocations.
6. **Implement human approval workflows** — Build AWS Step Functions workflows with `waitForTaskToken` for high-risk agent actions (basket modifications above thresholds, user account changes). Critical safety control for production agents.
7. **Add integration tests** — Create JUnit 5 test suite covering all API endpoints. Add API contract tests. Run tests in CI/CD pipeline. Ensures agent tools don't break during code changes.
8. **Implement SQS-based async processing** — Introduce Amazon SQS for basket write operations. Add Amazon EventBridge for domain event publishing. Begin decoupling the monolith for future service extraction.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

Advanced capabilities that enable production-grade agent operations and continuous improvement:

1. **Deploy production customer support agent** — Upgrade PoC agent to production quality with full RAG integration, conversation memory (DynamoDB), multi-turn support, and escalation workflows.
2. **Implement agent evaluation framework** — Create golden datasets for customer support scenarios. Build automated scoring pipeline (relevance, accuracy, helpfulness, safety). Run evaluations in CI/CD for prompt/model changes.
3. **Add LLM cost tracking** — Implement per-request token tracking with user/conversation/workflow attribution. Create CloudWatch dashboards for cost monitoring. Set up cost anomaly alerts.
4. **Extract Basket service** — Using Strangler Fig pattern, extract the shopping basket functionality into an independent ECS service backed by DynamoDB. Route via API Gateway. Map to a dedicated "Order Management" agent tool.
5. **Implement advanced observability** — Define SLOs for API endpoints and agent metrics (task success rate, hallucination rate). Enable CloudWatch anomaly detection. Create agent-specific dashboards. Establish observability ownership model.
6. **Add EventBridge analytics** — Stream domain events (basket updates, user actions, agent interactions) to EventBridge. Build analytics dashboards for agent effectiveness and customer support quality metrics.
7. **Implement blue/green deployments** — Configure CodeDeploy with ECS for blue/green deployments. Add canary analysis for agent prompt/model changes. Version all agent configurations with instant rollback.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
  - Directly applicable: ECS is the preferred container orchestration platform for this assessment
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
  - Covers migration from MySQL to RDS/Aurora and DynamoDB adoption
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Covers IaC, CI/CD, testing, and observability — all critical gaps in this assessment
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Critical pathway for the agentic-ai-enablement goal
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7

---

## Appendix: Evidence Index

| # | File | Key Findings |
|---|------|-------------|
| 1 | `build.gradle` | Java 8, Spring Boot 2.1.6, MySQL connector 8.0.11, AWS SDK v1 1.11.567, Spring Security OAuth2, MyBatis, commented-out Docker task, Spring Boot Actuator |
| 2 | `src/main/resources/application.properties` | Hardcoded DB credentials (MonoToMicroUser/MonoToMicroPassword), MySQL JDBC connection, port 8080, env var for DB endpoint |
| 3 | `database/create_tables.sql` | 3-table schema (unicorns, unicorns_basket, unicorn_user), no stored procedures, UNIQUE constraints, 10 seed products |
| 4 | `src/main/java/com/monoToMicro/Application.java` | @SpringBootApplication entry point, CORS security bypass with "not recommended for production" comment |
| 5 | `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | GET /unicorns endpoint, @PreAuthorize("permitAll()"), synchronous service call |
| 6 | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | POST/DELETE/GET /unicorns/basket endpoints, all permitAll(), synchronous processing |
| 7 | `src/main/java/com/monoToMicro/rest/controller/UserController.java` | POST /user and POST /user/login endpoints, email-based login without password verification |
| 8 | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | EC2MetadataUtils import confirming EC2 deployment, System.out.println logging, health endpoints |
| 9 | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | Synchronous full-table basket scan, no event-driven replication |
| 10 | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | @EnableResourceServer with authorizeRequests().anyRequest().permitAll() — security disabled |
| 11 | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | Service layer with synchronous repository calls, no resilience patterns |
| 12 | `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | UUID generation for users, direct repository call, no event publishing |
| 13 | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | @Repository @Transactional, try/catch with e.printStackTrace(), MyBatis mapper usage |
| 14 | `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | Synchronized create method, e.printStackTrace() error handling |
| 15 | `src/main/java/com/monoToMicro/core/model/Unicorn.java` | @JsonInclude(NON_NULL), uuid/name/description/price/image fields |
| 16 | `src/main/java/com/monoToMicro/core/model/User.java` | @JsonInclude(NON_NULL), PII fields (email, firstName, lastName) exposed without redaction |
| 17 | `src/main/java/com/monoToMicro/core/model/CoreModel.java` | Base model with @JsonIgnore on internal fields, Joda DateTime dependency |
| 18 | `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | Centralized mapper configuration, SqlSessionFactory setup for all 3 mappers |
| 19 | `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | INSERT IGNORE (basic idempotency), JOIN queries, getAllBaskets with resultMap |
| 20 | `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | insert ignore into unicorn_user (UNIQUE email constraint), getByEmail query |
