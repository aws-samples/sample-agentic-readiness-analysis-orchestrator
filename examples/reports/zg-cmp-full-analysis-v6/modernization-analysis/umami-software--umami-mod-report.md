# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | umami-software--umami |
| **Date** | 2026-05-08 |
| **TD Version** | modernization-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, analytics, web-app |
| **Context** | Self-hosted privacy-focused web analytics. |
| **Overall Score** | 1.71 / 4.0 |

**Archetype Justification**: The application owns persistent state (PostgreSQL via Prisma ORM, ClickHouse for analytics), exposes CRUD operations on business entities (users, websites, teams, sessions, events), and manages entity lifecycle (soft deletes, timestamps). Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false

**Classification Tier**: 🟠 Remediation Required

**Classification Rationale**: This repo has 9 High findings, 23 Medium findings, 3 Low findings. Rule matched: "2-11 High → Remediation Required". Note: Unlike the Agentic Readiness Analysis (ARA) where 1 High finding is an agent-deployment gate (maps to "Remediation Required"), the MOD classification treats 1 High as "Pilot-Ready" because a single modernization gap is typically not a deployment blocker — it represents one area needing improvement rather than a safety concern. MOD's threshold for Remediation Required is 2-11 High findings, reflecting that multiple concurrent modernization gaps warrant structured remediation before proceeding.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.71 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+2+2+1+1+1+1+1+1+2) / 11 = 14/11 = 1.27
- APP: (4+2+2+2+1+1) / 6 = 12/6 = 2.00
- DATA: (1+3+3+4) / 4 = 11/4 = 2.75
- SEC: (1+1+3+1+2+1+1) / 7 = 10/7 = 1.43
- OPS: (1+1+1+1+1+2+1+1+1) / 9 = 10/9 = 1.11
- Overall: (1.27+2.00+2.75+1.43+1.11) / 5 = 8.56/5 = 1.71

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — all infrastructure would be manually created (ClickOps) | Cannot reproduce environments, no disaster recovery, blocks all modernization pathways |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute defined — only Docker Compose for local/self-hosted deployment | No auto-scaling, no managed orchestration, manual capacity management |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured | No forensic capability, compliance risk, incident investigation impossible |
| 4 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing — only basic debug-level logging | Cannot diagnose performance issues or trace requests across services |
| 5 | INF-Q2: Managed Databases | 1 | Database is self-managed PostgreSQL in Docker with no managed service configuration | Manual patching, no automated failover, no PITR, single point of failure |

---

## Quick Agent Wins

No Quick Agent Wins identified. The system lacks the foundational capabilities needed to support agent integration:
- No API documentation (APP-Q5 = 1) — no OpenAPI spec for agent tool discovery
- No CI/CD automation beyond basic build/test (INF-Q11 = 2) — pipeline exists but lacks deployment automation
- No structured logging or tracing (OPS-Q1 = 1) — no observability data for agent correlation

Address the gaps identified in this analysis before pursuing agent opportunities.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Not Triggered | — | — | Dockerfile and docker-compose.yml exist; contextual guard: application already containerized |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected (PostgreSQL is open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1, DATA-Q3=3 |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4=2 (self-managed Kafka); data processing workloads exist (ClickHouse analytics, event streaming) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=1, OPS-Q6=2 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:**
- The application is a monolithic Next.js full-stack application (APP-Q2=2) with identifiable modules (queries, permissions, components) but tightly coupled through shared database schemas and a single deployable unit.
- Compute is self-managed Docker containers with no cloud-native orchestration (INF-Q1=1).
- Communication is primarily synchronous HTTP with Kafka available as an optional streaming layer (APP-Q3=2).
- Long-running operations (analytics queries, event processing) are handled synchronously within request handlers (APP-Q4=2).

**Recommended Decomposition Approach:**
- Extract the analytics event ingestion pipeline as a separate service (high write volume, different scaling requirements).
- Extract the reporting/query engine as a read-optimized service.
- Keep the admin/management API as the core service.

**Representative AWS Services:** EKS (preferred per user preferences), API Gateway, EventBridge, Aurora PostgreSQL, Amazon Managed Service for Apache Flink (for streaming analytics).

**Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing for analytics events.

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- PostgreSQL is self-managed in Docker containers (INF-Q2=1) with no automated failover, PITR, or managed backups.
- ClickHouse is optionally used for OLAP analytics but also self-managed.
- Redis is used for caching but self-managed.
- Database engine version pinned to PostgreSQL 15 in docker-compose.yml (DATA-Q3=3).

**Recommended Migration Targets (respecting preferences):**
- PostgreSQL → **Aurora PostgreSQL** (preferred: aurora) — provides automated failover, PITR, read replicas, and auto-scaling storage.
- ClickHouse → **Amazon Managed Service for Apache Flink** or retain ClickHouse on EKS with managed storage.
- Redis → **Amazon ElastiCache for Redis** or **Amazon MemoryDB** for caching layer.

**Migration Tools:** AWS DMS for data migration, Prisma ORM abstracts connection strings making switchover straightforward.

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:**
- Self-managed Kafka (via KafkaJS) for event streaming (INF-Q4=2).
- ClickHouse for OLAP analytics queries — self-managed.
- Data pipeline from event ingestion → Kafka → ClickHouse is application-managed.
- Multiple data sources (PostgreSQL for CRUD, ClickHouse for analytics, Redis for cache) with a partially unified access layer.

**Recommended Migration Targets (respecting preferences):**
- Self-managed Kafka → **Amazon MSK** or **EventBridge** (preferred: eventbridge) for event streaming.
- ClickHouse analytics → Consider **Amazon Redshift Serverless** or **Amazon Athena** for analytics queries, OR retain ClickHouse on EKS.
- Event pipeline → **EventBridge** + **Kinesis Data Streams** for real-time ingestion.

**Note:** User preference is to avoid self-managed-kafka, which aligns with moving to MSK or EventBridge.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- No Infrastructure as Code (INF-Q10=1) — all infrastructure is manually provisioned.
- CI/CD pipeline exists for build and test (GitHub Actions) but deployment to production is not automated (INF-Q11=2).
- Direct-to-production deployment with no staged rollout (OPS-Q5=1).
- E2E tests exist (Cypress) but are not consistently run in CI pipeline (OPS-Q6=2).

**Recommended DevOps Toolchain:**
- IaC: **Terraform** or **CDK** for defining EKS clusters, Aurora, ElastiCache, networking.
- CI/CD: Extend GitHub Actions with deployment stages, or adopt **AWS CodePipeline** + **CodeBuild**.
- Deployment: **ArgoCD** on EKS for GitOps-based deployments with canary rollouts.
- Testing: Integrate Cypress E2E tests as a deployment gate.

**Representative AWS Services:** CodePipeline, CodeBuild, CDK, EKS + ArgoCD, CloudFormation.

---

## Decomposition Strategy

*(Included because APP-Q2 < 3)*

### Recommended Approach: Strangler Fig (Parallel Track)

The application has identifiable modules (event ingestion, analytics queries, CRUD management, reporting) with coupling primarily through the shared PostgreSQL database. This makes incremental extraction feasible.

**Approach Options:**

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2=2 — modules are identifiable but coupled through shared DB | Medium to High | ✅ **Recommended.** Extract high-volume event ingestion first, then reporting. |
| **Conditional / Adaptive** | If team capacity is limited | Low to Medium | ✅ Alternative: Containerize on EKS first, then selectively extract. |
| **Big-Bang Rewrite** | — | Very High | ⚠️ Not recommended. The monolith is functional and maintainable. |

**Recommended Extraction Order:**
1. **Event Ingestion Service** — High write volume, distinct scaling needs, already partially decoupled via Kafka integration.
2. **Analytics Query Service** — Read-heavy ClickHouse queries, can be independently scaled.
3. **Core Management API** — Remains as the primary service for CRUD operations on users/websites/teams.

**Pattern Recommendations:**

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate new services from monolith's Prisma data model | Every extraction — place ACL between new service and shared DB |
| **Saga Pattern** | Manage distributed transactions (e.g., website creation + event tracking setup) | When extracting event ingestion from core CRUD |
| **Event Sourcing** | Capture all analytics events as immutable event stream | Event ingestion service — already aligned with current Kafka usage |
| **Hexagonal Architecture** | Structure each new service with clear boundaries | Every new service — ensures testability and portability |

**Effort Estimation Factors:**

| Factor | Analysis | Signal |
|--------|-----------|--------|
| Module boundaries | Clear query separation (prisma/ vs sql/), permissions layer | Low-Medium effort |
| Data coupling | Single shared PostgreSQL + optional ClickHouse | Medium effort (need per-service schemas) |
| Stored procedures | None (DATA-Q4=4) | Low effort |
| Communication patterns | Mostly sync with optional Kafka | Medium effort |
| CI/CD maturity | Basic pipeline, no deployment automation | Medium effort (need to build deployment pipeline first) |
| Test coverage | Minimal (3 unit tests, 6 E2E tests) | High risk during extraction |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is defined as self-managed Docker containers via docker-compose.yml. No AWS managed compute (ECS, EKS, Lambda, Fargate) is configured. The Dockerfile builds a Next.js standalone application on node:22-alpine, exposed on port 3000. The CD pipeline builds and pushes multi-arch Docker images to GHCR and Docker Hub, but no deployment to managed compute is defined. |
| **Gap** | No managed container orchestration or serverless deployment. The application runs on self-managed Docker hosts with no auto-scaling, health-based routing, or managed orchestration. |
| **Recommendation** | Deploy on Amazon EKS (preferred) with Fargate profiles for the application workload. Define Kubernetes Deployment manifests with health checks, resource limits, and HPA for auto-scaling. |
| **Evidence** | `docker-compose.yml`, `Dockerfile`, `.github/workflows/cd.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | PostgreSQL 15 is self-managed in Docker (`postgres:15-alpine` in docker-compose.yml). ClickHouse, Redis, and Kafka are all configured via environment variables pointing to self-managed instances. No AWS managed database resources (RDS, Aurora, DynamoDB, ElastiCache) are defined in any IaC or deployment configuration. |
| **Gap** | All databases are self-managed with no automated failover, no PITR, manual patching, and no managed backups. Single point of failure for all data stores. |
| **Recommendation** | Migrate PostgreSQL to Aurora PostgreSQL (preferred). Migrate Redis to Amazon ElastiCache. Consider Amazon MSK for Kafka replacement. |
| **Evidence** | `docker-compose.yml` (postgres:15-alpine), `src/lib/clickhouse.ts`, `src/lib/redis.ts`, `src/lib/kafka.ts` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has multi-step operations: event ingestion (receive → validate → store in PostgreSQL → optionally forward to Kafka → insert into ClickHouse), report generation (multi-query aggregation), and data migrations. These workflows are implemented as sequential application code with no dedicated orchestration service. Build scripts use npm-run-all for multi-step build orchestration. |
| **Gap** | No dedicated workflow orchestration (Step Functions, Temporal) for business-critical multi-step operations. All workflow logic is hardcoded in application code. |
| **Recommendation** | For the event ingestion pipeline and report generation workflows, consider AWS Step Functions to manage retry logic, error handling, and state transitions. This becomes more critical as services are decomposed. |
| **Evidence** | `package.json` (npm-run-all scripts), `src/queries/sql/events/saveEvent.ts`, `src/lib/kafka.ts` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kafka (via KafkaJS) is implemented for event streaming but is self-managed — configured via `KAFKA_URL` and `KAFKA_BROKER` environment variables with application-level connection management. Redis is available for caching. No managed messaging services (SQS, SNS, EventBridge, MSK) are configured. The Kafka integration is optional (enabled only when env vars are set). |
| **Gap** | Self-managed Kafka for cross-service event flows. No managed messaging infrastructure. The Kafka client includes manual connection management, timeout handling, and error serialization — operational overhead that managed services eliminate. |
| **Recommendation** | Migrate from self-managed Kafka to Amazon MSK Serverless or EventBridge (preferred per user preferences). EventBridge provides native AWS integration for event-driven patterns without broker management. |
| **Evidence** | `src/lib/kafka.ts` (KafkaJS client with self-managed connection), `package.json` (kafkajs dependency) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists. The docker-compose.yml exposes port 3000 directly. No network policies, no private subnet isolation, no security groups defined. The application has CORS configured (Access-Control-Allow-Origin: *) with no network-level access control. |
| **Gap** | No network security — services would be deployed without VPC isolation, private subnets, or least-privilege security groups. CORS allows all origins. |
| **Recommendation** | Deploy within a VPC with private subnets for application and database tiers. Define security groups with least-privilege rules. Use VPC endpoints for AWS service access. Restrict CORS to known domains. |
| **Evidence** | `docker-compose.yml` (port 3000 exposed), `next.config.ts` (Access-Control-Allow-Origin: *) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or load balancer is configured. The Next.js application serves directly on port 3000 with no managed entry point providing throttling, authentication, or request validation at the infrastructure level. API authentication and validation are handled at the application level only. |
| **Gap** | No managed API entry point. Direct service exposure without infrastructure-level throttling, DDoS protection, or traffic management. |
| **Recommendation** | Deploy behind an Application Load Balancer (ALB) for health checks and routing, or use API Gateway (preferred per user preferences) for throttling, authentication offloading, and request validation. Consider CloudFront for global edge caching of the tracker script and static assets. |
| **Evidence** | `docker-compose.yml` (direct port exposure), absence of any load balancer or gateway configuration |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The docker-compose.yml defines a single instance with no scaling mechanism. No ASG, ECS service scaling, HPA, or Lambda concurrency configuration found. |
| **Gap** | All capacity is statically provisioned. Cannot respond to traffic spikes (common for analytics — traffic correlates with client website traffic patterns). |
| **Recommendation** | Implement Kubernetes HPA on EKS based on request rate and CPU/memory. Configure Aurora auto-scaling for read replicas during peak query periods. |
| **Evidence** | `docker-compose.yml` (single instance), absence of any scaling configuration |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. The PostgreSQL container uses a Docker volume (`umami-db-data`) with no backup automation, no retention policy, no PITR, and no restore procedures. No AWS Backup plans, no S3 backup targets, no EBS snapshot policies. |
| **Gap** | No automated backups. Data loss event would result in complete loss of analytics data with no recovery path. |
| **Recommendation** | Aurora PostgreSQL provides automated backups with 35-day retention and PITR by default. For immediate improvement, implement pg_dump scheduled backups to S3 with lifecycle policies. |
| **Evidence** | `docker-compose.yml` (Docker volume with no backup), absence of any backup configuration |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment. The docker-compose.yml defines single instances of both the application and PostgreSQL with no redundancy. No load balancer, no database replication, no cross-AZ configuration. A single-AZ failure would take down the entire analytics platform. |
| **Gap** | All resources in a single deployment with no fault isolation. No AZ configuration found. |
| **Recommendation** | Deploy on EKS across 2+ AZs with Aurora PostgreSQL Multi-AZ for automated database failover. Configure ALB with cross-zone load balancing. |
| **Evidence** | `docker-compose.yml` (single instance per service), absence of any HA configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code found. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. All infrastructure deployment would be manually created. The only deployment artifacts are Dockerfile and docker-compose.yml for local/self-hosted development. |
| **Gap** | 0% IaC coverage. Infrastructure changes are manual, non-reproducible, and not version-controlled. Cannot recreate environments, perform disaster recovery, or audit infrastructure changes. |
| **Recommendation** | Adopt Terraform or CDK (preferred approach for TypeScript teams) to define EKS cluster, Aurora PostgreSQL, ElastiCache, networking, and security configuration. Start with the compute and database layer. |
| **Evidence** | Absence of any .tf, .cfn.yaml, cdk.json, Chart.yaml, or kustomization.yaml files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI pipeline exists with build and test stages (`.github/workflows/ci.yml`). CD pipeline builds and pushes Docker images to GHCR and Docker Hub on tag push (`.github/workflows/cd.yml`). However, no deployment automation exists — images are built and pushed but not deployed to any environment. No infrastructure deployment pipeline. No automated rollback. |
| **Gap** | Build is automated but deployment is manual. No continuous deployment to any environment. No IaC pipeline. No automated rollback capability. |
| **Recommendation** | Extend GitHub Actions (or adopt AWS CodePipeline) with deployment stages that deploy to EKS via ArgoCD or Helm. Add staging environment with automated smoke tests before production promotion. |
| **Evidence** | `.github/workflows/ci.yml` (build + test), `.github/workflows/cd.yml` (image build + push only) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript 5.9+ with Node.js 22 (Alpine) runtime. Modern framework stack: Next.js 15 (App Router), React 19, Prisma 6 ORM, Zod 4 validation. Package manager: pnpm. Build tooling: Rollup, tsup, Biome (linter/formatter). This is a fully modern cloud-native language stack with first-class AWS SDK coverage and mature ecosystem. |
| **Gap** | N/A — language and framework stack is modern and current. |
| **Recommendation** | N/A — no language or framework modernization needed. The TypeScript/Node.js stack has excellent AWS SDK support (@aws-sdk/*). |
| **Evidence** | `package.json` (typescript ^5.9.3, next ^15.5.9, react ^19.2.3, prisma ^6.18.0, zod ^4.1.13), `Dockerfile` (node:22-alpine) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit (one Dockerfile, one Next.js application) serving both the frontend UI and 77 backend API routes. The codebase has identifiable modules: `src/queries/prisma/` (CRUD), `src/queries/sql/` (analytics), `src/permissions/` (RBAC), `src/components/` (UI). However, these modules share the same PostgreSQL database schema through Prisma, have direct cross-module data access, and are deployed as a single process. |
| **Gap** | Monolith with identifiable modules but shared database schemas and a single deployment unit. Cannot independently scale the high-volume event ingestion vs the low-volume admin API. Cannot deploy changes to analytics independently from the management UI. |
| **Recommendation** | Begin Strangler Fig decomposition: extract event ingestion (high-write, scaling-sensitive) as the first independent service, followed by the analytics query engine. See Decomposition Strategy section. |
| **Evidence** | Single `Dockerfile`, single `docker-compose.yml` service, `prisma/schema.prisma` (shared schema), `src/app/api/` (77 route handlers in one deployment) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is primarily synchronous — all 77 API routes handle requests synchronously. Kafka is available as an optional async path for event ingestion (`src/lib/kafka.ts`) but is not the default and requires explicit configuration. When Kafka is disabled (the default), event writes go directly to the database synchronously. No other async patterns (SQS, EventBridge, pub/sub) are used for cross-module communication. |
| **Gap** | Primarily synchronous with some async available for background event processing. The analytics write path (high volume) benefits from async but defaults to synchronous. State changes (user creation, website updates) are fully synchronous with no event emission for other modules to react to. |
| **Recommendation** | Adopt EventBridge (preferred) for state change events (website created, user updated) to enable decoupled reactions. Move event ingestion to a fully async path via managed streaming (MSK or EventBridge). |
| **Evidence** | `src/lib/kafka.ts` (optional async), `src/app/api/` routes (synchronous handlers), absence of SQS/SNS/EventBridge usage |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Analytics queries (funnel analysis, journey reports, retention reports, attribution) can be long-running depending on data volume. These are executed synchronously within request handlers (`src/queries/sql/reports/`). The ClickHouse queries for large date ranges with complex aggregations may exceed 30 seconds. No background job framework, no status polling, no async job processing exists. |
| **Gap** | Some background job processing patterns exist (Kafka for event ingestion) but reporting queries are fully synchronous with no timeout protection or async fallback. |
| **Recommendation** | Implement async report generation: accept report request → return job ID → process in background (Step Functions or EKS job) → poll for status. This is critical for funnel, journey, and attribution reports on large datasets. |
| **Evidence** | `src/queries/sql/reports/` (getFunnel.ts, getJourney.ts, getRetention.ts, getAttribution.ts — all synchronous), absence of job queue or status polling patterns |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. All 77 API routes are at `/api/{resource}` with no version prefix (/v1/, /v2/), no version headers, and no versioning annotations. No changelog file for API changes. Breaking changes would affect all consumers simultaneously. |
| **Gap** | No versioning — breaking changes deployed directly. The tracker script (`/script.js`) is consumed by thousands of client websites and has no version negotiation. |
| **Recommendation** | Implement URL-based versioning (/api/v1/) for the management API. For the tracker script, implement a version negotiation mechanism or maintain backward compatibility guarantees with semantic versioning. |
| **Evidence** | `src/app/api/` (no version prefix in route paths), `next.config.ts` (rewrites without versioning), absence of API changelog |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All service endpoints are configured via environment variables with hard-coded connection strings: `DATABASE_URL`, `CLICKHOUSE_URL`, `REDIS_URL`, `KAFKA_URL`, `KAFKA_BROKER`. No service discovery mechanism (Consul, AWS Service Discovery, Kubernetes DNS) is used. No API catalog or service registry exists. |
| **Gap** | All service endpoints hard-coded in environment variables. No dynamic discovery, no health-based routing, no service mesh. |
| **Recommendation** | When deploying on EKS, leverage Kubernetes DNS-based service discovery. For cross-service communication after decomposition, use AWS Cloud Map or EKS-native service discovery. |
| **Evidence** | `podman/env.sample` (hard-coded URLs), `src/lib/clickhouse.ts` (process.env.CLICKHOUSE_URL), `src/lib/redis.ts` (process.env.REDIS_URL), `src/lib/kafka.ts` (process.env.KAFKA_URL) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 or managed object storage is used. GeoIP data is stored as local files (built via `scripts/build-geo.js` downloading MaxMind databases). The tracker script is served from the local filesystem. Locale/translation files are stored in `public/intl/`. No document parsing or extraction pipelines exist. |
| **Gap** | Data on local file systems. GeoIP databases, tracker scripts, and locale files are bundled into the Docker image rather than served from managed object storage. No S3 usage detected. |
| **Recommendation** | Store GeoIP databases, tracker script bundles, and static assets in S3 with CloudFront distribution. This enables independent updates without redeployment and provides better cache control. |
| **Evidence** | `scripts/build-geo.js` (local GeoIP file), `public/intl/` (local translation files), absence of S3 configuration |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a well-structured data access layer. CRUD operations use Prisma ORM with centralized query files in `src/queries/prisma/` (user.ts, website.ts, team.ts, etc.). Analytics queries are centralized in `src/queries/sql/` with a dual-database abstraction that routes to either PostgreSQL or ClickHouse based on configuration. The `src/lib/` directory provides centralized database client initialization (prisma.ts, clickhouse.ts, redis.ts, kafka.ts). |
| **Gap** | Mostly centralized but the dual-database abstraction (PostgreSQL vs ClickHouse) adds complexity. Some query logic is tightly coupled to the specific database engine (ClickHouse-specific SQL in `src/lib/clickhouse.ts`). |
| **Recommendation** | Maintain the existing centralized pattern. When decomposing services, ensure each service owns its data access layer with clear API boundaries rather than sharing the Prisma client across services. |
| **Evidence** | `src/queries/prisma/` (9 CRUD query files), `src/queries/sql/` (40+ analytics query files), `src/lib/prisma.ts`, `src/lib/clickhouse.ts` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | PostgreSQL 15 is explicitly pinned in docker-compose.yml (`postgres:15-alpine`). PostgreSQL 15 is supported until November 2027 — not approaching EOL but not the latest major version (PostgreSQL 16/17 are current). ClickHouse version is not pinned in the application — it's configured via URL. Prisma version is pinned at ^6.18.0. The Dockerfile pins Prisma at 6.19.0. |
| **Gap** | PostgreSQL version pinned but approaching the 12-month EOL window within the next year. ClickHouse version is not explicitly managed. No documented version-update procedure. |
| **Recommendation** | Document a database version update procedure. Plan upgrade to PostgreSQL 16+ when migrating to Aurora. Explicitly pin ClickHouse version in deployment configuration. |
| **Evidence** | `docker-compose.yml` (postgres:15-alpine), `Dockerfile` (PRISMA_VERSION="6.19.0"), `package.json` (@prisma/client ^6.18.0) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs detected. All business logic resides in the application layer (TypeScript). Database migrations in `prisma/migrations/` use standard DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX) without stored procedures. ClickHouse migrations in `db/clickhouse/migrations/` also use standard DDL. The application uses Prisma ORM for CRUD and parameterized SQL queries for analytics — no proprietary SQL dialects. |
| **Gap** | N/A — no stored procedures or proprietary SQL. All business logic in application layer. |
| **Recommendation** | N/A — this is the ideal state for database modernization. The absence of stored procedures makes migration to Aurora PostgreSQL straightforward. |
| **Evidence** | `prisma/migrations/` (14 migration files — standard DDL), `db/clickhouse/migrations/` (8 migration files — standard DDL), `src/queries/sql/` (parameterized SQL, no stored procedures) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configured. No IaC defines audit log infrastructure. Application-level logging uses the `debug` npm package with namespaces (`umami:auth`, `umami:prisma`, `umami:clickhouse`, `umami:kafka`) but this is development-level debug logging, not production audit logging. No structured audit trail for administrative actions (user creation, permission changes, data deletion). |
| **Gap** | No audit logging. Administrative actions (user CRUD, team management, website deletion) are not logged to an immutable audit trail. Cannot perform forensic analysis after incidents. |
| **Recommendation** | Enable CloudTrail for AWS API audit logging. Implement application-level audit logging for administrative actions, writing structured audit events to CloudWatch Logs or S3 with immutable storage (Object Lock). |
| **Evidence** | `package.json` (debug dependency), absence of CloudTrail, CloudWatch, or audit logging configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured. PostgreSQL data is stored in an unencrypted Docker volume (`umami-db-data`). No KMS keys, no S3 encryption, no EBS encryption configuration exists. The application encrypts JWT tokens using AES-256-GCM (`src/lib/crypto.ts`) but this is application-level token encryption, not data-at-rest encryption for the database or storage layer. |
| **Gap** | No encryption at rest for any data store. Analytics data (potentially containing PII like IP addresses, page URLs, user sessions) is stored unencrypted. |
| **Recommendation** | Aurora PostgreSQL provides encryption at rest by default with AWS-managed keys. Configure customer-managed KMS keys for sensitive data. Ensure all S3 buckets, EBS volumes, and ElastiCache clusters use encryption at rest. |
| **Evidence** | `docker-compose.yml` (unencrypted Docker volume), `src/lib/crypto.ts` (application-level encryption only), absence of KMS configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JWT-based authentication is implemented with AES-256-GCM encrypted tokens (`src/lib/jwt.ts`, `src/lib/crypto.ts`). Token validation occurs via Bearer token in Authorization header (`parseAuthToken`). Password hashing uses bcrypt with 10 salt rounds (`src/lib/password.ts`). RBAC with 7 roles enforced in `src/permissions/`. The tracker endpoint (`/api/send`) is intentionally public (by design — receives anonymous analytics events). The API has per-request authentication on management endpoints. |
| **Gap** | Token-based auth on management endpoints. The public tracker endpoint (`/api/send`) lacks infrastructure-level throttling — relies on application-level rate limiting only. No OAuth2/OIDC — custom JWT implementation. |
| **Recommendation** | Consider offloading authentication to API Gateway with Cognito authorizer for management endpoints. The tracker endpoint should have API Gateway throttling to prevent abuse. The custom JWT implementation is functional but not standards-based OAuth2. |
| **Evidence** | `src/lib/jwt.ts` (JWT with AES-256-GCM), `src/lib/crypto.ts` (encryption), `src/lib/password.ts` (bcrypt), `src/permissions/` (RBAC) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. User credentials (username + bcrypt password) are stored in the local PostgreSQL database. No integration with any external identity provider (Cognito, Okta, SAML, OIDC). No SSO capability. No federation. The login flow is entirely self-contained within the application. |
| **Gap** | Application manages its own authentication with no external IdP integration. Cannot integrate into organizational SSO. Each Umami deployment is an isolated identity silo. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. This enables SSO, MFA, social login, and SAML/OIDC federation with organizational identity providers. |
| **Evidence** | `prisma/schema.prisma` (User model with username/password), `src/lib/password.ts` (local bcrypt auth), absence of OIDC/SAML/Cognito configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets are managed via environment variables: `DATABASE_URL` (contains credentials), `APP_SECRET` (JWT signing key), `CLICKHOUSE_URL` (may contain credentials), `KAFKA_URL` (may contain credentials). The docker-compose.yml contains a hardcoded `APP_SECRET: replace-me-with-a-random-string` placeholder and database credentials (`POSTGRES_PASSWORD: umami`). The `podman/env.sample` file shows the same pattern. No Secrets Manager, Vault, or encrypted parameter store is used. No rotation configured. |
| **Gap** | Production credentials are kept in environment variables with no rotation. The docker-compose.yml contains placeholder credentials that may be used as-is in development. No secrets management system. |
| **Recommendation** | Store all secrets (DATABASE_URL, APP_SECRET, KAFKA credentials) in AWS Secrets Manager with automated rotation. Reference secrets from EKS via External Secrets Operator or native Kubernetes secrets synced from Secrets Manager. |
| **Evidence** | `docker-compose.yml` (APP_SECRET: replace-me-with-a-random-string, POSTGRES_PASSWORD: umami), `podman/env.sample` (credential templates), `src/lib/kafka.ts` (credentials from URL env var) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Dockerfile uses `node:22-alpine` as base image — Alpine Linux provides a minimal attack surface but no evidence of hardening beyond this default. No vulnerability scanning (Inspector, Snyk, Trivy) configured. No SSM Patch Manager. No CIS-hardened base image. The Docker build creates a non-root user (`nextjs:nodejs`) which is a security best practice, but no systematic patching strategy exists. |
| **Gap** | No patching strategy beyond Docker image rebuilds. No vulnerability scanning. No hardened base images. Rely on manual Docker image updates for security patches. |
| **Recommendation** | Add container image scanning (ECR native scanning or Trivy in CI pipeline). Implement automated base image updates via Dependabot or Renovate. Consider Bottlerocket for EKS node images. |
| **Evidence** | `Dockerfile` (node:22-alpine, non-root user), absence of vulnerability scanning, absence of patching automation |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools configured in the CI/CD pipeline. No SAST (SonarQube, Semgrep, CodeGuru), no DAST, no dependency vulnerability scanning (Dependabot, npm audit, Snyk), no container scanning. The CI pipeline (`ci.yml`) runs only `pnpm test` and `pnpm build` with no security gates. No `.snyk` policy file. No Dependabot configuration (`.github/dependabot.yml` absent). |
| **Gap** | No security scanning. Vulnerabilities in dependencies or application code reach production undetected. No blocking gates for critical findings. |
| **Recommendation** | Add Dependabot or Renovate for dependency vulnerability scanning. Add SAST (Semgrep or CodeGuru Reviewer) to the CI pipeline. Add container image scanning for the Docker build. Configure security gates that block merges on critical findings. |
| **Evidence** | `.github/workflows/ci.yml` (no security steps), absence of `.github/dependabot.yml`, absence of `.snyk`, absence of Semgrep/SonarQube configuration |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry SDK, no X-Ray, no Jaeger, no Datadog APM. Application logging uses the `debug` npm package which produces unstructured text output controlled by the `DEBUG` environment variable. No trace ID propagation, no span creation, no correlation IDs in logs. |
| **Gap** | No distributed tracing. Cannot trace requests across the application boundary, diagnose latency issues, or correlate events across PostgreSQL, ClickHouse, Redis, and Kafka interactions. |
| **Recommendation** | Instrument with OpenTelemetry SDK for Node.js (auto-instrumentation available for Express/Next.js, Prisma, Redis, Kafka). Send traces to AWS X-Ray or CloudWatch ServiceLens. |
| **Evidence** | `package.json` (debug dependency, no OpenTelemetry/X-Ray), absence of tracing configuration |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs defined. No error budget tracking. No CloudWatch alarms for p99/p95 latency. The only health check is `/api/heartbeat` (binary up/down). No formal definition of acceptable service levels for event ingestion latency, dashboard query response time, or data freshness. |
| **Gap** | No SLOs. Cannot measure whether the analytics platform is meeting user expectations. No quantitative targets for event ingestion delay, query latency, or availability. |
| **Recommendation** | Define SLOs for critical user journeys: event ingestion latency (<1s p99), dashboard query response time (<3s p95), tracker script availability (>99.9%). Implement CloudWatch-based SLO monitoring with error budgets. |
| **Evidence** | `src/app/api/heartbeat/` (basic health check only), absence of SLO definitions, absence of latency alarms |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. No CloudWatch `put_metric_data` calls. No Prometheus metrics endpoint. No custom dashboards. The application tracks analytics data for *its users* (page views, events, sessions) but does not publish operational business metrics about its own performance (events/second ingested, active websites, query cache hit rate, concurrent sessions). |
| **Gap** | No business metrics. Cannot measure operational health in business terms. Only infrastructure-level Docker container metrics would be available. |
| **Recommendation** | Publish custom CloudWatch metrics: events ingested/second, active tracking sessions, query latency by report type, cache hit rate, Kafka lag (when enabled). Create operational dashboards. |
| **Evidence** | Absence of metrics publishing code, absence of Prometheus/CloudWatch metrics configuration |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. No error rate monitoring. No latency monitoring. The application has no mechanism to detect or alert on degradation. |
| **Gap** | No alerting. Degradation goes undetected until users report issues. No anomaly detection for error rates or latency. |
| **Recommendation** | Configure CloudWatch alarms for error rates (5xx responses), latency (p99 > threshold), and Kafka consumer lag. Enable CloudWatch anomaly detection on key metrics. Integrate with PagerDuty or OpsGenie for on-call alerting. |
| **Evidence** | Absence of any alerting, monitoring, or alarm configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. The CD pipeline builds Docker images and pushes them to registries but does not deploy. No blue/green, no canary, no rolling deployment configuration. No CodeDeploy, no Argo Rollouts, no Helm canary, no traffic shifting. Deployment would be direct-to-production with no staged rollout. |
| **Gap** | Direct-to-production deployment with no staged rollout. No ability to detect regressions before they affect all users. No automated rollback. |
| **Recommendation** | Implement canary deployments on EKS using Argo Rollouts or Flagger. Route 5% of traffic to new version, validate metrics, then promote. Configure automated rollback on error rate increase. |
| **Evidence** | `.github/workflows/cd.yml` (build + push only, no deployment), absence of deployment strategy configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Cypress E2E tests exist covering login, user management, website management, and team API operations (6 test files in `cypress/e2e/`). A Dockerized Cypress test environment is configured (`cypress/docker-compose.yml`). Jest unit tests exist but are minimal (3 files in `src/lib/__tests__/`). However, the CI pipeline only runs `pnpm test` (Jest unit tests) — Cypress E2E tests are not run in CI. |
| **Gap** | Integration/E2E tests exist but are not consistently run in CI. Only 3 unit tests run in the pipeline. The Cypress tests require a running application and database, which the CI pipeline does not set up. |
| **Recommendation** | Add a CI job that spins up the Dockerized test environment and runs Cypress E2E tests on every PR. Make E2E test pass a required check for merging. Expand unit test coverage for critical business logic (permissions, query building). |
| **Evidence** | `cypress/e2e/` (6 test files), `cypress/docker-compose.yml` (test environment), `.github/workflows/ci.yml` (runs `pnpm test` only — Jest unit tests), `src/lib/__tests__/` (3 unit test files) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks exist. No Systems Manager Automation documents. No Lambda-based remediation. No self-healing patterns. No incident response workflows of any kind. The application has a health check endpoint (`/api/heartbeat`) and Docker restart policies (`restart: always` in docker-compose.yml) as the only automated recovery mechanism. |
| **Gap** | No runbooks — incident response is entirely ad hoc. The only "self-healing" is Docker container restart on crash. |
| **Recommendation** | Create structured runbooks for common incidents (database connection failure, Kafka unavailability, ClickHouse timeout). Implement Systems Manager Automation documents for automated remediation. Configure container health checks with EKS liveness/readiness probes. |
| **Evidence** | `docker-compose.yml` (restart: always, health check), absence of runbooks or automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership. No CODEOWNERS file referencing observability assets. No per-service dashboards. No alarms with named owners. No SLO definitions with team attribution. No monitoring configuration of any kind exists in the repository. |
| **Gap** | No observability ownership. Monitoring is non-existent, let alone attributed to specific teams or owners. |
| **Recommendation** | As observability is built out (tracing, metrics, dashboards), establish CODEOWNERS for monitoring configuration. Define per-service dashboards with named owners. Attribute SLOs to specific teams. |
| **Evidence** | Absence of CODEOWNERS file, absence of monitoring/dashboard configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging. No IaC exists to tag resources. No `default_tags` in Terraform provider, no tag enforcement, no cost allocation tags. No tagging standard defined. |
| **Gap** | No tags. Cannot track costs per workload, identify resource ownership, or enforce budget controls. |
| **Recommendation** | When adopting IaC, define a tagging standard (Environment, Service, Owner, CostCenter) and enforce via `default_tags` in Terraform provider or CDK Aspects. Activate cost allocation tags in AWS Billing. |
| **Evidence** | Absence of IaC with tagging, absence of tagging standard documentation |

---

## Learning Materials

- **Move to Cloud Native**: [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Managed Databases**: [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Managed Analytics**: [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)
- **Move to Modern DevOps**: [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, SEC-Q2, SEC-Q5, OPS-Q7 | Single-instance deployment with PostgreSQL 15, port exposure, credentials |
| `Dockerfile` | INF-Q1, APP-Q2, SEC-Q6 | Multi-stage Node.js 22 Alpine build, non-root user, standalone output |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline with build + test only, no security scanning |
| `.github/workflows/cd.yml` | INF-Q1, INF-Q11, OPS-Q5 | Docker image build and push, no deployment automation |
| `package.json` | APP-Q1, INF-Q4, OPS-Q1, SEC-Q1 | TypeScript 5.9, Next.js 15, KafkaJS, debug logging |
| `prisma/schema.prisma` | APP-Q2, DATA-Q2, DATA-Q4, SEC-Q4 | 13 models, shared schema, PostgreSQL datasource |
| `src/lib/jwt.ts` | SEC-Q3 | JWT authentication with encrypted tokens |
| `src/lib/crypto.ts` | SEC-Q3, SEC-Q2 | AES-256-GCM encryption for tokens |
| `src/lib/password.ts` | SEC-Q3, SEC-Q4 | bcrypt password hashing |
| `src/lib/clickhouse.ts` | INF-Q2, DATA-Q2, INF-Q3 | Self-managed ClickHouse client |
| `src/lib/redis.ts` | INF-Q2, APP-Q6 | Self-managed Redis client via env var |
| `src/lib/kafka.ts` | INF-Q4, APP-Q3, INF-Q3 | Self-managed Kafka producer with KafkaJS |
| `src/queries/prisma/` | DATA-Q2, APP-Q2 | 9 centralized CRUD query files |
| `src/queries/sql/` | DATA-Q2, APP-Q4, INF-Q3 | 40+ analytics SQL query files |
| `prisma/migrations/` | DATA-Q3, DATA-Q4 | 14 PostgreSQL migrations (standard DDL) |
| `db/clickhouse/migrations/` | DATA-Q3, DATA-Q4 | 8 ClickHouse migrations (standard DDL) |
| `src/permissions/` | SEC-Q3 | RBAC with 7 roles |
| `next.config.ts` | INF-Q5, APP-Q5 | CSP headers, CORS (Allow-Origin: *), rewrites |
| `podman/env.sample` | SEC-Q5, APP-Q6 | Environment variable templates with credential patterns |
| `cypress/e2e/` | OPS-Q6 | 6 E2E test files (not run in CI) |
| `src/lib/__tests__/` | OPS-Q6 | 3 unit test files (minimal coverage) |
| `cypress/docker-compose.yml` | OPS-Q6 | Dockerized E2E test environment |
