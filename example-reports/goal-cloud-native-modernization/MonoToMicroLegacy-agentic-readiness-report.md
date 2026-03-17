# Agentic Readiness Assessment Report
**Target**: MonoToMicroLegacy (Java Spring Boot Monolith)
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

This legacy Java 8 Spring Boot 2.1.x monolith running on EC2 with MySQL is fundamentally unprepared for cloud-native modernization. The application has **zero infrastructure-as-code**, **no CI/CD pipeline**, **no containerization**, and **no API documentation** — all critical prerequisites for decomposing into containerized microservices on EKS. The codebase does exhibit some positive internal structure (separate controllers per domain, repository pattern with MyBatis mappers, service interface abstractions), which provides a foundation for incremental decomposition. However, the shared MySQL database schema (`unishop` with 3 co-located tables), hardcoded credentials, complete absence of observability, and lack of any test coverage represent substantial barriers to the EKS migration goal. The most urgent actions are containerizing the monolith as-is, establishing Terraform IaC, and building a CI/CD pipeline with GitOps — all prerequisites before any service extraction can begin safely.

### Overall Score: 1.2 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.0 / 4.0 | ❌ |
| Application Architecture | 1.2 / 4.0 | ❌ |
| Data Foundations | 1.8 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.1 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

**1. APP-Q4 — Tightly-Coupled Monolith Architecture (Score: 1/4)**
All domains (Unicorn catalog, Shopping basket, User management, Health checks, Data replication) are deployed as a single Spring Boot JAR with a shared MySQL schema (`unishop`). There are no independent service boundaries. **Why this blocks cloud-native modernization**: You cannot deploy, scale, or update services independently on EKS until the monolith is decomposed. **First step**: Conduct a domain modeling workshop to identify bounded contexts (Catalog, Basket, User) and map data coupling between the 3 MySQL tables (`unicorns`, `unicorns_basket`, `unicorn_user`).

**2. INF-Q1 — EC2-Only Compute with No Container Orchestration (Score: 1/4)**
`HealthController.java` calls `EC2MetadataUtils.getInstanceInfo()`, confirming the application runs directly on EC2 instances. No Dockerfile, no ECS/EKS task definitions, no container orchestration of any kind. **Why this blocks cloud-native modernization**: EKS migration requires the application to be containerized first. Without a Dockerfile, there is no path to Kubernetes deployment. **First step**: Create a multi-stage Dockerfile for the Spring Boot application using the existing `bootJar` Gradle task with `launchScript()`.

**3. INF-Q5 — Zero Infrastructure as Code (Score: 1/4)**
No Terraform `.tf` files, no CDK stacks, no CloudFormation templates, no Helm charts exist anywhere in the repository. All infrastructure is presumably provisioned manually or outside the repo. **Why this blocks cloud-native modernization**: GitOps deployment (a stated preference) requires all infrastructure defined as code in a Git repository. Manual provisioning cannot support the automated, repeatable deployments needed for microservices on EKS. **First step**: Create a Terraform module defining the VPC, EKS cluster, Aurora MySQL, and ECR repository.

**4. INF-Q6 — No CI/CD Pipeline (Score: 1/4)**
No GitHub Actions workflows, no Jenkinsfile, no `buildspec.yml`, no CodePipeline definitions. The `build.gradle` includes `bootJar { launchScript() }`, suggesting manual deployment by copying the JAR to EC2. **Why this blocks cloud-native modernization**: Microservices on EKS require automated build, test, and deploy pipelines — especially with GitOps (ArgoCD/Flux). Manual deployments do not scale to multiple independently deployed services. **First step**: Create a GitHub Actions workflow or CodePipeline that builds the Docker image, pushes to ECR, and deploys to EKS via Helm/ArgoCD.

**5. APP-Q3 — 100% Synchronous Communication (Score: 1/4)**
All 6 controllers (`UnicornController`, `BasketController`, `UserController`, `HealthController`, `DataReplicationController`, `CoreController`) use synchronous HTTP request-response via `ResponseEntity`. No SQS, SNS, EventBridge, or any messaging imports exist. **Why this blocks cloud-native modernization**: Microservices require async communication for resilience and decoupling. Synchronous inter-service calls create cascading failure chains and tight temporal coupling. The Basket → Catalog relationship (JOIN in `UnicornMapper.xml`) will need an async event pattern when these become separate services. **First step**: Introduce Amazon SQS or EventBridge for the basket-to-catalog data flow as the first async communication pattern.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: `HealthController.java` calls `EC2MetadataUtils.getInstanceInfo()` to retrieve instance ID, type, AZ, and region — confirming the application runs directly on EC2. The `build.gradle` uses `bootJar { launchScript() }` which generates a system service init script, consistent with bare EC2 deployment. No Dockerfile, no ECS task definitions, no EKS manifests, no Lambda functions found.
- **Gap**: 100% of compute is raw EC2. No container orchestration or serverless compute.
- **Recommendation**: Create a multi-stage Dockerfile, push to Amazon ECR, and deploy to EKS with Fargate. Replace `EC2MetadataUtils` calls with Kubernetes downward API or IMDS v2.

#### INF-Q2: Databases
- **Score**: 1/4 ❌
- **Finding**: `application.properties` defines `spring.datasource.url: jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The MySQL connector `mysql:mysql-connector-java:8.0.11` is declared in `build.gradle`. No IaC defining `aws_rds_*` or `aws_dynamodb_*` resources. Database credentials are hardcoded in `application.properties` (`MonoToMicroUser`/`MonoToMicroPassword`). The absence of any IaC and the direct JDBC connection pattern suggest either self-managed MySQL on EC2 or an unmanaged RDS instance created outside the repo.
- **Gap**: No IaC confirms managed database. Database credentials hardcoded. No automated failover configuration visible.
- **Recommendation**: Migrate to Amazon Aurora MySQL using AWS DMS. Define the Aurora cluster in Terraform with automated failover, backups, and engine version pinning. Move credentials to AWS Secrets Manager.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow engine detected. No workflow definitions or state machine patterns in any file. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` is straightforward CRUD with no multi-step orchestration.
- **Gap**: No workflow orchestration capability exists.
- **Recommendation**: Introduce AWS Step Functions for any multi-step business processes that emerge during decomposition (e.g., order processing workflows spanning Catalog and Basket services).

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, MSK, or any messaging service imports. AWS SDK `com.amazonaws:aws-java-sdk:1.11.567` is present in `build.gradle` but only used for EC2 metadata. All inter-component communication is synchronous method calls within the monolith.
- **Gap**: No async messaging infrastructure. All communication is synchronous.
- **Recommendation**: Introduce Amazon SQS or EventBridge as the backbone for inter-service communication when decomposing. Start with the Basket → Catalog event flow (the `getUnicornBasket` JOIN query in `UnicornMapper.xml` will need to become an API call or event-driven sync).

#### INF-Q5: Infrastructure as Code
- **Score**: 1/4 ❌
- **Finding**: Zero IaC files found in the entire repository. No `.tf` files, no CDK stacks (no `cdk.json`), no CloudFormation templates (`template.yaml`), no Helm charts, no Kustomize manifests. The only build file is `build.gradle` for the Java application.
- **Gap**: 0% infrastructure defined as code. All infrastructure is provisioned manually or managed outside this repository.
- **Recommendation**: Create a Terraform project defining VPC, EKS cluster (with Fargate profiles), Aurora MySQL, ECR repository, and ALB/API Gateway. Use Terraform modules for reusability. Store state in S3 with DynamoDB locking.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No `.github/workflows/` directory, no `Jenkinsfile`, no `buildspec.yml`, no `.gitlab-ci.yml`, no CodePipeline definitions. The `build.gradle` task `bootJar { launchScript() }` generates an executable JAR suitable for manual deployment as a Linux service.
- **Gap**: No CI/CD pipeline. Deployments are manual.
- **Recommendation**: Implement a GitOps pipeline: GitHub Actions or CodePipeline for CI (build → test → Docker build → ECR push), and ArgoCD or Flux for CD to EKS. Align with the stated preference for GitOps deployment.

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: `application.properties` sets `server.port=8080`. The application exposes HTTP endpoints directly (`/unicorns`, `/unicorns/basket`, `/user`, `/health`, `/data`). `MVCConfig.java` configures CORS to allow all methods from all origins. No API Gateway, ALB, or CloudFront configuration exists.
- **Gap**: No API entry point with throttling, authentication, or request validation. Direct service exposure on port 8080.
- **Recommendation**: Deploy an AWS ALB Ingress Controller on EKS or Amazon API Gateway in front of the services. Configure throttling, request validation, and authentication at the gateway layer.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming infrastructure. No Kafka or streaming SDK imports. The `DataReplicationController.java` has a `/data` endpoint that calls `getAllBaskets()` — a synchronous read of all baskets, not a streaming pattern.
- **Gap**: No real-time streaming capability.
- **Recommendation**: If event-driven data replication is needed (replacing the synchronous `DataReplicationController`), introduce Amazon Kinesis Data Streams or MSK for real-time event streaming between decomposed services.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions in IaC (no IaC exists). `ResourceServerConfig.java` allows all requests with `authorizeRequests().anyRequest().permitAll()`. `MVCConfig.java` allows CORS from all origins for all HTTP methods. `Application.java` ignores all OPTIONS requests in WebSecurity.
- **Gap**: No network segmentation, no security groups, no private subnets. Application-level security is completely open.
- **Recommendation**: Define VPC with public/private subnets in Terraform. Place EKS worker nodes and Aurora in private subnets. Use Kubernetes NetworkPolicies and AWS Security Groups for pod-level network segmentation.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No ASG, ECS Service auto-scaling, Lambda concurrency, or Kubernetes HPA/VPA configurations. No scaling policies of any kind.
- **Gap**: No auto-scaling. Application likely runs on a fixed number of EC2 instances.
- **Recommendation**: Configure Kubernetes Horizontal Pod Autoscaler (HPA) for each service on EKS. Use Karpenter or EKS Auto Mode for cluster auto-scaling. Define min/max pod counts based on load testing.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`). Spring Boot 2.1.0 (`springBootVersion = '2.1.0.RELEASE'`). Gradle 7.4 as build tool (`gradle-wrapper.properties`). Java has a solid agent ecosystem via Spring AI but is not tier-1 compared to Python or TypeScript for agent framework maturity.
- **Gap**: Java 8 is an older LTS version (EOL Jan 2030 for extended support). Spring Boot 2.1.x reached EOL in November 2021. The AWS SDK version 1.11.567 is pre-v2 (legacy SDK).
- **Recommendation**: Upgrade to Java 17+ and Spring Boot 3.x as part of containerization. Migrate from AWS SDK v1 to AWS SDK v2 for better async support and performance.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No `openapi.yaml`, `swagger.json`, or any API specification files exist. No `@ApiOperation`, `@OpenAPIDefinition`, or Swagger annotations on any controller. No API documentation of any kind. Endpoints are discoverable only by reading source code: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`, `GET /data`.
- **Gap**: Zero API documentation. No OpenAPI spec.
- **Recommendation**: Add SpringDoc OpenAPI (`springdoc-openapi-ui`) to auto-generate OpenAPI specs from the existing controllers. This is a prerequisite for API Gateway integration and service contract definition during decomposition.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All 10 endpoints across 5 controllers return `ResponseEntity` synchronously. No message publishing (SQS, SNS, EventBridge), no event-driven handlers, no queue consumers. The event-like class names (`ReadUnicornsEvent`, `UnicornsReadEvent`, `WriteUnicornsBasketEvent`, etc.) in `com.monoToMicro.core.events` are misleading — they are plain DTOs used for internal method parameters, not actual async events.
- **Gap**: 100% synchronous communication. No async capability whatsoever.
- **Recommendation**: Introduce async messaging (SQS/EventBridge) for inter-service communication during decomposition. The Basket service will need to communicate with the Catalog service asynchronously to avoid tight coupling.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: Single Spring Boot application with one `build.gradle`, one `Application.java` entry point with `@SpringBootApplication`. All 5 domains (Unicorn Catalog, Basket, User, Health, DataReplication) are in one deployable unit. All 3 MySQL tables (`unicorns`, `unicorns_basket`, `unicorn_user`) reside in the shared `unishop` schema. The `UnicornMapper.xml` contains a JOIN between `unicorns` and `unicorns_basket` tables, creating a data-level coupling between the Catalog and Basket domains. **Positive internal structure**: Separate service interfaces (`UnicornService`, `UserService`, `HealthService`), repository pattern (`UnicornRepository`, `UserRepository`, `HealthRepository`), and separate controllers per domain — but all tightly coupled through shared database and single deployment.
- **Gap**: Tightly-coupled monolith with shared database schema. The cross-table JOIN in `UnicornMapper.xml` (`getUnicornBasket` query joins `unicorns` and `unicorns_basket`) creates a data-level dependency that will need to be resolved during decomposition.
- **Recommendation**: Use the Strangler Fig pattern to incrementally extract services. Start with the User service (least coupled — only `unicorn_user` table, no JOINs with other tables). The Basket service extraction will require replacing the direct JOIN with an API call to the Catalog service.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: Controllers return `ResponseEntity<Collection<Unicorn>>`, `ResponseEntity<UnicornBasket>`, `ResponseEntity<User>` — Java objects serialized to JSON by Spring's Jackson integration. Models use `@JsonInclude(JsonInclude.Include.NON_NULL)` for clean JSON output. `CoreModel` uses `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` and `@JsonIgnore` on internal fields.
- **Gap**: JSON responses are present but there is no standardized error response format. Error responses return raw `HttpStatus.BAD_REQUEST` with no body. No standardized envelope pattern (e.g., `{ "data": ..., "errors": ..., "meta": ... }`).
- **Recommendation**: Implement a standardized JSON response envelope and error handling with `@ControllerAdvice`. This ensures consistent error responses across all future microservices.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` is straightforward CRUD operations (get, create, add-to-basket, remove-from-basket). No multi-step workflows, no state machines, no sagas.
- **Gap**: No workflow orchestration capability. As services are decomposed, cross-service transactions will require orchestration.
- **Recommendation**: Introduce AWS Step Functions for cross-service workflows during decomposition. For example, an order checkout flow spanning Basket validation, payment, and inventory update.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys, no idempotency tokens in any API. `UnicornMapper.xml` uses `INSERT IGNORE INTO unicorns_basket` and `UserMapper.xml` uses `insert ignore into unicorn_user`, which provides MySQL-level deduplication based on unique constraints — not true API-level idempotency. No `Idempotency-Key` header handling.
- **Gap**: No API-level idempotency patterns. The `INSERT IGNORE` provides database-level deduplication only.
- **Recommendation**: Implement idempotency key support for write operations (POST, DELETE). Critical for microservices where network retries are common. Use DynamoDB or a dedicated idempotency store.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. `ResourceServerConfig.java` permits all requests with no throttling. No WAF rules, no API Gateway with usage plans, no application-level rate limiting middleware. CORS in `MVCConfig.java` allows all origins and all methods.
- **Gap**: Zero rate limiting. Any client can make unlimited requests.
- **Recommendation**: Configure rate limiting at the API Gateway / ALB Ingress level on EKS. Add WAF rules for DDoS protection. For per-service rate limiting, consider Spring Cloud Gateway or a service mesh rate limiting policy.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers (Resilience4j, Hystrix), no retry logic, no timeout configurations. Exception handling across all repositories (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) uses bare `try-catch` blocks with `e.printStackTrace()` that swallow exceptions and return null. `UserRepositoryImpl.create()` is `synchronized`, introducing a thread-blocking bottleneck.
- **Gap**: No resilience patterns. Exception handling swallows errors. The `synchronized` method in `UserRepositoryImpl` will not scale in a distributed environment.
- **Recommendation**: Add Resilience4j for circuit breaker, retry, and timeout patterns. Replace `e.printStackTrace()` with proper structured logging. Remove the `synchronized` keyword and rely on database-level concurrency control.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: No background jobs, no async processing, no job status APIs. All operations are short CRUD operations (database reads/writes). However, `DataReplicationController.java` calls `getAllBaskets()` which performs a full table scan JOIN — this could become long-running as data grows. No async infrastructure to handle such operations.
- **Gap**: No async processing capability for potentially long-running operations.
- **Recommendation**: Convert the `DataReplicationController` `/data` endpoint to an async job pattern using SQS + Lambda or Step Functions. Add job status polling endpoints for any operations that may exceed 30 seconds.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL versioning (`/v1/`, `/v2/`), no version headers, no versioning strategy. Endpoints are bare paths: `/unicorns`, `/unicorns/basket`, `/user`, `/health`, `/data`. No changelog or API versioning documentation.
- **Gap**: No API versioning. Breaking changes would affect all consumers immediately.
- **Recommendation**: Adopt URL-based versioning (e.g., `/v1/unicorns`) as part of the API Gateway setup. Critical for microservices where services evolve independently.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith — no service discovery needed currently. The only external dependency is the MySQL endpoint configured via the `MONO_TO_MICRO_DB_ENDPOINT` environment variable in `application.properties`. No service registry, no API catalog, no service mesh.
- **Gap**: No service discovery mechanism. When decomposed, services will need to discover each other.
- **Recommendation**: Use Kubernetes native service discovery (kube-dns) on EKS. For cross-cluster or advanced traffic management, consider AWS App Mesh or Istio. Register all service APIs in an API catalog.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports. No Bedrock, LangChain, Spring AI, OpenAI, or Anthropic SDKs. AWS SDK `1.11.567` is present but is pre-Bedrock (v1 SDK, 2019 era). No MCP SDK, no agent tool definitions.
- **Gap**: No AI/agent capability. AWS SDK is legacy v1.
- **Recommendation**: Upgrade to AWS SDK v2 as part of the Spring Boot 3.x migration. Add Spring AI or Strands Agents SDK when building agent capabilities in Phase 3.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database present. No OpenSearch with k-NN, no pgvector, no Pinecone, Weaviate, or Chroma imports. No Bedrock Knowledge Base configuration. No vector-related dependencies in `build.gradle`.
- **Gap**: No vector database or semantic search capability.
- **Recommendation**: Add Amazon OpenSearch Service with k-NN plugin or Aurora PostgreSQL with pgvector extension when building AI/RAG capabilities in Phase 3.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists, so management is not applicable. No managed or self-hosted vector store of any kind.
- **Gap**: No vector database to manage.
- **Recommendation**: When introducing a vector store, use a managed service (OpenSearch Service, Bedrock Knowledge Bases) to avoid operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No document chunking, no embedding model calls, no semantic search patterns. No Bedrock, OpenAI, or embedding SDK imports. No RAG pipeline of any kind.
- **Gap**: No RAG implementation.
- **Recommendation**: If knowledge-augmented AI is needed in Phase 3, implement a RAG pipeline using Bedrock Knowledge Bases with S3 as the document store and Aurora pgvector for embeddings.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database (`unishop` schema) with 3 tables (`unicorns`, `unicorns_basket`, `unicorn_user`). All data access goes through one datasource configured in `application.properties`. No additional API clients, no external data source connections.
- **Gap**: None — minimal data source sprawl.
- **Recommendation**: Maintain the single data source pattern. During decomposition, each microservice should own its own database (database-per-service pattern) — but access should be via APIs, not direct cross-service database queries.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Well-structured repository pattern: Controllers → Services (`UnicornServiceImpl`, `UserServiceImpl`) → Repositories (`UnicornRepositoryImpl`, `UserRepositoryImpl`) → MyBatis Mappers (`UnicornMapper`, `UserMapper`). Controllers never directly access the database. However, these are direct JDBC connections via MyBatis, not API-based access.
- **Gap**: Data is accessed via direct database connections, not through well-defined APIs. When services are decomposed, the Basket service will need API-based access to Catalog data instead of the current direct JOIN in `UnicornMapper.xml`.
- **Recommendation**: During decomposition, expose each service's data through REST APIs. Replace cross-domain JOINs (e.g., `getUnicornBasket` in `UnicornMapper.xml`) with API calls between services.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: AWS SDK S3 dependency (`com.amazonaws:aws-java-sdk-s3:1.11.567`) exists in `build.gradle` but is not used in any source code. No S3 bucket references, no document parsing (Textract, Tika), no file upload/download logic.
- **Gap**: No unstructured data handling despite S3 SDK being in dependencies (likely unused).
- **Recommendation**: Remove the unused S3 SDK dependency. If unstructured data handling is needed in the future, use S3 with Amazon Textract for document parsing.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `database/create_tables.sql` provides the complete schema definition with column types, constraints (UNIQUE, PRIMARY KEY, NOT NULL), and engine settings (InnoDB, UTF8MB4). MyBatis XML mappers (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) serve as query contract documentation. However, there is no formal schema versioning tool (no Flyway, Liquibase, or Alembic migration files).
- **Gap**: Schema is defined but not versioned. No migration tool. Schema changes would be applied manually.
- **Recommendation**: Adopt Flyway or Liquibase for schema versioning. Convert `create_tables.sql` into an initial migration. This is essential for safe database changes during and after decomposition.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Centralized, consistent data access layer using the Repository pattern with MyBatis mappers. `MyBatisConfig.java` configures all three mappers (`UnicornMapper`, `UserMapper`, `HealthMapper`) through `SqlSessionFactoryBean`. All repositories follow the same pattern: `@Repository @Transactional` with `@Autowired` mapper injection. Consistent error handling pattern (try-catch with `e.printStackTrace()`).
- **Gap**: Consistent but not ideal — error handling swallows exceptions. No connection pooling configuration visible. No retry logic on database calls.
- **Recommendation**: Add HikariCP connection pooling configuration (Spring Boot default). Replace `e.printStackTrace()` with proper logging. Add retry logic for transient database errors.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist. No vector indices. No embedding refresh pipelines, no CDC patterns, no scheduled re-indexing.
- **Gap**: No embedding infrastructure to maintain.
- **Recommendation**: When implementing embeddings in Phase 3, design for incremental updates using DynamoDB Streams or Aurora CDC to trigger embedding re-generation.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 1/4 ❌
- **Finding**: MySQL connector version `8.0.11` in `build.gradle` (released April 2018, over 7 years old). No IaC specifies the actual MySQL engine version — it is completely unknown. The `application.properties` connection string targets MySQL on port 3306 but the server version is not determinable from the code. No engine version pinning in any configuration.
- **Gap**: Database engine version is unknown and unpinned. MySQL connector is severely outdated (8.0.11 vs current 8.0.36+). Risk of running an EOL or vulnerable MySQL engine version.
- **Recommendation**: Pin the Aurora MySQL engine version in Terraform (e.g., Aurora MySQL 3.x compatible with MySQL 8.0). Update the MySQL connector to the latest 8.0.x version. Establish a version upgrade policy.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 3/4 🟡
- **Finding**: No stored procedures, no triggers, no functions in `create_tables.sql`. SQL in MyBatis mappers is standard CRUD: `SELECT *`, `INSERT IGNORE INTO`, `DELETE FROM`, and `SELECT ... JOIN`. The `INSERT IGNORE` syntax is MySQL-specific but minor. No proprietary PL/SQL or T-SQL constructs. All business logic resides in the Java application layer.
- **Gap**: Minor MySQL-specific syntax (`INSERT IGNORE`, `ENGINE=InnoDB`, `UTF8MB4` charset). These would need adjustment for a non-MySQL target but are standard for Aurora MySQL.
- **Recommendation**: Since Aurora MySQL is the preferred target (per customer preferences), the existing SQL is fully compatible. Document the MySQL-specific syntax for future reference if the database engine changes.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. These are committed to source control. The database endpoint uses an environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) but credentials are plaintext. No AWS Secrets Manager, no HashiCorp Vault, no SSM Parameter Store usage.
- **Gap**: Credentials hardcoded in source control. Critical security vulnerability.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager immediately. Use Spring Cloud AWS Secrets Manager integration or Kubernetes external secrets operator on EKS to inject secrets at runtime.

#### SEC-Q2: IAM Least Privilege
- **Score**: 1/4 ❌
- **Finding**: No IAM policies defined anywhere (no IaC exists). AWS SDK `1.11.567` is present in `build.gradle` but no IAM role configuration is visible. The application likely uses the EC2 instance profile, but its permissions are unknown and unmanaged in this repository.
- **Gap**: No IAM policies defined or managed. Permissions are unknown and likely overly broad.
- **Recommendation**: Define per-service IAM roles in Terraform with least-privilege policies. Use IRSA (IAM Roles for Service Accounts) on EKS to assign fine-grained permissions to each Kubernetes pod.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: Spring Security OAuth2 dependencies present in `build.gradle`: `spring-cloud-starter-oauth2:2.0.1`, `spring-security-jwt:1.0.9`, `spring-security-oauth2-autoconfigure`. `ResourceServerConfig.java` has `@EnableResourceServer` annotation. However, all endpoints use `@PreAuthorize("permitAll()")` — effectively disabling auth enforcement. The OAuth2 framework is configured but not utilized.
- **Gap**: OAuth2 framework is present but all auth is disabled. No identity propagation occurs. User identity is passed as request body data (`User` object in `UserController.java`), not via tokens.
- **Recommendation**: Configure the OAuth2 resource server to validate JWT tokens from Amazon Cognito or an external IdP. Remove `permitAll()` and implement proper role-based access control.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration. No audit logging implementation. Logging consists of `System.out.println()` in `HealthController.java` and `e.printStackTrace()` in repository implementations. No structured audit trail of who accessed what data.
- **Gap**: No audit logging. No way to trace user actions through the system.
- **Recommendation**: Enable CloudTrail for AWS API audit logging. Implement application-level audit logging using a structured logger (SLF4J + Logback JSON) that records user identity, action, resource, and timestamp for every state-changing operation.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. No API Gateway usage plans, no WAF rate rules, no application-level rate limiting middleware. All endpoints are open to unlimited requests.
- **Gap**: Zero rate limiting. Vulnerable to abuse and DDoS.
- **Recommendation**: Configure rate limiting at the EKS Ingress/API Gateway level. Add per-client quotas. Deploy AWS WAF with rate-based rules in front of the ALB.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: User PII (email, first name, last name) is handled in `UserController.java` and `UserMapper.xml` with no log scrubbing. `e.printStackTrace()` in `UserRepositoryImpl.java` could leak user data in error messages. No PII masking libraries, no log filters, no Macie integration.
- **Gap**: No PII redaction in logging. User data may appear in stack traces and logs.
- **Recommendation**: Implement structured logging with PII masking for email and name fields. Use CloudWatch Logs data protection policies to detect and redact PII automatically.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No approval workflows, no human-in-the-loop patterns. No Step Functions with `waitForTaskToken`. No approval gates in any process. The basket deletion endpoint (`DELETE /unicorns/basket`) has no confirmation or approval step.
- **Gap**: No human approval workflows for any operations.
- **Recommendation**: As the system matures, implement approval workflows for high-risk operations (e.g., bulk data deletion) using Step Functions with human approval tasks.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS configuration. No encryption settings on any data store. No IaC to define encryption policies. The MySQL connection string in `application.properties` does not include SSL/TLS parameters.
- **Gap**: No encryption at rest or in transit configuration visible. Database connections may not use TLS.
- **Recommendation**: Enable encryption at rest for Aurora MySQL using KMS customer-managed keys. Add `useSSL=true&requireSSL=true` to the JDBC connection string. Define KMS key policies in Terraform.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: `ResourceServerConfig.java` configures `@EnableResourceServer` but the `configure()` method allows all requests: `authorizeRequests().anyRequest().permitAll()`. Every endpoint across all controllers uses `@PreAuthorize("permitAll()")`. `Application.java` ignores all OPTIONS requests globally. CORS allows all origins and all methods. Effectively, there is zero authentication.
- **Gap**: All API endpoints are completely unauthenticated. OAuth2 framework is configured but bypassed.
- **Recommendation**: Configure JWT validation in the resource server. Integrate with Amazon Cognito user pool. Implement role-based access control (`@PreAuthorize("hasRole('USER')")`) for data-modifying endpoints.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: Spring Security OAuth2 dependencies suggest an intended Cognito or OAuth integration that was never completed. No Cognito user pool, no OIDC/SAML configuration, no identity provider federation. User authentication is a custom `POST /user/login` that looks up by email in the database — no password verification, no session management.
- **Gap**: No centralized identity provider. Custom login endpoint has no password verification (queries by email only in `UserMapper.xml`). No SSO.
- **Recommendation**: Deploy Amazon Cognito as the centralized identity provider. Implement proper user registration and authentication flows. Migrate the custom `/user/login` endpoint to Cognito-managed authentication.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray SDK, no OpenTelemetry imports, no tracing instrumentation. No trace ID propagation headers. No `traceparent`, `X-Amzn-Trace-Id`, or correlation ID handling in any controller or service. No Datadog, Jaeger, or Zipkin SDK in `build.gradle`.
- **Gap**: Zero distributed tracing capability. No way to trace requests through the system.
- **Recommendation**: Integrate OpenTelemetry Java auto-instrumentation as part of the Docker image. Configure the ADOT (AWS Distro for OpenTelemetry) collector on EKS. This will automatically trace Spring Boot HTTP requests, JDBC calls, and inter-service communication.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: Logging uses `System.out.println()` in `HealthController.java` and `e.printStackTrace()` across all repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`). No SLF4J/Logback configuration. No JSON log formatters. No correlation IDs. Spring Boot Actuator dependency exists in `build.gradle` but no custom logging configuration.
- **Gap**: No structured logging. Output goes to stdout as unstructured text. Stack traces printed to stderr. No correlation IDs.
- **Recommendation**: Configure Logback with JSON formatter (`logstash-logback-encoder`). Replace all `System.out.println()` and `e.printStackTrace()` with SLF4J logger calls. Add a correlation ID filter that injects trace IDs into every log entry. Configure FluentBit on EKS to ship logs to CloudWatch.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no test datasets, no scoring scripts. No AI or agent components to evaluate. No golden datasets, no A/B test infrastructure.
- **Gap**: No automated evaluation capability.
- **Recommendation**: Establish API contract tests as the first evaluation layer during decomposition. When AI capabilities are added in Phase 3, implement an eval pipeline with golden datasets and scoring.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions. No CloudWatch alarms. No error budget tracking. No latency monitoring. Spring Boot Actuator is in `build.gradle` but no custom health indicators beyond the basic `HealthController.java` (which is a custom implementation, not using Actuator's health endpoint pattern).
- **Gap**: No SLOs defined. No monitoring of availability, latency, or error rates.
- **Recommendation**: Define SLOs for key user journeys (e.g., catalog browse: p99 < 200ms, 99.9% availability; basket operations: p99 < 500ms). Configure CloudWatch alarms on these SLOs. Use Spring Boot Actuator metrics with Prometheus on EKS.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy defined. No blue/green, no canary, no rollback configuration. No feature flags. No CodeDeploy, no Helm releases, no ArgoCD rollback policy. The `bootJar { launchScript() }` in `build.gradle` suggests a bare JAR deployment with no rollback mechanism.
- **Gap**: No rollback capability. Failed deployments would require manual intervention.
- **Recommendation**: Implement Helm-based deployments on EKS with automatic rollback on failed health checks. Configure ArgoCD with automated sync and rollback policies. Add health probes (liveness, readiness) to Kubernetes manifests.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no LLM-related metrics.
- **Gap**: No LLM cost tracking (no LLMs in use).
- **Recommendation**: When AI capabilities are added in Phase 3, implement per-request token tracking with CloudWatch custom metrics. Tag costs by user, feature, and workflow.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom metrics published. No `cloudwatch.put_metric_data` calls. No business KPI dashboards. No tracking of basket operations, user registrations, or catalog views as business metrics.
- **Gap**: No business outcome metrics. Only infrastructure-level metrics (if any) from EC2.
- **Recommendation**: Publish custom CloudWatch metrics for key business events: basket additions/removals, user registrations, catalog page views. Create a business KPI dashboard.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection. No CloudWatch alarms. No PagerDuty/OpsGenie integration. No alerting of any kind. The application has no monitoring beyond the custom `/health/ishealthy` and `/health/dbping` endpoints.
- **Gap**: No anomaly detection or alerting. Failures would go unnoticed until user reports.
- **Recommendation**: Configure CloudWatch anomaly detection on error rates and p99 latency. Set up composite alarms for critical paths. Integrate with PagerDuty or OpsGenie for on-call notification.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy defined. No CodeDeploy configuration, no Helm charts, no ArgoCD manifests, no Argo Rollouts. The `build.gradle` `bootJar { launchScript() }` generates a Linux init script, indicating direct-to-server deployment (likely SCP/SSH to EC2). A commented-out Docker section exists in `build.gradle` (`/* docker { ... } */`) but it was never completed.
- **Gap**: Direct-to-production deployment with no progressive rollout. The commented-out Docker config suggests containerization was considered but abandoned.
- **Recommendation**: Implement GitOps with ArgoCD on EKS. Use Argo Rollouts for canary deployments. Define Helm charts for each microservice with configurable rollout strategies.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test directory exists. No test files of any kind found in the repository. `build.gradle` includes `testImplementation('org.springframework.boot:spring-boot-starter-test')` but no tests were ever written. Zero test coverage.
- **Gap**: Zero test coverage. No unit tests, no integration tests, no contract tests.
- **Recommendation**: Write integration tests for critical API endpoints before decomposition. Use Spring Boot test slices (`@WebMvcTest`, `@DataJpaTest`). Add contract tests (Spring Cloud Contract or Pact) to verify service boundaries during decomposition.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON). No SSM Automation documents. No Lambda-based remediation functions. No self-healing patterns. No incident response workflows of any kind.
- **Gap**: No incident response automation. All incident handling is manual.
- **Recommendation**: Create runbooks for common incidents (database connectivity loss, high latency, OOM). Implement Kubernetes liveness and readiness probes for automatic pod restart. Add SSM Automation documents for infrastructure-level remediation.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO definition files. No observability ownership model. No platform team tooling. No per-service dashboards or alarms.
- **Gap**: No observability governance. No ownership model for service reliability.
- **Recommendation**: Establish a CODEOWNERS file. Define per-service SLOs with named owners. Create a shared responsibility model between platform engineering (EKS cluster, observability stack) and service teams (per-service SLOs, dashboards, alerts).

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | High | High | APP-Q4: 1/4, INF-Q1: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Triggered | High | High | INF-Q1: 1/4, No Dockerfile found | Medium |
| Move to Open Source | Not Triggered | Medium | — | — | — |
| Move to Managed Databases | Triggered | Medium | High | INF-Q2: 1/4, DATA-Q10: 1/4 | Medium |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q5: 1/4, INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Low | Medium | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1 (Infrastructure Foundation)**: Move to Containers + Move to Modern DevOps + Move to Managed Databases — These can execute concurrently. Containerize the monolith, set up Terraform IaC and CI/CD, and migrate to Aurora MySQL simultaneously.

**Parallel Track 2 (Application Decomposition)**: Move to Cloud Native — Begins after Track 1 establishes container infrastructure on EKS. Service extraction requires a working CI/CD pipeline, container registry, and managed database.

**Parallel Track 3 (Future Capabilities)**: Move to AI — Lowest priority for cloud-native-modernization goal. Can begin in Phase 3 after decomposition foundations are established.

**Sequential Dependencies**:
- Move to Containers must complete before Move to Cloud Native (cannot decompose into microservices without container infrastructure)
- Move to Modern DevOps (CI/CD, IaC) should be established before Move to Cloud Native (decomposition requires automated pipelines)
- Move to Managed Databases can run in parallel but should complete before service extraction to avoid managing self-hosted databases during decomposition

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Tightly-coupled monolith with all domains in a single Spring Boot JAR and shared MySQL schema
  - INF-Q1: Score 1/4 — Running on raw EC2 with no container orchestration
  - APP-Q3: Score 1/4 — 100% synchronous communication with no async messaging
  - APP-Q10: Score 1/4 — No async processing capability for long-running operations
- **Current State**: Monolithic Java 8 Spring Boot application deployed as a single JAR on EC2 with 3 MySQL tables in a shared `unishop` schema. Some internal domain separation exists (separate controllers, services, repositories per domain) but all tightly coupled through the shared database.
- **Target State**: Independently deployable microservices on EKS (Catalog, Basket, User) each with their own database, communicating via async events (EventBridge/SQS) and synchronous APIs (API Gateway). Each service has its own Helm chart, CI/CD pipeline, and Kubernetes namespace.
- **Key Activities**:
  1. Conduct domain modeling to identify bounded contexts (Catalog, Basket, User)
  2. Extract User service first (least coupled — `unicorn_user` table only)
  3. Extract Basket service (requires replacing `UnicornMapper.xml` JOIN with API call to Catalog)
  4. Introduce EventBridge for inter-service events (basket updates, catalog changes)
  5. Implement API Gateway with per-service routing
- **Dependencies**: Move to Containers (prerequisite), Move to Modern DevOps (CI/CD needed for each service)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (preparation), Phase 2 (extraction), Phase 3 (optimization)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Containers

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q1: Score 1/4 — Application runs on raw EC2 with `EC2MetadataUtils.getInstanceInfo()` calls
  - No Dockerfile found anywhere in the repository (commented-out Docker config in `build.gradle` was never completed)
- **Current State**: Spring Boot JAR deployed directly on EC2 via `bootJar { launchScript() }`. No containerization. A commented-out Docker section in `build.gradle` suggests containerization was considered but abandoned.
- **Target State**: Multi-stage Dockerfile building from the Gradle bootJar, deployed to EKS with Fargate. ECR repository for image storage. Helm chart for Kubernetes deployment manifests.
- **Key Activities**:
  1. Create a multi-stage Dockerfile (Gradle build → JRE runtime)
  2. Set up Amazon ECR repository
  3. Deploy to EKS with Fargate profiles (per customer preference, avoiding self-managed Kubernetes)
  4. Replace `EC2MetadataUtils` calls with Kubernetes environment variables or downward API
  5. Create Helm chart with liveness/readiness probes pointing to `/health/ishealthy`
- **Dependencies**: None (can start immediately)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Containerize & Automate)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Managed Databases

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q2: Score 1/4 — MySQL database with no IaC. Hardcoded credentials. Unknown management status.
  - DATA-Q10: Score 1/4 — MySQL engine version unknown and unpinned. Connector version 8.0.11 is from 2018.
- **Current State**: MySQL database at `MONO_TO_MICRO_DB_ENDPOINT:3306` with `unishop` schema containing 3 tables. Hardcoded credentials. No IaC. Engine version unknown. Standard CRUD SQL compatible with Aurora MySQL.
- **Target State**: Amazon Aurora MySQL with multi-AZ deployment, automated backups, engine version pinning, and Secrets Manager for credentials. Defined in Terraform with automated failover.
- **Key Activities**:
  1. Create Aurora MySQL cluster in Terraform with engine version pinning
  2. Migrate data using AWS DMS (minimal downtime migration)
  3. Move credentials to AWS Secrets Manager
  4. Update `application.properties` to use Secrets Manager for credentials
  5. Configure automated backups and point-in-time recovery
- **Dependencies**: None (can start immediately, but coordinate with Move to Modern DevOps for Terraform)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Aurora setup), Phase 2 (data migration, database-per-service)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q5: Score 1/4 — Zero IaC files in the entire repository
  - INF-Q6: Score 1/4 — No CI/CD pipeline of any kind
  - OPS-Q9: Score 1/4 — No deployment strategy (manual JAR deployment)
  - OPS-Q10: Score 1/4 — Zero test coverage
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: Manual deployment of JAR to EC2. No IaC. No CI/CD. No tests. No observability. Development and operations are entirely manual.
- **Target State**: Full GitOps workflow: Terraform for infrastructure, GitHub Actions for CI, ArgoCD for CD to EKS. Helm charts for all services. OpenTelemetry for observability. Integration tests in CI pipeline.
- **Key Activities**:
  1. Create Terraform modules for VPC, EKS, Aurora, ECR
  2. Set up GitHub Actions workflow (build → test → Docker → ECR push)
  3. Deploy ArgoCD on EKS for GitOps-based continuous delivery
  4. Create Helm charts for each service
  5. Integrate OpenTelemetry auto-instrumentation
  6. Write integration tests for critical API endpoints
- **Dependencies**: None (should start immediately — prerequisite for all other pathways)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (IaC + CI/CD), Phase 2 (advanced deployment strategies)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: Medium
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks. AWS SDK is legacy v1 (pre-Bedrock).
  - DATA-Q1: Score 1/4 — No vector database
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated eval framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI or agent capabilities. Legacy AWS SDK v1. No vector database or embedding infrastructure.
- **Target State**: AI-augmented services with agent tool definitions per microservice boundary. Spring AI or Strands Agents SDK integrated. Vector store for product search.
- **Key Activities**:
  1. Upgrade AWS SDK to v2 (prerequisite for Bedrock)
  2. Add Spring AI dependency for agent integration
  3. Create semantic product search using Aurora pgvector or OpenSearch
  4. Build agent tools aligned with service boundaries (Catalog tool, Basket tool, User tool)
- **Dependencies**: Move to Cloud Native (service boundaries needed for agent tools), Move to Managed Databases (Aurora needed for pgvector)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 3 (Optimize & Scale)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

The MonoToMicroLegacy application is a tightly-coupled monolith (APP-Q4: 1/4) with shared database schema. Since the goal is `cloud-native-modernization`, a full decomposition strategy is warranted.

### Domain Analysis

Based on the code structure, three bounded contexts are identifiable:

| Domain | Controller | Service | Repository | Tables | Coupling |
|--------|-----------|---------|------------|--------|----------|
| **Catalog** | `UnicornController` | `UnicornService` | `UnicornRepository` + `UnicornMapper` | `unicorns` | Low — read-only catalog data |
| **Basket** | `BasketController` + `DataReplicationController` | `UnicornService` (shared!) | `UnicornRepository` + `UnicornMapper` | `unicorns_basket` | **High** — shares `UnicornService` and JOINs `unicorns` table |
| **User** | `UserController` | `UserService` | `UserRepository` + `UserMapper` | `unicorn_user` | **Low** — independent table, no JOINs with other domains |

**Key Coupling Point**: The `getUnicornBasket` query in `UnicornMapper.xml` performs a `JOIN unishop.unicorns u ON u.uuid = ub.unicornUuid` — this is the primary data-level coupling that must be resolved during decomposition.

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure while incrementally extracting services
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract the **User service** first — it has the clearest domain boundary (`unicorn_user` table, `UserController`, `UserService`, `UserMapper`), no JOINs with other tables, and can be independently deployed with zero impact on the Catalog or Basket domains.
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently, containerize modular components as-is, refactor tightly-coupled ones
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Containerize the monolith as-is first (get it on EKS), then extract User service, then tackle the coupled Catalog-Basket boundary
- **When to Use**: When the immediate priority is getting onto EKS/Fargate before any code changes

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

### Pattern Recommendations Based on Your Architecture

**Incremental Extraction**:
- Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (path-based routing)
- **Why**: The User service can be extracted by routing `/user/*` to the new service and everything else to the monolith. API Gateway (or EKS Ingress) provides routing, throttling, and auth without requiring a service mesh upfront.

**Data Consistency**:
- Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extracting the Basket service
- **Why**: Without idempotency (APP-Q7: 1/4), the Basket service extraction risks data inconsistency. The `getUnicornBasket` JOIN must be replaced with an API call + local cache, and the anti-corruption layer ensures the new Basket service contract doesn't leak monolith internals.

**Resilience First**:
- Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition
- **Why**: Microservices amplify failure modes. The current codebase has zero resilience patterns (APP-Q9: 1/4) — all exception handling uses bare `e.printStackTrace()`. Resilience patterns must be in place before increasing system distribution.

### Recommended Extraction Order

1. **User Service** (Low risk, low coupling)
   - Extract `UserController`, `UserService`, `UserMapper`, `unicorn_user` table
   - Route `/user/*` to new service via API Gateway/Ingress
   - New service gets its own Aurora MySQL database (or shared cluster, separate schema)

2. **Catalog Service** (Low risk, read-heavy)
   - Extract `UnicornController`, `UnicornService` (read-only catalog operations), `UnicornMapper` (catalog queries), `unicorns` table
   - Route `/unicorns` (GET) to new service
   - Catalog data is read-only from the application's perspective

3. **Basket Service** (Medium risk, requires JOIN resolution)
   - Extract `BasketController`, basket-related operations from `UnicornService`, `unicorns_basket` table
   - Replace `getUnicornBasket` JOIN with API call to Catalog Service
   - Introduce event-driven sync for denormalized product data in the Basket service

---

## Readiness Roadmap

### Phase 1 — Containerize & Automate (Days 1–30)

Low-effort, high-impact actions that establish the foundation for decomposition:

1. **Create Dockerfile** — Multi-stage Dockerfile using Gradle to build the bootJar and JRE 17 as runtime. Replace the existing Java 8 base with a modern JRE. Remove the `EC2MetadataUtils` dependency in `HealthController.java` (replace with environment variables).
2. **Set up ECR and EKS** — Create Terraform modules for VPC (public/private subnets), EKS cluster with Fargate profiles, and ECR repository. Use EKS Auto Mode or Fargate to avoid self-managed Kubernetes (per customer preference).
3. **Create Helm chart** — Define Kubernetes deployment, service, and ingress for the monolith. Configure liveness probe on `/health/ishealthy` and readiness probe on `/health/dbping`. Mount secrets from Secrets Manager via external-secrets-operator.
4. **Implement CI pipeline** — GitHub Actions workflow: checkout → Gradle build → Docker build → ECR push. Include basic linting and compilation checks.
5. **Move secrets to Secrets Manager** — Migrate hardcoded database credentials (`MonoToMicroUser`/`MonoToMicroPassword`) from `application.properties` to AWS Secrets Manager. Update Spring Boot config to read from Secrets Manager or Kubernetes secrets.
6. **Create Aurora MySQL cluster** — Define Aurora MySQL in Terraform with engine version pinning, multi-AZ, automated backups. Migrate data from existing MySQL using DMS.
7. **Conduct domain modeling workshop** — Identify bounded contexts (Catalog, Basket, User). Map current module dependencies and data coupling using the domain analysis in the decomposition section. Identify the User service as the first extraction candidate.
8. **Add structured logging** — Replace `System.out.println()` and `e.printStackTrace()` with SLF4J/Logback JSON output. Add correlation ID filter.

### Phase 2 — Decompose & Decouple (Months 1–3)

Structural improvements that enable independent service deployment:

1. **Deploy ArgoCD for GitOps** — Install ArgoCD on EKS. Configure GitOps repo structure with per-service Helm charts. Set up automated sync and rollback policies.
2. **Extract User Service** — Using the Strangler Fig pattern, extract `UserController`, `UserService`, `UserMapper`, and `unicorn_user` table into a separate Spring Boot 3.x application. Deploy as an independent Kubernetes deployment. Route `/user/*` to the new service via Ingress path-based routing.
3. **Implement API Gateway** — Deploy AWS ALB Ingress Controller or Amazon API Gateway with path-based routing to direct traffic to the monolith and extracted services. Configure throttling, rate limiting, and JWT authentication.
4. **Add integration tests** — Write API-level integration tests for critical endpoints (`GET /unicorns`, `POST /unicorns/basket`, `POST /user`). Add contract tests between the User service and the monolith.
5. **Extract Catalog Service** — Extract `UnicornController` and catalog-related `UnicornService` operations into a read-only Catalog service with its own database (or schema).
6. **Implement resilience patterns** — Add Resilience4j with circuit breaker, retry, and timeout for all inter-service HTTP calls. Configure per-service health checks and Kubernetes probes.
7. **Add OpenTelemetry** — Integrate ADOT auto-instrumentation for distributed tracing across all services. Configure FluentBit for centralized log aggregation to CloudWatch.
8. **Configure Kubernetes HPA** — Set up Horizontal Pod Autoscaler for each service based on CPU/memory metrics. Use Karpenter for cluster-level auto-scaling.

### Phase 3 — Optimize & Scale (Months 3–6)

Advanced capabilities that optimize the cloud-native architecture:

1. **Extract Basket Service** — The most complex extraction: replace the `getUnicornBasket` JOIN in `UnicornMapper.xml` with an API call to the Catalog service. Implement an anti-corruption layer. Introduce EventBridge for catalog change notifications to the Basket service (denormalized product data).
2. **Implement database-per-service** — Each service gets its own Aurora MySQL schema (or separate cluster). Use DMS for data migration. Implement the transactional outbox pattern for cross-service data consistency.
3. **Implement canary deployments** — Configure Argo Rollouts for canary deployments with automated rollback based on error rate and latency SLOs.
4. **Define and monitor SLOs** — Establish SLOs for all services (availability, latency, error rate). Configure CloudWatch dashboards and anomaly detection alarms. Set up error budget tracking.
5. **Add API versioning** — Implement URL-based versioning (`/v1/unicorns`) across all services via API Gateway. Establish backward compatibility policy.
6. **Implement Cognito authentication** — Deploy Amazon Cognito user pool. Migrate the custom `/user/login` endpoint to Cognito-managed authentication. Configure JWT validation at the API Gateway and per-service level.
7. **Explore AI integration** — Upgrade to AWS SDK v2. Evaluate Spring AI for product search enhancement (semantic search using Aurora pgvector). Build initial agent tools aligned with service boundaries.
8. **Continue service extraction** — Based on business priorities, extract additional services or refine existing service boundaries. Implement domain events for loose coupling.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless)**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

**Module 6: Move to Modern DevOps**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

**Module 7: Move to AI**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2

---

## Appendix: Evidence Index

| # | File | Key Finding |
|---|------|-------------|
| 1 | `build.gradle` | Spring Boot 2.1.0, Java 8, MySQL connector 8.0.11, AWS SDK 1.11.567, Spring Security OAuth2, MyBatis, commented-out Docker config |
| 2 | `src/main/resources/application.properties` | Hardcoded DB credentials, MySQL JDBC URL with env var endpoint, port 8080 |
| 3 | `database/create_tables.sql` | 3 tables (unicorns, unicorns_basket, unicorn_user) in `unishop` schema, InnoDB engine, no stored procedures |
| 4 | `src/main/java/com/monoToMicro/Application.java` | @SpringBootApplication entry point, CORS allow-all, WebSecurity ignores OPTIONS |
| 5 | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | EC2MetadataUtils.getInstanceInfo() confirming EC2 deployment, System.out.println logging |
| 6 | `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | GET /unicorns endpoint, synchronous ResponseEntity, @PreAuthorize("permitAll()") |
| 7 | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | POST/DELETE/GET basket endpoints, synchronous, no idempotency keys |
| 8 | `src/main/java/com/monoToMicro/rest/controller/UserController.java` | POST /user and /user/login, no password verification in login |
| 9 | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | GET /data endpoint, getAllBaskets() full table scan |
| 10 | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | @EnableResourceServer but anyRequest().permitAll() — auth framework present but disabled |
| 11 | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | CRUD operations, constructor injection, no resilience patterns |
| 12 | `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | User create with UUID generation, getByEmail, no password handling |
| 13 | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | @Repository @Transactional, e.printStackTrace() error handling, returns null on error |
| 14 | `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | synchronized create() method, e.printStackTrace() error handling |
| 15 | `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | INSERT IGNORE, JOIN between unicorns and unicorns_basket (key coupling point), getAllBaskets resultMap |
| 16 | `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | insert ignore into unicorn_user, getByEmail query |
| 17 | `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | Centralized MyBatis configuration, all 3 mappers registered |
| 18 | `src/main/java/com/monoToMicro/config/MVCConfig.java` | CORS allow all origins and all methods |
| 19 | `src/main/java/com/monoToMicro/core/model/Unicorn.java` | @JsonInclude(NON_NULL), domain model with uuid, name, description, price, image |
| 20 | `gradle/wrapper/gradle-wrapper.properties` | Gradle 7.4 distribution |
