# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | thingsboard |
| **Date** | 2026-04-30 |
| **TD Version** | modernization-assessment |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, iot, platform |
| **Context** | Open-source IoT platform for device management, data collection, and visualization. |
| **Overall Score** | 1.96 / 4.0 |

**Archetype Justification**: The platform's primary function is entity management (devices, dashboards, users, alarms, rules) with full CRUD operations persisted to PostgreSQL and Cassandra. While the rule engine processes telemetry events asynchronously via Kafka, the dominant API surface is synchronous REST with persistent state mutations, making `stateful-crud` the correct classification.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.36 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work |
| **Overall** | **1.96 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | Zero infrastructure-as-code — all infrastructure is Docker Compose with no Terraform, CloudFormation, CDK, or Helm. | Blocks reproducible environments, disaster recovery, and automated provisioning. Foundation for all other modernization. |
| 2 | INF-Q11: CI/CD Automation | 1 | No build/test/deploy pipeline — only license header formatting and config validation workflows exist. | Manual deployments are error-prone, slow, and block continuous delivery. No quality gates for production releases. |
| 3 | SEC-Q5: Secrets Management | 1 | Plaintext PostgreSQL credentials (`SPRING_DATASOURCE_PASSWORD=postgres`) committed in env files; default JWT signing key in thingsboard.yml. | Critical security vulnerability — credentials in source control accessible to all repo contributors. |
| 4 | INF-Q1: Managed Compute | 1 | All compute runs on self-managed Docker containers via docker-compose with no managed orchestration (ECS/EKS/Lambda). | No elastic scaling, no automated recovery, manual capacity management. Blocks cloud-native adoption. |
| 5 | INF-Q2: Managed Databases | 1 | PostgreSQL 16 and Cassandra 5.0 run as self-managed Docker containers with no managed database services. | Manual patching, no automated failover, no point-in-time recovery. Operational burden and data loss risk. |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 2 (≥ 2). Springdoc/Swagger UI is configured with OpenAPI annotations across the REST API (`springdoc-openapi-starter-webmvc-ui` dependency, Swagger config in `thingsboard.yml`).
- **What it enables:** An AI agent that discovers and invokes ThingsBoard REST API endpoints as tools — device provisioning, telemetry queries, alarm management, dashboard creation, and rule chain configuration via natural language.
- **Additional steps:** Generate a static OpenAPI spec file from the running Swagger endpoint for offline agent tool discovery. Ensure all endpoints have complete schema documentation.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2). Centralized DAO layer (`dao/` module) with JPA/Hibernate repositories and `dao-api` interfaces providing clean data access patterns.
- **What it enables:** A natural-language-to-SQL agent that queries device telemetry, entity attributes, and alarm history through the centralized DAO layer — enabling operators to ask questions like "Show me all devices with temperature above 80 in the last hour."
- **Additional steps:** Create a read-only query interface that wraps the DAO layer to prevent write operations from agent queries. Document the entity schema for agent context.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** README.md, security.md, and extensive inline documentation exist in the repository. The `thingsboard.yml` configuration file contains 2,208 lines of documented configuration options.
- **What it enables:** A retrieval-augmented generation agent that indexes ThingsBoard documentation, configuration reference, and API docs to answer developer and operator questions about platform configuration, deployment, and troubleshooting.
- **Additional steps:** Index the README, security.md, thingsboard.yml comments, and any existing wiki/documentation. Use Amazon Bedrock (preferred) for the LLM backend.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 2 (≥ 2). ThingsBoard's rule engine provides a visual workflow system (rule chains) for telemetry processing, alarm management, and device lifecycle automation.
- **What it enables:** An agent that monitors rule chain execution, identifies failing nodes, suggests rule chain optimizations, and can create or modify rule chains via the REST API based on natural language descriptions of desired automation behavior.
- **Additional steps:** Expose rule chain execution metrics and error logs in a structured format consumable by the agent. Leverage the existing Grafana rule engine dashboards as monitoring input.
- **Effort:** Medium

> **Note:** DevOps Agent was excluded because INF-Q11 = 1 (no CI/CD pipeline exists to orchestrate). Observability Agent was excluded because OPS-Q1 = 1 (no distributed tracing infrastructure for the agent to query).

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — modular architecture with separately deployable services already exists. Primary trigger (APP-Q2 < 3) not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but 13 Dockerfiles and docker-compose already exist. Contextual guard: workloads are already containerized. Gap is managed orchestration, not containerization. |
| 3 | Move to Open Source | Not Triggered | — | — | PostgreSQL and Cassandra are already open-source databases. No commercial DB engines (Oracle, SQL Server) detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed), DATA-Q3 = 3 (supporting). |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4 = 2 (self-managed Kafka), data processing workloads evident (rule engine telemetry processing, time-series partitioning, alarm aggregation). |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 1 (no CI/CD pipeline). Supporting: OPS-Q5 = 1, OPS-Q6 = 3. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context mentions "IoT platform for device management, data collection, and visualization" — no AI signal terms found. Note: langchain4j integration already exists in the rule engine but the pathway evaluates intent, not presence. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** All databases run as self-managed Docker containers:
- **PostgreSQL 16** (`postgres:16` image in `docker-compose.postgres.yml`) — primary entity and timeseries storage with hardcoded credentials (`POSTGRES_PASSWORD=postgres`)
- **Cassandra 5.0** (`cassandra:5.0` image in `docker-compose.hybrid.yml`) — optional timeseries storage in hybrid mode
- **Valkey 8.0** (`bitnamilegacy/valkey:8.0` in `docker-compose.valkey.yml`) — caching layer with `ALLOW_EMPTY_PASSWORD=yes`

No backup configuration, no automated failover, no encryption at rest, no point-in-time recovery.

**Recommended Migration Targets (respecting preferences):**

| Current | Recommended Target | Rationale |
|---------|-------------------|-----------|
| PostgreSQL 16 (Docker) | **Amazon Aurora PostgreSQL** (preferred) | Wire-compatible, managed failover, automated backups, PITR, Multi-AZ. Aurora's PostgreSQL compatibility means minimal application changes. Supports the stored functions/procedures already in use. |
| Cassandra 5.0 (Docker) | **Amazon DynamoDB** (preferred) for telemetry | DynamoDB provides managed NoSQL with single-digit millisecond latency, auto-scaling, and built-in backup. ThingsBoard's time-series data model (entity_id + key + timestamp) maps naturally to DynamoDB's partition/sort key model. Alternatively, Amazon Keyspaces for Cassandra wire compatibility. |
| Valkey 8.0 (Docker) | **Amazon ElastiCache for Valkey** | Managed Valkey-compatible cache with Multi-AZ replication, automated failover, and encryption at rest/in transit. |

**Migration Tools:** AWS Database Migration Service (DMS) for PostgreSQL → Aurora migration. AWS Schema Conversion Tool (SCT) if stored procedure conversion is needed.

**Key Steps:**
1. Provision Aurora PostgreSQL cluster (Multi-AZ) and ElastiCache for Valkey via IaC (Terraform/CDK)
2. Use DMS for zero-downtime migration of PostgreSQL data
3. Update connection strings via environment variables (already externalized in `thingsboard.yml`)
4. Evaluate DynamoDB as Cassandra replacement for time-series workload — prototype with ThingsBoard's pluggable DAO layer
5. Enable automated backups, PITR, and encryption at rest on all managed databases

**Learning Resources:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:** Self-managed Kafka (`bitnamilegacy/kafka:4.0` in `docker-compose.kafka.yml`) serves as the message broker for all inter-service communication:
- Transport services → Kafka → Rule Engine (telemetry processing)
- Core services → Kafka → Rule Engine (device lifecycle events, alarms)
- Custom queue abstraction in `common/queue/` with Kafka-specific implementation

Data processing workloads are significant: rule engine processes telemetry through configurable rule chains, time-series data is partitioned and aggregated via stored procedures (`schema-ts-psql.sql`), and alarm lifecycle management involves multi-step processing.

**Evidence of Data Processing Workloads:**
- Rule engine telemetry processing pipeline (rule chains with filtering, transformation, enrichment, and action nodes)
- Time-series partition management (`drop_partitions_by_system_ttl` procedure in `schema-ts-psql.sql`)
- TTL-based data cleanup functions (`delete_device_records_from_ts_kv`, `delete_asset_records_from_ts_kv`)
- Alarm aggregation functions (`create_or_update_active_alarm` in `schema-functions.sql`)

**Recommended Migration Targets (respecting preferences — avoid self-managed-kafka):**

| Current | Recommended Target | Rationale |
|---------|-------------------|-----------|
| Self-managed Kafka (Docker) | **Amazon EventBridge** (preferred) for event routing + **Amazon MSK Serverless** for streaming | EventBridge for device lifecycle events and alarm notifications. MSK Serverless for high-throughput telemetry streaming — maintains Kafka wire compatibility with ThingsBoard's existing `kafka-clients` dependency while eliminating operational overhead. |
| Stored procedure-based analytics | **Amazon Athena** + **AWS Glue** | For historical telemetry analytics, offload partition management and TTL cleanup to Glue ETL jobs and query via Athena on S3 data lake. |

**Key Steps:**
1. Replace self-managed Kafka with MSK Serverless — update `TB_KAFKA_SERVERS` environment variable
2. Introduce EventBridge for event-driven alarm routing and notification delivery
3. Evaluate moving time-series archival to S3 + Athena for cost-effective historical analytics
4. Migrate TTL cleanup logic from stored procedures to managed Glue jobs

**Learning Resources:** [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** The repository has critical DevOps gaps across all dimensions:

**IaC Coverage (INF-Q10 = 1):** Zero infrastructure-as-code. All infrastructure is defined in Docker Compose files (`docker/docker-compose*.yml`). No Terraform, CloudFormation, CDK, Helm charts, or Kustomize manifests exist for cloud resource provisioning.

**CI/CD Automation (INF-Q11 = 1):** Only 2 GitHub Actions workflows exist:
- `check-configuration-files.yml` — Validates YAML configuration files on push/PR
- `license-header-format.yml` — Formats license headers on push to master

Neither workflow builds, tests, or deploys the application. No build pipeline, no test automation in CI, no deployment automation.

**Deployment Strategy (OPS-Q5 = 1):** No canary, blue/green, or rolling deployment strategy. Docker Compose `restart: always` is the only recovery mechanism. Deployments are manual shell scripts (`docker-start-services.sh`, `docker-stop-services.sh`, `docker-upgrade-tb.sh`).

**Recommended DevOps Toolchain (respecting preferences — prefer EKS):**

| Gap | Recommended Solution | Priority |
|-----|---------------------|----------|
| No IaC | **Terraform** or **AWS CDK** for VPC, EKS cluster, Aurora, ElastiCache, MSK provisioning | P0 — Foundation for all other modernization |
| No CI/CD | **GitHub Actions** pipeline with build → test → container push → deploy stages. **AWS CodePipeline** + **CodeBuild** as alternative. | P0 — Enable continuous delivery |
| No deployment strategy | **EKS** (preferred) with **Helm charts** for deployment. ArgoCD or Flux for GitOps-based canary/blue-green deployments. | P1 — After IaC and CI/CD are in place |
| No security scanning | **Dependabot** for dependency scanning, **Amazon CodeGuru** or **SonarQube** for SAST, **ECR image scanning** for container vulnerabilities | P1 — Integrate into CI/CD pipeline |

**Key Steps:**
1. **Phase 1 (Weeks 1-4):** Create Terraform/CDK modules for core AWS infrastructure (VPC, EKS cluster, Aurora PostgreSQL, ElastiCache)
2. **Phase 2 (Weeks 2-6):** Build GitHub Actions CI/CD pipeline — Maven build, unit tests, Docker image build, push to ECR
3. **Phase 3 (Weeks 4-8):** Create Helm charts for all ThingsBoard services (tb-core, tb-rule-engine, transports, web-ui, js-executor)
4. **Phase 4 (Weeks 6-10):** Implement GitOps deployment (ArgoCD on EKS) with canary rollouts
5. **Phase 5 (Weeks 4-8, parallel):** Add security scanning — Dependabot, SAST, container scanning

**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute workloads run as self-managed Docker containers orchestrated via Docker Compose. The `docker/docker-compose.yml` defines 18+ services (tb-core1/2, tb-rule-engine1/2, tb-mqtt-transport1/2, tb-http-transport1/2, tb-coap-transport, tb-lwm2m-transport, tb-snmp-transport, tb-web-ui1/2, tb-vc-executor1/2, tb-js-executor, haproxy, zookeeper) all using `restart: always`. There are 13 Dockerfiles under `msa/`. No ECS, EKS, Lambda, Fargate, or any managed compute service definitions were found. No Terraform, CloudFormation, or CDK files exist in the repository. |
| **Gap** | All compute on self-managed Docker containers with no managed orchestration. No elastic scaling, no automated recovery beyond container restart, no resource limits enforcement at the orchestration level. |
| **Recommendation** | Migrate to **Amazon EKS** (preferred). Create Helm charts for each ThingsBoard service. Use EKS managed node groups with Graviton instances for cost optimization. Deploy transports as separate Kubernetes Deployments with HPA for auto-scaling based on connection count. |
| **Evidence** | `docker/docker-compose.yml`, `msa/tb-node/docker/Dockerfile`, `msa/transport/mqtt/docker/Dockerfile`, `docker/.env` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed Docker containers: PostgreSQL 16 (`postgres:16` in `docker-compose.postgres.yml`), Cassandra 5.0 (`cassandra:5.0` in `docker-compose.hybrid.yml`), and Valkey 8.0 (`bitnamilegacy/valkey:8.0` in `docker-compose.valkey.yml`). Credentials are hardcoded: `POSTGRES_PASSWORD=postgres` in docker-compose, `SPRING_DATASOURCE_PASSWORD=postgres` in `tb-node.postgres.env`, and Valkey runs with `ALLOW_EMPTY_PASSWORD=yes`. No RDS, Aurora, DynamoDB, ElastiCache, or any managed database resources found. |
| **Gap** | All databases self-managed on Docker with no automated failover, no managed backups, no encryption at rest, and hardcoded credentials. Single points of failure for all data stores. |
| **Recommendation** | Migrate to **Amazon Aurora PostgreSQL** (preferred) for entity storage with Multi-AZ enabled. Evaluate **Amazon DynamoDB** (preferred) for telemetry time-series data. Migrate Valkey to **Amazon ElastiCache for Valkey** with Multi-AZ replication. Use AWS DMS for zero-downtime PostgreSQL migration. |
| **Evidence** | `docker/docker-compose.postgres.yml`, `docker/docker-compose.hybrid.yml`, `docker/docker-compose.valkey.yml`, `docker/tb-node.postgres.env` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard implements its own rule engine as the primary workflow orchestration system. Rule chains provide visual workflow management with configurable nodes for message transformation, filtering, enrichment, and action execution. The rule engine processes telemetry, alarms, and device lifecycle events through these chains. However, this is application-level orchestration hardcoded in the Java codebase — not a dedicated external workflow orchestration service. No Step Functions, Temporal, MWAA, or Camunda found. For the `stateful-crud` archetype, this represents "simple state machines in code with some structure, but no dedicated service." |
| **Gap** | Workflow orchestration is implemented as application-level rule chains with no dedicated external orchestration service. Error handling, retry logic, and state management are embedded in the application code rather than managed by a specialized platform. |
| **Recommendation** | For complex multi-step operations (OTA firmware updates, bulk device provisioning, tenant onboarding), evaluate **AWS Step Functions** to externalize orchestration. Keep the rule engine for real-time telemetry processing but offload long-running administrative workflows to managed orchestration. |
| **Evidence** | `rule-engine/rule-engine-components/src/main/java/`, `application/src/main/resources/thingsboard.yml` (queue and rule_engine configuration) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Inter-service messaging uses self-managed Kafka (`bitnamilegacy/kafka:4.0` in `docker-compose.kafka.yml`) with KRaft mode. Kafka client 3.9.1 is used via `common/queue/` module with a custom queue abstraction (`TbQueueProducer`, `TbQueueConsumer`). The platform supports in-memory queue as an alternative (`queue.type: in-memory` in `thingsboard.yml`). AWS SDK v1 (1.12.701) dependencies exist for `aws-java-sdk-sqs` and `aws-java-sdk-sns` but no active SQS/SNS queue provider implementation was found. All services depend on Kafka for transport→core→rule-engine message flow. User preferences explicitly state to avoid self-managed Kafka. |
| **Gap** | Self-managed Kafka in Docker containers for all cross-service messaging. Requires manual scaling, patching, and monitoring. Single-node Kafka deployment with no replication in the default configuration. |
| **Recommendation** | Replace self-managed Kafka with **Amazon MSK Serverless** (maintains Kafka wire compatibility with existing `kafka-clients` dependency) or implement an **Amazon EventBridge** (preferred) queue provider for event routing. The existing queue abstraction in `common/queue/` makes provider substitution feasible. Consider implementing the dormant SQS/SNS provider to leverage AWS managed messaging directly. |
| **Evidence** | `docker/docker-compose.kafka.yml`, `docker/kafka.env`, `docker/queue-kafka.env`, `pom.xml` (kafka.version=3.9.1, aws.sdk.version=1.12.701) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud networking infrastructure defined. No VPC, subnets, security groups, NACLs, or network segmentation found anywhere in the repository. All services communicate over Docker's default bridge network. HAProxy (`docker/haproxy/config/haproxy.cfg`) provides some network-level controls: IP-based rate limiting (429 responses for >100 req/10s or >300 req/1m), trustlist/blocklist files, and connection limits per IP (50 concurrent connections). However, all internal services are directly accessible to each other with no network segmentation between tiers. |
| **Gap** | Services deployed without any cloud network isolation. No VPC, no private subnets, no security group rules. All services share a flat Docker network. No managed networking services (VPC endpoints, PrivateLink, VPC Lattice). |
| **Recommendation** | Define a VPC with public/private subnet tiers using IaC. Place databases and internal services (rule engine, ZooKeeper/Kafka) in private subnets. Deploy **API Gateway** (preferred) as the public-facing entry point. Use security groups with least-privilege rules between service tiers. |
| **Evidence** | `docker/docker-compose.yml` (default Docker networking), `docker/haproxy/config/haproxy.cfg` (rate limiting, trustlist/blocklist) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | HAProxy (`thingsboard/haproxy-certbot:2.2.33-alpine`) serves as the entry point with path-based routing, health checks, and TLS termination. Routes include: `/api/v1/` → HTTP transport backend, `/api/` → tb-core API backend, default → web UI backend. HAProxy provides rate limiting (100 req/10s, 300 req/1m per IP), connection limits, SSL/TLS configuration, and basic load balancing (leastconn for transport, source-based for API). However, there is no API Gateway with request validation, no authentication at the gateway level, no throttling per API key, and no request transformation. |
| **Gap** | Load balancer present but no API Gateway with auth, request validation, throttling per client, or API key management. Authentication is handled at the application level, not at the gateway. |
| **Recommendation** | Deploy **Amazon API Gateway** (preferred) as the public-facing entry point for the REST API. Configure per-client throttling, request validation, and API key management. Use API Gateway's Cognito or JWT authorizer for gateway-level authentication. Retain ALB/NLB for MQTT, CoAP, and LwM2M transport protocols that API Gateway doesn't natively support. |
| **Evidence** | `docker/docker-compose.yml` (haproxy service), `docker/haproxy/config/haproxy.cfg` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling mechanisms configured for any resource. All services use static replica counts defined in Docker Compose: `tb-js-executor` has `deploy: replicas: 10`, all other services have exactly 1 or 2 fixed instances (tb-core1/2, tb-rule-engine1/2, tb-mqtt-transport1/2, etc.). No cloud auto-scaling (ASG, ECS service auto-scaling, EKS HPA, Lambda concurrency) found. No DynamoDB auto-scaling, no Aurora auto-scaling. All capacity is statically provisioned. |
| **Gap** | All capacity statically provisioned. Cannot respond to traffic spikes (IoT device fleet growth, telemetry bursts) or scale down during low demand. Over-provisioning wastes resources; under-provisioning degrades IoT connectivity. |
| **Recommendation** | On EKS (preferred), configure Horizontal Pod Autoscaler (HPA) for transport services based on connection count metrics, and for rule engine based on queue depth. Use Cluster Autoscaler or Karpenter for node-level scaling. For Aurora, enable auto-scaling read replicas. For DynamoDB, enable on-demand capacity or auto-scaling provisioned mode. |
| **Evidence** | `docker/docker-compose.yml` (`deploy: replicas: 10` for js-executor, static instances for all others) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found for any data store. PostgreSQL data is stored in a Docker volume (`./tb-node/postgres:/var/lib/postgresql/data`) with no backup automation. Cassandra data is in a Docker volume (`./tb-node/cassandra:/var/lib/cassandra`) with no backup. Valkey data is in `./tb-node/valkey-data:/bitnami/valkey/data` with no persistence guarantees. No `aws_backup_plan`, no S3 versioning, no EBS snapshot policies, no point-in-time recovery configuration. The `backup_retention_period` is not applicable as no managed databases are in use. |
| **Gap** | No automated backups for any data store. A disk failure, accidental deletion, or corruption event would result in complete data loss. No restore procedures documented or tested. |
| **Recommendation** | After migrating to managed databases: enable automated backups with 7-day retention on Aurora PostgreSQL, enable PITR on DynamoDB tables, configure ElastiCache automatic backups. For the interim Docker deployment, implement `pg_dump` scheduled backups to S3 and Cassandra `nodetool snapshot` automation. |
| **Evidence** | `docker/docker-compose.postgres.yml` (Docker volume, no backup config), `docker/docker-compose.hybrid.yml` (Docker volume, no backup config), `docker/docker-compose.valkey.yml` (Docker volume) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Multiple service instances exist: tb-core1/2, tb-rule-engine1/2, tb-mqtt-transport1/2, tb-http-transport1/2, tb-web-ui1/2, tb-vc-executor1/2, and 10 js-executor replicas. HAProxy load balances across instances with health checks (`check inter 5s`). ZooKeeper coordinates service discovery. However, all instances run on a single Docker host — no multi-AZ deployment, no cross-host replication. ZooKeeper is a single instance (`ZOO_SERVERS: server.1=zookeeper:2888:3888`). PostgreSQL and Cassandra are single-instance. A host failure takes down the entire platform. |
| **Gap** | Service-level redundancy exists (multiple instances) but all on a single host. No multi-AZ deployment, no cross-host fault isolation. Single ZooKeeper, single PostgreSQL, single Cassandra instance. |
| **Recommendation** | Deploy on EKS (preferred) with worker nodes across 2+ AZs. Use Aurora PostgreSQL with Multi-AZ for database HA. Replace single ZooKeeper with a 3-node ensemble or migrate to Kafka KRaft (already configured). Configure pod anti-affinity rules to spread service instances across AZs. |
| **Evidence** | `docker/docker-compose.yml` (multiple instances on single host), `docker/docker-compose.yml` (single ZooKeeper), `docker/docker-compose.postgres.yml` (single PostgreSQL) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure-as-code found in the repository. No Terraform files (`.tf`, `.tfvars`), no CloudFormation templates, no CDK stacks (`cdk.json`), no Helm charts (`Chart.yaml`), no Kustomize (`kustomization.yaml`). All infrastructure is defined in Docker Compose files under `docker/`. While Docker Compose provides declarative container orchestration, it does not provision cloud resources (VPC, databases, load balancers, DNS, IAM). The repository contains only Docker Compose for local/single-host deployment. |
| **Gap** | All infrastructure created manually or via Docker Compose. No reproducible cloud infrastructure. Cannot provision environments on-demand, cannot perform disaster recovery from code, and cannot enforce infrastructure consistency across environments. |
| **Recommendation** | Adopt **Terraform** or **AWS CDK** for all cloud infrastructure. Start with VPC, EKS cluster, Aurora PostgreSQL, ElastiCache, and MSK Serverless. Create Helm charts for ThingsBoard service deployments on EKS. Store all IaC in the repository alongside application code. |
| **Evidence** | Repository root directory scan — no `.tf`, `.tfvars`, `Chart.yaml`, `kustomization.yaml`, `cdk.json`, or `*.cfn.yaml` files found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Only 2 GitHub Actions workflows exist (excluding `atx-transform.yml`): `check-configuration-files.yml` validates YAML configuration files using a Python script, and `license-header-format.yml` formats license headers and auto-commits on push to master. Neither workflow builds the application, runs tests, builds Docker images, or deploys to any environment. No `buildspec.yml`, no `Jenkinsfile`, no CodePipeline definitions found. The `build.sh` script exists in the repository root but is not integrated into any CI/CD pipeline. |
| **Gap** | No CI/CD pipeline for application build, test, or deployment. All builds and deployments are manual. No quality gates, no automated testing in CI, no container image publishing to a registry. |
| **Recommendation** | Create a **GitHub Actions** CI/CD pipeline with stages: Maven build → unit tests → integration tests → Docker image build → push to ECR → deploy to EKS. Add **AWS CodePipeline** as an alternative for AWS-native CI/CD. Implement branch protection rules requiring CI passage before merge. |
| **Evidence** | `.github/workflows/check-configuration-files.yml`, `.github/workflows/license-header-format.yml`, absence of build/deploy workflows |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary language is **Java 25** (maven.compiler.source=25, maven.compiler.target=25 in `pom.xml`) with **Spring Boot 3.5.12**. Frontend uses **Angular 20** (TypeScript 5.9.3, `@angular/core: 20.3.18` in `ui-ngx/package.json`). Modern framework ecosystem: Lombok 1.18.44, Hibernate/JPA via Spring Data, Jackson 2.21.1, Netty 4.1.132. However, **AWS SDK v1** (1.12.701) is used for `aws-java-sdk-sqs`, `aws-java-sdk-sns`, and `aws-java-sdk-lambda` — this is the legacy SDK (v1), not the modern AWS SDK for Java v2. Langchain4j 1.8.0-TB provides AI framework integration. |
| **Gap** | AWS SDK v1 (1.12.701) is legacy. AWS SDK for Java v2 offers better performance, non-blocking I/O, and enhanced credential management. The SDK version is the primary modernization gap — Java 25 and Spring Boot 3.5.12 are cutting-edge. |
| **Recommendation** | Migrate AWS SDK dependencies from v1 (`com.amazonaws:aws-java-sdk-*`) to v2 (`software.amazon.awssdk:*`). This is an SDK/library upgrade, not a language change. Spring Boot 3.5.x has excellent SDK v2 integration support. |
| **Evidence** | `pom.xml` (maven.compiler.source=25, spring-boot.version=3.5.12, aws.sdk.version=1.12.701), `ui-ngx/package.json` (@angular/core: 20.3.18) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | ThingsBoard has a **modular architecture with separately deployable services** sharing a database: tb-core (2 instances), tb-rule-engine (2 instances), 5 transport services (MQTT, HTTP, CoAP, LwM2M, SNMP), js-executor (10 replicas), web-ui (2 instances), vc-executor (2 instances), and EDQS. Each service runs in its own Docker container with its own Dockerfile. Services communicate via Kafka message queue (not direct HTTP calls). Service discovery uses ZooKeeper. The `thingsboard.yml` has `service.type: monolith` for single-node and `tb-core` / `tb-rule-engine` for microservice mode. However, all services share the same PostgreSQL/Cassandra database and share the core codebase (`common/` modules). This is a "modular monolith with separate schemas per module" pattern — services can be deployed independently but share the database instance. |
| **Gap** | Services share a single PostgreSQL database instance (though they operate on their own data domains). Shared codebase in `common/` modules means service boundaries are not fully independent. ZooKeeper dependency creates tight coupling in the service mesh. |
| **Recommendation** | The current architecture is appropriate for the platform's complexity. For further decomposition, consider: (1) Introduce per-service database schemas to enforce data ownership boundaries, (2) Replace ZooKeeper coordination with Kafka KRaft (already partially configured) or cloud-native service discovery, (3) Extract transport services into fully independent deployable units with their own CI/CD pipelines. |
| **Evidence** | `docker/docker-compose.yml` (18+ separate service containers), `application/src/main/resources/thingsboard.yml` (service.type configuration), `docker/docker-compose.postgres.yml` (shared PostgreSQL) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: stateful-crud.** The platform has a good mix of async and sync communication appropriate for the archetype. **Async (Kafka):** Transport services push device telemetry to Kafka queues → consumed by rule engine for processing. Core services publish state change events → consumed by rule engine. All inter-service communication for telemetry flow is async via the `common/queue/` abstraction. **Sync (REST):** Client-facing REST API (`/api/`) for entity CRUD operations is synchronous. Device HTTP transport (`/api/v1/`) is synchronous request-response. The queue abstraction (`TbQueueProducer`, `TbQueueConsumer`) provides a clean async interface for cross-service state propagation. |
| **Gap** | Managed messaging (SQS, EventBridge) for key flows is not yet in place — self-managed Kafka handles all async. Synchronous HTTP used for some flows that could benefit from async (e.g., bulk operations, report generation). |
| **Recommendation** | The async/sync ratio is appropriate for `stateful-crud`. Focus on replacing the self-managed Kafka with managed messaging (MSK Serverless or EventBridge) rather than changing communication patterns. Consider adding async patterns for bulk operations that currently block. |
| **Evidence** | `common/queue/src/main/java/` (queue abstraction), `docker/docker-compose.kafka.yml` (Kafka messaging), `application/src/main/resources/thingsboard.yml` (queue.type configuration) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: stateful-crud.** Most long-running operations are handled asynchronously: telemetry processing runs through Kafka queues and rule chains (async by design), alarm lifecycle management uses stored functions for atomic operations, OTA firmware updates are managed through the rule engine with status tracking, and version control operations (import/export) run via dedicated vc-executor services. The js-executor pool (10 replicas) handles JavaScript/TBEL rule node execution asynchronously. REST API endpoints for entity CRUD are synchronous but typically fast-returning. Some operations like bulk import and report generation may block. |
| **Gap** | Most long-running operations are async, but some bulk operations (device provisioning, CSV import) may still block the caller. No formal job status API pattern for tracking long-running administrative operations. |
| **Recommendation** | For bulk operations, implement async job processing with status polling endpoints. The existing vc-executor pattern (dedicated executor service) can be extended to other bulk operations. Use Step Functions for complex multi-step administrative workflows. |
| **Evidence** | `docker/docker-compose.yml` (tb-js-executor replicas: 10, vc-executor services), `rule-engine/rule-engine-components/src/main/java/` (async rule node processing), `application/src/main/resources/thingsboard.yml` (rule_engine.response_timeout) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Partial API versioning exists. The device transport HTTP API uses `/api/v1/` path prefix (visible in HAProxy routing: `acl transport_http_acl path_beg /api/v1/` and Swagger config: `non_security_path_regex: /api/(?:noauth|v1)/.*`). However, the main platform REST API (`/api/`) does not use version prefixes — endpoints like `/api/device`, `/api/dashboard`, `/api/tenant` have no versioning. The Swagger UI is configured with a single group (`thingsboard`) and version from package version. No `Accept-Version` headers or query parameter versioning detected. |
| **Gap** | Only the device transport API uses URL path versioning (`/api/v1/`). The main REST API has no versioning — breaking changes would affect all consumers simultaneously. No backward compatibility guarantees documented. |
| **Recommendation** | Adopt URL path versioning (`/api/v2/`) for the main REST API. Use API Gateway (preferred) versioning features to manage multiple API versions. Document a deprecation policy for older API versions. |
| **Evidence** | `docker/haproxy/config/haproxy.cfg` (`path_beg /api/v1/`), `application/src/main/resources/thingsboard.yml` (swagger.non_security_path_regex) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Service discovery uses **Apache ZooKeeper** (via Curator 5.6.0) for coordination among ThingsBoard services. The `ZkDiscoveryService` in `common/queue/src/main/java/org/thingsboard/server/queue/discovery/` registers and discovers services dynamically. Services register with `TB_SERVICE_ID` and `TB_SERVICE_TYPE` labels. `HashPartitionService` and `ConsistentHashCircle` implement consistent hashing for partition assignment. ZooKeeper is enabled via `ZOOKEEPER_ENABLED=true` and `ZOOKEEPER_URL=zookeeper:2181` in `tb-node.env`. HAProxy uses Docker DNS resolver for backend service discovery (`resolvers docker_resolver`). No hard-coded service endpoints — all service locations are resolved dynamically. |
| **Gap** | ZooKeeper-based service discovery is functional but adds operational complexity (ZooKeeper cluster management). Not a cloud-native service discovery mechanism. Single ZooKeeper instance is a SPOF. |
| **Recommendation** | When migrating to EKS (preferred), leverage Kubernetes-native service discovery (CoreDNS + Kubernetes Services) or AWS Cloud Map. Replace ZooKeeper with Kafka KRaft (partially supported — `KAFKA_CFG_PROCESS_ROLES=controller,broker` already configured in `kafka.env`) for consensus. |
| **Evidence** | `common/queue/src/main/java/org/thingsboard/server/queue/discovery/ZkDiscoveryService.java`, `docker/tb-node.env` (ZOOKEEPER_ENABLED=true), `docker/docker-compose.yml` (zookeeper service), `pom.xml` (curator.version=5.6.0) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Unstructured data (device telemetry blobs, OTA firmware packages, dashboard images, widget bundles) is stored in PostgreSQL and Cassandra — not in object storage. The `thingsboard.yml` has no S3 bucket configuration. File-type data (images, firmware) is stored as binary data in the database or on local filesystem. No S3, no Textract, no document parsing pipeline found. Some file handling exists through the REST API for OTA updates and image management, but all data ultimately resides in the database. |
| **Gap** | Unstructured data locked in databases rather than managed object storage. No parsing pipeline for document extraction. Database storage of binary blobs is expensive and limits scalability for large firmware files and media. |
| **Recommendation** | Migrate binary data (OTA packages, images, exports) to **Amazon S3** with lifecycle policies. Implement S3 presigned URLs for direct upload/download. Use S3 event notifications with EventBridge for processing triggers. For document-type data, consider Amazon Textract for automatic extraction. |
| **Evidence** | `application/src/main/resources/thingsboard.yml` (no S3 configuration), `docker/docker-compose.postgres.yml` (all data in PostgreSQL), `dao/src/main/resources/sql/schema-entities.sql` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `dao/` module provides a centralized data access layer with JPA/Hibernate repositories. The `common/dao-api/` module defines clean interfaces (`DeviceDao`, `AlarmDao`, `DashboardDao`, etc.) that abstract database access. Hypersistence Utils 3.7.4 enhances Hibernate for complex PostgreSQL types. The Cassandra driver (4.17.0) is used via dedicated DAO implementations for time-series data. The DAO layer supports both PostgreSQL-only and hybrid (PostgreSQL + Cassandra) modes via configuration. However, some direct database access patterns exist outside the main DAO layer — stored functions bypass the DAO for performance-critical operations. |
| **Gap** | Mostly centralized with some direct database access for performance-critical paths. Stored functions in PostgreSQL bypass the application-layer DAO for alarm management and partition cleanup, creating a secondary data access channel. |
| **Recommendation** | Evaluate migrating stored function logic to the application layer DAO to consolidate all data access through a single abstraction. This would also facilitate future migration to DynamoDB for time-series data, which doesn't support stored procedures. |
| **Evidence** | `dao/src/main/java/` (DAO implementations), `common/dao-api/` (DAO interfaces), `pom.xml` (hypersistence-utils.version=3.7.4, cassandra.version=4.17.0), `dao/src/main/resources/sql/schema-functions.sql` (stored functions bypassing DAO) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are pinned via Docker image tags: PostgreSQL 16 (`postgres:16` in `docker-compose.postgres.yml`) and Cassandra 5.0 (`cassandra:5.0` in `docker-compose.hybrid.yml`). Both are current, supported versions — PostgreSQL 16 (GA November 2023, supported until November 2028) and Cassandra 5.0 (GA December 2024, latest major). Valkey 8.0 is also current. However, version pinning is only at the Docker image tag level — no IaC with explicit `engine_version` parameters. No documented version-update procedure covering downtime windows, rollback, and risk acknowledgment. |
| **Gap** | Versions are current but pinned only via Docker image tags (e.g., `postgres:16` could auto-update minor versions). No formal version-update procedure documented. No IaC-level version pinning with explicit engine version parameters. |
| **Recommendation** | Pin to specific minor versions in Docker images (e.g., `postgres:16.4`). When migrating to Aurora PostgreSQL, pin the engine version explicitly in IaC. Document a database version-update procedure including testing, rollback plan, and maintenance window scheduling. |
| **Evidence** | `docker/docker-compose.postgres.yml` (`image: "postgres:16"`), `docker/docker-compose.hybrid.yml` (`image: "cassandra:5.0"`), `docker/docker-compose.valkey.yml` (`image: bitnamilegacy/valkey:8.0`) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | 16 stored functions/procedures found across SQL schema files, implementing business-critical logic in PostgreSQL PL/pgSQL: **Alarm management** (6 functions in `schema-functions.sql`): `create_or_update_active_alarm`, `update_alarm`, `acknowledge_alarm`, `clear_alarm`, `assign_alarm`, `unassign_alarm`. **Time-series management** (7 functions in `schema-ts-psql.sql`): `drop_partitions_by_system_ttl`, `get_partition_by_system_ttl_date`, `to_uuid`, `delete_device_records_from_ts_kv`, `delete_asset_records_from_ts_kv`, `delete_customer_records_from_ts_kv`. **TimescaleDB variant** (3 additional functions in `schema-timescale.sql`). While these use PostgreSQL's open-source PL/pgSQL (not proprietary T-SQL/PL/SQL), they couple significant business logic to the database engine, making migration more complex. |
| **Gap** | Moderate stored procedure usage coupling alarm management and time-series lifecycle logic to PostgreSQL. These procedures must be extracted or converted when migrating to different database engines (e.g., DynamoDB for time-series). No proprietary SQL dialect, but PL/pgSQL-specific constructs (`DECLARE`, `FOR UPDATE`, `PARTITION BY RANGE`). |
| **Recommendation** | Extract alarm management stored functions to the application-layer DAO using Spring Data JPA. For time-series partition management, evaluate using Aurora PostgreSQL's native partitioning (compatible with existing functions) or migrate to DynamoDB TTL for automatic data expiration. Prioritize extraction of alarm functions first as they contain the most business logic. |
| **Evidence** | `dao/src/main/resources/sql/schema-functions.sql` (6 alarm functions), `dao/src/main/resources/sql/schema-ts-psql.sql` (7 time-series functions), `dao/src/main/resources/sql/schema-timescale.sql` (3 TimescaleDB functions) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud-level audit logging configured. No `aws_cloudtrail` resources found (no IaC exists). ThingsBoard has application-level audit logging capabilities (audit log events for entity operations visible in the UI), but no cloud-native immutable audit trail. No CloudWatch log retention policies. No S3 Object Lock for log storage. Application logs use `json-file` Docker logging driver with size-based rotation (200m, 30 files) but these are local logs with no centralized log management. |
| **Gap** | No cloud audit trail. Application-level audit logs exist but are stored locally on the Docker host with no immutability, centralization, or retention guarantees. Cannot perform forensic analysis after infrastructure-level incidents. |
| **Recommendation** | Enable **AWS CloudTrail** with log file validation and immutable storage (S3 with Object Lock). Configure **CloudWatch Logs** for centralized application log aggregation. Ship Docker container logs to CloudWatch using the `awslogs` logging driver or Fluent Bit sidecar on EKS. |
| **Evidence** | `docker/docker-compose.yml` (json-file logging driver), absence of CloudTrail configuration in any file |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured for any data store. PostgreSQL data volume (`./tb-node/postgres:/var/lib/postgresql/data`) is unencrypted. Cassandra data volume (`./tb-node/cassandra:/var/lib/cassandra`) is unencrypted. Valkey data volume is unencrypted. No KMS keys defined, no encryption parameters on any database configuration. No S3 bucket encryption (no S3 buckets exist). SSL/TLS for database connections is not configured (default PostgreSQL connection without SSL). |
| **Gap** | Zero encryption at rest. All stored data (device telemetry, user credentials, API keys, alarm history) is stored in plaintext on disk. Does not meet basic compliance requirements for data protection. |
| **Recommendation** | After migrating to managed databases: enable encryption at rest with **AWS KMS** customer-managed keys on Aurora PostgreSQL, DynamoDB, ElastiCache, and any S3 buckets. Enable encryption in transit for all database connections. For interim Docker deployment, enable PostgreSQL TDE or volume encryption. |
| **Evidence** | `docker/docker-compose.postgres.yml` (unencrypted volume), `docker/docker-compose.hybrid.yml` (unencrypted Cassandra volume), `docker/docker-compose.valkey.yml` (unencrypted Valkey volume) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JWT token-based authentication configured for all API endpoints. `thingsboard.yml` defines JWT parameters: `tokenExpirationTime: 9000` (2.5 hours), `refreshTokenExpTime: 604800` (1 week), `tokenIssuer: thingsboard.io`. API keys are supported with configurable prefix (`tb_`) and key length (64 bytes). OAuth2 login processing is configured (`loginProcessingUrl: /login/oauth2/code/`). The Swagger config distinguishes security (`/api/.*`) from non-security paths (`/api/(?:noauth|v1)/.*`). Spring Security handles authentication at the application level. The device transport API (`/api/v1/`) uses device tokens for authentication. Rate limiting is implemented in HAProxy at the IP level, not per-token. |
| **Gap** | Token-based auth on all endpoints but authentication is at the application level, not at the gateway. No API Gateway authorizer. Rate limiting is IP-based in HAProxy, not per-API-key. Internal services between containers have no mutual TLS or auth. |
| **Recommendation** | When deploying API Gateway (preferred), configure JWT authorizer at the gateway level for REST API endpoints. Implement per-API-key throttling. Add mutual TLS between internal services on EKS using a service mesh (Istio or AWS App Mesh). |
| **Evidence** | `application/src/main/resources/thingsboard.yml` (security.jwt, security.oauth2, security.api_key sections), `docker/haproxy/config/haproxy.cfg` (IP-based rate limiting) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OAuth2 integration with external identity providers is configured. `thingsboard.yml` includes OAuth2 login processing URL and GitHub mapper (`emailUrl: https://api.github.com/user/emails`). The platform supports configurable OAuth2 providers via the admin UI. However, SSO is configuration-dependent (not enabled by default). The platform manages its own user authentication system with JWT tokens alongside OAuth2 federation. Local authentication (username/password) remains the primary mechanism. |
| **Gap** | OAuth2 federation exists but is not the primary authentication path. Local authentication with platform-managed credentials is the default. SSO not enabled by default. Some legacy auth flows may remain alongside OAuth2. |
| **Recommendation** | When migrating to AWS, integrate with **Amazon Cognito** user pools for centralized identity management. Configure Cognito as the OAuth2 provider for ThingsBoard. Enable SSO across the platform. Migrate local user accounts to Cognito for unified identity management. |
| **Evidence** | `application/src/main/resources/thingsboard.yml` (security.oauth2 section, githubMapper configuration) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **Plaintext credentials committed to the repository.** Critical findings: (1) `docker/tb-node.postgres.env` contains `SPRING_DATASOURCE_PASSWORD=postgres` in plaintext, (2) `docker/docker-compose.postgres.yml` has `POSTGRES_PASSWORD: postgres` in plaintext, (3) `docker/docker-compose.hybrid.yml` has `POSTGRES_PASSWORD: postgres` in plaintext, (4) `thingsboard.yml` contains default JWT signing key `JWT_TOKEN_SIGNING_KEY:thingsboardDefaultSigningKey`, (5) `docker/docker-compose.valkey.yml` uses `ALLOW_EMPTY_PASSWORD=yes`, (6) `docker/.env` is committed to git. HAProxy stats auth is hardcoded (`stats auth admin:admin@123`). No AWS Secrets Manager, HashiCorp Vault, or any secrets management solution found. No rotation configured. |
| **Gap** | Plaintext credentials in multiple files committed to source control. Default/weak passwords used. No secrets management system. No credential rotation. This is a deployment-blocking security issue. |
| **Recommendation** | Immediately: externalize all credentials from committed files. Use **AWS Secrets Manager** for database credentials, JWT signing keys, and API keys with automated rotation. Use Kubernetes secrets (encrypted with KMS) on EKS for runtime secret injection. Remove all hardcoded credentials from Docker env files. Configure `.gitignore` to exclude `.env` files with real credentials. |
| **Evidence** | `docker/tb-node.postgres.env` (SPRING_DATASOURCE_PASSWORD=postgres), `docker/docker-compose.postgres.yml` (POSTGRES_PASSWORD: postgres), `docker/.env` (committed to git), `docker/haproxy/config/haproxy.cfg` (stats auth admin:admin@123), `application/src/main/resources/thingsboard.yml` (JWT_TOKEN_SIGNING_KEY default) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Dockerfiles use `apt-get install` for package installation (`msa/tb-node/docker/Dockerfile` installs `libharfbuzz0b fontconfig fonts-dejavu-core`). Base images are not hardened — no CIS benchmark images, no Bottlerocket, no distroless. The Dockerfile does create a non-root user (`USER ${pkg.user}`) and removes apt cache (`rm -rf /var/lib/apt/lists/*`), which are good practices. No SSM Patch Manager, no AWS Inspector, no Snyk, no vulnerability scanning of any kind. No EC2 Image Builder pipelines. No evidence of systematic patching strategy beyond CVE-driven dependency bumps in `pom.xml` (several CVE fix comments visible). |
| **Gap** | No systematic patching or vulnerability scanning. Base images not hardened. No automated vulnerability detection for container images or OS packages. |
| **Recommendation** | Enable **Amazon ECR image scanning** for all container images. Integrate **AWS Inspector** or **Snyk** for runtime vulnerability scanning. Use hardened base images (Amazon Linux 2023 or Bottlerocket for EKS nodes). Implement automated base image rebuilds on security patch releases. |
| **Evidence** | `msa/tb-node/docker/Dockerfile` (apt-get install, non-root USER), `pom.xml` (CVE fix comments for jackson-bom, netty, lz4, zookeeper, commons-lang3, nimbus-jose-jwt) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools integrated into the CI/CD pipeline. No Dependabot configuration (`.github/dependabot.yml` not found). No `npm audit` or `pip-audit` steps in any workflow. No SonarQube, Semgrep, or CodeGuru configuration. No Snyk policy file (`.snyk` not found). No container scanning configured. The only GitHub Actions workflows perform configuration validation and license header formatting — no security validation whatsoever. The `pom.xml` does have manual CVE-driven version overrides (several `TODO: remove when fixed` comments), indicating reactive manual patching rather than automated scanning. |
| **Gap** | Zero automated security scanning in the pipeline. No dependency scanning, no SAST, no container scanning. Vulnerability management is entirely manual and reactive (CVE comments in pom.xml). |
| **Recommendation** | Immediately: add **Dependabot** configuration for automated dependency vulnerability alerts. Add **Amazon CodeGuru Reviewer** or **SonarQube** for SAST in the CI pipeline. Configure **ECR image scanning** for container vulnerability detection. Add `mvn dependency-check:check` (OWASP Dependency Check) as a CI pipeline stage. Block merges on critical vulnerability findings. |
| **Evidence** | `.github/workflows/` (no security scanning workflows), absence of `.github/dependabot.yml`, absence of `.snyk`, `pom.xml` (manual CVE version overrides with TODO comments) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No OpenTelemetry SDK in dependency manifests, no X-Ray SDK, no Jaeger or Zipkin configuration. The `pom.xml` has no OpenTelemetry dependencies. Micrometer metrics (via Spring Boot Actuator) are present for Prometheus endpoint exposure, but these provide metrics — not traces. No `traceparent` or `X-Amzn-Trace-Id` header propagation across service boundaries. Given the multi-service architecture (tb-core → rule-engine → transports via Kafka), debugging cross-service request flows currently requires manual log correlation. |
| **Gap** | No distributed tracing across service boundaries. Debugging failures in the telemetry pipeline (device → transport → Kafka → rule engine → core) is guesswork. Cannot measure end-to-end latency for device message processing. |
| **Recommendation** | Instrument all services with **AWS X-Ray** or **OpenTelemetry** SDK. Add trace ID propagation to Kafka message headers for cross-service tracing. On EKS, use the **AWS Distro for OpenTelemetry (ADOT)** collector as a sidecar. Correlate traces with Prometheus metrics in **Amazon CloudWatch** or **Grafana**. |
| **Evidence** | `pom.xml` (no OpenTelemetry dependencies), `docker/tb-node.env` (METRICS_ENABLED but no tracing), `docker/monitoring/prometheus/prometheus.yml` (metrics only) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking, no SLO configuration files, no formal definition of acceptable service levels for any user journey. Prometheus metrics are configured for scraping but used for dashboards only — no SLO-based alerting. No CloudWatch alarms on p99/p95 latency. The platform has implicit performance expectations (rule engine response timeout: 10000ms) but these are not formal SLOs with error budget tracking. |
| **Gap** | No formal SLOs for critical IoT user journeys: device telemetry ingestion latency, alarm processing time, REST API response time, MQTT connection establishment time. Cannot measure whether the platform meets user expectations or is degrading. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Device telemetry ingestion p99 < 500ms, (2) Alarm creation/acknowledgment p99 < 1s, (3) REST API availability > 99.9%, (4) MQTT connection success rate > 99.95%. Use **Amazon CloudWatch** SLO monitoring or Grafana SLO feature. Implement error budget tracking to prioritize operational improvements. |
| **Evidence** | Absence of SLO configuration files, `application/src/main/resources/thingsboard.yml` (DEFAULT_RULE_ENGINE_RESPONSE_TIMEOUT: 10000 — implicit performance target, not formal SLO) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus metrics endpoint is enabled (`METRICS_ENABLED=true`, `METRICS_ENDPOINTS_EXPOSE=prometheus` in `tb-node.env`). Micrometer/Spring Boot Actuator exposes metrics via `/actuator/prometheus`. Grafana dashboards exist for domain-specific metrics: `rule_engine_metrics.json`, `rule_engine_latency.json`, `transport_metrics.json`, `transport_connections.json`, `db_metrics.json`, `edqs.json`, `attributes_cache.json`, `core_js_tbel_metrics.json`. The `common/stats/` module provides a custom stats framework. However, these are primarily **infrastructure and application performance metrics** — rule engine throughput, transport connections, DB query times — not business outcome metrics (devices provisioned per hour, alarm resolution time, tenant onboarding success rate). |
| **Gap** | Rich application performance metrics but limited business outcome metrics. Dashboards focus on system health (queue depth, connection count, DB latency) rather than business KPIs (successful device onboarding rate, telemetry delivery success rate, alarm MTTR). |
| **Recommendation** | Add business metrics: devices provisioned per hour, telemetry messages processed per tenant, alarm mean-time-to-resolution, API error rate by endpoint category. Publish custom CloudWatch metrics for business KPIs alongside existing Prometheus infrastructure metrics. |
| **Evidence** | `docker/tb-node.env` (METRICS_ENABLED=true), `docker/monitoring/grafana/provisioning/dashboards/` (11 dashboard JSON files), `docker/monitoring/prometheus/prometheus.yml` (scrape targets for all services) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Grafana dashboards exist for monitoring key metrics across all services. Prometheus scrapes metrics from all ThingsBoard services at 15s intervals (5s for Prometheus self-monitoring). The Grafana provisioning includes datasource configuration and 11 pre-built dashboards. However, no anomaly detection is configured — Grafana dashboards are for visualization only, with no alerts defined in the provisioned dashboard JSON files. No Prometheus alert rules (`alerting:` section absent from `prometheus.yml`). No Alertmanager configuration. No CloudWatch anomaly detection. Monitoring is passive visualization, not active alerting. |
| **Gap** | Static dashboards only — no anomaly detection, no alerting rules, no Alertmanager. Operators must manually watch dashboards to detect issues. No automatic notification on error rate spikes, latency degradation, or connection drops. |
| **Recommendation** | Configure **Prometheus Alertmanager** with alert rules for critical metrics: rule engine queue depth > threshold, transport connection drop rate, database query latency p99, error rate spikes. On AWS, use **CloudWatch anomaly detection** for error rates and latency with PagerDuty/OpsGenie integration for incident notification. |
| **Evidence** | `docker/monitoring/prometheus/prometheus.yml` (no alerting section), `docker/monitoring/grafana/provisioning/dashboards/` (dashboards without alert definitions), `docker/docker-compose.prometheus-grafana.yml` (no Alertmanager service) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No canary, blue/green, or rolling deployment strategy configured. Docker Compose uses `restart: always` as the only recovery mechanism. Deployments are executed via shell scripts: `docker-start-services.sh`, `docker-stop-services.sh`, `docker-upgrade-tb.sh`, `docker-update-service.sh`. These scripts perform direct-to-production deployment with service restart — no staged rollout, no traffic shifting, no automated rollback on failure. No CodeDeploy, no Helm canary, no Argo Rollouts, no Lambda traffic shifting configuration. |
| **Gap** | Direct-to-production deployment with manual shell scripts. No staged rollout eliminates the window to catch regressions before they affect all connected IoT devices. A bad deployment could disconnect all devices simultaneously. |
| **Recommendation** | On EKS (preferred), implement **Helm-based deployments** with canary rollouts using **Argo Rollouts** or **Flagger**. Configure health check-based automated rollback. For transport services, implement connection-drain-aware rolling updates to prevent device disconnections during deployment. |
| **Evidence** | `docker/docker-compose.yml` (restart: always), `docker/docker-start-services.sh`, `docker/docker-stop-services.sh`, `docker/docker-upgrade-tb.sh` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Significant integration testing infrastructure exists: **128 black-box test files** in `msa/black-box-tests/` using TestNG (7.10.1) with Testcontainers (1.21.4) for container-based integration testing. The test suite includes Allure reporting (2.27.0), WebDriver Manager (6.1.0) for UI testing, and Docker-based test environments. The main application has **758 test files** including unit and integration tests. The `pom.xml` configures Maven Surefire Plugin (3.5.4) for test execution. Mock Server (5.15.0) and DBUnit (2.7.3) are used for test isolation. However, these tests are not run in any CI pipeline — the GitHub Actions workflows don't execute tests. |
| **Gap** | Comprehensive test suites exist but are NOT run in CI. Integration tests require manual execution. No automated quality gates before deployment. Black-box tests are available but not integrated into the delivery pipeline. |
| **Recommendation** | Integrate the existing test suites into the CI/CD pipeline. Run unit tests on every PR, integration tests on merge to main. Use Testcontainers in GitHub Actions for containerized integration testing. Add black-box test execution as a post-deployment verification step. |
| **Evidence** | `msa/black-box-tests/` (128 Java test files), `pom.xml` (testcontainers.version=1.21.4, testng.version=7.10.1, allure-testng.version=2.27.0, mock-server.version=5.15.0), `.github/workflows/` (no test execution steps) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns found. No SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The `security.md` describes a vulnerability reporting process (email security@thingsboard.io) but not operational incident response. No on-call rotation configuration, no PagerDuty/OpsGenie integration. Incident response is entirely ad hoc — manual investigation using Docker logs and Grafana dashboards. |
| **Gap** | No runbooks, no automated remediation, no incident response playbooks. When a service fails, operators must manually SSH into the Docker host, inspect logs, and restart services. No automated escalation or notification. |
| **Recommendation** | Create runbooks for common incidents: (1) Database connection exhaustion, (2) Kafka consumer lag buildup, (3) Transport service overload, (4) Rule engine processing backlog. On AWS, use **SSM Automation** for automated remediation. Use **AWS Incident Manager** for structured incident response with escalation paths. |
| **Evidence** | `security.md` (vulnerability reporting only, not operational incident response), absence of runbook files, absence of SSM documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Domain-specific Grafana dashboards are provisioned under `docker/monitoring/grafana/provisioning/dashboards/`: transport metrics, rule engine metrics, DB metrics, EDQS, attributes cache, core JS/TBEL metrics, single service metrics, and separate dashboards for hybrid DB mode. This shows intentional observability design per service domain. However, no CODEOWNERS file exists for observability configurations. No named alarm owners. No team attribution on dashboards or alerts. No SLO definitions tied to specific teams. |
| **Gap** | Good dashboard coverage per service domain but no ownership attribution. No CODEOWNERS for monitoring configs. No named owners on alarms. Ad hoc monitoring without clear accountability for observability gaps. |
| **Recommendation** | Create a CODEOWNERS file with team ownership for `docker/monitoring/` observability configurations. Assign named owners to each Grafana dashboard and alarm definition. Define per-service observability contracts specifying which metrics, dashboards, and alerts each team owns. |
| **Evidence** | `docker/monitoring/grafana/provisioning/dashboards/` (11 domain-specific dashboards), absence of CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging found anywhere. No cloud IaC means no opportunity for resource tags. Docker Compose services have service names and labels but no cost allocation, ownership, or environment tags. No `default_tags` in any Terraform provider (no Terraform exists). No `tags` on any cloud resources. No Config rules for tag enforcement. No Tag Policies. |
| **Gap** | No resource tagging. Cannot track costs per service, identify resource ownership, or distinguish environments. When migrating to AWS, this must be established from the start to enable cloud financial management. |
| **Recommendation** | Establish a tagging standard before AWS migration. Required tags: `Environment` (dev/staging/prod), `Service` (tb-core, tb-rule-engine, transport-mqtt, etc.), `Owner` (team name), `CostCenter`, `Project` (thingsboard). Enforce via IaC `default_tags` and AWS Tag Policies in Organizations. |
| **Evidence** | Absence of any cloud resource tags, absence of IaC with tagging configuration |

---

## Learning Materials

### Triggered Pathway Learning Resources

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

### Additional Recommended Resources

| Topic | Resource |
|-------|----------|
| **EKS (preferred compute platform)** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Cloud Design Patterns** | [AWS Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | APP-Q1, INF-Q4, APP-Q6, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q6 | Root Maven POM — Java 25, Spring Boot 3.5.12, AWS SDK v1 (1.12.701), Kafka 3.9.1, Langchain4j 1.8.0-TB, Testcontainers, CVE fix comments |
| `ui-ngx/package.json` | APP-Q1 | Angular 20 frontend dependencies (TypeScript 5.9.3) |
| `docker/docker-compose.yml` | INF-Q1, INF-Q7, INF-Q9, OPS-Q5, APP-Q2 | Main service topology — 18+ services, static replicas, HAProxy entry point, ZooKeeper |
| `docker/docker-compose.postgres.yml` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q2, SEC-Q5 | PostgreSQL 16 Docker container with hardcoded credentials |
| `docker/docker-compose.hybrid.yml` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q2, SEC-Q5 | Cassandra 5.0 Docker container, shared PostgreSQL |
| `docker/docker-compose.kafka.yml` | INF-Q4 | Self-managed Kafka (bitnamilegacy/kafka:4.0) |
| `docker/docker-compose.valkey.yml` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q2, SEC-Q5 | Valkey 8.0 cache with ALLOW_EMPTY_PASSWORD=yes |
| `docker/docker-compose.prometheus-grafana.yml` | OPS-Q4 | Prometheus v3.1.0 + Grafana monitoring stack |
| `docker/.env` | INF-Q1, SEC-Q5 | Environment configuration committed to git |
| `docker/tb-node.env` | OPS-Q1, OPS-Q3, APP-Q6 | Service configuration — ZooKeeper enabled, metrics enabled |
| `docker/tb-node.postgres.env` | INF-Q2, SEC-Q5 | Plaintext PostgreSQL credentials (SPRING_DATASOURCE_PASSWORD=postgres) |
| `docker/kafka.env` | INF-Q4, APP-Q6 | Kafka KRaft configuration |
| `docker/queue-kafka.env` | INF-Q4 | Kafka queue type and server configuration |
| `docker/haproxy/config/haproxy.cfg` | INF-Q5, INF-Q6, APP-Q5, SEC-Q3, SEC-Q5 | HAProxy load balancer — routing, rate limiting, TLS, trustlist/blocklist, hardcoded stats auth |
| `application/src/main/resources/thingsboard.yml` | INF-Q3, INF-Q4, APP-Q2, APP-Q4, APP-Q5, SEC-Q3, SEC-Q4, SEC-Q5, OPS-Q2 | Main application config — JWT, OAuth2, Swagger, queue, service type, rule engine timeout |
| `msa/tb-node/docker/Dockerfile` | INF-Q1, SEC-Q6 | TB-node Docker image — apt-get install, non-root USER |
| `msa/transport/mqtt/docker/Dockerfile` | INF-Q1 | MQTT transport Docker image |
| `.github/workflows/check-configuration-files.yml` | INF-Q11, SEC-Q7 | Config validation workflow — no build/test/deploy |
| `.github/workflows/license-header-format.yml` | INF-Q11, SEC-Q7 | License header formatting workflow — no security scanning |
| `dao/src/main/resources/sql/schema-functions.sql` | DATA-Q4, DATA-Q2 | 6 alarm management stored functions (PL/pgSQL) |
| `dao/src/main/resources/sql/schema-ts-psql.sql` | DATA-Q4, DATA-Q1 | 7 time-series management functions, partition management |
| `dao/src/main/resources/sql/schema-timescale.sql` | DATA-Q4 | TimescaleDB-specific functions |
| `dao/src/main/resources/sql/schema-entities.sql` | DATA-Q1 | Entity schema definitions |
| `dao/src/main/java/` | DATA-Q2 | Centralized DAO layer implementations |
| `common/dao-api/` | DATA-Q2 | DAO interface definitions |
| `common/queue/src/main/java/` | APP-Q3, INF-Q4 | Queue abstraction layer (TbQueueProducer, TbQueueConsumer) |
| `common/queue/src/main/java/.../discovery/ZkDiscoveryService.java` | APP-Q6 | ZooKeeper-based service discovery implementation |
| `rule-engine/rule-engine-components/src/main/java/` | INF-Q3, APP-Q4 | Rule engine processing, AI node (TbAiNode.java) |
| `common/data/src/main/java/.../ai/` | Move to AI pathway | Langchain4j AI model configurations (Bedrock, OpenAI, Anthropic, etc.) |
| `docker/monitoring/prometheus/prometheus.yml` | OPS-Q1, OPS-Q3, OPS-Q4 | Prometheus scrape configuration for all services |
| `docker/monitoring/grafana/provisioning/dashboards/` | OPS-Q3, OPS-Q4, OPS-Q8 | 11 Grafana dashboard JSON files — transport, rule engine, DB, EDQS metrics |
| `msa/black-box-tests/` | OPS-Q6 | 128 integration test files (TestNG + Testcontainers) |
| `security.md` | OPS-Q7 | Security vulnerability reporting policy |
| `docker/docker-start-services.sh` | OPS-Q5 | Manual deployment shell script |
| `docker/docker-upgrade-tb.sh` | OPS-Q5 | Manual upgrade shell script |
| `README.md` | Quick Agent Wins | Repository documentation |
