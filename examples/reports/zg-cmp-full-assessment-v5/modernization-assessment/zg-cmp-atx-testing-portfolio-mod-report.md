# Portfolio Modernization Assessment Report

**Date**: 2026-05-01
**Services Assessed**: 34
**Portfolio Context**: 34 open-source project mirrors for ATX TD validation across multiple languages, architectures, and domains.
**Technology Preferences**: Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock; Avoid: self-managed-kafka, self-managed-kubernetes, oracle

---

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 1.99 / 4.0 |
| Score Range | 1.51 – 2.78 |
| Score Standard Deviation | 0.27 |
| Highest Scoring Service | serverless--serverless (2.78) |
| Lowest Scoring Service | akveo--ngx-admin (1.51) |
| Pathways Triggered (portfolio-wide) | 6 of 7 |
| Cross-Cutting Foundational Blockers | 31 |
| Cross-Cutting Improvement Opportunities | 5 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 1 | 3% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 33 | 97% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 0 | 0% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 1.46 | 1.13 | 2.00 | 0 |
| Application Architecture (APP) | 2.73 | 1.75 | 3.75 | 0 |
| Data Platform (DATA) | 2.64 | 1.75 | 3.75 | 0 |
| Security Baseline (SEC) | 1.61 | 1.00 | 2.67 | 0 |
| Operations & Observability (OPS) | 1.53 | 1.00 | 2.50 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 16 | 47% |
| monorepo | 18 | 53% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-05-01 |
| total_services | 34 |
| portfolio_score | 1.99 |
| score_range_min | 1.51 |
| score_range_max | 2.78 |
| mature_services | 0 |
| partial_services | 1 |
| needs_work_services | 33 |
| not_ready_services | 0 |
| pathways_triggered | 6 |
| foundational_blockers | 31 |
| improvement_opportunities | 5 |
| category_inf | 1.46 |
| category_app | 2.73 |
| category_data | 2.64 |
| category_sec | 1.61 |
| category_ops | 1.53 |
| portfolio_level_avg | 1.80 |

---

## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| Java | 17 | 50% |
| JavaScript | 7 | 21% |
| TypeScript | 6 | 18% |
| C# | 5 | 15% |
| Python | 5 | 15% |
| HTML/CSS | 1 | 3% |

> Note: Some services use multiple languages. Java and JavaScript/TypeScript dominate the portfolio.

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| PostgreSQL | Relational | 11 | Self-managed |
| Redis | Cache | 7 | Self-managed |
| MySQL | Relational | 5 | Self-managed |
| SQLite | Relational (embedded) | 5 | Self-managed |
| MongoDB | NoSQL | 3 | Self-managed |
| Cassandra | NoSQL | 3 | Self-managed |
| Elasticsearch | Search / Analytics | 2 | Self-managed |
| MariaDB | Relational | 2 | Self-managed |
| OpenSearch | Search / Analytics | 2 | Self-managed |
| H2 | Relational (in-memory) | 1 | Self-managed |

**Database Distribution**: 0 managed, 17 self-managed services with databases, 0 commercial (Oracle/SQL Server detected in 0 deployed workloads), 17 open source

> ⚠️ **All databases are self-managed.** No service uses AWS managed database services (RDS, Aurora, DynamoDB, ElastiCache, DocumentDB). This is a portfolio-wide gap and a key driver for the Move to Managed Databases pathway. Aligns with preference for Aurora and DynamoDB.

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| No managed compute (local/bare-metal) | 32 | 94% |
| Containers (Docker available) | 21 | 62% |
| Serverless (Lambda-oriented tools) | 2 | 6% |

> ⚠️ **94% of services have no managed compute** (INF-Q1 score 1). While 21 services have Dockerfiles, none use ECS, EKS, or Fargate in production. The Serverless Framework (serverless--serverless) and Zappa (zappa--Zappa) are Lambda deployment tools but are themselves not deployed on managed compute.

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| None (no IaC) | IaC | 24 |
| Docker Compose | IaC (partial) | 8 |
| Serverless Framework YAML | IaC (partial) | 2 |
| GitHub Actions | CI/CD | 33 |
| Azure Pipelines | CI/CD | 4 |
| CircleCI | CI/CD | 2 |
| Travis CI | CI/CD | 1 |
| Jenkins | CI/CD | 1 |

> ⚠️ **71% of services have zero IaC.** GitHub Actions is the dominant CI/CD tool (97% adoption), but pipelines generally cover build+test only — not deployment.

### Standardization Opportunities

- **CI/CD Standardization**: GitHub Actions covers 33/34 services — standardize on GitHub Actions as the CI/CD platform across the portfolio.
- **IaC Gap**: 24 services have no IaC at all. Standardize on a single IaC tool (recommend AWS CDK or Terraform, both preferred-stack aligned) for all new infrastructure.
- **Database Consolidation**: 10 distinct database engines across the portfolio. Consolidate to Aurora PostgreSQL (preferred) for relational workloads, DynamoDB (preferred) for key-value/NoSQL, and ElastiCache for Redis caching.
- **Container Standardization**: 21 services have Docker definitions but none use managed container orchestration. Standardize on EKS (preferred) for container workloads.
- **Language Diversity**: 4 primary languages (Java, JS/TS, C#, Python). Technology diversity score = 4 languages / 34 services = 0.12 (moderate diversity). No immediate consolidation needed but consider platform teams per language ecosystem.

---

## Service Dependency Map

> Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`). This portfolio consists of 34 independent open-source projects with no direct inter-service dependencies. Inferred dependencies reflect only shared architectural patterns, not runtime communication.

### Inferred Dependency Clusters

The following service clusters share architectural patterns and technology stacks but do not have runtime dependencies:

**Cluster 1: *arr Suite** (Sonarr, Radarr, Lidarr, Prowlarr)
- **Shared Pattern**: C# / .NET, SQLite/PostgreSQL, ASP.NET Core REST API, NzbDrone shared codebase heritage
- **Type**: shared_infra (common framework and deployment pattern)
- **Coupling**: Low (no runtime communication between services)
- **Note**: These services share code lineage and could benefit from shared modernization templates

**Cluster 2: Scality Storage** (scality--backbeat, scality--cloudserver)
- **Shared Pattern**: Node.js, Docker Compose, Kafka-based messaging, S3-compatible storage
- **Type**: shared_infra (shared Kafka infrastructure, backbeat processes events from cloudserver)
- **Coupling**: Medium (backbeat consumes events related to cloudserver operations)

**Cluster 3: Angular Frontend Templates** (akveo--ngx-admin, coreui--coreui-free-angular-admin-template, realworld-apps--angular-realworld-example-app)
- **Shared Pattern**: TypeScript/Angular, SPA architecture, no backend
- **Type**: shared_infra (common deployment pattern opportunity)
- **Coupling**: Low (independent projects)

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| All 34 services | 0 | 0 | 3% | Independent | 1.51–2.78 |

> Since these are independent open-source projects with no runtime dependencies, all services have fan-in=0, fan-out=0, and blast radius of 1/34 (3%). No foundation services or leaf services are identified.

### Circular Dependencies

✅ No circular dependencies detected. All services are independent.

### Critical Path Analysis

No dependency chains exist. All services can be modernized independently and in parallel. The roadmap in Section 5 uses score-based ordering (lowest-scoring services first) rather than dependency-based ordering.

> **Recommendation**: For production portfolios with inter-service communication, add `dependency_overrides` to the portfolio config to enable dependency-aware analysis — including coupling scores, blast radius calculation, circular dependency detection, and dependency-ordered roadmap phasing.

---

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts. Address these first — nothing else matters until these are resolved.

**Infrastructure & DevOps (INF) — 10 Blockers:**

1. **INF-Q7: Multi-AZ / Multi-Region Resilience** — 34 of 34 services score < 2
   - **Score Distribution**: All 34 services score 1
   - **Impact**: No service has multi-AZ or multi-region resilience. Complete absence of high-availability architecture blocks production readiness.
   - **Affected Services**: All 34 services
   - **Portfolio-Level Recommendation**: Establish a shared EKS (preferred) or ECS cluster pattern with multi-AZ deployment built in. Create reusable Terraform/CDK modules for multi-AZ networking and auto-scaling groups.

2. **INF-Q5: Network Security Architecture** — 33 of 34 services score < 2
   - **Score Distribution**: 33 services score 1, 1 service scores 2
   - **Impact**: No VPC design, no security groups, no network segmentation. Blocks secure deployment of any service.
   - **Affected Services**: 33 of 34 services (all except serverless--serverless)
   - **Portfolio-Level Recommendation**: Design a shared VPC architecture with public/private subnets, NAT gateways, and security groups. Use AWS CDK or Terraform to provision as a shared foundation.

3. **INF-Q1: Managed Compute** — 32 of 34 services score < 2
   - **Score Distribution**: 32 services score 1, 2 services score 2
   - **Impact**: No managed compute (EC2, ECS, EKS, Lambda) used. Services run on local machines or bare-metal. Blocks auto-scaling, managed patching, and cost optimization.
   - **Affected Services**: 32 services (all except ToolJet--ToolJet, serverless--serverless)
   - **Portfolio-Level Recommendation**: Establish EKS (preferred) as the standard compute platform. For containerized services (21 have Dockerfiles), create a shared EKS cluster with standard deployment manifests.

4. **INF-Q10: Infrastructure as Code Coverage** — 31 of 34 services score < 2
   - **Score Distribution**: 31 services score 1, 3 services score 2
   - **Impact**: No IaC. All infrastructure is manual (ClickOps) or undefined. Blocks reproducible deployments, disaster recovery, and environment consistency.
   - **Affected Services**: 31 services
   - **Portfolio-Level Recommendation**: Standardize on AWS CDK or Terraform. Create shared IaC templates for common patterns (EKS cluster, Aurora database, API Gateway). Train all teams on IaC fundamentals.

5. **INF-Q6: Container-Readiness / Stateless Design** — 31 of 34 services score < 2
   - **Score Distribution**: 31 services score 1, 3 services score 2
   - **Impact**: Most services lack containerization or stateless design. Blocks migration to EKS/ECS.
   - **Affected Services**: 31 services
   - **Portfolio-Level Recommendation**: Create containerization guides per language (Java, Node.js, Python, C#). Provide Dockerfile templates and multi-stage build patterns.

6. **INF-Q2: Managed Database Services** — 14 of 15 applicable services score < 2
   - **Score Distribution**: 14 services score 1, 1 service scores 2 (19 services N/A — no database)
   - **Impact**: All databases are self-managed. No RDS, Aurora, DynamoDB, or ElastiCache usage. Blocks data platform modernization.
   - **Affected Services**: 14 of 15 database-using services
   - **Portfolio-Level Recommendation**: Migrate to Aurora PostgreSQL (preferred) for relational workloads, DynamoDB (preferred) for key-value/NoSQL. Use AWS DMS for migration.

7. **INF-Q8: Auto-Scaling Configuration** — 10 of 15 applicable services score < 2
   - **Score Distribution**: 10 services score 1, 5 services score 2 (19 services N/A)
   - **Impact**: No auto-scaling. Services cannot handle load spikes or reduce costs during low demand.
   - **Affected Services**: 10 of 15 applicable services
   - **Portfolio-Level Recommendation**: Configure auto-scaling on EKS (preferred) using Horizontal Pod Autoscaler and Cluster Autoscaler.

8. **INF-Q9: Service Mesh / Traffic Management** — 6 of 10 applicable services score < 2
   - **Score Distribution**: 6 services score 1, 4 services score 2 (24 services N/A)
   - **Impact**: No service mesh for traffic management, observability injection, or mutual TLS.
   - **Affected Services**: 6 of 10 applicable services
   - **Portfolio-Level Recommendation**: Evaluate AWS App Mesh or Istio on EKS for services with inter-service communication needs.

9. **INF-Q4: Event-Driven / Messaging Infrastructure** — 4 of 26 applicable services score < 2
   - **Score Distribution**: 4 services score 1, 11 services score 2, 11 services score 3 (8 services N/A)
   - **Impact**: Services with event processing needs lack proper messaging infrastructure.
   - **Affected Services**: 4 of 26 applicable services
   - **Portfolio-Level Recommendation**: Standardize on EventBridge (preferred) for event routing and SQS for message queuing. Avoid self-managed Kafka where possible.

10. **INF-Q3: API Gateway / Load Balancer** — 2 of 17 applicable services score < 2
    - **Score Distribution**: 2 services score 1, 11 services score 2, 4 services score 3 (17 services N/A)
    - **Impact**: Services with API surfaces lack API gateway or load balancer.
    - **Affected Services**: 2 of 17 applicable services
    - **Portfolio-Level Recommendation**: Standardize on Amazon API Gateway (preferred) for all API surfaces.

**Application Architecture (APP) — 2 Blockers:**

11. **APP-Q6: 12-Factor / Cloud-Native Compliance** — 10 of 34 services score < 2
    - **Score Distribution**: 10 services score 1, 18 services score 2, 6 services score 3
    - **Impact**: Weak cloud-native compliance blocks containerization and managed service adoption.
    - **Affected Services**: 10 services including akveo--ngx-admin, coreui--coreui-free-angular-admin-template, greenshot--greenshot, motdotla--node-lambda, and others
    - **Portfolio-Level Recommendation**: Conduct 12-factor assessment workshops. Create shared configuration management patterns using AWS Systems Manager Parameter Store or Secrets Manager.

12. **APP-Q5: Configuration Externalization** — 8 of 34 services score < 2
    - **Score Distribution**: 8 services score 1, 6 services score 2, 20 services score 3+
    - **Impact**: Hardcoded configuration prevents environment-specific deployments and secrets rotation.
    - **Affected Services**: 8 services
    - **Portfolio-Level Recommendation**: Standardize on AWS Systems Manager Parameter Store for non-sensitive config and AWS Secrets Manager for secrets. Create shared configuration libraries per language.

**Data Platform (DATA) — 3 Blockers:**

13. **DATA-Q1: Data Classification & Governance** — 20 of 34 services score < 2
    - **Score Distribution**: 20 services score 1, 6 services score 2, 8 services score 3+
    - **Impact**: No data classification or governance. Blocks compliance, security audit, and data migration planning.
    - **Affected Services**: 20 services
    - **Portfolio-Level Recommendation**: Implement a portfolio-wide data classification framework. Use AWS Macie for sensitive data discovery across data stores.

14. **DATA-Q3: Data Migration Readiness** — 14 of 34 services score < 2
    - **Score Distribution**: 14 services score 1, 8 services score 2, 12 services score 3+
    - **Impact**: No migration tooling, no schema versioning, no data migration strategy.
    - **Affected Services**: 14 services
    - **Portfolio-Level Recommendation**: Establish AWS DMS as the standard migration tool. Create migration playbooks for common database pairs (PostgreSQL→Aurora, MongoDB→DocumentDB, Redis→ElastiCache).

15. **DATA-Q2: Backup & Recovery Strategy** — 7 of 34 services score < 2
    - **Score Distribution**: 7 services score 1, 2 services score 2, 25 services score 3+
    - **Impact**: No backup strategy for services with persistent data. Risk of data loss.
    - **Affected Services**: 7 services
    - **Portfolio-Level Recommendation**: Configure automated backups via Aurora (preferred) automated snapshots and AWS Backup. All managed databases include built-in backup.

**Security Baseline (SEC) — 7 Blockers:**

16. **SEC-Q1: IAM & Access Control** — 30 of 34 services score < 2
    - **Score Distribution**: 30 services score 1, 4 services score 2
    - **Impact**: No IAM roles, no access control policies. Complete absence of AWS identity management.
    - **Affected Services**: 30 services
    - **Portfolio-Level Recommendation**: Create shared IAM role templates per service archetype (EKS pod roles, Lambda execution roles). Use AWS IAM Identity Center for centralized access management.

17. **SEC-Q6: Least-Privilege IAM Policies** — 25 of 34 services score < 2
    - **Score Distribution**: 25 services score 1, 7 services score 2, 2 services score 3
    - **Impact**: No least-privilege policies. All services either have no IAM or use overly broad permissions.
    - **Affected Services**: 25 services
    - **Portfolio-Level Recommendation**: Implement IAM Access Analyzer across the portfolio. Create per-service IAM policies with minimum required permissions. Use AWS CDK to generate least-privilege policies from service definitions.

18. **SEC-Q4: Dependency Vulnerability Management** — 20 of 34 services score < 2
    - **Score Distribution**: 20 services score 1, 7 services score 2, 7 services score 3
    - **Impact**: No automated dependency scanning. Vulnerable dependencies reach production undetected.
    - **Affected Services**: 20 services
    - **Portfolio-Level Recommendation**: Enable GitHub Dependabot and CodeQL across all repositories. Add Amazon Inspector for runtime vulnerability scanning on deployed workloads.

19. **SEC-Q3: Encryption in Transit** — 14 of 34 services score < 2
    - **Score Distribution**: 14 services score 1, 9 services score 2, 11 services score 3
    - **Impact**: No TLS enforcement. Data transmitted in plaintext between services and clients.
    - **Affected Services**: 14 services
    - **Portfolio-Level Recommendation**: Enforce TLS everywhere via API Gateway (preferred) with custom domains and ACM certificates. Use service mesh mutual TLS for inter-service communication on EKS.

20. **SEC-Q2: Encryption at Rest** — 13 of 14 applicable services score < 2
    - **Score Distribution**: 13 services score 1, 1 service scores 3 (20 services N/A)
    - **Impact**: No encryption at rest for persistent data stores.
    - **Affected Services**: 13 of 14 applicable services
    - **Portfolio-Level Recommendation**: Aurora (preferred) and DynamoDB (preferred) encrypt at rest by default. Migration to managed databases automatically resolves this gap.

21. **SEC-Q7: Application Security Pipeline** — 13 of 34 services score < 2
    - **Score Distribution**: 13 services score 1, 12 services score 2, 9 services score 3
    - **Impact**: No SAST, DAST, or container scanning in CI/CD pipelines.
    - **Affected Services**: 13 services
    - **Portfolio-Level Recommendation**: Add shared GitHub Actions security scanning workflows (CodeQL, Trivy, Snyk) as reusable workflow templates.

22. **SEC-Q5: Secrets Management** — 6 of 34 services score < 2
    - **Score Distribution**: 6 services score 1, 24 services score 2, 4 services score 3
    - **Impact**: Hardcoded secrets in source code. Critical security vulnerability.
    - **Affected Services**: 6 services
    - **Portfolio-Level Recommendation**: Migrate all secrets to AWS Secrets Manager. Implement pre-commit hooks to detect hardcoded secrets (git-secrets, trufflehog).

**Operations & Observability (OPS) — 9 Blockers:**

23. **OPS-Q7: Runbook / Incident Response** — 32 of 34 services score < 2
    - **Score Distribution**: 32 services score 1, 1 service scores 2, 1 service scores 3
    - **Impact**: No runbooks or incident response procedures. Operational incidents have no documented resolution path.
    - **Affected Services**: 32 services
    - **Portfolio-Level Recommendation**: Create standardized runbook templates. Use AWS Systems Manager Incident Manager for incident tracking and automated response.

24. **OPS-Q9: Chaos Engineering / Game Days** — 32 of 34 services score < 2
    - **Score Distribution**: 32 services score 1, 1 service scores 2, 1 service scores 3
    - **Impact**: No chaos engineering or resilience testing. Failure modes are unknown until production incidents occur.
    - **Affected Services**: 32 services
    - **Portfolio-Level Recommendation**: Establish quarterly game days using AWS Fault Injection Simulator. Start with simple experiments (AZ failure, dependency timeout) on Phase 1 services.

25. **OPS-Q4: Log Aggregation Strategy** — 28 of 34 services score < 2
    - **Score Distribution**: 28 services score 1, 5 services score 2, 1 service scores 3
    - **Impact**: No centralized log aggregation. Debugging requires manual log inspection across services.
    - **Affected Services**: 28 services
    - **Portfolio-Level Recommendation**: Deploy centralized logging via Amazon CloudWatch Logs with structured JSON logging. Create shared logging libraries per language.

26. **OPS-Q5: Deployment Strategy** — 26 of 34 services score < 2
    - **Score Distribution**: 26 services score 1, 6 services score 2, 2 services score 3
    - **Impact**: No deployment strategy (blue-green, canary, rolling). All deployments are all-at-once with no rollback capability.
    - **Affected Services**: 26 services
    - **Portfolio-Level Recommendation**: Standardize on EKS rolling deployments with health checks. For critical services, implement blue-green deployments via CodeDeploy.

27. **OPS-Q8: Capacity Planning** — 22 of 34 services score < 2
    - **Score Distribution**: 22 services score 1, 12 services score 2
    - **Impact**: No capacity planning or resource sizing. Services are either over-provisioned or under-provisioned.
    - **Affected Services**: 22 services
    - **Portfolio-Level Recommendation**: Use AWS Compute Optimizer for right-sizing recommendations. Implement cost allocation tags for portfolio-wide cost visibility.

28. **OPS-Q1: Distributed Tracing** — 20 of 34 services score < 2
    - **Score Distribution**: 20 services score 1, 6 services score 2, 8 services score 3
    - **Impact**: No distributed tracing. Cannot trace requests across services or identify performance bottlenecks.
    - **Affected Services**: 20 services
    - **Portfolio-Level Recommendation**: Deploy AWS X-Ray or OpenTelemetry ADOT Collector as a shared observability platform. Create shared tracing libraries per language.

29. **OPS-Q3: Centralized Metrics & Monitoring** — 19 of 34 services score < 2
    - **Score Distribution**: 19 services score 1, 4 services score 2, 11 services score 3
    - **Impact**: No centralized metrics. Cannot correlate performance across services or set up cross-service dashboards.
    - **Affected Services**: 19 services
    - **Portfolio-Level Recommendation**: Standardize on Amazon CloudWatch Metrics with custom namespaces per service. Create shared CloudWatch dashboards for portfolio-wide visibility.

30. **OPS-Q2: SLO/SLA Definition** — 16 of 18 applicable services score < 2
    - **Score Distribution**: 16 services score 1, 2 services score 2 (16 services N/A)
    - **Impact**: No SLOs or SLAs defined. Cannot measure service reliability or set improvement targets.
    - **Affected Services**: 16 of 18 applicable services
    - **Portfolio-Level Recommendation**: Define SLOs for all deployed services. Use Amazon CloudWatch SLO monitoring (Application Signals) for automated SLO tracking.

31. **OPS-Q6: Integration Testing** — 3 of 34 services score < 2
    - **Score Distribution**: 3 services score 1, 6 services score 2, 25 services score 3+
    - **Impact**: Services without integration tests have higher regression risk during modernization.
    - **Affected Services**: 3 services (akveo--ngx-admin, greenshot--greenshot, umami-software--umami)
    - **Portfolio-Level Recommendation**: Establish minimum testing standards (unit + integration) for all services before modernization begins.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking. Address as capacity allows or in parallel with other modernization work.

1. **INF-Q11: CI/CD Automation** — 16 of 34 services score < 3
   - **Score Distribution**: 1 service score 1, 15 services score 2, 18 services score 3
   - **Impact**: CI/CD pipelines exist but lack deployment automation. Build+test is automated but deployment is manual.
   - **Affected Services**: 16 services
   - **Portfolio-Level Recommendation**: Extend GitHub Actions workflows to include deployment stages (build → test → deploy to staging → deploy to production). Use AWS CodeDeploy for deployment orchestration.

2. **APP-Q1: Programming Languages & Frameworks** — 4 of 34 services score < 3
   - **Score Distribution**: 0 services score 1, 4 services score 2, 30 services score 3+
   - **Impact**: Some services use outdated language versions or frameworks.
   - **Affected Services**: 4 services
   - **Portfolio-Level Recommendation**: Establish language version upgrade cadence (annual). Prioritize upgrading to LTS versions.

3. **APP-Q2: Application Architecture Pattern** — 12 of 34 services score < 3
   - **Score Distribution**: 0 services score 1, 12 services score 2, 22 services score 3+
   - **Impact**: Monolithic architectures limit independent scaling and deployment.
   - **Affected Services**: 12 services
   - **Portfolio-Level Recommendation**: Apply Strangler Fig pattern for monolith decomposition. Use API Gateway (preferred) for routing between monolith and new microservices.

4. **APP-Q3: Async Communication Pattern** — 8 of 17 applicable services score < 3
   - **Score Distribution**: 1 service score 1, 7 services score 2, 9 services score 3+ (17 services N/A)
   - **Impact**: Services use synchronous communication where async would improve resilience.
   - **Affected Services**: 8 of 17 applicable services
   - **Portfolio-Level Recommendation**: Introduce EventBridge (preferred) for event-driven communication. Create shared event schema registry.

5. **APP-Q4: Statelessness & Horizontal Scalability** — 4 of 17 applicable services score < 3
   - **Score Distribution**: 0 services score 1, 4 services score 2, 13 services score 3+ (17 services N/A)
   - **Impact**: Stateful services cannot scale horizontally on EKS (preferred).
   - **Affected Services**: 4 of 17 applicable services
   - **Portfolio-Level Recommendation**: Externalize session state to ElastiCache (Redis). Design for horizontal scaling with EKS pod auto-scaling.

### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 1.46 / 4.0**

**Common Patterns:**
- GitHub Actions CI/CD: present in 33 services
- Docker definitions: present in 21 services
- No IaC: present in 24 services

**Critical Gaps:**
1. Multi-AZ Resilience (INF-Q7): all 34 services score 1 — establish shared multi-AZ infrastructure patterns
2. Network Security (INF-Q5): 33 services score 1 — design shared VPC architecture
3. Managed Compute (INF-Q1): 32 services score 1 — adopt EKS (preferred) as standard compute
4. IaC Coverage (INF-Q10): 31 services score 1 — standardize on AWS CDK or Terraform

#### Application Architecture

**Portfolio Score: 2.73 / 4.0**

**Common Patterns:**
- Strong language/framework maturity (APP-Q1 avg ~3.2)
- Good modular architecture in many services (APP-Q2 avg ~2.6)

**Critical Gaps:**
1. 12-Factor Compliance (APP-Q6): 10 services score 1 — conduct cloud-native readiness workshops
2. Configuration Externalization (APP-Q5): 8 services score 1 — standardize on Parameter Store/Secrets Manager

#### Data Platform

**Portfolio Score: 2.64 / 4.0**

**Common Patterns:**
- Strong proprietary SQL avoidance (DATA-Q4 avg ~3.9 — almost all use open-source databases)
- Good backup awareness for services with databases

**Critical Gaps:**
1. Data Classification (DATA-Q1): 20 services score 1 — implement portfolio-wide data governance
2. Migration Readiness (DATA-Q3): 14 services score 1 — establish AWS DMS migration playbooks

#### Security Baseline

**Portfolio Score: 1.61 / 4.0**

**Common Patterns:**
- Open-source projects generally lack IAM and AWS security integration
- Some services have dependency scanning via Dependabot (score 2-3 on SEC-Q4)

**Critical Gaps:**
1. IAM & Access Control (SEC-Q1): 30 services score 1 — create shared IAM templates
2. Least-Privilege Policies (SEC-Q6): 25 services score 1 — implement IAM Access Analyzer
3. Dependency Vulnerabilities (SEC-Q4): 20 services score 1 — enable Dependabot + CodeQL

#### Operations & Observability

**Portfolio Score: 1.53 / 4.0**

**Common Patterns:**
- Minimal observability infrastructure across the portfolio
- Some services have basic logging (stdout/stderr)
- Integration testing exists in many services (OPS-Q6 avg ~2.7)

**Critical Gaps:**
1. Runbooks (OPS-Q7): 32 services score 1 — create standardized runbook templates
2. Chaos Engineering (OPS-Q9): 32 services score 1 — establish quarterly game days
3. Log Aggregation (OPS-Q4): 28 services score 1 — deploy CloudWatch Logs centrally
4. Deployment Strategy (OPS-Q5): 26 services score 1 — standardize on EKS rolling deployments

---

## Portfolio Modernization Roadmap

> Score-based phased roadmap with fixed phase names. Since no dependency_overrides were provided and services are independent open-source projects, services are ordered by score (lowest first). All services are P2 priority.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Score-Based Order**: Lowest-scoring services first (most gaps = most value from early modernization)
3. **Risk Mitigation**: Cross-cutting blockers resolved before service-level work
4. **Parallel Tracks**: All services are independent and can be modernized concurrently within each phase
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities and address portfolio-wide blockers before any service-level modernization.

**Cross-Cutting Activities:**
- **IaC Foundation**: Select and standardize on AWS CDK or Terraform. Create shared module repository with templates for VPC, EKS cluster, Aurora, API Gateway, and CloudWatch. Addresses INF-Q10 (31 services) and INF-Q7 (34 services).
- **Shared VPC Architecture**: Design and deploy a shared VPC with public/private subnets, NAT gateways, and security group templates. Addresses INF-Q5 (33 services).
- **EKS Cluster Setup**: Deploy shared EKS (preferred) cluster with auto-scaling, multi-AZ configuration, and standard namespace layout. Addresses INF-Q1 (32 services) and INF-Q8 (10 services).
- **Security Foundation**: Create shared IAM role templates, enable Dependabot/CodeQL across all repos, deploy AWS Secrets Manager. Addresses SEC-Q1 (30 services), SEC-Q4 (20 services), SEC-Q5 (6 services).
- **Observability Platform**: Deploy centralized CloudWatch Logs, CloudWatch Metrics, and X-Ray tracing. Create shared logging/tracing libraries per language. Addresses OPS-Q4 (28 services), OPS-Q1 (20 services).
- **CI/CD Enhancement**: Create reusable GitHub Actions workflow templates for build+test+deploy+scan. Addresses INF-Q11 (16 services), SEC-Q7 (13 services).

**Organizational Enablers:**
- Training: IaC fundamentals (CDK/Terraform), container orchestration (EKS), AWS security basics, observability (CloudWatch/X-Ray)
- Tooling: Shared IaC module repository, reusable GitHub Actions workflows, Docker multi-stage build templates
- Standards: IaC style guide, container security scanning requirements, minimum testing standards, runbook templates

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize the lowest-scoring services. Establish patterns and reference implementations.

**Services in Scope** (5 services, score < 1.70):

1. **akveo--ngx-admin** (P2, Score: 1.51 / 4.0)
   - Current State: Angular SPA template with no IaC, no compute, no security
   - Target State: Containerized on EKS with CloudFront CDN, IaC via CDK
   - Key Activities:
     - Create Dockerfile for static SPA hosting (nginx + Angular build)
     - Deploy to EKS with CDK-defined infrastructure
     - Add CloudFront distribution for CDN
   - Dependencies: Phase 0 (EKS cluster, IaC templates)
   - Estimated Effort: Low

2. **coreui--coreui-free-angular-admin-template** (P2, Score: 1.55 / 4.0)
   - Current State: Angular SPA template, similar gaps to ngx-admin
   - Target State: Containerized on EKS with CloudFront CDN, IaC via CDK
   - Key Activities:
     - Replicate ngx-admin deployment pattern
     - Add security scanning to CI/CD
   - Dependencies: Phase 0 (EKS cluster, IaC templates)
   - Estimated Effort: Low

3. **getlift--lift** (P2, Score: 1.60 / 4.0)
   - Current State: Serverless Framework plugin, no IaC for the plugin itself, no security pipeline
   - Target State: Enhanced CI/CD with security scanning, npm publish automation
   - Key Activities:
     - Add dependency scanning (Dependabot/CodeQL)
     - Automate npm publish in GitHub Actions
     - Add IaC for any test infrastructure
   - Dependencies: Phase 0 (CI/CD templates)
   - Estimated Effort: Low

4. **motdotla--node-lambda** (P2, Score: 1.60 / 4.0)
   - Current State: Node.js CLI for Lambda deployment, no IaC, no security pipeline
   - Target State: Enhanced CI/CD with automated npm publish, security scanning
   - Key Activities:
     - Add security scanning workflows
     - Automate npm publish process
     - Add integration tests for Lambda deployment
   - Dependencies: Phase 0 (CI/CD templates)
   - Estimated Effort: Low

5. **greenshot--greenshot** (P2, Score: 1.68 / 4.0)
   - Current State: Windows desktop app (C#/.NET), no CI/CD deployment, no security pipeline
   - Target State: Automated build/release pipeline, security scanning, signed binaries
   - Key Activities:
     - Add CodeQL scanning for C# codebase
     - Automate release builds in GitHub Actions
     - Add Dependabot for NuGet dependencies
   - Dependencies: Phase 0 (CI/CD templates)
   - Estimated Effort: Medium

**Expected Outcomes:**
- 5 services modernized with basic cloud readiness
- Reference deployment patterns for Angular SPAs and CLI tools established
- Security scanning pipeline templates proven

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize services scoring 1.70–2.09. Build on Phase 1 patterns.

**Services in Scope** (15 services):

1. **umami-software--umami** (P2, Score: 1.70 / 4.0) — Containerize Next.js analytics platform on EKS, migrate to Aurora PostgreSQL
2. **tqdm--tqdm** (P2, Score: 1.76 / 4.0) — Enhance CI/CD, add security scanning for PyPI library
3. **dwyl--aws-sdk-mock** (P2, Score: 1.80 / 4.0) — Enhance CI/CD, add security scanning for npm library
4. **Netflix--eureka** (P2, Score: 1.82 / 4.0) — Containerize service discovery on EKS, evaluate AWS Cloud Map as replacement
5. **Lidarr--Lidarr** (P2, Score: 1.84 / 4.0) — Containerize on EKS, migrate SQLite to Aurora PostgreSQL
6. **realworld-apps--angular-realworld-example-app** (P2, Score: 1.84 / 4.0) — Apply Angular SPA pattern from Phase 1
7. **gulpjs--gulp** (P2, Score: 1.88 / 4.0) — Enhance CI/CD, add security scanning for npm library
8. **Radarr--Radarr** (P2, Score: 1.90 / 4.0) — Containerize on EKS, migrate SQLite to Aurora PostgreSQL, shared *arr pattern
9. **Prowlarr--Prowlarr** (P2, Score: 1.93 / 4.0) — Containerize on EKS, apply shared *arr deployment pattern
10. **arrow-py--arrow** (P2, Score: 1.93 / 4.0) — Enhance CI/CD, add security scanning for PyPI library
11. **OpenAPITools--openapi-generator** (P2, Score: 1.94 / 4.0) — Enhance CI/CD, add security scanning
12. **Sonarr--Sonarr** (P2, Score: 1.96 / 4.0) — Containerize on EKS, apply shared *arr deployment pattern
13. **thingsboard--thingsboard** (P2, Score: 1.96 / 4.0) — Containerize IoT platform on EKS, migrate to Aurora PostgreSQL + DynamoDB
14. **scality--backbeat** (P2, Score: 2.04 / 4.0) — Containerize on EKS, evaluate EventBridge to replace self-managed Kafka
15. **scality--cloudserver** (P2, Score: 2.08 / 4.0) — Containerize on EKS, migrate MongoDB to DocumentDB

**Parallel Tracks:**
- Track A: *arr suite (Sonarr, Radarr, Lidarr, Prowlarr) — shared C# containerization template
- Track B: Libraries (tqdm, arrow, gulp, dwyl, openapi-generator) — shared CI/CD enhancement pattern
- Track C: Web applications (umami, realworld) — shared containerized web app pattern
- Track D: Platform services (eureka, thingsboard, scality) — containerization + database migration

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize higher-scoring services, implement advanced capabilities.

**Services in Scope** (14 services, score >= 2.10):

1. **apache--flink-connector-aws** (P2, Score: 2.10 / 4.0) — Enhance CI/CD, add security scanning for Maven library
2. **conductor-oss--conductor** (P2, Score: 2.10 / 4.0) — Containerize workflow engine on EKS, migrate to Aurora + DynamoDB
3. **Graylog2--graylog2-server** (P2, Score: 2.12 / 4.0) — Containerize on EKS, migrate MongoDB to DocumentDB, evaluate OpenSearch
4. **FlowiseAI--Flowise** (P2, Score: 2.14 / 4.0) — Containerize LLM platform on EKS, integrate with Bedrock (preferred)
5. **getsentry--sentry-python** (P2, Score: 2.14 / 4.0) — Enhance CI/CD, add security scanning for PyPI SDK
6. **iterative--dvc** (P2, Score: 2.15 / 4.0) — Enhance CI/CD, add security scanning, evaluate SageMaker integration
7. **webpack--webpack** (P2, Score: 2.15 / 4.0) — Enhance CI/CD, add security scanning for npm library
8. **openzipkin--zipkin** (P2, Score: 2.18 / 4.0) — Containerize on EKS, evaluate X-Ray as managed alternative
9. **zappa--Zappa** (P2, Score: 2.19 / 4.0) — Enhance CI/CD, add security scanning, improve Lambda deployment patterns
10. **ToolJet--ToolJet** (P2, Score: 2.30 / 4.0) — Containerize on EKS, migrate to Aurora PostgreSQL
11. **Alluxio--alluxio** (P2, Score: 2.31 / 4.0) — Containerize on EKS, evaluate S3 integration patterns
12. **hapifhir--hapi-fhir** (P2, Score: 2.35 / 4.0) — Containerize FHIR server on EKS, migrate to Aurora PostgreSQL
13. **apache--druid** (P2, Score: 2.41 / 4.0) — Containerize analytics DB on EKS, evaluate managed analytics alternatives
14. **serverless--serverless** (P2, Score: 2.78 / 4.0) — Minor improvements: enhance security scanning, improve documentation

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6+ months (with 4+ parallel tracks per phase)
**Note**: Since all services are independent, maximum parallelism is achievable. The timeline can be compressed by increasing team size.

---

## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach. A customer portfolio may be divided into multiple pathways depending on workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 11 | 32% | Medium | High |
| Move to Containers | 12 | 35% | Medium | Medium |
| Move to Open Source | 0 | 0% | Low | — |
| Move to Managed Databases | 15 | 44% | Medium | High |
| Move to Managed Analytics | 3 | 9% | Low | Medium |
| Move to Modern DevOps | 34 | 100% | High | Medium |
| Move to AI | 1 | 3% | Low | Low |

### Portfolio Pathway Aggregation

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, akveo--ngx-admin, hapifhir--hapi-fhir, scality--backbeat, scality--cloudserver, umami-software--umami | Alluxio--alluxio, Netflix--eureka, OpenAPITools--openapi-generator, ToolJet--ToolJet, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, webpack--webpack, zappa--Zappa | — |
| Move to Containers | Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, akveo--ngx-admin, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, gulpjs--gulp, realworld-apps--angular-realworld-example-app | Alluxio--alluxio, FlowiseAI--Flowise, OpenAPITools--openapi-generator, ToolJet--ToolJet, apache--druid, apache--flink-connector-aws, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — |
| Move to Open Source | — | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — |
| Move to Managed Databases | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami | akveo--ngx-admin, Netflix--eureka, OpenAPITools--openapi-generator, apache--flink-connector-aws, arrow-py--arrow, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, realworld-apps--angular-realworld-example-app, serverless--serverless, tqdm--tqdm, webpack--webpack, zappa--Zappa | — |
| Move to Managed Analytics | scality--backbeat, thingsboard--thingsboard, umami-software--umami | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, serverless--serverless, tqdm--tqdm, webpack--webpack, zappa--Zappa | — |
| Move to Modern DevOps | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — | — |
| Move to AI | iterative--dvc | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| akveo--ngx-admin | ✅ | ✅ | — | — | — | ✅ | — |
| Alluxio--alluxio | — | — | — | ✅ | — | ✅ | — |
| apache--druid | — | — | — | ✅ | — | ✅ | — |
| apache--flink-connector-aws | — | — | — | — | — | ✅ | — |
| arrow-py--arrow | — | ✅ | — | — | — | ✅ | — |
| conductor-oss--conductor | — | ✅ | — | ✅ | — | ✅ | — |
| coreui--coreui-free-angular-admin-template | — | ✅ | — | — | — | ✅ | — |
| dwyl--aws-sdk-mock | — | — | — | — | — | ✅ | — |
| FlowiseAI--Flowise | ✅ | — | — | ✅ | — | ✅ | — |
| getlift--lift | — | — | — | — | — | ✅ | — |
| getsentry--sentry-python | — | — | — | — | — | ✅ | — |
| Graylog2--graylog2-server | ✅ | ✅ | — | ✅ | — | ✅ | — |
| greenshot--greenshot | — | — | — | — | — | ✅ | — |
| gulpjs--gulp | — | ✅ | — | — | — | ✅ | — |
| hapifhir--hapi-fhir | ✅ | — | — | — | — | ✅ | — |
| iterative--dvc | — | — | — | — | — | ✅ | ✅ |
| Lidarr--Lidarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| motdotla--node-lambda | — | — | — | — | — | ✅ | — |
| Netflix--eureka | — | ✅ | — | — | — | ✅ | — |
| OpenAPITools--openapi-generator | — | — | — | — | — | ✅ | — |
| openzipkin--zipkin | — | — | — | ✅ | — | ✅ | — |
| Prowlarr--Prowlarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| Radarr--Radarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| realworld-apps--angular-realworld-example-app | — | ✅ | — | — | — | ✅ | — |
| scality--backbeat | ✅ | — | — | ✅ | ✅ | ✅ | — |
| scality--cloudserver | ✅ | — | — | ✅ | — | ✅ | — |
| serverless--serverless | — | — | — | — | — | ✅ | — |
| Sonarr--Sonarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| thingsboard--thingsboard | — | — | — | ✅ | ✅ | ✅ | — |
| ToolJet--ToolJet | — | — | — | ✅ | — | ✅ | — |
| tqdm--tqdm | — | — | — | — | — | ✅ | — |
| umami-software--umami | ✅ | — | — | ✅ | ✅ | ✅ | — |
| webpack--webpack | — | — | — | — | — | ✅ | — |
| zappa--Zappa | — | — | — | — | — | ✅ | — |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is a prerequisite for Move to AI in many cases (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps (all 34 services) — runs first, enables everything
- **Track 2**: Move to Containers (12 services) + Move to Cloud Native (11 services) — can start after Phase 0
- **Track 3**: Move to Managed Databases (15 services) — can run in parallel with Track 2
- **Track 4**: Move to Managed Analytics (3 services) + Move to AI (1 service) — after Track 3 foundations

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: All 34 services
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q10 < 2: affects 31 services (no IaC)
  - INF-Q11 < 3: affects 16 services (incomplete CI/CD)
  - OPS-Q5 < 2: affects 26 services (no deployment strategy)
- **Representative AWS Services**: AWS CDK, AWS CloudFormation, AWS CodeDeploy, AWS CodePipeline, GitHub Actions (already adopted)
- **Key Activities**:
  1. Standardize IaC across portfolio (CDK or Terraform)
  2. Add deployment stages to existing GitHub Actions pipelines
  3. Implement blue-green/canary deployment patterns
  4. Add security scanning to all CI/CD pipelines
- **Cross-Service Synergies**: Reusable GitHub Actions workflow templates, shared IaC modules
- **Estimated Effort**: Medium across 34 services
- **Roadmap Phase Alignment**: Phase 0 (shared foundation) and Phase 1-3 (per-service)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to Managed Databases

- **Services Affected**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami (15 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q2 < 2: affects 14 services (self-managed databases)
  - DATA-Q3 < 2: affects 14 services (no migration readiness)
- **Representative AWS Services**: Aurora PostgreSQL (preferred), DynamoDB (preferred), Amazon DocumentDB, Amazon ElastiCache
- **Key Activities**:
  1. Map current database engines to target AWS managed services
  2. Create migration playbooks per database type (PostgreSQL→Aurora, MongoDB→DocumentDB, SQLite→Aurora, Redis→ElastiCache)
  3. Use AWS DMS for data migration
  4. Validate application compatibility with target databases
- **Cross-Service Synergies**: *arr suite shares SQLite→Aurora migration pattern; Scality pair shares MongoDB→DocumentDB migration
- **Estimated Effort**: High across 15 services
- **Roadmap Phase Alignment**: Phase 2-3
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Containers

- **Services Affected**: 12 services (Graylog2, Lidarr, Netflix--eureka, Prowlarr, Radarr, Sonarr, akveo--ngx-admin, arrow-py--arrow, conductor-oss--conductor, coreui, gulpjs--gulp, realworld-apps) 
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q1 < 2: affects 32 services (no managed compute)
  - No existing container orchestration detected
- **Representative AWS Services**: Amazon EKS (preferred), Amazon ECR, AWS Fargate
- **Key Activities**:
  1. Create Dockerfiles for services without them
  2. Build multi-stage Docker builds for optimal image size
  3. Deploy to shared EKS cluster (preferred)
  4. Configure health checks and resource limits
- **Cross-Service Synergies**: Shared EKS cluster, shared Dockerfile templates per language
- **Estimated Effort**: Medium across 12 services
- **Roadmap Phase Alignment**: Phase 1-2
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

#### Move to Cloud Native

- **Services Affected**: 11 services (FlowiseAI, Graylog2, Lidarr, Prowlarr, Radarr, Sonarr, akveo--ngx-admin, hapifhir, scality--backbeat, scality--cloudserver, umami)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - APP-Q2 < 3: monolithic architecture requiring decomposition
  - INF-Q1 = 1: no managed compute
- **Representative AWS Services**: Amazon EKS (preferred), Amazon API Gateway (preferred), Amazon EventBridge (preferred), AWS Lambda
- **Key Activities**:
  1. Identify service boundaries in monolithic applications
  2. Apply Strangler Fig pattern for incremental decomposition
  3. Implement API Gateway (preferred) for service routing
  4. Introduce EventBridge (preferred) for event-driven communication
- **Cross-Service Synergies**: *arr suite can share decomposition patterns; Scality pair can coordinate API gateway consolidation
- **Estimated Effort**: High across 11 services
- **Roadmap Phase Alignment**: Phase 2-3
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Managed Analytics

- **Services Affected**: scality--backbeat, thingsboard--thingsboard, umami-software--umami (3 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q4 related: data processing workloads using self-managed analytics infrastructure
- **Representative AWS Services**: Amazon Kinesis Data Analytics, Amazon OpenSearch Service, Amazon QuickSight
- **Key Activities**:
  1. Evaluate managed analytics alternatives for each service's data pipeline
  2. Migrate self-managed Kafka/Elasticsearch to managed services
- **Estimated Effort**: Medium across 3 services
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

#### Move to AI

- **Services Affected**: iterative--dvc (1 total)
- **Portfolio Priority**: Low
- **Aggregation**: Move to AI: Triggered in 1 of 34 services (32 services had no AI intent in context — pathway correctly suppressed)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): 32 services
  - Already present (AI frameworks detected): FlowiseAI--Flowise (LLM flow builder with existing AI integration)
- **Common Trigger Criteria**:
  - DVC is a data/ML versioning tool that could benefit from SageMaker/Bedrock integration
- **Representative AWS Services**: Amazon Bedrock (preferred), Amazon SageMaker, AWS Step Functions for ML pipelines
- **Key Activities**:
  1. Evaluate Bedrock (preferred) integration for DVC experiment tracking
  2. Explore SageMaker integration for model management
- **Estimated Effort**: Low across 1 service
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Integration Opportunities

### Shared Service Extraction

**Opportunity: Shared CI/CD Pipeline Templates**
- **Current State**: Each of the 34 services maintains its own GitHub Actions workflows with varying quality and coverage
- **Proposed Solution**: Create a shared `.github/workflows` repository with reusable composite actions for build, test, security scan, and deploy per language (Java, Node.js, Python, C#)
- **Benefits**: Consistent CI/CD quality, reduced maintenance, faster onboarding of new services
- **Effort**: Low
- **Priority**: High

**Opportunity: Shared IaC Module Library**
- **Current State**: 24 services have zero IaC; no standardization exists
- **Proposed Solution**: Create a shared CDK/Terraform module library with VPC, EKS, Aurora, API Gateway, and CloudWatch patterns
- **Benefits**: Consistent infrastructure, reduced time-to-deploy, standardized security controls
- **Effort**: Medium
- **Priority**: High

**Opportunity: Shared *arr Deployment Pattern**
- **Current State**: Sonarr, Radarr, Lidarr, Prowlarr share identical C#/.NET architecture patterns with separate deployment approaches
- **Proposed Solution**: Create a shared Helm chart / EKS deployment template for the *arr suite with configurable database and API settings
- **Benefits**: 4x reduction in deployment template maintenance, consistent monitoring and scaling
- **Effort**: Medium
- **Priority**: Medium

**Opportunity: Shared Logging/Tracing Libraries**
- **Current State**: No centralized observability. Each service has ad-hoc logging (28 services score 1 on OPS-Q4)
- **Proposed Solution**: Create per-language logging libraries (Java, Node.js, Python, C#) that output structured JSON to CloudWatch Logs and integrate with X-Ray tracing
- **Benefits**: End-to-end tracing, consistent log format, centralized dashboards
- **Effort**: Medium
- **Priority**: High

### Event-Driven Architecture

**Opportunity: Scality Event Processing Modernization**
- **Current State**: scality--backbeat uses self-managed Kafka (node-rdkafka) for event consumption from scality--cloudserver
- **Proposed Solution**: Evaluate replacing self-managed Kafka with Amazon MSK Serverless or EventBridge (preferred) for event routing
- **Benefits**: Reduced operational overhead, automatic scaling, lower cost. Aligns with preference to avoid self-managed-kafka.
- **Effort**: High

**Opportunity: ThingsBoard IoT Event Processing**
- **Current State**: thingsboard--thingsboard uses self-managed Kafka for telemetry event processing
- **Proposed Solution**: Evaluate Amazon Kinesis Data Streams for telemetry ingestion and EventBridge (preferred) for rule engine events
- **Benefits**: Managed scaling, reduced Kafka operational burden
- **Effort**: High

### API Gateway Consolidation

**Opportunity: Unified API Gateway for Services with API Surfaces**
- **Current State**: 17 services have API surfaces (INF-Q3 applicable) with no shared API management
- **Proposed Solution**: Deploy Amazon API Gateway (preferred) as a shared API management layer with custom domains, rate limiting, and authentication
- **Benefits**: Consistent auth, rate limiting, monitoring, cost reduction across all API services
- **Effort**: Medium

### Observability Unification

**Opportunity: Centralized Observability Stack**
- **Current State**: No shared observability. OPS category average is 1.53/4.0 — the lowest across all categories
- **Proposed Solution**: Deploy a centralized observability stack: CloudWatch Logs + CloudWatch Metrics + X-Ray/ADOT + CloudWatch Dashboards
- **Benefits**: End-to-end visibility, cross-service correlation, proactive alerting
- **Effort**: Medium
- **Priority**: High

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| No IaC across 91% of services — infrastructure changes are unreproducible | High | High | 🔴 Critical | Standardize on CDK/Terraform in Phase 0; create shared modules | Phase 0 |
| No network security (VPC/SG) for 97% of services | High | High | 🔴 Critical | Deploy shared VPC architecture with security groups in Phase 0 | Phase 0 |
| No IAM roles for 88% of services — no access control | High | High | 🔴 Critical | Create shared IAM templates; enable AWS IAM Identity Center | Phase 0 |
| No managed compute for 94% of services | High | High | 🔴 Critical | Deploy shared EKS cluster in Phase 0 | Phase 0 |
| All databases self-managed — no automated backup, no encryption | High | Medium | 🟠 High | Migrate to Aurora/DynamoDB (preferred) with built-in backup | Phase 2 |
| No deployment strategy for 76% of services | High | Medium | 🟠 High | Standardize on EKS rolling deployments in Phase 0-1 | Phase 1 |
| No distributed tracing for 59% of services | Medium | Medium | 🟡 Medium | Deploy X-Ray/ADOT in Phase 0 | Phase 0 |
| No runbooks for 94% of services | High | Medium | 🟠 High | Create runbook templates in Phase 0 | Phase 0 |
| No chaos engineering for 94% of services | Medium | Low | 🟢 Low | Establish game days in Phase 3 | Phase 3 |
| Self-managed Kafka in 2 services (Scality, ThingsBoard) | Medium | Medium | 🟡 Medium | Evaluate EventBridge/MSK Serverless replacement | Phase 2 |
| No dependency scanning for 59% of services | High | Medium | 🟠 High | Enable Dependabot/CodeQL across all repos in Phase 0 | Phase 0 |
| Hardcoded secrets in 6 services | High | High | 🔴 Critical | Immediate: rotate secrets; migrate to Secrets Manager | Phase 0 |

### High-Risk Dependencies

No services have both score < 2.0 AND fan-in >= 3 (all services are independent with fan-in = 0).

### Single Points of Failure

No services have blast radius >= 50% (all services are independent open-source projects with blast radius = 3%).

### Circular Dependency Risks

✅ No circular dependencies detected — all services are independent.

### Data Availability Risks

15 services use self-managed databases with no automated backup or failover. Migration to Aurora (preferred) and DynamoDB (preferred) would automatically provide:
- Automated daily backups with point-in-time recovery
- Multi-AZ failover
- Encryption at rest (default)
- Read replicas for scaling

### Observability Blind Spots

- 20 services (59%) have no distributed tracing (OPS-Q1 score < 2)
- 28 services (82%) have no centralized log aggregation (OPS-Q4 score < 2)
- 19 services (56%) have no centralized metrics (OPS-Q3 score < 2)
- Combined effect: The portfolio has near-zero operational visibility. Any production incident would require manual debugging with no correlation across services.

---

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + language-specific service teams

> With 31 foundational blockers and cross-cutting concerns affecting 90%+ of services, a centralized platform team is strongly recommended.

**Platform Team** (4–6 engineers):
- Responsibilities: Shared EKS infrastructure, VPC architecture, IaC module library, CI/CD templates, observability platform, security scanning, IAM templates
- Skills Required: AWS CDK or Terraform, EKS administration, CloudWatch/X-Ray, IAM, GitHub Actions, networking (VPC/SG)

**Service Teams** (organized by language ecosystem):
- **Java Team**: Alluxio, apache--druid, apache--flink-connector-aws, conductor-oss--conductor, Graylog2, hapifhir, Netflix--eureka, OpenAPITools, openzipkin--zipkin, thingsboard (10 services)
- **JavaScript/TypeScript Team**: akveo, coreui, dwyl, FlowiseAI, getlift, gulpjs, motdotla, realworld-apps, scality--backbeat, scality--cloudserver, serverless--serverless, ToolJet, umami, webpack (14 services)
- **Python Team**: arrow-py, getsentry, iterative--dvc, tqdm, zappa (5 services)
- **C# Team**: greenshot, Lidarr, Prowlarr, Radarr, Sonarr (5 services)

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| AWS CDK / Terraform | IaC for all services | No (24 services have no IaC) | High |
| Amazon EKS | Container orchestration | No (0 services use EKS) | High |
| Docker containerization | Moving to containers | Partial (21 services have Dockerfiles) | Medium |
| AWS IAM | Access control, security | No (30 services have no IAM) | High |
| CloudWatch / X-Ray | Observability | No (20 services have no tracing) | High |
| Aurora PostgreSQL | Database migration | No (0 services use Aurora) | Medium |
| DynamoDB | NoSQL data patterns | No (0 services use DynamoDB) | Medium |
| GitHub Actions (advanced) | CI/CD deployment automation | Partial (33 services have basic CI/CD) | Medium |
| API Gateway | API management | No (0 services use API Gateway) | Medium |
| EventBridge | Event-driven architecture | No (0 services use EventBridge) | Low |

### Training Recommendations

1. **Phase 0 Priority** (start immediately):
   - IaC fundamentals: AWS CDK or Terraform workshop (all teams)
   - EKS administration: Amazon EKS Primer + EKS Workshop (platform team)
   - AWS security: IAM & access control fundamentals (all teams)
   - Observability: CloudWatch and X-Ray basics (platform team)

2. **Phase 1-2 Priority**:
   - Container orchestration: Docker + EKS deployment patterns (service teams)
   - Database migration: AWS DMS + Aurora migration workshop (database-using service teams)
   - CI/CD automation: GitHub Actions advanced patterns + CodeDeploy (all teams)

3. **Phase 3 Priority**:
   - Advanced patterns: Event-driven architecture with EventBridge (applicable service teams)
   - AI/ML integration: Amazon Bedrock fundamentals (DVC/Flowise teams)

### External Support

Recommended AWS Professional Services or consulting partner engagement for:

1. **Phase 0: VPC and EKS Architecture Design** — AWS Solutions Architect engagement to design the shared VPC and EKS cluster architecture. Critical foundation that all services will depend on.
2. **Phase 2: Database Migration** — AWS Professional Services for DMS migration planning and execution for the 15 services with databases. Database migration carries highest risk of data loss.
3. **Phase 0: Security Posture Review** — AWS Security Specialist engagement to design IAM strategy, secrets management, and security scanning pipeline for the portfolio.

---

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.** Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | 33 of 34 services score < 2.5 — massive migration scope | 33 services have overall score < 2.5 (threshold: 3+) | Request MAP engagement via AWS Solutions Architect |
| Microsoft Modernization Program | MMP | 5 C#/.NET workloads detected | greenshot, Sonarr, Radarr, Lidarr, Prowlarr use C#/.NET | Request MMP assessment for .NET modernization |
| Windows App Modernization Program | WAMP | Windows desktop deployments detected | greenshot is a Windows desktop application (WinExe); *arr suite supports Windows deployment targets | Request WAMP assessment for Windows workload migration |
| Experience-Based Acceleration | EBA | 34 services have triggered pathways AND score < 3.0 | All 34 services have at least 1 triggered pathway and overall score < 3.0. Move to Modern DevOps (100%) and Move to Managed Databases (44%) are most prevalent. | Request EBA engagement focused on Modern DevOps and Managed Databases pathways |

### Program Details

**Migration Acceleration Program (MAP)**
- Why recommended: 33 of 34 services (97%) have overall scores below 2.5, indicating significant modernization gaps across the portfolio. The portfolio requires a coordinated migration effort spanning IaC adoption, container orchestration, managed database migration, and security hardening.
- What it provides: AWS credits, migration tools (AWS MGN, AWS DMS), Professional Services engagement, partner ecosystem support, and a structured migration methodology.
- Suggested timing: Initiate MAP engagement during Phase 0 to align with shared infrastructure provisioning and gain access to credits for EKS, Aurora, and other managed service adoption.

**Microsoft Modernization Program (MMP)**
- Why recommended: 5 services (greenshot, Sonarr, Radarr, Lidarr, Prowlarr) use C#/.NET. The *arr suite represents a significant modernization opportunity for .NET containerization on EKS or migration to AWS-native services.
- What it provides: .NET modernization tooling, Porting Assistant for .NET, .NET on Linux migration guidance, AWS-specific .NET optimization patterns.
- Suggested timing: Phase 2, when the *arr suite containerization begins.

**Windows App Modernization Program (WAMP)**
- Why recommended: greenshot is a Windows desktop application (WinForms/WPF, OutputType=WinExe). The *arr suite also supports Windows as a deployment target.
- What it provides: Windows workload assessment, EC2 Windows licensing optimization, Windows container guidance, AppStream 2.0 evaluation.
- Suggested timing: Phase 2-3, aligned with greenshot and *arr modernization.

**Experience-Based Acceleration (EBA)**
- Why recommended: All 34 services have at least one triggered pathway and overall scores below 3.0. The Move to Modern DevOps pathway is triggered for 100% of services, and Move to Managed Databases for 44%. This is a portfolio-wide modernization effort that would benefit from structured AWS engagement.
- What it provides: AWS Solutions Architects embedded with the customer team, pathway-specific workshops, hands-on implementation support, architecture reviews.
- Suggested timing: Initiate EBA engagement during Phase 0, focused on Move to Modern DevOps (IaC, CI/CD) and Move to Managed Databases (Aurora, DynamoDB) pathways.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect or Partner to determine eligibility and timing.

---

## Recommended Self-Paced Learning Materials

> Modules included based on portfolio-wide triggered pathways and skill gaps. Move to Open Source is excluded (0 services triggered).

### Module 2: Move to Cloud Native (Containers and Serverless)

- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

### Module 3: Move to Containers with Amazon ECS and EKS

- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

### Module 4: Move to Managed Databases

- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- Amazon DocumentDB Getting Started — https://skillbuilder.aws/learn/5RTP1DW5WQ/amazon-documentdb-with-mongodb-compatibility-getting-started/JDFWRT5GPD

### Module 5: Move to Managed Analytics

- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

### Module 6: Move to Modern DevOps

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/

### Module 7: Move to AI

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY

---

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across multiple repos. They are distinct from cross-cutting analysis (which aggregates individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 1
- **Finding**: The portfolio has no IaC standardization. 24 of 34 services (71%) have zero IaC. Of the remaining 10 services, 8 use Docker Compose (partial IaC) and 2 use Serverless Framework YAML. No service uses Terraform, AWS CDK, or CloudFormation. The most common "IaC tool" is Docker Compose at 24% coverage — far below the 80% threshold for score 3.
- **Evidence**: INF-Q10 scores: 31 services score 1 (no IaC), 3 services score 2 (partial). Docker Compose found in services with docker-compose.yml files (scality--backbeat, scality--cloudserver, Graylog2, FlowiseAI, ToolJet, conductor-oss, openzipkin, thingsboard).
- **Recommendation**: Select a single IaC tool (AWS CDK or Terraform, both align with preferences) and mandate it for all new infrastructure. Create a shared module library with standard patterns. Target 80%+ coverage within 6 months.
- **Contextual Annotations**: This finding amplifies the severity of INF-Q10 (Foundational Blocker #4) — the lack of standardization means there is no existing IaC pattern to replicate even for services that want to adopt IaC.

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: There is no centralized observability stack spanning the portfolio. Each service independently manages its own logging (if any). No shared CloudWatch Log Groups, no shared X-Ray tracing configuration, no shared dashboards, no consistent metric namespaces. OPS-Q1 (tracing) average is 1.4, OPS-Q3 (metrics) average is 1.7, OPS-Q4 (logging) average is 1.2 — all indicating near-absence of observability.
- **Evidence**: OPS-Q1: 20 services score 1, 6 services score 2. OPS-Q3: 19 services score 1. OPS-Q4: 28 services score 1. No cross-service correlation capability exists.
- **Recommendation**: Deploy a centralized observability platform: CloudWatch Logs for structured logging, CloudWatch Metrics with standardized namespaces, X-Ray/ADOT for distributed tracing. Create per-language observability libraries (Java, Node.js, Python, C#) that auto-instrument services.
- **Contextual Annotations**: This finding provides context for OPS-Q1, OPS-Q3, and OPS-Q4 (Foundational Blockers #28, #29, #25). A centralized platform deployment in Phase 0 would lift all three questions simultaneously.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 4
- **Finding**: No circular dependencies exist in the portfolio. All 34 services are independent open-source projects with no inter-service runtime dependencies. No dependency cycles were detected via either explicit `dependency_overrides` (not provided) or inference from report findings.
- **Evidence**: No inter-service REST/gRPC calls, no shared databases between services, no shared message queues (except within Scality cluster). Dependency graph has 34 disconnected nodes.
- **Recommendation**: Maintain independence. If services are deployed to a shared EKS cluster, ensure namespace isolation to prevent accidental coupling.
- **Contextual Annotations**: None — this score is independent of individual service assessments.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 2
- **Finding**: High technology diversity across the portfolio. 4 primary programming languages (Java=17, JavaScript=7, TypeScript=6, C#=5, Python=5), 10 distinct database engines, 5 CI/CD tools, and 2+ IaC approaches (mostly none). Technology diversity score: 4 languages + 10 DB engines + 5 CI tools = 19 distinct technologies / 34 services = 0.56. The Java and JavaScript/TypeScript ecosystems each cover ~50% of services, providing some natural standardization. However, the database layer is highly fragmented.
- **Evidence**: Languages: Java (50%), JS (21%), TS (18%), C# (15%), Python (15%). Databases: PostgreSQL (11), Redis (7), MySQL (5), SQLite (5), MongoDB (3), Cassandra (3), Elasticsearch (2), MariaDB (2), OpenSearch (2), H2 (1). Preference alignment: Portfolio currently has 0% alignment with preferred technologies (eks, aurora, dynamodb, api-gateway, eventbridge, bedrock) — all are targets, not current state.
- **Recommendation**: Consolidate database engines to 3 target platforms: Aurora PostgreSQL (preferred) for relational, DynamoDB (preferred) for NoSQL, ElastiCache for caching. Accept language diversity (4 languages is manageable) but standardize on shared deployment patterns per language.
- **Contextual Annotations**: This finding provides context for DATA-Q3 (Foundational Blocker #14) — database migration is complicated by the variety of source engines.

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: There is no centralized security posture across the portfolio. No shared WAF, no centralized security scanning pipeline, no unified vulnerability management, no consistent IAM patterns. SEC-Q1 (IAM) average is 1.1, SEC-Q4 (dependency scanning) average is 1.6, SEC-Q7 (security pipeline) average is 1.9. Some services have Dependabot enabled independently, but there is no portfolio-wide security governance.
- **Evidence**: SEC-Q1: 30 services score 1 (no IAM). SEC-Q4: 20 services score 1 (no dependency scanning). SEC-Q7: 13 services score 1 (no security pipeline). No shared WAF WebACL detected. No centralized Secrets Manager configuration.
- **Recommendation**: Deploy centralized security controls: (1) Enable Dependabot and CodeQL across all 34 repositories via GitHub organization settings. (2) Create shared IAM role templates per service archetype. (3) Deploy AWS WAF with shared WebACL for all API-facing services. (4) Implement AWS Secrets Manager with cross-account secret sharing for shared credentials.
- **Contextual Annotations**: This finding amplifies SEC-Q1 (Foundational Blocker #16), SEC-Q4 (#18), and SEC-Q6 (#17). A centralized security posture deployment in Phase 0 would address the root cause across all three blockers.

### Portfolio-Level Score Average

- **PORT-MOD-Q1**: 1 (IaC Standardization)
- **PORT-MOD-Q2**: 1 (Shared Observability Platform)
- **PORT-MOD-Q3**: 4 (Dependency Cycle Health)
- **PORT-MOD-Q4**: 2 (Technology Diversity)
- **PORT-MOD-Q5**: 1 (Shared Security Posture)
- **Average**: 1.80 / 4.0

---

## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| akveo--ngx-admin | application | P2 | 1.51 | 1.57 | 1.75 | 2.25 | 1.0 | 1.0 | 3 of 7 | 1 |
| coreui--coreui-free-angular-admin-template | application | P2 | 1.55 | 1.57 | 2.25 | 1.75 | 1.17 | 1.0 | 2 of 7 | 1 |
| getlift--lift | application | P2 | 1.60 | 1.3 | 2.5 | 1.8 | 1.2 | 1.1 | 1 of 7 | 1 |
| motdotla--node-lambda | application | P2 | 1.60 | 1.17 | 2.0 | 1.75 | 1.83 | 1.25 | 1 of 7 | 1 |
| greenshot--greenshot | monorepo | P2 | 1.68 | 1.17 | 2.0 | 2.75 | 1.5 | 1.0 | 1 of 7 | 1 |
| umami-software--umami | monorepo | P2 | 1.70 | 1.2 | 2.2 | 2.8 | 1.1 | 1.1 | 4 of 7 | 2 |
| tqdm--tqdm | application | P2 | 1.76 | 1.33 | 2.75 | 1.75 | 1.33 | 1.63 | 1 of 7 | 2 |
| dwyl--aws-sdk-mock | application | P2 | 1.80 | 1.33 | 3.0 | 1.75 | 1.67 | 1.25 | 1 of 7 | 2 |
| Netflix--eureka | monorepo | P2 | 1.82 | 1.13 | 2.33 | 3.25 | 1.17 | 1.22 | 2 of 7 | 2 |
| Lidarr--Lidarr | monorepo | P2 | 1.84 | 1.4 | 2.67 | 2.5 | 1.43 | 1.22 | 4 of 7 | 2 |
| realworld-apps--angular-realworld-example-app | application | P2 | 1.84 | 1.17 | 2.5 | 2.5 | 1.67 | 1.38 | 2 of 7 | 2 |
| gulpjs--gulp | application | P2 | 1.88 | 1.33 | 3.0 | 2.5 | 1.17 | 1.38 | 2 of 7 | 2 |
| Radarr--Radarr | monorepo | P2 | 1.90 | 1.4 | 2.7 | 2.5 | 1.4 | 1.4 | 4 of 7 | 2 |
| Prowlarr--Prowlarr | monorepo | P2 | 1.93 | 1.4 | 2.5 | 3.0 | 1.43 | 1.33 | 4 of 7 | 2 |
| arrow-py--arrow | application | P2 | 1.93 | 1.71 | 3.75 | 1.75 | 1.33 | 1.13 | 2 of 7 | 2 |
| OpenAPITools--openapi-generator | application | P2 | 1.94 | 1.71 | 2.0 | 3.25 | 1.5 | 1.22 | 1 of 7 | 2 |
| Sonarr--Sonarr | monorepo | P2 | 1.96 | 1.5 | 3.0 | 2.75 | 1.33 | 1.22 | 4 of 7 | 2 |
| thingsboard--thingsboard | monorepo | P2 | 1.96 | 1.36 | 2.83 | 2.5 | 1.57 | 1.56 | 3 of 7 | 2 |
| scality--backbeat | application | P2 | 2.04 | 1.36 | 2.67 | 2.75 | 1.43 | 2.0 | 4 of 7 | 2 |
| scality--cloudserver | application | P2 | 2.08 | 1.27 | 2.33 | 2.75 | 2.14 | 1.89 | 3 of 7 | 2 |
| apache--flink-connector-aws | monorepo | P2 | 2.10 | 1.3 | 3.3 | 2.5 | 1.8 | 1.6 | 1 of 7 | 3 |
| conductor-oss--conductor | monorepo | P2 | 2.10 | 1.6 | 3.0 | 3.0 | 1.3 | 1.6 | 3 of 7 | 3 |
| Graylog2--graylog2-server | monorepo | P2 | 2.12 | 1.3 | 2.5 | 3.0 | 2.14 | 1.67 | 4 of 7 | 3 |
| FlowiseAI--Flowise | monorepo | P2 | 2.14 | 1.27 | 2.67 | 3.0 | 1.86 | 1.89 | 3 of 7 | 3 |
| getsentry--sentry-python | application | P2 | 2.14 | 1.71 | 3.25 | 1.75 | 2.0 | 2.0 | 1 of 7 | 3 |
| iterative--dvc | application | P2 | 2.15 | 1.33 | 2.5 | 3.5 | 1.67 | 1.75 | 2 of 7 | 3 |
| webpack--webpack | application | P2 | 2.15 | 1.71 | 3.0 | 2.5 | 1.67 | 1.88 | 1 of 7 | 3 |
| openzipkin--zipkin | monorepo | P2 | 2.18 | 1.36 | 3.33 | 2.75 | 1.57 | 1.89 | 2 of 7 | 3 |
| zappa--Zappa | application | P2 | 2.19 | 1.71 | 2.75 | 2.75 | 2.0 | 1.75 | 1 of 7 | 3 |
| ToolJet--ToolJet | monorepo | P2 | 2.30 | 2.0 | 2.7 | 3.0 | 2.0 | 2.0 | 2 of 7 | 3 |
| Alluxio--alluxio | monorepo | P2 | 2.31 | 1.82 | 2.5 | 3.75 | 1.57 | 1.89 | 2 of 7 | 3 |
| hapifhir--hapi-fhir | monorepo | P2 | 2.35 | 1.75 | 3.17 | 3.0 | 2.17 | 1.67 | 2 of 7 | 3 |
| apache--druid | monorepo | P2 | 2.41 | 1.45 | 3.67 | 3.5 | 1.86 | 1.56 | 2 of 7 | 3 |
| serverless--serverless | monorepo | P2 | 2.78 | 2.0 | 3.75 | 3.0 | 2.67 | 2.5 | 1 of 7 | 3 |

### Individual Service Details

#### akveo--ngx-admin

- **Overall Score**: 1.51 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.57
  - Application Architecture: 1.75
  - Data Platform: 2.25
  - Security Baseline: 1.0
  - Operations & Observability: 1.0
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Modern DevOps
- **Roadmap Phase**: Phase 1

#### coreui--coreui-free-angular-admin-template

- **Overall Score**: 1.55 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.57
  - Application Architecture: 2.25
  - Data Platform: 1.75
  - Security Baseline: 1.17
  - Operations & Observability: 1.0
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Containers, Move to Modern DevOps
- **Roadmap Phase**: Phase 1

#### getlift--lift

- **Overall Score**: 1.60 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.3
  - Application Architecture: 2.5
  - Data Platform: 1.8
  - Security Baseline: 1.2
  - Operations & Observability: 1.1
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 1

#### motdotla--node-lambda

- **Overall Score**: 1.60 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.17
  - Application Architecture: 2.0
  - Data Platform: 1.75
  - Security Baseline: 1.83
  - Operations & Observability: 1.25
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 1

#### greenshot--greenshot

- **Overall Score**: 1.68 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.17
  - Application Architecture: 2.0
  - Data Platform: 2.75
  - Security Baseline: 1.5
  - Operations & Observability: 1.0
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 1

#### umami-software--umami

- **Overall Score**: 1.70 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.2
  - Application Architecture: 2.2
  - Data Platform: 2.8
  - Security Baseline: 1.1
  - Operations & Observability: 1.1
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q3: score 1 — API Gateway / Load Balancer
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### tqdm--tqdm

- **Overall Score**: 1.76 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.33
  - Application Architecture: 2.75
  - Data Platform: 1.75
  - Security Baseline: 1.33
  - Operations & Observability: 1.63
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### dwyl--aws-sdk-mock

- **Overall Score**: 1.80 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.33
  - Application Architecture: 3.0
  - Data Platform: 1.75
  - Security Baseline: 1.67
  - Operations & Observability: 1.25
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### Netflix--eureka

- **Overall Score**: 1.82 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.13
  - Application Architecture: 2.33
  - Data Platform: 3.25
  - Security Baseline: 1.17
  - Operations & Observability: 1.22
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q3: score 1 — API Gateway / Load Balancer
  - INF-Q4: score 1 — Event-Driven / Messaging
- **Triggered Pathways**: Move to Containers, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### Lidarr--Lidarr

- **Overall Score**: 1.84 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.4
  - Application Architecture: 2.67
  - Data Platform: 2.5
  - Security Baseline: 1.43
  - Operations & Observability: 1.22
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### realworld-apps--angular-realworld-example-app

- **Overall Score**: 1.84 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.17
  - Application Architecture: 2.5
  - Data Platform: 2.5
  - Security Baseline: 1.67
  - Operations & Observability: 1.38
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Containers, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### gulpjs--gulp

- **Overall Score**: 1.88 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.33
  - Application Architecture: 3.0
  - Data Platform: 2.5
  - Security Baseline: 1.17
  - Operations & Observability: 1.38
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Containers, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### Radarr--Radarr

- **Overall Score**: 1.90 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.4
  - Application Architecture: 2.7
  - Data Platform: 2.5
  - Security Baseline: 1.4
  - Operations & Observability: 1.4
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### Prowlarr--Prowlarr

- **Overall Score**: 1.93 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.4
  - Application Architecture: 2.5
  - Data Platform: 3.0
  - Security Baseline: 1.43
  - Operations & Observability: 1.33
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q4: score 1 — Event-Driven / Messaging
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### arrow-py--arrow

- **Overall Score**: 1.93 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.71
  - Application Architecture: 3.75
  - Data Platform: 1.75
  - Security Baseline: 1.33
  - Operations & Observability: 1.13
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Containers, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### OpenAPITools--openapi-generator

- **Overall Score**: 1.94 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.71
  - Application Architecture: 2.0
  - Data Platform: 3.25
  - Security Baseline: 1.5
  - Operations & Observability: 1.22
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### Sonarr--Sonarr

- **Overall Score**: 1.96 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-14
- **Category Scores**:
  - Infrastructure & DevOps: 1.5
  - Application Architecture: 3.0
  - Data Platform: 2.75
  - Security Baseline: 1.33
  - Operations & Observability: 1.22
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### thingsboard--thingsboard

- **Overall Score**: 1.96 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.36
  - Application Architecture: 2.83
  - Data Platform: 2.5
  - Security Baseline: 1.57
  - Operations & Observability: 1.56
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### scality--backbeat

- **Overall Score**: 2.04 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-14
- **Category Scores**:
  - Infrastructure & DevOps: 1.36
  - Application Architecture: 2.67
  - Data Platform: 2.75
  - Security Baseline: 1.43
  - Operations & Observability: 2.0
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### scality--cloudserver

- **Overall Score**: 2.08 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.27
  - Application Architecture: 2.33
  - Data Platform: 2.75
  - Security Baseline: 2.14
  - Operations & Observability: 1.89
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q4: score 1 — Event-Driven / Messaging
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 2

#### apache--flink-connector-aws

- **Overall Score**: 2.10 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.3
  - Application Architecture: 3.3
  - Data Platform: 2.5
  - Security Baseline: 1.8
  - Operations & Observability: 1.6
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q4: score 1 — Event-Driven / Messaging
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### conductor-oss--conductor

- **Overall Score**: 2.10 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.6
  - Application Architecture: 3.0
  - Data Platform: 3.0
  - Security Baseline: 1.3
  - Operations & Observability: 1.6
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### Graylog2--graylog2-server

- **Overall Score**: 2.12 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-25
- **Category Scores**:
  - Infrastructure & DevOps: 1.3
  - Application Architecture: 2.5
  - Data Platform: 3.0
  - Security Baseline: 2.14
  - Operations & Observability: 1.67
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### FlowiseAI--Flowise

- **Overall Score**: 2.14 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-14
- **Category Scores**:
  - Infrastructure & DevOps: 1.27
  - Application Architecture: 2.67
  - Data Platform: 3.0
  - Security Baseline: 1.86
  - Operations & Observability: 1.89
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### getsentry--sentry-python

- **Overall Score**: 2.14 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-17
- **Category Scores**:
  - Infrastructure & DevOps: 1.71
  - Application Architecture: 3.25
  - Data Platform: 1.75
  - Security Baseline: 2.0
  - Operations & Observability: 2.0
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### iterative--dvc

- **Overall Score**: 2.15 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.33
  - Application Architecture: 2.5
  - Data Platform: 3.5
  - Security Baseline: 1.67
  - Operations & Observability: 1.75
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps, Move to AI
- **Roadmap Phase**: Phase 3

#### webpack--webpack

- **Overall Score**: 2.15 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.71
  - Application Architecture: 3.0
  - Data Platform: 2.5
  - Security Baseline: 1.67
  - Operations & Observability: 1.88
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### openzipkin--zipkin

- **Overall Score**: 2.18 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.36
  - Application Architecture: 3.33
  - Data Platform: 2.75
  - Security Baseline: 1.57
  - Operations & Observability: 1.89
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### zappa--Zappa

- **Overall Score**: 2.19 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 1.71
  - Application Architecture: 2.75
  - Data Platform: 2.75
  - Security Baseline: 2.0
  - Operations & Observability: 1.75
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### ToolJet--ToolJet

- **Overall Score**: 2.30 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-01
- **Category Scores**:
  - Infrastructure & DevOps: 2.0
  - Application Architecture: 2.7
  - Data Platform: 3.0
  - Security Baseline: 2.0
  - Operations & Observability: 2.0
- **Top Gaps**:
  - INF-Q7: score 1 — Multi-AZ Resilience
  - INF-Q8: score 1 — Auto-Scaling
  - SEC-Q1: score 1 — IAM & Access Control
- **Triggered Pathways**: Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### Alluxio--alluxio

- **Overall Score**: 2.31 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.82
  - Application Architecture: 2.5
  - Data Platform: 3.75
  - Security Baseline: 1.57
  - Operations & Observability: 1.89
- **Top Gaps**:
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q7: score 1 — Multi-AZ Resilience
- **Triggered Pathways**: Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### hapifhir--hapi-fhir

- **Overall Score**: 2.35 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.75
  - Application Architecture: 3.17
  - Data Platform: 3.0
  - Security Baseline: 2.17
  - Operations & Observability: 1.67
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### apache--druid

- **Overall Score**: 2.41 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2026-04-30
- **Category Scores**:
  - Infrastructure & DevOps: 1.45
  - Application Architecture: 3.67
  - Data Platform: 3.5
  - Security Baseline: 1.86
  - Operations & Observability: 1.56
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q2: score 1 — Managed Database Services
  - INF-Q5: score 1 — Network Security Architecture
- **Triggered Pathways**: Move to Managed Databases, Move to Modern DevOps
- **Roadmap Phase**: Phase 3

#### serverless--serverless

- **Overall Score**: 2.78 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: 2025-07-16
- **Category Scores**:
  - Infrastructure & DevOps: 2.0
  - Application Architecture: 3.75
  - Data Platform: 3.0
  - Security Baseline: 2.67
  - Operations & Observability: 2.5
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security Architecture
  - INF-Q6: score 1 — Container-Readiness
- **Triggered Pathways**: Move to Modern DevOps
- **Roadmap Phase**: Phase 3

---


## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | akveo--ngx-admin | services/akveo--ngx-admin/modernization-assessment/akveo--ngx-admin-mod-report.md | 2026-04-30 | application | 1.51 |
| 2 | coreui--coreui-free-angular-admin-template | services/coreui--coreui-free-angular-admin-template/modernization-assessment/coreui--coreui-free-angular-admin-template-mod-report.md | 2026-04-30 | application | 1.55 |
| 3 | getlift--lift | services/getlift--lift/modernization-assessment/getlift--lift-mod-report.md | 2025-07-16 | application | 1.60 |
| 4 | motdotla--node-lambda | services/motdotla--node-lambda/modernization-assessment/motdotla--node-lambda-mod-report.md | 2026-04-30 | application | 1.60 |
| 5 | greenshot--greenshot | services/greenshot--greenshot/modernization-assessment/greenshot--greenshot-mod-report.md | 2026-04-30 | monorepo | 1.68 |
| 6 | umami-software--umami | services/umami-software--umami/modernization-assessment/umami-software--umami-mod-report.md | 2026-04-30 | monorepo | 1.70 |
| 7 | tqdm--tqdm | services/tqdm--tqdm/modernization-assessment/tqdm--tqdm-mod-report.md | 2025-07-16 | application | 1.76 |
| 8 | dwyl--aws-sdk-mock | services/dwyl--aws-sdk-mock/modernization-assessment/dwyl--aws-sdk-mock-mod-report.md | 2025-07-16 | application | 1.80 |
| 9 | Netflix--eureka | services/Netflix--eureka/modernization-assessment/Netflix--eureka-mod-report.md | 2025-07-15 | monorepo | 1.82 |
| 10 | Lidarr--Lidarr | services/Lidarr--Lidarr/modernization-assessment/Lidarr--Lidarr-mod-report.md | 2025-07-15 | monorepo | 1.84 |
| 11 | realworld-apps--angular-realworld-example-app | services/realworld-apps--angular-realworld-example-app/modernization-assessment/realworld-apps--angular-realworld-example-app-mod-report.md | 2025-07-15 | application | 1.84 |
| 12 | gulpjs--gulp | services/gulpjs--gulp/modernization-assessment/gulpjs--gulp-mod-report.md | 2025-07-16 | application | 1.88 |
| 13 | Radarr--Radarr | services/Radarr--Radarr/modernization-assessment/Radarr--Radarr-mod-report.md | 2026-04-30 | monorepo | 1.90 |
| 14 | Prowlarr--Prowlarr | services/Prowlarr--Prowlarr/modernization-assessment/Prowlarr--Prowlarr-mod-report.md | 2025-07-15 | monorepo | 1.93 |
| 15 | arrow-py--arrow | services/arrow-py--arrow/modernization-assessment/arrow-py--arrow-mod-report.md | 2026-04-30 | application | 1.93 |
| 16 | OpenAPITools--openapi-generator | services/OpenAPITools--openapi-generator/modernization-assessment/OpenAPITools--openapi-generator-mod-report.md | 2026-04-30 | application | 1.94 |
| 17 | Sonarr--Sonarr | services/Sonarr--Sonarr/modernization-assessment/Sonarr--Sonarr-mod-report.md | 2025-07-14 | monorepo | 1.96 |
| 18 | thingsboard--thingsboard | services/thingsboard--thingsboard/modernization-assessment/thingsboard--thingsboard-mod-report.md | 2026-04-30 | monorepo | 1.96 |
| 19 | scality--backbeat | services/scality--backbeat/modernization-assessment/scality--backbeat-mod-report.md | 2025-07-14 | application | 2.04 |
| 20 | scality--cloudserver | services/scality--cloudserver/modernization-assessment/scality--cloudserver-mod-report.md | 2025-07-16 | application | 2.08 |
| 21 | apache--flink-connector-aws | services/apache--flink-connector-aws/modernization-assessment/apache--flink-connector-aws-mod-report.md | 2026-04-30 | monorepo | 2.10 |
| 22 | conductor-oss--conductor | services/conductor-oss--conductor/modernization-assessment/conductor-oss--conductor-mod-report.md | 2025-07-15 | monorepo | 2.10 |
| 23 | Graylog2--graylog2-server | services/Graylog2--graylog2-server/modernization-assessment/Graylog2--graylog2-server-mod-report.md | 2025-07-25 | monorepo | 2.12 |
| 24 | FlowiseAI--Flowise | services/FlowiseAI--Flowise/modernization-assessment/FlowiseAI--Flowise-mod-report.md | 2025-07-14 | monorepo | 2.14 |
| 25 | getsentry--sentry-python | services/getsentry--sentry-python/modernization-assessment/getsentry--sentry-python-mod-report.md | 2025-07-17 | application | 2.14 |
| 26 | iterative--dvc | services/iterative--dvc/modernization-assessment/iterative--dvc-mod-report.md | 2025-07-16 | application | 2.15 |
| 27 | webpack--webpack | services/webpack--webpack/modernization-assessment/webpack--webpack-mod-report.md | 2025-07-15 | application | 2.15 |
| 28 | openzipkin--zipkin | services/openzipkin--zipkin/modernization-assessment/openzipkin--zipkin-mod-report.md | 2026-04-30 | monorepo | 2.18 |
| 29 | zappa--Zappa | services/zappa--Zappa/modernization-assessment/zappa--Zappa-mod-report.md | 2025-07-16 | application | 2.19 |
| 30 | ToolJet--ToolJet | services/ToolJet--ToolJet/modernization-assessment/ToolJet--ToolJet-mod-report.md | 2025-07-01 | monorepo | 2.30 |
| 31 | Alluxio--alluxio | services/Alluxio--alluxio/modernization-assessment/Alluxio--alluxio-mod-report.md | 2026-04-30 | monorepo | 2.31 |
| 32 | hapifhir--hapi-fhir | services/hapifhir--hapi-fhir/modernization-assessment/hapifhir--hapi-fhir-mod-report.md | 2026-04-30 | monorepo | 2.35 |
| 33 | apache--druid | services/apache--druid/modernization-assessment/apache--druid-mod-report.md | 2026-04-30 | monorepo | 2.41 |
| 34 | serverless--serverless | services/serverless--serverless/modernization-assessment/serverless--serverless-mod-report.md | 2025-07-16 | monorepo | 2.78 |
