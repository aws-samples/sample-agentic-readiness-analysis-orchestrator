# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | backbeat |
| **Date** | 2025-07-14 |
| **TD Version** | N/A — local execution |
| **Repo Type** | application |
| **Service Archetype** | event-processor (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, storage, replication |
| **Context** | Scality backend engine for replication, lifecycle, and metadata workflows. |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true |
| **Overall Score** | 2.04 / 4.0 |

**Archetype Justification**: Primary runtime pattern is Kafka message consumption via `node-rdkafka` (BackbeatConsumer.js is a core component). Multiple extension processors (replication queue processor, lifecycle conductor/bucket/object processors, GC, notification, oplog populator) consume from Kafka topics and process events asynchronously. The HTTP API surface (port 8900) is secondary — used for health checks, Prometheus metrics, and management operations. Classified as `event-processor`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.36 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 2.00 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.04 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No Infrastructure as Code — all infrastructure manually created (ClickOps) | Blocks reproducible deployments, disaster recovery, and environment consistency. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation definitions found | Services may be exposed without network isolation — fundamental security and blast-radius risk. |
| 3 | INF-Q1: Managed Compute | 1 | No managed compute orchestration defined — Dockerfile exists but no EKS/ECS/Fargate/Lambda IaC | Workload lacks elastic scaling, automated patching, and deployment orchestration. |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configuration | No forensic trail for compliance or incident investigation. |
| 5 | INF-Q6: API Entry Point | 1 | No API Gateway, ALB, or CloudFront entry point defined | API surface (port 8900) exposed without throttling, auth offload, or traffic management. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 — GitHub Actions CI/CD pipeline exists (`.github/workflows/tests.yaml`, `docker-build.yaml`, `release.yaml`) with automated test, build, and Docker image push stages.
- **What it enables:** An agent that triggers deployments, checks build status, monitors release pipelines, and manages Docker image tagging via GitHub Actions API.
- **Additional steps:** Expose GitHub Actions workflow dispatch API for agent invocation; add deployment stage to current pipeline to enable agent-triggered deploys.
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Rich documentation exists — `README.md`, `DESIGN.md`, and 14 markdown files in `docs/` covering CRR, lifecycle, metrics, healthcheck, pause/resume, data-mover, and more.
- **What it enables:** A knowledge agent that indexes existing documentation as a corpus and answers developer questions about Backbeat architecture, extension writing, and operational procedures using RAG.
- **Additional steps:** Index documentation into a vector store (e.g., Amazon Bedrock Knowledge Base with S3 source). Some docs reference internal systems — curate for relevance.
- **Effort:** Low

### Observability Agent

- **Prerequisite:** OPS-Q1 = 2 — Prometheus metrics via `prom-client` and `node-rdkafka-prometheus` are extensively instrumented. Structured logging via `werelogs` exists across all components. Grafana dashboards and Prometheus alerts are defined in `monitoring/`.
- **What it enables:** An agent that queries Prometheus metrics, traces Kafka consumer lag, correlates replication/lifecycle alert firings, and suggests root causes for backlog growth or latency spikes.
- **Additional steps:** Deploy Prometheus/Grafana with query API access; add distributed trace ID propagation (currently absent) for deeper correlation.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute). Supporting conditions: APP-Q4=3 (meets threshold — not a trigger) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but Dockerfile exists — containerization already in progress. Contextual guard: container definitions found. |
| 3 | Move to Open Source | Not Triggered | — | — | MongoDB and Redis are already open-source engines. No commercial DB engines detected. DATA-Q4=4. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (all databases self-managed), DATA-Q3=2 (no engine version pinning in IaC) |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4=2 (self-managed Kafka), evidence of data processing workloads (event-processor archetype with Kafka streaming) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), INF-Q11=2 (partial CI/CD), OPS-Q5=1 (no deployment strategy). Supporting conditions: OPS-Q6=3 (meets threshold — not a trigger) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context: "replication, lifecycle, metadata workflows" — no AI signal terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Backbeat is a single deployable monolith (one Dockerfile, one `package.json`) with an extensible plugin architecture (`extensions/`). All extensions (replication, lifecycle, GC, notification, ingestion, oplog populator) are packaged together and share the same process runtime, MongoDB connection pool, Redis client, Kafka consumer infrastructure, and Zookeeper coordination layer.

**Compute Model Gaps:** No managed compute orchestration defined. The Dockerfile produces a container image, but no EKS, ECS, Fargate, or Lambda definitions exist in the repository.

**Communication Pattern Gaps:** The event-driven Kafka-based architecture is architecturally sound for the archetype. However, all processors are co-located in a single deployment unit, limiting independent scaling of hot-path processors (e.g., replication data processor vs lifecycle object processor).

**Recommended Decomposition Approach:** See Decomposition Strategy section below. Strangler Fig extraction of individual extension processors into independently deployable EKS services is recommended, with Amazon MSK (preferred over self-managed Kafka) as the shared event backbone and Amazon EventBridge for cross-service coordination.

**Representative AWS Services:** Amazon EKS (preferred), Amazon MSK, Amazon EventBridge, AWS Step Functions, Amazon API Gateway

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing

**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** MongoDB is self-managed as a 3-node replica set (`localhost:27017,27018,27019` in `conf/config.json`). Redis is self-managed (`localhost:6379`). No IaC defines either database — they are provisioned manually or via external tooling not present in this repository.

**Engine Versions and EOL Status:** MongoDB driver version is `^6.11.0` (package.json), but the actual MongoDB server engine version is not pinned in any configuration within this repository. Redis engine version is similarly unspecified.

**Data Access Patterns:** MongoDB access is partially centralized through `extensions/utils/MongoUtils.js` for connection string construction, but `MongoClient` instances are created directly in `BackbeatAPI.js` and lifecycle extensions. Redis access uses `ioredis` and Arsenal's `RedisClient` wrapper.

**Recommended Managed Database Targets:**
- **MongoDB → Amazon DocumentDB** (MongoDB-compatible) or **Amazon DynamoDB** (preferred per technology preferences) for metadata storage. DynamoDB's event-driven integration with DynamoDB Streams could replace some Kafka-based change data capture patterns.
- **Redis → Amazon ElastiCache for Redis** or **Amazon MemoryDB for Redis** for metrics/caching with automated failover and backup.

**Representative AWS Services:** Amazon DocumentDB, Amazon DynamoDB (preferred), Amazon ElastiCache, Amazon MemoryDB

**Migration Tools:** AWS Database Migration Service (DMS), AWS Schema Conversion Tool (SCT)

**AWS Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Streaming/Messaging Infrastructure:** Apache Kafka is self-managed via `node-rdkafka` (v2.12.0). Kafka hosts are configured as `127.0.0.1:9092` with no managed service wrapper. The system uses 15+ Kafka topics for replication, lifecycle, GC, notification, metrics, and cold storage workflows. Apache ZooKeeper is self-managed for Kafka coordination and Backbeat's own distributed state management.

**Data Processing Workloads:** This is an event-processor archetype with substantial data processing: replication queue processing, lifecycle bucket/object processing, garbage collection, notification processing, and oplog population. All processing is Kafka-driven.

**Recommended Managed Analytics Targets:**
- **Kafka → Amazon MSK** (preferred over self-managed Kafka per technology preferences — `avoid: ["self-managed-kafka"]`). MSK Serverless for variable workloads or MSK Provisioned for predictable throughput.
- **ZooKeeper coordination → Amazon MSK** (handles ZooKeeper internally in KRaft mode) plus **Amazon EventBridge** (preferred) for cross-service event routing.

**Representative AWS Services:** Amazon MSK, Amazon EventBridge (preferred), Amazon Kinesis Data Streams

**AWS Prescriptive Guidance:** [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** No IaC files found (no Terraform, CloudFormation, CDK, Helm charts, or Kubernetes manifests). All infrastructure (Kafka, MongoDB, Redis, ZooKeeper, compute) is provisioned outside this repository — likely manually or via separate tooling.

**Current CI/CD State:** GitHub Actions workflows exist for:
- `tests.yaml` — Lint, unit tests, functional tests with service containers (Kafka, MongoDB, Redis, ZooKeeper)
- `docker-build.yaml` — Docker image build and push to GHCR, plus dashboard/policy artifact publishing
- `release.yaml` — Manual workflow_dispatch release with Docker build and GitHub Release creation
- `alerts.yaml` — Prometheus alert rule testing

No deployment automation exists — images are built and pushed but not deployed to any environment. No canary, blue/green, or rolling deployment configuration. Legacy `circle.yml` exists but appears to be superseded by GitHub Actions.

**Deployment Strategy Gaps:** No deployment strategy — Docker images are pushed to GHCR registry with no automated deployment to staging/production.

**Testing Gaps:** Unit tests and functional tests run in CI with service containers. Integration tests exist (`tests/functional/`) and run in the pipeline. No end-to-end deployment testing. Code coverage tracked via Codecov with component-level coverage targets.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK or Terraform for defining EKS clusters, MSK clusters, DocumentDB/DynamoDB, ElastiCache, networking, and monitoring infrastructure
- **CI/CD:** Enhance GitHub Actions with deployment stages targeting EKS via `kubectl`/Helm; add canary deployment via Argo Rollouts or AWS CodeDeploy
- **Deployment:** ArgoCD or Flux for GitOps-based Kubernetes deployments (preferred with EKS)

**Representative AWS Services:** AWS CDK, Amazon EKS, AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy

**AWS Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

---

## Decomposition Strategy

APP-Q2 scored 2 — Backbeat is a monolith with identifiable modules (extensions) but shared database connections, Redis clients, and Kafka infrastructure across all extensions.

### Recommended Approach: Strangler Fig (Parallel Track)

**Rationale:** Backbeat's extension architecture provides clear module boundaries (replication, lifecycle, GC, notification, ingestion, oplog populator). Each extension has its own Kafka topics, consumer groups, and processing logic. The extension plugin system (`extensions/index.js`) already defines clean entry points. This makes Strangler Fig extraction feasible — each extension can be extracted into an independently deployable service behind the shared Kafka/MSK backbone.

**Approach:**
1. **Phase 1 — Containerize and Deploy to EKS:** Deploy the current monolith as-is on Amazon EKS (preferred). Establish IaC, CI/CD pipeline, and observability baseline.
2. **Phase 2 — Extract Hot-Path Extensions:** Start with the highest-scale extension (replication queue processor) as a separate EKS deployment with its own scaling configuration. Place an Anti-corruption Layer between it and the shared MongoDB/Redis connections.
3. **Phase 3 — Progressive Extraction:** Extract lifecycle processors, notification processor, and GC processor as independent services. Each consumes from dedicated Kafka/MSK topics.
4. **Phase 4 — Shared Services Modernization:** Migrate shared MongoDB to Amazon DocumentDB or DynamoDB. Migrate Redis to ElastiCache. Migrate Kafka to Amazon MSK.

**Estimated Effort:** 6–12 months for Phases 1–3; Phase 4 can run in parallel.

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted extension services from the monolith's shared MongoDB/Redis connections | Every extraction — translate between shared and service-owned data models |
| **Saga Pattern** | Manage distributed transactions for replication workflows that span multiple services | Replication status updates that coordinate between data processor and status processor |
| **Event Sourcing** | Capture all replication/lifecycle state changes as events on Kafka/MSK topics | Already partially implemented — Kafka topics serve as event logs. Formalize the pattern. |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters | Every new service — decouple business logic from Kafka/MongoDB/Redis infrastructure |

### Effort Estimation

| Factor | Current State | Effort Signal |
|--------|---------------|---------------|
| Module boundaries | Clear extension directories with dedicated topics and consumer groups | Low — good extraction boundaries |
| Data coupling | Shared MongoDB connection pool, shared Redis client across extensions | Medium — need to separate data access per service |
| Stored procedures | None — all business logic in Node.js application layer | Low — no database migration blockers |
| Communication patterns | Kafka-driven async already in place | Low — event backbone exists |
| CI/CD maturity | GitHub Actions for build/test, no deployment automation | Medium — need to add deployment pipeline |
| Test coverage | Unit + functional tests with CI integration | Low — regression testing support exists |

---

<!-- SECTION 8: DETAILED FINDINGS -->
## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | A Dockerfile exists (`Dockerfile`) building a Node.js 22 container image with a multi-stage build. Docker images are built and pushed to GHCR via GitHub Actions (`docker-build.yaml`). However, no IaC defines where or how this container runs — no Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, no Kubernetes manifests, no Helm charts, and no CloudFormation templates exist in the repository. The `docker-entrypoint.sh` configures the application via environment variables, suggesting container-based deployment, but the deployment target is not defined in code. |
| **Gap** | Container image exists but no managed compute orchestration (EKS, ECS, Fargate, Lambda) is defined. Compute provisioning is entirely outside this repository. |
| **Recommendation** | Define compute infrastructure in IaC. Given technology preferences (`prefer: ["eks"]`), deploy Backbeat on Amazon EKS with Helm charts defining Deployment, Service, and HPA resources for each processor type. Avoid self-managed Kubernetes (`avoid: ["self-managed-kubernetes"]`). |
| **Evidence** | `Dockerfile`, `.github/workflows/docker-build.yaml`, `docker-entrypoint.sh` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | MongoDB is self-managed as a 3-node replica set (`localhost:27017,27018,27019` in `conf/config.json`). Redis is self-managed (`localhost:6379`). No IaC defines managed database resources — no `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, or `aws_elasticache_*` resources exist. The `docker-entrypoint.sh` accepts `MONGODB_HOSTS`, `REDIS_HOST`, and `REDIS_SENTINELS` environment variables for external database endpoints, confirming deployment-time database configuration but no managed service integration. Connection logic in `extensions/utils/MongoUtils.js` and `lib/api/BackbeatAPI.js` connects directly to MongoDB replica sets. |
| **Gap** | All databases (MongoDB, Redis) are self-managed with manual patching, backup, and scaling responsibility. No managed database services in use. |
| **Recommendation** | Migrate MongoDB to Amazon DocumentDB (MongoDB-compatible) or Amazon DynamoDB (preferred per preferences). Migrate Redis to Amazon ElastiCache for Redis or Amazon MemoryDB with automated failover. Define database infrastructure in IaC. |
| **Evidence** | `conf/config.json`, `extensions/utils/MongoUtils.js`, `lib/api/BackbeatAPI.js`, `docker-entrypoint.sh` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Backbeat coordinates multi-step workflows through Kafka topic chains and Zookeeper state management. Replication workflows span queue populator → data processor → status processor across dedicated Kafka topics (`backbeat-replication`, `backbeat-data-mover`, `backbeat-replication-status`, `backbeat-replication-failed`). Lifecycle workflows use `backbeat-lifecycle-bucket-tasks`, `backbeat-lifecycle-object-tasks`, and `backbeat-lifecycle-transition-tasks`. Retry logic is implemented with configurable `maxRetries`, `timeoutS`, and exponential backoff in application code (`conf/config.json` retry sections). However, no dedicated workflow orchestration service (Step Functions, Temporal, Camunda) coordinates these multi-step pipelines — orchestration is embedded in the application code and Kafka topic chain design. |
| **Gap** | Multi-step event processing (replication and lifecycle pipelines) is ad hoc in handler code — retry logic, error handling, and state transitions are implemented per-extension in JavaScript with no dedicated orchestrator. For the event-processor archetype, this represents moderate effort needed. |
| **Recommendation** | Adopt AWS Step Functions for multi-step lifecycle and replication orchestration workflows. Step Functions Express Workflows can coordinate bucket/object processing with built-in retry, error handling, and visual state management. Use Amazon EventBridge (preferred) Pipes for event-driven orchestration. |
| **Evidence** | `conf/config.json` (retry configurations), `lib/BackbeatConsumer.js` (consumer processing logic), `extensions/replication/queueProcessor/`, `extensions/lifecycle/conductor/` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kafka is the primary message broker via `node-rdkafka` (v2.12.0) with 15+ topics for replication, lifecycle, GC, notification, metrics, and cold storage workflows. `BackbeatConsumer.js` and `BackbeatProducer.js` are core library components implementing sophisticated consumer patterns (ordered processing, circuit breaker, offset management, backlog metrics). ZooKeeper (`node-zookeeper-client` v1.1.3) provides distributed coordination. Both Kafka and ZooKeeper are self-managed — no `aws_msk_*`, `aws_sqs_*`, `aws_kinesis_*`, or `aws_eventbridge_*` resources exist. For the event-processor archetype, having a managed event source is the correct Score 4 design — self-managed Kafka is a Score 2. |
| **Gap** | Self-managed Kafka broker is the primary event source — operational burden includes patching, scaling, monitoring, and ZooKeeper coordination management. This conflicts with technology preferences (`avoid: ["self-managed-kafka"]`). |
| **Recommendation** | Migrate from self-managed Kafka to Amazon MSK (Managed Streaming for Apache Kafka). MSK Serverless eliminates cluster sizing; MSK Provisioned offers fine-grained control. Replace ZooKeeper coordination with MSK's KRaft mode. Use Amazon EventBridge (preferred) for cross-service event routing where topic-based pub/sub is not required. |
| **Evidence** | `package.json` (node-rdkafka, node-zookeeper-client), `lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js`, `conf/config.json` (kafka hosts, zookeeper connection) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation definitions exist in the repository. No IaC of any kind defines networking infrastructure. The `conf/config.json` references `127.0.0.1` for all service endpoints (Kafka, ZooKeeper, MongoDB, Redis, S3, Vault), and `docker-entrypoint.sh` accepts external endpoints via environment variables. The `BackbeatServer.js` IP allowlist (`healthChecks.allowFrom: ["127.0.0.1/8", "::1"]`) provides basic application-level access control but no network-layer segmentation. |
| **Gap** | No network security infrastructure defined. Services may be deployed without VPC isolation, private subnets, or least-privilege security groups. |
| **Recommendation** | Define VPC infrastructure in IaC with private subnets for all Backbeat processors, MongoDB, Redis, and Kafka. Use security groups with least-privilege rules. Deploy Amazon VPC endpoints for AWS service access. Consider VPC Lattice for service-to-service communication. |
| **Evidence** | `conf/config.json`, `docker-entrypoint.sh`, `lib/api/BackbeatServer.js` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The HTTP API (port 8900) is served directly by `BackbeatServer.js` using Node.js `http.createServer()`. No API Gateway, ALB, CloudFront, or AppSync is configured as the entry point. The server implements basic IP allowlist checking via Arsenal's `ipCheck` module but no throttling, request validation, or auth offloading at the infrastructure level. The `Dockerfile` exposes port 8900 directly. |
| **Gap** | API surface exposed directly with no managed entry point — no throttling, no infrastructure-level auth, no traffic management, no TLS termination at the edge. |
| **Recommendation** | Deploy Amazon API Gateway (preferred per preferences) in front of the Backbeat API. Configure throttling, request validation, and API key management. For internal-only APIs, use VPC Lattice or an internal ALB with health checks. |
| **Evidence** | `lib/api/BackbeatServer.js`, `Dockerfile` (EXPOSE 8900) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists in the repository. No `aws_autoscaling_*`, `aws_appautoscaling_*`, Kubernetes HPA, or KEDA scaler definitions found. The `BackbeatConsumer.js` has configurable `concurrency` (default from constants) for per-instance parallelism, but cluster-level scaling is not defined. The `DESIGN.md` mentions "multiple instances per site" but scaling is manual. |
| **Gap** | All capacity is statically provisioned — no auto-scaling for compute, databases, or Kafka consumer groups. Replication and lifecycle workloads have variable load patterns that would benefit from dynamic scaling. |
| **Recommendation** | When deployed on EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on Kafka consumer lag metrics (available via `prom-client` and `node-rdkafka-prometheus`). Use KEDA with Kafka scaler for event-driven autoscaling of consumer pods. Configure DynamoDB auto-scaling if migrating from MongoDB. |
| **Evidence** | `DESIGN.md`, `lib/BackbeatConsumer.js` (concurrency config), `lib/constants.js` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists in the repository. No `aws_backup_plan`, `backup_retention_period`, `point_in_time_recovery`, S3 versioning, or EBS snapshot lifecycle policies are defined. MongoDB and Redis are self-managed with no backup automation visible in this codebase. The `conf/config.json` defines MongoDB with `writeConcern: "majority"` for durability but no backup strategy. |
| **Gap** | No backup configuration for any data store. MongoDB metadata and Redis state have no automated backup, no defined retention periods, and no tested restore procedures. |
| **Recommendation** | When migrating to managed databases: enable automated backups on Amazon DocumentDB/DynamoDB with PITR. Configure AWS Backup plans for all production data stores. For the interim period with self-managed MongoDB, implement automated backup scripts with defined retention. |
| **Evidence** | `conf/config.json` (MongoDB writeConcern), absence of backup configurations |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | `DESIGN.md` states: "Multiple instances per site for high availability. If an instance dies, the queue replica from another instance can be used to process records." MongoDB is configured as a 3-node replica set (`replicaSetHosts: "localhost:27017,localhost:27018,localhost:27019"`) providing data-layer redundancy. Redis supports Sentinel configuration (`REDIS_SENTINELS` in `docker-entrypoint.sh`). Kafka consumer groups inherently support multi-instance consumption with partition rebalancing (`BackbeatConsumer.js` implements rebalance handling). However, no IaC confirms multi-AZ deployment — all subnet and AZ configuration is absent. |
| **Gap** | HA is architecturally designed (replica sets, Kafka consumer groups, Sentinel support) but no IaC confirms multi-AZ deployment. AZ fault isolation is not explicit. |
| **Recommendation** | Define multi-AZ deployment in IaC. When deployed on EKS (preferred), configure pod anti-affinity rules and topology spread constraints across AZs. Deploy managed databases (DocumentDB, ElastiCache) with Multi-AZ enabled. |
| **Evidence** | `DESIGN.md`, `conf/config.json` (MongoDB replica set), `docker-entrypoint.sh` (Redis Sentinel support), `lib/BackbeatConsumer.js` (rebalance handling) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files exist in the repository. No Terraform (`.tf`), CloudFormation (`*.cfn.*`), CDK (`cdk.json`), Helm charts (`Chart.yaml`), Kustomize (`kustomization.yaml`), or Kubernetes manifests were found. All infrastructure — compute, networking, databases (MongoDB, Redis), messaging (Kafka, ZooKeeper), and operational resources — is created outside this repository with no code-defined specifications. The legacy `circle.yml` and current GitHub Actions workflows handle CI/CD only, not infrastructure provisioning. |
| **Gap** | 0% IaC coverage — all infrastructure is manually created (ClickOps) or managed by external systems not present in this repository. This blocks reproducible deployments, environment consistency, and disaster recovery. |
| **Recommendation** | Adopt IaC for all infrastructure. Use AWS CDK (TypeScript, aligned with team's JavaScript/Node.js expertise) or Terraform to define EKS clusters, MSK clusters, DocumentDB/DynamoDB, ElastiCache, VPC networking, and monitoring infrastructure. Start with compute and networking, then extend to databases and messaging. |
| **Evidence** | Absence of `.tf`, `*.cfn.*`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files across the entire repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions workflows provide partial CI/CD automation: (1) `tests.yaml` — runs lint, unit tests (with Kafka/MongoDB/Redis/ZooKeeper service containers), functional tests across 8 test suites, performance tests, and queue-populator integration tests with Docker Compose. (2) `docker-build.yaml` — builds Docker image, federation image, and publishes monitoring dashboards and IAM policies as OCI artifacts to GHCR. (3) `release.yaml` — manual `workflow_dispatch` that triggers Docker build and creates a GitHub Release with auto-generated release notes. (4) `alerts.yaml` — tests Prometheus alert rules for replication, lifecycle, notification, and oplog-populator. Build and test are automated, but **deployment is manual** — no deployment stage exists. No IaC pipeline exists (no IaC to deploy). Legacy `circle.yml` is superseded by GitHub Actions. |
| **Gap** | Build is automated but deployment is manual. No deployment automation for any environment. No IaC pipeline. Release process requires manual workflow_dispatch. |
| **Recommendation** | Add deployment stages to GitHub Actions pipeline targeting EKS (preferred). Implement GitOps with ArgoCD or Flux for continuous deployment. Add IaC deployment pipeline (CDK deploy or Terraform apply) with plan/review/apply stages. Automate release tagging with semantic versioning. |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/docker-build.yaml`, `.github/workflows/release.yaml`, `.github/workflows/alerts.yaml`, `circle.yml` (legacy) |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | JavaScript/Node.js >=20 (engines field in `package.json`), with `Dockerfile` using Node.js 22.14.0. AWS SDK v3 is in use: `@aws-sdk/client-s3` v3.921.0, `@aws-sdk/client-sts` v3.921.0, `@aws-sdk/client-iam` v3.921.0, `@aws-sdk/credential-providers` v3.921.0, `@smithy/node-http-handler` v3.3.3. Modern dependency ecosystem with `joi` for validation, `ioredis` v5.4.2, `mongodb` v6.11.0, `prom-client` v15.1.3. ESLint v9 with Airbnb config for code quality. TypeScript types available (`@types/node` v20 in devDependencies). Testing with `mocha` v11, `sinon` v10, and `c8` for coverage. |
| **Gap** | No significant gaps — modern Node.js version with current AWS SDK v3 and mature ecosystem. |
| **Recommendation** | Continue maintaining current Node.js LTS cadence. Consider TypeScript migration for type safety on critical paths (credentials, configuration, API contracts). |
| **Evidence** | `package.json` (engines, dependencies), `Dockerfile` (NODE_VERSION=22.14.0) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Backbeat is a single deployable unit — one `Dockerfile`, one `package.json`, one container image. It has identifiable modules via the `extensions/` directory: replication, lifecycle, GC, notification, ingestion, oplog populator, and mongo processor. Each extension has dedicated Kafka topics and consumer groups. However, all extensions share: (1) MongoDB connection pool (created in `BackbeatAPI.js`), (2) Redis client (`ioredis`), (3) ZooKeeper coordination layer, (4) Kafka consumer/producer infrastructure, and (5) the same process runtime and Node.js event loop. The `docker-entrypoint.sh` runs a single process selected by the command argument (`node bin/queuePopulator.js`, `node extensions/replication/queueProcessor/task.js`, etc.), but all code is packaged together. Cross-extension dependencies exist through shared libraries in `lib/`. |
| **Gap** | Monolith with identifiable modules but shared database connections, Redis clients, and Kafka infrastructure. Extensions cannot be independently deployed, scaled, or versioned. |
| **Recommendation** | Begin Strangler Fig decomposition by extracting high-traffic extensions (replication processor, lifecycle processors) into independently deployable EKS services. See Decomposition Strategy section. |
| **Evidence** | `Dockerfile`, `package.json`, `extensions/index.js`, `docker-entrypoint.sh`, `lib/api/BackbeatAPI.js` (shared MongoDB/Redis), `conf/config.json` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | As an event-processor archetype, the primary input is asynchronous via Kafka topics. `BackbeatConsumer.js` consumes from Kafka with ordered processing, circuit breaker protection, and offset management. `BackbeatProducer.js` publishes to downstream topics. Inter-component communication is entirely Kafka-driven: queue populator → replication topic → queue processor → status topic → status processor. Outbound calls to S3 (for data replication) and Vault (for credentials) are synchronous HTTP but are appropriate for the event-processing context — they are called within async event handlers. The HTTP API surface (port 8900) handles synchronous management requests but is not the primary workload path. |
| **Gap** | None for this archetype. Async input via Kafka is the correct design for event-processor. Synchronous outbound calls to S3 and Vault are appropriate within event handlers. |
| **Recommendation** | No change recommended for async/sync ratio. When migrating Kafka to Amazon MSK, maintain the event-driven architecture. Consider EventBridge for management/coordination events where topic granularity is not needed. |
| **Evidence** | `lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js`, `conf/config.json` (Kafka topic definitions), `extensions/replication/queueProcessor/` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Event handlers are async by design — Kafka consumers process messages asynchronously with configurable concurrency and timeout (`maxPollIntervalMs` defaults to 300000ms/5min in `BackbeatConsumer.js`). Long-running replication and lifecycle processing within handlers use retry with exponential backoff (configurable `maxRetries`, `timeoutS`, `backoff` in `conf/config.json`). The `BackbeatConsumer.js` implements a circuit breaker pattern (`breakbeat` library) that pauses consumption when downstream services are unhealthy. Slow task detection is instrumented (`_startProcessingTask` logs and tracks slow tasks exceeding `maxPollIntervalMs`). Rebalance timeout handling ensures stuck tasks trigger consumer disconnect for process restart. However, there is no formal checkpointing or sub-workflow pattern for very long replication operations — a handler that exceeds timeout without completing loses processing state. |
| **Gap** | Most handlers are safely bounded with timeout and retry, but a few may exceed timeout without checkpointing — processing can be lost on retry for very large objects. |
| **Recommendation** | Implement checkpointing for large object replication (multi-part upload progress tracking). Consider AWS Step Functions for long-running lifecycle transitions that span cold storage archive/restore operations. |
| **Evidence** | `lib/BackbeatConsumer.js` (maxPollIntervalMs, circuit breaker, slow task detection), `conf/config.json` (retry configurations), `lib/CircuitBreaker.js` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The `lib/api/routes.js` defines routes under the `/_/` prefix (e.g., `/_/healthcheck`, `/_/metrics/crr/<location>/backlog`) with no version segment (no `/v1/`, `/v2/` paths). No OpenAPI or Swagger specification files exist. No version headers or query parameter versioning detected. Route matching in `BackbeatAPI.js` uses extension names and categories but no version differentiation. The API returns JSON responses but with no versioned schema. |
| **Gap** | No API versioning — breaking changes would affect all consumers simultaneously. No API specification document for contract documentation. |
| **Recommendation** | Introduce URL-path versioning (e.g., `/_/v1/metrics/...`). Create an OpenAPI specification for the Backbeat API to document endpoints, request/response schemas, and support API Gateway integration. |
| **Evidence** | `lib/api/routes.js`, `lib/api/BackbeatAPI.js`, `lib/api/BackbeatRequest.js` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables in `docker-entrypoint.sh`: `KAFKA_HOSTS`, `ZOOKEEPER_CONNECTION_STRING`, `MONGODB_HOSTS`, `REDIS_HOST`/`REDIS_SENTINELS`, `CLOUDSERVER_HOST`/`CLOUDSERVER_PORT`, and various extension-specific endpoints. This provides deployment-time flexibility over hardcoded values. The `conf/config.json` contains default localhost endpoints that are overridden by environment variables at container startup. Replication destination sites are configured via `EXTENSIONS_REPLICATION_DEST_BOOTSTRAPLIST`. No dynamic service discovery mechanism (AWS Cloud Map, Consul, Istio) is used. |
| **Gap** | Environment variables for endpoints but no dynamic service discovery. Endpoint changes require container restart. |
| **Recommendation** | When deployed on EKS, use Kubernetes DNS for intra-cluster service discovery. For cross-cluster or external service endpoints, adopt AWS Cloud Map or use Kubernetes ExternalName services. |
| **Evidence** | `docker-entrypoint.sh`, `conf/config.json`, `lib/Config.js` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Backbeat's primary function is managing S3 object replication and lifecycle. It interacts with S3 extensively via `@aws-sdk/client-s3` v3 for object data operations (GET/PUT for replication, DELETE for lifecycle expiration, transition for storage class changes). S3 is the source and destination data store for all object data. The system handles multipart uploads, large object replication, and cold storage archive/restore operations. However, Backbeat does not implement parsing pipelines (no Textract, Tika) over the unstructured data — it replicates and manages objects without content analysis. |
| **Gap** | Data in S3 (correct storage) but no automated parsing or extraction pipeline for the replicated objects. This is expected for a replication engine — content parsing is not Backbeat's responsibility. |
| **Recommendation** | No immediate action for Backbeat itself. If content analysis of replicated objects is needed, integrate Amazon Textract or Amazon Comprehend downstream of the replication pipeline. |
| **Evidence** | `package.json` (`@aws-sdk/client-s3`), `extensions/replication/`, `extensions/lifecycle/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MongoDB access is partially centralized: `extensions/utils/MongoUtils.js` provides `constructConnectionString()` for building connection URLs, and `getMongoVersion()` for version detection. However, `MongoClient` instances are created directly in multiple locations — `BackbeatAPI.js` creates its own `MongoClient` in `_setupMongoClient()`, and lifecycle extensions create separate connections. Redis access uses `ioredis` directly in `BackbeatAPI.js` (`new Redis(this._redisConfig)`) and Arsenal's `RedisClient` wrapper for stats operations. ZooKeeper access is centralized through `lib/clients/ZookeeperManager.js`. There is a repository/DAO pattern in some modules (e.g., `LocationStatusManager` for location status) but inconsistent across the codebase — data access logic is mixed into API handlers and extension processors. |
| **Gap** | Repository/DAO pattern in some modules but inconsistent across the codebase. MongoDB and Redis clients are created in multiple locations with no single data access layer. |
| **Recommendation** | Centralize all database access through dedicated client modules in `lib/clients/`. Create a `MongoClientManager` that provides a shared connection pool and `RedisClientManager` for Redis connections. This will also ease migration to managed databases (DocumentDB, ElastiCache). |
| **Evidence** | `extensions/utils/MongoUtils.js`, `lib/api/BackbeatAPI.js` (MongoDB and Redis client creation), `lib/clients/ZookeeperManager.js`, `lib/util/LocationStatusManager.js` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The MongoDB Node.js driver is pinned to `^6.11.0` in `package.json`, and the test CI uses a custom MongoDB image (`ghcr.io/scality/backbeat/ci-mongodb`) built from `.github/dockerfiles/mongodb/Dockerfile` — the actual MongoDB server engine version is not pinned in any configuration within this repository. No IaC defines MongoDB resources with engine version parameters. Redis version is similarly unspecified — the test CI uses `redis:alpine` without version pinning. The `extensions/utils/MongoUtils.js` includes a `getMongoVersion()` function, suggesting version awareness at runtime but no governance over which version is deployed. |
| **Gap** | Some versions partially specified (driver in package.json, test images in CI), but actual production database engine versions are not pinned in any configuration. EOL status is unknown — no documented version-update procedure. |
| **Recommendation** | Pin MongoDB server engine version in deployment configuration (e.g., Helm values or IaC). Document version-update procedure covering downtime windows, rollback, and compatibility testing. When migrating to managed databases, engine versions are managed by AWS with clear EOL timelines. |
| **Evidence** | `package.json` (mongodb ^6.11.0), `.github/workflows/tests.yaml` (ci-mongodb image), `extensions/utils/MongoUtils.js` (getMongoVersion) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL/NoSQL constructs are used. All business logic resides in the Node.js application layer. MongoDB is used for metadata storage with standard CRUD operations via the `mongodb` driver (find, insert, update, delete). No aggregation framework abuse, no server-side JavaScript (`$where` clauses), and no MongoDB triggers detected. Redis is used for caching, metrics, and sorted set operations — all via standard commands (GET, SET, ZRANGE, ZSCORE, ZREM). The data layer is clean and portable. |
| **Gap** | None — all business logic in application layer with no database-coupled logic. |
| **Recommendation** | Maintain current pattern. This clean separation enables straightforward database migration (MongoDB → DocumentDB/DynamoDB, Redis → ElastiCache) without logic extraction. |
| **Evidence** | `lib/api/BackbeatAPI.js` (MongoDB/Redis operations), `extensions/utils/MongoUtils.js`, `lib/util/sortedSetHelper.js` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration exists (no IaC to define it). Application-level structured logging is implemented via `werelogs` (Scality's logging library) with configurable log levels (`info`, `debug`, `trace` in `conf/config.json`). Request logging exists in `BackbeatServer.js` (`_logRequestEnd` captures clientIp, httpMethod, httpURL, httpCode). However, this is application logging, not audit logging — no immutable log storage, no log file validation, and no centralized audit trail for compliance. |
| **Gap** | No CloudTrail audit logging. Application logs provide operational visibility but not compliance-grade audit trails with immutability guarantees. |
| **Recommendation** | Enable CloudTrail with log file validation and immutable storage (S3 Object Lock) for all AWS API calls. Centralize application logs with CloudWatch Logs or Amazon OpenSearch Service with retention policies. |
| **Evidence** | `conf/config.json` (log configuration), `lib/api/BackbeatServer.js` (`_logRequestEnd`), `package.json` (werelogs dependency) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Surface gate: `has_at_rest_data_surface=true` (MongoDB stores metadata). No KMS encryption configuration exists. No `kms_key_id` on any data store, no `aws_kms_key` resources (no IaC exists). The `conf/config.json` includes `certFilePaths` for TLS (key, cert, ca) suggesting encryption in transit capability, but no encryption at rest. MongoDB and Redis are self-managed with no visible encryption-at-rest configuration. No S3 bucket encryption defaults are defined. |
| **Gap** | No encryption at rest configured for any data store. MongoDB metadata and Redis cache data are unencrypted at rest. |
| **Recommendation** | When migrating to managed databases, enable encryption at rest with customer-managed KMS keys: DocumentDB KMS encryption, ElastiCache encryption at rest, S3 default bucket encryption with SSE-KMS. Define key rotation policies. |
| **Evidence** | `conf/config.json` (certFilePaths — transit only), absence of KMS configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The system uses Scality Vault for authentication — `vaultclient` dependency provides credential validation and service account management. Auth types supported include `service` (provisioned service accounts), `account` (static file accounts from `conf/authdata.json`), `role` (assume role for cross-account replication), and `assumeRole` (STS-style temporary credentials via `@aws-sdk/client-sts`). `lib/credentials/RoleCredentials.js` implements STS AssumeRole for temporary credential acquisition. However, the Backbeat HTTP API (port 8900) uses only IP allowlist checking (`healthChecks.allowFrom` in `BackbeatServer.js`) — no OAuth2/JWT, no API keys, no token-based auth on the management API endpoints. Authentication is applied to S3/Vault interactions but not to the Backbeat API itself. |
| **Gap** | API key or static credential authentication without token-based auth on the management API. The S3 replication path uses proper credential management (AssumeRole, Vault), but the management API relies solely on network-level IP allowlisting. |
| **Recommendation** | Add token-based authentication (JWT/OAuth2) to the Backbeat management API. When fronted by Amazon API Gateway (preferred), use API Gateway authorizers with Cognito or IAM authentication. |
| **Evidence** | `lib/credentials/AccountCredentials.js`, `lib/credentials/RoleCredentials.js`, `lib/api/BackbeatServer.js` (IP allowlist), `conf/config.json` (auth sections) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The system uses Scality Vault as its identity provider for S3-compatible authentication. `vaultclient` dependency provides integration with Vault's admin API (port 8500/8600 in `conf/config.json`). Service accounts are provisioned through Vault (`ProvisionedServiceAccountCredentials` in `AccountCredentials.js`). However, Vault is Scality's proprietary identity service — not a standard centralized IdP (no Cognito, OIDC, SAML, Okta integration). The system can federate with AWS IAM via AssumeRole (`RoleCredentials.js` uses `@aws-sdk/client-sts`) but this is specific to replication authentication, not general application identity. |
| **Gap** | Application uses Scality Vault for auth but can federate with AWS IAM for specific operations. No standard centralized IdP integration (Cognito, OIDC, SAML). |
| **Recommendation** | When migrating to AWS-native services, integrate with Amazon Cognito for user/service identity management. Use IAM roles for service-to-service authentication. Implement OIDC federation for the management API. |
| **Evidence** | `lib/credentials/AccountCredentials.js`, `lib/credentials/RoleCredentials.js`, `conf/config.json` (vaultAdmin config), `package.json` (vaultclient) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | `conf/authdata.json` contains plaintext sample credentials: `"access": "accessKey1", "secret": "verySecretKey1"` and `"access": "accessKey2", "secret": "verySecretKey2"`. While these appear to be sample/development credentials, the file is committed to version control. The `docker-entrypoint.sh` accepts credentials via environment variables but no Secrets Manager or Vault integration for secret rotation. `conf/config.json` includes plaintext ingestion source credentials (`"accessKey": "myAccessKey", "secretKey": "myEncryptedSecretKey"`). The `AccountCredentials.js` loads credentials from either the static file (`conf/authdata.json`) or from Scality's management service — no AWS Secrets Manager integration. The `S3AUTH_CONFIG` environment variable allows overriding the auth file path but doesn't change the secret storage mechanism. |
| **Gap** | Plaintext credentials present in version-controlled configuration files (`conf/authdata.json`, `conf/config.json`). No AWS Secrets Manager or HashiCorp Vault for secret management. No rotation configured. Score 1 applies because plaintext secrets exist in the repository regardless of whether they are sample data. |
| **Recommendation** | Remove all plaintext credentials from version control immediately. Migrate to AWS Secrets Manager for all production credentials with automated rotation. Use IAM roles and IRSA (IAM Roles for Service Accounts) on EKS to eliminate static credentials entirely. Reference secrets via environment variables backed by Kubernetes Secrets or ExternalSecrets Operator. |
| **Evidence** | `conf/authdata.json` (plaintext access/secret keys), `conf/config.json` (ingestion source credentials), `lib/credentials/AccountCredentials.js` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Dockerfile uses a multi-stage build with `node:22.14.0-bookworm-slim` base image — a Debian-based slim image. It installs `tini` for proper signal handling and `ca-certificates` for TLS. However: (1) The container runs as root — no `USER` directive to drop privileges. (2) No vulnerability scanning (no AWS Inspector, Snyk, or Trivy) is configured in the CI pipeline or Dockerfile. (3) No hardened base image (not CIS-benchmarked, not Bottlerocket). (4) No SSM Patch Manager configuration (no IaC). (5) `AWS_SDK_JS_SUPPRESS_MAINTENANCE_MODE_MESSAGE=1` is set, suggesting awareness of SDK v2 deprecation. The builder stage installs build tools (gcc, python3, git) but these are not present in the final image due to multi-stage build — good practice. |
| **Gap** | Default base image with no hardening. Container runs as root. No vulnerability scanning in CI/CD. |
| **Recommendation** | Add a `USER node` directive to the Dockerfile to run as non-root. Integrate container image scanning (Amazon ECR image scanning, Trivy, or Snyk) into the Docker build pipeline. Consider Distroless or Bottlerocket base images for reduced attack surface. |
| **Evidence** | `Dockerfile` (base image, no USER directive, multi-stage build), `.github/workflows/docker-build.yaml` (no scanning step) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are configured in the CI/CD pipeline. No Dependabot configuration file (`.github/dependabot.yml`), no Snyk policy (`.snyk`), no SonarQube/Semgrep integration in GitHub Actions, and no `npm audit` or `yarn audit` in the test pipeline. The `eslint` configuration provides code quality linting but not security-focused static analysis. Codecov is configured for coverage tracking (`codecov.yml`) but no security-specific coverage. The `tests.yaml` workflow runs functional and unit tests but no security scanning steps. |
| **Gap** | No security scanning tools configured — no dependency scanning, no SAST, no container scanning. Pipeline has no security validation step. |
| **Recommendation** | Enable GitHub Dependabot for automated dependency vulnerability scanning. Add `npm audit` or `yarn audit --level high` to the test pipeline as a blocking gate. Integrate Semgrep or CodeGuru Reviewer for SAST. Enable Amazon ECR image scanning for container vulnerabilities. |
| **Evidence** | `.github/workflows/tests.yaml` (no security scanning), `.github/workflows/docker-build.yaml` (no container scanning), absence of `.github/dependabot.yml` or `.snyk` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Basic per-service logging via `werelogs` with request IDs (used in `BackbeatServer.js` via `logger.newRequestLogger()`). Prometheus metrics are extensively instrumented via `prom-client` v15.1.3 and `node-rdkafka-prometheus` v1.0.0 — Kafka consumer/producer stats are automatically exported. Custom Prometheus metrics include message timestamps, delivery reports, rebalance events, slow tasks, and task processing time (`lib/KafkaBacklogMetrics.js`, `lib/constants.js`). However, no distributed tracing framework (OpenTelemetry, X-Ray) is instrumented. No `traceparent` or `X-Amzn-Trace-Id` header propagation across Kafka message boundaries. Tracing is limited to individual service request logging — no cross-service trace correlation for replication workflows spanning queue populator → data processor → status processor. |
| **Gap** | Basic tracing on individual services but no cross-service propagation. Cannot trace a single replication operation end-to-end across Kafka-connected processors. |
| **Recommendation** | Instrument OpenTelemetry SDK for Node.js across all Backbeat processors. Propagate trace context through Kafka message headers. Use AWS X-Ray or Grafana Tempo for trace storage and visualization. |
| **Evidence** | `package.json` (werelogs, prom-client, node-rdkafka-prometheus), `lib/util/probe.js`, `lib/KafkaBacklogMetrics.js`, `lib/api/BackbeatServer.js` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Surface gate: `has_api_surface=true`. No formal SLO definitions exist. However, Prometheus alert rules in `monitoring/replication/alerts.yaml` define operational thresholds that approximate SLIs: RPO warning at 600s / critical at 900s, replication latency warning at 3000s / critical at 6000s, and error rate thresholds at 0.1% warning / 1% critical. Backlog growth alerting detects processing falling behind intake. These are threshold-based alarms without formal SLO definitions, error budget tracking, or burn rate alerting. |
| **Gap** | Basic availability/latency alarms exist as Prometheus alert rules but no formal SLO definitions with error budgets. Thresholds are defined but not tied to business SLOs. |
| **Recommendation** | Formalize SLOs for replication RPO (e.g., 99.9% of objects replicated within 600s), replication latency, and lifecycle processing throughput. Implement error budget tracking with burn-rate alerting. Use Amazon CloudWatch Service Level Objectives or Grafana SLO dashboards. |
| **Evidence** | `monitoring/replication/alerts.yaml` (RPO, latency, error rate thresholds), `monitoring/lifecycle/alerts.yaml` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Business-relevant metrics are published via Prometheus alongside infrastructure metrics. Custom metrics include: `s3_replication_status_changed_total` (by replicationStatus: COMPLETED/FAILED), `s3_replication_rpo_seconds` (RPO tracking), `s3_replication_latency_seconds` (end-to-end replication latency by location), `s3_replication_replay_objects_completed_total`, and Kafka backlog metrics (published/consumed message timestamps, task processing time, slow task count, queue depth). Grafana dashboards exist in `monitoring/` for replication, lifecycle, notification, ingestion, cold-storage, and oplog-populator — each with JSON dashboard definitions and Python dashboard generators. However, not all extensions have comprehensive business metrics — lifecycle and notification metrics are less detailed than replication. |
| **Gap** | Some business metrics tracked but not systematically across all features. Replication has rich metrics; lifecycle and notification have less coverage. |
| **Recommendation** | Extend business metrics coverage to all extensions with consistent metric naming. Add lifecycle processing throughput metrics, notification delivery success/failure rates, and GC reclaimed storage metrics. Publish to CloudWatch for integration with AWS-native observability. |
| **Evidence** | `lib/KafkaBacklogMetrics.js`, `lib/constants.js` (promMetricNames), `monitoring/replication/alerts.yaml`, `monitoring/replication/dashboard.json`, `monitoring/lifecycle/dashboard.json` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Prometheus alert rules are defined for all major components: replication (`monitoring/replication/alerts.yaml`) with 12 alerts covering producer/processor degradation, error rates, RPO, latency, and backlog growth; lifecycle (`monitoring/lifecycle/alerts.yaml`); notification (`monitoring/notification/alerts.yaml`); and oplog-populator (`monitoring/oplog-populator/alerts.yaml`). Alert rules use warning and critical severity levels with configurable thresholds (templated via `x-inputs`). The `alerts.yaml` GitHub Actions workflow validates alert rules with test suites (`alerts.test.yaml`). However, these are static threshold alarms — no anomaly detection (CloudWatch Anomaly Detection or equivalent) is configured. Alerting is per-component with no composite alarms. |
| **Gap** | Anomaly detection on primary paths via configurable Prometheus thresholds; static thresholds on secondary paths. No dynamic anomaly detection — all thresholds are manually configured. |
| **Recommendation** | Add CloudWatch Anomaly Detection for key business metrics (replication RPO, latency, error rates). Implement composite alarms that correlate multiple signals (e.g., high latency + growing backlog = systemic issue). Integrate with PagerDuty or OpsGenie for on-call routing. |
| **Evidence** | `monitoring/replication/alerts.yaml`, `monitoring/lifecycle/alerts.yaml`, `monitoring/notification/alerts.yaml`, `monitoring/oplog-populator/alerts.yaml`, `.github/workflows/alerts.yaml` |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. Docker images are built and pushed to GHCR (`docker-build.yaml`) but no deployment automation targets any environment. No canary, blue/green, or rolling deployment configuration. No CodeDeploy, Helm canary, Argo Rollouts, or Lambda traffic shifting. The `release.yaml` workflow creates a GitHub Release with a manual `workflow_dispatch` trigger but does not deploy to any environment. No deployment healthchecks or rollback automation. |
| **Gap** | Direct-to-production deployment with no staged rollout. No deployment automation — images are pushed but not deployed. |
| **Recommendation** | Implement staged deployment strategy. On EKS (preferred), use ArgoCD with Argo Rollouts for canary deployments based on Kafka consumer lag and error rate metrics. Define rollback triggers on Prometheus alert thresholds. |
| **Evidence** | `.github/workflows/docker-build.yaml`, `.github/workflows/release.yaml`, absence of deployment configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive testing exists: (1) Unit tests in `tests/unit/` covering all major components (BackbeatConsumer, BackbeatProducer, API, credentials, lifecycle, replication, notification, oplog populator). (2) Functional tests in `tests/functional/` covering 8 test suites (api:routes, api:retry, replication, lifecycle, ingestion, lib, notification, oplogPopulator) — these run against real Kafka, MongoDB, Redis, and ZooKeeper service containers in CI. (3) Behavior tests in `tests/behavior/`. (4) Performance tests (`tests/performance/lifecycle/conductor-check-memory-balloon.js`). (5) Queue-populator integration tests with Docker Compose including CloudServer. All tests run in CI (`tests.yaml`). Codecov tracks coverage with component-level targets (80% patch coverage, auto target for project). However, no end-to-end deployment integration tests exist — tests validate component behavior but not deployment correctness. |
| **Gap** | Integration tests for primary workflows run in CI; some gaps in deployment-level testing. No end-to-end tests that validate a deployed Backbeat instance against live infrastructure. |
| **Recommendation** | Add end-to-end smoke tests that run post-deployment against a staging environment. Test replication workflow end-to-end (produce → consume → replicate → verify). Include contract tests for API stability. |
| **Evidence** | `tests/unit/`, `tests/functional/`, `tests/behavior/`, `tests/performance/`, `.github/workflows/tests.yaml`, `codecov.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automated remediation, or incident response workflows exist in the repository. No SSM Automation documents, Lambda-based remediation, or Step Functions for incident workflows. No markdown runbooks documenting common incident procedures. The `docs/` directory contains operational documentation (healthcheck, metrics, pause/resume) but these are feature documentation, not incident response runbooks. The circuit breaker in `BackbeatConsumer.js` provides a limited self-healing pattern (pauses consumption when downstream is unhealthy, resumes when recovered) but this is built into the application, not an operational runbook. |
| **Gap** | No runbooks — incident response is entirely ad hoc. The circuit breaker provides application-level self-healing but no operational automation for infrastructure-level incidents. |
| **Recommendation** | Create structured runbooks for common incidents (Kafka broker failure, MongoDB primary failover, Redis connection loss, replication backlog growth, consumer lag spike). Implement SSM Automation documents for automated remediation of common failures. |
| **Evidence** | `docs/` (feature documentation only), `lib/BackbeatConsumer.js` (circuit breaker — application-level self-healing) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Grafana dashboards and Prometheus alerts exist per-component in `monitoring/`: replication (dashboard + alerts), lifecycle (dashboard + alerts), notification (dashboard + alerts), oplog-populator (dashboard + alerts), cold-storage (dashboard), and ingestion (dashboards + alerts). Dashboard definitions are JSON with Python generators. Alert rules have test suites (`alerts.test.yaml`). Dashboards and alerts are published as OCI artifacts alongside the Docker image (`docker-build.yaml` — oras push). However, no CODEOWNERS file exists for observability assets. No named owners on alarms. No team attribution on dashboards. Alert test thresholds reference Kubernetes namespace/job names suggesting Kubernetes deployment context but no ownership tags. |
| **Gap** | Ad hoc observability — dashboards and alarms exist per-component but no clear ownership or team attribution. No CODEOWNERS for monitoring configs. |
| **Recommendation** | Add CODEOWNERS file mapping `monitoring/` directory to the Backbeat team. Add owner labels to Prometheus alert rules. Include team tags on Grafana dashboards. Document SLO ownership per extension. |
| **Evidence** | `monitoring/replication/`, `monitoring/lifecycle/`, `monitoring/notification/`, `monitoring/oplog-populator/`, `.github/workflows/docker-build.yaml` (oras push dashboards) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC exists to evaluate resource tagging on. No `default_tags`, no `tags` blocks, no tag enforcement rules. The Prometheus alert rules include `namespace` labels (templated as `zenko`) but these are Kubernetes labels, not AWS resource tags. No cost allocation tags, no ownership tags, no environment tags are defined anywhere in the repository. |
| **Gap** | No tags found on resources — no IaC exists to define tags. When infrastructure is defined in code, tagging governance must be established from the start. |
| **Recommendation** | When adopting IaC, define a tagging standard with required tags (Environment, Service, Team, CostCenter). Use `default_tags` in Terraform provider or CDK `Tags.of()` for automatic tag propagation. Enforce via AWS Config required-tags rules and Tag Policies in AWS Organizations. |
| **Evidence** | Absence of IaC files with tag definitions |

---

## Learning Materials

**Triggered Pathways:**

- **Move to Cloud Native:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Managed Databases:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Managed Analytics:** [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)
- **Move to Modern DevOps:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, APP-Q2, APP-Q3, APP-Q4, DATA-Q3, DATA-Q4, INF-Q4, SEC-Q1, SEC-Q5, OPS-Q1 | Dependencies, engine version, AWS SDK v3, Kafka/MongoDB/Redis drivers |
| `Dockerfile` | INF-Q1, INF-Q6, APP-Q1, APP-Q2, SEC-Q6 | Multi-stage build, Node.js 22, port 8900, no USER directive |
| `conf/config.json` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q8, INF-Q9, APP-Q2, APP-Q4, APP-Q6, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5 | Kafka/MongoDB/Redis/ZooKeeper endpoints, retry configs, auth settings |
| `conf/authdata.json` | SEC-Q5 | Plaintext sample credentials committed to version control |
| `docker-entrypoint.sh` | INF-Q1, INF-Q2, INF-Q9, APP-Q2, APP-Q6, SEC-Q5 | Environment variable configuration, endpoint overrides, credential handling |
| `lib/BackbeatConsumer.js` | INF-Q3, INF-Q4, INF-Q7, INF-Q9, APP-Q3, APP-Q4, OPS-Q7 | Kafka consumer, circuit breaker, offset management, rebalance handling |
| `lib/BackbeatProducer.js` | INF-Q4, APP-Q3 | Kafka producer, delivery reports, backlog metrics |
| `lib/api/BackbeatAPI.js` | INF-Q2, INF-Q6, APP-Q2, APP-Q5, DATA-Q2, DATA-Q4, SEC-Q3 | HTTP API, MongoDB/Redis client creation, route handling |
| `lib/api/BackbeatServer.js` | INF-Q5, INF-Q6, SEC-Q1, SEC-Q3, OPS-Q1 | HTTP server, IP allowlist, request logging |
| `lib/api/routes.js` | APP-Q5 | API route definitions, no versioning |
| `lib/credentials/AccountCredentials.js` | SEC-Q3, SEC-Q4, SEC-Q5 | Static file and provisioned service account credentials |
| `lib/credentials/RoleCredentials.js` | SEC-Q3, SEC-Q4 | STS AssumeRole for temporary credentials |
| `lib/KafkaBacklogMetrics.js` | OPS-Q1, OPS-Q3 | Prometheus metrics for Kafka backlog, publish/consume timestamps |
| `lib/constants.js` | INF-Q7, OPS-Q3 | Prometheus metric names, consumer defaults |
| `lib/util/probe.js` | OPS-Q1 | Probe server, Prometheus metrics collection, rdkafka stats |
| `lib/clients/ZookeeperManager.js` | DATA-Q2 | Centralized ZooKeeper access |
| `extensions/utils/MongoUtils.js` | INF-Q2, DATA-Q2, DATA-Q3, DATA-Q4 | MongoDB connection string construction, version detection |
| `extensions/replication/queueProcessor/` | INF-Q3, APP-Q3 | Replication processing, Kafka topic chain |
| `extensions/lifecycle/conductor/` | INF-Q3 | Lifecycle workflow orchestration |
| `DESIGN.md` | INF-Q1, INF-Q7, INF-Q9 | HA design, multi-instance architecture, Kafka rationale |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline with unit/functional/integration tests, service containers |
| `.github/workflows/docker-build.yaml` | INF-Q1, INF-Q11, OPS-Q5, OPS-Q8, SEC-Q6, SEC-Q7 | Docker build, GHCR push, dashboard/policy publishing |
| `.github/workflows/release.yaml` | INF-Q11, OPS-Q5 | Manual release workflow, no deployment automation |
| `.github/workflows/alerts.yaml` | INF-Q11, OPS-Q4 | Prometheus alert rule testing |
| `monitoring/replication/alerts.yaml` | OPS-Q2, OPS-Q3, OPS-Q4 | Replication alerts: RPO, latency, error rates, backlog |
| `monitoring/replication/dashboard.json` | OPS-Q3, OPS-Q8 | Grafana dashboard for replication metrics |
| `monitoring/lifecycle/alerts.yaml` | OPS-Q2, OPS-Q4 | Lifecycle alerts |
| `monitoring/notification/alerts.yaml` | OPS-Q4 | Notification alerts |
| `monitoring/oplog-populator/alerts.yaml` | OPS-Q4 | Oplog populator alerts |
| `codecov.yml` | OPS-Q6 | Coverage tracking with component-level targets |
| `circle.yml` | INF-Q11 | Legacy CI configuration (superseded) |
| `docs/` | OPS-Q7 | Feature documentation (14 markdown files) |
| `tests/unit/` | OPS-Q6 | Unit test suites for all components |
| `tests/functional/` | OPS-Q6 | Functional test suites (8 suites) |
| `tests/behavior/` | OPS-Q6 | Behavior tests |
| `tests/performance/` | OPS-Q6 | Performance tests (memory balloon) |
