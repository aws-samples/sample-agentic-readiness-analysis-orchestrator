# Portfolio Agentic Readiness Assessment Report
**Portfolio**: agentic-readiness-assessment
**Services Assessed**: 5
**Assessment Date**: 2026-03-05
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
6. Integration Opportunities
7. Resource Allocation Recommendations
8. Risk Analysis
9. Service-by-Service Summary
10. Appendix: Assessment Inventory

---

## Executive Dashboard

This portfolio of 5 services is **not ready for agentic workloads**. The portfolio-wide readiness score of **1.60 / 4.0** places it firmly in the "Needs Work" tier, with no services achieving even "Partial" readiness (2.5+). The weakest dimension is Operations & Observability (1.22/4.0) — every service lacks structured logging, SLO definitions, and anomaly detection, making agent behavior invisible and uncontrollable. Identity, Security & Governance (1.40/4.0) is the second weakest — 4 of 5 services have no or disabled API authentication, creating critical attack surfaces that agent automation would amplify at machine speed.

The most critical cross-cutting gaps are: (1) no API documentation (OpenAPI specs) on any service — agents cannot discover or invoke tools; (2) no CI/CD pipelines on 4/5 services — blocking safe, automated deployment; (3) no Infrastructure as Code on 4/5 services — preventing reproducible environments; and (4) no observability stack on any service — making agent debugging impossible. The brightest spot is **books-api** (score 2.0), which has full CI/CD, IaC, Cognito authentication, and serverless architecture — it should serve as the reference implementation for the portfolio.

The recommended modernization timeline is **9 months** across 4 phases, beginning with shared platform capabilities (authentication, observability, CI/CD templates) in Phase 0, followed by core service hardening (books-api, aws-microservices) in Phase 1, dependent service buildout (payment-service, notification-service) in Phase 2, and legacy modernization plus advanced agent capabilities (MonoToMicroLegacy, vector databases, RAG) in Phase 3. Estimated total effort is **30 person-months** with 3-4 teams working in parallel.

### Portfolio Readiness Score: 1.60 / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | 1.78 / 4.0 | ✅ 0 services, 🟡 2 services, 🟠 1 services, ❌ 2 services | 🟠 |
| Application Architecture | 1.64 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 4 services, ❌ 1 services | 🟠 |
| Data Foundations | 1.90 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 5 services, ❌ 0 services | 🟠 |
| Identity, Security & Governance | 1.40 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 2 services, ❌ 3 services | ❌ |
| Operations & Observability | 1.22 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 services, ❌ 4 services | ❌ |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): 0 services (0%)
- 🟡 Partial (2.5-3.4): 0 services (0%)
- 🟠 Needs Work (1.5-2.4): 3 services (60%) — books-api (2.0), aws-microservices (1.8), payment-service (1.6)
- ❌ Not Ready (< 1.5): 2 services (40%) — notification-service (1.3), MonoToMicroLegacy (1.30)

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | 5 | Mix of serverless (4) and monolith (1) architectures |
| Average Readiness Score | 1.60 / 4.0 | All services below "Partial" readiness threshold |
| Services Ready for Agents | 0 (0%) | No service is ready — foundational work required |
| Critical Dependencies | 4 | notification-service depends on 3 event sources; Basket→Ordering async flow |
| Shared Infrastructure Gaps | 10+ | Auth, observability, CI/CD, IaC, API docs all missing portfolio-wide |
| Estimated Modernization Effort | 30 person-months | Across 4 phases with parallel tracks |
| Expected Timeline | 9 months | With 3-4 teams working concurrently |

---

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- TypeScript: 2 services (40%) — books-api, aws-microservices (CDK/infra)
- JavaScript: 2 services (40%) — aws-microservices (Lambda handlers), payment-service (Node.js)
- Python: 1 service (20%) — notification-service
- Java: 1 service (20%) — MonoToMicroLegacy (Java 8 — EOL)

**Database Engines:**
- DynamoDB (managed): 3 services (60%) — books-api, aws-microservices (3 tables), notification-service (planned)
- RDS PostgreSQL (managed): 1 service (20%) — payment-service (single instance, no read replicas)
- MySQL (self-managed on EC2): 1 service (20%) — MonoToMicroLegacy (no confirmed RDS, hardcoded credentials)

**Compute Patterns:**
- Serverless (Lambda): 4 services (80%) — books-api (Node.js 22.x), notification-service (Python 3.11 planned), payment-service (Node.js 18.x), aws-microservices (Node.js 14.x — EOL)
- EC2 (monolith): 1 service (20%) — MonoToMicroLegacy (Spring Boot JAR on EC2)

**Deployment Maturity:**
- Full CI/CD: 1 service (20%) — books-api (CodePipeline with 4 stages, manual approval gate, canary deployments)
- Partial CI/CD: 0 services (0%)
- Manual deployment: 4 services (80%) — notification-service, payment-service, aws-microservices, MonoToMicroLegacy

### Common Strengths

1. **Serverless-first compute (4/5 services)**: 80% of services target AWS Lambda, providing auto-scaling, zero server management, and pay-per-use economics. This is the ideal compute foundation for agentic workloads that have bursty, unpredictable traffic patterns.
2. **No stored procedures or database-layer logic (5/5 services)**: All business logic resides in the application layer across every service. This portability means agent tools can interact with well-defined application APIs rather than opaque database procedures.
3. **Low data source sprawl (4/5 services)**: Most services use 1-2 data sources with clean boundaries. books-api uses a single DynamoDB table; aws-microservices uses 3 DynamoDB tables per bounded context.
4. **Managed databases for serverless services (3/5 services)**: DynamoDB usage eliminates database administration overhead and provides automatic scaling, backup, and encryption.
5. **Event-driven patterns emerging (1/5 implemented, 2/5 planned)**: aws-microservices has working EventBridge + SQS integration for the checkout flow. notification-service is designed around EventBridge consumption. This event backbone can be extended portfolio-wide.

### Common Gaps

1. **No API documentation on any service (5/5 services, APP-Q2 = 1/4)**: Zero OpenAPI/Swagger specifications exist across the entire portfolio. Agents cannot discover or invoke any service as a tool without machine-readable API documentation. This is the single most impactful cross-cutting gap.
2. **No CI/CD on 4/5 services (INF-Q6 = 1/4)**: Only books-api has automated deployment. All other services require manual deployment, blocking safe iteration on agent capabilities.
3. **No IaC on 4/5 services (INF-Q5 = 1/4)**: Only books-api (SAM+CDK) and aws-microservices (CDK) have Infrastructure as Code. notification-service, payment-service, and MonoToMicroLegacy have zero IaC.
4. **No observability on any service (OPS average = 1.22/4.0)**: No service has structured logging, SLO definitions, or anomaly detection. Only books-api has partial X-Ray tracing. Agent behavior across this portfolio is completely invisible.
5. **No or disabled authentication on 4/5 services (SEC-Q9)**: aws-microservices has zero auth on all endpoints; MonoToMicroLegacy has `permitAll()` overriding Spring Security; notification-service and payment-service have no auth. Only books-api has Cognito.
6. **No workflow orchestration on any service (5/5, INF-Q3 = 1/4)**: No Step Functions, Temporal, or workflow engine exists. Agentic systems require multi-step orchestration for tool chains, approval flows, and complex reasoning sequences.
7. **No AI/agent framework integration (5/5, APP-Q13 = 1/4)**: Zero agent framework dependencies across the portfolio. No Bedrock, Strands Agents, LangChain, or MCP integration exists.

---

## Service Dependency Map

### High-Level Architecture

The portfolio comprises an emerging e-commerce platform (aws-microservices, payment-service, notification-service, MonoToMicroLegacy) and a standalone content management service (books-api). The e-commerce platform has a nascent event-driven architecture centered on aws-microservices' EventBridge event bus, with the checkout flow triggering asynchronous order processing via SQS. The notification-service is designed to consume events from ordering, payment, and user account domains but is not yet implemented. MonoToMicroLegacy is a Java monolith serving the "Unicorn Shop" product catalog and user management with internal cross-domain data coupling. The books-api operates independently with no cross-service dependencies.

### Service Dependency Matrix

| Service | Depends On | Depended On By | Fan-In | Fan-Out | Coupling Score | Priority |
|---------|------------|----------------|--------|---------|----------------|----------|
| books-api | None | None | 0 | 0 | Isolated | P1 |
| aws-microservices | None (self-contained) | notification-service (order events), payment-service (order context) | 2 | 0 | Medium | P0 |
| payment-service | Stripe (external), aws-microservices (order context) | notification-service (payment events) | 1 | 2 | Medium | P1 |
| notification-service | aws-microservices (order events), payment-service (payment events), MonoToMicroLegacy (user events) | None | 0 | 3 | Low | P1 |
| MonoToMicroLegacy | None (self-contained) | notification-service (user events) | 1 | 0 | Low | P2 |

**Coupling Score Definitions:**
- **High**: Synchronous dependencies + shared databases, or 3+ dependency types
- **Medium**: Synchronous dependency or 2 dependency types
- **Low**: Asynchronous only or shared infrastructure only
- **Isolated**: No dependencies or dependents

**Priority Definitions:**
- **P0**: Critical path services that block others — must be modernized first
- **P1**: Important services with moderate dependencies — modernize after P0
- **P2**: Leaf services or services requiring extensive foundational work

### Critical Path Analysis

The critical path for portfolio modernization runs through the e-commerce event backbone:

1. **Foundation Services** (must be modernized first):
   - **aws-microservices** (P0): Publishes order events (order.created, order.shipped) that notification-service consumes. Its EventBridge integration is the backbone of the e-commerce event architecture. Has CDK IaC but needs auth, observability, CI/CD, and API docs.
   - **books-api** (P0): Highest-scoring service (2.0/4.0) with full CI/CD and IaC. Serves as the reference implementation for other services. Can be modernized in parallel with aws-microservices.

2. **Dependent Services** (can be modernized after foundation):
   - **payment-service** (P1): Depends on shared Cognito (Phase 0) and order context from aws-microservices. Publishes payment events consumed by notification-service.
   - **notification-service** (P1): Depends on events from aws-microservices (order events), payment-service (payment events), and MonoToMicroLegacy (user events). Must be built after event producers are modernized.

3. **Independent Services** (can be parallelized):
   - **MonoToMicroLegacy** (P2): No services depend on it except notification-service for user events (which can be deferred). Requires extensive foundational work (containerization, Java upgrade, IaC) that can proceed in parallel with Phase 2 services.

### Integration Points

**Synchronous Integrations:**
- payment-service → Stripe API: REST API for payment processing, refunds, and payment method management
- MonoToMicroLegacy → MySQL: Direct JDBC connection with hardcoded credentials for product catalog, basket, and user operations

**Asynchronous Integrations:**
- aws-microservices (Basket) → aws-microservices (Ordering): EventBridge event bus + SQS queue for checkout flow (`checkoutBasket` event)
- notification-service ← aws-microservices: Planned EventBridge consumption of order.created, order.shipped events
- notification-service ← payment-service: Planned EventBridge consumption of payment.succeeded, payment.failed events

**Shared Infrastructure:**
- **Cognito User Pool**: books-api has its own Cognito. Recommend centralizing into a shared Cognito for the e-commerce platform (aws-microservices, payment-service, notification-service, MonoToMicroLegacy)
- **EventBridge Event Bus**: aws-microservices has an event bus. Recommend extending as the portfolio-wide event backbone
- **No shared databases**: Each service has independent data stores — a strength for microservice isolation

---

## Cross-Cutting Concerns

### Infrastructure & Platform

**Portfolio Score: 1.78 / 4.0**

The infrastructure landscape is bifurcated: books-api has excellent IaC and CI/CD (scoring 4/4 on both), while 4 other services have minimal to no infrastructure automation. The portfolio benefits from 80% serverless compute adoption, but critical gaps in IaC, CI/CD, workflow orchestration, and async messaging affect the majority of services.

**Common Patterns:**
- Serverless compute (Lambda): present in 4 services — strong foundation for agent workloads
- DynamoDB as primary data store: present in 3 services — provides managed, auto-scaling NoSQL

**Critical Gaps:**
1. **No IaC (INF-Q5)**: affects 3 services (notification-service, payment-service, MonoToMicroLegacy — all score 1/4)
   - Impact: Infrastructure cannot be versioned, audited, or reproduced. Blocks CI/CD, security hardening, and auto-scaling configuration.
   - Recommendation: Create IaC templates per service — SAM for serverless services, CDK/Terraform for MonoToMicroLegacy. Use books-api's SAM template and aws-microservices' CDK stack as reference patterns.

2. **No CI/CD (INF-Q6)**: affects 4 services (all except books-api — all score 1/4)
   - Impact: Manual deployments block safe agent iteration. Cannot automate testing, security scanning, or progressive rollouts.
   - Recommendation: Create CI/CD pipeline templates based on books-api's CodePipeline pattern. Standardize on GitHub Actions or CodePipeline across the portfolio.

3. **No workflow orchestration (INF-Q3)**: affects 5 services (all score 1/4)
   - Impact: No multi-step orchestration for agent tool chains, approval flows, or complex reasoning sequences.
   - Recommendation: Introduce Step Functions for services requiring multi-step agent workflows. Start with aws-microservices checkout flow and payment-service refund approval.

4. **No async messaging on 3 services (INF-Q4)**: books-api (1/4), payment-service (1/4), MonoToMicroLegacy (1/4)
   - Impact: Synchronous-only architectures cannot support fire-and-forget agent patterns or event-driven workflows.
   - Recommendation: Extend EventBridge to books-api and payment-service. Add SQS for MonoToMicroLegacy basket operations during decomposition.

### Application Architecture

**Portfolio Score: 1.64 / 4.0**

Application architecture is the most consistently weak category across services. Every service lacks API documentation, AI/agent frameworks, and API versioning. Resilience patterns are absent in 4/5 services.

**Critical Gaps:**
1. **No API documentation (APP-Q2)**: affects 5 services (all score 1/4)
   - Impact: Agents cannot discover or invoke any service. This is the #1 blocker for agentic readiness.
   - Recommendation: Generate OpenAPI 3.0 specs for all services. For books-api, generate from SAM template. For aws-microservices, export from API Gateway. For others, create from README endpoint documentation.

2. **No AI/agent frameworks (APP-Q13)**: affects 5 services (all score 1/4)
   - Impact: No service has any AI integration capability.
   - Recommendation: Phase 3 activity. Add Strands Agents SDK (TypeScript for Node.js services, Python for notification-service) or Amazon Bedrock integration.

3. **No API versioning (APP-Q11)**: affects 4 services (all except MonoToMicroLegacy which scores 1/4 too)
   - Impact: Breaking API changes will disrupt agent tool contracts with no backward compatibility.
   - Recommendation: Add `/v1/` prefix to all API routes across the portfolio. Document versioning strategy.

4. **No resilience patterns (APP-Q9)**: affects 4 services with scores 1-2/4
   - Impact: Agent retries can create duplicate records, cascading failures, or silent data corruption.
   - Recommendation: Implement idempotency (Lambda Powertools) on all write endpoints. Add circuit breakers for external service calls (Stripe, SES/SNS).

### Data Foundations

**Portfolio Score: 1.90 / 4.0**

Data Foundations is the strongest category across the portfolio, benefiting from clean database choices (DynamoDB, PostgreSQL), no stored procedures, and low data source sprawl. However, no service has vector database, RAG pipeline, or embedding capabilities — all prerequisites for agentic AI.

**Critical Gaps:**
1. **No vector database (DATA-Q1)**: affects 5 services (all score 1/4)
   - Impact: No semantic search capability for any service. Agents cannot perform RAG or knowledge retrieval.
   - Recommendation: Deploy Amazon Bedrock Knowledge Bases or OpenSearch Serverless as a shared portfolio capability.

2. **No RAG implementation (DATA-Q3)**: affects 5 services (all score 1/4)
   - Impact: Agent responses cannot be grounded in domain-specific data.
   - Recommendation: Phase 3 activity. Build RAG pipelines per domain — books catalog, product catalog, payment policies, notification templates.

3. **No schema documentation (DATA-Q7)**: affects 4 services with scores 1-2/4
   - Impact: Agents need schema definitions to construct valid API requests and interpret responses.
   - Recommendation: Create JSON Schema definitions for all data models. Embed in OpenAPI specs.

### Identity, Security & Governance

**Portfolio Score: 1.40 / 4.0**

Security is a critical concern. 4/5 services have weak or no authentication, secret management is poor (MonoToMicroLegacy has hardcoded credentials), and no service has PII redaction, audit logging, or human approval workflows for agent operations.

**Critical Gaps:**
1. **No/disabled authentication (SEC-Q9)**: affects 4 services
   - Impact: Any internet user (or agent) can access all endpoints without identity. Agent actions are unattributable and uncontrollable.
   - Recommendation: Deploy shared Cognito User Pool in Phase 0. Attach authorizers to all API Gateways. Enable `@PreAuthorize` on MonoToMicroLegacy endpoints.

2. **No secret management (SEC-Q1)**: affects 4 services with scores 1-2/4
   - Impact: MonoToMicroLegacy has hardcoded database credentials in source code. Agent workloads need scoped, rotatable credentials.
   - Recommendation: Migrate all secrets to AWS Secrets Manager. Reference via IaC dynamic references.

3. **No audit logging (SEC-Q4)**: affects 4 services with scores 1-2/4
   - Impact: Agent actions are not captured in immutable audit trails. Cannot demonstrate compliance or investigate incidents.
   - Recommendation: Enable CloudTrail across all accounts. Configure log file validation and S3 object lock.

4. **No human approval workflows (SEC-Q7)**: affects 5 services (all score 1/4)
   - Impact: High-risk agent operations (bulk deletions, refunds, mass notifications) have no approval gates.
   - Recommendation: Implement Step Functions with `waitForTaskToken` for high-risk operations in Phase 3.

### Operations & Observability

**Portfolio Score: 1.22 / 4.0**

Operations & Observability is the weakest category by a significant margin. Every service scores ❌ status. No service has SLO definitions, anomaly detection, structured logging (except partial in notification-service's planned Powertools), or operational dashboards.

**Critical Gaps:**
1. **No structured logging (OPS-Q2)**: affects 5 services (4 score 1/4, 1 scores 2/4)
   - Impact: Agent debugging impossible. Cannot correlate requests across services. No JSON-formatted logs for automated analysis.
   - Recommendation: Standardize on AWS Lambda Powertools Logger across all services (TypeScript, Python, and Java variants). Implement correlation ID propagation.

2. **No SLO definitions (OPS-Q4)**: affects 5 services (all score 1/4)
   - Impact: No quality targets for agent interactions. Cannot measure or alert on service degradation.
   - Recommendation: Define SLOs for availability (99.9%), p99 latency (<500ms for reads, <1s for writes), and error rate (<0.1%) per service.

3. **No anomaly detection (OPS-Q8)**: affects 5 services (all score 1/4)
   - Impact: Abnormal agent behavior (runaway retries, cost spikes, unusual access patterns) goes undetected.
   - Recommendation: Enable CloudWatch Anomaly Detection on key metrics. Create composite alarms for agent-specific patterns.

4. **No distributed tracing (OPS-Q1)**: affects 4 services with scores 1-2/4
   - Impact: Cannot trace agent requests across service boundaries. Cross-service debugging is impossible.
   - Recommendation: Enable X-Ray tracing on all Lambda functions and API Gateways. Instrument SDK clients for downstream call visibility.

---

## Portfolio Modernization Roadmap

The roadmap accounts for cross-service dependencies, shared infrastructure needs, and organizational capacity. Work is sequenced to minimize risk and maximize value delivery, with independent services parallelized where possible.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services (aws-microservices, books-api) before downstream dependents (notification-service, payment-service)
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius — secure and observe before adding agent automation
4. **Parallel Tracks**: Independent services (books-api, MonoToMicroLegacy) can be modernized concurrently
5. **Quick Wins**: Early wins (OpenAPI specs, structured logging) build momentum and demonstrate value

### Phase 0 — Foundation (Months 0-1)

**Objective**: Establish shared capabilities and organizational readiness

**Shared Infrastructure:**
- **Centralized Cognito User Pool**: Deploy a shared Cognito User Pool for the e-commerce platform. Configure user groups, app clients, and OAuth2 scopes. Benefits 4 services (aws-microservices, payment-service, notification-service, MonoToMicroLegacy).
- **Portfolio EventBridge Event Bus**: Extend the existing aws-microservices EventBridge bus as the portfolio-wide event backbone. Define event schemas for order, payment, notification, and user domains. Benefits 4 services.
- **Shared Observability Templates**: Create reusable IaC modules for CloudWatch dashboards, alarm templates, and log group configurations. Define standard SLO framework. Benefits 5 services.
- **CloudTrail and Audit Logging**: Enable CloudTrail with log file validation across all accounts. Configure S3 bucket with object lock for immutable audit storage. Benefits 5 services.

**Platform Capabilities:**
- **CI/CD Pipeline Templates**: Create standardized GitHub Actions or CodePipeline templates for Node.js/TypeScript, Python, and Java services based on books-api's pattern. Enables service-level CI/CD work in Phase 1.
- **API Documentation Standards**: Establish OpenAPI 3.0 specification standards, validation tooling, and publishing pipeline. Create templates for common patterns (CRUD, event-driven, async).
- **IaC Module Library**: Create reusable SAM/CDK modules for Lambda functions, API Gateway with auth, DynamoDB tables, SQS queues, and EventBridge rules.

**Organizational Enablers:**
- Training: IaC (CDK/SAM), containers (Docker/ECS), serverless observability (Lambda Powertools), OpenAPI specifications
- Tooling: Standardize on CDK for new services, SAM for simple Lambda services
- Standards: API naming conventions, event schema standards, logging format standards, security baseline

**Expected Outcomes:**
- Shared authentication available for all services to integrate
- CI/CD templates ready for service teams to adopt
- Observability standards defined and reusable modules available
- Training completed for Phase 1 skill requirements

**Estimated Effort**: 6 person-months

### Phase 1 — Core Services (Months 1-3)

**Objective**: Modernize foundational services that others depend on, establishing reference patterns

**Services in Scope:**
1. **books-api** (P0, Score: 2.0/4.0)
   - Current State: Best-in-portfolio with full CI/CD, IaC, Cognito auth, serverless architecture. Missing API docs, structured logging, resilience patterns, and async messaging.
   - Target State: Reference implementation with OpenAPI spec, structured logging, idempotency, EventBridge integration, and hardened security.
   - Key Activities:
     - Generate OpenAPI 3.0 spec from SAM template routes
     - Add Lambda Powertools for TypeScript (structured logging, correlation IDs)
     - Implement idempotency on CreateBook endpoint
     - Add EventBridge integration for BookCreated events
     - Configure API Gateway throttling and usage plans
     - Tighten CI/CD pipeline IAM (remove IAMFullAccess)
     - Add API versioning (/v1/books)
   - Dependencies: Shared Cognito (Phase 0) — already has its own, can integrate with shared pool
   - Blocks: None directly, but serves as reference implementation for all other services
   - Estimated Effort: 3 person-weeks

2. **aws-microservices** (P0, Score: 1.8/4.0)
   - Current State: True microservices architecture with CDK IaC, EventBridge/SQS integration, 3 DynamoDB tables. Missing auth (all endpoints public), CI/CD, observability, API docs, and runs EOL Node.js 14.
   - Target State: Secured, observable, documented e-commerce backbone with CI/CD and current runtime.
   - Key Activities:
     - Upgrade Lambda runtime from Node.js 14.x to Node.js 20.x
     - Add Cognito authorizer to all 3 API Gateways
     - Add API Gateway throttling and usage plans
     - Create CI/CD pipeline (GitHub Actions with cdk synth/deploy)
     - Enable X-Ray tracing on all Lambda functions
     - Implement structured logging (Lambda Powertools)
     - Generate OpenAPI specs for Product, Basket, and Order APIs
     - Remove stack traces from error responses
     - Implement idempotency on checkout flow
     - Add CloudWatch alarms and SLO definitions
   - Dependencies: Shared Cognito (Phase 0)
   - Blocks: notification-service (order events), payment-service (order context)
   - Estimated Effort: 6 person-weeks

**Cross-Service Activities:**
- Standardize structured logging format across books-api and aws-microservices
- Validate shared Cognito integration pattern for reuse in Phase 2
- Document reference architecture patterns for Phase 2 teams

**Expected Outcomes:**
- 2 services with full observability, CI/CD, auth, and API documentation
- Reference implementation patterns validated and documented
- EventBridge event backbone ready for Phase 2 consumers
- EOL runtime risk eliminated (Node.js 14 → 20)

**Estimated Effort**: 5 person-months

### Phase 2 — Dependent Services (Months 3-6)

**Objective**: Build and modernize services that depend on Phase 1 services

**Services in Scope:**
1. **payment-service** (P1, Score: 1.6/4.0)
   - Current State: Only package.json and README exist. No source code, no IaC, no CI/CD. Describes Lambda + RDS PostgreSQL + Stripe integration.
   - Target State: Fully implemented serverless payment service with IaC, CI/CD, async processing, security controls, and observability.
   - Key Activities:
     - Create serverless.yml IaC definition (Lambda, API Gateway, RDS, SQS)
     - Implement source code following README architecture
     - Generate OpenAPI 3.0 spec for all 6 endpoints
     - Set up CI/CD pipeline from Phase 0 templates
     - Integrate shared Cognito for authentication
     - Implement async payment processing with SQS
     - Add distributed tracing (X-Ray) and structured logging
     - Configure VPC and network security for RDS
     - Implement RDS Multi-AZ and read replicas
     - Add Secrets Manager for Stripe keys and database credentials
     - Define SLOs and CloudWatch alarms
   - Dependencies: Shared Cognito (Phase 0), aws-microservices order context (Phase 1)
   - Blocks: notification-service (payment events)
   - Estimated Effort: 8 person-weeks

2. **notification-service** (P1, Score: 1.3/4.0)
   - Current State: Only README and requirements.txt exist. No source code, no IaC, no CI/CD. Describes well-designed EventBridge → SQS → Lambda → SES/SNS architecture.
   - Target State: Fully implemented event-driven notification service consuming events from aws-microservices and payment-service.
   - Key Activities:
     - Create SAM template.yaml (Lambda, DynamoDB, SQS, EventBridge rules, S3)
     - Implement Python Lambda handler with Lambda Powertools
     - Create OpenAPI spec for 5 notification endpoints
     - Set up CI/CD pipeline from Phase 0 templates
     - Integrate shared Cognito for API authentication
     - Connect to portfolio EventBridge for event consumption
     - Implement security controls (Secrets Manager, PII redaction, IAM least-privilege)
     - Enable observability (structured logging, X-Ray, CloudWatch alarms)
     - Add integration tests for notification processing flow
   - Dependencies: Shared Cognito (Phase 0), aws-microservices order events (Phase 1), payment-service payment events (Phase 2)
   - Blocks: None
   - Estimated Effort: 8 person-weeks

**Parallel Tracks:**
- MonoToMicroLegacy containerization and IaC can begin in parallel (see Phase 3 early start)

**Expected Outcomes:**
- E-commerce event-driven architecture fully operational
- Payment processing with async patterns and security controls
- Notification delivery pipeline consuming events from ordering and payments
- 4/5 services with CI/CD, auth, observability, and API documentation

**Estimated Effort**: 9 person-months

### Phase 3 — Optimization (Months 6-9)

**Objective**: Modernize legacy monolith, implement advanced agent capabilities, and optimize cross-service workflows

**Services in Scope:**
1. **MonoToMicroLegacy** (P2, Score: 1.30/4.0)
   - Current State: Java 8 Spring Boot 2.1.6 monolith on EC2 with hardcoded credentials, no IaC/CI/CD/containers, disabled OAuth2 auth.
   - Target State: Containerized on ECS Fargate with IaC, CI/CD, authentication, observability, and initial service extraction (User service).
   - Key Activities:
     - Remove hardcoded credentials → AWS Secrets Manager
     - Create Dockerfile and validate containerized build
     - Create IaC (CDK/Terraform) for VPC, ECS Fargate, RDS MySQL, ALB
     - Set up CI/CD pipeline (build JAR, Docker image, deploy to ECS)
     - Add API Gateway with Cognito authorizer in front of ALB
     - Enable Spring Security OAuth2 authentication (replace `permitAll()`)
     - Add structured logging (SLF4J + Logback JSON encoder)
     - Generate OpenAPI spec using Springdoc OpenAPI
     - Migrate to managed RDS MySQL with Multi-AZ
     - Begin User service extraction using Strangler Fig pattern
   - Dependencies: Shared Cognito (Phase 0)
   - Blocks: None (notification-service user events can be added later)
   - Estimated Effort: 12 person-weeks

**Portfolio-Wide Advanced Capabilities:**
- Deploy shared vector database (Amazon Bedrock Knowledge Bases or OpenSearch Serverless) for semantic search across book catalog, product catalog, and notification templates
- Build RAG pipelines per domain connecting vector database to service data
- Implement agent tools layer using Strands Agents SDK, wrapping service OpenAPI specs as callable tools
- Add Step Functions workflows for human approval on high-risk operations (refunds, bulk notifications, bulk deletions)
- Implement distributed tracing for agent workflows with OpenTelemetry `gen_ai.*` semantic conventions
- Set up automated eval frameworks for agent accuracy, latency, and safety
- Implement LLM cost tracking and token usage attribution

**Expected Outcomes:**
- MonoToMicroLegacy containerized and running on ECS with modern security and observability
- All 5 services with full CI/CD, auth, observability, and API documentation
- Agent tools available for all services via OpenAPI-backed tool definitions
- RAG capabilities enabling semantic search across portfolio data
- Human approval workflows for high-risk agent operations

**Estimated Effort**: 10 person-months

### Total Portfolio Effort

**Total Estimated Effort**: 30 person-months
**Expected Timeline**: 9 months (with 3-4 teams working in parallel)
**Investment Required**: ~$600,000 (assuming $20,000 per person-month fully loaded)

---

## Integration Opportunities

### Shared Service Extraction

**Opportunity 1: Centralized Authentication Service (Cognito User Pool)**
- Current State: books-api has its own Cognito User Pool. aws-microservices has zero auth. payment-service claims Cognito but has no implementation. MonoToMicroLegacy has disabled Spring Security OAuth2. notification-service has no auth.
- Proposed Solution: Deploy a shared Cognito User Pool with user groups, app clients per service, and OAuth2 scopes. Each service integrates via API Gateway authorizer or Spring Security.
- Benefits: Consistent identity across all services, single source of user management, enables identity propagation for agent audit trails, reduces duplicated auth infrastructure
- Effort: 3 person-weeks
- Priority: **High** — prerequisite for securing all services and enabling agent identity propagation

**Opportunity 2: Shared Observability Platform**
- Current State: No service has comprehensive observability. books-api has partial X-Ray. All others have console.log or no logging. No CloudWatch dashboards, no SLO framework, no structured logging standards.
- Proposed Solution: Create reusable IaC modules for: (1) Lambda Powertools configuration per runtime (TypeScript, Python, Java); (2) CloudWatch dashboard templates per service type; (3) Standard alarm definitions (error rate, latency, 5xx); (4) Log group retention policies; (5) X-Ray tracing configuration.
- Benefits: Consistent observability across all services, faster onboarding for new services, end-to-end distributed tracing for agent workflows, unified operational dashboards
- Effort: 4 person-weeks
- Priority: **High** — required for agent debugging and operational safety

**Opportunity 3: API Documentation Pipeline**
- Current State: Zero OpenAPI specifications across the entire portfolio. Agents cannot discover or invoke any service.
- Proposed Solution: Create an API documentation pipeline that: (1) validates OpenAPI specs in CI/CD; (2) publishes specs to a central API catalog; (3) auto-generates agent tool definitions from specs; (4) provides mock servers for development.
- Benefits: Machine-readable API descriptions for agent tool discovery, standardized API documentation, reduced integration friction
- Effort: 2 person-weeks
- Priority: **High** — single most impactful gap for agentic readiness

### Event-Driven Architecture

**Opportunity 1: Unified E-Commerce Event Bus**
- Current State: aws-microservices has EventBridge with basket checkout events. payment-service is synchronous only. notification-service is designed to consume events but no producers exist.
- Proposed Solution: Extend the aws-microservices EventBridge bus as the portfolio-wide event backbone. Define standard event schemas: `order.created`, `order.shipped`, `payment.succeeded`, `payment.failed`, `user.registered`, `notification.sent`. Add event publishing to payment-service and MonoToMicroLegacy.
- Benefits: Decoupled service communication, enables notification-service without synchronous dependencies, supports agent event-driven workflows, provides event replay for debugging
- Effort: 4 person-weeks
- Priority: **High** — enables the notification-service and decouples the e-commerce platform

**Opportunity 2: Books API Event Publishing**
- Current State: books-api is synchronous only (API Gateway → Lambda → DynamoDB). No events published.
- Proposed Solution: Add EventBridge publishing for `book.created` and `book.updated` events. Enables downstream consumers (embedding pipelines, search index updates, notification triggers).
- Benefits: Enables RAG pipeline triggers, decouples book catalog from future consumers, supports event-driven agent workflows
- Effort: 1 person-week
- Priority: **Medium** — valuable for Phase 3 RAG pipeline but not blocking other services

### API Gateway Consolidation

- Current State: aws-microservices has 3 separate API Gateways (productApi, basketApi, orderApi). books-api has 1 API Gateway. MonoToMicroLegacy exposes port 8080 directly on EC2 with no API Gateway. payment-service and notification-service have no API Gateways.
- Proposed Solution: (1) Consolidate aws-microservices' 3 API Gateways into a single API Gateway with path-based routing (/products, /baskets, /orders). (2) Add API Gateway in front of MonoToMicroLegacy ALB. (3) Evaluate a shared API Gateway for the e-commerce platform with unified auth, throttling, and monitoring.
- Benefits: Consistent authentication and authorization, unified rate limiting, single point for API monitoring, reduced infrastructure cost (fewer API Gateway instances), simplified agent tool configuration
- Effort: 3 person-weeks
- Priority: **Medium** — reduces operational complexity but not blocking agent enablement

### Observability Unification

- Current State: Each service has a different (or absent) observability approach. books-api has partial X-Ray. aws-microservices uses console.log. notification-service plans Lambda Powertools. payment-service mentions X-Ray in README. MonoToMicroLegacy has no observability.
- Proposed Solution: Standardize on: (1) AWS Lambda Powertools for structured logging (TypeScript for Node.js services, Python for notification-service); (2) SLF4J + Logback JSON for MonoToMicroLegacy; (3) X-Ray for distributed tracing across all services; (4) Unified CloudWatch dashboard showing cross-service request flows; (5) Common SLO definitions and burn-rate alerting.
- Benefits: End-to-end agent request tracing, consistent log format for automated analysis, unified operational view, faster incident resolution, agent behavior monitoring
- Effort: 4 person-weeks (included in Phase 0 observability templates)
- Priority: **High** — critical for agent debugging and operational safety

---

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + dedicated service teams

With 10+ cross-cutting concerns (authentication, observability, CI/CD, IaC, API documentation, event bus, audit logging, security baseline, SLO framework, agent tooling), a centralized platform team is essential to avoid duplicated effort and ensure consistency.

**Platform Team** (4 people):
- Responsibilities: Shared Cognito, EventBridge event bus, observability templates, CI/CD pipeline templates, IaC module library, API documentation standards, security baseline, agent framework patterns
- Skills Required: CDK/Terraform, CloudFormation, API Gateway, Cognito, EventBridge, CloudWatch, X-Ray, Lambda Powertools, OpenAPI tooling
- Duration: Full 9-month engagement, shifting from infrastructure (Phase 0-1) to agent enablement (Phase 2-3)

**Service Teams** (2-3 people per team, 3 teams):
- **Team A — books-api + aws-microservices** (3 people): TypeScript/JavaScript expertise, SAM + CDK, DynamoDB, Lambda. These are the Phase 1 core services that establish reference patterns.
- **Team B — payment-service + notification-service** (3 people): Node.js + Python expertise, Serverless Framework, RDS PostgreSQL, SQS/SNS/SES. These are the Phase 2 dependent services that build on Phase 1 patterns.
- **Team C — MonoToMicroLegacy** (2-3 people): Java/Spring Boot expertise, Docker, ECS/Fargate, MySQL/RDS, Gradle. This is the Phase 3 legacy modernization requiring specialized Java knowledge.

### Skill Gaps

1. **Infrastructure as Code (CDK/SAM/Terraform)**: Required for 4/5 services to create IaC from scratch. Currently available in 2/5 services (books-api SAM, aws-microservices CDK). Gap: 3 service teams need IaC skills.
2. **Containers (Docker/ECS/Fargate)**: Required for MonoToMicroLegacy containerization. Not currently available — the only non-serverless service has no Docker expertise. Gap: Team C needs container skills.
3. **Observability (Lambda Powertools, X-Ray, OpenTelemetry)**: Required for all 5 services. Partially available in books-api (X-Ray enabled). Gap: All teams need structured logging and tracing expertise.
4. **API Documentation (OpenAPI 3.0)**: Required for all 5 services. Not available in any — no service has OpenAPI specs. Gap: All teams need OpenAPI authoring skills.
5. **Agent Frameworks (Amazon Bedrock, Strands Agents SDK)**: Required for Phase 3 across all services. Not available in any. Gap: Platform team and all service teams need AI/agent training.
6. **Python (Lambda Powertools, Pydantic)**: Required for notification-service. Currently only available via dependency listing. Gap: Team B needs Python serverless development skills.

### Training Recommendations

**Phase 0-1 Skills (Immediate — Weeks 1-4):**
- AWS CDK/SAM Workshop — 1 week, all teams
- Lambda Foundations (Skill Builder) — all service teams
- Architecting Serverless Applications (Skill Builder) — all service teams
- Amazon API Gateway for Serverless Applications (Skill Builder) — all service teams
- Getting Started with DevOps on AWS (Skill Builder) — Teams B and C
- AWS CloudFormation Getting Started (Skill Builder) — Teams B and C

**Phase 2 Skills (Month 2-3):**
- Deploying Serverless Applications (Skill Builder) — all service teams
- Amazon DynamoDB for Serverless Architecture (Skill Builder) — Teams A and B
- Move to Managed Databases learning plan (Skill Builder) — Team B (RDS) and Team C (MySQL→RDS)
- Advanced Testing Practices Using AWS DevOps Tools (Skill Builder) — all teams

**Phase 3 Skills (Month 4-6):**
- Introduction to Agentic AI on AWS (Skill Builder) — all teams
- Amazon Bedrock Getting Started (Skill Builder) — all teams
- Creating an AWS DevOps AI Agent with Strands Agents SDK (Skill Builder Lab) — platform team + team leads
- Build and Evaluate RAG Applications using Knowledge Bases for Amazon Bedrock (Skill Builder Lab) — platform team
- Vector Databases for Generative AI Applications (Skill Builder) — platform team

**Certification Paths:**
- AWS Solutions Architect Associate — recommended for all team leads (architecture decisions)
- AWS DevOps Engineer Professional — recommended for platform team members (CI/CD, IaC, observability)

### External Support

Recommended areas for AWS Professional Services or consulting partner engagement:

1. **Phase 0 Platform Setup** (2 months): Accelerate shared infrastructure (Cognito, EventBridge, observability templates) with experienced consultants. Knowledge transfer to platform team. Estimated: 2 consultants × 2 months.
2. **MonoToMicroLegacy Modernization** (2 months): Java monolith containerization and ECS deployment is specialized work. Recommend external support for Docker/ECS architecture and Strangler Fig pattern implementation. Estimated: 1-2 consultants × 2 months.
3. **Agent Framework Architecture** (1 month): Phase 3 agent enablement benefits from AWS AI/ML specialists who can guide Bedrock integration, RAG pipeline design, and agent tool architecture. Estimated: 1 consultant × 1 month.

---

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MonoToMicroLegacy Java 8 + Spring Boot 2.1.6 are EOL — security vulnerabilities unpatched | High | High | Phase 3: Containerize and upgrade Java runtime. Interim: isolate via network segmentation. Effort: 4 person-weeks. |
| aws-microservices Node.js 14.x EOL — known security vulnerabilities | High | Medium | Phase 1: Upgrade to Node.js 20.x. One-line change per function in CDK. Effort: 1 person-day. |
| No authentication on 4/5 services — all endpoints publicly accessible | High | High | Phase 0: Deploy shared Cognito. Phase 1-2: Integrate authorizers on all API Gateways. Effort: 3 person-weeks. |
| No observability on any service — agent failures invisible | High | High | Phase 0: Create observability templates. Phase 1: Implement on core services. Effort: 4 person-weeks. |
| payment-service and notification-service have no source code — architecture unverifiable | Medium | High | Phase 2: Implement from README specifications with agentic readiness built in from the start. Effort: 16 person-weeks combined. |
| No idempotency on write endpoints — agent retries create duplicates | High | Medium | Phase 1: Add Lambda Powertools idempotency on books-api and aws-microservices. Phase 2: Add to payment/notification. Effort: 2 person-weeks per service. |
| No API versioning — breaking changes disrupt agent tool contracts | Medium | Medium | Phase 1: Add /v1/ prefix to all routes. Low effort, high impact. Effort: 1 person-day per service. |
| DynamoDB scan without pagination in books-api — performance degrades with scale | Medium | Low | Phase 1: Add pagination (ExclusiveStartKey/LastEvaluatedKey). Effort: 1 person-day. |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Multi-language portfolio (TypeScript, JavaScript, Python, Java) — skill fragmentation | Medium | Medium | Standardize observability and patterns per language. Use Lambda Powertools variants. Training investment per language. |
| No CI/CD on 4/5 services — manual deployments block automation and safety | High | High | Phase 0: Create CI/CD templates. Phase 1-2: Implement per service. Effort: 2 person-weeks per service. |
| No tests on 4/5 services — cannot verify changes safely | High | Medium | Phase 1-2: Add integration test suites per service. Require tests in CI pipeline. Effort: 2 person-weeks per service. |
| Team skill gaps in IaC, containers, and observability | Medium | Medium | Phase 0: Training program. Use books-api patterns as templates. Consider external support for specialized work. |
| Coordination overhead across 4 teams over 9 months | Medium | Medium | Weekly cross-team sync. Platform team as coordination point. Shared standards reduce decision overhead. |

### Dependency Risks

- **notification-service depends on events from services that don't yet publish them**: aws-microservices has EventBridge but may not publish all required event types. payment-service is not implemented. MonoToMicroLegacy has no async messaging. Mitigation: notification-service implementation must be sequenced after its event producers (Phase 2, after Phase 1 core services).
- **payment-service references order_id without established integration**: The payment service README assumes integration with an ordering system. Mitigation: Define integration contract (event schema) in Phase 0, implement in Phase 1 (aws-microservices) before Phase 2 (payment-service).
- **MonoToMicroLegacy internal cross-domain coupling**: The `unicorns_basket` table joins Unicorn and User domains via UUIDs. Service extraction requires resolving this data coupling. Mitigation: Implement Anti-corruption Layer and Transactional Outbox pattern before extracting User service in Phase 3.

### Single Points of Failure

1. **MonoToMicroLegacy on single EC2 instance**: No high availability, no auto-scaling, no failover. If the EC2 instance fails, the entire Unicorn Shop is unavailable. The `HealthController.java` calls `EC2MetadataUtils.getInstanceInfo()`, confirming single-instance deployment. Mitigation: Phase 3 containerization with ECS Fargate provides multi-AZ deployment and auto-scaling.
2. **payment-service single RDS PostgreSQL instance**: The README describes a single-instance RDS deployment with no read replicas or Multi-AZ. For a payment service, database unavailability means payment processing stops. Mitigation: Phase 2 implement RDS Multi-AZ with automated failover and read replicas.
3. **MonoToMicroLegacy hardcoded credentials**: `application.properties` contains plaintext `MonoToMicroUser`/`MonoToMicroPassword`. If credentials are compromised, the database is fully exposed. Mitigation: Phase 3 (or earlier quick win) — move to AWS Secrets Manager immediately.

---

## Service-by-Service Summary

### books-api

- **Overall Score**: 2.0 / 4.0 🟠
- **Repository**: services/books-api
- **Assessment Date**: 2026-03-05
- **Category Scores**:
  - Infrastructure: 2.6 / 4.0 🟡
  - Application: 1.7 / 4.0 🟠
  - Data: 1.9 / 4.0 🟠
  - Security: 1.9 / 4.0 🟠
  - Operations: 1.7 / 4.0 🟠
- **Top Priorities**:
  1. Generate OpenAPI 3.0 spec for agent tool discovery (APP-Q2)
  2. Add structured logging with correlation IDs (OPS-Q2)
  3. Implement idempotency on CreateBook endpoint (APP-Q7)
  4. Add EventBridge for async event publishing (INF-Q4)
  5. Configure API Gateway throttling and usage plans (APP-Q8)
- **Dependencies**: None (standalone service)
- **Depended On By**: None directly; serves as reference implementation
- **Modernization Phase**: Phase 1 — Core Services
- **Estimated Effort**: 3 person-weeks

### aws-microservices

- **Overall Score**: 1.8 / 4.0 🟠
- **Repository**: services/aws-microservices
- **Assessment Date**: 2026-03-05
- **Category Scores**:
  - Infrastructure: 2.5 / 4.0 🟡
  - Application: 1.8 / 4.0 🟠
  - Data: 2.1 / 4.0 🟠
  - Security: 1.4 / 4.0 ❌
  - Operations: 1.0 / 4.0 ❌
- **Top Priorities**:
  1. Add API authentication — all endpoints publicly accessible (SEC-Q9)
  2. Set up CI/CD pipeline (INF-Q6)
  3. Add observability stack — tracing, structured logging, alerting (OPS-Q1/Q2/Q4)
  4. Generate OpenAPI specs for all 3 APIs (APP-Q2)
  5. Upgrade Node.js 14.x (EOL) to Node.js 20.x (INF-Q1)
- **Dependencies**: Shared Cognito (Phase 0)
- **Depended On By**: notification-service (order events), payment-service (order context)
- **Modernization Phase**: Phase 1 — Core Services
- **Estimated Effort**: 6 person-weeks

### payment-service

- **Overall Score**: 1.6 / 4.0 🟠
- **Repository**: services/payment-service
- **Assessment Date**: 2026-03-05
- **Category Scores**:
  - Infrastructure: 1.8 / 4.0 🟠
  - Application: 1.7 / 4.0 🟠
  - Data: 1.7 / 4.0 🟠
  - Security: 1.6 / 4.0 🟠
  - Operations: 1.2 / 4.0 ❌
- **Top Priorities**:
  1. Create IaC definition — no serverless.yml exists (INF-Q5)
  2. Set up CI/CD pipeline (INF-Q6)
  3. Implement async payment processing with SQS (INF-Q4, APP-Q3)
  4. Add distributed tracing and structured logging (OPS-Q1, OPS-Q2)
  5. Generate OpenAPI 3.0 spec for all 6 endpoints (APP-Q2)
- **Dependencies**: Shared Cognito (Phase 0), aws-microservices order context (Phase 1)
- **Depended On By**: notification-service (payment events)
- **Modernization Phase**: Phase 2 — Dependent Services
- **Estimated Effort**: 8 person-weeks

### notification-service

- **Overall Score**: 1.3 / 4.0 ❌
- **Repository**: services/notification-service
- **Assessment Date**: 2026-03-05
- **Category Scores**:
  - Infrastructure: 1.0 / 4.0 ❌
  - Application: 1.6 / 4.0 🟠
  - Data: 1.8 / 4.0 🟠
  - Security: 1.0 / 4.0 ❌
  - Operations: 1.2 / 4.0 ❌
- **Top Priorities**:
  1. Create IaC foundation — zero IaC files exist (INF-Q5)
  2. Implement Lambda handler source code (APP-Q2 through APP-Q13)
  3. Set up CI/CD pipeline (INF-Q6)
  4. Implement all security controls — every SEC criterion scores 1/4 (SEC-Q1 through SEC-Q10)
  5. Create OpenAPI specification for 5 API endpoints (APP-Q2)
- **Dependencies**: Shared Cognito (Phase 0), aws-microservices order events (Phase 1), payment-service payment events (Phase 2)
- **Depended On By**: None
- **Modernization Phase**: Phase 2 — Dependent Services
- **Estimated Effort**: 8 person-weeks

### MonoToMicroLegacy

- **Overall Score**: 1.30 / 4.0 ❌
- **Repository**: services/unishop-monolith-to-microservices/MonoToMicroLegacy
- **Assessment Date**: 2026-03-05
- **Category Scores**:
  - Infrastructure: 1.0 / 4.0 ❌
  - Application: 1.38 / 4.0 ❌
  - Data: 2.0 / 4.0 🟠
  - Security: 1.1 / 4.0 ❌
  - Operations: 1.0 / 4.0 ❌
- **Top Priorities**:
  1. Remove hardcoded credentials from source code (SEC-Q1)
  2. Create Dockerfile for containerization (INF-Q1)
  3. Create IaC for all infrastructure (INF-Q5)
  4. Set up CI/CD pipeline (INF-Q6)
  5. Enable authentication — currently disabled via `permitAll()` (SEC-Q9)
- **Dependencies**: Shared Cognito (Phase 0)
- **Depended On By**: notification-service (user events, can be deferred)
- **Modernization Phase**: Phase 3 — Optimization
- **Estimated Effort**: 12 person-weeks

---

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------------|---------------|-------------|
| books-api | services/books-api | 2026-03-05 | 2.0 / 4.0 | services/books-api/agentic-readiness-assessment/books-api-agentic-readiness-report.md |
| aws-microservices | services/aws-microservices | 2026-03-05 | 1.8 / 4.0 | services/aws-microservices/agentic-readiness-assessment/aws-microservices-agentic-readiness-report.md |
| payment-service | services/payment-service | 2026-03-05 | 1.6 / 4.0 | services/payment-service/agentic-readiness-assessment/payment-service-agentic-readiness-report.md |
| notification-service | services/notification-service | 2026-03-05 | 1.3 / 4.0 | services/notification-service/agentic-readiness-assessment/notification-service-agentic-readiness-report.md |
| MonoToMicroLegacy | services/unishop-monolith-to-microservices/MonoToMicroLegacy | 2026-03-05 | 1.30 / 4.0 | services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-assessment/MonoToMicroLegacy-agentic-readiness-report.md |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)

---

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - Remove hardcoded credentials from MonoToMicroLegacy `application.properties` — this is a critical security vulnerability that should not wait for Phase 3
   - Upgrade aws-microservices Lambda runtime from Node.js 14.x (EOL) to Node.js 20.x — one-line change per function that eliminates security risk
   - Kick off platform team formation and begin Phase 0 planning

2. **Short-term (Month 1)**:
   - Deploy shared Cognito User Pool for the e-commerce platform
   - Create CI/CD pipeline templates (GitHub Actions and CodePipeline) based on books-api patterns
   - Establish observability standards and create reusable IaC modules
   - Begin training program for IaC, serverless, and observability skills
   - Generate OpenAPI 3.0 specifications for books-api and aws-microservices (highest-scoring services)

3. **Medium-term (Months 1-3)**:
   - Complete Phase 1 modernization of books-api and aws-microservices
   - Validate reference implementation patterns for reuse by Phase 2 teams
   - Begin payment-service and notification-service implementation using Phase 0 templates and Phase 1 patterns
   - Start MonoToMicroLegacy containerization planning and Dockerfile creation
   - Define portfolio-wide event schemas for the EventBridge event bus

4. **Long-term (Months 3-9)**:
   - Complete payment-service and notification-service buildout (Phase 2)
   - Containerize and modernize MonoToMicroLegacy (Phase 3)
   - Deploy shared vector database and build RAG pipelines per domain
   - Implement agent tools layer using Strands Agents SDK with OpenAPI-backed tool definitions
   - Add human approval workflows for high-risk agent operations
   - Establish automated eval frameworks for agent quality and safety
   - Conduct portfolio re-assessment to measure progress against baseline scores
