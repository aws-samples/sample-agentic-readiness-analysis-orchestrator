# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | ToolJet--ToolJet |
| **Date** | 2025-05-08 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | javascript, low-code, frontend |
| **Context** | Open-source low-code internal-tool builder. |
| **Overall Score** | 2.23 / 4.0 |

**Archetype Justification**: The application owns persistent PostgreSQL databases (main app DB + ToolJet DB), exposes CRUD operations on business entities (apps, data sources, organizations, users), and manages user-specific state with session/JWT authentication. Classified as `stateful-crud`.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true, has_iac_provisioning_aws_resources=true

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 2.00 / 4.0 | 🟠 Needs Work | Needs Work |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.17 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work | Needs Work |
| **Overall** | **2.23 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (3 + 2 + 3 + 3 + 2 + 2 + 1 + 1 + 1 + 2 + 2) / 11 = 22/11 = 2.00
- APP: (3 + 2 + 3 + 3 + 3 + 2) / 6 = 16/6 = 2.67
- DATA: (2 + 3 + 3 + 3) / 4 = 11/4 = 2.75
- SEC: (1 + 3 + 3 + 2 + 2 + 2) / 6 = 13/6 = 2.17 [SEC-Q1 excluded: Not Evaluated]
- OPS: (3 + 1 + 2 + 1 + 2 + 2 + 1 + 1 + 1) / 9 = 14/9 = 1.56
- Overall: (2.00 + 2.67 + 2.75 + 2.17 + 1.56) / 5 = 11.15/5 = 2.23

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q7: Auto-Scaling | 1 | No auto-scaling configured in IaC; Helm HPA defaults to max=1 | Cannot respond to traffic spikes; over/under-provisioning risk |
| 2 | INF-Q8: Backup and Recovery | 1 | RDS has no backup_retention_period configured (defaults to 0); no backup plans | Data loss risk with no recovery capability |
| 3 | OPS-Q4: Anomaly Detection | 1 | No alerting or anomaly detection configured | Degradation goes undetected until user reports |
| 4 | SEC-Q2: Encryption at Rest | 1 | No storage_encrypted on RDS; no KMS keys configured | Sensitive user data stored unencrypted at rest |
| 5 | OPS-Q7: Incident Response | 1 | No runbooks, incident response docs, or automated remediation | Mean-time-to-recovery entirely dependent on individual knowledge |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2; GitHub Actions workflows with build, test, and deploy stages)
- **What it enables:** An agent that triggers deployments, checks build status, monitors CI pipeline health, and manages releases via GitHub Actions API
- **Additional steps:** GitHub Actions REST API access needs to be configured; deploy workflow could expose webhook triggers
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in repo (README, docs/, CONTRIBUTING.md, SECURITY.md detected during discovery)
- **What it enables:** A knowledge agent using existing documentation as a corpus to answer developer questions about ToolJet architecture, deployment, and plugin development
- **Additional steps:** Documentation needs to be indexed; existing `docs/` directory and contributor guides provide the corpus. Consider adding architecture decision records.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 3; comprehensive OpenTelemetry with traces, metrics, custom business metrics)
- **What it enables:** An agent that queries OTEL traces and metrics, correlates incidents across service boundaries, and suggests root causes based on trace patterns
- **Additional steps:** OTEL collector endpoint needs to be accessible to the agent; custom metrics (api.hits, api.duration, users.concurrent) provide rich signal
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=3 (partial managed compute) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=3 and Dockerfiles + Helm charts already exist; compute is already containerized |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=3 (minimal stored procedures); no commercial DB engines detected — PostgreSQL is already open source |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=2 (self-managed Redis sidecar, PostgreSQL in dev compose) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads, ETL, or streaming infrastructure detected |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=2 (partial IaC), INF-Q11=2 (partial CI/CD), OPS-Q5=2 (no canary/blue-green), OPS-Q6=2 (limited integration tests in CI) |
| 7 | Move to AI | Not Triggered | — | — | AI/agent frameworks already present (AWS Bedrock, OpenAI, Anthropic plugins; server AI module with graph/agent services) |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** ToolJet is a modular monolith (APP-Q2=2) with identifiable modules (58 NestJS modules) but shared PostgreSQL database schemas and direct cross-module data access patterns. The backend is a single deployable NestJS application containing auth, AI, workflows, data-queries, organizations, licensing, and 50+ other modules.

**Compute Model:** Already containerized on ECS Fargate (INF-Q1=3), which is a positive foundation. The monolith runs as a single container image with Redis and PostgREST sidecars.

**Communication Patterns:** Inter-module communication is synchronous within the monolith process. External integrations (50+ data source plugins) are synchronous HTTP. BullMQ provides async job processing for background tasks.

**Recommended Decomposition Approach:** Strangler Fig pattern — incrementally extract high-value modules (AI, workflows, data-queries) as independent services while the monolith continues to serve traffic.

**Representative AWS Services:** ECS/EKS (preferred: EKS per preferences), API Gateway, EventBridge, Step Functions, Aurora PostgreSQL
**Recommended Patterns:** Anti-corruption Layer, Saga, Hexagonal Architecture

**Reference:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** Production ECS deployment uses RDS PostgreSQL (managed), but the Redis caching/job layer runs as a self-managed sidecar container within the ECS task definition. Development environments use self-managed PostgreSQL 13 and Redis 6.2 in Docker Compose.

**Engine Versions:** PostgreSQL 16 (ECS Terraform), PostgreSQL 13 (Docker Compose dev). Redis 6.2 (sidecar).

**Recommended Migration Targets:**
- **Redis → Amazon ElastiCache for Redis or Amazon MemoryDB**: Eliminates sidecar management, provides Multi-AZ, automatic failover, and backup capabilities. MemoryDB for durability requirements.
- **PostgreSQL → Aurora PostgreSQL** (preferred per preferences): Provides automated failover, read replicas, automated backups with PITR, and up to 5x throughput improvement over standard PostgreSQL.

**Migration Tools:** AWS DMS for zero-downtime migration; native PostgreSQL `pg_dump`/`pg_restore` for smaller datasets.

**Reference:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=2):** Terraform covers ECS, EC2, and AMI deployments but does not cover operational resources (CloudWatch alarms, backup plans, Route 53 health checks). Helm chart covers Kubernetes deployment but with minimal operational config. No `default_tags`, no shared modules.

**Current CI/CD State (INF-Q11=2):** GitHub Actions provides automated build and lint. Unit tests run in CI. Docker image builds are automated. However, deployment to production is manual (`deploy-to-stage.yml` requires manual trigger), no automated rollback, and no IaC deployment pipeline.

**Deployment Strategy Gaps (OPS-Q5=2):** RollingUpdate in Kubernetes with basic health checks. No canary, blue/green, or traffic shifting. The `deploy-to-stage.yml` uses `kubectl set image` directly.

**Testing Gaps (OPS-Q6=2):** 42 e2e controller tests and Cypress E2E tests exist but are not systematically run on every deployment. CI runs unit tests and lint but not full integration suites.

**Recommended DevOps Toolchain:**
- **IaC Pipeline:** Terraform with remote state + plan/apply in CI (GitHub Actions)
- **Deployment Strategy:** Implement blue/green via EKS with AWS CodeDeploy or Argo Rollouts
- **Integration Testing:** Add Cypress E2E to deployment pipeline as gate
- **Observability:** Extend OTEL config to all environments; add CloudWatch alarms via IaC

**Representative AWS Services:** CodePipeline, CodeDeploy, CloudFormation/CDK, X-Ray, CloudWatch

**Reference:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

---

## Decomposition Strategy

APP-Q2 scored 2 (monolith with identifiable modules but shared database schemas). The following decomposition guidance applies.

### Recommended Approach: Strangler Fig (Parallel Track)

ToolJet's 58 NestJS modules provide clear boundary candidates for extraction. The modular monolith structure with distinct module directories (`ai/`, `workflows/`, `data-queries/`, `auth/`, `organizations/`) makes incremental extraction feasible.

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | ToolJet's modular NestJS structure with identifiable module boundaries (58 modules). Team can sustain parallel development. | Medium to High | ✅ **Recommended.** Extract high-value modules (AI, workflows, data-queries) first while monolith serves traffic. |
| **Conditional / Adaptive** | If capacity is constrained — containerize as-is (already done), then selectively extract modules. | Low to Medium | ✅ **Alternative if capacity constrained.** Already containerized; focus on selective extraction. |
| **Big-Bang Rewrite** | Not applicable — the monolith is functional and well-structured. | Very High | ⚠️ **Not recommended.** Modular structure supports incremental approach. |

### Pattern Recommendations

| Pattern | Purpose | Application to ToolJet |
|---------|---------|----------------------|
| **Anti-corruption Layer** | Isolate extracted services from monolith data model | Place ACL between extracted AI/workflow services and the shared PostgreSQL database |
| **Saga Pattern** | Distributed transactions across services | Apply when extracting data-queries module — app execution involves multi-step data source queries |
| **Event Sourcing** | Capture state changes as events | Apply to audit-logs module; enable event-driven integration between extracted services via EventBridge |
| **Hexagonal Architecture** | Clear boundaries in new services | Structure each extracted service with ports/adapters for database, messaging, and external APIs |

### Effort Estimation

| Factor | Signal | Analysis |
|--------|--------|------------|
| Module boundaries | 58 distinct NestJS modules with clear directory structure | Low effort — boundaries exist |
| Data coupling | Shared PostgreSQL with TypeORM entities accessed across modules | High effort — data separation required |
| Stored procedures | Minimal (DATA-Q4=3) — business logic in application layer | Low effort — no DB logic extraction needed |
| Communication patterns | BullMQ for background jobs; mostly sync within process | Medium effort — need to externalize inter-module calls |
| CI/CD maturity | GitHub Actions exists but limited automation | Medium effort — pipeline needs multi-service support |
| Test coverage | 42 e2e tests + Cypress; moderate coverage | Medium effort — sufficient baseline for safe extraction |

**Priority extraction candidates:**
1. **AI Module** — Self-contained, rapidly evolving, distinct compute profile (GPU/high-memory for LLM calls)
2. **Workflow Module** (Temporal integration) — Already designed for external orchestration
3. **Data-Queries Module** — High fan-out to 50+ data sources; would benefit from independent scaling

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary production deployment uses ECS Fargate (managed container orchestration) with 2 tasks. Helm chart and Kubernetes manifests provide EKS/AKS/GKE deployment options. EC2 and AMI-based deployments also exist as alternative deployment paths. |
| **Gap** | EC2/AMI deployment options remain alongside managed compute. Not all deployment paths use managed orchestration. |
| **Recommendation** | Deprecate EC2/AMI deployment paths; standardize on EKS (preferred) or ECS Fargate for all environments. |
| **Evidence** | `terraform/ECS/main.tf` (Fargate), `terraform/AMI_EC2/ec2.tf` (EC2), `deploy/helm/` (Kubernetes), `deploy/kubernetes/` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Production ECS deployment uses RDS PostgreSQL 16 (managed). However, Redis 6.2 runs as a self-managed sidecar container within the ECS task. Development environments use self-managed PostgreSQL 13 and Redis in Docker Compose. RDS instance is single-AZ with no Multi-AZ failover. |
| **Gap** | Redis is self-managed as a sidecar (no failover, no persistence guarantees). Production RDS is single-AZ without Multi-AZ failover enabled. |
| **Recommendation** | Migrate Redis to Amazon ElastiCache for Redis or MemoryDB with Multi-AZ. Enable Multi-AZ on RDS. Consider Aurora PostgreSQL (preferred) for automated failover and enhanced performance. |
| **Evidence** | `terraform/ECS/main.tf` (RDS without multi_az, Redis sidecar container), `docker-compose.yaml` (self-managed postgres:13, redis:6.2) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Temporal.io is integrated for workflow orchestration (Enterprise Edition feature). BullMQ provides job queue processing for background tasks. The workflow module (`server/src/modules/workflows/`) provides dedicated orchestration for multi-step operations. |
| **Gap** | Temporal integration is EE-only; Community Edition has no dedicated workflow orchestration. BullMQ handles background jobs but is not a full workflow orchestrator. |
| **Recommendation** | Evaluate AWS Step Functions as a managed alternative to Temporal for workflow orchestration, providing native AWS integration and eliminating Temporal cluster management overhead. |
| **Evidence** | `server/package.json` (@temporalio/client, @temporalio/worker), `server/src/modules/workflows/`, BullMQ in dependencies |

*Archetype calibration applied: stateful-crud — multi-step operations exist (app building workflows, data query execution chains). Temporal addresses this appropriately for EE.*

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | BullMQ (backed by Redis) provides async job processing for background tasks. No managed AWS messaging service (SQS, SNS, EventBridge) is used. The async pattern covers internal job queues but not cross-service event-driven communication. |
| **Gap** | Messaging is Redis-backed BullMQ only — no managed messaging service. If Redis fails, all async processing stops. No event-driven architecture for cross-service communication. |
| **Recommendation** | Adopt Amazon SQS for job queues and EventBridge (preferred) for event-driven patterns as the system decomposes. This eliminates Redis as a single point of failure for async processing. |
| **Evidence** | `server/package.json` (bullmq, ioredis), `terraform/ECS/main.tf` (Redis sidecar), `.env.example` (REDIS_HOST, REDIS_PORT) |

*Archetype calibration applied: stateful-crud — cross-service state changes (user actions, app deployments, data source updates) would benefit from managed async messaging as the system decomposes.*

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECS Terraform creates a VPC with 2 public subnets. Security groups exist for ALB and ECS tasks. However, all subnets are public (no private subnets). The AMI/EC2 deployment puts instances directly in a public subnet with public IP. |
| **Gap** | No private subnets — ECS tasks and RDS are in public subnets. EC2 deployment has public IP with direct internet exposure. No VPC endpoints or PrivateLink. |
| **Recommendation** | Restructure VPC with public/private subnet tiers. Place ECS tasks and RDS in private subnets with NAT Gateway for outbound. Add VPC endpoints for AWS services (ECR, S3, Secrets Manager). |
| **Evidence** | `terraform/ECS/main.tf` (public subnets only, map_public_ip_on_launch=true), `terraform/AMI_EC2/ec2.tf` (public subnet, associate_public_ip_address) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ALB is configured in ECS Terraform with health checks on `/api/health`. Kubernetes deployment uses LoadBalancer service type with AWS SSL annotation. However, no throttling, request validation, or authentication is configured at the gateway level. |
| **Gap** | ALB provides basic routing and health checks only. No API Gateway with throttling, auth, or request validation. No rate limiting at the entry point. |
| **Recommendation** | Add Amazon API Gateway (preferred) in front of the ALB for throttling, request validation, and centralized auth. Alternatively, configure ALB with WAF rules for rate limiting and request filtering. |
| **Evidence** | `terraform/ECS/main.tf` (aws_lb, aws_lb_target_group with health check), `deploy/kubernetes/service.yaml` (LoadBalancer with SSL annotation) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configured in ECS Terraform (static `desired_count = 2`). Helm HPA exists but defaults to min=1, max=1 (effectively disabled). No Application Auto Scaling for ECS. No DynamoDB or database auto-scaling. |
| **Gap** | All capacity is statically provisioned. No auto-scaling on compute, database, or caching layers. System cannot respond to traffic changes. |
| **Recommendation** | Add ECS Application Auto Scaling with target tracking on CPU/memory and custom metrics (concurrent users, API request rate). Enable HPA in Helm with appropriate min/max. Consider Aurora Auto Scaling for read replicas. |
| **Evidence** | `terraform/ECS/main.tf` (desired_count=2, no aws_appautoscaling_*), `deploy/helm/values.yaml` (hpa.min=1, hpa.max=1) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | RDS instance has no `backup_retention_period` configured (defaults to 0 = no automated backups). No `aws_backup_plan` resources. `skip_final_snapshot = true` means no snapshot on deletion. No PITR capability. Redis sidecar has no persistence configuration. |
| **Gap** | Zero backup and recovery capability. Data loss on any failure is permanent. No restore procedures. |
| **Recommendation** | Configure `backup_retention_period = 7` (minimum) on RDS with PITR enabled. Add `aws_backup_plan` for cross-service backup orchestration. Enable Redis persistence or migrate to ElastiCache with automated backups. Remove `skip_final_snapshot = true` for production. |
| **Evidence** | `terraform/ECS/main.tf` (no backup_retention_period, skip_final_snapshot=true, no deletion_protection) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | ECS spans 2 subnets in different AZs (us-east-1a, us-east-1b) for compute, but RDS is single-AZ (no `multi_az = true`). Redis runs as a sidecar (single-instance, no replication). AMI/EC2 deployment is entirely single-AZ. |
| **Gap** | Database (RDS) is single-AZ — an AZ failure takes down the entire data layer. Redis sidecar has no failover. EC2 deployment path has no HA. |
| **Recommendation** | Enable `multi_az = true` on RDS. Migrate Redis to ElastiCache with Multi-AZ replication. Remove single-AZ EC2 deployment path or add ASG with multi-AZ. |
| **Evidence** | `terraform/ECS/main.tf` (no multi_az on aws_db_instance), `terraform/ECS/variables.tf` (2 AZs for subnets), `terraform/AMI_EC2/ec2.tf` (single subnet) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Terraform covers ECS cluster, VPC, ALB, RDS, and security groups. Helm chart covers Kubernetes deployment. However, no IaC for CloudWatch alarms, Route 53, backup plans, WAF, or operational resources. Multiple deployment targets (ECS, EC2, AMI, Kubernetes, AKS, GKE) without shared modules. |
| **Gap** | IaC covers compute and networking but not operational/DR resources. No monitoring, alerting, or backup infrastructure in code. No shared Terraform modules across deployment targets. |
| **Recommendation** | Extend IaC to cover CloudWatch alarms, backup plans, and WAF rules. Create shared Terraform modules for common patterns across deployment targets. Add `default_tags` to the AWS provider block. |
| **Evidence** | `terraform/ECS/main.tf` (compute + network), `deploy/helm/` (k8s deployment). No CloudWatch, Backup, or WAF resources found in any Terraform file. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides automated build, lint, and unit tests on push to develop/main. Docker image builds are automated on release. However, deployment requires manual workflow trigger (`deploy-to-stage.yml` is workflow_dispatch). No automated rollback. No IaC deployment pipeline (Terraform changes are manual). |
| **Gap** | Deployment is manual or semi-manual. No automated IaC pipeline. No automated rollback on failure. Build is automated but deploy is not continuous. |
| **Recommendation** | Implement continuous deployment pipeline: build → test → deploy-to-staging → integration-test → promote-to-prod. Add Terraform plan/apply stages to CI. Implement automated rollback via CodeDeploy or Argo Rollouts. |
| **Evidence** | `.github/workflows/ci.yml` (build + test), `.github/workflows/deploy-to-stage.yml` (manual trigger), `.github/workflows/docker-release.yml` (automated build). No terraform CI workflow. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeScript/JavaScript on Node.js 22.15.1 with NestJS 11.x framework. AWS SDK v3 used in marketplace plugins. Modern language version with mature cloud-native ecosystem. |
| **Gap** | Framework is current (NestJS 11), language is current (Node.js 22), but AWS SDK usage is limited to marketplace plugins rather than core infrastructure integration. No SDK usage for core AWS services (SQS, EventBridge, etc.) in the main server. |
| **Recommendation** | Expand AWS SDK v3 usage beyond marketplace plugins to core infrastructure (SQS for queues, EventBridge for events, Secrets Manager for credentials). TypeScript + NestJS 11 + Node.js 22 is a strong modern foundation. |
| **Evidence** | `server/package.json` (node engine 22.15.1, @nestjs/* 11.x), `marketplace/plugins/aws-bedrock/` (AWS SDK v3), root `package.json` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Modular monolith with 58 NestJS modules in a single deployable unit. Clear module directory structure (`server/src/modules/`). However, modules share a single PostgreSQL database with TypeORM entities accessed across module boundaries. Single container image deployed as one ECS task. |
| **Gap** | Shared database schemas with cross-module data access. Single deployable unit prevents independent scaling of high-load modules (AI, data-queries). All 58 modules must be deployed together. |
| **Recommendation** | Begin Strangler Fig decomposition starting with the AI module (distinct compute profile, self-contained functionality) and data-queries module (high fan-out, independent scaling needs). Introduce per-module database schemas as a first step toward data separation. |
| **Evidence** | `server/src/modules/` (58 module directories), `server/ormconfig.ts` (shared DB connections), `docker/` (single image builds), `terraform/ECS/main.tf` (single task definition) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | BullMQ provides async job processing for background tasks (email sending, webhook delivery, scheduled jobs). Within the monolith, module-to-module communication is synchronous (direct function calls). External data source integrations are synchronous HTTP. The async/sync ratio is appropriate for a stateful-crud monolith — background jobs are async while user-facing CRUD operations are synchronous. |
| **Gap** | As the system decomposes, synchronous inter-module calls will need to become async cross-service communication. No event-driven patterns for state change propagation exist today. |
| **Recommendation** | Introduce EventBridge (preferred) for state change events (app created, data source updated, user invited) as decomposition progresses. Current sync-for-CRUD + async-for-background pattern is appropriate for the monolith phase. |
| **Evidence** | `server/package.json` (bullmq), BullMQ job processors in server modules, synchronous HTTP calls in plugin system |

*Archetype calibration applied: stateful-crud — managed messaging for key async flows (BullMQ) with synchronous CRUD is the expected pattern.*

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | BullMQ handles background job processing for operations that may exceed 30 seconds (webhook retries, bulk data operations, scheduled workflows). Temporal.io (EE) provides explicit long-running workflow management with state tracking. The server has a 60-second statement timeout on database queries. |
| **Gap** | Community Edition lacks Temporal workflow support — long-running operations rely solely on BullMQ without state tracking or visual management. No user-facing status polling API for background operations. |
| **Recommendation** | Add status polling endpoints for long-running operations (bulk imports, AI generation). Consider AWS Step Functions as a managed alternative to Temporal for workflow state management. Expose job status via API for client-side polling. |
| **Evidence** | `server/package.json` (@temporalio/client, bullmq), `server/ormconfig.ts` (statement_timeout: 60000) |

*Archetype calibration applied: stateful-crud — long-running operations exist (AI generation, bulk data operations, workflow execution) and are partially handled via BullMQ/Temporal.*

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | NestJS URI-based versioning is enabled in the application bootstrap (`main.ts`). Default version is `VERSION_NEUTRAL`. Dedicated v2 controllers exist for components, pages, and events APIs. The versioning strategy is implemented but not applied uniformly across all endpoints. |
| **Gap** | Versioning exists but most endpoints use VERSION_NEUTRAL (unversioned). Only a few controllers (components, pages, events) have explicit v2 versions. No documented versioning policy. |
| **Recommendation** | Apply explicit versioning to all public API endpoints. Document the versioning policy and deprecation timeline. Ensure all new endpoints are created under a version prefix. |
| **Evidence** | `server/src/main.ts` (VersioningType.URI, VERSION_NEUTRAL default), v2 controllers in server/src/controllers/ |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Services find each other via environment variables (TOOLJET_HOST, TOOLJET_SERVER_URL, PG_HOST, REDIS_HOST, PGRST_HOST). ECS deployment uses localhost for sidecars within the same task. Kubernetes uses ClusterIP services. No dynamic service discovery (no Cloud Map, no Consul, no service mesh). |
| **Gap** | All service endpoints are environment-variable-based with no dynamic discovery. Adding or moving services requires configuration changes across all consumers. |
| **Recommendation** | Implement AWS Cloud Map for service discovery as decomposition progresses. For the current monolith + sidecars architecture, environment variables are acceptable. Plan for dynamic discovery when extracting services. |
| **Evidence** | `.env.example` (hardcoded host variables), `terraform/ECS/main.tf` (localhost references for sidecars), `deploy/kubernetes/service.yaml` (ClusterIP) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | File uploads and assets are referenced in the application (app icons, user avatars, imported data). Configuration supports various storage backends via environment variables. AWS Textract plugin exists in the marketplace for document parsing. No S3 bucket is defined in the Terraform IaC. |
| **Gap** | No S3 infrastructure defined in IaC. File storage configuration is environment-variable-driven without a clear managed object storage setup in the production infrastructure. Textract plugin exists but is not part of a cohesive document processing pipeline. |
| **Recommendation** | Define S3 buckets in Terraform for application assets, user uploads, and app exports. Establish a document processing pipeline leveraging the existing Textract marketplace plugin. Configure S3 lifecycle policies for cost optimization. |
| **Evidence** | `terraform/ECS/main.tf` (no S3 resources), `marketplace/plugins/textract/` (Textract plugin exists), `.env.example` (storage configuration variables) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeORM provides a centralized ORM layer with entity definitions (`server/src/entities/`) and repository pattern. Two database connections are managed through `ormconfig.ts`. Most data access goes through TypeORM repositories. PostgREST provides a separate API layer for the ToolJet Database feature. |
| **Gap** | Some modules may bypass the repository pattern for performance (raw SQL queries). Two separate database connections (main + tooljetDb) create complexity. PostgREST adds a second data access path outside of TypeORM. |
| **Recommendation** | Enforce repository pattern consistently across all modules. Document which access path (TypeORM vs PostgREST) is authoritative for each data domain. Consider consolidating to a single database connection with schema-based isolation. |
| **Evidence** | `server/ormconfig.ts` (two DB connections), `server/src/entities/` (20+ entity files), PostgREST sidecar container |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Production ECS deployment pins PostgreSQL 16 (current, not EOL). Development Docker Compose uses PostgreSQL 13 (approaching EOL November 2025). Redis 6.2 is pinned in sidecar (current). Engine versions are explicitly specified in IaC. |
| **Gap** | Development environment uses PostgreSQL 13 which approaches EOL. Version mismatch between dev (13) and production (16) could cause compatibility issues during development and testing. |
| **Recommendation** | Upgrade Docker Compose dev environment to PostgreSQL 16 to match production. Establish version-update procedure documenting upgrade path, testing requirements, and rollback plan. |
| **Evidence** | `terraform/ECS/main.tf` (engine_version = "16"), `docker-compose.yaml` (postgres:13), `terraform/ECS/main.tf` (redis:6.2 sidecar image) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Business logic resides in the application layer (NestJS modules). TypeORM migrations manage schema changes. The `pgcrypto` extension is used for UUID generation. No stored procedures, triggers, or proprietary SQL constructs detected in migration files. PostgREST relies on PostgreSQL's native row-level security for access control. |
| **Gap** | PostgREST's dependency on PostgreSQL row-level security policies is a mild form of database-layer logic coupling. However, this is standard PostgreSQL (not proprietary) and is minimal relative to the application logic scope. |
| **Recommendation** | Maintain current approach — keeping business logic in the application layer is the correct pattern. Monitor PostgREST RLS policies to ensure they remain simple access control rather than growing into business logic. |
| **Evidence** | `server/migrations/` (184 TypeORM migrations — schema-only, no stored procedures), `server/ormconfig.ts` (pgcrypto extension) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application-level IaC only (ECS tasks, RDS instances, networking for this service) which is the correct scope for an application repo. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `terraform/ECS/main.tf` (application-level resources only — no CloudTrail, Config, or GuardDuty resources) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | RDS instance has no `storage_encrypted` parameter configured (defaults to false). No KMS keys defined in any Terraform configuration. EBS volumes on EC2 deployment have no encryption. No encryption configuration on any data store. |
| **Gap** | All data at rest is unencrypted — PostgreSQL database, Redis data, and EBS volumes. No KMS key management. This is a critical security gap for a platform that stores user credentials, API keys, and application data. |
| **Recommendation** | Add `storage_encrypted = true` with a customer-managed KMS key on RDS. Configure EBS encryption by default. Add KMS key for application-level encryption (LOCKBOX_MASTER_KEY should use KMS-backed encryption). Migrate Redis to ElastiCache with at-rest encryption. |
| **Evidence** | `terraform/ECS/main.tf` (no storage_encrypted on aws_db_instance, no aws_kms_key resources), `terraform/AMI_EC2/ec2.tf` (no EBS encryption) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive authentication system: JWT-based sessions via Passport.js, multiple OAuth2 providers (Google, GitHub), SAML/OIDC/LDAP integration, MFA support. CASL-based authorization for fine-grained access control. All API endpoints protected by auth guards. |
| **Gap** | Authentication is at the application level only — no API Gateway-level auth or throttling. No rate limiting at the infrastructure level to prevent brute force attacks. |
| **Recommendation** | Add API Gateway (preferred) with Cognito or JWT authorizer for infrastructure-level auth. Implement rate limiting via WAF or API Gateway throttling. Current application-level auth is comprehensive for the authentication itself. |
| **Evidence** | `server/package.json` (passport, passport-jwt, @nestjs/passport, samlify, openid-client, ldapjs), `server/src/modules/auth/` (guards, strategies, CASL abilities) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Application integrates with external identity providers: Google OAuth2, GitHub OAuth2, OIDC (any provider), SAML (enterprise SSO), LDAP. SCIM module exists for automated user provisioning. SSO is supported as an enterprise feature. |
| **Gap** | SSO/SAML/OIDC integration is an Enterprise Edition feature — Community Edition manages its own authentication entirely. No AWS Cognito integration for unified AWS-native identity management. |
| **Recommendation** | Consider AWS Cognito as the centralized identity provider for AWS deployments, leveraging its built-in SAML/OIDC federation. This consolidates identity management and enables IAM-integrated access control. |
| **Evidence** | `server/src/modules/auth/` (OIDC, SAML, LDAP strategies), `server/src/modules/scim/` (SCIM provisioning), `.env.example` (SSO_* variables) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Production credentials are passed via environment variables (PG_PASS, REDIS_PASSWORD, LOCKBOX_MASTER_KEY, SECRET_KEY_BASE). ECS task execution role has Secrets Manager policy attached. No plaintext credentials in source code (`.env.example` uses empty placeholders). Kubernetes deployment uses Kubernetes Secrets (base64 encoded, not encrypted at rest by default). |
| **Gap** | Credentials in environment variables without rotation. Kubernetes Secrets are base64-encoded (not encrypted). No automated rotation configured. ECS has Secrets Manager IAM policy but no explicit `aws_secretsmanager_secret` resources defined in IaC. |
| **Recommendation** | Define `aws_secretsmanager_secret` resources in Terraform for all production credentials (PG_PASS, REDIS_PASSWORD, LOCKBOX_MASTER_KEY). Configure automatic rotation for database credentials. Reference secrets from Secrets Manager in ECS task definition rather than environment variables. Enable EKS secrets encryption with KMS. |
| **Evidence** | `terraform/ECS/main.tf` (IAM policy for secretsmanager:GetSecretValue), `.env.example` (empty credential placeholders), `deploy/helm/templates/tooljet/secret.yaml` (Kubernetes Opaque Secret), `terraform/ECS/variables.tf` (credential variables with empty defaults) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECS Fargate eliminates OS-level patching responsibility. Container images use standard base images. Dependabot is configured for dependency updates. Grype scanner runs for container vulnerability scanning. However, no hardened base images (no Bottlerocket, no CIS-benchmark AMIs for EC2 path). EC2 deployment uses a custom AMI with no documented hardening. |
| **Gap** | EC2/AMI deployment path uses custom AMI without documented hardening. No AWS Inspector for runtime vulnerability scanning. Vulnerability scanning (Grype, npm audit) is periodic (weekly) rather than blocking. |
| **Recommendation** | Use Bottlerocket for ECS container hosts or migrate fully to Fargate. Enable AWS Inspector for continuous vulnerability analysis. Make vulnerability scanning a blocking gate in CI (fail build on critical CVEs). Remove EC2 deployment path or document hardening procedures. |
| **Evidence** | `.github/workflows/vulnerability-ci.yml` (weekly npm audit), `.github/workflows/grype-slack-notify.yml` (Grype scanning), `dependabot.yml`, `deploy/ec2/ee/tooljet_ubuntu_focal.pkr.hcl` (Packer AMI) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependency scanning exists: `npm audit` runs weekly via GitHub Actions, Dependabot monitors for updates, Grype scans container images. License compliance workflow exists. However, no SAST tool (no SonarQube, Semgrep, or CodeGuru). Scanning is periodic/advisory rather than pipeline-blocking. |
| **Gap** | No SAST tool for source code analysis. Vulnerability scanning is weekly (not per-commit). No blocking gate — vulnerabilities create PRs but don't block releases. No container scanning in the build pipeline (Grype is separate). |
| **Recommendation** | Add SAST (Semgrep or SonarQube) to the CI pipeline running on every PR. Make `npm audit --audit-level=critical` a blocking step in CI. Integrate ECR image scanning with blocking on critical/high findings before deployment. |
| **Evidence** | `.github/workflows/vulnerability-ci.yml` (weekly npm audit), `.github/workflows/grype-slack-notify.yml` (Grype), `dependabot.yml`. No SonarQube, Semgrep, or CodeGuru configuration found. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive OpenTelemetry implementation with W3C TraceContext propagation. Instruments HTTP, Express, NestJS, PostgreSQL, and Pino. Exports via OTLP HTTP. Custom metrics for API hits, duration, concurrent users. Feature-gated behind ENABLE_OTEL (EE/Cloud editions). |
| **Gap** | Tracing is EE/Cloud only — Community Edition has no observability instrumentation. No tracing on the frontend (client-side). No explicit trace propagation to Redis or PostgREST sidecar. |
| **Recommendation** | Enable OTEL for all editions (CE included). Add trace propagation to Redis operations and PostgREST calls. Consider AWS X-Ray as the trace backend for native AWS integration. Add browser-side tracing for end-to-end visibility. |
| **Evidence** | `server/src/otel/tracing.ts` (full OTEL setup), `server/package.json` (12 @opentelemetry/* packages, nestjs-otel), `.env.example` (ENABLE_OTEL, APM_VENDOR) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking. No formal definition of acceptable service levels for availability, latency, or throughput. Custom OTEL metrics exist (api.duration histogram) but no SLO targets are defined against them. |
| **Gap** | No SLOs — system reliability has no formal measurement or target. Cannot determine if the system is meeting user expectations or degrading. |
| **Recommendation** | Define SLOs for critical user journeys: app loading time (p99 < 3s), API response time (p95 < 500ms), availability (99.9%). Implement error budget tracking using the existing OTEL metrics as signals. Add CloudWatch composite alarms for SLO burn rate. |
| **Evidence** | No SLO definition files found. `server/src/otel/tracing.ts` has metrics but no targets. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Custom OTEL metrics include `users.concurrent` and `sessions.active` (business-adjacent). `server/src/otel/audit-metrics.ts` tracks audit log events. However, no metrics for core business outcomes (apps created, queries executed, deployments triggered, data source connections). |
| **Gap** | Metrics are infrastructure-focused (API hits, duration) with minimal business context. No dashboards tracking business KPIs. No conversion or adoption metrics. |
| **Recommendation** | Add business metrics: apps_created, queries_executed, active_workspaces, data_source_connections, workflow_executions. Publish to CloudWatch with dimension tags for workspace/organization. Build dashboards tracking business outcomes alongside infrastructure health. |
| **Evidence** | `server/src/otel/tracing.ts` (api.hits, api.duration, users.concurrent, sessions.active), `server/src/otel/audit-metrics.ts` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured in IaC. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no alert routing. OTEL exports metrics but no consumers are defined. Sentry is configured for error tracking but is not anomaly detection. |
| **Gap** | No alerting of any kind — system degradation goes undetected until user reports. No error rate thresholds, no latency alerting, no anomaly detection. |
| **Recommendation** | Add CloudWatch alarms for: API error rate > 5%, p99 latency > 5s, concurrent users anomaly, ECS task health. Integrate with SNS → PagerDuty for on-call alerting. Enable CloudWatch anomaly detection on key metrics. Define in IaC for reproducibility. |
| **Evidence** | No aws_cloudwatch_metric_alarm in any Terraform file. No alerting configuration in any config file. `server/package.json` (@sentry/nestjs for error tracking only). |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes deployment uses RollingUpdate strategy with maxUnavailable: 25%, maxSurge: 25%. ECS deployment has basic health check (900s grace period). `deploy-to-stage.yml` uses `kubectl set image` for deployment. No canary, blue/green, or traffic shifting. |
| **Gap** | Rolling update with health checks only — no staged rollout, no traffic shifting, no automated rollback on error rate increase. Deployment goes to all instances simultaneously (after rolling). |
| **Recommendation** | Implement blue/green deployment via AWS CodeDeploy with ECS or Argo Rollouts with EKS. Add automated rollback triggered by CloudWatch alarm (error rate increase post-deploy). Consider canary releases for the frontend (Cloudflare Pages already used for staging). |
| **Evidence** | `deploy/kubernetes/deployment.yaml` (RollingUpdate strategy), `.github/workflows/deploy-to-stage.yml` (kubectl set image), `terraform/ECS/main.tf` (health_check_grace_period_seconds=900) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | 42 e2e controller tests in `server/test/controllers/`. Cypress E2E test suites for app-builder and platform. CI runs unit tests and server e2e tests with PostgreSQL service container. However, Cypress E2E tests are in a separate directory with their own config and are not run as part of the standard CI pipeline (separate workflow with manual triggers). |
| **Gap** | Integration tests exist but are not consistently run on every deployment. Cypress E2E tests are manual/separate from the deploy pipeline. No contract tests between modules. Test coverage is thin relative to the 58-module codebase. |
| **Recommendation** | Integrate Cypress E2E tests into the deployment pipeline as a gate (must pass before promotion to production). Add contract tests for inter-module interfaces. Increase server integration test coverage for critical workflows (app creation, data query execution, workflow triggering). |
| **Evidence** | `server/test/controllers/` (42 e2e tests), `cypress-tests/` (E2E suites), `.github/workflows/ci.yml` (unit-test job with Postgres) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response documentation, or automated remediation found anywhere in the repository. No Systems Manager Automation documents. No self-healing patterns. SECURITY.md exists but covers vulnerability reporting, not incident response. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (database failover, high error rate, capacity exhaustion). No automated remediation. |
| **Recommendation** | Create runbooks for top failure scenarios: database connection exhaustion, Redis failure, high API error rate, ECS task crash loops. Implement SSM Automation documents for common remediations. Add Lambda-based auto-scaling triggers for capacity incidents. |
| **Evidence** | `SECURITY.md` (vulnerability reporting only). No runbook files, no SSM documents, no automation workflows found. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS file exists but only covers package.json and module.ts files — no observability assets are owned. No per-service dashboards defined in code. No alarm ownership. No SLO team attribution. OTEL implementation exists but has no documented ownership model. |
| **Gap** | No observability ownership model. No team-attributed dashboards or alarms. Monitoring responsibility is undefined. |
| **Recommendation** | Extend CODEOWNERS to include observability configurations (OTEL config, alarm definitions, dashboard-as-code). Define per-module SLO owners. Create CloudWatch dashboards-as-code with team tags. Assign on-call ownership for each service module. |
| **Evidence** | `CODEOWNERS` (covers package.json and module.ts only), `server/src/otel/` (no ownership documentation) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Only `Name` tags found on EC2 resources. ECS Terraform has zero tags on any resource (no tags on ECS cluster, service, task definition, RDS, ALB, security groups). No `default_tags` in any AWS provider block. No tagging standard documented. No cost allocation or environment tags. |
| **Gap** | No tagging governance. Cannot track costs per environment/feature, identify resource ownership during incidents, or enforce budget controls. |
| **Recommendation** | Add `default_tags` block to AWS provider with: Environment, Service, Team, CostCenter, ManagedBy. Add resource-specific tags for Name and Purpose. Implement AWS Config rule `required-tags` to enforce compliance. Enable cost allocation tags in billing. |
| **Evidence** | `terraform/ECS/main.tf` (no tags on any resource), `terraform/AMI_EC2/ec2.tf` (only Name tag on EC2 instance), no default_tags in any provider block |

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
| `terraform/ECS/main.tf` | INF-Q1, INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, SEC-Q1, SEC-Q2, SEC-Q5, OPS-Q5, OPS-Q9 | ECS Fargate infrastructure: VPC, ALB, ECS cluster, RDS PostgreSQL, Redis sidecar |
| `terraform/AMI_EC2/ec2.tf` | INF-Q1, INF-Q5, INF-Q9, SEC-Q2, OPS-Q9 | EC2/AMI deployment infrastructure: single-AZ, public subnet |
| `terraform/ECS/variables.tf` | INF-Q9, SEC-Q5 | ECS deployment variables including credential placeholders |
| `deploy/helm/values.yaml` | INF-Q7 | Helm chart values with HPA min=1, max=1 |
| `deploy/helm/templates/tooljet/deployment.yaml` | INF-Q1, OPS-Q5 | Kubernetes deployment with RollingUpdate strategy |
| `deploy/helm/templates/tooljet/hpa.yaml` | INF-Q7 | HPA configuration (disabled by default) |
| `deploy/helm/templates/tooljet/secret.yaml` | SEC-Q5 | Kubernetes Opaque Secret for credentials |
| `deploy/kubernetes/deployment.yaml` | INF-Q1, APP-Q2, OPS-Q5 | Generic Kubernetes deployment: 2 replicas, RollingUpdate |
| `deploy/kubernetes/service.yaml` | APP-Q6 | LoadBalancer service with AWS SSL annotation |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6 | Main CI: build, lint, unit tests with Postgres service |
| `.github/workflows/deploy-to-stage.yml` | INF-Q11, OPS-Q5 | Manual deployment workflow: kubectl set image |
| `.github/workflows/docker-release.yml` | INF-Q11 | Automated Docker image build on release |
| `.github/workflows/vulnerability-ci.yml` | SEC-Q6, SEC-Q7 | Weekly npm audit scanning |
| `.github/workflows/grype-slack-notify.yml` | SEC-Q6, SEC-Q7 | Grype container vulnerability scanning |
| `dependabot.yml` | SEC-Q6, SEC-Q7 | Dependency update automation |
| `server/package.json` | APP-Q1, APP-Q3, APP-Q4, INF-Q3, INF-Q4, OPS-Q1, OPS-Q4 | Server dependencies: NestJS 11, TypeORM, BullMQ, Temporal, OTEL, Sentry |
| `server/ormconfig.ts` | APP-Q2, DATA-Q2, DATA-Q3, DATA-Q4 | TypeORM configuration: 2 PostgreSQL connections, connection pool |
| `server/src/modules/` | APP-Q2, INF-Q3 | 58 NestJS modules forming modular monolith |
| `server/src/modules/auth/` | SEC-Q3, SEC-Q4 | Auth system: JWT, OAuth2, SAML, OIDC, LDAP, MFA, CASL |
| `server/src/modules/ai/` | Move to AI pathway | AI module: conversations, graph service, agents |
| `server/src/modules/workflows/` | INF-Q3 | Temporal.io workflow orchestration (EE) |
| `server/src/otel/tracing.ts` | OPS-Q1, OPS-Q2, OPS-Q3 | OpenTelemetry: traces, metrics, W3C propagation |
| `server/src/otel/audit-metrics.ts` | OPS-Q3 | Audit log metrics |
| `server/test/controllers/` | OPS-Q6 | 42 e2e controller test files |
| `server/migrations/` | DATA-Q4 | 184 TypeORM migration files (schema-only) |
| `cypress-tests/` | OPS-Q6 | Cypress E2E test suites |
| `docker-compose.yaml` | INF-Q2, DATA-Q3 | Dev environment: PostgreSQL 13, Redis 6.2 |
| `docker/` | INF-Q1 | 16 Dockerfiles for various editions |
| `.env.example` | APP-Q6, INF-Q4, SEC-Q5, OPS-Q1 | Environment variable configuration template |
| `marketplace/plugins/aws-bedrock/` | Move to AI pathway | AWS Bedrock integration plugin |
| `CODEOWNERS` | OPS-Q8 | Code ownership: package.json and module.ts only |
| `SECURITY.md` | OPS-Q7 | Vulnerability reporting policy (not incident response) |
| `deploy/ec2/ee/tooljet_ubuntu_focal.pkr.hcl` | SEC-Q6 | Packer AMI template |

---

## Classification

**Tier: Pilot-Ready**

This repo has 1 High finding, 22 Medium findings, 3 Low findings. The matched rule is "1 High → Pilot-Ready."

**Classification rationale:** MOD classification uses a softer threshold than ARA for single-High findings. ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High (e.g., missing encryption at rest) is typically one modernization gap rather than a deployment blocker. ToolJet has 1 High-severity finding (SEC-Q2: no encryption at rest on a core-priority question) and 22 Medium-severity findings across infrastructure, operations, and security gaps. The Medium findings reflect significant modernization work needed but are individually non-blocking.

**⚠️ Classification Consistency Check: DIVERGENT**

| Field | Value |
|-------|-------|
| **V5 Band** | Needs Work (score 2.23, band 1.5–2.4) |
| **V6 Tier** | Pilot-Ready (1 High → Pilot-Ready) |
| **Expected V6 Tier** | Remediation Required (V5 Needs Work ≡ V6 Remediation Required) |
| **Reason** | Score 2.23 yields V5 Needs Work but only 1 High finding (SEC-Q2, the sole P1/core question scoring 1) yields V6 Pilot-Ready. The divergence arises because 8 of 9 score-1 questions are P2 (non-core), which maps to Medium severity in V6 rather than High. The V5 numeric score captures the aggregate immaturity across many score-1 and score-2 questions, while V6 severity counts weight only core-question failures as High. |

This divergence is documented rather than corrected because it reflects a genuine design difference between V5 (arithmetic mean penalizes many low scores equally) and V6 (only core-question Score-1 results produce High severity). The V5 numeric score (2.23) accurately reflects the system's modernization maturity. The V6 tier (Pilot-Ready) accurately reflects that only one critical security gap exists among the score-1 findings.
