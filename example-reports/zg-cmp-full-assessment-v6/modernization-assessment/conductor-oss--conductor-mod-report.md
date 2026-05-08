# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | conductor-oss--conductor |
| **Date** | 2025-05-07 |
| **Repo Type** | application |
| **Service Archetype** | orchestrator (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, workflow, orchestration |
| **Context** | Workflow orchestration engine originally from Netflix. |
| **Overall Score** | 1.99 / 4.0 |

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false

**Archetype Justification**: The application coordinates multi-step workflow execution by scheduling tasks to downstream workers, managing state transitions via a DeciderService, and reconciling workflow state across multiple steps. It is a workflow orchestration engine by design — its primary purpose is to coordinate multi-service workflows with retry, state management, and error handling.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial | Critical |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present | Critical |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present | Critical |
| **Overall** | **1.99 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+2+2+1+2+1+1+1+1+3) / 11 = 16/11 = 1.45
- APP: (4+2+2+3+1+3) / 6 = 15/6 = 2.50
- DATA: (2+3+4+4) / 4 = 13/4 = 3.25
- SEC: (1+1+1+1+2+1+2) / 7 = 9/7 = 1.29
- OPS: (1+1+1+1+2+3+1+2+1) / 9 = 13/9 = 1.44
- Overall: (1.45 + 2.50 + 3.25 + 1.29 + 1.44) / 5 = 9.93/5 = 1.99

---

## Classification

**Tier: Remediation Required**

This repo has 7 High findings, 22 Medium findings, 5 Low findings. The matched rule is: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. With 8 High findings across infrastructure, security, and operations categories, this system requires significant modernization effort before reaching cloud-native readiness.

**Classification Consistency Check:** consistent (V5 band "Needs Work" from score 1.99 ≡ V6 "Remediation Required")

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q3: API Authentication | 1 | No authentication or authorization on any API endpoint | Critical security vulnerability — server is completely open to any caller |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files exist (no Terraform, CloudFormation, CDK, Helm) | Cannot reproduce infrastructure; manual/ClickOps deployment; no DR capability |
| 3 | SEC-Q5: Secrets Management | 1 | All secrets via environment variables with no managed secrets service | No rotation, no audit trail, credential sprawl risk |
| 4 | INF-Q1: Managed Compute | 1 | No managed compute defined; only Docker Compose for local dev | Cannot scale, no auto-healing, no production-grade deployment |
| 5 | OPS-Q1: Distributed Tracing | 1 | No tracing SDK or trace propagation across service boundaries | Cannot diagnose latency or failures in distributed workflow execution |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions CI workflows are well-structured with build, test, and publish stages.
- **What it enables:** An agent that triggers deployments, checks build status, manages releases, and monitors pipeline health.
- **Additional steps:** Expose GitHub Actions API or integrate with a webhook-based trigger mechanism.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. The repo contains extensive README files, JSON schemas for workflows/tasks, protocol buffer definitions, and inline configuration documentation.
- **What it enables:** A knowledge agent that indexes the workflow definition schemas, API documentation (auto-generated via SpringDoc), and configuration reference to answer developer questions about workflow authoring and server configuration.
- **Additional steps:** Generate a static OpenAPI spec from the running server to use as the primary corpus alongside the proto definitions and JSON schemas.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** Workflow orchestration in place (INF-Q3 = 2). The system IS a workflow orchestrator with a well-defined execution engine, DeciderService, and queue-based task scheduling.
- **What it enables:** An agent that monitors workflow execution states, identifies stuck workflows, triggers retries, and manages the workflow lifecycle.
- **Additional steps:** Expose the existing REST API (`/api/workflow`) as an agent tool surface. The API already supports operations like retry, restart, rerun, pause, and resume.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2 |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but Dockerfiles exist; contextual guard blocks (containers already present) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (all databases self-managed in Docker Compose) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4=2 but contextual guard blocks (no data processing/analytics workloads detected) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, OPS-Q5=2, OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | AI frameworks already present (Spring AI 1.1.2, Bedrock, 12 LLM providers, MCP, vector DBs) |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a modular monolith (APP-Q2=2) with identifiable modules (48 Gradle subprojects), but all modules are compiled and deployed as a single Spring Boot JAR. Cross-module coupling exists through shared database schemas and the core execution engine. The system uses a queue-based internal decoupling pattern (DECIDER_QUEUE), which is a positive signal for eventual decomposition.

**Compute Model Gaps:** No managed compute infrastructure exists (INF-Q1=1). The application runs via Docker Compose locally and Docker images are published to Docker Hub, but there is no ECS/EKS/Lambda deployment definition.

**Communication Pattern Gaps:** The orchestrator relies on self-managed messaging (Kafka, RabbitMQ, NATS, SQS as pluggable options) but the default deployment uses in-process queues (Redis or SQLite). For an orchestrator archetype, managed async messaging should dominate for fan-out and task distribution (APP-Q3=2).

**Recommended Decomposition Approach:** See Decomposition Strategy section below.

**Representative AWS Services:** EKS (preferred per steering context), Aurora PostgreSQL, Amazon SQS (already supported), EventBridge, API Gateway, Step Functions (for meta-orchestration).

**Recommended Patterns:**
- Strangler Fig: Extract the AI module as an independent service first (it has the clearest bounded context)
- Anti-corruption Layer: Between the core execution engine and extracted services
- Event Sourcing: Leverage the existing event-driven architecture (workflow/task status events)

**Learning Materials:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** All databases are self-managed via Docker Compose — PostgreSQL 16, MySQL, Redis 6.2.3, Elasticsearch 7.17.11, and OpenSearch. No managed database resources are defined in any IaC. The system supports multiple database backends (pluggable persistence), which simplifies migration since connection configuration is centralized.

**Engine Versions and EOL Status:** PostgreSQL 16 (current, DATA-Q3=4), Redis 6.2.3 (approaching EOL), Elasticsearch 7.17.11 (EOL reached). The pluggable architecture means engine migration is a configuration change rather than code change.

**Data Access Patterns:** Mostly centralized with a DAO/repository pattern per persistence module (DATA-Q2=3). Each database backend has its own persistence module with clean interfaces.

**Recommended Managed Database Targets (respecting preferences for Aurora and DynamoDB):**
- PostgreSQL → **Amazon Aurora PostgreSQL** (preferred) — direct migration path, Flyway migrations are compatible
- Redis → **Amazon ElastiCache for Redis** or **MemoryDB** — connection string swap
- Elasticsearch/OpenSearch → **Amazon OpenSearch Service** — already supported via os-persistence modules
- For task queue persistence: Consider **Amazon DynamoDB** (preferred) for high-throughput queue operations

**Representative AWS Services:** Aurora PostgreSQL, ElastiCache, MemoryDB, OpenSearch Service, DynamoDB
**Migration Tools:** AWS DMS for initial data migration; Flyway handles schema management natively.

**Learning Materials:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** No infrastructure as code exists (INF-Q10=1). The repository contains Docker Compose files for local development and CI/CD workflows for building and publishing Docker images, but there is no definition of production infrastructure (networking, compute, databases, monitoring).

**Current CI/CD State:** GitHub Actions provides automated build, test (with JaCoCo coverage), and multi-arch Docker image publishing (INF-Q11=3). The pipeline is well-structured but limited to build and publish — no deployment automation to production environments.

**Deployment Strategy Gaps:** No canary, blue/green, or rolling deployment strategy exists (OPS-Q5=2). Docker images are published but deployment to a target environment is manual.

**Testing Gaps:** Integration tests exist and run in CI via Testcontainers (OPS-Q6=3), but the test-harness module is excluded from the main CI build (`-x :conductor-test-harness:test`), running separately.

**Recommended DevOps Toolchain (respecting preferences for EKS and avoiding self-managed Kubernetes):**
- **IaC:** Terraform or CDK for AWS infrastructure (EKS cluster, Aurora, ElastiCache, networking)
- **Container Orchestration:** Amazon EKS with managed node groups
- **CI/CD Extension:** AWS CodePipeline or GitHub Actions with deployment stages
- **Deployment Strategy:** ArgoCD on EKS for GitOps-based canary deployments
- **Observability IaC:** CloudWatch alarms, dashboards, and log groups defined in Terraform

**Representative AWS Services:** EKS, CodePipeline, CodeBuild, CloudFormation/CDK, CloudWatch
**Learning Materials:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

The application scores APP-Q2=2 (monolith with identifiable modules but shared database schemas and single deployment unit). Although it is internally modular (48 Gradle subprojects with clear package boundaries), all modules compile into a single Spring Boot JAR.

### Recommended Approach: Strangler Fig (Parallel Track)

**Why:** The monolith has well-defined module boundaries (separate Gradle subprojects for each concern — persistence, messaging, AI, REST, gRPC). The pluggable architecture with clean interfaces between modules makes incremental extraction feasible. The team can sustain parallel development because modules are already loosely coupled internally.

**Extraction Priority (highest value first):**
1. **AI Module** — Clearest bounded context with 116 Java files, independent dependencies (Spring AI, vector DBs, LLM providers), and no dependency on the core execution engine state
2. **Metrics/Observability** — Already a separate module; can run as a sidecar or separate service
3. **Event Queue Modules** (Kafka, SQS, AMQP) — Independent messaging adapters that can be extracted as event bridge services

### Pattern Recommendations

| Pattern | Application |
|---------|-------------|
| **Anti-corruption Layer** | Between extracted AI service and core engine — translate between internal task model and AI provider interfaces |
| **Saga Pattern** | For workflow execution spanning multiple extracted services — already naturally supported by the Conductor execution model itself |
| **Event Sourcing** | Leverage existing workflow/task status event publishing (Kafka, SQS publishers already exist) for inter-service communication |
| **Hexagonal Architecture** | Each persistence module already follows this pattern (ports = DAO interfaces, adapters = database-specific implementations) |

### Effort Estimation

| Factor | Signal | Assessment |
|--------|--------|------------|
| Module boundaries | 48 well-defined Gradle subprojects | Low effort — boundaries exist |
| Data coupling | Shared database schemas across persistence modules | Medium effort — need per-service databases |
| Stored procedures | None (DATA-Q4=4) | Low effort — no extraction needed |
| Communication patterns | Queue-based internal decoupling exists | Low-medium effort — already event-driven |
| CI/CD maturity | Automated build + multi-arch Docker publish | Medium effort — need deployment pipeline |
| Test coverage | Integration tests exist but not comprehensive | Medium effort — need cross-service contract tests |

**Estimated Timeline:** Medium to High effort — the modular structure accelerates extraction, but establishing per-service infrastructure (managed databases, networking, observability) requires significant foundation work first.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure is defined. The application is deployed via Docker Compose for local development and Docker images are published to Docker Hub (multi-arch linux/amd64 + linux/arm64). There is no ECS task definition, EKS deployment, Lambda function, or Fargate configuration. |
| **Gap** | All compute is self-managed via Docker containers with no managed orchestration. No auto-healing, no managed scaling, no production deployment target defined. |
| **Recommendation** | Deploy to Amazon EKS (preferred per steering) with managed node groups. Create Kubernetes Deployment manifests for the conductor-server container image. Start with a single EKS service and add HPA for auto-scaling. |
| **Evidence** | `docker/server/Dockerfile`, `docker/docker-compose.yaml`, `.github/workflows/publish.yml` — images published to Docker Hub but no deployment target defined |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed via Docker Compose: PostgreSQL 16, MySQL, Redis 6.2.3, Elasticsearch 7.17.11, OpenSearch. No managed database resources (RDS, ElastiCache, OpenSearch Service) are defined in any infrastructure code. |
| **Gap** | All databases self-managed with no automated failover, no managed backups, no patching automation. Redis 6.2.3 is approaching EOL. Elasticsearch 7 has reached EOL. |
| **Recommendation** | Migrate to Aurora PostgreSQL (preferred), ElastiCache for Redis, and Amazon OpenSearch Service. The pluggable persistence architecture allows connection string configuration changes without code modification. |
| **Evidence** | `docker/docker-compose.yaml` (Redis 6.2.3, ES 7.17.11), `docker/docker-compose-postgres.yaml` (PostgreSQL 16), no `aws_rds_*` or `aws_elasticache_*` resources anywhere |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype-calibrated (orchestrator).** The application IS a workflow orchestrator — it provides workflow orchestration as its core product function via a queue-based DeciderService pattern with reconciliation. However, it does not use a dedicated external orchestration service (Step Functions, Temporal) for its own internal coordination. Internal orchestration is implemented as hardcoded application logic (WorkflowReconciler polling DECIDER_QUEUE, WorkflowExecutor managing state transitions). |
| **Gap** | For an orchestrator archetype, the internal coordination patterns are implemented as custom code rather than leveraging a dedicated orchestration service. The reconciler uses a polling pattern with configurable sweep frequency rather than event-driven triggers. |
| **Recommendation** | The application's primary value IS workflow orchestration, so using an external orchestrator for its own internals may be over-engineering. However, for operational workflows around the system itself (deployment orchestration, data migration coordination, health check workflows), consider using AWS Step Functions. Score reflects that internal coordination has basic structure but uses no dedicated service. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/core/execution/DeciderService.java`, `core/src/main/java/com/netflix/conductor/core/reconciliation/WorkflowReconciler.java` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype-calibrated (orchestrator).** The system supports multiple messaging backends (Kafka, AWS SQS, AMQP/RabbitMQ, NATS) as pluggable event queue modules. However, the Kafka module uses self-managed Kafka (kafka-clients 3.5.1 with no MSK configuration), RabbitMQ is self-managed (AMQP client), and the default deployment uses in-process Redis or SQLite queues. Only the SQS module uses a managed service (AWS SDK v2 2.31.68). |
| **Gap** | For an orchestrator archetype, managed messaging should dominate for fan-out and decoupling. The default deployment relies on self-managed Redis queues. Self-managed Kafka and RabbitMQ options exist but require operational overhead. |
| **Recommendation** | Adopt Amazon SQS (already supported) as the primary event queue for production. For streaming use cases, use Amazon MSK Serverless instead of self-managed Kafka. Configure EventBridge for workflow lifecycle events. Avoid self-managed Kafka (per steering preferences). |
| **Evidence** | `awssqs-event-queue/` (AWS SDK v2), `kafka-event-queue/` (self-managed Kafka client), `amqp/` (self-managed RabbitMQ), `nats/` (self-managed NATS), `docker/docker-compose.yaml` (Redis as default queue) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security configuration exists. No VPC definition, no security groups, no subnet configuration, no NACLs. The Docker Compose files expose ports directly (8000:8080) with no network isolation beyond a Docker bridge network. |
| **Gap** | No production network security defined. Services would be exposed directly without segmentation, private subnets, or least-privilege security groups. |
| **Recommendation** | Define VPC with private subnets for the application and database tiers. Use security groups with least-privilege rules. Place the Conductor server in a private subnet behind an API Gateway or ALB. Use VPC endpoints for AWS service access (SQS, S3, Secrets Manager). |
| **Evidence** | No Terraform, CloudFormation, or CDK files exist. `docker/docker-compose.yaml` uses a flat `internal` Docker network with port exposure. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Docker Compose configuration exposes the application directly on port 8080. The Dockerfile includes nginx as a reverse proxy for the UI, routing `/api/` to the Spring Boot backend and serving static UI assets. However, there is no API Gateway, ALB, or CloudFront as a managed entry point with throttling, authentication, or request validation. |
| **Gap** | Load balancer present (nginx in container) but minimal configuration — no auth, no throttling, no WAF, no rate limiting. |
| **Recommendation** | Deploy API Gateway (preferred per steering) in front of the EKS service. Configure throttling, request validation, and authentication. Alternatively, use an ALB with WAF attached for lower-latency internal routing. |
| **Evidence** | `docker/server/Dockerfile` (nginx installed), `docker/server/nginx/nginx.conf` (reverse proxy), no `aws_api_gateway_*` or `aws_lb_*` resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The Docker Compose files define single instances of each service. No ASG, no ECS service scaling, no HPA, no application auto-scaling policies. The application properties reference configurable thread pools (sweeper threads, queue threads) but these are static. |
| **Gap** | All capacity is statically provisioned. No ability to respond to traffic spikes or scale down during low demand. |
| **Recommendation** | When deployed to EKS, configure Horizontal Pod Autoscaler based on custom metrics (workflow queue depth, task backlog size). Configure Aurora auto-scaling for read replicas. Use KEDA for event-driven scaling based on SQS queue depth. |
| **Evidence** | `docker/docker-compose.yaml` (single instances), `server/src/main/resources/application.properties` (static thread config), no `aws_autoscaling_*` or HPA resources |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. Docker Compose volumes use local driver with no backup strategy. No AWS Backup plans, no RDS backup retention, no S3 versioning, no disaster recovery procedures documented. |
| **Gap** | No automated backups for any data store. A failure would result in complete data loss for workflows, task definitions, and execution history. |
| **Recommendation** | When migrating to Aurora PostgreSQL, enable automated backups with PITR (default 7-day retention). Configure ElastiCache backup with 24-hour retention. Enable OpenSearch Service automated snapshots. Add cross-region backup replication for critical workflow metadata. |
| **Evidence** | `docker/docker-compose.yaml` (local volumes only), no `aws_backup_plan` or `backup_retention_period` anywhere |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. Docker Compose deploys single instances. No AZ specification, no cross-zone load balancing, no multi-AZ database configuration. |
| **Gap** | Single instance deployment — any AZ or host failure takes down the entire system. No automatic recovery. |
| **Recommendation** | Deploy EKS across 2+ AZs with pod anti-affinity rules. Use Aurora PostgreSQL Multi-AZ for database failover. Configure ElastiCache Multi-AZ with automatic failover. Ensure ALB spans all AZs. |
| **Evidence** | `docker/docker-compose.yaml` (single node), no `multi_az` or `availability_zones` configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize files. All infrastructure would need to be created manually (ClickOps) for any deployment beyond local Docker Compose. |
| **Gap** | No reproducible infrastructure. Cannot create consistent environments, cannot perform disaster recovery, cannot track infrastructure changes. |
| **Recommendation** | Create Terraform modules (or CDK stacks) for: EKS cluster, Aurora PostgreSQL, ElastiCache, OpenSearch Service, VPC networking, API Gateway, IAM roles, CloudWatch alarms. Start with a reference architecture module that captures the full stack. |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found anywhere in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides comprehensive CI/CD for application code: automated build with JDK 21, test execution with JaCoCo coverage, multi-arch Docker image publishing (arm64/amd64), Maven Central artifact publishing, and S3 JAR upload. The CI pipeline includes Gradle wrapper validation and caching. However, there is no deployment automation to production environments and no IaC pipeline. |
| **Gap** | CI/CD covers application build and publish but not deployment to a target environment. No IaC automation (because no IaC exists). No automated rollback capability. |
| **Recommendation** | Extend GitHub Actions (or adopt AWS CodePipeline) with deployment stages: deploy to staging EKS → run integration tests → promote to production with canary strategy. Add Terraform plan/apply stages for infrastructure changes. |
| **Evidence** | `.github/workflows/ci.yml` (build + test), `.github/workflows/publish.yml` (Maven Central + Docker Hub multi-arch), `.github/workflows/publish_s3.yaml` (S3 upload) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 21 (current LTS) with Spring Boot 3.3.11 (latest 3.3.x). The project uses Gradle 8.14.3 as the build system. AWS SDK v2 (2.31.68) is used for SQS integration. Frontend uses React 18 with TypeScript and Vite. The language/runtime, framework, and SDK combination represents the current generation across all axes. |
| **Gap** | N/A |
| **Recommendation** | N/A — the technology stack is modern and well-maintained. |
| **Evidence** | `build.gradle` (Java 21, Spring Boot 3.3.11), `dependencies.gradle` (AWS SDK v2 2.31.68), `ui-next/package.json` (React 18, Vite) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a modular monolith with 48 Gradle subprojects providing clear module boundaries (core, persistence, messaging, AI, REST, gRPC, metrics). However, all modules compile into a single Spring Boot JAR (`conductor-server`) for deployment. Modules share database schemas (the same PostgreSQL/MySQL tables are accessed by core, persistence, and indexing modules). The pluggable architecture provides clean interfaces between modules. |
| **Gap** | Single deployable unit despite modular structure. Shared database schemas between modules (workflow tables accessed by core execution, persistence, and indexing). Cannot independently scale or deploy individual modules. |
| **Recommendation** | Begin Strangler Fig extraction starting with the AI module (clearest bounded context, independent dependencies). Establish per-service databases as modules are extracted. The pluggable persistence architecture facilitates this transition. |
| **Evidence** | `settings.gradle` (48 subprojects), `server/build.gradle` (single bootJar), `postgres-persistence/src/main/resources/db/migration_postgres/` (shared schemas) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype-calibrated (orchestrator).** For an orchestrator archetype, async should dominate for fan-out. The system has both sync REST API endpoints (Spring MVC controllers) and async queue-based task distribution internally. However, the default deployment uses synchronous Redis polling for task distribution rather than managed async messaging. External integrations (Kafka, SQS, AMQP) provide async capability but are optional plugins, not the default path. Worker communication is polling-based (workers poll for tasks via HTTP). |
| **Gap** | For an orchestrator, the primary fan-out mechanism (task distribution to workers) relies on workers synchronously polling the server via HTTP rather than event-driven push. The default queue implementation (Redis/SQLite) is synchronous polling, not event-driven. |
| **Recommendation** | Make Amazon SQS the default event queue for production deployments. Implement EventBridge for workflow lifecycle events (started, completed, failed). Consider adopting push-based task notification (SNS → worker) to reduce polling latency and server load. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/controllers/TaskResource.java` (polling endpoint), `awssqs-event-queue/` (async option), `kafka-event-queue/` (async option), default config uses Redis polling |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype-calibrated (orchestrator).** Workflows are inherently long-running and are handled asynchronously with persistent state and queue-based reconciliation. The WorkflowReconciler periodically evaluates workflow state. Workers poll for tasks, execute them asynchronously, and report completion. Workflow state is persisted and can be queried via the REST API (`/api/workflow/{id}`). This is a status-polling pattern by design. |
| **Gap** | Most long-running coordination is async via the queue-based decider pattern. However, some edge cases — specifically, the reconciler relies on a fixed-interval sweep (500ms default) rather than event-driven triggers, introducing latency for state transitions. |
| **Recommendation** | The existing async pattern is appropriate for the orchestrator archetype. Consider replacing the fixed-interval reconciler sweep with event-driven triggers (SQS message → immediate evaluation) to reduce workflow completion latency. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/core/reconciliation/WorkflowReconciler.java` (polling sweep), `core/src/main/java/com/netflix/conductor/core/execution/DeciderService.java` (async state evaluation) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. All REST endpoints use a flat `/api/<resource>` path pattern (e.g., `/api/workflow`, `/api/tasks`, `/api/metadata`). No URL-based versioning (/v1/, /v2/), no version headers, no query parameter versioning. The gRPC services also have no versioning. |
| **Gap** | No versioning — any breaking API change would affect all consumers simultaneously. For a workflow orchestration platform with potentially many external integrations, this is a significant risk. |
| **Recommendation** | Introduce URL-based API versioning (e.g., `/api/v1/workflow`). Start by aliasing current endpoints under `/api/v1/` with backward compatibility. Use API Gateway (preferred per steering) to manage version routing. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/config/RequestMappingConstants.java` (flat `/api/` prefix), no version path segments in any controller |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The system uses environment variables for service endpoint configuration (`VITE_WF_SERVER`, connection strings for databases, Redis hosts). Docker Compose uses Docker DNS for inter-container discovery (service names as hostnames). Configuration properties support environment variable interpolation for all backend endpoints. No hard-coded service endpoints in application code. |
| **Gap** | Environment variables for endpoints but no dynamic discovery service. If deployed to EKS, Kubernetes DNS would provide service discovery, but there is no explicit service discovery mechanism (Cloud Map, Consul) configured. |
| **Recommendation** | When deployed to EKS, leverage Kubernetes DNS for intra-cluster discovery. For cross-cluster or external service communication, use AWS Cloud Map or API Gateway service integrations. |
| **Evidence** | `server/src/main/resources/application.properties` (env var interpolation for all endpoints), `docker/docker-compose.yaml` (Docker DNS service names), `ui-next/.env` (VITE_WF_SERVER env var) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The AI module includes document loading capabilities (`DocumentLoader`, `DocumentAccessPolicy`) for processing unstructured data (PDFs, text files). The `awss3-storage` module provides S3 integration for external payload storage (workflow inputs/outputs that exceed size limits). However, document access is file-system based by default with S3 as an optional external storage backend, not the primary storage layer. |
| **Gap** | Data in managed storage (S3 option exists) but the default document access is local filesystem. No automated parsing pipeline (Textract, Tika integration exists in the AI module via `tika-core` dependency but not as a standalone pipeline). |
| **Recommendation** | Make S3 the default external storage backend for production. Leverage the existing Tika integration in the AI module to build a document parsing pipeline. Consider Amazon S3 File Gateway if filesystem-dependent access patterns cannot be immediately refactored. |
| **Evidence** | `awss3-storage/` module, `ai/src/main/java/org/conductoross/conductor/ai/document/DocumentLoader.java`, `dependencies.gradle` (tika-core 3.2.2) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The system has a mostly centralized data access layer through its pluggable persistence architecture. Each persistence module (postgres-persistence, mysql-persistence, redis-persistence, etc.) implements a common DAO interface defined in the core module. Database access is not scattered — it goes through `ExecutionDAO`, `MetadataDAO`, `QueueDAO`, and `IndexDAO` interfaces. However, the AI module has its own separate vector database access layer (MongoDB, pgvector, Pinecone) that does not go through the main persistence interfaces. |
| **Gap** | Mostly centralized with the AI module's vector database access as an auxiliary path that does not follow the main persistence pattern. |
| **Recommendation** | Maintain the current DAO-interface pattern. When extracting the AI module as a separate service, its vector DB access becomes naturally isolated. No immediate action needed for the main persistence layer. |
| **Evidence** | `core/` (DAO interfaces), `postgres-persistence/`, `mysql-persistence/`, `redis-persistence/` (implementations), `ai/src/main/java/org/conductoross/conductor/ai/vectordb/` (separate access pattern) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Database engine versions are explicitly pinned in Docker Compose files and dependency manifests: PostgreSQL 16 (current), Redis 6.2.3 (pinned in docker-compose), Elasticsearch 7.17.11 (pinned), OpenSearch versions are module-specific (v1, v2, v3 supported). Flyway migrations explicitly target schema versions. The system supports multiple engine versions through separate persistence modules (es6, es7, es8, os, os-v2, os-v3). |
| **Gap** | N/A — versions are explicitly pinned and the system supports current engine versions. Redis 6.2.3 is approaching community EOL but this is a Docker Compose development configuration, not a production pin. |
| **Recommendation** | N/A — version management is well-handled through the pluggable module architecture. |
| **Evidence** | `docker/docker-compose.yaml` (Redis 6.2.3, ES 7.17.11), `docker/docker-compose-postgres.yaml` (PostgreSQL 16), `dependencies.gradle` (revElasticSearch7=7.17.11, revElasticSearch8=8.19.11) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. All 27 SQL migration files contain only DDL (CREATE TABLE, CREATE INDEX, ALTER TABLE) and standard ANSI SQL. Business logic resides entirely in the Java application layer (DeciderService, WorkflowExecutor). One exception: PostgreSQL `NOTIFY` is used for queue change notifications (`V10.1__notify.sql`), but this is a lightweight signaling mechanism, not business logic. |
| **Gap** | N/A |
| **Recommendation** | N/A — the application correctly keeps all business logic in the application layer. |
| **Evidence** | `postgres-persistence/src/main/resources/db/migration_postgres/` (DDL only), `mysql-persistence/src/main/resources/db/migration/` (DDL only), `postgres-persistence/src/main/resources/db/migration_postgres_notify/V10.1__notify.sql` (NOTIFY signal only) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging is configured. The application uses Log4j2 for application-level logging (console appender, INFO level) but there is no infrastructure-level audit trail, no immutable log storage, and no tracking of API calls or administrative actions. |
| **Gap** | No audit logging — cannot trace who performed what actions, when, or from where. No log file validation, no immutable storage. |
| **Recommendation** | Enable CloudTrail for all AWS API calls when deployed to AWS. Configure application-level audit logging for workflow CRUD operations, task assignments, and administrative actions. Ship logs to CloudWatch Logs with retention policies. Use S3 with Object Lock for immutable audit log archive. |
| **Evidence** | `server/src/main/resources/log4j2.xml` (console appender only), no `aws_cloudtrail` resources, no audit logging middleware in REST controllers |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured. Docker Compose volumes use local driver with no encryption. No KMS key references, no encryption configuration on any data store. The Elasticsearch Docker configuration explicitly disables security (`xpack.security.enabled=false`). |
| **Gap** | No encryption at rest for any data store (PostgreSQL, Redis, Elasticsearch, S3 payloads). Workflow execution data, task inputs/outputs, and metadata are stored unencrypted. |
| **Recommendation** | When migrating to managed services: enable Aurora encryption with customer-managed KMS keys, enable ElastiCache encryption at rest, enable OpenSearch Service encryption. For S3 external storage, enable SSE-KMS. Establish a centralized key management policy with documented rotation. |
| **Evidence** | `docker/docker-compose.yaml` (`xpack.security.enabled=false`), no `kms_key_id` references, no encryption configuration in any properties file |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No authentication or authorization exists on any API endpoint. The server is completely open — no Spring Security dependency, no `@EnableWebSecurity`, no SecurityFilterChain, no OAuth2/JWT validation, no API key authentication. Any caller can create/modify/delete workflows, tasks, and metadata without any identity verification. |
| **Gap** | All API endpoints are open — no authentication whatsoever. This is a critical security vulnerability for any production deployment. |
| **Recommendation** | Implement authentication immediately. Options: (1) Deploy API Gateway (preferred per steering) with Cognito authorizer or JWT validation. (2) Add Spring Security with OAuth2 resource server configuration for token validation. (3) At minimum, add API key authentication via API Gateway usage plans. |
| **Evidence** | No `spring-boot-starter-security` in any build.gradle, no `SecurityConfig` or `@EnableWebSecurity` classes, no auth middleware in `rest/` module |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration exists. No Cognito, Okta, OIDC, or SAML configuration. The application does not manage its own authentication either — it simply has none. |
| **Gap** | No identity integration — the application cannot authenticate users or integrate with organizational SSO. |
| **Recommendation** | Integrate with Amazon Cognito (aligned with API Gateway recommendation). Configure OIDC federation with the organization's identity provider. Define RBAC roles for workflow authors, operators, and administrators. |
| **Evidence** | No `aws_cognito_*` references, no OIDC/SAML configuration, no identity provider settings in application.properties |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | All secrets are managed via environment variables with no plaintext credentials in source code. API keys for AI providers use Spring Boot property interpolation from environment variables (e.g., `${OPENAI_API_KEY:}`, `${AWS_ACCESS_KEY_ID:}`). GitHub Actions uses repository secrets for CI/CD credentials (SONATYPE, SIGNING_KEY, DOCKERHUB). The `.env` files contain only non-secret configuration (PORT, VITE_WF_SERVER). No plaintext credentials in version control. |
| **Gap** | No plaintext credentials in source, but production credentials would be kept in environment variables with no rotation, no audit trail, no centralized management. No Secrets Manager or Vault integration exists. |
| **Recommendation** | Integrate with AWS Secrets Manager for all production credentials (database passwords, AI API keys, Redis auth). Configure automatic rotation for database credentials. Use EKS Secrets Store CSI Driver to inject secrets from Secrets Manager into pods. |
| **Evidence** | `server/src/main/resources/application.properties` (env var interpolation: `${OPENAI_API_KEY:}`, `${AWS_ACCESS_KEY_ID:}`), `.github/workflows/publish.yml` (GitHub secrets), `ui/.env` (PORT=5000 only), `ui-next/.env` (non-secret config only) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. The Dockerfile uses `debian:stable-slim` as the base image with no hardening. No vulnerability scanning (Inspector, Snyk, Trivy) is configured. No SSM Patch Manager. The CI Dockerfile uses OpenJDK 17 (legacy, not matching the JDK 21 production target). Positive signal: CVE patches are proactively applied in `build.gradle` (lz4-java, tika-core, commons-beanutils, mssql-jdbc). |
| **Gap** | No vulnerability scanning in CI/CD for container images. No hardened base images (no CIS, no Bottlerocket, no distroless). No runtime patching strategy. |
| **Recommendation** | Switch to a hardened base image (Eclipse Temurin on Alpine or Google Distroless for JRE 21). Add container image scanning (ECR image scanning or Trivy in CI). When deployed to EKS, use Bottlerocket AMIs for nodes. The proactive CVE patching in build.gradle is good — extend this pattern with automated dependency scanning. |
| **Evidence** | `docker/server/Dockerfile` (debian:stable-slim, no hardening), `build.gradle` (CVE patches for lz4-java, tika-core, commons-beanutils, mssql-jdbc), no vulnerability scanning in `.github/workflows/ci.yml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline integrates SonarCloud for code quality analysis (SonarQube token configured in CI workflow). The build.gradle proactively patches CVEs via dependency version forcing (CVE-2025-12183, CVE-2025-66516, CVE-2025-48734, CVE-2025-59250). However, there is no dedicated SAST tool, no container scanning, no `npm audit` or `yarn audit` in the UI pipeline, and no Dependabot configuration. |
| **Gap** | SonarCloud provides some code analysis but no dedicated SAST tool with security rules. No container image scanning. No dependency vulnerability scanning automation (Dependabot, Snyk, npm audit). Manual CVE patching in build.gradle is reactive, not proactive. |
| **Recommendation** | Add Dependabot or Snyk for automated dependency vulnerability alerts. Add Trivy or ECR scanning for container images in CI. Configure SonarCloud security rules as blocking gates for critical findings. Add `yarn audit` step to the UI CI workflow. |
| **Evidence** | `.github/workflows/ci.yml` (SONAR_TOKEN configured), `build.gradle` (CVE version forcing), no `.github/dependabot.yml`, no container scanning step |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, no X-Ray, no Jaeger, no Zipkin. The metrics module supports OTLP metrics export (via Micrometer) but this is metrics-only, not traces. No trace ID propagation headers (traceparent, X-Amzn-Trace-Id) are set or propagated in the REST or gRPC layers. |
| **Gap** | Cannot trace request flows across the workflow execution lifecycle. Cannot correlate workflow execution with task worker activity. For a distributed orchestration engine, this is a critical observability gap. |
| **Recommendation** | Add OpenTelemetry Java Agent (auto-instrumentation) for immediate tracing without code changes. Configure OTLP exporter to AWS X-Ray via the ADOT Collector. Instrument trace context propagation in the task distribution path so worker execution traces are correlated with parent workflow traces. |
| **Evidence** | `metrics/build.gradle` (Micrometer only), `server/src/main/resources/application.properties` (OTLP metrics export disabled by default), no OpenTelemetry SDK in any dependency manifest |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs are defined. The application exposes Prometheus metrics with percentile tracking (p50, p75, p90, p95, p99) via Micrometer, but there are no formal SLO definitions, no error budget tracking, no SLO-based alerts. |
| **Gap** | No formal SLO definitions for workflow execution latency, task scheduling latency, or API response time. Cannot measure whether the system is meeting user expectations. |
| **Recommendation** | Define SLOs for critical user journeys: workflow start-to-complete latency (per workflow type), task scheduling latency (time from schedulable to picked up), API p99 response time. Use CloudWatch or Prometheus with error budget alerting. |
| **Evidence** | `server/src/main/resources/application.properties` (percentile tracking configured), no SLO definition files, no error budget configuration |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The metrics module publishes infrastructure-level metrics via Micrometer (JVM metrics, HTTP request metrics, system metrics). Prometheus endpoint is enabled by default. However, no custom business metrics are published — no workflow completion rates, no task failure rates by type, no worker utilization metrics, no workflow SLA compliance tracking. |
| **Gap** | Infrastructure metrics only. No business outcome metrics that would drive informed modernization and operational decisions. |
| **Recommendation** | Publish custom metrics for: workflows started/completed/failed per type, task scheduling latency percentiles, worker poll frequency and utilization, workflow SLA violations, queue depth trends. Use Micrometer's existing infrastructure to add custom gauges and counters. |
| **Evidence** | `server/src/main/resources/application.properties` (prometheus enabled, actuator endpoints: health, info, prometheus), `metrics/` module (Micrometer registries only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection is configured. Prometheus metrics are exposed but no alerting rules (Prometheus AlertManager rules, CloudWatch alarms, or PagerDuty integration) exist. No composite alarms, no error rate thresholds, no latency anomaly detection. |
| **Gap** | No alerting — operational issues would only be discovered through manual observation or user reports. |
| **Recommendation** | Configure CloudWatch alarms on: API error rate > threshold, workflow failure rate spike, task queue depth exceeding capacity, database connection pool exhaustion. Use CloudWatch Anomaly Detection for latency metrics. Integrate with PagerDuty or OpsGenie for on-call notification. |
| **Evidence** | No CloudWatch alarm definitions, no AlertManager rules, no PagerDuty/OpsGenie configuration, no `aws_cloudwatch_metric_alarm` resources |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker images are published to Docker Hub with version tags and a `latest` tag. The CI/CD pipeline builds and pushes multi-arch images. The Docker Compose HEALTHCHECK provides basic health verification. However, there is no canary, blue/green, or rolling deployment strategy — the published Docker image would be deployed directly to whatever environment consumes it. |
| **Gap** | Rolling deployments with basic health checks (Docker HEALTHCHECK) but no traffic shifting, no canary analysis, no automated rollback. Direct-to-production deployment pattern. |
| **Recommendation** | When deployed to EKS, use ArgoCD with progressive delivery (Argo Rollouts) for canary deployments. Configure automatic rollback on error rate increase. Alternatively, use AWS CodeDeploy with ECS blue/green deployment. |
| **Evidence** | `.github/workflows/publish.yml` (Docker push with version tags), `docker/server/Dockerfile` (HEALTHCHECK configured), no deployment strategy configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist in the `test-harness` module using Testcontainers 1.21.4 for Docker-based database and service testing. The CI pipeline runs integration tests in a separate job (`test-harness`). End-to-end tests exist in the `e2e` module. Functional test profiles are configured (`application-functionaltest.properties`, `application-integrationtest.properties`). LocalStack is used for SQS/S3 integration testing. |
| **Gap** | Integration tests for primary workflows exist; the test-harness runs in CI but is split into a separate job. Some gaps: no contract tests for the gRPC API, no performance/load testing in CI. |
| **Recommendation** | Add gRPC contract tests to validate proto compatibility. Add performance regression tests to CI (JMH benchmarks or Gatling for API load). Consider consolidating the test-harness job into the main CI build for faster feedback. |
| **Evidence** | `test-harness/` (integration tests), `e2e/` (end-to-end tests), `.github/workflows/ci.yml` (separate test-harness job), `dependencies.gradle` (revTestContainer=1.21.4) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks exist. No Systems Manager Automation documents, no Lambda-based remediation, no self-healing patterns. No runbook files (markdown or YAML) for common operational scenarios. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation for common failure modes (stuck workflows, queue backlog, database connection exhaustion). |
| **Recommendation** | Create runbooks for common operational scenarios: stuck workflow recovery (the API already supports retry/restart), queue backlog remediation, database failover procedures. Automate via Systems Manager Automation documents or Step Functions. Implement self-healing for stuck workflows using the existing `WorkflowReconciler` pattern with configurable thresholds. |
| **Evidence** | No runbook files, no SSM documents, no Lambda remediation functions, no self-healing configuration |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application exposes metrics and health endpoints but there is no defined observability ownership. No CODEOWNERS file referencing observability assets, no per-service dashboards, no named alarm owners, no team attribution on monitoring resources. The Prometheus endpoint provides raw metrics without dashboard or alerting ownership. |
| **Gap** | Ad hoc observability — metrics are exposed but no clear ownership, no dashboards, no team attribution. |
| **Recommendation** | Define observability ownership: create Grafana/CloudWatch dashboards for key workflows, assign alarm owners, add CODEOWNERS entries for observability configuration. Establish SRE ownership for the Conductor platform with defined escalation paths. |
| **Evidence** | `server/src/main/resources/application.properties` (prometheus endpoint), no CODEOWNERS file, no dashboard definitions, no alarm owner configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists. Since there is no IaC, there are no AWS resources to tag. Docker images use version tags but not cost/ownership attribution tags. No tagging standard, no tag enforcement, no cost allocation configuration. |
| **Gap** | No tags on any resources. Cannot track costs, cannot identify ownership, cannot enforce budget controls. |
| **Recommendation** | When creating IaC, establish a mandatory tagging policy: `Environment`, `Service`, `Team`, `CostCenter`, `ManagedBy`. Use Terraform `default_tags` on the provider. Enforce via AWS Organizations Tag Policies and Config rules. |
| **Evidence** | No IaC exists — no resources to tag. No tagging standard documented. |

---

## Learning Materials

- **Move to Cloud Native:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Managed Databases:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Modern DevOps:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `build.gradle` | APP-Q1, SEC-Q6, SEC-Q7 | Root build config: Java 21, Spring Boot 3.3.11, CVE patches |
| `dependencies.gradle` | APP-Q1, DATA-Q3, INF-Q4 | Central dependency versions: AWS SDK v2 2.31.68, Spring AI 1.1.2, Testcontainers 1.21.4 |
| `settings.gradle` | APP-Q2 | 48 Gradle subprojects defining module structure |
| `server/src/main/resources/application.properties` | INF-Q4, OPS-Q1, OPS-Q2, OPS-Q3, SEC-Q5 | Application configuration: metrics, AI providers, queue settings |
| `docker/server/Dockerfile` | INF-Q1, INF-Q6, SEC-Q6 | Multi-stage build: JDK 21, nginx, debian:stable-slim base |
| `docker/docker-compose.yaml` | INF-Q1, INF-Q2, INF-Q5, INF-Q7, INF-Q8, INF-Q9 | Default dev stack: Redis 6.2.3, Elasticsearch 7.17.11 |
| `docker/docker-compose-postgres.yaml` | INF-Q2, DATA-Q3 | PostgreSQL 16 development configuration |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline: build, test, coverage, SonarCloud |
| `.github/workflows/publish.yml` | INF-Q1, INF-Q11, OPS-Q5 | Multi-arch Docker publish to Docker Hub + Maven Central |
| `rest/src/main/java/com/netflix/conductor/rest/config/RequestMappingConstants.java` | APP-Q5 | Flat `/api/` prefix with no versioning |
| `core/src/main/java/com/netflix/conductor/core/execution/DeciderService.java` | INF-Q3, APP-Q4 | Workflow state evaluation engine |
| `core/src/main/java/com/netflix/conductor/core/reconciliation/WorkflowReconciler.java` | INF-Q3, APP-Q4 | Queue-based polling reconciliation |
| `awssqs-event-queue/` | INF-Q4 | AWS SQS integration (managed messaging) |
| `kafka-event-queue/` | INF-Q4 | Self-managed Kafka integration |
| `amqp/` | INF-Q4 | Self-managed RabbitMQ integration |
| `postgres-persistence/src/main/resources/db/migration_postgres/` | DATA-Q3, DATA-Q4, APP-Q2 | PostgreSQL DDL migrations (Flyway) |
| `mysql-persistence/src/main/resources/db/migration/` | DATA-Q4 | MySQL DDL migrations (Flyway) |
| `ai/src/main/java/org/conductoross/conductor/ai/` | DATA-Q1, DATA-Q2 | AI module with vector DB access, document loading |
| `test-harness/` | OPS-Q6 | Integration test harness with Testcontainers |
| `e2e/` | OPS-Q6 | End-to-end test suite |
| `metrics/` | OPS-Q1, OPS-Q3 | Micrometer metrics module (14 registries) |
| `server/src/main/resources/log4j2.xml` | SEC-Q1 | Console-only logging configuration |
| `ui/.env` | SEC-Q5 | Non-secret config (PORT=5000) |
| `ui-next/.env` | SEC-Q5, APP-Q6 | Non-secret config (VITE_WF_SERVER) |
