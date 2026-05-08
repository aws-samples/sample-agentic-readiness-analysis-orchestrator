# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Graylog2--graylog2-server |
| **Date** | 2025-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, observability, logging |
| **Context** | Graylog centralized log-management server. |
| **Overall Score** | 1.97 / 4.0 |

**Classification:** 🟠 Remediation Required — This repo has 8 High findings, 9 Medium findings, 3 Low findings. Rule matched: 2-11 High → Remediation Required. MOD classification treats 1 High as Pilot-Ready (a single modernization gap), unlike ARA which treats 1 High as a deployment blocker for agent safety.

**Archetype Justification**: MongoDB is the primary persistent data store with full CRUD lifecycle management (users, streams, configurations, log messages). The application exposes a comprehensive REST API with create/update/delete operations on business entities. While it has cluster fan-out patterns, its primary role is stateful data management with CRUD operations, classifying it as `stateful-crud`.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 1.36 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **1.97 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+2+3+1+1+1+1+1+1+2) / 11 = 15/11 = 1.36
- APP: (4+2+2+2+2+1) / 6 = 13/6 = 2.17
- DATA: (2+3+3+3) / 4 = 11/4 = 2.75
- SEC: (1+1+3+2+2+2+3) / 7 = 14/7 = 2.00
- OPS: (2+1+3+1+1+3+1+1+1) / 9 = 14/9 = 1.56
- Overall: (1.36 + 2.17 + 2.75 + 2.00 + 1.56) / 5 = 9.84/5 = 1.97

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Lambda/Fargate) — no IaC for any compute resources in the repository | Prevents elastic scaling, increases operational overhead for patching and capacity planning |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files in the repository — all infrastructure is provisioned externally/manually | Non-reproducible infrastructure, manual error-prone changes, no disaster recovery automation |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configuration | No forensic analysis capability, compliance risk |
| 4 | OPS-Q2: SLO Definitions | 1 | No SLO definitions or error budget tracking | Cannot measure service level commitments or prioritize reliability investments |
| 5 | OPS-Q5: Deployment Strategy | 1 | No deployment pipeline — CI only, no CD, no blue/green or canary | All deployments are manual with full user impact on failures |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 >= 2 (score: 3) — Graylog has a centralized data access layer via MongoJack/MongoDB driver with entity-level services.
- **What it enables:** Natural language querying of Graylog's operational data (streams, inputs, configurations) via the existing MCP server infrastructure, which already provides tool interfaces for search, aggregation, and resource listing.
- **Additional steps:** The MCP server is already implemented with tools (SearchMessagesTool, AggregateMessagesTool, ListStreamsTool, etc.). This win is partially realized.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repo (docs/ directory, changelog/ fragments, OpenAPI spec, extensive code comments).
- **What it enables:** Developer/operator knowledge assistant that can answer questions about Graylog configuration, troubleshooting, and architecture using existing documentation as corpus.
- **Additional steps:** Index existing documentation and code comments into a vector store. The MCP infrastructure provides the serving layer.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 >= 2 (score: 2) — OpenTelemetry javaagent support exists with Prometheus metrics (200+ metric mappings).
- **What it enables:** Agent that queries Prometheus metrics, correlates with log patterns, and suggests root causes for anomalies.
- **Additional steps:** Need to configure the OTel javaagent in production and set up a metrics store (e.g., Amazon Managed Prometheus) for the agent to query.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2, APP-Q4=2 |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no production container definitions (only test Dockerfile and migration compose) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=3, no commercial DB engines detected (MongoDB and OpenSearch are open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed MongoDB and OpenSearch in docker-compose) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4=3 (managed Kafka client present); no data pipeline/ETL workloads in repo |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=1, OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | AI/agent frameworks ARE present (MCP 1.1.0 with full server implementation) |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Graylog is a modular monolith (APP-Q2=2) with identifiable modules (streams, inputs, security, views, pipelines) but shared MongoDB database, shared in-process EventBus, and shared Disruptor ring buffers creating tight coupling.

**Compute Model Gaps:** No managed compute infrastructure defined in the repository (INF-Q1=1). The application requires self-managed deployment.

**Communication Pattern Gaps:** Inter-component communication is primarily synchronous via Guava EventBus (in-process) with MongoDB-polled ClusterEventBus for cross-node events (APP-Q3=2). Long-running operations use a custom Periodical framework with no async job status API (APP-Q4=2).

**Recommended Decomposition Approach:** Strangler Fig pattern — incrementally extract high-value modules (e.g., alerting/events, pipeline processing, data archiving) into independent services while the monolith continues serving core log management.

**Representative AWS Services:** EKS (preferred per context), Amazon DocumentDB (MongoDB-compatible), Amazon OpenSearch Service, EventBridge (preferred), API Gateway (preferred), Step Functions for workflow orchestration.

**Recommended Patterns:** Anti-corruption Layer, Event Sourcing (for log event processing), Hexagonal Architecture for extracted services.

**Links:** [AWS Modernization: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** No production containerization. Only a test Dockerfile (eclipse-temurin:21-jre-jammy base) and migration docker-compose files exist. The application is distributed as a tarball/package for self-managed deployment.

**Container Readiness Indicators:** The application already has a working test Dockerfile demonstrating it can run in a container. Configuration is externalized via `graylog.conf`. Port bindings are configurable. The Java 21 runtime with Temurin JRE is container-friendly.

**Recommended Container Orchestration:** Amazon EKS (per preferences). EKS provides managed Kubernetes orchestration that can handle Graylog's stateful nature with StatefulSets and persistent volumes.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS App Mesh for service mesh.

**Migration Approach:** Lift-and-containerize — create a production Dockerfile from the existing test Dockerfile, add health check endpoints, configure Kubernetes manifests with proper resource limits and persistent volumes for the journal.

**Links:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** MongoDB is self-managed (connection string `mongodb://localhost/graylog` in config). OpenSearch/Elasticsearch are also self-managed — the data-node module manages OpenSearch instances but they are not AWS-managed services.

**Engine Versions:** MongoDB 7.0/8.0 (docker-compose), OpenSearch 2.19.3 (CI matrix). No EOL engines detected but no explicit version pinning in production IaC (none exists).

**Data Access Patterns:** Centralized MongoJack-based data access layer (DATA-Q2=3). Clean entity-service pattern with MongoDB collections per domain object.

**Recommended Managed Database Targets:**
- MongoDB → Amazon DocumentDB (MongoDB-compatible) — per preferences favoring Aurora, DocumentDB provides managed MongoDB compatibility
- OpenSearch → Amazon OpenSearch Service — fully managed, eliminates the need for the data-node self-management module
- For new microservices extracted via decomposition: Amazon DynamoDB (per preferences)

**Representative AWS Services:** Amazon DocumentDB, Amazon OpenSearch Service, Amazon DynamoDB (for new services).

**Migration Tools:** AWS Database Migration Service (DMS) for MongoDB → DocumentDB migration.

**Links:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** Zero IaC files in the repository (INF-Q10=1). All infrastructure is provisioned externally or manually.

**Current CI/CD State:** GitHub Actions provides CI (build, test) but no deployment automation (INF-Q11=2). Four parallel build jobs with matrix testing but no deploy stage.

**Deployment Strategy Gaps:** No deployment automation, no blue/green, no canary (OPS-Q5=1). Releases are published to Sonatype Nexus but actual deployment to production infrastructure is manual.

**Testing Gaps:** Integration tests exist and run in CI (OPS-Q6=3). This is a strength that the DevOps modernization can build upon.

**Recommended DevOps Toolchain:**
- IaC: Terraform or AWS CDK for EKS cluster, DocumentDB, OpenSearch Service provisioning
- CI/CD: Extend GitHub Actions with deploy stages using AWS CodeDeploy or ArgoCD for EKS
- Deployment: EKS with ArgoCD for GitOps-based canary deployments

**Representative AWS Services:** AWS CDK, CodeBuild, CodePipeline, ECR, EKS with ArgoCD.

**Links:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

APP-Q2 scored 2 (monolith with identifiable modules but shared database and coupling). A decomposition strategy is warranted.

### Approach Recommendation: Strangler Fig (Parallel Track)

**Why this approach:** Graylog has identifiable modules (streams, inputs, pipelines, events/alerts, views/dashboards, security, archiving) with shared MongoDB access. The modules have recognizable boundaries despite coupling through the EventBus and shared database. The Strangler Fig approach allows incremental extraction while the monolith continues serving core log ingestion and search.

**Recommended extraction order (by business value and decoupling feasibility):**
1. **Alerting/Events Engine** — Already somewhat isolated in `org.graylog.events`; high-value for independent scaling
2. **Pipeline Processing** — Stateless rule evaluation can be extracted as an event processor
3. **Data Archiving/Lake** — S3-based archival logic is naturally decoupled from real-time search
4. **User/Auth Service** — Security domain has clear boundaries

### Pattern Recommendations

| Pattern | Purpose | Application |
|---------|---------|-------------|
| **Anti-corruption Layer** | Isolate extracted services from MongoDB-centric data model | Place ACL between each new service and the remaining monolith's MongoDB collections |
| **Event Sourcing** | Capture log processing state changes as events | Natural fit for Graylog's log processing pipeline — events already flow through Disruptor ring buffers |
| **Saga Pattern** | Manage distributed transactions across extracted services | Apply when alerting triggers span multiple services (e.g., alert → notification → escalation) |
| **Hexagonal Architecture** | Structure each new service with clean boundaries | Apply to every extracted service — keeps them testable and infrastructure-portable |

### Effort Estimation

| Factor | Signal | Impact |
|--------|--------|--------|
| Module boundaries | Clear package structure with 40+ domain packages | Low effort — boundaries exist |
| Data coupling | Shared MongoDB with cross-module collection access | High effort — data separation required |
| Stored procedures | None (MongoDB, no stored procedures) | Low effort |
| Communication patterns | In-process EventBus (needs replacement with external events) | Medium effort |
| CI/CD maturity | CI exists, no CD | Medium effort — need to build deployment pipeline |
| Test coverage | Strong unit and integration tests | Low effort — regression safety net exists |

**Calibrated Estimate:** Medium to High — 6-12 months for first 2-3 service extractions, leveraging the existing test suite for regression safety.

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure defined in the repository. No Terraform, CloudFormation, CDK, or other IaC defining ECS, EKS, Lambda, Fargate, or EC2 resources. The application is packaged for self-managed deployment (tarball/package distribution via Sonatype Nexus). |
| **Gap** | All compute is self-managed with no managed container orchestration or serverless adoption. |
| **Recommendation** | Containerize the application and deploy on Amazon EKS (per preferences). Create a production Dockerfile from the existing test Dockerfile, define Kubernetes manifests with StatefulSets for the journal-dependent components, and use Fargate profiles for stateless workers. |
| **Evidence** | No IaC files found. Only test Dockerfile at `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile`. Migration docker-compose at `data-node/migration/docker-compose.yml`. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed. MongoDB is referenced via `mongodb://localhost/graylog` in configuration. OpenSearch is managed by the custom data-node module. Docker-compose files define self-hosted MongoDB 7.0 and OpenSearch 2.10 instances. No managed database services (RDS, DocumentDB, Amazon OpenSearch Service) are configured. |
| **Gap** | All databases self-managed with no managed service adoption. This creates operational burden for patching, backup, scaling, and failover. |
| **Recommendation** | Migrate MongoDB to Amazon DocumentDB (MongoDB-compatible) and OpenSearch to Amazon OpenSearch Service. Both provide automated backups, Multi-AZ failover, and managed patching. The data-node module would be replaced by the managed OpenSearch Service. |
| **Evidence** | `misc/graylog.conf` (mongodb_uri), `data-node/migration/docker-compose.yml` (MongoDB 7, OpenSearch 2.10 services), `data-node/` module (custom OpenSearch management). |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has multi-step workflows (migration sequences, index rotation with retention, event correlation with alerting) implemented as hardcoded state machines in the custom Periodical framework. 26+ scheduled background tasks manage complex workflows including leader-only tasks with election-based start/stop. No dedicated workflow orchestration service (Step Functions, Temporal) is used. |
| **Gap** | Workflows are hardcoded in application code with the custom Periodical framework. No dedicated orchestration service provides visibility, retry logic, or error handling beyond what's coded manually. |
| **Recommendation** | Adopt AWS Step Functions (or Temporal) for multi-step operations like index rotation, data migration, and event correlation workflows. This provides visual workflow management, automatic retries, and state persistence without custom infrastructure. EventBridge (preferred) can trigger workflows based on system events. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/periodical/` (26+ Periodical classes), `graylog2-server/src/main/java/org/graylog2/indexer/rotation/` (rotation strategy), custom `AbstractIdleService` lifecycle management. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application uses Kafka 4.2.0 and AMQP Client 5.29.0 as external input transports for log ingestion. Internally, it uses LMAX Disruptor ring buffers for high-performance message processing and Guava EventBus for in-process pub/sub. The ClusterEventBus uses MongoDB polling for cross-node events. Kafka and AMQP are used as managed client libraries connecting to external brokers — not self-managed brokers within this application. |
| **Gap** | Cross-node cluster events use MongoDB polling (ClusterEventBus) rather than managed messaging. This is a custom implementation with polling latency and MongoDB coupling. |
| **Recommendation** | For cross-node cluster events, consider migrating the ClusterEventBus from MongoDB polling to Amazon EventBridge (preferred per context) or Amazon SQS for decoupled, low-latency event propagation. The external Kafka/AMQP inputs are appropriately used as client-side integrations. |
| **Evidence** | Root `pom.xml` (kafka-clients 4.2.0, amqp-client 5.29.0), `graylog2-server/src/main/java/org/graylog2/events/ClusterEventBus.java`, LMAX Disruptor usage in message processing pipeline. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security configuration exists in the repository. No VPC, subnet, security group, or NACL definitions. No IaC files defining network topology. The application configuration shows TLS disabled by default (`http_enable_tls = false`) in `misc/graylog.conf`. |
| **Gap** | No network segmentation, no VPC configuration, no security groups defined. TLS is disabled by default. The deployment network topology is entirely external to this repository. |
| **Recommendation** | Define VPC infrastructure with private subnets for Graylog, DocumentDB, and OpenSearch Service. Use security groups with least-privilege rules. Enable TLS by default. Consider VPC endpoints for AWS service access and VPC Lattice for service-to-service communication. |
| **Evidence** | No IaC files. `misc/graylog.conf` (`http_enable_tls = false`). No Terraform, CloudFormation, or Kubernetes NetworkPolicy files. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or managed entry point configured. The Graylog server exposes its REST API directly on configurable ports. The LB status endpoint (`/system/lbstatus`) indicates load balancer integration is expected but not defined in the repository. |
| **Gap** | Services exposed directly with no managed gateway or load balancer defined. No throttling, request validation, or centralized auth at the entry point. |
| **Recommendation** | Deploy behind API Gateway (preferred per context) or an Application Load Balancer. API Gateway provides throttling, request validation, and centralized authentication. For the ingest path (high-throughput log reception), use a Network Load Balancer. |
| **Evidence** | `misc/graylog.conf` (direct port binding), `graylog2-server/src/main/java/org/graylog2/rest/resources/system/LoadBalancerStatusResource.java` (LB status endpoint exists but no LB defined). |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No ASG, ECS auto-scaling, or Kubernetes HPA definitions. The application supports clustering (multiple nodes with leader election) but scaling is entirely manual. |
| **Gap** | All capacity is statically provisioned. No automatic response to traffic spikes or scale-down during low demand. |
| **Recommendation** | After containerizing on EKS, configure Horizontal Pod Autoscaler (HPA) based on custom Prometheus metrics (e.g., journal utilization, input buffer usage). For DocumentDB, configure auto-scaling on read replicas. For OpenSearch Service, use Auto-Tune. |
| **Evidence** | No IaC files. No auto-scaling resources. Manual cluster sizing via configuration. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists in the repository. No AWS Backup plans, no RDS backup retention, no S3 versioning, no snapshot lifecycle policies. Database backup is entirely external to this codebase. |
| **Gap** | No backup configuration found. Data recovery depends entirely on external operational procedures not defined here. |
| **Recommendation** | After migrating to managed databases: enable automated backups on DocumentDB (configurable retention, PITR), enable snapshot policies on Amazon OpenSearch Service, and define an AWS Backup plan covering all data stores with cross-region replication for critical data. |
| **Evidence** | No IaC files. No backup-related configuration. No `aws_backup_plan`, no `backup_retention_period` settings. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Multi-AZ configuration exists in the repository. While the application architecture supports clustering (multiple Graylog nodes with MongoDB-based leader election), there is no infrastructure definition ensuring AZ distribution. The docker-compose migration files run everything on a single host. |
| **Gap** | No AZ configuration found. Cluster architecture supports HA in principle but without infrastructure guarantees of AZ distribution. |
| **Recommendation** | After deploying on EKS, configure pod anti-affinity rules to spread Graylog pods across AZs. Use Multi-AZ DocumentDB clusters. Amazon OpenSearch Service provides Multi-AZ by default. Configure EKS node groups across 3 AZs. |
| **Evidence** | No IaC files. `data-node/migration/docker-compose.yml` (single-host deployment). Leader election in `graylog2-server/src/main/java/org/graylog2/cluster/` (assumes multiple nodes but no AZ awareness). |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files. All infrastructure is created and managed externally — either manually or in a separate repository not included here. |
| **Gap** | No IaC — all infrastructure is created outside this repository with no reproducibility or version control of infrastructure definitions. |
| **Recommendation** | Create IaC (Terraform or AWS CDK) defining: EKS cluster, DocumentDB cluster, OpenSearch Service domain, VPC/networking, ALB/API Gateway, IAM roles, CloudWatch alarms, and backup plans. Store IaC alongside the application code or in a linked infrastructure repository. |
| **Evidence** | No `.tf`, `.tfvars`, `template.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found anywhere in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides CI automation with 4 parallel jobs (build-artifacts, frontend-tests, backend-tests, full-backend-tests) running on Ubuntu 4-core runners with JDK 21. Matrix testing covers OpenSearch 2.19.3/MongoDB 8.0 and DataNode/MongoDB 7.0. However, there is no deployment automation — the pipeline ends at build and test. Releases are published to Sonatype Nexus via GPG-signed Maven deploy, which is semi-automated. |
| **Gap** | Build is automated but deployment is manual. No CD pipeline deploying to production infrastructure. No automated rollback capability. |
| **Recommendation** | Extend GitHub Actions with deployment stages: build container image → push to ECR → deploy to EKS staging → run smoke tests → promote to production. Use ArgoCD for GitOps-based deployment to EKS with automatic rollback on health check failure. |
| **Evidence** | `.github/workflows/build.yml` (4 parallel CI jobs), `.github/dependabot.yml` (dependency scanning), no deploy stage in any workflow. |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 21 (latest LTS) with modern framework stack: Google Guice 7.0.0, Jersey 4.0.2 (Jakarta EE/JAX-RS 4.0), Jackson 2.21.2. Already migrated to Jakarta namespace. Frontend uses TypeScript 5.9.3 with React 18.3.1. AWS SDK v2 (2.42.1) is present alongside legacy v1 (1.12.675). First-class cloud-native language at current version with modern frameworks. |
| **Gap** | N/A — language and framework stack is mature and current. Minor note: dual AWS SDK (v1 + v2) presence indicates incomplete SDK migration. |
| **Recommendation** | Complete the AWS SDK v1 → v2 migration to consolidate on the modern SDK. Otherwise, no language/framework modernization needed. |
| **Evidence** | Root `pom.xml` (Java 21, Guice 7.0.0, Jersey 4.0.2, Jakarta EE, AWS SDK v2 2.42.1, AWS SDK v1 1.12.675), `graylog2-web-interface/package.json` (TypeScript 5.9.3, React 18.3.1). |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Graylog is a modular monolith with 40+ domain packages under `org.graylog2.*` and a plugin architecture via Guice modules. Identifiable modules include: streams, inputs, security, views/dashboards, pipelines, events/alerts, archiving, and the data-node. However, modules share a single MongoDB instance with cross-module collection access, communicate via in-process Guava EventBus, and share LMAX Disruptor ring buffers. The data-node is a separate deployable but tightly coupled to the main server. |
| **Gap** | Monolith with identifiable modules but shared database schemas, shared in-process communication (EventBus, Disruptor), and no independent deployability of modules. Cross-module data access is direct via shared MongoDB collections. |
| **Recommendation** | Apply Strangler Fig pattern to incrementally extract high-value modules (alerting/events, pipeline processing, archiving) into independent services. Start by establishing per-module database schemas/collections and replacing in-process EventBus with external events (EventBridge). See Decomposition Strategy section. |
| **Evidence** | Package structure under `graylog2-server/src/main/java/org/graylog2/` (40+ packages), `org/graylog/events/`, `org/graylog/plugins/views/`, shared MongoDB access via MongoJack, Guava EventBus (`@Subscribe` annotations in 30+ classes), LMAX Disruptor ring buffers. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Inter-component communication is primarily synchronous. The `ProxiedResource` pattern fans out HTTP requests to all cluster nodes synchronously via OkHttp/Retrofit2. Cross-node events use MongoDB-polled ClusterEventBus (pseudo-async with polling latency). In-process communication uses Guava EventBus (synchronous dispatch). External input transports (Kafka, AMQP) are async for ingestion but not for internal coordination. |
| **Gap** | Primarily synchronous with some async for background jobs (Periodicals). Cross-service coordination (cluster-wide operations) is synchronous HTTP fan-out — a cascading failure risk when nodes are unhealthy. |
| **Recommendation** | Replace synchronous cluster fan-out with async messaging via EventBridge or SQS for cross-node state changes and notifications. Keep synchronous reads for configuration queries. The custom ClusterEventBus (MongoDB polling) should migrate to EventBridge for near-real-time event propagation. |
| **Evidence** | `ProxiedResource` pattern (synchronous HTTP fan-out), `ClusterEventBus` (MongoDB polling), Guava EventBus (synchronous in-process), `RemoteInterfaceProvider` (Retrofit2 clients for node-to-node calls). |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Long-running operations (index rotation, data migration, cluster-wide maintenance) are handled by the custom Periodical framework running on a 30-thread ScheduledThreadPoolExecutor. These are background processes but provide no status polling API, no callbacks, and no external visibility into progress. The job scheduler (`org.graylog.scheduler`) manages scheduled jobs with status tracking in MongoDB, which is a partial implementation. |
| **Gap** | Some background job processing exists (Periodicals, job scheduler) but inconsistent patterns. Index rotation and maintenance operations block without status feedback. No unified async job API with status polling for operations exceeding 30 seconds. |
| **Recommendation** | Implement an async job status API for long-running operations. For multi-step workflows (index rotation, data migration), adopt Step Functions to provide visibility, status tracking, and automatic retries. Expose job status via REST endpoint with progress/completion callbacks. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/periodical/` (26+ scheduled tasks), `org/graylog/scheduler/` (job scheduler with MongoDB-backed status), ScheduledThreadPoolExecutor with 30 threads. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The REST API uses a flat `/api/` prefix with domain-based paths (e.g., `/api/cluster/inputstates`, `/api/system/loggers`, `/api/streams`). No `/v1/`, `/v2/` URL patterns, no `Accept-Version` headers, no versioning annotations found. Some API evolution is managed through Swagger annotations and the OpenAPI spec, but no formal backward compatibility guarantee exists. |
| **Gap** | No versioning applied — API changes are deployed directly without versioning. Less than half of the API surface uses any versioning scheme. |
| **Recommendation** | Introduce API versioning using URL path prefixes (`/api/v1/`) for external-facing endpoints. Use API Gateway's stage-based versioning when deploying behind API Gateway. Define a backward compatibility policy for the REST API. |
| **Evidence** | REST resource classes under `graylog2-server/src/main/java/org/graylog2/rest/resources/` (flat `/api/` paths), `api-specs/stream-output-filters.yml` (OpenAPI 3.1.0 spec without version in path), Swagger 2.2.45 annotations. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Service discovery uses a custom MongoDB-based node registry. Each Graylog node registers its HTTP URI in a MongoDB collection. Other nodes discover peers by querying MongoDB. Leader election uses MongoDB distributed locks. No standard service discovery mechanism (DNS, Consul, AWS Cloud Map, Kubernetes Service) is used. Endpoints are effectively hard-coded in MongoDB entries. |
| **Gap** | All service endpoints are registered in MongoDB with no dynamic discovery mechanism. This couples service discovery to the database and creates a single point of failure for discovery. |
| **Recommendation** | After migrating to EKS, leverage Kubernetes Service discovery (DNS-based) for pod-to-pod communication. For external service integration, use AWS Cloud Map or API Gateway service integrations. Remove MongoDB as the discovery mechanism — let the container orchestrator handle it. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog2/cluster/` (MongoDB-based node registry), `NodeService` interface, leader election via MongoDB locks, `RemoteInterfaceProvider` creating clients from stored URIs. |

---

### Data Platform (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Graylog stores log data (unstructured/semi-structured) in OpenSearch/Elasticsearch indices. There is also S3 integration for data archiving (AWS SDK present for S3 operations in the archiver module). The S3 archiver uses Iceberg table format for structured access. However, the primary unstructured data (log messages) lives in the search engine, not S3, with limited parsing pipeline for documents beyond log fields. |
| **Gap** | Data in managed storage (OpenSearch) but not S3 for the primary log store. S3 archiving exists for cold data but the active dataset requires the search engine for access. No automated parsing pipeline for extracting insights from archived data. |
| **Recommendation** | Leverage the existing S3 archiver with Iceberg format. Add Athena for querying archived data in S3 without needing to restore to OpenSearch. Consider Amazon S3 as the primary long-term store with Amazon OpenSearch Service for hot/warm data and Athena for cold analytics. |
| **Evidence** | AWS SDK S3 usage in archiver module, Iceberg table format references, `data-node/` managing OpenSearch, `prometheus-exporter.yml` (data lake S3/Iceberg I/O metrics). |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | MongoDB access is centralized through MongoJack (ORM-like mapping layer) with entity-level service classes providing CRUD operations. Each domain entity has a dedicated service class (e.g., `StreamService`, `InputService`, `UserService`) that encapsulates MongoDB operations. Some direct MongoDB access exists in migration classes and auxiliary code paths, but the primary pattern is consistent. |
| **Gap** | Mostly centralized with some direct access in migrations and auxiliary code. Not all modules strictly use the service layer — some have direct collection access for performance-critical operations. |
| **Recommendation** | Maintain the current MongoJack-based data access pattern. When extracting microservices, ensure each service gets its own data access layer with clearly defined collection ownership. No immediate action needed — this is a strength. |
| **Evidence** | MongoJack 5.1.0 in `pom.xml`, entity service classes under `graylog2-server/src/main/java/org/graylog2/` (StreamServiceImpl, InputServiceImpl, UserServiceImpl), migration classes with direct MongoDB operations. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database engine versions are specified in docker-compose and CI matrix: MongoDB 7.0 and 8.0, OpenSearch 2.19.3. These are current versions with no EOL risk. However, versions are only pinned in CI/test configurations — there is no production IaC pinning engine versions. The Dependabot configuration explicitly ignores OpenSearch client updates (manual control). |
| **Gap** | Versions pinned in CI/test but no production IaC exists to enforce version pinning. No documented version-update procedure covering downtime windows and rollback. |
| **Recommendation** | When creating IaC for managed databases, explicitly pin engine versions in DocumentDB and OpenSearch Service configurations. Define a version upgrade procedure document covering testing, rollback, and downtime windows. |
| **Evidence** | `data-node/migration/docker-compose.yml` (MongoDB 7.0, OpenSearch 2.10), `.github/workflows/build.yml` (MongoDB 8.0, OpenSearch 2.19.3 in CI matrix), `.github/dependabot.yml` (opensearch-java client ignored). |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. MongoDB is schema-less with no server-side execution. All business logic resides in the Java application layer. The only database-level operations are index creation and aggregation pipelines, which are standard MongoDB operations. Minimal use of MongoDB-specific aggregation framework for performance-critical queries. |
| **Gap** | Minimal stored procedure equivalent — some MongoDB aggregation pipelines are used for performance-critical operations, which creates minor MongoDB coupling. These are not blocking for migration but would need translation for DocumentDB compatibility. |
| **Recommendation** | Verify that MongoDB aggregation pipelines used in the codebase are compatible with Amazon DocumentDB. DocumentDB supports most aggregation operators but has some differences. Run the DocumentDB compatibility assessment tool before migration. |
| **Evidence** | No `.sql` files, no `CREATE PROCEDURE`, no stored triggers. Java-based migrations in `graylog2-server/src/main/java/org/graylog2/migrations/` (~52 migration classes, all application-layer logic). MongoJack-based data access. |

---

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration in the repository. Graylog itself is a log management tool with internal audit capabilities (user action logging, access logs) but no CloudTrail infrastructure audit trail is defined. OpenSearch security audit logging is configured in `data-node/src/main/resources/opensearch/config/opensearch-security/audit.yml` but this covers only the OpenSearch layer, not the broader infrastructure. |
| **Gap** | No CloudTrail or equivalent infrastructure-level audit logging. The application logs its own actions but the surrounding infrastructure has no audit trail. |
| **Recommendation** | Enable CloudTrail with log file validation and immutable storage (S3 Object Lock) for all AWS API operations. Route CloudTrail logs into the Graylog instance itself for centralized audit analysis. Define in IaC: `aws_cloudtrail` with `enable_log_file_validation = true` and S3 bucket with object lock. |
| **Evidence** | No `aws_cloudtrail` in any IaC (no IaC exists). `data-node/src/main/resources/opensearch/config/opensearch-security/audit.yml` (OpenSearch-level audit only). |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration exists. No KMS key definitions, no encryption settings on data stores. The docker-compose files run MongoDB and OpenSearch without encryption. The `misc/graylog.conf` has a `password_secret` for internal encryption of stored credentials (EncryptedValue mechanism) but no infrastructure-level encryption at rest for the databases or journal. |
| **Gap** | No encryption at rest configured for MongoDB data, OpenSearch indices, or the Kafka journal. Only application-level password encryption exists (EncryptedValue for stored credentials). |
| **Recommendation** | After migrating to managed databases: enable encryption at rest on DocumentDB (KMS-encrypted, enabled by default), OpenSearch Service (KMS encryption at rest), and EBS volumes for any stateful containers. Define customer-managed KMS keys with rotation policy in IaC. |
| **Evidence** | No IaC with encryption settings. `misc/graylog.conf` (`password_secret` for EncryptedValue only). `data-node/migration/docker-compose.yml` (no encryption configuration on MongoDB or OpenSearch volumes). |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The REST API uses Apache Shiro 2.1.0 for authentication with multiple backends: session-based auth, token-based auth, LDAP/AD integration. JWT (jjwt 0.13.0) is used for token-based authentication. All API endpoints require authentication (enforced by Shiro filter). The MCP server has its own permission helper for authorization. Internal-only endpoints are protected by the same auth framework. |
| **Gap** | Token-based auth (JWT) exists on all external endpoints. However, the system uses both session-based and token-based auth (mixed model). No OAuth2 standard flow — proprietary token mechanism. Internal cluster communication may bypass auth within the trusted network. |
| **Recommendation** | Standardize on OAuth2/OIDC for external API authentication when deploying behind API Gateway. Use API Gateway authorizers (Cognito or custom Lambda) for the external surface. Internal cluster communication can remain token-based with mTLS. |
| **Evidence** | Apache Shiro 2.1.0, jjwt 0.13.0 in `pom.xml`, `graylog2-server/src/main/java/org/graylog/security/` (auth framework), `graylog2-server/src/main/java/org/graylog2/security/` (Shiro integration), MCP `PermissionHelper.java`. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application integrates with LDAP and Microsoft Active Directory for authentication via the `authservice` framework (`LDAPAuthServiceBackend`, `ADAuthServiceBackend`). It can federate with these external IdPs. However, there is no SAML, OIDC, or OAuth2 SSO integration in the open-source codebase. The primary auth is still the internal MongoDB-backed user store with optional LDAP/AD federation. |
| **Gap** | Application has its own auth (MongoDB-based) but can federate with LDAP/AD. No modern SSO protocols (SAML, OIDC, OAuth2) for centralized identity. Enterprise SSO may be in the commercial version but is not present here. |
| **Recommendation** | Integrate with Amazon Cognito as a centralized IdP with OIDC/SAML support. Cognito can federate with existing LDAP/AD backends while providing standard OAuth2/OIDC flows. This enables SSO across the Graylog ecosystem and other AWS-hosted applications. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/security/authservice/backend/LDAPAuthServiceBackend.java`, `ADAuthServiceBackend.java`, `MongoDBAuthServiceBackend.java` (internal auth), no SAML/OIDC configuration files. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials are committed in production source code. The `misc/graylog.conf` is a sample configuration file with empty `password_secret` and placeholder `root_password_sha2`. Docker-compose files reference `.env` files for secrets. The application has an internal `EncryptedValue`/`EncryptedValueService` mechanism for encrypting stored credentials at the application level. However, no external secrets manager (AWS Secrets Manager, HashiCorp Vault) is integrated. Production credentials would be in environment variables or config files at deployment time. |
| **Gap** | No external secrets manager integration. Production credentials are expected in environment variables or config files without rotation. The internal EncryptedValue mechanism protects stored credentials but does not provide rotation or centralized management. |
| **Recommendation** | Integrate AWS Secrets Manager for all production credentials (MongoDB connection string, OpenSearch credentials, LDAP bind passwords, SMTP credentials). Configure automated rotation for database credentials. Reference secrets via environment variables injected from Secrets Manager (EKS CSI Secrets Store driver or init containers). |
| **Evidence** | `misc/graylog.conf` (placeholder secrets), `data-node/migration/docker-compose.yml` (`.env` file references), `EncryptedValueService` (internal encryption), no imports of `software.amazon.awssdk.services.secretsmanager` or Vault clients. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The test Dockerfile uses `eclipse-temurin:21-jre-jammy` as the base image (an official, maintained image). Dependabot provides dependency vulnerability scanning with daily checks. The Maven pom includes 6 explicit CVE mitigations via dependency overrides (log4j2, json-smart, avro, commons-compress, mina-core, lz4-java). Maven Enforcer plugin bans known-vulnerable dependencies. However, no SSM Patch Manager, AWS Inspector, or container image scanning is configured. |
| **Gap** | Default base images with no hardening. Dependabot provides dependency scanning but no container image scanning or runtime vulnerability scanning. No patching automation for deployed infrastructure. |
| **Recommendation** | Use a hardened base image (Amazon Corretto on Amazon Linux 2023, or Bottlerocket for EKS nodes). Enable ECR image scanning for container vulnerabilities. Add AWS Inspector for runtime vulnerability assessment. Consider a multi-stage Dockerfile with minimal runtime image. |
| **Evidence** | `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile` (eclipse-temurin:21-jre-jammy), `.github/dependabot.yml` (daily scans), `pom.xml` (6 CVE overrides, Maven Enforcer). |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Dependabot is configured with 8 ecosystem configurations scanning daily. SpotBugs and PMD are configured as Maven plugins but explicitly skipped in CI (`-Dspotbugs.skip=true`). Error Prone provides compile-time bug detection (active). ForbiddenAPIs enforces banned API usage. CycloneDX SBOM generation is configured but skipped in test runs. The pipeline has dependency scanning (Dependabot) running but no SAST tool actively blocking on findings in CI. |
| **Gap** | Dependency scanning configured and running (Dependabot). Static analysis tools exist (SpotBugs, PMD, Error Prone) but SpotBugs is explicitly skipped in CI. No container scanning. No blocking security gate in the pipeline. |
| **Recommendation** | Enable SpotBugs in CI (remove `-Dspotbugs.skip=true`). Add ECR image scanning when container images are built. Configure a security gate that blocks merges on critical/high findings. Consider adding Semgrep or CodeGuru Reviewer for SAST coverage beyond bug patterns. |
| **Evidence** | `.github/dependabot.yml` (8 ecosystems, daily), `.github/workflows/build.yml` (SpotBugs skipped), `pom.xml` (SpotBugs, PMD, Error Prone, ForbiddenAPIs, CycloneDX configured), `config/spotbugs-exclude.xml`, `config/pmd-rules.xml`. |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | OpenTelemetry Java Agent support exists with a `TracerProvider` obtaining tracers from `GlobalOpenTelemetry`. Custom semantic attributes are defined (`GraylogSemanticAttributes`) for lookup tables, periodicals, jobs, and schedulers. However, no explicit span creation exists in production code — all tracing depends on javaagent auto-instrumentation. Cross-service trace propagation (between Graylog nodes) is not explicitly implemented. |
| **Gap** | Basic tracing support on individual nodes via OTel javaagent but no custom span creation for business operations and no explicit cross-service trace propagation between cluster nodes. |
| **Recommendation** | Add explicit span creation for key business operations (message processing pipeline, search queries, alert evaluation). Propagate trace context in the `ProxiedResource` HTTP headers when fanning out to cluster nodes. Configure X-Ray or Amazon Managed Grafana as the trace backend. |
| **Evidence** | `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java`, `GraylogSemanticAttributes.java`, `TracingModule.java`, OpenTelemetry 1.60.1 in `pom.xml`. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking, no p99/p95 latency targets, no availability targets defined. The application exposes Prometheus metrics (200+ metric mappings) which could be used for SLO measurement, but no SLO definitions exist. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for log ingestion latency, search response time, or availability. |
| **Recommendation** | Define SLOs for critical user journeys: log ingestion latency (p99 < Xms), search response time (p99 < Xs), API availability (99.9%). Implement error budget tracking using the existing Prometheus metrics. Use Amazon Managed Grafana with SLO dashboards. |
| **Evidence** | No SLO definitions in any configuration, documentation, or code file. `prometheus-exporter.yml` (200+ metrics available for SLO measurement but unused for this purpose). |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Prometheus exporter configuration defines 200+ metrics including business-relevant metrics: stream incoming messages rates, journal utilization, pipeline/rule execution times, event processor execution (aggregation + correlation), input connections and message rates, traffic throughput (input/output/decoded), and data lake I/O metrics. These go beyond pure infrastructure metrics and track business outcomes (messages processed, events triggered, pipeline latency). |
| **Gap** | Business metrics tracked but not systematically across all features. Some features lack specific business outcome metrics. No dashboards defined in the repository for visualizing these metrics. |
| **Recommendation** | Define Grafana dashboards (as code) for the existing business metrics. Add custom metrics for remaining features (alert evaluation success rate, user login frequency, API endpoint usage patterns). Use Amazon Managed Grafana for visualization. |
| **Evidence** | `graylog2-server/src/main/resources/prometheus-exporter.yml` (200+ metric mappings including stream messages, journal utilization, pipeline execution, event processing, traffic throughput, data lake I/O). |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configuration exists in the repository. While Graylog is an alerting platform for log data (it has an events/alerting engine for log-based alerts), there are no operational alerts defined for Graylog's own health. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration for self-monitoring. |
| **Gap** | No alerting configured for Graylog's own operational health. No anomaly detection on error rates, latency, journal utilization, or cluster health. |
| **Recommendation** | Define Prometheus alerting rules (or CloudWatch alarms) for: journal utilization > 80%, search response time p99 > threshold, node health check failures, input buffer overflow, output failures. Configure anomaly detection on error rates using CloudWatch Anomaly Detection. Integrate with PagerDuty/OpsGenie for incident notification. |
| **Evidence** | No alerting rules in any configuration file. No `alertmanager.yml`, no CloudWatch alarm definitions, no PagerDuty configuration. The application has an alerting engine for user-defined log alerts but no self-monitoring alerts. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment automation exists in the repository. CI builds and tests but does not deploy. No blue/green, canary, or rolling deployment configuration. Releases are published as Maven artifacts to Sonatype Nexus. Actual deployment to production is entirely manual and external to this repository. |
| **Gap** | Direct-to-production deployment with no staged rollout. No deployment strategy of any kind is defined in the repository. |
| **Recommendation** | Implement canary deployments on EKS using ArgoCD Rollouts or Flagger. Define deployment manifests with progressive traffic shifting (10% → 50% → 100%) with automatic rollback on error rate increase. For the initial containerized deployment, start with rolling updates with health checks. |
| **Evidence** | No deploy stage in `.github/workflows/build.yml`, no CodeDeploy config, no ArgoCD manifests, no Helm charts with deployment strategy. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration testing exists: 92+ integration test files (`*IT.java`) using Testcontainers with real MongoDB, OpenSearch, S3 (Minio), GCS, and Azurite. The `full-backend-tests/` module contains 50 end-to-end test classes testing the complete REST API against a full Graylog backend. Tests run in CI via the GitHub Actions build pipeline (full-backend-tests job). |
| **Gap** | Integration tests for primary workflows exist and run in CI. Some gaps in coverage — not all features have dedicated integration tests. Contract tests between cluster nodes are absent. |
| **Recommendation** | Add contract tests for the inter-node API (RemoteInterface contracts). Expand full-backend-tests to cover deployment scenarios (rolling update behavior, leader election during scale events). Current coverage is strong — maintain and extend. |
| **Evidence** | `full-backend-tests/` (50 E2E test classes), `*IT.java` files (92+ integration tests), `.github/workflows/build.yml` (full-backend-tests job), Testcontainers 2.0.4 in `pom.xml`. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident playbooks, or automated incident response workflows exist in the repository. No Systems Manager Automation documents, no Lambda-based remediation, no self-healing patterns defined. Incident response is entirely ad hoc. |
| **Gap** | No runbooks — incident response is entirely ad hoc with no documentation or automation. |
| **Recommendation** | Create operational runbooks for common incidents: journal full, search cluster degraded, node unresponsive, input failures, high memory pressure. Define SSM Automation documents for automated remediation (restart unhealthy pods, scale up on journal pressure). Store runbooks as versioned Markdown in the repository. |
| **Evidence** | No runbook files (markdown, YAML, JSON) found. No `docs/runbooks/` directory. No SSM Automation documents. No incident response automation. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for observability assets, no per-service dashboards defined in the repository, no named owners on alarms (no alarms exist), no team-attributed SLO definitions. The Prometheus metric configuration exists but has no ownership attribution. |
| **Gap** | No observability ownership — monitoring assets (metrics, dashboards, alarms) have no defined owners or team attribution. |
| **Recommendation** | Define CODEOWNERS for observability configurations. Create per-component dashboards (ingest pipeline, search, alerting, cluster health) with named team owners. Attribute SLOs to specific teams when they are defined. |
| **Evidence** | No CODEOWNERS file referencing observability. No dashboard definitions. No alarm configurations with owner tags. `prometheus-exporter.yml` has no ownership metadata. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging patterns found. No IaC exists to tag resources. No `default_tags` in Terraform provider, no tag enforcement rules, no cost allocation tags. The application code has no AWS resource tagging logic (only a test for CloudTrail SNS parsing references AWS concepts). |
| **Gap** | No tags found on resources. No tagging standard, no cost allocation, no ownership attribution via tags. |
| **Recommendation** | When creating IaC, define a mandatory tagging schema: Environment, Service, Team, CostCenter, DataClassification. Use `default_tags` in Terraform provider block. Enforce via AWS Config `required-tags` rule and Tag Policies in AWS Organizations. |
| **Evidence** | No IaC files with tags. No tagging patterns in source code. No Tag Policies or AWS Config rules. |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | APP-Q1, INF-Q4, SEC-Q3, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q6 | Root Maven POM with dependency versions, plugins, and framework configuration |
| `misc/graylog.conf` | INF-Q2, INF-Q5, INF-Q6, SEC-Q2, SEC-Q5 | Main server configuration with database URIs, security settings, sample secrets |
| `.github/workflows/build.yml` | INF-Q11, SEC-Q7, OPS-Q5, OPS-Q6 | CI pipeline definition with 4 parallel jobs, no deploy stage |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Dependency vulnerability scanning configuration (8 ecosystems, daily) |
| `data-node/migration/docker-compose.yml` | INF-Q2, INF-Q9, SEC-Q2, DATA-Q3 | Migration docker-compose with self-managed MongoDB and OpenSearch |
| `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile` | INF-Q1, SEC-Q6 | Test Dockerfile with eclipse-temurin:21-jre-jammy base |
| `graylog2-server/src/main/java/org/graylog2/periodical/` | INF-Q3, APP-Q4 | 26+ scheduled background tasks (custom Periodical framework) |
| `graylog2-server/src/main/java/org/graylog2/events/ClusterEventBus.java` | INF-Q4, APP-Q3 | MongoDB-polled cross-node event system |
| `graylog2-server/src/main/java/org/graylog/security/authservice/` | SEC-Q3, SEC-Q4 | Auth service framework with LDAP/AD backends |
| `graylog2-server/src/main/resources/prometheus-exporter.yml` | OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4 | 200+ Prometheus metric mappings |
| `graylog2-server/src/main/java/org/graylog/tracing/` | OPS-Q1 | OpenTelemetry tracing support (TracerProvider, semantic attributes) |
| `graylog2-server/src/main/java/org/graylog2/cluster/` | APP-Q6, INF-Q9 | MongoDB-based node registry and leader election |
| `graylog2-server/src/main/java/org/graylog2/rest/resources/` | APP-Q5, INF-Q6 | REST API resources with flat /api/ paths |
| `full-backend-tests/` | OPS-Q6 | 50 end-to-end integration test classes |
| `graylog2-server/src/main/java/org/graylog2/migrations/` | DATA-Q4 | ~52 Java-based MongoDB migration classes |
| `api-specs/stream-output-filters.yml` | APP-Q5 | OpenAPI 3.1.0 specification |
| `graylog2-server/src/main/java/org/graylog/mcp/` | Quick Agent Wins | MCP server implementation with tools and resources |
| `config/spotbugs-exclude.xml` | SEC-Q7 | SpotBugs exclusion rules |
| `config/pmd-rules.xml` | SEC-Q7 | PMD static analysis rules |
| `data-node/src/main/resources/opensearch/config/opensearch-security/audit.yml` | SEC-Q1 | OpenSearch audit logging configuration |
| `graylog2-web-interface/package.json` | APP-Q1 | Frontend dependencies (TypeScript 5.9.3, React 18.3.1) |
