# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Radarr |
| **Date** | 2025-07-17 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Movie collection manager (*arr suite). |
| **Overall Score** | 1.82 / 4.0 |

**Archetype Justification**: Radarr owns persistent state via SQLite/PostgreSQL databases, exposes full CRUD REST APIs for movies, collections, and configuration, and manages entity lifecycle (movie status, download state, file management). While it orchestrates multiple external services (TMDb, indexers, download clients), it is fundamentally a stateful CRUD application. Classified as `stateful-crud`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.82 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No cloud compute — application is self-hosted with no IaC for ECS/EKS/Lambda/Fargate. | Blocks containerization and cloud-native modernization pathways. |
| 2 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code — all infrastructure is manually provisioned or user-configured. | Prevents reproducible deployments, environment consistency, and disaster recovery automation. |
| 3 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation — application exposes HTTP directly. | Limits ability to enforce least-privilege network access and isolate blast radius. |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or centralized audit logging — only application-level NLog. | No forensic trail for security incidents or compliance audits. |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumentation — no OpenTelemetry or X-Ray SDK. | Cannot diagnose cross-service request flows or identify performance bottlenecks. |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 3 (≥ 2). Comprehensive OpenAPI 3.0.4 specification exists at `src/Radarr.Api.V3/openapi.json` (12,843 lines, 302 KB) with structured JSON responses across all `/api/v3/` endpoints.
- **What it enables:** An AI agent can discover and invoke Radarr's REST API endpoints as tools — managing movies, triggering searches, monitoring downloads, and querying history programmatically.
- **Additional steps:** The OpenAPI spec is already production-ready. Agent tooling can consume it directly. Consider generating SDK client libraries for the agent's preferred language.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2). Centralized `BasicRepository<T>` pattern in `src/NzbDrone.Core/Datastore/` with Dapper ORM provides a clean data access layer.
- **What it enables:** A natural-language-to-query agent that translates user questions ("show me all movies added this month with quality upgrades pending") into structured queries against the Radarr database.
- **Additional steps:** Schema documentation would need to be generated from the FluentMigrator migration files (140+ migrations). The agent would need read-only access to the database.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). Azure Pipelines CI/CD pipeline exists with build, test, and packaging stages.
- **What it enables:** An agent that triggers builds, monitors pipeline status, checks test results, and manages release packaging via Azure DevOps REST APIs.
- **Additional steps:** Azure DevOps API access needs to be configured for the agent. Pipeline status webhooks could enhance real-time monitoring.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, wiki references at `wiki.servarr.com/radarr`, and the OpenAPI spec provide a documentation corpus.
- **What it enables:** A retrieval-augmented generation agent that answers developer and user questions by indexing Radarr's documentation, API specs, and contribution guidelines.
- **Additional steps:** Index the README, CONTRIBUTING, API docs, and external wiki content. Consider using Amazon Bedrock with knowledge bases for the RAG pipeline.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute), APP-Q3=2 (primarily sync) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (no managed compute), no Dockerfile/container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); SQLite and PostgreSQL are already open source |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (all databases self-managed — embedded SQLite, user-provisioned PostgreSQL) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads (streaming, ETL, analytics) detected in discovery |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), OPS-Q5=1 (no staged deployment strategy) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Movie collection manager (*arr suite)") |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Radarr is a tightly-coupled monolith (APP-Q2=2) compiled as a single deployable unit (`Radarr.sln`). All modules — API (Radarr.Api.V3), core business logic (NzbDrone.Core), HTTP layer (Radarr.Http), SignalR (NzbDrone.SignalR), and platform-specific code (NzbDrone.Windows, NzbDrone.Mono) — share a single database and DI container. The application handles everything from REST API serving to background job scheduling, media file management, indexer communication, and download client orchestration within one process.

**Compute Model Gaps:** No cloud compute definitions exist. The application is distributed as platform-specific packages (zip/tar/installer) for manual installation on user machines. No ECS, EKS, Lambda, or Fargate configurations.

**Communication Pattern Gaps:** External service communication (TMDb API, indexers, download clients, notification services) is primarily synchronous HTTP. The internal event aggregator (`EventAggregator.cs`) provides in-process async event handling, but no managed messaging service (EventBridge, SQS, SNS) is used for cross-boundary communication.

**Recommended Decomposition:** See Decomposition Strategy section below. The Strangler Fig (Parallel Track) approach is recommended, starting with extracting the API gateway layer and gradually separating indexer management, download orchestration, and media file management into independent services.

**Representative AWS Services (respecting preferences):**
- **Compute:** Amazon EKS (preferred) for containerized microservices
- **API Layer:** Amazon API Gateway (preferred) for request routing, throttling, and authentication
- **Messaging:** Amazon EventBridge (preferred) for event-driven communication between services
- **Database:** Amazon Aurora PostgreSQL (preferred) or Amazon DynamoDB (preferred) for per-service data stores
- **Orchestration:** AWS Step Functions for multi-step workflows (search → download → organize)

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Radarr is distributed as bare-metal packages — platform-specific zip/tar archives and Windows installers. No Dockerfile, docker-compose.yml, or Kubernetes manifests exist in the repository. The README references Docker images from the `linuxserver/radarr` community (Docker Hub badge present), but these are maintained externally, not in this repository.

**Container Readiness Indicators:**
- .NET 8.0 application with self-contained publishing already configured (`-p:SelfContained=True`)
- Multi-platform build support (linux-x64, linux-musl-x64, linux-arm64, linux-musl-arm64) — Alpine/musl builds already validated in CI
- Configuration externalized via environment variables (`Radarr__Postgres__Host`, etc.)
- Port binding configurable at runtime
- Health check infrastructure exists (`NzbDrone.Core/HealthCheck/`)

**Recommended Container Orchestration (respecting preferences):**
- **Amazon EKS** (preferred) — Kubernetes orchestration for the containerized Radarr application
- Avoid self-managed Kubernetes (as specified in preferences)
- **Amazon ECR** for container image storage
- **AWS App Runner** as a simpler alternative for initial containerization

**Migration Approach:** Lift-and-containerize first — create a Dockerfile based on the existing `linux-musl-x64` build artifacts (already tested in CI against Alpine containers). Then refactor deployment to use EKS with Helm charts.

**AWS Container Migration Guidance:**
- [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** Radarr uses embedded SQLite as the default database engine (`SourceGear.sqlite3` v3.50.4.2, `System.Data.SQLite` v2.0.2) with optional PostgreSQL support via `Npgsql` v9.0.3. SQLite files are stored on the local filesystem with no managed backup, replication, or failover. PostgreSQL, when used, is user-provisioned (the application connects to a user-supplied PostgreSQL instance configured via environment variables).

**Engine Versions and EOL Status:** SQLite is embedded with the NuGet package version. PostgreSQL version depends on user provisioning — CI tests against PostgreSQL 14 and 15. No engine version pinning in IaC (no IaC exists).

**Data Access Patterns:** Centralized `BasicRepository<T>` pattern with Dapper ORM (`src/NzbDrone.Core/Datastore/`). All data access flows through the Datastore layer. Database type is abstracted — the application already supports switching between SQLite and PostgreSQL via connection string configuration.

**Recommended Managed Database Targets (respecting preferences):**
- **Amazon Aurora PostgreSQL** (preferred) — drop-in replacement for user-provisioned PostgreSQL with managed failover, automated backups, and read replicas
- **Amazon DynamoDB** (preferred) — for specific data patterns that benefit from key-value access (e.g., configuration, session state)
- Avoid Oracle (as specified in preferences)

**Migration Tools:**
- AWS Database Migration Service (DMS) for PostgreSQL → Aurora migration
- Connection string update in `ConnectionStringFactory.cs` to point to Aurora endpoint

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** No infrastructure-as-code exists. No Terraform, CloudFormation, CDK, Helm, or Kustomize files found. All infrastructure is manually provisioned by end users or community Docker image maintainers.

**Current CI/CD State (INF-Q11=3):** Azure Pipelines provides comprehensive build and test automation — multi-platform builds (Windows, Linux, macOS, FreeBSD), unit tests, integration tests (including PostgreSQL 14/15), automation tests, SonarCloud analysis, and Sentry source map uploads. GitHub Actions CI provides an additional build pipeline. However, deployment is manual — packages are created but not automatically deployed to any environment.

**Deployment Strategy Gaps (OPS-Q5=1):** No canary, blue/green, or rolling deployment strategy. Packages are built and distributed for manual installation. The built-in update mechanism (`NzbDrone.Update`) handles self-updating but with no staged rollout.

**Testing Gaps (OPS-Q6=3):** Integration tests exist and run in CI across platforms, including PostgreSQL integration tests. This is a strength that supports modernization.

**Recommended DevOps Toolchain (respecting preferences):**
- **AWS CDK** or **Terraform** for IaC — define EKS clusters, Aurora databases, API Gateway, and EventBridge resources
- **AWS CodePipeline + CodeBuild** for CI/CD — or continue with Azure Pipelines and add deployment stages
- **AWS CodeDeploy** with EKS integration for blue/green deployments
- **Helm charts** for Kubernetes deployment configuration

**AWS DevOps Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

Radarr scores APP-Q2 = 2 (monolith with identifiable modules but shared database schemas and tight coupling through a shared DI container). The following decomposition guidance applies.

### Decomposition Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping the monolith running. New features are built as services; existing features are migrated over time. | Radarr has identifiable module boundaries (Movies, Indexers, Download, Notifications, MediaFiles) that can be extracted one at a time. | **Medium to High** — 6-18 months | ✅ **Recommended.** Radarr's clear namespace structure supports incremental extraction with lowest risk. |
| **Conditional / Adaptive** | Containerize the monolith as-is first, then selectively extract high-value services. | If team capacity is limited or the primary goal is cloud deployment rather than full decomposition. | **Low to Medium** — containerization in 2-4 weeks, selective extraction over 3-12 months | ✅ **Recommended when capacity is constrained.** Containerize first (Radarr already has musl/Alpine CI validation), then extract. |
| **Big-Bang Rewrite** | Rewrite as microservices from scratch. | Almost never appropriate for Radarr — the application is functional with identifiable modules. | **Very High** — 12-24+ months | ⚠️ **Not recommended.** Radarr is a working, actively developed application. Strangler Fig is safer. |

### Candidate Service Boundaries

Based on the `NzbDrone.Core` module structure:

1. **Movie Management Service** — `Movies/`, `Collections/`, `MediaCover/`, `Tags/`
2. **Indexer & Search Service** — `Indexers/`, `IndexerSearch/`, `DecisionEngine/`
3. **Download Orchestration Service** — `Download/`, `Queue/`
4. **Media File Service** — `MediaFiles/`, `Extras/`, `Organizer/`, `RootFolders/`
5. **Notification Service** — `Notifications/`
6. **Import List Service** — `ImportLists/`

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's data model. | Every extraction — place an ACL between new services and the monolith. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions (e.g., search → grab → download → import pipeline). | When extracting the Download Orchestration and Media File services. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture all movie state changes as events. | When separating Movie Management from downstream consumers (notifications, history). | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear ports and adapters. | Every new service — ensures testability and infrastructure portability. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation

| Factor | Current State | Effort Signal |
|--------|--------------|---------------|
| Module boundaries | Clear namespace structure (Movies, Indexers, Download, etc.) with identifiable responsibilities | **Low** — boundaries exist |
| Data coupling | Single shared database via `BasicRepository<T>` — all modules access the same DB instance | **High** — database must be decomposed per service |
| Stored procedures | None — all business logic in C# application layer (DATA-Q4=4) | **Low** — no database-layer logic to extract |
| Communication patterns | Primarily synchronous HTTP for external calls; internal event aggregator for in-process events | **Medium** — event aggregator pattern provides a foundation for EventBridge migration |
| CI/CD maturity | Comprehensive CI pipeline with multi-platform builds and integration tests (INF-Q11=3) | **Low** — pipeline can be extended for multi-service deployment |
| Test coverage | Integration tests covering API endpoints across platforms, PostgreSQL tests (OPS-Q6=3) | **Low** — existing tests provide regression safety during extraction |

**Calibrated Effort Estimate:** Medium-High for full decomposition via Strangler Fig (9-15 months). Low for initial containerization via Conditional/Adaptive approach (2-4 weeks for Dockerfile + Helm chart creation).

---

<!-- SECTION: DETAILED_FINDINGS_PLACEHOLDER -->

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute infrastructure exists. Radarr is distributed as self-contained platform-specific packages (zip, tar.gz, Windows installer) for manual installation. Build artifacts target bare-metal runtimes: `win-x64`, `win-x86`, `linux-x64`, `linux-musl-x64`, `linux-arm`, `linux-arm64`, `osx-x64`, `osx-arm64`, `freebsd-x64`. No IaC definitions for ECS, EKS, Lambda, Fargate, or EC2 were found. |
| **Gap** | All compute is user-provisioned with no managed services. No Dockerfile or container orchestration exists in this repository. |
| **Recommendation** | Create a Dockerfile leveraging the existing `linux-musl-x64` build (already CI-validated on Alpine). Deploy to Amazon EKS (preferred) with Helm charts. Start with a single-container deployment before decomposing. |
| **Evidence** | `build.sh` (package targets), `azure-pipelines.yml` (build matrix), `src/Directory.Build.props` (RuntimeIdentifiers), absence of any `.tf`, `cdk.json`, `Dockerfile`, or `Chart.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Radarr uses embedded SQLite as the default database (`SourceGear.sqlite3` v3.50.4.2, `System.Data.SQLite` v2.0.2 in `Radarr.Common.csproj`) with optional PostgreSQL support (`Npgsql` v9.0.3 in `Radarr.Core.csproj`). SQLite files are stored on the local filesystem. PostgreSQL, when enabled, is user-provisioned via environment variables (`Radarr__Postgres__Host`, `Radarr__Postgres__Port`, etc.). No managed database service (RDS, Aurora, DynamoDB) is defined anywhere. |
| **Gap** | All databases are self-managed — either embedded SQLite on disk or user-provisioned PostgreSQL. No automated failover, managed backups, or scaling. |
| **Recommendation** | Migrate to Amazon Aurora PostgreSQL (preferred) for the production database. Radarr already supports PostgreSQL via `Npgsql` — switching to Aurora requires only a connection string change in `ConnectionStringFactory.cs`. Use DynamoDB (preferred) for configuration/session data if decomposing into microservices. |
| **Evidence** | `src/NzbDrone.Common/Radarr.Common.csproj` (SQLite packages), `src/NzbDrone.Core/Radarr.Core.csproj` (Npgsql), `src/NzbDrone.Core/Datastore/DbFactory.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/PostgresOptions.cs` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Radarr implements its own in-process workflow orchestration via the `CommandQueue` and `CommandExecutor` pattern (`src/NzbDrone.Core/Messaging/Commands/`). Commands are queued, prioritized, and executed with exclusivity/concurrency controls. The `TaskManager` (`src/NzbDrone.Core/Jobs/TaskManager.cs`) schedules recurring tasks (RSS sync, movie refresh, backups, health checks). This is a structured state machine in code but not a dedicated orchestration service. |
| **Gap** | Workflow orchestration is entirely in application code — no dedicated service like AWS Step Functions or Temporal. The `CommandQueue` implements priority, exclusivity, and disk-access concurrency controls manually rather than using a managed orchestrator. |
| **Recommendation** | Migrate the command queue pattern to AWS Step Functions for multi-step workflows (search → evaluate → grab → download → import → organize). Step Functions would provide visual workflow management, built-in retry/error handling, and state persistence. Use Amazon EventBridge (preferred) to trigger workflows from events. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Radarr uses an in-process `EventAggregator` (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) for event-driven communication within the application. Events are published synchronously to `IHandle<T>` handlers and asynchronously to `IHandleAsync<T>` handlers via `TaskFactory`. This provides structured internal messaging but no cross-process or managed messaging infrastructure. No SQS, SNS, EventBridge, Kafka, or RabbitMQ usage detected. |
| **Gap** | Internal event aggregator provides async patterns within the process, but state changes that cross service boundaries (if decomposed) would require managed messaging. Currently, all messaging is in-process only. Using the stateful-crud rubric: managed messaging exists in concept (event aggregator) but not via managed AWS services. |
| **Recommendation** | Migrate the `EventAggregator` pattern to Amazon EventBridge (preferred) for cross-service event routing. Events like `MovieAddedEvent`, `DownloadCompletedEvent`, `MovieFileImportedEvent` are natural candidates for EventBridge event buses. Avoid self-managed Kafka (as specified in preferences). |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Messaging/Events/IHandle.cs`, `src/NzbDrone.Core/Datastore/Events/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation definitions exist. The application runs as a self-hosted web server using Kestrel, binding directly to a configurable port (default 7878). The `Startup.cs` configures forwarded headers for reverse proxy support (recognizing private network ranges 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) but no cloud networking is defined. |
| **Gap** | No cloud network security architecture. The application is exposed directly on the host network. |
| **Recommendation** | When deploying to AWS, place the application in private subnets within a VPC. Use Amazon API Gateway (preferred) as the public entry point with security groups limiting backend access. Implement VPC endpoints for AWS service access. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (ForwardedHeaders config), absence of any VPC/security group IaC |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront is configured. The application exposes its REST API directly via ASP.NET Core Kestrel with built-in routing, CORS, and authentication middleware. Swagger/OpenAPI docs are served from the built-in server in debug mode. |
| **Gap** | No managed API entry point providing throttling, WAF protection, or centralized request validation. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the front door. Configure throttling, request validation, and API key management at the gateway level. Use CloudFront for static frontend assets. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (app.UseEndpoints, Swagger config), `src/Radarr.Api.V3/openapi.json` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application runs as a single process on user-provisioned hardware. No ASG, ECS service scaling, Lambda concurrency, or DynamoDB auto-scaling definitions found. |
| **Gap** | All capacity is statically provisioned by the end user. |
| **Recommendation** | When containerized on EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on CPU and request metrics. For Aurora PostgreSQL (preferred), enable Aurora Auto Scaling for read replicas. |
| **Evidence** | Absence of any auto-scaling IaC or configuration |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Radarr has a built-in backup system (`src/NzbDrone.Core/Backup/BackupService.cs`) that creates scheduled zip backups of the SQLite database and config file. Backup intervals are configurable (1-7 days) with retention policies. Restore functionality exists. However, this is application-level backup only — no cloud backup services (AWS Backup, S3 Object Lock, PITR) are configured. PostgreSQL backups are not handled by the application. |
| **Gap** | Application-level backups exist for SQLite but no PITR, no cross-region replication, no PostgreSQL backup management, and no cloud backup infrastructure. Restore procedures are not documented or tested in CI. |
| **Recommendation** | When migrating to Aurora PostgreSQL (preferred), leverage automated backups with PITR. Configure AWS Backup plans for comprehensive data protection. Enable S3 versioning for any object storage. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, `src/NzbDrone.Core/Backup/BackupCommand.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` (scheduled backup task) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ or high availability configuration. Radarr is designed as a single-instance application — the `SingleInstancePolicy` in `Startup.cs` explicitly prevents multiple instances from running simultaneously. The SQLite database is a single-writer, file-based database with no replication. |
| **Gap** | Single-instance design with no fault isolation. An AZ failure or host failure takes down the entire application. |
| **Recommendation** | When containerized on EKS (preferred), deploy across multiple AZs with Aurora PostgreSQL (preferred) Multi-AZ for database failover. The application's PostgreSQL support already enables external database HA. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (EnsureSingleInstance), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (single SQLite file) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files found in the repository. No Terraform (`.tf`), CloudFormation (`.cfn.yaml`), CDK (`cdk.json`), Helm (`Chart.yaml`), or Kustomize (`kustomization.yaml`) files exist. All infrastructure is manually provisioned by end users or community maintainers. |
| **Gap** | 0% IaC coverage. All infrastructure is ClickOps or manual configuration. |
| **Recommendation** | Create IaC definitions using AWS CDK (TypeScript or C#) or Terraform for the target cloud architecture: EKS cluster, Aurora PostgreSQL, API Gateway, EventBridge, VPC networking, and IAM roles. Start with the compute and database layers. |
| **Evidence** | File system search for `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` returned no results |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD pipeline via Azure Pipelines (`azure-pipelines.yml`): multi-stage pipeline with Setup → Build Backend (Windows/Linux/Mac) → Build Frontend → Packages → Installer → Unit Tests (native + Docker/Alpine + PostgreSQL 14/15) → Integration Tests (native + Docker + PostgreSQL 14/15 + FreeBSD) → Automation Tests → Analyze (SonarCloud backend + frontend, lint) → Report. GitHub Actions CI (`.github/workflows/ci.yml`) provides additional build validation. Sentry source map uploads on release branches. |
| **Gap** | Build and test stages are fully automated, but no automated deployment to production exists. Packages are built and distributed for manual installation. No automated rollback mechanism. The pipeline is a build-and-package pipeline, not a deploy pipeline. |
| **Recommendation** | Extend the pipeline with deployment stages — add EKS/Helm deployment via CodeDeploy or ArgoCD for blue/green rollouts. Keep the existing multi-platform packaging for community distribution alongside the cloud deployment pipeline. |
| **Evidence** | `azure-pipelines.yml` (full pipeline definition), `.github/workflows/ci.yml`, `.github/dependabot.yml`, `build.sh`, `test.sh` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Backend: C# on .NET 8.0 (SDK 8.0.405 per `global.json`). Frontend: TypeScript/JavaScript with React 18.3.1. C# has good AWS SDK coverage (AWSSDK.* NuGet packages available) with a narrower but functional cloud-native tooling ecosystem compared to Python/TypeScript/Go. TypeScript frontend scores 4 (first-class AWS SDK/CDK support) but the primary application language is C#. |
| **Gap** | C# has good AWS SDK support but a narrower cloud-native tooling ecosystem (fewer Lambda layers, CDK construct libraries, and community examples compared to TypeScript/Python). |
| **Recommendation** | No language migration needed. C# on .NET 8.0 is fully supported on EKS, Lambda (.NET 8 runtime), and all AWS services. Consider using AWS CDK for C# to keep the IaC in the same language as the application. |
| **Evidence** | `global.json` (.NET 8.0.405), `src/Directory.Build.props` (TargetFrameworks=net8.0), `package.json` (TypeScript 5.7.2, React 18.3.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Radarr is a single deployable unit (`Radarr.sln` → one application binary). The codebase has clear namespace/module boundaries — `NzbDrone.Core` contains ~50 subdirectories organized by domain (Movies, Indexers, Download, Notifications, MediaFiles, etc.), with a shared `Datastore` layer. However, all modules share a single database (SQLite or PostgreSQL), communicate via in-process events and direct method calls, and are wired together through a single DryIoc DI container. The `Radarr.Host` project references all other projects and serves as the single entry point. |
| **Gap** | Monolith with identifiable modules but shared database schemas, direct cross-module data access, and a single deployment unit. Modules cannot be independently deployed, scaled, or developed. |
| **Recommendation** | Adopt a Strangler Fig decomposition approach (see Decomposition Strategy section). Start by containerizing the monolith, then extract high-value services (Indexer Search, Download Orchestration, Notification) one at a time behind an Anti-corruption Layer. |
| **Evidence** | `src/Radarr.sln`, `src/NzbDrone.Host/Radarr.Host.csproj` (references all projects), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (shared DB), `src/NzbDrone.Host/Startup.cs` (single DI container) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | External communication with TMDb API, indexer APIs, download client APIs, and notification services is primarily synchronous HTTP (via `HttpClient`). Internal communication uses the `EventAggregator` with sync `IHandle<T>` and async `IHandleAsync<T>` handlers — this provides some async patterns within the process. The `CommandQueue` provides internal async job processing with priority queuing. Using the stateful-crud rubric: primarily synchronous with some async for background jobs — limited async for cross-service state propagation. |
| **Gap** | No managed messaging (SQS, SNS, EventBridge) for cross-service state changes. All external calls are synchronous HTTP. The internal event aggregator provides in-process async but would not survive a process restart. |
| **Recommendation** | When decomposing, migrate the `EventAggregator` pattern to Amazon EventBridge (preferred) for cross-service events. Use SQS for reliable command delivery between services. Keep synchronous HTTP for read operations where appropriate. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Http/` (HTTP clients) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Radarr handles long-running operations through its internal `CommandQueue` system (`src/NzbDrone.Core/Messaging/Commands/`). Operations like movie searches, download monitoring, media file imports, and library refreshes are queued as commands and executed asynchronously by the `CommandExecutor`. The API exposes a `/api/v3/command` endpoint for triggering and polling command status. SignalR (`NzbDrone.SignalR`) provides real-time updates to the UI for progress tracking. The `TaskManager` schedules recurring long-running tasks (RSS sync, movie refresh, backup). |
| **Gap** | Long-running operations are handled async with status tracking, but the queue is in-memory (not durable). A process restart loses queued commands. No managed orchestration for multi-step workflows. |
| **Recommendation** | Migrate the command queue to AWS Step Functions for durable, managed workflow orchestration. Use SQS for durable command delivery. The existing `/api/v3/command` polling pattern maps well to Step Functions execution ARN status polling. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.SignalR/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The API uses a consistent `/api/v3/` URL prefix across all endpoints. The OpenAPI spec (`src/Radarr.Api.V3/openapi.json`, v3.0.0) documents all endpoints under the `/api/v3/` path. The API version is embedded in the project namespace (`Radarr.Api.V3`). Swagger documentation is generated via `Swashbuckle.AspNetCore`. The versioning convention is applied consistently to all endpoints. |
| **Gap** | Versioning is present and consistent, but no backward compatibility guarantees or deprecation policies are documented. Only one active version (v3) exists. |
| **Recommendation** | Document backward compatibility guarantees and a deprecation policy. When deploying behind API Gateway (preferred), use Gateway-level versioning to support multiple API versions simultaneously. |
| **Evidence** | `src/Radarr.Api.V3/openapi.json` (all paths prefixed `/api/v3/`), `src/Radarr.Api.V3/Radarr.Api.V3.csproj`, `src/NzbDrone.Host/Startup.cs` (Swagger config with v3 doc) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | External service endpoints (indexers, download clients, notification targets) are configured by the user through the UI and stored in the database. These are essentially environment/config-based endpoints — no dynamic service discovery, service registry, or service mesh is in use. Internal module communication is via direct DI injection (no service discovery needed for a monolith). |
| **Gap** | No dynamic service discovery. External service endpoints are user-configured and stored in the database. This works for a self-hosted monolith but would need service discovery when decomposed into microservices. |
| **Recommendation** | When decomposing into microservices on EKS (preferred), use Kubernetes native service discovery (DNS-based) or AWS Cloud Map for service registration. For external integrations (indexers, download clients), continue using configuration-based endpoints. |
| **Evidence** | `src/NzbDrone.Core/Indexers/` (user-configured indexer URLs), `src/NzbDrone.Core/Download/` (user-configured download client URLs), `src/NzbDrone.Core/Notifications/` (user-configured notification targets) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Media files (movies, subtitles, metadata, cover art) are stored on user-configured local file systems ("root folders"). The `RootFolders/` and `MediaFiles/` modules manage file paths on disk. Cover art is processed with `SixLabors.ImageSharp` and stored locally. No S3 integration or cloud object storage is used. FFmpeg/FFprobe (`Servarr.FFMpegCore`, `Servarr.FFprobe`) process media files from local paths. |
| **Gap** | All unstructured data (media files, cover art, subtitles) on local file systems with no cloud storage or parsing pipeline. |
| **Recommendation** | When modernizing, use Amazon S3 for media metadata and cover art storage. Consider S3 File Gateway for backward compatibility with filesystem-dependent operations. Use Amazon Textract or custom Lambda functions for metadata extraction from media files. |
| **Evidence** | `src/NzbDrone.Core/RootFolders/`, `src/NzbDrone.Core/MediaFiles/`, `src/NzbDrone.Core/MediaCover/`, `src/NzbDrone.Core/Radarr.Core.csproj` (SixLabors.ImageSharp, Servarr.FFMpegCore) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Radarr has a well-structured, centralized data access layer in `src/NzbDrone.Core/Datastore/`. The `BasicRepository<T>` base class provides standardized CRUD operations (Insert, Update, Delete, Get, Query, Paged) with Dapper ORM. All domain repositories extend `BasicRepository<T>`. The `SqlBuilder` and `WhereBuilder` (with separate SQLite and PostgreSQL variants) abstract query construction. Database type abstraction (`DatabaseType.SQLite` vs `DatabaseType.PostgreSQL`) is handled at the connection level. `TableMapping` provides centralized table/column mapping. |
| **Gap** | Mostly centralized with the `BasicRepository<T>` pattern, but some raw Dapper queries may exist in specific repositories that bypass the standard patterns. No formal data contract/schema documentation beyond migration files. |
| **Recommendation** | Document the data schema and access contracts. When decomposing, each service should own its data — split the single `BasicRepository<T>` hierarchy into per-service data access layers. The existing pattern provides a clean foundation for this split. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilder.cs`, `src/NzbDrone.Core/Datastore/TableMapping.cs`, `src/NzbDrone.Core/Datastore/DbFactory.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SQLite version is pinned via NuGet package: `SourceGear.sqlite3` v3.50.4.2, `System.Data.SQLite` v2.0.2. PostgreSQL client version is pinned: `Npgsql` v9.0.3. However, the PostgreSQL *server* version is not pinned in any IaC — it depends on whatever version the user installs. CI tests against PostgreSQL 14 and 15, but there's no mechanism to enforce a minimum version at the application level. The initial migration (`000_database_engine_version_check.cs`) suggests some version checking exists. |
| **Gap** | Client library versions are pinned via NuGet, but no PostgreSQL server version enforcement or IaC-based pinning exists. PostgreSQL 14 reaches EOL in November 2026 — not critical yet but approaching. No documented version-update procedure. |
| **Recommendation** | When migrating to Aurora PostgreSQL (preferred), pin the engine version in IaC. Add application-level PostgreSQL version checks (the migration framework already has a hook for this via `000_database_engine_version_check.cs`). Document a version-update procedure covering downtime windows and rollback. |
| **Evidence** | `src/NzbDrone.Common/Radarr.Common.csproj` (SourceGear.sqlite3 v3.50.4.2), `src/NzbDrone.Core/Radarr.Core.csproj` (Npgsql v9.0.3), `azure-pipelines.yml` (postgres:14, postgres:15 in CI), `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found. All 140+ database migrations (`src/NzbDrone.Core/Datastore/Migration/`) use FluentMigrator's C# API for schema changes. All business logic is in the C# application layer. Dapper is used for data access with parameterized queries constructed by `SqlBuilder`. No `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements found. The application supports both SQLite and PostgreSQL, requiring standard SQL without vendor-specific extensions. |
| **Gap** | None — all business logic is in the application layer. |
| **Recommendation** | Maintain this pattern. The absence of stored procedures significantly reduces database migration complexity and supports the Move to Managed Databases pathway. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (140+ FluentMigrator C# migrations), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Dapper queries), grep for CREATE PROCEDURE/TRIGGER/FUNCTION returned no results |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or centralized cloud audit logging. The application uses NLog (`NLog` v5.4.0) for application-level logging with targets including database (`DatabaseTarget.cs`), syslog (`NLog.Targets.Syslog`), and CLEF JSON format (`NLog.Layouts.ClefJsonLayout`). Sentry (`Sentry` v4.0.2) is used for error reporting. These are application-level logs, not infrastructure audit logs. |
| **Gap** | No immutable audit logging infrastructure. Application logs are useful for debugging but do not provide the compliance-grade, tamper-proof audit trail that CloudTrail provides. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Route application logs to CloudWatch Logs for centralized access. |
| **Evidence** | `src/NzbDrone.Common/Radarr.Common.csproj` (NLog, NLog.Targets.Syslog, Sentry), `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration. SQLite database files are stored unencrypted on the local filesystem. PostgreSQL encryption depends entirely on user configuration. No KMS, customer-managed keys, or encryption configuration found in the codebase. |
| **Gap** | No encryption at rest for data stores. Database files are accessible to anyone with filesystem access. |
| **Recommendation** | When migrating to Aurora PostgreSQL (preferred), encryption at rest is enabled by default with AWS-managed KMS keys. For additional security, use customer-managed KMS keys for Aurora, S3, and EBS volumes. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (no encryption parameters), absence of any KMS or encryption configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The API uses API key authentication via the `ApiKeyAuthenticationHandler` (`src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`). Keys are passed via `X-Api-Key` header, `apikey` query parameter, or `Authorization: Bearer` header. The key is a static string compared against the configured API key. Forms-based authentication is also available via `AuthenticationController`. All API endpoints require authentication by default (fallback policy requires authenticated user). This is API key / static credential authentication, not token-based OAuth2/JWT. |
| **Gap** | Static API key authentication without token-based auth (OAuth2/JWT). API keys do not expire, cannot be scoped to specific operations, and lack per-user attribution. No API Gateway-level throttling or validation. |
| **Recommendation** | When deploying behind API Gateway (preferred), implement Cognito user pools or JWT authorizers for token-based authentication. Keep API key support for backward compatibility but add OAuth2/OIDC as the primary auth mechanism. |
| **Evidence** | `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Radarr.Http/Authentication/AuthenticationController.cs`, `src/NzbDrone.Host/Startup.cs` (FallbackPolicy), `src/Radarr.Api.V3/openapi.json` (security schemes) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Radarr manages its own authentication entirely. The `UserService` and `UserRepository` (`src/NzbDrone.Core/Authentication/`) store user credentials in the local database. Password hashing uses `Microsoft.AspNetCore.Cryptography.KeyDerivation`. No OIDC, SAML, Cognito, Okta, or any external IdP integration exists. The `AuthenticationType` enum (`src/NzbDrone.Core/Authentication/AuthenticationType.cs`) supports Forms and External (reverse proxy) auth modes. |
| **Gap** | Fully self-managed authentication with no centralized IdP integration. No SSO, no federation, no external identity provider support beyond reverse proxy trust. |
| **Recommendation** | Integrate with Amazon Cognito user pools for centralized identity management. Implement OIDC support for SSO with enterprise identity providers. The existing reverse proxy auth mode (`AuthenticationType.External`) provides a partial foundation for IdP integration. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/NzbDrone.Core/Authentication/AuthenticationType.cs`, `src/NzbDrone.Core/Radarr.Core.csproj` (KeyDerivation) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The API key is generated by the application and stored in the configuration file (`Config.xml`). PostgreSQL credentials are provided via environment variables (`Radarr__Postgres__Password`). Download client credentials, indexer API keys, and notification tokens are stored in the application database. No AWS Secrets Manager, HashiCorp Vault, or dedicated secrets management system is used. Credentials are not hardcoded in source code — they are user-configured at runtime. |
| **Gap** | Secrets are stored in config files and the database without encryption or rotation. No dedicated secrets management system. No automated key rotation. |
| **Recommendation** | When deploying to AWS, store database credentials and API keys in AWS Secrets Manager with automated rotation. Use IAM roles for service-to-service authentication. Migrate environment variable secrets to Secrets Manager with EKS pod identity integration. |
| **Evidence** | `src/NzbDrone.Core/Datastore/PostgresOptions.cs` (env vars for DB creds), `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (API key from config), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or managed patching configuration. No SSM Patch Manager, AWS Inspector, Snyk, or vulnerability scanning for the runtime environment. Dependabot is configured only for devcontainer dependencies (`.github/dependabot.yml` covers `devcontainers` ecosystem only). No hardened base images are defined (no Dockerfile exists). |
| **Gap** | No patching strategy, no vulnerability scanning for the runtime environment, and no hardened images. Dependabot coverage is minimal (devcontainers only). |
| **Recommendation** | When containerizing, use a hardened base image (e.g., Bottlerocket for EKS nodes, distroless or Alpine for application containers). Enable Amazon Inspector for container vulnerability scanning. Expand Dependabot to cover `nuget` and `npm` ecosystems. Add Snyk or Trivy to the CI pipeline. |
| **Evidence** | `.github/dependabot.yml` (devcontainers only), absence of Dockerfile, SSM, or Inspector configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud analysis is integrated in Azure Pipelines for both backend (`Analyze_Backend` job with code coverage) and frontend (`Analyze_Frontend` job). StyleCop analyzers are configured for C# code style enforcement. Dependabot is configured but only for devcontainer dependencies. No SAST tools (Semgrep, CodeGuru), no container scanning (no containers), and no blocking security gates in the pipeline. SonarCloud provides some security rule coverage but is primarily a code quality tool. |
| **Gap** | SonarCloud provides partial security coverage, but no dedicated SAST tool, no dependency vulnerability scanning for NuGet/npm packages, and no blocking gates on critical findings. |
| **Recommendation** | Add `dotnet-audit` and `npm audit` to the CI pipeline. Expand Dependabot to cover `nuget` and `npm` ecosystems. Add a dedicated SAST tool (Amazon CodeGuru Reviewer or Semgrep) with blocking gates on critical findings. When containerizing, add ECR image scanning. |
| **Evidence** | `azure-pipelines.yml` (SonarCloudPrepare, SonarCloudAnalyze tasks for backend and frontend), `src/Directory.Build.props` (StyleCop.Analyzers), `.github/dependabot.yml` (devcontainers only) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No OpenTelemetry SDK, X-Ray SDK, or tracing libraries found in any dependency manifest. The application uses NLog for structured logging and Sentry for error tracking, but neither provides distributed trace propagation across service boundaries. |
| **Gap** | No distributed tracing — cannot correlate requests across the API layer, background jobs, external service calls (TMDb, indexers, download clients), and database operations. |
| **Recommendation** | Add OpenTelemetry .NET SDK (`OpenTelemetry.Extensions.Hosting`, `OpenTelemetry.Instrumentation.AspNetCore`, `OpenTelemetry.Exporter.Otlp`) to instrument the application. Export traces to AWS X-Ray or CloudWatch via the OTLP exporter. This can be done before cloud migration to establish observability early. |
| **Evidence** | `src/NzbDrone.Core/Radarr.Core.csproj`, `src/NzbDrone.Host/Radarr.Host.csproj`, `src/NzbDrone.Common/Radarr.Common.csproj` — no OpenTelemetry or X-Ray packages |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No latency targets, error budget tracking, or formal service level definitions. The application has built-in health checks (`src/NzbDrone.Core/HealthCheck/`) that monitor application health (disk space, indexer status, download client connectivity) but these are operational checks, not SLO definitions. |
| **Gap** | No formal SLOs — no definition of acceptable API latency, availability targets, or error budgets. |
| **Recommendation** | Define SLOs for critical user journeys (e.g., movie search latency < 2s at p99, API availability > 99.9%, movie import success rate > 99%). Implement SLO monitoring with CloudWatch when deployed to AWS. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational health checks, not SLOs), absence of SLO definition files |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics publishing. The `AnalyticsService` (`src/NzbDrone.Core/Analytics/AnalyticsService.cs`) exists but is minimal. Sentry captures errors and performance data. No CloudWatch custom metrics, no business KPI tracking (movies added per day, successful imports, search hit rate, download completion rate). |
| **Gap** | Infrastructure metrics only (via Sentry error rates). No business outcome metrics that would drive modernization decisions. |
| **Recommendation** | Instrument key business metrics using CloudWatch custom metrics or OpenTelemetry metrics: movies processed, search success rate, download completion time, import success rate. These metrics will validate modernization ROI. |
| **Evidence** | `src/NzbDrone.Core/Analytics/AnalyticsService.cs`, `src/NzbDrone.Common/Radarr.Common.csproj` (Sentry package) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration. The built-in health check system (`src/NzbDrone.Core/HealthCheck/`) provides application-level status checks but no threshold-based or anomaly-based alerting. Notification integrations exist (email, Discord, Slack, etc.) but are for media events (movie available, download complete), not operational alerting. |
| **Gap** | No alerting on error rates, latency, or operational metrics. Health checks are passive — they report status when queried but do not proactively alert. |
| **Recommendation** | When deployed to AWS, configure CloudWatch alarms for API error rates, latency p99, database connection failures, and queue depth. Enable CloudWatch anomaly detection on key metrics. Integrate with PagerDuty or OpsGenie for on-call alerting. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (passive health checks), `src/NzbDrone.Core/Notifications/` (media event notifications, not operational alerting) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No canary, blue/green, or rolling deployment strategy. The application is distributed as platform-specific packages for manual installation. An internal update mechanism (`src/NzbDrone.Update/`) handles self-updating — it downloads a new version, stops the application, replaces files, and restarts. This is a direct-to-production replacement with no staged rollout, no traffic shifting, and no automatic rollback. |
| **Gap** | Direct-to-production deployment with no staged rollout. The update mechanism is a binary replacement, not a controlled deployment strategy. |
| **Recommendation** | When deploying to EKS (preferred), implement blue/green deployments using AWS CodeDeploy with EKS integration or Argo Rollouts. Configure health check-based automatic rollback. Keep the self-update mechanism for community/self-hosted distribution. |
| **Evidence** | `src/NzbDrone.Update/` (binary replacement updater), `azure-pipelines.yml` (Packages stage creates archives, no deployment stage), `build.sh` (packaging only) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration test suite in `src/NzbDrone.Integration.Test/` with API tests covering critical workflows: movies, collections, history, downloads, indexers, notifications, queue, releases, blocklist, calendar, and more. Tests run in the Azure Pipelines `Integration` stage across Windows, macOS, Linux, FreeBSD, and Docker/Alpine. PostgreSQL-specific integration tests run against Postgres 14 and 15. Automation tests (`src/NzbDrone.Automation.Test/`) provide browser-based UI testing. All tests run in CI on every build. |
| **Gap** | Integration tests cover primary API workflows but may not cover all edge cases. Contract tests between the frontend and API are not explicitly defined. Some platform-specific tests (FreeBSD) have relaxed failure requirements. |
| **Recommendation** | Add API contract tests (e.g., using Pact) to validate the OpenAPI spec against actual API behavior. Expand integration tests to cover decomposition scenarios (when services are extracted). The existing test infrastructure is a significant strength for safe modernization. |
| **Evidence** | `src/NzbDrone.Integration.Test/ApiTests/` (18+ test fixtures), `src/NzbDrone.Automation.Test/` (UI automation), `azure-pipelines.yml` (Integration, Automation stages), `test.sh` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation, runbooks, or self-healing patterns. No Systems Manager Automation documents, Lambda-based remediation, or Step Functions incident workflows. The application has a `SECURITY.md` with a vulnerability reporting process (Discord or email) but no operational incident response procedures. |
| **Gap** | Incident response is entirely ad hoc. No runbooks, no automated remediation, no escalation procedures. |
| **Recommendation** | Create runbooks for common operational scenarios (database connectivity loss, disk space exhaustion, update failure). Implement as SSM Automation documents or markdown runbooks in the repository. Add self-healing patterns (e.g., automatic restart on health check failure) when containerized. |
| **Evidence** | `SECURITY.md` (vulnerability reporting only), absence of runbook files, SSM documents, or remediation Lambda functions |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-service dashboards, named alarm owners, or SLO definitions with team attribution. The health check system (`src/NzbDrone.Core/HealthCheck/`) provides application-level status but with no team ownership. No CODEOWNERS file referencing observability assets. The project has a `CONTRIBUTING.md` for development but no on-call or observability ownership documentation. |
| **Gap** | No observability ownership model. Monitoring is reactive and fragmented. |
| **Recommendation** | Establish observability ownership by creating per-service dashboards (when decomposed) with named owners. Add a CODEOWNERS file for alerting/monitoring configurations. Define on-call rotation and escalation policies. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (no team attribution), absence of CODEOWNERS for observability, `CONTRIBUTING.md` (development only) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources exist, therefore no resource tagging. No tagging standards, no `default_tags` in Terraform (no Terraform exists), no tag policies, no cost allocation tags. |
| **Gap** | No tagging governance — no cloud resources exist to tag. |
| **Recommendation** | When creating IaC, establish a tagging standard from day one. Define required tags: `Environment`, `Service`, `Owner`, `CostCenter`, `Project`. Implement via CDK/Terraform `default_tags` and enforce with AWS Config rules and Tag Policies. |
| **Evidence** | Absence of any IaC or cloud resource definitions |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `azure-pipelines.yml` | INF-Q1, INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7, DATA-Q3 | Full CI/CD pipeline definition with build, test, package, and analysis stages |
| `.github/workflows/ci.yml` | INF-Q11 | GitHub Actions build pipeline |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Dependabot configuration (devcontainers only) |
| `build.sh` | INF-Q1, INF-Q11 | Build script with multi-platform packaging |
| `test.sh` | OPS-Q6 | Test execution script for unit, integration, and automation tests |
| `global.json` | APP-Q1 | .NET SDK version (8.0.405) |
| `package.json` | APP-Q1 | Frontend dependencies (React, TypeScript) |
| `src/Directory.Build.props` | INF-Q1, APP-Q1 | Build configuration, RuntimeIdentifiers, StyleCop |
| `src/NuGet.config` | APP-Q1 | NuGet package sources |
| `src/Radarr.sln` | APP-Q2 | Solution file — single deployable unit |
| `src/NzbDrone.Core/Radarr.Core.csproj` | INF-Q2, APP-Q1, DATA-Q3, OPS-Q1, SEC-Q1 | Core project dependencies (Npgsql, Dapper, FluentMigrator, NLog) |
| `src/NzbDrone.Host/Radarr.Host.csproj` | APP-Q2, OPS-Q1 | Host project with all project references |
| `src/NzbDrone.Common/Radarr.Common.csproj` | INF-Q2, SEC-Q1, OPS-Q1 | Common dependencies (SQLite, NLog, Sentry) |
| `src/Radarr.Api.V3/Radarr.Api.V3.csproj` | APP-Q5 | API project with Swashbuckle |
| `src/Radarr.Api.V3/openapi.json` | APP-Q5, INF-Q6, SEC-Q3 | OpenAPI 3.0.4 specification (12,843 lines) |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, INF-Q9, APP-Q2, SEC-Q3 | Application startup, routing, auth, Swagger config |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | INF-Q2 | Database factory (SQLite/PostgreSQL) |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2, SEC-Q2, SEC-Q5 | Connection string configuration |
| `src/NzbDrone.Core/Datastore/PostgresOptions.cs` | INF-Q2, SEC-Q5 | PostgreSQL env var configuration |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | APP-Q2, DATA-Q2 | Centralized repository pattern with Dapper |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 140+ FluentMigrator migrations (C#, no SQL) |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | INF-Q4, APP-Q3 | In-process event aggregator (sync + async handlers) |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` | INF-Q3, APP-Q3, APP-Q4 | Internal command queue with priority/exclusivity |
| `src/NzbDrone.Core/Jobs/TaskManager.cs` | INF-Q3, INF-Q8, APP-Q4 | Scheduled task management |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Built-in backup system with retention |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q4, OPS-Q8 | Application health check framework |
| `src/NzbDrone.Core/Analytics/AnalyticsService.cs` | OPS-Q3 | Minimal analytics |
| `src/NzbDrone.Core/Instrumentation/` | SEC-Q1, OPS-Q1 | NLog, Sentry, database logging |
| `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key authentication handler |
| `src/NzbDrone.Core/Authentication/` | SEC-Q4 | Self-managed user authentication |
| `src/NzbDrone.Core/Notifications/` | APP-Q6, OPS-Q4 | External notification integrations |
| `src/NzbDrone.Core/Indexers/` | APP-Q6 | External indexer integrations |
| `src/NzbDrone.Core/Download/` | APP-Q6 | Download client integrations |
| `src/NzbDrone.Core/RootFolders/` | DATA-Q1 | Local filesystem root folder management |
| `src/NzbDrone.Core/MediaFiles/` | DATA-Q1 | Media file management on local filesystem |
| `src/NzbDrone.Core/MediaCover/` | DATA-Q1 | Cover art storage |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test suite |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | UI automation test suite |
| `src/NzbDrone.Update/` | OPS-Q5 | Binary replacement update mechanism |
| `SECURITY.md` | OPS-Q7 | Vulnerability reporting process |
| `README.md` | Quick Agent Wins | Repository documentation |
| `CONTRIBUTING.md` | OPS-Q8 | Contribution guidelines |
