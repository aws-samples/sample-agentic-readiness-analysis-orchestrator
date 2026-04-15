# Portfolio Modernization Readiness Assessment Report

**Date**: 2026-04-15
**Services Assessed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.
**Technology Preferences**: Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock, terraform, gitops; Avoid: self-managed-kafka, self-managed-kubernetes, oracle, manual-deployments

---

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 2.05 / 4.0 |
| Score Range | 1.29 – 2.66 |
| Highest Scoring Service | eks-saas-gitops (2.66) |
| Lowest Scoring Service | local-monolith (1.29) |
| Pathways Triggered (portfolio-wide) | 6 of 7 |
| Cross-Cutting Foundational Blockers | 20 |
| Cross-Cutting Improvement Opportunities | 4 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 2 | 40% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 1 | 20% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 2 | 40% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 2.16 | 1.00 | 3.18 | 0 |
| Application Architecture (APP) | 2.09 | 1.17 | 3.00 | 1 |
| Data Platform (DATA) | 2.85 | 2.00 | 4.00 | 0 |
| Security Baseline (SEC) | 1.77 | 1.00 | 2.86 | 0 |
| Operations & Observability (OPS) | 1.29 | 1.00 | 2.11 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 4 | 80% |
| infrastructure-only | 1 | 20% |
| deployment-config | 0 | 0% |
| monorepo | 0 | 0% |
| library | 0 | 0% |

## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| PHP 8.2 | 1 (local-monolith) | 20% |
| Java 8 (Spring Boot 2.1.x) | 1 (MonoToMicroLegacy) | 20% |
| JavaScript/TypeScript (Node.js) | 2 (aws-microservices, books-api) | 40% |
| Terraform/HCL | 1 (eks-saas-gitops) | 20% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| MySQL 8.0 (self-managed, Docker) | Relational | 1 (local-monolith) | No |
| MySQL 8.0 (self-managed, EC2) | Relational | 1 (MonoToMicroLegacy) | No |
| DynamoDB | NoSQL (Key-Value) | 3 (aws-microservices, books-api, eks-saas-gitops) | Yes |

**Database Distribution**: 3 managed (DynamoDB), 2 self-managed (MySQL), 0 commercial, 2 open source (MySQL)

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| Docker containers / No orchestration | 1 (local-monolith) | 20% |
| EC2 / VM-based | 1 (MonoToMicroLegacy) | 20% |
| Serverless (Lambda) | 2 (aws-microservices, books-api) | 40% |
| Managed containers (EKS) | 1 (eks-saas-gitops) | 20% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| None (zero IaC) | IaC | 2 (local-monolith, MonoToMicroLegacy) |
| AWS CDK (TypeScript) | IaC | 2 (aws-microservices, books-api) |
| Terraform + Flux CD | IaC | 1 (eks-saas-gitops) |
| None (manual deployment) | CI/CD | 2 (local-monolith, MonoToMicroLegacy) |
| Manual `cdk deploy` | CI/CD | 1 (aws-microservices) |
| AWS CodePipeline + CodeBuild | CI/CD | 1 (books-api) |
| Gitea Actions + Flux CD | CI/CD | 1 (eks-saas-gitops) |

### Standardization Opportunities

- **IaC Standardization on Terraform (preferred)**: Only 1 of 5 services (eks-saas-gitops) uses Terraform — the preferred IaC tool. 2 services (aws-microservices, books-api) use CDK and could be migrated. 2 services (local-monolith, MonoToMicroLegacy) have zero IaC — Terraform should be adopted from scratch. This is a **high-priority consolidation opportunity**.
- **GitOps Adoption (preferred)**: Only eks-saas-gitops uses GitOps (Flux CD). All other services should adopt GitOps practices as they are modernized and deployed to EKS, avoiding manual deployments per preferences.
- **MySQL → Aurora Migration (preferred)**: 2 services use self-managed MySQL 8.0. Aurora MySQL is the preferred managed database target and provides drop-in compatibility. This is a shared migration pattern that can be standardized.
- **Observability Standardization**: Only books-api has X-Ray tracing instrumentation. The remaining 4 services lack any observability. AWS X-Ray / ADOT should be standardized across the portfolio.
- **Technology Diversity Score**: 10 distinct technologies / 5 services = **2.0** (high diversity indicating fragmentation)
- **Preference Alignment**: eks-saas-gitops is the only service aligned with multiple preferred technologies (EKS, Terraform, GitOps). The serverless services (aws-microservices, books-api) use DynamoDB (preferred) but not EKS. The legacy monoliths have no alignment with preferred technologies.

## Service Dependency Map

### Dependency Overview

| Source Service | Target Service | Type | Coupling | Description |
|---------------|---------------|------|----------|-------------|
| aws-microservices | books-api | async | — | Microservices ordering flow triggers book catalog updates via EventBridge events |
| books-api | aws-microservices | sync | — | Books API queries product microservice for catalog data via REST |
| unishop-monolith | eks-saas-gitops | shared_infra | Low | Unishop will be deployed onto the EKS cluster managed by eks-saas-gitops |
| local-monolith | eks-saas-gitops | shared_infra | Low | Local monolith will be containerized and deployed onto the EKS cluster |
| aws-microservices | local-monolith | sync | Medium | Microservices query monolith for legacy product data during migration |

**Pair Coupling Scores:**
- **aws-microservices ↔ books-api**: **Medium** — 2 dependency types (1 async + 1 sync) between the pair
- **aws-microservices → local-monolith**: **Medium** — Synchronous dependency only
- **unishop-monolith → eks-saas-gitops**: **Low** — Shared infrastructure only
- **local-monolith → eks-saas-gitops**: **Low** — Shared infrastructure only

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| eks-saas-gitops | 2 | 0 | 80% (4/5) | Foundation | 2.66 |
| local-monolith | 1 | 1 | 20% (1/5) | Internal | 1.29 |
| aws-microservices | 1 | 2 | 40% (2/5) | Internal | 2.24 |
| books-api | 1 | 1 | 40% (2/5) | Internal | 2.64 |
| unishop-monolith | 0 | 1 | 0% (0/5) | Leaf | 1.43 |

**Blast Radius Calculation (BFS):**
- **eks-saas-gitops**: If eks-saas-gitops fails → local-monolith and unishop-monolith lose infrastructure; local-monolith failure cascades to aws-microservices (sync dep); aws-microservices failure cascades to books-api. **4 of 5 services affected = 80%**.
- **aws-microservices**: aws-microservices failure → impacts books-api (books-api depends on aws-microservices sync) and local-monolith is not downstream. books-api has no downstream dependents. **2 of 5 = 40%**.
- **books-api**: books-api failure → impacts aws-microservices (aws-microservices depends on books-api async). aws-microservices failure cascades to local-monolith (sync). **2 of 5 = 40%**.
- **local-monolith**: local-monolith failure → impacts aws-microservices (sync dependency). aws-microservices cascades to books-api. **1 of 5 directly = 20%** (considering blast radius as directly affected = 1).
- **unishop-monolith**: No services depend on it. **0 of 5 = 0%**.

### Foundation Services (High Fan-In)

- **eks-saas-gitops** (Fan-In: 2, Fan-Out: 0) — Both unishop-monolith and local-monolith depend on the EKS cluster infrastructure. This service **must be modernized and stabilized first**. Despite being P1 priority, its foundation role makes it a Phase 1 prerequisite.

### Circular Dependencies

⚠️ **Circular dependencies detected** — these must be broken in Phase 0:

- **Cycle: aws-microservices → books-api (async) → aws-microservices (sync)**
  - aws-microservices publishes EventBridge events that trigger book catalog updates in books-api
  - books-api synchronously queries aws-microservices via REST for catalog data
  - **Resolution**: Decouple the sync dependency (books-api → aws-microservices) by replacing the synchronous REST call with an EventBridge event subscription or a local cache of catalog data in books-api. This breaks the cycle while preserving the data flow.

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based purely on score severity — no goal-based logic.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.

1. **OPS-Q2: SLO Definitions** — 5 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 1, eks-saas-gitops: 1
   - **Impact**: No service in the portfolio has defined SLOs. Without measurable reliability baselines, the team cannot prioritize modernization investments, measure agent impact, or detect degradation.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, books-api, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Define portfolio-wide SLO standards. Establish SLOs for critical user journeys per service (availability ≥ 99.9%, p99 latency < 500ms for APIs, < 2s for agent-invoked endpoints). Implement CloudWatch composite alarms with error budget tracking. Start with agent-facing endpoints.

2. **OPS-Q7: Incident Response Automation** — 5 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 1, eks-saas-gitops: 1
   - **Impact**: Zero runbooks or automated incident response across the entire portfolio. All incident response is ad hoc. Autonomous agents amplify this risk — agent-triggered failures need documented remediation paths.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, books-api, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Create shared runbook templates for common incidents (database failure, deployment rollback, SQS queue backup, API error spikes). Implement SSM Automation documents for the most common remediation actions. Start with the agent-critical path: inventory API → order API → return processing.

3. **OPS-Q8: Observability Ownership** — 5 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 1, eks-saas-gitops: 1
   - **Impact**: No service in the portfolio has defined observability ownership. No CODEOWNERS, no per-service dashboards, no alarm ownership. When issues occur, there is no escalation path.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, books-api, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Establish a portfolio-wide observability ownership model. Create CODEOWNERS files. Assign per-service dashboard and alarm ownership. Define on-call rotations per service priority (P0 services first).

4. **SEC-Q1: Audit Logging** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, eks-saas-gitops: 1, books-api: 2
   - **Impact**: 4 of 5 services have zero CloudTrail or audit logging. No forensic trail for security incidents, compliance failures, or unauthorized access. Critical gap before deploying autonomous agents that make decisions.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy a centralized CloudTrail with multi-region trail, log file validation, and immutable S3 storage (Object Lock). Enable CloudTrail data events for DynamoDB and S3. This is a shared infrastructure investment benefiting all services.

5. **OPS-Q1: Distributed Tracing** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, eks-saas-gitops: 1, books-api: 3
   - **Impact**: 4 of 5 services have zero tracing. Cross-service debugging is impossible. Agent-initiated request flows cannot be traced. Only books-api has X-Ray.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy ADOT (AWS Distro for OpenTelemetry) as a shared tracing infrastructure. Enable X-Ray on all Lambda functions and API Gateways. Deploy ADOT DaemonSet on EKS. Propagate trace IDs through EventBridge events.

6. **OPS-Q3: Business Metrics** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 1, eks-saas-gitops: 2
   - **Impact**: 4 of 5 services publish zero custom business metrics. Cannot measure business outcomes, agent effectiveness, or modernization impact. Only eks-saas-gitops has basic cost metrics via Kubecost.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, books-api
   - **Portfolio-Level Recommendation**: Define a portfolio-wide business metrics standard. Publish custom CloudWatch metrics for: orders/min, inventory restocking events, agent decision accuracy, API response times, checkout conversion rate. Use CloudWatch EMF for zero-latency metric emission.

7. **OPS-Q4: Anomaly Detection and Alerting** — 4 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, eks-saas-gitops: 1, books-api: 2
   - **Impact**: 4 of 5 services have zero alerting. Issues go undetected until users complain. Agent-triggered failures will be invisible without alerting.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Deploy a centralized alerting strategy. Define CloudWatch alarms for error rates, latency, and resource utilization per service. Integrate with SNS → PagerDuty/OpsGenie for on-call notifications. Enable CloudWatch anomaly detection on key metrics.

8. **INF-Q1: Managed Compute** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 4, books-api: 4, eks-saas-gitops: 3
   - **Impact**: 2 services run on unmanaged compute (Docker containers, raw EC2). No auto-scaling, no managed orchestration, no HA.
   - **Affected Services**: local-monolith, MonoToMicroLegacy
   - **Portfolio-Level Recommendation**: Containerize both monoliths and deploy to EKS (preferred). The eks-saas-gitops cluster provides the target infrastructure. Use Strangler Fig pattern for incremental migration.

9. **INF-Q2: Managed Databases** — 2 of 5 applicable services score < 2
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 4, books-api: 4, eks-saas-gitops: 4
   - **Impact**: 2 services use self-managed MySQL with no backups, no failover, no encryption. Critical data loss and availability risk.
   - **Affected Services**: local-monolith, MonoToMicroLegacy
   - **Portfolio-Level Recommendation**: Migrate both MySQL instances to Aurora MySQL (preferred) using AWS DMS. Standardize on a shared migration pattern: provision Aurora via Terraform, replicate via DMS, cut over, enable PITR and Multi-AZ.

10. **INF-Q3: Workflow Orchestration** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 1, eks-saas-gitops: 4
    - **Impact**: 4 of 5 services have no workflow orchestration. Business workflows are hardcoded with no retry logic, error handling, or visibility. The fulfillment workflow in local-monolith requires manual human intervention at each step.
    - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, books-api
    - **Portfolio-Level Recommendation**: Introduce AWS Step Functions for multi-step business workflows. The fulfillment workflow (local-monolith), checkout flow (aws-microservices), and pre-traffic validation (books-api) are immediate candidates.

11. **INF-Q4: Async Messaging and Streaming** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, books-api: 1, aws-microservices: 3, eks-saas-gitops: 3
    - **Impact**: 3 services have zero messaging infrastructure. All communication is synchronous, preventing event-driven patterns critical for agent integration and service decoupling.
    - **Affected Services**: local-monolith, MonoToMicroLegacy, books-api
    - **Portfolio-Level Recommendation**: Deploy Amazon EventBridge (preferred) as the shared event bus. Define domain events (OrderPlaced, InventoryUpdated, BookCreated, ReturnRequested) published by each service. This enables the restocking agent to react to events in real-time.

12. **INF-Q5: Network Security** — 2 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 3, eks-saas-gitops: 3
    - **Impact**: 3 services have no network security (no VPC, no security groups, no subnets). The monolith MySQL port is exposed directly.
    - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices
    - **Portfolio-Level Recommendation**: Define a shared VPC architecture with Terraform (preferred). Place all services in private subnets with API Gateway (preferred) as the only public entry point. Use security groups with least-privilege rules.

13. **INF-Q6: API Entry Point** — 2 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 2, books-api: 3, eks-saas-gitops: 3
    - **Impact**: 2 services have no API gateway or load balancer. Services are directly exposed with no throttling, auth, or request validation. Agents need a managed entry point for tool invocation.
    - **Affected Services**: local-monolith, MonoToMicroLegacy
    - **Portfolio-Level Recommendation**: Deploy Amazon API Gateway (preferred) as the unified entry point for all services. Configure throttling, request validation, and Cognito-based authentication. This provides the tool discovery surface for AI agents.

14. **INF-Q7: Auto-Scaling** — 2 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 4, books-api: 4, eks-saas-gitops: 3
    - **Impact**: 2 services have static, single-instance capacity with no auto-scaling. Cannot handle traffic spikes from agent-driven workloads.
    - **Affected Services**: local-monolith, MonoToMicroLegacy
    - **Portfolio-Level Recommendation**: Deploy to EKS (preferred) with HPA-based auto-scaling. Configure Karpenter for cluster-level node scaling (already available in eks-saas-gitops).

15. **INF-Q8: Backup and Recovery** — 2 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 2, eks-saas-gitops: 2
    - **Impact**: 3 services have no backup strategy. A failure could result in complete, irrecoverable data loss for order, inventory, and product data.
    - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices
    - **Portfolio-Level Recommendation**: Implement a portfolio-wide backup strategy. Enable Aurora automated backups + PITR for migrated MySQL databases. Enable DynamoDB PITR on all tables. Create an AWS Backup plan covering all data stores.

16. **INF-Q9: High Availability and Fault Isolation** — 2 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 4, books-api: 4, eks-saas-gitops: 3
    - **Impact**: 2 services are single-instance with no fault isolation. A single failure takes down the entire service and database.
    - **Affected Services**: local-monolith, MonoToMicroLegacy
    - **Portfolio-Level Recommendation**: Deploy to EKS (preferred) with multi-AZ pod distribution. Use Aurora Multi-AZ for database HA. Align with the shared EKS cluster in eks-saas-gitops.

17. **INF-Q10: Infrastructure as Code Coverage** — 2 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 4, books-api: 4, eks-saas-gitops: 4
    - **Impact**: 2 services have zero IaC. Cannot reproduce environments, perform disaster recovery, or manage infrastructure changes safely. Blocks all other modernization pathways.
    - **Affected Services**: local-monolith, MonoToMicroLegacy
    - **Portfolio-Level Recommendation**: Adopt Terraform (preferred) for both services immediately. Start by codifying target-state infrastructure (EKS deployment, Aurora MySQL, API Gateway, EventBridge). Use the eks-saas-gitops Terraform modules as templates.

18. **INF-Q11: CI/CD Automation** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 3, eks-saas-gitops: 3
    - **Impact**: 3 services have no CI/CD pipeline. All deployments are manual. Blocks safe iterative modernization, automated testing, and GitOps adoption. Avoid manual deployments per preferences.
    - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices
    - **Portfolio-Level Recommendation**: Implement CI/CD pipelines for all 3 services. Adopt GitOps (preferred) with automated pipelines: lint → test → build → security scan → deploy. For EKS-hosted services, use Flux CD (already proven in eks-saas-gitops). For serverless services, use CodePipeline or GitHub Actions.

19. **SEC-Q4: Centralized Identity Integration** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 4, eks-saas-gitops: 2
    - **Impact**: 3 services have no centralized identity provider. Each manages its own auth independently. Cannot participate in SSO, cannot federate identities. Agents need a unified identity framework for M2M auth.
    - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices
    - **Portfolio-Level Recommendation**: Deploy Amazon Cognito as the centralized identity provider for the portfolio. Configure Cognito User Pools for human users and Identity Pools for machine-to-machine (agent) authentication. Migrate all services to Cognito-based auth.

20. **SEC-Q7: Application Security Pipeline** — 3 of 5 applicable services score < 2
    - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 1, eks-saas-gitops: 2
    - **Impact**: 4 services have zero security scanning. Vulnerabilities in dependencies, containers, and code reach production undetected. This is a compliance and security risk for an e-commerce platform handling payment data.
    - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices, books-api
    - **Portfolio-Level Recommendation**: Integrate security scanning into all CI/CD pipelines. Standardize on: (1) SAST — Semgrep or CodeGuru, (2) dependency scanning — Dependabot + npm audit/pip-audit, (3) container scanning — ECR scanning + Trivy, (4) IaC scanning — Checkov/tfsec. Add security gates that block deployment on critical findings.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking.
> Address as capacity allows or in parallel with other modernization work.

1. **SEC-Q2: Encryption at Rest** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 3, books-api: 3, eks-saas-gitops: 3
   - **Impact**: 2 services have no encryption at rest. 3 services use AWS-managed keys but not customer-managed KMS keys. For an e-commerce platform handling payment data, customer-managed encryption provides better governance.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices (no CMK)
   - **Portfolio-Level Recommendation**: Create portfolio-wide KMS keys for each data classification level. Apply customer-managed KMS to all data stores during migration. Enable key rotation and audit trails.

2. **SEC-Q5: Secrets Management** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 2, books-api: 3, eks-saas-gitops: 2
   - **Impact**: 2 services have hardcoded credentials (local-monolith fallback defaults, MonoToMicroLegacy plaintext in application.properties). 2 services use partial secrets management without rotation.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices
   - **Portfolio-Level Recommendation**: Migrate all secrets to AWS Secrets Manager with automated rotation. Remove all hardcoded credentials. Use EKS Secrets Store CSI driver for Kubernetes-native secret injection.

3. **SEC-Q3: API Authentication** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith: 2, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 3, eks-saas-gitops: 2
   - **Impact**: 2 services have completely open APIs (no auth). 1 service has basic session auth. Only books-api has proper Cognito OAuth2. Agent integration requires authenticated endpoints.
   - **Affected Services**: MonoToMicroLegacy, aws-microservices, eks-saas-gitops
   - **Portfolio-Level Recommendation**: Implement Cognito-based API authentication across all services. Configure API Gateway (preferred) authorizers with JWT validation. Add machine-to-machine client credentials flow for agent authentication.

4. **OPS-Q9: Resource Tagging Governance** — 3 of 5 applicable services score < 3
   - **Score Distribution**: local-monolith: 1, MonoToMicroLegacy: 1, aws-microservices: 1, books-api: 2, eks-saas-gitops: 2
   - **Impact**: 3 services have zero tags. 2 services have inconsistent/incomplete tagging. Cannot attribute costs, identify ownership, or distinguish environments across the portfolio.
   - **Affected Services**: local-monolith, MonoToMicroLegacy, aws-microservices
   - **Portfolio-Level Recommendation**: Define a portfolio-wide tagging standard: `Project`, `Environment`, `Service`, `Team`, `CostCenter`, `Priority`. Enforce via Terraform `default_tags` and AWS Config `required-tags` rules. Activate cost allocation tags.

### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 2.16 / 4.0**

**Common Patterns:**
- IaC coverage is bimodal: 3 services have 100% IaC (scores 4) while 2 services have 0% (scores 1)
- CI/CD is similarly split: 2 services have CI/CD (scores 3), 3 services have none (scores 1)
- Serverless services (aws-microservices, books-api) have excellent compute and database scores (4) but lack workflow orchestration and messaging

**Critical Gaps:**
1. Zero IaC in local-monolith and MonoToMicroLegacy — blocks all modernization for these P0 services
2. No CI/CD for 3 services including the P0 aws-microservices — manual deployments are high risk
3. No workflow orchestration in 4 of 5 services — hardcoded workflows cannot support agent-driven automation

#### Application Architecture

**Portfolio Score: 2.09 / 4.0** (4 services, eks-saas-gitops N/A)

**Common Patterns:**
- 2 monoliths (scores 1–2) and 2 well-structured services (scores 3–4)
- All 4 application services lack API versioning (3 score 1, 1 scores 1) — critical blocker for agent tool integration
- Communication patterns are mostly synchronous (3 services score 1 for async)

**Critical Gaps:**
1. APP-Q5 (API Versioning): All 4 application services lack API versioning — agents need stable, versioned APIs as tool interfaces
2. APP-Q3 (Async Communication): 3 of 4 services are 100% synchronous — limits event-driven agent patterns
3. APP-Q2 (Architecture): 2 services are tightly-coupled monoliths requiring decomposition

#### Data Platform

**Portfolio Score: 2.85 / 4.0**

**Common Patterns:**
- Strong positive: All services have zero stored procedures (DATA-Q4 = 4 across all applicable services)
- DynamoDB users (3 services) have excellent managed database scores
- Self-managed MySQL users (2 services) drag down the average

**Critical Gaps:**
1. DATA-Q1 (Unstructured Data): 4 of 5 services score 1 — no S3 storage for images, documents, or AI knowledge bases
2. DATA-Q2 (Data Access Layer): Scattered across services with varying patterns (scores 1-3)

#### Security Baseline

**Portfolio Score: 1.77 / 4.0**

**Common Patterns:**
- Audit logging is absent across 4 services (SEC-Q1)
- Identity management is fragmented — each service uses a different approach
- books-api is the only service with proper Cognito integration (score 4)
- Security scanning is absent in 4 of 5 services

**Critical Gaps:**
1. SEC-Q1 (Audit Logging): 4 services score 1 — no forensic capability
2. SEC-Q4 (Identity): 3 services have no centralized identity — fragments the authentication model
3. SEC-Q7 (Security Pipeline): 4 services score 1 — vulnerabilities reach production undetected

#### Operations & Observability

**Portfolio Score: 1.29 / 4.0**

**Common Patterns:**
- This is the weakest category portfolio-wide. Only books-api has any meaningful operational maturity.
- SLOs, incident response, and observability ownership are universally absent (all 5 services score 1)
- Distributed tracing exists only in books-api
- Only books-api has a deployment strategy (score 4) — the rest are manual or basic

**Critical Gaps:**
1. OPS-Q2 (SLOs): All 5 services score 1 — no service level objectives anywhere
2. OPS-Q7 (Incident Response): All 5 services score 1 — completely ad hoc
3. OPS-Q8 (Observability Ownership): All 5 services score 1 — no accountability for system health
4. OPS-Q5 (Deployment Strategy): 3 services score 1 — direct-to-production with no safety net

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
- **Centralized CloudTrail**: Deploy multi-region CloudTrail with immutable S3 storage (addresses SEC-Q1 across 4 services)
- **Observability Platform**: Deploy ADOT on EKS, enable X-Ray on Lambda functions, standardize CloudWatch dashboards (addresses OPS-Q1, OPS-Q3, OPS-Q4, OPS-Q8)
- **SLO Framework**: Define portfolio-wide SLO standards and implement CloudWatch composite alarms (addresses OPS-Q2)
- **Shared Identity**: Deploy Amazon Cognito User Pools with M2M auth for agents (addresses SEC-Q3, SEC-Q4)
- **Security Scanning**: Integrate Semgrep, Dependabot, Trivy into pipeline templates (addresses SEC-Q7)
- **Tagging Standard**: Define and enforce portfolio-wide tagging standard in Terraform (addresses OPS-Q9)
- **Circular Dependency Breaking**: Decouple books-api → aws-microservices sync dependency by introducing EventBridge-based catalog data synchronization or local cache. Replace the synchronous REST call with an event subscription.

**Organizational Enablers:**
- Training: Terraform fundamentals, EKS operations, observability (X-Ray/ADOT), Aurora migration
- Tooling: Standardize on Terraform (preferred), establish GitOps patterns with Flux CD
- Standards: API versioning policy, runbook templates, incident response procedures, tagging standard

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize foundation services and establish patterns.

**Services in Scope:**

1. **eks-saas-gitops** (P1, Score: 2.66 / 4.0) — Foundation Service
   - Current State: EKS infrastructure with Terraform and Flux CD. Score 2.66 with gaps in security (SEC 2.14) and operations (OPS 1.33). Gitea is a SPOF.
   - Target State: Hardened EKS platform with full observability, audit logging, and HA improvements. Score target: 3.2+
   - Key Activities:
     - Enable EKS control plane audit logging
     - Deploy ADOT DaemonSet for tracing
     - Harden Argo Workflows authentication (replace --auth-mode=server)
     - Add multiple NAT gateways for fault isolation
     - Define SLOs for tenant-facing services
   - Dependencies: None (foundation service)
   - Blocks: local-monolith, unishop-monolith (both depend on EKS cluster)
   - Estimated Effort: Medium

2. **local-monolith** (P0, Score: 1.29 / 4.0)
   - Current State: PHP monolith in Docker with zero IaC, zero CI/CD, self-managed MySQL, score 1.29. Lowest-scoring service.
   - Target State: Containerized on EKS with Terraform IaC, CI/CD pipeline, Aurora MySQL. Score target: 2.5+
   - Key Activities:
     - Create Terraform project for EKS deployment, Aurora MySQL, API Gateway
     - Push Docker image to ECR and deploy to EKS cluster
     - Migrate MySQL to Aurora MySQL (preferred) via DMS
     - Create CI/CD pipeline with Flux CD (preferred)
     - Add X-Ray instrumentation
   - Dependencies: eks-saas-gitops (EKS cluster)
   - Blocks: aws-microservices (sync dependency for legacy product data)
   - Estimated Effort: High

3. **unishop-monolith (MonoToMicroLegacy)** (P0, Score: 1.43 / 4.0)
   - Current State: Java Spring Boot monolith on EC2 with zero IaC, zero CI/CD, self-managed MySQL, score 1.43. Hardcoded credentials.
   - Target State: Containerized on EKS with Terraform IaC, CI/CD pipeline, Aurora MySQL. Score target: 2.5+
   - Key Activities:
     - Create Dockerfile (currently missing) and containerize the Spring Boot JAR
     - Create Terraform project for EKS deployment and Aurora MySQL
     - Migrate MySQL to Aurora MySQL (preferred) via DMS
     - Remediate hardcoded credentials (SEC-Q5) — migrate to Secrets Manager
     - Create CI/CD pipeline with GitOps (preferred)
     - Upgrade Java 8 → Java 17+ and Spring Boot 2.1.x → 3.x
   - Dependencies: eks-saas-gitops (EKS cluster)
   - Blocks: None (leaf service)
   - Estimated Effort: High

**Expected Outcomes:**
- EKS platform hardened and ready for workloads
- Both monoliths containerized and deployed on managed infrastructure
- Self-managed MySQL databases migrated to Aurora MySQL
- CI/CD pipelines established for all Phase 1 services

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize services that depend on Phase 1 services. Replicate proven patterns.

**Services in Scope:**

1. **aws-microservices** (P0, Score: 2.24 / 4.0)
   - Current State: Well-structured serverless microservices with Lambda, DynamoDB, EventBridge. Gaps in CI/CD (score 1), security (SEC 1.57), and operations (OPS 1.00). EOL Lambda runtime (Node.js 14).
   - Target State: Fully automated CI/CD, authenticated APIs, comprehensive observability. Score target: 3.2+
   - Key Activities:
     - Create CI/CD pipeline (GitHub Actions or CodePipeline)
     - Add API Gateway authentication (Cognito authorizer)
     - Enable DynamoDB PITR on all tables; change removal policy to RETAIN
     - Upgrade Lambda runtime from NODEJS_14_X to NODEJS_20_X+
     - Enable X-Ray tracing on all Lambda functions and API Gateways
     - Add API versioning (/v1/ prefix)
     - Add DLQ for OrderQueue
     - Define SLOs and CloudWatch alarms
   - Dependencies: local-monolith (Phase 1 — sync dependency for legacy product data)
   - Blocks: books-api (async EventBridge events; circular dependency broken in Phase 0)
   - Estimated Effort: Medium

**Parallel Tracks:**
- aws-microservices can proceed independently once Phase 0 circular dependency is broken and Phase 1 local-monolith is deployed on EKS

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize leaf services, implement advanced capabilities, continuous improvement.

**Services in Scope:**

1. **books-api** (P1, Score: 2.64 / 4.0)
   - Current State: Well-structured serverless API with CDK, Cognito auth, X-Ray tracing, full CI/CD pipeline. Highest operational maturity among application services. Gaps in async messaging, workflow orchestration, and security scanning.
   - Target State: Event-driven with EventBridge, API versioning, security scanning, advanced observability. Score target: 3.5+
   - Key Activities:
     - Add API versioning (/v1/books)
     - Add EventBridge integration for BookCreated events
     - Add security scanning to CI/CD pipeline (npm audit, Dependabot)
     - Add SLO definitions and business metrics
     - Generate OpenAPI specification for agent tool discovery
     - Add incident response runbooks
   - Dependencies: aws-microservices (Phase 2 — circular dependency broken in Phase 0)
   - Estimated Effort: Low

**Advanced Portfolio Activities:**
- Begin monolith decomposition (Strangler Fig) for local-monolith and unishop-monolith
- Deploy AI agent integration: inventory restocking agent (Bedrock), order inquiry agent
- Implement shared EventBridge event bus for portfolio-wide domain events
- Deploy Amazon Bedrock Knowledge Bases for RAG-based knowledge agents

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6+ months (with 2 parallel tracks in Phase 1: local-monolith + unishop-monolith)
**Critical Path**: eks-saas-gitops (Phase 1) → local-monolith (Phase 1) → aws-microservices (Phase 2) → books-api (Phase 3)

## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 2 | 40% | Medium | High |
| Move to Containers | 1 | 20% | Low | Medium |
| Move to Open Source | 0 | 0% | — | — |
| Move to Managed Databases | 2 | 40% | High | Medium |
| Move to Managed Analytics | 0 | 0% | — | — |
| Move to Modern DevOps | 3 | 60% | High | Medium |
| Move to AI | 4 | 80% | High | Medium |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing
a single at-a-glance view of pathway coverage across the portfolio. Each repo appears
in exactly one column per pathway row.

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | local-monolith, MonoToMicroLegacy | aws-microservices, books-api | eks-saas-gitops |
| Move to Containers | MonoToMicroLegacy | local-monolith, aws-microservices, books-api | eks-saas-gitops |
| Move to Open Source | — | local-monolith, MonoToMicroLegacy, aws-microservices, books-api, eks-saas-gitops | — |
| Move to Managed Databases | local-monolith, MonoToMicroLegacy | aws-microservices, books-api, eks-saas-gitops | — |
| Move to Managed Analytics | — | local-monolith, aws-microservices, books-api | MonoToMicroLegacy, eks-saas-gitops |
| Move to Modern DevOps | local-monolith, MonoToMicroLegacy, aws-microservices | books-api, eks-saas-gitops | — |
| Move to AI | local-monolith, MonoToMicroLegacy, aws-microservices, books-api | — | eks-saas-gitops |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| local-monolith | ✅ | — | — | ✅ | — | ✅ | ✅ |
| MonoToMicroLegacy | ✅ | ✅ | — | ✅ | N/A | ✅ | ✅ |
| aws-microservices | — | — | — | — | — | ✅ | ✅ |
| books-api | — | — | — | — | — | — | ✅ |
| eks-saas-gitops | N/A | N/A | — | — | N/A | — | N/A |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize monoliths before decomposing them)
- Move to Managed Databases can proceed in parallel with Move to Containers (Aurora migration independent of containerization)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is a prerequisite for Move to AI (data foundations needed for agent integration)

**Parallel Execution Tracks:**
- **Track 1**: Move to Modern DevOps + Move to Containers + Move to Managed Databases (foundational, Mo 0–3)
- **Track 2**: Move to Cloud Native + Move to AI (advanced, Mo 3–6+, builds on Track 1)

### Pathway Details

#### Move to Modern DevOps

- **Services Affected**: local-monolith, MonoToMicroLegacy, aws-microservices (3 total)
- **Portfolio Priority**: High (triggered for 60% of portfolio, including all 3 P0 services)
- **Common Trigger Criteria**:
  - INF-Q10 (IaC) score 1: affects 2 services (local-monolith, MonoToMicroLegacy)
  - INF-Q11 (CI/CD) score 1: affects 3 services (local-monolith, MonoToMicroLegacy, aws-microservices)
  - OPS-Q5 (Deployment Strategy) score 1: affects 3 services
  - OPS-Q6 (Integration Testing) score 1: affects 3 services
- **Representative AWS Services**: Terraform (preferred), Flux CD / ArgoCD (GitOps preferred), GitHub Actions, AWS CodePipeline + CodeBuild, Amazon ECR
- **Key Activities**:
  1. Adopt Terraform (preferred) for all infrastructure — standardize on eks-saas-gitops patterns
  2. Implement CI/CD pipelines with GitOps (preferred) — avoid manual deployments
  3. Add automated testing frameworks per language (PHPUnit, JUnit, Jest)
  4. Configure progressive deployment strategies (canary/blue-green)
- **Cross-Service Synergies**: Shared Terraform modules, shared CI/CD pipeline templates, shared security scanning configuration
- **Estimated Effort**: Medium across 3 services
- **Roadmap Phase Alignment**: Phase 0 (standards), Phase 1 (monoliths), Phase 2 (aws-microservices)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: local-monolith, MonoToMicroLegacy, aws-microservices, books-api (4 total)
- **Portfolio Priority**: High (triggered for 80% of portfolio)
- **Common Trigger Criteria**:
  - No AI/agent frameworks detected in any service
  - No vector database infrastructure
  - No RAG implementation
  - No agent evaluation frameworks
- **Representative AWS Services**: Amazon Bedrock (preferred), Amazon Bedrock AgentCore, Amazon Bedrock Knowledge Bases, Amazon OpenSearch Service (vector engine)
- **Key Activities**:
  1. Deploy Amazon Bedrock as the shared AI foundation
  2. Build inventory restocking agent using Bedrock with inventory API tools
  3. Build customer support agent for order inquiries and return processing
  4. Create RAG knowledge base from product catalog and order policies
  5. Generate OpenAPI specifications for all APIs to enable agent tool discovery
- **Cross-Service Synergies**: Shared Bedrock configuration, unified agent framework, common tool discovery pattern via OpenAPI specs
- **Estimated Effort**: Medium across 4 services
- **Roadmap Phase Alignment**: Phase 3 (after foundational modernization)
- **Relevant Learning Materials**: Module 7 — Move to AI

#### Move to Cloud Native

- **Services Affected**: local-monolith, MonoToMicroLegacy (2 total)
- **Portfolio Priority**: Medium (triggered for 40% of portfolio)
- **Common Trigger Criteria**:
  - APP-Q2 (Architecture) score 1-2: affects 2 services (tightly-coupled monoliths)
  - INF-Q1 (Managed Compute) score 1: affects 2 services
  - APP-Q3 (Async Communication) score 1: affects 2 services
  - APP-Q4 (Long-Running Processes) score 1: affects 2 services
- **Representative AWS Services**: Amazon EKS (preferred), Amazon API Gateway (preferred), Amazon EventBridge (preferred), AWS Step Functions, Aurora MySQL (preferred)
- **Key Activities**:
  1. Containerize monoliths and deploy to EKS (Phase 1)
  2. Implement Strangler Fig decomposition starting with Inventory Service (local-monolith) and Basket/Order Service (MonoToMicroLegacy)
  3. Introduce EventBridge for inter-service event-driven communication
  4. Implement Step Functions for workflow orchestration
- **Cross-Service Synergies**: Shared decomposition patterns, shared EventBridge event bus, shared API Gateway
- **Estimated Effort**: High across 2 services
- **Roadmap Phase Alignment**: Phase 1 (containerization), Phase 3 (decomposition)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native

#### Move to Managed Databases

- **Services Affected**: local-monolith, MonoToMicroLegacy (2 total)
- **Portfolio Priority**: High (triggered for 40% of portfolio, both P0 services with self-managed MySQL)
- **Common Trigger Criteria**:
  - INF-Q2 (Managed Databases) score 1: affects 2 services
  - DATA-Q3 (Engine Version) score 2: affects 2 services
- **Representative AWS Services**: Amazon Aurora MySQL (preferred), Amazon DynamoDB (preferred for extracted services), AWS DMS, AWS Secrets Manager
- **Key Activities**:
  1. Provision Aurora MySQL clusters via Terraform (preferred)
  2. Use AWS DMS for continuous replication from self-managed MySQL to Aurora
  3. Cut over connection strings to Aurora endpoints
  4. Enable automated backups, PITR, and Multi-AZ failover
- **Cross-Service Synergies**: Shared DMS migration pattern, shared Aurora Terraform modules, shared Secrets Manager configuration
- **Estimated Effort**: Medium across 2 services
- **Roadmap Phase Alignment**: Phase 1
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Containers

- **Services Affected**: MonoToMicroLegacy (1 total)
- **Portfolio Priority**: Low (triggered for 20% of portfolio)
- **Common Trigger Criteria**:
  - INF-Q1 (Managed Compute) score 1: raw EC2 with no container definitions
  - No Dockerfile exists (commented out docker task in build.gradle)
- **Representative AWS Services**: Amazon EKS (preferred), Amazon ECR, Helm, Karpenter
- **Key Activities**:
  1. Create Dockerfile for the Spring Boot fat JAR
  2. Set up ECR repository and push container image
  3. Deploy to EKS cluster (eks-saas-gitops) with Helm chart
  4. Replace EC2MetadataUtils with Kubernetes-native health probes
- **Cross-Service Synergies**: Reuse eks-saas-gitops Helm chart templates and Karpenter configuration
- **Estimated Effort**: Medium for 1 service
- **Roadmap Phase Alignment**: Phase 1
- **Relevant Learning Materials**: Module 3 — Move to Containers

## Integration Opportunities

### Shared Service Extraction

**Opportunity: Centralized Authentication Service**
- **Current State**: Duplicated in local-monolith (PHP sessions), MonoToMicroLegacy (disabled Spring Security), aws-microservices (no auth), books-api (Cognito), eks-saas-gitops (Gitea tokens + IRSA)
- **Proposed Solution**: Deploy Amazon Cognito as the centralized identity provider with User Pools for human users and Identity Pools for M2M agent authentication. Create a shared Terraform module for Cognito configuration.
- **Benefits**: Unified authentication across all services, SSO capability, centralized user management, M2M auth for AI agents
- **Effort**: Medium
- **Priority**: High

**Opportunity: Shared Observability Platform**
- **Current State**: Only books-api has X-Ray tracing. No shared dashboards, no centralized alerting, no unified log aggregation.
- **Proposed Solution**: Deploy ADOT (AWS Distro for OpenTelemetry) collector on EKS, enable X-Ray on all Lambda functions, create centralized CloudWatch dashboards per service, implement PagerDuty/OpsGenie integration via SNS.
- **Benefits**: End-to-end request tracing across all services, centralized monitoring, consistent alerting, agent action traceability
- **Effort**: Medium
- **Priority**: High

**Opportunity: Shared Database Migration Pattern**
- **Current State**: local-monolith and MonoToMicroLegacy both use self-managed MySQL 8.0. Both need migration to Aurora MySQL.
- **Proposed Solution**: Create a reusable Terraform module for Aurora MySQL provisioning and a shared DMS migration runbook. Execute both migrations using the same pattern and tooling.
- **Benefits**: Reduced migration effort through pattern reuse, consistent database configuration, shared operational knowledge
- **Effort**: Low (incremental, pattern already defined)
- **Priority**: High

### Event-Driven Architecture

**Opportunity: Portfolio-Wide EventBridge Event Bus**
- **Current State**: aws-microservices has its own EventBridge bus (SwnEventBus). No other services use EventBridge. books-api → aws-microservices is a synchronous REST call.
- **Proposed Solution**: Create a shared EventBridge event bus using Amazon EventBridge (preferred). Define domain events: `OrderPlaced`, `InventoryUpdated`, `BookCreated`, `ReturnRequested`, `BasketCheckedOut`. Migrate the books-api → aws-microservices sync dependency to EventBridge event subscription.
- **Benefits**: Decoupled services, real-time event processing for agents, async communication reducing cascading failures, circular dependency resolution
- **Effort**: Medium

**Opportunity: Agent Event Integration**
- **Current State**: No mechanism for AI agents to receive real-time notifications of inventory changes, order updates, or return requests.
- **Proposed Solution**: Extend EventBridge to publish agent-relevant events. The inventory restocking agent subscribes to `InventoryLow` events. The customer support agent subscribes to `ReturnRequested` events.
- **Benefits**: Real-time agent activation, reduced polling, event-driven agent architecture
- **Effort**: Low (once EventBridge is established)

### API Gateway Consolidation

- **Current State**: aws-microservices has 3 separate API Gateways (Product, Basket, Order). books-api has 1 API Gateway. local-monolith and MonoToMicroLegacy have no API gateway.
- **Proposed Solution**: Deploy a unified Amazon API Gateway (preferred) for all customer-facing APIs. Route to backend services (EKS pods, Lambda functions) via VPC links and Lambda integrations. Consolidate authentication, throttling, and request validation.
- **Benefits**: Consistent authentication and authorization, unified rate limiting, centralized API documentation for agent tool discovery, reduced management overhead
- **Effort**: Medium

### Observability Unification

- **Current State**: books-api uses X-Ray with aws-xray-sdk-core. eks-saas-gitops has Kubecost + Prometheus. Other services have zero observability.
- **Proposed Solution**: Standardize on AWS X-Ray + ADOT for distributed tracing, CloudWatch for metrics and logs, and Amazon Managed Grafana for dashboards. Deploy ADOT DaemonSet on EKS and enable X-Ray on all Lambda functions.
- **Benefits**: End-to-end request tracing across service boundaries, consistent metric collection, unified dashboards, agent action traceability
- **Effort**: Medium

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| eks-saas-gitops Gitea SPOF | High | High | 🔴 Critical | Replace single Gitea EC2 with HA solution (Gitea on EKS or managed Git service) | Phase 1 |
| Self-managed MySQL data loss (2 services) | High | High | 🔴 Critical | Migrate to Aurora MySQL (preferred) with automated backups and PITR | Phase 1 |
| Circular dependency (aws-microservices ↔ books-api) | Medium | Medium | 🟡 Medium | Break sync dependency via EventBridge event subscription | Phase 0 |
| No audit logging (4 services) | High | Medium | 🟠 High | Deploy centralized CloudTrail with immutable storage | Phase 0 |
| No API authentication (2 services completely open) | High | High | 🔴 Critical | Implement Cognito-based API Gateway authorization | Phase 0-1 |
| Hardcoded credentials (MonoToMicroLegacy) | High | High | 🔴 Critical | Migrate to AWS Secrets Manager immediately | Phase 1 |
| EOL Lambda runtime Node.js 14 (aws-microservices) | Medium | Medium | 🟡 Medium | Upgrade to NODEJS_20_X or NODEJS_22_X | Phase 2 |
| No observability (4 services) | Medium | High | 🟠 High | Deploy ADOT + X-Ray portfolio-wide | Phase 0 |
| DynamoDB PITR not enabled + DESTROY policy (aws-microservices) | Medium | High | 🟠 High | Enable PITR, change to RETAIN removal policy | Phase 2 |
| No automated tests (3 services) | Medium | Medium | 🟡 Medium | Add test frameworks before modernization | Phase 1 |

### High-Risk Dependencies

- **eks-saas-gitops** (Score: 2.66, Fan-In: 2, Blast Radius: 80%): While relatively healthy, this is the shared infrastructure foundation. The Gitea single-EC2-instance SPOF could take down the entire GitOps pipeline for all services.
- **local-monolith** (Score: 1.29, Fan-In: 1): Very low score with aws-microservices depending on it synchronously for legacy product data. A failure cascades to the microservices layer.

### Single Points of Failure

- **eks-saas-gitops — Gitea EC2 instance**: Single EC2 instance in one public subnet running the Git server. If it fails, all GitOps-based deployments stop. Blast radius: 80% of portfolio (all services deployed via GitOps). **No HA, no redundancy.**
- **local-monolith — Self-managed MySQL**: Docker volume with no backups, no PITR, no failover. Data loss is irrecoverable. Contains inventory, order, and payment data.
- **MonoToMicroLegacy — Self-managed MySQL on EC2**: Similar to local-monolith. Single-instance database with no backup strategy.

### Circular Dependency Risks

- **aws-microservices ↔ books-api**: Bidirectional dependency creates deployment coupling. Cannot independently deploy or scale either service without considering the other. Must be resolved in Phase 0 before either service is modernized.

### Data Availability Risks

- **local-monolith** (Self-managed MySQL, Docker volume): Data loss risk is critical. No automated backups, no PITR, no failover. A Docker volume failure destroys all e-commerce data.
- **MonoToMicroLegacy** (Self-managed MySQL, EC2): Similar risk. Unknown MySQL server version. No managed backup strategy.
- **aws-microservices** (DynamoDB with DESTROY policy): Stack deletion destroys all product, basket, and order data. PITR not enabled.

### Observability Blind Spots

- **aws-microservices** (Fan-Out: 2, OPS-Q1: 1): Calls both books-api (async) and local-monolith (sync) with no tracing. Cannot debug cross-service failures in the checkout flow (basket → EventBridge → SQS → ordering).
- **local-monolith** (Fan-Out: 1, OPS-Q1: 1): Called synchronously by aws-microservices for legacy product data. No tracing means latency issues in this dependency are invisible.

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized Platform Team + Service Teams

> With 20 Foundational Blockers (≥ 5 threshold), a centralized platform team is recommended to drive cross-cutting improvements while service teams focus on domain-specific modernization.

**Platform Team**:
- Responsibilities: Shared infrastructure (EKS cluster, Cognito, CloudTrail, ADOT, EventBridge), Terraform module library, CI/CD pipeline templates, security scanning integration, observability platform, tagging enforcement
- Skills Required: Terraform, EKS, AWS networking (VPC/ALB), observability (X-Ray/ADOT/CloudWatch), security (Cognito/KMS/Secrets Manager)
- Recommended Size: 2–3 engineers

**Service Teams**:
- Responsibilities: Service-specific modernization, domain-specific testing, API versioning, database migration execution, application code changes
- Skills Required: Per-service language expertise (PHP, Java, TypeScript), DMS migration, containerization, API design
- Recommended Size: 1–2 engineers per service (shared across monoliths)

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| Terraform | IaC for all services (preferred) | Partial (eks-saas-gitops only) | High |
| EKS / Kubernetes | Container orchestration for monoliths | Partial (eks-saas-gitops only) | High |
| AWS X-Ray / ADOT | Distributed tracing portfolio-wide | Partial (books-api X-Ray only) | High |
| Aurora MySQL / DMS | Database migration for 2 services | No | High |
| Amazon Cognito | Centralized identity for all services | Partial (books-api only) | High |
| Amazon Bedrock | AI agent integration | No | Medium |
| Flux CD / GitOps | Deployment automation (preferred) | Partial (eks-saas-gitops only) | Medium |
| Containerization (Docker) | Monolith containerization | Partial (local-monolith has Dockerfile) | Medium |
| EventBridge | Event-driven architecture | Partial (aws-microservices only) | Medium |
| Security scanning (Semgrep/Trivy) | CI/CD security gates | No | Medium |

### Training Recommendations

**Phase 0 (Immediate — Required for foundation work):**
- Terraform Fundamentals — required for 4 of 5 service teams
- EKS Workshop — required for monolith containerization teams
- AWS Observability — required for platform team (X-Ray, ADOT, CloudWatch)
- Move to Modern DevOps learning plan — required for all 3 DevOps pathway services

**Phase 1 (Weeks 1–4 — Required for monolith modernization):**
- Move to Managed Databases learning plan — required for MySQL → Aurora migration
- Move to Containers learning plan — required for MonoToMicroLegacy containerization
- AWS DMS Getting Started — required for database migration team

**Phase 2–3 (Months 2–6 — Required for advanced capabilities):**
- Move to AI learning plan — required for agent integration
- Amazon Bedrock Getting Started — required for AI agent development
- Move to Cloud Native learning plan — required for monolith decomposition

### External Support

**Recommended AWS Professional Services or Partner engagement for:**
- **Database Migration (High Risk)**: Engage AWS Professional Services for Aurora MySQL migration of the 2 self-managed databases. Production data migration with minimal downtime requires expertise in DMS configuration and cutover planning.
- **EKS Cluster Hardening**: Engage an AWS Partner for eks-saas-gitops security hardening (Argo Workflows authentication, network segmentation, multi-NAT gateway configuration).
- **AI Agent Design**: Engage AWS Professional Services for Bedrock agent architecture design — specifically for the inventory restocking agent and customer support agent use cases.
- **Monolith Decomposition Planning**: Engage AWS Professional Services for Strangler Fig decomposition strategy for both monoliths. Domain boundary identification and data separation planning require architectural expertise.

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | 3 of 5 services have overall score < 2.5 | local-monolith (1.29), MonoToMicroLegacy (1.43), aws-microservices (2.24) all below 2.5 threshold | Request MAP engagement via AWS Solutions Architect |
| Experience-Based Acceleration | EBA | 3 services have triggered pathways AND score < 3.0 | local-monolith (4 pathways, 1.29), MonoToMicroLegacy (5 pathways, 1.43), aws-microservices (2 pathways, 2.24) | Request EBA engagement focused on Move to Modern DevOps pathway |

### Program Details

**Migration Acceleration Program (MAP)**

This program is recommended because 3 of 5 services (60%) have overall modernization readiness scores below 2.5, indicating significant modernization work is needed. The two monoliths (local-monolith at 1.29 and MonoToMicroLegacy at 1.43) are particularly low-scoring, requiring infrastructure modernization (IaC, CI/CD, managed compute, managed databases) before any advanced modernization can proceed. MAP provides migration funding credits, partner ecosystem access, and methodology support to accelerate the modernization journey. **Suggested timing**: Initiate MAP engagement during Phase 0 to support Phase 1 infrastructure modernization activities.

**Experience-Based Acceleration (EBA)**

This program is recommended because 3 services have at least one triggered modernization pathway AND an overall score below 3.0. The most prevalent pathway is **Move to Modern DevOps** (triggered for 3 services), making it the recommended EBA focus area. EBA provides AWS-led sprints where AWS architects work alongside the customer team to execute specific modernization activities. **Suggested timing**: Align the first EBA sprint with Phase 1 (Mo 1–2) to establish Terraform, CI/CD, and GitOps patterns that all services can adopt.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

## Recommended Self-Paced Learning Materials

> Included modules are relevant to the portfolio's triggered pathways and skill gaps.

### Module 2: Move to Cloud Native (Containers and Serverless)

- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
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
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

### Module 6: Move to Modern DevOps

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
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
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2

## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| local-monolith | application | P0 | 1.29 | 1.00 | 1.17 | 2.00 | 1.29 | 1.00 | 4 of 7 | 1 |
| MonoToMicroLegacy | application | P0 | 1.43 | 1.00 | 1.67 | 2.50 | 1.00 | 1.00 | 5 of 7 | 1 |
| aws-microservices | application | P0 | 2.24 | 2.64 | 3.00 | 3.00 | 1.57 | 1.00 | 2 of 7 | 2 |
| books-api | application | P1 | 2.64 | 3.00 | 2.50 | 2.75 | 2.86 | 2.11 | 1 of 7 | 3 |
| eks-saas-gitops | infrastructure-only | P1 | 2.66 | 3.18 | N/A | 4.00 | 2.14 | 1.33 | 0 of 7 | 1 |

### Individual Service Details

#### local-monolith

- **Overall Score**: 1.29 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.00
  - Application Architecture: 1.17
  - Data Platform: 2.00
  - Security Baseline: 1.29
  - Operations & Observability: 1.00
- **Top Gaps**:
  - INF-Q10: score 1 — Zero IaC, all infrastructure manually defined in docker-compose.yml
  - INF-Q11: score 1 — No CI/CD pipeline, only manual deploy.sh script
  - APP-Q2: score 1 — Entire application in single index.php (~2000+ lines)
- **Triggered Pathways**: Move to Cloud Native, Move to Managed Databases, Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Containerize and deploy to EKS (preferred) using existing Dockerfile
  - Migrate self-managed MySQL to Aurora MySQL (preferred) via DMS
  - Adopt Terraform (preferred) for all infrastructure
- **Depends On**: eks-saas-gitops (shared_infra — EKS cluster)
- **Depended On By**: aws-microservices (sync — legacy product data)
- **Blast Radius**: 20%
- **Roadmap Phase**: Phase 1 — Quick Wins

#### MonoToMicroLegacy (unishop-monolith)

- **Overall Score**: 1.43 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**:
  - Infrastructure & DevOps: 1.00
  - Application Architecture: 1.67
  - Data Platform: 2.50
  - Security Baseline: 1.00
  - Operations & Observability: 1.00
- **Top Gaps**:
  - INF-Q10: score 1 — Zero IaC, 100% ClickOps
  - INF-Q11: score 1 — No CI/CD pipeline, local Gradle build only
  - SEC-Q5: score 1 — Database credentials hardcoded in plaintext in application.properties
- **Triggered Pathways**: Move to Cloud Native, Move to Containers, Move to Managed Databases, Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Create Dockerfile (missing) and containerize on EKS (preferred)
  - Migrate self-managed MySQL to Aurora MySQL (preferred) via DMS
  - Immediately remediate hardcoded credentials — migrate to Secrets Manager
- **Depends On**: eks-saas-gitops (shared_infra — EKS cluster)
- **Depended On By**: None (leaf service)
- **Blast Radius**: 0%
- **Roadmap Phase**: Phase 1 — Quick Wins

#### aws-microservices

- **Overall Score**: 2.24 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**:
  - Infrastructure & DevOps: 2.64
  - Application Architecture: 3.00
  - Data Platform: 3.00
  - Security Baseline: 1.57
  - Operations & Observability: 1.00
- **Top Gaps**:
  - INF-Q11: score 1 — No CI/CD pipeline, all deployments are manual cdk deploy
  - SEC-Q3: score 1 — All 3 API Gateway endpoints completely open with no authentication
  - INF-Q8: score 1 — DynamoDB PITR not enabled; removalPolicy: DESTROY on all tables
- **Triggered Pathways**: Move to Modern DevOps, Move to AI
- **Key Recommendations**:
  - Implement CI/CD pipeline immediately (avoid manual deployments per preferences)
  - Add API Gateway authentication (Cognito authorizer) before agent integration
  - Enable DynamoDB PITR and change removal policy to RETAIN
- **Depends On**: local-monolith (sync — legacy product data), books-api (async — EventBridge events, circular dependency)
- **Depended On By**: books-api (sync — catalog data REST query, circular dependency)
- **Blast Radius**: 40%
- **Roadmap Phase**: Phase 2 — Foundation

#### books-api

- **Overall Score**: 2.64 / 4.0
- **Repository Type**: application
- **Priority**: P1
- **Assessment Date**: 2026-04-15
- **Category Scores**:
  - Infrastructure & DevOps: 3.00
  - Application Architecture: 2.50
  - Data Platform: 2.75
  - Security Baseline: 2.86
  - Operations & Observability: 2.11
- **Top Gaps**:
  - INF-Q3: score 1 — No workflow orchestration service
  - INF-Q4: score 1 — No messaging or streaming infrastructure
  - APP-Q5: score 1 — No API versioning strategy
- **Triggered Pathways**: Move to AI
- **Key Recommendations**:
  - Add API versioning (/v1/books) for stable agent tool interfaces
  - Add EventBridge (preferred) integration for BookCreated events
  - Add security scanning to CI/CD pipeline
- **Depends On**: aws-microservices (sync — catalog data REST query, circular dependency)
- **Depended On By**: aws-microservices (async — EventBridge events, circular dependency)
- **Blast Radius**: 40%
- **Roadmap Phase**: Phase 3 — Advanced

#### eks-saas-gitops

- **Overall Score**: 2.66 / 4.0
- **Repository Type**: infrastructure-only
- **Priority**: P1
- **Assessment Date**: 2025-07-17
- **Category Scores**:
  - Infrastructure & DevOps: 3.18
  - Application Architecture: N/A
  - Data Platform: 4.00
  - Security Baseline: 2.14
  - Operations & Observability: 1.33
- **Top Gaps**:
  - SEC-Q1: score 1 — No CloudTrail or audit logging defined in IaC
  - OPS-Q1: score 1 — No distributed tracing instrumentation
  - OPS-Q2: score 1 — No SLO definitions or error budget tracking
- **Triggered Pathways**: None (0 of 7)
- **Key Recommendations**:
  - Enable EKS control plane audit logging and deploy CloudTrail
  - Deploy ADOT DaemonSet for distributed tracing
  - Harden Argo Workflows authentication (replace --auth-mode=server)
- **Depends On**: None (foundation service)
- **Depended On By**: local-monolith (shared_infra), unishop-monolith (shared_infra)
- **Blast Radius**: 80%
- **Roadmap Phase**: Phase 1 — Quick Wins (Foundation Service)

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | local-monolith | monolith/monolith-mod-report.md | 2026-04-15 | application | 1.29 |
| 2 | MonoToMicroLegacy | services/unishop-monolith-to-microservices/MonoToMicroLegacy/MonoToMicroLegacy-mod-report.md | 2026-04-15 | application | 1.43 |
| 3 | aws-microservices | services/aws-microservices/aws-microservices-mod-report.md | 2026-04-15 | application | 2.24 |
| 4 | books-api | services/books-api/books-api-mod-report.md | 2026-04-15 | application | 2.64 |
| 5 | eks-saas-gitops | services/eks-saas-gitops/eks-saas-gitops-mod-report.md | 2025-07-17 | infrastructure-only | 2.66 |

---

*Portfolio Modernization Readiness Assessment Report generated on 2026-04-15. Assessment covers 5 services in the ecommerce-platform-v2 portfolio.*
