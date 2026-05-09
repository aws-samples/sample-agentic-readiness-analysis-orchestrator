# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | FlowiseAI--Flowise |
| **Date** | 2025-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, ai, llm |
| **Context** | Low-code UI for building LLM flows and agents. |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true |
| **Overall Score** | 2.14 / 4.0 |
| **Classification Tier** | 🟠 Remediation Required |
| **Rule Matched** | 2-11 High → Remediation Required |

**Classification Rationale:** This repository has 7 High findings, 22 Medium findings, and 5 Low findings. The matched classification rule is "2-11 High → Remediation Required." Note: MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. Under ARA rules, 1 High would trigger "Remediation Required"; under MOD rules, 1 High maps to "Pilot-Ready" instead, reflecting that a single modernization gap does not block all forward progress.

**Archetype Justification**: The application owns persistent state via TypeORM entities (20 entities with CRUD operations — ChatFlow, ChatMessage, Credential, etc.), exposes a full REST API surface with create/update/delete endpoints, and manages user-specific data (API keys, credentials, workspaces). Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work | Needs Work |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.14 / 4.0** | **🟠 Needs Work** | — |

**Scoring Notes:**
- INF: (1+1+2+2+1+2+1+1+2+1+2) / 11 = 16/11 = 1.45
- APP: (4+2+2+3+2+1) / 6 = 14/6 = 2.33
- DATA: (2+3+4+4) / 4 = 13/4 = 3.25
- SEC: (1+2+3+3+2+1+2) / 7 = 14/7 = 2.00
- OPS: (3+1+2+2+1+2+1+2+1) / 9 = 15/9 = 1.67
- Overall: (1.45 + 2.33 + 3.25 + 2.00 + 1.67) / 5 = 10.70/5 = 2.14

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute — Docker Compose only, no ECS/EKS/Lambda | Blocks container orchestration, auto-scaling, and HA |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — zero Terraform, CDK, or CloudFormation | Cannot reproduce environments, no disaster recovery |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging in IaC | No forensic analysis capability, compliance gap |
| 4 | OPS-Q5: Deployment Strategy | 1 | No blue/green or canary — direct-to-production via manual dispatch | Regressions affect all users immediately |
| 5 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined | Services potentially exposed without isolation |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 2) and structured JSON responses detected. Swagger/OpenAPI spec at `packages/api-documentation/src/yml/swagger.yml` with 56 route modules.
- **What it enables:** An agent that discovers and invokes Flowise API endpoints as tools — enabling natural language orchestration of flow creation, chatbot management, and document store operations.
- **Additional steps:** The Swagger spec needs to be fully populated (currently a partial spec). All 56 route modules should have OpenAPI annotations.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in repository — README, i18n docs, SECURITY.md, extensive .env.example documentation, and inline code documentation.
- **What it enables:** A knowledge agent that indexes Flowise documentation and provides developer assistance for configuration, deployment, and component development.
- **Additional steps:** Consolidate documentation into a structured corpus. The existing docs are scattered across multiple locations.
- **Effort:** Low

### Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 3). Winston structured JSON logging with OpenTelemetry traces and Prometheus metrics.
- **What it enables:** An agent that queries logs, traces incidents across the LLM execution pipeline, and suggests root causes for failed predictions or slow chatflow executions.
- **Additional steps:** Ensure OTel trace propagation covers all async BullMQ worker flows (currently unclear if queue operations are traced).
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2 |
| 2 | Move to Containers | Not Triggered | — | — | Dockerfiles exist; compute already containerized (Docker) — contextual guard blocks |
| 3 | Move to Open Source | Not Triggered | — | — | No commercial DB engines detected; already uses PostgreSQL/MySQL/SQLite |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed databases in Docker Compose) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing/analytics workloads detected; BullMQ is task queue not analytics |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=1, OPS-Q6=2 |
| 7 | Move to AI | Not Triggered | — | — | AI/agent frameworks extensively present (LangChain, Bedrock, OpenAI, etc.) — this IS an AI platform |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a modular monolith (APP-Q2=2) with identifiable packages (server, components, ui, agentflow) but shared database schemas, a single deployment unit, and cross-package dependencies. All compute runs as Docker containers without managed orchestration (INF-Q1=1). Inter-service communication is primarily synchronous HTTP within the monolith (APP-Q3=2).

**Recommended Decomposition Approach:** Strangler Fig pattern — extract high-value services (prediction engine, document store, credential management) into independent EKS pods while keeping the monolith as the primary entry point. The existing BullMQ worker pattern demonstrates the architecture already supports separated concerns.

**Representative AWS Services:** EKS (preferred per steering context), API Gateway, EventBridge, Aurora PostgreSQL, ElastiCache (Redis), S3.

**Recommended Patterns:**
- Anti-corruption Layer between extracted services and monolith
- Event Sourcing for chatflow execution state
- Saga pattern for multi-step prediction workflows

**Links:** [AWS Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** The application supports PostgreSQL, MySQL, MariaDB, and SQLite. In Docker Compose deployment, the database runs as a self-managed container or local SQLite file. No managed database infrastructure is defined in IaC (because no IaC exists).

**Engine Versions and EOL Status:** No version pinning detected in Docker Compose for the database — the application connects to whatever is configured via environment variables. TypeORM migrations exist for all 4 database types.

**Data Access Patterns:** TypeORM provides a centralized data access layer (DATA-Q2=3). 20 entities with migration support make managed database migration straightforward.

**Recommended Managed Database Targets (respecting preferences):**
- **Aurora PostgreSQL** (preferred) — full PostgreSQL compatibility with automatic failover, backups, and scaling
- **DynamoDB** (preferred) — for key-value patterns like API keys, variables, and session storage
- **ElastiCache for Redis** — for BullMQ queue and rate limiting (already Redis-dependent)

**Representative AWS Services:** Aurora PostgreSQL, DynamoDB, ElastiCache, AWS DMS

**Links:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** Zero IaC exists (INF-Q10=1). All infrastructure is manually created. Docker Compose files provide application orchestration but not cloud infrastructure provisioning.

**Current CI/CD State:** GitHub Actions workflows exist for build/test (automated on push/PR) and Docker image publishing (manual dispatch to ECR/DockerHub). Deployment to production is manual — no automated deployment pipeline with stages (INF-Q11=2).

**Deployment Strategy Gaps:** No blue/green, canary, or rolling deployment strategy (OPS-Q5=1). Container images are pushed to ECR manually and presumably deployed via manual steps.

**Testing Gaps:** Unit tests exist (Jest) with some E2E (Cypress), but integration tests for critical workflows are limited and not consistently run in CI (OPS-Q6=2).

**Recommended DevOps Toolchain (respecting preferences — prefer EKS, avoid Lambda):**
- **Terraform or CDK** for IaC — define VPC, EKS cluster, Aurora, ElastiCache, S3
- **GitHub Actions + ArgoCD** for GitOps deployment to EKS
- **EKS with Helm charts** for container orchestration
- **AWS CodeDeploy** (or Argo Rollouts) for canary/blue-green deployments

**Representative AWS Services:** EKS, ECR, CodePipeline, CodeBuild, CloudFormation/CDK

**Links:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

*(Included because APP-Q2 = 2)*

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2 = 2 — identifiable packages with coupling. The monorepo already has clear package boundaries (server, components, agentflow). | Medium to High | ✅ **Recommended.** Extract prediction/execution engine, document store, and credential vault as independent services behind API Gateway. |
| **Conditional / Adaptive** | Limited team capacity. Containerize as-is on EKS first, then selectively extract. | Low to Medium | ✅ **Recommended as Phase 1.** Deploy the monolith on EKS first, then extract services based on scaling needs. |
| **Big-Bang Rewrite** | Only if monolith is unmaintainable. | Very High | ⚠️ **Not recommended.** The monolith is functional with clear module boundaries. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from monolith data model | Every extraction — especially the prediction engine which currently shares TypeORM entities |
| **Saga Pattern** | Multi-step prediction workflows (document upload → chunking → embedding → storage) | When extracting document processing pipeline |
| **Event Sourcing** | Chatflow execution state tracking | When extracting execution/prediction service |
| **Hexagonal Architecture** | Clean boundaries on new services | Every new service — especially credential vault and document store |

### Effort Estimation Factors

| Factor | Signal | Assessment |
|--------|--------|------------|
| Module boundaries | Clear package structure (server/components/ui/agentflow) | Low effort — boundaries exist |
| Data coupling | Shared TypeORM entities, single database | Medium effort — need schema separation |
| Stored procedures | None (DATA-Q4=4) | Low effort — all logic in application layer |
| Communication patterns | Primarily synchronous HTTP within monolith | Medium effort — need to add async patterns |
| CI/CD maturity | Basic CI exists; no deployment automation | Medium effort — need to build deployment pipeline first |
| Test coverage | Limited integration tests | Medium effort — extraction without tests is risky |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs as Docker containers orchestrated by Docker Compose. No ECS, EKS, Lambda, or Fargate resources are defined. The application is deployed via `docker/docker-compose.yml` (single service) and `docker/worker/docker-compose.yml` (worker). The ECR workflow (`docker-image-ecr.yml`) pushes images but does not deploy them to managed compute. |
| **Gap** | No managed container orchestration or serverless compute. Docker Compose provides no auto-scaling, no self-healing, and no managed deployment lifecycle. |
| **Recommendation** | Deploy on EKS (preferred per steering context) with separate Deployments for the main server and BullMQ worker. Use Fargate for burstable worker pods. Define Helm charts for both workloads. |
| **Evidence** | `docker/docker-compose.yml`, `docker/worker/docker-compose.yml`, `.github/workflows/docker-image-ecr.yml`, `Dockerfile`, `docker/worker/Dockerfile` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application supports PostgreSQL, MySQL, MariaDB, and SQLite via environment variables. Docker Compose references database connection via env vars but does not define a managed database service — the database is either a self-managed container, a local SQLite file, or an externally provisioned instance. No IaC defines any `aws_rds_*`, `aws_dynamodb_*`, or managed database resources. Redis for BullMQ is also self-managed. |
| **Gap** | All databases are self-managed with no automated failover, backup, or scaling. |
| **Recommendation** | Migrate to Aurora PostgreSQL (preferred) for the primary database with Multi-AZ failover. Use ElastiCache for Redis (BullMQ and rate limiting). Define infrastructure via Terraform/CDK with automated backups and PITR. |
| **Evidence** | `packages/server/src/DataSource.ts`, `packages/server/.env.example` (DATABASE_* vars), `docker/docker-compose.yml` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses BullMQ as a task queue for long-running operations (document processing, predictions) with a dedicated worker architecture. This is a basic orchestration pattern — job enqueue/dequeue with retries — but not a dedicated workflow orchestration service. Multi-step operations like document processing (upload → chunk → embed → store) are coordinated through sequential code logic within the worker, not via Step Functions or similar. |
| **Gap** | Multi-step workflows are hardcoded as sequential application logic within BullMQ job handlers. No visual workflow management, no cross-service state tracking, no retry policies beyond BullMQ's built-in retry. |
| **Recommendation** | Evaluate AWS Step Functions for the document processing pipeline and chatflow execution workflows. Step Functions would provide visual monitoring, error handling, and retry logic for the multi-step AI operations that are currently buried in BullMQ handlers. |
| **Evidence** | `packages/server/src/index.ts` (QueueManager), `docker/worker/Dockerfile`, `packages/server/.env.example` (MODE=queue, WORKER_CONCURRENCY) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | BullMQ (Redis-backed) provides async job processing between the main server and worker. However, Redis is self-managed (not ElastiCache or Amazon MQ). The architecture uses queues for prediction offloading and long-running tasks — this is appropriate for a stateful-crud service with heavy background processing. No managed messaging service (SQS, SNS, EventBridge) is in use. |
| **Gap** | Self-managed Redis for messaging. No managed messaging service for cross-service events or notifications. Redis failure would take down the entire queue system without managed failover. |
| **Recommendation** | Migrate to ElastiCache for Redis (preferred) for BullMQ backing. For event-driven patterns (chatflow completion events, webhook notifications), introduce EventBridge (preferred per steering context). Consider SQS for decoupling document processing stages. |
| **Evidence** | `packages/server/src/utils/rateLimit.ts` (Redis/ioredis), `packages/server/.env.example` (REDIS_*, MODE=queue), `packages/server/package.json` (bullmq dependency) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation is defined anywhere in the repository. No IaC exists to provision networking infrastructure. The Docker Compose files expose port 3000 directly. The application has CORS configuration and rate limiting at the application layer, but no network-level isolation. |
| **Gap** | No network segmentation. Services are not deployed in private subnets with least-privilege security groups. No VPC endpoints or PrivateLink. |
| **Recommendation** | Define a VPC with private subnets for EKS worker nodes, Aurora, and ElastiCache. Use public subnets only for ALB/API Gateway. Configure security groups with least-privilege rules. Use VPC endpoints for S3 and Secrets Manager access. |
| **Evidence** | `docker/docker-compose.yml` (port exposure), absence of any `.tf`, CloudFormation, or CDK files defining VPC resources |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application exposes its API directly via Express.js on port 3000. Docker Compose health checks hit `http://localhost:${PORT}/api/v1/ping` directly. There is no API Gateway, ALB, or CloudFront in front of the service. The application implements its own rate limiting (`packages/server/src/utils/rateLimit.ts`) and auth middleware, but lacks a managed entry point with throttling, request validation, and WAF. |
| **Gap** | No managed entry point. The Express server is directly exposed without a load balancer, API Gateway, or CDN providing edge security and traffic management. |
| **Recommendation** | Deploy API Gateway (preferred per steering context) in front of the EKS service with throttling, request validation, and WAF. Alternatively, use an ALB with AWS WAF for the initial migration. Configure CloudFront for the React UI static assets. |
| **Evidence** | `docker/docker-compose.yml` (direct port exposure), `packages/server/src/utils/rateLimit.ts` (application-level rate limiting) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling is configured. Docker Compose runs a single instance of each service with no scaling mechanism. The BullMQ worker has a `WORKER_CONCURRENCY` setting (for in-process concurrency) but no horizontal scaling. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or Kubernetes HPA configurations exist. |
| **Gap** | All capacity is statically provisioned. The system cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | On EKS: configure HPA (Horizontal Pod Autoscaler) for both main server and worker deployments based on CPU, memory, and custom metrics (queue depth for workers, request rate for server). Configure Aurora auto-scaling for read replicas. |
| **Evidence** | `docker/docker-compose.yml` (single instance), `packages/server/.env.example` (WORKER_CONCURRENCY — process-level only), absence of any scaling configuration |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning for blob storage, no PITR configuration. The SQLite default database has no backup mechanism. For PostgreSQL deployments, backups would depend entirely on manual configuration outside the repository. |
| **Gap** | No automated backups for any data store. A data loss event would be unrecoverable. |
| **Recommendation** | Aurora PostgreSQL provides automated backups and PITR by default. For S3 blob storage, enable versioning. Define an AWS Backup plan for cross-service backup governance. Document and test restore procedures. |
| **Evidence** | Absence of any backup configuration in IaC, Docker Compose, or application config; `packages/server/.env.example` (no backup-related settings) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application architecture supports multi-instance deployment (main + worker split via BullMQ), and the Docker images are pushed to ECR for potential multi-AZ deployment. However, no actual Multi-AZ configuration is defined. Docker Compose runs single instances. The architecture is designed to be stateless at the server layer (shared database, Redis for state), which would support multi-AZ if properly deployed. |
| **Gap** | No actual multi-AZ deployment configuration. Single-instance Docker Compose means a single point of failure. Database, Redis, and application are all SPOF. |
| **Recommendation** | Deploy on EKS across 2+ AZs. Use Aurora Multi-AZ for database HA. Use ElastiCache Multi-AZ for Redis HA. Configure ALB with cross-zone load balancing. |
| **Evidence** | `docker/docker-compose.yml` (single instance), `Dockerfile`, `docker/worker/Dockerfile` (stateless worker design supports HA) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure is defined in IaC. No Terraform files, no CDK stacks, no CloudFormation templates, no Helm charts, no Kustomize configurations exist in the repository. All infrastructure is created manually or via Docker Compose for local development. |
| **Gap** | 0% IaC coverage. Infrastructure changes are manual, non-reproducible, and undocumented. No disaster recovery capability from code. |
| **Recommendation** | Create Terraform modules (or CDK stacks) defining: VPC/networking, EKS cluster, Aurora PostgreSQL, ElastiCache Redis, S3 buckets, API Gateway, IAM roles, CloudWatch alarms. Start with a single environment and use Terraform workspaces or CDK stages for multi-environment. |
| **Evidence** | Absence of any `.tf`, `.tfvars`, `cdk.json`, `template.yaml`, `Chart.yaml`, or `kustomization.yaml` files in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions workflows provide automated build and test on push/PR (`main.yml`: install, lint, build, test:coverage, Cypress E2E). Docker image builds are automated but deployment is manual dispatch only (`docker-image-ecr.yml` uses `workflow_dispatch`). There is no automated deployment pipeline — images are pushed to ECR but not automatically deployed to any environment. |
| **Gap** | Build is automated but deployment is manual. No continuous delivery pipeline with staging → production progression. No automated rollback. |
| **Recommendation** | Extend GitHub Actions (or adopt CodePipeline) with automated deployment stages: build → deploy-to-staging → integration-test → deploy-to-production. Implement ArgoCD for GitOps deployment to EKS with automated rollback on health check failure. |
| **Evidence** | `.github/workflows/main.yml` (automated build/test), `.github/workflows/docker-image-ecr.yml` (manual dispatch deployment) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application is 100% TypeScript/JavaScript running on Node.js v20.19.2 (current LTS). Uses modern frameworks: Express 4.x, React 18, Vite, TypeORM, BullMQ. Dependencies include current AWS SDK v3 (`@aws-sdk/client-s3`, `@aws-sdk/client-secrets-manager`). TypeScript provides type safety. The ecosystem has first-class AWS SDK coverage and mature cloud-native tooling. |
| **Gap** | N/A — language/runtime, framework, and SDK are all modern and current. |
| **Recommendation** | N/A — no action needed. Continue tracking Node.js LTS releases (currently on v20, v22 LTS available). |
| **Evidence** | `.nvmrc` (v20.19.2), `packages/server/package.json` (TypeScript, Express 4, AWS SDK v3), `packages/ui/package.json` (React 18, Vite) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a monolith with identifiable modules. The monorepo has clear package boundaries (`server`, `components`, `ui`, `agentflow`, `api-documentation`) managed by pnpm workspaces + Turborepo. However, it deploys as a single unit (one Docker image, one database, one server process). The `server` package contains 40+ route modules, 40+ controllers, and 20 shared TypeORM entities in a single database schema. The worker is a second instance of the same codebase running in queue mode — not a separate service. |
| **Gap** | Single deployable unit with shared database schema. All controllers access the same TypeORM entities. No independent scaling of sub-domains (predictions, document processing, auth). Cross-module coupling through shared entities. |
| **Recommendation** | Apply Strangler Fig pattern to extract high-value services: (1) Prediction/execution engine (handles LLM calls, heaviest compute), (2) Document store service (chunking, embedding — already uses async via BullMQ), (3) Credential vault (security-sensitive, independent lifecycle). Keep the UI and main API as the monolith shell that proxies to extracted services. |
| **Evidence** | `packages/server/src/routes/` (56 route modules in single server), `packages/server/src/database/entities/` (20 shared entities), `Dockerfile` (single image), `docker/docker-compose.yml` (single service) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is primarily synchronous HTTP. All API endpoints respond synchronously. BullMQ provides async for prediction offloading (MODE=queue), but this is optional and runs within the same codebase. There is no event-driven communication between distinct services. Server-Sent Events (SSEStreamer) provides streaming responses to clients but is not inter-service async. Rate limiting uses Redis pub/sub for cross-instance coordination. |
| **Gap** | Inter-component communication is primarily synchronous within the monolith. The BullMQ queue pattern exists but is intra-application (same codebase, same database). No event-driven patterns for state changes (e.g., chatflow created → notify → index). |
| **Recommendation** | For the stateful-crud archetype, introduce managed messaging (EventBridge preferred) for cross-service state propagation once services are extracted. Key flows: chatflow execution completion → event → analytics/audit; document upload → event → processing pipeline; credential rotation → event → dependent flows. |
| **Evidence** | `packages/server/src/index.ts` (SSEStreamer, QueueManager), `packages/server/src/utils/rateLimit.ts` (Redis pub/sub), `packages/server/.env.example` (MODE=queue) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application handles long-running operations (LLM predictions, document processing, embedding generation) via BullMQ queue offloading with dedicated worker processes. The worker architecture (`docker/worker/Dockerfile`) is specifically designed for long-running tasks with 8GB heap allocation. Clients receive streaming responses via SSE for real-time predictions. Job status can be tracked via the BullMQ dashboard (configurable via `ENABLE_BULLMQ_DASHBOARD`). |
| **Gap** | Most long-running operations are async via BullMQ; however, some prediction paths may still be synchronous when not in queue mode (`MODE` defaults to non-queue). Status polling for queued jobs is available but not universally applied. |
| **Recommendation** | Ensure all prediction paths default to async with status callbacks. Consider exposing a standardized job status API (e.g., `/api/v1/executions/{id}/status`) for all async operations. |
| **Evidence** | `docker/worker/Dockerfile` (NODE_OPTIONS=--max-old-space-size=8192), `packages/server/.env.example` (MODE=queue, WORKER_CONCURRENCY), `packages/server/src/index.ts` (QueueManager, SSEStreamer) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The API uses a `/api/v1/` URL prefix applied at the Express app level (`this.app.use('/api/v1', flowiseApiV1Router)`). All 56 route modules are mounted under this prefix. However, only one version (`v1`) exists — there is no `v2` or migration strategy. The Swagger spec documents the API but does not include versioning deprecation policies. |
| **Gap** | Single version (`v1`) with no evidence of backward compatibility guarantees, deprecation policy, or migration path for breaking changes. Versioning scheme exists but is not actively used for API evolution. |
| **Recommendation** | Document a versioning policy (when to increment versions, deprecation timeline). When breaking changes are needed, create `/api/v2/` routes alongside v1 with a documented migration window. Consider API Gateway versioning stages for production deployment. |
| **Evidence** | `packages/server/src/routes/index.ts` (v1 router mount), `docker/docker-compose.yml` (health check: `/api/v1/ping`), `packages/api-documentation/src/yml/swagger.yml` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists. All service endpoints (database, Redis, S3, external APIs) are configured via environment variables with hard-coded values. There is no Consul, AWS Cloud Map, Kubernetes DNS, or API catalog. The application is a single deployable unit, so internal service discovery is less critical, but external service resolution is entirely static. |
| **Gap** | All service endpoints are hard-coded in environment variables. No dynamic service discovery for database, Redis, or any downstream service. |
| **Recommendation** | When deployed on EKS, leverage Kubernetes DNS for internal service discovery. For external AWS services, use VPC endpoints with IAM-based resolution. Consider AWS Cloud Map if extracting to microservices. |
| **Evidence** | `packages/server/.env.example` (DATABASE_HOST, REDIS_HOST — static env vars), `packages/server/src/DataSource.ts` (reads host from env), absence of any service discovery configuration |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application supports S3 for blob/file storage (`STORAGE_TYPE=s3` with full S3 configuration). Document stores process PDFs, images, and other unstructured data. However, the default storage is local filesystem (`STORAGE_TYPE=local`). The document processing pipeline (chunking, embedding) handles unstructured data but there is no parsing pipeline using Textract or similar AWS services — parsing is done via application-level libraries (Puppeteer, pdf-parse, csv-parse). |
| **Gap** | Default is local filesystem storage. S3 is supported but optional. No managed parsing pipeline (Textract, Comprehend) — all parsing is in-application via Node.js libraries. |
| **Recommendation** | Default to S3 storage in production deployment IaC. Evaluate AWS Textract for document parsing and Amazon Comprehend for entity extraction to offload from application compute. The existing document store architecture would benefit from managed parsing services. |
| **Evidence** | `packages/server/.env.example` (STORAGE_TYPE=local|s3|gcs|azure, S3_STORAGE_*), `packages/components/` (document loaders with in-app parsing) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeORM provides a centralized data access layer with 20 well-defined entities, repository pattern, and migration support for 4 database types. The server package uses consistent TypeORM repositories throughout controllers and services. Some direct database queries exist for performance-critical operations (e.g., complex joins in chatflow queries), but the pattern is predominantly centralized. |
| **Gap** | Mostly centralized but some direct query patterns exist alongside TypeORM repositories. The components package has its own database connections for vector stores and memory backends (MongoDB, Redis, DynamoDB) that are outside the main TypeORM layer. |
| **Recommendation** | Maintain TypeORM as the primary data access layer. For vector store and memory backends in the components package, standardize the connection management pattern. When decomposing services, each service should own its data access layer independently. |
| **Evidence** | `packages/server/src/DataSource.ts` (TypeORM data source factory), `packages/server/src/database/entities/` (20 entities), `packages/server/src/database/migrations/` (4 DB types) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application does not pin specific database engine versions — it uses TypeORM which is engine-agnostic and connects to whatever PostgreSQL/MySQL/MariaDB version is provided via environment variables. No engines at or past EOL are embedded in the application. The Node.js runtime (v20.19.2) is current LTS. TypeORM supports all current PostgreSQL (12-16+), MySQL (5.7-8.x), and MariaDB (10.x+) versions. |
| **Gap** | N/A — no engine version pinning issues detected. The application is database-engine-agnostic by design. |
| **Recommendation** | When deploying to Aurora PostgreSQL, pin the engine version in IaC and document the upgrade procedure. Aurora provides managed engine upgrades with minimal downtime. |
| **Evidence** | `packages/server/src/DataSource.ts` (no version pinning — connects via env vars), `packages/server/package.json` (typeorm latest) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist anywhere in the codebase. All business logic resides in the TypeScript application layer. Database migrations use standard DDL (CREATE TABLE, ALTER TABLE) with no procedural SQL. TypeORM handles all query generation. |
| **Gap** | N/A — all business logic is in the application layer. |
| **Recommendation** | N/A — the clean separation between application logic and database schema makes database migration straightforward. |
| **Evidence** | `packages/server/src/database/migrations/` (all migrations are standard DDL), search for CREATE PROCEDURE/TRIGGER/FUNCTION returned zero results |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging infrastructure is defined. The application has request logging via Winston (server, error, request loggers) and optional S3 log streaming, but there is no infrastructure-level audit trail. No `aws_cloudtrail` resource exists (no IaC at all). Application-level logs track requests but not infrastructure actions or API calls to AWS services. |
| **Gap** | No infrastructure audit logging. No immutable log storage. No ability to trace administrative actions or forensic analysis after security incidents. |
| **Recommendation** | Enable CloudTrail in the AWS account with log file validation and S3 Object Lock for immutability. Configure CloudTrail to log all management events and S3 data events for sensitive buckets. Define in IaC alongside the infrastructure. |
| **Evidence** | Absence of any CloudTrail configuration, absence of IaC; `packages/server/src/utils/logger.ts` (application-level logging only) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application encrypts credentials at the application layer using `crypto-js` with a configurable secret key (stored locally or in AWS Secrets Manager). However, no infrastructure-level encryption at rest is configured — no KMS keys defined, no S3 bucket encryption policy, no RDS encryption configuration (because no IaC exists). The application-level encryption protects credential values in the database but does not constitute infrastructure-level encryption at rest. |
| **Gap** | No KMS configuration. No S3 bucket encryption policy. No database encryption at rest. Application-level encryption exists but infrastructure encryption is absent. |
| **Recommendation** | When defining IaC: configure customer-managed KMS keys for Aurora (storage encryption), S3 (SSE-KMS), and ElastiCache (at-rest encryption). Enable default encryption on all data stores. The existing application-level credential encryption can remain as defense-in-depth. |
| **Evidence** | `packages/server/.env.example` (SECRETKEY_STORAGE_TYPE, FLOWISE_SECRETKEY_OVERWRITE), `packages/server/package.json` (crypto-js dependency), absence of KMS or encryption IaC |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application implements JWT-based authentication with access and refresh tokens, Passport.js strategies (local, JWT, OAuth2, SSO), API key validation, and session management. Auth middleware protects API endpoints. The system supports multiple auth providers (Auth0, GitHub, Google, OpenID Connect). Some endpoints are intentionally public (predictions API for embedded chatbots) with rate limiting. |
| **Gap** | Auth exists at the application layer but there is no API Gateway authorizer providing a defense-in-depth layer. Intentionally public endpoints rely solely on application-level rate limiting without WAF or API Gateway throttling. |
| **Recommendation** | When deploying API Gateway, configure JWT authorizers for protected endpoints and usage plans with throttling for public endpoints. Layer WAF rules for additional protection on public prediction APIs. |
| **Evidence** | `packages/server/src/enterprise/middleware/passport/` (Passport strategies), `packages/server/.env.example` (JWT_*, AUTH parameters), `packages/server/src/utils/validateKey.ts`, `packages/server/src/utils/rateLimit.ts` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application integrates with external identity providers: Auth0, GitHub OAuth, Google OAuth 2.0, and generic OpenID Connect. SSO is supported via the enterprise module (`packages/server/src/enterprise/sso/`). The application can federate with centralized IdPs. However, the primary auth flow is still application-managed (local username/password with bcrypt). |
| **Gap** | SSO and external IdP integration exist for enterprise users, but the default auth path is self-managed (local user database). No Cognito integration for standardized AWS identity management. |
| **Recommendation** | For AWS deployment, consider Cognito User Pool as the identity provider — it provides built-in SSO, MFA, and integrates with API Gateway authorizers. The existing Passport.js OIDC strategy can connect to Cognito. |
| **Evidence** | `packages/server/src/enterprise/sso/`, `packages/server/src/enterprise/middleware/passport/` (Auth0, GitHub, Google, OIDC strategies), `packages/server/.env.example` (JWT configuration) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application supports AWS Secrets Manager for encryption key storage (`SECRETKEY_STORAGE_TYPE=aws`). However, database credentials, Redis passwords, S3 access keys, SMTP passwords, and other secrets are configured via environment variables (`.env.example` shows `DATABASE_PASSWORD`, `REDIS_PASSWORD`, `S3_STORAGE_SECRET_ACCESS_KEY`, `SMTP_PASSWORD`). No automated rotation is configured. The `.env.example` files are committed (as templates without values), but the secret management pattern relies on plain environment variables for most production credentials. |
| **Gap** | Most production credentials are in environment variables without rotation. Only the encryption master key supports Secrets Manager. Database password, Redis password, S3 keys, and SMTP credentials are all plain env vars. |
| **Recommendation** | Migrate all production secrets to AWS Secrets Manager with rotation: database credentials (Aurora supports Secrets Manager rotation natively), Redis AUTH token, API keys. Use IAM roles for S3 access instead of static credentials. Reference secrets from Secrets Manager in EKS pod definitions via ExternalSecrets or ASCP. |
| **Evidence** | `packages/server/.env.example` (DATABASE_PASSWORD, REDIS_PASSWORD, S3_STORAGE_SECRET_ACCESS_KEY, SMTP_PASSWORD as env vars; SECRETKEY_STORAGE_TYPE=aws for master key only) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Dockerfile uses `node:20-alpine` as the base image — a minimal image but not a hardened or scanned base. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened AMI references. The Docker image installs build tools (python3, make, g++, chromium) that increase attack surface. No multi-stage build to minimize the final image. |
| **Gap** | No vulnerability scanning. No hardened base images. Build tools and chromium included in the final production image increase attack surface. No patching strategy. |
| **Recommendation** | Use multi-stage Docker builds to separate build and runtime images. Use AWS-provided base images or Bottlerocket for EKS nodes. Enable ECR image scanning. Integrate Snyk or Trivy container scanning in the CI pipeline. Remove chromium and build tools from the production image (use a separate image for Puppeteer tasks). |
| **Evidence** | `Dockerfile` (single-stage build with python3, make, g++, chromium in production image), absence of vulnerability scanning in CI workflows |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline (`main.yml`) runs lint and tests but has no SAST, DAST, or dependency vulnerability scanning steps. No Dependabot configuration, no `npm audit` in the pipeline, no SonarQube/Semgrep integration. The `.github/workflows/` directory contains no security scanning workflows. However, ESLint is configured which provides basic code quality checks. |
| **Gap** | No dependency vulnerability scanning (no Dependabot, no npm audit in CI). No SAST tool. No container image scanning. Pipeline has no security validation step. |
| **Recommendation** | Add `npm audit --audit-level=high` to the CI pipeline. Enable GitHub Dependabot for dependency alerts. Integrate Semgrep or CodeGuru Reviewer for SAST. Add ECR image scanning for Docker builds. Configure security gates that block on critical/high findings. |
| **Evidence** | `.github/workflows/main.yml` (no security scanning steps), `.github/workflows/docker-image-ecr.yml` (no image scanning), absence of `.github/dependabot.yml` |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry is integrated with support for OTLP export via HTTP, gRPC, and Proto protocols. The OTel Collector is configured to export traces to Datadog. The `@opentelemetry/auto-instrumentations-node` package provides automatic instrumentation for Express, HTTP, and database calls. Prometheus metrics are also available as an alternative. The tracing infrastructure is well-implemented for the main server process. |
| **Gap** | Tracing on the primary server is implemented. However, it is unclear if trace context propagates through BullMQ queue boundaries (worker receives a job — does it inherit the parent trace?). OTel Collector is configured for Datadog only, not X-Ray. |
| **Recommendation** | Ensure trace context propagation through BullMQ job metadata so worker spans are linked to the originating request trace. For AWS deployment, add X-Ray exporter to the OTel Collector configuration (or use ADOT Collector). Consider enabling W3C trace context headers for downstream LLM API calls. |
| **Evidence** | `packages/server/src/metrics/OpenTelemetry.ts`, `metrics/otel/otel.config.yml` (Datadog exporter), `packages/server/package.json` (@opentelemetry/auto-instrumentations-node) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No error budget tracking, no p99/p95 latency targets, no availability targets. The Prometheus metrics and Grafana dashboards provide observability data but there are no formal SLO definitions or alerting based on SLO violations. |
| **Gap** | No formal SLO definitions for any user journey. No error budgets. Cannot measure whether the system is meeting user expectations. |
| **Recommendation** | Define SLOs for critical journeys: prediction latency p99 < X seconds, chatflow creation success rate > 99.5%, document processing completion rate > 99%. Implement CloudWatch Synthetics or custom metrics for SLO tracking. Configure alerts on error budget burn rate. |
| **Evidence** | `metrics/grafana/` (dashboards exist but no SLO targets), absence of SLO definition files or error budget configuration |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus metrics include application-specific counters via `FLOWISE_METRIC_COUNTERS` enum (prediction counts, chatflow executions, etc.) alongside default infrastructure metrics. PostHog is integrated for product analytics (`posthog-node`). However, there are no CloudWatch custom metrics for business outcomes, and the metrics are primarily operational rather than business-outcome focused. |
| **Gap** | Infrastructure and basic operational metrics exist. Product analytics (PostHog) tracks user behavior. But no formal business outcome metrics (conversion rates, time-to-value, cost-per-prediction) are published to the observability stack. |
| **Recommendation** | Define and publish business metrics: predictions-per-hour by model, average prediction latency by provider, document processing throughput, active chatflow count, API key usage patterns. Integrate with CloudWatch custom metrics for unified alerting. |
| **Evidence** | `packages/server/src/metrics/Prometheus.ts` (FLOWISE_METRIC_COUNTERS), `packages/server/package.json` (posthog-node), `metrics/grafana/` (dashboards) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus + Grafana provide metrics collection and visualization. The Grafana dashboards exist for app and server metrics. However, no anomaly detection is configured, and no alerting rules are defined in the Prometheus or Grafana configs within the repository. Static threshold alarms would need to be configured in Grafana or CloudWatch — neither is present in the codebase. |
| **Gap** | Metrics are collected but no alerting or anomaly detection is configured. Dashboards exist for visualization but no automated response to anomalies. |
| **Recommendation** | Configure CloudWatch anomaly detection on key metrics (error rate, prediction latency, queue depth). Define Grafana alerting rules for static thresholds as a first step. Integrate with PagerDuty or OpsGenie for on-call notification. |
| **Evidence** | `metrics/prometheus/prometheus.config.yml` (scrape config only, no alert rules), `metrics/grafana/` (dashboards without alerting) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Deployment is manual. The ECR workflow (`docker-image-ecr.yml`) uses `workflow_dispatch` (manual trigger) to build and push images. There is no blue/green, canary, rolling, or staged deployment strategy. After an image is pushed to ECR, deployment to the running environment is entirely manual (not defined in any workflow or IaC). |
| **Gap** | Direct-to-production deployment with no staged rollout. No deployment automation after image build. No rollback mechanism. |
| **Recommendation** | Implement GitOps with ArgoCD on EKS — automatic deployment on image push to ECR. Configure Argo Rollouts for canary deployments with automatic rollback on health check failure. Define progressive delivery: 10% → 50% → 100% traffic shift with metric gates. |
| **Evidence** | `.github/workflows/docker-image-ecr.yml` (workflow_dispatch, push-only — no deploy step), absence of any deployment automation |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Jest unit tests exist across packages (server, components, agentflow). Cypress E2E tests cover API key management and variables. Artillery load testing is configured. However, integration tests for critical AI workflows (prediction flow, document processing pipeline, chatflow execution) are limited. The CI pipeline runs unit tests and Cypress E2E but the E2E tests are minimal (2 test files: apikey, variables). |
| **Gap** | Unit tests exist but integration tests for critical workflows (prediction, document processing, multi-agent execution) are missing or minimal. Cypress E2E covers only basic CRUD operations, not the AI-critical paths. |
| **Recommendation** | Add integration tests for: (1) Full prediction flow (chatflow → prediction → response), (2) Document processing pipeline (upload → chunk → embed → store), (3) Agent execution (multi-agent workflow completion). Run these in CI with test containers (Testcontainers for PostgreSQL, Redis). |
| **Evidence** | `.github/workflows/main.yml` (runs test:coverage and Cypress), `packages/server/cypress/e2e/` (2 test files only), `packages/agentflow/` (60+ unit tests but UI-focused) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The `SECURITY.md` provides a vulnerability reporting process but no operational incident response documentation. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation for common failure scenarios (queue backlog, database connection exhaustion, OOM). |
| **Recommendation** | Create runbooks for common incidents: (1) Queue backlog — auto-scale workers via HPA, (2) Database connection exhaustion — circuit breaker + connection pool alert, (3) LLM provider timeout — fallback model routing. Implement SSM Automation documents or Step Functions for automated remediation. |
| **Evidence** | Absence of any runbook files, SSM documents, or automated remediation; `SECURITY.md` (vulnerability reporting only, not operational incident response) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Grafana dashboards exist (app and server dashboards) and Prometheus metrics are configured. However, there is no CODEOWNERS file, no named owners on alarms, no team attribution on dashboards or metrics. The observability configuration is centralized in the `metrics/` directory but without ownership metadata. |
| **Gap** | Observability assets exist but have no ownership attribution. No CODEOWNERS for observability configs. No team-specific dashboards or alarm ownership. |
| **Recommendation** | Create a CODEOWNERS file with ownership for `metrics/` directory. Add team attribution tags to Grafana dashboards. When moving to CloudWatch, use resource tags for alarm ownership. Define on-call ownership for critical metrics. |
| **Evidence** | `metrics/grafana/` (dashboards without ownership), `metrics/prometheus/` (config without ownership), absence of CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists because no IaC exists. No `default_tags`, no tag enforcement, no cost allocation tags. The Docker Compose files have no tagging mechanism. When infrastructure is eventually defined in IaC, tagging governance will need to be established from scratch. |
| **Gap** | No tags on any AWS resources. No tagging standard. No cost allocation or ownership attribution possible. |
| **Recommendation** | When creating IaC, define mandatory tags: `Environment`, `Service`, `Team`, `CostCenter`, `ManagedBy`. Use Terraform `default_tags` provider block. Enforce via AWS Config required-tags rules. Activate cost allocation tags in AWS Billing. |
| **Evidence** | Absence of any IaC with tags; no tagging configuration anywhere in the repository |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `Dockerfile` | INF-Q1, SEC-Q6 | Root monorepo Docker build — single-stage, node:20-alpine with build tools |
| `docker/Dockerfile` | INF-Q1 | Pre-built image Docker configuration |
| `docker/worker/Dockerfile` | INF-Q1, INF-Q3, APP-Q4 | Worker container with 8GB heap for long-running tasks |
| `docker/docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q9, APP-Q2, APP-Q5 | Main single-service deployment with env var config |
| `docker/worker/docker-compose.yml` | INF-Q1 | Worker deployment configuration |
| `.github/workflows/main.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline with build, lint, test, Cypress |
| `.github/workflows/docker-image-ecr.yml` | INF-Q1, INF-Q11, OPS-Q5 | Manual dispatch ECR push — no deploy step |
| `packages/server/src/index.ts` | INF-Q3, APP-Q3, APP-Q4 | Express app with QueueManager, SSEStreamer, MetricsProvider |
| `packages/server/src/DataSource.ts` | INF-Q2, DATA-Q2, DATA-Q3 | TypeORM multi-database connection factory |
| `packages/server/.env.example` | INF-Q2, INF-Q4, INF-Q5, SEC-Q5, DATA-Q1 | 204-line config with all env vars |
| `packages/server/src/utils/rateLimit.ts` | INF-Q4, APP-Q3, SEC-Q3 | Redis-backed rate limiting with BullMQ |
| `packages/server/src/utils/logger.ts` | SEC-Q1, OPS-Q1 | Winston logging with multiple transports |
| `packages/server/src/metrics/Prometheus.ts` | OPS-Q1, OPS-Q3 | Prometheus metrics with custom counters |
| `packages/server/src/metrics/OpenTelemetry.ts` | OPS-Q1 | OTel metrics with OTLP export |
| `metrics/otel/otel.config.yml` | OPS-Q1, OPS-Q4 | OTel Collector config (Datadog export) |
| `metrics/prometheus/prometheus.config.yml` | OPS-Q4 | Prometheus scrape config |
| `metrics/grafana/` | OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q8 | Grafana dashboards (app + server) |
| `packages/server/src/database/entities/` | APP-Q2, DATA-Q2 | 20 TypeORM entities (shared schema) |
| `packages/server/src/database/migrations/` | DATA-Q3, DATA-Q4 | Migrations for 4 DB types (standard DDL only) |
| `packages/server/src/routes/` | APP-Q2, APP-Q5, APP-Q6 | 56 route modules under single v1 prefix |
| `packages/server/src/enterprise/middleware/passport/` | SEC-Q3, SEC-Q4 | Passport.js auth strategies |
| `packages/server/src/enterprise/sso/` | SEC-Q4 | SSO integration |
| `packages/server/package.json` | APP-Q1, INF-Q4, OPS-Q1, SEC-Q6 | Server dependencies (Express, TypeORM, OTel, BullMQ) |
| `packages/api-documentation/src/yml/swagger.yml` | APP-Q5 | OpenAPI spec |
| `.nvmrc` | APP-Q1 | Node.js v20.19.2 |
| `packages/server/cypress/e2e/` | OPS-Q6 | Cypress E2E tests (2 files) |
| `artillery-load-test.yml` | OPS-Q6 | Load testing configuration |
| `SECURITY.md` | OPS-Q7 | Security vulnerability reporting policy |
