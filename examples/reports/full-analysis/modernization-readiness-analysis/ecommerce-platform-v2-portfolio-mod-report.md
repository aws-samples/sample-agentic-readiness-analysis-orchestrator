# Portfolio Modernization Assessment Report

**Date**: 2026-05-18
**Services Assessed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.
**Technology Preferences**: Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock, terraform, gitops; Avoid: self-managed-kafka, self-managed-kubernetes, oracle, manual-deployments

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 2.31 / 4.0 |
| Score Range | 1.40 – 3.00 |
| Highest Scoring Service | books-api (3.00) |
| Lowest Scoring Service | unishop-monolith (1.40) |
| Pathways Triggered (portfolio-wide) | 4 of 7 |
| Cross-Cutting Foundational Blockers | 21 |
| Cross-Cutting Improvement Opportunities | 5 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 2 | 40% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 2 | 40% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 1 | 20% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 2.60 | 1.09 | 3.36 | 0 |
| Application Architecture (APP) | 2.17 | 1.33 | 3.00 | 1 |
| Data Platform (DATA) | 3.10 | 2.25 | 4.00 | 0 |
| Security Baseline (SEC) | 2.01 | 1.17 | 2.83 | 0 |
| Operations & Observability (OPS) | 1.53 | 1.00 | 2.33 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 4 | 80% |
| infrastructure-only | 1 | 20% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-05-18 |
| total_services | 5 |
| portfolio_score | 2.31 |
| score_range_min | 1.40 |
| score_range_max | 3.00 |
| mature_services | 0 |
| partial_services | 2 |
| needs_work_services | 2 |
| not_ready_services | 1 |
| pathways_triggered | 4 |
| foundational_blockers | 21 |
| improvement_opportunities | 5 |
| category_inf | 2.60 |
| category_app | 2.17 |
| category_data | 3.10 |
| category_sec | 2.01 |
| category_ops | 1.53 |
| portfolio_level_avg | 2.00 |

## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| PHP | 1 | 20% |
| Java (Spring Boot) | 1 | 20% |
| TypeScript/Node.js | 2 | 40% |
| Python (Terraform/GitOps tooling) | 1 | 20% |
| HCL (Terraform) | 1 | 20% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| MySQL | Relational | 2 | Mixed (RDS in local-monolith, self-managed in unishop) |
| DynamoDB | NoSQL | 3 | Yes |

**Database Distribution**: 4 managed, 1 self-managed, 0 commercial, 2 open source

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| Serverless (Lambda) | 2 | 40% |
| Containers (EKS) | 1 | 20% |
| Managed Containers (App Runner) | 1 | 20% |
| EC2 / VM-based | 1 | 20% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| Terraform | IaC | 1 (eks-saas-gitops) |
| AWS CDK | IaC | 2 (aws-microservices, books-api) |
| AWS SAM | IaC | 1 (books-api) |
| CloudFormation | IaC | 1 (local-monolith) |
| None | IaC | 1 (unishop-monolith) |
| Flux CD / Gitea Actions | CI/CD | 1 (eks-saas-gitops) |
| CodePipeline / CodeBuild | CI/CD | 1 (books-api) |
| None | CI/CD | 3 (local-monolith, unishop-monolith, aws-microservices) |

### Standardization Opportunities

- **IaC Consolidation**: 4 different IaC approaches (Terraform, CDK, SAM, CloudFormation, none). Preferences favor Terraform — consider standardizing on Terraform for infrastructure-only repos and CDK for application repos.
- **CI/CD Gap**: 3 of 5 services have no CI/CD pipeline. The eks-saas-gitops GitOps pattern (Flux CD) could serve as a template for container workloads.
- **Runtime Consolidation**: aws-microservices uses EOL Node.js 14.x — urgent upgrade needed. books-api uses Node.js 22.x which should be the target.
- **Database Strategy**: DynamoDB dominates (3 services). MySQL services should evaluate Aurora MySQL per preferences.

### 🏗️ Blueprint Candidates — Repos as Standardization Templates

> These repos demonstrate strong operational patterns that can be extracted and
> applied across the portfolio. Use them as reference implementations when
> modernizing other services.

| Blueprint Repo | Overall Score | Qualifying Scores | Extractable Patterns | Benefits For |
|---|---|---|---|---|
| eks-saas-gitops | 2.93 | INF-Q1=4, INF-Q10=3, INF-Q11=3, OPS-Q5=3, INF-Q5=3, SEC-Q7=3 | Terraform modules, Flux CD GitOps, Karpenter autoscaling, VPC patterns | 3 repos scoring < 2 on these questions |
| books-api | 3.00 | INF-Q10=4, INF-Q11=4, OPS-Q5=4, INF-Q5=3, INF-Q1=4 | SAM/CDK templates, CodePipeline CI/CD, canary deployments, X-Ray tracing | 3 repos without CI/CD |

**eks-saas-gitops** — Strongest infrastructure patterns in the portfolio. Terraform modules for EKS, VPC, and Karpenter are production-ready and can be templated for other services.
- **Extract**: `terraform/modules/`, `gitops/` directory structure, Flux CD manifests, Karpenter configs
- **Apply to**: unishop-monolith (containerization target), local-monolith (EKS migration)
- **Effort**: Medium (adapt Terraform modules to include application-specific resources)

**books-api** — Best-in-class CI/CD and deployment strategy for serverless workloads.
- **Extract**: `pipeline/` buildspec patterns, SAM deployment preferences (canary), X-Ray tracing config
- **Apply to**: aws-microservices (needs CI/CD), local-monolith (needs CI/CD)
- **Effort**: Low (pipeline patterns directly reusable for other Lambda/CDK projects)

## Service Dependency Map

> Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`).
> Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context.
> For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Inferred Dependencies

| Source Service | Target Service | Type | Coupling | Description |
|---------------|---------------|------|----------|-------------|
| unishop-monolith | eks-saas-gitops | shared_infra | Low | EKS platform is the target deployment environment for containerized monolith |
| local-monolith | eks-saas-gitops | shared_infra | Low | EKS platform is the target deployment environment after containerization |
| aws-microservices | eks-saas-gitops | shared_infra | Low | Serverless services may use shared infrastructure patterns |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| eks-saas-gitops | 3 | 0 | 60% | Foundation | 2.93 |
| local-monolith | 0 | 1 | 0% | Leaf | 1.82 |
| unishop-monolith | 0 | 1 | 0% | Leaf | 1.40 |
| aws-microservices | 0 | 1 | 0% | Leaf | 2.40 |
| books-api | 0 | 0 | 0% | Independent | 3.00 |

### Foundation Services (High Fan-In)

- **eks-saas-gitops** (fan-in: 3) — Centralized EKS platform that all containerized workloads will deploy to. Must be stabilized first.

### Circular Dependencies

✅ No circular dependencies detected.

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.

1. **APP-Q3: Async vs Sync Communication** — 2 of 4 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, books-api=4, aws-microservices=4
   - **Affected Services**: local-monolith, unishop-monolith
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

2. **APP-Q4: Long-Running Process Handling** — 2 of 4 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, books-api=4, aws-microservices=4
   - **Affected Services**: local-monolith, unishop-monolith
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

3. **APP-Q5: API Versioning Strategy** — 4 of 4 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, books-api=1, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Define API versioning standard (URL-path: /v1/). All new APIs must be versioned. Critical for agent tool invocation stability.

4. **DATA-Q1: Unstructured Data Storage** — 2 of 4 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, books-api=4, aws-microservices=4
   - **Affected Services**: local-monolith, unishop-monolith
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

5. **INF-Q4: Async Messaging and Streaming** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=4, books-api=4, aws-microservices=4
   - **Affected Services**: local-monolith, unishop-monolith
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

6. **INF-Q8: Backup and Recovery** — 3 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=3, unishop-monolith=1, eks-saas-gitops=3, books-api=1, aws-microservices=1
   - **Affected Services**: unishop-monolith, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

7. **INF-Q11: CI/CD Automation** — 3 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=3, books-api=4, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Establish CI/CD pipelines for all services. Adopt GitOps (ArgoCD/Flux) for container workloads, CDK Pipelines for serverless. Use books-api pipeline as blueprint.

8. **OPS-Q1: Distributed Tracing** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=1, books-api=4, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, aws-microservices
   - **Portfolio-Level Recommendation**: Deploy ADOT/X-Ray across all services. Standardize on OpenTelemetry for cross-service trace correlation.

9. **OPS-Q2: SLO Definitions** — 3 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=2, books-api=2, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

10. **OPS-Q3: Business Metrics** — 5 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=1, books-api=1, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Define portfolio-wide business metrics standard. Implement CloudWatch Embedded Metric Format (EMF) across all services.

11. **OPS-Q4: Anomaly Detection** — 3 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=2, books-api=2, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

12. **OPS-Q5: Deployment Strategy** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=2, unishop-monolith=1, eks-saas-gitops=3, books-api=4, aws-microservices=1
   - **Affected Services**: unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

13. **OPS-Q6: Integration Testing** — 3 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=2, books-api=4, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Establish integration testing standards. Require automated tests before any deployment. Use books-api test patterns as reference.

14. **OPS-Q7: Incident Response Automation** — 5 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=1, books-api=1, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Create shared runbook templates. Implement SSM Automation documents for common failure scenarios.

15. **OPS-Q8: Observability Ownership** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=2, books-api=1, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

16. **OPS-Q9: Resource Tagging** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=2, unishop-monolith=1, eks-saas-gitops=2, books-api=2, aws-microservices=1
   - **Affected Services**: unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

17. **SEC-Q3: API Authentication** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=2, unishop-monolith=1, eks-saas-gitops=3, books-api=3, aws-microservices=1
   - **Affected Services**: unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

18. **SEC-Q4: Centralized Identity** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=2, eks-saas-gitops=2, books-api=3, aws-microservices=1
   - **Affected Services**: local-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

19. **SEC-Q5: Secrets Management** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=3, books-api=4, aws-microservices=4
   - **Affected Services**: local-monolith, unishop-monolith
   - **Portfolio-Level Recommendation**: Migrate all secrets to AWS Secrets Manager with automated rotation. Remove plaintext credentials from all repositories.

20. **SEC-Q6: Compute Hardening** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=2, unishop-monolith=1, eks-saas-gitops=2, books-api=3, aws-microservices=1
   - **Affected Services**: unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Address this gap across all affected services as part of Phase 0 cross-cutting foundation work.

21. **SEC-Q7: Application Security Pipeline** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith=1, unishop-monolith=1, eks-saas-gitops=3, books-api=1, aws-microservices=1
   - **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Implement centralized security scanning pipeline. Add Dependabot/Snyk for dependencies, Semgrep for SAST, and container scanning as CI gates.


### 💡 Improvement Opportunities

> Criteria scoring < 3 in at least **max(3, 33% of applicable repos)**. Important but not blocking.

1. **APP-Q1: Programming Languages** — 3 of 4 applicable services score < 3
   - **Score Distribution**: local-monolith=2, unishop-monolith=2, books-api=3, aws-microservices=2
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Upgrade EOL runtimes. Target Node.js 20+ for TypeScript services. Evaluate language consolidation during decomposition.

2. **APP-Q6: Service Discovery** — 4 of 4 applicable services score < 3
   - **Score Distribution**: local-monolith=2, unishop-monolith=2, books-api=2, aws-microservices=2
   - **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Implement service discovery via API Gateway service catalog and Cloud Map. Publish OpenAPI specs for all APIs.

3. **DATA-Q2: Unified Data Access Layer** — 3 of 4 applicable services score < 3
   - **Score Distribution**: local-monolith=1, unishop-monolith=3, books-api=2, aws-microservices=2
   - **Affected Services**: local-monolith, books-api, aws-microservices
   - **Portfolio-Level Recommendation**: Implement repository/DAO pattern for all data access. Centralize DynamoDB client configuration.

4. **INF-Q3: Workflow Orchestration** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith=2, unishop-monolith=2, eks-saas-gitops=3, books-api=4, aws-microservices=2
   - **Affected Services**: local-monolith, unishop-monolith, aws-microservices
   - **Portfolio-Level Recommendation**: Introduce Step Functions for multi-step workflows. eks-saas-gitops Argo Workflows pattern can serve as reference for container workloads.

5. **INF-Q7: Auto-Scaling** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith=2, unishop-monolith=1, eks-saas-gitops=3, books-api=2, aws-microservices=3
   - **Affected Services**: local-monolith, unishop-monolith, books-api
   - **Portfolio-Level Recommendation**: Implement auto-scaling across all services. Use Karpenter for EKS, DynamoDB on-demand or auto-scaling, App Runner auto-scaling.

### 🔗 Infrastructure Cross-References

> The following application repo findings may be mitigated by capabilities in
> infrastructure-only or deployment-config repos in this portfolio. Individual
> scores are unchanged — verify that the infra repo's configuration covers the
> application repo's deployment.

| App Repo | Question | App Score | Potentially Covered By | Infra Repo Score | Status |
|----------|----------|-----------|------------------------|------------------|--------|
| unishop-monolith | INF-Q1 | 1 | eks-saas-gitops (infrastructure-only) | 4 | Verify |
| unishop-monolith | INF-Q2 | 1 | eks-saas-gitops (infrastructure-only) | 4 | Verify |
| unishop-monolith | INF-Q5 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| unishop-monolith | INF-Q7 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| unishop-monolith | INF-Q8 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| unishop-monolith | INF-Q10 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| unishop-monolith | INF-Q11 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| local-monolith | INF-Q11 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| aws-microservices | INF-Q11 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| unishop-monolith | OPS-Q5 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| aws-microservices | OPS-Q5 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| books-api | INF-Q8 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |
| aws-microservices | INF-Q8 | 1 | eks-saas-gitops (infrastructure-only) | 3 | Verify |

**Summary**: 13 application repo findings across 7 questions may be mitigated by infrastructure capabilities in eks-saas-gitops. These represent potential false positives at the portfolio level — the capability exists but in a separate repository.

> ⚠️ **Action Required**: For each "Verify" row, confirm that the infrastructure repo's
> IaC/config actually covers the application repo's deployment environment. If confirmed,
> the application repo's finding is a false positive at the portfolio level (though the
> individual repo score remains unchanged for traceability).

## Portfolio Modernization Roadmap

> Dependency-aware phased roadmap with fixed phase names. Services are ordered
> by dependency graph position, then by priority (P0 → P1 → P2), then by score.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services before downstream dependents
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Independent services can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, break circular dependencies, and address portfolio-wide blockers.

**Cross-Cutting Activities:**
- Establish CI/CD pipeline standards (INF-Q11 blocker: 3 of 5 services)
- Implement centralized secrets management via AWS Secrets Manager (SEC-Q5 blocker)
- Deploy security scanning pipeline — Dependabot, Semgrep, container scanning (SEC-Q7 blocker: 4 of 5 services)
- Define API versioning standard (/v1/) for all services (APP-Q5 blocker: 4 of 4 application repos)
- Deploy ADOT/OpenTelemetry distributed tracing across portfolio (OPS-Q1 blocker: 4 of 5 services)
- Define business metrics standard with CloudWatch EMF (OPS-Q3 blocker: all services)
- Create shared runbook templates for incident response (OPS-Q7 blocker: all services)

**Organizational Enablers:**
- Training: Terraform, EKS operations, GitOps (ArgoCD/Flux), CI/CD automation
- Tooling: Standardize on Terraform for infra, CDK for app IaC, GitHub Actions/CodePipeline for CI/CD
- Standards: API versioning, tagging, observability ownership, security scanning gates

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize foundation services and establish patterns.

**Services in Scope:**

1. **eks-saas-gitops** (P1, Score: 2.93 / 4.0)
   - Current State: EKS platform with Terraform, Flux CD, Karpenter. Missing tracing, audit logging, quality gates.
   - Target State: Production-ready EKS platform with full observability and security controls
   - Key Activities:
     - Add CloudTrail and EKS control plane logging (SEC-Q1)
     - Deploy ADOT DaemonSet for distributed tracing (OPS-Q1)
     - Add terraform validate/plan and container scanning to CI (INF-Q11, SEC-Q7)
     - Implement integration tests for tenant onboarding (OPS-Q6)
   - Dependencies: None (foundation service)
   - Blocks: unishop-monolith, local-monolith, aws-microservices
   - Estimated Effort: Medium

2. **aws-microservices** (P0, Score: 2.40 / 4.0)
   - Current State: Event-driven serverless microservices with CDK IaC but no CI/CD, no tests, no auth, EOL runtime
   - Target State: Production-grade serverless platform with CI/CD, canary deployments, observability
   - Key Activities:
     - Implement CI/CD pipeline with CDK Pipelines (INF-Q11)
     - Upgrade Node.js 14.x to 20.x (APP-Q1)
     - Add Cognito authorizers to API Gateway (SEC-Q3)
     - Enable X-Ray tracing on all Lambda functions (OPS-Q1)
     - Add integration tests (OPS-Q6)
     - Implement canary deployments (OPS-Q5)
   - Dependencies: None (independent serverless)
   - Blocks: None
   - Estimated Effort: Medium

**Expected Outcomes:**
- EKS platform hardened and ready for application onboarding
- aws-microservices production-ready with full CI/CD and observability
- Reference patterns established for remaining services

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize monolith services that depend on Phase 1 services. Replicate proven patterns.

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.40 / 4.0)
   - Current State: Legacy Java Spring Boot monolith on EC2, no IaC, no CI/CD, self-managed MySQL, plaintext secrets
   - Target State: Containerized on EKS with Aurora MySQL, CI/CD, progressive delivery
   - Key Activities:
     - Containerize Spring Boot app (create Dockerfile, push to ECR)
     - Deploy on EKS using eks-saas-gitops platform (INF-Q1)
     - Migrate MySQL to Aurora MySQL (INF-Q2)
     - Define all infrastructure in Terraform (INF-Q10)
     - Implement GitOps CD with ArgoCD/Flux (INF-Q11)
     - Remove plaintext credentials, adopt Secrets Manager (SEC-Q5)
     - Begin Strangler Fig decomposition: extract basket/order service
   - Dependencies: eks-saas-gitops (Phase 1)
   - Blocks: None
   - Estimated Effort: High

2. **local-monolith** (P0, Score: 1.82 / 4.0)
   - Current State: PHP monolith on App Runner with CloudFormation, RDS MySQL. No CI/CD, no tests, plaintext secrets.
   - Target State: Decomposed microservices on EKS with Terraform, CI/CD, observability
   - Key Activities:
     - Implement CI/CD pipeline (INF-Q11)
     - Remove plaintext credentials, adopt Secrets Manager (SEC-Q5)
     - Add integration tests for critical APIs (OPS-Q6)
     - Introduce EventBridge for async domain events (INF-Q4)
     - Begin Strangler Fig decomposition: extract inventory service for agent access
     - Migrate to EKS from App Runner for consistency with platform
   - Dependencies: eks-saas-gitops (Phase 1)
   - Blocks: None
   - Estimated Effort: High

**Parallel Tracks:**
- unishop-monolith and local-monolith can be modernized concurrently (no mutual dependencies)

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize services, implement advanced capabilities, continuous improvement.

**Services in Scope:**

1. **books-api** (P1, Score: 3.00 / 4.0)
   - Current State: Well-architected serverless API with full CI/CD and canary deployments. Gaps in security scanning, backup, incident response.
   - Target State: Fully mature serverless service with hardened security pipeline and operational excellence
   - Key Activities:
     - Enable DynamoDB PITR (INF-Q8)
     - Add security scanning to pipeline — Dependabot, Semgrep (SEC-Q7)
     - Migrate AWS SDK v2 to v3 (APP-Q1)
     - Add API versioning /v1/ (APP-Q5)
     - Define formal SLOs and business metrics (OPS-Q2, OPS-Q3)
   - Dependencies: None
   - Estimated Effort: Low

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6 months (with 2 parallel tracks in Phase 2)

### Target State Architecture

> After roadmap completion, the portfolio looks like this. Derived from triggered pathways,
> preferences, resolved cross-cutting blockers, and blueprint candidates.

- **Compute:** All services containerized on EKS with Karpenter autoscaling (monoliths) or Lambda serverless (books-api, aws-microservices). No EC2 instances in production.
- **Data:** Aurora MySQL for relational workloads (migrated from self-managed MySQL). DynamoDB for NoSQL. All databases fully managed with PITR and encryption.
- **Observability:** Centralized tracing via ADOT/X-Ray across all services. CloudWatch metrics with EMF. Formal SLOs with error budgets. Grafana dashboards for EKS workloads.
- **CI/CD:** GitOps (Flux CD/ArgoCD) for EKS workloads. CDK Pipelines for serverless. All pipelines include security scanning, integration tests, and canary deployments.
- **Security:** Centralized identity via Cognito. All secrets in Secrets Manager with rotation. Security scanning (SAST, dependency, container) in every pipeline. WAF on all public APIs.

## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 2 | 40% | High | High |
| Move to Containers | 1 | 20% | Medium | Medium |
| Move to Open Source | 0 | 0% | — | — |
| Move to Managed Databases | 1 | 20% | High | Medium |
| Move to Managed Analytics | 0 | 0% | — | — |
| Move to Modern DevOps | 3 | 60% | High | Medium |
| Move to AI | 0 | 0% | — | — |

### Portfolio Pathway Aggregation

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | local-monolith, unishop-monolith | books-api, aws-microservices | eks-saas-gitops |
| Move to Containers | unishop-monolith | local-monolith, books-api, aws-microservices | eks-saas-gitops |
| Move to Open Source | — | local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices | — |
| Move to Managed Databases | unishop-monolith | local-monolith, eks-saas-gitops, books-api, aws-microservices | — |
| Move to Managed Analytics | — | local-monolith, unishop-monolith, books-api, aws-microservices | eks-saas-gitops |
| Move to Modern DevOps | local-monolith, unishop-monolith, aws-microservices | eks-saas-gitops, books-api | — |
| Move to AI | — | local-monolith, unishop-monolith, books-api, aws-microservices | eks-saas-gitops |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| local-monolith | ✅ | — | — | — | — | ✅ | — |
| unishop-monolith | ✅ | ✅ | — | ✅ | — | ✅ | — |
| eks-saas-gitops | N/A | N/A | — | — | N/A | — | N/A |
| books-api | — | — | — | — | — | — | — |
| aws-microservices | — | — | — | — | — | ✅ | — |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is a prerequisite for Move to AI (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps + Move to Containers (infrastructure foundation)
- **Track 2**: Move to Managed Databases + Move to Cloud Native (after Track 1 foundation)

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: local-monolith, unishop-monolith, aws-microservices (3 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q11 score 1: affects 3 services (no CI/CD)
  - OPS-Q5 score 1: affects 2 services (no deployment strategy)
  - OPS-Q6 score 1: affects 3 services (no integration tests)
- **Representative AWS Services**: GitHub Actions, Terraform, ArgoCD, AWS CodePipeline, CDK Pipelines, Amazon ECR
- **Key Activities**:
  1. Establish CI/CD pipelines for all affected services
  2. Implement GitOps for EKS workloads (ArgoCD/Flux)
  3. Add security scanning and integration test gates
  4. Deploy canary/progressive delivery patterns
- **Cross-Service Synergies**: eks-saas-gitops Flux CD pattern reusable; books-api CodePipeline pattern reusable
- **Estimated Effort**: Medium across 3 services
- **Roadmap Phase Alignment**: Phase 0–1
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to Cloud Native

- **Services Affected**: local-monolith, unishop-monolith (2 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - APP-Q2 score < 3: affects 2 services (monolith architecture)
  - APP-Q3 score 1: affects 2 services (all synchronous)
  - APP-Q4 score 1: affects 2 services (no async processing)
- **Representative AWS Services**: Amazon EKS, Amazon API Gateway, Amazon EventBridge, AWS Step Functions, Amazon Aurora
- **Key Activities**:
  1. Containerize monoliths and deploy on EKS
  2. Apply Strangler Fig decomposition pattern
  3. Introduce EventBridge for domain events
  4. Extract inventory and order services for agent access
- **Cross-Service Synergies**: Both monoliths follow same decomposition pattern; shared EKS platform
- **Estimated Effort**: High across 2 services
- **Roadmap Phase Alignment**: Phase 2–3
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Containers

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q1 score 1: raw EC2 compute with no containerization
- **Representative AWS Services**: Amazon EKS, Amazon ECR, Karpenter
- **Key Activities**:
  1. Create Dockerfile for Spring Boot JAR
  2. Deploy to EKS using eks-saas-gitops platform
  3. Configure Karpenter for autoscaling
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon EKS

#### Move to Managed Databases

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q2 score 1: self-managed MySQL
  - DATA-Q3 score 1: no version pinning or lifecycle management
- **Representative AWS Services**: Amazon Aurora MySQL, AWS DMS
- **Key Activities**:
  1. Provision Aurora MySQL cluster in Terraform
  2. Migrate data via AWS DMS with minimal downtime
  3. Enable Multi-AZ, automated backups, encryption
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to AI

- **Services Affected**: None (0 total)
- **Portfolio Priority**: —
- **Aggregation**: Move to AI: Triggered in 0 of 5 services (4 services had no AI intent in context — pathway correctly suppressed)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): local-monolith, unishop-monolith, books-api, aws-microservices
  - Already present (AI frameworks detected): —
- **Note**: The portfolio context mentions building a "customer support agent" but the individual service reports did not detect AI-specific signal terms (agentic, LLM, Bedrock, generative AI). The agent integration use case may warrant re-evaluation with explicit AI intent in service contexts.

### Heavy Modernization Candidates

> These services trigger 4+ modernization pathways and represent concentrated modernization
> debt. They require dedicated sprint capacity or a focused modernization initiative.

| Service | Pathways Triggered | Pathway Load | Cross-Reference |
|---------|---------------------|--------------|-----------------|
| unishop-monolith | Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps | 4 | Risk register: high-risk dependency |

## Integration Opportunities

### Shared Service Extraction

**Opportunity: Centralized Identity Service**
- **Current State**: Authentication fragmented — local-monolith uses PHP sessions, books-api uses Cognito, unishop-monolith has disabled OAuth2, aws-microservices has none
- **Proposed Solution**: Amazon Cognito User Pool as centralized IdP for all services. API Gateway Cognito authorizers for consistent auth.
- **Benefits**: Single sign-on, centralized user management, consistent authorization, agent-friendly OAuth2 tokens
- **Effort**: Medium
- **Priority**: High

**Opportunity: Shared Observability Platform**
- **Current State**: Only books-api has X-Ray tracing. No cross-service correlation. No shared dashboards.
- **Proposed Solution**: Deploy ADOT as DaemonSet on EKS + ADOT Lambda layer for serverless. Centralize in CloudWatch with cross-service trace maps.
- **Benefits**: End-to-end request tracing across agent→service calls, unified dashboards, faster incident resolution
- **Effort**: Medium
- **Priority**: High

### Event-Driven Architecture

**Opportunity: Cross-Service Domain Events**
- **Current State**: local-monolith and unishop-monolith have all synchronous internal communication
- **Proposed Solution**: Amazon EventBridge as central event bus. Publish domain events (order.placed, inventory.restocked, return.initiated) for agent and service consumption.
- **Benefits**: Decoupled services, agent can subscribe to events, resilient to individual service failures
- **Effort**: High

### API Gateway Consolidation

- **Current State**: aws-microservices and books-api each have separate API Gateway instances
- **Proposed Solution**: Unified API Gateway with consistent auth, rate limiting, and API versioning. Single entry point for the customer support agent.
- **Benefits**: Consistent auth, rate limiting, single agent endpoint, reduced cost

### Observability Unification

- **Current State**: eks-saas-gitops uses Prometheus/Kubecost, books-api uses CloudWatch, others have nothing
- **Proposed Solution**: CloudWatch as unified platform with ADOT for trace collection. Prometheus metrics fed to CloudWatch via AMP.
- **Benefits**: Unified dashboards, cross-service correlation, single pane of glass

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| unishop-monolith failure affects platform (score 1.40, low resilience) | High | Medium | 🟠 High | Containerize and add HA before decomposition | Phase 2 |
| Plaintext secrets in 2 repos (local-monolith, unishop-monolith) | High | High | 🔴 Critical | Immediate migration to Secrets Manager | Phase 0 |
| EOL Node.js 14.x in aws-microservices (no security patches) | High | Medium | 🟠 High | Upgrade to Node.js 20.x in Phase 1 | Phase 1 |
| No integration tests in 3 services (regression risk during modernization) | High | High | 🔴 Critical | Add integration tests before any decomposition | Phase 0-1 |
| DynamoDB data loss (no PITR in books-api, aws-microservices) | Medium | High | 🟠 High | Enable PITR immediately | Phase 1 |
| No distributed tracing (4 of 5 services) blocks cross-service debugging | Medium | Medium | 🟡 Medium | Deploy ADOT in Phase 1 | Phase 1 |
| Open API endpoints in aws-microservices (no auth) | High | Medium | 🟠 High | Add Cognito authorizers | Phase 1 |

### Single Points of Failure

- **eks-saas-gitops** (blast radius: 60%) — Single NAT Gateway is a SPOF for outbound connectivity. Deploy NAT Gateways per AZ.

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + service teams (21 cross-cutting blockers warrant centralized platform investment)

**Platform Team**:
- Responsibilities: EKS platform (eks-saas-gitops), CI/CD templates, observability platform, security pipeline
- Skills Required: Terraform, EKS operations, GitOps (Flux/ArgoCD), CloudWatch/ADOT, security scanning

**Service Teams**:
- Responsibilities: Service-specific modernization, monolith decomposition, API development
- Skills Required: Java (Spring Boot), PHP, TypeScript/Node.js, DynamoDB, Aurora MySQL, API Gateway

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| Terraform | IaC standardization, EKS platform | Partial (eks-saas-gitops) | High |
| EKS/Kubernetes | Container workloads | Partial (eks-saas-gitops) | High |
| GitOps (ArgoCD/Flux) | Deployment automation | Partial (Flux in eks-saas-gitops) | High |
| CI/CD Pipeline Design | All services | Partial (books-api only) | High |
| Distributed Tracing (ADOT/X-Ray) | Observability | No (only books-api) | Medium |
| DMS/Database Migration | unishop-monolith Aurora migration | No | Medium |
| Microservices Decomposition | Monolith decomposition | No | High |

### Training Recommendations

- Phase 0: Terraform, CI/CD automation, security scanning (entire team)
- Phase 1: EKS operations, GitOps, distributed tracing (platform team)
- Phase 2: Microservices patterns (Strangler Fig), DMS migration, Aurora (service teams)

### External Support

- **AWS Professional Services**: Recommended for Aurora MySQL migration (high-risk data migration) and initial EKS platform hardening
- **Consulting Partners**: Consider for CI/CD pipeline implementation across 3 services simultaneously

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Experience-Based Acceleration | EBA | 3 repos with triggered pathways AND score < 3.0 | local-monolith (2 pathways, 1.82), unishop-monolith (4 pathways, 1.40), aws-microservices (1 pathway, 2.40) | Request EBA engagement via AWS Solutions Architect |

### Program Details

**Experience-Based Acceleration (EBA)**

- **Why recommended**: 3 of 5 services have at least one triggered modernization pathway AND an overall score below 3.0, indicating significant modernization work ahead. The portfolio has 4 distinct triggered pathways (Move to Modern DevOps, Move to Cloud Native, Move to Containers, Move to Managed Databases) spanning infrastructure, application, and data layers.
- **What it provides**: AWS-led immersive workshops focused on the most prevalent pathways (Modern DevOps and Cloud Native). Hands-on guidance for implementation patterns, architecture reviews, and best-practice adoption.
- **Suggested timing**: Phase 0–1 (foundational activities). EBA can accelerate CI/CD establishment and initial containerization.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

## Recommended Self-Paced Learning Materials

> Relevant modules based on portfolio-wide triggered pathways and skill gaps.

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA

**Module 3: Move to Containers with Amazon EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 2
- **Finding**: 4 different IaC approaches across 5 services (Terraform, CDK, SAM/CloudFormation, none). No single standard covers >50% of the portfolio.
- **Evidence**: eks-saas-gitops uses Terraform, books-api uses SAM+CDK, aws-microservices uses CDK, local-monolith uses CloudFormation, unishop-monolith has no IaC.
- **Recommendation**: Standardize on Terraform for infrastructure provisioning (aligned with preferences) and CDK for application-level resources. Migrate local-monolith CloudFormation to Terraform.

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: Each service has independent or no observability. Only books-api has X-Ray tracing. No cross-service correlation, no shared dashboards, no unified logging strategy.
- **Evidence**: books-api has X-Ray enabled; eks-saas-gitops has Prometheus/Kubecost; others have nothing.
- **Recommendation**: Deploy ADOT/X-Ray as shared observability platform. Standardize on OpenTelemetry SDK instrumentation. Create cross-service CloudWatch dashboards.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 4
- **Finding**: No circular dependencies detected. Service relationships are hierarchical (infrastructure → application) with no bidirectional coupling.
- **Evidence**: eks-saas-gitops is a pure infrastructure provider. Application services do not depend on each other.
- **Recommendation**: Maintain this healthy dependency structure. When decomposing monoliths, use EventBridge for async communication to avoid introducing cycles.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 2
- **Finding**: High diversity with no consistent mapping to service archetypes — 4+ languages (PHP, Java, TypeScript, Python/HCL), 4+ IaC tools, 2 database engines, 4 compute patterns. This represents accidental sprawl rather than intentional polyglot.
- **Evidence**: Each service uses a different technology combination. No standardization effort visible.
- **Recommendation**: Consolidate on TypeScript/Node.js for new application services (2 services already use it). Standardize Terraform for infra, CDK for app IaC. Target Aurora MySQL + DynamoDB for data.

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: Each service manages security independently. No centralized security scanning, no shared WAF, no unified vulnerability management. SEC-Q7 is a foundational blocker (4 of 5 services score 1).
- **Evidence**: No shared Dependabot config, no centralized SAST, no shared WAF WebACL, no unified secrets management.
- **Recommendation**: Implement centralized security scanning pipeline in Phase 0. Shared WAF via API Gateway. Unified Secrets Manager configuration. Centralize vulnerability tracking.

## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| unishop-monolith | application | P0 | 1.40 | 1.09 | 1.50 | 2.25 | 1.17 | 1.00 | 4 of 7 | 2 |
| local-monolith | application | P0 | 1.82 | 2.64 | 1.33 | 2.25 | 1.67 | 1.22 | 2 of 7 | 2 |
| aws-microservices | application | P0 | 2.40 | 2.82 | 2.83 | 3.50 | 1.83 | 1.00 | 1 of 7 | 1 |
| eks-saas-gitops | infrastructure-only | P1 | 2.93 | 3.09 | N/A | 4.00 | 2.57 | 2.11 | 0 of 7 | 1 |
| books-api | application | P1 | 3.00 | 3.36 | 3.00 | 3.50 | 2.83 | 2.33 | 0 of 7 | 3 |

### Individual Service Details

#### unishop-monolith

- **Overall Score**: 1.40 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-05-18
- **Category Scores**: INF: 1.09, APP: 1.50, DATA: 2.25, SEC: 1.17, OPS: 1.00
- **Top Gaps**: INF-Q10 (score 1 — zero IaC), INF-Q11 (score 1 — no CI/CD), SEC-Q5 (score 1 — plaintext credentials)
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**: Containerize on EKS, migrate to Aurora MySQL, implement CI/CD with GitOps, remove plaintext secrets
- **Roadmap Phase**: Phase 2

#### local-monolith

- **Overall Score**: 1.82 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-05-18
- **Category Scores**: INF: 2.64, APP: 1.33, DATA: 2.25, SEC: 1.67, OPS: 1.22
- **Top Gaps**: APP-Q2 (score 1 — tight monolith), INF-Q11 (score 1 — no CI/CD), SEC-Q5 (score 1 — plaintext secrets)
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps
- **Key Recommendations**: Implement CI/CD, decompose via Strangler Fig (extract inventory service first), remove plaintext secrets
- **Roadmap Phase**: Phase 2

#### aws-microservices

- **Overall Score**: 2.40 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-05-18
- **Category Scores**: INF: 2.82, APP: 2.83, DATA: 3.50, SEC: 1.83, OPS: 1.00
- **Top Gaps**: INF-Q11 (score 1 — no CI/CD), OPS-Q5 (score 1 — no deployment strategy), SEC-Q3 (score 1 — open APIs)
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**: Implement CI/CD pipeline, add authentication, upgrade Node.js runtime, add observability
- **Roadmap Phase**: Phase 1

#### eks-saas-gitops

- **Overall Score**: 2.93 / 4.0
- **Repository Type**: infrastructure-only
- **Priority**: P1
- **Assessment Date**: 2025-05-18
- **Category Scores**: INF: 3.09, APP: N/A, DATA: 4.00, SEC: 2.57, OPS: 2.11
- **Top Gaps**: OPS-Q1 (score 1 — no tracing), OPS-Q3 (score 1 — no business metrics), SEC-Q1 (score 2 — no CloudTrail)
- **Triggered Pathways**: None
- **Key Recommendations**: Add CloudTrail, deploy ADOT for tracing, add quality gates to CI, implement integration tests
- **Roadmap Phase**: Phase 1

#### books-api

- **Overall Score**: 3.00 / 4.0
- **Repository Type**: application
- **Priority**: P1
- **Assessment Date**: 2026-05-18
- **Category Scores**: INF: 3.36, APP: 3.00, DATA: 3.50, SEC: 2.83, OPS: 2.33
- **Top Gaps**: SEC-Q7 (score 1 — no security scanning), INF-Q8 (score 1 — no backup), OPS-Q3 (score 1 — no business metrics)
- **Triggered Pathways**: None
- **Key Recommendations**: Add security scanning to pipeline, enable DynamoDB PITR, add API versioning, define SLOs
- **Roadmap Phase**: Phase 3

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | local-monolith | monolith/modernization-readiness-analysis/local-monolith-mod-report.json | 2026-05-18 | application | 1.82 |
| 2 | unishop-monolith | services/unishop-monolith-to-microservices/MonoToMicroLegacy/modernization-readiness-analysis/unishop-monolith-mod-report.json | 2026-05-18 | application | 1.40 |
| 3 | eks-saas-gitops | services/eks-saas-gitops/modernization-readiness-analysis/eks-saas-gitops-mod-report.json | 2025-05-18 | infrastructure-only | 2.93 |
| 4 | books-api | services/books-api/modernization-readiness-analysis/books-api-mod-report.json | 2026-05-18 | application | 3.00 |
| 5 | aws-microservices | services/aws-microservices/modernization-readiness-analysis/aws-microservices-mod-report.json | 2026-05-18 | application | 2.40 |