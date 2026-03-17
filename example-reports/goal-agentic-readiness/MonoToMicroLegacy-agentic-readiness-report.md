# Agentic Readiness Assessment Report
**Target**: MonoToMicroLegacy
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

This legacy Java monolith e-commerce application (Unishop) scores **1.21 / 4.0** overall, indicating it is far from agentic readiness across all five assessment dimensions. The application is a Spring Boot 2.1.x monolith running on raw EC2 with a MySQL database, zero Infrastructure as Code, no CI/CD pipelines, no API documentation, and hardcoded credentials in plaintext. The strongest area is Data Foundations (1.82/4.0), owing to a simple single-database architecture with a clean MyBatis data access layer and no stored procedures — which simplifies future database migration. Every other category scores at or near 1.0/4.0, revealing fundamental gaps in infrastructure automation, security posture, application architecture, and operational observability that must be addressed before any agentic capabilities can be safely introduced.

### Overall Score: 1.21 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.0 / 4.0 | 🟠 |
| Application Architecture | 1.23 / 4.0 | 🟠 |
| Data Foundations | 1.82 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.0 / 4.0 | 🟠 |
| Operations & Observability | 1.0 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

1. **SEC-Q1: Secret Management — Hardcoded credentials in plaintext** — `application.properties` contains database username (`MonoToMicroUser`) and password (`MonoToMicroPassword`) in plaintext. This is the single most urgent security risk: any agent or automated system interacting with this codebase would inherit and potentially expose these credentials. **First step**: Migrate credentials to AWS Secrets Manager and update `application.properties` to reference secrets via the AWS SDK or Spring Cloud AWS Secrets Manager integration.

2. **INF-Q5: Infrastructure as Code — Zero IaC coverage** — No Terraform, CDK, CloudFormation, or Helm charts exist. All infrastructure (EC2, MySQL, networking) is presumably manually provisioned. Without IaC, there is no reproducible, auditable way to provision or modify environments — a fundamental blocker for agent-driven infrastructure automation. **First step**: Create a Terraform or CDK project defining the current EC2 instance, VPC, security groups, and database as code.

3. **INF-Q6: CI/CD — No automated deployment pipelines** — No GitHub Actions, CodePipeline, Jenkins, or any CI/CD definition exists. The `build.gradle` has a commented-out Docker task but no active automation. Agents cannot safely deploy changes without automated, tested deployment pipelines. **First step**: Create a basic CI pipeline (GitHub Actions or CodeBuild) that builds the Gradle project, runs tests, and produces an artifact.

4. **INF-Q1: Compute — Running on raw EC2** — `HealthController.java` confirms the application runs on EC2 via `EC2MetadataUtils.getInstanceInfo()`. No managed container orchestration (ECS/EKS) or serverless (Lambda) is used. Raw EC2 requires manual patching, scaling, and maintenance that blocks agentic workload patterns. **First step**: Create a Dockerfile for the Spring Boot application and deploy to ECS Fargate or EKS.

5. **APP-Q2: API Documentation — No OpenAPI/Swagger specs** — REST endpoints exist across 6 controllers (`/unicorns`, `/user`, `/unicorns/basket`, `/health`, `/data`) but have no OpenAPI documentation. Agents require machine-readable API specifications to discover and invoke tools. **First step**: Add `springdoc-openapi-ui` to `build.gradle` to auto-generate OpenAPI specs from existing Spring MVC annotations.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: `HealthController.java` uses `EC2MetadataUtils.getInstanceInfo()` (line 43), confirming the application runs directly on EC2 instances. No ECS, EKS, Lambda, or Fargate resource definitions exist anywhere in the repository. The `build.gradle` `bootJar` task includes `launchScript()`, indicating the JAR is deployed as a Linux init service directly on EC2.
- **Gap**: 100% of compute is raw EC2. No managed container orchestration or serverless compute is used.
- **Recommendation**: Create a `Dockerfile` for the Spring Boot application and deploy to Amazon ECS on Fargate or Amazon EKS. This eliminates OS patching overhead and enables auto-scaling, health checks, and rolling deployments.

#### INF-Q2: Databases
- **Score**: 1/4 ❌
- **Finding**: `application.properties` defines `spring.datasource.url: jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop` with a direct JDBC connection. `build.gradle` includes `mysql:mysql-connector-java:8.0.11`. `database/create_tables.sql` uses MySQL-specific `ENGINE=InnoDB`. No IaC exists to confirm whether the MySQL instance is Amazon RDS or self-managed on EC2. The database endpoint is parameterized via environment variable, but no managed database configuration is evidenced.
- **Gap**: Database management status is ambiguous. No IaC confirms managed RDS. No automated failover, backup, or patching configuration is visible.
- **Recommendation**: Define the database in IaC as Amazon RDS for MySQL or Aurora MySQL. Enable Multi-AZ, automated backups, and automatic minor version upgrades. Use AWS DMS if migrating from a self-managed MySQL instance.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow engine detected. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` follows simple synchronous request-response patterns without state machine logic.
- **Gap**: No dedicated workflow orchestration service exists. Future agentic workflows (multi-step tool calling, human-in-the-loop approvals) will require orchestration.
- **Recommendation**: Introduce AWS Step Functions for any multi-step business workflows. Start with the data replication endpoint (`/data` in `DataReplicationController.java`) as a candidate for Step Functions orchestration.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, MSK, Kafka, or RabbitMQ dependencies found in `build.gradle`. No messaging imports in any Java file. All communication is synchronous HTTP between controllers, services, and repositories within a single process.
- **Gap**: No asynchronous messaging infrastructure exists. Agent workflows that need to process tasks asynchronously or decouple services have no messaging backbone.
- **Recommendation**: Introduce Amazon SQS for task queuing and Amazon SNS/EventBridge for event-driven communication. Start with basket operations (add/remove from cart) as candidates for async processing.

#### INF-Q5: Infrastructure as Code
- **Score**: 1/4 ❌
- **Finding**: Zero IaC files found. No `.tf` (Terraform), CDK stacks, CloudFormation templates, Helm charts, or Kustomize files exist in the repository. The entire infrastructure stack (EC2, database, networking) is provisioned outside the codebase.
- **Gap**: 0% IaC coverage. Infrastructure changes are manual, unauditable, and unreproducible.
- **Recommendation**: Create a Terraform or AWS CDK project to define all infrastructure: VPC, subnets, security groups, EC2/ECS, RDS, and any load balancers. Start by reverse-engineering the current deployment topology into IaC.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No `.github/workflows/`, `Jenkinsfile`, `buildspec.yml`, or `.gitlab-ci.yml` found. `build.gradle` contains a commented-out `docker` task block, suggesting containerization was considered but not implemented. The `bootJar` with `launchScript()` indicates manual JAR deployment.
- **Gap**: No automated build, test, or deploy pipeline. Deployments are manual.
- **Recommendation**: Create a CI/CD pipeline using AWS CodePipeline + CodeBuild or GitHub Actions. Define stages for: build (Gradle), test (once tests are added), package (Docker image), and deploy (to ECS/EKS).

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: No API Gateway, ALB, or CloudFront configuration found (no IaC exists). The Spring Boot application exposes port 8080 directly (`application.properties`: `server.port=8080`). `ResourceServerConfig.java` has `permitAll()` with no gateway-level throttling or request validation.
- **Gap**: No API entry point with throttling, authentication, or request validation. Direct service exposure increases attack surface.
- **Recommendation**: Deploy an Application Load Balancer (ALB) in front of the application with health check targets. For agentic access, add Amazon API Gateway with throttling, request validation, and authorization.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or streaming infrastructure detected. No streaming SDK imports in `build.gradle` or any Java source file. The application is purely request-response.
- **Gap**: No real-time streaming capability exists. Agent workflows that need real-time data feeds have no streaming infrastructure.
- **Recommendation**: If real-time product updates or basket event streaming is needed, introduce Amazon Kinesis Data Streams or Amazon MSK Serverless.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions found (no IaC exists). Network security configuration is entirely absent from the codebase. The application is confirmed running on EC2 but its network posture is unknown.
- **Gap**: Network security is not codified. Cannot verify whether the application is in a private subnet, whether security groups enforce least privilege, or whether the database is network-isolated.
- **Recommendation**: Define VPC architecture in IaC with public subnets for load balancers and private subnets for application and database tiers. Create security groups with least-privilege rules (e.g., app SG allows inbound only from ALB SG on port 8080).

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No Auto Scaling Groups, ECS Service auto-scaling, or Lambda concurrency limits configured. No IaC defines any scaling policies. Single EC2 instance deployment implied by `HealthController.java` returning single instance metadata.
- **Gap**: No auto-scaling capability. The application cannot handle traffic spikes and has no capacity management.
- **Recommendation**: After containerizing the application, configure ECS Service auto-scaling or EKS Horizontal Pod Autoscaler with CPU/memory-based scaling policies.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`) with Spring Boot 2.1.0/2.1.6 (`springBootVersion = '2.1.0.RELEASE'`, plugin version `2.1.6.RELEASE`). Java has a growing agent ecosystem (Spring AI, LangChain4j) but is less mature than Python or TypeScript for agentic frameworks.
- **Gap**: Java 8 is end-of-life. Spring Boot 2.1.x is end-of-life. The agent framework ecosystem for Java is smaller than Python/TypeScript.
- **Recommendation**: Upgrade to Java 17+ and Spring Boot 3.x to access modern features (virtual threads, Spring AI integration). Consider adding Spring AI for agent framework capabilities.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI or Swagger specifications found. No `@ApiOperation`, `@OpenAPIDefinition`, `@Schema`, or springdoc annotations in any controller. REST endpoints exist in `UnicornController.java` (`/unicorns`), `UserController.java` (`/user`, `/user/login`), `BasketController.java` (`/unicorns/basket`), `HealthController.java` (`/health`), and `DataReplicationController.java` (`/data`) but are entirely undocumented.
- **Gap**: No machine-readable API documentation. Agents cannot discover or understand API capabilities without OpenAPI specs.
- **Recommendation**: Add `springdoc-openapi-ui` to `build.gradle` to auto-generate OpenAPI 3.0 specs from existing Spring MVC annotations. Add `@Operation` and `@Schema` annotations to controllers and models for richer documentation.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous communication. All controller methods are synchronous request-response. `UnicornController.getUnicorns()` → `UnicornServiceImpl.getUnicorns()` → `UnicornRepositoryImpl.getUnicorns()` → `UnicornMapper.getUnicorns()` — all blocking calls within a single thread. No `@Async` annotations, no message publishing, no event-driven handlers.
- **Gap**: No async communication patterns. All operations block the request thread until the database returns.
- **Recommendation**: Introduce async patterns for basket operations and data replication. Use Spring `@Async` for non-blocking operations and Amazon SQS for inter-service communication when decomposing the monolith.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single deployable Spring Boot application (monolith) with a single `Application.java` entry point and single `build.gradle`. All domains — product catalog (Unicorn), user management (User), and shopping cart (Basket) — are packaged together. However, there is meaningful modularity: service interfaces (`UnicornService`, `UserService`, `HealthService`), repository pattern with interfaces and implementations, and clear package separation (`controller/service/repository/model/config`). The coupling point is the shared MySQL database — `UnicornMapper.xml` performs JOINs across `unicorns` and `unicorns_basket` tables.
- **Gap**: Monolith with identifiable modules but database-level coupling. Cross-table JOINs in `UnicornMapper.xml` prevent clean service extraction without database refactoring.
- **Recommendation**: Use the existing service interface boundaries as starting points for microservice extraction. Start by decoupling the `unicorns_basket` table from `unicorns` using the Strangler Fig pattern, replacing JOINs with API calls.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: All controllers return `ResponseEntity<T>` with Spring Boot's default Jackson JSON serialization. Model classes (`Unicorn.java`, `User.java`) use `@JsonInclude(JsonInclude.Include.NON_NULL)` for clean JSON output. Structured JSON responses across all endpoints.
- **Gap**: JSON responses are present but lack a consistent envelope/error format (e.g., no standardized error response with error codes and messages).
- **Recommendation**: Implement a consistent API response envelope with status, data, and error fields. Add proper error handling with structured error responses instead of raw HTTP status codes.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No dedicated workflow orchestration. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` is simple CRUD — get unicorns, add to basket, create user, login. No complex workflows, sagas, or state machines detected. `DataReplicationController.java` has a `/data` endpoint that retrieves all baskets but with no orchestration logic.
- **Gap**: No workflow engine for multi-step operations. Agentic workflows require orchestration for tool chaining, retries, and human-in-the-loop patterns.
- **Recommendation**: Introduce AWS Step Functions for any future multi-step business processes. Design agent tool-use workflows as Step Functions state machines with error handling and retry logic.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: `UnicornMapper.xml` uses `INSERT IGNORE INTO unicorns_basket` which provides MySQL-specific deduplication for basket add operations. `UserMapper.xml` also uses `insert ignore into unicorn_user`. However, these are database-level workarounds, not application-level idempotency patterns. No idempotency-key headers in API contracts. No deduplication IDs for any operation.
- **Gap**: No proper idempotency implementation. `INSERT IGNORE` silently drops duplicates rather than returning consistent responses. No client-supplied idempotency keys.
- **Recommendation**: Implement idempotency-key headers for write operations (POST to `/user`, POST to `/unicorns/basket`). Store idempotency keys in a dedicated table or cache and return the original response for duplicate requests.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. `ResourceServerConfig.java` configures Spring Security with `authorizeRequests().anyRequest().permitAll()` — no throttling. No API Gateway, WAF, or application-level rate limiting middleware (e.g., Bucket4j, Guava RateLimiter) in `build.gradle`.
- **Gap**: No rate limiting. Agents or external clients can make unlimited requests, risking resource exhaustion.
- **Recommendation**: Add API Gateway with throttling (burst and rate limits) in front of the application. As a quick win, add Bucket4j or Spring Boot rate limiting middleware to critical endpoints.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry logic, or timeout configurations found. No Resilience4j, Hystrix, or Spring Retry in `build.gradle`. Exception handling in `UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, and `HealthRepositoryImpl.java` is basic `try-catch` with `e.printStackTrace()` and returning `null`. `DataReplicationController.java` even returns `null` directly on failure instead of a proper error response.
- **Gap**: No resilience patterns. Database failures result in null returns and stack traces to stdout. No retry, timeout, or circuit breaker protection.
- **Recommendation**: Add Resilience4j to `build.gradle`. Implement circuit breakers around database calls, retry with exponential backoff for transient failures, and timeouts on all external calls. Replace `e.printStackTrace()` with structured error handling.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: No background job frameworks (Celery, Bull, SQS workers), no `@Async` annotations, no async job handlers. All operations are synchronous CRUD. The `DataReplicationController.java` `/data` endpoint retrieves all baskets synchronously — this could become long-running as data grows but has no async handling.
- **Gap**: No async infrastructure for operations that may exceed 30 seconds. The data replication endpoint is a candidate for async processing.
- **Recommendation**: Implement the data replication endpoint as an async job using SQS + a background worker or AWS Step Functions. Return a job ID immediately and provide a status polling endpoint.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL versioning (`/v1/`, `/v2/`), no `Accept-Version` headers, no versioning annotations. Endpoints are unversioned: `/unicorns`, `/user`, `/unicorns/basket/{userUuid}`, `/health/ping`, `/health/ishealthy`, `/health/dbping`, `/data`.
- **Gap**: No API versioning strategy. Breaking changes to APIs will disrupt all clients simultaneously, including agent tool integrations.
- **Recommendation**: Adopt URL path versioning (e.g., `/v1/unicorns`) for all endpoints. Implement backward compatibility guarantees for at least one prior version.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: No service discovery, service mesh, or API catalog. As a monolith, the application does not currently need inter-service discovery. However, there are no mechanisms for service registration, discovery, or health checking beyond the basic `/health` endpoints.
- **Gap**: No service discovery infrastructure. Required for microservice decomposition and agent tool registry.
- **Recommendation**: When decomposing into microservices, implement AWS Cloud Map for service discovery or use API Gateway as a service catalog. For agents, create a tool registry that maps to discovered service endpoints.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent SDK imports in `build.gradle`. No Amazon Bedrock, LangChain4j, Spring AI, OpenAI, or Anthropic dependencies. The AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567`) is present but only used for `EC2MetadataUtils` in `HealthController.java`. No AI integration points identified.
- **Gap**: No AI or agent framework integration. The application has no AI capabilities and no integration points for agent tool-use.
- **Recommendation**: Add Spring AI or LangChain4j to the project. Create agent-compatible tool endpoints that wrap existing business logic (e.g., product search, basket management). Integrate with Amazon Bedrock for LLM capabilities.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database detected. No OpenSearch, pgvector, Pinecone, Weaviate, Chroma, or Amazon Bedrock Knowledge Base references found in `build.gradle` or any Java source file.
- **Gap**: No vector database for semantic search or embeddings storage. Required for RAG-based agent workflows.
- **Recommendation**: Provision Amazon OpenSearch Service with the k-NN plugin or enable pgvector extension on Aurora PostgreSQL. Alternatively, use Amazon Bedrock Knowledge Bases for managed vector storage.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists to evaluate management status.
- **Gap**: No vector DB present, therefore no management strategy.
- **Recommendation**: When implementing a vector database (DATA-Q1), choose a fully managed option (Amazon OpenSearch Serverless, Aurora pgvector, or Bedrock Knowledge Bases) to minimize operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG (Retrieval-Augmented Generation) implementation found. No embedding model calls, no document chunking or splitting code, no similarity search patterns. No Amazon Bedrock, Titan Embeddings, or OpenAI embeddings imports.
- **Gap**: No RAG pipeline for agent knowledge retrieval. Product descriptions in the `unicorns` table could benefit from semantic search.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases. Index product catalog data (unicorn names, descriptions) and user documentation for agent-assisted product search.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database (`unishop` schema) with 3 tables (`unicorns`, `unicorns_basket`, `unicorn_user`). All data access flows through one JDBC connection defined in `application.properties`. No additional API clients, Redis caches, or external data sources detected.
- **Gap**: None — single data source is simple and manageable.
- **Recommendation**: Maintain this simplicity as the application evolves. If additional data sources are added, create a unified data access layer.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: MyBatis mapper pattern provides structured data access: Controllers → Services → Repositories → MyBatis Mappers → MySQL. The repository layer (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`) wraps mapper calls cleanly. However, business logic directly accesses the database via JDBC/MyBatis — not via well-defined APIs. The `getUnicornBasket` query in `UnicornMapper.xml` performs a direct JOIN across tables.
- **Gap**: Data access is structured but tightly coupled to the database. No API-based data access layer that could be exposed to agents.
- **Recommendation**: Expose data access through REST APIs rather than direct database queries. This creates a natural boundary for agent tool integration — agents call APIs, not databases.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage or document parsing detected. `build.gradle` includes `aws-java-sdk-s3:1.11.567` as a dependency, but no S3 client usage was found in any Java source file. No Textract, Tika, or document parsing libraries. Product images are stored as string references (`image` column in `unicorns` table), not actual files.
- **Gap**: No unstructured data processing capability. S3 SDK is imported but unused.
- **Recommendation**: If product images or documents need processing, implement an S3-based pipeline with Amazon Textract or Rekognition. Remove the unused S3 SDK dependency to reduce the attack surface.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `database/create_tables.sql` provides the initial schema definition with 3 table structures and seed data. MyBatis mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) document the SQL queries and result mappings. However, there is no formal schema versioning — no Flyway, Liquibase, or Alembic migrations. No JSON Schema, Avro, or Protobuf definitions.
- **Gap**: Schema is documented in SQL files but not versioned or managed through migration tools. Schema changes are tracked manually.
- **Recommendation**: Introduce Flyway or Liquibase for database schema migration management. Create versioned migration scripts for all future schema changes. Document the data model in a schema registry.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: MyBatis with the repository pattern provides a centralized, well-organized data access layer. The architecture follows: Repository interface (`UnicornRepository.java`) → Implementation (`UnicornRepositoryImpl.java`) → Mapper interface (`UnicornMapper.java`) → Mapper XML (`UnicornMapper.xml`). This separation of concerns makes the data access layer modular and testable.
- **Gap**: While well-structured, the data access layer is internal to the monolith. No external API layer abstracts database access for external consumers or agents.
- **Recommendation**: Leverage the existing repository interfaces as the foundation for microservice API boundaries. Each repository interface could become a microservice API contract.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings or vector indexing exists. No event-driven embedding refresh triggers, no scheduled re-indexing pipelines, no CDC (Change Data Capture) patterns detected.
- **Gap**: No embedding infrastructure to evaluate freshness.
- **Recommendation**: When implementing RAG (DATA-Q3), design event-driven embedding updates triggered by product catalog changes. Use DynamoDB Streams or RDS event notifications to trigger re-indexing.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` specifies `mysql:mysql-connector-java:8.0.11` (released April 2018). No IaC exists to pin the MySQL server engine version. MySQL 8.0.11 connector is outdated — the current MySQL 8.0.x connector is 8.0.33+. Without IaC, the actual MySQL server version running in production is unknown and unmanaged.
- **Gap**: MySQL connector is outdated (2018). MySQL server engine version is not pinned in IaC. No evidence of version management or EOL tracking.
- **Recommendation**: Update the MySQL connector to the latest 8.0.x or 8.4.x version. Define the database engine version explicitly in IaC (Terraform/CDK) when creating the RDS instance. Establish a process for tracking database engine EOL dates.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 3/4 🟡
- **Finding**: `database/create_tables.sql` contains only `CREATE TABLE` and `INSERT` statements — no stored procedures, triggers, or functions. MyBatis mapper XMLs use standard SQL: `SELECT`, `INSERT`, `DELETE`, `JOIN`. The only MySQL-specific construct is `INSERT IGNORE` (used in `UnicornMapper.xml` and `UserMapper.xml`), which is a minor portability concern. `ENGINE=InnoDB` is MySQL-specific but functionally equivalent across managed MySQL services.
- **Gap**: Minor MySQL-specific constructs (`INSERT IGNORE`, `ENGINE=InnoDB`) that would need adjustment for a non-MySQL migration. No stored procedures or triggers blocking migration.
- **Recommendation**: Replace `INSERT IGNORE` with standard `INSERT ... ON CONFLICT` (if migrating to PostgreSQL) or retain as-is for Aurora MySQL. The clean schema makes database migration straightforward.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: `application.properties` contains hardcoded database credentials in plaintext: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. The database endpoint uses an environment variable `${MONO_TO_MICRO_DB_ENDPOINT}`, but the username and password are static strings committed to source control. No AWS Secrets Manager, HashiCorp Vault, or SSM Parameter Store integration found.
- **Gap**: Credentials are hardcoded in plaintext and committed to version control. This is the most critical security vulnerability in the codebase.
- **Recommendation**: Immediately migrate credentials to AWS Secrets Manager. Update `application.properties` to retrieve secrets at runtime using Spring Cloud AWS Secrets Manager or the AWS SDK. Rotate the exposed credentials.

#### SEC-Q2: IAM Least Privilege
- **Score**: 1/4 ❌
- **Finding**: No IAM policies are defined (no IaC exists). `build.gradle` imports the entire AWS SDK (`com.amazonaws:aws-java-sdk:1.11.567`) — a 200+ MB dependency — but only `EC2MetadataUtils` is used in `HealthController.java`. The application likely runs with an EC2 instance profile, but the IAM role and policies are not codified.
- **Gap**: IAM policies are not defined in code. The full AWS SDK import suggests potential over-permissioning. No evidence of least-privilege IAM configuration.
- **Recommendation**: Define IAM roles and policies in IaC with minimal permissions (only EC2 metadata access is currently needed). Replace the full SDK import (`aws-java-sdk`) with only the specific modules needed (`aws-java-sdk-core`).

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Spring Security OAuth2 dependencies exist in `build.gradle` (`spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`, `spring-security-jwt`). `ResourceServerConfig.java` annotates with `@EnableResourceServer`. However, `authorizeRequests().anyRequest().permitAll()` effectively disables all authorization. `Application.java` contains `CorsOptionsRequestSecurityConfigurationAdapter` that ignores all OPTIONS requests with the comment: "workaround... not recommended for production usage!" No JWT validation or token propagation is active.
- **Gap**: OAuth2/JWT framework is present but completely disabled. No user identity propagation across requests. All endpoints are publicly accessible.
- **Recommendation**: Configure the OAuth2 resource server properly with Cognito or another OIDC provider. Remove `permitAll()` and define role-based access control. Remove the insecure OPTIONS workaround.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration, no audit log setup. Logging throughout the application uses `System.out.println()` in `HealthController.java` and `e.printStackTrace()` in all repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`). No structured audit trail for business operations.
- **Gap**: No audit logging. Operations like user creation and basket modifications leave no audit trail. Stack traces go to stdout with no structure.
- **Recommendation**: Implement structured audit logging using SLF4J + Logback with JSON format. Log all business operations (user creation, basket changes) with who, what, when. Enable CloudTrail for AWS API audit logging.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. No API Gateway with throttle settings, no WAF rate rules, no application-level rate limiting middleware. `ResourceServerConfig.java` permits all requests without limits.
- **Gap**: No rate limiting. The application is vulnerable to abuse, DoS, and runaway agent loops.
- **Recommendation**: Deploy API Gateway with per-client usage plans and throttle settings. Add WAF rate-based rules. Implement application-level rate limiting with Bucket4j for defense in depth.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: The `User.java` model contains PII fields: `email`, `firstName`, `lastName`. These fields are serialized in full via `@JsonInclude(JsonInclude.Include.NON_NULL)` and returned in API responses (`UserController.java` returns `ResponseEntity<User>`). `e.printStackTrace()` in repository implementations could expose PII in log output. No PII masking, log scrubbing, or Amazon Macie integration detected.
- **Gap**: PII is returned unfiltered in API responses and potentially logged via stack traces. No PII detection or redaction.
- **Recommendation**: Implement response DTOs that exclude sensitive PII fields from API responses. Add log scrubbing middleware to mask PII. Consider Amazon Macie for S3-stored data if unstructured data is added.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows detected. No Step Functions with human approval tasks (`waitForTaskToken`), no approval API endpoints, no manual approval stages in deployment. User creation and basket operations execute immediately without any approval gate.
- **Gap**: No human-in-the-loop approval for any operation. Critical for agentic systems where agents must escalate high-risk actions (e.g., bulk modifications, refunds) to humans.
- **Recommendation**: Implement Step Functions-based approval workflows for high-risk agent actions. Start with a simple approval pattern: agent proposes action → SNS notification to human → human approves/rejects → agent proceeds.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS key configuration found (no IaC exists). No encryption settings for any data store. The MySQL database encryption status is unknown — no IaC defines RDS encryption or EC2 EBS encryption. No S3 bucket encryption settings.
- **Gap**: Encryption at rest status is unknown and unmanaged. Cannot verify that customer data (users, baskets) is encrypted.
- **Recommendation**: Define all data stores in IaC with encryption enabled. Use customer-managed KMS keys for RDS, EBS, and any S3 buckets. Ensure `StorageEncrypted: true` on RDS instances.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: Spring Security OAuth2 framework is present but completely disabled. `ResourceServerConfig.java` calls `authorizeRequests().anyRequest().permitAll()`. Every controller method uses `@PreAuthorize("permitAll()")`. The `/user/login` endpoint in `UserController.java` accepts a `User` object with email and returns user details — this is a lookup, not authentication. No actual credential validation, password hashing (`spring-security-crypto:5.1.2` is imported but unused), or token issuance.
- **Gap**: Zero authentication enforcement. All API endpoints are publicly accessible. The "login" endpoint is a database lookup, not an authentication mechanism.
- **Recommendation**: Implement proper authentication using Amazon Cognito as the identity provider. Configure the Spring Security OAuth2 resource server to validate JWT tokens from Cognito. Remove `permitAll()` and enforce authentication on all non-health endpoints.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: OAuth2 dependencies in `build.gradle` suggest intended integration with an identity provider, but no provider is configured. `application.properties` contains no OIDC issuer URL, Cognito pool ID, or OAuth2 client configuration. The `unicorn_user` table stores users directly in the application database rather than delegating to an external identity provider.
- **Gap**: No centralized identity provider. User management is handled directly in the application database without authentication, SSO, or federation.
- **Recommendation**: Deploy Amazon Cognito User Pool as the centralized identity provider. Migrate user records from `unicorn_user` table to Cognito. Configure OIDC federation for SSO. Update the Spring Security OAuth2 configuration to validate Cognito-issued tokens.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, Datadog, Jaeger, or any tracing library in `build.gradle`. No trace ID propagation in HTTP headers. Spring Boot Actuator (`spring-boot-starter-actuator`) is included but provides only health and metrics endpoints — no tracing configuration. No `gen_ai.*` semantic conventions for LLM spans.
- **Gap**: No distributed tracing. Request flows through the monolith cannot be traced end-to-end. When microservices are introduced, cross-service tracing will be essential.
- **Recommendation**: Add AWS X-Ray SDK or OpenTelemetry Java agent to `build.gradle`. Configure automatic instrumentation for Spring Boot, HTTP clients, and JDBC. Propagate trace IDs in all outbound requests.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: No structured logging framework. `HealthController.java` uses `System.out.println()` for instance info output. All repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) use `e.printStackTrace()` for error handling. No JSON log formatter (Logback JSON, Log4j2 JSON Layout). No correlation IDs or trace context in log output.
- **Gap**: Unstructured plain-text logging with no correlation IDs. Logs cannot be effectively queried, filtered, or correlated across requests.
- **Recommendation**: Replace `System.out.println()` and `e.printStackTrace()` with SLF4J logger calls. Configure Logback with JSON layout. Add a correlation ID filter that generates/propagates request IDs across all log entries.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework detected. No eval datasets, scoring scripts, LLM-as-judge patterns, golden dataset files, or A/B test infrastructure. No AI components exist in the application to evaluate.
- **Gap**: No eval infrastructure. When AI/agent capabilities are added, an evaluation framework will be needed to measure quality, accuracy, and safety.
- **Recommendation**: When implementing agent features, establish an automated eval pipeline with golden datasets. Use Amazon Bedrock's evaluation capabilities or RAGAS framework for RAG pipeline evaluation.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms, no p99/p95 latency targets, no error budget tracking. Spring Boot Actuator provides basic health endpoints (`/health`) but no SLO monitoring. No dashboard configurations.
- **Gap**: No SLOs defined. Reliability targets are not formalized, making it impossible to measure service quality or agent performance.
- **Recommendation**: Define SLOs for critical user journeys: product listing latency (p99 < 500ms), basket operations (p99 < 1s), user login (p99 < 500ms). Create CloudWatch alarms and dashboards.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment pipeline exists, therefore no rollback capability. No blue/green, canary, or rolling deployments. No CodeDeploy rollback triggers, no Helm rollback, no feature flags. The `bootJar` with `launchScript()` suggests manual JAR replacement on EC2.
- **Gap**: No rollback capability. Failed deployments require manual intervention to restore the previous version.
- **Recommendation**: Implement blue/green or canary deployments via CodeDeploy or ECS rolling updates. Store deployment artifacts in S3/ECR for quick rollback. Add feature flags (LaunchDarkly, AWS AppConfig) for agent feature rollback.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application, therefore no cost tracking. No token counting, cost attribution, or usage metrics.
- **Gap**: No LLM cost tracking infrastructure. When agent capabilities are added, token usage and cost attribution will be essential.
- **Recommendation**: When integrating LLMs via Amazon Bedrock, implement per-request token counting and cost attribution. Publish custom CloudWatch metrics for token usage by endpoint/user/workflow. Establish observability data retention policies.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics published. No `cloudwatch.put_metric_data`, no custom dashboards for business KPIs (e.g., orders placed, basket conversion rate, user registration rate). Spring Boot Actuator provides only infrastructure-level metrics (JVM, HTTP request counts).
- **Gap**: No business outcome tracking. Cannot measure business impact of changes or agent actions.
- **Recommendation**: Publish custom CloudWatch metrics for business events: products viewed, basket additions/removals, user registrations, login attempts. Create business KPI dashboards.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection, no alerting on error rates or latency. No CloudWatch anomaly detection, no composite alarms, no PagerDuty/OpsGenie integration. No behavioral baseline monitoring.
- **Gap**: No anomaly detection. Silent degradation (database slowdowns, increased error rates) would go unnoticed.
- **Recommendation**: Enable CloudWatch anomaly detection on key metrics (HTTP 5xx rate, database latency, response time p99). Create composite alarms for critical paths. Integrate with PagerDuty or OpsGenie for incident notification.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy defined in the codebase. No CodeDeploy, Helm canary, Argo Rollouts, Lambda traffic shifting, or ALB weighted target groups. The `build.gradle` `bootJar` with `launchScript()` produces a self-executing JAR, suggesting direct deployment to EC2 via SSH or manual copy.
- **Gap**: No defined deployment strategy. Deployments are presumably manual and uncontrolled.
- **Recommendation**: Implement blue/green deployments using AWS CodeDeploy (for EC2) or ECS rolling updates (after containerization). For agent prompt deployments, implement canary rollouts with automated rollback on error rate increase.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found in the repository. No `src/test/` directory, no integration tests, no unit tests, no contract tests. `build.gradle` declares `testImplementation('org.springframework.boot:spring-boot-starter-test')` but no test code exists.
- **Gap**: Zero test coverage. No automated verification of functionality. Changes cannot be validated before deployment.
- **Recommendation**: Create `src/test/java/` directory. Write unit tests for service implementations and integration tests for API endpoints using Spring Boot Test. Add test execution to the CI pipeline. Target 80% code coverage for critical business logic.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, SSM Automation documents, Lambda-based remediation, or self-healing patterns found. No markdown or YAML runbooks in the repository. No links to runbooks in any configuration. No auto-restart or auto-scaling on failure events.
- **Gap**: No incident response automation. Manual response to all incidents, including potential agent failures.
- **Recommendation**: Create machine-readable runbooks (YAML/Markdown) for common failure scenarios: database connection failures, high latency, deployment rollback. Implement SSM Automation documents for common remediation actions.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No `CODEOWNERS` file, no SLO ownership definitions, no observability stack configuration, no team ownership files. No evidence of platform engineering or shared responsibility model for observability.
- **Gap**: No observability governance. No defined ownership of service reliability or agent quality.
- **Recommendation**: Create a `CODEOWNERS` file. Define service-level ownership with on-call rotations. Establish SLO-driven culture with named owners for each critical journey. When agents are introduced, assign ownership of agent-level SLOs (task success rate, tool error rate).

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 2/4, INF-Q1: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Triggered | Medium | High | INF-Q1: 1/4, No Dockerfile found | High |
| Move to Open Source | Not Triggered | Medium | — | — | — |
| Move to Managed Databases | Triggered | Medium | High | INF-Q2: 1/4, DATA-Q10: 1/4 | Medium |
| Move to Managed Analytics | Not Triggered | Medium | — | — | — |
| Move to Modern DevOps | Triggered | Medium | High | INF-Q5: 1/4, INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Medium | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Containers + Move to Modern DevOps + Move to Managed Databases — These three pathways can execute concurrently. Containerizing the app, setting up CI/CD, and migrating to managed RDS are independent activities.

**Parallel Track 2**: Move to AI — Can begin in parallel with Track 1 for API documentation and vector DB setup, but agent framework integration depends on stable APIs (Track 1 completion).

**Sequential Dependencies**: Move to Containers must complete before Move to Cloud Native (cannot decompose into microservices without container infrastructure). Move to Modern DevOps (CI/CD) should be established early as it enables all other pathways.

### Move to Containers

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q1: Score 1/4 — Application runs on raw EC2 (`HealthController.java` uses `EC2MetadataUtils.getInstanceInfo()`)
  - No Dockerfile found — `build.gradle` has a commented-out `docker` task but no actual Dockerfile exists
- **Current State**: Spring Boot JAR deployed directly to EC2 via `bootJar` with `launchScript()`. No container definitions.
- **Target State**: Application containerized with multi-stage Dockerfile, deployed to ECS Fargate or EKS with health checks, auto-scaling, and rolling updates.
- **Key Activities**:
  1. Create a multi-stage Dockerfile for the Spring Boot application
  2. Set up Amazon ECR repository for container images
  3. Deploy to ECS Fargate or EKS with task definitions and service configuration
  4. Configure health check targets using existing `/health/ishealthy` endpoint
  5. Set up ECS Service auto-scaling based on CPU/memory metrics
- **Dependencies**: None — this is the foundational pathway
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for Dockerfile creation, Phase 2 (Foundation) for ECS/EKS deployment
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 2/4 — Monolith with identifiable modules (Unicorn, User, Basket) but database-level coupling via JOINs in `UnicornMapper.xml`
  - INF-Q1: Score 1/4 — EC2-based compute
  - APP-Q3: Score 1/4 — 100% synchronous communication
  - APP-Q10: Score 1/4 — No async infrastructure for long-running operations
- **Current State**: Single deployable Spring Boot monolith with all domains (product catalog, user management, basket) in one application. Database coupling via cross-table JOINs.
- **Target State**: Modular architecture with clear service boundaries. Async communication between domains. Independent scaling per domain.
- **Key Activities**:
  1. Conduct domain modeling to identify bounded contexts (Unicorn Products, User Management, Basket/Cart)
  2. Extract Basket service first (highest business value, clearest boundary)
  3. Replace `UnicornMapper.xml` JOIN queries with API calls between services
  4. Introduce Amazon SQS/EventBridge for async communication between extracted services
  5. Implement API Gateway routing between monolith and extracted services (Strangler Fig pattern)
- **Dependencies**: Move to Containers must complete first
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Foundation) for first service extraction, Phase 3 (Advanced Capabilities) for continued decomposition
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Managed Databases

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q2: Score 1/4 — MySQL database with no IaC confirming managed status. Connection via direct JDBC in `application.properties`
  - DATA-Q10: Score 1/4 — MySQL connector version 8.0.11 (2018) is outdated. No engine version pinning in IaC
- **Current State**: MySQL database accessed via JDBC connection string with hardcoded credentials. No IaC manages the database. MySQL connector is outdated (8.0.11, released 2018).
- **Target State**: Amazon RDS for MySQL or Aurora MySQL defined in IaC with Multi-AZ, automated backups, encryption at rest, and current engine version.
- **Key Activities**:
  1. Define the MySQL database in Terraform/CDK as Amazon RDS for MySQL or Aurora MySQL
  2. Enable Multi-AZ, automated backups, and encryption at rest with KMS
  3. Pin the engine version to a current, supported MySQL 8.0.x or 8.4.x release
  4. Update `build.gradle` MySQL connector from 8.0.11 to current version
  5. Migrate credentials from `application.properties` to AWS Secrets Manager
  6. Use AWS DMS if migrating from a self-managed MySQL instance
- **Dependencies**: None — can execute in parallel with other pathways
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for connector update and IaC, Phase 2 (Foundation) for Aurora migration
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q5: Score 1/4 — Zero IaC files in the repository
  - INF-Q6: Score 1/4 — No CI/CD pipeline defined
  - OPS-Q9: Score 1/4 — No deployment strategy (manual JAR deployment)
  - OPS-Q10: Score 1/4 — No test files exist despite test framework dependency
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: No IaC, no CI/CD, no tests, no observability, no deployment strategy. Everything is manual.
- **Target State**: Full IaC coverage, automated CI/CD pipeline with test/build/deploy stages, distributed tracing, structured logging, and blue/green deployments.
- **Key Activities**:
  1. Create Terraform/CDK project for all infrastructure (VPC, ECS/EKS, RDS, ALB)
  2. Set up CI/CD pipeline (CodePipeline + CodeBuild or GitHub Actions)
  3. Write unit and integration tests for existing business logic
  4. Add AWS X-Ray or OpenTelemetry for distributed tracing
  5. Replace `System.out.println()` and `e.printStackTrace()` with structured JSON logging
  6. Implement blue/green deployments via CodeDeploy or ECS rolling updates
- **Dependencies**: None — this is a foundational pathway that enables all others
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for IaC and CI/CD, Phase 2 (Foundation) for observability and testing
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in `build.gradle`
  - DATA-Q1: Score 1/4 — No vector database
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated eval framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: Zero AI/agent capabilities. No vector database, no RAG pipeline, no LLM integration, no eval framework. AWS SDK v1 is present but unused for AI services.
- **Target State**: Agent-compatible API layer with OpenAPI specs, Amazon Bedrock integration for LLM capabilities, vector database for RAG, automated eval pipeline, and LLM cost tracking.
- **Key Activities**:
  1. Add OpenAPI documentation to existing APIs (prerequisite for agent tool discovery)
  2. Provision Amazon OpenSearch Service or Aurora pgvector for vector storage
  3. Implement RAG pipeline for product catalog semantic search using Bedrock Knowledge Bases
  4. Add Spring AI or LangChain4j for agent framework integration
  5. Create agent-compatible tool endpoints wrapping existing business logic
  6. Implement automated eval pipeline with golden datasets
  7. Add per-request LLM token tracking and cost attribution
- **Dependencies**: Move to Modern DevOps (CI/CD needed to safely deploy AI features); Move to Managed Databases (stable data layer needed)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Foundation) for vector DB and API docs, Phase 3 (Advanced Capabilities) for agent integration
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure (containerize, set up CI/CD, migrate to managed DB) while incrementally extracting services
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract the Basket/Cart service first — it has a clear domain boundary (`BasketController.java`, `unicorns_basket` table), relatively low coupling (the JOIN in `UnicornMapper.xml` can be replaced with an API call to the Product service), and high business value (cart is a critical user journey)
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently. Containerize the monolith as-is first, then extract services opportunistically based on business need
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Containerize the entire monolith as a single ECS service. Then extract User service (simplest, least coupling — `UserController.java` + `UserServiceImpl.java` + `UserRepositoryImpl.java` with no cross-domain JOINs in `UserMapper.xml`)
- **When to Use**: When immediate containerization delivers business value and decomposition can be deferred

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

**Pattern Recommendations Based on Your Architecture:**

- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (hostname, path, or header-based). The existing REST endpoints (`/unicorns`, `/user`, `/unicorns/basket`) map naturally to path-based routing in API Gateway, allowing incremental extraction behind a single gateway without changing client URLs.

- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extraction. Without idempotency (APP-Q7 scored 1/4), extracting the Basket service risks data inconsistency. The JOIN between `unicorns` and `unicorns_basket` tables must be replaced with eventual consistency via API calls and an outbox pattern.

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition. The current `try-catch` with `e.printStackTrace()` pattern in all repositories will not survive service extraction. Add Resilience4j circuit breakers around all external calls before introducing network boundaries between services.

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **JSON API Agent Tool Integration** — Your existing REST APIs already return structured JSON responses (`@JsonInclude(JsonInclude.Include.NON_NULL)` on `Unicorn.java` and `User.java`). An agent can invoke these endpoints directly as tools with minimal parsing effort.
   - **Leverages**: Structured JSON responses from all controllers (`ResponseEntity<Collection<Unicorn>>`, `ResponseEntity<User>`, `ResponseEntity<UnicornBasket>`)
   - **Effort**: Low
   - **Value**: Enables an agent to browse products, manage baskets, and look up users via existing API surface

2. **Natural Language Product Search Agent** — The `unicorns` table has a clear schema with `name`, `description`, and `price` columns documented in `database/create_tables.sql`. An agent can translate natural language queries to SQL against this well-defined schema.
   - **Leverages**: Clean database schema documented in `database/create_tables.sql` with 3 well-defined tables
   - **Effort**: Medium
   - **Value**: Enables customers to search for products using natural language (e.g., "show me unicorn backpacks under $100") instead of browsing the catalog

3. **Documentation Knowledge Agent** — The repository includes `database/create_tables.sql` (schema documentation), MyBatis mapper XMLs (query documentation), and service interfaces that document the API contracts. This documentation can be indexed for a RAG-based knowledge agent.
   - **Leverages**: Schema definitions in `database/create_tables.sql`, query documentation in `UnicornMapper.xml`, `UserMapper.xml`, and `HealthMapper.xml`
   - **Effort**: Medium
   - **Value**: Enables developers and support staff to query the application's data model and API behavior using natural language

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Quick Wins (Days 1–30)

1. **Migrate secrets to AWS Secrets Manager** — Move `MonoToMicroUser`/`MonoToMicroPassword` from `application.properties` to Secrets Manager. Update application to retrieve credentials at runtime. Rotate exposed credentials immediately.
2. **Create a Dockerfile** — Write a multi-stage Dockerfile for the Spring Boot application. Test locally with `docker build` and `docker run`. This is the foundation for containerized deployment.
3. **Set up CI/CD pipeline** — Create a GitHub Actions workflow or AWS CodeBuild project that builds the Gradle project, runs (future) tests, and produces a Docker image. Push to Amazon ECR.
4. **Initialize IaC** — Create a Terraform or CDK project with VPC, subnets, security groups, and an RDS MySQL instance matching the current deployment topology.
5. **Add OpenAPI documentation** — Add `springdoc-openapi-ui` to `build.gradle` to auto-generate OpenAPI specs. This enables agent tool discovery immediately.
6. **Conduct EventStorming or domain modeling workshop** — Identify bounded contexts (Product Catalog, User Management, Basket/Cart) and map current module dependencies and data coupling.
7. **Map current module dependencies** — Document the `UnicornMapper.xml` JOIN between `unicorns` and `unicorns_basket` tables. Identify first candidate service for extraction (Basket service).

### Phase 2 — Foundation (Months 1–3)

1. **Deploy to ECS Fargate or EKS** — Migrate from EC2 to managed container orchestration using the Dockerfile from Phase 1. Configure health checks using `/health/ishealthy`.
2. **Migrate to Amazon RDS/Aurora MySQL** — Define database in IaC as RDS for MySQL or Aurora MySQL with Multi-AZ, encryption, and automated backups. Use AWS DMS for migration if needed.
3. **Implement structured logging and tracing** — Replace `System.out.println()` and `e.printStackTrace()` with SLF4J + Logback JSON. Add AWS X-Ray or OpenTelemetry for distributed tracing.
4. **Write tests** — Create unit tests for `UnicornServiceImpl`, `UserServiceImpl` and integration tests for API endpoints. Add test execution to CI pipeline.
5. **Enable authentication** — Configure Amazon Cognito as identity provider. Update `ResourceServerConfig.java` to validate JWT tokens. Remove `permitAll()`.
6. **Provision vector database** — Deploy Amazon OpenSearch Service with k-NN plugin or Aurora with pgvector for future RAG implementation.
7. **Extract first service (Strangler Fig)** — Extract the Basket service using API Gateway path-based routing. Replace the JOIN in `UnicornMapper.xml` with an API call to the Product service. Implement anti-corruption layer at the boundary.
8. **Add resilience patterns** — Add Resilience4j with circuit breakers, retry with backoff, and timeouts for all external dependency calls.

### Phase 3 — Advanced Capabilities (Months 3–6)

1. **Implement RAG pipeline** — Index product catalog data using Amazon Bedrock Knowledge Bases. Enable semantic product search via natural language queries.
2. **Add agent framework** — Integrate Spring AI or LangChain4j. Create agent-compatible tool endpoints wrapping business logic (product search, basket management, user lookup).
3. **Implement automated eval pipeline** — Create golden datasets for agent evaluation. Set up automated scoring for agent task success rate, response quality, and tool usage accuracy.
4. **Add LLM cost tracking** — Implement per-request token counting and cost attribution. Publish CloudWatch custom metrics for LLM usage by endpoint/user/workflow.
5. **Define and monitor SLOs** — Create SLOs for all critical user journeys and agent-level metrics (task success rate, hallucination rate, tool error rate). Set up CloudWatch dashboards and alarms.
6. **Implement human-in-the-loop approvals** — Build Step Functions workflows for high-risk agent actions with human approval gates (e.g., bulk data modifications, refunds).
7. **Continue service extraction** — Extract User service. Implement service discovery via AWS Cloud Map. Add domain-specific agent tools per service boundary.
8. **Enable anomaly detection** — Configure CloudWatch anomaly detection on error rates, latency, and agent behavioral metrics. Integrate with PagerDuty/OpsGenie for incident notification.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless)**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- EKS Workshop — https://www.eksworkshop.com/

**Module 4: Move to Managed Databases**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 6: Move to Modern DevOps**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 7: Move to AI**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `build.gradle` | Spring Boot 2.1.x, Java 8, MySQL connector 8.0.11, AWS SDK v1 1.11.567, Spring Security OAuth2, MyBatis, commented-out Docker task, `bootJar` with `launchScript()` |
| 2 | `src/main/resources/application.properties` | Hardcoded credentials (`MonoToMicroUser`/`MonoToMicroPassword`), JDBC MySQL connection string, port 8080 |
| 3 | `database/create_tables.sql` | MySQL schema with 3 tables (`unicorns`, `unicorns_basket`, `unicorn_user`), `ENGINE=InnoDB`, seed data, no stored procedures |
| 4 | `src/main/java/com/monoToMicro/Application.java` | `@SpringBootApplication` entry point, insecure CORS OPTIONS workaround |
| 5 | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | `@EnableResourceServer` with `permitAll()` — OAuth2 framework present but disabled |
| 6 | `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | `@PreAuthorize("permitAll()")`, `ResponseEntity<Collection<Unicorn>>`, GET `/unicorns` |
| 7 | `src/main/java/com/monoToMicro/rest/controller/UserController.java` | POST `/user` (create), POST `/user/login` (lookup by email), no authentication |
| 8 | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | POST/DELETE/GET `/unicorns/basket`, cart management endpoints |
| 9 | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | `EC2MetadataUtils.getInstanceInfo()` confirming EC2 deployment, `System.out.println()` |
| 10 | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | GET `/data`, returns `null` on failure, synchronous replication endpoint |
| 11 | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | Service interface pattern, delegates to repository, synchronous CRUD |
| 12 | `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | UUID generation, user creation logic, no password hashing |
| 13 | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | `e.printStackTrace()` error handling, returns `null` on exception, `@Transactional` |
| 14 | `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | `synchronized` create method, `e.printStackTrace()`, returns `null` on failure |
| 15 | `src/main/java/com/monoToMicro/core/repository/HealthRepositoryImpl.java` | Database health check via `select count(*) from unicorns`, `e.printStackTrace()` |
| 16 | `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | `INSERT IGNORE`, JOIN between `unicorns` and `unicorns_basket` tables, `getAllBaskets` with resultMap |
| 17 | `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | `insert ignore into unicorn_user`, `getByEmail` query, MyBatis cache enabled |
| 18 | `src/main/java/com/monoToMicro/core/model/Unicorn.java` | `@JsonInclude(JsonInclude.Include.NON_NULL)`, clean JSON model |
| 19 | `src/main/java/com/monoToMicro/core/model/User.java` | PII fields (email, firstName, lastName), `@JsonInclude(JsonInclude.Include.NON_NULL)` |
| 20 | `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | MyBatis configuration with 3 mapper XMLs, DataSource wiring, SqlSessionFactory setup |
