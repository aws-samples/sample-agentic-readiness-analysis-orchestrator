# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | graylog2-server |
| **Date** | 2025-07-25 |
| **TD Version** | 3g1iuew7esd4bia3 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, observability, logging |
| **Context** | Graylog centralized log-management server |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **2.12 / 4.0** |

**Archetype Justification**: graylog2-server owns persistent state in MongoDB (mongodb_uri configured, MongoCollections/MongoConnection referenced in 172+ Java files), exposes CRUD REST endpoints for streams, inputs, dashboards, users, and alerts via Jersey/JAX-RS on port 9000, and manages entity lifecycle with create/update/delete operations. While it has orchestrator-like qualities (message processing pipeline with LMAX Disruptor ring buffers, job scheduler, event processing), the primary architectural pattern is stateful CRUD. Classified as `stateful-crud`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.30 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.12 / 4.0** | **🟠 Needs Work** |

> **Scoring notes**: INF-Q9 is excluded (Not Evaluated — has_deployed_workload=false). INF category = mean of 10 scored questions. OPS category = mean of 9 scored questions. All other questions scored normally.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | Zero infrastructure-as-code — all infrastructure is manually provisioned or undefined in this repository | Blocks reproducible deployments, disaster recovery, and automated environment creation |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Lambda) defined; application runs as a bare Java process with no containerization for production | Prevents elastic scaling, increases operational overhead for patching and capacity planning |
| 3 | INF-Q2: Managed Databases | 1 | MongoDB and OpenSearch are self-managed with localhost connection strings; no managed database services (DocumentDB, Amazon OpenSearch Service) | Manual patching, backup, scaling, and failover management for all data stores |
| 4 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group definitions; no network segmentation or isolation | Services potentially exposed without network-level protection; no blast radius containment |
| 5 | SEC-Q2: Encryption at Rest | 1 | No encryption-at-rest configuration for MongoDB or OpenSearch data stores; no KMS integration | Sensitive log data stored unencrypted; compliance risk for regulated workloads |

---

## Quick Agent Wins

> **Note:** Graylog already has an MCP (Model Context Protocol) server implementation at `org.graylog.mcp` with 13 tools (SearchMessages, ListIndexSets, ListIndices, ListFields, ListInputs, ListStreams, AggregateMessages, SystemInfo, etc.) using the `io.modelcontextprotocol.spec` SDK (v1.1.0). This is a mature AI/agent surface that enables LLM-based agents to interact with Graylog's search and management APIs. The wins below complement this existing capability.

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — `README.markdown`, `CONTRIBUTING.md`, `UPGRADING.md`, `docs/` directory (netflow, cef documentation), `graylog2-web-interface/CLAUDE.md`, `graylog2-web-interface/AGENT.md`, and extensive inline Javadoc.
- **What it enables:** A knowledge agent that indexes Graylog's documentation, upgrade guides, and API documentation to answer developer and operator questions about configuration, troubleshooting, and best practices.
- **Additional steps:** Consolidate scattered documentation into a structured knowledge base. Generate complete OpenAPI specifications from the existing Swagger annotations for full API coverage.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 — MongoDB with centralized data access layer via `MongoCollections`/`MongoConnection` used consistently across modules; well-defined collection schemas via MongoJack annotations.
- **What it enables:** A natural-language-to-MongoDB-query agent that allows operators to query Graylog's configuration and operational data (streams, inputs, users, alerts) without knowing MongoDB query syntax. Complements the existing MCP SearchMessages tool which covers OpenSearch log data.
- **Additional steps:** Document MongoDB collection schemas. Implement query validation and read-only access controls.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3 — OpenTelemetry tracing instrumented (v1.60.1) with javaagent-based instrumentation; Prometheus metrics exporter with custom metric mappings; Dropwizard Metrics throughout the codebase.
- **What it enables:** An agent that queries Prometheus metrics and OpenTelemetry traces to identify performance bottlenecks, correlate processing pipeline slowdowns with specific inputs or streams, and suggest root causes for message processing delays.
- **Additional steps:** Ensure Prometheus exporter is enabled in production configuration. Configure OpenTelemetry exporter endpoint for trace collection.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 — GitHub Actions CI pipeline exists with build, test, and dispatch stages.
- **What it enables:** An agent that monitors CI build status, triggers builds, checks test results, and manages the dispatch workflow to the external `graylog-project-internal` build system.
- **Additional steps:** Expose GitHub Actions API tokens with appropriate scopes. Define agent permissions for workflow triggering.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (modular monolith), INF-Q1=1 (no managed compute) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (no managed compute), no production container definitions |
| 3 | Move to Open Source | Not Triggered | — | — | MongoDB (SSPL) and OpenSearch (Apache 2.0) are already open-source; no commercial database engines detected |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed MongoDB and OpenSearch) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Internal Kafka journal is embedded, not self-managed analytics infrastructure; Kinesis/SQS are input sources, not analytics workloads. No data processing/analytics workloads detected. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (zero IaC), INF-Q11=2 (CI exists, no deployment automation), OPS-Q5=1 (no deployment strategy) |
| 7 | Move to AI | Not Triggered | — | — | Contextual guard: no AI/agent intent detected in portfolio or service context ("Graylog centralized log-management server" contains no AI signal terms). Additionally, MCP server with io.modelcontextprotocol SDK already present (13 tools) — primary trigger also not met. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Graylog is a modular monolith (APP-Q2=2) — a single deployable JAR (`graylog2-server`) bundling REST API, message processing pipeline, scheduler, event processor, and web interface. The `data-node` is a separate deployable but tightly coupled via shared MongoDB. All compute runs as bare Java processes with no managed orchestration (INF-Q1=1).

**Compute Model Gaps:** No ECS, EKS, Lambda, or Fargate definitions exist. The application binds directly to port 9000 with no API Gateway or load balancer (INF-Q6=1). No auto-scaling configuration (INF-Q7=1).

**Communication Pattern Strengths:** The application already has solid async foundations internally — LMAX Disruptor ring buffers for message processing, local Kafka journal for durability, event bus for internal events, and a job scheduler for periodic tasks (APP-Q3=3). These patterns provide a foundation for decomposition.

**Recommended Decomposition Approach:** See Decomposition Strategy section below. The Strangler Fig pattern is recommended given the identifiable module boundaries within the monolith.

**Representative AWS Services:** Amazon EKS (preferred per technology preferences), API Gateway, EventBridge, Step Functions, Amazon DocumentDB (MongoDB-compatible), Amazon OpenSearch Service.

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Hexagonal Architecture.

**Reference:** [AWS Prescriptive Guidance — Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** The application runs as a bare Java process (`java -jar graylog.jar server`). The only Dockerfile exists in test resources (`graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile`) and is used for integration testing only. The `data-node/migration/docker-compose.yml` defines self-managed MongoDB and OpenSearch containers for migration testing but is not a production deployment configuration.

**Container Readiness Indicators:**
- The test Dockerfile already demonstrates a working containerized Graylog setup based on `eclipse-temurin:21-jre-jammy`
- Configuration is externalized via `graylog.conf` and environment variables (e.g., `GRAYLOG_PASSWORD_SECRET`, `GRAYLOG_MONGODB_URI`)
- Port bindings are well-defined (9000 for HTTP, 1514 for Syslog, 12201 for GELF)
- The application supports clustering via `http_publish_uri` and MongoDB replica sets

**Recommended Container Platform:** Amazon EKS (preferred per technology preferences). Avoid self-managed Kubernetes per preferences.

**Migration Approach:** Lift-and-containerize using the existing test Dockerfile as a foundation, then deploy to EKS with Helm charts for configuration management.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS Fargate (for sidecar workloads), AWS App Mesh.

**Reference:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
- **MongoDB** — Self-managed, connection string: `mongodb://localhost/graylog`. Used for configuration, user management, stream definitions, dashboard state, audit logs, and all operational metadata. MongoDB driver v5.6.4, MongoJack v5.1.0. Tested against MongoDB 7.0 and 8.0.
- **OpenSearch** — Self-managed, default `http://127.0.0.1:9200`. Used for log message indexing and search. Docker-compose defines OpenSearch 2.10.0 for testing; CI tests against 2.19.3. Data-node manages OpenSearch 3.5.0.

**Engine Versions and EOL Status:** MongoDB 7.0 EOL is ~2026, MongoDB 8.0 is current. OpenSearch 2.x is current. No immediate EOL risk but self-management burden is high (DATA-Q3=3).

**Data Access Patterns:** Centralized via `MongoCollections`/`MongoConnection` (DATA-Q2=3). No stored procedures (DATA-Q4=4). Clean migration path — all business logic in Java application layer.

**Recommended Managed Database Targets:**
- **MongoDB → Amazon DocumentDB** (MongoDB-compatible) or **Amazon DocumentDB Elastic Clusters** for horizontal scaling. Avoid Oracle per preferences.
- **OpenSearch → Amazon OpenSearch Service** with managed domains, automatic patching, Multi-AZ, and snapshot backups.

**Migration Tools:** AWS Database Migration Service (DMS) for MongoDB to DocumentDB. Amazon OpenSearch Service migration via snapshot/restore or reindexing.

**Representative AWS Services:** Amazon DocumentDB, Amazon OpenSearch Service, Amazon DynamoDB (for specific access patterns per preferences), AWS DMS.

**Reference:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** Zero infrastructure-as-code. No Terraform, CloudFormation, CDK, Helm, or Kustomize files exist in the repository. All infrastructure would need to be provisioned manually or is undefined.

**Current CI/CD State (INF-Q11=2):** GitHub Actions CI pipeline exists with:
- `build.yml`: Build artifacts, frontend tests, backend tests, full-backend-tests (integration tests with Testcontainers)
- `dispatch-main-build.yml`: Dispatches main branch builds to external `graylog-project-internal` repo
- `dispatch-pr-build.yml`: Dispatches PR builds to external repo
- Dependabot configured for Maven and npm dependency updates
- **Gap:** No deployment stage in this repository. Deployment is handled externally with no visibility or automation in this codebase.

**Deployment Strategy Gaps (OPS-Q5=1):** No blue/green, canary, or rolling deployment configuration. No CodeDeploy, Argo Rollouts, or feature flag infrastructure.

**Testing Gaps (OPS-Q6=3):** Integration tests exist via `full-backend-tests` (62 tests against real OpenSearch/MongoDB), which is a strength. Test matrix covers MongoDB 7.0/8.0 and OpenSearch 2.19.3/DataNode.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK (TypeScript or Java) or Terraform for infrastructure provisioning — EKS clusters, DocumentDB, OpenSearch Service, networking, security
- **CI/CD:** Extend GitHub Actions with deployment stages using AWS CodeDeploy or ArgoCD for EKS deployments
- **Deployment Strategy:** Implement blue/green deployments via EKS with Argo Rollouts or AWS CodeDeploy
- **Observability IaC:** Define CloudWatch alarms, dashboards, and Route 53 health checks as code

**Representative AWS Services:** AWS CDK, AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy, Amazon CloudWatch, AWS X-Ray.

**Reference:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

---

## Decomposition Strategy

> **Triggered because APP-Q2 = 2** (modular monolith with identifiable modules but shared database schemas and single deployable unit).

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping it running. New features built as services; existing features migrated over time. | APP-Q2=2 — Graylog has identifiable module boundaries (events, security, inputs, search, streams, scheduler) that can be extracted individually. | **Medium to High** — 6-18 months depending on extraction scope. | ✅ **Recommended.** The well-organized package structure (org.graylog2.rest, org.graylog.events, org.graylog.scheduler, org.graylog.security) provides clear extraction boundaries. |
| **Conditional / Adaptive** | Containerize the monolith as-is first, then selectively extract high-value services. | Limited team capacity; business pressure for quick wins. | **Low to Medium** — Containerization in 2-4 weeks (test Dockerfile exists), selective extraction over 3-12 months. | ✅ **Recommended as first step.** Containerize graylog2-server using the existing test Dockerfile, deploy to EKS, then extract services iteratively. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch. | Almost never appropriate for Graylog — the monolith is functional and well-maintained. | **Very High** — 12-24+ months. | ⚠️ **Not recommended.** The monolith has good internal structure and active development. Strangler Fig is safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's MongoDB data model | Every extraction — place an ACL between the new service and the monolith to translate between models | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions for operations spanning multiple services (e.g., creating a stream with associated rules, alerts, and pipelines) | When extracting modules involved in multi-step business operations | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture state changes as events — Graylog's event system (`org.graylog.events`) already uses event-driven patterns internally | When decomposing the event processing pipeline into independent services | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters | Every new service — ensures testability and infrastructure decoupling | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal | Analysis | Source |
|--------|--------|------------|--------|
| Module boundaries | Clear package structure: events, security, inputs, rest, search, streams, scheduler, plugins | **Low-Medium effort** — identifiable boundaries exist | APP-Q2 |
| Data coupling | Shared MongoDB via `MongoCollections` across 172+ files; single database `graylog` | **High effort** — database decomposition required per service | DATA-Q2 |
| Stored procedures | None — all business logic in Java | **Low effort** — no database-coupled logic to extract | DATA-Q4 |
| Communication patterns | Internal async via Disruptor + Kafka journal; REST for user-facing | **Medium effort** — async foundation exists but needs inter-service adaptation via EventBridge | APP-Q3 |
| CI/CD maturity | CI exists but no deployment automation | **Medium effort** — deployment pipeline must be built alongside decomposition | INF-Q11 |
| Test coverage | 62 integration tests with Testcontainers | **Low-Medium effort** — good test foundation to catch regressions during extraction | OPS-Q6 |

**Calibrated Estimate:** Start with the **Conditional/Adaptive** approach — containerize the monolith (2-4 weeks), deploy to EKS, then apply **Strangler Fig** for selective service extraction over 6-12 months. Priority extraction candidates: inputs/transports (most independent), event processing (already event-driven), and the scheduler (bounded context with clear interfaces).

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute services (ECS, EKS, Lambda, Fargate) are defined anywhere in the repository. No IaC exists. The application is designed to run as a bare Java process (`java -jar graylog.jar server`) binding to port 9000. The only Dockerfile is a test artifact at `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile` used for integration testing with Testcontainers. The `data-node/migration/docker-compose.yml` defines self-managed containers for migration testing only. Configuration (`misc/graylog.conf`) references `127.0.0.1:9000` as the default bind address. |
| **Gap** | All compute is assumed to run on raw EC2 or on-premises with no managed container orchestration or serverless compute. |
| **Recommendation** | Containerize graylog2-server using the existing test Dockerfile as a foundation. Deploy to Amazon EKS (preferred) with Helm charts for configuration management. Define ECS/EKS task definitions or Kubernetes Deployments in IaC. |
| **Evidence** | `misc/graylog.conf` (http_bind_address=127.0.0.1:9000), `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile`, `data-node/migration/docker-compose.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Both MongoDB and OpenSearch are self-managed. MongoDB connection string defaults to `mongodb://localhost/graylog` with no managed service references. OpenSearch nodes in `data-node/migration/docker-compose.yml` use `opensearchproject/opensearch:2.10.0` container images running on self-managed Docker containers. No `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, or OpenSearch Service domain definitions exist (no IaC at all). |
| **Gap** | All databases self-managed — manual patching, backup, scaling, and failover management required. |
| **Recommendation** | Migrate MongoDB to Amazon DocumentDB (MongoDB-compatible) for managed patching, automated backups, and Multi-AZ failover. Migrate OpenSearch to Amazon OpenSearch Service for managed domains with automatic patching and snapshot backups. |
| **Evidence** | `misc/graylog.conf` (mongodb_uri=mongodb://localhost/graylog), `misc/datanode.conf` (mongodb_uri=mongodb://localhost/graylog), `data-node/migration/docker-compose.yml` (opensearchproject/opensearch:2.10.0) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype: stateful-crud.** The application implements its own job scheduler (`org.graylog.scheduler`) with `JobSchedulerService`, `JobExecutionEngine`, `DBJobTriggerService`, and `DBJobDefinitionService` — a custom workflow orchestration engine stored in MongoDB. The scheduler handles event processing, notifications, and periodic maintenance tasks. This is a structured state machine implementation but uses no dedicated workflow orchestration service (Step Functions, Temporal, MWAA). The event processing pipeline (`org.graylog.events`) uses multi-step processing with processors chain. |
| **Gap** | Workflow orchestration is entirely in custom application code. The scheduler is a sophisticated but self-built engine without the visual management, built-in error handling, and retry logic of a dedicated service. |
| **Recommendation** | For new workflow-oriented features, consider AWS Step Functions for multi-step orchestration. The existing scheduler handles periodic jobs well and does not need immediate replacement, but complex event processing chains would benefit from managed orchestration. Prefer EventBridge for event routing per technology preferences. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/scheduler/` (JobSchedulerService.java, JobExecutionEngine.java, DBJobTriggerService.java), `graylog2-server/src/main/java/org/graylog/events/` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Archetype: stateful-crud.** The application uses self-managed messaging infrastructure: (1) Local Kafka journal (`org.graylog2.shared.messageq.localkafka`) with `LocalKafkaMessageQueueWriter`/`Reader`/`Acknowledger` — an embedded Kafka 0.9 (shaded, `kafka09.version=0.9.0.1-7`) for message durability; (2) LMAX Disruptor ring buffers (`disruptor.version=4.0.0`) for high-throughput message processing between input, process, and output buffers; (3) Internal event bus (`ClusterEventBus`, `JobSchedulerEventBus`) for async internal events; (4) AWS Kinesis transport (`org.graylog.integrations.aws.transports.KinesisTransport`) and SQS notifications as input sources using AWS SDK v2. No managed messaging (SQS for internal cross-service flows, EventBridge, MSK) for the application's own state change propagation. |
| **Gap** | Internal messaging relies on self-managed embedded Kafka 0.9 (very outdated) and custom ring buffers. No managed messaging for cross-service state changes. Kafka 0.9 is far beyond end-of-life. |
| **Recommendation** | Replace the embedded Kafka 0.9 journal with Amazon SQS or Amazon MSK Serverless for message durability. Use Amazon EventBridge (preferred) for internal event routing and cross-service state propagation when decomposing the monolith. Avoid self-managed Kafka per technology preferences. |
| **Evidence** | `pom.xml` (kafka09.version=0.9.0.1-7, kafka.version=4.2.0, disruptor.version=4.0.0), `graylog2-server/src/main/java/org/graylog2/shared/messageq/localkafka/`, `graylog2-server/src/main/java/org/graylog2/buffers/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL definitions exist — no IaC is present in the repository. Configuration files reference `127.0.0.1` (localhost) as default bind addresses. The application supports TLS (`http_enable_tls`) and trusted proxy configuration (`trusted_proxies`) but these are application-level, not infrastructure-level network controls. No VPC endpoints, PrivateLink, or VPC Lattice configurations. |
| **Gap** | No network-level security infrastructure defined. Services would potentially be deployed without network segmentation or isolation. |
| **Recommendation** | Define VPC infrastructure in IaC (CDK or Terraform): private subnets for application and database tiers, security groups with least-privilege rules, VPC endpoints for AWS services (S3, DynamoDB, ECR). Place Graylog server in private subnets behind an Application Load Balancer or API Gateway (preferred). |
| **Evidence** | No `.tf`, CloudFormation, CDK, or Helm files found. `misc/graylog.conf` (http_bind_address=127.0.0.1:9000, trusted_proxies commented out) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront defined (no IaC). The Graylog server binds directly to port 9000 via Jersey/Grizzly HTTP server. Configuration supports reverse proxy (`http_external_uri`) but no managed entry point is defined. The web interface and REST API are served from the same port with no separate ingress controller or gateway. |
| **Gap** | Services exposed directly with no gateway or load balancer — no throttling, request validation, or centralized authentication at the entry point. |
| **Recommendation** | Deploy an Amazon API Gateway (preferred) or Application Load Balancer in front of the Graylog server. Configure throttling, request validation, and WAF rules. API Gateway provides additional benefits for future microservice routing as services are extracted from the monolith. |
| **Evidence** | `misc/graylog.conf` (http_bind_address=127.0.0.1:9000, http_external_uri commented out) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists — no IaC defines ASGs, ECS service scaling, EKS HPA, or Lambda concurrency limits. The application's capacity is statically provisioned. Configuration allows tuning of processing buffer sizes (`ring_size=65536`, `inputbuffer_ring_size=65536`) and thread pool sizes, but these are static settings, not dynamic scaling. |
| **Gap** | All capacity statically provisioned. No dynamic scaling for variable log ingestion rates. |
| **Recommendation** | After containerizing and deploying to EKS, implement Horizontal Pod Autoscaler (HPA) based on custom metrics (message processing rate, journal queue depth). Configure auto-scaling for DocumentDB read replicas and OpenSearch Service domain data nodes based on indexing throughput. |
| **Evidence** | `misc/graylog.conf` (ring_size=65536, outputbuffer_processors, processbuffer_processors — all static), no IaC files |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists in the repository — no `aws_backup_plan`, no `backup_retention_period`, no `point_in_time_recovery` settings. MongoDB and OpenSearch are self-managed with no automated backup configuration in IaC. The `message_journal_max_age=12h` and `message_journal_max_size=5gb` settings in `graylog.conf` provide short-term message durability but not backup/recovery. |
| **Gap** | No backup configuration for MongoDB or OpenSearch data stores. No documented restore procedures. |
| **Recommendation** | After migrating to managed databases: enable automated backups on Amazon DocumentDB (default 1-day retention, configurable up to 35 days) with PITR. Enable automated snapshots on Amazon OpenSearch Service domains. Define an AWS Backup plan in IaC for all data stores with defined retention and tested restore procedures. |
| **Evidence** | `misc/graylog.conf` (message_journal_max_age=12h — journal retention, not backup), no IaC files |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. `has_deployed_workload=false` — no production IaC or deployment manifests define compute resources. The test Dockerfile and migration docker-compose are not production deployment artifacts. While `misc/graylog.conf` supports clustering configuration (`http_publish_uri`, MongoDB replica sets, leader election), no production deployment topology is defined in this repository. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No production Dockerfile, no Kubernetes manifests, no Helm charts, no IaC compute definitions |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure-as-code. No Terraform (`.tf`), CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. The only deployment-adjacent files are the test Dockerfile and migration docker-compose. All infrastructure required to run Graylog (compute, networking, databases, monitoring, backups) must be provisioned manually or through external tooling not present in this repository. |
| **Gap** | 100% of infrastructure is manually created (ClickOps) or undefined. No reproducible deployments, no environment consistency, no disaster recovery through IaC. |
| **Recommendation** | Create IaC for all Graylog infrastructure using AWS CDK (Java or TypeScript) or Terraform: EKS cluster, DocumentDB cluster, OpenSearch Service domain, VPC/subnets/security groups, ALB/API Gateway, CloudWatch alarms/dashboards, AWS Backup plans. Start with the compute and networking layer, then add database and operational resources. |
| **Evidence** | `find . -name "*.tf" -o -name "*.tfvars" -o -name "Chart.yaml" -o -name "kustomization.yaml"` returns only the test Dockerfile |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI pipeline exists with build and test automation: `build.yml` runs 4 parallel jobs (build-artifacts, frontend-tests, backend-tests, full-backend-tests) on every PR. Backend tests use `./mvnw -Pedantic clean verify`. Full-backend-tests run against a matrix of OpenSearch/MongoDB versions with Testcontainers. `dispatch-main-build.yml` and `dispatch-pr-build.yml` trigger external builds in `graylog-project-internal` repo. Dependabot is configured for Maven and npm. However, **no deployment stage exists in this repository** — deployment is entirely external and opaque. The `build.yml` `-Dspotbugs.skip` flag in some jobs means SpotBugs SAST is not consistently applied. |
| **Gap** | Build is automated but deployment is entirely external with no visibility. No deployment automation, no rollback stages, no IaC deployment pipeline. |
| **Recommendation** | Extend GitHub Actions (or adopt AWS CodePipeline) with deployment stages: IaC validation (CDK/Terraform plan), container image build and push to ECR, deploy to EKS staging, run smoke tests, promote to production. Add automated rollback on failed health checks. |
| **Evidence** | `.github/workflows/build.yml`, `.github/workflows/dispatch-main-build.yml`, `.github/workflows/dispatch-pr-build.yml`, `.github/dependabot.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 21 (`maven.compiler.release=21`) with a fully modern framework stack: Jersey 4.0.2 (Jakarta namespace, not javax), Jackson 2.21.2, Guice 7.0.0, Jakarta Inject 2.0.1, Jakarta WS RS 4.0.0, Netty 4.2.12.Final, Shiro 2.1.0, Hibernate Validator 9.1.0.Final. AWS SDK v2 (2.42.1) is the primary AWS integration; AWS SDK v1 (1.12.675) remains for some legacy integrations (Kinesis client library). Frontend uses TypeScript/React via `graylog2-web-interface`. OpenTelemetry 1.60.1 for tracing. All dependencies use modern, actively maintained versions. |
| **Gap** | Minor: AWS SDK v1 (1.12.675) still present alongside v2 (2.42.1). SDK v1 is in maintenance mode. |
| **Recommendation** | Complete migration from AWS SDK v1 to v2 for all AWS integrations (Kinesis transport, CloudTrail input, SQS notifications). This is an SDK-level upgrade, not a language change. |
| **Evidence** | `pom.xml` (maven.compiler.release=21, jersey.version=4.0.2, jackson.version=2.21.2, aws-java-sdk-2.version=2.42.1, aws-java-sdk-1.version=1.12.675, opentelemetry.version=1.60.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `graylog2-server` is a modular monolith — a single deployable JAR containing REST API, message processing pipeline, event processor, scheduler, security, search, inputs, streams, dashboards, and the bundled web interface. It has a well-organized package structure with identifiable modules: `org.graylog2.rest`, `org.graylog.events`, `org.graylog.scheduler`, `org.graylog.security`, `org.graylog2.inputs`, `org.graylog2.streams`, `org.graylog.plugins`. The `data-node` is a separate Maven module but shares the same MongoDB (`mongodb://localhost/graylog`). Storage adapters (opensearch2, opensearch3, elasticsearch7) are separate Maven modules but compile into the same JAR. All modules share a single MongoDB database without schema separation. Cross-module dependencies exist via shared Guice bindings and event bus. |
| **Gap** | Tightly-coupled monolith with shared database schemas, single deployable, and cross-module Guice injection. Module boundaries exist but data access is not isolated per module. |
| **Recommendation** | Begin decomposition using the Strangler Fig pattern. Priority extraction candidates: inputs/transports (most independent), event processing (already event-driven), scheduler (bounded context). Each extracted service should own its data in a separate DocumentDB collection or DynamoDB table. See Decomposition Strategy section. |
| **Evidence** | `graylog2-server/pom.xml` (single artifact), `pom.xml` (modules list), `misc/graylog.conf` (single mongodb_uri), package structure at `graylog2-server/src/main/java/org/graylog2/` and `org/graylog/` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: stateful-crud.** The application has strong internal async patterns: LMAX Disruptor ring buffers (`ring_size=65536`) for high-throughput message processing between input, process, and output stages; local Kafka journal for message durability; `ClusterEventBus` and `JobSchedulerEventBus` for internal async events; `async_eventbus_processors` configuration. REST API endpoints are synchronous for user-facing operations (CRUD on streams, inputs, dashboards, users), which is appropriate for stateful-crud archetype. AWS Kinesis transport and SQS notifications use async consumption patterns. |
| **Gap** | No managed async infrastructure for cross-service state propagation. Internal event bus is in-process only, not cross-service. When decomposing, synchronous REST calls between services will need async alternatives for state changes. |
| **Recommendation** | The current async/sync balance is appropriate for the stateful-crud archetype. During decomposition, introduce Amazon EventBridge (preferred) for cross-service event propagation and state change notifications. Keep synchronous REST for user-facing CRUD operations. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/buffers/`, `graylog2-server/src/main/java/org/graylog2/shared/messageq/localkafka/`, `misc/graylog.conf` (ring_size, inputbuffer_ring_size, async_eventbus_processors) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: stateful-crud.** Long-running operations are handled with configurable timeouts and background processing: index optimization uses `elasticsearch_index_optimization_timeout=1h` with a configurable maximum concurrent jobs (`elasticsearch_index_optimization_jobs=10`); the job scheduler (`org.graylog.scheduler.JobSchedulerService`) runs background tasks for event processing, notifications, and system maintenance with configurable concurrency limits (`job_scheduler_concurrency_limits`); search queries have configurable timeouts (`elasticsearch_socket_timeout=60s`). The search query engine uses dedicated thread pools (`search_query_engine_indexer_jobs_pool_size=4`) with configurable queue sizes. |
| **Gap** | Some operations may still block: search operations with large result sets, content pack imports, bulk index operations. No explicit async-with-status-polling pattern for user-initiated long-running operations in the REST API. |
| **Recommendation** | For user-facing operations that may exceed 30 seconds (large searches, bulk exports, index optimization), implement an async job submission with status polling API. The existing scheduler provides the execution infrastructure — add a REST endpoint for job status queries. |
| **Evidence** | `misc/graylog.conf` (elasticsearch_index_optimization_timeout=1h, elasticsearch_socket_timeout=60s, search_query_engine_indexer_jobs_pool_size=4), `graylog2-server/src/main/java/org/graylog/scheduler/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy found. REST endpoints use paths like `/cluster/inputstates`, `/streams/{streamId}/destinations/filters` without version prefixes (`/v1/`, `/v2/`). The OpenAPI spec at `api-specs/stream-output-filters.yml` defines paths without version segments. No `Accept-Version` headers or versioning annotations found. Swagger annotations via `swagger-jaxrs2-jakarta` generate API docs but do not enforce versioning. |
| **Gap** | No versioning — breaking API changes would affect all consumers simultaneously. This is critical for an application that exposes a REST API consumed by external tools, dashboards, and the MCP agent surface. |
| **Recommendation** | Implement URL-path versioning (e.g., `/api/v1/`, `/api/v2/`) for all REST endpoints. Start by prefixing all current endpoints under `/api/v1/`. Future breaking changes create `/api/v2/` while maintaining backward compatibility on `/api/v1/`. This is especially important for the MCP agent tools that depend on stable API contracts. |
| **Evidence** | `api-specs/stream-output-filters.yml` (no version in paths), `graylog2-server/src/main/java/org/graylog2/rest/resources/` (no version prefix in @Path annotations) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables and configuration files: `elasticsearch_hosts` for OpenSearch nodes, `mongodb_uri` for MongoDB, `http_publish_uri` for cluster peer discovery, `datanode_startup_connection_attempts` for data-node connection. Graylog has built-in cluster discovery via `http_publish_uri` and MongoDB for node registration, but this is a custom peer-discovery mechanism, not a standard service registry (Consul, Cloud Map, Istio). Docker-compose uses hostname-based service discovery within the compose network. |
| **Gap** | No dynamic service discovery — all service endpoints are configured via static URIs in configuration files. No service registry, API catalog, or service mesh. |
| **Recommendation** | When deploying to EKS, use Kubernetes native service discovery (DNS-based) for inter-pod communication. For cross-cluster or multi-environment discovery, consider AWS Cloud Map or EKS service mesh (App Mesh). Register Graylog's REST API in an API catalog for discoverability. |
| **Evidence** | `misc/graylog.conf` (elasticsearch_hosts, mongodb_uri, http_publish_uri), `misc/datanode.conf` (mongodb_uri, opensearch_discovery_seed_hosts) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Log messages (the primary unstructured data) are stored in OpenSearch indices — a self-managed search engine, not S3 managed object storage. Content packs are stored in the local `data/contentpacks` directory. GeoIP databases are referenced via `S3GeoIpFileService.java` which can fetch from S3, but this is a specific lookup table — not a general unstructured data storage pattern. The message journal uses local disk storage (`data/journal`). No automated parsing pipeline (Textract, Tika) for document processing. |
| **Gap** | Unstructured data (log messages) stored in self-managed OpenSearch, not S3. No managed parsing pipeline for document/log extraction. |
| **Recommendation** | Migrate log storage to Amazon OpenSearch Service for managed indexing. For long-term log retention and analytics, implement S3-based data lake with Amazon OpenSearch Ingestion for hot/warm/cold tiering. Use S3 Intelligent-Tiering for cost-optimized long-term storage of log data. |
| **Evidence** | `misc/graylog.conf` (elasticsearch_hosts, message_journal_dir=data/journal), `graylog2-server/src/main/java/org/graylog/plugins/map/config/S3GeoIpFileService.java` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | MongoDB access is centralized through `MongoCollections` and `MongoConnection` (`org.graylog2.database` package), which provide a consistent API for collection access, pagination, and query building. MongoJack (v5.1.0) provides ORM-like POJO mapping. The `MongoCollections` singleton is injected via Guice across the codebase. However, direct `MongoConnection` usage exists in 172+ files across `org.graylog2` and `org.graylog` packages, with some modules accessing MongoDB directly rather than through the centralized layer. The `database` package also provides `MongoEntityCollection`, `PaginatedList`, `MongoUtils`, and `ScopedEntityMongoUtils` for standardized data access patterns. |
| **Gap** | Mostly centralized but some direct MongoDB access bypasses the centralized `MongoCollections` API. Not all modules use the same data access patterns consistently. |
| **Recommendation** | Consolidate all MongoDB access through `MongoCollections`. Migrate any remaining direct `MongoConnection` usage to use `MongoEntityCollection` or `MongoUtils`. This will simplify the eventual migration to DocumentDB and support per-service database isolation during decomposition. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/database/MongoCollections.java`, `graylog2-server/src/main/java/org/graylog2/database/MongoConnection.java`, 172+ files referencing MongoCollection/MongoCollections/MongoConnection |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are referenced in CI test configuration: MongoDB 7.0 and 8.0 in `build.yml` test matrix (`mongodb-version: "8.0"`, `mongodb-version: "7.0"`). OpenSearch 2.19.3 in CI (`search-server-version: "2.19.3"`), 2.10.0 in migration docker-compose, and OpenSearch 3.5.0 referenced in data-node (`opensearch.shaded.version=2.19.3-1`, `opensearch.client.version=3.2.0`). MongoDB 7.0 GA was Oct 2023 (EOL ~Oct 2026). MongoDB 8.0 is current. OpenSearch 2.x is current. No explicit version pinning in `graylog.conf` (production version is operator-determined). |
| **Gap** | Versions are tested in CI but not pinned in production configuration — the actual deployed version depends on what operators install. MongoDB 7.0 is approaching EOL within ~12 months. |
| **Recommendation** | Document minimum required and recommended database engine versions. Pin OpenSearch version in data-node configuration. Plan migration testing against MongoDB 8.0 exclusively as MongoDB 7.0 approaches EOL. When migrating to managed services, DocumentDB and OpenSearch Service handle version management automatically. |
| **Evidence** | `.github/workflows/build.yml` (test matrix: mongodb-version 7.0/8.0, search-server-version 2.19.3), `data-node/migration/docker-compose.yml` (opensearch:2.10.0), `pom.xml` (opensearch.shaded.version=2.19.3-1, mongodb-driver.version=5.6.4) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. MongoDB does not use stored procedures. All business logic is implemented in the Java application layer. MongoDB aggregation pipelines, where used, are constructed via the Java driver's fluent API (e.g., `Aggregates.match()`, `Aggregates.group()`), not server-side JavaScript. No `.sql` migration files, no `CREATE PROCEDURE`, no `CREATE TRIGGER`, no `CREATE FUNCTION` statements anywhere in the repository. The application is completely database-engine-agnostic for business logic. |
| **Gap** | None — this is the ideal state. |
| **Recommendation** | Maintain the current pattern of keeping all business logic in the application layer. This significantly simplifies database migration to managed services (DocumentDB, OpenSearch Service). |
| **Evidence** | Search for `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` in repository: zero results. `graylog2-server/src/main/java/org/graylog2/database/` (all Java-based data access) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has comprehensive application-level audit logging via `org.graylog2.audit` package: `AuditEventSender` interface with implementations, `AuditEventTypes` defining audit event categories, `AuditActor` for tracking who performed actions, and `AuditBindings` for Guice wiring. Audit events are generated throughout the codebase for security-relevant operations. However, **no CloudTrail configuration exists** (no IaC). The application-level audit logging is complementary to CloudTrail but does not replace it for AWS API-level audit trails. |
| **Gap** | No CloudTrail configuration for AWS API-level auditing. Application-level audit exists but is not integrated with AWS audit infrastructure. |
| **Recommendation** | Define CloudTrail in IaC with log file validation and immutable S3 storage (S3 Object Lock). Integrate Graylog's application-level audit logs with CloudWatch Logs for centralized audit trail. Enable CloudTrail for all AWS services used in the deployment. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration for any data store. No KMS key definitions (no IaC). MongoDB configuration (`mongodb_uri=mongodb://localhost/graylog`) does not include TLS or encryption parameters. OpenSearch configuration in docker-compose does not enable encryption at rest. The application has `EncryptedValue`/`EncryptedValueService` for encrypting sensitive configuration values (input credentials) using AES with `password_secret` as the key material, but this is application-level encryption for specific fields — not database-level encryption at rest. No S3 bucket encryption, no EBS encryption configured. |
| **Gap** | No encryption at rest for MongoDB or OpenSearch data stores. Log data (potentially containing sensitive information) stored unencrypted. |
| **Recommendation** | When migrating to managed databases: enable encryption at rest on DocumentDB (uses KMS by default), OpenSearch Service (KMS encryption at rest), and any S3 buckets. Define customer-managed KMS keys in IaC for all data stores. Enable MongoDB TLS (`ssl=true` in connection string) for in-transit encryption. |
| **Evidence** | `misc/graylog.conf` (mongodb_uri without TLS), `data-node/migration/docker-compose.yml` (no encryption config), `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java` (app-level encryption only) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | REST endpoints use Apache Shiro (`shiro.version=2.1.0`) for authentication with `@RequiresAuthentication` annotations. JWT support via `jjwt.version=0.13.0` with `JwtSecret`/`JwtSecretProvider` for token generation. Session-based authentication with `AccessTokenService` for API access tokens. LDAP/AD integration via `org.graylog.security.authservice.ldap` with `LDAPAuthServiceBackend`. The `OrderedAuthenticatingRealms` supports multiple authentication backends. Most REST endpoints have `@RequiresAuthentication` or `@RequiresPermissions` annotations. Some internal/health endpoints may not require auth (load balancer status endpoint). |
| **Gap** | Token-based auth on external endpoints via Shiro/JWT but no OAuth2/OIDC built-in. Internal endpoints may lack auth if relying on network isolation. No API Gateway-level authentication. |
| **Recommendation** | Maintain existing Shiro/JWT auth for the application. When deploying behind API Gateway (preferred), add API Gateway authorizers (Lambda or Cognito) as an additional authentication layer. Consider adding OIDC support for modern SSO integration alongside existing LDAP. |
| **Evidence** | `pom.xml` (shiro.version=2.1.0, jjwt.version=0.13.0, unboundid-ldap.version=7.0.4), `graylog2-server/src/main/java/org/graylog2/security/` (JwtSecret.java, AccessTokenService.java), `graylog2-server/src/main/java/org/graylog/security/authservice/ldap/` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | LDAP/Active Directory integration exists via `org.graylog.security.authservice.ldap` with `LDAPAuthServiceBackend`, `LDAPAuthServiceBackendConfig`, `UnboundLDAPConnector`, and `LDAPConnectorConfig`. The `AuthServiceBackend` abstraction supports pluggable authentication backends. `GlobalAuthServiceConfig` manages the active authentication service. The `InternalAuthServiceBackend` provides fallback internal authentication. However, there is no built-in OIDC/SAML/SSO support in this open-source edition — federated identity requires the Graylog Enterprise SSO plugin. |
| **Gap** | LDAP/AD integration exists but no OIDC/SAML/SSO built-in. Some legacy internal auth paths remain as fallback. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management with SSO/OIDC support. Cognito provides SAML and OIDC federation that can supplement or replace LDAP. This enables integration with AWS IAM Identity Center for unified access management. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/security/authservice/ldap/LDAPAuthServiceBackend.java`, `graylog2-server/src/main/java/org/graylog/security/authservice/GlobalAuthServiceConfig.java`, `graylog2-server/src/main/java/org/graylog/security/authservice/InternalAuthServiceBackend.java` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets are managed via configuration files and environment variables — not a dedicated secrets management system. `password_secret` and `root_password_sha2` are defined in `graylog.conf` (empty in sample, expected to be populated at deployment). MongoDB URI supports embedded credentials (`mongodb://grayloguser:secret@localhost:27017/graylog` shown as commented example). The `EncryptedValueService` encrypts sensitive input configuration (API keys, passwords) in MongoDB using AES with `password_secret` as key material. Docker-compose uses environment variable references (`${GRAYLOG_PASSWORD_SECRET:?...}`). No AWS Secrets Manager, HashiCorp Vault, or Parameter Store integration found. No automated secret rotation configured. |
| **Gap** | No plaintext credentials hardcoded in source (Score 2, not Score 1), but production credentials rely on configuration files and environment variables without encryption or rotation. No Secrets Manager integration. |
| **Recommendation** | Integrate AWS Secrets Manager for all sensitive configuration: `password_secret`, MongoDB credentials, OpenSearch credentials, LDAP bind credentials, email transport credentials. Implement automated rotation for database credentials. Replace environment variable references in deployment configs with Secrets Manager ARN references. |
| **Evidence** | `misc/graylog.conf` (password_secret=, root_password_sha2=, commented mongodb_uri with credentials), `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java`, `data-node/migration/docker-compose.yml` (GRAYLOG_PASSWORD_SECRET env var) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-level compute hardening or vulnerability scanning configured (no IaC). No SSM Patch Manager, no AWS Inspector, no hardened AMI references. The test Dockerfile uses `eclipse-temurin:21-jre-jammy` as base image (standard JRE image, not hardened). SpotBugs with FindSecBugs (`findsecbugs-plugin:1.14.0`) provides static security analysis of Java code but this is source-code security, not compute hardening. Dependabot provides dependency update alerts. |
| **Gap** | No evidence of patching strategy, compute hardening, or vulnerability scanning for deployment infrastructure. |
| **Recommendation** | When containerizing: use a hardened base image (Amazon Corretto on Amazon Linux 2023, or Bottlerocket for EKS nodes). Enable Amazon ECR image scanning for container vulnerability detection. Enable AWS Inspector for runtime vulnerability scanning. For EKS, use managed node groups with automatic AMI updates or Fargate for serverless compute (no OS patching needed). |
| **Evidence** | `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile` (FROM eclipse-temurin:21-jre-jammy — not hardened), `graylog-project-parent/pom.xml` (findsecbugs-plugin:1.14.0) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multiple security scanning tools are configured: (1) SpotBugs with FindSecBugs plugin (v1.14.0) and fb-contrib (v7.7.4) in the `-Pedantic` Maven profile — runs SAST on Java code during `check` goal; (2) PMD with custom rules (`config/pmd-rules.xml`) for code quality checks; (3) CycloneDX Maven plugin for SBOM generation; (4) Dependabot configured for Maven and npm with daily checks. However, SpotBugs is skipped in several CI jobs (`-Dspotbugs.skip` in build-artifacts and full-backend-tests), CycloneDX is also skipped (`-Dcyclonedx.skip`). The backend-tests job runs the full `-Pedantic` profile without skipping SpotBugs. No container scanning (no production container). No DAST tool configured. |
| **Gap** | SAST (SpotBugs/FindSecBugs) runs in CI but is skipped in some jobs. No container scanning. No DAST tool. CycloneDX SBOM generation skipped in CI. No security gate blocking on critical findings (`failOnError=false` in SpotBugs config). |
| **Recommendation** | Enable SpotBugs and CycloneDX in all CI jobs (remove `-Dspotbugs.skip` and `-Dcyclonedx.skip`). Set `failOnError=true` for SpotBugs to block builds on critical security findings. Add container scanning when production Dockerfiles are created (ECR image scanning). Consider adding DAST (OWASP ZAP) to the integration test pipeline. |
| **Evidence** | `graylog-project-parent/pom.xml` (spotbugs-maven-plugin with findsecbugs-plugin:1.14.0, maven-pmd-plugin, failOnError=false), `.github/workflows/build.yml` (-Dspotbugs.skip in build-artifacts and full-backend-tests, -Dcyclonedx.skip), `config/pmd-rules.xml`, `config/spotbugs-exclude.xml`, `.github/dependabot.yml` |
### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry tracing is instrumented via `org.graylog.tracing` package: `TracingModule` binds the OpenTelemetry `Tracer` interface via `TracerProvider` which uses `GlobalOpenTelemetry.get().getTracer("org.graylog")`. The OpenTelemetry Java SDK (v1.60.1) and instrumentation annotations (v2.26.1) are dependencies. The `TracerProvider` falls back to a no-op tracer if the OpenTelemetry javaagent is not present, enabling opt-in distributed tracing. `GraylogSemanticAttributes` defines custom semantic attributes for spans. Tracing is primarily within the graylog2-server monolith — cross-service propagation to data-node or external services is not explicitly configured in the codebase (would depend on javaagent configuration). |
| **Gap** | Tracing instrumented on the primary server but cross-service propagation to data-node and OpenSearch is not configured in this codebase. Trace ID propagation headers not explicitly set in HTTP client calls. |
| **Recommendation** | Configure the OpenTelemetry javaagent with proper exporter (AWS X-Ray or OTLP to CloudWatch). Ensure trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`) are included in HTTP client calls to data-node and OpenSearch. Deploy the OpenTelemetry Collector as a sidecar in EKS for trace aggregation. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java`, `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java`, `pom.xml` (opentelemetry.version=1.60.1, opentelemetry-instrumentation.version=2.26.1) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No CloudWatch alarms for p99/p95 latency, no error budget tracking, no SLO definition files. The Prometheus exporter provides infrastructure and processing metrics, but no formal SLO targets are defined for critical user journeys (search latency, message ingestion throughput, API response time). |
| **Gap** | No SLOs — no formal definition of acceptable service levels for search, ingestion, or API responsiveness. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Search latency p99 < 5s for standard queries; (2) Message ingestion throughput — 99.9% of messages processed within 30s of arrival; (3) API response time p99 < 2s for CRUD operations. Implement error budget tracking using CloudWatch Metrics and alarms. |
| **Evidence** | Search for "SLO", "slo", "error_budget", "latency_target" in repository: zero results |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive metrics infrastructure: Prometheus exporter (`PrometheusExporterHTTPServer` on port 9833) with custom metric mappings (`PrometheusMappingConfig`, `MetricMapping`, `InputMetricMapping`). Dropwizard Metrics library (`metrics.version=4.2.38`) used throughout for instrumentation. Metrics cover both infrastructure (JVM, buffer utilization, thread pools) and business-level concerns (input message rates per input type, processing pipeline throughput, journal usage, stream processing times). Custom Prometheus metric mapping files allow operator-defined metric exports. |
| **Gap** | Business metrics exist (message rates, processing times) but are not systematically mapped to business outcomes (e.g., alert detection latency, SLA compliance, data completeness). No dedicated business metric dashboards defined in IaC. |
| **Recommendation** | Define CloudWatch dashboards in IaC for business metrics: message ingestion rates per input source, alert processing latency, search query performance distribution, journal utilization trends. Configure CloudWatch alarms on business-critical thresholds. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/metrics/prometheus/PrometheusExporterHTTPServer.java`, `graylog2-server/src/main/java/org/graylog/metrics/prometheus/mapping/`, `pom.xml` (metrics.version=4.2.38, prometheus-client.version=0.16.0), `misc/graylog.conf` (prometheus_exporter_enabled, prometheus_exporter_bind_address) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured for monitoring the Graylog server itself. No CloudWatch anomaly detection (no IaC), no PagerDuty/OpsGenie integration for the server's own health. While Graylog is itself an alerting and log analysis platform for other systems, no configuration exists for monitoring Graylog's own health, error rates, or latency. The Prometheus exporter provides the metrics but no alerting rules are defined on them. |
| **Gap** | No alerting on Graylog server health — no error rate alarms, no latency monitoring, no journal overflow detection. |
| **Recommendation** | Define CloudWatch alarms in IaC for critical operational metrics: journal utilization > 80%, message processing error rate > 1%, API error rate > 5%, search latency p99 > 10s. Use CloudWatch anomaly detection for message ingestion rate to detect unexpected drops. Integrate with PagerDuty or OpsGenie for incident notification. |
| **Evidence** | No alarm definitions, no monitoring IaC, no PagerDuty/OpsGenie config in repository |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy is defined in this repository. The `dispatch-main-build.yml` and `dispatch-pr-build.yml` workflows trigger external builds in `graylog-project-internal` but no deployment configuration is visible. No blue/green, canary, or rolling deployment configuration. No CodeDeploy appspec, no Argo Rollouts, no Helm release strategy, no feature flag infrastructure. Deployment is entirely opaque from this repository's perspective. |
| **Gap** | Direct-to-production deployment with no staged rollout. No traffic shifting, no automated rollback, no deployment health checks. |
| **Recommendation** | Implement blue/green or canary deployments for EKS using Argo Rollouts or AWS CodeDeploy. Define deployment manifests with health check-based promotion criteria. Use feature flags (AWS AppConfig) for gradual feature rollout independent of deployment. |
| **Evidence** | `.github/workflows/dispatch-main-build.yml` (dispatches to external repo), `.github/workflows/dispatch-pr-build.yml` (dispatches to external repo), no deployment config in repository |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration testing via `full-backend-tests` module: 62 integration test files covering search, views, sessions, aggregations, inputs, streams, events, alerts, and more. Tests use Testcontainers (v2.0.4) to run against real OpenSearch and MongoDB instances. CI test matrix covers MongoDB 7.0/8.0 and OpenSearch 2.19.3/DataNode distributions. Tests are tagged with `@Tag("full-backend-test")` and run in a dedicated CI job. REST-assured (v6.0.0) is used for API testing. Backend unit tests run separately in the `backend-tests` job. |
| **Gap** | Integration tests for primary workflows exist but some coverage gaps — no explicit contract tests for the MCP agent tools, no end-to-end tests for the full message pipeline (input → processing → indexing → search). |
| **Recommendation** | Add contract tests for the MCP agent tool endpoints to ensure API stability for AI/agent consumers. Add end-to-end pipeline tests that validate the full message lifecycle. Consider adding performance benchmarks to the integration test suite. |
| **Evidence** | `full-backend-tests/src/test/java/` (62 test files), `.github/workflows/build.yml` (full-backend-tests job with matrix), `pom.xml` (testcontainers.version=2.0.4, restassured.version=6.0.0) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automation documents, or self-healing patterns found in the repository. No SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No markdown runbooks in `docs/` directory (only protocol documentation for netflow/cef). The `UPGRADING.md` file provides version upgrade guidance but is not an incident response runbook. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No self-healing automation. |
| **Recommendation** | Create operational runbooks for common incidents: (1) Journal full — auto-scale OpenSearch write capacity or increase journal retention; (2) MongoDB connection failures — automatic failover to replica; (3) Message processing backlog — scale processing buffers; (4) Certificate expiry — automated renewal via data-node. Implement as SSM Automation documents or Step Functions. |
| **Evidence** | `docs/` directory (only netflow/cef protocol docs), `UPGRADING.md` (version upgrade guide, not incident runbook) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Minimal observability ownership: `.github/CODEOWNERS` defines ownership only for index mappings (`*Mapping*.java` → `@Graylog2/architecture`) and `Message.java` — no ownership for observability assets (metrics, dashboards, alarms, SLOs). No per-service dashboards defined. No team attribution on alarms or metrics. The Prometheus exporter provides metrics infrastructure but no governance over who owns what metrics or who responds to alerts. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No named owners for dashboards, alarms, or SLOs. |
| **Recommendation** | Extend CODEOWNERS to include observability configuration files. Define per-component dashboards (message processing, search, inputs, scheduler) with named team owners. Tag CloudWatch alarms with owner information. Establish on-call rotation for Graylog operational alerts. |
| **Evidence** | `.github/CODEOWNERS` (only 2 entries: index mappings and Message.java) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging — no IaC resources exist to tag. No `default_tags`, no `tags` blocks, no tagging standards, no `required-tags` Config rules, no Tag Policies. |
| **Gap** | No tagging — no cost allocation, no ownership tracking, no environment identification possible for AWS resources. |
| **Recommendation** | When creating IaC, define a mandatory tagging standard: `Environment` (dev/staging/prod), `Service` (graylog-server/data-node/opensearch), `Team`, `CostCenter`, `ManagedBy` (terraform/cdk). Implement tag enforcement via AWS Config `required-tags` rule and AWS Organizations Tag Policies. Use `default_tags` in Terraform provider or CDK `Tags.of()` for consistent tagging. |
| **Evidence** | No IaC files, no tag configuration |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q4, APP-Q1, APP-Q3, DATA-Q3, SEC-Q3, SEC-Q7, OPS-Q1, OPS-Q3, OPS-Q6 | Root Maven POM with all dependency versions (Java 21, AWS SDK v2 2.42.1, Jersey 4.0.2, Kafka 0.9, OpenTelemetry 1.60.1, etc.) |
| `graylog2-server/pom.xml` | APP-Q2 | Server module POM — single deployable artifact |
| `graylog-project-parent/pom.xml` | SEC-Q7 | Parent POM with SpotBugs/FindSecBugs and PMD plugin configuration (edantic profile) |
| `misc/graylog.conf` | INF-Q1, INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, APP-Q2, APP-Q3, APP-Q4, APP-Q6, DATA-Q1, OPS-Q3 | Primary application configuration — MongoDB URI, OpenSearch hosts, buffer sizes, port bindings, Prometheus exporter settings |
| `misc/datanode.conf` | INF-Q2, APP-Q6 | DataNode configuration — MongoDB URI, OpenSearch settings |
| `.github/workflows/build.yml` | INF-Q11, DATA-Q3, SEC-Q7, OPS-Q6 | CI pipeline — build, test (frontend/backend/full-backend), SpotBugs skip flags, test matrix (MongoDB 7.0/8.0, OpenSearch 2.19.3) |
| `.github/workflows/dispatch-main-build.yml` | INF-Q11, OPS-Q5 | Build dispatch to external graylog-project-internal repo |
| `.github/workflows/dispatch-pr-build.yml` | INF-Q11, OPS-Q5 | PR build dispatch to external repo |
| `.github/dependabot.yml` | INF-Q11, SEC-Q7 | Dependabot config for Maven and npm dependency updates |
| `.github/CODEOWNERS` | OPS-Q8 | Minimal code ownership — index mappings and Message.java only |
| `api-specs/stream-output-filters.yml` | APP-Q5 | OpenAPI 3.1.0 spec without API versioning in paths |
| `data-node/migration/docker-compose.yml` | INF-Q1, INF-Q2, DATA-Q3 | Migration testing compose — MongoDB 7.0, OpenSearch 2.10.0, self-managed containers |
| `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile` | INF-Q1, SEC-Q6 | Test Dockerfile — eclipse-temurin:21-jre-jammy base, port 9000 |
| `graylog2-server/src/main/java/org/graylog/mcp/tools/` | Quick Agent Wins | MCP server tools — 13 agent tools (SearchMessages, ListIndexSets, ListIndices, etc.) |
| `graylog2-server/src/main/java/org/graylog/tracing/` | OPS-Q1 | OpenTelemetry tracing — TracingModule, TracerProvider, GraylogSemanticAttributes |
| `graylog2-server/src/main/java/org/graylog/metrics/prometheus/` | OPS-Q3 | Prometheus exporter — HTTP server, metric mappings, custom metric configuration |
| `graylog2-server/src/main/java/org/graylog2/database/` | DATA-Q2, DATA-Q4 | Centralized MongoDB access — MongoCollections, MongoConnection, MongoEntityCollection |
| `graylog2-server/src/main/java/org/graylog2/audit/` | SEC-Q1 | Application-level audit logging — AuditEventSender, AuditEventTypes, AuditActor |
| `graylog2-server/src/main/java/org/graylog/security/authservice/ldap/` | SEC-Q3, SEC-Q4 | LDAP/AD authentication — LDAPAuthServiceBackend, LDAPConnectorConfig |
| `graylog2-server/src/main/java/org/graylog2/security/encryption/` | SEC-Q2, SEC-Q5 | Application-level encryption — EncryptedValueService, EncryptedValue |
| `graylog2-server/src/main/java/org/graylog2/security/` | SEC-Q3, SEC-Q5 | Security infrastructure — JwtSecret, AccessTokenService, session management |
| `graylog2-server/src/main/java/org/graylog/scheduler/` | INF-Q3, APP-Q4 | Custom job scheduler — JobSchedulerService, JobExecutionEngine, DBJobTriggerService |
| `graylog2-server/src/main/java/org/graylog2/shared/messageq/localkafka/` | INF-Q4, APP-Q3 | Local Kafka journal — embedded Kafka 0.9 for message durability |
| `graylog2-server/src/main/java/org/graylog2/buffers/` | INF-Q4, APP-Q3 | LMAX Disruptor ring buffers — OutputBuffer, buffer processors |
| `graylog2-server/src/main/java/org/graylog/plugins/map/config/S3GeoIpFileService.java` | DATA-Q1 | S3 integration for GeoIP database files |
| `graylog2-server/src/main/java/org/graylog/integrations/aws/` | INF-Q4 | AWS integrations — Kinesis transport, SQS notifications, CloudTrail S3 client |
| `full-backend-tests/src/test/java/` | OPS-Q6 | Integration tests — 62 test files with Testcontainers, REST-assured |
| `config/spotbugs-exclude.xml` | SEC-Q7 | SpotBugs exclusion configuration |
| `config/pmd-rules.xml` | SEC-Q7 | PMD custom rule definitions |
| `misc/security.properties` | SEC-Q3 | JVM security properties — TLS protocol configuration |
| `README.markdown` | Quick Agent Wins | Repository documentation |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
| `graylog2-web-interface/CLAUDE.md` | Quick Agent Wins | AI agent documentation |
| `graylog2-web-interface/AGENT.md` | Quick Agent Wins | Agent configuration documentation |
