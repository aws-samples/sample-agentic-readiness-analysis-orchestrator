# Portfolio Agentic Readiness Assessment Report

**Portfolio**: ecommerce-platform-test
**Assessment Goal**: agentic-ai-enablement
**Goal Context**: Building customer-facing AI agents for support and order management
**Services Assessed**: 4
**Assessment Date**: 2026-03-12
**Assessed by**: AWS Transform Custom — Portfolio Agentic Readiness Assessment

---

## Table of Contents

1. Executive Dashboard
2. Portfolio Readiness Overview
3. Service Dependency Map
4. Cross-Cutting Concerns
5. Portfolio Modernization Roadmap
   - Phase 0 — Cross-Cutting Foundation (Mo 0–1)
   - Phase 1 — Agent Quick Wins (Mo 1–2)
   - Phase 2 — Agent Foundations (Mo 2–4)
   - Phase 3 — Agent Scale & Optimization (Mo 4–6+)
6. AWS Modernization Pathways
7. Portfolio Quick Agent Wins
8. AWS Programs & Engagement Recommendations
9. Integration Opportunities
10. Resource Allocation Recommendations
11. Recommended Self-Paced Learning Materials
12. Risk Analysis
13. Service-by-Service Summary
14. Appendix: Assessment Inventory

---

## Executive Dashboard

The ecommerce-platform-test portfolio — comprising four services (unishop-monolith, aws-microservices, local-monolith, and books-api) — is **not ready for agentic AI enablement** with a portfolio readiness score of **1.7 / 4.0**. None of the four services have the foundational capabilities required for building customer-facing AI agents for support and order management: zero services have API documentation (OpenAPI specs) for agent tool discovery, zero have AI/agent framework integrations, zero have vector databases or RAG pipelines for knowledge retrieval, and zero have the observability infrastructure needed to monitor autonomous agent behavior. The portfolio is firmly in the "Needs Work" tier, with the legacy unishop-monolith falling into "Not Ready" territory at 1.3/4.0.

However, the portfolio has significant strengths that reduce the modernization effort. All four services expose structured JSON REST APIs (APP-Q5 scores: 3, 4, 4, 4), all have clean database schemas with zero stored procedures (DATA-Q11: all 4/4), and two services (aws-microservices and books-api) already run on fully managed infrastructure (Lambda, DynamoDB, CDK). The aws-microservices repo demonstrates a mature event-driven architecture with EventBridge and SQS that can serve as a reference pattern for the entire portfolio. These existing capabilities mean agent Quick Wins — such as a unified customer support agent querying existing product and order APIs — are achievable within weeks, not months.

The recommended 6-month roadmap addresses 8 critical agentic-AI-blocking gaps across all services (API documentation, agent frameworks, vector databases, RAG pipelines, human approval workflows, automated evaluations, and LLM cost tracking) while tackling 20+ general improvement opportunities. A centralized platform team should establish shared infrastructure (Cognito authentication, unified API Gateway, Bedrock Knowledge Bases, observability stack) in Phase 0, enabling all four service teams to pursue agent capabilities in parallel. The circular dependency between aws-microservices and books-api must be resolved through clear API contract definition in Phase 0 before proceeding with service-level modernization.

### Portfolio Readiness Score: 1.7 / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | 2.1 / 4.0 | ✅ 0 services, 🟡 2 services, 🟠 1 service, ❌ 1 service | 🟠 |
| Application Architecture | 1.6 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 0 services, ❌ 4 services | ❌ |
| Data Foundations | 1.9 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 4 services, ❌ 0 services | 🟠 |
| Identity, Security & Governance | 1.5 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 service, ❌ 3 services | ❌ |
| Operations & Observability | 1.2 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 service, ❌ 3 services | ❌ |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): 0 services (0%)
- 🟡 Partial (2.5-3.4): 0 services (0%)
- 🟠 Needs Work (1.5-2.4): 3 services (75%) — aws-microservices (1.8), local-monolith (1.5), books-api (2.1)
- ❌ Not Ready (< 1.5): 1 service (25%) — unishop-monolith (1.3)

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | 4 | 2 monoliths, 1 microservices platform, 1 serverless API |
| Average Readiness Score | 1.7 / 4.0 | All services below "Partial" readiness — significant investment required |
| Services Ready for Agents | 0 (0%) | No service has the minimum capabilities for agent deployment |
| Critical Dependencies | 1 circular | aws-microservices ↔ books-api bidirectional dependency must be resolved |
| Shared Infrastructure Gaps | 8 goal-blocking | APP-Q2, APP-Q13, DATA-Q1/Q2/Q3, SEC-Q7, OPS-Q3, OPS-Q6 affect all services |
| Estimated Modernization Effort | High | All services require significant work across all 5 categories |
| Expected Timeline | 6 months | With 3 parallel service tracks after shared foundation (Phase 0) |

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- Java 8 (Spring Boot 2.1): 1 service (25%) — unishop-monolith
- JavaScript/TypeScript (Node.js): 1 service (25%) — aws-microservices
- PHP 8.2 (Slim Framework): 1 service (25%) — local-monolith
- TypeScript (Node.js): 1 service (25%) — books-api

**Database Engines:**
- Amazon DynamoDB (managed): 2 services (50%) — aws-microservices, books-api
- MySQL self-managed (no IaC): 1 service (25%) — unishop-monolith
- Amazon RDS MySQL (managed): 1 service (25%) — local-monolith

**Compute Patterns:**
- AWS Lambda (serverless): 2 services (50%) — aws-microservices, books-api
- EC2 (bare metal): 1 service (25%) — unishop-monolith
- App Runner / Docker: 1 service (25%) — local-monolith

**Infrastructure as Code:**
- Full IaC (CDK/SAM): 2 services (50%) — aws-microservices (CDK), books-api (SAM+CDK)
- Partial IaC (CloudFormation): 1 service (25%) — local-monolith
- No IaC: 1 service (25%) — unishop-monolith

**Deployment Maturity:**
- Full CI/CD (CodePipeline): 1 service (25%) — books-api
- Manual deployment (deploy.sh / cdk deploy): 2 services (50%) — aws-microservices, local-monolith
- No deployment automation: 1 service (25%) — unishop-monolith

### Common Strengths

1. **Structured JSON APIs (APP-Q5)**: 3 of 4 services score 4/4 on API response format; all return consistent JSON. This is the #1 enabler for agent tool integration — agents can parse API responses without custom handling.
2. **Clean Database Schemas (DATA-Q11)**: All 4 services score 4/4 — zero stored procedures, triggers, or proprietary SQL. All business logic resides in application code, making database migration and agent data access straightforward.
3. **Simple Data Architectures (DATA-Q4)**: 2 services score 4/4 and 2 score 3/4 — each service has a single, focused data source. No data sprawl to complicate agent data access patterns.
4. **Event-Driven Foundation (aws-microservices)**: EventBridge + SQS architecture in aws-microservices provides a reusable pattern for cross-service agent event routing.
5. **Mature CI/CD Reference (books-api)**: Full CodePipeline with staging, manual approval, and gradual deployment serves as a template for other services.

### Common Gaps

1. **No API Documentation (APP-Q2)**: All 4 services score 1/4. Zero OpenAPI/Swagger specs exist. Agents cannot discover or invoke any service's capabilities without manually created tool definitions.
2. **No AI/Agent Frameworks (APP-Q13)**: All 4 services score 1/4. No Bedrock, Strands Agents, LangChain, or any agent SDK integrated anywhere in the portfolio.
3. **No Vector Databases (DATA-Q1, DATA-Q2)**: All 4 services score 1/4. No vector store for semantic search. Customer support agents cannot perform similarity-based retrieval.
4. **No RAG Pipeline (DATA-Q3)**: All 4 services score 1/4. No document chunking, embedding generation, or knowledge retrieval infrastructure.
5. **No Observability Infrastructure (OPS-Q1, OPS-Q2)**: 3 of 4 services have zero distributed tracing, zero structured logging. Agent debugging will be impossible without observability foundations.
6. **No Human Approval Workflows (SEC-Q7)**: All 4 services score 1-2/4. Agents could execute destructive operations (order modifications, deletions) without human oversight.
7. **No Rate Limiting (APP-Q8, SEC-Q5)**: All 4 services score 1/4. Agent loops could overwhelm APIs with unbounded requests.

## Service Dependency Map

### High-Level Architecture

The ecommerce-platform-test portfolio consists of four services spanning the e-commerce domain: two monolithic applications (unishop-monolith and local-monolith) that encapsulate product catalog, basket, and order management; one serverless microservices platform (aws-microservices) with event-driven architecture (EventBridge + SQS + DynamoDB); and one serverless REST API (books-api) for book catalog management. The two monoliths are isolated with no cross-service dependencies. The aws-microservices and books-api services share a bidirectional dependency: books-api queries aws-microservices for product catalog data via REST (synchronous), and aws-microservices triggers catalog updates in books-api via EventBridge events (asynchronous).

### Service Dependency Matrix

| Service | Depends On | Depended On By | Coupling Score | Fan-In | Fan-Out | Blast Radius | Priority |
|---------|------------|----------------|----------------|--------|---------|-------------|----------|
| unishop-monolith | None | None | Low (isolated) | 0 | 0 | 25% (self only) | P0 |
| aws-microservices | None (upstream) | books-api | Medium | 1 | 1 | 50% (self + books-api) | P0 |
| local-monolith | None | None | Low (isolated) | 0 | 0 | 25% (self only) | P0 |
| books-api | aws-microservices | aws-microservices | Medium | 1 | 1 | 50% (self + aws-microservices) | P1 |

**Coupling Score Definitions:**
- **High**: Synchronous dependency + shared database OR 3+ dependency types
- **Medium**: Synchronous dependency OR 2 dependency types — *aws-microservices ↔ books-api: 1 sync + 1 async = 2 types*
- **Low**: Minimal or no dependencies — *unishop-monolith and local-monolith are isolated*

**Priority Definitions:**
- **P0**: Critical path services that block others or require immediate modernization
- **P1**: Important services with moderate dependencies, can follow P0 services

### Critical Path Analysis

1. **Foundation Services** (must be modernized first):
   - **unishop-monolith** (P0): Legacy Java monolith with lowest score (1.3/4.0). Isolated — can be modernized independently. Needs containerization, IaC, CI/CD before agent enablement.
   - **aws-microservices** (P0): Strongest infrastructure (EventBridge, DynamoDB, CDK) but weakest operations (1.0/4.0). books-api depends on it — must establish API contracts first.
   - **local-monolith** (P0): PHP monolith with Docker/CloudFormation foundation. Isolated — can be modernized in parallel with other P0 services.

2. **Dependent Services** (modernized after foundation):
   - **books-api** (P1): Depends on aws-microservices for product catalog data. Has best existing CI/CD (4/4) and testing (4/4). Can begin agent integration once aws-microservices APIs are documented and stable.

3. **Independent Services** (can be parallelized):
   - unishop-monolith, local-monolith: Both isolated — can be modernized concurrently with no sequencing constraints.

### Circular Dependency Alert

⚠️ **aws-microservices ↔ books-api** forms a bidirectional dependency (strongly connected component of size 2):
- **books-api → aws-microservices** (sync): REST API queries for product catalog data
- **aws-microservices → books-api** (async): EventBridge events triggering catalog updates

This circular dependency creates deployment coupling — changes to either service could affect the other. **Must be resolved in Phase 0** by defining clear API contracts, versioning interfaces, and implementing circuit breakers.

### Integration Points

**Synchronous Integrations:**
- books-api → aws-microservices: REST API calls for product catalog data

**Asynchronous Integrations:**
- aws-microservices → books-api: EventBridge events for catalog updates (checkout events, product changes)

**Shared Infrastructure:**
- Common e-commerce domain: All 4 services handle product catalog, orders, or basket management
- No shared databases detected — each service owns its own data store
- No shared API Gateway — each service has its own entry point (or none)

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across 3 or more services (with score < 3.0, excluding services where the criterion is N/A). They are split into two subsections based on the portfolio's assessment goal (`agentic-ai-enablement`) to help prioritize what matters most.

### Blocking Your Goal

> These cross-cutting gaps directly impede progress toward building customer-facing AI agents for support and order management. Resolving these should be the highest priority in Phase 0 and Phase 1.

1. **APP-Q2: API Documentation** — 4 of 4 services score 1/4
   - **Impact on goal**: Blocks agent tool discovery across the entire portfolio. Without OpenAPI specs, agents cannot discover available endpoints, understand request/response schemas, or invoke tools.
   - **Affected services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Recommendation**: Establish a portfolio-wide OpenAPI specification standard. Auto-generate specs from existing code (springdoc for Java, swagger-autogen for Node.js, OpenAPI annotations for PHP). Store specs in a shared API catalog.

2. **APP-Q13: AI/Agent Frameworks** — 4 of 4 services score 1/4
   - **Impact on goal**: Blocks all agent development. No service has Bedrock, Strands Agents, LangChain, or any agent SDK. The portfolio cannot support any AI agent capability.
   - **Affected services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Recommendation**: Select a shared agent framework (Strands Agents SDK recommended for AWS-native integration). Build a centralized agent orchestration service that calls individual service APIs as tools. Deploy agent service on ECS (preferred) alongside existing services.

3. **DATA-Q1: Vector Database Presence** — 4 of 4 services score 1/4
   - **Impact on goal**: Blocks semantic search for customer support. Agents cannot perform similarity-based product lookup, order matching, or knowledge retrieval without a vector store.
   - **Affected services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Recommendation**: Deploy a shared Amazon Bedrock Knowledge Base backed by OpenSearch Serverless. Ingest product catalogs, order schemas, and support documentation from all services into a unified knowledge base.

4. **DATA-Q2: Vector DB Management** — 4 of 4 services score 1/4
   - **Impact on goal**: Blocks production-grade RAG. When vector storage is introduced, it must be fully managed for reliable agent operations.
   - **Affected services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Recommendation**: Use Amazon Bedrock Knowledge Bases (fully managed) or OpenSearch Serverless (managed vector search) as the shared vector store. Avoid self-hosted solutions.

5. **DATA-Q3: RAG Implementation** — 4 of 4 services score 1/4
   - **Impact on goal**: Blocks context-grounded agent responses. Customer support agents cannot answer questions about products, orders, or policies without a retrieval-augmented generation pipeline.
   - **Affected services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Recommendation**: Build a shared RAG pipeline using Bedrock Knowledge Bases + Titan Embeddings. Create data connectors from each service's data store (DynamoDB, MySQL) to the knowledge base. Implement automatic sync for embedding freshness.

6. **SEC-Q7: Human Approval Workflows** — 4 of 4 services score 1-2/4
   - **Impact on goal**: Blocks safe agent deployment. Agents performing order management (refunds, cancellations, basket modifications) must have human-in-the-loop approval for high-risk actions.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), books-api (2/4)
   - **Recommendation**: Implement shared AWS Step Functions approval workflows with `waitForTaskToken`. Define portfolio-wide risk thresholds for agent actions (e.g., operations above $100 require human approval). Integrate with Slack/email for approval notifications.

7. **OPS-Q3: Automated Evaluations** — 4 of 4 services score 1/4
   - **Impact on goal**: Blocks production agent quality assurance. Without automated evaluation pipelines, there is no way to measure agent accuracy, detect hallucinations, or regression-test prompt changes.
   - **Affected services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Recommendation**: Create a shared evaluation framework with golden datasets for customer support scenarios. Implement automated scoring (relevance, accuracy, safety) in the CI/CD pipeline. Use Amazon Bedrock model evaluation for standardized assessment.

8. **OPS-Q6: LLM Cost Tracking** — 4 of 4 services score 1/4
   - **Impact on goal**: Blocks cost-effective agent operations. Without token tracking, agent costs could spiral unchecked, especially with customer-facing agents handling high conversation volumes.
   - **Affected services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Recommendation**: Implement centralized LLM cost tracking from day one. Log Bedrock token usage per request with conversation ID, user ID, and service attribution. Create CloudWatch dashboards and cost anomaly alerts. Budget allocation per service.

### General Opportunities

> These cross-cutting gaps are important improvements but do not directly block agentic AI enablement. Address these after resolving goal-blocking concerns.

1. **INF-Q3: Workflow Orchestration** — 4 of 4 services score 1/4
   - **Impact**: No Step Functions or workflow engine. Multi-step agent operations (checkout, returns, escalations) lack orchestration.
   - **Recommendation**: Deploy AWS Step Functions for cross-service workflow orchestration, starting with the checkout flow in aws-microservices.

2. **INF-Q4: Async Messaging** — 3 of 4 services score 1/4 (aws-microservices: 4/4)
   - **Impact**: 75% of services have no async messaging. Agent-triggered operations block on synchronous calls.
   - **Recommendation**: Extend EventBridge pattern from aws-microservices to all services. Add SQS queues for write operations.

3. **INF-Q6: CI/CD** — 3 of 4 services score 1/4 (books-api: 4/4)
   - **Impact**: 75% of services have no automated deployment. Agent prompt/model changes cannot be safely rolled out.
   - **Recommendation**: Use books-api's CodePipeline as a template. Create CI/CD pipelines for all services.

4. **INF-Q8: Real-time Streaming** — 4 of 4 services score 1/4
   - **Impact**: No streaming capability for real-time agent context updates.
   - **Recommendation**: Implement EventBridge for event routing; add DynamoDB Streams for change notifications.

5. **APP-Q3: Async Communication** — 4 of 4 services score 1-2/4
   - **Impact**: Most operations are synchronous. Agent workflows requiring long-running processing will timeout.
   - **Recommendation**: Introduce async patterns with SQS and EventBridge across all services.

6. **APP-Q6: Workflow Logic** — 4 of 4 services score 1-2/4
   - **Impact**: Business logic is hardcoded without orchestration. Complex agent workflows lack state management.
   - **Recommendation**: Refactor into Step Functions state machines, especially for checkout and return flows.

7. **APP-Q7: Idempotency** — 4 of 4 services score 1-2/4
   - **Impact**: Agent retries on failed tool calls could create duplicate orders, products, or basket entries.
   - **Recommendation**: Add Idempotency-Key header support to all write endpoints. Use DynamoDB conditional writes.

8. **APP-Q8: Rate Limiting** — 4 of 4 services score 1/4
   - **Impact**: Agent loops could overwhelm APIs. No per-client throttling exists.
   - **Recommendation**: Add API Gateway throttling to all services. Create separate usage plans for agent vs human traffic.

9. **APP-Q9: Resilience Patterns** — 4 of 4 services score 1/4
   - **Impact**: No circuit breakers, retry logic, or timeout configurations. Agent tool calls fail silently.
   - **Recommendation**: Add retry with exponential backoff, circuit breakers, and timeout configuration across all services.

10. **APP-Q11: API Versioning** — 4 of 4 services score 1/4
    - **Impact**: API changes break agent tool configurations with no migration path.
    - **Recommendation**: Adopt URL path versioning (`/v1/`) for all endpoints before agent tools are defined.

11. **SEC-Q4: Audit Logging** — 4 of 4 services score 1-2/4
    - **Impact**: No audit trail for agent actions. Compliance and debugging are impossible.
    - **Recommendation**: Implement structured audit logging with CloudTrail and CloudWatch Logs.

12. **SEC-Q6: PII Redaction** — 4 of 4 services score 1/4
    - **Impact**: Customer PII exposed in logs and API responses. Agents handling customer data create compliance risk.
    - **Recommendation**: Implement log sanitization and field-level access control for PII.

13. **OPS-Q1: Distributed Tracing** — 3 of 4 services score 1/4 (books-api: 3/4)
    - **Impact**: Cannot trace agent tool invocations across services. Debugging multi-step agent workflows impossible.
    - **Recommendation**: Add X-Ray/OpenTelemetry to all services. Use books-api's X-Ray setup as reference.

14. **OPS-Q2: Structured Logging** — 4 of 4 services score 1/4
    - **Impact**: Unstructured logging prevents log correlation and CloudWatch Log Insights queries.
    - **Recommendation**: Adopt Lambda Powertools (Node.js/Python) or SLF4J+Logback JSON (Java) across all services.

15. **OPS-Q4: SLOs** — 4 of 4 services score 1/4
    - **Impact**: No performance baselines. Cannot detect if agents degrade API performance.
    - **Recommendation**: Define SLOs for all API endpoints and agent-specific metrics (task success rate, response time).

16. **OPS-Q7, OPS-Q8, OPS-Q11, OPS-Q12: Operations Maturity** — 4 of 4 services score 1/4 on each
    - **Impact**: No business metrics, anomaly detection, incident response, or observability governance.
    - **Recommendation**: Build unified observability platform with CloudWatch dashboards, anomaly detection, and runbooks.

### Per-Category Analysis

### Infrastructure & Platform

**Portfolio Score: 2.1 / 4.0**

The strongest category in the portfolio, driven by aws-microservices (2.5) and books-api (2.7) having solid managed compute and IaC foundations. However, unishop-monolith (1.0) has zero infrastructure capabilities (no IaC, no CI/CD, no containers, no API Gateway), and local-monolith (2.0) has partial coverage. The key strengths are Lambda compute (2 services), CDK/SAM IaC (2 services), and DynamoDB managed databases (2 services). Critical gaps are workflow orchestration (all 4 services: 1/4), real-time streaming (all 4: 1/4), and the wide variance in CI/CD maturity (1 service at 4/4, 3 services at 1/4).

### Application Architecture

**Portfolio Score: 1.6 / 4.0**

The weakest functional category. While all services have strong JSON APIs (3-4/4) and one service has excellent microservices architecture (aws-microservices: 4/4), the portfolio universally lacks API documentation (all 1/4), AI frameworks (all 1/4), rate limiting (all 1/4), resilience patterns (all 1/4), and API versioning (all 1/4). Two services are monoliths requiring decomposition. The lack of API documentation is the single most impactful gap for agent enablement.

### Data Foundations

**Portfolio Score: 1.9 / 4.0**

Clean data architectures with zero stored procedures (all 4/4) and simple data sources (3-4/4), but completely lacking in AI-specific data capabilities. All 4 services score 1/4 on vector database, vector DB management, RAG implementation, unstructured data handling, and embedding freshness. The MySQL-based services (unishop-monolith, local-monolith) have well-documented schemas that are ideal for natural-language-to-SQL agents, while DynamoDB services (aws-microservices, books-api) have clean key-value patterns.

### Identity, Security & Governance

**Portfolio Score: 1.5 / 4.0**

Critical security gaps across the portfolio. Only books-api has partial authentication (SEC-Q9: 2/4) and a centralized identity provider (SEC-Q10: 3/4). The other 3 services have effectively zero authentication — unishop-monolith has OAuth2 configured but disabled with `permitAll()`, and aws-microservices has completely unauthenticated API Gateway endpoints. PII redaction (all 1/4), human approval workflows (all 1-2/4), and API rate limits (all 1/4) are universally absent.

### Operations & Observability

**Portfolio Score: 1.2 / 4.0**

The weakest category by far. Only books-api has meaningful operations capabilities (OPS: 1.9/4.0) with X-Ray tracing, CodePipeline CI/CD, rollback capability, and integration testing. The other 3 services score 1.0/4.0 with zero observability across all 12 operations criteria. This is a critical gap for agent deployment — autonomous agents operating without tracing, logging, or monitoring create significant operational risk.

## Portfolio Modernization Roadmap

> This roadmap accounts for cross-service dependencies, shared infrastructure, and organizational capacity. Work is sequenced to minimize risk and maximize value delivery. Phase names reflect the `agentic-ai-enablement` goal. Within each phase, goal-priority activities (APP-Q2, APP-Q13, DATA-Q1/Q2/Q3, SEC-Q7, OPS-Q3, OPS-Q6) are listed first.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: aws-microservices (Phase 1) before books-api (Phase 2)
3. **Risk Mitigation**: Circular dependency resolution and authentication before agent deployment
4. **Parallel Tracks**: unishop-monolith, aws-microservices, and local-monolith can be modernized concurrently
5. **Quick Wins**: OpenAPI specs and agent PoCs deliver immediate value
6. **Goal Alignment**: Within each phase, agentic-AI-priority activities are listed first

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, resolve architectural risks, and prepare the organization for agent development

**Shared Infrastructure (Goal-Blocking — Highest Priority):**
- **Agent framework selection and PoC**: Select Strands Agents SDK as the shared agent framework. Create a reference agent implementation that calls a mock API. Benefits all 4 services.
- **OpenAPI specification standard**: Define portfolio-wide OpenAPI 3.0 template with consistent naming, versioning, and schema conventions. Each service team generates specs in Phase 1.
- **Shared vector database**: Provision Amazon Bedrock Knowledge Base backed by OpenSearch Serverless. Configure data source connectors for S3 (documentation) and DynamoDB (product catalogs).
- **Authentication platform**: Deploy shared Amazon Cognito User Pool for customer and agent authentication. Define OAuth scopes for agent actions (read, write, admin).

**Shared Infrastructure (General):**
- **Observability stack**: Deploy unified CloudWatch + X-Ray + OpenTelemetry collector. Create portfolio dashboard templates.
- **CI/CD templates**: Create reusable CodePipeline/GitHub Actions templates for Lambda, ECS, and CDK-based services.
- **EventBridge shared bus**: Create a portfolio-wide EventBridge event bus for cross-service domain events.

**Architectural Risk Resolution:**
- **Circular dependency (aws-microservices ↔ books-api)**: Define versioned API contracts between the two services. Implement circuit breakers for the sync dependency. Document event schemas for the async dependency.

**Organizational Enablers:**
- Training: Amazon Bedrock Getting Started, Strands Agents SDK, ECS/Lambda patterns, CDK
- Tooling: Shared CDK construct library, OpenAPI linting tools, agent testing harness
- Standards: API naming conventions, logging format (JSON), error response format (RFC 7807)

**Expected Outcomes:**
- Shared Cognito User Pool deployed and ready for service integration
- Bedrock Knowledge Base provisioned with initial product documentation
- API contract between aws-microservices and books-api formalized
- All teams trained on agent development basics

**Estimated Effort**: High

### Phase 1 — Agent Quick Wins (Mo 1–2)

**Objective**: Modernize foundational services, generate OpenAPI specs, and deliver first agent prototypes. Goal-priority activities listed first.

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.3/4.0)
   - Current State: Java 8 / Spring Boot 2.1 monolith on EC2, self-managed MySQL, no IaC/CI/CD/observability
   - Target State: Containerized on ECS, OpenAPI specs generated, managed database, CI/CD pipeline, initial agent PoC
   - Key Activities (goal-priority first):
     - Generate OpenAPI 3.0 specs via springdoc-openapi-ui (APP-Q2)
     - Build customer support agent PoC calling `/unicorns` and `/unicorns/basket/{userUuid}` (APP-Q13)
     - Containerize application (Dockerfile → ECR → ECS Fargate)
     - Migrate secrets to Secrets Manager
     - Establish CDK IaC and CodePipeline CI/CD
     - Migrate MySQL to Amazon RDS (managed)
   - Dependencies: None (isolated service)
   - Blocks: None
   - Estimated Effort: High

2. **aws-microservices** (P0, Score: 1.8/4.0)
   - Current State: Lambda + DynamoDB + EventBridge + CDK, but no CI/CD, no auth, no observability
   - Target State: OpenAPI specs generated, CI/CD pipeline, X-Ray tracing, Cognito authentication, agent PoC
   - Key Activities (goal-priority first):
     - Generate OpenAPI 3.0 specs for product/basket/ordering APIs (APP-Q2)
     - Build customer support agent PoC querying product and order endpoints (APP-Q13)
     - Create CI/CD pipeline (CodePipeline: lint → test → cdk synth → deploy)
     - Add Cognito authorizer to all API Gateway endpoints (SEC-Q9)
     - Enable X-Ray tracing on all Lambda functions (OPS-Q1)
     - Upgrade Lambda runtime from NODEJS_14_X to NODEJS_20_X
   - Dependencies: None
   - Blocks: books-api (Phase 2) depends on stable, documented APIs
   - Estimated Effort: High

3. **local-monolith** (P0, Score: 1.5/4.0)
   - Current State: PHP 8.2 monolith with Docker/CloudFormation, RDS MySQL, manual deploy.sh
   - Target State: ECS deployment, OpenAPI specs, CI/CD pipeline, Cognito auth, agent PoC
   - Key Activities (goal-priority first):
     - Generate OpenAPI 3.0 specs for all 20+ API endpoints (APP-Q2)
     - Build customer support agent PoC for order lookup and product catalog (APP-Q13)
     - Migrate from App Runner/Docker to ECS Fargate (preferred compute)
     - Create CodePipeline CI/CD replacing manual deploy.sh
     - Integrate Cognito for API authentication
     - Add X-Ray tracing and structured logging
   - Dependencies: None (isolated service)
   - Blocks: None
   - Estimated Effort: High

**Cross-Service Activities:**
- Integrate all 3 services with shared Cognito User Pool
- Begin populating Bedrock Knowledge Base with product catalog data from all services
- Establish EventBridge event schemas for cross-service communication

**Expected Outcomes:**
- OpenAPI specs available for all 4 services
- 3 agent PoCs demonstrating customer support query capabilities
- CI/CD pipelines operational for all services
- Authentication enabled on all API endpoints

**Estimated Effort**: High

### Phase 2 — Agent Foundations (Mo 2–4)

**Objective**: Build production-grade agent infrastructure, implement RAG, deploy approval workflows, and integrate books-api. Goal-priority activities listed first.

**Services in Scope:**

1. **books-api** (P1, Score: 2.1/4.0)
   - Current State: Lambda + DynamoDB + CDK + CodePipeline — best infrastructure maturity. No agent frameworks or RAG.
   - Target State: Agent integration with RAG, Step Functions for approval workflows, structured logging
   - Key Activities (goal-priority first):
     - Integrate with shared Bedrock Knowledge Base for book catalog RAG (DATA-Q1, DATA-Q3)
     - Add agent tool definitions from OpenAPI specs (APP-Q13)
     - Implement human approval workflow for catalog modifications (SEC-Q7)
     - Implement LLM cost tracking per agent request (OPS-Q6)
     - Add SQS queues for async event processing (INF-Q4)
     - Add structured logging with Lambda Powertools (OPS-Q2)
   - Dependencies: aws-microservices (Phase 1) — stable, documented API required
   - Blocks: None
   - Estimated Effort: Medium

**Cross-Service Activities (all services):**
- **RAG Pipeline**: Complete Bedrock Knowledge Base integration with all data sources (DynamoDB exports, MySQL dumps, S3 documentation). Configure automatic sync.
- **Step Functions Approval Workflows**: Deploy shared approval state machines for high-risk agent actions (order modifications above threshold, product deletions, refunds).
- **Unified API Gateway**: Begin consolidating service endpoints behind a unified API Gateway with path-based routing.
- **Agent Evaluation Framework**: Create golden datasets for customer support scenarios. Build automated scoring pipeline.

**Parallel Tracks:**
- unishop-monolith: Continue microservices decomposition (Basket service extraction)
- aws-microservices: Add Step Functions for checkout flow, idempotency for all writes
- local-monolith: Add Step Functions for return/refund workflows

**Expected Outcomes:**
- RAG pipeline operational with cross-service product and order knowledge
- Human approval workflows active for high-risk agent actions
- books-api fully integrated with agent platform
- Evaluation framework with initial golden datasets

**Estimated Effort**: High

### Phase 3 — Agent Scale & Optimization (Mo 4–6+)

**Objective**: Deploy production customer support agents, implement evaluation pipelines, optimize costs, and achieve advanced observability. Goal-priority activities listed first.

**Activities (goal-priority first):**
- **Production Agent Deployment**: Deploy unified customer-facing support agent handling product queries, order status, returns, and basket management across all 4 services. Full RAG integration with conversation memory (DynamoDB).
- **Automated Evaluation Pipeline** (OPS-Q3): Golden dataset regression testing in CI/CD. Track relevance, accuracy, hallucination rate, and safety scores. Automated alerts on quality degradation.
- **LLM Cost Optimization** (OPS-Q6): Per-conversation token tracking with user/workflow attribution. Cost anomaly alerts. Implement tiered model selection (smaller model for simple queries, larger for complex).
- **Agent Quality SLOs**: Define and monitor: task success rate > 90%, p95 response time < 5s, hallucination rate < 5%, customer satisfaction > 4.0/5.0.
- **Microservices Decomposition**: Extract Basket service from unishop-monolith (DynamoDB-backed, agent-friendly). Decompose local-monolith into order, product, and fulfillment services.
- **Advanced Observability**: CloudWatch anomaly detection on agent behavior (detect reasoning loops). Business metrics dashboards (support tickets resolved, order modifications by agent). Incident response runbooks.
- **Event-Driven Analytics**: Stream agent interactions to EventBridge → analytics pipeline. Build agent effectiveness dashboards.
- **Blue/Green Deployments**: CodeDeploy with canary analysis for agent prompt/model changes. Version all agent configurations.

**Expected Outcomes:**
- Production customer support agent serving real customers
- Automated evaluation pipeline catching quality regressions
- Full cost visibility and optimization
- Advanced observability and anomaly detection

**Estimated Effort**: High

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6 months (with 3 parallel service tracks after Phase 0)
- Phase 0: Month 0–1 (shared foundation)
- Phase 1: Month 1–2 (3 services in parallel: unishop-monolith, aws-microservices, local-monolith)
- Phase 2: Month 2–4 (books-api + cross-service integration)
- Phase 3: Month 4–6+ (production agents + optimization)

## AWS Modernization Pathways

Based on the portfolio-wide assessment findings, the following AWS Modernization Pathways have been identified for each service. The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach — a customer portfolio may be divided into multiple pathways depending on workloads and priorities, and these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 4 services | 100% | High | High |
| Move to Containers | 3 services | 75% | High | Medium |
| Move to Open Source | 0 services | 0% | Low | — |
| Move to Managed Databases | 3 services | 75% | High | Medium |
| Move to Managed Analytics | 3 services | 75% | Medium | Low |
| Move to Modern DevOps | 4 services | 100% | High | High |
| Move to AI | 4 services | 100% | High | High |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| unishop-monolith | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| aws-microservices | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| local-monolith | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| books-api | ✅ | — | — | — | ✅ | ✅ | ✅ |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing a single at-a-glance view of pathway coverage across the portfolio. Each repo appears in exactly one column per pathway row. Goal Alignment is based on the portfolio-level goal (`agentic-ai-enablement`) using the goal-pathway alignment mapping.

| Pathway | Triggered | Not Triggered | Not Applicable | Goal Alignment |
|---------|-----------|---------------|----------------|---------------|
| Move to Cloud Native | unishop-monolith, aws-microservices, local-monolith, books-api | — | — | Medium |
| Move to Containers | unishop-monolith, aws-microservices, local-monolith | books-api | — | Medium |
| Move to Open Source | — | unishop-monolith, aws-microservices, local-monolith, books-api | — | Low |
| Move to Managed Databases | unishop-monolith, aws-microservices, local-monolith | books-api | — | High |
| Move to Managed Analytics | unishop-monolith, aws-microservices, books-api | local-monolith | — | Low |
| Move to Modern DevOps | unishop-monolith, aws-microservices, local-monolith, books-api | — | — | High |
| Move to AI | unishop-monolith, aws-microservices, local-monolith, books-api | — | — | High |

**Validation**: Each row totals 4 repos (Triggered + Not Triggered + Not Applicable = 4). ✓

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- **Move to Containers** should precede **Move to Cloud Native** — containerize monoliths before decomposing into microservices
- **Move to Managed Databases** should precede **Move to AI** — data foundations (vector store, managed DB) needed for RAG pipeline
- **Move to Modern DevOps** enables faster execution of all other pathways — CI/CD accelerates delivery across the portfolio

**Parallel Execution Tracks:**
- **Track 1 (Infrastructure)**: Move to Containers + Move to Modern DevOps — containerization and CI/CD can proceed simultaneously
- **Track 2 (Data)**: Move to Managed Databases + Move to Managed Analytics — database migration and analytics can proceed in parallel
- **Track 3 (Agent)**: Move to AI — agent framework integration, RAG pipeline, evaluation infrastructure

### Pathway Details

#### Move to Cloud Native

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, books-api (4 total)
- **Portfolio Priority**: High (100% of services triggered)
- **Common Trigger Criteria**:
  - APP-Q4 < 4: 3 services (unishop 2/4, local-monolith 1/4, books-api 3/4)
  - INF-Q1 < 3: 2 services (unishop 1/4, local-monolith 2/4)
  - APP-Q3 < 3: 4 services (all score 1-2/4)
  - APP-Q10 < 3: 3 services (unishop 1/4, aws-microservices 2/4, local-monolith 1/4)
- **Representative AWS Services**: Lambda, API Gateway, Step Functions, EventBridge, SQS, SNS
- **Key Activities**: Decompose monoliths using Strangler Fig pattern, introduce async communication via EventBridge, adopt serverless patterns for new services
- **Cross-Service Synergies**: aws-microservices demonstrates clean microservices architecture (4/4) — use as reference for monolith decomposition
- **Estimated Effort**: High across 4 services
- **Roadmap Phase Alignment**: Phase 1 (containerization), Phase 2-3 (decomposition)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

#### Move to Containers

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith (3 total)
- **Portfolio Priority**: High (75% of services triggered, includes P0 foundation services)
- **Common Trigger Criteria**:
  - INF-Q1 < 3: unishop-monolith (1/4 — EC2), local-monolith (2/4 — App Runner)
  - No Dockerfile: aws-microservices (Lambda-based but no container packaging)
- **Representative AWS Services**: ECS, Fargate, ECR, Docker
- **Key Activities**: Create Dockerfiles for monoliths, deploy to ECS Fargate, configure ALB health checks
- **Cross-Service Synergies**: local-monolith already has a Dockerfile — use as template for unishop-monolith
- **Estimated Effort**: Medium across 3 services (books-api already serverless, not triggered)
- **Roadmap Phase Alignment**: Phase 1 (containerization)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

#### Move to Managed Databases

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith (3 total)
- **Portfolio Priority**: High (75% of services triggered, **High Goal Alignment** for agentic-ai-enablement)
- **Common Trigger Criteria**:
  - INF-Q2 < 4: unishop-monolith (1/4 — self-managed MySQL)
  - DATA-Q2 < 4: aws-microservices (1/4 — no vector DB)
  - DATA-Q10: local-monolith (3/4 — dev/prod version mismatch)
- **Representative AWS Services**: Amazon RDS, Aurora, DynamoDB, OpenSearch Serverless
- **Key Activities**: Migrate self-managed MySQL to RDS/Aurora, provision vector database for RAG, evaluate DynamoDB for key-value patterns
- **Cross-Service Synergies**: DynamoDB pattern from aws-microservices/books-api as template for basket service migration
- **Estimated Effort**: Medium across 3 services
- **Roadmap Phase Alignment**: Phase 1 (database migration), Phase 2 (vector DB)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Managed Analytics

- **Services Affected**: unishop-monolith, aws-microservices, books-api (3 total)
- **Portfolio Priority**: Medium (75% triggered but Low Goal Alignment)
- **Common Trigger Criteria**:
  - INF-Q8 < 3: All 3 triggered services score 1/4 on real-time streaming
- **Representative AWS Services**: EventBridge, Kinesis Data Streams, DynamoDB Streams
- **Key Activities**: Implement EventBridge for domain event streaming, add DynamoDB Streams for real-time data changes
- **Estimated Effort**: Low across 3 services
- **Roadmap Phase Alignment**: Phase 3 (analytics and optimization)
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

#### Move to Modern DevOps

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, books-api (4 total)
- **Portfolio Priority**: High (100% of services triggered, **High Goal Alignment**)
- **Common Trigger Criteria**:
  - INF-Q6 < 3: 3 services (unishop 1/4, aws-microservices 1/4, local-monolith 1/4)
  - OPS-Q9 < 3: 3 services (unishop 1/4, aws-microservices 1/4, local-monolith 1/4)
  - OPS-Q10 < 3: 3 services (unishop 1/4, aws-microservices 1/4, local-monolith 1/4)
  - OPS-Q1 < 3: 3 services (unishop 1/4, aws-microservices 1/4, local-monolith 1/4)
- **Representative AWS Services**: CodePipeline, CodeBuild, CodeDeploy, CloudFormation, CDK, X-Ray
- **Key Activities**: Establish CI/CD pipelines, implement IaC, add distributed tracing, configure structured logging
- **Cross-Service Synergies**: books-api's CodePipeline (4/4) as reference pattern; aws-microservices' CDK (4/4) as IaC template
- **Estimated Effort**: High across 4 services
- **Roadmap Phase Alignment**: Phase 0-1 (CI/CD, IaC), Phase 2 (advanced observability)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, books-api (4 total)
- **Portfolio Priority**: High (100% of services triggered, **High Goal Alignment** — this is the primary pathway for agentic-ai-enablement)
- **Common Trigger Criteria**:
  - APP-Q13 < 3: ALL 4 services score 1/4 (no agent frameworks)
  - DATA-Q1 < 3: ALL 4 services score 1/4 (no vector database)
  - DATA-Q3 < 3: ALL 4 services score 1/4 (no RAG implementation)
  - OPS-Q3 < 3: ALL 4 services score 1/4 (no automated evaluations)
  - OPS-Q6 < 3: ALL 4 services score 1/4 (no LLM cost tracking)
- **Representative AWS Services**: Amazon Bedrock, Amazon Bedrock AgentCore, Amazon Q, Strands Agents SDK, OpenSearch Serverless
- **Key Activities**: Build centralized agent orchestration service, deploy RAG pipeline with Bedrock Knowledge Bases, implement agent evaluation framework, add LLM cost tracking
- **Cross-Service Synergies**: Unified customer support agent serves all 4 services via their APIs as tools. Shared Bedrock Knowledge Base indexes data from all services.
- **Estimated Effort**: High across 4 services
- **Roadmap Phase Alignment**: Phase 0 (framework selection), Phase 1 (agent PoCs), Phase 2 (RAG, approvals), Phase 3 (production deployment)
- **Relevant Learning Materials**: Module 7 — Move to AI

### Example: Parallel Pathway Execution for a Single Service

**aws-microservices** simultaneously pursues:
- **Move to Cloud Native**: Already microservices (4/4) — extend async patterns (Step Functions, more EventBridge events)
- **Move to Containers**: Package Lambda functions for container deployment flexibility
- **Move to Modern DevOps**: Build CI/CD pipeline, add X-Ray tracing, structured logging
- **Move to Managed Databases**: Provision vector database (OpenSearch Serverless) for RAG
- **Move to AI**: Build customer support agent PoC, integrate with Bedrock Knowledge Base, implement evaluation framework

## Portfolio Quick Agent Wins

> Included because the portfolio goal is `agentic-ai-enablement`. Goal context: Building customer-facing AI agents for support and order management.

Across the portfolio, these agent opportunities are immediately available based on existing capabilities found in individual assessments:

**Customer Support Query Agents** (4 repos: unishop-monolith, aws-microservices, local-monolith, books-api)
- All 4 services expose REST APIs returning structured JSON for products, orders, and baskets. An agent can be built today to query product catalogs (`GET /unicorns`, `GET /product`, `GET /api/products`, `GET /books`), check order status (`GET /order/{userName}`, `GET /api/orders/me`), and view basket contents (`GET /unicorns/basket/{userUuid}`, `GET /basket/{userName}`). This directly enables the "customer-facing AI agents for support and order management" goal.

**Agent Tool Integration via JSON APIs** (2 repos: aws-microservices, books-api)
- aws-microservices and books-api return consistently structured JSON responses (`{ message: "...", body: <data> }`). Agent tool parsers can be standardized across these services without custom response handling, accelerating multi-tool agent development.

**Natural Language Data Query Agents** (2 repos: unishop-monolith, local-monolith)
- Both MySQL-based monoliths have clean relational schemas ideal for text-to-SQL agents. unishop-monolith has a 3-table schema (unicorns, unicorns_basket, unicorn_user) and local-monolith has a 9-table schema (orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users). Agents can translate customer support queries like "Show me all orders from last week" into SQL.

**Knowledge Base / RAG Agents** (3 repos: unishop-monolith, aws-microservices, books-api)
- unishop-monolith has SQL schema documentation and product seed data. aws-microservices has README with architecture docs and DynamoDB schema comments. books-api has comprehensive README and CONTRIBUTING.md. These can be ingested into a shared Bedrock Knowledge Base for an internal developer support agent.

**DevOps Deployment Agents** (2 repos: aws-microservices, books-api)
- aws-microservices has comprehensive CDK IaC for the full infrastructure stack. books-api has a complete CodePipeline with staging and production stages. Agents can trigger deployments, check pipeline status, and report on infrastructure changes.

**Return/Fulfillment Support Agents** (1 repo: local-monolith)
- local-monolith has rich decision-support APIs for returns (`POST /api/returns`), warehouse assignment scoring, and carrier shipping options. An agent can automate return intake and recommend fulfillment decisions.

### Cross-Repo Agent Opportunities

**Unified E-Commerce Customer Support Agent** (all 4 repos)
- Combine product catalog queries (all services), order management (aws-microservices, local-monolith, unishop-monolith), and book catalog (books-api) into a single customer-facing support agent. The agent uses each service's API as a tool, providing a unified interface for customers to ask "What products do you have?", "Where is my order?", "Can I return this item?", and "Do you have any books about X?". This is more valuable than individual per-service agents because customers don't know (or care) which backend service handles their request.

**Cross-Service Order Orchestration Agent** (aws-microservices → books-api)
- The EventBridge-based async dependency between aws-microservices and books-api enables an orchestration agent that manages cross-service workflows: when an order is placed in aws-microservices, the agent can verify related book catalog items in books-api, update inventory, and notify the customer — all as a coordinated workflow.

**Portfolio-Wide Developer Support Agent** (all repos)
- Combine documentation from all 4 repos into a unified knowledge base. Internal developers can ask "How does checkout work in aws-microservices?", "What's the database schema for the monolith?", or "How do I deploy books-api?" — a single agent answers based on all repo documentation.

### Prioritized Agent Wins

| Win | Repos Affected | Goal Alignment | Effort | Recommended Phase |
|-----|---------------|----------------|--------|-------------------|
| Unified Customer Support Agent | 4 repos | High | Medium | Phase 1 |
| Product Catalog Query Agent | 4 repos | High | Low | Phase 1 |
| Order Status Lookup Agent | 3 repos | High | Low | Phase 1 |
| NL-to-SQL Data Query Agent | 2 repos | High | Medium | Phase 2 |
| RAG Knowledge Base Agent | 3 repos | High | Low-Medium | Phase 2 |
| Return Intake Agent | 1 repo | High | Low | Phase 1 |
| DevOps Deployment Agent | 2 repos | Medium | Medium | Phase 2 |
| Cross-Service Orchestration Agent | 2 repos | High | Medium | Phase 3 |

> These portfolio-wide agent opportunities can be pursued in parallel with the
> modernization roadmap. They demonstrate agent value early while foundations
> are being built across the portfolio.

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.** Programs are engagement-level decisions scoped to the customer's overall estate, not per-repo.

Based on the portfolio assessment findings, the following AWS programs may accelerate your modernization journey:

### Recommended Programs

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| Migration Acceleration Program (MAP) | High | All 4 repos score below 2.5 overall (unishop-monolith: 1.3, aws-microservices: 1.8, local-monolith: 1.5, books-api: 2.1) — significantly exceeds the 3-repo threshold | Evaluate MAP eligibility with your AWS account team for migration credits and professional services support |
| EBA — Move to Cloud Native | High | 4 of 4 services triggered (APP-Q4, INF-Q1, APP-Q3, APP-Q10). Two monoliths require decomposition. | Request EBA engagement via SA for Strangler Fig decomposition guidance |
| EBA — Move to Containers | High | 3 of 4 services triggered (unishop-monolith INF-Q1: 1/4, aws-microservices no Dockerfile, local-monolith INF-Q1: 2/4). Core P0 services need containerization. | Request EBA engagement via SA for ECS migration acceleration |
| EBA — Move to Managed Databases | Medium | 3 of 4 services triggered (unishop-monolith INF-Q2: 1/4 self-managed MySQL, aws-microservices DATA-Q2: 1/4, local-monolith DATA-Q10: 3/4) | Request EBA engagement via SA for database migration planning |
| EBA — Move to Modern DevOps | High | 4 of 4 services triggered. 3 services have zero CI/CD (INF-Q6: 1/4). 3 services have zero observability (OPS-Q1: 1/4). | Request EBA engagement via SA for DevOps transformation |
| EBA — Move to AI | High | 4 of 4 services triggered with all AI criteria at 1/4 (APP-Q13, DATA-Q1, DATA-Q3, OPS-Q3, OPS-Q6). Primary pathway for `agentic-ai-enablement` goal. | Request EBA engagement via SA for agent architecture design and Bedrock implementation |

### Program Details

**Migration Acceleration Program (MAP)** — Recommended with High relevance because all 4 services in the portfolio score below 2.5/4.0, indicating substantial modernization needs across compute, data, security, and operations dimensions. MAP provides migration credits, AWS Professional Services engagement, and partner support that can significantly accelerate the 6-month roadmap, particularly for Phase 0 shared infrastructure establishment and Phase 1 service modernization. Suggested timing: Initiate MAP assessment during Phase 0.

**EBA — Move to Cloud Native** — The two monoliths (unishop-monolith and local-monolith) both require decomposition into microservices for effective agent tool boundary definition. An EBA engagement provides hands-on guidance for Strangler Fig pattern implementation, event-driven architecture design (EventBridge/SQS), and API Gateway routing strategies. Suggested timing: Phase 1-2.

**EBA — Move to Containers** — Three P0 services need containerization: unishop-monolith (EC2 → ECS), local-monolith (App Runner → ECS), and aws-microservices (Lambda → container packaging). EBA provides accelerated ECS cluster design, Dockerfile optimization, and ECR/deployment pipeline guidance. Suggested timing: Phase 1.

**EBA — Move to Managed Databases** — unishop-monolith has self-managed MySQL with no IaC, presenting migration risk. EBA provides database migration strategy guidance with AWS DMS and Schema Conversion Tool expertise. Suggested timing: Phase 1-2.

**EBA — Move to Modern DevOps** — Three of four services have zero CI/CD and zero observability. EBA provides accelerated DevOps transformation with CodePipeline/CodeBuild templates, X-Ray integration, and structured logging patterns. Suggested timing: Phase 0-1.

**EBA — Move to AI** — The primary pathway for the portfolio's `agentic-ai-enablement` goal. All services lack AI foundations. EBA provides agent architecture design, Bedrock Knowledge Base implementation guidance, Strands Agents SDK best practices, and evaluation framework design. Suggested timing: Phase 0-3 (continuous engagement).

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

## Integration Opportunities

### Shared Service Extraction

**Opportunity 1: Centralized Authentication Service (Amazon Cognito)**
- Current State: unishop-monolith has OAuth2 disabled (permitAll), aws-microservices has zero auth, local-monolith has basic WAF, books-api has partial Cognito
- Proposed Solution: Deploy shared Amazon Cognito User Pool with customer pools and agent service accounts. OAuth scopes for read, write, and admin operations.
- Benefits: Consistent authentication across all services, agent identity propagation, per-user data access boundaries
- Effort: Medium
- Priority: High — prerequisite for safe agent deployment

**Opportunity 2: Agent Orchestration Service (Strands Agents SDK)**
- Current State: All 4 services score 1/4 on APP-Q13. No agent framework anywhere.
- Proposed Solution: Build a centralized agent service using Strands Agents SDK that calls individual service APIs as tools. Deploy on ECS Fargate. Define tools from OpenAPI specs.
- Benefits: Single agent service manages all customer interactions, consistent tool interface, centralized prompt management
- Effort: High
- Priority: High — core requirement for agentic-ai-enablement goal

**Opportunity 3: Unified Observability Platform**
- Current State: 3 of 4 services have zero tracing and logging. Only books-api has X-Ray.
- Proposed Solution: Deploy unified CloudWatch + X-Ray + OpenTelemetry stack. Shared dashboards, log format standards, correlation ID propagation.
- Benefits: End-to-end agent request tracing, consistent metrics, portfolio-level visibility
- Effort: Medium
- Priority: High — required for debugging agent tool invocations

**Opportunity 4: Shared Bedrock Knowledge Base**
- Current State: All 4 services score 1/4 on DATA-Q1, DATA-Q2, DATA-Q3. No vector store or RAG.
- Proposed Solution: Deploy Amazon Bedrock Knowledge Base backed by OpenSearch Serverless. Ingest product catalogs, order schemas, and support documentation from all 4 services.
- Benefits: Unified semantic search across all e-commerce data, reduced infrastructure cost vs per-service vector stores
- Effort: Medium
- Priority: High — core enabler for customer support RAG

### Event-Driven Architecture

**Opportunity 1: Portfolio-Wide EventBridge Bus**
- Current State: aws-microservices has EventBridge + SQS (INF-Q4: 4/4). Other 3 services score 1/4.
- Proposed Solution: Create a shared EventBridge event bus. Extend the aws-microservices EventBridge pattern to all services. Define domain event schemas: `OrderCreated`, `ProductUpdated`, `ReturnRequested`, `CatalogUpdated`, `BasketModified`.
- Benefits: Decoupled services, agent event-driven reactions, real-time knowledge base updates
- Effort: Medium
- Priority: High — aligned with EventBridge preference

**Opportunity 2: Async Agent Task Processing**
- Current State: All services process requests synchronously. Agent workflows could timeout on long operations.
- Proposed Solution: SQS queues for async agent tasks (returns processing, order modifications). Status polling endpoints for agent completion tracking.
- Benefits: Agents don't timeout on long operations, scalable task processing
- Effort: Low
- Priority: Medium

### API Gateway Consolidation

- Current State: aws-microservices has 3 separate API Gateways, local-monolith has WAF only, unishop-monolith has no gateway, books-api has API Gateway with Cognito
- Proposed Solution: Unified Amazon API Gateway with path-based routing for all services. Consistent auth (Cognito), throttling, request validation, and monitoring. Agent-specific usage plans with higher rate limits.
- Benefits: Single entry point for agents, consistent security, simplified tool configuration, portfolio-level API analytics
- Effort: Medium
- Priority: High — aligned with API Gateway preference

### Observability Unification

- Current State: Only books-api has X-Ray tracing (OPS-Q1: 3/4). Others score 1/4. No service has structured logging.
- Proposed Solution: Deploy OpenTelemetry collector + X-Ray + CloudWatch Logs across all services. Shared dashboards for portfolio-level visibility. Agent-specific metrics (tool call success rate, response latency, token usage).
- Benefits: End-to-end tracing across agent → API Gateway → service → database, consistent log format for CloudWatch Log Insights
- Effort: Medium
- Priority: High

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + embedded service teams (20+ cross-cutting concerns detected — exceeds the 5-concern threshold for centralized platform team recommendation).

**Platform Team**:
- Responsibilities: Shared Cognito deployment, API Gateway management, EventBridge bus, observability stack, Bedrock Knowledge Base, agent orchestration framework, CI/CD templates, CDK construct library
- Skills Required: AWS CDK, Amazon Bedrock, Strands Agents SDK, API Gateway, Cognito, EventBridge, X-Ray/OpenTelemetry, CloudWatch

**Service Teams**:
- **unishop-monolith team**: Java/Spring Boot containerization, database migration, OpenAPI generation
- **aws-microservices team**: Node.js/TypeScript CI/CD, Lambda optimization, EventBridge patterns
- **local-monolith team**: PHP modernization, ECS migration, order management domain
- **books-api team**: TypeScript agent integration, RAG implementation, evaluation pipeline

### Skill Gaps

1. **Agent Development (Strands Agents, Bedrock)**: Required across all teams, currently absent across the entire portfolio. Critical for goal achievement.
2. **Containerization (Docker, ECS, Fargate)**: Required for unishop-monolith and local-monolith teams. local-monolith has Docker experience; unishop-monolith has none.
3. **Infrastructure as Code (CDK)**: Required for unishop-monolith team (zero IaC). aws-microservices and books-api teams have CDK experience.
4. **CI/CD (CodePipeline, CodeBuild)**: Required for 3 of 4 teams. books-api team has expertise to share.
5. **Observability (X-Ray, OpenTelemetry, CloudWatch)**: Required across all teams. books-api team has X-Ray experience.
6. **RAG / Vector Databases (Bedrock KB, OpenSearch)**: Required for platform team and all service teams. Not present anywhere.

### Training Recommendations

- **Phase 0 priority**: Amazon Bedrock Getting Started, Strands Agents SDK, ECS/Fargate fundamentals, CDK basics
- **Phase 1 priority**: CI/CD with CodePipeline, X-Ray tracing, structured logging, OpenAPI specification
- **Phase 2 priority**: RAG pipeline design, Step Functions, evaluation frameworks, cost optimization
- **Certification paths**: AWS Solutions Architect (platform team), AWS DevOps Engineer (service teams)

### External Support

- **AWS Professional Services or consulting partners** recommended for:
  - Phase 0 shared platform infrastructure (Cognito, API Gateway, Bedrock KB) — accelerate foundation work
  - Agent architecture design — Strands Agents SDK implementation patterns, multi-tool agent orchestration
  - Database migration (unishop-monolith MySQL → RDS) — mitigate data migration risk
  - Knowledge transfer — upskill all teams on agent development simultaneously
- Estimated engagement: 2-3 months for platform work, shorter engagements for individual service consultations

## Recommended Self-Paced Learning Materials

Based on portfolio-wide skill gaps identified in containerization, CI/CD, managed databases, DevOps practices, and AI/agent development:

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
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
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Optimizing Foundation Models — https://skillbuilder.aws/learn/CDYTAJCKGY/optimizing-foundation-models/PVR1FRGN1T
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Unauthenticated APIs exposed to agents (SEC-Q9: 3 services at 1/4) | High | High | Deploy Cognito in Phase 0. No agent deployment until auth is in place. |
| No rate limiting allows agent loops to overwhelm APIs (APP-Q8: all 4 at 1/4) | High | High | Add API Gateway throttling in Phase 0/1. Separate usage plans for agents vs humans. |
| Self-managed MySQL data loss (unishop-monolith INF-Q2: 1/4, no IaC) | High | Medium | Migrate to Amazon RDS with automated backups in Phase 1. |
| No testing infrastructure (OPS-Q10: 3 of 4 services at 1/4) | High | High | Establish test suites before agent tool deployment. API contract tests prevent breaking agent tools. |
| Circular dependency between aws-microservices and books-api | Medium | Medium | Define API contracts and event schemas in Phase 0. Add circuit breakers. |
| Java 8 EOL blocks agent framework adoption (unishop-monolith) | Medium | Medium | Build agent layer as separate Python/TypeScript service on ECS. Upgrade Java later. |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| 4 different programming languages create skill fragmentation | Medium | Medium | Platform team uses Python/TypeScript for shared agent service. Service teams maintain existing stacks. |
| No CI/CD in 3 services slows agent iteration velocity | High | Medium | CI/CD is Phase 0/1 priority. Use books-api pipeline as template. |
| Agent development skills absent across all teams | High | High | Phase 0 training on Bedrock + Strands Agents SDK. External support for initial implementation. |
| Scope creep from 4 simultaneous modernization tracks | Medium | Medium | Clear phase boundaries. P0/P1 prioritization. Platform team coordinates shared work. |

### Dependency Risks

- **aws-microservices ↔ books-api bidirectional dependency**: Creates deployment coupling. Changes to aws-microservices API could break books-api's sync queries. Changes to event schemas could break async processing. **Mitigation**: Versioned API contracts (Phase 0), circuit breakers (Phase 1), contract testing (Phase 2).
- **Monolith isolation (unishop-monolith, local-monolith)**: Low dependency risk. Both can be modernized independently. No cross-service impact.

### Single Points of Failure

- **unishop-monolith self-managed MySQL**: No automated failover, no IaC, no backups verifiable. Customer data at risk. **Mitigation**: Priority migration to RDS with automated backups and Multi-AZ in Phase 1.
- **No blast radius >= 50%**: All services are mostly independent. aws-microservices and books-api each affect 50% (themselves + the other), but this is manageable with circuit breakers.

### Risk Matrix

|  | **Low Impact** | **Medium Impact** | **High Impact** |
|--|---------------|------------------|----------------|
| **High Likelihood** | — | Self-managed MySQL EOL, No CI/CD (3 services) | No API authentication, No rate limiting, No testing, Agent skill gap |
| **Medium Likelihood** | — | Circular dependency, Language diversity, Scope creep | — |
| **Low Likelihood** | Isolated service blast radius | — | — |

## Service-by-Service Summary

### unishop-monolith

- **Overall Score**: 1.3 / 4.0 ❌
- **Repository**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-11
- **Category Scores**:
  - Infrastructure: 1.0 / 4.0 ❌
  - Application: 1.4 / 4.0 ❌
  - Data: 1.9 / 4.0 🟠
  - Security: 1.0 / 4.0 ❌
  - Operations: 1.0 / 4.0 ❌
- **Top Priorities**:
  1. APP-Q2 — No API Documentation (Score: 1/4)
  2. APP-Q13 — No AI/Agent Frameworks (Score: 1/4)
  3. DATA-Q1 — No Vector Database (Score: 1/4)
  4. DATA-Q3 — No RAG Implementation (Score: 1/4)
  5. SEC-Q7 — No Human Approval Workflows (Score: 1/4)
- **Dependencies**: None (isolated monolith)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native (High), Move to Containers (High), Move to Managed Databases (High), Move to Managed Analytics (Medium), Move to Modern DevOps (High), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Managed Databases (High), Move to Modern DevOps (High)
- **Modernization Phase**: Phase 1
- **Estimated Effort**: High

### aws-microservices

- **Overall Score**: 1.8 / 4.0 🟠
- **Repository**: ./services/aws-microservices
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-11
- **Category Scores**:
  - Infrastructure: 2.5 / 4.0 🟡
  - Application: 1.9 / 4.0 🟠
  - Data: 2.0 / 4.0 🟠
  - Security: 1.4 / 4.0 ❌
  - Operations: 1.0 / 4.0 ❌
- **Top Priorities**:
  1. APP-Q2 — No API Documentation (Score: 1/4)
  2. APP-Q13 — No AI/Agent Frameworks (Score: 1/4)
  3. DATA-Q1 — No Vector Database (Score: 1/4)
  4. DATA-Q3 — No RAG Implementation (Score: 1/4)
  5. SEC-Q9 — No API Authentication (Score: 1/4)
- **Dependencies**: None (upstream)
- **Depended On By**: books-api (sync REST queries + async EventBridge events)
- **Modernization Pathways**: Move to Cloud Native (Low), Move to Containers (Low), Move to Managed Databases (High), Move to Managed Analytics (High), Move to Modern DevOps (High), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Managed Databases (High), Move to Modern DevOps (High)
- **Modernization Phase**: Phase 1
- **Estimated Effort**: High

### local-monolith

- **Overall Score**: 1.5 / 4.0 🟠
- **Repository**: ./monolith
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-11
- **Category Scores**:
  - Infrastructure: 2.0 / 4.0 🟠
  - Application: 1.3 / 4.0 ❌
  - Data: 1.8 / 4.0 🟠
  - Security: 1.3 / 4.0 ❌
  - Operations: 1.0 / 4.0 ❌
- **Top Priorities**:
  1. APP-Q2 — No API Documentation (Score: 1/4)
  2. APP-Q13 — No AI/Agent Frameworks (Score: 1/4)
  3. DATA-Q1 — No Vector Database (Score: 1/4)
  4. DATA-Q3 — No RAG Implementation (Score: 1/4)
  5. SEC-Q7 — No Human Approval Workflows (Score: 1/4)
- **Dependencies**: None (isolated monolith)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native (High), Move to Containers (High), Move to Managed Databases (Medium), Move to Modern DevOps (High), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Managed Databases (High), Move to Modern DevOps (High)
- **Modernization Phase**: Phase 1
- **Estimated Effort**: High

### books-api

- **Overall Score**: 2.1 / 4.0 🟠
- **Repository**: ./services/books-api
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-11
- **Category Scores**:
  - Infrastructure: 2.7 / 4.0 🟡
  - Application: 1.9 / 4.0 🟠
  - Data: 2.0 / 4.0 🟠
  - Security: 2.1 / 4.0 🟠
  - Operations: 1.9 / 4.0 🟠
- **Top Priorities**:
  1. APP-Q2 — No API Documentation (Score: 1/4)
  2. APP-Q13 — No AI/Agent Frameworks (Score: 1/4)
  3. DATA-Q1 — No Vector Database (Score: 1/4)
  4. DATA-Q3 — No RAG Implementation (Score: 1/4)
  5. OPS-Q3 — No Automated Evaluations (Score: 1/4)
- **Dependencies**: aws-microservices (sync REST for product catalog data)
- **Depended On By**: aws-microservices (async EventBridge for catalog updates)
- **Modernization Pathways**: Move to Cloud Native (Medium), Move to Managed Analytics (Low), Move to Modern DevOps (Medium), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Modern DevOps (High)
- **Modernization Phase**: Phase 2
- **Estimated Effort**: Medium

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Repo Type | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------|-----------------|---------------|-------------|
| unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy | application | 2026-03-11 | 1.3 / 4.0 | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-assessment/MonoToMicroLegacy-agentic-readiness-report.md |
| aws-microservices | ./services/aws-microservices | application | 2026-03-11 | 1.8 / 4.0 | ./services/aws-microservices/agentic-readiness-assessment/aws-microservices-agentic-readiness-report.md |
| local-monolith | ./monolith | application | 2026-03-11 | 1.5 / 4.0 | ./monolith/agentic-readiness-assessment/monolith-agentic-readiness-report.md |
| books-api | ./services/books-api | application | 2026-03-11 | 2.1 / 4.0 | ./services/books-api/agentic-readiness-assessment/books-api-agentic-readiness-report.md |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)
- Portfolio scores: Arithmetic mean of individual service scores
- No N/A criteria in this portfolio (all services are application type)

---

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - Review this portfolio assessment with stakeholders and agree on Phase 0 priorities
   - Initiate MAP eligibility discussion with AWS account team
   - Begin Cognito User Pool design for shared authentication
   - Schedule team training on Amazon Bedrock and Strands Agents SDK

2. **Short-term (Month 1 — Phase 0)**:
   - Deploy shared Cognito User Pool and API Gateway
   - Provision Bedrock Knowledge Base with initial product documentation
   - Define API contracts between aws-microservices and books-api (resolve circular dependency)
   - Create CI/CD pipeline templates and CDK construct library
   - Deploy unified observability stack (CloudWatch + X-Ray)
   - Request EBA engagements for Move to AI and Move to Modern DevOps

3. **Medium-term (Months 1-3 — Phases 1-2)**:
   - Generate OpenAPI specs for all 4 services (highest-impact action for agent enablement)
   - Build and deploy 3 agent PoCs (one per P0 service)
   - Containerize monoliths on ECS Fargate
   - Establish CI/CD pipelines for all services
   - Complete RAG pipeline with Bedrock Knowledge Bases
   - Implement human approval workflows for high-risk agent actions
   - Integrate books-api with agent platform

4. **Long-term (Months 3-6+ — Phase 3)**:
   - Deploy production customer-facing support agent
   - Implement automated evaluation pipeline with golden datasets
   - Establish LLM cost tracking and optimization
   - Begin microservices decomposition for monoliths
   - Implement advanced observability with anomaly detection
   - Continuous agent quality improvement based on evaluation metrics
