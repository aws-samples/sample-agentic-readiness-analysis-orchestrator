# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Prowlarr |
| **Date** | 2025-07-15 |
| **TD Version** | 3g1iuew7esd4bia3 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Indexer manager/proxy for the *arr suite. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **1.93 / 4.0** |

**Archetype Justification**: Prowlarr has persistent state (SQLite/PostgreSQL via ConnectionStringFactory.cs), CRUD write endpoints (BasicRepository Insert/Update/Delete), and an HTTP API surface (ASP.NET Core controllers). While it coordinates with downstream *arr apps and indexers, it primarily owns and manages indexer/application state. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.40 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **1.93 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure is undefined or manual. | Blocks reproducible cloud deployments and environment consistency. Foundational blocker for all modernization pathways. |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute — application is a self-hosted desktop binary with no cloud compute definitions. | Prevents elastic scaling, managed patching, and cloud-native deployment patterns. Triggers Move to Containers and Move to Cloud Native pathways. |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent immutable audit logging. Application-level NLog exists but no centralized, immutable audit trail. | Compliance risk and inability to perform forensic analysis after security incidents. |
| 4 | INF-Q2: Managed Databases | 1 | All databases self-managed — embedded SQLite for local installs, user-managed PostgreSQL for advanced setups. No managed AWS database services. | Operational burden for patching, backup, failover, and scaling. Triggers Move to Managed Databases pathway. |
| 5 | OPS-Q5: Deployment Strategy | 1 | No staged deployment strategy — application distributed as zip/tar.gz/installer packages with no blue/green or canary capability. | Regressions reach all users simultaneously with no rollback capability beyond manual re-installation. |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 3 (≥ 2). OpenAPI spec exists at `src/Prowlarr.Api.V1/openapi.json` with Swagger generation configured in `src/NzbDrone.Host/Startup.cs`. Versioned API at `/api/v1/`.
- **What it enables:** An AI agent can discover and invoke Prowlarr API endpoints as tools — managing indexers, triggering searches, checking indexer health, and syncing applications without manual UI interaction.
- **Additional steps:** The OpenAPI spec is already comprehensive. For full agent tool discovery, ensure the spec includes example request/response bodies and parameter descriptions for all endpoints.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (≥ 2). Centralized `BasicRepository<T>` pattern with Dapper ORM provides a clean, well-structured data access layer across all entities.
- **What it enables:** A natural-language-to-SQL agent can query indexer statistics, search history, application sync status, and health check data using the existing schema.
- **Additional steps:** Generate a schema documentation artifact from FluentMigrator migrations. Map entity relationships for the agent to understand join paths.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). Azure Pipelines multi-stage pipeline with build, test, and packaging stages is fully automated.
- **What it enables:** An agent can trigger builds, monitor pipeline status, check test results across platforms (Windows/Mac/Linux/FreeBSD), and manage release packaging via Azure DevOps APIs.
- **Additional steps:** Expose Azure DevOps API credentials to the agent with appropriate scoping. Configure agent permissions for pipeline trigger and artifact access.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, wiki links (wiki.servarr.com), API documentation, and inline code comments.
- **What it enables:** A retrieval-augmented generation agent can index existing documentation, code comments, and wiki content to answer developer questions about Prowlarr architecture, API usage, indexer definition format (Cardigann YML), and contribution guidelines.
- **Additional steps:** Index the wiki.servarr.com content alongside repo documentation. Include the OpenAPI spec in the knowledge base for API-specific queries.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith) + INF-Q1=1, APP-Q3=2, APP-Q4=2 (all supporting triggers met) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (no managed compute) + no Dockerfile/container definitions found. Guard passes: no existing Lambda/Fargate/ECS. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures). SQLite and PostgreSQL are already open source. Microsoft.Data.SqlClient present as a dependency but not used as primary engine. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (all databases self-managed). DATA-Q3=3 (supporting). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads found. Contextual guard prevents trigger — no streaming, ETL, or analytics artifacts detected. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC). OPS-Q5=1 (supporting — no deployment strategy). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context. Context: "Indexer manager/proxy for the *arr suite." — no AI signal terms found. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:**
Prowlarr is a monolithic .NET 8 application (APP-Q2 = 2) deployed as self-hosted platform-specific packages (zip, tar.gz, Windows installer, macOS app). All source projects compile into a single deployable unit via `src/Prowlarr.sln`. The application has identifiable module boundaries (Core, Common, Host, Api.V1, Http, SignalR, platform-specific projects) but shares a single database instance via `BasicRepository<T>`.

**Compute Model Gaps:**
INF-Q1 = 1. No cloud compute infrastructure exists. The application runs on user-managed hardware or community Docker images (hotio/prowlarr) not maintained in this repository.

**Communication Pattern Gaps:**
APP-Q3 = 2. All inter-service communication (with indexers, *arr apps, download clients) is synchronous HTTP. The internal `IEventAggregator` provides in-process pub/sub but no cross-service async messaging.
APP-Q4 = 2. Long-running operations (indexer sync, bulk search, application sync) appear to be handled synchronously with SignalR providing real-time UI updates but without async job patterns like status polling or callbacks.

**Recommended Decomposition Approach:**
See Decomposition Strategy section below. Strangler Fig or Conditional/Adaptive approach recommended given identifiable module boundaries.

**Representative AWS Services:**
- **Compute:** EKS (preferred per preferences), Fargate for serverless containers
- **API:** Amazon API Gateway (preferred) for external API management with throttling and auth
- **Orchestration:** AWS Step Functions for indexer sync workflows
- **Messaging:** Amazon EventBridge (preferred) for indexer state change events to downstream *arr app sync
- **Data:** Aurora PostgreSQL (preferred) for managed database

**Recommended Patterns:**
- Strangler Fig pattern for incremental extraction of indexer proxy and application sync services
- Anti-corruption Layer between new services and legacy monolith data model
- Event Sourcing for indexer state changes to enable decoupled *arr app notifications
- Hexagonal Architecture for each extracted service

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:**
INF-Q1 = 1. No Dockerfile, docker-compose, or Kubernetes manifests exist in this repository. The application is distributed as platform-specific packages (zip, tar.gz, MSI installer, macOS .app). Community Docker images exist (hotio/prowlarr referenced in README badge) but are maintained externally.

**Contextual Guard:** Passes — compute is not already Lambda/Fargate/ECS. There is no cloud compute infrastructure at all.

**Container Readiness Indicators:**
- .NET 8 applications are well-suited for containerization with `mcr.microsoft.com/dotnet/aspnet:8.0` base images
- Application configuration is already externalized via `IConfigFileProvider` and environment variables (e.g., `Prowlarr__Postgres__Host`, `Prowlarr__Postgres__Port`)
- Port binding is configurable (default 9696 per Startup.cs OpenAPI server config)
- CI pipeline already builds platform-specific packages that could serve as container build inputs
- SQLite requires volume mounting for persistence; PostgreSQL mode is already containerization-friendly

**Recommended Container Orchestration:**
EKS (preferred per preferences) with Fargate node groups for operational simplicity. Avoid self-managed Kubernetes per preferences.

**Representative AWS Services:**
- Amazon EKS with Fargate profiles (preferred)
- Amazon ECR for container image registry
- AWS App Runner as a simpler alternative for initial containerization

**Migration Approach:**
1. Create a multi-stage Dockerfile using `mcr.microsoft.com/dotnet/sdk:8.0` for build and `mcr.microsoft.com/dotnet/aspnet:8.0` for runtime
2. Configure PostgreSQL mode (Aurora) instead of embedded SQLite for cloud deployments
3. Externalize all configuration via environment variables (already partially done)
4. Set up ECR repository and integrate image build into Azure Pipelines
5. Deploy to EKS with Helm chart for environment management

**AWS Guidance:**
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
INF-Q2 = 1. Prowlarr uses embedded SQLite for default local installations and user-managed PostgreSQL for advanced setups. Both are self-managed with no automated failover, no managed patching, and no cloud-native backup/recovery.

- SQLite: Embedded via `System.Data.SQLite 2.0.2` and `SourceGear.sqlite3 3.50.4.2`. Stored as local files. No HA, no automatic failover.
- PostgreSQL: Supported via `Npgsql 9.0.3`. Connection configured through environment variables (`Prowlarr__Postgres__Host`, etc.). User-managed PostgreSQL instances with no managed service integration.

**Engine Versions and EOL:**
DATA-Q3 = 3. SQLite version is current. PostgreSQL driver (Npgsql 9.0.3) is current. CI tests run against PostgreSQL 14 and 15. No EOL engines detected but no explicit version pinning for production PostgreSQL.

**Data Access Patterns:**
DATA-Q2 = 4. Centralized `BasicRepository<T>` with Dapper ORM. Clean data access layer will simplify migration — connection string changes in `ConnectionStringFactory.cs` are the primary integration point.

**Recommended Managed Database Target:**
Amazon Aurora PostgreSQL (preferred per preferences). The existing PostgreSQL support in Prowlarr means migration is primarily a connection string change pointing to an Aurora PostgreSQL endpoint.

**Representative AWS Services:**
- Amazon Aurora PostgreSQL-Compatible Edition (preferred) — Multi-AZ, automated backups, automated patching
- Amazon RDS for PostgreSQL — Simpler option if Aurora features are not needed
- Amazon DynamoDB (preferred per preferences) — For specific use cases like indexer health status cache or session data

**Migration Tools:**
- AWS Database Migration Service (DMS) for data migration from self-managed PostgreSQL to Aurora
- ConnectionStringFactory.cs already supports PostgreSQL — update environment variables to point to Aurora endpoint

**AWS Guidance:**
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
INF-Q10 = 1. No Infrastructure as Code exists. Zero IaC coverage — no Terraform, CloudFormation, CDK, Helm charts, or Kustomize files. All infrastructure (when deployed to cloud) would need to be defined from scratch.

INF-Q11 = 3. Azure Pipelines provides comprehensive CI automation with multi-stage build, unit tests, integration tests, automation tests, and packaging. However, there is no cloud deployment automation — the pipeline produces packages but does not deploy to any environment.

OPS-Q5 = 1. No deployment strategy — application distributed as downloadable packages. No blue/green, canary, or rolling deployments.

OPS-Q6 = 4. Strong integration testing — multi-platform (Windows, Mac, Linux, FreeBSD, Alpine), multi-database (SQLite, PostgreSQL 14, PostgreSQL 15), and automation tests.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK (TypeScript/C#) or Terraform for defining EKS clusters, Aurora databases, networking, and supporting infrastructure
- **CI/CD:** Extend Azure Pipelines to include container image build, push to ECR, and deployment to EKS. Alternatively, adopt AWS CodePipeline + CodeBuild for AWS-native pipeline.
- **Deployment:** Helm charts for Kubernetes deployments on EKS with ArgoCD or Flux for GitOps-based deployment
- **Environments:** Use CDK/Terraform to provision staging and production environments with identical configurations

**Representative AWS Services:**
- AWS CDK for infrastructure definition
- AWS CodeBuild / CodePipeline (or continue with Azure Pipelines + AWS integrations)
- Amazon ECR for container images
- AWS CloudFormation for stack management

**Recommended First Steps:**
1. Define cloud infrastructure in CDK/Terraform: VPC, EKS cluster, Aurora PostgreSQL, API Gateway
2. Create Helm chart for Prowlarr deployment on EKS
3. Add container build and ECR push stage to Azure Pipelines
4. Implement blue/green deployment using EKS + ALB target group switching
5. Add deployment stage to pipeline with automated rollback on health check failure

**AWS Guidance:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Decomposition Strategy

APP-Q2 = 2 — Prowlarr is a modular monolith with identifiable module boundaries but a single deployable unit and shared database. Decomposition strategy applies.

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services (e.g., indexer proxy, application sync, notification dispatch) while keeping the monolith running. New features built as services; existing features migrated over time. | Prowlarr's clear project boundaries (Core, Api.V1, Applications, Indexers, Notifications) make this feasible. | **Medium to High** — 6-18 months. Each extraction is bounded. | ✅ **Recommended.** Lowest risk. Extract the indexer proxy layer first (highest fan-out), then application sync service, then notification dispatch. |
| **Conditional / Adaptive** | Containerize Prowlarr as-is first (single Docker image on EKS), then selectively extract high-value services based on scaling needs. Not all modules need to become services. | Best given the current state — no cloud infrastructure exists yet. Containerization provides immediate value before decomposition. | **Low to Medium** — Containerization in 2-4 weeks; selective extraction over 3-12 months. | ✅ **Recommended for initial phase.** Start with containerization (Move to Containers pathway), then extract services incrementally. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch. | Not recommended. Prowlarr has clear modules and active development. | **Very High** — 12-24+ months. High risk. | ⚠️ **Recommended against.** The monolith is functional and well-structured. Strangler Fig is safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's SQLite/PostgreSQL data model. Prevent legacy schema from leaking into new services. | Every extraction — e.g., when extracting indexer proxy service, ACL translates between legacy `IndexerDefinition` table and new service's domain model. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions across services. Currently, operations like "add indexer → sync to all *arr apps → send notification" are a single transaction. | When extracting application sync and notification services — these become distributed operations requiring saga coordination. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture indexer state changes as events rather than current-state-only. Enables decoupled notification to *arr apps. | When extracting the application sync service — indexer state changes become events consumed by multiple downstream services. EventBridge (preferred) as the event bus. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear boundaries between business logic, external interfaces, and infrastructure adapters. | Every new service — ensures testability and portability. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation

| Factor | Signal for Prowlarr | Effort Impact |
|--------|---------------------|---------------|
| Module boundaries | Clear project structure (Core, Common, Host, Api.V1, Http). Well-defined namespaces. | **Low** — boundaries exist and are identifiable. |
| Data coupling | Single shared database via `BasicRepository<T>`. All modules access the same SQLite/PostgreSQL instance. `ConnectionStringFactory.cs` is the single connection point. | **Medium-High** — database separation is the hardest part. Modules share tables. |
| Stored procedures | None (DATA-Q4 = 4). All business logic in C# application layer via FluentMigrator and Dapper. | **Low** — no database-coupled business logic to extract. |
| Communication patterns | All synchronous HTTP (APP-Q3 = 2). Internal `IEventAggregator` for in-process events. | **Medium** — need to introduce async messaging (EventBridge) for cross-service communication. |
| CI/CD maturity | Comprehensive Azure Pipelines with multi-platform build/test (INF-Q11 = 3). | **Low** — strong CI foundation can be extended for multi-service deployment. |
| Test coverage | Integration tests across platforms and databases (OPS-Q6 = 4). | **Low** — strong test coverage reduces regression risk during extraction. |

**Calibrated Estimate:** Start with Conditional/Adaptive approach (2-4 weeks for containerization), then Strangler Fig extraction over 6-12 months. Total: **8-14 months** for initial cloud-native deployment with 2-3 extracted services.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure exists. No Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources. No CloudFormation or CDK stacks. The application is built as platform-specific binaries (Windows x64/x86, macOS x64/arm64, Linux x64/arm/arm64, FreeBSD x64) and distributed as downloadable packages. Community Docker images (hotio/prowlarr) are maintained externally and not part of this repository. |
| **Gap** | All compute is on user-managed hardware — raw desktops, NAS devices, or community-maintained Docker containers. No managed services, no elastic scaling, no managed patching. |
| **Recommendation** | Containerize the application using a multi-stage Dockerfile targeting `mcr.microsoft.com/dotnet/aspnet:8.0`. Deploy to Amazon EKS (preferred) with Fargate profiles for operational simplicity. This enables managed compute with auto-scaling, health checks, and managed patching. |
| **Evidence** | `azure-pipelines.yml` (packaging stages), `src/Directory.Build.props` (RuntimeIdentifiers), `README.md` (Docker badge referencing hotio/prowlarr) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. Default: embedded SQLite via `System.Data.SQLite 2.0.2` and `SourceGear.sqlite3 3.50.4.2` stored as local files. Advanced: user-managed PostgreSQL via `Npgsql 9.0.3` configured through environment variables (`Prowlarr__Postgres__Host`, `Prowlarr__Postgres__Password`). No AWS managed database services (RDS, Aurora, DynamoDB) referenced anywhere. `ConnectionStringFactory.cs` constructs connection strings for both SQLite and PostgreSQL but with no managed service integration. |
| **Gap** | Self-managed databases require manual patching, backup configuration, failover management, and capacity planning. SQLite files have no HA or automatic failover. User-managed PostgreSQL instances lack managed backup, automated patching, and Multi-AZ failover. |
| **Recommendation** | For cloud deployment, migrate to Amazon Aurora PostgreSQL (preferred per preferences). The existing PostgreSQL code path in `ConnectionStringFactory.cs` means migration is primarily a connection string change. Enable Multi-AZ, automated backups with PITR, and automated minor version upgrades. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Common/Prowlarr.Common.csproj` (SQLite/Npgsql packages), `azure-pipelines.yml` (PostgreSQL test variables) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) Multi-step workflows exist: scheduled tasks via `TaskManager.cs`/`Scheduler.cs` in `src/NzbDrone.Core/Jobs/`, indexer sync operations (`ApplicationIndexerSyncCommand`), notification chains, and health check orchestration (`HealthCheckService.cs`). All workflows are implemented as in-code command patterns via `IExecute<TCommand>` with no dedicated workflow orchestration service. The `IEventAggregator` handles in-process pub/sub for event-driven workflow steps. |
| **Gap** | Business-critical multi-step operations (indexer sync to *arr apps, scheduled tasks, notification dispatch) are hardcoded state machines in application code. No visual workflow management, no built-in retry/error handling beyond Polly, no state persistence for long-running workflows. |
| **Recommendation** | For cloud deployment, adopt AWS Step Functions to orchestrate multi-step indexer sync, application sync, and notification workflows. Step Functions provides visual workflow management, built-in retry logic, error handling, and state persistence. Start with the indexer-to-*arr-app sync workflow as the first candidate. |
| **Evidence** | `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs`, `src/NzbDrone.Core/Applications/ApplicationIndexerSyncCommand.cs`, `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | (Archetype: stateful-crud) No managed messaging or streaming infrastructure. No SQS, SNS, EventBridge, Kafka, Kinesis, or Amazon MQ. The internal `IEventAggregator` (`src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`) provides in-process pub/sub for domain events, but this is not cross-service messaging — it operates within the single application process. All communication with external services (indexers, *arr apps, download clients) is synchronous HTTP via `HttpIndexerBase`, `ApplicationBase`, etc. |
| **Gap** | For a stateful-crud service that coordinates state changes across multiple downstream services (*arr apps), the absence of cross-service async messaging creates tight synchronous coupling. Indexer state changes that need to propagate to Sonarr, Radarr, Lidarr, etc. are done via synchronous HTTP — if any downstream app is unavailable, the operation fails or blocks. |
| **Recommendation** | Introduce Amazon EventBridge (preferred per preferences) for indexer state change events. When an indexer is added, updated, or removed, publish an event to EventBridge. Each *arr app integration becomes an EventBridge target with its own error handling and retry logic. This decouples the indexer management lifecycle from downstream sync operations. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Applications/ApplicationService.cs`, `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation defined in IaC (no IaC exists). The application runs as a self-hosted desktop process with Kestrel web server. `Startup.cs` configures forwarded headers for private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7, fe80::/10) suggesting reverse proxy awareness, but no cloud network security is defined. CORS is configured to `AllowAnyOrigin()` on API endpoints. |
| **Gap** | No network isolation, no security groups, no VPC. When deployed to cloud, the application would need complete network security configuration from scratch. The `AllowAnyOrigin()` CORS policy is overly permissive. |
| **Recommendation** | For cloud deployment, define VPC with private subnets for EKS worker nodes and Aurora database. Place API Gateway (preferred) in a public subnet as the entry point. Use security groups with least-privilege rules. Replace `AllowAnyOrigin()` CORS with specific allowed origins. Consider VPC endpoints for AWS service access (ECR, Secrets Manager). |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (forwarded headers config, CORS AllowAnyOrigin) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point. The application exposes its API directly via ASP.NET Core Kestrel web server on port 9696 (per OpenAPI server config in `Startup.cs`). No throttling, no request validation at the gateway level, no centralized auth offloading. Authentication is handled inline by `ApiKeyAuthenticationHandler.cs`. |
| **Gap** | Direct service exposure without a managed entry point lacks throttling, request validation, DDoS protection, and centralized authentication. No TLS termination at a managed layer. |
| **Recommendation** | Deploy Amazon API Gateway (preferred per preferences) as the entry point. Configure API key validation, request throttling, and TLS termination at the gateway level. API Gateway can forward the existing `X-Api-Key` header to the backend. For WebSocket support (SignalR), use API Gateway WebSocket APIs or an ALB with WebSocket support. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (Kestrel configuration, OpenAPI server URL localhost:9696), `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configured. The application is a single-instance desktop process with `SingleInstancePolicy` enforced in code. No ASG, no ECS service desired count, no Lambda concurrency, no DynamoDB auto-scaling. The application explicitly prevents multiple instances from running simultaneously. |
| **Gap** | No ability to respond to traffic spikes or scale down during low demand. Single-instance design means any resource exhaustion affects all users. |
| **Recommendation** | For cloud deployment on EKS, configure Horizontal Pod Autoscaler (HPA) based on CPU/memory utilization and custom metrics (request count, queue depth). Remove `SingleInstancePolicy` for cloud deployments — it's appropriate for desktop but prevents horizontal scaling. Configure Aurora auto-scaling for read replicas if read-heavy. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (EnsureSingleInstance call), `src/NzbDrone.Core/Jobs/` (no scaling-aware scheduling) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Built-in backup functionality exists in `src/NzbDrone.Core/Backup/BackupService.cs`. The service creates zip archives containing the SQLite database file and config.xml with configurable retention periods. Scheduled and manual backups are supported via `BackupCommand`. Restore functionality exists for both zip archives and raw database files. However, this is application-managed backup to local filesystem — no cloud backup, no PITR, no cross-region replication. PostgreSQL mode has no backup mechanism defined in the application. |
| **Gap** | Backups are local filesystem only — no offsite backup, no automated cloud backup, no PITR. PostgreSQL backup is entirely user-managed. No documented restore testing procedures. Backup retention is configurable but not enforced by cloud-native backup services. |
| **Recommendation** | For cloud deployment with Aurora PostgreSQL, leverage Aurora's automated backups with PITR (up to 35-day retention). Configure AWS Backup for cross-region replication of critical data. For application-specific config backup, store backup artifacts in S3 with versioning and lifecycle policies. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, `src/NzbDrone.Core/Backup/BackupCommand.cs`, `src/NzbDrone.Core/Backup/MakeDatabaseBackup.cs` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. `has_deployed_workload` is false — no IaC defines deployable compute, no Dockerfile exists in the repository. The application is distributed as self-hosted platform-specific packages. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository. No Terraform (.tf, .tfvars), CloudFormation, CDK, Helm charts, Kustomize, or Ansible. Zero percent of infrastructure is defined in code. The application is a self-hosted desktop application with no cloud infrastructure to define. |
| **Gap** | No IaC means infrastructure changes are entirely manual (ClickOps). No environment reproducibility, no disaster recovery from code, no infrastructure version control. This is a foundational blocker for all cloud modernization pathways. |
| **Recommendation** | Define cloud infrastructure using AWS CDK (C# supported, aligning with the existing .NET codebase) or Terraform. Start with core infrastructure: VPC, EKS cluster, Aurora PostgreSQL, ECR repository, API Gateway. Store IaC in the same repository or a dedicated infrastructure repository. Target 90%+ IaC coverage from initial cloud deployment. |
| **Evidence** | Repository root directory listing shows no `.tf`, `.tfvars`, `cdk.json`, `template.yaml`, `Chart.yaml`, or `kustomization.yaml` files. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive Azure Pipelines configuration (`azure-pipelines.yml`) with multi-stage pipeline: Setup → Build Backend (Windows/Mac/Linux) → Build Frontend → Installer → Packages → Unit Tests (native + Docker + PostgreSQL 14/15) → Integration Tests (native + Docker + PostgreSQL 14/15 + FreeBSD) → Automation Tests → Analyze (SonarCloud, Frontend Lint, API Docs) → Report Out (Discord notification). GitHub Actions workflows also exist (`.github/workflows/`) for labeling and issue management. Build produces platform-specific packages (zip, tar.gz, MSI installer, macOS app) with Sentry source map uploads. |
| **Gap** | No cloud deployment automation. The pipeline builds and packages artifacts but does not deploy to any environment. No IaC deployment stage (since no IaC exists). No automated rollback capability. The CI is strong but the CD is limited to package distribution. |
| **Recommendation** | Extend the existing Azure Pipelines with deployment stages: container image build → ECR push → EKS deployment via Helm. Add automated rollback on health check failure. Alternatively, add an AWS CodePipeline stage that triggers on ECR image push. |
| **Evidence** | `azure-pipelines.yml`, `.github/workflows/`, `.github/dependabot.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | C# targeting .NET 8 (`net8.0` in `src/Directory.Build.props`), SDK version 8.0.405 (`global.json`). .NET 8 is a current LTS release with first-class AWS SDK coverage and mature cloud-native tooling. ASP.NET Core 8 for the web framework. TypeScript 5.7.2 / React 17.0.2 for the frontend. Key libraries: Dapper 2.1.66, Npgsql 9.0.3, Polly 8.6.4, FluentValidation 9.5.4, Newtonsoft.Json 13.0.4, Swashbuckle 8.1.4. FluentValidation 9.5.4 is older (current is 11.x) but functional. No AWS SDK currently in use, but AWS SDK for .NET v3 has full .NET 8 support. |
| **Gap** | No significant language/framework gap. FluentValidation is several major versions behind (9.5.4 vs 11.x), and React 17.0.2 is behind current (18.x), but these are minor framework updates, not blockers. |
| **Recommendation** | Update FluentValidation to v11.x and React to v18.x when convenient. When adding AWS integration, use the AWS SDK for .NET v3, which fully supports .NET 8. |
| **Evidence** | `global.json`, `src/Directory.Build.props`, `src/NzbDrone.Core/Prowlarr.Core.csproj`, `package.json` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single .NET solution (`src/Prowlarr.sln`) with ~25 projects that compile into one deployable unit. Modular monolith with clear project separation: `NzbDrone.Core` (business logic), `NzbDrone.Common` (shared utilities), `NzbDrone.Host` (web host), `Prowlarr.Api.V1` (API controllers), `Prowlarr.Http` (HTTP framework), `NzbDrone.SignalR` (WebSocket), plus platform-specific projects (Mono, Windows) and test projects. All projects share a single database via `BasicRepository<T>` with `ConnectionStringFactory.cs` as the single connection point. Project references define clear dependency structure with no circular dependencies observed. |
| **Gap** | Single deployable unit with shared database schemas. While module boundaries are clear at the project level, all modules access the same database tables through a shared repository layer. Cannot independently deploy or scale individual components (e.g., indexer proxy vs. application sync). |
| **Recommendation** | Begin decomposition planning using Strangler Fig approach. First candidate for extraction: the indexer proxy/search service (high fan-out to external indexers). Second candidate: the application sync service (coordinates with *arr apps). Use the existing project boundaries as service boundary candidates. See Decomposition Strategy section. |
| **Evidence** | `src/Prowlarr.sln`, `src/NzbDrone.Host/Prowlarr.Host.csproj` (project references), `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) All inter-service communication is synchronous HTTP. Prowlarr communicates with indexers via `HttpIndexerBase` (synchronous HTTP requests), with *arr apps (Sonarr, Radarr, Lidarr, Readarr, Whisparr, Mylar, LazyLibrarian) via synchronous HTTP clients in `src/NzbDrone.Core/Applications/`, and with download clients via synchronous HTTP. The internal `IEventAggregator` provides in-process pub/sub for domain events but is not cross-service async. SignalR provides real-time push to the frontend UI but is not inter-service messaging. |
| **Gap** | For a stateful-crud service managing state that propagates to multiple downstream services, 100% synchronous HTTP communication creates tight coupling. If Sonarr is down during an indexer sync, the sync to Sonarr fails while syncs to other apps may succeed, creating inconsistent state. No async patterns for cross-service state propagation. |
| **Recommendation** | Introduce EventBridge (preferred) for cross-service state change events. Indexer CRUD operations publish events; *arr app integrations consume events asynchronously with independent retry logic. Keep synchronous HTTP for real-time search/query operations where immediate response is needed. Target: 50%+ async for state propagation, sync for queries. |
| **Evidence** | `src/NzbDrone.Core/Applications/` (Sonarr, Radarr, Lidarr, etc. — synchronous HTTP clients), `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs`, `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) Prowlarr has several potentially long-running operations: bulk indexer search across 500+ trackers, application sync to multiple *arr apps, and scheduled indexer health checks. These operations use the command pattern (`IExecute<TCommand>`) and `TaskManager.cs`/`Scheduler.cs` for scheduling, with `SignalR` (`MessageHub`) for real-time UI progress updates. However, the operations themselves appear to execute synchronously within the command handler. Polly (`Polly 8.6.4`) is used for retry policies. No async job queue, no status polling endpoints, no callback patterns detected. |
| **Gap** | Long-running operations (bulk search, multi-app sync) execute synchronously. While SignalR provides UI progress feedback, there is no status polling API for programmatic consumers. If the process fails mid-way, there is no checkpoint/resume capability — the operation must restart from scratch. |
| **Recommendation** | Implement async job patterns for bulk operations: submit a job command that returns a job ID, poll for status via a `/api/v1/jobs/{id}` endpoint. For cloud deployment, offload long-running operations to Step Functions workflows or SQS-backed worker processes. This enables retry at the operation level rather than the entire batch. |
| **Evidence** | `src/NzbDrone.Core/Jobs/TaskManager.cs`, `src/NzbDrone.Core/Jobs/Scheduler.cs`, `src/NzbDrone.Core/Messaging/Commands/`, `src/NzbDrone.SignalR/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Consistent API versioning via URL path pattern. `VersionedApiControllerAttribute.cs` defines the template `api/v{version}/{resource}`, with `V1ApiControllerAttribute` as a convenience for `/api/v1/`. All API controllers in `src/Prowlarr.Api.V1/` use this attribute. OpenAPI spec at `src/Prowlarr.Api.V1/openapi.json` documents the v1 API. Swagger generation is configured in `Startup.cs`. Only v1 exists currently — no v2 or backward compatibility testing across versions. |
| **Gap** | Only one API version exists (v1). No evidence of backward compatibility guarantees, versioning policy documentation, or deprecation procedures. The architecture supports versioning (can add V2 namespace), but it has not been exercised. |
| **Recommendation** | Document the API versioning policy. When breaking changes are needed, create a `Prowlarr.Api.V2` project with `V2ApiControllerAttribute`. Maintain v1 for backward compatibility during a deprecation period. Consider API Gateway (preferred) for version routing in cloud deployment. |
| **Evidence** | `src/Prowlarr.Http/VersionedApiControllerAttribute.cs`, `src/Prowlarr.Api.V1/openapi.json`, `src/NzbDrone.Host/Startup.cs` (SwaggerDoc "v1") |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dynamic service discovery. *Arr app endpoints (Sonarr, Radarr, etc.) are configured manually by users through the Prowlarr UI and stored in the database. Indexer URLs are configured per-indexer definition. PostgreSQL host is configured via environment variable (`Prowlarr__Postgres__Host`). No AWS Service Discovery, no Istio, no Consul. Service endpoints are effectively user-configured through the application's settings. |
| **Gap** | All service endpoints are user-configured and stored in the application database. No dynamic discovery — if a downstream service moves or scales, the user must manually update the configuration. No health-based routing or failover for downstream services. |
| **Recommendation** | For cloud deployment, use Kubernetes service discovery (DNS-based) on EKS for internal services. For *arr app integration, consider AWS Cloud Map for service registration and discovery. For the API entry point, use API Gateway (preferred) as a centralized catalog. |
| **Evidence** | `src/NzbDrone.Core/Applications/` (ApplicationDefinition with user-configured URLs), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (environment variable-based PostgreSQL config) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 or managed object storage integration. Prowlarr primarily stores structured data (indexer configurations, application settings, search history, indexer statistics) in SQLite/PostgreSQL. Torrent files and NZB files are handled as transient downloads passed through to download clients — not stored persistently by Prowlarr. No Textract, Tika, or document parsing libraries. The application does not manage unstructured document collections. |
| **Gap** | No managed object storage for any data. Local filesystem used for application data, backups, and logs. No parsing pipeline for any unstructured data. |
| **Recommendation** | For cloud deployment, store application backups and logs in S3 with appropriate lifecycle policies. If indexer definition files (Cardigann YML) or torrent/NZB files need to be persisted, use S3 as the storage backend. Consider S3 File Gateway if filesystem-dependent code paths need to be preserved during migration. |
| **Evidence** | `src/NzbDrone.Core/Prowlarr.Core.csproj` (no S3 SDK), `src/NzbDrone.Core/Backup/BackupService.cs` (local filesystem backup) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Exemplary centralized data access layer. All database operations go through `BasicRepository<T>` (`src/NzbDrone.Core/Datastore/BasicRepository.cs`) which provides CRUD operations, pagination, bulk operations, and event publishing for data changes. Supporting infrastructure: `SqlBuilder` for query construction, `WhereBuilder`/`WhereBuilderPostgres`/`WhereBuilderSqlite` for database-specific query building, `TableMapping` for ORM configuration, `ConnectionStringFactory` for connection management. Dapper ORM provides the underlying data access with Polly retry policies. Each entity has a dedicated repository (e.g., `IndexerRepository`, `ApplicationRepository`, `AppIndexerMapRepository`). No scattered database imports — all data access is channeled through the repository pattern. |
| **Gap** | None — the data access layer is well-structured with a single point of control for all database operations. |
| **Recommendation** | Maintain the current pattern. When migrating to Aurora PostgreSQL, the `ConnectionStringFactory.cs` is the single integration point to update. Consider adding a thin caching layer (e.g., Amazon ElastiCache for read-heavy indexer lookups) through the repository pattern. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilder.cs`, `src/NzbDrone.Core/Datastore/TableMapping.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | SQLite: Embedded via `SourceGear.sqlite3 3.50.4.2` and `System.Data.SQLite 2.0.2` — both current versions with no EOL concerns. PostgreSQL: Client library `Npgsql 9.0.3` is current. CI pipeline tests against PostgreSQL 14 and 15 (visible in `azure-pipelines.yml` with Docker images `postgres:14` and `postgres:15`). PostgreSQL 14 reaches EOL in November 2026 and PostgreSQL 15 reaches EOL in November 2027 — both within the support window. However, no explicit engine version pinning for production PostgreSQL — the user-managed PostgreSQL version is not validated by the application. A `000_database_engine_version_check.cs` migration exists but its scope is unclear. |
| **Gap** | No explicit version pinning for production PostgreSQL deployments. The application supports whatever PostgreSQL version the user provides. No documented version update procedure covering downtime windows, rollback, or risk acknowledgment. |
| **Recommendation** | For cloud deployment with Aurora PostgreSQL, pin to a specific Aurora PostgreSQL version (e.g., 15.x) in IaC. Document the supported PostgreSQL version range. Enable Aurora auto minor version upgrade for patches. Add a migration-time version check to warn users on unsupported PostgreSQL versions. |
| **Evidence** | `src/NzbDrone.Common/Prowlarr.Common.csproj` (SQLite/Npgsql versions), `azure-pipelines.yml` (postgres:14, postgres:15 in CI), `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic is in the C# application layer. Schema management is handled entirely through FluentMigrator with 43+ migration files in `src/NzbDrone.Core/Datastore/Migration/` — all written in C# code, not raw SQL. The `BasicRepository<T>` uses Dapper for data access with `SqlBuilder` constructing standard SQL queries. `WhereBuilderPostgres` and `WhereBuilderSqlite` handle minor database-specific query differences (parameter syntax) but no proprietary SQL extensions. No `.sql` files containing `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` found anywhere in the repository. |
| **Gap** | None — the application is clean of stored procedures and proprietary SQL, making database migration straightforward. |
| **Recommendation** | Maintain this clean separation. When migrating to Aurora PostgreSQL, no stored procedure extraction or SQL rewriting will be needed. The FluentMigrator migrations will run against Aurora PostgreSQL without modification. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (43+ C# migration files), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Dapper-based queries), `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent immutable audit logging. The application uses NLog for application-level logging with syslog support (`NLog.Targets.Syslog 7.0.0` in both Core and Common csproj). `DatabaseTarget.cs` writes logs to the application database. Authentication events are logged via `AuthenticationService.cs` (login success, failure, logout with IP addresses). Sentry (`Sentry 4.0.2`) is configured for error tracking with source map uploads in CI. However, none of these provide immutable, centralized audit logging suitable for compliance or forensic analysis. |
| **Gap** | No immutable log storage, no centralized audit trail, no log file validation. Application logs are stored in the local database or filesystem — they can be modified or deleted. Auth logs exist but are not tamper-proof. |
| **Recommendation** | For cloud deployment, enable AWS CloudTrail for API-level audit logging. Configure application logs to ship to CloudWatch Logs with a defined retention period. For immutable audit storage, stream critical events (auth, config changes, indexer modifications) to an S3 bucket with Object Lock enabled. |
| **Evidence** | `src/NzbDrone.Common/Prowlarr.Common.csproj` (NLog, Sentry packages), `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/Prowlarr.Http/Authentication/AuthenticationService.cs` (auth logging) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest for the database. SQLite database files are stored unencrypted on the local filesystem. PostgreSQL encryption is user-managed and not enforced by the application. `ProtectionService.cs` provides AES encryption for specific sensitive data fields (download client credentials, indexer API keys) using a `DownloadProtectionKey` stored in application config — this is field-level encryption, not database-level encryption at rest. No KMS integration, no customer-managed keys, no encryption configuration in any data store definition. |
| **Gap** | Database files (SQLite) are unencrypted on disk. Sensitive data fields have application-level AES encryption but the encryption key itself (`DownloadProtectionKey`) is stored in application configuration without key rotation or managed key storage. No database-level encryption at rest. |
| **Recommendation** | For cloud deployment with Aurora PostgreSQL, enable encryption at rest using AWS KMS customer-managed keys. All Aurora storage, backups, and snapshots are automatically encrypted. Migrate the `DownloadProtectionKey` to AWS Secrets Manager with automated rotation. For S3-stored backups, enable server-side encryption with KMS. |
| **Evidence** | `src/NzbDrone.Core/Security/ProtectionService.cs` (AES field-level encryption), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (no encryption parameters in connection strings) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API key authentication implemented via `ApiKeyAuthenticationHandler.cs`. API keys are accepted via `X-Api-Key` header, `apikey` query parameter, or `Authorization: Bearer` header. Forms-based cookie authentication for the web UI (`CookieAuthenticationOptions` configured in `AuthenticationBuilderExtensions.cs`). SignalR authentication via separate API key scheme (`access_token` query parameter). Authentication is mandatory — `Startup.cs` configures a fallback policy requiring authentication on all endpoints except those marked `[AllowAnonymous]`. An `AuthenticationType.None` mode exists for development/testing, and `AuthenticationType.External` for reverse proxy auth delegation. No OAuth2, JWT, or token-based auth with scopes/claims. |
| **Gap** | Static API key authentication without token-based auth (OAuth2/JWT). API keys do not expire, cannot be scoped to specific operations, and have no rotation mechanism. The `apikey` query parameter exposes credentials in URLs and access logs. |
| **Recommendation** | For cloud deployment, implement OAuth2/JWT authentication via Amazon Cognito or API Gateway authorizers. Replace static API keys with short-lived JWT tokens with scoped claims (read-only, admin, indexer-management). Deprecate the `apikey` query parameter to avoid credential exposure in logs. Keep API key as a fallback for backward compatibility during migration. |
| **Evidence** | `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Prowlarr.Http/Authentication/AuthenticationBuilderExtensions.cs`, `src/NzbDrone.Host/Startup.cs` (authorization config) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application manages its own authentication entirely. `AuthenticationService.cs` handles login/logout with `IUserService` for user management. Password hashing uses `Microsoft.AspNetCore.Cryptography.KeyDerivation` (PBKDF2 per migration `024_add_salt_to_users.cs`). Authentication types: Forms (cookie-based), External (reverse proxy delegation), None (development), and API Key. No OIDC/SAML configuration, no Cognito, no Okta, no external IdP federation. Users are stored in the application database. |
| **Gap** | Fully self-managed authentication with no centralized identity provider integration. No SSO, no federated identity, no external IdP. Users must maintain separate credentials for Prowlarr. |
| **Recommendation** | For cloud deployment, integrate with Amazon Cognito as the centralized identity provider. Configure Cognito user pools for user management with optional federation to corporate IdPs (SAML/OIDC). Use Cognito tokens (JWT) for API authentication. This enables SSO across the *arr suite if other apps adopt Cognito. |
| **Evidence** | `src/Prowlarr.Http/Authentication/AuthenticationService.cs`, `src/Prowlarr.Http/Authentication/AuthenticationBuilderExtensions.cs`, `src/NzbDrone.Core/Datastore/Migration/024_add_salt_to_users.cs` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials in source code. PostgreSQL credentials are configured via environment variables (`Prowlarr__Postgres__Host`, `Prowlarr__Postgres__Port`, `Prowlarr__Postgres__User`, `Prowlarr__Postgres__Password` — visible in `azure-pipelines.yml` CI configuration with test values). API keys are stored in the application database. The `DownloadProtectionKey` is stored in application config via `IConfigService`. Sentry auth token is a pipeline variable (`sentryAuthTokenServarr`), not committed to code. GitHub token is a pipeline variable (`githubToken`). No AWS Secrets Manager, no HashiCorp Vault, no encryption of environment variable secrets, no rotation configured. |
| **Gap** | Production credentials are kept in environment variables without encryption or rotation. The `DownloadProtectionKey` (used for AES encryption of sensitive fields) is stored in application configuration without managed key storage. No automated secret rotation for any credential. |
| **Recommendation** | For cloud deployment, migrate all secrets to AWS Secrets Manager: Aurora PostgreSQL credentials (with automated rotation), API keys, `DownloadProtectionKey`, and any external service credentials. Use IAM roles for service accounts on EKS to access Secrets Manager. Configure automated rotation for database credentials using Secrets Manager Lambda rotation functions. |
| **Evidence** | `azure-pipelines.yml` (environment variables for PostgreSQL credentials, pipeline variables for tokens), `src/NzbDrone.Core/Security/ProtectionService.cs` (DownloadProtectionKey usage), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (environment variable-based config) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed patching strategy, no vulnerability scanning, no hardened images. The application is a self-hosted desktop application — compute hardening is the responsibility of the end user. No SSM Patch Manager, no AWS Inspector, no Snyk. No hardened base images (CIS, Bottlerocket). The CI pipeline uses standard Azure Pipelines VM images (`ubuntu-24.04`, `windows-2025`, `macOS-15`) for building but these are build environments, not runtime hardening. |
| **Gap** | No compute hardening or patching strategy for the application runtime. Users run on their own hardware with their own OS patching practices. No container scanning since no container images are built. |
| **Recommendation** | For cloud deployment with EKS, use Bottlerocket OS for EKS nodes (hardened, minimal attack surface). If building container images, use `mcr.microsoft.com/dotnet/aspnet:8.0-alpine` for minimal image size. Enable Amazon ECR image scanning for vulnerability detection on push. Add AWS Inspector for runtime vulnerability assessment on EKS nodes. |
| **Evidence** | `azure-pipelines.yml` (build VM images, no runtime hardening), no Dockerfile (no container scanning) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud analysis is integrated into Azure Pipelines (`SonarCloudPrepare@3` and `SonarCloudAnalyze@3` tasks in the Analyze stage) for static code analysis with code coverage reporting via Cobertura. Dependabot is configured (`.github/dependabot.yml`) but only for the `devcontainers` ecosystem — not for NuGet, npm, or other application dependency ecosystems. No SAST tool beyond SonarCloud. No dependency vulnerability scanning in the pipeline (no `dotnet list package --vulnerable`, no `npm audit`, no Snyk). No container scanning (no container images built). ESLint configured for frontend linting but this is code quality, not security scanning. |
| **Gap** | Dependabot covers only devcontainers, missing NuGet and npm ecosystems. No dedicated dependency vulnerability scanning step in the pipeline. SonarCloud provides some code quality analysis but is not a comprehensive SAST tool. No security gate that blocks the pipeline on critical findings. |
| **Recommendation** | Extend Dependabot configuration to cover `nuget` and `npm` ecosystems. Add `dotnet list package --vulnerable` and `npm audit` steps to Azure Pipelines. Consider adding Snyk or GitHub Advanced Security for comprehensive dependency and code scanning. Configure pipeline gates to fail on critical/high severity vulnerabilities. When containerized, add ECR image scanning to the build pipeline. |
| **Evidence** | `azure-pipelines.yml` (SonarCloud tasks), `.github/dependabot.yml` (devcontainers only), no `npm audit` or `dotnet audit` in pipeline |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No X-Ray SDK, no OpenTelemetry SDK, no Jaeger or Zipkin. The application uses NLog for logging (`NLog 5.4.0` with syslog support and CLEF JSON layout via `NLog.Layouts.ClefJsonLayout 1.0.3`). Sentry (`Sentry 4.0.2`) provides error tracking and crash reporting with source map integration. No trace ID propagation across service boundaries (to indexers, *arr apps, or download clients). |
| **Gap** | No end-to-end tracing across service boundaries. When a search request spans multiple indexers and downstream *arr apps, there is no way to trace the request flow, identify bottlenecks, or diagnose failures across the distributed system. |
| **Recommendation** | For cloud deployment, add OpenTelemetry .NET SDK to instrument the application. Configure X-Ray as the tracing backend. Propagate `traceparent` headers on outbound HTTP requests to indexers and *arr apps. This enables end-to-end visibility of search request flows. Start with auto-instrumentation for ASP.NET Core and HttpClient. |
| **Evidence** | `src/NzbDrone.Common/Prowlarr.Common.csproj` (NLog, Sentry — no OpenTelemetry), `src/NzbDrone.Core/Prowlarr.Core.csproj` (no tracing SDK) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs defined. No formal definition of acceptable service levels for search latency, indexer sync success rate, API availability, or any critical user journey. No error budget tracking. No CloudWatch alarms on p99/p95 latency. The internal health check system (`src/NzbDrone.Core/HealthCheck/`) monitors indexer health status but this is operational health checking, not SLO definition with measurable targets and error budgets. |
| **Gap** | No SLOs means no measurable definition of "good enough" service quality. Cannot prioritize operational improvements or modernization investments based on service level impact. No error budget to balance velocity against reliability. |
| **Recommendation** | Define SLOs for critical user journeys: search latency (p99 < X ms), indexer sync success rate (> 99%), API availability (> 99.9%). For cloud deployment, implement SLO monitoring using CloudWatch metrics with alarms on SLO breach thresholds. Consider CloudWatch ServiceLevelObjective resources. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational health checks, not SLOs), no SLO definition files |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No external business metrics publishing. `IndexerStatisticsService.cs` tracks internal indexer statistics (search counts, grab counts, etc.) stored in the application database. The `HealthCheckService.cs` monitors indexer health. However, no metrics are published to CloudWatch, Prometheus, or any external metrics system. No custom dashboards for business outcomes (successful searches per hour, indexer availability trends, application sync success rates). |
| **Gap** | All metrics are internal to the application database — no external visibility into business outcomes. Operations teams cannot monitor indexer performance trends, search success rates, or application sync health without querying the application database directly. |
| **Recommendation** | For cloud deployment, publish custom CloudWatch metrics for key business outcomes: searches per minute, successful grabs, indexer availability percentage, application sync success/failure rates. Use CloudWatch dashboards for real-time visibility. Consider Amazon Managed Grafana for advanced visualization. |
| **Evidence** | `src/NzbDrone.Core/IndexerStats/IndexerStatisticsService.cs`, `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or external alerting configured. The internal `HealthCheckService.cs` with checks in `src/NzbDrone.Core/HealthCheck/Checks/` monitors indexer health and application status, surfacing issues through the UI and notification system (email, Discord, Telegram, etc. via `src/NzbDrone.Core/Notifications/`). However, this is application-level health monitoring, not infrastructure-level anomaly detection. No CloudWatch alarms, no Datadog, no PagerDuty integration for infrastructure alerting. |
| **Gap** | No infrastructure-level alerting on error rates, latency, or resource utilization. Application-level health checks catch known failure modes but cannot detect novel patterns (gradual degradation, resource exhaustion, unusual traffic patterns). No on-call escalation path for infrastructure issues. |
| **Recommendation** | For cloud deployment, configure CloudWatch anomaly detection on API error rates and latency. Set up composite alarms that aggregate multiple signals (high error rate + high latency = incident). Integrate with PagerDuty or OpsGenie for on-call escalation. The existing notification infrastructure (email, Discord, Telegram) can be complemented with CloudWatch SNS-based alerting. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/Notifications/` (application-level only) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No staged deployment strategy. The application is distributed as downloadable packages (zip, tar.gz, MSI installer, macOS .app) via the Azure Pipelines packaging stage. Users download and install updates manually or via the built-in self-update mechanism (`src/NzbDrone.Update/`). The update mechanism replaces the running binary — no blue/green, no canary, no traffic shifting, no staged rollout. All users get the same version simultaneously when they update. |
| **Gap** | No staged rollout — regressions reach all users simultaneously. No automated rollback capability beyond manually re-installing a previous version. The self-update mechanism is a binary replacement, not a deployment strategy. |
| **Recommendation** | For cloud deployment on EKS, implement canary deployments using Argo Rollouts or Flagger. Configure ALB/API Gateway weighted target groups for gradual traffic shifting (e.g., 5% → 25% → 100%). Add automated rollback on error rate increase during canary. Use Helm for release management with easy version rollback. |
| **Evidence** | `azure-pipelines.yml` (Packages stage), `src/NzbDrone.Update/` (self-update mechanism) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive integration test suite. Azure Pipelines runs integration tests across multiple dimensions: platforms (Windows, Mac, Linux, FreeBSD, Docker Alpine), database backends (SQLite default, PostgreSQL 14, PostgreSQL 15), and test types (unit tests, integration tests, automation tests). `src/NzbDrone.Integration.Test/` contains API tests, CORS tests, HTTP log fixtures, and integration test base classes. `src/NzbDrone.Automation.Test/` contains browser automation tests with screenshot capture on failure. All tests run in the CI pipeline with published results. Tests use real PostgreSQL Docker containers in CI (`docker run postgres:14`, `docker run postgres:15`). |
| **Gap** | None — integration test coverage is excellent, spanning multiple platforms and database backends. This is a strong foundation for safe modernization. |
| **Recommendation** | Maintain this coverage. When containerizing, add container-based integration tests that test the Docker image end-to-end. When deploying to EKS, add smoke tests that run against the deployed environment before promoting traffic. |
| **Evidence** | `azure-pipelines.yml` (Integration and Automation stages), `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Automation.Test/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated incident response. No runbooks (markdown, YAML, or JSON). No SSM Automation documents. No Lambda-based remediation. No self-healing patterns. `SECURITY.md` provides a manual vulnerability reporting process (report via Discord or email to development@servarr.com with 72-hour response commitment). The internal health check system alerts users through the UI but does not trigger automated remediation. |
| **Gap** | Incident response is entirely ad hoc. No documented runbooks for common operational scenarios (database migration failure, indexer connectivity issues, high memory usage). No automated recovery for infrastructure or application failures. |
| **Recommendation** | For cloud deployment, create SSM Automation documents for common operational tasks: database failover, pod restart on OOM, certificate renewal. Implement self-healing patterns: configure EKS liveness/readiness probes based on the existing health check system. Create versioned runbooks in the repository for operational procedures. |
| **Evidence** | `SECURITY.md` (manual process only), `src/NzbDrone.Core/HealthCheck/` (UI alerts only, no automated remediation) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No formal observability ownership. No per-service dashboards, no named alarm owners, no SLO definitions tied to specific teams. No CODEOWNERS file referencing observability assets. The internal health check system provides self-monitoring but there is no team attribution or ownership model. The Sentry integration provides error tracking but without team-level routing or ownership. |
| **Gap** | No observability ownership model. When issues occur, there is no clear escalation path or responsible team for specific components. No dashboard or alarm ownership. |
| **Recommendation** | For cloud deployment, establish observability ownership: create per-component CloudWatch dashboards (indexer service, application sync, API layer) with named team owners. Add CODEOWNERS entries for monitoring configuration. Define on-call rotation and escalation procedures. |
| **Evidence** | No CODEOWNERS file for observability, no SLO definition files, no dashboard definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources to tag — no IaC, no cloud infrastructure. No tagging standards, no tag enforcement, no cost allocation tags. The application has no cloud resource footprint to tag. |
| **Gap** | When cloud infrastructure is created (as recommended by multiple triggered pathways), there is no tagging governance in place. Without tagging standards, cost allocation, ownership tracking, and environment identification will be impossible. |
| **Recommendation** | When creating IaC, define a tagging standard from day one. Required tags: `Environment` (prod/staging/dev), `Service` (prowlarr), `Owner` (team name), `CostCenter`, `ManagedBy` (terraform/cdk). Use `default_tags` in Terraform provider or CDK aspects to enforce tags. Configure AWS Config `required-tags` rule and Tag Policies in AWS Organizations. |
| **Evidence** | No IaC files, no tag definitions |

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
| `global.json` | APP-Q1 | .NET SDK version 8.0.405 |
| `package.json` | APP-Q1 | Frontend dependencies — React 17.0.2, TypeScript 5.7.2 |
| `azure-pipelines.yml` | INF-Q11, INF-Q2, DATA-Q3, SEC-Q5, SEC-Q7, OPS-Q5, OPS-Q6 | Multi-stage CI/CD pipeline, PostgreSQL test configs, SonarCloud analysis |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot configured for devcontainers only |
| `.github/workflows/` | INF-Q11 | GitHub Actions workflows for issue management |
| `src/Directory.Build.props` | APP-Q1, INF-Q1 | Target framework net8.0, RuntimeIdentifiers for multi-platform |
| `src/Prowlarr.sln` | APP-Q2 | Solution file with ~25 projects — single deployable unit |
| `src/NzbDrone.Core/Prowlarr.Core.csproj` | APP-Q1, DATA-Q3, OPS-Q1 | Core project dependencies — Dapper, Npgsql, Polly, FluentMigrator, Microsoft.Data.SqlClient |
| `src/NzbDrone.Common/Prowlarr.Common.csproj` | INF-Q2, DATA-Q3, OPS-Q1 | Common project dependencies — SQLite, Npgsql, Sentry, NLog |
| `src/NzbDrone.Host/Prowlarr.Host.csproj` | APP-Q2 | Host project references all other projects |
| `src/Prowlarr.Api.V1/Prowlarr.Api.V1.csproj` | APP-Q5 | API v1 project with Swashbuckle |
| `src/Prowlarr.Http/Prowlarr.Http.csproj` | SEC-Q3 | HTTP framework project |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, SEC-Q3, APP-Q5 | ASP.NET Core startup — auth, CORS, Swagger, middleware |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2, DATA-Q2, SEC-Q5 | Database connection management — SQLite and PostgreSQL |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | APP-Q2, DATA-Q2 | Centralized repository pattern with Dapper |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2, DATA-Q4 | SQL query construction |
| `src/NzbDrone.Core/Datastore/WhereBuilder.cs` | DATA-Q2 | Query where clause builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | DATA-Q4 | PostgreSQL-specific query building |
| `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` | DATA-Q4 | SQLite-specific query building |
| `src/NzbDrone.Core/Datastore/TableMapping.cs` | DATA-Q2 | ORM table mapping configuration |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 43+ FluentMigrator migration files in C# |
| `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` | DATA-Q3 | Database engine version validation |
| `src/NzbDrone.Core/Datastore/Migration/024_add_salt_to_users.cs` | SEC-Q4 | Password salt migration |
| `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3, INF-Q6 | API key auth handler |
| `src/Prowlarr.Http/Authentication/AuthenticationService.cs` | SEC-Q1, SEC-Q4 | Auth service with login/logout logging |
| `src/Prowlarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | SEC-Q3, SEC-Q4 | Auth scheme registration |
| `src/Prowlarr.Http/VersionedApiControllerAttribute.cs` | APP-Q5 | API versioning attribute — `/api/v{version}/` pattern |
| `src/Prowlarr.Api.V1/openapi.json` | APP-Q5 | OpenAPI v1 specification |
| `src/NzbDrone.Core/Security/ProtectionService.cs` | SEC-Q2, SEC-Q5 | AES field-level encryption for sensitive data |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Built-in backup to local filesystem |
| `src/NzbDrone.Core/Backup/BackupCommand.cs` | INF-Q8 | Backup command definition |
| `src/NzbDrone.Core/Backup/MakeDatabaseBackup.cs` | INF-Q8 | SQLite database backup |
| `src/NzbDrone.Core/Jobs/TaskManager.cs` | INF-Q3, APP-Q4 | Scheduled task management |
| `src/NzbDrone.Core/Jobs/Scheduler.cs` | INF-Q3, APP-Q4 | Task scheduler |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | INF-Q3, INF-Q4, APP-Q3 | In-process event pub/sub |
| `src/NzbDrone.Core/Applications/` | APP-Q2, APP-Q3, APP-Q6 | *Arr app integrations (Sonarr, Radarr, Lidarr, etc.) |
| `src/NzbDrone.Core/Applications/ApplicationIndexerSyncCommand.cs` | INF-Q3 | Indexer sync workflow command |
| `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs` | INF-Q4, APP-Q3 | Synchronous HTTP indexer communication |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q4, OPS-Q7 | Internal health check system |
| `src/NzbDrone.Core/IndexerStats/IndexerStatisticsService.cs` | OPS-Q3 | Internal indexer statistics |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | SEC-Q1 | NLog database target |
| `src/NzbDrone.Core/Notifications/` | OPS-Q4 | Application notification system |
| `src/NzbDrone.Update/` | OPS-Q5 | Self-update mechanism |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test suite |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | Browser automation tests |
| `README.md` | INF-Q1 | Docker badge, project description |
| `CONTRIBUTING.md` | Quick Agent Wins | Developer contribution documentation |
| `SECURITY.md` | OPS-Q7 | Vulnerability reporting process |
