# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Lidarr--Lidarr |
| **Date** | 2025-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | Music collection manager (*arr suite). |
| **Overall Score** | 1.76 / 4.0 |

**Archetype Justification**: The application owns persistent state (SQLite/PostgreSQL databases storing artists, albums, tracks, history, user config) and exposes full CRUD operations on these business entities via a REST API. It is a self-hosted monolithic application managing entity lifecycles. Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false

> Note: `has_at_rest_data_surface` is `false` because no IaC defines cloud-managed storage (S3, RDS, EBS, etc.) — the database is local/embedded SQLite or user-provisioned PostgreSQL. `has_deployed_workload` is `false` because no IaC or container definitions define a cloud deployment — the app distributes as platform packages for self-hosting.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.33 / 4.0 | ❌ Not Present | Critical |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present | Critical |
| **Overall** | **1.76 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+1+2+1+1+1+1+3) / 9 = 12/9 = 1.33 — INF-Q8 and INF-Q9 excluded (surface-gated: has_at_rest_data_surface=false, has_deployed_workload=false)
- APP: (4+1+2+2+2+2) / 6 = 13/6 = 2.17 — APP-Q3 and APP-Q4 evaluated normally for stateful-crud archetype
- DATA: (1+3+2+4) / 4 = 10/4 = 2.50
- SEC: (1+2+1+2+2+2) / 6 = 10/6 = 1.67 — SEC-Q2 excluded (surface-gated: has_at_rest_data_surface=false)
- OPS: (1+1+1+1+1+2+1+1+1) / 9 = 10/9 = 1.11
- Overall: (1.33+2.17+2.50+1.67+1.11) / 5 = 8.78/5 = 1.76

**Classification:** 🟠 Remediation Required

This repo has 9 High findings, 21 Medium findings, 1 Low findings. Rule matched: "2-11 High → Remediation Required."

MOD classification note: Unlike ARA (Agentic Readiness Assessment) where 1 High is a deployment blocker due to agent safety concerns, MOD treats 1 High as a single modernization gap mapping to Pilot-Ready. The Remediation Required tier is triggered here by 9 High findings indicating multiple fundamental modernization gaps that must be addressed before cloud-native operation.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute — application distributes as self-hosted platform packages with no cloud compute infrastructure | Blocks containerization, auto-scaling, and cloud-native deployment |
| 2 | INF-Q10: Infrastructure as Code | 1 | No IaC exists — all infrastructure (if any) is manually provisioned by end users | Prevents reproducible deployments, environment consistency, and automated DR |
| 3 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith with shared database, extensive cross-module dependencies | Limits independent scaling, deployment velocity, and team autonomy |
| 4 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing or OpenTelemetry instrumentation | Cannot trace request flows or diagnose performance issues in production |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or cloud audit logging infrastructure | No compliance-grade audit trail for API actions or system changes |

---

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 2) — OpenAPI 3.0.4 specification available at `src/Lidarr.Api.V1/openapi.json` with comprehensive endpoint documentation and structured JSON responses.
- **What it enables:** An agent that can discover and invoke Lidarr's REST API endpoints as tools — managing artists, albums, searches, downloads, and system operations programmatically.
- **Additional steps:** The OpenAPI spec is already machine-readable. Agent integration would require exposing the spec at a discoverable endpoint and implementing proper API key auth delegation.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — README.md, CONTRIBUTING.md, SECURITY.md, extensive wiki at wiki.servarr.com, and 80+ database migration files documenting schema evolution.
- **What it enables:** A knowledge agent that indexes Lidarr's documentation and code to answer developer questions about the codebase, API usage, and troubleshooting.
- **Additional steps:** Would need to index external wiki content (wiki.servarr.com) alongside repo docs. Code comments and migration history provide schema documentation.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no Dockerfile or container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected (SQLite+PostgreSQL are open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed databases), DATA-Q3=2 (versions not pinned in IaC) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected; application is a media manager, not an analytics system |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), OPS-Q5=1 (no deployment strategy), OPS-Q6=2 (integration tests exist but not deployed) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:** Lidarr is a tightly-coupled monolith (APP-Q2=1) with all business logic in a single deployable unit (NzbDrone.Core), a single shared database, and cross-cutting concerns woven throughout. The application runs on self-hosted compute with no managed cloud infrastructure.

**Gaps Identified:**
- Single deployable unit with 2,300+ C# files in one core project
- Shared SQLite/PostgreSQL database with 80+ migration files managing all tables
- Internal event aggregator (IEventAggregator/IHandle<T>) provides some decoupling but remains in-process
- All communication is synchronous within the monolith

**Recommended Decomposition Approach:** See Decomposition Strategy section below.

**Representative AWS Services:** ECS/EKS (prefer EKS per preferences), API Gateway, EventBridge, Aurora PostgreSQL, Step Functions

**Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing (for download/import history)

**Learning Materials:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:** No Dockerfile or container definitions exist. The application distributes as platform-specific packages (zip/tar.gz for 11 runtime identifiers). Docker is used only in CI for testing. A dev container exists for development purposes only.

**Container Readiness Indicators:**
- .NET 8 is container-ready with official Microsoft base images
- Application already supports environment variable configuration (`Lidarr__` prefix)
- External PostgreSQL support exists (not just embedded SQLite)
- Cross-platform build already targets linux-x64, linux-arm64, linux-musl-x64

**Recommended Platform:** EKS (per preferences: prefer EKS) with Fargate for initial deployment simplicity.

**Immediate Actions:**
1. Create a Dockerfile using `mcr.microsoft.com/dotnet/aspnet:8.0` base image
2. Externalize all configuration to environment variables (partially done)
3. Switch default database to PostgreSQL (Aurora) for production container deployments
4. Create Helm chart for EKS deployment

**Representative AWS Services:** EKS, ECR, Fargate, App Runner

**Learning Materials:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** Databases are entirely self-managed. The default is embedded SQLite (no server at all). PostgreSQL is optional and user-provisioned. No IaC defines any database infrastructure. Connection strings are configured via environment variables without managed service integration.

**Database Topology:**
- SQLite: embedded, single-file, no HA, no backup automation
- PostgreSQL 14/15: optional, user-provisioned, no managed failover

**Recommended Target:** Aurora PostgreSQL (per preferences: prefer Aurora). The application already has PostgreSQL support with Npgsql driver and PostgreSQL-specific query builders.

**Migration Path:**
1. Containerize the application (prerequisite)
2. Deploy Aurora PostgreSQL cluster with Multi-AZ
3. Configure connection strings to Aurora endpoints via environment variables
4. Enable automated backups, PITR, and automated failover
5. Phase out SQLite support for cloud deployments

**Representative AWS Services:** Aurora PostgreSQL, RDS, DynamoDB (for metadata/caching if needed)

**Learning Materials:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC:** None — no Terraform, CloudFormation, CDK, or Helm charts for deployment infrastructure
- **CI/CD:** Azure DevOps Pipelines provides comprehensive build/test automation but no deployment pipeline to cloud infrastructure
- **Deployment Strategy:** No deployment strategy — the pipeline produces packages but does not deploy them to any managed environment
- **Testing:** Integration tests exist (NzbDrone.Integration.Test) and run in CI, but test no cloud deployment

**Recommended DevOps Toolchain:**
1. **IaC:** CDK or Terraform for Aurora, EKS, networking, and operational resources
2. **CI/CD Deployment:** Extend existing pipeline (or migrate to CodePipeline) with deploy-to-EKS stage
3. **Deployment Strategy:** Implement blue/green or canary deployments via CodeDeploy or ArgoCD on EKS
4. **Integration Testing:** Run integration tests against deployed cloud environment in pipeline

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation/CDK, EKS + ArgoCD

**Learning Materials:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

APP-Q2 scored 1 (tightly-coupled monolith). The following decomposition guidance applies.

### Recommended Approach: Conditional / Adaptive

**Rationale:** Given that Lidarr is a self-hosted desktop/server application with P2 priority, the conditional/adaptive approach is most appropriate:
1. **Containerize first** — Package the monolith as-is into a container (lift-and-containerize)
2. **Selectively extract** — Based on business priority, extract high-value bounded contexts as independent services over time

This approach is recommended over full Strangler Fig because:
- The application is functional and actively maintained
- Not all modules need independent scaling (e.g., media file management is tightly coupled to local disk access)
- Team capacity should focus on cloud enablement before full decomposition

### Candidate Bounded Contexts for Extraction

| Context | Current Location | Extraction Value |
|---------|-----------------|------------------|
| Indexer/Search | `NzbDrone.Core/Indexers/`, `NzbDrone.Core/IndexerSearch/` | High — independent scaling for search workloads |
| Download Management | `NzbDrone.Core/Download/` | Medium — could run as async worker |
| Notifications | `NzbDrone.Core/Notifications/` | High — event-driven, stateless |
| Import Lists | `NzbDrone.Core/ImportLists/` | Medium — external API integrations |
| Metadata Source | `NzbDrone.Core/MetadataSource/` | Medium — external API calls to MusicBrainz |

### Pattern Recommendations

| Pattern | Application |
|---------|-------------|
| **Anti-corruption Layer** | Between extracted services and the monolith's shared database |
| **Event Sourcing** | For download history and import tracking (already has History table) |
| **Saga Pattern** | For the search → download → import → organize workflow |
| **Hexagonal Architecture** | For each extracted service — already partially present with DI container |

### Effort Estimation

| Factor | Signal | Assessment |
|--------|--------|------------|
| Module boundaries | Identifiable namespaces but heavy cross-dependencies via DI | Moderate effort |
| Data coupling | Single shared database with all 80 migrations in one project | High effort |
| Stored procedures | None — all logic in application layer | Low effort |
| Communication patterns | In-process event aggregator (IHandle<T>) — not distributed | Moderate effort |
| CI/CD maturity | Strong build pipeline but no deployment pipeline | Moderate effort |
| Test coverage | Integration tests exist | Low effort |

**Overall Decomposition Effort:** High — primarily driven by data coupling and the need to establish cloud infrastructure before extraction.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is self-managed by end users. The application distributes as platform-specific packages (zip, tar.gz, Windows installer) for 11 runtime identifiers. No managed container orchestration (ECS/EKS), no serverless (Lambda), no cloud compute infrastructure defined. Docker is used only in CI for testing, not for deployment. |
| **Gap** | No managed compute whatsoever — the application has no cloud deployment model. |
| **Recommendation** | Containerize the application using the existing .NET 8 runtime and deploy to EKS (preferred) with Fargate. The application already supports Linux runtime identifiers and environment variable configuration. |
| **Evidence** | `azure-pipelines.yml` (build targets), absence of Dockerfile, `src/NzbDrone.Host/Bootstrap.cs` (self-hosted Kestrel), `distribution/` directory (platform packages) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Databases are entirely self-managed. The default is embedded SQLite (single file on local disk). PostgreSQL is optional and user-provisioned via environment variables (`Lidarr__Postgres__Host`, etc.). No managed database service (RDS, Aurora, DynamoDB) is configured or referenced. |
| **Gap** | All databases are self-managed with no automated failover, no managed backups, no managed scaling. |
| **Recommendation** | Migrate to Aurora PostgreSQL (preferred). The application already has full PostgreSQL support via Npgsql driver with PostgreSQL-specific query builders (`WhereBuilderPostgres.cs`). Deploy Aurora with Multi-AZ and automated backups. |
| **Evidence** | `src/NzbDrone.Core/Datastore/DbFactory.cs`, `src/NzbDrone.Core/Datastore/DatabaseConnectionInfo.cs`, `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application has multi-step workflows (search → download → import → organize → notify) that are entirely hardcoded in application logic. The `CommandExecutor` pattern dispatches commands synchronously. The RSS sync → decision engine → download → import pipeline is implemented as direct method calls chained through the DI container. No dedicated workflow orchestration service (Step Functions, Temporal, or equivalent) is used. |
| **Gap** | Multi-step business workflows exist (search-download-import-organize is a core pipeline) and are entirely hardcoded with no orchestration primitives, retry logic, or visual workflow management. |
| **Recommendation** | For a cloud-native deployment, extract the download-import-organize pipeline into AWS Step Functions (preferred over self-managed orchestration). This would provide retry logic, error handling, and visibility into long-running import operations. |
| **Evidence** | `src/NzbDrone.Core/IndexerSearch/`, `src/NzbDrone.Core/Download/`, `src/NzbDrone.Core/MediaFiles/`, `src/NzbDrone.Core/Jobs/` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses an in-process event aggregator (`IEventAggregator`, `IHandle<T>`) for internal pub/sub communication between components. This provides loose coupling within the monolith (e.g., when an album is grabbed, notifications fire via events). However, this is not distributed messaging — it runs in-process only. No managed messaging (SQS, SNS, EventBridge) or self-managed message brokers are present. For a stateful-crud service, cross-service state changes should use managed messaging, but the monolith has no service boundaries to communicate across. |
| **Gap** | Internal event aggregator provides in-process pub/sub but is not distributed. When decomposition occurs, state changes will need managed messaging between services. |
| **Recommendation** | When extracting services, introduce EventBridge (preferred) for cross-service event propagation. The existing `IHandle<T>` pattern maps naturally to event-driven architecture — events like `AlbumGrabbedEvent`, `TrackImportedEvent` would become EventBridge events. |
| **Evidence** | `src/NzbDrone.Core/Messaging/`, grep for `IEventAggregator` and `IHandle<` across NzbDrone.Core |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnets, security groups, or network segmentation defined. The application is self-hosted — users expose it directly on their network. The application listens on port 8686 (HTTP) and 6868 (HTTPS) with no network-level isolation. Forwarded headers middleware exists for reverse proxy scenarios, but this is optional user configuration. |
| **Gap** | No cloud network security infrastructure. No VPC, no private subnets, no security groups. |
| **Recommendation** | When deploying to AWS, define VPC with private subnets for the application and database tier. Use VPC endpoints for AWS service access. Deploy behind an ALB or API Gateway in a public subnet. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (ForwardedHeaders middleware), `src/NzbDrone.Host/Bootstrap.cs` (port configuration), absence of any IaC |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront as entry point. The application exposes its Kestrel web server directly. Users may optionally configure a reverse proxy (Nginx, Caddy) but this is not part of the application itself. |
| **Gap** | Services are exposed directly with no gateway, load balancer, or managed entry point providing throttling, auth offloading, or request validation. |
| **Recommendation** | Deploy behind API Gateway (preferred per preferences) with throttling, request validation, and API key management. Alternatively, use ALB with WAF rules. |
| **Evidence** | `src/NzbDrone.Host/Bootstrap.cs` (direct Kestrel binding), absence of IaC |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application runs as a single instance on user-managed hardware. No ASG, no ECS service scaling, no Lambda concurrency configuration. |
| **Gap** | All capacity is statically provisioned (single instance). No ability to respond to demand changes. |
| **Recommendation** | When containerized and deployed to EKS, configure Horizontal Pod Autoscaler with custom metrics (active downloads, queue depth). For Aurora, enable auto-scaling on read replicas. |
| **Evidence** | Absence of any scaling configuration, single-instance deployment model |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed cloud data-at-rest surface — no IaC defines S3 buckets, RDS instances, EBS volumes, or similar managed storage. The database is local SQLite or user-provisioned PostgreSQL. INF-Q8 does not apply to the cloud assessment surface. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_at_rest_data_surface=false`; absence of IaC defining cloud storage resources |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed cloud workload requiring HA evaluation. No IaC defines compute or database resources. The application is self-hosted with no cloud deployment model. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_deployed_workload=false`; absence of IaC, Dockerfiles, or Kubernetes manifests for deployment |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC exists — no Terraform, CloudFormation, CDK, Helm charts, or Kustomize files. The application has no cloud infrastructure to codify. All infrastructure (if any) is manually provisioned by end users. |
| **Gap** | 0% IaC coverage. No infrastructure is defined in code. |
| **Recommendation** | Create IaC (CDK preferred for .NET ecosystem) defining: VPC, EKS cluster, Aurora PostgreSQL, ECR repository, and operational resources (CloudWatch alarms, backup plans). |
| **Evidence** | Absence of `.tf`, `*.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files anywhere in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Azure DevOps Pipelines provides comprehensive CI automation with 8+ stages: build (multi-platform .NET + frontend), unit testing (native + Docker + PostgreSQL), integration testing, UI automation, and SonarCloud analysis. The pipeline triggers on push to develop/master and on PRs. However, there is no CD (deployment) pipeline — the pipeline produces packages but does not deploy them to any environment. GitHub Actions workflows exist but are stubs (empty jobs). |
| **Gap** | Strong CI automation but no CD pipeline — builds produce artifacts but do not deploy to any environment. No automated deployment stage exists. |
| **Recommendation** | Extend the pipeline with deploy stages targeting EKS. Implement staged deployment: dev → staging → production with automated smoke tests between stages. Consider CodePipeline or ArgoCD for GitOps-based continuous deployment. |
| **Evidence** | `azure-pipelines.yml` (8 stages, multi-platform matrix), `.github/workflows/ci.yml` (empty stub) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is C# on .NET 8.0 (SDK 8.0.405) — the latest LTS version with first-class AWS SDK coverage. Uses ASP.NET Core 8 with modern patterns (DI, middleware pipeline, async/await). Frontend uses TypeScript 5.7 with React 18. The AWS SDK for .NET v3 has full coverage for .NET 8. |
| **Gap** | N/A — language and runtime are modern. |
| **Recommendation** | N/A — .NET 8 is current LTS with excellent AWS ecosystem support. |
| **Evidence** | `global.json` (SDK 8.0.405), `src/Directory.Build.props` (net8.0 TFM), `package.json` (TypeScript 5.7, React 18) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Tightly-coupled monolith with no clear module boundaries for independent deployment. All business logic resides in `NzbDrone.Core` (one massive project with 50+ subdirectories). A single shared database (80 migrations in one project) manages all state. Cross-module dependencies are pervasive through DI container registration. The solution has one deployable entry point (Lidarr.Console/Lidarr.exe). While internal namespaces provide some logical separation, there is shared mutable state and no interface boundaries between logical modules. |
| **Gap** | Tightly-coupled monolith with pervasive shared state, single database, and no independently deployable components. |
| **Recommendation** | Begin with containerization (lift-and-containerize the monolith). Then apply conditional/adaptive decomposition: extract high-value bounded contexts (Notifications, Indexer/Search, Download Management) as independent services. See Decomposition Strategy section. |
| **Evidence** | `src/Lidarr.sln` (single solution), `src/NzbDrone.Core/` (2,300+ files in one project), `src/NzbDrone.Core/Datastore/Migration/` (80 shared migrations) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The monolith uses primarily synchronous communication patterns. Internal method calls are synchronous. The in-process event aggregator (`IEventAggregator`/`IHandle<T>`) provides some async-like patterns (publish-subscribe) but these are in-process and not distributed. External HTTP calls (to indexers, download clients, metadata sources) are synchronous. SignalR provides real-time push to the UI but this is client-facing, not inter-service. For a stateful-crud monolith, the lack of async for background processing of downloads and imports represents a gap. |
| **Gap** | Primarily synchronous with some in-process pub/sub. Background processing of downloads and imports would benefit from async patterns for cross-service decoupling when decomposed. |
| **Recommendation** | When decomposing, convert the `IHandle<T>` event pattern to distributed async messaging via EventBridge. Download processing, notification dispatch, and metadata refresh are strong candidates for async-first communication. |
| **Evidence** | `src/NzbDrone.Core/Messaging/` (in-process event aggregator), `src/NzbDrone.Common/Http/HttpClient.cs` (synchronous HTTP), `src/NzbDrone.SignalR/` (UI push only) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has operations that can exceed 30 seconds — bulk artist metadata refresh, large album imports, indexer searches across multiple sources. These are handled by an internal `CommandExecutor` with a job queue (stored in database) that provides basic async job processing. The frontend polls for command status via the API. This is a partial implementation — job status tracking exists but runs in-process with no distributed job infrastructure. |
| **Gap** | Some background job processing exists (internal command queue with status polling) but it is in-process with no dedicated async job infrastructure. Large import operations can still block. |
| **Recommendation** | For cloud deployment, migrate the command queue to SQS with Step Functions orchestrating multi-step operations (search → download → import → organize). The existing command/status pattern maps well to Step Functions task tokens. |
| **Evidence** | `src/NzbDrone.Core/Jobs/`, `src/NzbDrone.Core/Messaging/Commands/`, API endpoints for command status polling |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The API uses URL path versioning (`/api/v1/`) consistently across all endpoints. However, only a single version (v1) exists with no backward compatibility guarantees, no deprecation policy, and no evidence of version migration support. The versioning is embedded in the namespace (`Lidarr.Api.V1`) and URL structure but functions as a prefix rather than a managed versioning strategy. |
| **Gap** | Single version with URL prefix but no actual versioning strategy — no v2, no deprecation policy, no backward compatibility guarantees. |
| **Recommendation** | Formalize the versioning strategy: document backward compatibility policy, implement API version negotiation when breaking changes are needed, and plan for v2 endpoints as modernization progresses. |
| **Evidence** | `src/Lidarr.Api.V1/openapi.json` (API version 1.0.0), `src/Lidarr.Api.V1/` namespace structure |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | External service endpoints (indexers, download clients, notification services) are configured via environment variables and user-configured settings stored in the database. No dynamic service discovery mechanism exists. The application uses a configuration-based approach where users manually enter service URLs. This is appropriate for the current self-hosted model but would need service discovery for a cloud-native multi-service deployment. |
| **Gap** | Environment variables and database-stored configuration for endpoints but no dynamic discovery. |
| **Recommendation** | When deploying to AWS with multiple services, implement service discovery via AWS Cloud Map or Kubernetes DNS (if on EKS). For external integrations (indexers, download clients), maintain the configuration-based approach as these are user-specific. |
| **Evidence** | `src/NzbDrone.Core/Configuration/`, `src/NzbDrone.Core/Indexers/` (configured endpoints), `src/NzbDrone.Core/Download/` (configured download client URLs) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Unstructured data (album artwork, artist images, media cover files) is stored on the local filesystem. The `MediaCover` subsystem reads/writes images to disk paths relative to the application data directory. No S3 or managed object storage is used. Media files (music) are managed on local/network drives with no cloud storage integration. |
| **Gap** | All unstructured data on local file systems with no managed object storage. Media covers, artwork, and metadata files are filesystem-bound. |
| **Recommendation** | Migrate media cover storage to S3 for cloud deployments. Consider S3 for media file management with appropriate storage classes. For the cloud-native version, use S3 as the backing store for album artwork with CloudFront CDN for serving. |
| **Evidence** | `src/NzbDrone.Core/MediaCover/`, `src/NzbDrone.Core/MediaFiles/`, `src/NzbDrone.Core/Extras/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a mostly centralized data access layer. The `Datastore` directory contains the core data access infrastructure (Dapper, SqlBuilder, converters, extensions). Repository pattern is used consistently — each entity has a dedicated repository class (e.g., `ArtistRepository`, `AlbumRepository`, `TrackRepository`). However, some auxiliary code paths access the database directly through raw SQL or bypass the repository pattern. The `BasicRepository<T>` base class provides consistent CRUD operations. |
| **Gap** | Mostly centralized with repository pattern, but some direct SQL access in auxiliary paths and custom queries outside the repository layer. |
| **Recommendation** | When migrating to managed databases, ensure all data access goes through the repository layer. Audit for any raw SQL that bypasses the repository pattern and consolidate into proper repository methods. |
| **Evidence** | `src/NzbDrone.Core/Datastore/` (centralized), `src/NzbDrone.Core/Music/Repositories/`, `src/NzbDrone.Core/Datastore/SqlBuilder.cs` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database engine versions are not pinned in IaC (no IaC exists). CI tests against PostgreSQL 14 and 15 (defined in `azure-pipelines.yml`). SQLite version is controlled by the NuGet package (`SourceGear.sqlite3`). PostgreSQL versions are not explicitly pinned for production — users deploy whatever version they choose. The first migration (`000_database_engine_version_check.cs`) validates minimum engine versions at runtime. |
| **Gap** | No IaC version pinning. PostgreSQL version depends on user deployment. CI tests against 14/15 which are current, but no formal version management or EOL tracking exists. |
| **Recommendation** | When creating IaC for Aurora PostgreSQL, explicitly pin the engine version (PostgreSQL 15 recommended). Establish a version update procedure with testing across the defined CI matrix before upgrading. |
| **Evidence** | `azure-pipelines.yml` (postgres:14, postgres:15 in CI), `src/NzbDrone.Core/Datastore/Migration/000_database_engine_version_check.cs`, absence of IaC with engine version pins |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the application layer (C#). The 80 FluentMigrator migrations define schema only (CREATE TABLE, ALTER TABLE, CREATE INDEX). Database queries use standard SQL via Dapper with parameterized queries. The application supports both SQLite and PostgreSQL, which inherently prevents reliance on engine-specific features. |
| **Gap** | N/A — no stored procedures or proprietary SQL. |
| **Recommendation** | N/A — the application layer owns all business logic, making database migration straightforward. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (schema-only migrations), `src/NzbDrone.Core/Datastore/SqlBuilder.cs` (standard SQL), dual SQLite/PostgreSQL support |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud audit logging infrastructure. Application-level logging exists via NLog (file-based and database log table) but this is application debugging logs, not immutable audit trails. The History table tracks download/import actions but is mutable application state, not an audit log. |
| **Gap** | No immutable audit logging. No CloudTrail configuration. Application logs are not audit-grade — they are mutable, not validated, and not stored in immutable storage. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. For application-level audit trails, implement structured audit events sent to CloudWatch Logs with defined retention. |
| **Evidence** | NLog configuration in `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Core/History/` (mutable application history), absence of CloudTrail configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no IaC defines S3 buckets, RDS instances, EBS volumes, or similar managed storage requiring encryption configuration. The database is local SQLite or user-provisioned PostgreSQL. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_at_rest_data_surface=false`; absence of cloud storage resources in IaC |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API authentication uses a static API key approach — a single key validated via `X-Api-Key` header, `apikey` query parameter, or `Authorization: Bearer` header. The key is a simple string comparison against a configured value. There is no OAuth2/JWT token-based authentication, no token expiry, no scoped permissions, and no user-level attribution. The API key is generated on first run and stored in a config file. |
| **Gap** | Static API key authentication without token-based auth (OAuth2/JWT). No token expiry, no per-user attribution, no scoped permissions. |
| **Recommendation** | For cloud deployment, implement OAuth2/JWT via Amazon Cognito (preferred) or integrate with API Gateway authorizers. The static API key can remain for backward compatibility with existing clients during migration. |
| **Evidence** | `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Lidarr.Http/Authentication/AuthenticationService.cs` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. Users are stored in the local database (`UserRepository`, `UserService`). Password hashing uses `Microsoft.AspNetCore.Cryptography.KeyDerivation`. There is no integration with any external identity provider — no Cognito, no OIDC, no SAML, no SSO. Authentication types are limited to `None`, `Basic`, or `Forms` (local credential check). |
| **Gap** | Entirely self-managed authentication with no external IdP integration. No SSO, no OIDC/SAML federation. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. Implement OIDC federation to support SSO. The existing forms-based auth can remain as a fallback for self-hosted deployments. |
| **Evidence** | `src/NzbDrone.Core/Authentication/User.cs`, `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Authentication/AuthenticationType.cs` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials are committed to the repository source code. Database credentials for PostgreSQL are configured via environment variables (`Lidarr__Postgres__Password`). The API key is generated at runtime and stored in a local XML config file (not in source). However, there is no secrets management system — no Secrets Manager, no Vault. Credentials are in environment variables without encryption or rotation. The NuGet.config references Azure DevOps package feeds with credentials managed by the CI system. |
| **Gap** | No dedicated secrets management. Production credentials are in environment variables without encryption or rotation. No Secrets Manager or Vault integration. |
| **Recommendation** | Integrate with AWS Secrets Manager for database credentials, API keys, and external service tokens. Configure automatic rotation for database passwords. Reference secrets from EKS pods via External Secrets Operator or native Secrets Store CSI driver. |
| **Evidence** | `src/NzbDrone.Core/Datastore/DbFactory.cs` (env vars for PG credentials), `src/NuGet.config` (feed credentials managed by CI), absence of Secrets Manager references |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline uses up-to-date base images (ubuntu-24.04, windows-2025, macOS-15) and .NET 8 SDK. Dependabot is configured but only for devcontainer updates (limited scope). SonarCloud provides code quality analysis. However, no vulnerability scanning (Inspector, Snyk, Trivy) is integrated. No hardened base images for deployment. No patching strategy for deployed instances. |
| **Gap** | Default images in CI with limited vulnerability scanning. No deployment patching strategy. Dependabot covers only devcontainers, not NuGet or npm packages. |
| **Recommendation** | Extend Dependabot to cover `nuget` and `npm` ecosystems. Add container vulnerability scanning (ECR image scanning or Trivy) when Dockerfiles are created. For EKS deployment, use Bottlerocket or AL2023 hardened nodes. |
| **Evidence** | `.github/dependabot.yml` (devcontainers only), `azure-pipelines.yml` (SonarCloud analysis), absence of vulnerability scanning tools |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SonarCloud is integrated in the CI pipeline for SAST-like code quality analysis (code smells, bugs, security hotspots). Dependabot is configured but with minimal scope (devcontainers only). No dedicated SAST tool (Semgrep, CodeQL). No dependency vulnerability scanning (`dotnet list package --vulnerable` not run). No container scanning. The SonarCloud configuration provides some security insight but is not a purpose-built security gate. |
| **Gap** | SonarCloud provides partial SAST coverage but is a code quality tool, not a dedicated security scanner. No dependency vulnerability scanning for NuGet/npm packages. No container scanning. No security gate blocking on critical findings. |
| **Recommendation** | Add CodeQL or Semgrep for C# SAST. Extend Dependabot to cover NuGet and npm ecosystems. Add `dotnet list package --vulnerable` and `yarn audit` to the CI pipeline. When containerized, add ECR image scanning. Implement a security gate that blocks builds on critical findings. |
| **Evidence** | `azure-pipelines.yml` (SonarCloudPrepare, SonarCloudAnalyze tasks), `.github/dependabot.yml` (devcontainers only) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No OpenTelemetry SDK, no X-Ray, no trace ID propagation. The application uses NLog for text-based logging only. No correlation IDs are propagated across HTTP calls to external services (indexers, download clients, metadata providers). |
| **Gap** | No distributed tracing. Cannot trace request flows across the application's interactions with external services. |
| **Recommendation** | Instrument with OpenTelemetry SDK for .NET (already supports ASP.NET Core auto-instrumentation). Export traces to X-Ray or a managed observability platform. Propagate trace context headers on outbound HTTP calls. |
| **Evidence** | Absence of OpenTelemetry/X-Ray packages in `.csproj` files, `src/NzbDrone.Host/Startup.cs` (NLog only), `src/NzbDrone.Common/Http/HttpClient.cs` (no trace propagation) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs defined. No formal definition of acceptable service levels (latency, availability, error rates). The application has internal health checks (`HealthCheck/` directory with 20+ checks) but these monitor operational readiness, not SLO compliance. No error budget tracking. |
| **Gap** | No SLOs, no error budgets, no formal service level definitions for user-facing API journeys. |
| **Recommendation** | Define SLOs for critical user journeys: API response latency (p95/p99), search availability, download success rate. Implement CloudWatch dashboards with SLO tracking and error budget alerting. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (operational checks only), absence of SLO definitions |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. The `Analytics` directory exists but only for telemetry opt-in tracking. No CloudWatch custom metrics, no business outcome dashboards (albums imported/day, search success rate, download failure rate). Only application-level NLog text logging exists. |
| **Gap** | No business metrics. No visibility into application performance from a user-outcome perspective. |
| **Recommendation** | Instrument key business metrics: albums imported per day, download success/failure rates, indexer response times, queue depth, search latency. Publish to CloudWatch custom metrics and build operational dashboards. |
| **Evidence** | `src/NzbDrone.Core/Analytics/` (basic telemetry only), absence of metric publishing code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. The application has internal health checks but no external monitoring, no CloudWatch alarms, no PagerDuty/OpsGenie integration. Health check results are displayed in the UI but not pushed to any alerting system. |
| **Gap** | No alerting infrastructure. Health check failures are visible only in the application UI, not in external monitoring systems. |
| **Recommendation** | Implement CloudWatch alarms on key metrics (error rates, API latency, queue depth). Enable anomaly detection on error rates. Integrate with SNS for alerting and escalation. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (UI-only health checks), absence of alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The application includes a self-update mechanism (`NzbDrone.Update/`) that downloads and replaces the running binary — a direct-to-production replacement with no staged rollout, no canary, no blue/green. The CI pipeline produces packages but does not deploy them. |
| **Gap** | Direct binary replacement for updates. No blue/green, no canary, no rolling deployments. No deployment pipeline to any managed environment. |
| **Recommendation** | When deployed to EKS, implement canary deployments via ArgoCD Rollouts or Kubernetes rolling updates with readiness probes. For production releases, use blue/green deployment to enable instant rollback. |
| **Evidence** | `src/NzbDrone.Update/` (self-update mechanism), `azure-pipelines.yml` (no deploy stage) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Integration tests exist (`src/NzbDrone.Integration.Test/`) and run in the CI pipeline. Tests exercise the full HTTP API stack including authentication, and run against both SQLite and PostgreSQL. The CI pipeline has dedicated integration test stages on multiple platforms. However, these test the self-contained application — they do not test against any cloud deployment or cloud services. |
| **Gap** | Integration tests exist and run in CI but test only the self-contained application. No cloud integration tests (against Aurora, EKS health, S3 connectivity). |
| **Recommendation** | When cloud-deployed, add integration test stages that validate the application against the deployed cloud infrastructure (Aurora connectivity, S3 access, API Gateway routing). Extend existing tests to run against a staging environment. |
| **Evidence** | `src/NzbDrone.Integration.Test/`, `azure-pipelines.yml` (Integration stage with Docker+Postgres variants) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation. No runbooks (manual or automated). No Systems Manager Automation documents. No self-healing patterns beyond the internal health check system. The application has a self-recovery mechanism for corrupt log databases (auto-recreation) but this is application-level, not operational. |
| **Gap** | No runbooks, no automated incident response, no self-healing patterns for infrastructure-level issues. |
| **Recommendation** | Create operational runbooks for common failure scenarios (database connection loss, disk full, OOM). Implement SSM Automation documents for automated remediation. Define escalation procedures. |
| **Evidence** | `src/NzbDrone.Core/Datastore/DbFactory.cs` (log DB auto-recreation), absence of runbook files or automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership structure. No per-service dashboards (single monolith), no named alarm owners, no SLO definitions with team attribution. No CODEOWNERS file for observability assets. The application has internal health checks but no external observability ownership. |
| **Gap** | No observability ownership — no dashboards, no alarm owners, no team attribution for monitoring. |
| **Recommendation** | When deployed to AWS, establish observability ownership: create CloudWatch dashboards per functional area, define alarm owners, and implement CODEOWNERS for observability infrastructure code. |
| **Evidence** | Absence of dashboards, CODEOWNERS, or observability configuration files |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources exist. No IaC defines any resources, so there are no tags to evaluate. |
| **Gap** | No resources to tag — but when cloud infrastructure is created, tagging governance must be established from the start. |
| **Recommendation** | When creating IaC, implement mandatory tagging from day one: `Environment`, `Service`, `Team`, `CostCenter`. Use CDK aspects or Terraform `default_tags` for consistent application. Enforce with AWS Config rules. |
| **Evidence** | Absence of any IaC or AWS resources |

---

## Learning Materials

- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR)
- [EKS Workshop](https://www.eksworkshop.com/)
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `azure-pipelines.yml` | INF-Q1, INF-Q11, SEC-Q6, SEC-Q7, OPS-Q5, OPS-Q6, DATA-Q3 | Primary CI/CD pipeline with 8+ stages, SonarCloud integration, multi-platform testing |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, OPS-Q1 | ASP.NET Core startup with auth, middleware pipeline, NLog |
| `src/NzbDrone.Host/Bootstrap.cs` | INF-Q1, INF-Q5, INF-Q6 | Application entry point, Kestrel binding, port configuration |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | INF-Q2, SEC-Q5, OPS-Q7 | Database factory supporting SQLite and PostgreSQL, env var credentials |
| `src/NzbDrone.Core/Datastore/Migration/` | APP-Q2, DATA-Q3, DATA-Q4 | 80 FluentMigrator schema migrations, shared database |
| `src/NzbDrone.Core/Datastore/DatabaseConnectionInfo.cs` | INF-Q2 | Database connection configuration |
| `src/NzbDrone.Core/Datastore/WhereBuilderPostgres.cs` | INF-Q2 | PostgreSQL-specific query support |
| `src/NzbDrone.Core/Datastore/SqlBuilder.cs` | DATA-Q2, DATA-Q4 | Centralized SQL query building |
| `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key auth implementation |
| `src/NzbDrone.Core/Authentication/` | SEC-Q4 | Self-managed user authentication |
| `src/Lidarr.Api.V1/openapi.json` | APP-Q5 | OpenAPI 3.0.4 spec, version 1.0.0 |
| `src/NzbDrone.Core/HealthCheck/` | OPS-Q2, OPS-Q4 | Internal health check system (UI-only) |
| `src/NzbDrone.Core/MediaCover/` | DATA-Q1 | Local filesystem media cover storage |
| `src/NzbDrone.Core/Messaging/` | INF-Q4, APP-Q3 | In-process event aggregator |
| `src/NzbDrone.Core/IndexerSearch/` | INF-Q3 | Search workflow logic |
| `src/NzbDrone.Core/Download/` | INF-Q3, APP-Q4 | Download management workflow |
| `src/NzbDrone.Core/Jobs/` | APP-Q4 | Internal job/command queue |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Dependabot config (devcontainers only) |
| `.github/workflows/ci.yml` | INF-Q11 | Empty GitHub Actions stub |
| `global.json` | APP-Q1 | .NET SDK 8.0.405 |
| `src/Directory.Build.props` | APP-Q1 | Central build properties, net8.0 TFM |
| `package.json` | APP-Q1 | Frontend dependencies (React 18, TypeScript 5.7) |
| `src/NzbDrone.Core/Analytics/` | OPS-Q3 | Basic telemetry (not business metrics) |
| `src/NzbDrone.Update/` | OPS-Q5 | Self-update mechanism (binary replacement) |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | Integration test project |
| `distribution/` | INF-Q1 | Platform package distribution files |
| `src/NuGet.config` | SEC-Q5 | NuGet package source configuration |
| `src/Lidarr.sln` | APP-Q2 | Single solution file (22 projects) |
