# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | Lidarr |
| **Date** | 2025-07-16 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Music collection manager (*arr suite). |
| **Overall Score** | 1.87 / 4.0 |

**Archetype Justification**: Lidarr uses SQLite/PostgreSQL databases with full CRUD operations on Artists, Albums, Tracks, History, Downloads, and other business entities. The OpenAPI spec exposes extensive POST/PUT/DELETE endpoints alongside reads. The application owns its persistent state — classified as `stateful-crud`.

> **Note**: Although `repo_type` is `monorepo`, Lidarr is effectively a single deployable application with a .NET backend and React frontend sharing a unified database — not multiple independent services. All 37 questions are evaluated against the unified application.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.87 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code — all infrastructure is manually provisioned or absent | Blocks reproducible deployments, environment consistency, and disaster recovery; foundational gap for all modernization pathways |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute — self-hosted desktop/server application with no cloud compute defined | Prevents elastic scaling, increases operational overhead, and limits deployment automation |
| 3 | INF-Q5: Network Security | 1 | No VPC, private subnets, or network segmentation configured | Exposes the application to uncontrolled network access; prerequisite for any cloud deployment |
| 4 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — artifacts packaged for manual distribution with no staged rollout | Releases go directly to users with no canary, blue/green, or rollback mechanism |
| 5 | SEC-Q1: Audit Logging | 1 | No immutable audit logging — application uses NLog file logging only | No forensic capability for security incidents; compliance gap for production workloads |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 3). The repository contains a comprehensive OpenAPI 3.0.4 specification at `src/Lidarr.Api.V1/openapi.json` with 308 KB of endpoint definitions covering Artists, Albums, Tracks, Downloads, Notifications, and more.
- **What it enables:** An AI agent (powered by Amazon Bedrock) that discovers and invokes Lidarr's existing REST API endpoints as tools — enabling natural language queries like "find all albums by Artist X" or "trigger a manual search for missing tracks."
- **Additional steps:** The OpenAPI spec is already well-structured with endpoint descriptions and parameter schemas. Minor enrichment of response descriptions would improve agent accuracy.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 3). Lidarr has a centralized `BasicRepository<T>` pattern with well-defined entity models (Artist, Album, Track, History, etc.) backed by SQLite/PostgreSQL.
- **What it enables:** A natural language to SQL agent that queries the Lidarr database — enabling questions like "which artists have missing albums?" or "show download history for the last week."
- **Additional steps:** Schema documentation would need to be generated from the entity models and migration files. Read-only database access should be enforced for the agent connection.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). Azure Pipelines provides a comprehensive multi-stage pipeline with build, test, package, and analysis stages.
- **What it enables:** An agent that monitors build status, triggers pipeline runs, checks test results, and reports on code analysis findings from SonarCloud.
- **Additional steps:** Azure DevOps API access would need to be configured. The agent would interact with the Azure Pipelines REST API to query build status and trigger operations.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CLA.md`, and the Servarr wiki (referenced in README) provide a documentation corpus.
- **What it enables:** A retrieval-augmented generation agent using Amazon Bedrock that indexes Lidarr documentation, code comments, and API specs to answer developer and user questions about the application.
- **Additional steps:** The wiki content (hosted externally at wiki.servarr.com) would need to be indexed alongside the in-repo documentation. Embedding generation and vector store setup (e.g., Amazon OpenSearch Service with vector engine) required.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolith), INF-Q1 = 1 (no managed compute), APP-Q3 = 2 (limited async) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no managed compute), no container definitions found in repository |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures); SQLite and PostgreSQL are already open-source engines |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (self-managed embedded SQLite/Postgres), DATA-Q3 = 3 (versions pinned but no lifecycle mgmt) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected; no streaming, ETL, or analytics artifacts found |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 3 (integration tests exist) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context ("Music collection manager" contains no AI signal terms) |

---

<!-- PATHWAY_DETAIL_SECTIONS -->

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
Lidarr is a monolithic .NET 8.0 application (APP-Q2 = 2) with identifiable but coupled modules: `NzbDrone.Core` (business logic, data access, messaging), `Lidarr.Api.V1` (REST API controllers), `Lidarr.Http` (web framework/authentication), `NzbDrone.Host` (application host), `NzbDrone.Common` (shared utilities), and `NzbDrone.SignalR` (real-time updates). All modules share a single SQLite or PostgreSQL database with no schema separation between concerns.

**Compute Model Gaps (INF-Q1 = 1):**
No cloud compute is defined. Lidarr is distributed as a self-hosted binary for Windows, macOS, Linux, and FreeBSD. There is no IaC, no container definition, and no serverless function.

**Communication Pattern Gaps (APP-Q3 = 2, APP-Q4 = 3):**
Internal communication uses an in-process `EventAggregator` with synchronous and async handlers. External communication (metadata lookups, download client interactions, notification dispatches) is all synchronous HTTP. The `CommandQueue` pattern provides async processing for long-running operations, which is a good foundation.

**Recommended Decomposition Approach:**
See the **Decomposition Strategy** section below for detailed approach options. The Strangler Fig (Parallel Track) approach is recommended — the existing module boundaries (Download, Notifications, MetadataSource, MediaFiles) provide natural extraction candidates.

**Representative AWS Services (respecting preferences):**
- **Compute:** Amazon EKS (preferred) for containerized services, with API Gateway (preferred) as the entry point
- **Orchestration:** Amazon EventBridge (preferred) for event-driven communication between decomposed services
- **Database:** Amazon Aurora PostgreSQL (preferred) for the primary data store, Amazon DynamoDB (preferred) for high-throughput operational data (download tracking, queue state)
- **Serverless:** AWS Lambda for lightweight notification dispatching and metadata lookup functions

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Saga

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model (INF-Q1 = 1):**
Lidarr is distributed as platform-specific binaries (Windows .exe, macOS .app, Linux/FreeBSD tarballs) built by the Azure Pipelines CI. No Dockerfile, docker-compose.yml, or container manifest exists in the repository. The community Docker image (`linuxserver/lidarr`, referenced in the README badge) is maintained externally.

**Container Readiness Indicators:**
- ✅ Self-contained .NET 8.0 application with well-defined entry point
- ✅ Configuration externalized via environment variables (Postgres connection) and config files
- ✅ Port binding configurable (default 8686)
- ✅ Stateless compute with state in SQLite/Postgres
- ⚠️ Local filesystem dependency for music library access needs volume mount strategy
- ⚠️ SQLite database file needs persistent volume or migration to managed Postgres

**Recommended Container Orchestration Platform (respecting preferences):**
Amazon EKS (preferred) is recommended for container orchestration. Avoid self-managed Kubernetes as specified in preferences. Amazon ECR for container image storage.

**Migration Approach:**
Lift-and-containerize is the fastest path:
1. Create a Dockerfile based on the .NET 8.0 runtime image
2. Externalize all configuration to environment variables
3. Migrate from SQLite to Aurora PostgreSQL (preferred) for production
4. Define Kubernetes manifests or Helm charts for EKS deployment
5. Configure persistent volumes for music library access

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS App Runner (alternative for simpler deployments)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):**
Lidarr uses an embedded SQLite database by default, stored as a file in the application data directory (`lidarr.db`). PostgreSQL is supported as an optional backend, configured via environment variables (`Lidarr__Postgres__Host`, `Lidarr__Postgres__Port`, `Lidarr__Postgres__User`, `Lidarr__Postgres__Password`). When PostgreSQL is used, it is self-managed — the application connects to a user-provisioned PostgreSQL instance.

**Engine Versions and EOL Status (DATA-Q3 = 3):**
- SQLite: `System.Data.SQLite 2.0.2`, `SourceGear.sqlite3 3.50.4.2` — actively maintained, no EOL concern
- PostgreSQL: `Npgsql 9.0.3` — supports PostgreSQL 14+ which is actively maintained through at least Nov 2026

**Data Access Patterns (DATA-Q2 = 3):**
Centralized `BasicRepository<T>` pattern via Dapper ORM. `FluentMigrator` manages schema migrations (90 migration files). The application already supports dual-database (SQLite + PostgreSQL), making the migration to managed PostgreSQL straightforward.

**Recommended Managed Database Target (respecting preferences):**
- **Primary:** Amazon Aurora PostgreSQL (preferred) — the application already has full PostgreSQL support, making this a low-friction migration
- **Caching (future):** Amazon DynamoDB (preferred) for session state and download queue management if decomposed

**Migration Approach:**
1. Deploy Aurora PostgreSQL instance in the target VPC
2. Configure Lidarr's `Lidarr__Postgres__*` environment variables to point to Aurora endpoint
3. Run FluentMigrator to create schema on Aurora
4. Migrate data from SQLite using `pg_dump`/`pg_restore` or DMS
5. Enable Multi-AZ for production; configure automated backups with PITR

**Migration Tools:** AWS Database Migration Service (DMS) for data transfer, though the existing PostgreSQL support in Lidarr makes direct connection the simplest path.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
No infrastructure-as-code exists in the repository. There are no Terraform files, CloudFormation templates, CDK stacks, Helm charts, or any other IaC artifacts. All infrastructure (if any) is manually provisioned.

**Current CI/CD State (INF-Q11 = 3):**
Azure Pipelines provides comprehensive build and test automation:
- Multi-platform builds (Windows, macOS, Linux, FreeBSD)
- Unit tests across all platforms including Docker (Alpine) and PostgreSQL 14/15
- Integration tests on multiple platforms with PostgreSQL backends
- Automation (UI) tests
- SonarCloud analysis for both frontend and backend
- Sentry source map upload
- Artifact packaging for distribution

However, the pipeline produces distribution artifacts (zip, tar.gz, installers) — there is no automated deployment to any infrastructure. Distribution is manual.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No canary, blue/green, or rolling deployment strategy. Artifacts are published for manual download and installation.

**Testing Gaps (OPS-Q6 = 3):**
Integration tests exist and run in CI, which is a strong foundation. The gap is in deployment automation, not testing.

**Recommended DevOps Toolchain (respecting preferences):**
1. **IaC:** AWS CDK (TypeScript or C#) or Terraform for defining EKS clusters, Aurora PostgreSQL, API Gateway, and networking
2. **Container Registry:** Amazon ECR for Docker images
3. **Deployment:** AWS CodePipeline + CodeDeploy for EKS deployments with canary strategy
4. **Monitoring:** Amazon CloudWatch with alarms and dashboards
5. **GitOps (optional):** ArgoCD on EKS for declarative deployments

**Representative AWS Services:** AWS CDK, CodePipeline, CodeBuild, CodeDeploy, CloudFormation, CloudWatch

---

## Decomposition Strategy

> **Conditional Section:** Included because APP-Q2 = 2 (monolith with identifiable modules but shared database and cross-module coupling).

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the Lidarr monolith while keeping it running. Extract modules like Notifications, Download Clients, and Metadata Source as independent services. | ✅ Recommended — Lidarr has identifiable module boundaries (NzbDrone.Core/Notifications, Download, MetadataSource, MediaFiles) that can be extracted incrementally. | **Medium to High** — 6-18 months depending on which modules are extracted. | ✅ **Recommended.** Lowest risk, incremental value delivery. Start with Notifications (most independent) and Download Client management. |
| **Conditional / Adaptive** | Containerize the Lidarr monolith as-is first, then selectively extract high-value services. | ✅ Recommended if capacity is constrained — containerization is the immediate win. | **Low to Medium** — Containerization in 2-4 weeks; selective extraction over 3-12 months. | ✅ **Recommended for quick start.** Containerize first, then decide which modules to extract based on scaling needs. |
| **Big-Bang Rewrite** | Rewrite Lidarr as a suite of microservices from scratch. | Not recommended — the existing codebase is functional with clear module structure. | **Very High** — 12-24+ months. | ⚠️ **Not recommended.** The monolith is well-structured with identifiable boundaries; incremental extraction is safer. |

### Module Extraction Candidates (Priority Order)

1. **Notifications Service** — Most independent module. `NzbDrone.Core/Notifications/` supports 20+ notification providers (Discord, Slack, Email, Plex, etc.). Can be extracted as an EventBridge-triggered Lambda function or EKS service.
2. **Download Client Management** — `NzbDrone.Core/Download/` manages interactions with SABnzbd, NZBGet, torrent clients. Natural service boundary with clear API contracts.
3. **Metadata Source** — `NzbDrone.Core/MetadataSource/SkyHook/` proxies external metadata APIs. Can be a standalone API Gateway + Lambda function with caching.
4. **Media File Processing** — `NzbDrone.Core/MediaFiles/` handles file scanning, organization, and tagging. IO-intensive workload that benefits from independent scaling.

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's data model | Every extraction — translate between monolith and service models | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions for download → process → organize workflows | When extracting Download and MediaFile modules that participate in multi-step workflows | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture state changes as events; leverage existing EventAggregator patterns | When extracting modules that emit events consumed by multiple subscribers | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear ports and adapters | Every new service — ensures testability and infrastructure decoupling | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation

| Factor | Analysis | Signal |
|--------|------------|--------|
| Module boundaries | Clear package structure (Core, Api, Http, Host) with some coupling | Medium effort |
| Data coupling | Single shared SQLite/Postgres database; all modules access same DB | High effort — database decomposition is the hardest part |
| Stored procedures | None (DATA-Q4 = 4) | Low effort — no database logic to extract |
| Communication patterns | Internal EventAggregator provides a foundation for event-driven extraction | Medium effort — EventAggregator patterns map to EventBridge |
| CI/CD maturity | Azure Pipelines with build+test (INF-Q11 = 3) | Medium effort — pipeline exists but needs deployment stages |
| Test coverage | Integration tests exist (OPS-Q6 = 3); SonarCloud analysis | Medium effort — test foundation supports safe extraction |

**Calibrated Estimate:** Using the Conditional/Adaptive approach, containerization can be achieved in **2-4 weeks**. Selective extraction of the first service (Notifications) would take an additional **4-8 weeks**. Full decomposition into 4-5 services would take **9-15 months**.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr is a self-hosted desktop/server application distributed as platform-specific binaries (Windows, macOS, Linux, FreeBSD). No cloud compute resources are defined in the repository — no Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources. No IaC of any kind exists. The Azure Pipelines CI produces distribution artifacts (zip, tar.gz, installers) for manual installation. |
| **Gap** | All compute is on user-managed machines with no managed services. There is no path to elastic scaling, automated patching, or infrastructure automation. |
| **Recommendation** | Containerize the application (Dockerfile) and deploy to Amazon EKS (preferred). Start with a single-container deployment, then progress to managed compute as the architecture evolves. Use AWS App Runner as a simpler alternative for initial cloud deployment. |
| **Evidence** | `azure-pipelines.yml` (packaging stages), absence of any IaC files, absence of Dockerfile |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr uses an embedded SQLite database by default (`src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`) with optional PostgreSQL support via environment variables (`src/NzbDrone.Core/Datastore/PostgresOptions.cs`). Both database engines are self-managed — SQLite is a local file, PostgreSQL requires user-provisioned infrastructure. No `aws_rds_*`, `aws_dynamodb_*`, or other managed database resources exist. |
| **Gap** | All databases are self-managed. SQLite provides no failover, no automated backups (beyond application-level), and no scaling. User-managed PostgreSQL requires manual patching, backup configuration, and capacity planning. |
| **Recommendation** | Migrate to Amazon Aurora PostgreSQL (preferred). The application already has full PostgreSQL support via `Npgsql`, making this a low-friction migration. Configure `Lidarr__Postgres__*` environment variables to point to the Aurora endpoint. Enable Multi-AZ and automated backups. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/PostgresOptions.cs`, `src/NzbDrone.Core/Datastore/DbFactory.cs`, `src/NzbDrone.Common/Lidarr.Common.csproj` (SQLite/Npgsql packages) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr implements workflow orchestration through a custom in-process `CommandQueueManager` (`src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`) and `Scheduler` (`src/NzbDrone.Core/Jobs/Scheduler.cs`). The system supports queued commands with priority, deduplication, and status tracking. Scheduled tasks (refresh artists, RSS sync, health checks, backups) run on configurable intervals via `TaskManager`. This is a structured state machine in code but not a dedicated orchestration service. |
| **Gap** | No dedicated workflow orchestration service (Step Functions, Temporal, Camunda). All orchestration logic is embedded in the application code. The command queue provides structure but lacks visual workflow management, error budgets, and cross-service coordination capabilities. |
| **Recommendation** | When migrating to AWS, extract the scheduled task and command processing logic to AWS Step Functions (for multi-step workflows like download → process → organize) and Amazon EventBridge Scheduler (for periodic tasks like RSS sync and metadata refresh). The existing `CommandQueue` pattern maps well to Step Functions state machine definitions. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr uses an in-process `EventAggregator` (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) for publish-subscribe messaging within the application. Events are dispatched both synchronously (`IHandle<T>`) and asynchronously (`IHandleAsync<T>`) via `TaskFactory`. SignalR (`src/NzbDrone.SignalR/`) provides real-time push updates to the frontend. However, all messaging is in-process — no external message broker (SQS, SNS, EventBridge, Kafka) is used. |
| **Gap** | No managed messaging infrastructure. The in-process EventAggregator cannot survive process restarts, does not support cross-service communication, and provides no message durability. For a `stateful-crud` application, cross-service state propagation via managed messaging is needed when the application is decomposed. |
| **Recommendation** | When decomposing the monolith, replace the in-process EventAggregator with Amazon EventBridge (preferred) for cross-service event routing. The existing event patterns (album grabbed, download completed, track imported) map directly to EventBridge event schemas. Use Amazon SQS for durable command queues replacing the in-process `CommandQueue`. Avoid self-managed Kafka as specified in preferences. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.SignalR/`, `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists in the repository. Lidarr is a self-hosted application that binds to a configurable port (default 8686) on the host machine. Network security is entirely the responsibility of the user. |
| **Gap** | Services deployed without VPC isolation are exposed to uncontrolled network access. No evidence of network security practices in the codebase. |
| **Recommendation** | When migrating to AWS, deploy within a VPC with private subnets for the application and database tiers. Use Amazon API Gateway (preferred) as the public-facing entry point with security groups restricting access. Configure VPC endpoints for AWS service access (S3, SQS, etc.) to keep traffic within the VPC. |
| **Evidence** | Absence of any networking configuration files (no `.tf`, no CloudFormation, no Kubernetes NetworkPolicy) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr uses the built-in ASP.NET Core Kestrel web server (`src/NzbDrone.Host/Lidarr.Host.csproj` references `Microsoft.NET.Sdk.Web`). The application directly exposes its HTTP API on a configurable port. There is no API Gateway, ALB, CloudFront, or any managed entry point providing throttling, authentication offload, or request validation. |
| **Gap** | Direct service exposure lacks throttling, centralized authentication, request validation, and traffic management capabilities that a managed entry point provides. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point for the Lidarr API. Configure throttling, API key validation, and request validation at the gateway level. Use API Gateway's built-in authentication integration with Amazon Cognito for user authentication, replacing the current forms-based auth. |
| **Evidence** | `src/NzbDrone.Host/Lidarr.Host.csproj`, `src/Lidarr.Http/VersionedApiControllerAttribute.cs` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. Lidarr is a single-instance application with no horizontal scaling capability defined in the repository. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or Kubernetes HPA definitions found. |
| **Gap** | No auto-scaling means the application cannot respond to traffic spikes or scale down during low demand. A single instance represents a single point of failure. |
| **Recommendation** | When deployed to EKS (preferred), configure Kubernetes Horizontal Pod Autoscaler (HPA) based on CPU/memory utilization. For Aurora PostgreSQL, enable Aurora Auto Scaling for read replicas. Consider EKS Karpenter for node-level auto-scaling. |
| **Evidence** | Absence of any scaling configuration in the repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr includes a built-in backup system (`src/NzbDrone.Core/Backup/BackupService.cs`) that creates zip archives of the SQLite database and configuration file. Backups are scheduled via `TaskManager` with configurable retention periods (`CleanupOldBackups`). The backup system supports manual, scheduled, and update-triggered backups with configurable backup folder paths. However, this only covers SQLite — PostgreSQL backups are not handled by the application. No PITR, no cross-region replication, no restore testing. |
| **Gap** | Backup exists for SQLite only. No automated backup for PostgreSQL. No point-in-time recovery. No documented restore testing procedures. Backups stored locally — vulnerable to host failure. |
| **Recommendation** | When migrating to Aurora PostgreSQL (preferred), leverage Aurora's automated backups with PITR (up to 35-day retention). Configure AWS Backup for cross-region replication of critical data. Remove the application-level backup for database (Aurora handles it) and retain config backup only. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, `src/NzbDrone.Core/Backup/BackupCommand.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No high availability or fault isolation configuration exists. Lidarr runs as a single instance with a single SQLite database file. Even when using PostgreSQL, there is no Multi-AZ configuration defined in the repository. No load balancer, no replica configuration, no AZ spanning. |
| **Gap** | Single-instance deployment with no fault isolation. An instance failure takes down the entire workload with no automatic recovery. |
| **Recommendation** | Deploy to EKS (preferred) across multiple Availability Zones with at least 2 replicas. Use Aurora PostgreSQL (preferred) with Multi-AZ enabled for database high availability. Configure an Application Load Balancer for traffic distribution across EKS pods. |
| **Evidence** | Absence of any HA configuration; single-instance architecture |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in the repository. No Terraform files (`.tf`), no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize files, no Ansible playbooks. The `build.sh` script handles build orchestration but defines no infrastructure. The `distribution/` directory contains OS-specific packaging (Debian, macOS, Windows) but no IaC. |
| **Gap** | 0% IaC coverage. All infrastructure is manually created (or doesn't exist for cloud). This is the foundational gap — without IaC, no other modernization effort can be automated, reproduced, or disaster-recovered. |
| **Recommendation** | Create IaC as the first modernization step. Use AWS CDK (C# — matching the team's language) or Terraform to define: VPC/networking, EKS cluster, Aurora PostgreSQL, API Gateway, and operational resources (CloudWatch alarms, backup plans). Start with a minimal viable infrastructure and iterate. |
| **Evidence** | Absence of any IaC files; `distribution/` directory contains only OS packaging |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Azure Pipelines (`azure-pipelines.yml`) provides comprehensive CI automation: multi-platform builds (Windows, macOS, Linux), unit tests across 6 platforms, integration tests with SQLite and PostgreSQL (14, 15), automation (UI) tests, SonarCloud analysis for frontend and backend, artifact packaging and publication, and Sentry source map upload. The GitHub Actions CI workflow (`.github/workflows/ci.yml`) is effectively empty (`jobs: {}`). Dependabot is configured only for devcontainers. |
| **Gap** | Strong CI (build + test) but no CD (deploy). The pipeline produces distribution artifacts but does not deploy them to any infrastructure. There are no automated rollback mechanisms. |
| **Recommendation** | Extend the existing Azure Pipelines (or migrate to AWS CodePipeline) to add deployment stages: build container image → push to ECR → deploy to EKS with canary strategy → health check validation → automatic rollback on failure. The strong test foundation (unit, integration, automation) supports safe continuous deployment. |
| **Evidence** | `azure-pipelines.yml` (stages: Setup, Build_Backend, Build_Frontend, Installer, Packages, Unit_Test, Integration, Automation, Analyze, Report_Out), `.github/workflows/ci.yml`, `.github/dependabot.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lidarr is built with C# (.NET 8.0) for the backend and TypeScript/JavaScript (React) for the frontend. The .NET SDK version is pinned at 8.0.405 (`global.json`). The target framework is `net8.0` across all projects (`src/Directory.Build.props`). The frontend uses React 18.3 with TypeScript 5.7 (`package.json`). |
| **Gap** | .NET/C# has good AWS SDK coverage (`AWSSDK.Core` for .NET) but a narrower cloud-native tooling ecosystem compared to Python, TypeScript, Go, or Java. Some AWS services have richer first-party libraries in those languages. |
| **Recommendation** | .NET 8.0 is a strong foundation with good AWS SDK support. Consider using the AWS SDK for .NET for service integrations. For AWS CDK IaC, C# is a supported language — leverage the team's existing C# expertise. |
| **Evidence** | `global.json`, `src/Directory.Build.props`, `package.json`, `src/NzbDrone.Core/Lidarr.Core.csproj` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr is a single deployable monolith with identifiable modules: `NzbDrone.Core` (business logic, data access, messaging, 50+ subdirectories), `Lidarr.Api.V1` (REST API controllers), `Lidarr.Http` (web framework, authentication), `NzbDrone.Host` (application host), `NzbDrone.Common` (shared utilities), `NzbDrone.SignalR` (real-time updates). Module boundaries exist via .NET project references, but all share a single database (SQLite or PostgreSQL). Cross-module dependencies are extensive: `Lidarr.Api.V1` → `Lidarr.Http` → `NzbDrone.Core` → `NzbDrone.Common`. No circular project references detected, but `NzbDrone.Core` is a monolithic core with 50+ feature directories all sharing the same database. |
| **Gap** | Single deployable unit with shared database. Module boundaries are organizational (directories/namespaces) rather than architectural (separate services with separate data stores). The Core project contains tightly coupled concerns: database access, business logic, messaging, scheduling, and external service integration all in one project. |
| **Recommendation** | Begin with the Conditional/Adaptive approach — containerize the monolith as-is, then progressively extract services. The well-defined subdirectories in `NzbDrone.Core` (Download, Notifications, MetadataSource, MediaFiles) provide natural extraction candidates. See the Decomposition Strategy section for detailed guidance. |
| **Evidence** | `src/Lidarr.sln`, `src/Directory.Build.props`, `src/NzbDrone.Core/` (50+ subdirectories), `src/Lidarr.Api.V1/Lidarr.Api.V1.csproj` (project references) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Internal communication uses the `EventAggregator` with both synchronous (`IHandle<T>`) and asynchronous (`IHandleAsync<T>`) handlers. The `CommandQueue` provides async command processing. SignalR enables async push to the frontend. However, all external communication (SkyHook metadata API, download clients, notification services) is synchronous HTTP. The application does not use any external message broker. For a `stateful-crud` archetype, the expected pattern is managed messaging (SQS, SNS, EventBridge) for cross-service state changes. |
| **Gap** | Primarily synchronous HTTP for external communication. While internal async patterns exist via EventAggregator, there is no managed messaging infrastructure for cross-service state propagation. This limits decoupling and resilience when decomposing the monolith. |
| **Recommendation** | When migrating to AWS, introduce Amazon EventBridge (preferred) for event-driven communication between decomposed services. Map the existing EventAggregator event types to EventBridge event schemas. Use SQS for durable work queues (replacing the in-process CommandQueue). |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`, `src/NzbDrone.SignalR/`, `src/NzbDrone.Core/MetadataSource/SkyHook/` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lidarr handles long-running operations asynchronously via the `CommandQueue` system. The `Scheduler` polls for pending tasks every 30 seconds and pushes commands to the queue. Commands like `RefreshArtistCommand`, `RssSyncCommand`, `BackupCommand`, and `RescanFoldersCommand` execute asynchronously in the background. Download processing (`DownloadProcessingService`, `CompletedDownloadService`) runs as background tasks. The API exposes command status via `/api/v1/command` endpoints for polling. |
| **Gap** | Most long-running operations are handled asynchronously, which is good. However, there is no timeout or checkpointing mechanism for commands — a long-running command that fails mid-execution has no resume capability. The scheduler uses a simple timer rather than managed orchestration. |
| **Recommendation** | The existing async command pattern is a strong foundation. When migrating to AWS, map long-running commands to AWS Step Functions for state management, error handling, and timeout control. The command status API already supports the polling pattern needed for async UX. |
| **Evidence** | `src/NzbDrone.Core/Jobs/Scheduler.cs`, `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`, `src/Lidarr.Api.V1/Commands/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lidarr implements URL-path-based API versioning via `VersionedApiControllerAttribute` (`src/Lidarr.Http/VersionedApiControllerAttribute.cs`). All API endpoints use the `/api/v1/` prefix, enforced by the `V1ApiControllerAttribute`. The OpenAPI specification (`src/Lidarr.Api.V1/openapi.json`, 13,102 lines) documents the v1 API comprehensively with Swashbuckle annotations. The versioning strategy is consistent across all endpoints. |
| **Gap** | Versioning is consistently applied across all endpoints (only v1 currently exists). The strategy supports future versions via the parameterized `VersionedApiControllerAttribute(int version, ...)`. Minor gap: no explicit backward compatibility guarantee documentation or deprecation policy. |
| **Recommendation** | The current versioning strategy is solid. When adding new versions, maintain backward compatibility guarantees and implement a deprecation timeline. Document the versioning policy in the API specification. The comprehensive OpenAPI spec is an excellent foundation for API Gateway integration. |
| **Evidence** | `src/Lidarr.Http/VersionedApiControllerAttribute.cs`, `src/Lidarr.Api.V1/openapi.json`, `src/Lidarr.Api.V1/` (all controllers use V1ApiControllerAttribute) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr is a single application with no service discovery mechanism. External service endpoints (SkyHook metadata API, download clients, notification services) are configured via hard-coded base URLs or user-configured settings stored in the database. The metadata service (`NzbDrone.Core/MetadataSource/SkyHook/`) uses a built-in URL. Download client and notification endpoints are user-configured per-instance. |
| **Gap** | No service discovery, service registry, or API catalog. All endpoints are hard-coded or manually configured. If the application is decomposed into microservices, there is no mechanism for dynamic service-to-service routing. |
| **Recommendation** | When deploying to EKS (preferred), leverage Kubernetes Service Discovery for internal service communication. Use Amazon API Gateway (preferred) as a centralized API catalog and entry point. For service mesh capabilities, consider AWS App Mesh or Istio on EKS. |
| **Evidence** | `src/NzbDrone.Core/MetadataSource/SkyHook/`, `src/NzbDrone.Core/Download/Clients/`, `src/NzbDrone.Core/Notifications/` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr stores music files on the local filesystem, managed by `NzbDrone.Core/MediaFiles/`. Media covers and artwork are fetched from remote URLs and cached locally via `NzbDrone.Core/MediaCover/`. Album art is processed with `SixLabors.ImageSharp`. No S3 integration, no cloud object storage, no parsing pipeline (Textract, Tika) exists. All unstructured data is on local file systems. |
| **Gap** | Unstructured data (music files, cover art, metadata) is locked to local file systems, making it inaccessible for cloud-native workloads, AI integration, or distributed access. |
| **Recommendation** | When migrating to AWS, use Amazon S3 for music library storage with S3 File Gateway for filesystem-compatible access (preserving the application's file-based access patterns). Use CloudFront for cover art CDN distribution. Consider Amazon Rekognition for album art analysis and Amazon Transcribe for audio content metadata extraction as future AI enhancements. |
| **Evidence** | `src/NzbDrone.Core/MediaFiles/`, `src/NzbDrone.Core/MediaCover/`, `src/NzbDrone.Core/Lidarr.Core.csproj` (SixLabors.ImageSharp, TagLibSharp-Lidarr) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lidarr uses a centralized data access layer built on the `BasicRepository<T>` pattern (`src/NzbDrone.Core/Datastore/BasicRepository.cs`). All entities (Artists, Albums, Tracks, History, etc.) extend `ModelBase` and are accessed through typed repositories. The `SqlBuilder` (`src/NzbDrone.Core/Datastore/SqlBuilder.cs`) provides consistent query construction. Dapper ORM handles object-relational mapping with `TableMapping` for configuration. Database-specific query builders exist for SQLite (`WhereBuilderSqlite.cs`) and PostgreSQL (`WhereBuilderPostgres.cs`). |
| **Gap** | Mostly centralized, but some specialized queries bypass the repository pattern for performance (pagination, complex joins). The dual-database support (SQLite + PostgreSQL) introduces database-specific code paths that add maintenance complexity. |
| **Recommendation** | The centralized repository pattern is a strong foundation. When migrating to Aurora PostgreSQL (preferred), consolidate to a single database backend and remove the SQLite-specific code paths. Consider adding a caching layer (Amazon ElastiCache or DynamoDB for frequently accessed data like artist metadata). |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs`, `src/NzbDrone.Core/Datastore/TableMapping.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are explicitly pinned in `.csproj` files: `System.Data.SQLite 2.0.2` and `SourceGear.sqlite3 3.50.4.2` (SQLite), `Npgsql 9.0.3` (PostgreSQL client). `FluentMigrator.Runner.SQLite 6.2.0` and `FluentMigrator.Runner.Postgres 6.2.0` manage schema migrations (90 migration files). The Azure Pipelines CI tests against PostgreSQL 14 and 15 — both actively supported (PostgreSQL 14 EOL: Nov 2026, PostgreSQL 15 EOL: Nov 2027). SQLite 3.50.4 is the latest stable release. |
| **Gap** | Versions are pinned and none are at or past EOL. However, there is no documented version-update procedure covering downtime windows, rollback, or risk acknowledgment. PostgreSQL version support is validated in CI only for 14 and 15 — newer versions (16, 17) are not tested. |
| **Recommendation** | Add PostgreSQL 16/17 to the CI test matrix to ensure compatibility with current releases. Document a version-update procedure for database engine upgrades. When using Aurora PostgreSQL, leverage Aurora's managed version upgrade capabilities with maintenance windows. |
| **Evidence** | `src/NzbDrone.Common/Lidarr.Common.csproj` (SQLite packages), `src/NzbDrone.Core/Lidarr.Core.csproj` (Npgsql, FluentMigrator), `azure-pipelines.yml` (Postgres 14/15 test stages) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. All business logic resides in the application layer (C#). Database schema is managed through `FluentMigrator` with 90 C#-based migration files (`src/NzbDrone.Core/Datastore/Migration/`). SQL queries are built programmatically via `SqlBuilder` and Dapper — no raw SQL files exist. The application uses standard SQL compatible with both SQLite and PostgreSQL, avoiding engine-specific features. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements found in any migration or source file. |
| **Gap** | None — this is a best-practice implementation. All business logic is in the application layer, and the database is used purely for data storage. |
| **Recommendation** | Maintain this approach. The absence of stored procedures and proprietary SQL means database migration (e.g., from self-managed PostgreSQL to Aurora) is significantly simpler — no logic extraction required, only data migration. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (90 C# migration files), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Dapper), `src/NzbDrone.Core/Datastore/SqlBuilder.cs` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent immutable audit logging exists. Lidarr uses NLog for application logging (`src/NzbDrone.Core/Instrumentation/`) with targets including file, database (`DatabaseTarget.cs`), and Sentry (`ReconfigureSentry.cs`). Authentication events are logged via `AuthenticationService.cs` (login success/failure, logout, unauthorized access with IP addresses). Log data is stored in a local SQLite/PostgreSQL database (`LogRepository.cs`). |
| **Gap** | No immutable audit logs. Application logs are stored in the same database as application data with no integrity protection. Logs can be modified or deleted. No CloudTrail equivalent for infrastructure-level audit trail. No log file validation or S3 Object Lock for immutability. |
| **Recommendation** | When migrating to AWS, enable CloudTrail for infrastructure audit logging. Configure application logs to ship to Amazon CloudWatch Logs with retention policies. For immutable audit trails, stream critical security events (auth failures, admin actions) to S3 with Object Lock. |
| **Evidence** | `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `src/Lidarr.Http/Authentication/AuthenticationService.cs` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured. The SQLite database is stored as an unencrypted file on the local filesystem. When using PostgreSQL, encryption depends entirely on the user's PostgreSQL configuration — the application does not enforce or configure encryption. No KMS keys, no encryption configuration in any data store definition. |
| **Gap** | No encryption at rest for any data store. Sensitive data (user credentials, API keys, notification service tokens) is stored in plain-text database files. |
| **Recommendation** | When migrating to Aurora PostgreSQL (preferred), encryption at rest is enabled by default with AWS-managed keys. For sensitive data, use customer-managed KMS keys. Configure S3 encryption for any music library or backup storage. Use AWS Secrets Manager for credential storage instead of database-stored API keys. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (SQLite connection string with no encryption), absence of any encryption configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lidarr supports API Key authentication via `ApiKeyAuthenticationHandler` (`src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`). API keys can be provided via `X-Api-Key` header, `apikey` query parameter, or `Authorization: Bearer` header. Forms-based authentication with username/password is supported via `AuthenticationService`. Passwords are hashed using PBKDF2 with HMACSHA512 (`UserService.cs`). Authentication can be optionally disabled (`NoAuthenticationHandler.cs`). |
| **Gap** | API Key authentication without OAuth2/JWT. The API key is a static credential with no expiration, rotation, or scope limitation. No token-based authentication with claims-based authorization. The option to disable authentication entirely (`AuthenticationType.None`) is a security risk. |
| **Recommendation** | When migrating to AWS, integrate Amazon API Gateway (preferred) with Amazon Cognito for OAuth2/JWT-based authentication. Configure JWT validation at the gateway level with user pools and identity pools. Remove the option to disable authentication. Implement API key rotation via AWS Secrets Manager. |
| **Evidence** | `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Lidarr.Http/Authentication/AuthenticationService.cs`, `src/NzbDrone.Core/Authentication/UserService.cs`, `src/Lidarr.Http/Authentication/NoAuthenticationHandler.cs` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Lidarr manages its own authentication entirely. User credentials (username, hashed password, salt) are stored in the application database via `UserRepository` (`src/NzbDrone.Core/Authentication/UserRepository.cs`). Password hashing uses PBKDF2 with HMACSHA512 (10,000 iterations, 128-bit salt). There is no integration with any external identity provider — no OIDC, SAML, SSO, Cognito, Okta, or Active Directory. |
| **Gap** | Standalone authentication with no external IdP integration. This creates inconsistency in multi-application environments and increases the attack surface. No SSO capability. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. This enables SSO across *arr suite applications, OIDC/SAML federation with corporate identity providers, and MFA support. Use API Gateway's Cognito authorizer for seamless integration. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/NzbDrone.Core/Authentication/AuthenticationType.cs` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API keys are auto-generated and stored in the application's `Config.xml` file (`src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`). PostgreSQL credentials are provided via environment variables (`Lidarr__Postgres__Host`, `Lidarr__Postgres__Password`, etc.) as documented in `PostgresOptions.cs`. Notification service credentials (Discord webhooks, email passwords, Plex tokens) are stored in the application database. No dedicated secrets management system (Secrets Manager, Vault) is used. No secrets are hardcoded in source code. |
| **Gap** | Secrets stored in config files and database rather than a dedicated secrets manager. No secret rotation. PostgreSQL password passed as plain-text environment variable. Notification service tokens stored unencrypted in the database. |
| **Recommendation** | Use AWS Secrets Manager for all credentials: database passwords, API keys, notification service tokens. Configure automatic rotation for the Aurora PostgreSQL password. Use EKS Secrets Store CSI driver to inject secrets into pods. Replace config file credential storage with Secrets Manager lookups. |
| **Evidence** | `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Datastore/PostgresOptions.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. Lidarr is a self-hosted application — the user is responsible for OS patching, runtime updates, and vulnerability management. No SSM Patch Manager, AWS Inspector, or vulnerability scanning configuration. No hardened base image references. The application does include a self-update mechanism (`src/NzbDrone.Core/Update/`, `src/NzbDrone.Update/`) for updating the Lidarr binary itself. |
| **Gap** | No patching strategy for the host OS or runtime environment. No vulnerability scanning. The self-update mechanism covers the application binary only, not the underlying infrastructure. |
| **Recommendation** | When containerizing for EKS, use hardened base images (e.g., .NET 8.0 runtime on Alpine or Bottlerocket nodes). Enable Amazon ECR image scanning for container vulnerability detection. Use AWS Systems Manager for node patching. Enable Amazon Inspector for continuous vulnerability analysis. |
| **Evidence** | `src/NzbDrone.Core/Update/`, `src/NzbDrone.Update/`, absence of any patching configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | SonarCloud is integrated into the Azure Pipelines CI for both frontend (`Analyze_Frontend` job) and backend (`Analyze_Backend` job with code coverage). SonarCloud provides SAST capabilities including code smell detection, bug detection, and security hotspot analysis. Code coverage is generated via Cobertura and published to Azure DevOps. Dependabot is configured but only for devcontainers ecosystem — not for NuGet or npm dependencies. No DAST tools. No container scanning (no containers to scan). |
| **Gap** | SonarCloud provides SAST, but dependency vulnerability scanning is missing for the main package ecosystems (NuGet, npm). Dependabot is not configured for NuGet or npm packages. No container image scanning. No security gate that blocks deployment on critical findings. |
| **Recommendation** | Extend Dependabot configuration to cover NuGet and npm ecosystems. Add `dotnet list package --vulnerable` to the CI pipeline for .NET dependency scanning. When containerizing, add ECR image scanning or Snyk container scanning. Configure SonarCloud quality gates to block merges on critical security findings. |
| **Evidence** | `azure-pipelines.yml` (SonarCloudPrepare, SonarCloudAnalyze tasks), `.github/dependabot.yml` (devcontainers only), `src/Directory.Build.props` (StyleCop.Analyzers) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, X-Ray instrumentation, or trace ID propagation found in any dependency manifest or source code. Sentry (`Sentry 4.0.2` in `Lidarr.Common.csproj`) is present for error reporting and crash tracking (`ReconfigureSentry.cs`), but Sentry is not a distributed tracing solution — it captures exceptions, not request traces. NLog provides structured logging but no trace context propagation. |
| **Gap** | No distributed tracing capability. When decomposed into microservices, debugging cross-service failures will be guesswork without end-to-end trace propagation. |
| **Recommendation** | Add OpenTelemetry SDK for .NET to instrument the application. When deploying to AWS, configure the OpenTelemetry Collector to export traces to AWS X-Ray. This provides end-to-end visibility across service boundaries when the monolith is decomposed. Start with auto-instrumentation for HTTP and database calls. |
| **Evidence** | `src/NzbDrone.Common/Lidarr.Common.csproj` (Sentry package), `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, absence of OpenTelemetry/X-Ray in any dependency |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. Lidarr has a `HealthCheck` system (`src/NzbDrone.Core/HealthCheck/`) that monitors internal service health (disk space, indexer connectivity, download client status, metadata service availability), but these are operational health checks, not SLO definitions with targets, error budgets, or monitoring. No p99/p95 latency targets, no availability targets, no error budget tracking. |
| **Gap** | No formal SLO definitions. The health check system provides basic operational awareness but does not define acceptable service levels or track against targets. |
| **Recommendation** | Define SLOs for critical user journeys: API response latency (p95 < 500ms), search availability (99.5%), download processing success rate (99%). When deployed to AWS, use CloudWatch Composite Alarms for SLO monitoring and Amazon CloudWatch SLO (if available) or custom dashboards for error budget tracking. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational health checks only), absence of any SLO definition files |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. Lidarr uses NLog for application logging (`src/NzbDrone.Core/Instrumentation/`) and Sentry for error tracking, but does not emit structured business outcome metrics (e.g., albums downloaded, search success rate, notification delivery rate, library scan duration). The application tracks some internal statistics (`src/NzbDrone.Core/ArtistStats/`) but these are for UI display, not observability metric publication. |
| **Gap** | No business metrics. Only infrastructure-level logging exists. Without business metrics, it's impossible to measure whether the application is delivering value to users or to make data-driven modernization decisions. |
| **Recommendation** | Instrument key business metrics using Amazon CloudWatch custom metrics or OpenTelemetry metrics: downloads per hour, search success/failure rate, indexer response times, notification delivery success, library scan completion time. Create CloudWatch dashboards for these metrics. |
| **Evidence** | `src/NzbDrone.Core/Instrumentation/`, `src/NzbDrone.Core/ArtistStats/`, absence of any metric publishing code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration exists in the repository. The health check system provides internal checks with warning/error states, but these are displayed in the application UI, not forwarded to an external alerting system. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no composite alarms. Notifications (Discord, Slack, Email, etc.) are for application events (download completed, album imported) — not operational alerts. |
| **Gap** | No alerting infrastructure. Operational issues are only visible through the application UI, requiring someone to actively check the health page. No proactive notification of degradation or failures. |
| **Recommendation** | When deployed to AWS, configure CloudWatch Alarms for key metrics: API error rate > 5%, API latency p99 > 2s, database connection failures, disk space low. Enable CloudWatch Anomaly Detection for baseline-driven alerting. Integrate with Amazon SNS for alarm notifications and PagerDuty/OpsGenie for on-call management. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (UI-only health checks), `src/NzbDrone.Core/Notifications/` (application event notifications, not operational alerts) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. Azure Pipelines produces distribution artifacts (zip, tar.gz, installers, Sentry source maps) that are published as pipeline artifacts. The application includes a self-update mechanism (`src/NzbDrone.Update/`) for in-place binary updates. There is no canary, blue/green, or rolling deployment. Users download and install updates manually or via the built-in updater. Docker images are maintained by a third party (linuxserver/lidarr). |
| **Gap** | No staged deployment strategy. Updates go directly to users with no traffic shifting, canary analysis, or rollback mechanism beyond the self-update's previous version backup. |
| **Recommendation** | When deploying to EKS (preferred), implement a canary deployment strategy using AWS CodeDeploy or Argo Rollouts. Configure health check validation gates before promoting new versions. Use API Gateway canary releases for API changes. The existing integration and automation tests provide the confidence needed for automated rollouts. |
| **Evidence** | `azure-pipelines.yml` (Packages stage — artifact creation only), `src/NzbDrone.Update/`, absence of any deployment configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist in `src/NzbDrone.Integration.Test/` covering 15+ API test fixtures (ArtistFixture, AlbumFixture, CommandFixture, DownloadClientFixture, HistoryFixture, IndexerFixture, etc.). Tests run in the Azure Pipelines `Integration` stage across multiple platforms (Windows, macOS, Linux, FreeBSD, Docker Alpine) and with PostgreSQL 14 and 15 backends. Automation (UI) tests exist in `src/NzbDrone.Automation.Test/` and run on all three major platforms. |
| **Gap** | Integration tests cover primary API workflows but may not cover all edge cases. Tests run against a locally launched application instance rather than a deployed cloud environment. No contract testing between services (not yet decomposed). |
| **Recommendation** | Maintain and expand the integration test suite. When deploying to AWS, add integration tests that run against the deployed environment (smoke tests post-deployment). Add contract tests when services are extracted from the monolith. The existing comprehensive test infrastructure is a strong asset for safe modernization. |
| **Evidence** | `src/NzbDrone.Integration.Test/` (15+ API test fixtures), `src/NzbDrone.Automation.Test/`, `azure-pipelines.yml` (Integration and Automation stages) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks exist. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The health check system provides self-detection of some issues but no automated remediation. No runbook files (markdown, YAML, JSON) found. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failures. No automated remediation for known issues. |
| **Recommendation** | Create runbooks for common operational scenarios: database connection failures, disk space exhaustion, download client disconnection, metadata service unavailability. When deployed to AWS, implement Systems Manager Automation documents for common remediation actions (restart service, scale up, failover). Use EventBridge rules to trigger automated responses to CloudWatch alarm state changes. |
| **Evidence** | Absence of any runbook or incident response files; `src/NzbDrone.Core/HealthCheck/` (detection only, no remediation) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file referencing observability assets. No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. The health check system is generic with no ownership mapping. |
| **Gap** | No observability ownership structure. Monitoring gaps will emerge when the application is cloud-deployed with no clear responsibility for dashboard maintenance and alarm response. |
| **Recommendation** | Create a CODEOWNERS file with ownership for observability configurations. Define per-service CloudWatch dashboards with team attribution when decomposing. Tag CloudWatch alarms and dashboards with owner metadata. Establish on-call rotations with PagerDuty or OpsGenie integration. |
| **Evidence** | Absence of CODEOWNERS file, absence of any observability ownership configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging governance exists. No IaC means no tags are defined on any AWS resources (because no AWS resources exist). No tagging standard, no tag enforcement, no cost allocation tags. The Azure Pipelines CI does not define any tagging for build artifacts beyond version naming. |
| **Gap** | No tagging standard or enforcement. When AWS resources are created, there will be no cost allocation, ownership tracking, or environment identification without establishing tagging governance first. |
| **Recommendation** | Define a tagging standard before creating any AWS infrastructure. Minimum required tags: `Environment` (dev/staging/prod), `Service` (lidarr), `Team` (owner), `CostCenter`, `ManagedBy` (terraform/cdk). Enforce tags via AWS CDK required-tags construct or Terraform `default_tags`. Enable AWS Config rules for tag compliance. Activate cost allocation tags in AWS Billing. |
| **Evidence** | Absence of any IaC or tagging configuration |

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
| `azure-pipelines.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7, DATA-Q3 | Comprehensive CI pipeline with build, test, analyze stages across multiple platforms |
| `.github/workflows/ci.yml` | INF-Q11 | Empty GitHub Actions workflow (no jobs defined) |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot configured only for devcontainers ecosystem |
| `global.json` | APP-Q1 | .NET SDK version pinned at 8.0.405 |
| `package.json` | APP-Q1 | Frontend dependencies — React 18.3, TypeScript 5.7, SignalR client |
| `src/Directory.Build.props` | APP-Q1, APP-Q2, SEC-Q7 | Build configuration — .NET 8.0 target, StyleCop analyzers, multi-platform support |
| `src/NzbDrone.Core/Lidarr.Core.csproj` | INF-Q2, APP-Q1, DATA-Q1, DATA-Q3 | Core project dependencies — Dapper, Npgsql, FluentMigrator, ImageSharp, Polly |
| `src/NzbDrone.Common/Lidarr.Common.csproj` | INF-Q2, OPS-Q1, DATA-Q3 | Common project dependencies — SQLite, Sentry, NLog |
| `src/Lidarr.Api.V1/Lidarr.Api.V1.csproj` | APP-Q2 | API project references showing monolith coupling |
| `src/NzbDrone.Host/Lidarr.Host.csproj` | INF-Q6 | Application host — ASP.NET Core Web SDK, Swashbuckle |
| `src/Lidarr.Api.V1/openapi.json` | APP-Q5, Quick Agent Wins | OpenAPI 3.0.4 specification (308 KB, 13,102 lines) |
| `src/Lidarr.Http/VersionedApiControllerAttribute.cs` | APP-Q5, INF-Q6 | URL-path-based API versioning (`/api/v{version}/`) |
| `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API Key auth via header, query param, or Bearer token |
| `src/Lidarr.Http/Authentication/AuthenticationService.cs` | SEC-Q1, SEC-Q3 | Forms-based auth with login/logout and IP logging |
| `src/Lidarr.Http/Authentication/NoAuthenticationHandler.cs` | SEC-Q3 | Optional no-auth mode |
| `src/NzbDrone.Core/Authentication/UserService.cs` | SEC-Q4 | Internal user management with PBKDF2 password hashing |
| `src/NzbDrone.Core/Authentication/UserRepository.cs` | SEC-Q4 | Database-backed user credential storage |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | DATA-Q2, DATA-Q4 | Centralized repository pattern with Dapper ORM |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2, SEC-Q2, SEC-Q5 | SQLite and PostgreSQL connection string construction |
| `src/NzbDrone.Core/Datastore/PostgresOptions.cs` | INF-Q2, SEC-Q5 | PostgreSQL configuration via environment variables |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | INF-Q2 | Database factory with SQLite and PostgreSQL support |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2, DATA-Q4 | Programmatic SQL query construction |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | DATA-Q2 | PostgreSQL-specific WHERE clause builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` | DATA-Q2 | SQLite-specific WHERE clause builder |
| `src/NzbDrone.Core/Datastore/TableMapping.cs` | DATA-Q2 | ORM table mapping configuration |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 90 FluentMigrator C# migration files |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | INF-Q4, APP-Q3 | In-process event aggregator with sync/async handlers |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs` | INF-Q3, APP-Q4 | In-process command queue with priority and deduplication |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` | INF-Q4 | Blocking collection-based command queue |
| `src/NzbDrone.Core/Jobs/Scheduler.cs` | INF-Q3, APP-Q4 | Timer-based job scheduler (30-second polling) |
| `src/NzbDrone.Core/Jobs/TaskManager.cs` | INF-Q3, INF-Q8, APP-Q4 | Scheduled task management with default task definitions |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Built-in backup system with SQLite database and config backup |
| `src/NzbDrone.Core/Backup/BackupCommand.cs` | INF-Q8 | Backup command definition |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q4 | Operational health check system (UI display, no alerting) |
| `src/NzbDrone.Core/Instrumentation/` | SEC-Q1, OPS-Q1, OPS-Q3 | NLog-based logging infrastructure |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | OPS-Q1 | Sentry error tracking configuration |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | SEC-Q5 | API key generation and config file management |
| `src/NzbDrone.Core/MetadataSource/SkyHook/` | APP-Q6 | Hard-coded metadata service endpoint |
| `src/NzbDrone.Core/Download/Clients/` | APP-Q6 | User-configured download client endpoints |
| `src/NzbDrone.Core/Notifications/` | APP-Q6, OPS-Q4 | 20+ notification provider integrations |
| `src/NzbDrone.Core/MediaFiles/` | DATA-Q1 | Local filesystem media file management |
| `src/NzbDrone.Core/MediaCover/` | DATA-Q1 | Remote cover art fetching and local caching |
| `src/NzbDrone.SignalR/` | APP-Q3, INF-Q4 | Real-time push updates to frontend |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | 15+ API integration test fixtures |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | UI automation tests |
| `src/NzbDrone.Core/Update/` | SEC-Q6, OPS-Q5 | Application self-update mechanism |
| `distribution/` | INF-Q10 | OS-specific packaging (Debian, macOS, Windows) |
| `README.md` | Quick Agent Wins | Project documentation and feature description |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
| `SECURITY.md` | Quick Agent Wins | Security policy documentation |
