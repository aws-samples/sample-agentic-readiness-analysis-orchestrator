# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | ToolJet/ToolJet |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, low-code, frontend |
| **Context** | Open-source low-code internal-tool builder. |
| **Overall Score** | 2.35 / 4.0 |

**Archetype Justification**: The server component owns persistent state via PostgreSQL (TypeORM with `pg` driver) and Redis (ioredis for BullMQ). It exposes CRUD operations on business entities (apps, organizations, users, data-sources, data-queries) and manages entity lifecycle with user-specific data (user sessions, organization membership). Classified as `stateful-crud`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.18 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.78 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.35 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q7: Auto-Scaling | 1 | No auto-scaling configured on any resource — ECS, RDS, or Helm HPA are all statically provisioned. | Cannot respond to traffic spikes; over-provisioning wastes cost, under-provisioning degrades user experience. Blocks elastic scaling modernization. |
| 2 | SEC-Q2: Encryption at Rest | 1 | No KMS keys or encryption-at-rest configuration found on RDS, S3, or any data store. | Sensitive customer data (app definitions, credentials, user data) stored unencrypted — critical compliance and security gap. |
| 3 | OPS-Q2: SLO Definitions | 1 | No formal SLO definitions, error budgets, or SLO monitoring found. | No measurable service-level targets — impossible to track whether system meets user expectations or to prioritize improvements. |
| 4 | OPS-Q4: Anomaly Detection | 1 | No CloudWatch alarms, anomaly detection, or alerting rules defined in IaC. Sentry captures errors but no proactive alerting. | Gradual degradation and novel failures go undetected until users report them. No early warning system. |
| 5 | OPS-Q7: Incident Response | 1 | No runbooks, no Systems Manager Automation, no self-healing patterns. | Incident response is entirely ad hoc — slow MTTR, inconsistent remediation, knowledge loss when team members change. |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 ≥ 2 (score: 2) — NestJS API versioning infrastructure exists with URI-based versioning. NestJS returns structured JSON responses by default.
- **What it enables:** An agent that discovers and invokes existing ToolJet API endpoints as tools, enabling automated app management, data source configuration, and user administration via natural language.
- **Additional steps:** Generate a comprehensive OpenAPI specification from NestJS decorators (e.g., using `@nestjs/swagger`) for full tool discovery. Currently, no OpenAPI spec file exists in the repository.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** DATA-Q2 ≥ 2 (score: 3) — TypeORM provides a centralized data access layer with well-defined entities for apps, organizations, users, data sources, and data queries.
- **What it enables:** A natural-language-to-SQL agent that queries the ToolJet database for analytics — e.g., "How many apps were created in the last 30 days?" or "Which data sources have the most queries?"
- **Additional steps:** Create read-only database views or a dedicated analytics schema to isolate agent queries from production write paths. Ensure the agent only has SELECT permissions.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 ≥ 2 (score: 3) — GitHub Actions CI/CD pipeline exists with build, test, lint, and Docker image release workflows.
- **What it enables:** An agent that triggers CI builds, checks pipeline status, manages Docker image releases, and reports vulnerability scan results via natural language.
- **Additional steps:** Configure GitHub API access tokens for the agent. Consider adding workflow_dispatch triggers to additional workflows for agent-initiated actions.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — README.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, and a full `docs/` directory with Docusaurus documentation site.
- **What it enables:** A knowledge agent that indexes ToolJet documentation and answers developer questions about setup, configuration, plugin development, and deployment using retrieval-augmented generation.
- **Additional steps:** Index the `docs/docs/` directory content. Consider using Amazon Bedrock with knowledge bases for managed RAG infrastructure.
- **Effort:** Low

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 ≥ 2 (score: 3) — Temporal SDK (`@temporalio/activity`, `@temporalio/client`, `@temporalio/worker`, `@temporalio/workflow`) is in use for workflow orchestration. BullMQ provides additional job queue infrastructure.
- **What it enables:** An agent that monitors Temporal workflow execution status, retries failed workflows, and manages BullMQ job queues — reducing manual operational overhead.
- **Additional steps:** Expose Temporal and BullMQ monitoring APIs. The Bull Board UI (`@bull-board/express`) is already integrated — agent can leverage the same data endpoints.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 ≥ 2 (score: 3) — Comprehensive OpenTelemetry instrumentation with W3C Trace Context propagation, OTLP exporters for traces and metrics, structured logging via Pino.
- **What it enables:** An agent that queries OTLP traces and logs to correlate incidents, identify slow API endpoints, and suggest root causes based on trace data patterns.
- **Additional steps:** Ensure OTLP collector is configured and accessible. Set up a query API (e.g., via Grafana Tempo or AWS X-Ray) for the agent to query trace data programmatically.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 2 (primary trigger met), but no supporting triggers met: INF-Q1 = 3, APP-Q3 = 3, APP-Q4 = 3. Trigger logic requires APP-Q2 < 3 AND at least one supporting condition < 3. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 (not < 3). Compute already on ECS Fargate. Dockerfiles, docker-compose, K8s manifests, and Helm charts all present. Already containerized. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (not < 3). No commercial database engines detected — PostgreSQL is open-source. No stored procedures or proprietary SQL. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 (< 3): Redis runs as self-managed container sidecar in ECS task definition. MemoryDB cluster code is commented out. DATA-Q3 = 3 (supporting). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 2 (< 3), but contextual guard prevents trigger: no streaming, ETL, data pipeline, or analytics artifacts found. BullMQ is for background job processing, not data analytics. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 2 (< 3, primary trigger met): IaC covers compute and networking but missing operational resources (alarms, backup plans, monitoring). OPS-Q5 = 2 (< 3, supporting): rolling deployments only, no canary/blue-green. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "Open-source low-code internal-tool builder." does not contain any of the 17 AI-related signal terms. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
- **PostgreSQL:** Managed via AWS RDS (`aws_db_instance` in `terraform/ECS/main.tf`) — engine `postgres`, version `16`, instance class `db.t3.micro`. This is already a managed database service. However, it is deployed **single-AZ** (no `multi_az = true`), with `skip_final_snapshot = true` and default credentials (`postgres`/`postgres` in `variables.tf`).
- **Redis:** Runs as a **self-managed container sidecar** within the ECS Fargate task definition (`redis:6.2` image, 512 CPU, 1024 MB memory). This is the primary gap — Redis provides critical functionality (BullMQ job queues, caching, session state) but runs as an ephemeral container with no persistence, no failover, and no backup. A commented-out `aws_memorydb_cluster` resource in `terraform/ECS/redis.tf` indicates migration to MemoryDB was considered but not completed.
- **PostgreSQL (dev/compose):** `postgres:13` in `docker-compose.yaml` — older version used for local development.

**Engine Versions and EOL Status (from DATA-Q3):**
- RDS PostgreSQL 16: Current, not approaching EOL. Explicitly pinned in IaC.
- Redis 6.2 (container): Approaching community EOL. No version management or update strategy for the sidecar container.

**Data Access Patterns (from DATA-Q2):**
- TypeORM ORM with centralized `ormconfig.ts` — mostly centralized data access layer with some direct access in auxiliary paths.

**Recommended Migration Targets (respecting preferences: prefer `aurora`, `dynamodb`; avoid `oracle`):**
1. **Redis → Amazon MemoryDB for Redis** (preferred) or **Amazon ElastiCache for Redis**: Migrate the self-managed Redis sidecar to a fully managed Redis-compatible service. MemoryDB provides durability and Multi-AZ replication — critical for BullMQ job queues where job loss is unacceptable. The commented-out `aws_memorydb_cluster` in `redis.tf` provides a starting template.
2. **PostgreSQL RDS → Amazon Aurora PostgreSQL** (preferred): Migrate from standard RDS PostgreSQL to Aurora for improved performance, automatic storage scaling, and up to 15 read replicas. Aurora PostgreSQL is compatible with the existing `pg` driver and TypeORM configuration.

**Representative AWS Services:** Aurora PostgreSQL, MemoryDB for Redis, ElastiCache for Redis, RDS PostgreSQL (current), DMS (for migration)

**Migration Approach:**
1. **Redis migration (Phase 1 — 2-4 weeks):** Uncomment and configure the `aws_memorydb_cluster` resource in `redis.tf`. Update the ECS task definition to remove the Redis sidecar container and point `REDIS_HOST` to the MemoryDB endpoint. Update security groups to allow ECS tasks to reach MemoryDB. Test BullMQ job processing with the new endpoint.
2. **Aurora migration (Phase 2 — 4-8 weeks, optional):** Use AWS DMS for zero-downtime migration from RDS PostgreSQL to Aurora PostgreSQL. Update connection strings. Enable Multi-AZ for automatic failover. Configure auto-scaling read replicas for read-heavy workloads.

**Links:** [AWS Database Migration Guide](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-databases/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (from INF-Q10, score: 2):**
- Terraform covers: ECS cluster, task definitions, service, RDS instance, VPC, subnets, security groups, ALB, IAM roles, CloudWatch log groups.
- Helm chart covers: Kubernetes deployment, service, HPA, secrets, PostgreSQL subchart.
- **Missing from IaC:** CloudWatch alarms, backup plans (AWS Backup), monitoring dashboards, Route 53 health checks, SNS topics for alerting, WAF rules, CloudTrail configuration, KMS keys. Operational and DR resources are entirely absent from IaC — approximately 40% of production infrastructure would need manual creation.

**Current CI/CD State (from INF-Q11, score: 3):**
- **Build & Test:** Automated via `ci.yml` — build, lint (frontend, server, plugins), unit tests (with PostgreSQL service container), e2e tests. Triggered on push to develop/main and labeled PRs.
- **Docker Image Release:** Automated via `docker-release.yml` — builds CE, EE, Cloud, and Try-ToolJet images on GitHub release events. Pushes to Docker Hub.
- **Stage Deployment:** Semi-automated via `deploy-to-stage.yml` — manual `workflow_dispatch` trigger. Builds Docker image, deploys to AKS, deploys frontend to Cloudflare Pages. Includes health check verification.
- **Production Deployment:** Not defined in repository IaC/CI — likely manual or via external tooling.
- **Automated Rollback:** Not configured. No canary analysis or automatic rollback on failure.

**Deployment Strategy Gaps (from OPS-Q5, score: 2):**
- ECS uses rolling deployment (`deployment_maximum_percent=200`, `deployment_minimum_healthy_percent=100`).
- Kubernetes uses `RollingUpdate` (`maxUnavailable: 1`, `maxSurge: 1`).
- No blue/green or canary deployment strategy. No traffic shifting. No deployment gates beyond basic health checks.

**Testing Gaps (from OPS-Q6, score: 3):**
- Unit and e2e tests run in CI. Cypress tests exist for app builder, marketplace, and platform.
- Minor gap: Cypress workflows are separate and may not run on every PR. Contract testing is absent.

**Recommended DevOps Toolchain (respecting preferences: prefer `eks`, `api-gateway`, `eventbridge`):**
1. **Expand IaC Coverage:** Add Terraform modules for CloudWatch alarms (API latency, error rates, ECS CPU/memory), AWS Backup plans for RDS, KMS keys for encryption, CloudTrail for audit logging, and resource tagging via `default_tags` in the AWS provider. Target: 90%+ IaC coverage.
2. **Adopt Canary Deployments:** For EKS deployments (preferred), adopt Argo Rollouts with canary analysis. For ECS, use AWS CodeDeploy with blue/green deployment configuration and automatic rollback on CloudWatch alarm triggers.
3. **Add Production Deployment Pipeline:** Define a GitHub Actions workflow for production deployment with approval gates, canary analysis, and automated rollback.
4. **Implement Deployment Gates:** Add integration test execution as a deployment gate. Require Cypress e2e test pass before production promotion.

**Representative AWS Services:** CDK or Terraform (current), CodeBuild, CodePipeline, CodeDeploy (for ECS blue/green), EKS with Argo Rollouts (preferred), CloudWatch, X-Ray, CloudFormation

**Links:** [AWS DevOps Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/devops/welcome.html)

## Decomposition Strategy

APP-Q2 scored 2 — ToolJet is a monolith with identifiable module boundaries (~60 NestJS modules under `server/src/modules/`) but a single shared PostgreSQL database accessed via a shared TypeORM configuration (`server/ormconfig.ts`). The frontend (React) and plugins (Lerna monorepo) are separate build units but the server is a single deployable.

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping it running. New features built as services; existing features migrated over time. | ToolJet has ~60 identifiable NestJS modules (auth, apps, data-sources, data-queries, workflows, AI, marketplace) with recognizable boundaries. Team can extract high-value modules one at a time. | **Medium to High** — 6-12 months. Each extraction is bounded. | ✅ **Recommended.** Lowest risk, incremental value delivery. Start with `workflows` and `AI` modules which already have Temporal orchestration and could benefit from independent scaling. |
| **Conditional / Adaptive** | Containerize as-is (already done), then selectively extract only high-value modules based on business priority. Some modules remain in monolith permanently. | ToolJet is already containerized (Dockerfiles, ECS Fargate, K8s manifests). Selective extraction can target modules needing independent scaling without full decomposition. | **Low to Medium** — selective extraction over 3-9 months. | ✅ **Recommended when capacity is constrained.** Extract `workflows`, `AI`, and `marketplace` as independent services on EKS (preferred). Leave core CRUD modules in the monolith. |
| **Big-Bang Rewrite** | Rewrite entire application as microservices from scratch. | Almost never applicable for ToolJet — the monolith is functional, well-structured with clear module boundaries, and actively developed. | **Very High** — 12-24+ months. | ⚠️ **Recommended against.** ToolJet's monolith has clear module structure and is actively maintained. Strangler Fig or Conditional approaches are significantly safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's data model. Prevent the monolith's design from leaking into new services. | Every extraction — place ACL between new service and monolith to translate between their models. Critical when extracting `workflows` or `AI` modules. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions across services that were single-database transactions. | When extracting modules participating in multi-step operations (e.g., app creation → data source setup → query configuration). Use Amazon EventBridge (preferred) for saga coordination. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture state changes as events for audit, temporal queries, and inter-service integration. | The existing `audit-logs` module and `@nestjs/event-emitter` provide a foundation. Evolve toward EventBridge for cross-service events. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear boundaries between business logic, external interfaces, and infrastructure adapters. | Every new extracted service. Ensures testability and portability. NestJS module structure already approximates this pattern. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation

| Factor | Signal | Evidence | Impact |
|--------|--------|----------|--------|
| Module boundaries | ✅ Low effort | ~60 NestJS modules with dedicated service layers under `server/src/modules/` | Clear extraction targets |
| Data coupling | ⚠️ High effort | Single shared `ormconfig.ts`, all modules access same PostgreSQL instance. No per-module schema separation. | Database decomposition required per extracted service |
| Stored procedures | ✅ Low effort | No stored procedures found (DATA-Q4 = 4). All business logic in application layer. | No database-coupled logic to extract |
| Communication patterns | 🟡 Medium effort | BullMQ and Temporal provide async patterns. `@nestjs/event-emitter` for in-process events. | Async foundation exists but needs migration to managed messaging (EventBridge preferred) |
| CI/CD maturity | ✅ Low effort | GitHub Actions CI pipeline with build, test, Docker release. | Pipeline can be extended for multi-service deployment |
| Test coverage | ✅ Low effort | Unit tests, e2e tests, and Cypress tests exist for critical workflows. | Regression safety during extraction |

**Calibrated Estimate:** Medium effort with **Strangler Fig approach over 6-12 months**. The primary cost driver is database decomposition — each extracted service needs its own data store. Recommend starting with the `workflows` module (already uses Temporal) and the `AI` module (already has dedicated service/repository layers) as they have the clearest service boundaries and most to gain from independent scaling. Deploy extracted services on EKS (preferred) with Aurora PostgreSQL (preferred) per-service databases.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary workload runs on **ECS Fargate** (`requires_compatibilities = ["FARGATE"]` in `terraform/ECS/main.tf`). The ECS task definition includes the ToolJet application container (2048 CPU, 4096 MB), a Redis sidecar (512 CPU, 1024 MB), and a PostgREST sidecar (512 CPU, 1024 MB). An alternative **EC2 deployment** exists in `terraform/EC2/ec2.tf` using an `aws_instance` with a user-data install script. Kubernetes and Helm deployment manifests in `deploy/` provide additional managed orchestration options. |
| **Gap** | EC2 remains an active deployment option alongside managed compute. Mixed compute model with the primary path on Fargate but EC2 not deprecated. |
| **Recommendation** | Deprecate the EC2 deployment path and consolidate on ECS Fargate or migrate to EKS (preferred per preferences). Document that EC2 is for edge cases only. |
| **Evidence** | `terraform/ECS/main.tf` (ECS Fargate task), `terraform/EC2/ec2.tf` (EC2 instance), `deploy/helm/Chart.yaml`, `deploy/kubernetes/deployment.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | PostgreSQL is managed via **RDS** (`aws_db_instance` in `terraform/ECS/main.tf`, engine `postgres`, version `16`, `db.t3.micro`). Redis runs as a **self-managed container sidecar** (`redis:6.2` image) within the ECS Fargate task definition — not on ElastiCache or MemoryDB. A commented-out `aws_memorydb_cluster` in `terraform/ECS/redis.tf` shows migration was considered but not implemented. RDS is deployed single-AZ with no `multi_az = true`. |
| **Gap** | Redis is self-managed as an ephemeral container sidecar with no persistence, failover, or backup. This is critical because BullMQ job queues rely on Redis for job state. RDS is single-AZ. |
| **Recommendation** | Migrate Redis to **Amazon MemoryDB for Redis** (preferred — provides durability for BullMQ jobs) or ElastiCache. Enable Multi-AZ on RDS. Consider future migration to Aurora PostgreSQL (preferred). |
| **Evidence** | `terraform/ECS/main.tf` (RDS + Redis sidecar), `terraform/ECS/redis.tf` (commented MemoryDB), `docker-compose.yaml` (redis:6.2) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Temporal SDK** is integrated for workflow orchestration (`@temporalio/activity`, `@temporalio/client`, `@temporalio/worker`, `@temporalio/workflow` in `server/package.json`). **BullMQ** (`bullmq`, `@nestjs/bullmq`, `@nestjs/bull`) provides Redis-backed job queues with Bull Board UI for monitoring. The `workflows` module (`server/src/modules/workflows/`) uses Temporal for multi-step business operations. For the `stateful-crud` archetype, this represents partial adoption — dedicated orchestration (Temporal) for key workflows with BullMQ for job processing. |
| **Gap** | Some workflows may still be implemented as hardcoded application logic outside of Temporal. The Temporal server itself is not provisioned in the repository IaC — external dependency. |
| **Recommendation** | Expand Temporal adoption to cover all multi-step business operations. Define Temporal server infrastructure in IaC (consider AWS Step Functions as a managed alternative if Temporal operational overhead is a concern). |
| **Evidence** | `server/package.json` (Temporal + BullMQ deps), `server/src/modules/workflows/` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **BullMQ** (Redis-backed) provides async job processing for background tasks. **`@nestjs/event-emitter`** handles in-process event dispatching. **No managed AWS messaging** (SQS, SNS, EventBridge) is used. Redis itself is self-managed as a container sidecar. For the `stateful-crud` archetype, cross-service state changes should use managed messaging, but all messaging is self-managed Redis-backed. |
| **Gap** | All async messaging relies on self-managed Redis (BullMQ). No managed messaging service for cross-service or cross-module communication. If Redis sidecar fails, all job processing stops with no failover. EventBridge (preferred) would enable event-driven patterns with durability. |
| **Recommendation** | Migrate BullMQ backing store to managed Redis (MemoryDB/ElastiCache). Introduce **Amazon EventBridge** (preferred) for cross-module event-driven communication as modules are extracted. Replace `@nestjs/event-emitter` in-process events with EventBridge for cross-service events during decomposition. |
| **Evidence** | `server/package.json` (bullmq, @nestjs/event-emitter, ioredis), `terraform/ECS/main.tf` (Redis sidecar) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Custom VPC with 2 subnets across 2 AZs in ECS setup (`terraform/ECS/main.tf`). Security groups restrict ECS task ports to ALB (`aws_security_group.task_sg`). RDS security group limits PostgreSQL access to task security group. **However:** Both subnets are **public** (`map_public_ip_on_launch = true`), ECS tasks have `assign_public_ip = true`. EC2 setup (`terraform/EC2/sg.tf`) has **0.0.0.0/0 ingress on ports 22, 80, 443, 3000** — fully open to internet. ECS task_sg has 443 ingress from 0.0.0.0/0. No private subnets, no NAT gateway, no VPC endpoints. |
| **Gap** | All resources deployed in public subnets with public IPs. EC2 security group is wide open. No network segmentation between application and data tiers. No VPC endpoints or PrivateLink. |
| **Recommendation** | Move ECS tasks and RDS to **private subnets** behind a NAT gateway. Remove `map_public_ip_on_launch = true` and `assign_public_ip = true`. Restrict EC2 security groups. Add VPC endpoints for AWS services (ECR, CloudWatch, S3). Consider AWS VPC Lattice for service-to-service networking. |
| **Evidence** | `terraform/ECS/main.tf` (public subnets, task_sg), `terraform/EC2/sg.tf` (0.0.0.0/0 on 4 ports) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Application Load Balancer** (`aws_lb.tooljet_lb`) configured as internet-facing with target group routing to ECS port 3000. Health check on `/api/health`. HTTP listener on port 80 (HTTPS listener commented out). Kubernetes service uses `type: LoadBalancer` with AWS NLB SSL termination annotation. No **API Gateway** (preferred), no throttling configuration on ALB, no request validation, no WAF. |
| **Gap** | ALB provides basic routing and health checks but no throttling, authentication, request validation, or WAF protection. HTTPS is not configured (listener commented out). No API Gateway for advanced API management. |
| **Recommendation** | Add **Amazon API Gateway** (preferred) in front of the ALB for throttling, request validation, and centralized auth. At minimum, enable HTTPS listener with ACM certificate and attach AWS WAF to the ALB. Configure rate limiting. |
| **Evidence** | `terraform/ECS/main.tf` (aws_lb, listener_80, commented listener_443), `deploy/kubernetes/service.yaml` (LoadBalancer with SSL annotation) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | ECS service has `desired_count = 2` with **no auto-scaling policy** defined — no `aws_appautoscaling_target` or `aws_appautoscaling_policy` resources. Helm chart defines HPA with `min: 1, max: 1` — effectively disabled. RDS has no auto-scaling. Redis sidecar has no scaling capability. No Lambda concurrency limits (no Lambda used). |
| **Gap** | All capacity is statically provisioned. No auto-scaling on any resource type — compute, database, or cache. Cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | Add ECS Application Auto Scaling with target tracking on CPU and memory utilization. Configure RDS storage auto-scaling. Update Helm HPA to meaningful min/max values (e.g., min: 2, max: 10) with CPU/memory thresholds. When migrating Redis to MemoryDB, configure shard scaling. |
| **Evidence** | `terraform/ECS/main.tf` (desired_count=2, no scaling), `deploy/helm/values.yaml` (hpa min:1 max:1) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | RDS instance has `skip_final_snapshot = true` — no final snapshot on deletion. No explicit `backup_retention_period` parameter (AWS defaults to 7 days for RDS). No `aws_backup_plan` resource. No PITR configuration. No cross-region backup replication. Redis sidecar has no backup capability (ephemeral container). Helm PostgreSQL subchart has `persistence.enabled: true` with 8Gi storage but no backup configuration. |
| **Gap** | Only default AWS RDS backup retention applies. No explicit backup strategy, no PITR, no backup plans for Redis or other data stores, no restore testing documentation. `skip_final_snapshot = true` means database is lost on `terraform destroy`. |
| **Recommendation** | Explicitly set `backup_retention_period = 7` (minimum) on RDS. Enable PITR. Remove `skip_final_snapshot = true` for production. Add `aws_backup_plan` for RDS with defined retention. When Redis migrates to MemoryDB, configure snapshot retention. Document and test restore procedures. |
| **Evidence** | `terraform/ECS/main.tf` (skip_final_snapshot=true, no backup config), `deploy/helm/values.yaml` (persistence enabled, no backup) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECS service deploys across **2 subnets in different AZs** (us-east-1c, us-east-1d). ALB spans both subnets. RDS is **single-AZ** (no `multi_az = true`). Redis runs as a sidecar container — single instance within the task, no failover. Helm chart replication is `enabled: false` for PostgreSQL. |
| **Gap** | RDS is single-AZ — an AZ failure would cause database unavailability with no automatic failover. Redis sidecar is single-instance with no replication. While compute spans 2 AZs, the data layer is single-AZ. |
| **Recommendation** | Enable `multi_az = true` on RDS for automatic failover. Migrate Redis to MemoryDB (inherently Multi-AZ). Consider Aurora PostgreSQL (preferred) for automatic Multi-AZ with up to 15 replicas. |
| **Evidence** | `terraform/ECS/main.tf` (2 subnets, RDS no multi_az), `terraform/ECS/variables.tf` (AZ config), `deploy/helm/values.yaml` (replication: false) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Terraform covers: ECS cluster, task definition, service, RDS instance, VPC, subnets, security groups, ALB, IAM roles/policies, CloudWatch log groups. EC2 alternative deployment has separate Terraform. Helm chart covers K8s deployment, service, HPA, secrets, PostgreSQL subchart. Docker Compose for development. **Missing from IaC:** CloudWatch alarms, AWS Backup plans, CloudTrail, KMS keys, Route 53 health checks, SNS topics, WAF rules, monitoring dashboards, anomaly detection, auto-scaling policies. |
| **Gap** | Compute and networking are in IaC, but operational/DR resources (monitoring, alerting, backup, encryption, audit) are entirely absent. Estimated ~60% coverage — primary resources defined but significant manual infrastructure for operations. |
| **Recommendation** | Add IaC modules for: CloudWatch alarms (error rates, latency), AWS Backup plans, CloudTrail, KMS keys, resource tagging via `default_tags`, auto-scaling policies. Target 90%+ coverage including operational resources. |
| **Evidence** | `terraform/ECS/main.tf`, `terraform/EC2/ec2.tf`, `deploy/helm/Chart.yaml`, `deploy/helm/values.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **GitHub Actions** CI/CD pipeline: `ci.yml` (build, lint for frontend/server/plugins, unit tests with PostgreSQL, e2e tests — triggered on push/labeled PRs), `docker-release.yml` (automated Docker build/push for CE/EE/Cloud on GitHub release), `deploy-to-stage.yml` (manual workflow_dispatch to build, deploy to AKS, deploy frontend to Cloudflare Pages, health check verification), `vulnerability-ci.yml` (weekly npm audit for all packages with auto-fix PRs), `grype-slack-notify.yml` (weekly Docker image Grype scan), `license-compliance.yml` (license check on PRs). |
| **Gap** | No automated production deployment pipeline. Stage deployment requires manual trigger. No automated rollback on failure. No canary or blue/green deployment automation. |
| **Recommendation** | Add automated production deployment workflow with approval gates, canary analysis (via Argo Rollouts on EKS, preferred), and automated rollback on CloudWatch alarm triggers. Extend `deploy-to-stage.yml` to include automated promotion to production after health verification. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/docker-release.yml`, `.github/workflows/deploy-to-stage.yml`, `.github/workflows/vulnerability-ci.yml`, `.github/workflows/grype-slack-notify.yml`, `.github/workflows/license-compliance.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **TypeScript** (server — NestJS framework, Node.js 22.15.1) and **JavaScript/JSX** (frontend — React). Both languages have first-class AWS SDK coverage (`@aws-sdk/*`), broad cloud-native tooling, and mature framework ecosystems. TypeScript provides type safety and excellent IDE support. Node.js 22 is a current LTS release. |
| **Gap** | No gap — TypeScript and JavaScript are Tier 1 languages for AWS cloud-native development. |
| **Recommendation** | No change needed. Continue with TypeScript/JavaScript stack. Ensure consistent TypeScript adoption across all new modules (avoid new plain JavaScript). |
| **Evidence** | `server/package.json` (TypeScript, NestJS), `frontend/package.json` (React, JavaScript), `package.json` (Node.js 22.15.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable server unit serving both API and worker mode (`WORKER=true` flag in `server/scripts`). ~60 NestJS modules under `server/src/modules/` (auth, apps, data-sources, data-queries, workflows, AI, audit-logs, organizations, users, plugins, etc.). Frontend (React) is a separate build. PostgREST runs as a sidecar. All modules share a single PostgreSQL database via shared `ormconfig.ts`. Identifiable module boundaries exist (each module has its own controller, service, and entity files) but shared database schemas create tight coupling. |
| **Gap** | Monolith with identifiable modules but shared database. All modules access the same PostgreSQL instance through a single TypeORM configuration. No per-module schema separation. Cross-module data access likely exists (shared entities, foreign key relationships across modules). |
| **Recommendation** | Adopt Strangler Fig pattern to incrementally extract high-value modules (workflows, AI, marketplace) as independent services. See Decomposition Strategy section for detailed approach. Deploy on EKS (preferred). |
| **Evidence** | `server/src/modules/` (~60 modules), `server/src/main.ts` (single entry point), `docker-compose.yaml` (single server service), `server/package.json` (WORKER=true mode) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | For `stateful-crud` archetype: **BullMQ** handles async job processing (background tasks, scheduled jobs). **Temporal SDK** provides async workflow orchestration for multi-step operations. **`@nestjs/event-emitter`** dispatches in-process events. Primary API communication is synchronous HTTP (NestJS controllers return JSON responses). WebSocket support exists (`@nestjs/websockets`, `@nestjs/platform-ws`) for real-time collaboration (`y-websocket` for collaborative editing). Mix of async and sync with async for key workflows. |
| **Gap** | Async patterns (BullMQ, Temporal) exist for key workflows but primary inter-module communication within the monolith is synchronous function calls. No managed messaging for potential cross-service events during decomposition. |
| **Recommendation** | As modules are extracted, introduce **Amazon EventBridge** (preferred) for cross-service event-driven communication. Maintain synchronous HTTP for read-heavy API endpoints. Evolve `@nestjs/event-emitter` patterns to EventBridge during decomposition. |
| **Evidence** | `server/package.json` (bullmq, @temporalio/*, @nestjs/event-emitter, @nestjs/websockets), `server/src/main.ts` (WsAdapter) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | For `stateful-crud` archetype: **Temporal SDK** (`@temporalio/activity`, `@temporalio/client`, `@temporalio/worker`, `@temporalio/workflow`) handles workflow orchestration for long-running operations. **BullMQ** processes background jobs asynchronously via dedicated worker mode (`WORKER=true`). **Bull Board** (`@bull-board/express`, `@bull-board/nestjs`) provides job monitoring UI. `@nestjs/schedule` provides scheduled task support. Most long-running operations are delegated to worker processes. |
| **Gap** | Most long-running operations are async, but some blocking calls may remain in the API path (e.g., data source query execution). Worker mode separation (WORKER=true) is a process-level split, not a service-level split. |
| **Recommendation** | Audit API endpoints for blocking calls exceeding 30 seconds and migrate to BullMQ job + status polling pattern. Consider extracting the worker process as an independent service on EKS (preferred) for independent scaling. |
| **Evidence** | `server/package.json` (Temporal, BullMQ, @nestjs/schedule, Bull Board), `server/src/modules/workflows/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | NestJS API versioning is **enabled** in `server/src/main.ts` with `VersioningType.URI` and `defaultVersion: VERSION_NEUTRAL`. This means the versioning infrastructure exists but `VERSION_NEUTRAL` as default means most endpoints do not require an explicit version prefix — they respond without `/v1/` in the path. No OpenAPI specification file found in the repository. Some endpoints may use explicit version decorators on controllers, but the default behavior is unversioned. |
| **Gap** | Versioning infrastructure exists but is effectively unused due to `VERSION_NEUTRAL` default. No consistent `/v1/` prefix across endpoints. No OpenAPI spec for documentation. No backward compatibility guarantees documented. |
| **Recommendation** | Set `defaultVersion: '1'` to enforce `/v1/` prefix on all endpoints. Generate OpenAPI specification using `@nestjs/swagger`. Document versioning policy and backward compatibility guarantees. |
| **Evidence** | `server/src/main.ts` (enableVersioning with VERSION_NEUTRAL) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit — internal module communication is direct function calls (no service discovery needed within monolith). External service endpoints use **environment variables**: `PG_HOST`, `REDIS_HOST`, `PGRST_HOST`, `TOOLJET_DB_HOST` (from `.env.example`, `terraform/ECS/main.tf`, `deploy/kubernetes/deployment.yaml`). Kubernetes service (`deploy/kubernetes/service.yaml`) provides DNS-based discovery for K8s deployments. No dynamic service discovery (no AWS Cloud Map, no Consul, no Istio). |
| **Gap** | All service endpoints are environment-variable-based with no dynamic discovery. This works for the current monolith but will not scale as services are extracted. No service mesh or API catalog. |
| **Recommendation** | As services are extracted during decomposition, implement **AWS Cloud Map** for dynamic service discovery or use Kubernetes DNS with a service mesh (Istio on EKS, preferred). Register extracted services in an API catalog. |
| **Evidence** | `.env.example` (PG_HOST, REDIS_HOST, PGRST_HOST), `deploy/kubernetes/service.yaml`, `terraform/ECS/main.tf` (env vars in task def) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | A `files` module exists at `server/src/modules/files/`. No S3 bucket definitions found in Terraform IaC. No `aws_s3_bucket` resources. The `.env.example` does not contain S3-related environment variables (no `AWS_S3_BUCKET`, `S3_REGION`). File storage appears to be local filesystem or database-based. The Docker image includes Oracle InstantClient libraries, but these are for data source connectors (plugin system), not primary storage. |
| **Gap** | No evidence of S3 or managed object storage for unstructured data. Files likely stored on local filesystem or in the database, which limits scalability and accessibility for modern workloads. |
| **Recommendation** | Migrate file storage to **Amazon S3** with appropriate bucket policies. Add S3 configuration to IaC. Consider adding parsing capabilities (Amazon Textract) for document-heavy workflows. |
| **Evidence** | `server/src/modules/files/`, `terraform/ECS/main.tf` (no S3 resources), `.env.example` (no S3 vars) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **TypeORM** serves as the centralized ORM layer with a shared configuration. Entities are organized under `server/src/entities/`. Each NestJS module has dedicated repository/service layers (e.g., `server/src/modules/ai/repositories/`, `server/src/modules/apps/`). PostgREST provides direct REST-to-database access as a sidecar, bypassing the application layer. |
| **Gap** | Mostly centralized via TypeORM, but PostgREST provides a parallel data access path that bypasses application-layer business logic and validation. Some modules may have direct TypeORM queries outside the centralized repository pattern. |
| **Recommendation** | Audit PostgREST usage to ensure it's constrained to read-only ToolJet DB operations with proper row-level security. Ensure all write operations go through the application layer. Standardize repository pattern across all modules. |
| **Evidence** | `server/package.json` (typeorm), `server/src/modules/` (per-module repositories), `docker-compose.yaml` (PostgREST sidecar) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | RDS PostgreSQL **version 16** explicitly pinned in `terraform/ECS/main.tf` (`engine_version = "16"`). PostgreSQL 16 is current and not approaching EOL (supported through November 2028). `docker-compose.yaml` uses `postgres:13` for local development — PostgreSQL 13 is approaching EOL (November 2025). `render.yaml` specifies `postgresMajorVersion: 13`. Helm chart uses Bitnami PostgreSQL subchart version 11.1.3. Redis 6.2 in sidecar container is approaching community EOL. |
| **Gap** | Production engine version is current, but development/staging environments use PostgreSQL 13 (approaching EOL). Redis 6.2 has no version update strategy. No documented version-update procedure for production upgrades. |
| **Recommendation** | Update `docker-compose.yaml` and `render.yaml` to PostgreSQL 16 for consistency with production. Update Redis to 7.x when migrating to MemoryDB. Document a version-update procedure covering downtime windows, rollback, and risk acknowledgment. |
| **Evidence** | `terraform/ECS/main.tf` (engine_version=16), `docker-compose.yaml` (postgres:13), `render.yaml` (postgresMajorVersion: 13) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No `.sql` files found in the repository. All database migrations are TypeScript-based (`server/migrations/*.ts`) using TypeORM's migration framework. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements found. All business logic resides in the NestJS application layer (controllers, services, repositories). PostgREST provides direct SQL access but through standard PostgreSQL queries, not stored procedures. |
| **Gap** | No gap — all business logic is in the application layer with no stored procedure or proprietary SQL coupling. |
| **Recommendation** | Maintain this practice. Continue using TypeORM migrations for schema changes. Avoid introducing stored procedures or triggers that would couple business logic to the database engine. |
| **Evidence** | `server/migrations/` (TypeScript migrations only), `server/src/modules/` (business logic in app layer) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Application-level audit logging** exists via `server/src/modules/audit-logs/` module with dedicated OTEL audit metrics (`server/src/otel/audit-metrics.ts`). CloudWatch log groups defined for ECS containers (`/ecs/ToolJet`, `/ecs/postgrest`) with **30-day retention**. Container Insights enabled on ECS cluster (`containerInsights = "enabled"`). **No `aws_cloudtrail` resource** in any Terraform configuration. No S3 bucket for immutable log storage. |
| **Gap** | No CloudTrail for AWS API-level audit logging. Application audit logs exist but no infrastructure-level audit trail. No immutable log storage (S3 Object Lock). Partial coverage — application actions logged but AWS control plane actions are not. |
| **Recommendation** | Add `aws_cloudtrail` resource to Terraform with log file validation and immutable S3 storage (Object Lock). Integrate CloudTrail with CloudWatch for alerting on sensitive API calls. |
| **Evidence** | `terraform/ECS/main.tf` (CloudWatch log groups, Container Insights), `server/src/modules/audit-logs/`, `server/src/otel/audit-metrics.ts` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **No KMS keys** defined in any Terraform configuration. RDS `aws_db_instance` has **no `storage_encrypted` parameter** and no `kms_key_id`. No S3 buckets with encryption configuration (no S3 buckets defined at all). No EBS encryption defaults. No `aws_kms_key` resources found. The application stores sensitive data including data source credentials (encrypted with `LOCKBOX_MASTER_KEY` at application layer) but no infrastructure-level encryption at rest. |
| **Gap** | No encryption at rest configured at the infrastructure level. Customer data, app definitions, and credentials stored in RDS without storage encryption. This is a critical security gap for a platform that stores third-party data source credentials. |
| **Recommendation** | Add `storage_encrypted = true` and a customer-managed KMS key to the RDS instance. Add `aws_kms_key` resources for data stores. Enable default EBS encryption in the account. Define key rotation policy. |
| **Evidence** | `terraform/ECS/main.tf` (RDS with no encryption config), `terraform/ECS/variables.tf` (no KMS vars) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **JWT-based authentication** via `@nestjs/passport` and `passport-jwt`. **OIDC** support via `openid-client`. **SAML** support via `@node-saml/node-saml`. **Rate limiting** via `@nestjs/throttler`. Application-level auth validation (`GuardValidator` in `main.ts`). OIDC connection timeout configurable. **No API Gateway-level authentication** — ALB does not enforce auth. Health check endpoint (`/api/health`) excluded from auth. MFA support via `otpauth`. |
| **Gap** | Token-based auth on all application endpoints but no infrastructure-level auth enforcement (ALB/API Gateway). Internal endpoints rely on network isolation which is weak (public subnets). |
| **Recommendation** | Add **Amazon API Gateway** (preferred) with JWT authorizer for infrastructure-level auth enforcement. This provides a defense-in-depth layer independent of application code. Maintain existing Passport JWT for application-level validation. |
| **Evidence** | `server/package.json` (@nestjs/passport, passport-jwt, openid-client, @node-saml/node-saml, @nestjs/throttler, otpauth), `server/src/main.ts` (GuardValidator) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **OIDC** integration via `openid-client`. **SAML** via `@node-saml/node-saml`. **Google OAuth** via `google-auth-library`. **GitHub OAuth** via SSO configuration (`.env.example`: `SSO_GIT_OAUTH2_CLIENT_ID`). **SCIM** module (`server/src/modules/scim/`) for automated user provisioning with SCIM 2.0 protocol (`scimmy` library). **LDAP** support via `ldapts`. SSO domain restriction available (`SSO_ACCEPTED_DOMAINS`). |
| **Gap** | Application integrates with multiple centralized IdPs for most flows. Some legacy auth paths may remain (local password-based auth). No AWS Cognito integration — all IdP integration is application-managed. |
| **Recommendation** | Consider **Amazon Cognito** as a unified IdP layer to consolidate OIDC, SAML, and social login configurations. This would simplify IdP management and provide managed token handling. |
| **Evidence** | `server/package.json` (openid-client, @node-saml/node-saml, google-auth-library, scimmy, ldapts), `.env.example` (SSO vars), `server/src/modules/scim/` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **AWS Secrets Manager** IAM policy defined (`secrets_manager_policy` with `GetSecretValue` for `tooljet-secret`). Kubernetes deployment uses `secretKeyRef` for database credentials. **However:** ECS task definition passes database passwords directly as **environment variables** (`TOOLJET_DB_PASS`, `PG_PASS`, `LOCKBOX_MASTER_KEY`, `SECRET_KEY_BASE`). `terraform/ECS/variables.tf` has **default password values** (`PG_PASS = "postgres"`, `PG_USER = "postgres"`). `.env.example` shows all secrets as environment variables. Helm `values.yaml` contains default credentials (`pg_password: "postgresql"`, `lockbox_key: "0123456789ABCDEF"`). |
| **Gap** | Secrets Manager policy exists but production credentials are passed as plain environment variables in ECS task definitions. Default passwords hardcoded in Terraform variables and Helm values. No secret rotation configured. Mixed approach with significant gaps. |
| **Recommendation** | Migrate all secrets from environment variables to **AWS Secrets Manager** with ECS native secrets integration (`valueFrom` in container definitions). Remove all default passwords from `variables.tf` and `values.yaml`. Configure automatic rotation for database credentials. |
| **Evidence** | `terraform/ECS/main.tf` (env vars with passwords, secrets_manager_policy), `terraform/ECS/variables.tf` (default postgres/postgres), `deploy/helm/values.yaml` (default credentials), `deploy/kubernetes/deployment.yaml` (secretKeyRef) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Grype vulnerability scanning** on Docker images via `grype-slack-notify.yml` (weekly schedule, scans `tooljet/tooljet:ee-lts-latest`). **npm audit** runs weekly via `vulnerability-ci.yml` with automated PR creation for fixable vulnerabilities. Dockerfile uses **`debian:12`** base image (not hardened — not Alpine, Bottlerocket, or CIS-hardened). No SSM Patch Manager. No AWS Inspector. No hardened AMI for EC2 deployment. EC2 uses a custom AMI or default with user-data install script. |
| **Gap** | Vulnerability scanning exists (Grype for Docker images, npm audit for dependencies) but compute is not hardened. Debian base image is standard, not security-hardened. No OS-level patching strategy. No Inspector for continuous assessment. |
| **Recommendation** | Switch Docker base image to **Alpine** or **Distroless** for reduced attack surface. Enable **AWS Inspector** for continuous vulnerability assessment. For EC2 deployments, use hardened AMIs (CIS benchmarks or Bottlerocket). Add SSM Patch Manager for OS patching. |
| **Evidence** | `docker/ce-production.Dockerfile` (debian:12 base), `.github/workflows/grype-slack-notify.yml`, `.github/workflows/vulnerability-ci.yml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Dependabot** configured for daily dependency updates across server, frontend, plugins, and marketplace (`dependabot.yml`). **npm audit** runs weekly with automated fix PRs (`vulnerability-ci.yml`). **Grype** scans Docker images weekly (`grype-slack-notify.yml`). **License compliance** check on PRs (`license-compliance.yml` — only permits MIT and Apache-2.0). **No SAST tool** — no SonarQube, Semgrep, CodeGuru Reviewer, or equivalent in CI/CD. No container image scanning in CI (Grype runs weekly, not on every build). |
| **Gap** | Dependency scanning (Dependabot, npm audit) and Docker scanning (Grype) present. License compliance checking present. But no SAST tool for application code analysis. Docker scanning not integrated into build pipeline (weekly only). No security gates blocking deployment on critical findings. |
| **Recommendation** | Add **SAST tool** (Semgrep or Amazon CodeGuru Reviewer) to the CI pipeline. Move Grype scanning into the Docker build pipeline (`docker-release.yml`) with a security gate that blocks release on critical/high findings. Add `--audit-level=critical` flag to npm audit in the build pipeline. |
| **Evidence** | `dependabot.yml` (daily npm updates), `.github/workflows/vulnerability-ci.yml` (weekly npm audit), `.github/workflows/grype-slack-notify.yml` (weekly Docker scan), `.github/workflows/license-compliance.yml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive **OpenTelemetry** implementation in `server/src/otel/tracing.ts`. Instrumentations: Express, HTTP, NestJS, PostgreSQL (pg), Pino, Runtime Node. **W3C Trace Context** and **W3C Baggage** propagators configured for cross-service trace propagation. OTLP exporters for both traces and metrics. Custom metrics: `api.hits`, `api.duration`, `users.concurrent`, `sessions.active`, `users.concurrent.active`, `sessions.concurrent.active`. Audit log metrics. **Limitation:** OTEL is only enabled for EE/Cloud editions (`if tooljetEdition === TOOLJET_EDITIONS.EE || tooljetEdition === TOOLJET_EDITIONS.Cloud`). Community edition skips OTEL initialization. |
| **Gap** | Tracing is comprehensive but only available in EE/Cloud editions. Community edition users have no distributed tracing. OTEL is configured as a module-level auto-start but depends on edition check. |
| **Recommendation** | Consider enabling basic tracing for community edition (at minimum, health endpoint metrics). Ensure OTEL collector infrastructure is defined in IaC. Integrate with AWS X-Ray or Grafana Tempo for trace storage and querying. |
| **Evidence** | `server/src/otel/tracing.ts` (full OTEL setup), `server/package.json` (OTEL deps) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **No SLO definition files** found. No error budget tracking. Health check endpoint (`/api/health`) exists and is excluded from tracing. No `p99`/`p95` latency thresholds defined. No formal SLO monitoring or dashboards. The OTEL `api.duration` histogram provides raw latency data but no SLO targets are defined against it. |
| **Gap** | No formal SLO definitions — no measurable targets for availability, latency, or error rates. No error budget tracking to guide engineering prioritization. |
| **Recommendation** | Define SLOs for critical user journeys (app builder load time, data query execution latency, API availability). Set p99 latency targets and error rate thresholds. Implement SLO monitoring using CloudWatch or Grafana with the existing OTEL metrics as data sources. Track error budgets. |
| **Evidence** | `server/src/main.ts` (/api/health endpoint), `server/src/otel/tracing.ts` (api.duration histogram but no SLO targets) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Custom OTEL metrics: `users.concurrent` (login/logout based), `sessions.active`, `users.concurrent.active` (request-based per workspace), `sessions.concurrent.active`, `api.hits` (per route/method), `api.duration` (per route/method/status). Audit log metrics via `server/src/otel/audit-metrics.ts`. These are **operational metrics** with some business adjacency (concurrent users per workspace). No direct business outcome metrics (e.g., apps created per day, data queries executed, user onboarding completion rate). |
| **Gap** | Infrastructure and operational metrics exist. Some business-adjacent metrics (concurrent users). No direct business outcome metrics that would drive product decisions. |
| **Recommendation** | Add business outcome metrics: apps created/deployed per workspace, data queries executed per day, plugin marketplace installs, user activation rate. Publish alongside existing operational metrics. Build dashboards correlating business metrics with infrastructure health. |
| **Evidence** | `server/src/otel/tracing.ts` (custom metrics), `server/src/otel/audit-metrics.ts` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **No CloudWatch alarms** defined in any Terraform configuration. No anomaly detection configuration. **Sentry** integration (`@sentry/nestjs`, `@sentry/react`) captures errors but is configured via environment variable, not IaC. No alerting rules for error rates, latency, or resource utilization. Slack notifications exist for security scans (Grype, vulnerability-ci) but not for operational metrics. |
| **Gap** | No proactive alerting. No anomaly detection. No CloudWatch alarms for CPU, memory, error rates, or latency. System relies on manual observation or Sentry error notifications with no structured alerting. |
| **Recommendation** | Add CloudWatch alarms in IaC for: ECS CPU/memory utilization, API error rate (5xx), API p99 latency, RDS connections, RDS CPU. Enable CloudWatch anomaly detection on key metrics. Integrate with SNS/PagerDuty/OpsGenie for on-call alerting. |
| **Evidence** | `terraform/ECS/main.tf` (no alarms), `server/package.json` (@sentry/nestjs), `.env.example` (SENTRY_DNS) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECS service uses **rolling deployment** (`deployment_maximum_percent = 200`, `deployment_minimum_healthy_percent = 100`). Kubernetes deployment uses **RollingUpdate** (`maxUnavailable: 1`, `maxSurge: 1`). Health checks on `/api/health` with readiness probe (K8s: `initialDelaySeconds: 10`, `periodSeconds: 5`, `failureThreshold: 6`). ECS health check grace period of 900 seconds. No blue/green or canary deployment strategy. No traffic shifting. No deployment gates beyond health checks. |
| **Gap** | Rolling deployments with basic health checks but no staged rollout. All users receive the new version simultaneously once health check passes. No ability to detect regressions before full rollout. No automated rollback. |
| **Recommendation** | Adopt **canary deployments** using Argo Rollouts on EKS (preferred) or AWS CodeDeploy with ECS for blue/green. Configure automated rollback on CloudWatch alarm triggers (error rate spike, latency increase). Add deployment gates that require e2e test pass before production promotion. |
| **Evidence** | `terraform/ECS/main.tf` (deployment_maximum_percent=200), `deploy/kubernetes/deployment.yaml` (RollingUpdate) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CI pipeline runs **unit tests** (`npm --prefix server run test`) and **e2e tests** (`npm --prefix server run test:e2e`) with PostgreSQL service container. **Cypress tests** exist in `cypress-tests/` directory with dedicated workflows: `cypress-appbuilder.yml`, `cypress-marketplace.yml`, `cypress-platform.yml`. E2e tests use `jest` with `jest-e2e.json` configuration and `supertest` for HTTP testing. Test recording via `@pollyjs/core` for HTTP replay. |
| **Gap** | Integration tests cover primary workflows. Cypress tests exist for app builder, marketplace, and platform. Minor gap: Cypress workflows appear to be separate from the main CI pipeline and may not run on every PR. No contract tests for API compatibility. |
| **Recommendation** | Integrate Cypress tests into the main CI pipeline to run on every PR (not just separate workflows). Add API contract tests for critical endpoints. Consider adding load tests for performance regression detection. |
| **Evidence** | `.github/workflows/ci.yml` (unit-test, e2e-test jobs), `cypress-tests/`, `.github/workflows/cypress-appbuilder.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **No runbook files** found (no markdown, YAML, or JSON runbooks). No Systems Manager Automation documents. No self-healing patterns. Graceful shutdown handlers configured in `server/src/main.ts` (SIGINT, SIGTERM with app.close()). Sentry for error tracking but no automated remediation. Slack notifications exist for security scans but not for incident response. |
| **Gap** | Incident response is entirely ad hoc. No runbooks, no automation, no self-healing. Graceful shutdown is the only operational automation. |
| **Recommendation** | Create structured runbooks for common incidents (database connectivity failure, Redis unavailability, high error rate, deployment failure). Implement as Systems Manager Automation documents for one-click execution. Add ECS service auto-recovery patterns. Consider Lambda-based remediation for common failure modes. |
| **Evidence** | `server/src/main.ts` (graceful shutdown only), no runbook files found |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **CODEOWNERS** file defines ownership for: `package.json`/`package-lock.json` files (3 owners), `**/module.ts` files (2 owners), `server/migrations/` (2 owners). No per-service dashboards with named owners. No SLO definitions with team attribution. No CloudWatch alarms with owner tags. OTEL metrics exist but no ownership assignment for monitoring responsibility. |
| **Gap** | Code ownership is defined but observability ownership is ad hoc. No one is assigned responsibility for monitoring specific service components, responding to specific alerts, or maintaining specific dashboards. |
| **Recommendation** | Extend CODEOWNERS to include observability configurations (alarm definitions, dashboard files). Add team/owner tags to CloudWatch alarms and dashboards. Define per-module SLO ownership aligned with the NestJS module structure. |
| **Evidence** | `CODEOWNERS` (package.json and module.ts ownership only) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Minimal tags found: EC2 instance has `Name = "TooljetAppServer"`, VPC has `Name = "TooljetVPC"`, Internet Gateway has `Name = "TooljetInternetGateway"`. **No tags on ECS resources** (cluster, task definition, service). **No tags on RDS instance**. **No `default_tags` in AWS provider**. No cost allocation tags. No environment tags. No ownership tags. No tagging standard or enforcement (no AWS Config rules, no Tag Policies). |
| **Gap** | Almost no resource tagging. Only Name tags on EC2 resources. No cost allocation, ownership, environment, or project tags. Cannot track costs per workload, identify resource ownership, or enforce budget controls. |
| **Recommendation** | Add `default_tags` block to the AWS provider in Terraform with mandatory tags: `Environment`, `Project`, `Owner`, `CostCenter`. Apply tags to all resources. Enable AWS cost allocation tags. Add `required-tags` AWS Config rule for enforcement. |
| **Evidence** | `terraform/EC2/ec2.tf` (Name tags only), `terraform/ECS/main.tf` (no tags on ECS/RDS resources) |

## Learning Materials

Learning resources for triggered pathways:

### Move to Managed Databases
- [Move to Managed Databases — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [AWS Database Migration Guide](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-databases/welcome.html)

### Move to Modern DevOps
- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [AWS DevOps Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/devops/welcome.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1 | Root monorepo package.json, Node.js 22.15.1 engine |
| `server/package.json` | INF-Q3, INF-Q4, APP-Q1, APP-Q3, APP-Q4, SEC-Q3, SEC-Q4, SEC-Q6, OPS-Q1, OPS-Q4 | Server dependencies: NestJS, TypeORM, BullMQ, Temporal, OTEL, Passport, Sentry |
| `frontend/package.json` | APP-Q1 | Frontend dependencies: React, JavaScript |
| `terraform/ECS/main.tf` | INF-Q1, INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, SEC-Q1, SEC-Q2, SEC-Q5, OPS-Q4, OPS-Q5, OPS-Q9 | ECS Fargate, RDS PostgreSQL, Redis sidecar, VPC, subnets, security groups, ALB, CloudWatch log groups |
| `terraform/ECS/variables.tf` | INF-Q2, INF-Q9, SEC-Q2, SEC-Q5 | Variable defaults including default passwords |
| `terraform/ECS/redis.tf` | INF-Q2 | Commented-out MemoryDB cluster resource |
| `terraform/EC2/ec2.tf` | INF-Q1, INF-Q10, OPS-Q9 | EC2 instance alternative deployment, Name tags |
| `terraform/EC2/sg.tf` | INF-Q5 | Security group with 0.0.0.0/0 ingress on ports 22, 80, 443, 3000 |
| `deploy/helm/Chart.yaml` | INF-Q1, INF-Q10, DATA-Q3 | Helm chart with Bitnami PostgreSQL dependency |
| `deploy/helm/values.yaml` | INF-Q7, INF-Q8, INF-Q9, SEC-Q5 | HPA min:1/max:1, default credentials, PostgreSQL replication disabled |
| `deploy/kubernetes/deployment.yaml` | INF-Q1, APP-Q6, OPS-Q5, SEC-Q5 | K8s deployment with RollingUpdate, secretKeyRef, readiness probe |
| `deploy/kubernetes/service.yaml` | INF-Q6, APP-Q6 | LoadBalancer service with SSL annotation |
| `docker-compose.yaml` | INF-Q2, DATA-Q2, DATA-Q3 | Development environment: postgres:13, redis:6.2, PostgREST sidecar |
| `docker/ce-production.Dockerfile` | SEC-Q6 | debian:12 base image, multi-stage build, Oracle InstantClient |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6 | CI pipeline: build, lint, unit-test, e2e-test |
| `.github/workflows/docker-release.yml` | INF-Q11 | Docker image build/push on GitHub release |
| `.github/workflows/deploy-to-stage.yml` | INF-Q11 | Manual stage deployment to AKS + Cloudflare Pages |
| `.github/workflows/vulnerability-ci.yml` | SEC-Q6, SEC-Q7 | Weekly npm audit with automated fix PRs |
| `.github/workflows/grype-slack-notify.yml` | SEC-Q6, SEC-Q7 | Weekly Grype Docker image vulnerability scan |
| `.github/workflows/license-compliance.yml` | SEC-Q7 | License compliance check (MIT/Apache-2.0 only) |
| `.github/workflows/cypress-appbuilder.yml` | OPS-Q6 | Cypress e2e tests for app builder |
| `dependabot.yml` | SEC-Q7 | Daily Dependabot for npm (server, frontend, plugins, marketplace) |
| `server/src/main.ts` | APP-Q2, APP-Q5, APP-Q6, SEC-Q3, OPS-Q7 | NestJS bootstrap, API versioning (VERSION_NEUTRAL), graceful shutdown |
| `server/src/otel/tracing.ts` | OPS-Q1, OPS-Q2, OPS-Q3 | Full OTEL setup, W3C propagators, custom metrics |
| `server/src/otel/audit-metrics.ts` | SEC-Q1, OPS-Q3 | Audit log OTEL metrics |
| `server/src/modules/` | APP-Q2, INF-Q3 | ~60 NestJS modules (auth, apps, workflows, AI, etc.) |
| `server/src/modules/audit-logs/` | SEC-Q1 | Application-level audit logging |
| `server/src/modules/scim/` | SEC-Q4 | SCIM 2.0 user provisioning |
| `server/src/modules/ai/` | Decomposition Strategy | AI module with services, repositories, controllers |
| `server/src/modules/files/` | DATA-Q1 | File handling module |
| `server/src/modules/workflows/` | INF-Q3, APP-Q4, Decomposition Strategy | Workflow orchestration with Temporal |
| `server/migrations/` | DATA-Q4 | TypeScript-based database migrations (no SQL stored procedures) |
| `.env.example` | APP-Q6, SEC-Q4, SEC-Q5 | Environment variable configuration template |
| `CODEOWNERS` | OPS-Q8 | Code ownership for package.json, module.ts, migrations |
| `render.yaml` | DATA-Q3 | Render deployment with postgresMajorVersion: 13 |
| `README.md` | Quick Agent Wins | Documentation for RAG knowledge agent |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution documentation |
| `docs/` | Quick Agent Wins | Docusaurus documentation site |
| `cypress-tests/` | OPS-Q6 | Cypress e2e test suite |
