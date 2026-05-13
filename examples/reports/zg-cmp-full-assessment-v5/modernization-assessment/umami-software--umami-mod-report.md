# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | umami-software/umami |
| **Date** | 2026-04-30 |
| **TD Version** | Modernization Assessment v1.0 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, analytics, web-app |
| **Context** | Self-hosted privacy-focused web analytics. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **1.7 / 4.0** |

**Archetype Justification**: The application owns persistent state (PostgreSQL via Prisma ORM with 14 migration files and 13 models), exposes CRUD endpoints for users, websites, teams, reports, sessions, links, and pixels (75 API route files). It has write endpoints (POST for creating websites, users, events). Kafka is an optional event producer, not a consumer. The application does not fan-out to 3+ downstream services. Classified as `stateful-crud`.

> **Note:** Although classified as `monorepo` (pnpm-workspace.yaml present), the repository contains a single Next.js application — not multiple independent services. The assessment treats this as a single application unit within the monorepo classification.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.2 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.2 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.8 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.1 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.1 / 4.0 | ❌ Not Present |
| **Overall** | **1.7 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC files found — all infrastructure is manually provisioned via docker-compose or ClickOps | Blocks reproducible deployments, disaster recovery, and environment consistency. Foundation for all other modernization. |
| 2 | SEC-Q5: Secrets Management | 1 | Plaintext credentials in docker-compose.yml (POSTGRES_USER/PASSWORD: umami); APP_SECRET placeholder committed to repo | Critical security vulnerability — credentials exposed in version control. Deployment-blocking for any production AWS workload. |
| 3 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Lambda/Fargate) — application runs via docker-compose with no orchestration | No auto-scaling, no health-based recovery, no rolling deployments. Single point of failure. |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, dependency scanning, or container scanning in CI/CD pipeline | Vulnerabilities in dependencies or source code reach production undetected. |
| 5 | INF-Q9: High Availability | 1 | Single-instance deployment with no multi-AZ configuration; docker-compose runs one container per service | Any host or AZ failure takes down the entire analytics platform with no automatic recovery. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (unified data access layer exists). Umami has a well-structured data access layer with `src/queries/prisma/` for ORM queries, `src/queries/sql/` for raw SQL analytics queries, and `src/lib/db.ts` providing a unified `runQuery` dispatcher across PostgreSQL/ClickHouse/Kafka backends.
- **What it enables:** A natural-language-to-SQL agent that can query analytics data (page views, sessions, events, revenue) using the existing centralized query layer. Users could ask "Show me top 10 referrers for website X last month" and get structured results.
- **Additional steps:** Generate an OpenAPI specification from the existing 75 API routes to provide the agent with a discoverable tool interface. The Prisma schema provides a clean data model for query generation.
- **Effort:** Medium — query layer exists but needs OpenAPI spec generation and agent integration.

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (CI/CD pipeline exists). GitHub Actions workflows exist for CI (`ci.yml` with build+test) and CD (`cd.yml` with Docker image build on tag push).
- **What it enables:** An agent that can trigger builds, check CI status, manage Docker image releases, and monitor pipeline health. Could automate release tagging and image promotion workflows.
- **Additional steps:** Add GitHub Actions API tokens and configure agent access to the repository's workflow dispatch endpoints.
- **Effort:** Low — existing GitHub Actions provide the automation surface; agent orchestrates via GitHub API.

### RAG-Based Knowledge Agent

- **Prerequisite:** README.md and documentation content exist in the repository. The README provides installation instructions, Docker setup, and links to comprehensive docs at umami.is/docs.
- **What it enables:** A knowledge agent that indexes the README, code comments, and external documentation to answer developer questions about Umami configuration, deployment, and customization.
- **Additional steps:** Index the README.md, inline code documentation, and Prisma schema as the initial knowledge corpus. Consider including the external umami.is/docs content for comprehensive coverage.
- **Effort:** Medium — documentation exists but needs indexing and a retrieval pipeline (e.g., Amazon Bedrock with knowledge bases).

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute), APP-Q3=2 (sync-only), APP-Q4=2 (no async jobs) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but Dockerfile and docker-compose.yml exist — container definitions found. Contextual guard prevents trigger. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures). PostgreSQL and ClickHouse are already open-source engines. No commercial DB detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed PostgreSQL in Docker, self-managed ClickHouse), DATA-Q3=3 (versions pinned but lifecycle management limited) |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4=2 (self-managed Kafka), data processing workloads exist (ClickHouse materialized views, analytics aggregation pipeline) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (zero IaC), INF-Q11=2 (partial CI/CD), OPS-Q5=1 (no deployment strategy), OPS-Q6=2 (tests not in CI) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Self-hosted privacy-focused web analytics." contains no AI-related signal terms). |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Umami is a single Next.js 15 monolith (APP-Q2=2) bundling frontend (React 19), backend (75 API routes), and data access (Prisma ORM + ClickHouse client) in one deployable unit. All functionality—analytics collection, dashboard rendering, user management, report generation—ships as a single Docker container.

**Compute Model Gaps:** INF-Q1=1. No managed compute. The application runs via `docker-compose` with a single `umami` container and a `postgres:15-alpine` container. No ECS, EKS, Lambda, or Fargate definitions exist.

**Communication Pattern Gaps:** APP-Q3=2. All API endpoints are synchronous HTTP request/response. Kafka is an optional event producer for ClickHouse ingestion but is self-managed and not used for inter-service communication. APP-Q4=2. Report generation and analytics queries (funnel, journey, retention reports via `src/queries/sql/reports/`) may exceed 30 seconds for large datasets but are handled synchronously with no background job framework.

**Recommended Decomposition Approach:** Strangler Fig pattern — see Decomposition Strategy section below. Priority extraction candidates:
1. **Analytics Collection Service** (`/api/send`) — highest throughput endpoint, stateless event ingestion, natural bounded context
2. **Reporting Service** (`/api/reports/*`, `src/queries/sql/reports/`) — CPU-intensive queries, benefits from independent scaling
3. **Dashboard/Frontend** — static rendering, cacheable, can be served via CloudFront

**Representative AWS Services:** EKS (preferred per preferences), API Gateway (preferred), EventBridge (preferred) for event routing, Lambda for lightweight functions, Step Functions for report generation workflows.

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing (for analytics events), Hexagonal Architecture for extracted services.

**References:** [AWS Prescriptive Guidance — Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** INF-Q2=1. PostgreSQL 15 runs as a self-managed container (`postgres:15-alpine`) via docker-compose. ClickHouse is an optional analytics backend accessed via `CLICKHOUSE_URL` environment variable — also self-managed. Redis (`@umami/redis-client`) is used for caching and session storage, also self-managed via `REDIS_URL`.

**Engine Versions and EOL Status:** DATA-Q3=3. PostgreSQL 15 is pinned in docker-compose and is currently supported (EOL November 2027). ClickHouse version is not explicitly pinned.

**Data Access Patterns:** DATA-Q2=3. Well-organized centralized data access via `src/lib/db.ts` (unified `runQuery` dispatcher), `src/lib/prisma.ts` (Prisma ORM), and `src/lib/clickhouse.ts` (ClickHouse client). This clean separation simplifies database migration — connection strings and adapters can be swapped without refactoring business logic.

**Recommended Managed Database Targets:**
- **PostgreSQL → Amazon Aurora PostgreSQL** (preferred per preferences): Compatible engine, supports Prisma adapter, Multi-AZ by default, automated backups, auto-scaling replicas. The existing `@prisma/adapter-pg` and read replica support in `src/lib/prisma.ts` indicate readiness for Aurora's reader endpoints.
- **ClickHouse → Amazon Timestream or Amazon Redshift Serverless**: For analytics workloads. Alternatively, ClickHouse Cloud (managed) if ClickHouse-specific features (materialized views, MergeTree engines) are critical.
- **Redis → Amazon ElastiCache for Redis or Amazon MemoryDB**: Managed caching with Multi-AZ failover.

**Migration Tools:** AWS Database Migration Service (DMS) for PostgreSQL-to-Aurora migration. Minimal schema changes expected — Prisma ORM abstracts the PostgreSQL dialect.

**References:** [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Streaming/Messaging Infrastructure:** INF-Q4=2. KafkaJS (`kafkajs@^2.1.0`) provides optional self-managed Kafka integration for event streaming from the analytics collection endpoint to ClickHouse. The Kafka client is configured via `KAFKA_URL` and `KAFKA_BROKER` environment variables (`src/lib/kafka.ts`). This is a self-managed broker that requires patching, scaling, and monitoring.

**Data Processing Workloads:** The repository is fundamentally an analytics platform. ClickHouse materialized views in `db/clickhouse/schema.sql` perform real-time aggregation of website events into hourly statistics (`website_event_stats_hourly_mv`), revenue tracking (`website_revenue_mv`), and projection-based query optimization. The `src/queries/sql/` layer contains 40+ analytics query functions for events, pageviews, sessions, reports (funnel, journey, retention, UTM, breakdown).

**Data Access Patterns:** DATA-Q2=3. The `src/lib/db.ts` `runQuery` function dispatches to ClickHouse, Kafka, or Prisma based on configuration — providing a clean abstraction for migrating the streaming layer.

**Recommended Managed Analytics Targets:**
- **Self-managed Kafka → Amazon EventBridge** (preferred per preferences): For event routing between the collection service and analytics backend. EventBridge provides serverless event bus with schema registry, filtering, and fan-out — replacing self-managed Kafka (which should be avoided per preferences).
- **Self-managed Kafka → Amazon Kinesis Data Streams**: Alternative for high-throughput analytics event ingestion if EventBridge throughput limits are a concern.
- **ClickHouse materialized views → Amazon Kinesis Data Analytics or AWS Glue**: For real-time analytics aggregation currently handled by ClickHouse materialized views.
- **Analytics queries → Amazon Athena + S3 data lake**: For cost-optimized historical analytics queries using the existing query patterns.

**References:** [Move to Managed Analytics Learning Plan](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** INF-Q10=1. Zero infrastructure-as-code files exist in the repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize. All infrastructure is provisioned via docker-compose (development/simple deployments) or manually.

**Current CI/CD State:** INF-Q11=2. GitHub Actions provides:
- `ci.yml`: Build + test (jest) on push — runs `pnpm test` and `pnpm build` using Node.js 18.18
- `cd.yml`: Docker image build on tag push — builds multi-platform images (linux/amd64, linux/arm64) and pushes to GHCR and Docker Hub
- `cd-cloud.yml`: Cloud-specific Docker build for the hosted version

Missing: No deployment automation to production infrastructure (only image push). No IaC pipeline. No automated rollback.

**Deployment Strategy Gaps:** OPS-Q5=1. No blue/green, canary, or rolling deployment strategy. Docker images are pushed to registries; actual deployment to running infrastructure is manual.

**Testing Gaps:** OPS-Q6=2. Jest unit tests exist (3 test files in `src/lib/__tests__/`) and Cypress E2E tests exist (6 tests in `cypress/e2e/`) but Cypress tests are NOT run in the CI pipeline — only `pnpm test` (jest) is executed.

**Recommended DevOps Toolchain:**
1. **IaC Adoption:** AWS CDK (TypeScript — matches the existing codebase language) or Terraform for infrastructure provisioning. Define EKS cluster, Aurora PostgreSQL, ElastiCache, API Gateway, EventBridge, and networking in code.
2. **CI/CD Enhancement:** Extend GitHub Actions with:
   - Cypress E2E tests in CI pipeline
   - Security scanning (Dependabot, Snyk, or Amazon CodeGuru)
   - Infrastructure deployment via CDK/Terraform in CD pipeline
   - Automated rollback on deployment failure
3. **Deployment Strategy:** Implement blue/green or canary deployments via EKS (preferred) with ArgoCD or AWS CodeDeploy.

**Representative AWS Services:** CDK, CodeBuild, CodePipeline, CodeDeploy, CloudWatch, X-Ray.

**References:** [Move to Modern DevOps Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

## Decomposition Strategy

APP-Q2 = 2 — Umami is a monolith with identifiable modules but shared database schemas and tight coupling between frontend, backend, and data access layers. Decomposition is warranted.

### Recommended Approach: Strangler Fig (Parallel Track)

**Why:** Umami has clearly identifiable bounded contexts (analytics collection, reporting, user/team management, dashboard rendering) with a centralized data access layer (`src/lib/db.ts`, `src/queries/`) that provides natural extraction seams. The Strangler Fig approach allows incremental extraction while keeping the existing application running.

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services while keeping the monolith running. New features as services; existing features migrated over time. | ✅ Umami: APP-Q2=2, identifiable modules, clear bounded contexts | **Medium to High** — 6-18 months | ✅ **Recommended.** Lowest risk, incremental value delivery. |
| **Conditional / Adaptive** | Containerize as-is on EKS, then selectively extract high-value services based on business priority. | When capacity is limited or only specific modules need independent scaling. | **Low to Medium** — 2-4 weeks for containerization, 3-12 months for extraction | ✅ **Viable alternative** if team capacity is constrained. |
| **Big-Bang Rewrite** | Rewrite as microservices from scratch. | Almost never. | **Very High** — 12-24+ months | ⚠️ **Not recommended.** Umami is functional and actively maintained. Strangler Fig is safer. |

### Priority Extraction Candidates

1. **Analytics Collection Service** (`src/app/api/send/route.ts`)
   - **Why first:** Highest throughput endpoint. Stateless event ingestion. Natural bounded context — receives events from client-side tracker, validates, enriches with geo/device data, and persists.
   - **Extraction complexity:** Low — minimal dependencies (crypto, detect, schema validation). Database writes are isolated in `src/queries/sql/events/saveEvent.ts`.
   - **Target:** AWS Lambda behind API Gateway (preferred), or EKS service. EventBridge (preferred) for event routing to analytics backend.

2. **Reporting Service** (`src/app/api/reports/*`, `src/queries/sql/reports/`)
   - **Why second:** CPU-intensive analytics queries (funnel, journey, retention, UTM breakdown). Benefits from independent scaling and potentially async processing for large datasets.
   - **Extraction complexity:** Medium — depends on query layer (`src/queries/sql/`) and both PostgreSQL and ClickHouse backends.
   - **Target:** EKS service with DynamoDB (preferred) for report metadata, Step Functions for long-running report generation.

3. **User/Team Management** (`src/app/api/users/*`, `src/app/api/teams/*`, `src/queries/prisma/`)
   - **Why third:** CRUD operations on user, team, website entities. Lower throughput than collection or reporting. Clear Prisma-based data model.
   - **Extraction complexity:** Medium — Prisma models are well-defined but shared across the application.

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate new services from the monolith's data model | Every extraction — translate between monolith and service models |
| **Saga Pattern** | Manage distributed transactions (e.g., website creation → team assignment → permissions) | When extracting user/team management service |
| **Event Sourcing** | Capture analytics events as immutable event stream | Analytics collection service — events are naturally immutable |
| **Hexagonal Architecture** | Structure each service with clear ports and adapters | Every new service — ensures testability and infrastructure portability |

### Effort Estimation

| Factor | Current State | Effort Signal |
|--------|---------------|---------------|
| Module boundaries | Identifiable: `src/queries/prisma/`, `src/queries/sql/`, `src/lib/`, `src/components/` | **Medium** — modules exist but are not independently deployable |
| Data coupling | Single shared PostgreSQL database via Prisma; ClickHouse for analytics | **High** — shared Prisma schema requires per-service database separation |
| Stored procedures | None (DATA-Q4=4) | **Low** — no database-embedded logic to extract |
| Communication patterns | All synchronous HTTP (APP-Q3=2) | **Medium** — need to introduce async for event routing |
| CI/CD maturity | Basic (INF-Q11=2) — build+test only | **High** — need to build multi-service deployment pipeline before extraction |
| Test coverage | Limited (OPS-Q6=2) — 3 unit tests, 6 E2E tests not in CI | **High** — regression risk during extraction; need test coverage investment first |

**Calibrated Effort Estimate:** 9-15 months for Strangler Fig extraction of the top 2 services (analytics collection + reporting), assuming parallel investment in IaC and CI/CD pipeline (Move to Modern DevOps pathway).

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure exists. The application is deployed via `docker-compose.yml` which defines a single `umami` container (using `ghcr.io/umami-software/umami:latest`) and a `postgres:15-alpine` container. No Terraform, CloudFormation, or CDK resources define ECS, EKS, Lambda, Fargate, or EC2 instances. The `Dockerfile` builds a multi-stage Node.js 22-alpine image but there is no managed orchestration platform to run it. |
| **Gap** | All compute is self-managed via Docker Compose with no managed container orchestration, no auto-recovery, no rolling deployments, and no elastic scaling. |
| **Recommendation** | Deploy to Amazon EKS (preferred) with Fargate profiles for the application workload. Create EKS cluster definition in IaC (CDK TypeScript preferred). Use EKS managed node groups or Fargate for compute. The existing Dockerfile is production-ready and can be deployed directly to EKS. |
| **Evidence** | `Dockerfile`, `docker-compose.yml`, absence of `*.tf`, `*.cfn.*`, `cdk.json` files |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. PostgreSQL 15 runs as a Docker container (`postgres:15-alpine` in `docker-compose.yml`). ClickHouse is an optional self-managed analytics backend configured via `CLICKHOUSE_URL` environment variable. Redis is self-managed via `REDIS_URL`. No `aws_rds_*`, `aws_dynamodb_*`, or other managed database resources exist in the repository. |
| **Gap** | Self-managed databases require manual patching, backup management, failover configuration, and capacity planning. No automated failover, no PITR, no managed scaling. |
| **Recommendation** | Migrate PostgreSQL to Amazon Aurora PostgreSQL (preferred). The existing `@prisma/adapter-pg` and read replica support in `src/lib/prisma.ts` indicate compatibility with Aurora's reader endpoints. Migrate Redis to Amazon ElastiCache for Redis. Use AWS DMS for the PostgreSQL migration. |
| **Evidence** | `docker-compose.yml` (postgres:15-alpine), `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `src/lib/redis.ts`, `prisma/schema.prisma` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service is in use. The analytics event collection pipeline (`src/app/api/send/route.ts`) executes a multi-step process (validate → detect client info → bot check → IP block → create session → save event → return cache token) but this is implemented as sequential inline code, not a dedicated orchestration service. Report generation queries (funnel, journey, retention in `src/queries/sql/reports/`) are also inline. For the `stateful-crud` archetype, the event collection and report generation flows represent multi-step business-critical operations that would benefit from dedicated orchestration. |
| **Gap** | No dedicated workflow orchestration — all workflow logic is hardcoded in application code with no retry/error strategy, no visual management, and no state tracking. |
| **Recommendation** | Adopt AWS Step Functions for report generation workflows (funnel, journey, retention) which may be long-running. Use Step Functions express workflows for the event collection pipeline if decomposed into a separate service. |
| **Evidence** | `src/app/api/send/route.ts`, `src/queries/sql/reports/`, absence of `aws_sfn_*` or Temporal SDK |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Self-managed Kafka is used optionally for event streaming. `src/lib/kafka.ts` configures a KafkaJS producer that sends analytics events to a Kafka broker configured via `KAFKA_URL` and `KAFKA_BROKER` environment variables. The Kafka integration is optional — the `src/lib/db.ts` `runQuery` function dispatches to Kafka only when `CLICKHOUSE_URL` is set and a Kafka query path exists. When Kafka is not configured, events are written directly to PostgreSQL via Prisma. Redis (`@umami/redis-client`) provides caching for auth tokens and website data. For the `stateful-crud` archetype, cross-service state changes (event ingestion → analytics aggregation) should use managed messaging. |
| **Gap** | Self-managed Kafka requires operational overhead (patching, scaling, monitoring). The Kafka integration is producer-only with no consumer in the application — consumption is handled by ClickHouse's Kafka table engine externally. |
| **Recommendation** | Replace self-managed Kafka with Amazon EventBridge (preferred) for event routing between the collection service and analytics backend. EventBridge provides serverless event bus with schema registry, filtering, and fan-out without broker management. Avoid self-managed Kafka per preferences. |
| **Evidence** | `src/lib/kafka.ts`, `src/lib/db.ts`, `package.json` (kafkajs@^2.1.0), `src/lib/redis.ts` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security configuration exists. No VPC, subnet, security group, or NACL definitions found. The `docker-compose.yml` exposes port 3000 directly (`"3000:3000"`). No IaC files define any AWS networking resources. The `next.config.ts` sets CORS headers to `Access-Control-Allow-Origin: *` on all API endpoints, allowing requests from any origin. |
| **Gap** | Services are deployed without network isolation, without private subnets, and without least-privilege security groups. The wildcard CORS policy is appropriate for the analytics collection tracker (which must be embeddable on any website) but overly permissive for management API endpoints. |
| **Recommendation** | Define a VPC with public and private subnets in IaC. Place the application in private subnets behind an API Gateway (preferred) or ALB. Restrict CORS on management API endpoints (`/api/users/*`, `/api/teams/*`, `/api/admin/*`) to known origins while keeping `/api/send` open for tracker embedding. Add VPC endpoints for AWS services (S3, Secrets Manager, RDS). |
| **Evidence** | `docker-compose.yml`, `next.config.ts` (CORS config), absence of VPC/subnet IaC |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed API entry point exists. The Next.js application serves directly on port 3000 with no API Gateway, ALB, or CloudFront in front of it. The `docker-compose.yml` maps port 3000 directly. There is no throttling, no request validation at the gateway level, and no centralized auth enforcement. The README suggests using nginx as a reverse proxy but no configuration is provided in the repository. |
| **Gap** | No managed entry point — no throttling, no DDoS protection, no centralized authentication, no request routing. The `/api/send` endpoint (analytics collection) is exposed directly, making it vulnerable to abuse without rate limiting. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point. Configure throttling and request validation on all API endpoints. Use API Gateway's built-in auth (Cognito authorizer or Lambda authorizer) for management endpoints. Add CloudFront for static asset caching and global distribution of the tracker script. |
| **Evidence** | `docker-compose.yml`, `next.config.ts`, `README.md`, absence of API Gateway/ALB IaC |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists anywhere in the repository. The `docker-compose.yml` runs a single instance of each service with no scaling configuration. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or replica configuration found. The application has no mechanism to handle traffic spikes — during high-traffic periods, the single container must absorb all load. |
| **Gap** | All capacity is statically provisioned. No auto-scaling for compute, database, or caching layers. |
| **Recommendation** | When deployed to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on request rate and CPU utilization. Configure Aurora auto-scaling for read replicas. Configure ElastiCache auto-scaling for Redis shards. |
| **Evidence** | `docker-compose.yml`, absence of any scaling configuration |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. PostgreSQL data is stored in a Docker volume (`umami-db-data:/var/lib/postgresql/data`) with no backup strategy. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning, no PITR configuration. The `docker-compose.yml` defines the volume but no backup mechanism. If the volume is lost, all analytics data and user accounts are permanently lost. |
| **Gap** | No automated backups, no retention policy, no PITR, no restore procedures, no cross-region replication. Total data loss risk. |
| **Recommendation** | When migrated to Aurora PostgreSQL (preferred), enable automated backups with 14-day retention and PITR. Enable Aurora global database for cross-region DR if the analytics data is business-critical. Document and test restore procedures. |
| **Evidence** | `docker-compose.yml` (Docker volumes), absence of backup IaC |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No high availability configuration exists. The `docker-compose.yml` runs a single application container and a single PostgreSQL container, both on the same host. No multi-AZ configuration, no load balancer, no health-based failover. The `restart: always` policy provides basic container restart but not host-level or AZ-level fault isolation. Surface flags confirm: `has_deployed_workload=true`, `has_api_surface=true`, `has_multi_instance_deployment=false`. |
| **Gap** | Single point of failure at every layer — application, database, and host. Any host failure takes down the entire analytics platform. |
| **Recommendation** | Deploy to EKS (preferred) with replicas across 2+ AZs. Use Aurora PostgreSQL Multi-AZ for database HA. Place behind an ALB with cross-zone load balancing enabled. |
| **Evidence** | `docker-compose.yml`, absence of multi-AZ or replica configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure-as-code files exist in the repository. No Terraform (`.tf`, `.tfvars`), no CloudFormation (`template.yaml`, `*.cfn.*`), no CDK (`cdk.json`), no Helm charts (`Chart.yaml`), no Kustomize (`kustomization.yaml`). The only infrastructure definition is `docker-compose.yml` which defines two containers and a volume — this is a local development/simple deployment tool, not production IaC. |
| **Gap** | 0% IaC coverage. All infrastructure is manually created. No reproducible deployments, no environment consistency, no disaster recovery automation. |
| **Recommendation** | Adopt AWS CDK with TypeScript (matches the existing codebase language). Define the complete infrastructure stack: VPC, EKS cluster, Aurora PostgreSQL, ElastiCache, API Gateway, EventBridge, CloudWatch alarms, and Backup plans. Start with a minimal CDK stack for the existing docker-compose topology (ECS/Fargate + RDS) and expand incrementally. |
| **Evidence** | Absence of `*.tf`, `*.cfn.*`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` — confirmed via find command |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides partial CI/CD automation. `ci.yml` runs on every push: installs dependencies, runs `pnpm test` (Jest), and runs `pnpm build`. `cd.yml` triggers on version tags: builds multi-platform Docker images (linux/amd64, linux/arm64) and pushes to GHCR and Docker Hub. `cd-cloud.yml` builds cloud-specific images on branch push. However, there is no deployment automation — images are pushed to registries but deployment to production infrastructure is not automated. No IaC deployment pipeline exists. No automated rollback. |
| **Gap** | Build is automated but deployment is manual. No IaC pipeline. No automated rollback. Cypress E2E tests exist but are not run in CI. |
| **Recommendation** | Extend the GitHub Actions pipeline with: (1) Cypress E2E tests in CI, (2) CDK/Terraform deployment stage triggered by image push, (3) automated rollback on deployment failure, (4) security scanning (Dependabot, container scanning). |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/cd-cloud.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript 5.9+ (`typescript@^5.9.3`) with Next.js 15 (`next@^15.5.9`) and React 19 (`react@^19.2.3`). The CI pipeline uses Node.js 18.18. Modern cloud-native language version with modern framework. Zod for runtime validation (`zod@^4.1.13`), Prisma 6.18 for ORM. The stack has first-class AWS SDK support (though no AWS SDK is currently imported). TypeScript/Node.js is a Tier 1 AWS SDK language with comprehensive service coverage. |
| **Gap** | No significant language-level gaps. No AWS SDK currently imported (`@aws-sdk/*` packages absent), but this is expected for a self-hosted application not yet on AWS. |
| **Recommendation** | No language migration needed. When integrating AWS services, add `@aws-sdk/client-*` packages for the required services. The TypeScript ecosystem provides excellent AWS SDK v3 support. |
| **Evidence** | `package.json` (typescript@^5.9.3, next@^15.5.9, react@^19.2.3), `tsconfig.json` (target: es2022), `.github/workflows/ci.yml` (Node.js 18.18) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single Next.js application with all functionality in one deployable unit. The codebase bundles: frontend (React components in `src/components/`), backend (75 API routes in `src/app/api/`), data access (Prisma ORM in `src/queries/prisma/` and raw SQL in `src/queries/sql/`), authentication (`src/lib/auth.ts`, `src/lib/jwt.ts`), and business logic (`src/lib/`). Has identifiable modules with clear directory structure, but all share a single PostgreSQL database via the same Prisma schema (`prisma/schema.prisma` with 13 models). Cross-module data access exists — the `send` route directly imports from `src/queries/sql` and `src/lib/detect.ts`. |
| **Gap** | Monolith with identifiable modules but shared database schema, single deployable unit, and no independent scaling. All 75 API routes must scale together even though analytics collection (`/api/send`) has vastly different throughput requirements than admin operations. |
| **Recommendation** | Apply Strangler Fig decomposition — extract the analytics collection endpoint (`/api/send`) as an independent service first. See Decomposition Strategy section for detailed approach. |
| **Evidence** | `src/app/api/` (75 route files), `prisma/schema.prisma` (13 shared models), `src/queries/prisma/`, `src/queries/sql/`, `Dockerfile` (single deployable) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | All API endpoints are synchronous HTTP request/response. The 75 API route handlers in `src/app/api/` all follow the pattern: receive request → validate → query database → return JSON response. Kafka is available as an optional event producer (`src/lib/kafka.ts`) but is not used for inter-service communication — it's a fire-and-forget event forwarder to ClickHouse. Redis provides caching but not async communication. For the `stateful-crud` archetype, the application should have async patterns for cross-service state propagation, particularly for the event ingestion → analytics aggregation flow. |
| **Gap** | Primarily synchronous with some async for background event forwarding (Kafka). No async patterns for long-running analytics queries or cross-service state changes. |
| **Recommendation** | When decomposed, introduce EventBridge (preferred) for async event routing between the collection service and analytics backend. Use SQS for buffering event ingestion during traffic spikes. Keep synchronous HTTP for read-heavy dashboard queries where latency is critical. |
| **Evidence** | `src/app/api/send/route.ts`, `src/lib/kafka.ts`, `src/lib/db.ts`, `src/lib/request.ts` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Report generation queries (funnel analysis via `src/queries/sql/reports/getFunnel.ts`, journey analysis via `getJourney.ts`, retention analysis via `getRetention.ts`) perform complex analytical queries across large datasets and may exceed 30 seconds for websites with high traffic volumes. These are handled synchronously — the API endpoint blocks until the query completes. No background job framework (e.g., Bull, Celery, SQS workers) is configured. No status polling or callback patterns exist. The event collection endpoint (`/api/send`) is fast (simple insert) but bulk batch operations (`/api/batch`) could also be slow for large payloads. For the `stateful-crud` archetype, some background job processing exists (Kafka event forwarding) but the pattern is inconsistent. |
| **Gap** | Long-running analytics queries are handled synchronously. No async job processing, no status polling, no timeout management for complex report generation. |
| **Recommendation** | Implement async report generation using Step Functions: (1) Client requests report via API → returns job ID immediately, (2) Step Functions executes the query asynchronously, (3) Client polls for completion or receives callback. Use DynamoDB (preferred) for job status tracking. |
| **Evidence** | `src/queries/sql/reports/getFunnel.ts`, `src/queries/sql/reports/getJourney.ts`, `src/queries/sql/reports/getRetention.ts`, `src/app/api/batch/route.ts` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. All 75 API routes in `src/app/api/` use unversioned paths (e.g., `/api/websites`, `/api/users`, `/api/send`). No `/v1/` URL patterns, no `Accept-Version` headers, no versioning annotations. API changes are deployed directly — any breaking change affects all consumers simultaneously. The tracker script (`script.js`) embeds the current API contract with no version negotiation. |
| **Gap** | No versioning — breaking changes deployed directly. The tracker script embedded on third-party websites has no version pinning, making breaking API changes risky for all tracked websites. |
| **Recommendation** | Introduce URL-based versioning (`/api/v1/`) for the external-facing collection endpoint (`/api/send`) and the share/embed endpoints. Internal management APIs can use header-based versioning. When deploying API Gateway (preferred), use stage-based versioning. |
| **Evidence** | `src/app/api/` (all unversioned routes), `src/tracker/` (tracker script), `next.config.ts` (rewrite rules) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | External service endpoints are configured via environment variables: `DATABASE_URL` (PostgreSQL), `CLICKHOUSE_URL` (ClickHouse), `KAFKA_URL` and `KAFKA_BROKER` (Kafka), `REDIS_URL` (Redis). No dynamic service discovery mechanism exists. As a monolith, there is no inter-service communication to discover — but the external dependency endpoints (database, cache, message broker) are hard-coded in environment variables with no dynamic resolution. |
| **Gap** | Environment variables for all endpoints with no dynamic discovery. When decomposed into microservices, hard-coded environment variables will create deployment coupling between services. |
| **Recommendation** | When deployed to EKS (preferred), use Kubernetes-native service discovery (CoreDNS) for inter-service communication. For AWS services, use VPC endpoints with deterministic DNS names. Consider AWS Cloud Map for cross-service discovery as the architecture decomposes. |
| **Evidence** | `src/lib/prisma.ts` (DATABASE_URL), `src/lib/clickhouse.ts` (CLICKHOUSE_URL), `src/lib/kafka.ts` (KAFKA_URL, KAFKA_BROKER), `src/lib/redis.ts` (REDIS_URL) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The GeoLite2 MaxMind database (`GeoLite2-City.mmdb`) is stored on the local filesystem in the `geo/` directory. The `src/lib/detect.ts` loads it via `maxmind.open(path.resolve(dir, 'GeoLite2-City.mmdb'))`. The `scripts/build-geo.js` downloads this file during build. No S3 usage detected for any unstructured data storage. Analytics data (events, sessions, pageviews) is all structured and stored in PostgreSQL/ClickHouse. Localization files (`public/intl/messages/`) are stored as JSON in the local filesystem. |
| **Gap** | Unstructured data (GeoIP database, localization files) stored on local filesystem. No managed object storage. The GeoIP database must be re-downloaded on every container build. |
| **Recommendation** | Store the GeoIP database and localization assets in Amazon S3. Use S3 presigned URLs or S3 File Gateway for access. This enables versioning, cross-region replication, and eliminates the need to rebuild containers when the GeoIP database is updated. |
| **Evidence** | `src/lib/detect.ts` (maxmind.open), `scripts/build-geo.js`, `public/intl/messages/`, absence of S3 configuration |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-organized centralized data access architecture. `src/lib/db.ts` provides a unified `runQuery` dispatcher that routes queries to PostgreSQL (Prisma), ClickHouse, or Kafka based on the deployment configuration. `src/queries/prisma/` contains 8 module-specific query files (user, website, team, report, segment, link, pixel, teamUser) for CRUD operations via Prisma ORM. `src/queries/sql/` contains 40+ analytical query functions organized by domain (events, pageviews, sessions, reports). `src/lib/prisma.ts` provides the Prisma client with read replica support. `src/lib/clickhouse.ts` provides the ClickHouse client with query utilities. |
| **Gap** | Mostly centralized with some direct access patterns. The `runQuery` dispatcher is not used universally — some API routes import directly from `src/queries/prisma/` bypassing the dispatcher. The Prisma and ClickHouse query layers use different query patterns (ORM vs raw SQL) with no unified abstraction above them. |
| **Recommendation** | Enforce all data access through the `runQuery` dispatcher or a consistent repository pattern. When decomposing into services, each service should own its data access layer with clear contracts. |
| **Evidence** | `src/lib/db.ts` (runQuery), `src/queries/prisma/index.ts`, `src/queries/sql/index.ts`, `src/lib/prisma.ts`, `src/lib/clickhouse.ts` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | PostgreSQL 15 is pinned in `docker-compose.yml` as `postgres:15-alpine`. PostgreSQL 15 is currently supported with EOL in November 2027 — not approaching EOL. The Prisma schema (`prisma/schema.prisma`) specifies `provider = "postgresql"` but does not pin a version. ClickHouse version is not explicitly pinned — it is accessed via `CLICKHOUSE_URL` and version depends on the external deployment. The `Dockerfile` uses `PRISMA_VERSION="6.19.0"` for the Prisma engine. |
| **Gap** | PostgreSQL version is pinned and current. ClickHouse version is not pinned — version drift risk. No documented version-update procedure covering downtime windows, rollback, or risk acknowledgment. |
| **Recommendation** | When migrating to Aurora PostgreSQL, pin the engine version in IaC. Establish a version-update procedure. For ClickHouse, pin the version in the deployment configuration. |
| **Evidence** | `docker-compose.yml` (postgres:15-alpine), `prisma/schema.prisma` (provider = "postgresql"), `Dockerfile` (PRISMA_VERSION) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found. All business logic resides in the TypeScript application layer. The Prisma ORM handles all CRUD operations for user, website, team, report, segment, link, and pixel entities. Raw SQL queries in `src/queries/sql/` use standard PostgreSQL SQL (date_trunc, grouping, window functions) and standard ClickHouse SQL (formatDateTime, MergeTree-specific syntax). The ClickHouse schema (`db/clickhouse/schema.sql`) defines tables, materialized views, and projections using ClickHouse-native DDL — but no stored procedures or triggers. Migration files (`prisma/migrations/`) are pure DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX) with no procedural SQL. |
| **Gap** | No gaps. All business logic is in the application layer. The ClickHouse materialized views are declarative aggregations, not procedural business logic. |
| **Recommendation** | Maintain the current approach — keeping business logic in the application layer simplifies database migration and enables engine portability. |
| **Evidence** | `prisma/schema.prisma`, `prisma/migrations/`, `db/clickhouse/schema.sql`, `src/queries/sql/`, `src/queries/prisma/` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration exists. No IaC defines any logging infrastructure. The application uses the `debug` module (`debug@^4.4.3`) for development logging (`umami:auth`, `umami:prisma`, `umami:clickhouse`, `umami:kafka`) but this is debug-level output, not structured audit logging. No immutable log storage, no log retention policies, no centralized log aggregation. Admin actions (user creation, password changes, website deletion) are not logged in an audit trail. |
| **Gap** | No audit logging. Admin actions are untracked. No forensic analysis capability after incidents. |
| **Recommendation** | Enable CloudTrail for AWS API audit logging when deployed on AWS. Add application-level audit logging for admin actions (user CRUD, website CRUD, team management) using structured JSON logs shipped to CloudWatch Logs with defined retention. |
| **Evidence** | `src/lib/auth.ts` (debug logging only), absence of CloudTrail IaC, absence of structured audit log implementation |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration exists. PostgreSQL data is stored in a Docker volume (`umami-db-data`) with no encryption. No KMS keys, no encryption configuration on any data store. The application handles sensitive data including user passwords (hashed with bcryptjs), session tokens, and website analytics data. Surface flag `has_at_rest_data_surface=true` confirms this question applies. |
| **Gap** | No encryption at rest for any data store. PostgreSQL Docker volume is unencrypted. Analytics data (including user behavior, IP-derived geolocation) is stored without encryption. |
| **Recommendation** | When migrated to Aurora PostgreSQL (preferred), enable KMS encryption with a customer-managed key. Enable S3 default encryption for any object storage. Enable EBS encryption for any block storage. |
| **Evidence** | `docker-compose.yml` (unencrypted Docker volume), absence of KMS/encryption IaC |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Custom JWT-based authentication implemented in `src/lib/jwt.ts` and `src/lib/auth.ts`. Bearer token authentication via `checkAuth()` function. Login endpoint (`src/app/api/auth/login/route.ts`) accepts username/password, verifies with bcryptjs, and returns an encrypted JWT or Redis-backed auth key. The `/api/send` endpoint is intentionally unauthenticated (`skipAuth: true`) as it's the public analytics collection endpoint. The SSO endpoint (`src/app/api/auth/sso/route.ts`) generates short-lived Redis-backed tokens. The implementation uses AES-256-GCM encryption for token security (`src/lib/crypto.ts`). However, this is custom JWT — not OAuth2/OIDC standard. No token refresh mechanism. No API Gateway authorizer. |
| **Gap** | Custom JWT implementation rather than OAuth2/OIDC standard. No token refresh mechanism. No API key or rate limiting on the public `/api/send` endpoint. No centralized auth enforcement at gateway level. |
| **Recommendation** | When deploying API Gateway (preferred), use Cognito User Pool or Lambda authorizer for management endpoints. Implement OAuth2 flows for the admin interface. Add API key with usage plan on the `/api/send` endpoint for abuse prevention. |
| **Evidence** | `src/lib/jwt.ts`, `src/lib/auth.ts`, `src/lib/crypto.ts`, `src/app/api/auth/login/route.ts`, `src/app/api/auth/sso/route.ts`, `src/lib/request.ts` (skipAuth) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. User credentials (username + bcryptjs-hashed password) are stored in the `user` table via Prisma ORM (`prisma/schema.prisma`). Login is username/password only (`src/app/api/auth/login/route.ts`). The SSO endpoint (`src/app/api/auth/sso/route.ts`) exists but is not an external IdP integration — it generates a Redis-backed auth token for an already-authenticated user (used for cross-domain SSO within Umami's own infrastructure). No Cognito, Okta, Ping, Auth0, OIDC, or SAML integration detected. No external identity provider federation. |
| **Gap** | Application manages its own authentication with no external IdP integration. No SSO with corporate identity providers. No federated login (Google, GitHub, etc.). |
| **Recommendation** | Integrate with Amazon Cognito as the identity provider. Cognito supports OIDC/SAML federation with corporate IdPs, social login (Google, GitHub), and manages user pools. Replace the custom auth implementation with Cognito-issued JWTs verified by API Gateway. |
| **Evidence** | `src/app/api/auth/login/route.ts`, `src/app/api/auth/sso/route.ts`, `src/lib/password.ts`, `prisma/schema.prisma` (User model with password field) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Plaintext credentials are present in the repository. `docker-compose.yml` contains hardcoded database credentials: `POSTGRES_DB: umami`, `POSTGRES_USER: umami`, `POSTGRES_PASSWORD: umami`. The `DATABASE_URL` in docker-compose embeds these credentials: `postgresql://umami:umami@db:5432/umami`. The `APP_SECRET` is set to a placeholder value `replace-me-with-a-random-string`. The `Dockerfile` builder stage also contains `DATABASE_URL="postgresql://user:pass@localhost:5432/dummy"` (dummy value for build). All other secrets (`KAFKA_URL`, `REDIS_URL`, `CLICKHOUSE_URL`) are expected via environment variables with no secrets manager integration. No `aws_secretsmanager_*`, no Vault client imports, no `.env` encryption. |
| **Gap** | Plaintext credentials committed to version control. Placeholder APP_SECRET in docker-compose. No secrets rotation. No encrypted parameter store. |
| **Recommendation** | Migrate all secrets to AWS Secrets Manager. Store database credentials, APP_SECRET, Kafka credentials, and Redis credentials in Secrets Manager with automated rotation. Reference secrets via ARN in EKS pod configurations (External Secrets Operator) or CDK. Remove all hardcoded credentials from docker-compose.yml. |
| **Evidence** | `docker-compose.yml` (POSTGRES_USER: umami, POSTGRES_PASSWORD: umami, APP_SECRET: replace-me-with-a-random-string), `Dockerfile` (DATABASE_URL dummy) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. The `Dockerfile` uses `node:22-alpine` as the base image — Alpine is a minimal image which is a positive signal, but no vulnerability scanning, no hardened AMI, no SSM Patch Manager, no Inspector configuration. The Docker image creates a non-root user (`nextjs:nodejs` with UID/GID 1001) which is a security best practice. However, no container scanning is configured in the CI/CD pipeline. No Snyk, no ECR image scanning, no Trivy. |
| **Gap** | No vulnerability scanning on container images. No patching strategy. No CIS-hardened base images. The only positive signal is the Alpine base and non-root user. |
| **Recommendation** | Add container image scanning to the CD pipeline (ECR image scanning or Trivy in GitHub Actions). Use Bottlerocket or Amazon Linux-based images for EKS nodes. Enable AWS Inspector for runtime vulnerability detection. |
| **Evidence** | `Dockerfile` (node:22-alpine, USER nextjs), absence of scanning tools in CI/CD |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are configured in the CI/CD pipeline. The `ci.yml` workflow only runs `pnpm test` and `pnpm build`. No Dependabot configuration (`.github/dependabot.yml` not found). No Snyk (`.snyk` not found). No SonarQube or Semgrep. No `npm audit` or `pnpm audit` in the pipeline. No container scanning in the `cd.yml` Docker build workflow. No SAST tools configured. |
| **Gap** | No security scanning — no SAST, no DAST, no dependency scanning, no container scanning. Vulnerabilities in the 60+ production dependencies (including `jsonwebtoken`, `bcryptjs`, `kafkajs`, `pg`) could reach production undetected. |
| **Recommendation** | Add Dependabot for automated dependency updates. Add `pnpm audit` to the CI pipeline with a blocking gate on critical findings. Add ECR image scanning or Trivy for container scanning in the CD pipeline. Consider Amazon CodeGuru Reviewer for SAST. |
| **Evidence** | `.github/workflows/ci.yml` (no security steps), `.github/workflows/cd.yml` (no scanning), absence of `.github/dependabot.yml`, `.snyk`, `sonar-project.properties` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, no X-Ray SDK, no tracing library in dependencies. The `debug` module (`debug@^4.4.3`) is used for development logging with namespaces (`umami:auth`, `umami:prisma`, `umami:clickhouse`, `umami:kafka`) but provides no trace ID propagation, no request correlation, and no cross-service tracing. No `traceparent` or `X-Amzn-Trace-Id` header handling. |
| **Gap** | No distributed tracing. When the application is decomposed into microservices, debugging cross-service failures will be impossible without tracing. Even as a monolith, request tracing through the database layers (Prisma → PostgreSQL, ClickHouse client → ClickHouse) is unobservable. |
| **Recommendation** | Instrument with AWS X-Ray SDK or OpenTelemetry (OTEL) SDK for Node.js. X-Ray integrates natively with EKS, API Gateway, and Lambda. Add the OTEL auto-instrumentation for Prisma, HTTP clients, and ClickHouse queries. |
| **Evidence** | `package.json` (no tracing dependencies), `src/lib/` (debug module usage only) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No availability targets, no latency targets, no error rate budgets. No CloudWatch alarms on p99/p95 latency. No SLO dashboard configuration. The application has a heartbeat endpoint (`/api/heartbeat`) used by Docker health checks but this is a basic alive/not-alive check, not an SLO. Surface flag `has_api_surface=true` confirms this question applies. |
| **Gap** | No formal SLOs. No definition of acceptable service levels for analytics collection (which must be low-latency to avoid impacting tracked websites), dashboard rendering, or API response times. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Analytics collection endpoint (`/api/send`) — p99 latency < 200ms, availability > 99.9%, (2) Dashboard load — p95 < 3s, (3) Report generation — completion within 30s for standard reports. Implement SLO monitoring with CloudWatch and error budget tracking. |
| **Evidence** | `src/app/api/heartbeat/route.ts` (basic health check only), absence of SLO definitions or CloudWatch alarms |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom observability metrics are published. The application tracks analytics data (page views, events, sessions, revenue) as its core product — but these are the product itself, not observability metrics about the product. No `cloudwatch.put_metric_data` calls. No custom dashboards for monitoring the health of the analytics platform (e.g., events ingested per second, unique sessions per hour, report generation latency, Kafka lag). |
| **Gap** | No business outcome metrics published as observability signals. The team has no visibility into operational metrics like event ingestion rate, processing latency, or error rates by endpoint. |
| **Recommendation** | Publish custom CloudWatch metrics for: events ingested/second, unique sessions/hour, report generation p99 latency, Kafka producer lag (when enabled), cache hit rate, API error rate by endpoint. Create a CloudWatch dashboard for operational visibility. |
| **Evidence** | `package.json` (no CloudWatch SDK), absence of metrics publishing code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection is configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no alerting configuration of any kind. The `docker-compose.yml` health check (`curl http://localhost:3000/api/heartbeat`) provides basic liveness detection but no alerting on failure — it only triggers Docker container restart. |
| **Gap** | No alerting. If the analytics collection endpoint goes down, tracked websites silently lose data with no notification. No error rate alerts, no latency anomaly detection. |
| **Recommendation** | Configure CloudWatch alarms for: (1) HTTP 5xx error rate > 1%, (2) p99 latency anomaly detection on `/api/send`, (3) database connection errors, (4) Kafka producer failures. Integrate with SNS topics for email/Slack/PagerDuty notification. |
| **Evidence** | `docker-compose.yml` (healthcheck only), absence of alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The CD pipeline (`cd.yml`) builds Docker images and pushes them to GHCR and Docker Hub. Actual deployment to running infrastructure is manual — users pull the latest image and restart docker-compose. No blue/green deployment, no canary releases, no rolling updates, no traffic shifting. No CodeDeploy, no Argo Rollouts, no Helm release management. The `docker-compose.yml` uses `restart: always` for container recovery but this is not a deployment strategy. |
| **Gap** | Direct-to-production deployment with no staged rollout. No traffic shifting, no automated rollback. Image updates require manual `docker compose pull && docker compose up`. |
| **Recommendation** | When deployed to EKS (preferred), implement rolling updates with Kubernetes Deployment strategy and readiness/liveness probes. Advance to canary deployments using Argo Rollouts or AWS App Mesh traffic shifting. Use EKS with CodeDeploy for blue/green deployments. |
| **Evidence** | `.github/workflows/cd.yml` (image push only), `docker-compose.yml` (restart: always) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Jest is configured for unit tests (`jest.config.ts`) with 3 test files in `src/lib/__tests__/` (charts.test.ts, detect.test.ts, format.test.ts). Cypress is configured for E2E/integration tests (`cypress.config.ts`) with 6 test files in `cypress/e2e/` covering API team operations, API user operations, API website operations, login flow, user management, and website management. However, only Jest runs in the CI pipeline (`pnpm test` in `ci.yml`). Cypress tests are not executed in CI — they exist but are not integrated into the automated pipeline. The `cypress/docker-compose.yml` provides a Cypress test environment but it's not referenced in any CI workflow. |
| **Gap** | Cypress E2E tests exist but are not run in CI. Only 3 unit test files cover utility functions (charts, detect, format) — no tests for critical paths like event collection, authentication, or data access. |
| **Recommendation** | Add Cypress E2E tests to the CI pipeline using the existing `cypress/docker-compose.yml` for the test environment. Add unit tests for critical paths: `/api/send` event collection, `src/lib/auth.ts` authentication, `src/queries/` data access layer. |
| **Evidence** | `jest.config.ts`, `src/lib/__tests__/` (3 files), `cypress.config.ts`, `cypress/e2e/` (6 files), `.github/workflows/ci.yml` (pnpm test only) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no self-healing automation. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The `docker-compose.yml` `restart: always` policy provides basic container restart (self-healing at the container level) but this is not a documented incident response procedure. No knowledge base articles, no troubleshooting guides in the repository. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (database connection failure, Kafka producer errors, high memory usage, disk full). |
| **Recommendation** | Create runbooks for common failure scenarios as Markdown files in the repository. Automate recovery for known failure modes using SSM Automation documents or Lambda remediation functions. Implement self-healing for stateless components via Kubernetes liveness probes and HPA when on EKS. |
| **Evidence** | Absence of runbook files, SSM documents, or remediation Lambda functions |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership structure exists. No CODEOWNERS file referencing observability configurations. No per-service dashboards. No named alarm owners. No SLO definitions with team attribution. No team tags on monitoring resources (no monitoring resources exist at all). |
| **Gap** | No observability ownership. Monitoring is non-existent rather than fragmented — there are no alarms, dashboards, or SLOs to own. |
| **Recommendation** | Establish observability ownership as part of the IaC and DevOps modernization. Create a CODEOWNERS file with team ownership of monitoring configurations. Define per-service dashboards and alarms with named owners when the architecture is decomposed. |
| **Evidence** | Absence of CODEOWNERS, CloudWatch dashboard definitions, alarm configurations |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists. No IaC files exist to tag resources. No `default_tags` in Terraform provider, no `tags` on CloudFormation resources, no tag enforcement policies. The `docker-compose.yml` containers have no labels or tags for cost allocation, ownership, or environment identification. |
| **Gap** | No tagging. When deployed to AWS, resources will have no cost allocation tags, no ownership attribution, and no environment identification. |
| **Recommendation** | Define a tagging standard as part of the IaC adoption. Require tags in CDK constructs: `Environment`, `Service`, `Team`, `CostCenter`. Enforce via AWS Tag Policies in Organizations and AWS Config rules. |
| **Evidence** | Absence of any IaC with tags, `docker-compose.yml` (no labels) |

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

### Configuration & Deployment Files

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `Dockerfile` | INF-Q1, INF-Q6, SEC-Q6, Move to Containers | Multi-stage Node.js 22-alpine Docker build with non-root user |
| `docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, SEC-Q2, SEC-Q5, OPS-Q4, OPS-Q5, OPS-Q9 | Defines umami app + postgres:15-alpine with hardcoded credentials |
| `next.config.ts` | INF-Q5, INF-Q6, APP-Q5 | CORS configuration, CSP headers, URL rewrites |
| `package.json` | APP-Q1, INF-Q4, OPS-Q1, OPS-Q3, SEC-Q7 | Dependencies: TypeScript 5.9+, Next.js 15, React 19, KafkaJS, Prisma 6.18 |
| `pnpm-workspace.yaml` | Metadata | Monorepo workspace configuration |
| `tsconfig.json` | APP-Q1 | TypeScript configuration with ES2022 target |

### CI/CD Workflow Files

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | Build + test on push (Node.js 18.18, pnpm test, pnpm build) |
| `.github/workflows/cd.yml` | INF-Q11, OPS-Q5, SEC-Q7 | Docker image build on tag push to GHCR and Docker Hub |
| `.github/workflows/cd-cloud.yml` | INF-Q11 | Cloud-specific Docker build on branch push |

### Database & Data Layer Files

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `prisma/schema.prisma` | INF-Q2, APP-Q2, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q4 | 14 Prisma models (User, Session, Website, WebsiteEvent, etc.) |
| `prisma/migrations/` | DATA-Q3, DATA-Q4 | 14 SQL migrations (DDL only, no stored procedures) |
| `db/clickhouse/schema.sql` | DATA-Q1, DATA-Q4, Move to Managed Analytics | ClickHouse tables, materialized views, projections |
| `src/lib/db.ts` | INF-Q4, APP-Q3, DATA-Q2 | Unified runQuery dispatcher (Prisma/ClickHouse/Kafka) |
| `src/lib/prisma.ts` | INF-Q2, DATA-Q2, DATA-Q3 | Prisma client with read replica support |
| `src/lib/clickhouse.ts` | INF-Q2, INF-Q4, DATA-Q2 | ClickHouse client with query utilities |
| `src/lib/kafka.ts` | INF-Q4, APP-Q3, Move to Managed Analytics | KafkaJS producer for optional event streaming |
| `src/lib/redis.ts` | INF-Q2, APP-Q3, APP-Q6 | Redis client for caching and auth token storage |
| `src/queries/prisma/index.ts` | APP-Q2, DATA-Q2, DATA-Q4 | Prisma query exports (8 modules: user, website, team, etc.) |
| `src/queries/sql/index.ts` | APP-Q2, APP-Q4, DATA-Q2 | SQL query exports (40+ analytics functions) |

### Authentication & Security Files

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/lib/auth.ts` | SEC-Q1, SEC-Q3, SEC-Q4 | Bearer token auth, checkAuth(), Redis-backed auth keys |
| `src/lib/jwt.ts` | SEC-Q3, SEC-Q4 | JWT creation, parsing, encrypted tokens |
| `src/lib/crypto.ts` | SEC-Q3 | AES-256-GCM encryption, SHA-512 hashing, UUID generation |
| `src/lib/password.ts` | SEC-Q4 | bcryptjs password hashing (10 salt rounds) |
| `src/app/api/auth/login/route.ts` | SEC-Q3, SEC-Q4 | Username/password login → JWT token |
| `src/app/api/auth/sso/route.ts` | SEC-Q4 | Redis-backed SSO token generation |
| `src/lib/request.ts` | SEC-Q3, APP-Q3 | Request parsing with auth check and schema validation |

### API & Application Files

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/app/api/send/route.ts` | INF-Q3, APP-Q2, APP-Q3, APP-Q4, SEC-Q3 | Analytics collection endpoint (POST, skipAuth, event processing pipeline) |
| `src/app/api/` (75 route files) | APP-Q2, APP-Q5, APP-Q6 | All API routes (unversioned) |
| `src/lib/detect.ts` | DATA-Q1 | GeoIP detection using MaxMind (local filesystem) |
| `src/lib/response.ts` | APP-Q3 | Standardized HTTP responses (ok, json, badRequest, unauthorized, etc.) |

### Testing Files

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `jest.config.ts` | OPS-Q6 | Jest configuration for unit tests |
| `src/lib/__tests__/` (3 files) | OPS-Q6 | Unit tests: charts.test.ts, detect.test.ts, format.test.ts |
| `cypress.config.ts` | OPS-Q6 | Cypress E2E configuration |
| `cypress/e2e/` (6 files) | OPS-Q6 | E2E tests: API team/user/website, login, user, website |

### Documentation

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `README.md` | INF-Q6, Quick Agent Wins | Installation guide, Docker setup, getting started |
