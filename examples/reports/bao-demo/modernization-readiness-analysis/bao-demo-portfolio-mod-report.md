# Portfolio Modernization Readiness Analysis Report

**Date**: 2025-07-18
**Services Analyzed**: 5
**Portfolio Context**: Demonstrating BPMN agentic opportunity analysis across official open source process repositories covering invoice processing, order management, and BPMN interchange test cases.
**Technology Preferences**: Prefer: None; Avoid: None

---

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 1.51 / 4.0 |
| Score Range | 1.28 – 1.80 |
| Score Variance (Std Dev) | 0.21 |
| Highest Scoring Service | camunda-invoice (1.80) |
| Lowest Scoring Service | bpmn-miwg-test-suite (1.28) |
| Pathways Triggered (portfolio-wide) | 4 of 7 |
| Cross-Cutting Foundational Blockers | 33 |
| Cross-Cutting Improvement Opportunities | 1 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 0 | 0% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 2 | 40% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 3 | 60% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 1.25 | 1.09 | 1.45 | 0 |
| Application Architecture (APP) | 1.87 | 1.17 | 2.33 | 0 |
| Data Platform (DATA) | 2.15 | 1.75 | 2.75 | 0 |
| Security Baseline (SEC) | 1.17 | 1.00 | 1.43 | 0 |
| Operations & Observability (OPS) | 1.13 | 1.00 | 1.22 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 3 | 60% |
| monorepo | 2 | 40% |
| infrastructure-only | 0 | 0% |
| deployment-config | 0 | 0% |
| library | 0 | 0% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| analysis_date | 2025-07-18 |
| total_services | 5 |
| portfolio_score | 1.51 |
| score_range_min | 1.28 |
| score_range_max | 1.80 |
| mature_services | 0 |
| partial_services | 0 |
| needs_work_services | 2 |
| not_ready_services | 3 |
| pathways_triggered | 4 |
| foundational_blockers | 33 |
| improvement_opportunities | 1 |
| category_inf | 1.25 |
| category_app | 1.87 |
| category_data | 2.15 |
| category_sec | 1.17 |
| category_ops | 1.13 |
| portfolio_level_avg | 1.80 |

---

## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| Java | 5 | 100% |
| JavaScript / Node.js | 2 | 40% |
| Groovy | 2 | 40% |

**Java Version Distribution:**
- Java 17: camunda-invoice, camunda-bpm-examples
- Java 11: camunda8-order-process, camunda-rest-service
- Java 1.6 (target): bpmn-miwg-test-suite (builds with JDK 11)

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| H2 (in-memory) | Relational (embedded) | 3 (camunda-invoice, camunda-rest-service, camunda-bpm-examples) | No |
| H2 (file-based) | Relational (embedded) | 2 (camunda-rest-service, camunda-bpm-examples) | No |
| PostgreSQL (driver refs) | Relational | 2 (camunda-invoice, camunda-bpm-examples) | No (CI testing only) |
| MySQL (driver refs) | Relational | 2 (camunda-invoice, camunda-bpm-examples) | No (CI testing only) |
| Oracle (driver refs) | Relational | 2 (camunda-invoice, camunda-bpm-examples) | No (CI testing only) |
| SQL Server (driver refs) | Relational | 1 (camunda-invoice) | No (CI testing only) |
| DB2 (driver refs) | Relational | 1 (camunda-invoice) | No (CI testing only) |

**Database Distribution**: 0 managed, 3 self-managed (H2), 2 commercial (Oracle/SQL Server drivers referenced), 3 open source (H2, PostgreSQL, MySQL drivers referenced)

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| Traditional App Server / Local Execution | 5 | 100% |
| EC2 / VM-based | 0 | 0% |
| Containers (ECS/EKS/Fargate) | 0 | 0% |
| Serverless (Lambda) | 0 | 0% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| None (0% IaC coverage) | IaC | 5 |
| Jenkins | CI/CD | 1 (camunda-invoice) |
| GitHub Actions (build/publish) | CI/CD | 1 (bpmn-miwg-test-suite) |
| GitHub Actions (version-bump only) | CI/CD | 1 (camunda-bpm-examples) |
| None | CI/CD | 2 (camunda8-order-process, camunda-rest-service) |

### Standardization Opportunities

- **Java Version Standardization**: Java is used by 100% of services but spans three versions (1.6, 11, 17). Standardize on Java 17 or 21 (LTS) across all services to leverage modern language features, improved performance, and extended support.
- **IaC Tool Adoption**: Zero IaC coverage across the entire portfolio. This is a greenfield opportunity to standardize on a single IaC tool (Terraform or CDK) from the start, avoiding future fragmentation.
- **CI/CD Tool Consolidation**: CI/CD is fragmented across Jenkins (1 service), GitHub Actions (2 services with limited scope), and no CI/CD (2 services). Consolidate on a single CI/CD platform — GitHub Actions is the natural choice given the GitHub-hosted repositories.
- **Database Standardization**: H2 is used across 3 services but is not production-grade. Standardize on Aurora PostgreSQL as the managed production database — camunda-invoice already tests against Aurora PostgreSQL in CI.
- **Container Adoption**: Zero containerization. Adopt a single container orchestration platform (ECS/Fargate or EKS) for all services.
- **Technology Diversity Score**: 8 distinct technologies / 5 services = 1.6 (moderate diversity driven by multiple Java versions, multiple CI/CD tools, and multiple database driver references)
## Service Dependency Map

### Inferred Dependency Analysis

Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`). The following observations were made:

**Shared Platform Dependencies (Inferred):**
- **camunda-invoice**, **camunda-rest-service**, and **camunda-bpm-examples** all use the **Camunda 7 BPM engine** as their core workflow platform. This represents a shared technology dependency but not a direct service-to-service runtime dependency — each service embeds its own Camunda engine instance.
- **camunda8-order-process** uses **Camunda 8 / Zeebe** (a different platform generation), with no direct coupling to the Camunda 7 services.
- **bpmn-miwg-test-suite** is a test data repository with no runtime dependencies on any other service.

**Cross-Service Communication Evidence:**
- camunda-rest-service's `SearchContributorService` (Node.js external task worker) calls `localhost:8080` — this is an **internal** component-to-component dependency within the same service, not a cross-service dependency.
- No evidence of direct REST API calls, shared databases, or message queue connections between any of the 5 assessed services was found.

**Inferred Dependency Graph:**

No direct service-to-service dependencies could be inferred from the individual MOD report findings. All 5 services operate independently — they share the Camunda ecosystem as a technology choice but do not communicate with each other at runtime.

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| camunda-invoice | 0 | 0 | 0% | Independent | 1.80 |
| camunda8-order-process | 0 | 0 | 0% | Independent | 1.37 |
| camunda-rest-service | 0 | 0 | 0% | Independent | 1.42 |
| bpmn-miwg-test-suite | 0 | 0 | 0% | Independent | 1.28 |
| camunda-bpm-examples | 0 | 0 | 0% | Independent | 1.69 |

### Circular Dependencies

✅ No circular dependencies detected. All services are independent with no inter-service dependencies.

> **Recommendation**: No dependency information was provided in the portfolio configuration, and no direct cross-service dependencies could be inferred from the individual reports. To enable dependency-aware analysis — including coupling scores, blast radius calculation, circular dependency detection, and dependency-ordered roadmap phasing — add `dependency_overrides` to the portfolio config. The roadmap below uses priority-based ordering (P0 → P1 → P2) without dependency-based phase assignment.
## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.

1. **INF-Q1: Managed Compute** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: No managed compute across the entire portfolio. All services run on traditional app servers or locally from IDEs with no cloud deployment targets.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Establish containerized compute on ECS/Fargate or EKS as a shared platform capability. Create reusable Dockerfiles and ECS task definition templates for Java Spring Boot applications.

2. **INF-Q2: Managed Databases** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: No managed database infrastructure. H2 embedded databases are used for development but no production-grade database provisioning exists.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Provision a shared Aurora PostgreSQL cluster (or per-service instances) via IaC. Camunda 7 and 8 both support PostgreSQL natively. Define shared database IaC modules.

3. **INF-Q5: Network Security** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: No VPC, subnet, or security group configuration exists anywhere in the portfolio. Services have no network isolation.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Define a shared VPC architecture in IaC with private subnets for application/database tiers, security groups with least-privilege rules, and VPC endpoints for AWS service access. Use a shared networking module.

4. **INF-Q6: API Entry Point** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: No API Gateway, ALB, or managed entry point. Services are exposed directly without throttling, authentication, or request validation.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Deploy a shared ALB and/or API Gateway with centralized authentication (Cognito), throttling, and path-based routing for all Camunda REST APIs.

5. **INF-Q7: Auto-Scaling** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: No auto-scaling configuration. All capacity is statically provisioned or undefined.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Configure ECS Service Auto-Scaling with target tracking on CPU utilization for all containerized services. Define reusable scaling policy templates.

6. **INF-Q8: Backup and Recovery** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: No backup configuration. H2 data is ephemeral and process state could be lost with no recovery path.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Enable automated backups with PITR on all Aurora/RDS instances. Configure AWS Backup with cross-region replication. Establish a backup testing schedule.

7. **INF-Q9: High Availability and Fault Isolation** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: No multi-AZ configuration. Every service is a single point of failure.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Deploy all services across 2+ AZs. Configure Aurora Multi-AZ. Use ALB with cross-zone load balancing. Define HA patterns in shared IaC modules.

8. **INF-Q10: Infrastructure as Code Coverage** — 5 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
   - **Impact**: 0% IaC coverage across the entire portfolio. All infrastructure would be created manually (ClickOps). This is the #1 foundational blocker.
   - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Adopt a single IaC tool (CDK for Java teams, or Terraform) and create a shared infrastructure repository with reusable modules for VPC, ECS, Aurora, IAM, and CloudWatch. This unlocks all other modernization pathways.

9. **INF-Q11: CI/CD Automation** — 3 of 5 services score < 2
   - **Score Distribution**: camunda-invoice=3, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=3, camunda-bpm-examples=1
   - **Impact**: 3 services have zero CI/CD. The 2 services with CI/CD (score 3) lack deployment automation.
   - **Affected Services**: camunda8-order-process, camunda-rest-service, camunda-bpm-examples
   - **Portfolio-Level Recommendation**: Create a shared GitHub Actions CI/CD pipeline template with build, test, security scan, container build, and deployment stages. Apply to all 5 services.

10. **INF-Q4: Async Messaging and Streaming** — 2 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=2, camunda8-order-process=2, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=2
    - **Impact**: No managed messaging infrastructure. All async patterns are Camunda-internal (job executor, external tasks). No SQS, SNS, or EventBridge for cross-service communication.
    - **Affected Services**: camunda-rest-service, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Introduce Amazon EventBridge as a shared event bus for portfolio-wide event propagation. Define standard event schemas for process lifecycle events.

11. **APP-Q2: Monolith vs Microservices** — 4 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=2
    - **Impact**: 4 services are tightly-coupled monoliths with no decomposition. 1 service has identifiable module boundaries but shared coupling.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Use the Strangler Fig pattern portfolio-wide. Start with containerization (lift-and-containerize), then incrementally extract services using BPMN task boundaries as natural decomposition points.

12. **APP-Q3: Async vs Sync Communication** — 2 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=2, camunda8-order-process=2, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=2
    - **Impact**: Communication patterns are predominantly synchronous HTTP. No managed messaging for cross-service state propagation.
    - **Affected Services**: camunda-rest-service, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Introduce EventBridge/SQS for async communication. Define event-driven patterns for process state changes that other services can subscribe to.

13. **APP-Q5: API Versioning Strategy** — 4 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=2, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No API versioning strategy. Breaking changes would affect all consumers simultaneously.
    - **Affected Services**: camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Establish a portfolio-wide API versioning standard using URL-path versioning (`/api/v1/`). Generate and publish OpenAPI specifications from all REST endpoints.

14. **APP-Q6: Service Discovery** — 4 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=2
    - **Impact**: Service endpoints are hardcoded. No dynamic discovery mechanism exists.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Implement AWS Cloud Map or ECS Service Discovery. Externalize all endpoints to environment variables as a first step, then adopt DNS-based discovery.

15. **DATA-Q1: Unstructured Data Storage** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No managed object storage. All data is on local filesystems or embedded databases.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Create shared S3 buckets for process artifacts, BPMN definitions, audit documents, and report outputs. Define lifecycle policies and versioning.

16. **DATA-Q2: Unified Data Access Layer** — 2 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=3, camunda8-order-process=1, camunda-rest-service=2, bpmn-miwg-test-suite=1, camunda-bpm-examples=3
    - **Impact**: 2 services lack any data access abstraction. Data access patterns vary from Camunda's Process Engine API to raw Map access.
    - **Affected Services**: camunda8-order-process, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Standardize on the Camunda Process Engine API as the data access layer for Camunda services. For non-Camunda services, adopt a Repository/DAO pattern. Define typed DTOs for Zeebe job variables.

17. **DATA-Q3: Database Engine Version and EOL** — 3 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=2, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=2
    - **Impact**: No production database engine versions tracked. H2 versions are inherited from EOL Spring Boot BOMs. No version lifecycle management.
    - **Affected Services**: camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Pin all production database engine versions in IaC. Document EOL dates and establish a quarterly version review cadence.

18. **SEC-Q1: Audit Logging** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No audit logging. No CloudTrail. No immutable log storage. Process actions are unaudited.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Enable CloudTrail for all AWS accounts. Configure centralized CloudWatch log groups with defined retention. Ship Camunda history data to S3 with Object Lock for immutable audit storage.

19. **SEC-Q2: Encryption at Rest** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No encryption at rest. H2 databases and local file storage are unencrypted.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Enforce encryption at rest on all AWS resources from day one via IaC defaults. Define a shared KMS key policy with customer-managed keys and automated rotation.

20. **SEC-Q3: API Authentication** — 4 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=2
    - **Impact**: Camunda REST APIs are exposed without authentication. Admin UIs use hardcoded demo credentials.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Implement centralized OAuth2/JWT authentication using Amazon Cognito. Configure API Gateway authorizers for all REST endpoints.

21. **SEC-Q4: Centralized Identity Integration** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No centralized identity provider. Each service manages its own authentication with hardcoded credentials.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Deploy Amazon Cognito as the centralized IdP. Configure OIDC/SAML federation for Camunda web applications. Enable SSO across all services.

22. **SEC-Q5: Secrets Management** — 4 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=3, camunda-bpm-examples=1
    - **Impact**: **CRITICAL** — Database credentials, admin passwords, and API keys hardcoded in version-controlled configuration files across 4 services.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: **Immediate action**: Rotate all exposed credentials. Move all secrets to AWS Secrets Manager. Use Spring Cloud AWS Secrets Manager integration for injection. Add pre-commit hooks to prevent secret commits.

23. **SEC-Q6: Compute Hardening and Patching** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No compute hardening. No vulnerability scanning. Dependencies include EOL frameworks (Spring Boot 2.5.4).
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Use hardened base images (Amazon Corretto on Amazon Linux 2023). Enable ECR image scanning. Add OWASP dependency-check to all Maven builds.

24. **SEC-Q7: Application Security Pipeline** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No SAST, DAST, or dependency scanning anywhere in the portfolio. Vulnerabilities reach production undetected.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Add Dependabot to all repositories. Integrate OWASP dependency-check in Maven builds. Add Trivy/ECR scanning for containers. Define security gates that block deployments on critical findings.

25. **OPS-Q1: Distributed Tracing** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No distributed tracing. Debugging failures across Camunda engine, task workers, and external APIs is guesswork.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Deploy OpenTelemetry Java agent across all Spring Boot services. Configure X-Ray as the trace exporter. Establish a shared observability platform.

26. **OPS-Q2: SLO Definitions** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No SLO definitions. No error budgets. No formal service level targets.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Define SLOs for critical process journeys. Implement CloudWatch alarms with error budget tracking. Start with availability and p99 latency targets.

27. **OPS-Q3: Business Metrics** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No custom business metrics. Only `System.out.println()` console output. No visibility into business outcomes.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Integrate Micrometer with CloudWatch metrics exporter across all Spring Boot services. Define standard business metrics: process throughput, task completion rates, error rates.

28. **OPS-Q4: Anomaly Detection and Alerting** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No alerting configured. Failures go undetected until manually noticed.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Configure CloudWatch alarms for all critical metrics. Enable anomaly detection on error rates and latency. Integrate with PagerDuty/OpsGenie for on-call notification.

29. **OPS-Q5: Deployment Strategy** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No deployment strategy. All deployments are manual with no staged rollout or rollback.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Implement blue/green deployments via CodeDeploy with ECS. Define a shared deployment pipeline template with health check verification and automatic rollback.

30. **OPS-Q7: Incident Response Automation** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No runbooks. No automated remediation. Incident response is entirely ad hoc.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Create shared runbooks for common Camunda operational scenarios. Automate common remediations using SSM Automation documents.

31. **OPS-Q8: Observability Ownership** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No observability ownership. No dashboards, no alarm owners, no team accountability.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Create CODEOWNERS files. Define per-service dashboards. Assign alarm owners. Tie SLO definitions to responsible teams.

32. **OPS-Q9: Resource Tagging Governance** — 5 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=1, camunda8-order-process=1, camunda-rest-service=1, bpmn-miwg-test-suite=1, camunda-bpm-examples=1
    - **Impact**: No resource tagging. Cost allocation, ownership identification, and environment classification are impossible.
    - **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
    - **Portfolio-Level Recommendation**: Define a mandatory tagging standard (Environment, Service, Team, CostCenter, Priority). Enforce via IaC `default_tags` and AWS Config `required-tags` rules.

33. **APP-Q4: Long-Running Process Handling** — 2 of 5 services score < 2
    - **Score Distribution**: camunda-invoice=3, camunda8-order-process=2, camunda-rest-service=3, bpmn-miwg-test-suite=1, camunda-bpm-examples=3
    - **Impact**: 2 services lack async job processing for long-running operations. Workers block with `Thread.sleep()` or have no long-running process handling.
    - **Affected Services**: camunda8-order-process, bpmn-miwg-test-suite
    - **Portfolio-Level Recommendation**: Refactor blocking workers to use async job completion patterns. For services without long-running needs (bpmn-miwg-test-suite), this may be acceptable given the repo's nature as a test data suite.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking.
> Address as capacity allows or in parallel with other modernization work.

1. **OPS-Q6: Integration Testing** — 3 of 5 services score < 3
   - **Score Distribution**: camunda-invoice=N/A (not found in report tail), camunda8-order-process=1, camunda-rest-service=2, bpmn-miwg-test-suite=2, camunda-bpm-examples=3
   - **Impact**: Limited or no integration tests in CI. Tests exist in some repos but are not automated.
   - **Affected Services**: camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite
   - **Portfolio-Level Recommendation**: Wire all existing tests into CI pipelines. Add Testcontainers for Camunda integration testing. Establish minimum test coverage thresholds as quality gates.
### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 1.25 / 4.0**

**Common Patterns:**
- Zero IaC coverage: present in 5/5 services
- No managed compute: present in 5/5 services
- No network security: present in 5/5 services
- Camunda workflow orchestration (score 3): present in 4/5 services

**Critical Gaps:**
1. IaC (INF-Q10): 0% coverage across all 5 services — this is the top foundational blocker. No reproducible deployments, no DR, no environment parity.
2. Managed Compute (INF-Q1): All services run on traditional app servers or locally. No containers, no serverless, no managed compute.
3. CI/CD (INF-Q11): 3 services have zero CI/CD. Jenkins and GitHub Actions exist in 2 services but lack deployment automation.

#### Application Architecture

**Portfolio Score: 1.87 / 4.0**

**Common Patterns:**
- Java as primary language (score 4): present in 4/5 services (bpmn-miwg-test-suite scores 2 due to Java 1.6 target)
- Monolithic architecture: present in 4/5 services (score 1); 1 service scores 2 (modular monolith)
- Camunda BPMN workflow engine: present in 4/5 services

**Critical Gaps:**
1. Monolith Architecture (APP-Q2): 4 services are tightly-coupled monoliths. Decomposition using Strangler Fig is recommended.
2. Service Discovery (APP-Q6): 4 services have hardcoded endpoints with no dynamic discovery.
3. API Versioning (APP-Q5): 4 services have no API versioning strategy.

#### Data Platform

**Portfolio Score: 2.15 / 4.0**

**Common Patterns:**
- No stored procedures (DATA-Q4 score 4): present in 5/5 services — all business logic in application layer
- H2 embedded databases: present in 3/5 services for development/testing
- Camunda Process Engine API as data access layer: present in 3/5 services

**Critical Gaps:**
1. Unstructured Data Storage (DATA-Q1): No S3 or managed object storage across any service.
2. Database Engine Version (DATA-Q3): 3 services have no production database engine version tracking.

#### Security Baseline

**Portfolio Score: 1.17 / 4.0**

**Common Patterns:**
- Hardcoded credentials: present in 4/5 services (demo/demo, sa/sa, clientId/clientSecret in plaintext)
- No encryption at rest: present in 5/5 services
- No audit logging: present in 5/5 services

**Critical Gaps:**
1. Secrets Management (SEC-Q5): **CRITICAL** — Credentials hardcoded in 4 services and committed to version control. Immediate rotation required.
2. Application Security Pipeline (SEC-Q7): Zero security scanning across the entire portfolio.
3. Centralized Identity (SEC-Q4): No IdP integration. All authentication is application-managed with demo credentials.

#### Operations & Observability

**Portfolio Score: 1.13 / 4.0**

**Common Patterns:**
- `System.out.println()` as logging: present in 3/5 services
- No observability infrastructure: present in 5/5 services
- Camunda metrics explicitly disabled: present in 2/5 services

**Critical Gaps:**
1. Distributed Tracing (OPS-Q1): Zero tracing across the entire portfolio. Debugging cross-component failures is impossible.
2. Deployment Strategy (OPS-Q5): No deployment strategy in any service. All deployments are manual.
3. Incident Response (OPS-Q7): No runbooks, no automated remediation across the entire portfolio.

---

## Portfolio Modernization Roadmap

> Priority-based phased roadmap. Services are ordered by priority (P0 → P1 → P2),
> then by score (lowest first). Dependency-based ordering is not available — no
> `dependency_overrides` were provided and no inter-service dependencies were inferred.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Priority Order**: P0 services before P1 services (no dependency data available)
3. **Risk Mitigation**: Secrets remediation and security scanning before production deployments
4. **Parallel Tracks**: Independent services can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, remediate critical security issues, and build platform infrastructure.

**Cross-Cutting Activities:**
- **Secrets Remediation (SEC-Q5)**: Rotate all exposed credentials (camunda8-order-process Zeebe client, camunda-rest-service admin, camunda-bpm-examples admin). Move to AWS Secrets Manager.
- **IaC Foundation (INF-Q10)**: Create shared infrastructure repository with CDK (Java) or Terraform modules for VPC, ECS/Fargate, Aurora PostgreSQL, IAM, and CloudWatch.
- **CI/CD Template (INF-Q11)**: Create reusable GitHub Actions workflow template with build, test, security scan, container build, and deployment stages.
- **Network Architecture (INF-Q5)**: Define shared VPC with private subnets, security groups, and VPC endpoints.
- **Security Pipeline (SEC-Q7)**: Add Dependabot to all 5 repositories. Integrate OWASP dependency-check in Maven builds.
- **Observability Platform (OPS-Q1)**: Deploy OpenTelemetry Collector. Configure X-Ray and CloudWatch as backends.

**Organizational Enablers:**
- Training: IaC (CDK/Terraform), Containers (Docker, ECS), AWS Security Best Practices
- Tooling: GitHub Actions, AWS CDK, Docker, Amazon ECR
- Standards: Tagging standard, API versioning standard, secrets management policy

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize P0 services and establish reference patterns.

**Services in Scope:**

1. **camunda8-order-process** (P0, Score: 1.37 / 4.0)
   - Current State: Single Spring Boot worker with hardcoded Zeebe credentials, no compute, no CI/CD, no tests
   - Target State: Containerized on ECS/Fargate, secrets in Secrets Manager, CI/CD pipeline, basic tests
   - Key Activities:
     - Rotate and externalize Zeebe credentials to Secrets Manager
     - Create Dockerfile for Spring Boot application
     - Deploy to ECS Fargate with auto-scaling
     - Create GitHub Actions CI/CD pipeline
     - Add JUnit 5 + Testcontainers test suite
   - Dependencies: Phase 0 (shared IaC, VPC, ECS cluster)
   - Blocks: None (independent service)
   - Estimated Effort: Medium

2. **camunda-invoice** (P0, Score: 1.80 / 4.0)
   - Current State: Camunda 7 monolith on traditional app servers, Jenkins CI without deployment, Aurora PostgreSQL tested in CI
   - Target State: Containerized on ECS/Fargate, Aurora PostgreSQL database, extended CI/CD with deployment
   - Key Activities:
     - Containerize WAR into Tomcat Docker image
     - Provision Aurora PostgreSQL (CI matrix already tests aurora_postgresql)
     - Extend Jenkins pipeline with deployment stages (or migrate to GitHub Actions)
     - Implement blue/green deployment with CodeDeploy
   - Dependencies: Phase 0 (shared IaC, VPC, Aurora module)
   - Blocks: None (independent service)
   - Estimated Effort: High

**Expected Outcomes:**
- 2 P0 services containerized and deployed to AWS
- Reference Dockerfile and ECS task definition templates established
- CI/CD pipeline pattern validated
- Secrets management pattern established

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize P1 services. Replicate proven patterns from Phase 1.

**Services in Scope:**

1. **camunda-rest-service** (P1, Score: 1.42 / 4.0)
   - Current State: Camunda 7 monolith with embedded H2, no CI/CD, hardcoded credentials, Node.js external task worker
   - Target State: Containerized (both Java app and Node.js worker), Aurora PostgreSQL, CI/CD pipeline
   - Key Activities:
     - Create Dockerfiles for CamundaApplication (Java) and SearchContributorService (Node.js)
     - Replace H2 with Aurora PostgreSQL
     - Externalize endpoint configuration (replace hardcoded localhost:8080)
     - Create GitHub Actions CI/CD pipeline
     - Wire existing WorkflowTest integration tests into CI
   - Dependencies: Phase 0 (shared IaC)
   - Blocks: None
   - Estimated Effort: Medium

2. **bpmn-miwg-test-suite** (P1, Score: 1.28 / 4.0)
   - Current State: Test data repository with GitHub Actions for build/publish, GitHub Pages hosting
   - Target State: Hardened CI/CD with security scanning, IaC for hosting, dependency scanning
   - Key Activities:
     - Add Dependabot and OWASP dependency-check to CI pipeline
     - Add post-deployment validation for GitHub Pages
     - Update Java target version from 1.6 to 17
     - Add build quality gates (BPMN validation pass/fail criteria)
   - Dependencies: Phase 0 (security pipeline template)
   - Blocks: None
   - Estimated Effort: Low

3. **camunda-bpm-examples** (P1, Score: 1.69 / 4.0)
   - Current State: 43 Maven modules, H2 databases, GitHub Actions for version bumping only, hardcoded credentials
   - Target State: Containerized reference application, Aurora PostgreSQL, full CI/CD with test execution
   - Key Activities:
     - Containerize example-invoice as reference deployment
     - Replace H2 with Aurora PostgreSQL
     - Create full CI/CD pipeline (build, test, security scan, deploy)
     - Wire 37 existing test files into CI
     - Externalize all hardcoded credentials
   - Dependencies: Phase 0 (shared IaC), Phase 1 patterns
   - Blocks: None
   - Estimated Effort: Medium

**Parallel Tracks:**
- camunda-rest-service, bpmn-miwg-test-suite, and camunda-bpm-examples can be modernized concurrently (no inter-service dependencies)

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize all services, implement advanced capabilities, continuous improvement.

**Services in Scope:**
All 5 services participate in Phase 3 for advanced optimization after foundational work is complete.

**Advanced Activities:**
1. **Decomposition** — Extract microservices from monoliths using Strangler Fig pattern:
   - camunda-invoice: Extract invoice process as independent service
   - camunda8-order-process: Extract DoWork and DoLongWork as independent worker services
   - camunda-rest-service: Extract Java delegate, external task, and script task as independent services
   - camunda-bpm-examples: Extract external task handlers as reference microservices
2. **Event-Driven Architecture** — Introduce Amazon EventBridge for process lifecycle events
3. **Advanced Observability** — SLO definitions, business metrics dashboards, anomaly detection
4. **Identity Federation** — Amazon Cognito integration with Camunda web applications
5. **API Gateway** — Centralized API management with versioning and throttling
6. **Camunda Platform Modernization** — Evaluate migration from Camunda 7 (EOL) to Camunda 8 or AWS Step Functions

**Estimated Effort**: High

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6+ months (with 3 parallel tracks in Phase 2)
**Key Risk**: The volume of foundational blockers (33 items) means Phase 0 is critical and must not be rushed.
## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 5 | 100% | High | High |
| Move to Containers | 5 | 100% | High | Medium |
| Move to Open Source | 0 | 0% | Low | — |
| Move to Managed Databases | 3 | 60% | High | Medium |
| Move to Managed Analytics | 0 | 0% | Low | — |
| Move to Modern DevOps | 5 | 100% | High | Medium |
| Move to AI | 0 | 0% | Low | — |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing
a single at-a-glance view of pathway coverage across the portfolio. Each repo appears
in exactly one column per pathway row.

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | — | — |
| Move to Containers | camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | — | — |
| Move to Open Source | — | camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | — |
| Move to Managed Databases | camunda-invoice, camunda-rest-service, camunda-bpm-examples | camunda8-order-process, bpmn-miwg-test-suite | — |
| Move to Managed Analytics | — | camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | — |
| Move to Modern DevOps | camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | — | — |
| Move to AI | — | camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples | — |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| camunda-invoice | ✅ | ✅ | — | ✅ | — | ✅ | — |
| camunda8-order-process | ✅ | ✅ | — | — | — | ✅ | — |
| camunda-rest-service | ✅ | ✅ | — | ✅ | — | ✅ | — |
| bpmn-miwg-test-suite | ✅ | ✅ | — | — | — | ✅ | — |
| camunda-bpm-examples | ✅ | ✅ | — | ✅ | — | ✅ | — |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Open Source may precede Move to Managed Databases (migrate off proprietary first) — N/A for this portfolio as Move to Open Source is not triggered
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is often a prerequisite for Move to AI (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps (all 5 services) — enables all other pathways
- **Track 2**: Move to Containers (all 5 services) + Move to Managed Databases (3 services) — can run concurrently after DevOps foundation
- **Track 3**: Move to Cloud Native (all 5 services) — follows containerization

### Pathway Details

#### Move to Cloud Native

- **Services Affected**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples (5 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - APP-Q2 < 3: affects 5 services (all monoliths)
  - INF-Q1 < 3: affects 5 services (no managed compute)
  - APP-Q3 < 3: affects 5 services (predominantly synchronous)
- **Representative AWS Services**: Lambda, API Gateway, Step Functions, EventBridge, ECS/EKS, Aurora
- **Key Activities**:
  1. Portfolio-level: Define microservices architecture patterns and reference implementations
  2. Per-service: Decompose monoliths using Strangler Fig, starting with BPMN task type boundaries
- **Cross-Service Synergies**: All services use Camunda BPMN — shared decomposition patterns, shared Strangler Fig approach, shared Anti-corruption Layer templates
- **Estimated Effort**: High across 5 services
- **Roadmap Phase Alignment**: Phase 3 (Advanced) — after containerization and DevOps foundation
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Containers

- **Services Affected**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples (5 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q1 = 1: affects 5 services (no managed compute, no container definitions)
- **Representative AWS Services**: ECS, Fargate, ECR, EKS
- **Key Activities**:
  1. Portfolio-level: Create shared Dockerfile templates for Java Spring Boot applications
  2. Per-service: Create Dockerfiles, configure multi-stage builds, deploy to ECS Fargate
- **Cross-Service Synergies**: All services are Java/Spring Boot — single Dockerfile pattern covers 80% of needs. Shared ECR repository structure and ECS cluster configuration.
- **Estimated Effort**: Medium across 5 services
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) and Phase 2 (Foundation)
- **Relevant Learning Materials**: Module 3 — Move to Containers

#### Move to Managed Databases

- **Services Affected**: camunda-invoice, camunda-rest-service, camunda-bpm-examples (3 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q2 = 1: affects 3 services (H2 embedded databases, not production-grade)
  - DATA-Q3 < 3: affects 3 services (no production engine version pinning)
- **Representative AWS Services**: Aurora PostgreSQL, RDS PostgreSQL, DMS
- **Key Activities**:
  1. Portfolio-level: Define shared Aurora PostgreSQL IaC module with Multi-AZ, backups, PITR
  2. Per-service: Replace H2 with Aurora PostgreSQL, update JDBC driver, configure connection pooling
- **Cross-Service Synergies**: All 3 services use Camunda 7 which natively supports PostgreSQL. Shared Aurora module and connection configuration pattern.
- **Estimated Effort**: Medium across 3 services
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) and Phase 2 (Foundation)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Modern DevOps

- **Services Affected**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples (5 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q10 = 1: affects 5 services (zero IaC coverage)
  - INF-Q11 < 3: affects 3 services (no CI/CD at all)
  - OPS-Q5 = 1: affects 5 services (no deployment strategy)
- **Representative AWS Services**: CloudFormation, CDK, CodeBuild, CodePipeline, CodeDeploy, X-Ray, CloudWatch
- **Key Activities**:
  1. Portfolio-level: Create shared IaC repository, CI/CD pipeline templates, deployment strategy standards
  2. Per-service: Apply IaC modules, create service-specific pipelines, implement blue/green deployments
- **Cross-Service Synergies**: Shared IaC modules (VPC, ECS, Aurora) benefit all services. Shared CI/CD pipeline template reduces per-service setup to configuration.
- **Estimated Effort**: Medium across 5 services
- **Roadmap Phase Alignment**: Phase 0 (Cross-Cutting Foundation)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: None (0 total)
- **Portfolio Priority**: Low
- **Aggregation**: Move to AI: Triggered in 0 of 5 services (5 services had no AI intent in context — pathway correctly suppressed)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
  - Already present (AI frameworks detected): —
- **Common Trigger Criteria**: N/A — pathway not triggered for any service
- **Representative AWS Services**: Amazon Bedrock, SageMaker, Amazon Q Developer
- **Key Activities**: N/A — no services require AI pathway activities at this time
- **Cross-Service Synergies**: N/A
- **Estimated Effort**: N/A
- **Roadmap Phase Alignment**: Phase 3 (if triggered in future)
- **Relevant Learning Materials**: Module 7 — Move to AI
## Integration Opportunities

### Shared Service Extraction

**Opportunity: Shared IaC Module Library**
- **Current State**: Zero IaC across all 5 services — each would need to build from scratch
- **Proposed Solution**: Create a shared IaC repository with reusable CDK constructs or Terraform modules for VPC, ECS cluster, Aurora PostgreSQL, IAM roles, CloudWatch alarms, and ECR repositories
- **Benefits**: Consistency across services, reduced duplication, faster onboarding, standardized security baselines
- **Effort**: Medium
- **Priority**: High (Phase 0 activity)

**Opportunity: Shared CI/CD Pipeline Templates**
- **Current State**: Fragmented CI/CD — Jenkins (1), GitHub Actions (2 with limited scope), none (2)
- **Proposed Solution**: Create reusable GitHub Actions workflow templates for Java/Maven build, test, security scan, Docker build, and ECS deployment
- **Benefits**: Consistent quality gates, reduced pipeline setup time, standardized security scanning
- **Effort**: Medium
- **Priority**: High (Phase 0 activity)

**Opportunity: Camunda Platform Upgrade Coordination**
- **Current State**: 3 services use Camunda 7 (EOL), 1 service uses Camunda 8, 1 is not Camunda-dependent
- **Proposed Solution**: Coordinate Camunda 7 → Camunda 8 (or AWS Step Functions) migration across the portfolio. Develop shared migration tooling and reference patterns.
- **Benefits**: Platform consolidation, reduced maintenance burden, access to cloud-native Camunda 8 features
- **Effort**: High
- **Priority**: Medium (Phase 3 activity)

### Event-Driven Architecture

**Opportunity: Process Lifecycle Event Bus**
- **Current State**: No cross-service event communication. Each Camunda service operates independently with no shared event infrastructure.
- **Proposed Solution**: Introduce Amazon EventBridge as a shared event bus. Publish standard events (process.started, task.completed, process.failed, sla.breached) from all Camunda services.
- **Benefits**: Decoupled integration, real-time process monitoring dashboard, cross-service event correlation
- **Effort**: Medium

### API Gateway Consolidation

**Opportunity: Unified Camunda API Gateway**
- **Current State**: Each Camunda service exposes its REST API directly on port 8080 with no gateway, throttling, or centralized authentication.
- **Proposed Solution**: Deploy a shared API Gateway (or ALB) with Cognito authorizer, path-based routing to each service's REST API, throttling, and request validation.
- **Benefits**: Centralized authentication, consistent rate limiting, unified monitoring, cost reduction
- **Effort**: Medium

### Observability Unification

**Opportunity: Centralized Observability Platform**
- **Current State**: Zero observability across all 5 services. No tracing, no metrics, no alerting.
- **Proposed Solution**: Deploy a shared observability stack: OpenTelemetry Collector → X-Ray (tracing) + CloudWatch (metrics/logs/alarms) + shared dashboards
- **Benefits**: End-to-end tracing across all services, consistent metrics, unified alerting, reduced tool sprawl
- **Effort**: Medium

---

## Risk Analysis

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| Hardcoded secrets in version control (SEC-Q5) | High | High | 🔴 Critical | Rotate all credentials immediately. Move to Secrets Manager. | Phase 0 |
| Zero IaC — no reproducible deployments (INF-Q10) | High | High | 🔴 Critical | Adopt IaC as first modernization priority. Create shared modules. | Phase 0 |
| Camunda 7 EOL — no vendor support (APP-Q1 context) | High | Medium | 🟠 High | Plan Camunda 7 → 8 or Step Functions migration. | Phase 3 |
| No deployment strategy — manual releases (OPS-Q5) | High | Medium | 🟠 High | Implement blue/green deployments via CodeDeploy + ECS. | Phase 1 |
| No security scanning — undetected CVEs (SEC-Q7) | High | Medium | 🟠 High | Add Dependabot + OWASP dependency-check to all repos. | Phase 0 |
| No encryption at rest — data exposure risk (SEC-Q2) | High | Medium | 🟠 High | Enforce encryption on all AWS resources via IaC defaults. | Phase 0 |
| H2 databases in production — data loss (INF-Q2) | Medium | High | 🟠 High | Migrate to Aurora PostgreSQL with Multi-AZ and PITR. | Phase 1-2 |
| No distributed tracing — blind debugging (OPS-Q1) | High | Low | 🟡 Medium | Deploy OpenTelemetry + X-Ray across all services. | Phase 0 |
| No auto-scaling — capacity failures (INF-Q7) | Medium | Medium | 🟡 Medium | Configure ECS auto-scaling after containerization. | Phase 1-2 |
| No incident response — ad hoc recovery (OPS-Q7) | Medium | Medium | 🟡 Medium | Create shared runbooks for common Camunda scenarios. | Phase 2 |
| Java version fragmentation (APP-Q1 context) | Low | Low | 🟢 Low | Standardize on Java 17/21 LTS across all services. | Phase 2-3 |

### High-Risk Dependencies

No services have both score < 2.0 AND fan-in >= 3. All services are independent (fan-in = 0, fan-out = 0). However, all 5 services score below 2.0, making the entire portfolio high-risk from a modernization readiness perspective.

### Single Points of Failure

Without dependency data, blast radius cannot be calculated. However, each service is a single-instance deployment with no redundancy:
- **camunda-invoice**: Single WAR deployment, no HA, no multi-AZ
- **camunda8-order-process**: Single worker process, no failover
- **camunda-rest-service**: Single Spring Boot process with embedded H2
- **camunda-bpm-examples**: Single Spring Boot JAR, no redundancy

### Circular Dependency Risks

✅ No circular dependencies detected — all services are independent.

### Data Availability Risks

- **camunda-rest-service**: Uses H2 file database (`camunda-h2-database`) — data loss on disk failure with no backup
- **camunda-bpm-examples**: Uses H2 in-memory databases — data loss on every restart
- **camunda-invoice**: No managed database provisioned despite testing against Aurora PostgreSQL in CI

### Observability Blind Spots

All 5 services are observability blind spots — zero tracing (OPS-Q1=1 across all), zero metrics (OPS-Q3=1 across all), zero alerting (OPS-Q4=1 across all). No service has any observability instrumentation.

---

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + service teams

The portfolio has 33 cross-cutting Foundational Blockers (>= 5 threshold), strongly recommending a centralized platform team.

**Platform Team**:
- Responsibilities: Shared IaC modules, CI/CD pipeline templates, observability platform, security baselines, networking
- Skills Required: IaC (CDK/Terraform), AWS (ECS, Aurora, CloudWatch, IAM), CI/CD (GitHub Actions), Container (Docker, ECR), Security (Secrets Manager, KMS)
- Recommended Size: 2-3 engineers

**Service Teams**:
- Responsibilities: Service-specific containerization, database migration, test coverage, decomposition
- Skills Required: Java (Spring Boot), Camunda BPM/Zeebe, Docker, PostgreSQL, OpenTelemetry
- Recommended Size: 1-2 engineers per service

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| IaC (CDK or Terraform) | Phase 0: shared infrastructure | No | High |
| Docker / Container build | Phase 1-2: containerization | No | High |
| ECS / Fargate | Phase 1-2: managed compute | No | High |
| Aurora PostgreSQL | Phase 1-2: database migration | Partial (CI testing) | High |
| GitHub Actions CI/CD | Phase 0-1: pipeline creation | Partial (2 services) | High |
| OpenTelemetry / X-Ray | Phase 0: observability | No | Medium |
| AWS Secrets Manager | Phase 0: secrets remediation | No | High |
| CodeDeploy (blue/green) | Phase 1-2: deployment strategy | No | Medium |
| Camunda 8 / Zeebe | Phase 3: platform migration | Partial (1 service) | Low |

### Training Recommendations

**Phase 0 Priority (Immediate):**
1. IaC — CDK for Java developers or Terraform fundamentals
2. Docker — Container basics, multi-stage builds, security best practices
3. AWS Security — Secrets Manager, KMS, IAM best practices

**Phase 1-2 Priority:**
4. ECS/Fargate — Container orchestration, task definitions, service auto-scaling
5. Aurora PostgreSQL — Migration from H2, Multi-AZ configuration, PITR
6. CI/CD — GitHub Actions advanced workflows, CodeDeploy blue/green

**Phase 3 Priority:**
7. Microservices patterns — Strangler Fig, Anti-corruption Layer, Saga
8. Event-driven architecture — EventBridge, SQS patterns
9. Observability — OpenTelemetry, X-Ray, CloudWatch dashboards

### External Support

**Recommended AWS Professional Services or Partner engagement for:**
- **Phase 0**: Architecture review and IaC foundation setup (2-4 weeks)
- **Phase 1**: Reference containerization and first production deployment (2-4 weeks)
- **Phase 3**: Camunda 7 EOL migration strategy and execution planning (4-8 weeks)
- **Ongoing**: AWS Well-Architected Review after each phase completion
## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | All 5 services have overall score < 2.5, indicating significant modernization effort | 5 of 5 services score below 2.5 (threshold: 3+ repos) | Request MAP engagement via AWS Solutions Architect |
| Optimization and Licensing Analysis | OLA | Oracle and SQL Server JDBC drivers detected in camunda-invoice | camunda-invoice has Oracle (v23.5.0.24.07) and SQL Server (v8.4.1) JDBC drivers; CI matrix tests against Oracle 19/23 and SQL Server 2017/2019/2022 | Request OLA engagement to assess commercial database licensing optimization |
| Experience-Based Acceleration | EBA | All 5 services have triggered pathways AND overall score < 3.0 | 5 of 5 services have at least one triggered pathway AND score < 3.0 (threshold: 2+). Focus: Move to Cloud Native (100%), Move to Modern DevOps (100%) | Request EBA engagement focused on Move to Containers and Move to Modern DevOps pathways |
| ISV Workload Migration Program | ISV WMP | Camunda BPM is a third-party commercial workflow platform used across 4/5 services | Camunda Platform 7 (third-party ISV software) is the core of camunda-invoice, camunda-rest-service, and camunda-bpm-examples; Camunda 8 SaaS is used by camunda8-order-process | Request ISV WMP engagement for Camunda platform modernization |

### Program Details

**Migration Acceleration Program (MAP)**
- **Why recommended**: All 5 services in the portfolio score below 2.5, with the portfolio average at 1.51/4.0. This indicates a significant migration and modernization effort requiring coordinated planning, funding support, and AWS partner resources.
- **What it provides**: Migration funding credits, partner support, migration methodology, and tools to accelerate the move to AWS.
- **Suggested timing**: Engage during Phase 0 to align MAP benefits with the infrastructure foundation build-out.

**Optimization and Licensing Analysis (OLA)**
- **Why recommended**: camunda-invoice includes Oracle (driver v23.5.0.24.07) and SQL Server (driver v8.4.1) JDBC drivers with CI testing against Oracle 19/23 and SQL Server 2017/2019/2022. This indicates potential commercial database licensing costs that could be optimized by migrating to Aurora PostgreSQL.
- **What it provides**: Analysis of current database licensing costs and recommendations for license optimization through migration to open-source managed databases.
- **Suggested timing**: Engage during Phase 0-1 to inform database migration decisions in the roadmap.

**Experience-Based Acceleration (EBA)**
- **Why recommended**: All 5 services have triggered modernization pathways with overall scores below 3.0. The most prevalent pathways are Move to Cloud Native (100%), Move to Containers (100%), and Move to Modern DevOps (100%).
- **What it provides**: Hands-on workshops and immersive experiences focused on specific modernization pathways, guided by AWS experts.
- **Suggested timing**: Engage during Phase 0-1 with workshops focused on containerization (Move to Containers) and CI/CD pipeline creation (Move to Modern DevOps).

**ISV Workload Migration Program (ISV WMP)**
- **Why recommended**: Camunda BPM is a third-party ISV workflow platform used across 4 of 5 services. The portfolio includes both Camunda 7 (EOL) and Camunda 8 SaaS deployments. Migrating ISV workloads to AWS requires specialized planning.
- **What it provides**: Migration funding and partner support specifically for ISV/third-party software workloads running on AWS.
- **Suggested timing**: Engage during Phase 3 when Camunda platform modernization is planned.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

---

## Recommended Self-Paced Learning Materials

> Included modules are relevant to the portfolio's 4 triggered pathways and identified skill gaps.

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- EKS Workshop — https://www.eksworkshop.com/

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Amazon RDS for Oracle Getting Started — https://skillbuilder.aws/learn/YMYMJUMAET/amazon-rds-for-oracle-getting-started/74GQB3CA9U
- Amazon RDS for SQL Server Getting Started — https://skillbuilder.aws/learn/WSV85JHZFF/amazon-rds-for-sql-server-getting-started/E446MXPEYH
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 1
- **Finding**: No IaC tools are used across any of the 5 services. Zero IaC coverage means there is no tool to standardize — the portfolio has a complete absence of infrastructure-as-code.
- **Evidence**: INF-Q10 = 1 across all 5 repos. No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found in any repository.
- **Recommendation**: This is a greenfield opportunity — adopt a single IaC tool (CDK for Java teams, given the all-Java portfolio, or Terraform for multi-language flexibility) from day one. Create a shared IaC repository with reusable modules before any service-specific IaC work begins.
- **Contextual Annotations**: This finding reinforces the severity of INF-Q10 Foundational Blocker across all 5 services. The absence of IaC is not just a per-service gap — it's a portfolio-wide capability void.

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: No shared observability exists. Each service has independent (or no) observability. No shared CloudWatch Log Groups, no shared X-Ray/ADOT configuration, no shared dashboards, no consistent metric namespaces. OPS-Q1 (tracing), OPS-Q2 (SLOs), and OPS-Q3 (metrics) all score 1 across every service. Camunda metrics are explicitly disabled in 2 services (`metrics.enabled: false`).
- **Evidence**: OPS-Q1=1 (all 5), OPS-Q2=1 (all 5), OPS-Q3=1 (all 5). No OpenTelemetry, X-Ray, or CloudWatch dependencies in any `pom.xml`. `application.yaml` files in camunda-bpm-examples explicitly disable Camunda metrics.
- **Recommendation**: Establish a centralized observability platform before containerizing services. Deploy OpenTelemetry Collector with X-Ray and CloudWatch exporters. Define shared CloudWatch Log Group naming conventions and metric namespaces (e.g., `bao-demo/<service-name>`). Create a shared portfolio dashboard.
- **Contextual Annotations**: This finding provides context for OPS-Q1, OPS-Q2, OPS-Q3, and OPS-Q4 Foundational Blockers. A shared observability platform addresses all 4 gaps simultaneously across all 5 services.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 4
- **Finding**: No circular dependencies exist. No dependencies of any kind were detected between the 5 services — each operates independently with no inter-service runtime communication. The services share the Camunda ecosystem as a technology choice but do not call each other at runtime.
- **Evidence**: Dependency analysis in Step 4 found no direct service-to-service dependencies. All fan-in and fan-out values are 0. No shared databases, no REST API calls between services, no message queue connections.
- **Recommendation**: No action needed for circular dependency resolution. When services begin to communicate (e.g., via EventBridge events or shared API Gateway), establish dependency monitoring to detect cycles early.
- **Contextual Annotations**: None — this finding does not affect individual service concerns.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 2
- **Finding**: Moderate-to-high technology diversity exists across the portfolio. Java is the dominant language (5/5 services) but spans 3 versions (1.6, 11, 17). Additional languages include JavaScript/Node.js (2/5) and Groovy (2/5). CI/CD is fragmented across Jenkins (1), GitHub Actions (2), and none (2). Database references include H2, PostgreSQL, MySQL, Oracle, SQL Server, and DB2. Technology diversity score: 8 distinct technologies / 5 services = 1.6.
- **Evidence**: APP-Q1 scores vary from 2 (bpmn-miwg-test-suite, Java 1.6 target) to 4 (others, Java 11-17). CI/CD findings across INF-Q11 show 3 different tools. Database findings across INF-Q2 and DATA-Q3 show 6+ database platforms referenced.
- **Recommendation**: Standardize on Java 17/21 LTS, a single CI/CD platform (GitHub Actions), and Aurora PostgreSQL as the production database. Reduce the technology diversity score by consolidating fragmented tools. The all-Java portfolio provides a strong foundation for standardization.
- **Contextual Annotations**: None — technology diversity is a portfolio-level metric.

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: No shared security scanning pipeline, no shared WAF, and no unified vulnerability management exists across the portfolio. SEC-Q7 (security pipeline) scores 1 across all 5 services. No Dependabot, no SAST, no container scanning in any CI/CD pipeline. Secrets management (SEC-Q5) is critically deficient — 4 of 5 services have hardcoded credentials committed to version control. No shared IAM policies, no shared KMS keys, no shared Cognito configuration.
- **Evidence**: SEC-Q1=1 (all 5), SEC-Q2=1 (all 5), SEC-Q5 scores: 1,1,1,3,1 (bpmn-miwg-test-suite is the only service using GitHub Secrets properly). SEC-Q7=1 (all 5). No `.github/dependabot.yml` in 4 of 5 repos. No OWASP dependency-check in any Maven build.
- **Recommendation**: Establish a shared security posture immediately in Phase 0: (1) Add Dependabot to all 5 repositories, (2) Integrate OWASP dependency-check into all Maven builds, (3) Create a shared Cognito user pool for centralized identity, (4) Define shared KMS key policies and IAM role patterns, (5) Rotate all exposed credentials and move to Secrets Manager.
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-MOD-Q5 found that bpmn-miwg-test-suite (SEC-Q5=3) uses GitHub Secrets properly for credential management. This may serve as a reference pattern for the other 4 services — **verify** that the GitHub Secrets approach used in bpmn-miwg-test-suite's workflows can be adapted for the other services' CI/CD pipelines.
## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| bpmn-miwg-test-suite | application | P1 | 1.28 | 1.09 | 1.17 | 1.75 | 1.29 | 1.11 | 3 of 7 | 2 |
| camunda8-order-process | application | P0 | 1.37 | 1.27 | 1.83 | 1.75 | 1.00 | 1.00 | 3 of 7 | 1 |
| camunda-rest-service | application | P1 | 1.42 | 1.18 | 1.83 | 2.00 | 1.00 | 1.11 | 4 of 7 | 2 |
| camunda-bpm-examples | monorepo | P1 | 1.69 | 1.27 | 2.33 | 2.50 | 1.14 | 1.22 | 4 of 7 | 2 |
| camunda-invoice | monorepo | P0 | 1.80 | 1.45 | 2.17 | 2.75 | 1.43 | 1.22 | 4 of 7 | 1 |

### Individual Service Details

#### bpmn-miwg-test-suite

- **Overall Score**: 1.28 / 4.0
- **Repository Type**: application
- **Priority**: P1
- **Analysis Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.09
  - Application Architecture: 1.17
  - Data Platform: 1.75
  - Security Baseline: 1.29
  - Operations & Observability: 1.11
- **Top Gaps**:
  - INF-Q10: score 1 — No IaC found
  - INF-Q1: score 1 — No compute infrastructure
  - APP-Q2: score 1 — Single jar packaging with no module boundaries
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Modern DevOps
- **Key Recommendations**:
  - Add security scanning (Dependabot, OWASP) to GitHub Actions pipeline
  - Update Java target from 1.6 to 17
  - Add deployment verification and quality gates
- **Roadmap Phase**: Phase 2 — Foundation

#### camunda8-order-process

- **Overall Score**: 1.37 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Analysis Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.27
  - Application Architecture: 1.83
  - Data Platform: 1.75
  - Security Baseline: 1.00
  - Operations & Observability: 1.00
- **Top Gaps**:
  - SEC-Q5: score 1 — **CRITICAL**: Zeebe client credentials hardcoded in plaintext
  - INF-Q10: score 1 — Zero IaC files
  - INF-Q11: score 1 — No CI/CD pipeline
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Modern DevOps
- **Key Recommendations**:
  - Immediately rotate exposed Zeebe credentials
  - Containerize and deploy to ECS Fargate
  - Create CI/CD pipeline from scratch
- **Roadmap Phase**: Phase 1 — Quick Wins

#### camunda-rest-service

- **Overall Score**: 1.42 / 4.0
- **Repository Type**: application
- **Priority**: P1
- **Analysis Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.18
  - Application Architecture: 1.83
  - Data Platform: 2.00
  - Security Baseline: 1.00
  - Operations & Observability: 1.11
- **Top Gaps**:
  - INF-Q10: score 1 — No IaC
  - INF-Q11: score 1 — No CI/CD pipeline
  - INF-Q1: score 1 — No compute infrastructure
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize both Java app and Node.js worker
  - Replace H2 with Aurora PostgreSQL
  - Create CI/CD pipeline and wire existing tests into CI
- **Roadmap Phase**: Phase 2 — Foundation

#### camunda-bpm-examples

- **Overall Score**: 1.69 / 4.0
- **Repository Type**: monorepo
- **Priority**: P1
- **Analysis Date**: 2025-07-18
- **Category Scores**:
  - Infrastructure & DevOps: 1.27
  - Application Architecture: 2.33
  - Data Platform: 2.50
  - Security Baseline: 1.14
  - Operations & Observability: 1.22
- **Top Gaps**:
  - INF-Q10: score 1 — Zero IaC
  - INF-Q11: score 1 — No build/test CI/CD (only version bumping)
  - SEC-Q5: score 1 — Credentials hardcoded in multiple config files
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize example-invoice as reference deployment
  - Replace H2 with Aurora PostgreSQL
  - Wire 37 existing tests into CI pipeline
- **Roadmap Phase**: Phase 2 — Foundation

#### camunda-invoice

- **Overall Score**: 1.80 / 4.0
- **Repository Type**: monorepo
- **Priority**: P0
- **Analysis Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.45
  - Application Architecture: 2.17
  - Data Platform: 2.75
  - Security Baseline: 1.43
  - Operations & Observability: 1.22
- **Top Gaps**:
  - INF-Q10: score 1 — No IaC
  - INF-Q1: score 1 — Traditional app servers only
  - APP-Q2: score 1 — Tightly-coupled monolith with 30+ modules
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize WAR into Tomcat Docker image
  - Provision Aurora PostgreSQL (already tested in CI)
  - Extend Jenkins CI/CD with deployment automation
- **Roadmap Phase**: Phase 1 — Quick Wins

---

## Analysis Inventory

| # | Service | Report File | Analysis Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | bpmn-miwg-test-suite | example-reports/bao-demo/repos/bpmn-miwg-test-suite/bpmn-miwg-test-suite-mod-report.md | 2025-07-15 | application | 1.28 |
| 2 | camunda8-order-process | example-reports/bao-demo/repos/camunda8-order-process/camunda8-order-process-mod-report.md | 2025-07-15 | application | 1.37 |
| 3 | camunda-rest-service | example-reports/bao-demo/repos/camunda-rest-service/camunda-rest-service-mod-report.md | 2025-07-15 | application | 1.42 |
| 4 | camunda-bpm-examples | example-reports/bao-demo/repos/camunda-bpm-examples/camunda-bpm-examples-mod-report.md | 2025-07-18 | monorepo | 1.69 |
| 5 | camunda-invoice | example-reports/bao-demo/repos/camunda-invoice/camunda-invoice-mod-report.md | 2025-07-16 | monorepo | 1.80 |
