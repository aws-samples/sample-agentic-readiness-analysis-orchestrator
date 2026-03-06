# Agentic Readiness Assessment Report
**Target**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
**Date**: 2026-03-06
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment

---

## Table of Contents

1. Executive Summary
2. Top Priorities (Critical Gaps)
3. Readiness Roadmap
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Agent Enablement (Months 3–6)
4. Recommended Modernization Pathways
5. Recommended Self-Paced Learning Materials
6. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
7. Appendix: Evidence Index

---

## Executive Summary

The Unishop monolith is a legacy Java 8 / Spring Boot 2.1 e-commerce application running on raw EC2 instances with a self-managed MySQL database and an Aurora MySQL 5.7 cluster that has passed end-of-life. The application has **no containerization, no CI/CD pipeline, no API gateway, no authentication enforcement, no observability stack, and no AI/agent capabilities**. The strongest area is Data Foundations, where a clean schema with no stored procedures and a centralized repository pattern provide a reasonable starting point. The most critical gaps are the complete absence of security controls (hardcoded credentials, no encryption, no auth enforcement), zero operational observability, and the tightly-coupled monolithic architecture running on unscalable EC2 instances. Significant modernization across all five categories is required before this application can support agentic workloads.

### Overall Score: 1.4 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.4 / 4.0 | ❌ |
| Application Architecture | 1.5 / 4.0 | ❌ |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.2 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

**1. Hardcoded Credentials and Zero Secret Management (SEC-Q1: 1/4)**
Database credentials (`MonoToMicroUser`/`MonoToMicroPassword`) are hardcoded in `application.properties` and repeated in clear text across CloudFormation `cfn-init` commands in `MonoToMicroCF.yaml`. Agentic workloads require dynamic credential rotation for tool-use APIs; hardcoded secrets are a critical security risk and a blocker for any production agent deployment. **First step**: Migrate all secrets to AWS Secrets Manager and reference them via `{{resolve:secretsmanager:...}}` in CloudFormation and environment-variable injection in application code.

**2. No CI/CD Pipeline — Manual EC2 Deployment (INF-Q6: 1/4, OPS-Q9: 1/4)**
The application is deployed by cloning a Git repo onto an EC2 instance via `cfn-init` and running `gradlew build` on the instance itself. There is no build pipeline, no automated testing, no deployment automation, and no rollback capability. Agentic systems require rapid, safe iteration cycles — especially for prompt tuning and tool configuration changes. **First step**: Create a GitHub Actions workflow with build, test, and deploy stages targeting a containerized deployment on ECS Fargate.

**3. 100% Synchronous Architecture with No Messaging (APP-Q3: 1/4, INF-Q4: 1/4)**
Every API call is a synchronous HTTP request → service → database query chain. There is no SQS, SNS, EventBridge, or any async messaging. Agent workflows are inherently multi-step and asynchronous; without event-driven infrastructure, agents cannot reliably orchestrate long-running tasks, handle retries, or decouple tool execution. **First step**: Introduce Amazon SQS for basket operations and Amazon EventBridge for domain events (user created, item added to basket).

**4. No API Gateway or Authentication Enforcement (INF-Q7: 1/4, SEC-Q9: 1/4)**
The application is exposed through nginx on EC2 with no API Gateway, no rate limiting, no request validation, and no authentication enforcement. Although Spring Security OAuth2 is imported, `ResourceServerConfig.java` sets `permitAll()` on every endpoint. Agents hitting unprotected APIs can be exploited or abused at machine speed. **First step**: Deploy Amazon API Gateway in front of the application with Cognito authorizer, request throttling, and usage plans.

**5. Zero Observability — No Tracing, No Structured Logging, No Metrics (OPS-Q1: 1/4, OPS-Q2: 1/4, OPS-Q4: 1/4)**
The application uses `System.out.println` and `e.printStackTrace()` for logging with no JSON formatting, no correlation IDs, no distributed tracing, and no CloudWatch alarms. Agent workflows span multiple components and without end-to-end tracing and structured logs, debugging agent failures is impossible. **First step**: Add AWS X-Ray SDK to `build.gradle`, configure structured JSON logging with correlation IDs, and create CloudWatch alarms for error rates and latency on critical endpoints.

---

## Readiness Roadmap

> Cross-dependencies: Containerization (Phase 1) is a prerequisite for ECS/EKS deployment (Phase 2). Secret management (Phase 1) is a prerequisite for API Gateway auth (Phase 2). IaC and CI/CD (Phase 1) are prerequisites for canary deployments (Phase 2). Database migration to Aurora MySQL 3 (Phase 2) is a prerequisite for pgvector-based RAG (Phase 3).

### Microservices Decomposition Strategy

The Unishop monolith has identifiable domain boundaries — **Unicorn Catalog**, **Shopping Basket**, and **User Management** — each with its own controller, service, repository, and mapper. However, all three domains share a single MySQL database, a single deployment unit (`bootJar`), and shared base models (`CoreModel`). The `unicorns_basket` table creates a data coupling between the Unicorn and Basket domains via `JOIN` queries in `UnicornMapper.xml`.

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure (containerize, add API Gateway, add CI/CD) while incrementally extracting services using the Strangler Fig pattern
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract the **Shopping Basket** service first — it has the clearest domain boundary, maps directly to the existing `MonoToMicroLambda.yaml` Lambda functions (AddUnicornToBasket, RemoveUnicornFromBasket, GetUnicornsBasket), and the `MonoToMicroCFDDB.yaml` already provisions a DynamoDB table (`unishop-users`) indicating a planned migration path to DynamoDB
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition. Aligns with the aggressive modernization preference.

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently; containerize the monolith as-is first, then extract services opportunistically
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Containerize the entire monolith in a single Docker image, deploy to ECS Fargate, then extract Basket service
- **When to Use**: If timeline is very tight and the team needs to demonstrate containerized deployment quickly before committing to decomposition

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

**Pattern Recommendations Based on Your Architecture:**

- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (path-based routing: `/unicorns/basket/*` → Lambda/DynamoDB, everything else → monolith)
  - **Why**: API Gateway provides routing, throttling, and auth without requiring service mesh infrastructure upfront. The existing `RefactorSpaces` environment in `MonoToMicroCF.yaml` was designed for exactly this pattern.

- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extraction
  - **Why**: Without idempotency (APP-Q7 score 2), service extraction risks data inconsistency; the `INSERT IGNORE` pattern in `UnicornMapper.xml` provides partial protection but is insufficient for cross-service boundaries.

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition
  - **Why**: Microservices amplify failure modes; the current bare `try/catch` with `e.printStackTrace()` in `UnicornRepositoryImpl.java` and `UserRepositoryImpl.java` will not survive distributed call chains.

### Phase 1 — Quick Wins (Days 1–30)

1. **Move secrets to AWS Secrets Manager**: Migrate `MonoToMicroUser`/`MonoToMicroPassword` from `application.properties` and `MonoToMicroCF.yaml` cfn-init scripts to Secrets Manager. Update the Spring Boot app to read credentials from environment variables injected at runtime.
2. **Create a Dockerfile**: Package the Spring Boot application (`bootJar` output) in a container image. This is the first step toward ECS/EKS deployment and eliminates the fragile `cfn-init` build-on-instance pattern.
3. **Set up CI/CD pipeline**: Create a GitHub Actions workflow with stages for build (Gradle), test (add basic smoke tests), container image push to ECR, and deployment to ECS Fargate.
4. **Add structured logging**: Replace all `System.out.println` and `e.printStackTrace()` calls with SLF4J/Logback JSON formatter. Add correlation ID middleware. Configure CloudWatch Logs agent for JSON ingestion.
5. **Conduct EventStorming workshop**: Map domain boundaries (Unicorn Catalog, Shopping Basket, User Management), identify bounded contexts, and document current data coupling via `unicorns_basket` JOIN queries. Identify the Basket service as the first extraction candidate.

### Phase 2 — Foundation (Months 1–3)

1. **Deploy to ECS Fargate with API Gateway**: Containerize the monolith and deploy to ECS Fargate behind Amazon API Gateway. Configure path-based routing, request throttling (burst/rate limits), and Cognito authorizer for JWT-based authentication.
2. **Migrate Aurora MySQL 5.7 to Aurora MySQL 3 (MySQL 8.0-compatible)**: The current `EngineVersion: 5.7.mysql_aurora.2.11.2` in `MonoToMicroCF.yaml` is past EOL. Perform in-place upgrade to Aurora MySQL 3.x. Eliminate the self-managed MySQL on EC2 (`DBInstance`) by migrating to the RDS Aurora cluster.
3. **Extract Basket service using Strangler Fig**: Route `/unicorns/basket/*` through API Gateway to Lambda functions backed by DynamoDB (infrastructure already partially defined in `MonoToMicroLambda.yaml` and `MonoToMicroCFDDB.yaml`). Implement anti-corruption layer at the boundary.
4. **Introduce EventBridge for domain events**: Publish `BasketItemAdded`, `BasketItemRemoved`, `UserCreated` events to EventBridge. This decouples services and enables future agent event subscriptions.
5. **Add distributed tracing**: Integrate AWS X-Ray SDK into the Spring Boot application and Lambda functions. Propagate trace IDs across API Gateway → ECS/Lambda boundaries.
6. **Enable encryption at rest**: Add KMS keys for S3 buckets (`UIBucket`, `AssetBucket`), Aurora cluster, and EBS volumes. Configure customer-managed KMS keys in CloudFormation.
7. **Implement canary deployments**: Configure ECS service with CodeDeploy blue/green deployment. Add CloudWatch alarms as rollback triggers.

### Phase 3 — Agent Enablement (Months 3–6)

1. **Create OpenAPI specifications**: Document all API endpoints (`/unicorns`, `/unicorns/basket`, `/user`, `/health`) with OpenAPI 3.0 specs. These become the tool definitions for agent frameworks.
2. **Deploy vector database**: Add Aurora PostgreSQL with pgvector extension or Amazon OpenSearch Service for product catalog semantic search. Build embeddings pipeline for unicorn product descriptions.
3. **Implement RAG pipeline**: Use Amazon Bedrock Knowledge Bases to index product catalog and user documentation. Enable semantic search for agent-powered product recommendations.
4. **Add agent framework**: Integrate Strands Agents SDK or LangChain (Java) with Amazon Bedrock. Define tools mapped to Unicorn Catalog, Basket, and User service APIs.
5. **Establish agent SLOs and eval framework**: Define task success rate, hallucination rate, and tool error rate SLOs. Create golden datasets for agent evaluation. Implement automated eval pipeline in CI/CD.
6. **Implement human-in-the-loop for high-risk operations**: Add Step Functions approval workflows for bulk operations, order processing, and data modifications triggered by agents.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are recommended for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Triggered | Priority | Key Trigger Criteria | Est. Effort |
|---------|-----------|----------|---------------------|-------------|
| Move to Cloud Native | Yes | High | APP-Q4=2 (monolith), INF-Q1=1 (EC2), APP-Q3=1 (sync-only), APP-Q10=1 (no async) | High |
| Move to Containers | Yes | High | INF-Q1=1 (no containers), APP-Q4=2 (monolith), no Dockerfile found | Medium |
| Move to Open Source | No | N/A | MySQL is already open source | N/A |
| Move to Managed Databases | Yes | High | INF-Q2=2 (self-managed MySQL on EC2), DATA-Q10=1 (Aurora 5.7 past EOL) | Medium |
| Move to Managed Analytics | Yes | Medium | INF-Q8=1 (no streaming), DATA-Q4=4 but no analytics services | Medium |
| Move to Modern DevOps | Yes | High | INF-Q5=3, INF-Q6=1, OPS-Q9=1, OPS-Q10=1, OPS-Q1=1 | High |
| Move to AI | Yes | High | APP-Q13=1, DATA-Q1=1, DATA-Q3=1, OPS-Q3=1, OPS-Q6=1 | High |

### Parallel Execution Plan

**Parallel Track 1 (Infrastructure)**: Move to Containers + Move to Modern DevOps — can run concurrently. Containerize the application while simultaneously building CI/CD pipelines and observability.

**Parallel Track 2 (Data)**: Move to Managed Databases + Move to Managed Analytics — can run concurrently after containerization is complete. Database migration and analytics setup are independent of each other.

**Sequential Dependencies**:
- Move to Containers must complete before Move to Cloud Native (containerize before decomposing into microservices/serverless)
- Move to Modern DevOps (CI/CD, IaC) should be in place before Move to Cloud Native (need deployment automation before service extraction)
- Move to Managed Databases should be in progress before Move to AI (vector DB and managed DB are prerequisites for RAG)
- Move to AI depends on foundations from Cloud Native (API boundaries), Managed Databases (vector store), and Modern DevOps (eval pipelines)

### Move to Cloud Native (Containers and Serverless)

- **Priority**: High
- **Trigger Criteria Met**:
  - APP-Q4: Score 2/4 — Monolith with identifiable domain boundaries but tightly coupled via shared database and models
  - INF-Q1: Score 1/4 — 100% EC2 compute with no ECS/EKS/Lambda for the monolith
  - APP-Q3: Score 1/4 — All communication is synchronous HTTP; no async messaging
  - APP-Q10: Score 1/4 — No async processing for any operations
- **Current State**: Single Spring Boot JAR deployed on EC2 via cfn-init. All API calls are synchronous request-response. No event-driven architecture.
- **Target State**: Basket service extracted to Lambda + DynamoDB. Catalog and User services on ECS Fargate. EventBridge for domain events. API Gateway for routing and throttling.
- **Key Activities**:
  1. Extract Basket service to Lambda + DynamoDB (infrastructure partially exists in `MonoToMicroLambda.yaml` and `MonoToMicroCFDDB.yaml`)
  2. Introduce EventBridge for domain events and SQS for async processing
  3. Deploy remaining services on ECS Fargate with auto-scaling
  4. Implement Step Functions for multi-step workflows
- **Dependencies**: Move to Containers must complete first
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Foundation) and Phase 3 (Agent Enablement)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

### Move to Containers

- **Priority**: High
- **Trigger Criteria Met**:
  - INF-Q1: Score 1/4 — No ECS/EKS/Fargate detected; application runs on raw EC2
  - APP-Q4: Score 2/4 — Monolith needing containerization as first step toward decomposition
  - No Dockerfile or container definitions found in the repository
- **Current State**: Application is built on EC2 via cfn-init (`gradlew clean build` on instance). No Dockerfile, no container registry, no container orchestration.
- **Target State**: Application packaged as Docker container, stored in ECR, deployed to ECS Fargate with auto-scaling and health checks.
- **Key Activities**:
  1. Create Dockerfile for the Spring Boot application
  2. Set up Amazon ECR repository
  3. Deploy to ECS Fargate with task definitions and service auto-scaling
  4. Configure ALB/API Gateway health checks
- **Dependencies**: None — this is a foundational step
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for Dockerfile creation, Phase 2 (Foundation) for ECS deployment
- **Relevant Learning Materials**: Module 3 — Move to Containers

### Move to Managed Databases

- **Priority**: High
- **Trigger Criteria Met**:
  - INF-Q2: Score 2/4 — Self-managed MySQL 8.0 on EC2 (`DBInstance` in `MonoToMicroCF.yaml` installs `mysql-community-server` via cfn-init)
  - DATA-Q10: Score 1/4 — Aurora MySQL 5.7 (`EngineVersion: 5.7.mysql_aurora.2.11.2`) is past EOL (October 2024)
- **Current State**: Dual database setup: self-managed MySQL on EC2 (source) with DMS replication to Aurora MySQL 5.7 (target). Aurora engine version is past end-of-life.
- **Target State**: Single Aurora MySQL 3.x cluster (MySQL 8.0-compatible) with automated backups, failover, and encryption. No self-managed database instances.
- **Key Activities**:
  1. Upgrade Aurora MySQL from 5.7 to 3.x (MySQL 8.0-compatible)
  2. Eliminate self-managed MySQL on EC2 (`DBInstance`) — migrate all traffic to Aurora
  3. Enable encryption at rest with KMS
  4. Add Aurora PostgreSQL with pgvector for vector database needs (Phase 3)
- **Dependencies**: None — can start immediately
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for version pinning, Phase 2 (Foundation) for migration
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Managed Analytics

- **Priority**: Medium
- **Trigger Criteria Met**:
  - INF-Q8: Score 1/4 — No managed streaming services (Kinesis, MSK) detected
  - No managed analytics services detected in discovery
- **Current State**: No streaming, no analytics, no data lake. The application is a simple CRUD e-commerce store.
- **Target State**: EventBridge for event streaming, with optional Kinesis Data Firehose for analytics data pipeline.
- **Key Activities**:
  1. Implement EventBridge as the event bus for domain events
  2. Add Kinesis Data Firehose for event archival and analytics if needed
  3. Consider Amazon Athena for ad-hoc query capabilities on archived events
- **Dependencies**: Move to Cloud Native (EventBridge introduction)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2 (Foundation) for streaming, Phase 3 for analytics
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

### Move to Modern DevOps

- **Priority**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline; only cfn-nag security scan in GitHub Actions
  - OPS-Q9: Score 1/4 — Direct-to-production deployment via cfn-init on single EC2 instance
  - OPS-Q10: Score 1/4 — No test files exist despite `spring-boot-starter-test` dependency in build.gradle
  - OPS-Q1: Score 1/4 — No distributed tracing (no X-Ray, no OpenTelemetry)
  - INF-Q5: Score 3/4 — CloudFormation covers most resources but gaps remain
- **Current State**: Application is deployed by SSH-equivalent (cfn-init) onto EC2. Single GitHub Actions workflow runs only cfn-nag scan. No test files. No tracing. No monitoring dashboards.
- **Target State**: Full CI/CD pipeline with build, test, container push, and canary deployment stages. Distributed tracing with X-Ray. Structured logging. CloudWatch dashboards and alarms.
- **Key Activities**:
  1. Create CI/CD pipeline in GitHub Actions (build → test → push to ECR → deploy to ECS)
  2. Add integration tests and unit tests
  3. Integrate AWS X-Ray for distributed tracing
  4. Configure structured JSON logging with correlation IDs
  5. Set up CloudWatch dashboards, alarms, and anomaly detection
  6. Implement canary/blue-green deployments with CodeDeploy
- **Dependencies**: None — can start immediately in parallel with containerization
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for CI/CD and logging, Phase 2 for advanced deployment
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in build.gradle
  - DATA-Q1: Score 1/4 — No vector database present
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI capabilities. No vector store. No embeddings. No agent framework. No LLM integration.
- **Target State**: Amazon Bedrock integration with Strands Agents SDK. Vector database (pgvector on Aurora PostgreSQL or OpenSearch). RAG pipeline for product catalog. Automated eval framework with golden datasets. Token usage tracking with cost attribution.
- **Key Activities**:
  1. Deploy vector database (Aurora PostgreSQL with pgvector or OpenSearch)
  2. Build RAG pipeline with Amazon Bedrock Knowledge Bases for product catalog
  3. Integrate Strands Agents SDK with tool definitions mapped to service APIs
  4. Create eval framework with golden datasets and scoring
  5. Implement LLM cost tracking with CloudWatch custom metrics
- **Dependencies**: Move to Cloud Native (API boundaries for tools), Move to Managed Databases (vector store), Move to Modern DevOps (eval in CI/CD)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 3 (Agent Enablement)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more. Directly applicable to the Unishop monolith decomposition strategy.
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
  - The Basket service extraction to Lambda is the recommended first extraction target.
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - API Gateway is the critical missing entry point for throttling, auth, and routing.
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
  - DynamoDB table (`unishop-users`) already provisioned in `MonoToMicroCFDDB.yaml`; understanding DynamoDB patterns is essential for the Basket service migration.
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
  - Directly relevant hands-on lab for the Unishop containerization journey.
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
  - ECS Fargate is the recommended compute target for the monolith containerization.
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
  - EKS is a preferred technology per transformation preferences.
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
  - Foundational — no Dockerfile exists in the repository today.
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- EKS Workshop — https://www.eksworkshop.com/

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
  - Directly applicable — the application needs to migrate from self-managed MySQL to Aurora MySQL 3.x.
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
  - DMS resources already exist in `MonoToMicroCF.yaml`.
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Required for Phase 3 vector database deployment.

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundational — no CI/CD exists today.
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Directly applicable lab for the target CI/CD architecture.
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - CloudFormation is already in use; this helps improve IaC coverage.
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Critical — no tests exist today.
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
  - Directly applicable for Java/Spring Boot observability.

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Essential for building the product catalog RAG pipeline.
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on lab for the recommended agent framework.
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: The application runs on raw EC2 instances. `MonoToMicroCF.yaml` defines `EC2Instance` (AWS::EC2::Instance, type t3.small) for the Spring Boot application and `DBInstance` (AWS::EC2::Instance, type t3.small) for self-managed MySQL. No ECS, EKS, Lambda, or Fargate resources are defined for the monolith. The `MonoToMicroLambda.yaml` defines Lambda functions for future basket service extraction but these are not yet integrated into the primary application flow.
- **Gap**: 100% of the monolith's compute is raw EC2. No container orchestration or serverless compute for the primary application.
- **Recommendation**: Create a Dockerfile for the Spring Boot JAR, push to ECR, and deploy to ECS Fargate. Use the existing Lambda functions in `MonoToMicroLambda.yaml` for the Basket service extraction.

#### INF-Q2: Databases
- **Score**: 2/4 🟠
- **Finding**: Dual database setup in `MonoToMicroCF.yaml`: (1) `DBInstance` — self-managed MySQL 8.0 installed via `cfn-init` using `mysql80-community-release-el7-1.noarch.rpm` on EC2, serving as DMS source. (2) `RDSCluster` — managed Aurora MySQL cluster (`Engine: aurora-mysql`, `EngineVersion: 5.7.mysql_aurora.2.11.2`) with `RDSInstance` (db.r6i.2xlarge), serving as DMS target. DMS endpoints (`MySQLSourceEndpoint`, `MySQLTargetEndpoint`) and replication instance configured for migration. Application connection string in `application.properties` points to `MONO_TO_MICRO_DB_ENDPOINT` env var which resolves to the self-managed EC2 MySQL.
- **Gap**: Self-managed MySQL on EC2 is the primary database. Aurora MySQL is available but the application still connects to the EC2 instance. Aurora engine version 5.7 is past EOL.
- **Recommendation**: Complete DMS migration to Aurora. Upgrade Aurora from 5.7 to 3.x (MySQL 8.0-compatible). Eliminate the self-managed `DBInstance` EC2 instance. Update `MONO_TO_MICRO_DB_ENDPOINT` to point to the Aurora cluster endpoint.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service found in CloudFormation templates, `build.gradle`, or application code. Business logic flows are hardcoded in `UnicornServiceImpl.java` and `UserServiceImpl.java` as direct method calls.
- **Gap**: No dedicated orchestration service. All business logic is procedural.
- **Recommendation**: Introduce AWS Step Functions for multi-step workflows such as order processing, basket checkout, and future agent orchestration flows.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or MSK resources in any CloudFormation template. No messaging SDK imports in `build.gradle`. All inter-component communication in the monolith is synchronous method calls. The event classes in `com.monoToMicro.core.events` (e.g., `CreateEvent.java`, `ReadEvent.java`) are in-memory data transfer objects, not actual messaging events.
- **Gap**: Zero async messaging capability. All operations are synchronous.
- **Recommendation**: Introduce Amazon EventBridge for domain events (`BasketItemAdded`, `UserCreated`) and Amazon SQS for async processing of non-critical operations. This aligns with the preferred event-driven architecture pattern.

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: Three CloudFormation templates in `MonoToMicroAssets/`: `MonoToMicroCF.yaml` (VPC, subnets, EC2, RDS, S3, IAM, DMS, RefactorSpaces — comprehensive), `MonoToMicroCFDDB.yaml` (DynamoDB table, Lambda IAM role), `MonoToMicroLambda.yaml` (Lambda functions). IaC covers compute, networking, databases, storage, IAM, and migration infrastructure. One GitHub Actions workflow (`cfn-security.yml`) runs cfn-nag scan on templates.
- **Gap**: IaC covers ~80% of infrastructure. Missing: CloudWatch alarms, API Gateway, WAF, KMS keys, Secrets Manager, and deployment automation resources. The application build and deployment process is imperative (cfn-init scripts) rather than declarative.
- **Recommendation**: Extend IaC to cover API Gateway, CloudWatch alarms, KMS encryption, Secrets Manager secrets, and deployment automation (CodeDeploy). Consider migrating to CDK for better developer experience with Java.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: Only one GitHub Actions workflow exists: `.github/workflows/cfn-security.yml` which runs `cfn_nag` security scan on CloudFormation templates in `MonoToMicroAssets/` on every push. No build pipeline, no test stage, no deployment automation. The application is built on EC2 during `cfn-init` (`gradlew clean build` in `MonoToMicroCF.yaml` EC2Instance configure step).
- **Gap**: No CI/CD pipeline. Application is built and deployed via cfn-init on EC2 instance provisioning. No automated testing. No deployment automation.
- **Recommendation**: Create a full CI/CD pipeline in GitHub Actions with stages: checkout → Gradle build → unit test → container build → push to ECR → deploy to ECS Fargate via CodeDeploy.

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: The application is fronted by nginx installed on EC2 (`MonoToMicroCF.yaml`, cfn-init step `3-install-nginx`) with a reverse proxy config: `proxy_pass http://127.0.0.1:8080/`. No API Gateway, no ALB, no CloudFront in any CloudFormation template. A `RefactorSpaces` environment (`UniShopRefactorSpacesModernizationEnvironment`) and application (`UniShopRefactorSpacesApplication` with `ProxyType: API_GATEWAY`) are created but not wired to route traffic.
- **Gap**: No managed API entry point. No throttling, no request validation, no auth at the gateway level. nginx on EC2 provides no protection against abuse.
- **Recommendation**: Deploy Amazon API Gateway (regional) as the entry point. Configure throttling (burst/rate limits), Cognito authorizer, request validation, and usage plans. The RefactorSpaces environment can be leveraged for routing during the Strangler Fig decomposition.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming service resources in CloudFormation templates. No Kafka or Kinesis SDK imports in `build.gradle`. No stream consumer patterns in application code.
- **Gap**: No real-time streaming capability.
- **Recommendation**: Introduce Amazon EventBridge for event-driven patterns. Add Kinesis Data Firehose for analytics data pipeline if real-time analytics is needed.

#### INF-Q9: Network Security
- **Score**: 2/4 🟠
- **Finding**: `MonoToMicroCF.yaml` defines a VPC (`MonoToMicroVPC`, CIDR 10.0.0.0/16) with 4 subnets: 2 public (MonoToMicroSubnet1/2 with `MapPublicIpOnLaunch: true`) and 2 private (MonoToMicroSubnet3/4 with `MapPublicIpOnLaunch: false`). NAT Gateways (MonoToMicroNatGateway1/2) provide internet access for private subnets. `DBSecurityGroup` restricts MySQL port 3306 to `EC2SecurityGroup` source only — good. `EC2SecurityGroup` allows inbound 0.0.0.0/0 on ports 80 and 443 — overly permissive. EC2 instance is in a public subnet. RDS is in public subnets (DBSubnetGroup uses Subnet1/2 which are public).
- **Gap**: EC2 is publicly exposed on 0.0.0.0/0. RDS subnet group uses public subnets. No WAF. No NACLs defined beyond default.
- **Recommendation**: Move the application EC2 (and future ECS tasks) behind an ALB or API Gateway. Place RDS in private subnets (Subnet3/4). Restrict EC2SecurityGroup ingress to ALB/API Gateway security group only. Add WAF for web application protection.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No `AWS::AutoScaling::AutoScalingGroup`, `AWS::ApplicationAutoScaling::ScalableTarget`, or any auto-scaling resources in CloudFormation. Both `EC2Instance` and `DBInstance` are single standalone instances (no ASG). `RDSInstance` has `MultiAZ: false`.
- **Gap**: Zero auto-scaling. Single point of failure for compute and database.
- **Recommendation**: Deploy the application on ECS Fargate with service auto-scaling (target tracking on CPU/memory). Enable Aurora Multi-AZ. Configure Lambda reserved concurrency for basket functions.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`) with Spring Boot 2.1.0/2.1.6 (`springBootVersion = '2.1.0.RELEASE'`, plugin `2.1.6.RELEASE`). AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567`). Gradle 7.4 (`gradle-wrapper.properties`). Java has agent framework support (Spring AI, LangChain4j) but the ecosystem is less mature than Python/TypeScript. Java 8 is past EOL and Spring Boot 2.1 is end of OSS support.
- **Gap**: Java 8 and Spring Boot 2.1 are significantly outdated. AWS SDK v1 is in maintenance mode. Agent framework ecosystem in Java is available but less mature than Python.
- **Recommendation**: Upgrade to Java 17+ and Spring Boot 3.x. Migrate to AWS SDK v2. Consider Java 21 for virtual threads which improve async handling. Spring AI provides Bedrock integration for agent workloads.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specification files found in the repository. No `openapi.yaml`, `swagger.json`, or API documentation files. No Swagger annotations (`@ApiOperation`, `@OpenAPIDefinition`) in any controller. No SpringDoc or springfox dependencies in `build.gradle`. API endpoints are defined only in controller annotations: `/unicorns` (GET), `/unicorns/basket` (POST, DELETE, GET/{userUuid}), `/user` (POST, POST/login), `/health/ping`, `/health/ishealthy`, `/health/dbping`, `/data` (GET).
- **Gap**: Zero API documentation. Agents require machine-readable API specifications to define tools.
- **Recommendation**: Generate OpenAPI 3.0 specifications for all endpoints. Add springdoc-openapi dependency to `build.gradle` for auto-generation from controllers. These specs become the tool definitions for agent frameworks.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous communication. All controllers (`BasketController`, `UnicornController`, `UserController`, `HealthController`, `DataReplicationController`) make direct synchronous calls to service implementations which call repository methods which execute MyBatis SQL queries. No message publishing, no event-driven handlers, no async patterns anywhere in the codebase. The `core.events` package contains in-memory DTOs (e.g., `ReadUnicornsEvent`, `WriteUnicornsBasketEvent`), not actual async messaging events.
- **Gap**: Zero async communication. All operations block on database queries.
- **Recommendation**: Introduce EventBridge for domain events and SQS for async processing. Start with basket add/remove operations as async candidates with status polling.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single deployable Spring Boot JAR (`bootJar` in `build.gradle`) containing all controllers, services, and repositories. Package structure shows identifiable domains: `rest/controller/` (UnicornController, BasketController, UserController, HealthController, DataReplicationController), `core/services/` (UnicornService, UserService, HealthService), `core/repository/` (UnicornRepository, UserRepository, HealthRepository), `core/model/` (Unicorn, UnicornBasket, User). Coupling evidence: `BasketController` uses `UnicornService` (not a separate BasketService), `UnicornServiceImpl` handles both unicorn catalog AND basket operations, `UnicornMapper.xml` contains JOIN queries across `unicorns` and `unicorns_basket` tables, all models extend `CoreModel` (shared base class). The `DataReplicationController` calls `unicornService.getAllBaskets()` indicating cross-domain data access.
- **Gap**: Monolith with identifiable but coupled domains. Shared database, shared service implementations (Unicorn and Basket logic in same service), shared base models.
- **Recommendation**: Extract Basket service first using Strangler Fig pattern. Separate `UnicornService` into Catalog and Basket services. Use API Gateway routing to direct `/unicorns/basket/*` to the new Lambda+DynamoDB service.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API responses use JSON via Jackson serialization. Models use `@JsonInclude(JsonInclude.Include.NON_NULL)` on `Unicorn.java` and `User.java`. `CoreModel.java` uses `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)`. All controllers return `ResponseEntity<T>` with typed objects (Unicorn, UnicornBasket, User, String) that are automatically serialized to JSON by Spring Boot's Jackson auto-configuration.
- **Gap**: None — JSON is the standard response format.
- **Recommendation**: Maintain JSON responses. Consider adding consistent error response format with error codes for agent consumption.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` is simple CRUD with direct repository calls. No Step Functions, no Temporal, no state machines, no saga patterns. The `addUnicornToBasket` flow is a direct write without any multi-step orchestration.
- **Gap**: No workflow orchestration. Business logic is hardcoded procedural code.
- **Recommendation**: Introduce Step Functions for multi-step workflows (e.g., checkout process, order fulfillment). Design agent orchestration flows with Step Functions using `waitForTaskToken` for human-in-the-loop approvals.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: `UnicornMapper.xml` uses `INSERT IGNORE INTO unicorns_basket` for `addUnicornToBasket` — this provides database-level idempotency for basket additions (duplicate uuid+unicornUuid is silently ignored due to `CONSTRAINT UnicornUnique UNIQUE (uuid, unicornUuid)` in `create_tables.sql`). `UserMapper.xml` uses `INSERT IGNORE INTO unicorn_user` for user creation with `CONSTRAINT UserUnique UNIQUE (email)`. However, no idempotency keys in HTTP headers, no deduplication IDs, no application-level idempotency mechanisms.
- **Gap**: Database-level idempotency via `INSERT IGNORE` exists but no API-level idempotency keys. Agents retrying failed requests could cause side effects for non-INSERT operations.
- **Recommendation**: Add `Idempotency-Key` header support to all write APIs. Implement a deduplication table or use DynamoDB conditional writes for idempotency in the extracted services.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. No API Gateway usage plans (no API Gateway exists). No WAF rules. No rate limiting middleware in the Spring Boot application (no `express-rate-limit` equivalent, no `spring-boot-starter-webflux` rate limiter). No throttling configuration in nginx config (basic proxy_pass only).
- **Gap**: Zero rate limiting. Agents or malicious clients can make unlimited requests.
- **Recommendation**: Deploy API Gateway with throttling (burst/rate limits per client). Add usage plans with API keys for agent consumers. Consider application-level rate limiting with Spring Boot's Bucket4j or resilience4j-ratelimiter.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retries, or timeouts implemented. All repository methods use bare `try/catch` blocks that call `e.printStackTrace()` and return null/false: `UnicornRepositoryImpl.java` (5 methods), `UserRepositoryImpl.java` (2 methods), `HealthRepositoryImpl.java` (1 method). No Resilience4j, Hystrix, or retry libraries in `build.gradle`. No timeout configurations on database connections in `application.properties`. No AWS SDK retry configuration.
- **Gap**: Zero resilience patterns. Any database failure results in silent null returns with stack traces printed to stdout.
- **Recommendation**: Add Resilience4j to `build.gradle`. Implement circuit breakers on database calls, retry with exponential backoff, and connection timeouts. Replace `e.printStackTrace()` with structured error logging.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All operations are synchronous and complete within the HTTP request lifecycle. No background job frameworks (no Celery, Bull, SQS workers). No async/polling patterns. No job status APIs. No Lambda async invocations from the monolith. The `DataReplicationController.java` `/data` endpoint calls `unicornService.getAllBaskets()` synchronously — this could become a long-running operation as data grows.
- **Gap**: No async processing capability. All operations block the request thread.
- **Recommendation**: Introduce SQS-backed async processing for operations that could become long-running (data replication, bulk operations). Implement job status polling endpoint pattern for agent consumption.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy. Endpoints use flat paths: `/unicorns`, `/unicorns/basket`, `/user`, `/health`, `/data`. No `/v1/` or `/v2/` URL prefixes. No `Accept-Version` headers. No versioning annotations. No changelog files.
- **Gap**: No versioning. Breaking changes will affect all consumers including agents.
- **Recommendation**: Adopt URL path versioning (`/v1/unicorns`, `/v1/user`) when deploying behind API Gateway. Establish a backward compatibility policy.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith with nginx reverse proxy. nginx config in `MonoToMicroCF.yaml` uses hardcoded `proxy_pass http://127.0.0.1:8080/`. No AWS Service Discovery, App Mesh, Consul, or service registry. No environment-based service discovery. The `MONO_TO_MICRO_DB_ENDPOINT` env var is the only external service reference.
- **Gap**: No service discovery. Hardcoded localhost proxy. No mechanism for dynamic service resolution when decomposing to microservices.
- **Recommendation**: Use API Gateway as the service catalog and routing layer during decomposition. Implement AWS Cloud Map for service discovery as services are extracted. Avoid hardcoded endpoints.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports in `build.gradle`. No Bedrock SDK, no LangChain4j, no Spring AI, no OpenAI, no Anthropic SDK, no MCP SDK. The AWS SDK dependency (`com.amazonaws:aws-java-sdk:1.11.567`) is v1 which does not include Bedrock client. No AI-related code patterns in any Java source file.
- **Gap**: Zero AI/agent capability. No framework, no integration points, no LLM interaction.
- **Recommendation**: Add Amazon Bedrock SDK (AWS SDK v2) and Strands Agents SDK. Define API tools from OpenAPI specifications. Start with a product recommendation agent using RAG over the unicorn catalog.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch, pgvector, Pinecone, Weaviate, or Chroma references in any CloudFormation template, `build.gradle`, or application code. No Bedrock Knowledge Base resources. No k-NN or similarity search patterns.
- **Gap**: No vector store capability. Required for semantic search, RAG, and agent tool matching.
- **Recommendation**: Deploy Aurora PostgreSQL with pgvector extension or Amazon OpenSearch Service with k-NN plugin. Start with product catalog embeddings for semantic search.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). Not applicable for managed vs self-hosted evaluation.
- **Gap**: No vector database of any kind.
- **Recommendation**: When deploying a vector database, use a managed service (Aurora PostgreSQL Serverless v2 with pgvector, or Amazon OpenSearch Service) to eliminate operational burden.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline. No embedding model calls, no document chunking/splitting code, no similarity search patterns. No Bedrock Knowledge Base integration. The product catalog is stored in the `unicorns` MySQL table with simple text columns (name, description) — no vector representations.
- **Gap**: No RAG capability. Product catalog data is accessible only via exact SQL queries.
- **Recommendation**: Build a RAG pipeline with Amazon Bedrock Knowledge Bases. Embed unicorn product descriptions using Bedrock Titan Embeddings. Store vectors in Aurora PostgreSQL pgvector. Enable semantic product search for agent-powered recommendations.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database with 3 tables: `unicorns`, `unicorns_basket`, `unicorn_user` (defined in `database/create_tables.sql`). Single datasource configuration in `application.properties` (`spring.datasource.url: jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`). No additional database connections, no external API clients, no secondary data sources in the codebase.
- **Gap**: None — single, well-defined data source. However, introducing DynamoDB (for basket) and a vector DB (for RAG) will increase sprawl; plan a unified data access strategy.
- **Recommendation**: Maintain simplicity. When adding DynamoDB and vector DB, create a unified data access layer or API abstraction to prevent sprawl.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Data is accessed via MyBatis mappers (`UnicornMapper`, `UserMapper`, `HealthMapper`) called from repository implementations (`UnicornRepositoryImpl`, `UserRepositoryImpl`, `HealthRepositoryImpl`). The repository pattern provides a clean interface layer (`UnicornRepository`, `UserRepository`, `HealthRepository`). However, controllers access data through service → repository → mapper chain with direct SQL execution via MyBatis XML — not via APIs. The `BasketController` calls `unicornService` directly, bypassing any API boundary.
- **Gap**: Direct database access from the application layer. No API-mediated data access. Data access is centralized via repository pattern but tightly coupled to MyBatis/MySQL.
- **Recommendation**: When extracting services, ensure each service owns its data and exposes it only via APIs. The Basket service should access unicorn data through the Catalog API, not via direct JOIN queries.

#### DATA-Q6: Unstructured Data
- **Score**: 2/4 🟠
- **Finding**: `MonoToMicroCF.yaml` defines two S3 buckets: `UIBucket` (configured for static website hosting with `index.html`) and `AssetBucket` (stores compiled JAR files and Lambda artifacts). Product images are referenced by name in the `unicorns` table (`image` column contains names like 'UnicornFloat', 'UnicornHipHop') but the actual image assets are in `MonoToMicroAssets/assets/` and `assets1024/` directories. No document parsing (no Textract, Tika, or PDF processing).
- **Gap**: S3 is used for static asset storage only. No document parsing pipeline for unstructured data.
- **Recommendation**: Store product images in S3 with proper key structure. Add Textract integration if product documentation or invoices need processing. Consider S3 as the document store for a future knowledge base.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `database/create_tables.sql` documents the schema with CREATE TABLE statements for `unicorns`, `unicorns_basket`, and `unicorn_user`. MyBatis mapper XML files (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) document the SQL queries. No schema versioning tool (no Flyway, Liquibase, or Alembic). No JSON Schema files. No formal schema documentation beyond the SQL script and mapper files.
- **Gap**: Schema exists in SQL script but is not versioned. No migration tool. Schema changes require manual SQL execution.
- **Recommendation**: Add Flyway or Liquibase for schema versioning. Create migration scripts. Document schema in a formal format (JSON Schema or OpenAPI component schemas).

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Centralized repository pattern: `UnicornRepository` (interface) → `UnicornRepositoryImpl` (implementation with `@Repository` + `@Transactional`), `UserRepository` → `UserRepositoryImpl`, `HealthRepository` → `HealthRepositoryImpl`. All database access goes through these repositories. Mapper interfaces (`UnicornMapper`, `UserMapper`, `HealthMapper`) are created via `MyBatisConfig.java` as Spring beans. Configuration is centralized in `MyBatisConfig.java` with a single `DataSource` bean.
- **Gap**: Repository pattern is well-structured for a monolith. However, `UnicornRepository` mixes catalog operations (`getUnicorns`) with basket operations (`addUnicornToBasket`, `getUnicornBasket`, `getAllBaskets`) — this needs to be split for decomposition.
- **Recommendation**: Split `UnicornRepository` into CatalogRepository and BasketRepository before or during service extraction. Maintain the clean interface/implementation pattern when building new services.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1, DATA-Q3). No embedding generation pipeline, no refresh triggers, no CDC patterns, no scheduled re-indexing.
- **Gap**: No embedding pipeline exists to evaluate freshness.
- **Recommendation**: When implementing RAG, set up event-driven embedding refresh: when a product is added/updated in the catalog, trigger a Lambda function to re-embed and update the vector store.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 1/4 ❌
- **Finding**: `MonoToMicroCF.yaml` `RDSCluster` specifies `EngineVersion: 5.7.mysql_aurora.2.11.2` (Aurora MySQL 5.7-compatible). Aurora MySQL 5.7 reached end-of-life in October 2024. The self-managed MySQL on EC2 (`DBInstance`) installs `mysql80-community-release-el7-1.noarch.rpm` (MySQL 8.0) but the version is not pinned beyond the RPM package. The `DBInstance` image uses Amazon Linux 2 AMI which itself approaches EOL.
- **Gap**: Aurora MySQL 5.7 is past EOL — critical security and compatibility risk. Self-managed MySQL version is not precisely pinned. Amazon Linux 2 is approaching EOL.
- **Recommendation**: Immediately upgrade Aurora MySQL from 5.7 to 3.x (MySQL 8.0-compatible). Pin MySQL version explicitly in cfn-init scripts (or better, eliminate the self-managed instance). Migrate base AMI to Amazon Linux 2023.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: `database/create_tables.sql` contains only standard DDL (CREATE SCHEMA, CREATE TABLE) and DML (INSERT INTO). No stored procedures, triggers, functions, or proprietary SQL constructs. MyBatis mapper XML files (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) contain standard ANSI SQL (SELECT, INSERT IGNORE, DELETE) with MySQL-specific `INSERT IGNORE` syntax only. No T-SQL, PL/SQL, or vendor-specific procedural code. All business logic resides in the Java application layer.
- **Gap**: None — clean schema with no database-side business logic. This is excellent for database migration and modernization.
- **Recommendation**: Maintain all business logic in the application layer. When migrating to DynamoDB for the basket service, this clean separation makes the transition straightforward.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials hardcoded in `application.properties`: `spring.datasource.username: MonoToMicroUser`, `spring.datasource.password: MonoToMicroPassword`. Same credentials repeated in clear text in `MonoToMicroCF.yaml` cfn-init commands: `mysql -u root "-pMonoToMicroPassword"`, `CREATE USER 'MonoToMicroUser'@'%' IDENTIFIED BY 'MonoToMicroPassword'`, and in `RDSCluster` properties (`MasterUsername: MonoToMicroUser`, `MasterUserPassword: MonoToMicroPassword`). DMS endpoints also contain plaintext credentials (`Username: MonoToMicroUser`, `Password: MonoToMicroPassword`). No AWS Secrets Manager, SSM Parameter Store (for secrets), or HashiCorp Vault usage.
- **Gap**: All credentials are hardcoded in source code and IaC templates. This is a critical security vulnerability.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager. Use `{{resolve:secretsmanager:...}}` dynamic references in CloudFormation. Inject credentials via environment variables from ECS task definitions with Secrets Manager ARN references.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: `S3Policy` in `MonoToMicroCF.yaml` uses specific S3 actions (`s3:GetBucketLocation`, `s3:GetObject`, `s3:PutObject`) on specific bucket ARNs (`UIBucket`, `AssetBucket`) — good practice. `S3Role` adds managed policies `AmazonSSMManagedInstanceCore` and `CloudWatchAgentServerPolicy` which are broader but appropriate for EC2 management. `MonoToMicroDmsVpcRole` uses `AmazonDMSVPCManagementRole` managed policy. `LambdaRole` in `MonoToMicroCFDDB.yaml` has specific DynamoDB actions on a specific table ARN — good. `ModernizationCloud9.yaml` has `ModernizationC9Role` with `arn:aws:iam::aws:policy/AdministratorAccess` — overly permissive (though it's a workshop resource). `ModernizationC9LambdaExecutionRole` has `Resource: "*"` on EC2 and IAM actions.
- **Gap**: S3 and DynamoDB policies follow least privilege. However, Cloud9 role has AdministratorAccess, and there are no per-service IAM roles (single role for the EC2 instance). No condition keys or session tags.
- **Recommendation**: Create per-service IAM roles when decomposing. Remove AdministratorAccess from production roles. Add condition keys (e.g., `aws:SourceVpc`) to restrict access. Use IAM Access Analyzer to identify unused permissions.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: `ResourceServerConfig.java` configures Spring Security OAuth2 with `@EnableResourceServer` but the `configure()` method sets `authorizeRequests().anyRequest().permitAll()` — all requests are allowed without authentication. JWT dependency present in `build.gradle` (`spring-security-jwt:1.0.9.RELEASE`, `spring-cloud-starter-oauth2:2.0.1.RELEASE`) but not enforced. `Application.java` `CorsOptionsRequestSecurityConfigurationAdapter` ignores all OPTIONS requests (CORS workaround). No token exchange patterns, no user context propagation between services.
- **Gap**: OAuth2/JWT framework is imported but completely bypassed. No identity propagation. No user context in service calls.
- **Recommendation**: Configure Cognito as the OAuth2 provider. Enforce JWT validation on all endpoints except health checks. Propagate user identity (JWT claims) through service calls. Remove `permitAll()` authorization.

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: CloudWatch agent configured in `MonoToMicroCF.yaml` EC2Instance to collect `app.log` and send to `InstanceLogGroup` (CloudWatch Log Group with 7-day retention). However, no CloudTrail resource in any CloudFormation template. No log file validation. No immutable storage (no S3 bucket with Object Lock for logs). The app.log is a raw text file from `System.out.println` and `e.printStackTrace()` output.
- **Gap**: Basic CloudWatch Logs configured but no CloudTrail, no log validation, no immutable storage, and logs are unstructured text.
- **Recommendation**: Enable CloudTrail in CloudFormation with log file validation. Store CloudTrail logs in S3 with Object Lock enabled. Increase log retention period. Convert to structured logging.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. No API Gateway (therefore no usage plans or throttle settings). No WAF rules. No application-level rate limiting middleware. nginx proxy has no rate limiting configuration.
- **Gap**: Zero rate limiting. Critical for agent workloads that can generate high request volumes.
- **Recommendation**: Deploy API Gateway with per-client throttling and usage plans. Add WAF with rate-based rules. Implement API keys for agent consumers with per-key quotas.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Email addresses stored in `unicorn_user` table (`email` column in `create_tables.sql`). `UserMapper.xml` `getByEmail` query returns email in responses. `User.java` model includes `email`, `firstName`, `lastName` fields. `e.printStackTrace()` in all repository implementations could expose database connection details in logs. No log scrubbing middleware. No PII masking libraries. No Macie integration.
- **Gap**: PII (email, names) exposed in API responses and potentially in logs. No redaction or masking.
- **Recommendation**: Add PII masking to log output. Implement response filtering for sensitive fields when accessed by agents. Enable Amazon Macie on S3 buckets. Add log scrubbing middleware.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No approval workflows of any kind. No Step Functions with human approval tasks. No approval Lambda patterns. No approval API endpoints. No manual approval stages in CI/CD (only cfn-nag scan, no deployment pipeline).
- **Gap**: No human-in-the-loop mechanism. Critical for agent workloads that may take high-risk actions (data deletion, bulk modifications, order processing).
- **Recommendation**: Implement Step Functions with `waitForTaskToken` for high-risk agent actions. Add manual approval gates in CI/CD for production deployments. Design approval workflows for bulk operations.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS keys defined in any CloudFormation template. `UIBucket` and `AssetBucket` in `MonoToMicroCF.yaml` have no `BucketEncryption` property (S3 default encryption with SSE-S3 may apply, but no customer-managed keys). `RDSCluster` has no `StorageEncrypted` or `KmsKeyId` property. EC2 instances have no EBS encryption specified. No `AWS::KMS::Key` resources.
- **Gap**: No encryption at rest configured in IaC. Sensitive data (user emails, passwords) stored without explicit encryption.
- **Recommendation**: Create customer-managed KMS keys. Enable encryption on S3 buckets (`aws:kms`), Aurora cluster (`StorageEncrypted: true`), and EBS volumes. Use KMS key policies with least privilege.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: Spring Security OAuth2 framework is configured (`ResourceServerConfig.java` with `@EnableResourceServer`) but `authorizeRequests().anyRequest().permitAll()` effectively disables authentication on all endpoints. Every controller method annotated with `@PreAuthorize("permitAll()")`: `BasketController` (3 methods), `UnicornController` (1 method), `UserController` (2 methods), `HealthController` (3 methods), `DataReplicationController` (1 method). No API keys, no Cognito authorizer, no Bearer token validation.
- **Gap**: Authentication framework present but explicitly disabled. All 10 API endpoints are completely unauthenticated.
- **Recommendation**: Configure Cognito User Pool. Replace `permitAll()` with role-based access control (`@PreAuthorize("hasRole('USER')")`). Add API Gateway authorizer for Cognito JWT validation. Agent access should require specific IAM roles or API keys.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No Cognito User Pool, Okta, Ping, or any centralized identity provider configured in CloudFormation or application code. The `unicorn_user` table in `create_tables.sql` stores user accounts (email, first_name, last_name) with no password hashing visible. `CoreConfig.java` creates a `BCryptPasswordEncoder` bean but it is not used in any controller or service. `UserController.java` `/user/login` endpoint simply looks up user by email — no password verification.
- **Gap**: No centralized identity provider. User management is a custom, unsecured implementation with no password verification.
- **Recommendation**: Deploy Amazon Cognito User Pool. Migrate user accounts to Cognito. Implement OIDC/OAuth2 flows. SSO integration for administrative access.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, or any tracing SDK in `build.gradle`. No trace ID propagation in HTTP headers. No `traceparent` or `X-Amzn-Trace-Id` header handling. No instrumentation wrappers. No Datadog, Jaeger, or Zipkin SDKs. Note: `MonoToMicroLambda.yaml` Lambda functions have `TracingConfig: Mode: Active` (X-Ray enabled) and `MonoToMicroCFDDB.yaml` LambdaRole includes `AWSXRayDaemonWriteAccess` policy — but the monolith itself has zero tracing.
- **Gap**: No distributed tracing in the monolith. Lambda functions have X-Ray enabled but the primary application does not. No end-to-end trace correlation possible.
- **Recommendation**: Add AWS X-Ray SDK for Java to `build.gradle`. Add X-Ray Spring Boot auto-instrumentation. Propagate trace IDs through API Gateway to the application. Connect traces across API Gateway → ECS/EC2 → Aurora.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: `HealthController.java` uses `System.out.println(infoStr)` for logging instance metadata. All repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) use `e.printStackTrace()` for error handling. No SLF4J JSON formatters. No logback-spring.xml configuration. No correlation ID middleware. CloudWatch agent in `MonoToMicroCF.yaml` collects raw `app.log` output to `InstanceLogGroup` — this is unstructured text.
- **Gap**: All logging is unstructured text via `System.out.println` and `e.printStackTrace()`. No JSON format. No correlation IDs. Not queryable.
- **Recommendation**: Configure Logback with JSON encoder (`logstash-logback-encoder`). Replace all `System.out.println` with SLF4J logger calls. Add MDC-based correlation ID middleware. Update CloudWatch agent to parse JSON logs.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, test datasets, scoring scripts, or LLM assertion patterns found. No RAGAS, no golden dataset files. No A/B test infrastructure. No AI/LLM usage exists to evaluate.
- **Gap**: No agent evaluation capability. Required before deploying any agentic system.
- **Recommendation**: Create golden datasets for agent evaluation (e.g., product search queries with expected results). Implement automated eval pipeline using RAGAS or custom scoring. Integrate eval runs into CI/CD pipeline.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions in any file. No CloudWatch alarms in any CloudFormation template. No latency or error tracking configuration. No SLO dashboards. Spring Boot Actuator is included in `build.gradle` (`spring-boot-starter-actuator`) which exposes `/actuator` endpoints, but these are not connected to any monitoring system.
- **Gap**: Zero SLO definitions. No monitoring or alerting. Actuator endpoints exist but are unused.
- **Recommendation**: Define SLOs for critical user journeys (product listing latency <200ms p99, basket operations availability >99.9%). Create CloudWatch alarms on p99 latency and error rates. Build CloudWatch dashboards. Leverage Actuator metrics endpoints.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback capability. Application is deployed via `cfn-init` on EC2 instance provisioning — there is no mechanism to roll back a deployment. No blue/green or canary deployment configuration. No CodeDeploy. No Helm rollback (no Helm). No feature flags. No prompt versioning (no prompts). The `mono2micro.service` systemd unit has `Restart=on-failure` which restarts the same version on crash, but cannot roll back to a previous version.
- **Gap**: Zero rollback capability. A bad deployment requires reprovisioning the entire EC2 instance stack.
- **Recommendation**: Implement blue/green deployment using ECS with CodeDeploy. Add CloudWatch alarm-based rollback triggers. Implement feature flags for gradual feature rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no usage metrics. No CloudWatch custom metrics for AI workloads.
- **Gap**: No LLM usage to track. Infrastructure for cost tracking must be established before agent deployment.
- **Recommendation**: When integrating Bedrock, implement per-request token counting. Log usage objects from LLM responses. Create CloudWatch custom metrics for token usage with dimensions for user/feature/workflow attribution. Establish tiered retention policies.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics. No `cloudwatch.put_metric_data` calls in application code (despite AWS SDK being in `build.gradle`). No business outcome tracking (basket conversion rate, product views, user signups). Only infrastructure-level CloudWatch agent for log collection.
- **Gap**: Zero business metrics. Only raw log collection.
- **Recommendation**: Publish custom CloudWatch metrics for: basket additions per minute, unique users per hour, product catalog views. Create dashboards tracking business KPIs alongside infrastructure metrics.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection. No error rate alarms. No latency p99 alarms. No PagerDuty, OpsGenie, or SNS alert integration. No composite alarms. No alerting of any kind configured in CloudFormation.
- **Gap**: Zero alerting and anomaly detection. Silent failures are undetectable.
- **Recommendation**: Configure CloudWatch anomaly detection on error rates and latency for all endpoints. Set up SNS topics for alert routing. Implement composite alarms for service health. Add PagerDuty/OpsGenie integration.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Direct-to-production deployment via CloudFormation cfn-init on a single EC2 instance. `MonoToMicroCF.yaml` EC2Instance `configure` step clones the repo and runs `gradlew clean build` on the instance. The `start-service` step starts the application via systemd. No canary, blue/green, or gradual rollout. No CodeDeploy. No traffic shifting. No feature flags.
- **Gap**: No deployment strategy. Every deployment is a full reprovisioning. No ability to test in production incrementally.
- **Recommendation**: Migrate to ECS Fargate with CodeDeploy blue/green deployment. Configure canary traffic shifting (10% → 50% → 100%) with CloudWatch alarm-based rollback.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files found in the repository (confirmed by searching for `*test*`, `*Test*`, `*spec*`, `*Spec*` patterns). `build.gradle` includes `testImplementation('org.springframework.boot:spring-boot-starter-test')` but no actual test classes exist. No integration test directories. No API test suites (no Postman collections, no Newman). No contract tests. No end-to-end test pipelines.
- **Gap**: Zero tests of any kind. Test dependency in build.gradle is unused.
- **Recommendation**: Add unit tests for service and repository layers using Spring Boot Test. Add integration tests for API endpoints using MockMvc or TestRestTemplate. Add contract tests for service boundaries. Run tests in CI pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files in the repository. No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. The `mono2micro.service` systemd unit has `Restart=on-failure` with `RestartSec=60` — this is the only self-healing pattern (process restart on crash). No links to runbooks in alert configurations (no alerts exist). No structured incident response process.
- **Gap**: No incident response automation beyond basic process restart. No runbooks. No self-healing beyond systemd restart.
- **Recommendation**: Create machine-readable runbooks (YAML/Markdown) for common failure scenarios. Implement SSM Automation documents for automated remediation (e.g., instance restart, service restart, database failover). Link runbooks to CloudWatch alarms via SNS.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No SLO definition files or dashboards with named owners. No CODEOWNERS file in the repository. No platform team tooling configuration. No per-service dashboards or alarms. No evidence of developer-owned instrumentation. No shared responsibility model documented.
- **Gap**: No observability governance. No ownership model. No SLO-driven culture.
- **Recommendation**: Add CODEOWNERS file mapping service areas to team owners. Define SLOs with named owners. Create per-service observability dashboards. Establish a shared responsibility model for agent-level SLOs (task success rate, tool error rate).

---

## Appendix: Evidence Index

| # | File | Key Findings |
|---|------|-------------|
| 1 | `MonoToMicroLegacy/build.gradle` | Java 8, Spring Boot 2.1, MyBatis 3.2, MySQL Connector 8.0, AWS SDK v1.11, no test libraries used, no AI/agent frameworks, no resilience libraries |
| 2 | `MonoToMicroAssets/MonoToMicroCF.yaml` | VPC, 2 public + 2 private subnets, EC2 instances (app + self-managed MySQL), Aurora MySQL 5.7 (EOL), S3 buckets, IAM roles, DMS replication, RefactorSpaces, nginx proxy, cfn-init deployment, hardcoded credentials, no encryption, no alarms |
| 3 | `MonoToMicroAssets/MonoToMicroCFDDB.yaml` | DynamoDB table `unishop-users`, Lambda IAM role with least-privilege DynamoDB access and X-Ray write access |
| 4 | `MonoToMicroAssets/MonoToMicroLambda.yaml` | Three Lambda functions (AddUnicornToBasket, RemoveUnicornFromBasket, GetUnicornsBasket) with X-Ray active tracing — planned basket service extraction |
| 5 | `MonoToMicroLegacy/src/main/resources/application.properties` | Hardcoded DB credentials (MonoToMicroUser/MonoToMicroPassword), single MySQL datasource on port 3306 |
| 6 | `MonoToMicroLegacy/database/create_tables.sql` | 3 tables (unicorns, unicorns_basket, unicorn_user), no stored procedures, no triggers, standard MySQL DDL, UNIQUE constraints |
| 7 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/rest/controller/BasketController.java` | REST controller for basket CRUD, @PreAuthorize("permitAll()") on all endpoints, synchronous service calls |
| 8 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | GET /unicorns endpoint, permitAll(), synchronous |
| 9 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/rest/controller/UserController.java` | POST /user (create), POST /user/login (lookup by email only, no password verification) |
| 10 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/rest/controller/HealthController.java` | System.out.println logging, EC2 metadata access, basic health endpoints |
| 11 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | OAuth2 @EnableResourceServer configured but authorizeRequests().anyRequest().permitAll() — auth completely disabled |
| 12 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | Unicorn catalog + basket logic in same service (coupling), direct repository calls, no resilience |
| 13 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | try/catch with e.printStackTrace(), null returns on failure, no retries, no timeouts |
| 14 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | Synchronized create method, e.printStackTrace() error handling |
| 15 | `MonoToMicroLegacy/src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | INSERT IGNORE (idempotency), JOIN across unicorns/unicorns_basket (coupling), standard SQL |
| 16 | `MonoToMicroLegacy/src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | INSERT IGNORE for user creation, getByEmail query, no password field in schema |
| 17 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/config/MyBatisConfig.java` | Centralized MyBatis config, single DataSource, 3 mapper beans |
| 18 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/core/model/CoreModel.java` | Shared base model with @JsonIgnore audit fields, Joda DateTime usage |
| 19 | `.github/workflows/cfn-security.yml` | Only CI pipeline: cfn-nag security scan on MonoToMicroAssets/, no build/test/deploy |
| 20 | `MonoToMicroLegacy/src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | GET /data endpoint, calls getAllBaskets() synchronously — potential long-running operation |
