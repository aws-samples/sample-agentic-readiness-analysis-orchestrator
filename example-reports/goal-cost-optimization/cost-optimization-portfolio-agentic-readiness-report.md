# Portfolio Agentic Readiness Assessment Report
**Portfolio**: cost-optimization
**Assessment Goal**: cost-optimization
**Goal Context**: Reducing licensing costs and migrating to managed and open-source services
**Services Assessed**: 3
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
   - Phase 1 — License & Quick Savings (Mo 1–2)
   - Phase 2 — Managed Service Migration (Mo 2–4)
   - Phase 3 — Optimization & Governance (Mo 4–6+)
6. AWS Modernization Pathways
7. AWS Programs & Engagement Recommendations
8. Integration Opportunities
9. Resource Allocation Recommendations
10. Recommended Self-Paced Learning Materials
11. Risk Analysis
12. Service-by-Service Summary
13. Appendix: Assessment Inventory

---

## Executive Dashboard

This portfolio of 3 e-commerce services scores **1.54 / 4.0** overall, indicating significant cost-optimization opportunities across compute, database management, and operational maturity. The portfolio spans three distinct technology stacks — a PHP monolith on App Runner (local-monolith), a Java Spring Boot monolith on raw EC2 with self-managed MySQL (unishop-monolith), and a serverless microservices application using Lambda and DynamoDB (aws-microservices). The most impactful cost-optimization target is **unishop-monolith**, which runs a self-managed MySQL database on EC2 with zero Infrastructure as Code, zero CI/CD, and zero observability — representing the highest operational overhead and cost risk in the portfolio.

The portfolio's greatest cost-optimization advantage is the **complete absence of commercial database licenses or proprietary SQL constructs** (DATA-Q11: 4.0/4.0 across all services). All three services use open-source database engines (MySQL or DynamoDB) with standard SQL, making managed-service migration straightforward. The most critical portfolio-wide gap is **Operations & Observability** (1.0/4.0 across all services) — all 12 operations criteria score 1/4 for every service, meaning zero CI/CD, zero observability, zero testing, and zero deployment automation exist anywhere in the portfolio. This operations gap drives hidden costs through manual deployments, extended incident resolution times, and inability to detect cost anomalies.

The recommended approach is a 6-month phased roadmap prioritizing: (1) establishing cross-cutting CI/CD, observability, and rate-limiting foundations (Phase 0), (2) quick cost wins including Lambda Graviton migration and secret management (Phase 1), (3) migrating the self-managed MySQL to Aurora and optimizing DynamoDB capacity (Phase 2), and (4) implementing cost governance, SLOs, and long-term optimization (Phase 3).

### Portfolio Readiness Score: 1.54 / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | 1.9 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 2 services, ❌ 1 service | 🟠 |
| Application Architecture | 1.59 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 1 service, ❌ 2 services | ❌ |
| Data Foundations | 1.86 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 2 services, ❌ 1 service | 🟠 |
| Identity, Security & Governance | 1.3 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 0 services, ❌ 3 services | ❌ |
| Operations & Observability | 1.0 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 0 services, ❌ 3 services | ❌ |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): 0 services (0%)
- 🟡 Partial (2.5-3.4): 0 services (0%)
- 🟠 Needs Work (1.5-2.4): 2 services (67%) — local-monolith (1.5), aws-microservices (1.8)
- ❌ Not Ready (< 1.5): 1 service (33%) — unishop-monolith (1.31)

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | 3 | 2 monoliths + 1 microservices application |
| Average Readiness Score | 1.54 / 4.0 | All services below "Partial" threshold — significant modernization needed |
| Services Ready for Agents | 0 (0%) | No service meets the 3.5 agent-ready threshold |
| Critical Dependencies | 1 | aws-microservices → local-monolith (sync product data query) |
| Shared Infrastructure Gaps | 15+ | CI/CD, observability, identity, rate limiting affect all 3 services |
| Self-Managed Databases | 1 | unishop-monolith — primary cost-optimization target |
| Estimated Modernization Effort | High | All services require foundational work across multiple categories |
| Expected Timeline | 6 months | 4 phases with 2 parallel tracks |

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- PHP 8.2: 1 service (33%) — local-monolith
- Java 8 / Spring Boot 2.1.6: 1 service (33%) — unishop-monolith
- JavaScript/TypeScript (Node.js 14.x): 1 service (33%) — aws-microservices

**Database Engines:**
- RDS MySQL 8.4.8 (managed): 1 service (33%) — local-monolith
- Self-managed MySQL on EC2 (version unknown, connector 8.0.11): 1 service (33%) — unishop-monolith ⚠️ **Primary cost-optimization target**
- DynamoDB on-demand (managed, serverless): 1 service (33%) — aws-microservices
- Self-managed databases: 1 of 3 (33%)
- Managed databases: 2 of 3 (67%)

**Compute Patterns:**
- Serverless (Lambda): 1 service (33%) — aws-microservices
- Managed Containers (App Runner): 1 service (33%) — local-monolith
- EC2 (raw): 1 service (33%) — unishop-monolith ⚠️ **No auto-scaling, no containerization**

**Infrastructure as Code:**
- CDK (TypeScript): 1 service (33%) — aws-microservices ✅ 100% IaC coverage
- CloudFormation: 1 service (33%) — local-monolith ✅ Comprehensive template
- None: 1 service (33%) — unishop-monolith ❌ Zero IaC

**Deployment Maturity:**
- Full CI/CD: 0 services (0%) ❌
- Partial CI/CD: 0 services (0%)
- Manual deployment: 3 services (100%) — deploy.sh, manual cdk deploy, manual JAR deployment

### Common Strengths

1. **No Stored Procedures or Proprietary SQL (DATA-Q11: 4.0/4.0)**: All 3 services use standard SQL with application-layer business logic. This is the single most important finding for cost optimization — database engine migration (MySQL → Aurora) requires minimal SQL translation.
2. **Structured JSON API Responses (APP-Q5: 3.7/4.0 avg)**: All services return well-structured JSON responses. local-monolith and aws-microservices score 4/4, unishop-monolith scores 3/4. This provides a solid API foundation.
3. **Managed Compute for 2 of 3 Services**: local-monolith (App Runner) and aws-microservices (Lambda) already run on managed, auto-scaling compute — only unishop-monolith requires compute modernization.
4. **Clean Data Ownership in Microservices (DATA-Q4: 4.0/4.0 for aws-microservices)**: The microservices architecture has clean service-per-table ownership with no cross-service data access.
5. **Simple Database Schemas**: All services have simple schemas (3-9 tables) with no complex relationships, triggers, or stored procedures — ideal for managed-service migration.

### Common Gaps

1. **Zero CI/CD Across the Entire Portfolio (INF-Q6: 1.0/4.0)**: Not a single service has automated build, test, or deploy pipelines. Every deployment is manual.
2. **Complete Absence of Observability (OPS: 1.0/4.0)**: No distributed tracing, no structured logging, no SLOs, no alarms, no dashboards, no anomaly detection in any service.
3. **No API Rate Limiting (APP-Q8/SEC-Q5: 1.0/4.0)**: No service has rate limiting at any layer — creating direct cost exposure from traffic spikes or abuse.
4. **No Centralized Identity (SEC-Q10: 1.0/4.0)**: Each service has its own auth approach (PHP sessions, disabled OAuth2, no auth). No shared identity provider.
5. **No API Documentation (APP-Q2: 1.0/4.0)**: No OpenAPI specs, no Swagger, no machine-readable API docs in any service.
6. **No Integration Testing (OPS-Q10: 1.0/4.0)**: Zero test coverage across all services. No unit tests, no integration tests, no end-to-end tests.
7. **Hardcoded Credentials in Monoliths (SEC-Q1)**: Both local-monolith and unishop-monolith have hardcoded database credentials in source code or configuration files.

## Service Dependency Map

### High-Level Architecture

The portfolio consists of three independent e-commerce applications that serve different aspects of the business. There is one explicit cross-service dependency: aws-microservices queries local-monolith synchronously for legacy product data during a data migration period. Both monoliths (local-monolith and unishop-monolith) are fully independent with no shared databases or infrastructure. The aws-microservices application is the most architecturally advanced, using event-driven patterns (EventBridge → SQS) for inter-service communication within its own microservices boundary.

### Service Dependency Matrix

| Service | Depends On | Depended On By | Fan-In | Fan-Out | Coupling Score | Blast Radius | Priority |
|---------|------------|----------------|--------|---------|----------------|--------------|----------|
| local-monolith | None | aws-microservices | 1 | 0 | — | 33% (1 service) | P0 |
| unishop-monolith | None | None | 0 | 0 | — | 0% (isolated) | P0 |
| aws-microservices | local-monolith | None | 0 | 1 | Medium | 0% | P1 |

**Coupling Score Definitions:**
- High: Synchronous dependencies, shared databases, tight coupling
- Medium: Async dependencies, some shared infrastructure
- Low: Minimal dependencies, loose coupling

**Priority Definitions:**
- P0: Critical path services that block others or have highest cost-optimization impact
- P1: Important services with moderate dependencies
- P2: Leaf services with minimal dependencies

### Critical Path Analysis

1. **Foundation Services** (must be modernized first):
   - **local-monolith** (P0, fan-in=1): aws-microservices depends on this service for product data queries. Modernization of local-monolith must proceed first or in parallel to avoid blocking downstream work. As a foundation service, its stability directly impacts aws-microservices.

2. **Independent Services** (can be parallelized):
   - **unishop-monolith** (P0, fan-in=0): Fully isolated with no dependents. Can be modernized on an independent track in parallel with local-monolith. Has the lowest score (1.31/4.0) and the most significant cost-optimization opportunity (self-managed MySQL → Aurora).

3. **Dependent Services** (can be modernized after foundation):
   - **aws-microservices** (P1, fan-out=1): Depends on local-monolith. Quick wins (Lambda runtime upgrade, throttling) can proceed immediately, but deeper integration work should wait until local-monolith is stable.

### Integration Points

**Synchronous Integrations:**
- aws-microservices → local-monolith: REST API call for legacy product data query during migration. Type: Synchronous HTTP. Coupling: Medium. Risk: If local-monolith is unavailable, aws-microservices product queries fail.

**Asynchronous Integrations:**
- Within aws-microservices: Basket Service → EventBridge → SQS → Ordering Service (checkout flow). This is internal to the aws-microservices boundary, not cross-portfolio.

**Shared Infrastructure:**
- None identified. Each service operates on independent infrastructure. No shared databases, no shared API gateways, no shared message queues between portfolio services.

---

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are classified into four tiers based on severity and relationship to the portfolio's assessment goal (`cost-optimization`).

### 🚨 Foundational Blockers

> These gaps block all modernization efforts, not just `cost-optimization`.
> Address these first — nothing else matters until these are resolved.

1. **INF-Q6: CI/CD Automation** — 3 of 3 services score < 2
   - **Impact**: No automated pipelines exist anywhere in the portfolio. Every deployment is manual — `deploy.sh`, `cdk deploy`, manual JAR copying. This blocks all other modernization because infrastructure changes, database migrations, and application updates cannot be safely automated, tested, or rolled back. Manual deployments directly increase operational labor costs and deployment failure risk.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Establish reusable CI/CD pipeline templates (GitHub Actions reusable workflows or CodePipeline templates) in Phase 0. Each service adopts the shared template with service-specific configuration. Include cost estimation checks (e.g., `cdk diff` output review) in the pipeline.

2. **OPS-Q1: Distributed Tracing** — 3 of 3 services score < 2
   - **Impact**: Zero observability into request flows across the portfolio. Without tracing, production incidents require expensive manual investigation. Cost anomalies (runaway Lambda invocations, DynamoDB scan storms) go undetected for hours or days. This is a direct cost driver — every minute of undetected anomaly increases the bill.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Enable AWS X-Ray across all services in Phase 0. For aws-microservices, add `tracing: Tracing.ACTIVE` (one-line CDK change). For local-monolith, enable X-Ray in App Runner. For unishop-monolith, add X-Ray Java agent when containerizing on ECS.

3. **APP-Q8 + SEC-Q5: Rate Limiting** — 3 of 3 services score < 2 on both criteria
   - **Impact**: No rate limiting at any layer in any service. Combined with missing authentication on 2 of 3 services, the portfolio is fully exposed to denial-of-wallet attacks where abusive traffic drives unbounded compute and database costs. This is the highest immediate cost risk in the portfolio.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Add WAF rate-based rules to local-monolith's existing WAF. Add API Gateway throttling (`deployOptions`) to aws-microservices. Add ALB/API Gateway with throttling for unishop-monolith when implementing the API entry point. All in Phase 0.

### ⚠️ Prerequisites for `cost-optimization`

> These gaps specifically block your path to `cost-optimization`.
> They aren't the goal itself, but you can't get there without them.

No criteria met the Tier 2 threshold for `cost-optimization`. The Tier 2 criteria for cost-optimization are INF-Q5 (IaC, threshold < 3) and OPS-Q1 (observability, threshold < 3). OPS-Q1 was already classified as Tier 1 (foundational blocker). INF-Q5 has only 1 service scoring < 3 (unishop-monolith at 1/4), which does not meet the 2-service minimum for Tier 2 classification. The IaC gap for unishop-monolith is addressed in its individual service roadmap.

### 🎯 Goal Deliverables — What You're Here to Build

> These are the capabilities your `cost-optimization` initiative will deliver.
> Low scores here confirm the need for the initiative, not additional blockers.
> Your individual assessment reports detail the current state and roadmap for each.

1. **INF-Q8: Real-time Streaming / Managed Analytics** — 3 of 3 services score < 3
   - **Current state**: No streaming infrastructure exists in any service. All data flows are synchronous database writes. None of the services use Kinesis, MSK, or managed streaming services. While streaming is not an immediate cost driver, the absence means real-time cost monitoring, event-driven architectures, and managed analytics pipelines are not available.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Roadmap reference**: Phase 3 — evaluate streaming needs as part of architecture optimization

2. **DATA-Q2: Vector DB Management (Managed Services)** — 3 of 3 services score < 3
   - **Current state**: No vector databases exist in the portfolio. While not a direct cost-optimization target, this criterion reflects the portfolio's position on the spectrum of managed data service adoption. When vector databases are needed for AI/search capabilities, the cost-optimization preference is to use managed services (OpenSearch Serverless, Aurora pgvector) rather than self-managed alternatives.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Roadmap reference**: Phase 3 — evaluate when AI capabilities are pursued

### 💡 General Improvement Opportunities

> These gaps are important but do not directly block `cost-optimization`.
> Address them as capacity allows or in parallel with goal work.

1. **OPS-Q2: Structured Logging** — 3 of 3 services score < 3
   - **Impact**: Unstructured logging across all services. local-monolith uses `ini_set('log_errors')`, unishop-monolith uses `System.out.println()` and `e.printStackTrace()`, aws-microservices uses `console.log()`. Without structured JSON logs, CloudWatch Logs Insights queries cannot efficiently identify cost-driving operations.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Establish portfolio-wide structured logging standard (JSON format, correlation IDs) in Phase 0. Each service adopts the appropriate library: Monolog (PHP), Logback (Java), Powertools Logger (Node.js).

2. **OPS-Q4: SLOs** — 3 of 3 services score < 3
   - **Impact**: No SLO definitions, no CloudWatch alarms, no error budget tracking. Without SLOs, cost-vs-quality tradeoffs cannot be made data-driven.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Define portfolio-wide SLO standards (p99 latency, error rate, availability) in Phase 2. Create CloudWatch alarms for each service.

3. **OPS-Q5: Rollback Capability** — 3 of 3 services score < 3
   - **Impact**: No automated rollback for any service. Failed deployments require manual intervention, causing extended downtime and associated revenue loss.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Configure rollback mechanisms as part of CI/CD establishment: App Runner automatic rollback, ECS deployment circuit breaker, Lambda alias-based canary deployments.

4. **OPS-Q7 through OPS-Q12: Operations Maturity** — 3 of 3 services score < 3 on all criteria
   - **Impact**: Complete absence of business metrics (OPS-Q7), anomaly detection (OPS-Q8), deployment strategy (OPS-Q9), integration testing (OPS-Q10), incident response automation (OPS-Q11), and observability governance (OPS-Q12) across the entire portfolio.
   - **Affected services**: All 3 services score 1/4 on all operations criteria
   - **Recommendation**: Address progressively — testing and deployment strategy in Phase 1, business metrics and anomaly detection in Phase 2, advanced operations in Phase 3.

5. **APP-Q2: API Documentation** — 3 of 3 services score < 3
   - **Impact**: No machine-readable API specs anywhere. Increases integration costs and prevents automated SDK generation.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Generate OpenAPI 3.0 specs for each service in Phase 2.

6. **APP-Q11: API Versioning** — 3 of 3 services score < 3
   - **Impact**: No versioning strategy. Breaking API changes affect all consumers simultaneously.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Adopt URL-path versioning (`/api/v1/`) when establishing API Gateway in Phase 2.

7. **APP-Q13: AI/Agent Frameworks** — 3 of 3 services score < 3
   - **Impact**: No AI capabilities anywhere. Low priority for cost-optimization goal.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Defer to Phase 3. Evaluate ROI of AI features after operational foundations are solid.

8. **SEC-Q1: Secret Management** — 3 of 3 services score < 3
   - **Impact**: Both monoliths have hardcoded credentials. aws-microservices uses IAM roles (better) but has no Secrets Manager. Credential exposure risk drives potential breach costs.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (2/4)
   - **Recommendation**: Migrate to AWS Secrets Manager in Phase 1 for both monoliths.

9. **SEC-Q4: Audit Logging** — 3 of 3 services score < 3
   - **Impact**: No CloudTrail, no application-level audit logging. Cannot determine who accessed what data.
   - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
   - **Recommendation**: Enable CloudTrail and set CloudWatch Logs retention policies in Phase 1.

10. **SEC-Q6: PII Redaction** — 3 of 3 services score < 3
    - **Impact**: PII (emails, addresses, card info) logged in plaintext. Error stack traces exposed to API consumers.
    - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
    - **Recommendation**: Add PII masking to structured logging implementation in Phase 1.

11. **SEC-Q9: API Authentication** — 3 of 3 services score < 3
    - **Impact**: unishop-monolith and aws-microservices have no authentication. local-monolith uses PHP sessions. Unauthenticated APIs create cost risk.
    - **Affected services**: local-monolith (2/4), unishop-monolith (1/4), aws-microservices (1/4)
    - **Recommendation**: Deploy shared Cognito User Pool in Phase 2. Integrate with all services.

12. **SEC-Q10: Centralized Identity** — 3 of 3 services score < 3
    - **Impact**: No centralized identity. Each service manages users differently or not at all.
    - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
    - **Recommendation**: Shared Cognito User Pool addresses both SEC-Q9 and SEC-Q10.

13. **DATA-Q1: Vector Database** — 3 of 3 services score < 3
    - **Impact**: No vector database. Low priority for cost-optimization.
    - **Affected services**: local-monolith (1/4), unishop-monolith (1/4), aws-microservices (1/4)
    - **Recommendation**: Defer to Phase 3 when AI capabilities are evaluated.

### Per-Category Analysis

### Infrastructure & Platform

**Portfolio Score: 1.9 / 4.0**

Infrastructure maturity varies significantly across the portfolio. aws-microservices leads with 2.6/4.0 (100% serverless, 100% IaC, auto-scaling DynamoDB and Lambda), followed by local-monolith at 2.1/4.0 (App Runner managed compute, RDS MySQL, CloudFormation IaC). unishop-monolith trails at 1.0/4.0 with raw EC2, self-managed MySQL, zero IaC, and zero CI/CD.

**Common Patterns:**
- Manual deployment: All 3 services (100%)
- No real-time streaming: All 3 services (100%)
- No async messaging: 2 of 3 services (local-monolith, unishop-monolith)

**Critical Gaps:**
1. **No CI/CD (INF-Q6)**: Affects all 3 services. Portfolio-level solution: shared CI/CD pipeline templates.
2. **Self-managed compute (INF-Q1)**: unishop-monolith on raw EC2. Containerize on ECS Fargate with Graviton for 20-40% cost savings.
3. **Self-managed database (INF-Q2)**: unishop-monolith self-managed MySQL. Migrate to Aurora MySQL/PostgreSQL.

### Application Architecture

**Portfolio Score: 1.59 / 4.0**

Architecture patterns span the full spectrum: local-monolith is a tightly-coupled single-file PHP monolith (APP-Q4: 1/4), unishop-monolith is a modular Spring Boot monolith (APP-Q4: 2/4), and aws-microservices is a well-decomposed microservices architecture (APP-Q4: 4/4). The portfolio universally lacks API documentation, versioning, rate limiting, and AI frameworks.

**Common Patterns:**
- JSON API responses: All 3 services ✅
- No API documentation: All 3 services ❌
- No rate limiting: All 3 services ❌

**Critical Gaps:**
1. **No API documentation (APP-Q2)**: Affects all 3 services. Generate OpenAPI specs for each service.
2. **No rate limiting (APP-Q8)**: Affects all 3 services. Add at API Gateway/WAF level.

### Data Foundations

**Portfolio Score: 1.86 / 4.0**

Data architecture is the strongest area relative to the cost-optimization goal. The critical finding is DATA-Q11: 4.0/4.0 — no stored procedures or proprietary SQL constructs exist anywhere, making database migration straightforward. aws-microservices has the cleanest data architecture (DynamoDB with clean service-per-table ownership). unishop-monolith has well-structured repository/MyBatis patterns. local-monolith has scattered raw SQL queries that should be refactored.

**Common Patterns:**
- Standard SQL / no stored procedures: All 3 services ✅ (4.0/4.0)
- No vector database: All 3 services (not needed for current use cases)

**Critical Gaps:**
1. **Self-managed database (INF-Q2 via DATA)**: unishop-monolith. Migrate to Aurora MySQL.
2. **No schema documentation (DATA-Q7)**: local-monolith has inline PHP schema, unishop-monolith has SQL file, aws-microservices has code comments only.

### Identity, Security & Governance

**Portfolio Score: 1.3 / 4.0**

Security is the weakest category after Operations. All services lack centralized identity (SEC-Q10: 1.0/4.0), audit logging (SEC-Q4: 1.0/4.0), PII redaction (SEC-Q6: 1.0/4.0), and rate limiting (SEC-Q5: 1.0/4.0). Both monoliths have hardcoded credentials. The strongest security posture is aws-microservices which uses IAM roles for DynamoDB access (SEC-Q2: 3/4).

**Common Patterns:**
- No centralized identity: All 3 services
- No PII redaction: All 3 services
- IAM least-privilege in serverless: aws-microservices (3/4)

**Critical Gaps:**
1. **No centralized identity (SEC-Q10)**: Portfolio-wide Cognito deployment needed.
2. **Hardcoded credentials (SEC-Q1)**: Both monoliths. Migrate to Secrets Manager.
3. **No rate limiting (SEC-Q5)**: All services exposed to abuse.

### Operations & Observability

**Portfolio Score: 1.0 / 4.0**

Operations is the most critical portfolio-wide gap. Every single operations criterion (all 12) scores 1/4 across all 3 services. There is zero observability, zero testing, zero deployment automation, zero incident response, and zero operational governance anywhere in the portfolio. This is the single largest hidden cost driver — incidents take longer to detect, diagnose, and resolve, driving up labor costs and customer impact.

**Common Patterns:**
- None. There are no operational capabilities to identify as patterns.

**Critical Gaps:**
1. **All 12 operations criteria score 1/4 across all 3 services**. This is a systematic organizational gap, not a service-specific issue. The portfolio has never invested in operational maturity.
2. **Recommendation**: Address in Phase 0 (CI/CD, tracing, logging) and progressively through Phase 1-3.

---

## Portfolio Modernization Roadmap

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: local-monolith (foundation service) before aws-microservices deep work
3. **Risk Mitigation**: Rate limiting and observability first to prevent cost overruns during migration
4. **Parallel Tracks**: unishop-monolith can be modernized independently in parallel with local-monolith
5. **Quick Wins**: Lambda Graviton migration, log retention, throttling deliver immediate cost savings
6. **Goal Alignment**: Within each phase, cost-optimization priority activities (managed DB migration, licensing reduction) are listed first

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities that protect against cost overruns and enable safe modernization across all services.

**Shared Infrastructure:**
- **CI/CD Pipeline Templates**: Create reusable GitHub Actions workflow templates or CodePipeline patterns for all 3 services. Include lint → test → build → deploy stages with cost estimation checks. Benefits all 3 services.
- **Observability Standards**: Define portfolio-wide structured logging standard (JSON format with correlation IDs). Establish CloudWatch dashboard templates. Enable X-Ray tracing across all services.
- **Rate Limiting / Cost Protection**: Add WAF rate-based rules to local-monolith. Add API Gateway throttling to aws-microservices. Plan ALB with throttling for unishop-monolith.

**Platform Capabilities:**
- Cost allocation tagging strategy: Define mandatory tags (team, environment, application, cost-center) for all IaC resources
- CloudWatch Logs retention policies: Set 30-90 day retention to stop indefinite log accumulation costs

**Organizational Enablers:**
- Training: IaC (CDK/CloudFormation), CI/CD (GitHub Actions), observability (X-Ray/CloudWatch)
- Standards: Logging format, tagging policy, deployment checklist, CODEOWNERS files
- Cost governance: AWS Budgets alerts, Cost Anomaly Detection enrollment

**Expected Outcomes:**
- All 3 services have CI/CD pipelines (even if basic)
- X-Ray tracing enabled across all services
- Rate limiting prevents cost overruns
- Cost allocation tags enable per-service cost tracking

**Estimated Effort**: High

### Phase 1 — License & Quick Savings (Mo 1–2)

**Objective**: Deliver immediate cost savings through quick wins and prepare foundations for managed service migration. Cost-optimization priority activities listed first.

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.31/4.0)
   - Current State: Java 8 / Spring Boot 2.1 monolith on raw EC2, self-managed MySQL, zero IaC, hardcoded credentials
   - Target State: Containerized application with IaC, secrets in Secrets Manager, Aurora migration plan in place
   - Key Activities (cost-optimization priorities first):
     - Begin Aurora MySQL provisioning planning (evaluate Aurora MySQL vs Aurora PostgreSQL)
     - Create Dockerfile from existing bootJar output (prerequisite for ECS Fargate + Graviton cost savings)
     - Implement baseline IaC (CDK or CloudFormation) with cost allocation tags
     - Move hardcoded credentials from `application.properties` to Secrets Manager
     - Add structured logging (logback-spring.xml with JSON format)
   - Dependencies: None (isolated service)
   - Blocks: None
   - Estimated Effort: High

2. **local-monolith** (P0, Score: 1.5/4.0)
   - Current State: PHP 8.2 monolith on App Runner, RDS MySQL 8.4.8, CloudFormation IaC, hardcoded credentials, WAF with IP whitelisting only
   - Target State: Secrets secured, rate limiting active, Aurora migration plan in place
   - Key Activities (cost-optimization priorities first):
     - Begin Aurora MySQL/PostgreSQL Serverless v2 migration planning
     - Store database credentials in Secrets Manager (remove hardcoded defaults from index.php)
     - Add WAF rate-based rules to existing WAF Web ACL
     - Replace `die()` with proper error handling
     - Add basic PHPUnit integration tests for critical API endpoints
   - Dependencies: None
   - Blocks: aws-microservices (sync dependency on product data)
   - Estimated Effort: Medium

3. **aws-microservices** (P1, Score: 1.8/4.0)
   - Current State: Serverless Lambda + DynamoDB + EventBridge + SQS, no CI/CD, no auth, EOL Node.js 14.x runtime
   - Target State: Updated runtime with Graviton, throttling active, log retention set, cost-protected
   - Key Activities (cost-optimization priorities first):
     - Upgrade Lambda runtime Node.js 14→20 + ARM64/Graviton (~20% Lambda cost savings)
     - Set CloudWatch Logs retention to 30 days (stop indefinite log cost growth)
     - Add API Gateway throttling (`deployOptions` with rate/burst limits)
     - Set Lambda reserved concurrency limits
     - Remove error stack traces from API responses
     - Add Powertools for AWS Lambda structured logging
   - Dependencies: local-monolith (sync — product data queries)
   - Blocks: None
   - Estimated Effort: Low

**Expected Outcomes:**
- ~20% Lambda cost reduction via Graviton (aws-microservices)
- Credential exposure risk eliminated (both monoliths)
- Cost protection active via throttling and log retention
- unishop-monolith ready for containerization

**Estimated Effort**: High

### Phase 2 — Managed Service Migration (Mo 2–4)

**Objective**: Migrate to managed services for reduced operational costs. Cost-optimization priority activities listed first.

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.31/4.0)
   - Current State: Dockerfile created, IaC in place (from Phase 1)
   - Target State: Running on ECS Fargate with Graviton, Aurora MySQL, ALB, full CI/CD
   - Key Activities (cost-optimization priorities first):
     - **Migrate self-managed MySQL to Aurora MySQL** using AWS DMS (zero-downtime). Pin engine version in IaC. Enable encryption at rest. Simple schema (3 tables, no stored procedures) = low-risk migration.
     - Deploy to ECS Fargate with Graviton (ARM64) task definitions (~20% compute cost savings)
     - Implement ALB with health checks using existing `/health/ishealthy` endpoint
     - Configure ECS Service Auto Scaling with target tracking on CPU/memory
     - Complete CI/CD pipeline with deploy-to-ECS stage and deployment circuit breaker
     - Add integration tests for critical API endpoints
   - Dependencies: Phase 1 IaC and Dockerfile
   - Blocks: None
   - Estimated Effort: High

2. **local-monolith** (P0, Score: 1.5/4.0)
   - Current State: RDS MySQL 8.4.8, App Runner, CloudFormation IaC
   - Target State: Aurora MySQL/PostgreSQL Serverless v2, optimized compute, full observability
   - Key Activities (cost-optimization priorities first):
     - **Migrate RDS MySQL to Aurora MySQL Serverless v2** — auto-scaling from 0.5 to 128 ACUs eliminates fixed-instance over-provisioning. Built-in Multi-AZ provides automatic failover.
     - Implement data access layer (repository pattern per domain) — prerequisite for future Aurora PostgreSQL migration
     - Enable X-Ray distributed tracing in App Runner
     - Define SLOs and create CloudWatch alarms (p99 latency, error rate)
     - Add CloudTrail for audit logging
   - Dependencies: Phase 1 secrets migration
   - Blocks: aws-microservices
   - Estimated Effort: Medium

3. **aws-microservices** (P1, Score: 1.8/4.0)
   - Current State: Lambda with Graviton (from Phase 1), DynamoDB on-demand, no auth
   - Target State: Authenticated APIs, DynamoDB optimized, SQS DLQ, full observability
   - Key Activities (cost-optimization priorities first):
     - **DynamoDB capacity optimization analysis** — analyze usage patterns from Phase 1 CloudWatch data. If traffic is predictable, switch to provisioned capacity with auto-scaling (50-70% cost reduction vs on-demand).
     - Add Cognito User Pool authorizer to all API Gateway endpoints (prevents unauthorized invocation costs)
     - Add SQS Dead-Letter Queue to OrderQueue (prevents silent order loss)
     - Increase SQS batch size from 1 to 10 (reduces Lambda invocation count and costs)
     - Implement CDK infrastructure tests and Lambda handler unit tests
     - Add CloudWatch alarms for error rates, DynamoDB throttling, SQS DLQ depth
   - Dependencies: local-monolith (sync dependency)
   - Blocks: None
   - Estimated Effort: Medium

**Expected Outcomes:**
- Self-managed MySQL eliminated (unishop-monolith → Aurora)
- RDS MySQL upgraded to Aurora Serverless v2 (local-monolith — pay-per-use)
- unishop-monolith compute costs reduced 20-40% (EC2 → ECS Fargate + Graviton)
- DynamoDB costs potentially reduced 50-70% (on-demand → provisioned if applicable)
- Authentication prevents unauthorized API invocation costs

**Estimated Effort**: High

### Phase 3 — Optimization & Governance (Mo 4–6+)

**Objective**: Establish long-term cost governance and optimize the fully operational portfolio. Cost-optimization priority activities listed first.

**Activities:**

**Cost Governance & Optimization (priority):**
- Enable Aurora Serverless v2 auto-scaling tuning based on production data
- Right-size ECS Fargate task definitions based on 30+ days of utilization data
- Implement AWS Budgets with per-service cost alerts using cost allocation tags
- Enable AWS Cost Anomaly Detection for automated cost spike detection
- Replace DynamoDB `ScanCommand` with `QueryCommand` + GSIs in aws-microservices (reduces read capacity costs)

**Operational Maturity:**
- Implement SLOs with error budgets across all services
- Publish custom business metrics to CloudWatch (orders/hour, revenue, fulfillment time)
- Enable CloudWatch anomaly detection on key metrics
- Create operational runbooks for common failure scenarios

**Architecture Optimization (lower priority for cost-optimization):**
- Evaluate Aurora PostgreSQL migration for local-monolith (enables pgvector for future AI, better cost-performance for complex queries)
- Plan Spring Boot 2.1 → 3.x upgrade for unishop-monolith (enables modern ecosystem)
- Evaluate service decomposition for both monoliths (independent scaling reduces over-provisioning)
- Evaluate event-driven replacement for aws-microservices → local-monolith sync dependency

**Expected Outcomes:**
- Per-service cost tracking and alerting active
- Cost anomalies detected automatically
- Data-driven right-sizing based on production utilization
- Portfolio-wide cost governance framework established

**Estimated Effort**: Medium

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6 months (with 2 parallel tracks: unishop-monolith + local-monolith in parallel)

---

## AWS Modernization Pathways

Based on the portfolio-wide assessment findings, the following AWS Modernization Pathways have been identified for each service. The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach — a customer portfolio may be divided into multiple pathways depending on workloads and priorities, and these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Goal Alignment | Est. Effort |
|---------|--------------------|----------------|----------|----------------|-------------|
| Move to Cloud Native | 2 services | 67% | High | Low | High |
| Move to Containers | 1 service | 33% | Medium | Medium | Medium |
| Move to Open Source | 0 services | 0% | Low | High | — |
| Move to Managed Databases | 1 service | 33% | Medium | High | Medium |
| Move to Managed Analytics | 0 services | 0% | Low | High | — |
| Move to Modern DevOps | 3 services | 100% | High | Medium | High |
| Move to AI | 3 services | 100% | High | Low | Medium |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| local-monolith | ✅ | — | — | — | — | ✅ | ✅ |
| unishop-monolith | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| aws-microservices | — | — | — | — | — | ✅ | ✅ |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing a single at-a-glance view of pathway coverage across the portfolio. Each repo appears in exactly one column per pathway row. Goal Alignment is based on the portfolio-level goal (`cost-optimization`) using the goal-pathway alignment mapping.

| Pathway | Triggered | Not Triggered | Not Applicable | Goal Alignment |
|---------|-----------|---------------|----------------|---------------|
| Move to Cloud Native | local-monolith, unishop-monolith | aws-microservices | — | Low |
| Move to Containers | unishop-monolith | local-monolith, aws-microservices | — | Medium |
| Move to Open Source | — | local-monolith, unishop-monolith, aws-microservices | — | High |
| Move to Managed Databases | unishop-monolith | local-monolith, aws-microservices | — | High |
| Move to Managed Analytics | — | local-monolith, unishop-monolith, aws-microservices | — | High |
| Move to Modern DevOps | local-monolith, unishop-monolith, aws-microservices | — | — | Medium |
| Move to AI | local-monolith, unishop-monolith, aws-microservices | — | — | Low |

**Validation**: Each of the 7 pathway rows contains all 3 repos across the Triggered + Not Triggered + Not Applicable columns. ✅

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native for unishop-monolith — must containerize the application before decomposing it into microservices
- Move to Modern DevOps enables faster execution of all other pathways — CI/CD pipelines are required to safely deploy infrastructure changes (Aurora migration, ECS deployment)
- Move to Managed Databases (Aurora) and Move to Containers (ECS Fargate) are prerequisites for fully realizing Move to Cloud Native benefits

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps — all 3 services, start immediately. No dependencies on other pathways.
- **Track 2**: Move to Containers + Move to Managed Databases — unishop-monolith, in parallel with Track 1. Containerize and migrate database concurrently.
- **Track 3**: Move to Cloud Native — Phase 3, after Tracks 1 and 2 complete. Decompose monoliths into microservices.
- **Track 4**: Move to AI — Phase 3, lowest priority for cost-optimization. Evaluate ROI after foundations are solid.

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: local-monolith, unishop-monolith, aws-microservices (3 total)
- **Portfolio Priority**: High (100% of services triggered)
- **Goal Alignment**: Medium
- **Common Trigger Criteria**:
  - INF-Q6 (CI/CD) score 1/4: affects 3 services
  - OPS-Q9 (Deployment Strategy) score 1/4: affects 3 services
  - OPS-Q10 (Integration Testing) score 1/4: affects 3 services
  - OPS-Q1 (Distributed Tracing) score 1/4: affects 3 services
- **Representative AWS Services**: CodePipeline, CodeBuild, CodeDeploy, CloudFormation, CDK, X-Ray, CloudWatch
- **Key Activities**:
  1. Establish reusable CI/CD pipeline templates across portfolio
  2. Enable X-Ray distributed tracing on all services
  3. Implement structured logging standards with CloudWatch Logs Insights
  4. Add integration tests per service
  5. Configure automated rollback mechanisms
- **Cross-Service Synergies**: CI/CD pipeline templates can be shared. Observability dashboard patterns reusable. Testing patterns transferable across languages.
- **Estimated Effort**: High across 3 services
- **Roadmap Phase Alignment**: Phase 0 and Phase 1
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to Managed Databases

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Medium (33% of services, but High goal alignment)
- **Goal Alignment**: High
- **Common Trigger Criteria**:
  - INF-Q2 (Databases) score 1/4: affects 1 service (self-managed MySQL)
  - DATA-Q10 (DB Engine EOL) score 2/4: affects 1 service (unpinned MySQL version)
- **Representative AWS Services**: Aurora MySQL, Aurora PostgreSQL, DMS, RDS
- **Key Activities**:
  1. Provision Aurora MySQL cluster with IaC
  2. Use AWS DMS for zero-downtime migration from self-managed MySQL
  3. Enable encryption at rest with AWS-managed KMS keys (free)
  4. Pin engine version in IaC
  5. Evaluate Aurora Serverless v2 for auto-scaling
- **Cross-Service Synergies**: Aurora migration patterns from unishop-monolith can inform local-monolith's future Aurora migration. DMS expertise is reusable.
- **Estimated Effort**: Medium (simple 3-table schema, no stored procedures)
- **Roadmap Phase Alignment**: Phase 2
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Containers

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Medium (33% of services)
- **Goal Alignment**: Medium
- **Common Trigger Criteria**:
  - INF-Q1 (Compute) score 1/4: raw EC2 with no container orchestration
  - No Dockerfile found in repository
- **Representative AWS Services**: ECS, Fargate, ECR, Graviton
- **Key Activities**:
  1. Create Dockerfile from existing bootJar output
  2. Build and push image to Amazon ECR
  3. Create ECS Fargate task definition with ARM64/Graviton (~20% cost savings)
  4. Configure ECS Service Auto Scaling
  5. Implement ALB for health checking and load distribution
- **Cross-Service Synergies**: local-monolith already has a Dockerfile and runs on App Runner — containerization patterns can be shared.
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Dockerfile) and Phase 2 (ECS deployment)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

#### Move to Cloud Native

- **Services Affected**: local-monolith, unishop-monolith (2 total)
- **Portfolio Priority**: High (67% of services, but Low goal alignment)
- **Goal Alignment**: Low
- **Common Trigger Criteria**:
  - APP-Q4 (Monolith vs Microservices): local-monolith 1/4, unishop-monolith 2/4
  - APP-Q3 (Async Communication): local-monolith 1/4, unishop-monolith 1/4
  - INF-Q1 (Compute): unishop-monolith 1/4
- **Representative AWS Services**: Lambda, API Gateway, Step Functions, EventBridge, SQS, ECS
- **Key Activities**:
  1. Containerize monoliths as-is first (prerequisite)
  2. Identify bounded contexts for decomposition
  3. Extract first candidate service using Strangler Fig pattern
  4. Introduce async messaging (SQS/EventBridge) between extracted services
- **Cross-Service Synergies**: aws-microservices provides a reference architecture for event-driven microservices (EventBridge + SQS pattern already proven).
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 3 (lower priority for cost-optimization)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

#### Move to AI

- **Services Affected**: local-monolith, unishop-monolith, aws-microservices (3 total)
- **Portfolio Priority**: High (100% of services, but Low goal alignment)
- **Goal Alignment**: Low
- **Common Trigger Criteria**:
  - APP-Q13 (AI/Agent Frameworks) score 1/4: affects 3 services
  - DATA-Q1 (Vector Database) score 1/4: affects 3 services
  - DATA-Q3 (RAG Implementation) score 1/4: affects 3 services
- **Representative AWS Services**: Amazon Bedrock, Amazon Bedrock AgentCore, Amazon Q, OpenSearch Service
- **Key Activities**:
  1. Evaluate AI use cases that deliver cost optimization ROI
  2. Add Bedrock SDK integration for targeted AI features
  3. Evaluate OpenSearch Serverless for product semantic search (if ROI justified)
  4. Implement LLM cost tracking before any AI feature goes to production
- **Cross-Service Synergies**: AI capabilities built for one service can be reused across the portfolio (e.g., a product recommendation agent could serve both e-commerce applications).
- **Estimated Effort**: Medium per service
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 7 — Move to AI

### Example: Parallel Pathway Execution for a Single Service

**unishop-monolith** simultaneously pursues:
- **Move to Modern DevOps** (Phase 0-1): Establish IaC, CI/CD pipeline, structured logging
- **Move to Containers** (Phase 1-2): Create Dockerfile, deploy to ECS Fargate with Graviton
- **Move to Managed Databases** (Phase 2): Migrate self-managed MySQL to Aurora MySQL
- **Move to Cloud Native** (Phase 3): Begin service decomposition after containerization and DB migration

These pathways naturally sequence: DevOps foundations enable safe container deployment, which enables managed database migration, which prepares for service decomposition.

---

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.** Programs are engagement-level decisions scoped to the customer's overall estate, not per-repo.

Based on the portfolio assessment findings, the following AWS programs may accelerate your modernization journey:

### Recommended Programs

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| Migration Acceleration Program (MAP) | High | All 3 repos score below 2.5/4.0: local-monolith (1.5), unishop-monolith (1.31), aws-microservices (1.8). Portfolio requires significant modernization investment across infrastructure, operations, and security. | Evaluate MAP eligibility with your AWS account team. MAP provides credits, methodology, and partner support for large-scale modernization. |
| Cloud Economics (CE) | High | Portfolio goal is `cost-optimization`. Self-managed MySQL in unishop-monolith, RDS MySQL in local-monolith, and DynamoDB capacity optimization in aws-microservices all represent quantifiable cost reduction opportunities. | Request a Cloud Economics engagement via your AWS Solutions Architect to build a detailed business case with projected savings for Aurora migration and compute optimization. |
| EBA — Move to Modern DevOps | High | 3 repos triggered (100%): local-monolith, unishop-monolith, aws-microservices. Key trigger: INF-Q6 (CI/CD) = 1/4 for all, OPS-Q1 (tracing) = 1/4 for all, OPS-Q9 (deployment) = 1/4 for all. Universal DevOps gap. | Request EBA engagement via SA for guided CI/CD, observability, and testing implementation. |
| EBA — Move to Managed Databases | High | 1 repo triggered: unishop-monolith (INF-Q2: 1/4, DATA-Q10: 2/4). Self-managed MySQL → Aurora migration is the highest-value cost-optimization activity. High goal alignment. | Request EBA engagement via SA for Aurora migration planning and execution guidance. |
| EBA — Move to Containers | Medium | 1 repo triggered: unishop-monolith (INF-Q1: 1/4). Raw EC2 to ECS Fargate + Graviton migration. | Request EBA engagement via SA for containerization guidance. |
| EBA — Move to Cloud Native | Medium | 2 repos triggered: local-monolith (APP-Q4: 1/4), unishop-monolith (APP-Q4: 2/4). Monolith decomposition candidates. Lower priority for cost-optimization. | Defer until Phase 3. Request EBA engagement when service decomposition becomes a priority. |
| EBA — Move to AI | Low | 3 repos triggered (100%): All services lack AI capabilities (APP-Q13: 1/4). Low goal alignment for cost-optimization. | Defer until Phase 3. Evaluate AI ROI after operational foundations are solid. |

### Program Details

**Migration Acceleration Program (MAP)**: Recommended because all 3 services in the portfolio score below 2.5/4.0, indicating a significant modernization investment is needed. MAP provides AWS credits that can offset the cost of migration tooling (DMS, SCT), training, and professional services. The portfolio's self-managed MySQL database, raw EC2 compute, and zero-observability baseline make it a strong MAP candidate. Suggested timing: engage in Phase 0 to secure credits before Phase 2 managed service migrations.

**Cloud Economics (CE)**: Recommended because the portfolio goal is explicitly `cost-optimization`. A Cloud Economics engagement will quantify the expected savings from: (1) self-managed MySQL → Aurora migration (eliminating operational overhead), (2) EC2 → ECS Fargate + Graviton (20-40% compute savings), (3) Lambda Graviton migration (20% savings), and (4) DynamoDB capacity optimization (potential 50-70% savings with provisioned). Suggested timing: engage in Phase 0-1 to build the business case that justifies the modernization investment.

**EBA — Move to Modern DevOps**: The highest-priority EBA engagement because DevOps foundations are universally absent and are a prerequisite for all other pathways. An EBA engagement provides prescriptive guidance for establishing CI/CD, observability, and testing patterns that work across the portfolio's three different technology stacks (PHP, Java, Node.js). Suggested timing: Phase 0.

**EBA — Move to Managed Databases**: The highest-value single activity for cost-optimization. An EBA engagement provides DMS migration guidance, Aurora sizing recommendations, and Serverless v2 configuration best practices. The simple schema (3 tables, no stored procedures, standard SQL) makes this a low-risk, high-reward migration. Suggested timing: Phase 2.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

---

## Integration Opportunities

### Shared Service Extraction

**Opportunity 1: Centralized Identity (Amazon Cognito)**
- Current State: local-monolith uses PHP sessions (`$_SESSION`), unishop-monolith has disabled Spring Security OAuth2 (`permitAll()`), aws-microservices has no authentication at all. Three different auth approaches — none adequate.
- Proposed Solution: Deploy a shared Amazon Cognito User Pool. Each service integrates via its appropriate mechanism: API Gateway Cognito Authorizer (aws-microservices), Spring Security OAuth2 resource server (unishop-monolith), JWT validation middleware (local-monolith).
- Benefits: Consistent authentication, MFA, password policies, social login. Free tier covers 50,000 MAU. Eliminates per-service auth maintenance.
- Effort: Medium
- Priority: High

**Opportunity 2: Centralized Observability Platform**
- Current State: All 3 services score 1/4 on OPS-Q1 (tracing), OPS-Q2 (logging), OPS-Q4 (SLOs). Zero observability exists anywhere.
- Proposed Solution: Build a shared observability stack: CloudWatch dashboards with common templates, X-Ray tracing across all services, structured JSON logging standard (Monolog for PHP, Logback for Java, Powertools for Node.js), common CloudWatch alarm patterns.
- Benefits: Cross-service tracing, consistent metrics, shared runbooks, single-pane-of-glass visibility. Enables cost anomaly detection.
- Effort: Medium
- Priority: High

**Opportunity 3: Shared CI/CD Pipeline Templates**
- Current State: All 3 services have zero CI/CD. Each uses a different language/framework.
- Proposed Solution: Create reusable GitHub Actions workflow templates with language-specific build steps and common deployment patterns. Shared workflows for: lint → test → build → deploy, with cost estimation checks.
- Benefits: Reduced pipeline setup time per service, consistent deployment quality, shared deployment standards.
- Effort: Medium
- Priority: High

### Event-Driven Architecture

**Opportunity 1: Replace aws-microservices → local-monolith Sync Dependency**
- Current State: aws-microservices queries local-monolith synchronously for legacy product data during migration.
- Proposed Solution: Implement event-driven data replication. local-monolith publishes product data changes to EventBridge. aws-microservices consumes events and maintains a local DynamoDB cache of product data.
- Benefits: Decoupling (aws-microservices no longer fails when local-monolith is down), improved resilience, enables independent modernization.
- Effort: Medium
- Priority: Medium (address after Phase 1 stabilization)

**Opportunity 2: local-monolith Fulfillment Workflow Orchestration**
- Current State: 7-step fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) is manual API calls with no orchestration.
- Proposed Solution: AWS Step Functions state machine with human approval tasks, automatic retries, and error handling.
- Benefits: Reduced manual coordination labor costs, audit trail, timeout handling.
- Effort: Medium
- Priority: Low (Phase 3, not directly cost-optimization)

### API Gateway Consolidation

- Current State: aws-microservices has 3 separate API Gateways (Product, Basket, Order). local-monolith uses App Runner built-in endpoint + WAF. unishop-monolith has no API gateway.
- Proposed Solution: Consolidate aws-microservices to 1 API Gateway with path-based routing (`/product/*`, `/basket/*`, `/order/*`). Add ALB for unishop-monolith. Standardize throttling, auth, and monitoring patterns across all API entry points.
- Benefits: Consistent auth and throttling, reduced API Gateway costs (fewer REST APIs), unified monitoring.
- Effort: Low (aws-microservices consolidation), Medium (unified strategy)
- Priority: Medium

### Observability Unification

- Current State: All 3 services need observability from scratch — a unique opportunity to build it right.
- Proposed Solution: Standardized observability stack:
  - **Logging**: JSON format with correlation IDs, service name, request context. Monolog (PHP), Logback (Java), Powertools Logger (Node.js).
  - **Tracing**: AWS X-Ray across all services. Enable trace propagation for cross-service calls.
  - **Metrics**: CloudWatch custom metrics with common naming conventions. Per-service dashboards from shared templates.
  - **Alerting**: CloudWatch alarms for error rates, latency, and cost anomalies. SNS for notifications.
- Benefits: End-to-end tracing across aws-microservices → local-monolith dependency, consistent metrics for portfolio-wide cost analysis, shared runbooks.
- Effort: Medium
- Priority: High (Phase 0)

---

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + dedicated service teams (15+ cross-cutting concerns identified → centralized platform team recommended)

**Platform Team:**
- Responsibilities: Shared CI/CD pipeline templates, observability standards and dashboards, Cognito identity setup, IaC patterns and cost tagging standards, cost governance tooling (Budgets, Cost Anomaly Detection)
- Skills Required: CDK/CloudFormation, CI/CD (GitHub Actions or CodePipeline), CloudWatch/X-Ray, Amazon Cognito, AWS cost management tools

**Service Teams:**
- **local-monolith team**: PHP, Aurora migration (RDS MySQL → Aurora Serverless v2), App Runner optimization, CloudFormation
- **unishop-monolith team**: Java/Spring Boot, Docker/ECS Fargate, Aurora migration (self-managed MySQL → Aurora), IaC from scratch (CDK or CloudFormation)
- **aws-microservices team**: TypeScript/JavaScript, Lambda optimization (runtime, concurrency, Graviton), DynamoDB tuning (capacity modes, GSIs), API Gateway configuration

### Skill Gaps

1. **IaC (CDK/CloudFormation)**: Required for all infrastructure changes. unishop-monolith team has zero IaC experience. aws-microservices team has strong CDK skills — potential mentors.
2. **Containers (Docker/ECS/Fargate)**: Required for unishop-monolith containerization. local-monolith already has Docker experience (Dockerfile exists). Knowledge transfer opportunity.
3. **CI/CD Automation**: Required by all teams. No team has production CI/CD experience. Platform team leads the effort.
4. **Observability (X-Ray/CloudWatch)**: Required by all teams. No team has observability skills. Training needed across the portfolio.
5. **Database Migration (DMS/Aurora)**: Required for both monolith teams. Specialized skill — consider AWS Professional Services or partner support.
6. **Serverless Optimization (Lambda/DynamoDB)**: Required for aws-microservices team. Lambda concurrency tuning, DynamoDB capacity optimization, GSI design.

### Training Recommendations

- **Priority 1 (Phase 0)**: Module 6 — Move to Modern DevOps (all teams). CI/CD, observability, and testing are foundational for all subsequent work.
- **Priority 2 (Phase 1)**: Module 3 — Move to Containers (unishop-monolith team). Containerization is a prerequisite for ECS Fargate deployment.
- **Priority 3 (Phase 2)**: Module 4 — Move to Managed Databases (both monolith teams). Aurora migration requires understanding of DMS, Aurora features, and capacity planning.
- **Priority 4 (Phase 2-3)**: Module 2 — Cloud Design Patterns (all teams). Architecture patterns for resilience, decoupling, and service decomposition.

### External Support

- Recommend AWS Professional Services or consulting partners for:
  - **unishop-monolith Aurora migration** (self-managed MySQL → Aurora) — highest-risk activity with greatest cost-optimization impact. External expertise reduces migration risk.
  - **Platform team bootstrapping** — CI/CD templates, observability standards, and Cognito setup benefit from experienced guidance given the portfolio has zero operational maturity.
  - **Cloud Economics engagement** — quantify expected savings to justify modernization investment.
- Estimated external engagement: 2-3 months for platform work, overlapping with Phase 0 and Phase 1.

---

## Recommended Self-Paced Learning Materials

The following learning materials are selected based on the portfolio-wide skill gaps identified: CI/CD automation, containerization, managed database migration, observability, and cloud-native architecture patterns.

**Module 6: Move to Modern DevOps** *(Highest priority — addresses universal CI/CD, observability, and testing gaps)*
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 3: Move to Containers with Amazon ECS and EKS** *(For unishop-monolith containerization)*
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1

**Module 4: Move to Managed Databases** *(For Aurora migration — both monoliths)*
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

**Module 2: Move to Cloud Native (Containers and Serverless)** *(For architecture patterns and future decomposition)*
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S

---

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Denial-of-wallet attack on aws-microservices — public APIs with no auth, no throttling, unbounded Lambda/DynamoDB costs | Medium | High | Phase 0: Add API Gateway throttling and Lambda reserved concurrency. Phase 2: Add Cognito authentication. |
| Hardcoded credentials exposure (local-monolith: `ecommerce_pass` in docker-compose; unishop-monolith: `MonoToMicroPassword` in application.properties) | Medium | High | Phase 1: Migrate to AWS Secrets Manager for both monoliths. Remove hardcoded defaults from source code. |
| EOL Lambda runtime (aws-microservices: Node.js 14.x) — force-deprecation will disable Lambda functions | High | Medium | Phase 1: Upgrade to Node.js 20.x + ARM64/Graviton. One-line CDK change per function. |
| No rollback capability for any service — failed deployments cause extended downtime | High | Medium | Phase 0: Establish CI/CD with rollback. Configure App Runner auto-rollback, ECS circuit breaker, Lambda aliases. |
| Self-managed MySQL failure (unishop-monolith) — no automated failover, no IaC, manual recovery | High | Medium | Phase 2: Migrate to Aurora MySQL with built-in Multi-AZ failover. |
| Single-AZ RDS MySQL (local-monolith: db.t3.micro) — AZ failure causes downtime + data loss risk | Medium | Medium | Phase 2: Migrate to Aurora MySQL Serverless v2 with automatic Multi-AZ. |
| Indefinite CloudWatch Logs retention (aws-microservices) — silently growing storage costs | High | Low | Phase 1: Set `logRetention: RetentionDays.ONE_MONTH` on all Lambda functions. |
| DynamoDB full-table Scans (aws-microservices) — read capacity costs scale with table size | Medium | Medium | Phase 3: Replace ScanCommand with QueryCommand + GSIs for list operations. |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| IaC skill gap — unishop-monolith team has zero IaC experience | High | Medium | Pair programming with aws-microservices team (strong CDK). Module 6 training. Platform team provides IaC templates. |
| Multi-language portfolio complexity — 3 different stacks (PHP, Java, Node.js) | Medium | Low | Standardize operational patterns (logging, monitoring, CI/CD) even if application languages differ. Shared platform team abstracts language differences. |
| No operational ownership — all services score 1/4 on OPS-Q12 | High | Medium | Phase 0: Create CODEOWNERS files. Define SLO ownership per service. Establish basic on-call rotation. |
| Change fatigue — modernizing 3 services simultaneously across all dimensions | Medium | Medium | Prioritize phases strictly. Don't start Phase 2 until Phase 0/1 foundations are solid. Use parallel tracks to limit per-team scope. |

### Dependency Risks

**aws-microservices → local-monolith sync dependency**: If local-monolith modernization encounters delays (e.g., Aurora migration complications), aws-microservices integration work is blocked. Mitigation: (1) Prioritize local-monolith stability in Phase 1, (2) aws-microservices quick wins (runtime upgrade, throttling) can proceed independently, (3) consider event-driven data replication to eliminate the sync dependency entirely.

### Single Points of Failure

1. **local-monolith RDS MySQL (db.t3.micro, single-AZ)**: A single AZ failure causes downtime for local-monolith AND impacts aws-microservices (which depends on it synchronously). Blast radius: 67% of portfolio (2 of 3 services). Mitigation: Aurora migration in Phase 2 provides automatic Multi-AZ failover.

2. **unishop-monolith self-managed MySQL on EC2**: No automated failover. Unknown backup strategy. Blast radius: 0% (isolated service, no dependents). Mitigation: Aurora migration in Phase 2 with automated backups and Multi-AZ.

---

## Service-by-Service Summary

### local-monolith

- **Overall Score**: 1.5 / 4.0 🟠
- **Repository**: ./monolith
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 2.1 / 4.0
  - Application: 1.3 / 4.0
  - Data: 1.5 / 4.0
  - Security: 1.4 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. No CI/CD Automation (INF-Q6: 1/4)
  2. Zero Observability (OPS-Q1: 1/4, OPS-Q2: 1/4)
  3. No Deployment Strategy or Rollback (OPS-Q9: 1/4, OPS-Q5: 1/4)
  4. No Testing (OPS-Q10: 1/4)
  5. Tightly-Coupled Monolith (APP-Q4: 1/4)
- **Dependencies**: None
- **Depended On By**: aws-microservices (sync product data query)
- **Modernization Pathways**: Move to Cloud Native (Low), Move to Modern DevOps (Medium), Move to AI (Low)
- **Modernization Phase**: Phase 1 (License & Quick Savings) + Phase 2 (Managed Service Migration)
- **Estimated Effort**: Medium

### unishop-monolith

- **Overall Score**: 1.31 / 4.0 ❌
- **Repository**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 1.0 / 4.0
  - Application: 1.38 / 4.0
  - Data: 2.09 / 4.0
  - Security: 1.1 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. Self-Managed MySQL Database (INF-Q2: 1/4) — **primary cost-optimization target**
  2. Raw EC2 Compute (INF-Q1: 1/4)
  3. No Infrastructure as Code (INF-Q5: 1/4)
  4. No CI/CD Pipeline (INF-Q6: 1/4)
  5. Unpinned Database Engine Version (DATA-Q10: 2/4)
- **Dependencies**: None
- **Depended On By**: None (isolated)
- **Modernization Pathways**: Move to Cloud Native (Low), Move to Containers (Medium), Move to Managed Databases (High), Move to Modern DevOps (Medium), Move to AI (Low)
- **Modernization Phase**: Phase 1 (License & Quick Savings) + Phase 2 (Managed Service Migration)
- **Estimated Effort**: High

### aws-microservices

- **Overall Score**: 1.8 / 4.0 🟠
- **Repository**: ./services/aws-microservices
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 2.6 / 4.0
  - Application: 2.1 / 4.0
  - Data: 2.0 / 4.0
  - Security: 1.4 / 4.0
  - Operations: 1.0 / 4.0
- **Top Priorities**:
  1. No CI/CD Pipeline (INF-Q6: 1/4)
  2. No API Authentication (SEC-Q9: 1/4) — critical cost risk
  3. EOL Lambda Runtime Node.js 14.x (INF-Q1/APP-Q1)
  4. No Observability (OPS-Q1 through OPS-Q12: all 1/4)
  5. No API Rate Limiting (SEC-Q5/APP-Q8: 1/4)
- **Dependencies**: local-monolith (sync — product data queries)
- **Depended On By**: None
- **Modernization Pathways**: Move to Modern DevOps (Medium), Move to AI (Low)
- **Modernization Phase**: Phase 1 (quick wins) + Phase 2 (Managed Service Migration)
- **Estimated Effort**: Medium

---

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Repo Type | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------|-----------------|---------------|-------------|
| local-monolith | ./monolith | application (auto-detected) | 2026-03-17 | 1.5 / 4.0 | ./monolith/agentic-readiness-assessment/monolith-agentic-readiness-report.md |
| unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy | application (auto-detected) | 2026-03-17 | 1.31 / 4.0 | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-assessment/MonoToMicroLegacy-agentic-readiness-report.md |
| aws-microservices | ./services/aws-microservices | application (auto-detected) | 2026-03-17 | 1.8 / 4.0 | ./services/aws-microservices/agentic-readiness-assessment/aws-microservices-agentic-readiness-report.md |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)
- Portfolio scores: Arithmetic mean of individual service scores
- Goal: cost-optimization — phases and priorities weighted toward managed service migration, licensing cost reduction, and operational efficiency
- Preferences: prefer [aurora-postgresql, opensearch, dynamodb, managed-services, open-source], avoid [oracle, sql-server, windows, self-managed-databases]

---

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - Request MAP eligibility assessment with your AWS account team
   - Request Cloud Economics engagement to quantify expected savings
   - Begin platform team formation and assign CODEOWNERS for each service
   - Upgrade aws-microservices Lambda runtime to Node.js 20.x + ARM64/Graviton (immediate ~20% savings, one-line CDK change)
   - Set CloudWatch Logs retention on aws-microservices Lambda functions (stop log cost growth)

2. **Short-term (Month 1)**:
   - Establish CI/CD pipeline templates for all 3 services (Phase 0)
   - Enable X-Ray tracing across all services (Phase 0)
   - Add WAF rate-based rules and API Gateway throttling (Phase 0)
   - Migrate hardcoded credentials to AWS Secrets Manager (Phase 1)
   - Begin unishop-monolith Dockerfile creation and IaC implementation (Phase 1)

3. **Medium-term (Months 1-3)**:
   - Migrate unishop-monolith self-managed MySQL to Aurora MySQL using DMS (Phase 2)
   - Migrate local-monolith RDS MySQL to Aurora MySQL Serverless v2 (Phase 2)
   - Deploy unishop-monolith to ECS Fargate with Graviton (Phase 2)
   - Add Cognito authentication to aws-microservices (Phase 2)
   - Analyze DynamoDB usage patterns and evaluate provisioned capacity (Phase 2)

4. **Long-term (Months 3-6)**:
   - Implement SLOs, business metrics, and anomaly detection across all services (Phase 3)
   - Right-size compute based on production utilization data (Phase 3)
   - Implement AWS Budgets and Cost Anomaly Detection for cost governance (Phase 3)
   - Evaluate Aurora PostgreSQL migration for local-monolith (Phase 3)
   - Plan Spring Boot upgrade for unishop-monolith (Phase 3)
   - Evaluate service decomposition opportunities for both monoliths (Phase 3)
