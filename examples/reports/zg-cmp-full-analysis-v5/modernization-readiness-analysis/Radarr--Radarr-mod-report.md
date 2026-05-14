# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | Radarr |
| **Date** | 2026-04-30 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Movie collection manager (*arr suite). |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | 1.9 / 4.0 |

**Archetype Justification**: Radarr owns persistent state (SQLite/PostgreSQL databases via Dapper/FluentMigrator), exposes CRUD operations on business entities (movies, collections, tags, profiles via /api/v3/*), and manages user-specific data and entity lifecycle. Classified as stateful-crud.

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.4 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.7 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.5 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.4 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.4 / 4.0 | ❌ Not Present |
| **Overall** | **1.9 / 4.0** | **🟠 Needs Work** |

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | All compute is self-hosted binary distribution with no managed container orchestration or serverless. | Blocks containerization and cloud-native modernization pathways. |
| 2 | INF-Q10: IaC Coverage | 1 | No Infrastructure as Code found — 0% IaC coverage. All infrastructure is manually provisioned by end-users. | Prevents reproducible deployments, automated disaster recovery, and environment consistency. |
| 3 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation. Application exposes HTTP directly without managed networking. | No network isolation or blast-radius limiting in cloud deployment scenarios. |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent cloud audit logging infrastructure. Application uses NLog for local logging only. | No immutable audit trail for compliance or forensic analysis in a cloud-hosted scenario. |
| 5 | INF-Q6: API Entry Point | 1 | No API Gateway, ALB, or CloudFront — application self-hosts via Kestrel/ASP.NET Core with no throttling or request validation layer. | No centralized traffic management, rate limiting, or request validation for the API surface. |

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** API docs exist (openapi.json with OpenAPI 3.0.4 spec, APP-Q5 = 3)
- **What it enables:** An agent that discovers and invokes existing Radarr API endpoints as tools — movie search, collection management, download queue monitoring, and configuration changes.
- **Additional steps:** The OpenAPI spec is already generated and comprehensive. Agent can use it directly for tool discovery.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 3, centralized BasicRepository pattern with Dapper)
- **What it enables:** A natural language to SQL agent that queries the Radarr movie database — "show me all movies released in 2024 with a quality below 1080p" or "which movies are missing from my collection?"
- **Additional steps:** SQLite/PostgreSQL schema is well-defined via FluentMigrator migrations. Agent would need read-only database access.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2)
- **What it enables:** An agent that triggers Azure Pipelines builds, checks build status, and monitors test results across the multi-platform matrix.
- **Additional steps:** Azure Pipelines API access would need to be configured for the agent.
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists (README.md, CONTRIBUTING.md, SECURITY.md, extensive code comments)
- **What it enables:** A knowledge agent that answers developer questions about the Radarr codebase, API usage, and contribution guidelines using existing documentation as a knowledge base.
- **Additional steps:** Index README.md, CONTRIBUTING.md, API docs, and wiki content into a vector store.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolith), INF-Q1 = 1 (no managed compute) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no managed compute), no Dockerfiles found, compute is not Lambda/Fargate/ECS |
| 3 | Move to Open Source | Not Triggered | — | — | Databases are already open source (SQLite, PostgreSQL). No commercial DB engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed — embedded SQLite or self-managed PostgreSQL) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No streaming/ETL/analytics workloads detected. Contextual guard prevents triggering. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). CI/CD exists but lacks deployment automation to cloud infrastructure. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Radarr is a tightly-coupled monolith — a single .NET 8 application with 20+ C# projects (NzbDrone.Core, Radarr.Api.V3, NzbDrone.Host, Radarr.Http, NzbDrone.SignalR, etc.) that all compile into a single deployable binary. The application includes a React/TypeScript frontend bundled into the same output directory. There is no managed compute — the application is distributed as zip/tar archives for direct installation on user machines.

**Compute Model Gaps:** No cloud compute at all. Application runs as a self-hosted process on bare metal or VMs.

**Communication Pattern Gaps:** All internal communication is synchronous and in-process. External communication (to indexers, download clients, notification services) is synchronous HTTP. SignalR provides real-time push to the frontend only.

**Recommended Decomposition Approach:** See Decomposition Strategy section below.

**Representative AWS Services (per preferences):** EKS for container orchestration, API Gateway for API entry point, EventBridge for event-driven communication between extracted services, Aurora PostgreSQL for managed database, DynamoDB for high-throughput metadata caching.

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Hexagonal Architecture.

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Self-hosted binary distribution across 12+ platform-architecture combinations (win-x64, win-x86, osx-x64, osx-arm64, linux-x64, linux-musl-x64, linux-arm, linux-musl-arm, linux-arm64, linux-musl-arm64, freebsd-x64). No Dockerfiles, docker-compose, or Kubernetes manifests found in the repository.

**Container Readiness Indicators:** The application is already built for multiple Linux architectures including musl (Alpine-compatible). It uses ASP.NET Core (Kestrel) for HTTP hosting. Configuration is externalized via environment variables (Radarr__Postgres__Host, etc.). These are strong indicators of containerization readiness.

**Recommended Container Orchestration (per preferences):** EKS (preferred). The application's multi-architecture build matrix already supports linux-musl (Alpine) targets, making lightweight container images straightforward.

**Representative AWS Services:** EKS, ECR, Fargate (for serverless container hosting), App Runner.

**Migration Approach:** Lift-and-containerize — create Dockerfiles based on existing linux-musl build targets, then deploy to EKS.

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** Embedded SQLite (default) or self-managed PostgreSQL configured via environment variables. The CI/CD pipeline tests against PostgreSQL 14 and 15 via Docker containers, confirming PostgreSQL compatibility. No managed database services (RDS, Aurora, DynamoDB) are defined in IaC (no IaC exists).

**Engine Versions:** SQLite version bundled via `SourceGear.sqlite3` NuGet package (3.50.4.2). PostgreSQL tested against versions 14 and 15. No version pinning in IaC (no IaC exists).

**Data Access Patterns:** Centralized BasicRepository pattern with Dapper ORM. Data access is well-structured and consistent across the codebase.

**Recommended Managed Targets (per preferences):** Aurora PostgreSQL (preferred) for primary data store. DynamoDB (preferred) for high-throughput metadata caching if the application is decomposed.

**Representative AWS Services:** Aurora PostgreSQL, DynamoDB, RDS PostgreSQL.

**Migration Tools:** AWS DMS for PostgreSQL migration, native pg_dump/pg_restore for straightforward data transfer.

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** 0% — No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files found. The application is distributed as binary packages with no cloud infrastructure definition.

**Current CI/CD State:** Comprehensive Azure Pipelines configuration (`azure-pipelines.yml`) with multi-stage pipeline: Setup → Build_Backend → Build_Frontend → Unit_Test → Integration → Automation → Analyze → Packages → Installer → Report_Out. Also has GitHub Actions CI (`ci.yml`) for basic build verification. SonarCloud analysis is integrated for both backend and frontend. However, there is no deployment automation to any cloud environment — the pipeline produces binary artifacts only.

**Deployment Strategy Gaps:** Binary distribution via zip/tar archives. No blue/green, canary, or rolling deployments. No cloud deployment automation.

**Testing Gaps:** Strong test coverage exists — unit tests (multi-platform: Windows, Mac, Linux, FreeBSD, Alpine), integration tests (PostgreSQL 14/15, multi-platform), and automation/UI tests. However, these run in CI only for artifact validation, not as part of cloud deployment gates.

**Recommended DevOps Toolchain (per preferences):** Terraform or CDK for IaC, CodePipeline + CodeDeploy for deployment automation to EKS, CloudWatch for monitoring.

**Representative AWS Services:** CDK, CodePipeline, CodeBuild, CodeDeploy, CloudFormation, CloudWatch, X-Ray.

## Decomposition Strategy

**Condition:** APP-Q2 = 2 (monolith with identifiable modules but single deployment)

### Approach Recommendation

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Identifiable modules exist (Core, Api, Notifications, Download, Indexers, MediaFiles, ImportLists). The monolith has recognizable domain boundaries. | **Medium to High** — 6-18 months | ✅ **Recommended.** Module boundaries in the NzbDrone.Core namespace map to domain services that can be incrementally extracted. |
| **Conditional / Adaptive** | Team has limited capacity. Business pressure requires quick wins. | **Low to Medium** — containerize in 2-4 weeks, selective extraction 3-12 months | ✅ **Recommended when capacity is constrained.** Containerize the monolith first (linux-musl targets already exist), then extract high-value services. |
| **Big-Bang Rewrite** | Almost never. | **Very High** — 12-24+ months | ⚠️ **Recommended against.** The monolith is functional and well-structured. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's data model | Every extraction — place ACL between new service and monolith |
| **Saga Pattern** | Manage distributed transactions across extracted services | When extracting Download + Import workflows that currently run in a single transaction |
| **Event Sourcing** | Capture state changes as events | When extracting notification and event-driven flows |
| **Hexagonal Architecture** | Clear boundaries between business logic and infrastructure | Every new service |

### Effort Estimation

| Factor | Signal | Source |
|--------|--------|--------|
| Module boundaries | Clear namespace/project structure (Core, Api, Http, SignalR, Mono, Windows) — identifiable domains | APP-Q2 |
| Data coupling | Centralized BasicRepository pattern — shared SQLite database but well-abstracted access layer | DATA-Q2 |
| Stored procedures | None — all business logic in application layer | DATA-Q4 |
| Communication patterns | All synchronous in-process — event aggregator pattern used internally | APP-Q3 |
| CI/CD maturity | Strong multi-platform CI pipeline — can support multi-service deployment with extension | INF-Q11 |
| Test coverage | Comprehensive unit + integration + automation tests — low regression risk during extraction | OPS-Q6 |

## Detailed Findings

### Infrastructure, Platform, and DevOps

<!-- TODO: INF-Q1 through INF-Q11 detailed findings -->

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is self-hosted binary distribution. The application is packaged as zip/tar archives for 12+ platform combinations (win-x64, osx-x64, linux-x64, linux-musl-x64, etc.). No AWS ECS, EKS, Lambda, Fargate, or EC2 resources are defined anywhere in the repository. No IaC files exist. |
| **Gap** | No managed compute infrastructure. Application runs entirely on user-provisioned bare metal or VMs. |
| **Recommendation** | Containerize the application using the existing linux-musl build targets and deploy to EKS (preferred). Create Dockerfiles based on the Alpine-compatible builds already tested in CI. |
| **Evidence** | azure-pipelines.yml (Packages stage), distribution/windows/setup/radarr.iss, build.sh |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Databases are entirely self-managed. Default is embedded SQLite (via `SourceGear.sqlite3` 3.50.4.2 NuGet package). Optional PostgreSQL support via Npgsql 9.0.3, configured through environment variables (Radarr__Postgres__Host, etc.). CI pipeline tests against postgres:14 and postgres:15 Docker containers. No RDS, Aurora, or DynamoDB resources defined (no IaC). |
| **Gap** | All databases self-managed with no automated failover, managed patching, or cloud backup integration. |
| **Recommendation** | Migrate to Aurora PostgreSQL (preferred) for production deployments. Use DynamoDB (preferred) for high-throughput metadata caching if decomposing into microservices. |
| **Evidence** | src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs, src/NzbDrone.Common/Radarr.Common.csproj (SQLite package), azure-pipelines.yml (postgres:14/15 containers) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | For a stateful-crud archetype, Radarr has multi-step workflows (search → grab → download → import → rename → notify) implemented as in-code command queue patterns. The `CommandQueue` and `CommandExecutor` in `src/NzbDrone.Core/Messaging/Commands/` implement a structured command pattern with prioritization and status tracking. Scheduled tasks in `src/NzbDrone.Core/Jobs/Scheduler.cs` handle periodic operations. No dedicated workflow orchestration service (Step Functions, Temporal) is used. |
| **Gap** | Simple state machines in code with some structure, but no dedicated orchestration service. Multi-step media import workflows are hardcoded. |
| **Recommendation** | For cloud modernization, consider AWS Step Functions (or EventBridge-based orchestration per preferences) for the download→import→rename→notify workflow chain. |
| **Evidence** | src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs, src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs, src/NzbDrone.Core/Jobs/Scheduler.cs |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | For a stateful-crud archetype, Radarr has an internal event aggregator (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) that provides in-process pub/sub for domain events (movie added, download completed, file imported). SignalR is used for real-time push to the browser frontend. However, there is no managed messaging infrastructure (SQS, SNS, EventBridge) for cross-service communication. All external communication (indexers, download clients, notifications) is synchronous HTTP. |
| **Gap** | No managed messaging where state changes cross service boundaries. Internal event aggregator is in-process only — not durable and not cross-service. Notifications to external services (Discord, Slack, Telegram, etc.) are dispatched synchronously. |
| **Recommendation** | Adopt EventBridge (preferred) for event-driven notification dispatching and cross-service communication if decomposing. |
| **Evidence** | src/NzbDrone.Core/Messaging/Events/EventAggregator.cs, src/NzbDrone.SignalR/MessageHub.cs, src/NzbDrone.Core/Notifications/ |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, subnet configurations, or network segmentation found. Application self-hosts via Kestrel and exposes HTTP directly on a configurable port. No IaC exists to define network infrastructure. |
| **Gap** | Services deployed with no network isolation — no private subnets, no security groups, no managed networking services. |
| **Recommendation** | When deploying to AWS, provision a VPC with private subnets, security groups with least-privilege rules, and VPC endpoints for AWS service communication. Use API Gateway (preferred) as the entry point. |
| **Evidence** | No .tf, .cfn.yaml, or CDK files found. src/NzbDrone.Host/Startup.cs (Kestrel self-hosting) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync. The application self-hosts via ASP.NET Core Kestrel with no external gateway, throttling, or request validation layer. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, no centralized auth validation, no request size limits. |
| **Recommendation** | Deploy API Gateway (preferred) with throttling, API key validation, and request validation as the entry point for the Radarr API. |
| **Evidence** | src/NzbDrone.Host/Startup.cs, src/NzbDrone.Host/Radarr.Host.csproj |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application runs as a single instance with `SingleInstancePolicy` enforcement. No ASG, ECS service scaling, or Lambda concurrency configuration. |
| **Gap** | No auto-scaling — all capacity is statically provisioned by the end-user. |
| **Recommendation** | When containerized on EKS (preferred), configure Horizontal Pod Autoscaler based on CPU/memory metrics. |
| **Evidence** | src/NzbDrone.Host/SingleInstancePolicy.cs, No IaC found |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Radarr has a built-in backup service (`src/NzbDrone.Core/Backup/BackupService.cs`) that creates application-level backups of the SQLite database and configuration. The `BackupCommand` triggers scheduled and manual backups. However, there is no cloud-native backup infrastructure (AWS Backup, RDS automated backups, S3 versioning). No PITR, no cross-region replication, no restore testing documentation. |
| **Gap** | Application-level backups exist but are local only. No cloud backup plans, no PITR, no automated restore testing. |
| **Recommendation** | When migrated to Aurora PostgreSQL (preferred), enable automated backups with PITR and configure AWS Backup plans for cross-region replication. |
| **Evidence** | src/NzbDrone.Core/Backup/BackupService.cs, src/NzbDrone.Core/Backup/BackupCommand.cs, src/NzbDrone.Core/Backup/MakeDatabaseBackup.cs |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed cloud workload (has_deployed_workload=false). INF-Q9 does not apply. The application is a self-hosted single-instance desktop/server application distributed as binaries. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC, no Dockerfile, no deployment manifests |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository — no Terraform (.tf), CloudFormation (.cfn.yaml), CDK (cdk.json), Helm (Chart.yaml), or Kustomize (kustomization.yaml). 0% IaC coverage. All infrastructure is provisioned manually by end-users. |
| **Gap** | No IaC — all infrastructure created manually (ClickOps or manual installation). |
| **Recommendation** | Create IaC using CDK or Terraform to define the complete cloud infrastructure: EKS cluster, Aurora PostgreSQL, API Gateway, VPC, and operational resources. |
| **Evidence** | Repository root and all subdirectories scanned — no IaC files found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Comprehensive CI pipeline exists in Azure Pipelines (`azure-pipelines.yml`) with multi-stage build, test, and packaging. Stages: Setup → Build_Backend (multi-platform) → Build_Frontend (multi-platform) → Unit_Test (native + Docker + PostgreSQL 14/15) → Integration (native + Docker + PostgreSQL + FreeBSD) → Automation (UI tests) → Analyze (SonarCloud + coverage) → Packages → Installer → Report_Out. GitHub Actions CI (`ci.yml`) provides basic build verification. However, there is no deployment automation — the pipeline produces binary artifacts only, with no automated deployment to any environment. |
| **Gap** | Build is automated but deployment is entirely manual. No automated deployment to staging or production environments. No IaC deployment pipeline. |
| **Recommendation** | Extend the existing Azure Pipelines (or migrate to CodePipeline) to include automated deployment stages for containerized workloads on EKS. Add IaC deployment via CDK/Terraform pipeline. |
| **Evidence** | azure-pipelines.yml, .github/workflows/ci.yml |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | C# on .NET 8.0 (SDK 8.0.405, target framework net8.0) — modern .NET with ASP.NET Core. Frontend: TypeScript 5.7.2 / React 18.3.1 with Node.js 20.11.1. The .NET ecosystem provides first-class AWS SDK coverage and mature cloud-native tooling. Modern framework versions throughout: Dapper 2.1.66, FluentMigrator 6.2.0, DryIoc 5.4.3, Polly 8.6.0, Sentry 4.0.2. No AWS SDK is currently used, but the .NET 8 ecosystem has full AWS SDK v3 support. |
| **Gap** | N/A — language and framework stack are fully modern. |
| **Recommendation** | N/A — .NET 8 with current ASP.NET Core is a Score 4 language ecosystem. When migrating to AWS, adopt AWS SDK for .NET v3. |
| **Evidence** | global.json (SDK 8.0.405), src/Directory.Build.props (TargetFrameworks: net8.0), src/NzbDrone.Core/Radarr.Core.csproj, package.json (TypeScript 5.7.2, React 18.3.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit with 20+ C# projects in one solution (Radarr.sln). All projects compile to a shared output directory (`_output/`). Radarr.Host references Core, Api.V3, Http, SignalR, Common. Identifiable modules exist: Core (business logic), Api.V3 (REST controllers), Http (middleware/auth), SignalR (real-time), Notifications (30+ notification providers), Download (15+ download clients), Indexers (10+ indexer providers), ImportLists, MediaFiles, MediaCover. However, these modules share a single database, share the same process, and have direct in-process cross-module calls. |
| **Gap** | Monolith with identifiable modules but shared database schemas, direct cross-module data access through the shared BasicRepository, and single deployment unit. |
| **Recommendation** | Adopt Strangler Fig or Conditional/Adaptive decomposition approach. Start by containerizing the monolith, then extract high-value domains (Notifications, Download Clients, Indexers) as independent services. See Decomposition Strategy section. |
| **Evidence** | src/Radarr.sln, src/NzbDrone.Host/Radarr.Host.csproj (project references), src/Directory.Build.props (shared OutputPath) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | For a stateful-crud archetype, communication is primarily synchronous. External HTTP calls to indexers, download clients, and notification services are all synchronous (`NzbDrone.Common/Http/HttpClient.cs`). Internal event aggregation (`Messaging/Events/EventAggregator.cs`) provides in-process pub/sub, but this is not durable async messaging. SignalR provides push notifications to the frontend client only. Background jobs (Scheduler) use synchronous execution within the command queue. |
| **Gap** | Primarily synchronous with some async for background jobs. No durable async messaging for cross-service state propagation. Notification dispatch to 30+ external services is synchronous. |
| **Recommendation** | Adopt EventBridge (preferred) for notification fan-out and state change propagation when decomposing. Use SQS for durable async processing of download and import workflows. |
| **Evidence** | src/NzbDrone.Common/Http/HttpClient.cs, src/NzbDrone.Core/Messaging/Events/EventAggregator.cs, src/NzbDrone.Core/Notifications/ |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | For a stateful-crud archetype, Radarr handles long-running operations through its Command pattern. The `CommandQueue` (`Messaging/Commands/CommandQueue.cs`) and `CommandExecutor` provide async job processing with status tracking, priority management, and progress reporting via SignalR. Media scanning, indexer searches, and download monitoring run as background commands. The API exposes command status endpoints for polling. |
| **Gap** | Most long-running operations are async via the command pattern. However, some operations (e.g., large library scans) may still block threads, and there's no checkpointing or distributed job recovery. |
| **Recommendation** | Maintain current command pattern. When migrating to cloud, consider Step Functions for multi-step import workflows that benefit from checkpointing and retry. |
| **Evidence** | src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs, src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs, src/Radarr.Api.V3/Commands/CommandController.cs |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | API is versioned at /api/v3/ — consistent across all endpoints. The `Radarr.Api.V3` project name and `VersionedApiControllerAttribute` in `Radarr.Http` enforce versioning. An OpenAPI 3.0.4 specification is maintained at `src/Radarr.Api.V3/openapi.json` and auto-generated via the `docs.sh` script. The CI pipeline has an `Api_Docs` stage that auto-generates and commits API doc changes. |
| **Gap** | Versioning strategy exists and is applied consistently to all endpoints, but there's only one version (v3) with no documented backward compatibility guarantees or deprecation policy. |
| **Recommendation** | Document API versioning policy and backward compatibility guarantees. When exposing via API Gateway (preferred), implement API versioning at the gateway level. |
| **Evidence** | src/Radarr.Api.V3/openapi.json, src/Radarr.Http/VersionedApiControllerAttribute.cs, azure-pipelines.yml (Api_Docs stage) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single application — no inter-service discovery needed. External service communication (to indexers, download clients, notification targets) uses user-configured URLs stored in the database. These are essentially environment variables/config for endpoints, not dynamic discovery. No service mesh, Consul, or AWS Service Discovery. |
| **Gap** | Environment variables/config for endpoints but no dynamic discovery. External service addresses are hardcoded in user configuration. |
| **Recommendation** | When decomposing into microservices, adopt service discovery via EKS service mesh or AWS Cloud Map. |
| **Evidence** | src/NzbDrone.Core/Download/Clients/ (hardcoded settings per client), src/NzbDrone.Core/Indexers/ (URL-based configuration) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Media files, cover images, and metadata are stored on the local filesystem. `MediaCoverService` (`src/NzbDrone.Core/MediaCover/MediaCoverService.cs`) manages cover art by downloading and caching on disk. `MediaFileService` manages movie files on local paths. No S3, managed object storage, or parsing pipeline. |
| **Gap** | Data on local file systems with no managed object storage or parsing capabilities. |
| **Recommendation** | Migrate media cover art and metadata to S3 (with CloudFront for caching). Media files can remain user-managed but metadata should be cloud-hosted. |
| **Evidence** | src/NzbDrone.Core/MediaCover/MediaCoverService.cs, src/NzbDrone.Core/MediaFiles/MediaFileService.cs |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Centralized data access via `BasicRepository<T>` pattern (`src/NzbDrone.Core/Datastore/BasicRepository.cs`) using Dapper ORM. All entities extend `ModelBase` and go through the repository layer. `SqlBuilder` provides structured query building with database-type-aware WHERE clause generation (WhereBuilderPostgres.cs / WhereBuilderSqlite.cs). FluentMigrator manages schema migrations (242+ migrations). Most data access goes through the repository layer consistently. |
| **Gap** | Mostly centralized with some direct SQL access in auxiliary code paths (raw SQL in migration files and some query optimizations). |
| **Recommendation** | Maintain the centralized repository pattern. When migrating to Aurora PostgreSQL, the Npgsql-based data access will work with minimal changes. |
| **Evidence** | src/NzbDrone.Core/Datastore/BasicRepository.cs, src/NzbDrone.Core/Datastore/SqlBuilder.cs, src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SQLite version is bundled via NuGet package (SourceGear.sqlite3 3.50.4.2) — implicitly pinned via dependency. PostgreSQL is tested against versions 14 and 15 in CI (azure-pipelines.yml), but no explicit version pin exists in application configuration — users can run any PostgreSQL version. PostgreSQL 14 reaches EOL in November 2026 (approaching). No documented version-update procedure. |
| **Gap** | Some versions pinned (SQLite via NuGet), others implicit (PostgreSQL). PostgreSQL 14 is approaching EOL. No documented version-update or migration procedure. |
| **Recommendation** | Pin minimum PostgreSQL version requirement in documentation. When migrating to Aurora PostgreSQL (preferred), choose Aurora PostgreSQL 15+ to avoid near-EOL versions. |
| **Evidence** | src/NzbDrone.Common/Radarr.Common.csproj (SourceGear.sqlite3 3.50.4.2), azure-pipelines.yml (postgres:14, postgres:15) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found. All business logic is in the C# application layer. Database migrations (242+ FluentMigrator migrations) use standard DDL only — CREATE TABLE, ALTER TABLE, CREATE INDEX, INSERT, UPDATE, DELETE. The WhereBuilder implementations generate standard SQL compatible with both SQLite and PostgreSQL. Dapper-based queries are parameterized and database-agnostic. |
| **Gap** | N/A — no stored procedures or proprietary SQL. |
| **Recommendation** | N/A — all business logic in application layer. This is a best-practice implementation. |
| **Evidence** | src/NzbDrone.Core/Datastore/Migration/ (242 migration files), src/NzbDrone.Core/Datastore/BasicRepository.cs, src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent cloud audit logging. Application uses NLog 5.4.0 for local logging with file targets and optional Syslog target. Sentry 4.0.2 is integrated for error tracking. Database logging via `DatabaseTarget` writes to a separate log database. However, no immutable audit trail, no CloudTrail, no S3 Object Lock for log storage. |
| **Gap** | No CloudTrail or equivalent audit logging. Local NLog logging is not immutable and not suitable for compliance or forensic analysis. |
| **Recommendation** | When deployed to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable audit storage. |
| **Evidence** | src/NzbDrone.Common/Radarr.Common.csproj (NLog 5.4.0, Sentry 4.0.2), src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured. SQLite database is stored as a plain file on disk with no encryption. PostgreSQL connection strings in `ConnectionStringFactory.cs` do not configure SSL/TLS (no `SslMode` or `SSL` parameters set). No KMS configuration, no customer-managed keys. |
| **Gap** | No encryption at rest configured for any data store. |
| **Recommendation** | When migrating to Aurora PostgreSQL (preferred), enable encryption at rest with KMS customer-managed keys. Enable S3 server-side encryption for any object storage. |
| **Evidence** | src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs (no SSL in NpgsqlConnectionStringBuilder) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API key authentication via `X-Api-Key` header and `apikey` query parameter, implemented in `ApiKeyAuthenticationHandler.cs`. Forms-based authentication for the web UI via `AuthenticationController.cs`. No OAuth2/JWT tokens. The API key is static and not rotated. Password hashing uses PBKDF2 via `Microsoft.AspNetCore.Cryptography.KeyDerivation`. |
| **Gap** | API key authentication without token-based auth (no OAuth2/JWT). Static API key with no rotation mechanism. |
| **Recommendation** | When exposed via API Gateway (preferred), implement OAuth2/JWT authentication with Amazon Cognito for token-based auth. Maintain API key as a secondary auth mechanism. |
| **Evidence** | src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs, src/Radarr.Http/Authentication/AuthenticationController.cs, src/Radarr.Api.V3/openapi.json (security schemes) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application manages its own authentication entirely. `UserRepository` and `UserService` in `src/NzbDrone.Core/Authentication/` manage local users with PBKDF2-hashed passwords and salt. No OIDC, SAML, Cognito, or external IdP federation. Forms-based login with cookie authentication. |
| **Gap** | Application manages its own authentication with no external IdP integration. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management and SSO support when deploying to AWS. |
| **Evidence** | src/NzbDrone.Core/Authentication/UserService.cs, src/NzbDrone.Core/Authentication/UserRepository.cs |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials found in source code. CI pipeline uses Azure DevOps pipeline variables for secrets (sentryAuthTokenServarr, githubToken, discordWebhookKey, discordChannelId). PostgreSQL credentials are passed via environment variables (Radarr__Postgres__Password). API key is generated at runtime and stored in the local config file. No Secrets Manager, Vault, or KMS references. No automated rotation. |
| **Gap** | Production credentials kept in environment variables without encryption or rotation. No centralized secrets management. |
| **Recommendation** | Adopt AWS Secrets Manager for database credentials and API keys with automated rotation when deploying to AWS. |
| **Evidence** | azure-pipelines.yml (env vars: SENTRY_AUTH_TOKEN, GITHUBTOKEN), src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs (password from config) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute resources to harden. No SSM Patch Manager, AWS Inspector, or vulnerability scanning infrastructure. The application self-updates via its own update mechanism (`src/NzbDrone.Core/Update/InstallUpdateService.cs`). No hardened base images or AMI references. |
| **Gap** | No evidence of patching strategy or vulnerability scanning for the compute environment. |
| **Recommendation** | When containerized, use hardened base images (e.g., Bottlerocket for EKS nodes) and enable ECR image scanning. Integrate Inspector for runtime vulnerability detection. |
| **Evidence** | src/NzbDrone.Core/Update/InstallUpdateService.cs (self-update mechanism) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud is integrated for SAST on both backend (C#) and frontend (TypeScript/React) via the Analyze stage in azure-pipelines.yml. Code coverage is generated and published. Dependabot is configured but only for devcontainers — not for NuGet packages, npm packages, or the main application dependencies. StyleCop analyzers are enabled for code style enforcement. No container image scanning. No DAST. No security gate blocking on critical findings. |
| **Gap** | SAST via SonarCloud exists but Dependabot does not cover main application dependencies (NuGet, npm). No container scanning, no DAST, no blocking security gate. |
| **Recommendation** | Extend Dependabot to cover `nuget` and `npm` ecosystems. Add a security gate in the CI pipeline that blocks on critical SonarCloud findings. When containerized, enable ECR image scanning. |
| **Evidence** | azure-pipelines.yml (SonarCloudPrepare@4, SonarCloudAnalyze@4, reportgenerator@5), .github/dependabot.yml (devcontainers only), src/Directory.Build.props (StyleCop.Analyzers) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Sentry SDK 4.0.2 is integrated (`src/NzbDrone.Common/Radarr.Common.csproj`) with source map uploads in the CI pipeline. Sentry provides error tracking and basic performance monitoring. NLog with structured logging (ClefJsonLayout) provides application-level log context. However, no OpenTelemetry SDK, no X-Ray SDK, no trace ID propagation across service boundaries. |
| **Gap** | Basic tracing on individual services (Sentry error tracking) but no cross-service trace propagation or distributed tracing standard (OpenTelemetry). |
| **Recommendation** | Add OpenTelemetry SDK for .NET to enable distributed tracing. When deployed to AWS, integrate with X-Ray for end-to-end trace visualization. |
| **Evidence** | src/NzbDrone.Common/Radarr.Common.csproj (Sentry 4.0.2), src/NzbDrone.Common/Instrumentation/Sentry/SentryTarget.cs, azure-pipelines.yml (Sentry source map upload) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs defined. No error budget tracking, no p99/p95 latency monitoring, no formal service level definitions. The HealthCheck system (`src/NzbDrone.Core/HealthCheck/`) provides internal health monitoring (disk space, indexer status, download client connectivity) but these are operational checks, not SLOs. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. |
| **Recommendation** | Define SLOs for key user journeys: API response time, movie search success rate, download completion rate. When deployed to AWS, implement SLO monitoring with CloudWatch. |
| **Evidence** | src/NzbDrone.Core/HealthCheck/ (operational health checks, not SLOs) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | `AnalyticsService` exists (`src/NzbDrone.Core/Analytics/AnalyticsService.cs`) but it appears to be a basic opt-in telemetry service, not business outcome metric publishing. No custom CloudWatch metrics, no business KPI dashboards, no conversion/success rate tracking. |
| **Gap** | No custom business metrics — only default infrastructure-level logging via NLog. |
| **Recommendation** | Publish business metrics (movies added per day, search success rate, download completion rate, notification delivery rate) to CloudWatch custom metrics when deployed to AWS. |
| **Evidence** | src/NzbDrone.Core/Analytics/AnalyticsService.cs |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The HealthCheck system (`src/NzbDrone.Core/HealthCheck/`) provides 30+ health checks covering indexer status, download client connectivity, disk space, root folder accessibility, update availability, database integrity, and more. Health check events trigger notifications via the notification system. However, these are static threshold checks (e.g., indexer offline, disk full), not anomaly detection on error rates or latency trends. |
| **Gap** | Static threshold health checks only — no anomaly detection on error rates or latency. |
| **Recommendation** | When deployed to AWS, enable CloudWatch anomaly detection on API error rates and response latency. Configure composite alarms for correlated failures. |
| **Evidence** | src/NzbDrone.Core/HealthCheck/Checks/ (30+ health check implementations) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Binary distribution via zip/tar archives for 12+ platform combinations. The CI pipeline produces packages but there is no deployment automation. The application has a built-in self-update mechanism (`src/NzbDrone.Core/Update/InstallUpdateService.cs`) that downloads and applies updates directly. No blue/green, canary, or rolling deployment strategy. No CodeDeploy, Argo Rollouts, or traffic shifting. |
| **Gap** | Direct-to-production deployment via self-update mechanism with no staged rollout, no traffic shifting, and no automated rollback. |
| **Recommendation** | When containerized on EKS (preferred), implement rolling deployments with health check gates as a baseline. Progress to canary deployments using Argo Rollouts or EKS-native traffic shifting. |
| **Evidence** | azure-pipelines.yml (Packages stage), src/NzbDrone.Core/Update/InstallUpdateService.cs |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration test suite exists. Azure Pipelines runs integration tests on Linux, Mac, Windows, and FreeBSD natively, plus Alpine Docker containers. PostgreSQL 14 and 15 integration tests validate database compatibility. Automation/UI tests run on all three major platforms. Integration tests are in `src/NzbDrone.Integration.Test/` covering API endpoints (movies, commands, history, queue, blocklist, etc.). All tests run in CI pipeline automatically. |
| **Gap** | Integration tests exist for primary workflows but some API endpoints may lack coverage. No contract tests for external service integrations (indexers, download clients). |
| **Recommendation** | Add contract tests for external service integrations. When deploying to AWS, extend integration tests to validate Aurora PostgreSQL compatibility. |
| **Evidence** | azure-pipelines.yml (Integration stage), src/NzbDrone.Integration.Test/ (20+ test fixtures), src/NzbDrone.Automation.Test/ |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, SSM Automation documents, or incident response workflows found. The HealthCheck system provides some self-healing patterns (health check → notification), but incident response is entirely ad hoc. No machine-readable runbooks, no automated remediation. |
| **Gap** | No runbooks — incident response is entirely ad hoc. |
| **Recommendation** | Create SSM Automation runbooks for common incidents (database connectivity failures, disk space exhaustion, indexer outages). Implement Lambda-based auto-remediation for recoverable failures. |
| **Evidence** | src/NzbDrone.Core/HealthCheck/ (health monitoring but no automated remediation) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file referencing observability assets. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution. The single Sentry project tracks errors but has no ownership model. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. |
| **Recommendation** | Establish observability ownership by creating per-domain dashboards and assigning alarm ownership when deploying to AWS. |
| **Evidence** | No CODEOWNERS file found, no dashboard definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud resources exist to tag (no IaC). No tagging standard, no tag enforcement, no cost allocation tags. |
| **Gap** | No tags found on resources — no cloud resources exist. |
| **Recommendation** | When creating IaC, implement a tagging standard from day one with required tags (Environment, Service, Owner, CostCenter) enforced via CDK/Terraform required_tags. |
| **Evidence** | No IaC found |

## Learning Materials

- **Move to Cloud Native**: [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Containers**: [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/)
- **Move to Managed Databases**: [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Modern DevOps**: [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| azure-pipelines.yml | INF-Q1, INF-Q2, INF-Q11, OPS-Q1, OPS-Q5, OPS-Q6, SEC-Q5, SEC-Q7, DATA-Q3 | Multi-stage CI/CD pipeline definition |
| .github/workflows/ci.yml | INF-Q11 | GitHub Actions CI workflow |
| .github/dependabot.yml | SEC-Q7 | Dependabot config (devcontainers only) |
| global.json | APP-Q1 | .NET SDK 8.0.405 version pin |
| package.json | APP-Q1 | Node.js/TypeScript/React dependencies |
| src/Directory.Build.props | APP-Q1, SEC-Q7 | .NET build props, Sentry config, StyleCop |
| src/NzbDrone.Core/Radarr.Core.csproj | APP-Q1, INF-Q2 | Core project NuGet dependencies |
| src/NzbDrone.Common/Radarr.Common.csproj | OPS-Q1, SEC-Q1, INF-Q2 | Common project with SQLite, Sentry, NLog |
| src/NzbDrone.Host/Radarr.Host.csproj | INF-Q6 | Host project with Swashbuckle, DryIoc |
| src/Radarr.Api.V3/Radarr.Api.V3.csproj | APP-Q5 | API V3 project dependencies |
| src/Radarr.Api.V3/openapi.json | APP-Q5 | OpenAPI 3.0.4 specification |
| src/NzbDrone.Core/Datastore/BasicRepository.cs | DATA-Q2, DATA-Q4, APP-Q2 | Centralized repository pattern |
| src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs | INF-Q2, SEC-Q2 | SQLite + PostgreSQL connection configuration |
| src/NzbDrone.Core/Datastore/SqlBuilder.cs | DATA-Q2 | Database-agnostic query building |
| src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs | DATA-Q2 | PostgreSQL-specific WHERE clause generation |
| src/NzbDrone.Core/Datastore/Migration/ | DATA-Q3, DATA-Q4 | 242+ FluentMigrator migrations |
| src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs | INF-Q3, APP-Q4 | Internal command queue pattern |
| src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs | INF-Q3, APP-Q4 | Command execution with status tracking |
| src/NzbDrone.Core/Messaging/Events/EventAggregator.cs | INF-Q4, APP-Q3 | In-process event pub/sub |
| src/NzbDrone.SignalR/MessageHub.cs | INF-Q4 | Real-time SignalR communication |
| src/NzbDrone.Core/Notifications/ | APP-Q3, INF-Q4 | 30+ notification providers (sync dispatch) |
| src/NzbDrone.Core/Download/Clients/ | APP-Q3 | 15+ download client integrations |
| src/NzbDrone.Core/Indexers/ | APP-Q3 | 10+ indexer integrations |
| src/NzbDrone.Core/Backup/BackupService.cs | INF-Q8 | Built-in application-level backup |
| src/NzbDrone.Host/SingleInstancePolicy.cs | INF-Q7 | Single instance enforcement |
| src/NzbDrone.Host/Startup.cs | INF-Q6, SEC-Q3 | ASP.NET Core Kestrel self-hosting |
| src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs | SEC-Q3 | API key authentication |
| src/NzbDrone.Core/Authentication/UserService.cs | SEC-Q4 | Local user management |
| src/NzbDrone.Core/HealthCheck/Checks/ | OPS-Q4 | 30+ operational health checks |
| src/NzbDrone.Core/Analytics/AnalyticsService.cs | OPS-Q3 | Basic telemetry service |
| src/NzbDrone.Core/Update/InstallUpdateService.cs | OPS-Q5, SEC-Q6 | Self-update mechanism |
| src/NzbDrone.Integration.Test/ | OPS-Q6 | Integration test suite |
| src/NzbDrone.Automation.Test/ | OPS-Q6 | UI automation test suite |
| src/NzbDrone.Core/MediaCover/MediaCoverService.cs | DATA-Q1 | Local filesystem media cover storage |
| src/NzbDrone.Core/MediaFiles/MediaFileService.cs | DATA-Q1 | Local filesystem media file management |
| src/NzbDrone.Core/Jobs/Scheduler.cs | INF-Q3 | Task scheduling |
| src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs | SEC-Q1 | Database-backed logging |
| src/Radarr.sln | APP-Q2 | Solution file with 20+ projects |
| src/Radarr.Http/VersionedApiControllerAttribute.cs | APP-Q5 | API versioning enforcement |
| distribution/ | INF-Q1 | Binary distribution packaging (Windows installer, macOS app) |
