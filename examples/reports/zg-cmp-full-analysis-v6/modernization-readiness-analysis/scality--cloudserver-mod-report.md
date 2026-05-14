# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | scality--cloudserver |
| **Date** | 2025-01-08 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, storage, s3 |
| **Context** | Scality open-source S3-compatible object-storage server. |
| **Overall Score** | 2.22 / 4.0 |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true |

**Archetype Justification**: The application owns persistent state via MongoDB (metadata) and file/object storage backends, exposes CRUD operations on S3 objects and buckets, and manages object lifecycle. Classified as stateful-crud.

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.73 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.22 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (2+2+2+2+1+1+1+1+2+2+3) / 11 = 19/11 = **1.73**
- APP: (3+2+3+2+2+3) / 6 = 15/6 = **2.50**
- DATA: (2+3+3+3) / 4 = 11/4 = **2.75**
- SEC: (1+2+3+2+2+2+3) / 7 = 15/7 = **2.14**
- OPS: (2+1+2+2+2+3+1+3+2) / 9 = 18/9 = **2.00**
- Overall: (1.73 + 2.50 + 2.75 + 2.14 + 2.00) / 5 = 11.12 / 5 = **2.22**

**Classification Tier: 🟠 Remediation Required**

This repo has 3 High findings, 23 Medium findings, 11 Low findings. The classification rule matched is: "2-11 High → Remediation Required." MOD classification treats "1 High" as Pilot-Ready (a single modernization gap rather than a deployment blocker), whereas ARA's "1 High" is an agent-deployment gate — reflecting the different concerns each analysis evaluates.

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined in any IaC | Services lack network isolation; no blast radius containment |
| 2 | INF-Q6: API Entry Point | 1 | No API Gateway, ALB, or CloudFront in front of services | No throttling, auth offload, or request validation at the edge |
| 3 | INF-Q7: Auto-Scaling | 1 | No auto-scaling configuration found anywhere | Cannot respond to traffic spikes; over-provisioning or outages likely |
| 4 | INF-Q8: Backup and Recovery | 1 | No backup configuration for MongoDB or any data store | Data loss risk with no recovery mechanism |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging infrastructure | No forensic capability; compliance gaps |

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3) — GitHub Actions workflows with build, test, and deploy stages are present.
- **What it enables:** An agent that triggers deployments, checks build status across the 7+ CI workflow jobs, and manages releases via the existing `release.yaml` workflow.
- **Additional steps:** Expose workflow dispatch APIs and add structured build status reporting.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — README.md, DESIGN.md, CONTRIBUTING.md, TESTING.md, CLAUDE.md, Healthchecks.md, plus full Sphinx docs directory with architecture, getting started, Docker, and integration guides.
- **What it enables:** A RAG-based knowledge agent that indexes existing documentation to answer developer questions about the S3 implementation, backend configuration, and operational procedures.
- **Additional steps:** Index the docs/ directory and top-level markdown files into a vector store; configure Bedrock for retrieval.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and metrics in place (OPS-Q1 = 2) — Prometheus metrics via prom-client, Grafana dashboards, and structured logging via werelogs.
- **What it enables:** An agent that queries Prometheus metrics, correlates with structured logs, and suggests root causes for S3 endpoint degradation or latency spikes.
- **Additional steps:** Add trace ID propagation (currently missing cross-service); configure Bedrock for log analysis.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=2 (limited managed compute), APP-Q3=2 (sync-dominant) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=2 but Dockerfiles and container definitions already exist; contextual guard prevents trigger |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=3 (minimal stored procedures); no commercial DB engines detected — MongoDB is already open source |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=2 (MongoDB self-managed in Docker), DATA-Q3=3 |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads or streaming infrastructure detected; contextual guard prevents trigger |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=2 (partial IaC), OPS-Q5=2 (rolling deploys only), OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:**
- The application is a single monolithic Node.js server (index.js) with 5 entry points but deployed as a single unit. All S3 API operations, authentication, KMS, metadata, and data backends are in one deployable artifact.
- Compute is container-based (Docker) but without managed orchestration (no EKS/ECS/Fargate definitions in IaC).
- Communication between internal components (metadata server, data server) is synchronous HTTP on localhost.

**Recommended Decomposition Approach:**
- Use **Strangler Fig** pattern to incrementally extract services: metadata service, data service, KMS service, and management agent as independently deployable containers on EKS.
- Leverage existing separation of concerns in `lib/` (api, auth, data, metadata, kms, management) as natural service boundaries.

**Representative AWS Services:** EKS (preferred per steering context), API Gateway, EventBridge, Step Functions, Aurora

**Recommended Patterns:**
- Anti-corruption Layer between extracted services and remaining monolith
- Event Sourcing for object lifecycle events (already has recordLog infrastructure)
- Hexagonal Architecture for each extracted service

**Links:** [AWS Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- MongoDB is self-managed — configured as a replica set in Docker containers for CI and referenced in config.json with direct host:port connections.
- No IaC provisions managed database infrastructure (no `aws_docdb_*`, `aws_rds_*`, `aws_dynamodb_*`).
- Redis is self-managed via Docker container (redis:alpine).

**Recommended Migration Targets:**
- **Amazon DocumentDB** (MongoDB-compatible) for metadata storage — direct driver compatibility with the existing mongodb ^6.11.0 driver
- **Amazon ElastiCache for Redis** for the caching layer
- Consider **Amazon DynamoDB** for metadata if schema allows (preferred per steering context)

**Representative AWS Services:** DocumentDB, ElastiCache, DynamoDB

**Migration Approach:**
1. Create DocumentDB cluster with Multi-AZ
2. Use AWS DMS for initial data migration
3. Update connection strings via environment variables (already externalized: `MONGODB_HOSTS`, `MONGODB_RS`)
4. Validate with existing functional test suite

**Links:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- CI/CD exists via GitHub Actions with comprehensive test coverage (lint, unit, functional, multi-backend).
- No IaC for production infrastructure — only monitoring configs (Prometheus alerts, Grafana dashboards).
- Deployment strategy is basic — Docker image push to GHCR with no canary/blue-green.
- No integration tests that run against deployed infrastructure (tests run against Docker compose locally).

**Recommended Actions:**
1. Define production infrastructure in IaC (Terraform or CDK) — EKS cluster, DocumentDB, ElastiCache, networking
2. Add deployment stages to CI/CD (staging → canary → production)
3. Implement blue/green deployments via EKS rolling updates or Argo Rollouts
4. Add integration test stage against staging environment

**Representative AWS Services:** CDK, CodePipeline, CodeBuild, CodeDeploy, EKS, CloudWatch

**Links:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

---

## Decomposition Strategy

**Condition:** APP-Q2 = 2 (monolith with identifiable modules but shared process)

### Recommended Approach: Strangler Fig (Parallel Track)

The CloudServer monolith has well-defined internal boundaries (`lib/api`, `lib/auth`, `lib/data`, `lib/metadata`, `lib/kms`, `lib/management`) that map to natural service extraction points. The existing multi-process deployment mode (mdserver.js, dataserver.js, pfsserver.js) already separates concerns at the process level, making extraction lower-risk.

| Approach | Suitability | Rationale |
|----------|-------------|-----------|
| **Strangler Fig** | ✅ Recommended | Identifiable modules; existing process separation (metadata server, data server) provides natural extraction boundaries |
| **Conditional / Adaptive** | Acceptable | Already containerized; could selectively extract high-traffic services (metadata, KMS) |
| **Big-Bang Rewrite** | ⚠️ Not Recommended | System is functional; monolith has internal structure; too much risk for a working S3 implementation |

### Pattern Recommendations

| Pattern | Application |
|---------|------------|
| **Anti-corruption Layer** | Between extracted metadata service and S3 API service to isolate data models |
| **Saga Pattern** | For multi-part upload operations that span metadata + data services |
| **Event Sourcing** | Leverage existing `recordLog` infrastructure for object state changes |
| **Hexagonal Architecture** | Structure each extracted service with clear ports/adapters |

### Extraction Priority

1. **Metadata Service** (already has mdserver.js) — High value, clear boundary
2. **Data Service** (already has dataserver.js) — High value, clear boundary
3. **KMS Service** (lib/kms/) — Independent concern, clear interface
4. **Management Agent** (managementAgent.js) — Already a separate process
5. **S3 API Gateway** (lib/api/) — Becomes the thin routing layer

### Effort Factors

| Factor | Signal | Analysis |
|--------|--------|------------|
| Module boundaries | Clear (lib/ subdirectories, separate entry points) | Low effort |
| Data coupling | Moderate (shared MongoDB, some cross-module references) | Medium effort |
| Stored procedures | None (all logic in application layer) | Low effort |
| Communication patterns | Sync HTTP between internal processes | Medium effort |
| CI/CD maturity | Good pipeline exists (GH Actions) | Low effort for extension |
| Test coverage | Strong functional test suite | Low regression risk |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is containerized (Dockerfile using node:22-bookworm-slim, multi-stage build) and deployed via Docker to GHCR. However, there is no managed container orchestration defined — no EKS, ECS, Fargate, or Lambda resources in any IaC. The docker-compose.yaml is for CI testing only. No production orchestration is defined. |
| **Gap** | Containerized but no managed orchestration layer. Production deployment model is undefined in code — relies on external tooling (likely Kubernetes deployed by the Zenko platform, but not defined in this repo). |
| **Recommendation** | Define EKS (preferred) cluster infrastructure in Terraform/CDK. Create Helm charts or Kubernetes manifests for production deployment with proper resource limits, health checks, and scaling. |
| **Evidence** | `Dockerfile`, `.github/docker/docker-compose.yaml`, absence of any `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` Terraform resources, absence of Helm charts or Kubernetes manifests |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MongoDB is configured as a self-managed replica set (hosts: `localhost:27018,localhost:27019,localhost:27020` in config.json, deployed as Docker container in CI compose). Redis is self-managed (redis:alpine container). No IaC provisions any managed database service. Connection is configured via environment variables (`MONGODB_HOSTS`, `MONGODB_RS`, `REDIS_HOST`). |
| **Gap** | Both MongoDB and Redis are self-managed with no managed service equivalents (DocumentDB, ElastiCache) provisioned in IaC. Production database management is entirely outside this repository. |
| **Recommendation** | Migrate to Amazon DocumentDB (MongoDB-compatible) for metadata and Amazon ElastiCache for Redis. Define these in IaC with Multi-AZ, automated backups, and encryption. Consider DynamoDB for metadata if schema allows (preferred per steering). |
| **Evidence** | `config.json` (mongodb section), `.github/docker/docker-compose.yaml` (redis:alpine, mongo services), absence of `aws_docdb_*`, `aws_dynamodb_*`, `aws_elasticache_*` in IaC |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has multi-step workflows: multipart upload (initiate → upload parts → complete), object lifecycle transitions, replication workflows (Backbeat integration), and SSE/KMS key migration. These are all implemented as hardcoded application logic in `lib/api/` and `lib/routes/routeBackbeat.js` with basic state machines in code. No dedicated workflow orchestration service (Step Functions, Temporal) is used. |
| **Gap** | Multi-step operations (multipart upload coordination, replication workflows, lifecycle transitions) are hardcoded state machines without dedicated orchestration. Error handling and retry logic are embedded in application code. |
| **Recommendation** | Adopt AWS Step Functions for orchestrating multi-step operations like replication workflows and lifecycle transitions. Multipart upload coordination could remain in-process due to latency sensitivity, but background workflows (lifecycle, replication) benefit from managed orchestration with visual debugging and built-in retries. |
| **Evidence** | `lib/api/objectPutPart.js`, `lib/api/completeMultipartUpload.js`, `lib/routes/routeBackbeat.js`, `tests/functional/sse-kms-migration/migration.js`, absence of `aws_sfn_*` or Temporal imports |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has some event-driven patterns: bucket notifications (`bucketNotificationDestinations` in config.json), Backbeat integration for replication (references `backbeat` service at localhost:8900), and a `recordLog` system for state changes. However, no managed messaging infrastructure (SQS, SNS, EventBridge, MSK) is defined in IaC. Communication between internal services and Backbeat is synchronous HTTP. Bucket notifications reference a "dummy" type destination. |
| **Gap** | Cross-service state changes (replication triggers, lifecycle events, bucket notifications) use synchronous HTTP or dummy destinations rather than managed messaging. The `recordLog` infrastructure exists but is not connected to managed streaming. |
| **Recommendation** | Adopt Amazon EventBridge for bucket event notifications and lifecycle triggers. Use SQS for decoupling replication and lifecycle workflows from the S3 API path. This aligns with the existing event patterns without requiring architectural redesign. |
| **Evidence** | `config.json` (bucketNotificationDestinations with type "dummy", backbeat config), `lib/routes/routeBackbeat.js`, absence of `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*` in IaC |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists in the repository. All services bind to localhost or 0.0.0.0 in config and Docker compose. No network policies, service mesh, or PrivateLink configurations are defined. The docker-compose uses `network_mode: "host"` for all services. |
| **Gap** | Complete absence of network security infrastructure. No private subnets, no security groups, no network segmentation between tiers (API, metadata, data). |
| **Recommendation** | Define VPC with private subnets for database and application tiers. Place S3 API endpoints in private subnets behind an ALB or API Gateway. Use security groups with least-privilege rules. Consider VPC endpoints for AWS service access. |
| **Evidence** | `.github/docker/docker-compose.yaml` (network_mode: host), `config.json` (all binds to localhost/0.0.0.0), absence of any `aws_vpc`, `aws_subnet`, `aws_security_group` resources |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The S3 API is exposed directly on port 8000 with no gateway, load balancer, or CDN in front. No API Gateway, ALB, CloudFront, or any managed entry point is defined. The application handles all request routing, authentication, and rate limiting internally (lib/api/apiUtils/rateLimit/). Health checks are exposed at the application level only. |
| **Gap** | No managed entry point provides throttling, DDoS protection, request validation, or traffic management. All security and traffic control is application-level. |
| **Recommendation** | Deploy an Application Load Balancer (ALB) in front of the service with health checks. For external-facing deployments, add CloudFront for DDoS protection and caching. Consider API Gateway if per-endpoint throttling and request validation are needed. |
| **Evidence** | `config.json` (port: 8000, direct exposure), `lib/server.js` (direct HTTP server), absence of `aws_lb_*`, `aws_api_gateway_*`, `aws_cloudfront_*` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The `clusters` config in config.json is set to 1. No ASG, ECS service scaling, HPA, or Lambda concurrency configuration is defined. The application supports cluster mode (Node.js cluster) but scaling decisions are manual. |
| **Gap** | No dynamic scaling — all capacity is statically provisioned. Cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | When deploying to EKS, configure Horizontal Pod Autoscaler (HPA) based on request rate (from Prometheus metrics already exposed on port 8002). Configure cluster autoscaler for node-level scaling. |
| **Evidence** | `config.json` (clusters: 1), absence of `aws_autoscaling_*`, `aws_appautoscaling_*`, absence of HPA or VPA manifests |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists for MongoDB or any data store. No `aws_backup_plan`, no backup_retention_period, no point-in-time recovery configuration, no S3 versioning for data buckets. The application stores data in volumes (`localData/`, `localMetadata/`) with no backup strategy defined. |
| **Gap** | No automated backup or recovery mechanism for metadata (MongoDB) or object data. A data loss event would be unrecoverable from the configuration defined in this repository. |
| **Recommendation** | When migrating to DocumentDB, enable automated backups with 7+ day retention and point-in-time recovery. For object data backends, implement S3 versioning and cross-region replication. Define AWS Backup plans in IaC. |
| **Evidence** | Absence of `aws_backup_plan`, `backup_retention_period`, `point_in_time_recovery` in any configuration; `config.json` (no backup section); Docker volumes without backup strategy |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MongoDB is configured as a replica set (`rs0` with 3 members: ports 27018, 27019, 27020 in config.json), which provides data-layer redundancy. However, no multi-AZ deployment configuration exists in IaC. No load balancer distributes traffic across multiple application instances. The application supports cluster mode but no cross-AZ or cross-node HA is defined. |
| **Gap** | Database has replica set (single-host in config, but pattern supports multi-AZ). Application layer has no defined multi-AZ or multi-instance HA configuration in IaC. |
| **Recommendation** | Deploy application across 2+ AZs in EKS with at least 2 replicas. Configure DocumentDB with Multi-AZ. Use ALB with cross-zone load balancing. |
| **Evidence** | `config.json` (mongodb replicaSetHosts on localhost), absence of multi-AZ subnet configurations, absence of load balancer resources |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | IaC coverage is limited to monitoring/observability: Prometheus alerting rules (`monitoring/alerts.yaml`), Grafana dashboard (`monitoring/dashboard.json`), and CI infrastructure (GitHub Actions workflows, Docker compose for testing). No production infrastructure is defined in IaC — no compute, networking, databases, or security resources. The Dockerfile defines the container build but not deployment infrastructure. |
| **Gap** | Production infrastructure (compute orchestration, databases, networking, security groups, load balancers, auto-scaling) is not defined in code. Only monitoring and CI environments have IaC. |
| **Recommendation** | Create Terraform or CDK modules for: VPC/networking, EKS cluster, DocumentDB, ElastiCache, ALB, IAM roles, CloudWatch alarms. Start with a baseline module covering compute + database + networking. |
| **Evidence** | `monitoring/alerts.yaml`, `monitoring/dashboard.json`, `.github/workflows/tests.yaml`, absence of `.tf` files, CloudFormation templates, or CDK stacks for production infrastructure |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI pipeline via GitHub Actions: lint (JS, Python, YAML, Markdown), unit tests with coverage, Docker image builds, functional tests across multiple configurations (MongoDB v0, v1, KMIP, S3C, multi-backend). Release workflow builds and pushes production Docker images. Coverage reports to Codecov with 80% patch target. However, deployment to production environments is not automated in this repo — release workflow only pushes images to GHCR. No deployment stages (staging, canary, production) exist. |
| **Gap** | Build and test are fully automated. Deployment is limited to image push — no automated deployment to staging or production environments. No IaC deployment pipeline. |
| **Recommendation** | Extend CI/CD to include deployment stages: add staging environment deployment after image build, run integration tests against staging, then promote to production with canary or blue/green strategy. Add IaC deployment pipeline (terraform plan/apply or CDK deploy). |
| **Evidence** | `.github/workflows/tests.yaml` (lint, unit, build, functional test jobs), `.github/workflows/release.yaml` (image push only), `.github/workflows/codeql.yaml`, `.github/workflows/dependency-review.yaml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary language is JavaScript (Node.js >= 22, CommonJS modules) — a modern runtime version with first-class AWS SDK support. Uses `aws-sdk` ^2.1692.0 (AWS SDK v2 for JavaScript). The language version is current (Node.js 22), but the AWS SDK is v2 (maintenance mode) rather than v3 (modular, current). Framework/SDK lag: modern runtime with legacy SDK. |
| **Gap** | AWS SDK v2 is in maintenance mode. The modular AWS SDK v3 provides better tree-shaking, middleware support, and TypeScript-first design. No TypeScript adoption despite Node.js 22 supporting it natively. |
| **Recommendation** | Migrate from `aws-sdk` v2 to `@aws-sdk/*` v3 modular packages for reduced bundle size and modern middleware. Consider gradual TypeScript adoption for new modules. |
| **Evidence** | `package.json` (engines: node >= 22, aws-sdk: ^2.1692.0), `Dockerfile` (node:22.14.0-bookworm-slim) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a monolith with identifiable modules. All S3 API operations, auth, KMS, metadata, and data backends are in a single deployable container. The codebase has clear module boundaries (lib/api, lib/auth, lib/data, lib/metadata, lib/kms, lib/management) and separate entry points (index.js, mdserver.js, dataserver.js, pfsserver.js, managementAgent.js). However, all modules share the same process memory, configuration (Config.js), and deployment artifact. Cross-module dependencies exist (e.g., API handlers directly call metadata and data modules). |
| **Gap** | Single deployable unit prevents independent scaling of components (metadata vs data vs API). Shared configuration object and in-process dependencies create coupling. Cannot deploy or scale metadata independently from the API layer. |
| **Recommendation** | Extract metadata service and data service as independently deployable containers on EKS, leveraging existing process separation (mdserver.js, dataserver.js). Define inter-service communication contracts (already partially defined via HTTP on internal ports 9990, 9991). |
| **Evidence** | `index.js`, `mdserver.js`, `dataserver.js`, `pfsserver.js` (multiple entry points but single container), `lib/Config.js` (95KB shared config), `Dockerfile` (single production target) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Inter-component communication is primarily synchronous HTTP (S3 API → metadata server on :9990, S3 API → data server on :9991). The application has some async patterns: bucket notifications (configured but with "dummy" type), Backbeat integration for async replication, recordLog for state change streaming, and WebSocket-based management agent. However, cross-service state propagation for replication and lifecycle relies on synchronous HTTP calls to Backbeat. |
| **Gap** | State changes that trigger replication or lifecycle operations flow synchronously. Bucket notifications use a dummy type rather than actual async delivery. The recordLog is a foundation for async but not connected to managed messaging. |
| **Recommendation** | Convert bucket notification delivery to EventBridge for genuine async event distribution. Move replication trigger flow to SQS for decoupling. The existing recordLog infrastructure provides a natural insertion point for event streaming. |
| **Evidence** | `config.json` (bucketNotificationDestinations type: "dummy", backbeat host:port), `lib/routes/routeBackbeat.js` (HTTP-based integration), `lib/management/` (WebSocket async for management) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has long-running operations: multipart uploads (can span hours/days between initiate and complete), SSE/KMS key migration (tested with 300s timeout), lifecycle transitions, and cross-region replication. Multipart upload is inherently async (initiate returns uploadId, parts uploaded separately, complete finalizes) — this is correct S3 protocol behavior. However, the SSE/KMS migration and lifecycle operations appear to be synchronous within their execution context. Object copy operations for large objects can exceed 30 seconds. |
| **Gap** | Object copy and lifecycle transitions for large objects may exceed 30 seconds synchronously. SSE/KMS migration has no async job tracking infrastructure. The multipart upload pattern is correct but other long-running ops lack status polling. |
| **Recommendation** | Implement async job processing with status polling for: large object copy operations, SSE/KMS migration, and lifecycle transitions. Use Step Functions or SQS-based worker pattern for long-running background operations. |
| **Evidence** | `lib/api/objectCopy.js`, `tests/functional/sse-kms-migration/` (300s timeout), `lib/api/completeMultipartUpload.js` (async by S3 design) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements the AWS S3 API protocol, which has implicit versioning through API version headers and feature-specific parameters. There is no explicit versioning strategy in URL paths or custom headers for the CloudServer-specific extensions (Backbeat routes, management API, health checks). The Backbeat routes are at `/default/backbeat/` with no version prefix. Management API uses WebSocket without versioning. |
| **Gap** | CloudServer-specific API extensions (Backbeat, management, health) have no versioning strategy. Breaking changes to these internal APIs would affect all consumers simultaneously. |
| **Recommendation** | Add version prefixes to internal API routes (e.g., `/v1/backbeat/`, `/v1/management/`). Document API compatibility guarantees for internal routes. S3 protocol routes inherit AWS S3 versioning which is appropriate. |
| **Evidence** | `lib/routes/routeBackbeat.js` (no version prefix), `lib/utilities/healthcheckHandler.js` (no version), `lib/management/` (WebSocket, no version negotiation) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Service endpoints are configured via environment variables (`MONGODB_HOSTS`, `REDIS_HOST`, `S3VAULT`, `SCUBA_HOST`, `S3KMIP_HOSTS`) and config.json. The Docker entrypoint script generates configuration from environment variables, enabling dynamic configuration at deployment time. This is a step above hard-coded endpoints but falls short of dynamic service discovery (no Consul, no AWS Service Discovery, no DNS-based discovery). |
| **Gap** | Environment variable-based configuration is better than hardcoded endpoints but requires restart to pick up changes. No dynamic service discovery for runtime endpoint changes, failover, or service mesh routing. |
| **Recommendation** | When deploying to EKS, leverage Kubernetes DNS-based service discovery. For cross-cluster or cross-account communication, adopt AWS Cloud Map or VPC Lattice. |
| **Evidence** | `docker-entrypoint.sh` (env var config generation), `config.json` (static endpoints), `lib/Config.js` (reads env vars at startup) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application IS an S3-compatible object store — it stores unstructured data in multiple backends including file system (`localData/`), Sproxyd (Scality RING), AWS S3, Azure Blob, and GCP. However, for its own operational needs, data is stored in local file system volumes (`localData/`, `localMetadata/`) and MongoDB. No S3 or managed object storage is used for the server's own operational data (logs, audit trails, configuration backups). |
| **Gap** | The server stores its own operational data (server access logs at `/logs/server-access.log`, local metadata, local data) on local filesystems rather than managed object storage. No parsing pipeline for access logs exists. |
| **Recommendation** | Route server access logs to S3 with a parsing pipeline (Athena for query, or Textract for unstructured analysis). Store operational data in S3 rather than local volumes for durability and accessibility. |
| **Evidence** | `config.json` (serverAccessLogs outputFile: "/logs/server-access.log"), `Dockerfile` (VOLUME localData, localMetadata), `schema/server_access_log.schema.json` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a reasonably centralized data access layer. Metadata access goes through `lib/metadata/` abstraction (supporting MongoDB, LevelDB, bucketd backends). Data access goes through `lib/data/` abstraction (supporting file, memory, multiple backends including S3, Azure, GCP, Sproxyd). The `arsenal` library provides shared data models and serialization. However, some modules access MongoDB directly for operational queries, and configuration/auth data is accessed through separate pathways (lib/auth/, lib/Config.js). |
| **Gap** | While primary data and metadata access is centralized, configuration data, auth data, and some operational queries bypass the main abstraction layers. |
| **Recommendation** | Consolidate remaining direct access patterns through the existing abstraction layers. Ensure all MongoDB access goes through the metadata abstraction rather than direct driver calls. |
| **Evidence** | `lib/metadata/` (centralized metadata abstraction), `lib/data/` (centralized data abstraction), `lib/Config.js` (separate config access), `lib/auth/` (separate auth data access) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | MongoDB driver version is explicitly pinned in package.json (`mongodb` ^6.11.0). The CI MongoDB image is custom-built (`.github/docker/mongodb/Dockerfile`) but the base version is not explicitly visible from the Dockerfile reference alone. The driver version (6.x) is compatible with MongoDB 6.0-8.0 server versions, all of which are within support. Redis uses `redis:alpine` image (latest) in Docker compose without explicit version pinning. |
| **Gap** | MongoDB server version is not explicitly pinned in the CI Docker image reference. Redis version is unpinned (uses latest alpine image). No documented version-update procedure exists. |
| **Recommendation** | Pin MongoDB server version explicitly in CI compose (e.g., `mongo:7.0`). Pin Redis version. Document a version-update procedure covering downtime, rollback, and driver compatibility. When migrating to DocumentDB, the engine version will be managed by AWS. |
| **Evidence** | `package.json` (mongodb: ^6.11.0), `.github/docker/docker-compose.yaml` (${MONGODB_IMAGE}, redis:alpine), `.github/docker/mongodb/Dockerfile` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic is in the Node.js application layer. MongoDB is used for metadata storage with standard CRUD operations via the mongodb driver. The data model uses MongoDB indexes and compound queries but no server-side JavaScript, MapReduce, or aggregation pipelines with complex business logic. Minor dependency: the `sql-where-parser` package is used for metadata search query parsing in the application layer (not database-side SQL). |
| **Gap** | Minor: some MongoDB-specific query patterns (e.g., `$regex`, `$in` with specific semantics) may need adjustment when migrating to DocumentDB, which has some MongoDB compatibility gaps. |
| **Recommendation** | Validate DocumentDB compatibility for existing MongoDB queries before migration. The `sql-where-parser` is application-layer only and not a concern. Test aggregation queries (if any) against DocumentDB's supported operations. |
| **Evidence** | `package.json` (sql-where-parser for app-layer search), absence of `.sql` files, absence of `CREATE PROCEDURE/TRIGGER/FUNCTION`, `lib/metadata/` (standard CRUD operations) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent infrastructure audit logging is configured. The application has S3 server access logging (`serverAccessLogs` in config.json writing to `/logs/server-access.log`) and a structured JSON schema for access logs (`schema/server_access_log.schema.json`). Application-level logging uses `werelogs` for structured operational logs. However, there is no infrastructure-level audit trail (who deployed what, who changed configuration, API call audit). |
| **Gap** | No infrastructure audit logging (CloudTrail). Server access logs exist but are written to local filesystem without immutable storage. No log file validation or tamper protection. |
| **Recommendation** | Enable CloudTrail for all AWS API calls when deploying to AWS. Ship server access logs to S3 with Object Lock for immutability. Configure CloudWatch Logs for application logs with defined retention. |
| **Evidence** | `config.json` (serverAccessLogs to local file), `schema/server_access_log.schema.json`, absence of `aws_cloudtrail` or any audit logging infrastructure |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements server-side encryption (SSE) for stored objects via multiple KMS backends: file-based keys (`lib/kms/file/`), in-memory keys (`lib/kms/in_memory/`), AWS KMS integration (`kmsAWS` in config.json), and KMIP (enterprise key management). The KMS wrapper (`lib/kms/wrapper.js`) supports key rotation and per-account default encryption keys. However, MongoDB metadata is not encrypted at rest in any configuration. No KMS key for metadata encryption is defined. Local data volumes have no filesystem-level encryption. |
| **Gap** | Object data encryption is well-implemented with multiple KMS backends. However, metadata in MongoDB and local storage volumes lack encryption at rest configuration. No customer-managed KMS key for infrastructure-level encryption. |
| **Recommendation** | When migrating to DocumentDB, enable encryption at rest with customer-managed KMS key. Enable EBS encryption for any persistent volumes. Ensure the existing KMS infrastructure (AWS KMS backend) uses customer-managed keys with documented rotation policy. |
| **Evidence** | `lib/kms/wrapper.js`, `lib/kms/file/`, `config.json` (kmsAWS section), `lib/kms/Cache.js`, absence of MongoDB encryption config, absence of `aws_kms_key` in IaC |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive S3 authentication is implemented: AWS Signature V4 (`lib/auth/streamingV4/`), integration with external Vault IAM service (`lib/auth/vault.js`), and in-memory accounts for development. All S3 API endpoints require authentication (AWS Sig V4). The health check endpoint is restricted by IP allowlist (`healthChecks.allowFrom` in config.json). However, authentication is custom-implemented rather than using a standard OAuth2/JWT flow, and some internal routes (Backbeat, management) have their own auth patterns. |
| **Gap** | Authentication is strong for S3 operations (AWS Sig V4) but is custom-implemented. Internal service routes (Backbeat) may have weaker authentication. No OAuth2/JWT for management API. |
| **Recommendation** | Maintain AWS Sig V4 for S3 operations (protocol requirement). Add mTLS or JWT for internal service-to-service communication (Backbeat routes). When deploying behind API Gateway, leverage Cognito authorizers for management endpoints. |
| **Evidence** | `lib/auth/vault.js` (auth backend switcher), `lib/auth/streamingV4/` (Sig V4 implementation), `config.json` (healthChecks.allowFrom), `conf/authdata.json` (in-memory accounts) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application supports external identity federation via the Scality Vault service (`vaultclient` dependency, `S3VAULT` environment variable). Vault provides IAM-compatible authentication and can federate with external identity providers. The `S3VAULT=multiple` mode supports chaining multiple auth backends. However, no standard IdP integration (Cognito, Okta, SAML, OIDC) is configured directly — federation goes through the proprietary Vault service. In-memory auth mode (`S3VAULT=mem`) uses static accounts in `conf/authdata.json`. |
| **Gap** | Identity is managed through Scality's proprietary Vault service rather than a standard centralized IdP. No SSO, no OIDC/SAML federation configured directly. Fallback to static accounts in dev mode. |
| **Recommendation** | Integrate with Amazon Cognito for user identity management and OIDC federation. When deploying to AWS, replace Vault dependency with Cognito + IAM for authentication. Support SAML federation for enterprise SSO. |
| **Evidence** | `package.json` (vaultclient dependency), `lib/auth/vault.js` (vault/mem/multiple modes), `conf/authdata.json` (static dev accounts), `config.json` (vaultd host:port) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets management uses a combination of approaches: Docker secrets (`/run/secrets/s3-credentials` referenced in entrypoint), environment variables for production credentials (`MONGODB_HOSTS`, `REDIS_HOST`, various backend access keys), and GitHub Actions secrets for CI. The `conf/authdata.json` contains static development credentials committed to the repository (access keys "accessKey1", "verySecretKey1" etc.) — these are clearly labeled test/dev accounts but the pattern exists. The `config.json` has `kmsAWS.ak` and `kmsAWS.sk` with placeholder values "tbd". No Secrets Manager or Vault (AWS) integration exists in IaC. |
| **Gap** | No dedicated secrets management service with rotation. Production credentials are in environment variables without encryption or rotation. Development credentials committed to repository (test accounts). KMS credentials use "tbd" placeholders in config rather than secret references. |
| **Recommendation** | Adopt AWS Secrets Manager for all production secrets (MongoDB credentials, Redis passwords, KMS keys, backend access keys). Configure automatic rotation for database credentials. Remove placeholder credential patterns from config.json — use Secrets Manager ARN references instead. |
| **Evidence** | `conf/authdata.json` (static dev credentials), `config.json` (kmsAWS.ak: "tbd", sk: "tbd"), `docker-entrypoint.sh` (env var based), `.github/workflows/tests.yaml` (GH Actions secrets for CI) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The production Docker image uses `node:22.14.0-bookworm-slim` (Debian slim variant) with minimal packages installed. The builder stage includes build tools that are not carried to production (multi-stage build). Production stage only adds `jq`, `tini`, `python3-redis`, `python3-requests`. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk) on the container image, no hardened base image (Bottlerocket, distroless). Dependency review (`dependency-review.yaml`) runs on PRs but is limited to new dependencies. |
| **Gap** | No container image vulnerability scanning in CI/CD pipeline. Using Debian-based image rather than hardened alternative. No runtime patching strategy. Dependency review only checks new additions, not existing vulnerabilities. |
| **Recommendation** | Add ECR image scanning or Trivy/Snyk container scanning to the CI pipeline. Consider Bottlerocket or distroless base images for reduced attack surface. Implement automated dependency updates (Dependabot or Renovate) for existing dependencies. |
| **Evidence** | `Dockerfile` (node:22.14.0-bookworm-slim), `.github/workflows/dependency-review.yaml` (PR-only), absence of Snyk, Trivy, or Inspector configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Security scanning is present: CodeQL (`codeql.yaml`) for SAST on JavaScript, Python, Ruby. Dependency review (`dependency-review.yaml`) on pull requests. However, no container scanning, no DAST, and no explicit security gate that blocks merges on critical findings. CodeQL runs on push and PR to development/hotfix branches. |
| **Gap** | CodeQL provides SAST coverage. Missing: container image scanning, DAST, explicit blocking gate on critical security findings. Dependency review is PR-only (not on existing dependencies). |
| **Recommendation** | Add container image scanning (ECR native or Trivy) to the build job. Configure CodeQL to block PRs on critical/high findings. Add `npm audit` or Snyk to the CI pipeline for existing dependency vulnerabilities. |
| **Evidence** | `.github/workflows/codeql.yaml` (CodeQL for JS/Python/Ruby), `.github/workflows/dependency-review.yaml` (PR dependency review), absence of container scanning, absence of blocking gates |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses structured logging via `werelogs` (Scality logging library) with request IDs for per-request correlation. Prometheus metrics are exposed on port 8002 via `prom-client` ^15.1.3. However, no distributed tracing (X-Ray, OpenTelemetry) is instrumented. There is no trace ID propagation across service boundaries (metadata server, data server, Backbeat, Vault). Request correlation exists within a single process but not across services. |
| **Gap** | No distributed tracing instrumentation. Cannot trace a request across S3 API → metadata → data → external backends. Request IDs exist but are not propagated as trace contexts. |
| **Recommendation** | Instrument OpenTelemetry SDK for distributed tracing with X-Ray exporter. Propagate trace context (W3C traceparent header) between internal services (metadata, data, Backbeat). This is critical for debugging multi-backend operations. |
| **Evidence** | `package.json` (werelogs, prom-client — no OpenTelemetry/X-Ray), `lib/utilities/logger.js`, absence of `@opentelemetry/*` or `aws-xray-sdk` imports |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No formal SLO definitions exist. Prometheus alerting rules (`monitoring/alerts.yaml`) define thresholds for endpoint health (< 100% = warning, < 50% = critical), system error rates (3% warning, 5% critical), and latency (listing 300ms/500ms, delete 500ms/1000ms). These are operational alerts, not SLO definitions with error budgets. No error budget tracking, no SLO dashboards, no formal SLO documentation. |
| **Gap** | Alerting thresholds exist but no formal SLOs are defined. No error budget tracking. Cannot measure whether the service is meeting user expectations over time windows. |
| **Recommendation** | Define SLOs for critical S3 operations: availability (99.9%), p99 latency for GET/PUT/LIST/DELETE, error rate. Use CloudWatch ServiceLevelObjective or Prometheus-based SLO tracking with error budgets. |
| **Evidence** | `monitoring/alerts.yaml` (threshold alerts only), absence of SLO definition files, absence of error budget configuration |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus metrics are exposed (prom-client ^15.1.3) and a Grafana dashboard exists (`monitoring/dashboard.json`). The UTAPI (Usage Tracking API) module tracks per-account storage utilization and API call counts. Server access logs capture per-request data. However, metrics appear to be primarily operational (request counts, latencies, error rates, endpoint health) rather than business-outcome metrics. No custom CloudWatch metrics for business KPIs. |
| **Gap** | Operational metrics exist. Missing: business-outcome metrics (storage growth rate per account, data transfer costs, SLA adherence per customer, capacity planning signals). UTAPI provides usage data but it's not published as CloudWatch metrics. |
| **Recommendation** | Publish UTAPI metrics to CloudWatch as custom metrics for per-account dashboards. Add business metrics: storage utilization trends, API operation distribution, backend latency comparison, capacity forecast signals. |
| **Evidence** | `package.json` (prom-client, utapi), `monitoring/dashboard.json`, `lib/utapi/`, `lib/utilities/monitoringHandler.js` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Static threshold alerts are defined in `monitoring/alerts.yaml`: endpoint health, system error rate thresholds (3%/5%), latency thresholds for specific operations (listing, delete). Alert severity levels (warning, critical) are defined with `for` durations (30s). However, no anomaly detection is configured. All alerts use fixed thresholds rather than dynamic baselines. No composite alarms or multi-signal correlation. |
| **Gap** | Alerting is threshold-based only. Cannot detect gradual degradation, novel failure modes, or seasonal traffic pattern deviations. |
| **Recommendation** | Enable CloudWatch anomaly detection on key metrics (error rate, latency p99) after migrating monitoring to CloudWatch. Configure composite alarms for multi-signal alerting. Consider ML-based anomaly detection for storage growth and API pattern changes. |
| **Evidence** | `monitoring/alerts.yaml` (static thresholds only), `monitoring/alerts.test.yaml` (threshold test cases), absence of anomaly detection configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployment is image-push only: the release workflow builds Docker images and pushes to GHCR with version tags. No deployment strategy (blue/green, canary, rolling) is defined in this repository. The docker-compose for CI uses direct container replacement. No CodeDeploy, no Argo Rollouts, no Helm canary, no traffic shifting configuration exists. |
| **Gap** | No staged deployment strategy. Production releases go directly to the registry without canary, blue/green, or progressive rollout. No automated rollback mechanism. |
| **Recommendation** | Implement canary or blue/green deployments via EKS with Argo Rollouts or AWS App Mesh traffic shifting. Start with rolling updates in Kubernetes with health check gates, then progress to canary with automated rollback on error rate increase. |
| **Evidence** | `.github/workflows/release.yaml` (image push only, no deployment), absence of deployment strategy configuration, absence of CodeDeploy, Argo Rollouts, or Flagger |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive functional test suites run in CI: AWS SDK tests, s3cmd tests, raw Node.js HTTP tests, health check tests, Backbeat integration tests, KMIP encryption tests, SSE/KMS migration tests, multi-backend tests, metadata format tests. Tests run against real MongoDB, Redis, PyKMIP, and storage backends (Sproxyd, Ceph) via Docker compose. Coverage reported to Codecov with 80% patch target. However, these are integration tests against a local Docker environment, not against deployed production-like infrastructure. |
| **Gap** | Integration tests exist and are comprehensive for local Docker testing. Missing: integration tests against deployed staging infrastructure (real DocumentDB, real ElastiCache, real EKS). All tests run against co-located containers, not network-separated services. |
| **Recommendation** | Add a staging integration test stage that runs the AWS SDK functional test suite against a deployed staging environment (EKS + DocumentDB + ElastiCache). This validates real network conditions, IAM permissions, and managed service behavior. |
| **Evidence** | `.github/workflows/tests.yaml` (multiple functional test jobs), `tests/functional/` (15 subdirectories), `.github/docker/docker-compose.yaml` (test infrastructure) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automation documents, or incident response workflows exist in the repository. No SSM Automation documents, no Lambda remediation, no self-healing patterns. The Prometheus alerts define severity levels but have no associated response procedures. The health check endpoint (`/healthcheck`) provides basic readiness information but no automated remediation. |
| **Gap** | No incident response automation or runbooks. Alerts fire but response is entirely manual. No self-healing for common failure modes (MongoDB connection loss, Redis unavailability, backend timeout). |
| **Recommendation** | Create runbooks for common incidents: MongoDB failover handling, Redis connection recovery, backend timeout escalation, disk space exhaustion. Implement self-healing with SSM Automation or Kubernetes liveness/readiness probes with restart policies. |
| **Evidence** | Absence of runbook files, absence of SSM Automation documents, absence of Lambda remediation functions, `monitoring/alerts.yaml` (alerts without response procedures) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The monitoring directory contains team-owned observability assets: Prometheus alerts with clear ownership (alerts.yaml), Grafana dashboard (dashboard.json), and a dashboard generator (dashboard.py). Alert test cases exist (alerts.test.yaml, alerts.10s.test.yaml) showing maintained ownership. The Codecov configuration defines per-component coverage flags. However, no CODEOWNERS file references observability assets, no named team/person ownership on alarms, no SLO attribution. |
| **Gap** | Observability assets exist and are maintained (evidenced by test cases). Missing: explicit team/person ownership attribution on alarms, CODEOWNERS for monitoring/, SLO definitions tied to specific teams. |
| **Recommendation** | Add CODEOWNERS entries for monitoring/ directory. Add team attribution labels to Prometheus alerts. Define SLOs with team ownership for accountability. |
| **Evidence** | `monitoring/alerts.yaml`, `monitoring/alerts.test.yaml`, `monitoring/dashboard.json`, `monitoring/dashboard.py`, absence of CODEOWNERS |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker images pushed to GHCR include labels (`git.repository`, `git.commit-sha`) in the release and test workflows. Prometheus metrics include namespace and service labels in alert definitions. However, no AWS resource tagging standard exists — no `default_tags` in Terraform (no Terraform exists), no tag enforcement, no cost allocation tags. |
| **Gap** | Container image labels exist but no AWS resource tagging strategy is defined. When infrastructure moves to IaC, there will be no tagging standard in place. |
| **Recommendation** | Define a tagging standard before creating IaC: Environment, Service, Team, CostCenter at minimum. Implement `default_tags` in Terraform provider configuration. Add AWS Config rules for tag enforcement. |
| **Evidence** | `.github/workflows/release.yaml` (Docker labels: git.repository, git.commit-sha), `monitoring/alerts.yaml` (namespace, service labels), absence of AWS resource tags |

---

## Learning Materials

- **Move to Cloud Native:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Managed Databases:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Modern DevOps:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `Dockerfile` | INF-Q1, APP-Q1, SEC-Q6 | Multi-stage Docker build, Node.js 22, base image |
| `.github/docker/docker-compose.yaml` | INF-Q1, INF-Q2, INF-Q5, INF-Q9, OPS-Q6 | CI test infrastructure (MongoDB, Redis, services) |
| `config.json` | INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, SEC-Q1, SEC-Q2, SEC-Q5 | Main server configuration |
| `package.json` | APP-Q1, DATA-Q3, OPS-Q1, OPS-Q3 | Dependencies, engine version, SDK versions |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q6 | CI pipeline (lint, unit, functional tests) |
| `.github/workflows/release.yaml` | INF-Q11, OPS-Q5, OPS-Q9 | Release workflow (image push) |
| `.github/workflows/codeql.yaml` | SEC-Q7 | SAST scanning |
| `.github/workflows/dependency-review.yaml` | SEC-Q6, SEC-Q7 | Dependency vulnerability review |
| `monitoring/alerts.yaml` | OPS-Q2, OPS-Q4, OPS-Q7, OPS-Q8 | Prometheus alerting rules |
| `monitoring/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard |
| `lib/auth/vault.js` | SEC-Q3, SEC-Q4 | Authentication backend switcher |
| `lib/auth/streamingV4/` | SEC-Q3 | AWS Sig V4 authentication |
| `lib/kms/wrapper.js` | SEC-Q2 | KMS backend abstraction |
| `lib/metadata/` | DATA-Q2, APP-Q2 | Metadata access abstraction |
| `lib/data/` | DATA-Q2, APP-Q2 | Data access abstraction |
| `lib/Config.js` | APP-Q2, APP-Q6 | Configuration management (95KB) |
| `lib/routes/routeBackbeat.js` | INF-Q3, INF-Q4, APP-Q3 | Replication route handlers |
| `lib/utilities/monitoringHandler.js` | OPS-Q3 | Prometheus metrics handler |
| `conf/authdata.json` | SEC-Q5 | Static development credentials |
| `docker-entrypoint.sh` | APP-Q6, SEC-Q5 | Runtime config generation |
| `index.js` | APP-Q2, INF-Q6 | Main S3 API entry point |
| `mdserver.js` | APP-Q2 | Metadata server entry point |
| `dataserver.js` | APP-Q2 | Data server entry point |
| `tests/functional/` | OPS-Q6 | Functional test suites (15 directories) |
| `schema/server_access_log.schema.json` | DATA-Q1, SEC-Q1 | Access log schema |
| `lib/utapi/` | OPS-Q3 | Usage tracking API |
