# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Flowise |
| **Date** | 2025-07-14 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, ai, llm |
| **Context** | Low-code UI for building LLM flows and agents. |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **2.14 / 4.0** |

**Archetype Justification**: The server owns persistent state via TypeORM (SQLite/PostgreSQL/MySQL/MariaDB) with 19+ database entities, exposes extensive CRUD operations on business entities (chatflows, messages, credentials, tools, variables, etc.), and uses BullMQ for supplementary background job processing. Classified as stateful-crud because it is not primarily an event-processor, orchestrator, data-gateway, or stateless-utility.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.89 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.14 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code — all infrastructure is manually configured or Docker Compose only | Blocks reproducible deployments, disaster recovery, and environment consistency; prerequisite for all modernization pathways |
| 2 | INF-Q1: Managed Compute | 1 | No managed container orchestration (ECS/EKS) or serverless — self-managed Docker Compose only | No auto-scaling, self-healing, or managed upgrades; operational burden increases with scale |
| 3 | INF-Q5: Network Security | 1 | No VPC, subnet, security group, or network segmentation defined | Services exposed without network isolation; blast radius of any compromise is unlimited |
| 4 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption-at-rest configuration for database or storage | Sensitive LLM API keys, credentials, and user data stored without encryption at rest |
| 5 | INF-Q2: Managed Databases | 1 | All databases self-managed — no RDS/Aurora/DynamoDB definitions | Manual patching, backup, scaling; single point of failure without managed failover |

---

## Quick Agent Wins

### 1. API-Aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 3 ≥ 2) AND structured JSON responses detected. OpenAPI 3.0.3 spec exists at `packages/api-documentation/src/yml/swagger.yml` with 2,665 lines covering all `/api/v1/` endpoints. Swagger UI is served via `swagger-ui-express`.
- **What it enables:** An AI agent that discovers and invokes existing Flowise API endpoints as tools — creating chatflows, triggering predictions, managing credentials, and querying chat history programmatically.
- **Additional steps:** The OpenAPI spec is comprehensive. Ensure it stays synchronized with route changes (consider auto-generation from Express routes).
- **Effort:** Low

### 2. Data Query Agent

- **Prerequisite:** Database with clear, documented schema (DATA-Q2 = 3 ≥ 2). TypeORM entities in `packages/server/src/database/entities/` define 19+ entities (ChatFlow, ChatMessage, Credential, Tool, Variable, Dataset, Evaluation, etc.) with typed columns and relations.
- **What it enables:** A natural-language-to-SQL agent that queries Flowise's operational database — "How many chatflows were created this week?", "Show all failed predictions in the last 24 hours", "List credentials expiring soon."
- **Additional steps:** Add a read-only database user for agent queries. Document entity relationships for the agent's context window.
- **Effort:** Medium

### 3. DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2 ≥ 2). GitHub Actions workflows in `.github/workflows/` provide build, test, and Docker image push automation.
- **What it enables:** An agent that triggers Docker image builds, checks CI status, monitors test results, and manages release tagging via GitHub Actions API.
- **Additional steps:** Add GitHub Actions API tokens for agent access. Create workflow dispatch events for agent-triggered deployments.
- **Effort:** Medium

### 4. RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `packages/agentflow/ARCHITECTURE.md`, and the OpenAPI spec provide substantial knowledge corpus.
- **What it enables:** A RAG agent that indexes Flowise documentation and answers developer questions — "How do I configure S3 storage?", "What environment variables control queue mode?", "How do I add a new node type?"
- **Additional steps:** Index `.env.example` files as configuration reference. Consider including the Flowise docs site content for broader coverage.
- **Effort:** Low

### 5. Workflow Automation Agent

- **Prerequisite:** Workflow orchestration in place (INF-Q3 = 2 ≥ 2). BullMQ queues (PredictionQueue, UpsertQueue) with Redis event pub/sub provide the execution surface.
- **What it enables:** An agent that monitors BullMQ queue health, manages stuck jobs, triggers retries, and provides queue analytics — "How many predictions are queued?", "Retry all failed upsert jobs", "What's the average prediction latency?"
- **Additional steps:** Enable the BullMQ dashboard (`ENABLE_BULLMQ_DASHBOARD=true`) and expose queue metrics via the existing Prometheus/OpenTelemetry integration.
- **Effort:** Medium

### 6. Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 3 ≥ 2). OpenTelemetry SDK with auto-instrumentation, Winston structured logging with sanitization, Prometheus and OpenTelemetry metrics providers, and Grafana dashboards.
- **What it enables:** An agent that queries OpenTelemetry traces, correlates logs with prediction failures, identifies slow LLM provider responses, and suggests root causes for degraded performance.
- **Additional steps:** Ensure trace data is exported to a queryable backend (e.g., AWS X-Ray, Jaeger, or Grafana Tempo). Add trace IDs to error responses for correlation.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute), APP-Q3=2 (primarily sync) |
| 2 | Move to Containers | Not Triggered | — | — | Container definitions exist (Dockerfiles, docker-compose). Already containerized; needs managed orchestration (covered by Move to Cloud Native). |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no proprietary SQL); all database engines are open source (SQLite, PostgreSQL, MySQL, MariaDB). |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (all databases self-managed), DATA-Q3=2 (no version pinning) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data analytics/streaming workloads. BullMQ is application-level job processing, not analytics. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), INF-Q11=2 (partial CI/CD), OPS-Q5=1 (no deployment strategy) |
| 7 | Move to AI | Not Triggered | — | — | Extensive AI/agent frameworks already present: LangChain, Bedrock SDK, OpenAI, MCP, vector stores, evaluation tools. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
Flowise is a monolith deployed as a single Docker container (APP-Q2 = 2). The pnpm monorepo has 5 packages (server, ui, components, agentflow, api-documentation), but they deploy as a single unit with a shared database. The server package contains all routes, controllers, services, and business logic in one process. A worker mode exists (BullMQ) that shares the same codebase and database.

**Compute Model Gaps (INF-Q1 = 1):**
All compute runs as self-managed Docker containers via Docker Compose. No ECS, EKS, Lambda, or Fargate definitions exist. No managed container orchestration, no auto-scaling, no health-check-driven replacement.

**Communication Pattern Gaps (APP-Q3 = 2):**
Inter-component communication is primarily synchronous HTTP via Express routes. BullMQ provides async job processing for predictions and upserts, but the standard mode processes everything synchronously. Redis pub/sub is used for SSE event streaming.

**Recommended Decomposition Approach:**
See the Decomposition Strategy section below for detailed approach options. The Conditional/Adaptive approach is recommended — containerize on **Amazon EKS** (per technology preferences) and selectively extract high-value services.

**Representative AWS Services:**
- **Amazon EKS** (preferred) for container orchestration
- **Amazon API Gateway** (preferred) for API entry point with throttling, auth, and request validation
- **Amazon EventBridge** (preferred) for event-driven communication between extracted services
- **AWS Step Functions** for workflow orchestration of multi-step LLM operations
- **AWS Lambda** for lightweight event handlers (where appropriate)

**Recommended Patterns:**
- Strangler Fig pattern for incremental service extraction
- Anti-corruption Layer between monolith and new services
- Event Sourcing for LLM prediction audit trails
- Saga pattern for multi-step chatflow execution workflows

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):**
All databases are self-managed. Flowise supports SQLite (default, local file), PostgreSQL, MySQL, and MariaDB via TypeORM, configured entirely through environment variables. There are no IaC definitions for managed database services. The default SQLite database stores everything in a single file at `~/.flowise/database.sqlite`.

**Engine Versions and EOL Status (DATA-Q3 = 2):**
No database engine versions are pinned in the repository. The `docker-compose-queue-prebuilt.yml` uses `redis:alpine` without a version pin. Database engine versions are determined by the user's deployment, with no lifecycle management.

**Data Access Patterns (DATA-Q2 = 3):**
TypeORM provides a centralized ORM layer. All 19+ entities are defined in `packages/server/src/database/entities/` with typed columns. Migration files exist for all 4 database types in `packages/server/src/database/migrations/`. The data access pattern is clean and well-structured.

**Recommended Managed Database Targets:**
- **Amazon Aurora PostgreSQL** (preferred) — Drop-in replacement for PostgreSQL with managed failover, automated backups, and auto-scaling storage. TypeORM connection requires only changing `DATABASE_HOST` and credentials.
- **Amazon DynamoDB** (preferred) — For high-throughput metadata like chat messages, session state, and API key lookups. Would require refactoring the TypeORM data access layer for DynamoDB.
- **Amazon ElastiCache for Redis** — Managed Redis for BullMQ queues and pub/sub, replacing the self-managed `redis:alpine` container.

**Migration Tools:**
- **AWS Database Migration Service (DMS)** — For migrating from self-managed PostgreSQL/MySQL to Aurora
- **AWS Schema Conversion Tool (SCT)** — Not needed (no schema conversion required; all engines are open source)

**Migration Approach:**
1. Start with Aurora PostgreSQL as the primary database — minimal code changes (connection string update only)
2. Migrate Redis to ElastiCache for Redis — update `REDIS_URL` environment variable
3. Evaluate DynamoDB for high-throughput tables (ChatMessage, Execution) as a second phase

**AWS Prescriptive Guidance:**
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure-as-code exists. All infrastructure configuration is done via Docker Compose files and environment variables. No Terraform, CloudFormation, CDK, Helm charts, or equivalent. The Docker Compose files define only the application runtime, not the underlying infrastructure (VPC, subnets, databases, load balancers).

**Current CI/CD State (INF-Q11 = 2):**
GitHub Actions provides partial automation:
- `main.yml` — Automated build, lint, test (Jest + Cypress e2e) on push/PR to main
- `docker-image-dockerhub.yml` — Manual dispatch (`workflow_dispatch`) to build and push Docker images to DockerHub
- `docker-image-ecr.yml` — Manual dispatch to build and push to AWS ECR
- `publish-agentflow.yml` — Manual dispatch to publish the agentflow package to npm

Build and test are automated; deployment is entirely manual. No automated rollback, no deployment gates, no environment promotion.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
Direct-to-production deployment with no staged rollout. Docker images are pushed manually via workflow dispatch, then deployed by the operator. No canary, blue/green, rolling, or traffic-shifting configuration.

**Recommended DevOps Toolchain:**
- **AWS CDK (TypeScript)** — Natural fit for a TypeScript team. Define VPC, EKS cluster, Aurora, ElastiCache, API Gateway, and all infrastructure as TypeScript code.
- **AWS CodePipeline + CodeBuild** — Automated CI/CD pipeline with build, test, and deploy stages. Integrates with EKS for container deployments.
- **AWS CodeDeploy** — Blue/green or canary deployments for EKS workloads.
- **Amazon EventBridge** (preferred) — Event-driven pipeline triggers on code push, image publish, or deployment completion.

**Implementation Roadmap:**
1. **Week 1-2:** Create CDK project defining VPC, EKS cluster, Aurora PostgreSQL, ElastiCache Redis, and API Gateway
2. **Week 3-4:** Create CodePipeline with automated build → test → deploy stages. Replace manual `workflow_dispatch` with automated triggers.
3. **Week 5-6:** Implement blue/green deployment strategy with CodeDeploy on EKS. Add automated rollback on health check failure.
4. **Week 7-8:** Add Dependabot for dependency scanning, integrate SAST (Semgrep or CodeGuru) into pipeline, and configure ECR image scanning.

**AWS Prescriptive Guidance:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Decomposition Strategy

Since APP-Q2 = 2 (monolith with identifiable modules but shared database), decomposition guidance is applicable.

### Recommended Approach

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping it running. New features as services; existing features migrated over time. | APP-Q2 = 2 — monorepo has recognizable package boundaries (server, components, ui, agentflow). | **Medium to High** — 6-18 months | ✅ Viable for Flowise given the clear package separation. |
| **Conditional / Adaptive** | Containerize on EKS as-is, then selectively extract high-value services. Not all modules need to become services. | Limited capacity; business pressure for quick wins. | **Low to Medium** — containerization in 2-4 weeks, extraction over 3-12 months | ✅ **Recommended.** Flowise is already containerized. Move to EKS first, then extract prediction processing and vector store operations as independent services. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch. | Almost never. | **Very High** — 12-24+ months | ⚠️ **Recommended against.** Flowise is functional and well-structured. Incremental approaches are safer. |

### Candidate Service Extractions

Based on the monorepo's package structure and the domain model:

1. **Prediction Service** — Extract LLM prediction processing (currently in PredictionQueue + inline handlers) into an independent service behind Amazon EventBridge (preferred). This is the highest-value extraction: predictions are long-running, resource-intensive, and independently scalable.
2. **Vector Store Service** — Extract vector upsert and retrieval operations (currently in UpsertQueue + vector store nodes) into a dedicated service. Vector operations have different scaling characteristics than CRUD operations.
3. **Document Processing Service** — Extract document loading and parsing (currently in `packages/components/nodes/documentloaders/`) into an event-driven service triggered by S3 uploads.

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's data model | Every extraction — place between new prediction service and the monolith | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions | When extracting prediction flows that span chatflow loading → credential resolution → LLM invocation → message storage | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture all prediction events as an immutable log | For prediction audit trails and replay capability | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Clear boundaries between business logic, ports, and adapters | Every new service — ensures testability and infrastructure portability | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Assessment | Signal |
|--------|-----------|--------|
| Module boundaries | **Low-Medium Effort** — Clear pnpm package structure with server/components/ui/agentflow separation | APP-Q2: Identifiable modules in monorepo |
| Data coupling | **Medium Effort** — Single shared database with TypeORM; all entities in one DataSource | DATA-Q2: Centralized ORM, but shared database |
| Stored procedures | **Low Effort** — No stored procedures; all logic in TypeScript application layer | DATA-Q4 = 4 |
| Communication patterns | **Medium Effort** — Primarily synchronous; BullMQ provides async foundation that can be extended | APP-Q3 = 2 |
| CI/CD maturity | **Medium Effort** — GitHub Actions exists for build/test; needs extension for multi-service deployment | INF-Q11 = 2 |
| Test coverage | **Low-Medium Effort** — Jest unit tests + Cypress e2e exist; need extension for service integration tests | OPS-Q6 = 3 |

**Calibrated Effort Estimate:** The Conditional/Adaptive approach with EKS containerization is estimated at **3-6 months** for Phase 1 (EKS deployment + Aurora migration) and **6-12 months** for Phase 2 (selective service extraction). The existing Docker containerization and modular package structure reduce initial effort.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs as self-managed Docker containers. The root `Dockerfile` builds a monorepo image using `node:20-alpine`. `docker/Dockerfile` is a multi-stage build installing Flowise from npm. `docker/docker-compose.yml` runs a single Flowise container. `docker/docker-compose-queue-prebuilt.yml` adds Redis and a worker container. No ECS task definitions, EKS manifests, Lambda functions, or Fargate configurations exist anywhere in the repository. |
| **Gap** | No managed compute infrastructure. All compute is self-managed Docker Compose with no orchestration, no auto-healing, and no managed scaling. |
| **Recommendation** | Deploy Flowise on **Amazon EKS** (preferred) with Fargate profiles for the worker containers. Define EKS cluster, node groups, and service manifests in AWS CDK. This provides managed orchestration, auto-scaling, and self-healing without managing Kubernetes infrastructure directly. Avoid self-managed Kubernetes (per preferences). |
| **Evidence** | `Dockerfile`, `docker/Dockerfile`, `docker/docker-compose.yml`, `docker/docker-compose-queue-prebuilt.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed database definitions exist. `packages/server/src/DataSource.ts` configures TypeORM to connect to SQLite (default), PostgreSQL, MySQL, or MariaDB via environment variables (`DATABASE_TYPE`, `DATABASE_HOST`, `DATABASE_PORT`). The default is SQLite stored as a local file at `~/.flowise/database.sqlite`. `docker/docker-compose-queue-prebuilt.yml` includes `redis:alpine` as a self-managed Redis instance. No `aws_rds_*`, `aws_dynamodb_*`, or `aws_elasticache_*` resources. |
| **Gap** | All databases are self-managed with no automated failover, backup, or scaling. SQLite default is a single-file database unsuitable for production. |
| **Recommendation** | Migrate to **Amazon Aurora PostgreSQL** (preferred) as the primary database — TypeORM's PostgreSQL driver requires only connection string changes. Replace the self-managed Redis with **Amazon ElastiCache for Redis** for BullMQ queues and pub/sub. Evaluate **Amazon DynamoDB** (preferred) for high-throughput tables (ChatMessage, Execution) in a later phase. |
| **Evidence** | `packages/server/src/DataSource.ts`, `docker/docker-compose-queue-prebuilt.yml`, `packages/server/.env.example`, `docker/.env.example` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | BullMQ provides queue-based job processing with two queues: `PredictionQueue` and `UpsertQueue` (in `packages/server/src/queue/`). `QueueManager` sets up queues with worker concurrency configuration. Jobs are dispatched asynchronously and processed by worker instances. This is basic job queuing with some structure, but not dedicated workflow orchestration — no Step Functions, Temporal, MWAA, or visual workflow management. The LLM prediction flow (load chatflow → resolve credentials → invoke LLM → store result) is orchestrated in application code. |
| **Gap** | Multi-step LLM prediction workflows are orchestrated in application code without dedicated workflow management, error handling patterns, or state persistence between steps. |
| **Recommendation** | Adopt **AWS Step Functions** for multi-step LLM workflows (chatflow execution, vector upsert pipelines, evaluation runs). Step Functions provides visual workflow management, built-in retry/error handling, and state persistence — critical for long-running LLM operations. Keep BullMQ for simple job queuing; use Step Functions for complex orchestration. |
| **Evidence** | `packages/server/src/queue/PredictionQueue.ts`, `packages/server/src/queue/UpsertQueue.ts`, `packages/server/src/queue/QueueManager.ts` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | BullMQ (Redis-backed) for job queuing and `RedisEventPublisher`/`RedisEventSubscriber` for real-time event streaming (SSE to UI). Redis runs as a self-managed container (`redis:alpine` in `docker/docker-compose-queue-prebuilt.yml`). No managed AWS messaging services (SQS, SNS, EventBridge, MSK, Kinesis). The queue mode is optional (`MODE=queue`) — default mode processes everything synchronously. |
| **Gap** | All messaging infrastructure is self-managed Redis. No managed messaging services for cross-service communication, event-driven patterns, or reliable message delivery. |
| **Recommendation** | Replace self-managed Redis messaging with **Amazon EventBridge** (preferred) for event-driven communication between services. Use **Amazon SQS** for reliable job queuing (replacing BullMQ). Keep **Amazon ElastiCache for Redis** for real-time SSE streaming and caching. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `packages/server/src/queue/RedisEventPublisher.ts`, `packages/server/src/queue/RedisEventSubscriber.ts`, `docker/docker-compose-queue-prebuilt.yml` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation configuration exists in the repository. Docker Compose uses a simple bridge network (`flowise-net` in `docker/docker-compose-queue-prebuilt.yml`). The Express server binds to port 3000 and is directly exposed via Docker port mapping. No private subnets, no VPC endpoints, no network policies. |
| **Gap** | No network isolation. Services are exposed without segmentation, security groups, or private subnets. Any compromise has unlimited blast radius. |
| **Recommendation** | Define a VPC with public and private subnets in CDK. Place EKS worker nodes and Aurora database in private subnets. Use **Amazon API Gateway** (preferred) as the public entry point. Configure security groups with least-privilege rules. Add VPC endpoints for AWS service access (S3, Secrets Manager, ECR) to avoid internet routing. |
| **Evidence** | `docker/docker-compose-queue-prebuilt.yml` (bridge network only), absence of any VPC/subnet/security group configuration |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync defined. The Express server directly serves all traffic on port 3000. `docker/docker-compose.yml` exposes `${PORT}:${PORT}` directly. The application implements its own rate limiting (`express-rate-limit`), authentication (Passport.js), and CORS handling — all at the application level with no infrastructure-level protection. |
| **Gap** | No managed entry point for throttling, authentication offloading, request validation, or DDoS protection. All traffic hits the Express server directly. |
| **Recommendation** | Deploy **Amazon API Gateway** (preferred) as the entry point. Configure throttling, request validation, and WAF integration at the gateway level. Use API Gateway's JWT authorizer to offload authentication from the application. Add CloudFront for static asset delivery (the React UI build). |
| **Evidence** | `packages/server/src/index.ts` (Express listening on port 3000), `docker/docker-compose.yml` (direct port exposure) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. Docker Compose runs single instances of each container. No ECS service scaling, EKS HPA, ASG, Lambda concurrency, DynamoDB auto-scaling, or Aurora auto-scaling. The worker concurrency is configurable via `WORKER_CONCURRENCY` environment variable, but this is process-level concurrency within a single container, not infrastructure-level scaling. |
| **Gap** | All capacity is statically provisioned. The application cannot respond to traffic spikes (popular chatbot suddenly gets high traffic) or scale down during low demand. |
| **Recommendation** | Configure Kubernetes HPA (Horizontal Pod Autoscaler) on EKS based on custom metrics — prediction queue depth, HTTP request rate, and CPU utilization. Configure Aurora auto-scaling for read replicas. Set ElastiCache shard scaling based on connection count. |
| **Evidence** | `docker/docker-compose-queue-prebuilt.yml` (single instance), `docker/.env.example` (`WORKER_CONCURRENCY` config) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found anywhere in the repository. No `aws_backup_plan`, no `backup_retention_period`, no PITR configuration. The default SQLite database is a single local file with no backup mechanism. When using PostgreSQL/MySQL, backup responsibility falls entirely on the user. Redis data in Docker Compose uses a named volume (`redis_data`) but no backup schedule. |
| **Gap** | No automated backups for any data store. A data loss event (disk failure, container crash, accidental deletion) results in complete loss of chatflows, credentials, chat history, and evaluation data. |
| **Recommendation** | Aurora PostgreSQL (recommended migration target) provides automated backups with configurable retention and PITR by default. For the migration period, configure `aws_backup_plan` in CDK covering Aurora, ElastiCache snapshots, and S3 versioning for blob storage. Test restore procedures quarterly. |
| **Evidence** | Absence of any backup configuration in the repository. `docker/docker-compose-queue-prebuilt.yml` (Redis volume without backup). |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration. Docker Compose runs all services on a single host. No load balancer with cross-zone enabled. No multi-AZ database configuration. Single Redis instance. The `has_multi_instance_deployment` surface flag is `false`. |
| **Gap** | Single point of failure at every layer — compute, database, and cache. An AZ or host failure takes down the entire application. |
| **Recommendation** | Deploy EKS worker nodes across 2+ AZs. Configure Aurora PostgreSQL with Multi-AZ failover. Deploy ElastiCache Redis with Multi-AZ replication. Use API Gateway (inherently multi-AZ) as the entry point. |
| **Evidence** | `docker/docker-compose.yml` (single instance), `docker/docker-compose-queue-prebuilt.yml` (single Redis, single Flowise, single worker) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC exists. No Terraform files (`.tf`), no CloudFormation templates, no CDK stacks (`cdk.json`), no Helm charts (`Chart.yaml`), no Kustomize files. All infrastructure configuration is done via Docker Compose files and environment variables. The Docker Compose files define only the application runtime containers, not underlying infrastructure (VPC, databases, load balancers, IAM roles). |
| **Gap** | 100% of infrastructure is manually created (ClickOps or ad hoc Docker commands). No reproducible deployments, no environment consistency, no disaster recovery automation. |
| **Recommendation** | Create an **AWS CDK (TypeScript)** project — natural fit for the existing TypeScript team. Define the complete infrastructure stack: VPC, EKS cluster, Aurora PostgreSQL, ElastiCache Redis, API Gateway, S3 buckets, KMS keys, IAM roles, CloudWatch alarms, and Backup plans. Target 90%+ IaC coverage. |
| **Evidence** | Absence of any `.tf`, `cdk.json`, `template.yaml`, `Chart.yaml`, or `kustomization.yaml` files in the entire repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides partial automation. `.github/workflows/main.yml` runs on push/PR: lint, build, test (Jest + Cypress e2e). `.github/workflows/docker-image-dockerhub.yml` and `.github/workflows/docker-image-ecr.yml` are `workflow_dispatch` (manual trigger) for Docker image builds and pushes. `.github/workflows/publish-agentflow.yml` manually publishes the agentflow package. Build and test are automated; deployment is manual. No IaC deployment pipeline. |
| **Gap** | Deployment is manual — operators must trigger `workflow_dispatch` to build images and then manually deploy. No automated rollback, no environment promotion, no IaC change pipeline. |
| **Recommendation** | Extend GitHub Actions or migrate to **AWS CodePipeline** for full CI/CD: automated build → test → deploy on merge to main. Add IaC deployment via CDK pipeline. Implement automated rollback on deployment failure. Add security scanning stage (see SEC-Q7). |
| **Evidence** | `.github/workflows/main.yml`, `.github/workflows/docker-image-dockerhub.yml`, `.github/workflows/docker-image-ecr.yml`, `.github/workflows/publish-agentflow.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript 5.4.5 on Node.js 20 (pinned via `.nvmrc` at v20.19.2). Modern framework ecosystem: Express.js 4.x for server, React 18 + Vite 5 for UI, pnpm 10.26.0 for package management, Turbo 1.10.16 for build orchestration. AWS SDK v3 across all packages (`@aws-sdk/client-bedrock-runtime@3.966.0`, `@aws-sdk/client-s3@^3.844.0`, `@aws-sdk/client-secrets-manager@^3.699.0`, `@aws-sdk/client-dynamodb@^3.360.0`, `@aws-sdk/client-kendra@^3.750.0`, `@aws-sdk/client-sns@^3.699.0`, `@aws-sdk/client-sts@^3.699.0`). First-class AWS SDK coverage with the latest v3 modular SDK. |
| **Gap** | N/A — language, framework, and SDK are all modern and current. |
| **Recommendation** | N/A — no language modernization needed. Continue tracking Node.js LTS releases and TypeScript major versions. |
| **Evidence** | `package.json` (TypeScript ^5.4.5), `.nvmrc` (v20.19.2), `packages/server/package.json` (Express, AWS SDKs), `packages/components/package.json` (AWS SDKs, LangChain), `packages/ui/package.json` (React 18, Vite 5) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a pnpm monorepo with 5 packages: `server` (Express API + worker), `ui` (React frontend), `components` (LLM nodes, vector stores, tools — the integration layer), `agentflow` (embeddable React component library), and `api-documentation` (Swagger docs). Despite the modular package structure, it deploys as a single unit — the server depends on `flowise-components: workspace:^` and `flowise-ui: workspace:^` as workspace dependencies. All packages share a single database via `packages/server/src/DataSource.ts`. The worker mode (BullMQ) shares the same codebase, entities, and database. The layered architecture (routes → controllers → services) provides internal structure, but there is no independent deployment or scaling of individual packages. |
| **Gap** | Single deployable monolith with a shared database. No independent deployment or scaling of components. The server package contains all business logic, all routes (50+ route modules), and all database access in one process. |
| **Recommendation** | Adopt the Conditional/Adaptive decomposition approach (see Decomposition Strategy section). Containerize on EKS as-is, then extract high-value services: Prediction Service, Vector Store Service, and Document Processing Service. The existing pnpm package boundaries provide a foundation for service extraction. |
| **Evidence** | `pnpm-workspace.yaml`, `packages/server/package.json` (workspace deps), `packages/server/src/routes/index.ts` (50+ route modules), `packages/server/src/DataSource.ts` (single shared database) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application primarily uses synchronous HTTP for its API surface (all Express routes in `packages/server/src/routes/`). BullMQ provides async job processing for predictions and vector upserts when `MODE=queue`. Redis pub/sub (`RedisEventPublisher`/`RedisEventSubscriber`) delivers real-time events to the UI via SSE. However, the default mode (`MODE` unset) processes all predictions synchronously in the API request handler. The async path is optional and supplementary. |
| **Gap** | Standard mode is fully synchronous. Even in queue mode, the async is for background job processing, not true event-driven communication between services. Cross-service state propagation (credential updates, chatflow changes) is not event-driven. |
| **Recommendation** | When decomposing into services, adopt **Amazon EventBridge** (preferred) for cross-service event communication. Publish events on chatflow creation, credential updates, and prediction completion. Consuming services react to events asynchronously. Keep synchronous HTTP for user-facing API requests. |
| **Evidence** | `packages/server/src/routes/index.ts` (synchronous routes), `packages/server/src/queue/PredictionQueue.ts` (optional async), `packages/server/src/queue/RedisEventPublisher.ts` (SSE events) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | LLM prediction requests are inherently long-running (often >30s). The application provides two modes: (1) Standard mode — predictions processed synchronously in the API handler; (2) Queue mode (`MODE=queue`) — predictions dispatched to BullMQ `PredictionQueue`, processed by worker instances, with SSE streaming for real-time response delivery to clients. Vector upserts similarly use `UpsertQueue`. Queue mode provides full async processing with status tracking via the BullMQ dashboard (`ENABLE_BULLMQ_DASHBOARD`). The queue mode is production-ready with configurable concurrency, job cleanup, and health monitoring. |
| **Gap** | Queue mode is optional (not default). Standard mode still processes predictions synchronously, risking timeouts for complex LLM chains. |
| **Recommendation** | Make queue mode the default for production deployments. Document that `MODE=queue` is required for reliable prediction processing. Consider making queue mode mandatory when deploying on EKS to enable horizontal worker scaling. |
| **Evidence** | `packages/server/src/queue/PredictionQueue.ts`, `packages/server/src/queue/UpsertQueue.ts`, `packages/server/src/queue/QueueManager.ts`, `docker/.env.example` (MODE=queue) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | All API routes are registered under `/api/v1/` via the router in `packages/server/src/routes/index.ts`. This is a consistent URL path versioning strategy applied to all endpoints (50+ route modules). The OpenAPI spec at `packages/api-documentation/src/yml/swagger.yml` documents all `/api/v1/` endpoints with structured request/response schemas. The versioning prefix is enforced by the middleware that checks `URL_CASE_SENSITIVE_REGEX: /\/api\/v1\//`. |
| **Gap** | Versioning is consistent but there's no evidence of backward compatibility guarantees, deprecation policies, or migration documentation for when `/api/v2/` is introduced. No changelog files for API changes. |
| **Recommendation** | Document a backward compatibility policy for the `/api/v1/` contract. Add API changelog tracking. When introducing breaking changes, create `/api/v2/` routes alongside `/api/v1/` with a deprecation timeline. |
| **Evidence** | `packages/server/src/routes/index.ts` (all routes under v1), `packages/server/src/index.ts` (URL_CASE_SENSITIVE_REGEX enforcement), `packages/api-documentation/src/yml/swagger.yml` (OpenAPI spec) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables: `DATABASE_HOST`, `REDIS_URL`/`REDIS_HOST`, `S3_ENDPOINT_URL`, etc. Docker Compose uses service names for inter-container communication (e.g., `redis://redis:6379` in `docker/docker-compose-queue-prebuilt.yml`). No dynamic service discovery mechanism (no AWS Cloud Map, no Consul, no Istio). No API catalog beyond the Swagger documentation. |
| **Gap** | All service endpoints are statically configured via environment variables or Docker Compose service names. No dynamic service discovery for scaling, failover, or service relocation. |
| **Recommendation** | When moving to EKS, leverage Kubernetes service discovery (ClusterIP services, DNS-based discovery). For cross-cluster or multi-service communication, use **AWS Cloud Map** for service registration and discovery. Register the Flowise API in Cloud Map for programmatic discovery by other services. |
| **Evidence** | `packages/server/.env.example` (DATABASE_HOST, REDIS_URL env vars), `docker/docker-compose-queue-prebuilt.yml` (redis://redis:6379 hardcoded), `packages/server/src/DataSource.ts` (env var-based database config) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application supports S3 for blob/file storage via `multer-s3`, `@aws-sdk/client-s3`, and `S3_STORAGE_*` environment variables. Storage providers are abstracted in `packages/components/src/storage/` with implementations for Local, S3, GCS, and Azure Blob. Document loaders in `packages/components/nodes/documentloaders/` handle PDF, EPUB, Office files (Word, PowerPoint, Excel), CSV, JSON, and web scraping (Cheerio, Puppeteer, Playwright). S3-specific document loaders exist (`S3File`, `S3Directory`). When configured with `STORAGE_TYPE=s3`, all file uploads are stored in S3. |
| **Gap** | No automated parsing pipeline (e.g., Textract) at the infrastructure level. Document parsing is handled by LangChain document loaders at the application level. No S3 event notifications for automated processing on upload. |
| **Recommendation** | Integrate Amazon Textract for automated document parsing on S3 upload. Add S3 event notifications (via EventBridge) to trigger document processing pipelines. This enables automated RAG ingestion pipelines without manual document loader invocation. |
| **Evidence** | `packages/components/src/storage/S3StorageProvider.ts`, `packages/components/nodes/documentloaders/S3File/S3File.ts`, `packages/components/nodes/documentloaders/Pdf/Pdf.ts`, `packages/server/.env.example` (STORAGE_TYPE, S3_STORAGE_*) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeORM provides a centralized ORM layer for all database operations. 19+ entities are defined in `packages/server/src/database/entities/` (ChatFlow, ChatMessage, Credential, Tool, Variable, Dataset, Evaluation, etc.) with typed columns and relations. Services access data through TypeORM repositories with consistent patterns. Migration files exist for all 4 database types (SQLite, PostgreSQL, MySQL, MariaDB) in `packages/server/src/database/migrations/`. |
| **Gap** | The `packages/components` package contains some direct database-related code for vector stores (Postgres vector store with direct `pg` driver usage, Redis vector store with direct `ioredis`). These bypass the TypeORM data access layer. The main application data access is well-structured, but auxiliary data paths (vector stores, cache) use direct connections. |
| **Recommendation** | Centralize vector store connection management through a shared connection pool or configuration layer. When extracting a Vector Store Service, ensure it owns its database connections independently from the main application's TypeORM DataSource. |
| **Evidence** | `packages/server/src/database/entities/index.ts`, `packages/server/src/DataSource.ts`, `packages/server/src/database/migrations/`, `packages/components/nodes/vectorstores/Postgres/driver/PGVector.ts` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No database engine versions are explicitly pinned in the repository. `packages/server/src/DataSource.ts` configures database connections via environment variables without specifying engine versions. `docker/docker-compose-queue-prebuilt.yml` uses `redis:alpine` without a version pin (pulls latest). Node.js drivers in dependencies (`sqlite3@^5.1.6`, `pg@^8.11.1`, `mysql2@^3.11.3`) constrain client versions but not server engine versions. The actual database engine version is determined entirely by the user's deployment. |
| **Gap** | No engine version pinning. No version lifecycle management. Users may run EOL database engines without awareness. Redis image uses `latest` tag, which can introduce breaking changes on pull. |
| **Recommendation** | Pin Redis image version in Docker Compose (e.g., `redis:7.4-alpine`). When migrating to Aurora PostgreSQL, pin the engine version in CDK and establish a version update procedure with documented downtime windows. Add a startup health check that logs the database engine version for visibility. |
| **Evidence** | `packages/server/src/DataSource.ts` (no version specification), `docker/docker-compose-queue-prebuilt.yml` (`redis:alpine` unpinned), `packages/server/package.json` (client driver versions) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found anywhere in the repository. All database interactions go through TypeORM with migration files that use standard SQL DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX). Migration files in `packages/server/src/database/migrations/` for all 4 database types (sqlite, postgres, mysql, mariadb) use only standard SQL. All business logic is in the TypeScript application layer — no database-side logic. No `.sql` files containing `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION`. |
| **Gap** | N/A — no stored procedures or proprietary SQL. |
| **Recommendation** | N/A — the current approach of keeping all business logic in the application layer is the best practice. This makes database migration (e.g., SQLite to Aurora PostgreSQL) straightforward. |
| **Evidence** | `packages/server/src/database/migrations/` (standard SQL DDL only), `packages/server/src/DataSource.ts` (TypeORM-only data access) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has application-level logging via Winston with daily rotate file support (`winston-daily-rotate-file`), S3 log streaming (`s3-streamlogger`), and configurable log sanitization for sensitive fields (`LOG_SANITIZE_BODY_FIELDS`, `LOG_SANITIZE_HEADER_FIELDS`). The enterprise module has an audit route (`packages/server/src/enterprise/routes/audit`). Express request logging is enabled via `expressRequestLogger` middleware. However, no CloudTrail or equivalent infrastructure-level immutable audit logging is configured. No IaC exists to enable CloudTrail. |
| **Gap** | No infrastructure-level audit logging (CloudTrail). Application-level logs are not immutable — they can be modified or deleted. No S3 Object Lock for log storage. |
| **Recommendation** | Enable AWS CloudTrail with log file validation in CDK. Store CloudTrail logs in an S3 bucket with Object Lock (WORM) for immutability. Stream application logs to CloudWatch Logs with defined retention policies. The existing S3 log streaming capability can be extended to use a dedicated, locked audit log bucket. |
| **Evidence** | `packages/server/package.json` (winston, winston-daily-rotate-file, s3-streamlogger), `packages/server/src/index.ts` (expressRequestLogger), `packages/server/.env.example` (LOG_SANITIZE_* settings) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS or encryption-at-rest configuration found in the repository. No `kms_key_id` on any resource, no `aws_kms_key` definitions. The application stores sensitive data (LLM API keys, database credentials, user credentials) but has no encryption-at-rest configuration. The `crypto-js` library is used for application-level encryption of stored credentials, but this is not equivalent to infrastructure-level KMS encryption. Database encryption depends entirely on the user's deployment configuration. S3 bucket encryption is not configured in the application code. |
| **Gap** | No infrastructure-level encryption at rest. Sensitive credentials and user data may be stored unencrypted depending on the database and storage backend configuration. |
| **Recommendation** | When migrating to Aurora PostgreSQL, enable storage encryption with a customer-managed KMS key. Configure S3 buckets with SSE-KMS encryption. Enable ElastiCache encryption at rest. Define KMS keys in CDK with appropriate key policies and rotation. The existing `crypto-js` application-level encryption of credentials provides defense-in-depth but is not a substitute for infrastructure-level encryption. |
| **Evidence** | `packages/server/package.json` (crypto-js for app-level encryption), absence of any KMS configuration, `packages/server/.env.example` (no encryption settings) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JWT-based authentication is implemented with `jsonwebtoken` and `passport-jwt`. Passport.js provides multiple authentication strategies: JWT (primary), local (username/password), OAuth2 (Auth0 via `passport-auth0`, GitHub via `passport-github`, Google via `passport-google-oauth20`, OIDC via `passport-openidconnect`). API key validation for external API access (`validateAPIKey` in `packages/server/src/utils/validateKey`). Bearer token auth on API endpoints. Rate limiting with `express-rate-limit`. Whitelist URLs (`WHITELIST_URLS`) define intentionally public endpoints. JWT configuration includes configurable token expiry (`JWT_TOKEN_EXPIRY_IN_MINUTES=360`), refresh tokens, and issuer/audience validation. |
| **Gap** | Internal endpoints accessed via `x-request-from: internal` header bypass API key validation and rely on JWT verification only. Some endpoints (whitelist URLs) are intentionally public without rate limiting differentiation. |
| **Recommendation** | When deploying behind API Gateway (preferred), offload JWT validation to the gateway's JWT authorizer. Implement API Gateway usage plans and API keys for external consumers. Add WAF rules for additional protection on public endpoints. |
| **Evidence** | `packages/server/src/index.ts` (auth middleware, validateAPIKey, WHITELIST_URLS, verifyToken), `packages/server/package.json` (jsonwebtoken, passport-*, express-rate-limit), `packages/server/.env.example` (JWT_* settings) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Passport.js with SSO support via multiple providers: `passport-auth0` (Auth0), `passport-google-oauth20` (Google), `passport-github` (GitHub), `passport-openidconnect` (generic OIDC). The enterprise module has `initializeSSO()` for SSO initialization. Federation with external IdPs is supported. The `IdentityManager` class manages identity and license validation. However, local username/password authentication (`passport-local`) remains as a fallback path. |
| **Gap** | Local username/password authentication coexists with SSO. Some users may bypass centralized identity management via local auth. |
| **Recommendation** | For enterprise deployments, enforce SSO-only authentication (disable local auth). When migrating to AWS, consider **Amazon Cognito** for centralized identity management with OIDC/SAML federation. Cognito integrates natively with API Gateway for JWT validation. |
| **Evidence** | `packages/server/package.json` (passport-auth0, passport-google-oauth20, passport-github, passport-openidconnect, passport-local), `packages/server/src/index.ts` (initializeSSO) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application supports AWS Secrets Manager for secret key storage (`SECRETKEY_STORAGE_TYPE=aws`, `@aws-sdk/client-secrets-manager`). Auth secrets (TOKEN_HASH_SECRET, EXPRESS_SESSION_SECRET, JWT tokens) can be stored in Secrets Manager, local files, or environment variables. The `.env.example` files show example credentials as comments (not committed plaintext values). The application uses `crypto-js` to encrypt stored credentials. However, the default configuration uses environment variables for production credentials, and no automatic rotation is configured. |
| **Gap** | Production credentials default to environment variables without rotation. AWS Secrets Manager is supported but optional. No automated rotation for any secrets. |
| **Recommendation** | Make AWS Secrets Manager the default for production deployments. Enable automated rotation for database credentials and JWT secrets. Remove environment variable fallback for sensitive secrets in production configuration. The existing `SECRETKEY_STORAGE_TYPE=aws` support makes this a configuration change, not a code change. |
| **Evidence** | `packages/server/.env.example` (SECRETKEY_STORAGE_TYPE=local|aws), `packages/server/package.json` (@aws-sdk/client-secrets-manager), `docker/.env.example` (SECRETKEY_AWS_* settings) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Dockerfiles use `node:20-alpine` as the base image. The root `Dockerfile` runs as non-root user (USER node), disables Puppeteer download, and sets NODE_OPTIONS. No SSM Patch Manager, no vulnerability scanning (Inspector, Snyk, Trivy), no hardened base images (CIS, Bottlerocket). No EC2 Image Builder pipelines. No container image scanning in CI/CD. The Docker images install system packages (`chromium`, `python3`, `make`, `g++`) which expand the attack surface. |
| **Gap** | No compute hardening or patching strategy. Base images are standard Alpine with additional build tools installed. No vulnerability scanning or compliance checking. |
| **Recommendation** | Use a hardened base image (e.g., AWS-provided Node.js on Amazon Linux 2023, or Chainguard images). Add Trivy or ECR image scanning to the CI/CD pipeline. Remove build tools from the runtime image (use multi-stage builds — the `docker/Dockerfile` already uses multi-stage). Enable Amazon Inspector for continuous vulnerability assessment on EKS. |
| **Evidence** | `Dockerfile` (node:20-alpine, installs chromium/python3/make/g++), `docker/Dockerfile` (multi-stage build), absence of any vulnerability scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are configured in the CI/CD pipeline. `.github/workflows/main.yml` runs lint, build, and tests (Jest + Cypress) but no SAST (SonarQube, Semgrep, CodeGuru), no dependency scanning (Dependabot, npm audit, Snyk), and no container scanning. No `.dependabot/config.yml`, no `.snyk` policy file. The `pnpm.overrides` in `package.json` shows manual version pinning for known vulnerable packages (axios, cross-spawn, ws, etc.), indicating manual vulnerability management rather than automated scanning. |
| **Gap** | No automated security scanning. Vulnerability management is manual (pnpm overrides). No security gates blocking deployments on critical findings. |
| **Recommendation** | Add Dependabot for automated dependency vulnerability scanning and PR creation. Integrate Semgrep or Amazon CodeGuru Reviewer for SAST in the CI pipeline. Add ECR image scanning for container vulnerabilities. Configure `npm audit` or `pnpm audit` as a pipeline step with fail-on-critical. |
| **Evidence** | `.github/workflows/main.yml` (no security scanning steps), `package.json` (pnpm.overrides for manual vulnerability patches), absence of `.dependabot/`, `.snyk`, or any security scanning configuration |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry SDK is fully integrated in the server package with comprehensive dependencies: `@opentelemetry/api@1.9.0`, `@opentelemetry/sdk-node@^0.54.0`, `@opentelemetry/auto-instrumentations-node@^0.52.0`, trace exporters for gRPC, HTTP, and proto formats. The server initializes OpenTelemetry when `METRICS_PROVIDER=open_telemetry`. Auto-instrumentation captures HTTP requests, database queries, and external service calls. Trace export configuration is environment-variable driven (`METRICS_OPEN_TELEMETRY_METRIC_ENDPOINT`, `METRICS_OPEN_TELEMETRY_PROTOCOL`). OTEL Collector config exists at `metrics/otel/otel.config.yml`. |
| **Gap** | Since Flowise is a monolith, cross-service trace propagation is limited to the app-to-external-service boundary (LLM providers, vector stores). Tracing within the monolith provides useful spans but not distributed trace propagation across independent services. |
| **Recommendation** | When decomposing into services, ensure trace context propagation (W3C traceparent header) across all service boundaries. Export traces to **AWS X-Ray** for centralized visualization and service map. The existing OpenTelemetry SDK supports X-Ray export natively. |
| **Evidence** | `packages/server/package.json` (OpenTelemetry dependencies), `packages/server/src/metrics/OpenTelemetry.ts`, `metrics/otel/otel.config.yml`, `packages/server/.env.example` (METRICS_OPEN_TELEMETRY_* settings) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the codebase. No error budget tracking. The metrics system tracks business counters (chatflow_created, predictions) and HTTP request duration via Prometheus and OpenTelemetry, but these are raw metrics — no formal SLO thresholds, no error budget policies, no SLO dashboards. No p99/p95 latency targets defined. |
| **Gap** | No formal definition of acceptable service levels. Cannot measure whether the system is meeting user expectations or degrading over time. |
| **Recommendation** | Define SLOs for critical user journeys: prediction latency (p95 < 30s), API availability (99.9%), chatflow CRUD latency (p95 < 500ms). Implement SLO monitoring using the existing Prometheus/OpenTelemetry metrics. Add error budget tracking and alerting when budgets are consumed. |
| **Evidence** | `packages/server/src/Interface.Metrics.ts` (FLOWISE_METRIC_COUNTERS — raw counters only), `metrics/prometheus/prometheus.config.yml` (scrape config, no alert rules) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Custom business metrics are defined via `FLOWISE_METRIC_COUNTERS` enum in `packages/server/src/Interface.Metrics.ts`: chatflow_created, agentflow_created, assistant_created, tool_created, vector_upserted, chatflow_prediction_internal, chatflow_prediction_external, agentflow_prediction_internal, agentflow_prediction_external. These are genuine business outcome metrics. Both Prometheus (`packages/server/src/metrics/Prometheus.ts`) and OpenTelemetry (`packages/server/src/metrics/OpenTelemetry.ts`) providers support these counters. Grafana dashboards exist in `metrics/grafana/` (app dashboard and server dashboard). |
| **Gap** | Business metrics cover creation and prediction events but not all features — no metrics for document store operations, evaluation runs, credential usage, or user activity patterns. No success/failure rate tracking per chatflow. |
| **Recommendation** | Extend business metrics to cover evaluation runs (critical for AI/LLM quality), document store ingestion throughput, per-chatflow prediction success/failure rates, and credential usage patterns. Add these to the existing Grafana dashboards. |
| **Evidence** | `packages/server/src/Interface.Metrics.ts`, `packages/server/src/metrics/Prometheus.ts`, `packages/server/src/metrics/OpenTelemetry.ts`, `metrics/grafana/grafana.dashboard.app.json.txt`, `metrics/grafana/grafana.dashboard.server.json.txt` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found. `metrics/prometheus/prometheus.config.yml` defines scrape targets but no alert rules (no `alerting` section, no `rule_files`). No CloudWatch alarms. No PagerDuty, OpsGenie, or SNS alerting integration. No Grafana alert rules in the dashboard definitions. The metrics infrastructure collects data but no alerts are defined to act on it. |
| **Gap** | Metrics are collected but never trigger alerts. Degradation, errors, and outages can go unnoticed indefinitely. |
| **Recommendation** | Add Prometheus Alertmanager with alert rules for: prediction failure rate > 5%, API latency p95 > 10s, queue depth > 1000 jobs, database connection failures. When on AWS, use CloudWatch alarms with SNS notifications. Configure anomaly detection on prediction latency using CloudWatch anomaly detection. |
| **Evidence** | `metrics/prometheus/prometheus.config.yml` (no alerting section), absence of any alert configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No canary, blue/green, or rolling deployment configuration exists. Docker image builds are triggered via manual `workflow_dispatch` in `.github/workflows/docker-image-dockerhub.yml` and `.github/workflows/docker-image-ecr.yml`. After image push, deployment is entirely manual. No CodeDeploy, no Argo Rollouts, no Helm upgrade strategies, no traffic shifting, no feature flags for gradual rollout. |
| **Gap** | Direct-to-production deployment with no staged rollout. Any regression immediately affects all users. No automated rollback mechanism. |
| **Recommendation** | Implement blue/green deployment on EKS using **AWS CodeDeploy** or Argo Rollouts. Configure health checks that automatically roll back on failure. Add canary deployment for the prediction service (route 10% of traffic to new version, monitor error rates, then promote). |
| **Evidence** | `.github/workflows/docker-image-dockerhub.yml` (workflow_dispatch, no deployment strategy), `.github/workflows/docker-image-ecr.yml` (workflow_dispatch, no deployment strategy) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Jest is configured for both server and components packages with coverage reporting. Cypress e2e tests exist in `packages/server/cypress/` and run in the CI pipeline (`.github/workflows/main.yml`). The CI workflow starts the server (`pnpm start`), waits for it to be ready (`wait-on: http://localhost:3000`), then runs Cypress tests in Chrome. Unit tests run via `pnpm test:coverage`. The pipeline covers lint → build → unit tests → Cypress e2e — a solid testing foundation. |
| **Gap** | Cypress tests cover UI workflows but may not cover all API contract scenarios. No explicit API contract testing (e.g., Pact, Postman/Newman). No load testing in CI (though `artillery-load-test.yml` exists at the repo root for manual use). |
| **Recommendation** | Add API contract tests using Postman/Newman or Supertest to validate all `/api/v1/` endpoint contracts in CI. Integrate the existing Artillery load test config into a periodic CI job for performance regression detection. When decomposing into services, add cross-service contract tests. |
| **Evidence** | `.github/workflows/main.yml` (Cypress e2e in CI), `packages/server/cypress/`, `packages/server/package.json` (jest, cypress, supertest), `artillery-load-test.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker Compose health checks exist (`curl -f http://localhost:${PORT}/api/v1/ping` in both `docker-compose.yml` and `docker-compose-queue-prebuilt.yml`) with restart policies, which provide basic self-healing (container restart on health check failure). No formal runbooks, no SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No structured incident response documentation. |
| **Gap** | Health checks provide container-level self-healing only. No runbooks for common operational scenarios (database connection failure, Redis unavailable, LLM provider timeout, disk full). No automated escalation. |
| **Recommendation** | Create operational runbooks for the top 5 failure scenarios. Implement AWS Systems Manager Automation documents for automated remediation (e.g., restart EKS pods on memory exhaustion, scale workers on queue depth threshold). Add PagerDuty or SNS-based alerting with escalation policies. |
| **Evidence** | `docker/docker-compose.yml` (healthcheck), `docker/docker-compose-queue-prebuilt.yml` (healthcheck with restart: always) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Grafana dashboards exist in `metrics/grafana/` (app dashboard and server dashboard). Prometheus and OpenTelemetry metrics providers are configured. However, no CODEOWNERS file exists for observability configs. No per-service dashboards with named owners. No SLO definitions with team attribution. The metrics infrastructure is comprehensive but has no ownership model. |
| **Gap** | Observability assets (dashboards, metrics, alarms) have no clear ownership or team attribution. Monitoring gaps can emerge without accountability. |
| **Recommendation** | Create a CODEOWNERS file assigning observability configs (`metrics/`, `packages/server/src/metrics/`) to a specific team. Add team tags to Grafana dashboards. When SLOs are defined, attribute them to specific service owners. |
| **Evidence** | `metrics/grafana/grafana.dashboard.app.json.txt`, `metrics/grafana/grafana.dashboard.server.json.txt`, absence of CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging configuration found. No IaC exists to define tags. No `default_tags`, no `required-tags` Config rules, no Tag Policies. The application is deployed via Docker Compose with no AWS resource tagging. When resources are created manually in AWS, there is no tagging standard or enforcement mechanism. |
| **Gap** | No tags on any resources. Cannot track costs per workload, identify resource ownership, or enforce budget controls. |
| **Recommendation** | Define a tagging standard in CDK using `default_tags`: `Environment` (dev/staging/prod), `Service` (flowise), `Team` (owning team), `CostCenter` (cost allocation). Enforce tags via AWS Config rules (`required-tags`). Activate cost allocation tags in AWS Billing. |
| **Evidence** | Absence of any tagging configuration. No IaC, no CODEOWNERS, no tagging standards documentation. |

## Learning Materials

The following resources are linked to the 3 triggered pathways:

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
| `package.json` | APP-Q1, SEC-Q7 | Root monorepo config: TypeScript 5.4.5, pnpm overrides for vulnerability patches |
| `pnpm-workspace.yaml` | APP-Q2 | Monorepo workspace definition |
| `turbo.json` | APP-Q2 | Build orchestration config |
| `.nvmrc` | APP-Q1 | Node.js version pin (v20.19.2) |
| `Dockerfile` | INF-Q1, SEC-Q6 | Root monorepo Docker build (node:20-alpine) |
| `docker/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage production Docker build |
| `docker/docker-compose.yml` | INF-Q1, INF-Q5, INF-Q6, INF-Q7, INF-Q9, OPS-Q7 | Single-container deployment config |
| `docker/docker-compose-queue-prebuilt.yml` | INF-Q1, INF-Q2, INF-Q4, INF-Q5, INF-Q7, INF-Q9, DATA-Q3, OPS-Q7 | Queue mode with Redis, Flowise, and worker containers |
| `docker/.env.example` | INF-Q2, INF-Q11, SEC-Q5, APP-Q4 | Environment variable documentation for Docker deployment |
| `packages/server/.env.example` | INF-Q2, SEC-Q1, SEC-Q5, OPS-Q1, OPS-Q3, APP-Q6 | Server environment variable documentation |
| `packages/server/package.json` | APP-Q1, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q5, SEC-Q6, OPS-Q1, OPS-Q6 | Server dependencies: Express, TypeORM, Passport, OpenTelemetry, BullMQ |
| `packages/components/package.json` | APP-Q1 | Components dependencies: LangChain, AWS SDKs, vector stores, AI frameworks |
| `packages/ui/package.json` | APP-Q1 | UI dependencies: React 18, Vite 5, MUI |
| `packages/agentflow/package.json` | APP-Q2 | Agentflow embeddable component library |
| `packages/api-documentation/package.json` | APP-Q5 | Swagger documentation server |
| `packages/api-documentation/src/yml/swagger.yml` | APP-Q5, Quick Agent Wins | OpenAPI 3.0.3 spec (2,665 lines) |
| `packages/server/src/index.ts` | INF-Q6, SEC-Q3, SEC-Q4, APP-Q5 | Express server initialization, auth middleware, metrics |
| `packages/server/src/DataSource.ts` | INF-Q2, DATA-Q2, DATA-Q3, APP-Q6 | TypeORM database configuration (SQLite/PostgreSQL/MySQL/MariaDB) |
| `packages/server/src/routes/index.ts` | APP-Q2, APP-Q3, APP-Q5 | 50+ route modules under /api/v1/ |
| `packages/server/src/database/entities/` | APP-Q2, DATA-Q2, Quick Agent Wins | 19+ TypeORM entities |
| `packages/server/src/database/migrations/` | DATA-Q2, DATA-Q3, DATA-Q4 | Database migrations for 4 DB types |
| `packages/server/src/queue/PredictionQueue.ts` | INF-Q3, APP-Q3, APP-Q4 | BullMQ prediction job queue |
| `packages/server/src/queue/UpsertQueue.ts` | INF-Q3, APP-Q4 | BullMQ vector upsert queue |
| `packages/server/src/queue/QueueManager.ts` | INF-Q3 | Queue setup and management |
| `packages/server/src/queue/RedisEventPublisher.ts` | INF-Q4, APP-Q3 | Redis pub/sub event publisher |
| `packages/server/src/queue/RedisEventSubscriber.ts` | INF-Q4 | Redis event subscriber for SSE |
| `packages/server/src/Interface.Metrics.ts` | OPS-Q2, OPS-Q3 | Business metric counter definitions |
| `packages/server/src/metrics/Prometheus.ts` | OPS-Q3 | Prometheus metrics provider |
| `packages/server/src/metrics/OpenTelemetry.ts` | OPS-Q1, OPS-Q3 | OpenTelemetry metrics and tracing provider |
| `packages/components/src/storage/S3StorageProvider.ts` | DATA-Q1 | S3 blob storage implementation |
| `packages/components/nodes/documentloaders/` | DATA-Q1 | 30+ document loader implementations |
| `packages/components/nodes/vectorstores/` | DATA-Q2 | 20+ vector store implementations |
| `packages/components/nodes/chatmodels/` | Move to AI pathway | 25+ LLM chat model integrations |
| `packages/components/evaluation/` | Move to AI pathway | Evaluation framework (LangSmith, Langfuse integration) |
| `packages/server/cypress/` | OPS-Q6 | Cypress e2e test suite |
| `.github/workflows/main.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline: lint, build, test, Cypress e2e |
| `.github/workflows/docker-image-dockerhub.yml` | INF-Q11, OPS-Q5 | Manual Docker Hub image build |
| `.github/workflows/docker-image-ecr.yml` | INF-Q11, OPS-Q5 | Manual ECR image build |
| `metrics/grafana/` | OPS-Q3, OPS-Q8 | Grafana dashboard definitions |
| `metrics/prometheus/prometheus.config.yml` | OPS-Q2, OPS-Q4 | Prometheus scrape configuration |
| `metrics/otel/otel.config.yml` | OPS-Q1 | OpenTelemetry Collector configuration |
| `README.md` | Quick Agent Wins | Repository documentation |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
| `packages/agentflow/ARCHITECTURE.md` | Quick Agent Wins | Agentflow architecture documentation |
| `artillery-load-test.yml` | OPS-Q6 | Artillery load test configuration |
