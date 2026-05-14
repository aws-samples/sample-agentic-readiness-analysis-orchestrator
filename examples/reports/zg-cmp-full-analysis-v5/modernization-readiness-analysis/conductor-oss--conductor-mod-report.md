# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | conductor |
| **Date** | 2025-07-15 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | monorepo |
| **Service Archetype** | orchestrator (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, workflow, orchestration |
| **Context** | Workflow orchestration engine originally from Netflix. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Overall Score** | 2.1 / 4.0 |

**Archetype Justification**: Conductor is a workflow orchestration engine that coordinates multi-step workflow executions across distributed task workers. It manages workflow state, fans out to task workers via a polling model, and coordinates sub-workflows — matching the `orchestrator` archetype. The server itself does not process tasks; it orchestrates them.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.6 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.0 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.0 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.3 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.6 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.1 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q3: API Authentication | 1 | No authentication middleware, no Spring Security dependency, REST endpoints are open | Any consumer can invoke workflow management APIs without authorization; critical for production deployment |
| 2 | SEC-Q5: Secrets Management | 1 | Plaintext database credentials in version-controlled config files (`conductor/conductor`) | Credentials exposed in source control; blocks secure production deployment |
| 3 | INF-Q10: IaC Coverage | 1 | No Terraform, CloudFormation, CDK, Helm, or Kustomize files; infrastructure is undefined beyond Docker Compose | Cannot reproducibly provision production infrastructure; manual setup required |
| 4 | INF-Q1: Managed Compute | 1 | Only Docker Compose for local dev; no ECS, EKS, Lambda, or Fargate IaC | No path to managed container orchestration without creating IaC from scratch |
| 5 | OPS-Q1: Distributed Tracing | 1 | No OpenTelemetry, X-Ray, or tracing instrumentation; no trace-ID propagation | Cannot trace requests across Conductor server, task workers, and dependent services |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 2 (≥ 2). Swagger/OpenAPI auto-generated via `springdoc-openapi-starter-webmvc-ui` at `/api-docs`. REST controllers expose structured JSON responses for workflow, task, metadata, and event APIs.
- **What it enables:** An AI agent that discovers and invokes Conductor's REST API endpoints as tools — start workflows, poll tasks, update task status, search workflows, and manage metadata definitions through natural language.
- **Additional steps:** The auto-generated OpenAPI spec is available at runtime but not committed as a static file. Generate and version a static `openapi.json` for offline agent tool discovery.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (≥ 2). Conductor has an exemplary DAO abstraction layer (ExecutionDAO, MetadataDAO, QueueDAO, IndexDAO, PollDataDAO) with clean interfaces and pluggable implementations.
- **What it enables:** A natural-language-to-query agent that translates questions like "show me all failed workflows in the last hour" into structured DAO queries or Elasticsearch/OpenSearch index queries.
- **Additional steps:** Expose a read-only query endpoint or use the existing `/api/workflow/search` and `/api/tasks/search` endpoints as the agent's query interface.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). GitHub Actions CI/CD pipeline exists with build, test-harness, and Docker multi-arch publish workflows.
- **What it enables:** An agent that triggers CI builds, checks build status, monitors test-harness results, and manages Docker image publishing via GitHub Actions API.
- **Additional steps:** Ensure GitHub Actions API tokens are available for agent invocation. Consider adding workflow dispatch triggers for on-demand agent-initiated builds.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists. The repository contains an extensive `docs/` directory with architecture guides, developer guides, quickstart, and API documentation. `README.md`, `ROADMAP.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `RELATED.md`, and `schemas/` (JSON schemas for Task, TaskDef, Workflow, WorkflowDef) provide rich content.
- **What it enables:** A RAG-powered knowledge agent that indexes Conductor documentation and answers developer questions about workflow authoring, API usage, deployment configuration, and troubleshooting.
- **Additional steps:** Index the `docs/` directory and schema files into a vector store (pgvector, which the AI module already supports). Leverage the existing Spring AI and document reader infrastructure in the `ai` module.
- **Effort:** Low — the AI module already includes Spring AI, Tika document readers, and pgvector integration.

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 4 (≥ 2). Conductor IS the workflow orchestration engine — it provides first-class workflow execution, state management, retry logic, and monitoring capabilities.
- **What it enables:** An agent that monitors running workflows, identifies stuck or failed executions, triggers retries or restarts, and provides natural-language workflow status updates.
- **Additional steps:** Use the existing REST API (`/api/workflow/{id}`, `/api/workflow/{id}/retry`, `/api/workflow/{id}/restart`) as the agent's action interface.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with clean boundaries); primary trigger not met |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (all compute on Docker Compose, no managed orchestration); Dockerfile and Docker Compose exist but no managed container orchestration IaC (no Kubernetes manifests, Helm charts, or ECS/EKS task definitions); contextual guard not triggered (compute is not Lambda/Fargate/ECS) |
| 3 | Move to Open Source | Not Triggered | — | — | No commercial database engines detected (PostgreSQL, MySQL, Redis, Elasticsearch are all open source) |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (all databases self-managed in Docker Compose); DATA-Q3 = 2 (version pinning gaps) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 for orchestrator archetype; no self-managed analytics infrastructure detected |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC); OPS-Q5 = 1 (no deployment strategy); OPS-Q6 = 3 (tests exist but deployment gaps) |
| 7 | Move to AI | Not Triggered | — | — | AI/agent frameworks already present (Spring AI 1.1.2, Bedrock, pgvector, Pinecone, MongoDB vector, MCP). No gap. |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Conductor runs as a self-built Docker image (`docker/server/Dockerfile`) using `debian:stable-slim` with `openjdk-21-jre-headless` and nginx. The deployment model is Docker Compose with single-container instances for the server, Redis, Elasticsearch, and optional PostgreSQL/MySQL. No managed container orchestration IaC exists.

**Trigger Note:** The TD's supporting trigger condition states "no container definitions found in the discovery scan." Container definitions (Dockerfile, Docker Compose files) DO exist in this repository. However, no *managed* container orchestration IaC was found — no Kubernetes manifests, Helm charts, ECS task definitions, or EKS cluster definitions. The existing Dockerfiles serve local development only and do not constitute production-grade managed container orchestration. The pathway is triggered because INF-Q1 = 1 (primary condition met), the contextual guard does not prevent it (compute is Docker Compose, not Lambda/Fargate/ECS), and the practical intent of the pathway — migrating to fully managed container orchestration — applies to this repository.

**Container Readiness Indicators:**
- ✅ Dockerfile exists and is well-structured (multi-stage build with builder, UI builder, and final stages)
- ✅ Multi-arch builds (linux/arm64, linux/amd64) are already configured in CI via `docker/build-push-action`
- ✅ Health check configured (`HEALTHCHECK` in Dockerfile and Docker Compose)
- ✅ Configuration externalized via properties files and environment variables (`CONFIG_PROP`, `JAVA_OPTS`)
- ✅ Docker images published to Docker Hub (`conductoross/conductor`, `orkesio/orkes-conductor-community`)
- ⚠️ No Kubernetes manifests, Helm charts, or ECS task definitions exist

**Recommended Container Orchestration Platform:** Amazon EKS (preferred per analysis context). EKS provides managed Kubernetes with Graviton node support, which aligns with the existing multi-arch builds.

**Migration Approach:**
1. Create EKS cluster IaC (Terraform or CDK) with managed node groups (Graviton instances for cost optimization)
2. Create Kubernetes Deployment manifests for the Conductor server using the existing Docker image
3. Add Kubernetes Service and Ingress resources with ALB Ingress Controller
4. Configure ConfigMaps for externalized properties and Secrets for database credentials
5. Add HorizontalPodAutoscaler for elastic scaling
6. Set up ECR for private image registry (currently Docker Hub public)

**Representative AWS Services:** EKS, ECR, ALB (via AWS Load Balancer Controller), Fargate (optional for burst workloads)

**AWS Prescriptive Guidance:** [EKS Workshop](https://www.eksworkshop.com/) · [Containers Migration](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-containers/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** All databases are self-managed in Docker Compose:
- **Redis 6.2.3** — used for persistence, queues, and locking (`conductor-redis` in `docker-compose.yaml`)
- **Elasticsearch 7.17.11** — used for workflow/task indexing (`conductor-elasticsearch` in `docker-compose.yaml`)
- **PostgreSQL 16** — alternative persistence backend (`conductor-postgres` in `docker-compose-postgres.yaml`)
- **MySQL (latest, unpinned)** — alternative persistence backend (`conductor-mysql` in `docker-compose-mysql.yaml`)
- **Cassandra** — supported via `cassandra-persistence` module (no Docker Compose definition)

**Engine Versions and EOL Status:**
- Redis 6.2.3: Approaching EOL (Redis 6.2 community EOL)
- Elasticsearch 7.17.11: EOL announced; Elastic 7.x end-of-life reached
- PostgreSQL 16: Current (supported until November 2028)
- MySQL latest: Version not pinned — risk of breaking changes on pull

**Data Access Patterns:** Conductor's DAO abstraction layer (ExecutionDAO, MetadataDAO, QueueDAO, IndexDAO) provides clean interfaces that decouple application logic from the database implementation. This significantly reduces managed database migration effort — the application code does not need to change; only configuration and connection settings need updating.

**Recommended Managed Database Targets:**
- Redis → **Amazon ElastiCache for Redis** or **Amazon MemoryDB for Redis** (for durable persistence use case)
- Elasticsearch → **Amazon OpenSearch Service** (Conductor already has OpenSearch persistence modules: `os-persistence`, `os-persistence-v2`)
- PostgreSQL → **Amazon Aurora PostgreSQL** (preferred per analysis context)
- MySQL → **Amazon Aurora MySQL** (preferred per analysis context)

**Migration Tools:** AWS Database Migration Service (DMS) for PostgreSQL/MySQL data migration. For Redis, use ElastiCache's built-in migration capabilities or the Redis DUMP/RESTORE approach.

**Representative AWS Services:** Aurora PostgreSQL, Aurora MySQL, ElastiCache for Redis, MemoryDB, OpenSearch Service, DMS

**AWS Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):** No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. All infrastructure is defined only through Docker Compose files for local development. Production deployment requires manual infrastructure provisioning.

**Current CI/CD State (INF-Q11 = 3):** GitHub Actions CI/CD pipeline exists with:
- `ci.yml` — Build with Gradle, test-harness tests (separate job), Cypress UI tests, JaCoCo coverage
- `publish.yml` — Maven Central publish + Docker multi-arch build and push on release
- `publish_build.yaml` — Server-lite JAR and Docker image publish
- `dependabot.yml` — Weekly Gradle and GitHub Actions dependency updates

**Deployment Strategy Gaps (OPS-Q5 = 1):** No blue/green, canary, or rolling deployment strategy. Docker images are pushed directly to Docker Hub on release with no staged rollout or traffic shifting.

**Testing Gaps (OPS-Q6 = 3):** Strong test foundation — test-harness module with Spock/JUnit integration tests using TestContainers; e2e module with tests against multiple backends (Postgres, MySQL, Redis+ES, Redis+OS). Tests run in CI. Gap: e2e tests require manual invocation (`RUN_E2E=true`) and are not part of the standard CI pipeline.

**Recommended DevOps Toolchain:**
1. **IaC Foundation:** Create Terraform modules (or CDK stacks) for VPC, EKS cluster, Aurora, ElastiCache, OpenSearch Service, and API Gateway. Use Terraform remote state in S3.
2. **CI/CD Enhancement:** Add deployment stages to GitHub Actions or migrate to AWS CodePipeline:
   - Add `terraform plan` on PR, `terraform apply` on merge to main
   - Add EKS deployment stage with kubectl/Helm after Docker push
   - Enable e2e tests in CI pipeline as a required quality gate
3. **Deployment Strategy:** Implement EKS rolling deployments with readiness probes, then graduate to canary with Argo Rollouts or AWS App Mesh traffic shifting.
4. **Security Pipeline:** Add SAST (SonarCloud is partially configured — SONAR_TOKEN exists) and container image scanning (ECR native scanning or Snyk).

**Representative AWS Services:** CodePipeline, CodeBuild, CodeDeploy, CloudFormation/CDK, ECR (image scanning), X-Ray

**AWS Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is defined via Docker Compose (`docker/docker-compose.yaml` and variants) running self-managed containers on the Docker daemon. The `docker/server/Dockerfile` builds a multi-stage image with `debian:stable-slim` base. No Terraform, CloudFormation, or CDK resources define ECS, EKS, Lambda, Fargate, or EC2 instances. The CI pipeline (`publish.yml`) publishes multi-arch Docker images to Docker Hub but does not deploy to any managed compute platform. |
| **Gap** | No managed compute infrastructure exists. Production deployment requires manual provisioning of compute resources. |
| **Recommendation** | Create EKS cluster IaC (Terraform or CDK) leveraging the existing multi-arch Docker images. Use managed node groups with Graviton instances. Define Kubernetes Deployment, Service, and HPA resources for the Conductor server. |
| **Evidence** | `docker/server/Dockerfile`, `docker/docker-compose.yaml`, `.github/workflows/publish.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All databases are self-managed in Docker Compose: Redis 6.2.3-alpine (`docker/docker-compose.yaml`), Elasticsearch 7.17.11 (`docker/docker-compose.yaml`), PostgreSQL 16 (`docker/docker-compose-postgres.yaml`), MySQL latest (`docker/docker-compose-mysql.yaml`). Cassandra is supported via `cassandra-persistence` module. No `aws_rds_*`, `aws_dynamodb_*`, `aws_elasticache_*`, or other managed database resources exist in IaC. |
| **Gap** | All databases are self-managed with no automated failover, patching, or scaling. Docker Compose is development-only — not suitable for production. |
| **Recommendation** | Migrate to managed database services: Redis → ElastiCache for Redis or MemoryDB; Elasticsearch → OpenSearch Service (OS modules already exist); PostgreSQL → Aurora PostgreSQL; MySQL → Aurora MySQL. Conductor's DAO abstraction makes this a configuration-only change. |
| **Evidence** | `docker/docker-compose.yaml`, `docker/docker-compose-postgres.yaml`, `docker/docker-compose-mysql.yaml` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Conductor IS a dedicated workflow orchestration service. As an `orchestrator` archetype, it provides first-class workflow orchestration with JSON-based workflow definitions, state management, retry logic, error handling, sub-workflow support, and task scheduling. The `core` module implements the workflow execution engine with `WorkflowExecutor`, `DeciderService`, and task scheduling. Conductor supports WAIT tasks, SUB_WORKFLOW tasks, and the `executeWorkflow` synchronous API with timeout handling (visible in `WorkflowResource.java`). |
| **Gap** | N/A — Conductor meets the highest bar for workflow orchestration for the `orchestrator` archetype. |
| **Recommendation** | No action needed. Consider documenting the orchestration patterns for teams deploying Conductor on AWS (Step Functions integration patterns for hybrid workflows). |
| **Evidence** | `core/src/main/java/com/netflix/conductor/core/`, `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `schemas/WorkflowDef.json` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Conductor has extensive messaging infrastructure support. The `awssqs-event-queue` module uses AWS SDK v2 (`software.amazon.awssdk:sqs:2.31.68`) for managed SQS messaging. The `kafka` and `kafka-event-queue` modules support Apache Kafka. The `amqp` module supports RabbitMQ/AMQP. The `nats` and `nats-streaming` modules support NATS. These are pluggable event queue backends configured via properties (`conductor.queue.type`). For the `orchestrator` archetype, the primary workflow coordination is handled internally (task polling model), while event-driven integrations use these queue backends. Managed messaging (SQS) is available for key flows. |
| **Gap** | Kafka and AMQP/RabbitMQ backends are self-managed options. The default Docker Compose configurations do not use managed messaging. Kafka client version is 2.6.0 (old). |
| **Recommendation** | For AWS deployment, prefer SQS (`awssqs-event-queue`) or Amazon EventBridge for event-driven integrations. If Kafka is required, use Amazon MSK Serverless instead of self-managed Kafka. Avoid self-managed Kafka per analysis preferences. Update Kafka client version if MSK is adopted. |
| **Evidence** | `awssqs-event-queue/build.gradle`, `kafka/build.gradle`, `kafka-event-queue/build.gradle`, `amqp/`, `nats/`, `docker/server/config/config-redis.properties` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation configuration exists anywhere in the repository. Docker Compose uses a flat `internal` network with no isolation between services. The conductor-server exposes ports 8000 (HTTP) and 8127 (debug) directly. No `aws_vpc`, `aws_subnet`, or `aws_security_group` resources found. |
| **Gap** | No network security configuration exists. Services would be deployed without network isolation in their current form. |
| **Recommendation** | Create VPC IaC with private subnets for Conductor server, database tier, and a public subnet only for the load balancer. Define security groups with least-privilege rules. Use VPC endpoints for AWS service access (SQS, S3, ECR). |
| **Evidence** | `docker/docker-compose.yaml` (flat `internal` network), no `.tf` or CloudFormation files found |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Conductor server exposes REST API directly via Spring Boot embedded Tomcat on port 8080 (mapped to 8000 in Docker Compose). Nginx is included in the Docker image as a reverse proxy for the UI only. No API Gateway, ALB, CloudFront, or AppSync configuration exists. The REST controllers (`WorkflowResource`, `TaskResource`, `MetadataResource`) are directly accessible with no throttling, request validation, or authentication at the gateway level. |
| **Gap** | No managed API entry point with throttling, auth, or request validation. Direct service exposure. |
| **Recommendation** | Deploy Amazon API Gateway (preferred per analysis context) in front of the Conductor REST API. Configure throttling, request validation, and authentication (Cognito authorizer or Lambda authorizer). Alternatively, use an ALB with WAF rules for the EKS deployment. |
| **Evidence** | `docker/server/Dockerfile` (nginx for UI only), `rest/src/main/java/com/netflix/conductor/rest/config/RequestMappingConstants.java`, `docker/docker-compose.yaml` (port mapping 8000:8080) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. Docker Compose runs single instances of each service. No `aws_autoscaling_*`, `aws_appautoscaling_*`, Kubernetes HPA, or ECS service auto-scaling found. No scaling policies, min/max capacity settings, or Lambda concurrency limits defined. |
| **Gap** | All capacity is statically provisioned. Cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | When deploying to EKS, configure HorizontalPodAutoscaler for the Conductor server based on CPU/memory and custom metrics (workflow queue depth, task poll rate). Configure auto-scaling on Aurora read replicas and ElastiCache shards. |
| **Evidence** | `docker/docker-compose.yaml` (single instances), no scaling configuration found in repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. Docker Compose volumes (`esdata-conductor`, `pgdata-conductor`, `conductor_mysql`) use local storage with no backup strategy. No `aws_backup_plan`, `backup_retention_period`, `point_in_time_recovery`, or S3 versioning configuration found. No documented restore procedures. |
| **Gap** | No automated backups for any data store. Data loss risk is total in a failure scenario. |
| **Recommendation** | When migrating to managed databases: enable automated backups with defined retention on Aurora (default 7 days, recommend 30 days for production), enable PITR on DynamoDB if adopted, configure ElastiCache backup with daily snapshots. Document and test restore procedures. |
| **Evidence** | `docker/docker-compose.yaml` (local volumes only), `docker/docker-compose-postgres.yaml` (no backup config) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. Docker Compose runs all services in a single host. No `multi_az`, `availability_zones`, or cross-AZ configuration found. Elasticsearch runs with `discovery.type=single-node`. No load balancer cross-zone configuration. |
| **Gap** | Single point of failure at every layer. An infrastructure failure takes down the entire Conductor installation. |
| **Recommendation** | When deploying to EKS, distribute pods across multiple AZs. Configure Aurora Multi-AZ with automated failover. Deploy ElastiCache with Multi-AZ replication. Use ALB with cross-zone load balancing enabled. |
| **Evidence** | `docker/docker-compose.yaml` (`discovery.type=single-node`), no multi-AZ configuration found |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files exist in the repository. Searched for: `.tf` files (Terraform), CloudFormation templates (`*.cfn.yaml`, `*.cfn.json`), CDK configurations (`cdk.json`), Helm charts (`Chart.yaml`, `values.yaml`), Kustomize (`kustomization.yaml`). None found. The only infrastructure definition is Docker Compose files, which define development environment topology but not production infrastructure. |
| **Gap** | 0% IaC coverage. All production infrastructure must be created manually (ClickOps). |
| **Recommendation** | Create Terraform modules (or CDK stacks) covering: VPC/networking, EKS cluster, Aurora PostgreSQL, ElastiCache, OpenSearch Service, API Gateway, IAM roles, CloudWatch alarms, and backup plans. This is the foundational step that enables all other modernization pathways. |
| **Evidence** | No `.tf`, `*.cfn.yaml`, `*.cfn.json`, `cdk.json`, `Chart.yaml`, `values.yaml`, or `kustomization.yaml` files found in repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI/CD pipeline exists with multiple workflows: `ci.yml` (build + test-harness + UI tests with Cypress), `publish.yml` (Maven Central publish + Docker multi-arch build/push on release), `publish_build.yaml` (server-lite JAR + Docker publish). Dependabot configured for weekly Gradle and GitHub Actions updates. JaCoCo coverage reports generated. SonarCloud integration configured (`SONAR_TOKEN` secret referenced). Build artifacts uploaded. |
| **Gap** | CI/CD covers application code build, test, and Docker publish, but no infrastructure deployment automation. No `terraform plan/apply` stages. No EKS deployment steps. The e2e test suite requires manual invocation (`RUN_E2E=true`). No automated rollback mechanism. |
| **Recommendation** | Add infrastructure deployment stages (Terraform plan/apply or CDK deploy). Add EKS deployment stage with kubectl/Helm after Docker push. Enable e2e tests as a required CI gate. Add automated rollback on deployment failure. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/publish.yml`, `.github/workflows/publish_build.yaml`, `.github/dependabot.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 21 (defined in `build.gradle`: `languageVersion = JavaLanguageVersion.of(21)`) with Spring Boot 3.3.11 (BOM version), Spring AI 1.1.2, AWS SDK v2 2.31.68, Jackson 2.17.0, Lombok 1.18.42. This is a modern, current-version Java stack with first-class AWS SDK coverage. The framework and SDK versions are fully current — Spring Boot 3.3.x is the latest stable line, AWS SDK v2 is the current major version, and Java 21 is LTS. UI is React (Node.js LTS). Groovy 4.0.21 used for Spock tests. |
| **Gap** | N/A — Language, framework, and SDK are all at current versions. |
| **Recommendation** | No action needed. Consider planning for Spring Boot 3.4.x and Java 25 (next LTS) when available. |
| **Evidence** | `build.gradle` (Java 21, Spring Boot 3.3.11), `dependencies.gradle` (AWS SDK 2.31.68, Spring AI 1.1.2, Micrometer 1.14.6) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Conductor is a modular monolith with well-defined module boundaries. The `settings.gradle` defines 40+ Gradle submodules with clear separation: `core` (domain logic), `common` (shared models), `rest` (API controllers), `grpc-server`/`grpc-client` (gRPC API), pluggable persistence modules (`redis-persistence`, `postgres-persistence`, `mysql-persistence`, `cassandra-persistence`, `sqlite-persistence`, `es7-persistence`, `es8-persistence`, `os-persistence`), pluggable event queue modules (`awssqs-event-queue`, `kafka`, `kafka-event-queue`, `amqp`, `nats`), `metrics`, `ai`, and `scheduler`. The `server` module assembles these into a single deployable Spring Boot JAR. Module boundaries are enforced via DAO interfaces (`ExecutionDAO`, `MetadataDAO`, `QueueDAO`, `IndexDAO`) — each persistence module implements these interfaces independently. No circular cross-module dependencies observed. |
| **Gap** | Single deployable unit — all modules compile into one `conductor-server-boot.jar`. Cannot independently scale or deploy individual modules (e.g., scale the task polling separately from the REST API). |
| **Recommendation** | The modular monolith design is appropriate for Conductor's architecture. The clean DAO interfaces and pluggable modules mean the system is decomposition-ready if needed. Consider extracting the scheduler module or the AI module as separate services if they need independent scaling. |
| **Evidence** | `settings.gradle`, `server/build.gradle`, `core/src/main/java/com/netflix/conductor/dao/` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | For the `orchestrator` archetype, Conductor has a healthy mix of async and sync communication. **Sync:** REST API (`/api/workflow`, `/api/tasks`, `/api/metadata`) via Spring MVC and gRPC API for service-to-service communication. The `executeWorkflow` endpoint provides synchronous workflow execution with reactive polling (Reactor Mono/Flux). **Async:** Task workers communicate asynchronously via a polling model (task queue). Event-driven integrations use SQS, Kafka, AMQP, and NATS backends. The `workflow-event-listener` and `task-status-listener` modules provide async notification patterns. For the orchestrator archetype, async dominates for fan-out (task distribution) while sync is reserved for reads and API calls. |
| **Gap** | Some fan-out still uses synchronous patterns (the `executeWorkflow` endpoint polls synchronously for completion). Primary workflows use async task polling, but some auxiliary flows could benefit from event-driven patterns. |
| **Recommendation** | Consider adopting Amazon EventBridge (preferred per analysis context) for workflow state change notifications to external systems, replacing the polling-based synchronous workflow execution pattern for non-latency-sensitive use cases. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (executeWorkflow with Mono/Flux), `awssqs-event-queue/build.gradle`, `kafka-event-queue/build.gradle` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Conductor is specifically designed to handle long-running processes. As an `orchestrator` archetype, all long-running coordination uses the async task polling model — workers poll for tasks, execute them asynchronously, and report results back. The `executeWorkflow` API provides timeout-bounded synchronous execution with `waitForSeconds` parameter and `Mono.timeout()` for graceful timeout handling. WAIT tasks, SUB_WORKFLOW tasks, and scheduling (via the `scheduler` module) all use async patterns with status tracking. The `WorkflowResource.java` `findBlockingTasks` method recursively checks workflow hierarchies for completion status. |
| **Gap** | N/A — Long-running process handling is the core value proposition of Conductor. |
| **Recommendation** | No action needed. The async task polling model with timeout-bounded synchronous execution is the correct design for a workflow orchestrator. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (executeWorkflow, findBlockingTasks), `scheduler/`, `core/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API versioning is applied ad hoc. The base API path is `/api/` (defined in `RequestMappingConstants.java`) with no version prefix (e.g., no `/api/v1/`). Some endpoints have versioned alternatives: `/search` and `/search-v2` (in both `WorkflowResource.java` and `TaskResource.java`), `/tasks/update-v2`. The `@Deprecated` annotation is used on the old `/tasks/queue/sizes` endpoint. However, fewer than half of endpoints use versioning, and the versioning scheme is inconsistent (suffix `-v2` vs no version). No `Accept-Version` headers or changelog files found. |
| **Gap** | No consistent versioning strategy. Breaking changes to the API (e.g., `search-v2` replacing `search`) are handled with ad hoc endpoint suffixes rather than a systematic approach. |
| **Recommendation** | Adopt a consistent URL path versioning strategy (e.g., `/api/v1/workflow`, `/api/v2/workflow`). Use API Gateway stage variables to manage version routing. Maintain backward compatibility on the current `/api/` prefix while introducing versioned paths for new features. |
| **Evidence** | `rest/src/main/java/com/netflix/conductor/rest/config/RequestMappingConstants.java`, `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (search-v2), `rest/src/main/java/com/netflix/conductor/rest/controllers/TaskResource.java` (search-v2, update-v2) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints are configured via environment variables and properties files. Docker Compose uses `links` for service name resolution (`conductor-elasticsearch:es`, `conductor-redis:rs`, `conductor-postgres:postgresdb`). Configuration properties reference service hostnames via environment variables or hardcoded Docker Compose service names (e.g., `conductor.redis.hosts=rs:6379:us-east-1c`, `spring.datasource.url=jdbc:postgresql://postgresdb:5432/postgres`, `conductor.elasticsearch.url=http://es:9200`). No AWS Service Discovery, Consul, Istio, or Kubernetes DNS-based service discovery. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. Configuration is tightly coupled to Docker Compose service names. Changing endpoints requires configuration file changes. |
| **Recommendation** | When deploying to EKS, leverage Kubernetes DNS-based service discovery for internal service communication. For AWS-native discovery, consider AWS Cloud Map for registering Conductor and its backing services. Use Kubernetes ConfigMaps and Secrets for endpoint configuration rather than hardcoded hostnames. |
| **Evidence** | `docker/server/config/config-redis.properties`, `docker/server/config/config-postgres.properties`, `docker/docker-compose.yaml` (links) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `awss3-storage` module provides S3 integration using AWS SDK v2 (`software.amazon.awssdk:s3:2.31.68`, `software.amazon.awssdk:sts:2.31.68`) for external payload storage. Conductor supports storing large workflow/task payloads in S3 via the `ExternalPayloadStorage` interface. The `ai` module includes extensive document parsing capabilities: `spring-ai-tika-document-reader`, `spring-ai-pdf-document-reader`, `spring-ai-markdown-document-reader`, `spring-ai-jsoup-document-reader` (HTML), and PDF generation via `flexmark-all`. The `postgres-external-storage` module provides an alternative PostgreSQL-based external storage. |
| **Gap** | S3 is used for payload storage but no automated parsing pipeline (Textract integration, ETL) exists for unstructured data analysis. The AI module's document readers are for LLM input, not for a structured data pipeline. |
| **Recommendation** | For workflow payloads in S3, consider adding S3 event notifications with Lambda for automated payload processing. If document analysis is a use case, integrate Amazon Textract or Bedrock for parsing workflows stored in S3. |
| **Evidence** | `awss3-storage/build.gradle`, `ai/build.gradle` (Tika, PDF readers), `postgres-external-storage/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Conductor has an exemplary unified data access layer. The `core/src/main/java/com/netflix/conductor/dao/` directory defines 8 DAO interfaces: `ExecutionDAO`, `MetadataDAO`, `QueueDAO`, `IndexDAO`, `PollDataDAO`, `ConcurrentExecutionLimitDAO`, `EventHandlerDAO`, `RateLimitingDAO`. Each persistence module (`redis-persistence`, `postgres-persistence`, `mysql-persistence`, `cassandra-persistence`, `sqlite-persistence`, `es7-persistence`, `es8-persistence`, `os-persistence`, `os-persistence-v2`) implements these interfaces independently. The `server/build.gradle` selects the persistence backend at build time via the `indexingBackend` property. No direct database access outside the DAO layer. This is a textbook Ports and Adapters (Hexagonal Architecture) pattern. |
| **Gap** | N/A — The DAO abstraction is comprehensive and consistently applied. |
| **Recommendation** | No action needed. The DAO pattern significantly eases migration to managed databases — swapping from self-managed Redis to ElastiCache requires only configuration changes, not code changes. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/dao/` (8 DAO interfaces), `postgres-persistence/build.gradle`, `redis-persistence/`, `mysql-persistence/`, `es7-persistence/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some database versions are explicitly pinned in Docker Compose, others are not: **Redis 6.2.3** — pinned (`redis:6.2.3-alpine` in `docker-compose.yaml`), approaching community EOL. **Elasticsearch 7.17.11** — pinned (`docker.elastic.co/elasticsearch/elasticsearch:7.17.11`), Elastic 7.x has reached end-of-life. **PostgreSQL 16** — pinned (`postgres:16`), current and supported. **MySQL** — NOT pinned (`mysql:latest` in `docker-compose-mysql.yaml`), risk of breaking changes. Flyway migration versioning is well-maintained with sequential version numbers (V1 through V13.1 for Postgres, V1 through V8 for MySQL). No documented version-update procedure. |
| **Gap** | Elasticsearch 7.17.11 is at EOL. MySQL image is not version-pinned. Redis 6.2.3 is aging. No documented version-update procedure for engine upgrades. |
| **Recommendation** | Pin MySQL to a specific version. Migrate from Elasticsearch 7 to OpenSearch Service (modules already exist: `os-persistence`, `os-persistence-v2`). Upgrade Redis to 7.x when moving to ElastiCache. Document engine version update procedures with rollback plans. |
| **Evidence** | `docker/docker-compose.yaml` (Redis 6.2.3, ES 7.17.11), `docker/docker-compose-postgres.yaml` (PostgreSQL 16), `docker/docker-compose-mysql.yaml` (mysql:latest) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Minimal stored procedure usage for performance-critical operations only. In PostgreSQL: `queue_notify()` function and `queue_notify_trigger()` for queue change notifications (V10.1 migration), `poll_data_update_check()` trigger for data integrity (V10 migration). In MySQL: `DropIndexIfExists` and `FixPkIfNeeded` procedures for schema migration safety (V8 migration). In `postgres-external-storage`: `keep_row_number_steady()` function for row count management. All business logic is in the application layer (Java). The stored procedures are purely operational/database-level — no business logic in stored procedures. All SQL is standard (no T-SQL, PL/SQL proprietary constructs). |
| **Gap** | A few PostgreSQL-specific functions and triggers exist. These would need adaptation if migrating away from PostgreSQL (though migrating TO Aurora PostgreSQL preserves compatibility). |
| **Recommendation** | No immediate action needed — the stored procedures are minimal and operational. When using Aurora PostgreSQL, these functions are fully compatible. If migrating to DynamoDB for any use case, the queue notification triggers would need replacement with DynamoDB Streams. |
| **Evidence** | `postgres-persistence/src/main/resources/db/migration_postgres/V10__poll_data_check.sql`, `postgres-persistence/src/main/resources/db/migration_postgres_notify/V10.1__notify.sql`, `mysql-persistence/src/main/resources/db/migration/V8__update_pk.sql` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration exists in the repository (no IaC). Application-level logging uses Log4j2 (`server/src/main/resources/log4j2.xml` is referenced; Log4j2 dependencies are declared in `build.gradle`). The `docker/server/config/log4j-file-appender.properties` and `log4j.properties` files configure local file logging. No immutable log storage (S3 Object Lock), no CloudWatch log group configuration, no audit-specific logging for API operations. The `Monitors.java` class records operational metrics but not audit events. |
| **Gap** | No audit logging infrastructure. No CloudTrail, no immutable log storage, no audit trail for workflow management operations (who created/deleted/modified workflow definitions). |
| **Recommendation** | Enable CloudTrail in the IaC. Configure CloudWatch Logs for Conductor application logs with defined retention. Implement application-level audit logging for workflow/task definition CRUD operations. Store audit logs in S3 with Object Lock for immutability. |
| **Evidence** | No `aws_cloudtrail` resources found, `docker/server/config/log4j.properties`, `build.gradle` (Log4j2 dependencies) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration exists. Docker Compose volumes use local storage with no encryption. No KMS key resources (`aws_kms_key`), no `kms_key_id` on any data store, no encryption configuration on S3 buckets, databases, or cache instances. The `awss3-storage` module does not configure server-side encryption when writing to S3. Elasticsearch `xpack.security.enabled=false` is explicitly set in Docker Compose. |
| **Gap** | No encryption at rest on any data surface. Workflow data, task payloads, and metadata are stored unencrypted. |
| **Recommendation** | When deploying to AWS managed services: enable KMS encryption on Aurora (default AWS-managed key minimum), ElastiCache (at-rest encryption), OpenSearch Service (encryption at rest), and S3 buckets (SSE-KMS). Configure the `awss3-storage` module to use S3 server-side encryption. |
| **Evidence** | `docker/docker-compose.yaml` (`xpack.security.enabled=false`), `awss3-storage/build.gradle` (no encryption config), no KMS resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication exists. Searched for `spring-boot-starter-security`, `spring-security`, `oauth`, `jwt`, `cognito` in all `build.gradle` files — none found. No authentication middleware, interceptors, or filter chains in the REST controllers. No `@PreAuthorize`, `@Secured`, or security annotations on any controller method. All REST API endpoints (`/api/workflow`, `/api/tasks`, `/api/metadata`, `/api/admin`, `/api/event`) are completely open. The `WorkflowResource`, `TaskResource`, and `MetadataResource` controllers have no auth checks. |
| **Gap** | All API endpoints are open — any network-reachable client can create/delete workflows, poll/update tasks, and modify metadata definitions without any authentication or authorization. This is the most critical security gap. |
| **Recommendation** | Add Spring Security with OAuth2/JWT bearer token authentication. Use Amazon Cognito (or API Gateway Cognito authorizer) for identity management. At minimum, add API Gateway with an authorizer in front of the Conductor REST API. Implement role-based access control: admin (workflow definition CRUD), operator (workflow execution), worker (task poll/update). |
| **Evidence** | `rest/build.gradle` (no security dependency), `server/build.gradle` (no security dependency), `rest/src/main/java/com/netflix/conductor/rest/controllers/` (no auth annotations) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration exists. No Cognito, Okta, Ping, OIDC, SAML, or SSO configuration found. The application has no authentication system at all (see SEC-Q3), so there is nothing to federate with an IdP. No `aws_cognito_*` resources, no OIDC/SAML configuration files. |
| **Gap** | No identity integration. Users of the Conductor API and UI are completely anonymous. |
| **Recommendation** | Integrate with Amazon Cognito for user identity management. Configure Cognito User Pool with OIDC/SAML federation for enterprise SSO. Use Cognito tokens for API Gateway authorization. For the UI, add Cognito Hosted UI or Amplify Auth for user login. |
| **Evidence** | No security dependencies in `build.gradle` files, no OIDC/SAML config, no Cognito resources |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Plaintext credentials are present in version-controlled configuration files. `docker/server/config/config-postgres.properties` contains: `spring.datasource.username=conductor`, `spring.datasource.password=conductor`. `docker/server/config/config-mysql.properties` contains: `spring.datasource.username=conductor`, `spring.datasource.password=conductor`. `docker/docker-compose-mysql.yaml` contains: `MYSQL_ROOT_PASSWORD: 12345`, `MYSQL_PASSWORD: conductor`. `docker/docker-compose-postgres.yaml` contains: `POSTGRES_PASSWORD=conductor`. The AI provider API keys in `application.properties` use environment variable references (`${OPENAI_API_KEY:}`, `${ANTHROPIC_API_KEY:}`, `${AWS_ACCESS_KEY_ID:}`) with empty defaults — this is better practice but the database credentials are still plaintext. No `aws_secretsmanager_*` resources, no Vault client imports. |
| **Gap** | Plaintext database credentials committed to source control. Even though these are development defaults, the pattern encourages plaintext credentials in production configurations. |
| **Recommendation** | Remove all plaintext credentials from version-controlled files. Use AWS Secrets Manager for database credentials with rotation enabled. Reference secrets via environment variables populated from Kubernetes Secrets (sourced from Secrets Manager via External Secrets Operator). The AI provider key pattern (`${ENV_VAR:}`) is correct and should be extended to database credentials. |
| **Evidence** | `docker/server/config/config-postgres.properties` (plaintext password), `docker/server/config/config-mysql.properties` (plaintext password), `docker/docker-compose-mysql.yaml` (MYSQL_ROOT_PASSWORD: 12345), `server/src/main/resources/application.properties` (AI keys via env vars) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Dockerfile uses `azul/zulu-openjdk-debian:21` as the builder base and `debian:stable-slim` as the final runtime base with `openjdk-21-jre-headless` installed via apt. Zulu JDK 21 is a well-maintained distribution. The `build.gradle` demonstrates active CVE patching: lz4-java forced to 1.8.1 for CVE-2025-12183, tika-core constrained to 3.2.2 for CVE-2025-66516, commons-beanutils to 1.11.0 for CVE-2025-48734, mssql-jdbc to 12.8.2 for CVE-2025-59250. Dependabot provides weekly dependency update PRs. However, no SSM Patch Manager, AWS Inspector, Snyk container scanning, or hardened base images (CIS, Bottlerocket) are used. |
| **Gap** | Active dependency patching but no container image vulnerability scanning, no hardened base image, no runtime vulnerability scanning. The `debian:stable-slim` base image is not CIS-hardened. |
| **Recommendation** | Add ECR image scanning (native or Snyk) to the CI pipeline after Docker push. Consider switching to `amazoncorretto:21-al2023-headless` or Bottlerocket for a more hardened runtime. Add Trivy or Grype container scanning as a CI gate. |
| **Evidence** | `docker/server/Dockerfile` (debian:stable-slim, zulu-openjdk-debian:21), `build.gradle` (CVE constraints), `.github/dependabot.yml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependabot is configured for weekly Gradle and GitHub Actions dependency updates with 3 named reviewers (`v1r3n`, `boney9`, `c4lm`). SonarCloud integration is partially configured — `SONAR_TOKEN` secret is referenced in `ci.yml` and SonarCloud packages are cached, but no explicit `sonarqube` or `sonar-scanner` step is visible in the workflow (it may be triggered via the `--scan` Gradle flag). JaCoCo code coverage is generated. No SAST tool (Semgrep, CodeGuru Reviewer), no DAST tool, no container image scanning step in CI. The `build.gradle` demonstrates proactive CVE management with forced dependency versions. |
| **Gap** | No SAST tool explicitly configured in CI. No container image scanning. SonarCloud integration is incomplete (no explicit analysis step). Dependabot provides dependency scanning but no blocking gate on critical findings. |
| **Recommendation** | Add explicit SonarCloud analysis step to `ci.yml` or integrate Semgrep for SAST. Add Docker image scanning (Trivy, Snyk, or ECR native) as a CI step after image build. Configure Dependabot security alerts with auto-merge for non-breaking patches. |
| **Evidence** | `.github/dependabot.yml`, `.github/workflows/ci.yml` (SONAR_TOKEN, --scan flag), `build.gradle` (CVE constraints) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. Searched for OpenTelemetry SDK, X-Ray instrumentation, `traceparent` header propagation, and tracing interceptors — none found in source code or dependencies. The `metrics` module supports OTLP (OpenTelemetry Protocol) for metrics export (`micrometer-registry-otlp`), but this is metrics-only, not tracing. No `spring-boot-starter-actuator` tracing auto-configuration or `micrometer-tracing` dependency. No trace-ID propagation between Conductor server and task workers. |
| **Gap** | No distributed tracing. Cannot trace a workflow execution request across the Conductor server, task workers, and dependent services. Debugging production issues requires log correlation only. |
| **Recommendation** | Add `micrometer-tracing-bridge-otel` and `opentelemetry-exporter-otlp` to instrument the Conductor server with OpenTelemetry. Configure X-Ray as the tracing backend via the AWS Distro for OpenTelemetry (ADOT) collector sidecar on EKS. Propagate trace context (`traceparent` header) through the task polling API so workers can continue traces. |
| **Evidence** | `metrics/build.gradle` (OTLP metrics only), no tracing dependencies in any `build.gradle` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No SLO configuration files, no error budget tracking, no CloudWatch composite alarms for SLI monitoring. The Spring Boot Actuator health endpoint is configured (`management.endpoint.health.show-details=always`) and Prometheus metrics are exposed (`management.endpoints.web.exposure.include=health,info,prometheus`), which provides raw signals for SLO calculation, but no SLOs are defined. No latency percentile targets (p99, p95) specified for workflow execution or task polling. |
| **Gap** | No formal SLO definitions. Cannot measure whether the system is meeting user expectations or degrading over time. |
| **Recommendation** | Define SLOs for critical user journeys: workflow start latency (p99 < X ms), task poll latency (p99 < X ms), workflow completion success rate (> 99.X%). Use CloudWatch or Datadog SLO features to track error budgets. The Micrometer metrics (especially `workflow_execution`, `task_queue_wait`, `workflow_decision`) provide the raw signals needed. |
| **Evidence** | `server/src/main/resources/application.properties` (Actuator, Prometheus config), no SLO definition files |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Extensive custom business metrics are published via Micrometer in `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` (472 lines). Metrics include: `workflow_start_success` (by workflow name, version, owner), `workflow_failure` (by name, status, owner), `workflow_execution` (timer by name and owner), `task_execution` (timer by type, status), `task_queue_wait` (timer by type), `task_queue_depth` (gauge by type and owner), `task_in_progress` (gauge), `workflow_running` (gauge), `task_poll_count`, `task_timeout`, `task_response_timeout`, `event_queue_messages_processed`, `dao_requests` (by DAO, action, task/workflow type), `dao_payload_size`, and more. The `metrics` module supports 14 Micrometer registries: Prometheus, CloudWatch, Datadog, JMX, OTLP, Dynatrace, Elastic, New Relic, Stackdriver, StatsD, Azure Monitor, Influx, Atlas. Percentiles configured at p50, p75, p90, p95, p99. |
| **Gap** | N/A — Business metrics are comprehensive and cover all critical workflow orchestration dimensions. |
| **Recommendation** | No action needed. When deploying to AWS, enable the CloudWatch metrics registry (`management.cloudwatch.metrics.export.enabled=true`) and configure the `conductor` namespace. Create CloudWatch dashboards for workflow execution rates, queue depths, and error rates. |
| **Evidence** | `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`, `metrics/build.gradle` (14 Micrometer registries), `server/src/main/resources/application.properties` (metrics config) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configuration found. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no alerting rules in any configuration file. The Prometheus metrics endpoint is exposed, but no Prometheus AlertManager rules or Grafana alert configurations are included. No composite alarms, no static threshold alarms. |
| **Gap** | No alerting of any kind. Production issues can only be discovered through manual monitoring or user reports. |
| **Recommendation** | When deploying to AWS: create CloudWatch alarms on key Conductor metrics — workflow failure rate > threshold, task queue depth growing unbounded, task timeout rate spike, workflow execution latency p99 exceeding SLO. Configure CloudWatch anomaly detection on error rates and latency. Integrate with SNS → PagerDuty/OpsGenie for on-call alerting. |
| **Evidence** | No alerting configuration found in repository. `server/src/main/resources/application.properties` (metrics export configs all disabled) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The `publish.yml` workflow builds and pushes Docker images to Docker Hub on release events. The `publish_build.yaml` workflow also builds and pushes. Both push directly to the registry with version tags and `latest` tag — there is no staged rollout, blue/green, canary, or rolling deployment. No CodeDeploy, Argo Rollouts, Helm canary, Lambda traffic shifting, or ALB weighted target groups found. |
| **Gap** | Direct-to-registry push with no deployment strategy. All consumers pulling `latest` get the new version simultaneously with no rollback mechanism. |
| **Recommendation** | When deploying to EKS: implement rolling deployments with Kubernetes Deployment strategy (`RollingUpdate` with `maxSurge` and `maxUnavailable`). Graduate to canary deployments with Argo Rollouts or EKS + App Mesh traffic shifting. Implement automated rollback based on health check failures and error rate metrics. |
| **Evidence** | `.github/workflows/publish.yml` (direct push), `.github/workflows/publish_build.yaml` (direct push) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong integration test coverage exists across multiple modules. **test-harness:** Spock/JUnit integration tests using TestContainers for Redis, Elasticsearch, and LocalStack (SQS, S3). Tests run as a separate CI job in `ci.yml`. Includes the `functionalTest` source set that compiles and runs e2e tests against an embedded Conductor server. **e2e:** Dedicated end-to-end test module with tests against multiple backend configurations: `run_tests-postgres.sh`, `run_tests-mysql.sh`, `run_tests-es8.sh`, `run_tests-redis-os2.sh`, `run_tests-redis-os3.sh`. Uses JUnit 5, Awaitility, and the Conductor client SDK. **UI:** Cypress E2E and component tests run in CI (`ci.yml` `build-ui` job). |
| **Gap** | The e2e test suite is not part of the standard CI pipeline — it requires manual activation (`RUN_E2E=true`). The test-harness runs in CI but the full e2e suite against Docker Compose backends does not. |
| **Recommendation** | Enable the e2e test suite as a CI gate, at least for the primary backend configuration (Postgres). Add contract testing between Conductor server and client SDKs. Run e2e tests against the production-equivalent backend configuration before release. |
| **Evidence** | `test-harness/build.gradle`, `e2e/build.gradle` (`onlyIf { System.getenv('RUN_E2E') == 'true' }`), `e2e/run_tests-postgres.sh`, `.github/workflows/ci.yml` (test-harness + build-ui jobs) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns found. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files (markdown, YAML, JSON) in the repository. `SECURITY.md` documents the vulnerability reporting process but not operational incident response. |
| **Gap** | No incident response automation. All incident handling is ad hoc. |
| **Recommendation** | Create operational runbooks for common Conductor incidents: stuck workflows, Redis connection failures, Elasticsearch indexing lag, task queue backlog. Implement self-healing patterns: auto-restart stuck workflows via a scheduled Lambda, auto-scale on queue depth growth, circuit breaker for external task HTTP calls. Store runbooks as versioned Markdown or SSM Automation documents. |
| **Evidence** | No runbook files found. `SECURITY.md` (vulnerability reporting only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership structure found. No CODEOWNERS file for observability assets, no per-service dashboards, no named alarm owners, no SLO definitions with team attribution. The `dependabot.yml` names 3 reviewers (`v1r3n`, `boney9`, `c4lm`) for dependency updates but no observability ownership. No CloudWatch dashboard definitions, no Grafana dashboard JSON files in the repository. |
| **Gap** | No observability ownership. No team is explicitly responsible for monitoring, alerting, or SLO tracking. |
| **Recommendation** | Add a CODEOWNERS file with observability asset ownership. Create per-component dashboards (server health, workflow execution, task processing, queue depth, database performance) and assign team owners. Define SLOs with team attribution for accountability. |
| **Evidence** | No CODEOWNERS file, no dashboard configurations, `.github/dependabot.yml` (3 reviewers for deps only) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists because no IaC exists. No `default_tags` in Terraform provider, no `tags` on CloudFormation resources, no `required-tags` Config rules, no Tag Policies. Docker Compose services have no AWS resource tagging equivalent. |
| **Gap** | No tagging strategy, governance, or enforcement. When IaC is created, tagging must be established from the start. |
| **Recommendation** | When creating IaC, establish a tagging standard with required keys: `Environment` (dev/staging/prod), `Service` (conductor), `Owner` (team), `CostCenter`, `ManagedBy` (terraform/cdk). Enforce via Terraform `default_tags` and AWS Config `required-tags` rules. Activate cost allocation tags. |
| **Evidence** | No IaC files with tags, no Tag Policy or Config rule definitions |

---

## Learning Materials

### Triggered Pathway Learning Resources

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `build.gradle` | APP-Q1, SEC-Q6, SEC-Q7 | Java 21, Spring Boot 3.3.11, CVE constraints, dependency management |
| `dependencies.gradle` | APP-Q1, INF-Q4 | AWS SDK 2.31.68, Spring AI 1.1.2, Kafka 2.6.0, Micrometer 1.14.6 |
| `settings.gradle` | APP-Q2 | 40+ Gradle submodules defining modular monolith structure |
| `gradle.properties` | APP-Q1 | Version 3.3.0.rc4-SNAPSHOT |
| `server/build.gradle` | APP-Q2, INF-Q3, INF-Q4 | Server assembly of all modules, persistence backend selection |
| `rest/build.gradle` | SEC-Q3, APP-Q5 | REST module dependencies (no security), springdoc |
| `ai/build.gradle` | DATA-Q1 | Spring AI, Bedrock, vector DBs (pgvector, Pinecone, MongoDB), Tika, MCP |
| `kafka/build.gradle` | INF-Q4 | Kafka client 2.6.0, event queue integration |
| `kafka-event-queue/build.gradle` | INF-Q4 | Kafka event queue alternative |
| `awssqs-event-queue/build.gradle` | INF-Q4 | AWS SQS SDK v2 for managed messaging |
| `awss3-storage/build.gradle` | DATA-Q1, SEC-Q2 | S3 external payload storage |
| `metrics/build.gradle` | OPS-Q3 | 14 Micrometer registries including CloudWatch |
| `postgres-persistence/build.gradle` | DATA-Q2, DATA-Q4 | PostgreSQL persistence with Flyway |
| `mysql-persistence/build.gradle` | DATA-Q2, DATA-Q4 | MySQL persistence with Flyway |
| `docker/server/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage build, debian:stable-slim, health check |
| `docker/docker-compose.yaml` | INF-Q1, INF-Q2, INF-Q5, INF-Q7, INF-Q8, INF-Q9, DATA-Q3 | Redis 6.2.3, ES 7.17.11, flat network, single instances |
| `docker/docker-compose-postgres.yaml` | INF-Q2, DATA-Q3, SEC-Q5 | PostgreSQL 16, plaintext credentials |
| `docker/docker-compose-mysql.yaml` | INF-Q2, DATA-Q3, SEC-Q5 | MySQL latest (unpinned), plaintext credentials |
| `docker/server/config/config-redis.properties` | INF-Q4, APP-Q6, OPS-Q3 | Redis config, Prometheus metrics, ES indexing |
| `docker/server/config/config-postgres.properties` | SEC-Q5, APP-Q6 | Plaintext credentials, DB connection |
| `docker/server/config/config-mysql.properties` | SEC-Q5, APP-Q6 | Plaintext credentials, DB connection |
| `server/src/main/resources/application.properties` | OPS-Q3, OPS-Q4, SEC-Q5 | Metrics config, AI provider keys via env vars |
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | Build, test-harness, Cypress, JaCoCo, SonarCloud |
| `.github/workflows/publish.yml` | INF-Q11, OPS-Q5 | Maven publish, Docker multi-arch push |
| `.github/workflows/publish_build.yaml` | INF-Q11, OPS-Q5 | Server-lite and Docker publish |
| `.github/dependabot.yml` | SEC-Q7 | Weekly Gradle + GitHub Actions updates |
| `core/src/main/java/com/netflix/conductor/dao/` | DATA-Q2 | 8 DAO interfaces (ExecutionDAO, MetadataDAO, etc.) |
| `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` | OPS-Q3 | Custom Micrometer business metrics (472 lines) |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` | APP-Q3, APP-Q4, APP-Q5, SEC-Q3 | Workflow REST API, executeWorkflow, search-v2 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/TaskResource.java` | APP-Q5, SEC-Q3 | Task REST API, search-v2, update-v2 |
| `rest/src/main/java/com/netflix/conductor/rest/config/RequestMappingConstants.java` | APP-Q5, INF-Q6 | API paths (/api/ prefix, no versioning) |
| `postgres-persistence/src/main/resources/db/migration_postgres/V1__initial_schema.sql` | DATA-Q4 | Initial schema, standard SQL |
| `postgres-persistence/src/main/resources/db/migration_postgres/V10__poll_data_check.sql` | DATA-Q4 | Poll data trigger function |
| `postgres-persistence/src/main/resources/db/migration_postgres_notify/V10.1__notify.sql` | DATA-Q4 | Queue notification triggers |
| `mysql-persistence/src/main/resources/db/migration/V8__update_pk.sql` | DATA-Q4 | Migration procedures (DropIndexIfExists) |
| `test-harness/build.gradle` | OPS-Q6 | Integration tests with TestContainers, LocalStack |
| `e2e/build.gradle` | OPS-Q6 | E2E tests, `RUN_E2E=true` gate |
| `e2e/run_tests-postgres.sh` | OPS-Q6 | E2E test runner for Postgres backend |
| `schemas/` | APP-Q5 | JSON schemas for Task, TaskDef, Workflow, WorkflowDef |
| `SECURITY.md` | SEC-Q1, OPS-Q7 | Vulnerability reporting policy |
| `docs/` | Quick Agent Wins | Architecture guides, developer guides, quickstart |
| `ai/src/main/java/org/conductoross/conductor/ai/vectordb/` | Move to AI | Vector DB implementations (MongoDB, Pinecone, pgvector) |
