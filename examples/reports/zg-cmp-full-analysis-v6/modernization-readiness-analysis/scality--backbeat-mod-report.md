# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | scality--backbeat |
| **Date** | 2026-05-07 |
| **Repo Type** | application |
| **Service Archetype** | event-processor (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, storage, replication |
| **Context** | Scality backend engine for replication, lifecycle, and metadata workflows. |
| **Overall Score** | 2.14 / 4.0 |

**Archetype Justification**: The application's primary function is consuming events from MongoDB oplog and Kafka topics, processing them asynchronously (replication, lifecycle transitions, garbage collection, notifications). Each extension runs as a separate Kafka consumer process with minimal synchronous API surface (health checks and metrics only). This matches the `event-processor` archetype.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 1.64 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.80 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.89 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.14 / 4.0** | **🟠 Needs Work** | **Remediation Required** |

**Scoring Notes:**
- INF: (1+1+4+4+1+1+1+1+1+1+2) / 11 = 18/11 = 1.64
- APP: (3+3+4+2+2) / 5 = 14/5 = 2.80 (APP-Q4 excluded as Not Evaluated)
- DATA: (2+3+2+3) / 4 = 10/4 = 2.50
- SEC: (1+2+2+2+2+2+2) / 7 = 13/7 = 1.86
- OPS: (2+1+3+3+1+3+1+2+1) / 9 = 17/9 = 1.89
- Overall: (1.64 + 2.80 + 2.50 + 1.86 + 1.89) / 5 = 10.69/5 = 2.14

### Classification

**Tier: Remediation Required**

This repo has 7 High findings, 19 Medium findings, 7 Low findings. Rule matched: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. With 7 High findings, this repository has significant modernization work ahead.

`classification_consistency_check`: consistent (V5 Needs Work band [score 2.14, range 1.5–2.4] maps to V6 Remediation Required).

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC definitions found in this repository — all infrastructure is manual or managed externally | Cannot reproduce environments, no disaster recovery automation, manual drift |
| 2 | INF-Q5: Network Security | 1 | No VPC, subnet, security group, or network segmentation definitions in the repository | Cannot verify network isolation; blast radius of failures is unknown |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configuration found | No forensic capability, compliance risk, cannot trace operational actions |
| 4 | OPS-Q2: SLO Definitions | 1 | No formal SLO definitions — alerts exist but no error budgets or SLO tracking | Cannot measure whether the system meets user expectations or is degrading |
| 5 | OPS-Q5: Deployment Strategy | 1 | No canary, blue/green, or staged rollout — Docker images built and pushed directly | Regressions affect all users immediately with no rollback automation |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2; GitHub Actions workflows are present with build and test stages)
- **What it enables:** An agent that triggers deployments, checks build status, monitors test results, and manages release workflows via GitHub Actions API
- **Additional steps:** Formalize the release workflow (currently manual `workflow_dispatch`) and add deployment status APIs
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and tracing partially in place (OPS-Q1 = 2; Prometheus metrics, structured logging via werelogs, health probes per service)
- **What it enables:** An agent that queries Prometheus metrics, correlates alert firings with service health, and suggests root causes for replication/lifecycle degradation
- **Additional steps:** Add distributed tracing (OpenTelemetry) for cross-service correlation; currently metrics are service-local
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (docs/ directory, comprehensive README, inline code documentation)
- **What it enables:** An agent that indexes Backbeat documentation and code comments to answer developer questions about extension architecture, Kafka topic contracts, and configuration
- **Additional steps:** Generate AsyncAPI spec from Kafka topic definitions to provide structured event contract documentation
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with well-defined extension boundaries); does not meet < 3 threshold |
| 2 | Move to Containers | Not Triggered | — | — | Contextual guard: Dockerfile exists, application is already containerized and deployed via container orchestration |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 3 (minimal stored procedures); no commercial database engines detected (MongoDB, Redis are open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed in containers); DATA-Q3 = 2 (engine versions not pinned in IaC) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (archetype-calibrated for event-processor — messaging architecture is correct); primary trigger threshold not met. Self-managed Kafka is captured under Move to Managed Databases pathway (INF-Q2). |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 3 (integration tests exist but partial) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- MongoDB runs self-managed (Docker containers in CI; production deployment model not defined in this repo)
- Redis runs self-managed (standalone or Sentinel mode configured via environment variables)
- No database engine version pinning in IaC (no IaC exists)
- No automated backup, failover, or scaling configuration visible

**Recommended Migration Targets** (respecting preferences: prefer EKS, Aurora, DynamoDB):
- **MongoDB → Amazon DocumentDB**: Compatible with MongoDB wire protocol; provides automated backups, scaling, and Multi-AZ. Alternatively, MongoDB Atlas on AWS if full MongoDB compatibility is required.
- **Redis → Amazon ElastiCache for Redis or MemoryDB**: Provides automated failover (Multi-AZ), backup, and scaling. MemoryDB for durability requirements.
- **Apache Kafka → Amazon MSK**: Managed Kafka eliminates cluster management, patching, and scaling. MSK Serverless provides automatic capacity; MSK Provisioned provides more control. KRaft mode eliminates ZooKeeper dependency.
- **ZooKeeper → Eliminated**: Modern Kafka (MSK with KRaft) removes ZooKeeper dependency. Coordination can move to DynamoDB or native Kafka features.

**Representative AWS Services:** DocumentDB, ElastiCache, MemoryDB, Amazon MSK, Amazon MSK Serverless

**Migration Approach:**
1. Stand up managed database services alongside self-managed instances
2. Migrate connection strings via environment variables (already externalized via `docker-entrypoint.sh`)
3. Validate with functional test suite (existing Mocha/functional tests cover database interactions)
4. Cut over production traffic

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- No Infrastructure as Code in this repository (INF-Q10 = 1)
- CI/CD exists for build and test (GitHub Actions) but no deployment automation (INF-Q11 = 2)
- No deployment strategy — images are built and pushed to GHCR with no canary/blue-green rollout (OPS-Q5 = 1)
- Functional tests exist but are not comprehensive across all workflows (OPS-Q6 = 3)

**Recommended DevOps Improvements** (respecting preferences: prefer EKS):
1. **IaC Adoption**: Define infrastructure using Terraform or CDK — EKS cluster, MSK, DocumentDB, ElastiCache, networking, IAM roles
2. **Deployment Pipeline**: Add deployment stages to GitHub Actions — deploy to EKS via Helm charts with ArgoCD or Flux for GitOps
3. **Deployment Strategy**: Implement canary deployments using Argo Rollouts or EKS-native progressive delivery
4. **Environment Parity**: Use IaC to create staging environments matching production

**Representative AWS Services:** EKS, CodePipeline, CodeBuild, CloudFormation/CDK, ECR

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute resources defined in this repository. The application is containerized (Dockerfile present) but no ECS, EKS, Lambda, or Fargate resource definitions exist. Production compute model is not defined here — infrastructure is managed externally. The Docker image is pushed to GHCR but deployment targets are not specified. |
| **Gap** | No managed compute orchestration defined. The repository contains only the container image definition, with no evidence of how it is deployed to managed compute services. |
| **Recommendation** | Define EKS deployment manifests (Helm charts or Kubernetes manifests) within this repository or link to the external deployment repository. Target EKS with Fargate profiles for the event-processing workloads that benefit from per-pod scaling. |
| **Evidence** | `Dockerfile`, `images/federation/Dockerfile`, `.github/workflows/docker-build.yaml` — images built and pushed but no deployment target defined |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. MongoDB, Redis, ZooKeeper, and Kafka are configured via connection strings in environment variables pointing to self-hosted instances. Docker Compose in CI uses bare MongoDB/Redis/ZooKeeper/Kafka containers. No managed database resources (RDS, DocumentDB, ElastiCache, MSK) are defined. |
| **Gap** | All data stores self-managed with no automated failover, backup, or scaling configuration visible. |
| **Recommendation** | Migrate to managed services: MongoDB → Amazon DocumentDB, Redis → ElastiCache/MemoryDB, Kafka → Amazon MSK. Connection strings are already externalized via environment variables, enabling migration without code changes. |
| **Evidence** | `conf/config.json` (localhost connections), `docker-entrypoint.sh` (env var overrides for MONGODB_HOSTS, REDIS_HOST, KAFKA_HOSTS, ZOOKEEPER_CONNECTION_STRING), `.github/dockerfiles/ft/docker-compose.yaml` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is an `event-processor`. Event pipeline uses Kafka-based orchestration with structured consumer patterns (BackbeatConsumer with TaskScheduler, OffsetLedger, circuit breaker). The lifecycle extension has a dedicated conductor service (`extensions/lifecycle/conductor/service.js`) that coordinates bucket and object processing workflows. ZooKeeper handles leader election and partition provisioning. While not a managed orchestration service like Step Functions, the orchestration is structured and appropriate for the event-processing archetype. |
| **Gap** | N/A — orchestration is appropriate for this archetype. |
| **Recommendation** | The current Kafka-based orchestration with conductor pattern is architecturally sound for an event-processor. No change needed. For future complex multi-step workflows (e.g., cold archive restore with approval), consider AWS Step Functions. |
| **Evidence** | `extensions/lifecycle/conductor/service.js`, `lib/BackbeatConsumer.js` (TaskScheduler, circuit breaker), `lib/clients/ZookeeperManager.js` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is an `event-processor`. The primary input is async (Kafka topics: backbeat-replication, backbeat-lifecycle-*, backbeat-gc, backbeat-oplog, etc.). Structured consumer patterns are in place with `BackbeatConsumer` providing flow control, circuit breaking, and ordered processing. MongoDB Change Streams feed the OplogPopulator for real-time event detection. The messaging architecture is correct and mature for this archetype. However, Kafka is self-managed rather than a managed service — this is evaluated under INF-Q2 and the Managed Analytics pathway rather than penalizing the messaging architecture itself. |
| **Gap** | N/A — async messaging architecture is correct for this archetype. The self-managed nature of Kafka is captured in INF-Q2. |
| **Recommendation** | The event-driven architecture using Kafka is the correct design for this event-processor. Migrating to Amazon MSK (managed Kafka) would reduce operational burden without changing the architecture. |
| **Evidence** | `lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js`, `conf/config.json` (15+ Kafka topics), `lib/wrappers/ChangeStream.js` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation definitions found in this repository. The health check endpoint is restricted to loopback addresses (`127.0.0.1/8`, `::1`) by default via `server.healthChecks.allowFrom` in config — this is application-level ACL, not network-level security. No evidence of VPC endpoints, PrivateLink, or service mesh configuration. |
| **Gap** | No network security definitions. Infrastructure managed externally means network posture cannot be verified from this repository alone. |
| **Recommendation** | Define network security in IaC: deploy services in private subnets with security groups restricting traffic to necessary ports only. Use VPC endpoints for AWS service access (MSK, DocumentDB, ElastiCache). Consider service mesh (Istio or App Mesh) for mTLS between services. |
| **Evidence** | `conf/config.json` (healthChecks.allowFrom), absence of any network/VPC definitions in the repository |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or load balancer configuration found. The API server listens on port 8900 directly. Routes are defined in `lib/api/routes.js` with no throttling, authentication middleware, or request validation at the entry point level. The service exposes its HTTP API directly. |
| **Gap** | Services exposed directly with no gateway or load balancer providing throttling, auth, or request validation. |
| **Recommendation** | Place an API Gateway or ALB in front of the Backbeat API server. For internal-only APIs (which this appears to be), use an internal ALB with health checks and routing rules. For external exposure, use API Gateway with throttling and IAM/Cognito auth. |
| **Evidence** | `lib/api/routes.js`, `lib/api/BackbeatServer.js`, `conf/config.json` (server.port: 8900) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No ASG, ECS service scaling, HPA (Horizontal Pod Autoscaler), or Lambda concurrency configuration. The Docker image is built and pushed but no scaling policies are defined for any compute or data layer. |
| **Gap** | All capacity is statically provisioned. No auto-scaling for compute or data layers. |
| **Recommendation** | Define HPA (Horizontal Pod Autoscaler) policies for EKS workloads based on Kafka consumer lag metrics. Configure auto-scaling for DocumentDB read replicas and ElastiCache shards based on connection count and memory utilization. |
| **Evidence** | Absence of any scaling configuration in the repository; no HPA, ASG, or application auto-scaling definitions |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, backup retention periods, PITR settings, or S3 versioning configuration. MongoDB, Redis, and Kafka data persistence depends entirely on external infrastructure configuration not present in this repository. |
| **Gap** | No backup configuration. Data recovery capability cannot be verified. |
| **Recommendation** | When migrating to managed services: enable automated backups on DocumentDB (with PITR), enable Redis snapshots on ElastiCache, configure MSK log retention. Define backup plans in IaC with tested restore procedures. |
| **Evidence** | Absence of any backup configuration in the repository |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Multi-AZ configuration found. MongoDB is configured with replica set support (`MONGODB_RS` env var) and Redis supports Sentinel mode (`REDIS_SENTINELS` env var), which indicates awareness of HA — but the actual multi-AZ deployment topology is not defined in this repository. No AZ-spread configuration for compute or data stores. |
| **Gap** | No evidence of multi-AZ deployment. HA mechanisms exist at application level (replica sets, Sentinel) but AZ distribution is not configured. |
| **Recommendation** | Deploy across 2+ AZs: EKS node groups spanning multiple AZs, DocumentDB Multi-AZ, ElastiCache Multi-AZ, MSK across 3 AZs. Define these in IaC. |
| **Evidence** | `docker-entrypoint.sh` (MONGODB_RS, REDIS_SENTINELS env vars indicate HA awareness), absence of AZ configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code found in this repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files. All infrastructure (compute, networking, databases, messaging) is either manually created or managed in a separate repository not linked here. |
| **Gap** | 0% IaC coverage in this repository. Infrastructure changes are not reproducible from this codebase. |
| **Recommendation** | Create IaC definitions (Terraform or CDK preferred based on team skills) covering: EKS cluster, Amazon MSK, DocumentDB, ElastiCache, VPC/networking, IAM roles, monitoring (CloudWatch alarms). Consider co-locating IaC with the application or establishing a clear cross-repository reference. |
| **Evidence** | Complete absence of .tf, .cfn.yaml, cdk.json, Chart.yaml, kustomization.yaml files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD exists for build and test via GitHub Actions (5 workflows covering lint, unit tests, functional tests, Docker build, alerts testing). Docker images are built and pushed to GHCR. However, there is no deployment automation — the release workflow is manual (`workflow_dispatch`) and only creates a GitHub release + pushes a tagged image. No deploy stage, no environment promotion, no IaC deployment pipeline. |
| **Gap** | Build is automated but deployment is manual. No automated deployment pipeline for application or infrastructure. |
| **Recommendation** | Add deployment stages to the GitHub Actions pipeline: deploy to staging EKS cluster, run smoke tests, promote to production with canary rollout. Add IaC deployment pipeline (terraform plan/apply or CDK deploy) triggered on infrastructure changes. |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/docker-build.yaml`, `.github/workflows/release.yaml` (manual workflow_dispatch) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary language is JavaScript (Node.js 22) with AWS SDK v3 (`@aws-sdk/client-s3` ^3.921.0, `@aws-sdk/client-iam`, `@aws-sdk/client-sts`). Secondary component is Go 1.15 (bucket-scanner). Node.js 22 is current and cloud-native-ready with first-class AWS SDK support. However, the Go component is severely outdated (Go 1.15 is EOL, current is 1.22+), and the Dockerfile still suppresses AWS SDK v2 maintenance mode warnings (`AWS_SDK_JS_SUPPRESS_MAINTENANCE_MODE_MESSAGE=1`), suggesting some v2 usage remains alongside v3. No TypeScript source despite TypeScript being a dev dependency. |
| **Gap** | Go 1.15 is end-of-life. Residual AWS SDK v2 usage exists alongside v3. No TypeScript adoption for type safety. |
| **Recommendation** | Upgrade bucket-scanner Go component to Go 1.22+. Complete AWS SDK v2 → v3 migration and remove the suppression flag. Consider gradual TypeScript adoption for new modules. |
| **Evidence** | `package.json` (node >=20, @aws-sdk/* ^3.921.0, AWS_SDK_JS_SUPPRESS_MAINTENANCE_MODE_MESSAGE in Dockerfile), `bucket-scanner/go.mod` (go 1.15) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Modular monolith with well-defined extension boundaries deployed as multiple independent processes. Each extension (replication, lifecycle, gc, notification, ingestion, oplogPopulator, mongoProcessor) runs as a separate container process with its own entry point. Extensions share a core library (`lib/`) but have clear interfaces (`index.js` exports: name, configValidator, queuePopulatorExtension). The lifecycle extension further decomposes into conductor, bucketProcessor, and objectProcessor sub-services. Kafka topics provide isolation between extensions. |
| **Gap** | While extensions are well-isolated at the process level, they share a single codebase and Docker image. A change to any extension requires rebuilding the entire image. Shared database access patterns exist (all extensions access the same MongoDB/Redis instances). |
| **Recommendation** | The current modular monolith deployed as microservices is architecturally sound. Consider splitting into per-extension Docker images if independent deployment cadence becomes important. The shared library pattern via npm packages would support this. |
| **Evidence** | `extensions/*/index.js` (7 extensions with standard interface), `bin/*.js` (separate entry points), `Dockerfile` (single image), `codecov.yml` (per-component coverage tracking) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is an `event-processor`. Primary input is async (Kafka topics via BackbeatConsumer). All inter-extension communication flows through Kafka topics — no synchronous coupling between extensions. MongoDB Change Streams provide async event detection. The only synchronous surface is the administrative API (healthcheck, metrics, pause/resume) which is minimal and correct for operational control. This is the correct design for an event-processor archetype. |
| **Gap** | N/A — async communication dominates appropriately for this archetype. |
| **Recommendation** | The async-first architecture is correct. No changes needed to communication patterns. |
| **Evidence** | `lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js`, `lib/wrappers/ChangeStream.js`, `lib/api/routes.js` (minimal sync API) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is an `event-processor`. Event handlers are async by design — each Kafka message is processed independently with the BackbeatConsumer providing flow control, circuit breaking, and ordered processing via TaskScheduler. Long-running operations (e.g., large object replication) are handled within the async consumer framework with configurable concurrency and retry logic. There is no synchronous caller waiting for completion. This question is not applicable by design for this archetype. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/BackbeatConsumer.js` (async processing with circuit breaker and flow control) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API routes are defined with `/_/` prefix paths but no versioning strategy. All endpoints are unversioned (e.g., `/_/metrics/crr/<location>/backlog`, `/_/crr/pause/<location>`). No `/v1/` or `/v2/` path segments, no version headers, no versioning documentation. The `/_/` prefix is a namespace convention, not a version indicator. |
| **Gap** | No API versioning — breaking changes would affect all consumers simultaneously. |
| **Recommendation** | Introduce API versioning using URL path prefixes (e.g., `/_/v1/metrics/crr/...`). Given this is an internal API, even a simple major-version prefix would enable safe evolution. Document the versioning policy. |
| **Evidence** | `lib/api/routes.js` (all routes use `/_/` prefix with no version segment) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables (`CLOUDSERVER_HOST`, `CLOUDSERVER_PORT`, `KAFKA_HOSTS`, `MONGODB_HOSTS`, `REDIS_HOST`, `ZOOKEEPER_CONNECTION_STRING`). This is a step above hardcoded endpoints but there is no dynamic service discovery mechanism. ZooKeeper provides some coordination but is not used as a service registry. No Consul, AWS Cloud Map, Kubernetes DNS, or service mesh detected. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. Adding or removing service instances requires configuration changes and restarts. |
| **Recommendation** | When deploying to EKS, leverage Kubernetes DNS for service discovery. Use AWS Cloud Map for cross-cluster discovery. For Kafka and databases, managed services (MSK, DocumentDB) provide their own discovery endpoints. |
| **Evidence** | `docker-entrypoint.sh` (env vars for all service endpoints), `conf/config.json` (static endpoint configuration) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application processes S3 objects (the core purpose is S3 replication, lifecycle, and metadata management) using S3-compatible storage via CloudServer. However, operational data (logs, metrics, dashboards) is stored locally or in monitoring systems rather than S3. Grafana dashboards are packaged as OCI artifacts rather than stored in managed object storage. No S3 bucket definitions or object parsing pipelines found for the application's own operational data. |
| **Gap** | Operational artifacts (dashboards, policies, logs) are distributed via OCI artifacts rather than managed object storage with parsing capabilities. |
| **Recommendation** | Store operational artifacts (Grafana dashboards, IAM policies, alert rules) in S3 with versioning. The application already integrates with S3 for its primary function — extend this to operational data management. |
| **Evidence** | `.github/workflows/docker-build.yaml` (ORAS push of dashboards/policies as OCI artifacts), `monitoring/` directory, `policies/` directory |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Data access is mostly centralized through dedicated client wrappers: `ClientManager` for S3/metadata access, `VaultClientCache` for authentication, `ZookeeperManager` for coordination, and BackbeatConsumer/Producer for Kafka. Redis access uses a shared `ioredis` client configured centrally. MongoDB access is primarily through the ChangeStream wrapper and centralized config. However, some extensions access databases directly without going through the central client layer. |
| **Gap** | Mostly centralized with some direct access in auxiliary code paths. Not all database interactions go through the formal client layer. |
| **Recommendation** | Continue consolidating data access through the client manager pattern. Ensure all MongoDB queries go through a central data access layer that can be instrumented for tracing and metrics. |
| **Evidence** | `lib/clients/ClientManager.js`, `lib/clients/VaultClientCache.js`, `lib/clients/ZookeeperManager.js`, `lib/wrappers/ChangeStream.js` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database engine versions are partially pinned in CI configurations but not in production IaC (no IaC exists). CI uses `zookeeper:3.9.4` and `redis:alpine` (implicit latest). MongoDB CI image is custom-built without explicit version pinning. The `mongodb` npm driver is at v6.11.0 (supports MongoDB 4.4–7.0). No production database version pinning or EOL tracking exists. Go component uses `confluent-kafka-go` v1.6.1 which is significantly outdated. |
| **Gap** | Some CI versions pinned, production versions unknown. No documented version-update procedure. |
| **Recommendation** | Pin all database engine versions in IaC when migrating to managed services. Document the supported version matrix (MongoDB 6.x/7.x, Redis 7.x, Kafka 3.x). Establish a version update procedure with downtime windows and rollback plans. |
| **Evidence** | `.github/workflows/tests.yaml` (zookeeper:3.9.4, redis:alpine), `.github/dockerfiles/mongodb/Dockerfile`, `package.json` (mongodb ^6.11.0, ioredis ^5.4.2, node-rdkafka ^2.12.0), `bucket-scanner/go.mod` (confluent-kafka-go v1.6.1) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs detected. The application uses MongoDB with driver-level queries — no server-side JavaScript functions, triggers, or MongoDB-specific aggregation pipelines that would couple logic to the database engine. All business logic is in the application layer (Node.js). The MongoDB oplog is consumed via Change Streams (a supported driver feature) rather than database-side triggers. Minimal schema coupling exists through MongoDB indexes and collection structures. |
| **Gap** | Minor: MongoDB Change Streams create a dependency on MongoDB's replication protocol, which limits portability to other document databases. |
| **Recommendation** | The application layer approach to business logic is correct. If migrating from MongoDB to DocumentDB, verify Change Stream compatibility (DocumentDB supports Change Streams with some limitations). Consider abstracting the change detection mechanism behind an interface for future portability. |
| **Evidence** | `lib/wrappers/ChangeStream.js`, `extensions/oplogPopulator/`, absence of .sql files or stored procedure definitions |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration found. The application has structured logging via `werelogs` for operational events but no audit trail of administrative actions (who paused replication, who changed configuration, who triggered a release). No CloudTrail resources in IaC (no IaC exists). No log file validation or immutable storage configuration. |
| **Gap** | No audit logging. Administrative actions on the system are not tracked in an immutable audit trail. |
| **Recommendation** | Enable CloudTrail for all AWS API calls when deploying on AWS. Add application-level audit logging for administrative API actions (pause/resume, configuration changes) with immutable storage (S3 with Object Lock). |
| **Evidence** | Absence of CloudTrail configuration; `lib/api/routes.js` (administrative endpoints with no audit logging) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No KMS key configuration found. `certFilePaths` in config are empty by default. The application handles S3 objects which may be encrypted at the storage layer, but no encryption-at-rest configuration for the application's own data stores (MongoDB, Redis, Kafka) is defined. TLS configuration paths exist but are empty, suggesting encryption in transit is optional/environment-configured. |
| **Gap** | No encryption at rest configuration for MongoDB, Redis, or Kafka data. Mix of potential encryption (managed by underlying infrastructure) with no explicit configuration. |
| **Recommendation** | When migrating to managed services: enable encryption at rest with customer-managed KMS keys on DocumentDB, ElastiCache, and MSK. Enable encryption in transit (TLS) for all inter-service communication. |
| **Evidence** | `conf/config.json` (empty certFilePaths), `docker-entrypoint.sh` (no encryption env vars), absence of KMS configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The API uses IP-based access control (`healthChecks.allowFrom` restricted to loopback `127.0.0.1/8` and `::1`) rather than token-based authentication. Internal service-to-service communication uses Vault service accounts (service-replication, service-lifecycle, etc.) for S3/metadata operations, but the administrative API itself has no per-request authentication. API key or static credential model — not token-based. |
| **Gap** | No per-request authentication on the administrative API. IP-based ACL is the only protection. |
| **Recommendation** | Add token-based authentication (JWT/OAuth2) to the administrative API endpoints. For internal-only deployment within a private VPC, network isolation may be acceptable, but defense-in-depth recommends per-request auth even internally. |
| **Evidence** | `conf/config.json` (server.healthChecks.allowFrom), `lib/api/BackbeatServer.js`, absence of auth middleware |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application integrates with Scality's Vault service for IAM authentication of service accounts (service-replication, service-lifecycle, service-gc, service-md-ingestion). This provides centralized identity for service-to-service communication. However, no integration with standard IdPs (Cognito, Okta, OIDC/SAML) exists. The Vault integration is proprietary to the Scality ecosystem rather than a standard centralized IdP. |
| **Gap** | Application uses a proprietary Vault implementation (not HashiCorp Vault) rather than standard IdP integration. No OIDC/SAML/Cognito federation. |
| **Recommendation** | When deploying on AWS, integrate with IAM roles for service identity (IRSA on EKS). For human access to administrative APIs, integrate with Cognito or an organizational IdP via OIDC. |
| **Evidence** | `lib/clients/VaultClientCache.js`, `conf/config.json` (vaultAdmin configuration, service auth accounts), `lib/credentials/` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Configuration files contain placeholder/development credentials: `conf/authdata.json` has `accessKey1`/`verySecretKey1`, `conf/config.json` has `myAccessKey`/`myEncryptedSecretKey`, and `conf/locationConfig.json` has `TO_BE_ADDED` placeholders. These are clearly development defaults overridden at runtime via environment variables. Production credentials are injected via env vars (`docker-entrypoint.sh`). No Secrets Manager or HashiCorp Vault (for secrets rotation) integration. No automated rotation. |
| **Gap** | Credentials in version-controlled config files (development defaults). Production credentials in environment variables without rotation. No dedicated secrets management service. |
| **Recommendation** | Remove all credential values from version-controlled config files (replace with empty strings or references). Integrate with AWS Secrets Manager for production credentials with automated rotation. Use IRSA (IAM Roles for Service Accounts) on EKS to eliminate static credentials entirely for AWS services. |
| **Evidence** | `conf/authdata.json` (accessKey1/verySecretKey1), `conf/config.json` (myAccessKey/myEncryptedSecretKey), `conf/locationConfig.json` (TO_BE_ADDED placeholders), `docker-entrypoint.sh` (env var injection) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker image uses `node:22.14.0-bookworm-slim` as base (Debian Bookworm slim is a maintained base). Multi-stage build reduces attack surface. However: no USER directive (container runs as root), no vulnerability scanning integration (no Snyk, Inspector, or Trivy in CI), no hardened base image (not using distroless or Bottlerocket). `dockerize` tool included adds unnecessary attack surface. |
| **Gap** | Container runs as root. No vulnerability scanning. No hardened base image. |
| **Recommendation** | Add a non-root USER directive to the Dockerfile. Integrate container scanning (Trivy or ECR scanning) into the Docker build pipeline. Consider switching to a distroless or hardened Node.js base image. Remove `dockerize` if not needed in production. |
| **Evidence** | `Dockerfile` (no USER directive, dockerize included, node:22.14.0-bookworm-slim base) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ESLint is configured for code quality (`eslint.config.mjs`) and runs in CI. However, no SAST tool (SonarQube, Semgrep, CodeGuru), no dependency vulnerability scanning (no Dependabot, no `npm audit` in pipeline, no Snyk), and no container scanning are configured. The CI pipeline focuses on functional correctness, not security validation. |
| **Gap** | No SAST, no dependency scanning, no container scanning in CI/CD. Only ESLint for code style. |
| **Recommendation** | Add Dependabot or `npm audit --production` to the CI pipeline. Integrate a SAST tool (Semgrep is lightweight and Node.js-aware). Add container image scanning (Trivy) to the Docker build workflow. Configure security gates that block merges on critical findings. |
| **Evidence** | `.github/workflows/tests.yaml` (lint step only), `eslint.config.mjs`, absence of .snyk, dependabot.yml, or security scanning steps |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Basic per-service observability exists via Prometheus metrics (`prom-client`) and structured logging (`werelogs`). Each service exposes metrics at `/_/monitoring/metrics`. However, no distributed tracing is instrumented — no OpenTelemetry, X-Ray, or equivalent. No trace ID propagation across Kafka messages or between services. Debugging cross-service issues (e.g., a replication failure spanning queue populator → producer → consumer → S3) requires correlating logs manually. |
| **Gap** | No distributed tracing. Cross-service request flows cannot be traced end-to-end. |
| **Recommendation** | Instrument OpenTelemetry with trace context propagation via Kafka message headers. Each BackbeatProducer message should carry a trace ID that BackbeatConsumer propagates. Send traces to AWS X-Ray or an OpenTelemetry Collector. |
| **Evidence** | `package.json` (prom-client, no opentelemetry-*), `lib/BackbeatConsumer.js` (no trace propagation), `lib/BackbeatProducer.js` (no trace headers) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No formal SLO definitions found. Prometheus alerts exist with thresholds (RPO > 600s warning, > 900s critical; error rate > 0.1% warning, > 1% critical; latency > 3000s warning, > 6000s critical) — but these are alerting thresholds, not SLO definitions with error budgets. No SLO tracking, no burn rate alerts, no error budget consumption monitoring. |
| **Gap** | No formal SLOs. Alert thresholds exist but are not tied to SLO definitions or error budget tracking. |
| **Recommendation** | Define SLOs for critical user journeys: replication RPO (e.g., 99.9% of objects replicated within 600s), lifecycle processing latency (e.g., 99% of lifecycle actions within 1 hour of rule trigger). Implement error budget tracking with burn rate alerts. |
| **Evidence** | `monitoring/replication/alerts.yaml` (thresholds without SLO framework), `monitoring/lifecycle/alerts.yaml` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Business-relevant metrics are published via Prometheus: replication RPO, replication completions, throughput, backlog size, lifecycle processing rates, ingestion throughput. Grafana dashboards visualize these business outcomes per extension. The API exposes business metrics endpoints (`/_/metrics/crr/<location>/all`). These go beyond infrastructure metrics to track actual business outcomes (objects replicated, lifecycle actions completed). |
| **Gap** | Business metrics exist but are not systematically tagged with SLO targets or business context. Some extensions have better metric coverage than others. |
| **Recommendation** | Formalize the business metrics taxonomy. Ensure all extensions publish consistent metric dimensions. Add business context labels (customer tier, data classification) where applicable. |
| **Evidence** | `monitoring/replication/dashboard.json`, `monitoring/lifecycle/dashboard.json`, `lib/api/routes.js` (metrics endpoints), `monitoring/ingestion/` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive static threshold alerts configured across all extensions: replication (15 alerts including RPO, latency, error rate, backlog growth), lifecycle, notification, oplog-populator, and ingestion. Alerts have warning/critical tiers. Alert rules are tested with dedicated test files (`alerts.test.yaml`). However, these are all static thresholds — no anomaly detection, no dynamic baselines, no composite alarms. |
| **Gap** | Static threshold alerting only. No anomaly detection for gradual degradation or novel failure patterns. |
| **Recommendation** | Add CloudWatch anomaly detection for key metrics (replication RPO, processing latency) when deploying on AWS. Implement composite alarms that correlate multiple signals (e.g., backlog growing + error rate increasing + latency rising). |
| **Evidence** | `monitoring/replication/alerts.yaml`, `monitoring/lifecycle/alerts.yaml`, `monitoring/notification/alerts.yaml`, `monitoring/replication/alerts.test.yaml` |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. Docker images are built and pushed to GHCR via GitHub Actions, but no canary, blue/green, or rolling deployment configuration exists. The release workflow (`release.yaml`) is a manual `workflow_dispatch` that creates a GitHub release and builds a tagged image — no deployment steps follow. No CodeDeploy, Argo Rollouts, Helm canary, or traffic shifting configuration found. |
| **Gap** | Direct-to-production with no staged rollout. No automated deployment, no traffic shifting, no rollback automation. |
| **Recommendation** | Implement canary deployments using Argo Rollouts on EKS. Define progressive delivery with Kafka consumer lag as the health metric — if lag increases after deployment, automatically roll back. Start with rolling deployments with readiness probes as a minimum. |
| **Evidence** | `.github/workflows/release.yaml` (manual workflow_dispatch, no deploy step), `.github/workflows/docker-build.yaml` (push only), absence of deployment configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Functional tests exist covering major workflows: replication, lifecycle, ingestion, notification, oplogPopulator, API routes, and library functions. Tests run in CI with service containers (Redis, ZooKeeper, Kafka, MongoDB). Docker Compose defines a complete test environment. Memory ballooning tests validate resource constraints. However, not all extensions have equal coverage, and the queue-populator integration test uses a separate Docker Compose setup suggesting fragmentation. |
| **Gap** | Integration tests exist for primary workflows but coverage is inconsistent across extensions. Test environments are fragmented (service containers vs Docker Compose). |
| **Recommendation** | Standardize the integration test approach across all extensions. Ensure every extension has functional tests that run in CI. Add contract tests for Kafka message schemas between producer and consumer extensions. |
| **Evidence** | `tests/functional/` (replication, lifecycle, ingestion, notification, oplogPopulator, api, lib), `.github/workflows/tests.yaml` (functional test matrix), `.github/dockerfiles/ft/docker-compose.yaml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated incident response workflows found. No runbooks (markdown or automated), no SSM Automation documents, no Lambda-based remediation, no self-healing patterns beyond the circuit breaker in BackbeatConsumer. The circuit breaker pauses consumption when downstream is unhealthy (a form of self-healing) but there are no broader incident response automations. |
| **Gap** | No runbooks or automated incident response. The circuit breaker provides local self-healing but no system-wide incident automation exists. |
| **Recommendation** | Create runbooks for common incidents: Kafka consumer lag spike, replication RPO breach, MongoDB connection failure, Redis failover. Automate the most common remediation (e.g., scale up consumers when lag exceeds threshold). Implement as SSM Automation documents or Step Functions. |
| **Evidence** | `lib/BackbeatConsumer.js` (circuit breaker — limited self-healing), absence of runbook files, absence of automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Per-extension dashboards and alerts exist (replication, lifecycle, notification, oplog-populator, ingestion, cold-storage), suggesting some ownership structure. Codecov tracks per-component coverage. However, no CODEOWNERS file referencing observability assets, no named alert owners, no team attribution on dashboards. The monitoring infrastructure exists but ownership is implicit rather than explicit. |
| **Gap** | Observability assets exist but have no explicit ownership attribution. No CODEOWNERS for monitoring, no team tags on alerts. |
| **Recommendation** | Add CODEOWNERS entries for `monitoring/` directories. Add team labels to Prometheus alert rules and Grafana dashboards. Define on-call rotation ownership per extension. |
| **Evidence** | `monitoring/` (per-extension structure), `codecov.yml` (per-component flags), absence of CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging found. No IaC exists to tag resources. No `default_tags`, no tagging standard, no AWS Organizations Tag Policies. The Docker images are tagged by git SHA and version but AWS resources are not tagged (because no AWS resources are defined in this repository). |
| **Gap** | No resource tagging governance. When infrastructure is provisioned, there is no tagging standard to apply. |
| **Recommendation** | Define a tagging standard (Environment, Service, Team, CostCenter minimum). Implement as `default_tags` in Terraform provider or CDK aspects when creating IaC. Enforce via Tag Policies in AWS Organizations. |
| **Evidence** | Absence of any tagging configuration; no IaC to apply tags to |

---

## Learning Materials

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
| `Dockerfile` | INF-Q1, APP-Q1, SEC-Q6 | Production container image definition; multi-stage build, Node 22, no USER directive |
| `images/federation/Dockerfile` | INF-Q1 | Federation variant image with supervisord |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline with build, lint, unit, and functional test stages |
| `.github/workflows/docker-build.yaml` | INF-Q1, INF-Q11, OPS-Q5 | Docker build and push pipeline; OCI artifact distribution |
| `.github/workflows/release.yaml` | INF-Q11, OPS-Q5 | Manual release workflow (workflow_dispatch) |
| `conf/config.json` | INF-Q2, INF-Q5, INF-Q6, SEC-Q3, SEC-Q5 | Application configuration with localhost defaults and service auth |
| `conf/authdata.json` | SEC-Q5 | Development credentials (accessKey1/verySecretKey1) |
| `conf/locationConfig.json` | SEC-Q5 | Location config with TO_BE_ADDED credential placeholders |
| `docker-entrypoint.sh` | INF-Q2, INF-Q9, SEC-Q5, APP-Q6 | Runtime configuration via environment variables |
| `lib/api/routes.js` | INF-Q6, APP-Q5, SEC-Q1, SEC-Q3 | API route definitions, no versioning, no auth middleware |
| `lib/BackbeatConsumer.js` | INF-Q3, INF-Q4, APP-Q3, OPS-Q1, OPS-Q7 | Kafka consumer with flow control, circuit breaker, TaskScheduler |
| `lib/BackbeatProducer.js` | INF-Q4, APP-Q3, OPS-Q1 | Kafka producer with compression, delivery reports |
| `lib/wrappers/ChangeStream.js` | INF-Q4, DATA-Q4 | MongoDB Change Stream wrapper with resume token recovery |
| `lib/clients/ClientManager.js` | DATA-Q2 | Centralized S3/metadata client management with credential caching |
| `lib/clients/VaultClientCache.js` | SEC-Q4, DATA-Q2 | Vault authentication client cache |
| `lib/clients/ZookeeperManager.js` | INF-Q3, DATA-Q2 | ZooKeeper coordination client |
| `lib/Config.js` | APP-Q6 | Configuration loader with env var overrides |
| `extensions/lifecycle/conductor/service.js` | INF-Q3 | Lifecycle workflow conductor |
| `extensions/*/index.js` | APP-Q2 | Extension standard interface (7 extensions) |
| `monitoring/replication/alerts.yaml` | OPS-Q2, OPS-Q4 | Prometheus alert rules (15 alerts, warning/critical tiers) |
| `monitoring/lifecycle/alerts.yaml` | OPS-Q2, OPS-Q4 | Lifecycle Prometheus alerts |
| `monitoring/replication/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard for replication metrics |
| `package.json` | APP-Q1, DATA-Q3, OPS-Q1 | Node.js dependencies including AWS SDK v3, mongodb, ioredis, prom-client |
| `bucket-scanner/go.mod` | APP-Q1, DATA-Q3 | Go 1.15 module (outdated) |
| `codecov.yml` | OPS-Q8 | Per-component coverage tracking |
| `eslint.config.mjs` | SEC-Q7 | Code quality linting (not security scanning) |
| `policies/` | SEC-Q1 | IAM policies (minimal vaultadmin:GetAccountInfo only) |
| `.github/dockerfiles/ft/docker-compose.yaml` | INF-Q2, OPS-Q6 | Functional test environment with self-managed services |
