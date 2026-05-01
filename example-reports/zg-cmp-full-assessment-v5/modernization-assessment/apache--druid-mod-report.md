# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | druid |
| **Date** | 2026-04-30 |
| **TD Version** | Modernization Readiness Assessment v1.0 |
| **Repo Type** | monorepo |
| **Service Archetype** | data-gateway (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, analytics, database |
| **Context** | Apache Druid: high-performance real-time analytics database. |
| **Overall Score** | **2.41 / 4.0** |

**Archetype Justification**: Druid is a distributed analytics database whose primary value proposition is serving sub-second OLAP queries over pre-indexed columnar data. The query path (Broker → Historical/MiddleManager) dominates the API surface and is read-heavy by design. While the ingestion side has event-processor and orchestrator characteristics (Kafka/Kinesis consumers, Overlord task management), the majority of API endpoints and runtime traffic serve analytics queries. Classified as `data-gateway`.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true

**Monorepo Treatment**: Although classified as `monorepo`, Apache Druid is a single distributed system with tightly-coupled service types (Coordinator, Overlord, Broker, Router, Historical, MiddleManager, Peon, Indexer) sharing one codebase, one Maven build, and one deployment artifact (`apache/druid:37.0.0`). Services are differentiated by runtime command, not by independent codebases. This assessment treats Druid as a single logical application rather than per-service evaluation.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 3.67 / 4.0 | ✅ Mature |
| Data Platform Modernization (DATA) | 3.50 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.41 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No production Infrastructure as Code — all infrastructure is manual or undefined. | Blocks reproducible deployments, disaster recovery, and environment consistency. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute IaC (ECS/EKS/Lambda). Docker images exist but no deployment-to-managed-services defined. | Running on self-managed infrastructure increases operational overhead and limits elastic scaling. Triggers Move to Managed Databases and Modern DevOps pathways. |
| 3 | SEC-Q5: Secrets Management | 1 | Plaintext credentials (`FoolishPassword`) committed in docker-compose.yml and environment file. No Secrets Manager or Vault integration. | Critical security vulnerability — plaintext passwords in version control. |
| 4 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined. Docker-compose exposes ports directly. | No network isolation for production deployments; all services accessible on exposed ports. |
| 5 | INF-Q2: Managed Databases | 1 | Metadata storage is self-managed PostgreSQL in Docker container. No managed database (RDS/Aurora) IaC. | Self-managed databases require manual patching, backup, and failover management. Triggers Move to Managed Databases pathway. |

---

## Quick Agent Wins

### 1. RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists — `docs/` directory contains 14 API reference files, 17 design documents, 31 operations guides, configuration docs, ingestion guides, and tutorials. Total documentation corpus exceeds 200 files.
- **What it enables:** An Amazon Bedrock-powered RAG agent that indexes Druid's comprehensive documentation to answer developer and operator questions about configuration, API usage, ingestion patterns, tuning, and troubleshooting.
- **Additional steps:** Index documentation into a vector store (Amazon OpenSearch Service with vector engine or Amazon Bedrock Knowledge Bases). Generate embeddings from markdown files.
- **Effort:** Medium

### 2. API-Aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 3) with structured HTTP endpoint documentation across 14 files covering SQL API (`/druid/v2/sql`), Tasks API (`/druid/indexer/v1/tasks`), Supervisor API, Compaction API, and more. JSON request/response formats are documented.
- **What it enables:** An agent that discovers and invokes Druid's HTTP APIs as tools — submitting queries, checking task status, managing supervisors, and triggering compaction without requiring users to construct HTTP requests manually.
- **Additional steps:** Generate formal OpenAPI specifications from the existing markdown documentation to enable tool-use agent frameworks to auto-discover endpoints. Currently no OpenAPI/Swagger spec exists.
- **Effort:** Medium

### 3. Data Query Agent

- **Prerequisite:** Druid has a SQL query interface (DATA-Q2 = 4) with a well-documented SQL API (`/druid/v2/sql`), clear schema via `INFORMATION_SCHEMA` tables, and structured JSON responses.
- **What it enables:** A natural-language-to-Druid-SQL agent that translates user questions into Druid SQL queries, executes them via the SQL API, and formats results. Particularly valuable for business analysts who need analytics access without SQL expertise.
- **Additional steps:** Configure Amazon Bedrock agent with Druid SQL dialect reference (Calcite-based with Druid extensions). Set up JDBC connection or HTTP API tool.
- **Effort:** Medium

### 4. DevOps Agent

- **Prerequisite:** CI pipeline exists (INF-Q11 = 2) with comprehensive GitHub Actions workflows — unit tests, static checks, Docker tests, CodeQL scanning, and OWASP dependency checks.
- **What it enables:** An agent that monitors build status, triggers CI runs, reviews test failures, and assists with release management by interacting with GitHub Actions APIs.
- **Additional steps:** Configure GitHub API access for the agent. CI pipeline exists but CD does not — agent's deployment capabilities would be limited to CI operations.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with well-defined boundaries). Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | Container definitions exist (Dockerfile, docker-compose.yml). Contextual guard: Druid already has containerization. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). No commercial DB engines detected in primary configuration — PostgreSQL and MySQL are open source. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (self-managed PostgreSQL in Docker). DATA-Q3 = 3 (supporting). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 (data-gateway archetype, sync reads correct). Druid IS the analytics platform — recommending migration away from it is not applicable. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no production IaC). INF-Q11 = 2 (CI only, no CD). Supporting: OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 3. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "Apache Druid: high-performance real-time analytics database" contains no AI signal terms. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
Apache Druid's metadata storage is self-managed PostgreSQL (version 17.6) running as a Docker container defined in `distribution/docker/docker-compose.yml`. The metadata store houses critical system state — segment records, rule records, configuration records, task-related tables, and audit records. Production deployments recommend PostgreSQL or MySQL (`docs/design/metadata-storage.md`). The current configuration uses plaintext credentials (`FoolishPassword`) and has no automated backup, failover, or encryption at rest.

**Gaps Identified:**
- INF-Q2 = 1: Metadata database is entirely self-managed with no managed service involvement
- No automated backups or point-in-time recovery (INF-Q8 = 1)
- No multi-AZ failover configuration (INF-Q9 = 1)
- No encryption at rest (SEC-Q2 = 1)
- Plaintext credentials in configuration files (SEC-Q5 = 1)

**Recommended Migration Targets (respecting preferences — prefer Aurora):**
- **Amazon Aurora PostgreSQL** (preferred): Migrate Druid's metadata storage to Aurora PostgreSQL. Aurora provides automated backups, point-in-time recovery, Multi-AZ failover, encryption at rest via KMS, and up to 15 read replicas. Druid's PostgreSQL metadata storage extension (`extensions-core/postgresql-metadata-storage/`) is directly compatible.
- **Amazon RDS for PostgreSQL**: A lower-effort alternative if Aurora's advanced features are not required.
- Store metadata credentials in **AWS Secrets Manager** with automated rotation.

**Representative AWS Services:** Aurora PostgreSQL, RDS for PostgreSQL, AWS Secrets Manager, AWS KMS

**Migration Tools:** AWS Database Migration Service (DMS) for live migration from self-managed PostgreSQL to Aurora. The migration is straightforward since Druid uses standard JDBC with DBCP — only the connection URI and credentials need to change.

**Migration Steps:**
1. Provision Aurora PostgreSQL cluster with Multi-AZ, encryption at rest, and automated backups
2. Create Druid metadata schema on Aurora
3. Migrate data from self-managed PostgreSQL using pg_dump/pg_restore or AWS DMS
4. Update Druid configuration (`druid_metadata_storage_connector_connectURI`) to point to Aurora endpoint
5. Store credentials in AWS Secrets Manager; configure Druid's [Environment Variable Dynamic Config Provider](docs/operations/dynamic-config-provider.md) for secret retrieval
6. Validate segment availability, task execution, and coordinator operations

**Links:**
- [AWS Prescriptive Guidance: Migrate to Managed Databases](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-databases/welcome.html)
- [Aurora PostgreSQL Migration Guide](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Migrating.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
Druid has a mature CI pipeline (GitHub Actions) but lacks production infrastructure-as-code and continuous deployment capabilities.

- **IaC Coverage (INF-Q10 = 1):** No Terraform, CloudFormation, CDK, or Helm charts exist for provisioning production infrastructure. The repository contains a Dockerfile and docker-compose.yml for local development only. All production infrastructure must be created manually.
- **CI/CD Automation (INF-Q11 = 2):** CI is comprehensive — 13 GitHub Actions workflows covering unit tests (JDK 17/21), static analysis (Checkstyle, SpotBugs, PMD, forbidden-apis), CodeQL SAST, OWASP dependency checking, Docker integration tests, and JaCoCo coverage. However, no CD pipeline exists — there is no automated deployment to any environment.
- **Deployment Strategy (OPS-Q5 = 1):** No deployment strategy defined. No blue/green, canary, or rolling deployment configuration.
- **Integration Testing (OPS-Q6 = 3):** Docker integration tests exist and run in CI.

**Gaps Identified:**
- No IaC for production infrastructure (networking, compute, databases, monitoring)
- No CD pipeline for automated deployments
- No deployment strategy for safe rollouts
- No resource tagging governance (OPS-Q9 = 1)

**Recommended DevOps Toolchain (respecting preferences — prefer EKS):**

1. **Infrastructure as Code:**
   - Create **Terraform** or **AWS CDK** modules for Druid production infrastructure:
     - VPC with private subnets, security groups, NACLs
     - **Amazon EKS** cluster (preferred) for Druid service orchestration
     - Aurora PostgreSQL for metadata storage
     - S3 buckets for deep storage
     - CloudWatch alarms and dashboards
     - AWS Backup plans for data protection
   - Adopt Helm charts for Druid Kubernetes deployment (community Helm charts exist)

2. **Continuous Deployment:**
   - Extend existing GitHub Actions with deployment stages targeting EKS
   - Implement **ArgoCD** or **AWS CodePipeline** for GitOps-based deployment
   - Use Helm with value overrides per environment (dev, staging, production)

3. **Deployment Strategy:**
   - Implement rolling deployments for stateless services (Broker, Router)
   - Blue/green for stateful services (Historical, MiddleManager) using EKS rolling update strategy
   - Integrate health checks into deployment lifecycle

**Representative AWS Services:** AWS CDK, Amazon EKS, AWS CodePipeline, AWS CodeBuild, Amazon ECR, AWS CloudFormation, AWS Systems Manager

**Links:**
- [AWS Prescriptive Guidance: Move to Modern DevOps](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-modernizing-applications/move-to-modern-devops.html)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [EKS Workshop](https://www.eksworkshop.com/)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure (ECS, EKS, Lambda, Fargate) is defined in IaC. The repository provides Docker images (`distribution/docker/Dockerfile` — multi-stage build using `gcr.io/distroless/java17-debian12` base) and a `docker-compose.yml` for local development with 5 Druid services. Kubernetes extensions exist (`extensions-core/kubernetes-extensions/`, `extensions-core/kubernetes-overlord-extensions/`) providing K8s integration capability, but no Kubernetes manifests, Helm charts, or EKS/ECS Terraform are present. All production compute provisioning is external to this repository. |
| **Gap** | No production compute infrastructure defined — no EKS cluster, no ECS task definitions, no Lambda functions, no Fargate configurations. Container images exist but have no managed orchestration target defined. |
| **Recommendation** | Define EKS cluster infrastructure using Terraform or AWS CDK (preferred per assessment preferences). Create Helm charts for deploying Druid service types (Coordinator, Broker, Historical, MiddleManager, Router) as separate Kubernetes Deployments/StatefulSets on EKS. Leverage Druid's existing Kubernetes extensions for task management. |
| **Evidence** | `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`, `extensions-core/kubernetes-extensions/`, `extensions-core/kubernetes-overlord-extensions/` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Metadata storage is a self-managed PostgreSQL 17.6 instance running as a Docker container (`distribution/docker/docker-compose.yml`: `image: postgres:17.6`). The `distribution/docker/environment` file configures the JDBC connection: `druid_metadata_storage_connector_connectURI=jdbc:postgresql://postgres:5432/druid`. Documentation (`docs/design/metadata-storage.md`) recommends MySQL or PostgreSQL for production but the repository has no managed database IaC. No `aws_rds_*`, `aws_dynamodb_*`, or any managed database resource definitions exist. |
| **Gap** | All database infrastructure is self-managed. No managed database provisioning, no automated failover, no managed backups, no encryption at rest. |
| **Recommendation** | Migrate metadata storage to **Amazon Aurora PostgreSQL** (preferred). Druid's `postgresql-metadata-storage` extension is directly compatible. Provision Aurora with Multi-AZ, automated backups with 7+ day retention, PITR enabled, and KMS encryption. Update `druid_metadata_storage_connector_connectURI` to Aurora endpoint. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `distribution/docker/environment`, `docs/design/metadata-storage.md`, `extensions-core/postgresql-metadata-storage/` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid has built-in workflow orchestration for its ingestion pipeline: the Overlord service coordinates ingestion tasks, the MiddleManager/Peon system executes them, and the tasks API (`/druid/indexer/v1/tasks`) provides status polling. This is a proprietary, application-embedded orchestration system — not a managed external service (Step Functions, Temporal, etc.). For the `data-gateway` archetype, the read path (queries) has no multi-step workflows; orchestration applies only to the background ingestion/maintenance jobs. The existing Overlord/MiddleManager orchestration is functional but not externalized to a managed service. |
| **Gap** | Ingestion orchestration is built into the application rather than using a managed workflow service. While functional, it lacks the visibility, error handling, and operational tooling that managed orchestration provides. |
| **Recommendation** | For the data-gateway archetype, this is a minor gap. The built-in orchestration is appropriate for Druid's domain. Consider using **AWS Step Functions** for complex multi-step ingestion workflows that span beyond Druid (e.g., S3 → transform → Druid ingestion → validation), or **Amazon EventBridge** for event-driven ingestion triggers. |
| **Evidence** | `docs/design/overlord.md`, `docs/design/middlemanager.md`, `docs/api-reference/tasks-api.md`, `indexing-service/` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid's read path is synchronous (HTTP queries to Broker → Historical/MiddleManager), which is the correct pattern for a data-gateway archetype. The ingestion path consumes from external Kafka (via `extensions-core/kafka-indexing-service/`, Apache Kafka client 3.9.1) and Kinesis (via `extensions-core/kinesis-indexing-service/`). These are managed consumers of external messaging infrastructure. The repository does not provision the messaging infrastructure itself — it provides client-side extensions. A contrib extension for RabbitMQ Stream exists (`extensions-contrib/rabbit-stream-indexing-service/`). The kafka-emitter contrib extension enables publishing Druid metrics to Kafka. |
| **Gap** | Synchronous reads dominate and are correct for this archetype. The Kafka/Kinesis ingestion clients are well-implemented. However, the repository does not define the messaging infrastructure — this is assumed to be provisioned externally. No Amazon EventBridge integration exists for event-driven ingestion triggering. |
| **Recommendation** | Synchronous HTTP for queries is appropriate for this archetype — adopting async messaging for the query path is NOT recommended. For ingestion, consider adding **Amazon EventBridge** integration for event-driven ingestion triggers (e.g., new data arriving in S3 triggers ingestion). Avoid self-managed Kafka (per preferences) — use **Amazon MSK Serverless** or **Amazon Kinesis** for streaming ingestion sources. |
| **Evidence** | `extensions-core/kafka-indexing-service/`, `extensions-core/kinesis-indexing-service/`, `extensions-contrib/rabbit-stream-indexing-service/`, `extensions-contrib/kafka-emitter/`, `pom.xml` (apache.kafka.version=3.9.1) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security group, NACL, or network segmentation is defined in the repository. The `docker-compose.yml` exposes ports directly to the host: PostgreSQL (5432), ZooKeeper (2181), Coordinator (8081), Broker (8082), Historical (8083), MiddleManager (8091, 8100-8105), Router (8888). No `aws_vpc`, `aws_subnet`, or `aws_security_group` resources exist. The security documentation (`docs/operations/security-overview.md`) recommends using firewalls and network layer filtering but no IaC enforces this. |
| **Gap** | No network security infrastructure defined. All services exposed without isolation. No private subnets, no security groups, no VPC endpoints. |
| **Recommendation** | Define VPC infrastructure with private subnets for all Druid services and the metadata database. Only the Router/Broker should be accessible from application subnets via an **API Gateway** (preferred) or ALB. Place Historical, MiddleManager, Coordinator, and Overlord in private subnets with no direct internet access. Use VPC endpoints for S3 (deep storage) and other AWS services. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `docs/operations/security-overview.md` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS managed API entry point (API Gateway, ALB, CloudFront) is defined. Druid's Router service (`docs/design/router.md`) acts as an internal unified API gateway — routing queries to Brokers, and management requests to Coordinators/Overlords. It also hosts the web console. However, no managed load balancer or API gateway is provisioned in front of the Router. The security docs recommend using "an API gateway to restrict access from untrusted networks" but this is not implemented in IaC. |
| **Gap** | No managed entry point with throttling, authentication, or request validation in front of Druid services. |
| **Recommendation** | Deploy an **Amazon API Gateway** (preferred) or Application Load Balancer in front of Druid's Router/Broker services. Configure throttling, authentication (Cognito/JWT), and request validation. Use API Gateway for external SQL query access and ALB for internal service routing. |
| **Evidence** | `docs/design/router.md`, `docs/operations/security-overview.md`, `distribution/docker/docker-compose.yml` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists in the repository. No ASG, ECS service scaling, EKS HPA, Lambda concurrency, or DynamoDB auto-scaling definitions. The `docker-compose.yml` runs fixed single instances of each service. Druid's architecture supports horizontal scaling of Brokers and Historicals, but no automated scaling mechanisms are defined. |
| **Gap** | All capacity is statically provisioned. No ability to scale Broker or Historical instances based on query load, or MiddleManagers based on ingestion load. |
| **Recommendation** | When deploying on EKS (preferred), configure Horizontal Pod Autoscaler (HPA) for Broker and Historical pods based on CPU/memory and custom Druid metrics (query/time, segment/count). Use Cluster Autoscaler or Karpenter for node-level scaling. Consider **AWS Graviton** instances for cost-optimized compute. |
| **Evidence** | `distribution/docker/docker-compose.yml` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. The self-managed PostgreSQL container in `docker-compose.yml` has no backup_retention_period, no PITR, no snapshot lifecycle. The metadata storage documentation (`docs/design/metadata-storage.md`) warns "there is no way to restore lost metadata" and recommends high availability, but no backup IaC exists. Deep storage (segments) on local disk in the dev setup has no backup configuration. No `aws_backup_plan` or S3 versioning defined. |
| **Gap** | No automated backups for metadata storage or deep storage. Critical metadata loss would be unrecoverable. |
| **Recommendation** | When migrating to Aurora PostgreSQL, enable automated backups with 14-day retention and PITR. For deep storage on S3, enable versioning and configure lifecycle policies. Create an **AWS Backup** plan covering Aurora and S3 with cross-region replication for disaster recovery. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `docs/design/metadata-storage.md` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists in IaC. The `docker-compose.yml` runs all services on a single host. Druid's architecture documentation (`docs/design/architecture.md`) describes a distributed design supporting multiple instances of each service type, and `docs/operations/high-availability.md` provides HA recommendations (ZK cluster of 3-5 nodes, multiple Coordinators/Overlords, Brokers behind load balancer, PostgreSQL replication). However, none of this is enforced through IaC — it relies on manual operator implementation. |
| **Gap** | No multi-AZ deployment configuration. Single-node docker-compose is the only defined deployment topology. HA architecture is documented but not codified. |
| **Recommendation** | Define EKS cluster spanning 2+ AZs with pod anti-affinity rules for Druid services. Deploy Aurora PostgreSQL with Multi-AZ failover. Run ZooKeeper ensemble across 3 AZs (or consider migrating to AWS-managed alternatives). Distribute Historical segment replicas across AZs. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `docs/design/architecture.md`, `docs/operations/high-availability.md` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No production Infrastructure as Code exists. No Terraform files (`.tf`), no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize configurations were found. The only infrastructure-defining files are `distribution/docker/Dockerfile` (container image build) and `distribution/docker/docker-compose.yml` (local development environment). All production infrastructure — networking, compute, databases, monitoring, and operational resources — must be provisioned manually. |
| **Gap** | 0% IaC coverage for production infrastructure. All infrastructure is manually created (ClickOps). |
| **Recommendation** | Create IaC covering all production infrastructure: VPC/networking, EKS cluster, Aurora PostgreSQL, S3 deep storage, CloudWatch monitoring, AWS Backup plans, and IAM roles. Use **Terraform** or **AWS CDK** (preferred for teams familiar with TypeScript/Java). Start with networking and compute, then add database and monitoring resources. Create Helm charts for Druid Kubernetes deployment. |
| **Evidence** | Repository root (no `.tf`, no `cdk.json`, no `template.yaml`, no `Chart.yaml` found) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid has comprehensive CI automation via 13 GitHub Actions workflows. **CI capabilities:** Unit tests on JDK 17 and 21 with matrix strategy (`ci.yml`), Docker integration tests (`docker-tests.yml`), static analysis — Checkstyle, SpotBugs, PMD, forbidden-apis (`static-checks.yml`), CodeQL SAST for Java/JavaScript/Python (`codeql.yml`), OWASP dependency vulnerability scanning (`cron-job-its.yml`), JaCoCo coverage reporting, QTest/Quidem SQL validation, packaging validation, and OpenRewrite automated refactoring. **CD gaps:** No deployment pipeline exists. No CodeDeploy, no Helm deployment, no ArgoCD, no environment-specific deployment stages. The CI builds and tests artifacts but does not deploy to any environment. This is typical for an open-source project distributed as release artifacts via Maven Central and Docker Hub. |
| **Gap** | Build is fully automated but deployment is entirely manual. No CD pipeline for application or infrastructure changes. |
| **Recommendation** | Add CD stages to the existing GitHub Actions pipeline: build Docker image → push to **Amazon ECR** → deploy to EKS via Helm upgrade (or implement ArgoCD for GitOps). Add environment-specific deployment stages (dev → staging → production) with approval gates. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/static-checks.yml`, `.github/workflows/codeql.yml`, `.github/workflows/docker-tests.yml`, `.github/workflows/cron-job-its.yml`, `.github/workflows/unit-and-integration-tests-unified.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is **Java 17** (`pom.xml`: `<java.version>17</java.version>`). Modern Java version with current, well-maintained dependencies: Jackson 2.19.2, Jetty 12.0.30, Guice 6.0.0, Apache Curator 5.8.0, AWS SDK v2 (2.40.0), Netty 4.2.6. CI tests on both JDK 17 and JDK 21. Secondary language is **TypeScript 5.5** (`web-console/package.json`) with React 18.3 for the management UI. Node.js 20+ required. AWS SDK v2 is current. Java has first-class AWS SDK coverage and mature cloud-native tooling. No legacy language versions detected — no Java 8, no deprecated frameworks. |
| **Gap** | N/A — modern language versions with current dependencies. |
| **Recommendation** | No immediate action needed. Continue testing on JDK 21 for future LTS migration. Consider adopting GraalVM native-image for faster startup in containerized deployments. |
| **Evidence** | `pom.xml` (java.version=17, aws.sdk.v2.version=2.40.0, jackson.version=2.19.2, jetty.version=12.0.30), `web-console/package.json` (typescript 5.5, react 18.3), `.github/workflows/ci.yml` (JDK 17 and 21 matrix) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid is a **modular monolith** — a single codebase producing one deployment artifact that runs different service roles based on runtime configuration. The `docker-compose.yml` deploys the same image (`apache/druid:37.0.0`) 5 times with different commands (`coordinator`, `broker`, `historical`, `middleManager`, `router`). The architecture has well-defined module boundaries: `processing/` (core query engine), `server/` (common server functionality), `sql/` (SQL planning via Calcite), `indexing-service/` (task framework), `multi-stage-query/` (MSQ engine). Each module has clear interfaces. Metadata storage is shared across all services but uses separate tables per service role (segments table for Coordinator, task tables for Overlord). No circular dependencies detected in the Maven module graph. The architecture supports independent scaling of service types. |
| **Gap** | While module boundaries are well-defined, all services share a single deployment artifact (JAR/Docker image). Independent versioning and deployment of individual service types is not supported — a change to any module requires rebuilding and redeploying the entire distribution. |
| **Recommendation** | Druid's modular monolith architecture is appropriate for its domain (distributed analytics database). The current design allows independent scaling via multiple instances with different service roles. If independent service versioning becomes a requirement, consider extracting the web-console as a separate deployable (it's already a separate `npm` build) and evaluating whether the query path (Broker/Historical) and ingestion path (Overlord/MiddleManager) could be split into separate distribution artifacts. |
| **Evidence** | `pom.xml` (75+ Maven modules), `distribution/docker/docker-compose.yml`, `docs/design/architecture.md`, `AGENTS.md` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | For the `data-gateway` archetype, synchronous reads are the correct pattern. Druid's query path is synchronous HTTP: clients submit queries to the Broker via REST API (`/druid/v2/sql`, `/druid/v2/`), the Broker fans out to Historical and MiddleManager nodes, merges results, and returns them synchronously. This is optimal for sub-second OLAP queries. The ingestion path uses async patterns: Kafka indexing service (`extensions-core/kafka-indexing-service/`) consumes from Kafka topics asynchronously, and Kinesis indexing service (`extensions-core/kinesis-indexing-service/`) consumes from Kinesis streams. Internal coordination uses ZooKeeper for async state propagation (leader election, segment announcements, service discovery). |
| **Gap** | N/A — sync reads are correct for this archetype, and async is available for ingestion and coordination flows. |
| **Recommendation** | Synchronous HTTP for queries is appropriate for this archetype — async messaging for the query path is NOT recommended. The current sync/async balance is architecturally sound. |
| **Evidence** | `docs/api-reference/sql-api.md`, `docs/design/broker.md`, `extensions-core/kafka-indexing-service/`, `extensions-core/kinesis-indexing-service/`, `docs/design/zookeeper.md` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | For the `data-gateway` archetype, no user-facing operations exceed 30 seconds. Druid queries are designed for sub-second to seconds-range response times. Heavy ingestion jobs (batch and streaming) are handled asynchronously via the Overlord/MiddleManager/Peon task system with full status polling support. The Tasks API (`/druid/indexer/v1/tasks`) provides task status, task detail, and task shutdown endpoints (`docs/api-reference/tasks-api.md`). Compaction tasks are also async with monitoring APIs. Reindexing and export operations use the same async task framework. |
| **Gap** | N/A — long-running operations (ingestion, compaction) are already async with status polling. Query operations are bounded by design. |
| **Recommendation** | No action needed. The async task framework with status polling APIs is well-designed. |
| **Evidence** | `docs/api-reference/tasks-api.md`, `docs/design/overlord.md`, `docs/design/middlemanager.md`, `docs/design/indexer.md` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid uses URL-path-based API versioning for most endpoints. The SQL API uses `/druid/v2/sql`, native queries use `/druid/v2/`, and task management uses `/druid/indexer/v1/tasks`. Supervisor APIs use `/druid/indexer/v1/supervisor`. The versioning is consistently applied across major API surfaces. However, some management APIs (Coordinator, data management) use unversioned paths. Backward compatibility is maintained across releases — the API docs note deprecation of older endpoints. No formal backward compatibility guarantee or changelog is documented for API consumers. |
| **Gap** | Versioning applied to most but not all endpoints. Some management APIs lack version prefixes. No formal API compatibility policy documented for external consumers. |
| **Recommendation** | Standardize versioning across all API endpoints. Document a formal API compatibility policy. Consider generating **OpenAPI specifications** from the existing markdown documentation to enable automated compatibility checking and agent tool discovery. |
| **Evidence** | `docs/api-reference/sql-api.md` (`/druid/v2/sql`), `docs/api-reference/tasks-api.md` (`/druid/indexer/v1/tasks`), `docs/api-reference/json-querying-api.md` (`/druid/v2/`) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Druid uses **Apache ZooKeeper** for dynamic internal service discovery (`docs/design/zookeeper.md`). Services register themselves via ephemeral znodes at `${druid.zk.paths.announcementsPath}/${druid.host}`, and other services (Coordinator, Broker) watch these paths to discover available nodes and their segments. ZooKeeper also handles Coordinator and Overlord leader election. No hard-coded service endpoints. Additionally, Druid provides Kubernetes-native extensions (`extensions-core/kubernetes-extensions/`) for K8s-based service discovery, and a Consul extension (`extensions-contrib/consul-extensions/`) for Consul-based discovery. |
| **Gap** | N/A — dynamic service discovery is fully implemented via ZooKeeper with K8s and Consul alternatives available. |
| **Recommendation** | When deploying on EKS, consider transitioning from ZooKeeper to Kubernetes-native service discovery using Druid's Kubernetes extensions. This eliminates the ZooKeeper dependency and operational overhead. |
| **Evidence** | `docs/design/zookeeper.md`, `extensions-core/kubernetes-extensions/`, `extensions-contrib/consul-extensions/`, `distribution/docker/environment` (`druid_zk_service_host=zookeeper`) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid supports S3 as deep storage via `extensions-core/s3-extensions/`, enabling columnar segment files to be stored in S3. The `docs/design/deep-storage.md` documents S3 as the recommended deep storage for clustered deployments. Additionally, Druid can ingest data directly from S3 (batch ingestion from S3 paths). However, Druid is designed for structured/semi-structured time-series and event data — it does not handle unstructured documents (PDFs, images, text files). No parsing pipeline (Textract, Tika) is integrated. The default docker-compose configuration uses local storage (`druid_storage_type=local`). |
| **Gap** | Data is stored in S3 (when configured) but no automated parsing or extraction pipeline exists for unstructured content. Druid's focus is structured columnar data, not documents. |
| **Recommendation** | For the analytics database use case, unstructured document parsing is not a primary concern. However, if unstructured data sources (logs, documents) need to be ingested, consider using **Amazon Textract** or **AWS Glue** for pre-processing before Druid ingestion. Ensure production deep storage is configured to use S3 rather than local disk. |
| **Evidence** | `extensions-core/s3-extensions/`, `docs/design/deep-storage.md`, `distribution/docker/environment` (`druid_storage_type=local`) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Druid has an exemplary unified data access architecture. All client queries go through the **Broker** service, which provides a single entry point for both native JSON queries (`/druid/v2/`) and SQL queries (`/druid/v2/sql`). The Broker routes queries to appropriate Historical and MiddleManager nodes, merges results, and returns them to the client. The SQL layer (`sql/` module) uses Apache Calcite for query planning and translates SQL to native Druid queries. The processing layer (`processing/` module) provides the core query engine. No direct access to data servers bypassing the Broker is recommended. This is a textbook centralized data access pattern with a single point of data contract. |
| **Gap** | N/A — data access is fully centralized through the Broker. |
| **Recommendation** | No action needed. The Broker-based query routing is a mature, well-designed pattern. |
| **Evidence** | `docs/design/broker.md`, `docs/design/architecture.md`, `sql/`, `processing/`, `docs/api-reference/sql-api.md` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Metadata storage versions:** PostgreSQL 17.6 is pinned in docker-compose.yml (`image: postgres:17.6`) — current major version, not approaching EOL. MySQL driver 8.2.0 is pinned in `pom.xml` — current. MariaDB driver 2.7.3. **ZooKeeper:** version 3.8.6 pinned in `pom.xml` — current LTS, but ZooKeeper 3.5.10 is used in docker-compose.yml (`image: zookeeper:3.5.10`), which is approaching end of support. **Derby:** version 10.14.2.0 in `pom.xml` — Derby 10.14 was released in 2017 and is effectively stale (development mode only, so impact is limited). No documented version-update procedure covering downtime windows, rollback, or risk acknowledgment. |
| **Gap** | ZooKeeper 3.5.10 in docker-compose is older than the 3.8.6 client version in pom.xml — version mismatch. Derby 10.14.2.0 is very old (development use only). No documented version-update procedure exists. |
| **Recommendation** | Update `docker-compose.yml` ZooKeeper image to match the client version (3.8.x). Document a version-update procedure for metadata storage covering downtime windows and rollback. Consider dropping Derby support in favor of PostgreSQL-only for development environments using Testcontainers (already present: `extensions-core/druid-testcontainers/`). |
| **Evidence** | `distribution/docker/docker-compose.yml` (postgres:17.6, zookeeper:3.5.10), `pom.xml` (zookeeper.version=3.8.6, derby.version=10.14.2.0, mysql.version=8.2.0, postgresql.version=42.7.2) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Druid does **not** use stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the Java application layer. The metadata storage is used for simple CRUD operations on system tables (segments, rules, configs, tasks, audit) via standard JDBC with Apache DBCP connection pooling. Druid's own SQL engine is Calcite-based and executes queries against Druid's columnar data — it does not use database-specific SQL features. No `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` were found in the repository. The metadata storage schemas are portable across PostgreSQL, MySQL, and Derby. |
| **Gap** | N/A — no stored procedures or proprietary SQL. All logic is in the application layer. |
| **Recommendation** | No action needed. The clean separation of business logic from the database layer makes metadata storage migration straightforward. |
| **Evidence** | `docs/design/metadata-storage.md`, `extensions-core/postgresql-metadata-storage/`, `extensions-core/mysql-metadata-storage/`, repository-wide search for `.sql` files (none found) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS CloudTrail or equivalent cloud audit logging is configured. No IaC defines CloudTrail resources. Druid has an application-level audit table in metadata storage (`docs/design/metadata-storage.md`: "The audit table stores the audit history for configuration changes such as rule changes done by Coordinator and other config changes"). However, this covers only Druid configuration changes — not API access, data access, or infrastructure-level audit trails. No log file validation or immutable storage is configured. |
| **Gap** | No CloudTrail for AWS-level audit logging. Application-level audit is limited to configuration changes. No immutable log storage. |
| **Recommendation** | When deploying on AWS, enable **AWS CloudTrail** with log file validation and S3 Object Lock for immutable storage. Configure Druid's request logging (`docs/operations/request-logging.md`) to emit to CloudWatch Logs for query audit trails. Enable VPC Flow Logs for network-level auditing. |
| **Evidence** | `docs/design/metadata-storage.md` (audit table), `docs/operations/request-logging.md`, repository (no `aws_cloudtrail` resources found) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured. No KMS key references, no `kms_key_id` on any resource, no encryption configuration in docker-compose.yml or environment files. The self-managed PostgreSQL container has no encryption. Local deep storage (`druid_storage_type=local`) has no encryption. No IaC exists to configure S3 server-side encryption, EBS encryption, or RDS encryption. |
| **Gap** | No encryption at rest for metadata storage, deep storage, or segment caches. Sensitive metadata (segment locations, task configurations, audit records) is stored unencrypted. |
| **Recommendation** | When migrating to Aurora PostgreSQL, enable encryption at rest with **AWS KMS** customer-managed keys. Configure S3 deep storage buckets with default SSE-KMS encryption. Enable EBS encryption for EKS worker nodes hosting Historical segment caches. Centralize key management with a documented rotation policy. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `distribution/docker/environment`, repository (no KMS references found) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid provides authentication extensions but they are **not enabled by default**. Available options: `druid-basic-security` (basic HTTP auth with internal credential store), `druid-kerberos` (Kerberos/SPNEGO), `druid-pac4j` (OIDC/SAML/CAS federation). The default `docker-compose.yml` and `environment` files do not load any security extensions (`druid_extensions_loadList` includes no security extensions). The security documentation (`docs/operations/security-overview.md`) states: "By default, security features in Druid are disabled" and recommends enabling for production. API key or static credential authentication is available through basic-security but is not token-based (OAuth2/JWT). The pac4j extension supports OIDC tokens. |
| **Gap** | Authentication is available as opt-in extensions but not active by default. Default configuration exposes all API endpoints without authentication. No token-based auth (OAuth2/JWT) is configured — only basic auth and Kerberos are available as core extensions, with OIDC via pac4j. |
| **Recommendation** | Enable the `druid-pac4j` extension for OIDC-based authentication, integrating with **Amazon Cognito** (preferred for AWS deployments). For API access, deploy an **Amazon API Gateway** (preferred) with Cognito authorizer in front of Druid's Router/Broker for JWT validation and throttling. |
| **Evidence** | `extensions-core/druid-basic-security/`, `extensions-core/druid-kerberos/`, `extensions-core/druid-pac4j/`, `distribution/docker/environment` (no security extensions in loadList), `docs/operations/security-overview.md` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid's `druid-pac4j` extension supports OIDC and SAML federation with external identity providers, and `druid-kerberos` supports Kerberos integration. These enable centralized identity integration with providers like Cognito, Okta, or Ping Identity. However, these extensions are opt-in — neither is enabled in the default configuration. The `druid-basic-security` extension provides a standalone credential store that does not federate with any external IdP. The current default configuration manages no authentication at all. |
| **Gap** | Centralized IdP integration is available via pac4j extension but not enabled. Default configuration has no authentication, making IdP integration irrelevant until auth is enabled. |
| **Recommendation** | Enable `druid-pac4j` with OIDC configuration pointing to **Amazon Cognito** as the centralized identity provider. Configure SSO for the Druid web console via Cognito's hosted UI. For programmatic API access, use Cognito user pool tokens or machine-to-machine credentials. |
| **Evidence** | `extensions-core/druid-pac4j/`, `extensions-core/druid-kerberos/`, `extensions-core/druid-basic-security/`, `docs/operations/auth.md` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **CRITICAL:** Plaintext credentials are committed in the repository. `distribution/docker/docker-compose.yml` contains: `POSTGRES_PASSWORD=FoolishPassword`, `POSTGRES_USER=druid`. `distribution/docker/environment` contains: `druid_metadata_storage_connector_password=FoolishPassword`, `druid_metadata_storage_connector_user=druid`. These are version-controlled plaintext credentials. No AWS Secrets Manager, HashiCorp Vault, or any secrets management system is referenced. Druid does provide a [Dynamic Config Provider](docs/operations/dynamic-config-provider.md) mechanism that supports environment variable-based secret injection, but the default configuration uses hardcoded values. While labeled as development credentials, they are committed to the repository and establish a pattern that could carry into production. |
| **Gap** | Plaintext credentials in version-controlled files. No secrets management system. No credential rotation. |
| **Recommendation** | **Immediate:** Remove plaintext credentials from version control. Use `.env` files excluded via `.gitignore` for local development, or use Docker secrets. **Production:** Store all credentials in **AWS Secrets Manager** with automated rotation. Configure Druid's Environment Variable Dynamic Config Provider to inject secrets at runtime from Secrets Manager via EKS pod identity or IAM roles for service accounts (IRSA). |
| **Evidence** | `distribution/docker/docker-compose.yml` (POSTGRES_PASSWORD=FoolishPassword), `distribution/docker/environment` (druid_metadata_storage_connector_password=FoolishPassword), `docs/operations/dynamic-config-provider.md` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Dockerfile uses **distroless** base image (`gcr.io/distroless/java17-debian12`) — a security best practice providing minimal attack surface with no shell (busybox added separately), no package manager, and no unnecessary system tools. Multi-stage build reduces image size. Non-root user (`druid:1000`) is configured. OWASP dependency vulnerability checking runs daily via cron (`cron-job-its.yml`) and on changes to the suppressions file, using NVD API key for vulnerability data. The OWASP suppressions file (`owasp-dependency-check-suppressions.xml`, 744 lines) shows active vulnerability triage. Static analysis tools (SpotBugs, PMD, Checkstyle, forbidden-apis) enforce code quality. No SSM Patch Manager or AWS Inspector configuration (no IaC). |
| **Gap** | No managed patching system (SSM Patch Manager) or runtime vulnerability scanning (AWS Inspector). OWASP dependency check is comprehensive but runs as a cron job, not as a blocking gate in every PR pipeline. |
| **Recommendation** | When deploying on EKS, enable **Amazon Inspector** for container image scanning. Integrate OWASP dependency check as a blocking gate in the PR pipeline (currently runs only on cron and when suppressions change). Consider using **Amazon ECR** image scanning for automated vulnerability detection on push. |
| **Evidence** | `distribution/docker/Dockerfile` (distroless base, non-root user), `.github/workflows/cron-job-its.yml` (OWASP dependency-check), `owasp-dependency-check-suppressions.xml` (744 lines), `codestyle/spotbugs-exclude.xml`, `codestyle/checkstyle.xml`, `codestyle/pmd-ruleset.xml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **SAST:** CodeQL runs in CI (`codeql.yml`) covering Java, JavaScript, and Python with `security-and-quality` query suite. Runs on push to master, PRs, and weekly schedule. Uses custom config (`.github/config/codeql-config.yml`). **Dependency scanning:** OWASP dependency-check runs as a cron job (`cron-job-its.yml`) using NVD API. Dependabot is configured for Maven dependencies (`.github/dependabot.yml`) with daily checks and 14-day cooldown. **Static analysis:** Checkstyle, SpotBugs, PMD, and forbidden-apis run on every PR (`static-checks.yml`). **Gaps:** No container image scanning in CI pipeline. No DAST. No explicit security gate that blocks merges on critical findings — CodeQL results are reported but not configured as a blocking check. |
| **Gap** | No container image scanning. No blocking security gate on critical findings. OWASP dependency check runs as cron, not on every PR. |
| **Recommendation** | Add **Amazon ECR** image scanning or Trivy to the Docker test workflow. Configure CodeQL as a required status check that blocks PRs on critical/high findings. Move OWASP dependency check to run on every PR (not just cron). Consider adding DAST via OWASP ZAP against the Docker integration test environment. |
| **Evidence** | `.github/workflows/codeql.yml`, `.github/workflows/cron-job-its.yml`, `.github/workflows/static-checks.yml`, `.github/config/codeql-config.yml`, `.github/dependabot.yml`, `owasp-dependency-check-suppressions.xml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid has an extensible emitter framework for metrics, with an **OpenTelemetry emitter** available as a contrib extension (`extensions-contrib/opentelemetry-emitter/`). Additional emitter backends include Prometheus (`extensions-contrib/prometheus-emitter/`), StatsD, Graphite, Dropwizard, Kafka, InfluxDB, OpenTSDB, and Ambari. These emitters publish Druid's internal metrics (query times, segment counts, ingestion rates, JVM stats). However, the emitter framework is primarily metric-oriented — it does not implement distributed request tracing with trace ID propagation across service boundaries (Broker → Historical fan-out). No `traceparent` or `X-Amzn-Trace-Id` header propagation is built into the default request path. The OpenTelemetry emitter bridges Druid metrics to OTel but does not add tracing spans. |
| **Gap** | Basic per-service metrics exist. No cross-service distributed tracing with propagated trace IDs. Query fan-out from Broker to Historicals cannot be traced end-to-end. |
| **Recommendation** | Integrate **AWS X-Ray** or **OpenTelemetry** tracing SDK into Druid's Broker and Historical request paths. Add trace ID propagation on internal HTTP calls. When deploying on EKS, use the **AWS Distro for OpenTelemetry (ADOT)** sidecar for automatic instrumentation. Enable the Prometheus emitter for metrics and add tracing as a separate concern. |
| **Evidence** | `extensions-contrib/opentelemetry-emitter/`, `extensions-contrib/prometheus-emitter/`, `extensions-contrib/statsd-emitter/`, `docs/operations/metrics.md` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No formal SLO definitions exist in the repository. No error budget tracking, no SLO configuration files, no SLO dashboards. The metrics documentation (`docs/operations/metrics.md`) describes extensive metrics including query latency (`query/time`), query success/failure, ingestion rates, and segment availability, but these are raw metrics — not wrapped in SLO definitions with targets and error budgets. |
| **Gap** | No SLOs defined for any user-facing journey. No formal definition of acceptable query latency, availability, or ingestion throughput targets. |
| **Recommendation** | Define SLOs for critical user journeys: query p99 latency < Xms, query availability > 99.9%, ingestion lag < Y seconds. Implement SLO monitoring using Druid's Prometheus emitter with **Amazon Managed Grafana** for SLO dashboards and error budget tracking. Use **CloudWatch** composite alarms for SLO breach alerting. |
| **Evidence** | `docs/operations/metrics.md`, repository (no SLO definition files found) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid publishes extensive operational and business-relevant metrics via its emitter framework (`docs/operations/metrics.md` — 658 lines documenting metrics). Metrics cover: query performance (query/time, query/bytes, query/count per datasource), ingestion rates (ingest/events/*, ingest/rows/*, ingest/persists/*), segment management (segment/count, segment/size, segment/loadQueue/*), coordination metrics, and JVM metrics. These go beyond pure infrastructure metrics — query performance and ingestion throughput are business-relevant metrics for an analytics database. Multiple emitter backends (Prometheus, StatsD, Graphite, etc.) enable integration with monitoring systems. However, no dashboards or metric visualization is defined in the repository. |
| **Gap** | Rich metrics are published but not all are systematically organized as business outcome metrics with dashboards. No pre-built dashboards or metric alerting rules are defined in the repository. |
| **Recommendation** | Create **Amazon Managed Grafana** dashboards organized by business outcome: query SLAs (p50/p95/p99 latency per datasource), ingestion health (events/sec, lag, failures), and data availability (segment count, replication factor). Use the Prometheus emitter as the metrics backend. |
| **Evidence** | `docs/operations/metrics.md`, `extensions-contrib/prometheus-emitter/`, `extensions-contrib/statsd-emitter/`, `extensions-contrib/graphite-emitter/` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration exists in the repository. No CloudWatch anomaly detection, no alarm definitions, no PagerDuty/OpsGenie integration, no composite alarms. The Druid documentation describes an alerting system (`docs/operations/alerts.md`) for internal Druid alerts (segment load failures, task failures), but these are application-level alerts emitted through the emitter framework — not CloudWatch or external monitoring system alarms. No threshold-based or anomaly-based alerting is configured. |
| **Gap** | No alerting for query latency degradation, ingestion failures, segment load failures, or infrastructure anomalies. Application-level alerts exist but are not connected to an external alerting system. |
| **Recommendation** | Configure **Amazon CloudWatch** alarms on Druid metrics exported via Prometheus emitter and CloudWatch agent. Set up anomaly detection on query latency (`query/time`) and error rates. Use CloudWatch composite alarms for multi-signal alerting. Integrate with **Amazon SNS** and PagerDuty/OpsGenie for on-call notification. |
| **Evidence** | `docs/operations/alerts.md`, repository (no alarm definitions found) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy is defined in the repository. No blue/green, canary, or rolling deployment configuration. No CodeDeploy appspec, no Helm canary, no Argo Rollouts. The `docker-compose.yml` is for local development only. The documentation describes rolling updates (`docs/operations/rolling-updates.md`) with guidance on safe upgrade order (Historicals first, then MiddleManagers, then Brokers, then Coordinator/Overlord) but this is manual operational guidance, not automated deployment configuration. |
| **Gap** | No automated deployment strategy. All production deployments are manual. Rolling update guidance exists as documentation but is not codified in deployment automation. |
| **Recommendation** | When deploying on EKS, implement Kubernetes rolling update strategy for Druid Deployments/StatefulSets with appropriate `maxUnavailable` and `maxSurge` settings. Follow Druid's documented rolling update order. Consider **Argo Rollouts** for canary deployments of the Broker service (stateless query router). Use **AWS CodeDeploy** or Helm hooks for deployment lifecycle management. |
| **Evidence** | `distribution/docker/docker-compose.yml`, `docs/operations/rolling-updates.md` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid has comprehensive integration testing. **Docker integration tests** (`docker-tests.yml`): builds a full Druid Docker image and runs integration tests against a live Druid cluster (60-minute timeout, failsafe reports). **Quidem SQL tests** (`quidem-ut/`): SQL query validation tests that verify Druid's SQL engine produces correct results. **Unit tests**: matrix testing across JDK 17 and JDK 21 with 9 test patterns. **Embedded tests** (`embedded-tests/`): includes TLS testing (`embedded-tests/tls/`). **JaCoCo coverage reporting** in CI. **Testcontainers** support (`extensions-core/druid-testcontainers/`). Gaps: integration tests are comprehensive for query correctness but may not cover all operational scenarios (failover, scaling, upgrade). |
| **Gap** | Integration tests cover query correctness and basic cluster functionality. No contract tests for API consumers. No chaos/resilience testing in CI. |
| **Recommendation** | Add API contract tests (using OpenAPI specs once generated) to catch breaking changes. Consider adding resilience tests that validate failover scenarios (Historical failure, Broker failure, metadata storage failover). The existing Testcontainers infrastructure provides a good foundation for expanded integration testing. |
| **Evidence** | `.github/workflows/docker-tests.yml`, `.github/workflows/ci.yml`, `quidem-ut/`, `embedded-tests/`, `extensions-core/druid-testcontainers/`, `.codecov.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated incident response exists. No runbooks (markdown, YAML, or JSON), no Systems Manager Automation documents, no Lambda-based remediation, no self-healing automation. The `docs/operations/` directory contains 31 operational guides covering configuration, security, performance tuning, and migration — but these are human-readable documentation, not machine-executable runbooks. No on-call integration or escalation paths are defined. |
| **Gap** | No automated incident response. No machine-readable runbooks. No self-healing patterns. All incident response is ad hoc. |
| **Recommendation** | Create **AWS Systems Manager** runbooks for common Druid operational scenarios: segment load failures, task failures, Historical node recovery, metadata storage failover, and ingestion lag spikes. Implement Lambda-based self-healing for automatable scenarios (e.g., auto-restart failed ingestion tasks, auto-scale Historicals on segment backlog). |
| **Evidence** | `docs/operations/` (31 files — operational documentation, not automated runbooks) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership structure exists. No CODEOWNERS file for observability assets. No per-service dashboards defined. No alarm ownership attribution. No team-specific SLO definitions. The `.codecov.yml` has coverage reporting but with project and patch status set to `off` — effectively disabling coverage enforcement. The emitter framework provides the data pipeline for observability, but no ownership or governance layer exists on top of it. |
| **Gap** | No observability ownership. No per-service dashboards. No alarm owners. Coverage enforcement disabled. |
| **Recommendation** | Define observability ownership: assign dashboard and alarm owners per Druid service type (Coordinator, Broker, Historical, MiddleManager). Create per-service dashboards in Amazon Managed Grafana. Define CODEOWNERS for observability configurations. Enable coverage enforcement in `.codecov.yml`. |
| **Evidence** | `.codecov.yml` (project: off, patch: off), repository (no CODEOWNERS file for observability) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tags are defined anywhere in the repository. No IaC exists, so there are no `default_tags`, `tags` blocks, `required-tags` Config rules, or Tag Policies. No tagging standard is documented. |
| **Gap** | No resource tagging governance. When infrastructure is provisioned, there will be no cost allocation, ownership attribution, or environment identification via tags. |
| **Recommendation** | When creating IaC, define a mandatory tagging schema (Environment, Service, Team, CostCenter) using `default_tags` in the Terraform AWS provider or CDK `Tags.of()`. Enforce via **AWS Config** required-tags rule and **AWS Organizations** Tag Policies. Activate cost allocation tags for FinOps reporting. |
| **Evidence** | Repository (no IaC, no tag definitions found) |

## Learning Materials

The following learning resources are mapped to the triggered pathways:

### Move to Managed Databases
- [Move to Managed Databases — AWS Skill Builder Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [Aurora PostgreSQL Migration Guide](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Migrating.html)

### Move to Modern DevOps
- [Move to Modern DevOps — AWS Skill Builder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [EKS Workshop](https://www.eksworkshop.com/)
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q1, INF-Q4, APP-Q1, APP-Q2, DATA-Q3, DATA-Q4 | Root Maven POM — Java 17, 75+ modules, AWS SDK v2.40.0, Kafka 3.9.1, ZooKeeper 3.8.6, Jackson 2.19.2, Jetty 12.0.30, Guice 6.0.0, database driver versions |
| `distribution/docker/Dockerfile` | INF-Q1, INF-Q2, SEC-Q6 | Multi-stage Docker build using distroless Java 17 base, non-root user (druid:1000) |
| `distribution/docker/docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, APP-Q2, DATA-Q3, SEC-Q2, SEC-Q5, OPS-Q5 | Local dev environment — postgres:17.6, zookeeper:3.5.10, 5 Druid services, plaintext credentials |
| `distribution/docker/environment` | INF-Q2, INF-Q4, SEC-Q3, SEC-Q5, APP-Q6 | Runtime configuration — JDBC connection string, extensions loadList, plaintext password |
| `docs/design/architecture.md` | INF-Q1, INF-Q9, APP-Q2 | Druid distributed architecture — service types, server roles, external dependencies |
| `docs/design/metadata-storage.md` | INF-Q2, INF-Q8, DATA-Q4, SEC-Q1 | Metadata storage design — segments, rules, config, tasks, audit tables |
| `docs/design/zookeeper.md` | APP-Q6 | ZooKeeper service discovery — announcements, leader election, segment publishing |
| `docs/design/deep-storage.md` | DATA-Q1 | Deep storage options — S3, HDFS, local, GCS, Azure |
| `docs/design/broker.md` | APP-Q3, DATA-Q2 | Broker service — query routing, result merging |
| `docs/design/overlord.md` | INF-Q3, APP-Q4 | Overlord service — ingestion task coordination |
| `docs/design/middlemanager.md` | INF-Q3, APP-Q4 | MiddleManager service — task execution |
| `docs/design/router.md` | INF-Q6 | Router service — internal API gateway, web console |
| `docs/design/indexer.md` | APP-Q4 | Indexer service — alternative task execution engine |
| `docs/api-reference/sql-api.md` | APP-Q3, APP-Q5, DATA-Q2 | SQL API — `/druid/v2/sql`, versioned URL path |
| `docs/api-reference/tasks-api.md` | INF-Q3, APP-Q4, APP-Q5 | Tasks API — `/druid/indexer/v1/tasks`, async task management |
| `docs/api-reference/json-querying-api.md` | APP-Q5 | Native query API — `/druid/v2/`, versioned URL path |
| `docs/operations/security-overview.md` | INF-Q5, INF-Q6, SEC-Q3 | Security best practices — auth, TLS, network isolation recommendations |
| `docs/operations/metrics.md` | OPS-Q1, OPS-Q2, OPS-Q3 | 658 lines of metrics documentation — query, ingestion, coordination, JVM metrics |
| `docs/operations/high-availability.md` | INF-Q9 | HA recommendations — ZK ensemble, multiple Coordinators, Brokers behind LB |
| `docs/operations/rolling-updates.md` | OPS-Q5 | Rolling update order documentation |
| `docs/operations/alerts.md` | OPS-Q4 | Application-level alerting system |
| `docs/operations/dynamic-config-provider.md` | SEC-Q5 | Dynamic config provider — env var based secret injection capability |
| `docs/operations/auth.md` | SEC-Q4 | Authentication configuration guide |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6 | Unit test CI — JDK 17/21 matrix, JaCoCo coverage |
| `.github/workflows/static-checks.yml` | INF-Q11, SEC-Q7 | Static analysis — Checkstyle, SpotBugs, PMD, forbidden-apis, OpenRewrite |
| `.github/workflows/codeql.yml` | INF-Q11, SEC-Q7 | CodeQL SAST — Java, JavaScript, Python with security-and-quality queries |
| `.github/workflows/docker-tests.yml` | INF-Q11, OPS-Q6 | Docker integration tests — full cluster build and test |
| `.github/workflows/cron-job-its.yml` | INF-Q11, SEC-Q6, SEC-Q7 | OWASP dependency vulnerability scanning (daily cron + on suppressions change) |
| `.github/workflows/unit-and-integration-tests-unified.yml` | INF-Q11, OPS-Q6 | Unified CI pipeline — unit tests then Docker tests |
| `.github/config/codeql-config.yml` | SEC-Q7 | CodeQL custom configuration |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot — Maven daily, npm disabled |
| `.codecov.yml` | OPS-Q8 | Codecov — project and patch status OFF |
| `owasp-dependency-check-suppressions.xml` | SEC-Q6, SEC-Q7 | 744 lines of vulnerability suppressions — active triage |
| `codestyle/checkstyle.xml` | SEC-Q6 | Checkstyle configuration |
| `codestyle/spotbugs-exclude.xml` | SEC-Q6 | SpotBugs exclusion rules |
| `codestyle/pmd-ruleset.xml` | SEC-Q6 | PMD rule set |
| `extensions-core/kafka-indexing-service/` | INF-Q4, APP-Q3 | Kafka ingestion — async message consumer |
| `extensions-core/kinesis-indexing-service/` | INF-Q4, APP-Q3 | Kinesis ingestion — async stream consumer |
| `extensions-core/kubernetes-extensions/` | INF-Q1, APP-Q6 | Kubernetes integration — K8s service discovery |
| `extensions-core/kubernetes-overlord-extensions/` | INF-Q1 | K8s-based task management |
| `extensions-core/s3-extensions/` | DATA-Q1 | S3 deep storage extension |
| `extensions-core/postgresql-metadata-storage/` | INF-Q2, DATA-Q4 | PostgreSQL metadata storage extension |
| `extensions-core/mysql-metadata-storage/` | DATA-Q4 | MySQL metadata storage extension |
| `extensions-core/druid-basic-security/` | SEC-Q3, SEC-Q4 | Basic HTTP authentication |
| `extensions-core/druid-kerberos/` | SEC-Q3, SEC-Q4 | Kerberos authentication |
| `extensions-core/druid-pac4j/` | SEC-Q3, SEC-Q4 | OIDC/SAML federation |
| `extensions-core/druid-testcontainers/` | OPS-Q6, DATA-Q3 | Testcontainers integration |
| `extensions-contrib/opentelemetry-emitter/` | OPS-Q1 | OpenTelemetry metrics emitter |
| `extensions-contrib/prometheus-emitter/` | OPS-Q1, OPS-Q3 | Prometheus metrics emitter |
| `extensions-contrib/statsd-emitter/` | OPS-Q1, OPS-Q3 | StatsD metrics emitter |
| `extensions-contrib/graphite-emitter/` | OPS-Q3 | Graphite metrics emitter |
| `extensions-contrib/kafka-emitter/` | INF-Q4 | Kafka metrics emitter |
| `extensions-contrib/rabbit-stream-indexing-service/` | INF-Q4 | RabbitMQ Stream ingestion |
| `extensions-contrib/consul-extensions/` | APP-Q6 | Consul service discovery |
| `extensions-contrib/sqlserver-metadata-storage/` | DATA-Q4 | SQL Server metadata (contrib, not default) |
| `web-console/package.json` | APP-Q1 | TypeScript 5.5, React 18.3, Node.js 20+ |
| `cloud/aws-common/pom.xml` | APP-Q1 | AWS SDK v2 integration module |
| `AGENTS.md` | APP-Q2 | Developer guide — key modules, code style, testing |
| `rewrite.yml` | INF-Q11 | OpenRewrite recipe — automated code modernization |
| `sql/` | DATA-Q2 | SQL planning module (Calcite-based) |
| `processing/` | DATA-Q2 | Core query processing engine |
| `indexing-service/` | INF-Q3 | Ingestion task framework |
| `quidem-ut/` | OPS-Q6 | SQL query validation tests |
| `embedded-tests/` | OPS-Q6 | Embedded integration tests including TLS |
| `docs/operations/` | OPS-Q7 | 31 operational guides (human-readable, not automated) |
