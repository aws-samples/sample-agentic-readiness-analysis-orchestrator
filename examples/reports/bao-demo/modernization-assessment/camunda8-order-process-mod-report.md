# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | camunda8-order-process |
| **Date** | 2025-07-15 |
| **Repo Type** | application |
| **Service Archetype** | orchestrator (auto-detected) |
| **Priority** | P0 |
| **Tags** | camunda-c8, orders, zeebe |
| **Context** | Camunda 8 order processing with Zeebe job workers, BPMN error events, timer escalation patterns, and event subprocesses. |
| **Overall Score** | 1.37 / 4.0 |

**Archetype Justification**: Repository contains BPMN process definitions orchestrating multiple service tasks, user tasks, and business rule tasks via Camunda 8/Zeebe with parallel gateways, timer events, error boundary events, and message-based event subprocesses. The Java application provides Zeebe job workers that execute within this orchestrated workflow.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 1.83 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.00 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **1.37 / 4.0** | **❌ Not Present** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q5: Secrets Management | 1 | Zeebe client credentials (clientId, clientSecret) hardcoded in `application.yml` and committed to version control in plaintext. | Critical security vulnerability — credentials exposed in Git history. Immediate remediation required before any production deployment. |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC files found. No Terraform, CloudFormation, CDK, Helm, or any infrastructure definitions. | All infrastructure is undefined or manually configured. Blocks reproducible deployments, disaster recovery, and environment consistency. Triggers Move to Modern DevOps pathway. |
| 3 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline definitions found. README instructs running the Worker class from an IDE manually. | No automated build, test, or deploy process. Blocks continuous delivery and safe releases. Triggers Move to Modern DevOps pathway. |
| 4 | APP-Q2: Monolith vs Microservices | 1 | Single `Worker.java` class contains all job worker handlers (`DoWork`, `DoLongWork`) in one `@SpringBootApplication` with no module boundaries. | Tightly-coupled monolith prevents independent scaling and deployment of worker types. Triggers Move to Cloud Native pathway and Decomposition Strategy. |
| 5 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no ECS, EKS, Lambda, EC2, or any deployment target. Application is run from an IDE. | No production-ready compute hosting. Blocks all operational maturity. Triggers Move to Containers pathway. |

---

## Quick Agent Wins

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` contains substantial content describing BPMN patterns (error events, timer events, event subprocesses), setup instructions, and process details. `BPMN_DMN/process-five.bpmn` and `BPMN_DMN/decide-on-assignee.dmn` provide structured process definitions. `bpmn-analysis.json` provides task-level analysis with scoring and migration recommendations.
- **What it enables:** A RAG-based knowledge agent that indexes README documentation, BPMN/DMN model definitions, and the BPMN analysis JSON to answer developer questions about the order processing workflow patterns, setup procedures, and process design decisions.
- **Additional steps:** Generate embeddings from README.md, BPMN XML, and bpmn-analysis.json. Deploy a vector store (e.g., OpenSearch with knn plugin or pgvector). Build a retrieval chain using Amazon Bedrock or LangChain.
- **Effort:** Medium — documentation corpus exists but requires indexing infrastructure and retrieval chain setup.

### Workflow Automation Agent

- **Prerequisite:** Workflow orchestration in place (INF-Q3 = 3). Camunda 8/Zeebe provides a mature workflow orchestration surface with the Zeebe REST API and gRPC API for process instance management, job completion, message correlation, and incident resolution.
- **What it enables:** An agent that monitors Zeebe workflow instances, checks process instance status, manages incidents (retry or resolve), correlates messages (e.g., triggering the `CancelMessage` event subprocess), and provides natural language interaction with the running process engine.
- **Additional steps:** The Zeebe API endpoint must be exposed to the agent. Agent needs appropriate API credentials (replace hardcoded credentials with Secrets Manager). Configure agent tool definitions mapping to Zeebe REST API operations.
- **Effort:** Medium — Zeebe API surface exists but agent needs credential management and tool configuration.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (primary), INF-Q1=1, APP-Q3=2, APP-Q4=2 — monolith worker with no managed compute and limited async patterns. |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (primary), no container definitions found. Compute is undefined (not Lambda/Fargate/ECS). |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 — no stored procedures or proprietary SQL. No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | No databases exist in the application (self-managed or otherwise). Low INF-Q2 score reflects absence of data persistence, not self-managed databases. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected. INF-Q4=2 reflects missing AWS messaging for the orchestrator, not analytics needs. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (primary), INF-Q11=1 (primary), OPS-Q5=1, OPS-Q6=1 — zero IaC, no CI/CD, no deployment strategy, no tests. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context mentions workflow orchestration patterns only. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a single Spring Boot monolith (`Worker.java`) containing all Zeebe job worker handlers in one class. APP-Q2 scored 1 — tightly coupled with no module boundaries. All worker logic (`DoWork`, `DoLongWork`) shares a single `@SpringBootApplication` entry point and a single `application.yml` configuration.

**Compute Model Gaps:**
INF-Q1 scored 1 — no compute infrastructure is defined. The application is designed to be run from an IDE (per README). No ECS, EKS, Lambda, or EC2 definitions exist. No Dockerfile or Kubernetes manifests.

**Communication Pattern Gaps:**
- APP-Q3 scored 2 — the Zeebe job worker model provides some async behavior (workers poll for jobs), but within workers, processing is synchronous. The `DoLongWork` handler blocks with `TimeUnit.MINUTES.sleep()`. No SQS, SNS, or EventBridge messaging.
- APP-Q4 scored 2 — long-running operations (up to 6+ minutes) are handled via blocking sleep. The BPMN process has timer boundary events for escalation, but the worker itself has no checkpointing or async callback.

**Recommended Decomposition Approach:**
See the [Decomposition Strategy](#decomposition-strategy) section below for detailed approach options, patterns, and effort estimates.

**Representative AWS Services:**
- **Compute:** Lambda (for short-lived workers), ECS/Fargate (for long-running workers), EKS (if container orchestration complexity is warranted)
- **Orchestration:** AWS Step Functions (as potential complement or replacement for Camunda 8 SaaS orchestration for AWS-native workflows)
- **Messaging:** Amazon EventBridge, SQS, SNS for event-driven decoupling between worker services
- **API:** API Gateway for service entry points

**Recommended Patterns:**
- **Strangler Fig** — Incrementally extract worker types (DoWork, DoLongWork) into independent services while the Camunda 8 BPMN process continues to orchestrate them via Zeebe.
- **Anti-corruption Layer** — Isolate new AWS-native services from Camunda/Zeebe coupling.
- **Event Sourcing** — Consider for order state management as workers are decomposed.
- **Saga Pattern** — Already partially implemented via the BPMN process; formalize with Step Functions or EventBridge for AWS-native orchestration.

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
INF-Q1 scored 1. No compute infrastructure is defined. The Spring Boot application (`Worker.java`) is run manually from an IDE per the README. No Dockerfile, no docker-compose.yml, no Kubernetes manifests, and no Helm charts were found in the repository.

**Container Readiness Indicators:**
- The application is a standard Spring Boot JAR (packaging=jar in `pom.xml`) — straightforward to containerize.
- Dependencies are managed via Maven (`pom.xml`) with only 2 dependencies: `spring-zeebe-starter:8.1.14` and `commons-io:2.8.0`.
- Configuration is externalized in `application.yml` — can be replaced with environment variables or mounted config maps.
- No local file system dependencies detected — the worker is stateless.

**Recommended Container Orchestration Platform:**
ECS with Fargate is recommended as the simplest path for a small number of Zeebe worker containers. EKS is an option if the team plans to manage multiple services or requires more sophisticated orchestration.

**Representative AWS Services:**
- **Container Registry:** Amazon ECR for storing Docker images
- **Orchestration:** Amazon ECS (Fargate launch type) for managed container hosting
- **Networking:** ALB or VPC Lattice for service-to-service communication (if multiple worker services are deployed)

**Migration Approach:**
1. **Lift-and-containerize:** Create a Dockerfile for the Spring Boot application. Build and push to ECR.
2. **Deploy to ECS Fargate:** Define an ECS task definition and service. Configure Zeebe connection via environment variables (replacing hardcoded credentials).
3. **Add auto-scaling:** Configure ECS Service Auto Scaling based on Zeebe job backlog metrics or CPU utilization.
4. **Iterate:** Once containerized, extract individual worker types into separate containers as part of the Move to Cloud Native pathway.

**AWS Container Migration Guidance:**
- [Containerizing applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/containers-provision-environment/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:**
INF-Q10 scored 1. Zero IaC files found in the repository. No Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible files. All infrastructure — if any exists beyond the Camunda 8 SaaS cluster — is manually configured or undefined.

**Current CI/CD State:**
INF-Q11 scored 1. No CI/CD pipeline definitions found. No `.github/workflows/`, no `Jenkinsfile`, no `buildspec.yml`, no `appspec.yml`. The README instructs developers to "run the Worker class" from an IDE, indicating fully manual execution.

**Deployment Strategy Gaps:**
OPS-Q5 scored 1. No deployment strategy — no blue/green, no canary, no rolling deployments. Manual IDE execution is the only documented approach.

**Testing Gaps:**
OPS-Q6 scored 1. No `src/test/` directory exists. No unit tests, no integration tests, no automated tests of any kind. Zero test coverage creates high regression risk during any modernization changes.

**Recommended DevOps Toolchain:**
1. **IaC:** AWS CDK (Java — aligns with existing Java stack) or Terraform for defining ECS/Fargate infrastructure, networking, and IAM roles.
2. **CI/CD Pipeline:** GitHub Actions or AWS CodePipeline with CodeBuild for automated build, test, and deploy.
3. **Container Build:** CodeBuild with Docker support for building and pushing images to ECR.
4. **Deployment:** AWS CodeDeploy with ECS blue/green deployment for zero-downtime releases.
5. **Testing:** JUnit 5 for unit tests, Testcontainers for integration tests with Zeebe.
6. **Security Scanning:** Dependabot or Snyk for dependency vulnerability scanning. Amazon ECR image scanning for container images.

**Implementation Priority:**
1. **Immediate:** Move secrets out of `application.yml` to AWS Secrets Manager or environment variables.
2. **Week 1-2:** Create a Dockerfile and basic CI pipeline (build + test).
3. **Week 2-4:** Define IaC for compute (ECS Fargate), networking (VPC, subnets, security groups), and IAM.
4. **Week 4-6:** Add integration tests using Testcontainers with embedded Zeebe. Configure deployment pipeline with staging environment.
5. **Week 6-8:** Implement blue/green or canary deployment strategy via CodeDeploy.

**AWS DevOps Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/welcome.html)

---

## Decomposition Strategy

> **Condition:** APP-Q2 = 1 (< 3) — application is a tightly-coupled monolith worker.

### Decomposition Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract Zeebe job worker types (`DoWork`, `DoLongWork`) into independent microservices while the BPMN process continues to orchestrate via Zeebe. Each worker type becomes a separate deployable unit. | The BPMN process already defines clear task type boundaries (`DoWork`, `DoLongWork`). These map directly to natural service boundaries. | **Medium** — 3-6 months. Each worker extraction is bounded. BPMN process is unchanged. | ✅ **Recommended.** The Camunda 8 BPMN process already provides the orchestration layer, making Strangler Fig extraction straightforward — each Zeebe task type maps to an independent worker service. |
| **Conditional / Adaptive** | Containerize the monolith worker as-is first (lift-and-containerize), then selectively extract high-value worker types based on scaling needs. Not all workers may need to be separate services. | Team has limited capacity. Quick win needed (containerization) before architectural change. The `DoLongWork` worker has different resource and scaling characteristics than `DoWork`. | **Low to Medium** — Containerization in 1-2 weeks, selective extraction over 2-4 months. | ✅ **Recommended when capacity is constrained.** Containerize first for immediate operational improvement, then extract `DoLongWork` as a separate service due to its blocking sleep pattern and different scaling profile. |
| **Big-Bang Rewrite** | Rewrite all workers as separate microservices from scratch. | Not recommended — the existing codebase is small (~80 lines of Worker.java) and functional. | **Low** for this small codebase, but **unnecessary**. | ⚠️ **Not recommended.** The codebase is too small to justify a full rewrite. Strangler Fig or Conditional approaches achieve the same outcome with less risk. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new worker services from the Camunda/Zeebe SDK coupling. Each new service wraps the Zeebe client interaction in an adapter layer, keeping business logic independent. | Every worker extraction — place an ACL between the new service's business logic and the Zeebe job worker SDK interface. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage the multi-step order processing workflow across decomposed services. | Already implemented — the BPMN process IS the saga orchestration. Camunda 8/Zeebe coordinates the Decide on Assignee → Validate Data → Update External Audit → Process Data workflow with error handling and compensating actions (Cancel event subprocess). | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture order processing events for audit trails and temporal queries. | When order state tracking is added. Currently the BPMN process variables carry state, but there is no persistent event store. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture (Ports and Adapters)** | Structure each new worker service with clear boundaries between business logic (core), Zeebe interface (port), and infrastructure adapters (AWS SDK, database). | Every new worker service — ensures testability and portability. Critical given current zero test coverage (OPS-Q6=1). | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation

| Factor | Signal | Assessment | Source |
|--------|--------|------------|--------|
| Module boundaries | ✅ LOW effort | BPMN task types (`DoWork`, `DoLongWork`) map to natural service boundaries. Each job type can be independently deployed. | APP-Q2, `process-five.bpmn` |
| Data coupling | ✅ LOW effort | No database, no shared state between workers. Workers are stateless — they read job variables and complete/fail jobs. | DATA-Q2, `Worker.java` |
| Stored procedures | ✅ LOW effort | No database procedures. All business logic in application code and BPMN/DMN models. | DATA-Q4 |
| Communication patterns | 🟡 MEDIUM effort | Zeebe provides async job dispatch, but no AWS messaging layer exists. New services will need SQS/EventBridge for non-Zeebe communication. | APP-Q3, INF-Q4 |
| CI/CD maturity | ❌ HIGH effort | No CI/CD pipeline exists. Must build pipeline before safe decomposition can proceed. | INF-Q11 |
| Test coverage | ❌ HIGH effort | No tests at all — zero coverage. Must establish testing baseline before extracting services to prevent regressions. | OPS-Q6 |

**Calibrated Overall Estimate:** The decomposition itself is **low effort** due to the small codebase and clear task-type boundaries in the BPMN model. However, the **prerequisite infrastructure** (CI/CD, containers, IaC, tests) represents **high effort** and must be built first. Recommended sequence: (1) Secrets remediation → (2) Containerize as-is → (3) Build CI/CD pipeline → (4) Add tests → (5) Extract worker types into independent services.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in the repository. No IaC files (Terraform, CloudFormation, CDK), no Dockerfiles, no Kubernetes manifests, and no Helm charts were found. The application is a Spring Boot JAR designed to be run locally from an IDE — the README states "load the project in your IDE of choice and run the `Worker` class." The application connects to Camunda 8 SaaS (cloud-hosted Zeebe cluster), but the worker process itself has no defined compute hosting. |
| **Gap** | All compute on raw EC2 or on-premises with no managed services — in this case, no compute hosting is defined at all. The application has no deployment target. |
| **Recommendation** | Containerize the Spring Boot application with a Dockerfile and deploy to Amazon ECS with Fargate launch type. This provides managed compute with auto-scaling, eliminates server management, and establishes a foundation for the Move to Containers and Move to Cloud Native pathways. |
| **Evidence** | `pom.xml` (JAR packaging), `README.md` ("run the Worker class"), absence of Dockerfile/docker-compose.yml/Kubernetes manifests in repository scan. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database is used by the application. No database-related IaC resources (`aws_rds_*`, `aws_dynamodb_*`), no database connection strings (beyond Zeebe cluster), no database drivers in `pom.xml`, no ORM frameworks, and no SQL migration files. The application is stateless — it reads process variables from Zeebe job activations (`job.getVariablesAsMap()`) and completes/fails jobs. State management is entirely delegated to the Camunda 8/Zeebe engine. |
| **Gap** | For an order processing application, the complete absence of persistent data storage is a concern. Order data, processing history, and audit trails have no persistent store outside of Zeebe's internal state. |
| **Recommendation** | Evaluate whether the application needs its own persistent data store for order processing state, audit trails, or reporting. If so, adopt a managed database service (Aurora PostgreSQL or DynamoDB) defined in IaC. If the Camunda 8 SaaS cluster handles all persistence needs, document this architectural decision explicitly. |
| **Evidence** | `pom.xml` (no database drivers — only `spring-zeebe-starter` and `commons-io`), `Worker.java` (no database imports or connection code), `application.yml` (only Zeebe cluster connection), repository-wide scan (no `.sql` files, no migration directories). |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | *Archetype calibration: orchestrator.* Camunda 8/Zeebe is a dedicated workflow orchestration service actively in use. The BPMN process (`process-five.bpmn`) orchestrates a multi-step "Process Data Example" workflow with: parallel gateways (concurrent Validate Data + Update External Audit paths), exclusive gateways (decision-based routing by complexity), timer boundary events (1-min non-interrupting SLA warnings, 5-min interrupting escalation), error boundary events (BPMN error propagation from service tasks to terminate events), message-based event subprocesses (cancel message correlation), and a DMN business rule task (`decide-on-assignee.dmn`). This is a mature orchestration implementation with advanced BPMN patterns. |
| **Gap** | Orchestration is on Camunda 8 SaaS (third-party platform), not an AWS-native service. While functional and mature, this creates a dependency on a non-AWS orchestration platform. Partial adoption — the primary workflow is orchestrated but auxiliary flows (if any) are in code. |
| **Recommendation** | The current Camunda 8/Zeebe orchestration is well-designed with advanced patterns. If migrating to AWS-native services is a goal, evaluate AWS Step Functions as a potential complement for new workflows. For the existing BPMN process, Camunda 8 SaaS provides mature orchestration that would be complex to replicate in Step Functions due to the advanced BPMN patterns (timer events, error boundary events, event subprocesses). Maintain current orchestration while building AWS-native infrastructure around it. |
| **Evidence** | `BPMN_DMN/process-five.bpmn` (process definition with parallel gateways, timer events, error events, event subprocess), `BPMN_DMN/decide-on-assignee.dmn` (DMN decision table), `Worker.java` (@JobWorker annotations, Zeebe client interactions), `application.yml` (Zeebe cloud cluster connection). |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | *Archetype calibration: orchestrator.* The Camunda 8/Zeebe system provides an internal async job dispatch model — Zeebe job workers poll for available tasks and process them asynchronously. The `@JobWorker` annotations in `Worker.java` handle `DoWork` and `DoLongWork` job types dispatched by the Zeebe engine. The Zeebe client uses async completion patterns (`.send().exceptionally()`). The BPMN process also includes a message event subprocess with `CancelMessage` message correlation — a form of async messaging within the Zeebe ecosystem. However, no AWS managed messaging infrastructure exists — no SQS, SNS, EventBridge, MSK, Kinesis, or Amazon MQ definitions in IaC or code. No self-managed messaging brokers either. |
| **Gap** | For an orchestrator archetype, managed messaging (EventBridge, SQS, MSK) is expected for fan-out and decoupling. The Zeebe job dispatch model provides async behavior within the Camunda ecosystem, but there is no AWS messaging layer for cross-service communication outside of Zeebe. |
| **Recommendation** | Introduce Amazon EventBridge or SQS for event-driven communication between worker services, especially as workers are decomposed into independent services. EventBridge is recommended for order processing events (order created, order processed, SLA warning) that other systems may need to consume. For the Zeebe job worker pattern specifically, consider whether Zeebe's internal messaging is sufficient or whether AWS-native messaging would reduce platform coupling. |
| **Evidence** | `Worker.java` (`@JobWorker` annotations for async job dispatch, `.send().exceptionally()` async completion), `process-five.bpmn` (`CancelMessage` message event), `pom.xml` (no SQS/SNS/EventBridge SDK dependencies), `application.yml` (only Zeebe connection — no AWS messaging endpoints), repository scan (no `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*` in IaC). |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, or security group definitions found. No IaC files exist in the repository. The application connects to Camunda 8 SaaS over the public internet using OAuth2 client credentials (`clientId`/`clientSecret`) defined in `application.yml`. No network segmentation, no private subnets, no security group rules. |
| **Gap** | Services deployed in the default VPC or to public subnets without isolation. In this case, no network infrastructure is defined at all — the application has no deployment target with network controls. |
| **Recommendation** | Define a VPC with private subnets, security groups, and NAT gateways in IaC. Deploy the containerized worker in private subnets with outbound-only internet access (for Camunda 8 SaaS communication). Use VPC endpoints for AWS service access. Restrict security group egress to only the Camunda 8 SaaS cluster endpoint. |
| **Evidence** | Repository-wide scan (no `.tf`, `.cfn.yaml`, CDK, or Helm files found), `application.yml` (Zeebe cloud connection with `region: bru-2` indicating public internet connectivity to Camunda SaaS). |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any inbound entry point is defined. The application is a Zeebe job worker — it initiates outbound connections to the Zeebe cluster to poll for jobs. It has no inbound API surface and does not expose HTTP endpoints. |
| **Gap** | Services exposed directly with no gateway or load balancer. While the worker pattern does not inherently require an inbound entry point, there is no health check endpoint, no management API, and no way to inspect worker status externally. |
| **Recommendation** | Add a Spring Boot Actuator health endpoint for container health checks (required for ECS/EKS health monitoring). If the application evolves to expose APIs (e.g., for manual job triggering or status queries), add API Gateway with throttling and authentication. For pure workers, an ALB is not required — ECS service health checks via Actuator are sufficient. |
| **Evidence** | `Worker.java` (no `@RestController`, no `@RequestMapping`, no HTTP endpoint annotations), `pom.xml` (no spring-boot-starter-web or spring-boot-starter-actuator dependencies), repository scan (no API Gateway or ALB IaC definitions). |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No compute infrastructure is defined, so there is nothing to scale. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or ECS service scaling policies. No Lambda concurrency limits. The application runs as a single worker process with no horizontal scaling capability. |
| **Gap** | No auto-scaling — all capacity is statically provisioned (in this case, a single manually-run process). The worker cannot scale in response to Zeebe job backlog increases. |
| **Recommendation** | When containerized on ECS Fargate, configure ECS Service Auto Scaling with target tracking on CPU utilization or a custom metric based on Zeebe job backlog depth. For the `DoLongWork` handler (which blocks for minutes), consider separate scaling policies tuned to job queue depth rather than CPU. |
| **Evidence** | Repository-wide scan (no auto-scaling IaC resources), `README.md` (single worker execution from IDE). |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. The application has no data stores to back up — no databases, no S3 buckets, no persistent volumes. State is managed by the Camunda 8 SaaS platform (which handles its own backups). However, the BPMN/DMN model files and application configuration are only in the Git repository with no documented backup or recovery strategy. |
| **Gap** | No backup configuration found; no `backup_retention_period`, no `aws_backup_plan`, no PITR configuration. The application code and BPMN models rely solely on Git for version history. |
| **Recommendation** | Since the application is stateless and relies on Camunda 8 SaaS for process state, backup requirements are minimal. Ensure the Git repository is regularly backed up (e.g., mirrored to CodeCommit or S3). When databases are introduced, configure automated backups with PITR and defined retention periods. Document the Camunda 8 SaaS backup SLA and ensure it meets RPO requirements. |
| **Evidence** | Repository-wide scan (no `aws_backup_plan`, no database resources, no S3 bucket definitions), `application.yml` (state managed by external Camunda 8 SaaS cluster). |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration found. No AZ-related settings in IaC (because no IaC exists). The application runs as a single worker process with no redundancy. If the worker fails, no automatic recovery occurs — Zeebe will retain unprocessed jobs until the worker restarts, but there is no failover mechanism. |
| **Gap** | All resources in a single AZ; or no AZ configuration found. In this case, no deployment infrastructure exists at all. |
| **Recommendation** | When deployed to ECS Fargate, configure the service with a minimum of 2 tasks across 2+ Availability Zones. This ensures that if one AZ fails, the worker continues processing jobs from the remaining AZ. Zeebe's job distribution model naturally supports multiple workers — adding a second task provides immediate HA improvement. |
| **Evidence** | Repository-wide scan (no `multi_az`, no `availability_zones` configuration), `README.md` (single worker execution). |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files found. No Terraform (`.tf`, `.tfvars`), no CloudFormation (`.cfn.yaml`, `.cfn.json`), no CDK (`cdk.json`), no Helm charts (`Chart.yaml`), no Kustomize (`kustomization.yaml`), no Ansible playbooks. The entire repository contains only application source code (`Worker.java`), configuration (`application.yml`), and process model files (`BPMN_DMN/`). All infrastructure — if any exists — is manually created or relies on the Camunda 8 SaaS console. |
| **Gap** | No IaC — all infrastructure created manually (ClickOps). 0% IaC coverage. This blocks reproducible deployments, disaster recovery, and environment consistency. |
| **Recommendation** | Adopt IaC as the first modernization priority. Use AWS CDK (Java, to align with existing Java skills) or Terraform to define: VPC/subnets/security groups, ECS Fargate cluster and service, IAM roles and policies, Secrets Manager for credentials, CloudWatch log groups and alarms. Start with a minimal viable IaC stack for the containerized worker, then expand coverage iteratively. |
| **Evidence** | Full repository file listing (19 files total, none are IaC): `pom.xml`, `Worker.java`, `application.yml`, `process-five.bpmn`, `decide-on-assignee.dmn`, `README.md`, `bpmn-analysis.json`, `.gitignore`, `.gitattributes`, `LICENSE`, `settings.json`, image files, and existing reports. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline definitions found. No `.github/workflows/` directory, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`, no `appspec.yml`, no CodePipeline definitions in IaC. The README instructs: "load the project in your IDE of choice and run the `Worker` class" — indicating fully manual, IDE-based execution with no automated build, test, or deployment process. |
| **Gap** | No CI/CD — all deployments are manual scripts or ClickOps. In this case, there are no deployments at all — the application is run locally. |
| **Recommendation** | Establish a CI/CD pipeline as a foundational priority. Recommended: GitHub Actions or AWS CodePipeline with CodeBuild. Pipeline stages: (1) Build — Maven package, (2) Test — unit and integration tests (to be created), (3) Security scan — dependency vulnerability check, (4) Docker build — containerize and push to ECR, (5) Deploy — ECS service update with blue/green deployment. Start with build + security scan, then add test and deploy stages as infrastructure matures. |
| **Evidence** | Repository-wide scan (no pipeline configuration files), `README.md` ("run the Worker class in IDE"). |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application is written in Java 11 (`maven-compiler-plugin` configuration: `<source>11</source>`, `<target>11</target>`). Java is explicitly listed as a score-4 language with first-class AWS SDK coverage, broad cloud-native tooling, and a mature framework ecosystem. The application uses Spring Boot via `spring-zeebe-starter:8.1.14` (which bundles Spring Boot) and the Zeebe client SDK. |
| **Gap** | Java 11 reached end of public updates in September 2023. While the language ecosystem is mature, the specific version is aging. Java 17 or 21 (current LTS) would provide better performance, language features, and longer support. |
| **Recommendation** | Upgrade from Java 11 to Java 17 or Java 21 LTS. Update `maven-compiler-plugin` source/target to 17+. This is a low-effort change that provides improved performance (virtual threads in Java 21), better language features, and extended support. Also upgrade `spring-zeebe-starter` from 8.1.14 to the latest Camunda 8 Spring SDK version. |
| **Evidence** | `pom.xml` (`maven-compiler-plugin` source=11, target=11; `spring-zeebe-starter:8.1.14`, `commons-io:2.8.0`), `Worker.java` (Java source with Spring Boot annotations). |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application is a single deployable unit — one `Worker.java` file containing a `@SpringBootApplication` class with all Zeebe job worker handlers (`DoWork` and `DoLongWork`) in a single class. There is one package (`io.camunda.getstarted.genericWorker`), one entry point (`main()`), one configuration file (`application.yml`), and one Maven module (`pom.xml`). No separate service directories, no multi-module Maven project, no Docker Compose with multiple services. All worker logic shares the same Spring application context and configuration. |
| **Gap** | Tightly-coupled monolith with no clear module boundaries and pervasive shared state (single application context, single configuration, all workers co-located). The `DoWork` handler (quick operations with error handling) and `DoLongWork` handler (blocking sleep up to 6+ minutes) have fundamentally different runtime characteristics but cannot be scaled or deployed independently. |
| **Recommendation** | Decompose into independent worker services aligned to Zeebe job types. Each job type (`DoWork`, `DoLongWork`) should be a separate deployable unit with its own `pom.xml`, Dockerfile, and scaling configuration. The BPMN process already defines clean task-type boundaries — use these as natural service boundaries. See the Decomposition Strategy section for detailed approach options. |
| **Evidence** | `Worker.java` (single class with `@SpringBootApplication`, `@EnableZeebeClient`, and multiple `@JobWorker` methods), `pom.xml` (single Maven module), `application.yml` (single shared configuration), repository structure (single `src/main/java` tree with one package). |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | *Archetype calibration: orchestrator.* The Zeebe job worker pattern provides inherent async behavior — the Zeebe engine dispatches jobs asynchronously, and workers poll for available work. The `@JobWorker` annotations establish async job consumption. The Zeebe client's `.send().exceptionally()` pattern provides async completion/failure signaling. The BPMN `CancelMessage` event subprocess demonstrates async message correlation. However, within the worker handlers, processing is synchronous: `DoWork` performs synchronous business logic with `if/else` branching, and `DoLongWork` blocks with `TimeUnit.MINUTES.sleep(mins)`. No SQS, SNS, EventBridge, or other managed messaging is used for cross-service communication. |
| **Gap** | For an orchestrator archetype, async communication should dominate for fan-out. The Zeebe job model provides worker-level async, but there is no AWS messaging layer for broader event-driven communication. Workers process jobs synchronously — no parallel async patterns within handlers. |
| **Recommendation** | Introduce Amazon EventBridge for publishing domain events (order processed, SLA breached, process cancelled) that other systems can consume. Within workers, convert blocking operations (like `DoLongWork`) to non-blocking async patterns — e.g., submit work to an SQS queue and use a callback pattern to complete the Zeebe job when processing finishes, rather than blocking the worker thread. |
| **Evidence** | `Worker.java` (`@JobWorker` async dispatch, `TimeUnit.MINUTES.sleep()` synchronous blocking, `.send().exceptionally()` async completion), `process-five.bpmn` (`CancelMessage` async message event), `pom.xml` (no SQS/SNS/EventBridge dependencies). |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | *Archetype calibration: orchestrator.* The `DoLongWork` method (`DoMoreWork` in code) uses `TimeUnit.MINUTES.sleep(mins)` to simulate a long-running operation that blocks for up to 6+ minutes (configurable via the `minutes` process variable). This is a synchronous blocking pattern with no checkpointing, no status polling endpoint, and no async callback. The BPMN process partially mitigates this with timer boundary events: a 1-minute non-interrupting timer sends SLA warnings (`R/PT1M` — repeating every minute), and a 5-minute interrupting timer escalates to a `Manual Check` user task. These BPMN timers provide orchestration-level escalation, but the worker itself remains blocked. |
| **Gap** | For an orchestrator archetype, long-running coordination should use Step Functions, polling, or callback patterns. The actual worker blocks synchronously — the BPMN timer events provide timeout escalation but cannot recover the blocked thread. If the worker crashes during the sleep, work is lost until Zeebe retries. |
| **Recommendation** | Refactor `DoLongWork` to use an async job completion pattern: (1) Activate the job, (2) Submit the actual work to an SQS queue or Step Functions workflow, (3) Return immediately (don't call `newCompleteCommand` yet), (4) When the async work finishes, a callback completes the Zeebe job. This eliminates thread blocking and enables checkpointing for crash recovery. The Zeebe SDK supports `autoComplete = false` for this pattern. |
| **Evidence** | `Worker.java` (`TimeUnit.MINUTES.sleep(mins)` in `DoMoreWork` method), `process-five.bpmn` (1-min non-interrupting timer `R/PT1M`, 5-min interrupting timer `PT5M` on `Process Data` task), `README.md` (documents timer escalation pattern with `"minutes": 6` payload). |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application has no HTTP API endpoints. It is a Zeebe job worker that communicates exclusively with the Zeebe engine via the Zeebe client SDK — it does not expose REST endpoints, GraphQL, or any other API surface. No `@RestController`, `@RequestMapping`, or API-related annotations exist in the source code. No OpenAPI, AsyncAPI, or GraphQL schema files were found. |
| **Gap** | No versioning — no API endpoints exist to version. While the Zeebe job types (`DoWork`, `DoLongWork`) serve as implicit contracts, they have no versioning strategy. If the job input/output schema changes, all BPMN processes using these job types are affected simultaneously. |
| **Recommendation** | Define versioned job type names (e.g., `DoWork_v1`, `DoWork_v2`) to enable backward-compatible evolution of worker contracts. Document job input/output schemas explicitly (e.g., in an AsyncAPI specification). If REST endpoints are added in the future, implement URL-path versioning (e.g., `/api/v1/`) from the start. |
| **Evidence** | `Worker.java` (no REST controllers, only `@JobWorker` annotations with unversioned job types `DoWork` and `DoLongWork`), `pom.xml` (no spring-boot-starter-web dependency), repository scan (no OpenAPI/AsyncAPI/GraphQL files). |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Zeebe cluster connection is hardcoded in `application.yml` with specific values: `clusterId: 01a4dee5-75d1-4c74-8cfa-36070ec57c22`, `clientId: DhS9SVqb8psF5YatlashhrAvVN8.058i`, `region: bru-2`. No service discovery mechanism exists — no AWS Service Discovery, no Istio, no Consul. No environment variable substitution (e.g., `${ZEEBE_CLUSTER_ID}`) is used in the configuration. The connection targets a specific cluster instance rather than a discoverable service name. |
| **Gap** | All service endpoints hard-coded in application code or configuration. The Zeebe cluster ID, client ID, client secret, and region are all hardcoded literal values. Changing the Zeebe cluster requires modifying `application.yml` and redeploying. |
| **Recommendation** | Replace hardcoded values in `application.yml` with environment variable references: `clusterId: ${ZEEBE_CLUSTER_ID}`, `clientId: ${ZEEBE_CLIENT_ID}`, `clientSecret: ${ZEEBE_CLIENT_SECRET}`, `region: ${ZEEBE_REGION}`. Store actual values in AWS Secrets Manager and inject via ECS task definition. For multi-environment support, use Spring profiles (`application-dev.yml`, `application-prod.yml`) with externalized configuration. |
| **Evidence** | `application.yml` (hardcoded `clusterId`, `clientId`, `clientSecret`, `region` values), repository scan (no service discovery configuration, no environment variable substitution patterns). |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage exists. No S3 buckets, no file storage configuration, no document management. The application processes BPMN process variables (JSON key-value pairs) passed through Zeebe job activations — `job.getVariablesAsMap()` retrieves structured data only. No file upload, document processing, image handling, or blob storage patterns exist in the code. |
| **Gap** | Data on local file systems, legacy document management, or inaccessible storage. In this case, no unstructured data handling exists at all. For an order processing system, there may be future needs for document storage (invoices, receipts, supporting documents). |
| **Recommendation** | If the order processing workflow requires document handling (e.g., invoices, audit documents, supporting files), introduce Amazon S3 for unstructured data storage with lifecycle policies. Consider Amazon Textract for document parsing if document extraction is needed. If no unstructured data needs exist, document this as an intentional architectural decision. |
| **Evidence** | `Worker.java` (only `job.getVariablesAsMap()` — no file I/O, no S3 client, no document processing), `pom.xml` (no S3 SDK, no Textract SDK, no file processing libraries beyond `commons-io:2.8.0`), repository scan (no S3 bucket definitions). |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No data access layer exists. The application reads process variables directly from the `ActivatedJob` object via `job.getVariablesAsMap()` — a raw Map access pattern with no abstraction, no type safety, and no data contract enforcement. Variables are accessed by string key with explicit casting: `(Boolean) variablesAsMap.get("throwError")`, `(Integer) variablesAsMap.get("minutes")`. No repository pattern, no DAO pattern, no ORM framework, no database access of any kind. |
| **Gap** | Database imports and queries scattered across many modules with no pattern. In this case, data access is entirely ad hoc through untyped Zeebe job variable maps. There is no data contract, no validation, and no consistent access pattern. |
| **Recommendation** | Define typed data transfer objects (DTOs) for Zeebe job variables rather than using raw `Map<String, Object>` with string-key access. Create a data access abstraction layer: `OrderProcessVariables` class with typed fields (`Boolean throwError`, `Integer minutes`, `String complexity`). Use Jackson or MapStruct for deserialization. This provides type safety, validation, and a clear data contract between the BPMN process and worker code. |
| **Evidence** | `Worker.java` (`job.getVariablesAsMap()`, `(Boolean) variablesAsMap.get("throwError")`, `(Integer) variablesAsMap.get("minutes")` — raw Map access with casting), `pom.xml` (no ORM, no database driver dependencies). |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database is defined in the application. No database engine version pinning exists because no database resources are provisioned. No IaC defines database instances, no Docker Compose includes database services, and no database connection configuration exists (apart from the Zeebe cluster connection). The application is entirely stateless from a data persistence perspective — all state is managed by the Camunda 8 SaaS platform. |
| **Gap** | No version pinning; no database exists. For an order processing application, the absence of a persistent data store means there is no database lifecycle to manage — but also no data persistence outside the Camunda platform. This creates platform lock-in for all order processing state. |
| **Recommendation** | If a database is introduced (per INF-Q2 recommendation), ensure the engine version is explicitly pinned in IaC, a version update procedure is documented, and EOL monitoring is established. Use Aurora PostgreSQL (currently supported versions) or DynamoDB (no version management needed) depending on data access patterns. |
| **Evidence** | Repository-wide scan (no database IaC resources, no database Docker containers, no database connection strings), `pom.xml` (no database driver dependencies), `application.yml` (only Zeebe cluster connection). |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. The application has no database at all. All business logic resides in the application layer: decision logic in the DMN model (`decide-on-assignee.dmn` with complexity-based routing), workflow orchestration in the BPMN model (`process-five.bpmn` with gateways, timers, error events), and worker logic in Java code (`Worker.java` with job handling). This is the correct pattern — business logic in application code and declarative models, not in database stored procedures. |
| **Gap** | N/A — this criterion is fully met. No stored procedures or proprietary SQL to impede database migration or modernization. |
| **Recommendation** | Maintain this pattern. If a database is introduced, keep business logic in the application layer and BPMN/DMN models. Use the database only for data persistence, not business logic execution. Avoid stored procedures, triggers, and database-specific functions. |
| **Evidence** | `Worker.java` (all business logic in Java), `BPMN_DMN/decide-on-assignee.dmn` (decision logic in DMN), `BPMN_DMN/process-five.bpmn` (workflow logic in BPMN), repository scan (no `.sql` files, no stored procedure definitions). |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration found. No IaC defines any logging infrastructure. The application uses `System.out.println()` for console output — not a structured logging framework. Log statements include: `"Lets find out if i can throw an error"`, `"Going to complete the task now... i hope"`, `"Going to throw an error now... i think"`, `"This is going to take X minute(s) to execute"`. These are development-level debug statements, not audit logs. No log retention policies, no log file validation, no immutable storage. |
| **Gap** | No CloudTrail or equivalent audit logging. No structured logging framework. No log aggregation, retention, or immutability configuration. Console output only. |
| **Recommendation** | Replace `System.out.println()` with SLF4J/Logback (included via Spring Boot). Configure structured JSON logging for CloudWatch Logs ingestion. Enable CloudTrail for AWS API audit trails when AWS infrastructure is provisioned. Configure CloudWatch log groups with defined retention periods. For process-level audit, leverage Camunda 8 Operate (included in Camunda 8 SaaS) for process instance audit trails. |
| **Evidence** | `Worker.java` (`System.out.println()` statements throughout — 6 instances), `pom.xml` (no explicit logging framework dependency — SLF4J is transitively included via Spring Boot but not configured), repository scan (no CloudTrail IaC, no logback.xml, no log4j2.xml). |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration found. No KMS keys defined. No data stores exist to encrypt — no databases, no S3 buckets, no EBS volumes. The application has no persistent data of its own. Process state is managed by Camunda 8 SaaS (which has its own encryption). However, when AWS infrastructure is provisioned, encryption at rest will need to be configured for all data stores and volumes. |
| **Gap** | No encryption at rest configured. While the application currently has no data stores, no proactive encryption configuration exists for future infrastructure. |
| **Recommendation** | When IaC is introduced, enforce encryption at rest on all resources from day one: KMS customer-managed keys for ECS task storage, S3 buckets, and any database resources. Define a KMS key policy with appropriate IAM permissions. Enable encryption by default in Terraform provider configuration or CDK constructs. |
| **Evidence** | Repository-wide scan (no `aws_kms_key`, no `kms_key_id` references, no encryption configuration), `pom.xml` (no KMS SDK dependency). |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API endpoints exist to authenticate. The application is a Zeebe job worker with no HTTP API surface. The Zeebe client connection uses OAuth2 client credentials (`clientId`/`clientSecret`) for cluster authentication, but this is a machine-to-machine credential for the Zeebe SaaS platform — not application-level API authentication. No `@RestController`, no auth middleware, no JWT validation, no API Gateway authorizers. |
| **Gap** | No API authentication — no endpoints exist. If the application evolves to expose REST endpoints, authentication infrastructure will need to be built from scratch. |
| **Recommendation** | When REST endpoints are added (e.g., for health checks, management APIs, or worker status queries), implement OAuth2/JWT authentication from the start. Use Amazon Cognito as the identity provider and API Gateway with Cognito authorizers for token validation. For internal endpoints within a VPC, consider whether network isolation (security groups, VPC Lattice) is sufficient or whether per-request auth is required. |
| **Evidence** | `Worker.java` (no REST controllers, no auth annotations), `application.yml` (Zeebe client credentials only — machine-to-machine OAuth2), `pom.xml` (no spring-security dependency). |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito user pools, no Okta configuration, no SAML/OIDC federation. The application has no user-facing authentication surface — it is a background Zeebe worker process. The Camunda 8 SaaS platform has its own identity management (Camunda Console accounts), but the worker application itself does not integrate with any IdP. |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. In this case, the application has no authentication at all. |
| **Recommendation** | If the application evolves to have user-facing components (e.g., an admin dashboard, task management UI, or order status portal), integrate with Amazon Cognito or an existing organizational IdP via OIDC/SAML federation. For machine-to-machine authentication (Zeebe client), continue using OAuth2 client credentials but store them in Secrets Manager (see SEC-Q5). |
| **Evidence** | Repository-wide scan (no `aws_cognito_*` IaC, no OIDC/SAML configuration), `pom.xml` (no spring-security-oauth2 dependency), `Worker.java` (no identity/auth imports). |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **CRITICAL:** Zeebe client credentials are hardcoded in `application.yml` and committed to version control in plaintext. The exposed secrets include: `clientId: DhS9SVqb8psF5YatlashhrAvVN8.058i` and `clientSecret: zEG_xpsDOY0J6Di_RYPu99gRSuK70PJIqJzKO-sCrfUPLr0uJ6ssoC6ZlDmBvCE8`. The `clusterId: 01a4dee5-75d1-4c74-8cfa-36070ec57c22` is also exposed. These credentials provide access to the Camunda 8 SaaS Zeebe cluster and are visible in the Git repository history. No AWS Secrets Manager, no HashiCorp Vault, no environment variable substitution. |
| **Gap** | Secrets hardcoded in code or committed to version control. This is the most critical finding in the entire assessment. Anyone with access to this repository can use these credentials to connect to the Camunda 8 cluster, deploy arbitrary BPMN processes, start process instances, and complete/fail active jobs. |
| **Recommendation** | **Immediate action required:** (1) Rotate the exposed `clientId`/`clientSecret` in the Camunda 8 Console — the current credentials are compromised. (2) Replace hardcoded values in `application.yml` with environment variable references: `clientId: ${ZEEBE_CLIENT_ID}`, `clientSecret: ${ZEEBE_CLIENT_SECRET}`. (3) Store credentials in AWS Secrets Manager with automated rotation. (4) Add `application.yml` patterns to `.gitignore` or use Spring profiles with a `application-local.yml` (git-ignored) for development credentials. (5) Scan Git history for any other committed secrets. |
| **Evidence** | `application.yml` (plaintext `clientId`, `clientSecret`, `clusterId` values committed to repository), `.gitignore` (no entries for `application.yml` or secret files). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined, so there is nothing to harden or patch. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base images. The application dependencies include `spring-zeebe-starter:8.1.14` (released ~2023) and `commons-io:2.8.0` — both are aging and may contain known vulnerabilities. No dependency vulnerability scanning is configured. |
| **Gap** | No evidence of patching strategy; no vulnerability scanning. Dependencies are not scanned for known CVEs. |
| **Recommendation** | When containerized, use a hardened base image (e.g., Amazon Corretto 17 on Amazon Linux 2023, or Distroless Java). Enable ECR image scanning for container vulnerability detection. Add OWASP dependency-check or Snyk to the CI/CD pipeline for Java dependency scanning. Audit current dependencies: `commons-io:2.8.0` should be updated to the latest version (2.15+) and `spring-zeebe-starter:8.1.14` should be updated to the latest Camunda 8 Spring SDK. |
| **Evidence** | `pom.xml` (`spring-zeebe-starter:8.1.14`, `commons-io:2.8.0` — aging dependencies), repository scan (no SSM, no Inspector, no Snyk configuration, no hardened image references). |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No application security scanning is configured. No CI/CD pipeline exists (INF-Q11=1), so there is no pipeline to integrate security scanning into. No Dependabot configuration (`.github/dependabot.yml`), no Snyk policy (`.snyk`), no OWASP dependency-check plugin in `pom.xml`, no SonarQube or Semgrep configuration. No SAST, DAST, or container scanning of any kind. |
| **Gap** | No security scanning tools configured — no Dependabot, no SAST, no container scanning. Pipeline has no security validation step because no pipeline exists. |
| **Recommendation** | When the CI/CD pipeline is established (see INF-Q11 recommendation): (1) Add OWASP dependency-check Maven plugin for Java dependency vulnerability scanning. (2) Add Dependabot or Renovate for automated dependency update PRs. (3) Add a SAST tool (SonarQube, Semgrep, or Amazon CodeGuru Reviewer) for static code analysis. (4) When containerized, enable ECR image scanning and add Trivy or Snyk container scanning to the pipeline. (5) Configure security gates that block merges on critical/high severity findings. |
| **Evidence** | Repository scan (no `.github/dependabot.yml`, no `.snyk`, no `sonar-project.properties`), `pom.xml` (no OWASP dependency-check plugin, no SpotBugs, no Checkstyle), repository root (no CI/CD pipeline files to integrate scanning into). |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, no X-Ray SDK, and no tracing dependencies in `pom.xml`. No trace ID propagation between the Zeebe engine and job workers. The application does not generate or propagate trace context (no `traceparent` or `X-Amzn-Trace-Id` headers). |
| **Gap** | No distributed tracing instrumented. For an orchestrated workflow with multiple worker types, timer events, and parallel paths, tracing is essential for debugging process execution, identifying bottlenecks (especially in `DoLongWork`), and understanding end-to-end request flow. |
| **Recommendation** | Add OpenTelemetry Java agent or SDK to the Spring Boot application. Configure trace context propagation between Zeebe and worker processes. Export traces to AWS X-Ray via the OpenTelemetry Collector. This enables correlating process instance execution with individual job worker traces, making it possible to visualize the full order processing pipeline. |
| **Evidence** | `pom.xml` (no `opentelemetry-*`, no `aws-xray-*`, no `micrometer-tracing-*` dependencies), `Worker.java` (no tracing annotations or span creation), repository scan (no OpenTelemetry configuration files). |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No CloudWatch alarms, no error budget tracking, no service level objectives. The BPMN process has timer-based escalation (1-min SLA warning, 5-min interrupting timeout), which represents business-level SLA awareness at the process design level — but these are BPMN constructs, not infrastructure SLOs with monitoring and alerting. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. Despite the BPMN process having SLA-awareness (timer events), there are no measurable SLOs for worker response time, job completion rate, error rate, or end-to-end process duration. |
| **Recommendation** | Define SLOs for critical metrics: (1) Job worker response time — p99 latency for `DoWork` job completion, (2) `DoLongWork` processing time vs SLA threshold, (3) Job failure rate < X%, (4) End-to-end process completion time < Y minutes. Implement with CloudWatch custom metrics (job duration, completion/failure counts) and CloudWatch alarms with defined thresholds. Track error budgets monthly. |
| **Evidence** | Repository-wide scan (no SLO definition files, no CloudWatch alarm IaC, no monitoring configuration), `process-five.bpmn` (timer events `R/PT1M` and `PT5M` represent business SLA awareness but not infrastructure SLOs). |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The application outputs only `System.out.println()` console messages with informal text: "Lets find out if i can throw an error", "Going to complete the task now... i hope", "This is going to take X minute(s) to execute". No CloudWatch `putMetricData` calls, no Micrometer metrics, no Prometheus endpoints. No business outcome tracking for orders processed, orders failed, SLA breaches, or error event triggers. |
| **Gap** | No custom metrics — only `System.out.println` console output. No business outcome metrics (orders processed per hour, error rate by job type, SLA breach count, average processing duration). |
| **Recommendation** | Integrate Micrometer with CloudWatch metrics exporter (included in Spring Boot). Publish business metrics: `orders.processed` (counter), `orders.failed` (counter), `job.duration` (timer, tagged by job type), `sla.warnings.sent` (counter), `error.events.triggered` (counter). Create CloudWatch dashboards for business outcome visibility. |
| **Evidence** | `Worker.java` (6 `System.out.println()` statements — no structured metrics), `pom.xml` (no Micrometer, no CloudWatch metrics dependency), repository scan (no metrics configuration). |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms (static or anomaly-based). No PagerDuty, OpsGenie, or SNS alerting integration. No composite alarms. No error rate monitoring. If the worker fails or job processing degrades, there is no automated notification mechanism. |
| **Gap** | No alerting configured. Worker failures, job processing delays, and error rate spikes go undetected until manually noticed. |
| **Recommendation** | Configure CloudWatch alarms for: (1) Worker process health (ECS task health checks), (2) Job failure rate above threshold, (3) `DoLongWork` duration exceeding SLA, (4) Error event trigger count anomaly. Route alarms to SNS → PagerDuty/OpsGenie for on-call notification. Enable CloudWatch anomaly detection on job processing latency to catch gradual degradation. |
| **Evidence** | Repository-wide scan (no CloudWatch alarm IaC, no alerting configuration, no PagerDuty/OpsGenie integration files). |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. No CodeDeploy configuration, no Helm canary/rollout, no Argo Rollouts, no Lambda traffic shifting, no ALB weighted target groups, no feature flags. The README states: "load the project in your IDE of choice and run the `Worker` class" — indicating manual IDE execution as the sole deployment method. No staging environment, no deployment pipeline, no rollback mechanism. |
| **Gap** | Direct-to-production deployment with no staged rollout. In this case, there is no deployment process at all — the application is manually run from an IDE. |
| **Recommendation** | When deployed to ECS Fargate, implement blue/green deployment via AWS CodeDeploy with ECS. This provides: (1) Zero-downtime deployments, (2) Automatic rollback on health check failure, (3) Gradual traffic shifting from old to new task set. For a Zeebe worker, blue/green is particularly safe — the Zeebe engine naturally load-balances job distribution across available workers, so old and new worker versions can coexist during deployment. |
| **Evidence** | `README.md` ("run the Worker class in IDE"), repository scan (no deployment configuration files, no CodeDeploy/Helm/Argo configurations). |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No tests of any kind exist. No `src/test/` directory, no test source files, no test configurations. No unit tests, no integration tests, no contract tests, no end-to-end tests. The `pom.xml` has no test dependencies (no JUnit, no Mockito, no Testcontainers, no spring-boot-starter-test). Zero test coverage. |
| **Gap** | No integration tests — no unit tests or automated tests at all. This is a high-risk gap for an order processing application. Any code change, dependency update, or infrastructure migration risks undetected regressions. |
| **Recommendation** | Establish a testing baseline: (1) Add `spring-boot-starter-test` and JUnit 5 to `pom.xml`. (2) Write unit tests for `DoWork` logic (error handling paths, variable parsing). (3) Add Testcontainers with `zeebe-test-container` for integration testing — start an embedded Zeebe engine, deploy the BPMN process, start a process instance, and verify the worker completes/fails jobs correctly. (4) Test the BPMN process paths: happy path, error event path, timer escalation path, cancel message path. (5) Integrate tests into the CI pipeline. |
| **Evidence** | Repository structure (no `src/test/` directory), `pom.xml` (no test dependencies — no `junit-jupiter`, no `mockito-core`, no `spring-boot-starter-test`, no `zeebe-test-container`). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation found. No runbooks (markdown, YAML, or JSON), no Systems Manager Automation documents, no Lambda-based remediation, no self-healing patterns. No incident response documentation of any kind. If the worker crashes or Zeebe connectivity fails, there is no automated recovery or escalation procedure. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No documented procedures for common failure modes (worker crash, Zeebe connectivity loss, credential expiry, job processing timeout). |
| **Recommendation** | Create runbooks for common failure modes: (1) Worker crash — automated ECS task restart (native ECS behavior when deployed), (2) Zeebe connectivity failure — automated alert + credential validation, (3) Job processing timeout — automated incident creation with process instance details, (4) High job failure rate — automated incident with recent error logs. Implement as Systems Manager Automation documents or Step Functions workflows. |
| **Evidence** | Repository-wide scan (no runbook files, no SSM Automation documents, no incident response configuration). |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file, no per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. No CloudWatch dashboards, no Grafana dashboards, no monitoring configuration of any kind. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. In this case, no monitoring exists at all. |
| **Recommendation** | When observability infrastructure is established: (1) Create a CODEOWNERS file assigning ownership of monitoring configuration, (2) Define per-worker-type dashboards (DoWork metrics, DoLongWork metrics, process completion metrics), (3) Assign alarm owners for critical alerts, (4) Tie SLO definitions to the team responsible for the order processing workflow. |
| **Evidence** | Repository-wide scan (no CODEOWNERS file, no dashboard definitions, no alarm configuration with owner tags). |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging found. No IaC exists, so there are no AWS resources to tag. No tagging standards, no `default_tags` in Terraform provider configuration, no `required-tags` Config rules, no Tag Policies. |
| **Gap** | No tags found on resources. When AWS infrastructure is provisioned, cost allocation, ownership identification, and environment classification will be impossible without a tagging strategy. |
| **Recommendation** | Establish a tagging standard before provisioning any IaC resources. Required tags: `Environment` (dev/staging/prod), `Service` (camunda8-order-process), `Team` (owning team name), `CostCenter` (for cost allocation), `Priority` (P0). Enforce via `default_tags` in Terraform provider or CDK aspects. Add AWS Config `required-tags` rule and Tag Policies in AWS Organizations. |
| **Evidence** | Repository-wide scan (no IaC files with tags, no tagging configuration). |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Containers
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR)
- [EKS Workshop](https://www.eksworkshop.com/)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q6, INF-Q10, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q3, OPS-Q6 | Maven project definition: Java 11, spring-zeebe-starter 8.1.14, commons-io 2.8.0. JAR packaging. No test dependencies, no database drivers, no security frameworks, no tracing SDKs. |
| `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q6, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q1, SEC-Q3, SEC-Q4, OPS-Q1, OPS-Q3 | Single @SpringBootApplication class with @JobWorker methods (DoWork, DoLongWork). System.out.println logging. TimeUnit.MINUTES.sleep() blocking. Zeebe client async completion patterns. |
| `src/main/resources/application.yml` | INF-Q2, INF-Q3, INF-Q4, INF-Q5, APP-Q6, DATA-Q3, SEC-Q3, SEC-Q5 | Zeebe SaaS cluster connection with hardcoded clientId, clientSecret, clusterId, and region. **Critical: plaintext secrets committed to version control.** |
| `BPMN_DMN/process-five.bpmn` | INF-Q3, INF-Q4, APP-Q2, APP-Q3, APP-Q4, DATA-Q4, OPS-Q2 | BPMN process definition: "Process Data Example" with parallel gateways, exclusive gateways, timer boundary events (1-min non-interrupting, 5-min interrupting), error boundary event, message event subprocess (CancelMessage), service tasks (DoWork, DoLongWork), user tasks, business rule task. |
| `BPMN_DMN/decide-on-assignee.dmn` | INF-Q3, DATA-Q4 | DMN decision table: complexity-based assignee routing (High→needsUser=true, Medium/Low→needsUser=false). |
| `README.md` | INF-Q1, INF-Q7, INF-Q9, INF-Q11, APP-Q4, OPS-Q5 | Setup instructions ("run the Worker class in IDE"), BPMN pattern documentation (error events, timer events, event subprocesses), process variable examples. |
| `bpmn-analysis.json` | Quick Agent Wins | BPMN task-level analysis with AI benefit scores, migration types, and integration approaches for 5 process tasks. |
| `.gitignore` | SEC-Q5 | Standard Java/Maven/IDE ignores. Does not exclude `application.yml` or secret files. |
| `LICENSE` | Metadata | MIT License, Copyright 2023 Niall. |
| `.vscode/settings.json` | INF-Q10 | VS Code editor settings — not IaC. |
