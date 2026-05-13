# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | tooljet |
| **Date** | 2025-07-01 |
| **TD Version** | modernization-assessment |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, low-code, frontend |
| **Context** | Open-source low-code internal-tool builder. |
| **Preferences (Prefer)** | eks, aurora, dynamodb, api-gateway, eventbridge, bedrock |
| **Preferences (Avoid)** | self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true |
| **Overall Score** | 2.3 / 4.0 |


**Archetype Justification**: The ToolJet server owns persistent state (PostgreSQL via TypeORM, Redis via ioredis) and exposes CRUD operations on business entities (apps, users, organizations, data sources, workflows). While BullMQ provides background job processing, the primary surface is a synchronous HTTP API. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.0 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.7 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.0 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.0 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 2.0 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.3 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q7: Auto-Scaling | 1 | No auto-scaling configured; all capacity statically provisioned | Cannot respond to traffic spikes; cost waste from over-provisioning or outages from under-provisioning |
| 2 | INF-Q8: Backup and Recovery | 1 | No backup configuration; skip_final_snapshot=true; no retention | Data loss risk with no recovery capability for all ToolJet application state |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or infrastructure audit logging in IaC | No forensic capability for security incidents at infrastructure level |
| 4 | SEC-Q2: Encryption at Rest | 1 | No storage_encrypted on RDS; no KMS keys | Sensitive data (apps, users, credentials) stored unencrypted at rest |
| 5 | OPS-Q9: Resource Tagging | 1 | No tags on ECS resources; no tagging standard or enforcement | No cost attribution, ownership tracking, or environment identification |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2). TypeORM entities provide a well-structured, centralized data access layer with 184 migrations and clearly defined entity schemas across apps, users, organizations, data sources, and workflows.
- **What it enables:** A natural-language-to-SQL agent that translates developer queries into TypeORM or raw PostgreSQL queries against the ToolJet database. Could also power a "ToolJet DB Explorer" for end-users building internal tools.
- **Additional steps:** Generate a machine-readable schema document from TypeORM entities for agent consumption. Expose a read-only query endpoint with guardrails to prevent mutations.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (≥ 2). GitHub Actions CI pipeline exists with build, lint, unit tests, e2e tests, and Docker image builds.
- **What it enables:** An agent that triggers Docker image builds, checks CI status, monitors vulnerability scan results (Grype, npm audit), and manages release workflows.
- **Additional steps:** Expose GitHub Actions API access to the agent; create a deployment trigger endpoint for ECS/K8s updates.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — README.md, CONTRIBUTING.md, docs/ directory, SECURITY.md, and extensive inline documentation in IaC and configuration files.
- **What it enables:** A knowledge agent that indexes ToolJet's documentation, setup guides, and configuration references to answer developer questions about deployment, configuration, and troubleshooting.
- **Additional steps:** Index documentation files using Amazon Bedrock with an embedding model. Store embeddings in a vector store (e.g., OpenSearch with vector engine). Connect to a Bedrock-powered RAG chain.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 3 (≥ 2). Temporal SDK (@temporalio/client, @temporalio/worker, @temporalio/workflow, @temporalio/activity) is integrated with server/src/modules/workflows/.
- **What it enables:** An agent that monitors Temporal workflow execution, identifies failed workflows, suggests retry strategies, and triggers workflow actions based on business events.
- **Additional steps:** Expose Temporal workflow status via API endpoints; integrate with Sentry for error correlation.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3 (≥ 2). Comprehensive OpenTelemetry setup with distributed tracing (HTTP, Express, NestJS, PostgreSQL, Pino instrumentations), W3C TraceContext propagation, and custom business metrics.
- **What it enables:** An agent that queries OTEL traces and metrics, correlates errors across service boundaries, identifies performance bottlenecks, and suggests root causes for incidents.
- **Additional steps:** Ensure OTEL data is exported to a queryable backend (e.g., AWS X-Ray, Grafana Tempo). Provide agent access to the metrics API.
- **Effort:** Low

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2=2 (primary met), but no supporting conditions met: INF-Q1=3, APP-Q3=3, APP-Q4=3 (all ≥ 3) |
| 2 | Move to Containers | Not Triggered | — | — | Container definitions exist (Dockerfiles, Helm, K8s manifests); compute already on ECS Fargate |
| 3 | Move to Open Source | Not Triggered | — | — | Primary database is PostgreSQL (open source); DATA-Q4=4; no commercial DB engines in primary infrastructure |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=2 (Redis self-managed as container sidecar) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing/analytics workloads detected; BullMQ is job queue, not analytics |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=2 (partial IaC), INF-Q11=2 (CI exists, deploy manual), OPS-Q5=2, OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Open-source low-code internal-tool builder") |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** PostgreSQL runs on RDS (managed, engine_version 16) — this is the correct approach. However, Redis runs as a self-managed container sidecar (`redis:6.2` image) within the ECS task definition, requiring manual patching, no automated failover, and shared CPU/memory with the application.

**Engine Versions and EOL Status:** PostgreSQL 16 on RDS is current and well-supported. Redis 6.2 as a container image is approaching EOL (Redis 6.2 reached end of life in early 2025).

**Data Access Patterns:** TypeORM provides centralized data access. Redis is used for BullMQ job queues, session caching, and in-memory operations via ioredis.

**Recommended Migration Target:** Replace the self-managed Redis sidecar with **Amazon ElastiCache for Redis** or **Amazon MemoryDB for Redis**. This provides automated failover, patching, backups, and scaling without sharing task resources. Consider Aurora PostgreSQL (per preferences) for enhanced read replicas and serverless scaling as the application grows.

**Representative AWS Services:** ElastiCache for Redis, MemoryDB for Redis, Aurora PostgreSQL

**Migration Tools:** Direct endpoint swap — update `REDIS_HOST` environment variable from `127.0.0.1` to the ElastiCache endpoint. Remove the Redis container from the ECS task definition.

**AWS Prescriptive Guidance:** [Amazon ElastiCache Migration Guide](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Migration.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 2):** Terraform covers core infrastructure (ECS cluster, task definition, VPC, ALB, RDS) but is missing operational resources — no CloudWatch alarms, no backup plans, no Route 53, no auto-scaling policies. Redis is defined inline as a container sidecar rather than as a managed resource. The Helm chart provides Kubernetes deployment but with minimal operational configuration (HPA min=max=1).

**Current CI/CD State (INF-Q11 = 2):** GitHub Actions provides build automation (ci.yml: build, lint, unit tests, e2e tests) and Docker image publishing (docker-release.yml on GitHub releases). However, deployment to production (ECS or Kubernetes) is not automated in the pipeline — no CodeDeploy, no `aws ecs update-service`, no ArgoCD, no Flux. Deployment appears to be manual or out-of-band.

**Deployment Strategy Gaps (OPS-Q5 = 2):** Rolling updates are configured (ECS: deployment_maximum_percent=200; K8s: RollingUpdate), but no canary or blue/green deployment strategy exists. No traffic shifting, no feature flags.

**Testing Gaps (OPS-Q6 = 3):** Integration tests and Cypress e2e tests run in CI, which is good. However, they are triggered only on labeled PRs (`run-ci` label), not on every push, which creates coverage gaps.

**Recommended DevOps Toolchain:**
1. **Add automated deployment** to CI/CD pipeline — deploy Docker images to ECS using `aws ecs update-service` or CodeDeploy for blue/green deployments
2. **Expand IaC coverage** — add CloudWatch alarms, backup plans, auto-scaling policies, and Route 53 records to Terraform
3. **Adopt GitOps** for Kubernetes deployments using ArgoCD or Flux (aligns with EKS preference)
4. **Implement canary deployments** using AWS CodeDeploy with ECS or Argo Rollouts with EKS

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CDK, CloudWatch, EKS (per preferences)

**AWS Prescriptive Guidance:** [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Decomposition Strategy

> APP-Q2 = 2 — ToolJet is a modular monolith with identifiable NestJS module boundaries but shared database schemas and a single deployment unit.

### Recommended Approach: Strangler Fig (Parallel Track)

| Factor | Assessment | Signal |
|--------|-----------|--------|
| Module boundaries | ✅ Clear NestJS module structure with 55+ modules (auth, apps, workflows, ai, data-queries, etc.) | Low effort |
| Data coupling | ⚠️ Single PostgreSQL database shared across all modules; TypeORM entities likely have cross-module relations | High effort |
| Stored procedures | ✅ No stored procedures found in 184 migration files; all logic in application layer | Low effort |
| Communication patterns | ✅ BullMQ async jobs + Temporal workflows; some async already in place | Medium effort |
| CI/CD maturity | ⚠️ Build/test automated but deployment manual; pipeline extension needed | Medium effort |
| Test coverage | ✅ Unit + e2e + Cypress tests in CI | Low effort |

**Recommended Approach:** ✅ **Strangler Fig (Parallel Track)** — Given the clear NestJS module boundaries, incrementally extract high-value modules into independent services while keeping the monolith running. The NestJS module system provides natural seams for extraction.

**Suggested Extraction Order:**
1. **Workflows Module** → Independent service backed by Temporal (already has @temporalio SDK). Deploy as a separate EKS service (per preferences).
2. **AI Module** → Independent service that can scale independently and leverage Amazon Bedrock (per preferences).
3. **Data Queries / Plugins** → Extract the data source connector layer into a separate service with its own scaling characteristics.

**Pattern Recommendations:**

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the monolith's data model | Every extraction — place an ACL between new services and the monolith |
| **Saga Pattern** | Manage distributed transactions (e.g., app creation + permissions + data source setup) | When extracting modules that participate in multi-step transactions |
| **Event Sourcing** | Capture app edit history, audit trail of configuration changes | When extracting the apps/versions module |
| **Hexagonal Architecture** | Structure each new service with clear domain boundaries | Every new service |

**Estimated Timeline:** 6–12 months for first two extractions (workflows, AI). Full decomposition: 12–18 months.

⚠️ **Big-Bang Rewrite is NOT recommended.** The monolith is functional, well-structured with NestJS modules, and has established test coverage. Incremental extraction is the safe path.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary production path uses ECS Fargate (`requires_compatibilities = ["FARGATE"]`) in `terraform/ECS/main.tf` with a 4096 CPU / 8192 MiB task. Kubernetes Deployment manifests exist in `deploy/kubernetes/deployment.yaml` and Helm charts in `deploy/helm/`. However, `terraform/EC2/ec2.tf` defines an alternative raw EC2 deployment with `aws_instance` using user-data scripts. Multiple deployment options coexist, with ECS Fargate as the managed compute primary. |
| **Gap** | EC2 deployment path remains available as an alternative, representing unmanaged compute. No Lambda or App Runner usage. |
| **Recommendation** | Consolidate on EKS (per preferences) or ECS Fargate as the sole production deployment model. Deprecate the EC2 deployment path or clearly document it as a development/testing option only. |
| **Evidence** | `terraform/ECS/main.tf` (ECS Fargate task), `terraform/EC2/ec2.tf` (EC2 instance), `deploy/kubernetes/deployment.yaml`, `deploy/helm/Chart.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | PostgreSQL runs on RDS (`aws_db_instance` with `engine = "postgres"`, `engine_version = "16"` in `terraform/ECS/main.tf`) — fully managed. However, Redis runs as a self-managed container sidecar (`image: redis:6.2`) within the ECS task definition, sharing CPU/memory with the application container (512 CPU, 1024 MiB). PostgREST also runs as a sidecar container. The Helm chart bundles a Bitnami PostgreSQL dependency (`version: 11.1.3`). |
| **Gap** | Redis is self-managed as a container sidecar — no automated failover, no managed patching, no independent scaling. Redis 6.2 is approaching end-of-life. |
| **Recommendation** | Replace the Redis sidecar with Amazon ElastiCache for Redis or MemoryDB for Redis. This removes the self-managed burden, provides Multi-AZ failover, and frees task CPU/memory for the application. Update `REDIS_HOST` from `127.0.0.1` to the ElastiCache endpoint. |
| **Evidence** | `terraform/ECS/main.tf` (aws_db_instance, redis:6.2 sidecar), `docker-compose.yaml` (redis:6.2), `deploy/helm/Chart.yaml` (postgresql dependency) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Temporal SDK is integrated (`@temporalio/client`, `@temporalio/worker`, `@temporalio/workflow`, `@temporalio/activity` in `server/package.json`). The `server/src/modules/workflows/` directory contains controllers, services, processors, listeners, DTOs, and guards — indicating active workflow orchestration. Archetype = stateful-crud, so this scores against the stateful-crud column. |
| **Gap** | Partial adoption — Temporal covers workflow orchestration, but not all multi-step operations may be using it. BullMQ handles background jobs separately. Two orchestration systems coexist without clear separation of concerns. |
| **Recommendation** | Formalize the boundary between Temporal (multi-step business workflows) and BullMQ (simple background job processing). Consider migrating simple BullMQ jobs to Temporal activities if they benefit from Temporal's retry and state management. |
| **Evidence** | `server/package.json` (@temporalio/*), `server/src/modules/workflows/` (module structure) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | BullMQ (`bullmq`, `@nestjs/bull`, `@nestjs/bullmq` in `server/package.json`) provides async job processing via Redis. `@nestjs/event-emitter` handles in-process event-driven patterns. WebSocket support (`ws`, `y-websocket`) for real-time collaboration. However, all messaging relies on self-managed Redis — no SQS, SNS, EventBridge, MSK, or Kinesis in IaC. Archetype = stateful-crud. |
| **Gap** | Cross-service state changes rely on self-managed Redis (BullMQ). No managed messaging service for cross-service event distribution. For a stateful-crud archetype, managed messaging should be in place for key flows (state change notifications, webhook delivery, etc.). |
| **Recommendation** | Adopt Amazon EventBridge (per preferences) for cross-service state change events and notifications. Keep BullMQ for internal job processing or migrate to SQS for managed job queues. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `server/package.json` (bullmq, @nestjs/bull, @nestjs/event-emitter, ws), `terraform/ECS/main.tf` (no SQS/SNS/EventBridge) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Custom VPC (`10.0.0.0/16`) with 2 subnets across 2 AZs in `terraform/ECS/main.tf`. Security groups restrict RDS access to the task security group. However: (1) subnets have `map_public_ip_on_launch = true` — these are public subnets, not private; (2) ECS tasks are assigned public IPs (`assign_public_ip = true`); (3) task SG allows 0.0.0.0/0 on port 443; (4) LB SG allows 0.0.0.0/0 on ports 80 and 443. EC2 deployment (`terraform/EC2/sg.tf`) allows 0.0.0.0/0 on ports 22, 80, 443, and 3000. No VPC endpoints, no PrivateLink, no NAT Gateway. |
| **Gap** | Services deployed in public subnets with public IP assignment. Overly permissive security group rules (SSH from 0.0.0.0/0 on EC2). No private subnet tier for compute workloads. No VPC endpoints for AWS service access. |
| **Recommendation** | Move ECS tasks to private subnets with a NAT Gateway for outbound access. Remove public IP assignment. Add VPC endpoints for ECR, S3, CloudWatch Logs, and Secrets Manager. Restrict EC2 SSH access to a bastion host or Systems Manager Session Manager. |
| **Evidence** | `terraform/ECS/main.tf` (VPC, subnets, security groups), `terraform/EC2/sg.tf` (0.0.0.0/0 on 22, 80, 443, 3000) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ALB (`aws_lb`) in `terraform/ECS/main.tf` serves as the entry point with a target group and `/api/health` health check. HTTP listener on port 80 is active. HTTPS listener on port 443 is **commented out** — indicating TLS termination is not configured in the provided IaC. No API Gateway, no CloudFront, no WAF configured. |
| **Gap** | ALB present but with minimal configuration — no TLS (HTTPS listener commented out), no throttling, no authentication at the gateway level, no WAF. Traffic enters over plain HTTP. |
| **Recommendation** | Enable the HTTPS listener with a valid ACM certificate. Add API Gateway (per preferences) in front of the ALB for throttling, request validation, and API key management. Consider CloudFront for global edge caching and DDoS protection via AWS Shield. |
| **Evidence** | `terraform/ECS/main.tf` (aws_lb, aws_lb_listener port 80, commented HTTPS listener) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling resources found anywhere in Terraform (`aws_autoscaling_*`, `aws_appautoscaling_*`). ECS service uses static `desired_count = 2`. Helm HPA is configured with `min: 1, max: 1` — effectively disabled. No Lambda concurrency limits. No DynamoDB auto-scaling. No scaling policies on any resource. |
| **Gap** | All capacity is statically provisioned. The application cannot respond to traffic spikes or scale down during low demand, leading to either over-provisioning (cost waste) or under-provisioning (degraded experience). |
| **Recommendation** | Configure ECS Application Auto Scaling with target tracking policies (e.g., CPU utilization, request count per target). Update Helm HPA to a meaningful range (e.g., min=2, max=10). Consider custom CloudWatch metrics for business-driven scaling (e.g., active users per workspace). |
| **Evidence** | `terraform/ECS/main.tf` (desired_count=2, no scaling), `deploy/helm/values.yaml` (hpa min=1, max=1) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | RDS instance in `terraform/ECS/main.tf` has `skip_final_snapshot = true` and no explicit `backup_retention_period` (defaults to 0 for `db.t3.micro` when not specified). No `aws_backup_plan` resources. No PITR configuration. No S3 versioning for any state. No cross-region backup replication. |
| **Gap** | No backup configuration found. `skip_final_snapshot = true` means even instance deletion produces no backup. The PostgreSQL database — containing all ToolJet application state — has no recovery capability. |
| **Recommendation** | Add `backup_retention_period = 7` (minimum) and `skip_final_snapshot = false` to the RDS instance. Enable PITR on the database. Create an `aws_backup_plan` for automated daily backups with cross-region replication. Document and test restore procedures. |
| **Evidence** | `terraform/ECS/main.tf` (skip_final_snapshot=true, no backup_retention_period) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECS service spans 2 subnets across 2 AZs (`us-east-1c`, `us-east-1d`) with `desired_count = 2`. Kubernetes deployment has `replicas: 2`. However, RDS `aws_db_instance` has no `multi_az = true` specified — it defaults to single-AZ for `db.t3.micro`. No explicit AZ distribution for Redis (runs as a sidecar). |
| **Gap** | Main production database is single-AZ. An AZ failure would take down the database with no automatic failover. Compute spans 2 AZs (good), but the data tier is the single point of failure. |
| **Recommendation** | Enable `multi_az = true` on the RDS instance (requires upgrading from `db.t3.micro`). When migrating Redis to ElastiCache, configure Multi-AZ with automatic failover. Consider Aurora PostgreSQL (per preferences) for built-in multi-AZ with up to 15 read replicas. |
| **Evidence** | `terraform/ECS/main.tf` (2 subnets, 2 AZs for ECS; no multi_az on RDS), `terraform/ECS/variables.tf` (us-east-1c, us-east-1d) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Terraform covers: ECS cluster, task definition, ECS service, VPC, subnets, internet gateway, route tables, security groups, ALB, target group, listeners, RDS instance, IAM roles/policies. Helm chart covers: Kubernetes deployment, service, HPA, secrets. However, missing from IaC: CloudWatch alarms, CloudWatch dashboards, Route 53 records, backup plans, auto-scaling policies, WAF rules, SNS topics, S3 buckets, Secrets Manager secrets (policy exists but secret itself not in IaC). Redis is inline in the task definition, not a managed resource. EC2/AMI_EC2/Azure_VM/GCP Terraform modules add coverage breadth but duplicate infrastructure across providers. |
| **Gap** | Partial IaC — primary compute and networking covered, but operational resources (monitoring, alerting, backup, scaling, DNS) are not in code. Estimated 50-60% of production infrastructure is in IaC. |
| **Recommendation** | Expand Terraform to include CloudWatch alarms (error rates, latency p99), Route 53 DNS records, AWS Backup plans, auto-scaling policies, and Secrets Manager secrets. Consider adopting CDK for TypeScript-native IaC that aligns with the team's language expertise. |
| **Evidence** | `terraform/ECS/main.tf`, `terraform/EC2/ec2.tf`, `deploy/helm/Chart.yaml`, `deploy/helm/values.yaml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides comprehensive build and test automation: `ci.yml` (build, lint, unit tests, e2e tests), `docker-release.yml` (Docker image builds on release for CE, EE, and Cloud editions), `vulnerability-ci.yml` (npm audit), `grype-slack-notify.yml` (container scanning), `license-compliance.yml`. However, no automated deployment step exists in any workflow — no `aws ecs update-service`, no CodeDeploy, no ArgoCD, no Flux, no Kubernetes apply. Docker images are pushed to Docker Hub but not deployed to any environment automatically. `deploy-to-stage.yml` exists but may require manual triggering. |
| **Gap** | Build is automated but deployment is manual. Docker images are published but not automatically deployed to staging or production. This creates a bottleneck at the deployment stage and increases the risk of deploying untested configurations. |
| **Recommendation** | Add automated deployment stages to `docker-release.yml` — deploy to staging automatically after image push, then promote to production with manual approval. Use CodeDeploy for ECS blue/green deployments or ArgoCD for EKS GitOps (per preferences). |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/docker-release.yml`, `.github/workflows/deploy-to-stage.yml`, `.github/workflows/vulnerability-ci.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Server: TypeScript 5.8+ with NestJS 11.x on Node.js 22.15.1 (current LTS). Frontend: JavaScript/React 18.2 with Webpack 5. Plugins: TypeScript. All dependencies are current versions — no legacy framework or SDK lag. No AWS SDK in server dependencies (uses `got` and `undici` for HTTP), but the ecosystem has first-class `@aws-sdk/client-*` support for Node.js/TypeScript. |
| **Gap** | No gap — modern cloud-native language at current versions with matching modern frameworks. |
| **Recommendation** | No action needed. When integrating AWS services (Bedrock, EventBridge per preferences), use `@aws-sdk/client-*` v3 for TypeScript-native SDK support. |
| **Evidence** | `server/package.json` (typescript ^5.8.3, @nestjs/* 11.x), `frontend/package.json` (react ^18.2.0), `.nvmrc` (v22.15.1), `package.json` (engines.node: 22.15.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ToolJet is a modular monolith — a single NestJS application (`server/`) containing 55+ modules (auth, apps, data-queries, workflows, ai, organizations, audit-logs, CRM, scim, etc.) deployed as one container. All modules share a single PostgreSQL database. The worker process (`WORKER=true` flag in `server/src/main.ts`) runs the same codebase as a separate process but is not an independent service. Frontend is built separately but bundled into the same production Docker image (`docker/ce-production.Dockerfile`). PostgREST runs as a sidecar, not an independent service. NestJS module boundaries provide identifiable seams, but cross-module data access through shared TypeORM entities and a single database creates tight coupling. |
| **Gap** | Single deployable unit with shared database. Cross-module dependencies exist through shared entities. Independent scaling, deployment, and team autonomy are not possible for individual modules. |
| **Recommendation** | Begin Strangler Fig decomposition starting with the workflows module (already backed by Temporal) and AI module. Define per-module database schemas to prepare for database-per-service. See Decomposition Strategy section. |
| **Evidence** | `server/src/modules/` (55+ module directories), `server/ormconfig.ts` (single postgres connection), `docker/ce-production.Dockerfile` (single image), `server/package.json` (worker:prod script) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Archetype = stateful-crud. Mix of async and sync patterns: BullMQ for async job processing (`@nestjs/bull`, `@nestjs/bullmq`), `@nestjs/event-emitter` for in-process async events, Temporal for async workflow execution, and WebSocket (`ws`, `y-websocket`) for real-time collaboration. Primary API surface is synchronous HTTP (NestJS/Express). For a stateful-crud archetype, this is a good balance — sync for CRUD operations, async for key workflows and background processing. |
| **Gap** | Minor — async patterns exist for key workflows, but some state change notifications and webhook deliveries may still be synchronous. The lack of managed messaging (see INF-Q4) limits async scalability. |
| **Recommendation** | Adopt EventBridge (per preferences) for cross-service state change events as modules are extracted. The existing BullMQ + Temporal + event-emitter foundation provides a solid async pattern. |
| **Evidence** | `server/package.json` (bullmq, @nestjs/event-emitter, @temporalio/*, ws, y-websocket), `server/src/main.ts` (Express/NestJS HTTP) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Archetype = stateful-crud. Temporal workflows (`server/src/modules/workflows/`) handle long-running orchestration processes. BullMQ provides background job processing via a dedicated worker process (`worker:prod` script). The worker runs as a separate process of the same codebase with `WORKER=true`. For a stateful-crud archetype, most long-running operations should be async — Temporal + BullMQ cover the primary use cases. |
| **Gap** | Most long-running operations appear to be async via Temporal and BullMQ. However, some data source query operations (plugin executions) may still be synchronous depending on the plugin. |
| **Recommendation** | Audit data source query execution for long-running operations (e.g., large SQL queries, slow API calls). Ensure plugin executions that exceed 30 seconds are routed through BullMQ with status polling. |
| **Evidence** | `server/src/modules/workflows/` (Temporal workflows), `server/package.json` (bullmq, @temporalio/*), `package.json` (worker:prod script) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | `server/src/main.ts` enables URI-based versioning (`VersioningType.URI` with `VERSION_NEUTRAL` as default). The versioning infrastructure exists in the NestJS framework. However, `VERSION_NEUTRAL` as default means all endpoints respond without a version prefix unless explicitly versioned. No `/v1/` or `/v2/` URL patterns were detected in the primary route declarations. No API changelog or version deprecation policy found. |
| **Gap** | Versioning infrastructure is set up but applied ad hoc — `VERSION_NEUTRAL` default means most endpoints are unversioned. This makes it impossible to make breaking changes without affecting all consumers. |
| **Recommendation** | Set a concrete default version (e.g., `VERSION_1`) and version all public API endpoints. Establish a version deprecation policy. Generate OpenAPI documentation for each API version. |
| **Evidence** | `server/src/main.ts` (VersioningType.URI, VERSION_NEUTRAL) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ToolJet is a monolith — internal module communication is in-process. External service endpoints are configured via environment variables: `PG_HOST`, `REDIS_HOST`, `PGRST_HOST` (PostgREST on `127.0.0.1:3002`). Kubernetes `service.yaml` provides cluster DNS-based service discovery. No AWS Cloud Map, no Consul, no Istio service mesh. No centralized API catalog. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. As services are extracted from the monolith, hard-coded or env-var-based endpoints will create deployment coupling. |
| **Recommendation** | For Kubernetes deployments (EKS per preferences), leverage Kubernetes DNS-based service discovery. For ECS, use AWS Cloud Map for service discovery. As the architecture evolves toward microservices, implement API Gateway (per preferences) as a centralized entry point and service catalog. |
| **Evidence** | `deploy/kubernetes/deployment.yaml` (env vars for PG_HOST, REDIS_HOST, PGRST_HOST), `deploy/kubernetes/service.yaml` (ClusterIP service) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No S3 bucket resources found in IaC. No `@aws-sdk/client-s3` in dependencies. File uploads appear to be handled by `server/src/modules/files/` but the storage mechanism is not S3-based in the open-source edition. The Dockerfile does not install S3-related packages. Files appear to be stored locally or in the database. No Textract or document parsing pipeline detected. |
| **Gap** | Unstructured data (file uploads, documents) stored in managed storage but not S3. No parsing or extraction pipeline for document content. Limited accessibility for analytics or AI integration. |
| **Recommendation** | Migrate file storage to S3 with bucket-per-environment. Add Textract or Tika for document parsing if internal tools need document content extraction. Configure S3 lifecycle policies and versioning. |
| **Evidence** | `server/package.json` (no @aws-sdk/client-s3), `terraform/ECS/main.tf` (no aws_s3_bucket), `docker/ce-production.Dockerfile` (no S3 SDK) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeORM provides a centralized ORM-based data access layer (`server/ormconfig.ts` with PostgreSQL configuration). Entity definitions use TypeORM decorators. 184 migration files in `server/migrations/` demonstrate structured schema evolution. Two database connections exist: primary PostgreSQL and ToolJet DB (a separate PostgreSQL database for user-created data). NestJS modules follow a service/repository pattern. However, PostgREST (`postgrest/postgrest:v12.2.0`) provides a secondary data access path — a REST API directly on the database — which bypasses the application's data access layer. |
| **Gap** | Mostly centralized through TypeORM, but PostgREST provides a secondary direct-database access path that bypasses application-layer validation and business logic. Two database connection configurations (primary PG + ToolJet DB) add complexity. |
| **Recommendation** | Ensure PostgREST access is restricted to the ToolJet DB (user-created tables) and not the primary application database. Enforce all application-level business logic through the NestJS service layer. Consider replacing PostgREST with a managed API (API Gateway + Lambda or AppSync) for the ToolJet DB feature. |
| **Evidence** | `server/ormconfig.ts` (two DB connections), `server/migrations/` (184 files), `terraform/ECS/main.tf` (PostgREST sidecar), `docker-compose.yaml` (PostgREST service) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | PostgreSQL version is explicitly pinned in Terraform: `engine_version = "16"` in `terraform/ECS/main.tf` — PostgreSQL 16 is current and well-supported (EOL not until 2028). Docker Compose uses `postgres:13` (supported until November 2025, approaching EOL). Redis `6.2` in Docker Compose and ECS sidecar has reached community EOL. Helm chart references Bitnami PostgreSQL chart `version: 11.1.3` (chart version, not engine version). No documented version-update procedure. |
| **Gap** | Production PostgreSQL (v16) is current. However, Docker Compose PostgreSQL (v13) is approaching EOL. Redis 6.2 has reached community EOL. No documented version upgrade procedure. |
| **Recommendation** | Upgrade Docker Compose PostgreSQL from 13 to 16 to match production. Upgrade Redis from 6.2 to 7.x (or migrate to ElastiCache which manages versions automatically). Document a version-update procedure covering downtime windows, rollback, and risk assessment. |
| **Evidence** | `terraform/ECS/main.tf` (engine_version="16"), `docker-compose.yaml` (postgres:13, redis:6.2), `deploy/helm/Chart.yaml` (postgresql 11.1.3) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found in the 184 migration files. All migrations use TypeORM's query runner with standard SQL (CREATE TABLE, ALTER TABLE, CREATE INDEX). Business logic is entirely in the NestJS application layer. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements detected. The application uses the `pg` driver with TypeORM — no proprietary SQL dialect dependencies. |
| **Gap** | No gap — all business logic resides in the application layer. The database serves as a pure data store with no embedded logic. |
| **Recommendation** | No action needed. Continue the practice of keeping business logic in the application layer. This makes database migration (e.g., to Aurora PostgreSQL per preferences) straightforward. |
| **Evidence** | `server/migrations/` (184 files, no stored procedures), `server/ormconfig.ts` (TypeORM with postgres), `server/package.json` (pg driver) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No `aws_cloudtrail` resource found in any Terraform file. No CloudTrail configuration in IaC. Application-level audit logging exists (`server/src/modules/audit-logs/` directory, `server/src/otel/audit-metrics.ts` for OTEL-based audit metrics), but this covers application events, not infrastructure API calls. No immutable log storage (S3 Object Lock) configured. CloudWatch log groups exist with 30-day retention (`/ecs/ToolJet`, `/ecs/postgrest`). |
| **Gap** | No CloudTrail or equivalent infrastructure audit logging. Application-level audit logs exist but do not cover AWS API calls, IAM actions, or infrastructure changes. No immutable storage for audit trails. |
| **Recommendation** | Enable CloudTrail in IaC with log file validation. Store logs in an S3 bucket with Object Lock for immutability. Configure CloudTrail to log management events and data events for S3 and Lambda. Integrate CloudTrail with CloudWatch Logs for real-time alerting. |
| **Evidence** | `terraform/ECS/main.tf` (no aws_cloudtrail), `server/src/modules/audit-logs/` (app-level), `server/src/otel/audit-metrics.ts` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | RDS instance in `terraform/ECS/main.tf` has no `storage_encrypted = true` and no `kms_key_id` specified — storage encryption is not enabled. No `aws_kms_key` resources found in any Terraform file. No S3 buckets defined in IaC (no encryption to evaluate). EBS root volume on EC2 (`terraform/EC2/ec2.tf`) uses default gp3 with no encryption. |
| **Gap** | No encryption at rest configured on any data store. The RDS instance storing all ToolJet application data (apps, users, organizations, credentials) is unencrypted. |
| **Recommendation** | Add `storage_encrypted = true` to the RDS instance. Create a customer-managed KMS key for database encryption. Enable EBS encryption by default for EC2 instances. When adding S3 buckets, configure SSE-KMS. |
| **Evidence** | `terraform/ECS/main.tf` (aws_db_instance — no storage_encrypted, no kms_key_id), `terraform/EC2/ec2.tf` (no encrypted flag on root_block_device) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JWT-based authentication via `@nestjs/passport`, `passport-jwt`, and `@nestjs/jwt` in `server/package.json`. SAML SSO support via `@node-saml/node-saml`. OIDC client integration via `openid-client`. Throttling via `@nestjs/throttler`. Auth modules exist (`server/src/modules/auth/`, `server/src/modules/login-configs/`). CASL for authorization (`@casl/ability`). Public health check endpoints (`/api/health`) are explicitly excluded from auth. However, no API Gateway-level authentication (no API Gateway in IaC). |
| **Gap** | Token-based auth on all external endpoints with OIDC/SAML support is good. Internal endpoints may lack auth if relying only on network isolation (PostgREST on localhost:3002). No gateway-level throttling or validation beyond NestJS middleware. |
| **Recommendation** | Add API Gateway (per preferences) with authorizer integration for gateway-level auth. Ensure PostgREST endpoints are authenticated via JWT (PGRST_JWT_SECRET is configured). |
| **Evidence** | `server/package.json` (@nestjs/passport, passport-jwt, @nestjs/jwt, @node-saml/node-saml, openid-client, @nestjs/throttler, @casl/ability), `server/src/main.ts` (health check exclusions) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | ToolJet supports external IdP federation: Google OAuth2 (`SSO_GOOGLE_OAUTH2_CLIENT_ID`), GitHub OAuth2 (`SSO_GIT_OAUTH2_CLIENT_ID`), SAML (`@node-saml/node-saml`), OIDC (`openid-client`), and LDAP (`ldapts`). SSO configuration is available (`server/src/modules/login-configs/`). SCIM provisioning support exists (`server/src/modules/scim/`). However, the application also manages its own local authentication (bcrypt-based passwords, session management). Not all auth flows may use the external IdP. |
| **Gap** | Application supports centralized IdP for most flows, but some legacy local auth paths remain (local email/password login with bcrypt). |
| **Recommendation** | Encourage SSO-only mode for enterprise deployments. Document how to disable local auth when an external IdP is configured. Consider AWS Cognito integration for a managed user pool with IdP federation. |
| **Evidence** | `.env.example` (SSO_GOOGLE_OAUTH2_CLIENT_ID, SSO_GIT_OAUTH2_CLIENT_ID), `server/package.json` (@node-saml/node-saml, openid-client, ldapts, bcrypt), `server/src/modules/scim/` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Terraform includes an IAM policy for Secrets Manager access (`secrets_manager_policy` referencing `tooljet-secret`), indicating awareness of managed secrets. Kubernetes deployment uses `secretKeyRef` for database credentials. However: (1) ECS task definition passes `TOOLJET_DB_PASS`, `PG_PASS`, `LOCKBOX_MASTER_KEY`, `SECRET_KEY_BASE`, `REDIS_PASSWORD`, and `PGRST_JWT_SECRET` as plaintext environment variables from Terraform variables; (2) `terraform/ECS/variables.tf` defaults `PG_USER` to `"postgres"` and `PG_PASS` to `"postgres"`; (3) `deploy/helm/values.yaml` contains `pg_password: "postgresql"` and `lockbox_key: "0123456789ABCDEF"` in plaintext; (4) RDS instance has hardcoded `username = "postgres"` and `password = "postgres"` in `terraform/ECS/main.tf`. No `.env` file committed (only `.env.example` with placeholders). No rotation configured. |
| **Gap** | No plaintext credentials in committed source code (`.env.example` uses placeholders), but production credentials are passed as environment variables and Terraform variables without encryption. Helm values contain default plaintext passwords. RDS master credentials are hardcoded in Terraform. Secrets Manager policy exists but is not used to inject secrets into the task definition. |
| **Recommendation** | Replace all plaintext environment variable secrets with Secrets Manager references in the ECS task definition. Use `secrets` (not `environment`) in the container definition to pull from Secrets Manager. Remove hardcoded RDS credentials and use `manage_master_user_password = true` for RDS-managed secrets. Configure rotation on Secrets Manager secrets. Remove default passwords from Helm values. |
| **Evidence** | `terraform/ECS/main.tf` (plaintext env vars, hardcoded RDS password="postgres"), `terraform/ECS/variables.tf` (PG_PASS default "postgres"), `deploy/helm/values.yaml` (pg_password: "postgresql", lockbox_key: "0123456789ABCDEF") |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker image uses `node:22.15.1` (builder) and `debian:12` (runtime) base images — standard but not hardened (no CIS benchmarks, no Bottlerocket, no distroless). `apt-get update` and package installation in Dockerfile. Non-root user created (`appuser`). Grype vulnerability scanning runs weekly on Docker images (`grype-slack-notify.yml`). No SSM Patch Manager. No AWS Inspector. EC2 deployment uses custom AMI with user-data script (`install_tooljet.sh`). Packer workflow exists (`packer-build.yml`) for AMI building. |
| **Gap** | Manual patching process — no SSM Patch Manager. Default Debian base images without hardening. No AWS Inspector for continuous vulnerability assessment. Grype scans are weekly, not per-build. |
| **Recommendation** | Switch to a minimal/hardened base image (e.g., distroless, Alpine, or Bottlerocket for EKS). Run Grype scanning in the CI pipeline (not just weekly) to catch vulnerabilities before release. Enable AWS Inspector for continuous assessment. For EC2, use SSM Patch Manager for automated patching. |
| **Evidence** | `docker/ce-production.Dockerfile` (debian:12, non-root user), `.github/workflows/grype-slack-notify.yml` (weekly Grype scan), `.github/workflows/packer-build.yml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependency vulnerability scanning is well-established: `vulnerability-ci.yml` runs `npm audit` periodically (weekly) and on-demand for frontend, server, plugins, marketplace, and root. `grype-slack-notify.yml` runs Grype container scanning weekly. `dependabot.yml` configured for daily npm dependency updates across all directories. `license-compliance.yml` checks package licenses. However: no SAST tool (no SonarQube, Semgrep, CodeGuru Reviewer, ESLint security rules). No DAST tool. Grype is weekly, not in every build pipeline. No security gate blocking deployment on critical findings. |
| **Gap** | Dependency scanning present (npm audit, Dependabot, Grype) but no SAST tool in CI/CD. No blocking security gates — vulnerabilities are reported but do not stop deployments. Container scanning is weekly, not per-build. |
| **Recommendation** | Add a SAST tool (Semgrep or CodeGuru Reviewer) to the CI pipeline. Run Grype container scanning on every Docker image build (not just weekly). Add a security gate that blocks deployment on critical/high findings. Consider ESLint security plugins (`eslint-plugin-security`) for JavaScript-specific patterns. |
| **Evidence** | `.github/workflows/vulnerability-ci.yml` (npm audit), `.github/workflows/grype-slack-notify.yml` (weekly Grype), `dependabot.yml` (daily npm updates), `.github/workflows/license-compliance.yml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive OpenTelemetry setup in `server/src/otel/tracing.ts`: NodeSDK with BatchSpanProcessor, OTLP trace and metric exporters, W3C TraceContext + W3C Baggage propagation. Instrumentations include HTTP, Express, NestJS, PostgreSQL (`PgInstrumentation` with enhanced database reporting), Pino logging, and Node.js runtime. Custom middleware (`otelMiddleware`) tracks API hits, duration, and request attributes. Conditional on `ENABLE_OTEL=true` and Enterprise/Cloud edition. |
| **Gap** | Tracing is comprehensive but conditional on EE/Cloud edition — the community edition does not have OTEL enabled by default. Some service boundaries (Redis, external plugin calls) may lack explicit instrumentation. |
| **Recommendation** | Consider making basic OTEL tracing available in the CE edition. Add Redis instrumentation (`@opentelemetry/instrumentation-ioredis`). Ensure Temporal workflow spans are correlated with HTTP request traces. |
| **Evidence** | `server/src/otel/tracing.ts` (full OTEL setup), `server/package.json` (@opentelemetry/* packages) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definition files found in the repository. No error budget tracking. No latency or availability targets defined. Health check endpoint exists (`/api/health`) but no SLO is defined for it. CloudWatch log groups exist with retention policies but no SLO-driven alerting. OTEL metrics (api.duration, api.hits) provide the data foundation but are not connected to SLO definitions. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for API latency, availability, or error rates. Without SLOs, there is no objective measure of whether the system is meeting user expectations. |
| **Recommendation** | Define SLOs for critical user journeys: (1) API availability ≥ 99.9%, (2) p99 API latency ≤ 500ms for CRUD operations, (3) workflow execution success rate ≥ 99%. Use OTEL metrics as the data source. Implement error budget tracking with CloudWatch composite alarms. |
| **Evidence** | `server/src/main.ts` (/api/health endpoint), `server/src/otel/tracing.ts` (api.duration, api.hits metrics), no SLO files found |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Custom business metrics are published via OTEL: `users.concurrent` (login/logout based), `sessions.active`, `users.concurrent.active` (request-based, per-workspace), `sessions.concurrent.active` (per-workspace), `api.hits` (per-route), `api.duration` (per-route histogram). `server/src/otel/audit-metrics.ts` provides audit log metrics. `prom-client` dependency enables Prometheus metrics. `@bull-board/express` provides BullMQ job queue dashboards. `server/src/modules/metrices/` exists for additional metrics. |
| **Gap** | Good business metrics coverage for user activity and API performance. However, metrics are not systematically defined across all features (e.g., app creation rates, data source connection success rates, workflow execution metrics may be missing). |
| **Recommendation** | Extend business metrics to cover: app creation/deletion rates, data source connection success/failure rates, query execution latency by data source type, workflow completion rates, and plugin execution performance. Create CloudWatch dashboards grouping business and infrastructure metrics. |
| **Evidence** | `server/src/otel/tracing.ts` (custom metrics), `server/src/otel/audit-metrics.ts`, `server/package.json` (prom-client, @bull-board/*), `server/src/modules/metrices/` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No CloudWatch alarms in IaC. No anomaly detection configuration. Sentry integration exists (`@sentry/nestjs`, `@sentry/react`) for error tracking and notification. OTEL metrics are exported but no alerting rules are defined in the repository. Slack notifications are configured for CI/CD events (vulnerability scans, Docker builds) but not for runtime anomalies. ECS Container Insights is enabled (`containerInsights = "enabled"` on the cluster). |
| **Gap** | Static threshold alerting via Sentry for errors, but no anomaly detection on latency, error rates, or business metrics. No CloudWatch alarms despite having Container Insights enabled. Sentry captures errors but does not provide latency anomaly detection. |
| **Recommendation** | Create CloudWatch alarms for: (1) ECS CPU/memory utilization, (2) RDS connection count and latency, (3) ALB 5xx error rate, (4) API p99 latency via OTEL metrics. Enable CloudWatch anomaly detection on error rates and latency. Integrate alarms with SNS for PagerDuty/OpsGenie notification. |
| **Evidence** | `terraform/ECS/main.tf` (containerInsights enabled, no alarms), `server/package.json` (@sentry/nestjs), `server/src/otel/tracing.ts` (metrics export) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Rolling deployments configured: ECS service has `deployment_maximum_percent = 200` and `deployment_minimum_healthy_percent = 100` (rolling update). Kubernetes deployment uses `RollingUpdate` with `maxUnavailable: 1` and `maxSurge: 1`. Readiness probe configured (`/api/health`). No canary deployment. No blue/green deployment. No CodeDeploy. No Argo Rollouts. No feature flags. No traffic shifting. |
| **Gap** | Rolling deployments with health checks provide basic safety, but no canary or blue/green strategy exists. Regressions affect all users simultaneously during a rolling update — there is no window to catch issues with a subset of traffic. |
| **Recommendation** | Implement blue/green deployments using CodeDeploy for ECS or Argo Rollouts for EKS (per preferences). Start with 10% canary traffic for 5 minutes before full rollout. Add automated rollback on CloudWatch alarm breach. |
| **Evidence** | `terraform/ECS/main.tf` (deployment_maximum_percent=200), `deploy/kubernetes/deployment.yaml` (RollingUpdate strategy) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Unit tests (`npm --prefix server run test`) and e2e tests (`npm --prefix server run test:e2e`) run in CI. Cypress end-to-end test workflows exist: `cypress-appbuilder.yml`, `cypress-marketplace.yml`, `cypress-platform.yml`. CI job runs with a PostgreSQL service container for database integration. Tests use `@pollyjs` for HTTP recording/playback. `supertest` for API testing. `@nestjs/testing` for NestJS test utilities. Code coverage workflow exists (`code-coverage.yml`). |
| **Gap** | Integration tests exist for primary workflows, but CI is triggered only on labeled PRs (`run-ci` label), not on every push. Cypress tests run in separate workflows. Some gaps in consistent CI execution. |
| **Recommendation** | Run unit and e2e tests on every push to develop/main branches (not just labeled PRs). Integrate Cypress tests into the main CI pipeline or run them as a required check on PRs. Add contract tests for the PostgREST API boundary. |
| **Evidence** | `.github/workflows/ci.yml` (unit-test, e2e-test jobs), `.github/workflows/cypress-appbuilder.yml`, `.github/workflows/cypress-platform.yml`, `server/package.json` (test scripts) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbook files found in the repository (no markdown, YAML, or JSON runbooks). No SSM Automation documents. No Lambda-based remediation. No self-healing automation. No Step Functions for incident workflows. Sentry provides error notification. Slack notifications exist for CI/CD events (vulnerability scans, build status) but not for runtime incidents. No PagerDuty or OpsGenie integration detected. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation for common failure modes (e.g., restart unhealthy tasks, scale on high error rates, rotate compromised credentials). |
| **Recommendation** | Create runbooks for common incidents: (1) database connection failure, (2) high error rate, (3) task out-of-memory, (4) Redis connection failure. Implement SSM Automation documents for automated remediation. Add PagerDuty/OpsGenie integration for on-call alerting. |
| **Evidence** | No runbook files found, `server/package.json` (@sentry/nestjs), `.github/workflows/grype-slack-notify.yml` (Slack notification for scans only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CODEOWNERS defines ownership for `package.json`, `package-lock.json`, `module.ts` files, and migration directories across the monorepo. This establishes code review ownership. However, no observability-specific ownership exists — no per-service dashboards with named owners, no alarm ownership attribution, no SLO definitions with team attribution. The OTEL setup is centralized in `server/src/otel/` without per-module observability configuration. |
| **Gap** | Code ownership exists (CODEOWNERS), but observability ownership is absent. No one owns specific alarms, dashboards, or SLO targets. Monitoring is likely reactive and fragmented. |
| **Recommendation** | Define observability ownership per module/team. Create per-module CloudWatch dashboards. Assign alarm owners in alarm descriptions. As services are extracted, establish per-service SLO ownership. |
| **Evidence** | `CODEOWNERS` (code review ownership), `server/src/otel/tracing.ts` (centralized OTEL), no dashboard or alarm ownership files |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | EC2 Terraform has `Name` tags on a few resources: `TooljetAppServer` (EC2 instance), `TooljetVPC` (VPC), `TooljetPublicSubnet` (subnet), etc. However, ECS Terraform (`terraform/ECS/main.tf`) has **no tags** on the ECS cluster, task definition, ECS service, ALB, target group, RDS instance, security groups, subnets, VPC, or any other resource. No `default_tags` in the AWS provider. No Tag Policies, AWS Config rules, or SCPs for tag enforcement. No cost allocation tags. |
| **Gap** | No tags on ECS infrastructure resources. Only `Name` tags on EC2 resources with no cost allocation, ownership, or environment tags. No tagging standard, no enforcement, no cost attribution capability. |
| **Recommendation** | Add `default_tags` to the AWS provider in all Terraform modules with keys: `Environment`, `Project`, `Owner`, `CostCenter`. Add `required-tags` AWS Config rule. Enable cost allocation tags for billing analysis. Tag all existing resources. |
| **Evidence** | `terraform/ECS/main.tf` (no tags on resources), `terraform/EC2/ec2.tf` (Name tag only on EC2/VPC) |

## Learning Materials

The following learning resources correspond to the 2 triggered modernization pathways:

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1 | Root package — Node.js 22.15.1, npm 10.9.2 engine requirements |
| `server/package.json` | INF-Q3, INF-Q4, APP-Q1, APP-Q3, APP-Q4, SEC-Q3, SEC-Q4, OPS-Q1, OPS-Q3, OPS-Q4 | Server dependencies — NestJS 11.x, TypeScript 5.8, Temporal, BullMQ, OTEL, Sentry, auth libs |
| `frontend/package.json` | APP-Q1 | Frontend dependencies — React 18.2, Webpack 5 |
| `server/src/main.ts` | APP-Q5, SEC-Q3, OPS-Q2 | Application bootstrap — API versioning, middleware, auth setup, health endpoints |
| `server/ormconfig.ts` | APP-Q2, DATA-Q2, DATA-Q4 | TypeORM configuration — PostgreSQL connection, dual database config |
| `server/src/otel/tracing.ts` | OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4 | OpenTelemetry setup — tracing, metrics, custom business metrics |
| `server/src/otel/audit-metrics.ts` | SEC-Q1, OPS-Q3 | Audit log metrics via OTEL |
| `server/src/modules/workflows/` | INF-Q3, APP-Q4 | Temporal workflow module — controllers, services, processors |
| `server/src/modules/ai/` | Pathway: Move to AI | AI module — controller, service, cache, utilities |
| `server/src/modules/audit-logs/` | SEC-Q1 | Application-level audit logging module |
| `server/src/modules/auth/` | SEC-Q3, SEC-Q4 | Authentication module — JWT, SAML, OIDC |
| `server/src/modules/login-configs/` | SEC-Q4 | SSO and login configuration module |
| `server/src/modules/scim/` | SEC-Q4 | SCIM provisioning module |
| `server/src/modules/metrices/` | OPS-Q3 | Additional metrics module |
| `server/migrations/` | DATA-Q2, DATA-Q3, DATA-Q4 | 184 TypeORM migration files — schema evolution |
| `terraform/ECS/main.tf` | INF-Q1–Q11, SEC-Q1, SEC-Q2, SEC-Q5, OPS-Q4, OPS-Q5, OPS-Q9 | ECS infrastructure — Fargate, ALB, RDS, VPC, security groups, Redis sidecar |
| `terraform/ECS/variables.tf` | INF-Q9, SEC-Q5 | Terraform variables — AZ config, default credentials |
| `terraform/EC2/ec2.tf` | INF-Q1, INF-Q5, SEC-Q2, OPS-Q9 | EC2 deployment — instance, VPC, public subnet |
| `terraform/EC2/sg.tf` | INF-Q5 | EC2 security group — 0.0.0.0/0 on SSH, HTTP, HTTPS, 3000 |
| `docker-compose.yaml` | INF-Q2, DATA-Q3 | Local development — postgres:13, redis:6.2, PostgREST |
| `docker/ce-production.Dockerfile` | APP-Q2, SEC-Q6 | Production Docker image — multi-stage build, debian:12, non-root user, Oracle client |
| `deploy/helm/Chart.yaml` | INF-Q1, INF-Q2, DATA-Q3 | Helm chart — Bitnami PostgreSQL dependency v11.1.3 |
| `deploy/helm/values.yaml` | INF-Q7, SEC-Q5 | Helm values — HPA min=max=1, plaintext passwords |
| `deploy/kubernetes/deployment.yaml` | INF-Q1, INF-Q9, APP-Q6, OPS-Q5 | K8s deployment — replicas=2, RollingUpdate, readiness probe |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6 | CI pipeline — build, lint, unit tests, e2e tests |
| `.github/workflows/docker-release.yml` | INF-Q11 | Docker image builds on release — CE, EE, Cloud editions |
| `.github/workflows/vulnerability-ci.yml` | SEC-Q7 | Periodic npm audit for all directories |
| `.github/workflows/grype-slack-notify.yml` | SEC-Q6, SEC-Q7 | Weekly Docker image vulnerability scanning with Grype |
| `.github/workflows/license-compliance.yml` | SEC-Q7 | Package license compliance checking |
| `dependabot.yml` | SEC-Q7 | Daily npm dependency updates for server, frontend, plugins, marketplace |
| `CODEOWNERS` | OPS-Q8 | Code review ownership for package files, modules, migrations |
| `.env.example` | SEC-Q4, SEC-Q5 | Environment variable template — SSO config, placeholder secrets |
| `.nvmrc` | APP-Q1 | Node.js version pin — v22.15.1 |
| `SECURITY.md` | SEC-Q6 | Security policy and vulnerability reporting |
| `deploy/kubernetes/service.yaml` | APP-Q6 | Kubernetes ClusterIP service |
