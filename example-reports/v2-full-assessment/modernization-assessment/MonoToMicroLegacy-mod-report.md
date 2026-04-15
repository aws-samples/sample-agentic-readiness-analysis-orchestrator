# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | MonoToMicroLegacy |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | monolith, java, ec2, decomposition-target |
| **Context** | Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs. |
| **Overall Score** | 1.43 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.00 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 1.67 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.00 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **1.43 / 4.0** | **❌ Not Present** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC files — 100% of infrastructure is manually created (ClickOps). No Terraform, CloudFormation, CDK, Helm, or Kustomize. | Blocks reproducible deployments, disaster recovery, and environment consistency. Foundation for all other modernization pathways. |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline definitions. No GitHub Actions, Jenkinsfile, buildspec, or CodePipeline. Builds are local Gradle only. | Manual deployments are error-prone, slow, and block rapid iteration. Required for containers, GitOps, and safe decomposition. |
| 3 | INF-Q1: Managed Compute | 1 | All compute runs on raw EC2 instances. No ECS, EKS, Fargate, or managed container orchestration. | High operational overhead for patching, scaling, and capacity management. Blocks containerization and cloud-native pathways. |
| 4 | INF-Q2: Managed Databases | 1 | MySQL is self-managed (likely on EC2). No RDS, Aurora, or managed database service. No automated failover or backups. | Manual patching, backup, and scaling burden. Single point of failure. Blocks managed database migration pathway. |
| 5 | SEC-Q5: Secrets Management | 1 | Database credentials hardcoded in `application.properties` in plaintext (`MonoToMicroUser` / `MonoToMicroPassword`). Committed to version control. | Critical security vulnerability. Credential exposure risk. Must be remediated before any production modernization. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2 required). The repository pattern with MyBatis mappers (`UnicornMapper`, `UserMapper`, `HealthMapper`) provides a clean, centralized data access layer through well-defined repository interfaces (`UnicornRepository`, `UserRepository`, `HealthRepository`).
- **What it enables:** A natural-language-to-SQL agent that queries the unicorn product catalog, user basket contents, and user account data through the structured repository layer. This directly supports the stated context requirement: "The agent needs access to order and return data through discrete service APIs."
- **Additional steps:** Generate an OpenAPI specification from the Spring Boot controllers (`/unicorns`, `/unicorns/basket/{userUuid}`, `/user`, `/user/login`) to enable full tool discovery for the agent. The controllers return structured JSON responses (Jackson serialization) which are agent-friendly.
- **Effort:** Medium — the data access layer exists and is well-structured, but an OpenAPI spec must be generated and the controllers need API versioning before agent integration is production-ready.

> **Note:** 5 of 6 potential Quick Agent Wins are not available due to missing foundations: no API documentation (blocks API-aware agent), no CI/CD pipeline (blocks DevOps agent), insufficient documentation (blocks RAG knowledge agent), no workflow orchestration (blocks workflow agent), and no distributed tracing (blocks observability agent). Prioritize the Modern DevOps pathway to unlock these wins.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=1, APP-Q4=1 — monolith on EC2 with all-sync communication |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no container definitions found — raw EC2 with no Dockerfile |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); MySQL is already open-source; no commercial DB engines detected |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1, DATA-Q3=2 — self-managed MySQL with uncontrolled engine version |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: no data processing workloads, ETL, streaming, or analytics artifacts found — simple CRUD e-commerce app |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=1, OPS-Q5=1, OPS-Q6=1 — zero IaC, zero CI/CD, no deployment strategy, no tests |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks, no vector DB, no RAG, no agent eval framework detected |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a Spring Boot 2.1.x monolith (APP-Q2 = 2) deployed on a single EC2 instance. The `Application.java` entry point bootstraps a single `@SpringBootApplication` process. The `HealthController` uses `EC2MetadataUtils.getInstanceInfo()` confirming raw EC2 deployment. The codebase has identifiable module boundaries — `UnicornController`/`BasketController` (product catalog + basket), `UserController` (user management), and `HealthController`/`DataReplicationController` (operational endpoints) — but these modules share a single MySQL database (`unishop` schema) and the `UnicornService` combines both catalog and basket logic in a single service class.

**Compute Model Gaps (INF-Q1 = 1):**
All compute is raw EC2. No ECS, EKS, or managed container orchestration exists. No IaC defines compute resources.

**Communication Pattern Gaps (APP-Q3 = 1, APP-Q4 = 1):**
All inter-component communication is synchronous HTTP request-response. No async messaging patterns exist. No EventBridge, SQS, or event-driven handlers. Every controller endpoint blocks until the MySQL query completes.

**Recommended Decomposition Approach:**
Strangler Fig with EKS (see Decomposition Strategy section below). Extract the Basket/Order service first to satisfy the agent's need for discrete service APIs for order and return data.

**Representative AWS Services:**
- **EKS** (preferred) for container orchestration of decomposed microservices
- **API Gateway** (preferred) as the unified entry point with request routing, throttling, and authentication
- **EventBridge** (preferred) for event-driven communication between extracted services
- **Aurora MySQL** (preferred) as per-service managed database after data separation

**Recommended Patterns:**
- Strangler Fig pattern for incremental extraction
- Anti-corruption Layer between new services and legacy monolith
- Event Sourcing with EventBridge for basket/order events
- Saga pattern for distributed transactions spanning Catalog, Basket, and User services

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Decompose monoliths into microservices](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model (INF-Q1 = 1):**
The application runs on raw EC2 instances. `HealthController.java` directly calls `EC2MetadataUtils.getInstanceInfo()` to report EC2 instance metadata (account ID, AZ, instance ID, instance type, region). No Dockerfile exists — the `docker` task in `build.gradle` is commented out. No `docker-compose.yml` or Kubernetes manifests exist.

**Container Readiness Indicators:**
- ✅ Spring Boot fat JAR with `bootJar { launchScript() }` — self-contained, single artifact deployment
- ✅ Application port externalized (`server.port=8080` in `application.properties`)
- ✅ Database endpoint via environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) — partially externalized config
- ⚠️ Database credentials hardcoded in `application.properties` — must be externalized to secrets before containerization
- ⚠️ `EC2MetadataUtils` usage in `HealthController` — must be replaced with container-aware health checks
- ⚠️ Java 8 source compatibility — consider upgrading to Java 17+ for better container support (GC tuning, container-aware memory limits)

**Recommended Container Orchestration:**
**EKS** (preferred) with Terraform (preferred) for IaC. Avoid self-managed Kubernetes (per preferences).

**Migration Approach:**
Lift-and-containerize first — create a Dockerfile for the existing monolith, deploy to EKS, then extract services incrementally (Strangler Fig).

**Representative AWS Services:**
- **Amazon EKS** (preferred) for Kubernetes orchestration
- **Amazon ECR** for container image registry
- **AWS App Runner** as a simpler alternative for initial containerization

**AWS Container Migration Guidance:**
- [Containerize Java applications on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-containers/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):**
MySQL is self-managed — `application.properties` connects to `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop` with no RDS or Aurora resource definitions in IaC (no IaC exists). The database likely runs on EC2 with manual patching, backup, and scaling. Connection uses `mysql-connector-java:8.0.11`.

**Engine Versions and EOL Status (DATA-Q3 = 2):**
MySQL connector 8.0.11 is pinned in `build.gradle`, but the actual MySQL server engine version is unknown — no IaC controls it. MySQL 8.0 is supported, but without version pinning in infrastructure, the server may be running any version including EOL releases (MySQL 5.6 and 5.7 are past EOL).

**Data Access Patterns (DATA-Q2 = 3):**
Clean, consistent repository pattern via MyBatis mappers. All queries use standard ANSI SQL with no stored procedures (DATA-Q4 = 4). Schema is simple: 3 tables (`unicorns`, `unicorns_basket`, `unicorn_user`) with straightforward JOINs. This makes migration highly feasible with minimal query rewriting.

**Recommended Managed Database Target:**
**Aurora MySQL** (preferred) — wire-compatible with MySQL, zero query changes required. Provides automated backups, Multi-AZ failover, auto-scaling storage, and managed patching.

**Migration Tools:**
- **AWS Database Migration Service (DMS)** for online data migration with minimal downtime
- Connection string update: change `MONO_TO_MICRO_DB_ENDPOINT` from EC2 MySQL host to Aurora MySQL cluster endpoint

**Representative AWS Services:**
- **Amazon Aurora MySQL** (preferred) for the primary relational database
- **Amazon DynamoDB** (preferred) as a future option for the basket service after decomposition (key-value access pattern)

**AWS Managed Database Migration Guidance:**
- [Migrate MySQL to Aurora MySQL](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-mysql-to-aurora-mysql/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure-as-code files exist in the repository. No `.tf`, CloudFormation, CDK, Helm, or Kustomize files. All infrastructure is manually created (ClickOps). This is the most foundational gap — every other modernization pathway depends on having infrastructure defined in code.

**Current CI/CD State (INF-Q11 = 1):**
No CI/CD pipeline definitions. No `.github/workflows`, `Jenkinsfile`, `buildspec.yml`, or CodePipeline. The only build mechanism is a local `build.gradle` with Gradle wrapper. Deployments are entirely manual.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy — no blue/green, canary, or rolling deployments. No CodeDeploy, Helm releases, or Argo Rollouts. Direct-to-production deployment with no staged rollout.

**Testing Gaps (OPS-Q6 = 1):**
No automated tests exist. `spring-boot-starter-test` is declared in `build.gradle`, but no `src/test` directory or test files exist. No integration tests, no API test suites, no test containers.

**Recommended DevOps Toolchain (respecting preferences):**
- **Terraform** (preferred) for all infrastructure provisioning (EKS cluster, Aurora MySQL, VPC, IAM, etc.)
- **GitOps** (preferred) with ArgoCD or Flux for Kubernetes deployment automation
- **GitHub Actions** or **AWS CodePipeline + CodeBuild** for CI pipeline (build, test, security scan)
- Canary deployments via Argo Rollouts on EKS (preferred)

**Implementation Order:**
1. **IaC foundation** — Define VPC, subnets, security groups, EKS cluster, and Aurora MySQL in Terraform
2. **CI pipeline** — Add GitHub Actions or CodeBuild for automated build, unit test, and container image creation
3. **CD pipeline** — Implement GitOps with ArgoCD for EKS deployments
4. **Integration tests** — Add test suites before decomposition to establish regression safety net
5. **Deployment strategy** — Configure canary deployments via Argo Rollouts

**Representative AWS Services:**
- **AWS CodeBuild** for CI builds
- **AWS CodePipeline** for pipeline orchestration
- **Amazon EKS** (preferred) as deployment target
- **AWS CloudWatch** for pipeline monitoring

**AWS DevOps Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-migration/dev-ops.html)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI or agent framework usage detected in the repository:
- ❌ No Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker imports
- ❌ No vector database infrastructure (no OpenSearch vector engine, Pinecone, pgvector, Weaviate, or Qdrant)
- ❌ No RAG implementation patterns (no embedding generation, vector store queries, or retrieval chains)
- ❌ No agent evaluation frameworks (no Ragas, DeepEval, or custom eval harness)

The AWS SDK v1 (`aws-java-sdk:1.11.567`) is present in `build.gradle` but does not include Bedrock client (which requires AWS SDK v2).

**Application Domain and Potential AI Use Cases:**
The Unicorn Shop is an e-commerce application with a product catalog, shopping basket, and user management. Potential AI integrations:
1. **Product recommendation engine** — Use Bedrock (preferred) to generate personalized unicorn recommendations based on basket history
2. **Natural language product search** — Agent-powered search over the unicorn catalog using Bedrock embeddings
3. **Order/return data agent** — Aligns directly with stated context: "The agent needs access to order and return data through discrete service APIs." After decomposition, the Basket/Order microservice API becomes a tool the agent can invoke.

**Quick Wins:** See Quick Agent Wins section — the Data Query Agent is immediately viable given the clean data access layer (DATA-Q2 = 3).

**Foundation Requirements Before AI Integration:**
1. Upgrade to AWS SDK v2 (Bedrock requires `software.amazon.awssdk:bedrockruntime`)
2. Generate OpenAPI specifications from Spring controllers for agent tool discovery
3. Implement API authentication (SEC-Q3) before exposing endpoints as agent tools
4. Add structured logging (OPS-Q1) for agent action traceability

**Recommended AI Services:**
- **Amazon Bedrock** (preferred) for foundation model access and agent orchestration
- **Amazon Bedrock AgentCore** for agent runtime management
- **Amazon OpenSearch Service** with vector engine for semantic product search

**AWS AI/ML Prescriptive Guidance:**
- [Amazon Bedrock Getting Started](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)

---

## Decomposition Strategy

> **Condition:** APP-Q2 = 2 (< 3) — Monolith with identifiable modules but significant coupling through shared database.

### Recommended Approach: Strangler Fig (Parallel Track)

**Why this approach:** APP-Q2 = 2 indicates the monolith has identifiable module boundaries that can be extracted incrementally. The controller/service/repository layering provides natural seams for extraction. The stated context — "The agent needs access to order and return data through discrete service APIs" — makes the Basket/Order module the highest-priority extraction candidate.

**Extraction Sequence:**

| Phase | Service to Extract | Source Module | Target | Timeline |
|-------|-------------------|---------------|--------|----------|
| 0 | Containerize monolith as-is | Entire app | EKS (preferred) | 2–4 weeks |
| 1 | Basket/Order Service | `BasketController` + basket operations from `UnicornServiceImpl` + `unicorns_basket` table | EKS microservice + DynamoDB (preferred) or Aurora MySQL (preferred) | 3–4 months |
| 2 | User Service | `UserController` + `UserServiceImpl` + `unicorn_user` table | EKS microservice + Aurora MySQL (preferred) | 2–3 months |
| 3 | Product Catalog Service | `UnicornController` + catalog operations from `UnicornServiceImpl` + `unicorns` table | EKS microservice + Aurora MySQL (preferred) | 2–3 months |

**Phase 0** is the Conditional/Adaptive quick win — containerize the monolith first to gain immediate benefits (portability, consistent environments, EKS deployment) before starting decomposition.

### Alternative Approach: Conditional / Adaptive

Containerize the monolith as-is first (Phase 0), then selectively extract only the Basket/Order service (Phase 1) to satisfy the immediate agent API requirement. Defer User and Catalog extraction until business need arises. This approach takes 4–6 months for the first discrete service API.

### Approach NOT Recommended: Big-Bang Rewrite

⚠️ **Not recommended.** The monolith has identifiable module boundaries (APP-Q2 = 2), making incremental extraction viable. A big-bang rewrite introduces high risk of scope creep, feature parity gaps, and failed cutover. The 9–15 month timeline for Strangler Fig is lower risk with incremental value delivery.

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted Basket Service from monolith's `UnicornMapper` queries. Prevent monolith schema assumptions from leaking into new service. | Phase 1: Place ACL between new Basket Service and monolith's `unishop` schema. Translate `unicorns_basket` JOINs to dedicated basket data model. |
| **Saga Pattern** | Manage distributed transactions for basket operations that currently rely on single-database ACID transactions. | Phase 1: When basket operations need to coordinate with catalog (e.g., checking unicorn existence via `unicorns` table JOIN in `getUnicornBasket`). Use EventBridge (preferred) for saga coordination. |
| **Event Sourcing** | Capture basket add/remove events as an immutable event stream instead of current CRUD-only pattern. | Phase 1: Replace `addUnicornToBasket`/`removeUnicornFromBasket` with events published to EventBridge (preferred). Enables audit trail and cross-service event consumption. |
| **Hexagonal Architecture** | Structure each new microservice with clear ports and adapters — business logic core separated from HTTP controllers and database adapters. | Every extracted service — ensures testability and infrastructure portability. |

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)
- [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html)

### Effort Calibration

| Factor | Assessment | Effort Signal |
|--------|-----------|---------------|
| Module boundaries | Clear controller/service/repository layers. However, `UnicornService` handles both catalog AND basket — coupling. | Moderate |
| Data coupling | Single shared `unishop` MySQL schema. `getUnicornBasket` JOINs `unicorns` and `unicorns_basket` tables. All 3 domain models share one `DataSource`. | High |
| Stored procedures | None — DATA-Q4 = 4. All business logic in Java. | Low |
| Communication patterns | 100% synchronous HTTP — APP-Q3 = 1. Must introduce async patterns (EventBridge preferred) from scratch. | High |
| CI/CD maturity | No pipeline — INF-Q11 = 1. Must build CI/CD from scratch before safe multi-service deployment. | High |
| Test coverage | Zero tests — OPS-Q6 = 1. No regression safety net for extraction. Must add tests before cutting. | High |

**Calibrated Estimate:** 9–15 months for full Strangler Fig decomposition across all 3 phases. Shorter (4–6 months) if using Conditional approach targeting only Basket/Order Service extraction.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs on raw EC2 instances. `HealthController.java` uses `EC2MetadataUtils.getInstanceInfo()` to retrieve EC2 instance metadata (account ID, AZ, instance ID, instance type, region), confirming direct EC2 deployment. No ECS, EKS, Fargate, or Lambda resources found. No IaC exists to define any managed compute. The `docker` task in `build.gradle` is commented out, indicating containerization was considered but never implemented. |
| **Gap** | 100% of compute is raw EC2 with no managed container orchestration or serverless. |
| **Recommendation** | Containerize the Spring Boot application on EKS (preferred). Create a Dockerfile for the fat JAR, set up ECR for image storage, and deploy to an EKS cluster provisioned via Terraform (preferred). Replace `EC2MetadataUtils` calls in `HealthController` with Kubernetes-native health probes. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (EC2MetadataUtils usage), `build.gradle` (commented docker task), `src/main/resources/application.properties` (server.port=8080) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | `application.properties` connects to MySQL via `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The database endpoint is provided via environment variable, but no RDS, Aurora, or managed database IaC resources exist (no IaC exists at all). Connection uses `mysql-connector-java:8.0.11`. The database is likely self-managed MySQL installed on EC2 with manual patching, backup, and scaling. |
| **Gap** | Database is fully self-managed with no automated failover, no managed backups, no auto-scaling storage. |
| **Recommendation** | Migrate to Aurora MySQL (preferred) using AWS DMS for minimal-downtime migration. Aurora MySQL is wire-compatible with MySQL — zero query changes required given the standard SQL usage. Update `MONO_TO_MICRO_DB_ENDPOINT` environment variable to point to the Aurora cluster endpoint. Define the Aurora cluster in Terraform (preferred). |
| **Evidence** | `src/main/resources/application.properties` (JDBC connection string), `build.gradle` (mysql-connector-java:8.0.11) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service detected. No Step Functions, Temporal, Camunda, or workflow engine imports. All business logic is hardcoded in the service layer: `UnicornServiceImpl` handles catalog queries and basket CRUD operations, `UserServiceImpl` handles user creation and login. Business flows follow a simple request → service → repository → mapper → database pattern with no orchestration. |
| **Gap** | All workflow logic is hardcoded in application code with no dedicated orchestration service. |
| **Recommendation** | As microservices are extracted (see Decomposition Strategy), introduce AWS Step Functions for cross-service business workflows (e.g., order processing that spans Basket, Catalog, and User services). For the current monolith, this is lower priority than IaC, CI/CD, and containerization. |
| **Evidence** | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java`, `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure detected. No SQS, SNS, EventBridge, MSK, or Kinesis references in any file. All controller endpoints (`UnicornController`, `BasketController`, `UserController`, `DataReplicationController`) are synchronous HTTP request-response. The event classes in `com.monoToMicro.core.events` package are internal POJO wrappers for method return values — not actual messaging events. No message publishing or consumption patterns exist. |
| **Gap** | Zero async communication — all inter-component communication is synchronous HTTP with no messaging infrastructure. |
| **Recommendation** | Introduce EventBridge (preferred) for event-driven communication between extracted microservices. Publish basket events (add/remove unicorn) to EventBridge for cross-service consumption. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (sync HTTP), `src/main/java/com/monoToMicro/core/events/` (internal POJOs, not messaging events) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL configuration found. No IaC exists to define network topology. The application listens on port 8080 with no evidence of network segmentation. `ResourceServerConfig` and `Application.java` configure CORS to allow all origins and methods — `registry.addMapping("/**").allowedMethods("HEAD", "GET", "PUT", "POST", "DELETE", "PATCH", "OPTIONS")`. |
| **Gap** | No network security configuration. Application may be directly exposed to the internet without VPC controls. |
| **Recommendation** | Define VPC with public and private subnets in Terraform (preferred). Place the EKS cluster (preferred) in private subnets. Use an API Gateway (preferred) or ALB in public subnets as the entry point. Configure security groups with least-privilege rules. Restrict CORS origins to known domains. |
| **Evidence** | `src/main/java/com/monoToMicro/config/MVCConfig.java` (open CORS), `src/main/java/com/monoToMicro/Application.java` (CORS workaround) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront detected. The application listens directly on `server.port=8080`. No IaC defines load balancers or API gateway resources. `HealthController` exposes EC2 instance metadata directly via the `/health/ping` endpoint, suggesting the application is accessed directly on the EC2 instance without any managed entry point. |
| **Gap** | Services exposed directly with no gateway, load balancer, throttling, or authentication at the entry point. |
| **Recommendation** | Deploy API Gateway (preferred) as the unified entry point for all API endpoints. Configure throttling, request validation, and authentication (Cognito authorizer) on the gateway. Route traffic to the EKS cluster (preferred) via VPC link. |
| **Evidence** | `src/main/resources/application.properties` (server.port=8080), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (direct EC2 metadata exposure) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration detected. No ASG (Auto Scaling Group), Application Auto Scaling, ECS service auto-scaling, or Lambda concurrency limits. The application runs on a static EC2 instance with no ability to scale in response to traffic changes. No IaC exists to define scaling policies. |
| **Gap** | All capacity is statically provisioned. No auto-scaling mechanism exists. |
| **Recommendation** | When deploying to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) for the application pods based on CPU/memory utilization. Add Cluster Autoscaler or Karpenter for node-level scaling. Define scaling policies in Terraform (preferred). |
| **Evidence** | `src/main/resources/application.properties` (static port), No IaC files found |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning, no EBS snapshot lifecycle policies. No IaC exists. The self-managed MySQL database has no documented backup strategy — no automated backups, no PITR, no restore testing evidence. |
| **Gap** | No backup configuration for any data store. No disaster recovery capability. |
| **Recommendation** | Aurora MySQL (preferred) provides automated backups with configurable retention (up to 35 days) and continuous PITR by default. After migrating to Aurora, verify backup retention is set appropriately and test restore procedures. Define backup configuration in Terraform (preferred). |
| **Evidence** | No IaC files found, `database/create_tables.sql` (schema definition with no backup references) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration detected. `HealthController` reports a single EC2 instance with one availability zone. No load balancer distributes traffic across AZs. No IaC defines multi-AZ deployment. A single AZ failure would take down the entire application and database. |
| **Gap** | All resources in a single AZ. No fault isolation or automatic recovery from AZ failure. |
| **Recommendation** | Deploy EKS (preferred) across at least 2 AZs with pods distributed across AZ-aware node groups. Aurora MySQL (preferred) provides Multi-AZ by default with automatic failover. Define multi-AZ subnet configuration in Terraform (preferred). |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (single instance AZ reporting) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files exist in the repository. No `.tf` (Terraform), CloudFormation templates, CDK stacks, Helm charts, or Kustomize files found. The entire infrastructure — EC2 instances, MySQL database, networking, security groups — is manually created (ClickOps). The repository contains only application source code, build configuration, and database DDL. |
| **Gap** | 0% IaC coverage. All infrastructure is manually provisioned and non-reproducible. |
| **Recommendation** | Adopt Terraform (preferred) immediately as the foundational modernization step. Start by codifying the existing infrastructure (VPC, subnets, security groups, EC2 instances, MySQL). Then evolve to target-state IaC (EKS cluster, Aurora MySQL, API Gateway). Use GitOps (preferred) for IaC deployment automation. |
| **Evidence** | Repository-wide scan: no `.tf`, `.cfn.yaml`, `.cfn.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline definitions exist. No `.github/workflows/`, `Jenkinsfile`, `buildspec.yml`, `.gitlab-ci.yml`, or CodePipeline definitions in IaC. The only build mechanism is `build.gradle` with Gradle wrapper (`gradlew`), which provides local compilation and packaging only. No automated test, build, deploy, or security scanning stages. |
| **Gap** | No CI/CD — all deployments are manual. No automated testing, building, or deployment pipeline. |
| **Recommendation** | Create a CI/CD pipeline using GitHub Actions or AWS CodePipeline + CodeBuild. Pipeline stages: (1) build with Gradle, (2) run unit and integration tests, (3) security scan (SAST + dependency), (4) build container image and push to ECR, (5) deploy to EKS via GitOps (preferred) with ArgoCD. Avoid manual deployments (per preferences). |
| **Evidence** | `build.gradle` (local Gradle build only), Repository-wide scan: no CI/CD config files found |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 8 (`sourceCompatibility = 1.8`) with Spring Boot 2.1.x. Java has a mature cloud-native ecosystem with extensive AWS SDK support, container tooling, microservices frameworks (Spring Cloud, Micronaut, Quarkus), and one of the largest developer communities. Dependencies include Spring Boot Web, Spring Security, MyBatis, AWS SDK v1, and Jackson for JSON serialization. |
| **Gap** | Java 8 is functional but nearing the end of community support. Spring Boot 2.1.x is EOL. AWS SDK v1 is in maintenance mode. |
| **Recommendation** | Upgrade to Java 17+ and Spring Boot 3.x during containerization. Migrate from AWS SDK v1 (`com.amazonaws`) to AWS SDK v2 (`software.amazon.awssdk`) which is required for Bedrock integration. These upgrades can be bundled with the containerization effort. |
| **Evidence** | `build.gradle` (sourceCompatibility = 1.8, springBootVersion = '2.1.0.RELEASE', aws-java-sdk:1.11.567) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit — one `build.gradle`, one `Application.java` `@SpringBootApplication` entry point, one `bootJar` artifact. The code has identifiable modules with layered architecture: controllers (`UnicornController`, `BasketController`, `UserController`, `HealthController`, `DataReplicationController`), service interfaces + implementations (`UnicornService/Impl`, `UserService/Impl`, `HealthService/Impl`), repository interfaces + implementations, and MyBatis mappers. **Coupling:** `UnicornService` handles both product catalog AND basket operations through a single `UnicornRepository`, combining two distinct business domains. All modules share a single MySQL database (`unishop` schema) with 3 tables. `getUnicornBasket` in `UnicornMapper.xml` JOINs `unicorns` and `unicorns_basket` tables, creating data coupling between catalog and basket domains. |
| **Gap** | Monolith with identifiable modules but significant coupling through shared database and combined service boundaries (catalog + basket in one service). |
| **Recommendation** | Execute Strangler Fig decomposition (see Decomposition Strategy). Priority 1: Extract Basket/Order service from `UnicornServiceImpl` to provide discrete APIs for agent access. Priority 2: Extract User service. Priority 3: Extract Product Catalog service. Use EKS (preferred) for each microservice. |
| **Evidence** | `src/main/java/com/monoToMicro/Application.java` (single entry point), `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` (combined catalog + basket), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (cross-domain JOIN), `database/create_tables.sql` (shared schema) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All communication is synchronous HTTP request-response. Every controller method blocks until the database query completes and returns a `ResponseEntity`. No message publishing, event-driven handlers, or async patterns exist. The event classes (`ReadUnicornsEvent`, `UnicornsReadEvent`, etc.) in the `core.events` package are synchronous method parameter/return wrappers — not actual messaging events. No SQS, SNS, or EventBridge SDK imports. |
| **Gap** | 100% synchronous — no async communication patterns at all. |
| **Recommendation** | Introduce EventBridge (preferred) for event-driven communication between extracted microservices. Key async candidates: basket add/remove events (publish to EventBridge for inventory tracking, analytics), user creation events (publish for welcome emails, onboarding). Avoid self-managed Kafka (per preferences). |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (sync POST/DELETE/GET), `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (sync GET), `src/main/java/com/monoToMicro/core/events/` (internal POJOs) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All operations are synchronous regardless of duration. Every controller endpoint blocks on database queries via MyBatis mapper calls. No background job frameworks, no async/polling patterns, no Step Functions. The `DataReplicationController.replicate()` method retrieves all baskets synchronously — a potentially long-running operation with no async handling. `UserRepositoryImpl.create()` uses a `synchronized` keyword, creating a blocking bottleneck. |
| **Gap** | All operations are synchronous with no async job processing for potentially long-running operations. |
| **Recommendation** | After extracting microservices, implement async patterns for operations like data replication (`DataReplicationController`) using Step Functions or EventBridge (preferred). For the basket operations that may grow with scale, use async processing with status polling. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` (sync bulk query), `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (synchronized create) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning. Endpoints use unversioned paths: `/unicorns` (GET), `/unicorns/basket` (POST/DELETE), `/unicorns/basket/{userUuid}` (GET), `/user` (POST), `/user/login` (POST), `/health/ping` (GET), `/health/ishealthy` (GET), `/health/dbping` (GET), `/data` (GET). No `/v1/` or `/v2/` URL prefixes. No `Accept-Version` headers. No OpenAPI specification. No changelog or API versioning documentation. |
| **Gap** | No versioning strategy — breaking changes would affect all consumers simultaneously. |
| **Recommendation** | Introduce URL-path versioning (e.g., `/v1/unicorns`, `/v1/basket`) during decomposition. Generate OpenAPI 3.0 specifications from the Spring controllers using Springdoc. This is prerequisite for both API Gateway (preferred) integration and agent tool discovery. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (@RequestMapping("/unicorns")), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (@RequestMapping("/unicorns/basket")), `src/main/java/com/monoToMicro/rest/controller/UserController.java` (@RequestMapping("/user")) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism. The application is a single monolith — service-to-service communication is internal Java method calls, not network calls. The only external endpoint reference is the database, accessed via the `MONO_TO_MICRO_DB_ENDPOINT` environment variable. No AWS Service Discovery, App Mesh, Istio, Consul, or service registry. No DNS-based discovery. |
| **Gap** | No service discovery. When decomposed into microservices, hard-coded endpoints will create deployment coupling. |
| **Recommendation** | When deploying microservices to EKS (preferred), use Kubernetes-native service discovery (ClusterIP services + DNS). For external-facing APIs, route through API Gateway (preferred). For service mesh capabilities, evaluate AWS App Mesh or Istio on EKS. |
| **Evidence** | `src/main/resources/application.properties` (MONO_TO_MICRO_DB_ENDPOINT env var), No service discovery configuration found |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 bucket definitions or unstructured data storage. AWS SDK S3 dependency (`aws-java-sdk-s3:1.11.567`) exists in `build.gradle` but no S3 usage found in source code — no `AmazonS3Client`, no `putObject`, no bucket references. The application stores only structured data in MySQL: product catalog (`unicorns` table), basket items (`unicorns_basket` table), and users (`unicorn_user` table). Product images are stored as name references only (`image` column is `varchar(256)` containing names like 'UnicornFloat'), not actual binary file storage. No Textract, document parsing, or file processing. |
| **Gap** | No managed object storage. Product image references suggest images may be served from local file system or CDN outside the application, but no S3 integration exists. |
| **Recommendation** | Store product images and any future unstructured content in S3. Integrate S3 with CloudFront for CDN delivery. After AI pathway adoption, S3 becomes the foundation for document storage that feeds RAG pipelines. |
| **Evidence** | `build.gradle` (aws-java-sdk-s3 dependency, unused), `database/create_tables.sql` (image column as varchar), `src/main/java/com/monoToMicro/core/model/Unicorn.java` (image field is String) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The repository pattern is consistently applied across all data access. All database queries flow through a clean, centralized architecture: Controllers → Service interfaces/implementations → Repository interfaces/implementations → MyBatis Mapper interfaces → MyBatis XML mapper SQL. `MyBatisConfig.java` creates all mappers centrally through a single `SqlSessionFactory` and `DataSource`. No direct JDBC calls or scattered database imports exist outside the repository layer. **Minor gap:** All 3 domain models (Unicorn, User, Health) share a single `DataSource` and `SqlSessionFactory`, and `UnicornRepository` handles both catalog and basket operations — conflating two bounded contexts. |
| **Gap** | Clean pattern but all mappers share one DataSource. UnicornRepository handles both catalog and basket — no per-domain data access separation. |
| **Recommendation** | During decomposition, split the single `UnicornRepository` into separate Catalog and Basket repositories with their own data sources. Each extracted microservice should own its data access layer. The existing MyBatis pattern is a strong foundation — maintain it in each new service. |
| **Evidence** | `src/main/java/com/monoToMicro/config/MyBatisConfig.java` (centralized mapper config), `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`, `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java`, `src/main/java/com/monoToMicro/core/repository/HealthRepositoryImpl.java` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MySQL connector version 8.0.11 is explicitly pinned in `build.gradle` (`mysql:mysql-connector-java:8.0.11`), indicating the application targets MySQL 8.0. However, no IaC exists to define or control the actual MySQL server engine version. The server-side engine version is unknown and unmanaged through code. MySQL 8.0.11 connector is outdated (released 2018) and may have known CVEs. The MySQL server version running on the EC2 instance could be any version including EOL releases (MySQL 5.6 EOL Feb 2021, MySQL 5.7 EOL Oct 2023). |
| **Gap** | Client connector pinned but server engine version uncontrolled. Connector version is outdated (2018). |
| **Recommendation** | After migrating to Aurora MySQL (preferred), the engine version is managed by AWS with automated minor version upgrades. Pin the Aurora engine version in Terraform (preferred) and upgrade the MySQL connector to the latest 8.x version. Aurora MySQL 3.x (MySQL 8.0 compatible) is the recommended target. |
| **Evidence** | `build.gradle` (mysql:mysql-connector-java:8.0.11), No IaC files defining database engine version |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL. `create_tables.sql` contains only standard DDL: `CREATE SCHEMA`, `CREATE TABLE`, and `INSERT` statements. MyBatis mapper XML files (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) use standard ANSI SQL: `SELECT`, `INSERT`, `DELETE`, `JOIN`. No MySQL-specific constructs beyond `INSERT IGNORE` (which is standard MySQL syntax, not proprietary PL/SQL). No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements anywhere in the repository. All business logic resides in the Java service layer (`UnicornServiceImpl`, `UserServiceImpl`). |
| **Gap** | None — this is best practice. All business logic is in the application layer. |
| **Recommendation** | Maintain this pattern during decomposition. The absence of stored procedures means database migration to Aurora MySQL (preferred) requires no stored procedure extraction or rewriting — only schema and data migration via DMS. |
| **Evidence** | `database/create_tables.sql` (DDL only), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (standard SQL), `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml`, `src/main/resources/com/monoToMicro/core/repository/mappers/HealthMapper.xml` |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration. No IaC exists to define logging infrastructure. The application uses only `System.out.println` for basic console output in `HealthController` ("No instance found"). Spring Boot Actuator is included as a dependency but provides only infrastructure metrics, not audit logging. No CloudWatch log groups, no log retention policies, no structured logging framework (Logback/Log4j2 configuration is absent). |
| **Gap** | No audit logging. No ability to trace actions or perform forensic analysis after incidents. |
| **Recommendation** | Define CloudTrail in Terraform (preferred) with log file validation and immutable storage (S3 with Object Lock). Add structured logging (Logback with JSON output) to the application for CloudWatch Logs integration. Replace `System.out.println` with SLF4J logger. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println only), No IaC or logging configuration found |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS keys or encryption configuration. No IaC exists to define encrypted data stores. The MySQL connection string in `application.properties` (`jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop?useUnicode=true&characterEncoding=UTF8&&serverTimezone=UTC`) shows no SSL/TLS parameters (`useSSL`, `requireSSL` are absent). No S3 bucket encryption, no EBS volume encryption, no RDS storage encryption configuration. |
| **Gap** | No encryption at rest for the database or any data store. No encryption in transit for database connections. |
| **Recommendation** | Aurora MySQL (preferred) supports encryption at rest with KMS by default. Enable `storage_encrypted = true` with a customer-managed KMS key in Terraform (preferred). Add SSL/TLS parameters to the JDBC connection string for encryption in transit. |
| **Evidence** | `src/main/resources/application.properties` (no SSL params in JDBC URL), No IaC with encryption configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Spring Security OAuth2 dependencies exist in `build.gradle` (`spring-boot-starter-security`, `spring-security-oauth2-autoconfigure`, `spring-security-jwt`, `spring-cloud-starter-oauth2`), and `ResourceServerConfig.java` uses `@EnableResourceServer`. However, the security configuration effectively disables all authentication: `http.requestMatchers().and().authorizeRequests().anyRequest().permitAll().and().cors()`. Every controller method uses `@PreAuthorize("permitAll()")`, allowing unauthenticated access to all endpoints including user creation and basket operations. `Application.java` ignores all OPTIONS requests for CORS workaround. |
| **Gap** | Security framework present but configured to permit everything. All API endpoints are open with no authentication. |
| **Recommendation** | Integrate with Amazon Cognito for OAuth2/JWT authentication. Configure API Gateway (preferred) with Cognito authorizer for all endpoints. Update `ResourceServerConfig` to validate JWT tokens. Remove `permitAll()` from controllers and apply role-based access control. |
| **Evidence** | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll()), `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (@PreAuthorize("permitAll()")), `build.gradle` (OAuth2 dependencies) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, Okta, Ping, or SAML/OIDC configuration. The application manages its own user table (`unicorn_user`) with basic create and email-lookup operations. `UserController.login()` performs email lookup only — `userRepository.getByEmail(email)` — with no password validation, no token issuance, and no session management. `CoreConfig.java` creates a `BCryptPasswordEncoder` bean but it's unused — no password field exists in the User model or database schema. |
| **Gap** | Application manages its own authentication entirely. No external IdP integration, no SSO, no password validation. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. Replace the custom `unicorn_user` table-based auth with Cognito user pools. Configure OIDC federation for SSO. This is a prerequisite for secure API Gateway (preferred) integration and agent-safe endpoint exposure. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/UserController.java` (email-only login), `src/main/java/com/monoToMicro/config/CoreConfig.java` (unused BCryptPasswordEncoder), `database/create_tables.sql` (unicorn_user table with no password column) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Database credentials are hardcoded in plaintext in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. These are committed to version control. The database endpoint uses an environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) which is a slight improvement, but credentials are fully exposed. No AWS Secrets Manager, no HashiCorp Vault, no encrypted configuration. No credential rotation mechanism. |
| **Gap** | Critical — credentials hardcoded in source code and committed to version control. No secrets management. |
| **Recommendation** | Immediately migrate credentials to AWS Secrets Manager. Use Spring Cloud AWS Secrets Manager integration or EKS secrets store CSI driver to inject secrets at runtime. Rotate the exposed credentials. Define secrets rotation in Terraform (preferred). Remove hardcoded credentials from `application.properties`. |
| **Evidence** | `src/main/resources/application.properties` (plaintext username and password) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No evidence of compute hardening or patching strategy. No SSM Patch Manager, AWS Inspector, or vulnerability scanning configuration. No hardened AMI references (CIS, Bottlerocket). No EC2 Image Builder pipelines. The EC2 instance running the application has no documented patching cadence. The application runs Java 8 and Spring Boot 2.1.x which have known CVEs. MySQL connector 8.0.11 is from 2018 and likely has known vulnerabilities. |
| **Gap** | No patching strategy, no vulnerability scanning, no hardened base images. Known-vulnerable dependency versions. |
| **Recommendation** | When containerizing on EKS (preferred), use Bottlerocket or Amazon Linux 2023 as base OS for EKS nodes. Use ECR image scanning to detect vulnerabilities in container images. Add AWS Inspector for runtime vulnerability assessment. Upgrade Java and Spring Boot versions to address known CVEs. |
| **Evidence** | `build.gradle` (Java 8, Spring Boot 2.1.x, MySQL connector 8.0.11 — all outdated), No patching or hardening configuration found |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning. No CI/CD pipeline exists to integrate security scanning into. No Dependabot configuration, no `.snyk` policy file, no SonarQube configuration, no `npm audit` or equivalent. No container image scanning (no containers exist). The `build.gradle` dependencies include multiple libraries from 2018-2019 with no evidence of vulnerability assessment. |
| **Gap** | No security scanning at any stage — no dependency scanning, no SAST, no container scanning. |
| **Recommendation** | When creating the CI/CD pipeline, integrate security scanning: (1) OWASP Dependency-Check or Snyk for Java dependency scanning in the Gradle build, (2) Semgrep or Amazon CodeGuru Reviewer for SAST, (3) ECR image scanning for container vulnerabilities, (4) security gates that block deployment on critical findings. |
| **Evidence** | `build.gradle` (outdated dependencies, no security plugins), No CI/CD or security scanning configuration found |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No X-Ray SDK, OpenTelemetry SDK, or tracing library in `build.gradle`. No trace ID propagation headers (`traceparent`, `X-Amzn-Trace-Id`) in controller or config code. No tracing configuration files. As a monolith, cross-service tracing is not yet needed, but application-level request tracing and performance profiling are absent. |
| **Gap** | No tracing — no ability to trace request flows, identify bottlenecks, or diagnose performance issues. |
| **Recommendation** | Add OpenTelemetry Java agent or AWS X-Ray SDK to the application. When deploying to EKS (preferred), use the ADOT (AWS Distro for OpenTelemetry) collector as a sidecar for automated trace collection. This is prerequisite for the Observability Agent quick win. |
| **Evidence** | `build.gradle` (no tracing dependencies), No tracing configuration found |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions. No CloudWatch alarms for latency, availability, or error rates. No error budget tracking. No SLO files or configurations. Spring Boot Actuator is included as a dependency but not configured with custom health indicators or SLO-aligned metrics. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for the Unicorn Shop. |
| **Recommendation** | Define SLOs for critical user journeys: product catalog browsing (p99 latency < 500ms, availability > 99.9%), basket operations (p99 latency < 300ms), user login (p99 latency < 200ms). Implement CloudWatch alarms for these SLOs. Track error budgets to prioritize reliability vs feature work. |
| **Evidence** | `build.gradle` (spring-boot-starter-actuator, unconfigured), No SLO definitions or CloudWatch alarms found |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics. No `cloudwatch.put_metric_data` or equivalent calls. The application uses only `System.out.println` for basic output. Spring Boot Actuator provides default JVM and HTTP metrics (request count, response times) but no custom business metrics are defined — no basket conversion rate, no items-per-basket, no user registration rate. |
| **Gap** | No business outcome metrics. Only default infrastructure metrics via Actuator (if configured). |
| **Recommendation** | Add Micrometer (Spring Boot's metrics facade) with CloudWatch exporter. Publish business metrics: basket additions/removals per minute, unique active users, catalog page views, basket-to-order conversion rate. These metrics drive informed modernization and decomposition decisions. |
| **Evidence** | `build.gradle` (spring-boot-starter-actuator), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting. No CloudWatch alarms (static or anomaly-based). No PagerDuty, OpsGenie, or on-call integration. No composite alarms. No error rate or latency monitoring. The application has no mechanism to detect or alert on degraded performance, increased error rates, or unusual traffic patterns. |
| **Gap** | No alerting — degraded service goes undetected until user complaints. |
| **Recommendation** | Configure CloudWatch alarms for error rates (5xx responses), latency (p99 > threshold), and database connection failures. Add anomaly detection on key metrics after establishing baselines. Integrate with SNS and PagerDuty/OpsGenie for on-call notifications. |
| **Evidence** | No IaC or monitoring configuration found |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy. No blue/green, canary, or rolling deployment configuration. No CodeDeploy, Helm releases, Argo Rollouts, or feature flags. No CI/CD pipeline exists to define deployment stages. Deployments are likely manual — copy the fat JAR to the EC2 instance and restart the process. The `bootJar { launchScript() }` in `build.gradle` creates a self-executing JAR for direct Linux service deployment. |
| **Gap** | Direct-to-production deployment with no staged rollout, no rollback capability, no traffic shifting. |
| **Recommendation** | When deploying to EKS (preferred), implement canary deployments with Argo Rollouts. Define progressive delivery stages: 5% canary → automated analysis → 25% → 50% → 100%. Use GitOps (preferred) with ArgoCD for declarative deployment management. Avoid manual deployments (per preferences). |
| **Evidence** | `build.gradle` (bootJar with launchScript — manual deployment artifact), No CI/CD or deployment configuration found |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No integration tests or automated tests of any kind. `spring-boot-starter-test` is declared in `build.gradle` as `testImplementation`, but no `src/test` directory exists in the repository. No test files found anywhere. No test containers, no Postman/Newman API tests, no contract tests, no end-to-end test pipelines. |
| **Gap** | Zero automated tests — no regression safety net for any changes or decomposition. |
| **Recommendation** | Before starting decomposition, establish a test foundation: (1) Integration tests for all API endpoints using Spring Boot Test with TestContainers for MySQL, (2) Contract tests for the API surface that becomes the service boundary, (3) End-to-end tests for critical user journeys (browse catalog → add to basket → checkout). Tests are essential before extracting services to prevent regression. |
| **Evidence** | `build.gradle` (spring-boot-starter-test declared but unused), No `src/test` directory or test files found |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation. No runbooks (markdown, YAML, JSON, or SSM Automation documents). No self-healing patterns. No Lambda-based remediation. No Step Functions for incident workflows. The `/health/ishealthy` and `/health/dbping` endpoints provide basic health checks but are not connected to any automated incident response. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation. |
| **Recommendation** | Create runbooks for common incidents: database connection failure (detected via `/health/dbping`), high latency, out-of-memory. Implement SSM Automation documents for EC2/EKS remediation. After deploying to EKS (preferred), configure pod restart policies and health probe-based auto-healing. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (basic health endpoints, not connected to automation) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership structure. No CODEOWNERS file. No per-service dashboards (no dashboards at all). No alarm ownership or team attribution. No SLO definitions with named owners. The repository has no documentation of who is responsible for monitoring, alerting, or operational health of the application. |
| **Gap** | No observability ownership — monitoring responsibility is undefined. |
| **Recommendation** | Add CODEOWNERS file with observability owners. As microservices are extracted, assign per-service observability ownership: each service team owns their dashboards, alarms, and SLOs. Create CloudWatch dashboards with team tags for the Unicorn Shop service. |
| **Evidence** | No CODEOWNERS file, no dashboards, no alarm configurations found |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging. No IaC exists to define tags on any AWS resource. No `default_tags` in Terraform provider (no Terraform exists). No tag enforcement via AWS Config rules or SCPs. No cost allocation tags. Resources cannot be attributed to the Unicorn Shop for cost tracking, ownership identification, or environment classification. |
| **Gap** | No tags on any resources — impossible to track costs, identify ownership, or distinguish environments. |
| **Recommendation** | Define a tagging standard (minimum: `Project`, `Environment`, `Owner`, `CostCenter`) and enforce it in Terraform (preferred) via `default_tags` on the AWS provider. Add AWS Config rule `required-tags` for enforcement. Tag all resources for the Unicorn Shop: `Project=UnicornShop`, `Environment=production`, `Owner=platform-team`. |
| **Evidence** | No IaC files found, no tagging configuration |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `build.gradle` | INF-Q1, INF-Q2, INF-Q11, APP-Q1, APP-Q2, APP-Q3, DATA-Q1, DATA-Q3, DATA-Q4, SEC-Q3, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q5, OPS-Q6 | Gradle build configuration — defines Java 8, Spring Boot 2.1.x, all dependencies (MySQL connector, AWS SDK, Spring Security OAuth2, MyBatis, Actuator), commented docker task |
| `src/main/resources/application.properties` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, SEC-Q2, SEC-Q5 | Application configuration — server port 8080, JDBC connection string with hardcoded credentials, environment variable for DB endpoint |
| `database/create_tables.sql` | INF-Q2, INF-Q8, APP-Q2, DATA-Q1, DATA-Q4, SEC-Q4 | MySQL DDL — `unishop` schema with 3 tables (unicorns, unicorns_basket, unicorn_user), seed data inserts, no stored procedures |
| `src/main/java/com/monoToMicro/Application.java` | INF-Q1, INF-Q5, APP-Q2, SEC-Q3 | Spring Boot entry point — `@SpringBootApplication`, CORS configuration, OPTIONS request ignoring |
| `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | INF-Q1, INF-Q6, INF-Q9, SEC-Q1, OPS-Q3, OPS-Q7 | Health endpoints — EC2MetadataUtils usage confirming EC2 deployment, System.out.println logging, basic health check endpoints |
| `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | APP-Q2, APP-Q3, APP-Q5, SEC-Q3 | Product catalog endpoint — GET /unicorns, @PreAuthorize("permitAll()"), synchronous response |
| `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | APP-Q2, APP-Q3, APP-Q4, APP-Q5 | Basket endpoints — POST/DELETE/GET /unicorns/basket, synchronous operations, no versioning |
| `src/main/java/com/monoToMicro/rest/controller/UserController.java` | APP-Q5, SEC-Q3, SEC-Q4 | User endpoints — POST /user (create), POST /user/login (email-only lookup, no password), @PreAuthorize("permitAll()") |
| `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | APP-Q4 | Data replication endpoint — GET /data, synchronous bulk basket query |
| `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | INF-Q3, APP-Q2, APP-Q3 | Business logic — combined catalog + basket service, synchronous operations, constructor injection |
| `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | INF-Q3, APP-Q2 | User business logic — user creation with UUID generation, email lookup |
| `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | APP-Q2, DATA-Q2 | Data access — MyBatis mapper delegation, @Transactional, exception handling with e.printStackTrace() |
| `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | APP-Q4, DATA-Q2 | Data access — synchronized create method, MyBatis mapper delegation |
| `src/main/java/com/monoToMicro/core/repository/HealthRepositoryImpl.java` | DATA-Q2 | Health data access — database reachability check via MyBatis mapper |
| `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | DATA-Q2 | Centralized MyBatis configuration — single SqlSessionFactory, single DataSource, all mappers registered centrally |
| `src/main/java/com/monoToMicro/config/MVCConfig.java` | INF-Q5 | MVC configuration — open CORS allowing all methods on all paths |
| `src/main/java/com/monoToMicro/config/CoreConfig.java` | SEC-Q4 | Core configuration — unused BCryptPasswordEncoder bean |
| `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | SEC-Q3 | Security configuration — @EnableResourceServer with permitAll() on all requests |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | APP-Q2, DATA-Q4 | MyBatis SQL — standard SELECT/INSERT/DELETE/JOIN, cross-domain JOIN between unicorns and unicorns_basket tables |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | DATA-Q4 | MyBatis SQL — standard INSERT and SELECT for user operations |
| `src/main/resources/com/monoToMicro/core/repository/mappers/HealthMapper.xml` | DATA-Q4 | MyBatis SQL — simple SELECT count(*) for database health check |
| `src/main/java/com/monoToMicro/core/model/Unicorn.java` | DATA-Q1 | Model — image field as String (name reference, not file storage) |
| `src/main/java/com/monoToMicro/core/events/` (package) | APP-Q3, INF-Q4 | Internal POJO event wrappers — not actual messaging events, used as method parameters/return values |
| `README.md` | Quick Agent Wins | Minimal documentation — redirect URL only, insufficient for RAG knowledge base |
