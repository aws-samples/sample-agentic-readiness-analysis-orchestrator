# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | umami-software--umami |
| **Date** | 2026-05-08 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | typescript, analytics, web-app |
| **Context** | Self-hosted privacy-focused web analytics. |
| **Overall Score** | 1.79 / 4.0 |

**Archetype Justification**: The application owns persistent state in PostgreSQL (users, websites, sessions, events, revenue) and exposes CRUD operations across 75 API route handlers managing entity lifecycle (create/update/delete websites, users, teams, reports). Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.79 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+1+2+1+1+1+1+1+1+3) / 11 = 14/11 = 1.27
- APP: (4+2+2+2+1+2) / 6 = 13/6 = 2.17
- DATA: (1+3+3+4) / 4 = 11/4 = 2.75
- SEC: (Not Evaluated + 1+3+2+2+1+1) / 6 = 10/6 = 1.67 (SEC-Q1 excluded)
- OPS: (1+1+1+1+1+2+1+1+1) / 9 = 10/9 = 1.11
- Overall: (1.27+2.17+2.75+1.67+1.11) / 5 = 8.97/5 = 1.79

---

## Classification

**Tier: Remediation Required**

This repo has 8 High findings, 7 Medium findings, 3 Low findings. The matched rule is: "2-11 High → Remediation Required."

MOD classification treats "1 High" as Pilot-Ready (a single modernization gap), unlike ARA classification which treats "1 High" as a deployment-blocking agent safety concern. MOD measures modernization maturity where multiple High findings indicate systemic gaps requiring remediation before the system can be considered cloud-native ready.

**Classification Consistency Check**: consistent (V5 Needs Work [score 1.79, band 1.5–2.4] ≡ V6 Remediation Required)

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — all infrastructure manually created via Docker Compose | Cannot reproduce environments, no disaster recovery, no audit trail for infrastructure changes |
| 2 | INF-Q1: Managed Compute | 1 | Self-hosted Docker containers with no managed container orchestration | No elastic scaling, manual patching, no health-based replacement |
| 3 | INF-Q2: Managed Databases | 1 | PostgreSQL self-managed in Docker container | Manual backups, no automated failover, patching burden |
| 4 | OPS-Q1: Distributed Tracing | 1 | No tracing instrumentation — only debug logging | Cannot diagnose request flows or identify bottlenecks in production |
| 5 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency scanning in CI/CD | Vulnerabilities in dependencies and code reach production undetected |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions workflows for CI (build+test) and CD (Docker image publish) are operational.
- **What it enables:** An agent that triggers deployments, checks build status, manages Docker image releases, and automates version tagging.
- **Additional steps:** Add deployment stage to the pipeline (currently only publishes images, does not deploy). Add webhook or API trigger for agent invocation.
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. README.md with setup instructions, 52+ internationalization files, and extensive code comments exist.
- **What it enables:** A knowledge agent that indexes project documentation and code patterns to assist developers with setup, configuration, and API usage questions.
- **Additional steps:** Generate API documentation from route handlers and Zod schemas to enrich the knowledge base.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but Dockerfile and docker-compose exist; application is already containerized |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected (PostgreSQL is open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1, DATA-Q3=3 |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4=2 (self-managed Kafka); evidence of data processing workloads (ClickHouse analytics ingestion pipeline) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, OPS-Q5=1, OPS-Q6=2 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a monolithic Next.js full-stack application (APP-Q2=2) with frontend, backend API (75 routes), and data layer in a single deployable unit. Modules are identifiable (queries, lib, components, permissions) but share a single PostgreSQL database with no clear service boundaries.

**Compute Model Gaps:** All compute runs as self-hosted Docker containers (INF-Q1=1) with no managed orchestration (ECS, EKS, or Lambda).

**Communication Pattern Gaps:** Inter-component communication is primarily synchronous HTTP (APP-Q3=2). Kafka exists only for the ClickHouse event ingestion path. Long-running operations (analytics queries over large datasets) are handled synchronously (APP-Q4=2).

**Recommended Decomposition Approach:** Strangler Fig pattern — incrementally extract high-value services (event collection/ingestion, analytics query engine, user/team management) while keeping the monolith running. See Decomposition Strategy section below.

**Representative AWS Services:** ECS on Fargate (preferred per preferences for EKS), Aurora PostgreSQL, API Gateway, EventBridge, DynamoDB for session/event data, Lambda for event processing.

**Recommended Patterns:** Anti-corruption Layer, Event Sourcing (for analytics events), Hexagonal Architecture for extracted services.

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** PostgreSQL 15 running self-managed in a Docker container (INF-Q2=1). Optional ClickHouse also self-managed. No automated failover, no managed backups, no Multi-AZ.

**Engine Versions and EOL Status:** PostgreSQL 15 pinned in docker-compose (DATA-Q3=3). PostgreSQL 15 GA November 2022, EOL November 2027 — not at risk but approaching mid-lifecycle.

**Data Access Patterns:** Mostly centralized via Prisma ORM (DATA-Q2=3) with raw SQL for analytics queries. Read replica support already built into the Prisma client configuration.

**Recommended Managed Database Targets:** Aurora PostgreSQL (preferred per `preferences.prefer: ["aurora"]`) for the primary workload. The read replica pattern already implemented maps directly to Aurora read replicas. For high-volume analytics events, consider DynamoDB (preferred) or Amazon Timestream for time-series data.

**Representative AWS Services:** Aurora PostgreSQL, DynamoDB, ElastiCache (to replace self-hosted Redis)

**Migration Tools:** AWS DMS for live migration from self-hosted PostgreSQL to Aurora with minimal downtime. Connection string update via environment variables (`DATABASE_URL`) makes cutover straightforward.

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Streaming/Messaging Infrastructure:** Self-managed Kafka (kafkajs library) used as a producer for async event ingestion into ClickHouse (INF-Q4=2). The Kafka broker and ClickHouse are external dependencies not managed by IaC.

**Data Processing Workloads:** The application processes web analytics events at scale — page views, custom events, session data, and revenue tracking. Events flow through Kafka into ClickHouse for high-performance analytics queries.

**Recommended Managed Analytics Targets:** Replace self-managed Kafka with Amazon MSK Serverless or Amazon Kinesis Data Streams. Replace self-managed ClickHouse with Amazon Redshift Serverless or Amazon Timestream for time-series analytics. EventBridge (preferred) for event routing.

**Representative AWS Services:** MSK Serverless, Kinesis Data Streams, Redshift Serverless, Athena, EventBridge

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** No infrastructure as code exists (INF-Q10=1). All infrastructure is defined in docker-compose files for local/single-node deployment. No AWS resource definitions, no environment reproducibility.

**Current CI/CD State:** GitHub Actions provides build+test on push and Docker image publishing on tags (INF-Q11=3). However, there is no deployment stage — images are published but not deployed automatically.

**Deployment Strategy Gaps:** Direct-to-production by pulling latest Docker image (OPS-Q5=1). No blue/green, no canary, no traffic shifting.

**Testing Gaps:** Only 3 Jest unit tests and 6 Cypress E2E tests for 674 source files (OPS-Q6=2). E2E tests exist but are not run in CI (only available via separate docker-compose).

**Recommended DevOps Toolchain:** AWS CDK (TypeScript, matching the application language) for IaC. AWS CodePipeline or GitHub Actions with ECS deploy stage for CD. ECS blue/green deployment via CodeDeploy.

**Representative AWS Services:** CDK, CodePipeline, CodeDeploy, CodeBuild, ECR, CloudWatch

---

## Decomposition Strategy

### Recommended Approach: Strangler Fig (Parallel Track)

APP-Q2 = 2 indicates identifiable modules with shared database coupling. The monolith has recognizable boundaries (auth, event collection, analytics queries, user management, team management) that can be extracted incrementally.

**Why Strangler Fig:** The application has clear functional domains (event ingestion, analytics querying, user/team CRUD, reporting) that naturally map to service boundaries. The existing Kafka integration for event ingestion already demonstrates an async boundary. Incremental extraction delivers value without a risky big-bang cutover.

### Pattern Recommendations

| Pattern | Purpose | Application to Umami |
|---------|---------|---------------------|
| **Anti-corruption Layer** | Isolate new services from monolith data model | Place between extracted event-ingestion service and the monolith's database. Translate between Prisma models and the new service's domain model. |
| **Event Sourcing** | Capture analytics events as immutable stream | Natural fit — analytics events are already append-only (WebsiteEvent, EventData). Extract to EventBridge/Kinesis with event store. |
| **Saga Pattern** | Manage distributed transactions | Apply when extracting user/team management — team membership changes span User, Team, TeamUser, and Website entities. |
| **Hexagonal Architecture** | Structure extracted services | Each extracted service uses ports/adapters: API port (Next.js route → standalone API), DB adapter (Prisma → Aurora), messaging adapter (kafkajs → MSK/EventBridge). |

### Suggested Extraction Order

1. **Event Collection Service** (highest value, already partially decoupled via Kafka) — `/api/send` endpoint, session creation, event data storage
2. **Analytics Query Service** — Read-only analytics queries from `src/queries/sql/`, ClickHouse/PostgreSQL query routing
3. **User & Team Management Service** — Auth, user CRUD, team CRUD, permissions

### Effort Estimation

| Factor | Analysis | Signal |
|--------|-----------|--------|
| Module boundaries | Identifiable (queries/prisma, queries/sql, lib, permissions) | Medium effort |
| Data coupling | Single shared PostgreSQL database, cross-module joins | High effort for data separation |
| Stored procedures | None (DATA-Q4=4) | Low effort — no DB logic extraction needed |
| Communication patterns | Primarily sync, some Kafka for events | Medium effort to add async |
| CI/CD maturity | Build+test exists, no deploy automation | Medium effort to extend pipeline |
| Test coverage | Very minimal (3 unit, 6 E2E) | High risk — no regression safety net |

**Estimated Total Effort:** High — primarily driven by data coupling (shared PostgreSQL) and minimal test coverage (high regression risk during extraction).

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs as self-hosted Docker containers. The `docker-compose.yml` defines an `umami` service using `ghcr.io/umami-software/umami:latest` and a `db` service using `postgres:15-alpine`. No managed container orchestration (ECS, EKS, Fargate) or serverless (Lambda) is configured. No IaC defines any compute resources. |
| **Gap** | No managed compute — all workloads are self-managed Docker containers requiring manual scaling, patching, and capacity planning. |
| **Recommendation** | Migrate to ECS on Fargate or EKS (preferred per technology preferences) for managed container orchestration with elastic scaling and automated patching. The existing Dockerfile and health check endpoint (`/api/heartbeat`) provide a strong foundation for container orchestration adoption. |
| **Evidence** | `Dockerfile`, `docker-compose.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | PostgreSQL 15 runs self-managed in a Docker container (`postgres:15-alpine` in `docker-compose.yml`). Optional ClickHouse is also self-managed (connection via `CLICKHOUSE_URL` environment variable). Redis is self-managed (via `REDIS_URL`). No managed database services (RDS, Aurora, DynamoDB, ElastiCache) are configured. |
| **Gap** | All databases are self-managed with no automated failover, no managed backups, and manual patching requirements. |
| **Recommendation** | Migrate PostgreSQL to Aurora PostgreSQL (preferred). Migrate Redis to ElastiCache. The application already supports read replicas via `@prisma/extension-read-replicas` and uses `DATABASE_URL` / `DATABASE_REPLICA_URL` environment variables, making Aurora migration straightforward with connection string updates. |
| **Evidence** | `docker-compose.yml`, `src/lib/prisma.ts`, `prisma/schema.prisma` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service is in use. The application has multi-step operations (user registration → team creation → website setup, event ingestion → session resolution → data storage) that are handled as inline application logic in route handlers. The build process (`npm-run-all build-db build-tracker build-geo build-app`) is a multi-step workflow handled by npm scripts, not managed orchestration. |
| **Gap** | Multi-step business operations (event ingestion pipeline, report generation, data export) are implemented as hardcoded sequential logic with no dedicated orchestration, error handling, or retry mechanisms. |
| **Recommendation** | Adopt AWS Step Functions for multi-step workflows such as the event ingestion pipeline (session resolution → event storage → analytics aggregation) and report generation. The event collection flow (`/api/send` → session lookup → event creation → Kafka publish) is a natural candidate for managed orchestration. |
| **Evidence** | `src/app/api/send/route.ts`, `src/queries/sql/events/saveEvent.ts`, `package.json` (npm-run-all scripts) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Self-managed Kafka is used via the `kafkajs` library for async event ingestion when ClickHouse is the analytics backend. Kafka is configured via `KAFKA_URL` and `KAFKA_BROKER` environment variables with SASL authentication support. Redis is used for session/auth caching. However, both Kafka and Redis are self-managed — no managed messaging services (SQS, SNS, EventBridge, MSK) are in use. |
| **Gap** | Messaging infrastructure is self-managed. Kafka requires manual broker management, scaling, and patching. Cross-service state changes (e.g., website deletion cascading to events, team membership changes) are handled synchronously with no event-driven decoupling. |
| **Recommendation** | Replace self-managed Kafka with Amazon MSK Serverless or EventBridge (preferred per technology preferences). The existing Kafka producer pattern in `src/lib/kafka.ts` maps directly to MSK or Kinesis producers. For CRUD state change events, adopt EventBridge to decouple operations. |
| **Evidence** | `src/lib/kafka.ts`, `src/lib/redis.ts`, `package.json` (kafkajs, @umami/redis-client) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists. The docker-compose exposes port 3000 directly. No IaC defines network topology. The application has no network isolation between the web tier and database tier beyond Docker's default bridge network. |
| **Gap** | No network security — services are not deployed in a VPC with private subnets or security groups. The database is exposed on the same network as the application with no segmentation. |
| **Recommendation** | Deploy into a VPC with private subnets for the database tier and public subnets (behind ALB) for the application tier. Define least-privilege security groups. Use VPC endpoints for AWS service access. |
| **Evidence** | `docker-compose.yml` (port 3000 exposed, db on same network), absence of any IaC files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or load balancer is configured. The Next.js application serves directly on port 3000 with CORS headers configured in `next.config.ts`. The tracker script has `Access-Control-Allow-Origin: *` for cross-origin collection. No throttling, request validation at the gateway level, or centralized auth is present at the entry point. |
| **Gap** | Services are exposed directly with no gateway or load balancer providing throttling, authentication, or request validation at the network edge. |
| **Recommendation** | Deploy API Gateway (preferred per technology preferences) in front of the application for throttling, auth, and request validation. Alternatively, use an ALB with WAF for DDoS protection and rate limiting. CloudFront can serve the tracker script globally with edge caching. |
| **Evidence** | `next.config.ts` (CORS headers, direct port exposure), `docker-compose.yml` (port 3000:3000) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling mechanisms are configured. The docker-compose runs a single instance of each service with no scaling configuration. No ASG, ECS service scaling, or Lambda concurrency configuration exists. The application supports stateless horizontal scaling (sessions in Redis, no local file state) but no scaling infrastructure is defined. |
| **Gap** | No auto-scaling — all capacity is statically provisioned as a single container instance. Cannot respond to traffic spikes from analytics collection bursts. |
| **Recommendation** | Configure auto-scaling on ECS/EKS services based on CPU, memory, and request count metrics. The application's stateless design (sessions in Redis, no local state) makes horizontal scaling straightforward. Configure DynamoDB auto-scaling if adopted for event data. |
| **Evidence** | `docker-compose.yml` (single instance), absence of any scaling configuration |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated backup configuration exists. The PostgreSQL database uses a Docker named volume (`umami-db-data`) with no backup plan, no point-in-time recovery, and no snapshot lifecycle. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning for any data. |
| **Gap** | No backup configuration — a volume failure or corruption would result in complete data loss with no recovery path. |
| **Recommendation** | Migrating to Aurora PostgreSQL (recommended above) provides automated backups with 35-day retention and continuous PITR by default. If remaining on self-managed PostgreSQL, implement pg_dump scheduled backups to S3 with lifecycle policies. |
| **Evidence** | `docker-compose.yml` (named volume only, no backup), absence of any backup configuration |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All resources run as single instances in docker-compose with no multi-AZ deployment. The application and database are co-located on a single host. No load balancer, no replica configuration in the deployment model (code supports read replicas via `DATABASE_REPLICA_URL` but docker-compose does not configure one). |
| **Gap** | Single-instance deployment — any host failure takes down the entire application and database with no automatic recovery. |
| **Recommendation** | Deploy across 2+ Availability Zones using ECS/EKS with multi-AZ task placement. Use Aurora PostgreSQL with Multi-AZ automatic failover. Configure ALB with cross-zone load balancing. |
| **Evidence** | `docker-compose.yml` (single instance per service), `src/lib/prisma.ts` (replica support exists in code but not in deployment) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code exists. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files are present. The only infrastructure definition is `docker-compose.yml` for single-node deployment. Platform deployment files exist for Heroku (`app.json`) and Netlify (`netlify.toml`) but these are PaaS configs, not IaC. |
| **Gap** | 0% IaC coverage — all infrastructure is manually created. Cannot reproduce environments, no audit trail for infrastructure changes, no disaster recovery automation. |
| **Recommendation** | Adopt AWS CDK (TypeScript, matching the application language) to define all infrastructure: VPC, ECS/EKS cluster, Aurora PostgreSQL, ElastiCache, API Gateway, and supporting resources. Start with the compute and database layers as the highest-impact IaC targets. |
| **Evidence** | Absence of any `.tf`, `cdk.json`, `template.yaml`, `Chart.yaml`, or `kustomization.yaml` files. Only `docker-compose.yml`, `app.json`, `netlify.toml` exist. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides CI/CD automation with: (1) CI workflow running `pnpm test` and `pnpm build` on every push, (2) CD workflow building multi-architecture Docker images (linux/amd64, linux/arm64) and publishing to GHCR and Docker Hub on version tags with semantic versioning. However, there is no automated deployment stage — images are published but deployment to any environment requires manual action. No IaC deployment automation exists. |
| **Gap** | CI/CD covers application code (build + test + publish) but lacks an automated deployment stage. No IaC exists to automate infrastructure deployment alongside application code. |
| **Recommendation** | Add a deployment stage to the CD pipeline that deploys to ECS/EKS after image publication. Implement environment promotion (dev → staging → production). Add IaC deployment (CDK deploy) as part of the pipeline. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/cd-cloud.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript 5.9+ with Node.js 18.18, Next.js 15 (App Router), React 19 with React Compiler. Modern cloud-native language at current versions with matching modern frameworks. First-class AWS SDK coverage for TypeScript/Node.js ecosystem. Package manager: pnpm. ESM modules. |
| **Gap** | N/A — language and framework ecosystem is fully modern. |
| **Recommendation** | N/A — no language modernization needed. The TypeScript/Node.js ecosystem provides excellent AWS SDK support and cloud-native tooling. |
| **Evidence** | `package.json` (next ^15.5.9, react ^19.2.3, typescript ^5.9.3), `.github/workflows/ci.yml` (Node.js 18.18) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable monolith (Next.js full-stack) with identifiable modules: `src/queries/prisma/` (9 query modules), `src/queries/sql/` (raw analytics queries), `src/lib/` (33 utility modules), `src/permissions/` (RBAC), `src/components/` (UI). However, all modules share a single PostgreSQL database, direct cross-module data access exists (e.g., event queries join session tables), and the entire application is a single Docker image. |
| **Gap** | Monolith with identifiable modules but shared database schemas and tight coupling through direct table joins. No independent deployability — all 75 API routes deploy together. |
| **Recommendation** | Begin Strangler Fig decomposition starting with the event collection/ingestion service (already partially decoupled via Kafka) and the analytics query service (separate raw SQL modules). See Decomposition Strategy section. |
| **Evidence** | `Dockerfile` (single image), `docker-compose.yml` (single app service), `prisma/schema.prisma` (shared schema, 13 models), `src/queries/` directory structure |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Primarily synchronous HTTP for all API operations. Kafka exists for async event ingestion to ClickHouse (when `KAFKA_URL` is set), but this is optional and only applies to the analytics write path. The main application flow — authentication, CRUD operations, analytics queries — is entirely synchronous. Cross-domain operations (e.g., deleting a website cascading to events) are handled synchronously via Prisma transactions. |
| **Gap** | Primarily synchronous with some async for background event ingestion only. State changes that cross domain boundaries (user → team → website lifecycle) are tightly coupled via synchronous database transactions. |
| **Recommendation** | Introduce EventBridge for cross-domain state change events (website created/deleted, team membership changed). Convert the event ingestion path to always use managed async messaging (currently optional Kafka). Adopt async patterns for report generation and data export operations. |
| **Evidence** | `src/lib/kafka.ts` (optional Kafka producer), `src/lib/db.ts` (query routing showing sync-first design), `src/queries/prisma/` (synchronous Prisma calls) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some background processing exists via Kafka for event ingestion (async writes to ClickHouse). However, analytics queries over large datasets (sessions, events, metrics calculations) and report generation are handled synchronously in API route handlers. The `pagedRawQuery` function in `src/lib/prisma.ts` handles pagination but queries still execute synchronously within the request lifecycle. |
| **Gap** | Analytics queries over large datasets and report generation are synchronous operations that may exceed 30 seconds under load. No async job processing, no status polling, no background job framework for heavy operations. |
| **Recommendation** | Implement async job processing for report generation and bulk data export using Step Functions or SQS + Lambda workers. Add status polling endpoints for long-running analytics queries. The existing pagination helps but doesn't address aggregation queries over millions of events. |
| **Evidence** | `src/lib/prisma.ts` (pagedRawQuery, rawQuery — synchronous), `src/lib/kafka.ts` (async event writes only), absence of any job queue framework |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. All 75 API routes use unversioned paths (`/api/send`, `/api/auth/login`, `/api/websites/[websiteId]/metrics`). No `/v1/` prefixes, no version headers, no versioning annotations. Breaking changes would be deployed directly to all consumers. |
| **Gap** | No versioning — breaking changes to API contracts affect all consumers simultaneously. The tracker script (`script.js`) is served to third-party websites with no version control mechanism. |
| **Recommendation** | Implement URL-path versioning (`/api/v1/`) for the public API surface. This is especially critical for the tracker script and data collection endpoint (`/api/send`) which are embedded on third-party websites and cannot be updated atomically. |
| **Evidence** | `src/app/api/` directory structure (no version prefixes), `next.config.ts` (rewrites without version paths) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables (`DATABASE_URL`, `DATABASE_REPLICA_URL`, `CLICKHOUSE_URL`, `KAFKA_URL`, `KAFKA_BROKER`, `REDIS_URL`, `CLOUD_URL`). No dynamic service discovery, no service registry, no service mesh. The application itself is a monolith with no inter-service communication, but external dependencies are hard-configured. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. When decomposed into microservices, hard-coded endpoints will create deployment coupling. |
| **Recommendation** | When migrating to EKS (preferred), adopt Kubernetes service discovery or AWS Cloud Map for dynamic service resolution. For the monolith phase, environment variables are acceptable since there is only one deployable unit. Priority increases during decomposition. |
| **Evidence** | `src/lib/prisma.ts` (DATABASE_URL env var), `src/lib/kafka.ts` (KAFKA_URL, KAFKA_BROKER env vars), `src/lib/redis.ts` (REDIS_URL env var) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed object storage (S3) is configured. The application stores GeoIP data locally via the `maxmind` library (built during `build-geo` script). No document parsing, no unstructured data pipeline. All data is structured (PostgreSQL relational data, ClickHouse columnar data). |
| **Gap** | GeoIP database files are stored locally on the container filesystem. No S3 storage for data exports, report artifacts, or backup files. No parsing pipeline for any unstructured content. |
| **Recommendation** | Store GeoIP databases in S3 with lifecycle policies for updates. Use S3 for report exports (PDF/CSV generation). If data export features are added, store export artifacts in S3 with presigned URL access. |
| **Evidence** | `package.json` (maxmind dependency), `scripts/build-geo.js`, absence of any S3 configuration |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Mostly centralized data access through Prisma ORM (`src/queries/prisma/` with 9 query modules) and raw SQL analytics queries (`src/queries/sql/`). Query routing is centralized in `src/lib/db.ts` which directs queries to PostgreSQL, ClickHouse, or Kafka based on configuration. However, some direct database access exists in utility modules within `src/lib/prisma.ts` (raw queries bypassing the query module structure). |
| **Gap** | Mostly centralized but some raw SQL queries bypass the query module structure, and the dual-database routing adds complexity. The `rawQuery` function allows arbitrary SQL execution from any module. |
| **Recommendation** | Maintain the existing query module structure as services are extracted. Ensure all data access goes through the query layer rather than using `rawQuery` directly from route handlers. This pattern will serve as the foundation for data access microservices. |
| **Evidence** | `src/queries/prisma/` (9 modules), `src/queries/sql/` (analytics queries), `src/lib/db.ts` (centralized routing), `src/lib/prisma.ts` (rawQuery function) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | PostgreSQL 15 is explicitly pinned in `docker-compose.yml` (`postgres:15-alpine`). PostgreSQL 15 was released November 2022 with EOL projected November 2027 — not at risk but approaching mid-lifecycle. The Prisma schema specifies `provider = "postgresql"` without a version constraint. No documented version-update procedure exists. |
| **Gap** | Version is pinned but no documented version-update procedure covering downtime windows, rollback plans, or risk acknowledgment. PostgreSQL 15 is stable but will approach EOL within 2 years. |
| **Recommendation** | Document a database version upgrade procedure. Plan migration to PostgreSQL 16 or 17 (or Aurora PostgreSQL which handles version upgrades with managed blue/green deployments). When migrating to Aurora, leverage managed major version upgrades. |
| **Evidence** | `docker-compose.yml` (`postgres:15-alpine`), `prisma/schema.prisma` (provider = postgresql) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the application layer via Prisma ORM and raw SQL queries. The 14 Prisma migrations contain only DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX) — no procedural SQL. Raw SQL queries in `src/queries/sql/` use standard PostgreSQL syntax (date functions, window functions, CTEs) without proprietary extensions. |
| **Gap** | N/A — no stored procedures or proprietary SQL. |
| **Recommendation** | N/A — the application layer correctly owns all business logic. This is ideal for database engine migration. |
| **Evidence** | `prisma/migrations/` (14 DDL-only migrations), `src/queries/sql/` (standard SQL), absence of any CREATE PROCEDURE/FUNCTION/TRIGGER |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains no IaC provisioning AWS resources (`has_iac_provisioning_aws_resources=false`). It is a self-hosted application without AWS infrastructure definitions. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of any Terraform, CDK, or CloudFormation files provisioning AWS resources |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured. PostgreSQL data is stored in a Docker named volume (`umami-db-data`) with no disk encryption. No KMS keys, no encrypted EBS volumes, no S3 server-side encryption. The application encrypts JWT tokens (AES-256-GCM in `src/lib/crypto.ts`) but the underlying data store has no at-rest encryption. |
| **Gap** | Database volume has no encryption at rest. User data (passwords are bcrypt-hashed but other PII — usernames, session data, website domains — is stored in plaintext on disk). |
| **Recommendation** | Migrating to Aurora PostgreSQL (recommended above) provides encryption at rest by default using AWS KMS. If remaining on self-managed PostgreSQL, enable disk-level encryption on the host volume. Use customer-managed KMS keys for encryption key rotation and audit. |
| **Evidence** | `docker-compose.yml` (named volume, no encryption), `src/lib/crypto.ts` (application-level encryption for tokens only) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JWT Bearer token authentication is implemented for all API endpoints via `src/lib/auth.ts`. Tokens are encrypted using AES-256-GCM (`src/lib/crypto.ts`) before signing. Redis-backed session storage with configurable expiration. Share tokens allow read-only public access to specific website dashboards. The `/api/send` data collection endpoint is intentionally unauthenticated (by design — receives events from third-party websites). |
| **Gap** | Token-based auth on all management endpoints. The collection endpoint (`/api/send`) is intentionally open but has no API Gateway throttling or validation beyond application-level bot detection. Internal endpoints do not have additional network-level isolation. |
| **Recommendation** | Add API Gateway with throttling and request validation in front of the collection endpoint. The existing JWT auth is solid for management APIs. Consider adding rate limiting at the network level for the open collection endpoint to prevent abuse. |
| **Evidence** | `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/lib/crypto.ts`, `src/lib/password.ts` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application manages its own authentication with username/password stored in PostgreSQL (bcrypt-hashed). SSO support exists (`src/app/api/auth/sso/route.ts`) enabling federation with external identity providers. However, the primary auth mechanism is self-managed — no Cognito, Okta, or external IdP integration by default. |
| **Gap** | Application has its own auth system with SSO capability but does not integrate with a centralized IdP by default. Users must configure SSO separately. |
| **Recommendation** | When deploying on AWS, integrate with Amazon Cognito as the centralized identity provider. The existing SSO endpoint provides the foundation — configure Cognito User Pool as the OIDC provider with the application as a relying party. |
| **Evidence** | `src/app/api/auth/sso/route.ts`, `src/lib/auth.ts`, `src/lib/password.ts`, `prisma/schema.prisma` (User model with password field) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials in source code. All secrets (`DATABASE_URL`, `APP_SECRET`, `KAFKA_URL`, `REDIS_URL`) are configured via environment variables. The docker-compose.yml contains example credentials (`APP_SECRET: replace-me-with-a-random-string`, `POSTGRES_PASSWORD: umami`) but these are documented as examples. No Secrets Manager, Vault, or rotation mechanism is configured. `.env` files are in `.gitignore`. |
| **Gap** | Production credentials are in environment variables with no rotation, no encryption-at-rest for the env vars themselves, and no centralized secrets management. The docker-compose example values could be mistakenly used in production. |
| **Recommendation** | Adopt AWS Secrets Manager for all production credentials (DATABASE_URL, APP_SECRET, KAFKA credentials). Configure automatic rotation for database credentials. Reference secrets from ECS task definitions via Secrets Manager ARNs rather than plaintext environment variables. |
| **Evidence** | `docker-compose.yml` (example credentials), `.gitignore` (.env files excluded), `src/lib/prisma.ts` (DATABASE_URL from process.env), `src/lib/kafka.ts` (KAFKA_URL from process.env) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Dockerfile uses `node:22-alpine` as base image and runs as non-root user (uid 1001) — a good security practice. However, there is no vulnerability scanning, no hardened base image (no CIS benchmark), no SSM Patch Manager, and no automated patching strategy. The alpine base provides a smaller attack surface but is not a security-hardened image. |
| **Gap** | No patching strategy, no vulnerability scanning (Inspector, Snyk, Trivy), no hardened AMI or image. Relies solely on rebuilding with newer base images. |
| **Recommendation** | Add container image scanning (ECR image scanning or Trivy) to the CI/CD pipeline. Consider using AWS-maintained base images or Bottlerocket for container hosts. Implement automated rebuilds when base image CVEs are published. |
| **Evidence** | `Dockerfile` (node:22-alpine, non-root user), absence of any scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are configured in the CI/CD pipeline. No Dependabot, no Snyk, no CodeQL, no SonarQube, no npm audit step. The CI workflow (`.github/workflows/ci.yml`) only runs `pnpm test` and `pnpm build`. No container scanning in the CD workflow. Biome is configured for linting/formatting but does not perform security analysis. |
| **Gap** | No security scanning — vulnerabilities in 72+ production dependencies and application code reach production undetected. No dependency vulnerability alerts, no SAST, no container scanning. |
| **Recommendation** | Add Dependabot or Snyk for dependency vulnerability scanning. Add CodeQL or Semgrep for SAST in the CI pipeline. Add ECR image scanning for container vulnerabilities. Configure security gates that block merges on critical findings. |
| **Evidence** | `.github/workflows/ci.yml` (no security steps), `.github/workflows/cd.yml` (no image scanning), absence of `.github/dependabot.yml`, `.snyk`, or `codeql-analysis.yml` |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. The application uses the `debug` library for debug-level logging (`debug('umami:auth')`, `debug('umami:prisma')`, `debug('umami:kafka')`) but this is not structured tracing. No OpenTelemetry SDK, no X-Ray instrumentation, no trace ID propagation across the Kafka producer or HTTP calls. |
| **Gap** | No tracing — cannot diagnose request flows, identify bottlenecks, or correlate events across the application's components (HTTP → DB → Kafka → ClickHouse). |
| **Recommendation** | Instrument with OpenTelemetry SDK for Node.js. Add X-Ray or ADOT (AWS Distro for OpenTelemetry) for end-to-end tracing. Propagate trace IDs through Kafka messages and database queries. The `debug` library calls can be augmented with trace context. |
| **Evidence** | `package.json` (no OpenTelemetry or X-Ray dependencies), `src/lib/auth.ts` (debug library only), `src/lib/kafka.ts` (no trace propagation) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No CloudWatch alarms on latency or error rates. No error budget tracking. The only health check is the `/api/heartbeat` endpoint used by Docker health checks — it verifies the application is responsive but does not measure service levels. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for the analytics collection endpoint (availability, latency) or the dashboard API (response time, error rate). |
| **Recommendation** | Define SLOs for critical user journeys: (1) Event collection endpoint availability ≥ 99.9%, p99 latency < 200ms; (2) Dashboard API p95 latency < 2s; (3) Real-time data freshness < 30s. Implement CloudWatch metrics and alarms to track these SLOs. |
| **Evidence** | `src/app/api/heartbeat/` (basic health check only), absence of any SLO, alarm, or metric configuration |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The application tracks website analytics for its users but does not instrument its own operational metrics. No CloudWatch `put_metric_data` calls, no custom dashboards for the application's own health (events processed/second, active sessions, query latency by type). |
| **Gap** | No business metrics — cannot measure events ingested per second, active websites, query performance, or user engagement with the analytics platform itself. Only default infrastructure metrics would be available if deployed on AWS. |
| **Recommendation** | Publish custom CloudWatch metrics for: events collected/sec, unique sessions/min, API error rates by endpoint, database query duration by type, Kafka producer latency. These metrics inform capacity planning and SLO tracking. |
| **Evidence** | Absence of any metrics library or CloudWatch SDK usage in source code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection is configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no threshold-based alerts. The application has no mechanism to detect or notify on degraded performance, elevated error rates, or unusual traffic patterns. |
| **Gap** | No alerting — failures and degradations go undetected until users report issues. No anomaly detection for sudden traffic spikes (bot attacks on collection endpoint) or query performance degradation. |
| **Recommendation** | Configure CloudWatch alarms for error rates, latency percentiles, and resource utilization. Enable CloudWatch anomaly detection on the event collection endpoint to catch unusual traffic patterns. Integrate with SNS/PagerDuty for on-call notification. |
| **Evidence** | Absence of any alerting configuration, alarm definitions, or notification integrations |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment by pulling the latest Docker image. The CD workflow publishes images to GHCR/Docker Hub with `:latest` tag. Deployment requires manually pulling the new image and restarting containers. No canary, no blue/green, no rolling deployment, no traffic shifting. No CodeDeploy, no Argo Rollouts. |
| **Gap** | Direct-to-production with no staged rollout. A bad release affects all users immediately with no automatic rollback capability. |
| **Recommendation** | Adopt ECS blue/green deployment via CodeDeploy, or Kubernetes rolling updates with readiness probes on EKS. Implement canary deployments for the event collection endpoint (most critical path). The existing health check endpoint (`/api/heartbeat`) supports readiness probing. |
| **Evidence** | `.github/workflows/cd.yml` (publishes images only, no deploy), `docker-compose.yml` (`:latest` tag) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Integration tests exist but have minimal coverage and are not consistently run in CI. Cypress E2E tests (6 test files) cover login, website CRUD, user CRUD, and team CRUD workflows. A dedicated `cypress/docker-compose.yml` enables containerized E2E testing. However, CI only runs Jest unit tests (3 files) — Cypress tests are not part of the CI pipeline. |
| **Gap** | Integration tests exist but are not run in CI. Only 6 E2E test files for 75 API routes and 674 source files. Critical workflows (event collection, analytics queries, Kafka integration) have no integration test coverage. |
| **Recommendation** | Add Cypress E2E tests to the CI pipeline (the Docker Compose infrastructure already exists). Expand integration test coverage to include: event collection end-to-end, analytics query accuracy, Kafka event ingestion, and authentication flows. Target critical paths first. |
| **Evidence** | `cypress/e2e/` (6 test files), `cypress/docker-compose.yml`, `.github/workflows/ci.yml` (runs Jest only), `src/lib/__tests__/` (3 unit tests) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. No Systems Manager Automation documents, no Lambda-based remediation, no documented incident procedures. The Docker health check restarts the container on failure (basic self-healing) but no structured incident response exists. |
| **Gap** | No incident response — entirely ad hoc. The Docker restart policy provides basic container-level recovery but no application-level incident handling (e.g., circuit breakers, database failover procedures, Kafka producer retry strategies). |
| **Recommendation** | Create runbooks for common failure scenarios: database connection failures, Kafka producer failures, high memory usage, elevated error rates. Implement Systems Manager Automation for self-healing (auto-restart, connection pool reset). Document escalation procedures. |
| **Evidence** | `docker-compose.yml` (`restart: always` — basic only), absence of any runbook or automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for monitoring configuration, no service-level dashboards, no alarms with named owners, no SLO definitions with team attribution. The application has no observability infrastructure to own. |
| **Gap** | No observability ownership — monitoring is nonexistent, not just unowned. No dashboards, no alarms, no team attribution. |
| **Recommendation** | Establish observability ownership as part of the cloud migration. Define CODEOWNERS for monitoring configuration. Create per-service dashboards in CloudWatch with named team owners. Tie SLOs to specific team responsibilities. |
| **Evidence** | Absence of any CODEOWNERS file referencing observability, absence of dashboard or alarm definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists — there are no IaC-defined AWS resources to tag. No `default_tags` in any Terraform provider, no `tags` on any resources, no tagging standard documented. |
| **Gap** | No tagging governance — when AWS resources are created for this workload, there is no tagging standard to follow for cost allocation, ownership tracking, or environment identification. |
| **Recommendation** | Define a tagging standard before creating AWS infrastructure. Required tags should include: `Service=umami`, `Environment={dev,staging,prod}`, `Team={owner}`, `CostCenter={value}`. Implement via CDK `default_tags` or AWS Organizations Tag Policies. |
| **Evidence** | Absence of any IaC files or tagging configuration |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Managed Analytics
- [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `Dockerfile` | INF-Q1, APP-Q2, SEC-Q6 | Multi-stage Docker build, node:22-alpine, non-root user |
| `docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2, SEC-Q5, OPS-Q5, OPS-Q7 | Production deployment config, PostgreSQL 15, port exposure, named volumes |
| `package.json` | APP-Q1, INF-Q4, DATA-Q1, OPS-Q1 | Dependencies, scripts, language/framework versions |
| `prisma/schema.prisma` | INF-Q2, APP-Q2, DATA-Q3, DATA-Q4, SEC-Q4 | PostgreSQL provider, 13 models, no stored procedures |
| `prisma/migrations/` | DATA-Q4 | 14 DDL-only migrations |
| `src/lib/prisma.ts` | INF-Q2, APP-Q3, APP-Q4, DATA-Q2, SEC-Q5 | Prisma client with read replica support, raw queries |
| `src/lib/kafka.ts` | INF-Q4, APP-Q3, APP-Q4, OPS-Q1 | Self-managed Kafka producer, SASL auth |
| `src/lib/redis.ts` | INF-Q2, APP-Q6 | Redis client for session/auth caching |
| `src/lib/auth.ts` | SEC-Q3, OPS-Q1 | JWT Bearer token auth, Redis session storage |
| `src/lib/jwt.ts` | SEC-Q3 | JWT creation/verification with encryption |
| `src/lib/crypto.ts` | SEC-Q2, SEC-Q3 | AES-256-GCM encryption, PBKDF2 key derivation |
| `src/lib/password.ts` | SEC-Q3, SEC-Q4 | bcrypt password hashing |
| `src/lib/db.ts` | INF-Q4, APP-Q3, DATA-Q2 | Database type detection and query routing |
| `src/app/api/auth/sso/route.ts` | SEC-Q4 | SSO support endpoint |
| `src/queries/prisma/` | DATA-Q2, APP-Q2 | 9 centralized Prisma query modules |
| `src/queries/sql/` | DATA-Q2, DATA-Q4, APP-Q4 | Raw SQL analytics queries |
| `next.config.ts` | INF-Q6, APP-Q5 | CSP headers, CORS config, rewrites |
| `.github/workflows/ci.yml` | INF-Q11, SEC-Q7, OPS-Q6, APP-Q1 | CI pipeline — test and build |
| `.github/workflows/cd.yml` | INF-Q11, OPS-Q5, SEC-Q7 | CD pipeline — Docker image publish |
| `cypress/e2e/` | OPS-Q6 | 6 E2E test files |
| `cypress/docker-compose.yml` | OPS-Q6 | Containerized E2E testing infrastructure |
| `app.json` | INF-Q10 | Heroku PaaS config (not IaC) |
| `netlify.toml` | INF-Q10 | Netlify PaaS config (not IaC) |
| `scripts/build-geo.js` | DATA-Q1 | GeoIP database build script |
