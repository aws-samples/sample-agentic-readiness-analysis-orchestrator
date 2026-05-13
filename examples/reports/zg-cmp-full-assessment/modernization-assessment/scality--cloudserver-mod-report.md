# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | S3 (Zenko CloudServer) |
| **Date** | 2025-04-29 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, storage, s3 |
| **Context** | Scality open-source S3-compatible object-storage server. |
| **Overall Score** | 2.12 / 4.0 |

**Archetype Justification**: MongoDB metadata persistence with configurable data backends (file, mem, S3, Azure, GCP), full CRUD S3 API surface (PutObject, GetObject, DeleteObject, PutBucket, DeleteBucket, multipart uploads), and no high fan-out to downstream services. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.29 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.89 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.12 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found — all infrastructure is manually created or undefined | Blocks reproducible deployments, disaster recovery, and all infrastructure modernization pathways |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute orchestration (ECS/EKS/Lambda) defined; app runs as raw Docker container | Prevents elastic scaling, automated patching, and cost-optimized compute |
| 3 | INF-Q2: Managed Databases | 1 | MongoDB is self-managed on localhost replica set with no managed database service | Manual patching, backup, and scaling; single point of operational failure |
| 4 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumented; only request UIDs in werelogs | Debugging production issues across service boundaries is guesswork |
| 5 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group definitions found | Services may be exposed without network isolation; blast radius is unlimited |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3; CI/CD pipeline exists with GitHub Actions (tests.yaml, release.yaml) including lint, unit test, build, and Docker push stages.
- **What it enables:** An agent that triggers CI pipeline runs, checks build/test status, monitors release workflows, and manages Docker image tagging via GitHub Actions API.
- **Additional steps:** Generate GitHub API tokens for agent access; expose pipeline status via webhook or polling.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists — `docs/` directory with 15+ files (ARCHITECTURE.rst, GETTING_STARTED.rst, CLIENTS.rst, DOCKER.rst, INTEGRATIONS.rst, MD_SEARCH.rst, etc.), plus README.md, DESIGN.md, Healthchecks.md, CONTRIBUTING.md, TESTING.md.
- **What it enables:** A Bedrock-powered RAG agent that indexes existing documentation and answers developer questions about S3 API operations, deployment procedures, architecture decisions, and configuration options.
- **Additional steps:** Index documentation corpus into a vector store (e.g., Amazon OpenSearch with vector engine); create a Bedrock knowledge base pointing to the indexed content.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3; unified data access layer exists via `DataWrapper` and `MetadataWrapper` patterns from the arsenal library, providing centralized interfaces for data and metadata operations.
- **What it enables:** An agent that queries MongoDB metadata collections (buckets, objects, users) using natural language, useful for operational troubleshooting and reporting.
- **Additional steps:** Expose read-only query interface to MongoDB metadata; implement query sanitization for safety.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute), APP-Q3=1 (all sync), APP-Q4=2 (limited async) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but Dockerfile exists — app is already containerized. Guard: container definitions found. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); MongoDB is already open source — no commercial DB detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed MongoDB), DATA-Q3=2 (no engine version pinning) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected; no streaming/ETL/analytics artifacts found. Contextual guard: stateful-crud with no streaming. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), OPS-Q5=1 (no deployment strategy) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context "Scality open-source S3-compatible object-storage server." |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a tightly-coupled monolith (APP-Q2=2) deployed as a single Docker container. Internal modules (api/, data/, metadata/, auth/, kms/, routes/, utilities/) have identifiable boundaries but share a single process, single package.json, and common state through the Config singleton. Cross-module coupling exists via direct imports and shared in-memory configuration updates.

**Compute Model Gaps:** No managed compute orchestration defined (INF-Q1=1). The app runs as a raw Docker container with `yarn start`. No ECS task definitions, no EKS manifests, no Lambda functions. The Node.js cluster module provides basic multi-process execution but no elastic scaling.

**Communication Pattern Gaps:** All inter-service communication is synchronous HTTP (APP-Q3=1). The app communicates with vaultd, bucketd, backbeat, and workflowEngineOperator via hardcoded localhost endpoints. Bucket notification destinations exist but use a "dummy" type with no managed messaging. For a stateful-crud archetype handling cross-service state changes (replication, lifecycle, notifications), the absence of async messaging creates tight coupling.

**Recommended Decomposition Approach:** Strangler Fig pattern — incrementally extract high-value services (e.g., KMS service, auth service) while keeping the core S3 API running. See Decomposition Strategy section below.

**Representative AWS Services:** Amazon EKS (preferred per preferences), API Gateway (preferred), EventBridge (preferred for async events), Step Functions for multipart upload orchestration, DynamoDB (preferred) or Aurora (preferred) for metadata.

**Recommended Patterns:**
- **Strangler Fig** — Extract KMS, auth, and notification subsystems as independent services
- **Anti-corruption Layer** — Isolate extracted services from monolith's internal data model
- **Event Sourcing** — Capture object lifecycle events (create, delete, replicate) as event streams via EventBridge

**AWS Prescriptive Guidance:**
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** MongoDB is configured as a self-managed replica set on `localhost:27018,27019,27020` (config.json `mongodb.replicaSetHosts`). Write concern is set to "majority" with "primary" read preference. The database stores all object and bucket metadata.

**Engine Version & EOL Status:** No MongoDB engine version is pinned in any configuration file or IaC (DATA-Q3=2). The MongoDB Node.js driver is pinned at `^6.11.0` in package.json, which supports MongoDB 5.0+. Without explicit engine version management, the deployment may be running an EOL MongoDB version.

**Data Access Patterns:** The `MetadataWrapper` from arsenal provides a centralized abstraction layer (DATA-Q2=3) supporting multiple backends (mem, file, scality, mongodb, cdmi). Migration to a managed service requires updating the metadata backend configuration and potentially the wrapper implementation.

**Recommended Migration Target:** Amazon DocumentDB (MongoDB-compatible) for direct compatibility with existing MongoDB driver and queries. Alternatively, consider Amazon DynamoDB (preferred per preferences) for metadata if the data model can be adapted to key-value access patterns, or Aurora (preferred) if relational patterns emerge.

**Representative AWS Services:** Amazon DocumentDB, Amazon DynamoDB, Aurora, AWS DMS for migration tooling.

**Migration Approach:**
1. Deploy Amazon DocumentDB cluster with Multi-AZ
2. Use AWS DMS to replicate existing MongoDB data to DocumentDB
3. Update `config.json` `mongodb.replicaSetHosts` to point to DocumentDB endpoints
4. Validate with existing functional test suite (extensive coverage exists)
5. Decommission self-managed MongoDB

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** No IaC files exist (INF-Q10=1). No Terraform, CloudFormation, CDK, Helm charts, or Kustomize manifests were found. All infrastructure (compute, networking, databases) is either manually created or undefined in the repository.

**Current CI/CD State:** GitHub Actions workflows exist (INF-Q11=3) with comprehensive stages: lint (JS, Python, YAML, Markdown), unit tests with coverage, Docker image build and push, functional tests in multiple configurations (file backend, MongoDB v0/v1, multiple backends, KMIP, SSE migration), and a release workflow. However, there is no automated deployment to any environment — the release workflow only builds/pushes Docker images and creates GitHub releases.

**Deployment Strategy Gaps:** No canary, blue/green, or rolling deployment configuration (OPS-Q5=1). Docker images are pushed to GHCR but no deployment automation exists.

**Testing Gaps:** Integration testing is strong (OPS-Q6=4) with extensive functional test suites. This is a solid foundation for a deployment pipeline.

**Recommended DevOps Toolchain:**
1. **IaC:** Define all infrastructure in CDK or Terraform — EKS cluster (preferred), DocumentDB/DynamoDB, networking, security groups
2. **Deployment:** AWS CodePipeline or GitHub Actions with deployment stages to EKS via Helm charts
3. **Deployment Strategy:** Implement canary deployments using EKS with Argo Rollouts or AWS App Mesh traffic shifting
4. **Environment Parity:** Use IaC to create staging and production environments with identical configurations

**Representative AWS Services:** CDK, CloudFormation, CodePipeline, CodeBuild, CodeDeploy, EKS (preferred), ECR.

**AWS Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

*Included because APP-Q2 = 2 (< 3)*

### Decomposition Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2=2 — identifiable modules (api/, auth/, kms/, data/, metadata/) with coupling via Config singleton and shared imports. Team can sustain parallel development. | **Medium to High** — 6-18 months | ✅ **Recommended.** Extract KMS, auth/vault, and notification subsystems first while core S3 API remains. |
| **Conditional / Adaptive** | Team has limited capacity; containerize monolith on EKS first, then selectively extract high-value services based on scaling needs. | **Low to Medium** — containerization in 2-4 weeks (Dockerfile exists), selective extraction over 3-12 months | ✅ **Recommended when capacity is constrained.** Deploy on EKS as-is first, then extract. |
| **Big-Bang Rewrite** | Almost never. Only if monolith is unmaintainable. | **Very High** — 12-24+ months | ⚠️ **Recommended against.** The codebase is well-structured with clear module separation. Incremental extraction is safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate new services from monolith's Config singleton and internal data models | Every extraction — place ACL between new service and monolith |
| **Saga Pattern** | Manage distributed transactions (e.g., multipart upload → metadata update → notification) | When extracting modules participating in multi-step operations |
| **Event Sourcing** | Capture object lifecycle events as EventBridge events | When extracting notification, replication, and lifecycle subsystems |
| **Hexagonal Architecture** | Structure each new service with clear ports and adapters | Every new service — ensures testability and portability |

### Effort Estimation Factors

| Factor | Current Signal | Effort Impact |
|--------|---------------|---------------|
| Module boundaries | Clear package structure (api/, data/, metadata/, auth/, kms/) — LOW effort | ✅ Favorable |
| Data coupling | MetadataWrapper abstracts DB access; DataWrapper abstracts storage — MODERATE coupling | 🟡 Manageable |
| Stored procedures | None — all logic in JavaScript (DATA-Q4=4) | ✅ Favorable |
| Communication patterns | All synchronous HTTP (APP-Q3=1) — HIGH effort to decouple | 🟠 Significant |
| CI/CD maturity | Strong CI with functional tests (INF-Q11=3, OPS-Q6=4) — LOW effort to extend | ✅ Favorable |
| Test coverage | Extensive functional tests covering all S3 operations — LOW regression risk | ✅ Favorable |

**Calibrated Estimate:** With strong test coverage and clear module boundaries, the **Conditional/Adaptive** approach (deploy on EKS first, then extract) is recommended as the initial phase, followed by **Strangler Fig** extraction of KMS, auth, and notification services. Total timeline: 3-6 months for EKS deployment, 6-12 months for first service extractions.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute orchestration is defined in the repository. The application runs as a Docker container (`Dockerfile` using `node:22.14.0-bookworm-slim`) and is started with `yarn start`. No ECS task definitions, EKS manifests, Lambda functions, or Fargate configurations exist. The `DockerfileMem` is a legacy Node 6 image. The CI pipeline builds and pushes Docker images to GHCR but does not deploy to any managed compute service. |
| **Gap** | All compute is Docker-only with no managed orchestration. No elastic scaling, no automated health-based restarts, no infrastructure-level load balancing. |
| **Recommendation** | Deploy on Amazon EKS (preferred) with Fargate for serverless pod execution. Create Helm charts or Kustomize manifests for the CloudServer deployment, leveraging the existing Dockerfile. |
| **Evidence** | `Dockerfile`, `DockerfileMem`, `.github/workflows/release.yaml`, `config.json` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | MongoDB is self-managed, configured as a replica set at `localhost:27018,27019,27020` in `config.json`. The MongoDB driver `mongodb ^6.11.0` is in `package.json`. Docker compose files in CI spin up MongoDB containers for testing. No `aws_rds_*`, `aws_dynamodb_*`, or `aws_docdb_*` resources exist. Redis is used optionally for local caching (health check stats). |
| **Gap** | All databases are self-managed — MongoDB runs on localhost with no managed service, no automated backups, no automated failover beyond the replica set. |
| **Recommendation** | Migrate to Amazon DocumentDB (MongoDB-compatible) for immediate compatibility, or evaluate DynamoDB (preferred) for metadata if access patterns allow. Use AWS DMS for migration. |
| **Evidence** | `config.json` (mongodb section), `package.json` (mongodb dependency), `.github/docker/` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype: stateful-crud.** Multi-step workflows exist: multipart uploads (initiate → upload parts → complete), object lifecycle management, SSE key migration, and cross-region replication coordination. These are implemented as sequential application code in `lib/api/completeMultipartUpload.js`, `lib/api/initiateMultipartUpload.js`, and `lib/api/objectRestore.js`. No Step Functions, Temporal, or dedicated orchestration service is used. |
| **Gap** | Simple state machines in code with some structure (multipart upload has defined steps) but no dedicated orchestration service. Error handling and retry logic are embedded in application code. |
| **Recommendation** | Extract multipart upload coordination and object lifecycle workflows into AWS Step Functions for visibility, retry management, and error handling. |
| **Evidence** | `lib/api/completeMultipartUpload.js`, `lib/api/initiateMultipartUpload.js`, `lib/api/objectRestore.js`, `constants.js` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **Archetype: stateful-crud.** No managed messaging infrastructure exists. `config.json` has `bucketNotificationDestinations` configured with a dummy localhost endpoint. The application communicates with backbeat (replication/lifecycle engine) and workflowEngineOperator via synchronous HTTP. For a stateful-crud archetype, cross-service state changes (replication events, lifecycle transitions, notifications) should use async messaging but instead rely on synchronous HTTP calls. |
| **Gap** | No messaging — state changes cross service boundaries via synchronous HTTP. Tight coupling between CloudServer and backbeat/workflowEngineOperator creates cascading failure risk. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for bucket notification events, object lifecycle events, and replication triggers. Replace synchronous HTTP calls to backbeat with event-driven patterns. |
| **Evidence** | `config.json` (bucketNotificationDestinations, backbeat, workflowEngineOperator), `lib/routes/routeBackbeat.js` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation definitions exist in the repository. No IaC is present to define network topology. The application listens on port 8000 (S3 API) and port 8002 (metrics) without any network-level access controls defined in code. Health check endpoints are IP-restricted via `config.json` `healthChecks.allowFrom` (127.0.0.1/8, ::1). |
| **Gap** | Services deployed without defined network isolation. No VPC, no private subnets, no security groups. The health check IP restriction is application-level only. |
| **Recommendation** | Define VPC, private subnets, and security groups in IaC (CDK or Terraform). Place CloudServer in private subnets with an API Gateway (preferred) or ALB for ingress. Use VPC endpoints for AWS service access. |
| **Evidence** | `config.json` (healthChecks.allowFrom, port, metricsPort) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync is defined. The S3 server exposes port 8000 directly for S3 API traffic and port 8002 for metrics. `config.json` `restEndpoints` maps hostnames to regions but provides no throttling, authentication at the gateway level, or request validation before the application. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, no WAF, no TLS termination at the edge. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the S3 API entry point with throttling, request validation, and WAF integration. Alternatively, use an ALB with target groups pointing to EKS pods. |
| **Evidence** | `config.json` (port: 8000, restEndpoints), `lib/server.js` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application uses Node.js `cluster` module to fork worker processes based on `config.json` `clusters` setting (default: 1), but this is static in-process scaling only. No ASG, ECS service auto-scaling, EKS HPA, or Lambda concurrency limits are defined. |
| **Gap** | All capacity is statically provisioned. No response to traffic spikes or scale-down during low demand. |
| **Recommendation** | Deploy on EKS (preferred) with Horizontal Pod Autoscaler (HPA) based on CPU/memory and custom metrics (HTTP request rate from Prometheus). Configure cluster autoscaler for node-level scaling. |
| **Evidence** | `config.json` (clusters: 1), `lib/server.js` (cluster module usage) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found in the repository. No `aws_backup_plan`, no `backup_retention_period`, no PITR configuration. MongoDB is self-managed with no automated backup evident. Data volumes (`localData/`, `localMetadata/`) have no snapshot or backup policies. |
| **Gap** | No backup configuration — a data loss event would wipe all metadata and local data with no recovery path. |
| **Recommendation** | After migrating to managed databases (DocumentDB/DynamoDB), enable automated backups with PITR. For object data stored on S3 backends, leverage S3 versioning and cross-region replication. Define backup plans in IaC with AWS Backup. |
| **Evidence** | `config.json`, `Dockerfile` (VOLUME declarations for localData, localMetadata) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. The MongoDB replica set is configured on localhost ports (27018-27020), which is a single-host configuration — not true multi-AZ. No IaC defines AZ-aware subnet placement, cross-AZ load balancing, or multi-AZ database deployment. |
| **Gap** | All resources are single-host. An AZ or host failure takes down the entire service with no automatic recovery. |
| **Recommendation** | Deploy on EKS (preferred) across multiple AZs. Use DocumentDB Multi-AZ for metadata. Configure ALB with cross-zone load balancing. |
| **Evidence** | `config.json` (mongodb.replicaSetHosts: localhost), `lib/server.js` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files exist in the repository. No `.tf` files, no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize manifests. All infrastructure (compute, networking, databases, messaging, monitoring) is either manually configured or undefined. The only infrastructure-adjacent files are `Dockerfile` (container build) and `docker-compose.yaml` (CI testing). |
| **Gap** | No IaC — all infrastructure created manually (ClickOps) or undefined. Infrastructure changes are non-reproducible and environment-specific. |
| **Recommendation** | Define all infrastructure in AWS CDK (TypeScript, matching the JavaScript codebase) or Terraform. Start with: EKS cluster, DocumentDB, VPC/networking, API Gateway, and monitoring (CloudWatch alarms from existing Prometheus alerts). |
| **Evidence** | Repository root (no .tf, no cdk.json, no template.yaml), `.github/docker/` (docker-compose for CI only) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI pipeline exists via GitHub Actions: `tests.yaml` runs lint (JS, Python, YAML, Markdown), unit tests with coverage (Codecov integration), Docker image build/push to GHCR, and 10+ functional test jobs (file backend, MongoDB v0/v1, multiple backends, S3C integration, KMIP, SSE migration, utapi, SUR tests). `release.yaml` builds production and federation images and creates GitHub releases with auto-generated release notes. `codeql.yaml` runs SAST. `dependency-review.yaml` scans dependency changes on PRs. |
| **Gap** | CI/CD pipeline has build and test stages but no automated deployment to any environment. The release workflow pushes Docker images and creates GitHub releases but does not deploy. No automated rollback capability. |
| **Recommendation** | Extend the CI/CD pipeline with deployment stages: deploy to staging (automated), run smoke tests, deploy to production with canary rollout on EKS. Add automated rollback on health check failure. |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/release.yaml`, `.github/workflows/codeql.yaml`, `.github/workflows/dependency-review.yaml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application is written in JavaScript (Node.js 22), a first-class language for AWS cloud-native development. `package.json` specifies `engines.node >= 22`. The ecosystem includes AWS SDK (`aws-sdk ^2.1692.0`), comprehensive npm libraries, and mature cloud-native tooling. The codebase also includes Python scripts for monitoring (`monitoring/dashboard.py`) and testing utilities. |
| **Gap** | None — JavaScript/Node.js has excellent AWS SDK coverage and cloud-native tooling. Minor note: using `aws-sdk` v2 rather than `@aws-sdk` v3 (modular). |
| **Recommendation** | Consider migrating from AWS SDK v2 (`aws-sdk`) to AWS SDK v3 (`@aws-sdk/client-*`) for modular imports, reduced bundle size, and improved middleware support. |
| **Evidence** | `package.json` (engines, dependencies), `index.js`, `lib/server.js` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a single deployable monolith with identifiable internal modules. `index.js` → `lib/server.js` starts a single HTTP server handling all S3 API operations. Internal separation exists: `lib/api/` (60+ API handlers), `lib/data/` (data backends), `lib/metadata/` (metadata backends), `lib/auth/` (authentication), `lib/kms/` (encryption key management), `lib/routes/` (routing), `lib/utilities/` (monitoring, logging). However, all modules share a single `Config` singleton, a single process, and a single `package.json`. Cross-module dependencies are direct imports. External services (vaultd, bucketd, backbeat) are accessed via hardcoded localhost endpoints. |
| **Gap** | Monolith with identifiable modules but shared state (Config singleton), direct cross-module imports, and a single deployment unit. Cannot independently scale, deploy, or evolve individual subsystems. |
| **Recommendation** | Apply Strangler Fig pattern to extract KMS, auth/vault, and notification subsystems as independent services. The existing module structure provides natural extraction boundaries. |
| **Evidence** | `index.js`, `lib/server.js`, `lib/api/`, `lib/data/wrapper.js`, `lib/metadata/wrapper.js`, `lib/auth/vault.js`, `lib/kms/wrapper.js`, `lib/Config.js`, `config.json` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **Archetype: stateful-crud.** All communication is synchronous HTTP. The server handles S3 API requests synchronously and communicates with external services (vaultd at localhost:8500, bucketd at localhost:9000, backbeat at localhost:8900, workflowEngineOperator at localhost:3001) via synchronous HTTP. No message queue producers, no event-driven patterns, no async state propagation. Bucket notification destinations are configured but use a "dummy" type. For a stateful-crud archetype with cross-service state changes (replication triggers, lifecycle transitions, notification delivery), the absence of async messaging creates tight synchronous coupling. |
| **Gap** | All communication synchronous HTTP with no async patterns. State changes that cross service boundaries (notifications, replication, lifecycle) are synchronously coupled. |
| **Recommendation** | Introduce EventBridge (preferred) for object lifecycle events (create, delete, replicate). Decouple notification delivery, replication triggers, and lifecycle actions from the synchronous request path. |
| **Evidence** | `config.json` (vaultd, bucketd, backbeat, workflowEngineOperator — all localhost HTTP), `lib/auth/vault.js`, `lib/routes/routeBackbeat.js` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype: stateful-crud.** Multipart uploads can be long-running (5GB max per part, 10000 parts max). The `server.requestTimeout = 0` disables Node.js request timeout to allow long uploads. Object restore operations (`lib/api/objectRestore.js`) delegate to backbeat for async processing. However, multipart uploads are handled synchronously per-part with no status polling API beyond S3's native ListParts. No general async job processing framework exists. The `completeMultipartUpload` operation is synchronous and may take significant time for large uploads. |
| **Gap** | Some background processing exists (object restore → backbeat), but multipart upload completion is synchronous. No general async job framework with status polling or callbacks. |
| **Recommendation** | For the largest operations (completeMultipartUpload with many parts), consider implementing async completion with status polling. Extract long-running operations into Step Functions workflows. |
| **Evidence** | `lib/server.js` (requestTimeout=0), `lib/api/completeMultipartUpload.js`, `lib/api/objectRestore.js`, `constants.js` (maximumAllowedPartCount: 10000) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements the AWS S3 API, which is inherently versioned by AWS specifications. S3 API backward compatibility is maintained by design (AWS S3 API has been stable since 2006). However, internal APIs (backbeat routes at `/_/backbeat/`, metadata routes at `/_/metadata/`, Veeam routes, workflow engine routes) have no versioning. No `/v1/` URL patterns, no version headers, no changelog for internal API changes. |
| **Gap** | Versioning applied ad hoc — S3 API is versioned by AWS spec compliance, but internal service APIs have no versioning scheme. Breaking changes to internal APIs could disrupt backbeat, lifecycle, and replication consumers. |
| **Recommendation** | Introduce version prefixes for internal APIs (e.g., `/_/v1/backbeat/`, `/_/v1/metadata/`). Document API contracts and breaking change policies for internal consumers. |
| **Evidence** | `lib/routes/routeBackbeat.js`, `lib/routes/routeMetadata.js`, `lib/routes/routeVeeam.js`, `lib/routes/routeWorkflowEngineOperator.js` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via `config.json` and environment variables. `vaultd` is at `localhost:8500`, `bucketd` at `localhost:9000`, `backbeat` at `localhost:8900`, `workflowEngineOperator` at `localhost:3001`, `metadataClient` at `127.0.0.1:9990`, `dataClient` at `127.0.0.1:9991`. `docker-entrypoint.sh` allows overriding via environment variables (`DATA_HOST`, `METADATA_HOST`, `PFSD_HOST`, `MONGODB_HOSTS`, etc.). This is static endpoint configuration, not dynamic discovery. |
| **Gap** | Environment variables for endpoints but no dynamic service discovery. Adding or relocating a service requires configuration changes and redeployment. |
| **Recommendation** | When deploying on EKS (preferred), leverage Kubernetes DNS-based service discovery. Internal services become discoverable via `service-name.namespace.svc.cluster.local`. For cross-cluster communication, use AWS Cloud Map or VPC Lattice. |
| **Evidence** | `config.json` (vaultd, bucketd, backbeat, metadataClient, dataClient), `docker-entrypoint.sh` (env var overrides), `lib/Config.js` |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application IS an S3-compatible object storage server. It stores unstructured data using multiple configurable backends: local file system (`localData/` directory, `DataFileInterface`), in-memory (`inMemory`), AWS S3 (`aws_s3`), Azure Blob Storage (`azure`), GCP Cloud Storage (`gcp`), and CDMI. The `MultipleBackendGateway` in `lib/data/wrapper.js` (via arsenal) enables routing objects to different storage backends based on location constraints. |
| **Gap** | Data is accessible through S3 API but no automated parsing or extraction pipeline exists for unstructured content (no Textract, no document indexing). |
| **Recommendation** | For AWS deployment, leverage native S3 as the primary data backend. Add parsing pipelines (Amazon Textract, Amazon Comprehend) for document-heavy workloads if needed by downstream consumers. |
| **Evidence** | `lib/data/wrapper.js`, `locationConfig.json`, `config.json` (externalBackends) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application uses centralized data access wrappers from the `arsenal` library. `DataWrapper` (in `lib/data/wrapper.js`) provides a unified interface for all data backends (file, mem, multiple, cdmi). `MetadataWrapper` (in `lib/metadata/wrapper.js`) provides a unified interface for all metadata backends (mem, file, scality, mongodb, cdmi). All API handlers access data and metadata exclusively through these wrappers. Some direct access to configuration and utilities exists outside the wrapper pattern. |
| **Gap** | Mostly centralized with some direct access in auxiliary code paths (management agent, utility scripts). The wrapper pattern is well-implemented for data and metadata. |
| **Recommendation** | Maintain the wrapper pattern during modernization. When migrating metadata to a managed service (DocumentDB/DynamoDB), update the `MetadataWrapper` backend configuration without changing API handler code. |
| **Evidence** | `lib/data/wrapper.js`, `lib/metadata/wrapper.js`, `lib/api/` (all handlers use data/metadata wrappers) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The MongoDB Node.js driver is pinned at `^6.11.0` in `package.json`, which requires MongoDB server 5.0+. However, no explicit MongoDB engine version is specified in `config.json`, Docker Compose files, or any IaC (none exists). The CI testing uses a custom MongoDB image (`.github/docker/mongodb/`) without visible version pinning in the repository. Without explicit engine version management, the production deployment may drift to an unsupported version. |
| **Gap** | Some versions pinned (driver), others implicit (engine). EOL status unknown for the actual MongoDB engine in production. No version-update procedure documented. |
| **Recommendation** | Pin MongoDB engine version explicitly in deployment configuration. When migrating to DocumentDB, engine version management becomes AWS-managed. Document a version update procedure covering downtime windows, rollback, and risk acknowledgment. |
| **Evidence** | `package.json` (mongodb ^6.11.0), `config.json` (mongodb section — no engine_version), `.github/docker/mongodb/` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. The application uses MongoDB as a document store with all business logic implemented in the JavaScript application layer. No `.sql` files, no `CREATE PROCEDURE`, no `CREATE TRIGGER` found. The `MetadataWrapper` from arsenal provides the data access interface. All query logic is in application code. |
| **Gap** | None — all business logic is in the application layer. |
| **Recommendation** | No action needed. This clean separation makes database migration (to DocumentDB or DynamoDB) significantly easier. |
| **Evidence** | `lib/metadata/wrapper.js`, `package.json` (no SQL-related dependencies), repository-wide search for stored procedures |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements S3 server access logging (`lib/utilities/serverAccessLogger.js`) with a detailed schema (`schema/server_access_log.schema.json`) that captures requester, bucket, key, operation, status, error codes, and timing. This is configurable via `config.json` `serverAccessLogs` section (DISABLED, LOG_ONLY, ENABLED modes). However, this is application-level access logging, not infrastructure audit logging. No CloudTrail or equivalent immutable infrastructure audit trail exists. |
| **Gap** | Partial logging — application-level S3 access logs exist but no infrastructure-level audit logging (CloudTrail) with immutable storage. |
| **Recommendation** | Enable AWS CloudTrail in the target AWS account with log file validation and S3 Object Lock for immutable storage. The existing server access logging complements but does not replace CloudTrail. |
| **Evidence** | `lib/utilities/serverAccessLogger.js`, `schema/server_access_log.schema.json`, `config.json` (serverAccessLogs section) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application supports server-side encryption (SSE) with multiple KMS backends: in-memory, file-based, Scality KMS, KMIP (Thales), and AWS KMS (`lib/kms/wrapper.js`). Bucket-level encryption and per-object encryption are implemented. SSE migration between KMS providers is supported. However, no IaC-level KMS key management exists — the `kmsAWS` config in `config.json` has placeholder `ak`/`sk` values. Local data stored on disk (`localData/`) is not encrypted at the filesystem level. |
| **Gap** | Mix of encryption types with coverage gaps — SSE is available at the application level but no infrastructure-level encryption-at-rest for local storage volumes, and no IaC-managed KMS keys. |
| **Recommendation** | When deploying on AWS, use customer-managed KMS keys defined in IaC for all data stores. Configure EBS volume encryption, DocumentDB encryption, and S3 bucket encryption with KMS. Leverage the existing AWS KMS integration in `lib/kms/wrapper.js`. |
| **Evidence** | `lib/kms/wrapper.js`, `lib/kms/common.js`, `config.json` (kmsAWS, kmip sections) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application implements comprehensive AWS Signature V2 and V4 authentication via the arsenal library's auth module. `lib/auth/vault.js` supports multiple backends: in-memory (from `conf/authdata.json`), Vault (centralized identity), or chained (multiple). All S3 API requests go through authentication middleware. Internal routes (`/_/`) bypass user bucket policies but still authenticate via request headers (`x-scal-request-uids`). Health check endpoints are IP-restricted but not token-authenticated. |
| **Gap** | Token-based auth on all external S3 endpoints. Internal/private endpoints use reduced authentication (IP restriction on health checks, header-based identification for internal routes). |
| **Recommendation** | When deploying behind API Gateway (preferred), add API Gateway authorization (IAM, Cognito, or Lambda authorizer) as an additional authentication layer. Ensure internal routes are only accessible within the VPC. |
| **Evidence** | `lib/auth/vault.js`, `conf/authdata.json`, `lib/server.js` (routeRequest, routeAdminRequest, internalRouteRequest), `config.json` (healthChecks.allowFrom) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application integrates with Vault (`vaultclient` dependency) as a centralized identity provider for production deployments. Vault handles account management, access key verification, and IAM policy evaluation. The `lib/auth/vault.js` supports chained backends (in-memory + Vault) allowing fallback authentication. In-memory auth from `conf/authdata.json` provides standalone development/testing capability. |
| **Gap** | Application uses centralized IdP (Vault) for most flows; in-memory auth path remains for development and fallback. No SSO or OIDC/SAML federation visible. |
| **Recommendation** | When deploying on AWS, integrate with Amazon Cognito for customer-facing identity or continue using Vault if it's the organizational standard. Ensure the in-memory auth backend is disabled in production deployments. |
| **Evidence** | `lib/auth/vault.js`, `config.json` (vaultd section), `conf/authdata.json`, `package.json` (vaultclient dependency) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Mixed secrets management. Docker Swarm secrets are supported via `/run/secrets/s3-credentials` in `docker-entrypoint.sh`. GitHub Actions use GitHub Secrets for CI (Azure keys, GCP keys, AWS keys). However, `config.json` contains placeholder KMS credentials (`kmsAWS.ak: "tbd"`, `kmsAWS.sk: "tbd"`). `conf/authdata.json` contains sample credentials for development (accessKey1/verySecretKey1). Environment variables are used extensively for runtime configuration, including database credentials (`MONGODB_HOSTS`). No AWS Secrets Manager or Vault-based secrets rotation configured. |
| **Gap** | Some secrets in Docker Swarm secrets and GitHub Secrets, but `config.json` has placeholder credentials and `conf/authdata.json` has sample keys committed to the repository. No secrets rotation. |
| **Recommendation** | Migrate all secrets to AWS Secrets Manager with automated rotation. Remove placeholder credentials from `config.json`. Ensure `conf/authdata.json` is clearly marked as development-only and excluded from production builds. Reference secrets from Secrets Manager in EKS pod configurations via External Secrets Operator. |
| **Evidence** | `docker-entrypoint.sh` (/run/secrets/s3-credentials), `config.json` (kmsAWS.ak/sk), `conf/authdata.json` (sample credentials), `.github/workflows/tests.yaml` (GitHub Secrets) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy found. The `Dockerfile` uses `node:22.14.0-bookworm-slim` as the base image — a standard Debian image, not a hardened image. No SSM Agent, no AWS Inspector, no CIS benchmarks, no Bottlerocket. No vulnerability scanning of the container image in CI. The `DockerfileMem` uses an outdated `node:6-slim` base (severely EOL). |
| **Gap** | No evidence of patching strategy, no vulnerability scanning of container images, default base images with no hardening. |
| **Recommendation** | Switch to a hardened base image (Amazon Linux 2023 or Bottlerocket for EKS nodes). Add container image scanning (Amazon ECR image scanning or Trivy) to the CI pipeline. Remove the deprecated `DockerfileMem` (Node 6 is EOL). |
| **Evidence** | `Dockerfile` (node:22.14.0-bookworm-slim), `DockerfileMem` (node:6-slim) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub CodeQL SAST scanning is configured (`.github/workflows/codeql.yaml`) running on push and PR to development/hotfix branches, analyzing JavaScript, Python, and Ruby. Dependency review (`.github/workflows/dependency-review.yaml`) runs on PRs using `actions/dependency-review-action@v4`. No container image scanning is configured. No explicit blocking gate on critical findings. |
| **Gap** | SAST (CodeQL) + dependency scanning in CI, but missing container image scanning and no blocking gate on critical findings. |
| **Recommendation** | Add container image scanning (Amazon ECR scanning or Trivy in CI). Configure CodeQL and dependency review to block PRs on critical/high-severity findings. Add `npm audit` or `yarn audit` to the CI pipeline. |
| **Evidence** | `.github/workflows/codeql.yaml`, `.github/workflows/dependency-review.yaml` |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. The application uses `werelogs` (Scality's logging library) with request UIDs propagated via `x-scal-request-uids` headers. This provides request correlation within the CloudServer process but not distributed tracing across service boundaries (vaultd, bucketd, backbeat). No OpenTelemetry SDK, no X-Ray, no traceparent header propagation found in dependencies or code. |
| **Gap** | No distributed tracing instrumented. Debugging failures across CloudServer → vaultd → bucketd boundaries requires manual log correlation by request UID. |
| **Recommendation** | Instrument with AWS X-Ray or OpenTelemetry SDK. Propagate trace context via W3C traceparent headers to all downstream services (vaultd, bucketd, backbeat). The existing `x-scal-request-uids` header can be mapped to trace IDs for backward compatibility. |
| **Evidence** | `package.json` (werelogs dependency, no OpenTelemetry), `lib/utilities/logger.js`, `lib/server.js` (x-scal-request-uids handling) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus alerting rules in `monitoring/alerts.yaml` define latency and error rate thresholds: system errors warning at 3%, critical at 5%; listing latency warning at 300ms, critical at 500ms; delete latency warning at 500ms, critical at 1s. These function as implicit SLO thresholds but are not formally defined as SLOs with error budgets. No SLO definition files, no error budget tracking. |
| **Gap** | Basic availability/latency alarms exist but no formal SLO definitions with error budgets or burn rate alerts. |
| **Recommendation** | Formalize SLOs based on existing alert thresholds: e.g., "99.9% of S3 API requests complete within 500ms" and "99.95% availability (non-5xx)". Implement error budget tracking and burn rate alerts in Prometheus/Grafana. |
| **Evidence** | `monitoring/alerts.yaml` (SystemErrorsWarning, ListingLatencyWarning, DeleteLatencyWarning) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Custom Prometheus metrics published via `lib/utilities/monitoringHandler.js` include business-relevant metrics: `s3_cloudserver_buckets_count`, `s3_cloudserver_objects_count`, `s3_cloudserver_ingested_objects_count`, `s3_cloudserver_ingested_bytes`, `s3_cloudserver_disk_available_bytes`, `s3_cloudserver_disk_free_bytes`, `s3_cloudserver_disk_total_bytes`, quota metrics (`quota_evaluation_duration`, `quota_unavailable_count`, `utilization_service_available`). HTTP request metrics include action labels enabling per-S3-operation tracking. Grafana dashboard (`monitoring/dashboard.json`) visualizes these metrics. |
| **Gap** | Some business metrics tracked (object counts, storage utilization, quotas) but not systematically across all business features (e.g., no replication success rate, no lifecycle completion metrics in CloudServer itself). |
| **Recommendation** | Add business metrics for replication status, lifecycle operation completion, and per-account/per-bucket utilization trends. Publish these to CloudWatch for integration with AWS dashboards. |
| **Evidence** | `lib/utilities/monitoringHandler.js`, `monitoring/dashboard.json`, `monitoring/alerts.yaml` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Static threshold alerts are defined in `monitoring/alerts.yaml`: error rate > 3%/5%, listing latency > 300ms/500ms, delete latency > 500ms/1s, endpoint availability < 100%/50%, quota metrics unavailability. Alert tests exist in `monitoring/alerts.test.yaml` and `monitoring/alerts.10s.test.yaml`. No anomaly detection — all alerts use fixed thresholds. No CloudWatch anomaly detection or ML-based alerting. |
| **Gap** | Static threshold alarms only. No anomaly detection for gradual degradation, seasonal patterns, or novel failure modes. |
| **Recommendation** | Enable CloudWatch anomaly detection on key metrics (error rate, latency, request rate) after migrating monitoring to AWS. Keep static thresholds as safety nets alongside anomaly-based alerts. |
| **Evidence** | `monitoring/alerts.yaml`, `monitoring/alerts.test.yaml`, `monitoring/alerts.10s.test.yaml` |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The release workflow (`.github/workflows/release.yaml`) builds Docker images, pushes to GHCR with a version tag, pushes monitoring dashboards/alerts as OCI artifacts, and creates a GitHub release. No deployment to any environment is automated. No canary, blue/green, or rolling deployment strategy is defined. No CodeDeploy, Argo Rollouts, or Helm-based deployment. |
| **Gap** | Direct-to-registry image push with no staged deployment. No deployment automation, no traffic shifting, no automated rollback. |
| **Recommendation** | Implement canary deployments on EKS (preferred) using Argo Rollouts or AWS App Mesh for progressive traffic shifting. Define deployment manifests with health check gates and automatic rollback on failure. |
| **Evidence** | `.github/workflows/release.yaml` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Extensive integration/functional test suites covering all critical workflows, run in CI via Docker Compose: `tests/functional/aws-node-sdk/` (S3 SDK tests for buckets, objects, versioning, multipart, external backends), `tests/functional/s3cmd/` (s3cmd CLI tests), `tests/functional/s3curl/` (s3curl tests), `tests/functional/raw-node/` (raw HTTP tests), `tests/functional/backbeat/` (replication tests), `tests/functional/healthchecks/` (health check tests), `tests/functional/kmip/` (KMIP encryption tests), `tests/functional/sse-kms-migration/` (SSE migration tests). Tests run against multiple configurations: file backend, MongoDB v0/v1, multiple backends, S3C integration. Codecov integration tracks coverage. |
| **Gap** | None — integration test coverage is comprehensive and runs in CI. |
| **Recommendation** | Maintain this excellent testing foundation. When deploying on AWS, extend tests to run against managed services (DocumentDB, S3 backends) in a staging environment. |
| **Evidence** | `tests/functional/`, `.github/workflows/tests.yaml` (10+ CI test jobs), `package.json` (ft_* scripts) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | `Healthchecks.md` documents the `/live` health check endpoint with response codes and Redis-based stats. No automated runbooks, no SSM Automation documents, no Lambda-based remediation, no self-healing patterns. Incident response is entirely documentation-based (not automated). |
| **Gap** | No runbooks — incident response is entirely ad hoc. Health check documentation exists but no automated remediation. |
| **Recommendation** | Create SSM Automation runbooks for common incidents (restart unhealthy pods, scale up on high latency, failover MongoDB). Implement self-healing via EKS liveness/readiness probes leveraging the existing `/live` and `/ready` endpoints. |
| **Evidence** | `Healthchecks.md`, `lib/utilities/healthcheckHandler.js` |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `monitoring/` directory contains Prometheus alerts (`alerts.yaml`), alert tests (`alerts.test.yaml`, `alerts.10s.test.yaml`), a Grafana dashboard (`dashboard.json`), and a dashboard generation script (`dashboard.py`). The alerts CI workflow (`.github/workflows/alerts.yaml`) validates alert configurations. However, no named owners on alerts, no team attribution on dashboards, no CODEOWNERS for monitoring assets, no SLO definitions with team responsibility. |
| **Gap** | Ad hoc observability — alerts and dashboards exist but no clear ownership or team attribution. |
| **Recommendation** | Add CODEOWNERS entries for `monitoring/` directory. Tag alerts and dashboards with owning team. Define on-call responsibilities for each alert severity. |
| **Evidence** | `monitoring/alerts.yaml`, `monitoring/dashboard.json`, `monitoring/alerts.test.yaml`, `.github/workflows/alerts.yaml` |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC resources exist to tag. No tagging governance, no `default_tags`, no tag enforcement policies. Docker images in CI are labeled with `git.repository` and `git.commit-sha` but these are container labels, not AWS resource tags. |
| **Gap** | No tags found on resources; no tagging standard. When IaC is created, tagging governance must be established from day one. |
| **Recommendation** | When creating IaC, define mandatory tags (Environment, Team, CostCenter, Service) using `default_tags` in Terraform or CDK stack-level tags. Enforce via AWS Config required-tags rule and Tag Policies. |
| **Evidence** | Repository root (no IaC files), `.github/workflows/release.yaml` (Docker labels only) |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

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
| `package.json` | INF-Q1, INF-Q2, APP-Q1, APP-Q2, DATA-Q3, DATA-Q4, OPS-Q1, OPS-Q6 | Dependencies, engine requirements, scripts |
| `config.json` | INF-Q1–Q9, APP-Q3, APP-Q6, DATA-Q3, SEC-Q1, SEC-Q2, SEC-Q5 | Server config, MongoDB, KMS, endpoints, health checks |
| `Dockerfile` | INF-Q1, SEC-Q6, SEC-Q7 | Multi-stage Docker build, Node 22 bookworm-slim |
| `DockerfileMem` | INF-Q1, SEC-Q6 | Legacy Node 6 Docker image |
| `index.js` | APP-Q2 | Application entry point |
| `lib/server.js` | INF-Q1, INF-Q7, INF-Q9, APP-Q2, APP-Q4 | HTTP server, cluster module, request routing |
| `lib/Config.js` | APP-Q2, APP-Q6 | Singleton configuration, backend selection |
| `lib/data/wrapper.js` | APP-Q2, DATA-Q1, DATA-Q2 | Data access abstraction layer |
| `lib/metadata/wrapper.js` | APP-Q2, DATA-Q2, DATA-Q3, DATA-Q4 | Metadata access abstraction layer |
| `lib/auth/vault.js` | APP-Q3, SEC-Q3, SEC-Q4 | Auth backend (Vault, in-memory, chain) |
| `lib/kms/wrapper.js` | SEC-Q2 | KMS backends (file, KMIP, AWS, memory) |
| `lib/utilities/monitoringHandler.js` | OPS-Q3, OPS-Q8 | Prometheus metrics (business + infra) |
| `lib/utilities/serverAccessLogger.js` | SEC-Q1 | S3 server access logging |
| `lib/api/` | APP-Q2, APP-Q4 | 60+ S3 API handler implementations |
| `lib/routes/routeBackbeat.js` | APP-Q3, APP-Q5, INF-Q4 | Internal backbeat routes (unversioned) |
| `lib/routes/routeMetadata.js` | APP-Q5 | Internal metadata routes (unversioned) |
| `conf/authdata.json` | SEC-Q3, SEC-Q5 | Sample authentication data (dev credentials) |
| `docker-entrypoint.sh` | APP-Q6, SEC-Q5 | Environment variable processing, Docker secrets |
| `monitoring/alerts.yaml` | OPS-Q2, OPS-Q4 | Prometheus alerting rules |
| `monitoring/alerts.test.yaml` | OPS-Q4, OPS-Q8 | Alert rule tests |
| `monitoring/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard definition |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q6 | CI pipeline: lint, test, build, functional tests |
| `.github/workflows/release.yaml` | INF-Q11, OPS-Q5 | Release pipeline: Docker build, push, GitHub release |
| `.github/workflows/codeql.yaml` | SEC-Q7 | CodeQL SAST scanning |
| `.github/workflows/dependency-review.yaml` | SEC-Q7 | Dependency vulnerability review |
| `.github/workflows/alerts.yaml` | OPS-Q8 | Alert configuration validation CI |
| `locationConfig.json` | DATA-Q1 | Location constraint definitions (file, tlp, crr) |
| `constants.js` | APP-Q4 | S3 constants (part limits, sizes, splitter) |
| `schema/server_access_log.schema.json` | SEC-Q1 | Server access log schema definition |
| `Healthchecks.md` | OPS-Q7 | Health check documentation |
| `DESIGN.md` | APP-Q2 | Architecture documentation |
| `README.md` | Quick Agent Wins | Project documentation |
| `docs/` | Quick Agent Wins | Extensive documentation directory (15+ files) |
| `tests/functional/` | OPS-Q6 | Functional test suites (aws-sdk, s3cmd, s3curl, backbeat, kmip, etc.) |
