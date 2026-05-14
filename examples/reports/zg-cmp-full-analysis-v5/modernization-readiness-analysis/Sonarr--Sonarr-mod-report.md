# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | Sonarr |
| **Date** | 2025-07-14 |
| **TD Version** | N/A (version not available — `atx custom def get -n modernization-readiness-analysis` not resolvable at analysis time) |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | TV-series PVR for usenet and BitTorrent users (*arr suite). |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **1.96 / 4.0** |

**Archetype Justification**: Sonarr uses SQLite/PostgreSQL for persistent series, episode, and history data with full CRUD operations (POST/PUT/DELETE on series, episodes, download clients, etc.). It has a comprehensive REST API surface but is a self-contained application — not an orchestrator calling 3+ downstream services and not an event-processor. Classified as `stateful-crud`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.50 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.00 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.33 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.96 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | All compute is self-hosted — no managed container orchestration or serverless. No IaC defines any compute resources. | Blocks containerization, auto-scaling, and HA. Every infrastructure operation is manual. |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC — no Terraform, CloudFormation, CDK, Helm, or Kustomize. All infrastructure is ClickOps or self-managed. | Prevents reproducible deployments, disaster recovery, and environment consistency. |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or cloud-native audit logging. Application uses NLog/Sentry for app-level logging only. | No compliance-grade audit trail for infrastructure or API actions. |
| 4 | OPS-Q2: SLO Definitions | 1 | No SLO definitions, error budgets, or formal service level targets found. | Cannot measure whether the system meets user expectations. Blocks data-driven modernization prioritization. |
| 5 | INF-Q5: Network Security | 1 | No VPC, security groups, NACLs, or network segmentation defined. Application exposes API directly on configured port. | Services are exposed without network isolation. No blast-radius containment. |

---

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 4). OpenAPI specs are published for both V3 (`src/Sonarr.Api.V3/openapi.json`) and V5 (`src/Sonarr.Api.V5/openapi.json`), with structured JSON responses across all endpoints.
- **What it enables:** An agent that discovers Sonarr's API endpoints as tools — querying series, triggering searches, managing download clients, and interacting with the queue programmatically via natural language.
- **Additional steps:** OpenAPI specs are already comprehensive. An API Gateway (prefer: api-gateway) fronting Sonarr would add throttling and auth for agent access.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions workflows (`.github/workflows/build_v5.yml`, `.github/workflows/deploy.yml`) provide build, test, and deploy automation.
- **What it enables:** An agent that triggers builds, monitors CI status, and manages releases via the GitHub Actions API. Can check build status, rerun failed jobs, and coordinate deployment timing.
- **Additional steps:** GitHub Actions API access is already available. Agent would need GitHub token with appropriate permissions.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CLA.md`, and wiki links are present. The API docs workflow (`.github/workflows/api_docs.yml`) maintains up-to-date API documentation.
- **What it enables:** A knowledge agent (prefer: bedrock) that indexes Sonarr's documentation, wiki content, and API specs to answer developer and user questions about configuration, troubleshooting, and API usage.
- **Additional steps:** Index the OpenAPI specs and README content into a vector store. External wiki content (wiki.servarr.com) would need to be scraped or mirrored for comprehensive coverage.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith) + INF-Q1=1 (no managed compute) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (no managed compute), no Kubernetes/deployment manifests. Dockerfile exists for legacy Mono build only. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures). Sonarr already uses open-source databases (SQLite, PostgreSQL). |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed embedded SQLite / self-managed PostgreSQL) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads, no streaming/ETL/analytics artifacts. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (zero IaC). OPS-Q5=1 (direct-to-production). OPS-Q6=3 (integration tests exist). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("TV-series PVR for usenet and BitTorrent users"). |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:** Sonarr is a tightly-coupled monolith (APP-Q2=2) deployed as a single self-hosted process with no managed compute (INF-Q1=1). All modules share a single SQLite/PostgreSQL database. Internal communication uses an in-process EventAggregator and CommandQueue — no external messaging or service boundaries.

**Compute Model Gaps:** No IaC defines any compute resources. The application runs as a standalone binary on user-managed servers (Windows, Linux, macOS). There is no container orchestration, no serverless deployment, and no managed compute platform.

**Communication Pattern Gaps:** All inter-module communication is in-process (synchronous method calls and EventAggregator). There are no cross-service async patterns because no service boundaries exist. Long-running operations (RSS sync, download monitoring, media file processing) are handled by an internal command queue (APP-Q4=3), which is a strength for future decomposition.

**Recommended Decomposition Approach:** See the Decomposition Strategy section below. The Strangler Fig pattern is recommended — start by containerizing the monolith, then incrementally extract bounded contexts (e.g., Download Management, Indexer/Search, Media Management, Notification) into independent services behind API Gateway (prefer: api-gateway).

**Representative AWS Services:** EKS (prefer), API Gateway (prefer), EventBridge (prefer), DynamoDB (prefer) for metadata, Aurora (prefer) for relational data, Lambda for event-driven notification dispatching.

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing (via EventBridge), Hexagonal Architecture.

**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:** Sonarr builds for multiple runtime platforms (linux-x64, linux-arm64, win-x64, osx-arm64, etc.) as self-contained .NET executables. The existing Dockerfile (`distribution/docker-build/Dockerfile`) is a legacy Mono-based Debian packaging build — not a runtime container image. No Kubernetes manifests, Helm charts, or container orchestration configuration exist.

**Container Readiness Indicators:** The application is already cross-platform (.NET 10.0), supports Linux runtimes, and externalizes configuration via XML config files and environment variables (e.g., `Sonarr__Postgres__Host`, `Sonarr__Postgres__Port`). Port binding is configurable. These are positive signals for containerization.

**Recommended Container Orchestration:** EKS (prefer) with Fargate for operational simplicity. Create a modern multi-stage Dockerfile using `mcr.microsoft.com/dotnet/aspnet:10.0` as the runtime base. Package as a Helm chart for deployment.

**Representative AWS Services:** EKS (prefer), ECR for container registry, Fargate for serverless containers.

**Migration Approach:** Lift-and-containerize first — create a production Dockerfile, push to ECR, deploy to EKS. Then refactor-then-containerize as services are extracted per the Cloud Native pathway.

**AWS Guidance:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** Sonarr uses embedded SQLite as the default database (`SourceGear.sqlite3` 3.50.4.5, `System.Data.SQLite` 2.0.2 in `src/NzbDrone.Common/Sonarr.Common.csproj`) and optionally supports self-managed PostgreSQL (`Npgsql` 10.0.2 in `src/NzbDrone.Core/Sonarr.Core.csproj`). Both are self-managed — no RDS, Aurora, or DynamoDB. The connection string factory (`src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`) switches between SQLite and PostgreSQL based on configuration.

**Engine Versions:** SQLite 3.50.4.5 (current, no EOL concern). PostgreSQL support via Npgsql 10.0.2 — supports PostgreSQL 16, 17, 18 (tested in CI per `.github/workflows/build_v5.yml`).

**Data Access Patterns:** Centralized via `BasicRepository<TModel>` pattern using Dapper ORM (`src/NzbDrone.Core/Datastore/BasicRepository.cs`). All data access goes through the repository layer. Database abstraction supports SQLite and PostgreSQL with separate `WhereBuilderSqlite.cs` and `WhereBuilderPostgres.cs`.

**Recommended Managed Database Targets:** Aurora PostgreSQL (prefer: aurora) for the main database. The existing PostgreSQL support means migration requires only connection string changes and minor tuning. DynamoDB (prefer: dynamodb) could be evaluated for specific access patterns (e.g., episode metadata, configuration storage) but would require schema redesign.

**Representative AWS Services:** Aurora PostgreSQL (prefer), RDS PostgreSQL, DynamoDB (prefer) for specific patterns.
**Migration Tools:** AWS DMS for initial data migration, native `pg_dump`/`pg_restore` for PostgreSQL-to-Aurora.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** The CI/CD pipeline (`.github/workflows/build_v5.yml`) is well-structured with build, unit test, PostgreSQL test matrix, and integration test stages. However, there is **zero Infrastructure as Code** (INF-Q10=1) — all infrastructure is manually provisioned. Deployments are direct-to-production (OPS-Q5=1) with no canary or blue/green strategy. The deploy workflow (`.github/workflows/deploy.yml`) packages binaries and publishes to GitHub Releases + a custom `services.sonarr.tv` update API — no staged rollout.

**IaC Coverage:** No Terraform, CloudFormation, CDK, Helm, or Kustomize files found. All cloud infrastructure would need to be defined from scratch.

**Deployment Strategy Gaps:** No traffic shifting, canary, or blue/green deployment. The application uses a self-update mechanism (`src/NzbDrone.Core/Update/`) rather than infrastructure-managed deployment.

**Recommended DevOps Toolchain:** Terraform or CDK for IaC. CodePipeline or GitHub Actions (existing) for CI/CD. EKS (prefer) with Helm charts for deployment. ArgoCD or Flux for GitOps-based deployment.

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation/CDK, X-Ray, CloudWatch.

**AWS Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

## Decomposition Strategy

Since APP-Q2 = 2 (monolith with identifiable modules but shared database), a decomposition strategy is warranted.

### Recommended Approach: Strangler Fig (Parallel Track)

Sonarr has identifiable module boundaries in `src/NzbDrone.Core/` (Download, Indexers, MediaFiles, Notifications, Queue, Tv, etc.) that share a single database. The Strangler Fig approach is recommended:

1. **Phase 1 — Containerize as-is** (2–4 weeks): Create a production Dockerfile, deploy to EKS (prefer). This gives immediate operational benefits without architectural change.
2. **Phase 2 — Extract high-value bounded contexts** (6–12 months): Start with Notifications (low coupling, event-driven), then Download Management (clear API surface), then Indexer/Search.
3. **Phase 3 — Data separation** (ongoing): Migrate extracted services to own databases (Aurora PostgreSQL prefer), using the existing dual-database abstraction (`WhereBuilderSqlite.cs` / `WhereBuilderPostgres.cs`) as a foundation.

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2=2 — identifiable modules with coupling. Team can sustain parallel development. | Medium to High (6–18 months) | ✅ **Recommended.** Lowest risk, incremental value delivery. |
| **Conditional / Adaptive** | Limited team capacity. Need quick wins. | Low to Medium (containerize in 2–4 weeks, selective extraction 3–12 months) | ✅ **Recommended when capacity is constrained.** |
| **Big-Bang Rewrite** | Only if monolith is truly unmaintainable. | Very High (12–24+ months) | ⚠️ **Not recommended.** Sonarr's module structure supports incremental extraction. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from monolith's data model | Every extraction — translate between monolith and service models |
| **Saga Pattern** | Manage distributed transactions (e.g., grab → download → import) | When extracting Download Management and Media Import modules |
| **Event Sourcing** | Capture state changes as events for audit and integration | Episode state transitions, download lifecycle events. Use EventBridge (prefer). |
| **Hexagonal Architecture** | Clear business logic boundaries in new services | Every new service — ensures testability and infrastructure portability |

### Effort Estimation Factors

| Factor | Signal | Analysis |
|--------|--------|------------|
| Module boundaries | Identifiable subdirectories in `src/NzbDrone.Core/` (Download/, Indexers/, MediaFiles/, Notifications/) | **Medium effort** — boundaries exist but coupling through shared DB |
| Data coupling | Single shared database via `BasicRepository<TModel>` | **High effort** — all modules share one DB; data separation required |
| Stored procedures | None (DATA-Q4=4) | **Low effort** — no database-coupled business logic to extract |
| Communication patterns | In-process EventAggregator + CommandQueue | **Medium effort** — good patterns but need externalization (EventBridge prefer) |
| CI/CD maturity | GitHub Actions pipeline with build/test/integration | **Low effort** — pipeline exists, needs extension for multi-service |
| Test coverage | Integration tests exist for critical workflows | **Low effort** — regression safety net in place |

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defines any compute resources. The application is distributed as self-contained .NET 10.0 binaries for multiple platforms (linux-x64, win-x64, osx-arm64, etc.) and runs as a self-hosted process. The Dockerfile at `distribution/docker-build/Dockerfile` is a legacy Mono-based Debian packaging build, not a runtime container. No ECS, EKS, Lambda, Fargate, or EC2 definitions found. |
| **Gap** | All compute is entirely self-managed. No managed container orchestration or serverless compute. |
| **Recommendation** | Containerize the application using a modern multi-stage Dockerfile targeting `mcr.microsoft.com/dotnet/aspnet:10.0`. Deploy to EKS (prefer) with Fargate. Define compute resources in IaC (Terraform or CDK). |
| **Evidence** | `distribution/docker-build/Dockerfile`, `.github/workflows/build_v5.yml` (multi-platform build matrix), `global.json` (SDK 10.0.201) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Sonarr uses embedded SQLite as the default database (`SourceGear.sqlite3` 3.50.4.5, `System.Data.SQLite` 2.0.2 in `src/NzbDrone.Common/Sonarr.Common.csproj`) and supports self-managed PostgreSQL via `Npgsql` 10.0.2 (`src/NzbDrone.Core/Sonarr.Core.csproj`). Connection string factory (`src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`) switches between SQLite and PostgreSQL based on environment configuration. No managed database services (RDS, Aurora, DynamoDB) are defined. |
| **Gap** | All databases are self-managed — embedded SQLite on local disk or user-provisioned PostgreSQL. No automated failover, managed backups, or scaling. |
| **Recommendation** | Migrate to Aurora PostgreSQL (prefer: aurora) for the main and log databases. The existing PostgreSQL support means migration requires connection string changes and minor tuning. Use DynamoDB (prefer) for specific high-throughput access patterns if decomposing the monolith. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (SQLite packages), `src/NzbDrone.Core/Sonarr.Core.csproj` (Npgsql, Dapper), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Sonarr implements a custom in-process command queue and scheduler for multi-step workflows. The `CommandQueue` (`src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`) manages command execution with priority ordering, disk-access exclusion, and exclusive command support. The `Scheduler` (`src/NzbDrone.Core/Jobs/Scheduler.cs`) fires scheduled tasks via a timer. The `TaskManager` (`src/NzbDrone.Core/Jobs/TaskManager.cs`) defines recurring tasks (RSS sync, download monitoring, health checks, backups, housekeeping). These are hardcoded state machines in application code with some structure (priority, exclusion rules). |
| **Gap** | Multi-step workflows (episode search → grab → download monitor → import → rename → notify) are entirely coded as application logic. No dedicated orchestration service (Step Functions, Temporal). Error handling and retry logic is embedded in each command executor. |
| **Recommendation** | For cloud deployment, extract critical multi-step workflows into AWS Step Functions. The existing command/event pattern maps well to Step Functions states. Start with the download lifecycle (grab → monitor → import → notify) which is the most complex workflow. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Sonarr uses an in-process EventAggregator (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) for internal event-driven communication with both synchronous (`IHandle<T>`) and asynchronous (`IHandleAsync<T>`) handlers. SignalR (`@microsoft/signalr` 10.0.0 in `package.json`, `src/NzbDrone.SignalR/`) provides real-time push updates to the frontend. The internal command queue acts as a message broker within the process. However, there is no external messaging infrastructure — no SQS, SNS, EventBridge, Kafka, or RabbitMQ. |
| **Gap** | For a stateful-crud application, cross-service state change propagation should use managed messaging. Currently all messaging is in-process — this works for a monolith but blocks decomposition. When modules are extracted into services, the EventAggregator cannot cross process boundaries. |
| **Recommendation** | When decomposing into services, externalize the EventAggregator pattern to EventBridge (prefer). Map existing event types (e.g., `EpisodeGrabbedEvent`, `DownloadCompletedEvent`, `SeriesUpdatedEvent`) to EventBridge event patterns. Use SQS for command queue externalization. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.SignalR/Sonarr.SignalR.csproj`, `package.json` (SignalR client), `src/NzbDrone.Core/Download/DownloadCompletedEvent.cs`, `src/NzbDrone.Core/Download/EpisodeGrabbedEvent.cs` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation definitions found. No IaC exists. The application binds to a configurable address and port (default `*:8989` per `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`) with optional SSL. Network security is entirely delegated to the host environment. |
| **Gap** | Services are deployed without any cloud network isolation. No private subnets, no security group rules, no VPC endpoints. |
| **Recommendation** | When deploying to AWS, define VPC with private subnets for compute and database resources. Place Sonarr behind API Gateway (prefer) or ALB in a public subnet with security groups restricting ingress. Use VPC endpoints for S3 and other AWS service access. |
| **Evidence** | `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (BindAddress, Port configuration), absence of any `.tf`, `.cfn.yaml`, or CDK files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync defined. The application directly serves HTTP requests via Kestrel (ASP.NET Core built-in server). API endpoints are at `/api/v3/` and `/api/v5/` paths. No throttling, request validation, or gateway-level auth is applied at the infrastructure level. |
| **Gap** | API is exposed directly with no managed entry point. No throttling, no WAF, no request validation at the infrastructure layer. |
| **Recommendation** | Deploy API Gateway (prefer: api-gateway) in front of the application. Configure throttling, request validation, and API key plans. API Gateway can also serve as a service catalog for the V3 and V5 APIs using the existing OpenAPI specs. |
| **Evidence** | `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `src/Sonarr.Http/VersionedApiControllerAttribute.cs`, absence of any gateway/ALB IaC |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No ASGs, ECS service scaling, Lambda concurrency limits, or DynamoDB auto-scaling. The application runs as a single instance with statically provisioned resources. |
| **Gap** | All capacity is statically provisioned. No ability to respond to traffic spikes or scale down during low demand. |
| **Recommendation** | When deploying to EKS (prefer), configure Horizontal Pod Autoscaler (HPA) based on CPU/memory and custom metrics (e.g., queue depth, active downloads). For Aurora (prefer), enable auto-scaling read replicas. |
| **Evidence** | Absence of any auto-scaling configuration in the repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Sonarr implements application-level backup via `BackupService` (`src/NzbDrone.Core/Backup/BackupService.cs`). It creates ZIP archives containing the SQLite database and config file, with configurable retention (`BackupRetention`). Scheduled backups run automatically via the `TaskManager`. The `Restore` method supports restoring from backup ZIPs. However, this is application-managed — no infrastructure-level backup (AWS Backup, RDS automated backups, PITR). Only SQLite databases are backed up; PostgreSQL backups are not managed by the application. |
| **Gap** | Backup exists but is application-managed. No PITR, no cross-region replication, no infrastructure-level backup plans. PostgreSQL users have no application-managed backup. Restore procedures are not documented as infrastructure runbooks. |
| **Recommendation** | When migrating to Aurora (prefer), leverage automated backups with PITR and cross-region replication. Define `aws_backup_plan` resources in IaC for all data stores. Document and test restore procedures. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` (BackupCommand scheduling) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. `has_deployed_workload=false` — no IaC defines deployable compute, and while a Dockerfile exists, no deployment manifests (Helm, Kubernetes, CloudFormation) reference it. The application is a self-hosted desktop/server process that runs as a single instance by design. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of IaC compute resources, `distribution/docker-build/Dockerfile` (legacy build-only) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC. No Terraform (`.tf`), CloudFormation (`.cfn.yaml`), CDK (`cdk.json`), Helm (`Chart.yaml`), or Kustomize (`kustomization.yaml`) files found anywhere in the repository. All infrastructure is created manually or managed outside the repository. |
| **Gap** | No infrastructure defined in code. All infrastructure changes are manual, error-prone, and non-reproducible. No environment consistency or disaster recovery automation. |
| **Recommendation** | Adopt Terraform or CDK for all infrastructure. Start by defining the target deployment infrastructure: VPC, EKS cluster (prefer), Aurora PostgreSQL (prefer), API Gateway (prefer), ECR, and CloudWatch alarms. Commit IaC to the repository alongside application code. |
| **Evidence** | Repository-wide scan found no IaC files of any type |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-structured CI/CD pipeline in `.github/workflows/build_v5.yml` with: multi-platform backend build (10 runtime targets), frontend build with lint/stylelint, unit tests across 3 OS (Ubuntu, macOS, Windows), PostgreSQL test matrix (versions 16, 17, 18), integration tests across 3 OS, and automated deployment via `.github/workflows/deploy.yml`. Deploy workflow packages artifacts, creates GitHub Releases, and publishes to `services.sonarr.tv` update API. Dependabot configured for devcontainer updates (`.github/dependabot.yml`). |
| **Gap** | CI/CD covers application code well, but there is no IaC to deploy or test. No infrastructure deployment pipeline. Dependabot only covers devcontainers, not NuGet or npm dependencies. No security scanning in the pipeline (see SEC-Q7). |
| **Recommendation** | Extend the CI/CD pipeline to include IaC validation (`terraform plan`, CDK synth). Add NuGet and npm dependency updates to Dependabot configuration. Integrate security scanning (see SEC-Q7 recommendation). |
| **Evidence** | `.github/workflows/build_v5.yml`, `.github/workflows/deploy.yml`, `.github/dependabot.yml`, `.github/actions/build/action.yml`, `.github/actions/test/action.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Backend: C# targeting .NET 10.0 (`net10.0` in all `.csproj` files, SDK 10.0.201 in `global.json`). Frontend: TypeScript 5.7.2 with React 18.3.1 (`package.json`). Modern ASP.NET Core framework (Microsoft.AspNetCore packages v10.0.5). Modern NuGet packages: Dapper 2.1.72, Npgsql 10.0.2, Polly 8.6.6, FluentMigrator 8.0.1, Newtonsoft.Json 13.0.4, Sentry 5.16.3. Node.js 20.11.1 (via Volta). |
| **Gap** | None. Language, framework, and SDK are all current-generation. |
| **Recommendation** | No action needed. Continue tracking .NET LTS releases and upgrading NuGet packages. |
| **Evidence** | `global.json`, `src/Directory.Build.props`, `src/NzbDrone.Core/Sonarr.Core.csproj`, `src/NzbDrone.Host/Sonarr.Host.csproj`, `package.json` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Sonarr is a single deployable unit (`src/Sonarr.sln`) producing one executable. The `src/NzbDrone.Core/` directory contains identifiable modules (Download, Indexers, MediaFiles, Notifications, Queue, Tv, ImportLists, HealthCheck, etc.) organized as subdirectories. However, all modules share a single database (SQLite or PostgreSQL), accessed through a common `BasicRepository<TModel>` pattern. Module boundaries are recognizable but there is direct cross-module data access through shared database tables and the in-process EventAggregator. |
| **Gap** | Monolith with identifiable modules but shared database schemas. Direct cross-module data access through the shared repository layer. No module independence — all modules must be deployed together. |
| **Recommendation** | Begin decomposition using the Strangler Fig pattern (see Decomposition Strategy section). First containerize the monolith, then incrementally extract bounded contexts starting with Notifications (low coupling, event-driven) and Download Management (clear API surface). |
| **Evidence** | `src/Sonarr.sln`, `src/NzbDrone.Core/` (module subdirectories), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (shared data access), `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` (in-process events) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | As a stateful-crud monolith, inter-module communication is in-process. The EventAggregator (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) provides both synchronous (`IHandle<T>`) and asynchronous (`IHandleAsync<T>`) event handling. Download events, series updates, and notification triggers use async handlers. The command queue (`src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`) processes commands asynchronously with priority ordering. SignalR provides real-time async push to the frontend. This is a functional mix of sync and async patterns within a monolith. |
| **Gap** | Async patterns exist for key internal workflows (events, commands). However, all communication is in-process — there is no external async infrastructure (SQS, EventBridge) for cross-service flows that would be needed when decomposing the monolith. |
| **Recommendation** | During decomposition, externalize the EventAggregator to EventBridge (prefer) and the CommandQueue to SQS. The existing async handler patterns (`IHandleAsync<T>`) map directly to event-driven consumers. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.SignalR/` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Long-running operations are handled asynchronously through the internal command queue system. The `CommandQueue` supports priority ordering, long-running command awareness (`IsLongRunning`), and exclusive execution (`IsExclusive`). Download monitoring (`RefreshMonitoredDownloadsCommand` — runs every 1 minute), RSS sync (`RssSyncCommand`), series refresh (`RefreshSeriesCommand` — every 12 hours), and health checks (`CheckHealthCommand` — every 6 hours) are all executed asynchronously via scheduled tasks. The API can query command status via the Commands endpoint. |
| **Gap** | Most long-running operations are handled asynchronously with status tracking. However, some operations (e.g., media file import, episode rename) may still block within a command executor without checkpointing. |
| **Recommendation** | When migrating to cloud, replace the internal CommandQueue with Step Functions for long-running workflows. The existing `IsLongRunning` and `IsExclusive` flags can map to Step Functions execution configuration. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` (IsLongRunning, IsExclusive), `src/NzbDrone.Core/Jobs/TaskManager.cs` (scheduled tasks), `src/NzbDrone.Core/Messaging/Commands/CommandStatus.cs` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Consistent URL-path versioning strategy with V3 (`src/Sonarr.Api.V3/`) and V5 (`src/Sonarr.Api.V5/`) API versions. Both have published OpenAPI specifications (`openapi.json`). The `VersionedApiControllerAttribute.cs` in `src/Sonarr.Http/` enforces versioned routing at `/api/v3/` and `/api/v5/`. The API docs workflow (`.github/workflows/api_docs.yml`) automatically generates and maintains OpenAPI documentation. |
| **Gap** | None. Versioning strategy is consistent, applied to all endpoints, and backed by OpenAPI specs. |
| **Recommendation** | No action needed. Continue the versioned API approach. When deploying behind API Gateway (prefer), use the OpenAPI specs to configure API Gateway resources. |
| **Evidence** | `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `src/Sonarr.Http/VersionedApiControllerAttribute.cs`, `.github/workflows/api_docs.yml` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Sonarr is a single monolith — there is no inter-service communication requiring service discovery. External services (indexers, download clients, notification targets) are configured via user-provided URLs stored in the database. These are essentially hard-coded endpoints per configuration. No AWS Service Discovery, Consul, or Istio is used. Environment variables are used for some configuration (e.g., PostgreSQL connection via `Sonarr__Postgres__Host`). |
| **Gap** | External service endpoints (indexers, download clients) are configured as static URLs in the database. No dynamic service discovery for external integrations. When decomposing the monolith, extracted services will need dynamic discovery. |
| **Recommendation** | When decomposing into microservices on EKS (prefer), use Kubernetes service discovery for internal service communication. For external integrations (indexers, download clients), consider an API Gateway (prefer) or service mesh for dynamic routing and health-based endpoint management. |
| **Evidence** | `src/NzbDrone.Core/Indexers/` (static URLs), `src/NzbDrone.Core/Download/Clients/` (static URLs), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (env var configuration) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Sonarr handles media cover images (`src/NzbDrone.Core/MediaCover/`) and media file metadata (`src/NzbDrone.Core/MediaFiles/`) entirely through the local filesystem. Cover images are downloaded and cached locally. Media files are managed on local or NFS-mounted directories configured as root folders. No S3, managed object storage, or document parsing capabilities (Textract, Tika) are used. |
| **Gap** | All unstructured data (cover images, media file metadata, logs) stored on local file systems. No cloud-native object storage or parsing pipeline. |
| **Recommendation** | Migrate media covers and metadata cache to S3. Use S3 for log archival. For media files, consider S3 with Amazon S3 File Gateway for NFS compatibility, preserving the application's filesystem-based access pattern without code changes. |
| **Evidence** | `src/NzbDrone.Core/MediaCover/MediaCoverService.cs`, `src/NzbDrone.Core/MediaFiles/DiskScanService.cs`, `src/NzbDrone.Core/RootFolders/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Sonarr has a well-structured centralized data access layer through `BasicRepository<TModel>` (`src/NzbDrone.Core/Datastore/BasicRepository.cs`) using Dapper as the micro-ORM. All database operations go through this repository pattern. The `TableMapping` and `SqlBuilder` classes provide a unified query abstraction. Database-specific query builders (`WhereBuilderSqlite.cs`, `WhereBuilderPostgres.cs`) handle dialect differences. However, some auxiliary code paths use direct SQL queries via Dapper for complex queries or bulk operations. |
| **Gap** | Mostly centralized with some direct SQL access in auxiliary code paths (migration files, specialized queries). The dual-database abstraction (SQLite + PostgreSQL) adds complexity to the data access layer. |
| **Recommendation** | When migrating to Aurora PostgreSQL (prefer), consolidate to a single database dialect. Remove the SQLite abstraction layer to simplify the codebase. The existing repository pattern is well-suited for cloud deployment. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are explicitly pinned in csproj files: SQLite via `SourceGear.sqlite3` 3.50.4.5 and `System.Data.SQLite` 2.0.2 (`src/NzbDrone.Common/Sonarr.Common.csproj`), PostgreSQL via `Npgsql` 10.0.2 (`src/NzbDrone.Core/Sonarr.Core.csproj`). CI tests against PostgreSQL 16, 17, and 18 (`.github/workflows/build_v5.yml`). SQLite 3.50.x is current. PostgreSQL 16 has EOL in November 2028. No engines at or past EOL. However, no documented version-update procedure exists. |
| **Gap** | Versions are pinned and tested but no documented version-update procedure covering downtime windows, rollback, or risk acknowledgment. PostgreSQL 16 (the oldest tested version) is still well within support. |
| **Recommendation** | Document a database engine version-update procedure. Continue the PostgreSQL version test matrix in CI. When migrating to Aurora (prefer), Aurora manages engine version lifecycle automatically. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (sqlite3 3.50.4.5), `src/NzbDrone.Core/Sonarr.Core.csproj` (Npgsql 10.0.2), `.github/workflows/build_v5.yml` (postgres-version: [16, 17, 18]) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found. All business logic is in the C# application layer. Database migrations use FluentMigrator (`FluentMigrator.Runner.Core` 8.0.1 in `src/NzbDrone.Core/Sonarr.Core.csproj`) with C# migration classes (`src/NzbDrone.Core/Datastore/Migration/`). SQL queries are generated by Dapper and the `SqlBuilder` class. No raw SQL files found. No T-SQL or PL/SQL. The 230+ migration files all use the FluentMigrator DSL (`Create.TableForModel()`, `Alter.Table()`) — no raw SQL procedure definitions. |
| **Gap** | None. All business logic is in the application layer. Database is used as a data store only. |
| **Recommendation** | No action needed. This is an ideal state for database migration — no stored procedure extraction required. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (230+ FluentMigrator C# migrations), `src/NzbDrone.Core/Sonarr.Core.csproj` (FluentMigrator packages), grep for stored procedure patterns returned no results |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud-native audit logging configured. The application uses NLog 5.5.1 (`src/NzbDrone.Common/Sonarr.Common.csproj`) for structured application logging with database logging (`src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`), syslog support (`NLog.Targets.Syslog`), and CLEF JSON format (`NLog.Layouts.ClefJsonLayout`). Sentry 5.16.3 is used for error tracking (`src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`). However, these are application-level logging — no infrastructure audit trail, no immutable log storage, no CloudTrail. |
| **Gap** | No compliance-grade audit logging. Application logs are stored locally and in the application database. No immutable log storage. No infrastructure-level audit trail for API access or configuration changes. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Ship application logs to CloudWatch Logs for centralized analysis. Configure CloudWatch Logs retention policies. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (NLog, Sentry), `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed storage defined in IaC. The application uses local embedded SQLite and user-managed PostgreSQL, neither of which is provisioned through cloud infrastructure. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of any IaC-defined data stores (no `aws_rds_*`, `aws_s3_bucket`, `aws_ebs_*`) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Sonarr uses API key authentication via `ApiKeyAuthenticationHandler` (`src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`). The API key is checked from the `X-Api-Key` header, `apikey` query parameter, or `Authorization: Bearer` header. The key is a static GUID generated on first run and stored in `Config.xml`. Forms-based authentication is available for the UI (`AuthenticationType.Forms` in `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`). There is no OAuth2, JWT, or token-based auth with expiration. The API key is a static credential without rotation. |
| **Gap** | API key or static credential authentication without token-based auth. No OAuth2/JWT. No key rotation. API key is a long-lived static secret. |
| **Recommendation** | When deploying behind API Gateway (prefer), implement Cognito user pools or OAuth2 for per-request token-based authentication. Use API Gateway API keys with usage plans for programmatic access. Keep the existing API key as a migration path but add JWT validation for new integrations. |
| **Evidence** | `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey property), `src/NzbDrone.Core/Authentication/AuthenticationType.cs` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Sonarr manages its own authentication entirely. User accounts are stored in the local database via `UserRepository` (`src/NzbDrone.Core/Authentication/UserRepository.cs`). Password hashing uses `Microsoft.AspNetCore.Cryptography.KeyDerivation` (`src/NzbDrone.Core/Sonarr.Core.csproj`). Authentication modes are `None`, `Forms`, or `Basic` (deprecated). No external IdP integration — no Cognito, Okta, OIDC, or SAML configuration found. No SSO. |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. Users are stored in the application database. No SSO, no federation, no centralized identity management. |
| **Recommendation** | When deploying to AWS, integrate with Cognito user pools for centralized identity. Cognito provides OIDC/SAML federation, MFA, and SSO — all missing from the current implementation. The Forms auth handler can be adapted to validate Cognito JWT tokens. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Authentication/AuthenticationType.cs`, `src/Sonarr.Http/Authentication/AuthenticationService.cs` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials found hardcoded in source code. The API key is dynamically generated and stored in `Config.xml` (not version-controlled). PostgreSQL credentials are configured via environment variables (`Sonarr__Postgres__User`, `Sonarr__Postgres__Password` in `.github/actions/test/action.yml`) or `Config.xml` properties. CI/CD uses GitHub Secrets (`secrets.SERVICES_API_KEY`, `secrets.DISCORD_WEBHOOK_URL`). However, there is no Secrets Manager or Vault integration. Production credentials in environment variables without encryption. No rotation configured. |
| **Gap** | No plaintext credentials in source, but production credentials are kept in environment variables or XML config files without encryption or rotation. No Secrets Manager or Vault integration. |
| **Recommendation** | Integrate AWS Secrets Manager for all production credentials (PostgreSQL password, API keys, notification service tokens). Configure automatic rotation for database credentials. Reference secrets via the Secrets Manager SDK or EKS (prefer) CSI driver instead of environment variables. |
| **Evidence** | `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgresPassword, ApiKey), `.github/actions/test/action.yml` (env var credentials), `.github/workflows/deploy.yml` (GitHub Secrets) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No evidence of compute hardening or vulnerability scanning. The Dockerfile at `distribution/docker-build/Dockerfile` uses `ubuntu:focal` base (Ubuntu 20.04 — EOL April 2025) with `apt-get upgrade` as the only patching mechanism. No SSM Patch Manager, no AWS Inspector, no Snyk, no hardened base images (CIS, Bottlerocket). No container image scanning configured. |
| **Gap** | No patching strategy. Dockerfile base image is EOL. No vulnerability scanning. No hardened images. |
| **Recommendation** | Create a modern multi-stage Dockerfile using `mcr.microsoft.com/dotnet/aspnet:10.0` (maintained, patched base). Enable ECR image scanning. When deploying to EKS (prefer), use Bottlerocket AMIs for node groups. Integrate Snyk or Trivy container scanning into the CI pipeline. |
| **Evidence** | `distribution/docker-build/Dockerfile` (ubuntu:focal base), absence of any vulnerability scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools found in the CI/CD pipeline. The build workflows (`.github/workflows/build_v5.yml`) contain build, lint, and test stages but no security scanning stages. Dependabot (`.github/dependabot.yml`) is configured only for devcontainers — not for NuGet (`nuget`) or npm (`npm`) dependency updates. No SonarQube, Semgrep, CodeGuru Reviewer, Snyk, or container scanning configured. StyleCop analyzers in `src/Directory.Build.props` are code style tools, not security scanners. |
| **Gap** | No security scanning tools configured. No SAST. No dependency vulnerability scanning for NuGet or npm packages. No container scanning. Pipeline has no security validation step. |
| **Recommendation** | Add Dependabot configuration for `nuget` and `npm` ecosystems. Integrate SAST (Semgrep or CodeGuru Reviewer) into the CI pipeline. Add `dotnet list package --vulnerable` to the build workflow for NuGet vulnerability detection. Enable ECR image scanning for container images. Add a security gate blocking on critical findings. |
| **Evidence** | `.github/workflows/build_v5.yml` (no security stages), `.github/dependabot.yml` (devcontainers only), `src/Directory.Build.props` (StyleCop only — not a security scanner) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry SDK, X-Ray agent, or traceparent header propagation found. Sentry 5.16.3 (`src/NzbDrone.Common/Sonarr.Common.csproj`) provides error tracking and performance monitoring but is not a distributed tracing solution — it does not propagate trace IDs across service boundaries. NLog provides structured logging but no trace correlation. MiniProfiler (`MiniProfiler.AspNetCore` 4.5.4 in `src/NzbDrone.Host/Sonarr.Host.csproj`) provides request-level profiling but no distributed tracing. |
| **Gap** | No distributed tracing. No trace ID propagation. No end-to-end request flow visibility across service boundaries. |
| **Recommendation** | Instrument OpenTelemetry for .NET. The `OpenTelemetry.Instrumentation.AspNetCore` and `OpenTelemetry.Instrumentation.Http` packages provide automatic instrumentation. Export traces to AWS X-Ray or CloudWatch. This is foundational for debugging when the monolith is decomposed. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (Sentry only), `src/NzbDrone.Host/Sonarr.Host.csproj` (MiniProfiler only), grep for OpenTelemetry/X-Ray returned no results |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No error budget tracking. No CloudWatch alarms on latency or availability. The application has a health check system (`src/NzbDrone.Core/HealthCheck/`) that monitors internal component health (disk space, indexer connectivity, download client availability), but these are operational health checks, not SLO definitions with formal targets and error budgets. |
| **Gap** | No formal SLO definitions. No error budget tracking. No measurement of whether the system meets user expectations. The health check system monitors internal components but does not define or track service-level targets. |
| **Recommendation** | Define SLOs for critical user journeys: API response latency (p99 < 500ms), RSS sync success rate (>99%), download monitoring availability (>99.9%). Implement CloudWatch alarms with composite metrics for SLO tracking when deployed to AWS. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational checks, not SLOs), absence of SLO definitions in any config or code |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. No CloudWatch custom metrics. No business event tracking beyond application logging. The application tracks download history, series statistics (`src/NzbDrone.Core/SeriesStats/`), and analytics events (`src/NzbDrone.Core/Analytics/`), but these are internal data — not published as operational metrics for monitoring and alerting. |
| **Gap** | No business metrics published. Only default infrastructure metrics (if any cloud monitoring were configured). No dashboards for downloads-per-hour, search success rate, or import failure rate. |
| **Recommendation** | Publish custom CloudWatch metrics for key business outcomes: episodes grabbed per hour, download completion rate, import success rate, indexer availability. Create CloudWatch dashboards for operational visibility. |
| **Evidence** | `src/NzbDrone.Core/Analytics/`, `src/NzbDrone.Core/SeriesStats/`, absence of any metrics publishing code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms. No PagerDuty/OpsGenie integration. The application's health check system (`src/NzbDrone.Core/HealthCheck/`) provides internal monitoring with in-app notifications, but there is no infrastructure-level alerting or anomaly detection. The notification system (`src/NzbDrone.Core/Notifications/`) can send alerts on specific events (grab, download, health issues) but this is application-level, not operational monitoring. |
| **Gap** | No alerting configured at the infrastructure level. No anomaly detection. No external incident notification system. |
| **Recommendation** | When deploying to AWS, configure CloudWatch alarms for error rates, latency, and resource utilization. Enable CloudWatch anomaly detection for critical paths. Integrate with SNS or EventBridge (prefer) for incident notification routing. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (app-level only), `src/NzbDrone.Core/Notifications/` (app-level event notifications) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment. The deploy workflow (`.github/workflows/deploy.yml`) packages binaries, creates a GitHub Release, and publishes update metadata to `services.sonarr.tv/v1/update`. The application has a self-update mechanism (`src/NzbDrone.Core/Update/`) that downloads and applies updates in-place. No canary, blue/green, or staged rollout. No traffic shifting. No CodeDeploy. No ArgoCD Rollouts. |
| **Gap** | Direct-to-production deployment with no staged rollout. Updates are applied in-place with no rollback mechanism beyond restoring from backup. No ability to test a release with a subset of users before full rollout. |
| **Recommendation** | When deploying to EKS (prefer), implement canary deployments using ArgoCD Rollouts or Helm canary charts. Use API Gateway (prefer) weighted routing for traffic shifting. For the self-hosted distribution, consider implementing a beta channel with percentage-based rollout via the update service. |
| **Evidence** | `.github/workflows/deploy.yml` (direct publish), `src/NzbDrone.Core/Update/` (self-update mechanism) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist in `src/NzbDrone.Integration.Test/` covering critical API workflows: series CRUD, episode management, download client integration, indexer management, history, calendar, queue management, and blocklist operations. Tests are run in the CI pipeline across 3 OS (Ubuntu, macOS, Windows) as a dedicated `integration_test` job in `.github/workflows/build_v5.yml`. The integration tests spin up a live Sonarr instance and test against its API. |
| **Gap** | Integration tests cover primary workflows but some API endpoints may have gaps. No contract testing. No performance testing in the pipeline. |
| **Recommendation** | Add contract tests for the V5 API to ensure backward compatibility. Consider adding load/performance tests for the API. Expand integration test coverage to include PostgreSQL-mode integration tests (currently PostgreSQL testing is limited to unit tests). |
| **Evidence** | `src/NzbDrone.Integration.Test/` (18+ test fixture files), `src/NzbDrone.Integration.Test/ApiTests/` (API-specific tests), `.github/workflows/build_v5.yml` (integration_test job) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns found. No SSM Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. The application has a health check system (`src/NzbDrone.Core/HealthCheck/`) with automatic detection of issues (disk space, indexer availability, download client connectivity) and health restored notifications, but these are application-level — not infrastructure runbooks. |
| **Gap** | No runbooks or incident response automation. Response is entirely ad hoc. The in-app health check system provides detection but not automated remediation at the infrastructure level. |
| **Recommendation** | Create runbooks for common operational scenarios: database connectivity failure, disk space exhaustion, indexer timeout escalation. Implement SSM Automation documents for automated remediation. The existing health check system's event types can trigger automated responses via EventBridge (prefer) → Step Functions → Lambda remediation. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (detection only), absence of any runbook or SSM document files |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership structure found. No CODEOWNERS file referencing observability assets. No per-service dashboards or alarms with named owners. No team attribution on monitoring resources. No SLO definitions with team responsibility. |
| **Gap** | No observability ownership. No dashboards. No alarm ownership. Monitoring is reactive and fragmented — limited to in-app health checks and Sentry error tracking. |
| **Recommendation** | Create a CODEOWNERS file with ownership for observability configuration. Define per-service CloudWatch dashboards and alarms with team attribution when deploying to AWS. Assign SLO ownership to specific teams. |
| **Evidence** | Absence of CODEOWNERS file, absence of dashboard or alarm configurations |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging found. No IaC exists, so no `default_tags`, `tags` blocks, or tagging standards are defined. No Tag Policies, Config rules, or cost allocation tags. |
| **Gap** | No tags on any resources. No tagging standard. No cost allocation or ownership attribution via tags. |
| **Recommendation** | When creating IaC, define a tagging standard with mandatory tags: `Environment`, `Service`, `Team`, `CostCenter`. Use Terraform `default_tags` or CDK `Tags.of()` for consistent application. Enable AWS Organizations Tag Policies for enforcement. Activate cost allocation tags. |
| **Evidence** | Absence of any IaC files or tagging configuration |

## Learning Materials

Based on the 4 triggered pathways, the following learning resources are recommended:

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
| `global.json` | APP-Q1 | .NET SDK version 10.0.201 |
| `package.json` | APP-Q1, INF-Q4 | Frontend dependencies (React, TypeScript, SignalR client) |
| `src/Directory.Build.props` | APP-Q1, SEC-Q7 | Build configuration, StyleCop analyzers, test packages |
| `src/NzbDrone.Core/Sonarr.Core.csproj` | INF-Q2, DATA-Q3, DATA-Q4, SEC-Q4 | NuGet dependencies: Dapper, Npgsql, FluentMigrator, Polly, MailKit |
| `src/NzbDrone.Common/Sonarr.Common.csproj` | INF-Q2, DATA-Q3, SEC-Q1, OPS-Q1 | SQLite, NLog, Sentry, SharpZipLib dependencies |
| `src/NzbDrone.Host/Sonarr.Host.csproj` | APP-Q1, OPS-Q1 | Host project: Swashbuckle, MiniProfiler, DryIoc |
| `src/Sonarr.Http/Sonarr.Http.csproj` | APP-Q5 | HTTP framework: FluentValidation, MiniProfiler |
| `src/NzbDrone.SignalR/Sonarr.SignalR.csproj` | INF-Q4, APP-Q3 | SignalR real-time communication |
| `src/Sonarr.Api.V3/openapi.json` | APP-Q5, INF-Q6, Quick Agent Wins | V3 OpenAPI specification |
| `src/Sonarr.Api.V5/openapi.json` | APP-Q5, INF-Q6, Quick Agent Wins | V5 OpenAPI specification |
| `src/Sonarr.Http/VersionedApiControllerAttribute.cs` | APP-Q5 | API versioning enforcement |
| `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key authentication implementation |
| `src/Sonarr.Http/Authentication/AuthenticationService.cs` | SEC-Q4 | Authentication service |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | APP-Q2, DATA-Q2 | Centralized data access pattern (Dapper ORM) |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2 | SQLite/PostgreSQL connection abstraction |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2 | Unified SQL query builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` | DATA-Q2 | SQLite-specific query builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | DATA-Q2 | PostgreSQL-specific query builder |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 230+ FluentMigrator database migrations |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | APP-Q2, APP-Q3, INF-Q4 | In-process event-driven communication |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` | APP-Q3, APP-Q4, INF-Q3 | In-process async command queue |
| `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` | INF-Q3 | Command execution logic |
| `src/NzbDrone.Core/Jobs/Scheduler.cs` | INF-Q3 | Scheduled task execution |
| `src/NzbDrone.Core/Jobs/TaskManager.cs` | INF-Q3, INF-Q8 | Task scheduling and management |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Application-level backup and restore |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | INF-Q5, SEC-Q3, SEC-Q5, APP-Q6 | Configuration (bind address, ports, PostgreSQL credentials) |
| `src/NzbDrone.Core/Authentication/UserRepository.cs` | SEC-Q4 | Local user account storage |
| `src/NzbDrone.Core/Authentication/AuthenticationType.cs` | SEC-Q3, SEC-Q4 | Authentication mode definitions |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | SEC-Q1 | NLog database logging target |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | SEC-Q1, OPS-Q1 | Sentry error tracking configuration |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q4, OPS-Q7 | Application health check system |
| `src/NzbDrone.Core/MediaCover/MediaCoverService.cs` | DATA-Q1 | Local filesystem media cover management |
| `src/NzbDrone.Core/MediaFiles/DiskScanService.cs` | DATA-Q1 | Local filesystem media file scanning |
| `src/NzbDrone.Core/Download/` | APP-Q4 | Download client management and monitoring |
| `src/NzbDrone.Core/Notifications/` | OPS-Q4 | Notification dispatch system |
| `src/NzbDrone.Core/Update/` | OPS-Q5 | Self-update mechanism |
| `src/NzbDrone.Core/Analytics/` | OPS-Q3 | Internal analytics tracking |
| `src/NzbDrone.Core/SeriesStats/` | OPS-Q3 | Series statistics |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test suite |
| `src/NzbDrone.Integration.Test/ApiTests/` | OPS-Q6 | API-specific integration tests |
| `distribution/docker-build/Dockerfile` | INF-Q1, SEC-Q6 | Legacy Mono-based Debian packaging Dockerfile |
| `.github/workflows/build_v5.yml` | INF-Q11, OPS-Q6, DATA-Q3 | CI/CD build, test, and deploy pipeline |
| `.github/workflows/deploy.yml` | INF-Q11, OPS-Q5 | Deployment and release workflow |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot configuration (devcontainers only) |
| `.github/actions/build/action.yml` | INF-Q11 | Build action definition |
| `.github/actions/test/action.yml` | INF-Q11, SEC-Q5 | Test action definition (PostgreSQL env vars) |
| `.github/workflows/api_docs.yml` | APP-Q5, Quick Agent Wins | API documentation automation |
| `README.md` | Quick Agent Wins | Project documentation |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
| `SECURITY.md` | Quick Agent Wins | Security policy |
| `src/Sonarr.sln` | APP-Q2 | Solution file — single deployable unit |
