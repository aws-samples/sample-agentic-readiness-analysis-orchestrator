# Agentic Readiness Assessment Report
**Target**: /Users/antonaws/dev/tmp/atx-ai-assessment
**Date**: 2026-02-17
**Assessed by**: Claude Agentic Readiness Assessment Skill

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Top Priorities (Critical Gaps)](#top-priorities-critical-gaps)
3. [Readiness Roadmap](#readiness-roadmap)
   - [Phase 1 — Quick Wins (Days 1–30)](#phase-1--quick-wins-days-130)
   - [Phase 2 — Foundation (Months 1–3)](#phase-2--foundation-months-13)
   - [Phase 3 — Agent Enablement (Months 3–6)](#phase-3--agent-enablement-months-36)
4. [Detailed Findings](#detailed-findings)
   - [Infrastructure & Platform](#infrastructure--platform)
   - [Application Architecture](#application-architecture)
   - [Data Foundations](#data-foundations)
   - [Identity, Security & Governance](#identity-security--governance)
   - [Operations & Observability](#operations--observability)
5. [Appendix: Evidence Index](#appendix-evidence-index)

---

## Executive Summary

This TODO application is a traditional monolithic Java 13 Spring Boot application running entirely on EC2 instances with self-managed databases. While it demonstrates good practices in structured logging, API documentation, and centralized identity (Cognito), it is fundamentally **not ready for agentic workloads**. The architecture relies on manual deployment, lacks resilience patterns, has no async messaging or workflow orchestration, and stores secrets insecurely. The vector search capability uses custom SHA-256 hash-based embeddings rather than proper embedding models, making it unsuitable for production RAG applications. Most critically, there is no CI/CD automation, no observability beyond basic logging, and zero test coverage.

### Overall Score: 1.8 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.6 / 4.0 | ❌ Not Present |
| Application Architecture | 1.6 / 4.0 | ❌ Not Present |
| Data Foundations | 2.3 / 4.0 | 🟠 Needs Work |
| Identity, Security & Governance | 2.1 / 4.0 | 🟠 Needs Work |
| Operations & Observability | 1.3 / 4.0 | ❌ Not Present |

---

## Top Priorities (Critical Gaps)

### 1. Migrate from EC2 to Managed Compute (ECS/Fargate or Lambda)
**Why it matters**: Raw EC2 instances require manual scaling, patching, and high operational overhead. Agents need elastic compute that scales automatically with demand. Current architecture (single EC2 instances in [terraform/compute.tf:52-119](terraform/compute.tf#L52-L119)) cannot handle variable agentic workloads.

**First step**: Containerize the application with Docker and deploy to ECS Fargate. This eliminates instance management while maintaining compatibility with Spring Boot. Estimated effort: 2-3 weeks for containerization and ECS migration.

### 2. Replace Self-Managed Databases with RDS Aurora and OpenSearch Service
**Why it matters**: MySQL and ElasticSearch running on EC2 ([terraform/compute.tf:52-86](terraform/compute.tf#L52-L86)) lack automated backups, failover, and encryption at rest. Agents require reliable data persistence with zero manual intervention.

**First step**: Create RDS Aurora MySQL cluster via Terraform, migrate schema using existing JPA migrations, then switch connection string. Follow with OpenSearch Service for vector search. Estimated effort: 2-3 weeks for both migrations.

### 3. Implement Secrets Manager for All Credentials
**Why it matters**: Database passwords are currently passed as plaintext environment variables in user-data scripts ([terraform/compute.tf:60-108](terraform/compute.tf#L60-L108)) and Terraform variables ([terraform/variables.tf:55-77](terraform/variables.tf#L55-L77)). This is a critical security vulnerability that blocks any production agent deployment.

**First step**: Create AWS Secrets Manager secrets for MySQL and Cognito credentials via Terraform, update IAM role to allow secret access, and modify application.properties to fetch secrets at startup using AWS SDK. Estimated effort: 3-5 days.

### 4. Build Automated CI/CD Pipeline with Testing
**Why it matters**: Current deployment is fully manual ([build.sh](build.sh), [deploy.sh](deploy.sh)) with zero test coverage (0 test files found). Agents require rapid, safe iteration with automated validation. Manual deployments create risk and slow down development velocity.

**First step**: Create GitHub Actions workflow that runs `mvn test` (after adding tests), builds Docker image, pushes to ECR, and deploys to ECS. Add integration tests for critical TODO CRUD operations. Estimated effort: 1-2 weeks.

### 5. Implement Real Embedding Models via Bedrock or SageMaker
**Why it matters**: Current embedding generation uses SHA-256 hashing ([src/main/java/com/todo/app/service/EmbeddingService.java:21-41](src/main/java/com/todo/app/service/EmbeddingService.java#L21-L41)), not semantic embeddings. This makes vector search functionally useless for RAG applications. Agents need actual semantic understanding.

**First step**: Integrate Amazon Bedrock Titan Embeddings v2 via AWS SDK. Replace `EmbeddingService.generateEmbedding()` to call Bedrock API. Update ElasticSearch dimension from 128 to match Bedrock model (1024 or 384 depending on model). Estimated effort: 3-5 days.

---

## Readiness Roadmap

### Phase 1 — Quick Wins (Days 1–30)

1. **Add Secrets Manager integration** — Eliminate hardcoded credentials from Terraform and application config. Move all secrets to AWS Secrets Manager with proper IAM policies.

2. **Implement API Gateway with throttling** — Replace direct ALB exposure with API Gateway. Configure burst/rate limits, request validation, and Cognito authorizer at gateway level.

3. **Add structured business metrics** — Emit custom CloudWatch metrics for TODO operations (create/update/delete counts, search latency, user activity). Enable data-driven decision making.

4. **Enable CloudWatch anomaly detection** — Configure CloudWatch anomaly detection alarms on ALB 5xx errors, target response time (p99), and unhealthy host count.

5. **Integrate Bedrock Titan Embeddings** — Replace mock hash-based embeddings with real Bedrock Titan Embeddings v2 API calls for production-grade semantic search.

### Phase 2 — Foundation (Months 1–3)

1. **Migrate to ECS Fargate** — Containerize application, create ECS cluster with Fargate tasks, implement auto-scaling based on CPU/memory/request count. Remove EC2 instance management burden.

2. **Replace self-managed databases** — Migrate MySQL to RDS Aurora with multi-AZ, automated backups, and encryption at rest. Migrate ElasticSearch to Amazon OpenSearch Service with k-NN plugin.

3. **Build full CI/CD pipeline** — GitHub Actions workflow with automated testing, Docker build, ECR push, ECS deployment with blue/green strategy. Include rollback capability.

4. **Implement async messaging with SQS** — Decouple long-running operations (embedding generation, bulk operations) into async SQS queues with Lambda or ECS task consumers.

5. **Add comprehensive test coverage** — Write integration tests for all CRUD operations, authentication flows, and search functionality. Target 70%+ coverage.

6. **Implement retry and circuit breaker patterns** — Add Resilience4j for all external calls (MySQL, OpenSearch, Bedrock). Configure exponential backoff and circuit breakers.

### Phase 3 — Agent Enablement (Months 3–6)

1. **Implement Step Functions workflow orchestration** — Move complex multi-step operations (e.g., bulk TODO processing, approval workflows) to Step Functions state machines.

2. **Add distributed tracing with X-Ray** — Instrument all service calls with AWS X-Ray SDK. Enable end-to-end trace ID propagation across services.

3. **Build Bedrock Knowledge Base** — Create Bedrock Knowledge Base backed by OpenSearch for RAG. Implement automated document ingestion and embedding refresh pipeline.

4. **Implement agent framework integration** — Add support for Claude via Bedrock, integrate with LangChain or Strands Agents SDK. Create agent-callable APIs for TODO operations.

5. **Add human-in-the-loop approval workflow** — Implement Step Functions with manual approval tasks for high-risk operations (bulk delete, admin actions).

6. **Implement API versioning strategy** — Add /v1/ URL prefix, implement backward compatibility, create versioned OpenAPI specs.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: All compute runs on raw EC2 instances. Application server ([terraform/compute.tf:88-119](terraform/compute.tf#L88-L119)), MySQL ([terraform/compute.tf:52-70](terraform/compute.tf#L52-L70)), and ElasticSearch ([terraform/compute.tf:72-86](terraform/compute.tf#L72-L86)) are all single EC2 instances with no auto-scaling or container orchestration.
- **Gap**: 0% managed compute. Manual instance management, patching, and scaling required. Single points of failure.
- **Recommendation**: Containerize Spring Boot app with Docker, deploy to ECS Fargate with auto-scaling. This eliminates instance management and provides automatic scaling for variable agent workloads.

#### INF-Q2: Databases
- **Score**: 1/4 ❌
- **Finding**: MySQL 8.0 installed on EC2 via user-data script ([terraform/compute.tf:60-65](terraform/compute.tf#L60-L65)). ElasticSearch 7.13.4 on EC2 ([terraform/compute.tf:81](terraform/compute.tf#L81)). No managed database services.
- **Gap**: Self-managed databases lack automated backups, failover, encryption at rest, and monitoring. High operational burden and risk.
- **Recommendation**: Migrate to RDS Aurora MySQL with multi-AZ, automated backups, and KMS encryption. Replace self-hosted ElasticSearch with Amazon OpenSearch Service with k-NN plugin for vector search.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, or workflow orchestration found in IaC or application code. All business logic is synchronous in service layer ([src/main/java/com/todo/app/service/TodoService.java](src/main/java/com/todo/app/service/TodoService.java)).
- **Gap**: No orchestration for complex multi-step processes. Cannot handle long-running agentic workflows or approval chains.
- **Recommendation**: Introduce AWS Step Functions for multi-step workflows. Start with a simple workflow for bulk TODO processing or approval flows. This enables durable, resumable agent orchestration.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or messaging services in Terraform. Application uses synchronous HTTP and JPA calls only. No async patterns in code.
- **Gap**: All operations are blocking. Cannot handle background jobs, event-driven patterns, or decouple services.
- **Recommendation**: Introduce SQS for async operations. Move embedding generation to SQS queue processed by Lambda or ECS task. This enables agents to queue long-running tasks without blocking API responses.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: Complete Terraform infrastructure covering compute ([terraform/compute.tf](terraform/compute.tf)), networking ([terraform/network.tf](terraform/network.tf)), IAM ([terraform/iam.tf](terraform/iam.tf)), Cognito ([terraform/cognito.tf](terraform/cognito.tf)), and CloudWatch ([terraform/cloudwatch.tf](terraform/cloudwatch.tf)). No manual resources detected.
- **Gap**: None. IaC coverage is comprehensive.
- **Recommendation**: Maintain this practice. Add Terraform modules for reusability as infrastructure grows.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: Manual build and deploy scripts ([build.sh](build.sh), [deploy.sh](deploy.sh)). No GitHub Actions, CodePipeline, or automated deployment. `build.sh` skips tests with `-DskipTests` flag (line 13).
- **Gap**: Fully manual deployment requiring SSH access to private EC2 instances. No automated testing, building, or deployment. High risk of human error.
- **Recommendation**: Create GitHub Actions workflow with stages: test → build → push to ECR → deploy to ECS. Implement blue/green deployment with automated rollback on health check failure.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Application Load Balancer present ([terraform/compute.tf:2-48](terraform/compute.tf#L2-L48)) with health checks ([line 23-31](terraform/compute.tf#L23-L31)). No API Gateway. No throttling, no WAF, no request validation at gateway layer.
- **Gap**: Basic load balancing only. Missing API Gateway features: throttling, request validation, usage plans, API keys, caching.
- **Recommendation**: Replace ALB with API Gateway HTTP API or REST API. Configure Cognito authorizer at gateway level, add throttling (burst/rate limits), and request validation. Maintain ALB for internal routing if needed.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, MSK, or streaming services in infrastructure. No streaming SDK imports in application.
- **Gap**: Cannot handle real-time event streams or stream processing for agent telemetry.
- **Recommendation**: If real-time agent telemetry is needed, add Kinesis Data Streams for event ingestion and Kinesis Data Analytics for stream processing. Not critical for initial agent enablement.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: VPC with public/private subnet separation ([terraform/network.tf:1-102](terraform/network.tf#L1-L102)). NAT Gateway for private subnet egress ([network.tf:54-62](terraform/network.tf#L54-L62)). Security groups with scoped ingress rules ([network.tf:104-237](terraform/network.tf#L104-L237)). App/MySQL/ElasticSearch in private subnet. However, `allowed_cidr_blocks` defaults to `["0.0.0.0/0"]` ([terraform/variables.tf:87](terraform/variables.tf#L87)).
- **Gap**: ALB accepts traffic from entire internet by default. No NACLs defined. Egress rules are wide open (0.0.0.0/0).
- **Recommendation**: Change `allowed_cidr_blocks` default to specific IP ranges or VPN CIDR. Add NACLs for defense in depth. Implement least-privilege egress rules (specific AWS service VPC endpoints).

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: Single EC2 instances for all tiers. No Auto Scaling Groups, no ECS Service auto-scaling, no Lambda concurrency limits. Static capacity.
- **Gap**: Cannot scale with load. Agent workloads are inherently bursty and require elastic scaling.
- **Recommendation**: After ECS migration, implement ECS Service auto-scaling based on target tracking (CPU/memory/ALB request count). Set min 2, desired 2, max 10 for high availability and elasticity.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 13 ([pom.xml:24](pom.xml#L24)) with Spring Boot 2.3.12 ([pom.xml:19](pom.xml#L19)). Maven project.
- **Gap**: Java has mature LangChain4j and Spring AI frameworks, but Python and TypeScript have richer agent ecosystems (LangGraph, CrewAI, Anthropic SDK). Java 13 is outdated (current LTS is Java 17/21).
- **Recommendation**: Upgrade to Java 21 LTS immediately. Consider adding Python microservices for agent orchestration using LangGraph or CrewAI, calling Java APIs for TODO operations.

#### APP-Q2: API Documentation
- **Score**: 4/4 ✅
- **Finding**: OpenAPI annotations throughout controllers ([src/main/java/com/todo/app/controller/TodoController.java](src/main/java/com/todo/app/controller/TodoController.java)). Springdoc OpenAPI UI configured ([src/main/java/com/todo/app/config/OpenApiConfig.java](src/main/java/com/todo/app/config/OpenApiConfig.java)). Swagger UI available at `/swagger-ui.html` and JSON spec at `/api-docs` ([application.properties:37-38](src/main/resources/application.properties#L37-L38)).
- **Gap**: None. API documentation is comprehensive and machine-readable.
- **Recommendation**: Maintain OpenAPI specs as APIs evolve. Export spec to CI/CD pipeline for agent SDK generation. This is already agent-ready.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All operations are synchronous HTTP/JPA transactions. No message queue producers or async `@Async` methods. Embedding generation blocks API response ([TodoService.java:47,96](src/main/java/com/todo/app/service/TodoService.java#L47)).
- **Gap**: 0% async. Long operations (embedding generation, bulk processing) block request threads.
- **Recommendation**: Make embedding generation async via SQS. Return 202 Accepted for long operations with status polling endpoint. This prevents timeout issues for agent-initiated bulk operations.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single Spring Boot monolith with all functionality (auth, CRUD, search) in one deployable JAR. Good internal modularity with controller/service/repository layers.
- **Gap**: Single deployment unit limits independent scaling and technology choices. Cannot scale search differently from CRUD.
- **Recommendation**: Acceptable for initial agent integration. Later, extract search service to separate microservice if search load diverges from CRUD operations.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API endpoints return JSON ([TodoController.java](src/main/java/com/todo/app/controller/TodoController.java)). Spring Boot auto-serialization via Jackson. Structured response DTOs ([TodoResponse.java](src/main/java/com/todo/app/model/TodoResponse.java)).
- **Gap**: None. JSON everywhere makes APIs agent-consumable.
- **Recommendation**: Maintain consistent JSON response structure. Consider adding HAL or JSON:API links for hypermedia if agents need to discover operations.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: Business logic embedded directly in service classes ([TodoService.java](src/main/java/com/todo/app/service/TodoService.java)). No workflow orchestration. State transitions are implicit in method calls.
- **Gap**: Cannot represent complex multi-step agent workflows as declarative state machines. No visibility into workflow state or retry logic.
- **Recommendation**: Introduce Step Functions for multi-step workflows. Model agent decision flows as state machines with error handling and retry policies.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No `Idempotency-Key` header support. No idempotency checks in create/update operations. Database-level idempotency relies on transaction boundaries only.
- **Gap**: Agents retrying failed requests can create duplicate TODOs. No safe retry pattern.
- **Recommendation**: Add `Idempotency-Key` header to POST/PUT endpoints. Store keys in Redis or DynamoDB with TTL. Return same response for duplicate keys within TTL window.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No API Gateway throttling (no API Gateway exists). No rate limiting middleware in Spring Security config. No Bucket4j or similar library in dependencies.
- **Gap**: Agents can overwhelm API with unlimited requests. No protection against runaway agent loops.
- **Recommendation**: Implement rate limiting at API Gateway (after migration). Configure burst/rate limits per Cognito identity. Add application-level limiting with Bucket4j as backup.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No Resilience4j or Hystrix in dependencies ([pom.xml](pom.xml)). Direct database and ElasticSearch calls without retry logic ([TodoService.java](src/main/java/com/todo/app/service/TodoService.java)). No circuit breakers.
- **Gap**: Transient failures propagate to API callers immediately. No exponential backoff, no circuit breaker to prevent cascading failures.
- **Recommendation**: Add Resilience4j dependency. Wrap all external calls (MySQL, OpenSearch, Bedrock) with `@Retry`, `@CircuitBreaker`, and `@Timeout` annotations. Configure sensible defaults (3 retries, exponential backoff, 30s circuit breaker).

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All API endpoints are synchronous. No background job framework (no Celery, Bull, SQS workers). Embedding generation happens inline ([TodoService.java:47](src/main/java/com/todo/app/service/TodoService.java#L47)).
- **Gap**: Operations >30s will timeout at ALB (default 60s idle timeout). Agents cannot trigger long-running batch operations safely.
- **Recommendation**: Implement async job pattern. POST to `/api/todos/batch` returns 202 with job ID. GET `/api/jobs/{id}` polls status. Use SQS + Lambda for processing.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No version prefix in URLs ([TodoController.java:23](src/main/java/com/todo/app/controller/TodoController.java#L23) shows `/api/todos`). No `Accept-Version` header handling. No versioning annotations.
- **Gap**: Cannot evolve APIs without breaking existing agent integrations.
- **Recommendation**: Add `/v1/` prefix to all endpoints. Create versioning strategy for future v2. Maintain backward compatibility for at least 2 versions.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Hard-coded private IPs in user-data scripts ([terraform/compute.tf:98-108](terraform/compute.tf#L98-L108)). No AWS Service Discovery, no App Mesh, no service registry.
- **Gap**: IP address changes require redeployment. Cannot dynamically discover services. No service mesh benefits (mTLS, traffic splitting).
- **Recommendation**: After ECS migration, use AWS Cloud Map (Service Discovery) for service registration. Update application to resolve services via DNS instead of hard-coded IPs.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No agent SDK dependencies in [pom.xml](pom.xml). Custom embedding service using SHA-256 hash ([EmbeddingService.java:21-41](src/main/java/com/todo/app/service/EmbeddingService.java#L21-L41)), not real embeddings. No Bedrock SDK, LangChain, or agent framework.
- **Gap**: Cannot integrate with LLMs or agent frameworks. Mock embeddings prevent real RAG.
- **Recommendation**: Add AWS SDK for Bedrock. Integrate Bedrock Titan Embeddings v2 and Claude 3. Consider LangChain4j or Spring AI for agent orchestration.

### Data Foundations

#### DATA-Q1: Vector Database
- **Score**: 3/4 🟡
- **Finding**: ElasticSearch with `dense_vector` type configured ([ElasticSearchService.java:83-86](src/main/java/com/todo/app/service/ElasticSearchService.java#L83-L86)). Index created with 128-dimensional vectors. Vector search capability present.
- **Gap**: Self-hosted on EC2 rather than managed service. Embeddings are mock (SHA-256 hash), not semantic.
- **Recommendation**: Keep ElasticSearch vector capability but migrate to Amazon OpenSearch Service. Replace mock embeddings with Bedrock Titan Embeddings (requires dimension update to 1024 or 384).

#### DATA-Q2: Vector DB: Managed vs Self-hosted
- **Score**: 1/4 ❌
- **Finding**: ElasticSearch 7.13.4 installed on EC2 via user-data script ([terraform/compute.tf:72-86](terraform/compute.tf#L72-L86)). Manual installation and management required.
- **Gap**: No automated backups, scaling, or patching for vector store. Operational burden and risk.
- **Recommendation**: Migrate to Amazon OpenSearch Service with k-NN plugin enabled. Terraform resource `aws_opensearch_domain` with `engine_version = "OpenSearch_2.11"`. Managed service handles scaling, backups, and updates.

#### DATA-Q3: RAG Implementation
- **Score**: 2/4 🟠
- **Finding**: Chunking exists (concatenates title + description, [ElasticSearchService.java:102](src/main/java/com/todo/app/service/ElasticSearchService.java#L102)). Embedding generation present ([EmbeddingService.java](src/main/java/com/todo/app/service/EmbeddingService.java)). Semantic search implemented ([ElasticSearchService.java:133-161](src/main/java/com/todo/app/service/ElasticSearchService.java#L133-L161)). However, embeddings are SHA-256 hash-based ([EmbeddingService.java:28](src/main/java/com/todo/app/service/EmbeddingService.java#L28)), not semantic.
- **Gap**: RAG skeleton exists but embeddings are functionally useless for semantic search. No actual semantic understanding.
- **Recommendation**: Replace `EmbeddingService` implementation with Bedrock Titan Embeddings v2 API calls. Update ElasticSearch mapping to match Bedrock dimension (1024 for Titan v2). Re-index all existing TODOs.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Two data sources: MySQL for persistence ([TodoRepository.java](src/main/java/com/todo/app/repository/TodoRepository.java)) and ElasticSearch for search ([ElasticSearchService.java](src/main/java/com/todo/app/service/ElasticSearchService.java)). Both accessed from `TodoService`.
- **Gap**: Dual-write pattern (write to both MySQL and ElasticSearch) creates consistency risk if one fails. No event sourcing or CDC.
- **Recommendation**: Acceptable for current scale. Consider adding DynamoDB Streams or Aurora CDC to automatically replicate changes to OpenSearch, eliminating dual-write risk.

#### DATA-Q5: Data Access Pattern
- **Score**: 3/4 🟡
- **Finding**: Repository pattern used for MySQL ([TodoRepository.java](src/main/java/com/todo/app/repository/TodoRepository.java)). Service layer encapsulates data access ([TodoService.java](src/main/java/com/todo/app/service/TodoService.java)). No direct JDBC or SQL in controllers.
- **Gap**: ElasticSearchService is tightly coupled to domain objects. Could benefit from additional abstraction.
- **Recommendation**: Good pattern overall. Consider adding repository interface for ElasticSearch operations to enable easy swapping to OpenSearch or other vector stores.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 buckets in Terraform. No Textract, Comprehend, or document parsing libraries in dependencies. Application only handles structured TODO text.
- **Gap**: Cannot process documents, images, or unstructured files for RAG.
- **Recommendation**: Add S3 bucket for document storage. Implement Lambda function to invoke Textract for document parsing and Bedrock embeddings. Store embeddings in OpenSearch for retrieval.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: JPA entities define schema ([TodoItem.java](src/main/java/com/todo/app/model/TodoItem.java)). ElasticSearch mapping in code ([ElasticSearchService.java:60-97](src/main/java/com/todo/app/service/ElasticSearchService.java#L60-L97)). No external schema registry, no Flyway/Liquibase migrations, no schema versioning.
- **Gap**: Schema changes are implicit in code. No formal versioning or migration tracking. Cannot rollback schema changes.
- **Recommendation**: Add Flyway for database migrations. Export OpenAPI schema to version control. Create schema changelog with semantic versioning.

#### DATA-Q8: Data Access Layer
- **Score**: 4/4 ✅
- **Finding**: Unified repository pattern ([TodoRepository.java](src/main/java/com/todo/app/repository/TodoRepository.java)). Service layer acts as single data access point ([TodoService.java](src/main/java/com/todo/app/service/TodoService.java)). Controllers never access data directly.
- **Gap**: None. Clean separation of concerns.
- **Recommendation**: Maintain this pattern. Excellent foundation for agent integration.

#### DATA-Q9: Embedding Freshness
- **Score**: 2/4 🟠
- **Finding**: Embeddings generated synchronously on create/update ([TodoService.java:47,96](src/main/java/com/todo/app/service/TodoService.java#L47)). No scheduled refresh, no event-driven updates, no batch re-indexing pipeline.
- **Gap**: Manual trigger only. If embedding model changes, no way to refresh existing embeddings in bulk.
- **Recommendation**: Add EventBridge scheduled rule to trigger Lambda for periodic re-indexing. Implement versioned embeddings (store model version with embedding) to detect stale embeddings.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: MySQL passwords passed as plaintext in Terraform user-data ([terraform/compute.tf:60-65](terraform/compute.tf#L60-L65)). Database credentials in environment variables ([application.properties:7-8](src/main/resources/application.properties#L7-L8)). Secrets defined as Terraform variables ([terraform/variables.tf:55-77](terraform/variables.tf#L55-L77)).
- **Gap**: Critical security vulnerability. Secrets stored in Terraform state, environment variables, and CloudWatch Logs. No rotation capability.
- **Recommendation**: Create AWS Secrets Manager secrets for all credentials. Update IAM role to grant `secretsmanager:GetSecretValue`. Modify application to fetch secrets at startup using AWS SDK. Remove secrets from environment variables and Terraform outputs.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: IAM role scoped to specific resources ([iam.tf:24-44](terraform/iam.tf#L24-L44) for CloudWatch, [iam.tf:48-64](terraform/iam.tf#L48-L64) for Cognito). No wildcard actions except within scoped resources. Per-service role separation.
- **Gap**: Could further restrict Cognito actions (currently allows GetUser and ListUsers globally on user pool). Egress from VPC is unrestricted.
- **Recommendation**: Already good practice. Consider adding condition keys for additional constraints (source IP, MFA requirement for sensitive operations).

#### SEC-Q3: Identity Propagation
- **Score**: 3/4 🟡
- **Finding**: JWT tokens validated via Cognito JWKS ([application.properties:25](src/main/resources/application.properties#L25)). User ID extracted from token ([SecurityUtils.java](src/main/java/com/todo/app/util/SecurityUtils.java)). All operations scoped to authenticated user.
- **Gap**: No correlation ID or trace ID propagation across service boundaries (currently monolith, but will matter after microservices).
- **Recommendation**: Add correlation ID header (`X-Correlation-Id`) to all requests. Propagate through logging context. This enables end-to-end request tracing for agent interactions.

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: CloudWatch Logs configured ([cloudwatch.tf](terraform/cloudwatch.tf)). Application logs all TODO operations with full content ([TodoService.java:137-148](src/main/java/com/todo/app/service/TodoService.java#L137-L148)). Retention set to 7 days ([cloudwatch.tf:4](terraform/cloudwatch.tf#L4)).
- **Gap**: No CloudTrail for AWS API call auditing. No log file validation or immutable storage. Logs stored in CloudWatch without object lock.
- **Recommendation**: Enable CloudTrail with S3 bucket + object lock for immutable audit logs. Enable CloudTrail log file validation. Increase CloudWatch retention to 90+ days for compliance.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No API Gateway (using ALB). No rate limiting at ALB or application layer. No Bucket4j or similar library in dependencies.
- **Gap**: APIs are unprotected from abuse. Agents can overwhelm service with unlimited requests.
- **Recommendation**: Migrate to API Gateway and configure usage plans with rate/burst limits per Cognito identity. Add Bucket4j at application layer as defense in depth.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Full TODO content logged at INFO level ([TodoService.java:137-148](src/main/java/com/todo/app/service/TodoService.java#L137-L148)). TODO title and description contain user-generated content, potentially including PII. No masking or redaction.
- **Gap**: PII may be logged to CloudWatch. Compliance risk (GDPR, CCPA).
- **Recommendation**: Implement logging filter to redact email addresses, phone numbers, SSNs using regex before logging. Alternatively, log only metadata (TODO ID, user ID, operation) not content. Enable Amazon Macie for PII detection in CloudWatch Logs.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No approval workflows in application or infrastructure. All operations execute immediately upon authentication.
- **Gap**: High-risk operations (bulk delete, admin actions) have no approval gate. Agents acting on user behalf could perform destructive actions without human oversight.
- **Recommendation**: Implement Step Functions state machine with callback pattern (`waitForTaskToken`) for high-risk operations. Send approval request to SNS/email, wait for approval before proceeding.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS keys defined in Terraform. MySQL on EC2 has no encryption at rest. ElasticSearch on EC2 unencrypted. ALB uses HTTP (no HTTPS listener defined, [compute.tf:40-48](terraform/compute.tf#L40-L48)).
- **Gap**: All data stored in plaintext. Non-compliant with most security frameworks (PCI DSS, HIPAA, FedRAMP).
- **Recommendation**: Create customer-managed KMS key. Migrate to RDS Aurora with KMS encryption. Migrate to OpenSearch Service with encryption at rest. Add HTTPS listener to ALB with ACM certificate.

#### SEC-Q9: API Authentication
- **Score**: 4/4 ✅
- **Finding**: JWT authentication required for all endpoints except health check and documentation ([SecurityConfig.java:38-42](src/main/java/com/todo/app/config/SecurityConfig.java#L38-L42)). Cognito JWT validation via JWKS ([application.properties:25](src/main/resources/application.properties#L25)). Stateless authentication.
- **Gap**: None. Every API endpoint is authenticated.
- **Recommendation**: Maintain this pattern. Consider adding OAuth2 scopes for fine-grained permission control as agent capabilities expand.

#### SEC-Q10: Centralized Identity
- **Score**: 4/4 ✅
- **Finding**: AWS Cognito User Pool configured ([cognito.tf:2-27](terraform/cognito.tf#L2-L27)) with strong password policy. User Pool Client configured for JWT auth ([cognito.tf:30-53](terraform/cognito.tf#L30-L53)). Application integrates via JWKS endpoint.
- **Gap**: None. Centralized identity with industry-standard protocols.
- **Recommendation**: Consider enabling MFA for enhanced security. Add Cognito advanced security features (adaptive authentication, compromised credentials check).

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray SDK in dependencies ([pom.xml](pom.xml)). No OpenTelemetry imports. No trace context propagation headers. Logs have structured fields but no trace IDs.
- **Gap**: Cannot trace request flow end-to-end. Agent interactions spanning multiple services (after microservices migration) will be opaque.
- **Recommendation**: Add AWS X-Ray SDK for Java. Instrument all HTTP requests, database calls, and external service calls. Propagate `X-Amzn-Trace-Id` header across service boundaries.

#### OPS-Q2: Structured Logging
- **Score**: 4/4 ✅
- **Finding**: JSON structured logging with Logstash encoder ([logback-spring.xml:9-14](src/main/resources/logback-spring.xml#L9-L14)). Structured arguments used consistently ([TodoService.java:76-77,131-132](src/main/java/com/todo/app/service/TodoService.java#L76-L77)). CloudWatch Logs integration.
- **Gap**: None. Logs are fully structured and searchable.
- **Recommendation**: Maintain this practice. Add trace ID field once X-Ray integration is implemented. Excellent foundation for agent debugging.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: Zero test files found (0 Java test files). No eval framework, no golden datasets, no LLM-as-judge patterns. Maven build skips tests ([build.sh:13](build.sh#L13)).
- **Gap**: No automated validation of API behavior or agent interactions. Cannot safely evolve system.
- **Recommendation**: Immediately add integration tests for CRUD operations, authentication, and search. Create golden dataset of TODO queries with expected results. Implement eval pipeline in CI/CD to validate search quality after embedding model changes.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch alarms defined in Terraform. No SLO definitions. ALB has health checks ([compute.tf:23-31](terraform/compute.tf#L23-L31)) but no latency/error rate alarms.
- **Gap**: No alerting on degraded service. Team unaware of performance issues until user reports.
- **Recommendation**: Define SLOs for critical operations (e.g., "99.9% of TODO create requests complete in <500ms"). Create CloudWatch alarms for p99 latency, 5xx error rate >1%, and unhealthy target count >0.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: Manual deployment script ([deploy.sh](deploy.sh)) with systemctl restart. No blue/green, no canary, no automated rollback. No deployment tracking.
- **Gap**: Failed deployment requires manual intervention. No safe rollback mechanism. Cannot quickly revert bad agent prompt changes.
- **Recommendation**: After ECS migration, implement blue/green deployment with CodeDeploy. Configure automatic rollback on CloudWatch alarm breach (5xx errors, p99 latency spike).

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage (mock embeddings). No token counting code. No cost attribution tags or metrics.
- **Gap**: Once Bedrock is integrated, no way to track token usage or attribute costs to users/features.
- **Recommendation**: After Bedrock integration, log token counts from API responses (`usage.input_tokens`, `usage.output_tokens`). Emit CloudWatch custom metrics with dimensions (user_id, operation, model). Track cost per user for billing.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: Application logs operation counts ([TodoService.java:75-77](src/main/java/com/todo/app/service/TodoService.java#L75-L77)) but doesn't emit CloudWatch metrics. No custom metrics for business KPIs (TODO completion rate, search success rate, user engagement).
- **Gap**: Only infrastructure metrics available (CPU, memory). Cannot measure business outcomes or agent effectiveness.
- **Recommendation**: Emit CloudWatch custom metrics: `todos_created`, `search_queries`, `search_results_returned`, `todos_completed_rate`. Create CloudWatch dashboard for business KPIs.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection enabled. No alarms on error rates or latency. Basic health check only ([compute.tf:23-31](terraform/compute.tf#L23-L31)).
- **Gap**: Subtle performance degradation or increased error rates go unnoticed.
- **Recommendation**: Enable CloudWatch anomaly detection on ALB TargetResponseTime (p99), ALB HTTPCode_Target_5XX_Count, and custom business metrics. Configure alarms to trigger on anomaly detection.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Direct deployment to production via SSH ([deploy.sh:34-45](deploy.sh#L34-L45)). Systemctl restart immediately cuts over traffic. No gradual rollout, no canary testing.
- **Gap**: All users immediately exposed to new version. High risk of widespread impact from bugs.
- **Recommendation**: After ECS migration, implement canary deployment (10% traffic for 10 minutes, then 50%, then 100%). Configure automatic rollback on alarm breach.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: Zero test files found. Maven build explicitly skips tests with `-DskipTests` flag ([build.sh:13](build.sh#L13)). No integration test suite, no API contract tests.
- **Gap**: No automated validation of critical user journeys. High risk of regression.
- **Recommendation**: Create integration test suite using Spring Boot Test + TestContainers for MySQL and ElasticSearch. Test critical workflows: create TODO → search → retrieve → update → delete. Run in CI pipeline before deployment.

---

## Appendix: Evidence Index

Key files examined during assessment:

1. **[pom.xml](pom.xml)** — Maven dependencies, Java version 13, Spring Boot 2.3.12, OpenAPI, ElasticSearch, Cognito SDK
2. **[README.md](README.md)** — Architecture overview, confirms EC2-based deployment, self-managed databases
3. **[terraform/main.tf](terraform/main.tf)** — Terraform provider configuration, AWS region settings
4. **[terraform/compute.tf](terraform/compute.tf)** — EC2 instances (app, MySQL, ElasticSearch), ALB configuration, target groups
5. **[terraform/network.tf](terraform/network.tf)** — VPC, subnets (public/private), NAT Gateway, security groups
6. **[terraform/iam.tf](terraform/iam.tf)** — IAM roles for EC2, policies for CloudWatch and Cognito access
7. **[terraform/cognito.tf](terraform/cognito.tf)** — Cognito User Pool and Client configuration
8. **[terraform/cloudwatch.tf](terraform/cloudwatch.tf)** — CloudWatch Log Group with 7-day retention
9. **[terraform/variables.tf](terraform/variables.tf)** — Configuration variables including secret management gaps
10. **[build.sh](build.sh)** — Manual build script that skips tests
11. **[deploy.sh](deploy.sh)** — Manual SSH-based deployment script
12. **[src/main/java/com/todo/app/controller/TodoController.java](src/main/java/com/todo/app/controller/TodoController.java)** — REST API endpoints with OpenAPI annotations
13. **[src/main/java/com/todo/app/service/TodoService.java](src/main/java/com/todo/app/service/TodoService.java)** — Business logic, synchronous operations, PII logging
14. **[src/main/java/com/todo/app/service/ElasticSearchService.java](src/main/java/com/todo/app/service/ElasticSearchService.java)** — Vector search implementation, dense_vector configuration
15. **[src/main/java/com/todo/app/service/EmbeddingService.java](src/main/java/com/todo/app/service/EmbeddingService.java)** — Mock embeddings using SHA-256 hash
16. **[src/main/java/com/todo/app/config/OpenApiConfig.java](src/main/java/com/todo/app/config/OpenApiConfig.java)** — OpenAPI specification configuration
17. **[src/main/java/com/todo/app/config/SecurityConfig.java](src/main/java/com/todo/app/config/SecurityConfig.java)** — JWT authentication, endpoint security rules
18. **[src/main/resources/application.properties](src/main/resources/application.properties)** — Application configuration, database credentials in env vars
19. **[src/main/resources/logback-spring.xml](src/main/resources/logback-spring.xml)** — Structured JSON logging configuration with CloudWatch
20. **[src/main/java/com/todo/app/repository/TodoRepository.java](src/main/java/com/todo/app/repository/TodoRepository.java)** — JPA repository pattern for data access

---

**End of Report**
