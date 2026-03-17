# Agentic Readiness Assessment Report
**Target**: MonoToMicroLegacy (Unishop E-Commerce Application)
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

This Unishop e-commerce monolith is a legacy Java 8 Spring Boot application running directly on EC2 with a MySQL database, and it is **far from ready** to support an AI agent for order status inquiries, returns processing, and inventory restocking. The application scores **1.3 / 4.0 overall** — indicating fundamental gaps across all five assessment dimensions. The strongest area is Data Foundations (1.8/4.0), thanks to a clean data access layer using the repository pattern, a single MySQL data source without stored procedures, and structured JSON API responses. However, the application has **zero infrastructure-as-code, zero CI/CD automation, zero API documentation, zero security enforcement, zero observability, and zero AI/agent capabilities**. Every prerequisite for building the targeted customer support agent — documented APIs for tool invocation, secure credential management for agent auth, and a vector database for RAG-powered knowledge retrieval — is completely absent. Significant modernization is required before the order/returns/inventory agent can be safely deployed.

### Overall Score: 1.3 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.1 / 4.0 | ❌ |
| Application Architecture | 1.4 / 4.0 | ❌ |
| Data Foundations | 1.8 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.0 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

**1. APP-Q2 — API Documentation (Score: 1/4 ❌)**
No OpenAPI or Swagger specifications exist for any of the REST endpoints (`/unicorns`, `/unicorns/basket`, `/user`, `/health`, `/data`). **Why this blocks the agent**: The order/returns/inventory agent needs machine-readable API descriptions to discover and invoke endpoints as tools. Without OpenAPI specs, the agent cannot know what parameters to pass or what responses to expect. **First step**: Generate OpenAPI 3.0 specs from the existing Spring Boot controllers using Springdoc OpenAPI or manually document all endpoints.

**2. APP-Q13 — AI/Agent Frameworks (Score: 1/4 ❌)**
No AI or agent frameworks are present. The `build.gradle` includes only AWS SDK v1 (1.11.567) with no Bedrock, LangChain, Strands Agents, or any agent SDK imports. **Why this blocks the agent**: There is no foundation to build the customer support agent — no LLM integration, no tool-use framework, no agent orchestration layer. **First step**: Add Amazon Bedrock SDK (AWS SDK v2) and Strands Agents SDK to the project dependencies; create a proof-of-concept agent that can answer basic product catalog queries.

**3. DATA-Q1 — Vector Database Presence (Score: 1/4 ❌)**
No vector database is configured. No OpenSearch, pgvector, Pinecone, or Bedrock Knowledge Base references found. **Why this blocks the agent**: The returns/inventory agent needs semantic search over product catalogs, order histories, and return policies to provide accurate answers. Without a vector store, RAG-powered knowledge retrieval is impossible. **First step**: Provision Amazon OpenSearch Service with the k-NN plugin or configure a Bedrock Knowledge Base backed by Amazon S3 for product and policy documentation.

**4. DATA-Q3 — RAG Implementation (Score: 1/4 ❌)**
No RAG pipeline exists — no embedding model calls, no document chunking, no similarity search patterns. **Why this blocks the agent**: The agent handling order status inquiries and return processing needs to retrieve relevant context from order history, product specs, and return policies. Without RAG, agent responses will lack grounding. **First step**: Build a document ingestion pipeline that chunks product/order documentation into embeddings stored in the vector database, and integrate semantic retrieval into the agent's tool chain.

**5. SEC-Q1 — Secret Management (Score: 1/4 ❌)**
Database credentials are hardcoded in plaintext in `application.properties` (`MonoToMicroUser`/`MonoToMicroPassword`). No AWS Secrets Manager, no HashiCorp Vault, no secure credential management. **Why this blocks the agent**: An agent that connects to order and inventory databases with hardcoded credentials creates a critical security exposure — agent-generated queries could leak credentials in logs or error messages. **First step**: Migrate database credentials to AWS Secrets Manager and update `application.properties` to use `${sm://...}` or environment-variable-based injection from Secrets Manager.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: The application runs on raw EC2 instances. `HealthController.java` directly uses `com.amazonaws.util.EC2MetadataUtils` to retrieve `InstanceInfo` including `accountId`, `availabilityZone`, `instanceId`, and `instanceType` — confirming EC2-based deployment. No Dockerfile, no ECS task definitions, no EKS manifests, no container orchestration of any kind found in the repository.
- **Gap**: 100% of compute is raw EC2. No managed container orchestration (ECS/EKS) or containerization.
- **Recommendation**: Create a Dockerfile for the Spring Boot application, define Terraform modules for an ECS Fargate cluster, and deploy the monolith as a containerized service on ECS behind an ALB. Per preferences, use ECS Fargate (avoid Lambda/serverless).

#### INF-Q2: Databases
- **Score**: 2/4 🟠
- **Finding**: `application.properties` configures JDBC connection to MySQL at `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The DB endpoint is injected via environment variable `MONO_TO_MICRO_DB_ENDPOINT`, which could point to RDS or a self-managed MySQL instance. No IaC files exist to confirm whether this is RDS or self-managed. The `mysql-connector-java:8.0.11` dependency is specified in `build.gradle`. Credentials are hardcoded (`MonoToMicroUser`/`MonoToMicroPassword`). The `create_tables.sql` uses `ENGINE=InnoDB` — standard MySQL.
- **Gap**: No IaC confirming managed database status. Credentials are hardcoded rather than managed. No evidence of automated failover or backup configuration.
- **Recommendation**: Define the MySQL database as an Amazon RDS for MySQL instance (or Amazon Aurora MySQL) in Terraform with Multi-AZ deployment, automated backups, and Secrets Manager integration for credentials. Per preferences, consider migrating the basket data to DynamoDB for the shopping cart use case.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service found. No Step Functions (`aws_sfn_*`), no Temporal SDK, no Camunda, no workflow YAML definitions. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` is simple CRUD — no complex multi-step workflows.
- **Gap**: No orchestration service for multi-step agent workflows such as processing returns (validate → approve → refund → update inventory).
- **Recommendation**: Implement AWS Step Functions for the returns processing workflow. Define states for return validation, approval routing, refund processing, and inventory update — these will become agent-invokable tools. Per preferences, use EventBridge for event-driven triggers.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No messaging infrastructure found. No SQS, SNS, EventBridge, or MSK references in any file. All communication is synchronous HTTP request/response. No event-driven patterns in the codebase.
- **Gap**: No async messaging for decoupling operations. Agent-initiated inventory restocking and return processing events have no event bus.
- **Recommendation**: Introduce Amazon SQS for order processing queues, Amazon SNS for notifications (return status updates), and Amazon EventBridge for event-driven inventory restocking triggers. Per preferences, prioritize SQS, SNS, and EventBridge.

#### INF-Q5: Infrastructure as Code
- **Score**: 1/4 ❌
- **Finding**: Zero IaC files found in the repository. No `.tf` files, no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize manifests. All infrastructure appears to be manually provisioned.
- **Gap**: 0% of infrastructure is defined in IaC. No reproducibility, no audit trail, no automated provisioning.
- **Recommendation**: Create a Terraform project to define all infrastructure: VPC, subnets, security groups, RDS instance, ECS cluster, ALB, and associated IAM roles. Per preferences, use Terraform with a GitOps workflow (e.g., Atlantis or GitHub Actions-based Terraform apply).

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/`, no `Jenkinsfile`, no `buildspec.yml`, no `.gitlab-ci.yml`. Only a Gradle build wrapper (`gradlew`) for local builds.
- **Gap**: No automated build, test, or deploy pipeline. Deployments are presumably manual.
- **Recommendation**: Create a CI/CD pipeline using GitHub Actions (or AWS CodePipeline) with stages for build (`gradle build`), test, Docker image build/push to ECR, and deploy to ECS. Per preferences, implement GitOps with Helm charts for deployment management.

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: The application exposes HTTP directly via Spring Boot embedded Tomcat on port 8080 (`server.port=8080` in `application.properties`). No API Gateway, no ALB, no CloudFront distribution defined. No throttling, no request validation, no auth at the gateway level.
- **Gap**: No managed API entry point. Direct service exposure without throttling or gateway-level security.
- **Recommendation**: Deploy Amazon API Gateway in front of the ECS service with throttling, request validation, and API key management. The API Gateway will serve as the agent's entry point for tool invocation. Per preferences, use API Gateway (REST API type).

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No streaming infrastructure found. No Kinesis, no MSK, no Kafka, no stream consumer patterns in the codebase.
- **Gap**: No real-time streaming for inventory change events or order status updates that the agent could subscribe to.
- **Recommendation**: Evaluate Amazon EventBridge for event-driven inventory updates. If high-throughput streaming is needed for order analytics, consider Amazon Kinesis Data Streams. Per preferences, use EventBridge for event routing.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions found. No IaC exists at all. The application's network security posture is unknown from the repository.
- **Gap**: No evidence of network segmentation, private subnets, or security groups. No least-privilege network access controls.
- **Recommendation**: Define a VPC in Terraform with public subnets (for ALB), private subnets (for ECS tasks and RDS), security groups restricting traffic to minimum required ports, and NACLs for additional defense-in-depth.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No auto-scaling configuration found. No ASGs, no ECS Service auto-scaling, no scaling policies. The application runs on a single EC2 instance with no scaling capability.
- **Gap**: No auto-scaling for handling variable agent-driven load. The agent could generate bursts of API calls that overwhelm a single instance.
- **Recommendation**: Configure ECS Service Auto Scaling with target tracking policies based on CPU utilization and request count. Define minimum (2) and maximum capacity limits in Terraform.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`) with Spring Boot 2.1.x (`springBootVersion = '2.1.0.RELEASE'`). Java has a mature ecosystem but Java 8 is EOL and the agent framework ecosystem (LangChain, Strands Agents) is strongest in Python and TypeScript.
- **Gap**: Java 8 is end-of-life. Spring Boot 2.1.x is also EOL. The agent SDK ecosystem in Java (Spring AI) is maturing but lags behind Python.
- **Recommendation**: Upgrade to Java 17+ and Spring Boot 3.x as a prerequisite. Consider implementing the agent layer as a separate Python or TypeScript service using Strands Agents SDK, communicating with the Java backend via API Gateway.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specs found. No `swagger.json`, `openapi.yaml`, or API documentation annotations (`@ApiOperation`, `@OpenAPIDefinition`) in any controller. REST controllers exist: `UnicornController` (`/unicorns`), `BasketController` (`/unicorns/basket`), `UserController` (`/user`), `HealthController` (`/health`), `DataReplicationController` (`/data`) — all undocumented.
- **Gap**: Zero API documentation. Agents cannot discover or invoke APIs without machine-readable specs.
- **Recommendation**: Add `springdoc-openapi-ui` dependency to `build.gradle` and annotate controllers with OpenAPI annotations. Generate an `openapi.yaml` spec that the agent can consume for tool definitions.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous. Controllers call services synchronously (`unicornService.getUnicorns()`), services call repositories synchronously (`unicornRepository.getUnicorns()`). No message queues, no event handlers, no `@Async` annotations, no CompletableFuture patterns.
- **Gap**: 0% async communication. All operations are blocking HTTP request/response.
- **Recommendation**: Introduce SQS-backed async processing for write operations (basket updates, user creation). Use EventBridge for inventory restocking events triggered by the agent. Keep read operations synchronous for low latency.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single Spring Boot application with one `build.gradle` and one deployable JAR. All domain logic (unicorns/products, baskets/orders, users, health) shares a single MySQL database (`unishop`). However, there IS internal structure: separate controller/service/repository layers per domain — `UnicornController`→`UnicornService`→`UnicornRepository`, `UserController`→`UserService`→`UserRepository`, `HealthController`→`HealthService`→`HealthRepository`. Coupling is moderate — domains share the same database with no cross-domain foreign keys (baskets reference unicorns by UUID, not FK).
- **Gap**: Single deployable unit. All domains share one database. No independent service boundaries for agent tool isolation.
- **Recommendation**: See the Move to Cloud Native pathway. The existing layered structure provides a good foundation for eventual service extraction. Containerize the monolith first on ECS, then incrementally extract services.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: Spring Boot returns JSON by default. Models use `@JsonInclude(JsonInclude.Include.NON_NULL)` annotations (`Unicorn.java`, `User.java`). Controllers return `ResponseEntity<Unicorn>`, `ResponseEntity<Collection<Unicorn>>`, `ResponseEntity<UnicornBasket>`, `ResponseEntity<User>` — all serialized as JSON.
- **Gap**: JSON responses are present but no explicit content-type enforcement or response envelope pattern (no standard error response format).
- **Recommendation**: Standardize response format with a consistent envelope (e.g., `{ data: ..., errors: [...], meta: {...} }`) to make agent parsing more reliable.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration. Business logic in `UnicornServiceImpl` and `UserServiceImpl` is simple CRUD operations. No state machines, no saga patterns, no Step Functions definitions. The `DataReplicationController` has a basic `replicate()` method with no orchestration.
- **Gap**: No orchestrated workflows for complex operations like returns processing or inventory restocking.
- **Recommendation**: Implement AWS Step Functions for multi-step workflows: returns processing (validate → approve → refund → notify), inventory restocking (check threshold → create PO → confirm), and order fulfillment. These become agent-invokable workflows.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No explicit idempotency keys in the API layer. `UnicornMapper.xml` uses `INSERT IGNORE` for basket additions, which provides basic DB-level deduplication but is not API-level idempotency. `UserMapper.xml` also uses `insert ignore` for user creation. No `Idempotency-Key` header handling in any controller.
- **Gap**: No API-level idempotency keys. Agent retries could create duplicate records or inconsistent state.
- **Recommendation**: Implement idempotency key support for POST/DELETE endpoints on the basket and user controllers. Store idempotency keys in a DynamoDB table with TTL for deduplication.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. `ResourceServerConfig.java` permits all requests (`authorizeRequests().anyRequest().permitAll()`). No API Gateway throttling, no WAF rules, no application-level rate limiting middleware.
- **Gap**: No rate limiting. An agent in a feedback loop could overwhelm the application with unlimited requests.
- **Recommendation**: Deploy API Gateway with usage plans and throttling (burst/rate limits per API key). The agent should have its own API key with appropriate rate limits.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry logic, or timeout configurations. No Resilience4j, Hystrix, or retry decorators. Repository methods (`UnicornRepositoryImpl`, `UserRepositoryImpl`) catch exceptions with `e.printStackTrace()` and return `null` — no retry, no fallback, no timeout handling.
- **Gap**: No resilience patterns. Database failures silently return nulls. No circuit breaking or retry with backoff.
- **Recommendation**: Add Resilience4j for circuit breaker and retry patterns on database calls. Configure timeouts on all external calls. Replace `e.printStackTrace()` with structured error handling and fallback responses.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: All operations appear to be short-lived CRUD operations (product listing, basket add/remove, user creation/login). No background job frameworks (Celery, Bull, SQS workers), no async/polling patterns, no job status APIs. However, current operations are likely under 30 seconds.
- **Gap**: No async infrastructure exists for future long-running operations like bulk inventory restocking or batch return processing that the agent might trigger.
- **Recommendation**: Implement SQS-based async job processing for operations that could exceed 30 seconds (bulk inventory updates, report generation). Return a job ID and provide a status polling endpoint for the agent to check completion.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning. Endpoints are `/unicorns`, `/unicorns/basket/{userUuid}`, `/user`, `/user/login`, `/health/ping`, `/health/ishealthy`, `/health/dbping`, `/data`. No `/v1/` prefix, no version headers, no versioning strategy.
- **Gap**: No versioning strategy. Breaking API changes will disrupt the agent's tool definitions.
- **Recommendation**: Introduce URL path versioning (`/v1/unicorns`, `/v1/user`) and maintain backward compatibility. Configure API Gateway to route versioned paths.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith with no inter-service communication. The database endpoint is provided via environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) — basic but not service discovery. No AWS Cloud Map, no App Mesh, no Consul.
- **Gap**: No service discovery mechanism. As services are extracted, hard-coded endpoints will become a maintenance burden.
- **Recommendation**: Implement AWS Cloud Map for service discovery when extracting microservices. Use ECS Service Connect for service-to-service communication within the ECS cluster.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent frameworks present. `build.gradle` includes AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567`) but no Bedrock SDK, no LangChain, no Strands Agents, no OpenAI, no Spring AI imports. No MCP SDK references.
- **Gap**: Zero AI/agent capability. No foundation for the order/returns/inventory agent.
- **Recommendation**: Implement the agent layer using Strands Agents SDK (Python) or Spring AI (Java). Integrate with Amazon Bedrock for LLM capabilities. Define tools for each API endpoint (get orders, process return, check inventory). Start with a simple read-only agent that queries the product catalog and basket data.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch with k-NN, no Aurora pgvector, no Bedrock Knowledge Base, no Pinecone/Weaviate/Chroma imports in `build.gradle` or any source file.
- **Gap**: No vector store for semantic search over order data, product catalogs, or return policies.
- **Recommendation**: Provision Amazon OpenSearch Service with the k-NN plugin for product semantic search, or use Amazon Bedrock Knowledge Bases with S3 as the document source for return policies and product documentation.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists, so management is not applicable. No managed or self-hosted vector DB.
- **Gap**: No vector DB to manage.
- **Recommendation**: When provisioning the vector store (see DATA-Q1), use a fully managed service — Amazon OpenSearch Service or Bedrock Knowledge Bases — to eliminate operational burden.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline found. No embedding model calls (Bedrock Titan, OpenAI ada), no document chunking/splitting code, no similarity search patterns, no Bedrock Knowledge Base integration.
- **Gap**: No RAG capability. The agent cannot retrieve contextual information from product documentation, order histories, or return policies.
- **Recommendation**: Build a RAG pipeline: ingest product descriptions and return policies into embeddings using Amazon Bedrock Titan Embeddings, store in OpenSearch or Bedrock Knowledge Base, and integrate retrieval into the agent's reasoning loop.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Single MySQL database (`unishop`) with 3 tables: `unicorns`, `unicorns_basket`, `unicorn_user`. One JDBC connection configured in `application.properties`. `build.gradle` includes `aws-java-sdk-s3` but no S3 operations were found in the source code.
- **Gap**: Only one data source, which is favorable. However, as the agent use case expands, additional data sources (vector DB, order history service) will need unified access.
- **Recommendation**: Maintain the single-source advantage. When adding vector DB and other data sources for the agent, create a unified data access layer or API abstraction.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Data is accessed through a layered pattern: Controllers → Services → Repositories → MyBatis Mappers → MySQL. The repository pattern (`UnicornRepository`/`UnicornRepositoryImpl`, `UserRepository`/`UserRepositoryImpl`) provides a data access layer. However, this is direct DB access via JDBC, not API-based access.
- **Gap**: Agent code would need to access data via APIs, not direct DB connections. Currently the repositories are tightly coupled to MyBatis/MySQL.
- **Recommendation**: Expose data through REST APIs (already partially done) and ensure the agent interacts only through the API layer, never directly with the database. Add API endpoints for order lookup, return status, and inventory levels.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` includes `aws-java-sdk-s3:1.11.567` but no S3 operations, no document parsing, no Textract calls found in any source file. The `image` field in `unicorns` table stores only image name strings, not actual files.
- **Gap**: No unstructured data pipeline. Return documentation, policy PDFs, and product images are not processed.
- **Recommendation**: Store return policies and product documentation in S3. Implement a document processing pipeline using Amazon Textract for OCR if needed, and feed processed text into the RAG pipeline.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `create_tables.sql` provides the schema definition for all 3 tables (`unicorns`, `unicorns_basket`, `unicorn_user`) with column types and constraints. MyBatis XML mappers (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) document all SQL queries. No formal schema versioning tool (Flyway, Liquibase, Alembic) or schema registry.
- **Gap**: Schema is documented in SQL files but not versioned with a migration tool. No schema registry for the agent to discover data models.
- **Recommendation**: Implement Flyway or Liquibase for schema migration versioning. Generate JSON Schema definitions from the data models for the agent to understand data structure.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Repository pattern is used consistently. `UnicornRepository`/`UnicornRepositoryImpl` and `UserRepository`/`UserRepositoryImpl` provide a unified data access layer. `MyBatisConfig.java` centralizes SqlSessionFactory configuration and mapper bean registration. All database access goes through this layer.
- **Gap**: The data access layer exists but is coupled to a single database. No abstraction for multiple data sources.
- **Recommendation**: Maintain the existing repository pattern. When adding DynamoDB for basket data (per preferences), create a new repository implementation behind the same interface.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist, so no freshness mechanism is applicable. No CDC patterns, no event-driven refresh, no scheduled re-indexing.
- **Gap**: No embedding update pipeline. When RAG is implemented, there will be no mechanism to keep embeddings current with product/order changes.
- **Recommendation**: Implement EventBridge-triggered embedding refresh when product catalog or return policies change. Use DynamoDB Streams or MySQL CDC (via AWS DMS) to detect data changes and trigger re-indexing.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` specifies `mysql-connector-java:8.0.11` (released 2018). No IaC exists to specify the MySQL server engine version. The connector version 8.0.11 is severely outdated (current is 8.0.35+). No explicit engine version pinning in any configuration.
- **Gap**: MySQL connector is from 2018. Server engine version is unknown and unpinned. Potential security vulnerabilities in outdated connector.
- **Recommendation**: Update `mysql-connector-java` to the latest 8.0.x version. When defining RDS in Terraform, explicitly pin the MySQL engine version (e.g., `8.0.35`) and enable auto minor version upgrades. Per preferences, define this in Terraform.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: `create_tables.sql` contains only `CREATE SCHEMA`, `CREATE TABLE`, and `INSERT` statements. No stored procedures, no triggers, no functions. MyBatis mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) use standard SQL only: `SELECT`, `INSERT IGNORE`, `DELETE`, `JOIN`. No proprietary SQL constructs, no PL/SQL, no T-SQL.
- **Gap**: None. All business logic is in the application layer.
- **Recommendation**: Maintain this clean separation. Continue keeping business logic in the application layer, which makes database migration straightforward.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. The DB endpoint uses an environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) but credentials are plaintext. No Secrets Manager, no Vault, no encrypted credential storage.
- **Gap**: Hardcoded credentials in configuration files. Critical security risk, especially when agents access the database.
- **Recommendation**: Migrate all credentials to AWS Secrets Manager. Use Spring Cloud AWS Secrets Manager integration to inject credentials at runtime. Define the secret in Terraform.

#### SEC-Q2: IAM Least Privilege
- **Score**: 1/4 ❌
- **Finding**: No IAM policies defined in any IaC. `build.gradle` includes the full AWS SDK (`aws-java-sdk:1.11.567`) which implies broad AWS API access but no IAM roles or policies are configured. No IaC exists to define per-service roles.
- **Gap**: No IAM policies defined. No least-privilege enforcement. Unknown what AWS permissions the application has.
- **Recommendation**: Define IAM task roles in Terraform for the ECS service with minimum required permissions (S3 read for specific buckets, Secrets Manager read for specific secrets). Define a separate IAM role for the agent with scoped permissions.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: `ResourceServerConfig.java` configures OAuth2 resource server (`@EnableResourceServer`) but permits all requests (`authorizeRequests().anyRequest().permitAll()`). Spring Security OAuth2 and JWT dependencies are present in `build.gradle` but are configured in fully permissive mode. No JWT validation, no token exchange, no user identity propagation.
- **Gap**: OAuth2 scaffolding exists but is completely disabled. No user identity propagation end-to-end.
- **Recommendation**: Enable JWT validation in `ResourceServerConfig`. Integrate with Amazon Cognito as the identity provider. Propagate user identity through JWT tokens so the agent's actions are attributed to the correct user.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration. No audit logging infrastructure. No structured logging of any kind. `HealthController.java` uses `System.out.println()` for log output.
- **Gap**: No audit trail for API calls or data access. Agent actions cannot be traced or audited.
- **Recommendation**: Enable CloudTrail for API-level auditing. Implement application-level audit logging for all data mutations (basket changes, user creation) with user context, action, and timestamp. Store audit logs in CloudWatch with appropriate retention.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. No API Gateway, no WAF, no application-level rate limiting middleware. `ResourceServerConfig.java` permits all requests without throttling.
- **Gap**: No rate limiting. The agent could be exploited or enter a loop that generates unlimited API calls.
- **Recommendation**: Deploy API Gateway with usage plans specifying burst/rate limits. Create separate API keys for the agent and human users. Configure WAF rules for additional protection.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction in logging. Repository classes (`UnicornRepositoryImpl`, `UserRepositoryImpl`) use `e.printStackTrace()` which could leak SQL statements containing user data. The `User` model contains PII fields: `email`, `firstName`, `lastName`. No log scrubbing, no PII masking.
- **Gap**: PII (email, names) could be exposed in exception stack traces and logs. No automated PII detection or redaction.
- **Recommendation**: Replace `e.printStackTrace()` with a structured logging framework (SLF4J + Logback). Implement log scrubbing middleware that masks PII fields. Consider enabling Amazon Macie for S3-based data classification.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows found. No Step Functions with approval tasks, no approval API endpoints, no manual approval gates in any pipeline.
- **Gap**: No human-in-the-loop for high-risk agent actions like processing refunds or bulk inventory changes.
- **Recommendation**: Implement Step Functions with `waitForTaskToken` for human approval of high-risk actions: return refunds over a threshold, bulk inventory modifications, and account deletions. The agent should trigger the workflow and pause for human approval.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS configuration found. No encryption configuration on data stores. No IaC defining encryption. The `build.gradle` does not include any KMS SDK references for application-level encryption.
- **Gap**: No evidence of encryption at rest for the database, logs, or any data store.
- **Recommendation**: Enable encryption at rest for RDS using AWS-managed or customer-managed KMS keys. Enable S3 bucket encryption for any future document storage. Define KMS keys in Terraform.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: OAuth2 resource server is configured in `ResourceServerConfig.java` but set to `permitAll()` — effectively no authentication enforced. All controller methods use `@PreAuthorize("permitAll()")`. The `/user/login` endpoint in `UserController.java` accepts a user object but performs no credential validation — it simply looks up by email.
- **Gap**: Zero authentication enforced on any endpoint. Any caller can access any endpoint without credentials.
- **Recommendation**: Enable JWT-based authentication via Amazon Cognito. Configure API Gateway with a Cognito authorizer. Issue the agent a service-to-service credential (OAuth2 client credentials grant) for API access.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: OAuth2 dependencies present in `build.gradle` (`spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`) but no identity provider is configured. No Cognito, no Okta, no OIDC/SAML configuration. The `/user/login` endpoint is a simple email lookup with no authentication.
- **Gap**: No centralized identity provider. No SSO. No federated identity.
- **Recommendation**: Deploy Amazon Cognito user pool as the centralized identity provider. Configure OIDC-based authentication for the Spring Boot application. Use Cognito machine-to-machine tokens for agent authentication.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing. No X-Ray, no OpenTelemetry, no Datadog/Jaeger/Zipkin SDK. `build.gradle` includes `spring-boot-starter-actuator` but no tracing configuration. No trace ID propagation in HTTP headers.
- **Gap**: No end-to-end tracing. Agent workflows spanning multiple tool invocations cannot be traced.
- **Recommendation**: Add AWS X-Ray SDK or OpenTelemetry Java agent for distributed tracing. Configure trace ID propagation in all HTTP requests. This is critical for debugging agent workflows that chain multiple API calls.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: No structured logging. `HealthController.java` uses `System.out.println()` for output. `UnicornRepositoryImpl` and `UserRepositoryImpl` use `e.printStackTrace()` for error handling. No JSON log formatters, no correlation IDs, no log levels.
- **Gap**: Unstructured logs. No correlation IDs to trace agent requests through the system.
- **Recommendation**: Replace `System.out.println()` and `e.printStackTrace()` with SLF4J/Logback. Configure JSON log format with Logstash encoder. Add MDC-based correlation ID middleware that propagates through all service layers.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no golden dataset files.
- **Gap**: No automated evaluation for the agent. Cannot measure agent accuracy on order queries, return processing, or inventory management.
- **Recommendation**: Create a golden dataset of order status inquiries, return scenarios, and inventory questions with expected agent responses. Implement an automated eval pipeline using RAGAS or custom scoring scripts that run in CI.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms, no latency targets, no error budget tracking. The health endpoint (`/health/ishealthy`) returns a static string — no metric collection.
- **Gap**: No SLOs for API availability, latency, or error rates. No way to measure if the system meets agent response time requirements.
- **Recommendation**: Define SLOs for critical endpoints: product listing p99 < 500ms, basket operations p99 < 300ms. Create CloudWatch alarms with composite thresholds. When the agent is deployed, add agent-specific SLOs (task success rate, response latency).

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy defined. No blue/green, no canary, no rollback configuration. No feature flags, no prompt versioning.
- **Gap**: No automated rollback capability. A bad deployment or agent configuration change cannot be safely reverted.
- **Recommendation**: Implement ECS blue/green deployments via CodeDeploy with automatic rollback on CloudWatch alarm triggers. Add feature flags for the agent integration to enable gradual rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token tracking, no cost attribution, no usage metrics.
- **Gap**: No infrastructure for tracking LLM costs. When the agent is deployed, there will be no visibility into token consumption per user or per workflow.
- **Recommendation**: Implement per-request token usage logging from Bedrock API responses. Create CloudWatch custom metrics for token consumption attributed by user, workflow type (order inquiry vs. return processing vs. inventory), and agent session.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics. No CloudWatch `put_metric_data` calls. No dashboards tracking business KPIs. Only infrastructure-level health checks via the `/health` endpoints.
- **Gap**: No business outcome metrics. Cannot measure agent effectiveness on order resolution rate, return processing time, or inventory accuracy.
- **Recommendation**: Publish custom CloudWatch metrics for: orders viewed, baskets modified, users created, returns processed. When the agent is live, add: agent task completion rate, customer satisfaction, escalation rate.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection. No CloudWatch alarms of any kind. No error rate monitoring, no latency tracking, no PagerDuty/OpsGenie integration.
- **Gap**: No alerting on anomalous behavior. An agent entering a tool-calling loop or generating excessive errors would go undetected.
- **Recommendation**: Enable CloudWatch anomaly detection on API error rates and latency. Set up composite alarms. When the agent is deployed, add behavioral anomaly detection (e.g., alert if tool calls per session exceed 3x normal baseline).

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy defined. No blue/green, no canary, no progressive rollout. No IaC, no CI/CD — deployments are presumably manual.
- **Gap**: Direct-to-production deployments with no safety net. Agent configuration changes and prompt updates have no graduated rollout.
- **Recommendation**: Implement ECS blue/green deployments with CodeDeploy. Use ALB weighted target groups for canary releases. For the agent, implement prompt versioning with A/B testing via feature flags.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` includes `spring-boot-starter-test` dependency but no test directory was found containing any test files. No integration tests, no test containers, no API test suites (Postman/Newman), no contract tests.
- **Gap**: Zero test coverage. No integration tests to verify agent tool invocations work correctly.
- **Recommendation**: Create integration test suites for all API endpoints. Use TestContainers for database integration tests. When the agent is built, add end-to-end tests for agent workflows (order inquiry flow, return processing flow).

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, no SSM automation documents, no Lambda remediation functions, no incident response workflows. No self-healing patterns.
- **Gap**: No automated incident response. Agent failures require manual investigation and remediation.
- **Recommendation**: Create machine-readable runbooks in YAML for common failure scenarios (database connection failure, high error rate, agent timeout). Implement SSM Automation documents for automated remediation. Link runbooks to CloudWatch alarms.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions, no CODEOWNERS file, no team ownership files, no observability governance. No evidence of platform engineering or shared responsibility model.
- **Gap**: No observability ownership model. When the agent is deployed, it's unclear who owns agent quality, reliability, and safety monitoring.
- **Recommendation**: Define CODEOWNERS for the repository. Establish an observability ownership model: platform team owns the infrastructure metrics pipeline, product team owns agent SLOs (task success rate, hallucination rate). Define dashboards with named owners.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | High | APP-Q4: 2/4, INF-Q1: 1/4, APP-Q3: 1/4, APP-Q10: 2/4 | High |
| Move to Containers | Triggered | Medium | High | INF-Q1: 1/4, No Dockerfile found | Medium |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Triggered | High | High | INF-Q2: 2/4, DATA-Q10: 1/4 | Medium |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q5: 1/4, INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1 (Infrastructure Foundation)**: Move to Containers + Move to Modern DevOps — can run concurrently. Containerize the application while building CI/CD pipelines and IaC.

**Parallel Track 2 (Data & AI)**: Move to Managed Databases + Move to AI — can run concurrently after containers are in place. Migrate to RDS/DynamoDB while building the agent layer.

**Sequential Dependencies**: Move to Containers must complete before Move to Cloud Native (containerize before decomposing). Move to Modern DevOps should start first to enable automated deployments for all other pathways.

### Move to Containers

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q1: Score 1/4 — Application runs on raw EC2 (`HealthController.java` uses `EC2MetadataUtils`). No container definitions found.
  - No Dockerfile found in repository — no containerization at all.
- **Current State**: Java Spring Boot application deployed directly on EC2 as a JAR with embedded Tomcat. No Dockerfile, no container image, no container orchestration.
- **Target State**: Application containerized with a multi-stage Dockerfile, images stored in ECR, deployed on ECS Fargate with health checks and resource limits.
- **Key Activities**:
  1. Create a multi-stage Dockerfile for the Spring Boot application (Gradle build stage + JRE runtime stage)
  2. Set up Amazon ECR repository for container images
  3. Define ECS Fargate task definitions and service in Terraform
  4. Configure ALB health checks pointing to `/health/ishealthy`
- **Dependencies**: None — this is a starting point pathway
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Managed Databases

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q2: Score 2/4 — MySQL database with unconfirmed management status. No IaC defining RDS. Hardcoded credentials.
  - DATA-Q10: Score 1/4 — MySQL connector 8.0.11 (2018) is severely outdated. No engine version pinning.
- **Current State**: MySQL database accessible via environment variable `MONO_TO_MICRO_DB_ENDPOINT`. No IaC confirming RDS. Credentials hardcoded. Connector outdated.
- **Target State**: Amazon RDS for MySQL (or Aurora MySQL) with Multi-AZ, automated backups, Secrets Manager integration, and explicit engine version pinning. DynamoDB for basket/cart data per preferences.
- **Key Activities**:
  1. Define RDS MySQL instance in Terraform with Multi-AZ, encryption, and automated backups
  2. Migrate credentials from `application.properties` to Secrets Manager
  3. Update `mysql-connector-java` to latest 8.0.x
  4. Evaluate migrating `unicorns_basket` table to DynamoDB (per preferences) for cart data
- **Dependencies**: Move to Modern DevOps (need Terraform pipeline to deploy RDS)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (version pinning, Secrets Manager) and Phase 2 (RDS/DynamoDB migration)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Cloud Native

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 2/4 — Monolith with identifiable modules but shared database coupling
  - INF-Q1: Score 1/4 — Raw EC2 compute
  - APP-Q3: Score 1/4 — 100% synchronous communication
  - APP-Q10: Score 2/4 — No async infrastructure for long-running operations
- **Current State**: Single Spring Boot monolith with controller/service/repository layers per domain (unicorns, baskets, users). All domains share one MySQL database. All communication is synchronous HTTP.
- **Target State**: Modular services with clear boundaries — at minimum, a Product/Inventory Service, an Order/Basket Service, and a User Service — each independently deployable on ECS with its own data store, communicating via EventBridge and SQS.
- **Key Activities**:
  1. Conduct domain modeling to identify bounded contexts (Product, Basket/Order, User)
  2. Introduce EventBridge for event-driven communication between domains
  3. Add SQS queues for async processing of order and inventory operations
  4. Extract first service candidate (Basket/Order service) using Strangler Fig pattern
- **Dependencies**: Move to Containers must complete first (containerize before decomposing)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Agent Foundations) and Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q5: Score 1/4 — Zero IaC files in repository
  - INF-Q6: Score 1/4 — No CI/CD pipeline definitions
  - OPS-Q9: Score 1/4 — No deployment strategy (no blue/green, no canary)
  - OPS-Q10: Score 1/4 — No integration tests
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: No IaC, no CI/CD, no automated testing, no deployment strategy, no observability. Entirely manual operations.
- **Target State**: Full Terraform IaC covering all infrastructure. GitOps-based CI/CD pipeline (GitHub Actions + Helm). Blue/green deployments on ECS. Integration test suites in CI. Distributed tracing with OpenTelemetry.
- **Key Activities**:
  1. Create Terraform project for VPC, ECS, RDS, ALB, and IAM
  2. Build GitHub Actions CI/CD pipeline with build, test, push, and deploy stages
  3. Implement Helm charts for ECS deployments (per preferences)
  4. Add distributed tracing (OpenTelemetry or X-Ray)
  5. Create integration test suites for all API endpoints
- **Dependencies**: None — this should be the first pathway to start
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (IaC and CI/CD) and Phase 2 (advanced observability)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No agent frameworks present
  - DATA-Q1: Score 1/4 — No vector database
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated evals
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: Zero AI/agent capability. No LLM integration, no vector store, no RAG pipeline, no evaluation framework, no cost tracking.
- **Target State**: Fully operational AI agent for order status inquiries, returns processing, and inventory management, powered by Amazon Bedrock, with RAG-based knowledge retrieval from product/policy documentation, automated evaluation pipeline, and per-request cost tracking.
- **Key Activities**:
  1. Integrate Amazon Bedrock SDK and Strands Agents SDK
  2. Generate OpenAPI specs from existing controllers to define agent tools
  3. Set up Amazon OpenSearch or Bedrock Knowledge Base for RAG
  4. Build agent tools for: product lookup, basket/order query, return initiation, inventory check
  5. Create golden evaluation dataset for order/return/inventory scenarios
  6. Implement LLM token usage tracking and cost attribution
- **Dependencies**: Move to Modern DevOps (need CI/CD for agent deployment). Move to Managed Databases (need reliable data backend). API documentation (APP-Q2) must be addressed first.
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Agent Foundations) and Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

This monolith would benefit from service extraction to create clear agent tool boundaries. The existing layered architecture — with separate controller/service/repository stacks for Unicorns (products), Baskets (orders), and Users — provides natural service candidates. Baskets reference unicorns by UUID (not foreign key), suggesting loose coupling at the data level. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface (`/unicorns`, `/unicorns/basket`, `/user`) while containerization and API documentation are completed.

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Order/Inventory Query Agent via JSON APIs** — Your existing REST endpoints (`/unicorns`, `/unicorns/basket/{userUuid}`) already return structured JSON responses (APP-Q5 score 3/4). An agent can invoke these endpoints as tools to answer customer questions like "What products are available?" or "What's in my cart?"
   - **Leverages**: JSON API responses via `@JsonInclude` annotations on `Unicorn.java` and `User.java` models; existing `GET /unicorns` and `GET /unicorns/basket/{userUuid}` endpoints
   - **Effort**: Low
   - **Value**: Demonstrates agent value immediately for order status inquiries by querying the product catalog and basket data

2. **Natural Language to SQL Agent for Customer Support** — The MySQL database has a clear, documented schema (`create_tables.sql` with 3 tables: `unicorns`, `unicorns_basket`, `unicorn_user`) with well-defined column names and types (DATA-Q7 score 2/4). A text-to-SQL agent could answer questions like "How many items does customer X have in their basket?" or "Show me all products under $50."
   - **Leverages**: Well-documented schema in `create_tables.sql`; MyBatis mapper XMLs documenting all query patterns; single MySQL database with 3 tables
   - **Effort**: Medium
   - **Value**: Enables the customer support agent to query order and inventory data using natural language without building custom API endpoints first

3. **Product Knowledge Agent via RAG** — While no RAG pipeline exists today, the product descriptions in the `unicorns` table and the `web/index.html` storefront contain product information that can be chunked and embedded. Combined with return policy documentation (to be created), this enables a knowledge-based support agent.
   - **Leverages**: Existing product data in MySQL (`unicorns` table with `name`, `description`, `price` fields); web storefront content in `web/index.html`
   - **Effort**: Medium
   - **Value**: Powers the customer support agent's ability to answer product-specific questions and recommend alternatives during returns

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

1. **Create Dockerfile and containerize the application** — Build a multi-stage Dockerfile (Gradle build + JRE 8 runtime). Push to Amazon ECR. This unblocks all subsequent infrastructure improvements. *(Move to Containers)*
2. **Create Terraform project with foundational IaC** — Define VPC (public/private subnets), ECS Fargate cluster, ALB, security groups, and IAM task roles. Deploy the containerized monolith on ECS. *(Move to Modern DevOps)*
3. **Set up CI/CD pipeline** — Create GitHub Actions workflow with Gradle build, Docker image build/push to ECR, and ECS deployment stages. Per preferences, implement GitOps with Helm charts. *(Move to Modern DevOps)*
4. **Migrate secrets to AWS Secrets Manager** — Move database credentials from `application.properties` to Secrets Manager. Update the application to retrieve credentials at runtime. *(Security foundation)*
5. **Generate OpenAPI specs** — Add `springdoc-openapi-ui` to the project. Annotate existing controllers. Generate machine-readable API documentation that can define agent tools. *(Agent prerequisite)*

### Phase 2 — Agent Foundations (Months 1–3)

1. **Define RDS MySQL in Terraform** — Migrate database to Amazon RDS for MySQL with Multi-AZ, automated backups, encryption at rest, and explicit engine version pinning. Update the application to use Secrets Manager for credentials. *(Move to Managed Databases)*
2. **Implement structured logging and distributed tracing** — Replace `System.out.println()` and `e.printStackTrace()` with SLF4J/Logback JSON logging. Add OpenTelemetry or X-Ray for distributed tracing. Add correlation IDs. *(Move to Modern DevOps)*
3. **Deploy API Gateway** — Place Amazon API Gateway in front of the ECS service with throttling, request validation, and Cognito-based authentication. Create agent-specific API keys with rate limits. *(Infrastructure + Security)*
4. **Build the first agent prototype** — Integrate Strands Agents SDK (Python) with Amazon Bedrock. Define tools from the OpenAPI spec: product search, basket query, user lookup. Deploy as a separate ECS service behind API Gateway. *(Move to AI)*
5. **Set up vector database and RAG pipeline** — Provision OpenSearch Service or configure Bedrock Knowledge Base. Ingest product descriptions and return policies. Integrate semantic retrieval into the agent. *(Move to AI)*
6. **Introduce async messaging** — Deploy SQS queues for order processing and SNS topics for return status notifications. Set up EventBridge for inventory restocking events. *(Move to Cloud Native)*
7. **Enable Cognito authentication** — Deploy Cognito user pool. Configure JWT validation in Spring Security. Issue machine-to-machine credentials for the agent. *(Security)*

### Phase 3 — Agent Scale & Optimization (Months 3–6)

1. **Implement automated agent evaluation** — Create golden dataset for order inquiry, return processing, and inventory scenarios. Build eval pipeline that runs in CI/CD on every agent change. *(Move to AI)*
2. **Implement human-in-the-loop approval** — Deploy Step Functions workflow for high-risk agent actions (refunds, bulk inventory changes) with `waitForTaskToken` for human approval. *(Security + Workflow)*
3. **Extract first microservice** — Using Strangler Fig pattern, extract the Basket/Order service as an independent ECS service with its own DynamoDB table (per preferences). Route via API Gateway. *(Move to Cloud Native)*
4. **Implement LLM cost tracking and business metrics** — Track token usage per request with user/workflow attribution. Publish business metrics (agent task completion rate, resolution time, escalation rate) to CloudWatch. *(Operations)*
5. **Enable anomaly detection and SLOs** — Define SLOs for critical endpoints and agent workflows. Enable CloudWatch anomaly detection on error rates and latency. Set up behavioral baselines for agent tool-calling patterns. *(Operations)*
6. **Implement blue/green deployments and rollback** — Configure ECS blue/green deployments via CodeDeploy with automatic rollback on alarm triggers. Add prompt versioning with A/B testing for the agent. *(Move to Modern DevOps)*

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
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
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ
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
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

---

## Appendix: Evidence Index

| # | File | Key Finding |
|---|------|-------------|
| 1 | `build.gradle` | Java 8, Spring Boot 2.1.x, AWS SDK v1 (1.11.567), MySQL connector 8.0.11, Spring Security OAuth2/JWT dependencies, no AI/agent frameworks |
| 2 | `src/main/resources/application.properties` | Port 8080, MySQL JDBC connection with env var endpoint, hardcoded credentials (MonoToMicroUser/MonoToMicroPassword) |
| 3 | `database/create_tables.sql` | 3 tables (unicorns, unicorns_basket, unicorn_user), InnoDB engine, no stored procedures/triggers, standard SQL only |
| 4 | `src/main/java/com/monoToMicro/Application.java` | @SpringBootApplication main entry point, CORS configuration, WebSecurity ignoring OPTIONS requests |
| 5 | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | EC2MetadataUtils usage confirming EC2 deployment, System.out.println() logging, no structured logging |
| 6 | `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | GET /unicorns endpoint, @PreAuthorize("permitAll()"), synchronous service calls |
| 7 | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | POST/DELETE/GET /unicorns/basket endpoints, no idempotency keys, no rate limiting |
| 8 | `src/main/java/com/monoToMicro/rest/controller/UserController.java` | POST /user and /user/login endpoints, no authentication validation on login |
| 9 | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | GET /data endpoint for basket replication, no orchestration |
| 10 | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | @EnableResourceServer with permitAll() — security completely disabled |
| 11 | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | Repository pattern, e.printStackTrace() error handling, no retry/circuit breaker |
| 12 | `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | Repository pattern, synchronized create method, e.printStackTrace() error handling |
| 13 | `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | Centralized SqlSessionFactory, mapper registration for Unicorn/User/Health mappers |
| 14 | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | CRUD service, synchronous calls, no async patterns |
| 15 | `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | User creation with UUID generation, synchronous calls |
| 16 | `src/main/java/com/monoToMicro/core/model/Unicorn.java` | @JsonInclude(NON_NULL) — confirms JSON response format |
| 17 | `src/main/java/com/monoToMicro/core/model/User.java` | PII fields (email, firstName, lastName), @JsonInclude(NON_NULL) |
| 18 | `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | INSERT IGNORE, SELECT with JOIN, standard MySQL SQL |
| 19 | `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | insert ignore, getByEmail query, standard SQL |
| 20 | `README.md` | Minimal — redirects to external workshop URL, no local documentation |
