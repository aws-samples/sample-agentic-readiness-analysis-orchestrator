# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | scality--cloudserver |
| **Date** | 2026-05-08 |
| **TD Version** | modernization-assessment |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, storage, s3 |
| **Context** | Scality open-source S3-compatible object-storage server. |
| **Overall Score** | 2.34 / 4.0 |

**Archetype Justification**: The application owns persistent state via MongoDB (metadata) and Redis (caching/rate-limiting). It exposes full CRUD operations on S3 objects and buckets (PUT, GET, DELETE, POST). User-specific data is managed through access keys and accounts. Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true, has_iac_provisioning_aws_resources=false

**Classification Tier**: 🟠 Remediation Required

**Classification Rationale**: This repo has 2 High findings, 18 Medium findings, 11 Low findings. Rule matched: "2-11 High → Remediation Required". MOD classification differs from ARA: ARA's "1 High" is an agent-deployment gate (safety concern); MOD's "1 High" maps to Pilot-Ready because a single modernization gap is typically not a deployment blocker. MOD requires ≥2 High findings to reach Remediation Required.

```
classification_consistency_check: consistent
V5 band: Needs Work (score 2.34, range 1.5–2.4)
V6 tier: Remediation Required (2 High findings)
Equivalence: V5 Needs Work ≡ V6 Remediation Required ✓
```

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 1.82 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Operations & Observability (OPS) | 2.13 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.34 / 4.0** | **🟠 Needs Work** | **Critical** |

**Scoring Notes:**
- INF: (3+2+2+4+1+1+1+1+1+1+3) / 11 = 20/11 = 1.82
- APP: (4+2+NE+NE+2+2) / 4 = 10/4 = 2.50
- DATA: (3+3+2+3) / 4 = 11/4 = 2.75
- SEC: (NE+3+3+2+2+2+3) / 6 = 15/6 = 2.50
- OPS: (1+2+3+3+NE+3+1+2+2) / 8 = 17/8 = 2.13
- Overall: (1.82+2.50+2.75+2.50+2.13) / 5 = 11.70/5 = 2.34

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group definitions found in this repo | Cannot verify network isolation; services may be exposed without proper segmentation |
| 2 | INF-Q10: IaC Coverage | 1 | No Infrastructure as Code found in this repository | Infrastructure changes are manual, non-reproducible, and error-prone |
| 3 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumented (no OpenTelemetry, X-Ray) | Debugging failures across service boundaries is guesswork |
| 4 | OPS-Q7: Incident Response | 1 | No runbooks or automated incident response found | Incident response is entirely ad hoc with no structured playbooks |
| 5 | INF-Q6: API Entry Point | 1 | No API Gateway, ALB, or CloudFront entry point defined | Services lack throttling, auth offload, and centralized traffic management |

---

## Quick Agent Wins

### DevOps Agent
- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions workflows automate build, test, lint, and Docker image publishing.
- **What it enables:** An agent that triggers deployments, checks build status, monitors workflow runs, and manages release processes via the GitHub Actions API.
- **Additional steps:** Expose workflow dispatch endpoints and build status APIs for agent consumption.
- **Effort:** Low

### RAG-based Knowledge Agent
- **Prerequisite:** Documentation exists in the repo (README.md, DESIGN.md, CONTRIBUTING.md, TESTING.md, Healthchecks.md, docs/ directory with Sphinx documentation).
- **What it enables:** A knowledge agent that indexes existing documentation and answers developer questions about S3 API implementation, deployment, and configuration.
- **Additional steps:** Index Markdown and RST documentation files into a vector store; documentation is already well-structured.
- **Effort:** Medium

### Observability Agent
- **Prerequisite:** Structured logging and metrics in place (OPS-Q1 scored 1 for tracing, but Prometheus metrics are mature). Comprehensive Prometheus metrics and alerting rules exist. Alert rules cover endpoint health, error rates, and latency.
- **What it enables:** An agent that queries Prometheus metrics, correlates alert firings, and suggests root causes based on metric patterns.
- **Additional steps:** Distributed tracing should be added first for full cross-service correlation. Currently limited to metrics-only analysis.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=3 (mix of managed/self-managed) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=3; container definitions already present (8 Dockerfiles, docker-compose) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=3 (minimal stored procedures); no commercial DB engines detected (MongoDB is open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=2 (self-managed MongoDB/Redis), DATA-Q3=2 (no version pinning in IaC) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4=4 (sync is correct design); no data processing workloads detected |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), OPS-Q6=3 (partial), INF-Q5=1, INF-Q6=1, INF-Q7=1, INF-Q8=1, INF-Q9=1 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a single deployable monolith (APP-Q2=2). While it has identifiable modules (lib/api, lib/data, lib/metadata, lib/kms, lib/auth), they share a single process, single config.json, and direct in-process calls. The metadata layer, data layer, and API layer are tightly coupled through shared imports and direct function calls.

**Compute Model:** Container-ready (Dockerized, deployed to Kubernetes externally), but the application itself is a single monolithic Node.js process with cluster-mode parallelism rather than microservice decomposition.

**Communication Pattern Gaps:** Inter-module communication is entirely synchronous in-process function calls. No async event-driven patterns for cross-module state changes.

**Recommended Decomposition Approach:** See Decomposition Strategy section below.

**Representative AWS Services:** EKS (preferred per preferences), Lambda for lightweight operations, API Gateway for S3 API entry point, EventBridge for async events between extracted services, DynamoDB (preferred per preferences) for metadata where appropriate.

**Recommended Patterns:** Strangler Fig (extract metadata service first), Anti-corruption Layer between monolith and new services, Event Sourcing for object lifecycle events.

**Learning Resources:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** MongoDB replica set (self-managed in containers/VMs) for metadata storage. Redis (self-managed) for caching and rate limiting. Both are configured via environment variables and docker-compose for CI, but production deployment uses self-managed instances.

**Engine Versions and EOL:** MongoDB ^6.11.0 driver used (compatible with MongoDB 6.x/7.x). No explicit engine version pinning in IaC (no IaC exists). Redis version not pinned.

**Data Access Patterns:** Metadata access is centralized through `lib/metadata/wrapper.js`. Redis access is centralized through arsenal's RedisClient. The data access layer is well-structured for migration.

**Recommended Managed Database Targets:**
- **MongoDB → Amazon DocumentDB** (MongoDB-compatible) or **DynamoDB** (preferred per preferences) for metadata storage
- **Redis → Amazon ElastiCache for Redis** or **Amazon MemoryDB** for caching and rate limiting

**Representative AWS Services:** DocumentDB, DynamoDB (preferred), ElastiCache, MemoryDB
**Migration Tools:** AWS DMS for MongoDB-to-DocumentDB migration

**Learning Resources:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** No Infrastructure as Code exists in this repository (INF-Q10=1). All infrastructure is provisioned externally or manually. No Terraform, CloudFormation, CDK, or Helm charts.

**Current CI/CD State:** GitHub Actions provides build, test, lint, and Docker image publishing automation (INF-Q11=3). However, there is no deployment automation — the release workflow only builds and pushes Docker images to ghcr.io; actual deployment to Kubernetes is handled externally.

**Deployment Strategy Gaps:** No canary, blue/green, or rolling deployment configuration found in this repo (OPS-Q5=Not Evaluated due to surface gating — deployment orchestration managed externally).

**Testing Gaps:** Extensive functional and unit tests exist (OPS-Q6=3), but integration testing in CI could be more comprehensive with contract tests.

**Recommended DevOps Toolchain:**
- **IaC:** CDK or Terraform for EKS cluster, DocumentDB/DynamoDB, ElastiCache, networking
- **CI/CD:** AWS CodePipeline + CodeBuild (or continue GitHub Actions with AWS deployment integration)
- **Deployment:** ArgoCD on EKS (preferred per EKS preference) with canary deployments via Argo Rollouts
- **Observability:** CloudWatch Container Insights + X-Ray for distributed tracing

**Representative AWS Services:** CDK, CodePipeline, CodeBuild, EKS, CloudWatch, X-Ray

**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2=2 — the monolith has identifiable modules (api, data, metadata, kms, auth) that can be extracted incrementally. | Medium to High | ✅ **Recommended.** Extract metadata service first, then data/storage service, while keeping monolith running. |
| **Conditional / Adaptive** | Team capacity is limited; containerization is already done. Selectively extract high-value modules. | Low to Medium | ✅ **Also viable** given the application is already containerized and deployed to Kubernetes. |
| **Big-Bang Rewrite** | Almost never appropriate. | Very High | ⚠️ **Recommended against.** The monolith is functional with clear module boundaries — incremental extraction is safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's internal data model | Every extraction — place between new metadata service and remaining monolith |
| **Saga Pattern** | Manage distributed transactions for multi-object operations | When extracting operations that span metadata + data layers (e.g., multipart upload) |
| **Event Sourcing** | Capture object lifecycle events as a stream | For replication, lifecycle, and notification features — already partially implemented via Backbeat integration |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters | Every new service — the existing multi-backend pattern (lib/data/wrapper.js, lib/metadata/wrapper.js) already follows this pattern |

### Effort Estimation

| Factor | Assessment | Signal |
|--------|-----------|--------|
| Module boundaries | Clear (api, data, metadata, kms, auth directories) | Low effort |
| Data coupling | Moderate — metadata and data layers share config and some state | Medium effort |
| Stored procedures | None — all logic in application layer | Low effort |
| Communication patterns | All synchronous in-process calls | Medium effort to introduce async |
| CI/CD maturity | CI exists but no deployment automation | Medium effort to extend |
| Test coverage | Extensive test suite with functional tests | Low risk during extraction |

**Recommended first extraction:** The metadata service (`lib/metadata/`) is the clearest candidate — it has a well-defined wrapper interface, uses MongoDB as its backend, and has minimal dependencies on other modules.

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application is containerized (multi-stage Dockerfile using node:22.14.0-bookworm-slim) and deployed to Kubernetes (evidenced by monitoring/alerts.yaml referencing Kubernetes namespaces and services). However, this repo does not contain the Kubernetes deployment manifests or EKS configuration — those are managed externally. The Docker Compose files are for CI testing only. |
| **Gap** | Kubernetes orchestration configuration is not co-located with the application. Cannot confirm whether EKS (managed) or self-managed Kubernetes is used. |
| **Recommendation** | Adopt EKS (preferred per preferences) for managed container orchestration. Co-locate Helm charts or Kustomize manifests with the application code for deployment transparency. |
| **Evidence** | Dockerfile, .github/docker/docker-compose.yaml, monitoring/alerts.yaml (references `${namespace}`, `artesca-data-connector-s3api-metrics`) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MongoDB (replica set) is used for metadata storage and Redis for caching/rate-limiting. Both are self-managed — configured via environment variables (MONGODB_HOSTS, REDIS_HOST, REDIS_SENTINELS) and run in containers for CI. No managed database services (DocumentDB, ElastiCache) are referenced. Docker Compose spins up MongoDB in a custom container image (.github/docker/mongodb/Dockerfile). |
| **Gap** | All databases are self-managed. No managed database services in use. Operational burden includes manual patching, backup configuration, and scaling. |
| **Recommendation** | Migrate MongoDB to Amazon DocumentDB (MongoDB-compatible) or DynamoDB (preferred). Migrate Redis to Amazon ElastiCache for Redis or MemoryDB for Redis. Both provide automatic failover, backups, and patching. |
| **Evidence** | config.json (mongodb section), docker-entrypoint.sh (MONGODB_HOSTS, REDIS_HOST, REDIS_SENTINELS env vars), .github/docker/docker-compose.yaml, package.json (mongodb ^6.11.0) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application handles multi-step operations (multipart uploads, cross-region replication, lifecycle management) through in-code orchestration. The config.json references `workflowEngineOperator` (external) and `backbeat` for async replication/lifecycle, but within the CloudServer codebase, complex operations like multipart upload are implemented as hardcoded state machines in application code (lib/api/objectPutPart.js, lib/api/completeMultipartUpload.js). |
| **Gap** | Multi-step operations (multipart upload coordination, lifecycle transitions) are implemented as in-code state machines without dedicated orchestration. Error handling and retry logic are embedded in application code. |
| **Recommendation** | For the stateful-crud archetype, consider AWS Step Functions for multi-step operations like multipart upload lifecycle coordination and cross-region replication workflows. The existing Backbeat integration suggests some workflow externalization already exists — extend this pattern to CloudServer's internal multi-step operations. |
| **Evidence** | config.json (workflowEngineOperator, backbeat sections), lib/api/objectPutPart.js, lib/api/completeMultipartUpload.js |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | For a stateful-crud service, the application appropriately uses synchronous request/response for S3 API operations (the core CRUD surface). Async patterns are delegated to the external Backbeat service for replication and lifecycle management. Bucket notifications are configured but use an external notification destination. Redis pub/sub is used for internal cache invalidation. This is the correct architectural pattern for an S3 API server — the synchronous request/response model matches the S3 protocol contract. |
| **Gap** | N/A — architecture is appropriate for the service archetype. |
| **Recommendation** | Current design is appropriate. If decomposing into microservices, introduce EventBridge (preferred) for cross-service state change notifications. The existing Backbeat delegation pattern is a good model to extend. |
| **Evidence** | config.json (backbeat, bucketNotificationDestinations), lib/server.js (synchronous HTTP handling), package.json (no SQS/SNS/Kafka client deps) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation definitions exist in this repository. The application binds to configured addresses (LISTEN_ADDR env var, defaults to all interfaces) and health checks are IP-allowlisted (config.json healthChecks.allowFrom: ["127.0.0.1/8", "::1"]), but no infrastructure-level network isolation is defined. |
| **Gap** | No network security infrastructure defined. Cannot verify that the application runs in private subnets with proper segmentation. Network security is likely managed in a separate infrastructure repository. |
| **Recommendation** | Define VPC with private subnets, least-privilege security groups (allow only port 8000 from ALB, port 8002 from monitoring), and network segmentation in IaC. Consider VPC endpoints for AWS service access. Since this is an application repo and networking may be managed elsewhere, verify that the external infrastructure provides proper isolation. |
| **Evidence** | No .tf, CloudFormation, or CDK files found. config.json (healthChecks.allowFrom), docker-entrypoint.sh (LISTEN_ADDR) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or load balancer configuration exists in this repository. The S3 server listens directly on port 8000. The monitoring/alerts.yaml references a Kubernetes service (`artesca-data-connector-s3api-metrics`), suggesting a Kubernetes Service resource exists externally, but no ingress, load balancer, or gateway configuration is present here. |
| **Gap** | No managed entry point with throttling, authentication offload, or request validation defined. Direct service exposure without centralized traffic management. |
| **Recommendation** | Deploy behind an Application Load Balancer or API Gateway (preferred per preferences). Configure throttling, health-check-based routing, and TLS termination at the entry point. For S3-compatible API, ALB with path-based routing is more appropriate than API Gateway due to the binary data streaming requirements. |
| **Evidence** | No ALB, API Gateway, or CloudFront resources found. config.json (port: 8000 direct listen), monitoring/alerts.yaml (Kubernetes service reference) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found in this repository. The application supports cluster mode (config.json: clusters: 1) for multi-process execution within a single container, but no HPA (Horizontal Pod Autoscaler), ASG, or application auto-scaling definitions exist. |
| **Gap** | No auto-scaling mechanisms configured for compute or database workloads. Static capacity provisioning means the service cannot respond to traffic spikes. |
| **Recommendation** | Define Kubernetes HPA on EKS (preferred) based on request rate and latency metrics (already exposed via Prometheus). Configure auto-scaling for DocumentDB/ElastiCache when migrating to managed databases. Consider KEDA for event-driven scaling. |
| **Evidence** | config.json (clusters: 1), no HPA or auto-scaling definitions found |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found in this repository. MongoDB is used for metadata storage and Redis for caching, but no automated backup plans, retention policies, or PITR (Point-in-Time Recovery) configurations are defined. Backup responsibility is likely external. |
| **Gap** | No backup or recovery configuration. Data loss protection depends entirely on external infrastructure management. |
| **Recommendation** | When migrating to managed databases: enable automated backups on DocumentDB with 7+ day retention and PITR. For ElastiCache, enable automatic backups. Define an AWS Backup plan covering all data stores. Document and test restore procedures. |
| **Evidence** | No aws_backup_plan, backup_retention_period, or point_in_time_recovery configurations found |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration exists in this repository. The MongoDB replica set configuration (3 hosts: localhost:27018,27019,27020) suggests HA intent at the database layer, but actual AZ distribution is not configured here. Redis Sentinel support exists (REDIS_SENTINELS env var) for Redis HA. However, no infrastructure-level multi-AZ configuration is present. |
| **Gap** | No multi-AZ deployment verified. Cannot confirm that compute or databases span multiple AZs. HA depends on external infrastructure configuration. |
| **Recommendation** | When deploying to EKS (preferred), configure node groups across 3 AZs. DocumentDB clusters automatically support multi-AZ. ElastiCache should be configured with multi-AZ automatic failover. Define pod topology spread constraints for the CloudServer pods. |
| **Evidence** | config.json (mongodb.replicaSetHosts), docker-entrypoint.sh (REDIS_SENTINELS support), no multi-AZ IaC found |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code exists in this repository. No Terraform files, CloudFormation templates, CDK stacks, Helm charts, or Kustomize manifests were found. All infrastructure provisioning and Kubernetes deployment configuration is managed externally. |
| **Gap** | 0% IaC coverage in this repository. Infrastructure changes are managed outside this codebase with no visibility or version control alongside the application. |
| **Recommendation** | Adopt CDK (TypeScript, matching the Node.js stack) or Terraform to define: EKS cluster configuration, DocumentDB/ElastiCache instances, VPC/networking, ALB, auto-scaling policies, and backup plans. Co-locate IaC with the application for infrastructure-as-code visibility. Alternatively, define Helm charts for the Kubernetes deployment. |
| **Evidence** | No .tf, .tfvars, template.yaml, cdk.json, Chart.yaml, or kustomization.yaml files found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions provides comprehensive CI automation: lint (JS, Python, YAML, Markdown), unit tests with coverage, functional tests (multiple backends, MongoDB v0/v1, SSE-KMS, KMIP), Docker image build and push to ghcr.io, and security scanning (CodeQL, dependency review). The release workflow builds and publishes Docker images on manual trigger. However, no deployment automation exists — actual deployment to Kubernetes is handled externally. |
| **Gap** | CI/CD covers build and test but not deployment. No automated deployment pipeline from image build to production. No infrastructure-as-code deployment automation. |
| **Recommendation** | Extend CI/CD to include deployment automation: ArgoCD for GitOps-based Kubernetes deployment (aligns with EKS preference), or AWS CodePipeline with CodeDeploy for ECS/EKS deployment. Add deployment verification (smoke tests, canary analysis) to the pipeline. |
| **Evidence** | .github/workflows/tests.yaml (lint, unit, functional tests, build), .github/workflows/release.yaml (Docker push), .github/workflows/codeql.yaml, .github/workflows/dependency-review.yaml |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Node.js >= 22 (current LTS) with JavaScript. The Dockerfile pins node:22.14.0-bookworm-slim. Node.js 22 is a current, cloud-native-ready runtime with first-class AWS SDK support. The `aws-sdk` dependency is v2 (^2.1692.0) which is in maintenance mode, but the runtime itself is modern. Key frameworks: Express-like custom HTTP server (arsenal), Mocha for testing, prom-client for metrics. |
| **Gap** | AWS SDK v2 is used (maintenance mode) rather than AWS SDK v3 (modular, tree-shakeable). This is a framework lag signal but does not downgrade below 4 because the primary runtime (Node.js 22) is current and the SDK usage is limited to external backend interactions. |
| **Recommendation** | Migrate from aws-sdk v2 to @aws-sdk/* v3 modular packages for better performance, tree-shaking, and long-term support. This is a low-risk incremental change. |
| **Evidence** | package.json (engines: node >= 22, aws-sdk ^2.1692.0), Dockerfile (node:22.14.0-bookworm-slim) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a monolith with identifiable modules: lib/api (70 handlers), lib/data (storage backends), lib/metadata (MongoDB/LevelDB), lib/kms (encryption), lib/auth (vault integration), lib/utilities (monitoring, logging). These modules have clear directory boundaries and wrapper interfaces (data/wrapper.js, metadata/wrapper.js, kms/wrapper.js). However, they share a single process (index.js → lib/server.js), single configuration (config.json), and communicate through direct in-process function imports rather than service interfaces. Cross-module data access exists (API handlers directly import metadata and data wrappers). |
| **Gap** | Single deployable unit with shared configuration and direct cross-module coupling. Modules cannot be independently scaled, deployed, or replaced. The metadata layer and data layer are tightly coupled through shared config and direct imports. |
| **Recommendation** | Begin Strangler Fig decomposition — extract the metadata service first (already has a wrapper interface). Define API contracts between modules before extraction. See Decomposition Strategy section. |
| **Evidence** | index.js (single entry point), lib/server.js (single HTTP server), config.json (unified config), lib/api/*.js (direct imports of lib/metadata/wrapper, lib/data/wrapper) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateful-crud`. As a monolithic S3 API server, all inter-module communication is in-process synchronous function calls — there are no separate services communicating over the network. The question of async vs sync inter-service communication does not apply until the monolith is decomposed into separate services. Evaluating this question pre-decomposition would penalize the application for not having inter-service async patterns that are not yet architecturally relevant. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Single-process monolith with in-process function calls between modules |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateful-crud`. Long-running operations (multipart upload, large object PUT) are handled by the S3 protocol's built-in async patterns — multipart upload is inherently an async-with-status protocol (InitiateMultipartUpload → UploadPart → CompleteMultipartUpload). The S3 protocol design handles long-running processes at the protocol level rather than requiring application-level async job infrastructure. Cross-region replication and lifecycle management (operations that genuinely exceed 30 seconds) are delegated to the external Backbeat service. This question evaluates application-level async job handling which is not applicable here because the S3 protocol already provides the async pattern. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | S3 multipart upload protocol (lib/api/initiateMultipartUpload.js, lib/api/objectPutPart.js, lib/api/completeMultipartUpload.js), config.json (backbeat integration) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements the Amazon S3 API which does not use URL-path versioning. S3's versioning strategy is implicit — new features are added in a backward-compatible manner. The CloudServer does not define its own API versioning strategy for extensions or internal APIs. No /v1/, /v2/ patterns, version headers, or versioning annotations found. |
| **Gap** | No explicit versioning strategy for the S3 API extensions or internal management APIs. Breaking changes would affect all consumers simultaneously. |
| **Recommendation** | Since the API follows the S3 protocol, version compatibility is maintained by tracking AWS S3 API compatibility. For any custom extensions (management API, internal endpoints), implement version headers or URL-path versioning. Document which S3 API version is supported. |
| **Evidence** | lib/routes/routeGET.js, lib/routes/routePUT.js (no version path segments), lib/api/api.js (no version routing) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables (MONGODB_HOSTS, REDIS_HOST, REDIS_SENTINELS, DATA_HOST, METADATA_HOST, PFSD_HOST, CRR_METRICS_HOST, WE_OPERATOR_HOST) and config.json (vaultd.host, bucketd.bootstrap, backbeat.host). This is environment-variable-based endpoint configuration without dynamic service discovery. Redis Sentinel provides service discovery for Redis HA specifically. Kubernetes service DNS may provide discovery in production but is not defined here. |
| **Gap** | No dynamic service discovery. All service endpoints are statically configured via environment variables. Changes require container restart or config reload. |
| **Recommendation** | Leverage Kubernetes service DNS (already likely in use given K8s deployment) and document the service discovery pattern. For AWS-managed services, use VPC endpoints with DNS. Consider AWS Cloud Map for cross-cluster service discovery if decomposing into microservices. |
| **Evidence** | docker-entrypoint.sh (MONGODB_HOSTS, REDIS_HOST, DATA_HOST, METADATA_HOST, etc.), config.json (vaultd, bucketd, backbeat, workflowEngineOperator host/port) |

---

### Data Platform Modernization (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application IS an S3-compatible object storage server — it stores unstructured data by design. It supports multiple storage backends including AWS S3, local filesystem, Scality RING (sproxyd), and in-memory. Data is stored in S3-compatible format with full object lifecycle support. However, no parsing pipeline (Textract, Tika) exists for stored content — the server stores and retrieves objects without content analysis. |
| **Gap** | No automated parsing or content extraction pipeline for stored objects. The server stores unstructured data but does not analyze content. |
| **Recommendation** | If content analysis is needed, integrate Amazon Textract or S3 Object Lambda for on-read content extraction. For the core storage use case, the current architecture is appropriate — content parsing should be a downstream consumer concern, not a storage server responsibility. |
| **Evidence** | lib/data/wrapper.js (multi-backend storage), locationConfig.json (19 storage locations including AWS S3), lib/api/objectPut.js, lib/api/objectGet.js |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a well-structured data access layer using wrapper pattern: lib/metadata/wrapper.js (metadata access), lib/data/wrapper.js (data/object storage access), lib/kms/wrapper.js (key management). These wrappers abstract the underlying backend (MongoDB vs LevelDB for metadata, filesystem vs S3 vs Azure vs GCP for data). The wrapper pattern provides a unified interface regardless of backend. API handlers access data exclusively through these wrappers. |
| **Gap** | While the wrapper pattern is consistent, some utility modules access Redis directly for caching and rate limiting (lib/api/apiUtils/rateLimit/client.js) without going through a centralized cache abstraction. Minor inconsistency in cache access patterns. |
| **Recommendation** | Maintain the wrapper pattern during decomposition. Consider a unified cache abstraction wrapper (similar to the data and metadata wrappers) for Redis access to maintain consistency. This is a minor gap. |
| **Evidence** | lib/metadata/wrapper.js, lib/data/wrapper.js, lib/kms/wrapper.js, lib/api/apiUtils/rateLimit/client.js (direct Redis access) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The MongoDB Node.js driver version is pinned in package.json (^6.11.0), which is compatible with MongoDB 6.x and 7.x servers. However, no IaC pins the actual MongoDB server engine version — the CI docker-compose uses a custom MongoDB image (.github/docker/mongodb/Dockerfile) without visible version pinning. Redis version is not pinned anywhere. No documented version-update procedure exists. |
| **Gap** | Database server engine versions are not explicitly pinned in infrastructure configuration. Only the client driver version is pinned. No documented version update procedure covering downtime, rollback, or risk. |
| **Recommendation** | Pin MongoDB and Redis server versions in IaC (when created). Document a version-update procedure. When migrating to managed services (DocumentDB, ElastiCache), engine versions are managed by AWS with controlled upgrade windows. |
| **Evidence** | package.json (mongodb ^6.11.0), .github/docker/mongodb/Dockerfile, .github/docker/docker-compose.yaml |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic is in the application layer (Node.js). MongoDB is used with native queries through the driver — no server-side JavaScript functions or aggregation pipelines that would constitute stored procedure equivalents. The data model is document-based with no schema-level complexity beyond standard MongoDB collections. |
| **Gap** | Minor: Some MongoDB-specific query patterns (e.g., compound indexes, specific query operators) may need adjustment when migrating to DocumentDB or DynamoDB, but there are no stored procedures or triggers. |
| **Recommendation** | When migrating to DocumentDB, verify that MongoDB query patterns used are supported (DocumentDB has some compatibility limitations with advanced aggregation features). For DynamoDB migration, data access patterns will need redesign from document queries to single-table design. |
| **Evidence** | No .sql files, no CREATE PROCEDURE/TRIGGER/FUNCTION, lib/metadata/wrapper.js (standard MongoDB driver operations) |

---

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application-level code only (no IaC provisioning AWS resources; `has_iac_provisioning_aws_resources=false`). CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. The application does implement S3 server access logging (lib/utilities/serverAccessLogger.js, configurable via config.json serverAccessLogs section) which provides request-level audit at the application layer. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No aws_cloudtrail or account-level IaC. lib/utilities/serverAccessLogger.js provides application-level request logging. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application implements comprehensive server-side encryption (SSE) with multiple KMS backends: in-memory, file-based, Scality KMS, KMIP (enterprise key management), and AWS KMS. The KMS wrapper (lib/kms/wrapper.js) provides a unified encryption interface. AWS KMS integration is configured in config.json (kmsAWS section with region, endpoint, credentials). SSE-S3, SSE-KMS, and SSE-C are all supported per the S3 protocol. Default encryption per account is supported (defaultEncryptionKeyPerAccount: true). |
| **Gap** | The KMS configuration in config.json contains placeholder credentials ("ak": "tbd", "sk": "tbd") for the AWS KMS backend. While these are sample/dev values, production key management configuration is not visible. No evidence of KMS key rotation policy. |
| **Recommendation** | When deploying to AWS: use AWS KMS with customer-managed keys (CMK), configure automatic key rotation, and ensure the KMS key policy follows least privilege. Remove placeholder credentials from config files and use IAM roles for KMS access. |
| **Evidence** | lib/kms/wrapper.js (5 KMS backends), config.json (kmsAWS section, kmip section, defaultEncryptionKeyPerAccount), lib/kms/common.js |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application implements AWS Signature V4 authentication for all S3 API requests, including streaming V4 authentication (lib/auth/streamingV4/V4Transform.js). Authentication is handled through Vault integration (lib/auth/vault.js) which connects to Scality Vault or uses an in-memory backend for development. All API requests require valid AWS credentials (access key + secret key + signature). Health check endpoints are protected by IP allowlist (config.json healthChecks.allowFrom). |
| **Gap** | Authentication is S3-specific (AWS Signature V4) rather than modern OAuth2/JWT. While appropriate for S3 protocol compatibility, internal/management APIs may not have the same auth rigor. The in-memory auth backend (conf/authdata.json) contains sample credentials for development. |
| **Recommendation** | For production: ensure Vault integration is used (not in-memory auth). For any non-S3 internal APIs, add OAuth2/JWT authentication. The S3 SigV4 authentication is appropriate and well-implemented for the S3 protocol. |
| **Evidence** | lib/auth/vault.js, lib/auth/streamingV4/V4Transform.js, conf/authdata.json (sample dev credentials), config.json (vaultd, healthChecks.allowFrom) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses Scality Vault as its identity provider (lib/auth/vault.js, config.json vaultd section). Vault manages IAM-style accounts with access keys and policies. While Vault acts as a centralized IdP for the Scality/Zenko ecosystem, it is not a standard external IdP (not Cognito, Okta, or OIDC/SAML federation). The in-memory backend (conf/authdata.json) is a standalone auth system for development. No SSO or OIDC federation is configured. |
| **Gap** | Application uses a proprietary IdP (Scality Vault) rather than a standard centralized identity provider with federation capabilities. No OIDC/SAML integration for SSO. |
| **Recommendation** | When deploying to AWS: integrate with Amazon Cognito for user identity management, or configure OIDC federation between Scality Vault and AWS IAM. For management plane access, integrate with AWS IAM Identity Center (SSO). |
| **Evidence** | lib/auth/vault.js, config.json (vaultd.host, vaultd.port), conf/authdata.json (standalone auth data), package.json (vaultclient dependency) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets management uses multiple approaches: Docker secrets (/run/secrets/s3-credentials referenced in entrypoint), GitHub Secrets for CI workflows (Azure, AWS, GCP keys), and environment variables for runtime secrets (MONGODB_HOSTS, REDIS_HOST). The config.json contains placeholder credentials ("ak": "tbd", "sk": "tbd" for KMS). The conf/authdata.json contains sample access keys and secrets ("verySecretKey1") but these are clearly development-only values. No AWS Secrets Manager, HashiCorp Vault (for secrets, distinct from Scality Vault for auth), or rotation configuration found. |
| **Gap** | No dedicated secrets management service with rotation. Production credentials are likely in environment variables without encryption or rotation. Sample credentials exist in version-controlled files (development-only but still a hygiene concern). |
| **Recommendation** | Adopt AWS Secrets Manager for all production credentials (MongoDB connection strings, Redis auth, KMS keys, external backend credentials). Configure automatic rotation for database credentials. Remove placeholder credentials from config.json. Use IAM roles instead of access key/secret key pairs where possible. |
| **Evidence** | config.json (kmsAWS.ak/sk placeholders), conf/authdata.json (sample keys), docker-entrypoint.sh (env var based secrets), .github/workflows/tests.yaml (GitHub Secrets), .github/docker/creds.env |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The main Dockerfile uses a slim base image (node:22.14.0-bookworm-slim) which reduces attack surface. The multi-stage build separates build dependencies from the production image. However, no vulnerability scanning of the container image is configured in CI (no Trivy, Snyk container, or ECR scanning). No evidence of regular base image updates or security hardening beyond the slim base. The legacy DockerfileMem uses node:6-slim (extremely outdated, end-of-life). |
| **Gap** | No container image vulnerability scanning in CI/CD. No hardened base image (not CIS-benchmarked, not Bottlerocket). Legacy Dockerfile uses EOL Node.js 6. No evidence of regular patching cadence. |
| **Recommendation** | Add container image scanning to CI (Trivy or Snyk in GitHub Actions). Remove or update DockerfileMem (node:6 is EOL). Consider using Bottlerocket or a hardened base image for production. Configure ECR image scanning when using AWS container registry. |
| **Evidence** | Dockerfile (node:22.14.0-bookworm-slim, multi-stage), DockerfileMem (node:6-slim — EOL), no Trivy/Snyk container scanning in .github/workflows/ |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CodeQL (SAST) is configured for JavaScript, Python, and Ruby in .github/workflows/codeql.yaml. Dependency vulnerability scanning is configured via .github/workflows/dependency-review.yaml (actions/dependency-review-action@v4 on PRs). These provide SAST and dependency scanning coverage. However, no container scanning is configured, and there is no explicit blocking gate on critical findings (CodeQL results are informational rather than pipeline-blocking). |
| **Gap** | No container image scanning. No explicit security gate that blocks merges on critical findings. DAST (Dynamic Application Security Testing) is not configured. |
| **Recommendation** | Add container image scanning (Trivy) to the CI pipeline. Configure CodeQL to block PRs on critical/high severity findings. Consider adding DAST scanning for the S3 API endpoints in the functional test stage. |
| **Evidence** | .github/workflows/codeql.yaml (CodeQL SAST for JS/Python/Ruby), .github/workflows/dependency-review.yaml (dependency vulnerability review) |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, X-Ray agent, Jaeger client, or trace ID propagation found in the codebase or dependencies. Request correlation within the application uses werelogs' request-scoped logging (log entries include request IDs), but this does not propagate trace context across service boundaries (to MongoDB, Redis, Vault, Backbeat, or downstream storage backends). |
| **Gap** | No distributed tracing. Debugging request flows across service boundaries (CloudServer → MongoDB, CloudServer → Vault, CloudServer → Backbeat, CloudServer → external backends) requires manual log correlation. |
| **Recommendation** | Instrument with OpenTelemetry SDK for Node.js (auto-instrumentation covers HTTP, MongoDB, Redis). Export traces to AWS X-Ray via the OTLP exporter. Propagate trace context (W3C traceparent header) to downstream services. This is a high-impact, moderate-effort improvement. |
| **Evidence** | package.json (no opentelemetry, x-ray, or jaeger dependencies), lib/utilities/logger.js (request-scoped logging only), no trace propagation headers in HTTP client calls |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No formal SLO definitions exist. However, Prometheus alerting rules in monitoring/alerts.yaml define operational thresholds that function as informal SLO-adjacent signals: error rate thresholds (3% warning, 5% critical), listing latency (300ms warning, 500ms critical), delete latency (500ms warning, 1s critical), endpoint availability (<100% degraded, <50% critical). These thresholds indicate operational expectations but are not formalized as SLO/SLI definitions with error budgets. |
| **Gap** | Operational thresholds exist as alert rules but are not formalized as SLOs with error budgets, burn-rate alerting, or SLO dashboards. No documentation of acceptable service levels or customer-facing guarantees. |
| **Recommendation** | Formalize the existing alert thresholds as SLO definitions: availability SLO (99.9% based on endpoint health), latency SLO (p99 < 500ms for listings, p99 < 1s for deletes), error rate SLO (< 3% 5xx). Implement error budget tracking and burn-rate alerting. Consider OpenSLO format for machine-readable SLO definitions. |
| **Evidence** | monitoring/alerts.yaml (threshold-based alerts for error rates, latency, availability), no formal SLO definitions or error budget tracking |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application publishes business-relevant metrics beyond infrastructure metrics: s3_cloudserver_buckets_count (total buckets), s3_cloudserver_objects_count (total objects), s3_cloudserver_ingested_objects_count (ingested objects), s3_cloudserver_ingested_bytes (data ingested), s3_cloudserver_quota_* metrics (quota evaluation, availability, counts). The UTAPI (Utilization API) subsystem provides per-account and per-bucket usage metrics. A Grafana dashboard (monitoring/dashboard.json) visualizes these metrics. |
| **Gap** | Business metrics exist for storage operations (object counts, bytes ingested, quotas) but lack correlation to business outcomes (e.g., request success rate by customer, data growth trends, SLA compliance rates). No custom dashboards for business KPIs beyond operational metrics. |
| **Recommendation** | Extend metrics to include per-customer/per-account request rates, storage growth trends, and SLA compliance tracking. Leverage the existing UTAPI infrastructure to build business outcome dashboards. |
| **Evidence** | lib/utilities/monitoringHandler.js (business metrics: buckets_count, objects_count, ingested_bytes, quota metrics), monitoring/dashboard.json (Grafana dashboard), lib/utapi/ |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Static threshold alerting is configured in monitoring/alerts.yaml with multi-level severity (warning + critical) for: endpoint availability (sum(up) < replicas), error rates (> 3% / > 5%), listing latency (> 300ms / > 500ms), delete latency (> 500ms / > 1s), quota metrics availability. The alerting covers key operational dimensions with appropriate warning-to-critical escalation. However, no anomaly detection (CloudWatch anomaly detection, Prometheus anomaly detection plugins) is configured — all thresholds are static. |
| **Gap** | All alerting uses static thresholds. No anomaly detection for gradual degradation, seasonal patterns, or novel failure modes. Static thresholds may miss slow degradation or generate false positives during traffic pattern changes. |
| **Recommendation** | Add CloudWatch anomaly detection bands for key metrics (request rate, latency percentiles, error rate). Consider Prometheus-based anomaly detection (z-score alerting on rate changes) for the existing metrics stack. Anomaly detection is particularly valuable for the object count and ingestion rate metrics. |
| **Evidence** | monitoring/alerts.yaml (9 alert rules with static thresholds, warning+critical severity levels) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No deployed workload configuration found in this repo. The repository contains source code and Docker image build definitions, but no Kubernetes Deployment manifests, Helm charts, ArgoCD configurations, or deployment strategies (canary, blue/green, rolling). Deployment orchestration is managed in a separate repository (evidenced by monitoring/alerts.yaml referencing Kubernetes namespace and service names that are not defined here). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No Helm charts, no Kubernetes manifests, no ArgoCD/Flux configs. Deployment managed externally. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Extensive functional/integration tests exist and run in CI: AWS SDK-based tests (tests/functional/aws-node-sdk/), multi-backend tests (tests/multipleBackend/), MongoDB metadata tests (tests/functional/metadata/), KMIP encryption tests (tests/functional/kmip/), Python boto tests (tests/functional/boto/), Java JAWS tests (tests/functional/jaws/), Ruby fog tests, health check tests. Tests run against real services (MongoDB, Redis, Ceph, sproxyd) in Docker Compose. Coverage target: 80% patch. |
| **Gap** | No contract tests between CloudServer and its dependencies (Vault, Backbeat, bucketd). Integration tests cover the S3 API surface well but don't verify integration contracts with external services beyond what's dockerized for CI. |
| **Recommendation** | Add contract tests (Pact or similar) for the Vault, Backbeat, and bucketd interfaces. This becomes critical during microservice decomposition. The existing test infrastructure (Docker Compose with real services) is a strong foundation. |
| **Evidence** | tests/functional/ (224 test files across aws-node-sdk, boto, jaws, fog, raw-node, metadata, kmip), .github/workflows/tests.yaml (multiple-backend, mongo-v0-ft-tests jobs), .github/docker/docker-compose.yaml (test services) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns found. No Systems Manager Automation documents, Lambda-based remediation, or Step Functions for incident workflows. The alerting rules (monitoring/alerts.yaml) fire notifications but there is no automated response to those alerts. No runbook files (markdown, YAML, or JSON) found in the repository. |
| **Gap** | Incident response is entirely ad hoc. No structured runbooks for common incidents (endpoint degradation, high error rates, quota failures). No automated remediation for any alert condition. |
| **Recommendation** | Create runbooks for each alert condition defined in monitoring/alerts.yaml: DataAccessS3EndpointDegraded (pod restart, scaling), SystemErrors (log analysis, rollback), ListingLatency (MongoDB index check, connection pool). Start with Markdown runbooks, then automate with Step Functions or SSM Automation documents. |
| **Evidence** | No runbook files found, monitoring/alerts.yaml (alerting without response), no SSM or remediation automation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | A Grafana dashboard exists (monitoring/dashboard.json) and alerting rules are defined (monitoring/alerts.yaml), but there is no CODEOWNERS file for observability assets, no named alarm owners, no team attribution on alerts, and no SLO definitions tied to specific teams. The monitoring directory exists but has no ownership documentation. |
| **Gap** | Observability assets exist but lack ownership attribution. No CODEOWNERS for monitoring/, no team tags on alerts, no documented escalation paths. |
| **Recommendation** | Add CODEOWNERS entries for the monitoring/ directory. Add team/owner labels to Prometheus alert rules. Document on-call rotation and escalation paths for each alert severity level. |
| **Evidence** | monitoring/dashboard.json (Grafana dashboard), monitoring/alerts.yaml (alerts without owner labels), no CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker image labels are applied in CI (git.repository, git.commit-sha labels in .github/workflows/tests.yaml build step). However, no AWS resource tagging strategy exists (no IaC with tags, no tag enforcement policies). The Kubernetes deployment (managed externally) may have labels/annotations but they are not defined here. No cost allocation tags, environment tags, or ownership tags are visible. |
| **Gap** | No AWS resource tagging strategy. Docker image labels exist but no infrastructure resource tags for cost allocation, ownership, or environment identification. |
| **Recommendation** | When creating IaC: define a tagging standard (Environment, Service, Team, CostCenter) and apply required tags to all resources. Use CDK/Terraform default_tags for consistent application. Configure AWS Config required-tags rule for enforcement. |
| **Evidence** | .github/workflows/tests.yaml (Docker labels: git.repository, git.commit-sha), no IaC with resource tags |

---

## Learning Materials

- **Move to Cloud Native:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Managed Databases:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Modern DevOps:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, INF-Q2, DATA-Q3, OPS-Q1 | Node.js dependencies, engine version, MongoDB driver version |
| `Dockerfile` | APP-Q1, INF-Q1, SEC-Q6 | Multi-stage build, Node.js 22, production image |
| `DockerfileMem` | SEC-Q6 | Legacy image with EOL Node.js 6 |
| `config.json` | INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q9, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, APP-Q6 | Server config: ports, endpoints, MongoDB, Redis, KMS, auth, health checks |
| `docker-entrypoint.sh` | INF-Q2, INF-Q5, INF-Q9, SEC-Q5, APP-Q6 | Environment variable configuration for services |
| `index.js` | APP-Q2 | Main entry point — single process |
| `lib/server.js` | APP-Q2, INF-Q4 | S3Server class — monolith HTTP server |
| `lib/metadata/wrapper.js` | DATA-Q2, DATA-Q4 | Metadata access layer (MongoDB/LevelDB) |
| `lib/data/wrapper.js` | DATA-Q2, DATA-Q1 | Data access layer (multi-backend) |
| `lib/kms/wrapper.js` | SEC-Q2, DATA-Q2 | KMS abstraction (5 backends) |
| `lib/auth/vault.js` | SEC-Q3, SEC-Q4 | Vault-based authentication |
| `lib/auth/streamingV4/V4Transform.js` | SEC-Q3 | AWS Signature V4 streaming auth |
| `lib/utilities/monitoringHandler.js` | OPS-Q3, OPS-Q4 | Prometheus metrics implementation |
| `lib/utilities/logger.js` | OPS-Q1 | Werelogs structured logging |
| `lib/utilities/serverAccessLogger.js` | SEC-Q1 | S3 server access logging |
| `lib/api/apiUtils/rateLimit/client.js` | DATA-Q2 | Direct Redis access for rate limiting |
| `monitoring/alerts.yaml` | INF-Q1, OPS-Q2, OPS-Q4, OPS-Q7, OPS-Q8 | Prometheus alert rules (9 alerts) |
| `monitoring/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q6, OPS-Q9 | CI: lint, unit tests, functional tests, build |
| `.github/workflows/release.yaml` | INF-Q11 | Docker image build and push |
| `.github/workflows/codeql.yaml` | SEC-Q7 | CodeQL SAST scanning |
| `.github/workflows/dependency-review.yaml` | SEC-Q7 | Dependency vulnerability scanning |
| `.github/docker/docker-compose.yaml` | INF-Q1, INF-Q2, OPS-Q6 | CI test stack (MongoDB, Redis, Ceph) |
| `conf/authdata.json` | SEC-Q3, SEC-Q5 | Sample auth data (dev credentials) |
| `locationConfig.json` | DATA-Q1 | 19 storage location definitions |
| `codecov.yml` | OPS-Q6 | Coverage configuration (80% patch target) |
| `tests/functional/` | OPS-Q6 | 224 functional test files |
| `lib/api/` | APP-Q2, APP-Q5 | 70 S3 API handlers |
