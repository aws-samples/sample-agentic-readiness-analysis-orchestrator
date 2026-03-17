# Agentic Readiness Assessment Report
**Target**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
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

This Java Spring Boot monolith (Unishop) runs directly on EC2 instances with a self-managed MySQL database, representing significant cost optimization opportunities across compute, database, and operational overhead. The application has **zero Infrastructure as Code**, **no CI/CD pipelines**, **no containerization**, and **hardcoded database credentials** — all of which compound operational costs through manual provisioning, deployment effort, and inability to right-size resources. The strongest area is Data Foundations (2.09/4.0) due to a clean single-database architecture with standard SQL (no stored procedures or proprietary constructs), making database migration to a managed service like Aurora MySQL or Aurora PostgreSQL straightforward. The most impactful cost savings will come from migrating the self-managed MySQL to Aurora (eliminating operational overhead), containerizing the application on ECS Fargate with Graviton instances (reducing compute costs by ~20-40%), and implementing IaC to enable infrastructure right-sizing and governance.

### Overall Score: 1.31 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.0 / 4.0 | ❌ |
| Application Architecture | 1.38 / 4.0 | ❌ |
| Data Foundations | 2.09 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.1 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

The following 5 gaps are prioritized for maximum cost-reduction impact, weighted toward cost-optimization priority criteria (INF-Q2, DATA-Q10, INF-Q8, DATA-Q2, DATA-Q11):

### 1. INF-Q2 — Self-Managed MySQL Database (Score: 1/4) ❌
**Why it matters for cost**: Self-managed MySQL on EC2 requires ongoing patching, backup management, failover configuration, and capacity planning — all manual operational overhead that directly translates to engineering time and cost. No automated failover means downtime risk equals revenue loss.
**First step**: Evaluate Aurora MySQL or Aurora PostgreSQL as migration target. Use AWS Database Migration Service (DMS) to plan a zero-downtime migration. The schema (3 simple tables, no stored procedures) is fully compatible with Aurora.

### 2. INF-Q1 — Raw EC2 Compute (Score: 1/4) ❌
**Why it matters for cost**: Running on EC2 requires manual capacity management and prevents auto-scaling. Instances likely run 24/7 at fixed capacity even during low-traffic periods, resulting in wasted compute spend. No containerization blocks adoption of Graviton-based Fargate, which offers ~20% price-performance improvement.
**First step**: Create a Dockerfile for the Spring Boot application (bootJar already produces a self-contained JAR). Deploy to ECS Fargate with Graviton (ARM64) task definitions for immediate cost savings.

### 3. INF-Q5 — No Infrastructure as Code (Score: 1/4) ❌
**Why it matters for cost**: Without IaC, infrastructure cannot be version-controlled, audited, or cost-tagged. There is no way to enforce cost governance policies, implement resource tagging for cost allocation, or replicate environments consistently. Manual provisioning leads to resource sprawl and abandoned resources.
**First step**: Define the application's infrastructure in AWS CDK or CloudFormation, starting with compute (ECS) and database (Aurora). Implement mandatory cost allocation tags from day one.

### 4. INF-Q6 — No CI/CD Pipeline (Score: 1/4) ❌
**Why it matters for cost**: Manual deployments consume engineer time on repetitive tasks and introduce deployment failures that cause costly rollbacks. Without automated testing gates, bugs reach production more frequently, increasing incident response costs.
**First step**: Create a GitHub Actions workflow or AWS CodePipeline with stages for build (Gradle), test, container image push (ECR), and deploy (ECS).

### 5. DATA-Q10 — Unpinned Database Engine Version (Score: 2/4) 🟠
**Why it matters for cost**: The MySQL connector version 8.0.11 (from 2018) suggests the MySQL server may be running an older version. Older engine versions miss performance improvements available in newer releases and may approach end-of-life, requiring emergency migration efforts that are more expensive than planned upgrades.
**First step**: Pin the database engine version in IaC when migrating to Aurora. Target the latest Aurora MySQL 8.0-compatible version to benefit from performance and cost optimizations.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: The application runs directly on EC2 instances. `HealthController.java` uses `EC2MetadataUtils.getInstanceInfo()` to retrieve accountId, availability zone, instanceId, instanceType, and region — confirming raw EC2 deployment. No ECS, EKS, Lambda, or Fargate resources found. No Dockerfile exists (a Docker build configuration is commented out in `build.gradle`). `bootJar` with `launchScript()` produces a self-executing JAR deployed directly to EC2.
- **Gap**: No managed container orchestration or serverless compute. The application is deployed as a self-executing JAR on bare EC2 instances with no container abstraction.
- **Recommendation**: Containerize the application by creating a Dockerfile based on the existing `bootJar` output. Deploy on ECS Fargate with Graviton (ARM64) instances for ~20% cost savings. The commented-out Docker configuration in `build.gradle` shows this was previously considered.

#### INF-Q2: Databases
- **Score**: 1/4 ❌
- **Finding**: `application.properties` defines a direct JDBC connection to MySQL: `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The MySQL connector `mysql-connector-java:8.0.11` is specified in `build.gradle`. No IaC exists defining RDS, Aurora, or DynamoDB resources. The database endpoint is configured via environment variable (`MONO_TO_MICRO_DB_ENDPOINT`), suggesting a self-managed MySQL instance. `database/create_tables.sql` defines the schema with MySQL-specific `ENGINE=InnoDB` and `DEFAULT CHARSET=UTF8MB4`.
- **Gap**: Self-managed MySQL database with no managed service definition, no automated backups, no automated failover, and no multi-AZ configuration evident.
- **Recommendation**: Migrate to Aurora MySQL (wire-compatible, minimal application changes) or Aurora PostgreSQL (better long-term cost-performance). Use AWS DMS for migration. The simple schema (3 tables, standard SQL, InnoDB engine) makes this migration low-risk. Prefer Aurora MySQL initially for zero application code changes, or Aurora PostgreSQL for better price-performance at scale.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow engine detected. All business logic follows synchronous request-response patterns in controllers (`UnicornController.java`, `BasketController.java`, `UserController.java`). The event classes under `core/events/` are simple DTOs, not event-driven workflow patterns.
- **Gap**: No dedicated workflow orchestration service. All operations are simple CRUD — no complex business workflows requiring orchestration are evident.
- **Recommendation**: Not a priority for cost optimization. If multi-step workflows are added in the future, implement AWS Step Functions to avoid custom state machine maintenance costs.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, Kafka, or RabbitMQ dependencies or code patterns found. `build.gradle` includes `aws-java-sdk` but no messaging SDK is used in any source file. All inter-component communication is synchronous method calls within the monolith.
- **Gap**: No asynchronous messaging infrastructure. All operations are synchronous.
- **Recommendation**: Not a priority for cost optimization. If the application scales and async processing is needed (e.g., order processing, notifications), adopt SQS or EventBridge rather than self-managing messaging infrastructure.

#### INF-Q5: Infrastructure as Code
- **Score**: 1/4 ❌
- **Finding**: No `.tf`, CDK, CloudFormation, Helm, or Kustomize files found anywhere in the repository. Infrastructure appears to be entirely manually provisioned. The only infrastructure-relevant configuration is `application.properties` with a database endpoint variable.
- **Gap**: Zero IaC coverage. All infrastructure is manually provisioned, making it impossible to track costs by resource, enforce tagging policies, or replicate environments.
- **Recommendation**: Implement IaC using AWS CDK or CloudFormation covering all infrastructure: VPC, subnets, ECS cluster, Aurora database, security groups, and IAM roles. Include mandatory cost allocation tags (team, environment, application) on all resources.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No `.github/workflows/`, `buildspec.yml`, `Jenkinsfile`, or `.gitlab-ci.yml` found. No pipeline definitions in IaC (no IaC exists). The application builds with Gradle (`gradlew`) but deployment appears entirely manual.
- **Gap**: No automated build, test, or deployment pipeline. Manual deployments increase operational costs and deployment failure rates.
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions, CodePipeline, or GitLab CI) with stages: Gradle build → run tests → build Docker image → push to ECR → deploy to ECS. This reduces deployment time and enables automated rollbacks.

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: No API Gateway, ALB, or CloudFront configuration found. The Spring Boot application exposes port 8080 directly (`server.port=8080` in `application.properties`). `ResourceServerConfig.java` permits all requests with no throttling. `MVCConfig.java` enables CORS for all origins and methods.
- **Gap**: No managed API entry point with throttling, caching, or authentication. Direct service exposure on port 8080.
- **Recommendation**: Place an Application Load Balancer in front of ECS tasks when containerizing. For API management features (throttling, caching, auth), add API Gateway. ALB alone provides health checking and load distribution at low cost.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or streaming SDK usage found. No real-time streaming requirements are evident in the application — it is a simple CRUD e-commerce store.
- **Gap**: No streaming infrastructure. However, the application does not have evident streaming requirements.
- **Recommendation**: Not a priority. Streaming infrastructure should only be added if real-time event processing becomes a business requirement. If needed, use Kinesis Data Streams or MSK Serverless rather than self-managed Kafka.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions found (no IaC exists). The EC2 deployment likely uses default VPC settings. `ResourceServerConfig.java` permits all requests. `MVCConfig.java` enables CORS for all origins.
- **Gap**: No evidence of network segmentation, private subnets, or least-privilege security groups. CORS is wide open.
- **Recommendation**: When implementing IaC, define a VPC with public and private subnets. Place the application in private subnets behind an ALB. Create least-privilege security groups allowing only ALB-to-ECS and ECS-to-Aurora traffic.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No ASG, ECS Service auto-scaling, or Lambda concurrency configuration found. The EC2 deployment appears to be a fixed-size instance with no scaling policies.
- **Gap**: No auto-scaling. Fixed compute capacity means over-provisioning during low traffic and under-provisioning during peaks — both are cost-inefficient.
- **Recommendation**: When migrating to ECS Fargate, configure ECS Service Auto Scaling with target tracking on CPU/memory utilization. Set minimum capacity to handle baseline traffic and maximum capacity for peaks. This eliminates over-provisioning costs.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`) with Spring Boot 2.1.6. Spring Boot 2.1.x is EOL (end of support was November 2019). Java 8 is still receiving updates but is increasingly legacy. The agent framework ecosystem for Java is moderate (Spring AI exists but requires Spring Boot 3.x+).
- **Gap**: Java 8 and Spring Boot 2.1 are both legacy versions. Spring Boot 2.1 is no longer maintained, missing security patches and performance improvements. Upgrading to Spring Boot 3.x and Java 17+ would enable access to Spring AI and modern cloud-native features.
- **Recommendation**: Plan Spring Boot upgrade path: 2.1 → 2.7 → 3.x (with Java 17+). This is a prerequisite for accessing modern Spring ecosystem features and reduces security vulnerability exposure. Spring Boot 3.x also enables GraalVM native compilation for faster cold starts on serverless.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specifications found. No `openapi.yaml`, `swagger.json`, or API documentation files. No `@OpenAPIDefinition`, `@ApiOperation`, or Springfox/SpringDoc annotations in any controller. Endpoints are discoverable only by reading source code: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`, `GET /data`.
- **Gap**: No machine-readable API documentation. API contracts are undocumented.
- **Recommendation**: Add SpringDoc OpenAPI (`springdoc-openapi-ui`) to auto-generate OpenAPI specs from controller annotations. This is low effort and enables future API Gateway integration.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous HTTP. All controller methods (`UnicornController.getUnicorns()`, `BasketController.addUnicornToBasket()`, `UserController.createUser()`) use synchronous `@RequestMapping` with blocking database calls via MyBatis. No message publishing, event-driven handlers, or async patterns found.
- **Gap**: 100% synchronous communication. No async patterns for any operations.
- **Recommendation**: Not a priority for cost optimization. As the application is a monolith, async communication would become relevant during service decomposition. If adopted, use SQS for decoupling write operations.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single deployable Spring Boot application (`bootJar` in `build.gradle`). All domains — Unicorn catalog, shopping basket, user management, health monitoring, and data replication — are in one deployment unit. Some modular structure exists: separate packages for controllers (`rest/controller/`), services (`core/services/`), repositories (`core/repository/`), and models (`core/model/`). Service interfaces exist (`UnicornService`, `UserService`, `HealthService`). However, all share the same MySQL database and deployment artifact.
- **Gap**: Monolith with identifiable modules but all coupled to a single database. The module structure provides a starting point for decomposition but shared data prevents independent deployment.
- **Recommendation**: For cost optimization, containerize the monolith as-is first. Decomposition can be considered later if specific modules would benefit from different database technologies or scaling profiles.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: Controllers return `ResponseEntity` with Java objects serialized to JSON via Jackson (included transitively through `spring-boot-starter-web`). Models use `@JsonInclude(JsonInclude.Include.NON_NULL)` annotations (`Unicorn.java`, `User.java`). `CoreModel.java` uses `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` and `@JsonIgnore` for internal fields. All API responses are structured JSON.
- **Gap**: JSON responses are well-structured, but no standardized error response format. Error responses return only HTTP status codes (`HttpStatus.BAD_REQUEST`) without error details.
- **Recommendation**: Add standardized error response DTOs with error codes and messages. This is low priority for cost optimization but improves operational debugging.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No dedicated workflow orchestration. Business logic is hardcoded in service implementations (`UnicornServiceImpl.java`, `UserServiceImpl.java`). Event classes exist (`ReadUnicornsEvent`, `WriteUnicornsBasketEvent`, etc.) but are simple DTOs used for method parameter passing, not event-driven workflow patterns. No saga, state machine, or process orchestration is present.
- **Gap**: No workflow orchestration. Business logic is simple CRUD — no complex multi-step workflows are evident.
- **Recommendation**: Not a priority. The application's CRUD operations do not require workflow orchestration. If business processes become more complex, adopt Step Functions.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: `UnicornMapper.xml` uses `INSERT IGNORE INTO unicorns_basket` for `addUnicornToBasket`, providing database-level idempotency for basket operations. `UserMapper.xml` uses `insert ignore into unicorn_user` for user creation, preventing duplicate users by email (UNIQUE constraint). However, no idempotency keys exist at the API layer — no `Idempotency-Key` headers or request deduplication tokens.
- **Gap**: Database-level idempotency via `INSERT IGNORE` but no API-level idempotency keys. Retry safety depends entirely on database constraints.
- **Recommendation**: Low priority for cost optimization. The current database-level idempotency is adequate for the simple CRUD operations. API-level idempotency keys should be added when exposing APIs to external consumers.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. `ResourceServerConfig.java` calls `.authorizeRequests().anyRequest().permitAll()` — no throttling. No API Gateway with throttle settings. No WAF rules. No rate limiting middleware in `build.gradle` dependencies.
- **Gap**: No rate limiting. All endpoints are open to unlimited requests.
- **Recommendation**: When implementing ALB/API Gateway, enable rate limiting. API Gateway provides built-in throttling with usage plans. This prevents runaway costs from abusive traffic.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retries, or timeouts configured. Repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) catch exceptions with `e.printStackTrace()` and return `null` or `false`. No Resilience4j, Hystrix, or retry decorators. No timeout configurations on database connections. `UserRepositoryImpl.create()` is `synchronized` — a naive concurrency approach.
- **Gap**: No resilience patterns. Exceptions are swallowed with `e.printStackTrace()`. No retries, timeouts, or circuit breakers for database operations.
- **Recommendation**: Add connection pool timeouts and query timeouts to `application.properties`. When migrating to Aurora, configure connection pool settings (HikariCP defaults in Spring Boot) with appropriate timeouts. Replace `e.printStackTrace()` with proper logging.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: No async job frameworks. No background processing, job queues, or polling patterns. All operations are synchronous CRUD with immediate database operations. No Celery, Bull, SQS worker, or async invocation patterns.
- **Gap**: No async handling for any operations. All operations appear to be fast CRUD queries, so long-running processes may not be a current concern.
- **Recommendation**: Not a priority for cost optimization. If operations become long-running (e.g., bulk data operations, report generation), implement async processing with SQS.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL path versioning (`/v1/`, `/v2/`). No version headers. Endpoints are: `/unicorns`, `/unicorns/basket`, `/unicorns/basket/{userUuid}`, `/user`, `/user/login`, `/health/*`, `/data`. No versioning strategy.
- **Gap**: No API versioning. Breaking changes would impact all consumers simultaneously.
- **Recommendation**: Low priority for cost optimization. When adding API Gateway, implement URL path versioning (`/v1/unicorns`).

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: No service discovery. Single monolith deployment — service discovery is not currently needed. No AWS Service Discovery, App Mesh, Consul, or service registry. The database endpoint is passed via environment variable.
- **Gap**: No service discovery infrastructure. Not currently needed for a single monolith.
- **Recommendation**: Not a priority. If the application is decomposed into microservices, implement AWS Cloud Map for service discovery.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent SDK usage. `build.gradle` includes `aws-java-sdk:1.11.567` (AWS SDK v1) but no Bedrock, LangChain, Spring AI, or agent framework imports. No MCP SDK, OpenAI, or Anthropic client references.
- **Gap**: No AI or agent framework integration. AWS SDK v1 is also legacy (SDK v2 is current).
- **Recommendation**: Low priority for cost optimization. If AI capabilities are added, upgrade to AWS SDK v2 and use Amazon Bedrock SDK. Spring Boot 3.x upgrade is a prerequisite for Spring AI.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch, pgvector, Pinecone, Weaviate, or Chroma references in `build.gradle` or any source code. No Bedrock Knowledge Base configuration.
- **Gap**: No vector database capability.
- **Recommendation**: Low priority for cost optimization. If semantic search is needed in the future, Aurora PostgreSQL with pgvector extension provides a cost-effective vector store without additional service costs.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database present, so management is not applicable. Score reflects absence.
- **Gap**: No vector database to manage.
- **Recommendation**: Low priority. When adopting vector search, use a managed service (OpenSearch Serverless, Aurora pgvector) to avoid operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No document chunking, embeddings, or semantic search. No Bedrock, Titan, or OpenAI embedding model references. No similarity search patterns.
- **Gap**: No RAG implementation.
- **Recommendation**: Low priority for cost optimization. RAG can be added when AI capabilities become a business requirement.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database (`unishop` schema) accessed via a single JDBC connection. Three tables: `unicorns`, `unicorns_basket`, `unicorn_user`. All data access goes through one database endpoint configured in `application.properties`. No additional data sources, external APIs, or secondary databases.
- **Gap**: None. Single, clean data source.
- **Recommendation**: Maintain this simplicity when migrating to Aurora. A single managed database is cost-optimal for this application's scale.

#### DATA-Q5: Data Access Pattern
- **Score**: 3/4 🟡
- **Finding**: Well-structured repository pattern: Controllers → Services (interfaces: `UnicornService`, `UserService`, `HealthService`) → Service Implementations → Repository Implementations → MyBatis Mappers → MySQL. Data access is consistently layered through interfaces. `MyBatisConfig.java` centralizes all mapper configuration.
- **Gap**: The data access layer is clean, but no database abstraction that would facilitate switching databases. MyBatis mapper XMLs contain MySQL-specific syntax (though the SQL used is ANSI-standard).
- **Recommendation**: The clean data access layer will ease Aurora migration. The MyBatis mapper XMLs use standard SQL that works with both MySQL and PostgreSQL with minimal changes.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage or document parsing. `build.gradle` includes `aws-java-sdk-s3:1.11.567` but no S3 operations are found in any source code file. Product images are stored as string references (`image` column in `unicorns` table), not actual file storage.
- **Gap**: No unstructured data storage or processing pipeline. S3 SDK is included but unused.
- **Recommendation**: Remove unused `aws-java-sdk-s3` dependency to reduce artifact size. If product images need to be served, use S3 with CloudFront for cost-effective static asset delivery.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `database/create_tables.sql` provides complete schema definitions for all three tables with column types, constraints, primary keys, unique constraints, and seed data. MyBatis mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) document the query patterns. However, no Flyway, Liquibase, or Alembic migration framework — schema changes are not versioned beyond this single creation script.
- **Gap**: Schema is documented in one DDL file but not version-controlled through a migration framework. No JSON Schema, Avro, or formal schema registry.
- **Recommendation**: Adopt Flyway or Liquibase for schema migration versioning. This is important when migrating to Aurora to track schema changes and enable rollbacks.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Well-structured unified data access layer using MyBatis. `MyBatisConfig.java` configures `SqlSessionFactory` with all three mapper locations. Mapper interfaces (`UnicornMapper`, `UserMapper`, `HealthMapper`) are registered as Spring beans. Repository implementations wrap mappers with transaction management (`@Transactional`). All database access is funneled through this single layer.
- **Gap**: Unified layer exists but lacks connection pooling configuration, query timeout settings, or metrics. Default HikariCP settings are used without tuning.
- **Recommendation**: When migrating to Aurora, configure HikariCP connection pool settings in `application.properties` (max pool size, connection timeout, idle timeout) to optimize cost and performance.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings or indexing pipeline. No event-driven refresh triggers, scheduled re-indexing, or CDC patterns.
- **Gap**: No embedding infrastructure.
- **Recommendation**: Low priority for cost optimization. Not applicable until AI/embedding capabilities are added.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 2/4 🟠
- **Finding**: `build.gradle` specifies `mysql-connector-java:8.0.11` (released April 2018). No IaC exists to verify the actual MySQL server version. The JDBC connector version suggests the server may be running MySQL 8.0.x, but the exact version is unknown. MySQL 8.0 reaches end-of-life in April 2026. The connector version 8.0.11 is significantly outdated (current is 8.0.36+). No version pinning in IaC (no IaC exists).
- **Gap**: MySQL connector is severely outdated (8.0.11 from 2018). Actual database server version is unknown and not pinned in IaC. MySQL 8.0 line approaches EOL.
- **Recommendation**: When migrating to Aurora MySQL, use the latest Aurora MySQL 8.0-compatible version. Update the MySQL connector to the latest 8.0.x release. Pin the engine version in IaC to prevent unplanned version changes.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: `database/create_tables.sql` contains only standard DDL: `CREATE SCHEMA`, `CREATE TABLE`, `INSERT INTO`. No stored procedures, triggers, or functions. MyBatis mapper XMLs contain standard SQL: `SELECT`, `INSERT IGNORE INTO`, `DELETE`, `JOIN`. No PL/SQL, T-SQL, or proprietary MySQL constructs beyond `ENGINE=InnoDB` (which is standard). No raw SQL execution bypass in application code.
- **Gap**: None. All business logic is in the application layer. Standard SQL is used throughout.
- **Recommendation**: This is a significant advantage for cost optimization. The absence of stored procedures and proprietary SQL means database migration to Aurora MySQL or Aurora PostgreSQL requires minimal schema changes. The `INSERT IGNORE` syntax may need to be adapted for PostgreSQL (`ON CONFLICT DO NOTHING`) if migrating to Aurora PostgreSQL.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: `application.properties` contains hardcoded database credentials: `spring.datasource.username: MonoToMicroUser`, `spring.datasource.password: MonoToMicroPassword`. No AWS Secrets Manager, Parameter Store, or Vault usage. No `boto3.client('secretsmanager')` or equivalent Java SDK calls. No `.env` file (credentials are directly in the committed properties file).
- **Gap**: Database credentials are hardcoded in the committed configuration file. Critical security risk and compliance violation.
- **Recommendation**: Migrate credentials to AWS Secrets Manager immediately. Use the Spring Cloud AWS Secrets Manager integration or the AWS SDK to retrieve credentials at runtime. This is a Phase 1 quick win that also reduces credential rotation costs.

#### SEC-Q2: IAM Least Privilege
- **Score**: 1/4 ❌
- **Finding**: No IAM policies defined (no IaC). `build.gradle` includes `aws-java-sdk` (full SDK bundle) suggesting broad AWS permissions may be in use. The application uses `EC2MetadataUtils` in `HealthController.java`, implying an EC2 instance role exists, but its permissions are unknown.
- **Gap**: No IAM policy definitions. The full AWS SDK bundle is included rather than specific service SDKs, suggesting potentially broad permissions.
- **Recommendation**: When implementing IaC, create a minimal IAM task role for ECS with only required permissions (Secrets Manager read, CloudWatch logs). Replace the full `aws-java-sdk` with only needed SDK modules to reduce attack surface and artifact size.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: Spring Security OAuth2 infrastructure is present: `ResourceServerConfig.java` has `@EnableResourceServer`, `build.gradle` includes `spring-security-oauth2-autoconfigure`, `spring-security-jwt:1.0.9.RELEASE`, and `spring-cloud-starter-oauth2:2.0.1.RELEASE`. However, `ResourceServerConfig.java` sets `.authorizeRequests().anyRequest().permitAll()` — effectively disabling authentication. `Application.java` ignores all OPTIONS requests. `@PreAuthorize("permitAll()")` is applied to every controller method.
- **Gap**: OAuth2/JWT infrastructure exists but is completely disabled. All endpoints are publicly accessible without authentication.
- **Recommendation**: When ready, configure the OAuth2 resource server to validate JWT tokens from Amazon Cognito or another IdP. The infrastructure is already in place — it just needs to be activated with proper configuration.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration (no IaC). No application-level audit logging. `HealthController.java` uses `System.out.println()` for output. Repository implementations use `e.printStackTrace()` for error handling. No structured logging framework (no SLF4J, Logback, or Log4j2 configuration beyond Spring Boot defaults).
- **Gap**: No audit logging at infrastructure or application level. Exception handling writes to stderr without context.
- **Recommendation**: Configure CloudTrail in IaC for AWS API audit trail. Replace `System.out.println()` and `e.printStackTrace()` with SLF4J/Logback structured logging. Spring Boot includes Logback by default but no configuration file was found to customize it.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. No API Gateway throttle settings. No WAF rules. No application-level rate limiting middleware. `ResourceServerConfig.java` applies no request restrictions.
- **Gap**: No rate limiting. Unprotected endpoints are vulnerable to abuse, which can cause unexpected compute costs.
- **Recommendation**: Implement rate limiting at ALB/API Gateway level when deploying to ECS. This directly prevents cost spikes from abusive traffic.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction in logging. The `User` model stores `email`, `firstName`, `lastName` — all PII. `UserMapper.xml` queries user email directly. `e.printStackTrace()` in repository implementations could log user data in stack traces. No log scrubbing middleware or PII masking libraries.
- **Gap**: PII (user email, names) is handled without redaction. Exception stack traces could leak PII.
- **Recommendation**: Add PII masking to the logging configuration. Use Logback's pattern-based masking or a custom appender to redact email addresses and names from logs.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No approval workflows. No Step Functions with human approval tasks. No manual approval gates in deployment (no CI/CD exists). No approval API endpoints.
- **Gap**: No human-in-the-loop approval for any operations.
- **Recommendation**: Low priority for cost optimization. Implement production deployment approval gates when CI/CD is established.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS configuration (no IaC). No encryption settings on any data stores. The self-managed MySQL database may or may not have encryption enabled — it cannot be determined from the codebase.
- **Gap**: No evidence of encryption at rest for the database or any data stores.
- **Recommendation**: When migrating to Aurora, enable encryption at rest with AWS-managed KMS keys (included at no additional cost). This is a free security improvement.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: `ResourceServerConfig.java` configures Spring Security with `.authorizeRequests().anyRequest().permitAll()` — all endpoints are publicly accessible. Every controller method has `@PreAuthorize("permitAll()")`. While OAuth2 resource server is enabled (`@EnableResourceServer`), it is effectively bypassed.
- **Gap**: All API endpoints are unauthenticated. The security configuration explicitly permits all requests.
- **Recommendation**: Activate OAuth2 token validation by configuring a JWT issuer (e.g., Amazon Cognito). Remove `permitAll()` and define proper role-based access control. This prevents unauthorized access that could generate unexpected compute costs.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: Spring Security OAuth2 dependencies are present but no identity provider is configured. No `aws_cognito_*` resources, no OIDC/SAML configuration, no SSO setup. User authentication is implemented as a simple email lookup in `UserController.login()` → `UserServiceImpl.getByEmail()` — no password verification, no token issuance.
- **Gap**: No centralized identity provider. The "login" endpoint is a simple database lookup with no actual authentication.
- **Recommendation**: Implement Amazon Cognito as the centralized identity provider. Configure the existing Spring Security OAuth2 infrastructure to validate Cognito JWT tokens.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, Datadog, Jaeger, or Zipkin SDK found. No trace ID propagation headers. No instrumentation wrappers or auto-instrumentation configuration. No tracing dependencies in `build.gradle`.
- **Gap**: No distributed tracing capability. No observability into request flows through the application.
- **Recommendation**: When deploying to ECS, enable AWS X-Ray via the X-Ray daemon sidecar. Add the X-Ray SDK for Java to `build.gradle`. Alternatively, adopt OpenTelemetry Java agent for vendor-neutral instrumentation.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: `HealthController.java` uses `System.out.println()` for output. All repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) use `e.printStackTrace()` for error handling. No JSON log formatters, no correlation IDs, no structured logging configuration. Spring Boot includes Logback by default, but no `logback-spring.xml` configuration file exists.
- **Gap**: No structured logging. Unstructured `System.out.println()` and `e.printStackTrace()` throughout the codebase. No correlation IDs for request tracing.
- **Recommendation**: Add a `logback-spring.xml` configuration with JSON output format. Replace all `System.out.println()` with SLF4J logger calls. Add MDC-based correlation IDs. This is essential for cost-effective log analysis with CloudWatch Log Insights.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No eval framework, golden datasets, or LLM evaluation infrastructure. No AI capabilities exist in the application.
- **Gap**: No automated evaluation capability. Not applicable until AI features are added.
- **Recommendation**: Low priority for cost optimization. Implement when AI capabilities are added.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: Spring Boot Actuator is included (`spring-boot-starter-actuator` in `build.gradle`), which provides basic health endpoints (`/actuator/health`). However, no SLO definitions, no CloudWatch alarms, no latency monitoring, and no error budget tracking are configured.
- **Gap**: No SLO definitions. Actuator provides basic health but no SLO-level monitoring.
- **Recommendation**: When deploying to ECS with ALB, define SLOs for response latency (p99 < 500ms) and availability (> 99.9%). Create CloudWatch alarms for these SLOs. This enables data-driven right-sizing decisions.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment automation or rollback configuration. No blue/green, canary, or feature flag infrastructure. No versioned deployments. `bootJar` with `launchScript()` produces a single JAR — rollback would require manually replacing the JAR on EC2.
- **Gap**: No automated rollback capability. Manual JAR replacement for rollback.
- **Recommendation**: ECS provides built-in deployment rollback with circuit breaker. When deploying to ECS, enable deployment circuit breaker with automatic rollback on failure.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, cost attribution, or LLM-related metrics.
- **Gap**: No LLM usage to track. Not applicable.
- **Recommendation**: Low priority. Implement when AI/LLM capabilities are adopted. Use CloudWatch custom metrics for token usage tracking.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics. No `CloudWatch.putMetricData()` calls. No tracking of orders, cart additions, user registrations, or conversion rates. Actuator provides only JVM/infrastructure metrics.
- **Gap**: No business outcome metrics. Cannot correlate infrastructure costs with business value.
- **Recommendation**: Add CloudWatch custom metrics for key business events (cart additions, user registrations). This enables cost-per-transaction analysis essential for cost optimization.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection, no error rate alarms, no latency monitoring, no PagerDuty/OpsGenie integration. No alerting infrastructure of any kind.
- **Gap**: No anomaly detection or alerting. No visibility into application health or error rates.
- **Recommendation**: When deploying to ECS with CloudWatch, configure anomaly detection on error rates and request latency. Set up CloudWatch alarms with SNS notifications for operational awareness.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment automation. `build.gradle` produces a bootJar with `launchScript()` — a self-executing JAR meant for direct deployment on Linux. The commented-out Docker configuration suggests containerization was considered but not implemented. Deployment is manual.
- **Gap**: Manual deployment with no automation, no canary, no blue/green, no rollback strategy.
- **Recommendation**: When deploying to ECS, use rolling updates with deployment circuit breaker as the minimum strategy. For higher reliability, implement blue/green deployments via CodeDeploy.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found. The `src/test/` directory does not exist. `build.gradle` includes `spring-boot-starter-test` as `testImplementation` dependency, but no test classes have been written.
- **Gap**: Zero test coverage. No unit tests, integration tests, or any automated testing.
- **Recommendation**: Add integration tests for critical API endpoints (list unicorns, add to basket, create user) before migration. This provides a safety net for validating the application works correctly after containerization and database migration.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files, SSM Automation documents, or remediation Lambda functions. No Step Functions for incident workflows. No self-healing patterns.
- **Gap**: No incident response automation. All incident response is manual.
- **Recommendation**: When deploying to ECS, ECS service auto-recovery handles basic self-healing (unhealthy task replacement). Create runbooks for common incidents (database connection failures, high latency) and configure automated remediation.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO dashboards or ownership definitions. No observability governance infrastructure. No team ownership files or dashboard configurations.
- **Gap**: No observability governance. No defined ownership model for application health monitoring.
- **Recommendation**: Define service ownership in a CODEOWNERS file. Create CloudWatch dashboards with defined owners for application health, database performance, and cost metrics.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Low | High | APP-Q4: 2/4, INF-Q1: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Triggered | Medium | High | INF-Q1: 1/4, No Dockerfile found | Medium |
| Move to Open Source | Not Triggered | High | — | — | — |
| Move to Managed Databases | Triggered | High | High | INF-Q2: 1/4, DATA-Q10: 2/4 | Medium |
| Move to Managed Analytics | Not Triggered | High | — | — | — |
| Move to Modern DevOps | Triggered | Medium | High | INF-Q5: 1/4, INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Low | Low | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Containers + Move to Managed Databases — these are independent and can run concurrently. Containerizing the application does not depend on database migration, and vice versa.

**Parallel Track 2**: Move to Modern DevOps — CI/CD pipeline setup can run in parallel with both Track 1 workstreams, and in fact enables them (automated deployment to ECS, automated database migration validation).

**Sequential Dependencies**: Move to Cloud Native depends on Move to Containers (must containerize before decomposing). Move to AI depends on foundational infrastructure (containers, managed database, CI/CD) and is deferred to Phase 3.

### Move to Managed Databases

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q2: Score 1/4 — Self-managed MySQL database with direct JDBC connection, no managed service IaC
  - DATA-Q10: Score 2/4 — MySQL connector 8.0.11 (2018), server version unknown and unpinned
- **Current State**: Self-managed MySQL 8.0.x on EC2 with direct JDBC connection. Three simple tables (unicorns, unicorns_basket, unicorn_user) using standard SQL. No stored procedures. Manual backup/failover management.
- **Target State**: Aurora MySQL or Aurora PostgreSQL with automated backups, multi-AZ failover, auto-scaling storage, and Performance Insights. Engine version pinned in IaC.
- **Key Activities**:
  1. Provision Aurora MySQL (or Aurora PostgreSQL) cluster in IaC with appropriate instance class
  2. Use AWS DMS to replicate data from self-managed MySQL to Aurora
  3. Update `application.properties` to use Aurora endpoint via Secrets Manager
  4. Validate application with Aurora using integration tests
  5. Enable Aurora Serverless v2 for automatic scaling to match traffic patterns
- **Dependencies**: IaC implementation (Move to Modern DevOps) should proceed first or in parallel
- **Estimated Effort**: Medium — simple schema, standard SQL, no stored procedures
- **Roadmap Phase Alignment**: Phase 2 (Managed Service Migration)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Containers

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q1: Score 1/4 — Application runs on raw EC2 with no container orchestration
  - No Dockerfile found — a commented-out Docker config exists in `build.gradle` but no Dockerfile is present
- **Current State**: Spring Boot bootJar deployed directly on EC2 instances. No containerization. EC2MetadataUtils confirms bare EC2 deployment.
- **Target State**: Application containerized and running on ECS Fargate with Graviton (ARM64) instances for ~20% cost savings. ECR for image storage.
- **Key Activities**:
  1. Create a Dockerfile based on the existing `bootJar` output
  2. Build and push container image to Amazon ECR
  3. Create ECS Fargate task definition with Graviton (ARM64) architecture
  4. Configure ECS Service with health checks using existing `/health/ishealthy` endpoint
  5. Configure ECS Service Auto Scaling with target tracking on CPU utilization
- **Dependencies**: None — can start immediately
- **Estimated Effort**: Medium — straightforward containerization of a Spring Boot JAR
- **Roadmap Phase Alignment**: Phase 1 (License & Quick Savings) for Dockerfile, Phase 2 for full ECS deployment
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q5: Score 1/4 — Zero IaC coverage
  - INF-Q6: Score 1/4 — No CI/CD automation
  - OPS-Q9: Score 1/4 — Manual deployment strategy
  - OPS-Q10: Score 1/4 — Zero test coverage
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: No IaC, no CI/CD, no automated testing, no deployment automation, no observability. Everything is manual.
- **Target State**: Full IaC coverage with CDK/CloudFormation, CI/CD pipeline with automated test and deploy stages, integration test suite, structured logging with CloudWatch, distributed tracing with X-Ray.
- **Key Activities**:
  1. Implement IaC (CDK or CloudFormation) for all infrastructure with cost allocation tags
  2. Create CI/CD pipeline with build, test, and deploy stages
  3. Add integration tests for critical API endpoints
  4. Configure structured JSON logging with Logback
  5. Enable X-Ray tracing for request flow visibility
- **Dependencies**: None — can start immediately
- **Estimated Effort**: High — building DevOps from scratch across multiple dimensions
- **Roadmap Phase Alignment**: Phase 1 (IaC and CI/CD), Phase 2 (testing and observability), Phase 3 (advanced deployment strategies)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q4: Score 2/4 — Monolith with identifiable modules but shared database
  - INF-Q1: Score 1/4 — Raw EC2 compute
  - APP-Q3: Score 1/4 — 100% synchronous communication
  - APP-Q10: Score 1/4 — No async processing
- **Current State**: Single Spring Boot monolith with all domains (Unicorn, User, Basket, Health) in one deployable. Synchronous communication only. Shared MySQL database.
- **Target State**: Modular services with independent deployment capability, async communication for write operations, event-driven patterns where appropriate.
- **Key Activities**:
  1. Containerize the monolith as-is first (prerequisite)
  2. Identify first candidate service for extraction (Basket service has clearest boundary)
  3. Implement API Gateway for routing between monolith and extracted services
  4. Add async messaging (SQS) for decoupled write operations
- **Dependencies**: Move to Containers must complete first. Move to Managed Databases should be complete or in progress.
- **Estimated Effort**: High — requires service decomposition, data separation, and async patterns
- **Roadmap Phase Alignment**: Phase 3 (Optimization & Governance) — lower priority for cost optimization goal
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to AI

- **Priority**: Low
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks
  - DATA-Q1: Score 1/4 — No vector database
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No eval framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI or agent capabilities. Legacy AWS SDK v1. Java 8 and Spring Boot 2.1 limit access to modern AI frameworks.
- **Target State**: AI-ready with modern SDK, potential Bedrock integration for product recommendations or customer support.
- **Key Activities**:
  1. Upgrade to Spring Boot 3.x and Java 17+ (prerequisite for Spring AI)
  2. Upgrade from AWS SDK v1 to v2
  3. Evaluate Bedrock integration for product-related AI features
- **Dependencies**: Spring Boot upgrade, managed database, and containerization should be complete
- **Estimated Effort**: High — requires major framework upgrades before AI adoption
- **Roadmap Phase Alignment**: Phase 3 (Optimization & Governance)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Readiness Roadmap

### Phase 1 — License & Quick Savings (Days 1–30)

1. **Move secrets to AWS Secrets Manager**: Migrate hardcoded database credentials from `application.properties` to Secrets Manager. Eliminates security risk and enables credential rotation. *(SEC-Q1, immediate)*
2. **Create a Dockerfile**: Build a Dockerfile for the Spring Boot application using the `bootJar` output. Target ARM64 for Graviton compatibility. The commented-out Docker config in `build.gradle` provides a starting point. *(INF-Q1, prerequisite for ECS)*
3. **Implement baseline IaC**: Define VPC, subnets, security groups, and ECS cluster in CDK or CloudFormation. Include mandatory cost allocation tags on all resources. *(INF-Q5, INF-Q9)*
4. **Create basic CI/CD pipeline**: Set up GitHub Actions or CodePipeline with stages: Gradle build → Docker build → push to ECR. *(INF-Q6)*
5. **Add structured logging**: Create `logback-spring.xml` with JSON format. Replace `System.out.println()` and `e.printStackTrace()` with SLF4J logger calls. *(OPS-Q2)*

### Phase 2 — Managed Service Migration (Months 1–3)

1. **Migrate MySQL to Aurora**: Provision Aurora MySQL (or Aurora PostgreSQL) cluster. Use AWS DMS for zero-downtime migration. Pin engine version in IaC. Enable encryption at rest (free with AWS-managed KMS). The simple schema (3 tables, no stored procedures, standard SQL) makes this low-risk. *(INF-Q2, DATA-Q10, SEC-Q8)*
   - **Cross-dependency**: IaC from Phase 1 must be in place to define Aurora cluster
2. **Deploy to ECS Fargate with Graviton**: Create ECS task definition with ARM64/Graviton architecture. Configure health checks using `/health/ishealthy` endpoint. Set up ECS Service Auto Scaling. *(INF-Q1, INF-Q10)*
   - **Cross-dependency**: Dockerfile from Phase 1, CI/CD pipeline from Phase 1
3. **Implement ALB**: Place Application Load Balancer in front of ECS tasks. Configure health checks, HTTPS, and basic request routing. *(INF-Q7)*
4. **Add integration tests**: Write integration tests for critical API endpoints (GET /unicorns, POST /unicorns/basket, POST /user). Run in CI pipeline. *(OPS-Q10)*
5. **Enable distributed tracing**: Add AWS X-Ray SDK sidecar to ECS task definition. Instrument Spring Boot with X-Ray auto-configuration. *(OPS-Q1)*
6. **Complete CI/CD pipeline**: Add deploy-to-ECS stage with deployment circuit breaker and automatic rollback. *(OPS-Q5, OPS-Q9)*

### Phase 3 — Optimization & Governance (Months 3–6)

1. **Right-size compute**: Analyze ECS task CPU/memory utilization after 30+ days of production data. Right-size task definitions and auto-scaling parameters. *(Cost optimization)*
2. **Enable Aurora Serverless v2**: Evaluate Aurora Serverless v2 for automatic scaling to match traffic patterns, eliminating over-provisioning. *(Cost optimization)*
3. **Implement cost governance**: Set up AWS Budgets and Cost Anomaly Detection. Create CloudWatch dashboards for cost-per-transaction analysis. Implement tagging enforcement policies. *(Cost governance)*
4. **Add business metrics**: Publish CloudWatch custom metrics for cart additions, user registrations, and orders. Correlate business metrics with infrastructure costs. *(OPS-Q7)*
5. **Configure SLOs and alerting**: Define SLOs for latency and availability. Create CloudWatch alarms and anomaly detection for error rates. *(OPS-Q4, OPS-Q8)*
6. **Plan Spring Boot upgrade**: Assess effort for Spring Boot 2.1 → 3.x migration (required for Java 17+, Spring AI, and latest Spring ecosystem). The upgrade enables GraalVM native compilation for potential cold start improvements. *(APP-Q1)*
7. **Evaluate service decomposition**: If specific modules would benefit from independent scaling or different database technologies, plan extraction using Strangler Fig pattern. *(APP-Q4, deferred — not primary cost optimization lever)*

---

## Recommended Self-Paced Learning Materials

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `build.gradle` | Spring Boot 2.1.6, Java 8, MySQL connector 8.0.11, AWS SDK 1.11.567, Spring Security OAuth2, MyBatis, Actuator. Commented-out Docker config. |
| 2 | `application.properties` | MySQL JDBC connection string, hardcoded credentials (MonoToMicroUser/MonoToMicroPassword), port 8080 |
| 3 | `database/create_tables.sql` | 3 tables (unicorns, unicorns_basket, unicorn_user), InnoDB engine, UTF8MB4, standard SQL DDL, seed data |
| 4 | `Application.java` | @SpringBootApplication entry point, CORS config, OPTIONS request bypass |
| 5 | `ResourceServerConfig.java` | @EnableResourceServer with permitAll() — OAuth2 disabled |
| 6 | `UnicornController.java` | GET /unicorns, @PreAuthorize("permitAll()"), synchronous ResponseEntity |
| 7 | `BasketController.java` | POST/DELETE/GET /unicorns/basket, synchronous CRUD operations |
| 8 | `UserController.java` | POST /user, POST /user/login — email-based lookup, no password verification |
| 9 | `HealthController.java` | EC2MetadataUtils usage (confirms EC2), System.out.println(), health endpoints |
| 10 | `DataReplicationController.java` | GET /data endpoint for basket replication |
| 11 | `UnicornServiceImpl.java` | Business logic in service layer, constructor injection |
| 12 | `UserServiceImpl.java` | User creation with UUID generation, email lookup |
| 13 | `UnicornRepositoryImpl.java` | e.printStackTrace() error handling, @Transactional, MyBatis mapper delegation |
| 14 | `UserRepositoryImpl.java` | synchronized create method, e.printStackTrace() error handling |
| 15 | `HealthRepositoryImpl.java` | Database reachability check via SELECT count(*) |
| 16 | `UnicornMapper.xml` | INSERT IGNORE (idempotency), JOIN queries, standard SQL |
| 17 | `UserMapper.xml` | insert ignore (idempotency), email-based SELECT |
| 18 | `HealthMapper.xml` | SELECT count(*) from unicorns (health check) |
| 19 | `MyBatisConfig.java` | Centralized SqlSessionFactory, mapper bean configuration |
| 20 | `CoreModel.java` | Base model with @JsonIgnore/@JsonSerialize, Joda DateTime usage |
