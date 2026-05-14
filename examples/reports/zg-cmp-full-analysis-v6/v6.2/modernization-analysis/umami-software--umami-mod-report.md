# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | umami-software--umami |
| **Date** | 2026-01-15 |
| **TD Version** | modernization-analysis-v6.2-simulated |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | typescript, analytics, web-app |
| **Context** | Self-hosted privacy-focused web analytics. |
| **Overall Score** | 1.79 / 4.0 |
| **Classification Tier** | Remediation Required (2-11 High → Remediation Required) |

**Archetype Justification**: Next.js app backed by Prisma ORM against PostgreSQL with user/session management (bcrypt + JWT auth), CRUD REST routes for websites, teams, reports, and users, and owned persistent state. Classified as `stateful-crud` — the conservative default that applies the strictest rubric without false downgrades.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

### Classification Rationale

This repo has **6 High**, **26 Medium**, **1 Low** finding (33 emitted findings from 37 evaluated questions, of which 1 is Not Evaluated for archetype-N/A and 3 are passing at Score 4). Rule matched: **"2-11 High → Remediation Required"**.

**MOD classification is deliberately softer than ARA on '1 High'**: ARA treats a single High as an agent-deployment gate (1 High → Remediation Required), whereas MOD treats a single High as typically one modernization gap and maps to Pilot-Ready. Here, with 6 Highs, both schemes would arrive at Remediation Required, and the V5 overall score of 1.79 falls in V5 "Needs Work" (1.5–2.4), which per Req 29 equivalence is consistent with V6 Remediation Required.

`classification_consistency_check`: **consistent**

---

## Score Summary

| Category | Numeric Score | V5 Rating | V6 Severity Status |
|----------|---------------|-----------|--------------------|
| Infrastructure, Platform, and DevOps (INF) | 1.09 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work | Needs Work |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.33 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.79 / 4.0** | **🟠 Needs Work** | **Critical** |

**Scoring Notes:**
- INF: (1+1+1+1+1+1+1+1+1+1+2) / 11 = 12/11 = **1.09**
- APP: (4+2+2+2+1+2) / 6 = 13/6 = **2.17**
- DATA: (2+4+3+4) / 4 = 13/4 = **3.25**
- SEC: (null+1+2+1+2+1+1) / 6 = 8/6 = **1.33** — SEC-Q1 Not Evaluated (no account-level IaC); excluded from numerator and denominator.
- OPS: (1+1+1+1+1+2+1+1+1) / 9 = 10/9 = **1.11**
- Overall: mean of five category scores = (1.09 + 2.17 + 3.25 + 1.33 + 1.11) / 5 = 8.95/5 = **1.79**

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — zero Terraform/CloudFormation/CDK/Helm files in repo. | Blocks reproducible environments and every downstream modernization pathway. |
| 2 | INF-Q1: Managed Compute | 1 | Compute model is Dockerfile + docker-compose with no managed container orchestration target. | Cannot scale elastically; operators run raw Docker on their own hosts. |
| 3 | INF-Q2: Managed Databases | 1 | Default deployment runs self-managed PostgreSQL (plus optional ClickHouse, Redis) in Docker. | Operators shoulder patching, backups, HA, and failover. |
| 4 | INF-Q5: Network Security | 1 | No VPC / subnet / security-group IaC; port 3000 bound on host directly. | No baseline segmentation shipped — blast radius is the whole host. |
| 5 | SEC-Q2: Encryption at Rest | 1 | No KMS, no storage encryption configured; local Docker volume only. | No encryption-at-rest guarantees for analytics data. |

---

## Quick Agent Wins

### Data query agent

- **Prerequisite:** Centralised Prisma schema and unified repository layer under `src/queries` (DATA-Q2 = 4).
- **What it enables:** Natural-language-to-SQL agent over the Umami event model (sessions, page views, events).
- **Additional steps:** Expose a read-only Prisma connection and add row/column allowlists to keep PII out of agent scope.
- **Effort:** Medium

### DevOps agent

- **Prerequisite:** GitHub Actions workflows exist for CI build, tag-triggered Docker publish, and cloud image builds (INF-Q11 = 2).
- **What it enables:** Agent can trigger release tagging, inspect build status, and manage Docker image promotions.
- **Additional steps:** Add a scoped GitHub App for the agent; restrict to release-management scopes.
- **Effort:** Low

### RAG-based knowledge agent

- **Prerequisite:** `README.md` plus extensive inline comments across `src/` and `db/` supply a corpus (detected during Step 1 discovery).
- **What it enables:** Developer-facing RAG agent answering "how does tracker ingest work?" or "what does `APP_SECRET` control?" from the repo's own documentation.
- **Additional steps:** Index README + `src/lib` comments into a vector store (OpenSearch with vector engine — preferences.prefer has no explicit vector DB, OpenSearch is the default AWS choice).
- **Effort:** Low

> **Note:** The API-aware agent prerequisite (APP-Q5 ≥ 2) is **not met** (APP-Q5 = 1). Introducing `/api/v1/*` path prefixes unblocks that win.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (primary, <3); INF-Q1 = 1, APP-Q3 = 2, APP-Q4 = 2 all supporting |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but Dockerfile + docker-compose already exist; workload already containerized |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 and all engines already open source (PostgreSQL, ClickHouse, Redis) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (primary, <3); DATA-Q3 = 3 supporting |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4 = 1 (primary, <3) with self-managed Kafka and ClickHouse data-processing workload |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 AND INF-Q11 = 2 (both primary); OPS-Q5 = 1, OPS-Q6 = 2 supporting |
| 7 | Move to AI | Not Triggered | — | — | Contextual guard not satisfied — no AI signal terms in service context. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

- **Current architecture (APP-Q2 = 2):** Single Next.js deployable serves tracker ingest, admin UI, and reporting. Module boundaries exist under `src/app/api` but the Prisma schema is shared across all modules.
- **Compute model gaps (INF-Q1 = 1):** Only Dockerfile + docker-compose; no EKS / ECS / Fargate / Lambda target.
- **Communication pattern gaps (APP-Q3 = 2, APP-Q4 = 2):** Mostly synchronous; heavy reports run inline in the request path.
- **Recommended approach:** Strangler Fig — see the Decomposition Strategy section below.
- **Representative AWS services:** EKS (preferences.prefer), API Gateway, EventBridge, Aurora PostgreSQL, Lambda.
- **Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing (tracker ingest is already an event log).
- **Learning:** [Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

- **Current database topology (INF-Q2 = 1):** `docker-compose.yml` runs `postgres:15-alpine`. When operators enable advanced features, ClickHouse and Redis are also self-hosted.
- **Engine versions and EOL (DATA-Q3 = 3):** Pinned to PostgreSQL 15; no documented upgrade/EOL playbook.
- **Data access patterns (DATA-Q2 = 4):** Centralised via Prisma + `src/queries` — migration to Aurora is an endpoint swap, not a rewrite.
- **Recommended targets:** Aurora PostgreSQL (preferences.prefer: aurora), ElastiCache for Redis. DynamoDB is in preferences.prefer but is not a natural fit for Umami's relational schema.
- **Representative AWS services:** Aurora PostgreSQL, ElastiCache for Redis, Amazon MemoryDB.
- **Migration tools:** AWS DMS, Prisma connection-string switchover.
- **Learning:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

- **Current streaming infrastructure (INF-Q4 = 1):** Optional `kafkajs` client against self-managed Kafka. `preferences.avoid` explicitly lists `self-managed-kafka`.
- **Data-access sprawl guard:** DATA-Q2 = 4 — access is centralised. The guard requires evidence of data-processing workloads; ClickHouse plus the Kafka event stream satisfy the guard.
- **Recommended targets:** MSK Serverless or EventBridge (preferences.prefer: eventbridge) for Kafka replacement. Redshift Serverless or Athena for the ClickHouse reporting workload.
- **Representative AWS services:** Amazon MSK Serverless, EventBridge, Kinesis Data Streams, Amazon Redshift Serverless, Amazon Athena.
- **Learning:** [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

- **IaC coverage (INF-Q10 = 1):** 0%. Adopt CDK (preferences.prefer context — TypeScript teams pair naturally with CDK).
- **CI/CD state (INF-Q11 = 2):** CI builds and tests; CD publishes images only.
- **Deployment strategy (OPS-Q5 = 1):** No blue/green or canary in-repo.
- **Testing (OPS-Q6 = 2):** Cypress E2E exists but is not wired into CI.
- **Recommended toolchain:** CDK for IaC; GitHub Actions → ArgoCD for GitOps deploys to EKS; Cypress E2E as a merge gate; Argo Rollouts or CodeDeploy weighted target groups for canaries.
- **Representative AWS services:** CodePipeline, CodeBuild, CDK, EKS + ArgoCD.
- **Learning:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy (APP-Q2 = 2)

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Extract services incrementally from the monolith while it keeps running. New traffic routes to the new service; old traffic stays on the monolith until cutover. | APP-Q2 = 2 with identifiable modules (tracker ingest, reports, admin) and shared schema. | **Medium-High (9-15 months)** — each extraction is bounded. | ✅ **Recommended** — lowest risk, incremental value, no big-bang cutover. |
| **Conditional / Adaptive** | Already containerized (Dockerfile + docker-compose). Selectively extract highest-value services (tracker ingest first) and leave the rest in the monolith. | When engineering capacity is constrained. | **Low-Medium** — containerization is already complete. | ✅ Acceptable fallback. |
| **Big-Bang Rewrite** | Rewrite as microservices from scratch. | Almost never. | **Very High** — 12-24+ months with high risk of feature-parity gaps. | ⚠️ **Against.** |

### Recommended Pattern Stack

| Pattern | Purpose | AWS Prescriptive Guidance |
|---------|---------|---------------------------|
| **Anti-corruption Layer** | Isolate extracted tracker service from shared Prisma schema | [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga** | Coordinate session → event → event_data writes across stores | [Saga](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Tracker ingestion is already an event log | [Event Sourcing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure new services with ports/adapters | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Factors

| Factor | Signal for umami | Effort Impact |
|--------|------------------|---------------|
| Module boundaries | Clear (tracker, reports, admin, users, teams) | ⬇ Low |
| Data coupling | Shared Prisma schema across all modules | ⬆ High |
| Stored procedures | None — all logic in app layer | ⬇ Low |
| Communication patterns | Mostly synchronous; Kafka optional | ⬆ High |
| CI/CD maturity | Build+publish pipeline exists; no deploy pipeline | ↔ Mixed |
| Test coverage | Jest unit + Cypress E2E; Cypress not in CI | ↔ Mixed |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: High** — P1, Effort High, Phase 1 |
| **Finding** | Compute model is a Dockerfile (Next.js standalone output on node:22-alpine) plus docker-compose.yml running one umami container and one postgres:15-alpine container. No ECS, EKS, Fargate, Lambda, or App Runner references in the repo. cd.yml publishes the image to GHCR and Docker Hub but does not deploy anywhere. |
| **Gap** | No managed container orchestration, no serverless. All compute guidance leaves operators on raw Docker. |
| **Recommendation** | Publish a reference CDK or Helm deployment targeting EKS (preferences.prefer: eks). Keep docker-compose as the local-dev default and add EKS manifests as the recommended production path. |
| **Evidence** | `Dockerfile`, `docker-compose.yml`, `.github/workflows/cd.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: High** — P1, Effort Medium, Phase 1 |
| **Finding** | docker-compose.yml runs `postgres:15-alpine` as the reference database deployment. When enabled, ClickHouse (`@clickhouse/client`) and Redis (`@umami/redis-client`) are also self-managed. No RDS, Aurora, DynamoDB, DocumentDB, or ElastiCache resources in the repo. Surface gate: `has_persistent_data_store = true` — question was evaluated. |
| **Gap** | Default production guidance points operators at self-managed engines; backups, patching, HA, and failover are manual. |
| **Recommendation** | Document Aurora PostgreSQL (preferences.prefer: aurora) plus ElastiCache for Redis as the recommended managed path. Provide a CDK or Terraform module alongside the docker-compose fast-path. |
| **Evidence** | `docker-compose.yml` (lines 17-30), `package.json` (`@prisma/client`, `@clickhouse/client`, `@umami/redis-client`) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 — **archetype-calibrated (stateful-crud)** |
| **Finding** | Multi-step flows (session → event save → event-data save → optional Kafka publish) are implemented inline in `src/queries/sql/events` and `src/queries/sql/sessions`. No Step Functions, Temporal, MWAA, or Camunda references. For a **stateful-crud** archetype, "No orchestration — all workflow logic hardcoded" is Score 1 under the calibrated rubric. |
| **Gap** | Business-critical multi-step writes are state-machine-in-code with no retry/compensation primitives. |
| **Recommendation** | In the managed reference deployment, wrap cross-store writes in Step Functions Express Workflows or EventBridge Pipes for built-in retries and observability. |
| **Evidence** | `src/queries/sql/events/saveEvent.ts`, `src/queries/sql/sessions/saveSessionData.ts` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 — **archetype-calibrated (stateful-crud)** |
| **Finding** | `src/lib/kafka.ts` uses kafkajs against a Kafka cluster configured via `KAFKA_URL` and `KAFKA_BROKER`. The path is env-gated and optional. No SQS, SNS, EventBridge, MSK, or Kinesis references. For **stateful-crud**, "no messaging where state changes cross service boundaries — tight synchronous coupling" maps to Score 1 under the calibrated rubric, and `preferences.avoid` lists self-managed-kafka. |
| **Gap** | When operators enable event streaming, they run Kafka themselves. |
| **Recommendation** | Replace the kafkajs target with MSK Serverless or EventBridge (preferences.prefer: eventbridge). Keep the env-gated adapter so self-hosted operators can still choose Kafka. |
| **Evidence** | `src/lib/kafka.ts` (lines 1-115), `package.json` (kafkajs dependency) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: High** — P1, Effort Medium, Phase 1 |
| **Finding** | No VPC, subnet, security group, NACL, or PrivateLink definitions anywhere in the repo. docker-compose.yml exposes port 3000:3000 on the host. |
| **Gap** | Network segmentation is entirely an operator responsibility — no baseline shipped. |
| **Recommendation** | Ship reference IaC placing the app in private subnets behind an ALB with least-privilege security groups to RDS/ElastiCache. |
| **Evidence** | `docker-compose.yml`, absence of IaC |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | Next.js serves /api routes directly on port 3000. No API Gateway, AppSync, ALB, or CloudFront. |
| **Gap** | No throttling, auth gateway, request validation, or WAF at the entry point. |
| **Recommendation** | Front the app with API Gateway (preferences.prefer: api-gateway) or CloudFront + ALB. Add a Lambda authorizer for admin APIs. |
| **Evidence** | `docker-compose.yml` (lines 4-9) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | docker-compose runs one fixed umami container and one fixed postgres container. No ASG, ECS service, Lambda concurrency, DynamoDB auto-scaling, or Aurora replica auto-scaling. |
| **Gap** | All capacity is statically provisioned. |
| **Recommendation** | In the reference EKS deployment, add HPA on the Next.js pod + Aurora auto-scaling replicas. Publish custom CloudWatch metrics for tracker-ingest requests-in-flight as scaling signal. |
| **Evidence** | `docker-compose.yml` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Low, Phase 2 |
| **Finding** | docker-compose declares `umami-db-data` as a local Docker volume. No aws_backup_plan, no RDS backup_retention_period, no DynamoDB point_in_time_recovery, no S3 versioning, no EBS snapshot lifecycle. Surface gate: `has_persistent_data_store OR has_at_rest_data_surface = true` — evaluated. |
| **Gap** | No backup strategy shipped with the distribution. |
| **Recommendation** | In the reference Aurora deployment, enable `backup_retention_period = 30` with PITR plus cross-region automated backups. Ship a restore runbook. |
| **Evidence** | `docker-compose.yml` (lines 29-31) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | Single-container reference deployment. No Aurora Multi-AZ, no ASG spanning AZs, no ECS service across AZs. Surface gate: `has_deployed_workload AND (has_api_surface OR has_persistent_data_store) = true` — evaluated. |
| **Gap** | Reference deployment has no HA / fault isolation. |
| **Recommendation** | Reference EKS deployment should span 2+ AZs with Aurora Multi-AZ. Document the minimum production topology. |
| **Evidence** | `docker-compose.yml` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: High** — P1, Effort High, Phase 1 |
| **Finding** | No Terraform, CloudFormation, CDK, Helm, or Kustomize files anywhere in the repo. The only deployment artifacts are Dockerfile and docker-compose.yml. |
| **Gap** | 0% IaC coverage. |
| **Recommendation** | Adopt CDK (preferred for TypeScript teams and preferences.prefer) to define EKS, Aurora, ElastiCache, networking, and security. Start with compute + database. |
| **Evidence** | Repo file listing — no IaC files present |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P1, Effort Medium, Phase 1 |
| **Finding** | ci.yml runs pnpm install, pnpm test, pnpm build. cd.yml builds and pushes multi-arch Docker images to GHCR and Docker Hub on tag. cd-cloud.yml pushes a cloud image on branch push. No deployment stage, no rollback, no environment promotion. |
| **Gap** | Build + publish automation exists; deploy automation does not. |
| **Recommendation** | Extend cd.yml with a deploy stage to the reference EKS cluster via CDK + ArgoCD. Add automated rollback on health-check failure. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/cd-cloud.yml` |

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 (Mature) — **No finding emitted (passing)** |
| **Finding** | TypeScript 5.9, Next.js 15.5, React 19, Node 22-alpine base image, modern toolchain (Biome, tsup, rollup, Prisma 6). Modern cloud-native language at a current version. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json`, `tsconfig.json`, `Dockerfile` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P1, Effort High, Phase 1 |
| **Finding** | Single Next.js deployable serves tracker ingest (`/api/send`), the admin UI, and the reporting API. Module boundaries exist under `src/app/api` (websites, reports, events, users, teams) but all modules share the same Prisma schema and database. |
| **Gap** | Tracker ingest and reporting cannot scale independently; deploys affect the whole product. |
| **Recommendation** | Strangler Fig extraction starting with tracker ingest (highest volume, naturally async). Use an Anti-corruption Layer when the extracted service reads the shared schema. |
| **Evidence** | `src/app/api/` (route tree), `prisma/schema.prisma` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P2, Effort Medium, Phase 2 — **archetype-calibrated (stateful-crud)** |
| **Finding** | Inter-module communication is synchronous Prisma/HTTP. Kafka integration is env-gated and optional. For **stateful-crud**, "Primarily synchronous with some async for background jobs" is Score 2 under the calibrated rubric. |
| **Gap** | No event-driven path unless Kafka is enabled. |
| **Recommendation** | Publish tracker-event events to EventBridge as the reference async path. Keep synchronous Prisma for admin CRUD flows. |
| **Evidence** | `src/lib/kafka.ts`, `src/queries/sql/` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P2, Effort Medium, Phase 2 — **archetype-calibrated (stateful-crud)** |
| **Finding** | Reporting endpoints under `src/app/api/reports` execute Prisma / ClickHouse queries inline in the request path. No background job queue, no callback pattern for long-running exports. For **stateful-crud**, "Some background job processing but inconsistent patterns" is Score 2 under the calibrated rubric. |
| **Gap** | Heavy reports risk request timeouts. |
| **Recommendation** | Offload heavy report generation to an SQS-backed worker or Step Functions, returning a job ID the UI polls. |
| **Evidence** | `src/app/api/reports/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | Next.js App Router routes under `src/app/api/*` are not grouped under /v1, /v2. No Accept-Version headers. |
| **Gap** | No versioning — breaking changes propagate directly. |
| **Recommendation** | Introduce `/api/v1/*` path prefix and document deprecation windows. Apply first to tracker ingest, then admin APIs. |
| **Evidence** | `src/app/api/` route tree |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P2, Effort Low, Phase 2 |
| **Finding** | `DATABASE_URL`, `KAFKA_URL`, `CLICKHOUSE_URL`, `REDIS_URL` supplied via environment variables. No AWS Service Discovery / Cloud Map / Consul / service mesh. |
| **Gap** | Endpoint changes require restart; no dynamic discovery. |
| **Recommendation** | For the EKS reference deployment, use AWS Cloud Map / CoreDNS for intra-cluster service discovery. |
| **Evidence** | `src/lib/kafka.ts` (lines 14-20), `src/lib/prisma.ts` |

### Data Platform Modernization (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P1, Effort Low, Phase 3 |
| **Finding** | All analytics data lives in PostgreSQL (via Prisma) and ClickHouse. No `aws_s3_bucket`, no Textract, no document-parsing libraries. The product's core domain has no unstructured-data path today — but there is also no reference S3 path for future exports/uploads. |
| **Gap** | If the roadmap adds user-uploaded assets (brand logos, PDF report exports), there is no storage target. |
| **Recommendation** | When future features require unstructured storage (e.g., PDF exports), standardise on S3 with server-side encryption. |
| **Evidence** | `prisma/schema.prisma` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 (Mature) — **No finding emitted (passing)** |
| **Finding** | All database access goes through `src/queries/**` which wraps Prisma and the ClickHouse client behind a consistent interface. No scattered raw queries in handlers. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/queries/` module tree, `src/lib/prisma.ts` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 (Partial) — **Severity: Low** — P1, Effort Low, Phase 2 |
| **Finding** | docker-compose pins `postgres:15-alpine`. Dockerfile uses `node:22-alpine`. 14 Prisma migration folders track schema changes cleanly. No documented engine EOL / upgrade procedure. |
| **Gap** | PostgreSQL 15 is still supported, but no documented upgrade playbook. |
| **Recommendation** | Add a MAINTAINERS.md section covering the PostgreSQL upgrade path, rollback window, and testing procedure. |
| **Evidence** | `docker-compose.yml` (lines 17-30), `prisma/migrations/` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 (Mature) — **No finding emitted (passing)** |
| **Finding** | All business logic lives in the Next.js application layer via Prisma. The only SQL files (`db/postgresql/data-migrations/*.sql`) are data backfill migrations with no `CREATE PROCEDURE` / `CREATE TRIGGER` / `CREATE FUNCTION`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `db/postgresql/data-migrations/` |

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | `has_iac_provisioning_aws_resources = false` and the repo contains no account/foundation-level IaC (no CloudTrail, AWS Config, GuardDuty, or Organization SCPs). Per Step 1.6 SEC-Q1 gate, CloudTrail is an AWS account-level service provisioned once per account or organization and belongs in foundation IaC, not in this application repo. Evaluating SEC-Q1 here would produce a false Score 1. |
| **Gap** | N/A |
| **Recommendation** | N/A — evaluate in the foundation/account-level infrastructure repo. |
| **Evidence** | Absence of `aws_cloudtrail` / `aws_config_*` / `aws_guardduty_*` in repo |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: High** — P1, Effort Low, Phase 1 |
| **Finding** | The persistent data surface is the `umami-db-data` docker-compose volume. No KMS, no `aws_kms_key`, no encryption config on any data store. Surface gate: `has_at_rest_data_surface = true` — evaluated. |
| **Gap** | No encryption-at-rest shipped with the distribution. |
| **Recommendation** | In the reference Aurora deployment, enable storage encryption with a customer-managed KMS key. Document the key-rotation policy. |
| **Evidence** | `docker-compose.yml` (lines 29-31) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | Admin APIs use JWT (`src/lib/jwt.ts`, `jsonwebtoken`) authenticated against an APP_SECRET-derived key. Tracker ingestion endpoints (`/api/send`) are intentionally public to accept calls from untrusted browsers. `bcryptjs` is used for password hashing (SALT_ROUNDS = 10). |
| **Gap** | No OAuth2/OIDC; all auth is app-managed. Tracker endpoint has no throttling at the app layer. |
| **Recommendation** | Keep JWT for admin but place `/api/send` behind API Gateway with per-origin throttling. Consider Cognito for admin identity federation. |
| **Evidence** | `src/app/api/auth/login/route.ts`, `src/lib/jwt.ts`, `src/lib/password.ts` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | `src/app/api/auth/login/route.ts` authenticates users against Umami's own users table with bcrypt. No Cognito, Okta, OIDC, or SAML integration. |
| **Gap** | Enterprise operators cannot federate against their existing IdP. |
| **Recommendation** | Add an OIDC adapter (NextAuth.js or AWS Cognito) and document how operators plug in their own IdP. |
| **Evidence** | `src/app/api/auth/login/route.ts` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P1, Effort Medium, Phase 1 |
| **Finding** | APP_SECRET, DATABASE_URL, KAFKA_URL, and related secrets are supplied via environment variables (`src/lib/crypto.ts`, `src/lib/kafka.ts`). `docker-compose.yml` ships `APP_SECRET: replace-me-with-a-random-string` and `POSTGRES_PASSWORD: umami` as placeholders. No Secrets Manager, Vault, or encrypted parameter store. No rotation. The repo does not commit real credentials — only placeholders — so this is Score 2 (no plaintext in source, but no rotation). |
| **Gap** | Production credentials held in env vars with no rotation. |
| **Recommendation** | Store all secrets in AWS Secrets Manager with automated rotation. Reference from EKS via External Secrets Operator or the native Secrets Store CSI driver. |
| **Evidence** | `docker-compose.yml` (lines 8-12), `src/lib/crypto.ts`, `src/lib/kafka.ts` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | Dockerfile builds against `node:22-alpine` and `postgres:15-alpine`. No SSM Patch Manager, Inspector, Snyk, or Trivy scan configured. cd.yml does not scan images. No hardened base images. |
| **Gap** | Vulnerability scanning and patching are entirely operator responsibility. |
| **Recommendation** | Add container scanning (ECR image scan, Trivy, or Snyk) to cd.yml before image push. Use Bottlerocket for EKS worker nodes in the managed deployment. |
| **Evidence** | `Dockerfile`, `.github/workflows/cd.yml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Low, Phase 2 |
| **Finding** | ci.yml runs `pnpm install`, `pnpm test`, `pnpm build` only. No Dependabot in `.github`, no SonarQube, Semgrep, CodeGuru Reviewer, or npm/pnpm audit step. |
| **Gap** | No automated security validation in the pipeline. |
| **Recommendation** | Enable Dependabot for pnpm and GitHub Actions. Add a Semgrep or CodeQL SAST step to ci.yml. Gate releases on critical findings. |
| **Evidence** | `.github/workflows/ci.yml` |

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Low, Phase 2 |
| **Finding** | Application logging uses the `debug` npm package for unstructured text output. No OpenTelemetry, X-Ray, Jaeger, or APM SDK. No trace-id propagation, no correlation IDs in logs. |
| **Gap** | Cannot trace a request across Next.js → Prisma → PostgreSQL → ClickHouse → Redis → Kafka. |
| **Recommendation** | Instrument with OpenTelemetry SDK for Node.js (auto-instrumentation covers Next.js, Prisma, Redis, Kafka). Export to AWS X-Ray or CloudWatch ServiceLens. |
| **Evidence** | `package.json` (debug only; no OTEL/X-Ray dependency) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 3 |
| **Finding** | No SLO files, CloudWatch alarm definitions, error-budget tracking, or SLO dashboards in the repo. Per the OPS-Q2 rubric scoring-limitation note, SLOs typically live in external platforms — finding has a known high false-positive rate. Surface gate: `has_api_surface OR has_persistent_data_store = true` — evaluated. |
| **Gap** | No SLO evidence in the repo. |
| **Recommendation** | Ship a reference SLO set for tracker ingest (availability, p99 latency) and admin API. Track in CloudWatch with error-budget burn alarms. |
| **Evidence** | Absence of SLO artifacts |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | No `cloudwatch.put_metric_data`, StatsD, or Prometheus metric-publishing in `src/`. |
| **Gap** | Operators cannot track business-relevant metrics as first-class metrics. |
| **Recommendation** | Publish tracker-ingest count, report-generation latency p99, and DB pool exhaustion as CloudWatch custom metrics. |
| **Evidence** | Absence of metric-publishing code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 2 |
| **Finding** | No CloudWatch alarm definitions, PagerDuty integration, or anomaly detectors in the repo. |
| **Gap** | No alerting on error-rate or latency regressions. |
| **Recommendation** | Add CloudWatch anomaly detection on `/api/send` ingest error rate and admin-API p99 latency. |
| **Evidence** | Absence of alarm definitions |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: High** — P1, Effort Medium, Phase 1 |
| **Finding** | cd.yml and cd-cloud.yml only build and push Docker images. No CodeDeploy, no Helm canary, no Argo Rollouts, no Lambda traffic shifting, no ALB weighted target groups. The GHCR `latest` tag is reassigned on every release (direct replacement). Surface gate: `has_deployed_workload = true` — evaluated. Scoring-limitation note: deployment orchestration may live outside the repo — recommendation accommodates this. |
| **Gap** | No staged rollout strategy shipped. |
| **Recommendation** | In the reference EKS deployment, adopt Argo Rollouts for canary releases. Publish immutable version tags only (stop reassigning `latest`). |
| **Evidence** | `.github/workflows/cd.yml`, `.github/workflows/cd-cloud.yml` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 (Needs Work) — **Severity: Medium** — P1, Effort Low, Phase 1 |
| **Finding** | `cypress.config.ts` and `cypress/` directory contain E2E tests. package.json defines `cypress-open` and `cypress-run` scripts. ci.yml runs `pnpm test` (Jest unit tests) but does NOT invoke Cypress. |
| **Gap** | E2E coverage exists in-repo but never runs in CI. |
| **Recommendation** | Add a Cypress job to ci.yml that runs against the locally-started Next.js + postgres docker-compose stack. Gate merges on passing E2E. |
| **Evidence** | `cypress.config.ts`, `cypress/`, `.github/workflows/ci.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Medium, Phase 3 |
| **Finding** | No runbook files, no SSM Automation documents, no Lambda-based remediation, no self-healing patterns. |
| **Gap** | Incident response is entirely ad hoc. |
| **Recommendation** | Publish runbooks for common incidents (DB pool exhaustion, tracker ingest backlog, Kafka consumer lag). Automate recovery as SSM documents in the reference deployment. |
| **Evidence** | Absence of runbook files |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Low, Phase 3 |
| **Finding** | No CODEOWNERS file. No service-level dashboards, no SLO definitions with team attribution, no team tags on observability assets. |
| **Gap** | No defined observability ownership. |
| **Recommendation** | Add CODEOWNERS for the repo. Ship a reference Grafana/CloudWatch dashboard JSON with named owners. |
| **Evidence** | Absence of CODEOWNERS, no dashboard JSON |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 (Not Ready) — **Severity: Medium** — P2, Effort Low, Phase 3 |
| **Finding** | No IaC in repo, therefore no `default_tags`, required-tags Config rules, or Tag Policies. |
| **Gap** | No resource tagging strategy shipped with the distribution. |
| **Recommendation** | In the CDK reference, add `default_tags` for application, environment, owner, cost-center. Layer AWS Config required-tags rule and Organizations Tag Policies in the foundation account. |
| **Evidence** | Absence of IaC |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|---------------|---------|
| `Dockerfile` | INF-Q1, SEC-Q6 | Next.js build + runtime on node:22-alpine, multi-arch |
| `docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, SEC-Q2, SEC-Q5 | Reference local/self-hosted deployment with self-managed postgres |
| `package.json` | APP-Q1, INF-Q2, OPS-Q1 | Dependency manifest — Next.js 15, Prisma 6, Kafka, Redis, ClickHouse |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | Node.js CI — pnpm install/test/build |
| `.github/workflows/cd.yml` | INF-Q11, OPS-Q5, SEC-Q6 | Docker image build-and-push on tag |
| `.github/workflows/cd-cloud.yml` | INF-Q11, OPS-Q5 | Cloud branch image build-and-push |
| `src/lib/kafka.ts` | INF-Q4, APP-Q3, APP-Q6, SEC-Q5 | Optional kafkajs client against self-managed Kafka |
| `src/lib/jwt.ts` | SEC-Q3 | JWT token creation and verification |
| `src/lib/crypto.ts` | SEC-Q5 | Secret derivation from APP_SECRET env var |
| `src/lib/password.ts` | SEC-Q3 | bcryptjs password hashing |
| `src/app/api/auth/login/route.ts` | SEC-Q3, SEC-Q4 | Login endpoint — bcrypt + JWT |
| `src/app/api/` | APP-Q2, APP-Q5, APP-Q6 | Next.js API route tree |
| `src/app/api/reports/` | APP-Q4 | Report endpoints |
| `src/queries/` | DATA-Q2, APP-Q3 | Unified data access layer |
| `src/queries/sql/events/saveEvent.ts` | INF-Q3, INF-Q4 | Multi-store event write flow |
| `src/queries/sql/sessions/saveSessionData.ts` | INF-Q3 | Session data save flow |
| `prisma/schema.prisma` | DATA-Q1 | Shared Prisma schema |
| `prisma/migrations/` | DATA-Q3 | 14 migration folders |
| `db/postgresql/data-migrations/` | DATA-Q4 | SQL data backfill migrations (no stored procs) |
| `cypress.config.ts` | OPS-Q6 | Cypress E2E configuration (not wired into CI) |
| `app.json` | SEC-Q5 | Heroku deploy config with APP_SECRET generator |
| `netlify.toml` | INF-Q1 | Netlify Next.js plugin config |

---

*Analysis generated by AWS Transform — Modernization Analysis TD v6.2 (simulated). MOD classification tier: Remediation Required. V5/V6 classification consistency check: consistent.*
