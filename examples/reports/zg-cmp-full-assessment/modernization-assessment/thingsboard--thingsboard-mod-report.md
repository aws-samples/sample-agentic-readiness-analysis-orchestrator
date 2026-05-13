# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | thingsboard |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, iot, platform |
| **Context** | Open-source IoT platform for device management, data collection, and visualization. |
| **Overall Score** | **2.17 / 4.0** |

**Archetype Justification**: ThingsBoard has persistent state (PostgreSQL, Cassandra, Valkey), exposes CRUD operations on business entities (devices, assets, dashboards, alarms, customers), and combines orchestration (Rule Engine) with event processing (multi-protocol IoT transport). Classified as `stateful-crud` — the conservative default that applies the strictest rubric without false downgrades for this hybrid platform.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.36 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 3.00 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **2.17 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q2: Managed Databases | 1 | All databases (PostgreSQL, Cassandra, Valkey) are self-managed in Docker containers with no managed cloud services. | High operational burden — manual patching, backup, scaling. Blocks Managed Databases pathway. |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found — no Terraform, CloudFormation, or CDK. All infrastructure is Docker Compose definitions. | Non-reproducible infrastructure, manual provisioning, no disaster recovery automation. Triggers Modern DevOps pathway. |
| 3 | INF-Q11: CI/CD Automation | 1 | No build/test/deploy pipeline. GitHub Actions limited to config validation and license formatting. | Manual deployments, no automated quality gates, slow iteration cycles. Triggers Modern DevOps pathway. |
| 4 | SEC-Q2: Encryption at Rest | 1 | No encryption-at-rest configuration for any data store. No KMS integration. | Sensitive IoT telemetry and customer data stored without encryption — compliance and security risk. |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumentation. No OpenTelemetry or X-Ray. Only Prometheus metrics. | Cannot trace requests across tb-core, rule-engine, and transport services — blind to cross-service failures. |

---

## Quick Agent Wins

ThingsBoard already has AI framework integration via langchain4j (v1.8.0-TB) with `AiChatModelService`, `AiModelController`, and `Langchain4jChatModelConfigurerImpl` supporting multiple providers (OpenAI, Bedrock, Anthropic, Gemini, Mistral, Ollama). The following wins build on this existing AI foundation:

### API-aware Agent

- **Prerequisite:** APP-Q5 >= 2 ✅ — SpringDoc OpenAPI (v2.8.8TB) configured with Swagger UI at `/api/**`. `SwaggerConfiguration.java` present. Over 60 REST controllers with structured JSON responses.
- **What it enables:** An agent that discovers and invokes ThingsBoard REST API endpoints as tools — querying devices, reading telemetry, managing alarms, triggering RPC commands. The existing langchain4j integration provides the foundation for connecting AI models to these API endpoints.
- **Additional steps:** Generate a static OpenAPI spec file for offline agent tool discovery. Ensure all controller endpoints have complete `@Operation` annotations for agent-friendly descriptions.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 >= 2 ✅ — Centralized DAO layer in `dao/` with well-structured packages per entity (alarm, asset, device, customer, dashboard, etc.). JPA/Hibernate for PostgreSQL, dedicated Cassandra DAO.
- **What it enables:** A natural language to SQL/query agent that leverages the clear schema structure to answer questions like "How many devices are offline?" or "Show me alarms from the last 24 hours." The existing AI service infrastructure can be extended to support data query capabilities.
- **Additional steps:** Create a schema documentation layer mapping entity relationships for the agent. Define read-only query boundaries to prevent unintended data modifications.
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists ✅ — `README.md`, extensive `thingsboard.yml` (2,208 lines with detailed comments), Swagger API docs, `security.md`, `pull_request_template.md`, inline code documentation across the codebase.
- **What it enables:** A knowledge agent that indexes ThingsBoard documentation to answer developer and operator questions about configuration, deployment, rule engine setup, and API usage. The existing langchain4j integration provides the RAG foundation.
- **Additional steps:** Index `thingsboard.yml` comments and README into a vector store. Consider using Amazon Bedrock (per preferences) with Knowledge Bases for managed RAG.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 >= 2 ✅ — ThingsBoard Rule Engine provides workflow orchestration via rule chains that process device telemetry through configurable processing steps.
- **What it enables:** An agent that monitors rule chain execution, suggests optimizations for underperforming rule chains, and assists in configuring new rule chain workflows through natural language instructions. The existing AI model controller can be extended to interact with rule chain management APIs.
- **Additional steps:** Expose rule chain management APIs as agent tools. Define safety boundaries for agent-initiated rule chain modifications (e.g., staging environment only).
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — application has modular architecture with separate deployment units. Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 2 but 13 Dockerfiles exist. Contextual guard: application is already containerized. |
| 3 | Move to Open Source | Not Triggered | — | — | PostgreSQL and Cassandra are already open-source engines. No commercial database engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed). DATA-Q3 = 3 (versions pinned but no managed lifecycle). |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4 = 2 (self-managed Kafka). Data processing workloads exist (Rule Engine, telemetry processing pipeline). |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 1 (no CI/CD pipeline). OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 2 (tests exist but not in CI). |
| 7 | Move to AI | Not Triggered | — | — | AI frameworks already present — langchain4j v1.8.0-TB with multi-provider support (Bedrock, OpenAI, Anthropic, Gemini, Mistral, Ollama). |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 Finding):**
All databases are self-managed in Docker containers:
- **PostgreSQL 16** — Primary relational database for entities and timeseries (`docker-compose.postgres.yml`, image: `postgres:16`). POSTGRES_PASSWORD set in plain text.
- **Cassandra 5.0.4** — Alternative timeseries database for hybrid mode (`docker-compose.cassandra.volumes.yml`). Self-managed with external volume.
- **Valkey (Redis fork) 8.0** — Caching layer (`docker-compose.valkey.yml`, image: `bitnamilegacy/valkey:8.0`). Single-node, no authentication (`ALLOW_EMPTY_PASSWORD=yes`).

**Engine Versions and EOL Status (DATA-Q3 Finding):**
- PostgreSQL 16: Current, supported until November 2028. Explicitly pinned.
- Cassandra 5.0.4: Current LTS. Explicitly pinned in pom.xml.
- Valkey 8.0: Current. Explicitly pinned.

**Data Access Patterns (DATA-Q2 Finding):**
Centralized DAO layer in `dao/` module with clear entity-based package structure. JPA/Hibernate for PostgreSQL, dedicated NoSQL DAO for Cassandra. `ThingsboardPostgreSQLDialect.java` provides custom dialect support.

**Recommended Migration Targets (respecting preferences: prefer aurora, dynamodb):**
- **PostgreSQL → Amazon Aurora PostgreSQL-Compatible**: Drop-in replacement with Multi-AZ automatic failover, automated backups, PITR, and auto-scaling read replicas. Aurora's PostgreSQL compatibility means minimal application changes — the existing JPA/Hibernate layer and custom PostgreSQL dialect will work with Aurora.
- **Cassandra → Amazon DynamoDB**: For timeseries workloads in hybrid mode, DynamoDB offers fully managed, serverless NoSQL with on-demand capacity. The existing NoSQL DAO abstraction in `dao/nosql/` facilitates the migration path. Alternatively, Amazon Keyspaces (Cassandra-compatible) provides a lower-migration-effort path.
- **Valkey → Amazon ElastiCache for Valkey**: Managed caching with Multi-AZ, automatic failover, and encryption. The existing cache configuration in `thingsboard.yml` uses environment variable substitution, making endpoint migration straightforward.

**Representative AWS Services:** Aurora PostgreSQL, DynamoDB, ElastiCache for Valkey, Amazon Keyspaces
**Migration Tools:** AWS Database Migration Service (DMS), AWS Schema Conversion Tool (SCT)

**Note on Stored Procedures:** `schema-functions.sql` contains 6 PL/pgSQL functions for alarm management. These are compatible with Aurora PostgreSQL and do not require conversion. However, consider extracting alarm CRUD logic to the application layer long-term to reduce database coupling.

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Streaming/Messaging Infrastructure (INF-Q4 Finding):**
Self-managed Kafka (bitnami image `bitnamilegacy/kafka:4.0`) running in Docker with KRaft mode. Zookeeper for ThingsBoard service discovery (separate from Kafka). Kafka serves as the primary message bus for:
- Inter-service communication (tb-core ↔ tb-rule-engine ↔ transport nodes)
- Telemetry data pipeline (device → transport → core → rule engine)
- Queue abstraction (`common/queue/kafka/`) supporting topic-based routing

**Data Processing Workloads:**
- **Rule Engine**: Processes device telemetry through configurable rule chains — filtering, transformation, enrichment, alerting, and external system integration.
- **Telemetry Pipeline**: High-throughput ingestion from IoT devices via MQTT, HTTP, CoAP, LwM2M, and SNMP transports.
- **JS Executor**: Processes JavaScript-based transformations within rule chains (10 static replicas in Docker Compose).

**Recommended Managed Analytics Targets (respecting preferences: prefer eventbridge; avoid self-managed-kafka):**
- **Kafka → Amazon MSK Serverless**: Managed Kafka-compatible service requiring no broker management, auto-scaling, patching, or capacity planning. The existing `common/queue/kafka/` abstraction uses standard Kafka client APIs, enabling a straightforward migration by updating `TB_KAFKA_SERVERS` configuration. MSK Serverless eliminates the self-managed Kafka infrastructure that the preferences explicitly ask to avoid.
- **Event-Driven Integration → Amazon EventBridge**: For rule engine actions that trigger external system integrations (email, SMS, HTTP webhooks), EventBridge provides managed event routing with filtering, transformation, and delivery guarantees. This can complement or replace Kafka for specific inter-service communication patterns.
- **Telemetry Analytics → Amazon Kinesis Data Streams**: For real-time telemetry analytics beyond the rule engine (e.g., anomaly detection on device metrics), Kinesis provides managed streaming with built-in analytics capabilities.

**Representative AWS Services:** Amazon MSK Serverless, Amazon EventBridge, Amazon Kinesis Data Streams, AWS Glue (for ETL if needed)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 Finding):**
No Infrastructure as Code files found in the repository. No Terraform `.tf` files, no CloudFormation templates, no CDK constructs, no Helm charts, no Kubernetes manifests. All infrastructure is defined via Docker Compose files (`docker/docker-compose*.yml`) which configure local development/deployment environments but do not provision cloud infrastructure.

**Current CI/CD State (INF-Q11 Finding):**
GitHub Actions workflows exist but are limited to auxiliary tasks:
- `check-configuration-files.yml`: Validates YAML configuration files on PR
- `license-header-format.yml`: Formats license headers on push to master
- `atx-transform.yml`: ATX-specific transformation workflow

No build, test, or deploy pipeline stages exist. No automated testing in CI. No deployment automation.

**Deployment Strategy Gaps (OPS-Q5 Finding):**
Manual deployment via shell scripts (`docker-start-services.sh`, `docker-stop-services.sh`, `docker-upgrade-tb.sh`). No blue/green, canary, or rolling deployment strategy. Direct-to-production deployment model.

**Testing Gaps (OPS-Q6 Finding):**
Black-box integration tests exist (`msa/black-box-tests/` with TestNG and Testcontainers) but are not integrated into any CI pipeline. Unit tests exist across modules but are not run in CI.

**Recommended DevOps Toolchain (respecting preferences: prefer eks):**
1. **IaC Adoption**: Define all AWS infrastructure using AWS CDK (TypeScript) or CloudFormation:
   - EKS cluster for container orchestration (per preferences: prefer eks)
   - Aurora PostgreSQL for database
   - MSK Serverless for messaging
   - ElastiCache for caching
   - API Gateway for API entry point (per preferences: prefer api-gateway)
2. **CI/CD Pipeline**: Extend GitHub Actions with comprehensive pipeline stages:
   - **Build**: Maven build + Docker image creation, push to Amazon ECR
   - **Test**: Run unit tests + integration tests (leverage existing black-box-tests with Testcontainers)
   - **Security Scan**: Add Dependabot, SAST (SonarQube/Semgrep), container scanning (ECR image scanning)
   - **Deploy**: EKS deployment with ArgoCD or AWS CodeDeploy, canary/blue-green strategy
   - **Rollback**: Automated rollback on health check failure
3. **Deployment Strategy**: Implement canary deployments for EKS workloads using Argo Rollouts or AWS App Mesh traffic shifting.

**Representative AWS Services:** Amazon EKS, AWS CDK, Amazon ECR, AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy, Amazon CloudWatch

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard services are containerized with 13 Dockerfiles under `msa/` (tb-node, js-executor, web-ui, edqs, monitoring, vc-executor, transport/mqtt, transport/http, transport/coap, transport/lwm2m, transport/snmp, tb/docker-postgres, tb/docker-cassandra). Docker Compose orchestrates all services locally with static replica counts. No ECS, EKS, Lambda, or Fargate definitions exist. All compute is self-managed Docker containers. |
| **Gap** | Containerized but running on self-managed Docker Compose with no managed container orchestration. No cloud compute platform (ECS/EKS/Fargate) defined. |
| **Recommendation** | Migrate to Amazon EKS (per preferences) for managed Kubernetes orchestration. Create Helm charts for each ThingsBoard service (tb-core, tb-rule-engine, transports, js-executor, web-ui). Leverage EKS managed node groups or Fargate profiles for compute. |
| **Evidence** | `msa/tb-node/docker/Dockerfile`, `msa/js-executor/docker/Dockerfile`, `msa/web-ui/docker/Dockerfile`, `msa/transport/mqtt/docker/Dockerfile`, `docker/docker-compose.yml` (13 service definitions with static replicas) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed Docker containers: PostgreSQL 16 (`docker-compose.postgres.yml`, image `postgres:16`), Cassandra (`docker-compose.cassandra.volumes.yml`), Valkey 8.0 (`docker-compose.valkey.yml`, image `bitnamilegacy/valkey:8.0`). POSTGRES_PASSWORD is set to `postgres` in plain text. Valkey runs with `ALLOW_EMPTY_PASSWORD=yes`. No RDS, Aurora, DynamoDB, or ElastiCache definitions. |
| **Gap** | All databases self-managed with no automated failover, no managed patching, no automated backups, and weak credentials. |
| **Recommendation** | Migrate to Aurora PostgreSQL (per preferences) for the primary database, DynamoDB (per preferences) or Amazon Keyspaces for timeseries in hybrid mode, and ElastiCache for Valkey for caching. Enable Multi-AZ, automated backups, and encryption at rest. |
| **Evidence** | `docker/docker-compose.postgres.yml` (POSTGRES_PASSWORD: postgres), `docker/docker-compose.cassandra.volumes.yml`, `docker/docker-compose.valkey.yml` (ALLOW_EMPTY_PASSWORD: yes) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard has its own Rule Engine for workflow orchestration — rule chains process device telemetry through configurable steps (filtering, transformation, enrichment, alerting). This is application-level orchestration built into the platform, not a dedicated managed orchestration service. The `rule-engine/` module contains rule engine components and API. No Step Functions, Temporal, MWAA, or other external orchestration services are used. |
| **Gap** | Workflow orchestration is application-level code within the Rule Engine. No dedicated managed orchestration service for complex multi-step workflows. Error handling and retry logic are implemented in application code rather than declarative workflow definitions. |
| **Recommendation** | For stateful-crud archetype: consider adopting AWS Step Functions for complex multi-step workflows that extend beyond the Rule Engine (e.g., device provisioning workflows, multi-system integrations, data migration jobs). The Rule Engine is appropriate for telemetry processing but external orchestration would benefit administrative and operational workflows. |
| **Evidence** | `rule-engine/rule-engine-api/`, `rule-engine/rule-engine-components/`, `application/src/main/resources/thingsboard.yml` (queue configuration for rule engine topics) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Self-managed Kafka (bitnami image `bitnamilegacy/kafka:4.0`) is the primary message bus, running in KRaft mode. `docker-compose.kafka.yml` defines the Kafka service. The `common/queue/kafka/` module provides a Kafka queue abstraction. AWS SQS and SNS SDK dependencies (`aws-java-sdk-sqs`, `aws-java-sdk-sns`) exist in `pom.xml`, indicating the queue abstraction supports multiple backends. Default configuration is `TB_QUEUE_TYPE=kafka` (from `docker/.env`). The queue also supports `in-memory` mode. Zookeeper is used for ThingsBoard service discovery (separate from Kafka). |
| **Gap** | Primary messaging infrastructure is self-managed Kafka requiring manual patching, scaling, and monitoring. Despite having AWS SDK dependencies for SQS/SNS, the default and deployed configuration uses self-managed Kafka. |
| **Recommendation** | Migrate to Amazon MSK Serverless (preferred over self-managed Kafka per preferences). The existing Kafka client abstraction in `common/queue/kafka/` uses standard Kafka APIs, enabling migration by updating `TB_KAFKA_SERVERS` to point to MSK endpoints. For event-driven patterns beyond messaging, consider Amazon EventBridge (per preferences) for rule engine actions triggering external integrations. |
| **Evidence** | `docker/docker-compose.kafka.yml` (bitnamilegacy/kafka:4.0), `docker/kafka.env` (KRaft config), `docker/.env` (TB_QUEUE_TYPE=kafka), `common/queue/src/main/java/org/thingsboard/server/queue/kafka/`, `pom.xml` (aws-java-sdk-sqs, aws-java-sdk-sns dependencies) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation definitions found. No IaC exists. Docker Compose services communicate on a flat Docker network. HAProxy load balancer exposes ports 80, 443, 1883, 7070, and 9999 directly. Kafka exposes port 9092. PostgreSQL exposes port 5432. No network isolation between database tier, application tier, and transport tier. |
| **Gap** | Services deployed with no network segmentation. All services are on a flat network with no private subnets, security groups, or NACLs. Database ports are exposed without isolation. |
| **Recommendation** | Define a VPC with private subnets for databases and application services, public subnets only for load balancers. Implement least-privilege security groups: databases accessible only from application tier, Kafka accessible only from ThingsBoard services. Use VPC endpoints for AWS services (S3, KMS, Secrets Manager). Consider API Gateway (per preferences) as the managed entry point with WAF. |
| **Evidence** | `docker/docker-compose.yml` (flat network, exposed ports 80/443/1883/7070/9999), `docker/docker-compose.postgres.yml` (port 5432 exposed), `docker/docker-compose.kafka.yml` (port 9092 exposed) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | HAProxy serves as the entry point and load balancer (`docker/docker-compose.yml`, image `thingsboard/haproxy-certbot:2.2.33-alpine`). It routes HTTP (80/443), MQTT (1883), and Edge RPC (7070) traffic to backend services. HAProxy configuration includes health checks for backend services. SSL termination via Let's Encrypt integration. However, no API throttling, request validation, or authentication at the gateway level — auth is handled by the application. |
| **Gap** | Load balancer present but minimal configuration — no throttling, no request validation at the gateway level, no API management capabilities. HAProxy provides routing and SSL termination but not API gateway functionality. |
| **Recommendation** | Deploy Amazon API Gateway (per preferences) for REST API endpoints with throttling, request validation, usage plans, and API key management. Keep HAProxy or switch to AWS Network Load Balancer for MQTT and CoAP transport protocols which require TCP/UDP passthrough. API Gateway provides native integration with Cognito for auth, WAF for security, and CloudWatch for monitoring. |
| **Evidence** | `docker/docker-compose.yml` (haproxy service with ports 80/443/1883/7070/9999), `docker/haproxy/` (configuration directory) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Docker Compose uses static replica counts: `js-executor` has `deploy: replicas: 10`, all other services have single instances (with 2 explicit instances for core, rule-engine, mqtt-transport, http-transport, web-ui, and vc-executor defined as separate service entries). No auto-scaling configuration exists. No dynamic scaling based on load, queue depth, or resource utilization. |
| **Gap** | All capacity is statically provisioned. No auto-scaling for any service. IoT platforms experience variable load (device connection bursts, telemetry spikes) that static provisioning cannot handle efficiently. |
| **Recommendation** | On EKS (per preferences), implement Horizontal Pod Autoscaler (HPA) for tb-core, tb-rule-engine, and transport services based on CPU/memory and custom metrics (queue depth, active connections). Configure Cluster Autoscaler or Karpenter for node-level scaling. For Aurora, enable auto-scaling read replicas. For ElastiCache, configure auto-scaling for cache nodes. |
| **Evidence** | `docker/docker-compose.yml` (deploy: replicas: 10 for js-executor, static service instances for all others) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found anywhere in the repository. No `backup_retention_period` settings, no backup plans, no snapshot policies. PostgreSQL data is stored in a Docker volume (`./tb-node/postgres:/var/lib/postgresql/data`). Cassandra uses an external Docker volume. No PITR configuration. No restore procedures documented. |
| **Gap** | No automated backup for any data store. Data loss risk is critical — a Docker volume failure would result in complete data loss for the IoT platform including device definitions, telemetry history, dashboards, and user configurations. |
| **Recommendation** | Migrating to Aurora PostgreSQL (per Managed Databases pathway) provides automated backups with configurable retention and PITR by default. For the interim, implement PostgreSQL `pg_dump` scheduled backups with S3 storage. For Cassandra, implement nodetool snapshot with S3 backup. Document and test restore procedures. |
| **Evidence** | `docker/docker-compose.postgres.yml` (volume mount, no backup config), `docker/docker-compose.cassandra.volumes.yml` (external volume, no backup) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Docker Compose defines multiple instances for some services (2 core nodes, 2 rule-engine nodes, 2 MQTT transport nodes, 2 HTTP transport nodes, 2 web-ui nodes, 2 vc-executor nodes), providing basic redundancy within a single host. However, there is no multi-AZ configuration, no cross-host failover, and all services run on a single Docker host. PostgreSQL is single-instance with no replication. Kafka is single-broker. |
| **Gap** | All resources are on a single host. No multi-AZ deployment, no cross-AZ failover. Single-instance PostgreSQL and single-broker Kafka are single points of failure. A host failure takes down the entire platform. |
| **Recommendation** | On EKS (per preferences), deploy across at least 2 Availability Zones. Aurora PostgreSQL provides automatic Multi-AZ failover. MSK Serverless provides built-in multi-AZ replication. ElastiCache supports Multi-AZ with automatic failover. Configure pod anti-affinity rules in EKS to spread ThingsBoard services across AZs. |
| **Evidence** | `docker/docker-compose.yml` (all services on single host), `docker/docker-compose.postgres.yml` (single PostgreSQL instance), `docker/docker-compose.kafka.yml` (single Kafka broker) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code files found in the repository. No Terraform `.tf` files, no CloudFormation templates, no AWS CDK constructs, no Helm charts, no Kubernetes manifests, no Kustomize files. All infrastructure configuration is in Docker Compose files (`docker/docker-compose*.yml`) which define local development and deployment environments but do not provision or manage cloud infrastructure. |
| **Gap** | 0% IaC coverage for cloud infrastructure. All infrastructure is manually created (ClickOps) or local Docker Compose. No reproducible cloud infrastructure, no environment consistency, no disaster recovery automation. |
| **Recommendation** | Adopt AWS CDK (TypeScript or Java) or Terraform to define all AWS infrastructure: VPC networking, EKS cluster, Aurora databases, MSK, ElastiCache, API Gateway, IAM roles, CloudWatch alarms. Start with the foundational networking and compute layers, then progressively add data and operational resources. Create Helm charts for ThingsBoard Kubernetes deployment. |
| **Evidence** | Repository-wide search for `.tf`, `cdk.json`, `template.yaml`, `template.json`, `Chart.yaml`, `kustomization.yaml` — none found. Only `docker/docker-compose*.yml` files define infrastructure. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Three GitHub Actions workflows exist in `.github/workflows/`: `check-configuration-files.yml` (validates YAML config on PR), `license-header-format.yml` (formats license headers on push to master/develop), `atx-transform.yml` (ATX-specific). None of these implement a build, test, or deploy pipeline. No Maven build stage, no automated test execution, no container image build, no deployment automation, no rollback capability. |
| **Gap** | No CI/CD pipeline for build, test, or deployment. All deployments are manual. Existing GitHub Actions are auxiliary (config validation, license formatting) and do not constitute a delivery pipeline. |
| **Recommendation** | Implement a comprehensive GitHub Actions CI/CD pipeline: (1) Build stage: Maven build + Docker image build + push to Amazon ECR. (2) Test stage: Run unit tests + integration tests (leverage existing `msa/black-box-tests/` with Testcontainers). (3) Security stage: Add SAST scanning, dependency vulnerability scanning, container image scanning. (4) Deploy stage: Deploy to EKS using Helm + ArgoCD or AWS CodeDeploy with canary strategy. (5) Rollback: Automated rollback on health check failure. |
| **Evidence** | `.github/workflows/check-configuration-files.yml`, `.github/workflows/license-header-format.yml`, `.github/workflows/atx-transform.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is Java 25 (`maven.compiler.source=25`) with Spring Boot 3.5.12 — first-class AWS SDK coverage, broad cloud-native tooling, and mature framework ecosystem. TypeScript (Angular 20.x) for the frontend UI (`ui-ngx/`). Node.js for JS executor and web-ui server. All three languages have excellent AWS SDK support and cloud-native tooling. |
| **Gap** | None — language choices are well-suited for cloud-native development on AWS. |
| **Recommendation** | No action needed. Java, TypeScript, and Node.js provide comprehensive AWS SDK coverage and cloud-native tooling. |
| **Evidence** | `pom.xml` (maven.compiler.source=25, spring-boot.version=3.5.12), `ui-ngx/package.json` (Angular 20.3.18, TypeScript 5.9.3), `msa/js-executor/` (Node.js) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | ThingsBoard has multiple independently deployable services — 13 Dockerfiles under `msa/` for: tb-core (2 instances), tb-rule-engine (2 instances), transport/mqtt (2 instances), transport/http (2 instances), transport/coap, transport/lwm2m, transport/snmp, js-executor (10 replicas), web-ui (2 instances), vc-executor (2 instances), edqs, monitoring. Services have clear roles: core handles REST API and entity management, rule-engine processes telemetry, transports handle IoT protocols. However, all services share a single Maven reactor, common libraries (`common/*`), and the same PostgreSQL database instance. This is a modular monolith with separate deployment units sharing a database. |
| **Gap** | Services share a single database instance and are tightly coupled through common libraries. The single Maven reactor means all services are built and versioned together. Cross-service data access goes through the shared database rather than APIs. |
| **Recommendation** | The current architecture is appropriate for this platform's maturity level. Services have clear bounded contexts (core, rule-engine, transport, executor). The next evolution would be per-service database schemas or per-service databases to reduce data coupling, starting with the most independently-scalable service (e.g., js-executor already has its own deployment unit). |
| **Evidence** | `docker/docker-compose.yml` (13+ service definitions), `msa/` (13 Dockerfiles), `pom.xml` (single Maven reactor with 12 top-level modules), `docker/docker-compose.postgres.yml` (shared PostgreSQL instance for core and rule-engine services) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Good mix of async and sync communication. Kafka-based messaging is used extensively for inter-service communication: transport → core (telemetry ingestion), core → rule-engine (telemetry processing), rule-engine → core (alarm/notification results). The queue abstraction in `common/queue/` supports Kafka, SQS/SNS, and in-memory backends. Synchronous REST API serves client-facing endpoints (over 60 controllers). For stateful-crud archetype, this represents a good balance — async for cross-service state propagation, sync for client API. |
| **Gap** | While key workflows are async (telemetry pipeline), some cross-service communication patterns still rely on synchronous HTTP. The SQS/SNS backend is available but not the default configuration. |
| **Recommendation** | Continue expanding async patterns for cross-service state changes. When migrating to MSK Serverless, consider EventBridge (per preferences) for event-driven rule engine actions. Ensure the SQS/SNS queue backend is production-tested for AWS deployment. |
| **Evidence** | `common/queue/src/main/java/org/thingsboard/server/queue/kafka/`, `docker/.env` (TB_QUEUE_TYPE=kafka), `application/src/main/resources/thingsboard.yml` (queue configuration), `pom.xml` (aws-java-sdk-sqs, aws-java-sdk-sns) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | ThingsBoard handles long-running operations asynchronously. Rule Engine processes telemetry through rule chains asynchronously via Kafka queues. REST API controllers use Spring's `DeferredResult` for async responses in `DeviceController`, `TelemetryController`, `RpcV1Controller`, `RpcV2Controller`, and `AdminController`. The JS executor handles script execution asynchronously with configurable timeouts. Most long-running operations (telemetry processing, RPC to devices) are already async with status tracking. |
| **Gap** | Some administrative operations may still be synchronous. No evidence of job status polling APIs for bulk operations (e.g., bulk device provisioning, firmware updates). |
| **Recommendation** | For any remaining synchronous bulk operations, implement async job patterns with status polling endpoints. AWS Step Functions could orchestrate complex multi-step administrative workflows (firmware rollout, bulk device provisioning). |
| **Evidence** | `application/src/main/java/org/thingsboard/server/controller/DeviceController.java` (DeferredResult usage), `application/src/main/java/org/thingsboard/server/controller/TelemetryController.java`, `application/src/main/java/org/thingsboard/server/controller/RpcV1Controller.java`, `application/src/main/java/org/thingsboard/server/controller/RpcV2Controller.java` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API versioning is applied ad hoc. WebSocket telemetry commands have explicit v1/v2 versioning (`service/ws/telemetry/cmd/v1/`, `service/ws/telemetry/cmd/v2/` directories). RPC controllers have versioned paths (`RpcV1Controller`, `RpcV2Controller`). The Swagger configuration references `/api/(?:noauth|v1)/.*` as non-security paths. However, the majority of REST endpoints are mapped under `/api/` without version prefix (e.g., `/api/device`, `/api/alarm`, `/api/dashboard`). No systematic versioning strategy across all endpoints. |
| **Gap** | Versioning applied to fewer than half of endpoints. WebSocket and RPC have versioning, but the core REST API lacks version prefixes. Multiple versioning patterns coexist (directory-based for WS, controller-based for RPC, none for REST). |
| **Recommendation** | Adopt consistent URL-path versioning (`/api/v1/`) across all REST endpoints. Start by adding `/api/v1/` prefix to new endpoints while maintaining backward compatibility on existing `/api/` paths. Use API Gateway (per preferences) version management to route traffic between API versions during migration. |
| **Evidence** | `application/src/main/java/org/thingsboard/server/controller/` (60+ controllers under /api), `application/src/main/java/org/thingsboard/server/controller/RpcV1Controller.java`, `application/src/main/java/org/thingsboard/server/controller/RpcV2Controller.java`, `application/src/main/resources/thingsboard.yml` (SWAGGER_NON_SECURITY_PATH_REGEX with /v1/) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Apache Zookeeper is used for service discovery (`ZOOKEEPER_ENABLED=true` in `docker/tb-node.env`, `ZOOKEEPER_URL=zookeeper:2181`). Apache Curator library (v5.6.0) provides service registration and discovery. The `common/discovery-api/` module defines the discovery abstraction (`TbServiceInfoProvider`). The `common/queue/discovery/` package implements service discovery. Services register with Zookeeper on startup and discover peers dynamically. |
| **Gap** | Partial service discovery — Zookeeper-based discovery for ThingsBoard services (core, rule-engine, transport) but Docker Compose service names are used as hard-coded DNS entries for infrastructure services (PostgreSQL, Kafka, Valkey). Some endpoints configured via environment variables (e.g., `TB_KAFKA_SERVERS=localhost:9092`). |
| **Recommendation** | On EKS (per preferences), replace Zookeeper-based discovery with Kubernetes native service discovery (CoreDNS). Use AWS Cloud Map for cross-cluster or cross-service discovery. For infrastructure services (databases, cache, messaging), use AWS service endpoints which are inherently discoverable. |
| **Evidence** | `docker/tb-node.env` (ZOOKEEPER_ENABLED=true, ZOOKEEPER_URL=zookeeper:2181), `pom.xml` (curator.version=5.6.0, zookeeper.version=3.9.5), `common/discovery-api/src/main/java/org/thingsboard/server/queue/discovery/TbServiceInfoProvider.java` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard stores IoT telemetry data in PostgreSQL (with TimescaleDB extension support via `schema-timescale.sql`) or Cassandra (hybrid mode). File and image resources (device images, OTA packages, dashboards) are managed through the application's resource service (`TbResourceController`, `ImageController`, `OtaPackageController`). No S3 integration detected for unstructured data storage. Resources appear to be stored in the database or local filesystem. |
| **Gap** | Unstructured data (OTA packages, images, exported dashboards) stored in the database or local filesystem rather than managed object storage. No S3 integration for scalable, durable unstructured data storage. No parsing pipeline for document processing. |
| **Recommendation** | Migrate unstructured data storage to Amazon S3 for OTA packages, device images, exported dashboards, and backup files. Implement S3 lifecycle policies for cost optimization. For IoT data analytics, consider S3 as a data lake destination for historical telemetry with Athena for ad-hoc queries. |
| **Evidence** | `dao/src/main/resources/sql/schema-timescale.sql`, `dao/src/main/resources/sql/schema-ts-psql.sql`, `application/src/main/java/org/thingsboard/server/controller/TbResourceController.java`, `application/src/main/java/org/thingsboard/server/controller/ImageController.java`, `application/src/main/java/org/thingsboard/server/controller/OtaPackageController.java` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The `dao/` module provides an exemplary centralized data access layer with clear package structure: `dao/alarm`, `dao/asset`, `dao/device`, `dao/customer`, `dao/dashboard`, `dao/entity`, `dao/entityview`, `dao/event`, `dao/notification`, `dao/oauth2`, `dao/ota`, `dao/queue`, `dao/relation`, `dao/resource`, `dao/rpc`, `dao/rule`, `dao/settings`, `dao/tenant`, `dao/user`, `dao/widget`, and more. JPA/Hibernate for PostgreSQL with `ThingsboardPostgreSQLDialect.java` for custom dialect. Dedicated NoSQL DAO (`dao/nosql/`) for Cassandra. Unified DAO interfaces (`Dao.java`, `DaoUtil.java`, `ExportableEntityDao.java`) provide consistent data access patterns. |
| **Gap** | None — the DAO layer is well-structured with clear entity boundaries and consistent patterns. |
| **Recommendation** | No action needed. The DAO layer is a strength of the codebase and provides a clean foundation for database migration (e.g., to Aurora PostgreSQL). |
| **Evidence** | `dao/src/main/java/org/thingsboard/server/dao/` (30+ entity-specific packages), `dao/src/main/java/org/thingsboard/server/dao/Dao.java`, `dao/src/main/java/org/thingsboard/server/dao/DaoUtil.java`, `dao/src/main/java/org/thingsboard/server/dao/ThingsboardPostgreSQLDialect.java`, `dao/src/main/java/org/thingsboard/server/dao/nosql/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are explicitly pinned: PostgreSQL 16 in `docker-compose.postgres.yml` (image: `postgres:16`), Cassandra driver 4.17.0 and Cassandra-all 5.0.4 in `pom.xml`. Valkey 8.0 pinned in `docker-compose.valkey.yml`. PostgreSQL 16 is current and supported until November 2028. Cassandra 5.0 is the current LTS release. No engines are at or past EOL. However, no documented version-update procedure exists — no documented process for testing and rolling out engine version upgrades. |
| **Gap** | Versions are pinned and current, but no documented version-update procedure covering downtime windows, rollback, and risk acknowledgment. |
| **Recommendation** | Document a version-update procedure for each database engine. On Aurora PostgreSQL (per Managed Databases pathway), version upgrades are managed with minimal downtime via blue/green deployment. For now, document the upgrade path from PostgreSQL 16 and establish a policy for tracking EOL timelines. |
| **Evidence** | `docker/docker-compose.postgres.yml` (image: postgres:16), `pom.xml` (cassandra.version=4.17.0, cassandra-all.version=5.0.4), `docker/docker-compose.valkey.yml` (image: bitnamilegacy/valkey:8.0) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | `schema-functions.sql` contains 6 PL/pgSQL stored functions specifically for alarm management: `create_or_update_active_alarm`, `update_alarm`, `acknowledge_alarm`, `clear_alarm`, `assign_alarm`, `unassign_alarm`. These functions implement atomic alarm state transitions (read-check-update patterns using `SELECT ... FOR UPDATE`). The stored procedures are limited to alarm CRUD operations — the vast majority of business logic resides in the Java application layer. No proprietary SQL constructs (T-SQL, PL/SQL) are used — only standard PL/pgSQL. |
| **Gap** | Minimal stored procedure usage limited to alarm management for performance-critical atomic operations. While the count is small (6 functions), they couple alarm state management to PostgreSQL's PL/pgSQL. |
| **Recommendation** | The current stored procedure usage is appropriate for performance-critical atomic operations. These PL/pgSQL functions are compatible with Aurora PostgreSQL and do not require conversion for the Managed Databases pathway. Long-term, consider extracting alarm state management to the application layer using optimistic locking or database-level advisory locks to eliminate database coupling entirely. |
| **Evidence** | `dao/src/main/resources/sql/schema-functions.sql` (6 functions: create_or_update_active_alarm, update_alarm, acknowledge_alarm, clear_alarm, assign_alarm, unassign_alarm) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard has a built-in application-level audit logging subsystem. The `dao/audit/` package contains audit log DAO classes. `AuditLogController` exposes audit log query APIs. The audit log tracks entity CRUD operations, user login events, and administrative actions within the ThingsBoard platform. However, no cloud-level audit logging (CloudTrail) is configured — no IaC exists to define CloudTrail. The audit logging is application-level only, covering ThingsBoard platform actions but not AWS infrastructure-level actions. |
| **Gap** | Application-level audit logging exists but no cloud-level audit logging (CloudTrail). No immutable log storage. No log file validation. Audit logs stored in the same PostgreSQL database as application data. |
| **Recommendation** | Enable AWS CloudTrail for infrastructure-level audit logging. Configure CloudTrail with log file validation and immutable storage (S3 with Object Lock). Ship ThingsBoard application audit logs to CloudWatch Logs or S3 for centralized, immutable storage separate from the application database. |
| **Evidence** | `dao/src/main/java/org/thingsboard/server/dao/audit/`, `application/src/main/java/org/thingsboard/server/controller/AuditLogController.java` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration found for any data store. PostgreSQL in Docker Compose has no encryption settings. Cassandra SSL configuration exists in `thingsboard.yml` but is for transport encryption (client-to-server), not at-rest encryption. No KMS keys defined. No encryption configuration on Docker volumes. Valkey runs with no authentication (`ALLOW_EMPTY_PASSWORD=yes`) and no encryption. |
| **Gap** | No encryption at rest for any data store. Sensitive IoT data (device credentials, telemetry, customer information, API keys) stored without encryption. This is a significant compliance and security risk. |
| **Recommendation** | Migrating to managed AWS services (per Managed Databases pathway) enables encryption at rest by default: Aurora PostgreSQL with KMS encryption, DynamoDB with AWS-managed encryption, ElastiCache with encryption at rest and in-transit. Define customer-managed KMS keys for sensitive data stores with automated rotation. Enable EBS encryption for any remaining EC2/EKS volumes. |
| **Evidence** | `docker/docker-compose.postgres.yml` (no encryption), `docker/docker-compose.valkey.yml` (ALLOW_EMPTY_PASSWORD: yes, no encryption), `application/src/main/resources/thingsboard.yml` (SSL settings for transport, not at-rest) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive JWT-based authentication implemented via Spring Security. JWT token management with configurable expiration (`JWT_TOKEN_EXPIRATION_TIME`), issuer validation, and signing key (`JWT_TOKEN_SIGNING_KEY`). JJWT library v0.12.5 for token processing. Multiple auth filters: `JwtTokenAuthenticationProcessingFilter`, `RefreshTokenProcessingFilter`. OAuth2 support configured (`security.oauth2` section in `thingsboard.yml`). Controllers use `@PreAuthorize` annotations for role-based access control. API key authentication supported (`ApiKeyController`). Public endpoints explicitly defined (`/api/noauth/`, `/api/v1/`). Rate limiting via Bucket4j (v8.10.1). Two-factor authentication supported (`TwoFactorAuthController`). |
| **Gap** | None — comprehensive token-based authentication with OAuth2 support, API keys, rate limiting, and 2FA. |
| **Recommendation** | No action needed for authentication. When deploying to AWS with API Gateway (per preferences), integrate with Amazon Cognito for user pool management and API Gateway authorizers for token validation at the edge. |
| **Evidence** | `pom.xml` (jjwt.version=0.12.5, bucket4j.version=8.10.1), `application/src/main/java/org/thingsboard/server/service/security/auth/jwt/`, `application/src/main/java/org/thingsboard/server/controller/AuthController.java`, `application/src/main/java/org/thingsboard/server/controller/TwoFactorAuthController.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`, `application/src/main/resources/thingsboard.yml` (security section) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OAuth2 integration is configured in `thingsboard.yml` (`security.oauth2` section) with support for external identity providers. The OAuth2 login processing URL is configurable (`SECURITY_OAUTH2_LOGIN_PROCESSING_URL`). GitHub OAuth mapper is configured for email mapping. The platform supports OIDC federation for SSO. OAuth2 controller (`OAuth2Controller`) and configuration template controller (`OAuth2ConfigTemplateController`) exist. However, some legacy auth paths remain (local username/password authentication, API key authentication). |
| **Gap** | OAuth2/OIDC integration exists for external IdP federation, but local authentication remains as a parallel auth path. Not all auth flows go through a centralized IdP. |
| **Recommendation** | When deploying to AWS, integrate with Amazon Cognito as the centralized identity provider. Configure Cognito user pools for local users and Cognito identity pools for federated access. Gradually migrate local auth users to Cognito-managed identities. |
| **Evidence** | `application/src/main/resources/thingsboard.yml` (security.oauth2 section), `application/src/main/java/org/thingsboard/server/controller/OAuth2Controller.java`, `application/src/main/java/org/thingsboard/server/controller/OAuth2ConfigTemplateController.java` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets are managed through environment variables with defaults in configuration files. `thingsboard.yml` uses env var substitution for sensitive values (e.g., `${SSL_KEY_STORE_PASSWORD:thingsboard}`, `${JWT_TOKEN_SIGNING_KEY:thingsboardDefaultSigningKey}`, `${SECURITY_JAVA_CACERTS_PASSWORD:changeit}`). Docker Compose files contain plain text credentials: `POSTGRES_PASSWORD: postgres` in `docker-compose.postgres.yml`, `ALLOW_EMPTY_PASSWORD=yes` for Valkey. The `docker/*.env` files contain non-secret configuration. No AWS Secrets Manager, HashiCorp Vault, or equivalent secrets management integration detected. Default passwords are weak (`postgres`, `thingsboard`, `changeit`). |
| **Gap** | Secrets in environment variables with weak defaults committed to the repository. Production database credentials in plain text. No secrets management system with rotation. Default signing keys and passwords pose security risk. |
| **Recommendation** | Integrate with AWS Secrets Manager for all sensitive credentials (database passwords, JWT signing keys, Kafka credentials, SSL certificates). Enable automatic rotation for database credentials. Remove default passwords from configuration files and Docker Compose. Use AWS Secrets Manager CSI driver on EKS for injecting secrets into pods. |
| **Evidence** | `docker/docker-compose.postgres.yml` (POSTGRES_PASSWORD: postgres), `docker/docker-compose.valkey.yml` (ALLOW_EMPTY_PASSWORD: yes), `application/src/main/resources/thingsboard.yml` (SSL_KEY_STORE_PASSWORD:thingsboard, JWT_TOKEN_SIGNING_KEY:thingsboardDefaultSigningKey) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dockerfiles use non-root USER directive (`USER ${pkg.user}`) for all services. Base images use custom ThingsBoard-maintained images (`thingsboard/openjdk25:trixie-slim` for Java services, `thingsboard/node:22.18.0-bookworm-slim` for Node.js). Images are Debian-based slim variants. Java 25 with Corretto in CI. However, no vulnerability scanning (no Inspector, no Snyk, no Trivy), no SSM Patch Manager, no hardened AMI references, and no automated patching strategy. BouncyCastle (v1.78.1) and AntiSamy (v1.7.5) provide security libraries but no automated vulnerability scanning of dependencies. |
| **Gap** | Non-root containers and slim base images are good practices, but no vulnerability scanning, no automated patching strategy, and no hardened base images (CIS benchmarks, Bottlerocket). |
| **Recommendation** | Enable Amazon ECR image scanning for all container images. Add Trivy or Snyk container scanning in the CI pipeline. Consider Amazon EKS Bottlerocket AMIs for node-level hardening. Implement automated base image updates for the custom ThingsBoard Docker images. |
| **Evidence** | `msa/tb-node/docker/Dockerfile` (USER ${pkg.user}, FROM ${docker.base.image}), `pom.xml` (bouncycastle.version=1.78.1, antisamy.version=1.7.5) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD workflows. No Dependabot configuration (`dependabot.yml` not found). No SonarQube, Semgrep, CodeGuru Reviewer, or equivalent in the pipeline. No `.snyk` policy file. No `npm audit` or `pip-audit` in CI. The pom.xml does reference `sonar.exclusions` property, suggesting SonarQube may have been used externally, but no CI integration exists. No container image scanning. |
| **Gap** | No security scanning tools configured in the pipeline. No dependency vulnerability scanning, no SAST, no container scanning. The `sonar.exclusions` property suggests awareness but no active integration. |
| **Recommendation** | Add GitHub Dependabot for automated dependency vulnerability detection. Integrate SonarQube or Amazon CodeGuru Reviewer for SAST in the CI pipeline. Add ECR image scanning for container vulnerabilities. Configure security gates that block deployment on critical findings. Add `npm audit` for the ui-ngx frontend dependencies. |
| **Evidence** | `.github/workflows/` (no security scanning steps), `pom.xml` (sonar.exclusions property but no SonarQube plugin in build), repository search for dependabot.yml, .snyk — not found |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation detected. No OpenTelemetry SDK in dependencies, no X-Ray instrumentation, no Jaeger or Zipkin integration. Prometheus metrics are enabled (`METRICS_ENABLED=true`, `METRICS_ENDPOINTS_EXPOSE=prometheus` in `docker/tb-node.env`) providing application metrics, but Prometheus is a metrics system, not distributed tracing. No trace ID propagation across service boundaries (tb-core ↔ rule-engine ↔ transport). |
| **Gap** | No distributed tracing. Cannot trace requests across ThingsBoard's distributed services (core, rule-engine, transport, js-executor). Debugging cross-service failures in the telemetry pipeline is extremely difficult without tracing. |
| **Recommendation** | Instrument all services with OpenTelemetry Java agent (auto-instrumentation for Spring Boot). Export traces to AWS X-Ray via the OpenTelemetry Collector. Ensure trace ID propagation across Kafka messages (transport → core → rule-engine). This is especially critical for diagnosing latency issues in the IoT telemetry pipeline. |
| **Evidence** | `docker/tb-node.env` (METRICS_ENABLED=true, METRICS_ENDPOINTS_EXPOSE=prometheus), `pom.xml` (no OpenTelemetry or tracing dependencies) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The dedicated monitoring module (`monitoring/src/main/java/org/thingsboard/monitoring/`) provides health and availability monitoring for ThingsBoard services and transports (MQTT, HTTP, CoAP, LwM2M). Prometheus/Grafana setup (`docker-compose.prometheus-grafana.yml`) enables metrics visualization. However, no formal SLO definitions with error budgets are found. No p99/p95 latency SLOs, no availability SLOs, no error rate SLOs. The monitoring is health-check based rather than SLO-based. |
| **Gap** | Health monitoring exists but no formal SLO definitions. No error budgets, no latency targets, no availability commitments defined in code or configuration. |
| **Recommendation** | Define SLOs for critical user journeys: telemetry ingestion latency (p99 < Xms), API response time (p95 < Xms), device connection success rate (> 99.9%), rule engine processing latency. Use CloudWatch SLO monitoring when deployed to AWS. Implement error budget tracking. |
| **Evidence** | `monitoring/src/main/java/org/thingsboard/monitoring/` (ThingsboardMonitoringApplication, service/, config/), `docker/docker-compose.prometheus-grafana.yml` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus metrics endpoint is enabled, and the `common/stats/` module provides statistics collection infrastructure. The application collects and exposes infrastructure metrics via Prometheus. ThingsBoard itself collects device telemetry which constitutes business data, but the platform's own operational business metrics (e.g., active device count, messages processed per second, rule chain execution times, alarm resolution times) are not systematically published alongside infrastructure metrics. Grafana dashboards exist but appear focused on infrastructure monitoring. |
| **Gap** | Infrastructure metrics via Prometheus but no systematic business outcome metrics. Platform operational KPIs (device onboarding rate, telemetry throughput, alarm response times) are not tracked as custom metrics. |
| **Recommendation** | Publish custom CloudWatch metrics for business KPIs: active devices, telemetry messages/second, rule chain executions/second, alarm creation and resolution rates, API error rates by endpoint. Create CloudWatch dashboards combining infrastructure and business metrics. |
| **Evidence** | `common/stats/` (statistics module), `docker/tb-node.env` (METRICS_ENABLED=true, METRICS_ENDPOINTS_EXPOSE=prometheus), `docker/docker-compose.prometheus-grafana.yml` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection configuration found. Prometheus is configured for metrics collection but no alerting rules are defined in the repository. No Alertmanager configuration. No CloudWatch alarms. No PagerDuty, OpsGenie, or incident management integration. The Grafana deployment exists but no alert definitions are stored in the repository. The monitoring module checks service health but does not implement anomaly detection. |
| **Gap** | No alerting configured. No anomaly detection on error rates, latency, or resource utilization. No escalation or notification integration. Operational issues will go undetected until users report them. |
| **Recommendation** | Implement CloudWatch alarms for critical metrics: CPU/memory utilization, queue depth, error rates, latency p99. Enable CloudWatch Anomaly Detection on telemetry ingestion rate and API error rate to catch gradual degradation. Integrate with Amazon SNS for alert notifications and PagerDuty/OpsGenie for on-call escalation. |
| **Evidence** | `docker/docker-compose.prometheus-grafana.yml` (Grafana deployed but no alert configs), `docker/monitoring/` (Prometheus config but no alert rules) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Deployments are manual via shell scripts: `docker-start-services.sh`, `docker-stop-services.sh`, `docker-upgrade-tb.sh`, `docker-remove-services.sh`, `docker-update-service.sh`. No blue/green, canary, or rolling deployment strategy. The upgrade script (`docker-upgrade-tb.sh`) stops all services, runs database migration, and restarts — a manual, all-at-once upgrade with downtime. No traffic shifting, no health-check-based rollback, no staged rollout. |
| **Gap** | Direct-to-production deployment with manual shell scripts and downtime during upgrades. No staged rollout, no automated rollback, no traffic shifting. |
| **Recommendation** | On EKS (per preferences), implement rolling deployments with health check gates for zero-downtime updates. For critical releases, use canary deployments via Argo Rollouts or AWS App Mesh with weighted traffic routing. Automate database migrations as a pre-deployment step in the CI/CD pipeline. |
| **Evidence** | `docker/docker-start-services.sh`, `docker/docker-stop-services.sh`, `docker/docker-upgrade-tb.sh`, `docker/docker-update-service.sh` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Black-box integration tests exist in `msa/black-box-tests/` using TestNG (v7.10.1) and Allure for reporting. Testcontainers (v1.21.4) is available for container-based integration testing. Unit tests exist across multiple modules. However, integration tests are NOT run in any CI pipeline — the GitHub Actions workflows only perform config validation and license formatting. Integration tests require manual execution. |
| **Gap** | Integration tests exist but are not integrated into CI. They provide coverage for critical workflows but offer no automated quality gate. Regressions can reach production undetected. |
| **Recommendation** | Integrate the existing black-box tests into the CI pipeline as a mandatory quality gate. Run integration tests using Testcontainers in the build pipeline. Start with smoke tests for critical paths (device CRUD, telemetry ingestion, alarm creation) and expand coverage over time. |
| **Evidence** | `msa/black-box-tests/` (pom.xml, src/), `pom.xml` (testng.version=7.10.1, testcontainers.version=1.21.4, allure-testng.version=2.27.0) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found in the repository. No Systems Manager Automation documents. No Lambda-based remediation. No Step Functions for incident workflows. No self-healing patterns. The `docker-upgrade-tb.sh` script is the closest thing to an operational runbook but is a manual deployment script, not an incident response procedure. |
| **Gap** | No incident response automation. Incident response is entirely ad hoc. No documented procedures for common failure scenarios (database connection failure, Kafka broker down, transport service crash, queue backlog). |
| **Recommendation** | Create runbooks for common ThingsBoard failure scenarios. Implement automated remediation for self-healing patterns (e.g., auto-restart services on health check failure, auto-scale on queue depth threshold). Use AWS Systems Manager Automation for infrastructure-level incident response. Document escalation procedures. |
| **Evidence** | Repository-wide search for runbook files (markdown, YAML, JSON) — none found. `docker/docker-upgrade-tb.sh` (manual deployment script, not incident response) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Prometheus/Grafana setup exists for metrics collection and visualization. The monitoring module provides transport health monitoring. However, no per-service dashboards with named owners are defined. No CODEOWNERS file referencing observability configs. No team attribution on alarms or SLO definitions. No observability ownership model. |
| **Gap** | No observability ownership. Monitoring exists but is not attributed to specific teams or service owners. No accountability for monitoring gaps. |
| **Recommendation** | Define observability ownership: assign each ThingsBoard service (core, rule-engine, transport, js-executor) to a team with responsibility for dashboards, alarms, and SLOs. Create per-service Grafana dashboards. Add a CODEOWNERS file covering monitoring and observability configurations. |
| **Evidence** | `docker/docker-compose.prometheus-grafana.yml`, `monitoring/src/main/java/org/thingsboard/monitoring/` — no ownership attribution found |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging configuration found. No IaC exists, so no `default_tags`, no `tags` blocks, no tag enforcement policies. Docker Compose services have labels for Docker-level identification but no cloud resource tagging. No cost allocation tags, no ownership tags, no environment tags. |
| **Gap** | No resource tagging governance. When deployed to AWS, resources will lack cost allocation, ownership, and environment identification tags. |
| **Recommendation** | Define a tagging standard covering: Environment (dev/staging/prod), Service (tb-core/tb-rule-engine/transport), Owner (team name), CostCenter, Project. Implement mandatory tags in IaC (per Modern DevOps pathway). Enable AWS Cost Allocation Tags. Configure Tag Policies in AWS Organizations for enforcement. |
| **Evidence** | No IaC files with tags found. `docker/docker-compose.yml` (Docker service definitions without cloud tagging) |

---

## Learning Materials

The following learning resources are mapped to the triggered modernization pathways:

### Move to Managed Databases
- [Move to Managed Databases — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Managed Analytics
- [Move to Managed Analytics — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/RWZA84NMVV)

### Move to Modern DevOps
- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| **docker/** | | |
| `docker/docker-compose.yml` | INF-Q1, INF-Q5, INF-Q6, INF-Q7, INF-Q9, APP-Q2, OPS-Q9 | Main Docker Compose: 13+ service definitions, HAProxy load balancer, static replicas |
| `docker/docker-compose.postgres.yml` | INF-Q2, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2, SEC-Q5 | PostgreSQL 16 self-managed, POSTGRES_PASSWORD in plain text |
| `docker/docker-compose.kafka.yml` | INF-Q4, INF-Q9 | Self-managed Kafka (bitnamilegacy/kafka:4.0) with KRaft mode |
| `docker/docker-compose.cassandra.volumes.yml` | INF-Q2, INF-Q8 | Self-managed Cassandra with external Docker volume |
| `docker/docker-compose.valkey.yml` | INF-Q2, SEC-Q2, SEC-Q5 | Valkey 8.0 caching, ALLOW_EMPTY_PASSWORD=yes |
| `docker/docker-compose.prometheus-grafana.yml` | OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q8 | Prometheus/Grafana monitoring stack |
| `docker/.env` | INF-Q4, APP-Q3 | TB_QUEUE_TYPE=kafka, DATABASE=postgres |
| `docker/tb-node.env` | APP-Q6, OPS-Q1, OPS-Q3 | ZOOKEEPER_ENABLED=true, METRICS_ENABLED=true |
| `docker/kafka.env` | INF-Q4 | Kafka KRaft configuration |
| `docker/docker-start-services.sh` | OPS-Q5 | Manual deployment script |
| `docker/docker-stop-services.sh` | OPS-Q5 | Manual stop script |
| `docker/docker-upgrade-tb.sh` | OPS-Q5, OPS-Q7 | Manual upgrade script with downtime |
| `docker/docker-update-service.sh` | OPS-Q5 | Manual service update script |
| `docker/haproxy/` | INF-Q6 | HAProxy configuration directory |
| `docker/monitoring/` | OPS-Q4 | Prometheus configuration |
| **msa/** | | |
| `msa/tb-node/docker/Dockerfile` | INF-Q1, SEC-Q6 | Java service Dockerfile with non-root USER |
| `msa/js-executor/docker/Dockerfile` | INF-Q1 | Node.js JS executor Dockerfile |
| `msa/web-ui/docker/Dockerfile` | INF-Q1 | Web UI Dockerfile |
| `msa/transport/mqtt/docker/Dockerfile` | INF-Q1 | MQTT transport Dockerfile |
| `msa/black-box-tests/` | OPS-Q6 | Integration tests with TestNG and Testcontainers |
| **application/** | | |
| `application/src/main/resources/thingsboard.yml` | INF-Q3, INF-Q4, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, APP-Q5 | Main configuration (2,208 lines) — security, queue, database, transport settings |
| `application/src/main/java/.../controller/` | APP-Q2, APP-Q4, APP-Q5, SEC-Q3 | 60+ REST API controllers |
| `application/src/main/java/.../controller/AuditLogController.java` | SEC-Q1 | Audit log query APIs |
| `application/src/main/java/.../controller/AuthController.java` | SEC-Q3 | Authentication endpoints |
| `application/src/main/java/.../controller/OAuth2Controller.java` | SEC-Q4 | OAuth2 integration endpoints |
| `application/src/main/java/.../controller/ApiKeyController.java` | SEC-Q3 | API key management |
| `application/src/main/java/.../controller/TwoFactorAuthController.java` | SEC-Q3 | 2FA endpoints |
| `application/src/main/java/.../controller/RpcV1Controller.java` | APP-Q4, APP-Q5 | RPC v1 with DeferredResult |
| `application/src/main/java/.../controller/RpcV2Controller.java` | APP-Q4, APP-Q5 | RPC v2 with DeferredResult |
| `application/src/main/java/.../controller/DeviceController.java` | APP-Q4 | Device CRUD with DeferredResult |
| `application/src/main/java/.../controller/TelemetryController.java` | APP-Q4 | Telemetry with DeferredResult |
| `application/src/main/java/.../controller/AiModelController.java` | Quick Agent Wins | AI model management API |
| `application/src/main/java/.../service/ai/` | Quick Agent Wins, Move to AI | AI service with langchain4j integration |
| `application/src/main/java/.../service/security/auth/jwt/` | SEC-Q3 | JWT authentication implementation |
| **common/** | | |
| `common/queue/src/main/java/.../queue/kafka/` | INF-Q4, APP-Q3 | Kafka queue abstraction |
| `common/discovery-api/` | APP-Q6 | Service discovery abstraction |
| `common/stats/` | OPS-Q3 | Statistics collection module |
| **dao/** | | |
| `dao/src/main/java/.../dao/` | DATA-Q2 | Centralized DAO layer (30+ entity packages) |
| `dao/src/main/java/.../dao/Dao.java` | DATA-Q2 | Base DAO interface |
| `dao/src/main/java/.../dao/ThingsboardPostgreSQLDialect.java` | DATA-Q2 | Custom PostgreSQL dialect |
| `dao/src/main/java/.../dao/nosql/` | DATA-Q2 | Cassandra NoSQL DAO |
| `dao/src/main/java/.../dao/audit/` | SEC-Q1 | Audit log DAO |
| `dao/src/main/resources/sql/schema-functions.sql` | DATA-Q4 | 6 PL/pgSQL stored functions for alarm management |
| `dao/src/main/resources/sql/schema-timescale.sql` | DATA-Q1 | TimescaleDB schema |
| `dao/src/main/resources/sql/schema-ts-psql.sql` | DATA-Q1 | PostgreSQL timeseries schema |
| **rule-engine/** | | |
| `rule-engine/rule-engine-api/` | INF-Q3 | Rule Engine API |
| `rule-engine/rule-engine-components/` | INF-Q3 | Rule Engine components |
| **monitoring/** | | |
| `monitoring/src/main/java/.../monitoring/` | OPS-Q2, OPS-Q8 | Dedicated monitoring application |
| **Other** | | |
| `pom.xml` | APP-Q1, INF-Q4, DATA-Q3, SEC-Q3, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q6 | Root POM — Java 25, Spring Boot 3.5.12, langchain4j 1.8.0-TB |
| `ui-ngx/package.json` | APP-Q1 | Angular 20.3.18, TypeScript 5.9.3 |
| `.github/workflows/check-configuration-files.yml` | INF-Q11 | Config validation workflow |
| `.github/workflows/license-header-format.yml` | INF-Q11 | License header formatting workflow |
| `.github/workflows/atx-transform.yml` | INF-Q11 | ATX transformation workflow |
