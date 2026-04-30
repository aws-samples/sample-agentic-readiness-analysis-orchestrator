# Portfolio Modernization Readiness Assessment Report

**Date**: 2025-07-22
**Services Assessed**: 34
**Portfolio Context**: 34 open-source project mirrors for ATX TD validation across multiple languages, architectures, and domains.
**Technology Preferences**: Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock; Avoid: self-managed-kafka, self-managed-kubernetes, oracle

---

## 1. Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 2.04 / 4.0 |
| Score Range | 1.33 – 2.83 |
| Score Standard Deviation | 0.30 |
| Highest Scoring Service | getlift--lift (2.83) |
| Lowest Scoring Service | greenshot--greenshot (1.33) |
| Pathways Triggered (portfolio-wide) | 6 of 7 |
| Cross-Cutting Foundational Blockers | 33 |
| Cross-Cutting Improvement Opportunities | 2 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0.0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 2 | 5.9% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 31 | 91.2% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 1 | 2.9% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 1.59 | 1.09 | 3.64 | 0 |
| Application Architecture (APP) | 2.80 | 1.50 | 3.83 | 0 |
| Data Platform (DATA) | 2.69 | 1.75 | 4.00 | 0 |
| Security Baseline (SEC) | 1.63 | 1.00 | 2.29 | 0 |
| Operations & Observability (OPS) | 1.48 | 1.00 | 2.00 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 16 | 47.1% |
| monorepo | 18 | 52.9% |
| infrastructure-only | 0 | 0.0% |
| deployment-config | 0 | 0.0% |
| library | 0 | 0.0% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2025-07-22 |
| total_services | 34 |
| portfolio_score | 2.04 |
| score_range_min | 1.33 |
| score_range_max | 2.83 |
| mature_services | 0 |
| partial_services | 2 |
| needs_work_services | 31 |
| not_ready_services | 1 |
| pathways_triggered | 6 |
| foundational_blockers | 33 |
| improvement_opportunities | 2 |
| category_inf | 1.59 |
| category_app | 2.80 |
| category_data | 2.69 |
| category_sec | 1.63 |
| category_ops | 1.48 |
| portfolio_level_avg | 1.40 |

---

## 2. Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| Java | 10 | 29.4% |
| JavaScript | 10 | 29.4% |
| TypeScript | 7 | 20.6% |
| Python | 5 | 14.7% |
| C# | 5 | 14.7% |
| HTML | 2 | 5.9% |

> Note: Some services use multiple languages (e.g., FlowiseAI--Flowise uses both TypeScript and JavaScript), so percentages sum to >100%.

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| PostgreSQL | Relational | 10 | Mixed |
| SQLite | Relational | 5 | Self-managed |
| Redis | Cache | 4 | Mixed |
| MySQL | Relational | 3 | Mixed |
| MongoDB | NoSQL | 3 | Self-managed |
| Elasticsearch/OpenSearch | NoSQL | 3 | Mixed |
| Cassandra | NoSQL | 2 | Self-managed |
| Apache Derby | Relational | 1 | Self-managed |
| MS SQL Server | Relational | 1 | Managed |
| RocksDB | NoSQL (embedded) | 1 | Self-managed |

**Database Distribution**: 1 managed (MS SQL Server via RDS), 17 self-managed instances across services, 1 commercial (MS SQL Server), all others open source.

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| Containers (Docker/Docker Compose) | 17 | 50.0% |
| Serverless (Lambda) | 4 | 11.8% |
| None — Library/SDK/CLI/Build Tool | 9 | 26.5% |
| None — Frontend SPA | 3 | 8.8% |
| Desktop (Windows) | 1 | 2.9% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| Docker Compose | IaC (Container orchestration) | 17 |
| Serverless Framework | IaC (Serverless) | 3 |
| Helm | IaC (Kubernetes) | 1 |
| CDK | IaC (AWS) | 1 |
| None (No IaC) | — | 14 |
| GitHub Actions | CI/CD | 33 |
| Travis CI | CI/CD | 3 |
| Jenkins | CI/CD | 1 |
| CircleCI | CI/CD | 1 |
| Azure Pipelines | CI/CD | 1 |

### Standardization Opportunities

- **CI/CD is nearly standardized**: 33 of 34 services (97%) use GitHub Actions. The 3 Travis CI instances (akveo--ngx-admin, dwyl--aws-sdk-mock, motdotla--node-lambda) and 1 each of Jenkins, CircleCI, and Azure Pipelines are consolidation candidates. **Recommendation**: Migrate all CI/CD to GitHub Actions.
- **IaC is highly fragmented**: 14 services (41%) have zero IaC. Of the 20 that do, Docker Compose dominates (17) but only provides local/dev orchestration, not cloud infrastructure. Only 1 service uses CDK and 1 uses Helm. **Recommendation**: Adopt AWS CDK or Terraform as the standard cloud IaC tool. Docker Compose serves development only; cloud infrastructure needs dedicated IaC.
- **Preference alignment**: The portfolio preference for **EKS** is poorly aligned — zero services currently use EKS or Kubernetes manifests. The preference for **Aurora** is partially aligned — 10 services use PostgreSQL which is Aurora-compatible. The preference to **avoid oracle** is fully met — no Oracle databases detected. The preference to **avoid self-managed-kafka** is met — no Kafka instances found. The preference to **avoid self-managed-kubernetes** is met — no self-managed Kubernetes detected.
- **Technology diversity score**: 10+ distinct languages/frameworks, 10+ distinct database engines, 5 CI/CD platforms, 5 IaC approaches across 34 services = **high diversity** (characteristic of an independent open-source portfolio rather than a unified enterprise estate).
- **Language consolidation candidates**: HTML-only repos (2) are really TypeScript/Angular apps. The 5 primary language families (Java, JavaScript/TypeScript, Python, C#) reflect genuine domain diversity rather than unnecessary fragmentation.

---

## 3. Service Dependency Map

> Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Inferred Dependency Overview

| Source Service | Target Service | Type | Coupling | Description |
|---------------|---------------|------|----------|-------------|
| scality--backbeat | scality--cloudserver | sync | Medium | Backbeat is the replication/lifecycle engine for CloudServer; shares MongoDB and Redis data stores |
| scality--cloudserver | scality--backbeat | async | Medium | CloudServer triggers lifecycle and replication workflows in Backbeat |
| Sonarr--Sonarr | Prowlarr--Prowlarr | sync | Low | Sonarr uses Prowlarr as indexer proxy for search queries |
| Radarr--Radarr | Prowlarr--Prowlarr | sync | Low | Radarr uses Prowlarr as indexer proxy for search queries |
| Lidarr--Lidarr | Prowlarr--Prowlarr | sync | Low | Lidarr uses Prowlarr as indexer proxy for search queries |
| scality--backbeat | MongoDB (external) | shared_db | High | Shared MongoDB metadata store |
| scality--cloudserver | MongoDB (external) | shared_db | High | Shared MongoDB metadata store |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| Prowlarr--Prowlarr | 3 | 0 | 11.8% | Foundation | 1.80 |
| scality--cloudserver | 1 | 1 | 8.8% | Internal | 2.12 |
| scality--backbeat | 1 | 1 | 8.8% | Internal | 1.94 |
| Sonarr--Sonarr | 0 | 1 | 0.0% | Leaf | 1.97 |
| Radarr--Radarr | 0 | 1 | 0.0% | Leaf | 1.82 |
| Lidarr--Lidarr | 0 | 1 | 0.0% | Leaf | 1.87 |
| All other services (28) | 0 | 0 | 0.0% | Independent | — |

### Foundation Services (High Fan-In)

- **Prowlarr--Prowlarr** (Fan-In: 3) — Indexer proxy for the *arr suite. Sonarr, Radarr, and Lidarr all depend on Prowlarr for search functionality. Score: 1.80 — needs modernization before dependent services.

### Circular Dependencies

⚠️ **Circular dependency detected** — this should be resolved in Phase 0:
- Cycle: **scality--backbeat** ↔ **scality--cloudserver** (sync + async bidirectional dependency via shared MongoDB and lifecycle triggers)
- Resolution: Decouple via EventBridge (preferred) or SQS event-based communication rather than direct synchronous calls. Migrate shared MongoDB to separate data stores or introduce an API boundary.

### Critical Path Analysis

The dependency graph is sparse — most services (28 of 34) are fully independent with no inter-service dependencies. The two dependency clusters are:

1. **Scality cluster**: scality--backbeat ↔ scality--cloudserver (circular, needs Phase 0 resolution)
2. ***arr suite**: Prowlarr--Prowlarr → {Sonarr, Radarr, Lidarr} (Prowlarr must modernize first)

The longest dependency chain is 2 hops (Sonarr → Prowlarr), meaning 2 sequential phases suffice for dependency ordering. The majority of services can be modernized in parallel.

---

## 4. Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.

1. **OPS-Q7: Runbooks & Automation** — 33 of 34 services score < 2
   - **Score Distribution**: Score 1: 33 services; Score 2: 1 service
   - **Impact**: No operational runbooks or automated remediation exists across virtually the entire portfolio. Incident response is entirely manual and undocumented, creating operational risk at scale.
   - **Affected Services**: All except getlift--lift
   - **Portfolio-Level Recommendation**: Create a shared runbook template library. Establish standard incident response procedures. Implement AWS Systems Manager Automation documents for common operational tasks (restart, failover, scaling). Prioritize runbooks for the highest-blast-radius services first.

2. **INF-Q7: Disaster Recovery** — 32 of 34 services score < 2
   - **Score Distribution**: Score 1: 32 services; Score 3: 2 services
   - **Impact**: No disaster recovery plans, backup strategies, or recovery point/time objectives (RPO/RTO) defined for 94% of services. A regional failure would result in complete data loss and extended downtime.
   - **Affected Services**: All except getlift--lift, apache--druid
   - **Portfolio-Level Recommendation**: Define RPO/RTO targets for each service tier. Implement AWS Backup for all data stores. For critical services, deploy multi-region failover. Start with services that manage persistent data (PostgreSQL, MongoDB, Redis users).

3. **OPS-Q9: Chaos Engineering / Resilience Testing** — 32 of 34 services score < 2
   - **Score Distribution**: Score 1: 32 services; Score 2: 1 service; Score 3: 1 service
   - **Impact**: No resilience testing or chaos engineering practices. Services have never been tested for failure modes, making production incidents unpredictable and recovery untested.
   - **Affected Services**: All except serverless--serverless, getsentry--sentry-python
   - **Portfolio-Level Recommendation**: Adopt AWS Fault Injection Service (FIS) for portfolio-wide chaos engineering. Start with game days for the highest-blast-radius services. Establish a progressive resilience testing program.

4. **INF-Q5: Multi-AZ / High Availability** — 31 of 34 services score < 2
   - **Score Distribution**: Score 1: 31 services; Score 2: 2 services; Score 3: 1 service
   - **Impact**: Single points of failure across 91% of services. No multi-AZ deployment, no failover capability, no load balancing across availability zones.
   - **Affected Services**: All except getlift--lift, zappa--Zappa, serverless--serverless (Lambda inherently multi-AZ)
   - **Portfolio-Level Recommendation**: Establish a multi-AZ deployment standard. For EKS (preferred), deploy node groups across 3 AZs. For Aurora (preferred), enable multi-AZ read replicas. For serverless services, multi-AZ is automatic.

5. **INF-Q10: Infrastructure as Code Coverage** — 31 of 34 services score < 2
   - **Score Distribution**: Score 1: 31 services; Score 2: 2 services; Score 4: 1 service
   - **Impact**: Zero cloud IaC for 91% of services. Infrastructure is not version-controlled, not reproducible, and cannot be deployed consistently. This blocks all other infrastructure modernization.
   - **Affected Services**: All except getlift--lift (score 4), zappa--Zappa (score 2), ToolJet--ToolJet (score 2)
   - **Portfolio-Level Recommendation**: This is the **#1 foundational blocker**. Adopt AWS CDK (TypeScript) or Terraform as the portfolio-wide IaC standard. Create reusable IaC modules for common patterns (EKS cluster, Aurora database, API Gateway). Roll out IaC adoption in Phase 0 as an organizational enabler.

6. **OPS-Q2: SLOs & SLIs** — 31 of 34 services score < 2
   - **Score Distribution**: Score 1: 31 services; Score 2: 3 services
   - **Impact**: No Service Level Objectives or Indicators defined for 91% of services. Without SLOs, there is no measurable definition of "good enough" service performance, making reliability improvement unquantifiable.
   - **Affected Services**: All except serverless--serverless, scality--cloudserver, getsentry--sentry-python
   - **Portfolio-Level Recommendation**: Define portfolio-wide SLO templates (availability, latency, error rate). Use Amazon CloudWatch SLO targets and composite alarms. Start with externally-facing services.

7. **SEC-Q1: Audit Logging** — 30 of 34 services score < 2
   - **Score Distribution**: Score 1: 30 services; Score 2: 4 services
   - **Impact**: No audit logging for 88% of services. Security events, access patterns, and configuration changes are not tracked, preventing forensic analysis and compliance verification.
   - **Affected Services**: All except conductor-oss--conductor, scality--cloudserver, ToolJet--ToolJet, apache--druid
   - **Portfolio-Level Recommendation**: Enable AWS CloudTrail for all accounts. Implement centralized audit logging via CloudWatch Logs. Adopt a shared logging format standard across services.

8. **SEC-Q2: Encryption (at rest & in transit)** — 30 of 34 services score < 2
   - **Score Distribution**: Score 1: 30 services; Score 2: 2 services; Score 3: 2 services
   - **Impact**: No encryption at rest or in transit for 88% of services. Data is stored and transmitted in plaintext, creating significant security and compliance risk.
   - **Affected Services**: All except scality--cloudserver (score 3), apache--druid (score 3), ToolJet--ToolJet (score 2), serverless--serverless (score 2)
   - **Portfolio-Level Recommendation**: Enable default encryption for all AWS resources (S3 SSE, EBS encryption, RDS encryption). Enforce TLS 1.2+ for all service communication. Use AWS KMS for centralized key management.

9. **OPS-Q4: Alerting & Incident Response** — 30 of 34 services score < 2
   - **Score Distribution**: Score 1: 30 services; Score 2: 4 services
   - **Impact**: No alerting or incident response capability for 88% of services. Issues are detected only when users report them — no proactive monitoring or automated escalation.
   - **Affected Services**: All except scality--cloudserver, scality--backbeat, serverless--serverless, getsentry--sentry-python
   - **Portfolio-Level Recommendation**: Implement Amazon CloudWatch Alarms with SNS notification topics. Establish incident response playbooks. Consider AWS Incident Manager for coordinated response.

10. **INF-Q2: Managed Databases** — 29 of 34 services score < 2
    - **Score Distribution**: Score 1: 29 services; Score 2: 2 services; Score 3: 1 service; Score 4: 2 services
    - **Impact**: 85% of services have no managed database infrastructure. Databases are either absent, self-managed, or embedded (SQLite). This limits scalability, availability, and operational efficiency.
    - **Affected Services**: All except getlift--lift (score 4), Netflix--eureka (score 4), apache--druid (score 3), Alluxio--alluxio (score 2), iterative--dvc (score 2)
    - **Portfolio-Level Recommendation**: Migrate PostgreSQL workloads to Amazon Aurora PostgreSQL (preferred). Migrate MongoDB workloads to Amazon DocumentDB. Migrate Redis workloads to Amazon ElastiCache. Migrate SQLite workloads to Aurora or DynamoDB (preferred) based on access patterns.

11. **INF-Q6: Scalability & Auto-Scaling** — 29 of 34 services score < 2
    - **Score Distribution**: Score 1: 29 services; Score 2: 4 services; Score 4: 1 service
    - **Impact**: No auto-scaling capability for 85% of services. Services cannot handle traffic spikes and require manual intervention for capacity changes.
    - **Affected Services**: All except getlift--lift (score 4), ToolJet--ToolJet, zappa--Zappa, Alluxio--alluxio, serverless--serverless (score 2 each)
    - **Portfolio-Level Recommendation**: For EKS (preferred): implement Horizontal Pod Autoscaler and Karpenter node autoscaling. For serverless: Lambda auto-scales by default. For Aurora (preferred): enable auto-scaling read replicas.

12. **INF-Q8: Network Architecture** — 29 of 34 services score < 2
    - **Score Distribution**: Score 1: 29 services; Score 2: 4 services; Score 3: 1 service
    - **Impact**: No defined network architecture for 85% of services. No VPCs, subnets, security groups, or network segmentation.
    - **Affected Services**: All except getlift--lift (score 3), ToolJet--ToolJet, zappa--Zappa, Alluxio--alluxio, serverless--serverless (score 2 each)
    - **Portfolio-Level Recommendation**: Create a shared VPC architecture with private/public subnets across 3 AZs. Use VPC endpoints for AWS service access. Implement network segmentation by service tier.

13. **INF-Q9: Cost Optimization** — 29 of 34 services score < 2
    - **Score Distribution**: Score 1: 29 services; Score 2: 3 services; Score 3: 1 service; Score 4: 1 service
    - **Impact**: No cost optimization practices for 85% of services. No tagging strategy, no right-sizing, no reserved capacity planning.
    - **Affected Services**: All except getlift--lift (score 4), apache--druid (score 3), zappa--Zappa, ToolJet--ToolJet, scality--cloudserver (score 2 each)
    - **Portfolio-Level Recommendation**: Implement a portfolio-wide tagging strategy (service, environment, team, cost-center). Enable AWS Cost Explorer and set up budgets. Use Savings Plans for consistent compute workloads.

14. **INF-Q1: Managed Compute** — 26 of 34 services score < 2
    - **Score Distribution**: Score 1: 26 services; Score 2: 5 services; Score 3: 2 services; Score 4: 1 service
    - **Impact**: 76% of services have no managed compute infrastructure. Services are either not deployed to cloud compute, or use unmanaged Docker Compose only.
    - **Affected Services**: 26 services including greenshot--greenshot, realworld-apps--angular-realworld-example-app, coreui--coreui-free-angular-admin-template, and others
    - **Portfolio-Level Recommendation**: For containerized services (17): migrate from Docker Compose to Amazon EKS (preferred). For frontend SPAs (3): deploy to S3 + CloudFront. For serverless services (4): already on Lambda. For libraries/tools (9): compute infrastructure may not apply.

15. **OPS-Q8: Capacity Planning** — 26 of 34 services score < 2
    - **Score Distribution**: Score 1: 26 services; Score 2: 8 services
    - **Impact**: No capacity planning or load testing for 76% of services. Service limits and breaking points are unknown.
    - **Affected Services**: 26 services
    - **Portfolio-Level Recommendation**: Implement load testing with AWS Distributed Load Testing. Establish baseline performance metrics. Define capacity thresholds and scaling triggers.

16. **SEC-Q4: Secrets Management** — 23 of 34 services score < 2
    - **Score Distribution**: Score 1: 23 services; Score 2: 7 services; Score 3: 4 services
    - **Impact**: Secrets (API keys, database credentials, tokens) are hardcoded or stored in plaintext configuration for 68% of services.
    - **Affected Services**: 23 services
    - **Portfolio-Level Recommendation**: Migrate all secrets to AWS Secrets Manager. Implement automatic secret rotation. Remove all hardcoded secrets from code repositories.

17. **OPS-Q1: Distributed Tracing** — 22 of 34 services score < 2
    - **Score Distribution**: Score 1: 22 services; Score 2: 4 services; Score 3: 8 services
    - **Impact**: No distributed tracing for 65% of services. Cross-service request flows cannot be tracked, making debugging production issues extremely difficult.
    - **Affected Services**: 22 services
    - **Portfolio-Level Recommendation**: Adopt AWS X-Ray or OpenTelemetry (ADOT) as the portfolio-wide tracing standard. Implement auto-instrumentation where possible. Prioritize tracing for services with high fan-out.

18. **OPS-Q5: Deployment Strategy** — 20 of 34 services score < 2
    - **Score Distribution**: Score 1: 20 services; Score 2: 11 services; Score 3: 3 services
    - **Impact**: 59% of services deploy directly to production with no staged rollout, no canary, no blue/green, and no rollback capability.
    - **Affected Services**: 20 services
    - **Portfolio-Level Recommendation**: Implement blue/green deployments on EKS (preferred) using Argo Rollouts or EKS-native rolling updates. For Lambda: use weighted aliases for canary deployments. Establish a portfolio deployment standard.

19. **OPS-Q3: Metrics & Dashboards** — 18 of 34 services score < 2
    - **Score Distribution**: Score 1: 18 services; Score 2: 6 services; Score 3: 10 services
    - **Impact**: No operational metrics or dashboards for 53% of services. Service health and performance are invisible to operators.
    - **Affected Services**: 18 services
    - **Portfolio-Level Recommendation**: Deploy Amazon CloudWatch dashboards for all services. Implement standard metric namespaces. Use CloudWatch Container Insights for EKS workloads.

20. **DATA-Q1: Data Architecture** — 16 of 34 services score < 2
    - **Score Distribution**: Score 1: 16 services; Score 2: 3 services; Score 3: 11 services; Score 4: 4 services
    - **Impact**: 47% of services have no formal data architecture — no data models, no schema management, no data governance.
    - **Affected Services**: 16 services including all frontend/library repos
    - **Portfolio-Level Recommendation**: For services with databases, implement schema versioning (Flyway/Liquibase). Establish data governance standards. Define data retention policies.

21. **SEC-Q6: Vulnerability Management** — 16 of 34 services score < 2
    - **Score Distribution**: Score 1: 16 services; Score 2: 12 services; Score 3: 5 services; Score 4: 1 service
    - **Impact**: No vulnerability management for 47% of services. Known CVEs may exist in dependencies without detection or remediation.
    - **Affected Services**: 16 services
    - **Portfolio-Level Recommendation**: Enable Amazon Inspector for all container images. Run `npm audit` / `pip audit` / `dotnet list package --vulnerable` in CI/CD pipelines. Implement Dependabot or Snyk across all repositories.

22. **DATA-Q3: Data Migration Readiness** — 14 of 34 services score < 2
    - **Score Distribution**: Score 1: 14 services; Score 2: 3 services; Score 3: 11 services; Score 4: 6 services
    - **Impact**: 41% of services are not ready for data migration — no abstraction layer, tightly coupled to specific database implementations.
    - **Affected Services**: 14 services
    - **Portfolio-Level Recommendation**: Implement repository/DAO patterns to abstract database access. Use AWS Database Migration Service (DMS) for migration execution. Create migration runbooks for each database type.

23. **SEC-Q7: Security Scanning in CI/CD** — 13 of 34 services score < 2
    - **Score Distribution**: Score 1: 13 services; Score 2: 14 services; Score 3: 7 services
    - **Impact**: No security scanning in CI/CD for 38% of services. Security vulnerabilities can reach production undetected.
    - **Affected Services**: 13 services
    - **Portfolio-Level Recommendation**: Add SAST/DAST scanning to GitHub Actions pipelines. Use Amazon CodeGuru Security or GitHub Advanced Security. Implement container image scanning with ECR scan-on-push.

24. **SEC-Q3: Authentication & Authorization** — 11 of 34 services score < 2
    - **Score Distribution**: Score 1: 11 services; Score 2: 13 services; Score 3: 7 services; Score 4: 3 services
    - **Impact**: No authentication or authorization for 32% of services. Services are either open or use hardcoded/dummy auth.
    - **Affected Services**: 11 services
    - **Portfolio-Level Recommendation**: Implement Amazon Cognito or IAM-based authentication as the portfolio standard. Use API Gateway (preferred) authorizers for API-based services.

25. **APP-Q5: API Design & Versioning** — 9 of 34 services score < 2
    - **Score Distribution**: Score 1: 9 services; Score 2: 10 services; Score 3: 11 services; Score 4: 4 services
    - **Impact**: No API versioning or design standards for 26% of services.
    - **Affected Services**: 9 services
    - **Portfolio-Level Recommendation**: Adopt OpenAPI specification as the portfolio standard. Implement API versioning via URL path or header. Use API Gateway (preferred) for unified API management.

26. **APP-Q6: Error Handling & Resilience** — 10 of 34 services score < 2
    - **Score Distribution**: Score 1: 10 services; Score 2: 4 services; Score 3: 15 services; Score 4: 5 services
    - **Impact**: No structured error handling or resilience patterns for 29% of services. No circuit breakers, retries, or graceful degradation.
    - **Affected Services**: 10 services
    - **Portfolio-Level Recommendation**: Implement circuit breaker patterns (Resilience4j for Java, Polly for C#). Add structured error handling with correlation IDs. Implement retry with exponential backoff for all external calls.

27. **DATA-Q2: Data Access Patterns** — 7 of 34 services score < 2
    - **Score Distribution**: Score 1: 7 services; Score 2: 3 services; Score 3: 11 services; Score 4: 13 services
    - **Impact**: No defined data access patterns for 21% of services.
    - **Affected Services**: 7 services
    - **Portfolio-Level Recommendation**: Implement CQRS or repository patterns for data-heavy services. Use DynamoDB (preferred) for key-value access patterns, Aurora (preferred) for relational patterns.

28. **INF-Q4: Messaging & Streaming** — 7 of 34 services score < 2
    - **Score Distribution**: Score 1: 7 services; Score 2: 3 services; Score 3: 7 services; Score 4: 17 services
    - **Impact**: 21% of services lack event-driven messaging capabilities where they would benefit.
    - **Affected Services**: 7 services
    - **Portfolio-Level Recommendation**: Adopt Amazon EventBridge (preferred) for event-driven architecture. Use SQS for task queuing, SNS for fan-out notifications.

29. **INF-Q3: API Gateway / Load Balancer** — 6 of 34 services score < 2
    - **Score Distribution**: Score 1: 6 services; Score 2: 2 services; Score 3: 5 services; Score 4: 21 services
    - **Impact**: 18% of services lack API gateway or load balancing.
    - **Affected Services**: 6 services
    - **Portfolio-Level Recommendation**: Deploy Amazon API Gateway (preferred) as the unified API entry point. Use ALB for internal service-to-service traffic.

30. **SEC-Q5: Network Security** — 5 of 34 services score < 2
    - **Score Distribution**: Score 1: 5 services; Score 2: 17 services; Score 3: 10 services; Score 4: 2 services
    - **Impact**: No network security controls for 15% of services.
    - **Affected Services**: 5 services
    - **Portfolio-Level Recommendation**: Implement security groups and NACLs for all VPC resources. Use AWS WAF for public-facing endpoints.

31. **APP-Q3: Synchronous Communication** — 3 of 34 services score < 2
    - **Score Distribution**: Score 1: 3 services; Score 2: 3 services; Score 3: 7 services; Score 4: 21 services
    - **Impact**: Overly tight synchronous coupling in 3 services.
    - **Affected Services**: greenshot--greenshot, scality--cloudserver, umami-software--umami
    - **Portfolio-Level Recommendation**: Introduce API Gateway (preferred) and EventBridge (preferred) to decouple synchronous communication patterns.

32. **APP-Q4: Asynchronous Communication** — 2 of 34 services score < 2
    - **Score Distribution**: Score 1: 2 services; Score 2: 4 services; Score 3: 11 services; Score 4: 17 services
    - **Impact**: No async communication patterns in 2 services where they would benefit.
    - **Affected Services**: greenshot--greenshot, realworld-apps--angular-realworld-example-app
    - **Portfolio-Level Recommendation**: Implement EventBridge (preferred) for event-driven patterns.

33. **OPS-Q6: Testing Strategy** — 2 of 34 services score < 2
    - **Score Distribution**: Score 1: 2 services; Score 2: 4 services; Score 3: 22 services; Score 4: 6 services
    - **Impact**: No automated testing in 2 services.
    - **Affected Services**: greenshot--greenshot, akveo--ngx-admin
    - **Portfolio-Level Recommendation**: Establish minimum test coverage thresholds (80% unit test coverage). Implement integration testing in CI/CD pipelines.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking.
> Address as capacity allows or in parallel with other modernization work.

1. **INF-Q11: CI/CD Automation** — 13 of 34 services score < 3
   - **Score Distribution**: Score 1: 1 service; Score 2: 12 services; Score 3: 17 services; Score 4: 4 services
   - **Impact**: While 62% of services have functional CI/CD (score 3+), 38% have partial or no CI/CD automation. Pipelines lack testing stages, approval gates, or rollback capabilities.
   - **Affected Services**: akveo--ngx-admin, arrow-py--arrow, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, greenshot--greenshot, gulpjs--gulp, iterative--dvc, motdotla--node-lambda, realworld-apps--angular-realworld-example-app, scality--backbeat, tqdm--tqdm, umami-software--umami, webpack--webpack
   - **Portfolio-Level Recommendation**: Standardize GitHub Actions pipelines with a shared workflow template that includes: lint → test → build → security scan → deploy-to-staging → approval → deploy-to-production → rollback-on-failure.

2. **APP-Q2: Monolith vs Microservices** — 17 of 34 services score < 3
   - **Score Distribution**: Score 2: 17 services; Score 3: 13 services; Score 4: 4 services
   - **Impact**: 50% of services are monolithic with limited modularization. While monoliths are appropriate for some use cases, the lack of clear module boundaries limits independent scaling and deployment.
   - **Affected Services**: akveo--ngx-admin, Alluxio--alluxio, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, FlowiseAI--Flowise, greenshot--greenshot, gulpjs--gulp, iterative--dvc, Lidarr--Lidarr, motdotla--node-lambda, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, umami-software--umami
   - **Portfolio-Level Recommendation**: Apply the Strangler Fig pattern for services that would benefit from decomposition. Prioritize decomposition for services with high blast radius. For libraries and tools, monolithic architecture is appropriate — no change needed.

### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 1.59 / 4.0**

**Common Patterns:**
- Docker Compose for local development: present in 17 services
- GitHub Actions CI/CD: present in 33 services
- No cloud IaC: present in 31 services

**Critical Gaps:**
1. IaC Coverage (INF-Q10): 31 services score 1 — **the single most impactful gap**. Without IaC, no infrastructure changes are reproducible or automated.
2. Multi-AZ / HA (INF-Q5): 31 services score 1 — single points of failure everywhere
3. Managed Compute (INF-Q1): 26 services score 1 — no cloud-native compute infrastructure
4. Managed Databases (INF-Q2): 29 services score 1 — databases self-managed or absent
5. Disaster Recovery (INF-Q7): 32 services score 1 — no recovery capability

#### Application Architecture

**Portfolio Score: 2.80 / 4.0**

**Common Patterns:**
- Modern frameworks: present in most services (Angular, Spring Boot, NestJS, .NET)
- Health check endpoints: present in ~18 services
- RESTful APIs: present in most backend services

**Critical Gaps:**
1. Monolith Architecture (APP-Q2): 17 services score 2 — limited modularization
2. API Design (APP-Q5): 9 services score 1 — no API versioning
3. Error Handling (APP-Q6): 10 services score 1 — no resilience patterns

#### Data Platform

**Portfolio Score: 2.69 / 4.0**

**Common Patterns:**
- PostgreSQL dominance: 10 services (Aurora-compatible — aligns with preference)
- SQLite for embedded use: 5 services (acceptable for desktop apps)
- No commercial databases: Oracle not found (aligns with avoidance preference)

**Critical Gaps:**
1. Data Architecture (DATA-Q1): 16 services score 1 — no formal data architecture
2. Data Migration Readiness (DATA-Q3): 14 services score 1 — tightly coupled to specific DBs

#### Security Baseline

**Portfolio Score: 1.63 / 4.0**

**Common Patterns:**
- Basic auth in some services: present in ~12 services
- Environment variables for some secrets: present in ~10 services
- TLS for external APIs: present in ~4 services

**Critical Gaps:**
1. Audit Logging (SEC-Q1): 30 services score 1 — no audit trail
2. Encryption (SEC-Q2): 30 services score 1 — no encryption at rest or in transit
3. Secrets Management (SEC-Q4): 23 services score 1 — hardcoded secrets
4. Vulnerability Management (SEC-Q6): 16 services score 1 — no scanning

#### Operations & Observability

**Portfolio Score: 1.48 / 4.0**

**Common Patterns:**
- Basic logging in some services: present in ~15 services
- Unit tests: present in ~28 services
- No operational tooling: pervasive

**Critical Gaps:**
1. Runbooks (OPS-Q7): 33 services score 1 — zero operational documentation
2. Chaos Engineering (OPS-Q9): 32 services score 1 — no resilience testing
3. SLOs (OPS-Q2): 31 services score 1 — no reliability targets
4. Alerting (OPS-Q4): 30 services score 1 — no automated alerting
5. Capacity Planning (OPS-Q8): 26 services score 1 — no load testing

---

## 5. Portfolio Modernization Roadmap

> Dependency-aware phased roadmap with fixed phase names. Services are ordered
> by dependency graph position, then by priority (all P2), then by score (lowest first).

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services before downstream dependents
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Independent services can be modernized concurrently (28 of 34 have no dependencies)
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, break circular dependencies, and address portfolio-wide blockers.

**Cross-Cutting Activities:**
1. **IaC Standardization (INF-Q10)** — Adopt AWS CDK (TypeScript) or Terraform as portfolio standard. Create reusable modules for EKS cluster, Aurora database, API Gateway, VPC networking.
2. **Security Baseline (SEC-Q1, SEC-Q2, SEC-Q4)** — Enable CloudTrail, enforce encryption (KMS), migrate secrets to AWS Secrets Manager across all services.
3. **Observability Foundation (OPS-Q1, OPS-Q2, OPS-Q4)** — Deploy centralized CloudWatch logging, X-Ray tracing, and CloudWatch Alarms with SNS notifications.
4. **CI/CD Template (INF-Q11)** — Create shared GitHub Actions workflow template with lint → test → build → security scan → deploy → rollback stages.
5. **Circular Dependency Resolution** — Decouple scality--backbeat ↔ scality--cloudserver via EventBridge (preferred) event bus instead of direct calls + shared MongoDB.

**Organizational Enablers:**
- Training: IaC (CDK/Terraform), EKS fundamentals, AWS security best practices, CloudWatch/X-Ray
- Tooling: Standardize on CDK, GitHub Actions, CloudWatch, X-Ray, Secrets Manager
- Standards: IaC templates, CI/CD pipeline template, tagging strategy, SLO template, runbook template

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize foundation services and lowest-scoring services. Establish patterns.

**Services in Scope:**

1. **Prowlarr--Prowlarr** (P2, Score: 1.80 / 4.0) — *Foundation service (fan-in: 3)*
   - Current State: C# monorepo, SQLite/PostgreSQL, Docker Compose, no cloud IaC
   - Target State: Containerized on EKS, Aurora PostgreSQL, IaC-managed, CI/CD pipeline
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL, implement IaC, add security baseline
   - Dependencies: None (foundation service)
   - Blocks: Sonarr, Radarr, Lidarr
   - Estimated Effort: High

2. **greenshot--greenshot** (P2, Score: 1.33 / 4.0) — *Lowest scoring service*
   - Current State: C# Windows desktop app, Azure Pipelines CI, no cloud infrastructure
   - Target State: Modernized CI/CD, security scanning, vulnerability management
   - Key Activities: Migrate CI to GitHub Actions, add security scanning, implement secrets management
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Medium

3. **realworld-apps--angular-realworld-example-app** (P2, Score: 1.57 / 4.0)
   - Current State: TypeScript Angular SPA, minimal CI/CD, no cloud deployment
   - Target State: S3 + CloudFront hosting, CDK IaC, full CI/CD pipeline
   - Key Activities: Deploy to S3+CloudFront, add CDK IaC, implement CI/CD pipeline
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Low

4. **coreui--coreui-free-angular-admin-template** (P2, Score: 1.63 / 4.0)
   - Current State: TypeScript Angular SPA, no cloud deployment, no security
   - Target State: S3 + CloudFront hosting, CDK IaC, security baseline
   - Key Activities: Deploy to S3+CloudFront, add CDK IaC, implement security baseline
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Low

5. **akveo--ngx-admin** (P2, Score: 1.73 / 4.0)
   - Current State: TypeScript Angular SPA, Travis CI + GitHub Actions, rsync deployment
   - Target State: S3 + CloudFront hosting, unified GitHub Actions pipeline
   - Key Activities: Retire Travis CI, deploy to S3+CloudFront, add CDK IaC
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Low

6. **umami-software--umami** (P2, Score: 1.73 / 4.0)
   - Current State: TypeScript monorepo, Docker Compose, PostgreSQL/MySQL
   - Target State: EKS deployment, Aurora PostgreSQL, IaC-managed
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL, implement IaC, add observability
   - Dependencies: None
   - Blocks: None
   - Estimated Effort: Medium

7. **scality--backbeat** (P2, Score: 1.94 / 4.0) — *Circular dependency member*
   - Current State: JavaScript app, Docker Compose, MongoDB+Redis, circular dependency with cloudserver
   - Target State: EKS deployment, DocumentDB, ElastiCache, decoupled from cloudserver via EventBridge
   - Key Activities: Break circular dependency (Phase 0), migrate to EKS, adopt managed databases
   - Dependencies: Phase 0 circular dependency resolution
   - Blocks: scality--cloudserver
   - Estimated Effort: High

8. **scality--cloudserver** (P2, Score: 2.12 / 4.0) — *Circular dependency member*
   - Current State: JavaScript app, Docker Compose, MongoDB+Redis, circular dependency with backbeat
   - Target State: EKS deployment, DocumentDB, ElastiCache, decoupled from backbeat via EventBridge
   - Key Activities: Break circular dependency (Phase 0), migrate to EKS, adopt managed databases
   - Dependencies: Phase 0 circular dependency resolution
   - Blocks: scality--backbeat
   - Estimated Effort: High

**Expected Outcomes:**
- Foundation service (Prowlarr) modernized, unblocking *arr suite
- Circular dependency between Scality services resolved
- Pattern established for EKS deployment, Aurora migration, CDK IaC
- Frontend SPA hosting pattern established (S3+CloudFront)

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize services that depend on Phase 1 services. Replicate proven patterns.

**Services in Scope:**

1. **Radarr--Radarr** (P2, Score: 1.82 / 4.0)
   - Dependencies: Prowlarr--Prowlarr (Phase 1)
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL, apply *arr suite patterns from Prowlarr
   - Estimated Effort: Medium

2. **Lidarr--Lidarr** (P2, Score: 1.87 / 4.0)
   - Dependencies: Prowlarr--Prowlarr (Phase 1)
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL, apply *arr suite patterns from Prowlarr
   - Estimated Effort: Medium

3. **Sonarr--Sonarr** (P2, Score: 1.97 / 4.0)
   - Dependencies: Prowlarr--Prowlarr (Phase 1)
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL, apply *arr suite patterns from Prowlarr
   - Estimated Effort: Medium

4. **dwyl--aws-sdk-mock** (P2, Score: 1.81 / 4.0)
   - Key Activities: Modernize CI/CD, add security scanning, improve test coverage
   - Estimated Effort: Low

5. **gulpjs--gulp** (P2, Score: 1.82 / 4.0)
   - Key Activities: Modernize CI/CD, add security scanning, improve test coverage
   - Estimated Effort: Low

6. **motdotla--node-lambda** (P2, Score: 1.84 / 4.0)
   - Key Activities: Modernize Lambda deployment via CDK, add IaC, improve CI/CD
   - Estimated Effort: Medium

7. **OpenAPITools--openapi-generator** (P2, Score: 1.91 / 4.0)
   - Key Activities: Containerize, add security scanning, improve CI/CD
   - Estimated Effort: Medium

8. **conductor-oss--conductor** (P2, Score: 2.01 / 4.0)
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL + ElastiCache, implement IaC
   - Estimated Effort: High

9. **arrow-py--arrow** (P2, Score: 2.04 / 4.0)
   - Key Activities: Modernize CI/CD, add security scanning
   - Estimated Effort: Low

10. **getsentry--sentry-python** (P2, Score: 2.06 / 4.0)
    - Key Activities: Modernize CI/CD, add security scanning
    - Estimated Effort: Low

11. **iterative--dvc** (P2, Score: 2.08 / 4.0)
    - Key Activities: Modernize CI/CD, add IaC for cloud storage backends, improve security
    - Estimated Effort: Medium

12. **tqdm--tqdm** (P2, Score: 1.98 / 4.0)
    - Key Activities: Modernize CI/CD, add security scanning
    - Estimated Effort: Low

**Parallel Tracks:**
- Track A: *arr suite (Radarr, Lidarr, Sonarr) — can run in parallel using Prowlarr patterns
- Track B: Libraries/tools (dwyl, gulpjs, arrow-py, tqdm, getsentry) — independent, can run in parallel
- Track C: Backend services (conductor, motdotla, OpenAPITools, iterative) — independent

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize remaining services, implement advanced capabilities, continuous improvement.

**Services in Scope:**

1. **webpack--webpack** (P2, Score: 2.10 / 4.0)
   - Key Activities: Improve security scanning, modernize CI/CD
   - Estimated Effort: Low

2. **Alluxio--alluxio** (P2, Score: 2.12 / 4.0)
   - Key Activities: Migrate to EKS, implement IaC, add observability
   - Estimated Effort: High

3. **Graylog2--graylog2-server** (P2, Score: 2.15 / 4.0)
   - Key Activities: Migrate to EKS, adopt Amazon OpenSearch, implement IaC
   - Estimated Effort: High

4. **FlowiseAI--Flowise** (P2, Score: 2.16 / 4.0)
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL, implement IaC
   - Estimated Effort: Medium

5. **apache--flink-connector-aws** (P2, Score: 2.16 / 4.0)
   - Key Activities: Improve security, add IaC, modernize CI/CD
   - Estimated Effort: Medium

6. **openzipkin--zipkin** (P2, Score: 2.16 / 4.0)
   - Key Activities: Migrate to EKS, adopt Aurora/OpenSearch, implement IaC
   - Estimated Effort: High

7. **thingsboard--thingsboard** (P2, Score: 2.17 / 4.0)
   - Key Activities: Migrate to EKS, adopt Aurora + DynamoDB, implement IaC
   - Estimated Effort: High

8. **hapifhir--hapi-fhir** (P2, Score: 2.28 / 4.0)
   - Key Activities: Migrate to EKS, adopt Aurora PostgreSQL, implement IaC
   - Estimated Effort: High

9. **Netflix--eureka** (P2, Score: 2.29 / 4.0)
   - Key Activities: Migrate to EKS, implement IaC, add security baseline
   - Estimated Effort: Medium

10. **ToolJet--ToolJet** (P2, Score: 2.35 / 4.0)
    - Key Activities: Migrate to EKS, optimize Aurora PostgreSQL, improve observability
    - Estimated Effort: Medium

11. **serverless--serverless** (P2, Score: 2.37 / 4.0)
    - Key Activities: Improve security scanning, enhance observability
    - Estimated Effort: Low

12. **apache--druid** (P2, Score: 2.48 / 4.0)
    - Key Activities: Migrate to EKS, optimize data platform, improve security
    - Estimated Effort: High

13. **zappa--Zappa** (P2, Score: 2.57 / 4.0)
    - Key Activities: Improve observability, enhance security scanning
    - Estimated Effort: Low

14. **getlift--lift** (P2, Score: 2.83 / 4.0) — *Highest scoring service*
    - Key Activities: Improve observability (OPS-Q7, OPS-Q2), enhance security baseline
    - Estimated Effort: Low

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6+ months with 3–4 parallel tracks
- Phase 0: 1 month (platform team — shared infrastructure, IaC templates, CI/CD templates)
- Phase 1: 1 month (8 services — foundation + lowest scoring)
- Phase 2: 2 months (12 services — dependent + moderate scoring, 3 parallel tracks)
- Phase 3: 2+ months (14 services — remaining + optimization, 3 parallel tracks)

---

## 6. AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 16 | 47.1% | Medium | High |
| Move to Containers | 17 | 50.0% | Medium | Medium |
| Move to Open Source | 0 | 0.0% | Low | — |
| Move to Managed Databases | 22 | 64.7% | High | Medium |
| Move to Managed Analytics | 5 | 14.7% | Low | Medium |
| Move to Modern DevOps | 33 | 97.1% | High | Medium |
| Move to AI | 1 | 2.9% | Low | Medium |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing
a single at-a-glance view of pathway coverage across the portfolio. Each repo appears
in exactly one column per pathway row.

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, akveo--ngx-admin, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, greenshot--greenshot, gulpjs--gulp, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, umami-software--umami | Netflix--eureka, OpenAPITools--openapi-generator, ToolJet--ToolJet, apache--druid, apache--flink-connector-aws, arrow-py--arrow, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, webpack--webpack, zappa--Zappa | — |
| Move to Containers | Alluxio--alluxio, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, akveo--ngx-admin, arrow-py--arrow, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, realworld-apps--angular-realworld-example-app, tqdm--tqdm | FlowiseAI--Flowise, OpenAPITools--openapi-generator, ToolJet--ToolJet, apache--druid, apache--flink-connector-aws, conductor-oss--conductor, getlift--lift, getsentry--sentry-python, greenshot--greenshot, openzipkin--zipkin, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, umami-software--umami, webpack--webpack, zappa--Zappa | — |
| Move to Open Source | — | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — |
| Move to Managed Databases | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, hapifhir--hapi-fhir, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami | Netflix--eureka, OpenAPITools--openapi-generator, apache--flink-connector-aws, arrow-py--arrow, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, iterative--dvc, serverless--serverless, webpack--webpack, zappa--Zappa | — |
| Move to Managed Analytics | Alluxio--alluxio, Graylog2--graylog2-server, scality--backbeat, thingsboard--thingsboard, umami-software--umami | FlowiseAI--Flowise, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, serverless--serverless, tqdm--tqdm, webpack--webpack, zappa--Zappa | — |
| Move to Modern DevOps | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | getlift--lift | — |
| Move to AI | iterative--dvc | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, arrow-py--arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| akveo--ngx-admin | ✅ | ✅ | — | ✅ | — | ✅ | — |
| Alluxio--alluxio | ✅ | ✅ | — | ✅ | ✅ | ✅ | — |
| apache--druid | — | — | — | ✅ | — | ✅ | — |
| apache--flink-connector-aws | — | — | — | — | — | ✅ | — |
| arrow-py--arrow | — | ✅ | — | — | — | ✅ | — |
| conductor-oss--conductor | ✅ | — | — | ✅ | — | ✅ | — |
| coreui--coreui-free-angular-admin-template | ✅ | ✅ | — | ✅ | — | ✅ | — |
| dwyl--aws-sdk-mock | — | ✅ | — | ✅ | — | ✅ | — |
| FlowiseAI--Flowise | ✅ | — | — | ✅ | — | ✅ | — |
| getlift--lift | — | — | — | — | — | — | — |
| getsentry--sentry-python | — | — | — | — | — | ✅ | — |
| Graylog2--graylog2-server | ✅ | ✅ | — | ✅ | ✅ | ✅ | — |
| greenshot--greenshot | ✅ | — | — | — | — | ✅ | — |
| gulpjs--gulp | ✅ | ✅ | — | — | — | ✅ | — |
| hapifhir--hapi-fhir | — | ✅ | — | ✅ | — | ✅ | — |
| iterative--dvc | — | ✅ | — | — | — | ✅ | ✅ |
| Lidarr--Lidarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| motdotla--node-lambda | — | ✅ | — | ✅ | — | ✅ | — |
| Netflix--eureka | — | ✅ | — | — | — | ✅ | — |
| OpenAPITools--openapi-generator | — | — | — | — | — | ✅ | — |
| openzipkin--zipkin | — | — | — | ✅ | — | ✅ | — |
| Prowlarr--Prowlarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| Radarr--Radarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| realworld-apps--angular-realworld-example-app | ✅ | ✅ | — | ✅ | — | ✅ | — |
| scality--backbeat | ✅ | — | — | ✅ | ✅ | ✅ | — |
| scality--cloudserver | ✅ | — | — | ✅ | — | ✅ | — |
| serverless--serverless | — | — | — | — | — | ✅ | — |
| Sonarr--Sonarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| thingsboard--thingsboard | — | — | — | ✅ | ✅ | ✅ | — |
| ToolJet--ToolJet | — | — | — | ✅ | — | ✅ | — |
| tqdm--tqdm | — | ✅ | — | ✅ | — | ✅ | — |
| umami-software--umami | ✅ | — | — | ✅ | ✅ | ✅ | — |
| webpack--webpack | — | — | — | — | — | ✅ | — |
| zappa--Zappa | — | — | — | — | — | ✅ | — |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is often a prerequisite for Move to AI (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps (33 services) — highest priority, enables all other pathways
- **Track 2**: Move to Containers (17 services) + Move to Managed Databases (22 services) — can run concurrently
- **Track 3**: Move to Cloud Native (16 services) — follows containerization
- **Track 4**: Move to Managed Analytics (5 services) + Move to AI (1 service) — advanced capabilities

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: 33 of 34 (97.1%)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q10 < 3: affects 33 services (IaC gap)
  - INF-Q11 < 3: affects 13 services (CI/CD gap)
  - OPS-Q5 < 3: affects 31 services (deployment strategy gap)
  - OPS-Q6 < 3: affects 6 services (testing strategy gap)
- **Representative AWS Services**: AWS CDK (TypeScript), GitHub Actions, Amazon ECR, AWS CodePipeline, AWS CloudFormation
- **Key Activities**:
  1. Portfolio: Adopt CDK as standard IaC tool; create shared GitHub Actions workflow templates
  2. Per-service: Implement IaC for all infrastructure; add test/security stages to CI/CD
- **Cross-Service Synergies**: Shared CDK constructs, reusable GitHub Actions workflows, standard deployment patterns
- **Estimated Effort**: Medium across 33 services
- **Roadmap Phase Alignment**: Phase 0 (IaC foundation) + Phase 1-3 (service-specific)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to Managed Databases

- **Services Affected**: 22 of 34 (64.7%)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q2 < 3: affects 31 services (no managed databases)
- **Representative AWS Services**: Amazon Aurora PostgreSQL (preferred), Amazon DynamoDB (preferred), Amazon DocumentDB, Amazon ElastiCache, AWS DMS
- **Key Activities**:
  1. Portfolio: Establish Aurora PostgreSQL as the default relational database; DynamoDB for key-value patterns
  2. Per-service: Migrate self-managed PostgreSQL to Aurora, MongoDB to DocumentDB, Redis to ElastiCache, SQLite to Aurora/DynamoDB
- **Cross-Service Synergies**: 10 services use PostgreSQL — shared Aurora cluster templates; 4 services use Redis — shared ElastiCache patterns
- **Estimated Effort**: Medium across 22 services
- **Roadmap Phase Alignment**: Phase 1-2 (database migrations)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Containers

- **Services Affected**: 17 of 34 (50.0%)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q1 < 3: affects 31 services (no managed compute)
  - No Dockerfile or container orchestration defined
- **Representative AWS Services**: Amazon EKS (preferred), Amazon ECR, AWS Fargate, Amazon EKS Auto Mode
- **Key Activities**:
  1. Portfolio: Create EKS cluster template in CDK; establish container build standards
  2. Per-service: Write Dockerfiles, create Kubernetes manifests, deploy to EKS
- **Cross-Service Synergies**: Shared EKS cluster across services; common Helm charts for standard patterns
- **Estimated Effort**: Medium across 17 services
- **Roadmap Phase Alignment**: Phase 1 (containerize foundation services) + Phase 2 (remaining)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

#### Move to Cloud Native

- **Services Affected**: 16 of 34 (47.1%)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - APP-Q2 < 3: affects 17 services (monolithic architecture)
  - INF-Q1 < 3: affects 31 services (no cloud-native compute)
- **Representative AWS Services**: Amazon EKS (preferred), Amazon API Gateway (preferred), Amazon EventBridge (preferred), AWS App Mesh
- **Key Activities**:
  1. Portfolio: Define microservices decomposition patterns; establish API Gateway as entry point
  2. Per-service: Apply Strangler Fig pattern; extract shared services; implement API Gateway routing
- **Cross-Service Synergies**: Shared API Gateway; common service mesh patterns; reusable decomposition templates
- **Estimated Effort**: High across 16 services
- **Roadmap Phase Alignment**: Phase 2-3 (after containerization)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Managed Analytics

- **Services Affected**: 5 of 34 (14.7%)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q4 < 3: affects 10 services (messaging/streaming gaps)
  - Data processing workloads present
- **Representative AWS Services**: Amazon Kinesis, Amazon OpenSearch, Amazon EventBridge (preferred), AWS Glue
- **Key Activities**:
  1. Portfolio: Establish EventBridge as the standard event bus
  2. Per-service: Migrate log aggregation to OpenSearch, implement streaming pipelines
- **Cross-Service Synergies**: Shared EventBridge event bus; common OpenSearch patterns
- **Estimated Effort**: Medium across 5 services
- **Roadmap Phase Alignment**: Phase 3 (advanced capabilities)
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

#### Move to AI

- **Services Affected**: 1 of 34 (2.9%)
- **Portfolio Priority**: Low
- **Aggregation**: Move to AI: Triggered in 1 of 34 services (32 services had no AI intent in context — pathway correctly suppressed)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): 32 services
  - Already present (AI frameworks detected): thingsboard--thingsboard (langchain4j already integrated)
- **Common Trigger Criteria**:
  - Context contains "ML" — AI intent signal present in iterative--dvc
- **Representative AWS Services**: Amazon Bedrock (preferred), Amazon SageMaker, AWS Lambda for inference
- **Key Activities**:
  1. Portfolio: Evaluate Bedrock integration opportunities for ML/data services
  2. Per-service: iterative--dvc — integrate Bedrock for model serving and experiment tracking
- **Cross-Service Synergies**: Limited — only 1 service triggered
- **Estimated Effort**: Medium across 1 service
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## 7. Integration Opportunities

### Shared Service Extraction

**Opportunity: Centralized Logging Platform**
- **Current State**: Duplicated logging approaches in 34 services — some use console.log, some use Log4j, some use Serilog, some have no structured logging
- **Proposed Solution**: Deploy Amazon CloudWatch Logs with a standardized log format (JSON structured logging). Use CloudWatch Log Groups per service with a shared retention policy. For Java services, use ADOT auto-instrumentation. For Node.js/TypeScript, use Winston with CloudWatch transport.
- **Benefits**: Unified log search, cross-service correlation, compliance-ready audit trail
- **Effort**: Medium
- **Priority**: High (addresses SEC-Q1 blocker in 30 services)

**Opportunity: Shared CI/CD Pipeline Templates**
- **Current State**: 33 services use GitHub Actions but each has custom, inconsistent workflow definitions
- **Proposed Solution**: Create reusable GitHub Actions composite actions and workflow templates. Standard pipeline: lint → test → build → security scan (CodeGuru) → container build (ECR) → deploy (EKS/Lambda) → rollback-on-failure
- **Benefits**: Consistent quality gates, reduced pipeline maintenance, faster onboarding
- **Effort**: Low
- **Priority**: High (addresses INF-Q11 in 13 services, OPS-Q5 in 20 services)

**Opportunity: Shared Secrets Management**
- **Current State**: 23 services store secrets in environment variables, config files, or hardcoded values
- **Proposed Solution**: Deploy AWS Secrets Manager with automatic rotation. Create CDK construct for secret provisioning. Use External Secrets Operator for EKS integration.
- **Benefits**: Centralized secret lifecycle, automatic rotation, audit trail, no hardcoded secrets
- **Effort**: Medium
- **Priority**: High (addresses SEC-Q4 blocker in 23 services)

**Opportunity: Shared Authentication Service**
- **Current State**: 11 services have no authentication; others use inconsistent approaches (dummy auth, basic auth, custom implementations)
- **Proposed Solution**: Deploy Amazon Cognito as the portfolio-wide identity provider. Use API Gateway (preferred) authorizers for consistent authentication. Implement JWT token validation at the gateway level.
- **Benefits**: Single sign-on, consistent auth, centralized user management
- **Effort**: High
- **Priority**: Medium (addresses SEC-Q3 blocker in 11 services)

### Event-Driven Architecture

**Opportunity: Scality Decoupling**
- **Current State**: scality--backbeat and scality--cloudserver have circular synchronous dependencies via shared MongoDB
- **Proposed Solution**: Introduce Amazon EventBridge (preferred) event bus. CloudServer publishes lifecycle events; Backbeat subscribes and processes asynchronously. Migrate shared MongoDB to separate Amazon DocumentDB instances with event-driven sync.
- **Benefits**: Independent deployment, elimination of circular dependency, improved resilience
- **Effort**: High

**Opportunity: *arr Suite Event Bus**
- **Current State**: Sonarr, Radarr, Lidarr communicate with Prowlarr synchronously
- **Proposed Solution**: Introduce EventBridge event bus for index search requests. Prowlarr publishes index results as events; *arr services subscribe to relevant topics.
- **Benefits**: Decoupled services, Prowlarr can process in parallel, improved scalability
- **Effort**: Medium

### API Gateway Consolidation

- **Current State**: No unified API gateway exists. Services expose APIs independently with no common authentication, rate limiting, or monitoring.
- **Proposed Solution**: Deploy Amazon API Gateway (preferred) as the unified entry point. Implement per-service API stages. Use usage plans for rate limiting and API keys for external consumers. Enable CloudWatch metrics and X-Ray tracing at the gateway level.
- **Benefits**: Consistent auth, rate limiting, monitoring, cost reduction, API versioning
- **Effort**: Medium

### Observability Unification

- **Current State**: Each service manages observability independently. 22 services have no distributed tracing (OPS-Q1). 31 services have no SLOs (OPS-Q2). 18 services have no metrics dashboards (OPS-Q3).
- **Proposed Solution**: Deploy a unified observability stack: CloudWatch Logs (centralized logging) + X-Ray / ADOT (distributed tracing) + CloudWatch Metrics (custom metrics) + CloudWatch Dashboards (per-service and portfolio-level views). For EKS workloads, enable Container Insights.
- **Benefits**: End-to-end tracing across services, consistent metrics, unified dashboards, SLO tracking
- **Effort**: Medium

---

## 8. Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| Portfolio-wide IaC gap blocks all infrastructure modernization | High | High | 🔴 Critical | Adopt CDK/Terraform in Phase 0; create reusable modules | Phase 0 |
| Security baseline absence exposes portfolio to breaches | High | High | 🔴 Critical | Enable CloudTrail, KMS encryption, Secrets Manager in Phase 0 | Phase 0 |
| No disaster recovery leads to data loss in regional failure | High | High | 🔴 Critical | Implement AWS Backup, define RPO/RTO targets, multi-AZ deployment | Phase 0 |
| Circular dependency between Scality services prevents independent deployment | High | Medium | 🟠 High | Break circular dependency via EventBridge in Phase 0 | Phase 0 |
| No observability means issues detected only by end users | High | Medium | 🟠 High | Deploy CloudWatch + X-Ray + alerting in Phase 0 | Phase 0 |
| No automated testing in 6 services allows regressions to production | Medium | Medium | 🟡 Medium | Add test stages to CI/CD pipelines | Phase 1 |
| Self-managed databases in 17 services have availability risk | Medium | Medium | 🟡 Medium | Migrate to Aurora/DocumentDB/ElastiCache | Phase 2 |
| Single points of failure in 31 services | High | Medium | 🟠 High | Multi-AZ deployment for all production services | Phase 1-2 |
| No secrets management in 23 services — credential leakage risk | High | High | 🔴 Critical | Deploy Secrets Manager, remove hardcoded secrets | Phase 0 |
| No runbooks for 33 services — incident response is ad hoc | High | Medium | 🟠 High | Create runbook templates, implement SSM Automation | Phase 0-1 |

### High-Risk Dependencies

No services have score < 2.0 AND fan-in >= 3. Prowlarr--Prowlarr (fan-in: 3, score: 1.80) is the closest and should be prioritized in Phase 1.

### Single Points of Failure

All 31 services with INF-Q5 score 1 are potential single points of failure. None have blast radius >= 50% due to the sparse dependency graph. The highest blast radius services are:
- Prowlarr--Prowlarr: 11.8% blast radius (affects Sonarr, Radarr, Lidarr, plus Prowlarr itself)
- scality--cloudserver: 8.8% blast radius
- scality--backbeat: 8.8% blast radius

### Circular Dependency Risks

⚠️ **scality--backbeat ↔ scality--cloudserver**: Bidirectional sync + async dependency via shared MongoDB. Must be broken in Phase 0. Resolution: EventBridge-based event communication + separate data stores.

### Data Availability Risks

Services with self-managed databases AND serving as data platforms:
- **thingsboard--thingsboard**: Self-managed PostgreSQL + Cassandra + Redis. IoT platform handling device data — high data volume, high availability requirement.
- **Graylog2--graylog2-server**: Self-managed MongoDB + Elasticsearch. Log management server — critical operational data.
- **conductor-oss--conductor**: Self-managed PostgreSQL + Redis + Elasticsearch. Workflow orchestration — operational continuity dependent on data availability.
- **scality--cloudserver / scality--backbeat**: Shared MongoDB + Redis. Object storage server — data integrity is core function.

### Observability Blind Spots

Services with OPS-Q1 < 3 (no tracing) are observability blind spots. With 22 services lacking tracing, debugging cross-service issues is effectively impossible. Priority should be given to services with inter-service communication (Scality cluster, *arr suite).

---

## 9. Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + service teams

> Rationale: 33 foundational blockers affecting 90%+ of services demand a centralized platform team to build shared capabilities efficiently. A federated model would result in duplicated effort across 34 services.

**Platform Team** (4-6 engineers):
- Responsibilities: Shared IaC modules (EKS, Aurora, VPC, API Gateway), CI/CD templates, observability stack, security baseline, runbook templates
- Skills Required: AWS CDK/Terraform, EKS administration, Aurora management, CloudWatch/X-Ray, Secrets Manager, GitHub Actions

**Service Teams** (1-2 engineers per service cluster):
- Responsibilities: Service-specific modernization, containerization, database migration, application-level improvements
- Skills Required: Service-specific language expertise (Java, TypeScript, Python, C#), Docker, Kubernetes basics, database migration

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| AWS CDK (TypeScript) | IaC for all services | No — only 1 service uses CDK | High |
| Amazon EKS | Container orchestration for 17+ services | No — zero EKS deployments | High |
| Amazon Aurora | Database migration for 10 PostgreSQL services | No — all self-managed | High |
| AWS X-Ray / ADOT | Observability for 22 services | No — zero tracing implementations | High |
| AWS Secrets Manager | Secrets for 23 services | No — mostly hardcoded secrets | Medium |
| Amazon EventBridge | Event-driven architecture | No — no EventBridge usage | Medium |
| Amazon API Gateway | Unified API management | Partial — 1 service uses Lambda+APIGW | Medium |
| Docker / Containerization | Container builds for 17+ services | Partial — 17 services have Docker Compose | Medium |
| Amazon Bedrock | AI integration for 1 service | No | Low |

### Training Recommendations

**Phase 0 Priority (Weeks 1-4):**
1. AWS CDK Workshop (TypeScript) — Platform team
2. Amazon EKS Primer + EKS Workshop — Platform team + lead engineers
3. AWS Security Best Practices — All engineers
4. Getting Started with DevOps on AWS — All engineers

**Phase 1-2 Priority (Weeks 4-12):**
5. Amazon Aurora PostgreSQL migration — Database team
6. AWS X-Ray / OpenTelemetry — Observability team
7. Amazon EventBridge patterns — Platform team

### External Support

Recommended AWS Professional Services or consulting partner support for:
- **EKS cluster setup and architecture review** (High complexity, Phase 0-1) — Proper VPC design, node group configuration, Karpenter autoscaling, and security hardening
- **Database migration planning and execution** (High risk, Phase 1-2) — Especially for Scality MongoDB cluster and ThingsBoard Cassandra migration. Use AWS DMS with expert guidance.
- **Security posture assessment** (High priority, Phase 0) — Validate the security baseline implementation against AWS Well-Architected Framework security pillar

---

## 10. AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | 32 of 34 services have overall score < 2.5 | Massive portfolio-wide modernization need | Request MAP engagement via AWS Solutions Architect |
| Microsoft Modernization Program | MMP | 5 services use C# / .NET (greenshot, Lidarr, Sonarr, Radarr, Prowlarr) | .NET workloads detected | Discuss MMP eligibility with AWS Partner |
| Experience-Based Acceleration | EBA | 33 services have triggered pathways AND score < 3.0 | Move to Modern DevOps (33), Move to Managed Databases (22), Move to Containers (17) | Request EBA engagement focused on Modern DevOps pathway |

> Programs NOT triggered: OLA (no Oracle/SQL Server licensing issues — 1 MS SQL Server reference in hapifhir but not a primary workload), VMP (no VMware references), WAMP (greenshot is a Windows desktop app but not a Windows Server workload), ISV WMP (no ISV/third-party commercial software deployments).

### Program Details

**Migration Acceleration Program (MAP)**

This program is strongly recommended. With 32 of 34 services (94%) scoring below 2.5 overall, the portfolio has significant modernization needs across infrastructure, security, and operations. MAP provides funding, tools, and methodology support for large-scale migrations and modernizations.

- **Why recommended**: Portfolio overall score 2.04/4.0 with 33 foundational blockers. This is a large-scale modernization effort requiring structured program support.
- **What it provides**: Migration funding credits, AWS Migration Hub access, AWS Application Discovery Service, methodology guidance, partner resources
- **Suggested timing**: Engage MAP in Phase 0 to fund platform team infrastructure and tooling

**Microsoft Modernization Program (MMP)**

Five services in the portfolio use C# and .NET: greenshot--greenshot, Lidarr--Lidarr, Sonarr--Sonarr, Radarr--Radarr, Prowlarr--Prowlarr. These represent the *arr media suite and a Windows desktop application.

- **Why recommended**: 5 C# services representing 14.7% of the portfolio. The *arr suite services are candidates for containerization on EKS with .NET runtime.
- **What it provides**: Guidance on .NET modernization paths (.NET on EKS, .NET on Lambda), porting assistance, performance optimization for .NET on AWS
- **Suggested timing**: Engage MMP in Phase 1 when containerizing the *arr suite

**Experience-Based Acceleration (EBA)**

33 services have at least one triggered pathway AND an overall score below 3.0. The most prevalent pathway is Move to Modern DevOps (97.1% of portfolio).

- **Why recommended**: The portfolio's dominant pathway (Modern DevOps) affects virtually every service, making it an ideal candidate for EBA-style focused engagement.
- **What it provides**: Intensive, pathway-focused engagement with AWS specialists. Workshop-driven approach to accelerate specific modernization patterns.
- **Suggested timing**: Engage EBA in Phase 0–1, focused on Move to Modern DevOps + Move to Containers patterns

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

---

## 11. Recommended Self-Paced Learning Materials

> Included modules are mapped to the portfolio's triggered pathways (6 of 7) and identified skill gaps.

### Module 2: Move to Cloud Native (Containers and Serverless)

- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

### Module 3: Move to Containers with Amazon ECS and EKS

- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

### Module 4: Move to Managed Databases

- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Amazon RDS for SQL Server Getting Started — https://skillbuilder.aws/learn/WSV85JHZFF/amazon-rds-for-sql-server-getting-started/E446MXPEYH
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- Amazon DocumentDB Getting Started — https://skillbuilder.aws/learn/5RTP1DW5WQ/amazon-documentdb-with-mongodb-compatibility-getting-started/JDFWRT5GPD
- Amazon RDS for MariaDB Getting Started — https://skillbuilder.aws/learn/DAFQM637NV/amazon-rds-for-mariadb-getting-started/N2Z47FGXSE

### Module 5: Move to Managed Analytics

- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

### Module 6: Move to Modern DevOps

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- Monitor .NET Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/255DDEDPV5/monitor-net-applications-using-amazon-cloudwatch-application-signals/1WZ1NT16HJ
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/

### Module 7: Move to AI

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA

---

## 12. Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 1
- **Finding**: The portfolio has extreme IaC fragmentation. 14 of 34 services (41%) have zero IaC. Of the 20 services with some IaC, 17 use only Docker Compose (local orchestration, not cloud infrastructure). Only 1 service (getlift--lift) uses AWS CDK, 3 use Serverless Framework, and 1 uses Helm. No single cloud IaC tool covers more than 9% of the portfolio.
- **Evidence**: INF-Q10 scores: 31 services score 1 (no IaC), 2 services score 2 (partial), 1 service scores 4 (getlift--lift). IaC tools found: Docker Compose (17), Serverless Framework (3), CDK (1), Helm (1).
- **Recommendation**: Adopt AWS CDK (TypeScript) as the portfolio-wide cloud IaC standard. CDK aligns with the preference for EKS and is native to the dominant TypeScript ecosystem. Create reusable CDK construct libraries for common patterns (EKS cluster, Aurora database, VPC, API Gateway). Mandate IaC for all new infrastructure and migrate existing Docker Compose-only services to CDK.
- **Contextual Annotations**: This finding provides direct context for the INF-Q10 foundational blocker (31 services score < 2). The lack of any IaC standardization explains why infrastructure modernization is blocked portfolio-wide.

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: No centralized observability stack exists across the portfolio. Each service manages observability independently — or, more commonly, has no observability at all. No shared CloudWatch Log Groups, no shared X-Ray configuration, no shared dashboards, no consistent metric namespaces. Individual OPS scores confirm: OPS-Q1 avg 1.48, OPS-Q2 avg 1.09, OPS-Q3 avg 1.65.
- **Evidence**: OPS-Q1 (tracing): 22 services score 1. OPS-Q2 (SLOs): 31 services score 1. OPS-Q3 (metrics): 18 services score 1. No shared observability configuration files found across any service. Only getsentry--sentry-python and scality--cloudserver have partial observability.
- **Recommendation**: Deploy a centralized observability platform: CloudWatch Logs (shared log groups per service), X-Ray with ADOT auto-instrumentation (cross-service tracing), CloudWatch Container Insights (EKS metrics), CloudWatch Dashboards (portfolio-level and per-service views). Define standard metric namespaces and SLO templates.
- **Contextual Annotations**: This finding provides context for OPS-Q1, OPS-Q2, OPS-Q3, and OPS-Q4 foundational blockers. The complete absence of shared observability means individual service gaps cannot be mitigated by a centralized platform — **verify** that no external observability tools (Datadog, New Relic, etc.) are in use outside the repositories.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 2
- **Finding**: One circular dependency detected: scality--backbeat ↔ scality--cloudserver. This is a bidirectional dependency with both synchronous (REST API calls) and asynchronous (lifecycle event triggers) components, plus a shared MongoDB data store. The cycle is resolvable by introducing an event bus and separating the shared database.
- **Evidence**: Inferred from MOD report findings — scality--backbeat references cloudserver for replication workflows; scality--cloudserver triggers backbeat for lifecycle management. Both share MongoDB (shared_db type).
- **Recommendation**: Break the circular dependency in Phase 0 by: (1) Introducing Amazon EventBridge as the communication channel between the two services, (2) Migrating from shared MongoDB to separate Amazon DocumentDB instances with event-driven synchronization.
- **Contextual Annotations**: This circular dependency directly affects the roadmap — both Scality services are placed in Phase 1 with a Phase 0 prerequisite for dependency resolution.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 1
- **Finding**: Extreme technology fragmentation across the portfolio. 5 primary programming languages (Java, JavaScript, TypeScript, Python, C#), 10+ database engines (PostgreSQL, SQLite, MongoDB, Redis, MySQL, Elasticsearch, Cassandra, Derby, MS SQL Server, RocksDB), 5 CI/CD platforms (GitHub Actions, Travis CI, Jenkins, CircleCI, Azure Pipelines), and 5+ IaC approaches (Docker Compose, Serverless Framework, CDK, Helm, none). Technology diversity ratio: ~35 distinct technologies across 34 services = approximately 1.0 technologies per service.
- **Evidence**: Language distribution: Java (10), JavaScript (10), TypeScript (7), Python (5), C# (5). Database distribution: PostgreSQL (10), SQLite (5), Redis (4), MySQL (3), MongoDB (3), Elasticsearch (3), Cassandra (2), others (4). CI/CD: GitHub Actions (33), Travis CI (3), Jenkins (1), CircleCI (1), Azure Pipelines (1).
- **Recommendation**: This portfolio consists of 34 independent open-source projects — high technology diversity is expected and structurally inherent, not a deficiency to "fix." Standardization should focus on *operational* tooling (IaC, CI/CD, observability, security) rather than forcing language or framework convergence. Specifically: (1) Standardize CI/CD on GitHub Actions (already 97% adoption), (2) Standardize cloud IaC on AWS CDK, (3) Standardize observability on CloudWatch + X-Ray, (4) Standardize databases on Aurora PostgreSQL (preferred) + DynamoDB (preferred) for new workloads.
- **Contextual Annotations**: The high diversity score (1) does not indicate poor architecture — it reflects the portfolio's nature as a collection of independent open-source mirrors. Preference alignment is strong: no Oracle databases (avoidance met), PostgreSQL dominance enables Aurora migration (preference met).

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: No centralized security posture exists. No shared WAF, no centralized security scanning pipeline, no unified vulnerability management. Each service manages (or fails to manage) security independently. SEC category scores confirm: SEC avg 1.63, with 30 services scoring 1 on audit logging and encryption.
- **Evidence**: SEC-Q1 (audit logging): 30 services score 1. SEC-Q2 (encryption): 30 services score 1. SEC-Q4 (secrets): 23 services score 1. SEC-Q6 (vuln mgmt): 16 services score 1. SEC-Q7 (security scanning): 13 services score 1. No shared WAF WebACL, no centralized scanning configuration, no shared Secrets Manager references found.
- **Recommendation**: Implement a centralized security posture: (1) AWS WAF with shared WebACL for public-facing services, (2) Amazon Inspector for centralized vulnerability scanning across container images and Lambda functions, (3) AWS Secrets Manager with shared secret rotation policies, (4) AWS Security Hub for centralized security findings aggregation, (5) GitHub Advanced Security or CodeGuru Security for SAST in CI/CD pipelines across all repos.
- **Contextual Annotations**: This finding provides context for SEC-Q1 through SEC-Q7 foundational blockers. The complete absence of shared security infrastructure means every service is independently vulnerable — **verify** that no account-level security controls (GuardDuty, Security Hub, CloudTrail) are already deployed at the AWS account level.

---

## 13. Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| greenshot--greenshot | monorepo | P2 | 1.33 | 1.09 | 1.50 | 1.75 | 1.29 | 1.00 | 2 | 1 |
| realworld-apps--angular-realworld-example-app | application | P2 | 1.57 | 1.09 | 2.00 | 2.25 | 1.29 | 1.22 | 4 | 1 |
| coreui--coreui-free-angular-admin-template | application | P2 | 1.63 | 1.64 | 2.67 | 1.75 | 1.00 | 1.11 | 4 | 1 |
| akveo--ngx-admin | application | P2 | 1.73 | 1.64 | 2.67 | 2.25 | 1.00 | 1.11 | 4 | 1 |
| umami-software--umami | monorepo | P2 | 1.73 | 1.36 | 2.00 | 2.75 | 1.43 | 1.11 | 4 | 1 |
| Prowlarr--Prowlarr | monorepo | P2 | 1.80 | 1.27 | 2.33 | 2.75 | 1.43 | 1.22 | 4 | 1 |
| dwyl--aws-sdk-mock | application | P2 | 1.81 | 1.64 | 3.00 | 1.75 | 1.57 | 1.11 | 3 | 2 |
| Radarr--Radarr | monorepo | P2 | 1.82 | 1.45 | 2.50 | 2.50 | 1.43 | 1.22 | 4 | 2 |
| gulpjs--gulp | application | P2 | 1.82 | 1.73 | 3.00 | 1.75 | 1.29 | 1.33 | 3 | 2 |
| motdotla--node-lambda | application | P2 | 1.84 | 1.18 | 2.33 | 2.50 | 1.86 | 1.33 | 3 | 2 |
| Lidarr--Lidarr | monorepo | P2 | 1.87 | 1.45 | 2.33 | 2.75 | 1.57 | 1.22 | 4 | 2 |
| OpenAPITools--openapi-generator | application | P2 | 1.91 | 1.73 | 2.83 | 2.25 | 1.29 | 1.44 | 1 | 2 |
| scality--backbeat | application | P2 | 1.94 | 1.36 | 2.50 | 2.50 | 1.57 | 1.78 | 4 | 1 |
| Sonarr--Sonarr | monorepo | P2 | 1.97 | 1.45 | 2.67 | 3.00 | 1.29 | 1.44 | 4 | 2 |
| tqdm--tqdm | application | P2 | 1.98 | 1.82 | 3.33 | 1.75 | 1.43 | 1.56 | 3 | 2 |
| conductor-oss--conductor | monorepo | P2 | 2.01 | 1.64 | 2.83 | 3.00 | 1.14 | 1.44 | 3 | 2 |
| arrow-py--arrow | application | P2 | 2.04 | 1.73 | 3.83 | 1.75 | 1.57 | 1.33 | 2 | 2 |
| getsentry--sentry-python | application | P2 | 2.06 | 1.73 | 3.50 | 1.75 | 1.43 | 1.89 | 1 | 2 |
| iterative--dvc | application | P2 | 2.08 | 1.27 | 2.33 | 3.25 | 2.00 | 1.56 | 3 | 2 |
| webpack--webpack | application | P2 | 2.10 | 1.82 | 3.17 | 2.50 | 1.57 | 1.44 | 1 | 3 |
| Alluxio--alluxio | monorepo | P2 | 2.12 | 1.55 | 2.33 | 3.25 | 1.57 | 1.89 | 5 | 3 |
| scality--cloudserver | application | P2 | 2.12 | 1.27 | 2.17 | 3.00 | 2.29 | 1.89 | 3 | 1 |
| Graylog2--graylog2-server | monorepo | P2 | 2.15 | 1.36 | 2.50 | 3.00 | 2.00 | 1.89 | 5 | 3 |
| FlowiseAI--Flowise | monorepo | P2 | 2.16 | 1.45 | 2.83 | 3.00 | 1.86 | 1.67 | 3 | 3 |
| apache--flink-connector-aws | monorepo | P2 | 2.16 | 1.18 | 3.83 | 2.50 | 1.86 | 1.44 | 1 | 3 |
| openzipkin--zipkin | monorepo | P2 | 2.16 | 1.27 | 3.17 | 3.00 | 1.57 | 1.78 | 2 | 3 |
| thingsboard--thingsboard | monorepo | P2 | 2.17 | 1.36 | 3.00 | 3.00 | 2.14 | 1.33 | 3 | 3 |
| hapifhir--hapi-fhir | monorepo | P2 | 2.28 | 1.45 | 3.33 | 3.25 | 1.71 | 1.67 | 3 | 3 |
| Netflix--eureka | monorepo | P2 | 2.29 | 1.55 | 3.33 | 4.00 | 1.14 | 1.44 | 2 | 3 |
| ToolJet--ToolJet | monorepo | P2 | 2.35 | 2.18 | 2.67 | 3.00 | 2.14 | 1.78 | 2 | 3 |
| serverless--serverless | monorepo | P2 | 2.37 | 1.73 | 3.00 | 3.00 | 2.14 | 2.00 | 1 | 3 |
| apache--druid | monorepo | P2 | 2.48 | 1.64 | 3.33 | 3.50 | 2.29 | 1.67 | 2 | 3 |
| zappa--Zappa | application | P2 | 2.57 | 2.18 | 2.83 | 3.75 | 2.29 | 1.78 | 1 | 3 |
| getlift--lift | application | P2 | 2.83 | 3.64 | 3.67 | 3.75 | 1.86 | 1.22 | 0 | 3 |

---

## 14. Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | akveo--ngx-admin | services/akveo--ngx-admin/modernization-assessment/akveo--ngx-admin-mod-report.md | 2025-07-16 | application | 1.73 |
| 2 | Alluxio--alluxio | services/Alluxio--alluxio/modernization-assessment/Alluxio--alluxio-mod-report.md | 2025-07-17 | monorepo | 2.12 |
| 3 | apache--druid | services/apache--druid/modernization-assessment/apache--druid-mod-report.md | 2025-07-22 | monorepo | 2.48 |
| 4 | apache--flink-connector-aws | services/apache--flink-connector-aws/modernization-assessment/apache--flink-connector-aws-mod-report.md | 2026-04-29 | monorepo | 2.16 |
| 5 | arrow-py--arrow | services/arrow-py--arrow/modernization-assessment/arrow-py--arrow-mod-report.md | 2025-04-29 | application | 2.04 |
| 6 | conductor-oss--conductor | services/conductor-oss--conductor/modernization-assessment/conductor-oss--conductor-mod-report.md | 2026-04-29 | monorepo | 2.01 |
| 7 | coreui--coreui-free-angular-admin-template | services/coreui--coreui-free-angular-admin-template/modernization-assessment/coreui--coreui-free-angular-admin-template-mod-report.md | 2026-04-29 | application | 1.63 |
| 8 | dwyl--aws-sdk-mock | services/dwyl--aws-sdk-mock/modernization-assessment/dwyl--aws-sdk-mock-mod-report.md | 2026-04-29 | application | 1.81 |
| 9 | FlowiseAI--Flowise | services/FlowiseAI--Flowise/modernization-assessment/FlowiseAI--Flowise-mod-report.md | 2025-07-17 | monorepo | 2.16 |
| 10 | getlift--lift | services/getlift--lift/modernization-assessment/getlift--lift-mod-report.md | 2025-07-18 | application | 2.83 |
| 11 | getsentry--sentry-python | services/getsentry--sentry-python/modernization-assessment/getsentry--sentry-python-mod-report.md | 2025-04-29 | application | 2.06 |
| 12 | Graylog2--graylog2-server | services/Graylog2--graylog2-server/modernization-assessment/Graylog2--graylog2-server-mod-report.md | 2025-07-14 | monorepo | 2.15 |
| 13 | greenshot--greenshot | services/greenshot--greenshot/modernization-assessment/greenshot--greenshot-mod-report.md | 2025-07-17 | monorepo | 1.33 |
| 14 | gulpjs--gulp | services/gulpjs--gulp/modernization-assessment/gulpjs--gulp-mod-report.md | 2026-04-29 | application | 1.82 |
| 15 | hapifhir--hapi-fhir | services/hapifhir--hapi-fhir/modernization-assessment/hapifhir--hapi-fhir-mod-report.md | 2026-04-29 | monorepo | 2.28 |
| 16 | iterative--dvc | services/iterative--dvc/modernization-assessment/iterative--dvc-mod-report.md | 2026-04-29 | application | 2.08 |
| 17 | Lidarr--Lidarr | services/Lidarr--Lidarr/modernization-assessment/Lidarr--Lidarr-mod-report.md | 2025-07-16 | monorepo | 1.87 |
| 18 | motdotla--node-lambda | services/motdotla--node-lambda/modernization-assessment/motdotla--node-lambda-mod-report.md | 2025-07-14 | application | 1.84 |
| 19 | Netflix--eureka | services/Netflix--eureka/modernization-assessment/Netflix--eureka-mod-report.md | 2026-04-29 | monorepo | 2.29 |
| 20 | OpenAPITools--openapi-generator | services/OpenAPITools--openapi-generator/modernization-assessment/OpenAPITools--openapi-generator-mod-report.md | 2026-04-29 | application | 1.91 |
| 21 | openzipkin--zipkin | services/openzipkin--zipkin/modernization-assessment/openzipkin--zipkin-mod-report.md | 2025-07-16 | monorepo | 2.16 |
| 22 | Prowlarr--Prowlarr | services/Prowlarr--Prowlarr/modernization-assessment/Prowlarr--Prowlarr-mod-report.md | 2025-07-17 | monorepo | 1.80 |
| 23 | Radarr--Radarr | services/Radarr--Radarr/modernization-assessment/Radarr--Radarr-mod-report.md | 2025-07-17 | monorepo | 1.82 |
| 24 | realworld-apps--angular-realworld-example-app | services/realworld-apps--angular-realworld-example-app/modernization-assessment/realworld-apps--angular-realworld-example-app-mod-report.md | 2026-04-29 | application | 1.57 |
| 25 | scality--backbeat | services/scality--backbeat/modernization-assessment/scality--backbeat-mod-report.md | 2025-07-16 | application | 1.94 |
| 26 | scality--cloudserver | services/scality--cloudserver/modernization-assessment/scality--cloudserver-mod-report.md | 2025-04-29 | application | 2.12 |
| 27 | serverless--serverless | services/serverless--serverless/modernization-assessment/serverless--serverless-mod-report.md | 2026-04-29 | monorepo | 2.37 |
| 28 | Sonarr--Sonarr | services/Sonarr--Sonarr/modernization-assessment/Sonarr--Sonarr-mod-report.md | 2025-07-17 | monorepo | 1.97 |
| 29 | thingsboard--thingsboard | services/thingsboard--thingsboard/modernization-assessment/thingsboard--thingsboard-mod-report.md | 2026-04-29 | monorepo | 2.17 |
| 30 | ToolJet--ToolJet | services/ToolJet--ToolJet/modernization-assessment/ToolJet--ToolJet-mod-report.md | 2026-04-29 | monorepo | 2.35 |
| 31 | tqdm--tqdm | services/tqdm--tqdm/modernization-assessment/tqdm--tqdm-mod-report.md | 2025-07-15 | application | 1.98 |
| 32 | umami-software--umami | services/umami-software--umami/modernization-assessment/umami-software--umami-mod-report.md | 2026-04-29 | monorepo | 1.73 |
| 33 | webpack--webpack | services/webpack--webpack/modernization-assessment/webpack--webpack-mod-report.md | 2025-07-17 | application | 2.10 |
| 34 | zappa--Zappa | services/zappa--Zappa/modernization-assessment/zappa--Zappa-mod-report.md | 2025-07-15 | application | 2.57 |
