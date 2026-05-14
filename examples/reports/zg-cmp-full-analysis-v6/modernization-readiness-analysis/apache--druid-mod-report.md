# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | druid |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-readiness-analysis-v6 |
| **Repo Type** | monorepo |
| **Service Archetype** | data-gateway (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, analytics, database |
| **Context** | Apache Druid: high-performance real-time analytics database. |
| **Overall Score** | 2.48 / 4.0 |
| **Classification** | 🟠 Remediation Required |

**Classification Rationale:** This repo has 6 High findings, 8 Medium findings, 5 Low findings. Rule matched: "2-11 High → Remediation Required." Note: MOD classification differs from ARA — ARA's "1 High" is an agent-deployment gate; MOD's "1 High" is typically a single modernization gap and maps to Pilot-Ready instead of Remediation Required.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true

**Archetype Justification**: Druid is a distributed analytics database whose primary workload is serving read-heavy analytical queries (aggregations, scans, SQL) over pre-ingested data segments. The vast majority of API endpoints are query (GET/POST) operations returning aggregated results. While ingestion writes exist, the runtime role is predominantly a high-throughput data access layer. Classified as data-gateway.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 3.25 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.48 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: INF-Q1=3, INF-Q2=3, INF-Q3=Not Evaluated, INF-Q4=4, INF-Q5=1, INF-Q6=1, INF-Q7=1, INF-Q8=1, INF-Q9=1, INF-Q10=2, INF-Q11=3. Excluding INF-Q3: (3+3+4+1+1+1+1+1+2+3)/10 = 20/10 = 2.00
- APP: APP-Q1=4, APP-Q2=3, APP-Q3=Not Evaluated, APP-Q4=Not Evaluated, APP-Q5=3, APP-Q6=3. Excluding APP-Q3, APP-Q4: (4+3+3+3)/4 = 13/4 = 3.25
- DATA: DATA-Q1=2, DATA-Q2=3, DATA-Q3=3, DATA-Q4=4. (2+3+3+4)/4 = 12/4 = 3.00
- SEC: SEC-Q1=1, SEC-Q2=1, SEC-Q3=3, SEC-Q4=3, SEC-Q5=2, SEC-Q6=2, SEC-Q7=3. (1+1+3+3+2+2+3)/7 = 15/7 = 2.14
- OPS: OPS-Q1=3, OPS-Q2=1, OPS-Q3=3, OPS-Q4=2, OPS-Q5=2, OPS-Q6=3, OPS-Q7=1, OPS-Q8=2, OPS-Q9=1. (3+1+3+2+2+3+1+2+1)/9 = 18/9 = 2.00
- Overall: (2.00+3.25+3.00+2.14+2.00)/5 = 12.39/5 = 2.48

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q5: Network Security | 1 | No IaC defining VPC, subnets, or security groups — infrastructure deployment is external to this repo | Deployment security posture is ungoverned from this codebase; no network segmentation evidence |
| 2 | INF-Q8: Backup and Recovery | 1 | No backup configuration, retention policies, or disaster recovery definitions in the repository | Data loss risk if operators do not configure backups externally |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging infrastructure defined | Compliance and forensic investigation capabilities are unverifiable |
| 4 | OPS-Q2: SLO Definitions | 1 | No SLO definitions, error budgets, or formal service-level targets found | Cannot measure whether system meets user expectations; no prioritization framework for improvements |
| 5 | OPS-Q9: Resource Tagging | 1 | No resource tagging governance or tag policies defined | No cost allocation, ownership tracking, or environment identification possible |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists (262 markdown files in `/docs/`, 29 READMEs, comprehensive API reference). APP-Q5 = 3.
- **What it enables:** A RAG-based knowledge agent that indexes Druid's extensive documentation corpus to answer developer and operator questions about configuration, querying, ingestion, and operations.
- **Additional steps:** Generate OpenAPI specs from the existing REST API annotations (JAX-RS `@Path` in source code) to enable API tool discovery. Index all `/docs/` markdown and API reference content.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). 13 GitHub Actions workflows cover unit tests, integration tests, Docker builds, CodeQL, and static checks.
- **What it enables:** A DevOps agent that triggers test pipelines, monitors build status, reports coverage regressions, and manages PR automation workflows.
- **Additional steps:** Configure API access tokens for GitHub Actions programmatic triggering.
- **Effort:** Low

### Observability Agent

- **Prerequisite:** Structured metrics emission exists (OPS-Q1 = 3). Druid has OpenTelemetry, Prometheus, Dropwizard, Graphite, StatsD, and InfluxDB emitter extensions. JVM and service status monitors are configured.
- **What it enables:** An observability agent that queries Druid metrics, correlates emitter output with service health, and identifies performance regressions in query latency or ingestion throughput.
- **Additional steps:** Ensure a production deployment has at least one emitter configured (currently defaults to `noop`).
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (already modular); primary trigger not met |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3, Dockerfiles exist; compute already containerized |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures); Druid itself is open source |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3; metadata storage supports RDS PostgreSQL/MySQL |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (data-gateway archetype, sync reads are correct); Druid IS the analytics platform |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 2, OPS-Q5 = 2, OPS-Q6 = 3 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 2):** No infrastructure-as-code exists within this repository. Infrastructure deployment relies on external projects (druid-operator, druid-helm). The repo itself defines only application code and Docker artifacts, with no Terraform, CDK, or CloudFormation templates for the operational/DR layer (alarms, backup plans, health checks).
- **CI/CD Automation (INF-Q11 = 3):** Comprehensive CI pipeline exists with 13 GitHub Actions workflows covering unit tests (JDK 17/21), integration tests, Docker builds, CodeQL SAST, static analysis, and JaCoCo coverage. However, there is no automated deployment pipeline — no CD stages for staging/production deployment of Druid services.
- **Deployment Strategy (OPS-Q5 = 2):** Docker image builds exist but no canary, blue/green, or rolling deployment automation is defined within the repository. Deployment is manual or handled by external operator tooling.
- **Integration Testing (OPS-Q6 = 3):** Integration tests exist using Testcontainers and Docker-based testing (embedded-tests module), but not all critical workflows have automated integration coverage in CI.

**Recommendations:**
- Adopt EKS-based deployment with the existing druid-operator, defining IaC for the EKS cluster, node groups, and Druid custom resources using Terraform or CDK.
- Implement GitOps (ArgoCD or Flux) for automated Druid deployments with canary rollout support.
- Add deployment pipeline stages to existing GitHub Actions that push built Docker images and trigger ArgoCD sync.
- Define CloudWatch alarms, Route 53 health checks, and AWS Backup plans as IaC within the repository.

**Representative AWS Services:** CodeBuild, CodePipeline, EKS, ECR, CloudFormation/CDK, CloudWatch, X-Ray

**Learning Materials:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid provides a multi-stage Dockerfile (`distribution/docker/Dockerfile`) producing a distroless JDK17 image. Docker Compose defines a full cluster (Coordinator, Broker, Historical, MiddleManager, Router). The `kubernetes-overlord-extensions` module runs tasks as Kubernetes Jobs. The `kubernetes-extensions` module provides K8s-native service discovery. External deployment is managed via the druid-operator and druid-helm chart on EKS/K8s. |
| **Gap** | No IaC within this repository defines the managed container orchestration (EKS/ECS) — it is handled externally. The repo provides containerization artifacts but not the orchestration platform definition. |
| **Recommendation** | Consider co-locating EKS cluster IaC (Terraform/CDK) or at minimum referencing the druid-operator Helm chart as a Git submodule to establish full deployment traceability. Prefer EKS per stated preferences. |
| **Evidence** | `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`, `extensions-core/kubernetes-overlord-extensions/`, `extensions-core/kubernetes-extensions/` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid's metadata storage supports MySQL, PostgreSQL, and SQL Server via dedicated extensions (`extensions-core/mysql-metadata-storage/`, `extensions-core/postgresql-metadata-storage/`, `extensions-contrib/sqlserver-metadata-storage/`). The Docker Compose uses PostgreSQL 17.6 for metadata. Production deployments on AWS would use RDS/Aurora. The `druid-aws-rds-extensions` module provides IAM authentication for RDS. |
| **Gap** | No IaC defines managed database resources (RDS/Aurora). The repository provides database drivers and connectivity but the infrastructure is provisioned externally. The default dev configuration uses embedded Derby. |
| **Recommendation** | Define Aurora PostgreSQL (preferred per preferences) as IaC for the metadata store. Leverage the existing `druid-aws-rds-extensions` for IAM-based authentication instead of password-based connections. |
| **Evidence** | `extensions-core/mysql-metadata-storage/pom.xml`, `extensions-core/postgresql-metadata-storage/pom.xml`, `extensions-core/druid-aws-rds-extensions/`, `distribution/docker/docker-compose.yml` (postgres:17.6), `examples/conf/druid/auto/_common/common.runtime.properties` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `data-gateway`. No multi-step workflows exist in the read path. Druid's primary function is serving analytical queries over pre-ingested data segments. Ingestion coordination is handled by its own internal task framework (MiddleManager/Indexer) which is purpose-built for data ingestion, not a general workflow orchestration concern. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Druid natively integrates with managed streaming infrastructure as a consumer. The `kafka-indexing-service` and `kinesis-indexing-service` core extensions consume from Kafka/MSK and Kinesis Data Streams respectively. Synchronous reads dominate the query path (correct for data-gateway archetype). The Kafka emitter extension enables metrics streaming to Kafka. These are first-class integrations with AWS managed services (Kinesis, MSK). |
| **Gap** | None — synchronous reads are the correct design for the query path, and ingestion already uses managed streaming (Kafka/Kinesis). |
| **Recommendation** | Synchronous query serving is appropriate for this data-gateway archetype. Adopting additional async messaging is NOT recommended — it would add operational complexity without architectural benefit. Continue using MSK/Kinesis for ingestion. |
| **Evidence** | `extensions-core/kafka-indexing-service/pom.xml`, `extensions-core/kinesis-indexing-service/pom.xml`, `extensions-contrib/kafka-emitter/pom.xml`, `pom.xml` (kafka 3.9.1) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation configuration exists within this repository. Infrastructure deployment (including network topology) is handled entirely externally. The Docker Compose exposes all services on host ports without network isolation. |
| **Gap** | No network security configuration is codified. Deployments depend entirely on external operator/Helm configurations for network isolation. |
| **Recommendation** | Define VPC architecture as IaC: private subnets for Druid data nodes (Historical, MiddleManager), restricted subnets for coordination (Coordinator, Overlord), and public-facing Router/Broker behind an ALB or API Gateway. Implement security groups with least-privilege rules between service tiers. |
| **Evidence** | `distribution/docker/docker-compose.yml` (ports exposed directly), absence of any `.tf`, CloudFormation, or CDK files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Druid exposes HTTP APIs directly on each service (Router on port 8888, Broker on 8082, Coordinator on 8081). The Router service acts as an internal query routing layer but is not an API Gateway — it lacks throttling, authentication enforcement, request validation, and rate limiting at the entry point level. No ALB, API Gateway, or CloudFront is defined. |
| **Gap** | No managed API entry point with throttling, auth enforcement, or request validation. Services are exposed directly. |
| **Recommendation** | Place an Application Load Balancer or API Gateway (preferred per preferences) in front of the Router service. Configure throttling, request validation, and WAF integration. Use API Gateway for external query consumers with usage plans and API keys. |
| **Evidence** | `distribution/docker/docker-compose.yml` (ports 8081-8888 exposed), `server/src/main/java/org/apache/druid/server/http/` (direct JAX-RS endpoints) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists within this repository. The Docker Compose defines static container counts. No ASG, ECS auto-scaling, EKS HPA, or KEDA configuration is present. Auto-scaling would depend entirely on external operator/Helm configuration. |
| **Gap** | No auto-scaling definitions for any Druid service tier. Static capacity is the default. |
| **Recommendation** | Define Kubernetes HPA for Broker and Router services (scale on query latency/CPU). Define cluster autoscaler for Historical nodes (scale on segment storage pressure). Consider KEDA for MiddleManager scaling based on pending task queue depth. |
| **Evidence** | `distribution/docker/docker-compose.yml` (static service definitions), absence of HPA/ASG/scaling config |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration, retention policies, point-in-time recovery settings, or disaster recovery plans exist in this repository. The metadata store (PostgreSQL in Docker Compose) has no backup configuration. Deep storage (local filesystem in default config) has no replication or backup strategy defined. |
| **Gap** | No automated backup strategy for metadata store or deep storage. No restore procedures documented in the deployment context. |
| **Recommendation** | Define Aurora PostgreSQL with automated backups and PITR for the metadata store. Configure S3 deep storage with versioning and cross-region replication for segment data. Define AWS Backup plans covering both. Document and test restore procedures. |
| **Evidence** | `distribution/docker/docker-compose.yml` (postgres with no backup config), `examples/conf/druid/auto/_common/common.runtime.properties` (local storage default) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration exists within this repository. Docker Compose defines single instances of each service. The Druid architecture supports HA (multiple Historicals, replicated segments, multiple Brokers) but no IaC defines this topology across availability zones. |
| **Gap** | No multi-AZ configuration. Single-AZ failure would take down the entire cluster as defined in this repo. |
| **Recommendation** | Define EKS node groups spanning 2+ AZs. Configure Druid segment replication factor ≥ 2 across AZ-aware Historicals. Deploy Aurora metadata store in Multi-AZ mode. Place ZooKeeper ensemble (or migrate to K8s-native discovery) across 3 AZs. |
| **Evidence** | `distribution/docker/docker-compose.yml` (single instances), absence of multi-AZ configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The repository contains Docker/container definitions (Dockerfile, docker-compose.yml) and Kubernetes test manifests but no production IaC. No Terraform, CDK, CloudFormation, or Helm charts for production deployment exist within this repo. The external druid-operator and druid-helm projects provide some Kubernetes IaC but are not co-located. |
| **Gap** | Significant infrastructure is not codified within this repository. Compute, networking, databases, messaging, and operational resources (monitoring, alarms, backups) have no IaC representation here. |
| **Recommendation** | Create a `deploy/` or `infrastructure/` directory with Terraform/CDK modules defining: EKS cluster, Aurora PostgreSQL, S3 deep storage, CloudWatch alarms, and AWS Backup plans. Alternatively, reference the external druid-helm chart and add overlay values for production topology. |
| **Evidence** | `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`, `embedded-tests/src/test/resources/manifests/` (test-only K8s manifests), absence of `.tf`/CDK/CloudFormation files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI automation exists: 13 GitHub Actions workflows covering unit tests (JDK 17/21, parallelized by test pattern), integration tests (Docker-based), CodeQL SAST, static analysis (Maven checks, strict compilation, OpenRewrite), JaCoCo coverage reporting, PR validation, and Docker image build/test. However, no CD (deployment) automation exists — no pipeline stage deploys to staging or production environments. |
| **Gap** | No deployment automation (CD). The pipeline builds and tests but does not deploy. IaC changes are not part of the pipeline either. |
| **Recommendation** | Add deployment stages: push Docker images to ECR, trigger ArgoCD sync for EKS deployment, include smoke tests post-deployment. Add IaC validation (terraform plan / cdk diff) as a PR check when infrastructure code is added. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/unit-and-integration-tests-unified.yml`, `.github/workflows/docker-tests.yml`, `.github/workflows/codeql.yml`, `.github/workflows/static-checks.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 17 with modern dependencies: Jetty 12, Jackson 2.19, Guice 6.0, Calcite 1.37, AWS SDK v2 2.40.0, Kubernetes Client 25.0. TypeScript (web console) with React and modern tooling. The codebase uses current Java 17 LTS with `maven.compiler.release=17`. AWS SDK v2 is the primary AWS integration path. CI tests on both JDK 17 and 21. |
| **Gap** | None — Java 17 is a current LTS, AWS SDK v2 is modern, and the framework stack is up-to-date. Legacy Jersey 1.x (1.19.4) is the only dated component but does not block cloud-native development. |
| **Recommendation** | Plan migration from Jersey 1.x to a modern JAX-RS implementation when feasible. Consider JDK 21 as the baseline once ecosystem stabilizes further. |
| **Evidence** | `pom.xml` (java.version=17, aws.sdk.v2.version=2.40.0, jetty.version=12.0.30), `.github/workflows/ci.yml` (JDK 17, 21 matrix), `web-console/package.json` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid is a modular distributed system with 74 Maven modules. Each runtime service (Coordinator, Broker, Historical, MiddleManager, Router) is independently deployable from a single codebase. The architecture has well-defined module boundaries: `processing/` (core engine), `server/` (common infrastructure), `sql/` (SQL layer), `indexing-service/` (task framework), `multi-stage-query/` (MSQ engine), and 64 extension modules. Services communicate via HTTP and ZooKeeper. |
| **Gap** | While services are independently deployable, they share a single Maven build and a monolithic Docker image. The codebase is a modular monorepo rather than independent microservice repositories. Shared database schemas exist (metadata store). |
| **Recommendation** | The current modular monorepo structure is appropriate for Druid's architecture. Consider extracting the web-console into a fully independent build/deploy pipeline. No forced decomposition recommended — the distributed service architecture with shared codebase is a valid pattern for this domain. |
| **Evidence** | `pom.xml` (74 modules), `distribution/docker/docker-compose.yml` (5 independent services), `extensions-core/kubernetes-overlord-extensions/` (K8s task runner), `services/` (service entry points) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `data-gateway`. Synchronous reads dominate the query path (correct design). Query requests arrive via HTTP, are routed to Brokers, which fan out to Historicals, aggregate results, and return synchronously. This is the correct communication pattern for a read-heavy analytics query engine. Ingestion uses Kafka/Kinesis consumers (async input) but the primary query serving is synchronous by design. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `data-gateway`. Most user-facing query operations complete within seconds (sub-second for typical aggregations). The MSQ (multi-stage query) engine handles longer-running batch queries asynchronously with task status polling via `/druid/indexer/v1/task/{taskId}/status` — this is already correctly implemented as an async job with status API. No user-facing query path blocks for >30 seconds by design. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid uses URL-path versioning consistently: `/druid/v2/` for query APIs, `/druid/coordinator/v1/` for coordination APIs, `/druid/indexer/v1/` for indexing APIs. This pattern is applied across all service endpoints. Deprecated APIs include `@Deprecated` annotations and migration notes (e.g., `CoordinatorCompactionConfigsResource`). |
| **Gap** | No formal backward compatibility guarantee mechanism or API changelog. Some newer endpoints don't strictly follow the versioning convention. No OpenAPI specification generated from the JAX-RS annotations for formal contract documentation. |
| **Recommendation** | Generate OpenAPI specifications from JAX-RS annotations using a Maven plugin (e.g., `swagger-maven-plugin`). Establish a formal API deprecation policy with version sunset timelines. |
| **Evidence** | `server/src/main/java/org/apache/druid/server/ClientInfoResource.java` (`@Path("/druid/v2/datasources")`), `server/src/main/java/org/apache/druid/server/http/CoordinatorResource.java` (`@Path("/druid/coordinator/v1")`), `docs/api-reference/` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid uses ZooKeeper for service discovery (node announcement, leader election, segment coordination). The `kubernetes-extensions` module provides K8s-native discovery as an alternative (`K8sDruidNodeDiscoveryProvider`, `K8sDruidNodeAnnouncer`, `K8sDruidLeaderSelector`). No hard-coded service endpoints — all discovery is dynamic via ZK or K8s API. |
| **Gap** | ZooKeeper is a legacy coordination service with significant operational overhead. The K8s-native discovery extension exists but is not the default. |
| **Recommendation** | For EKS deployments (preferred), migrate to the `kubernetes-extensions` module for service discovery, eliminating ZooKeeper dependency. This reduces operational complexity and aligns with cloud-native EKS patterns. |
| **Evidence** | `examples/conf/druid/auto/_common/common.runtime.properties` (druid.zk.service.host), `extensions-core/kubernetes-extensions/src/main/java/org/apache/druid/k8s/discovery/` |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Druid's deep storage supports S3 (`extensions-core/s3-extensions/`), HDFS (`extensions-core/hdfs-storage/`), Azure Blob, and GCS. However, the default configuration uses local filesystem (`druid.storage.type=local`). S3 is available as an extension but not the default. No parsing pipeline (Textract, Tika) for unstructured documents exists — Druid stores structured/semi-structured columnar data, not raw documents. |
| **Gap** | Default deep storage is local filesystem. S3 integration exists but requires explicit configuration. No document parsing capabilities. |
| **Recommendation** | Configure S3 as the default deep storage for all production deployments. For environments processing unstructured data alongside Druid analytics, consider adding S3-based document parsing pipelines for data that feeds into Druid ingestion. |
| **Evidence** | `extensions-core/s3-extensions/pom.xml`, `examples/conf/druid/auto/_common/common.runtime.properties` (druid.storage.type=local), `extensions-core/hdfs-storage/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid has a centralized data access architecture: all queries go through the SQL layer (`sql/` module) which translates to native Druid queries, or directly via the native JSON query API. The `processing/` module provides a unified query processing engine. Metadata access is centralized through the metadata storage connector abstraction. Extensions use well-defined SPIs for data access. |
| **Gap** | Some internal modules directly access metadata tables rather than going through the service API layer (e.g., coordinator duties reading metadata directly). The SQL layer and native query API are separate access paths rather than a single unified gateway. |
| **Recommendation** | Continue consolidating data access through the SQL layer as the primary interface. The existing architecture is sound for an analytics database — two query interfaces (SQL and native) are intentional design choices, not gaps. |
| **Evidence** | `sql/` module, `processing/` module, `server/src/main/java/org/apache/druid/server/` (query resources), metadata storage extension abstraction |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database driver versions are explicitly pinned in the root POM: MySQL 8.2.0, PostgreSQL 42.7.2. Docker Compose uses PostgreSQL 17.6 (current). ZooKeeper 3.8.6 is pinned. None of these are at or past EOL. However, Derby (default metadata store for development) is an embedded database with limited production viability. |
| **Gap** | No documented version-update procedure with downtime windows, rollback plans, and risk acknowledgment. Derby for dev is fine but could lead to confusion if used in production-like environments. |
| **Recommendation** | Document a database engine version update procedure. Add version validation to CI that flags when pinned versions approach EOL (within 12 months). Ensure production deployments never use Derby. |
| **Evidence** | `pom.xml` (mysql.version=8.2.0, postgresql.version=42.7.2), `distribution/docker/docker-compose.yml` (postgres:17.6), `pom.xml` (zookeeper.version=3.8.6) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. All business logic resides in the Java application layer. The metadata store schema is simple (task metadata, segments, rules) with no procedural database code. SQL files in the repository (249 files) are exclusively test queries for the SQL layer and MSQ engine — not database-side procedures. The Druid SQL layer implements its own SQL dialect on top of Calcite, independent of any database engine. |
| **Gap** | None. |
| **Recommendation** | No action needed. The application-layer-only approach is the ideal state for database portability and modernization. |
| **Evidence** | `sql/src/test/resources/` (test queries only), absence of CREATE PROCEDURE/TRIGGER/FUNCTION in any SQL file, `extensions-core/mysql-metadata-storage/`, `extensions-core/postgresql-metadata-storage/` (simple JDBC access) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail, audit trail, or immutable logging infrastructure is defined within this repository. Druid has application-level request logging (Log4j2 with 22 configuration files) and metrics emission, but no audit-grade logging with immutability guarantees, log file validation, or S3 Object Lock configuration. |
| **Gap** | No audit logging infrastructure. Application logs exist but are not immutable or compliance-grade. |
| **Recommendation** | Define CloudTrail for API-level audit logging of the AWS infrastructure. For Druid-specific audit, configure the request logger (`druid.request.logging.type=composing`) with log shipping to S3 with Object Lock enabled. Integrate CloudWatch Logs with retention policies. |
| **Evidence** | `examples/conf/druid/auto/_common/common.runtime.properties`, Log4j2 configs in `examples/conf/`, absence of CloudTrail/audit resources |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration exists within this repository. The default deep storage (local filesystem) and metadata store (Derby/PostgreSQL in Docker) have no KMS encryption configured. S3 extension code supports server-side encryption but no default configuration enforces it. No KMS key definitions or encryption policies are present. |
| **Gap** | No encryption at rest for deep storage (segments) or metadata store. No KMS key management. |
| **Recommendation** | Configure S3 deep storage with SSE-KMS using customer-managed keys. Define Aurora PostgreSQL with KMS encryption enabled. Add KMS key resources to IaC with documented rotation policies. Configure EBS encryption for any attached volumes. |
| **Evidence** | `examples/conf/druid/auto/_common/common.runtime.properties` (local storage, no encryption config), absence of KMS/encryption configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid provides comprehensive authentication extensions: `druid-basic-security` (username/password with LDAP), `druid-kerberos` (Kerberos/SPNEGO), and `druid-pac4j` (OAuth2/OIDC/SAML). The security framework supports per-request authentication with configurable authenticators and authorizers. However, authentication is disabled by default — the default configuration has no auth enabled. |
| **Gap** | Authentication is not enabled by default. Requires explicit extension loading and configuration for production. No API Gateway-level auth enforcement. |
| **Recommendation** | Enable `druid-basic-security` or `druid-pac4j` (OAuth2/OIDC) by default in production configurations. Consider placing API Gateway with Cognito authorizer in front for external access, with internal service-to-service auth via mTLS or IAM roles. |
| **Evidence** | `extensions-core/druid-basic-security/`, `extensions-core/druid-kerberos/`, `extensions-core/druid-pac4j/`, `examples/conf/druid/auto/_common/common.runtime.properties` (no auth config) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `druid-pac4j` extension provides OAuth2/OIDC/SAML integration enabling SSO with centralized identity providers (Cognito, Okta, Ping). The `druid-basic-security` extension supports LDAP federation. However, these integrations are optional extensions not enabled by default. |
| **Gap** | IdP integration is available but optional. Default deployment has standalone auth (or no auth). |
| **Recommendation** | Configure Cognito User Pool or corporate IdP integration via the pac4j extension for production deployments. Define this in deployment configuration/IaC as a required security baseline. |
| **Evidence** | `extensions-core/druid-pac4j/`, `extensions-core/druid-basic-security/` (LDAP support) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Docker Compose environment file contains a plaintext password (`druid_metadata_storage_connector_password=FoolishPassword`) and the docker-compose.yml contains `POSTGRES_PASSWORD=FoolishPassword`. These are clearly development/example values (not production credentials). The configuration files show commented-out credential placeholders (`druid.metadata.storage.connector.user=...`, `druid.metadata.storage.connector.password=...`). No Secrets Manager or Vault integration is present. The `druid-aws-rds-extensions` module provides IAM-based authentication (token-based, no static password), which is a secrets-management-adjacent capability. |
| **Gap** | Development example files contain plaintext passwords. No Secrets Manager integration for production credential management. No rotation mechanism. |
| **Recommendation** | Integrate AWS Secrets Manager for metadata store credentials. Leverage the existing `druid-aws-rds-extensions` for IAM authentication to Aurora PostgreSQL (eliminates static passwords entirely). Remove plaintext passwords from committed files or clearly mark them as non-production examples. |
| **Evidence** | `distribution/docker/environment` (druid_metadata_storage_connector_password=FoolishPassword), `distribution/docker/docker-compose.yml` (POSTGRES_PASSWORD=FoolishPassword), `extensions-core/druid-aws-rds-extensions/` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The production Docker image uses `gcr.io/distroless/java17-debian12` — a hardened, minimal base image with no shell, no package manager, and minimal attack surface. This is a good security practice. The OWASP dependency check suppressions file (`owasp-dependency-check-suppressions.xml`) indicates awareness of vulnerability scanning. However, no SSM Patch Manager, AWS Inspector, or automated vulnerability scanning pipeline is configured within the repository. |
| **Gap** | Good base image choice (distroless) but no automated vulnerability scanning in CI/CD pipeline. OWASP suppressions exist but it's unclear if dependency-check runs regularly. No ECR image scanning configuration. |
| **Recommendation** | Enable ECR image scanning for the Docker image. Add OWASP dependency-check or Snyk as a CI pipeline step (not just suppression file maintenance). Consider AWS Inspector for runtime vulnerability analysis of deployed containers. |
| **Evidence** | `distribution/docker/Dockerfile` (distroless/java17-debian12), `owasp-dependency-check-suppressions.xml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CodeQL SAST runs in CI (`.github/workflows/codeql.yml`) scanning Java, JavaScript, and Python. It runs on push, PR, and weekly schedule. Static checks workflow includes Maven static analysis and strict compilation. OWASP dependency-check suppressions indicate some dependency scanning awareness. However, no container scanning step exists in the Docker test workflow, and no blocking security gate prevents merging PRs with critical findings. |
| **Gap** | No explicit container scanning. No blocking security gate on critical CodeQL findings (it reports but doesn't block). No dependency vulnerability scanning step visible in CI (OWASP suppressions exist but no evidence of regular scan execution in pipeline). |
| **Recommendation** | Add container scanning (ECR scanning or Trivy) to the Docker build workflow. Configure CodeQL to block PRs on critical/high severity findings. Add explicit `mvn dependency-check:check` or Snyk step to the CI pipeline with a fail threshold. |
| **Evidence** | `.github/workflows/codeql.yml`, `.github/workflows/static-checks.yml`, `owasp-dependency-check-suppressions.xml` |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `opentelemetry-emitter` extension provides OpenTelemetry span emission for Druid queries (OpenTelemetry SDK 1.7.0, instrumentation 1.14.0-alpha). Druid also has internal request ID propagation across services (query IDs flow from Router → Broker → Historical). The Prometheus, Graphite, StatsD, and InfluxDB emitter extensions provide metrics instrumentation. |
| **Gap** | OpenTelemetry support exists but uses an older SDK version (1.7.0, current is 1.x series >1.30). It's a contrib extension (not core), meaning it's optional and may not have full trace propagation across all internal service boundaries. The emitter defaults to `noop`. |
| **Recommendation** | Upgrade the OpenTelemetry emitter to current SDK version. Promote it to a core extension or enable by default in production configurations. Ensure W3C Trace Context propagation across all internal Druid service-to-service calls (Broker→Historical, Coordinator→Historical). Integrate with AWS X-Ray via OTLP exporter. |
| **Evidence** | `extensions-contrib/opentelemetry-emitter/pom.xml` (OpenTelemetry 1.7.0), `extensions-contrib/prometheus-emitter/`, `examples/conf/druid/auto/_common/common.runtime.properties` (druid.emitter=noop) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions, error budgets, or formal service-level targets found anywhere in the repository. No CloudWatch alarm definitions for p99/p95 latency. No SLO monitoring dashboards or error budget tracking. The metrics framework exists (JVM monitors, service status monitors) but no SLOs are defined on top of them. |
| **Gap** | No SLOs defined for query latency, ingestion throughput, availability, or any critical user journey. No error budget framework. |
| **Recommendation** | Define SLOs for: query p99 latency (<500ms for typical aggregations), ingestion lag (<30s for real-time streams), metadata store availability (99.9%), and segment availability (99.99%). Implement as CloudWatch composite alarms with error budget dashboards. |
| **Evidence** | Absence of SLO definitions in any configuration, documentation, or code |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Druid publishes custom operational/business metrics via its emitter framework: `JvmMonitor`, `ServiceStatusMonitor`, query/time, query/bytes, segment/count, task/success, task/failed, ingest/events, and many more. These go beyond infrastructure metrics to measure query performance, ingestion throughput, and data management outcomes. Prometheus, Graphite, StatsD, and OpenTelemetry emitters are available for export. |
| **Gap** | While extensive metrics exist, the default emitter is `noop` — metrics are not published unless explicitly configured. No pre-built dashboards or CloudWatch metric definitions ship with the project. |
| **Recommendation** | Create CloudWatch dashboard templates defining key business metrics: queries/sec, query latency percentiles, ingestion events/sec, segment count growth, task success rate. Include these as IaC (CloudWatch dashboard JSON). Enable Prometheus or CloudWatch emitter by default. |
| **Evidence** | `examples/conf/druid/auto/_common/common.runtime.properties` (druid.monitoring.monitors, druid.emitter=noop), `server/src/main/java/org/apache/druid/server/metrics/` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The metrics infrastructure supports alerting (emitters can publish to monitoring systems that support alerting). However, no alert definitions, CloudWatch alarms, anomaly detection configurations, or PagerDuty/OpsGenie integrations exist within this repository. The monitoring monitors provide the signals but no alert rules consume them. |
| **Gap** | No alerting or anomaly detection defined. Metrics are available but no rules consume them for proactive alerting. |
| **Recommendation** | Define CloudWatch alarms for: query error rate > threshold, query p99 > SLO, ingestion lag > threshold, segment unavailable count > 0, ZooKeeper connection loss. Enable CloudWatch anomaly detection on query latency and ingestion throughput for drift detection. |
| **Evidence** | `server/src/main/java/org/apache/druid/server/metrics/` (metrics available), absence of alarm/alert definitions |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker image builds exist with basic health check support (Druid services expose health endpoints). The Docker Compose defines static service deployment. No canary, blue/green, or rolling deployment strategy is configured. The druid-operator (external) may support rolling updates, but no deployment strategy is codified within this repository. |
| **Gap** | No deployment strategy beyond basic Docker image builds. No canary or blue/green deployments. No traffic shifting or automated rollback. |
| **Recommendation** | Implement rolling deployments with health checks via the druid-operator on EKS. For critical deployments (Broker/Router), implement canary traffic shifting using Kubernetes service mesh or ALB weighted target groups. Define rollback triggers based on query error rate spikes. |
| **Evidence** | `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`, `.github/workflows/docker-tests.yml` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration testing exists: the `embedded-tests` module runs full Druid cluster tests using Testcontainers and Docker. The Docker tests workflow builds the production image and runs integration tests against it. Cron-scheduled integration tests (`cron-job-its.yml`) run on a regular cadence. The quidem framework tests SQL query correctness end-to-end. |
| **Gap** | Integration tests cover query correctness and cluster functionality but may not cover all critical operational workflows (failover, scaling, upgrade scenarios). Some gaps in coverage for extension-specific integration paths. |
| **Recommendation** | Add integration tests for: metadata store failover, segment replication recovery, ZooKeeper/K8s discovery failover, and rolling upgrade scenarios. These operational integration tests ensure production resilience. |
| **Evidence** | `embedded-tests/pom.xml`, `.github/workflows/docker-tests.yml`, `.github/workflows/cron-job-its.yml`, `quidem-ut/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks (markdown, YAML, or machine-readable), no Systems Manager Automation documents, no Lambda-based remediation, and no self-healing patterns exist within this repository. The `/docs/operations/` directory contains operational documentation but these are human-readable guides, not automated runbooks. |
| **Gap** | No automated incident response. No runbooks in any form. Incident response is entirely ad hoc. |
| **Recommendation** | Create runbooks for common incidents: segment unavailability (auto-trigger replication), ingestion lag (auto-scale MiddleManagers), metadata store connection failure (auto-failover to standby), ZooKeeper connection loss (auto-reconnect with backoff). Implement as SSM Automation documents or Step Functions with CloudWatch alarm triggers. |
| **Evidence** | `docs/operations/` (human-readable docs only), absence of runbook/automation files |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Metrics monitors exist per service type (JvmMonitor, ServiceStatusMonitor, HistoricalMetricsMonitor, TaskCountStatsMonitor) indicating service-level metric ownership. However, no CODEOWNERS for observability assets, no named alarm owners, no team-specific dashboards, and no SLO definitions with team attribution exist. |
| **Gap** | Observability infrastructure exists but has no ownership model. No team attribution on metrics, alarms, or dashboards. |
| **Recommendation** | Define CODEOWNERS for observability configurations. Create per-service-tier dashboards (Coordinator ops, Broker query perf, Historical segment serving, Indexer ingestion health) with named team ownership. Tag CloudWatch resources with owning team. |
| **Evidence** | `server/src/main/java/org/apache/druid/server/metrics/` (per-service monitors), absence of CODEOWNERS for observability |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging configuration, tag policies, or tagging standards exist within this repository. No `default_tags` in any IaC (because no IaC exists). No tagging conventions documented. Docker images have a maintainer label but no cost allocation, environment, or ownership tags on AWS resources. |
| **Gap** | No resource tagging governance whatsoever. No cost allocation, ownership tracking, or environment identification possible. |
| **Recommendation** | Define a tagging standard (environment, service-tier, team, cost-center) and enforce via IaC `default_tags` when infrastructure code is added. Implement AWS Tag Policies via Organizations. Tag all resources with: `Environment`, `Service`, `Team`, `CostCenter`, `Project=druid`. |
| **Evidence** | Absence of tagging configuration in any file, absence of IaC |

---

## Learning Materials

### Move to Modern DevOps (Triggered)
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q1, INF-Q4, APP-Q1, DATA-Q3 | Root POM defining Java 17, all dependency versions, 74 modules |
| `distribution/docker/Dockerfile` | INF-Q1, SEC-Q6, OPS-Q5 | Multi-stage Docker build producing distroless JDK17 image |
| `distribution/docker/docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, SEC-Q5 | Full Druid cluster definition with PostgreSQL 17.6 |
| `distribution/docker/environment` | SEC-Q5 | Docker environment file with plaintext metadata password |
| `examples/conf/druid/auto/_common/common.runtime.properties` | INF-Q2, INF-Q4, INF-Q8, DATA-Q1, SEC-Q1, OPS-Q1, OPS-Q3 | Default runtime configuration with noop emitter, local storage |
| `.github/workflows/ci.yml` | INF-Q11, APP-Q1 | Main CI workflow with JDK 17/21 matrix, parallelized tests |
| `.github/workflows/codeql.yml` | SEC-Q7 | CodeQL SAST scanning Java, JavaScript, Python |
| `.github/workflows/static-checks.yml` | INF-Q11 | Static analysis including Maven checks, strict compilation |
| `.github/workflows/docker-tests.yml` | INF-Q11, OPS-Q5, OPS-Q6 | Docker image build and integration test workflow |
| `.github/workflows/unit-and-integration-tests-unified.yml` | INF-Q11 | Unified test workflow triggering CI and Docker tests |
| `.github/workflows/cron-job-its.yml` | OPS-Q6 | Scheduled integration test runs |
| `extensions-core/kafka-indexing-service/pom.xml` | INF-Q4 | Kafka consumer for real-time ingestion |
| `extensions-core/kinesis-indexing-service/pom.xml` | INF-Q4 | Kinesis consumer for real-time ingestion |
| `extensions-core/s3-extensions/pom.xml` | DATA-Q1 | S3 deep storage support |
| `extensions-core/mysql-metadata-storage/pom.xml` | INF-Q2, DATA-Q4 | MySQL metadata store connector |
| `extensions-core/postgresql-metadata-storage/pom.xml` | INF-Q2, DATA-Q4 | PostgreSQL metadata store connector |
| `extensions-core/druid-aws-rds-extensions/` | INF-Q2, SEC-Q5 | IAM authentication for RDS |
| `extensions-core/druid-basic-security/` | SEC-Q3, SEC-Q4 | Basic auth with LDAP support |
| `extensions-core/druid-pac4j/` | SEC-Q3, SEC-Q4 | OAuth2/OIDC/SAML integration |
| `extensions-core/kubernetes-extensions/` | INF-Q1, APP-Q6 | K8s-native service discovery |
| `extensions-core/kubernetes-overlord-extensions/` | INF-Q1 | K8s Job-based task execution |
| `extensions-contrib/opentelemetry-emitter/pom.xml` | OPS-Q1 | OpenTelemetry span emission |
| `owasp-dependency-check-suppressions.xml` | SEC-Q6, SEC-Q7 | Vulnerability suppression file |
| `server/src/main/java/org/apache/druid/server/metrics/` | OPS-Q3, OPS-Q4, OPS-Q8 | Per-service metric monitors |
| `server/src/main/java/org/apache/druid/server/http/` | INF-Q6, APP-Q5 | JAX-RS API endpoints with versioned paths |
| `embedded-tests/pom.xml` | OPS-Q6 | Integration test module |
| `web-console/package.json` | APP-Q1 | React/TypeScript web console |
| `docs/` | Quick Agent Wins | 262 markdown documentation files |
| `sql/` | APP-Q2, DATA-Q2 | SQL planning layer (Calcite) |
| `processing/` | APP-Q2, DATA-Q2 | Core query processing engine |
