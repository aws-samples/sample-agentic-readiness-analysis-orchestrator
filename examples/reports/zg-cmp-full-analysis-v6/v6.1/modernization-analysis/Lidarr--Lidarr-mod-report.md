# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | Lidarr--Lidarr |
| **Date** | 2026-05-08 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Music collection manager (*arr suite). |
| **Overall Score** | 1.92 / 4.0 |

**Archetype Justification**: The application owns persistent state (SQLite/PostgreSQL databases for music library, configuration, and logs), exposes CRUD operations on business entities (artists, albums, tracks, quality profiles), and manages entity lifecycle (monitored/unmonitored status, import/delete). Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.22 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work | Needs Work |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.60 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.43 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.92 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+2+1+1+1+1+1+2) / 9 evaluated questions = 11/9 = 1.22 (INF-Q3 and INF-Q9 Not Evaluated)
- APP: (4+2+2+2+2+2) / 6 = 14/6 = 2.33
- DATA: (2+3+3+4) / 4 = 12/4 = 3.00
- SEC: (2+1+2+1+2) / 5 evaluated questions = 8/5 = 1.60 (SEC-Q1 and SEC-Q2 Not Evaluated)
- OPS: (1+2+1+1+3+1+1) / 7 evaluated questions = 10/7 = 1.43 (OPS-Q5 and OPS-Q9 Not Evaluated)
- Overall: (1.22 + 2.33 + 3.00 + 1.60 + 1.43) / 5 = 9.58/5 = 1.92

---

## Classification

**Tier: 🟠 Remediation Required**

This repo has 9 High findings, 8 Medium findings, 3 Low findings. Rule matched: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker.

**Classification Consistency Check:** The V5 overall score of 1.92 falls in the "Needs Work" band (1.5–2.4), which maps to V6 "Remediation Required" per the equivalence table. The V6 tier is "Remediation Required" (2-11 High findings). These are **consistent**.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute — application distributed as bare-metal packages with no cloud deployment model | Blocks containerization, auto-scaling, and cloud-native modernization |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure (if any) is manually provisioned | Prevents automated, reproducible deployments and environment consistency |
| 3 | SEC-Q4: Centralized Identity Integration | 1 | Single static API key with no external IdP integration | No SSO, no RBAC, no federated identity — limits multi-user and enterprise adoption |
| 4 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined | Application has no cloud networking layer; relies on host-level network config |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing — only NLog file-based logging and Sentry error tracking | Cannot trace requests across service boundaries; debugging limited to log correlation |

---

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 2) and structured JSON responses detected. OpenAPI 3.0 spec exists at `src/Lidarr.Api.V1/openapi.json` with full endpoint documentation.
- **What it enables:** An agent that discovers and invokes Lidarr's existing REST API endpoints as tools — managing music libraries, triggering searches, monitoring downloads, and configuring profiles through natural language.
- **Additional steps:** The OpenAPI spec is auto-generated and available at `/docs/v1/openapi.json` in debug mode. Generate a production-accessible spec for agent tool discovery.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 3). Centralized data access layer via BasicRepository pattern with well-defined entity mappings.
- **What it enables:** A natural language to SQL agent for querying the music library database — finding artists by criteria, generating collection statistics, identifying missing albums.
- **Additional steps:** Document the database schema (entity relationships from TableMapping.cs) for agent consumption.
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (README, wiki content, API documentation, extensive code comments).
- **What it enables:** A knowledge agent that answers user questions about Lidarr configuration, troubleshooting, and usage by indexing existing documentation and wiki content.
- **Additional steps:** Index the OpenAPI spec, health check documentation, and configuration reference as the knowledge corpus.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no container definitions found (no Dockerfile) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected (SQLite + PostgreSQL are open source) |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2=1 but databases are SQLite (embedded) and PostgreSQL (open source, self-managed by design for a desktop app). No cloud deployment context exists to migrate to managed services. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads, streaming, or analytics pipelines detected. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=Not Evaluated, OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context mentions "Music collection manager" with no AI-related signal terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Lidarr is a tightly-coupled monolith (APP-Q2=2) with identifiable module boundaries (NzbDrone.Core, Lidarr.Http, Lidarr.Api.V1) but shared database access, direct cross-module dependencies, and a single deployment unit. The internal event aggregator provides loose coupling within the monolith, but all components deploy together.

**Compute Model Gaps:** No managed compute exists (INF-Q1=1). The application is distributed as self-hosted platform packages (deb, macOS app, Windows installer) with no cloud deployment model.

**Communication Pattern Gaps:** All communication is synchronous HTTP within the monolith (APP-Q3=2). Long-running operations (media scanning, metadata refresh, download monitoring) run as synchronous background tasks with no async job infrastructure (APP-Q4=2).

**Recommended Decomposition Approach:** Strangler Fig — extract high-value services (download management, metadata indexing, notification dispatch) as independent services while keeping the monolith running for core CRUD operations.

**Representative AWS Services:** ECS/EKS (preferred per preferences), API Gateway, EventBridge (preferred), Step Functions, Aurora PostgreSQL (preferred per preferences)

**Recommended Patterns:** Anti-corruption Layer for gradual extraction, Event Sourcing for music library state changes, Saga for download-import workflows

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Application is built as self-contained .NET 8.0 executables for 12+ platform targets. No Dockerfile, no container orchestration, no container registry integration.

**Container Readiness Indicators:**
- .NET 8.0 supports containerization natively (multi-stage builds, slim runtime images)
- Configuration already externalized via environment variables (`Lidarr__Postgres__*` pattern)
- Port binding is configurable (default 8686)
- Dev container already uses `mcr.microsoft.com/devcontainers/dotnet:1-8.0`
- Health check endpoint exists

**Recommended Container Orchestration Platform:** Amazon EKS (per preferences favoring EKS)

**Migration Approach:** Lift-and-containerize — the application is already a self-contained executable that can run in a container with minimal modification. Create a Dockerfile based on the existing dev container pattern, configure for PostgreSQL (production), and deploy to EKS.

**Representative AWS Services:** EKS, ECR, App Runner (for simpler deployments)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** No infrastructure-as-code exists. The application has no cloud deployment model and no infrastructure to codify. Moving to cloud deployment requires creating IaC from scratch.

**Current CI/CD State (INF-Q11=2):** Azure Pipelines provides comprehensive build and test automation (multi-platform builds, unit tests, integration tests, SonarCloud analysis). However, there is no automated deployment stage — pipelines produce artifacts but do not deploy them. No deployment automation, no environment promotion, no rollback capability.

**Deployment Strategy Gaps (OPS-Q5=Not Evaluated):** No deployed workload in this repo to assess deployment strategy.

**Testing Gaps (OPS-Q6=3):** Integration tests exist and run in CI against PostgreSQL 14/15 in Docker containers. Minor gap: automation/E2E tests exist but coverage is not comprehensive across all workflows.

**Recommended DevOps Toolchain:**
- **IaC:** Terraform or CDK for AWS infrastructure provisioning (EKS cluster, Aurora PostgreSQL, ECR, networking)
- **CI/CD:** Migrate from Azure Pipelines to AWS CodePipeline + CodeBuild, or GitHub Actions with AWS deployment
- **Deployment:** CodeDeploy with EKS for blue/green or canary deployments
- **Monitoring:** CloudWatch for infrastructure, X-Ray for tracing

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation/CDK, X-Ray, CloudWatch

---

## Decomposition Strategy

APP-Q2 scored 2 (monolith with identifiable modules but shared database and cross-module coupling). Decomposition guidance follows.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | The monolith has recognizable module boundaries (Core/Http/Api/SignalR) that can be extracted incrementally. Team can sustain parallel development. | Medium to High | ✅ **Recommended.** Extract notification dispatch, download client management, and metadata indexing as independent services while keeping the core CRUD monolith running. |
| **Conditional / Adaptive** | Limited capacity for full decomposition. Containerize as-is first, then selectively extract high-value services based on scaling needs. | Low to Medium | ✅ **Recommended when capacity is constrained.** Containerize the monolith first (Move to Containers pathway), then extract services that need independent scaling (e.g., metadata indexer, notification dispatcher). |
| **Big-Bang Rewrite** | Almost never applicable here — the monolith is functional and maintainable. | Very High | ⚠️ **Recommended against.** Lidarr is actively maintained with clear internal structure. Incremental extraction is safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the monolith's Dapper/repository data model | Every extraction — translate between monolith's entity model and new service's domain model |
| **Saga Pattern** | Manage distributed transactions for download→import→notification workflows | When extracting download management as a separate service |
| **Event Sourcing** | Capture music library state changes as events for cross-service consumption | When multiple services need to react to library changes (metadata updates, file imports) |
| **Hexagonal Architecture** | Structure each extracted service with clear business logic / infrastructure separation | Every new service — Lidarr's existing DryIoc DI and repository pattern provide a starting point |

### Effort Estimation Factors

| Factor | Current State | Effort Impact |
|--------|--------------|---------------|
| Module boundaries | Clear project structure (15 .csproj files) but heavy cross-project references | Medium — boundaries exist but need untangling |
| Data coupling | Single SQLite/PostgreSQL database shared across all modules via BasicRepository | High — requires database-per-service extraction |
| Stored procedures | None — all logic in application layer (DATA-Q4=4) | Low — no database-coupled logic to extract |
| Communication patterns | Internal event aggregator provides some decoupling within the monolith | Medium — existing events can be externalized to EventBridge |
| CI/CD maturity | Build and test automated; no deployment automation | Medium — need to add deployment pipeline for new services |
| Test coverage | Comprehensive unit and integration tests exist | Low — good foundation for safe extraction |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is bare-metal/VM-based. Lidarr is distributed as self-contained executables and OS-specific packages (deb, macOS .app, Windows installer) with no managed compute services. The application runs directly on host operating systems with no container orchestration or serverless model. |
| **Gap** | No managed compute — no ECS, EKS, Lambda, or Fargate usage. No cloud deployment model exists. |
| **Recommendation** | Containerize the application using .NET 8.0's native container support and deploy to Amazon EKS (per preferences). The application's environment variable configuration pattern and configurable port binding make it container-ready. |
| **Evidence** | `distribution/debian/`, `distribution/osx/`, `distribution/windows/`, `azure-pipelines.yml` (builds platform packages, no container images), `.devcontainer/devcontainer.json` (dev only) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Databases are entirely self-managed. SQLite is the default embedded database; PostgreSQL is supported as an optional alternative configured via environment variables. Both run on the same host as the application or on user-managed infrastructure. No managed database service (RDS, Aurora, DynamoDB) is referenced anywhere in the codebase. |
| **Gap** | All databases self-managed with no automated failover, no managed backups, and no scaling capability. |
| **Recommendation** | When moving to cloud deployment, migrate PostgreSQL workloads to Amazon Aurora PostgreSQL (per preferences). Aurora provides automated backups, Multi-AZ failover, and read replica auto-scaling. For smaller deployments, RDS PostgreSQL is also appropriate. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/DbFactory.cs`, `src/NzbDrone.Core/Datastore/PostgresOptions.cs` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateful-crud`. While Lidarr has multi-step operations (download→import→rename→notify), these are managed through an internal event aggregator and command/query pattern within the monolith. For a self-hosted stateful-crud application, the current internal orchestration pattern is functional — dedicated external workflow orchestration (Step Functions) would become relevant only after decomposition into distributed services. Evaluating against the orchestration rubric in the current monolithic state is not meaningful. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses an internal event aggregator (`IEventAggregator`) for in-process pub/sub messaging and has a command/query pattern for internal orchestration. SignalR provides real-time push to the frontend. However, no external messaging infrastructure exists (no SQS, SNS, EventBridge, Kafka, or RabbitMQ). Cross-service state changes (e.g., download complete → trigger import) are handled through in-process events rather than durable messaging. |
| **Gap** | No external messaging for cross-service state changes. All event-driven patterns are in-process only — a process restart loses in-flight events. For a stateful-crud service that will eventually be decomposed, the absence of durable messaging between what will become service boundaries is a genuine gap. |
| **Recommendation** | When decomposing the monolith, externalize the internal event aggregator to Amazon EventBridge (per preferences). The existing event-driven patterns (TrackImportedEvent, AlbumGrabbedEvent, DownloadCompletedEvent) map directly to EventBridge event types. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/IEventAggregator.cs`, `src/NzbDrone.SignalR/`, internal event classes throughout NzbDrone.Core |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation defined. The application is designed for self-hosted deployment with no cloud networking layer. Network security relies entirely on the host operating system's firewall configuration and the user's network setup. The application binds to a configurable address/port (default 0.0.0.0:8686). |
| **Gap** | No cloud network security — no private subnets, no security groups, no network segmentation. Application exposes HTTP directly with no network-level isolation. |
| **Recommendation** | When deploying to AWS, provision within a VPC with private subnets. Place the application behind an ALB or API Gateway in public subnets, with the application and database in private subnets. Use security groups with least-privilege ingress rules. Consider VPC Lattice for service-to-service communication if decomposed. |
| **Evidence** | No IaC files found. `src/NzbDrone.Common/Options/ServerOptions.cs` shows configurable bind address. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Services are exposed directly via Kestrel (built-in ASP.NET Core web server) with no gateway, load balancer, or CDN in front. The application serves both the API and the frontend SPA directly on port 8686 with no throttling, no request validation beyond API key auth, and no traffic management. |
| **Gap** | No API Gateway, ALB, or CloudFront. Direct service exposure with no throttling, no WAF, and no managed TLS termination. |
| **Recommendation** | Deploy behind Amazon API Gateway for the REST API (with throttling, request validation, and IAM/Cognito auth) and CloudFront for the frontend SPA static assets. Alternatively, use an ALB with WAF rules for a simpler setup. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Common/Options/ServerOptions.cs` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling mechanisms configured. The application runs as a single-instance process on the host with no scaling capability. No ASG, no ECS service scaling, no Lambda concurrency management, no database auto-scaling. |
| **Gap** | All capacity is statically provisioned — a single instance serves all traffic with no ability to scale horizontally. |
| **Recommendation** | When containerized and deployed to EKS, configure Horizontal Pod Autoscaler (HPA) based on CPU/memory utilization and request rate. For the database layer, Aurora auto-scaling handles read replicas and storage. |
| **Evidence** | No IaC files, no scaling configuration. Single-process architecture in `src/NzbDrone.Host/Bootstrap.cs`. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated backup configuration found. SQLite database files are stored on the local filesystem with no backup automation. PostgreSQL backup relies entirely on user-configured external tools. No PITR, no retention policies, no cross-region replication, no restore testing. The application has a built-in backup feature (triggered manually via UI) that creates a zip archive, but this is not automated or scheduled. |
| **Gap** | No automated backups, no retention policy, no tested restore procedures. Data loss recovery depends entirely on user discipline. |
| **Recommendation** | When migrated to Aurora PostgreSQL, leverage automated backups with configurable retention (up to 35 days) and PITR. Additionally, configure AWS Backup with a backup plan for cross-region replication of critical data. |
| **Evidence** | `src/NzbDrone.Core/Backup/BackupService.cs` (manual backup only), no `aws_backup_plan` or `backup_retention_period` configuration |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Surface flag `has_deployed_workload` is `false` — this repository contains no IaC defining deployable compute, and the Dockerfile/deployment manifests do not exist. The application is distributed as self-hosted packages, and its deployment topology (including HA configuration) is determined by the end-user. INF-Q9 cannot be assessed from source code alone. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in the repository. No Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, no Kubernetes manifests. The application is distributed as platform-specific packages with no cloud infrastructure definition. |
| **Gap** | 0% IaC coverage — all infrastructure (if any cloud deployment exists) would be manually created. |
| **Recommendation** | Create IaC using Terraform or CDK to define the AWS infrastructure: EKS cluster, Aurora PostgreSQL, ECR repository, VPC networking, ALB/API Gateway, and monitoring resources. Start with a CDK stack that provisions the complete deployment environment. |
| **Evidence** | No `.tf`, `cdk.json`, `template.yaml`, `Chart.yaml`, `kustomization.yaml`, or any IaC files found in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Azure Pipelines provides comprehensive build and test automation: multi-platform builds (12+ targets), unit tests, integration tests (with PostgreSQL in Docker), automation tests, SonarCloud analysis, and artifact publishing. However, there is no deployment stage — pipelines produce packaged artifacts but do not deploy them to any environment. No staging, no production deployment, no environment promotion, no automated rollback. |
| **Gap** | Build is automated but deployment is entirely manual. No continuous delivery — artifacts must be manually distributed and installed. No environment promotion pipeline. |
| **Recommendation** | Extend the CI/CD pipeline with deployment stages: build container image → push to ECR → deploy to EKS staging → run smoke tests → promote to production. Use AWS CodePipeline with CodeDeploy for EKS blue/green deployments, or GitHub Actions with AWS deployment actions. |
| **Evidence** | `azure-pipelines.yml` (10 stages: Setup, Build_Backend, Build_Frontend, Installer, Packages, Unit_Test, Integration, Automation, Analyze, Report_Out — no Deploy stage) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Modern cloud-native language at a current version with matching modern framework and SDK. C# on .NET 8.0 (LTS, current) with ASP.NET Core for the web layer. Frontend uses TypeScript 5.7 with React 18. The .NET 8.0 ecosystem has first-class AWS SDK coverage, mature containerization support (native container builds), and comprehensive cloud-native tooling. SDK version is current (.NET 8.0.405). |
| **Gap** | N/A — no language/framework gap. |
| **Recommendation** | N/A — language and framework stack is modern and cloud-ready. |
| **Evidence** | `global.json` (sdk: 8.0.405), `src/Directory.Build.props` (TargetFramework: net8.0), `package.json` (TypeScript 5.7.2, React 18.3.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Monolith with identifiable modules but shared database and cross-module coupling. The solution has 15 projects with logical separation (Core, Http, Api.V1, SignalR, Common) but all compile into a single deployable unit. The internal event aggregator provides loose coupling for event dispatch, but modules share a single SQLite/PostgreSQL database through BasicRepository with no schema isolation. Cross-project references are extensive. |
| **Gap** | Single deployable unit with shared database access across all modules. No independent deployment capability. Circular or heavy cross-dependencies between NzbDrone.Core and other projects. |
| **Recommendation** | Begin with the Conditional/Adaptive approach: containerize the monolith as-is, then identify service extraction candidates. High-value candidates for extraction: notification dispatch (25+ integrations), download client management, metadata indexing (Spotify, MusicBrainz). See Decomposition Strategy section. |
| **Evidence** | `src/Lidarr.sln` (single solution, 15 projects), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (shared data access), single deployment output |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Communication is primarily synchronous within the monolith. The internal event aggregator provides fire-and-forget messaging for notifications and state updates, but all HTTP API operations are synchronous request/response. Background tasks (scheduled scanning, metadata refresh) run as synchronous polling loops rather than event-driven processing. External service calls (indexers, download clients, metadata providers) are all synchronous HTTP. |
| **Gap** | Primarily synchronous with some async patterns for background jobs. No durable async messaging for cross-service state propagation. The in-process event aggregator provides decoupling but is not durable — events are lost on restart. |
| **Recommendation** | When decomposing, adopt EventBridge (per preferences) for cross-service state changes. Convert the internal event aggregator pattern to publish events externally. Use SQS for durable work queues (download queue, import queue). Polly (already in dependencies) provides resilience for synchronous calls during transition. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/`, HTTP client calls throughout `src/NzbDrone.Core/` (Indexers, DownloadClients, MetadataProviders), synchronous scheduler in `src/NzbDrone.Core/Jobs/` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Long-running operations (library scanning, metadata refresh, bulk imports) run as synchronous background tasks with basic progress tracking via SignalR push to the UI. Some background job processing exists through the internal task/command system, but there is no async job infrastructure with status polling or callbacks. The command queue provides ordering but operations block the queue until completion. |
| **Gap** | Some background job processing but inconsistent patterns. Library scan can take minutes/hours with no true async handling — the command blocks until complete. No job status API for external consumers. |
| **Recommendation** | Implement async job processing with AWS Step Functions for complex workflows (album import pipeline) or SQS + Lambda workers for simple tasks (notification dispatch). Expose a job status API endpoint for polling. The existing command/event pattern provides a good foundation for extraction. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/`, `src/NzbDrone.Core/Jobs/`, SignalR progress events |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Partial versioning exists — the API is namespaced under `/api/v1/` with a dedicated `Lidarr.Api.V1` project, indicating awareness of versioning. However, only one version exists, there is no backward compatibility policy, and no mechanism for version negotiation or deprecation. The OpenAPI spec documents only v1 with no migration guidance. |
| **Gap** | Versioning applied but only one version exists with no policy for introducing v2 or deprecating v1. No version negotiation headers or backward compatibility guarantees. |
| **Recommendation** | Document a versioning strategy: define when breaking changes warrant a new version, implement Accept-Version header support, and establish a deprecation timeline policy. The existing `/api/v1/` pattern provides a good foundation. |
| **Evidence** | `src/Lidarr.Api.V1/` project structure, `src/Lidarr.Api.V1/openapi.json` (paths under /api/v1/), route prefix in controllers |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured through environment variables and the XML configuration file. External service URLs (indexers, download clients, metadata providers) are stored in the database as user-configured settings. There is no dynamic service discovery, no service registry, and no service mesh. However, the environment variable pattern for internal configuration (`Lidarr__Postgres__Host`) provides some deployment flexibility. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. All service endpoints are configured statically at deployment time or by the user through the UI. |
| **Recommendation** | When deploying to EKS, leverage Kubernetes DNS-based service discovery for internal services. For external dependencies, consider AWS Cloud Map for service registration and discovery. The existing configuration pattern can be adapted to pull endpoints from service discovery rather than static config. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (static host config), `src/NzbDrone.Common/Options/ServerOptions.cs`, user-configured indexer/download client URLs stored in database |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Music files, cover art, and metadata are stored on local filesystems managed by the application. The DiskProvider abstraction handles file operations (move, copy, rename) across platforms. Cover art images are downloaded and cached locally. No S3 or cloud object storage is used. Data is accessible only from the host machine with no remote access capability. |
| **Gap** | Data in local filesystem storage with limited accessibility. No cloud object storage, no CDN for cover art, no remote access to media files. |
| **Recommendation** | When modernizing, store cover art and metadata in S3 with CloudFront for CDN delivery. For media files, consider Amazon S3 File Gateway to provide NFS/SMB access to S3-backed storage, bridging the filesystem dependency without requiring application changes. |
| **Evidence** | `src/NzbDrone.Common/Disk/DiskProviderBase.cs`, `src/NzbDrone.Core/MediaCover/`, local file path management throughout NzbDrone.Core |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Mostly centralized data access through the BasicRepository pattern. All database operations go through `BasicRepository<T>` which wraps Dapper with consistent query patterns, caching, and entity mapping. Table mappings are centralized in `TableMapping.cs`. Some direct Dapper access exists in specialized repositories for complex queries, but the pattern is consistent. |
| **Gap** | Mostly centralized with some direct access in auxiliary code paths. A few repositories bypass BasicRepository for performance-critical queries using raw Dapper SQL. |
| **Recommendation** | Maintain the existing repository pattern. When migrating to Aurora, the Dapper/Npgsql data access layer requires minimal changes — connection strings point to the Aurora endpoint instead of a self-managed PostgreSQL instance. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/TableMapping.cs`, repository implementations in `src/NzbDrone.Core/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are partially managed. The CI/CD pipeline tests against PostgreSQL 14 and 15 explicitly. NuGet package `Npgsql 9.0.3` supports PostgreSQL 13-17. SQLite version is implicitly managed through the NuGet package. No explicit engine version pin exists in deployment configuration (users run whatever version they install), but the application's FluentMigrator compatibility targets are well-defined. |
| **Gap** | Versions not explicitly pinned in deployment — users can run any PostgreSQL version. No documented version-update procedure. Some CI coverage (PG 14, 15) but no explicit EOL tracking. |
| **Recommendation** | When deploying to Aurora, pin the engine version in IaC (e.g., `engine_version = "15.4"`). Document a version upgrade procedure with rollback plan. PostgreSQL 14 reaches EOL November 2026 — plan upgrade path to 15 or 16. |
| **Evidence** | `azure-pipelines.yml` (PostgreSQL 14, 15 in test containers), `src/NzbDrone.Core/Lidarr.Core.csproj` (Npgsql 9.0.3), FluentMigrator migrations |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the C# application layer. Database interactions use standard SQL via Dapper with no database-engine-specific extensions. FluentMigrator generates DDL that is compatible with both SQLite and PostgreSQL. The dual-database support (SQLite + PostgreSQL) inherently prevents proprietary SQL dependency. |
| **Gap** | N/A — no stored procedure or proprietary SQL dependency. |
| **Recommendation** | N/A — the application-layer logic pattern is ideal for database migration flexibility. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (80 FluentMigrator migrations with no stored procedures), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (standard SQL queries) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains no IaC provisioning AWS resources (`has_iac_provisioning_aws_resources=false`). CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | While the application has persistent data (SQLite/PostgreSQL databases, media files), there is no deployed AWS data-at-rest surface to evaluate. The application stores data on the user's local filesystem or user-managed PostgreSQL. Encryption at rest is determined by the host OS and user configuration (e.g., LUKS, FileVault, BitLocker), not by the application. No AWS KMS, S3 encryption, or RDS encryption configuration exists because no AWS infrastructure is provisioned by this repository. Evaluating SEC-Q2 against a self-hosted application with no cloud deployment artifacts produces a false positive. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API authentication uses a single static API key (configured at application startup) without token-based auth (OAuth2/JWT). The key can be provided via query parameter, custom header, or Bearer token header. Authentication is a simple string comparison with no hashing, no expiry, no rate limiting. Form-based login exists for the UI with username/password hashed via PBKDF2. |
| **Gap** | API key authentication without token-based auth. Single shared key grants full access — no per-user identity, no RBAC, no token expiry, no refresh mechanism. |
| **Recommendation** | Implement OAuth2/JWT authentication using Amazon Cognito (or integrate with an existing IdP). Replace the static API key with short-lived JWT tokens that carry user identity and scopes. Maintain API key support as a fallback for automation/scripting use cases but add rate limiting and key rotation. |
| **Evidence** | `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Lidarr.Http/Authentication/AuthenticationService.cs` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely with no external IdP integration. Users are stored in the local database via `UserRepository`. Authentication is handled by a custom `AuthenticationService` with password hashing (PBKDF2). No OIDC, SAML, Cognito, Okta, or any federated identity provider integration exists. The OAuth utilities in `src/NzbDrone.Common/OAuth/` are for outbound integration with external services (Spotify, etc.), not for inbound user authentication. |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. No SSO, no federated identity, no centralized user management. |
| **Recommendation** | Integrate with Amazon Cognito as the identity provider. Implement OIDC authentication flow for the web UI and token-based auth for the API. This enables SSO across *arr suite applications, centralized user management, and MFA support. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/Lidarr.Http/Authentication/AuthenticationService.cs` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials in source code or version control. Database credentials are provided via environment variables (`Lidarr__Postgres__Password`) or the runtime XML configuration file (not committed to git). API keys for external services (Spotify, indexers) are stored in the database. However, no secrets management service is used — credentials are in environment variables or the application's own config file without rotation, encryption, or audit trails. |
| **Gap** | No plaintext credentials in source, but production credentials are in environment variables or application config without rotation or centralized management. No Secrets Manager, no Vault, no encrypted parameter store. |
| **Recommendation** | When deploying to AWS, store all credentials (database passwords, API keys, service tokens) in AWS Secrets Manager with automated rotation. Use IAM roles for service-to-service authentication where possible. For the PostgreSQL password, configure Secrets Manager with RDS integration for automatic rotation. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (reads from config/env vars), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, no `.env` files in version control |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No evidence of compute hardening or patching strategy. The application is distributed as self-contained executables with a built-in self-update mechanism, but this is application-level patching only. No OS-level patching automation (SSM Patch Manager), no vulnerability scanning (Inspector/Snyk), no hardened base images. The self-update mechanism (`src/NzbDrone.Update/`) updates only the Lidarr application binaries. |
| **Gap** | No patching strategy beyond application self-update. No vulnerability scanning, no hardened images, no OS-level patching automation. |
| **Recommendation** | When containerized, use a hardened base image (e.g., AWS Bottlerocket for EKS nodes, or .NET runtime on Alpine/distroless for the application container). Enable ECR image scanning for vulnerability detection. Deploy SSM Patch Manager for any remaining EC2 instances. Integrate Snyk or AWS Inspector into the CI/CD pipeline. |
| **Evidence** | `src/NzbDrone.Update/` (application self-update only), no SSM, Inspector, or vulnerability scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud is integrated into the CI/CD pipeline for code quality and basic security analysis (both frontend and backend). However, there is no dedicated SAST tool, no DAST, no dependency vulnerability scanning (no Dependabot, no `dotnet list package --vulnerable`, no npm audit in pipeline), and no container scanning. SonarCloud provides some security rule coverage but is primarily a code quality tool. |
| **Gap** | SonarCloud for code quality but no dedicated SAST, no dependency scanning, no container scanning. No security gates blocking on critical findings. |
| **Recommendation** | Add dependency vulnerability scanning: configure Dependabot or GitHub Advanced Security for the .NET packages, add `npm audit` to the frontend build step. Add a dedicated SAST tool (Semgrep or CodeGuru Reviewer). When containerized, enable ECR image scanning. Configure pipeline gates to block on critical/high severity findings. |
| **Evidence** | `azure-pipelines.yml` (SonarCloudPrepare@3 tasks for frontend and backend), no Dependabot config, no `.snyk` file, no SAST tool configuration |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. The application uses NLog for structured logging and Sentry for error tracking, but there is no trace ID propagation, no OpenTelemetry instrumentation, no X-Ray SDK integration, and no correlation IDs across service boundaries. Request logging in `LoggingMiddleware` captures HTTP request metadata but without trace context. |
| **Gap** | No distributed tracing — no trace ID propagation, no request correlation across boundaries, no end-to-end visibility. |
| **Recommendation** | Integrate OpenTelemetry .NET SDK for distributed tracing. .NET 8.0 has first-class OpenTelemetry support via `System.Diagnostics.Activity`. Export traces to AWS X-Ray via the OTLP exporter. Add trace ID propagation headers (W3C TraceContext) for downstream HTTP calls to indexers and download clients. |
| **Evidence** | `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (NLog only), `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` (no trace context), no OpenTelemetry packages in any .csproj |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has basic health checks (`HealthCheckService`) that monitor system state (disk space, indexer connectivity, download client health, import errors) and alert through notifications. However, these are operational health checks, not SLO definitions. No formal SLOs (availability targets, latency percentiles, error budgets), no SLO monitoring, no error budget tracking. Basic availability detection exists through the health check system. |
| **Gap** | Basic availability/latency alarms via health checks but no formal SLO definitions. No error budget tracking, no latency percentile targets, no availability SLAs. |
| **Recommendation** | Define SLOs for critical user journeys: API response latency (p95 < 500ms), search availability (99.9%), import success rate (> 99%). Implement SLO monitoring using CloudWatch ServiceLevelObjective or a Prometheus-based system. Track error budgets to drive operational priorities. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`, `src/NzbDrone.Core/HealthCheck/HealthCheckBase.cs`, various health check implementations |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The application has no metrics emission framework — no CloudWatch PutMetricData, no Prometheus metrics, no StatsD, no custom dashboards. The only metrics-adjacent data is internal: health check status and log entries. There is no visibility into business outcomes (albums imported per hour, search hit rate, download success rate, notification delivery rate). |
| **Gap** | No custom metrics — no business outcome tracking, no operational dashboards, only default system-level data through logs. |
| **Recommendation** | Instrument business metrics using CloudWatch EMF (Embedded Metric Format) via the .NET SDK: track albums imported/hour, search requests/success rate, download completion rate, notification delivery success. Create CloudWatch dashboards for operational visibility. |
| **Evidence** | No metrics libraries in any .csproj, no CloudWatch SDK usage, no Prometheus/StatsD integration |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. The health check system provides binary pass/fail status but no threshold-based alerting, no anomaly detection, and no integration with external alerting systems (PagerDuty, OpsGenie). Notifications (Discord, Slack, email) are triggered by application events (grab, import, health issue) but these are user-facing notifications, not operational alerts with escalation policies. |
| **Gap** | No alerting configured — no anomaly detection, no threshold alarms, no escalation policies. Health checks notify users but don't page operators. |
| **Recommendation** | When deployed to AWS, configure CloudWatch Alarms for error rate spikes, latency degradation, and resource exhaustion. Enable CloudWatch Anomaly Detection on key metrics. Integrate with SNS → PagerDuty/OpsGenie for on-call escalation. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (binary health checks, no threshold-based alerting), notification system sends to user channels not ops channels |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No deployed workload found in this repo — deployment strategy cannot be assessed from source code alone. The application is distributed as self-hosted packages; deployment is performed by end-users installing on their own infrastructure. The CI/CD pipeline builds and packages but does not deploy. Deployment orchestration does not exist in this repo or a companion repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist and run in the CI pipeline. The `NzbDrone.Integration.Test` project tests API endpoints, download client interactions, and database operations. Tests run against PostgreSQL 14 and 15 in Docker containers. Automation tests (`NzbDrone.Automation.Test`) provide E2E coverage. Tests execute on multiple platforms (native, Docker/Alpine, FreeBSD). |
| **Gap** | Integration tests for primary workflows exist; some gaps in coverage. Automation tests exist but may not cover all critical user journeys comprehensively. |
| **Recommendation** | Expand integration test coverage to include all critical API workflows. Add contract tests if the API is consumed by third-party clients. Ensure integration tests cover the PostgreSQL path thoroughly (not just SQLite) since PostgreSQL would be the production database in a cloud deployment. |
| **Evidence** | `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Automation.Test/`, `azure-pipelines.yml` (Integration and Automation stages with PostgreSQL containers) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. The application has a self-update mechanism and health checks that notify users, but no machine-readable runbooks, no SSM Automation documents, no Lambda-based remediation, and no structured incident response workflow. Incident handling is entirely ad hoc. |
| **Gap** | No runbooks — incident response is entirely ad hoc with no automation, no documented procedures, no self-healing. |
| **Recommendation** | Create runbooks for common incidents: database connectivity loss, disk space exhaustion, indexer unavailability, download client failures. Implement as SSM Automation documents when deployed to AWS. Add self-healing for recoverable failures (automatic service restart, connection pool refresh). |
| **Evidence** | No runbook files found, no SSM automation documents, no incident response documentation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for monitoring configurations, no per-service dashboards, no named alarm owners, no SLO definitions with team attribution. The application is a single-team project with no formal observability governance. Health checks exist but have no ownership attribution or team-specific routing. |
| **Gap** | No observability ownership — no dashboards, no named owners, no team attribution for alerts or SLOs. |
| **Recommendation** | When deploying to AWS, establish observability ownership: define CODEOWNERS for CloudWatch dashboards and alarms, assign named owners to each alarm, create per-service dashboards with team tags. Use CloudWatch cross-account observability if multiple teams operate the service. |
| **Evidence** | No CODEOWNERS file referencing observability, no dashboard definitions, no alarm ownership configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No AWS resources are provisioned by this repository (`has_iac_provisioning_aws_resources=false`). Resource tagging evaluation requires AWS infrastructure to assess. This application has no IaC and no cloud resources to tag. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

## Learning Materials

- **Move to Cloud Native:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Containers:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/)
- **Move to Modern DevOps:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `azure-pipelines.yml` | INF-Q1, INF-Q11, DATA-Q3, SEC-Q7, OPS-Q6 | Primary CI/CD pipeline — multi-platform build, test, SonarCloud analysis; no deploy stage |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2, SEC-Q5, APP-Q6 | Database connection management — env var configuration, no hardcoded credentials |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | APP-Q2, DATA-Q2, DATA-Q4 | Generic repository pattern — centralized data access via Dapper |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | INF-Q2 | Database creation and migration orchestration |
| `src/NzbDrone.Core/Datastore/PostgresOptions.cs` | INF-Q2 | PostgreSQL configuration via IOptions pattern |
| `src/NzbDrone.Core/Datastore/TableMapping.cs` | DATA-Q2 | Centralized entity-to-table mapping |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 80 FluentMigrator migrations — no stored procedures |
| `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | Static API key authentication — simple string comparison |
| `src/Lidarr.Http/Authentication/AuthenticationService.cs` | SEC-Q3, SEC-Q4 | Custom authentication with PBKDF2 password hashing |
| `src/NzbDrone.Core/Authentication/UserService.cs` | SEC-Q4 | Local user management — no external IdP |
| `src/NzbDrone.Core/Authentication/UserRepository.cs` | SEC-Q4 | User storage in local database |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | SEC-Q5 | Runtime XML config — credentials not in source |
| `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` | OPS-Q1 | NLog initialization — no trace context |
| `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` | OPS-Q1 | HTTP request logging — no distributed trace propagation |
| `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` | OPS-Q2, OPS-Q4 | Health monitoring system — binary pass/fail, no SLOs |
| `src/NzbDrone.Host/Startup.cs` | INF-Q6, APP-Q1 | ASP.NET Core startup — Kestrel direct exposure |
| `src/NzbDrone.Host/Bootstrap.cs` | INF-Q7 | Single-process bootstrap — no scaling |
| `src/NzbDrone.Common/Options/ServerOptions.cs` | INF-Q5, INF-Q6, APP-Q6 | Configurable bind address and port |
| `src/NzbDrone.Core/Messaging/Events/` | INF-Q4, APP-Q3 | Internal event aggregator — in-process pub/sub |
| `src/NzbDrone.Update/` | SEC-Q6 | Application self-update mechanism |
| `src/Lidarr.Api.V1/openapi.json` | APP-Q5 | Auto-generated OpenAPI 3.0 spec |
| `global.json` | APP-Q1 | .NET SDK version 8.0.405 |
| `src/Directory.Build.props` | APP-Q1 | Target framework net8.0 |
| `src/Lidarr.sln` | APP-Q2 | 15 projects in single solution |
| `distribution/` | INF-Q1 | Platform-specific distribution packages |
| `.devcontainer/devcontainer.json` | INF-Q1 | Dev container only — no production container |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test project |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | E2E automation test project |
| `src/NzbDrone.Core/Backup/BackupService.cs` | INF-Q8 | Manual backup — no automated scheduling |
| `src/NzbDrone.Common/Disk/DiskProviderBase.cs` | DATA-Q1 | Local filesystem data storage |
| `src/NzbDrone.Core/MediaCover/` | DATA-Q1 | Cover art stored locally |
| `package.json` | APP-Q1 | Frontend dependencies — React 18, TypeScript 5.7 |
| `src/NzbDrone.Core/Lidarr.Core.csproj` | DATA-Q3, APP-Q1 | NuGet dependencies including Npgsql 9.0.3 |
