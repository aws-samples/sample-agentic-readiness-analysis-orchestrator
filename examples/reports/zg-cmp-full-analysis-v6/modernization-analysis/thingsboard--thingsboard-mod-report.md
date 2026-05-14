# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | thingsboard--thingsboard |
| **Date** | 2026-05-08 |
| **TD Version** | modernization-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, iot, platform |
| **Context** | Open-source IoT platform for device management, data collection, and visualization. |
| **Overall Score** | 1.90 / 4.0 |

**Archetype Justification**: The platform owns persistent state in PostgreSQL (devices, tenants, alarms, telemetry), manages full entity lifecycle through CRUD REST APIs, and stores user-specific data (tenant isolation, device ownership). Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **1.90 / 4.0** | **🟠 Needs Work** | |

### Scoring Notes

- **INF**: (1+2+2+2+1+1+1+1+1+1+1) / 11 = 14/11 = 1.27
- **APP**: (3+2+2+2+2+3) / 6 = 14/6 = 2.33
- **DATA**: (2+3+2+3) / 4 = 10/4 = 2.50
- **SEC**: (1+1+3+2+2+2+2) / 7 = 13/7 = 1.86
- **OPS**: (1+1+2+2+1+3+1+2+1) / 9 = 14/9 = 1.56
- **Overall**: (1.27+2.33+2.50+1.86+1.56) / 5 = 9.52/5 = 1.90

---

## Classification

**Tier: Remediation Required**

This repo has 8 High findings, 9 Medium findings, 4 Low findings. The matched rule is: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap and maps to Pilot-Ready. With 8 High findings, this system has multiple significant modernization gaps requiring remediation before it can be considered cloud-native ready.

**Classification Consistency Check**: consistent (V5 Needs Work band [score 1.90 < 2.5] ≡ V6 Remediation Required)

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — all infrastructure defined via Docker Compose and manual setup | Cannot reproduce environments, no disaster recovery automation, manual drift |
| 2 | INF-Q1: Managed Compute | 1 | All compute on Docker Compose with no managed orchestration (ECS/EKS) | No auto-healing, no managed scaling, manual container lifecycle |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging infrastructure | No forensic capability, compliance gaps, no action traceability |
| 4 | SEC-Q2: Encryption at Rest | 1 | No encryption at rest configuration for databases or storage | Data exposure risk, compliance violations |
| 5 | INF-Q11: CI/CD Automation | 1 | No build, test, or deployment pipelines — only config validation workflows | Manual deployments, no quality gates, slow iteration |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation and README content exists in the repository (extensive README, API docs via springdoc-openapi, configuration documentation in thingsboard.yml)
- **What it enables:** A knowledge agent that indexes platform documentation, configuration options, and rule engine node documentation to answer developer and operator questions about ThingsBoard deployment and configuration.
- **Additional steps:** Generate static OpenAPI spec from springdoc for full API tool discovery. Index the 29 rule engine node descriptions.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 1 — does NOT meet threshold). Not eligible.

### Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 1 — does NOT meet threshold). Not eligible.

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 3 — meets threshold)
- **What it enables:** A natural-language-to-SQL agent that queries the ThingsBoard PostgreSQL database for device telemetry, alarm history, and tenant analytics without requiring SQL expertise.
- **Additional steps:** Document the schema-entities.sql relationships and add column-level descriptions for the 982-line schema. Ensure read-only access patterns.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Not Triggered | — | — | Contextual guard: 13 Dockerfiles and Docker Compose already containerize the workload |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=3, no commercial DB engines (PostgreSQL is open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=2 (self-managed PostgreSQL in Docker), DATA-Q3=2 |
| 5 | Move to Managed Analytics | Triggered | Medium | Medium | INF-Q4=2 (self-managed Kafka), data processing workloads exist (rule engine, telemetry pipelines) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=1, OPS-Q5=1, OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | AI/agent frameworks already present (LangChain4j with Bedrock support) |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:** ThingsBoard is a modular monolith (APP-Q2=2) that supports microservices deployment via Docker Compose and Kafka. While module boundaries exist (29 rule engine nodes, separate transport services), all modules share a single PostgreSQL database with shared schemas and cross-module data access. The monolith-or-microservices duality is an architectural choice but the shared database coupling prevents true independent deployment.

**Compute Gaps:** All compute runs on raw Docker Compose with HAProxy load balancing (INF-Q1=1). No managed container orchestration (EKS/ECS) is in use.

**Communication Gaps:** Inter-service communication uses self-managed Kafka and gRPC (APP-Q3=2). Long-running operations (rule engine chains, telemetry processing) lack explicit async job handling with status polling (APP-Q4=2).

**Recommended Approach:**
- **Phase 1:** Migrate Docker Compose to Amazon EKS (preferred per context) with Helm charts for each service type (tb-core, tb-rule-engine, transports, edqs)
- **Phase 2:** Replace self-managed Kafka with Amazon MSK Serverless or EventBridge for inter-service messaging
- **Phase 3:** Incrementally extract high-coupling modules (telemetry ingestion, alarm processing) into independently deployable services with separate data stores

**Representative AWS Services:** Amazon EKS, Amazon MSK, Amazon EventBridge, Amazon API Gateway, AWS Step Functions

**Patterns:** Strangler Fig (extract services from monolith incrementally), Anti-corruption Layer (isolate new services from shared DB), Event Sourcing (telemetry events)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** PostgreSQL runs as a Docker container (self-managed) with default credentials. TimescaleDB and Cassandra are optional self-managed alternatives for time-series data. Redis/Valkey runs self-managed for caching. No automated backups, failover, or managed patching.

**Engine Versions:** PostgreSQL version is not explicitly pinned in Docker Compose (uses `postgres:16` image tag). TimescaleDB and Cassandra versions are similarly Docker-managed without lifecycle policies.

**Data Access:** The DAO layer is well-structured with JPA/Hibernate providing a centralized data access pattern (DATA-Q2=3).

**Recommended Targets (respecting preferences):**
- **PostgreSQL → Amazon Aurora PostgreSQL** (preferred): Managed, multi-AZ, auto-scaling storage, automated backups with PITR
- **TimescaleDB → Amazon Timestream** or **Aurora PostgreSQL with TimescaleDB extension**: For time-series telemetry data
- **Cassandra → Amazon Keyspaces** (if Cassandra mode retained) or **Amazon DynamoDB** (preferred for new time-series design)
- **Redis/Valkey → Amazon ElastiCache** or **Amazon MemoryDB**: Managed caching with multi-AZ

**Migration Tools:** AWS DMS for online migration, AWS SCT for schema validation

**Representative AWS Services:** Amazon Aurora PostgreSQL, Amazon DynamoDB, Amazon ElastiCache, Amazon Timestream, AWS DMS

---

### Pathway: Move to Managed Analytics

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:** Self-managed Apache Kafka 3.9.1 serves as the primary message bus between microservices. The rule engine processes IoT telemetry data through configurable processing chains. ZooKeeper provides coordination. No managed streaming or analytics services are in use.

**Data Processing Workloads:**
- Rule engine processes millions of telemetry messages per second
- Telemetry aggregation and downsampling pipelines
- Alarm correlation and event processing
- Device connectivity monitoring

**Recommended Targets (respecting preferences — avoid self-managed-kafka):**
- **Kafka → Amazon MSK Serverless**: Managed Kafka-compatible streaming without broker management
- **ZooKeeper → EKS-native service discovery** or **AWS Cloud Map**: Eliminate ZooKeeper dependency
- **Telemetry analytics → Amazon Kinesis Data Streams + Amazon Athena**: Real-time analytics on device telemetry
- **EventBridge** (preferred): For event-driven rule engine triggers and cross-service notifications

**Representative AWS Services:** Amazon MSK Serverless, Amazon Kinesis, Amazon EventBridge, Amazon Athena, AWS Glue

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10=1):** Zero infrastructure-as-code. All infrastructure is defined in Docker Compose files with manual setup. No Terraform, CloudFormation, CDK, or Helm charts.
- **CI/CD (INF-Q11=1):** Only 3 GitHub Actions workflows exist: ATX transform (manual), license header formatting, and YAML config validation. No build, test, container image build, or deployment automation.
- **Deployment Strategy (OPS-Q5=1):** Direct-to-production via Docker Compose restart. No blue/green, canary, or rolling deployment strategy.
- **Integration Testing (OPS-Q6=3):** Strong black-box test suite exists (128 test files) but is not integrated into CI pipelines.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK or Terraform for EKS cluster, Aurora, MSK, ElastiCache provisioning
- **CI/CD:** GitHub Actions with multi-stage pipeline (build → test → container build → deploy to EKS)
- **Container Registry:** Amazon ECR for Docker images
- **Deployment:** ArgoCD or AWS CodeDeploy for EKS-based canary/blue-green deployments
- **Testing in CI:** Integrate existing black-box tests into pipeline using Testcontainers

**Representative AWS Services:** AWS CDK, Amazon ECR, AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy

---

## Decomposition Strategy

APP-Q2 scored 2 (monolith with identifiable modules but shared database schemas). The following decomposition guidance applies.

### Recommended Approach: Strangler Fig (Parallel Track)

**Why:** ThingsBoard already has identifiable module boundaries (transport services, rule engine, EDQS, core) and supports microservices deployment. The shared PostgreSQL database is the primary coupling point. Strangler Fig allows incremental extraction of services while the monolith continues serving traffic.

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Module boundaries exist (transport services already separate). Team can sustain parallel development. | Medium to High | ✅ **Recommended.** Extract transport services and telemetry ingestion first; they already have minimal DB coupling. |
| **Conditional / Adaptive** | Limited capacity for full decomposition. Need quick EKS migration wins. | Low to Medium | ✅ **Recommended as Phase 1.** Containerize-as-is on EKS, then selectively extract. |
| **Big-Bang Rewrite** | — | Very High | ⚠️ **Not recommended.** The platform is functional and well-structured. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the shared PostgreSQL schema | Every extraction — translate between new service's data model and legacy shared tables |
| **Saga Pattern** | Manage distributed transactions (device provisioning, alarm lifecycle) | When extracting alarm management (currently uses DB stored procedures with row locking) |
| **Event Sourcing** | Capture telemetry and device state changes as immutable events | Telemetry ingestion service — enables replay, analytics, and audit |
| **Hexagonal Architecture** | Clean boundaries for each extracted service | Every new service — ensures portability across managed AWS services |

### Effort Estimation

| Factor | Signal | Analysis |
|--------|--------|------------|
| Module boundaries | Clear separation (transports, rule engine, EDQS) | Low effort for transport extraction |
| Data coupling | Shared PostgreSQL with cross-module joins | High effort for core/rule-engine separation |
| Stored procedures | 6 PL/pgSQL functions for alarm management | Medium effort — must extract to application layer |
| Communication patterns | Kafka + gRPC already in place | Low effort — messaging infrastructure exists |
| CI/CD maturity | No pipeline exists | High effort — must build pipeline first |
| Test coverage | 128 black-box tests + unit tests | Medium — tests exist but not in CI |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs on Docker Compose with HAProxy as the load balancer. 13 Dockerfiles define service images (tb-core, tb-rule-engine, transports, js-executor, web-ui, edqs, vc-executor). No managed container orchestration (ECS, EKS, Fargate) or serverless (Lambda) is used. Deployment model is docker-compose with manual lifecycle management. |
| **Gap** | No managed compute platform. Docker Compose provides no auto-healing, horizontal scaling, health-check-based routing, or rolling updates. |
| **Recommendation** | Migrate to Amazon EKS (preferred) with Helm charts for each service type. Use EKS managed node groups with Graviton instances for cost efficiency. Deploy Fargate profiles for burst workloads (JS executors, transport services). |
| **Evidence** | `docker/docker-compose.yml`, `msa/tb-node/docker/Dockerfile`, `msa/transport/mqtt/docker/Dockerfile` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | PostgreSQL runs as a Docker container (`postgres:16` image) with default credentials. Cassandra and TimescaleDB are optional self-managed alternatives. Redis/Valkey runs as a Docker container for caching. No managed database services (RDS, Aurora, DynamoDB, ElastiCache) are configured. However, the application is designed for externalized database configuration via environment variables, making managed DB migration straightforward. |
| **Gap** | All databases are self-managed in Docker containers. No automated backups, failover, patching, or scaling. Default credentials (`postgres:postgres`) in Docker environment. |
| **Recommendation** | Migrate PostgreSQL to Amazon Aurora PostgreSQL (preferred) for managed multi-AZ, automated backups, and PITR. Migrate Redis/Valkey to Amazon ElastiCache. For time-series, evaluate Amazon Timestream or DynamoDB (preferred). |
| **Evidence** | `docker/docker-compose.postgres.yml`, `docker/.env` (DATABASE=postgres), `application/src/main/resources/thingsboard.yml` (spring.datasource config) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The rule engine IS a workflow orchestration system (configurable processing chains for IoT data), but it is entirely custom-built application logic with no dedicated workflow service (Step Functions, Temporal, MWAA). Device provisioning, alarm lifecycle (6 stored procedures), and OTA update workflows are hardcoded in application code. The system has multi-step business operations (device onboarding, alarm escalation, firmware updates) managed through in-code state machines. |
| **Gap** | Business workflows (alarm lifecycle, device provisioning, OTA updates) are hardcoded rather than using a managed orchestration service. The rule engine is a custom orchestrator but lacks visibility, retry/error-budget management, and visual workflow design for operational workflows. |
| **Recommendation** | Adopt AWS Step Functions for operational workflows (device provisioning, OTA rollouts, alarm escalation). Keep the rule engine for real-time data processing but offload long-running multi-step operations to Step Functions for visibility, retry management, and operational control. |
| **Evidence** | `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/` (29 node types), `dao/src/main/resources/sql/schema-functions.sql` (alarm lifecycle procedures) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Apache Kafka 3.9.1 is the primary message bus for microservices mode, running self-managed in Docker. ZooKeeper 3.9.5 provides coordination. The platform also integrates with RabbitMQ, AWS SQS, and AWS SNS as rule engine outbound destinations. Kafka is used extensively with many topics (rule-engine, core, transport-api, notifications, JS-executor, OTA, edge, EDQS). In-memory queue is available for monolith mode. |
| **Gap** | Kafka and ZooKeeper are self-managed in Docker with no managed service (MSK, EventBridge). This requires manual broker management, partition rebalancing, ZooKeeper maintenance, and capacity planning. |
| **Recommendation** | Migrate to Amazon MSK Serverless (preferred — eliminates self-managed Kafka per preferences). Replace ZooKeeper with MSK's built-in coordination or EKS-native service discovery. Use Amazon EventBridge (preferred) for cross-service notifications and alarm events. |
| **Evidence** | `docker/docker-compose.yml` (kafka, zookeeper services), `docker/docker-compose.kafka.yml`, `docker/kafka.env`, `common/queue/src/main/java/org/thingsboard/server/queue/kafka/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists. Services communicate over Docker networks with no isolation between tiers. HAProxy exposes ports 80, 443, 1883 (MQTT), and 7070 (Edge RPC) directly. No private subnet isolation, no VPC endpoints, no PrivateLink configuration. |
| **Gap** | No network security infrastructure. All services are on a flat Docker network with no segmentation between data tier, application tier, and transport tier. No managed networking services. |
| **Recommendation** | Deploy in a VPC with private subnets for databases and application services. Use security groups with least-privilege rules. Place API Gateway (preferred) in front of HTTP endpoints. Use VPC endpoints for AWS service access. Implement network policies in EKS for pod-level isolation. |
| **Evidence** | `docker/docker-compose.yml` (flat network definition), absence of any `.tf`, CloudFormation, or VPC configuration files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | HAProxy serves as the load balancer with Let's Encrypt SSL termination. It routes traffic to backend services by path prefix (/api/, /mqtt, etc.) with basic health checks. No API Gateway, AppSync, CloudFront, or managed API entry point is configured. No throttling beyond application-level Bucket4j rate limiting. No request validation at the gateway level. |
| **Gap** | No managed API gateway with throttling, authentication offload, or request validation. HAProxy provides basic routing but no API management capabilities (usage plans, API keys, request/response transformation, WAF integration). |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point for REST APIs. Use API Gateway for throttling, API key management, request validation, and WAF integration. Retain internal gRPC communication between services on private network. Consider CloudFront for static frontend assets. |
| **Evidence** | `docker/haproxy/config/haproxy.cfg` (HAProxy routing), absence of API Gateway or CloudFront configuration |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. Docker Compose services have static replica counts (2x tb-core, 2x tb-rule-engine, 2x MQTT transport, 10x JS executor). Scaling requires manual docker-compose file editing and redeployment. No dynamic scaling based on load, queue depth, or telemetry throughput. |
| **Gap** | All capacity is statically provisioned. No horizontal pod autoscaler, no ASG, no dynamic scaling policies. Cannot respond to IoT traffic spikes (device onboarding storms, telemetry bursts). |
| **Recommendation** | Implement Kubernetes HPA in EKS for all service types based on custom metrics (Kafka consumer lag, MQTT connection count, rule engine queue depth). Configure cluster autoscaler for node-level scaling. Use KEDA for event-driven scaling from Kafka/SQS metrics. |
| **Evidence** | `docker/docker-compose.yml` (static replica counts: `tb-core1`, `tb-core2`, `tb-mqtt-transport1`, `tb-mqtt-transport2`) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated backup configuration exists. PostgreSQL runs in Docker with no backup_retention_period, no PITR, no snapshot lifecycle. Cassandra volumes are defined in `docker-compose.cassandra.volumes.yml` but with no backup automation. No AWS Backup plans, no S3 versioning, no cross-region replication. |
| **Gap** | No backup or recovery strategy. A Docker volume loss would result in complete data loss. No restore procedures documented or tested. |
| **Recommendation** | Migrating to Aurora PostgreSQL (recommended) provides automated backups with 35-day retention and PITR. For the interim Docker deployment, implement pg_dump scheduled backups to S3 with lifecycle policies. Define and test restore procedures. |
| **Evidence** | `docker/docker-compose.postgres.yml` (no backup config), `docker/docker-compose.cassandra.volumes.yml` (volumes only), absence of any backup automation scripts |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Docker Compose deployment runs on a single host with no multi-AZ configuration. While multiple service replicas exist (2x core, 2x rule-engine), they all run on the same Docker host. PostgreSQL is single-instance with no replication. No cross-AZ or cross-region configuration. Single points of failure: PostgreSQL, ZooKeeper (single instance), HAProxy. |
| **Gap** | Single-host deployment with multiple single points of failure. A host or AZ failure takes down the entire platform. No multi-AZ redundancy for any component. |
| **Recommendation** | Deploy on EKS across 3 AZs with pod anti-affinity rules. Use Aurora PostgreSQL Multi-AZ for database HA. Deploy MSK with multi-AZ broker placement. Use ALB with cross-zone load balancing. |
| **Evidence** | `docker/docker-compose.yml` (single-host deployment), single PostgreSQL instance, single ZooKeeper instance |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure-as-code exists. No Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize manifests, no Ansible playbooks. All infrastructure is defined in Docker Compose files (17+ compose files) which are not IaC for cloud infrastructure provisioning. |
| **Gap** | 100% of cloud infrastructure would need to be manually created (ClickOps) or has no definition at all. No reproducibility, no environment consistency, no disaster recovery automation. |
| **Recommendation** | Adopt AWS CDK (TypeScript or Java) to define EKS cluster, Aurora PostgreSQL, MSK, ElastiCache, VPC networking, and API Gateway. Create Helm charts for ThingsBoard service deployments on EKS. Target 90%+ IaC coverage including monitoring (CloudWatch alarms, dashboards) and DR resources. |
| **Evidence** | Absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or Ansible files in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Three GitHub Actions workflows exist but none perform build, test, or deployment: (1) ATX transform automation (manual dispatch), (2) license header formatting (push trigger), (3) YAML config validation (push trigger). No Maven build in CI, no unit test execution, no container image builds, no deployment pipelines. Build instructions exist in documentation (`mvn install -DskipTests`) but are not automated. |
| **Gap** | No CI/CD pipeline for application code or infrastructure. All builds and deployments are manual. The project's strong test infrastructure (JUnit 5, Testcontainers, 128 black-box tests) is not leveraged in any automated pipeline. |
| **Recommendation** | Implement GitHub Actions CI/CD: Maven build → unit tests → Docker image build/push to ECR → integration tests → deploy to EKS. Add IaC pipeline (CDK deploy) in parallel track. |
| **Evidence** | `.github/workflows/` (3 files, none with build/test/deploy stages), absence of buildspec.yml, Jenkinsfile, or deployment scripts |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Java 25 with Spring Boot 3.5.12 is the primary backend language — extremely current. TypeScript with Angular 20.3.18 is the frontend. Node.js 22 runs the JS executor. AWS SDK v1 (1.12.701) is used for SQS/SNS integrations. The language and framework versions are cutting-edge, but the AWS SDK is one major version behind (v1 vs v2). |
| **Gap** | AWS SDK v1 (1.12.701) is in maintenance mode. Should migrate to AWS SDK v2 for better performance (HTTP/2, non-blocking I/O), modular dependencies, and continued feature development. |
| **Recommendation** | Migrate AWS SDK from v1 (1.12.701) to AWS SDK v2. This affects SQS, SNS, and any future AWS service integrations. The migration is well-documented with the AWS SDK Migration Tool. |
| **Evidence** | Root `pom.xml` (Java 25, spring-boot 3.5.12, aws-java-sdk 1.12.701), `ui-ngx/package.json` (Angular 20.3.18, TypeScript 5.9.3) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard is a modular monolith with identifiable modules (transports, rule engine, core, EDQS) that can optionally deploy as microservices via Kafka. However, all services share a single PostgreSQL database with shared schemas. The `schema-entities.sql` (982 lines) defines a single unified schema accessed by all modules. Cross-module data access exists (rule engine reads device data, core reads alarm data). Transport services have the cleanest separation — they communicate only via Kafka/gRPC. |
| **Gap** | Shared database schema prevents true independent deployment. Database coupling through shared tables, stored procedures, and cross-module JPA queries. Modules cannot be independently versioned, scaled, or deployed without coordinated database changes. |
| **Recommendation** | Apply database-per-service pattern incrementally. Start with transport services (already decoupled). Then extract telemetry/time-series into its own data store (DynamoDB preferred). Extract alarm management from stored procedures into an alarm service with its own schema. |
| **Evidence** | `dao/src/main/resources/sql/schema-entities.sql` (shared 982-line schema), `docker/docker-compose.yml` (multiple services, single Postgres), `dao/src/main/resources/sql/schema-functions.sql` (shared stored procedures) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Inter-service communication is a mix: Kafka for rule engine processing, telemetry flow, and transport-to-core messaging (async). gRPC for cluster coordination and inter-node calls (sync). REST/HTTP for all external API access and some internal calls (sync). The transport services communicate primarily via Kafka (async), but core-to-rule-engine coordination uses both Kafka topics and synchronous gRPC. State changes (device updates, alarm transitions) propagate synchronously within the monolith process. |
| **Gap** | For a stateful-crud system, cross-service state changes should use managed async messaging. Currently, alarm state transitions use synchronous database stored procedures with row-level locking. Device state changes propagate synchronously. Kafka is present but self-managed and not used for all cross-module state propagation. |
| **Recommendation** | Use managed messaging (MSK Serverless or EventBridge) for all cross-service state changes. Extract alarm state transitions from stored procedures into event-driven patterns. Maintain gRPC for low-latency reads where synchronous is appropriate. |
| **Evidence** | `common/queue/src/main/java/org/thingsboard/server/queue/kafka/` (Kafka producer/consumer), `common/proto/src/main/proto/queue.proto` (gRPC definitions), `dao/src/main/resources/sql/schema-functions.sql` (synchronous alarm procedures) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some background job processing exists: OTA firmware updates use Kafka-based async delivery, rule engine processing is inherently async via Kafka topics, and the JS executor runs rule scripts asynchronously. However, device provisioning, bulk operations (import/export), and version control operations appear to run synchronously without status polling. The `tb-vc-executor` is a separate service but its operations may block the calling service. |
| **Gap** | Bulk operations (device import, tenant provisioning), version control operations, and some rule chain operations lack explicit async job patterns with status polling. No job status API for long-running administrative operations. |
| **Recommendation** | Implement async job processing with status polling for bulk operations. Use AWS Step Functions for multi-step provisioning workflows. Add a job status API endpoint for administrative operations that may exceed 30 seconds. |
| **Evidence** | `msa/vc-executor-docker/` (version control executor), rule engine Kafka-based async, absence of job status API patterns in controllers |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API versioning is minimal and inconsistent. The device HTTP API uses `/api/v1/` paths for telemetry and attributes. The RPC API has a v1/v2 split (`/api/plugins/rpc` legacy vs `/api/rpc` new). However, the management REST API (the majority of endpoints) uses flat `/api/` paths with no versioning. No Accept-Version headers or systematic versioning strategy exists. |
| **Gap** | The majority of API endpoints (management API) have no versioning. Breaking changes would affect all consumers simultaneously. Only the device telemetry API (v1) and RPC (v1/v2) have any versioning. |
| **Recommendation** | Implement URL-path versioning (`/api/v1/`, `/api/v2/`) for the management API. Use API Gateway (preferred) to manage API versions, enable gradual migration, and maintain backward compatibility. Define a versioning policy for breaking changes. |
| **Evidence** | Controller annotations using `/api/` (unversioned), `/api/v1/{deviceToken}/telemetry` (device API), `/api/plugins/rpc` and `/api/rpc` (RPC v1/v2 split) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | ZooKeeper-based service discovery via Apache Curator. Services register as ephemeral ZNodes; `PathChildrenCache` watches for join/leave events. Distributed locking via `ZkDistributedLockService`. The discovery system is pluggable with a `DummyDiscoveryService` for monolith mode. Configuration uses environment variables (`ZOOKEEPER_URL`, `ZOOKEEPER_ENABLED`). No hard-coded service endpoints — services discover peers dynamically. |
| **Gap** | ZooKeeper is a self-managed dependency that adds operational overhead. While functional, it requires separate infrastructure management (patching, quorum maintenance). Not cloud-native — EKS provides built-in service discovery. |
| **Recommendation** | Replace ZooKeeper with EKS-native service discovery (Kubernetes DNS + Service resources) or AWS Cloud Map. This eliminates a self-managed component and leverages platform-native capabilities. The pluggable discovery interface (`TbDiscoveryService`) makes this migration straightforward. |
| **Evidence** | `common/queue/src/main/java/org/thingsboard/server/queue/discovery/ZkDiscoveryService.java`, `docker/docker-compose.yml` (zookeeper service), environment variables in `docker/.env` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard stores device firmware images, dashboard configurations, rule chain definitions, and widget bundles as BLOBs in PostgreSQL or on local filesystem. OTA update packages are stored in configurable locations (local filesystem or object storage). No S3 integration for unstructured data storage. No document parsing pipeline for device documentation or manuals. |
| **Gap** | Unstructured data (firmware images, exports, reports) stored in PostgreSQL BLOBs or local filesystem rather than managed object storage. No automated parsing or extraction capabilities for device documentation. |
| **Recommendation** | Migrate binary data (OTA packages, exports, widget resources) to Amazon S3. Implement S3 lifecycle policies for firmware version retention. Consider Amazon Textract for device manual/datasheet parsing in future AI-driven device management features. |
| **Evidence** | `application/src/main/resources/thingsboard.yml` (file storage configuration), PostgreSQL BLOB storage for binary resources |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-structured DAO layer using Spring Data JPA with Hibernate. The `dao/` module provides a centralized repository pattern for all entity access. Custom implementations extend JPA repositories for complex queries. The `ThingsboardPostgreSQLDialect` customizes Hibernate for PostgreSQL-specific features. Some direct SQL exists in stored procedures (6 functions for alarms) bypassing the DAO layer. |
| **Gap** | The DAO layer is mostly centralized but 6 stored procedures bypass it for alarm management. Some direct JDBC/SQL queries exist outside the standard repository pattern for performance-critical paths. |
| **Recommendation** | Extract alarm stored procedure logic into the application DAO layer. This removes database coupling and enables future database migration (e.g., to Aurora or DynamoDB for alarms). Maintain the existing JPA repository pattern as the single data access path. |
| **Evidence** | `dao/src/main/java/org/thingsboard/server/dao/` (centralized DAO module), `dao/src/main/resources/sql/schema-functions.sql` (6 stored procedures bypassing DAO) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | PostgreSQL version is specified via Docker image tag (`postgres:16`) in compose files. Cassandra version 5.0.4 is pinned in the pom.xml driver dependency. TimescaleDB version depends on the base PostgreSQL image. No explicit version-update procedure, no EOL tracking, no migration playbook. PostgreSQL 16 is current (not EOL) but version management is implicit. |
| **Gap** | Versions are implicitly managed via Docker image tags rather than explicitly pinned with lifecycle policies. No documented version-update procedure covering downtime windows, rollback, and risk acknowledgment. EOL tracking is not formalized. |
| **Recommendation** | Explicitly pin database engine versions in IaC (when created). Document a version-update procedure. With Aurora PostgreSQL (recommended), AWS manages engine patching and provides version deprecation notifications. Define a policy to stay within 1 major version of current. |
| **Evidence** | `docker/docker-compose.postgres.yml` (postgres:16 image), root `pom.xml` (cassandra-driver-core 4.17.0), absence of version lifecycle documentation |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | 6 PL/pgSQL stored functions exist for alarm management: create_or_update_active_alarm, update_alarm, acknowledge_alarm, clear_alarm, assign_alarm, unassign_alarm. These use row-level locking (`FOR UPDATE`), return JSON results, and contain business logic (state transitions, timestamp management). All other business logic is in the Java application layer. The stored procedures are limited to a single domain (alarms) and represent a manageable migration scope. |
| **Gap** | Alarm management business logic is coupled to PostgreSQL via stored procedures. These functions use PL/pgSQL-specific constructs (row variables, PERFORM, FOR UPDATE with SKIP LOCKED) that would need translation for any database migration. |
| **Recommendation** | Extract alarm stored procedures into the Java application layer as part of the Move to Managed Databases pathway. Use optimistic locking in JPA instead of database-level row locks. This enables migration to Aurora PostgreSQL and future flexibility to move alarms to DynamoDB. |
| **Evidence** | `dao/src/main/resources/sql/schema-functions.sql` (6 functions, 301 lines) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent infrastructure audit logging exists. The application has its own audit log feature (entity-level audit logging within ThingsBoard for tenant actions), but no infrastructure-level audit trail. No log file validation, no immutable storage, no centralized log aggregation beyond Docker container stdout. |
| **Gap** | No infrastructure audit logging (CloudTrail). No immutable log storage. No centralized log management. Application-level audit logs are stored in PostgreSQL with no immutability guarantees. |
| **Recommendation** | Enable AWS CloudTrail with log file validation and S3 Object Lock for immutable storage. Configure CloudWatch Logs for application log aggregation from EKS pods. Implement log retention policies aligned with compliance requirements. |
| **Evidence** | Absence of `aws_cloudtrail`, CloudWatch log configuration, or centralized logging infrastructure in any configuration file |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration exists. PostgreSQL Docker container uses unencrypted volumes. No KMS key references, no encrypted EBS volumes, no S3 bucket encryption policies. Data including device credentials, tenant secrets, and telemetry is stored unencrypted on Docker volumes. |
| **Gap** | All data at rest is unencrypted — device credentials, API keys, telemetry data, and tenant information. No KMS integration, no disk-level encryption, no database-level encryption. |
| **Recommendation** | Migrating to Aurora PostgreSQL provides encryption at rest by default (AWS-managed or customer-managed KMS keys). Enable EBS encryption for EKS node volumes. Configure S3 bucket default encryption for any object storage. Use customer-managed KMS keys for sensitive data stores. |
| **Evidence** | `docker/docker-compose.postgres.yml` (no encryption config), absence of KMS, EBS encryption, or any encryption-at-rest configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive JWT-based authentication for all management API endpoints. OAuth2 support (GitHub, Apple, custom providers). Two-factor authentication (TOTP, email, SMS, backup codes). API key (PAT) authentication for programmatic access. Rate limiting via Bucket4j. Device authentication uses access tokens, X.509 certificates, or basic credentials. All external endpoints require authentication. |
| **Gap** | Internal service-to-service communication (gRPC, Kafka) relies on network isolation rather than mutual authentication. No mTLS between services. API Gateway-level auth offload is not available (no managed gateway). |
| **Recommendation** | Implement service mesh (Istio or App Mesh) for mTLS between services in EKS. Use API Gateway (preferred) authorizers for external-facing APIs to offload JWT validation. Maintain existing application-level auth as defense in depth. |
| **Evidence** | `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`, JWT filter, OAuth2 mappers, `common/data/src/main/java/org/thingsboard/server/common/data/security/` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ThingsBoard manages its own authentication system with a built-in user database. It CAN federate with external OAuth2 providers (GitHub, Apple, custom OIDC/SAML), but authentication is managed by the application itself. No integration with AWS Cognito, Okta, or enterprise SSO as a primary identity provider. OAuth2 is available as an optional login method, not as the primary identity system. |
| **Gap** | The application manages its own identity store rather than delegating to a centralized IdP. While OAuth2 federation exists, it's an add-on rather than the primary authentication mechanism. Multi-tenant identity management is custom. |
| **Recommendation** | Integrate with Amazon Cognito as the centralized identity provider for platform users. Use Cognito User Pools for user management and federated identity. Maintain device-level authentication (tokens, X.509) separate from user identity. |
| **Evidence** | `application/src/main/java/org/thingsboard/server/service/security/auth/oauth2/` (OAuth2 support), custom user management in `dao/`, absence of Cognito or external IdP as primary |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | All secrets are externalized via `${ENV_VAR:default}` pattern — credentials are not hardcoded in application code. However, Docker environment files contain default values: `SPRING_DATASOURCE_PASSWORD=postgres`, JWT signing key defaults to `thingsboardDefaultSigningKey`, SSL passwords default to `thingsboard`. No integration with AWS Secrets Manager, HashiCorp Vault, or any secrets management system. No automated rotation. |
| **Gap** | Production credentials in environment variables without encryption or rotation. Default passwords committed to repository in Docker env files. No secrets manager integration. The JWT signing key is auto-generated on fresh installs (since v3.4.2) but other credentials use plaintext defaults. |
| **Recommendation** | Integrate AWS Secrets Manager for all production credentials (database passwords, JWT signing keys, API keys). Configure automated rotation for database credentials. Use EKS Secrets Store CSI driver to inject secrets into pods. Remove all default credentials from committed env files. |
| **Evidence** | `docker/.env` (default values), `docker/tb-node.env`, `application/src/main/resources/thingsboard.yml` (`${SPRING_DATASOURCE_PASSWORD:postgres}`), absence of Secrets Manager or Vault references |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker images are based on standard base images (Eclipse Temurin JDK, Node.js official). No evidence of hardened base images (CIS benchmarks, Bottlerocket). No SSM Patch Manager or vulnerability scanning (Inspector, Snyk) integration. SonarQube exclusions exist in pom.xml suggesting historical SAST usage, but no active scanning pipeline. No ECR image scanning configured. |
| **Gap** | Default base images without hardening. No vulnerability scanning for container images. No patching automation. No runtime security monitoring. |
| **Recommendation** | Use Bottlerocket AMIs for EKS nodes (hardened, minimal attack surface). Enable ECR image scanning for all ThingsBoard images. Configure AWS Inspector for runtime vulnerability detection. Build multi-stage Dockerfiles with distroless or minimal base images. |
| **Evidence** | `msa/tb-node/docker/Dockerfile` (standard base image), `pom.xml` (sonar.exclusions suggesting past SonarQube use), absence of Inspector, Snyk, or image scanning config |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No active security scanning in CI/CD. SonarQube exclusion patterns in pom.xml indicate historical SAST usage but no active CI integration. No Dependabot configuration. No container image scanning. No SAST/DAST tools in GitHub Actions workflows. The project does use AntiSamy for XSS protection and Passay for password policy in application code (defensive coding) but no automated pipeline validation. |
| **Gap** | No automated security scanning in any pipeline. No dependency vulnerability scanning (Dependabot, npm audit, OWASP dependency-check). No container scanning. No security gates blocking deployment on critical findings. |
| **Recommendation** | Enable GitHub Dependabot for Maven and npm dependency scanning. Add SAST tooling (SonarQube, Semgrep, or CodeGuru Reviewer) to CI pipeline. Enable ECR image scanning with scan-on-push. Configure security gates to block deployment on critical/high findings. |
| **Evidence** | Absence of `.github/dependabot.yml`, `.snyk`, Semgrep config; `pom.xml` sonar.exclusions (inactive); absence of security scanning in `.github/workflows/` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, no AWS X-Ray, no Jaeger, no Zipkin dependencies in pom.xml or package.json. Prometheus metrics are available but provide counters/gauges, not traces. Inter-service calls via Kafka and gRPC have no trace ID propagation. Debugging cross-service issues requires manual log correlation. |
| **Gap** | No end-to-end tracing across the distributed service architecture. Cannot trace a device telemetry message from transport → rule engine → core → database. No trace ID propagation in Kafka messages or gRPC calls. |
| **Recommendation** | Instrument with OpenTelemetry SDK for Java (auto-instrumentation agent). Configure OTLP export to AWS X-Ray via ADOT collector on EKS. Propagate trace context through Kafka message headers. This enables end-to-end visibility of IoT message processing chains. |
| **Evidence** | Absence of opentelemetry, x-ray, jaeger, or zipkin dependencies in any pom.xml; absence of tracing configuration in thingsboard.yml |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No error budget tracking. Basic Prometheus alerting rules may exist in Grafana dashboards but no formal SLO definitions for critical user journeys (device connectivity, telemetry ingestion latency, API response time, dashboard rendering). |
| **Gap** | No formal SLOs for any user journey. Cannot measure whether the platform meets operator expectations for uptime, latency, or data freshness. No error budget-driven prioritization. |
| **Recommendation** | Define SLOs for critical journeys: device MQTT connection success rate (99.9%), telemetry ingestion p99 latency (<500ms), REST API p99 latency (<200ms), dashboard rendering time (<3s). Implement CloudWatch SLO monitoring with error budget alerts. |
| **Evidence** | Absence of SLO definition files, error budget configurations, or formal availability targets in any configuration or documentation |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus metrics expose infrastructure and application metrics: connected devices count, messages processed per second, rule engine execution time, transport protocol metrics (MQTT sessions, HTTP requests). 10 Grafana dashboards visualize these metrics. However, these are primarily technical metrics — no business outcome metrics (tenant activation rate, device onboarding success rate, alert resolution time). |
| **Gap** | Metrics are infrastructure and application-level (CPU, memory, message throughput) rather than business-outcome-level. No tenant-level SLA tracking, no device onboarding funnel metrics, no alarm resolution time tracking. |
| **Recommendation** | Publish custom CloudWatch metrics for business outcomes: tenant onboarding completion rate, device provisioning success rate, mean-time-to-alarm-resolution, rule chain execution success rate per tenant. Build business dashboards alongside infrastructure dashboards. |
| **Evidence** | `docker/docker-compose.prometheus-grafana.yml` (10 dashboards), `application/src/main/resources/thingsboard.yml` (METRICS_ENABLED, actuator prometheus endpoint) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Prometheus with Grafana provides basic alerting capability. Alert rules can be defined in Grafana for threshold-based monitoring (static thresholds on metrics). No CloudWatch anomaly detection, no ML-based anomaly detection, no dynamic baselines. Alerting is optional and must be manually configured per deployment. |
| **Gap** | Only static threshold alerting is available (if configured). No anomaly detection for gradual degradation, seasonal patterns, or novel failure modes. No automated baseline learning. |
| **Recommendation** | Migrate metrics to CloudWatch with anomaly detection enabled on critical metrics (telemetry ingestion rate, MQTT connection failures, rule engine latency). Use CloudWatch Composite Alarms for multi-signal alerting. Integrate with PagerDuty/OpsGenie for incident routing. |
| **Evidence** | `docker/docker-compose.prometheus-grafana.yml` (Grafana alerting), absence of anomaly detection configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy beyond `docker-compose up`. No blue/green, canary, or rolling deployment configuration. Service updates require manual container restart. No health-check-based traffic shifting. No automated rollback on failure. |
| **Gap** | Direct-to-production deployment with no staged rollout. Any bad deployment affects all users immediately with no automated rollback. No way to test new versions with a subset of traffic. |
| **Recommendation** | Implement canary deployments on EKS using ArgoCD Rollouts or AWS App Mesh. Define health check criteria (error rate, latency) for automatic promotion/rollback. Use EKS rolling updates as minimum viable strategy with readiness probes. |
| **Evidence** | `docker/docker-compose.yml` (no deployment strategy), absence of CodeDeploy, Argo Rollouts, or Flagger configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive black-box test suite: 128 test files covering MQTT/CoAP/HTTP/LWM2M connectivity, rule engine behavior, EDQS operations, and UI smoke tests (Selenium). Infrastructure uses TestNG + Testcontainers + Docker Compose for isolated testing. Supports multiple deployment modes (standalone, Redis cluster, sentinel, hybrid). Unit tests use JUnit 5 + Mockito with DBUnit for database testing. However, these tests are NOT integrated into CI — they run manually or locally. |
| **Gap** | Integration tests exist but do not run in any automated CI pipeline. Test execution is manual. No automated regression testing on pull requests or merges. |
| **Recommendation** | Integrate the black-box test suite into GitHub Actions CI pipeline. Run a subset (smoke tests) on every PR. Run full integration suite on merge to main. Use Testcontainers (already configured) for isolated, reproducible test environments in CI. |
| **Evidence** | `msa/black-box-tests/` (128 test files), Testcontainers dependency in pom.xml, TestNG + Selenium configuration, absence of test execution in `.github/workflows/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response procedures, or automated remediation exist in the repository. No Systems Manager Automation documents, no Lambda-based self-healing, no documented incident response workflows. The monitoring service provides health checks but no automated response to failures. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (database connection exhaustion, Kafka broker failure, transport service crash). No automated remediation. |
| **Recommendation** | Create runbooks for common failure scenarios as SSM Automation documents. Implement auto-remediation for known failure patterns (pod restart on OOM, connection pool reset, Kafka consumer group rebalance). Define escalation paths and on-call rotation. |
| **Evidence** | Absence of runbook files, SSM documents, or incident response documentation anywhere in the repository |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | 10 pre-built Grafana dashboards exist covering different service types (core, rule engine, transports, database, cache, EDQS). Prometheus scrapes all services at `/actuator/prometheus` every 15 seconds. However, no CODEOWNERS for observability assets, no named alarm owners, no team attribution on dashboards or alerts. Monitoring is optional (MONITORING_ENABLED=false by default). |
| **Gap** | Dashboards exist but have no ownership attribution. No team-level SLO definitions. Monitoring is disabled by default. No CODEOWNERS file covering observability configuration. |
| **Recommendation** | Enable monitoring by default. Add CODEOWNERS entries for Grafana dashboards and alerting rules. Define per-service-type observability owners. Create team-attributed CloudWatch dashboards when migrating to AWS. |
| **Evidence** | `docker/docker-compose.prometheus-grafana.yml` (10 dashboards), `docker/.env` (MONITORING_ENABLED=false), absence of CODEOWNERS |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists. No IaC defines any AWS resources, so no tags are applied. No tagging standards, no cost allocation tags, no ownership tags, no environment tags. Docker Compose services have no labels that map to cloud resource tags. |
| **Gap** | No tagging governance. When AWS resources are created for this workload, there will be no cost attribution, no ownership tracking, and no environment identification without establishing tagging standards. |
| **Recommendation** | Define a tagging standard (Environment, Service, Owner, CostCenter, Project) before creating AWS infrastructure. Implement required tags in CDK constructs or Terraform modules. Enable AWS Config rules for tag compliance. Activate cost allocation tags for FinOps. |
| **Evidence** | Absence of any AWS resource definitions, tagging policies, or tag-related configuration in the repository |

---

## Learning Materials

- **Move to Cloud Native**: [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Managed Databases**: [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Managed Analytics**: [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)
- **Move to Modern DevOps**: [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `docker/docker-compose.yml` | INF-Q1, INF-Q4, INF-Q5, INF-Q7, INF-Q9, APP-Q2, APP-Q6 | Main microservices Docker Compose definition (17 services) |
| `docker/docker-compose.postgres.yml` | INF-Q2, INF-Q8, SEC-Q2 | PostgreSQL Docker container definition |
| `docker/docker-compose.kafka.yml` | INF-Q4 | Kafka Docker configuration |
| `docker/docker-compose.prometheus-grafana.yml` | OPS-Q3, OPS-Q4, OPS-Q8 | Prometheus + Grafana monitoring stack |
| `docker/.env` | INF-Q2, APP-Q6, SEC-Q5, OPS-Q8 | Docker environment defaults |
| `docker/tb-node.env` | SEC-Q5 | Service-level environment configuration |
| `application/src/main/resources/thingsboard.yml` | INF-Q2, OPS-Q3, SEC-Q5, DATA-Q1 | Main application configuration (2,207 lines) |
| `dao/src/main/resources/sql/schema-entities.sql` | APP-Q2 | Shared database schema (982 lines) |
| `dao/src/main/resources/sql/schema-functions.sql` | INF-Q3, APP-Q3, DATA-Q2, DATA-Q4 | 6 PL/pgSQL stored functions for alarm management |
| `msa/tb-node/docker/Dockerfile` | INF-Q1, SEC-Q6 | Core service Dockerfile |
| `msa/black-box-tests/` | OPS-Q6 | 128 integration/E2E test files |
| `.github/workflows/` | INF-Q11, SEC-Q7 | 3 GitHub Actions workflows (config validation only) |
| `pom.xml` (root) | APP-Q1, SEC-Q6, SEC-Q7 | Maven build with Java 25, Spring Boot 3.5.12, AWS SDK v1 |
| `ui-ngx/package.json` | APP-Q1 | Angular 20 frontend dependencies |
| `common/queue/src/main/java/org/thingsboard/server/queue/kafka/` | INF-Q4, APP-Q3 | Kafka queue implementation |
| `common/queue/src/main/java/org/thingsboard/server/queue/discovery/ZkDiscoveryService.java` | APP-Q6 | ZooKeeper service discovery |
| `common/proto/src/main/proto/queue.proto` | APP-Q3 | gRPC service definitions |
| `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java` | SEC-Q3 | Security filter chain configuration |
| `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/` | INF-Q3 | 29 rule engine node types |
| `docker/haproxy/` | INF-Q6 | HAProxy load balancer configuration |
