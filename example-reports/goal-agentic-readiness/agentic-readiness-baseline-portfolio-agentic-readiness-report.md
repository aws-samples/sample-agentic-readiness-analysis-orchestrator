# Portfolio Agentic Readiness Assessment Report
**Portfolio**: agentic-readiness-baseline
**Assessment Goal**: agentic-readiness
**Services Assessed**: 5
**Assessment Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Portfolio Agentic Readiness Assessment

---

## Table of Contents

1. Executive Dashboard
2. Portfolio Readiness Overview
3. Service Dependency Map
4. Cross-Cutting Concerns
5. Portfolio Modernization Roadmap
   - Phase 0 — Cross-Cutting Foundation (Mo 0–1)
   - Phase 1 — Quick Wins (Mo 1–2)
   - Phase 2 — Foundation (Mo 2–4)
   - Phase 3 — Advanced Capabilities (Mo 4–6+)
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

This portfolio of 5 services scores **1.67 / 4.0** overall, placing it squarely in the **"Needs Work"** band with no services achieving even partial agentic readiness (≥ 2.5). The portfolio spans a wide technology spectrum — from a legacy Java monolith on raw EC2 (unishop-monolith, 1.21) to a well-architected serverless API with full CI/CD (books-api, 2.0) — but all services share critical gaps in AI/agent frameworks, observability, API documentation, and security. Operations & Observability is the weakest category across the portfolio at 1.18/4.0, with 4 of 5 services scoring 1.0 (zero observability). Identity, Security & Governance is the second weakest at 1.44/4.0, with hardcoded credentials in 2 services and missing API authentication in 2 others.

The most impactful portfolio-level investments are: (1) establishing a shared observability platform (tracing, structured logging, dashboards) across all 5 services, (2) creating CI/CD pipeline standards for the 3 services that lack automation, (3) migrating hardcoded secrets to AWS Secrets Manager, and (4) adding API authentication uniformly. These cross-cutting foundations are prerequisites for any agentic capability — agents require observable, secure, and automatically deployable services to operate safely.

The dependency graph reveals a circular dependency between aws-microservices and books-api (async EventBridge + sync REST) that must be broken in Phase 0. The remaining 3 services (unishop-monolith, local-monolith, eks-saas-gitops) are isolated with no cross-service dependencies, enabling parallel modernization. With a coordinated 6-month roadmap, the portfolio can establish foundational readiness (Phase 0–1) in 2 months and begin agent framework integration (Phase 2–3) by month 3.

### Portfolio Readiness Score: 1.67 / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | 2.16 / 4.0 | ✅ 0 services, 🟡 3 services, 🟠 1 service, ❌ 1 service | 🟠 |
| Application Architecture | 1.70 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 3 services, ❌ 2 services | 🟠 |
| Data Foundations | 1.85 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 5 services, ❌ 0 services | 🟠 |
| Identity, Security & Governance | 1.44 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 2 services, ❌ 3 services | ❌ |
| Operations & Observability | 1.18 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 0 services, ❌ 5 services | ❌ |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): 0 services (0%)
- 🟡 Partial (2.5-3.4): 0 services (0%)
- 🟠 Needs Work (1.5-2.4): 4 services (80%) — aws-microservices (1.73), local-monolith (1.50), books-api (2.0), eks-saas-gitops (1.9)
- ❌ Not Ready (< 1.5): 1 service (20%) — unishop-monolith (1.21)

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | 5 | 3 P0 priority, 2 P1 priority |
| Average Readiness Score | 1.67 / 4.0 | All services below "Partial" threshold (2.5) |
| Services Ready for Agents | 0 (0%) | No service scores ≥ 3.5; significant investment needed |
| Critical Dependencies | 1 pair | aws-microservices ↔ books-api circular dependency |
| Shared Infrastructure Gaps | 10+ | Observability, CI/CD, API docs, security baseline affect 3–5 services each |
| Estimated Modernization Effort | High | All 5 services require substantial work across all categories |
| Expected Timeline | 6 months | 4 phases with 3 parallel tracks |

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- TypeScript/Node.js: 2 services (40%) — aws-microservices, books-api
- Java 8 (Spring Boot 2.1.x): 1 service (20%) — unishop-monolith
- PHP 8.2: 1 service (20%) — local-monolith
- Python 3.9 (Flask): 1 service (20%) — eks-saas-gitops

**Database Engines:**
- DynamoDB (fully managed): 3 services (60%) — aws-microservices, books-api, eks-saas-gitops
- MySQL (self-managed / ambiguous): 1 service (20%) — unishop-monolith
- MySQL via RDS (managed): 1 service (20%) — local-monolith

**Compute Patterns:**
- Serverless (Lambda): 2 services (40%) — aws-microservices, books-api
- Containers (EKS): 1 service (20%) — eks-saas-gitops
- Managed Containers (App Runner): 1 service (20%) — local-monolith
- Raw EC2: 1 service (20%) — unishop-monolith

**IaC Coverage:**
- CDK: 2 services (40%) — aws-microservices, books-api (SAM+CDK)
- Terraform + GitOps: 1 service (20%) — eks-saas-gitops
- CloudFormation: 1 service (20%) — local-monolith
- None: 1 service (20%) — unishop-monolith

**Deployment Maturity:**
- Full CI/CD (build + test + staged deploy): 1 service (20%) — books-api
- CD Only (GitOps, no CI): 1 service (20%) — eks-saas-gitops
- Manual deployment: 3 services (60%) — unishop-monolith, aws-microservices, local-monolith

### Common Strengths

1. **Structured JSON APIs**: All 5 services return structured JSON responses (APP-Q5 scores 3–4/4), providing an immediate foundation for agent tool integration.
2. **DynamoDB Adoption**: 3 of 5 services use fully managed DynamoDB, eliminating database operational overhead and version management concerns.
3. **Managed Compute (4 of 5)**: 4 services use managed compute (Lambda, App Runner, or EKS) — only unishop-monolith runs on raw EC2.
4. **Clean SQL Schemas**: Both MySQL-based services (unishop-monolith, local-monolith) have no stored procedures or proprietary SQL constructs (DATA-Q11 scores 3–4/4), simplifying future database migration.
5. **Event-Driven Patterns**: aws-microservices uses EventBridge + SQS; eks-saas-gitops uses SQS + Argo Events — demonstrating existing async messaging capability.

### Common Gaps

1. **No AI/Agent Frameworks** (APP-Q13: 1/4 in all 5 services) — Zero agent framework integration across the entire portfolio.
2. **No Vector Databases** (DATA-Q1: 1/4 in all 5 services) — No semantic search or RAG capability exists anywhere.
3. **No RAG Implementation** (DATA-Q3: 1/4 in all 5 services) — No retrieval-augmented generation pipelines.
4. **No API Documentation** (APP-Q2: 1/4 in all 5 services) — No OpenAPI specs for agent tool discovery.
5. **No API Versioning** (APP-Q11: 1/4 in all 5 services) — Breaking API changes affect all consumers.
6. **No Resilience Patterns** (APP-Q9: 1/4 in all 5 services) — No circuit breakers, retries, or timeouts.
7. **Weak Observability** (OPS category avg: 1.18/4.0) — 4 services have zero distributed tracing; only books-api has X-Ray.

## Service Dependency Map

### High-Level Architecture

The portfolio consists of 5 services with minimal cross-service dependencies. Three services (unishop-monolith, local-monolith, eks-saas-gitops) are completely isolated with no dependencies on other portfolio services. The remaining two services (aws-microservices, books-api) form a bidirectional dependency pair — aws-microservices publishes events to books-api via EventBridge (async), and books-api queries aws-microservices for catalog data via REST (sync). This bidirectional dependency constitutes a **circular dependency** that must be resolved before independent modernization can proceed.

### Service Dependency Matrix

| Service | Depends On | Depended On By | Coupling Score | Fan-In | Fan-Out | Blast Radius | Priority |
|---------|------------|----------------|----------------|--------|---------|--------------|----------|
| unishop-monolith | — | — | None | 0 | 0 | 0% | P0 |
| aws-microservices | books-api (sync REST) | books-api (async EventBridge) | Medium | 1 | 1 | 20% | P0 |
| local-monolith | — | — | None | 0 | 0 | 0% | P0 |
| books-api | aws-microservices (async EventBridge) | aws-microservices (sync REST) | Medium | 1 | 1 | 20% | P1 |
| eks-saas-gitops | — | — | None | 0 | 0 | 0% | P1 |

**Coupling Score Definitions:**
- **High**: Synchronous dependencies + shared databases OR 3+ dependency types
- **Medium**: Synchronous dependency OR 2 dependency types
- **Low**: Asynchronous only OR shared infrastructure only
- **None**: No cross-service dependencies

**Priority Definitions:**
- **P0**: Critical path services — unishop-monolith (lowest score, most work), aws-microservices (circular dependency), local-monolith (low score, P0 per config)
- **P1**: Important services with moderate gaps — books-api (highest score), eks-saas-gitops

### Critical Path Analysis

1. **Circular Dependency** (⚠️ Phase 0 Resolution Required):
   - aws-microservices → books-api (async via EventBridge)
   - books-api → aws-microservices (sync via REST)
   - **Impact**: These two services cannot be independently deployed or modernized until the circular dependency is broken.
   - **Resolution**: Replace the sync REST call (books-api → aws-microservices) with an async EventBridge pattern or data replication, making the dependency fully unidirectional.

2. **Foundation Services** (must be modernized first):
   - No service has fan-in ≥ 3; no traditional "foundation service" exists in this portfolio.
   - The circular dependency pair (aws-microservices, books-api) is the only sequencing constraint.

3. **Independent Services** (can be parallelized):
   - unishop-monolith, local-monolith, eks-saas-gitops — all three can be modernized concurrently with no cross-service dependencies.

### Integration Points

**Synchronous Integrations:**
- books-api → aws-microservices: REST API call for product catalog data

**Asynchronous Integrations:**
- aws-microservices → books-api: EventBridge events for book catalog updates triggered by ordering flow

**Shared Infrastructure:**
- None identified — each service uses independent infrastructure (separate databases, separate compute, separate IaC)

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are classified into tiers based on severity. Since the portfolio goal is `agentic-readiness`, only Tier 1 (Foundational Blockers) and General Opportunities are rendered. Tiers 2 and 3 are omitted because `agentic-readiness` treats all non-foundational gaps as equal improvement opportunities.

### 🚨 Foundational Blockers

> These gaps block all modernization efforts, not just agentic-readiness.
> Address these first — nothing else matters until these are resolved.

1. **INF-Q6: CI/CD Pipelines** — 3 of 5 services score < 2
   - **Impact**: Without automated build, test, and deploy pipelines, no changes can be safely delivered. Manual deployments block iteration velocity for all modernization activities.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4)
   - **Recommendation**: Establish portfolio-wide CI/CD pipeline templates (GitHub Actions or CodePipeline) with standardized stages: lint, test, build, scan, deploy. books-api's pipeline can serve as the reference implementation.

2. **OPS-Q1: Distributed Tracing** — 4 of 5 services score < 2
   - **Impact**: Without tracing, cross-service request flows are invisible. Debugging failures in agent workflows spanning multiple services is impossible.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), eks-saas-gitops (1/4)
   - **Recommendation**: Deploy a unified observability platform: OpenTelemetry + AWS X-Ray for serverless services, ADOT collector for EKS services. books-api (3/4 with X-Ray) serves as the pattern.

3. **APP-Q8 + SEC-Q5: Rate Limiting** — 5 of 5 services score < 2 on both criteria
   - **Impact**: No rate limiting at any layer across the entire portfolio. APIs are vulnerable to abuse, DoS, and runaway agent loops. This blocks safe agent deployment.
   - **Affected services**: All 5 services
   - **Recommendation**: Implement API Gateway throttling or WAF rate-based rules as a shared infrastructure pattern. Define per-service rate limits based on expected traffic patterns.

### 💡 General Improvement Opportunities

> These gaps are important and represent equal improvement opportunities across the portfolio.
> Address them based on capacity and impact.

> With `agentic-readiness` as the goal, all non-foundational gaps are treated as equal improvement opportunities.

1. **APP-Q13: AI/Agent Frameworks** — 5 of 5 services score < 3
   - **Impact**: No service has any AI/agent framework integration. This is the core capability gap for agentic readiness.
   - **Affected services**: All 5 services (1/4 each)
   - **Recommendation**: Start with Amazon Bedrock integration in the Python service (eks-saas-gitops) and TypeScript services (aws-microservices, books-api). Use existing JSON APIs as agent tools. Add Spring AI for the Java service (unishop-monolith).

2. **DATA-Q1: Vector Database** — 5 of 5 services score < 3
   - **Impact**: No semantic search or RAG capability exists anywhere in the portfolio.
   - **Affected services**: All 5 services (1/4 each)
   - **Recommendation**: Deploy Amazon Bedrock Knowledge Bases or OpenSearch Serverless as a shared vector storage service accessible by all services.

3. **DATA-Q3: RAG Implementation** — 5 of 5 services score < 3
   - **Impact**: No retrieval-augmented generation pipelines for agent knowledge retrieval.
   - **Affected services**: All 5 services (1/4 each)
   - **Recommendation**: Build a shared RAG pipeline using Bedrock Knowledge Bases with product catalogs and documentation indexed across services.

4. **APP-Q2: API Documentation** — 5 of 5 services score < 3
   - **Impact**: Agents cannot discover or invoke APIs without machine-readable OpenAPI specs.
   - **Affected services**: All 5 services (1/4 each)
   - **Recommendation**: Generate OpenAPI 3.0 specs for all services — springdoc for Java, manual YAML for Node.js, flask-smorest for Python.

5. **APP-Q11: API Versioning** — 5 of 5 services score < 3
   - **Impact**: Breaking API changes disrupt all consumers including agent tool integrations.
   - **Affected services**: All 5 services (1/4 each)
   - **Recommendation**: Adopt URL path versioning (`/v1/`) across all services before exposing APIs as agent tools.

6. **APP-Q9: Resilience Patterns** — 5 of 5 services score < 3
   - **Impact**: No circuit breakers, retries, or timeouts. Agent-initiated failures cascade without mitigation.
   - **Affected services**: All 5 services (1/4 each)
   - **Recommendation**: Add Resilience4j (Java), tenacity (Python), or p-retry (Node.js) with circuit breakers and exponential backoff.

7. **OPS-Q2: Structured Logging** — 4 of 5 services score < 3
   - **Impact**: Unstructured logs across 4 services prevent efficient debugging and correlation.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), eks-saas-gitops (1/4)
   - **Recommendation**: Standardize on JSON-formatted logging with correlation IDs. Deploy shared log format templates per language.

8. **SEC-Q3: Identity Propagation** — 4 of 5 services score < 3
   - **Impact**: No user identity propagated across requests. Agents acting on behalf of users have no verifiable identity context.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), eks-saas-gitops (1/4)
   - **Recommendation**: Implement Amazon Cognito as centralized identity provider with JWT-based identity propagation.

9. **SEC-Q7: Human Approval Workflows** — 3 of 5 services score < 3
   - **Impact**: No human-in-the-loop approval for high-risk agent actions.
   - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), eks-saas-gitops (1/4)
   - **Recommendation**: Implement Step Functions with `waitForTaskToken` for agent action approval workflows.

10. **OPS-Q10: Integration Testing** — 4 of 5 services score < 3
    - **Impact**: Zero test coverage in 4 services. Cannot validate changes before deployment.
    - **Affected services**: unishop-monolith (1/4), aws-microservices (1/4), local-monolith (1/4), eks-saas-gitops (1/4)
    - **Recommendation**: Establish testing standards per language. books-api's test suite (unit + e2e) serves as the reference implementation.

### Per-Category Analysis

### Infrastructure & Platform

**Portfolio Score: 2.16 / 4.0**

The infrastructure category shows the widest variation across the portfolio — from 1.0 (unishop-monolith with zero IaC, zero CI/CD, raw EC2) to 2.7 (eks-saas-gitops with comprehensive Terraform, Flux CD GitOps, and EKS). Four of 5 services use managed compute (Lambda, App Runner, EKS), and 3 of 5 use fully managed databases (DynamoDB). The primary gaps are CI/CD automation (3 services lack pipelines), workflow orchestration (3 services have none), and async messaging (2 services are 100% synchronous).

### Application Architecture

**Portfolio Score: 1.70 / 4.0**

Application architecture is consistently weak across the portfolio. Universal gaps include API documentation (0/5 services), API versioning (0/5), and resilience patterns (0/5). Architecture diversity is high — 2 monoliths (unishop-monolith, local-monolith), 2 microservices architectures (aws-microservices, eks-saas-gitops), and 1 focused single-purpose API (books-api). The positive finding is that all services return structured JSON (APP-Q5 scores 3–4), which is the foundation for agent tool integration.

### Data Foundations

**Portfolio Score: 1.85 / 4.0**

Data foundations are uniformly weak in AI-specific capabilities (vector DB, RAG, embeddings) while being reasonable for traditional data management. Three services use DynamoDB (no version/EOL concerns), and both MySQL services have clean schemas without stored procedures. The universal gaps in DATA-Q1 (vector DB), DATA-Q3 (RAG), and DATA-Q9 (embedding freshness) reflect the complete absence of AI data infrastructure rather than traditional data management failures.

### Identity, Security & Governance

**Portfolio Score: 1.44 / 4.0**

Security is a critical concern across the portfolio. Two services have hardcoded credentials (unishop-monolith: plaintext in application.properties, local-monolith: plaintext in docker-compose.yml). Two services have completely unauthenticated APIs (aws-microservices, eks-saas-gitops). No service has centralized identity management beyond books-api's basic Cognito integration. PII redaction is absent from all services. These gaps must be addressed before any agent deployment — agents amplify security vulnerabilities by operating autonomously.

### Operations & Observability

**Portfolio Score: 1.18 / 4.0**

Operations is the weakest category and the most critical blocker for agentic readiness. Four of 5 services have zero distributed tracing (only books-api has X-Ray). All 5 services lack structured logging, automated evals, SLOs, LLM cost tracking, business metrics, anomaly detection, incident response automation, and observability governance. Without observability, agent workflows cannot be debugged, measured, or improved. This category requires the most portfolio-level investment.

## Portfolio Modernization Roadmap

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Break the aws-microservices ↔ books-api circular dependency before independent modernization
3. **Risk Mitigation**: Address hardcoded credentials and unauthenticated APIs before adding agent capabilities
4. **Parallel Tracks**: 3 isolated services (unishop-monolith, local-monolith, eks-saas-gitops) can be modernized concurrently
5. **Quick Wins**: Early observability and CI/CD wins build momentum and demonstrate value
6. **Goal Alignment**: With `agentic-readiness`, all criteria are equally prioritized — no special re-weighting

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, resolve architectural risks, and create organizational readiness

**Circular Dependency Resolution:**
- Break the aws-microservices ↔ books-api circular dependency by replacing the sync REST call (books-api → aws-microservices) with async data replication via EventBridge or DynamoDB Streams

**Shared Infrastructure:**
- Establish portfolio-wide CI/CD pipeline templates: GitHub Actions or CodePipeline with standardized stages (lint, test, build, scan, deploy). Use books-api's pipeline as the reference.
- Deploy unified observability platform: OpenTelemetry + X-Ray standards for all services, ADOT collector for EKS. Define shared structured logging format (JSON with correlation IDs).
- Implement shared secrets management pattern: AWS Secrets Manager with dynamic references for all services. Remediate hardcoded credentials in unishop-monolith and local-monolith immediately.
- Define shared API Gateway throttling standards: Rate limits per service based on expected traffic patterns.

**Organizational Enablers:**
- Training: IaC (Terraform/CDK), CI/CD, containers, observability, and AI fundamentals
- Tooling: Shared CI/CD templates, logging libraries, tracing SDKs per language
- Standards: API documentation (OpenAPI 3.0), versioning strategy, error response format

**Expected Outcomes:**
- All hardcoded credentials migrated to Secrets Manager
- CI/CD pipeline templates available for all 4 languages (Java, TypeScript, PHP, Python)
- Circular dependency broken — aws-microservices and books-api can be modernized independently
- Observability SDK integration started across all services

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize the lowest-scoring P0 services and establish patterns for others

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.21/4.0)
   - Current State: Legacy Java 8 monolith on raw EC2, zero IaC, zero CI/CD, hardcoded credentials
   - Target State: Containerized, basic IaC, CI/CD pipeline, credentials in Secrets Manager, structured logging
   - Key Activities:
     - Create Dockerfile and deploy to ECS Fargate
     - Initialize Terraform/CDK IaC for VPC, ECS, RDS
     - Set up CI/CD pipeline (GitHub Actions or CodePipeline)
     - Add springdoc-openapi-ui for OpenAPI spec generation
     - Replace System.out.println with SLF4J + JSON logging
     - Add X-Ray SDK for distributed tracing
   - Dependencies: Phase 0 shared infrastructure templates
   - Blocks: None (isolated service)
   - Estimated Effort: High

2. **local-monolith** (P0, Score: 1.50/4.0)
   - Current State: PHP monolith on App Runner, CloudFormation IaC, manual deploy.sh, hardcoded secrets
   - Target State: CI/CD pipeline, structured logging, distributed tracing, secrets in Secrets Manager
   - Key Activities:
     - Create CI/CD pipeline for App Runner deployment via ECR push
     - Add OpenTelemetry PHP SDK for distributed tracing
     - Implement Monolog with JSON formatter for structured logging
     - Generate OpenAPI 3.0 spec for 20+ API endpoints
   - Dependencies: Phase 0 shared infrastructure templates
   - Blocks: None (isolated service)
   - Estimated Effort: High

3. **aws-microservices** (P0, Score: 1.73/4.0)
   - Current State: Serverless Lambda + DynamoDB + EventBridge, CDK IaC, no CI/CD, no observability
   - Target State: CI/CD pipeline, X-Ray tracing enabled, structured logging, API authentication
   - Key Activities:
     - Create CI/CD pipeline with `cdk synth` + `cdk deploy` stages
     - Enable X-Ray tracing on all Lambda functions (single property addition)
     - Add @aws-lambda-powertools/logger for structured JSON logging
     - Implement Cognito authorizer on all API Gateway endpoints
     - Generate OpenAPI 3.0 specs for Product, Basket, and Order APIs
   - Dependencies: Phase 0 circular dependency resolution
   - Blocks: None (after circular dependency broken)
   - Estimated Effort: Medium

**Expected Outcomes:**
- 3 P0 services have CI/CD pipelines and basic observability
- All hardcoded credentials eliminated
- OpenAPI specs generated for all Phase 1 services
- Security baseline established (authentication, secrets management)

**Estimated Effort**: High

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize P1 services, deploy AI data foundations, and replicate Phase 1 patterns

**Services in Scope:**

1. **books-api** (P1, Score: 2.0/4.0)
   - Current State: Well-architected serverless API with full CI/CD and X-Ray tracing but no AI capabilities
   - Target State: API documentation complete, vector database provisioned, rate limiting enabled, SDK v3 migration
   - Key Activities:
     - Generate OpenAPI 3.0 spec and add to SAM template
     - Add API Gateway throttling and usage plans
     - Migrate from AWS SDK v2 to SDK v3
     - Deploy Bedrock Knowledge Base for book catalog semantic search
     - Create data access layer (books-repository.ts)
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Medium

2. **eks-saas-gitops** (P1, Score: 1.9/4.0)
   - Current State: Strong EKS + Terraform + GitOps foundation, no CI pipeline, no observability, no auth
   - Target State: CI pipeline, OpenTelemetry tracing, JWT authentication, structured logging, API docs
   - Key Activities:
     - Create Gitea Actions or CodeBuild CI pipeline for build + test
     - Add OpenTelemetry SDK to all Python microservices + ADOT collector DaemonSet
     - Implement Cognito JWT authentication replacing unverified tenantID headers
     - Add flask-smorest for OpenAPI spec generation
     - Implement python-json-logger for structured logging
     - Secure Argo Workflows server (change auth-mode, make internal)
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: High

**Cross-Service Activities:**
- Deploy shared vector database (Bedrock Knowledge Bases or OpenSearch Serverless) accessible by all services
- Begin RAG pipeline implementation with product catalogs and documentation
- Implement resilience patterns (circuit breakers, retries) across all services
- Define SLOs for all services and create CloudWatch dashboards

**Expected Outcomes:**
- All 5 services have CI/CD, observability, API documentation, and authentication
- Shared vector database deployed for semantic search
- Resilience patterns implemented portfolio-wide
- SLOs defined and monitored

**Estimated Effort**: High

### Phase 3 — Advanced Capabilities (Mo 4–6+)

**Objective**: Implement agent frameworks, RAG pipelines, evaluation frameworks, and advanced operational capabilities

**Activities:**
- Integrate agent frameworks: Spring AI (Java), Strands Agents SDK / LangChain.js (TypeScript/Node.js), strands-agents (Python)
- Complete RAG pipelines with Bedrock Knowledge Bases for all services with indexable data
- Build automated eval frameworks with golden datasets per service
- Implement LLM cost tracking with CloudWatch custom metrics per service/user/workflow
- Deploy human-in-the-loop approval workflows using Step Functions for high-risk agent actions
- Implement advanced deployment strategies: canary deployments (Lambda aliases, Flagger for EKS)
- Enable anomaly detection on agent behavioral metrics
- Continue monolith decomposition (unishop-monolith: extract Basket service, local-monolith: extract Inventory service)
- Establish observability governance with CODEOWNERS, SLO ownership, and agent-level SLOs

**Expected Outcomes:**
- Agent framework integration in at least 3 services
- RAG-based semantic search operational for product catalogs
- Automated eval pipeline running in CI/CD
- LLM cost tracking and attribution operational
- Human approval gates for high-risk agent operations

**Estimated Effort**: High

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6 months (with 3 parallel tracks for isolated services)
**Parallel Tracks**: unishop-monolith | local-monolith + aws-microservices | eks-saas-gitops + books-api

## AWS Modernization Pathways

Based on the portfolio-wide assessment findings, the following AWS Modernization Pathways have been identified for each service. The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach — a customer portfolio may be divided into multiple pathways depending on workloads and priorities, and these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 2 services | 40% | Medium | High |
| Move to Containers | 1 service | 20% | Low | High |
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
| local-monolith | ✅ | — | — | — | — | ✅ | ✅ |
| books-api | — | — | — | — | — | — | ✅ |
| eks-saas-gitops | — | — | — | — | — | ✅ | ✅ |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing a single at-a-glance view of pathway coverage across the portfolio. Each repo appears in exactly one column per pathway row. Goal Alignment is based on the portfolio-level goal (`agentic-readiness`) — all pathways receive Medium alignment.

| Pathway | Triggered | Not Triggered | Not Applicable | Goal Alignment |
|---------|-----------|---------------|----------------|---------------|
| Move to Cloud Native | unishop-monolith, local-monolith | aws-microservices, books-api, eks-saas-gitops | — | Medium |
| Move to Containers | unishop-monolith | aws-microservices, local-monolith, books-api, eks-saas-gitops | — | Medium |
| Move to Open Source | — | unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops | — | Medium |
| Move to Managed Databases | unishop-monolith | aws-microservices, local-monolith, books-api, eks-saas-gitops | — | Medium |
| Move to Managed Analytics | — | unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops | — | Medium |
| Move to Modern DevOps | unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops | books-api | — | Medium |
| Move to AI | unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops | — | — | Medium |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native for unishop-monolith (containerize before decomposing into microservices)
- Move to Modern DevOps enables all other pathways (CI/CD accelerates safe delivery of changes across all pathways)
- Move to Managed Databases (unishop-monolith MySQL migration) can proceed in parallel with Move to Containers

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps (all 4 triggered services simultaneously — each gets CI/CD, observability, deployment strategy)
- **Track 2**: Move to Containers + Move to Cloud Native (unishop-monolith containerization, then monolith decomposition; local-monolith decomposition planning)
- **Track 3**: Move to AI (all 5 services — API docs, vector DB, RAG, agent frameworks — starts after Phase 1 foundations)

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops (4 total)
- **Portfolio Priority**: High (80% of portfolio triggered)
- **Common Trigger Criteria**:
  - INF-Q6 (CI/CD) < 3: affects 4 services (unishop-monolith 1/4, aws-microservices 1/4, local-monolith 1/4, eks-saas-gitops 2/4)
  - OPS-Q1 (tracing) < 3: affects 4 services (all except books-api)
  - OPS-Q10 (testing) < 3: affects 4 services (all except books-api)
  - OPS-Q9 (deployment strategy) < 3: affects 4 services
- **Representative AWS Services**: CodePipeline, CodeBuild, X-Ray, CloudWatch, CodeDeploy
- **Key Activities**:
  1. Create CI/CD pipelines for all 4 services using language-appropriate tooling
  2. Deploy OpenTelemetry / X-Ray tracing across all services
  3. Implement structured JSON logging portfolio-wide
  4. Write tests and integrate into CI pipelines
  5. Implement progressive delivery (canary/linear deployments)
- **Cross-Service Synergies**: books-api's existing CI/CD pipeline serves as the template; shared logging format reduces per-service effort
- **Estimated Effort**: High across 4 services
- **Roadmap Phase Alignment**: Phase 0 (standards) → Phase 1 (implementation for P0 services) → Phase 2 (P1 services + advanced strategies)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: All 5 services
- **Portfolio Priority**: High (100% of portfolio triggered)
- **Common Trigger Criteria**:
  - APP-Q13 (agent frameworks) = 1/4: all 5 services
  - DATA-Q1 (vector DB) = 1/4: all 5 services
  - DATA-Q3 (RAG) = 1/4: all 5 services
  - OPS-Q3 (evals) = 1/4: all 5 services
  - OPS-Q6 (LLM cost) = 1/4: all 5 services
- **Representative AWS Services**: Amazon Bedrock, Bedrock Knowledge Bases, OpenSearch Serverless, Strands Agents SDK
- **Key Activities**:
  1. Generate OpenAPI specs for all services (prerequisite for agent tool discovery)
  2. Deploy shared vector database infrastructure
  3. Build RAG pipelines for product catalog and documentation semantic search
  4. Integrate agent frameworks per language ecosystem
  5. Implement evaluation frameworks and LLM cost tracking
- **Cross-Service Synergies**: Shared vector database serves multiple services; shared RAG pipeline for cross-service documentation; Python services share agent framework patterns
- **Estimated Effort**: High across all 5 services
- **Roadmap Phase Alignment**: Phase 1 (API docs) → Phase 2 (vector DB, RAG) → Phase 3 (agent frameworks, evals, cost tracking)
- **Relevant Learning Materials**: Module 7 — Move to AI

#### Move to Cloud Native

- **Services Affected**: unishop-monolith, local-monolith (2 total)
- **Portfolio Priority**: Medium (40% of portfolio)
- **Common Trigger Criteria**:
  - APP-Q4 (monolith) < 4: unishop-monolith (2/4), local-monolith (1/4)
  - APP-Q3 (async) < 3: both services at 1/4
  - INF-Q1 (compute) < 3: unishop-monolith (1/4)
- **Key Activities**: Monolith decomposition via Strangler Fig pattern, introduce async messaging (SQS/EventBridge)
- **Roadmap Phase Alignment**: Phase 1 (containerize) → Phase 2 (first extraction) → Phase 3 (continued decomposition)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Containers

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Low (20% of portfolio)
- **Common Trigger Criteria**: INF-Q1 = 1/4 (raw EC2, no containerization)
- **Key Activities**: Create Dockerfile, deploy to ECS Fargate or EKS
- **Roadmap Phase Alignment**: Phase 1
- **Relevant Learning Materials**: Module 3 — Move to Containers

#### Move to Managed Databases

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Low (20% of portfolio)
- **Common Trigger Criteria**: INF-Q2 = 1/4 (ambiguous MySQL management), DATA-Q10 = 1/4 (outdated connector)
- **Key Activities**: Define MySQL in IaC as RDS/Aurora, update connector, enable encryption
- **Roadmap Phase Alignment**: Phase 1 (IaC) → Phase 2 (migration)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

## Portfolio Quick Agent Wins

Across the portfolio, these agent opportunities are immediately available based on existing capabilities found in individual assessments:

**JSON API Tool Integration** (5 repos: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops)
- All 5 services return structured JSON responses (APP-Q5 scores 3–4/4). Agent frameworks can wrap these endpoints as tools with minimal parsing effort. This is the single broadest quick win — every service in the portfolio is immediately usable as an agent tool.

**Data Query Agents** (3 repos: unishop-monolith, local-monolith, eks-saas-gitops)
- These services have well-defined database schemas that enable natural language to SQL/DynamoDB query agents. unishop-monolith has a clean 3-table MySQL schema in `create_tables.sql`, local-monolith has 9 well-defined tables in `init_db()`, and eks-saas-gitops has DynamoDB with clear partition/sort keys in Terraform.

**Documentation Knowledge Agents** (5 repos: all services)
- Every repository contains README documentation, schema definitions, and code comments that can be indexed for RAG-based knowledge agents. This enables developer onboarding assistance and architecture knowledge retrieval across the portfolio.

**DevOps Agents** (2 repos: books-api, eks-saas-gitops)
- books-api has a full CI/CD pipeline with CloudFormation outputs that provide programmatic access to deployment status. eks-saas-gitops has Argo Workflows and SQS-based tenant lifecycle automation providing a clear API for DevOps automation. These provide the richest DevOps agent opportunities.

**Fulfillment Decision Agent** (1 repo: local-monolith)
- local-monolith has rich decision-support API endpoints (`/api/orders/{id}/validation-data`, `/api/warehouses/assignment-options`, `/api/carriers/shipping-options`) returning structured recommendation scores. An agent can automate a 6-step manual fulfillment workflow immediately.

### Cross-Repo Agent Opportunities

**Unified E-Commerce Agent** (unishop-monolith → aws-microservices → books-api)
- These three services collectively cover product catalog, shopping cart, ordering, and book management. A unified agent spanning all three could handle end-to-end e-commerce interactions: search products (unishop-monolith), browse books (books-api), manage cart (aws-microservices), and process orders — providing a cross-service conversational commerce experience more valuable than any single-service agent.

**Portfolio-Wide Developer Knowledge Agent** (all 5 repos)
- Combine README files, schema documentation, API endpoint definitions, and architectural documentation from all 5 repositories into a single knowledge base. An internal developer support agent could answer questions like "How does the checkout flow work in aws-microservices?" or "What database does eks-saas-gitops use?" — dramatically improving developer onboarding and cross-team knowledge sharing.

### Prioritized Agent Wins

| Win | Repos Affected | Goal Alignment | Effort | Recommended Phase |
|-----|---------------|----------------|--------|-------------------|
| JSON API Tool Integration | 5 repos | Medium | Low | Phase 1 |
| Documentation Knowledge Agent | 5 repos | Medium | Low | Phase 1 |
| Data Query Agents | 3 repos | Medium | Medium | Phase 2 |
| Unified E-Commerce Agent | 3 repos | Medium | Medium | Phase 2 |
| DevOps Agents | 2 repos | Medium | Medium | Phase 2 |
| Fulfillment Decision Agent | 1 repo | Medium | Medium | Phase 2 |

> These portfolio-wide agent opportunities can be pursued in parallel with the
> modernization roadmap. They demonstrate agent value early while foundations
> are being built across the portfolio.

## AWS Programs & Engagement Recommendations

> This section appears ONLY in portfolio reports, NEVER in individual reports. Programs are engagement-level decisions scoped to the customer's overall estate, not per-repo.

Based on the portfolio assessment findings, the following AWS programs may accelerate your modernization journey:

### Recommended Programs

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| Migration Acceleration Program (MAP) | High | All 5 repos have overall score < 2.5 (unishop-monolith: 1.21, local-monolith: 1.50, aws-microservices: 1.73, eks-saas-gitops: 1.9, books-api: 2.0). Significant modernization investment needed across the portfolio. | Evaluate MAP eligibility with AWS account team. MAP provides credits and professional services to accelerate migration and modernization. |
| EBA — Move to Modern DevOps | High | 4 repos trigger Move to Modern DevOps pathway (unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops). Key triggers: INF-Q6 < 3, OPS-Q1 < 3, OPS-Q10 < 3. | Request EBA engagement via SA for a 4-day guided workshop on CI/CD, observability, and deployment strategy. |
| EBA — Move to AI | High | All 5 repos trigger Move to AI pathway. Key triggers: APP-Q13 = 1/4, DATA-Q1 = 1/4, DATA-Q3 = 1/4 across all services. | Request EBA engagement via SA for a guided workshop on Amazon Bedrock integration, vector databases, and agent frameworks. |
| EBA — Move to Cloud Native | Medium | 2 repos trigger Move to Cloud Native (unishop-monolith, local-monolith). Key triggers: APP-Q4 < 4 (monolith decomposition), APP-Q3 = 1/4. | Request EBA engagement via SA for monolith decomposition strategy workshop using Strangler Fig pattern. |
| EBA — Move to Containers | Low | 1 repo triggers Move to Containers (unishop-monolith). Key trigger: INF-Q1 = 1/4 (raw EC2, no containers). | Request EBA engagement via SA for containerization workshop. |
| EBA — Move to Managed Databases | Low | 1 repo triggers Move to Managed Databases (unishop-monolith). Key triggers: INF-Q2 = 1/4, DATA-Q10 = 1/4 (MySQL management). | Request EBA engagement via SA for database migration planning. |

### Program Details

**Migration Acceleration Program (MAP)**: With all 5 services scoring below 2.5/4.0 and the portfolio requiring investment across infrastructure, security, observability, and AI capabilities, MAP provides migration credits and access to AWS Professional Services to accelerate the 6-month modernization roadmap. The portfolio's breadth of gaps (CI/CD, observability, security, AI) aligns well with MAP's holistic modernization support.

**EBA — Move to Modern DevOps**: The highest-value EBA engagement for this portfolio. With 80% of services lacking CI/CD pipelines and distributed tracing, a guided DevOps workshop would establish the foundational practices that enable all other modernization pathways. Suggested timing: Phase 0 (Month 1).

**EBA — Move to AI**: With 100% of services triggering Move to AI, this EBA engagement would provide guided implementation of Amazon Bedrock, vector databases, and agent frameworks. Suggested timing: Phase 2 (Months 2–3), after DevOps foundations are in place.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

## Integration Opportunities

### Shared Service Extraction

**Opportunity 1: Unified Observability Platform**
- Current State: 4 of 5 services have zero observability; only books-api has X-Ray tracing
- Proposed Solution: Deploy a shared observability stack — OpenTelemetry + X-Ray for tracing, JSON-formatted logging standard, CloudWatch dashboards per service, and a centralized alerting configuration
- Benefits: Consistent debugging experience, cross-service trace correlation, shared dashboard templates, reduced per-service setup cost
- Effort: Medium
- Priority: High

**Opportunity 2: Centralized Identity & Authentication**
- Current State: books-api has Cognito; aws-microservices and eks-saas-gitops have no auth; unishop-monolith has disabled OAuth2; local-monolith has session-based auth
- Proposed Solution: Deploy Amazon Cognito User Pools as the centralized identity provider for all services. Create shared JWT validation middleware per language (Java, TypeScript, PHP, Python).
- Benefits: Consistent auth across portfolio, SSO capability, agent identity propagation, reduced per-service implementation
- Effort: High
- Priority: High

**Opportunity 3: Shared Secrets Management Pattern**
- Current State: unishop-monolith has hardcoded credentials in plaintext; local-monolith has credentials in docker-compose.yml; no Secrets Manager usage across portfolio
- Proposed Solution: Establish AWS Secrets Manager as the standard for all services. Create shared IaC patterns (CDK constructs, Terraform modules, CloudFormation snippets) for secret management.
- Benefits: Eliminated credential exposure risk, automated rotation, consistent secret access patterns
- Effort: Low
- Priority: High

### Event-Driven Architecture

**Opportunity 1: Break Circular Dependency via EventBridge**
- Current State: books-api queries aws-microservices synchronously via REST for catalog data
- Proposed Solution: Replace the sync REST call with EventBridge events: aws-microservices publishes catalog updates to EventBridge, books-api subscribes and maintains a local cache (DynamoDB)
- Benefits: Decouples the two services, eliminates circular dependency, enables independent deployment
- Effort: Medium
- Priority: High

**Opportunity 2: Domain Event Standardization**
- Current State: aws-microservices uses EventBridge for checkout events; eks-saas-gitops uses SQS for tenant operations; other services have no event-driven patterns
- Proposed Solution: Define a portfolio-wide domain event schema standard (CloudEvents format). Use EventBridge as the shared event bus.
- Benefits: Consistent event format, cross-service event subscriptions, foundation for event-driven agent triggers
- Effort: Medium
- Priority: Medium

### Observability Unification

- Current State: books-api uses X-Ray; aws-microservices has no tracing; eks-saas-gitops mentions AMP/AMG but hasn't deployed them; unishop-monolith and local-monolith have zero observability
- Proposed Solution: Deploy a unified observability stack: X-Ray + OpenTelemetry for tracing, structured JSON logging to CloudWatch, Amazon Managed Grafana for dashboards, CloudWatch alarms for SLOs
- Benefits: End-to-end tracing across services, consistent metrics, shared dashboards, reduced tool sprawl
- Effort: High
- Priority: High

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + service teams (10+ cross-cutting concerns affect 3+ services)

**Platform Team**:
- Responsibilities: Shared observability platform, CI/CD pipeline templates, security baseline (Cognito, Secrets Manager), IaC standards, API documentation standards, shared vector database infrastructure, training
- Skills Required: IaC (Terraform + CDK), CI/CD (CodePipeline/GitHub Actions), OpenTelemetry/X-Ray, Amazon Cognito, Amazon Bedrock, CloudWatch

**Service Teams**:
- Responsibilities: Service-specific modernization, feature development, agent framework integration, domain-specific AI capabilities
- Skills Required: Language-specific expertise (Java/Spring Boot, TypeScript/Node.js, PHP, Python/Flask), DynamoDB/MySQL, service-specific testing

### Skill Gaps

1. **AI/Agent Frameworks**: Required for Phase 3 agent integration — no team currently has experience with Amazon Bedrock, Strands Agents SDK, LangChain, or RAG pipelines
2. **Observability (OpenTelemetry/X-Ray)**: Required for Phase 0–1 — only books-api team has X-Ray experience; other teams need training
3. **CI/CD Automation**: Required for Phase 0–1 — 3 of 5 services have no CI/CD; teams need CodePipeline/GitHub Actions skills
4. **Containerization (Docker/ECS)**: Required for Phase 1 — unishop-monolith team needs Docker and ECS/Fargate skills
5. **Security (Cognito/Secrets Manager)**: Required for Phase 0–1 — portfolio-wide need for JWT authentication and secrets management

### Training Recommendations

Phase 0–1 priorities: Modern DevOps (CI/CD, observability), containers, and security fundamentals
Phase 2–3 priorities: AI/agent frameworks, vector databases, and RAG implementation

### External Support

- Recommend AWS Professional Services or consulting partners for:
  - Phase 0 shared observability platform setup and CI/CD template creation (2–3 months)
  - Phase 1 unishop-monolith containerization and ECS deployment (complex legacy migration)
  - Phase 2–3 Amazon Bedrock and agent framework integration guidance (emerging technology)
  - Knowledge transfer sessions for all teams on new tooling and practices

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- EKS Workshop — https://www.eksworkshop.com/

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
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
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hardcoded credentials exploited (unishop-monolith SEC-Q1: 1/4, local-monolith SEC-Q1: 1/4) | High | High | **Phase 0**: Migrate all credentials to AWS Secrets Manager immediately. Rotate all exposed credentials. |
| Unauthenticated APIs abused (aws-microservices SEC-Q9: 1/4, eks-saas-gitops SEC-Q9: 1/4) | High | High | **Phase 0/1**: Implement Cognito JWT authentication on all API endpoints. |
| Circular dependency causes deployment failures (aws-microservices ↔ books-api) | Medium | Medium | **Phase 0**: Break circular dependency by replacing sync REST call with async EventBridge pattern. |
| Self-managed MySQL data loss (unishop-monolith INF-Q2: 1/4, no IaC confirms backups) | Medium | High | **Phase 1**: Define MySQL in IaC as RDS with Multi-AZ, automated backups, and encryption. |
| Observability blind spots hide agent failures (4 services OPS-Q1: 1/4) | High | High | **Phase 0–1**: Deploy unified tracing (OpenTelemetry + X-Ray) across all services. |
| No resilience patterns cause cascading failures (all 5 services APP-Q9: 1/4) | Medium | High | **Phase 2**: Implement circuit breakers, retries, and timeouts across all services. |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Skill fragmentation across 4 programming languages | High | Medium | Establish platform team with cross-language expertise. Invest in shared tooling that abstracts language differences. |
| No testing culture (4 services have zero tests) | High | Medium | Start testing in Phase 0–1 with books-api as the reference. Include test coverage gates in CI pipelines. |
| Lack of observability governance (no CODEOWNERS, no SLO owners) | High | Medium | Phase 2: Define service ownership, SLO ownership, and on-call responsibilities. |

### Dependency Risks

**Circular Dependency: aws-microservices ↔ books-api**
- Risk: Cannot independently deploy, test, or modernize these two services
- Likelihood: High (exists today)
- Impact: Medium (blocks 40% of portfolio)
- Mitigation: Phase 0 — Replace sync REST dependency with async EventBridge pattern

### Single Points of Failure

**unishop-monolith MySQL Database**
- No IaC confirms whether MySQL is RDS or self-managed
- No evidence of backups, failover, or encryption
- If self-managed on EC2: single instance with no HA
- Mitigation: Phase 1 — Define in IaC as RDS with Multi-AZ

**eks-saas-gitops Single NAT Gateway**
- `single_nat_gateway = true` creates a single point of failure for all EKS egress traffic
- Mitigation: Phase 2 — Enable multiple NAT Gateways across AZs

## Service-by-Service Summary

### unishop-monolith

- **Overall Score**: 1.21 / 4.0 ❌
- **Repository**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 1.0 / 4.0
  - Application: 1.23 / 4.0
  - Data: 1.82 / 4.0
  - Security: 1.0 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. SEC-Q1: Migrate hardcoded plaintext credentials to Secrets Manager
  2. INF-Q5: Create IaC for all infrastructure
  3. INF-Q6: Set up CI/CD pipeline
  4. INF-Q1: Containerize and deploy to ECS Fargate
  5. APP-Q2: Add OpenAPI documentation
- **Dependencies**: None
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps, Move to AI
- **Goal Alignment**: All pathways Medium (agentic-readiness)
- **Modernization Phase**: Phase 1 (Quick Wins)
- **Estimated Effort**: High

### aws-microservices

- **Overall Score**: 1.73 / 4.0 🟠
- **Repository**: ./services/aws-microservices
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 2.5 / 4.0
  - Application: 1.85 / 4.0
  - Data: 1.91 / 4.0
  - Security: 1.4 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. OPS category: Add tracing, logging, CI/CD, tests (all 1/4)
  2. SEC-Q9: Add API authentication to all endpoints
  3. SEC-Q3: Implement identity propagation (replace path-parameter user IDs)
  4. APP-Q2: Generate OpenAPI specs for Product, Basket, Order APIs
  5. APP-Q13: Add AI/agent framework integration
- **Dependencies**: books-api (sync REST — circular, resolved in Phase 0)
- **Depended On By**: books-api (async EventBridge)
- **Modernization Pathways**: Move to Modern DevOps, Move to AI
- **Goal Alignment**: All pathways Medium (agentic-readiness)
- **Modernization Phase**: Phase 1 (Quick Wins)
- **Estimated Effort**: Medium

### local-monolith

- **Overall Score**: 1.50 / 4.0 🟠
- **Repository**: ./monolith
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 2.1 / 4.0
  - Application: 1.3 / 4.0
  - Data: 1.7 / 4.0
  - Security: 1.5 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. APP-Q4: Begin monolith decomposition (single-file index.php with 7 domains)
  2. INF-Q6: Create CI/CD pipeline
  3. OPS-Q1: Add distributed tracing
  4. SEC-Q1: Migrate hardcoded secrets to Secrets Manager
  5. APP-Q13: Add AI/agent framework integration
- **Dependencies**: None
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native, Move to Modern DevOps, Move to AI
- **Goal Alignment**: All pathways Medium (agentic-readiness)
- **Modernization Phase**: Phase 1 (Quick Wins)
- **Estimated Effort**: High

### books-api

- **Overall Score**: 2.0 / 4.0 🟠
- **Repository**: ./services/books-api
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 2.5 / 4.0
  - Application: 1.9 / 4.0
  - Data: 1.9 / 4.0
  - Security: 2.0 / 4.0
  - Operations: 1.7 / 4.0
- **Top Priorities**:
  1. APP-Q13: Add AI/agent framework integration
  2. APP-Q2: Generate OpenAPI specification
  3. APP-Q8/SEC-Q5: Add API rate limiting
  4. DATA-Q1: Deploy vector database for semantic book search
  5. OPS-Q2: Add structured logging
- **Dependencies**: aws-microservices (async EventBridge — circular, resolved in Phase 0)
- **Depended On By**: aws-microservices (sync REST)
- **Modernization Pathways**: Move to AI
- **Goal Alignment**: All pathways Medium (agentic-readiness)
- **Modernization Phase**: Phase 2 (Foundation)
- **Estimated Effort**: Medium

### eks-saas-gitops

- **Overall Score**: 1.9 / 4.0 🟠
- **Repository**: ./services/eks-saas-gitops
- **Repository Type**: monorepo (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 2.7 / 4.0
  - Application: 2.2 / 4.0
  - Data: 1.9 / 4.0
  - Security: 1.3 / 4.0
  - Operations: 1.2 / 4.0
- **Top Priorities**:
  1. SEC-Q9: Add API authentication (currently unauthenticated, spoofable tenant headers)
  2. SEC-Q3: Implement JWT identity propagation replacing raw tenantID headers
  3. OPS-Q1: Add distributed tracing (OpenTelemetry + ADOT)
  4. APP-Q2: Generate OpenAPI specs for all microservices
  5. APP-Q13: Add AI/agent framework integration
- **Dependencies**: None
- **Depended On By**: None
- **Modernization Pathways**: Move to Modern DevOps, Move to AI
- **Goal Alignment**: All pathways Medium (agentic-readiness)
- **Modernization Phase**: Phase 2 (Foundation)
- **Estimated Effort**: High

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Repo Type | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------|-----------------|---------------|-------------|
| unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy | application | 2026-03-17 | 1.21 / 4.0 | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-assessment/MonoToMicroLegacy-agentic-readiness-report.md |
| aws-microservices | ./services/aws-microservices | application | 2026-03-17 | 1.73 / 4.0 | ./services/aws-microservices/agentic-readiness-assessment/aws-microservices-agentic-readiness-report.md |
| local-monolith | ./monolith | application | 2026-03-17 | 1.50 / 4.0 | ./monolith/agentic-readiness-assessment/monolith-agentic-readiness-report.md |
| books-api | ./services/books-api | application | 2026-03-17 | 2.0 / 4.0 | ./services/books-api/agentic-readiness-assessment/books-api-agentic-readiness-report.md |
| eks-saas-gitops | ./services/eks-saas-gitops | monorepo | 2026-03-17 | 1.9 / 4.0 | ./services/eks-saas-gitops/agentic-readiness-assessment/eks-saas-gitops-agentic-readiness-report.md |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - Migrate hardcoded credentials in unishop-monolith and local-monolith to AWS Secrets Manager
   - Secure eks-saas-gitops Argo Workflows server (change auth-mode from server to client, make internal)
   - Begin planning for breaking the aws-microservices ↔ books-api circular dependency

2. **Short-term (Month 1)**:
   - Create CI/CD pipeline templates for all 4 languages (Java, TypeScript, PHP, Python)
   - Deploy unified observability standards (OpenTelemetry + X-Ray tracing, JSON logging format)
   - Break the circular dependency between aws-microservices and books-api
   - Evaluate MAP eligibility with AWS account team
   - Request EBA engagement for Move to Modern DevOps

3. **Medium-term (Months 1–3)**:
   - Complete Phase 1 modernization for P0 services (unishop-monolith, aws-microservices, local-monolith)
   - Begin Phase 2 modernization for P1 services (books-api, eks-saas-gitops)
   - Deploy shared vector database (Bedrock Knowledge Bases)
   - Implement API authentication across all services via Amazon Cognito
   - Request EBA engagement for Move to AI

4. **Long-term (Months 3–6)**:
   - Integrate agent frameworks across the portfolio (Spring AI, LangChain.js, strands-agents)
   - Complete RAG pipelines for product catalog semantic search
   - Build automated evaluation frameworks for agent quality
   - Implement LLM cost tracking and human-in-the-loop approval workflows
   - Begin monolith decomposition (unishop-monolith, local-monolith)
   - Establish observability governance with SLO ownership
