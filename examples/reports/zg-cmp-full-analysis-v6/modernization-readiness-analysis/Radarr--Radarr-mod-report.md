# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | Radarr--Radarr |
| **Date** | 2025-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Movie collection manager (*arr suite). |
| **Overall Score** | 1.86 / 4.0 |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |

**Archetype Justification**: The application owns persistent state (SQLite/PostgreSQL databases), exposes CRUD API endpoints for movies, collections, and configuration, and manages entity lifecycle (movie status, monitored state). Classified as stateful-crud.

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 1.22 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.86 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF (9 questions evaluated; INF-Q3 and INF-Q9 Not Evaluated): (1+1+1+1+1+1+1+1+3) / 9 = 11/9 = 1.22
- APP (6 questions evaluated): (4+1+2+2+3+2) / 6 = 14/6 = 2.33
- DATA (4 questions evaluated): (2+3+2+4) / 4 = 11/4 = 2.75
- SEC (6 questions evaluated; SEC-Q2 Not Evaluated): (1+2+1+1+2+3) / 6 = 10/6 = 1.67
- OPS (9 questions evaluated): (1+1+2+1+1+3+1+1+1) / 9 = 12/9 = 1.33
- Overall: (1.22 + 2.33 + 2.75 + 1.67 + 1.33) / 5 = 9.30/5 = 1.86

---

## Classification

**Tier: Remediation Required**

This repo has 9 High findings, 5 Medium findings, 3 Low findings. The matched rule is "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. For MOD, 2-11 High findings map to Remediation Required.

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No cloud compute infrastructure — self-hosted desktop application with no container or serverless deployment | Prevents elastic scaling, automated recovery, and managed operations |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — all infrastructure (when deployed) would be manually configured | No reproducible deployments, no environment consistency, no disaster recovery |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or cloud audit logging — application runs self-hosted | No compliance audit trail, no forensic analysis capability |
| 4 | SEC-Q5: Secrets Management | 1 | Database credentials passed via environment variables without rotation or encryption | Credentials exposed in process environment; no automated rotation |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing — NLog provides basic logging but no trace propagation | No cross-request correlation; debugging production issues is guesswork |

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 3) and structured JSON responses detected — OpenAPI 3.0.4 spec at `src/Radarr.Api.V3/openapi.json` (12,842 lines) with full endpoint documentation.
- **What it enables:** An agent that discovers and invokes Radarr's REST API endpoints as tools — managing movies, triggering searches, monitoring queues, and configuring settings through natural language.
- **Additional steps:** The OpenAPI spec is already comprehensive. Agent could be implemented directly against the existing API surface.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (README, SECURITY.md, code comments, API spec, 140 migration files documenting schema evolution).
- **What it enables:** A knowledge agent that answers developer questions about the Radarr codebase, API contracts, database schema, and configuration options using existing documentation as a knowledge base.
- **Additional steps:** Index the OpenAPI spec, migration files, and code documentation. Consider adding developer guides.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3) — Azure Pipelines with multi-stage build, test, and analysis.
- **What it enables:** An agent that triggers builds, checks test results, manages release versions, and monitors pipeline health through the Azure DevOps API.
- **Additional steps:** Ensure Azure DevOps API tokens are available for agent access.
- **Effort:** Low

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed SQLite/PostgreSQL) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; contextual guard prevents trigger |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, OPS-Q5=1, OPS-Q6=2 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:** Radarr is a tightly-coupled monolith (APP-Q2=1) with a single deployable unit containing all business logic (movie management, download client integration, media processing, notifications, health checks) in a single ASP.NET Core process. All compute is self-hosted with no managed container orchestration (INF-Q1=1). Communication within the application is synchronous (APP-Q3=2). Long-running operations (media scanning, download processing) are handled with in-process background tasks (APP-Q4=2).

**Recommended Decomposition Approach:** Strangler Fig pattern — incrementally extract high-value services (download management, media processing, notification delivery) while keeping the core movie management monolith running.

**Representative AWS Services:** EKS (preferred per preferences), API Gateway, EventBridge (preferred), Step Functions, Aurora (preferred for PostgreSQL compatibility).

**Recommended Patterns:**
- Anti-corruption Layer between extracted services and the monolith
- Event Sourcing for movie state changes (added, downloaded, imported)
- Saga pattern for multi-step operations (search → download → import → organize)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:** No Dockerfile or container definitions exist in the repository. The application builds for multiple platforms (Windows, Linux, macOS, FreeBSD) as self-contained .NET executables. The dev container configuration (`mcr.microsoft.com/devcontainers/dotnet:1-8.0`) demonstrates .NET containerization is feasible.

**Container Readiness Indicators:**
- .NET 8 self-contained builds already produce platform-independent artifacts
- Port binding (7878) is configurable
- Configuration via environment variables (Postgres connection) already supported
- Multi-stage build pattern is straightforward for .NET 8

**Recommended Container Platform:** EKS (per preferences — `prefer: ["eks"]`)

**Representative AWS Services:** EKS, ECR, Fargate

**Migration Approach:** Lift-and-containerize — create a Dockerfile based on the existing .NET 8 runtime, externalize remaining configuration, and deploy to EKS.

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** The application uses SQLite (embedded, default) and PostgreSQL (optional, self-managed). SQLite is inherently self-managed with no automated failover, backup, or scaling. PostgreSQL when used is configured via environment variables pointing to a user-managed instance.

**Recommended Migration Target:** Aurora PostgreSQL (per preferences — `prefer: ["aurora"]`)

**Representative AWS Services:** Aurora PostgreSQL, RDS PostgreSQL

**Migration Tools:** AWS DMS for data migration; schema is already compatible (FluentMigrator supports PostgreSQL natively).

**Benefits:** Automated backups, point-in-time recovery, Multi-AZ failover, automated patching, read replicas for scaling.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10=1):** Zero infrastructure defined in code. When deployed to cloud, all infrastructure would be manually provisioned.
- **Deployment Strategy (OPS-Q5=1):** No deployment strategy exists — the application relies on a self-update mechanism. No blue/green, canary, or rolling deployments.
- **Integration Testing (OPS-Q6=2):** Integration tests exist and run in CI but are focused on application correctness, not deployment verification.

**Recommended DevOps Toolchain:**
- IaC: CDK or Terraform for EKS cluster, Aurora, networking
- CI/CD: Existing Azure Pipelines can be extended with deployment stages, or migrate to CodePipeline
- Deployment: CodeDeploy with EKS for blue/green deployments
- Observability: CloudWatch, X-Ray for distributed tracing

**Representative AWS Services:** CodePipeline, CodeBuild, CodeDeploy, CloudFormation/CDK, X-Ray, CloudWatch

---

## Decomposition Strategy

Since APP-Q2 scores 1 (tightly-coupled monolith), this section provides concrete decomposition guidance.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Recommended — the monolith has identifiable functional areas (movie management, download clients, notifications, media files) that can be extracted incrementally | Medium to High | ✅ **Recommended.** Extract high-traffic/high-change services first while keeping the core running. |
| **Conditional / Adaptive** | If team capacity is limited — containerize as-is first, then selectively extract services based on business priority | Low to Medium | ✅ **Recommended as starting point** given current state (no containerization). Containerize first, then decompose. |
| **Big-Bang Rewrite** | Not applicable — the codebase is functional, mature, and actively maintained | Very High | ⚠️ **Recommended against.** The monolith works; incremental extraction is safer. |

### Recommended: Conditional/Adaptive → Strangler Fig

Given the current state (no containerization, no IaC, no cloud deployment), the recommended path is:

1. **Phase 1:** Containerize the monolith as-is (create Dockerfile, deploy to EKS)
2. **Phase 2:** Add IaC for EKS cluster, Aurora PostgreSQL, networking
3. **Phase 3:** Extract high-value services using Strangler Fig:
   - Notification Service (event-driven, clear boundary)
   - Download Client Manager (async operations, external integrations)
   - Media File Processor (long-running, CPU-intensive)

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate new services from monolith's data model | Every extraction — translate between service and monolith models |
| **Saga Pattern** | Manage distributed transactions | Movie import workflow (search → download → import → organize) |
| **Event Sourcing** | Capture movie state changes as events | Movie lifecycle events fed through EventBridge |
| **Hexagonal Architecture** | Structure each extracted service | Every new service — ensures testability and portability |

### Effort Estimation Factors

| Factor | Current State | Effort Signal |
|--------|--------------|---------------|
| Module boundaries | No clear service boundaries — all logic in NzbDrone.Core | High |
| Data coupling | Single shared database with cross-domain queries | High |
| Stored procedures | None — all logic in application layer | Low |
| Communication patterns | Synchronous in-process; SignalR for real-time | Medium |
| CI/CD maturity | Azure Pipelines with build/test; no deploy stages | Medium |
| Test coverage | 10 test projects including integration tests | Low (good) |

---

## Detailed Findings

### Infrastructure & DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure exists. The application is distributed as self-contained .NET 8 executables for multiple platforms (win-x64, linux-x64, osx-x64, etc.) and runs as a self-hosted service. No ECS, EKS, Lambda, Fargate, or EC2 resources are defined in IaC or deployment configs. |
| **Gap** | All compute is self-hosted with no cloud deployment model. There is no elastic scaling, automated recovery, or managed operations. |
| **Recommendation** | Containerize the application and deploy to EKS (preferred). Create a Dockerfile using the .NET 8 runtime base image, externalize configuration, and define Kubernetes deployment manifests. |
| **Evidence** | No Dockerfile found; no IaC files; `src/NzbDrone.Console/Radarr.Console.csproj` targets self-contained exe; `azure-pipelines.yml` produces platform-specific packages (tar.gz, zip) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. SQLite is the default embedded database (System.Data.SQLite 2.0.2). PostgreSQL is supported as an optional backend via Npgsql 9.0.3, configured through environment variables (`Radarr__Postgres__Host/Port/User/Password`). Neither uses a managed database service. |
| **Gap** | No managed database service. SQLite has no failover, limited concurrency, and no automated backups. PostgreSQL when used is self-managed with manual patching and backup responsibility. |
| **Recommendation** | Migrate to Aurora PostgreSQL (preferred per preferences). The application already supports PostgreSQL natively via FluentMigrator. Aurora provides automated backups, Multi-AZ failover, and read replicas. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`; `src/NzbDrone.Core/Datastore/PostgresOptions.cs`; `src/NzbDrone.Core/Radarr.Core.csproj` (System.Data.SQLite, Npgsql packages) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateful-crud`. While the application has multi-step operations (movie search → download → import → organize), these are implemented as in-process command/event handlers using a custom event aggregator pattern. For a self-hosted desktop application, this is a reasonable design. However, if migrated to cloud-native architecture, workflow orchestration (Step Functions) would benefit the import pipeline. Since the current deployment model has no cloud workflows to evaluate, this question is not scored. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/` — custom command executor pattern; `src/NzbDrone.Core/Messaging/Events/` — in-process event aggregator |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure exists. The application uses an in-process event aggregator (`IEventAggregator`) and SignalR for real-time browser notifications. Cross-service state changes are handled synchronously within the monolith. No SQS, SNS, EventBridge, Kafka, or any external messaging system is used. |
| **Gap** | No async messaging infrastructure for cross-service communication. All operations are synchronous in-process calls. If decomposed into services, this would create tight coupling. |
| **Recommendation** | When migrating to cloud-native architecture, introduce EventBridge (preferred per preferences) for event-driven communication between extracted services. Use SQS for durable message queues where ordering matters (download queue management). |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`; `src/NzbDrone.SignalR/`; no `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*` in any file |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnets, security groups, or network segmentation is defined. The application runs as a self-hosted service binding directly to a configured port (default 7878). There is basic network access control in `src/NzbDrone.Host/AccessControl/` but no cloud network security infrastructure. |
| **Gap** | No cloud network security. When deployed, the service would need private subnets, security groups, and proper network segmentation. |
| **Recommendation** | Define VPC with private subnets for the application and database tiers. Use security groups for least-privilege access. Deploy API Gateway or ALB as the public entry point. |
| **Evidence** | No IaC files; `src/NzbDrone.Host/AccessControl/` (basic access control); `src/NzbDrone.Host/Startup.cs` (binds to port, configures forwarded headers for RFC private networks) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront is configured. The application exposes its REST API directly on port 7878 with no external entry point providing throttling, auth offload, or request validation. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, no centralized auth, no request validation at the edge. |
| **Recommendation** | Deploy API Gateway (preferred per preferences) as the entry point with throttling, API key validation, and request validation. Use the existing OpenAPI spec to configure API Gateway routes. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (direct HTTP binding); `src/Radarr.Api.V3/openapi.json` (default server: localhost:7878); no `aws_api_gateway_*` or `aws_lb_*` resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling mechanisms configured. The application runs as a single process with no scaling capability. No ASG, ECS service scaling, or Lambda concurrency configuration exists. |
| **Gap** | All capacity is statically provisioned (single instance). No ability to respond to traffic spikes or scale down during low demand. |
| **Recommendation** | When containerized on EKS, configure Horizontal Pod Autoscaler (HPA) based on CPU/memory and custom metrics (queue depth, active downloads). Consider KEDA for event-driven scaling. |
| **Evidence** | No IaC files; single-process application model; no `aws_autoscaling_*` or `aws_appautoscaling_*` resources |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated backup configuration exists. SQLite databases are stored as local files with no backup automation. PostgreSQL when used relies on manual backup procedures. No AWS Backup plans, no PITR configuration, no cross-region replication. |
| **Gap** | No backup configuration found. A data loss event would wipe the application state (movie library, configuration, history). |
| **Recommendation** | Migrate to Aurora PostgreSQL which provides automated backups with configurable retention, PITR, and cross-region replication. For the transition period, implement automated SQLite backup via cron/scheduled tasks. |
| **Evidence** | `src/NzbDrone.Core/Datastore/` (file-based SQLite); no `aws_backup_plan`, no `backup_retention_period`, no `point_in_time_recovery` configuration |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. The application is a self-hosted desktop/server application with no cloud deployment artifacts. No IaC defines compute resources, and no Kubernetes manifests or Helm charts exist. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files; no Dockerfile; no Kubernetes manifests; no cloud deployment configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure is defined in IaC. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. All infrastructure (when deployed to cloud) would need to be manually provisioned. |
| **Gap** | No IaC — all infrastructure created manually (ClickOps). No reproducible deployments, no environment consistency, no DR capability. |
| **Recommendation** | Create IaC using CDK or Terraform to define the target cloud architecture: EKS cluster, Aurora PostgreSQL, VPC/networking, API Gateway, and supporting services. Start with the core infrastructure (VPC, database) and expand incrementally. |
| **Evidence** | No `.tf` files; no `cdk.json`; no CloudFormation templates; no `Chart.yaml`; no `kustomization.yaml` anywhere in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD automation exists via Azure Pipelines (1,244-line `azure-pipelines.yml`) with multi-stage pipeline: Setup → Build_Backend (Linux/Mac/Windows matrix) → Build_Frontend → Installer → Packages → Unit_Test → Integration → Automation → Analyze → Report_Out. GitHub Actions provides supplementary CI (`ci.yml`). The pipeline includes SonarCloud analysis, code coverage, and automated API docs generation. |
| **Gap** | CI/CD covers build and test extensively but has no deployment stages. There is no automated deployment to any environment — the pipeline produces artifacts (packages) but does not deploy them. IaC changes are not part of the pipeline (no IaC exists). |
| **Recommendation** | Extend the pipeline with deployment stages once IaC and containerization are in place. Add deployment to staging, integration testing against deployed environment, and production deployment with approval gates. |
| **Evidence** | `azure-pipelines.yml` (1,244 lines, 9 stages); `.github/workflows/ci.yml`; stages include Unit_Test, Integration (with Postgres 14/15), Automation, Analyze (SonarCloud + coverage) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application uses C# on .NET 8.0 (modern, LTS) with ASP.NET Core 8.0 for the backend and TypeScript 5.7.2 / React 18.3.1 for the frontend. .NET 8 is the current LTS release with first-class AWS SDK coverage (AWS SDK for .NET v3). The framework stack is modern: ASP.NET Core (not legacy .NET Framework), current Polly v8 resilience library, and modern NuGet packages. |
| **Gap** | None — the language/runtime/framework combination is fully modern with excellent AWS SDK support. |
| **Recommendation** | No action required. .NET 8 with ASP.NET Core is a cloud-native-ready stack. |
| **Evidence** | `global.json` (.NET SDK 8.0.405); `src/Directory.Build.props` (net8.0 target); `package.json` (TypeScript 5.7.2, React 18.3.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Tightly-coupled monolith with pervasive shared state. All business logic resides in `NzbDrone.Core` (a single massive library) with a single deployable unit (`NzbDrone.Console`). The application has no clear service boundaries — movie management, download client integration, notification delivery, media file processing, indexer management, and health checking all share a single database and in-process event aggregator. Cross-domain coupling is evident: movies reference download clients, download clients reference media files, notifications reference all domains. |
| **Gap** | Single deployable unit with pervasive shared state. Cannot independently scale, deploy, or evolve subsystems. Team velocity limited by monolith coupling. |
| **Recommendation** | Begin with containerization (Conditional approach), then progressively extract services via Strangler Fig. Priority extraction candidates: Notification Service, Download Client Manager, Media File Processor. See Decomposition Strategy section. |
| **Evidence** | Single solution `src/Radarr.sln`; all business logic in `src/NzbDrone.Core/`; single entry point `src/NzbDrone.Console/`; shared `IDatabase` across all repositories; `IEventAggregator` couples all domains |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Communication is primarily synchronous within the monolith. The in-process event aggregator provides fire-and-forget messaging patterns within the application, and SignalR provides async real-time notifications to the frontend. However, all external integrations (indexers, download clients, metadata providers) are synchronous HTTP calls. Background tasks (scheduled commands) provide some async processing but are not decoupled from the monolith. |
| **Gap** | No managed async messaging for cross-boundary operations. External integrations are synchronous HTTP with no queue-based decoupling. If one external service is slow, it blocks the calling thread. |
| **Recommendation** | When decomposing into services, introduce EventBridge for cross-service events and SQS for durable command queues. The existing event aggregator pattern maps well to cloud-native events. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` (in-process); `src/NzbDrone.SignalR/` (browser notifications); HTTP clients in `src/NzbDrone.Core/` for indexers, download clients, metadata |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some background job processing exists but patterns are inconsistent. The application uses a custom command executor (`IExecute<T>`) for background operations like disk scanning, RSS sync, and download processing. These run in-process on background threads with no external job queue or status polling API. Long-running operations (media file scanning, bulk imports) block the command queue sequentially. |
| **Gap** | No external job infrastructure. Long-running operations run in-process with no timeout management, no external status tracking, and no ability to distribute work across instances. |
| **Recommendation** | Implement background job processing using SQS + Step Functions for multi-step operations. The existing command pattern (`IExecute<T>`) maps naturally to SQS message handlers with Step Functions orchestrating multi-step workflows. |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/` (custom command executor); `src/NzbDrone.Core/Jobs/` (scheduled tasks); no external job queue; no `/api/v3/command/{id}/status` polling endpoint (commands are fire-and-forget via SignalR notifications) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Consistent API versioning via URL path (`/api/v3/`). All API controllers in `Radarr.Api.V3` serve under the v3 prefix. The OpenAPI spec documents version 3.0.0. The versioning convention is applied uniformly across all endpoints. |
| **Gap** | Versioning strategy exists and is consistently applied (v3), but there is no evidence of backward compatibility guarantees, deprecation policies, or version migration documentation. Only a single version (v3) is currently active. |
| **Recommendation** | Document API versioning policy including backward compatibility commitments and deprecation timeline. This becomes critical when the API is consumed by third-party clients and agents. |
| **Evidence** | `src/Radarr.Api.V3/openapi.json` (version 3.0.0, paths under `/api/v3/`); all controllers in `src/Radarr.Api.V3/` namespace |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses environment variables for external service endpoints (PostgreSQL connection via `Radarr__Postgres__Host/Port`). Download clients, indexers, and notification services are configured via the application's settings UI and stored in the database. There is no dynamic service discovery mechanism. |
| **Gap** | Environment variables for database endpoint; all other service endpoints stored in application database configuration. No dynamic discovery — adding or moving a service requires manual configuration change. |
| **Recommendation** | When deploying to EKS, leverage Kubernetes service discovery (DNS-based) for internal services. Use AWS Service Discovery or VPC Lattice for cross-service communication. |
| **Evidence** | `src/NzbDrone.Core/Datastore/PostgresOptions.cs` (env var config); download client/indexer/notification configs stored in database; no Consul, Service Discovery, or Istio configuration |

---

### Data Platform

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Media cover images, movie posters, and metadata are stored on the local file system. The application manages media files (movies) on local/network storage paths. No S3 or managed object storage is used. Image processing uses SixLabors.ImageSharp for resizing/caching locally. |
| **Gap** | Data in local file system storage with limited accessibility. Not stored in managed object storage (S3). No parsing pipeline for movie metadata extraction. |
| **Recommendation** | Migrate media covers and metadata to S3. Use S3 File Gateway for compatibility with existing file-path-based access patterns. Consider Textract or Rekognition for automated movie poster/artwork analysis. |
| **Evidence** | `src/NzbDrone.Core/MediaCover/` (local file storage); SixLabors.ImageSharp in dependencies; root folder configuration points to local/network paths |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | A mostly centralized data access layer exists using the `BasicRepository<TModel>` generic repository pattern with Dapper. All database operations go through repositories that inherit from `BasicRepository`. Custom SQL builders (`SqlBuilder.cs`, `WhereBuilder.cs`) provide a consistent query construction pattern. Platform-specific builders exist for SQLite and PostgreSQL. |
| **Gap** | Mostly centralized but some direct database access may exist in auxiliary code paths. The custom SQL builder pattern is consistent within the repository layer but requires knowledge of both SQLite and PostgreSQL SQL dialects. |
| **Recommendation** | Maintain the centralized repository pattern. When migrating to Aurora PostgreSQL, the PostgreSQL-specific `WhereBuilderPostgres.cs` provides the correct query path — remove SQLite-specific code paths post-migration. |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`; `src/NzbDrone.Core/Datastore/SqlBuilder.cs`; `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs`; `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SQLite version is pinned in the NuGet package (System.Data.SQLite 2.0.2 — current, not approaching EOL). PostgreSQL versions are not pinned in the application — the application connects to whatever PostgreSQL instance is configured. CI/CD tests against PostgreSQL 14 and 15 (both within support window). No documented version-update procedure exists. |
| **Gap** | PostgreSQL version is not pinned or managed by the application. No documented version-update procedure covering downtime, rollback, or risk. Dependence on user-managed PostgreSQL means version lifecycle is not controlled. |
| **Recommendation** | When migrating to Aurora PostgreSQL, pin the engine version in IaC and document upgrade procedures. Aurora handles minor version upgrades automatically; major version upgrades should be planned with rollback strategy. |
| **Evidence** | `src/NzbDrone.Core/Radarr.Core.csproj` (System.Data.SQLite 2.0.2); `azure-pipelines.yml` (tests with postgres:14 and postgres:15); no version pinning in application config |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the application layer (C#). The 140 FluentMigrator migrations use standard DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX) without any stored procedure definitions. Query logic uses Dapper with standard SQL compatible with both SQLite and PostgreSQL. |
| **Gap** | None — the database is used purely for storage with all logic in the application layer. |
| **Recommendation** | No action required. The absence of stored procedures makes database migration straightforward. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (140 migrations, all DDL); `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Dapper queries, no stored procedure calls); no `.sql` files with CREATE PROCEDURE/TRIGGER/FUNCTION |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud audit logging exists. The application logs HTTP requests via `LoggingMiddleware.cs` (request method, path, status code, duration) to local log files using NLog. Auth events are logged to a separate "Auth" logger. However, there is no immutable audit trail, no centralized log collection, and no compliance-grade logging. |
| **Gap** | No CloudTrail or equivalent audit logging. Local log files are mutable, not centrally collected, and not suitable for forensic analysis or compliance. |
| **Recommendation** | When deployed to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Forward application logs to CloudWatch Logs with retention policies. |
| **Evidence** | `src/Radarr.Http/Middleware/LoggingMiddleware.cs` (local NLog logging); `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (file-based log targets); no CloudTrail configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no cloud database, S3 bucket, EBS volume, or similar managed storage is defined. The application stores data on local filesystems where encryption is an OS/disk-level concern, not an application-level one. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC defining storage resources; local file-based SQLite; no `aws_s3_bucket`, `aws_rds_*`, or EBS volume definitions |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API key authentication is implemented via `ApiKeyAuthenticationHandler.cs`. The API key can be provided via `X-Api-Key` header, query parameter, or `Authorization: Bearer` header. This is static credential authentication — a single API key shared across all clients with no per-user identity, no token expiration, and no OAuth2/JWT. |
| **Gap** | API key (static credential) authentication without token-based auth (OAuth2/JWT). No per-request identity, no token rotation, no fine-grained authorization. Simple string comparison for validation without timing-safe comparison. |
| **Recommendation** | When deploying behind API Gateway, implement Cognito user pools or OAuth2/JWT for per-user authentication. Use API Gateway authorizers for token validation. The existing API key can remain as a machine-to-machine credential for backward compatibility. |
| **Evidence** | `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (simple string comparison); `src/Radarr.Http/Authentication/AuthenticationService.cs`; no OAuth2/OIDC/JWT configuration |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. User credentials are stored in the local database via `UserRepository.cs` and `UserService.cs`. Password hashing uses `Microsoft.AspNetCore.Cryptography.KeyDerivation`. There is no integration with any external identity provider (Cognito, Okta, OIDC, SAML). Authentication types include Forms auth and API key — both self-managed. |
| **Gap** | Application manages its own authentication with no external IdP integration. No SSO, no federation, no centralized identity. Each Radarr instance manages its own user database independently. |
| **Recommendation** | Integrate with Cognito (or preferred IdP) for centralized identity management. Support OIDC/SAML federation for SSO. This enables consistent access policies across the *arr suite and other services. |
| **Evidence** | `src/NzbDrone.Core/Authentication/UserRepository.cs`; `src/NzbDrone.Core/Authentication/UserService.cs`; `Microsoft.AspNetCore.Cryptography.KeyDerivation` in dependencies; no OIDC/SAML/Cognito configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Database credentials are passed via environment variables (`Radarr__Postgres__Host`, `Radarr__Postgres__Port`, `Radarr__Postgres__User`, `Radarr__Postgres__Password`) without encryption or rotation. The CI/CD pipeline has credentials in pipeline variables (Discord webhook key, GitHub token, Sentry DSN). API keys are stored in the application database. No Secrets Manager or Vault integration exists. |
| **Gap** | Production credentials in plain environment variables without rotation. CI/CD secrets in pipeline variables (acceptable for CI but no rotation). No dedicated secrets management system. |
| **Recommendation** | Integrate AWS Secrets Manager for database credentials and API keys. Configure automated rotation for database passwords. Use Secrets Manager SDK to retrieve secrets at runtime rather than environment variables. |
| **Evidence** | `src/NzbDrone.Core/Datastore/PostgresOptions.cs` (plain env vars for credentials); `azure-pipelines.yml` (pipeline variables for tokens); no `aws_secretsmanager_*` resources; no HashiCorp Vault configuration |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses SonarCloud for static analysis (SAST) in the CI/CD pipeline, and StyleCop.Analyzers for code quality. Sentry provides runtime error tracking. However, there is no infrastructure-level patching strategy (no SSM Patch Manager, no hardened base images). Dependabot is configured but only tracks devcontainers — not NuGet or npm dependencies. |
| **Gap** | No infrastructure patching strategy (no managed compute to patch). Dependency vulnerability scanning is minimal — Dependabot does not track NuGet or npm packages. No container image scanning (no containers exist). |
| **Recommendation** | Enable Dependabot for NuGet and npm ecosystems. When containerized, use hardened base images (e.g., .NET runtime-deps on Alpine) and enable ECR image scanning. Configure SSM Patch Manager for any EC2 instances. |
| **Evidence** | `azure-pipelines.yml` (SonarCloud analysis); `.github/dependabot.yml` (only devcontainers); `src/Directory.Build.props` (StyleCop.Analyzers); no `aws_ssm_patch_baseline` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | SonarCloud SAST is integrated into the CI/CD pipeline (Azure Pipelines) for both backend (C#) and frontend (JS/TS). Code coverage is collected via coverlet and published. StyleCop provides compile-time code analysis. However, there is no dependency vulnerability scanning in the pipeline (Dependabot only tracks devcontainers), and no container scanning. |
| **Gap** | SAST present (SonarCloud) but no dependency vulnerability scanning for NuGet/npm packages in the pipeline. No security gate blocking on critical findings. No container scanning (no containers). |
| **Recommendation** | Add `dotnet list package --vulnerable` and `yarn audit` steps to the pipeline. Configure SonarCloud quality gates to fail builds on critical security issues. When containerized, add ECR image scanning. |
| **Evidence** | `azure-pipelines.yml` (SonarCloudPrepare@4, SonarCloudAnalyze@4 tasks); `.github/dependabot.yml` (devcontainers only); no `npm audit` or `dotnet list package --vulnerable` in pipeline |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. The application uses NLog for structured logging with request sequence IDs (`LoggingMiddleware.cs`) but these are per-instance counters, not distributed trace IDs. No OpenTelemetry, X-Ray, or trace header propagation exists. Sentry provides error tracking but not distributed tracing. |
| **Gap** | No distributed tracing. No trace ID propagation across service boundaries. Debugging request flows through external services (indexers, download clients) requires manual log correlation. |
| **Recommendation** | Add OpenTelemetry SDK instrumentation for .NET. Propagate trace context (W3C traceparent) to external HTTP calls. When deployed to AWS, export traces to X-Ray. |
| **Evidence** | `src/Radarr.Http/Middleware/LoggingMiddleware.cs` (sequence IDs, not trace IDs); no OpenTelemetry in dependencies; no X-Ray SDK; no `traceparent` header propagation |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs are defined. No formal definition of acceptable latency, availability, or error rates for the API. The health check system monitors internal component health (indexers, download clients, disk space) but does not define or measure service-level objectives for user-facing journeys. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. No error budget tracking. Cannot measure whether the system is meeting user expectations or degrading. |
| **Recommendation** | Define SLOs for critical user journeys: API response latency (p99 < 500ms), availability (99.9%), movie search success rate. Implement using CloudWatch alarms and dashboards when deployed to AWS. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (component health, not SLOs); no SLO definitions in config or code; no error budget tracking |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application tracks some operational metrics internally (health check results, command execution status) but does not publish custom business metrics to any external system. The health check system provides a form of business monitoring (indexer status, download client health) but this is exposed only through the API, not as metrics/dashboards. |
| **Gap** | Infrastructure-only metrics (via health checks) with no published business outcome metrics. No custom CloudWatch metrics for movies added, downloads completed, import success rate, or search hit rate. |
| **Recommendation** | Publish business metrics to CloudWatch: movies added per day, successful imports, download completion rate, search success rate, queue depth. Create dashboards for operational visibility. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational health); `src/Radarr.Api.V3/Health/` (API exposure); no `cloudwatch.put_metric_data` or Prometheus metrics |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. Sentry provides error reporting with debouncing (`SentryDebounce.cs`) but this is crash reporting, not operational alerting. The health check system has no external alerting integration — results are only visible through the UI and API. Notifications can be sent (email, Discord) but only for media events, not operational anomalies. |
| **Gap** | No alerting configured for error rates, latency, or system health anomalies. Health check failures are visible only in the application UI. |
| **Recommendation** | When deployed to AWS, configure CloudWatch anomaly detection on API error rates and latency. Set up alarms with SNS notifications for critical health degradation. Integrate with PagerDuty or OpsGenie for on-call alerting. |
| **Evidence** | `src/NzbDrone.Common/Instrumentation/Sentry/` (crash reporting only); `src/NzbDrone.Core/HealthCheck/` (no external alerting); `src/NzbDrone.Core/Notifications/` (media events only) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The application uses a self-update mechanism (`NzbDrone.Update`) that downloads and replaces the binary in-place — a direct-to-production update with no staged rollout, no health checks during update, and no automated rollback. There is no blue/green, canary, or rolling deployment. |
| **Gap** | Direct-to-production replacement with no staged rollout. Self-update mechanism with no health verification during update. No ability to rollback automatically if the new version fails. |
| **Recommendation** | When containerized on EKS, implement rolling deployments with health check gates. Progress to blue/green via CodeDeploy for zero-downtime deployments. Configure automated rollback on health check failure. |
| **Evidence** | `src/NzbDrone.Update/` (self-update binary replacement); no CodeDeploy, Argo Rollouts, or traffic shifting configuration; no deployment health checks |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration testing exists. The `NzbDrone.Integration.Test` project runs integration tests against the full application stack on multiple platforms (Linux, Mac, Windows) and with both SQLite and PostgreSQL (14, 15). Integration tests run in the CI pipeline (Azure Pipelines Integration stage). Automation tests (`NzbDrone.Automation.Test`) provide UI-level end-to-end testing. |
| **Gap** | Integration tests cover application correctness well but do not test deployment scenarios (container health, startup probes, graceful shutdown). Some gaps in coverage — tests do not verify external service integration patterns under failure conditions. |
| **Recommendation** | Extend integration tests to cover container deployment scenarios (startup/shutdown, health probe responses, graceful connection draining). Add contract tests for external service integrations. |
| **Evidence** | `src/NzbDrone.Integration.Test/`; `src/NzbDrone.Automation.Test/`; `azure-pipelines.yml` (Integration stage with Postgres 14/15, multi-platform matrix, Docker alpine tests) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. No runbooks (human-readable or machine-readable), no self-healing automation, no Systems Manager Automation documents. The health check system detects issues but has no automated remediation — it only reports status through the UI and can send notifications (Discord, email) for media events, not operational incidents. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No self-healing automation. No documented procedures for common failure scenarios. |
| **Recommendation** | Create runbooks for common operational scenarios (database connectivity loss, disk space exhaustion, indexer failures). When deployed to AWS, implement SSM Automation documents for self-healing and Step Functions for incident response workflows. |
| **Evidence** | No runbook files; no SSM Automation documents; `src/NzbDrone.Core/HealthCheck/` (detection only, no remediation); `SECURITY.md` (vulnerability reporting only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No defined observability ownership. No per-service dashboards (monolith has no services to separate). No alarms with named owners. No CODEOWNERS for observability assets. No team attribution on monitoring configuration. The health check system is owned by the core application but there is no operational ownership model. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No dashboards, no alarm ownership, no team accountability for service health. |
| **Recommendation** | When deployed to AWS, establish observability ownership: define CODEOWNERS for monitoring configs, create per-domain dashboards (movies, downloads, imports), assign alarm ownership to team members. |
| **Evidence** | No CODEOWNERS file; no dashboard definitions; no alarm configurations; no team tags on resources |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists. No AWS resources are defined (no IaC), so no tagging governance is possible. No tagging standards, no cost allocation tags, no ownership tags. |
| **Gap** | No tags found on resources. No tagging standard exists. Cannot track costs, identify ownership, or enforce governance. |
| **Recommendation** | Establish a tagging standard before creating IaC: Environment, Service, Team, CostCenter as required tags. Enforce via `default_tags` in Terraform provider or CDK Aspects. Configure Tag Policies in AWS Organizations. |
| **Evidence** | No IaC files; no `default_tags`; no `required-tags` Config rules; no Tag Policies |

---

## Learning Materials

- **Move to Cloud Native:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Containers:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)
- **Move to Managed Databases:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Modern DevOps:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `azure-pipelines.yml` | INF-Q11, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q6 | Primary CI/CD pipeline (1,244 lines, 9 stages) |
| `.github/workflows/ci.yml` | INF-Q11 | Supplementary GitHub Actions CI |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Dependency update tracking (devcontainers only) |
| `src/NzbDrone.Console/Radarr.Console.csproj` | INF-Q1 | Main entry point, self-contained exe |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2 | SQLite/PostgreSQL connection management |
| `src/NzbDrone.Core/Datastore/PostgresOptions.cs` | INF-Q2, SEC-Q5 | Postgres credentials via env vars |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | DATA-Q2, DATA-Q4 | Generic repository pattern with Dapper |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q3, DATA-Q4 | 140 FluentMigrator migrations (DDL only) |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2 | Custom SQL query builder |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | DATA-Q2 | PostgreSQL-specific query construction |
| `src/NzbDrone.Core/Datastore/WhereBuilderSqlite.cs` | DATA-Q2 | SQLite-specific query construction |
| `src/NzbDrone.Core/Messaging/Events/` | INF-Q4, APP-Q2, APP-Q3 | In-process event aggregator |
| `src/NzbDrone.Core/Messaging/Commands/` | INF-Q3, APP-Q4 | Custom command executor pattern |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q4, OPS-Q7 | Application health check system |
| `src/NzbDrone.Core/Authentication/` | SEC-Q4 | Self-managed user auth |
| `src/NzbDrone.Core/MediaCover/` | DATA-Q1 | Local file-based media storage |
| `src/NzbDrone.SignalR/` | APP-Q3 | Real-time browser notifications |
| `src/NzbDrone.Update/` | OPS-Q5 | Self-update mechanism |
| `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key auth (string comparison) |
| `src/Radarr.Http/Middleware/LoggingMiddleware.cs` | OPS-Q1, SEC-Q1 | Request logging middleware |
| `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` | OPS-Q1, SEC-Q1 | NLog configuration, Sentry integration |
| `src/NzbDrone.Common/Instrumentation/Sentry/` | OPS-Q4 | Error reporting (not alerting) |
| `src/Radarr.Api.V3/openapi.json` | APP-Q5, INF-Q6 | OpenAPI 3.0.4 spec (12,842 lines) |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, APP-Q6 | ASP.NET Core startup, middleware pipeline |
| `src/NzbDrone.Host/AccessControl/` | INF-Q5 | Basic network access control |
| `global.json` | APP-Q1 | .NET SDK 8.0.405 |
| `src/Directory.Build.props` | APP-Q1, SEC-Q6 | net8.0 target, StyleCop analyzers |
| `package.json` | APP-Q1 | TypeScript 5.7.2, React 18.3.1 |
| `src/NuGet.config` | INF-Q11 | Package sources (NuGet.org + Azure DevOps feeds) |
| `src/Radarr.sln` | APP-Q2 | Single solution, 28 projects |
| `SECURITY.md` | OPS-Q7 | Security reporting policy |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test project |
| `src/NzbDrone.Automation.Test/` | OPS-Q6 | UI automation test project |
| `src/NzbDrone.Core/Notifications/` | OPS-Q4 | Media event notifications (not operational) |
