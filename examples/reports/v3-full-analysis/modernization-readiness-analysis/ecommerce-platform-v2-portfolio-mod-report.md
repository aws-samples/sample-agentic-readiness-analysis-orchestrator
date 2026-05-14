# Portfolio Modernization Readiness Analysis Report

**Date**: 2026-04-27
**Services Analyzed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.
**Technology Preferences**: Prefer: EKS, Aurora, DynamoDB, API Gateway, EventBridge, Bedrock, Terraform, GitOps; Avoid: self-managed-kafka, self-managed-kubernetes, oracle, manual-deployments

---

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 2.13 / 4.0 |
| Score Range | 1.67 – 2.65 |
| Highest Scoring Service | books-api (2.65) |
| Lowest Scoring Service | unishop-monolith (1.67) |
| Pathways Triggered (portfolio-wide) | 5 of 7 |
| Cross-Cutting Foundational Blockers | 20 |
| Cross-Cutting Improvement Opportunities | 5 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 1 | 20% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 4 | 80% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 0 | 0% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 2.47 | 1.45 | 3.00 | 0 |
| Application Architecture (APP) | 2.21 | 1.33 | 2.83 | 1 |
| Data Platform (DATA) | 2.75 | 2.25 | 3.25 | 0 |
| Security Baseline (SEC) | 1.88 | 1.29 | 2.57 | 0 |
| Operations & Observability (OPS) | 1.31 | 1.00 | 2.11 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 4 | 80% |
| infrastructure-only | 1 | 20% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| analysis_date | 2026-04-27 |
| total_services | 5 |
| portfolio_score | 2.13 |
| score_range_min | 1.67 |
| score_range_max | 2.65 |
| mature_services | 0 |
| partial_services | 1 |
| needs_work_services | 4 |
| not_ready_services | 0 |
| pathways_triggered | 5 |
| foundational_blockers | 20 |
| improvement_opportunities | 5 |
| category_inf | 2.47 |
| category_app | 2.21 |
| category_data | 2.75 |
| category_sec | 1.88 |
| category_ops | 1.31 |
| portfolio_level_avg | 2.0 |
## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| Java 8 (Spring Boot 2.1) | 1 (unishop-monolith) | 20% |
| TypeScript / JavaScript | 2 (aws-microservices, books-api) | 40% |
| PHP 8.2 | 1 (local-monolith) | 20% |
| HCL / Terraform | 1 (eks-saas-gitops) | 20% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| DynamoDB | NoSQL (Key-Value/Document) | 3 (aws-microservices, books-api, eks-saas-gitops) | Yes |
| MySQL (self-managed on EC2) | Relational | 1 (unishop-monolith) | No |
| RDS MySQL 8.4 | Relational | 1 (local-monolith) | Yes |
| Aurora MySQL (migration target) | Relational | 1 (unishop-monolith target) | Yes |
| SQLite (Gitea) | Relational (Embedded) | 1 (eks-saas-gitops) | No |

**Database Distribution**: 4 managed (DynamoDB ×3, RDS MySQL ×1), 2 self-managed (MySQL on EC2 ×1, SQLite ×1), 0 commercial, all open source or AWS-native

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| EC2 / VM-based | 1 (unishop-monolith) | 20% |
| Serverless (Lambda) | 2 (aws-microservices, books-api) | 40% |
| App Runner (Managed Containers) | 1 (local-monolith) | 20% |
| EKS (Managed Kubernetes) | 1 (eks-saas-gitops) | 20% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| CloudFormation | IaC | 2 (unishop-monolith, local-monolith) |
| CDK | IaC | 2 (aws-microservices, books-api pipeline) |
| SAM | IaC | 1 (books-api) |
| Terraform | IaC | 1 (eks-saas-gitops) |
| None / Manual | CI/CD | 3 (unishop-monolith, aws-microservices, local-monolith) |
| CodePipeline + CodeBuild | CI/CD | 1 (books-api) |
| Gitea Actions + Flux CD | CI/CD | 1 (eks-saas-gitops) |

### Standardization Opportunities

- **IaC Fragmentation (Critical)**: 4 distinct IaC tools (CloudFormation, CDK, SAM, Terraform) across 5 services. Portfolio preference is Terraform — consolidate all IaC to Terraform modules. books-api and aws-microservices currently use CDK/SAM; migrate to Terraform with GitOps workflows.
- **CI/CD Gap (Critical)**: 3 of 5 services have no functional CI/CD pipeline. Standardize on GitHub Actions or CodePipeline with GitOps delivery (preferred). books-api's CodePipeline pattern can serve as a reference implementation.
- **Database Consolidation**: DynamoDB is the most common database (3 services) and aligns with preferences. The self-managed MySQL on EC2 (unishop-monolith) is the highest-risk database — migrate to Aurora MySQL (preferred).
- **Compute Diversity**: 4 different compute patterns. For containerized workloads, standardize on EKS (preferred). Maintain Lambda for event-driven serverless workloads (aws-microservices, books-api).
- **Technology Diversity Score**: 14 distinct technologies / 5 services = 2.8 — indicates high fragmentation requiring active standardization effort.
## Service Dependency Map

> Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

| Source Service | Target Service | Type | Coupling | Description |
|---------------|---------------|------|----------|-------------|
| unishop-monolith | eks-saas-gitops | shared_infra | Low | EKS will be the centralized platform for containerized workloads — unishop containerization targets EKS (inferred) |
| local-monolith | eks-saas-gitops | shared_infra | Low | Containerize and deploy on EKS — monolith migration targets EKS platform (inferred) |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| eks-saas-gitops | 2 | 0 | 40% | Foundation | 2.19 |
| unishop-monolith | 0 | 1 | 0% | Leaf | 1.67 |
| local-monolith | 0 | 1 | 0% | Leaf | 1.88 |
| aws-microservices | 0 | 0 | 0% | Isolated | 2.24 |
| books-api | 0 | 0 | 0% | Isolated | 2.65 |

### Foundation Services (High Fan-In)

- **eks-saas-gitops** (Fan-In: 2, Fan-Out: 0) — This is the EKS infrastructure platform that both unishop-monolith and local-monolith will target for containerized deployments. It must be hardened and modernized before dependent services migrate to EKS. Changes to this platform affect 40% of the portfolio.

### Circular Dependencies

✅ No circular dependencies detected.
## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts. Address these first — nothing else matters until these are resolved.

1. **OPS-Q7: Incident Response Automation** — 5 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=1, eks-saas-gitops=1
   - **Impact**: No runbooks or automated remediation exist anywhere in the portfolio. Incident response is entirely ad hoc across all services. MTTR is unpredictable.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Create a shared runbook repository with service-specific runbooks. Implement SSM Automation documents for common remediation patterns (restart, failover, rollback). Establish incident response procedures and on-call rotations.

2. **OPS-Q8: Observability Ownership** — 5 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=1, eks-saas-gitops=1
   - **Impact**: No CODEOWNERS, no dashboards, no alarm ownership across any service. No one is formally responsible for monitoring.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Create CODEOWNERS files for all repos. Define per-service CloudWatch dashboards via IaC. Assign named alarm owners and establish on-call rotation. Tag all observability resources with team ownership.

3. **OPS-Q1: Distributed Tracing** — 4 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=3, eks-saas-gitops=1
   - **Impact**: Cannot trace requests across services. Debugging cross-service issues and monitoring AI agent actions is impossible without tracing.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy ADOT (AWS Distro for OpenTelemetry) as the standard tracing collector. Enable X-Ray on all Lambda functions. Add OpenTelemetry SDK to Java, PHP, and TypeScript services. books-api's X-Ray setup can serve as reference.

4. **OPS-Q2: SLO Definitions** — 4 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=2, eks-saas-gitops=1
   - **Impact**: No formal service level targets anywhere. Cannot measure if the platform meets user expectations or prioritize modernization investment.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Define SLOs for all customer-facing services. Start with availability (99.9%) and p99 latency targets. Implement CloudWatch Composite Alarms and error budget tracking.

5. **OPS-Q3: Business Metrics** — 4 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=1, eks-saas-gitops=2
   - **Impact**: Cannot track business outcomes (orders, returns, checkouts, catalog updates). No data-driven modernization prioritization.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Portfolio-Level Recommendation**: Publish custom CloudWatch metrics from all services using EMF (Embedded Metrics Format) for Lambda or CloudWatch SDK for containers. Create a portfolio-level CloudWatch dashboard combining business metrics from all services.

6. **OPS-Q4: Anomaly Detection and Alerting** — 4 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=2, eks-saas-gitops=1
   - **Impact**: No proactive alerting. Failures are discovered only when users report issues. No anomaly detection for gradual degradation.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy centralized alerting via SNS topics with PagerDuty/OpsGenie integration. Add CloudWatch alarms for all services. Enable anomaly detection on error rates and latency.

7. **OPS-Q6: Integration Testing** — 4 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=3, eks-saas-gitops=1
   - **Impact**: No automated tests in 4 of 5 services. Regressions reach production undetected. Decomposition is extremely risky without test coverage.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Establish testing standards: unit tests for all new code, integration tests for API endpoints, contract tests for inter-service APIs. books-api's test pattern (Mocha/Chai e2e with Cognito auth) can serve as reference.

8. **APP-Q5: API Versioning** — 4 of 4 applicable services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=1 (eks-saas-gitops=N/A)
   - **Impact**: No API versioning on any service. Breaking API changes affect all consumers instantly. Critical blocker for AI agent integration — agents need stable API contracts.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Portfolio-Level Recommendation**: Mandate URL-path versioning (`/v1/`) for all APIs before AI agent integration. Generate OpenAPI specifications from all API definitions for agent tool discovery via Amazon Bedrock.

9. **INF-Q11: CI/CD Automation** — 3 of 5 services score < 2
   - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=4, eks-saas-gitops=2
   - **Impact**: 3 services have no CI/CD pipeline at all. All deployments are manual. Blocks safe, repeatable delivery for the majority of the portfolio.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith
   - **Portfolio-Level Recommendation**: Establish CI/CD pipelines for all services as Phase 0 priority. Use GitHub Actions or CodePipeline with GitOps delivery. Reference books-api's pipeline (CodePipeline with canary deployment and pre-traffic hooks).

10. **OPS-Q5: Deployment Strategy** — 3 of 5 services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=4, eks-saas-gitops=2
    - **Impact**: 3 services deploy directly to production with no staged rollout or rollback capability.
    - **Affected Services**: unishop-monolith, aws-microservices, local-monolith
    - **Portfolio-Level Recommendation**: Implement canary deployments: Lambda alias traffic shifting for serverless services, Argo Rollouts/Flagger for EKS workloads. Avoid manual deployments (per preferences).

11. **SEC-Q1: Audit Logging** — 3 of 5 services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=2, books-api=2, eks-saas-gitops=1
    - **Impact**: No CloudTrail in 3 services. No forensic capability after security incidents. Compliance risk.
    - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
    - **Portfolio-Level Recommendation**: Enable CloudTrail organization-wide with centralized S3 bucket and Object Lock for immutable storage. Add CloudTrail to all IaC definitions.

12. **SEC-Q3: API Authentication** — 3 of 5 services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=2, books-api=3, eks-saas-gitops=1
    - **Impact**: 3 services have completely unauthenticated APIs. Anyone can access, modify, or delete data. Critical security vulnerability for e-commerce platform.
    - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
    - **Portfolio-Level Recommendation**: Deploy Amazon Cognito as the portfolio-wide identity provider. Add Cognito authorizers to all API Gateway endpoints. For EKS, integrate OIDC authentication with Argo Workflows and Kubecost.

13. **SEC-Q4: Centralized Identity** — 3 of 5 services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=1, books-api=3, eks-saas-gitops=2
    - **Impact**: Each service manages authentication independently or has none. No SSO, no federated identity, no unified access control.
    - **Affected Services**: unishop-monolith, aws-microservices, local-monolith
    - **Portfolio-Level Recommendation**: Implement centralized Cognito User Pool for the entire portfolio. Enable OIDC federation for all services. Use machine-to-machine OAuth2 (client credentials) for AI agent authentication.

14. **SEC-Q7: Application Security Pipeline** — 3 of 5 services score < 2
    - **Score Distribution**: unishop=2, aws-microservices=1, local-monolith=2, books-api=1, eks-saas-gitops=1
    - **Impact**: No automated security scanning in CI/CD. Vulnerable dependencies reach production undetected.
    - **Affected Services**: aws-microservices, books-api, eks-saas-gitops
    - **Portfolio-Level Recommendation**: Add security scanning to all CI/CD pipelines: SAST (Semgrep/CodeGuru), dependency scanning (npm audit, Dependabot), container scanning (Trivy, ECR Enhanced Scanning). Block builds on critical findings.

15. **INF-Q8: Backup and Recovery** — 3 of 5 services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=1, local-monolith=3, books-api=1, eks-saas-gitops=2
    - **Impact**: 3 services have no backup strategy. Data loss from accidental deletion or corruption has no recovery path.
    - **Affected Services**: unishop-monolith, aws-microservices, books-api
    - **Portfolio-Level Recommendation**: Enable DynamoDB PITR on all tables. Set RemovalPolicy to RETAIN for production resources. Create AWS Backup plans. Migrate unishop self-managed MySQL to Aurora MySQL with automated backups.

16. **DATA-Q1: Unstructured Data** — 3 of 4 applicable services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=2, local-monolith=1, books-api=1 (eks-saas-gitops=N/A)
    - **Impact**: No unstructured data storage. Product images referenced but not managed. No document processing capability for AI agent use cases (return receipts, product documents).
    - **Affected Services**: unishop-monolith, local-monolith, books-api
    - **Portfolio-Level Recommendation**: Add S3 buckets for product images, documents, and unstructured data. Use CloudFront for image delivery. Enable Amazon Textract for document processing. Feed S3 content into Bedrock Knowledge Bases for RAG.

17. **INF-Q5: Network Security** — 2 of 5 services score < 2
    - **Score Distribution**: unishop=2, aws-microservices=1, local-monolith=3, books-api=1, eks-saas-gitops=2
    - **Impact**: 2 serverless services (aws-microservices, books-api) have no network isolation — Lambda runs outside VPC.
    - **Affected Services**: aws-microservices, books-api
    - **Portfolio-Level Recommendation**: Add VPC endpoints for DynamoDB. Configure WAF on API Gateway endpoints. Consider VPC-attached Lambda for sensitive workloads.

18. **INF-Q4: Async Messaging** — 2 of 5 services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=3, local-monolith=1, books-api=3, eks-saas-gitops=4
    - **Impact**: 2 monolith services have no messaging. Cross-domain state changes are tightly coupled.
    - **Affected Services**: unishop-monolith, local-monolith
    - **Portfolio-Level Recommendation**: Introduce EventBridge (preferred) as the portfolio-wide event bus. Emit domain events from all services. Use EventBridge rules for cross-service integration and AI agent triggers.

19. **APP-Q3: Async Communication** — 2 of 4 applicable services score < 2
    - **Score Distribution**: unishop=1, aws-microservices=3, local-monolith=1, books-api=3 (eks-saas-gitops=N/A)
    - **Impact**: Both monoliths rely entirely on synchronous communication. Decomposition requires async patterns.
    - **Affected Services**: unishop-monolith, local-monolith
    - **Portfolio-Level Recommendation**: Adopt EventBridge event-driven patterns during monolith decomposition. Model key domain events (OrderCreated, InventoryReserved, ReturnRequested).

20. **OPS-Q9: Resource Tagging** — 2 of 5 services score < 2
    - **Score Distribution**: unishop=2, aws-microservices=1, local-monolith=2, books-api=2, eks-saas-gitops=1
    - **Impact**: 2 services have virtually no tags. Cost allocation and ownership tracking impossible.
    - **Affected Services**: aws-microservices, eks-saas-gitops
    - **Portfolio-Level Recommendation**: Define a portfolio-wide tagging standard (Environment, Project, Team, CostCenter, ManagedBy). Apply via IaC default_tags. Deploy AWS Config required-tags rule for enforcement.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking. Address as capacity allows or in parallel with other modernization work.

1. **APP-Q6: Service Discovery** — 4 of 4 applicable services score < 3
   - **Score Distribution**: unishop=2, aws-microservices=2, local-monolith=2, books-api=2 (eks-saas-gitops=N/A)
   - **Impact**: All application services use static environment variables for endpoint configuration. No dynamic discovery mechanism.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
   - **Portfolio-Level Recommendation**: Use Kubernetes-native service discovery for EKS workloads and API Gateway as the service catalog for external consumers. Register all APIs in AWS Cloud Map for dynamic discovery.

2. **INF-Q6: API Entry Point** — 3 of 5 services score < 3
   - **Score Distribution**: unishop=1, aws-microservices=2, local-monolith=3, books-api=3, eks-saas-gitops=2
   - **Impact**: 3 services lack proper API management features (throttling, validation, WAF).
   - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy Amazon API Gateway (preferred) as the unified entry point. Add throttling, request validation, and WAF integration for all APIs.

3. **SEC-Q6: Compute Hardening** — 3 of 5 services score < 3
   - **Score Distribution**: unishop=2, aws-microservices=2, local-monolith=3, books-api=3, eks-saas-gitops=2
   - **Impact**: 3 services have incomplete patching and no vulnerability scanning.
   - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Enable AWS Inspector across the portfolio. Update all deprecated runtimes (Lambda NODEJS_14_X, Java 8). Use Bottlerocket for EKS nodes. Add SSM Patch Manager for EC2 instances.

4. **SEC-Q5: Secrets Management** — 3 of 5 services score < 3
   - **Score Distribution**: unishop=1, aws-microservices=3, local-monolith=2, books-api=3, eks-saas-gitops=2
   - **Impact**: Hardcoded credentials in unishop. Environment variable secrets in local-monolith and eks-saas-gitops. No rotation.
   - **Affected Services**: unishop-monolith, local-monolith, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Migrate all credentials to AWS Secrets Manager with automatic rotation. Remove hardcoded credentials from source code. Use External Secrets Operator for Kubernetes integration.

5. **INF-Q3: Workflow Orchestration** — 3 of 5 services score < 3
   - **Score Distribution**: unishop=2, aws-microservices=2, local-monolith=1, books-api=3, eks-saas-gitops=4
   - **Impact**: 3 services lack workflow orchestration for multi-step business processes. The local-monolith has a complex fulfillment workflow hardcoded in a single PHP file.
   - **Affected Services**: unishop-monolith, aws-microservices, local-monolith
   - **Portfolio-Level Recommendation**: Adopt AWS Step Functions for multi-step workflows in serverless services. For EKS workloads, leverage Argo Workflows (already deployed on eks-saas-gitops). Use EventBridge for event-driven workflow triggers.

### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 2.47 / 4.0**

**Common Patterns:**
- IaC adoption: all 5 services have some form of IaC (score 3 across the board)
- Managed compute: 4 of 5 services use managed compute (Lambda, App Runner, EKS); only unishop is on raw EC2

**Critical Gaps:**
1. CI/CD Automation (INF-Q11): 3 services have no pipeline — highest-priority cross-cutting blocker
2. Backup/Recovery (INF-Q8): 3 services have no backup strategy — data loss risk
3. Network Security (INF-Q5): 2 serverless services have no VPC isolation

#### Application Architecture

**Portfolio Score: 2.21 / 4.0** (4 applicable services; eks-saas-gitops N/A)

**Common Patterns:**
- API Versioning absence: all 4 application services score 1 on APP-Q5
- Service discovery via environment variables: all 4 services score 2 on APP-Q6

**Critical Gaps:**
1. API Versioning (APP-Q5): Universal gap — no service has versioning. Critical for AI agent integration.
2. Monolith architecture (APP-Q2): 2 services (unishop=2, local-monolith=1) are monoliths requiring decomposition
3. Synchronous communication (APP-Q3): 2 monolith services have all-sync communication patterns

#### Data Platform

**Portfolio Score: 2.75 / 4.0**

**Common Patterns:**
- No stored procedures: 4 of 4 applicable services score 4 on DATA-Q4 — all business logic in application layer
- DynamoDB adoption: 3 services use DynamoDB (managed, serverless)

**Critical Gaps:**
1. Unstructured data (DATA-Q1): 3 services have no S3/object storage for documents and images
2. Self-managed MySQL (unishop): Only unmanaged database in the portfolio — migration to Aurora required

#### Security Baseline

**Portfolio Score: 1.88 / 4.0**

**Common Patterns:**
- Encryption at rest: 4 of 5 services score ≥ 3 (AWS-managed encryption)
- Security pipeline gap: 3 of 5 services have no security scanning

**Critical Gaps:**
1. API Authentication (SEC-Q3): 3 services have no authentication — critical for e-commerce
2. Centralized Identity (SEC-Q4): 3 services have no external IdP
3. Audit Logging (SEC-Q1): 3 services have no CloudTrail
4. Hardcoded secrets (SEC-Q5): unishop has passwords in source code

#### Operations & Observability

**Portfolio Score: 1.31 / 4.0** — Lowest category across the portfolio

**Common Patterns:**
- Universal observability gap: No service has complete observability
- No incident response: All 5 services score 1 on OPS-Q7 and OPS-Q8

**Critical Gaps:**
1. Every OPS question is a Foundational Blocker except OPS-Q9 (which is still a blocker at 2 services <2)
2. Only books-api has any tracing (OPS-Q1=3) — all others have none
3. Only books-api has any deployment strategy (OPS-Q5=4) — all others are manual
4. Operations is the weakest category and must be prioritized in Phase 0
## Portfolio Modernization Roadmap

> Dependency-aware phased roadmap with fixed phase names. Services are ordered by dependency graph position, then by priority (P0 → P1 → P2), then by score.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services (eks-saas-gitops) before downstream dependents (unishop, local-monolith)
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Independent services (aws-microservices, books-api) can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, address portfolio-wide blockers, and build the foundation for all subsequent phases.

**Cross-Cutting Activities:**
- **CI/CD Pipelines**: Establish CI/CD for unishop-monolith, aws-microservices, and local-monolith (INF-Q11 blocker)
- **Centralized Observability**: Deploy ADOT collectors, enable X-Ray tracing, create CloudWatch dashboards (OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4 blockers)
- **CloudTrail Audit Logging**: Enable organization-wide CloudTrail with immutable S3 storage (SEC-Q1 blocker)
- **Cognito Identity Provider**: Deploy centralized Cognito User Pool for portfolio-wide authentication (SEC-Q3, SEC-Q4 blockers)
- **Backup and Recovery**: Enable DynamoDB PITR, set RemovalPolicy to RETAIN, create AWS Backup plans (INF-Q8 blocker)
- **API Versioning Standard**: Define /v1/ URL-path versioning standard; generate OpenAPI specs (APP-Q5 blocker)
- **Resource Tagging Standard**: Define and enforce portfolio tagging policy (OPS-Q9)
- **Incident Response Framework**: Create shared runbook repository and on-call procedures (OPS-Q7, OPS-Q8 blockers)

**Organizational Enablers:**
- Training: EKS administration, Terraform modules, GitOps (ArgoCD/Flux), Amazon Bedrock agent development
- Tooling: Standardize on Terraform for IaC, GitHub Actions for CI/CD, GitOps for deployment
- Standards: API versioning policy, tagging standard, security scanning requirements, observability ownership charter

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize foundation services and establish patterns for the rest of the portfolio.

**Services in Scope:**

1. **eks-saas-gitops** (P1, Score: 2.19 / 4.0) — Foundation service, Fan-In=2
   - Current State: EKS platform with Terraform IaC, Flux CD GitOps, Argo Workflows. Security gaps (unauthenticated Argo Workflows/Kubecost, Gitea SPOF). No tracing, no alerting.
   - Target State: Hardened EKS platform with authenticated services, progressive delivery (Flagger), ADOT tracing, CloudWatch alerting.
   - Key Activities:
     - Harden Argo Workflows auth (switch to `--auth-mode=sso` with Cognito OIDC)
     - Move Kubecost behind internal ALB or add authentication
     - Add VPC endpoints for ECR, SQS, S3, SSM
     - Deploy Flagger for canary deployments
     - Deploy ADOT DaemonSet for distributed tracing
     - Add integration tests to Gitea Actions pipelines
     - Add security scanning (checkov, trivy) to CI pipelines
   - Dependencies: None (foundation service)
   - Blocks: unishop-monolith (Phase 2), local-monolith (Phase 3)
   - Estimated Effort: Medium

2. **books-api** (P1, Score: 2.65 / 4.0) — Highest-scoring service, isolated
   - Current State: Serverless API with full CI/CD pipeline, X-Ray tracing, Cognito auth, canary deployments. Missing API versioning, backup, security scanning.
   - Target State: Fully modernized serverless API with versioned APIs, PITR backup, security scanning, EventBridge integration.
   - Key Activities:
     - Add API versioning (/v1/books)
     - Enable DynamoDB PITR (replace SimpleTable with DynamoDB Table)
     - Add security scanning to CodePipeline (npm audit, Dependabot)
     - Add EventBridge event emission on book creation (BookCreated events)
     - Generate OpenAPI specification for Bedrock agent tool discovery
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Low

**Expected Outcomes:**
- EKS platform hardened and ready for workload onboarding
- books-api serves as reference implementation for serverless patterns
- Canary deployment, tracing, and security scanning patterns established

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize services that depend on Phase 1 services. Replicate proven patterns.

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.67 / 4.0) — Lowest-scoring, depends on eks-saas-gitops
   - Current State: Java 8 Spring Boot monolith on EC2 with self-managed MySQL. No CI/CD, no tracing, hardcoded credentials, no authentication. All APIs unauthenticated and unversioned.
   - Target State: Containerized on EKS with Aurora MySQL, CI/CD pipeline, API Gateway entry point, initial Strangler Fig decomposition.
   - Key Activities:
     - Containerize on EKS with Fargate profile (Dockerfile using amazoncorretto:17)
     - Migrate self-managed MySQL to Aurora MySQL (leverage existing DMS config)
     - Establish CI/CD pipeline (GitHub Actions → ECR → ArgoCD on EKS)
     - Add Cognito authentication to API endpoints
     - Add API versioning (/v1/)
     - Move secrets to AWS Secrets Manager
     - Begin Strangler Fig decomposition — extract Basket/Order service first (enables AI agent access)
   - Dependencies: eks-saas-gitops (Phase 1)
   - Blocks: None
   - Estimated Effort: High

2. **aws-microservices** (P0, Score: 2.24 / 4.0) — Independent serverless service
   - Current State: Event-driven serverless microservices (Lambda, DynamoDB, EventBridge). No CI/CD, no tracing, no authentication, no API versioning, no backup.
   - Target State: Fully automated CI/CD, X-Ray tracing, Cognito auth, versioned APIs, DynamoDB PITR.
   - Key Activities:
     - Create CI/CD pipeline (GitHub Actions or CDK Pipelines)
     - Enable X-Ray tracing on all Lambda functions
     - Add Cognito authorizers to API Gateway endpoints
     - Enable DynamoDB PITR on all tables; change RemovalPolicy to RETAIN
     - Add API versioning (/v1/)
     - Add DLQ to SQS OrderQueue
     - Upgrade Lambda runtime from NODEJS_14_X to NODEJS_20_X
     - Add security scanning (npm audit, Dependabot)
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Medium

**Parallel Tracks:**
- unishop-monolith containerization and aws-microservices CI/CD can proceed in parallel (no dependencies between them)

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize leaf services, implement advanced capabilities, continuous improvement.

**Services in Scope:**

1. **local-monolith** (P0, Score: 1.88 / 4.0) — Depends on eks-saas-gitops, decomposition target
   - Current State: PHP 8.2 monolith on App Runner with RDS MySQL. No CI/CD, no tracing, no API versioning. Tightly-coupled single-file architecture (~2500+ lines).
   - Target State: Containerized on EKS, CI/CD with GitOps, Strangler Fig decomposition extracting Inventory and Returns services for AI agent integration.
   - Key Activities:
     - Establish CI/CD pipeline (GitHub Actions → ECR → ArgoCD on EKS)
     - Migrate IaC from CloudFormation to Terraform (preferred)
     - Migrate from App Runner to EKS for multi-service orchestration
     - Begin Strangler Fig decomposition:
       1. Extract Inventory Service (P0 — enables AI restocking agent)
       2. Extract Returns Service (P0 — enables AI return processing agent)
       3. Extract Fulfillment Service with Step Functions orchestration
     - Add EventBridge events for domain operations
     - Add OpenTelemetry PHP SDK instrumentation
   - Dependencies: eks-saas-gitops (Phase 1)
   - Blocks: None
   - Estimated Effort: High

2. **AI Agent Integration** (Portfolio-wide)
   - Implement Amazon Bedrock-powered customer support agent:
     - Order inquiry tool → aws-microservices Order API
     - Product lookup tool → books-api GET /v1/books
     - Return processing tool → local-monolith Returns Service API
     - Inventory restocking tool → local-monolith Inventory Service API
   - Deploy Amazon Bedrock AgentCore for production agent runtime
   - Create Bedrock Knowledge Bases for RAG-based product and documentation search
   - Add EventBridge integration for agent-triggered events

**Expected Timeline**: 6+ months with continuous improvement

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6–9 months (with 2–3 parallel tracks)
- Phase 0: Month 0–1 (cross-cutting foundation)
- Phase 1: Month 1–2 (2 parallel tracks: eks-saas-gitops + books-api)
- Phase 2: Month 2–4 (2 parallel tracks: unishop-monolith + aws-microservices)
- Phase 3: Month 4–6+ (local-monolith decomposition + AI agent integration)
## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach. A customer portfolio may be divided into multiple pathways depending on workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 2 | 40% | Medium | High |
| Move to Containers | 1 | 20% | Low | Medium |
| Move to Open Source | 0 | 0% | — | — |
| Move to Managed Databases | 1 | 20% | Low | Medium |
| Move to Managed Analytics | 0 | 0% | — | — |
| Move to Modern DevOps | 4 | 80% | High | Medium |
| Move to AI | 4 | 80% | High | Medium |

### Portfolio Pathway Aggregation

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | unishop-monolith, local-monolith | aws-microservices, books-api | eks-saas-gitops |
| Move to Containers | unishop-monolith | aws-microservices, local-monolith, books-api | eks-saas-gitops |
| Move to Open Source | — | unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops | — |
| Move to Managed Databases | unishop-monolith | aws-microservices, local-monolith, books-api, eks-saas-gitops | — |
| Move to Managed Analytics | — | unishop-monolith, aws-microservices, local-monolith, books-api | eks-saas-gitops |
| Move to Modern DevOps | unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops | books-api | — |
| Move to AI | unishop-monolith, aws-microservices, local-monolith, books-api | — | eks-saas-gitops |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| unishop-monolith | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| aws-microservices | — | — | — | — | — | ✅ | ✅ |
| local-monolith | ✅ | — | — | — | — | ✅ | ✅ |
| books-api | — | — | — | — | — | — | ✅ |
| eks-saas-gitops | N/A | N/A | — | — | N/A | ✅ | N/A |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is a prerequisite for Move to AI for unishop-monolith (data foundations needed for agent access)

**Parallel Execution Tracks:**
- **Track 1 (DevOps + Containers)**: Move to Modern DevOps + Move to Containers — establish CI/CD and containerize monoliths
- **Track 2 (Data + Security)**: Move to Managed Databases + security hardening — Aurora migration and authentication
- **Track 3 (Architecture + AI)**: Move to Cloud Native + Move to AI — decompose monoliths and integrate Bedrock agents

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, eks-saas-gitops (4 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q11 (CI/CD) score < 3: affects 4 services
  - OPS-Q5 (Deployment Strategy) score < 3: affects 4 services
  - OPS-Q6 (Integration Testing) score < 3: affects 4 services
- **Representative AWS Services**: CodePipeline, CodeBuild, ECR, GitHub Actions, ArgoCD (GitOps — preferred), Flagger, Terraform (preferred)
- **Key Activities**:
  1. Establish CI/CD pipelines for all 4 affected services
  2. Implement canary deployment strategies (Lambda alias shifting, Flagger on EKS)
  3. Add automated testing (unit, integration, contract tests)
  4. Standardize IaC on Terraform (preferred)
  5. Adopt GitOps workflows (preferred) for all deployments
- **Cross-Service Synergies**: Shared CI/CD templates, shared security scanning configuration, unified deployment strategy patterns
- **Estimated Effort**: Medium across 4 services
- **Roadmap Phase Alignment**: Phase 0 (foundation) and Phase 1 (implementation)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to Cloud Native

- **Services Affected**: unishop-monolith, local-monolith (2 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - APP-Q2 (Monolith) score < 3: affects 2 services
  - APP-Q3 (Async Communication) score < 3: affects 2 services
  - INF-Q1 (Managed Compute) score < 3: affects 1 service (unishop)
- **Representative AWS Services**: EKS (preferred), API Gateway (preferred), EventBridge (preferred), Aurora MySQL (preferred), Step Functions
- **Key Activities**:
  1. Containerize monoliths on EKS (preferred)
  2. Apply Strangler Fig decomposition pattern
  3. Introduce EventBridge (preferred) for event-driven communication
  4. Use API Gateway (preferred) for service routing during decomposition
- **Cross-Service Synergies**: Shared EKS cluster (eks-saas-gitops), shared EventBridge bus, common decomposition patterns
- **Estimated Effort**: High across 2 services
- **Roadmap Phase Alignment**: Phase 2 (unishop) and Phase 3 (local-monolith)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Containers

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q1 (Managed Compute) score = 1: all compute on raw EC2
- **Representative AWS Services**: EKS (preferred), ECR, EKS with Fargate (avoid self-managed Kubernetes)
- **Key Activities**:
  1. Create Dockerfile for Spring Boot monolith (amazoncorretto:17 base image)
  2. Push to ECR, deploy on EKS with Fargate profile
  3. Set up GitOps with ArgoCD for automated deployments
- **Cross-Service Synergies**: Leverage eks-saas-gitops platform; reuse Helm chart patterns
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2
- **Relevant Learning Materials**: Module 3 — Move to Containers

#### Move to Managed Databases

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q2 (Managed Databases) score = 2: self-managed MySQL on EC2
  - DATA-Q3 (Engine Version) score = 2: Aurora MySQL 5.7 past EOL
- **Representative AWS Services**: Aurora MySQL (preferred), DMS (already partially configured), Secrets Manager
- **Key Activities**:
  1. Execute DMS migration from self-managed MySQL to Aurora MySQL 3.x
  2. Upgrade Aurora from MySQL 5.7 to MySQL 8.0 compatible
  3. Enable Multi-AZ, automated backups, PITR
  4. Migrate credentials to Secrets Manager with rotation
- **Cross-Service Synergies**: Aurora MySQL patterns can guide future database migrations if local-monolith needs database-per-service
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to AI

- **Services Affected**: unishop-monolith, aws-microservices, local-monolith, books-api (4 total)
- **Portfolio Priority**: High
- **Aggregation**: Move to AI: Triggered in 4 of 5 services (1 service [eks-saas-gitops] is N/A — infrastructure-only repo, pathway correctly not applicable)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): —
  - Already present (AI frameworks detected): —
  - Not Applicable (infrastructure-only): eks-saas-gitops
- **Common Trigger Criteria**:
  - No AI/agent frameworks detected in any of the 4 application services
  - Portfolio context explicitly mentions AI agent intent
- **Representative AWS Services**: Amazon Bedrock (preferred), Bedrock AgentCore, Bedrock Knowledge Bases, DynamoDB (preferred for agent session state), EventBridge (preferred for agent events), API Gateway (preferred for agent tool APIs)
- **Key Activities**:
  1. Generate OpenAPI specifications for all service APIs (foundation for agent tool discovery)
  2. Implement Amazon Bedrock Agents with API tools for order inquiry, product lookup, return processing, inventory restocking
  3. Deploy Bedrock Knowledge Bases for RAG-based product and documentation search
  4. Add EventBridge integration for agent-triggered events
  5. Implement agent guardrails and evaluation framework
- **Cross-Service Synergies**: Shared Bedrock agent with tools spanning multiple services; shared EventBridge bus for agent events; unified Cognito authentication for agent API access
- **Estimated Effort**: Medium across 4 services
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 7 — Move to AI
## Integration Opportunities

### Shared Service Extraction

**Opportunity: Centralized Authentication (Amazon Cognito)**
- **Current State**: Duplicated or missing across all 5 services — unishop has broken OAuth2 (permitAll), aws-microservices has none, local-monolith has PHP sessions, books-api has Cognito (only one), eks-saas-gitops has basic auth on Gitea
- **Proposed Solution**: Deploy a single Amazon Cognito User Pool as the portfolio-wide identity provider. Configure Cognito authorizers on API Gateway (preferred) for all services. Use OIDC for EKS service authentication. Use machine-to-machine OAuth2 for Bedrock agent API access.
- **Benefits**: Unified identity, SSO capability, MFA enforcement, secure AI agent authentication
- **Effort**: Medium
- **Priority**: High

**Opportunity: Centralized Observability Platform**
- **Current State**: Only books-api has X-Ray tracing. No shared dashboards, no centralized alerting, no cross-service trace correlation.
- **Proposed Solution**: Deploy ADOT (AWS Distro for OpenTelemetry) as portfolio-wide tracing collector. Centralize on CloudWatch + X-Ray for metrics, logs, and traces. Create portfolio-level CloudWatch dashboards.
- **Benefits**: End-to-end request tracing, cross-service debugging, AI agent action visibility, unified alerting
- **Effort**: Medium
- **Priority**: High

### Event-Driven Architecture

**Opportunity: Portfolio Event Bus**
- **Current State**: aws-microservices uses EventBridge for checkout flow. All other services have no event publishing. Cross-service integration requires direct API calls.
- **Proposed Solution**: Deploy a shared Amazon EventBridge (preferred) custom event bus. All services publish domain events (OrderCreated, BasketUpdated, BookCreated, InventoryChanged, ReturnRequested). EventBridge rules route events to interested consumers and AI agent triggers.
- **Benefits**: Decoupled services, event-driven AI agent triggers, audit trail of all domain events, easier decomposition
- **Effort**: Medium

**Opportunity: AI Agent Event Integration**
- **Current State**: No event-driven integration exists for agent actions
- **Proposed Solution**: Use EventBridge (preferred) to connect agent actions with services — agent triggers restocking via InventoryRestockRequested event, agent approves returns via ReturnApproved event
- **Benefits**: Asynchronous agent actions, audit trail, retry capability
- **Effort**: Low

### API Gateway Consolidation

- **Current State**: unishop has no gateway (Nginx on EC2), aws-microservices has 3 separate API Gateways, local-monolith uses App Runner, books-api has 1 API Gateway, eks-saas-gitops uses ALBs
- **Proposed Solution**: Deploy Amazon API Gateway (preferred) as the unified entry point for all external API traffic. Route to Lambda functions, EKS services, and App Runner via VPC Link. Single point for authentication, throttling, versioning, and monitoring.
- **Benefits**: Consistent auth, rate limiting, monitoring, cost reduction, single API catalog for AI agent tool discovery

### Observability Unification

- **Current State**: books-api has X-Ray tracing. eks-saas-gitops has Kubecost/Prometheus. All others have minimal or no observability.
- **Proposed Solution**: Standardize on CloudWatch + X-Ray + ADOT. Deploy ADOT collectors on EKS (DaemonSet) and enable Lambda tracing. Create unified CloudWatch dashboards per service and a portfolio-level dashboard.
- **Benefits**: End-to-end tracing across services, consistent metrics, AI agent action observability
## Risk Analysis

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| Self-managed MySQL data loss (unishop — no backups, no PITR) | High | High | 🔴 Critical | Migrate to Aurora MySQL with automated backups and PITR; immediate DMS migration | Phase 2 |
| Unauthenticated APIs exposing user data (3 services) | High | High | 🔴 Critical | Deploy Cognito authorizers on all API Gateway endpoints | Phase 0 |
| Hardcoded credentials in source control (unishop) | High | High | 🔴 Critical | Migrate to Secrets Manager immediately; rotate all exposed credentials | Phase 0 |
| Gitea SPOF — single EC2 instance as GitOps source of truth | Medium | High | 🟠 High | Migrate Gitea to EKS with replicas, or replace with managed Git service | Phase 1 |
| Single NAT Gateway (eks-saas-gitops) — AZ failure disrupts all egress | Medium | High | 🟠 High | Enable multi-AZ NAT Gateways (single_nat_gateway=false) | Phase 1 |
| No CI/CD in 3 services — manual deployments create deployment risk | High | Medium | 🟠 High | Establish CI/CD pipelines for all services | Phase 0 |
| DynamoDB tables with RemovalPolicy.DESTROY (aws-microservices) | Medium | High | 🟠 High | Change to RETAIN and enable PITR on all DynamoDB tables | Phase 0 |
| Internet-facing Argo Workflows with no auth (eks-saas-gitops) | High | Medium | 🟠 High | Switch to --auth-mode=sso with Cognito OIDC | Phase 1 |
| No distributed tracing in 4 of 5 services | High | Medium | 🟠 High | Deploy ADOT and X-Ray across the portfolio | Phase 0 |
| Lambda NODEJS_14_X EOL runtime (aws-microservices) | Medium | Medium | 🟡 Medium | Upgrade to NODEJS_20_X or NODEJS_22_X | Phase 2 |
| Java 8 / Spring Boot 2.1.x EOL (unishop) | Medium | Medium | 🟡 Medium | Upgrade to Java 17+ / Spring Boot 3.x during containerization | Phase 2 |
| Aurora MySQL 5.7 past EOL (unishop migration target) | Medium | Medium | 🟡 Medium | Upgrade to Aurora MySQL 3.x (MySQL 8.0 compatible) | Phase 2 |

### High-Risk Dependencies

- **unishop-monolith** (score 1.67, Fan-In: 0) — Lowest-scoring service with self-managed MySQL, hardcoded credentials, and no CI/CD. While it has zero fan-in, it is the primary decomposition target for AI agent integration.

### Single Points of Failure

- **eks-saas-gitops: Gitea single EC2 instance** — Blast radius: 40% of portfolio (all services using GitOps depend on Gitea as source of truth). No redundancy, no backup for Git repositories. Mitigation: Migrate to EKS with replicas or managed Git service.
- **eks-saas-gitops: Single NAT Gateway** — All private subnet egress traffic routes through one NAT Gateway. AZ failure affects all EKS workloads.

### Circular Dependency Risks

✅ No circular dependencies detected.

### Data Availability Risks

- **unishop-monolith: Self-managed MySQL on EC2** — No automated backups, no PITR, no Multi-AZ. Credential hardcoded. This is the highest data availability risk in the portfolio. Mitigation: Immediate DMS migration to Aurora MySQL.
- **aws-microservices: DynamoDB with RemovalPolicy.DESTROY** — A `cdk destroy` permanently destroys all product, basket, and order data. Mitigation: Change RemovalPolicy to RETAIN, enable PITR.

### Observability Blind Spots

- **4 of 5 services have no distributed tracing** — Only books-api has X-Ray. Cross-service issues between the customer support agent and backend APIs will be impossible to debug without tracing.
- **All services lack business metrics** — Cannot correlate infrastructure issues with business impact.
## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized Platform Team + Service Teams (cross-cutting concerns count = 20, well above threshold of 5)

**Platform Team** (3–4 engineers):
- Responsibilities: Shared infrastructure (EKS, Cognito, EventBridge, observability), platform capabilities (CI/CD templates, security scanning), standards enforcement, Terraform module library
- Skills Required: Terraform, EKS administration, GitOps (ArgoCD/Flux), CloudWatch/X-Ray, Cognito, EventBridge

**Service Teams** (2–3 engineers per service):
- Responsibilities: Service-specific modernization, feature development, service-level SLOs, application testing
- Skills Required: Service-specific languages (Java, TypeScript, PHP), DynamoDB, Aurora, API development

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| Terraform | IaC standardization (all services) | Partial (eks-saas-gitops only) | High |
| EKS / Kubernetes | Container orchestration (unishop, local-monolith) | Partial (eks-saas-gitops) | High |
| GitOps (ArgoCD/Flux) | Deployment automation | Partial (eks-saas-gitops has Flux) | High |
| Amazon Bedrock | AI agent development | No | High |
| ADOT / X-Ray / OpenTelemetry | Observability (all services) | Partial (books-api has X-Ray) | High |
| CI/CD (GitHub Actions/CodePipeline) | Pipeline automation | Partial (books-api has CodePipeline) | Medium |
| Amazon Cognito | Authentication (all services) | Partial (books-api has Cognito) | Medium |
| DMS / Aurora MySQL | Database migration (unishop) | No | Medium |
| Strangler Fig patterns | Monolith decomposition | No | Medium |
| EventBridge | Event-driven architecture | Partial (aws-microservices) | Medium |

### Training Recommendations

**Phase 0–1 Priority (Immediate):**
1. EKS Workshop (eksworkshop.com) — Platform team, unishop and local-monolith teams
2. Terraform fundamentals — All teams (portfolio-wide IaC standardization)
3. Move to Modern DevOps (SkillBuilder) — All teams with CI/CD gaps
4. Getting Started with DevOps on AWS — All teams

**Phase 2–3 Priority:**
5. Amazon Bedrock Getting Started — AI integration team
6. Introduction to Agentic AI on AWS — AI integration team
7. Move to Managed Databases (SkillBuilder) — unishop team (Aurora migration)
8. Cloud Design Patterns (AWS Prescriptive Guidance) — All teams (decomposition patterns)

### External Support

- **AWS Professional Services or Consulting Partner** recommended for:
  - Database migration: Self-managed MySQL to Aurora MySQL (high-risk, requires DMS expertise)
  - Architecture redesign: Strangler Fig decomposition of both monoliths (requires domain-driven design expertise)
  - EKS platform hardening: Security and HA improvements to eks-saas-gitops
- **MAP (Migration Acceleration Program)** funding can offset Professional Services costs (see AWS Programs section)
## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.** Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | 4 services with overall score < 2.5 indicate significant modernization investment needed | unishop=1.67, aws-microservices=2.24, local-monolith=1.88, eks-saas-gitops=2.19 (4 of 5 < 2.5) | Request MAP engagement via AWS Solutions Architect to assess eligibility for migration credits |
| Experience-Based Acceleration | EBA | 4 services have triggered pathways AND overall score < 3.0, indicating need for guided modernization | unishop (5 pathways, 1.67), aws-microservices (2 pathways, 2.24), local-monolith (3 pathways, 1.88), eks-saas-gitops (1 pathway, 2.19) | Request EBA engagement focusing on Move to Modern DevOps and Move to AI pathways (highest coverage) |

### Program Details

**Migration Acceleration Program (MAP)**
This program was recommended because 4 of 5 services score below 2.5, indicating a large-scale modernization effort ahead. MAP provides migration credits, AWS Professional Services engagement, and partner funding to accelerate the modernization journey. Given the portfolio involves database migration (self-managed MySQL → Aurora), containerization (EC2 → EKS), and decomposition (2 monoliths → microservices), MAP credits can significantly offset the investment. Timing: Engage during Phase 0–1 to maximize benefit during the heaviest investment phases.

**Experience-Based Acceleration (EBA)**
This program was recommended because 4 services have at least one triggered pathway with an overall score below 3.0. EBA provides prescriptive, outcome-driven engagements led by AWS specialists for specific modernization pathways. The recommended EBA focus areas are: (1) Move to Modern DevOps — 80% of services triggered, and (2) Move to AI — 80% of services triggered. These two pathways have the broadest portfolio impact and would benefit most from guided acceleration. Timing: Engage during Phase 1–2 for maximum pathway execution support.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect or Partner to determine eligibility and timing.
## Recommended Self-Paced Learning Materials

> Curated based on the 5 triggered pathways and portfolio-wide skill gaps.

### Module 2: Move to Cloud Native (Containers and Serverless)

- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

### Module 3: Move to Containers with Amazon ECS and EKS

- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

### Module 4: Move to Managed Databases

- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

### Module 6: Move to Modern DevOps

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

### Module 7: Move to AI

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Build and Evaluate RAG Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across multiple repos. They are distinct from cross-cutting analysis (which aggregates individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 2
- **Finding**: The portfolio uses 4 distinct IaC tools: CloudFormation (unishop-monolith, local-monolith), CDK (aws-microservices, books-api pipeline), SAM (books-api), and Terraform (eks-saas-gitops). No single tool covers the majority of services. The preferred tool (Terraform) is used by only 1 of 5 services (20%).
- **Evidence**: unishop-monolith: `MonoToMicroCF.yaml` (CloudFormation); aws-microservices: `lib/*.ts` (CDK); local-monolith: `infrastructure/monolith-apprunner.yaml` (CloudFormation); books-api: `template.yml` (SAM) + `pipeline/lib/pipeline-stack.ts` (CDK); eks-saas-gitops: `terraform/` (Terraform)
- **Recommendation**: Standardize on Terraform (preferred) across the portfolio. Create a shared Terraform module library managed by the platform team. Migrate CloudFormation and CDK stacks to Terraform as services enter their modernization phases. Use Terraform Cloud or TF Controller (already deployed on eks-saas-gitops) for centralized state management.

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: No centralized observability stack exists. Each service operates independently: books-api has X-Ray tracing (OPS-Q1=3); eks-saas-gitops has Kubecost/Prometheus for cost metrics (OPS-Q3=2); unishop-monolith has only a CloudWatch log group; aws-microservices and local-monolith have no observability infrastructure. No cross-service trace correlation, no shared dashboards, no centralized alerting.
- **Evidence**: books-api: `template.yml` (Tracing: Active, aws-xray-sdk-core); eks-saas-gitops: `05-kubecost.yaml` (Kubecost with Prometheus); unishop-monolith: `MonoToMicroCF.yaml` (InstanceLogGroup only); aws-microservices: no tracing config; local-monolith: no tracing config
- **Recommendation**: Deploy a centralized observability platform: ADOT (AWS Distro for OpenTelemetry) as the standard collector, X-Ray as the tracing backend, CloudWatch as the metrics and logs platform. Create a portfolio-level CloudWatch dashboard showing health of all services. This is critical for the AI agent use case — agent actions must be traceable across services.
- **Contextual Annotations**: This finding provides context for all OPS-Q1 cross-cutting blocker findings. While individual services score 1 on tracing, a portfolio-level observability deployment would address all 4 affected services simultaneously.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 4
- **Finding**: No circular dependencies detected in the inferred dependency graph. The dependency structure is a simple tree: eks-saas-gitops is a foundation service with unishop-monolith and local-monolith as leaves. aws-microservices and books-api are isolated. No strongly connected components with size > 1 were found.
- **Evidence**: Inferred dependency graph from MOD reports shows only 2 directed edges (unishop → eks-saas-gitops, local-monolith → eks-saas-gitops) with no cycles.
- **Recommendation**: No action needed. Maintain the current acyclic dependency structure. As services are decomposed and new dependencies emerge (e.g., between extracted microservices), monitor for circular dependencies using architecture fitness functions.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 2
- **Finding**: High technology diversity across the portfolio: 4 programming languages (Java, TypeScript/JavaScript, PHP, HCL), 4 IaC tools (CloudFormation, CDK, SAM, Terraform), 4 compute patterns (EC2, Lambda, App Runner, EKS), 5 database engines (MySQL self-managed, DynamoDB, RDS MySQL, Aurora MySQL target, SQLite), 3+ CI/CD approaches (GitHub Actions, CodePipeline, Gitea Actions, manual). Technology diversity score: 14 distinct technologies / 5 services = 2.8 (high).
- **Evidence**: Cross-referenced from Technology Stack Summary section — each service uses a different primary language, IaC tool, and compute pattern.
- **Recommendation**: Consolidate where possible: Terraform for IaC (preferred), GitHub Actions or CodePipeline for CI/CD, EKS for containerized workloads (preferred), DynamoDB (preferred) for new services. Accept controlled diversity for justified cases (Lambda for event-driven workloads, PHP during monolith transition period). Set a target diversity score of < 2.0 within 12 months.

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: No centralized security posture exists. Each service manages security independently: books-api has Cognito auth; local-monolith has WAF + VPC Flow Logs; eks-saas-gitops has ECR scan-on-push; unishop-monolith has cfn-nag only; aws-microservices has no security tooling. No shared WAF Web ACL, no centralized security scanning pipeline, no unified vulnerability management, no shared Secrets Manager configuration.
- **Evidence**: books-api: `template.yml` (CognitoUserPool); local-monolith: `monolith-apprunner.yaml` (WebACL, VPCFlowLog); eks-saas-gitops: `apps_needs.tf` (ECR scan_on_push); unishop-monolith: `.github/workflows/cfn-security.yml` (cfn-nag only); aws-microservices: no security tooling
- **Recommendation**: Implement portfolio-wide security posture: (1) Centralized Cognito User Pool (already recommended in SEC-Q3/Q4), (2) Shared WAF Web ACL applied to all API Gateways and ALBs, (3) Centralized security scanning in all CI/CD pipelines (SAST, dependency scanning, container scanning), (4) AWS Security Hub for unified findings aggregation across accounts, (5) GuardDuty for threat detection. This is a Phase 0 priority.
## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| unishop-monolith | application | P0 | 1.67 | 1.45 | 2.00 | 2.50 | 1.29 | 1.11 | 5 of 7 | 2 |
| local-monolith | application | P0 | 1.88 | 2.55 | 1.33 | 2.25 | 2.14 | 1.11 | 3 of 7 | 3 |
| eks-saas-gitops | infrastructure-only | P1 | 2.19 | 2.82 | N/A | 3.00 | 1.71 | 1.22 | 1 of 7 | 1 |
| aws-microservices | application | P0 | 2.24 | 2.55 | 2.67 | 3.25 | 1.71 | 1.00 | 2 of 7 | 2 |
| books-api | application | P1 | 2.65 | 3.00 | 2.83 | 2.75 | 2.57 | 2.11 | 1 of 7 | 1 |

### Individual Service Details

#### unishop-monolith

- **Overall Score**: 1.67 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Analysis Date**: 2025-07-17
- **Category Scores**:
  - Infrastructure & DevOps: 1.45
  - Application Architecture: 2.00
  - Data Platform: 2.50
  - Security Baseline: 1.29
  - Operations & Observability: 1.11
- **Top Gaps**:
  - INF-Q1: score 1 — All compute on raw EC2, no managed orchestration
  - SEC-Q5: score 1 — Database credentials hardcoded in application.properties and CloudFormation
  - INF-Q11: score 1 — No CI/CD pipeline, only cfn-nag scan
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Containerize on EKS and migrate MySQL to Aurora MySQL
  - Establish CI/CD pipeline and move secrets to Secrets Manager
  - Begin Strangler Fig decomposition starting with Basket/Order service
- **Depends On**: eks-saas-gitops (shared_infra)
- **Depended On By**: None
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 2 — Foundation

#### local-monolith

- **Overall Score**: 1.88 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Analysis Date**: 2026-04-27
- **Category Scores**:
  - Infrastructure & DevOps: 2.55
  - Application Architecture: 1.33
  - Data Platform: 2.25
  - Security Baseline: 2.14
  - Operations & Observability: 1.11
- **Top Gaps**:
  - APP-Q2: score 1 — Tightly-coupled monolith, all logic in single index.php file
  - INF-Q11: score 1 — No CI/CD pipeline, manual deployments only
  - APP-Q3: score 1 — All communication synchronous, no async patterns
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Establish CI/CD pipeline and migrate IaC to Terraform
  - Extract Inventory and Returns services for AI agent integration
  - Migrate from App Runner to EKS for multi-service orchestration
- **Depends On**: eks-saas-gitops (shared_infra)
- **Depended On By**: None
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 3 — Advanced

#### eks-saas-gitops

- **Overall Score**: 2.19 / 4.0
- **Repository Type**: infrastructure-only
- **Priority**: P1
- **Analysis Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 2.82
  - Application Architecture: N/A
  - Data Platform: 3.00
  - Security Baseline: 1.71
  - Operations & Observability: 1.22
- **Top Gaps**:
  - SEC-Q1: score 1 — No CloudTrail configuration in IaC
  - SEC-Q3: score 1 — Argo Workflows and Kubecost exposed with no authentication
  - OPS-Q1: score 1 — No distributed tracing instrumentation
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**:
  - Harden Argo Workflows auth and secure internet-facing services
  - Add VPC endpoints, deploy ADOT for tracing, add CloudWatch alerting
  - Deploy Flagger for progressive delivery
- **Depends On**: None
- **Depended On By**: unishop-monolith, local-monolith
- **Blast Radius**: 40%
- **Roadmap Phase**: Phase 1 — Quick Wins

#### aws-microservices

- **Overall Score**: 2.24 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Analysis Date**: 2026-04-27
- **Category Scores**:
  - Infrastructure & DevOps: 2.55
  - Application Architecture: 2.67
  - Data Platform: 3.25
  - Security Baseline: 1.71
  - Operations & Observability: 1.00
- **Top Gaps**:
  - INF-Q11: score 1 — No CI/CD pipeline, manual `cdk deploy`
  - OPS-Q5: score 1 — No deployment strategy, direct-to-production
  - SEC-Q3: score 1 — No authentication on any API Gateway endpoint
- **Triggered Pathways**: Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Create CI/CD pipeline with canary deployment via Lambda alias shifting
  - Add Cognito auth to all API Gateways, enable X-Ray tracing
  - Enable DynamoDB PITR and upgrade Lambda runtime
- **Depends On**: None
- **Depended On By**: None
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 2 — Foundation

#### books-api

- **Overall Score**: 2.65 / 4.0
- **Repository Type**: application
- **Priority**: P1
- **Analysis Date**: 2026-04-27
- **Category Scores**:
  - Infrastructure & DevOps: 3.00
  - Application Architecture: 2.83
  - Data Platform: 2.75
  - Security Baseline: 2.57
  - Operations & Observability: 2.11
- **Top Gaps**:
  - SEC-Q7: score 1 — No security scanning in CI/CD pipeline
  - INF-Q5: score 1 — No VPC configuration, Lambda runs in default networking
  - INF-Q8: score 1 — No DynamoDB PITR or backup plan
- **Triggered Pathways**: Move to AI
- **Key Recommendations**:
  - Add security scanning to CodePipeline (npm audit, Dependabot)
  - Enable DynamoDB PITR and add API versioning
  - Generate OpenAPI spec for Bedrock agent tool discovery
- **Depends On**: None
- **Depended On By**: None
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 1 — Quick Wins
## Analysis Inventory

| # | Service | Report File | Analysis Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/MonoToMicroLegacy-mod-report.md | 2025-07-17 | application | 1.67 |
| 2 | aws-microservices | ./services/aws-microservices/aws-microservices-mod-report.md | 2026-04-27 | application | 2.24 |
| 3 | local-monolith | ./monolith/monolith-mod-report.md | 2026-04-27 | application | 1.88 |
| 4 | books-api | ./services/books-api/books-api-mod-report.md | 2026-04-27 | application | 2.65 |
| 5 | eks-saas-gitops | ./services/eks-saas-gitops/eks-saas-gitops-mod-report.md | 2025-07-15 | infrastructure-only | 2.19 |
