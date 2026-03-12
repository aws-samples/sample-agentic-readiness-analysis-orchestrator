# Portfolio Agentic Readiness Assessment Report
**Portfolio**: ecommerce-platform-test
**Assessment Goal**: agentic-ai-enablement
**Goal Context**: Building customer-facing AI agents for support and order management
**Services Assessed**: 5
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

The ecommerce-platform-test portfolio of 5 services scores **1.67 / 4.0** overall, placing the entire portfolio in the "Needs Work" category for agentic AI enablement. No service is agent-ready today, and the weakest categories — Operations & Observability (1.20) and Identity, Security & Governance (1.46) — represent critical gaps that must be addressed before customer-facing AI agents for support and order management can be deployed safely. Three foundational blockers affect the majority of the portfolio: 3 of 5 services have no CI/CD pipeline at all, 4 of 5 services have no observability infrastructure, and all 5 services lack API rate limiting and abuse protection — conditions that would make agent deployment unreliable, unmonitorable, and unsafe.

The strongest signal is that all 5 services already return structured JSON API responses (4 of 5 score ≥ 3.5 on APP-Q5), providing an immediate agent tool surface. The aws-microservices service has a well-architected event-driven pattern (Lambda, DynamoDB, EventBridge, SQS) that aligns directly with agent tool design, and books-api already has a fully automated CI/CD pipeline with canary deployments — a reference implementation for the rest of the portfolio. The recommended approach is a 6-month phased roadmap starting with shared infrastructure foundations (observability, CI/CD templates, authentication) in Month 0–1, followed by agent quick wins leveraging existing JSON APIs in Months 1–2, agent foundations (vector DB, RAG, evaluation pipelines) in Months 2–4, and full-scale agent deployment with optimization in Months 4–6+.

A circular dependency between aws-microservices and books-api (async via EventBridge + sync via REST) must be resolved in Phase 0 to enable independent modernization. Three P0 services (unishop-monolith, aws-microservices, local-monolith) require the most urgent attention due to their low scores and business criticality.

### Portfolio Readiness Score: 1.67 / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | 2.18 / 4.0 | ✅ 0 services, 🟡 3 services, 🟠 2 services, ❌ 0 services | 🟠 |
| Application Architecture | 1.74 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 3 services, ❌ 2 services | 🟠 |
| Data Foundations | 1.90 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 5 services, ❌ 0 services | 🟠 |
| Identity, Security & Governance | 1.46 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 2 services, ❌ 3 services | ❌ |
| Operations & Observability | 1.20 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 service, ❌ 4 services | ❌ |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): 0 services (0%)
- 🟡 Partial (2.5-3.4): 0 services (0%)
- 🟠 Needs Work (1.5-2.4): 4 services (80%) — aws-microservices (1.7), local-monolith (1.5), books-api (2.0), eks-saas-gitops (1.8)
- ❌ Not Ready (< 1.5): 1 service (20%) — unishop-monolith (1.33)

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | 5 | 3 P0 (critical), 2 P1 (important) |
| Average Readiness Score | 1.67 / 4.0 | All services below "Partial" threshold (2.5) |
| Services Ready for Agents | 0 (0%) | No service meets the 3.5 agent-ready threshold |
| Critical Dependencies | 1 circular | aws-microservices ↔ books-api must be resolved Phase 0 |
| Shared Infrastructure Gaps | 3 Tier-1 blockers | CI/CD, observability, rate limiting absent portfolio-wide |
| Estimated Modernization Effort | High | Extensive cross-cutting and service-level work required |
| Expected Timeline | 6 months | 4 phases with parallel execution tracks |

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- Java 8 (Spring Boot 2.1): 1 service (20%) — unishop-monolith
- TypeScript/Node.js: 2 services (40%) — aws-microservices, books-api
- PHP: 1 service (20%) — local-monolith
- Python: 1 service (20%) — eks-saas-gitops

**Database Engines:**
- DynamoDB (managed): 3 services (60%) — aws-microservices, books-api, eks-saas-gitops
- MySQL (self-managed on EC2): 1 service (20%) — unishop-monolith
- RDS MySQL (managed): 1 service (20%) — local-monolith

**Compute Patterns:**
- Serverless (Lambda): 2 services (40%) — aws-microservices, books-api
- EC2 (bare metal): 1 service (20%) — unishop-monolith
- App Runner: 1 service (20%) — local-monolith
- EKS (Kubernetes): 1 service (20%) — eks-saas-gitops

**Infrastructure as Code:**
- CDK: 2 services (40%) — aws-microservices, books-api
- CloudFormation: 1 service (20%) — local-monolith
- Terraform: 1 service (20%) — eks-saas-gitops
- None: 1 service (20%) — unishop-monolith

**Deployment Maturity:**
- Full CI/CD with canary: 1 service (20%) — books-api
- GitOps CI/CD (no test gates): 1 service (20%) — eks-saas-gitops
- Manual deployment only: 3 services (60%) — unishop-monolith, aws-microservices, local-monolith

### Common Strengths

1. **Structured JSON API Responses (APP-Q5)**: 4 of 5 services score ≥ 3.5 — agents can immediately parse and use API responses as tool outputs without transformation
2. **No Stored Procedures (DATA-Q11)**: All 5 services score 4/4 — clean database schemas with no vendor lock-in through stored procedures, simplifying data layer modernization
3. **Managed Database Adoption**: 4 of 5 services use fully managed databases (DynamoDB or RDS), reducing operational burden
4. **Event-Driven Patterns**: aws-microservices uses EventBridge + SQS; eks-saas-gitops uses SQS + Argo Events — proven async patterns that align with agent workflow orchestration
5. **Modern DB Engine Versions (DATA-Q10)**: 3 of 5 services score ≥ 3.5 on database engine currency

### Common Gaps

1. **No AI/Agent Frameworks (APP-Q13)**: All 5 services score 1/4 — zero agent integration exists anywhere in the portfolio
2. **No API Documentation (APP-Q2)**: All 5 services score 1/4 — no OpenAPI specs for agent tool discovery
3. **No Observability (OPS-Q1)**: 4 of 5 services score 1/4 — no distributed tracing, making agent behavior invisible
4. **No CI/CD (INF-Q6)**: 3 of 5 services have no CI/CD pipeline at all — cannot safely deploy agent changes
5. **No Rate Limiting (APP-Q8)**: All 5 services score 1/4 — APIs are unprotected from agent-generated traffic spikes
6. **No Vector Database (DATA-Q1)**: All 5 services score 1/4 — no semantic search capability for RAG
7. **No RAG Pipeline (DATA-Q3)**: All 5 services score 1/4 — no knowledge retrieval for grounded agent responses

## Service Dependency Map

### High-Level Architecture

The ecommerce-platform-test portfolio consists of 5 services with two distinct clusters: a connected pair (aws-microservices ↔ books-api) with bidirectional dependencies, and three isolated services (unishop-monolith, local-monolith, eks-saas-gitops) with no inter-portfolio dependencies. The connected pair forms a circular dependency that must be resolved before independent modernization can proceed.

### Service Dependency Matrix

| Service | Depends On | Depended On By | Coupling Score | Priority |
|---------|------------|----------------|----------------|----------|
| unishop-monolith | None | None | None (isolated) | P0 |
| aws-microservices | books-api (SYNC: REST) | books-api (ASYNC: EventBridge) | Medium | P0 |
| local-monolith | None | None | None (isolated) | P0 |
| books-api | aws-microservices (ASYNC: EventBridge) | aws-microservices (SYNC: REST) | Medium | P1 |
| eks-saas-gitops | None | None | None (isolated) | P1 |

**Coupling Score Definitions:**
- **High**: Synchronous dependency + shared database OR 3+ dependency types
- **Medium**: Synchronous dependency OR 2 dependency types
- **Low**: Asynchronous only OR shared infrastructure only

**Priority Definitions:**
- **P0**: Critical path services that block others or have lowest readiness scores
- **P1**: Important services with moderate dependencies
- **P2**: Leaf services with minimal dependencies

### Critical Path Analysis

1. **Circular Dependency (Phase 0 Resolution Required)**:
   - aws-microservices → books-api: ASYNC (ordering flow triggers book catalog updates via EventBridge events)
   - books-api → aws-microservices: SYNC (Books API queries product microservice for catalog data via REST)
   - **Resolution**: Define clear API contracts and event schemas. Consider replacing the synchronous REST dependency with EventBridge-based async communication to break the cycle.

2. **Foundation Services** (modernize first due to business criticality):
   - unishop-monolith: P0, legacy e-commerce core, lowest score (1.33)
   - aws-microservices: P0, event-driven microservices backbone
   - local-monolith: P0, containerized monolith for order management

3. **Independent Services** (can be parallelized):
   - unishop-monolith, local-monolith, eks-saas-gitops — no inter-portfolio dependencies, can be modernized concurrently

### Integration Points

**Synchronous Integrations:**
- books-api → aws-microservices: REST API call for product catalog data queries

**Asynchronous Integrations:**
- aws-microservices → books-api: EventBridge events for ordering flow → book catalog updates

**Shared Infrastructure:**
- No shared databases detected between services
- No shared API gateways (each service has its own)
- No shared authentication system (all services lack centralized auth — Tier 2 concern)

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are classified into four tiers based on severity and relationship to the portfolio's assessment goal (`agentic-ai-enablement`).

### 🚨 Foundational Blockers

> These gaps block all modernization efforts, not just agentic-ai-enablement.
> Address these first — nothing else matters until these are resolved.

1. **INF-Q6: CI/CD Pipeline** — 3 of 5 services score < 2
   - **Impact**: Without CI/CD, code changes cannot be safely deployed. Agent framework integration, observability instrumentation, and security fixes all require automated deployment pipelines. Manual deployments are error-prone and block iterative development at the speed agents require.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4)
   - **Recommendation**: Deploy shared CI/CD pipeline templates (GitHub Actions or similar) for all three services. Use books-api's CodePipeline as the reference implementation. Standardize on build → test → deploy stages with automated rollback.

2. **OPS-Q1: Distributed Tracing & Observability** — 4 of 5 services score < 2
   - **Impact**: Without observability, agent behavior is invisible. You cannot detect agent failures, reasoning loops, latency spikes, or tool errors. Deploying customer-facing agents without tracing is operationally dangerous — issues will only be discovered when customers complain.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), eks-saas-gitops (1/4)
   - **Recommendation**: Deploy a unified observability stack across the portfolio: OpenTelemetry auto-instrumentation with AWS X-Ray as the tracing backend, structured JSON logging with correlation IDs, and CloudWatch dashboards for each service. Use books-api (score 3/4) as the reference pattern.

3. **APP-Q8 + SEC-Q5: API Rate Limiting & Abuse Protection** — 5 of 5 services score < 2 on both criteria
   - **Impact**: APIs are completely unprotected from traffic spikes. AI agents can generate request volumes far exceeding human usage patterns — a misconfigured agent loop could overwhelm any service. Without rate limiting, there is no protection against accidental or malicious abuse.
   - **Affected services**: All 5 services score 1/4 on both APP-Q8 and SEC-Q5
   - **Recommendation**: Deploy API Gateway with rate limiting and throttling for all services. Configure per-client and per-agent rate limits. Implement WAF rules for abuse detection. This is a shared infrastructure investment that benefits the entire portfolio.

### ⚠️ Prerequisites for agentic-ai-enablement

> These gaps specifically block your path to agentic-ai-enablement.
> They aren't the goal itself, but you can't get there without them.

1. **APP-Q2: API Documentation / OpenAPI Specs** — 5 of 5 services score < 3
   - **Impact on goal**: AI agents discover and invoke service capabilities through machine-readable API specifications (OpenAPI/Swagger). Without OpenAPI specs, agents cannot programmatically understand what endpoints are available, what parameters they accept, or what responses they return. This is the single biggest prerequisite for agent tool discovery.
   - **Affected services**: All 5 services score 1/4
   - **Recommendation**: Generate OpenAPI specifications for all services. For Spring Boot (unishop-monolith): add `springdoc-openapi-ui`. For Lambda/API Gateway (aws-microservices, books-api): export API Gateway specs. For PHP (local-monolith): use `swagger-php` annotations. For Python/EKS (eks-saas-gitops): use FastAPI or `flasgger`. Establish portfolio-wide OpenAPI documentation standards.

2. **SEC-Q3: Identity Propagation** — 5 of 5 services score < 3
   - **Impact on goal**: Agents act on behalf of users. Without identity propagation (JWT tokens, OAuth2 scopes, user context in headers), an agent cannot perform actions scoped to a specific customer — it would either have no access or have overly broad access. Customer-facing support agents MUST propagate the customer's identity to backend services.
   - **Affected services**: unishop-monolith (2/4), aws-microservices (1/4), local-monolith (1/4), books-api (2/4), eks-saas-gitops (1/4)
   - **Recommendation**: Deploy Amazon Cognito as the shared identity provider across the portfolio. Implement JWT token propagation through all service calls. Define OAuth2 scopes for agent actions (read-only, write with approval, admin).

### 🎯 Goal Deliverables — What You're Here to Build

> These are the capabilities your agentic-ai-enablement initiative will deliver.
> Low scores here confirm the need for the initiative, not additional blockers.
> Your individual assessment reports detail the current state and roadmap for each.

1. **APP-Q13: AI/Agent Framework Integration** — 5 of 5 services score < 3
   - **Current state**: Zero AI/agent frameworks exist anywhere in the portfolio. No Bedrock SDK, no Strands Agents SDK, no LangChain, no agent orchestration of any kind.
   - **Affected services**: All 5 services score 1/4
   - **Roadmap reference**: Phase 1 (proof-of-concept agents), Phase 2 (production agent frameworks), Phase 3 (multi-agent orchestration)

2. **DATA-Q1: Vector Database for Semantic Search** — 5 of 5 services score < 3
   - **Current state**: No vector database deployed anywhere. No OpenSearch, no pgvector, no Bedrock Knowledge Bases.
   - **Affected services**: All 5 services score 1/4
   - **Roadmap reference**: Phase 2 (deploy shared vector database infrastructure)

3. **DATA-Q2: Vector DB Management (Managed vs Self-Hosted)** — 5 of 5 services score < 3
   - **Current state**: No vector database exists to manage.
   - **Affected services**: All 5 services score 1/4
   - **Roadmap reference**: Phase 2 (deploy managed vector DB — Bedrock Knowledge Bases or OpenSearch Serverless)

4. **DATA-Q3: RAG Pipeline** — 5 of 5 services score < 3
   - **Current state**: No RAG implementation exists. No embeddings, no chunking, no semantic search pipelines. Customer-facing agents cannot ground their responses in your actual product catalog, order data, or support documentation.
   - **Affected services**: All 5 services score 1/4
   - **Roadmap reference**: Phase 2 (build RAG pipelines for product knowledge and support documentation)

5. **SEC-Q7: Human Approval Workflows** — 5 of 5 services score < 3
   - **Current state**: No human-in-the-loop approval workflows for high-risk agent actions. Agents could execute refunds, cancel orders, or modify customer data without human oversight.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (2/4), books-api (2/4), eks-saas-gitops (1/4)
   - **Roadmap reference**: Phase 3 (Step Functions approval workflows for high-risk agent actions)

6. **OPS-Q3: Automated Agent Evaluation Framework** — 5 of 5 services score < 3
   - **Current state**: No evaluation framework for agent quality. No golden datasets, no automated eval pipelines, no regression testing for agent behavior.
   - **Affected services**: All 5 services score 1/4
   - **Roadmap reference**: Phase 2 (build eval pipeline), Phase 3 (integrate into CI/CD)

7. **OPS-Q6: LLM Cost Tracking** — 5 of 5 services score < 3
   - **Current state**: No LLM cost tracking infrastructure. When agents are deployed, there will be no visibility into per-request, per-user, or per-workflow token costs.
   - **Affected services**: All 5 services score 1/4
   - **Roadmap reference**: Phase 3 (per-request cost attribution with CloudWatch custom metrics)

### 💡 General Improvement Opportunities

> These gaps are important but do not directly block agentic-ai-enablement.
> Address them as capacity allows or in parallel with goal work.

1. **APP-Q3: Asynchronous Communication Patterns** — 3 of 5 services score < 3
   - **Impact**: Services rely heavily on synchronous REST calls. Async patterns (EventBridge, SQS, SNS) improve resilience and are better suited for agent workflows that may have variable latency.
   - **Affected services**: unishop-monolith (1/4), local-monolith (1/4), books-api (1/4)
   - **Recommendation**: Introduce EventBridge for cross-service communication. Use aws-microservices' event-driven pattern as the reference architecture.

2. **SEC-Q1: API Authentication** — 4 of 5 services score < 3
   - **Impact**: Most APIs have no authentication. Agents accessing unauthenticated APIs cannot enforce authorization policies.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), eks-saas-gitops (1/4)
   - **Recommendation**: Deploy Cognito-backed API Gateway authorizers across the portfolio.

3. **OPS-Q9: Deployment Strategy** — 3 of 5 services score < 3
   - **Impact**: Direct-to-production deployments without canary or blue/green strategies make agent deployments risky.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4)
   - **Recommendation**: Implement canary deployments using CodeDeploy (ECS services) or Flagger (EKS services).

4. **OPS-Q10: Integration Testing** — 4 of 5 services score < 3
   - **Impact**: No automated tests to catch regressions in agent tool APIs. API changes can silently break agent integrations.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), eks-saas-gitops (1/4)
   - **Recommendation**: Build integration test suites for all API endpoints. Add agent-specific integration tests that validate tool invocations end-to-end.

5. **SEC-Q4: Secrets Management** — 3 of 5 services score < 3
   - **Impact**: Hardcoded credentials in some services create security risks, especially when agents access multiple services.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (2/4)
   - **Recommendation**: Migrate all secrets to AWS Secrets Manager or SSM Parameter Store with automatic rotation.

### Per-Category Analysis

### Infrastructure & Platform

**Portfolio Score: 2.18 / 4.0**

The Infrastructure & Platform category shows the widest variance across the portfolio. eks-saas-gitops (2.8) and books-api (2.7) demonstrate strong IaC and managed compute patterns, while unishop-monolith (1.1) runs on bare EC2 with no IaC at all. The key patterns: 4 of 5 services use IaC (CDK, CloudFormation, or Terraform), but only 2 of 5 have CI/CD pipelines. The portfolio would benefit from standardizing on Terraform (per stated preferences) and deploying shared CI/CD pipeline templates.

### Application Architecture

**Portfolio Score: 1.74 / 4.0**

Application Architecture is the second-weakest category. All 5 services lack API documentation (APP-Q2: 1/4), the most critical prerequisite for agent tool discovery. Two services are monoliths (unishop-monolith, local-monolith) requiring decomposition, while aws-microservices and eks-saas-gitops already have clean microservices boundaries. The universal strength is structured JSON responses (APP-Q5: 4 of 5 services ≥ 3/4), meaning agents can immediately parse API outputs.

### Data Foundations

**Portfolio Score: 1.90 / 4.0**

Data Foundations scores are dragged down by the complete absence of AI-specific data infrastructure: no vector databases (DATA-Q1), no RAG pipelines (DATA-Q3), and no semantic search (DATA-Q2) across the entire portfolio. The bright side: all services have clean database schemas with no stored procedures (DATA-Q11: 5/5 score 4/4), and 4 of 5 use managed databases. This clean data layer will simplify AI integration.

### Identity, Security & Governance

**Portfolio Score: 1.46 / 4.0**

Security is critically weak. 4 of 5 services have no API authentication (SEC-Q1), all 5 lack identity propagation (SEC-Q3 < 3), and all 5 have no rate limiting (APP-Q8 + SEC-Q5). This is especially dangerous for agent deployments: without authentication and identity propagation, agents cannot securely act on behalf of users. The local-monolith has some WAF protection (SEC-Q2: 3/4) that could serve as a reference pattern.

### Operations & Observability

**Portfolio Score: 1.20 / 4.0**

Operations is the weakest category by far. 4 of 5 services have zero observability (OPS-Q1: 1/4), all 5 lack agent evaluation frameworks (OPS-Q3: 1/4), and 4 of 5 have no integration tests (OPS-Q10 < 2). books-api stands out with a 1.8 score driven by its CI/CD pipeline (OPS-Q9: 4/4, canary deployments) and partial test coverage (OPS-Q10: 3/4). The platform team's first priority should be deploying shared observability infrastructure across all services.

## Portfolio Modernization Roadmap

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: aws-microservices (Phase 1) before books-api (Phase 2) due to circular dependency resolution
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Isolated services (unishop-monolith, local-monolith, eks-saas-gitops) can be modernized concurrently
5. **Quick Wins**: Early agent wins build momentum and demonstrate value to stakeholders
6. **Goal Alignment**: Within each phase, agentic-ai-enablement priority activities are listed first

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities and organizational readiness

**Shared Infrastructure:**
- Deploy unified observability stack (OpenTelemetry + X-Ray + CloudWatch) — benefits all 5 services
- Deploy shared Amazon Cognito user pool for portfolio-wide authentication — benefits all 5 services
- Deploy shared API Gateway patterns with rate limiting and WAF — benefits all 5 services
- Establish portfolio-wide OpenAPI documentation standards and tooling

**Circular Dependency Resolution:**
- Define clear API contracts between aws-microservices and books-api
- Establish event schema registry for EventBridge events
- Consider replacing books-api → aws-microservices synchronous REST call with async EventBridge pattern

**Platform Capabilities:**
- Create CI/CD pipeline templates (GitHub Actions) for unishop-monolith, aws-microservices, local-monolith
- Standardize Terraform modules for common infrastructure patterns
- Set up shared ECR registries for container images

**Organizational Enablers:**
- Training: AI/Agent frameworks (Module 7), Modern DevOps (Module 6), Containers (Module 3)
- Tooling: Set up Amazon Bedrock access, provision development sandbox
- Standards: Define agent tool interface standards, API response format conventions

**Expected Outcomes:**
- All services have observability, authentication, and rate limiting
- CI/CD pipelines operational for all services
- Circular dependency between aws-microservices and books-api resolved
- Teams trained on agent frameworks and DevOps practices

**Estimated Effort**: High

### Phase 1 — Agent Quick Wins (Mo 1–2)

**Objective**: Modernize P0 foundation services and deploy first agent proof-of-concepts. Goal-priority activities listed first.

**Services in Scope:**

1. **aws-microservices** (P0, Score: 1.7/4.0)
   - Current State: Event-driven microservices (Product, Basket, Ordering) with Lambda, DynamoDB, EventBridge, SQS. Strong architecture but no CI/CD, no observability, no auth, no API docs.
   - Target State: OpenAPI-documented APIs with CI/CD, X-Ray tracing, Cognito auth, and proof-of-concept agent invoking Product/Basket/Order tools.
   - Key Activities (goal-priority first):
     - Generate OpenAPI specs for all 3 API Gateways (agent tool discovery prerequisite)
     - Deploy proof-of-concept agent Lambda using Strands Agents SDK with Product/Basket/Order tools
     - Set up GitHub Actions CI/CD pipeline (build → test → deploy)
     - Enable X-Ray tracing on all Lambda functions
     - Add Cognito authorizer to API Gateway
   - Dependencies: Phase 0 (shared Cognito, observability stack)
   - Blocks: books-api (Phase 2 — circular dependency)
   - Estimated Effort: Medium

2. **unishop-monolith** (P0, Score: 1.33/4.0)
   - Current State: Java 8 Spring Boot monolith on raw EC2 with self-managed MySQL. No IaC, no CI/CD, no auth, hardcoded credentials.
   - Target State: Containerized on ECS, Terraform IaC, CI/CD pipeline, RDS MySQL, OpenAPI-documented APIs, secrets in Secrets Manager.
   - Key Activities (goal-priority first):
     - Add `springdoc-openapi-ui` to auto-generate OpenAPI specs (agent tool discovery)
     - Create Dockerfile and push to ECR
     - Create Terraform project for VPC, ECS, RDS, ALB
     - Set up GitHub Actions CI/CD pipeline
     - Migrate MySQL to RDS with Multi-AZ
     - Move hardcoded credentials to Secrets Manager
   - Dependencies: None (isolated service)
   - Blocks: None
   - Estimated Effort: High

3. **local-monolith** (P0, Score: 1.5/4.0)
   - Current State: PHP monolith on App Runner with RDS MySQL. Has Dockerfile and CloudFormation but no CI/CD, no observability.
   - Target State: Migrated to ECS (per preference), CI/CD pipeline, OpenAPI-documented APIs, agent prototype for order management.
   - Key Activities (goal-priority first):
     - Generate OpenAPI spec using `swagger-php` annotations (agent tool discovery)
     - Deploy agent prototype for customer order lookup using existing JSON APIs
     - Migrate from App Runner to ECS with Terraform
     - Set up GitHub Actions CI/CD pipeline
     - Add OpenTelemetry instrumentation
   - Dependencies: None (isolated service)
   - Blocks: None
   - Estimated Effort: High

**Expected Outcomes:**
- All P0 services have CI/CD, observability, and OpenAPI specs
- First agent proof-of-concepts demonstrate value with customer support use cases
- Reference patterns established for Phase 2 services

**Estimated Effort**: High

### Phase 2 — Agent Foundations (Mo 2–4)

**Objective**: Build agent infrastructure and modernize Phase 1-dependent services. Goal-priority activities listed first.

**Services in Scope:**

1. **books-api** (P1, Score: 2.0/4.0)
   - Current State: Serverless (Lambda, DynamoDB, API Gateway) with full CI/CD and canary deployments. Strongest infrastructure in portfolio.
   - Target State: Agent-integrated book catalog with RAG, vector search, and evaluation pipeline.
   - Key Activities (goal-priority first):
     - Add agent framework (Strands Agents SDK or LangChain.js) to wrap GET/POST /books as agent tools
     - Deploy Bedrock Knowledge Base with book catalog embeddings
     - Build agent evaluation pipeline with golden datasets
     - Generate OpenAPI spec (export from API Gateway)
     - Add Cognito authorizer
   - Dependencies: aws-microservices (Phase 1 — circular dependency resolved)
   - Blocks: None
   - Estimated Effort: Medium

2. **eks-saas-gitops** (P1, Score: 1.8/4.0)
   - Current State: EKS with Terraform IaC, GitOps via Flux CD, SQS messaging, DynamoDB per-tenant. No observability, no API auth, no tests.
   - Target State: Observable, authenticated, agent-integrated SaaS platform with per-tenant agent capabilities.
   - Key Activities (goal-priority first):
     - Deploy agent-service microservice using Strands Agents SDK on EKS
     - Wrap producer/consumer/payments APIs as agent tools
     - Deploy Bedrock Knowledge Base for SaaS documentation RAG
     - Add OpenTelemetry with ADOT collector for distributed tracing
     - Implement API authentication (Cognito or EKS-native OIDC)
     - Add pytest integration tests with test gates in Gitea CI
     - Implement Flagger for canary deployments
   - Dependencies: None (isolated service)
   - Blocks: None
   - Estimated Effort: Medium

**Cross-Service Activities:**
- Deploy shared Bedrock Knowledge Base infrastructure with OpenSearch Serverless
- Build portfolio-wide RAG pipeline indexing product catalogs, order data, and support documentation
- Deploy shared vector database for semantic search across all services
- Begin agent evaluation framework standardization across teams

**Expected Outcomes:**
- All 5 services have agent integration (at minimum proof-of-concept)
- RAG pipelines operational for product knowledge and support documentation
- Vector search infrastructure deployed and shared across services

**Estimated Effort**: High

### Phase 3 — Agent Scale & Optimization (Mo 4–6+)

**Objective**: Production-grade agent deployment, multi-agent orchestration, and advanced capabilities. Goal-priority activities listed first.

**Activities:**
- Deploy production customer-facing agents across all services with full observability
- Build multi-agent orchestration for end-to-end customer support workflows spanning multiple services
- Implement human approval workflows (Step Functions) for high-risk agent actions (refunds, order cancellations, data modifications)
- Deploy agent evaluation pipelines in CI/CD — no agent changes deployed without passing eval suite
- Implement LLM cost tracking with per-user, per-workflow, per-tenant attribution
- Begin monolith decomposition (unishop-monolith → microservices, local-monolith → domain services) to create cleaner agent tool boundaries
- Expand event-driven architecture to replace remaining synchronous dependencies
- Define and enforce SLOs for all services and agent capabilities
- Implement anomaly detection for agent behavioral drift

**Expected Outcomes:**
- Customer-facing AI agents for support and order management in production
- Multi-agent orchestration handling end-to-end customer journeys
- Complete observability across all agent interactions
- LLM cost visibility and optimization

**Estimated Effort**: High

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6 months (with 3 parallel tracks: P0 isolated services, P0-P1 dependency chain, cross-cutting infrastructure)

## AWS Modernization Pathways

Based on the portfolio-wide assessment findings, the following AWS Modernization Pathways have been identified for each service. The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach — a customer portfolio may be divided into multiple pathways depending on workloads and priorities, and these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 2 services | 40% | Medium | High |
| Move to Containers | 2 services | 40% | Medium | Medium |
| Move to Open Source | 0 services | 0% | Low | — |
| Move to Managed Databases | 1 service | 20% | Low | Medium |
| Move to Managed Analytics | 0 services | 0% | Low | — |
| Move to Modern DevOps | 4 services | 80% | High | High |
| Move to AI | 5 services | 100% | High | High |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| unishop-monolith | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| aws-microservices | — | — | — | — | — | ✅ | ✅ |
| local-monolith | ✅ | ✅ | — | — | — | ✅ | ✅ |
| books-api | — | — | — | — | — | — | ✅ |
| eks-saas-gitops | — | — | — | — | — | ✅ | ✅ |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing a single at-a-glance view of pathway coverage across the portfolio. Each repo appears in exactly one column per pathway row. Goal Alignment is based on the portfolio-level goal (`agentic-ai-enablement`).

| Pathway | Triggered | Not Triggered | Not Applicable | Goal Alignment |
|---------|-----------|---------------|----------------|---------------|
| Move to Cloud Native | unishop-monolith, local-monolith | aws-microservices, books-api, eks-saas-gitops | — | Medium |
| Move to Containers | unishop-monolith, local-monolith | aws-microservices, books-api, eks-saas-gitops | — | Medium |
| Move to Open Source | — | unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops | — | Low |
| Move to Managed Databases | unishop-monolith | aws-microservices, local-monolith, books-api, eks-saas-gitops | — | High |
| Move to Managed Analytics | — | unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops | — | Low |
| Move to Modern DevOps | unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops | books-api | — | High |
| Move to AI | unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops | — | — | High |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native for the monoliths (containerize unishop-monolith and local-monolith before decomposing them)
- Move to Modern DevOps enables faster and safer execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases (unishop-monolith: MySQL EC2 → RDS) should precede Move to AI for that service (stable data backend needed)

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps (4 services) — start immediately, benefits all other pathways
- **Track 2**: Move to AI (5 services) — can run in parallel with DevOps, leverages existing JSON APIs
- **Track 3**: Move to Containers + Move to Cloud Native (2 monoliths) — sequential per-service, parallel across services

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops (4 total)
- **Portfolio Priority**: High (80% of portfolio triggered, High Goal Alignment)
- **Common Trigger Criteria**:
  - INF-Q6 score < 3: affects 3 services (no CI/CD at all)
  - OPS-Q1 score < 3: affects 4 services (no observability)
  - OPS-Q9 score < 3: affects 3 services (no deployment strategy)
  - OPS-Q10 score < 3: affects 4 services (no integration testing)
- **Representative AWS Services**: GitHub Actions, CodePipeline, CodeDeploy, X-Ray, CloudWatch, OpenTelemetry
- **Key Activities**:
  1. Portfolio-level: Create shared CI/CD pipeline templates and Terraform modules
  2. Per-service: Implement CI/CD, tracing, testing, and canary deployments
- **Cross-Service Synergies**: Shared pipeline templates reduce per-service setup time; unified observability stack provides portfolio-wide visibility
- **Estimated Effort**: High across 4 services
- **Roadmap Phase Alignment**: Phase 0 (shared templates), Phase 1 (per-service implementation)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops (5 total)
- **Portfolio Priority**: High (100% of portfolio triggered, High Goal Alignment — this IS the portfolio's goal)
- **Common Trigger Criteria**:
  - APP-Q13 score < 3: affects 5 services (no AI/agent frameworks)
  - DATA-Q1 score < 3: affects 5 services (no vector database)
  - DATA-Q3 score < 3: affects 5 services (no RAG pipeline)
  - OPS-Q3 score < 3: affects 5 services (no eval framework)
  - OPS-Q6 score < 3: affects 5 services (no LLM cost tracking)
- **Representative AWS Services**: Amazon Bedrock, Bedrock Knowledge Bases, OpenSearch Serverless, Strands Agents SDK, Step Functions, CloudWatch
- **Key Activities**:
  1. Portfolio-level: Deploy shared Bedrock Knowledge Bases, vector DB, and eval infrastructure
  2. Per-service: Integrate agent frameworks, define tool interfaces, build service-specific RAG pipelines
- **Cross-Service Synergies**: Shared vector DB and Knowledge Base infrastructure; portfolio-wide eval datasets; multi-agent orchestration spanning services
- **Estimated Effort**: High across 5 services
- **Roadmap Phase Alignment**: Phase 1 (quick wins), Phase 2 (foundations), Phase 3 (scale)
- **Relevant Learning Materials**: Module 7 — Move to AI

#### Move to Cloud Native

- **Services Affected**: unishop-monolith, local-monolith (2 total)
- **Portfolio Priority**: Medium (40% of portfolio triggered)
- **Common Trigger Criteria**:
  - APP-Q4 < 4: both are monoliths requiring decomposition
  - APP-Q3 < 3: both lack async communication patterns
- **Representative AWS Services**: Lambda, API Gateway, Step Functions, EventBridge, ECS
- **Key Activities**: Monolith decomposition using Strangler Fig pattern, service extraction by business domain
- **Estimated Effort**: High across 2 services
- **Roadmap Phase Alignment**: Phase 3 (after containerization and CI/CD)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Containers

- **Services Affected**: unishop-monolith, local-monolith (2 total)
- **Portfolio Priority**: Medium (40% of portfolio triggered)
- **Common Trigger Criteria**:
  - INF-Q1 < 3: unishop-monolith on raw EC2, local-monolith on App Runner (not ECS/EKS per preference)
- **Representative AWS Services**: ECS, Fargate, ECR, ALB
- **Key Activities**: Containerize applications, deploy to ECS with Terraform, Helm charts per preference
- **Estimated Effort**: Medium across 2 services
- **Roadmap Phase Alignment**: Phase 1 (containerization before decomposition)
- **Relevant Learning Materials**: Module 3 — Move to Containers

#### Move to Managed Databases

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Low (20% of portfolio, but High Goal Alignment)
- **Common Trigger Criteria**:
  - INF-Q2: 2/4 — self-managed MySQL on EC2
- **Representative AWS Services**: RDS MySQL, Aurora MySQL
- **Key Activities**: Migrate self-managed MySQL to RDS MySQL with Multi-AZ, encryption at rest
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (database migration alongside containerization)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Example: Parallel Pathway Execution for a Single Service

**unishop-monolith** simultaneously pursues 5 pathways:
- **Move to Containers**: Containerize Java Spring Boot app → ECS/Fargate (Phase 1)
- **Move to Managed Databases**: Migrate MySQL EC2 → RDS MySQL (Phase 1)
- **Move to Modern DevOps**: Terraform IaC + GitHub Actions CI/CD + X-Ray tracing (Phase 0-1)
- **Move to Cloud Native**: Decompose monolith into microservices — Strangler Fig (Phase 3)
- **Move to AI**: Agent framework integration, OpenAPI docs, RAG pipeline (Phase 1-3)

## Portfolio Quick Agent Wins

Across the portfolio, these agent opportunities are immediately available based on existing capabilities found in individual assessments. Framed around the portfolio goal of building customer-facing AI agents for support and order management:

**API-Aware Customer Support Agents** (5 repos: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops)
- All 5 services return structured JSON responses that agents can immediately parse as tool outputs. A customer support agent can be deployed today using manual tool definitions (without OpenAPI) to invoke existing endpoints for product search, order lookup, basket management, and book catalog queries. This is the fastest path to demonstrating agent value.

**Natural Language Data Query Agents** (3 repos: unishop-monolith, aws-microservices, eks-saas-gitops)
- Services with clean database schemas (MySQL tables with clear naming, DynamoDB with documented partition/sort keys) enable text-to-SQL/DynamoDB query agents. A customer can ask "What's in my basket?" or "Show me orders from last week" and get accurate results from the existing data layer.

**Product Knowledge & Recommendation Agents** (3 repos: unishop-monolith, aws-microservices, local-monolith)
- Product catalog data (unishop-monolith: unicorn products, aws-microservices: e-commerce products, local-monolith: product inventory) can power recommendation agents. Customers asking "Do you have running shoes under $100?" get accurate, grounded responses from actual product data.

**DevOps & Deployment Agents** (2 repos: books-api, eks-saas-gitops)
- books-api's CodePipeline and eks-saas-gitops' Flux CD/ArgoCD provide programmable deployment interfaces that DevOps agents can invoke for deployment management, status checks, and rollback operations.

**Documentation RAG Agents** (3 repos: aws-microservices, books-api, eks-saas-gitops)
- These repos have comprehensive README documentation that can be indexed into a Bedrock Knowledge Base to build an internal developer support agent answering "How do I deploy the microservices?" or "What's the architecture of the SaaS platform?"

### Cross-Repo Agent Opportunities

**Unified Customer Support Agent** (aws-microservices + unishop-monolith + local-monolith)
- A single customer-facing agent could orchestrate across all three e-commerce services: search products in aws-microservices, check baskets and order history in unishop-monolith, and process returns/fulfillment in local-monolith. This multi-tool agent addresses the core goal of "customer-facing AI agents for support and order management" by spanning the full customer journey.

**Cross-Service Order Management Agent** (aws-microservices → books-api)
- The dependency between aws-microservices and books-api means an agent can orchestrate the ordering flow end-to-end: take an order through aws-microservices, update the book catalog in books-api, and provide real-time status across both services.

**Portfolio Knowledge Base** (all repos)
- Combine documentation from all 5 repos into a unified knowledge base. An internal developer support agent can answer architecture questions, deployment procedures, and troubleshooting guides spanning the entire portfolio.

### Prioritized Agent Wins

| Win | Repos Affected | Goal Alignment | Effort | Recommended Phase |
|-----|---------------|----------------|--------|-------------------|
| Customer Support Agent with JSON APIs | 5 repos | High | Low | Phase 1 |
| Unified Customer Support Agent (multi-service) | 3 repos | High | Medium | Phase 2 |
| Natural Language Data Query Agent | 3 repos | High | Medium | Phase 1 |
| Product Knowledge Agent | 3 repos | High | Low | Phase 1 |
| Portfolio Knowledge Base (internal) | 5 repos | Medium | Low | Phase 1 |
| DevOps Deployment Agent | 2 repos | Medium | Medium | Phase 2 |
| Cross-Service Order Management Agent | 2 repos | High | Medium | Phase 2 |

> These portfolio-wide agent opportunities can be pursued in parallel with the
> modernization roadmap. They demonstrate agent value early while foundations
> are being built across the portfolio.

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.** Programs are engagement-level decisions scoped to the customer's overall estate, not per-repo.

Based on the portfolio assessment findings, the following AWS programs may accelerate your modernization journey:

### Recommended Programs

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| Migration Acceleration Program (MAP) | High | All 5 repos have overall score < 2.5 (unishop-monolith: 1.33, aws-microservices: 1.7, local-monolith: 1.5, books-api: 2.0, eks-saas-gitops: 1.8). Portfolio requires significant modernization investment. | Evaluate MAP eligibility with AWS account team — portfolio qualifies with 5 services scoring below 2.5 |
| EBA — Move to Modern DevOps | High | 4 of 5 services triggered Move to Modern DevOps pathway. INF-Q6 < 3 in 3 services, OPS-Q1 < 3 in 4 services. DevOps modernization is the highest-breadth pathway. | Request EBA engagement via SA for Move to Modern DevOps |
| EBA — Move to AI | High | 5 of 5 services triggered Move to AI pathway. 100% portfolio coverage. APP-Q13, DATA-Q1, DATA-Q3, OPS-Q3, OPS-Q6 all score 1/4 across entire portfolio. This is the portfolio's primary goal. | Request EBA engagement via SA for Move to AI |
| EBA — Move to Cloud Native | Medium | 2 of 5 services (unishop-monolith, local-monolith) triggered. Both monoliths require decomposition for clean agent tool boundaries. | Request EBA engagement via SA for Move to Cloud Native |
| EBA — Move to Containers | Medium | 2 of 5 services (unishop-monolith, local-monolith) triggered. Containerization is prerequisite for cloud-native decomposition. | Request EBA engagement via SA for Move to Containers |
| EBA — Move to Managed Databases | Low | 1 of 5 services (unishop-monolith) triggered. Self-managed MySQL on EC2 needs migration to RDS. | Request EBA engagement via SA for Move to Managed Databases |

### Program Details

**Migration Acceleration Program (MAP)**: All 5 portfolio services score below 2.5/4.0, indicating substantial modernization work across the board. MAP can provide credits, migration tooling, and expert guidance to accelerate the 6-month modernization roadmap. The portfolio's combination of legacy monoliths, missing CI/CD, and complete absence of AI infrastructure makes it an ideal MAP candidate. Timing: Engage in Phase 0 to maximize credit utilization across all phases.

**EBA — Move to Modern DevOps**: With 80% of the portfolio lacking CI/CD, observability, or both, a targeted EBA engagement can establish the DevOps foundation needed for safe agent deployment. The EBA team can help design shared CI/CD templates, observability standards, and deployment strategies. Timing: Phase 0.

**EBA — Move to AI**: This is the portfolio's primary goal. An EBA engagement focused on AI can help design the agent architecture, shared Knowledge Base infrastructure, evaluation frameworks, and multi-agent orchestration patterns. The EBA team can bring reference architectures from similar customer engagements. Timing: Phase 1-2.

**EBA — Move to Cloud Native / Containers**: These paired EBA engagements support the two monoliths (unishop-monolith and local-monolith). Containerization and decomposition are complex activities that benefit from expert guidance, especially for defining service boundaries that align with agent tool interfaces. Timing: Phase 1 (containers), Phase 3 (cloud native).

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

## Integration Opportunities

### Shared Service Extraction

**Opportunity 1: Shared Authentication Service (Amazon Cognito)**
- Current State: No centralized authentication. unishop-monolith has basic Spring Security, local-monolith has WAF but no app-level auth, books-api has Cognito for one endpoint, aws-microservices and eks-saas-gitops have no auth at all.
- Proposed Solution: Deploy a shared Cognito user pool with OAuth2/OIDC serving all 5 services. Define scopes for agent actions (read, write, admin).
- Benefits: Consistent identity across services, enables secure agent identity propagation, reduces per-service auth implementation cost
- Effort: Medium
- Priority: High — prerequisite for agent deployment

**Opportunity 2: Shared Observability Platform**
- Current State: 4 of 5 services have zero observability. books-api has X-Ray tracing. No shared dashboards, no cross-service tracing.
- Proposed Solution: Deploy OpenTelemetry with X-Ray backend, centralized CloudWatch dashboards, and shared alarm templates for all services.
- Benefits: End-to-end tracing across agent workflows spanning multiple services, consistent metrics, reduced per-service setup cost
- Effort: Medium
- Priority: High — required for agent monitoring

**Opportunity 3: Shared API Documentation Platform**
- Current State: All 5 services lack API documentation. Each would need to generate OpenAPI specs independently.
- Proposed Solution: Establish a portfolio-wide API documentation portal (e.g., API Gateway developer portal) with auto-generated specs from all services.
- Benefits: Single location for agent tool discovery, consistent documentation standards, enables automated tool registration
- Effort: Low
- Priority: High — prerequisite for agent tool discovery

### Event-Driven Architecture

**Opportunity 1: Replace Synchronous Dependencies with EventBridge**
- Current State: books-api makes synchronous REST calls to aws-microservices for product catalog data.
- Proposed Solution: books-api subscribes to product catalog change events via EventBridge. Maintains a local cache/projection of product data. Eliminates synchronous dependency.
- Benefits: Breaks the circular dependency, improves resilience, enables independent deployment, reduces latency for agent workflows
- Effort: Medium
- Priority: High — resolves the circular dependency identified in Phase 0

**Opportunity 2: Event-Driven Agent Workflows**
- Current State: Agent interactions will need to orchestrate across multiple synchronous APIs.
- Proposed Solution: Use EventBridge + Step Functions for agent workflow orchestration. Agent submits intent → Step Functions orchestrates service calls → results aggregated and returned.
- Benefits: Decoupled agent workflows, built-in retry/error handling, timeout management, human approval integration via Step Functions
- Effort: Medium
- Priority: Medium — Phase 2-3

### API Gateway Consolidation

- Current State: aws-microservices uses CDK-defined API Gateways (3 separate), books-api uses SAM-defined API Gateway, local-monolith uses App Runner (no API Gateway), unishop-monolith uses direct EC2 access, eks-saas-gitops uses Kubernetes Ingress.
- Proposed Solution: Consolidate customer-facing APIs behind a shared API Gateway with unified auth, rate limiting, and monitoring. Keep internal service-to-service communication separate.
- Benefits: Consistent auth and rate limiting, single entry point for agents, unified monitoring, simplified agent tool configuration
- Effort: Medium
- Priority: Medium — Phase 1-2

### Observability Unification

- Current State: books-api has X-Ray + CloudWatch. eks-saas-gitops has Kubecost. Other 3 services have nothing.
- Proposed Solution: Unified observability: OpenTelemetry for all services, X-Ray for tracing, CloudWatch for metrics/logs/alarms, and a shared Grafana dashboard (or CloudWatch cross-account) for portfolio-wide visibility.
- Benefits: Cross-service trace correlation (critical for multi-service agent workflows), consistent alerting, reduced tool sprawl
- Effort: Medium
- Priority: High — Phase 0

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + embedded service teams (cross-cutting concerns count exceeds 5, recommending dedicated platform team)

**Platform Team** (dedicated):
- Responsibilities: Shared Cognito infrastructure, API Gateway patterns, observability stack (OpenTelemetry + X-Ray), CI/CD pipeline templates, Bedrock Knowledge Base infrastructure, vector database management, agent evaluation framework
- Skills Required: Terraform, AWS CDK, OpenTelemetry, Amazon Bedrock, Cognito, API Gateway, CloudWatch

**Service Teams** (per-service):
- unishop-monolith team: Java/Spring Boot, containerization (Docker/ECS), MySQL→RDS migration
- aws-microservices team: TypeScript/Node.js, Lambda, DynamoDB, EventBridge
- local-monolith team: PHP, Docker, ECS, Terraform
- books-api team: TypeScript/Node.js, Lambda, CDK, CodePipeline
- eks-saas-gitops team: Python, EKS, Terraform, Helm, Flux CD

### Skill Gaps

1. **AI/Agent Frameworks**: Required for all 5 services, currently not available in any team. Gap: Strands Agents SDK, Amazon Bedrock, RAG pipeline design, prompt engineering.
2. **Containers/ECS**: Required for unishop-monolith (no container experience) and local-monolith (App Runner → ECS migration). Gap: Docker, ECS task definitions, Fargate, ECR.
3. **Terraform IaC**: Required for unishop-monolith (no IaC) and as portfolio standard. Gap: Terraform module design, state management, CI integration.
4. **Observability/OpenTelemetry**: Required for 4 services with zero observability. Gap: OpenTelemetry instrumentation, X-Ray configuration, CloudWatch dashboards.
5. **CI/CD Pipeline Design**: Required for 3 services with no CI/CD. Gap: GitHub Actions, automated testing, canary deployments, GitOps workflows.

### Training Recommendations

- **Immediate (Phase 0)**: AI/Agent frameworks (Module 7), Modern DevOps (Module 6) — needed first for all teams
- **Phase 1**: Containers (Module 3) for monolith teams, Managed Databases (Module 4) for unishop-monolith team
- **Phase 2-3**: Cloud Native (Module 2) for decomposition planning

### External Support

- **AWS Professional Services or Partner** recommended for:
  - Platform team bootstrap (2-3 months): Establish shared infrastructure, CI/CD templates, observability stack
  - Agent architecture design (1-2 months): Design multi-agent orchestration, RAG pipeline architecture, eval framework
  - Database migration (1 month): unishop-monolith MySQL EC2 → RDS migration with zero downtime
  - Knowledge transfer throughout all engagements

## Recommended Self-Paced Learning Materials

Based on portfolio-wide skill gaps in AI/Agent frameworks, DevOps, containers, databases, and cloud-native architecture:

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate RAG Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- EKS Workshop — https://www.eksworkshop.com/

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Circular dependency (aws-microservices ↔ books-api) blocks independent deployment | High | Medium | Resolve in Phase 0 by replacing sync REST call with async EventBridge pattern |
| 3 services with no CI/CD — manual deployments cause errors during rapid agent iteration | High | High | Deploy shared CI/CD templates in Phase 0. Use books-api as reference implementation |
| 4 services with no observability — agent failures invisible in production | High | High | Deploy unified OpenTelemetry + X-Ray stack in Phase 0 before any agent deployment |
| unishop-monolith self-managed MySQL on EC2 — data availability risk during migration | Medium | High | Use RDS read replica for zero-downtime migration. Implement DMS for continuous replication during cutover |
| All APIs lack rate limiting — agent loops could overwhelm services | High | High | Deploy API Gateway rate limiting in Phase 0. Implement per-agent rate limits and circuit breakers |
| 4 different programming languages — increases complexity of agent framework integration | Medium | Medium | Standardize on Strands Agents SDK (Python) for agent layer. Each service provides tools via REST/OpenAPI, not embedded SDKs |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI/Agent framework skill gap across all teams | High | High | Prioritize Module 7 training in Phase 0. Consider AWS Professional Services for agent architecture design |
| 4 distinct IaC tools (CDK, CloudFormation, Terraform, none) — standardization overhead | Medium | Medium | Standardize on Terraform (per preference) for new infrastructure. Migrate incrementally, don't rewrite existing CDK/CFN |
| Portfolio-wide modernization scope may overwhelm teams | Medium | High | Phase the work strictly. Focus Phase 0 on shared infrastructure, Phase 1 on P0 services only. Celebrate quick wins to maintain momentum |
| No platform team exists — shared infrastructure gaps persist | Medium | High | Establish dedicated platform team in Phase 0. Define clear ownership of shared services |

### Dependency Risks

- **Circular Dependency**: aws-microservices ↔ books-api forms a cycle that prevents independent deployment and scaling. Must be resolved in Phase 0 by defining API contracts and moving to async communication.
- **books-api depends on aws-microservices for product data**: If aws-microservices modernization is delayed, books-api agent integration is blocked. Mitigate by resolving the dependency in Phase 0.

### Single Points of Failure

- **unishop-monolith MySQL on EC2**: No Multi-AZ, no automated backups confirmed. If the EC2 instance or MySQL process fails, the entire e-commerce application is down. Mitigate by migrating to RDS Multi-AZ in Phase 1.
- **No shared authentication**: If one service implements auth differently than others, agent identity propagation breaks across the portfolio. Mitigate by deploying shared Cognito in Phase 0.

## Service-by-Service Summary

### unishop-monolith

- **Overall Score**: 1.33 / 4.0 ❌
- **Repository**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-12
- **Category Scores**:
  - Infrastructure: 1.1 / 4.0
  - Application: 1.5 / 4.0
  - Data: 2.0 / 4.0
  - Security: 1.1 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. APP-Q2: No API documentation — blocking agent tool discovery
  2. INF-Q5: No Infrastructure as Code — all infrastructure manually provisioned
  3. INF-Q6: No CI/CD pipeline — manual builds and deployments
  4. SEC-Q4: Hardcoded database credentials in application.properties
  5. APP-Q13: No AI/agent frameworks
- **Dependencies**: None (isolated)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native (High), Move to Containers (High), Move to Managed Databases (Medium), Move to Modern DevOps (High), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Managed Databases (High), Move to Modern DevOps (High), Move to Cloud Native (Medium), Move to Containers (Medium)
- **Modernization Phase**: Phase 1
- **Estimated Effort**: High

### aws-microservices

- **Overall Score**: 1.7 / 4.0 🟠
- **Repository**: ./services/aws-microservices
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-12
- **Category Scores**:
  - Infrastructure: 2.4 / 4.0
  - Application: 1.9 / 4.0
  - Data: 2.0 / 4.0
  - Security: 1.4 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. APP-Q2: No API documentation for 3 API Gateways
  2. OPS-Q1: No distributed tracing across Lambda/EventBridge/SQS
  3. INF-Q6: No CI/CD — manual `cdk deploy` only
  4. SEC-Q1: No API authentication
  5. APP-Q13: No AI/agent frameworks
- **Dependencies**: books-api (SYNC: REST for catalog data)
- **Depended On By**: books-api (ASYNC: EventBridge events)
- **Modernization Pathways**: Move to Modern DevOps (High), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Modern DevOps (High)
- **Modernization Phase**: Phase 1
- **Estimated Effort**: Medium

### local-monolith

- **Overall Score**: 1.5 / 4.0 🟠
- **Repository**: ./monolith
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-12
- **Category Scores**:
  - Infrastructure: 1.9 / 4.0
  - Application: 1.3 / 4.0
  - Data: 1.8 / 4.0
  - Security: 1.5 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. APP-Q2: No API documentation for 20+ JSON endpoints
  2. APP-Q4: Tightly coupled monolith in single index.php
  3. INF-Q6: No CI/CD — manual docker-compose deployments
  4. OPS-Q1: No distributed tracing or observability
  5. APP-Q13: No AI/agent frameworks
- **Dependencies**: None (isolated)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native (High), Move to Containers (Medium), Move to Modern DevOps (High), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Modern DevOps (High), Move to Cloud Native (Medium), Move to Containers (Medium)
- **Modernization Phase**: Phase 1
- **Estimated Effort**: High

### books-api

- **Overall Score**: 2.0 / 4.0 🟠
- **Repository**: ./services/books-api
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-12
- **Category Scores**:
  - Infrastructure: 2.7 / 4.0
  - Application: 1.8 / 4.0
  - Data: 1.9 / 4.0
  - Security: 2.0 / 4.0
  - Operations: 1.8 / 4.0
- **Top Priorities**:
  1. APP-Q2: No OpenAPI spec for agent tool discovery
  2. APP-Q13: No AI/agent framework integration
  3. DATA-Q1: No vector database for semantic book search
  4. DATA-Q3: No RAG pipeline for book catalog knowledge
  5. OPS-Q3: No automated agent evaluation framework
- **Dependencies**: aws-microservices (ASYNC: EventBridge events)
- **Depended On By**: aws-microservices (SYNC: REST catalog queries)
- **Modernization Pathways**: Move to AI (High)
- **Goal Alignment**: Move to AI (High)
- **Modernization Phase**: Phase 2
- **Estimated Effort**: Medium

### eks-saas-gitops

- **Overall Score**: 1.8 / 4.0 🟠
- **Repository**: ./services/eks-saas-gitops
- **Repository Type**: monorepo (auto-detected)
- **Assessment Date**: 2026-03-12
- **Category Scores**:
  - Infrastructure: 2.8 / 4.0
  - Application: 2.2 / 4.0
  - Data: 1.8 / 4.0
  - Security: 1.3 / 4.0
  - Operations: 1.2 / 4.0
- **Top Priorities**:
  1. APP-Q2: No API documentation for microservice APIs
  2. SEC-Q1: No API authentication
  3. OPS-Q1: No distributed tracing (no OpenTelemetry/X-Ray)
  4. APP-Q13: No AI/agent frameworks
  5. OPS-Q10: No integration tests
- **Dependencies**: None (isolated)
- **Depended On By**: None
- **Modernization Pathways**: Move to Modern DevOps (High), Move to AI (High)
- **Goal Alignment**: Move to AI (High), Move to Modern DevOps (High)
- **Modernization Phase**: Phase 2
- **Estimated Effort**: Medium

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Repo Type | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------|-----------------|---------------|-------------|
| unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy | application | 2026-03-12 | 1.33 / 4.0 | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-assessment/MonoToMicroLegacy-agentic-readiness-report.md |
| aws-microservices | ./services/aws-microservices | application | 2026-03-12 | 1.7 / 4.0 | ./services/aws-microservices/agentic-readiness-assessment/aws-microservices-agentic-readiness-report.md |
| local-monolith | ./monolith | application | 2026-03-12 | 1.5 / 4.0 | ./monolith/agentic-readiness-assessment/monolith-agentic-readiness-report.md |
| books-api | ./services/books-api | application | 2026-03-12 | 2.0 / 4.0 | ./services/books-api/agentic-readiness-assessment/books-api-agentic-readiness-report.md |
| eks-saas-gitops | ./services/eks-saas-gitops | monorepo | 2026-03-12 | 1.8 / 4.0 | ./services/eks-saas-gitops/agentic-readiness-assessment/eks-saas-gitops-agentic-readiness-report.md |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)
- Portfolio scores are arithmetic means of individual service scores
- N/A criteria excluded from aggregations (none detected in this portfolio — all services are application or monorepo type)

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - Establish the platform team and assign ownership of shared infrastructure
   - Set up Amazon Bedrock access and development sandbox for agent prototyping
   - Begin Module 7 (Move to AI) and Module 6 (Move to Modern DevOps) training for all teams
   - Start OpenAPI spec generation for aws-microservices (highest-value agent tool surface)

2. **Short-term (Month 1)**:
   - Deploy shared Cognito user pool for portfolio-wide authentication
   - Deploy unified observability stack (OpenTelemetry + X-Ray) for all services
   - Create CI/CD pipeline templates and deploy for unishop-monolith, aws-microservices, local-monolith
   - Resolve aws-microservices ↔ books-api circular dependency
   - Deploy API Gateway with rate limiting for all services

3. **Medium-term (Months 1-3)**:
   - Deploy first agent proof-of-concepts using existing JSON APIs (Phase 1 agent quick wins)
   - Containerize unishop-monolith and migrate MySQL to RDS
   - Migrate local-monolith from App Runner to ECS
   - Generate OpenAPI specs for all 5 services
   - Begin Bedrock Knowledge Base deployment for product catalog RAG

4. **Long-term (Months 3-6)**:
   - Deploy production customer-facing agents for support and order management
   - Build multi-agent orchestration spanning aws-microservices, unishop-monolith, and local-monolith
   - Implement human approval workflows for high-risk agent actions
   - Deploy agent evaluation pipelines in CI/CD
   - Implement LLM cost tracking and optimization
   - Begin monolith decomposition for cleaner agent tool boundaries
