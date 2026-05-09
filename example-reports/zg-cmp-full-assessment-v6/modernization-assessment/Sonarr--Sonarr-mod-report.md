# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Sonarr--Sonarr |
| **Date** | 2025-05-08 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, media, desktop |
| **Context** | TV-series PVR for usenet and BitTorrent users (*arr suite). |
| **Overall Score** | 1.88 / 4.0 |

**Archetype Justification**: The application owns persistent state (SQLite/PostgreSQL databases for series metadata, episode tracking, download history) and exposes CRUD operations on business entities (series, episodes, download clients, indexers). It has both read and write endpoints with entity lifecycle management. Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.22 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.40 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.88 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+1+1+1+1+1+1+3)/9 = 11/9 = 1.22 (INF-Q3 and INF-Q4 Not Evaluated, excluded)
- APP: (4+1+2+3+2)/5 = 12/5 = 2.40 (APP-Q3 Not Evaluated, excluded)
- DATA: (2+3+3+4)/4 = 12/4 = 3.00
- SEC: (1+2+2+1+2+1+2)/7 = 11/7 = 1.57
- OPS: (1+1+1+1+1+3+1+1+1)/9 = 11/9 = 1.22
- Overall: (1.22+2.40+3.00+1.57+1.22)/5 = 9.41/5 = 1.88

**Classification Tier:** 🔴 Not Ready

**Classification Rationale:** This repository has 14 High findings, 8 Medium findings, and 2 Low findings. Rule matched: "≥12 High → Not Ready." This application is a self-hosted desktop/server PVR with no cloud infrastructure — the high finding count reflects the complete absence of cloud-native capabilities rather than critical production failures in an existing cloud deployment. ARA's "1 High" gates on agent-deployment safety (a single High is a deployment blocker); MOD's scoring measures modernization maturity distance from cloud-native (a single High is one modernization gap, mapped to Pilot-Ready). With 14 core-question scores of 1, this application requires substantial modernization work before cloud-native deployment.

**Classification Consistency Check:** ⚠️ DIVERGENT — V5 overall score 1.88 yields band "Needs Work" (1.5–2.4), but V6 severity-count classification yields "Not Ready" (≥12 High). This divergence is expected: the V5 numeric score averages in the Score-4 APP-Q1 and Score-3 questions (INF-Q11, OPS-Q6, APP-Q5, DATA-Q2, DATA-Q3, DATA-Q4) which raise the mean, while V6 counts the absolute number of gaps (14 questions at Score 1 each emit a High finding). The V6 tier more accurately reflects the modernization distance — this workload needs foundational cloud infrastructure before any further optimization.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure would need to be created from scratch | Blocks all cloud deployment; no reproducible infrastructure |
| 2 | INF-Q1: Managed Compute | 1 | No cloud compute defined; application is a self-hosted desktop/server binary | Cannot scale, no managed patching, no elastic capacity |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or cloud audit logging | No compliance visibility, no forensic capability |
| 4 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith with shared database and in-process event bus | Cannot independently scale components; all-or-nothing deployments |
| 5 | OPS-Q5: Deployment Strategy | 1 | No staged deployment; self-update mechanism replaces binary in-place | High risk of failed updates with no automated rollback |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (README.md, CONTRIBUTING.md, SECURITY.md, and an external wiki at wiki.servarr.com). APP-Q5 ≥ 2 with OpenAPI specs present.
- **What it enables:** A RAG-based agent could index the existing OpenAPI specifications (V3 and V5), README, CONTRIBUTING guide, and wiki content to answer developer questions about the Sonarr API, contribution workflows, and configuration.
- **Additional steps:** The external wiki content would need to be crawled and indexed. The OpenAPI specs are already machine-readable.
- **Effort:** Medium

### API-aware Agent

- **Prerequisite:** API documentation exists (OpenAPI V3 and V5 specs at `src/Sonarr.Api.V3/openapi.json` and `src/Sonarr.Api.V5/openapi.json`). APP-Q5 = 3.
- **What it enables:** An agent that discovers and invokes Sonarr API endpoints as tools — managing series, triggering searches, checking download status, and querying episode data via natural language.
- **Additional steps:** The API requires authentication (API key), so the agent would need credential configuration.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (GitHub Actions with build, test, and deploy stages). INF-Q11 = 3.
- **What it enables:** An agent that triggers builds, checks test results, monitors deployment status, and manages releases through the existing GitHub Actions pipeline.
- **Additional steps:** Would need GitHub API access configured for the agent.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1, INF-Q1=1, APP-Q4=2 |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1; no modern container definitions found (existing Dockerfiles are legacy Mono-based) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected (uses SQLite and PostgreSQL) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (databases are self-managed SQLite/PostgreSQL) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads, streaming, or analytics infrastructure exists |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), OPS-Q5=1 (no staged deployment), OPS-Q6=3 (integration tests exist but gaps) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:** Sonarr is a tightly-coupled monolith (APP-Q2=1) with no cloud compute (INF-Q1=1) and limited async long-running process handling (APP-Q4=2). The application is designed as a self-hosted desktop/server application with an in-process event bus and command queue.

**Decomposition Candidates:**
- Media management (series/episode metadata, file management)
- Download client coordination (Usenet/BitTorrent integration)
- Indexer/search service (Torznab/Newznab protocol handling)
- Notification service (email, webhook, push notifications)
- API gateway (V3 and V5 API surfaces)

**Recommended AWS Services (respecting preferences):**
- Amazon EKS for container orchestration (preferred over ECS per user preferences)
- Amazon Aurora PostgreSQL for managed database (preferred)
- Amazon EventBridge for event-driven communication between services
- Amazon API Gateway for API entry point
- AWS Step Functions for download workflow orchestration

**Recommended Patterns:** Strangler Fig (incremental extraction), Anti-corruption Layer, Event Sourcing for download state tracking, Hexagonal Architecture for new services.

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:** The existing Dockerfiles are legacy Mono-based build containers and do not represent the current .NET 10 application. No modern runtime Dockerfile exists for the .NET 10 build.

**Container Readiness:**
- The application already supports multiple runtime identifiers (linux-x64, linux-arm64, linux-musl-x64, etc.)
- Configuration is externalized via XML config file and environment variables
- The application detects Docker environments and disables self-update accordingly
- Health check endpoint exists at `/ping`

**Recommended Approach:**
- Create a modern multi-stage Dockerfile using `mcr.microsoft.com/dotnet/aspnet:10.0` runtime image
- Deploy to Amazon EKS (preferred per user preferences)
- Use ECR for container image registry
- Implement Kubernetes health probes using the existing `/ping` endpoint

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** The application supports both SQLite (embedded, default) and PostgreSQL (optional). Both are self-managed — SQLite as a local file, PostgreSQL as a user-provisioned instance. No managed database service is used.

**Migration Path:**
- Migrate PostgreSQL deployment to Amazon Aurora PostgreSQL (preferred per user preferences)
- Aurora provides automated backups, failover, read replicas, and auto-scaling
- The existing Npgsql driver and FluentMigrator migrations are fully compatible with Aurora PostgreSQL
- Connection string configuration already supports external PostgreSQL — only the connection endpoint needs to change

**Recommended AWS Services:**
- Amazon Aurora PostgreSQL (primary recommendation, user preference)
- AWS Database Migration Service (DMS) for data migration if needed

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC (INF-Q10=1):** No infrastructure-as-code exists. All infrastructure would need to be defined from scratch.
- **Deployment (OPS-Q5=1):** The application uses a custom self-update mechanism that replaces binaries in-place. No blue/green or canary deployment strategy exists.
- **CI/CD (INF-Q11=3):** A comprehensive GitHub Actions pipeline exists with build, test (unit + integration on 3 platforms + PostgreSQL), and release stages.

**Recommended Actions:**
- Define infrastructure using AWS CDK or Terraform (EKS cluster, Aurora, networking)
- Implement GitOps with ArgoCD or Flux for Kubernetes deployments
- Add canary/blue-green deployment strategy using Kubernetes rolling updates or AWS CodeDeploy
- Extend existing CI/CD pipeline with infrastructure deployment stages

**Recommended AWS Services:**
- AWS CDK for IaC (preferred over CloudFormation for C# team familiarity)
- AWS CodePipeline / CodeBuild for CI/CD (alternative to GitHub Actions)
- AWS CodeDeploy for deployment strategy

---

## Decomposition Strategy

**Condition:** APP-Q2 = 1 (tightly-coupled monolith)

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services while keeping the monolith running. The existing layered architecture (Core/Host/API/Common) provides identifiable boundaries. | Medium to High | ✅ **Recommended.** The existing internal event bus and command queue boundaries provide natural service extraction points. |
| **Conditional / Adaptive** | Containerize the monolith first, then selectively extract high-value services. | Low to Medium | ✅ **Recommended as initial step** given the application already detects Docker and disables self-update. |
| **Big-Bang Rewrite** | Full rewrite as microservices. | Very High | ⚠️ **Recommended against.** The monolith is functional and well-structured internally. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the monolith's internal data model | Every extraction — especially between the download client coordination and the core metadata service |
| **Saga Pattern** | Manage distributed transactions across extracted services | When extracting the download → import → rename workflow that currently runs as an in-process command chain |
| **Event Sourcing** | Capture state changes as events for inter-service communication | Replace the in-process EventAggregator with EventBridge events when services are extracted |
| **Hexagonal Architecture** | Structure each new service with clear ports and adapters | Every new service — the existing layered architecture partially supports this already |

### Effort Estimation

| Factor | Signal | Assessment |
|--------|--------|------------|
| Module boundaries | Layered architecture (Core/Host/API) with internal namespaces (Series, Episodes, Download, Indexers) | Medium effort — boundaries exist but are not fully independent |
| Data coupling | Single database with shared tables across domains | High effort — data separation required |
| Stored procedures | None — all logic in application layer (DATA-Q4=4) | Low effort — no database-layer logic to extract |
| Communication patterns | In-process event bus and command queue | Medium effort — patterns exist but need to be externalized |
| CI/CD maturity | GitHub Actions pipeline with multi-platform builds | Low effort — existing pipeline can be extended |
| Test coverage | Integration tests exist for API endpoints | Medium effort — tests exist but coverage gaps remain |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute infrastructure is defined. The application is distributed as self-contained binaries for 10 runtime identifiers (win-x64, linux-x64, osx-arm64, etc.) and is designed to run as a self-hosted server process on user-managed hardware or VMs. No ECS, EKS, Lambda, or Fargate resources exist. |
| **Gap** | All compute is self-managed with no managed container orchestration or serverless adoption. |
| **Recommendation** | Containerize the .NET 10 application and deploy to Amazon EKS (user preference). Create a modern Dockerfile using the .NET 10 ASP.NET runtime image. The existing multi-platform build pipeline already produces linux-x64 and linux-arm64 binaries suitable for container packaging. |
| **Evidence** | `global.json` (.NET 10.0.201), `.github/workflows/build_v5.yml` (10 runtime identifiers), `distribution/docker-build/Dockerfile` (legacy Mono-based, not current) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application uses SQLite (embedded file-based, default) and PostgreSQL (optional, user-provisioned). Both are entirely self-managed. No managed database services (RDS, Aurora, DynamoDB) are referenced in IaC or configuration. The PostgreSQL connection is configured via environment variables or XML config pointing to user-managed instances. |
| **Gap** | All databases are self-managed with no managed services, no automated failover, no managed backups. |
| **Recommendation** | Migrate to Amazon Aurora PostgreSQL (user preference) for the PostgreSQL deployment path. The existing Npgsql driver (v10.0.2) and FluentMigrator migrations are compatible with Aurora. Connection string configuration already supports external PostgreSQL — only the endpoint needs to change. |
| **Evidence** | `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (SQLite/PostgreSQL config), `src/NzbDrone.Core/Datastore/DbFactory.cs` (database creation), `src/NzbDrone.Core/Sonarr.Core.csproj` (Npgsql 10.0.2) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateful-crud`. The application does have internal workflow-like patterns (download → import → rename chains implemented via an in-process command queue with 3 executor threads), but these are not multi-service orchestration workflows — they are in-process background task execution within a monolith. Given the monolithic architecture (APP-Q2=1), evaluating workflow orchestration readiness is premature; decomposition must occur first before inter-service orchestration becomes relevant. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateful-crud`. The application uses an in-process event aggregator (`IEventAggregator`) and command queue for internal pub/sub and background task execution. No external messaging infrastructure exists (no SQS, SNS, EventBridge, Kafka, RabbitMQ). Given the monolithic architecture, the in-process event bus is architecturally appropriate — the service does not cross service boundaries because it IS a single service. Async messaging becomes relevant only after decomposition. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists. The application is designed to bind to a local port (default 8989) on the host machine. No cloud networking infrastructure is defined. |
| **Gap** | No network security controls defined. The application exposes its API directly on the host network with no cloud-native network segmentation. |
| **Recommendation** | When deploying to AWS, define a VPC with private subnets for the application and database tiers. Use security groups with least-privilege rules. Place the API behind an ALB or API Gateway in a public subnet. Use VPC endpoints for AWS service communication. |
| **Evidence** | No IaC files found. `src/NzbDrone.Host/Startup.cs` (binds to configured port with open CORS). |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront is configured as an entry point. The application serves HTTP directly from the ASP.NET Core Kestrel server. The Swagger UI is available in debug mode only. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, no request validation at the entry point, no centralized auth gateway. |
| **Recommendation** | Deploy Amazon API Gateway in front of the application to provide throttling, request validation, and centralized authentication. Alternatively, use an ALB with AWS WAF for DDoS protection and request filtering. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (direct Kestrel serving, Swagger in debug only) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application runs as a single process on user-managed hardware. There is no concept of horizontal scaling — the application is designed as a single-instance server with a local SQLite database. |
| **Gap** | No auto-scaling; all capacity is statically provisioned by the user. |
| **Recommendation** | When containerized on EKS, configure Horizontal Pod Autoscaler (HPA) based on CPU/memory metrics. For Aurora PostgreSQL, configure auto-scaling read replicas. Consider application-level scaling based on queue depth (number of pending commands). |
| **Evidence** | No IaC files. Single-process architecture with in-process command queue (`CommandExecutor` with `THREAD_LIMIT = 3`). |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application has a built-in backup command (`BackupCommand`) that creates periodic backups of the SQLite database to the application's data directory. However, no cloud-native backup infrastructure exists (no AWS Backup, no automated cross-region replication, no PITR). The backup is a simple file copy with no retention policy enforcement beyond local disk. |
| **Gap** | No automated cloud backup with defined retention, no PITR, no cross-region replication. The built-in backup is a local file copy only. |
| **Recommendation** | With Aurora PostgreSQL, automated backups with PITR are included by default. Configure backup retention period (minimum 7 days) and enable cross-region backup replication for disaster recovery. For any remaining local storage needs, use AWS Backup with S3 lifecycle policies. |
| **Evidence** | `src/NzbDrone.Core/Jobs/TaskManager.cs` (BackupCommand scheduled), `src/NzbDrone.Core/Backup/` directory |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application is designed as a single-instance server. No multi-AZ deployment exists. The SQLite default database is a single file on local disk — the antithesis of high availability. Even with PostgreSQL, the user manages their own instance with no configured failover. |
| **Gap** | Single-instance deployment with no fault isolation or multi-AZ redundancy. |
| **Recommendation** | Deploy to EKS across multiple AZs with at least 2 replicas. Use Aurora PostgreSQL Multi-AZ for automatic database failover. Ensure the application can run as multiple instances (requires moving from SQLite to PostgreSQL and ensuring no file-system-based state that prevents horizontal scaling). |
| **Evidence** | Single-process design, SQLite as default database, no IaC with AZ configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files were found. All infrastructure (if any cloud deployment exists) is manually created. |
| **Gap** | 0% IaC coverage. All infrastructure would need to be defined from scratch for cloud deployment. |
| **Recommendation** | Define all infrastructure using AWS CDK (TypeScript or C# — C# would leverage team expertise). Start with: VPC, EKS cluster, Aurora PostgreSQL, ECR repository, ALB/API Gateway, and CloudWatch alarms. Use CDK Pipelines for infrastructure CI/CD. |
| **Evidence** | No `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found anywhere in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | A comprehensive GitHub Actions pipeline exists with: build stage (10 runtime identifiers), frontend build (yarn + webpack), unit tests (3 OS platforms), PostgreSQL integration tests (versions 16/17/18), integration tests (3 platforms), and automated release/deployment to GitHub Releases and the Sonarr update service. The pipeline includes concurrency control and path-based triggering. |
| **Gap** | CI/CD covers application code well but does not deploy infrastructure (no IaC to deploy). No canary or blue/green deployment strategy in the pipeline. Deployment is binary publishing, not container/service deployment. |
| **Recommendation** | Extend the existing pipeline to include: container image build and push to ECR, IaC deployment via CDK/Terraform, and staged rollout to EKS (canary or blue/green). Add infrastructure deployment stages that run after application artifact creation. |
| **Evidence** | `.github/workflows/build_v5.yml` (main build), `.github/workflows/deploy.yml` (packaging and release), `.github/actions/` (5 composite actions) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application uses C# on .NET 10.0 (latest) with modern ASP.NET Core. The frontend uses TypeScript 5.7 with React 18. The .NET SDK version is 10.0.201 (current). Dependencies include modern versions: Npgsql 10.0.2, Polly 8.6.6, SignalR 10.0.0. This is a first-class AWS SDK-supported language with broad cloud-native tooling. |
| **Gap** | N/A — language and framework are fully modern. |
| **Recommendation** | N/A — no language or framework modernization needed. The .NET 10 runtime with current ASP.NET Core is mature and has full AWS SDK coverage. |
| **Evidence** | `global.json` (.NET SDK 10.0.201), `src/NzbDrone.Core/Sonarr.Core.csproj` (net10.0 target), `package.json` (TypeScript 5.7.2, React 18.3.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application is a tightly-coupled monolith with a single deployable unit. All domains (series management, episode tracking, download client coordination, indexer integration, notification, media management, history, calendar) share a single SQLite/PostgreSQL database and communicate via an in-process event bus. There is no independent deployability — the entire application must be deployed as one unit. While internal namespaces provide some organization, all domains have direct access to the shared database through a common `BasicRepository` base class. |
| **Gap** | Tightly-coupled monolith with shared database, in-process communication, and no clear service boundaries that could be independently deployed. |
| **Recommendation** | Begin with the Strangler Fig pattern. First containerize the monolith as-is (Conditional/Adaptive approach). Then incrementally extract services starting with the most independently-valuable domains: Notification Service (already somewhat isolated with multiple notification implementations), Download Client Coordination (clear external integration boundary), and Search/Indexer Service (protocol-specific logic). |
| **Evidence** | `src/Sonarr.sln` (single solution, single deployable), `src/NzbDrone.Core/Datastore/` (shared database layer), `src/NzbDrone.Core/Messaging/` (in-process event bus) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateful-crud` monolith. As a monolith (APP-Q2=1), there is no inter-service communication to evaluate — all communication is in-process method calls and event aggregation. The async vs sync question becomes relevant only after decomposition when services need to communicate across process boundaries. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` (in-process only) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has a custom in-process command queue (`CommandQueue`) with 3 executor threads and a timer-based scheduler. Long-running operations (RSS sync, series refresh, download import) are dispatched to the queue and executed asynchronously in background threads. The command queue supports priority-based dequeuing and exclusive command handling. However, there is no external status polling API for individual command progress, no callback mechanism, and no checkpointing — if the process crashes mid-command, work is lost. |
| **Gap** | Background job processing exists but with inconsistent patterns: no external status tracking beyond the queue API, no checkpointing for crash recovery, and no distributed job execution capability. |
| **Recommendation** | When decomposing, externalize the command queue to AWS Step Functions for workflow orchestration or SQS for simple async job dispatch. Add idempotency keys and checkpointing for long-running operations. Expose job status via the API (partially exists at `/api/v3/command`). |
| **Evidence** | `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` (priority queue), `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` (3 threads), `src/NzbDrone.Core/Jobs/Scheduler.cs` (timer-based) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application maintains two coexisting API versions: V3 (legacy, at `/api/v3/`) and V5 (new, at `/api/v5/`). Both have OpenAPI specifications. URL-path-based versioning is consistently applied. Swagger documentation exists for both versions (debug mode). The versioning strategy is clear and backward-compatible — V3 is maintained for existing integrations while V5 introduces new features. |
| **Gap** | Versioning strategy exists and is applied consistently, but there is no documented deprecation timeline for V3, and some internal endpoints (like `/ping`, `/login`) are not versioned. |
| **Recommendation** | Document a deprecation timeline for V3. Ensure all new endpoints follow the versioning pattern. Consider adding version headers alongside URL paths for more flexible version negotiation. |
| **Evidence** | `src/Sonarr.Api.V3/` (V3 controllers), `src/Sonarr.Api.V5/` (V5 controllers), `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | External service endpoints (download clients, indexers, notification targets) are configured via the application's settings database — users manually enter URLs for each integration. There is no dynamic service discovery. The Sonarr update service endpoint is hardcoded (`services.sonarr.tv`). Internal communication is all in-process (monolith). |
| **Gap** | Environment variables for some endpoints but no dynamic discovery. All external service endpoints are user-configured and stored in the database. |
| **Recommendation** | When decomposed into microservices on EKS, use Kubernetes DNS-based service discovery for inter-service communication. For external integrations, consider a service registry pattern. For the update service, externalize the endpoint to configuration. |
| **Evidence** | `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (hardcoded update service URL), database-stored integration settings |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Media metadata (series images, episode screenshots, banners) is stored on the local file system in the application's data directory. Media files themselves are stored on user-configured root folders (local or network-attached storage). No S3 or managed object storage is used. The application handles media file analysis (FFprobe integration) locally. |
| **Gap** | Data in local file systems with limited accessibility. No managed object storage, no parsing pipeline for media metadata. |
| **Recommendation** | Migrate metadata storage (images, cached data) to Amazon S3. For media files, S3 File Gateway could bridge the existing file-system-dependent access patterns without requiring application changes. Use S3 lifecycle policies for tiered storage of older media. |
| **Evidence** | `src/NzbDrone.Core/Sonarr.Core.csproj` (FFMpegCore, FFprobeStatic, SixLabors.ImageSharp for local media processing), `src/NzbDrone.Core/MediaFiles/` directory |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application uses a centralized data access layer with a `BasicRepository<T>` base class and Dapper as the micro-ORM. All database access goes through repository interfaces registered in the DI container. FluentMigrator manages schema evolution. The pattern is consistent across all domains. Some raw SQL exists in specific repositories for complex queries, but it follows the same pattern. |
| **Gap** | Mostly centralized with some direct Dapper SQL in specialized repositories that bypass the standard `BasicRepository<T>` patterns for performance-critical queries. |
| **Recommendation** | The existing centralized repository pattern is a strength. When migrating to Aurora PostgreSQL, the existing Dapper + Npgsql stack requires no changes. Ensure any remaining raw SQL queries are PostgreSQL-compatible (they likely already are given the existing PostgreSQL support). |
| **Evidence** | `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Sonarr.Core.csproj` (Dapper 2.1.72), `src/NzbDrone.Core/Datastore/Migration/` (~210 migrations) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application targets PostgreSQL 16, 17, and 18 (all actively tested in CI). These are all current, supported versions with no EOL concerns. SQLite is embedded and versioned via the NuGet package. The CI pipeline explicitly tests against specific PostgreSQL versions, demonstrating version awareness. However, no explicit version pinning exists in IaC (because no IaC exists) and there is no documented version-update procedure. |
| **Gap** | Versions are tested but not pinned in infrastructure definition. No documented version-update procedure covering downtime windows and rollback. |
| **Recommendation** | When deploying to Aurora PostgreSQL, pin the engine version in IaC (CDK/Terraform). Document the version upgrade procedure including: backup, test against new version, blue/green engine upgrade, rollback plan. |
| **Evidence** | `.github/workflows/build_v5.yml` (PostgreSQL 16, 17, 18 tested), `src/NzbDrone.Core/Sonarr.Core.csproj` (Npgsql 10.0.2) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. All business logic resides in the C# application layer. Database migrations are handled via FluentMigrator using C# code (not raw SQL). The application uses standard ANSI SQL via Dapper with PostgreSQL-compatible queries. No T-SQL, PL/SQL, or other proprietary SQL dialect is present. |
| **Gap** | N/A — no stored procedures or proprietary SQL. |
| **Recommendation** | N/A — the clean separation of business logic from the database layer is a significant strength for any database migration or modernization effort. |
| **Evidence** | `src/NzbDrone.Core/Datastore/Migration/` (~210 C# migration files, no .sql files), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Dapper-based queries) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud-native audit logging exists. The application has internal authentication logging (login success/failure with IP addresses via NLog) and a log cleansing mechanism that scrubs sensitive data from logs. However, there is no immutable audit trail, no centralized log aggregation, and no compliance-grade audit infrastructure. |
| **Gap** | No CloudTrail or equivalent cloud audit logging. Internal auth logging exists but is local, mutable, and not centralized. |
| **Recommendation** | When deployed to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Ship application logs to CloudWatch Logs with appropriate retention policies. The existing NLog framework supports Syslog output which can be directed to CloudWatch. |
| **Evidence** | `src/Sonarr.Http/Authentication/AuthenticationService.cs` (auth logging), `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` (log sanitization), no CloudTrail configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No KMS or managed encryption at rest is configured (no cloud infrastructure exists). The SQLite database is stored as an unencrypted file on disk. PostgreSQL encryption depends on the user's own configuration. The application does use ASP.NET Core Data Protection (keys persisted to file system) for cookie/token encryption, but this is application-level, not storage-level encryption. |
| **Gap** | Mix of encryption types with coverage gaps. Application-level token encryption exists, but database storage has no configured encryption at rest. |
| **Recommendation** | When deploying to Aurora PostgreSQL, enable storage encryption with a customer-managed KMS key (enabled by default on Aurora). For any S3 buckets (metadata, backups), enable SSE-KMS with a centralized key policy. Ensure EBS volumes (if EKS uses them) have encryption enabled. |
| **Evidence** | `src/NzbDrone.Host/Startup.cs` (Data Protection with file-system key persistence), no KMS configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses API key authentication (`X-Api-Key` header or `apikey` query parameter) for all API endpoints. A fallback authorization policy requires authentication on all endpoints except those marked `[AllowAnonymous]`. Username/password login is also supported for the UI. However, this is a static API key pattern — not OAuth2/JWT token-based auth. The API key is a single shared secret with no per-user attribution, no token expiration, and no scoped permissions. |
| **Gap** | API key or static credential authentication without token-based auth. No per-user attribution, no token expiration, no permission scoping. |
| **Recommendation** | When deploying to AWS, integrate with Amazon Cognito for OAuth2/JWT authentication. Use API Gateway authorizers for token validation. The existing authentication middleware can be extended to validate JWT tokens alongside or instead of API keys. Consider maintaining API key support for backward compatibility with existing integrations (download clients, third-party tools). |
| **Evidence** | `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs` (auth configuration), `src/NzbDrone.Common/Options/AuthOptions.cs` (ApiKey option) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely with no external identity provider integration. Users are stored in the local database via `IUserService`. Authentication can be configured as Forms (username/password), External (reverse proxy header), or None (disabled). There is no OIDC, SAML, or OAuth federation capability. No Cognito, Okta, or any other IdP integration exists. |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. |
| **Recommendation** | Integrate with Amazon Cognito as a centralized identity provider. Implement OIDC authentication flow for the web UI. This enables SSO across multiple *arr suite applications and provides MFA, password policies, and audit trails without custom implementation. |
| **Evidence** | `src/NzbDrone.Core/Authentication/` (local user management), `src/Sonarr.Http/Authentication/AuthenticationBuilderExtensions.cs` (custom auth schemes only) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials are hardcoded in source code. Secrets (API key, PostgreSQL password, SSL certificate password) are stored in an XML configuration file on disk (`config.xml`) at runtime. The configuration file is generated on first run. Log cleansing actively scrubs secrets from log output. However, there is no secrets rotation, no encrypted storage, and no integration with AWS Secrets Manager or HashiCorp Vault. Database credentials for PostgreSQL are passed via configuration file or environment variables without encryption. |
| **Gap** | No plaintext credentials in source, but production credentials are kept in a local XML config file and environment variables without encryption or rotation. No secrets manager integration. |
| **Recommendation** | When deploying to AWS, store all secrets in AWS Secrets Manager with automated rotation. Use IAM database authentication for Aurora PostgreSQL where possible. Replace the XML config file with environment variables sourced from Secrets Manager (via EKS secrets store CSI driver or similar). |
| **Evidence** | `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (XML config with secrets), `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` (log sanitization), no Secrets Manager references |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or managed patching strategy exists. The application relies on its self-update mechanism to patch itself, but the underlying OS and runtime are entirely user-managed. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base images. The existing Dockerfile uses `ubuntu:focal` (an older Ubuntu version). |
| **Gap** | No evidence of patching strategy, no vulnerability scanning, no hardened images. |
| **Recommendation** | Use hardened container base images (e.g., `mcr.microsoft.com/dotnet/aspnet:10.0-alpine` or AWS Bottlerocket for EKS nodes). Enable Amazon Inspector for container vulnerability scanning. Integrate Dependabot for NuGet package vulnerability alerts (currently only monitors devcontainers). Add container image scanning in the CI pipeline. |
| **Evidence** | `distribution/docker-build/Dockerfile` (ubuntu:focal base), `.github/dependabot.yml` (only devcontainers ecosystem monitored) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependabot is configured but only monitors the devcontainers ecosystem — it does not scan NuGet packages, npm packages, or GitHub Actions. No SAST tool (SonarQube, Semgrep, CodeGuru) is integrated into the CI/CD pipeline. No container image scanning. The CI pipeline runs tests but has no explicit security validation stage. |
| **Gap** | Dependency scanning is configured but with minimal scope (devcontainers only). No SAST tool and no container scanning in the pipeline. |
| **Recommendation** | Expand Dependabot to cover `nuget` and `npm` ecosystems. Add a SAST tool (GitHub Code Scanning with CodeQL, or Amazon CodeGuru Reviewer) to the CI pipeline. Add container image scanning when Dockerfiles are created. Consider adding `dotnet list package --vulnerable` as a pipeline step. |
| **Evidence** | `.github/dependabot.yml` (devcontainers only), `.github/workflows/build_v5.yml` (no security scanning step) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. The application uses NLog for structured logging and Sentry for error/crash reporting, but there is no OpenTelemetry, X-Ray, or any trace ID propagation. Request correlation across the application's internal components relies on NLog's NDC/MDC context, not distributed trace headers. |
| **Gap** | No distributed tracing instrumented. No trace ID propagation across any boundary. |
| **Recommendation** | Add OpenTelemetry SDK for .NET with the AWS X-Ray exporter. The OpenTelemetry auto-instrumentation for ASP.NET Core and HTTP clients will provide immediate value. Propagate trace context through the existing SignalR connections and to external service calls (download clients, indexers). |
| **Evidence** | `src/NzbDrone.Common/Sonarr.Common.csproj` (NLog 5.5.1, NLog.Layouts.ClefJsonLayout), `src/NzbDrone.Host/Sonarr.Host.csproj` (Sentry 5.16.3), no OpenTelemetry references |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs are defined. No formal service level objectives, error budgets, or latency targets exist in the repository. The application has health checks (20+ internal checks for indexers, download clients, disk space) but these are operational status indicators, not SLO definitions. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for any user journey. |
| **Recommendation** | Define SLOs for critical user journeys: API response latency (p99 < 500ms for read endpoints), download tracking completeness (99.9% of completed downloads are imported), and series metadata freshness (refreshed within 24h of air date). Implement SLO monitoring with CloudWatch and error budget tracking. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` (operational checks, not SLOs), no SLO definition files |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The application has no CloudWatch custom metrics, no business event telemetry, and no outcome-focused measurement. Sentry captures errors but not business outcomes. Internal statistics exist only in the UI (series count, episode status, queue depth) but are not published to any metrics system. |
| **Gap** | No custom metrics — only default infrastructure-level error reporting via Sentry. |
| **Recommendation** | Publish custom CloudWatch metrics for business outcomes: episodes grabbed per hour, import success/failure rates, indexer response times, queue depth over time, and download client availability. These metrics will drive informed scaling decisions and SLO monitoring. |
| **Evidence** | No CloudWatch, Prometheus, or metrics SDK references. `src/NzbDrone.Host/Sonarr.Host.csproj` (Sentry for errors only). |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. The application has internal health checks that display warnings in the UI (indexer failures, disk space low, download client issues) but these are user-facing notifications, not operational alerts. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no threshold-based or anomaly-based alerting exists. |
| **Gap** | No alerting configured — only in-app health status display for users. |
| **Recommendation** | Configure CloudWatch alarms for: API error rate > threshold, command queue depth anomaly, database connection failures, and CPU/memory utilization. Integrate with SNS or EventBridge for alert routing. Use CloudWatch anomaly detection on key metrics once business metrics are published. |
| **Evidence** | `src/NzbDrone.Core/HealthCheck/` (in-app checks only), no alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application uses a custom self-update mechanism that downloads a new binary, stops the running process, replaces files in-place, and restarts. This is a direct-to-production deployment with no staged rollout, no canary, no blue/green, and no automated rollback (rollback requires manual intervention or restore from backup). The application refuses to self-update inside Docker containers, telling users to update the container image instead. |
| **Gap** | Direct-to-production deployment with no staged rollout. In-place binary replacement with no automated rollback capability. |
| **Recommendation** | When containerized on EKS, implement Kubernetes rolling updates with readiness probes (using the existing `/ping` endpoint). Progress to canary deployments using Argo Rollouts or AWS App Mesh traffic shifting. The existing health check infrastructure provides readiness signals for safe rollout. |
| **Evidence** | `src/NzbDrone.Core/Update/InstallUpdateService.cs` (in-place update), `src/NzbDrone.Core/Update/UpdateCheckService.cs` (update check) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist in `src/NzbDrone.Integration.Test/` covering 18 API test fixtures (Blocklist, Calendar, Command, DiskSpace, DownloadClient, EpisodeFile, Episode, FileSystem, History, Indexer, NamingConfig, Notification, Queue, Release, RootFolder, SeriesEditor, Series, SeriesLookup) plus CORS, HTTP logging, and generic API fixtures. Tests run in CI on 3 platforms (Ubuntu, macOS, Windows). PostgreSQL-specific tests run against versions 16, 17, 18. |
| **Gap** | Integration tests cover primary API workflows but there may be gaps in end-to-end download workflow testing (indexer → grab → download client → import chain). No contract tests with external services. |
| **Recommendation** | Add contract tests for external service integrations (download clients, indexers) to catch breaking changes. Consider adding end-to-end smoke tests for the download → import workflow. The existing test infrastructure is solid and can be extended. |
| **Evidence** | `src/NzbDrone.Integration.Test/ApiTests/` (18 fixtures), `.github/workflows/build_v5.yml` (integration_test job on 3 platforms) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. No runbooks (manual or automated), no Systems Manager Automation documents, no self-healing patterns. The application has internal recovery mechanisms (SQLite corruption detection, Postgres retry logic) but no operational incident response infrastructure. |
| **Gap** | No runbooks — incident response is entirely ad hoc. |
| **Recommendation** | Create SSM Automation runbooks for common incidents: database connection failure recovery, container restart on health check failure, log rotation issues. Implement Kubernetes pod disruption budgets and automatic pod replacement. Create operational runbooks in Markdown as a minimum starting point. |
| **Evidence** | No runbook files, no SSM documents, no automation scripts. Internal retry logic in `DbFactory.cs` is application-level, not operational. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership model exists. No CODEOWNERS for observability configs, no per-service dashboards, no named alarm owners. The application has no CloudWatch dashboards, no team attribution on monitoring resources. The internal health check system has no ownership concept — it's a single-developer/user-facing feature. |
| **Gap** | No observability ownership — monitoring is reactive and limited to the in-app health display. |
| **Recommendation** | When deployed to AWS, establish observability ownership: define CODEOWNERS for monitoring infrastructure, create per-domain dashboards (downloads, indexers, media management), assign alarm ownership to responsible teams or individuals. Use CloudWatch dashboards with annotations for deployment events. |
| **Evidence** | No CODEOWNERS file referencing monitoring, no dashboard definitions, no alarm configurations |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists (no cloud resources exist). No tagging standards, no tag enforcement policies, no cost allocation tags. |
| **Gap** | No tags found on resources; no tagging governance or standard defined. |
| **Recommendation** | When defining IaC, implement a tagging standard from day one. Minimum required tags: `Environment` (dev/staging/prod), `Service` (sonarr), `Team` (owner), `CostCenter`, `ManagedBy` (CDK/Terraform). Use CDK Aspects or Terraform `default_tags` to enforce tagging. Enable AWS Cost Allocation Tags for cost tracking. |
| **Evidence** | No IaC files with tags, no tagging documentation |

---

## Learning Materials

- **Move to Cloud Native**: [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Containers**: [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/)
- **Move to Managed Databases**: [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Modern DevOps**: [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `global.json` | INF-Q1, APP-Q1 | .NET SDK version 10.0.201 |
| `.github/workflows/build_v5.yml` | INF-Q1, INF-Q11, DATA-Q3, OPS-Q6, SEC-Q7 | Main CI/CD pipeline with multi-platform builds and tests |
| `.github/workflows/deploy.yml` | INF-Q11 | Package and release pipeline |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Dependency monitoring (devcontainers only) |
| `.github/actions/` | INF-Q11 | 5 composite actions for build pipeline |
| `distribution/docker-build/Dockerfile` | INF-Q1, SEC-Q6 | Legacy Mono-based build Dockerfile |
| `src/Sonarr.sln` | APP-Q2 | Solution structure — single deployable monolith |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | INF-Q2, OPS-Q7 | Database creation with SQLite/PostgreSQL support |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | INF-Q2, SEC-Q5 | Connection string management (config file/env vars) |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | DATA-Q2, APP-Q2 | Centralized data access layer |
| `src/NzbDrone.Core/Datastore/Migration/` | DATA-Q2, DATA-Q3, DATA-Q4 | ~210 FluentMigrator C# migrations |
| `src/NzbDrone.Core/Sonarr.Core.csproj` | APP-Q1, DATA-Q2, DATA-Q3 | Core project dependencies (Dapper, Npgsql, FluentMigrator) |
| `src/NzbDrone.Host/Startup.cs` | INF-Q5, INF-Q6, SEC-Q2, SEC-Q3 | ASP.NET Core startup with auth, CORS, middleware |
| `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | SEC-Q3 | API key authentication implementation |
| `src/Sonarr.Http/Authentication/AuthenticationService.cs` | SEC-Q1, SEC-Q4 | Authentication service with local user management |
| `src/NzbDrone.Core/Authentication/` | SEC-Q4 | Local user/password management |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | SEC-Q5, APP-Q6 | XML config with secrets, hardcoded service URLs |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | SEC-Q1, SEC-Q5 | Log sanitization for secrets |
| `src/NzbDrone.Common/Sonarr.Common.csproj` | OPS-Q1 | NLog 5.5.1, NLog.Layouts.ClefJsonLayout |
| `src/NzbDrone.Host/Sonarr.Host.csproj` | OPS-Q1, OPS-Q3 | Sentry 5.16.3 error reporting |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueue.cs` | APP-Q4, INF-Q3 | In-process priority command queue |
| `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` | APP-Q4, INF-Q3 | 3-thread background executor |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | APP-Q3, INF-Q4 | In-process event pub/sub |
| `src/NzbDrone.Core/Jobs/Scheduler.cs` | APP-Q4 | Timer-based scheduled task execution |
| `src/NzbDrone.Core/Update/InstallUpdateService.cs` | OPS-Q5 | Self-update mechanism (in-place binary replacement) |
| `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` | OPS-Q2, OPS-Q4 | 20+ internal health checks |
| `src/NzbDrone.Integration.Test/` | OPS-Q6 | 18 API integration test fixtures |
| `src/Sonarr.Api.V3/openapi.json` | APP-Q5 | OpenAPI V3 specification |
| `src/Sonarr.Api.V5/openapi.json` | APP-Q5 | OpenAPI V5 specification |
| `src/NzbDrone.Core/MediaFiles/` | DATA-Q1 | Local file system media management |
| `package.json` | APP-Q1 | Frontend: React 18, TypeScript 5.7, Sentry browser |
| `src/NzbDrone.SignalR/MessageHub.cs` | APP-Q6 | Real-time SignalR communication |
| `src/Sonarr.Http/Ping/PingController.cs` | OPS-Q5 | Health/liveness endpoint at /ping |
