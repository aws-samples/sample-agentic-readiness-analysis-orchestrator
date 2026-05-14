# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | graylog2-server |
| **Date** | 2025-07-14 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, observability, logging |
| **Context** | Graylog centralized log-management server. |
| **Overall Score** | 2.15 / 4.0 |

**Archetype Justification**: Graylog is a stateful application that owns persistent state in MongoDB and OpenSearch, exposes CRUD operations on business entities (streams, inputs, users, dashboards, alerts), and processes incoming log events through pipelines before writing to storage. It exhibits hybrid stateful-crud and event-processor characteristics, but the conservative stateful-crud classification is applied as the default since the system's primary user-facing surface is REST API CRUD operations over managed entities.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.36 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.89 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.15 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code — all infrastructure is manually created or defined only in docker-compose for testing | Blocks reproducible deployments, disaster recovery, and environment consistency. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Lambda/Fargate) — application designed for self-hosted deployment on raw VMs | Prevents elastic scaling, increases patching burden, and limits deployment velocity. Triggers Move to Containers and Move to Cloud Native pathways. |
| 3 | INF-Q2: Managed Databases | 1 | MongoDB and OpenSearch are self-managed with localhost connections and no managed service configuration | Operational burden for patching, backup, failover, and scaling. Triggers Move to Managed Databases pathway. |
| 4 | APP-Q5: API Versioning | 1 | No API versioning strategy — REST endpoints have no version prefixes, headers, or backward compatibility guarantees | Breaking changes deployed directly to all consumers; no graceful migration path for API clients. |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or immutable audit logging infrastructure configured | Compliance risk and inability to perform forensic analysis after security incidents in the AWS deployment layer. |

---

## Quick Agent Wins

> **Note:** Graylog already has an MCP (Model Context Protocol) server implementation at `graylog2-server/src/main/java/org/graylog/mcp/` with 13 tools including SearchMessages, ListStreams, ListInputs, AggregateMessages, SystemInfo, ListFields, ListIndexSets, ListIndices, and more. This existing AI/agent infrastructure provides a strong foundation for expanding agent capabilities.

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 — Centralized MongoDB data access layer via `org/graylog2/database/MongoCollections.java`, `PersistedServiceImpl.java`, and dedicated OpenSearch storage modules.
- **What it enables:** A natural-language-to-query agent that translates user questions into MongoDB or OpenSearch queries, enabling non-technical users to explore log data without learning query syntax. The existing MCP `SearchMessagesTool` and `AggregateMessagesTool` already provide this capability partially.
- **Additional steps:** Extend the existing MCP tools with Amazon Bedrock integration to provide natural language understanding. The MCP tool interface is already well-structured for agent consumption.
- **Effort:** Low — MCP tools already exist; adding Bedrock as an LLM layer is incremental.

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 — GitHub Actions CI pipeline exists with build, frontend tests, backend tests, and full-backend-tests matrix.
- **What it enables:** An agent that triggers builds, monitors CI status, reviews test results, and manages pull request workflows via the GitHub Actions API.
- **Additional steps:** Create GitHub Actions workflow dispatch endpoints for agent-triggered operations. Add structured output parsing for test results.
- **Effort:** Medium — pipeline exists but agent integration requires API wrappers.

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — `README.markdown`, `CONTRIBUTING.md`, `docs/netflow/README.md`, `docs/cef/README.md`, extensive Javadoc, and Swagger/OpenAPI annotations across 88+ REST resource files.
- **What it enables:** A RAG-based knowledge agent using existing documentation and code comments as a knowledge base, enabling developers and operators to ask questions about Graylog's architecture, configuration, and API usage.
- **Additional steps:** Index documentation and Swagger-generated API specs into a vector store (e.g., Amazon OpenSearch Service with vector engine). The MCP `ListResourceTool` and `ReadResourceTool` already provide resource discovery.
- **Effort:** Medium — requires documentation indexing and vector store setup, but content corpus already exists.

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3 — OpenTelemetry tracing instrumented via `TracingModule`, `TracerProvider`, and `GraylogSemanticAttributes` with custom semantic attributes for lookups, periodicals, system jobs, and scheduler jobs. Prometheus metrics exporter built-in with configurable metric mappings.
- **What it enables:** An agent that queries traces and metrics to identify performance bottlenecks, correlate log ingestion issues with infrastructure state, and suggest root causes for processing delays.
- **Additional steps:** Connect the observability agent to the Prometheus exporter endpoint and OpenTelemetry trace data. The existing MCP `SystemInfoTool` provides a starting point for system state queries.
- **Effort:** Medium — observability data sources exist; agent needs query interface to Prometheus and trace backends.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (no managed compute), no production container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); MongoDB and OpenSearch are already open-source engines |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed MongoDB and OpenSearch), DATA-Q3=3 |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4=2 (self-managed Kafka journal), data processing workloads confirmed (log analytics pipeline) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), INF-Q11=2 (limited CI/CD), OPS-Q5=2 (no staged deployment), OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context. Note: MCP server already exists in the codebase. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Graylog is a monolithic Java application (APP-Q2=2) with identifiable internal modules (inputs, outputs, streams, search, security, events, scheduler, plugins) but deployed as a single JAR. All modules share a single MongoDB database. The web frontend is bundled into the same deployable unit.

**Compute Model Gaps:** No managed compute infrastructure exists (INF-Q1=1). The application is designed for self-hosted deployment on VMs or bare-metal servers. Docker images exist (`graylog/graylog:5.2.0`) but are not orchestrated through ECS, EKS, or Fargate.

**Communication Pattern Gaps:** Internal message processing uses async patterns (LMAX Disruptor ring buffer, local Kafka journal) effectively (APP-Q3=3), but inter-module communication within the monolith is tightly coupled through shared MongoDB state.

**Recommended Decomposition Approach:** Strangler Fig pattern — incrementally extract high-value modules (e.g., input processing, alerting/events, search API) into independent services while maintaining the monolith for remaining functionality. See **Decomposition Strategy** section below.

**Representative AWS Services:** Amazon EKS (preferred per technology preferences), API Gateway, Amazon EventBridge, AWS Step Functions, AWS Lambda for event-driven processing

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing (for log event pipeline), Hexagonal Architecture

**AWS Prescriptive Guidance:** [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) · [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Graylog is distributed as a self-hosted application with Docker images available for testing/development (`graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile`). The test Dockerfile uses `eclipse-temurin:21-jre-jammy` base image and sets up a proper non-root user with security capabilities. However, there is no production container orchestration (no ECS task definitions, no EKS manifests, no Fargate configuration).

**Container Readiness Indicators:** The application already has Docker image definitions, proper port exposure (9000 for web/API, 1514 for syslog, 12201 for GELF), externalized configuration via environment variables, and JVM tuning options. The `docker-compose.yml` demonstrates multi-service deployment patterns.

**Recommended Container Orchestration:** Amazon EKS (preferred per technology preferences). Avoid self-managed Kubernetes per avoidance preferences.

**Migration Approach:** Lift-and-containerize first — the existing test Dockerfile provides a strong starting point. Then incrementally move to EKS with proper Helm charts, health checks, resource limits, and horizontal pod autoscaling.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS Fargate (for auxiliary services), AWS App Runner

**AWS Guidance:** [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** MongoDB is the primary operational database (`mongodb_uri=mongodb://localhost/graylog`) — self-managed with localhost connection strings. OpenSearch is the search/indexing engine — also self-managed with a 3-node cluster in docker-compose (`opensearchproject/opensearch:2.10.0`). Both require manual patching, backup configuration, and capacity management.

**Engine Versions and EOL:** MongoDB 7.0 and 8.0 tested in CI matrix — both are current and not at EOL. OpenSearch 2.19.3 (shaded library) and 2.10.0 (docker-compose) — current and supported. No immediate EOL risk, but self-management burden remains.

**Data Access Patterns:** Centralized MongoDB access layer in `org/graylog2/database/` (DATA-Q2=3). Dedicated OpenSearch storage modules (`graylog-storage-opensearch2/`, `graylog-storage-opensearch3/`). Clean separation enables targeted migration.

**Recommended Managed Database Targets:**
- **MongoDB → Amazon DocumentDB** (MongoDB-compatible) or **Amazon DynamoDB** (preferred per technology preferences) for metadata/configuration storage
- **OpenSearch → Amazon OpenSearch Service** for log search and analytics indexing

**Representative AWS Services:** Amazon DocumentDB, Amazon DynamoDB, Amazon OpenSearch Service, Amazon MemoryDB

**Migration Tools:** AWS Database Migration Service (DMS) for MongoDB-compatible migration, connection string updates for OpenSearch Service

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Streaming/Messaging Infrastructure:** Graylog uses a local Kafka journal (`LocalKafkaJournal.java`) for internal message buffering between input processing and output writing. The LMAX Disruptor ring buffer provides high-performance in-process message passing. These are self-managed, single-node patterns that do not scale horizontally without manual cluster setup. Avoid self-managed Kafka per technology preferences.

**Data Processing Workloads:** Graylog is fundamentally a log analytics platform. It processes massive data volumes through:
- Input transports (Syslog, GELF, Kinesis, CloudWatch)
- Processing pipelines with rule evaluation
- Output to search indices (OpenSearch/Elasticsearch)
- Alerting and event processing

**Recommended Managed Analytics Targets:**
- **Local Kafka journal → Amazon Kinesis Data Streams** or **Amazon EventBridge** (preferred per technology preferences) for durable message ingestion
- **OpenSearch indexing → Amazon OpenSearch Service** with serverless option for cost-optimized analytics
- **Data pipeline processing → AWS Step Functions** for complex event processing workflows

**Representative AWS Services:** Amazon Kinesis Data Streams, Amazon EventBridge, Amazon OpenSearch Service (Serverless), AWS Glue, Amazon Athena

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** No infrastructure-as-code exists (INF-Q10=1). All infrastructure is manually provisioned or defined only in `data-node/migration/docker-compose.yml` for testing purposes. No Terraform, CloudFormation, CDK, Helm charts, or Kubernetes manifests.

**Current CI/CD State:** GitHub Actions CI pipeline exists (INF-Q11=2) with:
- `build.yml`: Build artifacts, frontend tests, backend tests, full-backend-tests (matrix: OpenSearch 2.19.3/MongoDB 8.0, DataNode/MongoDB 7.0)
- `dispatch-main-build.yml`: Dispatches builds to private `graylog-project-internal` repo for deployment
- Dependabot configured for daily Maven and npm dependency updates
- SpotBugs and PMD configured in Maven but **skipped** in CI (`-Dspotbugs.skip`)
- CycloneDX SBOM generation configured but also skipped in some CI stages (`-Dcyclonedx.skip`)
- No deployment stage visible in the open-source CI pipeline

**Deployment Strategy Gaps:** No canary, blue/green, or rolling deployment configuration (OPS-Q5=2). Deployment is dispatched to an internal repository with no visibility into the deployment strategy.

**Recommended DevOps Toolchain:**
- **IaC:** Terraform or AWS CDK for infrastructure provisioning (EKS clusters, DocumentDB, OpenSearch Service, networking)
- **Container Registry:** Amazon ECR for Docker image management
- **CI/CD:** Extend GitHub Actions with deployment stages, or adopt AWS CodePipeline with CodeBuild
- **Deployment:** Implement canary deployments via EKS with ArgoCD or AWS CodeDeploy
- **Security:** Enable SpotBugs in CI (remove `-Dspotbugs.skip`), add container image scanning via ECR

**Representative AWS Services:** AWS CDK, Amazon ECR, AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy, AWS CloudFormation

---

## Decomposition Strategy

APP-Q2 scored 2 — Graylog is a monolith with identifiable modules but shared database schemas and cross-module coupling through MongoDB. This section provides decomposition guidance.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Graylog's identifiable module boundaries (inputs, outputs, streams, search, security, events, scheduler) make incremental extraction feasible. Team can sustain parallel development. | **Medium to High** — 6-18 months depending on extraction scope. | ✅ **Recommended.** Lowest risk. Extract input processing and alerting/events as first services. |
| **Conditional / Adaptive** | Start by containerizing the Graylog monolith on EKS as-is, then selectively extract high-value modules (e.g., input processing for independent scaling). | **Low to Medium** — Containerization in 2-4 weeks (Dockerfile exists), selective extraction over 3-12 months. | ✅ **Recommended when capacity is constrained.** Quick win: containerize first, decompose later. |
| **Big-Bang Rewrite** | Not recommended for Graylog. The application is functional and has identifiable modules — incremental extraction is viable. | **Very High** — 12-24+ months. | ⚠️ **Recommended against.** Graylog is a mature, functioning product. Strangler Fig or Conditional approaches are far safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's MongoDB data model. | Every extraction — place an ACL between the new service and the monolith's shared MongoDB collections. | [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions when extracting modules that participate in multi-step operations (e.g., stream processing → indexing → alerting). | When extracting the alerting/events module, which currently shares transactional boundaries with stream processing. | [Saga Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture log ingestion events as an immutable event stream. Enables replay, audit trails, and decoupled consumers. | When extracting the input processing pipeline — log events are naturally an event-sourced domain. Amazon EventBridge or Kinesis as the event backbone. | [Event Sourcing Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear boundaries between business logic, external interfaces, and infrastructure adapters. | Every new service extracted from the monolith — ensures testability and portability. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Current State | Effort Impact |
|--------|---------------|---------------|
| Module boundaries | Identifiable packages (`inputs/`, `outputs/`, `streams/`, `search/`, `security/`, `events/`, `scheduler/`, `plugins/`) but cross-package imports exist | Medium — boundaries exist but need hardening |
| Data coupling | Single shared MongoDB database (`mongodb://localhost/graylog`) with all modules writing to the same database | High — database per service requires data migration and API boundaries |
| Stored procedures | None (DATA-Q4=4) — all business logic in Java application layer | Low — no database logic extraction needed |
| Communication patterns | Internal async via LMAX Disruptor and local Kafka journal; REST API is synchronous | Medium — async infrastructure exists but is in-process, not distributed |
| CI/CD maturity | CI exists (GitHub Actions) but deployment automation is limited and dispatched to internal repo | Medium — pipeline needs extension for multi-service deployment |
| Test coverage | 62 integration test files in `full-backend-tests/`, matrix testing against multiple DB versions | Low-Medium — integration tests provide regression safety during extraction |

**Calibrated Effort Estimate:** For the Strangler Fig approach, expect **12-18 months** for the first 2-3 service extractions (input processing, alerting/events, search API), with the monolith remaining for core configuration and user management. For the Conditional approach, expect **2-4 weeks** for containerization on EKS and **6-12 months** for selective extraction of 1-2 high-value modules.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure (ECS, EKS, Lambda, Fargate) is defined anywhere in the repository. Graylog is designed as a self-hosted application deployed on VMs or bare-metal. A test Dockerfile exists at `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile` using `eclipse-temurin:21-jre-jammy`, and a migration `docker-compose.yml` references `graylog/graylog:5.2.0` images, but neither defines managed container orchestration. |
| **Gap** | All compute is on raw EC2/VMs with no managed services. No IaC for compute resources exists. |
| **Recommendation** | Containerize the application using the existing test Dockerfile as a base and deploy to Amazon EKS (preferred). Create Helm charts for Graylog server, data-node, and supporting services. |
| **Evidence** | `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile`, `data-node/migration/docker-compose.yml`, `misc/graylog.conf` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | MongoDB is configured with `mongodb_uri=mongodb://localhost/graylog` — a self-managed localhost instance. OpenSearch is self-managed with a 3-node cluster in `docker-compose.yml` (`opensearchproject/opensearch:2.10.0`). No RDS, DynamoDB, DocumentDB, or managed OpenSearch Service definitions exist. |
| **Gap** | All databases are self-managed with no automated failover, managed patching, or cloud-native backup. |
| **Recommendation** | Migrate MongoDB to Amazon DocumentDB (MongoDB-compatible) or Amazon DynamoDB for metadata. Migrate OpenSearch to Amazon OpenSearch Service. Both provide automated backups, patching, and Multi-AZ failover. |
| **Evidence** | `misc/graylog.conf` (mongodb_uri), `data-node/migration/docker-compose.yml` (opensearch images) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated workflow orchestration service (Step Functions, Temporal, MWAA). The application has an internal job scheduler (`org/graylog/scheduler/`) with `JobSchedulerService`, `JobExecutionEngine`, configurable concurrency limits, and trigger management. Periodical tasks are managed through `org/graylog2/periodical/` (22 periodical classes including `IndexRotationThread`, `IndexRetentionThread`, `ClusterHealthCheckThread`). This is a structured in-code scheduler but not a dedicated orchestration service. Archetype: stateful-crud — some workflow orchestration is expected. |
| **Gap** | Workflow orchestration is implemented as custom in-code schedulers. No dedicated orchestration service provides visual management, error handling, or retry logic. |
| **Recommendation** | Evaluate AWS Step Functions for complex multi-step operations (e.g., index rotation → optimization → retention) and Amazon EventBridge Scheduler for periodic tasks. The existing `JobSchedulerService` interface could be adapted to delegate to Step Functions. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/scheduler/`, `graylog2-server/src/main/java/org/graylog2/periodical/` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Graylog uses a local Kafka journal (`LocalKafkaJournal.java`) for internal message buffering between input and output processing. The LMAX Disruptor ring buffer (`ring_size=65536`, `inputbuffer_ring_size=65536`) provides high-performance in-process message passing. Kinesis transport (`KinesisTransport.java`) provides AWS log ingestion. AMQP client (`amqp-client.version=5.29.0`) for RabbitMQ input. However, all messaging is self-managed and in-process — no managed messaging services (SQS, SNS, EventBridge, MSK) are configured. Archetype: stateful-crud — managed messaging expected for cross-service state changes. |
| **Gap** | Self-managed messaging (local Kafka journal, in-process Disruptor) for all internal communication. No managed messaging for cross-service state propagation or event distribution. |
| **Recommendation** | Replace local Kafka journal with Amazon Kinesis Data Streams or Amazon EventBridge (preferred) for durable, horizontally-scalable message ingestion. Use Amazon SQS for decoupled processing stages. Avoid self-managed Kafka per technology preferences. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/shared/journal/LocalKafkaJournal.java`, `graylog2-server/src/main/java/org/graylog2/shared/messageq/`, `misc/graylog.conf` (ring_size, inputbuffer_ring_size), `pom.xml` (kafka.version=4.2.0, disruptor.version=4.0.0) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security group, NACL, or network segmentation configuration exists in the repository. The application binds to `127.0.0.1:9000` by default (`misc/graylog.conf`). TLS is available but not enforced (`http_enable_tls = true` is commented out). The docker-compose exposes ports directly (9000, 1514, 12201, 9200). No network isolation between Graylog, MongoDB, and OpenSearch. |
| **Gap** | No infrastructure-level network security. Services deployed without VPC isolation, private subnets, or security groups. |
| **Recommendation** | Define VPC infrastructure with private subnets for databases (DocumentDB, OpenSearch Service), public subnets only for load balancer/API Gateway entry points. Implement least-privilege security groups. Use VPC endpoints for AWS service access. |
| **Evidence** | `misc/graylog.conf` (http_bind_address), `data-node/migration/docker-compose.yml` (exposed ports) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or load balancer defined. The Graylog HTTP interface is served directly by an embedded web server (Jersey/Grizzly) on port 9000. The `lb_recognition_period_seconds=3` setting in `graylog.conf` suggests load balancer awareness, but no actual LB infrastructure is defined. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, centralized auth, or request validation at the entry point. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) in front of Graylog's REST API for throttling, authentication, request validation, and WAF protection. Use ALB for the web interface with health checks and SSL termination. |
| **Evidence** | `misc/graylog.conf` (http_bind_address, lb_recognition_period_seconds), `graylog2-server/src/main/java/org/graylog2/rest/resources/HelloWorldResource.java` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. Capacity is statically provisioned through configuration parameters: `ring_size=65536`, `inputbuffer_ring_size=65536`, `processbuffer_processors` (auto-calculated from CPU cores), `outputbuffer_processors` (auto-calculated), `mongodb_max_connections=1000`. No ASG, ECS auto-scaling, or Lambda concurrency configuration. |
| **Gap** | All capacity is statically provisioned. No ability to dynamically scale based on log ingestion volume or query load. |
| **Recommendation** | On EKS (preferred), implement Horizontal Pod Autoscaler (HPA) based on custom metrics (journal utilization, processing lag). Configure cluster autoscaler for node-level scaling. For OpenSearch Service, enable auto-scaling for data nodes. |
| **Evidence** | `misc/graylog.conf` (ring_size, processbuffer_processors, outputbuffer_processors, mongodb_max_connections) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning, no PITR configuration. MongoDB and OpenSearch backup strategies are not defined in any configuration or IaC. The `message_journal_max_age=12h` and `message_journal_max_size=5gb` settings provide short-term message durability but not data backup. |
| **Gap** | No backup configuration for any data store. A data loss event could result in complete loss of configuration, user accounts, dashboards, and indexed log data. |
| **Recommendation** | With managed databases: DocumentDB provides automated continuous backups with PITR; OpenSearch Service provides automated snapshots. Implement AWS Backup plans for cross-service backup coordination. |
| **Evidence** | `misc/graylog.conf` (message_journal_max_age, message_journal_max_size) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application supports clustering: `is_leader=true` setting indicates leader election, `http_publish_uri` enables cluster node discovery, and the docker-compose demonstrates a 3-node OpenSearch cluster with 3 DataNode instances. However, no IaC defines multi-AZ deployment. The HA capability exists in the application architecture but not in infrastructure configuration. |
| **Gap** | Application supports clustering but no multi-AZ infrastructure is configured. Single-AZ failure would take down the entire workload. |
| **Recommendation** | On EKS, spread pods across multiple AZs using pod topology spread constraints. Use DocumentDB and OpenSearch Service with Multi-AZ configuration for database HA. |
| **Evidence** | `misc/graylog.conf` (is_leader, http_publish_uri), `data-node/migration/docker-compose.yml` (3-node OpenSearch, 3 DataNodes) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files found. No Terraform (`.tf`), CloudFormation, CDK (`cdk.json`), Helm charts (`Chart.yaml`), or Kubernetes manifests. The only infrastructure definition is `data-node/migration/docker-compose.yml` for migration testing — not production infrastructure. |
| **Gap** | No IaC — all infrastructure is created manually (ClickOps) or via ad-hoc scripts. Infrastructure changes are non-reproducible and error-prone. |
| **Recommendation** | Create IaC using Terraform or AWS CDK for all infrastructure: EKS cluster, DocumentDB, OpenSearch Service, VPC/networking, IAM roles, monitoring. Start with CDK (Java support aligns with team skills). |
| **Evidence** | Repository root directory listing, `find` search for `.tf`, `Chart.yaml`, `kustomization.yaml`, `cdk.json` — all returned empty results. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI pipeline exists with 4 jobs in `build.yml`: (1) Build artifacts — compiles and generates Javadoc, (2) Frontend tests — runs web interface tests, (3) Backend tests — unit tests excluding full-backend-tests, (4) Full-backend-tests — integration tests against OpenSearch 2.19.3/MongoDB 8.0 and DataNode/MongoDB 7.0. Additionally, `dispatch-main-build.yml` dispatches builds to `graylog-project-internal` for deployment. Dependabot configured for daily dependency scanning. However, no deployment stage is visible in the open-source pipeline — deployment is fully delegated to an internal repository. SpotBugs is skipped in all CI stages (`-Dspotbugs.skip`). |
| **Gap** | Build is automated but deployment is not visible/automated in this repository. No deployment pipeline stages, no automated rollback, no staged environment promotion. |
| **Recommendation** | Extend CI/CD with deployment stages: build → test → staging deployment → integration tests → production canary. Use AWS CodeDeploy for EKS deployments with automated rollback on health check failures. |
| **Evidence** | `.github/workflows/build.yml`, `.github/workflows/dispatch-main-build.yml`, `.github/dependabot.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 21 is the primary language (~6,019 Java files) with first-class AWS SDK coverage (AWS SDK v2 `2.42.1`), mature cloud-native tooling (Spring ecosystem compatibility, gRPC `1.80.0`, OpenTelemetry `1.60.1`), and extensive framework support. TypeScript/JavaScript (~3,568 files) powers the React frontend with modern tooling (webpack, Jest, ESLint). Both are Tier 1 languages for AWS cloud-native development. |
| **Gap** | None — language choices are optimal for cloud-native development. |
| **Recommendation** | No change needed. Continue leveraging Java 21's modern features (virtual threads, pattern matching) and AWS SDK v2 for cloud service integration. |
| **Evidence** | `pom.xml` (maven.compiler.release=21), `graylog2-web-interface/package.json`, `pom.xml` (aws-java-sdk-2.version=2.42.1) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Graylog is a monolithic server application deployed as a single JAR. The codebase has identifiable modules: inputs (`org/graylog2/inputs/`), outputs (`org/graylog2/outputs/`), streams (`org/graylog2/rest/resources/streams/`), search (`org/graylog2/rest/resources/search/`), security (`org/graylog/security/`), events/alerting, scheduler (`org/graylog/scheduler/`), and plugins. The data-node is a separately deployable component. However, all modules share a single MongoDB database, the web frontend is bundled into the server JAR, and cross-module dependencies exist through shared service injection (Guice). Storage is abstracted through plugins (`graylog-storage-opensearch2/3/elasticsearch7`). |
| **Gap** | Monolith with identifiable modules but shared database schemas, direct cross-module data access through shared MongoDB, and a single deployable unit. |
| **Recommendation** | Apply Strangler Fig pattern to incrementally extract high-value services. See Decomposition Strategy section. Prioritize input processing and alerting/events as first extraction candidates. |
| **Evidence** | `pom.xml` (module list), `graylog2-server/src/main/java/org/graylog2/rest/resources/` (REST resource directories), `misc/graylog.conf` (single mongodb_uri for all modules) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Graylog has a strong internal async architecture. The LMAX Disruptor ring buffer handles high-throughput log message processing asynchronously. The local Kafka journal (`LocalKafkaJournal.java`) provides durable async message queuing between input and output stages. Kinesis transport provides async AWS log ingestion. The internal event bus (`async_eventbus_processors=2`) enables async inter-module communication. REST API endpoints are synchronous (Jersey/JAX-RS). The mix of async for core processing and sync for API operations is appropriate for a stateful-crud archetype. |
| **Gap** | Cross-service state propagation is not yet using managed async messaging. Internal async is strong but bound to the in-process monolith. |
| **Recommendation** | When decomposing, externalize the internal async patterns to managed services: Amazon EventBridge for event distribution, Amazon SQS for decoupled processing queues. The existing async architecture provides a strong design foundation. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/shared/journal/LocalKafkaJournal.java`, `graylog2-server/src/main/java/org/graylog2/buffers/`, `misc/graylog.conf` (async_eventbus_processors, processor_wait_strategy=blocking) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Long-running operations are handled through the job scheduler (`JobSchedulerService`) with configurable concurrency limits (`job_scheduler_concurrency_limits`), system job threads (`job_scheduler_system_worker_threads=5`), and the periodical system (22 periodical tasks). Index optimization has configurable timeouts (`elasticsearch_index_optimization_timeout=1h`). Index rotation and retention are handled as background periodical tasks. Search query execution uses configurable thread pools (`search_query_engine_indexer_jobs_pool_size=4`). |
| **Gap** | Most long-running operations are handled asynchronously, but some blocking calls may remain (e.g., cluster proxied requests with `proxied_requests_default_call_timeout=5s`). |
| **Recommendation** | Evaluate remaining synchronous operations for async conversion. Consider AWS Step Functions for multi-step operations like index lifecycle management (rotation → optimization → retention → deletion). |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/scheduler/JobSchedulerService.java`, `graylog2-server/src/main/java/org/graylog2/periodical/`, `misc/graylog.conf` (job_scheduler_concurrency_limits, elasticsearch_index_optimization_timeout) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy found. REST endpoints use unversioned paths: `@Path("/")` (HelloWorldResource), `/cluster/`, `/system/`, `/streams/`, `/users/`, `/roles/`, `/search/`, `/messages/`. No `/v1/` or `/v2/` URL patterns, no `Accept-Version` headers, no versioning annotations. Swagger v3 annotations (`swagger.version=2.2.45`) are used extensively across 88+ REST resource files for documentation, but without versioning. An OpenAPI spec exists at `api-specs/stream-output-filters.yml` with `version: "1.0.0"` but this is a spec version, not an API path version. |
| **Gap** | No API versioning — breaking changes are deployed directly to all consumers with no migration path. |
| **Recommendation** | Implement URL-path versioning (e.g., `/api/v1/streams/`) starting with the current API surface as v1. Use API Gateway (preferred) for version routing and gradual migration. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/rest/resources/` (all @Path annotations), `api-specs/stream-output-filters.yml` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Graylog has a built-in cluster node discovery mechanism using `http_publish_uri` — nodes advertise their HTTP URI for cluster discovery. Elasticsearch/OpenSearch hosts are configured via environment variables or config (`elasticsearch_hosts`). MongoDB connection uses a URI string (`mongodb_uri`). No service mesh (Istio, Consul), no AWS Service Discovery, and no dynamic service registry. Discovery relies on configuration strings rather than dynamic resolution. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. Endpoint changes require configuration updates and restarts. |
| **Recommendation** | On EKS, leverage Kubernetes native service discovery (DNS-based). For cross-cluster communication, use AWS Cloud Map or VPC Lattice. API Gateway can serve as a centralized service catalog. |
| **Evidence** | `misc/graylog.conf` (http_publish_uri, elasticsearch_hosts, mongodb_uri) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Log messages (unstructured data) are stored in OpenSearch/Elasticsearch indices — managed storage but not S3. The message journal is stored locally on disk (`data/journal` with configurable `message_journal_max_age=12h`, `message_journal_max_size=5gb`). AWS S3 integration exists for GeoIP file downloads (`S3GeoIpFileService.java`) and the AWS SDK S3 module is in dependencies, but S3 is not used for general-purpose unstructured data storage. No automated parsing pipeline (Textract, Tika) for document processing. |
| **Gap** | Data in managed storage (OpenSearch) but not S3. No automated parsing pipeline for unstructured content. Local journal storage limits durability and portability. |
| **Recommendation** | Use S3 as a data lake tier for long-term log archival (S3 Intelligent-Tiering). Implement S3 lifecycle policies for cost-optimized storage. Consider Amazon S3 File Gateway if filesystem access patterns are needed during migration. |
| **Evidence** | `misc/graylog.conf` (message_journal_dir, message_journal_max_age), `graylog2-server/src/main/java/org/graylog/plugins/map/config/S3GeoIpFileService.java`, `pom.xml` (aws-java-sdk-2 with S3 module) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | MongoDB access is centralized through `org/graylog2/database/` with `MongoCollections.java`, `MongoEntityCollection.java`, `PersistedServiceImpl.java`, `MongoPaginationHelper` (in pagination/), and `MongoConnection.java`. OpenSearch access is abstracted through dedicated storage modules: `graylog-storage-opensearch2/`, `graylog-storage-opensearch3/`, `graylog-storage-elasticsearch7/` — each providing a pluggable storage backend. MongoJack (`mongojack.version=5.1.0`) provides type-safe MongoDB operations. |
| **Gap** | Mostly centralized with clean abstraction. Some direct MongoDB access may exist in auxiliary code paths outside the central database package. The storage plugin architecture is well-designed for future migration. |
| **Recommendation** | Maintain the centralized data access pattern during migration. The storage plugin architecture makes it straightforward to add an Amazon OpenSearch Service adapter alongside the existing self-managed adapters. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/database/` (MongoCollections.java, PersistedServiceImpl.java, MongoConnection.java), `graylog-storage-opensearch2/`, `graylog-storage-opensearch3/`, `graylog-storage-elasticsearch7/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are explicitly specified: MongoDB 7.0 and 8.0 in CI test matrix (`.github/workflows/build.yml`), MongoDB driver `5.6.4` in `pom.xml`, OpenSearch shaded version `2.19.3-1` in `pom.xml`, OpenSearch `2.10.0` in `docker-compose.yml`. Neither MongoDB 7.0/8.0 nor OpenSearch 2.x are at EOL. MongoDB 7.0 reaches EOL in Aug 2026 — approaching within 12 months. |
| **Gap** | Versions pinned but MongoDB 7.0 approaching EOL within 12 months. No documented version-update procedure exists in the repository. |
| **Recommendation** | Document a database version-update procedure covering testing, downtime windows, and rollback. With managed services (DocumentDB, OpenSearch Service), engine version upgrades are automated and can be scheduled. |
| **Evidence** | `.github/workflows/build.yml` (matrix: mongodb-version 7.0, 8.0; search-server-version 2.19.3), `pom.xml` (mongodb-driver.version=5.6.4, opensearch.shaded.version=2.19.3-1), `data-node/migration/docker-compose.yml` (mongo:7.0, opensearch:2.10.0) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. Graylog uses MongoDB (document database — no stored procedure concept) and OpenSearch (search engine — no stored procedures). All business logic resides in the Java application layer. Database operations are expressed through the MongoDB driver and OpenSearch client APIs. No `.sql` files found in the repository. No ORM bypass patterns or raw SQL execution. |
| **Gap** | None — all business logic is in the application layer. No database-coupled logic to extract during migration. |
| **Recommendation** | No change needed. This clean separation significantly reduces migration effort for moving to managed databases. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/database/` (all operations via MongoDB driver), absence of `.sql` files in repository |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or immutable audit log storage configured. Graylog has an internal audit event system (`org/graylog2/audit/` with `AuditEventSender`, `AuditEventType`, `AuditEventTypes`, `AuditBindings`) that captures application-level audit events. However, this is application audit logging, not infrastructure-level CloudTrail logging. No S3 bucket with Object Lock for immutable log storage. |
| **Gap** | No CloudTrail or equivalent infrastructure audit logging. Application-level audit events exist but are not stored immutably. |
| **Recommendation** | Enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Graylog's own audit event system should feed into the centralized CloudTrail-based audit trail. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/audit/` (AuditEventSender.java, AuditEventTypes.java) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS configuration, no encryption-at-rest settings in IaC (no IaC exists). TLS for HTTP transport is configurable but disabled by default (`http_enable_tls` commented out). TLS for Elasticsearch connections is demonstrated in docker-compose with certificate volumes. The application uses BouncyCastle (`bouncycastle.version=1.83`) and AES tools (`AESTools.java`) for application-level encryption of sensitive values (access tokens, encrypted values). But no infrastructure-level encryption at rest is configured. |
| **Gap** | No infrastructure-level encryption at rest. MongoDB and OpenSearch data is not encrypted at rest in any configuration. |
| **Recommendation** | With managed services: DocumentDB and OpenSearch Service provide encryption at rest with AWS-managed or customer-managed KMS keys by default. Enable customer-managed KMS keys for all data stores. |
| **Evidence** | `misc/graylog.conf` (http_enable_tls commented out), `data-node/migration/docker-compose.yml` (TLS certificate volumes), `graylog2-server/src/main/java/org/graylog2/security/AESTools.java` |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive authentication system: Apache Shiro (`shiro.version=2.1.0`) provides the security framework. `@RequiresAuthentication` and `@RequiresPermissions` annotations are used across 179 Java files. JWT support exists (`jjwt.version=0.13.0` with `JwtSecret.java`, `JwtSecretProvider.java`). Access tokens are managed through `AccessTokenService`. Session-based auth with token support. All external API endpoints require authentication through the Shiro filter chain. |
| **Gap** | Token-based auth on all external endpoints, but internal endpoint auth relies on network isolation assumptions. No API Gateway-level throttling or request validation. |
| **Recommendation** | Add Amazon API Gateway (preferred) in front of the REST API for additional throttling, WAF protection, and request validation. The existing Shiro authentication is solid for application-level auth. |
| **Evidence** | `pom.xml` (shiro.version=2.1.0, jjwt.version=0.13.0), 179 files with `@RequiresAuthentication`/`@RequiresPermissions`, `graylog2-server/src/main/java/org/graylog2/security/` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | LDAP and Active Directory integration via `org/graylog/security/authservice/ldap/` with `LDAPAuthServiceBackend`, `ADAuthServiceBackend`, and configurable LDAP connection settings (`ldap_connection_timeout`). HTTP header-based authentication (`org/graylog2/security/headerauth/`) for SSO proxy integration. Multiple auth service backends supported through `AuthServiceBackend` interface. Global auth service configuration (`GlobalAuthServiceConfig`). |
| **Gap** | Application uses centralized IdP for most flows through LDAP/AD integration. Some legacy auth paths remain (internal username/password with `root_password_sha2`). No native OIDC/SAML support visible in the open-source codebase (may be in enterprise edition). |
| **Recommendation** | Ensure OIDC/SAML integration with Amazon Cognito or enterprise IdP for full SSO. The existing multi-backend auth service architecture supports this extension. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/security/authservice/ldap/`, `graylog2-server/src/main/java/org/graylog/security/authservice/backend/`, `misc/graylog.conf` (ldap_connection_timeout) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets are managed through configuration files and environment variables. `misc/graylog.conf` contains `password_secret=` and `root_password_sha2=` as empty placeholders. The docker-compose uses `${GRAYLOG_PASSWORD_SECRET:?Please configure}` with required validation. The `AccessTokenCipher` encrypts tokens using `password_secret` as the encryption key. MongoDB credentials are embedded in connection strings. No AWS Secrets Manager, HashiCorp Vault, or parameter store integration detected. |
| **Gap** | Production credentials in config files or environment variables. No dedicated secrets management system. No automated rotation. |
| **Recommendation** | Integrate AWS Secrets Manager for all credentials (MongoDB/DocumentDB URIs, API keys, password_secret). Implement automated rotation for database credentials. Reference secrets via environment variables sourced from Secrets Manager at container startup. |
| **Evidence** | `misc/graylog.conf` (password_secret, root_password_sha2, mongodb_uri), `data-node/migration/docker-compose.yml` (GRAYLOG_PASSWORD_SECRET env var) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependabot is configured for daily dependency vulnerability scanning across Maven and npm ecosystems (`.github/dependabot.yml`). The pom.xml explicitly manages vulnerable transitive dependencies (e.g., `commons-compress` for CVE-2023-42503, `avro` for CVE-2023-39410, `json-smart` for CVE-2024-57699, `lz4-java` for CVE-2025-12183, `mina-core` for CVE-2024-52046). The test Dockerfile uses `eclipse-temurin:21-jre-jammy` (official JDK image). No SSM Patch Manager, AWS Inspector, or systematic vulnerability scanning beyond dependency updates. |
| **Gap** | Dependency patching is proactive (Dependabot + explicit CVE management in pom.xml), but no compute-level hardening or vulnerability scanning for container images or OS packages. |
| **Recommendation** | Enable Amazon ECR image scanning for container vulnerability detection. Use AWS Inspector for runtime vulnerability analysis on EKS nodes. The existing Dependabot setup is a strong foundation — complement it with infrastructure-level scanning. |
| **Evidence** | `.github/dependabot.yml`, `pom.xml` (explicit CVE management comments for commons-compress, avro, json-smart, lz4-java, mina-core) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SpotBugs (`spotbugs-maven-plugin 4.9.8.2`) and PMD (`maven-pmd-plugin 3.28.0`) are configured in the Maven build, but SpotBugs is **skipped in all CI stages** (`-Dspotbugs.skip` appears in every build.yml command). Error Prone (`error-prone.version=2.48.0`) is enabled as a compiler plugin with extensive bug pattern configuration. ForbiddenApis plugin enforces banned API usage. CycloneDX SBOM generation (`cyclonedx-maven-plugin 2.9.1`) is configured but also skipped in some CI stages. Dependabot provides daily dependency scanning. No DAST tools or container image scanning. |
| **Gap** | SAST tools configured but skipped in CI. Dependency scanning active (Dependabot). No container scanning, no DAST, no security gate blocking on critical findings. |
| **Recommendation** | Enable SpotBugs in CI (remove `-Dspotbugs.skip`). Add CycloneDX SBOM generation to CI artifacts. Integrate Amazon CodeGuru Reviewer or Snyk for additional SAST. Add ECR container image scanning. Configure security gates to block on critical/high findings. |
| **Evidence** | `.github/workflows/build.yml` (-Dspotbugs.skip in all commands), `pom.xml` (spotbugs-maven-plugin, cyclonedx-maven-plugin, error_prone_core), `config/spotbugs-exclude.xml` |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry is integrated (`opentelemetry.version=1.60.1`, `opentelemetry-instrumentation.version=2.26.1`). `TracingModule` binds the OTel `Tracer` via `TracerProvider` as an eager singleton. `GraylogSemanticAttributes` defines custom semantic attributes for lookups, caches, data adapters, periodicals, system jobs, and scheduler jobs. Tracing is provided via the OpenTelemetry Java agent. |
| **Gap** | Tracing on primary services. Cross-service propagation may have gaps since the application is currently a monolith — distributed tracing across extracted services would need explicit trace context propagation. |
| **Recommendation** | When decomposing into microservices, ensure trace context propagation headers (W3C traceparent) are forwarded across all service-to-service calls. Export traces to AWS X-Ray or an OpenTelemetry Collector on EKS. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java`, `graylog2-server/src/main/java/org/graylog/tracing/GraylogSemanticAttributes.java`, `pom.xml` (opentelemetry.version=1.60.1) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definition files found. No error budget tracking. Graylog has processing status monitoring (`processing_status_persist_interval=1s`, `processing_status_update_threshold=1m`, `processing_status_journal_write_rate_threshold=1`) and journal health checks, but these are operational thresholds, not formal SLO definitions with error budgets. |
| **Gap** | No formal SLOs — no definition of acceptable service levels for log ingestion latency, search response time, or dashboard availability. |
| **Recommendation** | Define SLOs for critical user journeys: log ingestion p99 latency, search query p95 response time, API availability. Implement SLO monitoring via Amazon CloudWatch with error budget tracking. |
| **Evidence** | `misc/graylog.conf` (processing_status_persist_interval, processing_status_update_threshold) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Built-in Prometheus exporter (`prometheus_exporter_enabled` config option, `PrometheusExporterHTTPServer.java`, configurable mapping files). Dropwizard Metrics library (`metrics.version=4.2.38`) provides infrastructure and application metrics. Custom metric mappings configurable via `prometheus_exporter_mapping_file_path_custom`. `NodeMetricPeriodical`, `ThroughputCalculator`, `TrafficCounterPeriodical` track business-relevant metrics (throughput, traffic counts). |
| **Gap** | Some business metrics tracked (throughput, traffic) but not systematically across all features. No custom CloudWatch metric publication. |
| **Recommendation** | Export Prometheus metrics to Amazon CloudWatch via CloudWatch agent or Prometheus remote write. Define dashboards for business KPIs: messages per second, indexing lag, alert trigger rates. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/metrics/prometheus/PrometheusExporterHTTPServer.java`, `graylog2-server/src/main/java/org/graylog2/periodical/ThroughputCalculator.java`, `misc/graylog.conf` (prometheus_exporter_enabled) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Static threshold monitoring exists: `processing_status_journal_write_rate_threshold=1`, `lb_throttle_threshold_percentage=95`, `output_fault_count_threshold=5` with `output_fault_penalty_seconds=30`, `stream_processing_timeout=2000` with `stream_processing_max_faults=3`. These are static thresholds, not anomaly detection. No CloudWatch anomaly detection, no dynamic baseline alerting. `ClusterHealthCheckThread` and `IndexerClusterCheckerThread` periodicals monitor cluster health. |
| **Gap** | Static threshold alarms only. No anomaly detection for gradual degradation or novel failure modes. |
| **Recommendation** | Enable CloudWatch Anomaly Detection on key metrics (ingestion rate, processing lag, error rates). Implement composite alarms for multi-signal alerting. Integrate with PagerDuty/OpsGenie for incident management. |
| **Evidence** | `misc/graylog.conf` (processing_status_journal_write_rate_threshold, lb_throttle_threshold_percentage, output_fault_count_threshold, stream_processing_timeout), `graylog2-server/src/main/java/org/graylog2/periodical/ClusterHealthCheckThread.java` |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No canary, blue/green, or staged deployment configuration. The `build.yml` CI pipeline runs tests but has no deployment stages. `dispatch-main-build.yml` dispatches builds to `graylog-project-internal` — deployment happens externally with no visibility in this repository. The `lb_recognition_period_seconds=3` config indicates awareness of load balancer health checks during shutdown, suggesting some deployment coordination exists. |
| **Gap** | No staged rollout visible. Deployment is delegated to an internal system with no canary or blue/green strategy in this repository. |
| **Recommendation** | Implement canary deployments on EKS using Argo Rollouts or AWS App Mesh with traffic shifting. Define health check endpoints and configure progressive rollout with automatic rollback on error rate thresholds. |
| **Evidence** | `.github/workflows/build.yml` (no deploy stage), `.github/workflows/dispatch-main-build.yml` (dispatches to internal repo), `misc/graylog.conf` (lb_recognition_period_seconds=3) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Full backend integration tests exist in `full-backend-tests/` with 62 Java test files. CI runs integration tests against a matrix of database versions: OpenSearch 2.19.3/MongoDB 8.0 and DataNode/MongoDB 7.0. TestContainers (`testcontainers.version=2.0.4`) is used for spinning up real database instances during tests. RestAssured (`restassured.version=6.0.0`) provides API-level integration testing. Integration tests are separated from unit tests via `@Tag` groups (`full-backend-test`). |
| **Gap** | Integration tests for primary workflows exist. Some gaps in coverage — 62 test files for a ~6,000 file codebase suggests selective coverage of critical paths. |
| **Recommendation** | Expand integration test coverage for decomposed services. Implement contract tests (Pact) when extracting services. Add integration test stages to the deployment pipeline for post-deployment verification. |
| **Evidence** | `full-backend-tests/` (62 Java files), `.github/workflows/build.yml` (full-backend-tests matrix), `pom.xml` (testcontainers.version=2.0.4, restassured.version=6.0.0) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbook files (markdown, YAML, JSON), no SSM Automation documents, no Lambda-based remediation, no self-healing automation. The application has some built-in resilience: auto-restart capability for inputs (`auto_restart_inputs`), stream fault detection with automatic disabling (`stream_processing_max_faults=3`), and output fault handling (`output_fault_count_threshold=5`). But these are application-level circuit breakers, not infrastructure-level incident response automation. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation for infrastructure-level issues. |
| **Recommendation** | Create operational runbooks for common incidents (high journal utilization, OpenSearch cluster red, MongoDB connection failures). Implement SSM Automation documents for automated remediation on EKS. |
| **Evidence** | Repository search for runbook files — none found. `misc/graylog.conf` (auto_restart_inputs, stream_processing_max_faults, output_fault_count_threshold) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CODEOWNERS file exists but only covers 2 critical paths: `graylog2-server/src/main/java/org/graylog2/indexer/*Mapping*.java` (assigned to @Graylog2/architecture) and `graylog2-server/src/main/java/org/graylog2/plugin/Message.java` (same owners). No per-service dashboards, no alarm ownership attribution, no SLO definitions with team attribution, no observability asset ownership. |
| **Gap** | No observability ownership. Monitoring is reactive with no clear team attribution for alarms, dashboards, or SLOs. |
| **Recommendation** | Extend CODEOWNERS to cover observability configurations. Define per-service dashboards with named owners on Amazon CloudWatch. Tag all monitoring resources with team ownership. |
| **Evidence** | `.github/CODEOWNERS` (2 entries only) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no IaC exists. No `default_tags`, no `tags` blocks, no tag enforcement policies. The docker-compose and configuration files have no tagging-related settings. |
| **Gap** | No tags found on resources. No cost allocation, ownership identification, or environment tagging. |
| **Recommendation** | When creating IaC, implement mandatory tagging from the start: `Environment`, `Service`, `Team`, `CostCenter`. Use AWS Organizations Tag Policies and Config rules for enforcement. Apply `default_tags` in Terraform providers or CDK aspects. |
| **Evidence** | Absence of any IaC with tagging configuration. |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q4, APP-Q1, APP-Q3, DATA-Q3, SEC-Q3, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q6 | Root Maven POM — dependency versions (Java 21, AWS SDK, Kafka, OpenTelemetry, Shiro, MongoDB driver, OpenSearch), plugin configuration (SpotBugs, PMD, CycloneDX, Error Prone) |
| `graylog2-web-interface/package.json` | APP-Q1 | Frontend dependencies — React, TypeScript, webpack, Jest, ESLint |
| `misc/graylog.conf` | INF-Q1, INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, APP-Q2, APP-Q3, APP-Q4, APP-Q6, DATA-Q1, SEC-Q2, SEC-Q4, SEC-Q5, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q5, OPS-Q7 | Primary application configuration — MongoDB URI, HTTP settings, buffer sizes, journal config, processing parameters, scheduler settings |
| `data-node/migration/docker-compose.yml` | INF-Q1, INF-Q2, INF-Q5, INF-Q9, SEC-Q2, SEC-Q5, DATA-Q3 | Migration testing infrastructure — MongoDB 7.0, OpenSearch 2.10.0, DataNode, Graylog 5.2.0 |
| `.github/workflows/build.yml` | INF-Q11, SEC-Q7, OPS-Q5, OPS-Q6, DATA-Q3 | CI pipeline — build, test, full-backend-test matrix, SpotBugs skip |
| `.github/workflows/dispatch-main-build.yml` | INF-Q11, OPS-Q5 | Build dispatch to internal deployment repo |
| `.github/dependabot.yml` | INF-Q11, SEC-Q6, SEC-Q7 | Daily dependency scanning for Maven and npm |
| `.github/CODEOWNERS` | OPS-Q8 | Code ownership — 2 entries for index mappings and Message.java |
| `api-specs/stream-output-filters.yml` | APP-Q5 | OpenAPI 3.1.0 spec for stream destination filters |
| `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile` | INF-Q1 | Test Dockerfile — eclipse-temurin:21-jre-jammy base |
| `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java` | OPS-Q1 | OpenTelemetry tracer binding |
| `graylog2-server/src/main/java/org/graylog/tracing/GraylogSemanticAttributes.java` | OPS-Q1 | Custom OTel semantic attributes |
| `graylog2-server/src/main/java/org/graylog/mcp/` | Quick Agent Wins | MCP server — 13 tools for agent integration |
| `graylog2-server/src/main/java/org/graylog2/database/` | DATA-Q2, DATA-Q4 | Centralized MongoDB data access layer |
| `graylog-storage-opensearch2/` | DATA-Q2 | OpenSearch 2 storage plugin |
| `graylog-storage-opensearch3/` | DATA-Q2 | OpenSearch 3 storage plugin |
| `graylog-storage-elasticsearch7/` | DATA-Q2 | Elasticsearch 7 storage plugin (legacy) |
| `graylog2-server/src/main/java/org/graylog2/shared/journal/LocalKafkaJournal.java` | INF-Q4, APP-Q3 | Local Kafka journal for message buffering |
| `graylog2-server/src/main/java/org/graylog2/shared/messageq/` | INF-Q4, APP-Q3 | Message queue abstraction layer |
| `graylog2-server/src/main/java/org/graylog/scheduler/` | INF-Q3, APP-Q4 | Internal job scheduler with concurrency control |
| `graylog2-server/src/main/java/org/graylog2/periodical/` | INF-Q3, APP-Q4, OPS-Q3 | 22 periodical tasks — index rotation, retention, health checks, throughput |
| `graylog2-server/src/main/java/org/graylog2/buffers/` | APP-Q3 | LMAX Disruptor ring buffer for message processing |
| `graylog2-server/src/main/java/org/graylog2/rest/resources/` | APP-Q2, APP-Q5, SEC-Q3 | REST API resources — 88+ files with Swagger annotations |
| `graylog2-server/src/main/java/org/graylog2/audit/` | SEC-Q1 | Internal audit event system |
| `graylog2-server/src/main/java/org/graylog/security/authservice/` | SEC-Q4 | Auth service backends — LDAP, AD, multi-backend |
| `graylog2-server/src/main/java/org/graylog2/security/` | SEC-Q2, SEC-Q3, SEC-Q5 | Security infrastructure — AES encryption, JWT, access tokens, sessions |
| `graylog2-server/src/main/java/org/graylog/metrics/prometheus/` | OPS-Q3 | Built-in Prometheus exporter |
| `graylog2-server/src/main/java/org/graylog/integrations/aws/` | INF-Q4 | AWS integrations — Kinesis, CloudWatch, S3 |
| `full-backend-tests/` | OPS-Q6 | 62 integration test files |
| `config/spotbugs-exclude.xml` | SEC-Q7 | SpotBugs exclusion rules |
| `misc/security.properties` | SEC-Q2 | TLS/security configuration for JVM |
| `README.markdown` | Quick Agent Wins | Project documentation |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
| `docs/` | Quick Agent Wins | Documentation — netflow, CEF guides |
