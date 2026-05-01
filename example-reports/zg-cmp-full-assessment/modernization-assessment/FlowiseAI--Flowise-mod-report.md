# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | FlowiseAI/Flowise |
| **Date** | 2025-07-17 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) — Primary service: packages/server |
| **Priority** | P2 |
| **Tags** | typescript, ai, llm |
| **Context** | Low-code UI for building LLM flows and agents. |
| **Overall Score** | 2.16 / 4.0 |

**Archetype Justification**: The primary service (packages/server) has persistent state via TypeORM (SQLite/MySQL/MariaDB/PostgreSQL), exposes CRUD endpoints for chatflows, tools, credentials, variables, and manages user-specific data (workspaces, organizations). Classified as stateful-crud. Supporting packages (ui, components, agentflow, api-documentation) are libraries/frontend with no independent backend runtime.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.16 / 4.0** | **🟠 Needs Work** |

**Scoring Calculation:**
- INF: (2+2+2+2+1+1+1+1+1+1+2) / 11 = 16/11 = 1.45
- APP: (4+2+3+3+3+2) / 6 = 17/6 = 2.83
- DATA: (3+3+2+4) / 4 = 12/4 = 3.00
- SEC: (1+1+3+3+3+1+1) / 7 = 13/7 = 1.86
- OPS: (3+1+3+1+1+3+1+1+1) / 9 = 15/9 = 1.67
- Overall: (1.45+2.83+3.00+1.86+1.67) / 5 = 10.81/5 = 2.16

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure is manually created (ClickOps). | Blocks reproducible environments, disaster recovery, and automated deployments. Foundation for all modernization. |
| 2 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined. | Services may be publicly exposed without proper isolation; high security risk. |
| 3 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or container scanning in CI/CD. | Vulnerabilities in dependencies or code reach production undetected. |
| 4 | INF-Q6: API Entry Point | 1 | Express server directly exposed — no API Gateway, ALB, or CloudFront. | No throttling, centralized auth enforcement, or WAF protection at the entry point. Triggers Move to Cloud Native pathway. |
| 5 | OPS-Q5: Deployment Strategy | 1 | Direct-to-production via manual workflow_dispatch — no staged rollout. | No ability to catch regressions before full user impact; high blast radius for deployment failures. |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 3. Swagger OpenAPI 3.0.3 spec exists at `packages/api-documentation/src/yml/swagger.yml` (2,665 lines, 14 tagged API groups with bearerAuth security). Structured JSON responses across all endpoints.
- **What it enables:** An AI agent that discovers and invokes Flowise API endpoints as tools — enabling natural-language chatflow creation, credential management, and prediction triggering without direct UI interaction.
- **Additional steps:** The OpenAPI spec covers public-facing endpoints but may not include all internal enterprise routes. Supplement with auto-generated spec from Express routes for full coverage.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3. TypeORM entities provide a clear, documented schema (19 entities: ChatFlow, ChatMessage, Tool, Credential, Variable, etc.) with centralized DataSource.ts.
- **What it enables:** A natural-language-to-SQL agent that queries chatflow metadata, message history, execution data, and evaluation results without requiring direct database access.
- **Additional steps:** Generate database schema documentation from TypeORM entity definitions. Consider read-only database replica for agent queries.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2. GitHub Actions CI/CD pipeline exists (main.yml with build/lint/test/Cypress, docker-image-ecr.yml and docker-image-dockerhub.yml for image builds).
- **What it enables:** An agent that triggers Docker image builds, checks CI status, monitors build failures, and manages release tagging via GitHub Actions API.
- **Additional steps:** Add GitHub Actions API token scoping for agent access. Consider adding deployment pipeline stages that the agent can orchestrate.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — README.md (242 lines), CONTRIBUTING.md (220 lines), API docs (2,665 lines of OpenAPI spec), ARCHITECTURE.md in agentflow package, and extensive inline code documentation.
- **What it enables:** A RAG agent that indexes Flowise documentation, API specs, and contribution guides to answer developer questions about configuration, deployment, and extension development.
- **Additional steps:** Index all markdown files, .env.example files (configuration reference), and OpenAPI spec. Use Flowise's own document loader and vector store integrations (this application is itself an AI platform — dogfood opportunity).
- **Effort:** Low

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3. OpenTelemetry SDK with auto-instrumentation configured in both server and components packages. Prometheus custom metrics (chatflow_created, prediction counters, HTTP duration). Grafana dashboards exist.
- **What it enables:** An agent that queries Prometheus metrics, correlates traces via OpenTelemetry, identifies prediction latency anomalies, and suggests root causes for chatflow execution failures.
- **Additional steps:** Configure alerting rules in Prometheus (currently absent) to give the agent signals to act on. Expose OpenTelemetry trace query API.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 2. BullMQ queue system with prediction and upsert queues, Redis pub/sub for event streaming, BullBoard dashboard for queue monitoring.
- **What it enables:** An agent that monitors BullMQ queue depth, identifies stuck jobs, manages queue scaling, and triggers prediction retries based on queue health metrics.
- **Additional steps:** Expose BullMQ metrics via the existing Prometheus integration. Add queue health API endpoints for agent consumption.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolith), INF-Q1 = 2 (no managed compute defined), APP-Q3 = 3, APP-Q4 = 3. Primary trigger (APP-Q2 < 3) met with supporting trigger (INF-Q1 < 3). |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 2 but container definitions exist (Dockerfile, docker-compose.yml, ECR workflow). Contextual guard: application is already containerized. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4. No commercial database engines detected — application uses SQLite, MySQL, MariaDB, PostgreSQL (all open source). |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 (no managed database IaC). DATA-Q3 = 2 (no version pinning, EOL status unknown). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 2 but contextual guard: BullMQ/Redis is used for job queuing, not data analytics/ETL. No data lake, streaming analytics, or ETL pipeline artifacts found. Application is an LLM orchestration platform, not a data analytics workload. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC — primary trigger met). INF-Q11 = 2 (deployment manual — primary trigger met). OPS-Q5 = 1 (no deployment strategy). OPS-Q6 = 3. |
| 7 | Move to AI | Not Triggered | — | — | Contextual guard passed (context contains "LLM" and "agents"). However, primary trigger NOT met — extensive AI/agent frameworks already present: LangChain, @langchain/aws (Bedrock), OpenAI SDK, HuggingFace, 25+ vector store integrations, MCP SDK, agent evaluation nodes. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
Flowise is a monolithic Express.js application (APP-Q2 = 2) that bundles the REST API, UI static assets, queue workers, and all LLM component integrations into a single deployable unit. The `packages/` directory provides modular code organization (server, ui, components, agentflow, api-documentation) but they compile into one deployment artifact. All 50+ route handlers are registered in a single Express app (`packages/server/src/routes/index.ts`). The database is shared across all modules via a single TypeORM DataSource.

**Compute Model Gaps (INF-Q1 = 2):**
The application is containerized (Dockerfile exists, ECR push workflow present) but no managed compute infrastructure is defined. No ECS task definitions, EKS manifests, or Lambda functions exist in the repository. Deployment target is undefined — likely Docker on EC2 or self-managed infrastructure.

**Communication Pattern Gaps:**
- APP-Q3 = 3: BullMQ provides async processing for LLM predictions and vector upserts, but most API handlers are synchronous Express routes.
- APP-Q4 = 3: Long-running LLM inference is handled asynchronously via BullMQ queue mode, demonstrating partial readiness for async patterns.

**Recommended Decomposition Approach:**
See Decomposition Strategy section below. The Strangler Fig approach is recommended, starting with extracting the prediction engine as an independent service.

**Recommended AWS Services (aligned with preferences):**
- **Compute:** Amazon EKS (preferred) for container orchestration; API Gateway (preferred) for managed API entry point with throttling and auth
- **Async:** Amazon EventBridge (preferred) to replace self-managed Redis pub/sub; Amazon SQS to complement or replace BullMQ
- **AI Integration:** Amazon Bedrock (preferred) for managed LLM inference
- **Orchestration:** AWS Step Functions for multi-step workflow coordination

**Recommended Patterns:**
- Strangler Fig for incremental service extraction
- Anti-corruption Layer between extracted services and remaining monolith
- Hexagonal Architecture for new services
- Event Sourcing for chatflow execution history

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 2):**
Flowise supports multiple database engines via environment variables: SQLite (default), MySQL, MariaDB, and PostgreSQL. `packages/server/src/DataSource.ts` configures the database connection at startup based on `DATABASE_TYPE`. No IaC defines database infrastructure — it is unclear whether production deployments use managed services (RDS/Aurora) or self-managed databases. The absence of IaC is the primary gap.

**Engine Versions and EOL Status (DATA-Q3 = 2):**
No database engine versions are pinned in the repository. `DATABASE_TYPE` specifies the engine family but not the version. The `redis:alpine` image in docker-compose lacks a version pin. EOL status is unknown for production deployments.

**Data Access Patterns (DATA-Q2 = 3):**
TypeORM provides a centralized data access layer with 19 entity definitions and migration scripts for all four supported databases. This clean ORM abstraction makes managed database migration straightforward.

**Recommended Managed Database Targets (aligned with preferences):**
- **Primary:** Amazon Aurora PostgreSQL (preferred) — compatible with existing PostgreSQL support in DataSource.ts; provides auto-scaling, Multi-AZ failover, and automated backups
- **Cache/Queue:** Amazon ElastiCache for Redis or Amazon MemoryDB — replace self-managed Redis for BullMQ and session storage
- **Alternative for NoSQL workloads:** Amazon DynamoDB (preferred) — consider for chatflow metadata if read-heavy access patterns emerge during decomposition

**Migration Tools:**
- AWS Database Migration Service (DMS) for live migration with minimal downtime
- AWS Schema Conversion Tool (SCT) if schema adjustments are needed

**Migration Approach:**
1. Define Aurora PostgreSQL in IaC (CDK or Terraform)
2. Configure `DATABASE_TYPE=postgres` with Aurora endpoint
3. Run TypeORM migrations against Aurora
4. Replace self-managed Redis with ElastiCache for Redis
5. Validate with existing Cypress e2e tests

**AWS Prescriptive Guidance:**
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero IaC exists in the repository. No Terraform, CDK, CloudFormation, Helm, or Kustomize files were found. All infrastructure (compute, databases, networking, load balancers) must be provisioned manually. This is the single largest modernization gap — without IaC, no other modernization pathway can be executed safely or reproducibly.

**Current CI/CD State (INF-Q11 = 2):**
GitHub Actions provides automated build, lint, test, and Cypress e2e testing on every push/PR (`main.yml`). Docker image builds exist but are manually triggered via `workflow_dispatch` (`docker-image-dockerhub.yml`, `docker-image-ecr.yml`). There is no automated deployment pipeline — images are pushed to registries but not deployed to any environment.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy exists. Docker images are manually built and pushed. No canary, blue/green, or rolling deployment configuration. No CodeDeploy, Argo Rollouts, or Flux CD.

**Testing Gaps (OPS-Q6 = 3):**
Cypress e2e tests run in CI but cover limited workflows (2 test directories: apikey, variables). Jest unit tests exist across packages. Artillery load test configuration is present but not integrated into CI.

**Recommended DevOps Toolchain (aligned with preferences):**
- **IaC:** AWS CDK (TypeScript — aligns with existing codebase) or Terraform for infrastructure definitions
- **Container Orchestration:** Amazon EKS (preferred) with ArgoCD for GitOps deployment
- **CI/CD Pipeline:** Extend existing GitHub Actions with:
  - Automated deployment to EKS on merge to main
  - Canary/blue-green deployment via Argo Rollouts
  - Security scanning (Dependabot, Snyk, or CodeGuru)
- **API Entry:** Amazon API Gateway (preferred) for managed entry point
- **Monitoring:** Amazon CloudWatch for alarms; integrate with existing Prometheus/Grafana

**Recommended Implementation Order:**
1. **Week 1-2:** Create CDK project defining VPC, EKS cluster, Aurora PostgreSQL, ElastiCache Redis
2. **Week 3-4:** Create EKS deployment manifests (Helm chart) for Flowise server and worker
3. **Week 5-6:** Automate deployment pipeline: GitHub Actions → ECR push → ArgoCD sync to EKS
4. **Week 7-8:** Add canary deployment strategy via Argo Rollouts; add security scanning to CI

**AWS Prescriptive Guidance:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Decomposition Strategy

> This section is included because APP-Q2 = 2 (monolith with identifiable modules but shared database and single deployment unit).

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping the monolith running. New features are built as services; existing features are migrated over time. | APP-Q2 = 2 — Flowise has recognizable package boundaries (server, components, ui, agentflow). The `packages/` structure provides natural extraction seams. | **Medium to High** — 6-18 months. Each extraction is bounded. | ✅ **Recommended.** The pnpm monorepo structure already separates concerns. BullMQ queues provide an existing async decoupling point for extraction. |
| **Conditional / Adaptive** | Containerize-then-selectively-extract. Start by deploying the monolith to EKS (preferred), then extract high-value services based on scaling needs. | Team has limited capacity. Business pressure requires quick wins (move to managed compute/DB) before architectural change. | **Low to Medium** — EKS deployment in 2-4 weeks, selective extraction over 3-12 months. | ✅ **Recommended if capacity is constrained.** The existing Dockerfile makes containerization straightforward. Extract prediction engine first for independent scaling. |
| **Big-Bang Rewrite** | Rewrite as microservices from scratch. | Almost never applicable. | **Very High** — 12-24+ months. | ⚠️ **Recommended against.** Flowise is a functional, growing product. Incremental extraction preserves existing value. |

### Recommended Extraction Order (Strangler Fig)

1. **Prediction Engine Service** — Extract BullMQ prediction queue processing into an independent EKS service. This is the highest-value extraction: LLM inference is compute-intensive and benefits from independent scaling. BullMQ already provides the async boundary.
2. **Document Store / Vector Upsert Service** — Extract the document processing and vector upsert pipeline. Already has a separate BullMQ queue (`UpsertQueue`).
3. **Authentication / Identity Service** — Extract `IdentityManager` and Passport.js strategies into a dedicated auth service. Enables SSO across future microservices.
4. **API Gateway Layer** — Place Amazon API Gateway (preferred) in front of extracted services for unified routing, throttling, and auth.

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's TypeORM data model. | Every extraction — place an ACL between extracted services and the monolith's shared database. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions (e.g., chatflow creation + credential validation + vector store provisioning). | When extracting the prediction engine — predictions span multiple components. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture execution state changes as events for audit trail and replay. | For the execution/evaluation subsystem — captures chatflow execution history. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters. | Every new service — ensures testability and infrastructure portability. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Current State | Effort Signal |
|--------|--------------|---------------|
| Module boundaries | Clear package structure (server, components, ui, agentflow). Routes organized by domain. | **Low effort** — natural extraction seams exist. |
| Data coupling | Single shared TypeORM DataSource. All 19 entities in one database. | **High effort** — database decomposition required per service. |
| Stored procedures | None (DATA-Q4 = 4). All logic in TypeScript. | **Low effort** — no database-locked logic to extract. |
| Communication patterns | BullMQ provides async boundary. Redis pub/sub for events. | **Medium effort** — async foundation exists but needs expansion to Amazon EventBridge (preferred). |
| CI/CD maturity | Build/test automated but deployment manual. | **Medium effort** — CI exists to extend; deployment pipeline needs creation. |
| Test coverage | Cypress e2e + Jest unit tests in CI. | **Medium effort** — test foundation exists but coverage gaps in e2e. |

**Calibrated Estimate:** Using the Strangler Fig approach with the recommended extraction order, expect **9-15 months** for full decomposition with incremental value delivery at each stage. The Conditional/Adaptive approach delivers initial value (managed compute + managed DB) within **4-6 weeks**.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is containerized with Dockerfiles (root `Dockerfile` using `node:20-alpine`, `docker/Dockerfile` as a multi-stage production build). Docker Compose configurations exist for local development and queue mode (`docker-compose.yml`, `docker-compose-queue-prebuilt.yml`). A GitHub Actions workflow (`docker-image-ecr.yml`) pushes images to Amazon ECR, indicating container-based deployment. However, no IaC defines managed compute (no ECS task definitions, EKS manifests, Lambda functions, or Fargate configurations). The deployment target is undefined in the repository. |
| **Gap** | No managed container orchestration defined. Container images exist but are not deployed to ECS, EKS, or Fargate via IaC. Deployment is likely manual Docker-on-EC2 or self-managed. |
| **Recommendation** | Deploy to Amazon EKS (preferred) using Helm charts. Define EKS cluster, node groups, and service manifests in CDK or Terraform. Leverage the existing multi-architecture Docker builds (linux/amd64, linux/arm64) for Graviton-based EKS nodes to reduce compute costs. |
| **Evidence** | `Dockerfile`, `docker/Dockerfile`, `docker/docker-compose.yml`, `docker/docker-compose-queue-prebuilt.yml`, `.github/workflows/docker-image-ecr.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | `packages/server/src/DataSource.ts` supports SQLite, MySQL, MariaDB, and PostgreSQL via `DATABASE_TYPE` environment variable. Database connection parameters (host, port, user, password) are configured via env vars. SSL support is available (`DATABASE_SSL`, `DATABASE_SSL_KEY_BASE64`). No IaC defines managed database resources (no `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*` in Terraform; no CDK database constructs). Docker Compose files reference external databases (no database service defined in compose). Redis is self-managed via `redis:alpine` in `docker-compose-queue-prebuilt.yml`. |
| **Gap** | No managed database definitions in IaC. It is unknown whether production uses RDS/Aurora or self-managed databases. Redis for BullMQ queues is self-managed. No Multi-AZ or automated failover configuration visible. |
| **Recommendation** | Define Amazon Aurora PostgreSQL (preferred) in IaC with Multi-AZ enabled. Replace self-managed Redis with Amazon ElastiCache for Redis or Amazon MemoryDB. Pin the `DATABASE_TYPE=postgres` default for production. Consider Amazon DynamoDB (preferred) for high-throughput chatflow metadata if read patterns justify it. |
| **Evidence** | `packages/server/src/DataSource.ts`, `docker/docker-compose-queue-prebuilt.yml` (redis:alpine), `packages/server/.env.example`, `docker/.env.example` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | BullMQ provides queue-based processing with two queues: `prediction` (LLM inference) and `upsert` (vector store operations), managed by `QueueManager.ts`. BullBoard dashboard is available for queue monitoring. This is application-level queue management — not dedicated workflow orchestration. No AWS Step Functions, Temporal, or Camunda detected. Using stateful-crud archetype rubric: simple state machines in code with some structure (BullMQ queues) but no dedicated orchestration service. |
| **Gap** | BullMQ provides job queuing but not workflow orchestration with visual management, retry logic, or state machine coordination. Multi-step operations (chatflow creation → component initialization → credential validation → prediction) are handled in application code without explicit orchestration. |
| **Recommendation** | For multi-step workflows that span service boundaries (especially post-decomposition), adopt AWS Step Functions. The existing BullMQ queue pattern maps well to Step Functions task states. Retain BullMQ for simple job queuing within services; use Step Functions for cross-service orchestration. |
| **Evidence** | `packages/server/src/queue/QueueManager.ts`, `packages/server/src/queue/PredictionQueue.ts`, `packages/server/src/queue/UpsertQueue.ts` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | BullMQ with Redis provides async messaging for prediction and upsert operations. `RedisEventPublisher.ts` and `RedisEventSubscriber.ts` implement Redis pub/sub for SSE event streaming. `QueueManager.ts` configures Redis connection with TLS support. All messaging infrastructure is self-managed — Redis runs as `redis:alpine` in Docker Compose. No AWS managed messaging (SQS, SNS, EventBridge, MSK) is used. Using stateful-crud archetype rubric: self-managed messaging for cross-service flows. |
| **Gap** | Redis is self-managed, requiring manual patching, scaling, and monitoring. No managed messaging services. Redis pub/sub lacks message persistence and dead-letter queue support that SQS/EventBridge provide. |
| **Recommendation** | Replace self-managed Redis with Amazon ElastiCache for Redis (managed) for BullMQ queue backend. For event distribution (currently Redis pub/sub), migrate to Amazon EventBridge (preferred) for durable, filterable event routing. This enables fan-out to multiple consumers as services are extracted during decomposition. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `packages/server/src/queue/QueueManager.ts`, `packages/server/src/queue/RedisEventPublisher.ts`, `packages/server/src/queue/RedisEventSubscriber.ts`, `docker/docker-compose-queue-prebuilt.yml` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL configuration exists in the repository. No IaC of any kind defines network infrastructure. The Express server listens on port 3000 (configurable via `PORT` env var) with CORS configured via `CORS_ORIGINS` environment variable. The `TRUST_PROXY` setting exists for load balancer scenarios but no load balancer is defined. Docker Compose uses a bridge network (`flowise-net`) for local development only. |
| **Gap** | No network segmentation, no private subnets, no security groups. Services may be publicly exposed without proper isolation. This is a critical security gap for any production deployment. |
| **Recommendation** | Define VPC with public/private subnets in IaC (CDK/Terraform). Deploy application containers in private subnets. Place Amazon API Gateway (preferred) or ALB in public subnet as the entry point. Create least-privilege security groups. Add VPC endpoints for AWS service access (S3, Secrets Manager, ECR). |
| **Evidence** | `packages/server/src/index.ts` (server.listen on port 3000), `packages/server/.env.example` (TRUST_PROXY, CORS_ORIGINS), `docker/docker-compose-queue-prebuilt.yml` (flowise-net bridge network) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Express server listens directly on a configurable port (default 3000). The health check in Docker Compose targets `http://localhost:${PORT}/api/v1/ping`. No API Gateway, ALB, CloudFront, or AppSync is defined. Rate limiting is implemented in application code (`express-rate-limit` with optional Redis-backed limiter), but there is no infrastructure-level throttling or WAF protection. The `TRUST_PROXY` setting suggests awareness of load balancer scenarios but no load balancer is configured. |
| **Gap** | No managed API entry point. Direct service exposure lacks centralized throttling, request validation, WAF protection, and TLS termination at the infrastructure level. Application-level rate limiting exists but is not a substitute for infrastructure-level protection. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point with: throttling policies, request validation, WAF integration, and Cognito/JWT authorizer. For the UI static assets, consider Amazon CloudFront for CDN delivery. The existing `/api/v1/` URL structure maps cleanly to API Gateway routes. |
| **Evidence** | `packages/server/src/index.ts` (server.listen, rate limiting), `docker/docker-compose.yml` (healthcheck on localhost), `packages/server/.env.example` (TRUST_PROXY, NUMBER_OF_PROXIES) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No ASG, ECS service scaling, EKS HPA, Lambda concurrency, DynamoDB auto-scaling, or Aurora auto-scaling definitions found. The Docker Compose configurations run fixed container counts. The `WORKER_CONCURRENCY` environment variable controls BullMQ worker parallelism but is static. |
| **Gap** | All capacity is statically provisioned. No ability to respond to traffic spikes or scale down during low demand. LLM prediction workloads are inherently variable — inference latency and throughput depend on model complexity and request volume. |
| **Recommendation** | After deploying to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on CPU, memory, and custom metrics (BullMQ queue depth, prediction latency). For Aurora PostgreSQL, enable auto-scaling read replicas. For ElastiCache Redis, configure auto-scaling for shards. |
| **Evidence** | No auto-scaling files found. `packages/server/.env.example` (WORKER_CONCURRENCY is static), `docker/docker-compose-queue-prebuilt.yml` (fixed container count) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. No `aws_backup_plan`, RDS `backup_retention_period`, DynamoDB PITR, S3 versioning, or EBS snapshot policies defined. The default SQLite database stores data in `~/.flowise/database.sqlite` with no backup mechanism. When using external databases (MySQL/PostgreSQL), backup configuration is entirely dependent on the external provider — not defined in this repository. |
| **Gap** | No automated backups for any data store. A data loss event would require manual recovery with no guaranteed restore point. SQLite users have zero backup protection. External database users have no backup configuration defined or documented in the repository. |
| **Recommendation** | Define automated backups in IaC: Aurora PostgreSQL with automated backups and PITR, ElastiCache Redis with daily snapshots, S3 versioning for blob storage. Create an AWS Backup plan covering all data stores. Document restore procedures and test them quarterly. |
| **Evidence** | `packages/server/src/DataSource.ts` (SQLite default path ~/.flowise/database.sqlite), `packages/server/.env.example` (no backup-related config) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. No IaC defines availability zones for any resource. Docker Compose runs all containers on a single host. No load balancer with cross-zone configuration. No database Multi-AZ failover settings. |
| **Gap** | All resources run in a single failure domain. An AZ failure would take down the entire application with no automatic recovery. |
| **Recommendation** | Deploy EKS (preferred) cluster across 2+ AZs. Configure Aurora PostgreSQL with Multi-AZ failover. Deploy ElastiCache Redis with Multi-AZ replication. Place ALB or API Gateway in front with cross-zone load balancing. |
| **Evidence** | No AZ configuration found. `docker/docker-compose.yml`, `docker/docker-compose-queue-prebuilt.yml` (single-host Docker) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files found in the repository. No Terraform (.tf, .tfvars), CloudFormation (*.cfn.yaml), CDK (cdk.json, constructs), Helm (Chart.yaml), Kustomize (kustomization.yaml), or Ansible files exist. All infrastructure must be created manually. Docker Compose files exist for local development but do not constitute production IaC. |
| **Gap** | 0% IaC coverage. All infrastructure is ClickOps. No reproducible environments, no disaster recovery automation, no infrastructure audit trail. This is the single largest modernization blocker — without IaC, no other pathway can be executed safely. |
| **Recommendation** | Create an AWS CDK project (TypeScript — aligns with existing codebase) defining: VPC, EKS cluster, Aurora PostgreSQL, ElastiCache Redis, API Gateway, S3 buckets, IAM roles, CloudWatch alarms, and Backup plans. Use CDK Pipelines for infrastructure CI/CD. Target 90%+ IaC coverage as the foundation for all other modernization initiatives. |
| **Evidence** | Repository-wide scan found no .tf, .cfn.yaml, .cfn.json, cdk.json, Chart.yaml, kustomization.yaml, or Ansible playbook files. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI pipeline (`main.yml`) automates: pnpm install, lint, build, test:coverage, Cypress e2e tests on every push/PR. Docker image build workflows exist for DockerHub (`docker-image-dockerhub.yml`) and ECR (`docker-image-ecr.yml`) but are manually triggered (`workflow_dispatch`). Additional workflows: `publish-agentflow.yml` (npm publish), `test_docker_build.yml` (Docker build test), `proprietary-path-guard.yml` (path check). No automated deployment pipeline — images are pushed to registries but never deployed automatically. No rollback mechanism. |
| **Gap** | Build and test are automated. Deployment is entirely manual. No automated rollback. Docker image builds require manual triggering. Gap between CI (automated) and CD (absent). |
| **Recommendation** | Extend GitHub Actions to include automated deployment: on merge to main → build image → push to ECR → deploy to EKS via ArgoCD or Flux CD. Add canary deployment strategy. Automate Docker image builds on release tags instead of manual workflow_dispatch. Add security scanning step (Dependabot, Snyk). |
| **Evidence** | `.github/workflows/main.yml`, `.github/workflows/docker-image-dockerhub.yml`, `.github/workflows/docker-image-ecr.yml`, `.github/workflows/publish-agentflow.yml`, `.github/workflows/test_docker_build.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript/JavaScript throughout the entire monorepo. Node.js 20 runtime. React (UI), Express (server), Vite (build tooling). First-class AWS SDK coverage (`@aws-sdk/client-bedrock-runtime`, `@aws-sdk/client-s3`, `@aws-sdk/client-secrets-manager`, `@aws-sdk/client-dynamodb`, `@aws-sdk/client-sns`, `@aws-sdk/client-sts`, `@aws-sdk/client-kendra`). Broad cloud-native tooling ecosystem. |
| **Gap** | None. TypeScript/JavaScript is a tier-1 language for AWS cloud-native development with full SDK coverage and mature tooling. |
| **Recommendation** | No action needed. Continue with TypeScript. The CDK project for IaC should also use TypeScript for consistency. |
| **Evidence** | `package.json` (root), `packages/server/package.json`, `packages/components/package.json`, `packages/ui/package.json`, `packages/agentflow/package.json` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Flowise is a monolith with identifiable modules. The pnpm monorepo has 5 packages (server, ui, components, agentflow, api-documentation) but they compile into a single deployable unit. All 50+ route handlers are registered in one Express app (`packages/server/src/routes/index.ts`). A single TypeORM DataSource serves all 19 entities across all modules. Docker Compose runs one `flowise` service + one `flowise-worker` (same codebase, different entry point). The UI is bundled as static assets served by the server. Cross-module data access occurs through the shared database. |
| **Gap** | Single deployment unit with shared database. No independent scaling per module. All route handlers in one Express app. The `packages/` structure provides code organization but not deployment isolation. Database coupling prevents independent data ownership. |
| **Recommendation** | Apply Strangler Fig decomposition (see Decomposition Strategy section). Priority extractions: Prediction Engine (BullMQ already provides async boundary), Document Store, Authentication. The existing package structure provides natural extraction seams. |
| **Evidence** | `packages/server/src/routes/index.ts` (50+ route registrations), `packages/server/src/DataSource.ts` (single DataSource), `docker/docker-compose-queue-prebuilt.yml` (single service + worker), `packages/server/src/index.ts` (monolithic App class) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Using stateful-crud archetype rubric. BullMQ provides async processing for the two most important operations: LLM predictions and vector store upserts. Redis pub/sub enables SSE streaming for real-time prediction responses. Queue mode splits the application into main (API) and worker (processing) processes, enabling horizontal scaling of the compute-intensive prediction workload. Most CRUD API routes (chatflows, tools, credentials, etc.) remain synchronous Express handlers, which is appropriate for simple CRUD operations. |
| **Gap** | Async patterns exist for key workflows (prediction, upsert) but cross-service state propagation relies on direct database access rather than events. No event bus for entity lifecycle events (chatflow created, credential updated). |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for entity lifecycle events as services are extracted. Keep synchronous HTTP for CRUD operations within services. The existing BullMQ pattern is a solid async foundation — extend it with managed messaging as decomposition progresses. |
| **Evidence** | `packages/server/src/queue/PredictionQueue.ts`, `packages/server/src/queue/UpsertQueue.ts`, `packages/server/src/queue/RedisEventPublisher.ts`, `packages/server/src/routes/index.ts` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Using stateful-crud archetype rubric. LLM inference — the primary long-running operation — is handled asynchronously via BullMQ prediction queue with configurable worker concurrency (`WORKER_CONCURRENCY`). SSE streaming delivers real-time progress to clients. Vector store upserts (document embedding and indexing) are handled by a separate BullMQ upsert queue. Both queues support job removal based on age (`REMOVE_ON_AGE`) and count (`REMOVE_ON_COUNT`). Some operations may still block: document loading and parsing can be time-variable but are not consistently queued. |
| **Gap** | Most long-running operations are async (prediction, upsert). Some edge cases — document loading, large file processing, external API calls in custom nodes — may still execute synchronously within request handlers. No status polling API for async jobs (BullBoard dashboard exists but is admin-only). |
| **Recommendation** | Add a public job status API endpoint for async prediction and upsert operations. Ensure all data-volume-dependent operations (document loading, large imports) are routed through BullMQ queues. Consider AWS Step Functions for multi-step operations post-decomposition. |
| **Evidence** | `packages/server/src/queue/QueueManager.ts`, `packages/server/src/queue/PredictionQueue.ts`, `packages/server/src/queue/UpsertQueue.ts`, `packages/server/.env.example` (WORKER_CONCURRENCY, REMOVE_ON_AGE) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Consistent URL-path versioning: all API endpoints are registered under `/api/v1/` in `packages/server/src/routes/index.ts`. The middleware enforces case-sensitive `/api/v1/` matching. OpenAPI spec (`packages/api-documentation/src/yml/swagger.yml`) documents the v1 API with 2,665 lines covering 14 tagged groups. Only v1 exists — no evidence of backward-compatible v2 or version negotiation. |
| **Gap** | Versioning strategy exists and is applied consistently to all endpoints. However, only v1 exists with no evidence of version migration support or backward compatibility guarantees. No version deprecation policy documented. |
| **Recommendation** | Document API versioning policy. When introducing breaking changes, implement v2 routes alongside v1 with a documented deprecation timeline. The existing `/api/v1/` structure is well-positioned for multi-version support. |
| **Evidence** | `packages/server/src/routes/index.ts` (router.use('/api/v1', ...)), `packages/server/src/index.ts` (URL_CASE_SENSITIVE_REGEX for /api/v1/), `packages/api-documentation/src/yml/swagger.yml` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Flowise is a single monolith, so inter-service discovery is not currently needed. External service endpoints (Redis, database) are configured via environment variables (`REDIS_HOST`, `REDIS_PORT`, `DATABASE_HOST`, `DATABASE_PORT`). The Docker Compose `flowise-net` bridge network provides DNS-based service discovery for local development (worker references `redis` by hostname). No AWS service discovery, Consul, or service mesh configured. |
| **Gap** | Environment variables for endpoints without dynamic discovery. Acceptable for a monolith but becomes a problem during decomposition — hard-coded or env-var endpoints create deployment coupling between extracted services. |
| **Recommendation** | As services are extracted, implement service discovery via EKS (preferred) internal DNS (CoreDNS) or AWS Cloud Map. API Gateway (preferred) can serve as the service catalog for external consumers. Avoid hard-coded service endpoints in extracted services. |
| **Evidence** | `packages/server/.env.example` (REDIS_HOST, DATABASE_HOST), `docker/docker-compose-queue-prebuilt.yml` (redis service name), `packages/server/src/queue/QueueManager.ts` (Redis connection from env vars) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | S3 storage is supported via `multer-s3` and `@aws-sdk/client-s3`. The `STORAGE_TYPE` environment variable supports `local`, `s3`, `gcs`, and `azure`. Document loaders in `packages/components/nodes/documentloaders` parse PDFs, EPUBs, Office documents, and web content. Document store entities (`DocumentStore`, `DocumentStoreFileChunk`) manage document metadata and chunks. However, S3 is not the default (`STORAGE_TYPE` defaults to `local`), and no automated parsing pipeline is defined in IaC. |
| **Gap** | S3 is available as a storage option but not default. No automated parsing pipeline (e.g., Textract integration) defined. Document processing relies on application-layer libraries (pdf-parse, pdfjs-dist, mammoth) rather than managed services. |
| **Recommendation** | Set `STORAGE_TYPE=s3` as the production default. Define S3 buckets in IaC with lifecycle policies. Add Amazon Textract integration for structured data extraction from documents. Leverage the existing document loader architecture to add Textract as a processing node. |
| **Evidence** | `packages/server/.env.example` (STORAGE_TYPE, S3_STORAGE_*), `packages/server/package.json` (multer-s3, @aws-sdk/client-s3), `packages/components/nodes/documentloaders/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeORM provides a centralized data access layer. `packages/server/src/DataSource.ts` configures the single data source. 19 entity definitions in `packages/server/src/database/entities/` define the schema. Migration scripts exist for all four supported database engines (sqlite, mysql, mariadb, postgres). Services access data through TypeORM repositories via the shared DataSource. However, `packages/components` has some direct database access for vector store operations (Postgres/pgvector, Redis, MongoDB) that bypasses the centralized TypeORM layer. |
| **Gap** | Mostly centralized via TypeORM. Some direct database access in the components package for vector store integrations (necessary for specialized vector operations but breaks the unified access pattern). |
| **Recommendation** | Maintain TypeORM as the primary data access layer. For vector store operations, document the intentional bypass and ensure connection pooling is managed centrally. During decomposition, each extracted service should own its data access layer with clear contracts. |
| **Evidence** | `packages/server/src/DataSource.ts`, `packages/server/src/database/entities/`, `packages/server/src/database/migrations/`, `packages/components/nodes/vectorstores/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No database engine version is pinned in the repository. `packages/server/src/DataSource.ts` configures `DATABASE_TYPE` (sqlite, mysql, mariadb, postgres) without specifying engine versions. Docker Compose uses `redis:alpine` without a version tag (always pulls latest). No IaC exists to pin engine versions (no `engine_version` on RDS, no `EngineVersion` in CloudFormation). The TypeORM version (`^0.3.6`) supports a range of engine versions but none are enforced. |
| **Gap** | No version pinning anywhere. EOL status is unknown for production deployments. `redis:alpine` without version pin risks pulling breaking changes. No documented version-update procedure. |
| **Recommendation** | Pin Redis image version in Docker Compose (e.g., `redis:7.2-alpine`). Define database engine versions in IaC when creating Aurora PostgreSQL (preferred). Document supported engine version matrix and EOL tracking. Add version compatibility checks to CI. |
| **Evidence** | `packages/server/src/DataSource.ts` (no version parameters), `docker/docker-compose-queue-prebuilt.yml` (redis:alpine, no version pin), `packages/server/.env.example` (DATABASE_TYPE without version) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found in the repository. All TypeORM migrations in `packages/server/src/database/migrations/` are pure schema DDL (CREATE TABLE, ALTER TABLE, ADD COLUMN). All business logic is implemented in the TypeScript application layer. No `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` found. The ORM abstraction ensures database portability across SQLite, MySQL, MariaDB, and PostgreSQL. |
| **Gap** | None. All business logic is in the application layer. No database-coupled logic to extract during modernization. |
| **Recommendation** | No action needed. Continue keeping business logic in the application layer. This clean separation is a significant modernization advantage — database engine migration is straightforward. |
| **Evidence** | `packages/server/src/database/migrations/sqlite/`, `packages/server/src/database/migrations/mysql/`, `packages/server/src/database/migrations/mariadb/`, `packages/server/src/database/migrations/postgres/` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration exists (no IaC). Application-level logging via Winston (`packages/server/src/utils/logger.ts`) captures HTTP requests with method, URL, and params. Sensitive fields are sanitized via `LOG_SANITIZE_BODY_FIELDS` and `LOG_SANITIZE_HEADER_FIELDS` environment variables. Request logger writes to file via `winston-daily-rotate-file`. S3 log streaming is supported (`s3-streamlogger`). However, no immutable log storage (no S3 Object Lock), no CloudTrail for API-level audit trails, and no centralized log aggregation. |
| **Gap** | No CloudTrail or equivalent infrastructure audit logging. Application logs exist but are not immutable. No audit trail for infrastructure-level actions. |
| **Recommendation** | Enable AWS CloudTrail with log file validation and S3 Object Lock for immutable storage. Define CloudTrail in IaC. For application audit logging, consider sending Winston logs to Amazon CloudWatch Logs with defined retention policies. Add audit log entity for tracking user actions (chatflow modifications, credential access) at the application level. |
| **Evidence** | `packages/server/src/utils/logger.ts`, `packages/server/.env.example` (LOG_PATH, LOG_LEVEL, LOG_SANITIZE_*), `packages/server/package.json` (winston, winston-daily-rotate-file, s3-streamlogger) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS configuration exists. No IaC defines encryption at rest for any resource. The S3 storage configuration (`S3_STORAGE_*` env vars) does not include SSE-KMS settings. Database SSL is supported via `DATABASE_SSL` and `DATABASE_SSL_KEY_BASE64` environment variables, providing encryption in transit but not at rest. Application-level encryption exists for credentials (`crypto-js` in `packages/server/package.json` for encrypting stored credentials via `FLOWISE_SECRETKEY_OVERWRITE`), but this is application-layer encryption, not infrastructure encryption at rest. |
| **Gap** | No KMS-managed encryption at rest for databases, S3 buckets, or Redis. Application-level credential encryption exists but does not cover the full data estate. No encryption configuration in IaC (no IaC exists). |
| **Recommendation** | Define customer-managed KMS keys in IaC for: Aurora PostgreSQL (storage encryption), S3 buckets (SSE-KMS), ElastiCache Redis (at-rest encryption), and EBS volumes. Enable KMS key rotation. The existing `FLOWISE_SECRETKEY_OVERWRITE` for application-layer credential encryption should be complemented by infrastructure-level encryption. |
| **Evidence** | `packages/server/.env.example` (DATABASE_SSL, no KMS config), `packages/server/package.json` (crypto-js), `docker/.env.example` (S3_STORAGE_* without encryption config) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive JWT-based authentication. `packages/server/src/index.ts` implements middleware that: (1) checks if path is in whitelist (ping, public endpoints), (2) verifies JWT token for internal requests, (3) validates API key for external requests. Auth libraries: `jsonwebtoken`, `passport`, `passport-jwt`, `passport-local`, `passport-auth0`, `passport-github`, `passport-google-oauth20`, `passport-openidconnect`. JWT configuration includes token expiry, refresh tokens, issuer, and audience validation. Rate limiting via `express-rate-limit` with optional Redis backing. |
| **Gap** | Token-based auth on all external endpoints. Internal/private-subnet endpoints may lack auth if relying on `x-request-from: internal` header (network isolation not enforced since no VPC exists). Public endpoints (ping, public-chatflows, public-chatbots) bypass auth by design but are not protected by API Gateway throttling. |
| **Recommendation** | Add Amazon API Gateway (preferred) with Cognito authorizer for infrastructure-level auth enforcement. Ensure the `x-request-from: internal` header is only trusted when network isolation (VPC private subnets, security groups) is in place. Current application-level auth is solid — complement it with infrastructure-level auth for defense in depth. |
| **Evidence** | `packages/server/src/index.ts` (auth middleware), `packages/server/package.json` (passport, jsonwebtoken, passport-auth0, etc.), `packages/server/.env.example` (JWT_* config) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Passport.js is configured with multiple external IdP strategies: Auth0, GitHub OAuth, Google OAuth2, OIDC (generic). `IdentityManager` handles SSO initialization. Local authentication (username/password with bcrypt hashing) is also supported as a fallback. Enterprise features include workspace-level access control, role-based permissions, and organization management. |
| **Gap** | External IdP integration exists for most flows (Auth0, GitHub, Google, OIDC). Local authentication paths remain for users who don't use SSO. No single IdP enforcement — users can authenticate via local credentials or SSO depending on configuration. |
| **Recommendation** | Consider migrating to Amazon Cognito as the centralized IdP with federated sign-in from Auth0/Google/GitHub. This consolidates identity management and enables consistent access policies. For enterprise deployments, enforce SSO-only authentication to eliminate local credential management. |
| **Evidence** | `packages/server/package.json` (passport-auth0, passport-github, passport-google-oauth20, passport-openidconnect), `packages/server/src/index.ts` (identityManager.initializeSSO) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS Secrets Manager is supported for secret storage. `@aws-sdk/client-secrets-manager` is a dependency. The `SECRETKEY_STORAGE_TYPE` env var supports `local` or `aws`. When set to `aws`, encryption keys and auth secrets (JWT secrets, session secret, token hash secret) are stored in and retrieved from AWS Secrets Manager. The `.env.example` documents the AWS configuration: `SECRETKEY_AWS_ACCESS_KEY`, `SECRETKEY_AWS_REGION`, `SECRETKEY_AWS_NAME`. However, many secrets (database credentials, SMTP, Redis, S3 keys) are still configured via environment variables or `.env` files. No rotation configured. |
| **Gap** | Primary credentials (encryption keys, JWT secrets) can use Secrets Manager. Database credentials, Redis passwords, S3 access keys, and SMTP credentials remain in environment variables. No secret rotation configured. `.env.example` files contain placeholder secret patterns. |
| **Recommendation** | Expand Secrets Manager usage to cover all production secrets: database credentials, Redis passwords, S3 access keys, SMTP credentials. Configure automatic rotation for database credentials via Secrets Manager rotation lambdas. Remove static secret references from `.env` files in production. Define Secrets Manager resources in IaC. |
| **Evidence** | `packages/server/package.json` (@aws-sdk/client-secrets-manager), `packages/server/.env.example` (SECRETKEY_STORAGE_TYPE=local|aws, SECRETKEY_AWS_*), `docker/.env.example` (DATABASE_PASSWORD, REDIS_PASSWORD in env vars) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Dockerfiles use `node:20-alpine` as the base image — a minimal image but not CIS-hardened. Root `Dockerfile` runs as non-root user (`USER node`) after build. `docker/Dockerfile` production build does not set non-root user. No SSM Patch Manager, AWS Inspector, Snyk, or Bottlerocket. No vulnerability scanning in CI/CD pipeline. No EC2 Image Builder. The `pnpm.overrides` in `package.json` pin specific dependency versions to address known vulnerabilities (braces, cross-spawn, ws, semver), indicating manual vulnerability management. |
| **Gap** | No managed patching strategy. No vulnerability scanning. Default Alpine images without hardening. Manual dependency override approach for vulnerability mitigation is reactive, not proactive. |
| **Recommendation** | Enable Amazon ECR image scanning for container vulnerability detection. Add Snyk or AWS Inspector to CI/CD pipeline. Consider Bottlerocket as the EKS node OS for reduced attack surface. Enable Dependabot for automated dependency vulnerability alerts. Replace manual `pnpm.overrides` with automated scanning. |
| **Evidence** | `Dockerfile` (node:20-alpine, USER node), `docker/Dockerfile` (node:20-alpine, no USER directive), `package.json` (pnpm.overrides for security patches) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into the CI/CD pipeline. GitHub Actions `main.yml` runs lint, build, test:coverage, and Cypress e2e — no SAST, DAST, dependency scanning, or container scanning steps. No `.snyk` policy file. No `dependabot.yml` configuration. No CodeGuru Reviewer. No npm audit or pnpm audit in pipeline. The `pnpm.overrides` in root `package.json` manually pins specific dependency versions to address vulnerabilities, but this is reactive and manual. |
| **Gap** | Zero security scanning in the pipeline. No Dependabot, no SAST, no container scanning. Vulnerabilities in the 200+ dependencies reach production undetected. The manual override approach demonstrates awareness of the problem but lacks systematic coverage. |
| **Recommendation** | Add immediately: (1) Dependabot for automated dependency vulnerability alerts, (2) `pnpm audit` step in GitHub Actions CI, (3) Amazon ECR image scanning for container vulnerabilities. Add next: (4) Semgrep or CodeGuru Reviewer for SAST, (5) security gate in pipeline that blocks on critical findings. |
| **Evidence** | `.github/workflows/main.yml` (no security steps), No `.snyk` or `dependabot.yml` found, `package.json` (pnpm.overrides for manual security patches) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry SDK is heavily integrated. Both `packages/server` and `packages/components` include comprehensive OTEL dependencies: `@opentelemetry/api` (1.9.0), `@opentelemetry/sdk-node`, `@opentelemetry/auto-instrumentations-node`, trace exporters via gRPC, HTTP, and Proto. `packages/server/src/metrics/OpenTelemetry.ts` implements metric collection with configurable OTLP endpoints. `@arizeai/openinference-instrumentation-langchain` instruments LangChain calls for LLM observability. Metrics collector configuration exists in `metrics/otel/otel.config.yml`. Trace propagation via auto-instrumentation covers Express, HTTP, and database calls within the monolith. |
| **Gap** | Tracing covers the monolith's internal operations well. Since this is a single-service monolith, cross-service trace propagation is not yet needed. However, the OTEL setup focuses on metrics export — trace exporter configuration exists but trace export endpoints are not explicitly configured in `.env.example`. LangChain instrumentation provides LLM-specific tracing. |
| **Recommendation** | Configure trace export endpoint in `.env.example` documentation. After decomposition, ensure trace context propagation headers (traceparent, X-Amzn-Trace-Id) are forwarded between extracted services. Consider AWS X-Ray as the trace backend for native AWS integration, or continue with OTEL Collector export to Grafana/Jaeger. |
| **Evidence** | `packages/server/package.json` (@opentelemetry/*), `packages/components/package.json` (@opentelemetry/*, @arizeai/openinference-instrumentation-langchain), `packages/server/src/metrics/OpenTelemetry.ts`, `metrics/otel/otel.config.yml` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No error budget tracking. No CloudWatch alarms or SLO dashboards defined. The Prometheus configuration (`metrics/prometheus/prometheus.config.yml`) defines scrape targets but no alerting rules. Grafana dashboards exist but focus on operational metrics (HTTP requests, version info), not SLO tracking. |
| **Gap** | No formal definition of acceptable service levels for critical user journeys (prediction latency, chatflow creation success rate, document upload completion). No error budgets. Operations are reactive — there is no objective measure of when the service is degrading. |
| **Recommendation** | Define SLOs for critical journeys: (1) Prediction p99 latency < 30s, (2) API availability > 99.9%, (3) Document upsert success rate > 99%. Implement SLO monitoring via Prometheus recording rules and Grafana dashboards. Add error budget tracking. Consider Amazon CloudWatch SLO monitoring when migrating to AWS managed services. |
| **Evidence** | `metrics/prometheus/prometheus.config.yml` (no alert rules), `metrics/grafana/grafana.dashboard.app.json.txt`, `metrics/grafana/grafana.dashboard.server.json.txt` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Custom business metrics are published via Prometheus and OpenTelemetry. `FLOWISE_METRIC_COUNTERS` enum defines: `chatflow_created`, `agentflow_created`, `assistant_created`, `tool_created`, `vector_upserted`, `chatflow_prediction_internal`, `chatflow_prediction_external`, `agentflow_prediction_internal`, `agentflow_prediction_external`. HTTP request duration histograms and request counters provide performance metrics. Grafana dashboards exist in `metrics/grafana/` for app and server views. PostHog telemetry (`posthog-node`) provides product analytics. |
| **Gap** | Good business metrics for chatflow/agentflow lifecycle events. Missing: per-chatflow prediction latency breakdown, error rates by chatflow, document processing throughput, vector store operation latency, user engagement metrics. Metrics are not systematically tracked across all features. |
| **Recommendation** | Extend business metrics to cover: per-chatflow prediction latency, error rates by chatflow type, document processing throughput, queue depth over time. Integrate Prometheus alerting rules for business metric thresholds. The existing metric infrastructure is solid — expand coverage. |
| **Evidence** | `packages/server/src/Interface.Metrics.ts` (FLOWISE_METRIC_COUNTERS enum), `packages/server/src/metrics/Prometheus.ts`, `packages/server/src/metrics/OpenTelemetry.ts`, `metrics/grafana/` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. Prometheus scrape configuration exists (`metrics/prometheus/prometheus.config.yml`) but defines no alerting rules. No Prometheus Alertmanager configuration. No CloudWatch anomaly detection. No PagerDuty, OpsGenie, or other incident notification integration. The Grafana dashboards provide visualization but no alert thresholds. |
| **Gap** | No alerting of any kind. No static threshold alarms, no anomaly detection. Failures are discovered by users, not by monitoring systems. |
| **Recommendation** | Add Prometheus alerting rules for: (1) HTTP error rate > 5%, (2) prediction queue depth growing, (3) p99 latency exceeding SLO thresholds, (4) Redis connection failures. Configure Alertmanager with notification channels (PagerDuty, Slack). When migrating to AWS, add CloudWatch anomaly detection for key metrics. |
| **Evidence** | `metrics/prometheus/prometheus.config.yml` (scrape config only, no alert rules), No Alertmanager configuration found |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Docker image builds are manually triggered via `workflow_dispatch` in GitHub Actions. `docker-image-dockerhub.yml` and `docker-image-ecr.yml` push images to registries but do not deploy. No canary, blue/green, or rolling deployment strategy exists. No CodeDeploy, Argo Rollouts, Flux CD, or feature flag configuration. Deployments are direct-to-production with no staged rollout or automatic rollback. |
| **Gap** | No deployment strategy. Direct-to-production with no safety net. No ability to catch regressions before full user impact. No automatic rollback on failure. |
| **Recommendation** | Implement canary deployment via Argo Rollouts on EKS (preferred). Configure: 20% traffic → canary → monitor Prometheus metrics → promote or rollback. Add feature flags (LaunchDarkly, AWS AppConfig) for progressive feature rollout. Automate the deployment pipeline: merge to main → build → push to ECR → deploy canary → promote. |
| **Evidence** | `.github/workflows/docker-image-dockerhub.yml` (workflow_dispatch), `.github/workflows/docker-image-ecr.yml` (workflow_dispatch), No CodeDeploy or Argo Rollouts configuration found |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Cypress e2e tests in `packages/server/cypress/e2e/` run against a live server in CI (`main.yml`). Test directories: `1-apikey` (API key management), `2-variables` (variable management). The CI pipeline starts the server, waits for it to be available, then runs Cypress tests in Chrome. Jest unit tests exist across packages (`packages/server`, `packages/components`, `packages/agentflow`). Artillery load test configuration (`artillery-load-test.yml`) exists for performance testing but is not integrated into CI. `supertest` is a dev dependency for HTTP-level testing. |
| **Gap** | Integration tests exist for some critical workflows (API key, variables) and run in CI. Coverage is limited — many critical workflows (chatflow creation, prediction execution, document upload, credential management) lack e2e coverage. Artillery load test is not automated. |
| **Recommendation** | Expand Cypress e2e coverage to include: chatflow creation/execution, prediction workflow, document upload/processing, credential management. Integrate Artillery load tests into CI for performance regression detection. Add contract tests for the OpenAPI spec to ensure API changes don't break consumers. |
| **Evidence** | `packages/server/cypress/e2e/` (1-apikey, 2-variables), `.github/workflows/main.yml` (Cypress run in CI), `artillery-load-test.yml`, `packages/server/package.json` (supertest, cypress, jest) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, SSM Automation documents, Lambda remediation, Step Functions incident workflows, or self-healing automation found. No `SECURITY.md` incident response section (the file exists but covers vulnerability disclosure, not operational incident response). No on-call rotation configuration. |
| **Gap** | Incident response is entirely ad hoc. No documented runbooks for common failures (database connection issues, Redis failures, queue backlogs, OOM errors). No automated remediation. |
| **Recommendation** | Create machine-readable runbooks for: (1) Redis connection failure → restart worker, check ElastiCache health, (2) prediction queue backlog → scale workers, check LLM endpoint availability, (3) database connection pool exhaustion → check active connections, restart if needed. Implement SSM Automation documents for common remediation actions. |
| **Evidence** | `SECURITY.md` (vulnerability disclosure only), No runbook files found in repository |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Grafana dashboards exist (`metrics/grafana/grafana.dashboard.app.json.txt`, `grafana.dashboard.server.json.txt`) but have no named owners or team attribution. No CODEOWNERS file in the repository. No team tags on metrics or alarms. No SLO definitions with team attribution. The metrics provider implementation is comprehensive but observability assets are unowned. |
| **Gap** | No observability ownership. Dashboards exist but no one is responsible for maintaining them, responding to alerts (which don't exist), or tracking SLOs. |
| **Recommendation** | Add CODEOWNERS file with team ownership of `metrics/`, observability code, and alarm definitions. Add team labels to Prometheus metrics. Define per-service dashboards with named owners. When SLOs are defined, attribute them to specific teams. |
| **Evidence** | `metrics/grafana/grafana.dashboard.app.json.txt`, `metrics/grafana/grafana.dashboard.server.json.txt`, No CODEOWNERS file found |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC exists, so no AWS resource tags are defined. No `default_tags` in Terraform provider, no `Tags` properties in CloudFormation, no tagging policy. Docker Compose labels exist for container naming (`container_name: flowise-main`, `flowise-worker`, `flowise-redis`) but these do not translate to AWS resource tags. |
| **Gap** | No resource tagging of any kind. Cost allocation, ownership attribution, and environment identification are impossible without tags. |
| **Recommendation** | When creating IaC (CDK/Terraform), define required tags: `Project=flowise`, `Environment={dev|staging|prod}`, `Owner={team}`, `CostCenter={id}`, `ManagedBy=cdk`. Enforce tags via AWS Config rules or Tag Policies in AWS Organizations. Enable cost allocation tags in AWS Billing. |
| **Evidence** | No IaC files found. `docker/docker-compose-queue-prebuilt.yml` (container_name labels only) |

## Learning Materials

The following learning resources are mapped to the 3 triggered pathways:

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Saga Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [EKS Workshop](https://www.eksworkshop.com/)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, SEC-Q6, SEC-Q7 | Root package.json with pnpm overrides for security patches; engine requirements |
| `pnpm-workspace.yaml` | APP-Q2 | Monorepo workspace configuration |
| `Dockerfile` | INF-Q1, SEC-Q6 | Root Dockerfile using node:20-alpine with non-root user |
| `docker/Dockerfile` | INF-Q1, SEC-Q6 | Production multi-stage Dockerfile |
| `docker/docker-compose.yml` | INF-Q1, INF-Q5, INF-Q6 | Single-service Docker Compose with healthcheck |
| `docker/docker-compose-queue-prebuilt.yml` | INF-Q1, INF-Q2, INF-Q4, INF-Q7, INF-Q9, APP-Q2, OPS-Q9 | Queue mode with Redis, worker, and main services |
| `docker/.env.example` | INF-Q2, SEC-Q2, SEC-Q5, DATA-Q3 | Docker environment configuration reference |
| `.github/workflows/main.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline: lint, build, test, Cypress e2e |
| `.github/workflows/docker-image-ecr.yml` | INF-Q1, INF-Q11, OPS-Q5 | Manual ECR image build workflow |
| `.github/workflows/docker-image-dockerhub.yml` | INF-Q11, OPS-Q5 | Manual DockerHub image build workflow |
| `.github/workflows/publish-agentflow.yml` | INF-Q11 | npm publish for agentflow package |
| `.github/workflows/test_docker_build.yml` | INF-Q11 | Docker build test workflow |
| `packages/server/package.json` | APP-Q1, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6, OPS-Q1, OPS-Q6 | Server dependencies: Express, TypeORM, BullMQ, Passport, OTEL, Prometheus |
| `packages/server/src/index.ts` | INF-Q5, INF-Q6, SEC-Q3, SEC-Q4, APP-Q2 | Main application entry: Express app, auth middleware, metrics, SSO |
| `packages/server/src/DataSource.ts` | INF-Q2, DATA-Q2, DATA-Q3, INF-Q8, APP-Q2 | Database configuration for SQLite/MySQL/MariaDB/PostgreSQL |
| `packages/server/src/routes/index.ts` | APP-Q2, APP-Q3, APP-Q5 | 50+ route registrations under /api/v1/ |
| `packages/server/src/queue/QueueManager.ts` | INF-Q3, INF-Q4, APP-Q3, APP-Q4, APP-Q6 | BullMQ queue configuration and Redis connection |
| `packages/server/src/queue/PredictionQueue.ts` | INF-Q3, APP-Q3, APP-Q4 | LLM prediction queue processing |
| `packages/server/src/queue/UpsertQueue.ts` | INF-Q3, APP-Q3, APP-Q4 | Vector store upsert queue processing |
| `packages/server/src/queue/RedisEventPublisher.ts` | INF-Q4, APP-Q3 | Redis pub/sub for SSE event streaming |
| `packages/server/src/queue/RedisEventSubscriber.ts` | INF-Q4, APP-Q3 | Redis subscriber for SSE event consumption |
| `packages/server/src/utils/logger.ts` | SEC-Q1 | Winston logging with sanitization |
| `packages/server/src/metrics/Prometheus.ts` | OPS-Q3 | Prometheus metric counters and HTTP histograms |
| `packages/server/src/metrics/OpenTelemetry.ts` | OPS-Q1, OPS-Q3 | OpenTelemetry metric and trace collection |
| `packages/server/src/Interface.Metrics.ts` | OPS-Q3 | Business metric counter enum definitions |
| `packages/server/.env.example` | INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, SEC-Q1, SEC-Q2, SEC-Q5, DATA-Q3, APP-Q4, APP-Q6 | Comprehensive environment variable reference |
| `packages/server/src/database/entities/` | APP-Q2, DATA-Q2 | 19 TypeORM entity definitions |
| `packages/server/src/database/migrations/` | DATA-Q3, DATA-Q4 | Schema migration scripts for 4 database engines |
| `packages/server/cypress/e2e/` | OPS-Q6 | Cypress e2e test directories (apikey, variables) |
| `packages/ui/package.json` | APP-Q1 | React UI with Vite build |
| `packages/components/package.json` | APP-Q1, OPS-Q1 | AI/LLM components: LangChain, Bedrock, OpenAI, vector stores, OTEL |
| `packages/components/nodes/vectorstores/` | DATA-Q2 | 25 vector store integrations |
| `packages/components/nodes/chatmodels/` | Move to AI evaluation | 29 LLM provider integrations including AWSBedrock |
| `packages/components/nodes/documentloaders/` | DATA-Q1 | Document loaders for PDF, EPUB, Office, web |
| `packages/agentflow/package.json` | APP-Q1 | Published npm library for agent workflows |
| `packages/api-documentation/src/yml/swagger.yml` | APP-Q5, Quick Agent Wins | OpenAPI 3.0.3 spec, 2,665 lines, 14 API groups |
| `metrics/prometheus/prometheus.config.yml` | OPS-Q2, OPS-Q4 | Prometheus scrape config (no alerting rules) |
| `metrics/grafana/` | OPS-Q2, OPS-Q3, OPS-Q8 | Grafana dashboards for app and server metrics |
| `metrics/otel/otel.config.yml` | OPS-Q1 | OpenTelemetry collector configuration |
| `artillery-load-test.yml` | OPS-Q6 | Load test configuration (not in CI) |
| `README.md` | Quick Agent Wins | Project documentation, 242 lines |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guide, 220 lines |
| `SECURITY.md` | OPS-Q7 | Vulnerability disclosure policy |
