# Portfolio Modernization Assessment Report

**Date**: 2026-04-17
**Services Assessed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.
**Technology Preferences**: Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock, terraform, gitops; Avoid: self-managed-kafka, self-managed-kubernetes, oracle, manual-deployments

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 2.15 / 4.0 |
| Score Range | 1.40 – 2.71 |
| Score Variance (σ) | 0.46 |
| Highest Scoring Service | books-api (2.71) |
| Lowest Scoring Service | unishop-monolith (1.40) |
| Pathways Triggered (portfolio-wide) | 6 of 7 |
| Cross-Cutting Foundational Blockers | 22 |
| Cross-Cutting Improvement Opportunities | 3 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 1 | 20% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 3 | 60% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 1 | 20% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 2.40 | 1.00 | 3.00 | 0 |
| Application Architecture (APP) | 2.17 | 1.33 | 3.00 | 1 |
| Data Platform (DATA) | 2.95 | 2.50 | 4.00 | 0 |
| Security Baseline (SEC) | 1.86 | 1.00 | 2.71 | 0 |
| Operations & Observability (OPS) | 1.33 | 1.00 | 2.44 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 4 | 80% |
| infrastructure-only | 1 | 20% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-04-17 |
| total_services | 5 |
| portfolio_score | 2.15 |
| score_range_min | 1.40 |
| score_range_max | 2.71 |
| mature_services | 0 |
| partial_services | 1 |
| needs_work_services | 3 |
| not_ready_services | 1 |
| pathways_triggered | 6 |
| foundational_blockers | 22 |
| improvement_opportunities | 3 |
| category_inf | 2.40 |
| category_app | 2.17 |
| category_data | 2.95 |
| category_sec | 1.86 |
| category_ops | 1.33 |
| portfolio_level_avg | 1.80 |

## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| PHP | 1 (local-monolith) | 20% |
| Java | 1 (unishop-monolith) | 20% |
| JavaScript/TypeScript | 2 (aws-microservices, books-api) | 40% |
| Terraform/HCL | 1 (eks-saas-gitops) | 20% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| MySQL (RDS) | Relational | 1 (local-monolith) | Yes |
| MySQL (self-managed) | Relational | 1 (unishop-monolith) | No |
| DynamoDB | NoSQL / Key-Value | 3 (aws-microservices, books-api, eks-saas-gitops) | Yes |

**Database Distribution**: 4 managed (RDS MySQL + 3× DynamoDB), 1 self-managed (unishop-monolith MySQL), 0 commercial, 5 open source / AWS-native

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| App Runner (Managed Containers) | 1 (local-monolith) | 20% |
| EC2 / VM-based | 1 (unishop-monolith) | 20% |
| Serverless (Lambda) | 2 (aws-microservices, books-api) | 40% |
| EKS / Containers | 1 (eks-saas-gitops) | 20% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| CloudFormation | IaC | 1 (local-monolith) |
| CDK | IaC | 2 (aws-microservices, books-api pipeline) |
| SAM | IaC | 1 (books-api) |
| Terraform | IaC | 1 (eks-saas-gitops) |
| None | IaC | 1 (unishop-monolith) |
| CodePipeline | CI/CD | 1 (books-api) |
| Flux CD | CI/CD | 1 (eks-saas-gitops) |
| Gitea Actions | CI/CD | 1 (eks-saas-gitops — sample only) |
| None | CI/CD | 3 (local-monolith, unishop-monolith, aws-microservices) |

### Messaging / Streaming

| Technology | Services |
|------------|----------|
| EventBridge + SQS | 1 (aws-microservices) |
| SQS | 1 (eks-saas-gitops) |
| None | 3 (local-monolith, unishop-monolith, books-api) |

### Standardization Opportunities

- **IaC Fragmentation (Critical)**: 5 distinct IaC tools/approaches across 5 services (CloudFormation, CDK, SAM, Terraform, none). The preferred IaC tool is **Terraform**, but only 1 service (eks-saas-gitops) currently uses it. **Recommendation**: Standardize on Terraform across the portfolio for consistent state management, module reuse, and GitOps compatibility.
- **CI/CD Gap**: 3 of 5 services (60%) have no CI/CD pipeline at all. Only books-api has a mature pipeline. **Recommendation**: Establish a shared CI/CD pipeline template using GitHub Actions or AWS CodePipeline with GitOps deployment patterns.
- **DynamoDB as Dominant Database**: 3 of 5 services use DynamoDB (preferred). The remaining 2 use MySQL. **Recommendation**: Migrate unishop-monolith's self-managed MySQL to **Aurora MySQL** (preferred). Local-monolith already uses managed RDS MySQL — consider Aurora upgrade for consistency.
- **Messaging Adoption**: 3 of 5 services have no async messaging. **Recommendation**: Standardize on **Amazon EventBridge** (preferred) as the portfolio-wide event bus for inter-service communication.
- **Compute Convergence Target**: EKS (preferred) is the target for non-serverless workloads. Both monoliths should be containerized and deployed to the eks-saas-gitops EKS platform.
- **Technology Diversity Score**: 15 distinct technologies / 5 services = 3.0 (high fragmentation — score 2 on standardization scale).

## Service Dependency Map

> Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

| Source Service | Target Service | Type | Coupling | Description |
|---------------|---------------|------|----------|-------------|
| unishop-monolith | eks-saas-gitops | shared_infra | Medium | EKS is the target compute platform for containerized monolith (context: "everything that is not serverless will run here") |
| local-monolith | eks-saas-gitops | shared_infra | Medium | EKS is the target compute platform for containerized monolith post-decomposition |
| local-monolith | aws-microservices | async | Low | Inventory events from local-monolith will feed agent that invokes aws-microservices for order/return processing |
| unishop-monolith | aws-microservices | async | Low | Order data from unishop-monolith feeds into the agent orchestration layer alongside aws-microservices |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| eks-saas-gitops | 2 | 0 | 60% | Foundation | 2.49 |
| aws-microservices | 2 | 0 | 40% | Internal | 2.27 |
| local-monolith | 0 | 2 | 0% | Leaf | 1.90 |
| unishop-monolith | 0 | 2 | 0% | Leaf | 1.40 |
| books-api | 0 | 0 | 0% | Independent | 2.71 |

### Foundation Services (High Fan-In)

- **eks-saas-gitops** (Fan-in: 2) — Centralized EKS platform. Both monoliths will be deployed here post-containerization. Must be hardened and stabilized before onboarding workloads.

### Circular Dependencies

✅ No circular dependencies detected. All inferred dependencies are acyclic — the dependency graph flows from leaf services (monoliths) toward foundation services (eks-saas-gitops) and integration services (aws-microservices).

### Critical Path Analysis

- **Longest dependency chain**: 1 hop (monoliths → eks-saas-gitops)
- **Sequencing constraint**: eks-saas-gitops must be secured and stabilized (Phase 1) before monoliths can be deployed to it (Phase 2)
- **Independent services**: books-api has no dependencies and can be modernized in any phase

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.

1. **OPS-Q3: Business Metrics** — 5 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, books-api=1, eks-saas-gitops=1
   - **Impact**: Zero visibility into business outcomes across the entire portfolio. Cannot measure modernization ROI or make data-driven decisions.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, books-api, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Establish a shared CloudWatch custom metrics namespace (`ecommerce-platform/business`). Define standard business metrics per service (orders/min, cart abandonment, API usage). Use CloudWatch Embedded Metric Format (EMF) in Lambda and structured logging with metrics in EKS workloads.

2. **OPS-Q1: Distributed Tracing** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; books-api=4
   - **Impact**: Cannot trace requests across service boundaries. Agent interactions spanning multiple services will be undiagnosable.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy a centralized OpenTelemetry Collector on EKS (ADOT) and enable X-Ray tracing on all Lambda functions. books-api already has full X-Ray instrumentation — use it as the reference implementation.

3. **OPS-Q2: SLO Definitions** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; books-api=2
   - **Impact**: No formal service level objectives. Cannot measure if the portfolio meets user expectations or track error budgets.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Define SLOs for each service's critical user journeys. Start with availability (99.9%) and p99 latency targets. Implement CloudWatch Application Signals for SLO monitoring.

4. **OPS-Q4: Anomaly Detection and Alerting** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; books-api=2
   - **Impact**: Production failures go undetected until users report them. No proactive incident detection across the portfolio.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy centralized alerting: CloudWatch alarms for all services, Prometheus AlertManager on EKS, SNS integration with PagerDuty/OpsGenie. Enable CloudWatch anomaly detection on key metrics.

5. **OPS-Q6: Integration Testing** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; books-api=3
   - **Impact**: No automated regression detection. Any modernization change risks breaking existing functionality without detection.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Establish a shared testing strategy. Require integration tests before merging. Use books-api's test suite (unit + e2e + pre-traffic smoke tests) as the reference pattern.

6. **OPS-Q7: Incident Response Automation** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; books-api=2
   - **Impact**: All incident response is ad hoc. No runbooks, no automated remediation, no escalation procedures.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Create shared runbook templates as SSM Automation documents. Define incident escalation procedures. Leverage Argo Workflows on eks-saas-gitops for automated platform-level remediation.

7. **OPS-Q8: Observability Ownership** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; books-api=2
   - **Impact**: No accountability for monitoring, alerting, or incident response. Alarms have no defined owners.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Add CODEOWNERS files to all repositories. Assign dashboard and alarm ownership. Establish on-call rotations per service.

8. **APP-Q5: API Versioning Strategy** — 4 of 4 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, books-api=1 (eks-saas-gitops=N/A)
   - **Impact**: Breaking API changes affect all consumers immediately. Critical blocker for agent integration — agents need stable, versioned APIs with OpenAPI specs.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, books-api
   - **Portfolio-Level Recommendation**: Mandate URL-based API versioning (`/v1/`) across all services. Generate OpenAPI specs — this is prerequisite for Amazon Bedrock Agents tool discovery.

9. **INF-Q3: Workflow Orchestration** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, books-api=1; eks-saas-gitops=4
   - **Impact**: All workflow logic is hardcoded. No visual management, no automated retry/error handling, no state machines for complex business processes.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, books-api
   - **Portfolio-Level Recommendation**: Adopt AWS Step Functions for application-level workflow orchestration. eks-saas-gitops already has Argo Workflows for infrastructure workflows — extend this pattern.

10. **SEC-Q7: Application Security Pipeline** — 4 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, books-api=1; eks-saas-gitops=2
    - **Impact**: No automated security scanning. Vulnerabilities reach production undetected across the entire portfolio.
    - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, books-api
    - **Portfolio-Level Recommendation**: Create a shared security scanning pipeline template: SAST (Semgrep/CodeGuru), dependency scanning (npm audit/composer audit/Snyk), container scanning (ECR + Trivy). Gate all deployments on critical vulnerability findings.

11. **INF-Q4: Async Messaging and Streaming** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1, books-api=1; aws-microservices=4, eks-saas-gitops=3
    - **Impact**: Tight coupling between domains. No event-driven architecture for the majority of the portfolio.
    - **Affected Services**: local-monolith, unishop-monolith, books-api
    - **Portfolio-Level Recommendation**: Deploy a shared Amazon EventBridge event bus (preferred). Define standard event schemas for domain events (OrderCreated, InventoryUpdated, BookCreated). aws-microservices already uses EventBridge — replicate this pattern.

12. **INF-Q11: CI/CD Automation** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1; books-api=3, eks-saas-gitops=2
    - **Impact**: Manual deployments are error-prone and slow. Blocks all other modernization efforts for 3 services.
    - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
    - **Portfolio-Level Recommendation**: Create shared CI/CD pipeline templates. Avoid manual deployments (per preferences). Use GitOps (preferred) with ArgoCD/Flux for EKS workloads and CodePipeline for serverless.

13. **SEC-Q1: Audit Logging** — 3 of 5 applicable services score < 2
    - **Score Distribution**: unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; local-monolith=2, books-api=2
    - **Impact**: No audit trail for API calls or resource changes in 3 services. Compliance blocker.
    - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
    - **Portfolio-Level Recommendation**: Deploy CloudTrail at the account level via Terraform. Enable log file validation and S3 Object Lock for immutable storage. Define CloudWatch Logs retention policies.

14. **SEC-Q3: API Authentication** — 3 of 5 applicable services score < 2
    - **Score Distribution**: unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; local-monolith=2, books-api=3
    - **Impact**: Three services have no real API authentication. Agent requests cannot be authenticated. Critical security vulnerability.
    - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
    - **Portfolio-Level Recommendation**: Implement centralized Amazon Cognito user pools with API Gateway authorizers. All API endpoints must require authentication before agent integration can proceed.

15. **SEC-Q4: Centralized Identity Integration** — 3 of 4 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1; books-api=3 (eks-saas-gitops=2)
    - **Impact**: Fragmented authentication. Cannot implement SSO or unified access policies for the AI agent.
    - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
    - **Portfolio-Level Recommendation**: Deploy centralized Amazon Cognito with federation support. Migrate all services to token-based authentication (OAuth2/JWT). books-api already uses Cognito — replicate its pattern.

16. **OPS-Q9: Resource Tagging Governance** — 3 of 5 applicable services score < 2
    - **Score Distribution**: unishop-monolith=1, aws-microservices=1, eks-saas-gitops=1; local-monolith=2, books-api=2
    - **Impact**: Cannot track costs per workload, identify resource ownership, or enforce budget controls.
    - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
    - **Portfolio-Level Recommendation**: Define a portfolio-wide tagging standard: `Environment`, `Service`, `Team`, `CostCenter`, `Project`. Enforce with Terraform `default_tags` and AWS Config `required-tags` rules.

17. **OPS-Q5: Deployment Strategy** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1; books-api=4, eks-saas-gitops=2
    - **Impact**: Direct-to-production deployments with no safety nets. Any bad deployment affects all users immediately.
    - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
    - **Portfolio-Level Recommendation**: Implement progressive delivery: CodeDeploy with Linear traffic shifting for Lambda (books-api pattern), Argo Rollouts/Flagger for EKS workloads. Avoid all-or-nothing deployments.

18. **INF-Q8: Backup and Recovery** — 3 of 5 applicable services score < 2
    - **Score Distribution**: unishop-monolith=1, aws-microservices=1, books-api=1; local-monolith=3, eks-saas-gitops=2
    - **Impact**: No backup strategy for 3 services. Data loss would be unrecoverable.
    - **Affected Services**: unishop-monolith, aws-microservices, books-api
    - **Portfolio-Level Recommendation**: Enable DynamoDB PITR on all tables. Create AWS Backup plans via Terraform. Migrate to Aurora (preferred) which has built-in automated backups.

19. **DATA-Q1: Unstructured Data Storage** — 4 of 4 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1, aws-microservices=1, books-api=1 (eks-saas-gitops=N/A)
    - **Impact**: No capability to store or process product images, documents, or files across the portfolio.
    - **Affected Services**: local-monolith, unishop-monolith, aws-microservices, books-api
    - **Portfolio-Level Recommendation**: Create a shared S3 bucket strategy for product images and documents. Implement pre-signed URLs for secure upload/download. S3 also provides the document corpus for future RAG-based knowledge agents.

20. **APP-Q2: Monolith vs Microservices** — 2 of 4 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1; aws-microservices=3, books-api=3 (eks-saas-gitops=N/A)
    - **Impact**: Both P0 monoliths block independent scaling, deployment, and team autonomy. Primary trigger for Move to Cloud Native pathway.
    - **Affected Services**: local-monolith, unishop-monolith
    - **Portfolio-Level Recommendation**: Execute Strangler Fig decomposition for both monoliths. Extract inventory and order services first to enable agent integration.

21. **APP-Q3: Async vs Sync Communication** — 2 of 4 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1; aws-microservices=3, books-api=2 (eks-saas-gitops=N/A)
    - **Impact**: Tight coupling and cascading failure risk in both monoliths.
    - **Affected Services**: local-monolith, unishop-monolith
    - **Portfolio-Level Recommendation**: Introduce EventBridge (preferred) for async domain events during decomposition.

22. **APP-Q4: Long-Running Process Handling** — 2 of 4 applicable services score < 2
    - **Score Distribution**: local-monolith=1, unishop-monolith=1; aws-microservices=4, books-api=4 (eks-saas-gitops=N/A)
    - **Impact**: All operations are synchronous in both monoliths, regardless of duration.
    - **Affected Services**: local-monolith, unishop-monolith
    - **Portfolio-Level Recommendation**: Implement Step Functions for multi-step workflows and SQS for async job processing.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking.
> Address as capacity allows or in parallel with other modernization work.

1. **INF-Q6: API Entry Point** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith=2, unishop-monolith=1, aws-microservices=2; books-api=4, eks-saas-gitops=3
   - **Impact**: Lack of unified API Gateway with throttling, validation, and per-tenant rate limiting.
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Deploy Amazon API Gateway (preferred) as the unified entry point for all services. Consolidate the three separate API Gateway instances in aws-microservices.

2. **SEC-Q5: Secrets Management** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith=2, unishop-monolith=1, eks-saas-gitops=2; aws-microservices=3, books-api=4
   - **Impact**: Hardcoded credentials in unishop-monolith. No secrets rotation across most services.
   - **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Migrate all secrets to AWS Secrets Manager with automatic rotation. Use External Secrets Operator on EKS to sync with Kubernetes secrets.

3. **SEC-Q6: Compute Hardening and Patching** — 3 of 5 applicable services score < 3
   - **Score Distribution**: unishop-monolith=1, aws-microservices=2, eks-saas-gitops=2; local-monolith=3, books-api=3
   - **Impact**: Outdated runtimes and dependencies. No vulnerability scanning automation.
   - **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Upgrade all Lambda runtimes to Node.js 20+. Upgrade Java to 17+. Use Bottlerocket AMIs for EKS worker nodes. Enable AWS Inspector for continuous vulnerability scanning.

### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 2.40 / 4.0**

**Common Patterns:**
- IaC adoption: 4 of 5 services have some IaC (80%), but fragmented across 4 tools
- High IaC coverage: books-api (4), aws-microservices (4), eks-saas-gitops (4) demonstrate excellent IaC
- Managed compute: 4 of 5 services use managed compute (App Runner, Lambda, EKS); only unishop-monolith is on raw EC2

**Critical Gaps:**
1. CI/CD: 3 of 5 services have no CI/CD pipeline — this is the single most impactful gap blocking all modernization
2. Async messaging: 3 of 5 services have no event-driven architecture capability
3. Workflow orchestration: 4 of 5 services lack workflow orchestration (only eks-saas-gitops has Argo Workflows)

#### Application Architecture

**Portfolio Score: 2.17 / 4.0** (4 applicable services; eks-saas-gitops N/A)

**Common Patterns:**
- Serverless services (aws-microservices, books-api) score well: APP 3.0 and 2.83 respectively
- Both monoliths score poorly: APP 1.33 (local-monolith) and 1.5 (unishop-monolith)

**Critical Gaps:**
1. API versioning: All 4 applicable services score 1 — universal gap that blocks agent integration
2. Monolith decomposition: Both P0 monoliths need Strangler Fig decomposition
3. Async communication: 2 of 4 services have zero async patterns

#### Data Platform

**Portfolio Score: 2.95 / 4.0**

**Common Patterns:**
- DynamoDB (preferred) is dominant: 3 services use it with full managed status
- No stored procedures across the portfolio — clean separation of business logic (DATA-Q4 = 4 in all applicable services)
- Database versions are well-managed where applicable

**Critical Gaps:**
1. Unstructured data: All 4 applicable services score 1 — no S3 or object storage
2. Self-managed MySQL: unishop-monolith has no managed database — must migrate to Aurora MySQL (preferred)

#### Security Baseline

**Portfolio Score: 1.86 / 4.0**

**Common Patterns:**
- Encryption at rest is partially adopted (4 of 5 services score 3) using AWS-managed keys
- books-api has the most mature security posture (Cognito, IAM policies, no hardcoded secrets)

**Critical Gaps:**
1. API authentication: 3 services have no real auth (scores of 1) — especially critical for eks-saas-gitops with internet-facing Argo Workflows
2. Security pipeline: 4 of 5 services have no automated security scanning
3. Audit logging: 3 services have no CloudTrail or structured audit logging
4. Hardcoded credentials: unishop-monolith has plaintext DB credentials in source control

#### Operations & Observability

**Portfolio Score: 1.33 / 4.0**

**Common Patterns:**
- books-api is the only service with meaningful observability (OPS 2.44) — X-Ray tracing, error alarms, integration tests
- All other services score 1.0–1.11 — near-zero operational maturity

**Critical Gaps:**
1. Business metrics: All 5 services score 1 — the most pervasive gap in the portfolio
2. Tracing: 4 of 5 services have no distributed tracing
3. Alerting: 4 of 5 services have no alerting capability
4. Testing: 4 of 5 services have no integration tests
5. Incident response: 4 of 5 services have no runbooks or automated remediation

## Portfolio Modernization Roadmap

> Dependency-aware phased roadmap with fixed phase names. Services are ordered by dependency graph position, then by priority (P0 → P1 → P2), then by score.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services before downstream dependents
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Independent services can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, break circular dependencies, and address portfolio-wide blockers.

**Cross-Cutting Activities:**
- **CI/CD Pipeline Templates**: Create shared pipeline templates (GitHub Actions + ArgoCD for EKS, CodePipeline for Lambda). Addresses INF-Q11 Foundational Blocker.
- **Centralized Observability Platform**: Deploy ADOT Collector on EKS, enable X-Ray on Lambda. Create shared CloudWatch dashboards. Addresses OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4 Foundational Blockers.
- **CloudTrail & Audit Logging**: Deploy account-level CloudTrail via Terraform. Addresses SEC-Q1 Foundational Blocker.
- **Centralized Identity (Cognito)**: Deploy shared Cognito User Pool with federation. Addresses SEC-Q3, SEC-Q4 Foundational Blockers.
- **Security Scanning Pipeline**: Create shared Semgrep + dependency scanning + ECR scanning templates. Addresses SEC-Q7 Foundational Blocker.
- **Tagging Standard**: Define and enforce portfolio-wide tagging governance via Terraform `default_tags`. Addresses OPS-Q9 Blocker.
- **API Versioning Standard**: Define `/v1/` versioning convention and OpenAPI spec generation requirements. Addresses APP-Q5 Blocker.
- **EventBridge Event Bus**: Deploy shared EventBridge bus with standard event schemas. Addresses INF-Q4 Blocker.

**Organizational Enablers:**
- Training: Terraform, EKS/Kubernetes, GitOps (ArgoCD/Flux), Observability (X-Ray/OTEL), Amazon Bedrock
- Tooling: Standardize on Terraform, establish Terraform module registry
- Standards: API versioning convention, tagging standard, security scanning requirements, observability ownership model

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize foundation services and establish patterns.

**Services in Scope:**

1. **eks-saas-gitops** (P1, Score: 2.49 / 4.0) — Foundation Service
   - Current State: EKS platform with excellent IaC and workflow orchestration but critical security gaps (unauthenticated Argo Workflows, internet-facing management UIs)
   - Target State: Secured EKS platform ready to onboard application workloads
   - Key Activities:
     - **CRITICAL**: Fix Argo Workflows `--auth-mode=server` → add OIDC/Dex authentication
     - Switch all management UIs (Argo, Kubecost, Capacitor) to internal LoadBalancers
     - Set `cluster_endpoint_public_access = false`
     - Add Terraform CI pipeline (validate, plan, checkov)
     - Enable S3 versioning on artifact buckets
     - Add `default_tags` to Terraform provider
     - Deploy OpenTelemetry Collector (ADOT) as DaemonSet
   - Dependencies: None (foundation service)
   - Blocks: unishop-monolith, local-monolith (EKS platform must be secured first)
   - Estimated Effort: Medium

2. **unishop-monolith** (P0, Score: 1.40 / 4.0) — Highest Priority
   - Current State: Legacy Java Spring Boot on raw EC2, zero IaC, no CI/CD, hardcoded credentials, self-managed MySQL. Lowest score in portfolio.
   - Target State: Containerized on EKS with Terraform IaC, CI/CD pipeline, Aurora MySQL, rotated credentials
   - Key Activities:
     - **CRITICAL**: Rotate compromised database credentials (hardcoded in source)
     - Create Dockerfile for Spring Boot application
     - Create Terraform IaC for VPC, EKS deployment, Aurora MySQL
     - Migrate self-managed MySQL to Aurora MySQL (preferred) via DMS
     - Create CI/CD pipeline with GitHub Actions + ArgoCD (GitOps preferred)
     - Add integration tests before decomposition
     - Upgrade Java 8 → 17+, Spring Boot 2.1 → 3.x, AWS SDK v1 → v2
   - Dependencies: eks-saas-gitops (deploys to EKS platform)
   - Blocks: Agent integration (needs discrete order/return APIs)
   - Estimated Effort: High

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize services that depend on Phase 1 services. Replicate proven patterns.

**Services in Scope:**

1. **local-monolith** (P0, Score: 1.90 / 4.0)
   - Current State: PHP monolith on App Runner, CloudFormation IaC, no CI/CD, no async patterns, session-based auth
   - Target State: Decomposed services on EKS with Terraform, CI/CD, EventBridge, Cognito auth
   - Key Activities:
     - Create CI/CD pipeline (GitHub Actions + ArgoCD)
     - Migrate IaC from CloudFormation to Terraform (preferred)
     - Begin Strangler Fig decomposition: extract Inventory Service first (P0 for agent restocking)
     - Migrate authentication from PHP sessions to Cognito
     - Add EventBridge for domain events (OrderCreated, InventoryUpdated)
     - Add X-Ray tracing and CloudWatch business metrics
     - Add integration tests for critical API endpoints
   - Dependencies: eks-saas-gitops (deploys decomposed services to EKS)
   - Blocks: Agent restocking feature (needs inventory API)
   - Estimated Effort: High

2. **aws-microservices** (P0, Score: 2.27 / 4.0)
   - Current State: Well-architected serverless microservices but missing CI/CD, API auth, network security, tracing
   - Target State: Production-ready serverless with CI/CD, Cognito auth, X-Ray tracing, security scanning
   - Key Activities:
     - Create CI/CD pipeline (CDK Pipelines or GitHub Actions)
     - Add Cognito authorizer to all API Gateway endpoints
     - Upgrade Lambda runtime Node.js 14 → 20+
     - Enable X-Ray tracing on all Lambda functions
     - Add VPC endpoints for DynamoDB
     - Add WAF to API Gateway
     - Consolidate 3 API Gateways into 1 with path-based routing
     - Add DLQ to SQS OrderQueue
     - Enable DynamoDB PITR, change RemovalPolicy to RETAIN
   - Dependencies: None (independent serverless stack)
   - Blocks: Agent order/return processing (needs authenticated, documented APIs)
   - Estimated Effort: Medium

**Parallel Tracks:**
- local-monolith and aws-microservices can be modernized concurrently — they have no mutual dependencies

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize leaf services, implement advanced capabilities, continuous improvement.

**Services in Scope:**

1. **books-api** (P1, Score: 2.71 / 4.0)
   - Current State: Most mature service in portfolio — full CI/CD, X-Ray tracing, Cognito auth, deployment strategy. Minor gaps only.
   - Target State: Fully optimized with API versioning, EventBridge events, security scanning
   - Key Activities:
     - Add API versioning (`/v1/books`)
     - Generate OpenAPI spec for Bedrock Agent tool discovery
     - Add `GET /books/{isbn}` endpoint for efficient agent lookups
     - Add EventBridge events for BookCreated
     - Add `npm audit` to CI/CD pipeline
     - Add business metrics (CloudWatch EMF)
     - Strengthen Cognito password policy, migrate to auth code flow with PKCE
   - Dependencies: None (independent)
   - Estimated Effort: Low

2. **All Services — AI Agent Integration**
   - Key Activities:
     - Deploy Amazon Bedrock agent with tool endpoints for all services
     - Configure agent action groups: inventory restocking, order status, return processing, product lookups
     - Generate OpenAPI specs for all service APIs (prerequisite)
     - Implement agent evaluation framework (Ragas/DeepEval)
     - Add DynamoDB tables for agent session state
     - Implement feedback loop for agent quality improvement
   - Dependencies: Phase 1 + Phase 2 must be complete (APIs authenticated, documented, observable)
   - Estimated Effort: Medium

**Continuous Improvement:**
- Advanced observability: SLO monitoring, error budgets, automated canary analysis
- Complete monolith decomposition (remaining services from local-monolith and unishop-monolith)
- Event-driven architecture maturation across all services

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6+ months (with 2 parallel tracks in Phase 2)
**Critical Path**: Phase 0 → eks-saas-gitops (Phase 1) → monolith containerization (Phase 1–2) → Agent integration (Phase 3)

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

This table shows exactly which repositories fall into each pathway status, providing a single at-a-glance view of pathway coverage across the portfolio. Each repo appears in exactly one column per pathway row.

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | local-monolith, unishop-monolith | aws-microservices, books-api | eks-saas-gitops |
| Move to Containers | unishop-monolith | local-monolith, aws-microservices, books-api | eks-saas-gitops |
| Move to Open Source | — | local-monolith, unishop-monolith, aws-microservices, books-api | eks-saas-gitops |
| Move to Managed Databases | unishop-monolith | local-monolith, aws-microservices, books-api | eks-saas-gitops |
| Move to Managed Analytics | — | local-monolith, unishop-monolith, aws-microservices, books-api | eks-saas-gitops |
| Move to Modern DevOps | local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops | books-api | — |
| Move to AI | local-monolith, unishop-monolith, aws-microservices, books-api | — | eks-saas-gitops |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| local-monolith | ✅ | — | — | — | — | ✅ | ✅ |
| unishop-monolith | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| aws-microservices | — | — | — | — | — | ✅ | ✅ |
| books-api | — | — | — | — | — | — | ✅ |
| eks-saas-gitops | N/A | N/A | — | — | N/A | ✅ | N/A |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Open Source may precede Move to Managed Databases (migrate off proprietary first — N/A here, all MySQL is open source)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is often a prerequisite for Move to AI (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1 (Infrastructure)**: Move to Modern DevOps → Move to Containers → Move to Cloud Native (sequential for unishop-monolith)
- **Track 2 (Data + AI)**: Move to Managed Databases → Move to AI (sequential for unishop-monolith; parallel for others)

### Pathway Details

#### Move to Cloud Native

- **Services Affected**: local-monolith, unishop-monolith (2 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - APP-Q2 = 1 (monolith): affects 2 services
  - APP-Q3 = 1 (all sync): affects 2 services
  - APP-Q4 = 1 (no async processing): affects 2 services
  - INF-Q1 = 1 (raw EC2): affects 1 service (unishop-monolith)
- **Representative AWS Services**: Amazon EKS (preferred), Amazon API Gateway (preferred), Amazon EventBridge (preferred), Amazon Aurora MySQL (preferred), Amazon DynamoDB (preferred), AWS Step Functions
- **Key Activities**:
  1. Strangler Fig decomposition for both monoliths
  2. Extract Inventory Service (local-monolith) and Basket/Order Service (unishop-monolith) first for agent APIs
  3. Introduce EventBridge for inter-service communication
- **Cross-Service Synergies**: Shared decomposition patterns, common API Gateway configuration, reusable Terraform EKS modules
- **Estimated Effort**: High across 2 services
- **Roadmap Phase Alignment**: Phase 1–2
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Containers

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q1 = 1 (raw EC2): 1 service
  - No container definitions found: 1 service
- **Representative AWS Services**: Amazon EKS (preferred), Amazon ECR, EKS managed node groups with Graviton
- **Key Activities**:
  1. Create Dockerfile for Spring Boot monolith
  2. Deploy to EKS cluster (eks-saas-gitops)
  3. Establish container image scanning pipeline
- **Cross-Service Synergies**: EKS platform (eks-saas-gitops) serves both monoliths
- **Estimated Effort**: Medium for 1 service
- **Roadmap Phase Alignment**: Phase 1
- **Relevant Learning Materials**: Module 3 — Move to Containers

#### Move to Managed Databases

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q2 = 1 (self-managed MySQL): 1 service
  - DATA-Q3 = 2 (version not pinned in IaC): 1 service
- **Representative AWS Services**: Amazon Aurora MySQL (preferred), AWS DMS, Amazon DynamoDB (preferred for basket data post-decomposition), Amazon RDS Proxy
- **Key Activities**:
  1. Discover actual MySQL server version
  2. Migrate to Aurora MySQL via AWS DMS
  3. Update application connection string
  4. Post-decomposition: move basket data to DynamoDB (preferred)
- **Cross-Service Synergies**: Aurora MySQL Terraform modules can be shared with local-monolith's RDS MySQL upgrade
- **Estimated Effort**: Medium for 1 service
- **Roadmap Phase Alignment**: Phase 1
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Modern DevOps

- **Services Affected**: local-monolith, unishop-monolith, aws-microservices, eks-saas-gitops (4 total)
- **Portfolio Priority**: High (80% of portfolio triggered, all P0 services affected)
- **Common Trigger Criteria**:
  - INF-Q11 < 3 (CI/CD): affects 4 services
  - OPS-Q5 = 1 (no deployment strategy): affects 3 services
  - OPS-Q6 = 1 (no integration tests): affects 4 services
  - INF-Q10 = 1 (zero IaC): affects 1 service (unishop-monolith)
- **Representative AWS Services**: Terraform (preferred), ArgoCD/Flux CD (GitOps preferred), AWS CodePipeline, AWS CodeBuild, Amazon ECR, GitHub Actions
- **Key Activities**:
  1. Create CI/CD pipelines for 3 services with zero pipelines
  2. Add Terraform CI validation for eks-saas-gitops
  3. Implement progressive delivery (CodeDeploy for Lambda, Flagger/Argo Rollouts for EKS)
  4. Add integration testing to all services
  5. Standardize on Terraform across the portfolio
- **Cross-Service Synergies**: Shared CI/CD pipeline templates, shared Terraform modules, common GitOps workflow patterns. books-api's pipeline is the reference implementation.
- **Estimated Effort**: Medium across 4 services
- **Roadmap Phase Alignment**: Phase 0 (cross-cutting enabler) + Phase 1–2 (per-service pipelines)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: local-monolith, unishop-monolith, aws-microservices, books-api (4 total)
- **Portfolio Priority**: High (80% of portfolio triggered, aligned with agent integration goal)
- **Aggregation**: Move to AI: Triggered in 4 of 5 services (1 service — eks-saas-gitops — is infrastructure-only, pathway correctly marked Not Applicable)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): — (no services)
  - Already present (AI frameworks detected): — (no services)
  - Not Applicable (infrastructure-only): eks-saas-gitops
- **Common Trigger Criteria**:
  - No AI/agent frameworks detected: affects 4 services
  - Context contains "agent" AI signal term: all 4 services have AI intent confirmed
- **Representative AWS Services**: Amazon Bedrock (preferred), Amazon Bedrock AgentCore, Amazon Bedrock Knowledge Bases, Amazon DynamoDB (preferred for agent state), Amazon API Gateway (preferred for tool endpoints), Amazon EventBridge (preferred for event-driven triggers)
- **Key Activities**:
  1. Generate OpenAPI specs for all service APIs (prerequisite for Bedrock Agent tool discovery)
  2. Deploy Amazon Bedrock agent with action groups mapped to service endpoints
  3. Configure agent tools: inventory restocking (local-monolith), order status + return processing (aws-microservices/unishop-monolith), product lookups (books-api)
  4. Implement agent evaluation framework
  5. Add vector database (OpenSearch Serverless) for RAG-based knowledge agents
- **Cross-Service Synergies**: Shared Bedrock agent configuration, common tool endpoint patterns, unified agent evaluation framework, shared DynamoDB agent session state table
- **Estimated Effort**: Medium across 4 services
- **Roadmap Phase Alignment**: Phase 3 (requires authenticated, documented APIs from Phases 1–2)
- **Relevant Learning Materials**: Module 7 — Move to AI

## Integration Opportunities

### Shared Service Extraction

**Opportunity: Centralized Authentication & Identity (Cognito)**
- **Current State**: Fragmented across portfolio — books-api has Cognito, local-monolith uses PHP sessions, unishop-monolith has disabled Spring Security, aws-microservices has no auth, eks-saas-gitops has no auth on Argo
- **Proposed Solution**: Deploy a shared Amazon Cognito User Pool with federation support. All services use Cognito JWT tokens for API authentication. Machine-to-machine OAuth2 flows for agent access via client credentials grant.
- **Benefits**: Unified identity, SSO capability, consistent auth patterns, agent identity management
- **Effort**: Medium
- **Priority**: High — prerequisite for agent integration

**Opportunity: Centralized Observability Platform**
- **Current State**: Only books-api has X-Ray tracing. All other services have zero observability.
- **Proposed Solution**: Deploy ADOT Collector on EKS, enable X-Ray on all Lambda functions, create shared CloudWatch dashboards with portfolio-wide metrics namespace.
- **Benefits**: End-to-end request tracing across agent interactions, unified metrics, centralized alerting
- **Effort**: Medium
- **Priority**: High — required for production readiness

**Opportunity: Shared Terraform Module Registry**
- **Current State**: 5 different IaC tools across the portfolio
- **Proposed Solution**: Create reusable Terraform modules for common patterns: VPC, EKS deployment, Aurora MySQL, DynamoDB, API Gateway, EventBridge, CloudWatch dashboards
- **Benefits**: Consistent infrastructure, faster provisioning, reduced drift
- **Effort**: Medium
- **Priority**: High — enables all modernization work

### Event-Driven Architecture

**Opportunity: Portfolio Event Bus**
- **Current State**: aws-microservices uses EventBridge for checkout flow. All other services are synchronous.
- **Proposed Solution**: Deploy a shared Amazon EventBridge event bus (preferred). Standard event schemas: `OrderCreated`, `InventoryUpdated`, `BookCreated`, `ReturnRequested`, `TenantOnboarded`.
- **Benefits**: Decoupled services, agent event triggers (e.g., inventory threshold → restocking), audit trail
- **Effort**: Medium

**Opportunity: Async Order Fulfillment**
- **Current State**: local-monolith processes orders synchronously in a single PHP transaction
- **Proposed Solution**: EventBridge + Step Functions for orchestrated fulfillment: validate → assign warehouse → pick → pack → QC → ship
- **Benefits**: Resilience, visibility, automated retry, agent integration for warehouse assignment
- **Effort**: High

### API Gateway Consolidation

- **Current State**: aws-microservices has 3 separate API Gateway instances. local-monolith uses App Runner directly. unishop-monolith exposes port 8080 with no gateway.
- **Proposed Solution**: Consolidate into a unified Amazon API Gateway (preferred) architecture — one gateway per service with consistent auth, throttling, and monitoring. For EKS workloads, use API Gateway with ALB integration.
- **Benefits**: Consistent auth, rate limiting per consumer, monitoring, OpenAPI export for agent tool discovery
- **Effort**: Medium

### Observability Unification

- **Current State**: books-api has X-Ray. All others have nothing. No shared dashboards.
- **Proposed Solution**: Deploy OpenTelemetry/ADOT across all services. Centralized CloudWatch dashboards per service and portfolio-wide. Prometheus + Grafana on EKS for infrastructure metrics.
- **Benefits**: End-to-end tracing, consistent metrics, reduced tool sprawl, agent interaction monitoring
- **Effort**: Medium

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| Argo Workflows exposed without auth (eks-saas-gitops) — full cluster admin access | High | High | 🔴 Critical | Add OIDC/Dex auth, switch to internal LB, restrict ClusterRole | Phase 1 |
| Hardcoded DB credentials in source (unishop-monolith) | High | High | 🔴 Critical | Rotate credentials immediately, migrate to Secrets Manager | Phase 1 |
| No CI/CD for 3 P0 services — manual deployments | High | Medium | 🟠 High | Create CI/CD pipelines per service, adopt GitOps | Phase 0–1 |
| No observability across 4 services — blind to failures | Medium | High | 🟠 High | Deploy centralized tracing, alerting, dashboards | Phase 0–1 |
| Self-managed MySQL (unishop-monolith) — no backups, no HA | High | Medium | 🟠 High | Migrate to Aurora MySQL with Multi-AZ and automated backups | Phase 1 |
| No API authentication on 3 services — public access to CRUD | High | Medium | 🟠 High | Deploy Cognito authorizers on all API endpoints | Phase 0–1 |
| EKS API server publicly accessible (eks-saas-gitops) | Medium | High | 🟠 High | Set cluster_endpoint_public_access = false, use VPN | Phase 1 |
| No security scanning in any pipeline | Medium | Medium | 🟡 Medium | Add SAST + dependency scanning to CI/CD templates | Phase 0 |
| DynamoDB tables with RemovalPolicy.DESTROY (aws-microservices) | Medium | Medium | 🟡 Medium | Change to RETAIN, enable PITR | Phase 2 |
| Single NAT Gateway (eks-saas-gitops) — SPOF | Low | Medium | 🟡 Medium | Enable one_nat_gateway_per_az | Phase 1 |
| No integration tests across 4 services | Medium | Medium | 🟡 Medium | Add test suites using books-api as reference | Phase 1–2 |
| Gitea on unmanaged EC2 — SPOF for GitOps platform | Medium | High | 🟠 High | Migrate Gitea to EKS or managed Git service | Phase 1 |

### High-Risk Dependencies

- **unishop-monolith** (score 1.40): Lowest scoring service that provides order/return data needed for the AI agent. If this service fails, agent cannot process orders. Mitigation: Prioritize containerization and database migration in Phase 1.

### Single Points of Failure

- **eks-saas-gitops** (blast radius 60%): The centralized EKS platform affects all non-serverless workloads. Single NAT gateway and single Gitea instance amplify risk. Mitigation: Fix SPOF (NAT, Gitea) in Phase 1, add PDBs for critical controllers.
- **Gitea EC2 instance**: Backs the entire GitOps pipeline. No backup, no HA. Loss would disrupt all deployments.

### Circular Dependency Risks

✅ No circular dependencies detected.

### Data Availability Risks

- **unishop-monolith**: Self-managed MySQL with no automated backups and no HA (single EC2). High risk of data loss. Mitigation: Migrate to Aurora MySQL (preferred) with Multi-AZ and PITR.

### Observability Blind Spots

- **4 of 5 services** have no distributed tracing. The agent interaction chain (agent → API Gateway → Lambda/EKS → DynamoDB/Aurora) will be completely opaque without tracing. Mitigation: Deploy ADOT + X-Ray across all services in Phase 0.

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + service teams (cross-cutting concerns count = 22, well above the threshold of 5)

**Platform Team** (3–4 engineers):
- Responsibilities: Shared infrastructure (EKS, Terraform modules, CI/CD templates), centralized observability, shared Cognito, EventBridge, security scanning pipeline, CloudTrail, tagging governance
- Skills Required: Terraform, EKS/Kubernetes, GitOps (ArgoCD/Flux), Observability (ADOT/X-Ray/Prometheus), Cognito/IAM, CI/CD pipeline design

**Service Teams** (2 engineers per monolith, 1 per serverless service):
- Responsibilities: Service-specific modernization, decomposition, feature development, service-level testing
- Skills Required: Service-specific languages (PHP, Java, TypeScript), DynamoDB, Aurora, API Gateway, Bedrock (for agent integration)

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| Terraform | IaC standardization (all services) | Partial (eks-saas-gitops only) | High |
| EKS / Kubernetes | Monolith containerization, platform management | Partial (eks-saas-gitops only) | High |
| GitOps (ArgoCD/Flux) | Deployment automation | Partial (eks-saas-gitops only) | High |
| Observability (X-Ray/OTEL) | Tracing, metrics, alerting | Partial (books-api X-Ray only) | High |
| Amazon Bedrock / Agentic AI | Agent integration | No | Medium |
| CI/CD Pipeline Design | Pipeline creation for 3 services | Partial (books-api pipeline) | High |
| Strangler Fig Decomposition | Monolith modernization | No | Medium |
| Aurora MySQL / DMS | Database migration | No | Medium |
| Amazon Cognito | Centralized identity | Partial (books-api only) | High |

### Training Recommendations

**Phase 0 Training (Immediate — needed for cross-cutting foundation):**
- Terraform fundamentals and module development
- EKS/Kubernetes operations and GitOps workflows
- Observability with AWS X-Ray, ADOT, and CloudWatch
- CI/CD pipeline design with GitHub Actions and ArgoCD

**Phase 1–2 Training (Weeks 2–8 — needed for service modernization):**
- Strangler Fig pattern and microservices decomposition
- Aurora MySQL migration with AWS DMS
- Amazon Bedrock Agents and AgentCore fundamentals

**Phase 3 Training (Weeks 8+ — needed for AI integration):**
- Building agents with Amazon Bedrock
- Agentic AI patterns and evaluation frameworks
- RAG implementation with Bedrock Knowledge Bases

### External Support

**Recommended AWS Professional Services engagement for:**
- **Database Migration** (unishop-monolith MySQL → Aurora MySQL): High-risk activity requiring DMS expertise
- **EKS Platform Hardening** (eks-saas-gitops): Security architecture review, RBAC design, network policy implementation
- **Architecture Review**: Validate decomposition strategy for both monoliths before execution
- **Agent Architecture Design**: Amazon Bedrock agent design for multi-service tool orchestration

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | Portfolio has significant modernization needs with 4 services scoring below 2.5 | 4 of 5 services have overall score < 2.5 (unishop-monolith=1.40, local-monolith=1.90, aws-microservices=2.27, eks-saas-gitops=2.49) | Request MAP engagement via AWS Solutions Architect |
| Experience-Based Acceleration | EBA | Portfolio needs hands-on modernization guidance, especially for Move to Modern DevOps and Move to AI | All 5 services score < 3.0 and all 5 have at least one triggered pathway. Most prevalent: Move to Modern DevOps (4 services) and Move to AI (4 services) | Request EBA engagement focused on Move to Modern DevOps and Move to AI pathways |

### Program Details

**Migration Acceleration Program (MAP)**
- **Why recommended**: 80% of the portfolio (4 of 5 services) scores below 2.5, indicating significant modernization work ahead. The portfolio includes legacy monolith decomposition, database migration, containerization, and AI agent integration — all MAP-eligible activities.
- **What it provides**: Funding credits, migration tools, methodology framework, and partner support to accelerate the modernization journey. MAP provides a structured approach to assess, mobilize, and migrate/modernize workloads.
- **Suggested timing**: Begin MAP engagement in Phase 0 to fund cross-cutting foundation work and Phase 1 service modernization.

**Experience-Based Acceleration (EBA)**
- **Why recommended**: All 5 services score below 3.0 with active modernization pathways triggered. The team needs hands-on guidance for Move to Modern DevOps (80% of portfolio) and Move to AI (80% of portfolio) — both high-priority pathways.
- **What it provides**: Hands-on workshops and accelerators led by AWS experts, focused on specific modernization pathways. EBA provides practical implementation guidance, reference architectures, and working prototypes.
- **Suggested timing**: Schedule EBA workshops during Phase 0–1 for DevOps modernization and Phase 2–3 for AI agent integration.

**Programs NOT triggered:**
- **OLA**: No Oracle, SQL Server, VMware, or commercial licenses detected — MySQL (open source) and DynamoDB only
- **MMP**: No .NET or Windows workloads detected
- **VMP**: No VMware references detected
- **WAMP**: No Windows-based deployment targets detected
- **ISV WMP**: No ISV or third-party software workloads detected

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect or Partner to determine eligibility and timing.

## Recommended Self-Paced Learning Materials

> Include relevant links only from the following categories based on portfolio-wide skill gaps identified in the Resource Allocation section and triggered pathways.

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
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across multiple repos. They are distinct from cross-cutting analysis (which aggregates individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 2
- **Finding**: The portfolio uses 5 distinct IaC tools/approaches: CloudFormation (local-monolith), CDK (aws-microservices, books-api pipeline), SAM (books-api), Terraform (eks-saas-gitops), and no IaC (unishop-monolith). Terraform — the preferred tool — covers only 20% of the portfolio (1 of 5 services). The most common approach (CDK) covers 40% but is not the preferred tool.
- **Evidence**: local-monolith: `infrastructure/monolith-apprunner.yaml` (CloudFormation); aws-microservices: `lib/*.ts` (CDK); books-api: `template.yml` (SAM) + `pipeline/lib/pipeline-stack.ts` (CDK); eks-saas-gitops: `terraform/` (Terraform); unishop-monolith: no IaC files found.
- **Recommendation**: Standardize on Terraform (preferred) across the portfolio. Create a Terraform module registry with reusable modules for VPC, EKS, Aurora, DynamoDB, API Gateway, Lambda. Migrate services incrementally — start with unishop-monolith (needs IaC from scratch) and local-monolith (CloudFormation → Terraform).
- **Contextual Annotations**: This finding provides context for INF-Q10 cross-cutting scores — while 4 of 5 services have IaC (scoring well individually), portfolio-level fragmentation creates maintenance burden and knowledge silos.

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: No centralized observability platform exists. Each service operates independently: books-api has X-Ray tracing (OPS-Q1=4), but no other service shares this tracing configuration. There is no shared CloudWatch log group, no cross-service tracing, no shared dashboards, and no consistent metric namespaces. The only shared infrastructure metric comes from Kubecost on eks-saas-gitops, which is cost-focused, not observability-focused.
- **Evidence**: books-api: X-Ray tracing (Tracing: Active, TracingEnabled: true, aws-xray-sdk-core). All other services: no tracing configuration. No shared CloudWatch dashboards or metric namespaces found across repositories.
- **Recommendation**: Deploy a centralized observability stack: (1) ADOT Collector on EKS for all EKS workloads, (2) X-Ray enabled on all Lambda functions, (3) Shared CloudWatch dashboard with widgets per service, (4) Standardized metric namespace `ecommerce-platform/{service}` for business and operational metrics, (5) Centralized log aggregation with structured JSON logging format.
- **Contextual Annotations**: None — this is a net-new portfolio capability.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 4
- **Finding**: No circular dependencies detected in the inferred dependency graph. All dependencies flow in one direction: leaf services (monoliths) → foundation services (eks-saas-gitops, aws-microservices). The architecture supports independent modernization of each service.
- **Evidence**: Inferred dependency graph analysis using BFS from all service nodes. No strongly connected components with size > 1 found.
- **Recommendation**: No action needed. Maintain the acyclic dependency structure as services are decomposed. When extracting microservices from monoliths, ensure new services do not introduce circular dependencies.
- **Contextual Annotations**: None.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 1
- **Finding**: Extreme technology fragmentation: 4+ programming languages (PHP, Java, JavaScript/TypeScript, Terraform/HCL), 5 distinct IaC tools (CloudFormation, CDK, SAM, Terraform, none), 3 database engines (MySQL RDS, MySQL self-managed, DynamoDB), 4 compute patterns (App Runner, EC2, Lambda, EKS), 3+ CI/CD approaches (CodePipeline, Flux CD, none). Technology diversity score: 15 distinct technologies / 5 services = 3.0. This level of fragmentation creates significant knowledge silos and operational overhead.
- **Evidence**: All 5 MOD reports — each service uses a unique technology combination. No two services share the same IaC tool + compute pattern + CI/CD tool combination.
- **Recommendation**: Converge on preferred technologies: Terraform for IaC, EKS for containers (+ Lambda for serverless), Aurora/DynamoDB for databases, EventBridge for messaging, GitOps for deployments. Accept language diversity (PHP, Java, TypeScript) as a pragmatic reality but standardize tooling around services.
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-MOD-Q4 found extreme technology fragmentation (diversity score 3.0). This may affect the severity of INF-Q10 and INF-Q11 cross-cutting concerns for all services — **verify** that IaC migration and CI/CD standardization efforts account for the learning curve of adopting new tools.

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: No centralized security scanning pipeline, no shared WAF, and no unified vulnerability management. Each service manages security independently (or not at all). Only books-api has Cognito auth. Only eks-saas-gitops has ECR scan-on-push. No shared WAF WebACL (local-monolith has its own WAF, but it's not shared). No centralized security scanning tool (no SonarQube, no Snyk, no Dependabot). SEC category averages 1.86 across the portfolio.
- **Evidence**: books-api: Cognito auth, no security scanning; local-monolith: WAF on App Runner, no scanning; eks-saas-gitops: ECR scan-on-push, no pipeline scanning; aws-microservices: no auth, no scanning; unishop-monolith: hardcoded credentials, no scanning.
- **Recommendation**: (1) Deploy centralized security scanning: Semgrep for SAST, npm audit/composer audit/Snyk for dependencies, ECR scanning for containers, CDK-nag/Checkov for IaC. (2) Deploy shared WAF rules via Terraform module. (3) Deploy shared Cognito User Pool for unified identity. (4) Create shared AWS Config rules for security compliance. (5) Implement Dependabot or Renovate across all repositories.
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-MOD-Q5 found no shared security posture (score 1). This provides context for SEC-Q3 (API auth), SEC-Q4 (identity), and SEC-Q7 (security pipeline) cross-cutting concerns for all services — **verify** that the centralized Cognito and security scanning initiatives in Phase 0 address these individual gaps.

### Portfolio-Level Score Average

| Question | Score |
|----------|-------|
| PORT-MOD-Q1: IaC Standardization | 2 |
| PORT-MOD-Q2: Shared Observability Platform | 1 |
| PORT-MOD-Q3: Dependency Cycle Health | 4 |
| PORT-MOD-Q4: Technology Diversity | 1 |
| PORT-MOD-Q5: Shared Security Posture | 1 |
| **Portfolio-Level Average** | **1.80** |

## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| unishop-monolith | application | P0 | 1.40 | 1.00 | 1.50 | 2.50 | 1.00 | 1.00 | 5 of 7 | 1 |
| local-monolith | application | P0 | 1.90 | 2.55 | 1.33 | 2.50 | 2.00 | 1.11 | 3 of 7 | 2 |
| aws-microservices | application | P0 | 2.27 | 2.64 | 3.00 | 3.00 | 1.71 | 1.00 | 2 of 7 | 2 |
| eks-saas-gitops | infrastructure-only | P1 | 2.49 | 3.00 | N/A | 4.00 | 1.86 | 1.11 | 1 of 7 | 1 |
| books-api | application | P1 | 2.71 | 2.82 | 2.83 | 2.75 | 2.71 | 2.44 | 1 of 7 | 3 |

### Individual Service Details

#### unishop-monolith

- **Overall Score**: 1.40 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-17
- **Category Scores**:
  - Infrastructure & DevOps: 1.00
  - Application Architecture: 1.50
  - Data Platform: 2.50
  - Security Baseline: 1.00
  - Operations & Observability: 1.00
- **Top Gaps**:
  - INF-Q10: score 1 — Zero IaC, all infrastructure manually created (ClickOps)
  - INF-Q11: score 1 — No CI/CD pipeline, all deployments manual
  - SEC-Q5: score 1 — Database credentials hardcoded in plaintext in application.properties
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Rotate compromised credentials immediately
  - Create Terraform IaC and CI/CD pipeline from scratch
  - Containerize on EKS and migrate MySQL to Aurora
- **Depends On**: eks-saas-gitops (EKS platform)
- **Depended On By**: Agent integration (order/return data)
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 1 — Quick Wins

#### local-monolith

- **Overall Score**: 1.90 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2025-07-17
- **Category Scores**:
  - Infrastructure & DevOps: 2.55
  - Application Architecture: 1.33
  - Data Platform: 2.50
  - Security Baseline: 2.00
  - Operations & Observability: 1.11
- **Top Gaps**:
  - APP-Q2: score 1 — Tightly-coupled monolith, all business logic in single index.php
  - INF-Q11: score 1 — No CI/CD pipeline, manual docker-compose deployment
  - OPS-Q1–Q8: score 1 — Complete absence of operational practices
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Create CI/CD pipeline and migrate IaC to Terraform
  - Begin Strangler Fig decomposition, extract Inventory Service first
  - Add observability stack (X-Ray, CloudWatch, alerting)
- **Depends On**: eks-saas-gitops (EKS platform for decomposed services)
- **Depended On By**: Agent restocking feature (inventory API)
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 2 — Foundation

#### aws-microservices

- **Overall Score**: 2.27 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-17
- **Category Scores**:
  - Infrastructure & DevOps: 2.64
  - Application Architecture: 3.00
  - Data Platform: 3.00
  - Security Baseline: 1.71
  - Operations & Observability: 1.00
- **Top Gaps**:
  - INF-Q11: score 1 — No CI/CD pipeline, manual `cdk deploy`
  - SEC-Q3: score 1 — No authentication on any API Gateway endpoint
  - OPS-Q1–Q9: score 1 — Zero observability across all operations questions
- **Triggered Pathways**: Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Create CI/CD pipeline (CDK Pipelines or GitHub Actions)
  - Add Cognito authorizer to all API Gateway endpoints
  - Upgrade Lambda runtime from Node.js 14 to 20+
- **Depends On**: None (independent serverless stack)
- **Depended On By**: Agent order status and return processing
- **Blast Radius**: 40%
- **Roadmap Phase**: Phase 2 — Foundation

#### eks-saas-gitops

- **Overall Score**: 2.49 / 4.0
- **Repository Type**: infrastructure-only
- **Priority**: P1
- **Assessment Date**: 2025-07-17
- **Category Scores**:
  - Infrastructure & DevOps: 3.00
  - Application Architecture: N/A
  - Data Platform: 4.00
  - Security Baseline: 1.86
  - Operations & Observability: 1.11
- **Top Gaps**:
  - SEC-Q3: score 1 — Argo Workflows exposed internet-facing with no authentication and full cluster admin
  - SEC-Q1: score 1 — No CloudTrail or audit logging
  - OPS-Q1: score 1 — No distributed tracing across the platform
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**:
  - Fix Argo Workflows auth immediately (critical security risk)
  - Switch management UIs to internal LoadBalancers
  - Add Terraform CI pipeline and deploy ADOT for tracing
- **Depends On**: None (foundation service)
- **Depended On By**: unishop-monolith, local-monolith (EKS compute platform)
- **Blast Radius**: 60%
- **Roadmap Phase**: Phase 1 — Quick Wins

#### books-api

- **Overall Score**: 2.71 / 4.0
- **Repository Type**: application
- **Priority**: P1
- **Assessment Date**: 2026-04-17
- **Category Scores**:
  - Infrastructure & DevOps: 2.82
  - Application Architecture: 2.83
  - Data Platform: 2.75
  - Security Baseline: 2.71
  - Operations & Observability: 2.44
- **Top Gaps**:
  - APP-Q5: score 1 — No API versioning strategy
  - INF-Q4: score 1 — No async messaging
  - SEC-Q7: score 1 — No security scanning in CI/CD pipeline
- **Triggered Pathways**: Move to AI
- **Key Recommendations**:
  - Add API versioning and generate OpenAPI spec for Bedrock Agent
  - Add EventBridge events for BookCreated
  - Add npm audit to CI/CD pipeline
- **Depends On**: None (independent)
- **Depended On By**: Agent product lookups
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 3 — Advanced

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | local-monolith | ./monolith/monolith-mod-report.md | 2025-07-17 | application | 1.90 |
| 2 | unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/MonoToMicroLegacy-mod-report.md | 2026-04-17 | application | 1.40 |
| 3 | aws-microservices | ./services/aws-microservices/aws-microservices-mod-report.md | 2026-04-17 | application | 2.27 |
| 4 | books-api | ./services/books-api/books-api-mod-report.md | 2026-04-17 | application | 2.71 |
| 5 | eks-saas-gitops | ./services/eks-saas-gitops/eks-saas-gitops-mod-report.md | 2025-07-17 | infrastructure-only | 2.49 |
