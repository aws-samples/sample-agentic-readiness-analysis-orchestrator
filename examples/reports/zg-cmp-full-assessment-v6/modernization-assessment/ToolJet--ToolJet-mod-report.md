# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | ToolJet--ToolJet |
| **Date** | 2025-05-08 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, low-code, frontend |
| **Context** | Open-source low-code internal-tool builder. |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true |
| **Overall Score** | 2.31 / 4.0 |

**Archetype Justification**: The application owns two PostgreSQL databases (primary + ToolJet DB), exposes CRUD operations on apps, users, organizations, data sources, workflows, and AI conversations, and manages entity lifecycle state. Multiple write endpoints exist alongside reads. Classified as stateful-crud.

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 2.27 / 4.0 | 🟠 Needs Work | Needs Work |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.29 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.31 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (3+2+3+3+2+3+1+1+2+2+3) / 11 = 25/11 = 2.27
- APP: (3+2+3+3+2+3) / 6 = 16/6 = 2.67
- DATA: (2+3+3+3) / 4 = 11/4 = 2.75
- SEC: (1+2+3+3+2+3+2) / 7 = 16/7 = 2.29
- OPS: (3+1+1+1+2+2+1+1+2) / 9 = 14/9 = 1.56
- Overall: (2.27 + 2.67 + 2.75 + 2.29 + 1.56) / 5 = 11.54 / 5 = 2.31

### Classification

**Tier: Remediation Required**

This repo has 2 High findings, 19 Medium findings, 5 Low findings. The matched rule is: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. Under ARA rules, 1 High would be a blocker; under MOD rules, 1 High maps to Pilot-Ready and only 2+ High findings escalate to Remediation Required.

**Classification Consistency Check:** consistent (V5 Needs Work ≡ V6 Remediation Required)

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration found in IaC | No audit trail for forensic analysis or compliance |
| 2 | INF-Q7: Auto-Scaling | 1 | No auto-scaling configured; ECS service uses static desired_count=2 | Cannot respond to traffic spikes; over-provisioning during low demand |
| 3 | INF-Q8: Backup and Recovery | 1 | RDS has no backup_retention_period configured; defaults to 0 | Data loss risk with no recovery capability |
| 4 | OPS-Q2: SLO Definitions | 1 | No SLO definitions found anywhere in the repository | Cannot measure service quality or drive prioritization |
| 5 | OPS-Q3: Business Metrics | 1 | Only infrastructure metrics (OpenTelemetry); no business outcome metrics | No visibility into whether the system delivers business value |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). 29 GitHub Actions workflows provide comprehensive automation surface.
- **What it enables:** An agent that triggers deployments, checks build status, manages releases, and monitors pipeline health across the 29 workflows.
- **Additional steps:** Expose GitHub Actions API access to the agent; create a workflow dispatch interface for common operations.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repo. A full Docusaurus documentation site exists at `docs/` with extensive content.
- **What it enables:** A knowledge agent that indexes ToolJet's documentation and provides developers/users with natural-language answers about features, configuration, and troubleshooting.
- **Additional steps:** Index the `docs/` directory content and OpenAPI spec into a vector store for retrieval.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 3). TypeORM provides a centralized data access layer with 80+ entity models and clear schema definitions.
- **What it enables:** A natural language to SQL agent that enables operators to query application data (users, organizations, apps, workflows) without writing raw SQL.
- **Additional steps:** Generate a schema documentation from TypeORM entities; implement query guardrails to prevent destructive operations.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 3). Full OpenTelemetry instrumentation with traces, metrics, and custom gauges exists.
- **What it enables:** An agent that queries traces, correlates errors across services, and suggests root causes for production issues.
- **Additional steps:** Ensure OTLP exporter is configured to a queryable backend (e.g., AWS X-Ray, Grafana Tempo); expose trace query API to the agent.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=3, APP-Q3=3, APP-Q4=3. Primary trigger: APP-Q2 < 3 (monolith). |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=3 — compute already on ECS/Fargate and Kubernetes. Container definitions (14 Dockerfiles) exist. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=3 (minimal stored procedures). No commercial DB engines detected — PostgreSQL is already open source. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=2 (Redis self-managed as sidecar container). DATA-Q3=3 (version pinned but approaching considerations). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads (ETL, streaming pipelines, analytics jobs) detected. BullMQ is a job queue, not analytics infrastructure. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=2 (partial IaC coverage), OPS-Q5=2 (rolling deployments only), OPS-Q6=2 (tests not consistently in CI). |
| 7 | Move to AI | Not Triggered | — | — | AI/agent frameworks already present: AWS Bedrock, OpenAI, Anthropic, vector DBs (Pinecone, Qdrant, Weaviate), and internal AI module with agents. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a monolith (APP-Q2=2) — a single NestJS server deployment containing 50+ modules (auth, workflows, AI, data-queries, SCIM, licensing, encryption, etc.) with a shared PostgreSQL database. Modules have identifiable boundaries (NestJS module structure) but share database schemas via TypeORM with cross-module entity relationships and 80+ shared entities.

**Compute Model:**
Compute already runs on ECS Fargate (INF-Q1=3), so the container orchestration foundation exists. The gap is in architectural decomposition, not compute modernization.

**Recommended Decomposition Approach:**
Given the NestJS modular structure with identifiable module boundaries, the Strangler Fig (Parallel Track) approach is recommended. High-value extraction candidates:
- **Workflows service** — Already has Temporal.io integration (EE), BullMQ queues, dedicated processors. Natural extraction boundary.
- **AI service** — Separate entities, dedicated controllers, credit management. Low coupling to core CRUD.
- **ToolJet Database service** — Already uses a separate PostgreSQL instance and PostgREST.

**Representative AWS Services:** EKS (preferred per preferences), API Gateway, EventBridge, Step Functions, Aurora PostgreSQL.

**Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing for workflow state.

**Learning Resources:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
- Primary PostgreSQL: Managed via RDS in the ECS Terraform module (db.t3.micro, engine v16). However, RDS is configured single-AZ with no backup retention and skip_final_snapshot=true.
- Redis: Self-managed as a sidecar container in the ECS task definition. The `redis.tf` file has a commented-out MemoryDB cluster definition that was never activated.
- PostgREST: Runs as a sidecar container providing REST API over the ToolJet internal database.

**Gaps:**
- Redis runs as a sidecar container (not managed). Should migrate to Amazon ElastiCache or MemoryDB.
- RDS configuration lacks Multi-AZ, backup retention, and production-grade sizing.

**Recommended Targets (respecting preferences):**
- Redis → Amazon ElastiCache for Redis or MemoryDB for Redis (preferred: managed Redis with high availability)
- PostgreSQL → Aurora PostgreSQL (preferred per preferences) with Multi-AZ, automated backups, and PITR

**Representative AWS Services:** Aurora PostgreSQL, ElastiCache, MemoryDB, DMS for migration.

**Learning Resources:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=2):**
Terraform covers ECS cluster, VPC, ALB, RDS, and IAM roles but does NOT cover: CloudWatch alarms, backup plans, auto-scaling policies, Route 53, WAF, or operational resources. Kubernetes manifests are provided for deployment but lack HPA configuration, network policies, and monitoring resources. Significant infrastructure is implied to be manually created.

**Current CI/CD State (INF-Q11=3):**
29 GitHub Actions workflows provide strong automation for build, test, Docker image publishing, and vulnerability scanning. However, deployment to production environments appears to be manual/workflow_dispatch-triggered with limited automated rollback.

**Deployment Strategy Gaps (OPS-Q5=2):**
Kubernetes deployment uses `RollingUpdate` strategy with basic health checks. No canary or blue/green deployment configuration found. No traffic shifting or progressive delivery.

**Testing Gaps (OPS-Q6=2):**
Cypress e2e tests exist but are triggered by labels, not on every PR. Integration test execution is not consistent in the CI pipeline.

**Recommended DevOps Toolchain:**
- IaC expansion: Terraform modules for monitoring, alarms, backup plans, auto-scaling
- Deployment: EKS with ArgoCD or Flux for GitOps (preferred: eks per preferences)
- Progressive delivery: Argo Rollouts for canary deployments
- Testing: Automated integration test execution on every PR

**Representative AWS Services:** CodePipeline, CodeBuild, CloudFormation/CDK, X-Ray, CloudWatch.

**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

*(Included because APP-Q2 = 2 < 3)*

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2=2 — identifiable NestJS modules with coupling through shared DB. Team can sustain parallel development. | Medium to High | ✅ **Recommended.** The NestJS module structure provides natural extraction boundaries. |
| **Conditional / Adaptive** | If team capacity is limited. Containerization already done (ECS/K8s in use). Selectively extract high-value services. | Low to Medium | ✅ **Also viable** given containers are already in place. |
| **Big-Bang Rewrite** | Almost never appropriate for a working production system with 184 migrations and 50+ modules. | Very High | ⚠️ **Recommended against.** |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the monolith's TypeORM entity model | Every extraction — translate between monolith's shared entities and new service's domain model |
| **Saga Pattern** | Manage distributed transactions (e.g., app creation → permissions → audit log) | When extracting modules that participate in multi-step operations |
| **Event Sourcing** | Capture workflow state changes as events | Workflow service extraction — enables event-driven integration |
| **Hexagonal Architecture** | Clear boundaries in each new service | Every new service — ensures testability and infrastructure decoupling |

### Extraction Priority (based on assessment findings)

| Module | Coupling Level | Extraction Effort | Value |
|--------|---------------|-------------------|-------|
| Workflows | Low (separate queue, Temporal integration) | Medium | High — independent scaling of workflow execution |
| AI | Low (separate entities, credit system) | Low-Medium | Medium — AI features can scale independently |
| ToolJet Database | Low (separate DB instance, PostgREST) | Low | High — already architecturally separated |
| Auth/Session | Medium (shared user entities) | High | Medium — enables SSO/IdP as a service |

### Effort Estimation Factors

| Factor | Current Signal | Impact |
|--------|---------------|--------|
| Module boundaries | Clear NestJS module structure (50+ modules) | Lower effort — boundaries exist |
| Data coupling | Shared PostgreSQL with cross-entity relationships | Higher effort — DB separation needed |
| Stored procedures | None (all logic in application layer) | Lower effort |
| Communication patterns | Mix of sync HTTP + BullMQ async + Event Emitter | Medium — some async patterns already exist |
| CI/CD maturity | 29 workflows, Docker builds automated | Lower effort — pipeline foundation exists |
| Test coverage | Cypress e2e + unit tests exist | Medium — tests exist but coverage gaps |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary deployment targets use ECS Fargate (Terraform module) and Kubernetes (deployment manifests for generic K8s, AKS, GKE). The ECS Terraform creates a Fargate cluster with 2 tasks. Kubernetes manifests define deployments with 2 replicas. No raw EC2 instances for the application workload (EC2 Terraform modules exist as alternative deployment options for self-hosted users). |
| **Gap** | Mix of managed compute options provided but the ECS deployment bundles Redis as a sidecar container rather than using a managed service. |
| **Recommendation** | Migrate Redis from sidecar to Amazon ElastiCache. Standardize on EKS (preferred) as the primary container orchestration platform. |
| **Evidence** | `terraform/ECS/main.tf`, `deploy/kubernetes/deployment.yaml`, `docker/ce-production.Dockerfile` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | PostgreSQL is deployed via RDS in the ECS Terraform module (managed service), but configured single-AZ without Multi-AZ failover (`multi_az` not set). Redis runs as a self-managed sidecar container within the ECS task definition. The `redis.tf` file contains a commented-out MemoryDB cluster definition. |
| **Gap** | Redis is self-managed (sidecar container). RDS is managed but deployed single-AZ without Multi-AZ failover enabled. This is a mix of managed and self-managed with at least one production data store (Redis) self-hosted. |
| **Recommendation** | Enable Multi-AZ on RDS PostgreSQL. Migrate Redis to Amazon ElastiCache for Redis or MemoryDB with Multi-AZ. Uncomment and configure the MemoryDB resource in `redis.tf` or replace with ElastiCache. Consider Aurora PostgreSQL (preferred) for the primary database. |
| **Evidence** | `terraform/ECS/main.tf` (RDS without multi_az, Redis as container), `terraform/ECS/redis.tf` (commented-out MemoryDB) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Temporal.io is integrated for workflow orchestration (Enterprise Edition) with dedicated server configuration, PostgreSQL persistence backend, and SDK imports (`@temporalio/activity`, `@temporalio/client`, `@temporalio/worker`, `@temporalio/workflow` v1.11.6). Community Edition uses BullMQ with structured queue configuration, priority levels, retry policies, and configurable concurrency. |
| **Gap** | Temporal is EE-only; CE relies on BullMQ which is a job queue rather than a dedicated workflow orchestration service. Partial adoption — primary workflows use orchestration (EE) but CE workflows are queue-based. |
| **Recommendation** | For AWS deployment, consider AWS Step Functions as a managed alternative to self-hosted Temporal. This eliminates the need to manage Temporal server infrastructure. For CE, evaluate whether BullMQ workflow patterns could benefit from Step Functions for complex multi-step operations. |
| **Evidence** | `server/package.json` (Temporal dependencies), `docker/LTS/ee/temporal-server.yaml`, `server/src/modules/workflows/constants/queue-config.ts` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | BullMQ (Redis-based) provides managed job queuing with priority scheduling, exponential backoff retry, and job retention policies. NestJS Event Emitter provides internal event bus for workflow triggers and webhooks. WebSocket + Yjs enables real-time collaboration. However, all messaging infrastructure uses self-managed Redis (sidecar container) as the backing store rather than a fully managed AWS messaging service. |
| **Gap** | Messaging is functional but relies on self-managed Redis rather than managed messaging services (SQS, EventBridge). The event-driven patterns exist but are backed by infrastructure that requires operational management. |
| **Recommendation** | For cross-service state changes and notifications, consider Amazon EventBridge (preferred per context). For job queues, evaluate whether migrating BullMQ to SQS or keeping it on managed ElastiCache is more appropriate given the existing BullMQ patterns work well. Migrate the Redis backing store to ElastiCache at minimum. |
| **Evidence** | `server/src/modules/workflows/constants/queue-config.ts`, `server/package.json` (bullmq, @nestjs/event-emitter), `docker-compose.yaml` (redis:6.2 service) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | VPC is configured with a custom CIDR (`10.0.0.0/16`) and two subnets. Security groups implement some segmentation: RDS only accessible from task SG, task ports restricted to LB SG. However, both subnets are PUBLIC (`map_public_ip_on_launch = true`), and the LB SG allows `0.0.0.0/0` on ports 80 and 443. There are no private subnets, no NAT gateway, and no VPC endpoints. |
| **Gap** | Services deployed in public subnets with public IPs. No private subnet tier for application and database workloads. Missing VPC endpoints for AWS service access. LB security group is appropriately open but application tasks should be in private subnets. |
| **Recommendation** | Restructure VPC with private subnets for ECS tasks and RDS; public subnets only for ALB. Add NAT gateway for outbound internet access from private subnets. Add VPC endpoints for ECR, S3, and Secrets Manager. Consider VPC Lattice for service-to-service communication in a microservices architecture. |
| **Evidence** | `terraform/ECS/main.tf` (public subnets with map_public_ip_on_launch=true, no private subnets, 0.0.0.0/0 on LB SG) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | ALB is configured as the entry point in the ECS Terraform with health check at `/api/health` and 900s grace period. Kubernetes service uses AWS LoadBalancer type with SSL termination annotation. Basic routing and health checks are present. |
| **Gap** | ALB provides basic routing and health checks but no API Gateway-level features: no throttling, no request validation, no API-level authentication at the gateway. Rate limiting is handled at application level (NestJS Throttler) rather than at the edge. |
| **Recommendation** | Consider API Gateway (preferred per preferences) in front of the ALB for throttling, request validation, and API key management. Alternatively, implement WAF on the ALB for basic protection. |
| **Evidence** | `terraform/ECS/main.tf` (ALB resource, health check), `deploy/kubernetes/service.yaml` (LoadBalancer with SSL annotation) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling is configured anywhere in the infrastructure. ECS service has a static `desired_count = 2`. Kubernetes deployment specifies `replicas: 2` with no HPA. Helm values.yaml shows HPA min/max both set to 1 (effectively disabled). No DynamoDB or Aurora auto-scaling (not applicable — PostgreSQL RDS). No Lambda concurrency configuration. |
| **Gap** | All capacity is statically provisioned with no ability to scale up during traffic spikes or scale down during low demand. |
| **Recommendation** | Configure ECS Application Auto Scaling with target tracking (CPU and custom metrics). For EKS deployment, configure Horizontal Pod Autoscaler with appropriate min/max and custom metrics (request count, queue depth). Consider Karpenter for EKS node auto-scaling. |
| **Evidence** | `terraform/ECS/main.tf` (desired_count=2, no aws_appautoscaling_*), `deploy/kubernetes/deployment.yaml` (replicas: 2, no HPA), `deploy/helm/values.yaml` (HPA min=max=1) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | RDS instance in `terraform/ECS/main.tf` has no `backup_retention_period` configured (defaults to 0 — no automated backups). `skip_final_snapshot = true` means no final backup on deletion. No `aws_backup_plan` resources found. No PITR configuration. Redis (sidecar) has no persistence or backup strategy. |
| **Gap** | No backup configuration for any data store. RDS will not retain backups. Redis data is ephemeral (container restart loses all data). No documented restore procedures. |
| **Recommendation** | Set `backup_retention_period = 7` (minimum) on RDS with PITR enabled. Remove `skip_final_snapshot = true` for production. Create an AWS Backup plan covering RDS. Migrate Redis to ElastiCache with backup enabled. Consider cross-region backup replication for disaster recovery. |
| **Evidence** | `terraform/ECS/main.tf` (no backup_retention_period, skip_final_snapshot=true) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECS service runs 2 tasks and the VPC has 2 subnets in different AZs (us-east-1c, us-east-1d), so compute spans 2 AZs. However, RDS is single-AZ (no `multi_az = true`). Redis runs as a sidecar (no HA). Kubernetes deployment specifies 2 replicas (can span AZs depending on node topology). |
| **Gap** | Compute spans multiple AZs but the primary database (RDS) is single-AZ. A single AZ failure would take down the database. Redis as a sidecar provides no independent HA. |
| **Recommendation** | Enable `multi_az = true` on RDS. Migrate Redis to ElastiCache with Multi-AZ automatic failover. For EKS, ensure pod anti-affinity rules spread replicas across AZs. |
| **Evidence** | `terraform/ECS/main.tf` (2 subnets in different AZs, RDS without multi_az), `terraform/ECS/variables.tf` (subnet AZ variables) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Terraform covers: ECS cluster, VPC, ALB, RDS, IAM roles, security groups, CloudWatch log groups. Kubernetes manifests cover: deployments, services, ingress (GKE). Helm chart covers: deployment, HPA, service, secrets. However, NOT covered in IaC: CloudWatch alarms, backup plans, auto-scaling policies, Route 53, WAF, SNS topics, monitoring dashboards, or any operational/DR resources. |
| **Gap** | Partial IaC — compute and networking are defined but operational resources (monitoring, alerting, backup, scaling) are missing. Significant manual infrastructure likely exists for production environments. |
| **Recommendation** | Expand Terraform modules to cover: CloudWatch alarms (error rates, latency p99), AWS Backup plans, auto-scaling policies, Route 53 health checks, and WAF rules. Create a monitoring-as-code module. |
| **Evidence** | `terraform/ECS/main.tf` (compute, VPC, ALB, RDS defined), absence of aws_cloudwatch_metric_alarm, aws_backup_plan, aws_appautoscaling_*, aws_route53_*, aws_wafv2_* resources |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | 29 GitHub Actions workflows provide comprehensive CI/CD automation: CI build/lint/test (`ci.yml`), Docker image builds on release (`docker-release.yml`), vulnerability scanning (`vulnerability-ci.yml`), staging deployment (`deploy-to-stage.yml`), Cypress e2e tests, code coverage, docs deployment, and marketplace plugin deployment. Build, test, and Docker publish are fully automated. |
| **Gap** | Production deployment appears to require manual workflow_dispatch triggers (`deploy-to-stage.yml` requires manual dispatch). IaC changes (Terraform) have no automated apply pipeline — likely applied manually. No automated rollback mechanism visible in workflows. |
| **Recommendation** | Add automated production deployment pipeline triggered by release events with approval gates. Implement Terraform plan/apply pipeline with PR-based plan preview and automated apply on merge. Add automated rollback on deployment failure (health check driven). |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/docker-release.yml`, `.github/workflows/deploy-to-stage.yml` (workflow_dispatch), `.github/workflows/vulnerability-ci.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeScript (Node.js 22.15.1) with NestJS 11.1.3 backend and React (JavaScript/JSX) frontend. Node 22 is current LTS. NestJS 11 is the latest major version. TypeORM 0.3.24 is current. However, the frontend uses JavaScript/JSX rather than TypeScript, and the build tooling uses Webpack rather than more modern alternatives (Vite, esbuild). |
| **Gap** | Language and framework are modern (Node 22, NestJS 11 — Score 4 territory). However, the frontend codebase is JavaScript/JSX (not TypeScript), which limits type safety and refactoring confidence across the full stack. This is a minor gap that lands the score at 3. |
| **Recommendation** | Consider migrating the frontend to TypeScript for full-stack type safety. Evaluate Vite as a Webpack replacement for faster builds. These are optional improvements — the current stack has first-class AWS SDK coverage and mature cloud-native tooling. |
| **Evidence** | `.nvmrc` (v22.15.1), `server/package.json` (NestJS 11.1.3, TypeORM 0.3.24), `frontend/package.json` (React, Webpack), `.js`/`.jsx` files in frontend |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit (one NestJS server process) containing 50+ modules with shared PostgreSQL database via TypeORM. Modules have identifiable boundaries (NestJS module system with separate directories, controllers, services) but share database schemas through cross-entity relationships (80+ entities in a shared entity directory). PostgREST and Redis run as sidecars but are infrastructure, not independent services. |
| **Gap** | Monolith with identifiable modules but shared database schemas, direct cross-module entity access via TypeORM, and single deployment unit. All 50+ modules deploy together — no independent scaling or deployment. |
| **Recommendation** | Begin Strangler Fig decomposition starting with the most loosely-coupled modules: Workflows (already has separate queue infrastructure), AI (separate entities and credit system), and ToolJet Database (already uses separate DB instance). See Decomposition Strategy section. |
| **Evidence** | `server/src/main.ts` (single NestJS app), `server/src/modules/` (50+ modules), `server/src/entities/` (80+ shared entities), `docker/ce-production.Dockerfile` (single server build), `server/ormconfig.ts` (shared DB connection) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application uses a mix of synchronous HTTP (NestJS controllers for API requests) and asynchronous patterns: BullMQ for workflow execution queues with priority scheduling, NestJS Event Emitter for internal event bus (workflow triggers, webhooks), and WebSocket for real-time collaboration. Async is used for key workflows (job execution, event propagation). |
| **Gap** | Async patterns exist for workflow execution and events but most module-to-module communication within the monolith is synchronous (direct service injection and method calls). Cross-service state propagation does not use managed messaging (relies on in-process events and Redis-backed queues). |
| **Recommendation** | As services are extracted, implement EventBridge (preferred) for cross-service event propagation. Current BullMQ patterns provide a solid foundation — ensure extracted services communicate via events rather than synchronous HTTP where state changes are involved. |
| **Evidence** | `server/src/modules/workflows/constants/queue-config.ts` (BullMQ async), `server/package.json` (@nestjs/event-emitter, bullmq, ws), `server/src/modules/auth/controller.ts` (sync HTTP) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Workflow executions (potentially long-running) are handled asynchronously via BullMQ with configurable timeout (default 60s via WORKFLOW_TIMEOUT_SECONDS), priority levels, retry policies, and Temporal.io for durable orchestration (EE). Jobs are submitted to the queue and processed by dedicated workers with concurrency control. |
| **Gap** | Most long-running operations are handled asynchronously through BullMQ/Temporal. However, some operations may still block — data query execution against external sources (plugins) appears to be synchronous within the request lifecycle based on the architecture, and the 60s default timeout suggests awareness of long-running operations. |
| **Recommendation** | Audit plugin data query execution for operations that may exceed 30 seconds (e.g., large database queries against external sources). Consider implementing a polling/callback pattern for heavy data queries. The existing BullMQ infrastructure provides the foundation for this. |
| **Evidence** | `server/src/modules/workflows/constants/queue-config.ts` (WORKFLOW_TIMEOUT 60s, async processing), `server/package.json` (@temporalio/* for durable workflows) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | NestJS URI versioning is enabled in `main.ts` (`app.enableVersioning({ type: VersioningType.URI, defaultVersion: VERSION_NEUTRAL })`). This provides the framework for versioning. However, the default version is `VERSION_NEUTRAL` (no version prefix required), and examination of controllers shows no `@Version()` decorators or `/v1/`, `/v2/` patterns in use. The SCIM API has an OpenAPI spec but no version path. |
| **Gap** | Versioning framework is configured but not actively used — all endpoints operate at VERSION_NEUTRAL with no explicit version paths. Breaking changes would affect all consumers simultaneously. |
| **Recommendation** | Apply `@Version('1')` or `@Version('2')` decorators to controllers as APIs evolve. Establish a versioning policy for breaking changes. Consider versioning the public API surface first (SCIM, external integrations) while internal APIs remain neutral. |
| **Evidence** | `server/src/main.ts` (enableVersioning with VERSION_NEUTRAL default), `server/src/modules/auth/controller.ts` (no @Version decorator), `docs/openapi/scim/index.openapi.yaml` (no version in paths) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Service endpoints are configured via environment variables (`PG_HOST`, `REDIS_HOST`, `PGRST_HOST`, `TOOLJET_DB_HOST`). Kubernetes service resources provide DNS-based service discovery within the cluster. The Kubernetes deployment references services by environment variables populated from secrets. No hard-coded service endpoints in application code — all external connections are configurable. |
| **Gap** | Environment variables for endpoints but no dynamic service discovery (no AWS Cloud Map, no Consul, no Istio service mesh). Kubernetes provides cluster-internal DNS but this is basic service resolution, not a full service registry. |
| **Recommendation** | For EKS deployment (preferred), implement AWS Cloud Map for service discovery as services are extracted from the monolith. Consider a service mesh (AWS App Mesh or Istio) for advanced traffic management, observability, and mTLS between services. |
| **Evidence** | `.env.example` (PG_HOST, REDIS_HOST, PGRST_HOST variables), `deploy/kubernetes/deployment.yaml` (env vars from secrets), `deploy/kubernetes/service.yaml` (ClusterIP/LoadBalancer services) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application handles file uploads and assets (profile images, app icons, imported data) but no S3 configuration is found in IaC or environment variables. Files appear to be stored locally or via the configured `TOOLJET_HOST` path. The Dockerfile creates an `/assets` directory served by Express static middleware. No Textract or document parsing integration found. An S3 plugin exists for connecting to external S3 buckets as a data source, but this is for user data queries, not application storage. |
| **Gap** | Unstructured data (files, assets) stored on local filesystem or container volume rather than managed object storage. No automated parsing or extraction pipeline. |
| **Recommendation** | Migrate file storage to Amazon S3. Implement presigned URLs for direct upload/download. Consider S3 lifecycle policies for cost optimization. If document parsing is needed for AI features, integrate Amazon Textract. |
| **Evidence** | `server/src/main.ts` (express.static for /assets), `docker/ce-production.Dockerfile` (local filesystem), absence of aws_s3_bucket in Terraform, `plugins/packages/s3/` (S3 as data source connector, not storage backend) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeORM provides a centralized ORM layer with consistent entity definitions (80+ entities), repository pattern usage, and unified connection configuration (`ormconfig.ts`). Two separate database connections are clearly defined (primary PostgreSQL + ToolJet DB). Modules access data through TypeORM repositories with consistent patterns. |
| **Gap** | Mostly centralized through TypeORM but some modules may perform direct query building or raw SQL for complex operations. The dual-database architecture (primary + ToolJet DB) creates two separate access layers. PostgREST adds a third access path (REST over PostgreSQL). |
| **Recommendation** | Maintain TypeORM as the primary data access layer. As services are extracted, ensure each service owns its data through its own repository layer. Document which entities belong to which future service boundary to prepare for decomposition. |
| **Evidence** | `server/ormconfig.ts` (centralized config with connection pooling), `server/src/entities/` (80+ entities), `server/src/modules/*/repository.ts` (repository pattern) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | PostgreSQL 16 is explicitly pinned in the ECS Terraform (`engine_version` on RDS). PostgreSQL 16 is current and not approaching EOL. Docker Compose uses `postgres:13` for development, which is approaching EOL (November 2025). Redis 6.2 in Docker Compose is approaching EOL. |
| **Gap** | Production engine version (PG 16) is current but development environment uses older versions (PG 13, Redis 6.2). No documented version-update procedure. Development/production version mismatch could mask compatibility issues. |
| **Recommendation** | Update Docker Compose to PostgreSQL 16 to match production. Update Redis to 7.x in development. Document a version-update procedure covering downtime windows and rollback for production upgrades. |
| **Evidence** | `terraform/ECS/main.tf` (PostgreSQL 16), `docker-compose.yaml` (postgres:13, redis:6.2) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | All business logic resides in the application layer (NestJS services). TypeORM migrations use standard DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX). No stored procedures, triggers, or proprietary SQL constructs detected in migration files. The `pgcrypto` extension is used for UUID generation (standard PostgreSQL extension, not proprietary). PostgREST uses PostgreSQL functions for its configuration but these are infrastructure-level, not business logic. |
| **Gap** | Minimal stored procedures — PostgREST uses `postgrest.pre_config` function for JWT/schema configuration (infrastructure-level). This is not business logic coupling but does create a dependency on PostgreSQL-specific features. |
| **Recommendation** | Maintain the current approach of keeping business logic in the application layer. When considering database migration (e.g., to Aurora PostgreSQL), the PostgREST pre_config function will need to be accounted for but is not a significant migration blocker. |
| **Evidence** | `server/migrations/` (DDL-only migrations), `server/src/entities/` (TypeORM entity definitions), `.env.example` (PGRST_DB_PRE_CONFIG=postgrest.pre_config) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration found in any Terraform module. No `aws_cloudtrail` resource. No audit logging infrastructure defined in IaC. The application has an `audit-logs` module in the server (`server/src/modules/audit-logs/`) which provides application-level audit logging, but there is no AWS-level infrastructure audit trail (CloudTrail) or immutable log storage configuration. |
| **Gap** | No CloudTrail or equivalent infrastructure audit logging. Application-level audit logs exist but without CloudTrail, AWS API actions (IAM changes, resource modifications, security events) are not captured. No immutable log storage (S3 Object Lock). |
| **Recommendation** | Add `aws_cloudtrail` resource to Terraform with log file validation enabled. Configure S3 bucket with Object Lock for immutable log storage. Enable CloudTrail for all management events and data events on sensitive resources (S3, RDS). Integrate with CloudWatch Logs for real-time alerting. |
| **Evidence** | Absence of `aws_cloudtrail` in all Terraform modules, `server/src/modules/audit-logs/` (application-level only) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No KMS key configuration found in Terraform. RDS instance has no explicit `storage_encrypted` or `kms_key_id` parameter (defaults vary by instance class — db.t3.micro may not default to encrypted). No S3 bucket encryption configuration. However, the application implements column-level AES-256-GCM encryption for sensitive data via the encryption module (`LOCKBOX_MASTER_KEY` with HKDF key derivation). |
| **Gap** | Mix of encryption with coverage gaps. Application-level column encryption exists (AES-256-GCM) for sensitive fields, but infrastructure-level encryption at rest (RDS storage encryption, EBS encryption) is not explicitly configured in IaC. No customer-managed KMS keys. |
| **Recommendation** | Add `storage_encrypted = true` and a customer-managed KMS key to RDS. Create KMS keys for each sensitive data store. Ensure all EBS volumes and S3 buckets use KMS encryption. The existing application-level encryption (LOCKBOX_MASTER_KEY) provides defense-in-depth but does not replace infrastructure encryption. |
| **Evidence** | `terraform/ECS/main.tf` (RDS without storage_encrypted/kms_key_id), `server/src/modules/encryption/service.ts` (AES-256-GCM application encryption), `.env.example` (LOCKBOX_MASTER_KEY) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | All API endpoints use JWT token-based authentication via Passport JWT strategy. Guards are applied at the module/controller level (90+ guard files). OAuth2 (Google, GitHub), SAML, OIDC, and LDAP are supported as identity providers. The `/api/health` endpoint is intentionally public (excluded from auth via pathsToExclude). SCIM API has its own bearer token auth. |
| **Gap** | Token-based auth on all external endpoints. Internal endpoints are protected by the same JWT guards. However, API Gateway-level throttling and validation are not present (handled at application level via NestJS Throttler). No WAF or API Gateway authorizer — auth is entirely application-side. |
| **Recommendation** | Authentication implementation is solid. Consider adding API Gateway (preferred) with throttling and request validation at the edge as an additional layer. The application-level auth (JWT + guards) provides the core security; edge-level protection adds defense-in-depth. |
| **Evidence** | `server/src/modules/session/jwt/jwt.strategy.ts`, `server/src/modules/auth/controller.ts` (@UseGuards), `server/src/main.ts` (pathsToExclude for health), CODEOWNERS guards references |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application integrates with centralized identity providers: Google OAuth, GitHub OAuth, SAML, OIDC (OpenID Connect), and LDAP. SSO is supported for multi-workspace configurations. Environment variables (`SSO_GOOGLE_OAUTH2_CLIENT_ID`, `SSO_GIT_OAUTH2_CLIENT_ID`, OIDC configuration) enable federation. |
| **Gap** | Application uses centralized IdP for most flows (OAuth2, SAML, OIDC). However, it also maintains its own local authentication (email/password with bcrypt) as a primary auth path. Some legacy auth paths remain alongside IdP integration. No AWS Cognito integration — IdP federation is application-managed. |
| **Recommendation** | Consider AWS Cognito as a centralized identity layer to consolidate the multiple IdP integrations (Google, GitHub, SAML, OIDC, LDAP) into a single managed service. This would simplify IdP management and provide consistent token issuance across all providers. |
| **Evidence** | `.env.example` (SSO_*, GOOGLE_CLIENT_*, SSO_GIT_OAUTH2_*), `server/src/modules/auth/oauth/util-services/` (saml.service.ts, oidc-auth.service.ts, ldap.service.ts) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The ECS Terraform references `tooljet-secret` in AWS Secrets Manager for runtime secrets. Kubernetes deployment uses secretKeyRef for database credentials and keys. However, the Terraform `variables.tf` contains default values for sensitive variables (`PG_PASS = "postgres"`, `PG_USER = "postgres"`), and `.env.example` contains placeholder secrets (`LOCKBOX_MASTER_KEY=0000000000000000000000000000000000000000000000000000000000000000`). The `deploy/ec2/ee/.env` file exists in the repository (though likely a template). No rotation configuration found. |
| **Gap** | Some secrets are in Secrets Manager (ECS deployment) and Kubernetes Secrets (K8s deployment), but Terraform variables have hardcoded default credentials (`postgres/postgres`). No automated rotation configured. Environment variable templates committed to the repo contain placeholder values (not real secrets, but the pattern suggests production may use env vars without rotation). |
| **Recommendation** | Remove default credential values from Terraform variables (use `sensitive = true` and no defaults). Implement secrets rotation via AWS Secrets Manager rotation Lambda for database credentials. Ensure all production credentials flow through Secrets Manager, not env vars. Add `sensitive = true` to all credential variables in Terraform. |
| **Evidence** | `terraform/ECS/variables.tf` (PG_PASS default="postgres"), `terraform/ECS/main.tf` (references to tooljet-secret), `deploy/kubernetes/deployment.yaml` (secretKeyRef), `.env.example` (placeholder LOCKBOX_MASTER_KEY) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Docker images use a multi-stage build with `debian:12` base (current stable). Node.js 22.15.1 is current LTS. The `vulnerability-ci.yml` workflow runs weekly npm audit across all packages and creates PRs for fixes. Dependabot is configured for daily updates on `/server`, `/frontend`, `/plugins`, `/marketplace`. Grype scanning with Slack notifications exists. |
| **Gap** | Dependency vulnerability scanning is comprehensive (npm audit + Dependabot + Grype). However, no container image scanning (ECR scanning or Trivy in CI), no SSM Patch Manager (using Fargate — N/A for OS patching), and no hardened base image (using generic debian:12 rather than a minimal/hardened image like distroless or Alpine). |
| **Recommendation** | Add container image scanning to the CI pipeline (Amazon ECR image scanning or Trivy/Grype on the built Docker image). Consider migrating the production Dockerfile base from `debian:12` to a minimal image (distroless or Alpine) to reduce attack surface. Fargate handles OS patching automatically, which is a strength. |
| **Evidence** | `docker/ce-production.Dockerfile` (debian:12 base, node 22.15.1), `.github/workflows/vulnerability-ci.yml` (npm audit), `dependabot.yml` (daily updates) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependency scanning is configured: `vulnerability-ci.yml` runs weekly npm audit across all packages, Dependabot runs daily for 4 directories, and Grype scanning sends Slack notifications. However, no SAST tool (SonarQube, Semgrep, CodeGuru) is configured in the CI pipeline. No container scanning step in the Docker build workflow. |
| **Gap** | Dependency scanning is active (npm audit + Dependabot) but no SAST tool for code-level vulnerability detection. No container image scanning in the Docker release pipeline. The pipeline has security validation for dependencies but not for application code patterns. |
| **Recommendation** | Add SAST scanning (Amazon CodeGuru Reviewer, Semgrep, or SonarQube) to the CI pipeline. Add container image scanning (ECR scanning or Trivy) to the Docker release workflow. Configure security gates that block PRs with critical SAST findings. |
| **Evidence** | `.github/workflows/vulnerability-ci.yml` (npm audit only), `.github/workflows/docker-release.yml` (no image scanning step), `dependabot.yml` (dependency updates), absence of SAST tool configuration |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Full OpenTelemetry instrumentation exists in `server/src/otel/tracing.ts` with OTLP HTTP trace and metric exporters. Instrumentations cover HTTP, Express, NestJS, PostgreSQL, and Pino. Custom metrics include api.hits, api.duration, users.concurrent, and sessions.active. Trace IDs are propagated through the HTTP/Express/NestJS instrumentation chain. |
| **Gap** | Tracing on the primary NestJS server is comprehensive. However, tracing is only enabled for EE/Cloud editions (`ENABLE_OTEL=true`). No tracing on PostgREST sidecar. No evidence of trace propagation to external services (Redis, downstream data sources). Single-service tracing rather than distributed cross-service propagation. |
| **Recommendation** | Enable OTEL for all editions (CE included). Ensure trace context propagation to Redis (ioredis instrumentation exists in OTEL ecosystem) and PostgREST. As services are extracted, ensure W3C Trace Context headers propagate across service boundaries. Consider AWS X-Ray as the tracing backend for native AWS integration. |
| **Evidence** | `server/src/otel/tracing.ts` (full OTEL setup, EE/Cloud only), `server/package.json` (@opentelemetry/* dependencies) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking. No SLI definitions. Basic CloudWatch log groups are configured (30-day retention in ECS Terraform) but no formal service level definitions. Custom metrics exist (api.hits, api.duration) but are not tied to SLO targets. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. Custom metrics (API duration, concurrent users) exist but have no target thresholds or error budget tracking. |
| **Recommendation** | Define SLOs for critical user journeys: app builder load time (p99 latency), data query execution success rate, workflow execution success rate, API availability. Implement error budget tracking using the existing OpenTelemetry metrics as SLI data sources. Consider Amazon CloudWatch SLO monitoring. |
| **Evidence** | Absence of SLO definition files, `server/src/otel/tracing.ts` (metrics exist but no SLO targets), `terraform/ECS/main.tf` (CloudWatch logs only, no alarms) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | OpenTelemetry custom metrics track infrastructure-adjacent data: api.hits (request count), api.duration (latency), users.concurrent, sessions.active. These are valuable but are infrastructure/usage metrics, not business outcome metrics. No metrics for: apps created, queries executed successfully, workflow completion rates, user onboarding success, or feature adoption rates. |
| **Gap** | Only infrastructure and usage metrics. No business outcome metrics that measure whether the platform delivers value to its users (e.g., internal tools built, queries serving data, workflow automations running). |
| **Recommendation** | Add business outcome metrics: apps_created_total, data_queries_executed_success/failure, workflows_completed/failed, user_onboarding_completed, active_apps_serving_users. Publish these alongside infrastructure metrics to CloudWatch or the OTLP exporter. Create dashboards combining business and infrastructure views. |
| **Evidence** | `server/src/otel/tracing.ts` (only api.hits, api.duration, users.concurrent, sessions.active) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudWatch alarms defined in Terraform. No alerting configuration found in IaC or application config. No anomaly detection setup. Sentry is configured for error tracking (`SENTRY_DNS` env var, `@sentry/nestjs` dependency) which provides error alerting, but this is reactive error reporting, not proactive threshold or anomaly-based alerting. |
| **Gap** | No alerting configured beyond Sentry error reporting. No CloudWatch alarms on error rates, latency, or resource utilization. No anomaly detection for degradation patterns. |
| **Recommendation** | Add CloudWatch alarms for: API error rate > 5%, API p99 latency > 5s, ECS task failures, RDS connections > 80%, Redis memory utilization. Enable CloudWatch anomaly detection on error rates and latency for critical API paths. Integrate alarms with SNS → PagerDuty/OpsGenie for on-call notification. |
| **Evidence** | Absence of aws_cloudwatch_metric_alarm in Terraform, `.env.example` (SENTRY_DNS for error tracking only), `server/package.json` (@sentry/nestjs) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes deployment uses `RollingUpdate` strategy with `maxUnavailable: 1, maxSurge: 1` and readiness probe (httpGet /api/health). ECS service in Terraform has no explicit deployment configuration (defaults to rolling update). No canary, blue/green, or traffic-shifting configuration found. |
| **Gap** | Rolling deployments with basic health checks but no progressive delivery. No canary releases, no blue/green deployment, no traffic shifting. A bad deployment affects all users as soon as the rolling update completes. |
| **Recommendation** | Implement canary deployments using Argo Rollouts (for EKS) or AWS CodeDeploy with ECS blue/green deployment. Add automated rollback on health check failure. Consider feature flags (LaunchDarkly or AWS AppConfig) for gradual feature rollout independent of deployment. |
| **Evidence** | `deploy/kubernetes/deployment.yaml` (RollingUpdate strategy), `terraform/ECS/main.tf` (no deployment_controller config) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Cypress e2e tests exist covering app builder, marketplace, and platform (`cypress-appbuilder.yml`, `cypress-marketplace.yml`, `cypress-platform.yml`). However, these are triggered by PR labels and workflow_dispatch — not run automatically on every PR. The CI workflow (`ci.yml`) runs unit tests and linting but Cypress tests require explicit label triggers. |
| **Gap** | Integration/e2e tests exist but are not run consistently in CI. Tests require manual label triggering rather than running automatically on every PR. This means PRs can merge without integration test validation. |
| **Recommendation** | Configure Cypress tests to run automatically on every PR targeting main/develop branches (remove the label requirement for critical test suites). Run a core smoke test suite on every PR and the full suite on merge to develop. Consider parallelizing Cypress tests for faster feedback. |
| **Evidence** | `.github/workflows/cypress-appbuilder.yml`, `.github/workflows/ci.yml` (unit tests only in automatic flow), `cypress-tests/` directory |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found in the repository. No Systems Manager Automation documents. No self-healing automation. No incident response workflows or playbooks. Graceful shutdown is implemented in `main.ts` (SIGINT/SIGTERM handling) but this is application lifecycle, not incident response. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No documented procedures for common failure scenarios (database connection failures, Redis unavailability, high memory usage, deployment rollback). |
| **Recommendation** | Create runbooks for common incidents: database failover procedure, Redis cache clear/reconnect, high memory debugging, deployment rollback steps. Implement as SSM Automation documents for AWS-hosted deployments. Consider self-healing patterns: auto-restart on OOM, circuit breakers for external data sources. |
| **Evidence** | Absence of runbook files, absence of SSM Automation documents, `server/src/main.ts` (graceful shutdown only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS file exists but only covers package.json files, module.ts files, and migrations — no observability assets are owned. No per-service dashboards defined in IaC. No alarms with named owners. No team attribution on monitoring resources. OpenTelemetry metrics are defined but with no ownership assignment. |
| **Gap** | No observability ownership. Monitoring is reactive and fragmented. No dashboards, no alarm ownership, no team attribution. CODEOWNERS does not reference any observability configuration. |
| **Recommendation** | Extend CODEOWNERS to cover observability assets (Terraform alarm definitions, dashboard configurations). Create per-module dashboards with named owners. Assign alarm ownership to specific teams/individuals. Define on-call rotation ownership for critical alerts. |
| **Evidence** | `CODEOWNERS` (only covers package.json, module.ts, migrations), absence of dashboard definitions, absence of alarm ownership |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The ECS Terraform defines resources with a `Name` tag on the ECS cluster (`containerInsights` setting references the cluster name) but no consistent tagging strategy. No `default_tags` in the Terraform provider configuration. No cost allocation tags. No environment, team, or service tags on resources. Kubernetes manifests use labels for selector matching but not for cost/ownership attribution. |
| **Gap** | Some resources have Name tags but no consistent tagging standard. No cost allocation, ownership, or environment tags. No tag enforcement via Config rules or Tag Policies. |
| **Recommendation** | Add `default_tags` to the Terraform AWS provider with standard keys: Environment, Service, Team, CostCenter. Add corresponding tags to Kubernetes resources. Implement AWS Config rules for required-tags compliance. Activate cost allocation tags in the billing console. |
| **Evidence** | `terraform/ECS/main.tf` (minimal tagging, no default_tags), `deploy/kubernetes/deployment.yaml` (component label only) |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

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
| `terraform/ECS/main.tf` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, SEC-Q1, SEC-Q2, OPS-Q2, OPS-Q4, OPS-Q9 | ECS Fargate deployment, VPC, ALB, RDS, security groups |
| `terraform/ECS/variables.tf` | INF-Q2, SEC-Q5 | Variable definitions with default credentials |
| `terraform/ECS/redis.tf` | INF-Q2 | Commented-out MemoryDB cluster definition |
| `deploy/kubernetes/deployment.yaml` | INF-Q1, INF-Q7, APP-Q6, OPS-Q5, OPS-Q9 | K8s deployment with 2 replicas, RollingUpdate |
| `deploy/kubernetes/service.yaml` | INF-Q6, APP-Q6 | LoadBalancer service with SSL annotation |
| `server/src/main.ts` | APP-Q2, APP-Q5, SEC-Q3, OPS-Q7 | NestJS application bootstrap, versioning, middleware |
| `server/ormconfig.ts` | APP-Q2, DATA-Q2 | TypeORM configuration for dual PostgreSQL connections |
| `server/src/otel/tracing.ts` | OPS-Q1, OPS-Q2, OPS-Q3 | OpenTelemetry instrumentation and custom metrics |
| `server/package.json` | APP-Q1, APP-Q3, APP-Q4, INF-Q3, INF-Q4, OPS-Q1, SEC-Q6 | NestJS 11, TypeORM, BullMQ, Temporal, OTEL dependencies |
| `server/src/modules/workflows/constants/queue-config.ts` | INF-Q3, INF-Q4, APP-Q3, APP-Q4 | BullMQ queue configuration with priorities and retry |
| `server/src/modules/auth/controller.ts` | SEC-Q3, APP-Q5 | JWT-guarded auth endpoints |
| `.env.example` | SEC-Q5, APP-Q6, DATA-Q3, SEC-Q4 | Environment variable template with placeholders |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6 | CI pipeline with build, lint, test |
| `.github/workflows/vulnerability-ci.yml` | SEC-Q6, SEC-Q7 | Weekly npm audit vulnerability scanning |
| `.github/workflows/docker-release.yml` | INF-Q11, SEC-Q7 | Docker image build and publish on release |
| `.github/workflows/deploy-to-stage.yml` | INF-Q11, OPS-Q5 | Manual staging deployment workflow |
| `docker/ce-production.Dockerfile` | APP-Q1, APP-Q2, SEC-Q6 | Multi-stage Docker build, debian:12 base |
| `docker-compose.yaml` | DATA-Q3, INF-Q4 | Development environment with postgres:13, redis:6.2 |
| `dependabot.yml` | SEC-Q6, SEC-Q7 | Daily dependency updates for 4 directories |
| `CODEOWNERS` | OPS-Q8 | Ownership for package.json and migrations only |
| `server/src/entities/` | APP-Q2, DATA-Q2, DATA-Q4 | 80+ TypeORM entity definitions |
| `server/migrations/` | DATA-Q4 | 184 schema migrations (DDL only) |
| `docs/openapi/scim/index.openapi.yaml` | APP-Q5 | SCIM 2.0 API specification |
| `server/src/modules/ai/controller.ts` | Move to AI pathway | AI module with stub endpoints (CE) |
| `marketplace/plugins/aws-bedrock/` | Move to AI pathway | AWS Bedrock marketplace plugin |
| `marketplace/plugins/pinecone/` | Move to AI pathway | Pinecone vector DB plugin |
| `deploy/helm/values.yaml` | INF-Q7 | HPA min=max=1 (disabled) |
