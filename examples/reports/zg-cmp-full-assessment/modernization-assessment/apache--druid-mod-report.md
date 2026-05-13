# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | druid (apache/druid) |
| **Date** | 2025-07-22 |
| **Repo Type** | monorepo |
| **Service Archetype** | data-gateway (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, analytics, database |
| **Context** | Apache Druid: high-performance real-time analytics database. |
| **Overall Score** | 2.48 / 4.0 |

**Archetype Justification**: Druid is a distributed analytics database whose primary runtime role is serving read-heavy OLAP queries (sub-second aggregation queries over billions of rows). While it also ingests data from Kafka/Kinesis streams, the dominant usage pattern is high-concurrency analytical reads with SQL and native JSON query interfaces. Classified as `data-gateway`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.64 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.33 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.50 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 2.29 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.48 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute infrastructure (ECS/EKS/Lambda/Fargate) defined — all deployment is self-managed Docker Compose | Prevents elastic scaling, increases operational overhead for patching and capacity planning |
| 2 | INF-Q2: Managed Databases | 1 | Metadata store runs as self-managed PostgreSQL container with no managed database services | Manual patching, no automated failover, no automated backups for metadata store |
| 3 | INF-Q10: Infrastructure as Code | 1 | Zero IaC coverage — no Terraform, CloudFormation, CDK, or Helm charts for infrastructure provisioning | Infrastructure changes are manual, non-reproducible, and error-prone; blocks all automated deployment pathways |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or immutable audit logging infrastructure defined | No forensic capability for security incidents; compliance gap for production deployments |
| 5 | OPS-Q2: SLO Definitions | 1 | No SLO definitions for critical user journeys (query latency, ingestion throughput) | Cannot measure service quality or prioritize modernization investments based on user impact |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 2 (≥ 2) and Druid exposes structured JSON HTTP APIs (documented in `docs/api-reference/`). Druid has 14 documented API reference pages covering SQL queries, ingestion, supervision, data management, and status endpoints.
- **What it enables:** An agent that discovers and invokes Druid's HTTP API endpoints as tools — enabling natural-language cluster management, query execution, and ingestion supervision.
- **Additional steps:** Generate an OpenAPI specification from Druid's existing API documentation and JAX-RS annotations in `server/` source code. This would enable full tool discovery for agent frameworks.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (≥ 2). Druid has a well-defined SQL query layer (`sql/` module) with JDBC support and a native JSON query interface.
- **What it enables:** A natural-language-to-SQL agent that translates user questions into Druid SQL queries, leveraging Amazon Bedrock for LLM inference. Users could query analytics data conversationally.
- **Additional steps:** Document the schema catalog (datasource names, column types, dimensions vs metrics) to provide the agent with context for accurate SQL generation.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). Comprehensive GitHub Actions CI/CD pipeline exists with 12+ workflow definitions.
- **What it enables:** An agent that triggers CI builds, checks test status, monitors pipeline health, and manages releases via GitHub Actions API.
- **Additional steps:** None — GitHub Actions API is well-documented and agent-ready.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists — `docs/` directory with 60+ operational and API reference documents, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, and the full Druid documentation site source.
- **What it enables:** A RAG-based knowledge agent using Amazon Bedrock that indexes Druid documentation and provides contextual answers to operator and developer questions about configuration, troubleshooting, and best practices.
- **Additional steps:** Index the `docs/` directory content into a vector store (e.g., Amazon OpenSearch Service with vector engine). Chunk documents by section for optimal retrieval.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 3 (≥ 2). Druid has internal task orchestration via the Overlord/indexing-service with HTTP APIs for task management.
- **What it enables:** An agent that monitors ingestion tasks, manages supervisors, triggers compaction, and handles task failures through Druid's task management API.
- **Additional steps:** None — Druid's supervisor and task APIs are well-documented in `docs/api-reference/supervisor-api.md` and `docs/api-reference/tasks-api.md`.
- **Effort:** Low

### Observability Agent

- **Prerequisite:** OPS-Q1 = 2 (≥ 2). OpenTelemetry emitter extension exists (`extensions-contrib/opentelemetry-emitter/`), and Druid has comprehensive metrics emission to Prometheus, Graphite, StatsD, and other backends.
- **What it enables:** An agent that queries Druid metrics, correlates query performance issues with cluster state, and suggests root causes for slow queries or ingestion failures.
- **Additional steps:** Enable the OpenTelemetry or Prometheus emitter extension in production deployments. Configure metrics export to a centralized observability backend.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (≥ 3) — Druid already has well-defined distributed service boundaries |
| 2 | Move to Containers | Not Triggered | — | — | Container definitions exist (Dockerfile, docker-compose.yml) — contextual guard prevents trigger |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4, no commercial DB engines detected — PostgreSQL, MySQL, Derby are all open source |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (< 3): metadata store is self-managed PostgreSQL container; DATA-Q3 = 3 |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 (≥ 3) — data-gateway archetype calibration scores sync reads as correct design |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (< 3): zero IaC coverage; INF-Q11 = 3 (CI exists but no deployment automation) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
Druid's metadata store is a self-managed PostgreSQL 17.6 container (defined in `distribution/docker/docker-compose.yml`) with a plain-text password (`POSTGRES_PASSWORD=FoolishPassword`). The default configuration in `examples/conf/` uses embedded Apache Derby for single-server deployments. No managed database infrastructure (RDS, Aurora, DynamoDB) is defined in the repository.

**Engine Versions and EOL Status:**
- PostgreSQL 17.6 (docker-compose) — current, not at EOL
- PostgreSQL JDBC driver 42.7.2 (pom.xml) — current
- MySQL Connector 8.2.0 (pom.xml) — current
- MariaDB Connector 2.7.3 (pom.xml) — current
- Apache Derby 10.14.2.0 (pom.xml) — Apache Derby 10.14.x reached EOL; newer versions available

**Data Access Patterns:**
Druid's metadata store is accessed through a centralized JDBI-based data access layer (`server/` module), making migration to a managed database straightforward — connection strings and driver configuration are externalized.

**Recommended Migration Targets:**
- **Amazon Aurora PostgreSQL** (preferred per user preferences) — for Druid metadata storage. Aurora provides automated failover, backups, and scaling with PostgreSQL wire-protocol compatibility.
- **Amazon RDS for PostgreSQL** — alternative if Aurora's distributed storage model is not needed for the relatively small metadata workload.

**Representative AWS Services:** Aurora PostgreSQL, RDS PostgreSQL, AWS DMS (for migration)

**Migration Approach:**
1. Provision Aurora PostgreSQL cluster via IaC (Terraform or CDK)
2. Use AWS DMS for initial data migration from self-managed PostgreSQL
3. Update Druid configuration (`druid.metadata.storage.connector.connectURI`) to point to Aurora endpoint
4. Enable Multi-AZ for automatic failover
5. Configure automated backups with PITR
6. Store database credentials in AWS Secrets Manager (addresses SEC-Q5 gap)

**Relevant Guidance:** [AWS Database Migration Service](https://aws.amazon.com/dms/) · [Aurora PostgreSQL Migration Guide](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Migrating.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure-as-code exists in the repository. No Terraform, CloudFormation, CDK, or Helm charts for provisioning Druid infrastructure. All infrastructure (compute, networking, databases, ZooKeeper) must be created manually or via ad hoc scripts. The `distribution/docker/docker-compose.yml` provides a local development environment but is not production-grade IaC.

**Current CI/CD State (INF-Q11 = 3):**
The repository has comprehensive CI automation via GitHub Actions:
- Unit tests (`ci.yml`, triggered on push/PR)
- Docker-based integration tests (`docker-tests.yml`)
- Static code analysis (`static-checks.yml` — Checkstyle, PMD, SpotBugs, ForbiddenAPIs, ErrorProne)
- Security scanning (`codeql.yml` — CodeQL SAST for Java, JavaScript, Python)
- Dependency vulnerability scanning (`cron-job-its.yml` — OWASP dependency-check, daily)
- Dependency updates (`dependabot.yml` — Maven daily updates)

However, there is **no deployment automation** — no pipeline stage deploys Druid to any environment (staging, production). Deployments are manual.

**Deployment Strategy Gaps (OPS-Q5 = 2):**
Rolling updates are documented (`docs/operations/rolling-updates.md`) with a recommended node update order, but no automated canary or blue/green deployment is implemented. Deployment relies on manual operator execution.

**Testing Gaps (OPS-Q6 = 3):**
Integration tests are comprehensive (Docker-based tests run Druid cluster in containers and validate end-to-end behavior), but some auxiliary paths lack coverage.

**Recommended DevOps Toolchain (respecting preferences):**
1. **Infrastructure as Code:** Define Druid cluster infrastructure using Terraform or AWS CDK targeting **Amazon EKS** (preferred). Create modules for:
   - EKS cluster with node groups for each Druid node type (broker, historical, coordinator, overlord, middlemanager, router)
   - Aurora PostgreSQL for metadata store
   - S3 buckets for deep storage
   - VPC with private subnets and security groups
   - Amazon API Gateway for external query access (preferred)
2. **Deployment Automation:** Implement GitOps with ArgoCD or Flux CD for Kubernetes-based deployments on EKS. Define Helm charts for each Druid node type.
3. **Deployment Strategy:** Implement rolling deployments via Kubernetes `RollingUpdate` strategy, following Druid's documented update order (Historical → MiddleManager → Broker → Router → Overlord → Coordinator).

**Representative AWS Services:** Amazon EKS, AWS CDK/Terraform, CodePipeline, CodeBuild, ECR, CloudFormation

**Relevant Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is self-managed. The repository provides Docker images (`distribution/docker/Dockerfile`) and a `docker-compose.yml` that deploys Druid services (coordinator, broker, historical, middlemanager, router) as containers, but no IaC defines managed compute resources (ECS, EKS, Lambda, Fargate). The Dockerfile uses `gcr.io/distroless/java17-debian12` as base image. The `docker-compose.yml` orchestrates 5 Druid service containers plus PostgreSQL and ZooKeeper — all self-managed with no AWS compute primitives. |
| **Gap** | No managed compute infrastructure defined. Production deployments require manual provisioning of compute resources. |
| **Recommendation** | Deploy Druid on **Amazon EKS** (preferred) with dedicated node groups per Druid node type. Use Kubernetes StatefulSets for stateful nodes (Historical, MiddleManager) and Deployments for stateless nodes (Broker, Router). Reference the [druid-operator](https://github.com/apache/druid-operator) for Kubernetes-native deployment. |
| **Evidence** | `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Druid's metadata store is a self-managed PostgreSQL 17.6 container (`postgres:17.6` in `distribution/docker/docker-compose.yml`). The default configuration uses embedded Apache Derby (`druid.metadata.storage.type=derby` in `examples/conf/druid/cluster/_common/common.runtime.properties`). No `aws_rds_*`, `aws_dynamodb_*`, or other managed database IaC resources exist. The Docker environment file (`distribution/docker/environment`) hardcodes the PostgreSQL password as `FoolishPassword`. |
| **Gap** | All database infrastructure is self-managed. No automated failover, no managed backups, no automated patching for the metadata store. |
| **Recommendation** | Migrate the metadata store to **Amazon Aurora PostgreSQL** (preferred). Aurora provides automated Multi-AZ failover, point-in-time recovery, and automated patching. Store credentials in AWS Secrets Manager. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `distribution/docker/environment`, `examples/conf/druid/cluster/_common/common.runtime.properties` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: data-gateway.** Druid has its own internal task orchestration system via the Overlord service (`indexing-service/` module). The Overlord manages ingestion tasks, compaction tasks, and supervisor-based streaming ingestion with status tracking, retry logic, and task lifecycle management. This is partial adoption — the ingestion workflow is orchestrated via Druid's built-in system, but there is no external managed workflow orchestration service (Step Functions, Temporal) for broader operational workflows. No multi-step background maintenance jobs exist outside of Druid's internal system that would require external orchestration. |
| **Gap** | Minor — Druid's internal orchestration serves the data-gateway's ingestion needs. External orchestration could benefit complex multi-step operational workflows (e.g., coordinated backup → validation → compaction pipelines). |
| **Recommendation** | Consider **AWS Step Functions** (or **Amazon EventBridge** per preferences) for operational workflows that span beyond Druid's internal task system — e.g., automated data lifecycle management, cross-service coordination with upstream data producers. |
| **Evidence** | `indexing-service/`, `docs/api-reference/supervisor-api.md`, `docs/api-reference/tasks-api.md` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: data-gateway.** Synchronous reads dominate Druid's query path (correct design for this archetype). For the write/ingestion path, Druid provides Kafka (`extensions-core/kafka-indexing-service`) and Kinesis (`extensions-core/kinesis-indexing-service`) consumer extensions as core integration points, plus RabbitMQ stream support (`extensions-contrib/rabbit-stream-indexing-service`). These are consumer-side integrations — Druid consumes from existing messaging infrastructure but does not provision or manage it. The messaging infrastructure itself (Kafka, Kinesis) would be externally managed. |
| **Gap** | The repository does not provision or manage the messaging infrastructure it depends on. When deployed on AWS, Kafka clusters would need to be provisioned separately. |
| **Recommendation** | When deploying on AWS, use **Amazon MSK Serverless** or **Amazon Kinesis Data Streams** (avoid self-managed Kafka per preferences) for streaming ingestion. Configure Druid's Kafka/Kinesis indexing service extensions to consume from managed services. Use **Amazon EventBridge** (preferred) for operational event routing. |
| **Evidence** | `extensions-core/kafka-indexing-service/`, `extensions-core/kinesis-indexing-service/`, `extensions-contrib/rabbit-stream-indexing-service/`, `distribution/docker/environment` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation definitions exist in the repository. No networking IaC of any kind was found. The `docker-compose.yml` exposes service ports directly (8081, 8082, 8083, 8091, 8888, 5432, 2181) without network isolation. The security documentation (`docs/operations/security-overview.md`) recommends using firewalls and network-layer filtering but provides no IaC implementation. |
| **Gap** | No network security infrastructure defined. Services would be deployed without VPC isolation, private subnets, or security group controls. |
| **Recommendation** | Define VPC infrastructure via IaC with private subnets for all Druid services, security groups with least-privilege rules (e.g., only Broker/Router accessible from application tier, Historical/MiddleManager isolated to data tier), and VPC endpoints for S3 deep storage access. Use **Amazon API Gateway** (preferred) as the external entry point. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `docs/operations/security-overview.md` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid's Router service acts as an internal API gateway/load balancer that routes queries to Brokers and management requests to Coordinators/Overlords. The Router provides basic routing and health checks. However, no managed API entry point (API Gateway, ALB, CloudFront, AppSync) is defined in IaC. The `docs/operations/security-overview.md` recommends using an API gateway for throttling, authentication, and access control, but no implementation exists in the repository. |
| **Gap** | No managed API entry point with throttling, authentication, or request validation. Druid's Router provides internal routing but lacks external traffic management capabilities. |
| **Recommendation** | Deploy **Amazon API Gateway** (preferred) as the external entry point for Druid query and management APIs. Configure throttling, authentication (Cognito or IAM), and request validation. Route to Druid's Router or Broker behind an internal ALB. |
| **Evidence** | `distribution/docker/docker-compose.yml` (router service on port 8888), `docs/operations/security-overview.md` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists in the repository. The `docker-compose.yml` defines a single instance of each Druid node type with no scaling mechanism. No `aws_autoscaling_*`, `aws_appautoscaling_*`, Kubernetes HPA, or KEDA scaling definitions were found. Druid's architecture supports horizontal scaling of Broker and Historical nodes, but no automation is defined. |
| **Gap** | All capacity is statically provisioned. No mechanism to respond to traffic spikes (query load) or ingestion volume changes. |
| **Recommendation** | On **Amazon EKS** (preferred), configure Kubernetes Horizontal Pod Autoscaler (HPA) for Broker nodes (scale on CPU/query latency) and Historical nodes (scale on segment count/disk utilization). Use Karpenter for node-level autoscaling. Consider Graviton-based instances for cost efficiency. |
| **Evidence** | `distribution/docker/docker-compose.yml` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. No `aws_backup_plan`, `backup_retention_period`, `point_in_time_recovery`, or S3 versioning configuration was found. The self-managed PostgreSQL metadata store in `docker-compose.yml` has no backup configuration. Druid segments stored in deep storage (local disk in the example configuration) have no backup or replication mechanism defined. |
| **Gap** | No automated backups for metadata store or deep storage. A data loss event in the metadata store would require full cluster reconstruction. |
| **Recommendation** | Migrate metadata store to Aurora PostgreSQL (automated backups with PITR). For deep storage, use S3 with versioning and cross-region replication for critical data. Define an AWS Backup plan for the Aurora cluster with at least 7-day retention. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `examples/conf/druid/cluster/_common/common.runtime.properties` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. The `docker-compose.yml` deploys a single instance of each Druid node type, PostgreSQL, and ZooKeeper — all single points of failure. Druid's documentation (`docs/operations/high-availability.md`) recommends running multiple Coordinators/Overlords (with ZooKeeper-based failover), multiple Brokers behind a load balancer, and a ZooKeeper ensemble of 3-5 nodes, but no IaC implements these recommendations. |
| **Gap** | All resources are single-instance. No fault isolation or automatic recovery from AZ or node failures. |
| **Recommendation** | Deploy across 2+ AZs on **Amazon EKS** (preferred). Run ZooKeeper as a 3-node ensemble (or migrate to Druid's built-in coordination if available). Deploy multiple Broker and Historical replicas. Use Aurora PostgreSQL Multi-AZ for metadata store failover. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `docs/operations/high-availability.md` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform (`.tf`), CloudFormation, CDK (`cdk.json`), or Helm charts for infrastructure provisioning were found in the repository. The only infrastructure-adjacent file is `distribution/docker/docker-compose.yml`, which is a local development environment definition, not production IaC. The repository references external tools like the [druid-operator](https://github.com/apache/druid-operator) and community [Helm charts](https://github.com/asdf2014/druid-helm) in the README but does not include them. |
| **Gap** | All infrastructure is created manually (ClickOps). No reproducible environment provisioning, no drift detection, no infrastructure change auditing. |
| **Recommendation** | Create IaC modules (Terraform or AWS CDK) for the complete Druid deployment stack: EKS cluster, Aurora PostgreSQL, S3 deep storage buckets, VPC networking, API Gateway, CloudWatch monitoring. Start with the [druid-operator](https://github.com/apache/druid-operator) for Kubernetes-native deployment and layer IaC for AWS infrastructure. |
| **Evidence** | Repository root (no `.tf`, `.cfn.*`, `cdk.json`, `Chart.yaml` files found) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI automation exists via GitHub Actions (12 workflow files in `.github/workflows/`): unit tests (`ci.yml`), Docker-based integration tests (`docker-tests.yml`), unified test pipeline (`unit-and-integration-tests-unified.yml`), static code analysis (`static-checks.yml` — Checkstyle, PMD, SpotBugs, ForbiddenAPIs, ErrorProne, OpenRewrite), CodeQL SAST (`codeql.yml`), dependency vulnerability scanning (`cron-job-its.yml` — OWASP dependency-check daily), Dependabot for dependency updates (`dependabot.yml`), PR checks (`pr-checks.yml`), and labeler automation (`labeler.yml`). Build, test, and security scanning stages are automated. However, there is **no deployment stage** — no pipeline deploys Druid to any environment. |
| **Gap** | No deployment automation. CI pipeline covers build, test, and security scanning, but deployment to staging or production is manual. |
| **Recommendation** | Add deployment stages to the CI/CD pipeline. For EKS deployments, integrate with ArgoCD or Flux CD for GitOps-based deployment. Define separate pipelines for image building (push to ECR) and deployment (Helm chart updates). Implement automated rollback on health check failures. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/docker-tests.yml`, `.github/workflows/unit-and-integration-tests-unified.yml`, `.github/workflows/static-checks.yml`, `.github/workflows/codeql.yml`, `.github/workflows/cron-job-its.yml`, `.github/dependabot.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is Java 17 (`<java.version>17</java.version>` in `pom.xml`). Java has first-class AWS SDK coverage (AWS SDK v2 `2.40.0` used in `cloud/aws-common/`), mature cloud-native frameworks (Guice for DI, Jetty for HTTP, Jackson for serialization), and extensive tooling. Secondary languages: TypeScript (React web console in `web-console/`, Node 20), Python (tooling scripts). |
| **Gap** | None — Java 17 is a tier-1 language for AWS cloud-native development. |
| **Recommendation** | No action needed. Continue with Java 17+ and consider Java 21 LTS for future upgrades (virtual threads would benefit Druid's concurrent query processing). |
| **Evidence** | `pom.xml` (java.version=17, aws.sdk.v2.version=2.40.0), `web-console/package.json` (TypeScript, Node 20) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid is a distributed system with well-defined node types: Coordinator, Broker, Historical, MiddleManager/Indexer, Router, and Overlord. Each runs as a separate process with distinct responsibilities. The `docker-compose.yml` deploys 5 independent service containers from the same Docker image using different entrypoint commands. The architecture has clear module boundaries: `processing/` (query engine), `server/` (HTTP services), `indexing-service/` (task management), `sql/` (SQL planning), `multi-stage-query/` (MSQ engine). However, all modules share a single Maven build (`pom.xml`) and a single Docker image — they are not independently buildable or deployable artifacts. The modules share the `server/` module for common functionality. This is a **modular distributed system** with clear interfaces but a shared build artifact. |
| **Gap** | Single build artifact (one Docker image, one Maven project) means all node types must be versioned and released together. Cannot independently deploy or scale-test individual node types without building the entire project. |
| **Recommendation** | The current architecture is appropriate for Druid's nature as a tightly-integrated distributed database. The modular structure with clear node type boundaries scores well. Consider extracting Helm charts per node type (using the same image with different configs) for independent scaling and deployment on EKS. |
| **Evidence** | `pom.xml` (modules list), `distribution/docker/docker-compose.yml` (5 Druid services), `distribution/docker/Dockerfile` (single image), `AGENTS.md` (module descriptions) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: data-gateway.** Synchronous reads are the correct design for Druid's primary use case (sub-second OLAP queries). Inter-node query routing uses synchronous HTTP (Broker → Historical fan-out). For write-back/ingestion, Druid uses async consumers: Kafka indexing service (`extensions-core/kafka-indexing-service`), Kinesis indexing service (`extensions-core/kinesis-indexing-service`), and the Overlord task system with async task submission and status polling. ZooKeeper provides async coordination for cluster state. This is the correct design — synchronous for the read path, async for the write path. |
| **Gap** | None — the communication pattern is appropriate for the data-gateway archetype. |
| **Recommendation** | Adopting async messaging for the query path is NOT recommended — it would add latency and complexity to Druid's sub-second query engine. The current sync-read / async-write pattern is architecturally correct. |
| **Evidence** | `extensions-core/kafka-indexing-service/`, `extensions-core/kinesis-indexing-service/`, `server/` (HTTP routing), `indexing-service/` (async task management) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: data-gateway.** No user-facing query operations exceed 30 seconds in normal operation (Druid is designed for sub-second to low-second query latency). For heavy operations: ingestion tasks are handled asynchronously via the Overlord/indexing-service with task submission, status polling, and lifecycle management (`docs/api-reference/tasks-api.md`). Compaction and reindexing are long-running background jobs managed by the supervisor system (`docs/api-reference/supervisor-api.md`) with status tracking. The Multi-Stage Query (MSQ) engine (`multi-stage-query/`) handles large-scale batch operations asynchronously with progress reporting. |
| **Gap** | None — long-running operations (ingestion, compaction, MSQ queries) are properly handled asynchronously with status tracking. |
| **Recommendation** | No action needed. The async task management pattern is well-implemented. Consider exposing task status via Amazon EventBridge (preferred) for integration with external monitoring systems. |
| **Evidence** | `indexing-service/`, `multi-stage-query/`, `docs/api-reference/tasks-api.md`, `docs/api-reference/supervisor-api.md` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid's HTTP APIs do not use a consistent versioning strategy. API endpoints use paths like `/druid/v2/sql` and `/druid/v2/` for native queries, but this is a legacy prefix rather than a versioning strategy — there is no `/v1/` or `/v3/` alternative. The `docs/api-reference/` documents 14 API categories (SQL, JSON querying, supervisor, tasks, data management, etc.) with no versioning convention. Some endpoints are marked as "legacy" (`docs/api-reference/legacy-metadata-api.md`) but coexist with newer endpoints without formal deprecation or versioning. |
| **Gap** | No formal API versioning strategy. Breaking changes are deployed directly. The `/v2/` prefix is a historical artifact, not part of a versioning scheme. |
| **Recommendation** | Implement a formal API versioning strategy using URL path versioning (e.g., `/api/v1/`, `/api/v2/`) or header-based versioning. Document backward compatibility guarantees and deprecation timelines. When fronting with Amazon API Gateway (preferred), use API Gateway stages for versioning. |
| **Evidence** | `docs/api-reference/` (14 API reference documents), `docs/api-reference/legacy-metadata-api.md` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid uses Apache ZooKeeper for service discovery. All Druid services register themselves with ZooKeeper (`druid.zk.service.host=zookeeper` in `distribution/docker/environment`, `druid.zk.service.host=localhost` in `examples/conf/`). Service selectors are configured via `druid.selectors.indexing.serviceName` and `druid.selectors.coordinator.serviceName`. The Broker discovers Historical nodes via ZooKeeper. The Router discovers Brokers via ZooKeeper. However, ZooKeeper itself is configured with a hardcoded host address (`druid.zk.service.host`), and external dependencies (PostgreSQL) use hardcoded connection strings. |
| **Gap** | ZooKeeper provides internal service discovery, but ZooKeeper itself and external dependencies (PostgreSQL) use hardcoded hostnames. Moving to Kubernetes would enable native service discovery for all components. |
| **Recommendation** | On **Amazon EKS** (preferred), leverage Kubernetes native service discovery (DNS-based) for all Druid services. Consider migrating from ZooKeeper to Kubernetes-native coordination if the Druid project supports it. Use environment variables or ConfigMaps for service endpoints rather than hardcoded hostnames. |
| **Evidence** | `distribution/docker/environment` (druid_zk_service_host=zookeeper), `examples/conf/druid/cluster/_common/common.runtime.properties` (druid.zk.service.host, druid.selectors.*) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid stores data in its own columnar segment format with a pluggable deep storage abstraction. S3 deep storage is supported as a core extension (`extensions-core/s3-extensions/`) using AWS SDK v2. Configuration supports S3 (`druid.storage.type=s3`, `druid.storage.bucket`, `druid.storage.baseKey` in `examples/conf/`), HDFS, Azure, Google Cloud Storage, and local filesystem. The S3 extension provides full segment push/pull functionality. However, there is no automated parsing pipeline (Textract, Tika) for unstructured data — Druid ingests structured/semi-structured data (JSON, CSV, Avro, Parquet, ORC, Protobuf) via its ingestion framework. |
| **Gap** | S3 deep storage is supported but no automated unstructured data parsing pipeline exists. Druid's focus is on structured analytics data, not unstructured document processing. |
| **Recommendation** | For Druid's use case (analytics database), the focus should be on S3 deep storage optimization rather than unstructured data parsing. Enable S3 deep storage in production and configure S3 lifecycle policies for segment management. |
| **Evidence** | `extensions-core/s3-extensions/`, `examples/conf/druid/cluster/_common/common.runtime.properties` (S3 config comments), `pom.xml` (aws.sdk.v2.version=2.40.0) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Druid has a highly unified data access layer. All query access goes through the Broker node, which routes to appropriate Historical and MiddleManager nodes. The `processing/` module provides the core query processing engine with a consistent query interface. The `sql/` module adds a SQL layer (Apache Calcite-based) providing JDBC and HTTP SQL endpoints. Native JSON queries use a single endpoint (`/druid/v2/`). All data access — regardless of query type (TopN, GroupBy, Timeseries, Scan, SQL) — flows through the same processing pipeline. There are no scattered database connections — Druid IS the database. |
| **Gap** | None — Druid provides a single, unified data access point by design. |
| **Recommendation** | No action needed. The unified query layer is a core architectural strength. |
| **Evidence** | `processing/` (query engine), `sql/` (SQL layer), `server/` (HTTP endpoints), `docs/api-reference/sql-api.md`, `docs/api-reference/json-querying-api.md` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine and dependency versions are explicitly pinned in `pom.xml`. PostgreSQL: image `postgres:17.6` (docker-compose), JDBC driver `42.7.2` — current, well within support. MySQL Connector: `8.2.0` — current. MariaDB Connector: `2.7.3` — current. Apache Derby: `10.14.2.0` — **approaching concern** (Derby 10.14 is the last release compatible with Java 8; newer versions are available). ZooKeeper: `3.8.6` — current LTS, deliberately pinned with version upper bound in Dependabot (`versions: [3.6,)` ignored). Apache Kafka client: `3.9.1` — current. |
| **Gap** | Derby 10.14.2.0 is aging. While Derby is only used for non-production embedded metadata storage, it could be updated. ZooKeeper is deliberately held at 3.8.x (pinned in dependabot.yml) which may eventually approach EOL. |
| **Recommendation** | Update Derby to a newer version if compatibility allows. Monitor ZooKeeper 3.8.x EOL timeline and plan for upgrade when the Druid project removes the version pin. Document the version-update procedure for all metadata store engines. |
| **Evidence** | `pom.xml` (derby.version=10.14.2.0, zookeeper.version=3.8.6, postgresql.version=42.7.2, mysql.version=8.2.0), `distribution/docker/docker-compose.yml` (postgres:17.6), `.github/dependabot.yml` (ZooKeeper version pin) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Druid does not use stored procedures, triggers, or proprietary SQL constructs. All business logic (query processing, ingestion, coordination, segment management) resides in the Java application layer. The SQL files found in the repository (`embedded-tests/src/test/resources/multi-stage-query/*.sql`) are Druid SQL statements for test data, not database stored procedures. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements were found in any `.sql` file. The metadata store uses simple CRUD operations via JDBI (Java Data Access Interface). Druid's SQL dialect is its own (DruidSQL), not tied to any proprietary database SQL. |
| **Gap** | None — all business logic is in the application layer. |
| **Recommendation** | No action needed. The clean separation between application logic and data storage is exemplary. |
| **Evidence** | `embedded-tests/src/test/resources/multi-stage-query/*.sql` (Druid SQL test files, no stored procedures), `sql/` (Druid SQL engine), `server/` (JDBI-based metadata access) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or immutable audit logging infrastructure is defined in the repository. Druid has request logging capabilities (`docs/operations/request-logging.md`) that can log all queries with timestamps and user context, but this is application-level logging, not infrastructure audit logging. No `aws_cloudtrail` resources, no S3 Object Lock for log immutability, no log file validation configuration exists. The security documentation (`docs/operations/security-overview.md`) does not reference CloudTrail integration. |
| **Gap** | No infrastructure-level audit logging. Request logging exists but lacks immutability guarantees and is not integrated with AWS CloudTrail for API-level auditing. |
| **Recommendation** | Enable AWS CloudTrail with log file validation and immutable storage (S3 Object Lock) for all AWS API activity. Integrate Druid's request logging with CloudWatch Logs for centralized, searchable query audit trails. Define log retention policies. |
| **Evidence** | `docs/operations/security-overview.md`, `docs/operations/request-logging.md`, repository root (no CloudTrail IaC found) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration exists in the repository. No `kms_key_id`, `aws_kms_key`, or encryption configuration on any data store. The `docker-compose.yml` PostgreSQL instance has no encryption. The deep storage configuration (`druid.storage.type=local` in examples) uses unencrypted local filesystem. S3 deep storage configuration (commented in `examples/conf/`) does not specify server-side encryption. No TLS configuration is enabled by default (security documentation notes TLS must be configured manually). |
| **Gap** | No encryption at rest for metadata store, deep storage, or segment cache. |
| **Recommendation** | When deploying on AWS: use S3 server-side encryption (SSE-S3 or SSE-KMS with customer-managed keys) for deep storage, Aurora PostgreSQL encryption at rest for metadata store, and EBS encryption for Historical node segment caches. Define a centralized KMS key management strategy. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `examples/conf/druid/cluster/_common/common.runtime.properties`, `docs/operations/tls-support.md` |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid provides multiple authentication extensions as core components: `druid-basic-security` (username/password with built-in credential store), `druid-kerberos` (Kerberos/SPNEGO), and `druid-pac4j` (OIDC/SAML/OAuth2 via PAC4J framework). The security documentation (`docs/operations/security-overview.md`, `docs/operations/auth.md`) provides detailed configuration instructions. However, authentication is **disabled by default** — the example configurations and Docker deployment have no authentication enabled. The security best practices explicitly state: "Enable authentication to the Druid cluster for production environments." |
| **Gap** | Authentication extensions exist but are disabled by default. The Docker deployment and example configurations run without authentication, which is a security risk if deployed to production without modification. |
| **Recommendation** | Enable authentication in all non-development deployments. For AWS deployments, configure the `druid-pac4j` extension with Amazon Cognito for OIDC-based authentication, or front Druid with **Amazon API Gateway** (preferred) using Cognito authorizers. |
| **Evidence** | `extensions-core/druid-basic-security/`, `extensions-core/druid-pac4j/`, `extensions-core/druid-kerberos/`, `docs/operations/security-overview.md`, `docs/operations/auth.md` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid supports centralized identity provider integration through multiple mechanisms: LDAP authentication (`docs/operations/auth-ldap.md`) for enterprise directory integration, PAC4J extension (`extensions-core/druid-pac4j`) for OIDC/SAML federation (enabling SSO with providers like Okta, Cognito, Ping), and Kerberos (`extensions-core/druid-kerberos`) for enterprise Kerberos realms. The `druid-basic-security` extension also supports LDAP-based authentication with role mapping. However, the default configuration uses no IdP integration — the basic security extension manages credentials internally when enabled. |
| **Gap** | IdP integration capabilities exist but are not enabled by default. The basic security extension's internal credential store is used as the default when security is enabled, rather than federation with an external IdP. |
| **Recommendation** | Configure the `druid-pac4j` extension with **Amazon Cognito** for OIDC-based SSO in AWS deployments. This provides centralized user management, MFA support, and integration with enterprise identity providers. |
| **Evidence** | `extensions-core/druid-pac4j/`, `extensions-core/druid-kerberos/`, `docs/operations/auth-ldap.md`, `docs/operations/security-overview.md` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid has a `DynamicConfigProvider` framework (`docs/operations/dynamic-config-provider.md`) that supports environment variable-based secret injection, avoiding hardcoded secrets in config files. The `druid.server.hiddenProperties` configuration masks sensitive properties in logs and API responses (`["druid.s3.accessKey","druid.s3.secretKey","druid.metadata.storage.connector.password", "password", "key", "token", "pwd"]` in `examples/conf/`). However, the Docker deployment hardcodes `POSTGRES_PASSWORD=FoolishPassword` in `distribution/docker/environment`. No integration with AWS Secrets Manager, HashiCorp Vault, or automated rotation exists. The `DynamicConfigProvider` interface supports custom implementations but no AWS Secrets Manager implementation is included. |
| **Gap** | Environment variable-based secret injection exists but production database credentials are hardcoded in the Docker environment file. No secrets management service integration (Secrets Manager, Vault). No automated rotation. |
| **Recommendation** | Implement a custom `DynamicConfigProvider` for AWS Secrets Manager integration. Store all database credentials, S3 access keys, and API tokens in Secrets Manager with automated rotation. Remove all hardcoded credentials from configuration files. |
| **Evidence** | `docs/operations/dynamic-config-provider.md`, `distribution/docker/environment` (POSTGRES_PASSWORD=FoolishPassword), `examples/conf/druid/cluster/_common/common.runtime.properties` (druid.server.hiddenProperties) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Dockerfile (`distribution/docker/Dockerfile`) uses Google's distroless base image (`gcr.io/distroless/java17-debian12`), which is a hardened, minimal image with no shell, no package manager, and no unnecessary OS utilities — significantly reducing attack surface. The container runs as a non-root user (`druid`, uid 1000). Busybox is included only for essential utilities. These are security best practices for container hardening. However, no SSM Patch Manager, AWS Inspector, or container image scanning (ECR scanning, Snyk container) is configured. No automated patching strategy for the base image. |
| **Gap** | Hardened base image is used (distroless), but no automated vulnerability scanning for the container image and no managed patching strategy. |
| **Recommendation** | Push Docker images to **Amazon ECR** with automated image scanning enabled. Integrate ECR scan results into the CI pipeline as a quality gate. Use ECR lifecycle policies for image retention. Consider AWS Inspector for runtime vulnerability scanning on EKS nodes. |
| **Evidence** | `distribution/docker/Dockerfile` (gcr.io/distroless/java17-debian12, USER druid, uid 1000) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CI pipeline includes multiple security scanning tools: **CodeQL SAST** (`.github/workflows/codeql.yml`) scanning Java, JavaScript, and Python with `security-and-quality` queries; **OWASP Dependency Check** (`cron-job-its.yml`) running daily with `failBuildOnCVSS=7`; **Dependabot** (`.github/dependabot.yml`) for automated Maven dependency updates with 14-day cooldown; **OWASP suppression file** (`owasp-dependency-check-suppressions.xml`) for managing false positives; **CycloneDX SBOM** generation (`cyclonedx-maven-plugin`). SpotBugs, PMD, Checkstyle, and ForbiddenAPIs are also configured as static analysis tools. However, no container image scanning is integrated into the CI pipeline, and the OWASP check runs on a daily cron, not on every PR. |
| **Gap** | No container image scanning in CI. OWASP dependency check runs daily (not per-PR), so vulnerabilities could be merged before the next scan. No formal security gate blocking PRs on critical findings. |
| **Recommendation** | Add container image scanning (ECR or Trivy) to the Docker build pipeline. Move OWASP dependency check to run on PRs (in addition to the daily cron). Add a formal security gate that blocks merges on critical/high CVSS findings. |
| **Evidence** | `.github/workflows/codeql.yml`, `.github/workflows/cron-job-its.yml`, `.github/dependabot.yml`, `owasp-dependency-check-suppressions.xml`, `pom.xml` (cyclonedx-maven-plugin, spotbugs-maven-plugin, maven-pmd-plugin) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid has an OpenTelemetry emitter extension (`extensions-contrib/opentelemetry-emitter/`) that can emit OpenTelemetry spans for Druid queries. The extension uses OpenTelemetry SDK 1.7.0 with auto-instrumentation capabilities. Druid also has comprehensive request logging (`docs/operations/request-logging.md`) that logs query execution with timing data. However, the OpenTelemetry extension is a **contrib** extension (not core), meaning it requires explicit opt-in and may have limited community support. It emits query-level spans but does not provide cross-service trace propagation between Druid nodes (Broker → Historical) out of the box. |
| **Gap** | Tracing exists at the query level but cross-service propagation between Druid node types is not automatic. The OpenTelemetry emitter is contrib-only and uses an older SDK version (1.7.0 vs current 1.30+). |
| **Recommendation** | Enable the OpenTelemetry emitter extension in production deployments. Upgrade to a current OpenTelemetry SDK version. Configure trace propagation headers (traceparent/X-Amzn-Trace-Id) between Broker and Historical nodes. Export traces to AWS X-Ray or an OpenTelemetry-compatible backend. |
| **Evidence** | `extensions-contrib/opentelemetry-emitter/pom.xml` (opentelemetry.version=1.7.0), `docs/operations/request-logging.md` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions were found in the repository. No formal definition of acceptable query latency (p99, p95), ingestion throughput, or availability targets. The metrics documentation (`docs/operations/metrics.md`) defines extensive metrics (query/time, query/success, ingestion/events/processed) that could support SLO monitoring, but no SLO thresholds or error budgets are defined. No CloudWatch alarms, Prometheus alerting rules, or SLO dashboards exist in the repository. |
| **Gap** | No SLO definitions. Cannot measure whether the system is meeting user expectations or degrading over time. |
| **Recommendation** | Define SLOs for critical Druid operations: query p99 latency < X ms for interactive queries, ingestion lag < X seconds for streaming ingestion, and cluster availability > 99.9%. Implement SLO monitoring using Druid's metrics emission to Amazon CloudWatch or Prometheus with Amazon Managed Grafana dashboards. |
| **Evidence** | `docs/operations/metrics.md` (metrics defined but no SLO thresholds), repository root (no SLO definitions found) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid has an extensive metrics framework with multiple emitter extensions: `prometheus-emitter` (Prometheus), `graphite-emitter`, `statsd-emitter`, `influxdb-emitter`, `opentsdb-emitter`, `dropwizard-emitter`, `kafka-emitter`, and `ambari-metrics-emitter`. The default configuration includes `JvmMonitor` and `ServiceStatusMonitor` monitors. The metrics documentation (`docs/operations/metrics.md`, 76KB) documents hundreds of metrics across query execution, ingestion, coordination, segment management, and JVM/OS. Some metrics represent business outcomes (query success rate, ingestion events processed, segment availability), while others are purely infrastructure-level (JVM heap, GC time, CPU). The metrics are not systematically organized into "business" vs "infrastructure" categories. |
| **Gap** | Business-relevant metrics exist (query latency, ingestion throughput, segment availability) alongside infrastructure metrics, but no dashboards or structured organization separates business outcome metrics from infrastructure metrics. |
| **Recommendation** | Create dedicated business outcome dashboards (query performance, ingestion health, data freshness) separate from infrastructure dashboards. Export metrics to Amazon Managed Grafana or CloudWatch Dashboards with business-focused views. |
| **Evidence** | `docs/operations/metrics.md`, `extensions-contrib/prometheus-emitter/`, `extensions-contrib/graphite-emitter/`, `examples/conf/druid/cluster/_common/common.runtime.properties` (druid.monitoring.monitors) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration exists in the repository. The `docs/operations/alerts.md` documents Druid's alerting framework, which emits alert events for system issues (e.g., segment load failures, task failures), but no external alerting system (PagerDuty, OpsGenie, CloudWatch Alarms) is configured. No anomaly detection on query latency, error rates, or ingestion lag. No composite alarms or escalation policies. |
| **Gap** | No alerting infrastructure. System issues are not automatically detected or escalated. |
| **Recommendation** | Configure Druid metrics emission to CloudWatch Metrics. Create CloudWatch Alarms for critical thresholds: query error rate > 1%, ingestion lag > 60s, segment unavailability > 0. Enable CloudWatch Anomaly Detection on query latency and throughput. Integrate with PagerDuty or OpsGenie for on-call escalation. |
| **Evidence** | `docs/operations/alerts.md`, repository root (no alerting configuration found) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid documents a rolling update strategy in `docs/operations/rolling-updates.md` with a specific recommended node update order: Historical → MiddleManager/Indexer → Broker → Router → Overlord → Coordinator. This demonstrates operational maturity in the update process design. However, the rolling update is a manual process — no automated deployment tooling (CodeDeploy, ArgoCD, Helm rollouts) implements this strategy. The `docker-compose.yml` provides no deployment strategy configuration. No canary or blue/green deployment automation exists. |
| **Gap** | Rolling update procedure is documented but not automated. No canary or blue/green deployment. All deployments require manual operator execution. |
| **Recommendation** | Implement automated rolling deployments on **Amazon EKS** (preferred) using Kubernetes `RollingUpdate` strategy with `maxUnavailable=0` and `maxSurge=1` to ensure zero-downtime updates. Define update order via deployment dependencies or a CI/CD pipeline that orchestrates the rollout order. Consider ArgoCD progressive delivery for canary deployments of Broker nodes. |
| **Evidence** | `docs/operations/rolling-updates.md`, `distribution/docker/docker-compose.yml` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration testing infrastructure exists. Docker-based integration tests (`docker-tests.yml`) build a full Druid Docker image and run end-to-end tests against a running cluster. The `embedded-tests/` module contains Docker container-based integration tests. The `quidem-ut/` module provides SQL query testing with expected output validation. The unified test pipeline (`unit-and-integration-tests-unified.yml`) runs both unit and integration tests in CI on every push and PR. Code coverage is tracked via JaCoCo and Codecov (`.codecov.yml`). However, Codecov coverage enforcement is disabled (`project: off`, `patch: off`), and some test categories may have coverage gaps. |
| **Gap** | Integration test infrastructure is solid, but code coverage enforcement is disabled. Some areas may lack integration test coverage. |
| **Recommendation** | Enable Codecov coverage enforcement with minimum thresholds (e.g., 70% patch coverage) to prevent regression. Add integration tests for AWS-specific deployment scenarios (S3 deep storage, Kinesis ingestion) using localstack or testcontainers with AWS services. |
| **Evidence** | `.github/workflows/docker-tests.yml`, `.github/workflows/unit-and-integration-tests-unified.yml`, `embedded-tests/`, `quidem-ut/`, `.codecov.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns were found in the repository. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. Druid's documentation includes operational guides (`docs/operations/`) for configuration and tuning, but no structured runbooks for incident response. Druid does have some built-in self-healing (automatic segment rebalancing, task retry on failure), but no external incident response automation exists. |
| **Gap** | No runbooks or incident response automation. Incident response is entirely ad hoc and operator-dependent. |
| **Recommendation** | Create machine-readable runbooks (YAML or Markdown with structured actions) for common incidents: segment unavailability, ingestion failures, ZooKeeper connectivity loss, metadata store failures. Implement SSM Automation documents for automated remediation of common issues. Consider AWS Step Functions for multi-step incident response workflows. |
| **Evidence** | `docs/operations/` (operational guides exist but no structured runbooks), repository root (no runbook files found) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file exists in the repository. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution. The extensive metrics framework exists without ownership assignment. No team-specific monitoring configuration. This is characteristic of an open-source project where observability ownership is delegated to operators rather than defined in the codebase. |
| **Gap** | No observability ownership defined. Monitoring is reactive and fragmented without clear ownership of dashboards, alarms, or SLO definitions. |
| **Recommendation** | For production deployments, create a CODEOWNERS file assigning ownership of observability configurations. Define per-node-type dashboards (Broker dashboard, Historical dashboard, Ingestion dashboard) with named owners. Create an on-call rotation tied to SLO definitions. |
| **Evidence** | Repository root (no CODEOWNERS file), `docs/operations/metrics.md` (metrics defined without ownership) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging governance exists. Since there is no IaC (INF-Q10 = 1), there are no resources to tag. No `default_tags`, no `required-tags` Config rules, no Tag Policies defined. No tagging standard documented. |
| **Gap** | No tagging governance. Without tags, cost allocation, ownership tracking, and blast radius analysis are impossible. |
| **Recommendation** | When creating IaC for Druid infrastructure, define mandatory tags: `Environment` (prod/staging/dev), `Service` (druid), `NodeType` (broker/historical/coordinator/etc.), `Team`, `CostCenter`. Use Terraform `default_tags` or CDK `Tags.of()` for enforcement. Enable AWS Cost Allocation Tags. |
| **Evidence** | Repository root (no IaC, no tagging configuration) |

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q2, APP-Q1, APP-Q2, DATA-Q3, DATA-Q4, SEC-Q7 | Root Maven POM; Java 17, dependency versions (PostgreSQL 42.7.2, MySQL 8.2.0, Derby 10.14.2.0, ZooKeeper 3.8.6, AWS SDK v2 2.40.0), module structure, security plugins |
| `distribution/docker/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage Docker build; distroless base image (gcr.io/distroless/java17-debian12), non-root user (druid, uid 1000) |
| `distribution/docker/docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, APP-Q2, DATA-Q3, OPS-Q5 | Docker Compose deployment; PostgreSQL 17.6, ZooKeeper 3.5.10, 5 Druid service containers, port exposure |
| `distribution/docker/environment` | INF-Q4, SEC-Q5, APP-Q6 | Docker environment config; ZooKeeper host, metadata storage connection, hardcoded PostgreSQL password |
| `examples/conf/druid/cluster/_common/common.runtime.properties` | INF-Q2, INF-Q8, APP-Q6, SEC-Q5, OPS-Q3, DATA-Q1 | Cluster configuration; Derby default, ZooKeeper discovery, S3 deep storage (commented), hidden properties, monitoring monitors |
| `.github/workflows/ci.yml` | INF-Q11 | Unit test CI workflow |
| `.github/workflows/codeql.yml` | INF-Q11, SEC-Q7 | CodeQL SAST scanning for Java, JavaScript, Python |
| `.github/workflows/cron-job-its.yml` | INF-Q11, SEC-Q7 | Daily OWASP dependency vulnerability scanning |
| `.github/workflows/docker-tests.yml` | INF-Q11, OPS-Q6 | Docker-based integration testing |
| `.github/workflows/unit-and-integration-tests-unified.yml` | INF-Q11, OPS-Q6 | Unified test pipeline (unit + integration) |
| `.github/workflows/static-checks.yml` | INF-Q11 | Static code analysis (Checkstyle, PMD, SpotBugs, ErrorProne, OpenRewrite) |
| `.github/dependabot.yml` | SEC-Q7, DATA-Q3 | Dependabot config; Maven daily updates, ZooKeeper version pin |
| `.codecov.yml` | OPS-Q6 | Codecov configuration; coverage enforcement disabled |
| `extensions-core/kafka-indexing-service/` | INF-Q4, APP-Q3 | Kafka consumer integration for streaming ingestion |
| `extensions-core/kinesis-indexing-service/` | INF-Q4, APP-Q3 | Kinesis consumer integration for streaming ingestion |
| `extensions-core/s3-extensions/` | DATA-Q1 | S3 deep storage extension |
| `extensions-core/druid-basic-security/` | SEC-Q3 | Basic authentication extension |
| `extensions-core/druid-pac4j/` | SEC-Q3, SEC-Q4 | OIDC/SAML/OAuth2 authentication extension |
| `extensions-core/druid-kerberos/` | SEC-Q3, SEC-Q4 | Kerberos authentication extension |
| `extensions-contrib/opentelemetry-emitter/` | OPS-Q1 | OpenTelemetry trace emission (contrib, SDK 1.7.0) |
| `extensions-contrib/prometheus-emitter/` | OPS-Q3 | Prometheus metrics emission |
| `extensions-contrib/rabbit-stream-indexing-service/` | INF-Q4 | RabbitMQ stream ingestion |
| `indexing-service/` | INF-Q3, APP-Q4 | Task orchestration, ingestion management, Overlord service |
| `multi-stage-query/` | APP-Q4 | MSQ engine for large-scale batch operations |
| `processing/` | DATA-Q2 | Core query processing engine |
| `sql/` | DATA-Q2, DATA-Q4 | SQL layer (Calcite-based), JDBC support |
| `server/` | APP-Q3, DATA-Q2, DATA-Q4 | HTTP services, JDBI metadata access |
| `web-console/package.json` | APP-Q1 | TypeScript/React web console (Node 20) |
| `docs/operations/security-overview.md` | INF-Q5, INF-Q6, SEC-Q1, SEC-Q3, SEC-Q4 | Security best practices, auth configuration guidance |
| `docs/operations/auth.md` | SEC-Q3 | Authentication configuration documentation |
| `docs/operations/auth-ldap.md` | SEC-Q4 | LDAP integration documentation |
| `docs/operations/tls-support.md` | SEC-Q2 | TLS configuration documentation |
| `docs/operations/dynamic-config-provider.md` | SEC-Q5 | Dynamic config provider for secret management |
| `docs/operations/metrics.md` | OPS-Q2, OPS-Q3 | Metrics documentation (76KB, hundreds of metrics) |
| `docs/operations/alerts.md` | OPS-Q4 | Alerting framework documentation |
| `docs/operations/rolling-updates.md` | OPS-Q5 | Rolling update procedure and node order |
| `docs/operations/high-availability.md` | INF-Q9 | HA recommendations (ZK ensemble, multiple coordinators/brokers) |
| `docs/operations/request-logging.md` | SEC-Q1, OPS-Q1 | Request logging configuration |
| `docs/api-reference/` | APP-Q5 | 14 API reference documents (no versioning convention) |
| `docs/api-reference/legacy-metadata-api.md` | APP-Q5 | Legacy API coexisting with newer endpoints |
| `docs/api-reference/supervisor-api.md` | INF-Q3, APP-Q4 | Supervisor management API |
| `docs/api-reference/tasks-api.md` | INF-Q3, APP-Q4 | Task management API |
| `owasp-dependency-check-suppressions.xml` | SEC-Q7 | OWASP false positive suppressions |
| `AGENTS.md` | APP-Q2 | Module descriptions, development instructions |
| `README.md` | INF-Q10 | References external druid-operator and Helm charts |
| `embedded-tests/` | OPS-Q6 | Docker container-based integration tests |
| `quidem-ut/` | OPS-Q6 | SQL query testing framework |
