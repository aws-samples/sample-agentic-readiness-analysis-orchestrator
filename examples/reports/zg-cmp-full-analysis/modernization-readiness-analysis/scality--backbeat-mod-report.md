# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | backbeat |
| **Date** | 2025-07-16 |
| **Repo Type** | application |
| **Service Archetype** | event-processor (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, storage, replication |
| **Context** | Scality backend engine for replication, lifecycle, and metadata workflows. |
| **Overall Score** | 1.94 / 4.0 |

**Archetype Justification**: Primary input is Kafka message consumption via BackbeatConsumer (node-rdkafka); HTTP surface is limited to health checks, metrics, and operational control endpoints (pause/resume) on port 8900. No owned persistent state — reads/writes to external MongoDB and S3. Classified as event-processor per decision logic check #1.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.36 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.78 / 4.0 | 🟠 Needs Work |
| **Overall** | **1.94 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code exists — 0% IaC coverage. All infrastructure is provisioned manually or undocumented. | Blocks reproducible environments, disaster recovery, and safe modernization. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q2: Managed Databases | 1 | All databases (MongoDB, Redis) are self-managed with no managed service definitions. | High operational burden for patching, scaling, backup, and failover. Triggers Move to Managed Databases pathway. |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging infrastructure defined. | No forensic capability, compliance gap, and no visibility into infrastructure-level actions. |
| 4 | INF-Q1: Managed Compute | 2 | Application is containerized (Dockerfile exists) but no managed container orchestration (EKS/ECS/Fargate) is defined in the repository. | Manual compute management, no elastic scaling, no managed orchestration. Triggers Move to Cloud Native pathway. |
| 5 | SEC-Q7: Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD. No Dependabot. | Vulnerabilities in dependencies reach production undetected. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). GitHub Actions workflows exist for tests (`tests.yaml`), Docker builds (`docker-build.yaml`), and releases (`release.yaml`).
- **What it enables:** An agent that triggers deployments, checks build status, manages releases, and monitors pipeline health via the GitHub Actions API.
- **Additional steps:** Release workflow currently requires manual `workflow_dispatch` — automating trigger conditions would expand agent capabilities. Consider adding GitHub API tokens for agent access.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md`, `DESIGN.md`, and 14 docs in `docs/` directory covering CRR workflows, lifecycle, metrics, pause/resume, healthcheck, and operational procedures.
- **What it enables:** An Amazon Bedrock-powered RAG agent that indexes existing documentation and answers developer questions about Backbeat architecture, extension development, and operational procedures.
- **Additional steps:** Documentation is in Markdown format and ready for indexing. Consider consolidating operational runbooks into `docs/` to expand the knowledge base.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (modular monolith), INF-Q1=2 (no managed orchestration) |
| 2 | Move to Containers | Not Triggered | — | — | Contextual guard: Dockerfile exists — application is already containerized. INF-Q1=2 but compute is not raw EC2/VM. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures). MongoDB and Redis are already open source. No commercial DB engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (all databases self-managed), DATA-Q3=1 (no version pinning) |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4=2 (self-managed Kafka). Data processing workloads confirmed — Backbeat is a data processing engine for replication, lifecycle, and notifications. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), INF-Q11=2 (partial CI/CD, no deployment automation), OPS-Q5=1 (no deployment strategy), OPS-Q6=3 (integration tests exist but supporting) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "Scality backend engine for replication, lifecycle, and metadata workflows" contains no AI-related signal terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Backbeat is a modular monolith — a single codebase deployed as one Docker image with multiple extensions (replication, lifecycle, gc, notification, ingestion, oplogPopulator) that run as different process modes via separate entry points (`bin/queuePopulator.js`, `extensions/*/task.js`). Extensions share common libraries (`lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js`, `lib/Config.js`) and infrastructure (Kafka, MongoDB, Redis, ZooKeeper). Module boundaries are identifiable but coupled through shared configuration and infrastructure clients.

**Compute Model Gaps:** No managed container orchestration is defined — the application is containerized but lacks EKS, ECS, or Fargate resource definitions. Deployment is managed outside this repository.

**Communication Pattern Gaps:** Inter-extension communication uses Kafka topics (async, appropriate for event-processor archetype), but all infrastructure is self-managed. Outbound calls to S3 and MongoDB are synchronous, which is appropriate for the processing workload.

**Recommended Decomposition Approach:** See Decomposition Strategy section below. Extensions are natural service boundaries — each could be deployed independently on EKS with Amazon MSK (Serverless) or Amazon EventBridge replacing self-managed Kafka.

**Representative AWS Services:** Amazon EKS (preferred), AWS Lambda, Amazon API Gateway, AWS Step Functions, Amazon EventBridge (preferred), Amazon ECS/Fargate

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing (already partially in place via Kafka topics)

**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** MongoDB runs as a self-managed replica set (`localhost:27017,localhost:27018,localhost:27019` configured in `conf/config.json`). Redis runs self-managed on `localhost:6379`. ZooKeeper runs self-managed on `127.0.0.1:2181`. All connections use hardcoded host:port in configuration, overridable via environment variables in `docker-entrypoint.sh`.

**Engine Versions and EOL Status:** No database engine versions are pinned in IaC (no IaC exists). MongoDB driver version `^6.11.0` in `package.json` suggests modern MongoDB server compatibility (5.0+/6.0+/7.0+). Redis version is unspecified. ZooKeeper `3.9.4` used in CI tests.

**Data Access Patterns:** MongoDB is accessed via the `mongodb` npm driver primarily in `lib/queuePopulator/` and extensions. Redis is accessed via `ioredis` for metrics and caching. Access patterns are moderately centralized through `lib/clients/ClientManager.js`.

**Recommended Managed Database Targets:**
- **MongoDB → Amazon DocumentDB** or **Amazon DynamoDB** (preferred per technology preferences): DocumentDB provides MongoDB API compatibility for oplog-based workflows. DynamoDB is preferred for new service designs and metadata storage. Evaluate oplog dependency — Backbeat's queue populator reads the MongoDB oplog directly, which requires DocumentDB change streams or a redesign for DynamoDB Streams.
- **Redis → Amazon ElastiCache for Redis** or **Amazon MemoryDB**: Managed Redis with Multi-AZ failover and automated patching. ElastiCache is a drop-in replacement for the current ioredis usage.
- **ZooKeeper → Eliminate**: When migrating Kafka to Amazon MSK, ZooKeeper dependency is removed (MSK Serverless uses KRaft).

**Representative AWS Services:** Amazon DocumentDB, Amazon DynamoDB (preferred), Amazon ElastiCache, Amazon MemoryDB, Amazon Aurora (preferred for relational needs)

**Migration Tools:** AWS Database Migration Service (DMS), MongoDB-to-DocumentDB migration utilities

**AWS Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Streaming Infrastructure:** Kafka is self-managed via `node-rdkafka` (`^2.12.0` in `package.json`). Configuration in `conf/config.json` connects to `127.0.0.1:9092` with ZooKeeper at `127.0.0.1:2181/backbeat`. Multiple Kafka topics are used for inter-extension communication: `backbeat-replication`, `backbeat-replication-status`, `backbeat-replication-failed`, `backbeat-lifecycle-*`, `backbeat-gc`, `backbeat-ingestion`, `backbeat-oplog`, `backbeat-metrics`.

**Data Processing Workloads:** Backbeat IS a data processing engine — replication, lifecycle, garbage collection, and notification extensions all consume and produce Kafka messages. The queue populator reads from MongoDB oplog and publishes to Kafka topics. Multiple consumer groups process messages in parallel.

**Recommended Managed Analytics Targets:**
- **Self-managed Kafka → Amazon MSK Serverless** (strongly recommended per preference to avoid self-managed-kafka): Drop-in replacement for Kafka brokers with automatic scaling, no ZooKeeper management, and reduced operational overhead. `node-rdkafka` is compatible with MSK.
- **ZooKeeper → Eliminated**: MSK Serverless (KRaft mode) removes ZooKeeper dependency entirely.
- **Metrics/Backlog tracking → Amazon EventBridge** (preferred): Consider migrating metrics topics to EventBridge for event routing where appropriate.

**Representative AWS Services:** Amazon MSK Serverless (primary), Amazon EventBridge (preferred for event routing), Amazon Kinesis Data Streams (alternative)

**AWS Prescriptive Guidance:** [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** 0% — no Terraform, CloudFormation, CDK, Helm charts, or Kubernetes manifests found. All infrastructure is provisioned outside this repository with no reproducible definitions.

**Current CI/CD State:** GitHub Actions workflows exist:
- `tests.yaml` — lint, unit tests, functional tests with Docker services (Kafka, MongoDB, Redis, ZooKeeper)
- `docker-build.yaml` — builds and pushes Docker images to GHCR on push
- `release.yaml` — manual `workflow_dispatch` creates GitHub release and triggers Docker build

No automated deployment to any environment. No deployment pipeline (staging → production). No rollback automation.

**Deployment Strategy Gaps:** No blue/green, canary, or rolling deployment. Releases are manual. No CodeDeploy, Argo Rollouts, or Helm-based deployment.

**Testing Gaps:** Functional tests are comprehensive and run in CI with real services. This is a strength — integration testing coverage is good.

**Recommended DevOps Toolchain:**
- **IaC:** Terraform or CDK for AWS infrastructure (EKS cluster, MSK, DocumentDB/DynamoDB, ElastiCache, VPC, security groups)
- **Container Orchestration:** Amazon EKS (preferred) with Helm charts for Backbeat deployments
- **CI/CD:** Extend GitHub Actions with deployment stages using AWS CodeDeploy or ArgoCD on EKS
- **Deployment Strategy:** Implement rolling updates via EKS Deployment resource, then evolve to canary with Argo Rollouts

**Representative AWS Services:** AWS CDK/CloudFormation, Amazon EKS (preferred), AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy, Amazon ECR

**AWS Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

APP-Q2 scored 2 — Backbeat is a modular monolith with identifiable extensions but shared infrastructure coupling. Decomposition is recommended.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Backbeat's extensions (replication, lifecycle, gc, notification, ingestion, oplogPopulator) have identifiable boundaries — each has its own directory, index.js, config validator, and Kafka topic. Extract one extension at a time as an independent EKS service while the monolith continues running. | **Medium to High** — 6-18 months. Each extension extraction is bounded. | ✅ **Recommended.** Extensions already communicate via Kafka topics, making extraction natural. Start with the least-coupled extension (e.g., notification or gc). |
| **Conditional / Adaptive** | Start by deploying the existing Docker image on EKS (already containerized) with separate deployments per extension mode. Selectively extract high-value extensions based on scaling needs. | **Low to Medium** — EKS deployment in 2-4 weeks, selective extraction over 3-12 months. | ✅ **Recommended as first step.** Backbeat already supports running extensions as separate processes — deploy each entry point as a separate EKS Deployment. This achieves independent scaling without code changes. |
| **Big-Bang Rewrite** | Almost never appropriate. | **Very High** — 12-24+ months. | ⚠️ **Not recommended.** Backbeat is functional with clear module boundaries. Incremental approaches are safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the monolith's shared config and client patterns. | Every extraction — wrap shared `lib/Config.js` and `lib/clients/` access behind service-specific interfaces. |
| **Event Sourcing** | Already partially in place — extensions communicate via Kafka topics (backbeat-replication, backbeat-lifecycle-*, backbeat-gc). | Formalize Kafka topic contracts when extracting services. Define schemas for topic messages. |
| **Saga Pattern** | Manage distributed transactions when replication or lifecycle operations span multiple services. | When extracting replication status processor — currently coupled with replication queue processor via shared Kafka topics. |
| **Hexagonal Architecture** | Structure each extracted service with clear boundaries between business logic and infrastructure. | Every new service — decouple extension logic from shared `lib/BackbeatConsumer.js` and `lib/BackbeatProducer.js`. |

### Effort Estimation

| Factor | Current Signal | Effort Impact |
|--------|---------------|---------------|
| Module boundaries | Clear per-extension directories with own index.js, task.js entry points | **Low** — natural extraction boundaries |
| Data coupling | Shared MongoDB, Redis, Kafka, ZooKeeper infrastructure via shared config | **Medium** — need per-service connection config |
| Stored procedures | None (DATA-Q4=4) | **Low** — no database logic extraction needed |
| Communication patterns | Kafka topics between extensions (already async) | **Low** — Kafka topic boundaries are natural service boundaries |
| CI/CD maturity | Build/test in GitHub Actions but no deployment pipeline | **Medium** — need to build deployment pipeline for multi-service |
| Test coverage | Extensive functional tests per extension in CI | **Low** — existing tests can validate extraction |

**Recommended First Step:** Deploy the existing Docker image on EKS (preferred) with separate Deployment resources per extension mode (one for queue_populator, one for queue_processor, one for lifecycle_conductor, etc.) using the existing `docker-entrypoint.sh` and different command arguments. This achieves independent scaling immediately with zero code changes.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is containerized — a multi-stage `Dockerfile` exists at the repository root using `node:22.14.0-bookworm-slim` base image. A federation Dockerfile exists at `images/federation/Dockerfile`. Docker images are built and pushed to GHCR via `.github/workflows/docker-build.yaml`. However, no IaC defining ECS, EKS, Lambda, or Fargate resources exists in the repository. No Kubernetes manifests or Helm charts were found. The DESIGN.md states "Resides in its own container" and "Multiple instances per site for high availability," indicating container-based deployment managed externally. |
| **Gap** | Application is containerized but has no managed container orchestration defined. Deployment to managed compute (EKS/ECS/Fargate) is not codified in this repository. |
| **Recommendation** | Define EKS cluster infrastructure using Terraform or CDK (EKS is preferred per technology preferences). Create Helm charts for Backbeat deployments with separate Deployment resources per extension mode. Avoid self-managed Kubernetes (per preferences). |
| **Evidence** | `Dockerfile`, `images/federation/Dockerfile`, `.github/workflows/docker-build.yaml`, `DESIGN.md` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. MongoDB is configured as a replica set at `localhost:27017,localhost:27018,localhost:27019` in `conf/config.json` (`queuePopulator.mongo` section). Redis is configured at `localhost:6379` in the `redis` section. ZooKeeper is at `127.0.0.1:2181/backbeat`. No `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, or `aws_elasticache_*` resources found — no IaC exists. The `docker-entrypoint.sh` allows overriding via `MONGODB_HOSTS`, `REDIS_HOST`, and `ZOOKEEPER_CONNECTION_STRING` environment variables. |
| **Gap** | All databases are self-managed with no managed service definitions. No automated failover, no managed backups, no automatic patching. |
| **Recommendation** | Migrate MongoDB to Amazon DocumentDB (MongoDB-compatible) or Amazon DynamoDB (preferred). Migrate Redis to Amazon ElastiCache for Redis. Eliminate ZooKeeper when moving to Amazon MSK Serverless (KRaft). Avoid Oracle (per preferences). |
| **Evidence** | `conf/config.json`, `docker-entrypoint.sh`, `package.json` (mongodb ^6.11.0, ioredis ^5.4.2, node-zookeeper-client ^1.1.3) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype: event-processor.** No dedicated workflow orchestration service (Step Functions, Temporal, MWAA) is in use. The lifecycle conductor (`extensions/lifecycle/conductor/service.js`) uses `node-schedule` for cron-based batch scheduling. Replication uses Kafka topic chains for multi-step processing (backbeat-replication → backbeat-replication-status → backbeat-replication-failed). Multi-step event processing is handled through Kafka topic routing with retry and backoff logic configured in `conf/config.json`. |
| **Gap** | Multi-step event processing across Kafka topics is ad hoc — topic chains are defined in configuration but there is no managed orchestration for error handling, retry coordination, or visual workflow management across the pipeline stages. |
| **Recommendation** | For the lifecycle conductor's cron-based scheduling, consider AWS Step Functions with EventBridge Scheduler. For multi-step Kafka pipeline orchestration (replication → status → failed), evaluate EventBridge Pipes (preferred) to manage the topic chain with built-in error handling and DLQ support. |
| **Evidence** | `conf/config.json` (topic chain definitions), `extensions/lifecycle/conductor/service.js`, `lib/BackbeatConsumer.js` (retry logic), `package.json` (node-schedule ^2.1.1) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype: event-processor.** The primary event source is self-managed Kafka via `node-rdkafka` (`^2.12.0`). Multiple Kafka topics are defined in `conf/config.json`: `backbeat-replication`, `backbeat-replication-status`, `backbeat-replication-failed`, `backbeat-data-mover`, `backbeat-lifecycle-bucket-tasks`, `backbeat-lifecycle-object-tasks`, `backbeat-lifecycle-transition-tasks`, `backbeat-gc`, `backbeat-ingestion`, `backbeat-oplog`, `backbeat-metrics`, and cold storage topics. No `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*`, `aws_eventbridge_*` resources found. For an event-processor archetype, the primary event broker being self-managed is a score of 2. |
| **Gap** | Self-managed Kafka is the primary event broker for an event-processing application. This introduces operational overhead for broker patching, scaling, partition management, and monitoring. ZooKeeper adds additional operational burden. |
| **Recommendation** | Migrate to Amazon MSK Serverless (strongly recommended — avoids self-managed Kafka per preferences). MSK Serverless eliminates broker management, automatic scaling, and removes ZooKeeper dependency. `node-rdkafka` is compatible with MSK. Consider Amazon EventBridge (preferred) for event routing where topic-to-topic fan-out is needed. |
| **Evidence** | `conf/config.json` (kafka.hosts, all topic definitions), `package.json` (node-rdkafka ^2.12.0, node-zookeeper-client ^1.1.3), `lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network configuration defined. No IaC exists in the repository. The BackbeatServer listens on port 8900 with IP whitelisting (`server.healthChecks.allowFrom: ["127.0.0.1/8", "::1"]` in `conf/config.json`), but this is application-level, not infrastructure-level network security. All service connections use localhost or hardcoded IPs. |
| **Gap** | No infrastructure-level network security defined. Services would be deployed without documented VPC isolation, security groups, or network segmentation. |
| **Recommendation** | Define VPC infrastructure with private subnets using Terraform/CDK. Place Backbeat services in private subnets with least-privilege security groups. Use VPC endpoints for AWS service access (S3, DynamoDB, MSK). Consider VPC Lattice for service-to-service communication. |
| **Evidence** | `conf/config.json` (server.healthChecks.allowFrom), absence of any `.tf`, CloudFormation, or CDK files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The BackbeatServer (`lib/api/BackbeatServer.js`) creates a raw `http.createServer()` listening on port 8900 (configured in `conf/config.json`). There is no API Gateway, ALB, CloudFront, or any managed entry point. The server exposes healthcheck, metrics, pause/resume, and CRR failed endpoints directly. IP whitelisting is the only access control (`ipCheck.ipMatchCidrList` from arsenal). |
| **Gap** | Services exposed directly with no gateway, load balancer, throttling, or managed entry point. Note: for an event-processor, the HTTP surface is operational (healthcheck, metrics), so the impact is moderate — the primary workload enters via Kafka, not HTTP. |
| **Recommendation** | When deploying on EKS, use an Amazon API Gateway (preferred) or ALB ingress controller for the operational HTTP endpoints. Add throttling and request validation at the gateway layer. |
| **Evidence** | `lib/api/BackbeatServer.js` (http.createServer), `conf/config.json` (server.port: 8900), `lib/api/routes.js` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*`, `aws_appautoscaling_*`, HPA (Horizontal Pod Autoscaler), or KEDA definitions. The application supports configurable concurrency per consumer (e.g., `replication.queueProcessor.concurrency: 10` in `conf/config.json`), but this is static application-level configuration, not infrastructure auto-scaling. |
| **Gap** | No auto-scaling — all capacity is statically provisioned. Consumer concurrency is configured but not dynamically adjusted based on Kafka backlog or load. |
| **Recommendation** | On EKS, configure HPA based on Kafka consumer lag metrics (using KEDA with Kafka scaler). Scale replication and lifecycle processors independently based on their respective topic backlogs. |
| **Evidence** | `conf/config.json` (concurrency settings), absence of any auto-scaling definitions |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning, no PITR configuration. MongoDB backup strategy is not defined in this repository. Redis data persistence/backup is not configured. |
| **Gap** | No backup or recovery configuration for any data store. A MongoDB failure could result in metadata loss with no automated recovery. |
| **Recommendation** | When migrating to managed databases: enable automated backups on DocumentDB/DynamoDB with PITR, configure ElastiCache backup with retention periods, and document restore procedures. Use AWS Backup for centralized backup management. |
| **Evidence** | Absence of backup configuration in any files. `conf/config.json` (no backup settings) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DESIGN.md states "Multiple instances per site for high availability. If an instance dies, the queue replica from another instance can be used to process records." This indicates HA design intent. However, no Multi-AZ deployment configuration exists — no IaC defining `availability_zones`, no `multi_az = true` on databases, no cross-AZ subnet configuration. The MongoDB config uses a replica set (3 nodes), but all on localhost. |
| **Gap** | HA is designed at the application level (Kafka consumer groups, multiple instances) but no infrastructure-level multi-AZ deployment or fault isolation is codified. |
| **Recommendation** | When deploying on EKS: configure the cluster across 2+ AZs, spread Backbeat pods across AZs using pod anti-affinity, deploy DocumentDB/ElastiCache with Multi-AZ enabled. MSK Serverless handles multi-AZ automatically. |
| **Evidence** | `DESIGN.md` ("Multiple instances per site for high availability"), `conf/config.json` (MongoDB replica set on localhost), absence of IaC |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found. Search for `.tf`, `.tfvars`, `template.yaml`, `cdk.json`, `Chart.yaml`, `values.yaml`, `kustomization.yaml` returned zero results. All infrastructure (Kafka, MongoDB, Redis, ZooKeeper, compute) is provisioned outside this repository with no reproducible definitions. |
| **Gap** | 0% IaC coverage. Infrastructure changes are manual and non-reproducible. No disaster recovery capability from code. Environment consistency cannot be guaranteed. |
| **Recommendation** | Adopt Terraform or AWS CDK to define all infrastructure: EKS cluster, MSK Serverless, DocumentDB/DynamoDB, ElastiCache, VPC/subnets/security groups, IAM roles, CloudWatch alarms, and backup plans. Store IaC in this repository or a dedicated infrastructure repository. Create Helm charts for Backbeat Kubernetes deployments. |
| **Evidence** | Absence of any IaC files in the entire repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions workflows exist: `tests.yaml` (lint, unit tests, functional tests with Docker services), `docker-build.yaml` (build and push Docker images to GHCR on push), `release.yaml` (manual `workflow_dispatch` to create GitHub release and trigger Docker build). Build and test are automated. Docker image push is automated on every push. However, there is no automated deployment pipeline — `release.yaml` requires manual triggering and only creates a release/image, not a deployment. No CodeDeploy, no ArgoCD, no Helm deployment steps. |
| **Gap** | Build and test are automated but deployment is manual. No staging-to-production pipeline. No automated rollback. Release requires manual `workflow_dispatch`. |
| **Recommendation** | Extend GitHub Actions or adopt AWS CodePipeline to add deployment stages: build → test → push image → deploy to staging (EKS) → integration test → deploy to production (EKS) with automated rollback on failure. |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/docker-build.yaml`, `.github/workflows/release.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is JavaScript/Node.js (Node >= 20 required per `package.json` engines). The codebase uses modern AWS SDK v3 (`@aws-sdk/client-iam`, `@aws-sdk/client-s3`, `@aws-sdk/client-sts`, `@aws-sdk/credential-providers`). A secondary Go component exists at `bucket-scanner/` (Go 1.16.2 per CI). JavaScript has first-class AWS SDK coverage, broad cloud-native tooling, and mature framework ecosystem. |
| **Gap** | No significant gap. JavaScript/Node.js is well-suited for event-driven, async processing workloads like Backbeat. |
| **Recommendation** | Continue with Node.js. The migration to AWS SDK v3 (already in progress — `@aws-sdk/client-*` packages) positions the application well for cloud-native deployment. |
| **Evidence** | `package.json` (engines: node >= 20, @aws-sdk/* dependencies), `.github/workflows/tests.yaml` (node-version: 22), `bucket-scanner/` (Go) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit — one Dockerfile builds the entire application. Multiple extensions (replication, lifecycle, gc, notification, ingestion, oplogPopulator, mongoProcessor) run as different process modes via separate entry points defined in `package.json` scripts (e.g., `queue_populator`, `queue_processor`, `lifecycle_conductor`, `garbage_collector`). Each extension has its own directory with `index.js` and task entry points. Extensions share common libraries (`lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js`, `lib/Config.js`, `lib/clients/`), configuration (`conf/config.json`), and infrastructure (Kafka, MongoDB, Redis, ZooKeeper). Module boundaries are identifiable but coupled through shared config, shared client libraries, and a single Docker image. This is a modular monolith with clear but coupled module boundaries. |
| **Gap** | Single deployable unit with shared configuration and client libraries. Extensions cannot be independently versioned, deployed, or scaled at the infrastructure level (though they run as separate processes). Shared `conf/config.json` contains configuration for ALL extensions. |
| **Recommendation** | See Decomposition Strategy section. Immediate win: deploy existing Docker image on EKS with separate Deployment per extension mode. Medium-term: extract extensions into independently deployable services using Strangler Fig pattern. |
| **Evidence** | `Dockerfile` (single image), `package.json` (scripts per extension), `extensions/index.js`, `conf/config.json` (shared config), `lib/BackbeatConsumer.js` (shared consumer), `docker-entrypoint.sh` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: event-processor.** Primary input is async — Kafka message consumption via `BackbeatConsumer`. Inter-extension communication is async via Kafka topics (replication publishes to `backbeat-replication-status`, lifecycle publishes to `backbeat-lifecycle-*` topics). Outbound calls to S3 and MongoDB are synchronous HTTP/TCP, which is appropriate for data operations within event processing. The async input model is correct for the archetype. Some sync outbound calls exist where async might help (e.g., S3 data replication could benefit from async patterns for large objects). |
| **Gap** | Async input with some sync outbound calls that could be async. The architecture is mostly correct for the event-processor archetype but S3 replication operations and MongoDB writes are synchronous within event handlers. |
| **Recommendation** | Maintain the current async-first architecture. For long-running S3 operations, consider S3 Batch Operations or async multipart upload patterns. When migrating to MSK, leverage EventBridge for event fan-out where appropriate. |
| **Evidence** | `lib/BackbeatConsumer.js` (async Kafka consumption), `conf/config.json` (Kafka topic definitions), `lib/BackbeatProducer.js` (async message production) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: event-processor.** Event handlers are async by design — Kafka messages are processed with configurable concurrency (`concurrency: 10` in config). Retry with exponential backoff is configured per destination type in `conf/config.json` (e.g., `aws_s3.timeoutS: 900`, `backoff.min: 60000`, `backoff.max: 900000`). Circuit breaker patterns exist via `breakbeat` library (`lib/BackbeatConsumer.js` uses `CircuitBreaker` to pause consumption when downstream is unhealthy). Slow task detection exists (`_startProcessingTask` logs warnings for tasks exceeding `maxPollIntervalMs`). However, there is no checkpointing within individual event handlers — if a long-running replication operation fails midway, the entire message is retried. |
| **Gap** | Most handlers are safely bounded with timeouts and circuit breakers. However, no sub-workflow checkpointing exists — large object replication (multipart upload) within a single Kafka message handler has no intermediate checkpoint. If the handler crashes mid-transfer, all progress is lost. |
| **Recommendation** | For large object replication, implement checkpointing via DynamoDB (preferred) to track multipart upload progress per object. This enables resume-on-retry instead of restart-from-scratch. Consider Step Functions for multi-step replication workflows involving very large objects. |
| **Evidence** | `conf/config.json` (retry/backoff/timeout config), `lib/BackbeatConsumer.js` (CircuitBreaker, slow task detection, concurrency), `package.json` (breakbeat dependency) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | HTTP API routes defined in `lib/api/routes.js` use `/_/` prefix paths: `/_/healthcheck`, `/_/metrics/crr/<location>/backlog`, `/_/crr/pause/<location>`, `/_/crr/resume/<location>`, `/_/crr/status/<location>`, `/_/monitoring/metrics`, `/_/configuration/workflows`. No version numbering in paths (no `/v1/`, `/v2/`). No `Accept-Version` headers. No OpenAPI specification. No changelog for API changes. |
| **Gap** | No versioning — API changes would break all consumers. No OpenAPI spec for documentation or contract enforcement. |
| **Recommendation** | Add version prefix to API routes (e.g., `/_/v1/healthcheck`). Generate an OpenAPI specification from the route definitions. This is lower priority for an event-processor where the HTTP surface is operational, but critical if other services consume these APIs. |
| **Evidence** | `lib/api/routes.js` (all route definitions with `/_/` prefix, no version), `lib/api/BackbeatRequest.js` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via `conf/config.json` with hardcoded host:port values (Kafka: `127.0.0.1:9092`, ZooKeeper: `127.0.0.1:2181`, S3: `127.0.0.1:8000`, Vault: `127.0.0.1:8500`, MongoDB: `localhost:27017-27019`, Redis: `localhost:6379`). The `docker-entrypoint.sh` allows overriding via environment variables (`KAFKA_HOSTS`, `MONGODB_HOSTS`, `REDIS_HOST`, `CLOUDSERVER_HOST`, `ZOOKEEPER_CONNECTION_STRING`). This is environment-variable-based discovery — configurable but not dynamic. No AWS Service Discovery, Consul, Istio, or DNS-based discovery. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. Adding or removing service instances requires configuration changes and redeployment. |
| **Recommendation** | On EKS, use Kubernetes DNS-based service discovery (service names resolve to cluster IPs). For cross-cluster communication, use AWS Cloud Map. Environment variable approach is acceptable as a stepping stone when deploying to Kubernetes. |
| **Evidence** | `conf/config.json` (all hardcoded endpoints), `docker-entrypoint.sh` (environment variable overrides) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application operates on S3 objects — replication copies objects between S3 buckets, lifecycle manages object transitions and expirations, and ingestion imports objects from external sources. S3 is the primary data store for unstructured data. The application uses `@aws-sdk/client-s3` for S3 operations. However, no parsing pipeline (Textract, Tika) exists for the stored objects — Backbeat treats objects as opaque blobs for replication/lifecycle purposes. |
| **Gap** | Data is in S3 (or S3-compatible storage) but no automated parsing or extraction pipeline exists. This is expected for a replication/lifecycle engine — parsing is not its responsibility. |
| **Recommendation** | No action required for the current use case. If future requirements include content-aware lifecycle policies or intelligent tiering based on content type, consider integrating Amazon Textract or S3 Object Lambda for content analysis. |
| **Evidence** | `package.json` (@aws-sdk/client-s3), `conf/config.json` (s3 host/port config), `extensions/replication/` (S3 object replication), `extensions/lifecycle/` (S3 object lifecycle) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MongoDB access is centralized through configuration (`conf/config.json` `queuePopulator.mongo` section) and the `mongodb` npm driver. `lib/clients/ClientManager.js` provides some client management. Redis access is via `ioredis` configured in the `redis` section. However, there is no formal repository/DAO pattern — MongoDB operations are spread across `lib/queuePopulator/`, `extensions/oplogPopulator/`, and other extension directories. Different extensions access MongoDB and Redis directly through their own patterns rather than through a unified data access layer. |
| **Gap** | Repository/DAO pattern exists in some areas (client management) but inconsistent across the codebase. Extensions access MongoDB and Redis directly without a centralized data access abstraction. |
| **Recommendation** | Create a unified data access layer in `lib/clients/` that abstracts MongoDB and Redis operations behind consistent interfaces. This will ease migration to managed services (DocumentDB/DynamoDB, ElastiCache) by centralizing connection management and query patterns. |
| **Evidence** | `lib/clients/ClientManager.js`, `conf/config.json` (mongo and redis config sections), `package.json` (mongodb ^6.11.0, ioredis ^5.4.2) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine versions are pinned in IaC (no IaC exists). MongoDB server version is not specified anywhere in the repository configuration. The `mongodb` npm driver version is `^6.11.0` (compatible with MongoDB 5.0+/6.0+/7.0+). Redis server version is not specified. In CI tests (`.github/workflows/tests.yaml`), `redis:alpine` is used (no version pin) and `zookeeper:3.9.4` is pinned. The custom CI MongoDB image (`ghcr.io/${{ github.repository }}/ci-mongodb`) uses an unspecified base version. |
| **Gap** | No engine version pinning. MongoDB and Redis server versions are unknown and unmanaged. No documented version-update procedure. EOL status cannot be assessed without knowing the deployed versions. |
| **Recommendation** | Pin database engine versions in configuration or IaC. When migrating to managed services, specify engine versions explicitly (e.g., DocumentDB 5.0, ElastiCache Redis 7.x). Establish a version-update procedure with downtime windows and rollback plans. |
| **Evidence** | `conf/config.json` (no version info), `.github/workflows/tests.yaml` (redis:alpine, zookeeper:3.9.4, ci-mongodb custom image), `package.json` (mongodb ^6.11.0 driver) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. MongoDB is used as a document store — all business logic resides in the JavaScript application layer. No `.sql` files found. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` patterns. The application reads the MongoDB oplog for change detection (`queuePopulator.logSource: "mongo"` in config) but does not use server-side scripts. |
| **Gap** | No gap. All business logic is in the application layer. |
| **Recommendation** | No action required. This clean separation makes database migration (to DocumentDB or DynamoDB) significantly easier. |
| **Evidence** | `conf/config.json` (MongoDB as document store), absence of `.sql` files, `lib/queuePopulator/` (oplog reading in application layer) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging infrastructure defined. No `aws_cloudtrail` resources, no log file validation, no immutable storage configuration. The application uses `werelogs` for application-level structured logging, but this is operational logging, not audit logging for infrastructure actions. |
| **Gap** | No CloudTrail or equivalent audit logging. No forensic capability for infrastructure-level actions. |
| **Recommendation** | Enable CloudTrail with log file validation and S3 Object Lock for immutable storage when deploying AWS infrastructure. Configure CloudTrail to log all management events and S3 data events relevant to Backbeat's operations. |
| **Evidence** | Absence of CloudTrail configuration, `package.json` (werelogs for application logging only) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS key configuration found. No encryption-at-rest settings in any configuration or IaC (no IaC exists). The `conf/config.json` includes `certFilePaths` for TLS certificates (encryption in transit) but no encryption at rest. MongoDB, Redis, and Kafka data-at-rest encryption is not configured in this repository. |
| **Gap** | No encryption at rest configured for any data store. |
| **Recommendation** | When deploying managed services: enable encryption at rest with customer-managed KMS keys on DocumentDB/DynamoDB, ElastiCache, MSK, and S3 buckets. Define KMS key resources in IaC with rotation policies. |
| **Evidence** | `conf/config.json` (certFilePaths for TLS only), absence of KMS configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The BackbeatServer (`lib/api/BackbeatServer.js`) uses IP-based whitelisting via `ipCheck.ipMatchCidrList(this._config.healthChecks.allowFrom, req.socket.remoteAddress)`. Allowed IPs are configured as `["127.0.0.1/8", "::1"]` in `conf/config.json`. No OAuth2, JWT, or token-based authentication on API endpoints. For S3 and Vault communication, the application uses IAM-like role-based auth with STS AssumeRole via `CredentialsManager.js` (temporary credentials with expiration). |
| **Gap** | API key or static credential authentication (IP whitelisting) without token-based auth. While acceptable for internal operational endpoints in a private network, this does not meet the OAuth2/JWT standard for API authentication. |
| **Recommendation** | When exposing endpoints through API Gateway (preferred), add IAM authorization or Cognito-based JWT authentication. For internal EKS communication, Kubernetes network policies and service mesh mTLS can provide service-to-service authentication. |
| **Evidence** | `lib/api/BackbeatServer.js` (ipCheck.ipMatchCidrList), `conf/config.json` (healthChecks.allowFrom), `lib/credentials/CredentialsManager.js` (STS AssumeRole) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses Scality's Vault (`vaultclient` dependency) for credential management — an IAM-compatible identity service that issues temporary credentials. `CredentialsManager.js` implements STS AssumeRole workflow using `@aws-sdk/client-sts`. Credentials are temporary with expiration and automatic renewal. This is a federated identity model but with a custom/standalone identity provider (Scality Vault), not a standard centralized IdP (Cognito, Okta). |
| **Gap** | Application uses a custom identity provider (Scality Vault) that can federate but is not a standard centralized IdP. Integration with AWS IAM or Cognito is not in place. |
| **Recommendation** | When migrating to AWS, integrate with AWS IAM for service-to-service authentication using IAM roles for EKS pods (IRSA). Replace Vault-based credential issuance with native AWS IAM role assumption. For user-facing authentication (if needed), integrate with Amazon Cognito. |
| **Evidence** | `lib/credentials/CredentialsManager.js` (STS AssumeRole), `package.json` (vaultclient, @aws-sdk/client-sts), `conf/config.json` (vaultAdmin config) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | `conf/authdata.json` contains hardcoded test credentials (`accessKey1`, `verySecretKey1`). `conf/config.json` and `conf/locationConfig.json` contain credential placeholders (`TO_BE_ADDED`). In production, credentials are provided via environment variables through `docker-entrypoint.sh` and external files (`CredentialsManager.resolveExternalFileSync` reads credentials from filesystem). The `CredentialsManager.js` supports temporary credentials via STS AssumeRole. No AWS Secrets Manager, HashiCorp Vault (separate from Scality Vault), or dedicated secrets management with rotation. |
| **Gap** | Some secrets managed through environment variables and external files, but production database credentials and service endpoints are passed as environment variables without encryption or rotation. Test credentials are hardcoded in `conf/authdata.json`. |
| **Recommendation** | Migrate secrets to AWS Secrets Manager with automated rotation. Use EKS Secrets Store CSI Driver to mount secrets into pods. Remove hardcoded test credentials from `conf/authdata.json` (or mark the file as test-only). Enable AWS Secrets Manager integration for MongoDB, Redis, and Kafka credentials. |
| **Evidence** | `conf/authdata.json` (hardcoded test credentials), `docker-entrypoint.sh` (env var overrides), `lib/credentials/CredentialsManager.js` (resolveExternalFileSync), `conf/locationConfig.json` (credential placeholders) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dockerfile uses `node:22.14.0-bookworm-slim` base image — a version-pinned, slim Debian-based image. Multi-stage build reduces attack surface by not including build tools in the final image. `tini` is used as PID 1 for proper signal handling. However, no SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base image (CIS, Bottlerocket). No container image scanning in CI pipeline. |
| **Gap** | Default Debian base image with no hardening. No vulnerability scanning for the container image. No patching strategy for base image updates. |
| **Recommendation** | Consider switching to a hardened base image (Amazon Linux 2023 slim or Bottlerocket for EKS nodes). Add container image scanning in CI (Amazon ECR image scanning or Snyk container). Implement a base image update policy with automated rebuild triggers. |
| **Evidence** | `Dockerfile` (node:22.14.0-bookworm-slim, multi-stage build, tini), `.github/workflows/docker-build.yaml` (no scanning step) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CI/CD pipeline includes ESLint (`eslint ^9.12.0` in devDependencies, `yarn run lint` in `tests.yaml`) and Codecov for coverage reporting. No SAST (SonarQube, Semgrep, CodeGuru), no DAST, no dependency vulnerability scanning (no Dependabot, no `npm audit`, no `yarn audit`, no Snyk). No container image scanning. No security gates in the pipeline. `codecov.yml` is configured for coverage only. |
| **Gap** | No security scanning tools configured. No Dependabot. No SAST. No container scanning. Pipeline has no security validation step. |
| **Recommendation** | Add Dependabot or Renovate for automated dependency updates. Add `npm audit` or Snyk to the CI pipeline with a blocking gate on critical/high findings. Add a SAST tool (Semgrep or CodeGuru Reviewer). Enable Amazon ECR image scanning for the Docker images. |
| **Evidence** | `.github/workflows/tests.yaml` (lint only, no security scanning), `package.json` (eslint in devDependencies), `codecov.yml` (coverage only), absence of `.snyk`, `dependabot.yml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No OpenTelemetry SDK, X-Ray SDK, or distributed tracing library found in `package.json` dependencies. No trace ID propagation patterns (no `traceparent`, `X-Amzn-Trace-Id` headers). The application uses `werelogs` (`scality/werelogs`) for structured logging with request loggers (`logger.newRequestLogger()` in `BackbeatServer.js`), but this is logging, not distributed tracing. Kafka message processing has no trace context propagation between producer and consumer. |
| **Gap** | No distributed tracing instrumented. Debugging failures across the Kafka topic pipeline (producer → consumer → status processor) requires manual log correlation. |
| **Recommendation** | Add OpenTelemetry SDK for Node.js (`@opentelemetry/sdk-node`, `@opentelemetry/instrumentation-*`). Propagate trace context through Kafka message headers. Export traces to AWS X-Ray or an OpenTelemetry-compatible backend. This is critical for an event-processor with multi-stage pipelines. |
| **Evidence** | `package.json` (no tracing dependencies), `lib/api/BackbeatServer.js` (werelogs only), `lib/BackbeatConsumer.js` (no trace context in message processing) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus alerts define warning/critical thresholds for business-relevant metrics: replication RPO (`rpoWarningThreshold: 600s`, `rpoCriticalThreshold: 900s`), replication latency (`latencyWarningThreshold: 3000`, `latencyCriticalThreshold: 6000`), replication error rates (`replicationErrorsWarningThreshold: 0.1`, `replicationErrorsCriticalThreshold: 1`), lifecycle latency (`lifecycle_latency_warning_threshold: 24h`, `lifecycle_latency_critical_threshold: 36h`). These function as operational SLO-like thresholds but are not formally defined as SLOs with error budgets. |
| **Gap** | Basic availability/latency alarms exist but no formal SLO definitions with error budgets. Thresholds are configurable but there is no SLO tracking, burn-rate alerting, or error budget consumption tracking. |
| **Recommendation** | Formalize RPO, latency, and error rate thresholds as SLOs. Implement error budget tracking using CloudWatch or a dedicated SLO platform. Add burn-rate alerts that trigger before SLO breach. |
| **Evidence** | `monitoring/replication/alerts.yaml` (RPO, latency, error thresholds), `monitoring/lifecycle/alerts.yaml` (lifecycle latency thresholds) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Business-relevant metrics are published via `prom-client` (`^15.1.3`) and `node-rdkafka-prometheus` (`^1.0.0`). `lib/MetricsProducer.js` publishes replication/lifecycle metrics (ops, bytes, throughput). `lib/KafkaBacklogMetrics.js` tracks consumer lag, task processing times, and circuit breaker state. `lib/CircuitBreaker.js` exports `s3_circuit_breaker` and `s3_circuit_breaker_errors_count` gauges. Grafana dashboards exist in `monitoring/` for replication, lifecycle, notification, ingestion, oplog-populator, and cold storage. Prometheus alerts track RPO, latency, error rates, and service availability. |
| **Gap** | Some business metrics tracked but not systematically across all extensions. Dashboard coverage varies per extension. No unified business KPI dashboard combining all extensions. |
| **Recommendation** | Standardize business metrics across all extensions. Create a unified operational dashboard combining replication throughput, lifecycle completion rates, GC effectiveness, and notification delivery rates. When migrating to AWS, publish metrics to CloudWatch alongside Prometheus. |
| **Evidence** | `package.json` (prom-client, node-rdkafka-prometheus), `lib/MetricsProducer.js`, `lib/KafkaBacklogMetrics.js`, `lib/CircuitBreaker.js`, `monitoring/replication/dashboard.json`, `monitoring/lifecycle/dashboard.json`, `monitoring/notification/dashboard.json` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus alerts use static thresholds: `rpoWarningThreshold=600`, `rpoCriticalThreshold=900`, `latencyWarningThreshold=3000`, `latencyCriticalThreshold=6000`, `replicationErrorsWarningThreshold=0.1`, `replicationErrorsCriticalThreshold=1`, lifecycle latency `24h/36h`. Service availability alerts check `up` metric against expected replica counts. These are well-defined static thresholds but no anomaly detection is configured. |
| **Gap** | Static threshold alarms only. No anomaly detection for gradual degradation or novel failure modes. |
| **Recommendation** | Enable CloudWatch anomaly detection on key metrics (replication throughput, consumer lag, error rates) when migrating to AWS. CloudWatch anomaly detection uses ML models to automatically set dynamic thresholds based on historical patterns. |
| **Evidence** | `monitoring/replication/alerts.yaml` (static thresholds), `monitoring/lifecycle/alerts.yaml` (static thresholds) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Docker images are built and pushed to GHCR via `.github/workflows/docker-build.yaml`. Releases are created manually via `workflow_dispatch` in `.github/workflows/release.yaml`. No blue/green, canary, or rolling deployment strategy. No CodeDeploy, Argo Rollouts, Helm canary, Lambda traffic shifting, or ALB weighted target groups. No feature flags. Deployment to production is not automated in this repository. |
| **Gap** | Direct-to-production deployment with no staged rollout. No deployment strategy defined. |
| **Recommendation** | On EKS, implement rolling updates as a baseline (Kubernetes Deployment default). Evolve to canary deployments using Argo Rollouts with Prometheus metrics for automated rollback. For Kafka consumers, leverage consumer group rebalancing for rolling updates. |
| **Evidence** | `.github/workflows/docker-build.yaml`, `.github/workflows/release.yaml` (workflow_dispatch only), absence of deployment configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Extensive functional tests exist in `tests/functional/` covering: api (routes, retry), replication, lifecycle, ingestion, notification, oplogPopulator, queuePopulator, and lib. Tests run in CI (`.github/workflows/tests.yaml`) with real Docker services: Kafka (`ci-kafka`), MongoDB (`ci-mongodb`), Redis (`redis:alpine`), ZooKeeper (`zookeeper:3.9.4`), and syntheticbucketd. Unit tests exist in `tests/unit/`. Performance tests exist (`tests/performance/lifecycle/conductor-check-memory-balloon.js`). Codecov tracks coverage per component. |
| **Gap** | Integration tests for primary workflows exist and run consistently in CI. Some gaps may exist in coverage across all extensions. No contract testing or end-to-end tests against a full Zenko deployment in this repository's CI. |
| **Recommendation** | Maintain current functional test suite. Add contract tests for Kafka message schemas between extensions. When deploying on EKS, add integration tests against the deployed environment in the deployment pipeline. |
| **Evidence** | `tests/functional/` (8 test suites), `.github/workflows/tests.yaml` (functional-tests job with Docker services), `codecov.yml` (component coverage tracking) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbook files found. No Systems Manager Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. Alert rules exist in `monitoring/` (Prometheus alerts for service down, high error rates, RPO breach) but all alerts require manual response — no automated remediation. |
| **Gap** | No runbooks — incident response is entirely ad hoc. Alerts fire but remediation is manual. |
| **Recommendation** | Create machine-readable runbooks for common incidents: consumer lag spike (scale consumers), circuit breaker tripped (investigate downstream), service down (restart pod). Implement automated remediation using AWS Systems Manager Automation or Step Functions for self-healing patterns. |
| **Evidence** | `monitoring/replication/alerts.yaml` (alerts exist), `monitoring/lifecycle/alerts.yaml` (alerts exist), absence of runbook files |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Grafana dashboards and Prometheus alerts exist per extension: `monitoring/replication/` (dashboard.json, alerts.yaml), `monitoring/lifecycle/` (dashboard.json, alerts.yaml), `monitoring/notification/` (dashboard.json, alerts.yaml), `monitoring/oplog-populator/` (dashboard.json, alerts.yaml), `monitoring/ingestion/` (dashboards and alerts), `monitoring/cold-storage/` (dashboard.json). Dashboards are packaged as OCI artifacts via ORAS in `docker-build.yaml`. However, no CODEOWNERS file exists. No named owners on alarms. No team attribution on dashboards. |
| **Gap** | Ad hoc observability — dashboards and alarms exist for most extensions but no clear ownership or team attribution. |
| **Recommendation** | Add a CODEOWNERS file mapping `monitoring/*` directories to responsible teams. Add owner labels to Prometheus alerts. Include team attribution in Grafana dashboard metadata. |
| **Evidence** | `monitoring/` (per-extension dashboards and alerts), `.github/workflows/docker-build.yaml` (ORAS push of dashboards), absence of CODEOWNERS |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging found. No IaC exists to define tags on resources. No `default_tags`, no `required-tags` Config rules, no Tag Policies. No tagging standard defined. |
| **Gap** | No tags on resources. No cost allocation, ownership, or environment identification through tagging. |
| **Recommendation** | Define a tagging standard (minimum: `Environment`, `Service`, `Owner`, `CostCenter`). Implement `default_tags` in Terraform provider configuration when creating IaC. Enable AWS Tag Policies in Organizations and AWS Config rules for enforcement. |
| **Evidence** | Absence of IaC files and tagging configuration |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `Dockerfile` | INF-Q1, INF-Q4, APP-Q2, SEC-Q6 | Multi-stage Docker build with node:22.14.0-bookworm-slim base image |
| `images/federation/Dockerfile` | INF-Q1 | Federation-specific Docker image |
| `package.json` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, APP-Q1, APP-Q2, APP-Q4, DATA-Q2, DATA-Q3, OPS-Q1, OPS-Q3, SEC-Q4, SEC-Q7 | Dependencies, scripts, engine requirements |
| `conf/config.json` | INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, APP-Q2, APP-Q6, DATA-Q1, DATA-Q3, DATA-Q4, SEC-Q3 | All service endpoints, Kafka topics, MongoDB config, Redis config, server config |
| `conf/authdata.json` | SEC-Q5 | Hardcoded test credentials (accessKey1/verySecretKey1) |
| `conf/locationConfig.json` | SEC-Q5 | Location configuration with credential placeholders |
| `docker-entrypoint.sh` | INF-Q2, INF-Q11, APP-Q2, APP-Q6, SEC-Q5 | Environment variable overrides for all service configuration |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | CI pipeline: lint, unit tests, functional tests with Docker services |
| `.github/workflows/docker-build.yaml` | INF-Q1, INF-Q11, OPS-Q5, OPS-Q8, SEC-Q6 | Docker image build and GHCR push, ORAS dashboard packaging |
| `.github/workflows/release.yaml` | INF-Q11, OPS-Q5 | Manual release workflow (workflow_dispatch) |
| `lib/BackbeatConsumer.js` | INF-Q3, INF-Q4, APP-Q3, APP-Q4, OPS-Q1 | Kafka consumer with circuit breaker, retry, concurrency control |
| `lib/BackbeatProducer.js` | INF-Q4, APP-Q3 | Kafka producer |
| `lib/api/BackbeatServer.js` | INF-Q6, APP-Q5, SEC-Q3, OPS-Q1 | HTTP server on port 8900 with IP whitelisting |
| `lib/api/routes.js` | INF-Q6, APP-Q5 | API route definitions (/_/healthcheck, /_/metrics/*, /_/crr/*) |
| `lib/credentials/CredentialsManager.js` | SEC-Q3, SEC-Q4, SEC-Q5 | STS AssumeRole, external file credential loading |
| `lib/clients/ClientManager.js` | DATA-Q2 | Client management for database connections |
| `lib/Config.js` | APP-Q2, DATA-Q2 | Shared configuration loading for all extensions |
| `lib/CircuitBreaker.js` | APP-Q4, OPS-Q3 | Circuit breaker metrics export (Prometheus gauges) |
| `lib/MetricsProducer.js` | OPS-Q3 | Business metrics publishing (replication/lifecycle ops, bytes) |
| `lib/KafkaBacklogMetrics.js` | OPS-Q3 | Kafka consumer lag and task processing metrics |
| `extensions/index.js` | APP-Q2 | Extension module loader (dynamic directory scan) |
| `extensions/replication/` | DATA-Q1, APP-Q2 | Replication extension (queue processor, status processor) |
| `extensions/lifecycle/` | DATA-Q1, APP-Q2, INF-Q3 | Lifecycle extension (conductor, bucket/object processors) |
| `DESIGN.md` | INF-Q1, INF-Q9 | Architecture design: containerized, distributed, extensible |
| `README.md` | Quick Agent Wins | Documentation for RAG knowledge agent |
| `docs/` | Quick Agent Wins | 14 operational documentation files |
| `monitoring/replication/alerts.yaml` | OPS-Q2, OPS-Q4, OPS-Q7 | Prometheus alerts: RPO, latency, error rate thresholds |
| `monitoring/replication/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard for replication metrics |
| `monitoring/lifecycle/alerts.yaml` | OPS-Q2, OPS-Q4, OPS-Q7 | Prometheus alerts: lifecycle latency thresholds |
| `monitoring/lifecycle/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard for lifecycle metrics |
| `monitoring/notification/` | OPS-Q8 | Notification extension dashboards and alerts |
| `monitoring/oplog-populator/` | OPS-Q8 | Oplog populator dashboards and alerts |
| `monitoring/ingestion/` | OPS-Q8 | Ingestion extension dashboards and alerts |
| `monitoring/cold-storage/` | OPS-Q8 | Cold storage dashboard |
| `tests/functional/` | OPS-Q6 | 8 functional test suites with Docker services |
| `codecov.yml` | OPS-Q6, SEC-Q7 | Coverage tracking per component |
| `eslint.config.mjs` | SEC-Q7 | ESLint configuration (linting only, not security) |
| `circle.yml` | INF-Q11 | Legacy CI configuration (superseded by GitHub Actions) |
| `bucket-scanner/` | APP-Q1 | Go-based bucket scanner sub-component |
