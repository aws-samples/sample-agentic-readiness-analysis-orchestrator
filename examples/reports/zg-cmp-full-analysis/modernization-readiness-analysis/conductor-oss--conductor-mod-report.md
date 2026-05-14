# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | conductor |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | orchestrator (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, workflow, orchestration |
| **Context** | Workflow orchestration engine originally from Netflix. |
| **Overall Score** | 2.01 / 4.0 |

**Archetype Justification**: Conductor is a workflow orchestration engine that coordinates multi-step task execution across distributed workers via pluggable persistence backends (Redis, Postgres, MySQL, Cassandra) and event queues (SQS, Kafka, AMQP, NATS). It manages workflow state, dispatches tasks to workers, and handles retries and timeouts — classic orchestrator signals.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.64 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.14 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **2.01 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure is manually provisioned via Docker Compose or ClickOps. | Blocks reproducible deployments, disaster recovery, and environment consistency. Foundation for all other modernization. |
| 2 | SEC-Q5: Secrets Management | 1 | Hardcoded credentials in Docker Compose files and config properties. No Secrets Manager or Vault integration. | Critical security vulnerability; blocks production-grade deployment and compliance. |
| 3 | INF-Q1: Managed Compute | 1 | No managed compute definitions (ECS/EKS/Lambda/Fargate). Only Docker Compose for local development. | Prevents elastic scaling, increases operational overhead, and blocks containerized deployment to AWS. |
| 4 | SEC-Q3: API Authentication | 1 | No authentication middleware on REST/gRPC endpoints — all APIs are open by default. | Unauthenticated APIs are a critical security vulnerability in any deployment beyond localhost. |
| 5 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group definitions — no network isolation configured. | Services exposed without network controls; no blast radius containment. |

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 2 (≥ 2). SpringDoc/OpenAPI auto-generates API documentation at `/api-docs`. REST controllers return structured JSON responses across all endpoints (Workflow, Task, Metadata, Event, Admin, QueueAdmin, Health).
- **What it enables:** An API-aware agent that discovers and invokes Conductor's REST API as tools — starting workflows, querying task status, managing metadata definitions, and performing bulk operations programmatically.
- **Additional steps:** The auto-generated OpenAPI spec is available at runtime; export it as a static `openapi.json` for agent tool discovery without requiring a running server.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (≥ 2). Conductor uses a well-defined DAO pattern with clean interfaces (ExecutionDAO, MetadataDAO, QueueDAO, IndexDAO, PollDataDAO) and multiple backend implementations.
- **What it enables:** A data query agent that translates natural language queries into structured database lookups — e.g., "find all failed workflows in the last 24 hours" or "show task execution stats for HTTP tasks."
- **Additional steps:** Define a query schema mapping natural language intents to DAO method calls or SQL queries for the chosen backend.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). GitHub Actions CI pipeline exists with build, test, and Docker multi-arch publishing stages.
- **What it enables:** A DevOps agent that triggers CI builds, checks build status, reviews test results, and initiates Docker image publishing via GitHub Actions API.
- **Additional steps:** Create a GitHub App or personal access token for agent API calls to trigger workflow dispatches.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists — `docs/` directory with architecture guides, developer guides, quickstart documentation; `README.md`; `CONTRIBUTING.md`; `ai/README.md` with comprehensive AI module documentation; `schemas/` with JSON schemas; `ROADMAP.md`.
- **What it enables:** A RAG-based knowledge agent using existing documentation as a knowledge base for developer onboarding questions, API usage guidance, and configuration troubleshooting.
- **Additional steps:** Index the documentation corpus using Conductor's own `LLM_INDEX_TEXT` task type with a vector database (pgvector or Pinecone). The AI module already supports this natively.
- **Effort:** Low

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 4 (≥ 2). Conductor IS the workflow orchestration engine — it provides native workflow orchestration with the Decider service, task dispatch, retry logic, and status tracking.
- **What it enables:** A workflow automation agent that monitors workflow executions, detects stuck or failed workflows, automatically retries or restarts them, and reports anomalies to operators.
- **Additional steps:** Define agent-specific workflow definitions that monitor and remediate other workflows — Conductor can orchestrate its own operational workflows.
- **Effort:** Low

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (modular monolith), INF-Q1 = 1 (no managed compute) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1, but Dockerfiles and docker-compose files exist — containerization is already in progress. Contextual guard prevents trigger. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 3 (≥ 3). No commercial database engines detected — all databases (Postgres, MySQL, Redis, Elasticsearch) are open-source. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed in Docker Compose), DATA-Q3 = 2 |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 (≥ 3 with orchestrator archetype calibration). Kafka event-queue module exists but is a pluggable integration, not a self-managed Kafka deployment within the repo's operational scope. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC at all). INF-Q11 = 3 (CI exists but no deployment automation). OPS-Q5 = 1 (no deployment strategy). OPS-Q6 = 3. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context: "Workflow orchestration engine originally from Netflix" contains no AI signal terms. Note: AI module with 12+ LLM providers already exists in codebase. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Conductor is a modular monolith deployed as a single Spring Boot server (`conductor-server`). All 40+ Gradle submodules compile into one `bootJar`. Modules have well-defined boundaries (pluggable persistence, queues, metrics) but share database schemas and are not independently deployable. APP-Q2 scored 2 — identifiable modules with coupling.

**Compute Model Gaps:** INF-Q1 scored 1. No managed compute definitions exist. The repository provides Docker Compose for local development and publishes multi-arch Docker images to Docker Hub, but there is no IaC defining ECS/EKS/Fargate/Lambda workloads.

**Communication Pattern Strengths:** APP-Q3 scored 3 (orchestrator calibration). The workflow engine uses both sync (REST/gRPC) and async (event queues via SQS, Kafka, AMQP, NATS) patterns. For the orchestrator archetype, this is a strong foundation — managed messaging is already architecturally supported.

**Recommended Decomposition Approach:** See the **Decomposition Strategy** section below. The Strangler Fig approach is recommended — extract high-value modules (scheduler, AI module, persistence backends) into independent services while keeping the core workflow engine as the primary service.

**Representative AWS Services:** EKS (preferred per preferences), API Gateway (preferred), EventBridge (preferred), Aurora (preferred for persistence), DynamoDB (preferred for task queues), Step Functions (for orchestrating Conductor's own operational workflows).

**Recommended Patterns:**
- **Strangler Fig** — Incrementally extract modules behind API Gateway
- **Anti-corruption Layer** — Isolate extracted services from monolith data model
- **Event Sourcing** — Workflow state changes as event streams via EventBridge
- **Hexagonal Architecture** — Structure extracted services with clean port/adapter boundaries

**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** All databases are self-managed via Docker Compose:
- **Redis** 6.2.3-alpine — used for persistence, queuing, and locking
- **PostgreSQL** 16 — used for persistence, queuing, external storage, and indexing
- **MySQL** `latest` (no version pin) — used for persistence
- **Elasticsearch** 7.17.11 — used for indexing and search
- **Cassandra** — supported via pluggable persistence module
- **SQLite** — embedded lightweight option

All are running as plain containers with no Multi-AZ, no automated backups, no failover configuration.

**Engine Versions and EOL Status:** DATA-Q3 scored 2. Redis 6.2.3 is past EOL (EOL: March 2024). Elasticsearch 7.17.x is past EOL (August 2023). MySQL uses `latest` tag (unpinned). PostgreSQL 16 is current and supported.

**Data Access Patterns:** DATA-Q2 scored 4. Conductor uses a well-architected DAO pattern with clean interfaces — this is a significant advantage for migration. Each persistence backend is a separate Gradle module implementing the same DAO interfaces, making it straightforward to add managed service backends (e.g., Aurora, DynamoDB, ElastiCache, OpenSearch Service).

**Recommended Managed Database Targets (respecting preferences):**
- **Redis → Amazon ElastiCache for Redis or Amazon MemoryDB** — drop-in replacement for queue and cache layers
- **PostgreSQL → Amazon Aurora PostgreSQL** (preferred) — managed, Multi-AZ, auto-scaling replicas
- **Elasticsearch → Amazon OpenSearch Service** — managed indexing with OpenSearch compatibility (OS persistence modules already exist)
- **MySQL → Amazon Aurora MySQL** (preferred) — managed with automated failover
- **Cassandra → Amazon Keyspaces** — serverless Cassandra-compatible service

**Migration Tools:** AWS Database Migration Service (DMS), AWS Schema Conversion Tool (SCT)

**AWS Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** INF-Q10 scored 1. No Infrastructure as Code exists in the repository — zero Terraform, CloudFormation, CDK, Helm, or Kustomize files. All infrastructure is provisioned via Docker Compose (for local development only) or manually.

**Current CI/CD State:** INF-Q11 scored 3. GitHub Actions provides good CI automation:
- `ci.yml` — builds, runs tests (unit + test-harness), generates JaCoCo coverage, publishes test reports
- `publish.yml` — builds and publishes multi-arch Docker images (amd64/arm64) to Docker Hub on release
- `publish_build.yaml` — builds and publishes server-lite standalone JAR
- `publish_s3.yaml` — publishes server JAR to S3 bucket
- `ui-next-ci.yml` — lints, tests, and builds the UI v2
- Dependabot for Gradle and GitHub Actions dependency updates

However, there is no deployment automation — no CodeDeploy, no ECS/EKS deployment, no environment promotion pipeline.

**Deployment Strategy Gaps:** OPS-Q5 scored 1. Docker images are published but not deployed to any environment. No blue/green, canary, or rolling deployment strategy.

**Testing Gaps:** OPS-Q6 scored 3. Comprehensive test infrastructure exists (Spock/Groovy integration tests, JUnit 5 e2e tests, TestContainers), but some gaps in CI-integrated integration testing coverage.

**Recommended DevOps Toolchain (respecting preferences — prefer EKS, avoid self-managed-kubernetes):**
1. **IaC Foundation:** CDK or Terraform for AWS infrastructure (VPC, EKS cluster, Aurora, ElastiCache, OpenSearch)
2. **Container Orchestration:** EKS (preferred) with managed node groups or Fargate profiles
3. **CI/CD Pipeline:** Extend GitHub Actions with deployment stages — build → test → deploy to staging → integration test → promote to production
4. **Deployment Strategy:** EKS with Argo Rollouts for canary/blue-green deployments
5. **Environment Management:** Separate AWS accounts for dev/staging/prod with CDK environment stacks

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation/CDK, EKS, ECR

**AWS Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Decomposition Strategy

APP-Q2 scored 2 — Conductor is a modular monolith with identifiable module boundaries but shared database schemas and a single deployable unit. Decomposition guidance follows.

### Decomposition Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Conductor's modular Gradle structure makes this feasible. Extract modules like `scheduler`, `ai`, and individual persistence backends into independent services. The core workflow engine continues running while services are extracted. | **Medium to High** — 6-18 months. Each module extraction is a bounded effort due to well-defined DAO interfaces. | ✅ **Recommended.** Conductor's pluggable architecture (DAO interfaces, event queue abstractions) provides natural seams for extraction. Lowest risk. |
| **Conditional / Adaptive** | Containerize the monolith on EKS first (the Docker image already exists), then selectively extract high-value modules (e.g., AI module, scheduler) based on scaling needs. | **Low to Medium** — EKS deployment in 2-4 weeks; selective extraction over 3-12 months. | ✅ **Recommended for immediate action.** Deploy the existing Docker image to EKS, then extract modules that need independent scaling. |
| **Big-Bang Rewrite** | Not applicable. Conductor's codebase is well-structured with clear module boundaries, extensive tests, and active development. | **Very High** — 12-24+ months. | ⚠️ **Not recommended.** The modular monolith structure supports incremental extraction — a rewrite would discard significant value. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's shared database schemas. | Every extraction — place an ACL between the new service and the monolith. Conductor's DAO interfaces already serve as natural ACL boundaries. |
| **Saga Pattern** | Manage distributed transactions that span workflow execution and task dispatch. | When extracting the scheduler or task dispatch service — workflow state changes currently happen in a single transaction. |
| **Event Sourcing** | Capture workflow state changes as events via EventBridge (preferred). | When extracting the event listener modules — the `workflow-event-listener` and `task-status-listener` already emit events. |
| **Hexagonal Architecture** | Structure each extracted service with ports/adapters. | Every new service. Conductor's existing DAO/interface pattern is already hexagonal in nature. |

### Effort Estimation Factors (Calibrated to Conductor)

| Factor | Current State | Effort Signal |
|--------|--------------|---------------|
| Module boundaries | Well-defined Gradle modules with DAO interfaces | **Low effort** — natural extraction seams exist |
| Data coupling | Shared database schemas across persistence modules | **Medium effort** — DAO interfaces abstract the coupling, but schema separation requires migration |
| Stored procedures | Minimal (triggers for queue notifications, index maintenance) | **Low effort** — most business logic in Java application layer |
| Communication patterns | Both sync (REST/gRPC) and async (SQS, Kafka, AMQP, NATS) | **Low effort** — async foundation already exists |
| CI/CD maturity | CI exists but no deployment pipeline | **Medium effort** — deployment automation must be built |
| Test coverage | Extensive (Spock, JUnit 5, TestContainers, e2e) | **Low effort** — regression risk is well-managed |

**Calibrated Estimate:** The Conditional/Adaptive approach is recommended as Phase 1 (2-4 weeks to deploy on EKS), followed by Strangler Fig extraction of the AI module and scheduler as Phase 2 (3-6 months per module).

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute (ECS, EKS, Lambda, Fargate) definitions found. The repository provides Docker Compose files for local development (self-managed containers for Redis, Elasticsearch, Postgres, MySQL) and a multi-stage Dockerfile that packages the server as a Docker image (`debian:stable-slim` base). CI publishes multi-arch Docker images to Docker Hub. All compute is container-based but self-managed — no cloud-native orchestration. |
| **Gap** | No managed compute infrastructure defined. Docker images are published but not deployed to any managed service. |
| **Recommendation** | Deploy the existing Docker image to Amazon EKS (preferred per preferences) with managed node groups or Fargate profiles. Create IaC (CDK or Terraform) defining EKS cluster, ECR repository, and task definitions. |
| **Evidence** | `docker/server/Dockerfile`, `docker/docker-compose.yaml`, `docker/docker-compose-postgres.yaml`, `docker/docker-compose-mysql.yaml`, `.github/workflows/publish.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed in Docker Compose containers: Redis 6.2.3-alpine, Elasticsearch 7.17.11, PostgreSQL 16, MySQL `latest`. No AWS managed database resources (RDS, Aurora, DynamoDB, ElastiCache, OpenSearch Service) defined in IaC. Pluggable persistence modules exist for Redis, Postgres, MySQL, Cassandra, SQLite, and Elasticsearch/OpenSearch — but all run as self-managed containers. |
| **Gap** | Every database is self-managed with no automated failover, no managed patching, and no automated backups. |
| **Recommendation** | Migrate to managed databases: Redis → ElastiCache, PostgreSQL → Aurora PostgreSQL (preferred), MySQL → Aurora MySQL (preferred), Elasticsearch → OpenSearch Service. Conductor's DAO abstraction layer makes this migration straightforward — implement new persistence modules targeting managed service endpoints. |
| **Evidence** | `docker/docker-compose.yaml`, `docker/docker-compose-postgres.yaml`, `docker/docker-compose-mysql.yaml`, `redis-persistence/`, `postgres-persistence/`, `mysql-persistence/`, `cassandra-persistence/`, `es7-persistence/`, `os-persistence/` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Conductor IS the workflow orchestration engine. It provides comprehensive workflow orchestration with: DeciderService for workflow state evaluation, WorkflowExecutor for workflow lifecycle management, AsyncSystemTaskExecutor for async task dispatch, built-in retry and timeout logic, durable execution with persistent state, task queuing and dispatch to distributed workers. This is the core value proposition of the software — it IS the orchestration service. |
| **Gap** | N/A — Conductor natively provides workflow orchestration at the highest maturity level. |
| **Recommendation** | No action needed. Consider using AWS Step Functions for orchestrating Conductor's own operational workflows (backup, scaling, monitoring) while Conductor handles business workflow orchestration. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutor.java`, `core/src/main/java/com/netflix/conductor/core/execution/DeciderService.java`, `core/src/main/java/com/netflix/conductor/core/execution/AsyncSystemTaskExecutor.java` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Conductor supports multiple managed and self-managed messaging backends via pluggable event queue modules: SQS (`awssqs-event-queue/` with AWS SDK v2), Kafka (`kafka-event-queue/`), AMQP (`amqp/`), NATS (`nats/`, `nats-streaming/`). The default event queue type is SQS (see `application.properties`: `conductor.default-event-queue.type=sqs`). Internal task dispatch uses Redis or Postgres queues. For the orchestrator archetype, the architecture has managed messaging for key flows (SQS default) but Kafka integration is self-managed (no MSK references). |
| **Gap** | Kafka integration uses self-managed client configuration with no MSK or managed Kafka references. AMQP and NATS are also self-managed. |
| **Recommendation** | For production AWS deployment, use SQS (already the default) or EventBridge (preferred per preferences) for event queues. If Kafka is required, use Amazon MSK Serverless instead of self-managed Kafka (avoid self-managed-kafka per preferences). |
| **Evidence** | `awssqs-event-queue/build.gradle`, `kafka-event-queue/`, `amqp/`, `nats/`, `server/src/main/resources/application.properties` (line: `conductor.default-event-queue.type=sqs`) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL definitions found — no IaC exists. Docker Compose uses a flat `internal` network with services directly linked. No network segmentation between application and database tiers. Server exposes HTTP port 8080 mapped to host port 8000. |
| **Gap** | No network isolation or segmentation. All services on a flat network with no security groups or private subnets. |
| **Recommendation** | Define VPC with private subnets for databases and application tier. Use security groups with least-privilege rules. Deploy Conductor behind API Gateway (preferred) with VPC endpoints for AWS services. Consider VPC Lattice for service-to-service communication. |
| **Evidence** | `docker/docker-compose.yaml` (networks: internal), absence of any `.tf`, CloudFormation, or CDK files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync defined. The Conductor server exposes HTTP port 8080 directly. Docker Compose maps it to host port 8000. SpringDoc/OpenAPI is present at `/api-docs` for API documentation but there is no managed entry point with throttling, authentication, or request validation. Nginx is bundled in the Docker image for UI serving only. |
| **Gap** | Services exposed directly with no managed API gateway or load balancer providing throttling, auth, or validation. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) in front of the Conductor REST API. Configure throttling, request validation, and API key management. Use ALB for internal gRPC traffic. |
| **Evidence** | `docker/server/Dockerfile` (EXPOSE 8080), `docker/docker-compose.yaml` (ports: 8000:8080), `server/build.gradle` (springdoc dependency) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No ASG, ECS service scaling, EKS HPA, Lambda concurrency, DynamoDB auto-scaling, or Aurora auto-scaling defined. Docker Compose runs fixed-count containers with no scaling mechanism. |
| **Gap** | All capacity is statically provisioned. No dynamic scaling for compute or data layers. |
| **Recommendation** | When deployed to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on CPU/memory and custom metrics (workflow queue depth). Configure auto-scaling on Aurora replicas and ElastiCache nodes. |
| **Evidence** | Absence of any auto-scaling configuration in all files scanned |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. Docker Compose databases use local Docker volumes with no backup automation. No `aws_backup_plan`, no `backup_retention_period`, no PITR configuration. Redis is configured with `appendonly yes` (AOF persistence) but no backup export. No restore procedures documented. |
| **Gap** | No automated backups, no PITR, no restore procedures. Data loss is unrecoverable. |
| **Recommendation** | When migrating to managed databases: enable automated backups on Aurora (35-day retention), enable PITR on DynamoDB, configure ElastiCache daily snapshots. Create AWS Backup plan for cross-service backup orchestration. Document and test restore procedures. |
| **Evidence** | `docker/server/config/redis.conf` (appendonly yes), absence of backup configuration in all files scanned |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Multi-AZ or high availability configuration found. Docker Compose runs all services in single containers. No multi-replica configurations, no cross-AZ distribution, no load balancer health checks with failover. Elasticsearch runs in `discovery.type=single-node` mode. |
| **Gap** | All resources in a single container instance. No fault isolation or AZ redundancy. |
| **Recommendation** | When deployed to EKS, run at least 2 replicas across 2+ AZs. Configure Aurora Multi-AZ. Use ElastiCache with Multi-AZ enabled. Configure OpenSearch Service with multi-AZ domain. |
| **Evidence** | `docker/docker-compose.yaml` (single containers for all services, ES: `discovery.type=single-node`) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code found. Zero Terraform files (`.tf`), zero CloudFormation templates, zero CDK stacks, zero Helm charts, zero Kustomize files, zero Kubernetes manifests. Docker Compose files exist for local development but do not constitute production IaC. All production infrastructure would need to be created manually. |
| **Gap** | 0% IaC coverage. All infrastructure is manually provisioned (ClickOps). |
| **Recommendation** | Create IaC using CDK (Java, aligning with the codebase language) or Terraform for the full infrastructure stack: VPC, EKS cluster (preferred), Aurora PostgreSQL (preferred), ElastiCache, OpenSearch Service, API Gateway (preferred), IAM roles, CloudWatch alarms, and Backup plans. |
| **Evidence** | Absence of any `.tf`, `cdk.json`, `template.yaml`, `Chart.yaml`, `kustomization.yaml` files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides comprehensive CI automation: `ci.yml` (build, test, JaCoCo coverage, test reports for all submodules + separate test-harness job + UI build with Cypress E2E/component tests), `publish.yml` (multi-arch Docker image build and push to Docker Hub on release), `publish_build.yaml` (server-lite standalone JAR build and GitHub Release upload), `publish_s3.yaml` (JAR upload to S3), `ui-next-ci.yml` (UI v2 lint, format, typecheck, test, build). Dependabot configured for Gradle and GitHub Actions. Release Drafter for automated release notes. However, there is no deployment automation — images are published but not deployed to any environment. No automated rollback capability. |
| **Gap** | CI is strong but CD (deployment) is missing. No deployment to staging/production environments. No automated rollback. |
| **Recommendation** | Extend GitHub Actions with deployment stages: deploy to EKS staging after image publish, run integration tests against staging, promote to production with canary deployment via Argo Rollouts. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/publish.yml`, `.github/workflows/publish_build.yaml`, `.github/workflows/publish_s3.yaml`, `.github/workflows/ui-next-ci.yml`, `.github/dependabot.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is Java 21 with Spring Boot 3.3.11 — first-class AWS SDK coverage, the most mature cloud-native ecosystem, extensive framework support. Secondary languages: Groovy 4.0.21 (Spock tests), JavaScript/TypeScript (React UI and Next.js UI v2). Java 21 uses modern features (records, pattern matching, virtual threads support). Spring Boot provides auto-configuration, actuator, and comprehensive cloud integration. |
| **Gap** | None. Java 21 with Spring Boot 3.3 is the gold standard for cloud-native JVM development. |
| **Recommendation** | No language change needed. Ensure Graviton (ARM64) optimization is leveraged — the Docker image already supports `linux/arm64` builds. |
| **Evidence** | `build.gradle` (Java 21 toolchain, Spring Boot 3.3.11), `dependencies.gradle`, `server/build.gradle`, `ui/` (JavaScript/React), `ui-next/` (TypeScript/Next.js), `test-harness/build.gradle` (Groovy/Spock) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Conductor is a modular monolith deployed as a single Spring Boot application (`conductor-server`). All 40+ Gradle submodules compile into one `bootJar`. Module boundaries are well-defined with pluggable architecture: persistence (8 backends via DAO interfaces), event queues (5 backends via pluggable providers), metrics (14 registries), external storage (3 backends). However, all modules share the same JVM process, database schemas are shared across persistence modules (same tables used by all operations), and modules have direct in-process dependencies via Gradle `implementation project()` references. |
| **Gap** | Single deployable unit with shared database schemas. Modules cannot be independently scaled or deployed. The AI module, scheduler, and core engine all run in the same process despite having different scaling characteristics. |
| **Recommendation** | Begin with Conditional/Adaptive approach — deploy the monolith to EKS as-is, then use Strangler Fig to extract high-value modules (AI module, scheduler) into independent services. Conductor's DAO interfaces provide natural extraction seams. See Decomposition Strategy section. |
| **Evidence** | `settings.gradle` (40+ modules), `server/build.gradle` (all modules as dependencies in one bootJar), `core/src/main/java/com/netflix/conductor/dao/` (shared DAO interfaces) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Conductor uses a mix of synchronous and asynchronous communication patterns appropriate for its orchestrator archetype. Synchronous: REST API (Spring MVC controllers in `rest/`), gRPC API (`grpc-server/`). Asynchronous: event queues for workflow/task events (SQS, Kafka, AMQP, NATS), internal task dispatch via Redis/Postgres queues, workflow-event-listener and task-status-listener for async event propagation. For the orchestrator archetype, the primary workflow coordination uses managed messaging (SQS default) for fan-out, with sync reserved for API reads — this is the correct pattern. |
| **Gap** | Some fan-out paths still use synchronous HTTP (e.g., HTTP task execution calls external services synchronously). Internal module communication is in-process (not a gap for a monolith, but becomes one during decomposition). |
| **Recommendation** | When extracting services, ensure inter-service communication uses EventBridge (preferred) for event propagation and SQS for task dispatch. Maintain REST/gRPC for synchronous API reads. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/controllers/`, `grpc-server/`, `awssqs-event-queue/`, `kafka-event-queue/`, `workflow-event-listener/`, `task-status-listener/`, `server/src/main/resources/application.properties` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Conductor is specifically designed for long-running process handling — this is its core purpose. Workflows can span hours, days, or weeks with durable execution. The engine provides: async task dispatch to distributed workers with polling, task status tracking with callbacks (`WorkflowExecutor.updateTask()`), configurable task timeouts and retry policies, workflow-level timeouts, pause/resume/restart capabilities, persistent state across restarts, status polling APIs (`GET /workflow/{id}`). The AI module also implements async video generation with job polling (GENERATE_VIDEO task). |
| **Gap** | None. Long-running process handling is the primary design goal of the software. |
| **Recommendation** | No action needed. This is a mature, battle-tested implementation originally from Netflix. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutor.java`, `core/src/main/java/com/netflix/conductor/core/execution/AsyncSystemTaskExecutor.java`, `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `ai/README.md` (GENERATE_VIDEO async polling) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API versioning is partially implemented. Workflow definitions have explicit version fields (`version` parameter in `WorkflowResource` and `MetadataResource`). The REST API uses a flat URL structure (`/api/workflow`, `/api/tasks`, `/api/metadata`) without URL-path versioning (no `/v1/`, `/v2/` prefixes). SpringDoc/OpenAPI auto-generates API documentation at `/api-docs`. JSON schemas exist in `schemas/` directory (Task.json, TaskDef.json, Workflow.json, WorkflowDef.json) providing data contract definitions. However, the API endpoints themselves lack a consistent versioning strategy — there are no version headers or URL prefixes for the REST API surface. |
| **Gap** | No URL-path or header-based versioning on the REST API. Breaking changes could affect all consumers simultaneously. |
| **Recommendation** | Implement URL-path versioning (e.g., `/api/v1/workflow`) when deploying behind API Gateway (preferred). Use API Gateway stages for version management. Maintain backward compatibility with the current unversioned paths via API Gateway route mappings. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (`@RequestMapping(WORKFLOW)`), `schemas/`, `server/build.gradle` (springdoc-openapi dependency) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables and configuration properties. Docker Compose uses link aliases for service discovery (`conductor-redis:rs`, `conductor-elasticsearch:es`, `conductor-postgres:postgresdb`). Configuration properties reference hostnames via environment variables (e.g., `conductor.redis.hosts=rs:6379:us-east-1c`, `spring.datasource.url=jdbc:postgresql://postgresdb:5432/postgres`). No dynamic service discovery (no AWS Cloud Map, no Consul, no Istio, no Kubernetes service discovery). Eureka client dependency exists in `dependencies.gradle` (`revEurekaClient = '2.0.2'`) but is not actively wired into the server. |
| **Gap** | Static endpoint configuration via environment variables. No dynamic service discovery for runtime routing or failover. |
| **Recommendation** | When deployed to EKS, use Kubernetes service discovery natively. For AWS-native discovery, use AWS Cloud Map or API Gateway service integrations. For the monolith, service discovery is less critical — it becomes essential during decomposition. |
| **Evidence** | `docker/docker-compose.yaml` (links), `docker/server/config/config-redis.properties` (static hostnames), `dependencies.gradle` (revEurekaClient), `server/src/main/resources/application.properties` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | S3 integration exists via the `awss3-storage` module for external payload storage (using AWS SDK v2 `software.amazon.awssdk:s3`). This is used for storing large workflow inputs/outputs that exceed inline payload limits. Azure Blob storage is also supported (`azureblob-storage/`). A Postgres-based external storage module exists as well (`postgres-external-storage/`). The AI module adds document parsing capabilities via Spring AI document readers (PDF, Tika, Markdown, Jsoup). However, there is no automated parsing pipeline — S3 is used for raw storage without extraction or indexing of unstructured content. |
| **Gap** | S3 storage exists but no automated parsing or extraction pipeline for stored documents. |
| **Recommendation** | Leverage the AI module's document reader capabilities (Spring AI Tika, PDF reader) to build parsing workflows that extract and index unstructured content stored in S3. Use Conductor's own workflow engine to orchestrate the parsing pipeline. |
| **Evidence** | `awss3-storage/build.gradle`, `azureblob-storage/`, `postgres-external-storage/`, `ai/build.gradle` (spring-ai-tika-document-reader, spring-ai-pdf-document-reader) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Conductor implements an exemplary unified data access layer. The `core/` module defines clean DAO interfaces: `ExecutionDAO` (workflow/task execution state), `MetadataDAO` (workflow/task definitions), `QueueDAO` (task queuing), `IndexDAO` (search/indexing), `PollDataDAO` (worker poll tracking), `EventHandlerDAO` (event handler configuration), `ConcurrentExecutionLimitDAO`, `RateLimitingDAO`. Each interface has multiple backend implementations in separate Gradle modules: Redis, Postgres, MySQL, Cassandra, SQLite, Elasticsearch, OpenSearch. This is a textbook example of the repository pattern with clean separation of concerns. |
| **Gap** | None. This is a best-practice implementation of a unified data access layer. |
| **Recommendation** | No action needed. This architecture is a significant asset for modernization — adding new managed service backends (Aurora, DynamoDB, ElastiCache) requires implementing the same DAO interfaces without changing any business logic. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/dao/` (8 DAO interfaces), `redis-persistence/`, `postgres-persistence/`, `mysql-persistence/`, `cassandra-persistence/`, `sqlite-persistence/`, `es7-persistence/`, `os-persistence/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database engine versions are partially pinned in Docker Compose: Redis 6.2.3-alpine (pinned, but past EOL — Redis 6.2 EOL March 2024), Elasticsearch 7.17.11 (pinned, but past EOL — ES 7.x EOL August 2023), PostgreSQL 16 (pinned, currently supported), MySQL `latest` (NOT pinned — uses unpredictable latest tag). The codebase supports multiple Elasticsearch/OpenSearch versions (ES 6, 7, 8, OS 1, 2, 3 persistence modules). Flyway manages schema versions for Postgres and MySQL. No documented version-update procedure exists. |
| **Gap** | Redis 6.2.3 and Elasticsearch 7.17 are past EOL. MySQL uses unpinned `latest` tag. No version update procedure documented. |
| **Recommendation** | Pin MySQL to a specific version (e.g., 8.0.x or 8.4.x). Upgrade Redis to 7.x (supported). Migrate Elasticsearch to OpenSearch Service (managed, OS persistence modules already exist). When deploying to AWS, use Aurora PostgreSQL, ElastiCache Redis 7.x, and OpenSearch Service — all with automated version management. |
| **Evidence** | `docker/docker-compose.yaml` (redis:6.2.3-alpine, elasticsearch:7.17.11), `docker/docker-compose-postgres.yaml` (postgres:16), `docker/docker-compose-mysql.yaml` (mysql:latest), `es6-persistence/`, `es7-persistence/`, `es8-persistence/`, `os-persistence/`, `os-persistence-v2/`, `os-persistence-v3/` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Business logic is primarily in the Java application layer via DAO implementations. SQL migration files are mostly DDL (CREATE TABLE, CREATE INDEX). Minimal stored procedure usage found: Postgres has a `queue_notify_trigger()` function and triggers for queue notifications (`V10.1__notify.sql`) and poll data validation (`V10__poll_data_check.sql`). MySQL has utility stored procedures for schema migration (`DropIndexIfExists`, `FixPkIfNeeded` in `V8__update_pk.sql`). The external Postgres storage module has a trigger for row management. These are infrastructure-level triggers/functions, not business logic. No proprietary SQL constructs (T-SQL, PL/SQL) detected — all SQL is standard PostgreSQL and MySQL syntax. |
| **Gap** | Minor — a few infrastructure triggers exist but all business logic is in the application layer. |
| **Recommendation** | No significant action needed. The few triggers (queue notification, poll data validation) can be replaced with application-level event handling when migrating to managed databases. No stored procedure extraction is required. |
| **Evidence** | `postgres-persistence/src/main/resources/db/migration_postgres_notify/V10.1__notify.sql`, `postgres-persistence/src/main/resources/db/migration_postgres/V10__poll_data_check.sql`, `mysql-persistence/src/main/resources/db/migration/V8__update_pk.sql`, `postgres-persistence/src/main/resources/db/migration_postgres/V1__initial_schema.sql` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration exists (no IaC). Application-level logging uses Log4j2 with configurable appenders (console + rolling file in `docker/server/config/`). Workflow and task execution events are logged but there is no immutable audit trail. No CloudTrail, no S3 Object Lock for logs, no CloudWatch log retention policies defined. |
| **Gap** | No audit logging infrastructure. Application logs exist but are not immutable or centralized. |
| **Recommendation** | When deployed to AWS, enable CloudTrail with log file validation and S3 Object Lock. Configure centralized logging via CloudWatch Logs or OpenSearch Service. Set log retention policies. |
| **Evidence** | `docker/server/config/log4j.properties`, `docker/server/config/log4j-file-appender.properties`, absence of `aws_cloudtrail` in any IaC |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured. Docker Compose databases run without encryption — no KMS keys, no EBS encryption, no S3 server-side encryption defined. No `kms_key_id` references in any configuration. The application stores workflow state, task data, and potentially sensitive payload data without any at-rest encryption. |
| **Gap** | No encryption at rest on any data store. |
| **Recommendation** | When migrating to managed databases, enable encryption with customer-managed KMS keys: Aurora encryption, ElastiCache encryption at rest, OpenSearch domain encryption, S3 SSE-KMS for payload storage. Define a centralized key management policy. |
| **Evidence** | Absence of KMS configuration in all files scanned, `docker/docker-compose.yaml` (no encryption settings) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No authentication middleware found on REST or gRPC endpoints. REST controllers in `rest/src/main/java/com/netflix/conductor/rest/controllers/` use plain `@RestController` annotations with no security annotations (`@Secured`, `@PreAuthorize`, etc.). No Spring Security dependency in `server/build.gradle`. No API key validation. No OAuth2/JWT configuration. No Cognito authorizer. All API endpoints are open by default. The `WorkflowContext.java` stores authentication context but no enforcement is visible in the open-source codebase. |
| **Gap** | All API endpoints are unauthenticated. Any network-reachable client can execute workflows, modify metadata, and access task data. |
| **Recommendation** | Implement API authentication immediately: deploy API Gateway (preferred) with Cognito authorizer or Lambda authorizer for JWT validation. Alternatively, add Spring Security with OAuth2 Resource Server configuration to the server module. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `rest/src/main/java/com/netflix/conductor/rest/controllers/TaskResource.java`, `server/build.gradle` (no spring-boot-starter-security), `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration found. No Cognito, Okta, Auth0, Ping, or SAML/OIDC configuration. No SSO. The application has no identity management — it does not authenticate users or services at all. |
| **Gap** | No identity provider integration. Authentication is entirely absent. |
| **Recommendation** | Integrate with Amazon Cognito for user authentication and API authorization. Use Cognito user pools for human users and Cognito identity pools for service-to-service authentication. Configure OIDC/SAML federation for enterprise SSO. |
| **Evidence** | Absence of any identity provider configuration in all files scanned |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Hardcoded credentials found in Docker Compose files: `POSTGRES_PASSWORD=conductor` (docker-compose-postgres.yaml), `MYSQL_ROOT_PASSWORD=12345` and `MYSQL_PASSWORD=conductor` (docker-compose-mysql.yaml). Configuration properties contain plain-text database connection strings: `spring.datasource.username=conductor`, `spring.datasource.password=conductor`. AI provider API keys are read from environment variables with empty defaults (`${OPENAI_API_KEY:}`) — better than hardcoding but no secrets management system. No AWS Secrets Manager or HashiCorp Vault integration found. A document access policy exists for blocking sensitive file paths (application.properties), but secrets themselves are not managed. |
| **Gap** | Critical — database credentials hardcoded in Docker Compose and config files. No secrets management system. |
| **Recommendation** | Migrate all secrets to AWS Secrets Manager with automated rotation. Use Spring Cloud AWS Secrets Manager integration for seamless secret injection. Remove all hardcoded credentials from Docker Compose and config files. For AI provider keys, use Secrets Manager with environment variable injection via EKS pod identity. |
| **Evidence** | `docker/docker-compose-postgres.yaml` (POSTGRES_PASSWORD=conductor), `docker/docker-compose-mysql.yaml` (MYSQL_ROOT_PASSWORD=12345), `docker/server/config/config-postgres.properties` (spring.datasource.password=conductor), `server/src/main/resources/application.properties` (AI key defaults) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy found. The Docker image uses `debian:stable-slim` as the base image with `openjdk-21-jre-headless` installed via `apt-get`. No hardened base image (no Bottlerocket, no CIS-hardened AMI, no distroless). No SSM Patch Manager. No vulnerability scanning (no AWS Inspector, no Snyk container scanning, no Trivy). No EC2 Image Builder pipelines. |
| **Gap** | No patching strategy, no vulnerability scanning, no hardened base images. |
| **Recommendation** | Switch to a hardened base image: use `azul/zulu-openjdk-alpine:21-jre` (smaller attack surface) or `gcr.io/distroless/java21-debian12` (minimal OS). Add container image scanning in CI (Trivy or ECR image scanning). When deployed to EKS, use Bottlerocket AMIs for worker nodes. |
| **Evidence** | `docker/server/Dockerfile` (FROM debian:stable-slim, apt-get install openjdk-21-jre-headless) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependabot configured for Gradle and GitHub Actions dependency updates (weekly schedule). Build.gradle contains CVE-specific version constraints: lz4-java pinned to 1.8.1 (CVE-2025-12183), tika-core pinned to 3.2.2 (CVE-2025-66516), commons-beanutils pinned to 1.11.0 (CVE-2025-48734), mssql-jdbc pinned to 12.8.2 (CVE-2025-59250). SonarCloud cache exists in CI workflow but SONAR_TOKEN appears to be a conditional secret (may not be active). No SAST tool (no Semgrep, no CodeGuru Reviewer). No container image scanning. Gradle wrapper validation is performed in CI. |
| **Gap** | Dependency scanning exists (Dependabot) but no SAST tool and no container scanning. Security gates are not blocking — no PR checks for critical CVEs. |
| **Recommendation** | Add Semgrep or CodeGuru Reviewer for SAST in CI pipeline. Add Trivy or ECR image scanning for container vulnerability detection. Configure Dependabot security alerts to block PRs with critical/high CVEs. Activate SonarCloud for code quality and security analysis. |
| **Evidence** | `.github/dependabot.yml`, `build.gradle` (CVE constraints), `.github/workflows/ci.yml` (SonarCloud cache, Gradle wrapper validation) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry SDK, no X-Ray SDK, no Jaeger or Zipkin dependencies found in any Gradle build files. Micrometer is present for metrics (14 registry implementations) but not configured for tracing. No `traceparent` or `X-Amzn-Trace-Id` header propagation found in source code. |
| **Gap** | No distributed tracing. Debugging cross-service failures (workflow engine ↔ workers ↔ event queues) relies on log correlation only. |
| **Recommendation** | Add OpenTelemetry Java agent or Micrometer Tracing with AWS X-Ray exporter. Instrument the Conductor server and provide trace context propagation to workers via task metadata. Leverage Micrometer's existing metrics infrastructure to add tracing with minimal code changes. |
| **Evidence** | `metrics/build.gradle` (micrometer-core, no micrometer-tracing), `server/build.gradle` (no opentelemetry or xray dependencies), `dependencies.gradle` (no tracing-related dependencies) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No SLO configuration files, no error budget tracking, no formal definition of acceptable service levels. Health endpoint exists (`/health` via Spring Actuator with `show-details=always`). Prometheus metrics endpoint exposed (`management.endpoints.web.exposure.include=health,info,prometheus`). Actuator provides p50/p75/p90/p95/p99 percentile tracking for HTTP requests, but no SLO thresholds are defined against these percentiles. |
| **Gap** | No formal SLO definitions for workflow execution latency, task dispatch time, or API response time. |
| **Recommendation** | Define SLOs for critical user journeys: workflow start-to-complete latency (p99), task dispatch latency (p99), API response time (p95), workflow failure rate. Use CloudWatch Synthetics or Prometheus recording rules to track SLO compliance. Implement error budgets. |
| **Evidence** | `server/src/main/resources/application.properties` (actuator endpoints, percentile config), `rest/src/main/java/com/netflix/conductor/rest/controllers/HealthCheckResource.java` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive business metrics infrastructure exists via Micrometer. The `Monitors.java` class in `core/` provides counters, timers, and gauges for workflow/task-specific metrics: `task_poll`, `task_poll_error`, workflow execution counts, task execution duration, queue depths. `WorkflowMonitor.java` adds workflow-level metrics. The `metrics/` module integrates with 14 metric registries: Prometheus, CloudWatch, Datadog, OTLP, Dynatrace, Elastic, New Relic, Stackdriver, StatsD, InfluxDB, Azure Monitor, JMX, Atlas. Custom business metrics are published alongside infrastructure metrics. However, no dashboards are defined in the repository. |
| **Gap** | Business metrics exist but no pre-built dashboards. Metrics are published but visualization is left to operators. |
| **Recommendation** | Create CloudWatch dashboards (or Grafana dashboards for Prometheus) with workflow throughput, task execution latency, failure rates by workflow type, and queue depth trends. The metrics infrastructure is already excellent — dashboards are the missing piece. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`, `core/src/main/java/com/netflix/conductor/metrics/WorkflowMonitor.java`, `metrics/build.gradle` (14 Micrometer registries), `server/src/main/resources/application.properties` (conductor.metrics-prometheus.enabled=true) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. Docker Compose has basic health checks (`curl http://localhost:8080/health`), Redis health check (`redis-cli ping`), and Elasticsearch health check (`_cluster/health`). Prometheus metrics are exposed but no alerting rules (PrometheusRule, Alertmanager config) are defined. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no composite alarms. |
| **Gap** | No alerting on error rates, latency degradation, or queue depth anomalies. Health checks exist but no proactive alerting. |
| **Recommendation** | Create CloudWatch alarms for: workflow failure rate > threshold, task queue depth growing, API p99 latency degradation, database connection pool exhaustion. Use CloudWatch anomaly detection for error rate and latency baselines. Integrate with SNS → PagerDuty/OpsGenie for incident notification. |
| **Evidence** | `docker/docker-compose.yaml` (healthcheck configurations), absence of alerting rules in all files scanned |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists beyond Docker image publishing. CI builds and publishes multi-arch Docker images to Docker Hub on release, and uploads JARs to S3 and GitHub Releases. But there is no deployment automation to any environment — no CodeDeploy, no ECS/EKS deployment, no blue/green, no canary, no rolling update configuration. Deployment to production is entirely manual. |
| **Gap** | Direct-to-production (manual) deployment with no staged rollout, no traffic shifting, no automated rollback. |
| **Recommendation** | Implement canary deployments on EKS using Argo Rollouts or Flagger. Define deployment pipeline: build → push to ECR → deploy to staging → integration test → promote to production with 10% canary → full rollout. |
| **Evidence** | `.github/workflows/publish.yml` (image publish only, no deployment), `.github/workflows/publish_s3.yaml` (S3 upload only) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Extensive integration test infrastructure: `test-harness/` module with Spock/Groovy integration tests running against a full Conductor server with TestContainers (Redis, Elasticsearch, Postgres, LocalStack for S3/SQS). `e2e/` module with JUnit 5 tests targeting a running Conductor instance. Functional test source set in test-harness compiles and runs e2e tests against an embedded server. CI runs test-harness as a separate job. UI has Cypress E2E and component tests. However, e2e tests are gated by `RUN_E2E=true` environment variable and not run in standard CI builds. Some gaps in coverage for newer modules (AI module, scheduler). |
| **Gap** | e2e tests exist but are not run in standard CI builds (require explicit opt-in). Some newer modules lack integration test coverage. |
| **Recommendation** | Enable e2e tests in CI for at least critical path workflows. Add integration tests for the AI module and scheduler persistence modules. Run integration tests against the staging environment as part of the deployment pipeline. |
| **Evidence** | `test-harness/build.gradle` (Spock, TestContainers, functionalTest source set), `e2e/build.gradle` (JUnit 5, `onlyIf { RUN_E2E }`), `.github/workflows/ci.yml` (test-harness job, build-ui job with Cypress) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks or automated incident response found. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions incident workflows. No runbook files (markdown, YAML, JSON) in the repository. `SECURITY.md` exists but only covers vulnerability reporting, not operational incident response. |
| **Gap** | No runbooks — incident response is entirely ad hoc. |
| **Recommendation** | Create operational runbooks for common incidents: database connection exhaustion, workflow queue backup, worker timeout spikes, Redis memory pressure. Implement self-healing automation using Conductor's own workflow engine to detect and remediate operational issues. |
| **Evidence** | `SECURITY.md` (vulnerability reporting only), absence of runbook files in all directories scanned |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file found. No per-service dashboards. No alarms with named owners. No SLO definitions with team attribution. Prometheus endpoint is available and metrics are comprehensive (Monitors.java), but there is no governance around who owns which metrics, alarms, or dashboards. |
| **Gap** | No observability ownership — monitoring is fragmented with no accountability model. |
| **Recommendation** | Create CODEOWNERS file with team ownership for observability configs. Define per-service dashboards (workflow engine, task dispatch, indexing, AI module). Assign alarm ownership to specific teams. |
| **Evidence** | Absence of CODEOWNERS file, absence of dashboard definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging found. No IaC exists to define tags. No `default_tags`, no `tags` blocks, no Tag Policies, no AWS Config rules for tagging. Docker Compose does not have tagging capability. No cost allocation or ownership attribution infrastructure. |
| **Gap** | No resource tagging — impossible to track costs, ownership, or environment classification. |
| **Recommendation** | When creating IaC, implement a comprehensive tagging strategy with required tags: `Environment`, `Service`, `Owner`, `CostCenter`, `Project`. Use CDK `Tags.of()` or Terraform `default_tags`. Enforce via AWS Config required-tags rule and Tag Policies in AWS Organizations. |
| **Evidence** | Absence of any IaC with tagging configuration |

## Learning Materials

The following learning resources are mapped to the three triggered pathways:

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `build.gradle` | INF-Q11, APP-Q1, SEC-Q7 | Root build configuration — Java 21 toolchain, Spring Boot 3.3.11, CVE version constraints |
| `dependencies.gradle` | APP-Q1, APP-Q6, OPS-Q1 | Centralized dependency versions for all modules |
| `settings.gradle` | APP-Q2 | 40+ Gradle submodule definitions |
| `server/build.gradle` | INF-Q1, INF-Q3, INF-Q4, APP-Q2, APP-Q5, SEC-Q3 | Server module dependencies — all modules compiled into single bootJar |
| `server/src/main/resources/application.properties` | INF-Q4, INF-Q6, APP-Q5, APP-Q6, OPS-Q2, OPS-Q3, SEC-Q5 | Application configuration — event queue defaults, metrics, AI provider keys |
| **Docker** | | |
| `docker/server/Dockerfile` | INF-Q1, INF-Q6, SEC-Q6 | Multi-stage Dockerfile — debian:stable-slim base, JRE 21, nginx |
| `docker/docker-compose.yaml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q9, OPS-Q4, DATA-Q3 | Default Docker Compose — Redis 6.2.3, Elasticsearch 7.17.11 |
| `docker/docker-compose-postgres.yaml` | INF-Q2, DATA-Q3, SEC-Q5 | Postgres Docker Compose — Postgres 16, hardcoded credentials |
| `docker/docker-compose-mysql.yaml` | INF-Q2, DATA-Q3, SEC-Q5 | MySQL Docker Compose — MySQL latest, hardcoded root password |
| `docker/server/config/*.properties` | INF-Q4, SEC-Q5, OPS-Q3 | Runtime configuration for Redis, Postgres, MySQL, Elasticsearch, OpenSearch |
| `docker/server/config/redis.conf` | INF-Q8 | Redis AOF persistence configuration |
| **CI/CD** | | |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline — build, test, coverage, SonarCloud cache |
| `.github/workflows/publish.yml` | INF-Q11, OPS-Q5 | Docker multi-arch image publish to Docker Hub |
| `.github/workflows/publish_build.yaml` | INF-Q11 | Server-lite JAR build and GitHub Release |
| `.github/workflows/publish_s3.yaml` | INF-Q11 | JAR upload to S3 |
| `.github/workflows/ui-next-ci.yml` | INF-Q11 | UI v2 CI pipeline |
| `.github/dependabot.yml` | INF-Q11, SEC-Q7 | Dependabot for Gradle and GitHub Actions |
| **Core** | | |
| `core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutor.java` | INF-Q3, APP-Q4 | Workflow lifecycle management interface |
| `core/src/main/java/com/netflix/conductor/core/execution/DeciderService.java` | INF-Q3 | Workflow state evaluation |
| `core/src/main/java/com/netflix/conductor/core/execution/AsyncSystemTaskExecutor.java` | INF-Q3, APP-Q4 | Async task dispatch |
| `core/src/main/java/com/netflix/conductor/dao/` | APP-Q2, DATA-Q2 | 8 DAO interfaces — unified data access layer |
| `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` | OPS-Q3 | Custom business metrics (counters, timers, gauges) |
| `core/src/main/java/com/netflix/conductor/metrics/WorkflowMonitor.java` | OPS-Q3 | Workflow-level metrics |
| `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java` | SEC-Q3 | Authentication context store (unused) |
| **REST** | | |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` | APP-Q5, SEC-Q3 | REST API — no auth, no URL versioning |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/TaskResource.java` | SEC-Q3 | Task REST API — no auth |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/HealthCheckResource.java` | OPS-Q2 | Health endpoint |
| **Persistence** | | |
| `redis-persistence/` | INF-Q2, DATA-Q2 | Redis persistence backend |
| `postgres-persistence/` | INF-Q2, DATA-Q2, DATA-Q4 | Postgres persistence backend |
| `mysql-persistence/` | INF-Q2, DATA-Q2, DATA-Q4 | MySQL persistence backend |
| `cassandra-persistence/` | INF-Q2, DATA-Q2 | Cassandra persistence backend |
| `sqlite-persistence/` | DATA-Q2 | SQLite persistence backend |
| `postgres-persistence/src/main/resources/db/migration_postgres/` | DATA-Q3, DATA-Q4 | Flyway SQL migrations |
| `postgres-persistence/src/main/resources/db/migration_postgres_notify/V10.1__notify.sql` | DATA-Q4 | Queue notification trigger |
| `mysql-persistence/src/main/resources/db/migration/V8__update_pk.sql` | DATA-Q4 | MySQL utility stored procedures |
| **Event Queues** | | |
| `awssqs-event-queue/` | INF-Q4 | SQS event queue — AWS SDK v2 |
| `kafka-event-queue/` | INF-Q4 | Kafka event queue |
| `amqp/` | INF-Q4 | AMQP event queue |
| `nats/`, `nats-streaming/` | INF-Q4 | NATS event queues |
| **Indexing** | | |
| `es7-persistence/` | INF-Q2, DATA-Q3 | Elasticsearch 7 indexing |
| `os-persistence/`, `os-persistence-v2/`, `os-persistence-v3/` | DATA-Q3 | OpenSearch indexing modules |
| **Storage** | | |
| `awss3-storage/` | DATA-Q1 | S3 external payload storage |
| `azureblob-storage/` | DATA-Q1 | Azure Blob storage |
| `postgres-external-storage/` | DATA-Q1 | Postgres external storage |
| **AI** | | |
| `ai/build.gradle` | Move to AI pathway, DATA-Q1 | Spring AI, Bedrock, 12+ LLM providers, vector DBs |
| `ai/README.md` | APP-Q4, Quick Agent Wins | AI module documentation |
| **Testing** | | |
| `test-harness/build.gradle` | OPS-Q6 | Integration test infrastructure — Spock, TestContainers |
| `e2e/build.gradle` | OPS-Q6 | End-to-end test module |
| **Metrics** | | |
| `metrics/build.gradle` | OPS-Q1, OPS-Q3 | 14 Micrometer metric registries |
| **Other** | | |
| `schemas/` | APP-Q5 | JSON schema definitions for API contracts |
| `docs/` | Quick Agent Wins | Documentation for RAG knowledge base |
| `SECURITY.md` | OPS-Q7 | Vulnerability reporting policy |
| `grpc-server/` | APP-Q3 | gRPC API server |
