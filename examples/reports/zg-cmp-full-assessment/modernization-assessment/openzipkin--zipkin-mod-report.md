# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | zipkin |
| **Date** | 2025-07-16 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, observability, tracing |
| **Context** | Distributed tracing system. |
| **Overall Score** | 2.16 / 4.0 |

**Archetype Justification**: Zipkin server receives trace data via both synchronous (HTTP/gRPC) and asynchronous (Kafka/RabbitMQ/ActiveMQ/Pulsar) collectors, writes to persistent storage (Cassandra/Elasticsearch/MySQL), and serves query results via REST API. Mixed I/O with persistent state ownership classifies as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 3.17 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.78 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.16 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No IaC for managed compute — deployment is via self-hosted Docker containers with no ECS/EKS/Lambda definitions | Blocks cloud-native scaling, auto-patching, and operational maturity; all compute management is manual |
| 2 | INF-Q10: IaC Coverage | 1 | Zero IaC files — all infrastructure is provisioned manually or via Docker Compose examples intended for development only | Prevents reproducible deployments, disaster recovery, and environment consistency; foundational blocker for all modernization |
| 3 | SEC-Q3: API Authentication | 1 | No API authentication on any endpoint — CORS allowed-origins set to `*`, all endpoints are open by default | Critical security vulnerability; any network-accessible deployment exposes trace data without access control |
| 4 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group definitions — no network infrastructure defined | Services would be deployed without network isolation; blast radius of incidents is unlimited |
| 5 | OPS-Q2: SLO Definitions | 1 | No SLO definitions for any user journey — no error budgets, no latency targets | Cannot measure whether the tracing system meets reliability expectations; no data-driven prioritization of improvements |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 3 (API versioning exists with `/api/v2/` pattern across all query endpoints in `ZipkinQueryApiV2.java`). Structured JSON responses confirmed in trace and service query endpoints.
- **What it enables:** An agent that discovers and invokes Zipkin's existing REST API endpoints as tools — querying traces by ID, searching services, retrieving dependencies, and autocomplete values programmatically.
- **Additional steps:** No OpenAPI spec exists. Generate an OpenAPI specification from the Armeria annotated endpoints (`@Get` annotations in `ZipkinQueryApiV2.java`) for full tool discovery. The Zipkin API is well-documented in the README.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (unified data access layer via `StorageComponent` interface). The `StorageComponent` → `SpanStore` → `Traces` abstraction provides a clean, database-agnostic query interface.
- **What it enables:** A natural language to trace query agent — users can ask "show me slow traces for the payment service in the last hour" and the agent translates to Zipkin query API calls.
- **Additional steps:** The query API supports filtering by service name, span name, tags, duration, and time range. Agent needs mapping from natural language to `QueryRequest` parameters.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists with GitHub Actions — `test.yml`, `deploy.yml`, `docker_push.yml`, `create_release.yml`).
- **What it enables:** An agent that triggers test runs, checks build status, manages Docker image pushes, and initiates releases via GitHub Actions API.
- **Additional steps:** The deployment pipeline uses GitHub Actions with tag-based triggers (`release-*`, `docker-*`). Agent needs GitHub API access and understanding of the tag-based workflow.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists in the repository — `README.md`, `zipkin-server/README.md`, `docker/README.md`, `RATIONALE.md` files in `docker/`, `zipkin/`, `zipkin-server/`, `zipkin-storage/cassandra/`, and `zipkin-collector/activemq/`. Additionally, `SECURITY.md` and `RELEASE.md` provide operational context.
- **What it enables:** A RAG-based knowledge agent that indexes Zipkin documentation and answers developer questions about configuration, storage backend selection, collector setup, and operational best practices.
- **Additional steps:** Index the markdown files and source code comments. The `zipkin-server-shared.yml` configuration file with its extensive comments is particularly valuable as a knowledge source.
- **Effort:** Low

### Observability Agent

- **Prerequisite:** OPS-Q1 = 4 (Zipkin is itself a distributed tracing system with self-tracing via Brave/`ZipkinSelfTracingConfiguration` and Prometheus metrics via `ZipkinPrometheusMetricsConfiguration` and `MicrometerCollectorMetrics`).
- **What it enables:** An agent that queries Zipkin's own Prometheus metrics endpoint (`/prometheus`), traces self-tracing data, correlates collector throughput with storage performance, and suggests root causes for ingestion issues.
- **Additional steps:** Prometheus scrape configuration exists in `docker/examples/prometheus/prometheus.yml`. Agent needs access to the Prometheus endpoint and understanding of collector metric names (`zipkin_collector.messages`, `zipkin_collector.spans`, `zipkin_collector.spans_dropped`).
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with well-defined interfaces). Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1, but Dockerfile exists with multi-stage build and Docker Compose examples. Contextual guard prevents trigger — containerization is already in place. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures or proprietary SQL). All database engines used are open source (Cassandra, Elasticsearch/OpenSearch, MySQL/MariaDB). No commercial DB engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed via Docker Compose). DATA-Q3 = 2 (no version pinning in IaC). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 2, but Zipkin is a trace ingestion/query system, not a data analytics workload. No ETL, data pipeline, or analytics processing artifacts found. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (zero IaC). OPS-Q5 = 1 (no canary/blue-green). OPS-Q6 = 4 but INF-Q10 is the critical blocker. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "Distributed tracing system." contains no AI-related signal terms. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
Zipkin supports three storage backends, all self-managed via Docker Compose examples:
- **Apache Cassandra** — configured via `docker-compose-cassandra.yml` using `ghcr.io/openzipkin/zipkin-cassandra` image. Schema in `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql`. Connection via environment variables (`CASSANDRA_CONTACT_POINTS`, `CASSANDRA_USERNAME`, `CASSANDRA_PASSWORD`).
- **Elasticsearch/OpenSearch** — configured via `docker-compose-elasticsearch.yml` using `ghcr.io/openzipkin/zipkin-elasticsearch9` image. Connection via `ES_HOSTS`, `ES_USERNAME`, `ES_PASSWORD`. Supports both Elasticsearch 7-8.x and OpenSearch 2.x.
- **MySQL/MariaDB** — configured via `docker-compose-mysql.yml` using `ghcr.io/openzipkin/zipkin-mysql` image. Schema in `zipkin-storage/mysql-v1/src/main/resources/mysql.sql`. Described as legacy v1 storage with known performance issues. Connection via `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASS`.

**Engine Versions and EOL Status (DATA-Q3):**
No explicit version pinning in IaC (no IaC exists). Application code documents minimum supported versions: Cassandra 3.11.3+ (tested against 4.1), Elasticsearch 7-8.x, OpenSearch 2.x, MySQL 5.6+/MariaDB 10.11. Docker test images use `${TAG:-latest}` tags. EOL status cannot be verified without version pinning.

**Data Access Patterns (DATA-Q2):**
Excellent unified data access layer via `StorageComponent` interface. `CassandraStorage`, `ElasticsearchStorage`, and `MySQLStorage` all implement `StorageComponent` → `SpanStore` / `SpanConsumer` / `Traces`. This abstraction layer makes backend migration transparent to the application.

**Recommended Managed Database Targets:**
Given Zipkin's trace data patterns (high-write, time-series, search-heavy), the recommended migration path on AWS:

1. **Primary recommendation: Amazon OpenSearch Service** — Native replacement for the self-managed Elasticsearch storage. Zipkin already supports OpenSearch 2.x. Migration requires only changing `ES_HOSTS` to point to the managed OpenSearch domain. Provides managed scaling, automated backups, and Multi-AZ deployment.

2. **Alternative: Amazon DynamoDB** — For high-throughput trace storage with automatic scaling. Requires implementing a new `StorageComponent` for DynamoDB, leveraging the existing clean abstraction layer. DynamoDB's time-to-live (TTL) maps well to Zipkin's trace retention model.

3. **Alternative: Amazon Aurora (MySQL compatible)** — Drop-in replacement for the MySQL v1 storage. Migrate using AWS DMS. Note: MySQL storage is described as legacy with known performance issues — consider OpenSearch or DynamoDB instead.

4. **For Cassandra workloads: Amazon Keyspaces** — CQL-compatible managed service. Migration requires schema compatibility review and updating `CASSANDRA_CONTACT_POINTS` to the Keyspaces endpoint. Note: some Cassandra-specific features (SASI indexes, UDTs) may require adaptation.

**Representative AWS Services:** Amazon OpenSearch Service, Amazon DynamoDB, Amazon Aurora, Amazon Keyspaces, AWS DMS
**Migration Tools:** AWS Database Migration Service (DMS), AWS Schema Conversion Tool (SCT)
**Links:** [AWS Database Migration guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-databases/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure-as-code files exist in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize manifests were found. The only infrastructure definitions are Docker Compose files in `docker/examples/` which are explicitly labeled for learning/development — not production. All production infrastructure must be provisioned manually.

**Current CI/CD State (INF-Q11 = 3):**
Strong CI/CD pipeline via GitHub Actions with 8 workflows:
- `test.yml` — Matrix testing across JDK 21/25 with Docker-based integration tests for all storage and collector backends
- `deploy.yml` — Automated deployment to Maven Central (snapshots) and Docker Hub/GHCR
- `docker_push.yml` — Tag-triggered Docker image publishing
- `create_release.yml` — Tag-triggered release via maven-release-plugin
- `security.yml` — Trivy vulnerability and secret scanning
- `lint.yml` — YAML and markdown linting
- `test_readme.yml` — Validates README build commands on macOS/Windows

The CI pipeline is mature for library/artifact publishing. However, it does not include production deployment stages (no canary, blue/green, or rolling deployment to a running service).

**Deployment Strategy Gaps (OPS-Q5 = 1):**
The deployment model publishes artifacts (JARs to Maven Central, Docker images to registries). There is no deployment strategy for running instances — no CodeDeploy, no Argo Rollouts, no Kubernetes deployment manifests. Each consumer of Zipkin must manage their own deployment.

**Testing Gaps (OPS-Q6 = 4):**
Integration testing is excellent — Testcontainers-based integration tests cover all storage backends (`ITCassandraStorage`, `ITElasticsearchStorage`, `ITMySQLStorage`) and all collectors (`ITKafkaCollector`, `ITRabbitMQCollector`, `ITActiveMQCollector`, `ITPulsarCollector`). This is a strong foundation.

**Recommended DevOps Toolchain:**
1. **IaC Foundation:** Author AWS CDK or Terraform modules to define:
   - EKS cluster for running Zipkin (preferred per preferences)
   - Amazon OpenSearch Service domain for trace storage
   - API Gateway for trace ingestion endpoint (preferred per preferences)
   - EventBridge for event-driven alerting on Zipkin health (preferred per preferences)
   - VPC with private subnets, security groups, and VPC endpoints

2. **Deployment Automation:** Implement EKS-based deployment with:
   - Helm chart for Zipkin server (reference: [zipkin-helm](https://github.com/openzipkin/zipkin-helm) external project)
   - ArgoCD or Flux CD for GitOps deployment
   - Canary or blue/green deployment via Argo Rollouts

3. **Pipeline Enhancement:** Extend GitHub Actions with:
   - Terraform plan/apply stages
   - EKS deployment stages with health checks
   - Automated rollback on failure

**Representative AWS Services:** CDK, CloudFormation, CodeBuild, CodePipeline, CodeDeploy, EKS, ECR, CloudWatch, X-Ray
**Links:** [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC for managed compute services (ECS, EKS, Lambda, Fargate) exists in the repository. The Zipkin server is packaged as a self-contained executable JAR and Docker image (`docker/Dockerfile`) published to Docker Hub and GHCR. Docker Compose examples in `docker/examples/` define local development setups only. The Dockerfile uses a multi-stage build with `ghcr.io/openzipkin/java` base image and runs as non-root user, but there is no definition for where or how the container runs in production. |
| **Gap** | All compute is self-managed. No AWS managed compute service (ECS, EKS, Fargate, Lambda) is defined. Production deployment requires manual provisioning of compute infrastructure. |
| **Recommendation** | Deploy Zipkin on Amazon EKS (preferred) using the existing Docker image. Define EKS cluster, node groups, and Kubernetes deployment manifests via IaC. Leverage the existing Helm chart from the [zipkin-helm](https://github.com/openzipkin/zipkin-helm) project as a starting point. |
| **Evidence** | `docker/Dockerfile`, `docker/examples/docker-compose.yml`, absence of any `.tf`, `.cfn.yaml`, `cdk.json`, or Kubernetes manifests in the repository |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All three storage backends (Cassandra, Elasticsearch, MySQL) are configured as self-managed instances via Docker Compose. `docker-compose-cassandra.yml` runs `ghcr.io/openzipkin/zipkin-cassandra`, `docker-compose-elasticsearch.yml` runs `ghcr.io/openzipkin/zipkin-elasticsearch9`, and `docker-compose-mysql.yml` runs `ghcr.io/openzipkin/zipkin-mysql`. No `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, `aws_opensearch_*` resources exist. |
| **Gap** | All databases are self-managed with no automated failover, backup, or scaling. No managed database IaC exists. |
| **Recommendation** | Migrate to Amazon OpenSearch Service for the primary Elasticsearch/OpenSearch storage backend — Zipkin already supports OpenSearch 2.x natively. For Cassandra workloads, evaluate Amazon Keyspaces. For MySQL, consider Amazon Aurora MySQL. Define all database infrastructure in IaC with Multi-AZ, automated backups, and encryption at rest. |
| **Evidence** | `docker/examples/docker-compose-cassandra.yml`, `docker/examples/docker-compose-elasticsearch.yml`, `docker/examples/docker-compose-mysql.yml`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configuration) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration services (Step Functions, MWAA, Temporal, Camunda) are used. Zipkin's trace ingestion pipeline is a direct flow: collectors receive spans → storage component writes them → query API reads them. There are no multi-step business workflows requiring orchestration. However, the `zipkin-dependencies` job (referenced in README as a separate Spark job for aggregating dependency links) represents a multi-step process that runs outside the main server with no orchestration. Applying the stateful-crud calibration: the system does have multi-step processes (trace ingestion with throttling, dependency aggregation) that are handled via simple code paths rather than dedicated orchestration. |
| **Gap** | The dependency aggregation job (zipkin-dependencies) runs as a separate batch process with no managed orchestration. Throttled storage writes use in-code concurrency limits (`ThrottledStorageComponent`) rather than managed workflow primitives. |
| **Recommendation** | For the dependency aggregation batch job, consider AWS Step Functions to orchestrate the Spark job execution with retry logic and error handling. For the main trace ingestion pipeline, the direct flow is appropriate and does not require workflow orchestration. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`, `README.md` (references zipkin-dependencies Spark job), absence of `aws_sfn_*` or Temporal SDK in any file |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zipkin supports multiple messaging transports for span collection: Kafka (`KafkaCollector`), RabbitMQ (`RabbitMQCollector`), ActiveMQ (`ActiveMQCollector`), and Pulsar (`PulsarCollector`). All are configured via environment variables in `zipkin-server-shared.yml`. However, all messaging infrastructure is self-managed — Docker Compose examples use self-hosted broker images (`ghcr.io/openzipkin/zipkin-kafka`). No AWS managed messaging services (SQS, SNS, EventBridge, MSK, Amazon MQ) are defined in IaC. Applying stateful-crud calibration: the system correctly uses async messaging for cross-service state changes (trace span ingestion) alongside synchronous reads (query API), scoring a 2 because the messaging is self-managed rather than managed. |
| **Gap** | All messaging brokers are self-managed. No AWS managed messaging (MSK, Amazon MQ, SQS, EventBridge) is defined. Self-managed Kafka/RabbitMQ requires manual patching, scaling, and monitoring. |
| **Recommendation** | Migrate from self-managed Kafka to Amazon MSK Serverless or Amazon EventBridge (preferred per preferences). For RabbitMQ workloads, migrate to Amazon MQ. Avoid self-managed Kafka (per preferences). Define messaging infrastructure in IaC with appropriate scaling and monitoring. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (collector.kafka, collector.rabbitmq, collector.activemq, collector.pulsar configurations), `docker/examples/docker-compose-kafka.yml`, `zipkin-collector/kafka/`, `zipkin-collector/rabbitmq/`, `zipkin-collector/activemq/`, `zipkin-collector/pulsar/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL definitions exist in the repository. No IaC files of any kind are present. The Zipkin server is configured to listen on port 9411 (`server.port: ${QUERY_PORT:9411}`) with no network security layer defined. The Docker Compose examples expose ports directly without network isolation. |
| **Gap** | No network security infrastructure defined. Services would be deployed without VPC isolation, private subnets, or security groups. No managed networking services (VPC endpoints, PrivateLink, VPC Lattice). |
| **Recommendation** | Define a VPC with private subnets for Zipkin server and storage backends. Place the Zipkin API behind API Gateway (preferred) with VPC integration. Use security groups with least-privilege rules. Deploy storage backends in private subnets with no public access. Implement VPC endpoints for AWS service access. |
| **Evidence** | Absence of any `.tf`, CloudFormation, or CDK files. `docker/examples/docker-compose.yml` exposes port 9411 directly. `zipkin-server/src/main/resources/zipkin-server-shared.yml` (server.port configuration) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront is defined as an entry point. The Zipkin server exposes its HTTP API directly on port 9411 via Armeria server (`armeria.ports` in `zipkin-server-shared.yml`). The server has built-in compression support but no throttling, authentication, or request validation at the gateway level. CORS is configured as `allowed-origins: "*"` which allows any origin. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, no authentication at the entry point, no request validation. |
| **Recommendation** | Place Amazon API Gateway (preferred) in front of the Zipkin server. Configure throttling on the trace ingestion endpoints (`/api/v2/spans` POST) to prevent overload. Add authentication via API Gateway authorizers. Use API Gateway for the query endpoints with caching for frequently accessed data (services, span names). |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (armeria.ports, query.allowed-origins), absence of `aws_api_gateway_*`, `aws_lb_*` in any file |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or Kubernetes HPA definitions were found. The Zipkin server includes a built-in storage throttle mechanism (`STORAGE_THROTTLE_ENABLED`, min/max concurrency in `zipkin-server-shared.yml`) that limits concurrent storage writes, but this is application-level flow control, not infrastructure auto-scaling. |
| **Gap** | All capacity is statically provisioned. No auto-scaling for compute, storage, or messaging. Trace ingestion volume spikes could overwhelm static capacity. |
| **Recommendation** | When deploying on EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on trace ingestion rate metrics. Configure auto-scaling for the managed database (OpenSearch Service auto-tune, DynamoDB on-demand capacity). Set Lambda concurrency limits if using Lambda-based collectors. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage.throttle configuration), absence of any auto-scaling IaC |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. No `aws_backup_plan`, `backup_retention_period`, `point_in_time_recovery`, or S3 versioning definitions were found. The Cassandra schema defines `default_time_to_live = 604800` (7 days) on the span table and `default_time_to_live = 259200` (3 days) on the dependency table, providing built-in data expiry but no backup mechanism. |
| **Gap** | No backup configuration for any data store. No restore procedures documented. Data loss in production would be unrecoverable. |
| **Recommendation** | When migrating to managed databases, enable automated backups with appropriate retention periods. For OpenSearch Service, enable automated snapshots with cross-region replication for critical trace data. For Aurora, enable point-in-time recovery. Document and test restore procedures. |
| **Evidence** | `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql` (TTL configuration), absence of `aws_backup_plan` or backup-related IaC |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Multi-AZ or high availability configuration exists. No AZ configuration, no load balancer with cross-zone enabled, no Multi-AZ database configuration. The Cassandra schema uses `SimpleStrategy` with `replication_factor: 1`, which provides no fault tolerance. Docker Compose examples run single instances of all services. |
| **Gap** | All resources would run in a single AZ with no fault isolation. An AZ failure would take down the entire tracing system. Cassandra replication factor of 1 means a single node failure loses data. |
| **Recommendation** | Deploy on EKS across 2+ AZs. Configure managed databases with Multi-AZ (OpenSearch Service Multi-AZ with standby, Aurora Multi-AZ). Update Cassandra replication strategy to `NetworkTopologyStrategy` with RF=3 if using Amazon Keyspaces. Place ALB/API Gateway across multiple AZs. |
| **Evidence** | `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql` (`SimpleStrategy`, `replication_factor: 1`), absence of Multi-AZ IaC |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure-as-code files exist. No Terraform (`.tf`), CloudFormation templates, CDK stacks (`cdk.json`), Helm charts (`Chart.yaml`), or Kustomize manifests (`kustomization.yaml`) were found in the repository. The only infrastructure-related files are Docker Compose examples in `docker/examples/` which are explicitly labeled for learning and development, not production deployment. |
| **Gap** | 0% IaC coverage. All infrastructure must be created manually (ClickOps). No reproducible deployments, no environment consistency, no disaster recovery via IaC. This is the foundational blocker for all modernization initiatives. |
| **Recommendation** | Start with IaC for the most critical resources: (1) EKS cluster and node groups, (2) Amazon OpenSearch Service domain, (3) VPC with subnets and security groups, (4) API Gateway. Use AWS CDK (Java — matches the existing team's language) or Terraform. Reference the external [zipkin-helm](https://github.com/openzipkin/zipkin-helm) project for Kubernetes deployment patterns. |
| **Evidence** | Full repository scan: no `.tf`, `.cfn.yaml`, `.cfn.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files found. `docker/examples/README.md` labels compose files as examples. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong CI/CD automation via GitHub Actions with 8 workflows covering test, build, deploy, security, and lint stages. `test.yml` runs matrix tests across JDK 21/25 with separate Docker-based integration test jobs for each storage and collector module. `deploy.yml` deploys to Maven Central and Docker Hub/GHCR on master push. `create_release.yml` handles versioned releases via maven-release-plugin. `docker_push.yml` handles tag-triggered Docker image republishing. `security.yml` runs Trivy vulnerability scanning. `lint.yml` validates YAML and markdown. `test_readme.yml` validates README build commands on macOS and Windows. |
| **Gap** | CI/CD pipeline is mature for artifact publishing (JARs, Docker images) but lacks production deployment stages. No canary, blue/green, or rolling deployment. No automated rollback. No IaC deployment pipeline (no terraform plan/apply stages). |
| **Recommendation** | Extend the existing GitHub Actions pipeline with: (1) IaC validation stage (terraform plan / CDK synth), (2) EKS deployment stage with health checks, (3) Canary or blue/green deployment via Argo Rollouts or CodeDeploy, (4) Automated rollback on deployment failure. |
| **Evidence** | `.github/workflows/test.yml`, `.github/workflows/deploy.yml`, `.github/workflows/docker_push.yml`, `.github/workflows/create_release.yml`, `.github/workflows/security.yml`, `.github/workflows/lint.yml`, `.github/workflows/test_readme.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is Java 17 (`maven.compiler.release=17` in `pom.xml`) with the core library targeting Java 8 for broad compatibility. The UI (zipkin-lens) is TypeScript/JavaScript (`package.json` with TypeScript 4.9.4, React 16, Vite). Both Java and TypeScript have first-class AWS SDK coverage, broad cloud-native tooling, and mature framework ecosystems. The server uses Spring Boot 3.5.12 with Armeria as the HTTP server. |
| **Gap** | None — both Java and TypeScript are tier-1 languages for AWS cloud-native development. |
| **Recommendation** | No language migration needed. Continue leveraging Java's AWS SDK v2 and TypeScript's AWS SDK v3 for cloud integration. |
| **Evidence** | `pom.xml` (maven.compiler.release=17, spring-boot.version=3.5.12), `zipkin-lens/package.json` (TypeScript, React) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zipkin is a **modular monolith** — a single deployable JAR (`zipkin-server`) that bundles the core library, all storage backends, all collectors, and the UI. However, module boundaries are exceptionally well-defined: the `StorageComponent` interface cleanly separates storage implementations (Cassandra, Elasticsearch, MySQL), the `CollectorComponent` interface cleanly separates collector implementations (HTTP, gRPC, Kafka, RabbitMQ, ActiveMQ, Pulsar), and the `ZipkinQueryApiV2` is a separate concern. Modules communicate through well-defined Java interfaces with no circular dependencies. Each storage and collector module has its own Maven submodule, test suite, and can be included/excluded at build time (slim vs full builds). |
| **Gap** | Single deployment unit — all modules must be deployed together. Cannot independently scale the collector tier vs the query tier. However, module boundaries are clear with no shared mutable state between modules. |
| **Recommendation** | The current modular monolith architecture is appropriate for Zipkin's use case. The clean interface boundaries (StorageComponent, CollectorComponent) mean decomposition is achievable if independent scaling is needed in the future. No immediate decomposition is required. |
| **Evidence** | `pom.xml` (modules list), `zipkin/src/main/java/zipkin2/storage/StorageComponent.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `docker/Dockerfile` (single deployable) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Good mix of synchronous and asynchronous communication. Synchronous: HTTP collector (`ZipkinHttpCollector`), gRPC collector (`ZipkinGrpcCollector`), and query API (`ZipkinQueryApiV2`). Asynchronous: Kafka collector (`KafkaCollector`), RabbitMQ collector (`RabbitMQCollector`), ActiveMQ collector (`ActiveMQCollector`), Pulsar collector (`PulsarCollector`). Applying stateful-crud calibration: the system has managed messaging for key flows (span ingestion via multiple async transports) alongside synchronous HTTP for read operations (query API), which matches the expected pattern. However, the async messaging uses self-managed brokers rather than managed services. |
| **Gap** | Async messaging exists and is well-implemented at the application level, but uses self-managed brokers. Synchronous HTTP remains the primary ingestion path for many deployments. |
| **Recommendation** | When deploying on AWS, prefer Amazon MSK Serverless or Amazon EventBridge (preferred) for the Kafka collector transport to reduce operational overhead. The HTTP/gRPC synchronous collectors are appropriate for low-latency ingestion scenarios. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (all collector configurations), `zipkin-collector/kafka/`, `zipkin-collector/rabbitmq/`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinGrpcCollector.java` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Applying stateful-crud calibration: Most operations in Zipkin are designed to be fast. Trace span ingestion is non-blocking (collectors accept spans and write to storage asynchronously). Query operations have a configurable timeout (`QUERY_TIMEOUT: 11s` in `zipkin-server-shared.yml`). The storage throttle mechanism (`ThrottledStorageComponent` with min/max concurrency) prevents long-running storage writes from blocking the system. The `zipkin-dependencies` aggregation job is inherently long-running but runs as a separate batch process. The self-tracing configuration (`ZipkinSelfTracingConfiguration`) uses async span handlers (`AsyncZipkinSpanHandler`) with configurable flush intervals. |
| **Gap** | Query timeout is hardcoded at 11 seconds. No async job pattern with status polling for the dependency aggregation job. The storage throttle uses in-process concurrency limits rather than a managed queue. |
| **Recommendation** | The current handling is appropriate for Zipkin's workload profile. For the dependency aggregation job, consider orchestrating it via AWS Step Functions with status callbacks. If deploying queries against large trace stores, consider adding async query support with status polling for queries exceeding the 11-second timeout. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (query.timeout, storage.throttle), `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`, `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Consistent URL-path versioning strategy. All query and ingestion endpoints use `/api/v2/` prefix: `/api/v2/traces`, `/api/v2/trace/{traceId}`, `/api/v2/traceMany`, `/api/v2/services`, `/api/v2/spans`, `/api/v2/remoteServices`, `/api/v2/dependencies`, `/api/v2/autocompleteKeys`, `/api/v2/autocompleteValues`. The v2 version reflects the transition from Zipkin's v1 Thrift-based data model to the v2 JSON data model. Legacy v1 endpoints are maintained for backward compatibility. |
| **Gap** | Versioning is applied consistently to all query endpoints. However, there is no formal backward compatibility guarantee documented in the repository (no API changelog, no deprecation policy). Internal endpoints (health, actuator, prometheus) do not use the versioning scheme. |
| **Recommendation** | Document the API versioning policy and backward compatibility guarantees. Generate an OpenAPI specification from the Armeria `@Get` annotations in `ZipkinQueryApiV2.java` to formalize the API contract. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (`@Get("/api/v2/...")` annotations), `README.md` (API endpoint documentation) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Eureka-based service discovery is integrated via `ZipkinEurekaDiscoveryConfiguration`. When `EUREKA_SERVICE_URL` is set, Zipkin registers itself with a Eureka server using Armeria's `EurekaUpdatingListener`. Configuration includes `EUREKA_APP_NAME`, `EUREKA_INSTANCE_ID`, and `EUREKA_HOSTNAME`. A Docker Compose example (`docker-compose-eureka.yml`) demonstrates the integration. Other endpoint configurations use environment variables (`CASSANDRA_CONTACT_POINTS`, `ES_HOSTS`, `KAFKA_BOOTSTRAP_SERVERS`) rather than dynamic discovery. |
| **Gap** | Service discovery is available via Eureka but not all downstream connections use it. Storage backend and messaging broker endpoints are configured via static environment variables rather than dynamic discovery. |
| **Recommendation** | When deploying on AWS, leverage AWS Cloud Map or EKS service discovery (CoreDNS) for dynamic service resolution. For managed services (OpenSearch, MSK), use VPC endpoints which provide stable DNS names. Consider API Gateway (preferred) as a centralized service catalog for the Zipkin API. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/eureka/ZipkinEurekaDiscoveryConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` (discovery.eureka, storage.cassandra3.contact-points, storage.elasticsearch.hosts), `docker/examples/docker-compose-eureka.yml` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zipkin stores structured trace data (spans, annotations, tags, dependency links), not unstructured documents. Trace data is stored in Cassandra (CQL tables), Elasticsearch (JSON indices), or MySQL (relational tables). When using Elasticsearch/OpenSearch, trace data is stored as structured JSON documents with defined index templates — this is effectively managed storage with search capability. However, there is no S3-based storage, no document parsing pipeline, and no unstructured data management. The in-memory storage option (`InMemoryStorage`) is the default and provides no persistence. |
| **Gap** | No S3-based storage for trace data export or archival. No parsing pipeline for extracting insights from trace data. Trace data stored in Elasticsearch is queryable but not available in S3 for analytics or ML integration. |
| **Recommendation** | Consider exporting trace data to Amazon S3 for long-term archival and analytics. S3-stored trace data can feed into Amazon Athena for ad hoc analysis or Amazon Bedrock (preferred) for AI-powered trace analysis. Use S3 lifecycle policies to manage retention. |
| **Evidence** | `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql`, `zipkin-storage/mysql-v1/src/main/resources/mysql.sql`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage.type, storage.mem) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Excellent unified data access layer. The `StorageComponent` abstract class in `zipkin/src/main/java/zipkin2/storage/StorageComponent.java` provides a single interface with `spanStore()`, `spanConsumer()`, `traces()`, `serviceAndSpanNames()`, and `autocompleteTags()` methods. All storage backends — `CassandraStorage`, `ElasticsearchStorage`, `MySQLStorage`, and `InMemoryStorage` — implement this interface. The query API (`ZipkinQueryApiV2`) and all collectors interact with storage exclusively through the `StorageComponent` interface. This means the storage backend can be swapped by changing a single environment variable (`STORAGE_TYPE`) without any code changes. |
| **Gap** | None — this is a textbook implementation of the repository pattern with clean separation of concerns. |
| **Recommendation** | Leverage the existing `StorageComponent` interface when implementing new storage backends for AWS managed services (e.g., DynamoDB, Amazon OpenSearch Service). The clean abstraction makes migration straightforward. |
| **Evidence** | `zipkin/src/main/java/zipkin2/storage/StorageComponent.java`, `zipkin-storage/cassandra/src/main/java/zipkin2/storage/cassandra/CassandraStorage.java`, `zipkin-storage/elasticsearch/src/main/java/zipkin2/elasticsearch/ElasticsearchStorage.java`, `zipkin-storage/mysql-v1/src/main/java/zipkin2/storage/mysql/v1/MySQLStorage.java` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No explicit engine version pinning in IaC (no IaC exists). Docker test images use `${TAG:-latest}` tags. Application documentation specifies minimum supported versions: Cassandra 3.11.3+ (tested against 4.1), Elasticsearch 7-8.x, OpenSearch 2.x, MySQL 5.6+/MariaDB 10.11. The `pom.xml` pins client library versions (Cassandra Java driver 4.19.2, MariaDB client 3.5.7) but not database engine versions. Note: MySQL 5.6 reached EOL in February 2021, and Cassandra 3.11 reached EOL in May 2023, yet Zipkin still documents support for these as minimum versions. |
| **Gap** | No version pinning in infrastructure definitions. Minimum supported versions include EOL engines (MySQL 5.6, Cassandra 3.11). No documented version-update procedure covering downtime windows or rollback. Docker test images use `latest` tags which can drift unpredictably. |
| **Recommendation** | Pin database engine versions in IaC when deploying managed services. Use Amazon OpenSearch Service 2.x (current, supported). For Aurora MySQL, use the latest MySQL 8.x compatible version. For Amazon Keyspaces, version is managed by AWS. Establish a version-update procedure with rollback plans. |
| **Evidence** | `pom.xml` (java-driver.version=4.19.2, mariadb-java-client.version=3.5.7), `docker/examples/docker-compose-cassandra.yml` (`${TAG:-latest}`), `README.md` (documented minimum versions) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs in any storage backend. MySQL schema (`mysql.sql`) uses standard SQL DDL: `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ADD INDEX`, `PRIMARY KEY`. No stored procedures, triggers, or functions. Character set is UTF-8, engine is InnoDB with ROW_FORMAT=COMPRESSED. Cassandra schema (`zipkin2-schema.cql`) uses standard CQL: `CREATE KEYSPACE`, `CREATE TYPE`, `CREATE TABLE`. No Cassandra-specific stored procedures or triggers. All business logic resides in the Java application layer via the `StorageComponent` implementations. |
| **Gap** | None — all business logic is in the application layer. Schema is clean, portable, and uses only standard SQL/CQL. |
| **Recommendation** | Maintain this pattern. The absence of stored procedures makes database migration straightforward. The MySQL schema can be migrated to Aurora MySQL with minimal changes. The Cassandra schema may need adaptation for Amazon Keyspaces (UDT support, SASI index compatibility). |
| **Evidence** | `zipkin-storage/mysql-v1/src/main/resources/mysql.sql`, `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql`, `zipkin-storage/cassandra/src/main/resources/zipkin2-schema-indexes.cql` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit-specific logging infrastructure defined. Application uses SLF4J/Logback with trace ID propagation in log patterns (`logging.pattern.level: "%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}"`). This provides request tracing in logs but not audit logging. No `aws_cloudtrail` resources, no log file validation, no immutable storage for logs. |
| **Gap** | No CloudTrail or equivalent audit logging. No immutable log storage. Cannot trace administrative actions or forensic analysis after incidents. |
| **Recommendation** | Enable AWS CloudTrail for all API calls. Configure log file validation and store logs in S3 with Object Lock for immutability. Send application logs to CloudWatch Logs with defined retention policies. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging.pattern.level), absence of `aws_cloudtrail` in any file |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration found. No KMS keys, no encryption configuration on data stores. The Cassandra, Elasticsearch, and MySQL configurations in `zipkin-server-shared.yml` include SSL/TLS options for connections (`use-ssl`, `ssl.no-verify`) but not encryption at rest. No `kms_key_id` on any resource. No IaC exists to define encryption. |
| **Gap** | No encryption at rest for any data store. Trace data may contain sensitive information (service names, endpoints, tags) stored unencrypted. |
| **Recommendation** | When deploying managed databases, enable encryption at rest with customer-managed KMS keys. OpenSearch Service supports encryption at rest by default. Aurora supports encryption at rest via KMS. Define a centralized key management policy. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage.cassandra3.use-ssl, storage.elasticsearch.ssl), absence of `aws_kms_key` or `kms_key_id` in any file |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication on any endpoint. The query API (`ZipkinQueryApiV2`) serves all endpoints without authentication middleware. CORS `allowed-origins` is configured as `"*"` in `zipkin-server-shared.yml`, allowing requests from any origin. No auth middleware, no API Gateway authorizers, no Bearer token validation, no `@Authenticated` annotations. The server is designed to be deployed as an internal service, but no network-level access control is defined either. |
| **Gap** | All API endpoints are open — no authentication, no authorization. Critical security vulnerability for any network-accessible deployment. Trace data (potentially containing PII in tags) is accessible to anyone who can reach port 9411. |
| **Recommendation** | Place Amazon API Gateway (preferred) in front of Zipkin with IAM or Cognito authorizers. Restrict CORS allowed-origins to specific domains. For internal deployments, enforce network-level access control via security groups and VPC isolation. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no auth annotations), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (query.allowed-origins: "*") |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, OIDC, SAML, or external IdP configuration. Eureka integration (`ZipkinEurekaDiscoveryConfiguration`) is for service discovery, not identity. The server application manages no authentication at all — there is no user identity concept in the current architecture. |
| **Gap** | No identity management. Cannot attribute API calls to users or services. No SSO, no federation, no token-based identity. |
| **Recommendation** | Integrate with Amazon Cognito for user authentication on the Zipkin UI and API. Use API Gateway (preferred) with Cognito user pool authorizers. For service-to-service authentication (span ingestion), use IAM roles with API Gateway IAM authorization. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/eureka/ZipkinEurekaDiscoveryConfiguration.java` (service discovery, not identity), absence of `aws_cognito_*` or OIDC configuration in any file |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Credentials are managed via environment variables: `CASSANDRA_USERNAME`, `CASSANDRA_PASSWORD`, `MYSQL_USER`, `MYSQL_PASS`, `ES_USERNAME`, `ES_PASSWORD`, `RABBIT_PASSWORD`, `ACTIVEMQ_USERNAME`, `ACTIVEMQ_PASSWORD`. The Elasticsearch storage has a more sophisticated credential option via `ES_CREDENTIALS_FILE` with `DynamicCredentialsFileLoader` that reads credentials from a properties file and refreshes them on an interval (`ES_CREDENTIALS_REFRESH_INTERVAL: 5` minutes). This file-based approach is compatible with credential rotation but is not integrated with a secrets management system. No AWS Secrets Manager, HashiCorp Vault, or Parameter Store integration. GitHub Actions workflows use GitHub Secrets for deployment credentials (`GH_TOKEN`, `GPG_SIGNING_KEY`, `SONATYPE_USER`, `DOCKERHUB_TOKEN`). |
| **Gap** | Production database credentials are in environment variables with no rotation. No centralized secrets management. The ES credential file rotation mechanism is a good pattern but requires manual file management. |
| **Recommendation** | Integrate with AWS Secrets Manager for all database and messaging credentials. Use EKS Secrets Store CSI Driver to inject secrets from Secrets Manager into pods. Configure automated rotation for database credentials. The existing ES credentials file mechanism can be adapted to read from Secrets Manager. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (all credential environment variables), `zipkin-server/src/main/java/zipkin2/server/internal/elasticsearch/DynamicCredentialsFileLoader.java`, `.github/workflows/deploy.yml` (GitHub Secrets) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker images use `ghcr.io/openzipkin/java:${java_version}` as the base image (Java 25.0.2_p10 on Alpine Linux). The Dockerfile follows security best practices: runs as non-root user (`adduser -g '' -h ${PWD} -D ${USER}`), includes HEALTHCHECK with 5s interval and 30s start period, uses multi-stage build to minimize image size, removes platform-specific native libraries not needed for the target architecture. However, no SSM Patch Manager, no AWS Inspector, and no Snyk runtime scanning is configured. Trivy scanning exists in CI but not as a runtime vulnerability scanner. |
| **Gap** | Good container hardening practices but no runtime vulnerability scanning or managed patching. Base image updates are manual. No CIS benchmark compliance validation. |
| **Recommendation** | Enable Amazon ECR image scanning for the published Docker images. Configure AWS Inspector for runtime vulnerability detection when deployed on EKS. Automate base image updates via Dependabot or Renovate bot for the `ghcr.io/openzipkin/java` base image version. |
| **Evidence** | `docker/Dockerfile` (non-root user, HEALTHCHECK, multi-stage build), `.github/workflows/security.yml` (Trivy scanning) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Trivy vulnerability and secret scanner is integrated into CI/CD (`security.yml`) — scans the entire repository for HIGH and CRITICAL vulnerabilities with exit code 1 (pipeline fails on findings). ErrorProne static analysis is configured in the Maven build (`errorprone.version=2.48.0`) running on every compile. License checking via `license-maven-plugin` ensures license compliance. However, there is no dedicated SAST tool (SonarQube, Semgrep, CodeGuru Reviewer) and no container image scanning in the build pipeline (Trivy scans the filesystem, not built Docker images). |
| **Gap** | No dedicated SAST tool — ErrorProne catches Java coding errors but not security vulnerabilities specifically. No container image scanning in CI. Trivy filesystem scan does not cover all vulnerability vectors (e.g., compiled bytecode vulnerabilities). No security gate blocking on critical findings in the build pipeline (only in the security workflow). |
| **Recommendation** | Add Amazon CodeGuru Reviewer or Semgrep as a SAST tool in the CI pipeline. Add ECR image scanning or Trivy container scanning step after Docker image builds in `docker_push.yml`. Consider adding OWASP dependency-check for Java-specific vulnerability scanning alongside Trivy. |
| **Evidence** | `.github/workflows/security.yml` (Trivy action), `pom.xml` (errorprone configuration, license-maven-plugin) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Zipkin **is** a distributed tracing system — it is the thing being assessed for tracing. Additionally, Zipkin has self-tracing capability via `ZipkinSelfTracingConfiguration` using the Brave tracing library. When `SELF_TRACING_ENABLED=true`, Zipkin traces its own operations (storage reads/writes, HTTP requests) and sends self-traces to its own storage. Trace ID propagation is integrated into the logging pattern (`%X{traceId}/%X{spanId}`), enabling correlation between logs and traces. The self-tracing uses configurable sample rates (`SELF_TRACING_SAMPLE_RATE`) and rate limiting (`SELF_TRACING_TRACES_PER_SECOND`). |
| **Gap** | None — Zipkin provides comprehensive distributed tracing with self-tracing capability and trace-log correlation. |
| **Recommendation** | Enable self-tracing in production deployments for operational visibility. When deployed on AWS, also integrate with AWS X-Ray for unified trace visibility across AWS services. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` (self-tracing configuration, logging.pattern.level) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No error budgets, no latency targets, no availability targets. The query has a configurable timeout (`QUERY_TIMEOUT: 11s`) which could be considered an implicit latency bound, but it is not formalized as an SLO. The Prometheus metrics integration provides the measurement foundation, but no SLOs are defined on top of it. |
| **Gap** | No SLOs defined for any user journey. Cannot measure whether the tracing system meets reliability expectations. No error budget tracking. |
| **Recommendation** | Define SLOs for critical Zipkin user journeys: (1) Trace ingestion latency p99 < 500ms, (2) Trace query latency p99 < 2s, (3) Span drop rate < 0.1%, (4) API availability > 99.9%. Implement SLO monitoring using CloudWatch or the existing Prometheus metrics. Track error budgets. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (query.timeout: 11s), absence of SLO definitions in any file |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Micrometer/Prometheus metrics integration exists via `ZipkinPrometheusMetricsConfiguration` and `MicrometerCollectorMetrics`. Custom collector metrics include: `zipkin_collector.messages` (cumulative messages received per transport), `zipkin_collector.messages_dropped` (cumulative messages dropped), `zipkin_collector.bytes` (cumulative bytes), `zipkin_collector.spans` (cumulative spans read), `zipkin_collector.spans_dropped` (cumulative spans dropped), `zipkin_collector.message_spans` (gauge of spans per message), `zipkin_collector.message_bytes` (gauge of bytes per message). HTTP request metrics are also recorded. These are operational/infrastructure metrics rather than business outcome metrics. |
| **Gap** | No business outcome metrics. Missing: trace search success rate, unique services tracked, trace completeness rate, user query patterns, dependency graph coverage. Existing metrics are operational (throughput, drop rates) not business-oriented. |
| **Recommendation** | Add business metrics: (1) Unique services traced per day, (2) Trace completeness (% of traces with expected span count), (3) Query success rate by user, (4) Dependency graph coverage (% of known services with traces). Publish to CloudWatch Custom Metrics with dashboards. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`, `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`, `docker/examples/prometheus/prometheus.yml` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found. Prometheus integration exists for metric collection (`docker/examples/prometheus/prometheus.yml` scrapes the `/prometheus` endpoint at 5s intervals), but no alerting rules are defined. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no Prometheus AlertManager configuration. |
| **Gap** | No alerting on error rates, latency degradation, span drop rates, or storage health. Degradation would go undetected until users report issues. |
| **Recommendation** | Configure CloudWatch anomaly detection on key Zipkin metrics when deployed on AWS. Set alarms on: (1) Span drop rate exceeding threshold, (2) Query latency p99 exceeding SLO, (3) Collector message error rate, (4) Storage health check failures. Integrate with SNS for notifications. |
| **Evidence** | `docker/examples/prometheus/prometheus.yml`, `benchmarks/src/test/resources/prometheus.yml`, absence of alerting rules or CloudWatch alarm definitions |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy for running Zipkin instances. The CI/CD pipeline publishes artifacts (JARs to Maven Central, Docker images to Docker Hub/GHCR) but does not deploy to any running environment. There is no CodeDeploy configuration, no Kubernetes deployment manifests, no Argo Rollouts, no blue/green or canary deployment patterns. Docker Compose examples are for development only. Each consumer of Zipkin manages their own deployment independently. |
| **Gap** | Direct-to-production deployment model with no staged rollout. No canary, blue/green, or rolling deployment. No automated rollback. |
| **Recommendation** | Implement deployment to EKS (preferred) using Helm with Argo Rollouts for canary deployments. Define a deployment pipeline that: (1) Deploys to a staging environment, (2) Runs smoke tests against staging, (3) Canary deploys to production with traffic shifting, (4) Automatically rolls back on health check failures. |
| **Evidence** | `.github/workflows/deploy.yml` (publishes artifacts, no production deployment), `.github/workflows/docker_push.yml` (pushes images, no deployment), absence of Kubernetes manifests, Helm charts, or deployment configurations |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Excellent integration test coverage using Testcontainers. Docker-based integration tests cover all storage backends and collectors with real infrastructure: `ITCassandraStorage`, `ITElasticsearchStorage`, `ITMySQLStorage` (storage), `ITKafkaCollector`, `ITRabbitMQCollector`, `ITActiveMQCollector`, `ITPulsarCollector`, `ITScribeCollector` (collectors), and `ITZipkinServer`, `ITZipkinSelfTracing`, `ITZipkinMetrics`, `ITZipkinHealth`, `ITZipkinEureka`, `ITZipkinGrpcCollector` (server). The `test.yml` workflow runs these in parallel Docker test jobs for each module. The `test_readme.yml` validates build commands on macOS and Windows. Maven failsafe plugin is configured for integration test execution with `useModulePath=false` for compatibility. |
| **Gap** | None — integration test coverage is comprehensive and runs in CI on every push and PR. |
| **Recommendation** | Maintain current integration testing practices. When deploying on AWS, add end-to-end tests against the deployed stack (trace ingestion through managed services to query verification). |
| **Evidence** | `.github/workflows/test.yml` (test_docker matrix), `pom.xml` (maven-failsafe-plugin), `zipkin-collector/kafka/src/test/java/zipkin2/collector/kafka/ITKafkaCollector.java`, `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks or automated incident response found. `SECURITY.md` describes a basic security disclosure process (email `zipkin-admin@googlegroups.com`) but explicitly states "There is no SLA or warranty offered by volunteers." No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions incident workflows, no self-healing patterns. |
| **Gap** | No runbooks. No automated incident response. Incident handling is entirely ad hoc. As a volunteer-maintained open source project, this is expected but represents a gap for production deployments. |
| **Recommendation** | Create operational runbooks for common scenarios: (1) Storage backend failure recovery, (2) Collector message backlog handling, (3) High span drop rate triage, (4) Zipkin server restart procedures. Implement automated health checks and self-healing via EKS liveness/readiness probes (the existing Docker HEALTHCHECK can be reused). |
| **Evidence** | `SECURITY.md`, absence of runbook files, SSM documents, or incident automation in any file |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file for observability assets. No per-service dashboards defined in code. No team attribution on alarms or metrics. The Prometheus metrics exist but have no defined owner. The `SECURITY.md` mentions `zipkin-admin@googlegroups.com` as the contact for security concerns, but there is no operational ownership structure. |
| **Gap** | No observability ownership. Monitoring is fragmented with no clear responsibility. As an open source project, ownership is community-driven rather than team-attributed. |
| **Recommendation** | For production deployments, define observability ownership: (1) CODEOWNERS for monitoring configurations, (2) Per-service CloudWatch dashboards with named owners, (3) On-call rotation for Zipkin operational alerts, (4) SLO owners responsible for error budget management. |
| **Evidence** | Absence of `CODEOWNERS` file, absence of dashboard definitions, `SECURITY.md` (volunteer community statement) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tags found. No IaC exists to define tags. No `default_tags` in Terraform provider, no `tags` on resources, no tag policies or enforcement. The Docker images have OCI labels (`org.opencontainers.image.description`) but these are container metadata, not AWS resource tags. |
| **Gap** | No resource tagging. Cannot track costs per workload, identify resource ownership, or enforce budget controls for Zipkin infrastructure. |
| **Recommendation** | When defining IaC, implement a tagging standard with required tags: `Environment` (dev/staging/prod), `Service` (zipkin), `Owner` (team), `CostCenter`, `Project`. Use CDK/Terraform `default_tags` to ensure all resources are tagged. Enforce via AWS Config rules. |
| **Evidence** | `docker/Dockerfile` (OCI labels only), absence of any IaC with resource tags |

## Learning Materials

The following learning resources are linked to the triggered pathways:

### Move to Managed Databases
- [Move to Managed Databases Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [AWS Database Migration guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-databases/welcome.html)

### Move to Modern DevOps
- [Move to Modern DevOps Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [EKS Workshop](https://www.eksworkshop.com/) (for EKS deployment patterns)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q11, APP-Q1, DATA-Q3, SEC-Q7 | Parent POM: Java 17, Spring Boot 3.5.12, ErrorProne config, module structure, dependency versions |
| `docker/Dockerfile` | INF-Q1, SEC-Q6, OPS-Q9 | Multi-stage Docker build, non-root user, HEALTHCHECK, base image version |
| `docker/examples/docker-compose.yml` | INF-Q1, INF-Q5 | Base Docker Compose for development |
| `docker/examples/docker-compose-cassandra.yml` | INF-Q2, INF-Q9 | Self-managed Cassandra via Docker |
| `docker/examples/docker-compose-elasticsearch.yml` | INF-Q2 | Self-managed Elasticsearch via Docker |
| `docker/examples/docker-compose-mysql.yml` | INF-Q2 | Self-managed MySQL via Docker |
| `docker/examples/docker-compose-kafka.yml` | INF-Q4 | Self-managed Kafka via Docker |
| `docker/examples/docker-compose-eureka.yml` | APP-Q6 | Eureka service discovery example |
| `docker/examples/prometheus/prometheus.yml` | OPS-Q3, OPS-Q4 | Prometheus scrape configuration |
| `.github/workflows/test.yml` | INF-Q11, OPS-Q6 | CI test matrix with Docker integration tests |
| `.github/workflows/deploy.yml` | INF-Q11, SEC-Q5, OPS-Q5 | Deploy to Maven Central and Docker Hub/GHCR |
| `.github/workflows/security.yml` | SEC-Q6, SEC-Q7 | Trivy vulnerability and secret scanning |
| `.github/workflows/docker_push.yml` | INF-Q11, OPS-Q5 | Tag-triggered Docker image publishing |
| `.github/workflows/create_release.yml` | INF-Q11 | Tag-triggered release workflow |
| `.github/workflows/lint.yml` | INF-Q11 | YAML and markdown linting |
| `.github/workflows/test_readme.yml` | INF-Q11, OPS-Q6 | README build command validation |
| `zipkin-server/src/main/resources/zipkin-server-shared.yml` | INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, APP-Q3, APP-Q4, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q2 | Central configuration: storage, collectors, discovery, query, self-tracing |
| `zipkin-server/src/main/java/zipkin/server/ZipkinServer.java` | APP-Q2 | Spring Boot entry point |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` | APP-Q2, APP-Q5, SEC-Q3 | REST API with /api/v2/ versioning, no auth |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` | APP-Q3 | Synchronous HTTP span collector |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinGrpcCollector.java` | APP-Q3 | Synchronous gRPC span collector |
| `zipkin-server/src/main/java/zipkin2/server/internal/eureka/ZipkinEurekaDiscoveryConfiguration.java` | APP-Q6, SEC-Q4 | Eureka service discovery integration |
| `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java` | APP-Q4, OPS-Q1 | Self-tracing via Brave |
| `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java` | OPS-Q3 | Prometheus metrics configuration |
| `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java` | OPS-Q3 | Custom collector throughput metrics |
| `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java` | INF-Q3, APP-Q4 | Storage write throttling |
| `zipkin-server/src/main/java/zipkin2/server/internal/elasticsearch/DynamicCredentialsFileLoader.java` | SEC-Q5 | File-based credential rotation for ES |
| `zipkin/src/main/java/zipkin2/storage/StorageComponent.java` | APP-Q2, DATA-Q2 | Unified storage interface |
| `zipkin-storage/cassandra/src/main/java/zipkin2/storage/cassandra/CassandraStorage.java` | DATA-Q2 | Cassandra StorageComponent implementation |
| `zipkin-storage/elasticsearch/src/main/java/zipkin2/elasticsearch/ElasticsearchStorage.java` | DATA-Q2 | Elasticsearch StorageComponent implementation |
| `zipkin-storage/mysql-v1/src/main/java/zipkin2/storage/mysql/v1/MySQLStorage.java` | DATA-Q2 | MySQL StorageComponent implementation |
| `zipkin-storage/mysql-v1/src/main/resources/mysql.sql` | DATA-Q1, DATA-Q4 | MySQL schema — standard SQL DDL, no stored procedures |
| `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql` | DATA-Q1, DATA-Q4, INF-Q8, INF-Q9 | Cassandra schema — TTL, SimpleStrategy RF=1 |
| `zipkin-storage/cassandra/src/main/resources/zipkin2-schema-indexes.cql` | DATA-Q4 | Cassandra index definitions |
| `zipkin-collector/kafka/` | INF-Q4, APP-Q3 | Kafka collector module |
| `zipkin-collector/rabbitmq/` | INF-Q4, APP-Q3 | RabbitMQ collector module |
| `zipkin-collector/activemq/` | INF-Q4 | ActiveMQ collector module |
| `zipkin-collector/pulsar/` | INF-Q4 | Pulsar collector module |
| `zipkin-lens/package.json` | APP-Q1 | TypeScript/JavaScript UI dependencies |
| `README.md` | INF-Q3, APP-Q5, DATA-Q3 | Project documentation, storage backend details, API description |
| `SECURITY.md` | OPS-Q7, OPS-Q8 | Security process, volunteer community statement |
| `zipkin-collector/kafka/src/test/java/zipkin2/collector/kafka/ITKafkaCollector.java` | OPS-Q6 | Kafka integration test |
| `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java` | OPS-Q6 | Server integration test |
