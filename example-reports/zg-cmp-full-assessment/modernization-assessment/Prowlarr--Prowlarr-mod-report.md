# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Prowlarr |
| **Date** | 2025-07-17 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Indexer manager/proxy for the *arr suite. |
| **Overall Score** | 1.80 / 4.0 |

**Archetype Justification**: Prowlarr manages persistent state in SQLite/PostgreSQL databases with full CRUD operations on indexers, applications, notifications, download clients, and history. Write endpoints exist alongside reads across the `/api/v1/` surface. No fan-out to 3+ downstream services in an orchestration pattern. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.80 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — all infrastructure would need to be manually created (ClickOps) when deploying to AWS | Blocks reproducible deployments, disaster recovery, and environment consistency |
| 2 | INF-Q1: Managed Compute | 1 | Application is distributed as self-hosted binaries with no containerization or managed compute definitions | Prevents elastic scaling, increases operational overhead, blocks container/serverless modernization |
| 3 | INF-Q2: Managed Databases | 1 | Embedded SQLite by default with optional self-managed PostgreSQL — no managed database services | Creates manual patching, backup, and scaling burden; single point of failure risk |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or cloud-native audit logging; only application-level NLog | Cannot trace administrative actions for compliance or forensic analysis in cloud deployment |
| 5 | SEC-Q4: Centralized Identity Integration | 1 | Self-managed authentication with internal user table; no external IdP integration | Prevents SSO, increases security attack surface, inconsistent access management |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 3 (API versioning strategy exists) and OpenAPI 3.0.4 spec exists at `src/Prowlarr.Api.V1/openapi.json` with structured JSON responses across all `/api/v1/` endpoints.
- **What it enables:** An API-aware agent that discovers and invokes Prowlarr's existing REST endpoints as tools — managing indexers, triggering searches, checking application sync status, and managing download clients through natural language commands.
- **Additional steps:** The OpenAPI spec is already comprehensive (6,356 lines, covering all endpoints). Agent tool discovery can use this spec directly. Consider adding response examples to the spec for better agent reasoning.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (centralized `BasicRepository<T>` pattern with Dapper ORM provides a clean, documented data access layer).
- **What it enables:** A natural-language-to-SQL agent that queries indexer statistics, history, application sync status, and search results through conversational interfaces.
- **Additional steps:** Schema documentation would improve query accuracy. The `TableMapping.cs` file provides the entity-to-table mapping that an agent could use for schema discovery.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (Azure Pipelines CI/CD pipeline exists with build, test, and package stages).
- **What it enables:** A DevOps agent that triggers builds, checks pipeline status, monitors test results across platforms (Windows, Linux, macOS, FreeBSD), and manages release packaging.
- **Additional steps:** Azure DevOps API access would need to be configured for the agent. The pipeline already publishes test results and artifacts that an agent could monitor.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — `README.md` (comprehensive feature list), `CONTRIBUTING.md` (development guide links), `SECURITY.md` (vulnerability reporting), external wiki at `wiki.servarr.com/prowlarr`, and `docs.sh` for API documentation generation.
- **What it enables:** A RAG-based knowledge agent that indexes Prowlarr documentation and answers developer questions about indexer configuration, API usage, contribution guidelines, and troubleshooting.
- **Additional steps:** The wiki content at `wiki.servarr.com` would need to be crawled and indexed. The OpenAPI spec provides rich API documentation. Consider using Amazon Bedrock with a knowledge base backed by the indexed documentation.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolith), INF-Q1 = 1 (no managed compute), APP-Q3 = 2 (sync-dominant), APP-Q4 = 2 (inconsistent async patterns) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no managed compute), no Dockerfile or container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures); databases are already open source (SQLite, PostgreSQL) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (self-managed SQLite/PostgreSQL), DATA-Q3 = 2 (no version pinning in IaC) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected; contextual guard prevents trigger |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 3 (integration tests exist) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
Prowlarr is a monolithic .NET 8 application (APP-Q2 = 2) deployed as a self-contained binary across Windows, Linux, macOS, and FreeBSD. The solution contains ~20 projects within a single `Prowlarr.sln`, but these are libraries within a single deployable unit — one entry point (`NzbDrone/Prowlarr.csproj`), one self-hosted Kestrel web server, one shared SQLite/PostgreSQL database.

**Compute Model Gaps:**
All compute is self-hosted with no managed container orchestration or serverless (INF-Q1 = 1). No Dockerfiles, no ECS/EKS definitions, no Lambda functions.

**Communication Pattern Gaps:**
Inter-service communication is primarily synchronous HTTP (APP-Q3 = 2). Prowlarr makes outbound HTTP calls to indexer sites and downstream *arr applications. Internal event aggregator provides some async patterns but no cross-service messaging infrastructure. Background command processing exists (APP-Q4 = 2) but patterns are inconsistent.

**Recommended Decomposition Approach:**
See the Decomposition Strategy section below for detailed guidance. The Strangler Fig approach is recommended, starting with containerization of the existing monolith, then selectively extracting high-value services.

**Representative AWS Services:**
- **Amazon EKS** (preferred per technology preferences) for container orchestration
- **Amazon API Gateway** (preferred) as the managed API entry point with throttling and authentication
- **Amazon EventBridge** (preferred) for event-driven communication between decomposed services
- **AWS Step Functions** for workflow orchestration of multi-step indexer operations
- **AWS Lambda** for lightweight event-driven functions (if serverless is considered despite desktop preference)

**Recommended Patterns:**
- Strangler Fig pattern for incremental service extraction
- Anti-corruption Layer between new services and the existing monolith
- Event Sourcing for indexer state change tracking
- Hexagonal Architecture for new service boundaries

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
Prowlarr is distributed as self-contained .NET 8 binaries for 10+ platform/architecture combinations (win-x64, win-x86, linux-x64, linux-musl-x64, linux-arm, linux-arm64, linux-musl-arm, linux-musl-arm64, osx-x64, osx-arm64, freebsd-x64). No Dockerfile exists in the repository. No container orchestration configuration found.

**Container Readiness Indicators:**
- ✅ Application already runs on .NET 8 which has excellent container support
- ✅ Application already builds for linux-musl (Alpine-compatible) targets
- ✅ CI pipeline already tests in Docker containers (Alpine image for musl testing)
- ✅ Configuration externalized via environment variables (`Prowlarr__Postgres__*`)
- ✅ Application listens on a configurable port (default 9696)
- ⚠️ SQLite default storage requires volume mounts for persistence
- ⚠️ Data protection keys persisted to filesystem require volume configuration

**Recommended Container Orchestration Platform:**
**Amazon EKS** (preferred per technology preferences) — provides managed Kubernetes with Graviton-based node groups for cost optimization. Avoid self-managed Kubernetes as specified in technology preferences.

**Representative AWS Services:**
- **Amazon EKS** for container orchestration
- **Amazon ECR** for container image registry
- **AWS Fargate** for serverless container execution (if operational simplicity is prioritized)

**Migration Approach:**
1. **Phase 1 — Containerize as-is:** Create a Dockerfile based on the existing linux-musl build target. Use the `mcr.microsoft.com/dotnet/aspnet:8.0-alpine` base image. Mount volumes for SQLite data and configuration.
2. **Phase 2 — Orchestrate:** Deploy to Amazon EKS with Helm charts for configuration management. Configure persistent volume claims for database storage.
3. **Phase 3 — Migrate to managed database:** Switch from SQLite to Aurora PostgreSQL (see Move to Managed Databases pathway) to eliminate volume dependency for state.

**AWS Container Migration Guidance:**
- [Containerizing .NET applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-containerize-dotnet/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
- **Default:** Embedded SQLite — local file-based database with no network access, no automated failover, no Multi-AZ. Stored at the application's data directory.
- **Optional:** PostgreSQL via `Prowlarr__Postgres__*` environment variables — self-managed PostgreSQL instance (user provides host, port, user, password). No managed database IaC.
- **Connection management:** `ConnectionStringFactory.cs` handles both SQLite and PostgreSQL connection strings. Dapper ORM with `BasicRepository<T>` pattern.
- **Migrations:** 43+ FluentMigrator migrations in `src/NzbDrone.Core/Datastore/Migration/`.

**Engine Versions and EOL Status:**
- SQLite: Version not explicitly pinned (uses NuGet `System.Data.SQLite` package)
- PostgreSQL: Tested against versions 14 and 15 in CI pipeline. PostgreSQL 14 reaches EOL November 2026.

**Data Access Patterns:**
Centralized `BasicRepository<T>` pattern (DATA-Q2 = 4) provides a clean data access layer. No stored procedures or proprietary SQL (DATA-Q4 = 4). Migration to managed services has low data-layer friction.

**Recommended Managed Database Target:**
**Amazon Aurora PostgreSQL** (preferred per technology preferences) — Prowlarr already supports PostgreSQL as an alternative to SQLite. Migration path:
1. Deploy Aurora PostgreSQL cluster with Multi-AZ
2. Configure Prowlarr with Aurora endpoint via `Prowlarr__Postgres__*` environment variables
3. Run FluentMigrator migrations against Aurora (already supported)
4. Enable automated backups, PITR, and read replicas

**For future decomposition**, consider **Amazon DynamoDB** (preferred) for high-throughput indexer status tracking and search history, where the key-value access pattern matches well.

**Representative AWS Services:**
- **Amazon Aurora PostgreSQL** for primary relational database
- **Amazon DynamoDB** for key-value access patterns (future)
- **AWS DMS** for migration from existing PostgreSQL instances

**AWS Database Migration Guidance:**
- [Migrating to Aurora PostgreSQL](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-aurora-postgresql/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:**
No infrastructure-as-code exists (INF-Q10 = 1). Zero Terraform, CloudFormation, CDK, Helm charts, or Kustomize files found. All infrastructure would need to be manually created when deploying to AWS.

**Current CI/CD State:**
Azure Pipelines provides comprehensive CI with multi-stage pipeline (INF-Q11 = 3):
- ✅ Build stage: Multi-platform .NET 8 builds (Windows, Linux, macOS)
- ✅ Frontend build: Yarn/Webpack
- ✅ Unit tests: Multi-platform with PostgreSQL 14/15 matrix
- ✅ Integration tests: Multi-platform with PostgreSQL 14/15 matrix
- ✅ Automation tests: Multi-platform UI tests
- ✅ Code analysis: SonarCloud
- ✅ Packaging: Multi-platform archives and Windows installers
- ❌ No deployment stage — pipeline produces artifacts but does not deploy
- ❌ No automated rollback

**Deployment Strategy Gaps:**
No canary, blue/green, or rolling deployment strategy (OPS-Q5 = 1). Application is distributed as archives/installers for self-hosting. No deployment automation to cloud environments.

**Testing Gaps:**
Integration tests exist and run in CI (OPS-Q6 = 3). This is a strength. However, no contract tests or API backward-compatibility tests.

**Recommended DevOps Toolchain:**
1. **IaC:** AWS CDK (TypeScript or C#) or Terraform for defining EKS clusters, Aurora PostgreSQL, networking, and supporting services
2. **CI/CD:** Extend Azure Pipelines with deployment stages using AWS CodeDeploy, or migrate to a unified pipeline with AWS CodePipeline + CodeBuild
3. **Container Registry:** Amazon ECR for Docker image storage
4. **Deployment:** Helm charts for EKS deployments with canary or blue/green strategy via Argo Rollouts or AWS App Mesh
5. **GitOps:** ArgoCD for declarative Kubernetes deployments

**Representative AWS Services:**
- **AWS CDK** for infrastructure as code
- **AWS CodePipeline + CodeBuild** for CI/CD
- **Amazon ECR** for container registry
- **AWS CodeDeploy** for deployment automation

**AWS DevOps Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://aws.amazon.com/devops/)

---

## Decomposition Strategy

Since APP-Q2 = 2 (monolith with identifiable modules but shared database), decomposition guidance is provided below.

### Current Monolith Characteristics

Prowlarr is a modular monolith built as a single .NET 8 solution (`Prowlarr.sln`) containing ~20 projects:

| Module | Role | Dependencies |
|--------|------|-------------|
| `NzbDrone.Core` | Core business logic — indexers, applications, download clients, history, notifications, jobs, health checks | `NzbDrone.Common` |
| `NzbDrone.Host` | ASP.NET Core host — Startup, DI container, Kestrel configuration | Core, Common, SignalR, Api.V1, Http |
| `Prowlarr.Api.V1` | REST API controllers for all `/api/v1/` endpoints | Core, Http |
| `Prowlarr.Http` | HTTP middleware, authentication, frontend serving | Core, Common |
| `NzbDrone.SignalR` | Real-time UI communication via SignalR | Core, Common |
| `NzbDrone.Common` | Shared utilities — environment info, serialization, HTTP client | — |
| `NzbDrone.Update` | Self-update mechanism | Common |
| `NzbDrone.Windows` / `NzbDrone.Mono` | Platform-specific implementations | Common |

**Coupling signals:**
- All modules share a single SQLite/PostgreSQL database (high data coupling)
- `BasicRepository<T>` provides centralized data access (positive for extraction — clean interface)
- Internal `IEventAggregator` provides in-process pub/sub (could become cross-service messaging)
- `CommandQueue` manages background tasks within the process

### Decomposition Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2 = 2 — identifiable modules with coupling. Extract services incrementally while keeping the monolith running. | **Medium to High** — 6-18 months | ✅ **Recommended.** Lowest risk, incremental value. Start by extracting the indexer proxy and search service. |
| **Conditional / Adaptive** | Limited team capacity. Containerize the monolith first, then selectively extract high-value services. | **Low to Medium** — containerize in 2-4 weeks, selective extraction over 3-12 months | ✅ **Recommended as starting point.** Containerize first, migrate to Aurora PostgreSQL, then assess extraction needs. |
| **Big-Bang Rewrite** | Only if the monolith is unmaintainable. | **Very High** — 12-24+ months | ⚠️ **Recommended against.** Prowlarr has identifiable modules and a clean data access layer — incremental extraction is viable. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's data model | Every extraction — place an ACL between the new service and the remaining monolith | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions when indexer sync operations span multiple services | When extracting indexer sync to a separate service from application management | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture indexer state changes as events for audit and cross-service integration | When multiple services need to react to indexer state changes (e.g., sync to *arr apps) | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear ports and adapters | Every new service — ensures testability and infrastructure portability | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal | Assessment | Effort Impact |
|--------|--------|------------|---------------|
| Module boundaries | `Prowlarr.sln` has ~20 projects with clear namespaces (Core, Host, Api, Http, Common, SignalR) | Identifiable but coupled | Medium |
| Data coupling | Single shared database for all modules; `BasicRepository<T>` provides clean data access | High coupling but clean interface | High — database splitting required |
| Stored procedures | None — all business logic in application layer (DATA-Q4 = 4) | Low | Low — no database logic extraction needed |
| Communication patterns | Primarily synchronous HTTP; internal `IEventAggregator` for in-process events | Needs async infrastructure | Medium — add EventBridge for cross-service |
| CI/CD maturity | Azure Pipelines exists with build/test but no deployment (INF-Q11 = 3) | Partial | Medium — need deployment pipeline for multi-service |
| Test coverage | Integration tests exist (OPS-Q6 = 3) | Good | Low — existing tests reduce regression risk |

**Calibrated Estimate:** The Conditional/Adaptive approach is recommended as the starting point — containerize the monolith in 2-4 weeks, migrate to Aurora PostgreSQL in 4-6 weeks, then evaluate which modules warrant extraction. Full Strangler Fig extraction of the indexer proxy service is estimated at 3-6 months after containerization.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute definitions found. Prowlarr is distributed as self-contained .NET 8 binaries for 10+ platform/architecture combinations (win-x64, win-x86, linux-x64, linux-musl-x64, linux-arm, linux-arm64, osx-x64, osx-arm64, freebsd-x64). No Terraform `aws_ecs_*`, `aws_eks_*`, or `aws_lambda_*` resources. No Dockerfiles. No Kubernetes manifests. The application self-hosts using Kestrel on a user-provided machine. |
| **Gap** | All compute is self-managed with no containerization or managed service adoption. No path to elastic scaling or reduced operational overhead. |
| **Recommendation** | Containerize the application using the existing linux-musl build target as the base. Deploy to Amazon EKS (preferred) with Helm charts. See the Move to Containers pathway for detailed migration steps. |
| **Evidence** | `build.sh` (multi-platform packaging), `src/Directory.Build.props` (RuntimeIdentifiers), `azure-pipelines.yml` (build matrix), absence of Dockerfile/Kubernetes manifests |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application uses embedded SQLite by default (local file-based) with optional PostgreSQL support via environment variables (`Prowlarr__Postgres__Host`, `Port`, `User`, `Password`). No managed database IaC — no `aws_rds_*`, `aws_dynamodb_*`, or similar resources. Database connections are configured in `ConnectionStringFactory.cs` and `PostgresOptions.cs`. FluentMigrator manages 43+ schema migrations supporting both SQLite and PostgreSQL. |
| **Gap** | All databases are self-managed. SQLite provides no network access, no automated failover, no Multi-AZ. PostgreSQL is user-provisioned with no IaC managing it. |
| **Recommendation** | Migrate to Amazon Aurora PostgreSQL (preferred) with Multi-AZ deployment. Prowlarr already supports PostgreSQL — configure Aurora endpoint via existing `Prowlarr__Postgres__*` environment variables. Enable automated backups and PITR. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/PostgresOptions.cs`, `src/NzbDrone.Core/Prowlarr.Core.csproj` (Npgsql, System.Data.SQLite packages), `src/NzbDrone.Core/Datastore/Migration/` (43+ migration files) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prowlarr has a command queue system (`CommandQueue`, `CommandQueueManager`, `CommandExecutor` in `src/NzbDrone.Core/Messaging/Commands/`) that provides structured background task execution with priority ordering, deduplication, and status tracking. A `Scheduler` (`src/NzbDrone.Core/Jobs/Scheduler.cs`) manages periodic tasks. However, these are in-process implementations — not dedicated workflow orchestration services. No AWS Step Functions, Temporal, or equivalent. |
| **Gap** | Multi-step workflows (indexer sync, application sync, search-and-download) are implemented as hardcoded command sequences within the application process. No visual workflow management, no external error handling/retry infrastructure. |
| **Recommendation** | For the current monolith, the in-process command queue is adequate. When decomposing to microservices, introduce AWS Step Functions for multi-step workflows like indexer sync across multiple *arr applications. EventBridge (preferred) can replace the internal `IEventAggregator` for cross-service events. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure. Prowlarr uses SignalR (`src/NzbDrone.SignalR/`) for real-time UI push notifications and an internal `IEventAggregator` for in-process pub/sub events. No SQS, SNS, EventBridge, MSK, or Kinesis. No self-managed Kafka or RabbitMQ. As a stateful-crud service, Prowlarr's cross-service interactions (syncing indexer configurations to Sonarr, Radarr, etc.) are entirely synchronous HTTP — state changes are not propagated via events. |
| **Gap** | For stateful-crud, cross-service state changes should use async messaging for decoupling. Prowlarr syncs indexer configurations to downstream *arr applications via synchronous HTTP calls, creating tight coupling and failure propagation risk. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for asynchronous propagation of indexer state changes to downstream *arr applications. This decouples Prowlarr from the availability of each downstream app and enables retry/dead-letter handling. |
| **Evidence** | `src/NzbDrone.SignalR/` (SignalR for UI), `src/NzbDrone.Core/Messaging/Events/` (internal event aggregator), `src/NzbDrone.Core/Applications/` (synchronous HTTP sync to *arr apps), absence of SQS/SNS/EventBridge/MSK resources |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security group, NACL, or network segmentation configuration found. No IaC exists. Application self-hosts on user-provided infrastructure with no network isolation defined. The `Startup.cs` configures forwarded headers for private network ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) indicating reverse proxy awareness, but no cloud network topology is defined. |
| **Gap** | Services would be deployed without network isolation if moved to AWS without IaC. No private subnets, no security groups, no VPC endpoints. |
| **Recommendation** | Define VPC with private subnets for application compute (EKS nodes) and database (Aurora). Use security groups with least-privilege rules. Deploy VPC endpoints for AWS service access (ECR, S3, Secrets Manager). Consider API Gateway (preferred) as the public entry point. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (forwarded headers config), absence of any `.tf`, CloudFormation, or CDK files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync defined. Application self-hosts with ASP.NET Core Kestrel on port 9696. No throttling, no managed authentication at the gateway level, no request validation beyond application-level middleware. CORS is configured to allow any origin (`AllowAnyOrigin()` in `Startup.cs`). |
| **Gap** | Direct service exposure without managed entry point. No throttling, no WAF, no DDoS protection, no centralized auth at the gateway. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the managed entry point. Configure throttling, request validation, and authentication (migrate from API key to OAuth2/JWT via Cognito). Use CloudFront for frontend static asset delivery and caching. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (Kestrel self-hosting, CORS configuration, port 9696), absence of API Gateway/ALB/CloudFront resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or Kubernetes HPA. Application runs as a single process on user-provided infrastructure with no scaling capability. |
| **Gap** | No auto-scaling — all capacity is statically provisioned. Cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | When containerized on EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on CPU/memory metrics. Configure Aurora PostgreSQL auto-scaling for read replicas. Consider Karpenter for EKS node auto-scaling. |
| **Evidence** | Absence of any auto-scaling configuration in repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application has built-in backup functionality (`src/NzbDrone.Core/Backup/BackupService.cs`, `MakeDatabaseBackup.cs`) that creates local backup files. However, no cloud-native backup configuration exists — no `aws_backup_plan`, no `backup_retention_period` on any database resource, no S3 cross-region replication. Backups are stored locally with no offsite copy. |
| **Gap** | Backups are application-managed and stored locally. No automated cloud backup, no PITR, no cross-region replication, no tested restore procedures. |
| **Recommendation** | When migrated to Aurora PostgreSQL, enable automated backups with 7+ day retention and PITR. Configure AWS Backup for comprehensive backup management. Implement cross-region backup replication for disaster recovery. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, `src/NzbDrone.Core/Backup/MakeDatabaseBackup.cs`, absence of AWS backup resources |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration. Application runs as a single process on a single host. SQLite is inherently single-node. No AZ configuration found in any infrastructure definition (none exists). |
| **Gap** | Single point of failure. An AZ failure or host failure takes down the entire service with no automatic recovery. |
| **Recommendation** | Deploy to EKS (preferred) with pods distributed across 2+ AZs. Use Aurora PostgreSQL Multi-AZ for database high availability. Configure load balancing across AZs. |
| **Evidence** | Absence of any multi-AZ or HA configuration; single-process application architecture |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files found in the repository. No Terraform (`.tf`), CloudFormation templates, CDK stacks, Helm charts, or Kustomize files. All infrastructure for running Prowlarr must be manually provisioned. The repository contains only application source code, CI/CD pipeline definitions, and build scripts. |
| **Gap** | 0% IaC coverage. All infrastructure is manual (ClickOps). Non-reproducible, error-prone, and blocks automated disaster recovery. |
| **Recommendation** | Create IaC using AWS CDK (C# — aligns with team's .NET expertise) or Terraform to define: VPC and networking, EKS cluster, Aurora PostgreSQL, API Gateway, ECR repositories, CloudWatch alarms, and backup plans. Start with a foundational VPC + EKS + Aurora module. |
| **Evidence** | Absence of any `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive Azure Pipelines configuration (`azure-pipelines.yml`) with 8 stages: Setup, Build_Backend (multi-platform), Build_Frontend, Installer, Packages (multi-platform archives), Unit_Test (multi-platform including PostgreSQL 14/15 matrix), Integration (multi-platform including PostgreSQL 14/15 matrix, Docker Alpine), Automation (UI tests), and Analyze (SonarCloud, code coverage). GitHub Actions workflow (`.github/workflows/ci.yml`) for ATX transforms. Pipeline includes build, test, and package stages with published test results and artifacts. |
| **Gap** | No deployment stage — pipeline produces artifacts but does not deploy to any environment. No automated rollback capability. No deployment to staging or production environments. |
| **Recommendation** | Add deployment stages to the pipeline: push container images to ECR, deploy to EKS staging via Helm/ArgoCD, run smoke tests, promote to production with canary deployment using Argo Rollouts. Implement automated rollback on health check failures. |
| **Evidence** | `azure-pipelines.yml` (8 stages, multi-platform builds, PostgreSQL matrix testing, SonarCloud), `.github/workflows/ci.yml` (ATX transforms), `test.sh` (test runner), `.github/dependabot.yml` (devcontainer updates only) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Backend: C# with .NET 8 (`global.json` specifies SDK 8.0.405). Frontend: TypeScript/React with Node.js 20. C#/.NET has good AWS SDK coverage (`AWSSDK.Core` and service-specific packages available for .NET), and .NET 8 has excellent container support (minimal images, AOT compilation). However, the cloud-native tooling ecosystem is narrower than Python/TypeScript/Go. |
| **Gap** | Minor — C#/.NET 8 is well-supported on AWS but has fewer cloud-native framework options compared to TypeScript or Python. AWS CDK supports C# as a first-class language. |
| **Recommendation** | C#/.NET 8 is a strong choice for AWS modernization. Use AWS SDK for .NET for service integrations. Consider AWS CDK in C# for IaC to leverage team expertise. .NET 8 container images are well-optimized for EKS deployment. |
| **Evidence** | `global.json` (SDK 8.0.405), `src/Directory.Build.props` (net8.0 target), `package.json` (TypeScript/React frontend), `src/NzbDrone.Core/Prowlarr.Core.csproj` (C# packages) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prowlarr is a single deployable monolith. The `Prowlarr.sln` solution contains ~20 projects, but these are libraries within a single application — one entry point (`NzbDrone/Prowlarr.csproj`), one self-hosted Kestrel web server, one shared SQLite/PostgreSQL database. The projects form identifiable modules: Core (business logic), Host (web server), Api.V1 (REST controllers), Http (middleware/auth), Common (utilities), SignalR (real-time), Windows/Mono (platform-specific). However, modules share a single database with no schema separation, and `NzbDrone.Core` contains nearly all business logic in one assembly. |
| **Gap** | Single deployable unit with shared database prevents independent scaling, deployment, and team autonomy. Cross-module data access through shared `BasicRepository<T>` creates coupling. Module boundaries exist at the project level but not at the data level. |
| **Recommendation** | See Decomposition Strategy section. Start with the Conditional/Adaptive approach: containerize the monolith, migrate to Aurora PostgreSQL, then evaluate selective extraction of the indexer proxy/search service as the first candidate. |
| **Evidence** | `src/Prowlarr.sln` (~20 projects), `src/NzbDrone.Host/Prowlarr.Host.csproj` (single Host project referencing all modules), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (shared data access), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (single database connection) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | As a stateful-crud service, Prowlarr's communication is primarily synchronous HTTP. Outbound calls to indexer sites (search queries, RSS feeds) and downstream *arr applications (Sonarr, Radarr, Lidarr sync) are synchronous HTTP via `HttpClient`. The internal `IEventAggregator` provides in-process async event handling for UI notifications (via SignalR) and some background processing, but this does not extend to cross-service boundaries. No external messaging infrastructure (SQS, SNS, EventBridge) exists. |
| **Gap** | For a stateful-crud service, cross-service state propagation should use async patterns. Indexer configuration sync to downstream *arr applications is synchronous, creating coupling and failure propagation risk. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for asynchronous propagation of indexer state changes. Replace synchronous sync calls to *arr apps with event publishing. Keep synchronous HTTP for user-facing search queries where immediate response is needed. |
| **Evidence** | `src/NzbDrone.Core/Applications/` (synchronous HTTP sync implementations for Sonarr, Radarr, Lidarr, etc.), `src/NzbDrone.Core/Messaging/Events/` (internal `IEventAggregator`), `src/NzbDrone.SignalR/` (SignalR for UI), `package.json` (`@microsoft/signalr` dependency) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prowlarr has a `CommandQueue` (`src/NzbDrone.Core/Messaging/Commands/`) that provides background job processing with priority ordering, status tracking (`CommandStatus`: Queued, Started, Completed, Failed), and deduplication. Indexer searches, application syncs, and scheduled tasks are dispatched through this queue. However, the command queue is in-process with no external job tracking API. Some operations (bulk indexer search across many sites) could exceed 30 seconds and are processed asynchronously via the command queue, but status polling is internal to the UI via SignalR rather than a structured async job API. |
| **Gap** | Background processing exists but patterns are inconsistent. The command queue provides some async handling, but there is no structured status polling API for external consumers. Long-running operations are not consistently tracked with progress updates. |
| **Recommendation** | Formalize the command/job pattern with a proper async job API that returns a job ID and supports status polling. When decomposing, move long-running workflows (bulk sync, multi-site search) to AWS Step Functions for managed orchestration with built-in retry, error handling, and status tracking. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandStatus.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Consistent URL-path versioning (`/api/v1/`) applied across all API endpoints. The OpenAPI 3.0.4 specification (`src/Prowlarr.Api.V1/openapi.json`, 6,356 lines) documents the full API surface. The `Prowlarr.Api.V1` namespace and `VersionedApiControllerAttribute` enforce versioning at the framework level. All endpoints follow the `/api/v1/{resource}` pattern. However, only v1 exists — no evidence of backward compatibility guarantees or deprecation strategy for future versions. |
| **Gap** | Only v1 exists with no documented backward compatibility policy or deprecation strategy. No version negotiation via headers. |
| **Recommendation** | Document a backward compatibility policy for the v1 API. When introducing breaking changes, implement v2 endpoints in a separate `Prowlarr.Api.V2` namespace while maintaining v1 for a deprecation period. The existing versioning infrastructure supports this cleanly. |
| **Evidence** | `src/Prowlarr.Api.V1/openapi.json` (all endpoints under `/api/v1/`), `src/Prowlarr.Http/` (VersionedApiControllerAttribute), `src/NzbDrone.Host/Startup.cs` (Swagger configuration with v1 doc) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prowlarr is a single application that communicates with external services (indexer sites, downstream *arr applications). Downstream *arr application URLs are configured via user settings stored in the database (not environment variables or service discovery). Indexer endpoints are configured per-indexer in the database. No AWS Service Discovery, Consul, Istio, or other service mesh/registry. |
| **Gap** | All service endpoints are user-configured and stored in the database. No dynamic discovery. Adding a new *arr application integration requires configuration through the UI. |
| **Recommendation** | For the current monolith, database-stored configuration is adequate. When decomposing to microservices on EKS, implement Kubernetes-native service discovery (CoreDNS) and consider AWS Cloud Map for cross-namespace discovery. API Gateway (preferred) can serve as the service catalog for external consumers. |
| **Evidence** | `src/NzbDrone.Core/Applications/` (application definitions with URL settings stored in DB), `src/NzbDrone.Core/Indexers/IndexerDefinition.cs` (indexer URL settings), absence of service discovery infrastructure |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Prowlarr primarily handles structured data (indexer configurations, search results, history records, application sync state). However, some unstructured data exists: indexer definitions (YAML/XML files parsed by Cardigann), torrent files, NZB files, and RSS feed content. These are processed in-memory or stored temporarily on the local file system. No S3, Textract, or managed object storage found. No document parsing pipeline. |
| **Gap** | Unstructured content (torrent/NZB files, parsed indexer definitions) is handled in-memory or on local file system with no managed storage or parsing pipeline. |
| **Recommendation** | When migrated to AWS, store indexer definition files, torrent files, and NZB content in Amazon S3. This enables versioning, durability, and accessibility. For indexer definitions, S3 + Lambda trigger could automate definition validation and deployment. |
| **Evidence** | `src/NzbDrone.Core/Indexers/` (indexer parsers for RSS, Torznab, Newznab), absence of S3 or managed object storage resources |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Prowlarr uses a centralized `BasicRepository<T>` pattern (`src/NzbDrone.Core/Datastore/BasicRepository.cs`) with Dapper ORM for all database access. The repository provides standardized CRUD operations (Insert, Update, Delete, Get, GetPaged, Upsert), pagination, filtering, and event publishing. All entity repositories extend `BasicRepository<T>`. `TableMapping.cs` provides centralized entity-to-table mapping. `SqlBuilder` provides query construction. `WhereBuilder` (with SQLite and PostgreSQL variants) handles dialect-specific query generation. Database connections are managed centrally by `ConnectionStringFactory`. |
| **Gap** | None — data access is well-centralized through the repository pattern. |
| **Recommendation** | The centralized data access layer is a modernization strength. It will facilitate database migration (SQLite → Aurora PostgreSQL) with minimal code changes. Maintain this pattern when decomposing services — each service should own its data through its own repository instance. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/TableMapping.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SQLite: Version not explicitly pinned — uses the `System.Data.SQLite` NuGet package version bundled with the .NET SDK. No explicit version declaration in IaC (none exists). PostgreSQL: Not pinned in application configuration — user provides the PostgreSQL host. CI pipeline tests against PostgreSQL 14 and 15 (explicit Docker image tags in `azure-pipelines.yml`). PostgreSQL 14 reaches EOL November 2026. No documented version update procedure. |
| **Gap** | Database engine versions are not pinned in IaC (no IaC exists). PostgreSQL 14 is approaching EOL. No documented version update procedure with downtime windows, rollback plans, or risk acknowledgment. |
| **Recommendation** | When deploying Aurora PostgreSQL, explicitly pin the engine version in IaC (e.g., `engine_version = "15.4"` in Terraform or CDK). Document a version update procedure. Ensure CI tests cover the Aurora PostgreSQL version being deployed. |
| **Evidence** | `azure-pipelines.yml` (PostgreSQL 14 and 15 Docker containers in test stages), `src/NzbDrone.Core/Prowlarr.Core.csproj` (Npgsql 9.0.3, System.Data.SQLite via FluentMigrator.Runner.SQLite), `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found. All business logic is in the C# application layer. Database schema is managed through FluentMigrator migrations (43+ files in `src/NzbDrone.Core/Datastore/Migration/`). Data access uses Dapper with parameterized SQL queries generated by `SqlBuilder`. The `WhereBuilder` classes handle SQLite vs PostgreSQL dialect differences for query construction, but all queries are standard SQL without proprietary extensions. No `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` found. |
| **Gap** | None — all business logic is cleanly in the application layer. |
| **Recommendation** | This is a modernization strength. The absence of stored procedures and proprietary SQL means the database can be migrated to Aurora PostgreSQL with minimal friction. Maintain this pattern — keep business logic in the application layer. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (43+ C# FluentMigrator migrations — no SQL files), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Dapper queries), `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, absence of `.sql` files |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud-native audit logging found. Application uses NLog for application-level logging with configurable targets (console, file, Syslog via `NLog.Targets.Syslog`, database via `DatabaseTarget.cs`). Sentry integration for error tracking and crash reporting (`ReconfigureSentry.cs`). However, these are application logs, not audit logs — there is no structured record of administrative actions (who changed what, when) suitable for compliance or forensic analysis. |
| **Gap** | No cloud audit logging. Application logs exist but are not structured for audit compliance. No immutable log storage. No log file validation. |
| **Recommendation** | When deployed to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Implement application-level audit logging for administrative actions (indexer configuration changes, user management, application sync modifications) published to CloudWatch Logs with structured JSON format. |
| **Evidence** | `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `src/NzbDrone.Core/Prowlarr.Core.csproj` (NLog, NLog.Targets.Syslog packages), absence of CloudTrail or audit log resources |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration found. SQLite databases are stored as unencrypted files on the local file system. No KMS key references, no `kms_key_id` on any resource (no IaC exists). No encryption configuration for data protection keys (stored via `DataProtection.PersistKeysToFileSystem` in `Startup.cs`). |
| **Gap** | No encryption at rest for any data store. SQLite files, data protection keys, and configuration files are stored unencrypted. |
| **Recommendation** | When deployed to AWS: enable KMS encryption on Aurora PostgreSQL, enable S3 server-side encryption with customer-managed keys for any object storage, enable EBS encryption for EKS node volumes. Configure a centralized key management policy with documented rotation schedule. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (DataProtection.PersistKeysToFileSystem — unencrypted), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (SQLite connection — no encryption parameters), absence of KMS or encryption resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API uses static API key authentication via `X-Api-Key` header or `apikey` query parameter (`ApiKeyAuthenticationHandler.cs`). The API key is a single shared secret configured in the application settings. Also supports `Bearer` token in Authorization header (parsed in `ApiKeyAuthenticationHandler.cs`), but this is a direct key comparison, not OAuth2/JWT token validation. Forms-based authentication exists for the web UI (`AuthenticationController.cs`). No OAuth2 flows, no JWT validation, no Cognito integration. |
| **Gap** | API key authentication is static — no token expiration, no per-user authorization, no token refresh. Single shared API key means all API consumers have identical permissions. No fine-grained access control. |
| **Recommendation** | Migrate to OAuth2/JWT authentication using Amazon Cognito as the identity provider. API Gateway (preferred) can handle JWT validation at the gateway level, offloading auth from the application. Implement per-user API tokens with scoped permissions and expiration. |
| **Evidence** | `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs` (API key security scheme in Swagger config), `src/Prowlarr.Api.V1/openapi.json` (X-Api-Key and apikey security definitions) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application manages its own authentication entirely. `UserService.cs` and `UserRepository.cs` in `src/NzbDrone.Core/Authentication/` handle user management with an internal `Users` table. Password hashing uses `Microsoft.AspNetCore.Cryptography.KeyDerivation`. The `AuthenticationService.cs` in `src/Prowlarr.Http/Authentication/` handles login via forms. No Cognito, OIDC, SAML, or any external IdP integration found. |
| **Gap** | Self-managed authentication with no external IdP. No SSO capability. Each Prowlarr instance maintains its own user database. Increases attack surface and prevents unified access management. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. Implement OIDC authentication flow with Cognito user pools. This enables SSO across the *arr suite, MFA support, and centralized user lifecycle management. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/Prowlarr.Http/Authentication/AuthenticationService.cs`, `src/NzbDrone.Core/Prowlarr.Core.csproj` (Microsoft.AspNetCore.Cryptography.KeyDerivation) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | PostgreSQL database credentials are configured via environment variables (`Prowlarr__Postgres__Host`, `Prowlarr__Postgres__Port`, `Prowlarr__Postgres__User`, `Prowlarr__Postgres__Password` — see `PostgresOptions.cs`). API keys are stored in the application's configuration file. CI pipeline uses Azure DevOps variables and GitHub secrets for sensitive values (Sentry tokens, Discord webhooks). No AWS Secrets Manager, HashiCorp Vault, or SSM Parameter Store integration. No rotation configured. |
| **Gap** | Database credentials in environment variables with no rotation. API keys in application config files. No centralized secrets management. No audit trail for secret access. |
| **Recommendation** | Store all secrets in AWS Secrets Manager with automated rotation. Configure Prowlarr to retrieve PostgreSQL credentials from Secrets Manager at startup. Use Kubernetes external-secrets-operator to sync Secrets Manager values to Kubernetes secrets for EKS deployment. |
| **Evidence** | `src/NzbDrone.Core/Datastore/PostgresOptions.cs` (environment variable binding), `azure-pipelines.yml` (sentryAuthTokenServarr, githubToken, discordWebhookKey as pipeline variables), `.github/workflows/ci.yml` (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY as GitHub secrets) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy found. Application is distributed as self-contained .NET 8 binaries — the runtime and all dependencies are bundled. No SSM Agent, no Patch Manager, no Inspector, no vulnerability scanning configuration. The self-update mechanism (`NzbDrone.Update`) handles application-level updates but not OS or runtime patching. |
| **Gap** | No patching strategy for OS, runtime, or dependencies. No vulnerability scanning. Self-hosted deployments rely entirely on the operator for system-level security. |
| **Recommendation** | When containerized: use AWS-maintained base images (e.g., ECR public `dotnet/aspnet:8.0` or Bottlerocket for EKS nodes). Enable Amazon ECR image scanning for vulnerability detection. Configure AWS Systems Manager for node patching on EKS managed node groups. Integrate Snyk or Trivy container scanning into the CI pipeline. |
| **Evidence** | `src/NzbDrone.Update/` (self-update mechanism for application only), `src/Directory.Build.props` (runtime identifiers for self-contained deployment), absence of any patching or vulnerability scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud analysis is integrated in Azure Pipelines (`SonarCloudPrepare@3` and `SonarCloudAnalyze@3` tasks in the Analyze stage) with project-level exclusions for test files and external modules. StyleCop analyzers are configured via `Directory.Build.props` for code style enforcement. Dependabot is configured but only for devcontainers (`package-ecosystem: "devcontainers"`), not for NuGet or npm dependencies. No SAST tool (Semgrep, CodeGuru) in the pipeline. No container image scanning (no containers exist). |
| **Gap** | SonarCloud provides some code quality analysis but is not a full SAST tool. Dependabot does not cover NuGet or npm dependencies. No dependency vulnerability scanning (`dotnet list package --vulnerable`, `npm audit`) in the pipeline. No security gate blocking on critical findings. |
| **Recommendation** | Enable Dependabot for NuGet and npm ecosystems. Add `dotnet list package --vulnerable` and `npm audit` steps to the pipeline. Integrate a SAST tool (Amazon CodeGuru Reviewer or Semgrep) into the CI pipeline. Add a security gate that blocks the build on critical or high severity findings. When containerized, add ECR image scanning. |
| **Evidence** | `azure-pipelines.yml` (SonarCloud integration in Analyze stage), `src/Directory.Build.props` (StyleCop.Analyzers.Unstable package), `.github/dependabot.yml` (devcontainers only), absence of SAST tools or dependency vulnerability scanning |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No OpenTelemetry SDK in dependency manifests. No X-Ray SDK. No `traceparent` or `X-Amzn-Trace-Id` header propagation. Application uses NLog for structured logging and Sentry (`@sentry/browser` in frontend, `ReconfigureSentry.cs` in backend) for error tracking and crash reporting, but these are not distributed tracing solutions — they do not propagate trace IDs across service boundaries or provide request flow visualization. |
| **Gap** | No distributed tracing. Cannot trace request flows across Prowlarr and downstream *arr applications. Cannot identify latency bottlenecks in the indexer search pipeline. |
| **Recommendation** | Instrument with AWS X-Ray SDK for .NET or OpenTelemetry (OTEL) .NET SDK. Propagate trace context headers in outbound HTTP calls to indexer sites and *arr applications. When deployed on EKS, use ADOT (AWS Distro for OpenTelemetry) collector for trace aggregation. |
| **Evidence** | `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` (Sentry error tracking — not tracing), `src/NzbDrone.Core/Prowlarr.Core.csproj` (NLog packages — no OTEL), `package.json` (`@sentry/browser` — not tracing), absence of OpenTelemetry or X-Ray packages |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No CloudWatch alarms on p99/p95 latency. No error budget tracking. No SLO dashboards. The application has health checks (`src/NzbDrone.Core/HealthCheck/`) that verify internal component health (indexer connectivity, application sync status, disk space), but these are operational health checks, not SLO definitions for user-facing journeys. |
| **Gap** | No formal SLO definitions. Cannot measure whether the system meets user expectations for search latency, indexer sync reliability, or API availability. |
| **Recommendation** | Define SLOs for critical user journeys: indexer search latency (p99 < 5s), application sync success rate (> 99.5%), API availability (> 99.9%). Implement CloudWatch metrics and alarms to track SLO compliance. Set up error budget tracking and alerting. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational health checks only), absence of SLO definitions, CloudWatch alarms, or error budget configuration |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Internal indexer statistics exist (`src/NzbDrone.Core/IndexerStats/IndexerStatistics.cs`, `IndexerStatisticsService.cs`) that track per-indexer query counts and response times. However, these metrics are stored in the local database and surfaced only through the UI — they are not published to any external monitoring system (CloudWatch, Prometheus, Datadog). No custom metrics publishing code found. Only internal application metrics exist. |
| **Gap** | Business metrics are tracked internally but not published to a monitoring system. Cannot build dashboards, set alerts, or correlate business metrics with infrastructure metrics. |
| **Recommendation** | Publish indexer statistics (query counts, success rates, response times per indexer) as CloudWatch custom metrics. Add business metrics for application sync events, search throughput, and download client activity. Build CloudWatch dashboards combining business and infrastructure metrics. |
| **Evidence** | `src/NzbDrone.Core/IndexerStats/IndexerStatistics.cs`, `src/NzbDrone.Core/IndexerStats/IndexerStatisticsService.cs`, absence of CloudWatch `put_metric_data` or Prometheus metrics endpoint |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found. No CloudWatch anomaly detection. No static threshold alarms. No PagerDuty or OpsGenie integration. The application has internal health checks that detect component failures, but these are surfaced only in the UI — not integrated with external alerting systems. |
| **Gap** | No alerting of any kind. Component failures are only visible through the application UI, not pushed to on-call teams. |
| **Recommendation** | When deployed to AWS: configure CloudWatch alarms for error rates, latency, and resource utilization. Enable CloudWatch anomaly detection on critical metrics. Integrate with SNS for alert notification and PagerDuty/OpsGenie for on-call routing. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (UI-only health checks), absence of CloudWatch alarms, anomaly detection, or alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. Azure Pipelines builds and packages artifacts but does not deploy. Application is distributed as archives and installers for self-hosting. Users manually download and install updates. The self-update mechanism (`NzbDrone.Update`) replaces the application binary on the local machine — this is not a cloud deployment strategy. No blue/green, canary, rolling deployment, or traffic shifting configuration. |
| **Gap** | No deployment automation, no staged rollout, no traffic shifting. All deployments are manual (user downloads new version). No rollback capability beyond reverting to previous binary. |
| **Recommendation** | Implement canary deployments on EKS (preferred) using Argo Rollouts or Flagger. Define progressive delivery pipeline: deploy to canary (5% traffic), monitor error rates and latency, promote to full deployment or auto-rollback on failure. Configure AWS CodeDeploy for ECS/EKS deployment automation if using AWS-native tooling. |
| **Evidence** | `azure-pipelines.yml` (build/test/package stages only — no deploy), `src/NzbDrone.Update/` (self-update binary replacement), `distribution/` (installer scripts), absence of deployment configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration test suite exists in `src/NzbDrone.Integration.Test/` with API tests (`ApiTests/` directory), CORS tests, HTTP log tests, and generic API fixture tests. Integration tests run in Azure Pipelines across multiple platforms (Windows, macOS, Linux, Alpine Docker, FreeBSD) and with PostgreSQL 14 and 15 databases. Automation tests (`src/NzbDrone.Automation.Test/`) provide UI-level testing. Test runner (`test.sh`) supports Unit, Integration, and Automation test categories. Tests are run as a mandatory pipeline stage. |
| **Gap** | Integration tests exist and run in CI but there are no contract tests to verify API backward compatibility. No end-to-end tests that verify integration with actual downstream *arr applications. Some platform combinations may have gaps (FreeBSD integration tests have `failTaskOnMissingResultsFile: false`). |
| **Recommendation** | Add API contract tests (e.g., using Pact or OpenAPI-based validation) to prevent breaking changes. Add end-to-end smoke tests that verify the complete search → download client → *arr app sync flow. Ensure all platform integration tests are required to pass. |
| **Evidence** | `src/NzbDrone.Integration.Test/` (API integration tests), `src/NzbDrone.Automation.Test/` (UI automation tests), `azure-pipelines.yml` (Integration and Automation stages with multi-platform matrix), `test.sh` (test runner with Unit/Integration/Automation categories) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks found. No Systems Manager Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. The `SECURITY.md` describes vulnerability reporting (via Discord or email) but does not constitute an operational incident response procedure. |
| **Gap** | No runbooks, no automated remediation, no incident response workflow. Incident response is entirely ad hoc. |
| **Recommendation** | Create runbooks for common incident scenarios (database connection failure, indexer timeout spike, disk space exhaustion, failed sync). Implement as AWS Systems Manager documents or structured YAML/Markdown in the repository. Add Lambda-based auto-remediation for self-healing patterns (e.g., restart unhealthy pods, clear stale connections). |
| **Evidence** | `SECURITY.md` (vulnerability reporting only), absence of runbooks, SSM documents, or automated remediation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for observability configurations. No per-service dashboards. No named alarm owners. No SLO definitions with team attribution. No team tags on monitoring resources. The application's health check system (`HealthCheckService.cs`) provides internal component status but has no external ownership attribution. |
| **Gap** | No observability ownership. Monitoring gaps will emerge without clear team accountability for dashboards, alarms, and SLO tracking. |
| **Recommendation** | Define observability ownership: assign dashboard and alarm ownership to specific team members in CODEOWNERS. Create per-component dashboards (indexer health, application sync status, search performance) with named owners. Tag all CloudWatch resources with team attribution. |
| **Evidence** | Absence of CODEOWNERS for observability, absence of dashboards or named alarm owners, `src/NzbDrone.Core/HealthCheck/` (no external ownership) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging found — no IaC resources exist to tag. No `default_tags` in Terraform provider (no Terraform). No `tags` on any resources. No tag policies or Config rules. |
| **Gap** | Zero tagging. When resources are created on AWS, there will be no cost allocation, ownership identification, or environment distinction without a tagging standard. |
| **Recommendation** | Define a tagging standard before creating IaC. Required tags: `Environment` (dev/staging/prod), `Service` (prowlarr), `Owner` (team name), `CostCenter`, `ManagedBy` (terraform/cdk). Implement `default_tags` in Terraform provider or `Tags.of()` in CDK. Enforce via AWS Config `required-tags` rule. |
| **Evidence** | Absence of any IaC resources or tagging configuration |

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
| `azure-pipelines.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q5, SEC-Q7, DATA-Q3 | 8-stage CI pipeline with multi-platform builds, test matrix, SonarCloud analysis |
| `.github/workflows/ci.yml` | INF-Q11 | GitHub Actions workflow for ATX transforms |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot configured for devcontainers only |
| `global.json` | APP-Q1 | .NET SDK version 8.0.405 |
| `package.json` | APP-Q1, APP-Q3, OPS-Q1 | Frontend dependencies (React, TypeScript, SignalR, Sentry) |
| `build.sh` | INF-Q1 | Multi-platform build and packaging script |
| `test.sh` | OPS-Q6 | Test runner supporting Unit/Integration/Automation categories |
| `src/Directory.Build.props` | APP-Q1, INF-Q1, SEC-Q6, SEC-Q7 | Build configuration, runtime identifiers, StyleCop analyzers |
| `src/Prowlarr.sln` | APP-Q2 | Solution with ~20 projects — single deployable monolith |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, SEC-Q2, SEC-Q3 | ASP.NET Core configuration, Kestrel, auth, CORS, Swagger |
| `src/NzbDrone.Host/Prowlarr.Host.csproj` | APP-Q2 | Host project referencing all modules |
| `src/NzbDrone.Core/Prowlarr.Core.csproj` | INF-Q2, APP-Q1, SEC-Q1, OPS-Q1 | Core project dependencies (Dapper, Npgsql, NLog, Polly, FluentMigrator) |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | APP-Q2, DATA-Q2 | Centralized generic repository pattern with Dapper ORM |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2, SEC-Q2 | SQLite and PostgreSQL connection management |
| `src/NzbDrone.Core/Datastore/PostgresOptions.cs` | INF-Q2, SEC-Q5 | PostgreSQL configuration via environment variables |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2 | Centralized SQL query construction |
| `src/NzbDrone.Core/Datastore/WhereBuilder.cs` | DATA-Q2, DATA-Q4 | Query builder — standard SQL, no proprietary constructs |
| `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` | DATA-Q2 | SQLite-specific query dialect handling |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | DATA-Q2 | PostgreSQL-specific query dialect handling |
| `src/NzbDrone.Core/Datastore/TableMapping.cs` | DATA-Q2 | Centralized entity-to-table mapping |
| `src/NzbDrone.Core/Datastore/Migration/` | INF-Q2, DATA-Q3, DATA-Q4 | 43+ FluentMigrator migrations — schema managed in code, no stored procedures |
| `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` | DATA-Q3 | Engine version check at startup |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` | INF-Q3, APP-Q4 | In-process command queue with priority and status tracking |
| `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` | INF-Q3, APP-Q4 | Background command execution |
| `src/NzbDrone.Core/Messaging/Commands/CommandStatus.cs` | APP-Q4 | Job status enum (Queued, Started, Completed, Failed) |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs` | APP-Q4 | Command queue management |
| `src/NzbDrone.Core/Messaging/Events/` | INF-Q4, APP-Q3 | Internal event aggregator for in-process pub/sub |
| `src/NzbDrone.Core/Jobs/Scheduler.cs` | INF-Q3 | Periodic task scheduler |
| `src/NzbDrone.Core/Jobs/TaskManager.cs` | INF-Q3 | Scheduled task management |
| `src/NzbDrone.SignalR/` | INF-Q4, APP-Q3 | Real-time UI communication via SignalR |
| `src/NzbDrone.Core/Applications/` | APP-Q3, APP-Q6 | Synchronous HTTP sync to downstream *arr applications |
| `src/NzbDrone.Core/Indexers/` | APP-Q6, DATA-Q1 | Indexer definitions and HTTP-based indexer communication |
| `src/NzbDrone.Core/IndexerSearch/` | APP-Q4 | Search service — potentially long-running multi-site queries |
| `src/NzbDrone.Core/IndexerStats/` | OPS-Q3 | Internal indexer statistics (not published externally) |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Application-level local backup functionality |
| `src/NzbDrone.Core/Backup/MakeDatabaseBackup.cs` | INF-Q8 | Database backup creation |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q4, OPS-Q8 | Internal health checks surfaced through UI only |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | OPS-Q1 | Sentry error tracking configuration |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | SEC-Q1 | NLog database logging target |
| `src/NzbDrone.Core/Authentication/UserService.cs` | SEC-Q4 | Self-managed user authentication |
| `src/NzbDrone.Core/Authentication/UserRepository.cs` | SEC-Q4 | Internal user database |
| `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key authentication handler |
| `src/Prowlarr.Http/Authentication/AuthenticationService.cs` | SEC-Q4 | Forms-based authentication |
| `src/Prowlarr.Api.V1/openapi.json` | APP-Q5, SEC-Q3 | OpenAPI 3.0.4 spec with /api/v1/ versioning and API key security |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test suite |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | UI automation test suite |
| `src/NzbDrone.Update/` | SEC-Q6, OPS-Q5 | Self-update mechanism |
| `distribution/` | INF-Q1, OPS-Q5 | Platform-specific installer and distribution files |
| `README.md` | Quick Agent Wins | Comprehensive project documentation |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
| `SECURITY.md` | OPS-Q7 | Vulnerability reporting (not incident response) |
