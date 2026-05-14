# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | zipkin |
| **Date** | 2026-04-30 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, observability, tracing |
| **Context** | Distributed tracing system. |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **2.18 / 4.0** |

**Archetype Justification**: Zipkin-server has persistent state (Cassandra, Elasticsearch, MySQL storage backends with database drivers), exposes write endpoints (`POST /api/v2/spans`, gRPC span ingestion) alongside read endpoints (`GET /api/v2/traces`, `/api/v2/services`), and manages entity lifecycle (span storage with TTL). While it also consumes messages from Kafka/RabbitMQ/ActiveMQ/Pulsar (event-processor trait), the primary surface is CRUD-like — accept spans, store them, query them — making `stateful-crud` the best fit.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.36 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 3.33 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.89 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.18 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | Zero infrastructure-as-code — all infrastructure is undefined or manually created | Blocks reproducible deployments, disaster recovery, and environment consistency; foundational for all other modernization pathways |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Lambda/Fargate) defined; Docker Compose examples show self-managed containers only | Cannot leverage elastic scaling, managed patching, or AWS integration; prerequisite for Move to Containers and Move to Cloud Native |
| 3 | SEC-Q3: API Authentication | 1 | Zipkin API is entirely unauthenticated by default — no OAuth2, JWT, or API key protection on any endpoint | Exposes trace data to unauthorized access; critical security gap for any production deployment |
| 4 | INF-Q2: Managed Databases | 1 | All storage backends (Cassandra, Elasticsearch, MySQL) are self-managed with no AWS managed service definitions | Full operational burden for patching, backup, scaling, and failover on the operator; triggers Move to Managed Databases pathway |
| 5 | OPS-Q2: SLO Definitions | 1 | No SLO definitions, error budgets, or formal service-level targets found | Cannot measure whether the tracing system meets user expectations; no objective basis for prioritizing improvements |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 4 (≥ 2). Zipkin provides well-versioned REST API endpoints at `/api/v2/*` with documented behavior in `zipkin-server/README.md` and structured JSON responses.
- **What it enables:** An API-aware agent that can discover and invoke Zipkin's query endpoints as tools — querying traces by service name, retrieving dependency graphs, and looking up spans programmatically.
- **Additional steps:** Generate a formal OpenAPI spec from the Armeria-annotated endpoints. Currently the API is documented in README prose but lacks a machine-readable spec file.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). GitHub Actions CI/CD pipelines exist with automated test, build, deploy, and release workflows.
- **What it enables:** A DevOps agent that can trigger deployments, check build status, monitor test results, and manage Docker image releases via GitHub Actions API.
- **Additional steps:** None — the existing pipeline automation is directly invocable via GitHub API.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists: `README.md` (top-level), `zipkin-server/README.md` (comprehensive configuration reference), `docker/README.md`, `RATIONALE.md` files across modules, and per-storage `README.md` files.
- **What it enables:** A RAG-based knowledge agent that indexes Zipkin's documentation corpus to answer developer questions about configuration, deployment options, storage backend selection, and troubleshooting.
- **Additional steps:** Index the documentation files and provide a retrieval interface (e.g., using Amazon Bedrock with knowledge base).
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 4 (≥ 2). Zipkin self-traces with Brave instrumentation (`ZipkinSelfTracingConfiguration.java`), publishes Prometheus metrics via Micrometer, and has structured logging with trace ID correlation in log patterns.
- **What it enables:** An observability agent that queries Zipkin's own traces and metrics to detect anomalies in span ingestion rates, storage latency, and collector health — using the very tracing data Zipkin collects about itself.
- **Additional steps:** Deploy a Prometheus instance to scrape Zipkin metrics (example config exists in `docker/examples/docker-compose-prometheus.yml`).
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with well-defined module boundaries). Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | Dockerfile exists in the repository — container definitions found. Contextual guard prevents trigger. |
| 3 | Move to Open Source | Not Triggered | — | — | All database engines are open source (Cassandra, Elasticsearch/OpenSearch, MySQL via MariaDB driver). No commercial engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed). DATA-Q3 = 2 (version pinning inconsistent). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: Zipkin collectors consume spans from message brokers — this is span ingestion, not data analytics/ETL processing. No data processing workloads detected. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (zero IaC coverage). Supporting: OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 4 (integration tests exist — strong foundation). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "Distributed tracing system." does not contain AI-related signal terms. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** Zipkin supports three self-managed storage backends — Cassandra (via java-driver 4.19.2), Elasticsearch/OpenSearch (via Armeria HTTP client), and MySQL (via MariaDB JDBC client 3.5.7 + jOOQ 3.19.29). Docker Compose examples (`docker/examples/docker-compose-cassandra.yml`, `docker-compose-elasticsearch.yml`, `docker-compose-mysql.yml`) deploy these as standalone containers with no managed service configuration. All operational burden (patching, backup, scaling, failover) falls on the operator.

**Engine Versions and EOL Status:** Driver versions are pinned in `pom.xml` (java-driver 4.19.2, mariadb-java-client 3.5.7), but the actual database engine versions are not pinned in the repository — they default to `${TAG:-latest}` in Docker Compose. No documented version-update procedure exists.

**Data Access Patterns:** Zipkin has an exemplary unified data access layer via `StorageComponent` abstraction (`zipkin/src/main/java/zipkin2/storage/StorageComponent.java`). All backends implement the same `SpanStore`, `SpanConsumer`, and `Traces` interfaces. This makes backend migration significantly easier — the application layer is already decoupled from specific storage engines.

**Recommended Migration Targets (respecting preferences):**

| Current Backend | Recommended AWS Managed Service | Rationale |
|----------------|--------------------------------|-----------|
| Cassandra | **Amazon DynamoDB** (preferred) or Amazon Keyspaces | DynamoDB is preferred per analysis preferences. Keyspaces provides Cassandra-compatible API for minimal code changes. DynamoDB requires a new `StorageComponent` implementation but offers superior scaling and zero operational overhead. |
| Elasticsearch/OpenSearch | **Amazon OpenSearch Service** | Drop-in replacement — Zipkin's Elasticsearch storage module already supports OpenSearch (see `OpensearchVersion.java`, `OpensearchSpecificTemplates.java`). Migration is primarily an infrastructure change. |
| MySQL | **Amazon Aurora MySQL** (preferred) or Amazon RDS MySQL | Aurora is preferred per analysis preferences. MariaDB JDBC driver is compatible with Aurora MySQL. Schema (`mysql.sql`) uses standard SQL with no stored procedures — direct migration path. |

**Migration Tools:** AWS Database Migration Service (DMS) for data migration. No AWS Schema Conversion Tool needed — schemas are simple and use standard SQL/CQL without stored procedures.

**Key Advantage:** The `StorageComponent` abstraction means a new managed-service backend (e.g., `DynamoDBStorage`) can be implemented as a new module without modifying existing code. The pluggable architecture is already designed for this.

**References:**
- [AWS Database Migration Service](https://aws.amazon.com/dms/)
- [Amazon OpenSearch Service](https://aws.amazon.com/opensearch-service/)
- [Amazon DynamoDB](https://aws.amazon.com/dynamodb/)
- [Amazon Aurora](https://aws.amazon.com/rds/aurora/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** Zero. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. All infrastructure is either undefined or manually created. Docker Compose files in `docker/examples/` serve as development/learning examples but are explicitly marked "not for production deployments."

**Current CI/CD State:** GitHub Actions workflows provide automated build (`test.yml`), deploy (`deploy.yml`), security scanning (`security.yml`), Docker image push (`docker_push.yml`), linting (`lint.yml`), and release creation (`create_release.yml`). The CI/CD pipeline is reasonably mature for application code but has no IaC deployment track — there is no infrastructure to deploy because no IaC exists.

**Deployment Strategy Gaps:** No canary, blue/green, or rolling deployment strategy. Docker images are pushed directly. Maven artifacts deploy to Sonatype Central on master push. No staged rollout or traffic shifting.

**Testing Foundation:** Strong — extensive integration tests using Testcontainers for all storage backends and collectors, run in CI via `test_docker` matrix in `test.yml`. This is an excellent foundation for safe deployment automation.

**Recommended DevOps Toolchain (respecting preferences):**

1. **Infrastructure as Code:** Define Zipkin infrastructure using AWS CDK or Terraform:
   - **EKS cluster** (preferred over self-managed Kubernetes) for container orchestration
   - **Amazon OpenSearch Service** for trace storage
   - **Amazon API Gateway** (preferred) as the entry point with throttling and authentication
   - **Amazon EventBridge** (preferred) for event-driven integrations
   - VPC with private subnets, security groups, and network segmentation

2. **Deployment Pipeline:** Extend existing GitHub Actions with:
   - IaC validation and plan stage (CDK synth / terraform plan)
   - Container image build and push to Amazon ECR
   - EKS deployment with rolling update or canary strategy (Argo Rollouts or AWS CodeDeploy)
   - Post-deployment integration test stage leveraging existing Testcontainers tests

3. **Operational IaC:** Add CloudWatch alarms, backup plans, and auto-scaling configuration as code.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS CodePipeline, AWS CodeBuild, AWS CDK, Amazon CloudWatch, AWS X-Ray

**References:**
- [Move to Modern DevOps Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defines any AWS compute resources. The repository provides a multi-stage Dockerfile (`docker/Dockerfile`) that builds both `zipkin` (full) and `zipkin-slim` images based on `ghcr.io/openzipkin/java`. Docker Compose examples in `docker/examples/` run Zipkin as standalone containers with no orchestration platform. No ECS task definitions, EKS manifests, Lambda functions, or Fargate configurations exist anywhere in the repository. |
| **Gap** | All compute is self-managed Docker containers with no managed container orchestration or serverless. There is no path from the current Docker Compose examples to a production-grade managed compute deployment. |
| **Recommendation** | Deploy Zipkin on **Amazon EKS** (preferred per analysis preferences) using the existing Docker images. Create Kubernetes Deployment manifests, Service definitions, and HPA (Horizontal Pod Autoscaler) configuration. Alternatively, deploy on Amazon ECS with Fargate for a lower-operational-overhead option. |
| **Evidence** | `docker/Dockerfile`, `docker/examples/docker-compose.yml`, `docker/examples/docker-compose-cassandra.yml`, `docker/examples/docker-compose-elasticsearch.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All three storage backends are self-managed. Cassandra is deployed as `ghcr.io/openzipkin/zipkin-cassandra` container (`docker/examples/docker-compose-cassandra.yml`). Elasticsearch is deployed as `ghcr.io/openzipkin/zipkin-elasticsearch9` container (`docker/examples/docker-compose-elasticsearch.yml`). MySQL is deployed as `ghcr.io/openzipkin/zipkin-mysql` container (`docker/examples/docker-compose-mysql.yml`). No `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, or `aws_opensearch_*` resources exist. |
| **Gap** | All databases are self-managed in containers, requiring manual patching, backup, scaling, and failover. No managed database service is configured. |
| **Recommendation** | Migrate to **Amazon OpenSearch Service** (already supported — `OpensearchVersion.java` and `OpensearchSpecificTemplates.java` exist in the codebase) for the Elasticsearch backend. For MySQL, migrate to **Amazon Aurora MySQL** (preferred). For Cassandra, evaluate **Amazon DynamoDB** (preferred) with a new StorageComponent implementation or Amazon Keyspaces for Cassandra-compatible API. |
| **Evidence** | `docker/examples/docker-compose-cassandra.yml`, `docker/examples/docker-compose-elasticsearch.yml`, `docker/examples/docker-compose-mysql.yml`, `zipkin-storage/elasticsearch/src/main/java/zipkin2/elasticsearch/OpensearchVersion.java` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated workflow orchestration service (Step Functions, Temporal, MWAA) is used. Zipkin has multi-step operations within its storage pipeline: span ingestion → validation → sampling → storage write → indexing (for Cassandra and Elasticsearch). The storage throttle mechanism (`zipkin-server/src/main/java/zipkin2/server/internal/throttle/`) implements a basic concurrency limiter using Netflix concurrency-limits library, but this is application-code-level flow control, not a dedicated orchestration service. |
| **Gap** | Multi-step storage operations (particularly bulk writes, index management, and dependency link computation) are handled entirely in application code with no dedicated workflow orchestration. Error handling, retry logic, and state management are embedded in storage module code. |
| **Recommendation** | For the `stateful-crud` archetype, evaluate **AWS Step Functions** for orchestrating batch operations like dependency link computation and index rotation. The storage write path's current inline approach is acceptable for individual span ingestion but would benefit from managed orchestration for background maintenance tasks. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/throttle/`, `zipkin-storage/cassandra/src/main/java/zipkin2/storage/cassandra/CassandraSpanConsumer.java` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zipkin integrates with four message brokers for span collection: Kafka (`zipkin-collector/kafka/`), RabbitMQ (`zipkin-collector/rabbitmq/`), ActiveMQ (`zipkin-collector/activemq/`), and Pulsar (`zipkin-collector/pulsar/`). All are self-managed broker integrations — the collector modules use client libraries (Kafka client, RabbitMQ AMQP client, ActiveMQ client, Pulsar client) connecting to externally provisioned broker instances. No `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*`, or `aws_eventbridge_*` resources exist. Docker Compose examples show self-managed Kafka and RabbitMQ containers. |
| **Gap** | Cross-service messaging (span ingestion from instrumented applications) relies entirely on self-managed message brokers. This creates operational overhead for broker patching, scaling, and monitoring. |
| **Recommendation** | Migrate from self-managed Kafka (to be avoided per preferences) to **Amazon MSK Serverless** or **Amazon EventBridge** (preferred). For simpler queue-based collection, evaluate **Amazon SQS**. The collector architecture's pluggable design makes adding a new managed-service collector straightforward. |
| **Evidence** | `zipkin-collector/kafka/`, `zipkin-collector/rabbitmq/`, `zipkin-collector/activemq/`, `zipkin-collector/pulsar/`, `docker/examples/docker-compose-kafka.yml`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation configuration exists in the repository. No `aws_vpc`, `aws_subnet`, or `aws_security_group` resources. Docker Compose examples expose port 9411 directly on the container host with no network isolation between Zipkin and its storage backends. The `docker-compose.yml` files use Docker's default bridge networking. |
| **Gap** | Services are deployed with no network segmentation or isolation. In a production deployment, Zipkin and its storage backends would all be on the same flat network with no access controls. |
| **Recommendation** | Define VPC infrastructure with private subnets for storage backends (Cassandra, Elasticsearch, MySQL) and public-facing subnet only for the API entry point (behind **Amazon API Gateway**, preferred). Use security groups to restrict traffic between Zipkin, its storage backends, and message brokers. Add VPC endpoints for AWS service access. |
| **Evidence** | `docker/examples/docker-compose.yml`, `docker/examples/docker-compose-cassandra.yml` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zipkin-server exposes port 9411 directly via the Armeria HTTP server (`zipkin-server/src/main/resources/zipkin-server-shared.yml`: `server.port: ${QUERY_PORT:9411}`). The Dockerfile exposes ports 9410 and 9411 directly. No API Gateway, ALB, CloudFront, or any managed entry point is configured. CORS is configured as `allowed-origins: "*"` (all origins allowed). |
| **Gap** | Services are exposed directly with no gateway, load balancer, throttling, authentication, or request validation at the entry point. The wildcard CORS policy is overly permissive. |
| **Recommendation** | Deploy **Amazon API Gateway** (preferred) as the entry point for Zipkin's API. Configure throttling, request validation, and authentication (OAuth2/JWT). Use API Gateway's integration with AWS WAF for additional protection. For the UI, add **Amazon CloudFront** as a CDN. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `docker/Dockerfile` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No `aws_autoscaling_*`, `aws_appautoscaling_*`, ASG, HPA, or Lambda concurrency configurations found. Docker Compose examples deploy single instances. The only concurrency control is the storage throttle mechanism (`STORAGE_THROTTLE_ENABLED`, `STORAGE_THROTTLE_MAX_CONCURRENCY`), which is application-level back-pressure, not infrastructure auto-scaling. |
| **Gap** | All capacity is statically provisioned. No ability to respond to traffic spikes (e.g., during incident investigation when many engineers query traces simultaneously) or scale down during low demand. |
| **Recommendation** | When deployed on EKS, configure Horizontal Pod Autoscaler (HPA) based on custom metrics (span ingestion rate via `zipkin_collector.spans` Prometheus metric). For storage backends, configure auto-scaling on the managed services (OpenSearch Service domain scaling, Aurora auto-scaling, DynamoDB auto-scaling). |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage throttle settings) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. No `aws_backup_plan`, `backup_retention_period`, `point_in_time_recovery`, S3 versioning, or EBS snapshot policies found. The Cassandra schema defines `default_time_to_live = 604800` (7 days) and the dependency table uses `default_time_to_live = 259200` (3 days), which provides TTL-based data lifecycle but not backup/recovery. |
| **Gap** | No automated backups configured for any data store. No documented restore procedures. A storage failure would result in complete data loss. |
| **Recommendation** | When migrating to managed databases: enable automated backups with PITR on Aurora MySQL, configure automated snapshots on Amazon OpenSearch Service domains, and enable point-in-time recovery on DynamoDB tables. Define backup retention periods appropriate for trace data (typically 7-30 days matching the existing Cassandra TTL). |
| **Evidence** | `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql` (TTL settings) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. No `multi_az = true`, `availability_zones`, or cross-AZ deployment definitions found. Docker Compose examples deploy single instances of both Zipkin and its storage backends. The Cassandra schema uses `SimpleStrategy` with `replication_factor: 1` (`zipkin2-schema.cql`), which is a single-node configuration with no replication or fault tolerance. |
| **Gap** | All resources are single-instance with no fault isolation. An AZ failure would take down the entire tracing system — both the query/collection API and the storage backend. |
| **Recommendation** | Deploy Zipkin on EKS across 2+ AZs with multiple replicas. For managed databases: enable Multi-AZ on Aurora MySQL, deploy OpenSearch Service with 2+ AZ data nodes, and configure DynamoDB's built-in multi-AZ replication. Update the Cassandra replication strategy from `SimpleStrategy` to `NetworkTopologyStrategy` with replication across multiple AZs if continuing with Cassandra. |
| **Evidence** | `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql`, `docker/examples/docker-compose.yml` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform (`.tf`), CloudFormation templates, CDK stacks (`cdk.json`), Helm charts (`Chart.yaml`), or Kustomize (`kustomization.yaml`) files exist in the repository. The only infrastructure definition is Docker Compose files in `docker/examples/`, which are explicitly labeled "meant for learning Zipkin, not production deployments." |
| **Gap** | 0% of infrastructure is defined as code. All infrastructure for a production deployment would need to be created manually or from scratch. No reproducibility, version control, or automated provisioning. |
| **Recommendation** | Create IaC covering the full deployment stack: EKS cluster, managed databases (OpenSearch Service, Aurora), networking (VPC, subnets, security groups), API Gateway, monitoring (CloudWatch alarms), and backup plans. Use **AWS CDK** (TypeScript or Java — matching the existing developer skillset) or Terraform. Start with the compute and database layers as the highest-impact IaC targets. |
| **Evidence** | `docker/examples/docker-compose.yml` ("Note that this file is meant for learning Zipkin, not production deployments.") |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions workflows provide comprehensive CI/CD for application code: `test.yml` (matrix build with JDK 21 and 25, Docker-based integration tests for all storage backends and collectors), `deploy.yml` (snapshot deployment to Maven Central on master push, Docker image push to ghcr.io and Docker Hub), `security.yml` (Trivy vulnerability and secret scanning), `docker_push.yml` (Docker image re-push on tag), `create_release.yml` (Maven release on tag), `lint.yml` (Markdown and YAML linting). Build scripts in `build-bin/` provide structured deployment automation. |
| **Gap** | CI/CD covers application code comprehensively but has no IaC deployment track — there is no infrastructure as code to deploy. No automated rollback mechanism exists for Docker image deployments. The pipeline deploys directly without canary or blue/green staging. |
| **Recommendation** | Extend the existing pipeline with an IaC deployment stage once IaC is created. Add automated rollback capability for Docker image deployments. Implement a staged deployment strategy (canary or blue/green) when deploying to EKS. |
| **Evidence** | `.github/workflows/test.yml`, `.github/workflows/deploy.yml`, `.github/workflows/security.yml`, `.github/workflows/docker_push.yml`, `.github/workflows/create_release.yml`, `.github/workflows/lint.yml`, `build-bin/` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is **Java 17** (`maven.compiler.release=17` in `pom.xml`) with modern framework stack: Spring Boot 3.5.12, Armeria 1.37.0, Jackson 2.21.2, Micrometer 1.16.4. The core `zipkin` library targets Java 8 for maximum consumer compatibility but all server-side code is Java 17. Frontend is TypeScript with React 16, Vite 4, and Redux. Build requires JDK 21+ (`maven-enforcer-plugin` enforces `[21,22),[25,26)`). |
| **Gap** | None for the Java backend. The frontend uses React 16 (current is React 19) and some dated UI dependencies (@material-ui v4 rather than MUI v5+), but this is a UI modernization concern, not a cloud-native language gap. |
| **Recommendation** | No action needed for the backend — Java 17 + Spring Boot 3.x is a current, well-supported stack with first-class AWS SDK coverage. Consider upgrading the frontend to React 18+ and MUI v5 in a separate effort. |
| **Evidence** | `pom.xml` (java version, Spring Boot version, Armeria version), `zipkin-lens/package.json` (React, TypeScript versions) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zipkin-server is a **modular monolith** — a single deployable unit (Spring Boot executable jar) with well-defined module boundaries. Storage backends (Cassandra, Elasticsearch, MySQL, in-memory) are pluggable via the `StorageComponent` abstraction. Collectors (HTTP, gRPC, Kafka, RabbitMQ, ActiveMQ, Pulsar, Scribe) are pluggable modules loaded based on configuration. Modules are declared as `<optional>true</optional>` Maven dependencies and activated via Spring conditional configuration (`@ConditionalOnProperty`). No circular dependencies between modules. The `zipkin-slim` build excludes heavy backends (Cassandra, MySQL, collectors), demonstrating clean module separation. |
| **Gap** | While module boundaries are excellent and there are no circular dependencies, all modules still deploy as a single unit. Read (query API) and write (collector) paths cannot scale independently. A spike in trace ingestion affects query performance since both share the same JVM. |
| **Recommendation** | The current modular monolith architecture is well-designed for Zipkin's use case. If independent scaling of read and write paths becomes necessary, the `StorageComponent` abstraction and conditional module loading make it feasible to split into separate deployments (a collector-only instance and a query-only instance) with minimal code changes — both already share the same codebase. |
| **Evidence** | `zipkin-server/pom.xml` (optional dependencies, slim profile), `zipkin/src/main/java/zipkin2/storage/StorageComponent.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zipkin uses both synchronous and asynchronous communication patterns. **Sync:** HTTP POST (`/api/v1/spans`, `/api/v2/spans`) and gRPC endpoints for span ingestion; HTTP GET (`/api/v2/traces`, `/api/v2/services`) for queries. **Async:** Kafka, RabbitMQ, ActiveMQ, and Pulsar collectors consume spans asynchronously from message queues. Storage writes use async callbacks (`Callback<Void>` pattern in `ZipkinHttpCollector.java`). Applying `stateful-crud` calibration: the mix of async and sync is appropriate — async for key workflows (span ingestion from brokers), sync for queries. |
| **Gap** | The async path is available but uses self-managed brokers (addressed in INF-Q4). Some state-change propagation between Zipkin instances (if running multiple) has no async notification mechanism — each instance independently queries storage. |
| **Recommendation** | The current async/sync mix is well-suited for the `stateful-crud` archetype. When migrating to managed messaging (INF-Q4 recommendation), ensure the async span ingestion path via **Amazon EventBridge** or **Amazon SQS** maintains the same throughput characteristics. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin-collector/kafka/`, `zipkin-collector/rabbitmq/`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zipkin handles potentially long-running operations with appropriate patterns. **Storage throttle:** A concurrency limiter (`STORAGE_THROTTLE_ENABLED`, backed by Netflix concurrency-limits) prevents storage overload by queuing and rejecting requests when concurrency exceeds configured limits. **Async writes:** Span storage uses async callbacks — `collector.acceptSpans()` in `ZipkinHttpCollector.java` delegates to a blocking task executor, and the HTTP response returns `202 Accepted` immediately. **Query timeout:** The query API has a configurable timeout (`QUERY_TIMEOUT: 11s`). |
| **Gap** | The dependency link computation (trace analysis to generate service dependency graphs) can be long-running for large datasets, and it runs synchronously within the request. No background job pattern or status polling mechanism exists for this operation. |
| **Recommendation** | For the `stateful-crud` archetype, the current approach is largely appropriate. Consider offloading dependency link computation to a background job (AWS Step Functions or a dedicated worker) with status polling if trace volume grows significantly. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (CompletableCallback, async span acceptance), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage throttle, query timeout) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Zipkin uses a consistent URL path versioning strategy. The API has two versions: `/api/v1/spans` (legacy Thrift/JSON v1 format) and `/api/v2/spans`, `/api/v2/traces`, `/api/v2/services`, `/api/v2/remoteServices`, `/api/v2/dependencies`, `/api/v2/autocompleteKeys`, `/api/v2/autocompleteValues`, `/api/v2/trace/{traceId}`, `/api/v2/traceMany`. Both v1 and v2 are maintained with backward compatibility — the HTTP collector detects format mismatches and provides clear error messages (`testForUnexpectedFormat` method in `ZipkinHttpCollector.java`). |
| **Gap** | None — versioning is comprehensive and consistent. |
| **Recommendation** | No action needed. The API versioning strategy is mature. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zipkin has built-in Eureka service discovery via `armeria-eureka` dependency and `ZipkinEurekaDiscoveryConfiguration.java`. Configuration includes Eureka service URL (`EUREKA_SERVICE_URL`), app name (`EUREKA_APP_NAME: zipkin`), instance ID, and hostname — all configurable via environment variables. Docker Compose example exists (`docker/examples/docker-compose-eureka.yml`). However, storage backend endpoints (Cassandra, Elasticsearch, MySQL) use hard-coded or environment-variable-based configuration, not dynamic discovery. |
| **Gap** | Service discovery via Eureka is available for Zipkin service registration, but storage backend endpoints are configured via environment variables (e.g., `CASSANDRA_CONTACT_POINTS`, `ES_HOSTS`, `MYSQL_HOST`) rather than dynamic discovery. |
| **Recommendation** | When deployed on EKS, leverage Kubernetes-native service discovery (DNS-based) instead of Eureka. For managed database endpoints, use AWS service discovery or simply configure managed service endpoints via environment variables (which is standard practice for managed services with static endpoints). |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/eureka/ZipkinEurekaDiscoveryConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` (eureka and storage configuration) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zipkin stores structured trace data (spans with defined schemas). No unstructured data handling (documents, images, PDFs) exists. No S3 bucket definitions, Textract integrations, or document parsing libraries found. Trace data is stored in structured formats across all backends: Cassandra CQL tables, Elasticsearch JSON documents with defined mappings, MySQL relational tables. |
| **Gap** | No object storage or unstructured data capabilities. If trace data needs to be archived for long-term retention beyond the database TTL (e.g., for compliance), there is no S3-based archival pipeline. |
| **Recommendation** | Implement a trace archival pipeline to **Amazon S3** for long-term retention. Export expired trace data from the active storage backend to S3 in Parquet or JSON format. This enables cost-effective long-term storage with Athena querying for historical analysis. |
| **Evidence** | `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql`, `zipkin-storage/mysql-v1/src/main/resources/mysql.sql`, `zipkin-storage/elasticsearch/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Zipkin has an exemplary unified data access layer. The `StorageComponent` abstract class (`zipkin/src/main/java/zipkin2/storage/StorageComponent.java`) defines a clean contract with `SpanStore` (queries), `SpanConsumer` (writes), `Traces` (trace retrieval), `ServiceAndSpanNames` (name lookups), and `AutocompleteTags` (autocomplete). Every backend implements this contract: `CassandraStorage`, `ElasticsearchStorage`, `MySQLStorage`, and `InMemoryStorage`. All data access flows through this single abstraction — no scattered database connections anywhere in the codebase. The `StorageComponent.Builder` pattern ensures consistent configuration across backends. |
| **Gap** | None — this is a textbook implementation of the Repository pattern. |
| **Recommendation** | No action needed. The unified data access layer is a significant architectural strength that facilitates backend migration. Maintain this pattern when adding new storage backends (e.g., DynamoDB). |
| **Evidence** | `zipkin/src/main/java/zipkin2/storage/StorageComponent.java`, `zipkin/src/main/java/zipkin2/storage/SpanStore.java`, `zipkin/src/main/java/zipkin2/storage/SpanConsumer.java`, `zipkin-storage/cassandra/src/main/java/zipkin2/storage/cassandra/CassandraStorage.java`, `zipkin-storage/elasticsearch/src/main/java/zipkin2/elasticsearch/ElasticsearchStorage.java`, `zipkin-storage/mysql-v1/src/main/java/zipkin2/storage/mysql/v1/MySQLStorage.java` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Driver versions are pinned in `pom.xml`: Cassandra java-driver 4.19.2, MariaDB JDBC client 3.5.7, jOOQ 3.19.29. However, actual database engine versions are NOT pinned in the repository — Docker Compose files use `${TAG:-latest}` for all storage images. Docker test images reference specific versions (e.g., `zipkin-elasticsearch8`, `zipkin-elasticsearch9`, `zipkin-opensearch2`, `zipkin-mysql`, `zipkin-cassandra`) but the actual engine version within those images is controlled externally. No documented version-update procedure exists. |
| **Gap** | Driver versions are pinned but database engine versions are implicit. No documented process for evaluating or upgrading database engine versions. No EOL tracking for the specific Cassandra, Elasticsearch, or MySQL versions used in production. |
| **Recommendation** | Pin database engine versions explicitly in deployment configuration (not just Docker image tags). Document a version-update procedure covering: testing with new versions, downtime planning, rollback steps. When migrating to managed databases, use explicit engine version parameters (e.g., Aurora MySQL engine version, OpenSearch Service version). |
| **Evidence** | `pom.xml` (driver versions), `docker/examples/docker-compose-cassandra.yml` (`${TAG:-latest}`), `docker/test-images/` (test image directories) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. The MySQL schema (`zipkin-storage/mysql-v1/src/main/resources/mysql.sql`) contains only `CREATE TABLE` and `ALTER TABLE ADD INDEX` statements using standard SQL. The Cassandra schema (`zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql`) uses standard CQL. All business logic resides in the application layer via jOOQ (MySQL) and the Cassandra java-driver (Cassandra). Elasticsearch uses HTTP API calls with no server-side scripting. |
| **Gap** | None — all business logic is in the application layer. |
| **Recommendation** | No action needed. The absence of stored procedures and proprietary SQL is an architectural strength that significantly simplifies database migration (no logic extraction needed, no AWS SCT required). |
| **Evidence** | `zipkin-storage/mysql-v1/src/main/resources/mysql.sql`, `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql`, `zipkin-storage/mysql-v1/src/main/java/zipkin2/storage/mysql/v1/` (jOOQ-based queries) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail, audit logging, or equivalent configuration exists in the repository. No `aws_cloudtrail` resources, no audit log configuration, no log file validation, no immutable storage for logs. Application logging uses SLF4J/Log4j2 with trace ID correlation in log patterns, but this is operational logging, not audit logging. |
| **Gap** | No audit trail for API access, administrative actions, or data access. Cannot trace who accessed which traces or when. |
| **Recommendation** | Enable AWS CloudTrail for the AWS account hosting Zipkin. For application-level audit logging, add access logging to the Zipkin API (who queried which trace IDs, which services). Store audit logs in S3 with Object Lock for immutability. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging configuration) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration exists. No KMS key definitions, no `kms_key_id` on any data store, no encryption configuration in Docker Compose examples. Storage backends are deployed with default settings — no explicit encryption enabled. Trace data (which can contain sensitive PII in span tags and annotations) is stored in plaintext. |
| **Gap** | All data at rest (traces, annotations, dependency links) is unencrypted. Trace data commonly contains sensitive information (user IDs, IP addresses, HTTP headers). |
| **Recommendation** | When migrating to managed databases, enable encryption at rest with AWS-managed keys at minimum: OpenSearch Service encryption, Aurora storage encryption, DynamoDB encryption. For sensitive environments, use customer-managed KMS keys with documented rotation policies. |
| **Evidence** | `docker/examples/docker-compose-cassandra.yml`, `docker/examples/docker-compose-elasticsearch.yml`, `docker/examples/docker-compose-mysql.yml` |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Zipkin API is entirely unauthenticated by default. No authentication middleware, no OAuth2/JWT validation, no API key mechanism exists. The CORS configuration (`zipkin-server-shared.yml`) allows all origins: `allowed-origins: "*"`. The only credential handling is for storage backend connections (Cassandra, Elasticsearch, MySQL username/password) and Eureka service discovery — not for API consumer authentication. |
| **Gap** | All API endpoints are open — anyone with network access can query traces, submit spans, and access the dependency graph. This is a critical security gap for any production deployment handling sensitive trace data. |
| **Recommendation** | Deploy **Amazon API Gateway** (preferred) in front of Zipkin with OAuth2/JWT authorizer using Amazon Cognito or an existing corporate IdP. Separate the span collection endpoint (`POST /api/v2/spans`) from the query endpoints with different auth policies — collection may use API keys for instrumented services while queries use OAuth2 for human users. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (CORS config, no auth config), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no auth annotations) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration exists. No Cognito, OIDC, SAML, or external IdP configuration found. Eureka service discovery supports basic auth (`EUREKA_SERVICE_URL` can contain credentials), but this is for service registration, not user authentication. The Elasticsearch storage module has a `BasicCredentials.java` and `DynamicCredentialsFileLoader.java` for backend auth, but these are storage connection credentials, not API identity integration. |
| **Gap** | Application manages no authentication at all — there is no auth system to integrate with an IdP. |
| **Recommendation** | Integrate with a centralized IdP (Amazon Cognito or corporate OIDC/SAML provider) via API Gateway authorizer. This provides SSO, token-based auth, and user attribution for trace access. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (eureka config), `zipkin-server/src/main/java/zipkin2/server/internal/eureka/` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Storage credentials are passed via environment variables: `CASSANDRA_USERNAME`, `CASSANDRA_PASSWORD`, `ES_USERNAME`, `ES_PASSWORD`, `MYSQL_USER`, `MYSQL_PASS`. CI/CD secrets (GPG keys, Sonatype credentials, Docker Hub tokens) use GitHub Actions secrets properly (`${{ secrets.* }}`). However, Docker Compose examples contain plaintext credentials: `docker-compose-mysql.yml` has `MYSQL_USER=zipkin`, `MYSQL_PASS=zipkin` inline. The `docker-compose-cassandra.yml` has commented-out plaintext credentials. No Secrets Manager, Vault, or encrypted parameter store integration exists. |
| **Gap** | No plaintext credentials in source code itself, but Docker Compose examples contain plaintext credentials in version-controlled files. No secrets management service integration — all production credentials would be in plain environment variables without rotation. |
| **Recommendation** | Integrate **AWS Secrets Manager** for all database credentials. Reference Secrets Manager secrets in EKS pod environment via External Secrets Operator or Secrets Store CSI Driver. Remove plaintext credentials from Docker Compose examples (replace with placeholder instructions). Configure automated rotation for database credentials. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (env var credential references), `docker/examples/docker-compose-mysql.yml` (plaintext MYSQL_USER/MYSQL_PASS), `.github/workflows/deploy.yml` (GitHub secrets usage) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Dockerfile uses `ghcr.io/openzipkin/java:${java_version}-jre` as the base image (Alpine-based, non-root user configured). The container runs as a non-root `zipkin` user (`RUN adduser -g '' -h ${PWD} -D ${USER}`). Health checks are configured (`HEALTHCHECK --interval=5s --start-period=30s`). The Trivy security scanner (`security.yml`) scans for vulnerabilities with HIGH/CRITICAL severity gates. However, no SSM Patch Manager, AWS Inspector, or CIS-hardened AMI references exist — these are infrastructure-level concerns not addressed by the application repository. |
| **Gap** | Application-level container security is reasonable (non-root, health checks, vulnerability scanning). No infrastructure-level patching strategy (SSM, Inspector) because no infrastructure is defined. |
| **Recommendation** | When deploying to EKS: use Bottlerocket OS for worker nodes (hardened and auto-updating), enable ECR image scanning for container vulnerabilities, integrate AWS Inspector for runtime vulnerability analysis. The existing Trivy scanning in CI provides a good foundation for container-level security. |
| **Evidence** | `docker/Dockerfile` (non-root user, health check), `.github/workflows/security.yml` (Trivy scanner) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Trivy vulnerability and secret scanner is integrated into CI/CD (`security.yml`): `aquasecurity/trivy-action@v0.35.0` with `scan-type: 'fs'`, `scanners: vuln,secret`, `severity: HIGH,CRITICAL`, `exit-code: '1'` (fails build on findings). This provides dependency vulnerability scanning AND secret scanning with a blocking security gate. Runs on push to master and on pull requests. |
| **Gap** | Trivy covers dependency vulnerabilities and secrets but no SAST (Static Application Security Testing) tool is configured. No SonarQube, Semgrep, CodeGuru Reviewer, or equivalent for detecting application-level code vulnerabilities. No container image scanning separate from the filesystem scan. |
| **Recommendation** | Add a SAST tool (Semgrep or Amazon CodeGuru Reviewer) to the CI pipeline alongside Trivy. Add ECR container image scanning when publishing Docker images. The combination of Trivy (dependencies + secrets) and a SAST tool (code vulnerabilities) would provide Score 4 coverage. |
| **Evidence** | `.github/workflows/security.yml` (Trivy configuration with HIGH/CRITICAL gate) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Zipkin IS the distributed tracing system, and it traces itself. Self-tracing is built in via Brave instrumentation (`ZipkinSelfTracingConfiguration.java`, `brave.version=6.3.0`, `zipkin-reporter-brave 3.5.1`). When `SELF_TRACING_ENABLED=true`, Zipkin generates traces for its own API operations and storage calls, with configurable sample rate and traces-per-second. The logging pattern includes trace ID correlation: `"%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}"`. Armeria integration via `armeria-brave6` provides automatic HTTP/gRPC request tracing. |
| **Gap** | None — distributed tracing with trace ID propagation is the core product and is self-applied. |
| **Recommendation** | No action needed. Ensure `SELF_TRACING_ENABLED=true` in production deployments for operational visibility into Zipkin's own performance. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java`, `zipkin-server/pom.xml` (brave, zipkin-reporter-brave dependencies), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (self-tracing and logging config) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No error budget tracking, no SLI configuration, no service-level targets. The Prometheus configuration example (`docker/examples/docker-compose-prometheus.yml`) provides metric scraping but no SLO-based alerting or error budget calculations. |
| **Gap** | No formal definition of acceptable service levels for trace ingestion latency, query response time, or data availability. No objective measurement of whether the tracing system meets user expectations. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Span ingestion latency p99 < 100ms, (2) Trace query response time p99 < 2s, (3) Span ingestion availability > 99.9%. Implement SLO monitoring using Prometheus metrics already published (`http.server.requests` timer, `zipkin_collector.spans` counter). Configure error budget tracking with CloudWatch or Grafana. |
| **Evidence** | `docker/examples/docker-compose-prometheus.yml` (example only, no SLOs) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zipkin publishes business-relevant collector metrics via Micrometer/Prometheus: `zipkin_collector.messages` (cumulative messages by transport), `zipkin_collector.messages_dropped`, `zipkin_collector.bytes`, `zipkin_collector.spans` (cumulative spans by transport), `zipkin_collector.spans_dropped`, `zipkin_collector.message_spans` (gauge), `zipkin_collector.message_bytes` (gauge). HTTP request duration is tracked with `http.server.requests` timer with method, URI, and status tags. JVM metrics (memory, GC, threads, classloader, processor) are also registered. |
| **Gap** | Collector metrics are business-relevant (spans ingested, dropped rates) but there are no higher-level business metrics like: traces per unique service, query frequency by service name, active service count trends. No dashboards or alerting on these metrics within the repository. |
| **Recommendation** | Add custom metrics for: number of unique services reporting spans (service onboarding indicator), query patterns (most-queried services, dependency graph usage), and storage utilization. The Prometheus example and Grafana integration in `docker/examples/docker-compose-prometheus.yml` provide the foundation — add dashboards for these business metrics. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`, `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration exists. The Prometheus example (`docker/examples/docker-compose-prometheus.yml`) is labeled "meant for learning Zipkin, not production deployments." No CloudWatch anomaly detection, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. No static threshold alarms configured. |
| **Gap** | No alerting on error rates, span drop rates, query latency, or storage health. Production incidents (e.g., storage backend failure, sudden spike in dropped spans) would go undetected until users notice missing traces. |
| **Recommendation** | Configure alerting on key metrics: `zipkin_collector.spans_dropped` rate > threshold (span loss), `zipkin_collector.messages_dropped` rate > threshold (collector failure), `http.server.requests` p99 latency > threshold (degraded query performance). Use CloudWatch anomaly detection for dynamic thresholds on span ingestion rates. |
| **Evidence** | `docker/examples/docker-compose-prometheus.yml` (example only) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy beyond direct Docker image push. The `deploy.yml` workflow pushes snapshots to Maven Central and Docker images to ghcr.io/Docker Hub directly on master push. The `docker_push.yml` pushes images on tag. No canary, blue/green, rolling, or staged deployment exists. No CodeDeploy, Argo Rollouts, Helm canary, or traffic shifting configuration. |
| **Gap** | Direct-to-production deployment with no staged rollout. A bad image push immediately affects all users pulling the latest tag. No automated rollback mechanism. |
| **Recommendation** | When deploying on EKS, implement rolling deployments (Kubernetes native) at minimum, with canary deployments (via Argo Rollouts or AWS CodeDeploy) for higher safety. Define health check gates that prevent proceeding with rollout if span ingestion or query latency degrades. |
| **Evidence** | `.github/workflows/deploy.yml`, `.github/workflows/docker_push.yml` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Extensive integration tests exist for all critical workflows, run in CI. The `test.yml` workflow defines a `test_docker` matrix that runs Docker-based integration tests for: `zipkin-collector-activemq`, `zipkin-collector-kafka`, `zipkin-collector-rabbitmq`, `zipkin-collector-pulsar`, `zipkin-storage-cassandra`, `zipkin-storage-elasticsearch`, `zipkin-storage-mysql-v1`, and `zipkin-server`. Tests use Testcontainers (`testcontainers.version=2.0.4`) to spin up real database and broker instances. IT classes include `ITCassandraStorage`, `ITElasticsearchStorage` (V8, V9), `ITOpenSearchStorageV2`, `ITMySQLStorage`, `ITZipkinServer`. Unit tests run separately with JDK 21 and 25 matrix. |
| **Gap** | None — integration test coverage is comprehensive and runs in CI for every PR and push. |
| **Recommendation** | No action needed. The integration test suite is a significant strength. Leverage these tests as post-deployment validation when implementing canary deployments on EKS. |
| **Evidence** | `.github/workflows/test.yml` (test_docker matrix), `zipkin-storage/cassandra/src/test/java/zipkin2/storage/cassandra/ITCassandraStorage.java`, `zipkin-storage/elasticsearch/src/test/java/zipkin2/elasticsearch/integration/ITElasticsearchStorage.java`, `zipkin-storage/mysql-v1/src/test/java/zipkin2/storage/mysql/v1/ITMySQLStorage.java` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, SSM automation documents, self-healing patterns, or incident response automation found. No `RUNBOOKS.md`, no Systems Manager documents, no Lambda-based remediation, no Step Functions for incident workflows. The `SECURITY.md` file exists but it's a vulnerability disclosure policy, not an operational runbook. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (storage backend failure, span ingestion spike, memory exhaustion, credential rotation). |
| **Recommendation** | Create runbooks for common failure scenarios: (1) Storage backend unreachable — steps to verify, failover to in-memory, restore connection. (2) Span ingestion rate spike — enable storage throttle, scale collectors. (3) Memory exhaustion — tune `MEM_MAX_SPANS`, GC settings. Store runbooks as versioned Markdown in the repository. Automate common remediation steps with AWS Systems Manager Automation. |
| **Evidence** | `SECURITY.md` (vulnerability policy only, not operational runbook) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file referencing observability assets, no per-service dashboards in the repository, no alarm definitions with named owners, no SLO definitions with team attribution. The Grafana example (`docker/examples/docker-compose-prometheus.yml`) is for learning, not production. |
| **Gap** | No clear ownership of monitoring, alerting, or dashboards. Observability is reactive — metrics are available but nobody is explicitly responsible for watching them. |
| **Recommendation** | Define observability ownership: add CODEOWNERS entries for monitoring configuration, create per-environment dashboards (Grafana or CloudWatch) with team attribution, assign on-call ownership for Zipkin health alarms. |
| **Evidence** | `docker/examples/docker-compose-prometheus.yml` |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no IaC exists. No `default_tags`, no `tags` blocks on resources, no tagging policies, no Config rules for tag enforcement. Docker images use OCI labels (`org.opencontainers.image.description` in Dockerfile) but these are container labels, not AWS resource tags. |
| **Gap** | Zero resource tagging. When infrastructure is created, there will be no cost allocation, ownership tracking, or environment identification. |
| **Recommendation** | When creating IaC (INF-Q10 recommendation), define a mandatory tagging standard from the start: `Environment` (dev/staging/prod), `Service` (zipkin), `Team`, `CostCenter`. Enforce tags via required_tags in Terraform modules or CDK aspects. |
| **Evidence** | `docker/Dockerfile` (OCI labels only) |

---

## Learning Materials

### Move to Managed Databases
- [Move to Managed Databases Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | APP-Q1, DATA-Q3, INF-Q11 | Parent POM with Java 17 compiler settings, Spring Boot 3.5.12, driver version pins |
| `zipkin-server/pom.xml` | APP-Q1, APP-Q2, OPS-Q1 | Server module dependencies: Armeria, Spring Boot, Brave, collectors, storage backends |
| `zipkin-server/src/main/resources/zipkin-server-shared.yml` | INF-Q4, INF-Q5, INF-Q6, INF-Q7, APP-Q3, APP-Q4, APP-Q6, SEC-Q1, SEC-Q3, SEC-Q5, OPS-Q1 | Central configuration: collector settings, storage config, query config, CORS, Eureka, throttle |
| `zipkin-server/src/main/java/zipkin/server/ZipkinServer.java` | APP-Q2 | Spring Boot main class — single deployable entry point |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` | APP-Q2, APP-Q3, APP-Q4, APP-Q5 | HTTP span collector with v1/v2 versioned endpoints and async callback pattern |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` | APP-Q2, APP-Q5, SEC-Q3 | Query API with versioned endpoints, no auth annotations |
| `zipkin/src/main/java/zipkin2/storage/StorageComponent.java` | APP-Q2, DATA-Q2 | Unified storage abstraction — clean interface for all backends |
| `zipkin/src/main/java/zipkin2/storage/SpanStore.java` | DATA-Q2 | Query interface of the unified data access layer |
| `zipkin/src/main/java/zipkin2/storage/SpanConsumer.java` | DATA-Q2 | Write interface of the unified data access layer |
| `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql` | DATA-Q3, DATA-Q4, INF-Q8, INF-Q9 | Cassandra schema with SimpleStrategy replication, TTL settings |
| `zipkin-storage/mysql-v1/src/main/resources/mysql.sql` | DATA-Q4 | MySQL schema — standard SQL, no stored procedures |
| `zipkin-storage/cassandra/pom.xml` | DATA-Q3 | Cassandra java-driver 4.19.2 version pin |
| `zipkin-storage/elasticsearch/pom.xml` | DATA-Q3 | Elasticsearch storage module dependencies |
| `zipkin-storage/mysql-v1/pom.xml` | DATA-Q3 | MariaDB client 3.5.7, jOOQ 3.19.29 version pins |
| `zipkin-storage/elasticsearch/src/main/java/zipkin2/elasticsearch/OpensearchVersion.java` | INF-Q2 | Evidence that OpenSearch is already supported |
| `docker/Dockerfile` | INF-Q1, INF-Q6, SEC-Q6, OPS-Q9 | Multi-stage build, non-root user, health check, OCI labels |
| `docker/examples/docker-compose.yml` | INF-Q1, INF-Q9, INF-Q10 | Default compose — labeled "not for production" |
| `docker/examples/docker-compose-cassandra.yml` | INF-Q2, SEC-Q2, SEC-Q5 | Self-managed Cassandra container, commented plaintext credentials |
| `docker/examples/docker-compose-elasticsearch.yml` | INF-Q2, SEC-Q2 | Self-managed Elasticsearch container |
| `docker/examples/docker-compose-mysql.yml` | INF-Q2, SEC-Q2, SEC-Q5 | Self-managed MySQL container, plaintext credentials (MYSQL_USER=zipkin, MYSQL_PASS=zipkin) |
| `docker/examples/docker-compose-kafka.yml` | INF-Q4 | Self-managed Kafka container |
| `docker/examples/docker-compose-prometheus.yml` | OPS-Q2, OPS-Q4, OPS-Q8 | Example Prometheus/Grafana setup — labeled "not for production" |
| `.github/workflows/test.yml` | INF-Q11, OPS-Q6 | CI with JDK matrix, Docker-based integration test matrix for all backends |
| `.github/workflows/deploy.yml` | INF-Q11, SEC-Q5, OPS-Q5 | Deploy workflow: Maven Central + Docker image push, GitHub secrets usage |
| `.github/workflows/security.yml` | INF-Q11, SEC-Q7 | Trivy vulnerability and secret scanner with HIGH/CRITICAL gate |
| `.github/workflows/docker_push.yml` | INF-Q11, OPS-Q5 | Docker image re-push on tag trigger |
| `.github/workflows/create_release.yml` | INF-Q11 | Maven release workflow |
| `.github/workflows/lint.yml` | INF-Q11 | Markdown and YAML linting |
| `build-bin/` | INF-Q11 | Build automation scripts |
| `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java` | OPS-Q3 | Prometheus metrics configuration with HTTP request timing |
| `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java` | OPS-Q3 | Business metrics: collector messages, spans, bytes, dropped counts |
| `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java` | OPS-Q1 | Self-tracing configuration with Brave |
| `zipkin-server/src/main/java/zipkin2/server/internal/eureka/ZipkinEurekaDiscoveryConfiguration.java` | APP-Q6, SEC-Q4 | Eureka service discovery integration |
| `zipkin-lens/package.json` | APP-Q1 | Frontend: React 16, TypeScript, Vite, Redux |
| `zipkin-collector/kafka/` | INF-Q4, APP-Q3 | Kafka collector module — self-managed broker client |
| `zipkin-collector/rabbitmq/` | INF-Q4, APP-Q3 | RabbitMQ collector module — self-managed broker client |
| `zipkin-collector/activemq/` | INF-Q4 | ActiveMQ collector module — self-managed broker client |
| `zipkin-collector/pulsar/` | INF-Q4 | Pulsar collector module — self-managed broker client |
| `SECURITY.md` | OPS-Q7 | Vulnerability disclosure policy (not operational runbook) |
| `docker/test-images/` | DATA-Q3 | Test images for specific database versions (elasticsearch8, elasticsearch9, opensearch2, etc.) |
