# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | umami |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, analytics, web-app |
| **Context** | Self-hosted privacy-focused web analytics. |
| **Overall Score** | 1.73 / 4.0 |

**Archetype Justification**: The application owns persistent state via PostgreSQL (user, website, team, report CRUD) and ClickHouse (analytics event data). It exposes Create/Update/Delete endpoints alongside read-heavy analytics queries, manages entity lifecycles (soft deletes via `deletedAt`, user roles, team memberships), and handles user-specific data (`userId`, `sessionId`). Although marked as monorepo, this is effectively a single Next.js application — classified as `stateful-crud`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.36 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.73 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q2: Managed Databases | 1 | All databases (PostgreSQL, ClickHouse) are self-managed via Docker Compose with no managed services | Operational burden: manual patching, no automated failover, no PITR, single point of failure |
| 2 | INF-Q10: IaC Coverage | 1 | Zero infrastructure-as-code — all infrastructure is manually configured Docker Compose or ClickOps | Non-reproducible environments, no disaster recovery, no environment consistency |
| 3 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation — Docker Compose exposes port 3000 directly | Services exposed without network isolation; no blast radius containment |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline | Vulnerabilities in dependencies or code reach production undetected |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumentation — only `debug` npm package for basic logging | No visibility into request flows; debugging production issues is guesswork |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** Database with clear, documented schema (DATA-Q2 = 3). The Prisma schema (`prisma/schema.prisma`) provides a fully documented PostgreSQL data model with 12 entities. ClickHouse schema (`db/clickhouse/schema.sql`) defines the analytics data model. The unified data access layer in `src/lib/db.ts`, `src/lib/prisma.ts`, and `src/lib/clickhouse.ts` provides structured query interfaces.
- **What it enables:** A natural-language-to-SQL agent that queries analytics data (pageviews, sessions, events, revenue) from both PostgreSQL and ClickHouse, enabling non-technical users to extract insights without writing SQL.
- **Additional steps:** Generate OpenAPI spec from existing Next.js API routes to provide a machine-readable interface catalog. The Prisma schema already serves as a data dictionary.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). GitHub Actions workflows exist for CI (`.github/workflows/ci.yml` — build and test) and CD (`.github/workflows/cd.yml` — Docker image build and push to GHCR/Docker Hub).
- **What it enables:** An agent that triggers image builds, checks CI status, monitors Docker image tags, and manages release workflows via the GitHub API.
- **Additional steps:** Add deployment automation (currently only image building is automated, not deployment). Agent can orchestrate the existing `docker compose pull && docker compose up` pattern.
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists. `README.md` provides setup instructions, Docker deployment guides, and update procedures. External documentation exists at `umami.is/docs`. Code is well-structured with TypeScript types providing self-documentation.
- **What it enables:** An agent that indexes the README, code comments, TypeScript types, and Prisma schema to answer developer questions about the codebase, deployment procedures, and data model.
- **Additional steps:** Index the external documentation site (`umami.is/docs`) alongside the repository content. Consider using Amazon Bedrock for the knowledge base.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** Workflow orchestration in place (INF-Q3 = 2). The application has inline multi-step workflows — event ingestion (`/api/send`) coordinates session creation, event storage, and data routing across PostgreSQL and ClickHouse. ClickHouse materialized views provide automated data aggregation.
- **What it enables:** An agent that monitors event ingestion health, tracks materialized view freshness, and triggers data maintenance operations (migration runs, data exports).
- **Additional steps:** Expose workflow state as queryable metrics. Add health endpoints for ClickHouse materialized view lag.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=2, APP-Q3=2, APP-Q4=1 |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=2 but container definitions exist (Dockerfile, docker-compose.yml). App is already containerized. |
| 3 | Move to Open Source | Not Triggered | — | — | PostgreSQL and ClickHouse are already open-source engines. No commercial DB detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (all self-managed), DATA-Q3=3 (approaching but not EOL) |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium-High | INF-Q4=2 (self-managed Kafka), ClickHouse analytics with materialized views — data processing workloads exist |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=1, OPS-Q6=2 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Self-hosted privacy-focused web analytics.") |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:**
- **Architecture:** Single Next.js monolith (APP-Q2=2) serving web UI, REST API, tracker script, and analytics engine in one deployment unit. Identifiable modules exist (queries, lib, components, API routes) but all share the same process and deployment lifecycle.
- **Compute:** Self-hosted Docker container on raw VM/bare metal (INF-Q1=2). No managed orchestration.
- **Communication:** All communication is synchronous HTTP via Next.js API routes (APP-Q3=2). Kafka is available optionally but not used for inter-service communication.
- **Long-running Ops:** Data exports and complex ClickHouse aggregation queries run synchronously with no async job processing (APP-Q4=1).

**Recommended Decomposition:** See the Decomposition Strategy section below. The Strangler Fig approach is recommended, starting with extracting the event ingestion pipeline (`/api/send`) as an independent service backed by Amazon EventBridge and Amazon DynamoDB, followed by the analytics query engine.

**Representative AWS Services:** Lambda (event ingestion), API Gateway (API entry point — preferred per technology preferences), EventBridge (event routing — preferred), EKS (application workloads — preferred), DynamoDB (session cache — preferred), Step Functions (workflow orchestration).

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing (analytics events already follow this pattern), Hexagonal Architecture.

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **PostgreSQL:** Self-managed via `postgres:15-alpine` Docker image (`docker-compose.yml`). Single instance, no replication (except optional `DATABASE_REPLICA_URL` support in `src/lib/prisma.ts`), no automated backups, no failover.
- **ClickHouse:** Self-managed via external `CLICKHOUSE_URL`. No version pinning in the repository. Used for high-volume analytics event storage with materialized views.
- **Redis:** Optional self-managed cache via `REDIS_URL` (`src/lib/redis.ts`).

**Engine Versions:** PostgreSQL 15 pinned in docker-compose.yml (EOL expected Nov 2027 — not immediate risk). ClickHouse version not pinned in repository.

**Data Access Patterns:** Well-structured unified data access layer (`src/lib/db.ts`, `src/lib/prisma.ts`, `src/lib/clickhouse.ts`) with centralized query routing. Prisma ORM for PostgreSQL CRUD, raw SQL for analytics queries.

**Recommended Migration Targets (respecting technology preferences):**
- **PostgreSQL → Amazon Aurora PostgreSQL** (preferred): Multi-AZ, automated failover, point-in-time recovery, read replicas (already supported via `DATABASE_REPLICA_URL`). Aurora Serverless v2 for variable workloads.
- **ClickHouse → Amazon Timestream or self-managed ClickHouse on EKS**: ClickHouse has no direct AWS managed equivalent. Options: (a) Continue with ClickHouse on EKS (preferred container platform) with managed storage, or (b) Evaluate Amazon Timestream for time-series analytics if data model permits, or (c) Use Amazon Redshift Serverless for complex analytics queries.
- **Redis → Amazon ElastiCache or Amazon MemoryDB**: Managed Redis with automatic failover and backup.

**Migration Tools:** AWS DMS for PostgreSQL migration. Connection string update in environment variables is the primary application change.

**AWS Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium-High

**Current State:**
- **Streaming:** Optional self-managed Kafka (`kafkajs` in `src/lib/kafka.ts`) for event ingestion to ClickHouse. Kafka broker is self-managed (avoid per technology preferences).
- **Analytics Engine:** Self-managed ClickHouse with materialized views (`db/clickhouse/schema.sql`) for hourly aggregation (`website_event_stats_hourly`), revenue tracking (`website_revenue`), and projections for query optimization.
- **Data Processing:** ClickHouse materialized views perform continuous aggregation. No Glue, Athena, or managed ETL.

**Recommended Managed Analytics Targets (respecting preferences):**
- **Kafka → Amazon EventBridge** (preferred): Replace self-managed Kafka with EventBridge for event routing. The current Kafka usage is a simple producer pattern (`sendMessage` in `src/lib/kafka.ts`) that maps well to EventBridge event publishing.
- **ClickHouse analytics → Amazon Redshift Serverless or Amazon Athena + S3**: For complex analytics queries. Store raw events in S3 (data lake), query with Athena for ad-hoc analysis, use Redshift Serverless for dashboards requiring sub-second latency.
- **Real-time aggregation → Amazon Kinesis Data Streams + Lambda**: Replace ClickHouse materialized views with Kinesis for real-time event streaming and Lambda for aggregation.

**Representative AWS Services:** EventBridge (event routing — preferred), Kinesis Data Streams, Athena, Lake Formation, Redshift Serverless, S3 (data lake).

**AWS Prescriptive Guidance:** [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10=1):** Zero infrastructure-as-code. All infrastructure is manually configured Docker Compose (`docker-compose.yml`) or ad-hoc cloud setup. No Terraform, CloudFormation, CDK, or Helm charts.
- **CI/CD (INF-Q11=2):** GitHub Actions CI runs `pnpm test` and `pnpm build` on push. CD builds multi-arch Docker images on tag push to GHCR and Docker Hub. No automated deployment to any environment — deployment is manual (`docker compose pull && up`).
- **Deployment Strategy (OPS-Q5=1):** Direct-to-production via `docker compose up`. No blue/green, canary, or rolling deployments. No traffic shifting.
- **Integration Testing (OPS-Q6=2):** Cypress E2E tests exist (`cypress/e2e/` — 6 test files) but are NOT run in CI pipeline. Only Jest unit tests (3 files) run in CI.

**Recommended DevOps Toolchain (respecting preferences):**
1. **IaC:** AWS CDK (TypeScript — matches the application stack) or Terraform for infrastructure provisioning. Define VPC, EKS cluster, Aurora, ElastiCache, and supporting infrastructure in code.
2. **CI/CD Pipeline:** Extend GitHub Actions with deployment stages. Add AWS CodeDeploy for EKS deployments with blue/green strategy. Alternatively, use ArgoCD on EKS for GitOps-based deployment.
3. **Deployment Strategy:** Implement blue/green deployments for the application service on EKS. Use Helm charts for Kubernetes manifest management.
4. **Testing:** Integrate Cypress E2E tests into the CI pipeline. Add security scanning (see SEC-Q7 recommendations).

**Representative AWS Services:** CDK (IaC), CodeBuild, CodePipeline, CodeDeploy, EKS (preferred), CloudWatch, X-Ray.

**AWS Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

---

## Decomposition Strategy

APP-Q2 scored 2 — the application is a monolith with identifiable modules but shared state and a single deployment unit. This section provides concrete decomposition guidance.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2=2 — Umami has recognizable module boundaries (event ingestion, analytics queries, admin CRUD, web UI, tracker script) that can be extracted incrementally. | **Medium to High** — 6-18 months. Each extraction is bounded. | ✅ **Recommended.** Lowest risk, incremental value delivery, no big-bang cutover. Start with the event ingestion pipeline (`/api/send`) which has the clearest boundary and highest scalability need. |
| **Conditional / Adaptive** | Team has limited capacity (P2 priority). Containerize as-is (already done), then selectively extract high-value services based on business priority. | **Low to Medium** — Selective extraction over 3-12 months. | ✅ **Recommended given P2 priority.** Quick wins: deploy existing container to EKS, migrate PostgreSQL to Aurora, then selectively extract event ingestion. |
| **Big-Bang Rewrite** | Almost never — only when the monolith is unmaintainable. Umami has clean code structure and is actively maintained. | **Very High** — 12-24+ months. | ⚠️ **Not recommended.** The monolith is functional, well-structured, and actively maintained. Big-bang rewrite introduces unnecessary risk. |

### Recommended Extraction Order

1. **Event Ingestion Service** (`/api/send`, `/api/batch`): Highest throughput endpoint, clearest boundary. Receives tracking events from websites and writes to PostgreSQL/ClickHouse. Extract as a Lambda function or EKS service behind API Gateway, publishing events to EventBridge for downstream processing.
2. **Analytics Query Service** (`src/queries/sql/`): Read-heavy analytics queries against ClickHouse. Extract as a separate EKS service to scale independently from the CRUD API.
3. **Admin/CRUD API** (`src/app/api/users/`, `src/app/api/teams/`, `src/app/api/websites/`): User, team, and website management. Keep on EKS with Aurora PostgreSQL backend.
4. **Web UI** (`src/app/(main)/`): React/Next.js frontend. Can remain as-is, consuming the extracted API services.

### Pattern Recommendations

| Pattern | Purpose | Application to Umami |
|---------|---------|---------------------|
| **Anti-corruption Layer** | Isolate new services from monolith data model | Place ACL between extracted event ingestion service and the monolith's session management logic |
| **Event Sourcing** | Capture all changes as events | Analytics events already follow this pattern — ClickHouse stores raw events with materialized views for aggregation. Formalize this with EventBridge. |
| **Hexagonal Architecture** | Clear boundaries in new services | Structure the event ingestion service with ports (API Gateway input, EventBridge output) and adapters (DynamoDB session cache, Aurora PostgreSQL) |
| **Saga Pattern** | Distributed transactions | Apply when event ingestion involves multi-step operations (session creation → event storage → data aggregation) across separate services |

### Effort Estimation

| Factor | Assessment | Signal |
|--------|-----------|--------|
| Module boundaries | Clear package structure (`src/queries/`, `src/lib/`, `src/app/api/`) with identifiable modules | Medium effort |
| Data coupling | Two databases (PostgreSQL for CRUD, ClickHouse for analytics) — already partially separated. Shared `runQuery` routing in `src/lib/db.ts` | Medium effort |
| Stored procedures | None — all business logic in TypeScript application layer (DATA-Q4=3) | Low effort |
| Communication patterns | All synchronous HTTP (APP-Q3=2) — need to introduce async for event pipeline | Medium effort |
| CI/CD maturity | Basic CI exists but no deployment automation (INF-Q11=2) — pipeline needs extension for multi-service | Medium-High effort |
| Test coverage | Limited — 3 Jest unit tests, 6 Cypress E2E tests not in CI (OPS-Q6=2) — regression risk during extraction | Medium-High effort |

**Calibrated Estimate:** Given P2 priority and the Conditional/Adaptive approach, initial modernization (EKS deployment, Aurora migration, basic IaC) can be completed in 2-4 months. Selective service extraction over the following 6-12 months.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is containerized (Dockerfile with multi-stage Node.js Alpine build), runs via Docker Compose (`docker-compose.yml`), and supports Podman (`podman/podman-compose.yml`). Deployment targets include Netlify (`netlify.toml`) and Heroku (`app.json`). However, the primary self-hosted deployment model uses raw Docker containers with no managed orchestration (no ECS, EKS, Fargate, or Lambda). |
| **Gap** | No managed container orchestration or serverless compute. Self-hosted Docker Compose is the primary deployment model. |
| **Recommendation** | Deploy the application to Amazon EKS (preferred) with Fargate for serverless container execution. The existing Dockerfile and standalone Next.js output are EKS-ready. Create Helm charts for Kubernetes manifest management. |
| **Evidence** | `Dockerfile`, `docker-compose.yml`, `netlify.toml`, `app.json`, `podman/podman-compose.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. PostgreSQL runs as `postgres:15-alpine` via Docker Compose. ClickHouse is accessed via `CLICKHOUSE_URL` environment variable — self-managed externally. Redis is optional and self-managed via `REDIS_URL`. No IaC defines any managed database services (no `aws_rds_*`, `aws_dynamodb_*`, etc.). |
| **Gap** | All databases self-managed on Docker containers with no automated failover, backup, or scaling. |
| **Recommendation** | Migrate PostgreSQL to Amazon Aurora PostgreSQL (preferred) with Multi-AZ for automated failover and PITR. Evaluate Amazon Timestream or Redshift Serverless for analytics workloads currently on ClickHouse. Migrate Redis to Amazon ElastiCache. |
| **Evidence** | `docker-compose.yml` (postgres:15-alpine), `src/lib/prisma.ts` (DATABASE_URL), `src/lib/clickhouse.ts` (CLICKHOUSE_URL), `src/lib/redis.ts` (REDIS_URL) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) No dedicated workflow orchestration service (no Step Functions, Temporal, or equivalent). Multi-step operations are handled inline: event ingestion (`/api/send`) coordinates session creation, event storage, event data storage, and revenue tracking in a single synchronous handler. ClickHouse materialized views handle data aggregation automatically. Database migrations use Prisma Migrate. |
| **Gap** | Simple state machines in code with some structure (ClickHouse materialized views) but no dedicated orchestration service for multi-step business operations. |
| **Recommendation** | For the event ingestion pipeline, introduce AWS Step Functions to coordinate session creation → event storage → data aggregation as a managed workflow. This becomes critical during decomposition when these steps span multiple services. |
| **Evidence** | `src/app/api/send/route.ts` (multi-step event ingestion), `db/clickhouse/schema.sql` (materialized views), `prisma/migrations/` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) Self-managed Kafka (`kafkajs` in `package.json`, `src/lib/kafka.ts`) is available as an optional producer for event ingestion to ClickHouse. Kafka is enabled via `KAFKA_URL` and `KAFKA_BROKER` environment variables. The primary event path writes directly to PostgreSQL/ClickHouse without Kafka. Redis provides optional caching. For a stateful-crud service, managed messaging should be used for cross-service state changes. |
| **Gap** | Self-managed Kafka (when used) for event streaming. Primary path is synchronous direct database writes with no messaging. |
| **Recommendation** | Replace self-managed Kafka with Amazon EventBridge (preferred) for event routing. The current Kafka producer pattern (`sendMessage` in `src/lib/kafka.ts`) maps directly to EventBridge `PutEvents`. Avoid self-managed Kafka per technology preferences. |
| **Evidence** | `src/lib/kafka.ts`, `src/lib/db.ts` (runQuery routing), `package.json` (kafkajs dependency) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network configuration exists. No IaC defines any network resources. Docker Compose exposes port 3000 directly. The application relies on external reverse proxy (mentioned in README as nginx) for network security, but this is not configured in the repository. Content Security Policy headers are set in `next.config.ts` for browser-side security. |
| **Gap** | Services deployed without network isolation. No VPC, security groups, or network segmentation. Docker Compose exposes port directly. |
| **Recommendation** | Deploy to a VPC with private subnets for the application and database tiers. Use security groups with least-privilege rules. Place API Gateway (preferred) in front of the application for throttling and authentication. Use VPC endpoints for AWS service access. |
| **Evidence** | `docker-compose.yml` (ports: "3000:3000"), `next.config.ts` (CSP headers), `README.md` (mentions nginx reverse proxy) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or managed entry point. The Next.js application is exposed directly on port 3000. README recommends using nginx as a reverse proxy, but this is not configured in the repository. CORS headers are set in `next.config.ts` for all API routes. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, auth validation, or request validation at the entry point. |
| **Recommendation** | Place Amazon API Gateway (preferred) in front of the application for throttling, authentication, request validation, and WAF protection. Use CloudFront for static asset caching (tracker script, intl files, images). |
| **Evidence** | `docker-compose.yml` (direct port exposure), `next.config.ts` (CORS and rewrite rules), `README.md` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration. Docker Compose runs a single instance. No ASG, ECS service scaling, Lambda concurrency, or database auto-scaling. The application has no scaling mechanism for traffic spikes. |
| **Gap** | All capacity is statically provisioned as a single container instance. |
| **Recommendation** | Deploy to EKS (preferred) with Horizontal Pod Autoscaler (HPA) for compute scaling. Configure Aurora auto-scaling for read replicas. Set up DynamoDB on-demand capacity if migrating session cache. |
| **Evidence** | `docker-compose.yml` (single instance, no replicas) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration. PostgreSQL data persists on a Docker volume (`umami-db-data`) with no backup strategy. No `aws_backup_plan`, no `backup_retention_period`, no PITR configuration. ClickHouse backup is not addressed in the repository. |
| **Gap** | No backup configuration for any data store. A Docker volume failure would result in complete data loss. |
| **Recommendation** | Immediate: Implement PostgreSQL backup with `pg_dump` on a schedule. Target: Migrate to Aurora PostgreSQL (preferred) with automated backups, PITR, and cross-region replication for critical data. |
| **Evidence** | `docker-compose.yml` (volumes: umami-db-data, no backup config) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All resources run as single instances in Docker Compose. PostgreSQL is a single container. No Multi-AZ configuration. The Prisma client supports read replicas (`DATABASE_REPLICA_URL` in `src/lib/prisma.ts`), which shows HA awareness in the application code, but no replica infrastructure is defined. |
| **Gap** | Single-instance deployment. An instance failure takes down the entire application with no automatic recovery. |
| **Recommendation** | Deploy to EKS (preferred) across 2+ AZs. Use Aurora PostgreSQL with Multi-AZ for database HA. Configure Application Load Balancer with cross-zone load balancing. |
| **Evidence** | `docker-compose.yml` (single instance), `src/lib/prisma.ts` (DATABASE_REPLICA_URL support) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files found. No Terraform (`.tf`), CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. All infrastructure is defined in `docker-compose.yml` (Docker Compose is not IaC for cloud infrastructure) or manually created. |
| **Gap** | No IaC — all infrastructure is manually created (ClickOps). Environments are not reproducible. |
| **Recommendation** | Adopt AWS CDK (TypeScript — matches the application stack) to define all infrastructure: VPC, EKS cluster, Aurora PostgreSQL, ElastiCache, API Gateway, CloudWatch alarms, and backup plans. Start with the networking and database layers. |
| **Evidence** | Repository-wide search for `.tf`, `cdk.json`, `template.yaml`, `Chart.yaml` — none found. Only `docker-compose.yml` exists. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI (`.github/workflows/ci.yml`) runs `pnpm test` and `pnpm build` on every push. CD workflow (`.github/workflows/cd.yml`) builds multi-arch Docker images (linux/amd64, linux/arm64) on tag push and publishes to GHCR and Docker Hub. Cloud-specific CD (`.github/workflows/cd-cloud.yml`) builds images for cloud deployment. However, no automated deployment to any environment — only image building. |
| **Gap** | Build is automated but deployment is manual. No deployment stage in any pipeline. No automated rollback. |
| **Recommendation** | Extend GitHub Actions with a deployment stage using AWS CodeDeploy for EKS blue/green deployments. Add security scanning (Snyk, Trivy) and Cypress E2E tests to the CI pipeline. Implement automated rollback on deployment failure. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/cd-cloud.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript is the primary language with first-class AWS SDK coverage and broad cloud-native tooling. The application uses Next.js 15, React 19, and a modern TypeScript ecosystem (Zod for validation, Prisma ORM, TanStack Query). JavaScript is used for build scripts. |
| **Gap** | None — TypeScript is a Tier 1 language for AWS cloud-native development. |
| **Recommendation** | No action needed. Continue with TypeScript. Leverage `@aws-sdk` TypeScript packages when integrating with AWS services. |
| **Evidence** | `package.json` (TypeScript, Next.js 15, React 19), `tsconfig.json`, all `src/**/*.ts` and `src/**/*.tsx` files |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable Next.js application. All functionality — web UI (`src/app/(main)/`), REST API (`src/app/api/`), tracker script (`src/tracker/`), analytics engine (`src/queries/sql/`), and admin interface — resides in one codebase and one Docker image. Identifiable modules exist: Prisma queries (`src/queries/prisma/`) for CRUD, SQL queries (`src/queries/sql/`) for analytics, unified DB routing (`src/lib/db.ts`). Database separation exists (PostgreSQL for metadata, ClickHouse for analytics). However, all modules share the same process, deployment lifecycle, and Prisma client. |
| **Gap** | Monolith with identifiable modules but shared database access (via `src/lib/db.ts`), single deployment unit, and no independent scaling. |
| **Recommendation** | Apply the Strangler Fig pattern to extract high-value services incrementally. Start with the event ingestion pipeline (`/api/send`), which has the clearest boundary and highest independent scaling need. See Decomposition Strategy section. |
| **Evidence** | `Dockerfile` (single image), `docker-compose.yml` (single service), `src/lib/db.ts` (shared routing), `src/app/api/` (all API routes in one app) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) All API communication is synchronous HTTP via Next.js API routes. The application is a monolith with no inter-service communication. Kafka is available optionally as a producer for event ingestion (`src/lib/kafka.ts`) but is not used for cross-service state propagation. For stateful-crud, async should be available for key workflows — event ingestion to analytics is a cross-domain state change that would benefit from async decoupling. |
| **Gap** | Primarily synchronous with optional Kafka for background event processing. Event ingestion and analytics aggregation are tightly coupled via direct database writes. |
| **Recommendation** | Introduce EventBridge (preferred) for event-driven communication between the event ingestion path and the analytics aggregation path. This enables decoupling event collection from analytics processing and supports future service extraction. |
| **Evidence** | `src/app/api/send/route.ts` (synchronous handler), `src/lib/kafka.ts` (optional async), `src/lib/db.ts` (runQuery routing) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | (Archetype: stateful-crud) All operations are synchronous regardless of duration. The data export endpoint (`/api/websites/[websiteId]/export/route.ts`) generates CSV/JSON exports synchronously. Complex analytics queries (funnel, retention, journey, attribution reports in `src/queries/sql/reports/`) run synchronously against ClickHouse and could take significant time for large datasets. No async job framework, no background workers, no status polling patterns found. |
| **Gap** | All operations synchronous regardless of duration. Data exports and complex analytics queries risk timeout on large datasets. |
| **Recommendation** | Implement async job processing with status polling for long-running operations. Use AWS Step Functions for orchestrating export jobs and complex report generation. Return a job ID immediately and provide a status endpoint for polling. Consider SQS + Lambda for background processing. |
| **Evidence** | `src/app/api/websites/[websiteId]/export/route.ts`, `src/queries/sql/reports/` (complex queries), no background job framework in `package.json` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. All API routes use unversioned paths: `/api/users`, `/api/websites`, `/api/send`, `/api/auth/login`. No `/v1/` URL patterns, no `Accept-Version` headers, no versioning annotations. Breaking changes would affect all consumers simultaneously. |
| **Gap** | No versioning — breaking changes deployed directly to all consumers. |
| **Recommendation** | Implement URL-path versioning (`/api/v1/`) for all public API endpoints. The tracker script endpoint (`/api/send`) is particularly important to version as it's consumed by thousands of embedded scripts across client websites. |
| **Evidence** | `src/app/api/` directory structure (no version segments), `next.config.ts` (rewrites with no versioning) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single monolith with no inter-service communication. External dependencies (PostgreSQL, ClickHouse, Redis, Kafka) are configured via environment variables: `DATABASE_URL`, `CLICKHOUSE_URL`, `REDIS_URL`, `KAFKA_URL`, `KAFKA_BROKER`. No dynamic service discovery, but environment variables are appropriate for this monolithic architecture. |
| **Gap** | Environment variables for all endpoints with no dynamic discovery. This becomes a limitation when decomposing into multiple services. |
| **Recommendation** | Acceptable for current monolith. When decomposing, adopt AWS Cloud Map or EKS service discovery for dynamic service-to-service routing. API Gateway (preferred) can serve as a service catalog for external consumers. |
| **Evidence** | `src/lib/prisma.ts` (DATABASE_URL), `src/lib/clickhouse.ts` (CLICKHOUSE_URL), `src/lib/kafka.ts` (KAFKA_URL, KAFKA_BROKER), `src/lib/redis.ts` (REDIS_URL) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GeoIP data is stored locally — `scripts/build-geo.js` downloads MaxMind data to a local `geo/` directory. Internationalization files are stored as JSON in `public/intl/` (50+ locale files for countries, languages, messages). Static assets (browser/country/device/OS images) are stored in `public/images/`. No S3 or managed object storage is used. |
| **Gap** | Data in local filesystem storage, not managed object storage. GeoIP data, i18n files, and static assets are not in S3. |
| **Recommendation** | Store GeoIP data, static assets, and i18n files in Amazon S3. Use CloudFront for serving static assets. This enables independent scaling of static content delivery and removes storage dependency from the application container. |
| **Evidence** | `scripts/build-geo.js`, `public/intl/` (JSON locale files), `public/images/` (static assets), `.gitignore` (/geo — local storage) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-structured data access layer with centralized routing. `src/lib/db.ts` provides `runQuery()` which dispatches to Prisma (PostgreSQL), ClickHouse, or Kafka based on configuration. `src/lib/prisma.ts` provides centralized PostgreSQL access with `rawQuery`, `pagedQuery`, `parseFilters`. `src/lib/clickhouse.ts` mirrors the same pattern for ClickHouse. Prisma queries in `src/queries/prisma/` handle CRUD operations. SQL queries in `src/queries/sql/` handle analytics with consistent patterns for both PostgreSQL and ClickHouse. |
| **Gap** | Mostly centralized with some direct database-specific logic. ClickHouse SQL queries in `src/queries/sql/` contain ClickHouse-specific syntax (e.g., `formatDateTime`, `positionCaseInsensitive`, `LowCardinality`) alongside PostgreSQL-specific syntax (e.g., `to_char`, `ilike`). |
| **Recommendation** | Continue refining the data access layer. When migrating databases, the centralized routing in `src/lib/db.ts` minimizes the blast radius of connection string changes. Consider adding a query abstraction layer to reduce database-specific SQL duplication. |
| **Evidence** | `src/lib/db.ts` (runQuery routing), `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `src/queries/prisma/`, `src/queries/sql/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | PostgreSQL 15 is explicitly pinned in `docker-compose.yml` (`postgres:15-alpine`). PostgreSQL 15 EOL is November 2027 — approaching within 18 months but not imminent. ClickHouse version is not pinned in the repository (accessed via external `CLICKHOUSE_URL`). Prisma version pinned at `^6.18.0`. No documented version-update procedure. |
| **Gap** | PostgreSQL version pinned but approaching EOL window. ClickHouse version not pinned — deployment-dependent. No documented upgrade procedure. |
| **Recommendation** | Plan PostgreSQL upgrade path to version 16+ before November 2027. Pin ClickHouse version in deployment documentation. When migrating to Aurora PostgreSQL (preferred), Aurora manages engine version lifecycle with managed upgrades. |
| **Evidence** | `docker-compose.yml` (`postgres:15-alpine`), `src/lib/clickhouse.ts` (external URL), `package.json` (prisma: ^6.18.0) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No stored procedures, triggers, or functions in PostgreSQL. All PostgreSQL migrations (`prisma/migrations/`) contain standard DDL (CREATE TABLE, CREATE INDEX, ALTER TABLE). All business logic is in the TypeScript application layer. ClickHouse uses materialized views (`db/clickhouse/schema.sql` — `website_event_stats_hourly_mv`, `website_revenue_mv`) and projections — these are ClickHouse-specific aggregation constructs, not business logic. Raw SQL queries in `src/queries/sql/` use database-specific functions (PostgreSQL `to_char`, `ilike`; ClickHouse `formatDateTime`, `positionCaseInsensitive`). |
| **Gap** | Minimal proprietary constructs. ClickHouse materialized views and projections are vendor-specific and would need re-implementation if migrating away from ClickHouse. Database-specific SQL functions in query files. |
| **Recommendation** | The absence of stored procedures is a significant advantage for migration. ClickHouse materialized views can be replaced with Amazon Kinesis + Lambda for real-time aggregation, or Redshift materialized views. Database-specific SQL functions can be abstracted in the data access layer. |
| **Evidence** | `prisma/migrations/` (standard DDL), `db/clickhouse/schema.sql` (materialized views, projections), `src/queries/sql/` (database-specific SQL) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging. Application uses the `debug` npm package (`debug('umami:*')`) for development-level debug logging in `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `src/lib/kafka.ts`, and `src/lib/auth.ts`. The `LOG_QUERY` environment variable enables SQL query logging. No structured audit logging for security events (login attempts, permission changes, data access). |
| **Gap** | No CloudTrail or equivalent audit logging. No structured security event logging. |
| **Recommendation** | Enable AWS CloudTrail for API-level audit logging when deploying to AWS. Implement structured application-level audit logging for authentication events, permission changes, and sensitive data access. Use CloudWatch Logs with immutable log storage (S3 Object Lock). |
| **Evidence** | `src/lib/auth.ts` (debug logging), `src/lib/prisma.ts` (LOG_QUERY), `package.json` (debug dependency) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration. Self-managed PostgreSQL in Docker Compose has no encryption. No KMS keys, no encryption configuration in any file. Application-level encryption exists for JWT tokens (AES-256-GCM in `src/lib/crypto.ts`) and password hashing (bcryptjs in `src/lib/password.ts`), but database-level encryption at rest is absent. |
| **Gap** | No encryption at rest for any data store. |
| **Recommendation** | When migrating to Aurora PostgreSQL (preferred), encryption at rest is enabled by default with AWS-managed keys. Configure customer-managed KMS keys for sensitive data stores. Enable S3 default encryption for any object storage. |
| **Evidence** | `docker-compose.yml` (no encryption config), `src/lib/crypto.ts` (application-level encryption only) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Custom JWT-based authentication with AES-256-GCM encryption (`src/lib/crypto.ts`, `src/lib/jwt.ts`). Bearer token authentication on API endpoints via `parseRequest()` in `src/lib/request.ts`. The event collection endpoint (`/api/send`) intentionally skips auth (`skipAuth: true`) — by design for analytics tracking. Login uses username/password (`src/app/api/auth/login/route.ts`). Not standard OAuth2/OIDC — custom JWT implementation using `jsonwebtoken` library. Redis can be used for session storage (`src/lib/auth.ts`). |
| **Gap** | API key/static credential style authentication without standard OAuth2/OIDC. Custom JWT implementation instead of industry-standard identity protocols. |
| **Recommendation** | Integrate with Amazon Cognito for OAuth2/OIDC-based authentication. Use API Gateway (preferred) authorizers for token validation at the edge. Maintain `skipAuth` on `/api/send` for tracker script access but add API Gateway throttling and WAF protection. |
| **Evidence** | `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/lib/crypto.ts`, `src/lib/request.ts` (parseRequest with skipAuth), `src/app/api/auth/login/route.ts` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application manages its own authentication entirely. Login via username/password (`src/app/api/auth/login/route.ts`). SSO endpoint exists (`src/app/api/auth/sso/route.ts`) but it only creates auth tokens from existing authenticated sessions — it does not federate with external IdPs. No Cognito, Okta, OIDC, or SAML configuration. No external identity provider integration. |
| **Gap** | Application manages its own authentication with no external IdP integration. SSO endpoint does not actually integrate with external identity providers. |
| **Recommendation** | Integrate with Amazon Cognito as a centralized identity provider. Enable OIDC/SAML federation for enterprise SSO. This eliminates the need for custom password management and enables centralized access policies. |
| **Evidence** | `src/app/api/auth/login/route.ts` (custom login), `src/app/api/auth/sso/route.ts` (no external IdP), `src/lib/password.ts` (bcrypt password management) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets managed via environment variables. `APP_SECRET` used for JWT signing (`src/lib/crypto.ts`). Database credentials in `DATABASE_URL`, `CLICKHOUSE_URL`. Kafka credentials in `KAFKA_URL`. All configured via `.env` files (gitignored per `.gitignore`). Docker Compose `docker-compose.yml` contains a hardcoded placeholder `APP_SECRET: replace-me-with-a-random-string`. No Secrets Manager, no Vault, no rotation policy. |
| **Gap** | Secrets in environment variables with no dedicated secrets management. Docker Compose contains a hardcoded secret placeholder. No rotation. |
| **Recommendation** | Migrate secrets to AWS Secrets Manager with automated rotation. Use Secrets Manager for `APP_SECRET`, database credentials, Kafka credentials, and Redis credentials. Remove the hardcoded `APP_SECRET` placeholder from `docker-compose.yml`. |
| **Evidence** | `docker-compose.yml` (APP_SECRET placeholder), `src/lib/crypto.ts` (APP_SECRET usage), `.gitignore` (.env files excluded) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dockerfile uses `node:22-alpine` base image (slim Alpine Linux). Non-root user created (`adduser --system --uid 1001 nextjs`, `USER nextjs`). Multi-stage build reduces attack surface. However, no vulnerability scanning, no SSM Patch Manager, no hardened base images (CIS, Bottlerocket). No patching strategy documented. |
| **Gap** | Some hardening with non-root user and Alpine base, but no vulnerability scanning or patching strategy. |
| **Recommendation** | Add container image scanning with Amazon ECR + Inspector or Trivy in the CI/CD pipeline. Consider using AWS Bottlerocket for EKS node AMIs. Implement automated base image updates. |
| **Evidence** | `Dockerfile` (node:22-alpine, USER nextjs, multi-stage build) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CI pipeline (`.github/workflows/ci.yml`) runs only `pnpm test` and `pnpm build`. No SAST (SonarQube, Semgrep, CodeGuru), no DAST, no dependency scanning (no Dependabot config, no `npm audit`, no Snyk, no `.snyk` policy file). No container image scanning. Husky pre-commit hook runs `biome check` (linting/formatting, not security scanning). |
| **Gap** | No security scanning tools configured. Pipeline has no security validation step. |
| **Recommendation** | Add dependency scanning: configure Dependabot on the GitHub repository and add `pnpm audit` to the CI pipeline. Add SAST: integrate Semgrep or Amazon CodeGuru Reviewer. Add container scanning: use Trivy or ECR image scanning in the CD pipeline. Configure security gates that block on critical findings. |
| **Evidence** | `.github/workflows/ci.yml` (no security steps), `.husky/` (biome check only), no `.snyk`, no `dependabot.yml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No OpenTelemetry SDK, no X-Ray SDK, no trace ID propagation. Application uses `debug` npm package for debug-level logging (`debug('umami:prisma')`, `debug('umami:clickhouse')`, `debug('umami:kafka')`, `debug('umami:auth')`). No `traceparent` or `X-Amzn-Trace-Id` header propagation. Repository-wide search for "opentelemetry", "otel", "x-ray", "tracing" returned no results. |
| **Gap** | No distributed tracing. No visibility into request flows across PostgreSQL, ClickHouse, Redis, and Kafka. |
| **Recommendation** | Instrument with AWS X-Ray or OpenTelemetry. Add the `@opentelemetry/sdk-node` package with auto-instrumentation for Prisma, HTTP, and ClickHouse clients. Enable X-Ray tracing on API Gateway and EKS when deployed to AWS. |
| **Evidence** | `package.json` (no tracing dependencies), `src/lib/` (debug logging only), search for tracing-related terms found 0 results |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No CloudWatch alarms, no error budget tracking, no p99/p95 latency monitoring. No SLO configuration files. The only health check is in `docker-compose.yml` (`curl http://localhost:3000/api/heartbeat`) — a basic liveness probe, not an SLO. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. |
| **Recommendation** | Define SLOs for critical user journeys: event ingestion latency (p99 < 200ms), dashboard load time (p95 < 2s), API availability (99.9%). Implement with CloudWatch Synthetics and composite alarms. Track error budgets per SLO. |
| **Evidence** | `docker-compose.yml` (basic healthcheck only), `src/app/api/heartbeat/` (liveness endpoint) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom operational metrics publishing. No `cloudwatch.put_metric_data` or equivalent. The application generates analytics data for its users (pageviews, events, sessions, revenue) but does not publish metrics about its own operations (events ingested per second, query latency, active users, error rates by endpoint). A telemetry script exists (`scripts/telemetry.js`) but it's for Umami's own product telemetry, not operational metrics. |
| **Gap** | No custom metrics — only basic container-level metrics available via Docker. |
| **Recommendation** | Publish business outcome metrics: events ingested/second, unique sessions/hour, API error rate by endpoint, ClickHouse query latency, cache hit ratio. Use CloudWatch custom metrics with per-second resolution for real-time dashboards. |
| **Evidence** | `package.json` (no metrics libraries), `scripts/telemetry.js` (product telemetry only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configuration. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. No alert definitions in the repository. The Docker Compose healthcheck is the only monitoring. |
| **Gap** | No alerting configured. No anomaly detection. |
| **Recommendation** | Configure CloudWatch anomaly detection on event ingestion rate and API error rate. Set up composite alarms for critical paths. Integrate with PagerDuty or AWS SNS for incident notification. |
| **Evidence** | `docker-compose.yml` (healthcheck is only monitoring), no alarm definitions found |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment. CD workflow builds Docker images but does not deploy. Production deployment is manual: `docker compose pull && docker compose up --force-recreate`. No blue/green, canary, or rolling deployment. No traffic shifting. No CodeDeploy, Argo Rollouts, or Helm canary configuration. |
| **Gap** | Direct-to-production deployment with no staged rollout. All users impacted simultaneously by any regression. |
| **Recommendation** | Implement blue/green deployments on EKS (preferred) using ArgoCD Rollouts or AWS CodeDeploy. Use API Gateway canary releases for gradual traffic shifting. Feature flags for controlled rollout of new functionality. |
| **Evidence** | `.github/workflows/cd.yml` (build only, no deploy), `README.md` (manual docker compose up) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Jest unit tests exist (3 files: `src/lib/__tests__/charts.test.ts`, `detect.test.ts`, `format.test.ts`) and run in CI via `pnpm test`. Cypress E2E tests exist (6 files: `cypress/e2e/login.cy.ts`, `user.cy.ts`, `website.cy.ts`, `api-team.cy.ts`, `api-user.cy.ts`, `api-website.cy.ts`) covering login, CRUD operations. Cypress has Docker Compose support (`cypress/docker-compose.yml`). However, Cypress tests are NOT run in CI pipeline — `ci.yml` only runs `pnpm test` (Jest). |
| **Gap** | Integration tests exist but are not run consistently in CI. Only 3 unit tests run in CI. |
| **Recommendation** | Add Cypress E2E tests to the CI pipeline. Use the existing `cypress/docker-compose.yml` to spin up a test environment in CI. Expand test coverage to include analytics event ingestion, report generation, and ClickHouse query paths. |
| **Evidence** | `src/lib/__tests__/` (3 Jest tests), `cypress/e2e/` (6 Cypress tests), `.github/workflows/ci.yml` (only runs pnpm test), `cypress/docker-compose.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no Systems Manager Automation documents. No self-healing patterns. The Docker Compose `restart: always` policy provides basic container restart on crash. The healthcheck (`curl http://localhost:3000/api/heartbeat`) provides liveness detection. No structured incident response documentation. |
| **Gap** | No runbooks — incident response is entirely ad hoc. Only basic container restart on failure. |
| **Recommendation** | Create runbooks for common incidents: database connection failure, high event ingestion latency, ClickHouse out of disk space, memory pressure. Implement as AWS Systems Manager Automation documents when deployed to AWS. Add Lambda-based self-healing for common failure patterns. |
| **Evidence** | `docker-compose.yml` (restart: always, healthcheck), no runbook files found |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS for observability, no service-level dashboards, no named alarm owners. Debug logging exists across modules (`debug('umami:*')`) but no structured observability ownership. No team attribution on monitoring assets. No per-service dashboards. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. |
| **Recommendation** | Create per-service dashboards (event ingestion, analytics queries, admin CRUD). Define CODEOWNERS for observability configuration. Assign named owners to all alarms and SLOs. |
| **Evidence** | No CODEOWNERS file, no dashboard definitions, `src/lib/` (debug logging without ownership) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging. No IaC resources exist to tag. Docker Compose does not support tagging. No tagging standard, no `default_tags`, no `required-tags` Config rules. |
| **Gap** | No tags found on resources — no cost allocation, no ownership attribution. |
| **Recommendation** | When adopting IaC (CDK recommended), implement default tags on all resources: `Environment`, `Service`, `Team`, `CostCenter`. Enforce with AWS Config `required-tags` rules and Tag Policies in AWS Organizations. |
| **Evidence** | No IaC files, `docker-compose.yml` (no tagging support) |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `Dockerfile` | INF-Q1, INF-Q2, SEC-Q6 | Multi-stage Node.js Alpine build with non-root user; containerization evidence |
| `docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, SEC-Q5, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q7, OPS-Q9 | Primary deployment definition; postgres:15-alpine; port exposure; healthcheck; restart policy; hardcoded APP_SECRET placeholder |
| `.github/workflows/ci.yml` | INF-Q11, SEC-Q7, OPS-Q6 | CI pipeline: pnpm test + pnpm build on push; no security scanning; no Cypress E2E |
| `.github/workflows/cd.yml` | INF-Q11, OPS-Q5 | CD pipeline: Docker image build on tags to GHCR/Docker Hub; no deployment stage |
| `.github/workflows/cd-cloud.yml` | INF-Q11 | Cloud-specific Docker build for cloud deployment |
| `prisma/schema.prisma` | INF-Q2, DATA-Q2, DATA-Q4, APP-Q2 | PostgreSQL data model with 12 entities; Prisma ORM configuration |
| `prisma/migrations/` | INF-Q3, DATA-Q3, DATA-Q4 | 14 PostgreSQL migration files; standard DDL; no stored procedures |
| `db/clickhouse/schema.sql` | INF-Q4, DATA-Q4, APP-Q2 | ClickHouse analytics schema; materialized views; projections |
| `db/clickhouse/migrations/` | DATA-Q3, DATA-Q4 | 8 ClickHouse migration files |
| `src/lib/db.ts` | INF-Q3, INF-Q4, APP-Q2, APP-Q3, DATA-Q2 | Unified query routing (Prisma/ClickHouse/Kafka) |
| `src/lib/prisma.ts` | INF-Q2, INF-Q9, DATA-Q2, SEC-Q1 | PostgreSQL access layer; read replica support; query logging |
| `src/lib/clickhouse.ts` | INF-Q2, INF-Q4, DATA-Q2, SEC-Q1 | ClickHouse access layer; raw query execution |
| `src/lib/kafka.ts` | INF-Q4, APP-Q3 | Optional Kafka producer for event ingestion |
| `src/lib/redis.ts` | INF-Q2, INF-Q4, SEC-Q4 | Optional Redis client for caching/session storage |
| `src/lib/auth.ts` | SEC-Q1, SEC-Q3, SEC-Q4 | Bearer token authentication; Redis session support; debug logging |
| `src/lib/jwt.ts` | SEC-Q3 | JWT token creation/parsing with encryption |
| `src/lib/crypto.ts` | SEC-Q2, SEC-Q3, SEC-Q5 | AES-256-GCM encryption; APP_SECRET usage; hash functions |
| `src/lib/request.ts` | SEC-Q3 | Request parsing with skipAuth option; Zod validation |
| `src/app/api/send/route.ts` | INF-Q3, APP-Q2, APP-Q3, APP-Q4 | Event ingestion endpoint; multi-step processing; synchronous handler |
| `src/app/api/auth/login/route.ts` | SEC-Q3, SEC-Q4 | Custom username/password authentication |
| `src/app/api/auth/sso/route.ts` | SEC-Q4 | SSO endpoint without external IdP integration |
| `src/app/api/` | APP-Q2, APP-Q5, APP-Q6 | All API routes in single application; no versioning |
| `src/queries/prisma/` | DATA-Q2, APP-Q2 | Prisma CRUD queries; centralized PostgreSQL access |
| `src/queries/sql/` | DATA-Q2, APP-Q4, DATA-Q4 | Raw SQL analytics queries; database-specific functions |
| `src/queries/sql/reports/` | APP-Q4 | Complex analytics queries (funnel, retention, journey, attribution) |
| `src/lib/__tests__/` | OPS-Q6 | 3 Jest unit test files (charts, detect, format) |
| `cypress/e2e/` | OPS-Q6 | 6 Cypress E2E tests (login, user, website, API CRUD) |
| `cypress/docker-compose.yml` | OPS-Q6 | Cypress test environment definition |
| `next.config.ts` | INF-Q5, INF-Q6, APP-Q5 | CSP headers; CORS config; rewrites; no versioning |
| `package.json` | APP-Q1, INF-Q4, OPS-Q1 | TypeScript/Next.js stack; kafkajs; debug; no tracing dependencies |
| `README.md` | INF-Q5, INF-Q6, OPS-Q5 | Setup instructions; nginx proxy mention; manual deployment guide |
| `netlify.toml` | INF-Q1 | Netlify deployment support |
| `app.json` | INF-Q1 | Heroku deployment support with heroku-postgresql addon |
| `scripts/build-geo.js` | DATA-Q1 | GeoIP data download to local filesystem |
| `.gitignore` | SEC-Q5 | .env files properly excluded from version control |
| `podman/podman-compose.yml` | INF-Q1 | Alternative container runtime support |
| `src/lib/password.ts` | SEC-Q4 | bcrypt password hashing — custom password management |
| `scripts/telemetry.js` | OPS-Q3 | Product telemetry, not operational metrics |
| `src/app/api/heartbeat/` | OPS-Q2, OPS-Q7 | Basic liveness endpoint |




