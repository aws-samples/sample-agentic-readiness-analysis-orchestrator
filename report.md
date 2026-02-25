# Agentic Readiness Assessment Report
**Target**: TODO Application (Java/Spring Boot Monolith)  
**Date**: February 24, 2025  
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Top Priorities (Critical Gaps)](#top-priorities-critical-gaps)
3. [Readiness Roadmap](#readiness-roadmap)
   - [Phase 1 — Quick Wins (Days 1–30)](#phase-1--quick-wins-days-130)
   - [Phase 2 — Foundation (Months 1–3)](#phase-2--foundation-months-13)
   - [Phase 3 — Agent Enablement (Months 3–6)](#phase-3--agent-enablement-months-36)
4. [Recommended Self-Paced Learning Materials](#recommended-self-paced-learning-materials)
5. [Detailed Findings](#detailed-findings)
   - [Infrastructure & Platform](#infrastructure--platform)
   - [Application Architecture](#application-architecture)
   - [Data Foundations](#data-foundations)
   - [Identity, Security & Governance](#identity-security--governance)
   - [Operations & Observability](#operations--observability)
6. [Appendix: Evidence Index](#appendix-evidence-index)

---

## Executive Summary

This TODO application demonstrates foundational software engineering practices but is not yet ready for agentic workloads. The application runs on self-managed EC2 instances with manual deployments, lacks AI/agent framework integration entirely, and has significant gaps in async messaging, workflow orchestration, and operational observability. Strong points include comprehensive OpenAPI documentation, JWT-based authentication with AWS Cognito, good network segmentation, and structured JSON logging. However, critical blocking gaps prevent agentic implementation: no Amazon Bedrock or LLM integration, no workflow orchestration for multi-step agent workflows, completely manual CI/CD, and no distributed tracing or evaluation frameworks essential for agent quality assurance.

### Overall Score: 1.72 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.5 / 4.0 | 🟠 |
| Application Architecture | 1.69 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟡 |
| Identity, Security & Governance | 2.1 / 4.0 | 🟡 |
| Operations & Observability | 1.3 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

### 1. No AI/Agent Framework Integration

**What it is**: The application has zero integration with AI or agent frameworks. No Amazon Bedrock SDK, no LangChain, no Spring AI. The `EmbeddingService.java` uses a placeholder hash-based implementation instead of real ML embeddings.

**Why it matters for agentic workloads**: This is the fundamental blocking gap. Without LLM integration, the system cannot function as an agentic application. Agents require foundation model access for reasoning, natural language understanding, and decision-making. The placeholder embedding cannot generate meaningful semantic vectors for RAG.

**First concrete step**: Add AWS SDK for Java v2 Bedrock Runtime dependency to `pom.xml`. Create `BedrockService.java` to invoke foundation models. Replace `EmbeddingService.java` with Bedrock Titan Embeddings API calls. Test with TODO description embedding generation.

### 2. No Workflow Orchestration

**What it is**: No dedicated workflow orchestration (AWS Step Functions, Temporal). All business logic in `TodoService.java` is hardcoded synchronous method calls without state management, error handling, or human-in-the-loop capabilities.

**Why it matters for agentic workloads**: Agentic systems execute multi-step workflows involving multiple LLM calls, conditional branching, human approvals, and long-running operations (>30 seconds). Without orchestration, these workflows cannot be implemented reliably. Hardcoded logic lacks failure handling, state persistence, and execution visibility.

**First concrete step**: Define Step Functions state machine in Terraform for TODO creation workflow as proof-of-concept. Break workflow into states: ValidateTodo → SaveToDatabase → GenerateEmbedding → IndexInSearch, each with error handling and retries.

### 3. Manual Deployment with No CI/CD

**What it is**: Deployment is completely manual using `build.sh` and `deploy.sh` scripts that SCP files to EC2 and restart services via SSH. No GitHub Actions, CodePipeline, or any automated pipeline. Tests are explicitly skipped (`-DskipTests` in `build.sh`).

**Why it matters for agentic workloads**: Agentic systems require rapid iteration on prompts, models, and workflows. Manual deployment creates friction, prevents continuous deployment, blocks automated testing, and increases human error risk. Agent applications need automated A/B testing of prompts and models, impossible without CI/CD.

**First concrete step**: Create `buildspec.yml` for AWS CodeBuild. Create CodePipeline in Terraform to trigger on Git commits, run tests, build artifacts, and deploy to ECS or EC2 with automated rollback on failure.

### 4. No Async Messaging Infrastructure

**What it is**: No managed messaging (SQS, SNS, EventBridge). All operations in `TodoService.java` are synchronous and blocking. Embedding generation and ElasticSearch indexing happen in-transaction with database writes.

**Why it matters for agentic workloads**: LLM calls can take 5-30 seconds—blocking users if synchronous. Agents publish events triggering multiple workflows (e.g., TODO creation triggers embedding, notification, analytics). Message queues enable independent scaling and natural retry/dead-letter capabilities essential for resilient agents. Synchronous coupling prevents multi-agent systems.

**First concrete step**: Add SQS queue in Terraform for embedding generation. Modify `TodoService.java` to publish messages instead of calling `elasticSearchService.indexTodo()` synchronously. Create Lambda or ECS worker to consume queue and generate embeddings asynchronously.

### 5. No Encryption at Rest and Secrets in Environment Variables

**What it is**: Database credentials stored in Terraform variables and passed as environment variables (in `terraform/compute.tf` user-data). All data at rest (MySQL, ElasticSearch) is unencrypted. No AWS Secrets Manager, no KMS keys, no encrypted EBS volumes.

**Why it matters for agentic workloads**: Agents often process sensitive customer data, PII, and proprietary information. Exposing secrets in environment variables risks leakage through process listings, logs, or Terraform state. Unencrypted data violates compliance requirements (GDPR, HIPAA, PCI-DSS). Agent prompts themselves may be intellectual property requiring protection.

**First concrete step**: Create AWS Secrets Manager secrets in Terraform for database passwords. Update user-data scripts to retrieve secrets via AWS CLI. Create KMS customer-managed keys. Enable EBS encryption on all EC2 instances.

---

## Readiness Roadmap

### Phase 1 — Quick Wins (Days 1–30)

**1. Add Correlation IDs to Logging** (2-3 days)
- Implement servlet filter to generate X-Correlation-ID for each request
- Add to MDC for automatic inclusion in all logs
- Propagate to ElasticSearch and MySQL calls
- Impact: Immediate debugging improvement

**2. Implement Integration Tests** (3-5 days)
- Add Testcontainers for MySQL and ElasticSearch
- Create integration test suite for TODO CRUD workflow
- Remove `-DskipTests` from build.sh
- Impact: Catch integration issues pre-deployment

**3. Add CloudWatch Alarms for Basic Monitoring** (2-3 days)
- Create Terraform resources for ALB 5xx error rate alarms
- Add p99 latency alarms
- Configure SNS for alarm notifications
- Impact: Immediate production issue visibility

**4. Implement API Versioning** (2-3 days)
- Refactor `/api/todos` to `/api/v1/todos`
- Update OpenAPI spec
- Document versioning and deprecation policy
- Impact: Enable API evolution without breaking changes

**5. Migrate Secrets to AWS Secrets Manager** (3-4 days)
- Create Secrets Manager secrets in Terraform
- Update user-data scripts to retrieve via AWS CLI
- Update application with Spring Cloud AWS Secrets Manager
- Impact: Eliminate credential exposure risk

**Total Phase 1 Duration**: 2-4 weeks

---

### Phase 2 — Foundation (Months 1–3)

**Dependencies explicitly noted:**

**1. Containerize the Application** (1-2 weeks) — *Prerequisite for items 2, 3, 5*
- Create Dockerfile for Spring Boot application
- Create Docker Compose for local development
- Build and test container images
- **No dependencies**

**2. Migrate to Amazon ECS with Fargate** (2-3 weeks) — *Depends on: Containerization*
- Define ECS task definitions and service in Terraform
- Configure ALB target group for ECS
- Deploy containerized application
- Impact: Eliminates EC2 management, enables auto-scaling

**3. Implement CI/CD Pipeline with CodePipeline** (2-3 weeks) — *Depends on: Containerization*
- Create buildspec.yml for CodeBuild
- Create CodePipeline in Terraform
- Configure automated triggers on Git commits
- Add CodeDeploy for blue/green deployments
- Impact: Automated testing and deployment

**4. Migrate MySQL to Amazon RDS** (2-3 weeks) — *Independent workstream*
- Create RDS MySQL with Multi-AZ, backups, encryption
- Use DMS for zero-downtime migration
- Update connection strings
- Impact: Automated backups, patching, HA

**5. Implement Auto-Scaling for ECS** (1 week) — *Depends on: ECS migration*
- Configure ECS Service auto-scaling with target tracking
- Set min/max capacity (e.g., min=2, max=10)
- Test under load
- Impact: Automatic capacity adjustment

**6. Migrate ElasticSearch to Amazon OpenSearch Service** (2-3 weeks) — *Independent*
- Create OpenSearch domain with k-NN plugin, Multi-AZ
- Migrate index via snapshot/restore
- Update connection configuration
- Impact: Managed vector database, reduced operational burden

**7. Enable Encryption at Rest** (1 week) — *Depends on: RDS and OpenSearch migrations*
- Create KMS customer-managed keys
- Enable EBS encryption on ECS instances
- RDS and OpenSearch encryption enabled during migration
- Impact: Security compliance

**8. Implement SQS for Async Processing** (2-3 weeks) — *Independent*
- Create SQS queue for embedding generation
- Modify TodoService to publish messages
- Create Lambda/ECS worker to consume and process
- Impact: Decouple embedding generation, improve responsiveness

**Total Phase 2 Duration**: 10-12 weeks (parallel workstreams)

**Critical Path**: Containerization → ECS Migration → CI/CD Pipeline → Auto-scaling

---

### Phase 3 — Agent Enablement (Months 3–6)

**Dependencies on Phase 2 foundations:**

**1. Integrate Amazon Bedrock for LLM Access** (2-3 weeks) — *Depends on: Secrets Manager (Phase 1), SQS (Phase 2)*
- Add AWS SDK for Java v2 Bedrock Runtime
- Create BedrockService for invoking models
- Replace placeholder EmbeddingService with Bedrock Titan Embeddings
- Store Bedrock keys in Secrets Manager
- Impact: Real vector embeddings and LLM capabilities

**2. Implement AWS Step Functions for Workflow Orchestration** (3-4 weeks) — *Depends on: Bedrock, SQS*
- Define Step Functions state machines in Terraform
- Create Lambda functions for workflow steps
- Integrate with SQS for async jobs
- Add human-in-the-loop approval tasks
- Impact: Enable complex multi-step agentic workflows

**3. Implement Full RAG Pipeline** (4-5 weeks) — *Depends on: Bedrock, OpenSearch, Step Functions*
- Add document chunking logic
- Implement semantic search with Bedrock embeddings and OpenSearch k-NN
- Create RAG workflow: retrieve context → augment prompt → invoke LLM
- Add S3 for unstructured documents
- Integrate Amazon Textract for parsing
- Impact: Production-ready RAG for knowledge retrieval

**4. Implement Distributed Tracing with X-Ray** (1-2 weeks) — *Depends on: ECS migration*
- Add AWS X-Ray SDK dependencies
- Configure X-Ray daemon in ECS task definition
- Instrument Bedrock, OpenSearch, RDS calls
- Impact: End-to-end workflow visibility

**5. Implement Idempotency for Agent Actions** (2-3 weeks) — *Depends on: RDS migration*
- Add idempotency key support (Idempotency-Key header)
- Store processed keys in RDS or DynamoDB with TTL
- Implement checking middleware
- Impact: Safe retries for agent actions

**6. Implement LLM Cost Tracking and Business Metrics** (2-3 weeks) — *Depends on: Bedrock*
- Extract token counts from Bedrock responses
- Publish custom CloudWatch metrics per user/feature/model
- Create cost dashboards and budget alerts
- Track business KPIs (creation rate, search effectiveness)
- Impact: Cost control and business outcome visibility

**7. Implement Automated Agent Evaluation Framework** (3-4 weeks) — *Depends on: Bedrock, Step Functions*
- Create golden test dataset with expected queries/responses
- Implement LLM-as-judge using Bedrock
- Integrate into CI/CD pipeline
- Create evaluation metrics dashboard
- Impact: Continuous quality assurance for agents

**Total Phase 3 Duration**: 12-16 weeks (parallel workstreams)

**Critical Path**: Bedrock Integration → Step Functions → RAG Pipeline → Evaluation Framework

---

## Recommended Self-Paced Learning Materials

### Modernizing to Containers
This application runs on raw EC2 instances and needs containerization as a prerequisite for ECS migration and modern deployment practices.

- **Introduction to Containers** — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5  
  *Why helpful*: Provides foundational understanding of containers necessary for migrating the Spring Boot monolith to Docker and ECS.

- **AWS Modernization Pathways: Move to Containers with Amazon ECS** — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN  
  *Why helpful*: Comprehensive learning path for migrating this EC2-based Java application to ECS with Fargate, addressing INF-Q1 (Compute) gap.

- **Amazon EKS Primer** — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72  
  *Why helpful*: Alternative containerization path if Kubernetes is preferred over ECS for future microservices decomposition.

### Modernizing to Managed Databases
MySQL and ElasticSearch are self-managed on EC2, creating operational burden and reliability risks.

- **AWS Modernization Pathways: Move to Managed Databases** — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV  
  *Why helpful*: Guides migration from self-managed MySQL on EC2 to Amazon RDS, addressing INF-Q2 (Databases) and SEC-Q8 (Encryption at Rest) gaps.

- **Migrating RDS MySQL to Aurora (Lab)** — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK  
  *Why helpful*: Provides hands-on experience for eventual Aurora migration, which offers better performance for vector workloads.

- **Introduction to Building with AWS Databases** — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91  
  *Why helpful*: Covers managed database best practices, backup strategies, and encryption that this application currently lacks.

### Modernizing to Modern DevOps
Deployment is completely manual with no CI/CD pipeline, blocking rapid agent iteration.

- **AWS Modernization Pathways: Move to Modern DevOps** — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK  
  *Why helpful*: Comprehensive DevOps modernization addressing INF-Q6 (CI/CD) gap, essential for agent prompt/model iteration.

- **Getting Started with DevOps on AWS** — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R  
  *Why helpful*: Introduces CodePipeline, CodeBuild, and CodeDeploy needed to automate build.sh and deploy.sh processes.

- **Create a CI/CD Pipeline to Deploy to AWS Fargate** — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5  
  *Why helpful*: Directly applicable to Phase 2 roadmap item combining ECS migration with CI/CD implementation.

### Modernizing to AI
The application has no AI/agent framework integration whatsoever—the most critical gap.

- **AWS Modernization Pathways: Move to AI** — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63  
  *Why helpful*: Comprehensive AI modernization path addressing APP-Q13 (AI/Agent Frameworks) blocking gap.

- **Amazon Bedrock Getting Started** — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE  
  *Why helpful*: Essential for Phase 3 Bedrock integration, replacing the placeholder EmbeddingService with real Titan Embeddings.

- **Introduction to Agentic AI on AWS** — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY  
  *Why helpful*: Directly addresses agentic readiness, covering agent patterns, workflows, and Step Functions orchestration needed for Phase 3.

- **Introduction to Generative AI: Art of the Possible** — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U  
  *Why helpful*: Foundational understanding of generative AI capabilities and use cases for TODO application agent features.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: Application uses raw EC2 instances for all compute. In `terraform/compute.tf`, three `aws_instance` resources are defined: app (t3.medium), mysql (t3.small), and elasticsearch (t3.medium). No EKS, ECS, Lambda, or containerization present. Deployment via `deploy.sh` uses SCP and SSH.
- **Gap**: 100% EC2-based compute with no managed orchestration or serverless. Prevents elastic scaling essential for variable agent workloads.
- **Recommendation**: Containerize application and migrate to Amazon ECS with Fargate. First step: Create Dockerfile, then define ECS task definitions in Terraform.

#### INF-Q2: Databases
- **Score**: 1/4 ❌
- **Finding**: MySQL is self-managed on EC2 (`aws_instance.mysql` in `terraform/compute.tf`). User-data script installs MySQL. Credentials passed as template variables. No RDS, Aurora, DynamoDB, or DocumentDB.
- **Gap**: Self-managed database without automated backups, patching, HA, or point-in-time recovery. Operational burden and reliability risk.
- **Recommendation**: Migrate to Amazon RDS for MySQL with Multi-AZ, automated backups, and encryption. First step: Create RDS instance in Terraform, use DMS for migration.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service. Business logic in `TodoService.java` is direct method calls without state management. No Step Functions, Temporal, or Camunda in `pom.xml` or Terraform.
- **Gap**: Cannot implement multi-step agentic workflows with retries, timeouts, conditional logic, or human approvals.
- **Recommendation**: Integrate AWS Step Functions for multi-step workflows. First step: Define state machine in Terraform for TODO creation: validation → save → embed → index with error handling.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No managed messaging. No SQS, SNS, EventBridge, or Kafka dependencies in `pom.xml`. All operations synchronous in `TodoService.java`: `elasticSearchService.indexTodo(savedTodo)` is blocking call in transaction.
- **Gap**: No async communication infrastructure. Forces tight coupling, prevents independent scaling, blocks event-driven agent patterns.
- **Recommendation**: Implement Amazon SQS for background tasks. First step: Add SQS queue in Terraform, publish TODO events to queue, create Lambda consumer for async embedding generation.

#### INF-Q5: IaC Coverage
- **Score**: 3/4 🟡
- **Finding**: Strong IaC coverage. `terraform/network.tf` defines VPC, subnets, security groups. `terraform/compute.tf` defines instances, ALB. `terraform/cognito.tf` defines identity. `terraform/iam.tf` defines roles. Estimated 85% coverage, but user-data scripts contain configuration.
- **Gap**: User-data scripts not easily versioned or tested. No configuration management.
- **Recommendation**: Complete IaC coverage with Packer for pre-baked AMIs or full containerization. First step: Create Packer templates to build AMIs with dependencies pre-installed.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No automated CI/CD. `build.sh` runs Maven locally with `-DskipTests`. `deploy.sh` uses SCP/SSH for manual deployment. No GitHub Actions, CodePipeline, or CI infrastructure.
- **Gap**: Manual deployment creates inconsistency risk, prevents rapid iteration, blocks automated testing essential for agent prompt tuning.
- **Recommendation**: Implement AWS CodePipeline with CodeBuild and CodeDeploy. First step: Create `buildspec.yml`, configure pipeline to trigger on Git commits, deploy to ECS.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Application Load Balancer is entry point (`aws_lb.main` in `terraform/compute.tf`). Listener forwards port 80 to port 8080. However, no throttling, no WAF, no request validation. Security group allows `0.0.0.0/0` in `terraform/network.tf`.
- **Gap**: Basic load balancing but lacks throttling, request validation, and DDoS protection essential for agent API calls.
- **Recommendation**: Add Amazon API Gateway with throttling and request validation, or add WAF to ALB. First step: Create API Gateway REST API in Terraform with usage plans defining rate limits.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No streaming service. No Kinesis or MSK resources in Terraform. No Kafka/Kinesis dependencies in `pom.xml`. All processing is request-response.
- **Gap**: No streaming capability for event-driven data processing that benefits agent telemetry and real-time learning.
- **Recommendation**: Evaluate need for streaming. If needed, implement Amazon Kinesis Data Streams. First step: Add Kinesis stream in Terraform, publish TODO events for downstream analytics.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: Good network segmentation in `terraform/network.tf`: VPC (10.0.0.0/16), public subnet (10.0.1.0/24) for ALB, private subnet (10.0.2.0/24) for app/DB/ES. Security groups properly scoped: ALB → App (8080), App → MySQL (3306), App → ES (9200). However, default `allowed_cidr_blocks = ["0.0.0.0/0"]` in `terraform/variables.tf`.
- **Gap**: Default configuration allows public access. Security groups well-structured but default CIDR too permissive.
- **Recommendation**: Remove default CIDR, require explicit configuration. Implement AWS WAF. First step: Update `terraform/variables.tf` to require CIDR blocks, add WAF with rate-based rules.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No auto-scaling configured. Single EC2 instances in `terraform/compute.tf` with no ASG. No ECS Service auto-scaling. ALB has single static target.
- **Gap**: Fixed capacity cannot handle variable agent workload. Over-provisioning wastes cost, under-provisioning causes performance issues.
- **Recommendation**: Implement Auto Scaling Groups or ECS Service auto-scaling. First step: Create ASG in Terraform with scaling policies based on CPU or custom metrics.

---

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Application is Java 13 (specified in `pom.xml` properties: `<java.version>13</java.version>`). Uses Spring Boot 2.3.12. No Python or TypeScript.
- **Gap**: Java has less mature agent framework ecosystem compared to Python (LangChain, CrewAI) or TypeScript (LangChain.js).
- **Recommendation**: While Java is acceptable, consider Python microservices for AI/agent capabilities. First step: Evaluate Bedrock Java SDK (AWS SDK v2) or create Python service for agents communicating via REST.

#### APP-Q2: API Documentation
- **Score**: 4/4 ✅
- **Finding**: Comprehensive OpenAPI documentation. `OpenApiConfig.java` has `@OpenAPIDefinition` with metadata. `TodoController.java` has detailed `@Operation`, `@ApiResponse`, `@Parameter` annotations. SpringDoc OpenAPI UI 1.5.9 in `pom.xml`. Paths configured: `/api-docs`, `/swagger-ui.html`.
- **Gap**: None. Documentation is comprehensive and current.
- **Recommendation**: Maintain as single source of truth. Consider generating client SDKs from spec for agent integration. First step: Add OpenAPI spec export to CI/CD pipeline.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous communication. In `TodoService.java`, `elasticSearchService.indexTodo(savedTodo)` is blocking call. All database operations via `todoRepository` are synchronous JPA. No message queue producers, no async patterns. Ratio: 0% async, 100% sync.
- **Gap**: Tight coupling prevents independent scaling. LLM calls (5-30 seconds) cannot be async. Blocks event-driven agent architectures.
- **Recommendation**: Introduce async processing for non-critical operations. First step: Add Spring Boot `@Async` for embedding operations or integrate SQS for background jobs.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: Monolithic architecture. Single JAR (`<packaging>jar</packaging>` in `pom.xml`). Single `TodoApplication.java` entry point. All services run in same process.
- **Gap**: Limits independent scaling, deployment, and technology choices. Agents benefit from microservices to isolate AI components and enable polyglot development.
- **Recommendation**: Decompose into microservices. First step: Extract embedding and search into separate "Search Service" microservice, containerize independently.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All responses are JSON. `TodoResponse.java` uses Jackson annotations (`@JsonFormat`). Spring Boot auto-configures JSON serialization. No XML or binary formats.
- **Gap**: None. Structured JSON is ideal for agent consumption.
- **Recommendation**: Maintain consistent JSON format. Consider JSON Schema validation. First step: Document schemas in OpenAPI (already done), add validation in tests.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: Workflow logic is hardcoded in `TodoService.java`: direct method calls like `todoRepository.save(todo); elasticSearchService.indexTodo(savedTodo);` with no error handling or state management. No orchestration dependencies.
- **Gap**: Complex agent workflows with conditional logic, parallel execution, retries, and human approvals cannot be implemented.
- **Recommendation**: Integrate AWS Step Functions. First step: Model TODO creation as state machine: Validate → Save → Embed → Index with error handling per state.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency implementation. No `Idempotency-Key` headers in `TodoController.java`. No token checking in `TodoService.java`. POST requests can create duplicates if retried. No idempotency key field in `TodoRequest.java`.
- **Gap**: Retries create duplicate records. Critical for agents that may retry failed operations.
- **Recommendation**: Implement idempotency keys for all writes. First step: Add `Idempotency-Key` header validation, store processed keys in Redis/DynamoDB with TTL, check before processing.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. No API Gateway usage plans in Terraform. No rate limiting middleware in `SecurityConfig.java`. No Bucket4j or Resilience4j rate limiter in `pom.xml`. ALB has no throttling.
- **Gap**: No protection against API abuse or excessive agent calls. Cost overruns and service degradation risk.
- **Recommendation**: Implement API Gateway with usage plans. First step: Create `aws_api_gateway_rest_api` with `aws_api_gateway_usage_plan` defining throttle limits (e.g., 1000 req/sec burst, 500 steady).

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No resilience patterns. ElasticSearch client calls in `ElasticSearchService.java` have no timeouts: `client.index(request, RequestOptions.DEFAULT)`. No circuit breakers, no retry logic, no Resilience4j or Hystrix in `pom.xml`.
- **Gap**: External service failures cascade. Critical for agents integrating with LLM APIs with variable latency.
- **Recommendation**: Implement Resilience4j for circuit breakers, retries, timeouts. First step: Add Resilience4j dependency, configure circuit breaker for ElasticSearch with fallback, add retry with exponential backoff.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: Current operations complete quickly (<30s). `EmbeddingService.generateEmbedding()` is synchronous but fast. No infrastructure for handling long operations. No background job framework, no job status API.
- **Gap**: When LLM calls are added (5-30+ seconds), no async job handling capability. Blocks implementing complex agent reasoning.
- **Recommendation**: Implement async job processing with status tracking. First step: Add Spring Boot async execution or SQS. Create job status API returning job ID with polling endpoint.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No versioning strategy. Controller mapping is `/api/todos` (no version prefix in `TodoController.java`). No `Accept-Version` header handling. OpenAPI metadata has `version = "1.0.0"` but not enforced in URLs.
- **Gap**: Cannot evolve API without breaking existing agent integrations. Multiple agent versions cannot coexist.
- **Recommendation**: Implement URL-based versioning. First step: Refactor to `/api/v1/todos`, update OpenAPI spec, document versioning policy with deprecation timeline.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Service endpoints configured via environment variables in `application.properties`: `spring.datasource.url`, `elasticsearch.host`. No service registry. No AWS Cloud Map, Consul, or App Mesh. Static configuration but environment-based.
- **Gap**: Endpoints environment-based but not dynamically discovered. Adding services requires configuration updates. No service mesh for advanced traffic management.
- **Recommendation**: Implement AWS Cloud Map for service discovery. First step: Create Cloud Map namespace in Terraform, register services, query Cloud Map for endpoints instead of static env vars.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: Zero AI/agent framework integration. No Bedrock SDK, no LangChain, no Spring AI in `pom.xml`. `EmbeddingService.java` uses placeholder hash-based generation, not real ML model.
- **Gap**: Most critical blocking gap. Cannot integrate with LLMs or implement agent reasoning. Placeholder embeddings are meaningless for RAG.
- **Recommendation**: Integrate Amazon Bedrock SDK. First step: Add AWS SDK v2 Bedrock Runtime to `pom.xml`, create BedrockService for model invocation, replace EmbeddingService with Bedrock Titan Embeddings.

---

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 2/4 🟠
- **Finding**: ElasticSearch configured with vector storage. In `ElasticSearchService.java`, index mapping includes `"type": "dense_vector"` with `"dims": 128`. Self-hosted ElasticSearch 7.13.4 on EC2 (`aws_instance.elasticsearch` in `terraform/compute.tf`). Not OpenSearch with k-NN, not Aurora pgvector, not Bedrock Knowledge Bases.
- **Gap**: Vector database exists but self-hosted ElasticSearch rather than managed service. Lacks advanced k-NN features of OpenSearch.
- **Recommendation**: Migrate to Amazon OpenSearch Service with k-NN plugin. First step: Create OpenSearch domain in Terraform with k-NN enabled, migrate index, update connection config.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: Vector database (ElasticSearch) is self-hosted on EC2. User-data script installs ElasticSearch. Requires manual patching, scaling, backup management.
- **Gap**: Self-hosted creates operational burden. No automated backups, updates, multi-AZ, or scaling.
- **Recommendation**: Migrate to Amazon OpenSearch Service for fully managed vector database. First step: Define `aws_opensearch_domain` in Terraform with multi-AZ, automated snapshots, k-NN plugin.

#### DATA-Q3: RAG Implementation
- **Score**: 2/4 🟠
- **Finding**: Partial RAG infrastructure: embeddings generated (`EmbeddingService.java`), vectors stored (`ElasticSearchService.java`), semantic search implemented (`searchTodos()`). However: no document chunking, placeholder hash-based embeddings (not real ML model), no LLM integration for retrieval augmentation.
- **Gap**: Basic vector search infrastructure but no real embedding model, no document chunking, no LLM for generation phase of RAG.
- **Recommendation**: Implement proper RAG with Bedrock. First step: Replace `EmbeddingService` with Bedrock Titan Embeddings, add chunking logic, integrate Bedrock models for prompt augmentation.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Two distinct data sources: MySQL (via `TodoRepository.java` JPA) and ElasticSearch (via `ElasticSearchService.java` REST client). Both configured in `application.properties`.
- **Gap**: Two sources is reasonable, but no unified data access pattern. Services connect directly to both.
- **Recommendation**: While manageable, consider consolidating. First step: Evaluate if OpenSearch can serve both JSON documents and vector search, reducing to single source.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Data accessed via direct connections within service layer. `TodoRepository` (JPA) injected into `TodoService`. `ElasticSearchService` uses direct REST client. No dedicated data API layer.
- **Gap**: Direct database access from business logic. Tightly couples application to specific data stores.
- **Recommendation**: Implement dedicated Data Service API for RESTful data access. First step: Extract repository and ElasticSearch into separate Data Service microservice with REST endpoints.

#### DATA-Q6: Unstructured Data Handling
- **Score**: 1/4 ❌
- **Finding**: No unstructured data capability. No S3 in Terraform, no S3 SDK in `pom.xml`. No document parsing libraries (Textract, Tika, PDFBox). Only structured TODO items (title, description). No file upload in `TodoController.java`.
- **Gap**: Cannot process documents, PDFs, images. Agentic RAG often requires parsing various document types.
- **Recommendation**: Implement S3 with document parsing. First step: Add `aws_s3_bucket` in Terraform, create file upload endpoint, use Amazon Textract to extract text, chunk and embed.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: Schema partially documented. JPA entities (`TodoItem.java`) define schema with annotations. OpenAPI schemas in DTOs with validation. However, no explicit versioning (using `hibernate.ddl-auto=update` in `application.properties`). No Flyway or Liquibase. ElasticSearch mapping in code (`ElasticSearchService.java`) not versioned.
- **Gap**: Schema defined in code but not versioned or formally documented. No migration history.
- **Recommendation**: Implement Flyway for versioned migrations. First step: Add Flyway to `pom.xml`, convert current schema to initial migration, disable `hibernate.ddl-auto`, use Flyway for future changes.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Partial data access layer. `TodoRepository` interface (Spring Data JPA) abstracts MySQL. `ElasticSearchService` encapsulates ElasticSearch. Both injected into `TodoService`. However, no unified interface across sources, no caching, no read/write separation.
- **Gap**: Good abstraction per source but no unified pattern. No caching or query optimization layer.
- **Recommendation**: Strengthen with caching layer. First step: Add Spring Cache with Redis/ElastiCache to cache frequent TODO queries, reducing database load.

#### DATA-Q9: Embedding Freshness
- **Score**: 2/4 🟠
- **Finding**: Embeddings updated synchronously on modifications. In `TodoService.java`: `todoRepository.save(todo); elasticSearchService.indexTodo(savedTodo);` provides real-time updates. However, synchronous and tightly coupled. No event-driven refresh, no batch re-indexing. If embedding model updates, manual regeneration needed.
- **Gap**: Real-time but synchronous updates. No event-driven architecture for async refresh. Cannot re-index when embedding models evolve.
- **Recommendation**: Implement event-driven embedding updates. First step: Publish TODO change events to EventBridge, create Lambda to consume events and update embeddings asynchronously.

---

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Secrets in environment variables, not AWS Secrets Manager. In `terraform/compute.tf`, passwords passed as template variables to user-data. In `application.properties`: `spring.datasource.password=${MYSQL_PASSWORD:password}`. No `aws_secretsmanager_secret` in Terraform. README acknowledges: "Credentials in Environment Variables: In production, use AWS Secrets Manager".
- **Gap**: Secrets exposed in process listings, logs, Terraform state. Credential leakage risk.
- **Recommendation**: Migrate to AWS Secrets Manager. First step: Create `aws_secretsmanager_secret` resources in Terraform, update user-data to retrieve via AWS CLI, update app with Spring Cloud AWS Secrets Manager.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: IAM policies reasonably scoped in `terraform/iam.tf`. CloudWatch policy scoped to specific log group: `Resource = ["${aws_cloudwatch_log_group.app.arn}:*"]`. Cognito policy scoped to specific user pool. Actions are specific (not wildcards). However, `cognito-idp:ListUsers` may be too broad.
- **Gap**: Generally good but some actions like ListUsers may be unnecessary. No resource-level conditions.
- **Recommendation**: Further restrict policies. First step: Remove `cognito-idp:ListUsers` if not needed, add condition keys to CloudWatch policy (e.g., restrict by log stream prefix or instance tags).

#### SEC-Q3: Identity Propagation
- **Score**: 4/4 ✅
- **Finding**: JWT-based identity propagation well-implemented. In `JwtAuthenticationFilter.java`, JWT extracted, validated, userId propagated to `SecurityContextHolder`. In `SecurityUtils.java`, identity retrieved for data scoping. In `TodoService.java`, userId used: `SecurityUtils.getCurrentUserId(); todoRepository.findByUserId(userId)`.
- **Gap**: None. End-to-end JWT identity propagation properly implemented.
- **Recommendation**: Maintain current implementation. Consider adding claims like roles/groups for fine-grained authorization in agent workflows.

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: CloudWatch logging enabled (`terraform/cloudwatch.tf`: `aws_cloudwatch_log_group.app`, 7-day retention). Application logs sent to CloudWatch. In `TodoService.java`, operations logged: `logger.info("Todo operation performed", kv("operation", operation), kv("todoContent", todoJson))`. However, no CloudTrail. No `aws_cloudtrail` in Terraform. No immutable logs. No log file validation.
- **Gap**: Application logging exists but no CloudTrail for AWS API audit. Short retention. No immutable storage or integrity validation.
- **Recommendation**: Enable AWS CloudTrail with log file validation and immutable S3. First step: Add `aws_cloudtrail` in Terraform with S3 bucket having object lock, extend CloudWatch retention to 90+ days.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. No API Gateway with usage plans in Terraform. No rate limiting in `SecurityConfig.java`. No rate limiting libraries in `pom.xml`. ALB has no throttling. No WAF.
- **Gap**: No protection against API abuse. Agentic systems can generate high volumes, requiring rate limiting for cost control.
- **Recommendation**: Implement API Gateway with usage plans. First step: Create `aws_api_gateway_rest_api` with `aws_api_gateway_usage_plan` defining per-client rate limits (e.g., 100 req/sec burst, 50 steady).

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction. In `TodoService.java`, full TODO content logged: `logger.info(..., kv("todoContent", todoJson))`. TODOs may contain PII (names, emails). No PII masking, no log scrubbing. In `logback-spring.xml`, logs sent to CloudWatch without filtering. No Macie integration. README notes: "Full TODO content logged; consider PII implications".
- **Gap**: Full content logging without PII redaction. Compliance risk (GDPR, HIPAA). Agents often process sensitive data requiring protection.
- **Recommendation**: Implement PII redaction in logging. First step: Add Logback filter to detect and mask PII patterns (emails, phones, SSNs) before logging. Integrate Amazon Macie to scan CloudWatch logs for PII.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows. In `TodoController.java`, DELETE executes immediately: `todoService.deleteTodo(id); return ResponseEntity.noContent().build();`. No Step Functions with approval tasks, no approval endpoints, no admin review for high-risk operations.
- **Gap**: No human-in-the-loop for high-risk actions. Agents require approval workflows for critical operations (deletions, bulk changes, high-value transactions) to prevent autonomous errors.
- **Recommendation**: Implement Step Functions with human approval. First step: Create state machine with task token-based approval step for TODO deletions. Add approval API endpoints for admins.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No encryption at rest. In `terraform/compute.tf`, MySQL and ElasticSearch on EC2 have no EBS encryption specified (defaults to unencrypted). No `aws_kms_key` resources. No encryption in user-data scripts. README notes: "No Encryption: MySQL and ElasticSearch data should be encrypted at rest".
- **Gap**: All data at rest unencrypted. Critical security and compliance gap. Agents process sensitive data requiring encryption.
- **Recommendation**: Enable encryption with KMS. First step: Create `aws_kms_key` in Terraform, enable EBS encryption on EC2 instances with `encrypted = true` and `kms_key_id` in block device mappings.

#### SEC-Q9: API Authentication
- **Score**: 4/4 ✅
- **Finding**: API authentication well-implemented. In `SecurityConfig.java`: `.antMatchers("/api-docs/**", "/swagger-ui/**", "/actuator/health").permitAll()` `.anyRequest().authenticated()`. All endpoints except docs/health require auth. In `JwtAuthenticationFilter.java`, JWT validated per request: `Claims claims = jwtValidator.validateToken(jwt)`. Token validated against Cognito public keys, issuer verified.
- **Gap**: None. Per-request JWT authentication with proper validation.
- **Recommendation**: Maintain implementation. Consider adding RBAC for different agent types or user roles.

#### SEC-Q10: Centralized Identity
- **Score**: 3/4 🟡
- **Finding**: AWS Cognito used as centralized identity provider. In `terraform/cognito.tf`: `aws_cognito_user_pool.main` with password policy, email verification, username via email. Application validates tokens against Cognito in `CognitoJwtValidator.java`. However, no SSO integration, no federated identity providers (SAML, OIDC), no enterprise IdP integration.
- **Gap**: Centralized IdP present but no SSO or federation. Enterprise agentic systems often require SSO with corporate identity.
- **Recommendation**: Configure Cognito identity federation. First step: Add `aws_cognito_identity_provider` in Terraform to federate with Azure AD, Okta, or enterprise IdP, enabling SSO.

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing. No X-Ray SDK, OpenTelemetry, Spring Cloud Sleuth in `pom.xml`. No trace ID propagation in logs or HTTP headers. In `TodoService.java`, logs include structured args but no correlation/trace IDs.
- **Gap**: Cannot trace requests across service boundaries. Agentic workflows spanning multiple services cannot be traced for debugging or performance analysis.
- **Recommendation**: Integrate AWS X-Ray or OpenTelemetry. First step: Add X-Ray SDK to `pom.xml`, configure X-Ray daemon in Terraform, add X-Ray servlet filter, propagate trace context to ElasticSearch/MySQL calls.

#### OPS-Q2: Structured Logging
- **Score**: 3/4 🟡
- **Finding**: Structured logging well-implemented. In `logback-spring.xml`: `LogstashEncoder` with JSON format, MDC, structured arguments. In `TodoService.java`: `logger.info("Todo operation performed", kv("operation", operation), kv("userId", userId), kv("todoId", id))`. However, no correlation ID implementation, no trace ID propagation.
- **Gap**: Structured JSON logging present but no correlation IDs to link related logs across calls.
- **Recommendation**: Add correlation ID generation and propagation. First step: Implement servlet filter to generate/extract X-Correlation-ID from headers, add to MDC, propagate to downstream calls.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework. No test datasets, no eval scripts, no golden datasets, no LLM-as-judge patterns, no A/B testing infrastructure. Test directory `src/test/` is empty.
- **Gap**: No automated evaluation for agentic behavior. Cannot ensure quality, accuracy, safety of agent responses.
- **Recommendation**: Implement automated evaluation framework. First step: Create test dataset with golden TODO queries/responses. Use Bedrock to implement LLM-as-judge scoring. Integrate into CI/CD.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLOs defined. In `terraform/cloudwatch.tf`, only log group exists. No CloudWatch alarms for latency or availability. ALB health check exists in `terraform/compute.tf` but no SLO metrics, no error budget tracking, no p99/p95 latency targets.
- **Gap**: No SLOs for critical journeys. Cannot measure or track service quality objectives essential for reliable agent performance.
- **Recommendation**: Define and monitor SLOs. First step: Define SLOs (e.g., 99.9% availability, p95 latency < 200ms for TODO retrieval). Create CloudWatch alarms for error rate and latency thresholds.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No automated rollback. In `deploy.sh`: `sudo mv /tmp/todo-app.jar /opt/todo-app/todo-app.jar; sudo systemctl restart todo-app` is direct overwrite. No blue/green, canary, feature flags, version management, or rollback scripts. No CodeDeploy in Terraform.
- **Gap**: No rollback for failed deployments. Agentic systems with prompt engineering and config changes need quick rollback if performance degrades.
- **Recommendation**: Implement automated rollback with CodeDeploy. First step: Configure CodeDeploy in Terraform with automatic rollback on CloudWatch alarm triggers. Store multiple JAR versions for easy rollback.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM cost tracking (application doesn't use LLMs yet per APP-Q13). No infrastructure for token counting, cost attribution, CloudWatch custom metrics for LLM calls, or cost tracking in logs.
- **Gap**: No LLM cost tracking capability. When Bedrock is integrated, no visibility into token usage or cost attribution critical for agent cost control.
- **Recommendation**: Implement LLM cost tracking when Bedrock integrated. First step: Extract token counts from Bedrock response metadata, publish CloudWatch custom metrics per user/feature/model, create cost dashboards and budget alerts.

#### OPS-Q7: Business Metrics
- **Score**: 2/4 🟠
- **Finding**: Some business metrics logged but not published as CloudWatch metrics. In `TodoService.java`: `logger.info("Retrieved all todos", kv("count", responses.size())); logger.info("Search completed", kv("resultsCount", responses.size()))`. Logged but not measured. No CloudWatch `put_metric_data` calls, no custom business KPIs (completion rate, search effectiveness), only infrastructure metrics from ALB/EC2.
- **Gap**: Business events logged but not measured as metrics. Cannot create dashboards or alerts on business KPIs.
- **Recommendation**: Publish business metrics to CloudWatch. First step: Add CloudWatchAsyncClient, create metrics service to publish custom metrics (TodoCreated, SearchPerformed, CompletionRate), create dashboards.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection. In `terraform/cloudwatch.tf`, only log group exists. No CloudWatch alarms at all. No error rate alarms, latency alarms, CloudWatch Anomaly Detector, or composite alarms.
- **Gap**: No automated anomaly detection or alerting. Cannot proactively detect issues like error rate spikes or latency degradation critical for agent reliability.
- **Recommendation**: Implement CloudWatch alarms with anomaly detection. First step: Create alarms in Terraform for ALB 5xx error rate, target response time (p99), application error logs. Enable CloudWatch Anomaly Detector.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Direct-to-production deployment. In `deploy.sh`: `scp todo-app.jar ...; ssh ... 'sudo systemctl restart todo-app'` is single-step replacement with immediate restart. No blue/green, canary, gradual rollout, traffic shifting, or automated testing before full deployment.
- **Gap**: Direct-to-production with no safety net. High outage risk. Agentic systems need gradual rollout to detect quality regressions before full deployment.
- **Recommendation**: Implement blue/green or canary deployment. First step: Migrate to ECS with CodeDeploy. Configure canary traffic shifting (10% for 5 minutes, then 100%) with automatic rollback on error rate alarms.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No integration tests. `src/test/` directory is empty. No integration test suites, end-to-end tests, API contract tests, test containers. In `build.sh`: `mvn clean package -DskipTests` explicitly skips tests.
- **Gap**: No integration tests for critical workflows. Cannot verify components work together. Critical for agentic systems where multiple components (LLM, vector DB, orchestration) must coordinate.
- **Recommendation**: Implement integration test suite. First step: Add integration tests using Spring Boot Test and Testcontainers for MySQL/ElasticSearch. Test full TODO CRUD workflow including embedding and search. Run in CI pipeline.

---

## Appendix: Evidence Index

**Key files examined during this assessment:**

1. **pom.xml** — Maven dependencies revealing Spring Boot 2.3.12, Java 13, no AI frameworks, ElasticSearch 7.13.4 client
2. **terraform/compute.tf** — EC2 instances for app/MySQL/ElasticSearch, ALB configuration, no managed services
3. **terraform/network.tf** — VPC, subnets (public/private), security groups, NAT gateway configuration
4. **terraform/iam.tf** — IAM roles and policies for EC2 instances, CloudWatch logs, Cognito access
5. **terraform/cognito.tf** — Cognito user pool and client configuration for JWT authentication
6. **terraform/cloudwatch.tf** — CloudWatch log group with 7-day retention
7. **src/main/java/com/todo/app/TodoApplication.java** — Spring Boot application entry point
8. **src/main/java/com/todo/app/config/OpenApiConfig.java** — Comprehensive OpenAPI/Swagger configuration
9. **src/main/java/com/todo/app/config/SecurityConfig.java** — JWT authentication configuration, CORS settings
10. **src/main/java/com/todo/app/config/ElasticSearchConfig.java** — ElasticSearch REST client configuration
11. **src/main/java/com/todo/app/controller/TodoController.java** — REST API endpoints with OpenAPI annotations
12. **src/main/java/com/todo/app/service/TodoService.java** — Synchronous business logic, full content logging
13. **src/main/java/com/todo/app/service/ElasticSearchService.java** — Vector storage with dense_vector mapping (128 dims)
14. **src/main/java/com/todo/app/service/EmbeddingService.java** — Placeholder hash-based embedding (not real ML)
15. **src/main/java/com/todo/app/security/JwtAuthenticationFilter.java** — Per-request JWT validation
16. **src/main/java/com/todo/app/security/CognitoJwtValidator.java** — Cognito JWT verification with JWKS
17. **src/main/java/com/todo/app/repository/TodoRepository.java** — JPA repository for MySQL data access
18. **src/main/resources/application.properties** — Configuration with environment variable injection
19. **src/main/resources/logback-spring.xml** — Structured JSON logging with LogstashEncoder, CloudWatch appender
20. **build.sh** — Manual Maven build script with `-DskipTests` flag
21. **deploy.sh** — Manual SCP/SSH deployment script
22. **README.md** — Architecture documentation acknowledging security gaps
