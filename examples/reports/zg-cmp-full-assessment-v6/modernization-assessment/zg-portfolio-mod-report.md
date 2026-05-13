# Portfolio Modernization Assessment Report

**Date**: 2026-05-07
**Services Assessed**: 33
**Portfolio Context**: Portfolio of 33 open-source project mirrors validating ATX TDs across Java, Python, JS/TS, C# — monolith, microservices, serverless, CLI, frontend, data platform — observability, storage, IoT, AI/LLM, analytics, healthcare.
**Technology Preferences**: Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock; Avoid: self-managed-kafka, self-managed-kubernetes, oracle, lambda

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 2.17 / 4.0 |
| Score Range | 1.50 – 2.99 |
| Highest Scoring Service | dwyl--aws-sdk-mock (2.99) |
| Lowest Scoring Service | Netflix--eureka (1.50) |
| Pathways Triggered (portfolio-wide) | 6 of 7 |
| Cross-Cutting Foundational Blockers | 28 |
| Cross-Cutting Improvement Opportunities | 8 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 8 | 24% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 25 | 76% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 0 | 0% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 1.49 | 1.17 | 2.27 | 9 |
| Application Architecture (APP) | 2.60 | 1.25 | 3.50 | 0 |
| Data Platform (DATA) | 2.99 | 2.00 | 4.00 | 1 |
| Security Baseline (SEC) | 1.88 | 1.29 | 2.86 | 0 |
| Operations & Observability (OPS) | 1.69 | 1.00 | 3.00 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 24 | 73% |
| library | 7 | 21% |
| monorepo | 2 | 6% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-05-07 |
| total_services | 33 |
| portfolio_score | 2.17 |
| score_range_min | 1.50 |
| score_range_max | 2.99 |
| mature_services | 0 |
| partial_services | 8 |
| needs_work_services | 25 |
| not_ready_services | 0 |
| pathways_triggered | 6 |
| foundational_blockers | 28 |
| improvement_opportunities | 8 |
| category_inf | 1.49 |
| category_app | 2.60 |
| category_data | 2.99 |
| category_sec | 1.88 |
| category_ops | 1.69 |
| portfolio_level_avg | 1.80 |

## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| Java | 10 | 30% |
| TypeScript | 6 | 18% |
| JavaScript | 6 | 18% |
| C# | 5 | 15% |
| Python | 5 | 15% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| PostgreSQL | Relational | 10 | Mixed |
| Redis | Cache | 6 | No |
| SQLite | Relational (Embedded) | 5 | No |
| DynamoDB | NoSQL | 4 | Yes |
| MySQL/MariaDB | Relational | 4 | No |
| MongoDB | NoSQL | 3 | No |
| Elasticsearch/OpenSearch | Search | 3 | No |
| Cassandra | NoSQL | 2 | No |

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| N/A (Library/Tool) | 19 | 58% |
| Self-Managed Containers | 10 | 30% |
| Managed Compute (ECS/EKS/Fargate) | 3 | 9% |
| No Managed Compute / VM-based | 1 | 3% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| Docker Compose | IaC | 6 |
| None | IaC | 4 |

### Standardization Opportunities

- **IaC Consolidation**: The portfolio has highly fragmented IaC usage with many services having no IaC at all. Standardize on AWS CDK or Terraform across the portfolio.
- **CI/CD Standardization**: Multiple CI/CD tools in use (GitHub Actions, Azure Pipelines, Jenkins, Travis CI). Consolidate to GitHub Actions with AWS CodeBuild/CodePipeline integration.
- **Language Diversity**: 5 primary languages across 33 services. This is manageable but requires multi-language CI/CD templates and container base images.
- **Database Consolidation**: Multiple self-managed databases. Migrate to Aurora PostgreSQL (preferred) and DynamoDB for NoSQL workloads per technology preferences.
- **Preference Alignment**: Current stack has limited alignment with preferred technologies (EKS, Aurora, DynamoDB, API Gateway, EventBridge, Bedrock). Most services lack managed compute and managed databases.

## Service Dependency Map

> Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

No explicit `dependency_overrides` were provided in the portfolio configuration. Analysis of individual MOD report findings reveals this portfolio consists of independent open-source project mirrors with no inter-service dependencies detected. Each service operates independently.

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| Netflix--eureka | 0 | 0 | 0% | Independent | 1.50 |
| ngx-admin | 0 | 0 | 0% | Independent | 1.50 |
| greenshot--greenshot | 0 | 0 | 0% | Independent | 1.54 |
| motdotla--node-lambda | 0 | 0 | 0% | Independent | 1.56 |
| umami-software--umami | 0 | 0 | 0% | Independent | 1.71 |
| Lidarr--Lidarr | 0 | 0 | 0% | Independent | 1.76 |
| Prowlarr--Prowlarr | 0 | 0 | 0% | Independent | 1.76 |
| Radarr--Radarr | 0 | 0 | 0% | Independent | 1.86 |
| zappa--Zappa | 0 | 0 | 0% | Independent | 1.86 |
| Sonarr--Sonarr | 0 | 0 | 0% | Independent | 1.88 |
| Alluxio--alluxio | 0 | 0 | 0% | Independent | 1.90 |
| thingsboard--thingsboard | 0 | 0 | 0% | Independent | 1.90 |
| Graylog2--graylog2-server | 0 | 0 | 0% | Independent | 1.97 |
| OpenAPITools--openapi-generator | 0 | 0 | 0% | Independent | 1.97 |
| conductor-oss--conductor | 0 | 0 | 0% | Independent | 1.99 |
| iterative--dvc | 0 | 0 | 0% | Independent | 2.06 |
| FlowiseAI--Flowise | 0 | 0 | 0% | Independent | 2.14 |
| realworld-apps--angular-realworld-example-app | 0 | 0 | 0% | Independent | 2.18 |
| scality--cloudserver | 0 | 0 | 0% | Independent | 2.22 |
| coreui--coreui-free-angular-admin-template | 0 | 0 | 0% | Independent | 2.23 |
| openzipkin--zipkin | 0 | 0 | 0% | Independent | 2.28 |
| ToolJet--ToolJet | 0 | 0 | 0% | Independent | 2.31 |
| hapifhir--hapi-fhir | 0 | 0 | 0% | Independent | 2.35 |
| gulpjs--gulp | 0 | 0 | 0% | Independent | 2.38 |
| druid | 0 | 0 | 0% | Independent | 2.48 |
| getlift--lift | 0 | 0 | 0% | Independent | 2.60 |
| tqdm--tqdm | 0 | 0 | 0% | Independent | 2.60 |
| apache--flink-connector-aws | 0 | 0 | 0% | Independent | 2.68 |
| serverless--serverless | 0 | 0 | 0% | Independent | 2.77 |
| webpack--webpack | 0 | 0 | 0% | Independent | 2.88 |
| getsentry--sentry-python | 0 | 0 | 0% | Independent | 2.95 |
| arrow | 0 | 0 | 0% | Independent | 2.96 |
| dwyl--aws-sdk-mock | 0 | 0 | 0% | Independent | 2.99 |

### Foundation Services (High Fan-In)

No foundation services identified — all services in this portfolio are independent project mirrors with no inter-service dependencies.

### Circular Dependencies

✅ No circular dependencies detected.

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.

1. **SEC-Q1: SAST/DAST Security Scanning** — 23 of 25 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, ngx-admin=1, druid=1, apache--flink-connector-aws=1, arrow=1, getlift--lift=1, getsentry--sentry-python=1, greenshot--greenshot=1, gulpjs--gulp=1, iterative--dvc=1, motdotla--node-lambda=1, openzipkin--zipkin=1, realworld-apps--angular-realworld-example-app=1, scality--cloudserver=1, serverless--serverless=1, webpack--webpack=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--flink-connector-aws, arrow, druid, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, serverless--serverless, webpack--webpack, zappa--Zappa
   - **Portfolio-Level Recommendation**: Implement centralized SAST/DAST scanning in CI/CD pipelines. Deploy Amazon CodeGuru and AWS Inspector.

2. **OPS-Q7: Chaos Engineering & Resilience Testing** — 17 of 18 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, ngx-admin=1, druid=1, apache--flink-connector-aws=1, greenshot--greenshot=1, iterative--dvc=1, motdotla--node-lambda=1, openzipkin--zipkin=1, realworld-apps--angular-realworld-example-app=1, scality--cloudserver=1, serverless--serverless=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--flink-connector-aws, druid, greenshot--greenshot, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, serverless--serverless
   - **Portfolio-Level Recommendation**: Establish chaos engineering practice using AWS Fault Injection Service. Start with critical path services.

3. **INF-Q7: Environment Parity** — 14 of 14 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, ngx-admin=1, druid=1, greenshot--greenshot=1, iterative--dvc=1, openzipkin--zipkin=1, scality--cloudserver=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, druid, greenshot--greenshot, iterative--dvc, ngx-admin, openzipkin--zipkin, scality--cloudserver, zappa--Zappa
   - **Portfolio-Level Recommendation**: Implement environment parity through IaC and container-based deployments. Use CDK/Terraform workspaces for dev/staging/prod.

4. **INF-Q5: Infrastructure as Code Coverage** — 13 of 14 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, druid=1, greenshot--greenshot=1, iterative--dvc=1, openzipkin--zipkin=1, scality--cloudserver=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, druid, greenshot--greenshot, iterative--dvc, ngx-admin, openzipkin--zipkin, scality--cloudserver, zappa--Zappa
   - **Portfolio-Level Recommendation**: Standardize on AWS CDK or Terraform. Create shared IaC modules for common patterns (VPC, EKS cluster, RDS).

5. **OPS-Q9: Runbook Automation** — 13 of 16 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, druid=1, greenshot--greenshot=1, iterative--dvc=1, openzipkin--zipkin=1, realworld-apps--angular-realworld-example-app=1, serverless--serverless=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, druid, greenshot--greenshot, iterative--dvc, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, serverless--serverless
   - **Portfolio-Level Recommendation**: Automate runbooks using AWS Systems Manager Automation. Create shared playbooks for common failure modes.

6. **OPS-Q4: Alerting & Incident Response** — 12 of 16 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, ngx-admin=1, greenshot--greenshot=1, iterative--dvc=1, motdotla--node-lambda=1, openzipkin--zipkin=1, realworld-apps--angular-realworld-example-app=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, greenshot--greenshot, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app
   - **Portfolio-Level Recommendation**: Implement centralized alerting with CloudWatch Alarms and SNS. Create runbook-linked alerts.

7. **OPS-Q8: Capacity Planning** — 12 of 18 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, ngx-admin=1, greenshot--greenshot=1, iterative--dvc=1, motdotla--node-lambda=1, openzipkin--zipkin=1, realworld-apps--angular-realworld-example-app=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, greenshot--greenshot, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app
   - **Portfolio-Level Recommendation**: Implement capacity planning using CloudWatch metrics and AWS Compute Optimizer recommendations.

8. **INF-Q6: CI/CD Pipeline Maturity** — 11 of 14 applicable services score < 2
   - **Score Distribution**: Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, druid=1, greenshot--greenshot=1, iterative--dvc=1, openzipkin--zipkin=1, scality--cloudserver=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, druid, greenshot--greenshot, iterative--dvc, ngx-admin, openzipkin--zipkin, scality--cloudserver, zappa--Zappa
   - **Portfolio-Level Recommendation**: Establish CI/CD pipeline templates using GitHub Actions with AWS CodeBuild. Enforce pipeline-as-code standards.

9. **OPS-Q3: Metrics & Dashboards** — 11 of 17 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, ngx-admin=1, greenshot--greenshot=1, iterative--dvc=1, motdotla--node-lambda=1, openzipkin--zipkin=1, realworld-apps--angular-realworld-example-app=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, greenshot--greenshot, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app
   - **Portfolio-Level Recommendation**: Deploy unified CloudWatch dashboards with consistent metric namespaces across all services.

10. **INF-Q10: Container Orchestration** — 10 of 16 applicable services score < 2
   - **Score Distribution**: FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, greenshot--greenshot=1, openzipkin--zipkin=1, realworld-apps--angular-realworld-example-app=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, greenshot--greenshot, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, zappa--Zappa
   - **Portfolio-Level Recommendation**: Adopt EKS as the standard container orchestration platform. Create shared Helm charts and GitOps workflows.

11. **OPS-Q1: Distributed Tracing** — 10 of 26 applicable services score < 2
   - **Score Distribution**: Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, greenshot--greenshot=1, gulpjs--gulp=1, iterative--dvc=1, motdotla--node-lambda=1, realworld-apps--angular-realworld-example-app=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, greenshot--greenshot, gulpjs--gulp, iterative--dvc, motdotla--node-lambda, ngx-admin, realworld-apps--angular-realworld-example-app, zappa--Zappa
   - **Portfolio-Level Recommendation**: Deploy AWS X-Ray or OpenTelemetry with ADOT collector across all services. Establish distributed tracing standards.

12. **OPS-Q2: SLO/SLA Definition** — 10 of 10 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, druid=1, openzipkin--zipkin=1, scality--cloudserver=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, druid, openzipkin--zipkin, scality--cloudserver
   - **Portfolio-Level Recommendation**: Define SLOs/SLAs for each service using CloudWatch SLO. Establish error budget policies.

13. **SEC-Q4: IAM & Access Control** — 10 of 21 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, greenshot--greenshot=1, gulpjs--gulp=1, motdotla--node-lambda=1, realworld-apps--angular-realworld-example-app=1, webpack--webpack=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, greenshot--greenshot, gulpjs--gulp, motdotla--node-lambda, ngx-admin, realworld-apps--angular-realworld-example-app, webpack--webpack
   - **Portfolio-Level Recommendation**: Implement least-privilege IAM policies. Adopt AWS IAM Identity Center for centralized access management.

14. **INF-Q1: Managed Compute Adoption** — 9 of 14 applicable services score < 2
   - **Score Distribution**: FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, greenshot--greenshot=1, iterative--dvc=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, greenshot--greenshot, iterative--dvc, ngx-admin, zappa--Zappa
   - **Portfolio-Level Recommendation**: Adopt EKS with Fargate for containerized workloads. Establish container base images and deployment patterns.

15. **INF-Q8: Auto-Scaling Configuration** — 9 of 9 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ToolJet--ToolJet=1, druid=1, openzipkin--zipkin=1, scality--cloudserver=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, druid, openzipkin--zipkin, scality--cloudserver
   - **Portfolio-Level Recommendation**: Configure auto-scaling policies for all EKS workloads using Karpenter. Establish HPA/VPA patterns.

16. **APP-Q2: Service Decomposition** — 8 of 27 applicable services score < 2
   - **Score Distribution**: Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, greenshot--greenshot=1, iterative--dvc=1, realworld-apps--angular-realworld-example-app=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, greenshot--greenshot, iterative--dvc, ngx-admin, realworld-apps--angular-realworld-example-app, zappa--Zappa
   - **Portfolio-Level Recommendation**: Develop decomposition strategies for monolithic services. Use Strangler Fig pattern with EKS-hosted microservices.

17. **OPS-Q5: Log Aggregation & Analysis** — 8 of 16 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ngx-admin, zappa--Zappa
   - **Portfolio-Level Recommendation**: Centralize logging to CloudWatch Logs with structured logging standards. Deploy log insights queries.

18. **SEC-Q6: TLS/Encryption in Transit** — 8 of 26 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, FlowiseAI--Flowise=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, ngx-admin=1, greenshot--greenshot=1, motdotla--node-lambda=1, realworld-apps--angular-realworld-example-app=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Prowlarr--Prowlarr, Sonarr--Sonarr, greenshot--greenshot, motdotla--node-lambda, ngx-admin, realworld-apps--angular-realworld-example-app
   - **Portfolio-Level Recommendation**: Enforce TLS 1.2+ for all communications. Deploy ACM certificates and configure HTTPS-only endpoints.

19. **INF-Q2: Managed Database Services** — 5 of 10 applicable services score < 2
   - **Score Distribution**: FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, Lidarr--Lidarr=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr
   - **Portfolio-Level Recommendation**: Migrate self-managed databases to Aurora PostgreSQL or DynamoDB. Use AWS DMS for migration.

20. **INF-Q9: CDN & Edge Caching** — 5 of 9 applicable services score < 2
   - **Score Distribution**: Graylog2--graylog2-server=1, Prowlarr--Prowlarr=1, Sonarr--Sonarr=1, druid=1, openzipkin--zipkin=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Graylog2--graylog2-server, Prowlarr--Prowlarr, Sonarr--Sonarr, druid, openzipkin--zipkin
   - **Portfolio-Level Recommendation**: Deploy CloudFront distributions for public-facing services. Create shared CDN configuration templates.

21. **SEC-Q2: WAF & DDoS Protection** — 5 of 10 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, Graylog2--graylog2-server=1, Prowlarr--Prowlarr=1, druid=1, openzipkin--zipkin=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, Graylog2--graylog2-server, Prowlarr--Prowlarr, druid, openzipkin--zipkin
   - **Portfolio-Level Recommendation**: Deploy AWS WAF with shared WebACL rules. Implement AWS Shield Advanced for DDoS protection.

22. **SEC-Q3: Secrets Management** — 5 of 21 applicable services score < 2
   - **Score Distribution**: ngx-admin=1, greenshot--greenshot=1, gulpjs--gulp=1, motdotla--node-lambda=1, openzipkin--zipkin=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: greenshot--greenshot, gulpjs--gulp, motdotla--node-lambda, ngx-admin, openzipkin--zipkin
   - **Portfolio-Level Recommendation**: Adopt AWS Secrets Manager with automatic rotation. Create shared secret access patterns.

23. **APP-Q5: API Design & Versioning** — 3 of 25 applicable services score < 2
   - **Score Distribution**: greenshot--greenshot=1, motdotla--node-lambda=1, openzipkin--zipkin=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: greenshot--greenshot, motdotla--node-lambda, openzipkin--zipkin
   - **Portfolio-Level Recommendation**: Implement API versioning standards with Amazon API Gateway. Establish OpenAPI specification requirements.

24. **APP-Q6: Configuration Externalization** — 3 of 26 applicable services score < 2
   - **Score Distribution**: FlowiseAI--Flowise=1, Graylog2--graylog2-server=1, greenshot--greenshot=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: FlowiseAI--Flowise, Graylog2--graylog2-server, greenshot--greenshot
   - **Portfolio-Level Recommendation**: Externalize configurations using AWS AppConfig or Parameter Store. Remove hardcoded configs from code.

25. **DATA-Q1: Data Backup & Recovery** — 3 of 26 applicable services score < 2
   - **Score Distribution**: Lidarr--Lidarr=1, ngx-admin=1, iterative--dvc=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Lidarr--Lidarr, iterative--dvc, ngx-admin
   - **Portfolio-Level Recommendation**: Implement data platform best practices — backup strategies, encryption, and managed database migration.

26. **OPS-Q6: Health Checks & Readiness Probes** — 2 of 19 applicable services score < 2
   - **Score Distribution**: ngx-admin=1, greenshot--greenshot=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: greenshot--greenshot, ngx-admin
   - **Portfolio-Level Recommendation**: Implement health check endpoints and readiness probes for all deployed services.

27. **SEC-Q5: Dependency Vulnerability Scanning** — 2 of 27 applicable services score < 2
   - **Score Distribution**: getsentry--sentry-python=1, zappa--Zappa=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: getsentry--sentry-python, zappa--Zappa
   - **Portfolio-Level Recommendation**: Enable automated dependency scanning in all CI/CD pipelines. Use Amazon Inspector for vulnerability management.

28. **SEC-Q7: Authentication & Authorization Framework** — 2 of 26 applicable services score < 2
   - **Score Distribution**: Alluxio--alluxio=1, greenshot--greenshot=1
   - **Impact**: Critical gap blocking modernization readiness for affected services
   - **Affected Services**: Alluxio--alluxio, greenshot--greenshot
   - **Portfolio-Level Recommendation**: Standardize on Amazon Cognito or IAM Identity Center for authentication/authorization across services.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking.
> Address as capacity allows or in parallel with other modernization work.

1. **INF-Q11: Network Security & Segmentation** — 9 of 16 applicable services score < 3
   - **Score Distribution**: Alluxio--alluxio=2, FlowiseAI--Flowise=2, Graylog2--graylog2-server=2, Prowlarr--Prowlarr=2, ngx-admin=2, apache--flink-connector-aws=2, openzipkin--zipkin=2, realworld-apps--angular-realworld-example-app=2, zappa--Zappa=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Prowlarr--Prowlarr, apache--flink-connector-aws, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, zappa--Zappa
   - **Portfolio-Level Recommendation**: Implement network segmentation with VPCs and security groups. Adopt zero-trust network patterns.

2. **DATA-Q3: Database Performance Optimization** — 6 of 17 applicable services score < 3
   - **Score Distribution**: Alluxio--alluxio=2, Lidarr--Lidarr=2, Prowlarr--Prowlarr=2, dwyl--aws-sdk-mock=2, openzipkin--zipkin=2, tqdm--tqdm=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: Alluxio--alluxio, Lidarr--Lidarr, Prowlarr--Prowlarr, dwyl--aws-sdk-mock, openzipkin--zipkin, tqdm--tqdm
   - **Portfolio-Level Recommendation**: Optimize database performance with connection pooling, query optimization, and read replicas.

3. **APP-Q4: Event-Driven Architecture** — 5 of 16 applicable services score < 3
   - **Score Distribution**: Graylog2--graylog2-server=2, Lidarr--Lidarr=2, Prowlarr--Prowlarr=2, Sonarr--Sonarr=2, scality--cloudserver=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, scality--cloudserver
   - **Portfolio-Level Recommendation**: Adopt event-driven architecture patterns. Deploy EventBridge as the central event bus.

4. **INF-Q3: Load Balancing & Traffic Management** — 5 of 7 applicable services score < 3
   - **Score Distribution**: Lidarr--Lidarr=1, FlowiseAI--Flowise=2, Graylog2--graylog2-server=2, Prowlarr--Prowlarr=2, scality--cloudserver=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, scality--cloudserver
   - **Portfolio-Level Recommendation**: Deploy Application Load Balancers with target groups. Standardize traffic routing with API Gateway.

5. **APP-Q3: Async Communication Patterns** — 4 of 15 applicable services score < 3
   - **Score Distribution**: FlowiseAI--Flowise=2, Graylog2--graylog2-server=2, Lidarr--Lidarr=2, Prowlarr--Prowlarr=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr
   - **Portfolio-Level Recommendation**: Introduce async communication patterns using EventBridge and SQS. Reduce synchronous coupling.

6. **DATA-Q2: Data Encryption at Rest** — 4 of 27 applicable services score < 3
   - **Score Distribution**: ngx-admin=1, greenshot--greenshot=2, tqdm--tqdm=2, zappa--Zappa=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: greenshot--greenshot, ngx-admin, tqdm--tqdm, zappa--Zappa
   - **Portfolio-Level Recommendation**: Enable encryption at rest for all data stores using AWS KMS. Implement default encryption policies.

7. **INF-Q4: Messaging & Event-Driven Infrastructure** — 4 of 9 applicable services score < 3
   - **Score Distribution**: Prowlarr--Prowlarr=1, FlowiseAI--Flowise=2, Lidarr--Lidarr=2, scality--cloudserver=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: FlowiseAI--Flowise, Lidarr--Lidarr, Prowlarr--Prowlarr, scality--cloudserver
   - **Portfolio-Level Recommendation**: Adopt EventBridge for event routing and SQS for async processing. Avoid self-managed Kafka.

8. **APP-Q1: Language & Framework Currency** — 3 of 30 applicable services score < 3
   - **Score Distribution**: Alluxio--alluxio=2, ngx-admin=2, greenshot--greenshot=2
   - **Impact**: Limits modernization progress but does not block it
   - **Affected Services**: Alluxio--alluxio, greenshot--greenshot, ngx-admin
   - **Portfolio-Level Recommendation**: Upgrade language/framework versions across affected services. Target LTS versions.

### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 1.49 / 4.0**

**Critical Gaps:**
- INF-Q7 (Environment Parity): 14/14 services score < 2
- INF-Q5 (Infrastructure as Code Coverage): 13/14 services score < 2
- INF-Q6 (CI/CD Pipeline Maturity): 11/14 services score < 2
- INF-Q10 (Container Orchestration): 10/16 services score < 2
- INF-Q1 (Managed Compute Adoption): 9/14 services score < 2

#### Application Architecture

**Portfolio Score: 2.60 / 4.0**

**Critical Gaps:**
- APP-Q2 (Service Decomposition): 8/27 services score < 2
- APP-Q5 (API Design & Versioning): 3/25 services score < 2
- APP-Q6 (Configuration Externalization): 3/26 services score < 2

#### Data Platform

**Portfolio Score: 2.99 / 4.0**

**Critical Gaps:**
- DATA-Q1 (Data Backup & Recovery): 3/26 services score < 2

#### Security Baseline

**Portfolio Score: 1.88 / 4.0**

**Critical Gaps:**
- SEC-Q1 (SAST/DAST Security Scanning): 23/25 services score < 2
- SEC-Q4 (IAM & Access Control): 10/21 services score < 2
- SEC-Q6 (TLS/Encryption in Transit): 8/26 services score < 2
- SEC-Q2 (WAF & DDoS Protection): 5/10 services score < 2
- SEC-Q3 (Secrets Management): 5/21 services score < 2

#### Operations & Observability

**Portfolio Score: 1.69 / 4.0**

**Critical Gaps:**
- OPS-Q7 (Chaos Engineering & Resilience Testing): 17/18 services score < 2
- OPS-Q9 (Runbook Automation): 13/16 services score < 2
- OPS-Q4 (Alerting & Incident Response): 12/16 services score < 2
- OPS-Q8 (Capacity Planning): 12/18 services score < 2
- OPS-Q3 (Metrics & Dashboards): 11/17 services score < 2

## Portfolio Modernization Roadmap

> Priority-based phased roadmap. Services are ordered by priority (P0 → P1 → P2),
> then by overall score (lowest first). No dependency-based ordering available
> as services are independent open-source mirrors.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Risk Mitigation**: Lowest-scoring services prioritized to reduce portfolio risk
3. **Parallel Tracks**: Independent services can be modernized concurrently
4. **Quick Wins**: Early wins build momentum and demonstrate value
5. **Technology Alignment**: Leverage preferred technologies (EKS, Aurora, DynamoDB, API Gateway, EventBridge, Bedrock)

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities and address portfolio-wide blockers.

**Cross-Cutting Activities:**
- Establish centralized SAST/DAST scanning pipeline (SEC-Q1: 23/25 services affected)
- Deploy IaC framework and shared modules using AWS CDK (INF-Q5: 13/14 services affected)
- Create CI/CD pipeline templates with GitHub Actions + CodeBuild (INF-Q6: 11/14 services affected)
- Deploy shared observability platform: X-Ray + CloudWatch (OPS-Q7, OPS-Q9, OPS-Q8 gaps)
- Establish container base images and EKS deployment patterns (INF-Q1, INF-Q10 gaps)
- Implement environment parity standards (INF-Q7: 14/14 services affected)

**Organizational Enablers:**
- Training: EKS, IaC (CDK/Terraform), CloudWatch observability, security scanning
- Tooling: Shared CDK constructs, Helm charts, CI/CD templates
- Standards: API versioning, logging format, metric namespaces, secret management

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize lowest-scoring services and establish patterns.

**Services in Scope:**
1. **Netflix--eureka** (P2, Score: 1.50 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q10: Infrastructure as Code Coverage
     - SEC-Q5: Secrets Management
   - Dependencies: None (independent service)
   - Estimated Effort: High

2. **ngx-admin** (P2, Score: 1.50 / 4.0)
   - Key Activities:
     - INF-Q10: Address gap
     - INF-Q11: Address gap
     - OPS-Q5: Address gap
   - Dependencies: None (independent service)
   - Estimated Effort: High

3. **greenshot--greenshot** (P2, Score: 1.54 / 4.0)
   - Key Activities:
     - INF-Q10: Infrastructure as Code Coverage
     - APP-Q2: Monolith vs Microservices
     - OPS-Q6: Integration Testing
   - Dependencies: None (independent service)
   - Estimated Effort: High

4. **motdotla--node-lambda** (P2, Score: 1.56 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - SEC-Q3: API Authentication
     - SEC-Q4: Centralized Identity Integration
   - Dependencies: None (independent service)
   - Estimated Effort: High

5. **umami-software--umami** (P2, Score: 1.71 / 4.0)
   - Key Activities:
     - INF-Q10: Infrastructure as Code Coverage
     - INF-Q1: Managed Compute
     - SEC-Q1: Audit Logging
   - Dependencies: None (independent service)
   - Estimated Effort: High

6. **Lidarr--Lidarr** (P2, Score: 1.76 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q10: Infrastructure as Code
     - APP-Q2: Monolith vs Microservices
   - Dependencies: None (independent service)
   - Estimated Effort: High

7. **Prowlarr--Prowlarr** (P2, Score: 1.76 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q10: Infrastructure as Code Coverage
     - OPS-Q1: Distributed Tracing
   - Dependencies: None (independent service)
   - Estimated Effort: High

8. **Radarr--Radarr** (P2, Score: 1.86 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q10: Infrastructure as Code Coverage
     - SEC-Q5: Secrets Management
   - Dependencies: None (independent service)
   - Estimated Effort: High

9. **zappa--Zappa** (P2, Score: 1.86 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q10: Infrastructure as Code Coverage
     - SEC-Q1: Audit Logging
   - Dependencies: None (independent service)
   - Estimated Effort: High

10. **Sonarr--Sonarr** (P2, Score: 1.88 / 4.0)
   - Key Activities:
     - INF-Q10: Infrastructure as Code Coverage
     - INF-Q1: Managed Compute
     - SEC-Q1: Audit Logging
   - Dependencies: None (independent service)
   - Estimated Effort: High

11. **Alluxio--alluxio** (P2, Score: 1.90 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - SEC-Q2: Encryption at Rest
     - OPS-Q2: SLO Definitions
   - Dependencies: None (independent service)
   - Estimated Effort: High

12. **thingsboard--thingsboard** (P2, Score: 1.90 / 4.0)
   - Key Activities:
     - INF-Q10: Infrastructure as Code Coverage
     - INF-Q1: Managed Compute
     - SEC-Q1: Audit Logging
   - Dependencies: None (independent service)
   - Estimated Effort: High

13. **Graylog2--graylog2-server** (P2, Score: 1.97 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q10: Infrastructure as Code Coverage
     - SEC-Q1: Audit Logging
   - Dependencies: None (independent service)
   - Estimated Effort: High

14. **OpenAPITools--openapi-generator** (P2, Score: 1.97 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - SEC-Q1: Audit Logging
     - SEC-Q4: Centralized Identity Integration
   - Dependencies: None (independent service)
   - Estimated Effort: High

15. **conductor-oss--conductor** (P2, Score: 1.99 / 4.0)
   - Key Activities:
     - SEC-Q3: API Authentication
     - INF-Q10: Infrastructure as Code Coverage
     - SEC-Q5: Secrets Management
   - Dependencies: None (independent service)
   - Estimated Effort: High

**Expected Outcomes:**
- Establish containerization patterns with EKS
- Deploy first services with full CI/CD pipeline
- Validate IaC and observability standards

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Extend modernization to moderate-gap services. Replicate proven patterns.

**Services in Scope:**
1. **iterative--dvc** (P2, Score: 2.06 / 4.0)
   - Key Activities:
     - APP-Q2: Monolith vs Microservices
     - INF-Q1: Managed Compute
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

2. **FlowiseAI--Flowise** (P2, Score: 2.14 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q10: Infrastructure as Code Coverage
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

3. **realworld-apps--angular-realworld-example-app** (P2, Score: 2.18 / 4.0)
   - Key Activities:
     - INF-Q10: Infrastructure as Code Coverage
     - APP-Q2: Monolith vs Microservices
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

4. **scality--cloudserver** (P2, Score: 2.22 / 4.0)
   - Key Activities:
     - INF-Q5: Network Security
     - INF-Q6: API Entry Point
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

5. **coreui--coreui-free-angular-admin-template** (P2, Score: 2.23 / 4.0)
   - Key Activities:
     - INF-Q10: Infrastructure as Code Coverage
     - INF-Q1: Managed Compute
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

6. **openzipkin--zipkin** (P2, Score: 2.28 / 4.0)
   - Key Activities:
     - INF-Q5: Network Security
     - INF-Q6: API Entry Point
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

7. **ToolJet--ToolJet** (P2, Score: 2.31 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - INF-Q7: Auto-Scaling
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

8. **hapifhir--hapi-fhir** (P2, Score: 2.35 / 4.0)
   - Key Activities:
     - INF-Q1: Managed Compute
     - INF-Q5: Network Security
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

9. **gulpjs--gulp** (P2, Score: 2.38 / 4.0)
   - Key Activities:
     - OPS-Q1: Distributed Tracing
     - SEC-Q1: Audit Logging
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

10. **druid** (P2, Score: 2.48 / 4.0)
   - Key Activities:
     - INF-Q5: Network Security
     - INF-Q8: Backup and Recovery
   - Dependencies: Phase 0 cross-cutting infrastructure
   - Estimated Effort: Medium

**Parallel Tracks:**
- All Phase 2 services can be modernized concurrently (no inter-service dependencies)

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize higher-scoring services, implement advanced capabilities, continuous improvement.

**Services in Scope:**
1. **getlift--lift** (P2, Score: 2.60 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - APP-Q5: API Versioning Strategy
   - Estimated Effort: Low

2. **tqdm--tqdm** (P2, Score: 2.60 / 4.0)
   - Key Activities:
     - OPS-Q1: Address gap
     - SEC-Q1: Address gap
   - Estimated Effort: Low

3. **apache--flink-connector-aws** (P2, Score: 2.68 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - OPS-Q7: Incident Response Automation
   - Estimated Effort: Low

4. **serverless--serverless** (P2, Score: 2.77 / 4.0)
   - Key Activities:
     - SEC-Q1: Address gap
     - OPS-Q7: Address gap
   - Estimated Effort: Low

5. **webpack--webpack** (P2, Score: 2.88 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - SEC-Q4: Centralized Identity Integration
   - Estimated Effort: Low

6. **getsentry--sentry-python** (P2, Score: 2.95 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - SEC-Q5: Secrets Management
   - Estimated Effort: Low

7. **arrow** (P2, Score: 2.96 / 4.0)
   - Key Activities:
     - SEC-Q1: Audit Logging
     - OPS-Q1: Distributed Tracing
   - Estimated Effort: Low

8. **dwyl--aws-sdk-mock** (P2, Score: 2.99 / 4.0)
   - Key Activities:
     - APP-Q5: API Versioning Strategy
     - DATA-Q3: Database Engine Version and EOL
   - Estimated Effort: Low

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6+ months (with 33 parallel tracks — all services independent)

## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 19 | 58% | Medium | High |
| Move to Containers | 9 | 27% | Low | Medium |
| Move to Open Source | 0 | 0% | Low | Low |
| Move to Managed Databases | 13 | 39% | Medium | Medium |
| Move to Managed Analytics | 2 | 6% | Low | Low |
| Move to Modern DevOps | 25 | 76% | High | High |
| Move to AI | 1 | 3% | Low | Low |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing
a single at-a-glance view of pathway coverage across the portfolio. Each repo appears
in exactly one column per pathway row.

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, conductor-oss--conductor, greenshot--greenshot, hapifhir--hapi-fhir, iterative--dvc, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, thingsboard--thingsboard, umami-software--umami | OpenAPITools--openapi-generator, apache--flink-connector-aws, coreui--coreui-free-angular-admin-template, druid, motdotla--node-lambda, serverless--serverless, zappa--Zappa | arrow, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, gulpjs--gulp, tqdm--tqdm, webpack--webpack |
| Move to Containers | Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, coreui--coreui-free-angular-admin-template, hapifhir--hapi-fhir, ngx-admin | Alluxio--alluxio, FlowiseAI--Flowise, OpenAPITools--openapi-generator, ToolJet--ToolJet, apache--flink-connector-aws, conductor-oss--conductor, druid, greenshot--greenshot, iterative--dvc, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, umami-software--umami, zappa--Zappa | arrow, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, gulpjs--gulp, motdotla--node-lambda, tqdm--tqdm, webpack--webpack |
| Move to Open Source | — | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--flink-connector-aws, arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, druid, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — |
| Move to Managed Databases | FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--cloudserver, thingsboard--thingsboard, umami-software--umami | Alluxio--alluxio, Netflix--eureka, OpenAPITools--openapi-generator, apache--flink-connector-aws, coreui--coreui-free-angular-admin-template, druid, greenshot--greenshot, iterative--dvc, motdotla--node-lambda, ngx-admin, realworld-apps--angular-realworld-example-app, serverless--serverless, zappa--Zappa | arrow, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, gulpjs--gulp, tqdm--tqdm, webpack--webpack |
| Move to Managed Analytics | thingsboard--thingsboard, umami-software--umami | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--flink-connector-aws, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, druid, greenshot--greenshot, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, serverless--serverless, zappa--Zappa | arrow, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, gulpjs--gulp, tqdm--tqdm, webpack--webpack |
| Move to Modern DevOps | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--flink-connector-aws, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, druid, greenshot--greenshot, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, thingsboard--thingsboard, umami-software--umami, zappa--Zappa | serverless--serverless | arrow, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, gulpjs--gulp, tqdm--tqdm, webpack--webpack |
| Move to AI | iterative--dvc | Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--flink-connector-aws, arrow, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, druid, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa | — |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| Alluxio--alluxio | ✅ | — | — | — | — | ✅ | — |
| FlowiseAI--Flowise | ✅ | — | — | ✅ | — | ✅ | — |
| Graylog2--graylog2-server | ✅ | ✅ | — | ✅ | — | ✅ | — |
| Lidarr--Lidarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| Netflix--eureka | ✅ | ✅ | — | — | — | ✅ | — |
| OpenAPITools--openapi-generator | — | — | — | — | — | ✅ | — |
| Prowlarr--Prowlarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| Radarr--Radarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| Sonarr--Sonarr | ✅ | ✅ | — | ✅ | — | ✅ | — |
| ToolJet--ToolJet | ✅ | — | — | ✅ | — | ✅ | — |
| apache--flink-connector-aws | — | — | — | — | — | ✅ | — |
| arrow | N/A | N/A | — | N/A | N/A | N/A | — |
| conductor-oss--conductor | ✅ | — | — | ✅ | — | ✅ | — |
| coreui--coreui-free-angular-admin-template | — | ✅ | — | — | — | ✅ | — |
| druid | — | — | — | — | — | ✅ | — |
| dwyl--aws-sdk-mock | N/A | N/A | — | N/A | N/A | N/A | — |
| getlift--lift | N/A | N/A | — | N/A | N/A | N/A | — |
| getsentry--sentry-python | N/A | N/A | — | N/A | N/A | N/A | — |
| greenshot--greenshot | ✅ | — | — | — | — | ✅ | — |
| gulpjs--gulp | N/A | N/A | — | N/A | N/A | N/A | — |
| hapifhir--hapi-fhir | ✅ | ✅ | — | ✅ | — | ✅ | — |
| iterative--dvc | ✅ | — | — | — | — | ✅ | ✅ |
| motdotla--node-lambda | — | N/A | — | — | — | ✅ | — |
| ngx-admin | ✅ | ✅ | — | — | — | ✅ | — |
| openzipkin--zipkin | ✅ | — | — | ✅ | — | ✅ | — |
| realworld-apps--angular-realworld-example-app | ✅ | — | — | — | — | ✅ | — |
| scality--cloudserver | ✅ | — | — | ✅ | — | ✅ | — |
| serverless--serverless | — | — | — | — | — | — | — |
| thingsboard--thingsboard | ✅ | — | — | ✅ | ✅ | ✅ | — |
| tqdm--tqdm | N/A | N/A | — | N/A | N/A | N/A | — |
| umami-software--umami | ✅ | — | — | ✅ | ✅ | ✅ | — |
| webpack--webpack | N/A | N/A | — | N/A | N/A | N/A | — |
| zappa--Zappa | — | — | — | — | — | ✅ | — |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Open Source may precede Move to Managed Databases (migrate off proprietary first)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is often a prerequisite for Move to AI (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1 (DevOps Foundation)**: Move to Modern DevOps (25 services) — enables all other tracks
- **Track 2 (Compute Modernization)**: Move to Containers (9 services) → Move to Cloud Native (19 services)
- **Track 3 (Data Platform)**: Move to Managed Databases (13 services) → Move to Managed Analytics (2 services)
- **Track 4 (AI Enablement)**: Move to AI (1 service) — after data foundations are established

### Pathway Details

#### Move to Cloud Native

- **Services Affected**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, conductor-oss--conductor, greenshot--greenshot, hapifhir--hapi-fhir, iterative--dvc, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, thingsboard--thingsboard, umami-software--umami (19 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q1 score=1: affects 14 services
  - APP-Q2 score=2: affects 11 services
  - APP-Q3 score=2: affects 9 services
  - APP-Q4 score=2: affects 8 services
  - APP-Q2 score=1: affects 8 services
- **Representative AWS Services**: EKS, API Gateway, EventBridge, Aurora PostgreSQL, DynamoDB
- **Key Activities**:
  1. Containerize monolithic services and deploy to EKS
  2. Decompose into microservices using Strangler Fig pattern
  3. Implement event-driven communication with EventBridge
- **Cross-Service Synergies**: Shared EKS cluster, common Helm charts, API Gateway consolidation
- **Roadmap Phase Alignment**: Phase 1–3
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Containers

- **Services Affected**: Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, coreui--coreui-free-angular-admin-template, hapifhir--hapi-fhir, ngx-admin (9 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q1 score=1: affects 9 services
- **Representative AWS Services**: EKS, ECR, Fargate, AWS App Mesh
- **Key Activities**:
  1. Create Dockerfiles and container images for each service
  2. Deploy to EKS with Fargate for serverless containers
  3. Establish container security scanning with ECR
- **Cross-Service Synergies**: Shared base images, common EKS cluster, unified container registry
- **Roadmap Phase Alignment**: Phase 1–2
- **Relevant Learning Materials**: Module 3 — Move to Containers

#### Move to Managed Databases

- **Services Affected**: FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--cloudserver, thingsboard--thingsboard, umami-software--umami (13 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q2 score=1: affects 9 services
  - DATA-Q3 score=2: affects 5 services
  - INF-Q2 score=2: affects 4 services
  - DATA-Q3 score=3: affects 3 services
- **Representative AWS Services**: Aurora PostgreSQL, DynamoDB, ElastiCache, AWS DMS
- **Key Activities**:
  1. Assess database engines and plan migration targets (Aurora for relational, DynamoDB for NoSQL)
  2. Execute migrations using AWS DMS with minimal downtime
  3. Enable automated backups, Multi-AZ, and read replicas
- **Cross-Service Synergies**: Shared Aurora clusters, common DMS patterns, unified backup policies
- **Roadmap Phase Alignment**: Phase 2–3
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Managed Analytics

- **Services Affected**: thingsboard--thingsboard, umami-software--umami (2 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - INF-Q4 score=2: affects 2 services
- **Representative AWS Services**: Amazon OpenSearch Service, Amazon Managed Service for Apache Flink, Amazon Athena
- **Key Activities**:
  1. Migrate self-managed analytics to managed services
  2. Deploy managed OpenSearch/Flink for streaming analytics
- **Cross-Service Synergies**: Shared data lake, unified analytics platform
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

#### Move to Modern DevOps

- **Services Affected**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--flink-connector-aws, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, druid, greenshot--greenshot, hapifhir--hapi-fhir, iterative--dvc, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, thingsboard--thingsboard, umami-software--umami, zappa--Zappa (25 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q10 score=1: affects 17 services
  - OPS-Q5 score=1: affects 14 services
  - INF-Q11 score=2: affects 13 services
  - OPS-Q6 score=2: affects 9 services
  - OPS-Q5 score=2: affects 8 services
- **Representative AWS Services**: AWS CodeBuild, CodePipeline, CDK, CloudWatch, X-Ray
- **Key Activities**:
  1. Establish CI/CD pipeline standards with CodeBuild/GitHub Actions
  2. Deploy IaC using AWS CDK for all infrastructure
  3. Implement full observability stack with CloudWatch and X-Ray
- **Cross-Service Synergies**: Shared pipeline templates, CDK construct library, unified dashboards
- **Roadmap Phase Alignment**: Phase 0–1
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: iterative--dvc (1 total)
- **Portfolio Priority**: Low
- **Common Trigger Criteria**:
  - DISCOVERY score=None: affects 1 services
- **Aggregation**: Move to AI: Triggered in 1 of 33 services (27 services had no AI intent in context — pathway correctly suppressed)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): Alluxio--alluxio, FlowiseAI--Flowise, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, apache--flink-connector-aws, arrow, coreui--coreui-free-angular-admin-template, druid, dwyl--aws-sdk-mock, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, hapifhir--hapi-fhir, motdotla--node-lambda, ngx-admin, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--cloudserver, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa
  - Already present (AI frameworks detected): Graylog2--graylog2-server, ToolJet--ToolJet, conductor-oss--conductor, serverless--serverless, thingsboard--thingsboard
- **Representative AWS Services**: Amazon Bedrock, Amazon SageMaker, Amazon Q Developer
- **Key Activities**:
  1. Identify AI/ML use cases across the portfolio
  2. Integrate Amazon Bedrock for generative AI capabilities
- **Cross-Service Synergies**: Shared Bedrock model access, common RAG patterns
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 7 — Move to AI

## Integration Opportunities

### Shared Service Extraction

**Opportunity: Centralized Security Scanning Service**
- **Current State**: No SAST/DAST scanning in 23 of 25 applicable services
- **Proposed Solution**: Deploy centralized security scanning using Amazon Inspector and CodeGuru integrated into shared CI/CD templates
- **Benefits**: Consistent vulnerability detection, reduced per-service setup, centralized vulnerability management
- **Effort**: Medium
- **Priority**: High

**Opportunity: Shared Observability Platform**
- **Current State**: Fragmented or absent observability across 30+ services
- **Proposed Solution**: Deploy unified CloudWatch + X-Ray observability platform with ADOT collector, shared dashboards, and standardized metric namespaces
- **Benefits**: End-to-end tracing, consistent alerting, reduced tool sprawl, faster incident response
- **Effort**: Medium
- **Priority**: High

**Opportunity: Shared IaC Module Library**
- **Current State**: No IaC or fragmented IaC across 13/14 applicable services
- **Proposed Solution**: Create CDK construct library with reusable modules for VPC, EKS, Aurora, DynamoDB, API Gateway
- **Benefits**: Faster provisioning, consistency, reduced drift, auditability
- **Effort**: High
- **Priority**: High

### Event-Driven Architecture

**Opportunity: Async Communication Adoption**
- **Current State**: Multiple services rely on synchronous REST-only communication patterns
- **Proposed Solution**: Introduce EventBridge as central event bus with SQS queues for reliable async processing
- **Benefits**: Decoupling, resilience, scalability, reduced blast radius
- **Effort**: Medium

### API Gateway Consolidation

- Multiple services expose APIs without unified gateway management
- **Proposed Solution**: Deploy Amazon API Gateway with shared authentication (Cognito), rate limiting, and usage plans
- **Benefits**: Consistent auth, API versioning, observability, cost control

### Observability Unification

- Services use inconsistent or no observability tooling
- **Proposed Solution**: Deploy standardized observability with CloudWatch (metrics, logs), X-Ray (traces), and CloudWatch Application Signals
- **Benefits**: End-to-end visibility, cross-service correlation, faster MTTR

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| No security scanning across portfolio (SEC-Q1) | High | High | 🔴 Critical | Deploy centralized SAST/DAST in CI/CD pipelines | Phase 0 |
| No IaC — infrastructure drift and manual errors (INF-Q5) | High | High | 🔴 Critical | Standardize on CDK with shared module library | Phase 0 |
| No CI/CD — manual deployments (INF-Q6) | High | High | 🔴 Critical | Deploy pipeline templates with CodeBuild/GitHub Actions | Phase 0 |
| No environment parity (INF-Q7) | High | Medium | 🟠 High | Container-based deployments with IaC ensure consistency | Phase 0 |
| No auto-scaling (INF-Q8) | High | Medium | 🟠 High | Deploy Karpenter on EKS with HPA policies | Phase 1 |
| No distributed tracing (OPS-Q1) | High | Medium | 🟠 High | Deploy X-Ray/ADOT across all services | Phase 0 |
| No chaos engineering practice (OPS-Q7) | High | Medium | 🟠 High | Implement AWS Fault Injection Service | Phase 2 |
| No SLO/SLA definitions (OPS-Q2) | High | Medium | 🟠 High | Define SLOs with CloudWatch SLO tooling | Phase 1 |
| Self-managed databases without backups (DATA-Q1) | Medium | High | 🟠 High | Migrate to Aurora/DynamoDB with automated backups | Phase 2 |
| Weak IAM and access control (SEC-Q4) | High | High | 🔴 Critical | Implement least-privilege IAM with Identity Center | Phase 0 |
| No runbook automation (OPS-Q9) | High | Medium | 🟠 High | Deploy SSM Automation documents for common failures | Phase 2 |
| Technology fragmentation slowing delivery | Medium | Medium | 🟡 Medium | Standardize on preferred tech stack | Phase 1 |

### High-Risk Dependencies

No high-risk inter-service dependencies identified — services are independent project mirrors.

### Single Points of Failure

No single points of failure from inter-service coupling. Individual service resilience gaps (no auto-scaling, no multi-AZ) should be addressed per-service during Phase 1–2.

### Circular Dependency Risks

✅ No circular dependencies — all services are independent.

### Data Availability Risks

- Multiple services use self-managed databases (SQLite, PostgreSQL, MongoDB, Elasticsearch)
- Risk: No automated backups, no multi-AZ, no point-in-time recovery
- Mitigation: Migrate to Aurora PostgreSQL and DynamoDB per technology preferences

### Observability Blind Spots

- 10/26 services lack distributed tracing (OPS-Q1 score < 2)
- 11/17 services lack metrics and dashboards (OPS-Q3 score < 2)
- 12/16 services lack alerting (OPS-Q4 score < 2)
- Mitigation: Deploy unified CloudWatch + X-Ray observability in Phase 0

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + service teams (cross-cutting concerns count = 28, well above threshold of 5)

**Platform Team:**
- Responsibilities: Shared infrastructure (EKS clusters, CDK modules, CI/CD templates), security tooling, observability platform, database platform
- Skills Required: EKS/Kubernetes, AWS CDK, GitHub Actions, CloudWatch/X-Ray, Aurora/DynamoDB administration, security scanning

**Service Teams:**
- Responsibilities: Application-specific modernization (containerization, decomposition, code migration)
- Skills Required: Docker/containers, application-specific languages (Java, TypeScript, Python, C#), API design, event-driven patterns

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| EKS/Kubernetes | Container orchestration (INF-Q1, INF-Q10) | No | High |
| AWS CDK / Terraform | IaC adoption (INF-Q5) | No | High |
| CI/CD Pipeline Design | Pipeline standards (INF-Q6) | Partial | High |
| CloudWatch / X-Ray | Observability platform (OPS-Q1-Q9) | No | High |
| Security Scanning (SAST/DAST) | Security pipeline (SEC-Q1) | No | High |
| Aurora / DynamoDB Administration | Database migration (INF-Q2) | No | Medium |
| EventBridge / SQS | Event-driven patterns (APP-Q3, APP-Q4) | No | Medium |
| API Gateway | API management (INF-Q3) | Partial | Medium |
| Amazon Bedrock | AI integration (Move to AI) | No | Low |

### Training Recommendations

- **Immediate (Phase 0)**: EKS fundamentals, CDK/Terraform IaC, CI/CD with GitHub Actions + CodeBuild, CloudWatch observability
- **Phase 1**: Container security, Aurora DBA fundamentals, API Gateway design, DynamoDB data modeling
- **Phase 2–3**: EventBridge event-driven architecture, chaos engineering, Amazon Bedrock AI integration

### External Support

- **AWS Professional Services**: Recommended for EKS cluster architecture design, database migration planning (DMS), and security posture assessment
- **Consulting Partners**: Container migration acceleration, CI/CD pipeline implementation, observability platform deployment
- **AWS Solutions Architect**: Engage for architecture review of cross-cutting platform design

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | 25 services have overall score < 2.5 | 25 of 33 services below threshold | Request MAP engagement via AWS Solutions Architect |
| Microsoft Modernization Program | MMP | 5 services use C#/.NET | C# detected in: Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, greenshot--greenshot... | Engage MMP for .NET modernization guidance |
| Experience-Based Acceleration | EBA | 25 services have triggered pathways and score < 3.0 | Focus: Move to Modern DevOps (25 svc), Move to Cloud Native (19 svc) | Request EBA engagement for Move to Modern DevOps pathway |

### Program Details

**Migration Acceleration Program (MAP)**
- Recommended because 25 of 33 services score below 2.5, indicating significant modernization work required
- MAP provides funding credits, methodology, and expert guidance for large-scale migrations
- Timing: Initiate during Phase 0 to secure credits for Phase 1–3 execution

**Microsoft Modernization Program (MMP)**
- Recommended because 5 services use C#/.NET (Lidarr, Sonarr, Radarr, Prowlarr, greenshot)
- MMP provides guidance on .NET modernization to Linux containers, .NET 8 upgrades, and AWS-native patterns
- Timing: Align with Phase 1–2 containerization of .NET services on EKS

**Experience-Based Acceleration (EBA)**
- Recommended because 25 services have triggered pathways with scores < 3.0
- EBA provides immersive workshops focused on specific modernization pathways (Move to Modern DevOps most prevalent)
- Timing: Schedule EBA workshops during Phase 0 to accelerate shared infrastructure adoption

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

## Recommended Self-Paced Learning Materials

> Modules selected based on portfolio-wide triggered pathways and skill gaps.

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 1
- **Finding**: Extremely fragmented IaC landscape. Most services have no IaC at all. Tools found: {'None/Ad-hoc': 16, 'Docker Compose': 6}. No single tool reaches even 30% adoption.
- **Evidence**: INF-Q5 findings across all 33 services show 13/14 applicable services scoring < 2 (no IaC)
- **Recommendation**: Select AWS CDK as the portfolio-wide IaC standard. Create a shared CDK construct library covering common patterns (VPC, EKS, Aurora, DynamoDB). Mandate IaC for all new infrastructure.
- **Contextual Annotations**: This finding confirms the severity of the INF-Q5 Foundational Blocker — the portfolio has no IaC standard and most services lack any IaC.

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: No centralized observability platform exists. Each service either has independent logging or no observability at all. No shared tracing, no cross-service correlation, no unified dashboards.
- **Evidence**: OPS-Q1 (tracing): 10/26 services score < 2. OPS-Q3 (metrics): 11/17 score < 2. OPS-Q2 (SLOs): 10/10 applicable score < 2. No evidence of shared CloudWatch namespaces or X-Ray service map.
- **Recommendation**: Deploy a centralized observability platform using CloudWatch (metrics, logs), X-Ray with ADOT collector (distributed tracing), and CloudWatch Application Signals. Establish mandatory metric namespaces and log format standards.
- **Contextual Annotations**: This finding confirms the severity of OPS-Q1, OPS-Q2, OPS-Q3 Foundational Blockers. Portfolio lacks any shared observability.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 4
- **Finding**: No circular dependencies detected. All services in this portfolio are independent open-source project mirrors with no inter-service dependencies.
- **Evidence**: No dependency_overrides provided. Analysis of individual report findings confirms each service operates independently.
- **Recommendation**: No action required. If services are deployed as a connected system in production, provide dependency_overrides for deeper analysis.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 2
- **Finding**: High technology diversity — 5 primary languages (Java, TypeScript, JavaScript, Python, C#), fragmented IaC (Docker Compose, Terraform, none), multiple CI/CD tools (GitHub Actions, Azure Pipelines, Travis CI, Jenkins), diverse database engines (PostgreSQL, MongoDB, Redis, SQLite, Elasticsearch).
- **Evidence**: Language distribution across 33 services. Technology diversity score = high (5 languages, 4+ CI/CD tools, 5+ database engines across 33 services).
- **Recommendation**: Accept language diversity as inherent to this multi-technology portfolio. Focus standardization efforts on infrastructure tooling (IaC, CI/CD) and operational tooling (observability, security). Align new technology choices with preferences: EKS, Aurora, DynamoDB, API Gateway, EventBridge.
- **Contextual Annotations**: Technology diversity increases the complexity of Phase 0 shared tooling — CI/CD templates and container base images must support 5 language runtimes.

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: No centralized security posture. No shared WAF, no centralized scanning pipeline, no unified vulnerability management. Each service manages security independently (or not at all — 23/25 have no SAST/DAST).
- **Evidence**: SEC-Q1: 23/25 services score < 2 (no security scanning). SEC-Q4: 10/21 score < 2 (weak IAM). SEC-Q2: 5/10 score < 2 (no WAF). No evidence of shared security tooling.
- **Recommendation**: Deploy centralized security scanning (Amazon Inspector + CodeGuru) in CI/CD pipelines. Implement shared AWS WAF with WebACL rules for all public endpoints. Deploy AWS Secrets Manager with cross-account access patterns. Establish Security Hub for unified vulnerability management.
- **Contextual Annotations**: This finding confirms SEC-Q1 as the highest-impact Foundational Blocker (23/25 services affected). Portfolio-wide security posture is critically weak.

> **Portfolio-Level Average Score**: 1.80 / 4.0

## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| Netflix--eureka | application | P2 | 1.50 | 1.29 | 1.83 | 3.00 | 1.40 | 1.33 | 3 of 7 | 1 |
| ngx-admin | application | P2 | 1.50 | 1.17 | 2.00 | 2.00 | 1.33 | 1.00 | 3 of 7 | 1 |
| greenshot--greenshot | application | P2 | 1.54 | 1.33 | 1.25 | 2.67 | 1.33 | 1.13 | 2 of 7 | 1 |
| motdotla--node-lambda | application | P2 | 1.56 | N/A | 2.00 | N/A | 1.50 | 1.17 | 1 of 7 | 1 |
| umami-software--umami | application | P2 | 1.71 | 1.27 | 2.00 | 2.75 | 1.43 | 1.11 | 4 of 7 | 1 |
| Lidarr--Lidarr | application | P2 | 1.76 | 1.33 | 2.17 | 2.50 | 1.67 | 1.11 | 4 of 7 | 1 |
| Prowlarr--Prowlarr | application | P2 | 1.76 | 1.18 | 2.33 | 2.75 | 1.43 | 1.11 | 4 of 7 | 1 |
| Radarr--Radarr | application | P2 | 1.86 | 1.22 | 2.33 | 2.75 | 1.67 | 1.33 | 4 of 7 | 1 |
| zappa--Zappa | application | P2 | 1.86 | 1.17 | 2.25 | 2.50 | 1.60 | 1.80 | 1 of 7 | 1 |
| Sonarr--Sonarr | application | P2 | 1.88 | 1.22 | 2.40 | 3.00 | 1.57 | 1.22 | 4 of 7 | 1 |
| Alluxio--alluxio | application | P2 | 1.90 | 2.00 | 2.25 | 2.75 | 1.29 | 1.22 | 2 of 7 | 1 |
| thingsboard--thingsboard | application | P2 | 1.90 | 1.27 | 2.33 | 2.50 | 1.86 | 1.56 | 4 of 7 | 1 |
| Graylog2--graylog2-server | application | P2 | 1.97 | 1.36 | 2.17 | 2.75 | 2.00 | 1.56 | 4 of 7 | 1 |
| OpenAPITools--openapi-generator | application | P2 | 1.97 | 1.67 | 2.50 | 2.50 | 1.67 | 1.50 | 1 of 7 | 1 |
| conductor-oss--conductor | application | P2 | 1.99 | 1.45 | 2.50 | 3.25 | 1.29 | 1.44 | 3 of 7 | 1 |
| iterative--dvc | application | P2 | 2.06 | 1.50 | 2.50 | 2.67 | 2.25 | 1.38 | 3 of 7 | 2 |
| FlowiseAI--Flowise | application | P2 | 2.14 | 1.45 | 2.33 | 3.25 | 2.00 | 1.67 | 3 of 7 | 2 |
| realworld-apps--angular-realworld-example-app | application | P2 | 2.18 | 1.50 | 2.50 | 4.00 | 1.50 | 1.38 | 2 of 7 | 2 |
| scality--cloudserver | application | P2 | 2.22 | 1.73 | 2.50 | 2.75 | 2.14 | 2.00 | 3 of 7 | 2 |
| coreui--coreui-free-angular-admin-template | application | P2 | 2.23 | 1.17 | 3.33 | 4.00 | 1.50 | 1.13 | 2 of 7 | 2 |
| openzipkin--zipkin | application | P2 | 2.28 | 1.73 | 2.83 | 2.50 | 2.14 | 2.22 | 3 of 7 | 2 |
| ToolJet--ToolJet | application | P2 | 2.31 | 2.27 | 2.67 | 2.75 | 2.29 | 1.56 | 3 of 7 | 2 |
| hapifhir--hapi-fhir | application | P2 | 2.35 | 1.45 | 2.83 | 3.25 | 2.17 | 2.25 | 4 of 7 | 2 |
| gulpjs--gulp | library | P2 | 2.38 | N/A | 2.83 | 3.67 | 2.00 | 1.00 | 0 of 7 | 2 |
| druid | monorepo | P2 | 2.48 | 2.00 | 3.25 | 3.00 | 2.14 | 2.00 | 1 of 7 | 2 |
| getlift--lift | library | P2 | 2.60 | N/A | 3.00 | 2.75 | 2.67 | 2.00 | 0 of 7 | 3 |
| tqdm--tqdm | library | P2 | 2.60 | N/A | 3.17 | 2.75 | 2.50 | 2.00 | 0 of 7 | 3 |
| apache--flink-connector-aws | monorepo | P2 | 2.68 | 2.00 | 3.50 | 3.67 | 2.00 | 2.25 | 1 of 7 | 3 |
| serverless--serverless | application | P2 | 2.77 | N/A | 3.00 | 3.67 | 2.17 | 2.25 | 0 of 7 | 3 |
| webpack--webpack | library | P2 | 2.88 | N/A | 3.17 | 3.33 | 2.00 | 3.00 | 0 of 7 | 3 |
| getsentry--sentry-python | library | P2 | 2.95 | N/A | 3.33 | 3.25 | 2.20 | 3.00 | 0 of 7 | 3 |
| arrow | library | P2 | 2.96 | N/A | 3.33 | 4.00 | 2.50 | 2.00 | 0 of 7 | 3 |
| dwyl--aws-sdk-mock | library | P2 | 2.99 | N/A | 3.33 | 2.75 | 2.86 | 3.00 | 0 of 7 | 3 |

### Individual Service Details

#### Netflix--eureka

- **Overall Score**: 1.50 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.29
  - Application Architecture: 1.83
  - Data Platform: 3.00
  - Security Baseline: 1.40
  - Operations & Observability: 1.33
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - SEC-Q5: score 2 — Secrets Management
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize: convert WAR to embedded server, create Dockerfile, deploy to EKS. Define EKS cluster and service resources in Terraform or CDK.
  - Evaluate Step Functions or EventBridge for peer replication workflow observability. The current in-process approach may be architecturally appropriate for latency-sensitive service discovery.
  - Evaluate EventBridge or SQS for peer state propagation. Alternatively, migrating to AWS Cloud Map eliminates the peer replication concern entirely.
- **Roadmap Phase**: Phase 1

#### ngx-admin

- **Overall Score**: 1.50 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.17
  - Application Architecture: 2.00
  - Data Platform: 2.00
  - Security Baseline: 1.33
  - Operations & Observability: 1.00
- **Top Gaps**:
  - INF-Q10: score 1 — No IaC exists — 0% coverage
  - INF-Q11: score 2 — Partial CI/CD with legacy tooling and rsync deploy
  - OPS-Q5: score 1 — rsync direct-to-production with no staged rollout
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize the Angular application and deploy to EKS (preferred) or use S3 + CloudFront for static hosting. Create a Dockerfile with multi-stage build (Node.js build → nginx serve) and deploy via Helm to EKS.
  - When moving to AWS, deploy within a VPC with private subnets. Use CloudFront as CDN/entry point with WAF for DDoS protection. If using EKS, configure network policies and security groups via IaC.
  - Deploy CloudFront as CDN with S3 origin for static assets, or use an ALB/Ingress in front of EKS-hosted containers. Configure WAF rules for web application protection.
- **Roadmap Phase**: Phase 1

#### greenshot--greenshot

- **Overall Score**: 1.54 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.33
  - Application Architecture: 1.25
  - Data Platform: 2.67
  - Security Baseline: 1.33
  - Operations & Observability: 1.13
- **Top Gaps**:
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - APP-Q2: score 1 — Monolith vs Microservices
  - OPS-Q6: score 1 — Integration Testing
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps
- **Key Recommendations**:
  - If cloud features are planned (image hosting, collaboration), provision managed compute using EKS (preferred per technology preferences) for backend services.
  - When cloud services are introduced, deploy them in a VPC with private subnets, least-privilege security groups, and VPC endpoints.
  - If cloud backend services are developed, place API Gateway in front with throttling, authentication, and request validation.
- **Roadmap Phase**: Phase 1

#### motdotla--node-lambda

- **Overall Score**: 1.56 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 2.00
  - Data Platform: N/A
  - Security Baseline: 1.50
  - Operations & Observability: 1.17
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - SEC-Q3: score 1 — API Authentication
  - SEC-Q4: score 1 — Centralized Identity Integration
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**:
  - Migrate from aws-sdk v2 to @aws-sdk/client-lambda, @aws-sdk/client-s3, @aws-sdk/client-cloudwatch-logs, @aws-sdk/client-cloudwatch-events. Replace continuation-local-storage with native AsyncLocalStorage.
  - Inject AWS client instances rather than sharing a mutable global singleton. This improves testability and future modularization.
  - Implement a deprecation policy for CLI flags with warnings before removal. Adhere strictly to semver where major versions signal breaking flag changes.
- **Roadmap Phase**: Phase 1

#### umami-software--umami

- **Overall Score**: 1.71 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-05-08
- **Category Scores**:
  - Infrastructure & DevOps: 1.27
  - Application Architecture: 2.00
  - Data Platform: 2.75
  - Security Baseline: 1.43
  - Operations & Observability: 1.11
- **Top Gaps**:
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - INF-Q1: score 1 — Managed Compute
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps
- **Key Recommendations**:
  - Deploy on Amazon EKS (preferred) with Fargate profiles for the application workload. Define Kubernetes Deployment manifests with health checks, resource limits, and HPA for auto-scaling.
  - Migrate PostgreSQL to Aurora PostgreSQL (preferred). Migrate Redis to Amazon ElastiCache. Consider Amazon MSK for Kafka replacement.
  - For the event ingestion pipeline and report generation workflows, consider AWS Step Functions to manage retry logic, error handling, and state transitions.
- **Roadmap Phase**: Phase 1

#### Lidarr--Lidarr

- **Overall Score**: 1.76 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.33
  - Application Architecture: 2.17
  - Data Platform: 2.50
  - Security Baseline: 1.67
  - Operations & Observability: 1.11
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q10: score 1 — Infrastructure as Code
  - APP-Q2: score 1 — Monolith vs Microservices
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize the application using .NET 8 runtime and deploy to EKS with Fargate.
  - Migrate to Aurora PostgreSQL. Application already has full PostgreSQL support.
  - Extract the download-import-organize pipeline into AWS Step Functions for retry logic and visibility.
- **Roadmap Phase**: Phase 1

#### Prowlarr--Prowlarr

- **Overall Score**: 1.76 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.18
  - Application Architecture: 2.33
  - Data Platform: 2.75
  - Security Baseline: 1.43
  - Operations & Observability: 1.11
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - OPS-Q1: score 1 — Distributed Tracing
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize using .NET 8 container support and deploy to Amazon EKS. Create Dockerfile based on existing self-contained publish configuration.
  - Migrate PostgreSQL workloads to Amazon Aurora PostgreSQL. Application already has full PostgreSQL support via Npgsql driver.
  - Consider AWS Step Functions for indexer sync → notification → history → app sync workflow when deploying to cloud.
- **Roadmap Phase**: Phase 1

#### Radarr--Radarr

- **Overall Score**: 1.86 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.22
  - Application Architecture: 2.33
  - Data Platform: 2.75
  - Security Baseline: 1.67
  - Operations & Observability: 1.33
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - SEC-Q5: score 1 — Secrets Management
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize the application and deploy to EKS (preferred). Create a Dockerfile using the .NET 8 runtime base image.
  - Migrate to Aurora PostgreSQL (preferred). The application already supports PostgreSQL natively via FluentMigrator.
  - Introduce EventBridge (preferred) for cross-service events and SQS for durable command queues when decomposing.
- **Roadmap Phase**: Phase 1

#### zappa--Zappa

- **Overall Score**: 1.86 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.17
  - Application Architecture: 2.25
  - Data Platform: 2.50
  - Security Baseline: 1.60
  - Operations & Observability: 1.80
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**:
  - If operational hosting is desired (e.g., Zappa-as-a-Service), consider deploying as a containerized service on EKS. For current CLI usage, this gap is inherent to the tool's nature.
  - Tighten default IAM policies to use least-privilege resource-scoped permissions. Document network security best practices for users.
  - If a service-based deployment API is desired, consider exposing behind API Gateway with authentication. For CLI usage, this is inherent to the design.
- **Roadmap Phase**: Phase 1

#### Sonarr--Sonarr

- **Overall Score**: 1.88 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.22
  - Application Architecture: 2.40
  - Data Platform: 3.00
  - Security Baseline: 1.57
  - Operations & Observability: 1.22
- **Top Gaps**:
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - INF-Q1: score 1 — Managed Compute
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize the .NET 10 application and deploy to Amazon EKS. Create a modern Dockerfile using the .NET 10 ASP.NET runtime image.
  - Migrate to Amazon Aurora PostgreSQL for the PostgreSQL deployment path. Existing Npgsql driver and FluentMigrator migrations are compatible.
  - Define a VPC with private subnets for application and database tiers. Use security groups with least-privilege rules. Place API behind ALB or API Gateway.
- **Roadmap Phase**: Phase 1

#### Alluxio--alluxio

- **Overall Score**: 1.90 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 2.00
  - Application Architecture: 2.25
  - Data Platform: 2.75
  - Security Baseline: 1.29
  - Operations & Observability: 1.22
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - SEC-Q2: score 1 — Encryption at Rest
  - OPS-Q2: score 1 — SLO Definitions
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps
- **Key Recommendations**:
  - Standardize on EKS as primary deployment target. Add EKS-specific configs (IRSA, EBS CSI, ALB Ingress). Deprecate Vagrant/VM path.
  - Evaluate Aurora or DynamoDB for journal durability. Migrate ZooKeeper to managed alternative. RocksDB for hot metadata may remain architecturally appropriate.
  - Add Kubernetes NetworkPolicy to Helm chart. Deploy on EKS in private subnets. Enable gRPC TLS. Add VPC endpoints for S3 access.
- **Roadmap Phase**: Phase 1

#### thingsboard--thingsboard

- **Overall Score**: 1.90 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.27
  - Application Architecture: 2.33
  - Data Platform: 2.50
  - Security Baseline: 1.86
  - Operations & Observability: 1.56
- **Top Gaps**:
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - INF-Q1: score 1 — Managed Compute
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Managed Analytics, Move to Modern DevOps
- **Key Recommendations**:
  - Migrate to Amazon EKS with Helm charts for each service type. Use EKS managed node groups with Graviton instances.
  - Migrate PostgreSQL to Amazon Aurora PostgreSQL for managed multi-AZ, automated backups, and PITR. Migrate Redis/Valkey to Amazon ElastiCache.
  - Adopt AWS Step Functions for operational workflows (device provisioning, OTA rollouts, alarm escalation).
- **Roadmap Phase**: Phase 1

#### Graylog2--graylog2-server

- **Overall Score**: 1.97 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.36
  - Application Architecture: 2.17
  - Data Platform: 2.75
  - Security Baseline: 2.00
  - Operations & Observability: 1.56
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Containerize the application and deploy on Amazon EKS. Create a production Dockerfile, define Kubernetes manifests with StatefulSets for journal-dependent components.
  - Migrate MongoDB to Amazon DocumentDB and OpenSearch to Amazon OpenSearch Service for automated backups, Multi-AZ failover, and managed patching.
  - Adopt AWS Step Functions for multi-step operations like index rotation, data migration, and event correlation workflows. EventBridge can trigger workflows based on system events.
- **Roadmap Phase**: Phase 1

#### OpenAPITools--openapi-generator

- **Overall Score**: 1.97 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.67
  - Application Architecture: 2.50
  - Data Platform: 2.50
  - Security Baseline: 1.67
  - Operations & Observability: 1.50
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - SEC-Q1: score 1 — Audit Logging
  - SEC-Q4: score 1 — Centralized Identity Integration
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**:
  - Deploy the online service to EKS (per preferences) or ECS Fargate with managed health checks, auto-scaling, and service discovery. Define the deployment as IaC.
  - Define VPC with private subnets for the online service. Deploy behind an ALB or API Gateway in public subnets with the application in private subnets.
  - Place the online service behind API Gateway with throttling, authentication, and request validation.
- **Roadmap Phase**: Phase 1

#### conductor-oss--conductor

- **Overall Score**: 1.99 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.45
  - Application Architecture: 2.50
  - Data Platform: 3.25
  - Security Baseline: 1.29
  - Operations & Observability: 1.44
- **Top Gaps**:
  - SEC-Q3: score 1 — API Authentication
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - SEC-Q5: score 2 — Secrets Management
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Deploy to Amazon EKS with managed node groups. Create Kubernetes Deployment manifests for the conductor-server container image.
  - Migrate to Aurora PostgreSQL, ElastiCache for Redis, and Amazon OpenSearch Service.
  - For operational workflows around the system itself (deployment orchestration, data migration), consider AWS Step Functions. The application's core orchestration function is appropriately custom.
- **Roadmap Phase**: Phase 1

#### iterative--dvc

- **Overall Score**: 2.06 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.50
  - Application Architecture: 2.50
  - Data Platform: 2.67
  - Security Baseline: 2.25
  - Operations & Observability: 1.38
- **Top Gaps**:
  - APP-Q2: score 1 — Monolith vs Microservices
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - If cloud-hosted DVC capabilities are desired, define compute infrastructure using EKS (preferred) with Terraform or CDK. The existing Celery-based experiment queue worker is a natural candidate for cloud-hosted compute.
  - If cloud infrastructure is introduced, define VPC with private subnets, least-privilege security groups, and VPC endpoints for AWS service access.
  - If a cloud-hosted DVC API is created, use API Gateway with throttling, authentication, and request validation.
- **Roadmap Phase**: Phase 2

#### FlowiseAI--Flowise

- **Overall Score**: 2.14 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2025-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.45
  - Application Architecture: 2.33
  - Data Platform: 3.25
  - Security Baseline: 2.00
  - Operations & Observability: 1.67
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Deploy on EKS with separate Deployments for the main server and BullMQ worker. Use Fargate for burstable worker pods. Define Helm charts for both workloads.
  - Migrate to Aurora PostgreSQL for the primary database with Multi-AZ failover. Use ElastiCache for Redis.
  - Evaluate AWS Step Functions for document processing and chatflow execution workflows.
- **Roadmap Phase**: Phase 2

#### realworld-apps--angular-realworld-example-app

- **Overall Score**: 2.18 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.50
  - Application Architecture: 2.50
  - Data Platform: 4.00
  - Security Baseline: 1.50
  - Operations & Observability: 1.38
- **Top Gaps**:
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - APP-Q2: score 1 — Monolith vs Microservices
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Cloud Native, Move to Modern DevOps
- **Key Recommendations**:
  - Define hosting infrastructure in Terraform or CDK: S3 bucket for static assets, CloudFront distribution with OAC, Route 53 DNS records, ACM certificate for TLS.
  - Extend GitHub Actions to deploy build artifacts to AWS (S3 upload + CloudFront invalidation). Add environment promotion with approval gates.
  - For a reference/demo app of this size, full decomposition is not warranted. If independent deployment is desired: adopt Angular Module Federation for per-feature-module builds.
- **Roadmap Phase**: Phase 2

#### scality--cloudserver

- **Overall Score**: 2.22 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.73
  - Application Architecture: 2.50
  - Data Platform: 2.75
  - Security Baseline: 2.14
  - Operations & Observability: 2.00
- **Top Gaps**:
  - INF-Q5: score 1 — Network Security
  - INF-Q6: score 1 — API Entry Point
  - INF-Q7: score 1 — Auto-Scaling
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Define VPC with private subnets for database and application tiers. Place S3 API behind ALB in private subnets. Use security groups with least-privilege rules.
  - Deploy ALB in front of the service. For external-facing deployments, add CloudFront. Consider API Gateway for per-endpoint throttling.
  - Configure HPA in EKS based on request rate from existing Prometheus metrics on port 8002. Add cluster autoscaler for node-level scaling.
- **Roadmap Phase**: Phase 2

#### coreui--coreui-free-angular-admin-template

- **Overall Score**: 2.23 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-05-07
- **Category Scores**:
  - Infrastructure & DevOps: 1.17
  - Application Architecture: 3.33
  - Data Platform: 4.00
  - Security Baseline: 1.50
  - Operations & Observability: 1.13
- **Top Gaps**:
  - INF-Q10: score 1 — Infrastructure as Code Coverage
  - INF-Q1: score 1 — Managed Compute
  - INF-Q11: score 2 — CI/CD Automation
- **Triggered Pathways**: Move to Containers, Move to Modern DevOps
- **Key Recommendations**:
  - Define compute infrastructure using AWS CDK (TypeScript). For a static Angular application, the simplest approach is S3 + CloudFront. For containerized deployment aligned with preferences, use Amazon EKS with a Nginx-based container serving static assets.
  - When defining deployment infrastructure, ensure the application is served via CloudFront with origin access control to a private S3 bucket, or deploy containers in a VPC with private subnets and a load balancer in public subnets.
  - Deploy with Amazon CloudFront as the entry point, providing CDN caching, HTTPS termination, and DDoS protection. Alternatively, use API Gateway as a frontend to the containerized application.
- **Roadmap Phase**: Phase 2

#### openzipkin--zipkin

- **Overall Score**: 2.28 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.73
  - Application Architecture: 2.83
  - Data Platform: 2.50
  - Security Baseline: 2.14
  - Operations & Observability: 2.22
- **Top Gaps**:
  - INF-Q5: score 1 — Network Security
  - INF-Q6: score 1 — API Entry Point
  - INF-Q10: score 1 — Infrastructure as Code Coverage
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Define VPC with private subnets for databases and public subnet for the Zipkin server. Create security groups with least-privilege rules. Use VPC endpoints for AWS service access.
  - Deploy an ALB in front of EKS, or use API Gateway for the query API with throttling and authentication.
  - Configure HPA on EKS based on CPU/memory and custom metrics. Consider Karpenter for node-level autoscaling.
- **Roadmap Phase**: Phase 2

#### ToolJet--ToolJet

- **Overall Score**: 2.31 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 2.27
  - Application Architecture: 2.67
  - Data Platform: 2.75
  - Security Baseline: 2.29
  - Operations & Observability: 1.56
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - INF-Q7: score 1 — Auto-Scaling
  - INF-Q8: score 1 — Backup and Recovery
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Add aws_cloudtrail resource to Terraform with log file validation and S3 Object Lock for immutable storage. Enable for all management and data events on sensitive resources.
  - Configure ECS Application Auto Scaling with target tracking. For EKS, configure HPA with custom metrics. Consider Karpenter for node scaling.
  - Set backup_retention_period=7 on RDS with PITR. Remove skip_final_snapshot. Create AWS Backup plan. Migrate Redis to ElastiCache with backup.
- **Roadmap Phase**: Phase 2

#### hapifhir--hapi-fhir

- **Overall Score**: 2.35 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 1.45
  - Application Architecture: 2.83
  - Data Platform: 3.25
  - Security Baseline: 2.17
  - Operations & Observability: 2.25
- **Top Gaps**:
  - INF-Q1: score 1 — Managed Compute
  - INF-Q5: score 1 — Network Security
  - INF-Q10: score 1 — Infrastructure as Code
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps
- **Key Recommendations**:
  - Define EKS cluster infrastructure in CDK/Terraform. Create a production Dockerfile for the Spring Boot application. Deploy on EKS with Fargate node pools.
  - Provision Aurora PostgreSQL via IaC with Multi-AZ, automated backups, and auto-scaling. Use DynamoDB for session/cache workloads.
  - Evaluate migrating Batch2 coordination to AWS Step Functions or maintain the custom framework on managed compute (EKS) with proper monitoring.
- **Roadmap Phase**: Phase 2

#### gulpjs--gulp

- **Overall Score**: 2.38 / 4.0
- **Repository Type**: library
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 2.83
  - Data Platform: 3.67
  - Security Baseline: 2.00
  - Operations & Observability: 1.00
- **Top Gaps**:
  - OPS-Q1: score 1 — Distributed Tracing
  - SEC-Q1: score 1 — Audit Logging
  - SEC-Q3: score 1 — API Authentication
- **Triggered Pathways**: None
- **Key Recommendations**:
  - Consider adding optional OpenTelemetry instrumentation for task execution spans. Implement as an opt-in plugin or optional dependency to avoid adding overhead for users who don't need tracing.
  - Consider adding structured logging output (via a logging interface that consumers can configure) for task execution events. For a build-tool library this is a low-priority enhancement.
  - No action needed. A build-tool library consumed locally does not require API authentication.
- **Roadmap Phase**: Phase 2

#### druid

- **Overall Score**: 2.48 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 2.00
  - Application Architecture: 3.25
  - Data Platform: 3.00
  - Security Baseline: 2.14
  - Operations & Observability: 2.00
- **Top Gaps**:
  - INF-Q5: score 1 — Network Security
  - INF-Q8: score 1 — Backup and Recovery
  - SEC-Q1: score 1 — Audit Logging
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**:
  - Define VPC architecture as IaC: private subnets for Druid data nodes (Historical, MiddleManager), restricted subnets for coordination (Coordinator, Overlord), and public-facing Router/Broker behind an ALB or API Gateway. Implement security groups with least-privilege rules between service tiers.
  - Place an Application Load Balancer or API Gateway (preferred per preferences) in front of the Router service. Configure throttling, request validation, and WAF integration. Use API Gateway for external query consumers with usage plans and API keys.
  - Define Kubernetes HPA for Broker and Router services (scale on query latency/CPU). Define cluster autoscaler for Historical nodes (scale on segment storage pressure). Consider KEDA for MiddleManager scaling based on pending task queue depth.
- **Roadmap Phase**: Phase 2

#### getlift--lift

- **Overall Score**: 2.60 / 4.0
- **Repository Type**: library
- **Priority**: P2
- **Assessment Date**: 2026-05-07
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 3.00
  - Data Platform: 2.75
  - Security Baseline: 2.67
  - Operations & Observability: 2.00
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - APP-Q5: score 2 — API Versioning Strategy
  - DATA-Q4: score 2 — Stored Procedures and Schema Complexity
- **Triggered Pathways**: None
- **Key Recommendations**:
  - Add an optional audit/logging configuration to the plugin's top-level lift config that provisions a CloudTrail trail. Alternatively, document audit logging requirements clearly.
  - Introduce construct schema versioning or implement a deprecation-warning mechanism. Add a CHANGELOG.md with explicit breaking-change callouts per release.
  - Make the DynamoDB construct's attribute names configurable via the schema definition. Allow custom partition/sort key names, TTL attribute, and LSI/GSI patterns. Keep current defaults.
- **Roadmap Phase**: Phase 3

#### tqdm--tqdm

- **Overall Score**: 2.60 / 4.0
- **Repository Type**: library
- **Priority**: P2
- **Assessment Date**: 2026-05-08
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 3.17
  - Data Platform: 2.75
  - Security Baseline: 2.50
  - Operations & Observability: 2.00
- **Top Gaps**:
  - OPS-Q1: score 2 — No distributed tracing instrumentation in the library
  - SEC-Q1: score 2 — No SBOM generation or formal release audit trail
  - SEC-Q6: score 2 — No dependency vulnerability scanning configured
- **Triggered Pathways**: None
- **Key Recommendations**:
  - Drop Python 3.7 (and consider 3.8) support to align with actively maintained Python versions, simplify the codebase, and remove the importlib_metadata dependency.
  - Add a CHANGELOG.md following Keep a Changelog format. Document the semver policy and planned v5.0.0 breaking changes in a migration guide.
  - Make all external service base URLs configurable via constructor parameters. This is a minor improvement for a library's optional notification integrations.
- **Roadmap Phase**: Phase 3

#### apache--flink-connector-aws

- **Overall Score**: 2.68 / 4.0
- **Repository Type**: monorepo
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: 2.00
  - Application Architecture: 3.50
  - Data Platform: 3.67
  - Security Baseline: 2.00
  - Operations & Observability: 2.25
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - OPS-Q7: score 1 — Incident Response Automation
  - INF-Q10: score 2 — Infrastructure as Code Coverage
- **Triggered Pathways**: Move to Modern DevOps
- **Key Recommendations**:
  - Enable GitHub audit log streaming. Add automated CHANGELOG generation. Ensure Apache release signing and verification steps are documented and auditable.
  - Codify build environment requirements as reusable composite actions or container definitions. If AWS resources are used for E2E testing, define them in IaC.
  - Add automated release workflow for Maven Central publishing. Integrate OWASP dependency-check or Snyk as CI step. Add CodeQL as a required check.
- **Roadmap Phase**: Phase 3

#### serverless--serverless

- **Overall Score**: 2.77 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 3.00
  - Data Platform: 3.67
  - Security Baseline: 2.17
  - Operations & Observability: 2.25
- **Top Gaps**:
  - SEC-Q1: score 1 — No audit logging configuration for release infrastructure
  - OPS-Q7: score 1 — No runbooks or incident response automation
  - OPS-Q9: score 1 — No resource tagging governance
- **Triggered Pathways**: None
- **Key Recommendations**:
  - Define CloudTrail configuration for the release AWS accounts as IaC. Ensure log file validation is enabled and logs are stored in an immutable S3 bucket with Object Lock.
  - Complete migration from AWS SDK v2 to v3. Replace the aws-sdk dependency in packages/serverless/package.json with specific v3 client packages.
  - Add explicit API versioning to the MCP server tool definitions. Document the plugin API contract with version markers. Consider frameworkVersion validation for configuration features.
- **Roadmap Phase**: Phase 3

#### webpack--webpack

- **Overall Score**: 2.88 / 4.0
- **Repository Type**: library
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 3.17
  - Data Platform: 3.33
  - Security Baseline: 2.00
  - Operations & Observability: 3.00
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - SEC-Q4: score 1 — Centralized Identity Integration
  - SEC-Q3: score 2 — API Authentication
- **Triggered Pathways**: None
- **Key Recommendations**:
  - Implement npm provenance/Sigstore artifact signing to create an immutable, verifiable audit trail for published packages. Consider enabling GitHub audit log streaming.
  - For an open-source library, GitHub's native identity management is standard practice. If the organization has enterprise requirements, consider GitHub Enterprise with SAML SSO enforcement.
  - Enable npm provenance publishing (--provenance flag) which uses OIDC tokens from GitHub Actions to cryptographically attest package origin, eliminating long-lived NPM_TOKEN secrets.
- **Roadmap Phase**: Phase 3

#### getsentry--sentry-python

- **Overall Score**: 2.95 / 4.0
- **Repository Type**: library
- **Priority**: P2
- **Assessment Date**: 2025-05-07
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 3.33
  - Data Platform: 3.25
  - Security Baseline: 2.20
  - Operations & Observability: 3.00
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - SEC-Q5: score 1 — Secrets Management
  - APP-Q6: score 2 — Service Discovery
- **Triggered Pathways**: None
- **Key Recommendations**:
  - For the release pipeline security: consider enabling CloudTrail for the AWS account that publishes Lambda Layers. Document the audit trail for release artifacts (PyPI, Lambda Layer, GitHub Releases) and ensure release provenance is traceable.
  - Document secrets rotation procedures for release pipeline credentials. Consider using AWS Secrets Manager for the AWS credentials used in Lambda Layer publishing, with automated rotation. Add a SECURITY.md file documenting secrets handling practices.
  - Consider publishing a structured integration manifest (JSON/YAML) listing all integrations with their supported library versions, capabilities, and configuration schemas.
- **Roadmap Phase**: Phase 3

#### arrow

- **Overall Score**: 2.96 / 4.0
- **Repository Type**: library
- **Priority**: P2
- **Assessment Date**: Unknown
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 3.33
  - Data Platform: 4.00
  - Security Baseline: 2.50
  - Operations & Observability: 2.00
- **Top Gaps**:
  - SEC-Q1: score 1 — Audit Logging
  - OPS-Q1: score 2 — Distributed Tracing
  - SEC-Q6: score 2 — Compute Hardening and Patching
- **Triggered Pathways**: None
- **Key Recommendations**:
  - Adopt PyPI Trusted Publishers (OIDC-based publishing) to eliminate long-lived API tokens. Add Sigstore signing for release artifacts to create a verifiable audit trail.
  - Consider adding optional OpenTelemetry instrumentation (as an optional dependency) that creates spans for parsing and timezone conversion operations.
  - Add pip ecosystem to Dependabot configuration. Add pip-audit to CI pipeline for explicit vulnerability scanning.
- **Roadmap Phase**: Phase 3

#### dwyl--aws-sdk-mock

- **Overall Score**: 2.99 / 4.0
- **Repository Type**: library
- **Priority**: P2
- **Assessment Date**: 2025-05-07
- **Category Scores**:
  - Infrastructure & DevOps: N/A
  - Application Architecture: 3.33
  - Data Platform: 2.75
  - Security Baseline: 2.86
  - Operations & Observability: 3.00
- **Top Gaps**:
  - APP-Q5: score 2 — API Versioning Strategy
  - DATA-Q3: score 2 — Database Engine Version and EOL
  - SEC-Q3: score 2 — API Authentication
- **Triggered Pathways**: None
- **Key Recommendations**:
  - Consider internal decomposition of src/index.ts into focused modules (e.g., registry.ts, service-mocker.ts, method-mocker.ts) for maintainability without changing the public API.
  - Add a CHANGELOG.md documenting breaking changes per version. Add JSDoc @deprecated annotations for legacy APIs. Update README to accurately reflect v3-only status.
  - Consider implementing automatic discovery of installed @aws-sdk/client-* packages to reduce manual registry configuration for consumers.
- **Roadmap Phase**: Phase 3

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | Alluxio--alluxio | Alluxio--alluxio/modernization-assessment/Alluxio--alluxio-mod-report.json | Unknown | application | 1.90 |
| 2 | FlowiseAI--Flowise | FlowiseAI--Flowise/modernization-assessment/FlowiseAI--Flowise-mod-report.json | 2025-05-07 | application | 2.14 |
| 3 | Graylog2--graylog2-server | Graylog2--graylog2-server/modernization-assessment/Graylog2--graylog2-server-mod-report.json | 2025-05-07 | application | 1.97 |
| 4 | Lidarr--Lidarr | Lidarr--Lidarr/modernization-assessment/Lidarr--Lidarr-mod-report.json | 2025-05-07 | application | 1.76 |
| 5 | Netflix--eureka | Netflix--eureka/modernization-assessment/Netflix--eureka-mod-report.json | 2026-05-07 | application | 1.50 |
| 6 | OpenAPITools--openapi-generator | OpenAPITools--openapi-generator/modernization-assessment/OpenAPITools--openapi-generator-mod-report.json | 2026-05-07 | application | 1.97 |
| 7 | Prowlarr--Prowlarr | Prowlarr--Prowlarr/modernization-assessment/Prowlarr--Prowlarr-mod-report.json | Unknown | application | 1.76 |
| 8 | Radarr--Radarr | Radarr--Radarr/modernization-assessment/Radarr--Radarr-mod-report.json | 2025-05-07 | application | 1.86 |
| 9 | Sonarr--Sonarr | Sonarr--Sonarr/modernization-assessment/Sonarr--Sonarr-mod-report.json | Unknown | application | 1.88 |
| 10 | ToolJet--ToolJet | ToolJet--ToolJet/modernization-assessment/ToolJet--ToolJet-mod-report.json | Unknown | application | 2.31 |
| 11 | apache--flink-connector-aws | apache--flink-connector-aws/modernization-assessment/apache--flink-connector-aws-mod-report.json | Unknown | monorepo | 2.68 |
| 12 | arrow | arrow-py--arrow/modernization-assessment/arrow-py--arrow-mod-report.json | Unknown | library | 2.96 |
| 13 | conductor-oss--conductor | conductor-oss--conductor/modernization-assessment/conductor-oss--conductor-mod-report.json | Unknown | application | 1.99 |
| 14 | coreui--coreui-free-angular-admin-template | coreui--coreui-free-angular-admin-template/modernization-assessment/coreui--coreui-free-angular-admin-template-mod-report.json | 2026-05-07 | application | 2.23 |
| 15 | druid | apache--druid/modernization-assessment/apache--druid-mod-report.json | Unknown | monorepo | 2.48 |
| 16 | dwyl--aws-sdk-mock | dwyl--aws-sdk-mock/modernization-assessment/dwyl--aws-sdk-mock-mod-report.json | 2025-05-07 | library | 2.99 |
| 17 | getlift--lift | getlift--lift/modernization-assessment/getlift--lift-mod-report.json | 2026-05-07 | library | 2.60 |
| 18 | getsentry--sentry-python | getsentry--sentry-python/modernization-assessment/getsentry--sentry-python-mod-report.json | 2025-05-07 | library | 2.95 |
| 19 | greenshot--greenshot | greenshot--greenshot/modernization-assessment/greenshot--greenshot-mod-report.json | Unknown | application | 1.54 |
| 20 | gulpjs--gulp | gulpjs--gulp/modernization-assessment/gulpjs--gulp-mod-report.json | Unknown | library | 2.38 |
| 21 | hapifhir--hapi-fhir | hapifhir--hapi-fhir/modernization-assessment/hapifhir--hapi-fhir-mod-report.json | Unknown | application | 2.35 |
| 22 | iterative--dvc | iterative--dvc/modernization-assessment/iterative--dvc-mod-report.json | 2026-05-07 | application | 2.06 |
| 23 | motdotla--node-lambda | motdotla--node-lambda/modernization-assessment/motdotla--node-lambda-mod-report.json | Unknown | application | 1.56 |
| 24 | ngx-admin | akveo--ngx-admin/modernization-assessment/akveo--ngx-admin-mod-report.json | 2025-05-07 | application | 1.50 |
| 25 | openzipkin--zipkin | openzipkin--zipkin/modernization-assessment/openzipkin--zipkin-mod-report.json | Unknown | application | 2.28 |
| 26 | realworld-apps--angular-realworld-example-app | realworld-apps--angular-realworld-example-app/modernization-assessment/realworld-apps--angular-realworld-example-app-mod-report.json | Unknown | application | 2.18 |
| 27 | scality--cloudserver | scality--cloudserver/modernization-assessment/scality--cloudserver-mod-report.json | Unknown | application | 2.22 |
| 28 | serverless--serverless | serverless--serverless/serverless--serverless-mod-report.json | Unknown | application | 2.77 |
| 29 | thingsboard--thingsboard | thingsboard--thingsboard/modernization-assessment/thingsboard--thingsboard-mod-report.json | Unknown | application | 1.90 |
| 30 | tqdm--tqdm | tqdm--tqdm/modernization-assessment/tqdm--tqdm-mod-report.json | 2026-05-08 | library | 2.60 |
| 31 | umami-software--umami | umami-software--umami/modernization-assessment/umami-software--umami-mod-report.json | 2026-05-08 | application | 1.71 |
| 32 | webpack--webpack | webpack--webpack/modernization-assessment/webpack--webpack-mod-report.json | Unknown | library | 2.88 |
| 33 | zappa--Zappa | zappa--Zappa/modernization-assessment/zappa--Zappa-mod-report.json | Unknown | application | 1.86 |
