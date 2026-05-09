# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Prowlarr--Prowlarr |
| **Date** | 2025-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Indexer manager/proxy for the *arr suite. |
| **Overall Score** | 1.76 / 4.0 |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |

**Archetype Justification**: The application owns persistent state (SQLite/PostgreSQL databases), exposes CRUD APIs for indexers, applications, notifications, and history entities, and manages entity lifecycles (add/update/delete indexers). Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.18 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.76 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+2+1+1+1+1+1+1+1+2) / 11 = 13/11 = 1.18
- APP: (4+1+2+2+3+2) / 6 = 14/6 = 2.33
- DATA: (2+3+2+4) / 4 = 11/4 = 2.75
- SEC: (1+1+2+1+2+1+2) / 7 = 10/7 = 1.43
- OPS: (1+1+1+1+1+2+1+1+1) / 9 = 10/9 = 1.11
- Overall: (1.18 + 2.33 + 2.75 + 1.43 + 1.11) / 5 = 8.80/5 = 1.76

---

## Classification

**Tier: 🟠 Remediation Required**

**Classification Rationale:** This repository has 9 High findings, 24 Medium findings, and 2 Low findings. The matched rule is "2-11 High → Remediation Required." Note: MOD classification is deliberately softer than ARA on "1 High" — ARA gates on agent safety where a single High is a deployment blocker, while MOD measures modernization maturity where a single High is typically one modernization gap. This repository has 9 High findings across INF, APP, SEC, and OPS categories, indicating significant modernization gaps across infrastructure, application architecture, security, and operational practices.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute — application is distributed as platform-specific archives with no containerization or cloud compute | Prevents elastic scaling, automated deployment, and operational efficiency |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure is outside the repository | Non-reproducible infrastructure, manual provisioning, no disaster recovery automation |
| 3 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumented — no OpenTelemetry, X-Ray, or trace propagation | Cannot debug performance issues or trace request flows through the system |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent cloud audit logging | No forensic capability, no compliance audit trail for administrative actions |
| 5 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith with single deployable unit and shared database | Limits independent scaling, deployment velocity, and team autonomy |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (README.md, wiki content, extensive code comments, health check descriptions, OpenAPI spec at `src/Prowlarr.Api.V1/openapi.json`)
- **What it enables:** A knowledge agent that indexes the OpenAPI spec, health check descriptions, and README to answer developer questions about the Prowlarr API, configuration options, and troubleshooting steps
- **Additional steps:** OpenAPI spec already exists; would need indexing infrastructure (vector DB) and a retrieval agent framework
- **Effort:** Medium

### API-aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 3) — versioned REST API at `/api/v1/` with OpenAPI 3.0.4 specification
- **What it enables:** An agent that discovers and invokes Prowlarr API endpoints as tools (e.g., managing indexers, triggering searches, checking health status programmatically)
- **Additional steps:** OpenAPI spec exists and is comprehensive; agent can call endpoints directly once authentication (API key) is configured
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2) — comprehensive Azure DevOps pipeline with multi-platform builds and tests
- **What it enables:** An agent that triggers builds, checks test results, and monitors pipeline status across the 10+ platform matrix
- **Additional steps:** Azure DevOps API access would need to be configured for agent integration
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed SQLite/PostgreSQL), DATA-Q3=2 |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; INF-Q4 score reflects correct absence of messaging for this stateful-crud archetype |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=1, OPS-Q6=2 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Prowlarr is a tightly-coupled monolith (APP-Q2=1) deployed as a single binary with an embedded web server, self-update mechanism, and single-instance enforcement. All business logic (indexer management, search, notifications, downloads, health checks) is bundled in one deployable unit.

**Compute Model Gaps:** No managed compute at all (INF-Q1=1). The application is distributed as platform-specific archives and Windows installers — not containerized, not on any cloud compute service.

**Communication Pattern Gaps:** Inter-module communication is all in-process (APP-Q3=2). Some async patterns exist internally (SignalR for real-time updates, background jobs via a task scheduler) but no cross-service async communication.

**Recommended Decomposition Approach:** See Decomposition Strategy section below.

**Representative AWS Services (respecting preferences: prefer EKS, Aurora, DynamoDB, API Gateway, EventBridge, Bedrock; avoid self-managed-kafka, self-managed-kubernetes, oracle, lambda):**
- Amazon EKS for container orchestration
- Amazon API Gateway for API entry point
- Amazon EventBridge for event-driven communication between extracted services
- Amazon Aurora PostgreSQL for managed database

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Application is built for 10+ platform/architecture combinations (win-x64, linux-x64, linux-arm64, osx-arm64, etc.) and distributed as self-contained .NET 8 archives. No Dockerfile, docker-compose, or container orchestration manifests exist.

**Container Readiness Indicators:**
- .NET 8.0 runtime supports container deployment natively
- Application already uses environment variables for configuration override (`Prowlarr__` prefix)
- ASP.NET Core's Kestrel web server is container-friendly
- Application listens on configurable port (default 9696)
- Health check endpoints exist at `/api/v1/health`

**Recommended Container Orchestration Platform:** Amazon EKS (per preferences). The application's multi-platform build matrix suggests familiarity with cross-platform deployment, making containerization a natural fit.

**Representative AWS Services:**
- Amazon EKS (preferred) for container orchestration
- Amazon ECR for container image registry
- AWS App Runner as an alternative for simpler deployment model

**Migration Approach:** Lift-and-containerize first (create Dockerfile for the existing monolith), then refactor for EKS deployment with proper health checks, graceful shutdown, and externalized configuration.

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** The application uses SQLite as the default embedded database and optionally supports PostgreSQL. Both are self-managed — SQLite is an embedded file, and PostgreSQL (when used) requires the user to provision and manage their own instance. No managed database service (RDS, Aurora, DynamoDB) is referenced anywhere in the codebase.

**Engine Versions and EOL Status:** The application tests against PostgreSQL 14 and 15 in CI. No explicit engine version pinning in deployment configuration. SQLite version is determined by the .NET runtime package.

**Data Access Patterns:** Centralized via a Datastore layer using Dapper (micro-ORM) with a repository pattern (`BasicRepository`). Schema migrations managed through FluentMigrator with 44 versioned migrations.

**Recommended Managed Database Targets (respecting preferences):**
- Amazon Aurora PostgreSQL (preferred) — the application already has full PostgreSQL support with Npgsql driver
- Amazon DynamoDB (preferred) — for specific use cases like indexer status caching or session data if services are decomposed

**Representative AWS Services:**
- Amazon Aurora PostgreSQL — direct migration path from existing PostgreSQL support
- AWS Database Migration Service (DMS) — for data migration from self-managed PostgreSQL

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** No infrastructure-as-code exists in the repository (INF-Q10=1). All infrastructure provisioning is outside the repository scope.

**Current CI/CD State:** Azure DevOps Pipelines provides comprehensive build and test automation (10 stages, multi-platform matrix builds, PostgreSQL integration tests, SonarCloud analysis). However, there is no deployment automation — builds produce archives/installers but deployment is manual. GitHub Actions workflows exist but only for labeling and issue management.

**Deployment Strategy Gaps:** No deployment strategy exists (OPS-Q5=1). The application uses a self-update mechanism rather than CI/CD-driven deployment. No blue/green, canary, or rolling deployments.

**Testing Gaps:** Integration tests exist for core functionality (OPS-Q6=2) but are not comprehensive across all critical workflows. Unit tests cover core logic across all platforms.

**Recommended DevOps Toolchain (respecting preferences):**
- AWS CDK or Terraform for IaC (EKS cluster, Aurora, networking)
- AWS CodePipeline + CodeBuild for CI/CD (or continue Azure DevOps with AWS deployment targets)
- AWS CodeDeploy with EKS for blue/green deployments
- Amazon ECR for container image lifecycle

---

## Decomposition Strategy

### Recommended Approach: Strangler Fig (Parallel Track)

**Rationale:** APP-Q2=1 indicates a tightly-coupled monolith, but the internal structure has identifiable modules (Indexers, Applications, Notifications, Downloads, History, Authentication, Health Checks). The Dapper-based Datastore layer and repository pattern provide natural seams for extraction.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Internal modules are identifiable (Indexers, Notifications, History). Team can sustain parallel development. | Medium to High | ✅ **Recommended.** Extract high-value services incrementally while keeping the monolith running. |
| **Conditional / Adaptive** | Containerize first, then selectively extract only the modules that need independent scaling (e.g., Indexer search). | Low to Medium | ✅ **Recommended when capacity is constrained.** Quick win from containerization before full decomposition. |
| **Big-Bang Rewrite** | Not applicable — the monolith is functional and actively maintained. | Very High | ⚠️ **Recommended against.** High risk; the existing codebase is well-structured enough for incremental extraction. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's Dapper/Datastore data model | Every extraction — translate between the monolith's table mapper and the new service's domain model |
| **Saga Pattern** | Manage distributed transactions (e.g., indexer search → notification → history) | When extracting the search workflow that currently spans multiple in-process calls |
| **Event Sourcing** | Capture indexer state changes as events for downstream consumers (Sonarr, Radarr) | When the Applications module is extracted to enable event-driven sync with downstream *arr apps |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters | Every new service — ensures testability and infrastructure portability |

### Effort Estimation Factors

| Factor | Assessment | Signal |
|--------|-----------|--------|
| Module boundaries | Identifiable modules (Indexers, Notifications, History, Applications) but in-process coupling | Medium effort — seams exist but require ACL |
| Data coupling | Single shared SQLite/PostgreSQL database with cross-module table access | High effort — database decomposition required |
| Stored procedures | None (DATA-Q4=4) | Low effort — no database logic to extract |
| Communication patterns | All in-process with SignalR for UI updates | Medium effort — need to introduce inter-service communication |
| CI/CD maturity | Build automation exists; no deployment automation | Medium effort — need to build deployment pipeline |
| Test coverage | Unit and integration tests exist but gaps remain | Medium effort — tests exist but may need updating for distributed system |

### Suggested Extraction Order

1. **Notifications Service** — Low coupling, clear boundaries, event-driven by nature
2. **History/Logging Service** — Read-heavy, minimal write coupling to core domain
3. **Indexer Search Service** — High-value extraction for independent scaling
4. **Application Sync Service** — Manages sync with downstream *arr applications via EventBridge

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is self-managed. The application is distributed as platform-specific self-contained .NET 8 archives and Windows InnoSetup installers for 10+ platform/architecture combinations. No cloud compute services (ECS, EKS, Lambda, Fargate) are referenced. The application enforces single-instance via `ISingleInstancePolicy.PreventStartIfAlreadyRunning()`. |
| **Gap** | No managed compute infrastructure. Application runs directly on user-provisioned hardware or VMs with no cloud orchestration. |
| **Recommendation** | Containerize the application using .NET 8 container support and deploy to Amazon EKS (preferred). Create a Dockerfile based on the existing self-contained publish configuration. The application's existing env-var configuration override pattern (`Prowlarr__` prefix) and health check endpoint (`/api/v1/health`) support containerized deployment. |
| **Evidence** | `src/NzbDrone.Console/Prowlarr.Console.csproj`, `azure-pipelines.yml` (platform matrix), `distribution/` directory, `src/NzbDrone.Host/SingleInstancePolicy.cs` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. SQLite is the default embedded database (file-based, bundled with the application). PostgreSQL is optionally supported but requires the user to provision and manage their own instance. No managed database services (RDS, Aurora, DynamoDB) are referenced in the codebase. |
| **Gap** | No managed database services. SQLite provides zero operational features (no failover, no automated backup beyond application-level ZIP). PostgreSQL usage requires full self-management (patching, backup, scaling). |
| **Recommendation** | Migrate PostgreSQL workloads to Amazon Aurora PostgreSQL (preferred). The application already has full PostgreSQL support via Npgsql driver and FluentMigrator migrations. Aurora provides automated failover, backup, and scaling with no application code changes needed (connection string update only). |
| **Evidence** | `src/NzbDrone.Core/Datastore/DbFactory.cs`, `src/NzbDrone.Core/Datastore/PostgresOptions.cs`, `src/NzbDrone.Core/Prowlarr.Core.csproj` (Npgsql 9.0.3) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements workflow-like patterns in code — scheduled tasks via a custom `TaskManager`, background jobs for indexer synchronization, RSS sync, backup scheduling, and application sync. These are hardcoded state machines with some structure (separate job classes, scheduled execution) but no dedicated orchestration service. The `HealthCheckService` uses an event-driven pattern with debouncing. |
| **Gap** | Multi-step operations (indexer sync → notification → history recording → application sync) are coordinated through in-process event handlers and background tasks with no dedicated workflow orchestration, no visual workflow management, and limited retry/error handling beyond Polly retry policies on HTTP calls. |
| **Recommendation** | For a cloud deployment, consider AWS Step Functions to orchestrate the indexer sync → notification → history → app sync workflow. This provides visual workflow management, built-in retry logic, and error handling. However, given the stateful-crud archetype, this is a secondary priority behind containerization and managed database migration. |
| **Evidence** | `src/NzbDrone.Core/Jobs/`, `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`, `src/NzbDrone.Core/Applications/ApplicationService.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure exists. The application uses in-process event handling (custom `IEventAggregator` pattern) and SignalR WebSockets for real-time UI updates. Cross-service state changes (to downstream *arr applications like Sonarr/Radarr) are handled via synchronous HTTP calls. No SQS, SNS, EventBridge, or any message broker is used. |
| **Gap** | State changes that cross service boundaries (application sync with downstream *arr suite) are handled via synchronous HTTP with Polly retry but no decoupling, no dead letter queue, no guaranteed delivery. If downstream services are unavailable, sync operations fail. |
| **Recommendation** | For a cloud deployment, introduce Amazon EventBridge (preferred) for event-driven communication between Prowlarr and downstream *arr applications. This provides decoupling, retry with DLQ, and event filtering. The existing `IEventAggregator` pattern maps naturally to EventBridge events. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/`, `src/NzbDrone.SignalR/MessageHub.cs`, `src/NzbDrone.Core/Applications/` (sync via HTTP) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation is defined. The application runs on user-provisioned infrastructure with no cloud network controls. The application supports reverse proxy awareness via `ForwardedHeaders` middleware but this is for HTTP header trust, not network isolation. CORS is configured as permissive (`AllowAnyOrigin/Method/Header`). |
| **Gap** | No network security infrastructure. The application exposes port 9696 directly with no network segmentation, no private subnet isolation, and permissive CORS. |
| **Recommendation** | When deploying to AWS, provision a VPC with private subnets for the application and database tier. Use security groups with least-privilege rules. Place an Application Load Balancer or API Gateway in a public subnet. Remove permissive CORS and configure specific allowed origins. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (ForwardedHeaders, CORS config), no IaC files exist |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or managed entry point exists. The application exposes its Kestrel web server directly on port 9696. Users may configure a reverse proxy manually (the application supports ForwardedHeaders) but no managed entry point is defined. |
| **Gap** | Direct service exposure without throttling, centralized authentication, request validation, or traffic management. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) in front of the application for throttling, request validation, and centralized auth. Alternatively, use an Application Load Balancer with WAF rules for simpler setups. The existing `/api/v1/` path structure maps directly to API Gateway route configuration. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (Kestrel, ForwardedHeaders), `src/Prowlarr.Api.V1/openapi.json` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application enforces single-instance operation (`SingleInstancePolicy`). No ASG, ECS service scaling, or Lambda concurrency configuration is present. The application cannot scale horizontally in its current architecture. |
| **Gap** | Single-instance deployment with no ability to scale based on demand. No vertical or horizontal scaling automation. |
| **Recommendation** | After containerization and removal of single-instance enforcement, configure EKS Horizontal Pod Autoscaler based on request rate and CPU utilization. The search endpoint is the most likely scaling target — consider extracting it as a stateless service that can scale independently. |
| **Evidence** | `src/NzbDrone.Host/SingleInstancePolicy.cs`, no IaC files |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application implements its own backup mechanism (`BackupService.cs`) that creates ZIP archives of Config.xml + SQLite database + version info. Backup types include Manual, Scheduled, and Pre-Update with configurable retention. However, this only backs up SQLite — PostgreSQL backup is not handled by the application. No cloud backup services (AWS Backup), PITR, or cross-region replication exist. |
| **Gap** | Application-level backup only for SQLite. PostgreSQL has no backup automation. No PITR capability. No tested restore procedures documented. No cross-region backup replication. Backup is a ZIP file on the local filesystem — vulnerable to disk failure. |
| **Recommendation** | Migrate to Aurora PostgreSQL which provides automated backups with PITR. For configuration and application state, use AWS Backup with S3 for cross-region replication. The existing BackupService can be retained for user-initiated backups but should not be the only recovery mechanism. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs`, no PostgreSQL backup logic found |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration exists. The application enforces single-instance operation and has no load balancing, failover, or fault isolation mechanisms. The entire application runs as one process on one host with no redundancy. |
| **Gap** | Single point of failure with no automatic recovery. Any host failure takes down the entire application. No multi-AZ deployment for either compute or database. |
| **Recommendation** | After containerization, deploy to EKS with replicas across 2+ AZs (requires removing single-instance enforcement and addressing any shared-state assumptions). Use Aurora PostgreSQL Multi-AZ for database high availability. Configure health checks for automatic container restart on failure. |
| **Evidence** | `src/NzbDrone.Host/SingleInstancePolicy.cs`, no IaC or deployment manifests |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in the repository. No Terraform, CloudFormation, CDK, Helm, Kustomize, or any IaC files were found. All infrastructure provisioning is manual or outside the repository scope. |
| **Gap** | 0% IaC coverage. Infrastructure changes are non-reproducible, manual, and undocumented in code. No disaster recovery automation. Environment consistency cannot be guaranteed. |
| **Recommendation** | Define all infrastructure in AWS CDK (TypeScript) or Terraform. Start with the foundational resources: VPC, EKS cluster, Aurora PostgreSQL, ECR repository, and API Gateway. Store IaC in the same repository or a dedicated infrastructure repository. |
| **Evidence** | Repository-wide search for `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` — none found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Azure DevOps Pipelines provides comprehensive build and test automation across 10 stages (Setup, Build Backend, Build Frontend, Installer, Packages, Unit Tests, Integration Tests, Automation Tests, Analyze, Report). Builds cover 10+ platform/architecture combinations with PostgreSQL 14/15 integration testing. SonarCloud analysis is integrated. However, there is no deployment automation — builds produce archives but deployment is manual via self-update mechanism. GitHub Actions exist but only for issue/PR management. |
| **Gap** | Build is fully automated but deployment is entirely manual. No deploy stage in the pipeline. No automated rollback. No infrastructure deployment automation. The self-update mechanism is the only "deployment" path, which is user-initiated. |
| **Recommendation** | Extend the CI/CD pipeline with deployment stages targeting AWS. Add a deploy stage using AWS CodeDeploy to EKS after container builds. Implement automated rollback on health check failure. Add infrastructure pipeline for CDK/Terraform changes. |
| **Evidence** | `azure-pipelines.yml` (10 stages, no deploy stage), `.github/workflows/` (labeling only), self-update mechanism in `src/NzbDrone.Update/` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application uses .NET 8.0 (C#) with ASP.NET Core — a modern cloud-native language at a current version with matching modern framework. The .NET SDK version is 8.0.405 (pinned in `global.json`). ASP.NET Core is the current web framework with full AWS SDK support. Frontend uses TypeScript 5.7.2 with React (modern toolchain). |
| **Gap** | N/A — language and framework are current. |
| **Recommendation** | N/A — no language modernization needed. The .NET 8.0 + ASP.NET Core stack has first-class AWS SDK support and excellent cloud-native tooling. |
| **Evidence** | `global.json` (.NET SDK 8.0.405), `src/Directory.Build.props`, `src/NzbDrone.Host/Prowlarr.Host.csproj` (Microsoft.NET.Sdk.Web), `package.json` (TypeScript 5.7.2) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Tightly-coupled monolith deployed as a single binary. All functionality — indexer management, search, notifications, downloads, health checks, authentication, backup, history, application sync — is bundled in one deployable unit. Single shared database (SQLite or PostgreSQL) accessed by all modules. The application enforces single-instance operation. Internal modules exist (Indexers, Applications, Notifications, History) but share a database via the `BasicRepository` pattern with cross-module table access. |
| **Gap** | No module boundaries enforced — any module can access any repository. Shared mutable state in the database with no schema separation. Circular dependencies possible through the `IEventAggregator` pattern. Cannot deploy, scale, or update modules independently. |
| **Recommendation** | Begin with Strangler Fig extraction of the Notifications service (lowest coupling, event-driven nature), followed by History (read-heavy), then Indexer Search (highest scaling value). See Decomposition Strategy section. |
| **Evidence** | `src/Prowlarr.sln` (single solution, 13 non-test projects), `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Host/SingleInstancePolicy.cs` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Primarily synchronous architecture. Inter-module communication is in-process method calls. External communication with downstream *arr applications (Sonarr, Radarr, Lidarr) is via synchronous HTTP with Polly retry policies. Some internal async patterns exist: SignalR for real-time UI updates, background task scheduler for periodic jobs, and the `IEventAggregator` for in-process event handling. However, cross-service state propagation (application sync) is entirely synchronous HTTP. |
| **Gap** | Cross-service state changes (sync with downstream *arr applications) use synchronous HTTP with no decoupling. If downstream services are unavailable, operations fail after retries. No message queue or event bus for cross-service communication. |
| **Recommendation** | Introduce Amazon EventBridge for cross-service state propagation when deploying to AWS. The existing `IEventAggregator` pattern provides a natural mapping — internal events can be published to EventBridge for downstream consumer decoupling. |
| **Evidence** | `src/NzbDrone.Core/Applications/` (HTTP sync), `src/NzbDrone.Core/Messaging/Events/`, `src/NzbDrone.SignalR/MessageHub.cs` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some background job processing exists but patterns are inconsistent. The application has a custom `TaskManager` for scheduled background jobs (RSS sync, indexer sync, backup) and processes search operations asynchronously via a command queue pattern. However, bulk operations (full indexer sync, search across all indexers) can potentially exceed 30 seconds and are handled in background tasks with no status polling API or callback mechanism for clients. The SignalR hub provides some real-time status updates but this is not a formal async job pattern. |
| **Gap** | No formal async job pattern with status polling for long-running operations. Bulk searches and full syncs may exceed 30 seconds with no way for API clients to check progress. Background tasks have no checkpointing or resume capability. |
| **Recommendation** | Implement a formal async job pattern with status polling endpoints for long-running operations. When moving to AWS, consider Step Functions for multi-step workflows (full indexer sync → notification → app sync) with built-in status tracking and retry. |
| **Evidence** | `src/NzbDrone.Core/Jobs/`, `src/NzbDrone.Core/Messaging/Commands/`, `src/NzbDrone.SignalR/MessageHub.cs` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Consistent API versioning strategy exists. All endpoints use the `/api/v1/` URL path prefix. The entire API surface is versioned — `src/Prowlarr.Api.V1/` is a dedicated project containing all API controllers. OpenAPI 3.0.4 specification is generated. The API project is explicitly named `Prowlarr.Api.V1` indicating versioning is structural. |
| **Gap** | Only v1 exists — no evidence of backward-compatible migration strategy or version deprecation policy. No version headers or content negotiation as alternative mechanisms. |
| **Recommendation** | Document a version deprecation policy and migration guide for when v2 is introduced. Consider adding version sunset headers on API responses to signal future deprecation. Current v1-only state is acceptable for the application's maturity. |
| **Evidence** | `src/Prowlarr.Api.V1/` (project structure), `src/Prowlarr.Api.V1/openapi.json` (all paths under `/api/v1/`) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints for downstream *arr applications (Sonarr, Radarr, Lidarr) are configured via user-provided URLs stored in the database. These are effectively environment-driven configuration — users add application endpoints through the UI/API. No dynamic service discovery mechanism exists. The application does not participate in any service mesh or registry. |
| **Gap** | Hard-coded (user-configured) service endpoints with no dynamic discovery. If downstream services move, users must manually update configuration. No health-aware routing or automatic failover to alternative endpoints. |
| **Recommendation** | When deploying in AWS with multiple services, implement service discovery via AWS Cloud Map or EKS internal DNS. For the current architecture, the user-configured endpoints are acceptable since Prowlarr manages a known set of downstream applications. |
| **Evidence** | `src/NzbDrone.Core/Applications/` (URL-based application configuration), database-stored endpoint URLs |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application stores data primarily in SQLite/PostgreSQL structured tables. Configuration is stored in an XML file (`Config.xml`) on the local filesystem. Backup archives (ZIP files) are stored on the local filesystem. Log files are stored on the local filesystem with rolling archive. No S3 or managed object storage is used. |
| **Gap** | Backups, logs, and configuration are on local filesystem — vulnerable to disk failure and inaccessible for external tooling. No managed object storage for unstructured data. |
| **Recommendation** | When deploying to AWS, store backups in S3 with lifecycle policies. Ship logs to CloudWatch Logs or S3. Store configuration in AWS Systems Manager Parameter Store or Secrets Manager. This provides durability, accessibility, and integration with AWS analytics tools. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs` (filesystem ZIP), `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (file targets), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (Config.xml) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a well-structured data access layer. `BasicRepository<T>` provides a generic repository pattern using Dapper. All database access goes through repository classes that inherit from `BasicRepository`. The `DbFactory` provides centralized connection management. `TableMapper` handles entity-to-table mapping. `SqlBuilder` with `WhereBuilderSqlite`/`WhereBuilderPostgres` abstracts database-specific SQL. FluentMigrator manages schema evolution. |
| **Gap** | Mostly centralized but some direct SQL access exists in migration files and specialized query builders that bypass the repository pattern. The dual-database abstraction (SQLite + PostgreSQL) adds complexity with separate `WhereBuilder` implementations. |
| **Recommendation** | Maintain the current centralized pattern. When migrating to Aurora PostgreSQL exclusively, the SQLite-specific code paths can be removed, simplifying the data access layer. Consider documenting the repository pattern as a formal data contract. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/DbFactory.cs`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline tests against PostgreSQL 14 and 15. Migration `000_database_engine_version_check.cs` validates database versions at startup. However, no explicit version pinning exists in deployment configuration (since no IaC exists). SQLite version is implicitly determined by the .NET runtime package. PostgreSQL 14 reaches EOL in November 2026. |
| **Gap** | No explicit version pinning in deployment configuration. PostgreSQL 14 is approaching EOL. No documented version-update procedure. Version is validated at runtime but not controlled at deployment time. |
| **Recommendation** | When deploying with Aurora PostgreSQL, pin the engine version explicitly in IaC (e.g., `engine_version = "15.4"` in Terraform). Document a version-update procedure with rollback plan. Remove PostgreSQL 14 from CI testing as it approaches EOL and add PostgreSQL 16/17 testing. |
| **Evidence** | `azure-pipelines.yml` (PostgreSQL 14/15 test matrix), `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. All business logic resides in the C# application layer. Database schema is managed through FluentMigrator C# code (44 migrations) that generates standard SQL DDL. Queries use Dapper with parameterized SQL that is compatible across SQLite and PostgreSQL. No raw SQL files exist in the repository. |
| **Gap** | N/A — no stored procedures or proprietary SQL. |
| **Recommendation** | N/A — the current approach (all logic in application layer) is the target state for modernization. This significantly simplifies any database migration since there is no stored procedure logic to extract. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (44 C# migration files, no `.sql` files), `src/NzbDrone.Core/Datastore/SqlBuilder.cs` (parameterized SQL) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent cloud audit logging exists. The application has application-level logging via NLog (file, console, Sentry error tracking) and logs authentication events (login/logout with user info). However, there is no immutable audit trail, no infrastructure-level action logging, and no compliance-grade audit mechanism. |
| **Gap** | No cloud audit logging. Application logs are mutable files on the local filesystem. No immutable storage. No ability to trace administrative actions at the infrastructure level. No compliance audit trail. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Ship application audit logs (authentication events, configuration changes) to CloudWatch Logs with retention policies. Consider a dedicated audit log stream for compliance-sensitive events. |
| **Evidence** | `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (file-based logging), `src/Prowlarr.Http/Authentication/AuthenticationService.cs` (login audit logging), no CloudTrail or audit infrastructure |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured. SQLite database files are stored unencrypted on the local filesystem. Configuration file (`Config.xml`) containing API keys and passwords is stored as plaintext XML. Backup ZIP files containing database and config are unencrypted. No KMS or any encryption mechanism for data at rest. |
| **Gap** | All sensitive data at rest is unencrypted — database files, configuration with credentials, and backup archives. No customer-managed or AWS-managed encryption keys. |
| **Recommendation** | When deploying to AWS with Aurora PostgreSQL, enable encryption at rest with a customer-managed KMS key. Store backups in S3 with SSE-KMS encryption. Store sensitive configuration in Secrets Manager (encrypted by default). Enable EBS/EFS encryption for any persistent volumes. |
| **Evidence** | `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (plaintext Config.xml), `src/NzbDrone.Core/Backup/BackupService.cs` (unencrypted ZIP), SQLite file-based storage |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API authentication uses a static API key mechanism. Authentication is enforced via `ApiKeyAuthenticationHandler` checking the `X-Api-Key` header, `apikey` query parameter, or Bearer token. The API key is a GUID generated at first run and stored in Config.xml. Forms authentication (cookie-based, 7-day sliding expiration) is available for the UI. A fallback authorization policy requires authentication on all endpoints unless `[AllowAnonymous]`. The authentication system supports multiple modes: None, Basic, Forms, External. |
| **Gap** | Static API key authentication without rotation. Not token-based auth (no OAuth2/JWT). API key is a single GUID shared across all clients with no per-client keys or scoping. No token expiration beyond the cookie-based UI session. The "None" authentication mode allows completely unauthenticated access. |
| **Recommendation** | When deploying to AWS, implement API Gateway with OAuth2/JWT authorizers backed by Amazon Cognito. Replace the static API key with per-client API keys via API Gateway usage plans. Remove the "None" authentication mode or restrict it to localhost-only development. |
| **Evidence** | `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Prowlarr.Http/Authentication/AuthenticationBuilderExtensions.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (API key in Config.xml) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. User credentials (username + PBKDF2-HMAC-SHA512 hashed password) are stored in the local database via `UserService`/`UserRepository`. No integration with any external identity provider (Cognito, Okta, OIDC, SAML). The "External" authentication mode trusts a reverse proxy header but does not integrate with a centralized IdP. |
| **Gap** | No centralized identity provider integration. No SSO capability. No federation. Authentication is entirely self-contained within the application. |
| **Recommendation** | When deploying to AWS, integrate with Amazon Cognito for user authentication. Implement OIDC federation to enable SSO with corporate identity providers. The existing "External" auth mode provides a natural extension point for Cognito integration via ALB/API Gateway OIDC. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserService.cs` (PBKDF2 local auth), `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/NzbDrone.Core/Authentication/AuthenticationType.cs` (None, Basic, Forms, External) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets (API key, PostgreSQL password, SSL cert password, proxy password) are stored in `Config.xml` on the local filesystem. The file is not committed to version control (generated at runtime) so no plaintext credentials exist in the repository source code. Configuration can be overridden via environment variables (`Prowlarr__` prefix). No external secrets manager integration (no Secrets Manager, Vault, or Parameter Store). No rotation configured. |
| **Gap** | Production credentials are in a plaintext XML file on the filesystem and/or environment variables. No automated rotation. No centralized secrets management. No encryption of the config file. |
| **Recommendation** | When deploying to AWS, migrate all secrets to AWS Secrets Manager with automated rotation. Store the PostgreSQL connection string as a Secrets Manager secret with rotation Lambda. Replace Config.xml credential storage with Secrets Manager SDK calls. Use IAM roles for service-to-service authentication where possible. |
| **Evidence** | `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (Config.xml with ApiKey, PostgresPassword, SslCertPassword), `src/NzbDrone.Host/Bootstrap.cs` (env var override) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base images. The application is distributed as self-contained .NET 8 binaries with no managed patching infrastructure. The self-update mechanism handles application-level updates but not OS or runtime patching. |
| **Gap** | No infrastructure patching strategy. No vulnerability scanning for the deployed compute environment. No hardened base images. No container image scanning. |
| **Recommendation** | When containerizing, use hardened base images (Microsoft's .NET 8 distroless or Chainguard images). Enable Amazon ECR image scanning for vulnerability detection. Implement SSM Patch Manager for any remaining EC2 instances. Integrate Snyk or Trivy container scanning into the CI/CD pipeline. |
| **Evidence** | No patching infrastructure found, `azure-pipelines.yml` (no container scanning), self-update mechanism in `src/NzbDrone.Update/` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud is integrated into the Azure DevOps pipeline for static analysis with code coverage reporting. Dependabot is configured but only monitors the devcontainers ecosystem — not NuGet, npm/yarn, or GitHub Actions dependencies. No DAST, no container scanning, and no blocking security gate (SonarCloud analysis runs but does not gate the pipeline). |
| **Gap** | Limited security scanning coverage. Dependabot does not monitor the primary dependency ecosystems (NuGet, npm). SonarCloud provides SAST but without a blocking gate. No container scanning (no containers yet). No DAST. |
| **Recommendation** | Expand Dependabot to monitor `nuget` and `npm` ecosystems. Add a quality gate in SonarCloud that blocks merges on critical findings. When containerizing, add Trivy or ECR image scanning. Consider adding OWASP ZAP or similar DAST for the API surface. |
| **Evidence** | `azure-pipelines.yml` (SonarCloud analysis stage), `.github/dependabot.yml` (devcontainers only) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry, X-Ray, or any tracing SDK is present in the dependency manifests or source code. The application has request-level logging with sequence IDs in the HTTP middleware but no trace ID propagation across service boundaries. Sentry provides error tracking but not distributed tracing. |
| **Gap** | No distributed tracing. Cannot trace request flows through the system or to downstream *arr applications. No trace context propagation. Debugging cross-service issues requires manual log correlation. |
| **Recommendation** | Instrument with OpenTelemetry .NET SDK (compatible with .NET 8 and ASP.NET Core). Configure AWS X-Ray as the tracing backend. Propagate trace context in HTTP calls to downstream *arr applications. The existing HTTP middleware provides a natural instrumentation point. |
| **Evidence** | No `OpenTelemetry` or `AWS.XRay` in any `.csproj` file, `src/NzbDrone.Common/Instrumentation/` (NLog + Sentry only) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs are defined. No formal definition of acceptable service levels for latency, availability, or error rates. The internal health check system monitors component health (indexer status, application connectivity, system time) but these are operational checks, not SLO definitions with error budgets. No CloudWatch alarms for latency percentiles or error rate thresholds. |
| **Gap** | No SLOs defined for critical user journeys (search latency, indexer availability, API response times). No error budget tracking. No formal acceptable service level definition. |
| **Recommendation** | Define SLOs for critical journeys: search response time (p99 < 5s), indexer availability (>99.5%), API error rate (<1%). When on AWS, implement with CloudWatch metrics, composite alarms, and error budget dashboards. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational checks, not SLOs), no SLO definitions found |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The application has internal analytics (`src/NzbDrone.Core/Analytics/`) but these track application-level events internally (stored in database), not published as metrics for monitoring. No CloudWatch custom metrics, no Prometheus exposition, no business KPI dashboards. The health check system tracks component status but does not emit quantitative business metrics. |
| **Gap** | No business metrics instrumentation. Cannot measure search success rate, indexer utilization, sync failure rate, or other business-relevant KPIs externally. Only infrastructure-level logs exist. |
| **Recommendation** | Instrument business metrics using CloudWatch custom metrics or OpenTelemetry metrics: searches per minute, search success/failure rate, indexer response times, application sync success rate, grab/download rates. Build CloudWatch dashboards for operational visibility. |
| **Evidence** | `src/NzbDrone.Core/Analytics/` (internal only), no metrics SDK in dependencies |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or external alerting is configured. The internal health check system detects component-level issues (indexer down, application unreachable) and displays them in the UI via SignalR. However, there are no CloudWatch alarms, no PagerDuty/OpsGenie integration, no anomaly detection on error rates or latency, and no external notification of system degradation beyond the application's own notification system (email, Discord, etc. for indexer-level events). |
| **Gap** | No external alerting infrastructure. Health issues are only visible within the application UI. No anomaly detection on error rates or latency patterns. No escalation to operations teams. |
| **Recommendation** | When on AWS, configure CloudWatch alarms with anomaly detection on error rates and p99 latency. Integrate with SNS for alert routing to PagerDuty/OpsGenie. Create composite alarms for critical business flows (search availability + indexer health). |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (UI-only health display), `src/NzbDrone.Core/Notifications/` (indexer-level notifications, not ops alerting) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The application uses a self-update mechanism (`NzbDrone.Update` project) where the running instance downloads and applies updates in-place. There is no blue/green, canary, rolling deployment, or any staged rollout. Updates are applied directly with no traffic shifting or rollback capability beyond reverting to a backup. CI produces build artifacts but does not deploy them. |
| **Gap** | Direct in-place update with no staged rollout, no traffic shifting, no automated rollback, and no deployment validation. Users experience downtime during updates. Failed updates require manual intervention. |
| **Recommendation** | When containerized on EKS, implement rolling deployments with health check validation as the baseline. Progress to blue/green deployments using AWS CodeDeploy with EKS for zero-downtime releases. Configure automatic rollback on health check failure. |
| **Evidence** | `src/NzbDrone.Update/` (in-place self-update), `azure-pipelines.yml` (no deploy stage) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Integration tests exist in `NzbDrone.Integration.Test` and run in the CI pipeline against both SQLite and PostgreSQL databases. The tests exercise the API layer with a running application instance. Automation tests (`NzbDrone.Automation.Test`) test the UI via Selenium. However, integration tests do not cover all critical workflows — they focus on API endpoint validation rather than end-to-end business flow testing. Contract tests with downstream *arr applications are absent. |
| **Gap** | Integration tests exist but have limited workflow coverage. No contract tests with downstream services. No end-to-end tests for critical journeys (search across multiple indexers → notification → application sync). Automation tests are Selenium-based (brittle, slow). |
| **Recommendation** | Expand integration test coverage to include critical business workflows. Add contract tests for the API consumed by downstream *arr applications. Consider replacing Selenium tests with API-level end-to-end tests for reliability. When on EKS, run integration tests against the containerized deployment in a staging environment. |
| **Evidence** | `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Automation.Test/`, `azure-pipelines.yml` (Integration and Automation stages) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation, runbooks, or self-healing patterns exist. The internal health check system detects issues and displays them to the user but takes no automated remediation action. No Systems Manager Automation documents, no Lambda-based remediation, no runbook files. The application's auto-recovery is limited to restarting a corrupt log database. |
| **Gap** | No incident response automation. No runbooks (manual or automated). No self-healing beyond log database recovery. All incident response is manual and user-initiated. |
| **Recommendation** | Create runbooks for common failure scenarios (database corruption, indexer connectivity loss, disk full). When on AWS, implement SSM Automation documents for common remediations. Configure auto-recovery for the EKS deployment via health check-driven pod restarts. Consider Step Functions for automated incident workflows. |
| **Evidence** | `src/NzbDrone.Core/Datastore/DbFactory.cs` (log DB auto-recovery only), no runbook files found |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership patterns exist. No per-service dashboards, no CODEOWNERS for monitoring assets, no named alarm owners, no SLO definitions with team attribution. The internal health check system is the only observability surface and has no ownership attribution. |
| **Gap** | No observability ownership. No dashboards. No alarm ownership. No team attribution for monitoring assets. |
| **Recommendation** | When deploying to AWS, establish observability ownership: create CloudWatch dashboards per functional area (indexers, search, notifications, system health). Define alarm owners in the team's on-call rotation. Add CODEOWNERS entries for monitoring configuration. |
| **Evidence** | No CODEOWNERS file, no dashboard definitions, no alarm configurations |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources exist. No IaC defines any cloud resources, so there is no tagging strategy, no cost allocation tags, and no ownership tags. |
| **Gap** | No tagging governance. When cloud resources are provisioned, there is no existing standard for cost allocation, ownership, or environment identification. |
| **Recommendation** | Establish a tagging standard before provisioning any AWS resources. Required tags: `Environment` (dev/staging/prod), `Service` (prowlarr), `Team` (owner), `CostCenter`. Implement via `default_tags` in Terraform provider or CDK `Tags.of()`. Enforce with AWS Config required-tags rule and Tag Policies in Organizations. |
| **Evidence** | No IaC files, no cloud resources, no tagging configuration |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Containers
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR)
- [EKS Workshop](https://www.eksworkshop.com/)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `azure-pipelines.yml` | INF-Q11, SEC-Q7, OPS-Q6, DATA-Q3 | CI/CD pipeline definition with 10 stages, SonarCloud, PostgreSQL test matrix |
| `.github/dependabot.yml` | SEC-Q7 | Minimal Dependabot config (devcontainers only) |
| `global.json` | APP-Q1 | .NET SDK 8.0.405 version pin |
| `src/Directory.Build.props` | APP-Q1 | Centralized build properties |
| `src/Prowlarr.sln` | APP-Q2 | Solution structure (28 projects) |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, SEC-Q3 | ASP.NET Core startup with auth, CORS, middleware |
| `src/NzbDrone.Host/Prowlarr.Host.csproj` | APP-Q1 | Host project dependencies |
| `src/NzbDrone.Host/SingleInstancePolicy.cs` | INF-Q1, INF-Q7, INF-Q9, APP-Q2 | Single-instance enforcement |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | INF-Q2, OPS-Q7 | Database factory with SQLite/PostgreSQL support |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | APP-Q2, DATA-Q2 | Generic repository pattern |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2, DATA-Q4 | Parameterized SQL generation |
| `src/NzbDrone.Core/Datastore/PostgresOptions.cs` | INF-Q2 | PostgreSQL connection configuration |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 44 FluentMigrator C# migrations |
| `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs` | DATA-Q3 | Runtime DB version validation |
| `src/NzbDrone.Core/Prowlarr.Core.csproj` | INF-Q2, APP-Q1 | Core project with Npgsql, Dapper, Polly |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | SEC-Q2, SEC-Q5, DATA-Q1 | Config.xml with secrets storage |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8, DATA-Q1, SEC-Q2 | Application-level ZIP backup |
| `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` | INF-Q3, OPS-Q2, OPS-Q4 | Internal health check system |
| `src/NzbDrone.Core/Jobs/` | INF-Q3, APP-Q4 | Background task scheduling |
| `src/NzbDrone.Core/Messaging/Events/` | APP-Q3, INF-Q4 | In-process event aggregator |
| `src/NzbDrone.Core/Applications/` | APP-Q3, APP-Q6, INF-Q4 | Downstream *arr application sync |
| `src/NzbDrone.Core/Authentication/UserService.cs` | SEC-Q4 | PBKDF2 local user authentication |
| `src/NzbDrone.Core/Authentication/AuthenticationType.cs` | SEC-Q3, SEC-Q4 | Auth modes (None, Basic, Forms, External) |
| `src/NzbDrone.Core/Analytics/` | OPS-Q3 | Internal analytics (not published metrics) |
| `src/NzbDrone.Core/Notifications/` | OPS-Q4 | User notification system |
| `src/NzbDrone.SignalR/MessageHub.cs` | APP-Q3, APP-Q4 | Real-time WebSocket communication |
| `src/NzbDrone.Update/` | OPS-Q5 | Self-update mechanism |
| `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` | SEC-Q1, OPS-Q1, DATA-Q1 | NLog logging configuration |
| `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key authentication handler |
| `src/Prowlarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | SEC-Q3, SEC-Q4 | Auth scheme registration |
| `src/Prowlarr.Api.V1/openapi.json` | APP-Q5, APP-Q6 | OpenAPI 3.0.4 specification |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test project |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | Selenium UI automation tests |
| `src/NzbDrone.Host/Bootstrap.cs` | SEC-Q5 | Configuration/env var loading |
| `distribution/` | INF-Q1 | Platform-specific distribution packaging |
| `package.json` | APP-Q1 | Frontend dependencies (React 17, TypeScript 5.7) |
