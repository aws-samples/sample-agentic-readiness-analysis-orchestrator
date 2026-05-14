# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | Lidarr |
| **Date** | 2025-07-15 |
| **TD Version** | 1.9.0 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Music collection manager (*arr suite). |
| **Preferences** | Prefer: EKS, Aurora, DynamoDB, API Gateway, EventBridge, Bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **1.84 / 4.0** |

**Archetype Justification**: Lidarr owns a persistent database (SQLite by default, optional PostgreSQL) and exposes full CRUD operations on artists, albums, tracks, and related entities via a REST API. The application manages entity lifecycle (create, update, delete), user-specific configurations, and write-heavy operations alongside reads. Classified as `stateful-crud`.

> **Note:** Repo type is `monorepo` but Lidarr is effectively a single application with a C# backend and a React/TypeScript frontend in one repository. All 37 questions are evaluated against the single application.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.40 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.84 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure is manually provisioned or user-managed. | Blocks reproducible deployments, automated provisioning, and disaster recovery. Foundation for all modernization pathways. |
| 2 | INF-Q1: Managed Compute | 1 | Application distributed as self-hosted binaries on bare metal/VMs. No managed container orchestration or serverless. | Prevents elastic scaling, increases operational burden, and blocks containerization pathway. |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or cloud-native audit logging. Only internal NLog to files and database. | No compliance-grade audit trail. Forensic analysis after incidents is limited to local logs. |
| 4 | OPS-Q5: Deployment Strategy | 1 | No staged deployment. Users manually download and install binary updates. | No ability to detect regressions before all users are affected. No rollback mechanism beyond manual reinstall. |
| 5 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation. Kestrel directly exposed on the host network. | No blast radius containment. API is accessible to anyone on the network without infrastructure-level isolation. |

---

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 3) and structured JSON responses detected. OpenAPI 3.0.4 specification at `src/Lidarr.Api.V1/openapi.json` with full endpoint coverage for albums, artists, tracks, queue, history, calendar, and system management.
- **What it enables:** An API-aware agent can discover and invoke Lidarr's REST API endpoints as tools — querying artist libraries, triggering searches, managing download queues, and configuring notification targets via natural language.
- **Additional steps:** The OpenAPI spec is already comprehensive. Minor cleanup may be needed for agent tool descriptions (adding `summary` and `description` fields to operations that lack them). Deploy an agent gateway (e.g., Amazon Bedrock Agents) that reads the OpenAPI spec.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). Azure Pipelines with comprehensive build, test, and packaging stages.
- **What it enables:** A DevOps agent can trigger builds, check pipeline status, review test results, and coordinate release packaging across the 12+ platform targets.
- **Additional steps:** Azure DevOps API access would need to be configured. Pipeline status could be exposed via a webhook or the Azure DevOps REST API. Consider migrating to GitHub Actions to align with preferred AWS ecosystem (CodePipeline / CodeBuild).
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — README.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, CLA.md, and extensive code comments across the codebase.
- **What it enables:** A RAG-based knowledge agent can index the existing documentation, code comments, and API spec to answer developer questions about Lidarr's architecture, contribution guidelines, and API usage.
- **Additional steps:** Index README, CONTRIBUTING, API docs, and code comments into a vector store (Amazon Bedrock Knowledge Bases with OpenSearch Serverless). Connect to a Bedrock-powered chat interface.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolith), INF-Q1 = 1 (no managed compute), APP-Q3 = 2 (sync-heavy) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (bare metal/VM), no Dockerfiles or container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures), databases are already open source (SQLite, PostgreSQL) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed), DATA-Q3 = 2 (version lifecycle gaps) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing, streaming, or analytics workloads detected. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 2 (partial CI/CD, no deployment automation), OPS-Q5 = 1 (no staged deploys) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Music collection manager (*arr suite)") |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:**
Lidarr is a tightly-coupled monolithic application where all functionality — REST API, media management, download client orchestration, metadata refresh, notification delivery, indexer search, and background job scheduling — runs in a single .NET 8 process. The `src/NzbDrone.Core/` project contains all domain logic with inter-module dependencies through a shared in-process event aggregator.

**Compute Model Gaps:**
The application runs as a self-hosted binary on user machines (Windows, Linux, macOS, FreeBSD). There is no managed compute infrastructure — no ECS, EKS, Lambda, or Fargate definitions exist. All compute provisioning is manual.

**Communication Pattern Gaps:**
All external communication is synchronous HTTP (download clients, indexers, metadata providers). Internal communication uses an in-process `EventAggregator` with no external messaging infrastructure. SignalR provides real-time push to the frontend but is not an async service communication pattern.

**Recommended Decomposition Approach:**
See Decomposition Strategy section below. The Strangler Fig (Parallel Track) approach is recommended, with initial containerization as a first step.

**Representative AWS Services:** ECS on Fargate (preferred via EKS per preferences), API Gateway, EventBridge, Step Functions, DynamoDB/Aurora (per preferences)

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Hexagonal Architecture

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Decomposing monoliths into microservices](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:**
Lidarr is distributed as platform-specific binary packages (ZIP, tar.gz, DMG, Windows installer) built by Azure Pipelines. No Dockerfiles, docker-compose files, or Kubernetes manifests exist in the repository. The community provides unofficial Docker images, but the project itself has no container-first distribution.

**Container Readiness Indicators:**
- ✅ .NET 8.0 is fully container-compatible with official Microsoft base images
- ✅ Multi-platform builds already produce Linux x64 and Linux musl (Alpine) binaries
- ✅ Application reads configuration from environment variables (`Lidarr__Postgres__*`)
- ✅ Data directory is configurable via command-line arguments
- ⚠️ SQLite default requires volume mounts for persistence
- ⚠️ Media file access requires host volume mounts

**Recommended Container Orchestration:**
Per preferences, EKS is recommended over self-managed Kubernetes. For a single application like Lidarr, ECS on Fargate offers lower operational overhead. If the team prefers Kubernetes, EKS with Fargate profiles eliminates node management.

**Migration Approach:**
1. Create a Dockerfile using `mcr.microsoft.com/dotnet/aspnet:8.0` base image
2. Publish the application as a self-contained single-file deployment
3. Configure volume mounts for media library and database persistence
4. Migrate from SQLite to Aurora PostgreSQL (per preferences) to externalize state
5. Deploy to EKS/ECS with appropriate health checks and resource limits

**Representative AWS Services:** ECR, EKS (preferred), ECS, Fargate, App Runner

**AWS Prescriptive Guidance:**
- [Containerizing .NET applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-containers/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
Lidarr uses embedded SQLite as the default database (file-based, no server process) with optional PostgreSQL support configured via environment variables. Both options are entirely self-managed by the end user:
- **SQLite:** File stored in the application data directory. No automated backups, no failover, no encryption at rest. Single-writer limitation.
- **PostgreSQL:** User-provisioned. Application connects via `Npgsql` with credentials in environment variables. No version enforcement, no managed failover.

**Engine Versions:**
- SQLite: `SourceGear.sqlite3 3.50.4.2` (pinned via NuGet, current)
- PostgreSQL: Not pinned by the application — depends on user's installation. CI tests against PostgreSQL 14 and 15.

**Data Access Patterns:**
The centralized `BasicRepository<T>` pattern with Dapper ORM and database-type-specific SQL builders (`WhereBuilderPostgres`, `WhereBuilderSqlite`) provides a clean abstraction that would ease migration. The `DatabaseType` enum already supports switching between SQLite and PostgreSQL at runtime.

**Recommended Managed Database Targets:**
Per preferences, **Aurora PostgreSQL** is the primary recommendation. The existing PostgreSQL support in the codebase means no application code changes are needed — only the connection string needs to point to an Aurora cluster. Aurora provides automated backups, Multi-AZ failover, auto-scaling read replicas, and encryption at rest with KMS.

For the media metadata and configuration data that currently uses SQLite, migrating to Aurora PostgreSQL consolidates data management. For high-throughput use cases (if scaling beyond single-instance), **DynamoDB** (per preferences) could serve queue state and command tracking.

**Migration Tools:** AWS DMS for data migration, Aurora PostgreSQL-compatible endpoint

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 1):** Zero infrastructure-as-code. No Terraform, CloudFormation, CDK, Helm, or any IaC definitions exist. All infrastructure (if any cloud deployment exists) is manually provisioned.
- **CI/CD (INF-Q11 = 2):** Azure Pipelines provides comprehensive build and test automation (unit tests, integration tests, automation tests across Windows/Linux/macOS/FreeBSD, SonarCloud analysis). However, there is no deployment pipeline — the pipeline produces binary artifacts that are manually distributed.
- **Deployment Strategy (OPS-Q5 = 1):** No staged deployment. Users manually download new versions. No canary, blue/green, or rolling update capability.
- **Integration Testing (OPS-Q6 = 3):** Strong integration test suite covering multiple platforms and database engines.

**Recommended DevOps Toolchain:**
1. **IaC:** Define infrastructure using CDK or Terraform — EKS cluster, Aurora PostgreSQL, API Gateway, VPC networking, security groups
2. **CI/CD Migration:** Consider GitHub Actions (already has `.github/workflows/` directory) or AWS CodePipeline/CodeBuild. The Azure Pipelines configuration is comprehensive and can serve as the blueprint.
3. **Deployment Automation:** Implement blue/green deployments via CodeDeploy or EKS rolling updates. Use API Gateway canary deployments for staged rollout.
4. **GitOps:** If EKS is adopted, ArgoCD or Flux can manage Kubernetes deployments from Git.

**Representative AWS Services:** CodePipeline, CodeBuild, CodeDeploy, CDK, CloudFormation, ECR, X-Ray, CloudWatch

**AWS Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://aws.amazon.com/devops/getting-started/)
- [CI/CD pipeline for EKS](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/set-up-a-ci-cd-pipeline-for-an-amazon-eks-cluster.html)

---

## Decomposition Strategy

> **Condition:** APP-Q2 = 2 (monolith with identifiable modules but shared database and tight coupling)

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping Lidarr running. New features built as services; existing features migrated over time. | APP-Q2 = 2 — Lidarr has identifiable domain boundaries (Artist management, Album/Track management, Download orchestration, Notification delivery, Indexer search, Media processing, Import/Export, Queue management). | **Medium to High** — 6-18 months | ✅ **Recommended.** Lowest risk, incremental value delivery. |
| **Conditional / Adaptive** | Containerize Lidarr as-is first (lift-and-containerize), then selectively extract high-value modules based on scaling needs. | Lidarr is functional as a monolith — containerization provides immediate cloud benefits without architectural redesign. | **Low to Medium** — containerization in 2-4 weeks, selective extraction over 3-12 months | ✅ **Recommended as Phase 1** — containerize first, decompose selectively. |
| **Big-Bang Rewrite** | Rewrite as microservices from scratch. | Not recommended for Lidarr — the monolith is functional and well-structured. | **Very High** — 12-24+ months | ⚠️ **Not recommended.** |

### Recommended Strategy: Conditional / Adaptive (Phase 1) → Strangler Fig (Phase 2)

**Phase 1 — Containerize the Monolith (2-4 weeks):**
1. Create a Dockerfile for the existing Lidarr application
2. Replace SQLite with Aurora PostgreSQL (externalize persistent state)
3. Deploy to EKS (per preferences) with proper health checks
4. Set up IaC (CDK/Terraform) for the EKS cluster and Aurora database
5. Configure API Gateway as the entry point

**Phase 2 — Selective Service Extraction (3-12 months):**
Extract modules that would benefit from independent scaling:
1. **Notification Service** — Low-risk extraction. Notification delivery (Email, Slack, Discord, Telegram, etc.) is loosely coupled. Use EventBridge (per preferences) for event-driven notification dispatch.
2. **Indexer Search Service** — Independent search against external indexers (Newznab, Torznab). Can scale independently and retry without affecting the main application.
3. **Download Client Orchestration** — Manages interactions with download clients (SABnzbd, NZBGet, qBittorrent, Transmission). Extract behind an Anti-corruption Layer.

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the monolith's data model | Every extraction — prevent monolith's schema from leaking into new services |
| **Saga Pattern** | Manage distributed transactions across services | When extracting download orchestration (search → grab → download → import flow) |
| **Event Sourcing** | Capture state changes as events | For the notification pipeline — events from state changes trigger notifications |
| **Hexagonal Architecture** | Clear boundaries between business logic and infrastructure | Every new service — ensures portability and testability |

### Effort Estimation Factors

| Factor | Lidarr Analysis | Effort Impact |
|--------|-------------------|---------------|
| Module boundaries | Identifiable domains (Artist, Album, Download, Notification, Indexer, Media) but shared through `NzbDrone.Core` namespace | Medium |
| Data coupling | Single SQLite/PostgreSQL database with shared schema. All entities in one database. | High |
| Stored procedures | None — all business logic in C# | Low (positive) |
| Communication patterns | All synchronous with in-process EventAggregator | Medium |
| CI/CD maturity | Build pipeline exists but no deployment automation | Medium |
| Test coverage | Strong integration and automation test suites | Low (positive) |

**Calibrated Estimate:** Phase 1 (containerization): 2-4 weeks. Phase 2 (selective extraction of 2-3 services): 6-12 months.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr is distributed as self-hosted binary packages for Windows (ZIP, installer), Linux (tar.gz, Debian package), macOS (tar.gz, app bundle), and FreeBSD. No cloud compute infrastructure is defined — no Terraform, CloudFormation, CDK, or Helm definitions for ECS, EKS, Lambda, Fargate, or EC2 exist. The `azure-pipelines.yml` builds platform-specific binaries that users install manually on their own hardware. The application runs as a standalone Kestrel web server process. |
| **Gap** | All compute is user-managed on bare metal or VMs. No managed container orchestration or serverless infrastructure. |
| **Recommendation** | Containerize the application using the existing Linux musl (Alpine) build target and deploy to EKS (per preferences) or ECS on Fargate. The .NET 8 runtime is fully container-compatible. Start with a single-container deployment and evolve toward managed orchestration. |
| **Evidence** | `azure-pipelines.yml` (build stages), `distribution/` (packaging configs), `build.sh`, absence of Dockerfile/docker-compose/Helm/Terraform files |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr uses embedded SQLite as the default database (`SourceGear.sqlite3 3.50.4.2`, `System.Data.SQLite 2.0.2` in `Lidarr.Common.csproj`) with optional self-managed PostgreSQL support (`Npgsql 9.0.3` in `Lidarr.Core.csproj`). The `ConnectionStringFactory.cs` builds SQLite connections to local files or PostgreSQL connections from environment variables (`Lidarr__Postgres__Host`, `Lidarr__Postgres__Port`, `Lidarr__Postgres__User`, `Lidarr__Postgres__Password`). Both options are entirely self-managed. No managed database IaC (RDS, Aurora, DynamoDB) exists. |
| **Gap** | All databases are self-managed. SQLite provides no failover, no automated backups, and single-writer limitation. PostgreSQL, when used, is user-provisioned with no managed service wrapper. |
| **Recommendation** | Migrate to Aurora PostgreSQL (per preferences) for the primary data store. The existing PostgreSQL code path in `ConnectionStringFactory.cs` means no application code changes are needed — only the connection string needs to point to an Aurora cluster. Aurora provides automated backups, Multi-AZ failover, and encryption at rest. |
| **Evidence** | `src/NzbDrone.Common/Lidarr.Common.csproj` (SQLite packages), `src/NzbDrone.Core/Lidarr.Core.csproj` (Npgsql), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/PostgresOptions.cs` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr implements an internal command queue system (`CommandQueue.cs`, `CommandQueueManager.cs`, `CommandExecutor.cs`) with a `TaskManager.cs` scheduler that manages background jobs (download monitoring, artist refresh, RSS sync, backup, health checks, housekeeping). The command queue supports priority ordering, exclusive execution, disk-access coordination, and long-running process isolation. This is a structured in-code state machine with retry logic (via Polly in `BasicRepository.cs`) but no dedicated external workflow orchestration service (Step Functions, Temporal, MWAA). |
| **Gap** | Workflow orchestration exists as hardcoded application logic with some structure (priority queues, exclusive locks, scheduling). No dedicated orchestration service provides visual workflow management, external retry policies, or state persistence independent of the application. |
| **Recommendation** | For the `stateful-crud` archetype, the current command queue is partially adequate. When migrating to AWS, consider Step Functions for the multi-step workflows (search → grab → download → import → rename → notify) to gain visual debugging, automatic retry with backoff, and state persistence. EventBridge (per preferences) can replace the in-process `EventAggregator` for cross-service event routing. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr uses an in-process `EventAggregator` (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) for internal async event handling. The EventAggregator supports synchronous handlers (`IHandle<TEvent>`) and async handlers (`IHandleAsync<TEvent>`) dispatched via `TaskFactory`. SignalR provides real-time push notifications to the frontend. However, there is no external messaging infrastructure — no SQS, SNS, EventBridge, Kafka, or RabbitMQ. All cross-boundary communication (to download clients, indexers, notification targets) is synchronous HTTP. |
| **Gap** | For a `stateful-crud` archetype, cross-service state changes should use managed messaging. The in-process EventAggregator is not durable — events are lost on process crash. No external messaging exists for decoupled state change propagation. |
| **Recommendation** | When containerizing and potentially decomposing, introduce EventBridge (per preferences) for durable event delivery across service boundaries. Replace the in-process EventAggregator with EventBridge events for notifications and state change propagation. Avoid self-managed Kafka or RabbitMQ (per preferences). |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Messaging/Events/IEventAggregator.cs`, `src/NzbDrone.Core/Messaging/Events/IHandle.cs`, absence of SQS/SNS/EventBridge/Kafka/RabbitMQ references |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation is defined. The application runs directly on the host network with Kestrel binding to a configurable port (default 8686). The `Startup.cs` configures `ForwardedHeaders` for proxy support (indicating reverse proxy awareness) and allows CORS from any origin (`AllowAnyOrigin()`). No infrastructure-level network isolation exists. |
| **Gap** | Services deployed directly on user machines with no network segmentation. No VPC, private subnets, or security groups. The CORS policy allows any origin, which is intentional for a self-hosted app but inappropriate for cloud deployment. |
| **Recommendation** | When migrating to AWS, deploy within a VPC with private subnets. Place the application in private subnets with an API Gateway (per preferences) as the public-facing entry point. Configure security groups with least-privilege rules. Tighten CORS to specific allowed origins. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (CORS config, ForwardedHeaders), absence of VPC/security group IaC |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr's REST API is served directly by Kestrel (`Microsoft.AspNetCore`) with no API Gateway, ALB, or CloudFront in front. The `Startup.cs` configures Swagger/OpenAPI documentation at `/docs/v1/openapi.json` (debug mode only), authentication via API keys, and SignalR WebSocket at `/signalr/messages`. There is no throttling, rate limiting, WAF, or request validation at the infrastructure level. |
| **Gap** | No managed API entry point. The application is directly exposed with no infrastructure-level throttling, auth offloading, or traffic management. |
| **Recommendation** | Deploy Amazon API Gateway (per preferences) as the entry point for the REST API. API Gateway provides throttling, API key management (replacing the custom X-Api-Key implementation), request validation, and WAF integration. Use API Gateway WebSocket APIs for SignalR replacement or ALB with sticky sessions for WebSocket support. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (Kestrel configuration, Swagger setup, endpoint mapping), `src/Lidarr.Api.V1/openapi.json` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. Lidarr runs as a single-instance application by design — `Startup.cs` includes a `EnsureSingleInstance()` check that prevents multiple instances from running simultaneously. There are no ASG, ECS service scaling, Lambda concurrency, or any other scaling configuration. |
| **Gap** | All capacity is statically provisioned. The single-instance constraint prevents horizontal scaling. |
| **Recommendation** | When containerizing, configure EKS Horizontal Pod Autoscaler or ECS Service Auto Scaling. This requires removing the single-instance constraint and externalizing state (moving from SQLite to Aurora PostgreSQL). Consider Application Auto Scaling for Aurora read replicas if read traffic warrants it. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (EnsureSingleInstance), absence of auto-scaling IaC |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr implements an application-level backup system (`src/NzbDrone.Core/Backup/BackupService.cs`) that creates ZIP archives of the SQLite database files and configuration. The `TaskManager.cs` schedules backups at a configurable interval (default: daily). The backup creates timestamped archives (`lidarr_backup_v{version}_{timestamp}.zip`) stored in the local backup folder. However, there is no cloud-native backup (AWS Backup, RDS automated snapshots), no PITR, no cross-region replication, and no documented restore testing. |
| **Gap** | Backup exists but is application-managed with local storage only. No cloud-native backup infrastructure, no point-in-time recovery, no cross-region backup, and no restore testing documentation. |
| **Recommendation** | When migrating to Aurora PostgreSQL, leverage Aurora's automated backups with configurable retention (up to 35 days) and PITR. Enable cross-region replication for critical data. Document and test restore procedures. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, `src/NzbDrone.Core/Backup/BackupCommand.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` (backup scheduling) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed cloud workload requiring HA evaluation. Lidarr is distributed as a self-hosted binary with no IaC, no Dockerfile, and no deployment manifests defining compute infrastructure. The `has_deployed_workload` surface flag is `false`. Additionally, the application enforces single-instance operation via `EnsureSingleInstance()`. INF-Q9 does not apply until the application is migrated to a cloud deployment model. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (EnsureSingleInstance), absence of deployment IaC |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in the repository. Zero Terraform files (`.tf`), CloudFormation templates, CDK stacks, Helm charts, Kustomize manifests, or Ansible playbooks were found. The repository contains only application source code, frontend code, CI/CD pipeline definitions, and distribution packaging scripts. All infrastructure is either user-managed or nonexistent. |
| **Gap** | 0% IaC coverage. All infrastructure creation is manual. No reproducible infrastructure, no environment consistency, no disaster recovery from code. |
| **Recommendation** | Start with IaC for the target cloud deployment: define VPC, EKS cluster, Aurora PostgreSQL, API Gateway, and security groups using CDK (TypeScript or C#) or Terraform. Infrastructure should be defined before the first cloud deployment to establish the pattern. |
| **Evidence** | Repository-wide search for `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` — all absent |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Azure Pipelines (`azure-pipelines.yml`) provides comprehensive build and test automation across 7 stages: Setup, Build_Backend (Windows/Linux/macOS), Build_Frontend, Installer (Windows), Packages (12+ platform targets), Unit_Test (native + Docker + PostgreSQL 14/15), Integration (native + Docker + PostgreSQL 14/15 + FreeBSD), Automation (browser tests), and Analyze (SonarCloud for backend and frontend, API doc generation). The pipeline produces binary artifacts and uploads source maps to Sentry. `.github/workflows/ci.yml` exists but is empty (no GitHub Actions jobs defined). However, there is **no deployment automation** — the pipeline ends at artifact creation. No CodeDeploy, no Helm deploy, no infrastructure deployment. |
| **Gap** | Build and test automation is strong, but no deployment pipeline exists. Artifacts are produced but not automatically deployed to any environment. No automated rollback capability. IaC changes (when created) are not in the pipeline. |
| **Recommendation** | Extend the CI/CD pipeline with deployment stages. When migrating to AWS, add CodeBuild/CodePipeline stages for container image building, ECR push, and EKS/ECS deployment. Include IaC validation (`cdk diff`, `terraform plan`) in the pipeline. Add deployment gates and automated rollback. |
| **Evidence** | `azure-pipelines.yml` (all stages), `.github/workflows/ci.yml` (empty), `.github/dependabot.yml` (devcontainers only) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Backend:** C# on .NET 8.0 (SDK 8.0.405 pinned in `global.json`) with ASP.NET Core (Kestrel, MVC controllers, SignalR). Modern .NET with current framework version — first-class AWS SDK coverage, broad cloud-native tooling ecosystem, and mature container support. Key dependencies are current: Dapper 2.1.66, Npgsql 9.0.3, Polly 8.6.4, FluentMigrator 6.2.0, Sentry 4.0.2. **Frontend:** TypeScript 5.7.2 with React 18.3.1 — modern framework versions with full ecosystem support. The solution uses modern C# features (nullable references not enforced but code quality is maintained via StyleCop analyzers and SonarCloud). |
| **Gap** | No significant language or framework gaps. The stack is modern and well-maintained. |
| **Recommendation** | Continue tracking .NET LTS releases. When .NET 9 or 10 becomes the new LTS, plan the upgrade. No immediate action needed — the current stack is cloud-ready. |
| **Evidence** | `global.json` (SDK 8.0.405), `src/Directory.Build.props` (net8.0 targets), `src/NzbDrone.Core/Lidarr.Core.csproj` (modern package versions), `package.json` (TypeScript 5.7.2, React 18.3.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr is a monolithic application deployed as a single executable. All functionality resides in one .NET solution: `NzbDrone.Core` contains all domain logic (artist management, album management, download orchestration, indexer search, notification delivery, media processing, health checks, backup, configuration); `Lidarr.Api.V1` contains all REST API controllers; `NzbDrone.Host` is the single entry point. However, the monolith has **identifiable module boundaries**: the `src/Lidarr.Api.V1/` directory has separate subdirectories for each domain (Albums, Artist, DownloadClient, Indexers, Notifications, Queue, History, etc.), and `NzbDrone.Core` has parallel domain directories. The internal command system and EventAggregator provide some module decoupling. The shared database schema and in-process event bus create coupling. |
| **Gap** | Tightly-coupled monolith with shared database schema and in-process event aggregator. All modules share a single SQLite/PostgreSQL database with cross-module data access. Direct cross-module dependencies exist through the `NzbDrone.Core` project. |
| **Recommendation** | Apply the Conditional/Adaptive approach: containerize the monolith first, then selectively extract services using the Strangler Fig pattern. Start with loosely-coupled modules like Notifications and Indexer Search. See Decomposition Strategy section for detailed approach. |
| **Evidence** | `src/Lidarr.Api.V1/` (API controllers grouped by domain), `src/NzbDrone.Core/` (domain directories), `src/NzbDrone.Host/Startup.cs` (single entry point), all `.csproj` project references |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype: stateful-crud.** The majority of inter-service communication is synchronous HTTP. External service calls to download clients (SABnzbd, NZBGet, qBittorrent, Transmission, Deluge), indexers (Newznab, Torznab), metadata providers, and notification targets are all synchronous HTTP requests. Internally, the `EventAggregator` provides in-process async event handling with `IHandleAsync<TEvent>` dispatched via `TaskFactory`, and SignalR pushes real-time updates to the frontend. However, the EventAggregator is not durable — events are lost on process restart. For a `stateful-crud` archetype, cross-service state changes (e.g., album grabbed → download started → import completed → notification sent) should use managed messaging to ensure durability and decoupling. |
| **Gap** | Primarily synchronous communication. In-process EventAggregator provides some async decoupling but is not durable. No external messaging for cross-boundary state change propagation. For a stateful-crud service managing entity lifecycle, async messaging is needed for reliable state change notification. |
| **Recommendation** | Introduce EventBridge (per preferences) for durable, cross-service event delivery. Map the existing EventAggregator event types to EventBridge event schemas. Use SQS queues for guaranteed delivery to notification targets and download client orchestration. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Download/` (HTTP clients), `src/NzbDrone.Core/Notifications/` (HTTP-based notification delivery), `src/NzbDrone.SignalR/` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: stateful-crud.** Lidarr handles long-running operations through an internal command queue system. The `CommandQueue` (`CommandQueue.cs`) manages background jobs with priority ordering, exclusive execution, and disk-access coordination. Long-running operations include: metadata refresh (`RefreshArtistCommand` — daily, external API calls), download monitoring (`RefreshMonitoredDownloadsCommand` — every 1 minute), RSS sync, media file scanning (`RescanFoldersCommand`), and backup. The `CommandExecutor` processes commands asynchronously from the queue. The frontend receives status updates via SignalR WebSocket push. The command system supports: priority levels (`CommandPriority`), exclusive locks (`IsExclusive`, `IsTypeExclusive`), disk-access serialization (`RequiresDiskAccess`), and long-running detection (`IsLongRunning`). |
| **Gap** | Most long-running operations are handled asynchronously via the command queue. However, the command queue is in-process — it is lost on application restart. No external state machine or Step Functions equivalent provides durable state tracking. Some blocking calls remain (e.g., initial metadata fetch on artist add can block the API response). |
| **Recommendation** | The current command queue implementation is a solid foundation. When migrating to AWS, consider replacing the in-process queue with SQS or Step Functions for durability and visibility. The existing `CommandStatus` (Queued → Started → Completed/Failed) maps directly to Step Functions execution states. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lidarr uses consistent URL-path versioning with `/api/v1/` prefix on all API endpoints. The OpenAPI 3.0.4 specification at `src/Lidarr.Api.V1/openapi.json` documents the full API surface with version "1.0.0". All controllers in `src/Lidarr.Api.V1/` use the `VersionedApiControllerAttribute` for consistent routing. The API has a single version (v1) with no evidence of v2 or deprecated versions. Swagger documentation is available in debug mode at `/docs/v1/openapi.json`. |
| **Gap** | Versioning strategy exists and is consistently applied via `/api/v1/` paths. However, there is no documented backward-compatibility guarantee, no changelog for API changes, and only one version exists (limiting evidence of version migration practices). |
| **Recommendation** | The current versioning strategy is solid. When exposing via API Gateway (per preferences), map the `/api/v1/` paths to API Gateway stages. Document API backward-compatibility guarantees and establish a version migration policy before creating v2. |
| **Evidence** | `src/Lidarr.Api.V1/openapi.json` (OpenAPI 3.0.4, `/api/v1/` paths), `src/Lidarr.Api.V1/` (controller directories), `src/NzbDrone.Host/Startup.cs` (Swagger config) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr is a single application with no inter-service communication requiring service discovery. External service endpoints (download clients, indexers, notification targets) are user-configured through the UI and stored in the database as part of provider definitions (`DownloadClientDefinition`, `IndexerDefinition`, `NotificationDefinition`). These endpoints are essentially environment variables stored in the database rather than static configuration files. No service mesh, Consul, or AWS Service Discovery is used. |
| **Gap** | Endpoints are stored in the database (configurable via UI) rather than hard-coded in source, which is better than Score 1. However, there is no dynamic service discovery — if downstream services move, users must manually update configurations. |
| **Recommendation** | When decomposing into services, implement AWS Cloud Map or EKS service discovery for inter-service communication. For external service integrations (download clients, indexers), the current user-configurable approach is appropriate — these are external services outside Lidarr's control. |
| **Evidence** | `src/Lidarr.Api.V1/DownloadClient/`, `src/Lidarr.Api.V1/Indexers/`, `src/Lidarr.Api.V1/Notifications/`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (DB endpoint via env vars) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Music files and media cover art are stored on the local filesystem. The user configures root folders for their music library, and Lidarr manages files within those directories. Media cover images (album art, artist images) are downloaded from external sources and cached in the application's media cover directory. All unstructured data is stored on local or network-attached storage — no S3, no cloud object storage, no parsing pipeline. |
| **Gap** | All unstructured data on local file systems. No cloud object storage, no automated parsing or extraction pipeline. Media files are only accessible from the local machine/network. |
| **Recommendation** | When migrating to AWS, store media cover art and metadata in S3. Music files can remain on user-managed storage (EFS, FSx for Lustre, or local NVMe) for performance. Use S3 for backup/archive of media libraries. Consider Amazon Textract or Rekognition for album art analysis if AI features are desired. |
| **Evidence** | `src/NzbDrone.Core/MediaFiles/`, `src/NzbDrone.Core/MediaCover/`, `src/Lidarr.Api.V1/MediaCovers/`, `src/Lidarr.Api.V1/RootFolders/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lidarr implements a centralized `BasicRepository<T>` pattern (`src/NzbDrone.Core/Datastore/BasicRepository.cs`) using Dapper ORM. All data access flows through this repository base class, which provides CRUD operations, pagination, and query building. The `SqlBuilder` class generates SQL with database-type-specific dialect support via `WhereBuilderPostgres` and `WhereBuilderSqlite`. The `TableMapping` class manages entity-to-table mappings. Database connections are managed centrally via `ConnectionStringFactory`. The pattern is consistent across all entities — every domain model extends `ModelBase` and has a corresponding repository. |
| **Gap** | Mostly centralized data access. Some direct SQL execution exists in migration files and specific repository overrides, but the base pattern is consistent. The `ExpressionVisitor` handles LINQ-to-SQL translation. Minor inconsistency: some queries bypass the repository pattern for performance (e.g., bulk operations). |
| **Recommendation** | The existing data access layer is well-structured and will ease database migration. When moving to Aurora PostgreSQL, the `DatabaseType.PostgreSQL` code path is already implemented. Minimal code changes needed — the abstraction layer is the strength here. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **SQLite:** Version pinned via NuGet packages — `SourceGear.sqlite3 3.50.4.2` and `System.Data.SQLite 2.0.2` in `Lidarr.Common.csproj`. These are current versions and not approaching EOL. **PostgreSQL:** Not pinned by the application. The application connects to whatever PostgreSQL version the user provides. CI tests against PostgreSQL 14 and 15 (visible in `azure-pipelines.yml` pipeline stages). PostgreSQL 14 reaches community EOL in November 2026 (approaching within 12-18 months). PostgreSQL 15 EOL is November 2027. No documented version-update procedure covering downtime windows, rollback, or risk acknowledgment. |
| **Gap** | SQLite version is pinned and current. PostgreSQL version is not pinned by the application — depends on user installation. CI tests against PostgreSQL 14 (approaching EOL) and 15, but not newer versions (16, 17). No documented version-update procedure. |
| **Recommendation** | Add PostgreSQL 16 and 17 to the CI test matrix. Document supported PostgreSQL versions with EOL dates. When migrating to Aurora PostgreSQL, pin the engine version in IaC and establish a version upgrade procedure with testing gates. |
| **Evidence** | `src/NzbDrone.Common/Lidarr.Common.csproj` (SQLite packages with versions), `src/NzbDrone.Core/Lidarr.Core.csproj` (Npgsql 9.0.3), `azure-pipelines.yml` (postgres:14, postgres:15 in test stages) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the C# application layer. Schema migrations are managed through FluentMigrator (`FluentMigrator.Runner.Core 6.2.0`, `FluentMigrator.Runner.SQLite`, `FluentMigrator.Runner.Postgres` in `Lidarr.Core.csproj`) with 90 migration files in `src/NzbDrone.Core/Datastore/Migration/`. All SQL is generated programmatically by Dapper and the SqlBuilder — no raw SQL files, no stored procedures, no database-specific functions. Repository-wide search for `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` returned zero results. |
| **Gap** | No gap — all business logic is in the application layer. This is a modernization strength. |
| **Recommendation** | No action needed. The absence of stored procedures makes database engine migration straightforward. Continue the pattern of keeping business logic in the application layer. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (90 FluentMigrator files), `src/NzbDrone.Core/Lidarr.Core.csproj` (FluentMigrator packages), repository-wide search for stored procedures (none found) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud-native audit logging exists. Lidarr uses NLog (`NLog 5.4.0`) for application logging with multiple targets: file logging, database logging (via `DatabaseTarget` in `Startup.cs`), syslog (`NLog.Targets.Syslog 7.0.0`), and CLEF JSON structured logging (`NLog.Layouts.ClefJsonLayout 1.0.4`). Sentry integration (`Sentry 4.0.2`) captures errors and performance data. Logs are stored in a local log database (separate SQLite/PostgreSQL database per `LogDbConnection`). However, these are application logs — not audit logs with immutable storage, log validation, or compliance-grade retention. |
| **Gap** | No CloudTrail or equivalent audit logging. Application logs exist but are not immutable, not validated, and stored in a local database that can be modified. No compliance-grade audit trail. |
| **Recommendation** | When migrating to AWS, enable CloudTrail for API and infrastructure audit logging. Configure CloudTrail log file validation and deliver logs to an S3 bucket with Object Lock for immutability. For application-level audit logging, ship NLog output to CloudWatch Logs with a defined retention policy. |
| **Evidence** | `src/NzbDrone.Core/Lidarr.Core.csproj` (NLog packages), `src/NzbDrone.Common/Lidarr.Common.csproj` (Sentry), `src/NzbDrone.Host/Startup.cs` (NLog configuration, DatabaseTarget registration), absence of CloudTrail IaC |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | SQLite database files are stored unencrypted on disk. The `ConnectionStringFactory.cs` creates SQLite connections to plain file paths with no encryption options (no SQLCipher, no filesystem encryption). PostgreSQL connections, when used, do not enforce SSL/TLS (no `sslmode` parameter in the connection builder). No KMS keys, no S3 bucket encryption, no EBS encryption — there is no cloud data-at-rest surface to encrypt, but the application's local data stores are also unencrypted. Media cover images and metadata are stored as plain files. |
| **Gap** | No encryption at rest for any data store. SQLite files are readable by anyone with filesystem access. PostgreSQL connections do not enforce encryption in transit. |
| **Recommendation** | When migrating to Aurora PostgreSQL, enable encryption at rest with a customer-managed KMS key. Configure `sslmode=verify-full` on the Npgsql connection string for encryption in transit. Use S3 server-side encryption (SSE-KMS) for any media metadata stored in S3. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (no encryption config), `src/NzbDrone.Common/Lidarr.Common.csproj` (no SQLCipher), absence of KMS IaC |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr uses API key authentication via two mechanisms defined in `Startup.cs` and the OpenAPI spec: (1) `X-Api-Key` header and (2) `apikey` query parameter. Both use a static API key (type `SecuritySchemeType.ApiKey`). The `ApiKeyAuthenticationHandler` validates API keys on every request. The UI uses forms-based authentication managed by `AuthenticationController` and `AuthenticationService`. User credentials are managed internally via `UserRepository` and `UserService` with password hashing (`Microsoft.AspNetCore.Cryptography.KeyDerivation`). This is API key authentication — functional but not OAuth2/JWT token-based. API keys are static (not rotated automatically) and the `apikey` query parameter exposes the key in URLs and server logs. |
| **Gap** | API key authentication without token-based auth (OAuth2/JWT). Static API keys without automated rotation. API key in query parameter is a security concern (logged in URLs). No scoped permissions — the API key grants full access. |
| **Recommendation** | When deploying behind API Gateway (per preferences), use Cognito User Pools or Lambda authorizers for OAuth2/JWT-based authentication. Replace the static API key with short-lived JWT tokens. Remove the `apikey` query parameter mechanism. Implement scoped API permissions (read-only vs admin). |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (security scheme definitions), `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Lidarr.Api.V1/openapi.json` (security schemes), `src/NzbDrone.Core/Authentication/UserService.cs` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr manages its own authentication entirely. The `UserRepository` and `UserService` in `src/NzbDrone.Core/Authentication/` handle user creation, authentication, and password management. The `AuthenticationService` and `AuthenticationController` in `src/Lidarr.Http/Authentication/` manage login flows. The `AuthenticationType` enum indicates support for different authentication modes, but there is no OIDC, SAML, or external IdP federation. No Cognito, Okta, Ping, or any centralized identity provider integration exists. |
| **Gap** | Application manages its own authentication with no external IdP integration. No SSO, no federation, no centralized identity. |
| **Recommendation** | Integrate with Amazon Cognito (via API Gateway per preferences) for centralized identity. Use Cognito User Pools for user management and Cognito Identity Pools for federated access. This enables SSO across *arr suite applications if desired. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/NzbDrone.Core/Authentication/UserService.cs`, `src/Lidarr.Http/Authentication/AuthenticationController.cs`, `src/Lidarr.Http/Authentication/AuthenticationService.cs` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials were found in committed source code or configuration files. PostgreSQL credentials are provided via environment variables (`Lidarr__Postgres__Host`, `Lidarr__Postgres__User`, `Lidarr__Postgres__Password` — defined in `PostgresOptions.cs`). The application API key is auto-generated and stored in a local XML configuration file (not committed to the repository). External service credentials (download client passwords, indexer API keys, notification tokens) are stored in the application's database. The Azure Pipelines configuration uses pipeline variables for sensitive values (`sentryAuthTokenServarr`, `githubToken`, `discordChannelId`, `discordWebhookKey`). However, no dedicated secrets management service (Secrets Manager, Vault) is used, and no rotation is configured. |
| **Gap** | No plaintext credentials in source (Score 2 baseline). However, production credentials flow through environment variables without encryption or rotation. No Secrets Manager or Vault. External service credentials stored in the application database without encryption at rest. |
| **Recommendation** | When migrating to AWS, use AWS Secrets Manager for all credentials (database passwords, API keys, external service tokens). Configure automated rotation for the database password. Use Secrets Manager SDK in the application to retrieve secrets at runtime instead of environment variables. |
| **Evidence** | `src/NzbDrone.Core/Datastore/PostgresOptions.cs` (env var configuration), `azure-pipelines.yml` (pipeline variable references), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, absence of Secrets Manager/Vault references |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute exists to harden. The application is distributed as self-hosted binaries with no SSM Patch Manager, AWS Inspector, Snyk, or other vulnerability scanning in the deployment model. The application itself does not manage its operating system or runtime patching — users are responsible for their own OS and .NET runtime updates. The .NET 8 runtime is self-contained in the published binaries (per `Directory.Build.props` RuntimeIdentifiers configuration). No hardened base images, no CIS benchmarks, no EC2 Image Builder pipelines. |
| **Gap** | No compute hardening or patching strategy. Users manage their own OS patching. No vulnerability scanning of the deployed environment. |
| **Recommendation** | When containerizing, use hardened base images (e.g., Amazon Linux 2023 or Bottlerocket for EKS nodes). Enable Amazon Inspector for container image vulnerability scanning. Configure ECR image scanning for the Lidarr container image. Use SSM Patch Manager for any remaining EC2-based infrastructure. |
| **Evidence** | `src/Directory.Build.props` (RuntimeIdentifiers for self-contained binaries), `distribution/` (packaging scripts, no hardening), absence of security scanning IaC |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud is integrated into the Azure Pipelines for both backend (C#) and frontend (JavaScript/TypeScript) analysis. The `Analyze_Backend` job runs SonarCloud with code coverage reporting via Cobertura. The `Analyze_Frontend` job runs SonarCloud CLI analysis. Dependabot is configured (`.github/dependabot.yml`) but only for devcontainers — not for NuGet packages, npm packages, or Docker images. No SAST tool beyond SonarCloud, no container scanning (no containers to scan), and no blocking security gate (SonarCloud analysis does not fail the build on critical findings). |
| **Gap** | SonarCloud provides code quality analysis but is not a dedicated SAST tool. Dependabot is configured only for devcontainers. No dependency vulnerability scanning for NuGet or npm packages. No container scanning. No security gate that blocks deployment on critical findings. |
| **Recommendation** | Expand Dependabot to cover `nuget` (for `.csproj` files) and `npm` (for `package.json`). Add `dotnet list package --vulnerable` and `npm audit` to the CI pipeline. When containerizing, enable ECR image scanning. Configure SonarCloud quality gates to fail the build on critical security issues. Consider adding Snyk or GitHub Advanced Security for comprehensive SAST. |
| **Evidence** | `azure-pipelines.yml` (SonarCloudPrepare, SonarCloudAnalyze stages), `.github/dependabot.yml` (devcontainers only), absence of SAST tools, absence of `npm audit`/`dotnet list package --vulnerable` in pipeline |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing (X-Ray, OpenTelemetry) is instrumented. Sentry SDK (`Sentry 4.0.2` in `Lidarr.Common.csproj`) provides error tracking and performance monitoring. NLog provides structured logging with CLEF JSON format support (`NLog.Layouts.ClefJsonLayout`). Sentry source maps are uploaded for both backend and frontend in the pipeline. However, Sentry is error/performance monitoring, not distributed tracing — there is no trace ID propagation across service boundaries, no span creation, and no OpenTelemetry SDK. As a single-process application, there are technically no distributed boundaries to trace, but the external HTTP calls to download clients, indexers, and metadata providers lack request correlation. |
| **Gap** | No distributed tracing. External HTTP calls to downstream services have no request correlation or span tracking. As a single application, this is less critical but blocks observability when decomposing into services. |
| **Recommendation** | When migrating to AWS, instrument OpenTelemetry SDK in the .NET application. Use AWS X-Ray for distributed tracing across EKS services. Add trace ID propagation headers to external HTTP calls. The .NET OpenTelemetry SDK integrates cleanly with ASP.NET Core. |
| **Evidence** | `src/NzbDrone.Common/Lidarr.Common.csproj` (Sentry SDK, no OpenTelemetry), `src/NzbDrone.Common/Instrumentation/` (NLog, Sentry targets), absence of OpenTelemetry/X-Ray packages |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No formal definition of acceptable latency, availability, or error rates for any API endpoint or user journey. No error budget tracking. The application has health check infrastructure (`src/NzbDrone.Core/HealthCheck/` with multiple health check implementations) that monitors internal health (disk space, indexer connectivity, download client status, etc.), but these are operational health checks, not SLO definitions with targets. |
| **Gap** | No SLOs defined. No formal service level targets. Internal health checks exist but are not tied to SLO metrics. |
| **Recommendation** | Define SLOs for critical user journeys: API response latency (p99 < 500ms), search-to-grab success rate (> 95%), import success rate (> 99%). When deployed on AWS, use CloudWatch to monitor these metrics and establish error budgets. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (health check implementations), absence of SLO definition files |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. Sentry captures errors and performance data, but these are operational metrics, not business outcome metrics. The application tracks entity counts (artists, albums, tracks) and operational state (queue size, download status) internally but does not publish these as metrics to an external monitoring system. No CloudWatch custom metrics, no Prometheus endpoints, no business KPI dashboards. |
| **Gap** | No business metrics. The application tracks operational state internally but does not publish metrics for albums imported per day, search success rate, download completion rate, or library growth. |
| **Recommendation** | When deployed on AWS, publish custom CloudWatch metrics for business outcomes: albums imported per day, search-to-grab conversion rate, download completion time, library growth rate. These metrics inform capacity planning and feature prioritization. |
| **Evidence** | `src/NzbDrone.Common/Lidarr.Common.csproj` (Sentry SDK), absence of CloudWatch/Prometheus/metrics endpoints |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or external alerting is configured. The application has an internal health check system (`HealthCheckService`, multiple `HealthCheckBase` implementations) that detects issues like missing root folders, unavailable indexers, download client connectivity problems, and disk space warnings. These health checks generate in-app notifications visible in the UI. However, there is no external alerting integration (PagerDuty, OpsGenie, SNS), no CloudWatch alarms, and no anomaly detection on error rates or latency. |
| **Gap** | Internal health checks exist but do not trigger external alerts. No anomaly detection. No integration with alerting platforms. Issues are only visible to users who check the UI. |
| **Recommendation** | When deployed on AWS, configure CloudWatch alarms on error rates, latency p99, and queue depth. Enable CloudWatch Anomaly Detection for adaptive baselines. Integrate with SNS for alert delivery. Map existing health check categories to CloudWatch composite alarms. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`, `src/NzbDrone.Core/HealthCheck/` (health check implementations), absence of alerting integration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No staged deployment strategy. The Azure Pipelines produces binary packages that are distributed via direct download. Users manually download and install new versions, replacing the previous installation. The Sentry integration distinguishes between "nightly" (develop branch) and "production" (master branch) deployments for source map tagging, but this is error tracking metadata, not a deployment strategy. The `distribution/` directory contains packaging scripts for Windows (Inno Setup installer), macOS (app bundle), and Debian packages — all manual installation methods. There is no blue/green, canary, rolling update, or any automated deployment mechanism. |
| **Gap** | No staged deployment. All users receive the same version simultaneously via manual download. No canary, no blue/green, no rolling update. No automated rollback. |
| **Recommendation** | When containerized and deployed to EKS, implement rolling deployments with health check-based rollback. Progress to canary deployments using Argo Rollouts or EKS native capabilities. For the API Gateway layer, use canary release stages. |
| **Evidence** | `azure-pipelines.yml` (Packages stage, Sentry deploy environments), `distribution/` (Windows/macOS/Debian packaging), absence of deployment automation |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration test suite exists. `src/NzbDrone.Integration.Test/` contains integration tests run in the Azure Pipelines `Integration` stage across multiple platforms: Linux, macOS, Windows, FreeBSD (native), Alpine (Docker). PostgreSQL integration tests run against both PostgreSQL 14 and PostgreSQL 15. The `Automation` stage runs browser-based automation tests (`src/NzbDrone.Automation.Test/`) across Linux, macOS, and Windows. Integration tests download the packaged artifact, extract it, start the application, and run tests against the running instance. This is a strong integration testing practice with multi-platform and multi-database coverage. |
| **Gap** | Strong integration and automation test coverage. Some gaps: no contract tests between API versions, no load/performance testing in the pipeline, and no post-deployment verification tests (since there is no deployment pipeline). |
| **Recommendation** | The existing test suite is a strength. When adding deployment automation, include post-deployment smoke tests (call key API endpoints against the deployed environment). Add API contract tests to prevent breaking changes. Consider load testing with Artillery or k6 for capacity planning. |
| **Evidence** | `azure-pipelines.yml` (Integration and Automation stages), `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Automation.Test/`, PostgreSQL 14/15 test jobs |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated runbooks or incident response workflows exist. No Systems Manager Automation documents, Lambda-based remediation, or Step Functions for incident workflows. The application has internal self-recovery mechanisms (e.g., retry logic in `BasicRepository.cs` using Polly for SQLite busy errors) but no external incident response automation. Discord notifications are sent from the CI/CD pipeline on build completion/failure, but this is build notification, not incident response. |
| **Gap** | No incident response automation. No runbooks (documented or machine-readable). Incident response is entirely ad hoc. |
| **Recommendation** | When deployed on AWS, create runbooks for common incidents: database connection failures, high latency, disk space exhaustion, failed downloads. Use Systems Manager Automation for self-healing (e.g., auto-restart on health check failure, auto-scale on queue depth). |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry), `azure-pipelines.yml` (Discord notifications), absence of runbook files |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership is defined. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution, no CODEOWNERS file referencing observability assets. The application has no cloud-native observability infrastructure to own. Sentry provides error tracking but without formal ownership assignment. |
| **Gap** | No observability ownership. No dashboards, no named owners, no team attribution on monitoring assets. |
| **Recommendation** | When deployed on AWS, establish per-service CloudWatch dashboards with named owners. Create a CODEOWNERS file that includes observability configurations (alarm definitions, dashboard JSON, SLO definitions). Assign on-call ownership for alerting. |
| **Evidence** | Absence of CODEOWNERS file, absence of dashboard definitions, absence of SLO files with ownership |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources exist to tag. No `default_tags` in Terraform, no `tags` on CloudFormation resources, no tag policies, no cost allocation tags. The repository contains no IaC, so there are no resources to evaluate for tagging compliance. |
| **Gap** | No resource tagging. When IaC is created, tagging governance must be established from the start. |
| **Recommendation** | When creating IaC, implement tagging from day one. Define a tagging standard: `Environment` (dev/staging/prod), `Service` (lidarr), `Team` (team name), `CostCenter`, `ManagedBy` (terraform/cdk). Use `default_tags` in Terraform provider or CDK `Tags.of()` for consistent tagging. Enable AWS Config `required-tags` rule. |
| **Evidence** | Absence of IaC files, absence of tagging configuration |

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
| `azure-pipelines.yml` | INF-Q1, INF-Q11, DATA-Q3, SEC-Q7, OPS-Q5, OPS-Q6 | CI/CD pipeline with build, test, packaging, and analysis stages across 7+ platforms |
| `global.json` | APP-Q1 | .NET SDK version pin (8.0.405) |
| `package.json` | APP-Q1 | Frontend dependencies (TypeScript 5.7.2, React 18.3.1, SignalR client) |
| `src/Directory.Build.props` | APP-Q1, SEC-Q6 | .NET 8.0 target, runtime identifiers, Sentry configuration, StyleCop analyzers |
| `src/NzbDrone.Core/Lidarr.Core.csproj` | INF-Q2, DATA-Q2, DATA-Q3, DATA-Q4 | Core NuGet dependencies: Dapper, Npgsql, FluentMigrator, Polly, NLog |
| `src/NzbDrone.Common/Lidarr.Common.csproj` | INF-Q2, SEC-Q1, OPS-Q1 | SQLite packages, Sentry SDK, NLog, SharpZipLib |
| `src/NzbDrone.Host/Lidarr.Host.csproj` | INF-Q6 | ASP.NET Core Web SDK, Swashbuckle, DryIoc, SignalR |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, INF-Q7, INF-Q9, SEC-Q3, SEC-Q4 | Kestrel configuration, CORS, auth, SignalR, Swagger, single-instance enforcement |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | DATA-Q2, OPS-Q7 | Centralized repository pattern with Dapper, Polly retry |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2, SEC-Q2, APP-Q6 | SQLite/PostgreSQL connection management, credential handling |
| `src/NzbDrone.Core/Datastore/PostgresOptions.cs` | SEC-Q5 | Environment variable-based PostgreSQL configuration |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2 | Database-agnostic SQL query builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | DATA-Q2 | PostgreSQL-specific WHERE clause generation |
| `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` | DATA-Q2 | SQLite-specific WHERE clause generation |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 90 FluentMigrator migration files — schema versioning |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` | INF-Q3, APP-Q4 | In-process command queue with priority and exclusive execution |
| `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` | INF-Q3, APP-Q4 | Command execution engine |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | INF-Q4, APP-Q3 | In-process event bus with sync and async handlers |
| `src/NzbDrone.Core/Jobs/TaskManager.cs` | INF-Q3, INF-Q8 | Scheduled task management (backup, refresh, sync) |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Application-level backup to local ZIP archives |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q4 | Internal health check system |
| `src/NzbDrone.Core/Authentication/UserService.cs` | SEC-Q3, SEC-Q4 | Internal user authentication management |
| `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key validation handler |
| `src/Lidarr.Api.V1/openapi.json` | APP-Q5, INF-Q6 | OpenAPI 3.0.4 specification with /api/v1/ versioning |
| `src/Lidarr.Api.V1/` | APP-Q2, APP-Q5, APP-Q6 | API controllers grouped by domain (Albums, Artist, DownloadClient, etc.) |
| `src/NzbDrone.Core/MediaFiles/` | DATA-Q1 | Media file management on local filesystem |
| `src/NzbDrone.Core/MediaCover/` | DATA-Q1 | Cover art caching on local filesystem |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test suite |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | Browser-based automation test suite |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot configured for devcontainers only |
| `.github/workflows/ci.yml` | INF-Q11 | Empty GitHub Actions workflow (no jobs defined) |
| `distribution/` | OPS-Q5, SEC-Q6 | Platform-specific packaging (Windows installer, Debian, macOS) |
| `build.sh` | INF-Q1 | Build script for backend, frontend, and packaging |
