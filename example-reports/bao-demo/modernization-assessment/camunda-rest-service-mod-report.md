# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | camunda-rest-service |
| **Date** | 2025-07-15 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | camunda-c7, rest-api, integration |
| **Context** | REST API integration patterns from Camunda 7 BPMN processes including HTTP connectors and Java delegates. |
| **Overall Score** | 1.42 / 4.0 |

**Archetype Justification**: Application maintains persistent state via an embedded H2 file database (Camunda engine tables for process instances, tasks, variables, and history). Exposes Camunda REST API (`/engine-rest`) for process instance CRUD operations (start, complete, query). The embedded Camunda 7 BPMN engine manages stateful process lifecycle. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.18 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 1.83 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.00 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.00 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.42 / 4.0** | **❌ Not Present** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found — all infrastructure is manual (ClickOps). | Blocks reproducible deployments, disaster recovery, and all other modernization pathways. Triggers Move to Modern DevOps. |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — all deployments are manual. | No automated quality gates, no safe deployment mechanism. Triggers Move to Modern DevOps. |
| 3 | INF-Q1: Managed Compute | 1 | No AWS compute infrastructure defined — application runs as a local Spring Boot JAR. | No cloud-native compute; no scaling, no resilience. Triggers Move to Containers and Move to Cloud Native. |
| 4 | SEC-Q5: Secrets Management | 1 | Admin credentials hardcoded in `application.yaml` (`demo/demo`). No secrets management. | Critical security vulnerability — credentials exposed in version control. |
| 5 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith — single Spring Boot application with embedded Camunda engine, embedded H2 database, and all business logic in one deployable unit. | Limits independent scaling, deployment velocity, and team autonomy. Triggers Move to Cloud Native and Decomposition Strategy. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 >= 2 (scored 2). The Camunda engine provides a structured database with process instance, task, and variable data. The Camunda REST API (`/engine-rest`) exposes query endpoints for process instances, tasks, and history.
- **What it enables:** A natural language to Camunda REST API query agent that allows operators to query process state, find stuck instances, analyze task completion rates, and retrieve process variable values using conversational queries instead of raw REST API calls.
- **Additional steps:** Generate OpenAPI specification from the Camunda REST API endpoints. Configure agent access to the Camunda REST API with appropriate authentication.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` contains comprehensive documentation (400+ lines) covering all four REST call implementation patterns (Java Delegate, External Task, Connector, Script Task), error handling strategies (incidents, BPMN errors), transaction behavior, and configuration guidance.
- **What it enables:** A RAG-based knowledge agent that indexes the README documentation, BPMN process definitions, and DMN decision tables to answer developer questions about the workflow implementation, integration patterns, and Camunda best practices.
- **Additional steps:** Index `README.md`, `process.bpmn`, and `DecideOnPopularity.dmn` into a vector store. Configure chunking strategy appropriate for mixed Markdown and XML content.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 >= 2 (scored 3). Camunda 7 BPMN workflow orchestration is fully operational with a structured process definition (`process.bpmn`), DMN decision table, and external task pattern.
- **What it enables:** A workflow automation agent that monitors Camunda process instances via the REST API, detects stuck instances or failed jobs, triggers retries, escalates incidents, and provides process analytics (e.g., average cycle time, bottleneck identification).
- **Additional steps:** Deploy agent with access to Camunda REST API. Configure monitoring endpoints for process instance state queries and job management.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (<3), INF-Q1=1 (<3), APP-Q3=1 (<3) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (<3), no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (not <3) — no stored procedures or proprietary SQL. H2 is already open source. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (<3), DATA-Q3=1 (<3) — H2 embedded file database is not a managed service. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: No data processing workloads detected. Application queries GitHub API and evaluates results in BPMN workflow — no streaming, ETL, or analytics artifacts. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (<3), INF-Q11=1 (<3), OPS-Q5=1 (<3), OPS-Q6=2 (<3) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context mentions "REST API integration patterns from Camunda 7 BPMN processes" — no AI-related signal terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a tightly-coupled monolith (APP-Q2 = 1). A single Spring Boot application embeds the Camunda 7 BPMN engine, an H2 file database, Java delegates, Groovy script tasks, HTTP connectors, and DMN decision tables into one deployable JAR. The `SearchContributorService` (Node.js external task worker) is a loosely-coupled companion but depends entirely on the monolith's REST API via hardcoded `localhost:8080` endpoint.

**Compute Model Gaps (INF-Q1 = 1):**
No AWS compute infrastructure exists. The application runs as a local Spring Boot JAR with no containerization, no managed compute (ECS/EKS/Lambda/Fargate), and no cloud deployment artifacts.

**Communication Pattern Gaps (APP-Q3 = 1):**
All inter-service communication is synchronous HTTP. The Java delegate (`FindGitHubRepo.java`) uses synchronous `HttpClient.send()`. The Groovy script (`GetRepoLang.groovy`) uses synchronous `RESTClient.get()`. The external task worker (`service.js`) uses synchronous `node-fetch`. No messaging infrastructure (SQS, SNS, EventBridge) exists for cross-service state changes.

**Recommended Decomposition Approach:**
See the [Decomposition Strategy](#decomposition-strategy) section below. The Conditional/Adaptive approach is recommended: containerize the monolith first, replace H2 with a managed database, then selectively extract service tasks as independent microservices using the BPMN process as a natural decomposition boundary.

**Representative AWS Services:** Lambda, API Gateway, Step Functions, EventBridge, ECS/EKS, Aurora PostgreSQL
**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Saga

**AWS Prescriptive Guidance:**
- [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Decomposing Monoliths into Microservices](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model (INF-Q1 = 1):**
The application runs as a Spring Boot JAR executed locally with `java -jar`. No Dockerfile, no `docker-compose.yml`, no Kubernetes manifests, and no container orchestration configuration exist in the repository. The Node.js external task worker (`SearchContributorService`) is also executed directly via `node service.js` with no containerization.

**Container Readiness Indicators:**
- The Spring Boot application builds a self-contained JAR via `spring-boot-maven-plugin` — ready for containerization.
- Application configuration is in `application.yaml` with Spring externalization support — can be overridden via environment variables.
- The application binds to port 8080 (Spring Boot default) — straightforward port mapping.
- H2 file database dependency (`jdbc:h2:file:./camunda-h2-database`) must be replaced before containerization (file-based storage is not container-friendly).
- The Node.js worker has a simple `package.json` with two dependencies — straightforward to containerize.

**Recommended Container Orchestration Platform:**
ECS on Fargate for initial containerization (lower operational overhead than EKS for a single-service application). As the application evolves toward microservices decomposition, evaluate migration to EKS for richer orchestration capabilities.

**Migration Approach:** Lift-and-containerize first:
1. Create Dockerfiles for both `CamundaApplication` (Java 11 + Maven build) and `SearchContributorService` (Node.js).
2. Replace H2 file database with Aurora PostgreSQL (managed, container-friendly).
3. Create `docker-compose.yml` for local development.
4. Deploy to ECS Fargate with ECR for image storage.
5. Configure ECS service networking for communication between the Camunda application and the external task worker.

**Representative AWS Services:** ECS, Fargate, ECR, App Runner
**AWS Container Migration Guidance:**
- [Containerizing Applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-containers/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):**
The application uses an embedded H2 file database (`jdbc:h2:file:./camunda-h2-database`) configured in `application.yaml`. H2 is an embedded Java database intended for development and testing — it is not a production-grade database. The Camunda 7 engine stores all process instance state, task state, variables, and history in this database. Tests use an in-memory H2 variant (`jdbc:h2:mem:camunda-h2-database`).

**Engine Versions and EOL Status (DATA-Q3 = 1):**
H2 database version is inherited from the Spring Boot 2.5.4 BOM (not explicitly pinned). Spring Boot 2.5.x reached EOL in August 2022, and the transitive H2 version is correspondingly outdated.

**Data Access Patterns (DATA-Q2 = 2):**
Database access is managed entirely through the Camunda engine's persistence layer (MyBatis-based). Application code does not execute direct SQL queries — all data operations are via the Camunda Java API and REST API. This is favorable for migration as the data access layer is centralized within the Camunda engine.

**Recommended Managed Database Targets:**
- **Aurora PostgreSQL** — Camunda 7 officially supports PostgreSQL. Aurora provides Multi-AZ high availability, automated backups with PITR, and auto-scaling read replicas. Migration requires updating `spring.datasource.url` to point to Aurora and adding the PostgreSQL JDBC driver dependency.
- **RDS PostgreSQL** — Lower-cost alternative for non-production environments.

**Migration Tools:** AWS DMS is not needed for initial deployment (the H2 database contains development data only). For production migration from existing Camunda environments, use AWS DMS with the PostgreSQL endpoint.

**Representative AWS Services:** Aurora PostgreSQL, RDS PostgreSQL
**AWS Managed Database Migration Guidance:**
- [Migration to AWS Managed Databases](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero IaC coverage. No Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, no Kustomize manifests. All infrastructure (if any exists) would be manually created.

**Current CI/CD State (INF-Q11 = 1):**
No CI/CD pipeline exists. No GitHub Actions workflows (`.github/workflows/`), no GitLab CI (`.gitlab-ci.yml`), no Jenkinsfile, no `buildspec.yml`, no CodePipeline definitions. The Maven project builds locally via `mvn` but there is no automated build, test, or deploy pipeline.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy — there is no deployment automation at all. No canary, no blue/green, no rolling deployments.

**Testing Gaps (OPS-Q6 = 2):**
Integration tests exist in `WorkflowTest.java` (3 test methods testing BPMN process execution with real REST calls to GitHub API), but they are not run in any CI pipeline. The `SearchContributorService/package.json` has `"test": "echo \"Error: no test specified\" && exit 1"` — no tests at all for the Node.js worker.

**Recommended DevOps Toolchain:**
1. **IaC:** CDK (TypeScript or Java) or Terraform for AWS infrastructure provisioning (VPC, ECS, Aurora, ECR).
2. **CI/CD:** GitHub Actions for pipeline automation:
   - Build stage: Maven build + Docker image build
   - Test stage: Run `WorkflowTest` integration tests + add Node.js tests for `SearchContributorService`
   - Security stage: Dependabot for dependency scanning + Trivy for container image scanning
   - Deploy stage: ECS deployment with blue/green strategy via CodeDeploy
3. **Container Registry:** ECR for Docker image storage
4. **Deployment Strategy:** Start with rolling deployments, progress to blue/green via CodeDeploy

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK, ECR
**AWS DevOps Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-modernizing-applications/devops.html)

## Decomposition Strategy

APP-Q2 scored 1 (tightly-coupled monolith), triggering this section.

### Monolith Characteristics

The `CamundaApplication` is a single Spring Boot application that embeds:
- **Camunda 7 BPMN Engine** — Process execution, task management, history
- **H2 File Database** — All persistent state in a single embedded database
- **Java Delegate** (`FindGitHubRepo.java`) — Synchronous REST call to GitHub API
- **HTTP Connector** — Camunda connector for REST calls configured in BPMN XML
- **Groovy Script Task** — REST call to GitHub API for language detection
- **DMN Decision Table** (`DecideOnPopularity.dmn`) — Business rule evaluation
- **Camunda Webapp** — Admin UI, Tasklist, Cockpit
- **Camunda REST API** — Process management endpoints

The `SearchContributorService` is a Node.js external task worker that polls the monolith's REST API via hardcoded `http://localhost:8080/engine-rest`.

### Decomposition Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract service tasks as independent microservices while keeping the Camunda monolith running. Each BPMN service task is a natural extraction boundary. New service tasks are deployed as independent services; existing tasks are migrated over time. | When the team can sustain parallel development and the monolith has recognizable service task boundaries (it does). | **Medium to High** — 6-18 months. Each service task extraction is bounded. | ✅ **Recommended for this application.** The BPMN process provides natural decomposition boundaries — each service task can be extracted independently. |
| **Conditional / Adaptive** | Containerize the monolith as-is, replace H2 with Aurora PostgreSQL, then selectively extract high-value service tasks based on scaling needs. Not all tasks need to become services. | When capacity is limited and quick wins are needed before full decomposition. The application needs to be cloud-deployed before architectural changes. | **Low to Medium** — Containerization in 2-4 weeks, selective extraction over 3-12 months. | ✅ **Recommended as the first phase.** Containerize and deploy to AWS first, then decompose incrementally. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices, potentially migrating from Camunda 7 to Camunda 8 (Zeebe) or AWS Step Functions. | Almost never. Only if Camunda 7 engine is a hard constraint that cannot be evolved. | **Very High** — 12-24+ months. High risk. | ⚠️ **Recommended against.** The monolith is functional. Incremental approaches are safer. |

### Recommended Strategy: Conditional/Adaptive → Strangler Fig

**Phase 1 (Conditional/Adaptive — 4-6 weeks):**
1. Create Dockerfiles for `CamundaApplication` and `SearchContributorService`
2. Replace H2 with Aurora PostgreSQL (update `spring.datasource.url`)
3. Deploy to ECS Fargate
4. Configure service networking (replace `localhost:8080` with ECS service discovery)
5. Add CI/CD pipeline (GitHub Actions)

**Phase 2 (Strangler Fig — 3-12 months):**
1. Extract the Java Delegate (`FindGitHubRepo`) as an independent service (already has clear interface via `JavaDelegate`)
2. Extract the Groovy script task as a new external task worker or Lambda function
3. Extract the HTTP Connector logic as a dedicated integration service
4. Consider migrating the DMN decision table to a standalone decision service
5. Each extraction uses the Anti-corruption Layer pattern to isolate the new service from the Camunda engine's data model

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate each extracted service from the Camunda engine's data model and process variable contracts. | Every service task extraction — translate between Camunda process variables and the new service's domain model. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions if extracted services participate in multi-step workflows that previously shared the Camunda engine's transaction scope. | When extracting service tasks that have transactional dependencies (e.g., the "Search contributors" → "Search repo" → "Decide on popularity" chain). | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture all process state changes as events for audit and cross-service synchronization. | When extracted services need to react to process state changes or maintain a history of actions. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture (Ports and Adapters)** | Structure each new service with clear boundaries between business logic, external interfaces, and infrastructure adapters. | Every new service extracted from the monolith. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal | Assessment | Source |
|--------|--------|------------|--------|
| Module boundaries | BPMN service tasks provide natural boundaries (Java delegate, external task, connector, script task) | **Medium effort** — boundaries exist but are tightly coupled to Camunda engine internals | APP-Q2 finding |
| Data coupling | All state in single H2 database managed by Camunda engine | **Medium effort** — Camunda engine centralizes data access, but all process state is in one DB | DATA-Q2 finding |
| Stored procedures | None — all logic in application layer | **Low effort** — no database-embedded business logic to extract | DATA-Q4 finding |
| Communication patterns | All synchronous HTTP, no async messaging | **High effort** — need to introduce messaging for decoupled communication | APP-Q3 finding |
| CI/CD maturity | No pipeline exists | **High effort** — must build CI/CD from scratch to support multi-service deployment | INF-Q11 finding |
| Test coverage | 3 integration tests exist in `WorkflowTest.java`; no tests for Node.js worker | **Medium effort** — some regression safety exists but insufficient for safe extraction | OPS-Q6 finding |

**Calibrated Overall Effort Estimate:** Medium-High for Phase 1 + Phase 2 combined (8-14 months). Phase 1 alone is Low-Medium (4-6 weeks).

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS compute infrastructure is defined anywhere in the repository. The application runs as a Spring Boot JAR executed locally (`Application.java` with `@SpringBootApplication` and `SpringApplication.run()`). The Node.js external task worker (`service.js`) runs locally via `node service.js`. No Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources exist. No Dockerfile, no container definitions, no Kubernetes manifests. |
| **Gap** | All compute is local/manual with no cloud infrastructure. No managed container orchestration or serverless adoption. |
| **Recommendation** | Containerize both components (CamundaApplication and SearchContributorService) and deploy to ECS Fargate. Create Dockerfiles for Java 11 Spring Boot and Node.js runtimes. Use ECR for image storage. |
| **Evidence** | `CamundaApplication/src/main/java/com/example/workflow/Application.java`, `SearchContributorService/service.js`, absence of any IaC or container files in repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application uses an embedded H2 file database configured in `application.yaml` (`spring.datasource.url: jdbc:h2:file:./camunda-h2-database`). H2 is added as a dependency in `pom.xml` (`com.h2database:h2`). No managed database services (RDS, Aurora, DynamoDB) are provisioned. No IaC defines any database resources. |
| **Gap** | All database workloads run on an embedded H2 file database — not a production-grade database and not a managed service. No automated failover, no backups, no scaling. |
| **Recommendation** | Migrate from H2 to Aurora PostgreSQL (Camunda 7 supports PostgreSQL natively). Update `spring.datasource.url` to point to the Aurora endpoint. Add `postgresql` JDBC driver to `pom.xml`. Configure Multi-AZ for production resilience. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (datasource URL), `CamundaApplication/pom.xml` (H2 dependency). |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application uses Camunda 7 BPMN engine for workflow orchestration — a dedicated, structured workflow orchestration service. The process definition (`process.bpmn`) defines a multi-step workflow with service tasks (Java delegate, external task, HTTP connector, script task), business rule tasks (DMN), exclusive gateways, user tasks, event sub-processes, and async boundaries (`camunda:asyncBefore`, `camunda:asyncAfter`). The `DecideOnPopularity.dmn` provides externalized business rules. This is genuine workflow orchestration with error handling (BPMN errors, incidents), transaction management (async boundaries), and visual process management. However, Camunda 7 is self-managed (embedded in the application via `camunda-bpm-spring-boot-starter-rest` v7.16.0), not a managed AWS service (Step Functions, MWAA). |
| **Gap** | Workflow orchestration exists and is structured, but it is self-managed — the Camunda 7 engine is embedded in the application. This means the team must manage engine upgrades, database maintenance for process state, and engine configuration. |
| **Recommendation** | For the stateful-crud archetype, this is partial adoption (score 3). Consider evaluating AWS Step Functions for new workflows or migrating existing BPMN processes to Step Functions using ASL. Alternatively, deploy Camunda 7 as a managed container service on ECS to reduce the operational burden of the embedded engine. |
| **Evidence** | `CamundaApplication/src/main/resources/process.bpmn`, `CamundaApplication/src/main/resources/DecideOnPopularity.dmn`, `CamundaApplication/pom.xml` (Camunda dependencies). |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure exists. No SQS, SNS, EventBridge, MSK, Kinesis, or Amazon MQ resources. No self-managed Kafka or RabbitMQ. The Camunda external task pattern (used in `SearchContributorService/service.js`) provides a form of async task dispatch via REST API long-polling, but this is Camunda-internal task distribution — not cross-service messaging infrastructure. All REST calls to external APIs (GitHub) are synchronous HTTP. For the stateful-crud archetype, managed messaging should be used for cross-service state changes and notifications. |
| **Gap** | No messaging infrastructure for cross-service state changes. The application relies entirely on synchronous HTTP for all communication. Process state changes are communicated only through the Camunda engine's internal mechanisms (process variables, task completion). |
| **Recommendation** | Introduce SQS or EventBridge for cross-service state change notifications. When service tasks are extracted as independent microservices, use SQS for task dispatch instead of Camunda's REST API polling. Consider EventBridge for process event publishing (process started, task completed, process error). |
| **Evidence** | `SearchContributorService/service.js` (REST API polling at `http://localhost:8080/engine-rest`), absence of any messaging infrastructure in repository. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists. No IaC defines any networking resources. The application runs on `localhost:8080` with the Camunda REST API and web applications exposed directly. Admin credentials are hardcoded as `demo/demo` in `application.yaml`. |
| **Gap** | Services are deployed with no network isolation, no VPC, no security groups. The Camunda REST API and admin interfaces are exposed without any network-level protection. |
| **Recommendation** | Deploy into a VPC with private subnets. Place the Camunda application in a private subnet behind an ALB. Use security groups to restrict ingress to the ALB only. Use VPC endpoints for AWS service access. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (hardcoded admin credentials, no network config), absence of any IaC or network configuration files. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or managed entry point exists. The Camunda REST API is exposed directly on Spring Boot's embedded Tomcat server (port 8080) via `camunda-bpm-spring-boot-starter-rest`. The external task worker connects directly to `http://localhost:8080/engine-rest`. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, no authentication at the gateway level, no request validation, no SSL termination. |
| **Recommendation** | Deploy an Application Load Balancer (ALB) in front of the Camunda application. Configure path-based routing for the REST API (`/engine-rest/*`) and web applications (`/camunda/*`). Add API Gateway for external-facing endpoints with throttling and OAuth2/JWT authorization. |
| **Evidence** | `SearchContributorService/service.js` (`baseUrl: "http://localhost:8080/engine-rest"`), `CamundaApplication/pom.xml` (`camunda-bpm-spring-boot-starter-rest`). |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No IaC defines any scaling policies, ASG configurations, or capacity settings. The application runs as a single instance with no scaling capability. |
| **Gap** | No auto-scaling — all capacity is statically provisioned (single local instance). |
| **Recommendation** | After containerization to ECS Fargate, configure Application Auto Scaling with target tracking on CPU and memory utilization. Set min/max task counts based on expected workload. |
| **Evidence** | Absence of any IaC, scaling configuration, or ASG definitions in the repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. The H2 file database (`camunda-h2-database`) has no backup strategy. No `aws_backup_plan`, no S3 versioning, no backup retention settings. Process instance state and history data stored in H2 would be lost in case of failure. |
| **Gap** | No backup configuration found. Data loss risk is critical — all process state and history in the embedded H2 database has no backup or recovery mechanism. |
| **Recommendation** | After migrating to Aurora PostgreSQL, enable automated backups with a retention period of at least 7 days. Enable Point-in-Time Recovery (PITR). Configure cross-region backup replication for critical process data. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (H2 file database with no backup config), absence of any backup configuration files. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Single instance deployment with no redundancy. The application runs as a single Spring Boot process with an embedded H2 file database. No multi-AZ configuration, no load balancing, no failover. A single-point-of-failure at every layer (compute, database, network). |
| **Gap** | All resources in a single instance with no AZ configuration. Any failure takes down the entire workflow engine and all running process instances. |
| **Recommendation** | After migrating to ECS Fargate + Aurora PostgreSQL, deploy across 2+ Availability Zones. Configure Aurora Multi-AZ for database failover. Run at least 2 ECS tasks across AZs behind an ALB with cross-zone load balancing. |
| **Evidence** | Single `Application.java` entry point, single H2 database instance, no multi-AZ or redundancy configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code files exist in the repository. No Terraform (`.tf`), no CloudFormation (`.cfn.yaml`), no CDK (`cdk.json`), no Helm charts (`Chart.yaml`), no Kustomize (`kustomization.yaml`), no Ansible playbooks. The entire infrastructure footprint is zero — the application only has source code and Maven/npm build configuration. |
| **Gap** | No IaC — all infrastructure is manual (ClickOps) or non-existent. This is the most fundamental blocker for cloud deployment and modernization. |
| **Recommendation** | Create IaC for all required infrastructure: VPC, subnets, security groups, ECS cluster, Fargate service definitions, Aurora PostgreSQL, ALB, ECR repositories, CloudWatch alarms, and IAM roles. Use CDK (Java, given the team's skill set) or Terraform. |
| **Evidence** | Complete absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or Ansible files in the repository file listing. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists. No GitHub Actions (`.github/workflows/`), no GitLab CI (`.gitlab-ci.yml`), no Jenkinsfile, no `buildspec.yml`, no `appspec.yml`, no CodePipeline definitions in IaC. The Maven project (`pom.xml`) supports local builds, but there is no automated build, test, or deploy pipeline. The `SearchContributorService/package.json` has a placeholder test script (`"test": "echo \"Error: no test specified\" && exit 1"`). |
| **Gap** | No CI/CD — all deployments are manual. No automated build, no automated test execution, no automated deployment, no quality gates. |
| **Recommendation** | Create a GitHub Actions workflow with: (1) Build stage — Maven build for CamundaApplication, npm install for SearchContributorService; (2) Test stage — Run `WorkflowTest` integration tests; (3) Security stage — Dependency vulnerability scanning; (4) Deploy stage — Docker image build, push to ECR, ECS service update. |
| **Evidence** | Absence of `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml` in repository. `SearchContributorService/package.json` test script is a no-op. |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is Java 11 (`maven-compiler-plugin` source/target = 11 in `pom.xml`). Java has first-class AWS SDK coverage, broad cloud-native tooling, and mature framework ecosystems (Spring Boot, Quarkus, Micronaut). Secondary languages: JavaScript/Node.js (`SearchContributorService/service.js` with `camunda-external-task-client-js` and `node-fetch`) — also a tier-1 language for AWS. Groovy (`GetRepoLang.groovy`) used for script tasks — runs on the JVM and benefits from Java's ecosystem. |
| **Gap** | No gap — Java 11 and JavaScript are both tier-1 languages for AWS cloud-native development. |
| **Recommendation** | Consider upgrading from Java 11 to Java 17 or 21 (LTS) for improved performance, security patches, and modern language features. Java 11 is still supported but Java 17+ provides better container awareness and GC improvements. |
| **Evidence** | `CamundaApplication/pom.xml` (maven-compiler-plugin source=11, target=11), `SearchContributorService/package.json` (Node.js), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application is a tightly-coupled monolith. A single Spring Boot application (`CamundaApplication`) contains all components: embedded Camunda 7 BPMN engine, embedded H2 database, Java delegate (`FindGitHubRepo.java`), HTTP connector configuration (in BPMN XML), Groovy script tasks, DMN decision table, Camunda web applications (Tasklist, Cockpit, Admin), and REST API. All logic is in a single `pom.xml` build, single `Application.java` entry point, and single deployable JAR. The `SearchContributorService` is a separate Node.js process but depends entirely on the monolith's REST API (`http://localhost:8080/engine-rest`). There are no clear module boundaries — Java delegates, scripts, and connectors are all orchestrated by the embedded engine with shared process variables and a single database. |
| **Gap** | Tightly-coupled monolith with no clear module boundaries, pervasive shared state (all process variables and task state in single H2 database), and all business logic in a single deployable unit. |
| **Recommendation** | Implement the Decomposition Strategy outlined in the report. Phase 1: Containerize the monolith as-is. Phase 2: Use Strangler Fig pattern to extract service tasks (Java delegate, external task, script task) as independent microservices, using the BPMN process definition as a natural decomposition boundary. |
| **Evidence** | `CamundaApplication/pom.xml` (single build), `CamundaApplication/src/main/java/com/example/workflow/Application.java` (single entry point), `CamundaApplication/src/main/resources/process.bpmn` (all tasks in one process), `CamundaApplication/src/main/resources/application.yaml` (single H2 database for all state). |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous HTTP. For the stateful-crud archetype, this scores 1 (all communication synchronous HTTP with no async patterns). Specific evidence: (1) Java delegate `FindGitHubRepo.java` uses synchronous `HttpClient.newHttpClient()` with `client.send()` — blocking call to GitHub API. (2) Groovy script `GetRepoLang.groovy` uses synchronous `RESTClient.get()` — blocking call to GitHub API. (3) Node.js external task worker `service.js` uses `node-fetch` with `await fetch(url)` — synchronous within the async handler. (4) HTTP Connector in BPMN XML uses Camunda's synchronous `http-connector`. No SQS, SNS, EventBridge, or any messaging for cross-service state propagation. The Camunda external task pattern provides task-level async boundaries (process execution continues independently of task workers), but the actual REST calls within handlers are all synchronous. |
| **Gap** | All communication synchronous HTTP with no async patterns. No messaging infrastructure for cross-service state changes. Process state changes are communicated only through synchronous Camunda REST API interactions. |
| **Recommendation** | Introduce managed messaging (SQS or EventBridge) for cross-service state propagation. When extracting service tasks as independent microservices, use async messaging for fire-and-forget operations and event notification. Maintain synchronous communication only for request-response patterns that require immediate results. |
| **Evidence** | `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (synchronous HttpClient), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (synchronous RESTClient), `SearchContributorService/service.js` (synchronous node-fetch), `CamundaApplication/src/main/resources/process.bpmn` (http-connector). |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Camunda 7 BPMN engine handles long-running processes by design. The workflow (`process.bpmn`) spans multiple service tasks with explicit async boundaries: the start event has `camunda:asyncBefore="true"`, the "Search for contributors" external task has `camunda:asyncAfter="true"`, and the "Get repo languages" script task has `camunda:asyncAfter="true"`. Process instances persist across multiple task executions via the H2 database. The external task pattern (`SearchContributorService`) naturally supports long-running operations — the task worker fetches, processes, and completes tasks independently of the BPMN engine's execution thread. This is genuine async long-running process handling at the workflow level. However, individual REST calls within handlers (e.g., GitHub API calls in `FindGitHubRepo.java`) are synchronous with no timeout management or circuit-breaking. For the stateful-crud archetype, this is partial adoption (most long-running operations async via Camunda; some blocking calls remain). |
| **Gap** | Long-running workflow orchestration is well-handled by Camunda's async boundaries, but individual REST calls within service tasks are synchronous with no timeout or retry configuration. A slow GitHub API response could block a task execution thread. |
| **Recommendation** | Add HTTP timeout configuration to all REST clients (HttpClient in Java delegate, RESTClient in Groovy script, node-fetch in external task worker). Implement circuit-breaker patterns for external API calls. Consider using Camunda's retry mechanism for transient failures. |
| **Evidence** | `CamundaApplication/src/main/resources/process.bpmn` (async boundaries: `camunda:asyncBefore`, `camunda:asyncAfter`), `SearchContributorService/service.js` (external task pattern with task completion), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (synchronous HTTP calls without timeout). |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The Camunda REST API is exposed at `/engine-rest` (Camunda's built-in path) with no version prefix. The external task worker hardcodes `http://localhost:8080/engine-rest` in `service.js`. GitHub API URLs are hardcoded without version paths in `FindGitHubRepo.java` (`https://api.github.com/repos/...`) and `GetRepoLang.groovy`. No `/v1/` or `/v2/` URL patterns. No version headers. No changelog files. |
| **Gap** | No versioning — API changes would break all consumers simultaneously. The Camunda REST API version is implicitly tied to the Camunda engine version (7.16.0), but there is no explicit versioning strategy for the application's own API surface. |
| **Recommendation** | If custom API endpoints are added beyond the Camunda REST API, adopt a URL-path versioning strategy (`/api/v1/...`). For the Camunda REST API, document the engine version and REST API version in a service manifest. |
| **Evidence** | `SearchContributorService/service.js` (hardcoded `http://localhost:8080/engine-rest`), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (unversioned GitHub API URLs), absence of any versioning patterns. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All service endpoints are hardcoded. The external task worker (`service.js`) hardcodes the Camunda REST API endpoint: `baseUrl: "http://localhost:8080/engine-rest"`. The Java delegate (`FindGitHubRepo.java`) hardcodes the GitHub API URL: `"https://api.github.com/repos/" + repoOwner + "/" + repoName`. The Groovy script (`GetRepoLang.groovy`) hardcodes: `new RESTClient("https://api.github.com/")`. The HTTP Connector in BPMN XML hardcodes: `https://api.github.com/repos/#{repoOwner}/#{repoName}/community/profile`. No service registry, no dynamic discovery, no DNS-based service discovery, not even environment variable-based endpoint configuration. |
| **Gap** | All service endpoints hard-coded in application code and BPMN XML. This creates tight deployment coupling — any endpoint change requires code modifications and redeployment. |
| **Recommendation** | Externalize all service endpoints to environment variables as a first step. Then implement AWS Cloud Map or ECS Service Discovery for inter-service communication. Use environment variable injection in ECS task definitions to configure the Camunda REST API endpoint for the external task worker. |
| **Evidence** | `SearchContributorService/service.js` (`baseUrl: "http://localhost:8080/engine-rest"`), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (hardcoded GitHub URL), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (hardcoded GitHub URL), `CamundaApplication/src/main/resources/process.bpmn` (hardcoded connector URL). |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage or managed object storage exists. No S3 buckets, no Textract, no document parsing libraries. The application only deals with structured JSON responses from the GitHub REST API. Form definitions (`.form` files in `static/forms/`) are static assets bundled in the application, not managed documents. No document management or unstructured data processing capabilities. |
| **Gap** | No managed object storage. While the application doesn't currently handle documents or unstructured data, there is no S3 or object storage infrastructure that could support future unstructured data needs. |
| **Recommendation** | If unstructured data storage is needed in the future (e.g., storing BPMN process documentation, audit artifacts, or report outputs), create an S3 bucket with appropriate lifecycle policies. For the current application, this is a low-priority gap. |
| **Evidence** | Absence of any S3, Textract, or document storage references in IaC or source code. `CamundaApplication/src/main/resources/static/forms/` contains only static form definitions. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database access is managed entirely through the Camunda 7 engine's persistence layer. The application code does NOT execute direct SQL queries — all process state, task state, variables, and history are managed through the Camunda Java API and REST API. Spring Boot auto-configuration handles the JDBC connection setup via `spring-boot-starter-jdbc`. This provides implicit centralization: one persistence layer (Camunda engine) manages all database interactions. However, there is no explicit unified data access layer pattern in the application code — no repository/DAO pattern, no data access abstraction beyond what Camunda provides. External data (GitHub API responses) is accessed via scattered HTTP calls in different languages (Java, Groovy, JavaScript) with no consistent data access pattern. |
| **Gap** | Repository/DAO pattern exists implicitly (Camunda engine) but is inconsistent across the codebase. External API access is scattered across Java delegates, Groovy scripts, and JavaScript workers with different HTTP clients and error handling patterns. |
| **Recommendation** | Create a unified HTTP client abstraction for external API calls (GitHub API). Standardize on a single HTTP client library with consistent error handling, retry logic, and timeout configuration. When extracting services, each service should have its own data access layer following the repository pattern. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (Camunda engine manages H2 access), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (Java HttpClient for GitHub), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (Groovy RESTClient for GitHub), `SearchContributorService/service.js` (node-fetch for GitHub). |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The H2 database engine version is NOT explicitly pinned in `pom.xml` — it is inherited from the Spring Boot 2.5.4 BOM (via `spring-boot-dependencies`). Spring Boot 2.5.4 was released in August 2021 and the Spring Boot 2.5.x line reached EOL in August 2022. The transitive H2 version is approximately 1.4.200 (from the 2.5.4 BOM), which is outdated. No production database engine is defined — H2 is an embedded development database, not a production engine. No version update procedure is documented. The Camunda 7 BOM (`camunda-bom:7.15.0`) and Spring Boot starters (`7.16.0`) have a version mismatch that could introduce compatibility issues. |
| **Gap** | No database engine version pinning. Using an embedded H2 database inherited from an EOL Spring Boot BOM. No production database, no version lifecycle management, no update procedure. |
| **Recommendation** | Migrate to Aurora PostgreSQL with explicitly pinned engine version (e.g., `aurora-postgresql 15.x`). Pin the PostgreSQL JDBC driver version in `pom.xml`. Document a version update procedure covering downtime windows, rollback, and risk acknowledgment. Upgrade Spring Boot from 2.5.4 (EOL) to a supported version (3.x). |
| **Evidence** | `CamundaApplication/pom.xml` (Spring Boot 2.5.4 BOM, H2 dependency without version pin, Camunda BOM 7.15.0 vs starter 7.16.0 mismatch). |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic is in the application layer: Java delegate (`FindGitHubRepo.java`), Groovy script (`GetRepoLang.groovy`), JavaScript external task worker (`service.js`), DMN decision table (`DecideOnPopularity.dmn`), and BPMN process definition (`process.bpmn`). The Camunda engine manages its own database schema (auto-generated by `camunda-bpm-spring-boot-starter`) but does not use stored procedures — all engine logic is in Java. No `.sql` migration files, no `CREATE PROCEDURE`, no `CREATE TRIGGER`, no `CREATE FUNCTION` in the repository. |
| **Gap** | No gap — all business logic is in the application layer with no database-embedded logic. |
| **Recommendation** | Maintain this pattern. When migrating to Aurora PostgreSQL, the absence of stored procedures makes the migration significantly simpler — only schema DDL and data migration are needed, with no logic extraction required. |
| **Evidence** | `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (business logic in Java), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (logic in Groovy), `SearchContributorService/service.js` (logic in JavaScript), `CamundaApplication/src/main/resources/DecideOnPopularity.dmn` (business rules in DMN). Absence of any `.sql` files or stored procedure definitions. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configured. No IaC defines any logging infrastructure. The application has basic logging configuration in `application.yaml` for Camunda HTTP connector debugging (`org.camunda.bpm.connect: DEBUG`, `org.apache.http.headers: DEBUG`, `org.apache.http.wire: DEBUG`), but these are debug-level connector logs, not audit trails. A `logback-test.xml` exists in test resources for test logging. Camunda 7 has a built-in history service, but it is not configured for external audit log export. |
| **Gap** | No CloudTrail or equivalent audit logging. No immutable log storage. No audit trail for who initiated processes, completed tasks, or accessed the REST API. |
| **Recommendation** | Enable CloudTrail for AWS API audit logging. Configure Camunda history level to FULL and export history events to CloudWatch Logs or S3. Enable log file validation and S3 Object Lock for immutable audit storage. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (debug logging only), `CamundaApplication/src/test/resources/logback-test.xml` (test logging), absence of CloudTrail or audit logging configuration. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured. The H2 file database (`camunda-h2-database`) stores data as an unencrypted file on the local filesystem. No KMS keys, no encrypted storage volumes, no encryption configuration in any IaC (no IaC exists). Process variables — which may contain sensitive data — are stored in plaintext in the H2 database file. |
| **Gap** | No encryption at rest configured. Process instance data, task variables, and history stored in plaintext on disk. |
| **Recommendation** | After migrating to Aurora PostgreSQL, enable encryption at rest with a customer-managed KMS key. Configure KMS key rotation. Encrypt all data stores (Aurora, S3 for logs/artifacts, EBS volumes). |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (`jdbc:h2:file:./camunda-h2-database` — unencrypted file), absence of any KMS or encryption configuration. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-request authentication with OAuth2/JWT. The Camunda REST API and web applications use basic Camunda identity service authentication with hardcoded credentials (`id: demo`, `password: demo`) configured in `application.yaml`. The Camunda REST API endpoints at `/engine-rest/*` do not require authentication by default — they are open. The external task worker (`service.js`) connects to the REST API without any authentication credentials. No OAuth2 flows, no Bearer token validation, no API Gateway authorizers. |
| **Gap** | No API authentication — the Camunda REST API endpoints are open with no authentication required. Admin credentials are hardcoded demo values. |
| **Recommendation** | Implement OAuth2/JWT authentication on the Camunda REST API. Use Amazon Cognito as the identity provider. Configure API Gateway with a JWT authorizer in front of the Camunda REST API. Update the external task worker to obtain and send Bearer tokens. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (hardcoded `demo/demo` credentials), `SearchContributorService/service.js` (no auth headers in REST API config), absence of OAuth2/JWT configuration. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. The application uses Camunda 7's built-in identity service with a single hardcoded admin user (`id: demo`, `password: demo` in `application.yaml`). No Cognito, no Okta, no OIDC, no SAML configuration. No federation. User tasks in the BPMN process (`Activity_0scbww2`, `Activity_1vv3176`, `Activity_0hbvr03`) are assigned using `camunda:assignee="#{processOwner}"` — a process variable, not an IdP-backed identity. |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. Single hardcoded user with demo credentials. |
| **Recommendation** | Integrate Camunda 7 with Amazon Cognito using the LDAP or OIDC identity service plugin. Configure SSO for the Camunda web applications (Tasklist, Cockpit, Admin). Map Cognito groups to Camunda authorization roles. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (hardcoded admin user), `CamundaApplication/src/main/resources/process.bpmn` (user task assignments via process variable). |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Secrets are hardcoded in version-controlled configuration files. The Camunda admin user credentials (`id: demo`, `password: demo`) are hardcoded in `application.yaml` — this file is committed to the Git repository. No AWS Secrets Manager, no HashiCorp Vault, no environment variable substitution for secrets. No `.env` files with secrets (but also no secrets management of any kind). The GitHub API calls use no authentication tokens (anonymous access), but if API keys were needed, there is no mechanism to inject them securely. |
| **Gap** | Secrets hardcoded in code committed to version control. Critical security vulnerability — anyone with repository access can see admin credentials. |
| **Recommendation** | Move all secrets to AWS Secrets Manager. Replace hardcoded credentials in `application.yaml` with environment variable references (`${CAMUNDA_ADMIN_PASSWORD}`). Configure ECS task definitions to inject secrets from Secrets Manager. Enable automatic rotation for database credentials. |
| **Evidence** | `CamundaApplication/src/main/resources/application.yaml` (plaintext `camunda.bpm.admin-user.id: demo`, `password: demo`). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources are defined, so no hardening or patching strategy exists. No SSM Patch Manager, no vulnerability scanning (Inspector, Snyk), no hardened base images. The application runs on whatever JDK and OS the developer has locally. Spring Boot 2.5.4 (EOL August 2022) contains known CVEs. Camunda BOM 7.15.0 and starters 7.16.0 are also outdated with potential vulnerabilities. |
| **Gap** | No evidence of patching strategy. No vulnerability scanning. Dependencies include EOL Spring Boot 2.5.4 with known security issues. |
| **Recommendation** | After containerization, use a hardened base image (Amazon Corretto 11 on Amazon Linux 2023 or Bottlerocket). Enable ECR image scanning. Add dependency vulnerability scanning (Dependabot, Snyk) to the CI/CD pipeline. Upgrade Spring Boot from 2.5.4 to a supported 3.x version. |
| **Evidence** | `CamundaApplication/pom.xml` (Spring Boot 2.5.4, Camunda 7.15.0/7.16.0), absence of any vulnerability scanning or patching configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are configured. No Dependabot (`/.github/dependabot.yml`), no Snyk (`.snyk`), no SonarQube, no CodeGuru Reviewer. No CI/CD pipeline exists, so there is no pipeline to integrate security scanning into. No `npm audit` for the Node.js worker, no OWASP dependency-check for the Maven project. |
| **Gap** | No security scanning tools configured. No automated vulnerability detection for dependencies, source code, or container images. Pipeline has no security validation step (no pipeline exists). |
| **Recommendation** | Create a CI/CD pipeline (see INF-Q11) and integrate: (1) Dependabot for automated dependency updates and vulnerability alerts; (2) `mvn dependency-check:check` (OWASP) for Java dependency scanning; (3) `npm audit` for Node.js dependency scanning; (4) Trivy or ECR scanning for container image vulnerabilities; (5) SonarQube or Semgrep for SAST. Configure security gates to block deployments on critical findings. |
| **Evidence** | Absence of `.github/dependabot.yml`, `.snyk`, `sonar-project.properties`, or any security scanning configuration in the repository. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry SDK in dependency manifests (`pom.xml`, `package.json`). No X-Ray instrumentation. No `traceparent` or `X-Amzn-Trace-Id` header propagation in any source code. The application makes outbound REST calls to the GitHub API from three different components (Java delegate, Groovy script, Node.js worker) with no trace context propagation between them. Camunda 7 does not natively support OpenTelemetry or X-Ray. |
| **Gap** | No distributed tracing. Debugging failures across the Camunda engine, Java delegate, external task worker, and GitHub API calls is guesswork. No ability to trace a process instance's execution across all service task implementations. |
| **Recommendation** | Add OpenTelemetry Java Agent for the Spring Boot application (auto-instruments HTTP clients and JDBC). Add OpenTelemetry Node.js SDK to the external task worker. Configure X-Ray as the trace exporter. Propagate trace IDs through Camunda process variables to maintain trace continuity across async task boundaries. |
| **Evidence** | `CamundaApplication/pom.xml` (no OpenTelemetry or X-Ray dependencies), `SearchContributorService/package.json` (no tracing dependencies), absence of any tracing configuration. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No CloudWatch alarms on latency, error rates, or availability. No error budget tracking. No SLO configuration files. The application has no definition of acceptable service levels for process execution time, task completion latency, or API response times. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. No way to measure whether the workflow engine is meeting user expectations or degrading. |
| **Recommendation** | Define SLOs for critical process journeys: (1) Process instance start-to-completion latency (e.g., p99 < 30 seconds for the GitHub repo checker process); (2) External task completion latency; (3) Camunda REST API availability (e.g., 99.9%). Create CloudWatch alarms to monitor these SLOs. |
| **Evidence** | Absence of any SLO definition files, CloudWatch alarm configurations, or monitoring dashboards in the repository. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No `cloudwatch.put_metric_data` calls, no custom dashboards, no business KPI tracking. The application uses `System.out.println()` for basic output in `FindGitHubRepo.java` and `println()` in the Groovy script — console output, not structured metrics. No tracking of process throughput, task completion rates, error rates by service task, or GitHub API call success rates. |
| **Gap** | No custom metrics — only basic console logging. No visibility into business outcomes (how many repos are rated popular vs unpopular, what is the GitHub API error rate, how long do process instances take). |
| **Recommendation** | Instrument business metrics using CloudWatch custom metrics or EMF (Embedded Metric Format): (1) Process instances started per hour; (2) Process instances completed (popular vs unpopular outcome); (3) Service task error rates by implementation type (Java delegate, external task, connector, script); (4) GitHub API call latency and error rates. |
| **Evidence** | `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (`System.out.println(response.body())`), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (`println(path)`, `println(response.contentAsString)`). |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch alarms (static or anomaly-based), no PagerDuty/OpsGenie integration, no composite alarms. No error rate monitoring, no latency monitoring, no process instance failure detection. |
| **Gap** | No alerting configured. Failures in the workflow engine, stuck process instances, or GitHub API outages would go undetected until manually noticed. |
| **Recommendation** | After deploying to AWS, configure CloudWatch alarms for: (1) ECS task health (unhealthy task count > 0); (2) Aurora database connections and CPU; (3) Application error log patterns (Camunda incidents); (4) Process instance stuck detection (instances in ACTIVE state > threshold duration). Use CloudWatch Anomaly Detection on error rates and latency. |
| **Evidence** | Absence of any alerting, monitoring, or alarm configuration in the repository. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. No CI/CD pipeline, no CodeDeploy configuration, no Helm canary, no Argo Rollouts, no feature flags. The application has no deployment automation — it is started locally via `SpringApplication.run()`. The README instructs users to "Download the project and open the Camunda Spring Boot application in your IDE using Java 11" and "Start the application." |
| **Gap** | Direct-to-production deployment with no staged rollout. No deployment automation exists — the application is manually started in a local IDE. |
| **Recommendation** | Implement automated deployments via the CI/CD pipeline (see INF-Q11). Start with rolling deployments on ECS, then progress to blue/green deployments via CodeDeploy for zero-downtime releases. For the Camunda engine specifically, consider running old and new engine versions in parallel during deployment to avoid interrupting running process instances. |
| **Evidence** | `README.md` (manual startup instructions), absence of any deployment configuration, CI/CD pipeline, or deployment strategy files. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Integration tests exist in `WorkflowTest.java` with 3 test methods: (1) `shouldExecuteScriptTask` — tests the Groovy script task execution against the real GitHub API, verifying process variables are set correctly; (2) `testConnectorCallSuccesscully` — tests the HTTP Connector service task against the real GitHub API, verifying `healthPercentage` variable; (3) `testConnectorCallBpmnError` — tests BPMN error handling when `healthPercentage < 70`. These are genuine integration tests using `@SpringBootTest` with a real Camunda engine and real REST calls to GitHub. They test actual BPMN process execution end-to-end. However: (1) Tests are NOT run in any CI pipeline (no CI/CD exists); (2) The `SearchContributorService` has no tests at all (`"test": "echo \"Error: no test specified\" && exit 1"`); (3) No test for the Java Delegate (`FindGitHubRepo.java`); (4) Tests depend on live GitHub API availability. |
| **Gap** | Some integration tests exist but not run consistently in CI. No tests for the external task worker or Java delegate. Tests depend on external API availability (fragile). |
| **Recommendation** | Add integration tests to a CI pipeline. Add tests for `FindGitHubRepo.java` (Java delegate) and `SearchContributorService/service.js` (external task worker). Use WireMock or MockServer to stub GitHub API responses for deterministic testing. Add the test stage to the GitHub Actions pipeline. |
| **Evidence** | `CamundaApplication/src/test/java/com/example/workflow/WorkflowTest.java` (3 integration test methods), `CamundaApplication/src/test/resources/application.yaml` (H2 in-memory for tests), `SearchContributorService/package.json` (no test script). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response workflows, runbooks, or self-healing automation exists. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files (markdown, YAML, JSON). The BPMN process has an error-handling sub-process (`Activity_1kavuhs` — event sub-process triggered by BPMN errors that routes to a "Look at Error" user task), but this is process-level error handling, not infrastructure incident response. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No automated remediation for common failures (Camunda engine issues, database connectivity, GitHub API outages). |
| **Recommendation** | Create runbooks for common incident scenarios: (1) Camunda engine unresponsive — ECS task restart; (2) Database connectivity failure — Aurora failover check; (3) Stuck process instances — automated retry of failed jobs; (4) GitHub API rate limiting — circuit breaker activation. Implement SSM Automation documents for automated remediation. |
| **Evidence** | `CamundaApplication/src/main/resources/process.bpmn` (BPMN error handling sub-process — process-level, not ops-level), absence of any runbook or incident automation files. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No per-service dashboards, no alarm owners, no CODEOWNERS file, no team attribution on monitoring resources. No SLO definitions with team accountability. The application has no observability configuration beyond debug-level HTTP connector logging. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented (actually non-existent). No dashboards, no alarms, no team accountability for service health. |
| **Recommendation** | Create a CODEOWNERS file with team ownership of the Camunda application and external task worker. Define per-service dashboards in CloudWatch: (1) Camunda engine dashboard (process throughput, active instances, failed jobs, task completion rates); (2) External task worker dashboard (fetch latency, completion rates, error rates). Assign alarm owners to each alarm. |
| **Evidence** | Absence of CODEOWNERS file, dashboard definitions, alarm configurations, or team attribution in the repository. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists. No IaC defines any resources, so no tags can be applied. No `default_tags` in Terraform provider, no `tags` on resources, no tag policies, no AWS Config rules for tag enforcement. |
| **Gap** | No tags found on resources — no cost allocation, no ownership attribution, no environment identification. (No AWS resources exist yet.) |
| **Recommendation** | When creating IaC, define a mandatory tagging standard with at minimum: `Environment` (dev/staging/prod), `Team` (owning team), `Service` (camunda-rest-service), `CostCenter` (cost allocation), and `ManagedBy` (terraform/cdk). Use `default_tags` in Terraform provider or CDK `Tags.of()` for consistent application. Enable AWS Config rule `required-tags` for enforcement. |
| **Evidence** | Absence of any IaC files or AWS resource definitions in the repository. |

## Learning Materials

The following learning resources are mapped to the 4 triggered modernization pathways:

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
| `CamundaApplication/pom.xml` | INF-Q1, INF-Q2, INF-Q3, INF-Q11, APP-Q1, APP-Q2, DATA-Q3, DATA-Q4, SEC-Q6, OPS-Q1 | Maven build configuration; Spring Boot 2.5.4, Camunda 7.15/7.16, H2 dependency, Java 11 compiler, Groovy 3.0.8. |
| `CamundaApplication/src/main/resources/application.yaml` | INF-Q2, INF-Q4, INF-Q5, INF-Q8, APP-Q2, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5 | H2 file database URL, hardcoded admin credentials (demo/demo), HTTP connector debug logging. |
| `CamundaApplication/src/main/java/com/example/workflow/Application.java` | INF-Q1, APP-Q2 | Spring Boot entry point (`@SpringBootApplication`, `main()`) — single deployable application. |
| `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` | INF-Q4, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q2, DATA-Q4, OPS-Q3 | Java delegate with synchronous HttpClient REST calls to GitHub API; BPMN error handling. |
| `CamundaApplication/src/main/resources/process.bpmn` | INF-Q3, INF-Q4, APP-Q2, APP-Q3, APP-Q4, APP-Q6, OPS-Q7 | BPMN process definition with service tasks, external tasks, connectors, script tasks, DMN integration, async boundaries, and error handling sub-process. |
| `CamundaApplication/src/main/resources/DecideOnPopularity.dmn` | INF-Q3, DATA-Q4 | DMN decision table for popularity evaluation based on forks and contributors. |
| `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` | APP-Q1, APP-Q3, APP-Q6, DATA-Q2, DATA-Q4, OPS-Q3 | Groovy script task with synchronous RESTClient calls to GitHub API for language detection. |
| `SearchContributorService/service.js` | INF-Q1, INF-Q4, INF-Q6, APP-Q2, APP-Q3, APP-Q5, APP-Q6, DATA-Q2 | Node.js external task worker; hardcoded localhost:8080 endpoint; synchronous node-fetch; Camunda REST API polling. |
| `SearchContributorService/package.json` | INF-Q11, APP-Q1, OPS-Q1, OPS-Q6 | Node.js dependencies (camunda-external-task-client-js, node-fetch); placeholder test script. |
| `CamundaApplication/src/test/java/com/example/workflow/WorkflowTest.java` | OPS-Q6 | 3 integration test methods testing BPMN process execution with real GitHub API calls. |
| `CamundaApplication/src/test/resources/application.yaml` | INF-Q2, OPS-Q6 | H2 in-memory database configuration for tests. |
| `CamundaApplication/src/test/resources/logback-test.xml` | SEC-Q1 | Test logging configuration. |
| `CamundaApplication/src/main/resources/static/forms/*.form` | DATA-Q1 | Static form definitions for Camunda Tasklist (startForm, popularRepoForm, unpopularRepoForm). |
| `README.md` | OPS-Q5, Quick Agent Wins | Comprehensive documentation covering all four REST call implementation patterns and usage instructions. |
| `bpmn-analysis.json` | APP-Q2 | BPMN task analysis with AI migration scores for 8 tasks across the process. |
| `.gitignore` | SEC-Q5 | Excludes build artifacts, IDE files, and node_modules — but does not exclude secrets (application.yaml is committed). |
