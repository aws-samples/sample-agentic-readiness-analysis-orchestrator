# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | camunda-bpm-examples |
| **Date** | 2025-07-18 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | camunda-c7, examples, multi-pattern |
| **Context** | Official Camunda Platform 7 usage examples covering service tasks, external tasks, multi-tenancy, and Spring Boot integration patterns. |
| **Overall Score** | 1.69 / 4.0 |

**Archetype Justification**: The Spring Boot examples connect to databases (H2 in-memory), manage process instance state via Camunda Process Engine API (RuntimeService, TaskService, HistoryService), and expose CRUD operations on process definitions and instances. Multiple write endpoints exist (start process, complete task, set variables). Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.14 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.69 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC files — all infrastructure would be created manually (ClickOps). | Blocks reproducible environments, disaster recovery, and automated provisioning. Foundational blocker for all modernization. |
| 2 | INF-Q11: CI/CD Automation | 1 | No build, test, or deploy pipelines. GitHub Actions workflows only perform version bumping. | No automated quality gates, no continuous delivery — every deployment is manual and error-prone. |
| 3 | SEC-Q5: Secrets Management | 1 | Database credentials and admin passwords hardcoded in application.yaml files (camunda/camunda, sa/sa, demo/demo). | Critical security vulnerability. Credentials committed to source control are exposed to anyone with repo access. |
| 4 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no ECS, EKS, Lambda, EC2, or any cloud compute resources. | Application has no defined production hosting; cannot scale, monitor, or operate in the cloud without provisioning compute from scratch. |
| 5 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — no blue/green, no canary, no rolling deployments, no CodeDeploy configuration. | Every release goes directly to production with no rollback capability, maximizing blast radius of failed deployments. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 ≥ 2 (score = 3). Camunda provides a unified data access layer through its Process Engine API (RuntimeService, TaskService, HistoryService, RepositoryService) with a clear, documented schema.
- **What it enables:** A natural-language-to-query agent that translates developer questions into Camunda API calls — e.g., "How many process instances are stuck at the review task?" → HistoryService query. Can also query the H2 database directly using Camunda's schema.
- **Additional steps:** Generate an API reference document from the Camunda REST API endpoints exposed by the Spring Boot examples. Index the Camunda Process Engine Java API for tool discovery.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. README.md contains a comprehensive table of all ~45 examples with descriptions, keywords, container types, and links. Each module has its own README with setup instructions.
- **What it enables:** A retrieval-augmented generation agent that indexes the README.md, module-level documentation, and BPMN process definitions to answer developer questions — e.g., "How do I implement an async service task?" → points to `servicetask/service-invocation-asynchronous` with code examples.
- **Additional steps:** Index all README files and BPMN process definitions. Chunk documentation by module for targeted retrieval.
- **Effort:** Low

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 ≥ 2 (score = 3). Camunda BPM workflow orchestration is the core of the repository — BPMN process definitions, service tasks, external tasks, user tasks, message events, and signal events are extensively used.
- **What it enables:** An agent that monitors and manages Camunda process instances — check process status, identify stuck instances, trigger signal events, complete external tasks, and manage the job executor. Can automate common operational tasks like retrying failed jobs.
- **Additional steps:** Expose the Camunda REST API behind an API Gateway with proper authentication. Create agent tool definitions for common Camunda operations (start process, complete task, query history).
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (no managed compute), APP-Q3=2 (limited async) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (no compute), no Dockerfiles/container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 — no stored procedures or proprietary SQL. H2 is open source. No commercial DB engines in active configs. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (H2 in-memory only), DATA-Q3=2 (no production DB version pinning) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No streaming, ETL, data pipeline, or analytics artifacts found. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), INF-Q11=1 (no CI/CD), OPS-Q5=1 (no deployment strategy) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context. Context mentions "service tasks, external tasks, multi-tenancy, and Spring Boot integration patterns" — no AI/LLM terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The Spring Boot examples are self-contained monoliths — each bundles an embedded Camunda engine, web application, REST API, and database driver into a single deployable JAR (APP-Q2=2). Module boundaries exist (separate Maven modules) but the Camunda engine is a shared monolithic dependency. The external task pattern (`clients/java/order-handling`, `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp`) demonstrates a natural service decomposition boundary.

**Compute Model Gaps:** No cloud compute infrastructure exists (INF-Q1=1). Applications would need to be deployed to ECS, EKS, or Lambda from scratch.

**Communication Pattern Gaps:** Most examples use synchronous Java Delegate execution (APP-Q3=2). The `servicetask/service-invocation-asynchronous` module shows Camunda's built-in async pattern, and the external task pattern uses long-polling — but no managed messaging (SQS, SNS, EventBridge) is in use.

**Recommended Decomposition:** See Decomposition Strategy section below. The external task pattern is the natural starting point — tasks like `creditScoreChecker`, `loanGranter`, and `invoiceCreator` already run as decoupled workers and can be extracted as independent services.

**Representative AWS Services:** Lambda, API Gateway, Step Functions, EventBridge, ECS/EKS

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Saga Pattern, Hexagonal Architecture

**Prescriptive Guidance:** [AWS Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) · [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** No compute infrastructure is defined. Spring Boot examples produce executable JARs (`spring-boot-maven-plugin` with repackage goal) but no Dockerfiles, docker-compose files, or Kubernetes manifests exist. No container images are built or published.

**Container Readiness Indicators:** The Spring Boot examples are well-suited for containerization — they produce self-contained JARs with embedded Tomcat, externalize configuration via `application.yaml`, and use standard ports. The Maven build system is container-friendly.

**Recommended Container Orchestration:** ECS with Fargate for simplicity, or EKS for teams needing Kubernetes capabilities. Use ECR for container image registry.

**Migration Approach:** Lift-and-containerize — create Dockerfiles for each Spring Boot example using a multi-stage build (Maven build stage → JRE runtime stage). Start with `spring-boot-starter/example-invoice` as the reference containerization.

**Representative AWS Services:** ECS, EKS, Fargate, ECR, App Runner

**Prescriptive Guidance:** [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** All modules use H2 in-memory databases for development and testing. The `spring-boot-starter/example-invoice/src/main/resources/application.yaml` contains commented-out connection strings for PostgreSQL, MySQL, MariaDB, Oracle, DB2, and SQL Server — indicating these are the intended production targets but none are provisioned.

**Engine Versions and EOL:** H2 version 2.3.232 is pinned in some modules (`servicetask/service-invocation-asynchronous/pom.xml`). No production database engine versions are pinned or tracked.

**Data Access Patterns:** The Camunda Process Engine API provides a unified data access layer (DATA-Q2=3). All database interactions go through Camunda's service interfaces (RuntimeService, TaskService, HistoryService), which are database-engine agnostic and support PostgreSQL, MySQL, MariaDB, Oracle, DB2, and SQL Server.

**Recommended Managed Database Targets:** Amazon RDS for PostgreSQL or Aurora PostgreSQL — Camunda BPM officially supports PostgreSQL and it offers the best combination of cost, performance, and managed features. Avoid Oracle and DB2 to prevent licensing costs.

**Representative AWS Services:** Aurora, RDS, DynamoDB (for caching/session state)

**Migration Tools:** AWS DMS for data migration, AWS SCT for schema conversion if moving from a commercial engine.

**Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** Zero. No Terraform, CloudFormation, CDK, Helm, or any IaC files exist (INF-Q10=1). All infrastructure would be provisioned manually.

**Current CI/CD State:** Two GitHub Actions workflows exist (`.github/workflows/main.yml` and `.github/workflows/bump-versions.yml`) but both are exclusively for version bumping via `workflow_dispatch`. No build, test, or deploy pipelines exist (INF-Q11=1).

**Deployment Strategy Gaps:** No deployment strategy is defined (OPS-Q5=1). No CodeDeploy, Helm releases, Argo Rollouts, or feature flags.

**Testing Gaps:** Integration tests exist (OPS-Q6=3) including JUnit 4/5 tests with Camunda BPM Assert, but they are not wired into any CI pipeline.

**Recommended DevOps Toolchain:**
1. **IaC:** Start with CDK or Terraform to define VPC, ECS/EKS cluster, RDS, and supporting infrastructure.
2. **CI/CD:** Extend GitHub Actions with build (Maven), test (JUnit), container build (Docker), and deploy (ECS/EKS) stages. Add CodeDeploy for blue/green deployments.
3. **Security:** Add Dependabot for dependency scanning, Snyk or Trivy for container scanning, and SonarQube for SAST.

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK

**Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

*This section is included because APP-Q2 scored 2 (monolith with identifiable modules but shared coupling).*

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping the monolith running. The external task pattern already provides natural extraction boundaries. | ✅ **Best fit for this repo.** APP-Q2=2 with clear module boundaries (Maven modules) and the external task pattern already decouples service workers from the engine. | **Medium** — 6-12 months. Each external task handler can be extracted independently. | ✅ **Recommended.** Start with external task handlers (creditScoreChecker, loanGranter, invoiceCreator) as the first extracted services. |
| **Conditional / Adaptive** | Containerize the Camunda engine monolith as-is, then selectively extract high-value external task handlers based on scaling needs. | Good if team capacity is limited and quick wins are needed before full decomposition. | **Low to Medium** — containerize in 2-4 weeks, selective extraction over 3-12 months. | ✅ **Recommended when capacity is constrained.** Containerize first, extract later. |
| **Big-Bang Rewrite** | Rewrite all examples as microservices from scratch, potentially migrating to Camunda 8 (Zeebe) with native cloud-native architecture. | Only if Camunda 7 is being sunset entirely in favor of Camunda 8. | **Very High** — 12-24+ months. Complete rewrite risk. | ⚠️ **Not recommended** unless migrating to Camunda 8 is a strategic decision. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted external task handlers from the Camunda engine's internal data model. | Every extraction — place an ACL between the new service and the Camunda REST API. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions for multi-step BPMN processes that span multiple extracted services. | When extracting process steps that participate in multi-step workflows (e.g., loan granting: check → decide → grant/reject). | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture process state changes as events — aligns naturally with Camunda's history service and audit trail. | When building event-driven integration between extracted services and the core engine. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each extracted service with clear boundaries between business logic and infrastructure. | Every new service — ensures testability and portability away from Camunda-specific APIs. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal in This Repo | Effort Impact |
|--------|-------------------|---------------|
| Module boundaries | ✅ Clear — 43 separate Maven modules with independent `pom.xml` files | Low effort |
| Data coupling | ✅ Low — H2 in-memory, each module has its own datasource config. No shared schemas. | Low effort |
| Stored procedures | ✅ None — all business logic in Java application layer (DATA-Q4=4) | Low effort |
| Communication patterns | 🟡 Mixed — some async (external tasks, message events), mostly sync (Java Delegates) | Medium effort |
| CI/CD maturity | ❌ No pipeline to extend (INF-Q11=1) — must build from scratch | High effort |
| Test coverage | 🟡 Tests exist (37 test files, JUnit 4/5, Camunda Assert) but not in CI | Medium effort |

**Calibrated Estimate:** Medium overall effort. The clean module boundaries, absence of stored procedures, and existing external task pattern significantly reduce decomposition complexity. The primary investment is building CI/CD infrastructure from scratch.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined anywhere in the repository. No Terraform (`aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`), CloudFormation, CDK stacks, or any IaC compute resources were found. The Spring Boot examples produce executable JARs via `spring-boot-maven-plugin` but have no defined hosting target. |
| **Gap** | All compute is undefined — no managed or self-managed cloud compute exists. Applications cannot be deployed to production without provisioning compute from scratch. |
| **Recommendation** | Define compute infrastructure in IaC. For Spring Boot applications, containerize with ECS/Fargate or EKS. For lightweight external task handlers, consider Lambda. Start with the `spring-boot-starter/example-invoice` as the reference deployment. |
| **Evidence** | `pom.xml` (root — no IaC modules), absence of `*.tf`, `*.cfn.*`, `cdk.json` files across entire repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All modules use H2 in-memory databases for development/testing. Active configs: `jdbc:h2:mem:example-simple` in `spring-boot-starter/example-simple/src/main/resources/application.yaml`, `jdbc:h2:./camunda-h2-default/process-engine` in `spring-boot-starter/example-invoice/src/main/resources/application.yaml`. Commented-out connection strings for PostgreSQL, MySQL, MariaDB, Oracle, DB2, SQL Server exist in `example-invoice` and `quarkus-extension/datasource-example` but are inactive. No RDS, DynamoDB, or any managed database resources defined in IaC. |
| **Gap** | No production-grade managed database is provisioned. H2 in-memory databases lose data on restart and cannot support production workloads. |
| **Recommendation** | Provision Amazon RDS for PostgreSQL or Aurora PostgreSQL via IaC. Camunda BPM supports PostgreSQL natively. Enable Multi-AZ, automated backups, and PITR. Update `application.yaml` to reference the RDS endpoint via environment variables or Secrets Manager. |
| **Evidence** | `spring-boot-starter/example-simple/src/main/resources/application.yaml`, `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, `quarkus-extension/datasource-example/src/main/resources/application.properties` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Camunda BPM IS a dedicated workflow orchestration engine — the entire repository is built around BPMN process orchestration. 30+ BPMN process definitions define workflows with service tasks, user tasks, external tasks, message events, signal events, timer events, and gateways. Examples include multi-step loan granting (`loan-granting.bpmn`), Twitter approval (`TwitterDemoProcess.bpmn`), job announcement publication with call activities, and async service invocation. However, Camunda is self-hosted (embedded in Spring Boot) — not a managed AWS service like Step Functions. |
| **Gap** | Workflow orchestration exists but is self-managed. The embedded Camunda engine requires operational overhead for scaling, patching, and monitoring the orchestration layer itself. |
| **Recommendation** | For new workflows, evaluate AWS Step Functions for managed orchestration. For existing Camunda workflows, consider migrating high-value processes to Step Functions using the Strangler Fig pattern, or containerize the Camunda engine on ECS/EKS with proper operational monitoring. |
| **Evidence** | `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/resources/bpmn/loan-granting.bpmn`, `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn`, `servicetask/service-invocation-asynchronous/src/main/resources/asynchronousServiceInvocation.bpmn`, `bpmn-analysis.json` (54 BPMN files analyzed) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some async patterns exist within Camunda's framework: (1) The `servicetask/service-invocation-asynchronous` module implements `SignallableActivityBehavior` with a `MockMessageQueue` for async service invocation. (2) The external task pattern (`clients/java/order-handling`, `spring-boot-starter/external-task-client`) uses long-polling for async work distribution. (3) Message start events in `startevent/message-start` demonstrate Camunda's built-in message correlation. However, no managed messaging services (SQS, SNS, EventBridge, MSK, Kinesis) are used. The `MockMessageQueue` is an in-process simulation, not real infrastructure. |
| **Gap** | Async patterns are limited to Camunda's built-in mechanisms. No managed messaging infrastructure for cross-service communication beyond Camunda's process engine. For a stateful-crud archetype, managed messaging should be used for cross-service state changes. |
| **Recommendation** | Introduce SQS or EventBridge for cross-service event communication. External task completion events, process state changes, and audit events should be published to managed queues/topics. This decouples consumers from the Camunda engine and enables event-driven integration. |
| **Evidence** | `servicetask/service-invocation-asynchronous/src/main/java/org/camunda/quickstart/servicetask/invocation/AsynchronousServiceTask.java`, `servicetask/service-invocation-asynchronous/src/main/java/org/camunda/quickstart/servicetask/invocation/MockMessageQueue.java`, `clients/java/order-handling/src/main/java/org/camunda/bpm/App.java`, `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/resources/application.yml` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or any network configuration found. No `aws_vpc`, `aws_subnet`, `aws_security_group` resources in any file. The repository contains only application source code with no infrastructure definitions. |
| **Gap** | Network security is entirely absent. Services would be deployed without isolation, segmentation, or access controls. |
| **Recommendation** | Define a VPC with private subnets for application workloads and database instances. Create least-privilege security groups. Use VPC endpoints for AWS service access. Place only load balancers and API gateways in public subnets. |
| **Evidence** | Absence of any `*.tf`, `*.cfn.*`, or CDK files containing network resources across the entire repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point configuration found. The Spring Boot examples expose HTTP endpoints directly via embedded Tomcat (Camunda REST API on `localhost:8080`). The `spring-boot-starter/example-web` module includes Spring Boot Actuator but no external gateway or load balancer. |
| **Gap** | No managed API entry point — services are exposed directly without throttling, authentication at the gateway level, or request validation. |
| **Recommendation** | Deploy an API Gateway or ALB in front of the Camunda REST API. Configure throttling, authentication (Cognito authorizer or JWT), and request validation. Use CloudFront for the Camunda web applications (Cockpit, Tasklist). |
| **Evidence** | `spring-boot-starter/example-web/pom.xml` (spring-boot-starter-actuator dependency), `spring-boot-starter/example-web/src/main/resources/application.yml` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*`, `aws_appautoscaling_*`, scaling policies, Lambda concurrency limits, or DynamoDB auto-scaling. No compute infrastructure is defined to scale. |
| **Gap** | No auto-scaling — all capacity would be statically provisioned if deployed. |
| **Recommendation** | Configure auto-scaling on the target compute platform (ECS service auto-scaling, EKS HPA, or Lambda concurrency). Set target tracking policies based on CPU utilization and request count. Configure database auto-scaling (Aurora replicas, DynamoDB capacity) as applicable. |
| **Evidence** | Absence of any IaC files with scaling configuration across the entire repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. H2 in-memory databases lose all data on process restart by design. No `aws_backup_plan`, no `backup_retention_period`, no `point_in_time_recovery`, no S3 versioning. The file-based H2 in `example-invoice` (`jdbc:h2:./camunda-h2-default/process-engine`) persists to the local filesystem but has no backup strategy. |
| **Gap** | No backup or recovery capability. Data loss is guaranteed on any infrastructure failure. |
| **Recommendation** | When migrating to a managed database, enable automated backups with a minimum 7-day retention period. Enable PITR on RDS/Aurora. Configure cross-region backup replication for critical process data. Document and test restore procedures. |
| **Evidence** | `spring-boot-starter/example-invoice/src/main/resources/application.yaml` (file-based H2 with no backup), `spring-boot-starter/example-simple/src/main/resources/application.yaml` (in-memory H2) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ or high availability configuration. No `multi_az`, no `availability_zones` spanning multiple AZs, no cross-zone load balancing. No infrastructure is defined. |
| **Gap** | No fault isolation — a single AZ failure would take down all workloads. |
| **Recommendation** | Deploy compute across 2+ AZs. Configure RDS/Aurora with Multi-AZ. Use ALB with cross-zone load balancing. Ensure ECS/EKS services span multiple AZs. |
| **Evidence** | Absence of any IaC files with AZ configuration across the entire repository. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files found. No `.tf`, `.tfvars`, CloudFormation templates, CDK stacks, Helm charts, Kustomize files, or Ansible playbooks. The entire repository is application source code with no infrastructure definitions. |
| **Gap** | 0% IaC coverage — all infrastructure would need to be created manually (ClickOps). This is the most fundamental gap in the analysis. |
| **Recommendation** | Adopt IaC immediately. Use CDK (Java — matches the team's language) or Terraform to define all infrastructure: VPC, compute (ECS/EKS), database (RDS), networking, monitoring, and backup. Start with a reference CDK stack for the `example-invoice` application. |
| **Evidence** | Complete absence of IaC files confirmed by recursive directory scan for `*.tf`, `*.cfn.*`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` — no results. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Two GitHub Actions workflows exist but neither provides build/test/deploy automation: (1) `.github/workflows/main.yml` — triggered by `workflow_dispatch`, performs version string replacement using `camunda/bump-versions-action`. (2) `.github/workflows/bump-versions.yml` — triggered by `workflow_dispatch`, runs `mvn clean package -Pbump-versions` and creates a PR. Neither workflow builds the application, runs tests, or deploys artifacts. |
| **Gap** | No CI/CD pipeline for build, test, or deployment. All deployments would be manual. The existing 37 test files are never executed in CI. |
| **Recommendation** | Create a GitHub Actions CI pipeline with stages: (1) Build — `mvn clean verify` across all modules, (2) Test — run JUnit tests with Camunda BPM Assert, (3) Container Build — Docker build and push to ECR, (4) Deploy — ECS/EKS deployment with blue/green via CodeDeploy. Add quality gates: test coverage thresholds, dependency scanning (Dependabot), and SAST. |
| **Evidence** | `.github/workflows/main.yml`, `.github/workflows/bump-versions.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is Java 17 (`maven.compiler.release=17` across all modules). Java has first-class AWS SDK coverage, mature cloud-native tooling (Spring Boot, Quarkus), and broad framework ecosystem. Secondary language is JavaScript (~15 files for Cockpit plugins using React/Angular). Camunda BPM version 7.24.0 with Spring Boot 3.5.5. |
| **Gap** | None — Java 17 is a mature, cloud-native-ready language with excellent AWS support. |
| **Recommendation** | No action needed. Java 17 with Spring Boot 3.x is well-positioned for cloud-native modernization. |
| **Evidence** | `spring-boot-starter/example-simple/pom.xml` (`maven.compiler.release=17`, `spring.boot.version=3.5.5`), `spring-boot-starter/example-web/pom.xml`, `servicetask/service-invocation-asynchronous/pom.xml` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The repository contains ~43 independent Maven modules, but the Spring Boot examples are self-contained monoliths — each bundles an embedded Camunda engine, web application, REST API, and H2 database into a single deployable JAR. The external task pattern demonstrates a natural decomposition boundary: `clients/java/order-handling` and `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp` connect to the engine REST API as decoupled workers. Identifiable module boundaries exist (separate Maven modules, separate `pom.xml` files) but the shared Camunda engine dependency and shared H2 database create monolithic coupling. |
| **Gap** | Applications are monoliths with identifiable modules but shared database schemas and direct cross-module coupling through the embedded Camunda engine. The external task pattern is the only decomposition in practice. |
| **Recommendation** | See Decomposition Strategy section. Use the external task pattern as the primary decomposition boundary. Extract external task handlers (creditScoreChecker, loanGranter, invoiceCreator/Archiver) as independent services. Adopt Strangler Fig for incremental migration. |
| **Evidence** | `pom.xml` (root — 43 modules), `spring-boot-starter/example-simple/src/main/java/.../SimpleApplication.java` (@SpringBootApplication with embedded engine), `clients/java/order-handling/src/main/java/.../App.java` (external task client), `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/java/.../HandlerConfiguration.java` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Most examples use synchronous Java Delegate execution — service tasks are implemented as `JavaDelegate` classes invoked synchronously within the Camunda engine transaction. Async patterns exist but are limited: (1) External task pattern uses long-polling (async by design), (2) `servicetask/service-invocation-asynchronous` implements `SignallableActivityBehavior` for async service invocation with callback, (3) Message start events in `startevent/message-start`. No SQS, SNS, EventBridge, or any managed async messaging is used. For a stateful-crud archetype, this represents a gap — cross-service state changes should use async patterns. |
| **Gap** | Primarily synchronous communication. Limited async patterns are Camunda-specific (external tasks, signal events) rather than general-purpose managed messaging. |
| **Recommendation** | Introduce managed messaging (SQS, EventBridge) for cross-service communication. Publish domain events on state changes (process started, task completed, process ended). Use the external task pattern as the foundation for async communication and extend it with managed queues. |
| **Evidence** | `servicetask/service-invocation-synchronous/`, `servicetask/service-invocation-asynchronous/src/main/java/.../AsynchronousServiceTask.java`, `clients/java/order-handling/src/main/java/.../App.java`, `startevent/message-start/src/main/java/.../InstantiateProcessByMessageDelegate.java` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Camunda BPM inherently handles long-running processes. BPMN wait states (user tasks, timer events, message events) suspend execution and persist process state to the database. The async service invocation example (`AsynchronousServiceTask`) demonstrates the SignallableActivityBehavior pattern — the engine creates a wait state, sends a message to an external service, and resumes when signaled. The external task pattern supports long-running work via topic subscriptions with configurable lock durations (`lock-duration: 10000` in `application.yml`). Timer events enable scheduled delays. |
| **Gap** | Long-running process handling is well-implemented within Camunda's framework, but lacks explicit status polling APIs or async job frameworks beyond Camunda's built-in mechanisms. No HTTP status polling endpoints for external consumers. |
| **Recommendation** | Expose process instance status via a status API endpoint that queries Camunda's HistoryService. For operations with external consumers, implement the async request/reply pattern with a correlation ID and status callback. |
| **Evidence** | `servicetask/service-invocation-asynchronous/src/main/java/.../AsynchronousServiceTask.java` (SignallableActivityBehavior), `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/resources/application.yml` (lock-duration config), `spring-boot-starter/example-simple/src/main/java/.../SimpleApplication.java` (HistoryService query for process completion) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy found. No `/v1/` URL patterns, no `Accept-Version` headers, no versioning annotations, no OpenAPI specifications. The Camunda REST API is consumed as-is at `http://localhost:8080/engine-rest` without version prefixes. The cockpit plugin endpoints have no versioning. No changelog files documenting API evolution. |
| **Gap** | No API versioning — breaking changes would affect all consumers simultaneously. |
| **Recommendation** | Implement URL-based versioning (`/api/v1/`) for all custom REST endpoints. Generate OpenAPI specifications from the Spring Boot REST controllers. Use API Gateway stages for version management. |
| **Evidence** | `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/resources/application.yml` (`base-url: http://localhost:8080/engine-rest` — no version prefix), `spring-boot-starter/example-web/src/main/java/.../RestApplication.java` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Environment variables and configuration files are used for endpoint configuration. The external task client connects to the Camunda REST API via a configured URL (`base-url: http://localhost:8080/engine-rest` in `application.yml`). Spring Boot's `application.yaml` configures datasource URLs. No dynamic service discovery (no AWS Service Discovery, no Consul, no Istio, no service mesh). Some endpoints are hard-coded (e.g., `ExternalTaskClient.create().baseUrl("http://localhost:8080/engine-rest")` in `App.java`). |
| **Gap** | Service endpoints configured via static URLs and environment variables. No dynamic discovery mechanism. |
| **Recommendation** | Use environment variables with DNS-based service discovery (AWS Cloud Map, ECS Service Discovery, or Kubernetes DNS). Replace hard-coded localhost URLs with configurable service names that resolve via DNS. |
| **Evidence** | `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/resources/application.yml` (`base-url: http://localhost:8080/engine-rest`), `clients/java/order-handling/src/main/java/.../App.java` (hard-coded `http://localhost:8080/engine-rest`) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 configuration, no document parsing pipelines, no Textract integration. All data is stored in H2 in-memory databases. BPMN process definitions (30+ `.bpmn` files) and DMN decision tables (1 `.dmn` file) are bundled as classpath resources within JAR files, not stored in object storage. No document upload, processing, or archival capabilities. |
| **Gap** | No unstructured data storage capability. Process definitions are classpath resources, not externally managed. |
| **Recommendation** | Store BPMN/DMN definitions in S3 for versioned, accessible storage. If the application handles document-based workflows (invoice processing, form submissions), implement an S3-based document pipeline with parsing capabilities (Textract for OCR, Comprehend for classification). |
| **Evidence** | `spring-boot-starter/example-simple/src/main/resources/bpmn/sample.bpmn` (classpath resource), `dmn-engine/dmn-engine-drg/src/main/resources/org/camunda/bpm/example/drg/dinnerDecisions.dmn` (classpath resource), absence of any S3 configuration. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Camunda BPM provides a unified data access layer through its Process Engine API. All modules interact with the database through service interfaces: `RuntimeService` (process instances), `TaskService` (user tasks), `HistoryService` (audit/history), `RepositoryService` (process definitions). The Spring Boot examples use `@Autowired` injection of these services. The `process-engine-plugin/handling-jpa-variables` module demonstrates JPA integration for custom entities alongside Camunda's API. However, some modules show direct access patterns outside the unified layer. |
| **Gap** | Mostly centralized through Camunda's Process Engine API, but some direct access patterns exist (JPA in `handling-jpa-variables`). |
| **Recommendation** | Maintain the Camunda Process Engine API as the primary data access layer. For custom entities, use a Repository/DAO pattern that wraps JPA access and is injected alongside Camunda services. Avoid direct JDBC queries. |
| **Evidence** | `spring-boot-starter/example-simple/src/main/java/.../SimpleApplication.java` (HistoryService injection), `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/java/.../HandlerConfiguration.java` (ExternalTaskHandler interface), `process-engine-plugin/handling-jpa-variables/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | H2 database version is explicitly pinned in some modules: `version.h2=2.3.232` in `servicetask/service-invocation-asynchronous/pom.xml`. Spring Boot modules inherit H2 version from `spring-boot-dependencies` BOM (version managed, not explicit). Commented-out production database configs in `example-invoice` and `quarkus-extension/datasource-example` reference PostgreSQL, MySQL, MariaDB, Oracle, DB2, and SQL Server — but none have version pinning. No documented EOL tracking for any production database engine. |
| **Gap** | H2 version is pinned for testing but production database engine versions are unknown and untracked. No EOL awareness or version update procedure. |
| **Recommendation** | When provisioning production databases, explicitly pin engine versions in IaC (e.g., `engine_version = "15.7"` for PostgreSQL on RDS). Document a version-update procedure covering downtime windows, rollback, and risk acknowledgment. Monitor AWS RDS engine version EOL dates. |
| **Evidence** | `servicetask/service-invocation-asynchronous/pom.xml` (`version.h2=2.3.232`), `spring-boot-starter/example-invoice/src/main/resources/application.yaml` (commented-out PostgreSQL/MySQL/Oracle configs without version pinning), `quarkus-extension/datasource-example/src/main/resources/application.properties` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL found anywhere in the repository. All business logic is implemented in the Java application layer via Camunda Java Delegates (`JavaDelegate` interface), delegate expressions (`${...}`), external task handlers (`ExternalTaskHandler` interface), and Spring beans. No `.sql` migration files found (Camunda manages its own schema via internal migration framework). No raw SQL execution in application code — all data access is through Camunda's Process Engine API or JPA. |
| **Gap** | None — all business logic is in the application layer. No database coupling through stored procedures or proprietary SQL. |
| **Recommendation** | No action needed. Maintain the current pattern of keeping business logic in the application layer. This makes database migration straightforward — Camunda's schema is engine-managed and database-agnostic. |
| **Evidence** | `spring-boot-starter/example-simple/src/main/java/.../SayHelloDelegate.java` (JavaDelegate pattern), `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/java/.../HandlerConfiguration.java` (ExternalTaskHandler pattern), absence of `.sql` files in recursive search. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration. No centralized audit logging infrastructure. SLF4J/Logback logging is used across modules for application-level logging, but no audit trail is configured. Camunda's built-in history service (`HistoryService`) provides process-level audit data, but it's stored in the same H2 in-memory database — no immutable storage, no log file validation, no centralized aggregation. |
| **Gap** | No audit logging infrastructure. Process audit data is ephemeral (in-memory H2). |
| **Recommendation** | Enable CloudTrail for AWS API audit logging. Configure Camunda's history level to FULL and persist history data to a managed database with immutable audit storage (S3 with Object Lock). Ship application logs to CloudWatch Logs with retention policies. |
| **Evidence** | `spring-boot-starter/example-simple/src/test/resources/logback-test.xml` (local logging only), `spring-boot-starter/example-simple/src/main/resources/application.yaml` (Camunda metrics disabled) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS configuration. No encryption at rest on any data store. H2 in-memory databases have no encryption capability. No `kms_key_id`, no `aws_kms_key` resources, no encryption configuration on any storage. |
| **Gap** | No encryption at rest — all data is unencrypted. |
| **Recommendation** | When provisioning managed databases, enable encryption at rest with customer-managed KMS keys. Enable S3 default encryption. Enable EBS encryption for any compute volumes. Define a centralized key management policy with rotation. |
| **Evidence** | Absence of any KMS or encryption configuration across the entire repository. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `spring-boot-starter/example-web` module uses Spring Security (`spring-boot-starter-security` dependency) with static basic authentication: `spring.security.user.name: demo`, `spring.security.user.password: demo` in `application.yml`. This is static credential authentication without token-based auth (OAuth2/JWT). Most other modules have no authentication at all — the Camunda REST API is exposed without protection. The `example-twitter` and `example-webapp` modules configure an admin user (`id: demo, password: demo`) but this is for the Camunda web applications, not API authentication. |
| **Gap** | Static credential authentication on one module; no authentication on most others. No token-based auth (OAuth2/JWT). |
| **Recommendation** | Implement OAuth2/JWT authentication using Amazon Cognito as the identity provider. Configure API Gateway with Cognito authorizers for all REST endpoints. Remove hardcoded credentials from configuration files. |
| **Evidence** | `spring-boot-starter/example-web/src/main/resources/application.yml` (`spring.security.user.name: demo, password: demo`), `spring-boot-starter/example-web/pom.xml` (`spring-boot-starter-security`), `spring-boot-starter/example-twitter/src/main/resources/application.yaml` (`admin-user: id: demo, password: demo`) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Cognito, Okta, Ping, OIDC, or SAML integration found. The `example-web` module uses Spring Security with hardcoded basic auth credentials. Other modules use Camunda's built-in identity service with hardcoded admin users. No external identity provider federation, no SSO configuration. |
| **Gap** | No centralized identity provider. Authentication is entirely application-managed with hardcoded credentials. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. Configure OIDC/SAML federation for Camunda web applications. Enable SSO across all services. |
| **Evidence** | `spring-boot-starter/example-web/src/main/resources/application.yml`, `spring-boot-starter/example-webapp/src/main/resources/application.yaml` (`admin-user: id: demo, password: demo`) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Database credentials are hardcoded in multiple configuration files: `username: camunda, password: camunda` in `example-invoice/application.yaml`, `username: sa, password: sa` in `quarkus-extension/datasource-example/application.properties`, `spring.security.user.name: demo, password: demo` in `example-web/application.yml`, `admin-user.id: demo, password: demo` in `example-twitter/application.yaml` and `example-webapp/application.yaml`. No Secrets Manager, no Vault, no encrypted parameter store references. All credentials are committed to version control. |
| **Gap** | Critical — all secrets are hardcoded in source code committed to version control. No secrets management system. |
| **Recommendation** | Immediately move all credentials to AWS Secrets Manager. Use Spring Cloud AWS Secrets Manager integration to inject secrets at runtime. Remove all hardcoded credentials from configuration files. Enable secret rotation for database credentials. |
| **Evidence** | `spring-boot-starter/example-invoice/src/main/resources/application.yaml` (`username: camunda, password: camunda`), `quarkus-extension/datasource-example/src/main/resources/application.properties` (`username=sa, password=sa`), `spring-boot-starter/example-web/src/main/resources/application.yml` (`name: demo, password: demo`) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened AMIs, no EC2 Image Builder pipelines. No compute resources are defined in the repository — there is nothing to harden or patch. |
| **Gap** | No compute hardening strategy. When compute is provisioned, patching and vulnerability scanning must be established. |
| **Recommendation** | When provisioning compute: use hardened base images (Amazon Linux 2023, Bottlerocket for containers), enable SSM Patch Manager for EC2, enable AWS Inspector for vulnerability scanning, integrate Snyk or Trivy into container build pipelines. |
| **Evidence** | Absence of any compute infrastructure, AMI references, or vulnerability scanning configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency scanning tools integrated into the CI/CD pipeline. No Dependabot configuration (`.github/dependabot.yml` not found). No SonarQube, Semgrep, CodeGuru Reviewer, npm audit, pip-audit, or OWASP dependency check. The GitHub Actions workflows only perform version bumping — no security validation step exists. No `.snyk` policy files. |
| **Gap** | No security scanning in the pipeline. Vulnerabilities in dependencies or application code reach production undetected. |
| **Recommendation** | Add Dependabot for automated dependency vulnerability scanning. Integrate OWASP Dependency Check into the Maven build (`mvn verify -Ddependency-check`). Add SonarQube or Semgrep for SAST in the CI pipeline. If containerizing, add ECR image scanning or Trivy. Configure security gates that block deployments on critical findings. |
| **Evidence** | `.github/workflows/main.yml` (no security steps), `.github/workflows/bump-versions.yml` (no security steps), absence of `.github/dependabot.yml`, absence of `.snyk` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No OpenTelemetry SDK in any `pom.xml` or `package.json`. No X-Ray SDK imports. No `traceparent` or `X-Amzn-Trace-Id` header propagation. No tracing configuration in any `application.yaml` or `application.properties`. |
| **Gap** | No distributed tracing — debugging failures across service boundaries (e.g., external task client ↔ Camunda engine) is guesswork. |
| **Recommendation** | Add OpenTelemetry Java agent to the Spring Boot applications. Configure trace propagation between the Camunda engine and external task clients. Export traces to AWS X-Ray or a compatible backend. |
| **Evidence** | Absence of OpenTelemetry, X-Ray, or tracing dependencies in any `pom.xml` across all 43 modules. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No error budget tracking, no latency monitoring targets, no SLO dashboards. Camunda metrics are explicitly disabled: `camunda.bpm.metrics.enabled: false` and `db-reporter-activate: false` in multiple `application.yaml` files. |
| **Gap** | No SLOs defined — cannot measure whether the system meets user expectations. |
| **Recommendation** | Define SLOs for critical process journeys (e.g., loan approval p95 latency < 5s, tweet review completion rate > 99%). Enable Camunda metrics reporting and publish to CloudWatch. Configure error budget tracking. |
| **Evidence** | `spring-boot-starter/example-simple/src/main/resources/application.yaml` (`metrics.enabled: false, db-reporter-activate: false`), `spring-boot-starter/example-web/src/main/resources/application.yml` (`metrics.enabled: false`) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Camunda BPM metrics are explicitly disabled across modules (`metrics.enabled: false`). No custom CloudWatch metrics published. No `cloudwatch.put_metric_data` calls. No business KPI alarms (process completion rates, task resolution times, SLA breach rates). Only default JVM/Spring Boot Actuator metrics may be available in `example-web` (has `spring-boot-starter-actuator` dependency) but no custom business metrics are published. |
| **Gap** | No business metrics — only infrastructure-level metrics (if any). Cannot measure business outcomes or process performance. |
| **Recommendation** | Enable Camunda BPM metrics reporting. Publish custom CloudWatch metrics for business KPIs: process instance throughput, task completion latency, external task processing time, SLA compliance rates. Create CloudWatch dashboards for process monitoring. |
| **Evidence** | `spring-boot-starter/example-simple/src/main/resources/application.yaml` (`metrics.enabled: false`), `spring-boot-starter/example-web/pom.xml` (`spring-boot-starter-actuator` — but no custom metrics) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection, no alerting configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no composite alarms. No error rate monitoring or latency percentile tracking. |
| **Gap** | No alerting — operational issues go undetected until users report them. |
| **Recommendation** | Configure CloudWatch alarms on error rates and p99 latency for Camunda REST API endpoints. Enable CloudWatch anomaly detection for critical process metrics. Integrate with PagerDuty or OpsGenie for incident notification. |
| **Evidence** | Absence of any alerting or monitoring configuration across the entire repository. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. No CodeDeploy configuration, no Helm canary deployments, no Argo Rollouts, no Lambda traffic shifting, no ALB weighted target groups, no feature flags. No deployment automation exists — the GitHub Actions workflows are only for version bumping. |
| **Gap** | No deployment strategy — every release would go directly to production with no staged rollout or rollback capability. |
| **Recommendation** | Implement blue/green deployments using CodeDeploy with ECS or EKS. Configure health checks and automatic rollback on failure. For the Camunda engine, use rolling deployments with connection draining to avoid disrupting in-flight process instances. |
| **Evidence** | `.github/workflows/main.yml` (version bumping only), `.github/workflows/bump-versions.yml` (version bumping only), absence of any deployment configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | 37 test Java files found across multiple modules. Testing frameworks used: JUnit 4 (`testing/assert/`), JUnit 5 (`testing/junit5/`), Camunda BPM Assert (`camunda-bpm-assert` dependency), Camunda BPM Mockito (`camunda-bpm-mockito`), Arquillian (`multi-tenancy/schema-isolation/src/test/resources/arquillian.xml`). Tests cover process execution, task completion, variable handling, and integration scenarios. However, tests are designed to run locally — not wired into any CI pipeline. |
| **Gap** | Good test coverage exists but is not run in CI. Tests are local-only — no automated regression prevention. |
| **Recommendation** | Wire existing tests into the CI pipeline. Add `mvn verify` as a required CI step. Configure test reporting in GitHub Actions. Expand integration tests to cover REST API endpoints and external task client interactions. |
| **Evidence** | `testing/assert/job-announcement-publication-process/src/test/java/` (JUnit 4), `testing/junit5/camunda-bpm-junit-assert/src/test/java/` (JUnit 5), `spring-boot-starter/example-simple/src/test/java/` (Spring Boot tests), `multi-tenancy/schema-isolation/src/test/resources/arquillian.xml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found — no markdown, YAML, or JSON runbook files. No Systems Manager Automation documents. No Lambda-based remediation functions. No self-healing patterns. No incident response workflows. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failures (stuck processes, failed jobs, database connectivity issues). |
| **Recommendation** | Create runbooks for common Camunda operational scenarios: retry failed jobs, restart stuck process instances, clear external task locks, manage deployment rollbacks. Automate common remediations using SSM Automation or Lambda functions. |
| **Evidence** | Absence of runbook files or incident response automation across the entire repository. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-service dashboards, no alarms with named owners, no CODEOWNERS file referencing observability assets. No SLO definitions with team attribution. No CloudWatch dashboards defined in IaC. |
| **Gap** | No observability ownership — monitoring is nonexistent. No team attribution for operational health. |
| **Recommendation** | Create a CODEOWNERS file assigning observability ownership. Define per-service CloudWatch dashboards. Assign named owners to alarms. Tie SLO definitions to specific team responsibilities. |
| **Evidence** | Absence of CODEOWNERS file, absence of dashboard definitions, absence of alarm configurations. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources are defined in the repository — therefore no tagging exists. No `default_tags` in Terraform provider, no `tags` on resources, no Tag Policies, no Config rules for required tags. |
| **Gap** | No tagging governance — when infrastructure is provisioned, tagging must be established from the start. |
| **Recommendation** | Define a tagging standard (Environment, Owner, CostCenter, Service, Version) before provisioning any infrastructure. Use `default_tags` in Terraform provider or CDK aspects to enforce mandatory tags. Configure AWS Config rules for `required-tags`. Activate cost allocation tags. |
| **Evidence** | Absence of any IaC files with tagging configuration across the entire repository. |

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
| `pom.xml` | INF-Q1, INF-Q10, APP-Q2 | Root POM defining 43 Maven modules; no IaC modules |
| `.github/workflows/main.yml` | INF-Q11, SEC-Q7, OPS-Q5 | GitHub Actions workflow for version string replacement only |
| `.github/workflows/bump-versions.yml` | INF-Q11, SEC-Q7, OPS-Q5 | GitHub Actions workflow for Maven version bumping only |
| `spring-boot-starter/example-simple/pom.xml` | APP-Q1 | Java 17, Spring Boot 3.5.5, Camunda 7.24.0, H2 dependency |
| `spring-boot-starter/example-simple/src/main/resources/application.yaml` | INF-Q2, INF-Q8, OPS-Q2, OPS-Q3 | H2 in-memory datasource, Camunda metrics disabled |
| `spring-boot-starter/example-simple/src/main/java/.../SimpleApplication.java` | APP-Q2, APP-Q4, DATA-Q2 | @SpringBootApplication with embedded Camunda engine, HistoryService injection |
| `spring-boot-starter/example-web/pom.xml` | APP-Q1, INF-Q6, OPS-Q3, SEC-Q3 | Spring Security dependency, Spring Boot Actuator |
| `spring-boot-starter/example-web/src/main/resources/application.yml` | INF-Q6, SEC-Q3, SEC-Q5, OPS-Q2 | Basic auth credentials (demo/demo), metrics disabled |
| `spring-boot-starter/example-invoice/src/main/resources/application.yaml` | INF-Q2, INF-Q8, DATA-Q3, SEC-Q5 | H2 file-based datasource, commented-out PostgreSQL/MySQL/Oracle configs, hardcoded credentials |
| `spring-boot-starter/example-twitter/src/main/resources/application.yaml` | SEC-Q3, SEC-Q4, SEC-Q5 | Hardcoded admin credentials (demo/demo) |
| `spring-boot-starter/example-webapp/src/main/resources/application.yaml` | SEC-Q4, SEC-Q5 | Hardcoded admin credentials (demo/demo) |
| `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/resources/application.yml` | INF-Q4, APP-Q4, APP-Q5, APP-Q6 | External task client config with base-url, lock-duration, async-response-timeout |
| `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/java/.../HandlerConfiguration.java` | APP-Q2, DATA-Q2, DATA-Q4 | ExternalTaskHandler pattern with @ExternalTaskSubscription |
| `clients/java/order-handling/src/main/java/.../App.java` | INF-Q4, APP-Q3, APP-Q6 | External task client with hard-coded localhost URL |
| `servicetask/service-invocation-asynchronous/pom.xml` | DATA-Q3 | H2 version pinned (2.3.232) |
| `servicetask/service-invocation-asynchronous/src/main/java/.../AsynchronousServiceTask.java` | INF-Q4, APP-Q3, APP-Q4 | SignallableActivityBehavior with MockMessageQueue for async invocation |
| `servicetask/service-invocation-asynchronous/src/main/java/.../MockMessageQueue.java` | INF-Q4 | In-process mock message queue simulation |
| `quarkus-extension/datasource-example/src/main/resources/application.properties` | INF-Q2, DATA-Q3, SEC-Q5 | H2 datasource with commented-out PostgreSQL/MySQL/Oracle configs, hardcoded credentials |
| `startevent/message-start/src/main/java/.../InstantiateProcessByMessageDelegate.java` | APP-Q3 | Message start event pattern |
| `testing/assert/job-announcement-publication-process/src/test/java/` | OPS-Q6 | JUnit 4 process tests with Camunda BPM Assert |
| `testing/junit5/camunda-bpm-junit-assert/src/test/java/` | OPS-Q6 | JUnit 5 process tests |
| `multi-tenancy/schema-isolation/src/test/resources/arquillian.xml` | OPS-Q6 | Arquillian integration test configuration |
| `spring-boot-starter/example-simple/src/test/resources/logback-test.xml` | SEC-Q1 | Local logging configuration |
| `bpmn-analysis.json` | INF-Q3 | BPMN analysis with 54 process definitions analyzed |
| `README.md` | Quick Agent Wins | Comprehensive documentation of all ~45 examples |
| `spring-boot-starter/example-simple/src/main/resources/bpmn/sample.bpmn` | DATA-Q1 | BPMN classpath resource |
| `dmn-engine/dmn-engine-drg/src/main/resources/org/camunda/bpm/example/drg/dinnerDecisions.dmn` | DATA-Q1 | DMN classpath resource |
| `process-engine-plugin/handling-jpa-variables/` | DATA-Q2 | JPA variables handling module |
| `spring-boot-starter/example-web/src/main/java/.../RestApplication.java` | APP-Q5 | REST application without versioning |
