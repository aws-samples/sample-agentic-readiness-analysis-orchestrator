# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Sonarr |
| **Date** | 2025-07-17 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | TV-series PVR for usenet and BitTorrent users (*arr suite) |
| **Overall Score** | 1.97 / 4.0 |

**Archetype Justification**: Database connections (SQLite/PostgreSQL) detected with full CRUD operations on business entities (series, episodes, episode files, download clients, indexers). User-specific state management with entity lifecycle handling. The application owns persistent state and exposes Create/Update/Delete/Read endpoints — classified as stateful-crud.

> **Note**: While classified as `monorepo`, this repository is effectively a single application (Sonarr) with a C# backend and React frontend — it does not contain multiple independent services. The assessment evaluates it as a single application unit.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **1.97 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found — all infrastructure is manually provisioned or nonexistent. | Blocks reproducible deployments, disaster recovery, and environment consistency. Foundational blocker for all modernization pathways. |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Lambda/Fargate). Application is distributed as self-hosted binaries. | Prevents elastic scaling, auto-patching, and cloud-native deployment. Triggers Move to Containers and Move to Cloud Native pathways. |
| 3 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline. | Vulnerabilities in dependencies or application code reach production undetected. Security scanning is absent despite a mature CI/CD pipeline. |
| 4 | INF-Q2: Managed Databases | 1 | Databases are self-managed — embedded SQLite or user-provisioned PostgreSQL. No managed AWS database services. | Requires manual backup management, patching, and scaling. Triggers Move to Managed Databases pathway. |
| 5 | SEC-Q5: Secrets Management | 1 | Secrets (API keys, database credentials) stored in local configuration files with no rotation mechanism. | No audit trail, no rotation, no centralized management. Critical security gap for any cloud deployment. |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 4). OpenAPI specs for both V3 (`src/Sonarr.Api.V3/openapi.json`) and V5 (`src/Sonarr.Api.V5/openapi.json`) with Swagger generation configured in `Startup.cs`.
- **What it enables:** An API-aware agent can discover and invoke Sonarr's existing API endpoints as tools — managing series, triggering searches, checking queue status, and managing download clients programmatically.
- **Additional steps:** OpenAPI specs are already generated. Agent can consume them directly for tool discovery. Ensure specs are kept up to date with each release.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 4). Centralized data access layer via `BasicRepository<T>` pattern with well-defined entity models in `src/NzbDrone.Core/Datastore/`.
- **What it enables:** A natural language to SQL agent can query series information, episode status, download history, and media file metadata through the centralized data access layer.
- **Additional steps:** Schema documentation would need to be generated from the `TableMapping` configuration. Consider read-only access patterns to prevent unintended mutations.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). Comprehensive GitHub Actions pipeline with multi-platform build, unit tests, PostgreSQL tests, integration tests, packaging, and deployment.
- **What it enables:** A DevOps agent can trigger builds, monitor test results across platforms (Ubuntu/macOS/Windows), check deployment status, and manage releases via GitHub Actions API.
- **Additional steps:** GitHub Actions API access is available. Agent would need GitHub token with appropriate permissions to trigger workflows and read results.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists. `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and extensive wiki references (wiki.servarr.com) detected in the repository.
- **What it enables:** A RAG knowledge agent can index Sonarr's documentation, contributing guidelines, and API docs to answer developer and user questions about setup, configuration, and development workflows.
- **Additional steps:** Wiki content at wiki.servarr.com would need to be crawled/indexed alongside the in-repo documentation. The OpenAPI specs provide additional structured knowledge.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolith), INF-Q1 = 1 (no managed compute), APP-Q3 = 2 (limited async) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no managed compute), no runtime container definitions found. Compute is not ECS/EKS/Lambda/Fargate. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). SQLite and PostgreSQL are already open-source engines. No commercial DB engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (self-managed databases — embedded SQLite/user PostgreSQL). DATA-Q3 = 3 (supporting). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected. This is a media PVR, not a data analytics application. No streaming/ETL/analytics artifacts found. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). Supporting: OPS-Q5 = 2 (no canary/blue-green). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "TV-series PVR for usenet and BitTorrent users" contains no AI-related signal terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
Sonarr is a monolithic .NET 10 application with a single deployable unit (`Sonarr.sln`). The codebase has identifiable module boundaries (NzbDrone.Core, NzbDrone.Host, Sonarr.Api.V3, Sonarr.Api.V5, Sonarr.Http, NzbDrone.Common) but shares a single embedded SQLite database. All compute runs as a self-hosted binary on user-managed infrastructure with no cloud-native deployment model.

**Compute Model Gaps (INF-Q1):**
No managed compute resources exist. The application is distributed as platform-specific binaries (Linux, macOS, Windows, FreeBSD) via GitHub Releases. There are no ECS task definitions, EKS manifests, Lambda functions, or Fargate configurations.

**Communication Pattern Gaps (APP-Q3):**
The application uses an internal `EventAggregator` for in-process pub/sub but has no external async messaging infrastructure. Outbound HTTP calls to indexers and download clients are synchronous.

**Recommended Decomposition Approach:**
See the Decomposition Strategy section below. The Strangler Fig pattern is recommended given the clear module boundaries in the Sonarr codebase.

**Representative AWS Services:** Lambda, Amazon API Gateway, Step Functions, Amazon EventBridge, Amazon EKS, Amazon ECS
**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Hexagonal Architecture
**Prescriptive Guidance:** [AWS Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) · [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
Sonarr is distributed as self-contained platform-specific binaries (10 runtime targets: linux-x64, linux-arm, linux-arm64, linux-musl-x64, linux-musl-arm64, osx-x64, osx-arm64, win-x64, win-x86, freebsd-x64). Users install and run the binary directly on their host OS. The Dockerfile at `distribution/docker-build/Dockerfile` is a Mono/Debian build-packaging container, not a runtime container.

**Container Readiness Indicators:**
- ✅ .NET 10 self-contained deployment already produces portable binaries
- ✅ Configuration externalized via environment variables (`Sonarr__Postgres__Host`, etc.) and config files
- ✅ Application listens on a configurable port (default 8989)
- ⚠️ SQLite database file requires persistent volume mounting
- ⚠️ Media library paths require volume mounting

**Recommended Container Orchestration Platform:**
Amazon EKS (per preferences: `prefer: ["eks"]`) for production container orchestration. EKS provides managed Kubernetes with Graviton node support and integrates with AWS services for logging, monitoring, and secrets management.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS Fargate (for EKS), AWS App Runner
**Migration Approach:** Lift-and-containerize first (create a runtime Dockerfile for the .NET 10 binary), then refactor for cloud-native patterns (externalize SQLite to Aurora PostgreSQL, add health check endpoints for Kubernetes probes).
**Prescriptive Guidance:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
- **Primary:** Embedded SQLite via `System.Data.SQLite` (version 2.0.2) and `SourceGear.sqlite3` (version 3.50.4.5). Single-file database stored on the local filesystem.
- **Optional:** PostgreSQL via `Npgsql` (version 10.0.2) with FluentMigrator support. Users can configure Sonarr to use PostgreSQL instead of SQLite via environment variables (`Sonarr__Postgres__*`).
- **Hosting Model:** Self-managed. SQLite is embedded in-process. PostgreSQL, when used, is user-provisioned and managed.

**Engine Versions and EOL Status (DATA-Q3):**
SQLite 3.50.x and PostgreSQL (tested against versions 16, 17, 18 in CI) are actively maintained with no EOL concerns.

**Data Access Patterns (DATA-Q2):**
Centralized data access through `BasicRepository<T>` pattern using Dapper ORM. All database operations go through `src/NzbDrone.Core/Datastore/`. This centralization makes database migration significantly easier — connection strings and database-specific code (e.g., `WhereBuilderPostgres.cs` vs `WhereBuilderSqlite.cs`) are already isolated.

**Recommended Managed Database Target:**
Amazon Aurora PostgreSQL (per preferences: `prefer: ["aurora"]`). The application already supports PostgreSQL as an alternative to SQLite, making the migration path straightforward. Aurora provides automated backups, Multi-AZ failover, auto-scaling read replicas, and managed patching.

**Representative AWS Services:** Amazon Aurora PostgreSQL, Amazon RDS PostgreSQL, Amazon DynamoDB (for metadata/caching if decomposed)
**Migration Tools:** AWS Database Migration Service (DMS) for PostgreSQL-to-Aurora migration. For SQLite-to-Aurora: export data from SQLite, import to Aurora PostgreSQL using pg_restore or DMS.
**Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10):**
No Infrastructure as Code files found in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize manifests. All infrastructure — if any cloud infrastructure exists — would be manually provisioned (ClickOps).

**Current CI/CD State (INF-Q11):**
The CI/CD pipeline is mature for application code:
- Multi-platform builds (10 runtime targets) via GitHub Actions (`.github/workflows/build_v5.yml`)
- Unit tests across Ubuntu, macOS, Windows
- PostgreSQL integration tests (versions 16, 17, 18)
- Integration tests running actual Sonarr binary on 3 OS platforms
- Automated packaging and GitHub Release creation (`.github/workflows/deploy.yml`)
- Update publishing to services.sonarr.tv

**The gap is in infrastructure automation**, not application CI/CD.

**Deployment Strategy Gaps (OPS-Q5):**
Binary distribution via GitHub Releases with an update service at services.sonarr.tv. No canary or blue/green deployment. Users self-update via the built-in update mechanism. For a cloud-native deployment, staged rollouts would need to be implemented.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK (TypeScript) or Terraform for defining EKS clusters, Aurora databases, networking, and security configuration
- **Container Registry:** Amazon ECR
- **Deployment:** AWS CodeDeploy with EKS for blue/green deployments, or ArgoCD for GitOps
- **Monitoring:** Amazon CloudWatch with Container Insights for EKS

**Representative AWS Services:** AWS CDK, AWS CloudFormation, Amazon ECR, AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy, Amazon CloudWatch
**Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

> **Condition:** APP-Q2 = 2 (monolith with identifiable modules but shared database schemas). Decomposition strategy applies.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2 = 2. Sonarr has recognizable module boundaries (Core, Host, Api.V3, Api.V5, Http, Common) that can be extracted incrementally. | **Medium to High** — 6–18 months depending on scope. Each extraction is bounded. | ✅ **Recommended.** Lowest risk, incremental value delivery, no big-bang cutover. Start by extracting the indexer/download client integration as a separate service. |
| **Conditional / Adaptive** | Team has limited capacity. Containerize Sonarr as-is first, then selectively extract high-value modules (e.g., notification service, media scanner). | **Low to Medium** — Containerization in 2–4 weeks, selective extraction over 3–12 months. | ✅ **Recommended as initial step.** Containerize first (Move to Containers), migrate to Aurora PostgreSQL (Move to Managed Databases), then evaluate which modules warrant extraction. |
| **Big-Bang Rewrite** | Almost never. Only if the monolith is unmaintainable. | **Very High** — 12–24+ months. High risk. | ⚠️ **Not recommended.** Sonarr has clean module boundaries, centralized data access, and active development. Incremental approaches are clearly viable. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from Sonarr's data model and internal APIs. | Every extraction — place an ACL between the new service and the Sonarr monolith. | [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions for operations that span the monolith and extracted services. | When extracting download management or series monitoring — multi-step workflows. | [Saga Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture state changes as events for audit trails and cross-service integration. | When extracting notification or history services — multiple consumers react to the same events. | [Event Sourcing Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear boundaries between business logic and infrastructure. | Every new service — ensures testability and infrastructure portability. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal in Sonarr | Effort Impact |
|--------|-----------------|---------------|
| Module boundaries | Clear project separation: NzbDrone.Core, Sonarr.Api.V3/V5, Sonarr.Http, NzbDrone.Common. | **Low** — identifiable extraction points |
| Data coupling | Centralized `BasicRepository<T>` with single shared database (SQLite/PostgreSQL). All entities share the same database. | **Medium** — data separation required per extracted service |
| Stored procedures | None — all logic in C# application layer (DATA-Q4 = 4). | **Low** — no database-coupled logic to extract |
| Communication patterns | Internal `EventAggregator` for pub/sub. Some async event handling. | **Medium** — EventAggregator patterns can map to Amazon EventBridge events |
| CI/CD maturity | Comprehensive GitHub Actions pipeline with multi-platform build/test/deploy (INF-Q11 = 3). | **Low** — existing pipeline can be extended for multi-service deployment |
| Test coverage | Integration tests across 3 platforms with actual binary (OPS-Q6 = 3). Extensive unit tests. | **Low** — existing test coverage reduces regression risk during extraction |

**Calibrated Effort Estimate:** The recommended Conditional/Adaptive approach (containerize first, then selective extraction) is estimated at **3–6 months for initial containerization and Aurora migration**, followed by **6–12 months for selective service extraction** based on business priority.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute resources (ECS, EKS, Lambda, Fargate) are defined. Sonarr is distributed as self-contained platform-specific binaries for 10 runtime targets (linux-x64, linux-arm64, osx-arm64, win-x64, etc.). Users install and run the binary directly on their host OS or VM. The Dockerfile at `distribution/docker-build/Dockerfile` is a Mono/Debian build-packaging container using Ubuntu Focal and Mono 5.18 — not a runtime container. |
| **Gap** | All compute is on raw self-hosted infrastructure with no managed services. No cloud compute provisioning exists. |
| **Recommendation** | Containerize the .NET 10 application with a runtime Dockerfile and deploy on Amazon EKS (preferred). The self-contained binary model is already well-suited for containerization. Start with a single-container deployment on EKS with Fargate for serverless pod execution. |
| **Evidence** | `distribution/docker-build/Dockerfile`, `.github/workflows/build_v5.yml` (10 runtime targets), `.github/workflows/deploy.yml` (binary distribution) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Databases are entirely self-managed. Primary database is embedded SQLite via `System.Data.SQLite` (v2.0.2) and `SourceGear.sqlite3` (v3.50.4.5) — a single file on the local filesystem. Optional PostgreSQL support via `Npgsql` (v10.0.2) is available but user-provisioned. No AWS managed database resources exist (no IaC). |
| **Gap** | All databases self-managed — embedded SQLite on local filesystem or user-provisioned PostgreSQL. No automated failover, managed backups, or scaling. |
| **Recommendation** | Migrate to Amazon Aurora PostgreSQL (preferred). Sonarr already supports PostgreSQL as an alternative backend — the migration path is well-defined. Aurora provides automated backups, Multi-AZ failover, and auto-scaling read replicas. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (SourceGear.sqlite3 v3.50.4.5, System.Data.SQLite v2.0.2), `src/NzbDrone.Core/Sonarr.Core.csproj` (Npgsql v10.0.2, Dapper v2.1.72), `src/NzbDrone.Core/Datastore/DbFactory.cs` (SQLite and PostgreSQL connection factories) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | *Archetype: stateful-crud.* The application has an internal command/task scheduling system (`src/NzbDrone.Core/Jobs/TaskManager.cs`) that manages scheduled tasks (RSS sync, health checks, series refresh, backups, housekeeping) with interval-based execution. The `CommandExecutor` (`src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`) runs a 3-thread command processing pool with priority queuing, disk access management, and exclusive command handling. This is a structured in-code state machine with some orchestration patterns, but no dedicated workflow orchestration service. |
| **Gap** | Multi-step workflows (download → process → rename → notify) are implemented as hardcoded command chains in application code. No dedicated orchestration service (Step Functions, Temporal) for visibility into workflow state, retry logic, or error handling at the orchestration level. |
| **Recommendation** | For a cloud-native deployment, extract the task scheduling and command execution system to AWS Step Functions for visual workflow management, built-in retry/error handling, and state visibility. The existing command pattern maps naturally to Step Functions states. Use Amazon EventBridge for scheduled triggers instead of the internal `TaskManager`. |
| **Evidence** | `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | *Archetype: stateful-crud.* The application uses an internal `EventAggregator` (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) for in-process pub/sub with both synchronous (`IHandle<TEvent>`) and asynchronous (`IHandleAsync<TEvent>`) handlers. This provides event-driven communication within the monolith. However, there is no external managed messaging infrastructure (SQS, SNS, EventBridge). Cross-service state changes would require external messaging if the application were decomposed. |
| **Gap** | No external messaging infrastructure. The internal EventAggregator is process-local and would not survive application restarts or work across service boundaries. For a stateful-crud application with cross-service state changes, managed messaging should be in place. |
| **Recommendation** | When decomposing, replace the internal `EventAggregator` with Amazon EventBridge (preferred) for cross-service event routing. The existing `IHandle<TEvent>` / `IHandleAsync<TEvent>` pattern maps directly to EventBridge event consumers. For command processing, use Amazon SQS as a managed replacement for the in-memory `CommandQueue`. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Messaging/Events/IHandle.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security group, NACL, or network segmentation configuration exists. No IaC defines any AWS networking resources. The application self-hosts on Kestrel with forwarded headers support for private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 configured in `Startup.cs`), but this is application-level trust, not infrastructure-level network security. CORS is configured to allow any origin (`AllowAnyOrigin()`). |
| **Gap** | Services deployed without any network isolation. The CORS policy allows all origins — appropriate for a self-hosted application but a security concern for cloud deployment. |
| **Recommendation** | Deploy in a VPC with private subnets for the application and database. Use security groups with least-privilege rules. Place Amazon API Gateway (preferred) in front of the application for request validation and throttling. Restrict CORS to specific allowed origins. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (ForwardedHeaders configuration, CORS AllowAnyOrigin) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront is configured. The application self-hosts on Kestrel (ASP.NET Core's built-in web server) listening on port 8989. API endpoints are exposed directly without any gateway layer. Swagger is available in debug mode only (`if (BuildInfo.IsDebug)` in `Startup.cs`). |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, request validation, or centralized authentication at the gateway level. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point with throttling, request validation, and API key management. API Gateway can import the existing OpenAPI specs (`openapi.json`) directly for route configuration. For internal traffic, consider Amazon VPC Lattice for service-to-service routing. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (Kestrel self-hosting, Swagger debug-only), `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application runs as a single-instance process on user-managed infrastructure. No AWS auto-scaling resources (ASG, ECS service scaling, Lambda concurrency, DynamoDB auto-scaling) are defined. |
| **Gap** | No auto-scaling — all capacity is statically provisioned by the user. |
| **Recommendation** | When deployed on EKS, configure Horizontal Pod Autoscaler (HPA) based on CPU/memory utilization. For Aurora PostgreSQL, enable auto-scaling read replicas. Consider Karpenter for EKS node auto-scaling with Graviton instances. |
| **Evidence** | No IaC files found. No auto-scaling configuration in any discovered file. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has a built-in backup system (`src/NzbDrone.Core/Backup/BackupService.cs`) that creates ZIP archives of the SQLite database and configuration. Backups are scheduled via `TaskManager` with configurable intervals and retention periods. Backups are stored on the local filesystem. A restore API endpoint exists. However, there is no AWS-managed backup infrastructure (AWS Backup, RDS automated backups, S3 cross-region replication) and no PITR support. |
| **Gap** | Backups exist but are stored locally with no cloud-managed backup infrastructure. No PITR support. No cross-region backup replication. No restore testing automation. |
| **Recommendation** | When migrated to Aurora PostgreSQL, automated backups with PITR are included. For the containerized deployment, use AWS Backup for EBS volume snapshots. Store application backups in S3 with versioning and cross-region replication for critical data. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, `src/NzbDrone.Core/Backup/BackupCommand.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` (backup scheduling) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ or high availability configuration exists. The application runs as a single instance on user-managed infrastructure. No load balancer, no multi-AZ database, no failover configuration. The `ISingleInstancePolicy` in `Startup.cs` explicitly enforces single-instance execution — it kills other instances if detected. |
| **Gap** | All resources in a single instance; single-instance enforcement is by design. No fault isolation or automatic recovery. |
| **Recommendation** | For cloud deployment, deploy on EKS across multiple AZs with Aurora PostgreSQL Multi-AZ. The single-instance enforcement (`ISingleInstancePolicy`) will need to be refactored — either use leader election patterns or redesign for stateless horizontal scaling. Consider EBS-backed persistent volumes for the media library across AZs. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (EnsureSingleInstance method, ISingleInstancePolicy) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository. No Terraform (`.tf`), CloudFormation, CDK (`cdk.json`), Helm charts (`Chart.yaml`), or Kustomize (`kustomization.yaml`) files exist. All infrastructure — if any cloud infrastructure is provisioned — would be created manually. |
| **Gap** | No IaC — all infrastructure would need to be created manually (ClickOps). This is the foundational blocker for reproducible cloud deployments. |
| **Recommendation** | Adopt AWS CDK (TypeScript or C#) or Terraform to define the target cloud infrastructure: EKS cluster, Aurora PostgreSQL database, VPC networking, API Gateway, EventBridge rules, and CloudWatch monitoring. IaC is the prerequisite for all other modernization pathways. |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found in repository scan. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD pipeline via GitHub Actions. The `build_v5.yml` workflow includes: multi-platform backend builds (10 runtime targets), frontend build with lint/stylelint, unit tests on Ubuntu/macOS/Windows, PostgreSQL-specific tests (versions 16/17/18), integration tests running actual Sonarr binary on 3 platforms. The `deploy.yml` workflow handles packaging (10 platforms), GitHub Release creation with release notes, and publishing update metadata to services.sonarr.tv. Composite actions in `.github/actions/` (build, test, package) provide reusable build steps. Concurrency control prevents duplicate runs. |
| **Gap** | No automated rollback mechanism. No infrastructure deployment pipeline (no IaC to deploy). Deploy workflow targets `v5-develop-final` and `v5-main-final` branches only. No security scanning stages in the pipeline. |
| **Recommendation** | Add infrastructure deployment stages to the pipeline when IaC is adopted. Add automated rollback for failed deployments. Integrate security scanning (SAST, dependency scanning) into the build pipeline. Consider AWS CodePipeline for infrastructure deployment orchestration. |
| **Evidence** | `.github/workflows/build_v5.yml`, `.github/workflows/deploy.yml`, `.github/actions/build/action.yml`, `.github/actions/test/action.yml`, `.github/actions/package/` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Backend: C# on .NET 10.0 (SDK 10.0.201 per `global.json`). Frontend: TypeScript/React 18 with Webpack build pipeline. C#/.NET has good AWS SDK coverage (`AWSSDK.*` NuGet packages), mature cloud-native tooling (ASP.NET Core, Kestrel), and first-class container support. TypeScript has first-class AWS SDK coverage (`@aws-sdk/*`). |
| **Gap** | C#/.NET has narrower cloud-native ecosystem compared to Python/TypeScript/Go/Java. Some AWS services have delayed or reduced .NET SDK feature parity. |
| **Recommendation** | C#/.NET 10 is a solid choice for cloud-native development with good AWS SDK support. No language migration is needed. Leverage the AWS SDK for .NET for service integration. Consider using AWS Lambda with .NET 10 for extracted microservices. |
| **Evidence** | `global.json` (.NET SDK 10.0.201), `src/Directory.Build.props` (net10.0 target framework), `package.json` (TypeScript 5.7.2, React 18.3.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit (`Sonarr.sln`) built as one binary. Well-organized module structure with clear project separation: `NzbDrone.Core` (business logic), `NzbDrone.Host` (hosting/startup), `Sonarr.Api.V3` / `Sonarr.Api.V5` (API layers), `Sonarr.Http` (HTTP infrastructure), `NzbDrone.Common` (shared utilities), `NzbDrone.SignalR` (real-time notifications). However, all modules share a single database (SQLite or PostgreSQL) through the centralized `BasicRepository<T>` pattern. The Datastore layer is shared across all modules with no per-module schema isolation. |
| **Gap** | Monolith with identifiable modules but shared database schemas. Direct cross-module data access through the shared `BasicRepository<T>`. No independent deployability — all modules must be released together. |
| **Recommendation** | Start with the Conditional/Adaptive decomposition approach: containerize the monolith first, migrate to Aurora PostgreSQL, then selectively extract high-value modules (notifications, indexer integration, download client management) as independent services with separate schemas. See the Decomposition Strategy section. |
| **Evidence** | `src/Sonarr.sln`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (shared data access), `src/NzbDrone.Host/Sonarr.Host.csproj` (references all projects), `src/Sonarr.Api.V3/` (26+ API controller directories), `src/Sonarr.Api.V5/` (25+ API controller directories) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | *Archetype: stateful-crud.* As a monolith, there is no inter-service communication. Internal communication uses the `EventAggregator` with both sync (`IHandle<TEvent>`) and async (`IHandleAsync<TEvent>`) handlers. Outbound HTTP calls to external services (indexers like Newznab/Torznab, download clients like SABnzbd/NZBGet/Transmission) are synchronous. The `CommandExecutor` processes commands asynchronously via a 3-thread pool with priority queuing. The `Polly` library (v8.6.6) is included for resilience patterns (retry with exponential backoff on SQLite busy errors). |
| **Gap** | For a stateful-crud archetype, the expectation is that cross-service state propagation uses async messaging. While the internal EventAggregator provides some async patterns, external integration (indexers, download clients) is entirely synchronous HTTP. No managed messaging (SQS, SNS, EventBridge) for state changes that would cross service boundaries in a decomposed architecture. |
| **Recommendation** | When decomposing, introduce Amazon EventBridge (preferred) for cross-service event publishing. The existing `IHandleAsync<TEvent>` patterns provide a natural migration path. For external integrations (indexers, download clients), consider wrapping synchronous calls with SQS-based async patterns to improve resilience. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` (sync + async handlers), `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` (3-thread async processing), `src/NzbDrone.Core/Sonarr.Core.csproj` (Polly v8.6.6) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | *Archetype: stateful-crud.* The application has a well-structured command/task system for long-running operations. The `CommandQueue` (`src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`) manages async command execution with priority queuing, disk access coordination, and exclusive command handling. Long-running operations (RSS sync, series refresh, media scanning, backup) are implemented as commands processed by the `CommandExecutor`'s 3-thread pool. Commands have status tracking (`CommandStatus`: Queued, Started, Completed, Failed) and the API exposes command status via `/api/v3/command` and `/api/v5/command` endpoints. Real-time status updates are pushed via SignalR (`NzbDrone.SignalR`). |
| **Gap** | Most long-running operations are handled async. However, the command system is in-process — command state is lost on application restart. Some operations may still block (e.g., synchronous indexer searches triggered from the UI). |
| **Recommendation** | The existing command/task system is well-designed for a stateful-crud monolith. When migrating to cloud-native, replace the in-process command queue with SQS + Step Functions for durable, distributed command execution with built-in retry and state persistence. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandStatus.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Host/Startup.cs` (BufferingMiddleware for `/api/v3/command`) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Consistent API versioning strategy using URL path-based versioning: `/api/v3/` and `/api/v5/`. Two separate API projects (`Sonarr.Api.V3` and `Sonarr.Api.V5`) with independent controller implementations. OpenAPI specifications generated for both versions via Swashbuckle (`SwaggerDoc("v3", ...)` and `SwaggerDoc("v5", ...)`). A `DocInclusionPredicate` in `Startup.cs` ensures controllers are included in the correct API version document based on `VersionedApiControllerAttribute`. Backward compatibility maintained — V3 API serves both v3 and v4 of the Sonarr application. |
| **Gap** | None identified. Versioning strategy is consistent and well-implemented with backward compatibility guarantees. |
| **Recommendation** | No changes needed. The API versioning strategy is mature. When deploying behind Amazon API Gateway, leverage API Gateway's stage management to map to the existing version paths. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (SwaggerDoc v3/v5, DocInclusionPredicate), `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `src/Sonarr.Api.V3/` (26+ controller directories), `src/Sonarr.Api.V5/` (25+ controller directories) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | As a single application, traditional service discovery is not required for internal communication. External service endpoints (indexers, download clients, notification targets) are configured by users through the Sonarr UI and stored in the database. Configuration is retrieved from the database at runtime. No environment variables for service discovery. No dynamic service registry (AWS Service Discovery, Consul, Istio). |
| **Gap** | Environment variables or database-stored configuration for external endpoints but no dynamic discovery. In a decomposed architecture, hard-coded or database-stored endpoints would create deployment coupling. |
| **Recommendation** | When decomposing, adopt AWS Cloud Map for service discovery or use EKS internal DNS for service-to-service communication. For external integrations (indexers, download clients), consider a configuration service backed by AWS Systems Manager Parameter Store or DynamoDB (preferred) to centralize endpoint management. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs` (database-backed configuration), `src/Sonarr.Api.V3/Indexers/` (indexer configuration), `src/Sonarr.Api.V3/DownloadClient/` (download client configuration) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Media files (TV episodes) are stored on the local filesystem in user-configured root folders. Media cover images are downloaded from external sources (TVDB, TMDB) and cached locally. The application manages file paths, renames, and moves files on the local disk. No S3 or managed object storage is used. No document parsing capabilities (Textract, Tika). |
| **Gap** | Data on local file systems with no cloud object storage. Media files and cover art are inaccessible for modern workloads (search, analytics, AI integration). |
| **Recommendation** | For cloud deployment, store media cover art and metadata in Amazon S3 with CloudFront for CDN delivery. For media files, evaluate Amazon S3 File Gateway for NFS/SMB compatibility (the application uses filesystem APIs for media management). Large media libraries would benefit from S3 Intelligent-Tiering for cost optimization. |
| **Evidence** | `src/NzbDrone.Core/MediaFiles/` (media file management), `src/NzbDrone.Core/MediaCover/` (cover image handling), `src/NzbDrone.Core/RootFolders/` (root folder configuration) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Highly centralized data access layer in `src/NzbDrone.Core/Datastore/`. The `BasicRepository<T>` pattern provides a single point of data access with CRUD operations, pagination, filtering, and model events. All database operations go through this layer — no modules bypass it for direct SQL. `TableMapping` provides consistent entity-to-table mapping. `SqlBuilder` generates SQL queries. Database-specific behaviors are isolated in `WhereBuilderSqlite.cs` and `WhereBuilderPostgres.cs`. Dapper is used as the micro-ORM with explicit SQL generation. 230+ migration files in `src/NzbDrone.Core/Datastore/Migration/` maintain schema consistency. |
| **Gap** | None identified. The data access layer is well-centralized with a single point of data contract. |
| **Recommendation** | No changes needed. The centralized data access layer is a significant modernization asset — it makes database migration (SQLite → Aurora PostgreSQL) straightforward by isolating database-specific code. Maintain this pattern when decomposing into services. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/TableMapping.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs`, `src/NzbDrone.Core/Datastore/Migration/` (230+ migration files) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are pinned in NuGet package references: `SourceGear.sqlite3` v3.50.4.5, `System.Data.SQLite` v2.0.2, `Npgsql` v10.0.2, `FluentMigrator.Runner.SQLite` v8.0.1, `FluentMigrator.Runner.Postgres` v8.0.1. SQLite 3.50.x is current and actively maintained. PostgreSQL is tested in CI against versions 16, 17, and 18 — all actively supported with no EOL within 12 months. However, there is no documented version-update procedure covering downtime windows, rollback, or risk acknowledgment. |
| **Gap** | Versions pinned and no EOL risk, but no documented version-update procedure. Migration file `000_database_engine_version_check.cs` suggests a version check at startup, but no formal upgrade runbook exists. |
| **Recommendation** | Document a database engine version update procedure covering testing, rollback, and downtime considerations. When migrating to Aurora PostgreSQL, leverage Aurora's managed version upgrades with automated backup before upgrade. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (SourceGear.sqlite3 v3.50.4.5, System.Data.SQLite v2.0.2), `src/NzbDrone.Core/Sonarr.Core.csproj` (Npgsql v10.0.2), `.github/workflows/build_v5.yml` (PostgreSQL 16/17/18 test matrix), `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs detected. All business logic is implemented in the C# application layer. Database operations use Dapper with dynamically generated SQL (INSERT, UPDATE, DELETE, SELECT) in `BasicRepository<T>`. Schema migrations are managed via FluentMigrator with C# code-based migrations — no raw SQL files with proprietary constructs. The migration files (230+) use FluentMigrator's database-agnostic API, not database-specific SQL. |
| **Gap** | None identified. All business logic is in the application layer with no database-coupled logic. |
| **Recommendation** | No changes needed. The absence of stored procedures and proprietary SQL significantly reduces database migration complexity. This is a strong asset for the Move to Managed Databases pathway. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Dapper-based data access, no stored procedure calls), `src/NzbDrone.Core/Datastore/Migration/` (FluentMigrator-based migrations), `src/NzbDrone.Core/Sonarr.Core.csproj` (FluentMigrator.Runner.Core v8.0.1) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent immutable audit logging infrastructure. The application uses NLog for structured logging (NLog v5.5.1, NLog.Layouts.ClefJsonLayout v1.0.5 for JSON, NLog.Targets.Syslog v7.0.0 for syslog). Logs are stored in a separate log database (SQLite or PostgreSQL). Application logs capture operational events but are not immutable — they can be modified or deleted. |
| **Gap** | No immutable audit trail. Logs are stored in a mutable database without log file validation or object lock. No CloudTrail for infrastructure-level audit logging. |
| **Recommendation** | When deployed on AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. For application-level audit logs, ship NLog output to Amazon CloudWatch Logs with configurable retention. Consider using the existing syslog target (`NLog.Targets.Syslog`) to forward to a centralized log aggregator. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (NLog v5.5.1, NLog.Layouts.ClefJsonLayout v1.0.5, NLog.Targets.Syslog v7.0.0), `src/NzbDrone.Core/Datastore/LogDatabase.cs` (log database) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured. SQLite database is stored as an unencrypted file on the local filesystem. PostgreSQL connection strings (when used) do not reference SSL/TLS encryption parameters in the codebase. No KMS keys, no AWS encryption configuration (no IaC). Data protection keys are persisted to the filesystem (`PersistKeysToFileSystem` in `Startup.cs`). |
| **Gap** | No encryption at rest configured. Database files, media metadata, and data protection keys stored unencrypted on disk. |
| **Recommendation** | When deployed on AWS, use KMS customer-managed keys for Aurora PostgreSQL encryption at rest. Enable EBS encryption for container storage volumes. Use AWS Secrets Manager for data protection key storage instead of filesystem persistence. Enable S3 server-side encryption (SSE-KMS) for any object storage. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (PersistKeysToFileSystem), `src/NzbDrone.Core/Datastore/DbFactory.cs` (unencrypted connections) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API authentication uses static API keys via `X-Api-Key` header or `apikey` query parameter, implemented in `ApiKeyAuthenticationHandler.cs`. The handler validates the provided key against a stored API key from `ConfigFileProvider`. A fallback authorization policy requires authentication on all endpoints except those marked `[AllowAnonymous]`. Forms-based cookie authentication is available for UI access. Additionally, Bearer token format is supported (`Authorization: Bearer <key>`), but this is still an API key, not a JWT/OAuth2 token. No token expiration, no refresh mechanism, no scoped permissions. |
| **Gap** | API key authentication without token-based auth (OAuth2/JWT). No token expiration, rotation, or scoped permissions. API key passed as query parameter is logged in URLs. |
| **Recommendation** | When deploying behind Amazon API Gateway (preferred), use API Gateway's built-in API key management with usage plans for throttling. For user authentication, integrate with Amazon Cognito for OAuth2/JWT token-based auth with token expiration and refresh. Consider migrating the Forms-based auth to Cognito hosted UI. |
| **Evidence** | `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Sonarr.Http/Authentication/AuthenticationBuilderExtensions.cs`, `src/NzbDrone.Host/Startup.cs` (FallbackPolicy, AddAppAuthentication) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application manages its own authentication entirely. Custom username/password authentication stored in the local database (migration `076_add_users_table.cs` creates the users table, `174_add_salt_to_users.cs` adds salted password hashing). Password hashing uses `Microsoft.AspNetCore.Cryptography.KeyDerivation`. No integration with external identity providers (Cognito, Okta, Ping, SAML, OIDC). The `AuthenticationType` enum supports `None`, `External`, and `Forms` modes, where `External` trusts a reverse proxy for auth — but this is header-based trust, not IdP federation. |
| **Gap** | Application manages its own authentication with no external IdP integration. No SSO, no OIDC federation, no SAML support. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. Cognito provides OIDC/SAML federation, MFA, social login, and user pool management. The existing `External` auth mode can be leveraged as an intermediary step — place Cognito behind an ALB or API Gateway and use the `External` mode to trust the Cognito-authenticated headers. |
| **Evidence** | `src/Sonarr.Http/Authentication/AuthenticationBuilderExtensions.cs` (AuthenticationType: None, External, Forms), `src/NzbDrone.Core/Datastore/Migration/076_add_users_table.cs`, `src/NzbDrone.Core/Datastore/Migration/174_add_salt_to_users.cs`, `src/NzbDrone.Core/Sonarr.Core.csproj` (Microsoft.AspNetCore.Cryptography.KeyDerivation v10.0.5) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No dedicated secrets management system (AWS Secrets Manager, HashiCorp Vault). API keys are stored in local configuration files (`Config.xml`). Database credentials for PostgreSQL are passed via environment variables (`Sonarr__Postgres__Password`). The `SERVICES_API_KEY` for the deployment pipeline is stored as a GitHub Actions secret. Data protection keys are stored on the local filesystem. No secret rotation mechanism exists. |
| **Gap** | Secrets stored in local configuration files and environment variables with no rotation, no centralized management, and no audit trail. |
| **Recommendation** | Migrate secrets to AWS Secrets Manager with automated rotation. Store database credentials, API keys, and data protection keys in Secrets Manager. Use AWS Secrets Manager CSI driver for EKS to inject secrets as volumes. Remove secrets from environment variables and local config files. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (PersistKeysToFileSystem), `.github/workflows/deploy.yml` (SERVICES_API_KEY as GitHub secret), `.github/actions/test/action.yml` (Sonarr__Postgres__Password=postgres in env vars) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependabot is configured (`.github/dependabot.yml`) but only for devcontainer updates — not for NuGet or npm packages. NuGet packages are version-pinned in `.csproj` files with explicit version numbers. StyleCop analyzers (v1.2.0.556) enforce code quality standards at build time. .NET 10 provides automatic security updates via runtime patches (`TargetLatestRuntimePatch=true` in `Directory.Build.props`). Sentry SDK (v5.16.3) for crash reporting. However, there is no SSM Patch Manager, no Inspector scanning, no hardened base images. |
| **Gap** | Dependabot limited to devcontainers only — does not scan NuGet or npm dependencies for vulnerabilities. No vulnerability scanning (Inspector/Snyk). No hardened base images. Manual patching of dependencies. |
| **Recommendation** | Expand Dependabot configuration to cover NuGet and npm ecosystems. When containerized, use Bottlerocket or Amazon Linux 2023 as base images for EKS nodes. Enable Amazon Inspector for container image vulnerability scanning. Use ECR image scanning for continuous vulnerability assessment. |
| **Evidence** | `.github/dependabot.yml` (devcontainers only), `src/Directory.Build.props` (StyleCop.Analyzers.Unstable v1.2.0.556, TargetLatestRuntimePatch=true), `src/NzbDrone.Common/Sonarr.Common.csproj` (Sentry v5.16.3) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The `build_v5.yml` workflow runs: build → lint → unit test → integration test → deploy. No security scanning stage exists. Dependabot is configured only for devcontainers (not NuGet/npm). StyleCop analyzers provide code quality checks but not security analysis. No Snyk, SonarQube, Semgrep, CodeGuru Reviewer, npm audit, or dotnet-audit in the pipeline. |
| **Gap** | No security scanning tools configured. Pipeline has no security validation step. Vulnerabilities in NuGet/npm dependencies and application code can reach production undetected. |
| **Recommendation** | Add dependency vulnerability scanning (e.g., `dotnet list package --vulnerable`, npm audit) as a pipeline stage in `build_v5.yml`. Add SAST scanning (Semgrep, SonarQube, or Amazon CodeGuru Reviewer). Expand Dependabot to cover NuGet and npm ecosystems. Add a security gate that blocks merges on critical findings. |
| **Evidence** | `.github/workflows/build_v5.yml` (no security scanning stages), `.github/dependabot.yml` (devcontainers only), `src/Directory.Build.props` (StyleCop for code quality, not security) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No distributed tracing (OpenTelemetry, X-Ray) with trace ID propagation. The application uses Sentry (v5.16.3) for error reporting and crash tracking. NLog (v5.5.1) with CLEF JSON layout provides structured logging. MiniProfiler (v4.5.4) is configured for development-time request profiling. These provide basic individual service tracing but no cross-service trace propagation. |
| **Gap** | Basic tracing on individual services (Sentry error tracking, NLog structured logging) but no cross-service propagation of trace IDs. No OpenTelemetry or X-Ray instrumentation. |
| **Recommendation** | Add OpenTelemetry SDK for .NET to instrument the application with distributed tracing. Export traces to AWS X-Ray via the OpenTelemetry OTLP exporter. When deployed on EKS, use the AWS Distro for OpenTelemetry (ADOT) collector as a sidecar for telemetry export. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (Sentry v5.16.3, NLog v5.5.1, NLog.Layouts.ClefJsonLayout v1.0.5), `src/NzbDrone.Host/Sonarr.Host.csproj` (MiniProfiler.AspNetCore.Mvc v4.5.4) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions, error budgets, or formal service level metrics found in the repository. No CloudWatch alarms on latency or error rates. The application has internal health checks (`src/NzbDrone.Core/HealthCheck/`) that monitor operational health (download client connectivity, indexer status, disk space, update availability), but these are operational checks, not SLO definitions. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. No error budget tracking. No latency or availability targets. |
| **Recommendation** | Define SLOs for critical user journeys: API response time (p95 < 500ms), RSS sync success rate (> 99%), download processing latency. When deployed on AWS, use CloudWatch ServiceLevelObjective with error budget tracking. The existing health check system provides a foundation for SLO monitoring. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational health checks, not SLOs), `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. The application has internal health checks and operational monitoring (download success/failure, indexer response times stored in the database), but these are not published as structured metrics for external consumption. No CloudWatch `PutMetricData` calls, no Prometheus endpoints, no custom metrics dashboards. |
| **Gap** | No custom metrics — only operational health checks stored in the local database. No business outcome tracking (episodes grabbed, download completion rate, quality upgrades). |
| **Recommendation** | Publish key business metrics to Amazon CloudWatch: episodes grabbed per day, download completion rate, quality upgrade count, indexer response times, API request rates. Use CloudWatch embedded metric format from the application logs for zero-config metric extraction. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (internal health checks), `src/NzbDrone.Core/Instrumentation/` (NLog logging infrastructure) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting infrastructure. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate thresholds. The application has Sentry for error reporting (crash notifications) and internal health checks that show warnings in the UI, but no automated alerting for operational anomalies. |
| **Gap** | No alerting configured. The only notification mechanism is Sentry crash reports and in-app health check warnings visible to the user in the UI. |
| **Recommendation** | When deployed on AWS, configure CloudWatch anomaly detection for API error rates and latency. Create composite alarms for critical path monitoring. Integrate with Amazon SNS for alarm notifications. Use the existing Sentry integration as complementary error tracking alongside CloudWatch. |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (Sentry v5.16.3), `src/NzbDrone.Core/HealthCheck/` (UI health warnings) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Rolling release model via GitHub Releases. The `deploy.yml` workflow packages binaries for all platforms, creates a GitHub Release with auto-generated release notes, and publishes update metadata (version, hashes) to `services.sonarr.tv/v1/update`. Users receive updates through Sonarr's built-in update mechanism. This is a rolling deployment with health checks (the application validates the update before applying), but no canary or blue/green strategy. No traffic shifting. |
| **Gap** | Rolling deployments with basic validation but no staged rollout. All users receive the same update simultaneously. No ability to roll back automatically if the update causes issues (users must manually downgrade). |
| **Recommendation** | When deployed on EKS, implement canary deployments using AWS CodeDeploy or ArgoCD Rollouts. Use Amazon API Gateway canary release features for staged API rollouts. The existing update service at services.sonarr.tv could be enhanced to support percentage-based rollouts. |
| **Evidence** | `.github/workflows/deploy.yml` (GitHub Release + services.sonarr.tv update publishing), `.github/workflows/build_v5.yml` (deploy job gated on all tests passing) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist and run in the CI pipeline. The `NzbDrone.Integration.Test` project contains API-level integration tests covering: Blocklist, Calendar, Command, DiskSpace, DownloadClient, EpisodeFile, Episode, FileSystem, History, Indexer, NamingConfig, Notification, Queue, Release, RootFolder, SeriesEditor, Series, SeriesLookup, and Wanted tests. Tests run on Ubuntu, macOS, and Windows with the actual Sonarr binary (`integration_test` job in `build_v5.yml`). PostgreSQL integration tests run separately against versions 16, 17, and 18. |
| **Gap** | Integration tests cover primary API workflows but may have gaps in edge cases. No contract tests for external service integrations (indexers, download clients). No chaos or resilience testing. |
| **Recommendation** | Add contract tests for external API integrations (indexer Newznab/Torznab API, download client APIs). When decomposed, add inter-service contract testing. Consider adding resilience testing (network failure simulation) for the deployment pipeline. |
| **Evidence** | `src/NzbDrone.Integration.Test/` (18+ test fixture files), `src/NzbDrone.Integration.Test/ApiTests/` (API test suites), `.github/workflows/build_v5.yml` (integration_test job on 3 platforms) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated runbooks or incident response workflows. The `SECURITY.md` provides a vulnerability reporting process (Discord/email to maintainers) but no automated remediation. No Systems Manager Automation documents, no Lambda-based remediation, no self-healing patterns. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation for common failures. |
| **Recommendation** | Create runbooks for common operational scenarios: database corruption recovery (the application already has `DatabaseRestorationService`), disk space exhaustion, download client connectivity failures. When deployed on AWS, use Systems Manager Automation documents for automated remediation. Implement health-check-driven auto-restart in EKS via liveness/readiness probes. |
| **Evidence** | `SECURITY.md` (manual vulnerability reporting), `src/NzbDrone.Core/Datastore/DatabaseRestorationService.cs` (manual restore capability) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file for observability assets. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution. The application's observability is entirely embedded in the application itself (NLog logging, Sentry error tracking, in-app health checks) with no external monitoring infrastructure or ownership model. |
| **Gap** | No observability ownership — monitoring is reactive and embedded in the application. No team attribution, no external dashboards, no alarm ownership. |
| **Recommendation** | When deployed on AWS, create CloudWatch dashboards for each operational domain (API performance, download processing, media management). Assign dashboard and alarm ownership to team members. Define CODEOWNERS for observability configuration files. |
| **Evidence** | No CODEOWNERS file found. No dashboard definitions. No alarm configurations. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging — there are no IaC-defined AWS resources to tag. No tagging standards, no tag enforcement, no cost allocation tags. |
| **Gap** | No tags found on resources. No tagging standard or governance. |
| **Recommendation** | When adopting IaC, define a tagging standard with required tags: `Environment`, `Service`, `Owner`, `CostCenter`, `Application`. Use `default_tags` in Terraform provider or CDK aspects for consistent tagging. Enforce tags via AWS Config `required-tags` rule and Tag Policies in AWS Organizations. |
| **Evidence** | No IaC files found. No tagging configuration in any discovered file. |

---

## Learning Materials

Based on the 4 triggered pathways:

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
| `src/NzbDrone.Core/Sonarr.Core.csproj` | INF-Q2, INF-Q3, INF-Q4, APP-Q1, APP-Q3, DATA-Q3, DATA-Q4, SEC-Q4 | Core project dependencies: Dapper, Npgsql, Polly, FluentMigrator, NLog, KeyDerivation |
| `src/NzbDrone.Common/Sonarr.Common.csproj` | INF-Q2, OPS-Q1, OPS-Q4, SEC-Q1, SEC-Q6 | Common dependencies: SQLite, Sentry, NLog, SharpZipLib |
| `src/NzbDrone.Host/Sonarr.Host.csproj` | INF-Q6, OPS-Q1 | Host project: Swashbuckle, MiniProfiler, DryIoc |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, INF-Q9, SEC-Q2, SEC-Q3, SEC-Q5, APP-Q4, APP-Q5 | Application startup: auth, CORS, Swagger, forwarded headers, single-instance |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | INF-Q2, APP-Q2, APP-Q6, DATA-Q2, DATA-Q4 | Centralized data access layer with Dapper ORM |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | INF-Q2, SEC-Q2 | Database connection factory for SQLite and PostgreSQL |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q4 | 230+ FluentMigrator schema migrations |
| `src/NzbDrone.Core/Datastore/TableMapping.cs` | DATA-Q2 | Entity-to-table mapping configuration |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2 | SQL query builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | DATA-Q2 | PostgreSQL-specific query builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` | DATA-Q2 | SQLite-specific query builder |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | INF-Q4, APP-Q3 | In-process pub/sub with sync/async handlers |
| `src/NzbDrone.Core/Messaging/Events/IHandle.cs` | INF-Q4 | Event handler interfaces |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` | INF-Q3, INF-Q4, APP-Q4 | In-memory command queue with priority |
| `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` | INF-Q3, APP-Q3, APP-Q4 | 3-thread command processing pool |
| `src/NzbDrone.Core/Messaging/Commands/CommandStatus.cs` | APP-Q4 | Command status tracking (Queued, Started, Completed, Failed) |
| `src/NzbDrone.Core/Jobs/TaskManager.cs` | INF-Q3, INF-Q8, APP-Q4 | Scheduled task management with intervals |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Built-in backup/restore with retention |
| `src/NzbDrone.Core/Backup/BackupCommand.cs` | INF-Q8 | Backup command definition |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q3, OPS-Q4 | Internal health check system |
| `src/NzbDrone.Core/Datastore/DatabaseRestorationService.cs` | OPS-Q7 | Database restoration capability |
| `src/NzbDrone.Core/Datastore/LogDatabase.cs` | SEC-Q1 | Separate log database |
| `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key authentication implementation |
| `src/Sonarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | SEC-Q3, SEC-Q4 | Authentication scheme registration |
| `src/Sonarr.Api.V3/openapi.json` | APP-Q5, INF-Q6 | OpenAPI V3 specification |
| `src/Sonarr.Api.V5/openapi.json` | APP-Q5, INF-Q6 | OpenAPI V5 specification |
| `src/Sonarr.Api.V3/` | APP-Q2, APP-Q5, APP-Q6 | V3 API controllers (26+ directories) |
| `src/Sonarr.Api.V5/` | APP-Q2, APP-Q5 | V5 API controllers (25+ directories) |
| `src/NzbDrone.Core/MediaFiles/` | DATA-Q1 | Media file management on filesystem |
| `src/NzbDrone.Core/MediaCover/` | DATA-Q1 | Cover image caching |
| `src/NzbDrone.Core/RootFolders/` | DATA-Q1 | Root folder configuration |
| `.github/workflows/build_v5.yml` | INF-Q1, INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7, DATA-Q3 | Main CI/CD pipeline: build, test, deploy |
| `.github/workflows/deploy.yml` | INF-Q1, INF-Q11, OPS-Q5, SEC-Q5 | Deployment pipeline: package, release, publish |
| `.github/actions/build/action.yml` | INF-Q11 | Composite build action |
| `.github/actions/test/action.yml` | INF-Q11, OPS-Q6, SEC-Q5 | Composite test action with PostgreSQL support |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Dependabot config (devcontainers only) |
| `distribution/docker-build/Dockerfile` | INF-Q1 | Build-time Dockerfile (not runtime) |
| `global.json` | APP-Q1 | .NET SDK version 10.0.201 |
| `package.json` | APP-Q1 | Frontend dependencies: React, TypeScript |
| `src/Directory.Build.props` | APP-Q1, SEC-Q6 | Build configuration: StyleCop, .NET 10 target |
| `src/Sonarr.sln` | APP-Q2 | Solution file (single deployable unit) |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test project |
| `README.md` | Quick Agent Wins | Project documentation |
| `CONTRIBUTING.md` | Quick Agent Wins | Contributing guidelines |
| `SECURITY.md` | OPS-Q7 | Security vulnerability reporting process |
