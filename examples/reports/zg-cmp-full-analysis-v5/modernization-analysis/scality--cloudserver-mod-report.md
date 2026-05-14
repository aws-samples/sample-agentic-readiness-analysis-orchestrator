# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | cloudserver |
| **Date** | 2025-07-16 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, storage, s3 |
| **Context** | Scality open-source S3-compatible object-storage server. |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | 2.08 / 4.0 |

**Archetype Justification**: MongoDB database connections (mongodb ^6.11.0 driver), object data persistence on local filesystem volumes (localData/, localMetadata/), and a full CRUD API surface implementing the S3 protocol (GET/PUT/DELETE/POST/HEAD for objects and buckets on port 8000). Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.89 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.08 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code — all infrastructure is manually provisioned or undefined. | Blocks reproducible deployments, disaster recovery, and environment consistency. Foundation for all other modernization. |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Lambda) defined. Dockerfiles exist but no deployment target is specified. | Prevents elastic scaling, increases operational burden, and blocks containerized deployment to managed orchestration. |
| 3 | INF-Q2: Managed Databases | 1 | MongoDB is self-managed with no IaC defining managed database services. | Manual patching, backup, and scaling for metadata store. Single point of failure risk. |
| 4 | INF-Q5: Network Security | 1 | No VPC, subnets, security groups, or network segmentation defined. Docker Compose uses host networking. | Service exposed without network isolation. No blast-radius containment or defense-in-depth. |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumented (no OpenTelemetry, no X-Ray). Only structured logging with request IDs. | Cannot trace requests across service boundaries to Vault, Backbeat, or metadata services. Debugging production issues is guesswork. |

---

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** APP-Q5 = 3 (S3 protocol provides inherent versioning). The S3 API is well-documented via the AWS S3 API specification, which CloudServer implements.
- **What it enables:** An agent that can discover and invoke S3 API operations (PutObject, GetObject, ListBuckets, etc.) as tools, enabling automated storage management workflows.
- **Additional steps:** Generate an OpenAPI specification from the implemented S3 routes (lib/api/ directory) to enable full tool discovery. The AWS S3 API spec can serve as a reference.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (unified data access layer exists via lib/data/wrapper.js and lib/metadata/wrapper.js).
- **What it enables:** An agent that queries metadata (bucket/object listings, storage utilization) through the centralized wrapper interfaces.
- **Additional steps:** Document the metadata schema and expose query interfaces beyond the S3 protocol (e.g., the existing metadataSearch API could be extended).
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists with GitHub Actions — build, test, release workflows).
- **What it enables:** An agent that triggers deployments, checks build status, monitors test results, and manages releases through the existing GitHub Actions pipeline.
- **Additional steps:** Ensure GitHub Actions API access is configured for the agent. The existing release.yaml workflow supports manual dispatch which enables agent-triggered releases.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — README.md, DESIGN.md, CONTRIBUTING.md, TESTING.md, Healthchecks.md, plus extensive inline code documentation.
- **What it enables:** An agent that indexes existing documentation and code comments to answer developer questions about CloudServer's architecture, API implementation, and testing practices.
- **Additional steps:** Index the documentation files and code comments. Consider using Amazon Bedrock for the RAG pipeline with an S3 bucket as the document store.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 2 (workflow orchestration exists as structured application code). Multi-step operations — multipart uploads (`completeMultipartUpload.js`, `initiateMultipartUpload.js`), object restores (`objectRestore.js`), and replication coordination (`lib/routes/routeBackbeat.js`) — use async waterfall patterns providing a minimal but identifiable orchestration surface.
- **What it enables:** An agent that monitors and manages existing multi-step workflows — tracking multipart upload state, object restore progress, and replication coordination. The agent can detect stalled workflows, trigger retries, and report workflow health.
- **Additional steps:** The current orchestration is embedded in application code with no external workflow service. To fully operationalize this win, extract workflow state into an observable surface (e.g., expose workflow status via an internal API or emit workflow events). A migration to AWS Step Functions would provide a richer execution surface for the agent, but the current code-based orchestration is sufficient for basic monitoring and status queries.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute), APP-Q3=2 (sync-dominant), APP-Q4=2 (no async job handling) |
| 2 | Move to Containers | Not Triggered | — | — | Contextual guard: Dockerfiles and docker-compose.yaml exist — application is already containerized. Pathway requires no container definitions found. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures). MongoDB is already open source. No commercial DB engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (MongoDB self-managed), DATA-Q3=2 (engine version not pinned) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: No streaming, ETL, or analytics artifacts found. No data processing workloads detected. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), OPS-Q5=1 (no deployment strategy), OPS-Q6=4 (strong testing — mitigates some risk) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context: "Scality open-source S3-compatible object-storage server." |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
CloudServer is a monolithic Node.js application (APP-Q2 = 2) — a single deployable unit with identifiable internal modules (lib/api/, lib/auth/, lib/data/, lib/kms/, lib/metadata/) but tightly coupled through a singleton Config object and shared in-process state. All S3 operations, authentication, encryption, metadata management, and data storage run within a single process (with optional Node.js cluster forking for multi-core utilization).

**Compute Model Gaps:**
No managed compute infrastructure is defined (INF-Q1 = 1). Dockerfiles exist but no deployment to ECS, EKS, or Lambda is configured. The application container is built and pushed to GHCR but deployment orchestration is not defined in this repository.

**Communication Pattern Gaps:**
Inter-service communication is primarily synchronous HTTP (APP-Q3 = 2). CloudServer makes synchronous calls to Vault (authentication), Backbeat (replication metrics), and bucketd (metadata service). No async messaging patterns (SQS, SNS, EventBridge) are used for cross-service state propagation. Long-running operations like multipart uploads and object restores are handled synchronously without async job frameworks (APP-Q4 = 2).

**Recommended Decomposition Approach:**
Strangler Fig pattern — incrementally extract services starting with the authentication layer (lib/auth/) and KMS encryption layer (lib/kms/), which have the cleanest interfaces. See the Decomposition Strategy section below for detailed approach options.

**Representative AWS Services:**
- **Amazon EKS** (preferred) for container orchestration of extracted microservices
- **Amazon API Gateway** (preferred) as the S3-compatible entry point with throttling and authentication
- **Amazon EventBridge** (preferred) for event-driven communication between extracted services
- **AWS Step Functions** for orchestrating multi-step operations (multipart uploads, object restores)

**Recommended Patterns:**
- Strangler Fig — extract services incrementally while keeping the monolith running
- Anti-corruption Layer — isolate new services from the monolith's internal data model
- Hexagonal Architecture — structure each extracted service with clear ports and adapters

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
MongoDB is the primary metadata backend, configured as a self-managed replica set (config.json: `replicaSetHosts: "localhost:27018,localhost:27019,localhost:27020"`, `replicaSet: "rs0"`). No IaC defines the MongoDB infrastructure — no `aws_docdb_*`, `aws_rds_*`, or `aws_dynamodb_*` resources exist. Redis is used as a local cache (configured via environment variables in Docker Compose). All database infrastructure appears to be manually provisioned.

**Engine Versions and EOL Status:**
The MongoDB Node.js driver version is ^6.11.0 (package.json), but no MongoDB server engine version is pinned in configuration. The CI pipeline uses a custom MongoDB image (`ci-mongodb`) without a publicly documented version. Engine version lifecycle management is absent (DATA-Q3 = 2).

**Data Access Patterns:**
Data access is centralized through wrapper patterns — `lib/data/wrapper.js` abstracts data storage backends (file, mem, multiple, cdmi) and `lib/metadata/wrapper.js` abstracts metadata backends (mem, file, scality, mongodb). This clean abstraction makes database migration less disruptive because the wrapper interface can be adapted to new backends.

**Recommended Managed Database Targets:**
- **Amazon DocumentDB** (MongoDB-compatible) — drop-in replacement for the MongoDB metadata backend with managed backups, scaling, and Multi-AZ. Recommended as the primary migration path given the existing MongoDB driver and query patterns.
- **Amazon DynamoDB** (preferred) — for the metadata layer if a redesign is undertaken. DynamoDB provides serverless scaling and global tables, but would require refactoring the MongoDB query patterns in the metadata wrapper.
- **Amazon ElastiCache** — for the Redis local cache layer, providing managed caching with automatic failover.

**Migration Tools:**
- AWS Database Migration Service (DMS) for MongoDB → DocumentDB migration
- AWS Schema Conversion Tool (SCT) if restructuring to DynamoDB

**AWS Prescriptive Guidance:**
- [Move to Managed Databases learning plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:**
No infrastructure-as-code exists (INF-Q10 = 1). There are no Terraform files, CloudFormation templates, CDK stacks, Helm charts, or Kustomize configurations. All infrastructure (compute, networking, databases, monitoring) is either manually provisioned or undefined in this repository.

**Current CI/CD State:**
Application CI/CD is partially automated (INF-Q11 = 3). GitHub Actions workflows handle:
- Linting (ESLint, flake8, yamllint)
- Unit tests with coverage (Codecov integration)
- Multi-backend functional tests (file, MongoDB v0/v1, KMIP, SSE migration)
- Docker image builds and pushes to GHCR
- Release workflow (manual dispatch, creates GitHub Release, pushes tagged images)
- Security scanning (CodeQL SAST, dependency review)

However, there is no IaC deployment pipeline because no IaC exists, and the release workflow directly pushes images without a deployment stage.

**Deployment Strategy Gaps:**
No canary or blue/green deployment strategy (OPS-Q5 = 1). The release workflow pushes Docker images directly — there is no staged rollout, traffic shifting, or automated rollback mechanism.

**Testing Strengths:**
Extensive integration/functional testing (OPS-Q6 = 4) — multiple test suites (ft_awssdk, ft_s3cmd, ft_s3curl, ft_node, ft_healthchecks, ft_backbeat, ft_kmip, SSE migration tests) run against multiple backend configurations. This is a significant strength that can be leveraged when introducing IaC and deployment automation.

**Recommended DevOps Toolchain:**
- **Terraform** or **AWS CDK** for IaC (define EKS cluster, DocumentDB, ElastiCache, VPC, security groups)
- **Amazon EKS** (preferred) with Helm charts for Kubernetes deployment manifests
- **AWS CodePipeline** or continue with GitHub Actions for CI/CD with added deployment stages
- **AWS CodeDeploy** for EKS blue/green or canary deployments
- **ArgoCD** for GitOps-based deployment to EKS (if preferred over push-based deployment)

**Implementation Priority:**
1. Define IaC for the existing infrastructure (VPC, compute, databases)
2. Add Helm charts or Kubernetes manifests for the containerized application
3. Implement blue/green or canary deployment through EKS + CodeDeploy
4. Extend CI/CD pipeline with IaC validation (`terraform plan`, `cdk synth`) and deployment stages

**AWS Prescriptive Guidance:**
- [Move to Modern DevOps learning plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Decomposition Strategy

APP-Q2 scored 2 — CloudServer is a monolith with identifiable modules but shared database schemas and tight coupling through the Config singleton. Decomposition is warranted.

### Recommended Approach: Strangler Fig (Parallel Track)

**Why this approach:** CloudServer has identifiable module boundaries (lib/api/, lib/auth/, lib/data/, lib/kms/, lib/metadata/) that can be extracted incrementally. The team can sustain parallel development — the monolith continues handling traffic while services are extracted one at a time. The existing wrapper pattern (lib/data/wrapper.js, lib/metadata/wrapper.js) provides natural seam points for extraction.

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping it running. New features built as services; existing features migrated over time. | ✅ **Applies here** — APP-Q2 = 2, identifiable modules with coupling. Recognizable boundaries (auth, KMS, metadata, data) can be extracted one at a time. | **Medium to High** — 6-18 months depending on module count. | ✅ **Recommended.** Lowest risk, incremental value delivery. |
| **Conditional / Adaptive** | Containerize monolith as-is, then selectively extract high-value services based on business priority. | Alternative if team capacity is limited. Quick containerization win (already done via Dockerfile) followed by selective extraction. | **Low to Medium** — selective extraction over 3-12 months. | ✅ **Recommended if capacity is constrained.** |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch. | Almost never. CloudServer's modules are identifiable (APP-Q2 = 2, not 1), so incremental extraction is feasible. | **Very High** — 12-24+ months. | ⚠️ **Not recommended.** The codebase is maintainable with clear module structure. |

### Extraction Order (Recommended)

1. **Authentication Service** (lib/auth/) — Cleanest interface via Vault client. Extract to a standalone auth service behind Amazon API Gateway authorizers. Low coupling to data layer.
2. **KMS / Encryption Service** (lib/kms/) — Well-encapsulated with the KMS wrapper. Extract to a service backed by AWS KMS (already supported via kmsAWS config).
3. **Metadata Service** (lib/metadata/) — Already abstracted via MetadataWrapper. Migrate to Amazon DocumentDB and expose via a dedicated service.
4. **Data Storage Service** (lib/data/) — Already abstracted via DataWrapper. Can be backed by S3 for data storage with the extracted metadata service.

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's internal data model. | Every extraction — place an ACL between the new service and the monolith. |
| **Saga Pattern** | Manage distributed transactions across services. | When extracting multipart upload coordination and object lifecycle operations. |
| **Event Sourcing** | Capture state changes as events for audit and cross-service sync. | Object lifecycle events (create, delete, restore) — use Amazon EventBridge (preferred). |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters. | Every new service — ensures testability and infrastructure decoupling. |

### Effort Estimation Factors

| Factor | Signal in CloudServer | Effort Impact |
|--------|----------------------|---------------|
| Module boundaries | Clear package structure (lib/api/, lib/auth/, lib/data/, lib/kms/, lib/metadata/) with wrapper abstractions | **Lower effort** — identifiable extraction points |
| Data coupling | Shared Config singleton, in-process state for data/metadata clients | **Higher effort** — Config decoupling required per extraction |
| Stored procedures | None (DATA-Q4 = 4) — all business logic in JavaScript | **Lower effort** — no database logic to extract |
| Communication patterns | Synchronous HTTP to Vault, Backbeat, bucketd (APP-Q3 = 2) | **Moderate effort** — needs async patterns (EventBridge) for decoupling |
| CI/CD maturity | Strong CI pipeline (INF-Q11 = 3) but no deployment automation | **Moderate effort** — pipeline exists but needs deployment stages per service |
| Test coverage | Extensive functional tests (OPS-Q6 = 4) | **Lower effort** — regression testing foundation exists |

**Calibrated Estimate:** 9-15 months for Strangler Fig extraction of auth + KMS + metadata services, assuming a dedicated team of 3-4 engineers.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute resources are defined anywhere in the repository. There are no Terraform, CloudFormation, CDK, or Helm chart files defining `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources. A multi-stage Dockerfile exists (node:22-bookworm-slim base) that builds the application container, and GitHub Actions pushes images to GHCR, but no deployment target (ECS, EKS, EC2, Lambda) is specified. The Docker Compose file (`.github/docker/docker-compose.yaml`) orchestrates CI test environments only — it uses `network_mode: "host"` and is not a production deployment manifest. |
| **Gap** | The application is containerized but has no defined deployment to any managed compute platform. All compute provisioning is presumably manual or handled outside this repository. |
| **Recommendation** | Define EKS (preferred) deployment manifests using Helm charts. Create Terraform or CDK IaC to provision an EKS cluster with Fargate profiles or managed node groups. This is the highest-priority infrastructure gap — all other infrastructure improvements depend on having a defined compute target. |
| **Evidence** | `Dockerfile`, `DockerfileMem`, `.github/docker/docker-compose.yaml`, `.github/workflows/tests.yaml` (build job pushes to GHCR), absence of any IaC files |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | MongoDB is the primary metadata backend, configured as a self-managed replica set in `config.json` (`replicaSetHosts: "localhost:27018,localhost:27019,localhost:27020"`, `replicaSet: "rs0"`, `database: "metadata"`). The MongoDB Node.js driver (`mongodb: ^6.11.0`) is a direct dependency. Redis is used as a local cache (configured via `REDIS_HOST`/`REDIS_PORT` environment variables in Docker Compose). No IaC defines any managed database resources — no `aws_docdb_*`, `aws_rds_*`, `aws_dynamodb_*`, or `aws_elasticache_*` resources exist. |
| **Gap** | All databases are self-managed with no automated failover, backup, or scaling beyond what the MongoDB replica set provides natively. No managed database services are in use. |
| **Recommendation** | Migrate MongoDB metadata backend to Amazon DocumentDB (MongoDB-compatible) for managed backups, automatic failover, and scaling. Migrate Redis cache to Amazon ElastiCache. Consider Amazon DynamoDB (preferred) for the metadata layer if a redesign is undertaken alongside decomposition. |
| **Evidence** | `config.json` (mongodb section), `package.json` (mongodb ^6.11.0), `.github/docker/docker-compose.yaml` (mongo service), `lib/metadata/wrapper.js` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated workflow orchestration service (Step Functions, Temporal, MWAA) is used. Multi-step operations exist in the application — multipart uploads (`completeMultipartUpload.js`, `initiateMultipartUpload.js`, `objectPutPart.js`), object restores (`objectRestore.js`), and replication coordination (via Backbeat integration in `lib/routes/routeBackbeat.js`). These multi-step workflows are implemented as application code with some structural patterns (async waterfall in `lib/kms/wrapper.js`) but no dedicated orchestration. |
| **Gap** | Multi-step operations (multipart uploads, restores, replication) are handled in application code without dedicated orchestration, retry logic, or visual workflow management. For a stateful-crud service with identifiable multi-step operations, this represents a moderate gap. |
| **Recommendation** | Evaluate AWS Step Functions for orchestrating multipart upload coordination, object restore workflows, and replication. Step Functions would provide retry logic, error handling, and visual workflow management for these existing multi-step patterns. |
| **Evidence** | `lib/api/completeMultipartUpload.js`, `lib/api/initiateMultipartUpload.js`, `lib/api/objectRestore.js`, `lib/routes/routeBackbeat.js`, `lib/kms/wrapper.js` (async waterfall pattern) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure is defined. No `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*`, `aws_msk_*`, or `aws_kinesis_*` resources exist. Bucket notification destinations in `config.json` use a `"type": "dummy"` placeholder pointing to `localhost:6000`. The Backbeat integration (`lib/routes/routeBackbeat.js`) provides replication and lifecycle hooks via synchronous HTTP, not messaging. The application makes synchronous HTTP calls to Vault, Backbeat, bucketd, and workflowEngineOperator — all configured with host:port in config.json. For a stateful-crud service, the lack of async messaging for cross-service state changes (object creation, deletion, bucket policy changes) creates tight synchronous coupling. |
| **Gap** | No messaging where state changes cross service boundaries — tight synchronous coupling between CloudServer and its dependent services (Vault, Backbeat, metadata service). Bucket notifications use a dummy backend. |
| **Recommendation** | Adopt Amazon EventBridge (preferred) for event-driven communication of object lifecycle events (create, delete, restore, replicate). Replace the dummy notification destination with EventBridge targets. Use Amazon SQS for decoupling Backbeat replication workflows from the S3 API request path. |
| **Evidence** | `config.json` (bucketNotificationDestinations with dummy type, backbeat/vaultd/bucketd host:port), `lib/routes/routeBackbeat.js`, `package.json` (no SQS/SNS/EventBridge SDK imports) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security infrastructure is defined. No `aws_vpc`, `aws_subnet`, `aws_security_group`, or `aws_vpc_endpoint` resources exist — there is no IaC at all. The Docker Compose CI environment uses `network_mode: "host"` for all services, exposing all ports directly on the host network. The application listens on port 8000 (S3 API), 8002 (metrics), and additional ports for internal data/metadata daemons. Health check access is restricted by IP allowlist (`healthChecks.allowFrom: ["127.0.0.1/8", "::1"]` in config.json), but this is application-level, not network-level security. |
| **Gap** | Services deployed without network isolation — no VPC, no private subnets, no security groups, no network segmentation. No defense-in-depth or blast-radius containment. |
| **Recommendation** | Define a VPC with private subnets for CloudServer and its dependencies (MongoDB, Redis, Vault). Place the S3 API behind Amazon API Gateway (preferred) or an Application Load Balancer in a public subnet. Use security groups with least-privilege rules. Consider VPC endpoints for AWS service access (S3, KMS). |
| **Evidence** | `.github/docker/docker-compose.yaml` (network_mode: host), `config.json` (healthChecks.allowFrom), absence of any IaC |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync is defined. The S3 API is served directly by the Node.js HTTP server on port 8000 (configured in `config.json`). The metrics endpoint is served on port 8002. There is no throttling, no gateway-level authentication, no request validation, and no WAF protection. The application implements its own rate limiting (`lib/api/apiUtils/rateLimit/`) and authentication (AWS Signature V4), but these are application-level controls, not infrastructure-level. |
| **Gap** | Service exposed directly with no gateway or load balancer. No infrastructure-level throttling, DDoS protection, or centralized request routing. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point for the S3 API. API Gateway provides throttling, request validation, WAF integration, and can terminate TLS. For an S3-compatible service, a Network Load Balancer or Application Load Balancer may be more appropriate due to the binary object upload/download patterns — evaluate based on traffic characteristics. |
| **Evidence** | `config.json` (port: 8000, metricsPort: 8002), `lib/server.js` (http.createServer), `lib/api/apiUtils/rateLimit/` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No `aws_autoscaling_*` or `aws_appautoscaling_*` resources are defined. The application supports in-process clustering via Node.js cluster module (`config.clusters` in config.json, cluster fork logic in `lib/server.js`), but this is single-machine multi-core utilization, not infrastructure-level auto-scaling. No Lambda concurrency limits, ECS service auto-scaling, or Kubernetes HPA are configured. |
| **Gap** | All capacity is statically provisioned. No infrastructure-level auto-scaling for compute, database, or cache. |
| **Recommendation** | When deploying to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on the existing Prometheus metrics (s3_cloudserver_http_active_requests, request latency). Consider Karpenter for node-level auto-scaling. For DocumentDB, configure auto-scaling on read replicas. For ElastiCache, configure shard scaling. |
| **Evidence** | `config.json` (clusters: 1), `lib/server.js` (cluster.fork logic), absence of any auto-scaling IaC |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. No `aws_backup_plan`, `backup_retention_period`, or `point_in_time_recovery` resources are defined. MongoDB is configured as a self-managed replica set, which provides some data redundancy but no automated backup/restore procedures. Object data is stored on local filesystem volumes (`VOLUME ["/usr/src/app/localData","/usr/src/app/localMetadata"]` in Dockerfile) with no EBS snapshot, S3 versioning, or backup lifecycle policies. No documented restore procedures. |
| **Gap** | No automated backups for MongoDB metadata or object data. No defined retention periods, no PITR, no documented restore testing. A data loss event could wipe metadata and object state. |
| **Recommendation** | When migrating to Amazon DocumentDB, enable automated backups with a defined retention period and PITR. For object data, consider migrating the data backend from local filesystem to S3 (which provides native versioning and cross-region replication). Create an AWS Backup plan for all data stores. |
| **Evidence** | `Dockerfile` (VOLUME for localData/localMetadata), `config.json` (mongodb replica set), absence of any backup IaC |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. No IaC defines AZ placement for compute or databases. MongoDB is configured with a 3-node replica set (`localhost:27018,localhost:27019,localhost:27020` in config.json), but all on localhost — no AZ distribution. The application supports clustering (`lib/server.js` forks workers) but this is single-machine redundancy. No cross-zone load balancing, no multi-AZ database failover, no AZ-aware deployment. |
| **Gap** | All resources appear to be in a single availability zone (or single machine). An AZ failure would take down the entire workload with no automatic recovery. |
| **Recommendation** | When deploying to EKS (preferred), spread pods across 2+ AZs using topology spread constraints. Migrate MongoDB to Amazon DocumentDB with Multi-AZ enabled. Place the load balancer or API Gateway across multiple AZs with cross-zone load balancing. |
| **Evidence** | `config.json` (mongodb replicaSetHosts all on localhost), `lib/server.js` (cluster module — single machine), absence of any HA IaC |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files exist in the repository. No Terraform (`.tf`, `.tfvars`), CloudFormation (template.yaml), CDK (`cdk.json`), Helm charts (`Chart.yaml`), Kustomize (`kustomization.yaml`), or Ansible playbooks were found. The entire infrastructure — compute, networking, databases, monitoring — is either manually provisioned outside this repository or undefined. The only infrastructure-adjacent artifacts are the Dockerfile (container definition) and docker-compose.yaml (CI test orchestration). |
| **Gap** | 0% IaC coverage. All infrastructure is manually created (ClickOps) or defined outside this repository. No reproducible infrastructure, no environment consistency, no disaster recovery through IaC. |
| **Recommendation** | Adopt Terraform or AWS CDK to define all infrastructure: VPC, EKS cluster, DocumentDB, ElastiCache, API Gateway, security groups, IAM roles. Start with the compute and database infrastructure, then expand to monitoring and operational resources (CloudWatch alarms, Backup plans). This is the foundational gap — all other modernization efforts depend on having reproducible infrastructure. |
| **Evidence** | Repository-wide scan found no .tf, .tfvars, cdk.json, template.yaml, Chart.yaml, or kustomization.yaml files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Application CI/CD is well-automated via GitHub Actions. The `tests.yaml` workflow runs on every push: lint (ESLint, flake8, yamllint), unit tests with Codecov coverage, Docker image builds and pushes to GHCR (production, testcoverage, federation, pykmip, ci-mongodb images), and extensive functional test suites across multiple backend configurations (file, MongoDB v0/v1, KMIP, SSE migration, multiple backend, UTAPI v2, SUR). The `release.yaml` workflow (manual dispatch) builds tagged images, pushes to GHCR, creates a GitHub Release with auto-generated release notes, and pushes monitoring dashboards via ORAS. Security scanning includes CodeQL SAST (`codeql.yaml`) and dependency review (`dependency-review.yaml`). Code review uses Claude AI (`review.yml`). |
| **Gap** | No IaC CI/CD exists because no IaC is defined. The release workflow pushes container images but has no deployment stage — images are pushed to a registry without automated deployment to any environment. No automated rollback capability. |
| **Recommendation** | Extend the CI/CD pipeline with deployment stages once IaC is in place. Add `terraform plan` / `cdk synth` validation. Implement automated deployment to a staging environment with smoke tests before production. Add rollback automation triggered by health check failures. |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/release.yaml`, `.github/workflows/codeql.yaml`, `.github/workflows/dependency-review.yaml`, `.github/workflows/review.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Node.js 22+ (engines `>=22` in package.json) with JavaScript (no TypeScript). Node.js 22 is a current LTS release with first-class AWS SDK support. The AWS SDK v2 (`aws-sdk: ^2.1692.0`) is used — not the latest modular v3 SDK (`@aws-sdk/*`). The application uses a custom HTTP server built on Node.js `http` module and the `arsenal` library (Scality's shared infrastructure library) rather than Express/Fastify. The `werelogs` logging library, `prom-client` for metrics, and `async` for control flow are the primary runtime dependencies. |
| **Gap** | AWS SDK v2 is in maintenance mode — AWS recommends migrating to SDK v3 for modular imports, smaller bundle size, and continued feature development. The custom HTTP server framework limits the ecosystem of middleware and tooling compared to standard frameworks. |
| **Recommendation** | Migrate from `aws-sdk` v2 to `@aws-sdk/*` v3 modular packages. This reduces bundle size and unlocks newer AWS service features. Consider TypeScript adoption for improved type safety as the codebase grows. |
| **Evidence** | `package.json` (engines: >=22, aws-sdk: ^2.1692.0), `index.js`, `lib/server.js` (http.createServer) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit — one package.json, one Dockerfile, one entry point (`index.js` → `lib/server.js`). The application has identifiable internal modules: `lib/api/` (67 S3 API operation handlers), `lib/auth/` (authentication backends), `lib/data/` (data storage wrapper), `lib/kms/` (encryption/key management), `lib/metadata/` (metadata backend wrapper), `lib/routes/` (request routing), `lib/utilities/` (monitoring, logging, healthchecks). These modules have some separation of concerns, but they are tightly coupled through: (1) a singleton `Config` object imported everywhere, (2) shared in-process state (data client, metadata client, vault client instantiated at module load time), (3) cross-module direct imports (api modules directly import auth, data, metadata, kms). |
| **Gap** | Monolith with identifiable modules but shared config singleton, direct cross-module data access, and single shared process state. Module boundaries exist but are not independently deployable. |
| **Recommendation** | Begin Strangler Fig decomposition — the wrapper patterns in `lib/data/wrapper.js` and `lib/metadata/wrapper.js` provide natural extraction seams. See Decomposition Strategy section for detailed approach. |
| **Evidence** | `package.json` (single package), `Dockerfile` (single image), `index.js` → `lib/server.js` (single entry), `lib/api/`, `lib/auth/`, `lib/data/wrapper.js`, `lib/metadata/wrapper.js`, `lib/Config.js` (singleton) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Primarily synchronous communication. CloudServer makes synchronous HTTP calls to: Vault (authentication — `lib/auth/vault.js` via `vaultclient`), Backbeat (replication metrics — `config.json` backbeat host:port), bucketd (metadata — `config.json` bucketd bootstrap), workflowEngineOperator (lifecycle — `config.json`), and external backends (AWS S3, GCP, Azure — via `aws-sdk`, `google-auto-auth`, `@azure/storage-blob`). All inter-service communication is request-response HTTP. Some async patterns exist within the Node.js event loop (callback chains, async waterfall in kms/wrapper.js), but these are in-process, not cross-service async messaging. For a stateful-crud service, the lack of async messaging for state change propagation (e.g., object created → notify replication, object deleted → update quotas) creates coupling. |
| **Gap** | All cross-service communication is synchronous HTTP. No async messaging (SQS, SNS, EventBridge) for state change propagation. State changes that cross service boundaries (notifications, replication triggers, quota updates) are tightly coupled. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for event-driven state change propagation. Object lifecycle events (create, delete, restore) should publish events that downstream services (Backbeat, quotas, notifications) consume asynchronously. Keep synchronous HTTP for read-path operations where it's appropriate. |
| **Evidence** | `lib/auth/vault.js` (vaultclient HTTP), `config.json` (backbeat, bucketd, workflowEngineOperator host:port), `lib/data/wrapper.js`, `package.json` (no SQS/EventBridge dependencies) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some long-running operations exist and are handled synchronously. Object restores (`lib/api/objectRestore.js`) initiate restore operations for cold-tier objects (DMF, Azure Archive). Multipart uploads coordinate across multiple parts (`completeMultipartUpload.js` finalizes multi-part operations). Replication operations coordinated via Backbeat routes. The lifecycle duration metric (`s3_lifecycle_duration_seconds` in monitoringHandler.js, with buckets up to 24 hours) confirms that restore operations can be genuinely long-running. However, there is no explicit async job framework — no Bull/BullMQ, no SQS workers, no background job processing infrastructure. The Node.js cluster module provides multi-core execution but not async job handling. The `server.requestTimeout = 0` setting in `lib/server.js` explicitly disables request timeout to accommodate long uploads. |
| **Gap** | Some background job processing (quota checks, rate limit refill) exists via `startCleanupJob` and `startRefillJob`, but genuine long-running operations (restore, multipart finalization) lack status polling or callback patterns. Disabling request timeout is a workaround, not a solution. |
| **Recommendation** | Implement async job processing for object restores and other operations exceeding 30 seconds. Use AWS Step Functions for restore workflow orchestration with status polling via the existing S3 protocol (RestoreObject returns 202 Accepted). Consider SQS-backed workers for background processing. |
| **Evidence** | `lib/api/objectRestore.js`, `lib/api/completeMultipartUpload.js`, `lib/server.js` (server.requestTimeout = 0), `lib/utilities/monitoringHandler.js` (lifecycleDuration metric with 24h buckets) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CloudServer implements the AWS S3 API protocol, which provides inherent versioning through API compatibility. The S3 API is versioned by AWS specification, and CloudServer maintains compatibility with specific S3 API operations (PutObject, GetObject, ListBucket, etc.) documented in DESIGN.md. Route handling is done through `arsenal.s3routes.routes()` which maps HTTP methods and paths to S3 API operations. The application supports multiple API signature versions (V2 and V4 authentication via `lib/auth/streamingV4/`). No explicit `/v1/`, `/v2/` URL path versioning exists, but the S3 protocol itself serves as the versioning contract. Internal routes (/_/backbeat/, /_/healthcheck/) don't follow a versioning scheme. |
| **Gap** | Internal API routes (Backbeat, healthcheck, metrics) lack versioning. While the S3 protocol provides implicit versioning for external APIs, internal APIs could break consumers without warning. |
| **Recommendation** | Add versioning to internal API routes (e.g., `/_/v1/backbeat/`, `/_/v1/healthcheck/`). Maintain the S3 protocol compatibility as the external API versioning strategy. Document the S3 API version compatibility matrix. |
| **Evidence** | `lib/server.js` (arsenal.s3routes.routes), `DESIGN.md` (API specifications), `lib/auth/streamingV4/`, `lib/routes/routeBackbeat.js` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables and config.json — all are static host:port pairs. `config.json` defines: `vaultd: { host: "localhost", port: 8500 }`, `backbeat: { host: "localhost", port: 8900 }`, `bucketd: { bootstrap: ["localhost:9000"] }`, `metadataClient: { host: "127.0.0.1", port: 9990 }`, `dataClient: { host: "127.0.0.1", port: 9991 }`, `workflowEngineOperator: { host: "localhost", port: 3001 }`. The `docker-entrypoint.sh` script allows overriding many of these via environment variables (`DATA_HOST`, `METADATA_HOST`, `MONGODB_HOSTS`, etc.). No dynamic service discovery (AWS Cloud Map, Consul, Istio) is used. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. Service endpoint changes require config updates and restarts. No service mesh, no health-aware routing, no automatic failover on service endpoint changes. |
| **Recommendation** | When deploying to EKS (preferred), use Kubernetes Service DNS for internal service discovery. Consider AWS Cloud Map for cross-cluster discovery. For the S3 API entry point, use API Gateway (preferred) or an ALB with health-check-aware routing. |
| **Evidence** | `config.json` (vaultd, backbeat, bucketd, metadataClient, dataClient, workflowEngineOperator), `docker-entrypoint.sh` (environment variable overrides) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CloudServer IS an object storage server — it stores unstructured data (objects) on configured backends. The default data backend is local filesystem (`localData/` directory, configured as a Docker volume). Other supported backends include: in-memory (`mem`), Scality RING (`sproxyd`), multiple backends (including AWS S3, GCP Cloud Storage, Azure Blob Storage via `@azure/storage-blob`), and CDMI. Data is stored on local volumes (`VOLUME ["/usr/src/app/localData","/usr/src/app/localMetadata"]` in Dockerfile). The `multiple` backend mode can use S3 as a data target (`externalBackends.aws_s3` in config.json), but the default and primary mode uses local filesystem storage. No S3-based unstructured data storage with parsing pipelines (Textract, Tika) is configured for the application's own data. |
| **Gap** | Default data backend is local filesystem — not managed object storage. While S3 backend is supported as an option, no automated parsing or extraction pipeline exists for stored objects. |
| **Recommendation** | Consider migrating the default data backend from local filesystem to S3 for production deployments, leveraging the existing `multiple` backend support. This provides native S3 durability, versioning, and lifecycle management. For document-heavy workloads, evaluate adding Amazon Textract integration for automated document parsing. |
| **Evidence** | `lib/data/wrapper.js` (file, mem, multiple, cdmi backends), `Dockerfile` (VOLUME for localData), `config.json` (externalBackends.aws_s3), `locationConfig.json` (file type locations) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Data access is centralized through two well-defined wrapper patterns. `lib/data/wrapper.js` provides a unified interface (`DataWrapper`) for data storage operations, abstracting over file, in-memory, multiple backend (S3/GCP/Azure), and CDMI backends. `lib/metadata/wrapper.js` provides a unified interface (`MetadataWrapper` from arsenal) for metadata operations, abstracting over mem, file, scality (bucketd), and MongoDB backends. API operation handlers in `lib/api/` consistently use these wrappers rather than accessing backends directly. However, some auxiliary code paths bypass the wrapper — the monitoring handler (`monitoringHandler.js`) has direct metrics logic, and the Config singleton provides database connection parameters globally. |
| **Gap** | Mostly centralized with some direct access in auxiliary code paths. The Config singleton leaks backend configuration details across the codebase. Some edge cases in API handlers may access backend clients directly. |
| **Recommendation** | Strengthen the wrapper abstraction by ensuring all data access flows through the wrapper interface — this facilitates future backend migration (e.g., MongoDB → DocumentDB/DynamoDB). Consider formalizing the wrapper interfaces as TypeScript interfaces for contract enforcement. |
| **Evidence** | `lib/data/wrapper.js` (DataWrapper with backend switching), `lib/metadata/wrapper.js` (MetadataWrapper), `lib/api/` (uses wrappers consistently), `lib/Config.js` (singleton exposing backend params) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The MongoDB Node.js driver is pinned to `^6.11.0` in package.json, but the MongoDB server engine version is not pinned anywhere in the repository configuration. `config.json` defines MongoDB connection parameters (replica set, database name) but not the engine version. The CI pipeline uses a custom MongoDB image (`ghcr.io/${{ github.repository }}/ci-mongodb:${{ github.sha }}`) built from `.github/docker/mongodb/` — the base image version is not visible in the main repository. No documented version-update procedure exists. MongoDB server versions have defined EOL dates, and without explicit pinning, the deployed version is unknown and may be approaching or past EOL. |
| **Gap** | MongoDB server engine version is not pinned in configuration or IaC. EOL status is unknown. No documented version-update procedure. Driver version is pinned but server version is implicit. |
| **Recommendation** | Pin the MongoDB server engine version explicitly in IaC when migrating to DocumentDB. Document the current MongoDB server version in use. Establish a version lifecycle management procedure covering downtime windows, rollback, and risk acknowledgment. |
| **Evidence** | `package.json` (mongodb: ^6.11.0 driver), `config.json` (mongodb connection params, no engine version), `.github/docker/docker-compose.yaml` (MONGODB_IMAGE variable), `.github/workflows/tests.yaml` (ci-mongodb build) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. MongoDB is used with driver-level queries through the arsenal MetadataWrapper — no stored procedures, no server-side JavaScript functions, no aggregation pipeline triggers. All business logic is implemented in the JavaScript application layer (lib/api/ handlers). No SQL files (`*.sql`) were found in the repository. No ORM is used — data access is through the MongoDB driver with document operations. This is a significant modernization advantage: the entire business logic is in the application layer, making database engine migration a backend-swap rather than a logic-extraction exercise. |
| **Gap** | N/A — no stored procedures or proprietary constructs. |
| **Recommendation** | N/A — this is a strength. Maintain the pattern of keeping all business logic in the application layer when adding new features. |
| **Evidence** | Repository-wide scan found no .sql files, no CREATE PROCEDURE/TRIGGER/FUNCTION patterns, `lib/metadata/wrapper.js` (driver-level operations), `lib/api/` (all business logic in JavaScript) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration exists (no IaC). Application-level logging is implemented: `werelogs` provides structured JSON logging with request IDs (`x-scal-request-uids` header propagation in `lib/server.js`). Server access logging exists (`lib/utilities/serverAccessLogger.js`) with AWS S3-compatible log format including requester, operation, request URI, HTTP status, object key, total time, and turn-around time. The `serverAccessLogs` config (config.json) supports ENABLED/LOG_ONLY/DISABLED modes. However, these are application logs written to a local file (`/logs/server-access.log`), not immutable audit logs with CloudTrail or equivalent. No S3 Object Lock, no CloudWatch log retention, no log integrity validation. |
| **Gap** | No infrastructure-level audit logging (CloudTrail). Application logs exist but are not immutable, not shipped to a centralized log store, and have no integrity validation. |
| **Recommendation** | Enable CloudTrail in the AWS account for API-level audit logging. Ship application access logs to CloudWatch Logs or S3 with Object Lock for immutability. Configure log file validation and retention policies. The existing server access log format is already comprehensive — it needs infrastructure-level immutability. |
| **Evidence** | `lib/utilities/serverAccessLogger.js` (ServerAccessLogger class), `config.json` (serverAccessLogs section), `lib/server.js` (request ID propagation), absence of any CloudTrail IaC |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a comprehensive KMS integration for server-side encryption of S3 objects. `lib/kms/wrapper.js` supports multiple KMS backends: in-memory, file-based, KMIP (via arsenal KMIPClient/KMIPClusterClient), AWS KMS (via arsenal KmsAWSClient), and Scality KMS. The `config.json` includes `kmsAWS` configuration for AWS KMS (`region: "us-east-1"`, `endpoint`). Bucket-level encryption is supported with AES256 and aws:kms algorithms. The application creates cipher bundles per-object with encrypted data keys. `defaultEncryptionKeyPerAccount` is enabled. SSE migration support exists for transitioning between KMS providers. However, no IaC defines KMS keys — the AWS KMS config has placeholder credentials (`ak: "tbd"`, `sk: "tbd"`). The underlying data stores (MongoDB, local filesystem) are not encrypted at the infrastructure level. |
| **Gap** | Application-level encryption for S3 objects is mature (AWS KMS integration, KMIP support, per-account keys, SSE migration). However, no infrastructure-level encryption at rest for the metadata database (MongoDB) or the local filesystem data volumes. KMS key provisioning is not in IaC. |
| **Recommendation** | When migrating to DocumentDB, enable encryption at rest with customer-managed KMS keys. For EBS volumes backing data storage, enable default EBS encryption. Define KMS key resources in IaC with documented rotation policies. The application-layer SSE is a strength — layer infrastructure-level encryption underneath it. |
| **Evidence** | `lib/kms/wrapper.js` (KMS backends: mem, file, kmip, aws, scality), `config.json` (kmsAWS section, defaultEncryptionKeyPerAccount), `lib/kms/common.js`, `.github/workflows/tests.yaml` (KMIP and SSE migration test suites) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong API authentication implementing the AWS S3 protocol authentication model. Multiple auth backends supported: in-memory auth (`conf/authdata.json` with access key/secret key pairs), Vault integration (`lib/auth/vault.js` via `vaultclient`), and chained auth (`multiple` mode combining in-memory + Vault). AWS Signature V4 streaming authentication is implemented (`lib/auth/streamingV4/`). All S3 API requests are authenticated via AWS Signature unless explicitly configured for anonymous access. The health check endpoints (`/live`, `/ready`) are protected by IP allowlist (`healthChecks.allowFrom`). The metrics endpoint (`/metrics`) is on a separate port (8002). |
| **Gap** | Token-based auth (OAuth2/JWT) is not used — the S3 protocol uses AWS Signature V4 (HMAC-based), which is appropriate for S3 compatibility but not standard for REST APIs. Internal endpoints (Backbeat routes) rely on `req.isInternalServiceRequest` flag rather than separate authentication. |
| **Recommendation** | Maintain the AWS Signature V4 authentication for the S3 API surface (required for S3 compatibility). When deploying behind API Gateway (preferred), add gateway-level throttling and WAF protection. For internal service-to-service communication, consider mTLS or IAM-based authentication when deployed on EKS. |
| **Evidence** | `lib/auth/vault.js`, `lib/auth/in_memory/`, `lib/auth/streamingV4/`, `conf/authdata.json`, `lib/server.js` (internalRouteRequest sets isInternalServiceRequest), `config.json` (healthChecks.allowFrom) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application integrates with Scality Vault for centralized identity management (`lib/auth/vault.js` using `vaultclient`). Vault provides account management, access key generation, and authentication services. The `ChainBackend` (`lib/auth/vault.js`, `multiple` auth mode) federates in-memory auth with Vault. However, Vault is Scality's proprietary identity service, not a standard IdP (Cognito, Okta, OIDC). No SSO integration, no OIDC/SAML federation, no Cognito user pool. The in-memory auth backend (`conf/authdata.json`) provides hardcoded test accounts as a fallback. |
| **Gap** | Application has its own auth (in-memory) and can federate with Scality Vault (proprietary), but does not integrate with standard centralized identity providers (Cognito, Okta, OIDC). No SSO support. |
| **Recommendation** | Evaluate integrating with Amazon Cognito for centralized identity. For AWS deployments, IAM authentication via AWS Signature V4 is already supported — consider using IAM roles for service-to-service auth when deployed on EKS. For user-facing access, evaluate OIDC federation through Cognito. |
| **Evidence** | `lib/auth/vault.js` (vaultclient), `lib/auth/in_memory/backend.js`, `conf/authdata.json`, `package.json` (vaultclient dependency) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No Secrets Manager or HashiCorp Vault for secret management. Production credentials are configured via environment variables: `docker-entrypoint.sh` reads from `/run/secrets/s3-credentials` (Docker secrets), and the CI Docker Compose uses `creds.env` file (`.github/docker/creds.env`). The `config.json` has KMS credentials with placeholder values (`ak: "tbd"`, `sk: "tbd"`). `conf/authdata.json` contains hardcoded sample credentials (`accessKey1/verySecretKey1`) — these are sample/test data, not production credentials. CI workflow secrets are stored in GitHub Actions secrets (referenced via `${{ secrets.* }}`). No rotation is configured for any credentials. MongoDB auth can use `MONGODB_AUTH_USERNAME`/`MONGODB_AUTH_PASSWORD` env vars (referenced in docker-entrypoint.sh). |
| **Gap** | No plaintext production credentials in source (the authdata.json keys are clearly sample data), but production credentials live in environment variables and Docker secrets without rotation. No Secrets Manager or Vault integration for runtime secret retrieval. |
| **Recommendation** | Adopt AWS Secrets Manager for all production credentials (MongoDB connection strings, KMS access keys, service account credentials). Configure automated rotation for database credentials and API keys. Reference Secrets Manager secrets from EKS pods using the AWS Secrets and Configuration Provider (ASCP). |
| **Evidence** | `conf/authdata.json` (sample credentials), `config.json` (kmsAWS ak/sk: "tbd"), `docker-entrypoint.sh` (/run/secrets/s3-credentials), `.github/docker/creds.env`, `.github/workflows/tests.yaml` (GitHub Actions secrets) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or managed patching exists. The Dockerfile uses `node:22.14.0-bookworm-slim` as the base image — a standard Debian-based image, not a hardened image (no CIS benchmark, no Bottlerocket, no distroless). The multi-stage build reduces attack surface by using a slim runtime image, but no vulnerability scanning is applied to the container image (no Trivy, Snyk container, ECR scanning). No SSM Patch Manager, no AWS Inspector, no EC2 Image Builder. The production stage installs additional OS packages (`jq`, `tini`, `python3-redis`, `python3-requests`) which expand the attack surface. |
| **Gap** | No vulnerability scanning for container images. Base image is standard Debian-slim, not hardened. No patching automation. Additional OS packages installed in production image increase attack surface. |
| **Recommendation** | Add container image scanning to the CI pipeline (Trivy, Snyk, or Amazon ECR image scanning). Consider using a distroless or Bottlerocket-based image for production. Minimize OS packages in the production stage. When deploying to EKS, enable Amazon Inspector for continuous vulnerability scanning. |
| **Evidence** | `Dockerfile` (FROM node:22.14.0-bookworm-slim, apt-get install in production stage), absence of container scanning in CI workflows |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CodeQL SAST scanning is integrated into CI (`.github/workflows/codeql.yaml`) — runs on push to development/hotfix branches and PRs, analyzing JavaScript, Python, and Ruby. Dependency review on PRs (`.github/workflows/dependency-review.yaml`) uses `actions/dependency-review-action@v4` to flag vulnerable dependencies. Claude AI code review (`review.yml`) provides additional quality checks. However, no container image scanning (Trivy, Snyk, ECR scanning) is configured. No security gate blocks the pipeline on critical findings — CodeQL and dependency review are advisory, not blocking. No DAST (dynamic application security testing) is configured. |
| **Gap** | SAST (CodeQL) and dependency review exist but lack container scanning and have no blocking security gates. Findings are advisory — critical vulnerabilities could reach production. No DAST. |
| **Recommendation** | Add a blocking security gate to the CI pipeline — fail builds on critical CodeQL findings or vulnerable dependency introductions. Add container image scanning (Trivy or Snyk) to the Docker build step. Consider DAST testing against the functional test environments. |
| **Evidence** | `.github/workflows/codeql.yaml`, `.github/workflows/dependency-review.yaml`, `.github/workflows/review.yml`, `.github/workflows/tests.yaml` (no container scanning step) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, no X-Ray SDK, and no tracing libraries exist in the dependencies (package.json). The `werelogs` library provides structured JSON logging with request correlation IDs — the `x-scal-request-uids` header is propagated through request handling (`lib/server.js`), enabling request-level correlation within CloudServer. However, this is request-scoped logging, not distributed tracing — there is no trace context propagation (W3C `traceparent`, `X-Amzn-Trace-Id`) to Vault, Backbeat, bucketd, or external backends. Cross-service debugging requires manual log correlation across multiple services. |
| **Gap** | No distributed tracing — cannot trace requests across service boundaries to Vault, Backbeat, metadata service, or external storage backends. Debugging cross-service failures is manual log correlation. |
| **Recommendation** | Instrument OpenTelemetry for distributed tracing. Add `@opentelemetry/sdk-node` and `@opentelemetry/auto-instrumentations-node` to propagate trace context across all outbound HTTP calls. Export traces to AWS X-Ray or a Prometheus-compatible backend. Prioritize tracing on the S3 API → auth → metadata → data path. |
| **Evidence** | `package.json` (no OpenTelemetry or X-Ray dependencies), `lib/server.js` (x-scal-request-uids header — request ID, not trace context), `lib/utilities/logger.js` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No formal SLO definitions exist, but Prometheus alerting rules in `monitoring/alerts.yaml` define threshold-based alerts that approximate SLOs: listing latency warning at >300ms / critical at >500ms, delete latency warning at >500ms / critical at >1s, system error rate warning at >3% / critical at >5%, endpoint availability (<100% up = warning, <50% = critical), quota metrics availability. These are static thresholds, not formal SLOs with error budgets. No SLO definition files, no error budget tracking, no SLO dashboards. The alerting rules cover key user-facing operations (listing, delete, error rates) but do not define target availability or latency percentiles (p99, p95). |
| **Gap** | Alerting thresholds approximate SLOs but are not formalized. No error budget tracking, no p99/p95 latency targets, no availability targets. |
| **Recommendation** | Formalize SLOs for critical S3 operations: define target p99 latency for GET/PUT/LIST/DELETE operations, target availability (e.g., 99.9%), and target error rate. Implement error budget tracking using the existing Prometheus metrics. Create SLO dashboards in Grafana. |
| **Evidence** | `monitoring/alerts.yaml` (latency and error rate thresholds), absence of SLO definition files |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive Prometheus metrics cover both infrastructure and business outcomes. Business metrics: `s3_cloudserver_buckets_count` (total buckets), `s3_cloudserver_objects_count` (total objects), `s3_cloudserver_ingested_bytes` (cumulative ingested data), `s3_cloudserver_ingested_objects_count` (out-of-band ingested objects), quota metrics (`s3_cloudserver_quota_buckets_count`, `s3_cloudserver_quota_accounts_count`, `s3_cloudserver_quota_unavailable_count`). Infrastructure metrics: `s3_cloudserver_http_requests_total` (by method/action/code), `s3_cloudserver_http_request_duration_seconds` (histogram), `s3_cloudserver_http_active_requests`, `s3_cloudserver_disk_*` (available/free/total bytes). The `promMetrics` function in `monitoringHandler.js` updates business metrics on each S3 operation. A Grafana dashboard exists (`monitoring/dashboard.json`) for visualization. |
| **Gap** | Business metrics are tracked for storage operations but not systematically for all features. Missing: per-bucket metrics, per-account usage metrics, replication lag metrics, encryption operation metrics. |
| **Recommendation** | Add per-bucket and per-account usage metrics for cost attribution and capacity planning. Add replication lag metrics for Backbeat integration monitoring. Consider publishing business metrics to CloudWatch for integration with AWS alerting and dashboards. |
| **Evidence** | `lib/utilities/monitoringHandler.js` (all metric definitions), `monitoring/alerts.yaml` (business metric alerts), `monitoring/dashboard.json` (Grafana dashboard) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Static threshold-based alerting only. `monitoring/alerts.yaml` defines Prometheus alert rules with fixed thresholds: error rate ≥3% warning / ≥5% critical, listing latency ≥300ms warning / ≥500ms critical, delete latency ≥500ms warning / ≥1s critical, endpoint availability thresholds, quota unavailability. Warning and critical severity levels are used. No CloudWatch anomaly detection, no ML-based anomaly detection, no adaptive thresholds. The alerts cover key failure modes (error spikes, latency degradation, endpoint unavailability, quota issues) but cannot detect novel failure patterns or gradual degradation that falls below fixed thresholds. |
| **Gap** | Static thresholds only — no anomaly detection for novel failure patterns or gradual degradation. Alerts cannot adapt to seasonal traffic patterns. |
| **Recommendation** | When migrating metrics to CloudWatch, enable CloudWatch Anomaly Detection on key metrics (request latency, error rate, active requests). Consider composite alarms for multi-signal alerting. Integrate with PagerDuty or OpsGenie for structured incident response. |
| **Evidence** | `monitoring/alerts.yaml` (all alert rules with fixed thresholds) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No canary, blue/green, or rolling deployment strategy exists. The `release.yaml` workflow builds Docker images and pushes them directly to GHCR with the release tag — there is no staged rollout, no traffic shifting, no health-check-gated deployment. The `tests.yaml` workflow pushes images tagged with the commit SHA on every push. No CodeDeploy, no Argo Rollouts, no Helm canary, no Lambda traffic shifting, no feature flags for gradual rollout. Deployment is a direct image push to a registry — the actual deployment to production is not defined in this repository. |
| **Gap** | Direct-to-production deployment with no staged rollout. No mechanism to catch regressions before they affect all users. No automated rollback. |
| **Recommendation** | When deploying to EKS (preferred), implement blue/green or canary deployments using Argo Rollouts or AWS CodeDeploy for EKS. Define health-check-gated deployment stages that automatically roll back on failure. Leverage the existing comprehensive test suite as pre-deployment validation. |
| **Evidence** | `.github/workflows/release.yaml` (direct image push), `.github/workflows/tests.yaml` (commit SHA image push), absence of deployment strategy configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Extensive integration and functional test suites run in CI. The `tests.yaml` workflow runs: `ft_awssdk` (AWS SDK functional tests covering buckets, objects, versioning, external backends), `ft_s3cmd` (S3cmd client tests), `ft_s3curl` (S3curl client tests), `ft_node` (raw Node.js client tests), `ft_healthchecks` (health check tests), `ft_backbeat` (Backbeat integration tests), `ft_kmip` (KMIP encryption tests), SSE migration tests (SSE-KMS migration across KMS providers with before/after migration validation), `ft_mixed_bucket_format_version` (metadata format tests), `ft_util` (utility tests), `ft_search` (metadata search tests), `multiple_backend_test` (multi-backend tests), `test_utapi_v2` (UTAPI v2 tests), `test_sur` (SUR/quota tests). Tests run across multiple backend configurations: file backend, MongoDB v0, MongoDB v1, KMIP, multiple backends with sproxyd. Docker Compose orchestrates the full test environment. Coverage tracked via Codecov with 80% patch target. |
| **Gap** | No significant gaps. Tests cover all critical workflows across multiple backends and client types. Minor gap: no load/performance tests in CI. |
| **Recommendation** | Add performance regression tests to CI to catch latency degradation. Consider contract tests for the Vault and Backbeat integration points. This is a major strength — leverage it when adding deployment automation. |
| **Evidence** | `.github/workflows/tests.yaml` (all test jobs), `package.json` (ft_* and test_* scripts), `codecov.yml` (coverage targets), `.github/docker/docker-compose.yaml` (test orchestration) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated incident response or runbooks. Health check endpoints exist (`/live` for liveness, `/ready` for readiness in `lib/utilities/healthcheckHandler.js`) — the readiness check performs deep health checks against all backend clients (data, metadata, vault, kms). Prometheus alerts define severity levels (warning, critical). The application has self-recovery behavior: `lib/server.js` catches uncaught exceptions and kills the worker (which is auto-restarted by the cluster primary). However, no Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows, no runbook files exist. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation beyond the basic worker restart on crash. No escalation workflows. |
| **Recommendation** | Create structured runbooks for common incidents: MongoDB connection failures, high error rates, latency spikes, disk space exhaustion. When deployed to EKS, leverage Kubernetes self-healing (liveness/readiness probes are already supported). Consider AWS Systems Manager for automated remediation playbooks. |
| **Evidence** | `lib/utilities/healthcheckHandler.js` (/live, /ready endpoints), `lib/server.js` (uncaughtException handler, worker restart), `monitoring/alerts.yaml` (severity levels) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Observability assets exist but without clear ownership attribution. Prometheus metrics are defined in `lib/utilities/monitoringHandler.js`. Grafana dashboard exists (`monitoring/dashboard.json`). Prometheus alerts defined (`monitoring/alerts.yaml`) with warning/critical severity. However: no CODEOWNERS file referencing observability assets, no named alarm owners, no team attribution on metrics or dashboards, no per-service observability ownership. The monitoring artifacts are in a dedicated `monitoring/` directory, suggesting some organizational awareness, but no explicit ownership model. |
| **Gap** | Observability exists but lacks ownership — no CODEOWNERS, no named owners on alarms, no team attribution. Monitoring is present but organizational accountability is undefined. |
| **Recommendation** | Create a CODEOWNERS file with explicit ownership for the `monitoring/` directory. Add team/owner labels to Prometheus alerts. Define per-service SLO ownership when decomposing into microservices. |
| **Evidence** | `monitoring/alerts.yaml`, `monitoring/dashboard.json`, `lib/utilities/monitoringHandler.js`, absence of CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging governance exists. No IaC resources exist to tag — there are no Terraform `default_tags`, no CloudFormation tags, no Kubernetes labels for cost allocation. The Docker images pushed by GitHub Actions have some labels (`git.repository`, `git.commit-sha`) but these are image metadata, not AWS resource tags. No `required-tags` AWS Config rules, no Tag Policies, no cost allocation tag configuration. |
| **Gap** | No AWS resource tags for cost allocation, ownership, or environment identification. No tagging standard or enforcement. |
| **Recommendation** | When creating IaC, define a tagging standard with required tags: `Environment`, `Service`, `Team`, `CostCenter`. Use Terraform `default_tags` provider configuration or CDK aspects for tag enforcement. Enable AWS Config `required-tags` rules. Activate cost allocation tags in AWS Billing. |
| **Evidence** | Absence of any IaC files, `.github/workflows/tests.yaml` (Docker image labels — git.repository, git.commit-sha) |

## Learning Materials

The following resources are mapped to the 3 triggered pathways:

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | INF-Q1, INF-Q2, INF-Q4, INF-Q11, APP-Q1, APP-Q2, APP-Q3, DATA-Q3, OPS-Q1, OPS-Q6 | Node.js dependencies, engine version (>=22), AWS SDK v2, MongoDB driver ^6.11.0, prom-client, test scripts |
| `config.json` | INF-Q1, INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q9, APP-Q3, APP-Q6, DATA-Q3, SEC-Q2, SEC-Q3, SEC-Q5 | MongoDB config (replica set), port config, service endpoints (vaultd, backbeat, bucketd), KMS config, health check allowFrom, bucket notifications |
| `Dockerfile` | INF-Q1, INF-Q7, INF-Q8, SEC-Q6 | Multi-stage build (node:22-bookworm-slim), VOLUME for localData/localMetadata, EXPOSE 8000/8002, production packages |
| `DockerfileMem` | INF-Q1 | Legacy mem-backend Dockerfile |
| `index.js` | APP-Q1, APP-Q2 | Entry point → lib/server.js |
| `lib/server.js` | INF-Q1, INF-Q6, INF-Q7, INF-Q9, APP-Q2, APP-Q4, OPS-Q1, OPS-Q7 | HTTP server, cluster module, request routing, requestTimeout=0, uncaughtException handling, metrics server |
| `lib/Config.js` | APP-Q2, DATA-Q2 | Singleton config object, backend configuration |
| `lib/api/` (directory) | APP-Q2, APP-Q4, DATA-Q2, DATA-Q4 | 67 S3 API operation handlers |
| `lib/api/completeMultipartUpload.js` | INF-Q3, APP-Q4 | Multi-step multipart upload finalization |
| `lib/api/initiateMultipartUpload.js` | INF-Q3 | Multipart upload initiation |
| `lib/api/objectRestore.js` | INF-Q3, APP-Q4 | Object restore from cold tier |
| `lib/auth/vault.js` | APP-Q3, SEC-Q3, SEC-Q4 | Vault authentication client, ChainBackend |
| `lib/auth/in_memory/` | SEC-Q3, SEC-Q4 | In-memory auth backend |
| `lib/auth/streamingV4/` | SEC-Q3, APP-Q5 | AWS Signature V4 streaming auth |
| `lib/data/wrapper.js` | INF-Q2, APP-Q2, APP-Q3, DATA-Q1, DATA-Q2 | Data access wrapper (file, mem, multiple, cdmi backends) |
| `lib/metadata/wrapper.js` | INF-Q2, APP-Q2, DATA-Q2, DATA-Q3, DATA-Q4 | Metadata access wrapper (mem, file, scality, mongodb backends) |
| `lib/kms/wrapper.js` | INF-Q3, SEC-Q2 | KMS integration (mem, file, kmip, aws, scality backends) |
| `lib/routes/routeBackbeat.js` | INF-Q3, INF-Q4, APP-Q3 | Backbeat replication and lifecycle routes |
| `lib/utilities/monitoringHandler.js` | OPS-Q3, OPS-Q4, OPS-Q8 | Prometheus metrics definitions (HTTP, business, quota, lifecycle) |
| `lib/utilities/healthcheckHandler.js` | OPS-Q7 | /live and /ready health check endpoints |
| `lib/utilities/serverAccessLogger.js` | SEC-Q1 | Server access log implementation (S3-compatible format) |
| `lib/api/apiUtils/rateLimit/` | INF-Q6 | Application-level rate limiting |
| `conf/authdata.json` | SEC-Q3, SEC-Q4, SEC-Q5 | Sample auth data (test accounts with accessKey1/verySecretKey1) |
| `monitoring/alerts.yaml` | OPS-Q2, OPS-Q4, OPS-Q7, OPS-Q8 | Prometheus alert rules (latency, error rate, availability, quotas) |
| `monitoring/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard definition |
| `.github/workflows/tests.yaml` | INF-Q1, INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | CI pipeline (lint, unit tests, functional tests, Docker builds) |
| `.github/workflows/release.yaml` | INF-Q11, OPS-Q5 | Release workflow (image push, GitHub Release) |
| `.github/workflows/codeql.yaml` | INF-Q11, SEC-Q7 | CodeQL SAST scanning |
| `.github/workflows/dependency-review.yaml` | INF-Q11, SEC-Q7 | Dependency vulnerability review |
| `.github/workflows/review.yml` | INF-Q11 | Claude AI code review |
| `.github/docker/docker-compose.yaml` | INF-Q1, INF-Q2, INF-Q5, DATA-Q3, OPS-Q6 | CI test orchestration (redis, mongo, sproxyd, pykmip) |
| `docker-entrypoint.sh` | APP-Q6, SEC-Q5 | Environment variable configuration, Docker secrets |
| `DESIGN.md` | APP-Q5 | Architecture and API specification documentation |
| `locationConfig.json` | DATA-Q1 | Storage location configuration (file type, cold tier, CRR) |
| `codecov.yml` | OPS-Q6 | Coverage configuration (80% patch target) |
| `README.md` | Quick Agent Wins | Project documentation |
| `TESTING.md` | Quick Agent Wins | Test plan documentation |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
