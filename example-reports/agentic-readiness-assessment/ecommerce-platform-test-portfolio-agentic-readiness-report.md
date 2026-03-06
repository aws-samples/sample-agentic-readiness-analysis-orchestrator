# Portfolio Agentic Readiness Assessment Report
**Portfolio**: ecommerce-platform-test
**Services Assessed**: 4
**Assessment Date**: 2026-03-06
**Assessed by**: AWS Transform Custom — Portfolio Agentic Readiness Assessment

---

## Table of Contents

1. Executive Dashboard
2. Portfolio Readiness Overview
3. Service Dependency Map
4. Cross-Cutting Concerns
5. Portfolio Modernization Roadmap
   - Phase 0 — Foundation (Months 0-1)
   - Phase 1 — Core Services (Months 1-3)
   - Phase 2 — Dependent Services (Months 3-6)
   - Phase 3 — Optimization (Months 6-9)
6. AWS Modernization Pathways
7. Integration Opportunities
8. Resource Allocation Recommendations
9. Recommended Self-Paced Learning Materials
10. Risk Analysis
11. Service-by-Service Summary
12. Appendix: Assessment Inventory

---

## Executive Dashboard

The ecommerce-platform-test portfolio comprises four services spanning two monolithic applications and two serverless microservice architectures. With a portfolio-wide readiness score of **1.73 / 4.0**, the portfolio is firmly in the "Needs Work" category — no service is currently ready for agentic workloads. The most critical finding is a **circular dependency** between aws-microservices and books-api (synchronous REST + asynchronous EventBridge) that must be resolved before independent modernization can proceed. Three of four services lack CI/CD pipelines, all four lack API documentation (OpenAPI specs), and zero services have any AI/agent framework integration, vector databases, or RAG pipelines.

The strongest capability across the portfolio is **Data Foundations architecture** — all services use clean schemas with no stored procedures, and data sources are well-contained (scoring 4/4 on DATA-Q11 across all four services). The weakest dimension is **Operations & Observability** (portfolio score 1.25/4.0), where virtually every service lacks distributed tracing, structured logging, SLOs, and deployment automation. Security is the second-weakest category (1.53/4.0), with hardcoded credentials in two services, zero authentication on one service's APIs, and no centralized identity provider across the portfolio.

The recommended approach is a **9-month, four-phase modernization roadmap** starting with shared infrastructure (CI/CD, observability, authentication, secrets management) in Phase 0, followed by aggressive modernization of the three P0 services in Phase 1, stabilization and enhancement of books-api in Phase 2, and portfolio-wide AI/agent enablement in Phase 3. Six of seven AWS Modernization Pathways are triggered, with Move to Cloud Native, Move to Modern DevOps, Move to Managed Databases, and Move to AI all affecting 75-100% of the portfolio.

### Portfolio Readiness Score: 1.73 / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | 2.20 / 4.0 | ✅ 0 services, 🟡 2 services, 🟠 1 services, ❌ 1 services | 🟠 |
| Application Architecture | 1.65 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 services, ❌ 3 services | ❌ |
| Data Foundations | 1.93 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 3 services, ❌ 0 services | 🟠 |
| Identity, Security & Governance | 1.53 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 services, ❌ 3 services | ❌ |
| Operations & Observability | 1.25 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 services, ❌ 3 services | ❌ |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): 0 services (0%)
- 🟡 Partial (2.5-3.4): 0 services (0%)
- 🟠 Needs Work (1.5-2.4): 3 services (75%)
- ❌ Not Ready (< 1.5): 1 service (25%)

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | 4 | 2 monoliths, 2 serverless microservice architectures |
| Average Readiness Score | 1.73 / 4.0 | All services require significant modernization |
| Services Ready for Agents | 0 (0%) | No service is currently agent-ready |
| Critical Dependencies | 1 circular | aws-microservices ↔ books-api (SYNC + ASYNC cycle) |
| Shared Infrastructure Gaps | 30+ | Cross-cutting concerns affecting 3+ services |
| Estimated Modernization Effort | High | Portfolio-wide modernization across all 5 categories |
| Expected Timeline | 9 months | 4 phases with 2-3 parallel tracks |

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- PHP 8.2: 1 service (25%) — local-monolith
- Java 8 / Spring Boot 2.1: 1 service (25%) — unishop-monolith
- TypeScript / Node.js 22.x: 1 service (25%) — books-api
- JavaScript / Node.js 14.x (EOL): 1 service (25%) — aws-microservices

**Database Engines:**
- MySQL / Aurora MySQL: 2 services (50%) — local-monolith (RDS MySQL 8.4.8), unishop-monolith (Aurora MySQL 5.7 EOL + self-managed MySQL on EC2)
- DynamoDB: 2 services (50%) — books-api (1 table), aws-microservices (3 tables)

**Compute Patterns:**
- Serverless (Lambda): 2 services (50%) — books-api, aws-microservices
- Containers (App Runner / Docker): 1 service (25%) — local-monolith
- EC2: 1 service (25%) — unishop-monolith

**Infrastructure as Code:**
- CloudFormation / SAM: 3 services (75%) — local-monolith, unishop-monolith, books-api
- CDK: 2 services (50%) — books-api (pipeline), aws-microservices

**Deployment Maturity:**
- Full CI/CD: 1 service (25%) — books-api (CodePipeline with staging + production + manual approval)
- Partial CI/CD: 0 services (0%)
- Manual deployment: 3 services (75%) — local-monolith (deploy.sh), unishop-monolith (cfn-init on EC2), aws-microservices (manual cdk deploy)

### Common Strengths

1. **Clean Data Architecture (DATA-Q11: 4/4 across all services)**: All four services keep business logic in the application layer with no stored procedures, triggers, or proprietary SQL constructs. This significantly simplifies database migration and service extraction.
2. **Structured JSON API Responses (APP-Q5: 3-4/4 across all services)**: All services return well-structured JSON from their API endpoints, providing a solid foundation for agent tool integration.
3. **Contained Data Sources (DATA-Q4: 3-4/4 across all services)**: Each service has well-defined, contained data sources — no sprawl of databases, caches, and external APIs. This simplifies agent data access patterns.
4. **IaC Foundation (INF-Q5: 3-4/4 across all services)**: All services have meaningful IaC coverage (CloudFormation, SAM, or CDK), providing a foundation for adding monitoring, security, and deployment automation resources.
5. **Serverless Leader (books-api)**: books-api demonstrates a mature serverless pattern with Lambda, DynamoDB, Cognito, CI/CD with progressive deployments, and X-Ray tracing — a reference implementation for the portfolio.

### Common Gaps

1. **No AI/Agent Frameworks (APP-Q13: 1/4 across all 4 services)**: Zero services have any AI SDK, Bedrock integration, or agent framework. This is the fundamental blocker for agentic readiness.
2. **No API Documentation (APP-Q2: 1/4 across all 4 services)**: No service has OpenAPI specifications. Agents cannot discover or invoke tools without machine-readable API descriptions.
3. **No Vector Database or RAG (DATA-Q1, DATA-Q3: 1/4 across all 4 services)**: No semantic search, no embeddings, no retrieval-augmented generation capability anywhere in the portfolio.
4. **Weak Observability (OPS-Q2, OPS-Q7, OPS-Q12: 1/4 across 3-4 services)**: Three of four services lack structured logging, all four lack business metrics, and none have observability governance.
5. **No API Versioning (APP-Q11: 1/4 across all 4 services)**: No service implements API versioning, creating risk of breaking agent integrations during modernization.
6. **No Rate Limiting (APP-Q8, SEC-Q5: 1/4 across all 4 services)**: No service has API rate limiting or throttling — a critical gap for agent workloads that generate high-frequency programmatic calls.
7. **Inconsistent Security Posture (SEC category: 1.2-2.1 range)**: Hardcoded credentials in 2 services, no authentication on 1 service, and no centralized identity provider across the portfolio.

## Service Dependency Map

### High-Level Architecture

The portfolio consists of four e-commerce services with minimal inter-service coupling. Two services (local-monolith and unishop-monolith) are fully isolated monoliths with no external service dependencies. The remaining two services (aws-microservices and books-api) have a bidirectional dependency — aws-microservices publishes events to EventBridge consumed by books-api (async), while books-api calls aws-microservices REST APIs synchronously. This creates a circular dependency that must be resolved before independent modernization.

### Service Dependency Matrix

| Service | Depends On | Depended On By | Coupling Score | Fan-In | Fan-Out | Blast Radius | Priority |
|---------|------------|----------------|----------------|--------|---------|--------------|----------|
| unishop-monolith | None | None | None (isolated) | 0 | 0 | 0% | P0 |
| local-monolith | None | None | None (isolated) | 0 | 0 | 0% | P0 |
| aws-microservices | books-api (SYNC) | books-api (ASYNC) | Medium | 1 | 1 | 25% | P0 |
| books-api | aws-microservices (ASYNC) | aws-microservices (SYNC) | Medium | 1 | 1 | 25% | P1 |

**Coupling Score Definitions:**
- **High**: Synchronous dependencies + shared databases, OR 3+ dependency types
- **Medium**: Synchronous dependency OR 2 dependency types — aws-microservices ↔ books-api (SYNC + ASYNC = 2 types)
- **Low**: Asynchronous only OR shared infrastructure only

**Priority Definitions:**
- **P0**: Critical path services that block others OR lowest-scoring services requiring immediate attention — unishop-monolith (1.4), local-monolith (1.5), aws-microservices (1.8)
- **P1**: Important services with moderate dependencies — books-api (2.2, highest score, depends on aws-microservices stabilization)

### Critical Path Analysis

1. **⚠️ Circular Dependency (Phase 0 Resolution Required)**:
   - **Cycle**: aws-microservices → books-api (ASYNC via EventBridge) → aws-microservices (SYNC via REST)
   - **Risk**: Neither service can be independently deployed or modernized without affecting the other
   - **Resolution**: Replace the synchronous REST call from books-api → aws-microservices with an asynchronous EventBridge pattern, establishing clear unidirectional async contracts

2. **Foundation Services** (must be modernized first):
   - unishop-monolith: Lowest score (1.4), isolated — no dependencies to sequence against, can start immediately
   - local-monolith: Second-lowest score (1.5), isolated — can start in parallel with unishop-monolith

3. **Independent Services** (can be parallelized):
   - unishop-monolith and local-monolith have zero dependencies and can be modernized fully in parallel

### Integration Points

**Synchronous Integrations:**
- books-api → aws-microservices: REST API calls for product/catalog data retrieval

**Asynchronous Integrations:**
- aws-microservices → books-api: EventBridge events (e.g., checkout or catalog change events consumed by books-api)

**Shared Infrastructure:**
- No shared databases between services (good — each service owns its data)
- No shared API gateways (each service has its own)
- No shared authentication provider (gap — should be unified via Cognito)

## Cross-Cutting Concerns

### Infrastructure & Platform

**Portfolio Score: 2.20 / 4.0**

The portfolio shows a split between serverless services (books-api and aws-microservices scoring 2.6-2.7) and monoliths (unishop-monolith at 1.4, local-monolith at 2.1). The serverless services benefit from fully managed compute and databases but lack async messaging and workflow orchestration. The monoliths lack containerization, CI/CD, and modern compute patterns.

**Common Patterns:**
- IaC is present across all 4 services (CloudFormation, SAM, or CDK) with scores of 3-4
- Auto-scaling ranges from 1 (unishop on EC2) to 3 (Lambda + DynamoDB on-demand)

**Critical Gaps:**
1. **No CI/CD Pipelines (INF-Q6)**: 3 of 4 services (75%) — local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4). Only books-api has CI/CD.
   - Impact: Manual deployments prevent rapid, safe iteration cycles required for agentic workloads
   - Recommendation: Establish portfolio-wide CI/CD templates using CodePipeline or GitHub Actions; books-api's pipeline can serve as a reference implementation

2. **No Workflow Orchestration (INF-Q3)**: 4 of 4 services (100%) — all score 1-2/4
   - Impact: No Step Functions or workflow engine for multi-step agent orchestration
   - Recommendation: Introduce AWS Step Functions as the portfolio standard for workflow orchestration; prioritize the checkout saga in aws-microservices and fulfillment workflow in local-monolith

3. **No Real-time Streaming (INF-Q8)**: 4 of 4 services (100%) — all score 1-2/4
   - Impact: Cannot support real-time event analytics or embedding refresh pipelines for RAG
   - Recommendation: Standardize on EventBridge for event routing and DynamoDB Streams/Kinesis for CDC; low priority until Phase 3

### Application Architecture

**Portfolio Score: 1.65 / 4.0**

This is the second-weakest category. The most severe gaps are universal: no API documentation, no API versioning, no AI frameworks, and no rate limiting across any service. The portfolio shows a wide range of architectural maturity — from a single-file PHP monolith (local-monolith, APP-Q4: 1/4) to well-decomposed microservices (aws-microservices, APP-Q4: 4/4).

**Critical Gaps:**
1. **No API Documentation (APP-Q2: 1/4)**: affects 4 of 4 services (100%)
   - Impact: Agents cannot discover or invoke tools without OpenAPI specifications
   - Recommendation: Generate OpenAPI 3.0 specs for all services in Phase 0; use SAM/CDK integration for API Gateway validation

2. **No AI/Agent Frameworks (APP-Q13: 1/4)**: affects 4 of 4 services (100%)
   - Impact: Fundamental blocker for agentic readiness — no Bedrock, LangChain, or Strands SDK
   - Recommendation: Phase 3 activity; TypeScript services should use Strands Agents SDK, Java services should use Spring AI or LangChain4j

3. **No Rate Limiting (APP-Q8: 1/4)**: affects 4 of 4 services (100%)
   - Impact: No protection against runaway agent loops or API abuse at machine speed
   - Recommendation: Add API Gateway throttling and WAF rate-based rules to all services in Phase 0-1

4. **No API Versioning (APP-Q11: 1/4)**: affects 4 of 4 services (100%)
   - Impact: Breaking changes will disrupt agent tool integrations with no backward compatibility
   - Recommendation: Adopt URL path versioning (/v1/) across all services during API documentation phase

### Data Foundations

**Portfolio Score: 1.93 / 4.0**

Data Foundations has the best portfolio score among the weaker categories, primarily because all services maintain clean schemas (DATA-Q11: 4/4 everywhere) and contained data sources (DATA-Q4: 3-4/4). The critical gaps are entirely in AI/agent-specific capabilities: no vector databases, no RAG pipelines, and no embedding infrastructure.

**Critical Gaps:**
1. **No Vector Database (DATA-Q1: 1/4)**: affects 4 of 4 services (100%)
   - Impact: No semantic search, no similarity matching, no agent knowledge base
   - Recommendation: Deploy managed vector infrastructure in Phase 3; evaluate OpenSearch Serverless and Bedrock Knowledge Bases

2. **No RAG Pipeline (DATA-Q3: 1/4)**: affects 4 of 4 services (100%)
   - Impact: Agents cannot access contextual information through semantic retrieval
   - Recommendation: Build RAG pipelines per service using Bedrock Knowledge Bases in Phase 3

3. **No Embedding Freshness (DATA-Q9: 1/4)**: affects 4 of 4 services (100%)
   - Impact: When embeddings are implemented, no CDC mechanism exists to keep them current
   - Recommendation: Enable DynamoDB Streams on serverless services and set up event-driven embedding refresh

### Identity, Security & Governance

**Portfolio Score: 1.53 / 4.0**

Security is the second-weakest category and presents the most immediate risk to the portfolio. Two services have hardcoded credentials in source code, one service has completely unauthenticated APIs, and no service has a centralized identity provider that could support cross-service agent authentication.

**Critical Gaps:**
1. **No Centralized Identity (SEC-Q10)**: 3 of 4 services score 1/4 (75%), only books-api has Cognito (3/4)
   - Impact: No unified authentication for cross-service agent operations; cannot implement identity propagation
   - Recommendation: Deploy a shared Cognito User Pool in Phase 0; federate all services through this provider

2. **Weak API Authentication (SEC-Q9)**: 3 of 4 services score 1-2/4 (75%) — aws-microservices has zero auth, others are partial
   - Impact: Unprotected APIs allow unauthorized agent access and cannot attribute actions to users
   - Recommendation: Add Cognito authorizers to all API Gateway endpoints in Phase 0-1

3. **Hardcoded Credentials (SEC-Q1)**: 2 of 4 services (50%) — local-monolith (1/4) and unishop-monolith (1/4)
   - Impact: Critical security vulnerability; credentials in source code cannot be rotated
   - Recommendation: Migrate all secrets to AWS Secrets Manager in Phase 0

4. **No PII Redaction (SEC-Q6: 1/4)**: affects 4 of 4 services (100%)
   - Impact: PII exposed in API responses and logs; stack traces leak implementation details
   - Recommendation: Implement log scrubbing and response masking as part of structured logging initiative

### Operations & Observability

**Portfolio Score: 1.25 / 4.0**

Operations is the weakest category by a significant margin. Only books-api has meaningful observability (X-Ray tracing, CloudWatch alarms, progressive deployments), while the remaining three services have essentially zero operational maturity. This is a critical blocker for agentic workloads, which require deep observability to detect agent misbehavior, track performance, and ensure safety.

**Critical Gaps:**
1. **No Structured Logging (OPS-Q2)**: 3 of 4 services score 1/4 (75%), aws-microservices scores 2/4
   - Impact: Cannot debug agent workflows, cannot correlate requests across services
   - Recommendation: Standardize on AWS Lambda Powertools Logger (for serverless) and Logback JSON (for Java) across all services

2. **No SLOs (OPS-Q4)**: 3 of 4 services score 1/4 (75%)
   - Impact: No performance baselines, no alerting on degradation, no error budgets
   - Recommendation: Define SLOs per service for availability, latency p99, and error rate; implement CloudWatch alarms

3. **No Deployment Strategy (OPS-Q9)**: 3 of 4 services score 1/4 (75%)
   - Impact: Direct-to-production deployments with no safety net; cannot safely iterate on agent configurations
   - Recommendation: Implement canary/progressive deployments for all services; books-api's Linear10Percent pattern as reference

4. **No Integration Testing (OPS-Q10)**: 3 of 4 services score 1/4 (75%)
   - Impact: No regression protection; deploying agent integrations without tests amplifies risk
   - Recommendation: Establish integration test suites per service; integrate into CI/CD pipelines

## Portfolio Modernization Roadmap

This roadmap accounts for cross-service dependencies, shared infrastructure needs, and organizational capacity. Work is sequenced to minimize risk and maximize value delivery, with the circular dependency between aws-microservices and books-api addressed first.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities (CI/CD, observability, authentication, secrets) before service-specific work
2. **Dependency Order**: Circular dependency broken in Phase 0; upstream services stabilized before downstream dependents
3. **Risk Mitigation**: EOL runtimes (Node.js 14.x, Aurora MySQL 5.7), hardcoded credentials, and unauthenticated APIs addressed in Phase 0-1
4. **Parallel Tracks**: Isolated monoliths (unishop-monolith, local-monolith) modernized concurrently in Phase 1
5. **Quick Wins**: API documentation, structured logging, and secret migration build momentum and demonstrate value early

### Phase 0 — Foundation (Months 0-1)

**Objective**: Establish shared capabilities, resolve the circular dependency, and address critical security risks

**Shared Infrastructure:**
- Deploy shared Cognito User Pool for portfolio-wide authentication: benefits all 4 services
- Create portfolio-wide CI/CD pipeline templates (GitHub Actions / CodePipeline): benefits 3 services (local-monolith, unishop-monolith, aws-microservices)
- Deploy unified observability stack (OpenTelemetry Collector + CloudWatch): benefits all 4 services
- Create standardized structured logging library configuration: benefits all 4 services

**Critical Risk Mitigation:**
- Break circular dependency: replace books-api → aws-microservices synchronous REST call with EventBridge async pattern
- Migrate hardcoded credentials to AWS Secrets Manager: local-monolith and unishop-monolith
- Add Cognito authorizer to aws-microservices APIs (currently zero authentication)
- Remove stack trace exposure from aws-microservices error responses (SEC-Q6)

**Platform Capabilities:**
- Generate OpenAPI 3.0 specifications for all 4 services — foundation for agent tool definitions
- Establish API versioning standard (URL path versioning /v1/)
- Create IaC templates for monitoring (CloudWatch alarms, dashboards)

**Organizational Enablers:**
- Training: Containers/EKS, Serverless/Lambda Powertools, Modern DevOps, CDK
- Tooling: Standardize on CDK for new IaC; establish coding standards
- Standards: API documentation requirements, logging format, security baseline

**Expected Outcomes:**
- Circular dependency eliminated — services can be independently deployed
- All credentials moved to Secrets Manager — no hardcoded secrets
- All APIs authenticated via Cognito
- OpenAPI specs available for all services

**Estimated Effort**: High

### Phase 1 — Core Services (Months 1-3)

**Objective**: Modernize the three P0 services that form the portfolio's foundation

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.4/4.0)
   - Current State: Java 8/Spring Boot 2.1 monolith on raw EC2, self-managed MySQL, Aurora MySQL 5.7 (EOL), no CI/CD, hardcoded credentials, no auth
   - Target State: Containerized on ECS Fargate behind API Gateway with Cognito, Aurora MySQL 3.x, CI/CD pipeline, structured logging, X-Ray tracing
   - Key Activities:
     - Create Dockerfile, containerize Spring Boot JAR, deploy to ECS Fargate
     - Set up CI/CD pipeline (GitHub Actions: build → test → push ECR → deploy ECS)
     - Upgrade Java 8 → 17+ and Spring Boot 2.1 → 3.x
     - Upgrade Aurora MySQL 5.7 → 3.x (MySQL 8.0-compatible); eliminate self-managed MySQL EC2
     - Add X-Ray tracing and structured JSON logging (Logback)
     - Enforce Cognito JWT authentication on all endpoints (replace `permitAll()`)
   - Dependencies: Phase 0 shared Cognito User Pool and CI/CD templates
   - Blocks: None (isolated service)
   - Estimated Effort: High

2. **local-monolith** (P0, Score: 1.5/4.0)
   - Current State: PHP single-file monolith on Docker/App Runner, manual deploy.sh, no monitoring, hardcoded credentials
   - Target State: Containerized on EKS, CI/CD pipeline, structured logging, distributed tracing, first microservice extracted (Inventory)
   - Key Activities:
     - Create EKS cluster IaC (Terraform/CloudFormation) with ALB Ingress Controller
     - Deploy monolith to EKS behind ALB; migrate from App Runner per user preference
     - Set up CI/CD pipeline (CodePipeline: build → test → push ECR → deploy EKS)
     - Add structured JSON logging (Monolog) with correlation IDs
     - Deploy OpenTelemetry Collector as EKS DaemonSet for distributed tracing
     - Begin Strangler Fig extraction of Inventory Service (lowest coupling domain)
   - Dependencies: Phase 0 CI/CD templates and observability stack
   - Blocks: None (isolated service)
   - Estimated Effort: High

3. **aws-microservices** (P0, Score: 1.8/4.0)
   - Current State: Lambda/DynamoDB/EventBridge with Node.js 14.x (EOL), no auth, no CI/CD, no tracing, stack traces in error responses
   - Target State: Node.js 20.x, Cognito auth on all APIs, CI/CD pipeline, X-Ray tracing, structured logging, idempotency, integration tests
   - Key Activities:
     - Upgrade Lambda runtime from Node.js 14.x → 20.x; remove `aws-sdk` external modules config
     - Set up CI/CD pipeline (GitHub Actions: lint → build → test → cdk synth → cdk deploy)
     - Enable X-Ray tracing on all Lambda functions and API Gateway
     - Add structured logging with Lambda Powertools Logger
     - Implement idempotency on write operations using Lambda Powertools Idempotency
     - Write integration tests (uncomment and expand `test/aws-microservices.test.ts`)
     - Add DLQ to SQS OrderQueue for failed checkout events
   - Dependencies: Phase 0 Cognito User Pool and circular dependency resolution
   - Blocks: books-api (Phase 2) depends on aws-microservices API stabilization
   - Estimated Effort: Medium

**Cross-Service Activities:**
- Validate all Phase 0 shared infrastructure is operational
- Verify OpenAPI specs are accurate and complete for all services

**Expected Outcomes:**
- All P0 services have CI/CD pipelines, authentication, and observability
- EOL runtimes and databases upgraded
- Monoliths containerized and ready for incremental decomposition

**Estimated Effort**: High

### Phase 2 — Dependent Services (Months 3-6)

**Objective**: Modernize books-api (dependent on aws-microservices stabilization) and continue monolith decomposition

**Services in Scope:**

1. **books-api** (P1, Score: 2.2/4.0)
   - Current State: Well-architected serverless API with Lambda/DynamoDB/Cognito/CI/CD, but lacks async patterns, rate limiting, observability depth, and AI capabilities
   - Target State: Event-driven serverless with EventBridge, rate limiting, enhanced observability, API versioning, AWS SDK v3
   - Key Activities:
     - Add EventBridge integration for domain events (BookCreated, BookRetrieved)
     - Implement API Gateway throttling and usage plans with API keys
     - Add structured logging with Lambda Powertools Logger
     - Implement API versioning (/v1/books)
     - Upgrade AWS SDK v2 → v3 (modular, tree-shakeable)
     - Add idempotency to CreateBook using Lambda Powertools
     - Expand E2E test suite to cover new async patterns
     - Define SLOs and CloudWatch dashboards
   - Dependencies: aws-microservices (Phase 1) APIs must be stable
   - Blocks: None
   - Estimated Effort: Medium

2. **Continue Monolith Decomposition**:
   - unishop-monolith: Extract Basket service using Strangler Fig → Lambda + DynamoDB (infrastructure partially exists in MonoToMicroLambda.yaml)
   - local-monolith: Extract Orders service using Strangler Fig; implement SQS for async fulfillment events

**Parallel Tracks:**
- books-api modernization and monolith decomposition can proceed concurrently (no dependencies)

**Expected Outcomes:**
- books-api fully modernized with event-driven patterns and enhanced observability
- First microservices extracted from both monoliths
- All 4 services have consistent observability and security posture

**Estimated Effort**: Medium

### Phase 3 — Optimization (Months 6-9)

**Objective**: Enable agentic capabilities across the portfolio and implement advanced optimizations

**Activities:**
- Deploy vector databases across services (OpenSearch Serverless or Bedrock Knowledge Bases)
- Implement RAG pipelines for product catalogs and book data
- Integrate Amazon Bedrock agent frameworks — create e-commerce assistant and fulfillment automation agents
- Add agent evaluation frameworks with golden datasets per service
- Implement LLM cost tracking with CloudWatch custom metrics and per-request attribution
- Deploy end-to-end distributed tracing across all services with gen_ai semantic conventions
- Implement unified observability platform with centralized dashboards
- Add human-in-the-loop workflows via Step Functions for high-risk agent actions
- Continue monolith decomposition — extract Payments, Returns services from monoliths

**Expected Outcomes:**
- All services have agent-ready APIs with tools defined from OpenAPI specs
- RAG-powered semantic search across product catalogs
- Automated evaluation pipelines ensuring agent quality
- Unified observability with agent-specific SLOs and anomaly detection

**Estimated Effort**: High

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 9 months (with 2-3 parallel tracks per phase)

| Phase | Duration | Services | Effort | Key Deliverables |
|-------|----------|----------|--------|-----------------|
| Phase 0 | Months 0-1 | All 4 (shared) | High | CI/CD templates, Cognito, observability, API docs, secrets migration |
| Phase 1 | Months 1-3 | unishop, local-monolith, aws-microservices | High | Containerization, EOL upgrades, CI/CD, auth, tracing |
| Phase 2 | Months 3-6 | books-api, monolith decomposition | Medium | Event-driven patterns, rate limiting, service extraction |
| Phase 3 | Months 6-9 | All 4 | High | Vector DBs, RAG, agents, evals, LLM cost tracking |

## AWS Modernization Pathways

Based on the portfolio-wide assessment findings, the following AWS Modernization Pathways have been identified for each service. The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach — a customer portfolio may be divided into multiple pathways depending on workloads and priorities, and these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 4 services | 100% | High | High |
| Move to Containers | 3 services | 75% | High | Medium |
| Move to Open Source | 0 services | 0% | N/A | N/A |
| Move to Managed Databases | 4 services | 100% | High | Medium |
| Move to Managed Analytics | 4 services | 100% | Medium | Low |
| Move to Modern DevOps | 3 services | 75% | High | High |
| Move to AI | 4 services | 100% | High | High |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| local-monolith | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| unishop-monolith | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| books-api | ✅ | — | — | ✅ | ✅ | — | ✅ |
| aws-microservices | ✅ | — | — | ✅ | ✅ | ✅ | ✅ |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- **Move to Containers** should precede **Move to Cloud Native** for monoliths (containerize before decomposing into microservices)
- **Move to Modern DevOps** enables faster execution of all other pathways (CI/CD accelerates delivery, observability enables safe changes)
- **Move to Managed Databases** and **Move to Cloud Native** are prerequisites for **Move to AI** (data foundations and service boundaries needed for agent tools)
- **Move to Open Source** is not applicable (MySQL is already open source, DynamoDB is managed NoSQL)

**Parallel Execution Tracks:**
- **Track 1 (Phase 0-1)**: Move to Containers + Move to Modern DevOps — containerize monoliths while building CI/CD pipelines and observability simultaneously
- **Track 2 (Phase 1-2)**: Move to Managed Databases — database migrations (Aurora MySQL 5.7 → 3.x, eliminate self-managed MySQL) can proceed alongside containerization
- **Track 3 (Phase 2-3)**: Move to Cloud Native — decompose monoliths and expand async patterns after containers and databases are modernized
- **Track 4 (Phase 3)**: Move to AI — integrate agent frameworks and vector databases after Cloud Native and Managed Database foundations are in place

### Pathway Details

#### Move to Cloud Native

- **Services Affected**: local-monolith, unishop-monolith, books-api, aws-microservices (4 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - APP-Q4 < 4: affects 3 services (local-monolith=1, unishop-monolith=2, books-api=3)
  - APP-Q3 < 3: affects 4 services (all score 1-2)
  - APP-Q10 < 3: affects 3 services (local-monolith=1, unishop-monolith=1, aws-microservices=2)
- **Representative AWS Services**: Lambda, API Gateway, Step Functions, EventBridge, SQS, ECS Fargate, EKS
- **Key Activities**:
  1. Portfolio-level: Standardize on EventBridge for inter-service events; adopt Step Functions for workflow orchestration
  2. Per-service: Decompose monoliths (Strangler Fig), expand async patterns, add Step Functions workflows
- **Cross-Service Synergies**: EventBridge can serve as the portfolio-wide event bus; Step Functions patterns can be reused across services
- **Estimated Effort**: High across 4 services
- **Roadmap Phase Alignment**: Phase 1-2 (containerization → decomposition), Phase 3 (agent workflows)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

#### Move to Containers

- **Services Affected**: local-monolith, unishop-monolith, books-api (3 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q1 < 3: unishop-monolith (1/4, raw EC2)
  - APP-Q4 < 4: local-monolith (1/4, monolith), unishop-monolith (2/4), books-api (3/4)
- **Representative AWS Services**: ECS Fargate, EKS, ECR, App Runner
- **Key Activities**:
  1. unishop-monolith: Create Dockerfile for Spring Boot JAR → deploy to ECS Fargate
  2. local-monolith: Adapt existing Dockerfile for EKS deployment with Kubernetes manifests
  3. books-api: Already serverless Lambda — no containerization needed; triggered via APP-Q4 < 4 but containers not the right path
- **Estimated Effort**: Medium across 3 services
- **Roadmap Phase Alignment**: Phase 1 (Core Services)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

#### Move to Managed Databases

- **Services Affected**: local-monolith, unishop-monolith, books-api, aws-microservices (4 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q2 < 4: unishop-monolith (2/4, self-managed MySQL on EC2)
  - DATA-Q2 < 4: all 4 services (1/4, no vector database)
  - DATA-Q10 < 4: unishop-monolith (1/4, Aurora MySQL 5.7 EOL)
- **Representative AWS Services**: Aurora MySQL, DynamoDB, OpenSearch Serverless, Bedrock Knowledge Bases
- **Key Activities**:
  1. unishop-monolith: Upgrade Aurora MySQL 5.7 → 3.x; eliminate self-managed MySQL on EC2
  2. local-monolith: Align dev/prod MySQL versions; evaluate Aurora for production
  3. All services: Deploy managed vector databases (OpenSearch Serverless or Bedrock Knowledge Bases) for AI capabilities
- **Estimated Effort**: Medium across 4 services
- **Roadmap Phase Alignment**: Phase 1 (database upgrades), Phase 3 (vector databases)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Managed Analytics

- **Services Affected**: local-monolith, unishop-monolith, books-api, aws-microservices (4 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q8 < 3: all 4 services (scores 1-2, no managed streaming)
- **Representative AWS Services**: EventBridge, Kinesis Data Streams, Kinesis Data Firehose, Athena
- **Key Activities**:
  1. Evaluate whether EventBridge (from Cloud Native pathway) satisfies streaming needs
  2. Add Kinesis Data Streams if higher-throughput streaming is needed for analytics
  3. Set up S3 data lake with Athena for ad-hoc analytics
- **Estimated Effort**: Low across 4 services
- **Roadmap Phase Alignment**: Phase 2-3
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

#### Move to Modern DevOps

- **Services Affected**: local-monolith, unishop-monolith, aws-microservices (3 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q6 < 3: 3 services (all score 1/4 — no CI/CD)
  - OPS-Q1 < 3: 3 services (all score 1/4 — no tracing)
  - OPS-Q9 < 3: 3 services (all score 1/4 — no deployment strategy)
  - OPS-Q10 < 3: 3 services (all score 1/4 — no testing)
- **Representative AWS Services**: CodePipeline, CodeBuild, CodeDeploy, X-Ray, CloudWatch, CloudFormation, CDK
- **Key Activities**:
  1. Portfolio-level: Create CI/CD pipeline templates and observability standards
  2. Per-service: Build CI/CD pipelines, add tracing, structured logging, and integration tests
  3. Per-service: Implement progressive/canary deployment strategies
- **Cross-Service Synergies**: books-api's existing CI/CD pipeline serves as the reference implementation; Lambda Powertools patterns reusable across serverless services
- **Estimated Effort**: High across 3 services
- **Roadmap Phase Alignment**: Phase 0-1 (CI/CD, tracing, logging), Phase 2 (advanced deployment strategies)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: local-monolith, unishop-monolith, books-api, aws-microservices (4 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - APP-Q13 < 3: all 4 services (1/4 — no agent frameworks)
  - DATA-Q1 < 3: all 4 services (1/4 — no vector database)
  - DATA-Q3 < 3: all 4 services (1/4 — no RAG pipeline)
  - OPS-Q3 < 3: all 4 services (1/4 — no eval framework)
  - OPS-Q6 < 3: all 4 services (1/4 — no LLM cost tracking)
- **Representative AWS Services**: Amazon Bedrock, Bedrock Knowledge Bases, Bedrock AgentCore, OpenSearch Serverless, Strands Agents SDK
- **Key Activities**:
  1. Portfolio-level: Establish vector database infrastructure and Bedrock access patterns
  2. Per-service: Build RAG pipelines, integrate agent frameworks, create eval datasets
  3. Per-service: Implement LLM cost tracking and agent-specific observability
- **Estimated Effort**: High across 4 services
- **Roadmap Phase Alignment**: Phase 3 (Agent Enablement)
- **Relevant Learning Materials**: Module 7 — Move to AI

### Example: Parallel Pathway Execution for a Single Service

**unishop-monolith** simultaneously pursues:
- **Move to Containers** (Phase 1): Create Dockerfile, containerize Spring Boot JAR, deploy to ECS Fargate
- **Move to Modern DevOps** (Phase 0-1): Build CI/CD pipeline, add X-Ray tracing, structured logging
- **Move to Managed Databases** (Phase 1): Upgrade Aurora MySQL 5.7 → 3.x, eliminate self-managed MySQL EC2
- **Move to Cloud Native** (Phase 2): Extract Basket service using Strangler Fig, add EventBridge events
- **Move to Managed Databases** (Phase 3): Deploy vector database for product catalog semantic search
- **Move to AI** (Phase 3): Integrate Bedrock agents for product recommendations and conversational commerce

## Integration Opportunities

### Shared Service Extraction

**Opportunity 1: Centralized Authentication (Cognito User Pool)**
- **Current State**: Duplicated and inconsistent authentication across services — books-api has Cognito, aws-microservices has zero auth, monoliths use custom session/password mechanisms
- **Proposed Solution**: Deploy a single shared Amazon Cognito User Pool with OAuth2/OIDC flows, machine-to-machine client credentials for agent authentication, and user pools for human access
- **Services Affected**: All 4 services
- **Benefits**: Consistent identity across services, agent identity propagation, SSO capability, centralized MFA
- **Effort**: Medium
- **Priority**: High — prerequisite for secure agent operations

**Opportunity 2: Unified Observability Platform**
- **Current State**: books-api has X-Ray tracing only; other 3 services have zero observability. No structured logging standard. No cross-service trace correlation.
- **Proposed Solution**: Deploy OpenTelemetry Collector (ADOT) as a shared observability platform. Standardize on Lambda Powertools (serverless) and Logback JSON (Java) for structured logging. Centralize in CloudWatch with cross-service dashboards.
- **Services Affected**: All 4 services
- **Benefits**: End-to-end request tracing, unified log querying, consistent alerting, agent workflow visibility
- **Effort**: Medium
- **Priority**: High — required for safe agent deployment and debugging

**Opportunity 3: Portfolio API Catalog**
- **Current State**: No API documentation exists for any service. APIs discoverable only by reading source code.
- **Proposed Solution**: Generate OpenAPI 3.0 specs for all services. Create a centralized API catalog (API Gateway developer portal or custom documentation site). Use specs as the foundation for agent tool definitions.
- **Services Affected**: All 4 services
- **Benefits**: Agent tool discovery, consistent API documentation, request validation, developer onboarding
- **Effort**: Low
- **Priority**: High — fundamental prerequisite for agentic readiness

### Event-Driven Architecture

**Opportunity 1: Replace Synchronous Circular Dependency**
- **Current State**: books-api calls aws-microservices synchronously via REST API, while aws-microservices publishes to EventBridge consumed by books-api — creating a circular dependency
- **Proposed Solution**: Replace the synchronous REST call from books-api → aws-microservices with an EventBridge async pattern. books-api publishes a request event, aws-microservices processes it and publishes a response event.
- **Services Affected**: books-api, aws-microservices
- **Benefits**: Eliminates circular dependency, enables independent deployment, improves resilience
- **Effort**: Medium
- **Priority**: High — Phase 0 resolution required

**Opportunity 2: Portfolio-Wide Event Bus**
- **Current State**: Only aws-microservices uses EventBridge (for checkout flow). Other services have no event infrastructure.
- **Proposed Solution**: Establish a shared EventBridge custom event bus for portfolio-wide domain events (OrderCreated, ProductUpdated, BookCreated, UserRegistered). Each service publishes events to the bus; other services subscribe as needed.
- **Services Affected**: All 4 services
- **Benefits**: Loose coupling, event-driven agent triggers, audit trail for all domain events, embedding refresh triggers for RAG
- **Effort**: Medium
- **Priority**: Medium — Phase 2 activity

### Observability Unification

- **Current State**: books-api uses X-Ray + CloudWatch alarms; aws-microservices has basic console.log; monoliths have zero observability
- **Proposed Solution**: Standardize on X-Ray/ADOT for distributed tracing, Lambda Powertools Logger / Logback for structured logging, and CloudWatch for metrics/alarms/dashboards across all services
- **Services Affected**: All 4 services
- **Benefits**: End-to-end tracing across service boundaries, consistent metrics, unified alerting, reduced tool sprawl
- **Effort**: Medium
- **Priority**: High — Phase 0-1 activity

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + dedicated service teams (30+ cross-cutting concerns justify centralized approach)

**Platform Team** (dedicated):
- **Responsibilities**: Shared Cognito deployment, CI/CD pipeline templates, observability stack (ADOT, CloudWatch dashboards), IaC templates, security baseline (Secrets Manager patterns, encryption standards), API documentation standards, vector database infrastructure
- **Skills Required**: CDK/CloudFormation, Cognito/IAM, OpenTelemetry/X-Ray, CodePipeline/GitHub Actions, CloudWatch, EventBridge

**Service Team 1 — Monolith Modernization** (unishop-monolith + local-monolith):
- **Responsibilities**: Containerization, database migrations, service decomposition (Strangler Fig), EKS/ECS deployment
- **Skills Required**: Java/Spring Boot (unishop), PHP (local-monolith), Docker, ECS Fargate, EKS, MySQL/Aurora, domain-driven design
- **Note**: Both monoliths are isolated and can be worked in parallel by sub-teams

**Service Team 2 — Serverless Services** (aws-microservices + books-api):
- **Responsibilities**: Runtime upgrades, async pattern expansion, API hardening, agent integration (Phase 3)
- **Skills Required**: TypeScript/JavaScript, Lambda, DynamoDB, EventBridge, SAM/CDK, Lambda Powertools

### Skill Gaps

1. **EKS/Containers**: Required for local-monolith EKS deployment — currently not available (no EKS infrastructure exists)
2. **Serverless Patterns (Lambda Powertools)**: Required for structured logging, idempotency, and tracing across serverless services — not currently used
3. **IaC (CDK v2)**: Required for standardizing infrastructure across portfolio — aws-microservices uses CDK 2.17.0 (outdated), books-api uses CDK 2.189.1
4. **Observability (X-Ray/OpenTelemetry)**: Required for distributed tracing across all services — only books-api has basic X-Ray
5. **AI/Bedrock/Agents**: Required for Phase 3 agent enablement — zero AI capability exists in any service
6. **Database Migration (Aurora)**: Required for unishop-monolith Aurora MySQL 5.7 → 3.x upgrade — DMS partially configured but not executed

### Training Recommendations

- **Phase 0-1 Priority**: Containers/EKS, Modern DevOps (CI/CD, IaC), observability (X-Ray/OpenTelemetry) — skills needed immediately
- **Phase 2 Priority**: Serverless advanced patterns (Lambda Powertools, EventBridge), database migration (DMS, Aurora upgrades)
- **Phase 3 Priority**: AI/Bedrock, RAG pipelines, agent frameworks (Strands Agents SDK), agent evaluation

### External Support

- **Recommended**: AWS Professional Services or consulting partner engagement for:
  - EKS cluster setup and monolith-to-container migration (2-3 months, Phase 0-1)
  - Aurora MySQL 5.7 → 3.x migration planning and execution (1-2 months, Phase 1)
  - Agent framework architecture and initial implementation (2-3 months, Phase 3)
- **Knowledge Transfer**: External support should include knowledge transfer sessions to build internal capability

## Recommended Self-Paced Learning Materials

Based on portfolio-wide skill gaps, the following learning materials are recommended. All six triggered pathways are represented.

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more. Critical for the monolith decomposition strategy across unishop-monolith and local-monolith.
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
  - Primary learning path for local-monolith's EKS migration (preferred container platform).
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
  - Applicable for unishop-monolith's ECS Fargate deployment.
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
  - Directly applicable: unishop-monolith already has DMS partially configured for MySQL migration.
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Essential for understanding vector database options (OpenSearch k-NN, pgvector) for Phase 3 RAG pipelines.

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive learning plan covering CI/CD, IaC, monitoring — all critical gaps for 3 of 4 services.
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Critical: 3 of 4 services have zero tests.
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
  - Directly applicable for unishop-monolith's Java/Spring Boot observability.
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
  - Applicable for local-monolith's EKS deployment with GitOps CI/CD.
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Essential for building RAG pipelines across all 4 services in Phase 3.
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core learning for understanding agentic patterns before building agents across the portfolio.
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced: covers observable agent patterns critical for production agent deployments.

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| Aurora MySQL 5.7 EOL (unishop-monolith) — no security patches, compatibility issues | High | High | Critical | Upgrade Aurora MySQL 5.7 → 3.x in Phase 1; plan migration with DMS (partially configured) | Phase 1 |
| Node.js 14.x EOL (aws-microservices) — no security patches, runtime deprecation | High | High | Critical | Upgrade to Node.js 20.x in Phase 1; remove aws-sdk external modules config | Phase 1 |
| Hardcoded credentials (unishop-monolith, local-monolith) — secrets in source code | High | High | Critical | Migrate to AWS Secrets Manager in Phase 0; remove defaults from CloudFormation parameters | Phase 0 |
| Zero API authentication (aws-microservices) — all endpoints publicly accessible | High | High | Critical | Add Cognito authorizer to all API Gateway methods in Phase 0 | Phase 0 |
| Circular dependency (aws-microservices ↔ books-api) — prevents independent deployment | High | Medium | High | Replace sync REST call with EventBridge async pattern in Phase 0 | Phase 0 |
| No CI/CD for 3 services — manual deployments, no automated testing | Medium | High | High | Create CI/CD pipeline templates in Phase 0; deploy per-service pipelines in Phase 1 | Phase 0-1 |
| Stack traces in error responses (aws-microservices) — information leakage | High | Medium | High | Remove `errorStack: e.stack` from all three Lambda handlers | Phase 0 |
| No rollback capability for 3 services — bad deployments affect all traffic immediately | Medium | High | High | Implement canary/progressive deployments in Phase 1-2 | Phase 1-2 |

### Organizational Risks

| Risk | Likelihood | Impact | Priority | Mitigation |
|------|------------|--------|----------|------------|
| Skill gaps in containers/EKS — no EKS experience for local-monolith migration | Medium | Medium | Medium | Training (Module 3), consider external support for initial EKS setup |
| Language diversity (PHP, Java, TypeScript, JavaScript) — increases maintenance burden | Medium | Medium | Medium | Standardize new services on TypeScript; keep existing languages during transition |
| Training lag — teams not ready for Phase 1 activities | Medium | Medium | Medium | Start training in Phase 0; leverage books-api team as internal champions |
| Scope creep during monolith decomposition — extraction takes longer than planned | Medium | Medium | Medium | Use Parallel Track (Option B) approach; containerize first, extract incrementally |

### Dependency Risks

- **Circular Dependency (aws-microservices ↔ books-api)**: Must be resolved in Phase 0 before any independent modernization of these services. If resolution is delayed, both services are blocked from Phase 1 activities.
- **Shared Cognito Dependency**: All services will depend on the shared Cognito User Pool deployed in Phase 0. If Cognito deployment is delayed, authentication work in Phase 1 is blocked.
- **Phase 0 Completion Gate**: Phase 1 cannot begin until Phase 0 shared infrastructure is operational. Delays in CI/CD templates, observability stack, or Cognito will cascade to all subsequent phases.

### Single Points of Failure

- **unishop-monolith**: Single EC2 instance with no auto-scaling (INF-Q10: 1/4) and no Multi-AZ database (Aurora `MultiAZ: false`). Instance failure = total service outage. Mitigated in Phase 1 by moving to ECS Fargate with auto-scaling.
- **local-monolith**: Single App Runner service with limited auto-scaling (1-3 instances). Single RDS instance with no Multi-AZ. Mitigated in Phase 1 by EKS deployment with HPA.
- **aws-microservices SQS OrderQueue**: No DLQ configured — failed checkout messages are lost after visibility timeout expires. Mitigated in Phase 1 by adding DLQ.

## Service-by-Service Summary

### unishop-monolith

- **Overall Score**: 1.4 / 4.0 ❌
- **Repository**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
- **Assessment Date**: 2026-03-06
- **Category Scores**:
  - Infrastructure: 1.4 / 4.0
  - Application: 1.5 / 4.0
  - Data: 2.0 / 4.0
  - Security: 1.2 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. Hardcoded credentials — migrate to Secrets Manager
  2. No CI/CD — create pipeline with GitHub Actions
  3. 100% synchronous architecture — introduce EventBridge and SQS
  4. No API Gateway or authentication — deploy API Gateway with Cognito
  5. Zero observability — add X-Ray tracing and structured logging
- **Dependencies**: None (isolated)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps, Move to AI
- **Modernization Phase**: Phase 1
- **Estimated Effort**: High

### local-monolith

- **Overall Score**: 1.5 / 4.0 🟠
- **Repository**: ./monolith
- **Assessment Date**: 2026-03-06
- **Category Scores**:
  - Infrastructure: 2.1 / 4.0
  - Application: 1.2 / 4.0
  - Data: 1.7 / 4.0
  - Security: 1.4 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. Tightly-coupled monolith — conduct EventStorming, begin Strangler Fig extraction
  2. No CI/CD — create CodePipeline for Docker build → ECR → EKS
  3. Zero observability — add structured logging, tracing, monitoring
  4. No async messaging — introduce SQS for order fulfillment
  5. No API documentation — generate OpenAPI 3.0 specs
- **Dependencies**: None (isolated)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps, Move to AI
- **Modernization Phase**: Phase 1
- **Estimated Effort**: High

### aws-microservices

- **Overall Score**: 1.8 / 4.0 🟠
- **Repository**: ./services/aws-microservices
- **Assessment Date**: 2026-03-06
- **Category Scores**:
  - Infrastructure: 2.6 / 4.0
  - Application: 1.8 / 4.0
  - Data: 2.0 / 4.0
  - Security: 1.4 / 4.0
  - Operations: 1.1 / 4.0
- **Top Priorities**:
  1. No CI/CD — create pipeline with GitHub Actions or CodePipeline
  2. No API authentication — add Cognito authorizer to all endpoints
  3. No distributed tracing — enable X-Ray on all Lambda functions
  4. No resilience patterns — add retry, circuit breaker, idempotency
  5. Node.js 14.x EOL — upgrade to Node.js 20.x
- **Dependencies**: books-api (SYNC — REST calls)
- **Depended On By**: books-api (ASYNC — EventBridge events)
- **Modernization Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps, Move to AI
- **Modernization Phase**: Phase 1
- **Estimated Effort**: Medium

### books-api

- **Overall Score**: 2.2 / 4.0 🟠
- **Repository**: ./services/books-api
- **Assessment Date**: 2026-03-06
- **Category Scores**:
  - Infrastructure: 2.7 / 4.0
  - Application: 2.1 / 4.0
  - Data: 2.0 / 4.0
  - Security: 2.1 / 4.0
  - Operations: 1.9 / 4.0
- **Top Priorities**:
  1. No AI/agent framework — add Bedrock SDK and agent integration
  2. No API documentation — generate OpenAPI 3.0 spec
  3. No async messaging — add EventBridge for domain events
  4. No structured logging — add Lambda Powertools Logger
  5. No rate limiting — add API Gateway throttling and usage plans
- **Dependencies**: aws-microservices (ASYNC — EventBridge events)
- **Depended On By**: aws-microservices (SYNC — REST calls)
- **Modernization Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Managed Analytics, Move to AI
- **Modernization Phase**: Phase 2
- **Estimated Effort**: Medium

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------------|---------------|-------------|
| local-monolith | ./monolith | 2026-03-06 | 1.5 / 4.0 | ./monolith/agentic-readiness-assessment/monolith-agentic-readiness-report.md |
| unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy | 2026-03-06 | 1.4 / 4.0 | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-assessment/unishop-monolith-agentic-readiness-report.md |
| books-api | ./services/books-api | 2026-03-06 | 2.2 / 4.0 | ./services/books-api/agentic-readiness-assessment/books-api-agentic-readiness-report.md |
| aws-microservices | ./services/aws-microservices | 2026-03-06 | 1.8 / 4.0 | ./services/aws-microservices/agentic-readiness-assessment/aws-microservices-agentic-readiness-report.md |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)
- Portfolio scores: Arithmetic means of individual service scores

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - Remove hardcoded credentials from unishop-monolith and local-monolith source code; migrate to AWS Secrets Manager
   - Remove `errorStack: e.stack` from aws-microservices Lambda error responses to stop information leakage
   - Add API Gateway Cognito authorizer to aws-microservices endpoints (currently zero authentication)
   - Begin OpenAPI 3.0 specification generation for all 4 services

2. **Short-term (Month 1)**:
   - Deploy shared Cognito User Pool for portfolio-wide authentication
   - Create CI/CD pipeline templates; deploy pipelines for aws-microservices and unishop-monolith
   - Break the circular dependency between aws-microservices and books-api (replace sync REST with EventBridge)
   - Add structured logging to all 4 services (Lambda Powertools for serverless, Monolog/Logback for monoliths)
   - Begin training program: Module 3 (Containers), Module 6 (Modern DevOps)

3. **Medium-term (Months 1-3)**:
   - Containerize unishop-monolith on ECS Fargate; deploy local-monolith to EKS
   - Upgrade Node.js 14.x → 20.x in aws-microservices; upgrade Java 8 → 17+ in unishop-monolith
   - Upgrade Aurora MySQL 5.7 → 3.x; eliminate self-managed MySQL on EC2
   - Enable X-Ray distributed tracing across all services
   - Begin Strangler Fig extraction of first microservices from both monoliths

4. **Long-term (Months 3-9)**:
   - Modernize books-api with EventBridge, rate limiting, and API versioning (Phase 2)
   - Continue monolith decomposition using Strangler Fig pattern
   - Deploy vector databases and build RAG pipelines for product catalogs (Phase 3)
   - Integrate Amazon Bedrock agents with OpenAPI-defined tool interfaces (Phase 3)
   - Implement agent evaluation frameworks, LLM cost tracking, and unified observability (Phase 3)
   - Establish agent-specific SLOs: task success rate, hallucination rate, tool error rate
