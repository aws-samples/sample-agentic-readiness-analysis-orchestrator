# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | camunda-invoice |
| **Date** | 2025-07-16 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P0 |
| **Tags** | camunda-c7, finance, invoice |
| **Context** | Camunda 7 invoice receipt process with Java delegate service tasks, DMN business rules, data store references, and call activities. |
| **Overall Score** | 1.80 / 4.0 |

**Archetype Justification**: Application manages persistent workflow state through Camunda BPM engine with CRUD operations on users, groups, authorizations, tasks, and process instances. Workflow orchestration is delegated to the embedded Camunda engine rather than implemented as explicit fan-out HTTP calls.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.17 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.43 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.80 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC found — all infrastructure is manually created (ClickOps). | Foundation blocker: without IaC, no reproducible deployments, no DR recovery, no environment parity. Blocks all other modernization pathways. |
| 2 | INF-Q1: Managed Compute | 1 | All compute on traditional Java app servers (Tomcat/WildFly/JBoss) with no managed container orchestration or serverless. | Cannot leverage elastic scaling, automated patching, or modern deployment patterns. High operational overhead. |
| 3 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith (30+ modules, single WAR, shared database schema) with pervasive shared state. | Prevents independent scaling, deployment, and team autonomy. Single point of failure for the entire platform. |
| 4 | SEC-Q4: Centralized Identity Integration | 1 | Application manages its own authentication entirely via Camunda's internal IdentityService with no external IdP. | Inconsistent access policies, increased attack surface, no SSO, difficult to enforce enterprise identity governance. |
| 5 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — Jenkins publishes artifacts to Nexus but no production deployment automation, no blue/green or canary. | Every release is a direct-to-production gamble with no staged rollout or automatic rollback capability. |

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 2 (≥ 2). The `engine-rest-openapi` module contains OpenAPI specification generation infrastructure for the Camunda REST API. Structured JSON responses are used throughout the REST API.
- **What it enables:** An agent that discovers and invokes Camunda REST API endpoints as tools — querying process instances, completing tasks, starting processes, and retrieving history data through natural language commands.
- **Additional steps:** Generate and publish the OpenAPI specification from the `engine-rest-openapi` module. Ensure the generated spec is accessible for agent tool discovery.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2). Camunda provides a centralized data access layer through its Service APIs (RepositoryService, RuntimeService, TaskService, IdentityService, ManagementService).
- **What it enables:** A natural-language-to-query agent for process instance queries, task queries, and history analysis — e.g., "Show me all overdue invoices" or "Which invoices were rejected last week?"
- **Additional steps:** Map Camunda's query API parameters to a structured schema for the agent. Define guardrails to prevent mutations through the query agent.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). Jenkins pipeline with extensive CI/CD stages exists (Jenkinsfile with ASSEMBLY, unit test, integration test, and artifact publishing stages).
- **What it enables:** An agent that monitors Jenkins build status, triggers builds for specific branches, checks test results, and manages artifact publishing to Nexus — reducing manual CI/CD oversight.
- **Additional steps:** Expose Jenkins API endpoints for agent access. Configure authentication for the agent to interact with Jenkins.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — README.md, CONTRIBUTING.md, TESTING.md, SECURITY.md, and extensive inline code documentation (Javadoc, BPMN process descriptions, DMN decision table labels).
- **What it enables:** A knowledge base agent for developer onboarding, BPMN/DMN documentation queries, and contribution guideline lookups — e.g., "How do I run integration tests?" or "What does the invoice approval process look like?"
- **Additional steps:** Index the documentation corpus (Markdown files, BPMN XML descriptions, DMN labels). Consider adding BPMN diagram rendering for visual process documentation.
- **Effort:** Low

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 3 (≥ 2). Camunda BPM engine provides workflow orchestration with BPMN processes, job executor, and async continuations.
- **What it enables:** An agent that monitors Camunda process instances, identifies stuck processes (failed jobs, overdue tasks), and triggers remediation actions — e.g., retrying failed jobs, reassigning overdue tasks, or escalating blocked processes.
- **Additional steps:** Configure Camunda's ManagementService API for agent access. Define remediation playbooks for common failure scenarios.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 1 (monolith, primary), INF-Q1 = 1 (no managed compute, supporting), APP-Q3 = 2 (sync-heavy, supporting) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (EC2/app-server compute, primary), no Dockerfiles or container definitions found (supporting). Guard: compute is traditional app server, not already on ECS/EKS/Lambda/Fargate. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). Primary trigger not met. Oracle and SQL Server drivers exist but no proprietary SQL coupling. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (no managed DB resources, primary), DATA-Q3 = 2 (engine versions unpinned for production, supporting) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 2 (primary met), but contextual guard fails: no evidence of data processing workloads (no streaming, ETL, data pipeline artifacts). Async is Camunda job executor, not analytics. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC, primary), OPS-Q5 = 1 (no deployment strategy, supporting) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent frameworks detected (primary met), but contextual guard fails: no AI/agent/LLM signal terms in context. |

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The Camunda Platform 7 is a tightly-coupled monolith (APP-Q2 = 1) deployed as a single WAR file on traditional Java application servers. The root `pom.xml` defines 30+ Maven modules compiled and deployed together. All modules share the Camunda engine database schema with tables for runtime, history, identity, authorization, and job execution. The `examples/invoice` module demonstrates this pattern — it is a process application WAR that depends on the shared engine instance.

**Compute Model Gaps (INF-Q1 = 1):** No managed compute resources. The application targets Tomcat 10, WildFly, JBoss, and GlassFish via `jboss-web.xml` and `glassfish-web.xml`. No ECS/EKS/Lambda/Fargate definitions found.

**Communication Pattern Gaps (APP-Q3 = 2):** Primary communication is synchronous — form submissions, task completions, and process start events are all HTTP requests. The Camunda job executor provides internal async for service tasks (e.g., `camunda:async="true"` on ArchiveInvoiceService), but no external managed messaging (SQS, SNS, EventBridge) is in place.

**Recommended Decomposition Approach:** Strangler Fig (Parallel Track) — see the Decomposition Strategy section below.

**Representative AWS Services:** Lambda, API Gateway, Step Functions, EventBridge, ECS/EKS, Aurora

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Saga, Hexagonal Architecture

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model (INF-Q1 = 1):** Application deployed as WAR files on traditional Java application servers — Tomcat 10, WildFly (JBoss), and GlassFish. No Dockerfiles, `docker-compose.yml`, or Kubernetes manifests found anywhere in the repository. The CI pipeline uses Maven container images (`maven:3.9.7-eclipse-temurin-17`) for builds but no runtime containers are defined.

**Container Readiness Indicators:**
- The application is a standard Java WAR file — straightforward to containerize with a Tomcat or WildFly base image
- Dependencies are managed via Maven (`pom.xml`) — well-suited for multi-stage Docker builds
- Configuration externalization is partial — database connection strings use Maven properties but are not yet environment-variable driven
- Port bindings are standard (HTTP 8080) via servlet container defaults

**Recommended Container Orchestration:** ECS with Fargate for initial containerization (reduced operational overhead), with a migration path to EKS if Kubernetes-native tooling is needed.

**Migration Approach:** Lift-and-containerize first (package existing WAR into Tomcat Docker image), then refactor configuration for container-native patterns (environment variables, health checks, graceful shutdown).

**Representative AWS Services:** ECS, Fargate, ECR, EKS (future path)

**AWS Container Migration Guidance:** [AWS Containers Strategy](https://aws.amazon.com/containers/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):** No managed AWS database resources defined in IaC (no IaC exists). The `database/pom.xml` configures JDBC drivers for 6 database platforms: H2 (in-memory dev), PostgreSQL, MySQL, Oracle, SQL Server, and DB2. The CI test matrix (`.ci/config/matrices.yaml`) references specific database versions including `aws_aurora_postgresql_14/15/16`, `postgresql_150/160/170`, `mysql_80`, `oracle_19/23`, `db2_115`, and `sqlserver_2017/2019/2022`. Production database deployment is unspecified — assumed self-managed.

**Engine Versions and EOL Status (DATA-Q3 = 2):** JDBC driver versions are pinned in `database/pom.xml` (PostgreSQL 42.5.5, Oracle 23.5.0.24.07, MySQL 8.3.0, SQL Server 8.4.1, DB2 11.5.0.0). However, production database engine versions are not specified in any deployment configuration. The CI matrix tests against specific versions, but the actual production engine version is unknown. Camunda 7 itself is EOL.

**Data Access Patterns (DATA-Q2 = 3):** Centralized data access through Camunda's Service APIs (RepositoryService, RuntimeService, TaskService, etc.). MyBatis ORM (v3.5.15) handles all SQL generation internally. 542 SQL scripts exist for schema management across 6 database platforms — DDL only, no stored procedures.

**Recommended Managed Database Target:** Amazon Aurora PostgreSQL — aligns with the existing PostgreSQL testing profiles and `aws_aurora_postgresql` CI matrix entries.

**Representative AWS Services:** Aurora PostgreSQL, RDS PostgreSQL, Amazon MemoryDB (for caching layer)

**Migration Tools:** AWS DMS (Database Migration Service), AWS SCT (Schema Conversion Tool if migrating from Oracle/SQL Server)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):** No Infrastructure as Code found. No Terraform, CloudFormation, CDK, Helm, or Kustomize files. All infrastructure (compute, networking, databases, load balancers) is assumed to be manually created. This is the #1 gap — without IaC, infrastructure changes are manual, error-prone, and non-reproducible.

**Current CI/CD State (INF-Q11 = 3):** Jenkins pipeline exists with extensive build and test stages. The ASSEMBLY stage builds, tests, and publishes artifacts to Nexus. Parallel test stages cover unit tests (H2), engine integration tests (Tomcat/WildFly with PostgreSQL), webapp integration tests, Spring Boot starter tests, and Camunda Run tests. CodeQL SAST runs via GitHub Actions. However, production deployment is not automated — the pipeline stops at artifact publishing.

**Deployment Strategy Gaps (OPS-Q5 = 1):** No blue/green, canary, or rolling deployment strategy defined. No CodeDeploy, Helm rollout, or Argo Rollouts configuration. Releases appear to be direct-to-production with no staged rollout.

**Recommended DevOps Toolchain:**
1. **IaC Foundation:** Terraform or CDK for infrastructure provisioning (VPC, compute, databases, networking)
2. **CI/CD Enhancement:** Extend Jenkins pipeline (or migrate to CodePipeline) with deployment stages targeting AWS infrastructure
3. **Deployment Strategy:** CodeDeploy with blue/green deployments for the application server tier
4. **GitOps:** Consider ArgoCD or Flux for Kubernetes-based deployments if containerizing

**Representative AWS Services:** CloudFormation, CDK, CodeBuild, CodePipeline, CodeDeploy, X-Ray, CloudWatch

**AWS Prescriptive Guidance:** [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/introduction.html)

## Decomposition Strategy

*This section is included because APP-Q2 = 1 (< 3) — the application is a tightly-coupled monolith.*

### Decomposition Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the Camunda monolith while keeping the engine running. New capabilities are built as independent services; existing modules are migrated over time. | The Maven module structure (30+ modules) provides natural extraction boundaries despite tight DB coupling. | **High** — 12-18 months. The shared Camunda engine database is the primary coupling point. | ✅ **Recommended.** Lowest risk. Start by extracting the invoice process application as an independent service backed by Camunda 8 or Step Functions, while the legacy engine continues operating. |
| **Conditional / Adaptive** | Containerize the Camunda platform as-is, then selectively extract high-value process applications based on business priority. Not all modules need to become independent services. | The team has limited capacity for full decomposition. The invoice process is the highest-priority workflow. | **Medium** — containerization in 2-4 weeks, selective extraction over 6-12 months. | ✅ **Recommended when capacity is constrained.** Containerize first (Move to Containers pathway), then extract the invoice process as the first independent service. |
| **Big-Bang Rewrite** | Rewrite the entire Camunda Platform 7 application as microservices from scratch, replacing the monolith in a single cutover. | Almost never. Only if the platform is unmaintainable. | **Very High** — 18-24+ months. Camunda 7 is EOL but functional. | ⚠️ **Not recommended.** Camunda 7 is EOL but the codebase is well-structured with extensive tests. Incremental migration to Camunda 8 or Step Functions via Strangler Fig is significantly safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the Camunda engine's data model and REST API contracts. Prevents Camunda's internal domain model from leaking into new services. | Every extraction — place an ACL between the new service and the Camunda REST API to translate between Camunda's process model and the new service's domain model. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions when extracting the invoice approval workflow (approve → prepare bank transfer → archive). These steps were a single process instance in Camunda. | When extracting the invoice process into independent services that need coordinated state changes. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture invoice state changes as events to enable audit trails and event-driven integration between the legacy engine and new services during the transition period. | When building the new invoice service alongside the legacy Camunda engine — events keep both systems in sync. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear boundaries between business logic, external interfaces (ports), and infrastructure adapters. | Every new service — ensures testability, portability, and decoupling from specific infrastructure. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal | Effort Impact | Source |
|--------|--------|---------------|--------|
| Module boundaries | 30+ Maven modules with clear package structure, but all share the Camunda engine database | **High** — modules are build-time boundaries, not runtime boundaries. Runtime coupling through shared DB is deep. | APP-Q2 finding |
| Data coupling | Single shared database with Camunda engine tables (runtime, history, identity, authorization, job, batch, metrics) | **High** — extracting any service requires data separation from the Camunda engine schema. | DATA-Q2 finding |
| Stored procedures | None (DATA-Q4 = 4). All business logic in Java (JavaDelegate) and BPMN/DMN definitions. | **Low** — no database-layer logic to extract. Clean separation of concerns. | DATA-Q4 finding |
| Communication patterns | Primarily synchronous with some Camunda job executor async. No external messaging. | **Medium** — need to introduce EventBridge or SQS for inter-service communication. | APP-Q3 finding |
| CI/CD maturity | Jenkins pipeline exists with build, test, and artifact publishing. No production deployment. | **Medium** — pipeline exists but needs deployment stages for multi-service deployment. | INF-Q11 finding |
| Test coverage | Extensive integration tests (InvoiceTestCase, engine ITs, webapp ITs) across multiple platforms. | **Medium** — good regression safety net, but tests are tightly coupled to the monolith structure. | OPS-Q6 finding |

**Calibrated Effort Estimate:** High effort overall. The primary challenge is data separation from the shared Camunda engine database. Recommend starting with the Conditional/Adaptive approach — containerize the monolith first, then extract the invoice process application as the first independent service using Strangler Fig. Target 3-6 months for containerization + first service extraction.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is on traditional Java application servers — Tomcat 10, WildFly (JBoss), and GlassFish. The `jboss-web.xml` configures `security-domain="other"` and `context-root="/camunda-invoice"`. The `glassfish-web.xml` configures `context-root="/camunda-invoice"`. The CI pipeline uses Maven container images for builds (`maven:3.9.7-eclipse-temurin-17`) but no runtime container or managed compute definitions exist. No Terraform `aws_ecs_*`, `aws_eks_*`, or `aws_lambda_*` resources found. No Dockerfiles or Kubernetes manifests found. |
| **Gap** | No managed compute — all workloads run on traditional, self-managed application servers with no elastic scaling, automated patching, or container orchestration. |
| **Recommendation** | Containerize the Camunda WAR into a Tomcat or WildFly Docker image and deploy to ECS Fargate or EKS. This eliminates app server management overhead and enables auto-scaling. |
| **Evidence** | `examples/invoice/src/main/webapp/WEB-INF/jboss-web.xml`, `examples/invoice/src/main/webapp/WEB-INF/glassfish-web.xml`, `examples/invoice/pom.xml` (WAR packaging) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed AWS database resources defined. The `database/pom.xml` configures JDBC drivers for 6 database platforms: H2 (v2.3.232, in-memory dev), PostgreSQL (driver v42.5.5), MySQL (driver v8.3.0), Oracle (driver v23.5.0.24.07), SQL Server (driver v8.4.1), and DB2 (driver v11.5.0.0). The CI test matrix includes `aws_aurora_postgresql_14/15/16` entries, indicating Aurora PostgreSQL is used for CI testing. However, no IaC provisions any managed database. The H2 in-memory profile hardcodes `sa`/empty password. |
| **Gap** | Database deployment is entirely unspecified in the repository — no managed AWS resources, no IaC, no automated failover or backup configuration. Production database is assumed self-managed. |
| **Recommendation** | Provision Amazon Aurora PostgreSQL via IaC (Terraform/CDK) with Multi-AZ failover, automated backups, and PITR. The existing `aws_aurora_postgresql` CI matrix entries confirm compatibility. |
| **Evidence** | `database/pom.xml`, `.ci/config/matrices.yaml` (aws_aurora_postgresql_14/15/16) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Camunda BPM 7 IS a dedicated workflow orchestration engine. The repository contains BPMN process definitions (`invoice.v1.bpmn`, `invoice.v2.bpmn`, `reviewInvoice.bpmn`) with structured workflows including user tasks, service tasks, business rule tasks, call activities, and exclusive gateways. The DMN decision table (`invoiceBusinessDecisions.dmn`) provides declarative business rule evaluation. The `ArchiveInvoiceService` uses `camunda:async="true"` for async execution with retry handling via the job executor. |
| **Gap** | Camunda 7 is self-managed (not a cloud-native managed service like AWS Step Functions or MWAA) and is officially EOL. The orchestration capability is strong but the platform requires self-management of the engine, database, and runtime. |
| **Recommendation** | Evaluate migration to AWS Step Functions for new workflows (cloud-native, fully managed) or Camunda 8 (cloud-hosted). For the invoice process, Step Functions with Express Workflows can replicate the approval/review/archive flow with native AWS service integration. |
| **Evidence** | `examples/invoice/src/main/resources/invoice.v2.bpmn`, `examples/invoice/src/main/resources/reviewInvoice.bpmn`, `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | For the `stateful-crud` archetype, managed messaging is expected for cross-service state changes. The Camunda engine uses async continuations (`camunda:async="true"` on ArchiveInvoiceService) and the internal job executor for asynchronous task processing. This is engine-internal async — not managed messaging infrastructure. No SQS, SNS, EventBridge, MSK, Kinesis, or Amazon MQ resources found. No external messaging SDK imports or queue consumer patterns detected. |
| **Gap** | No managed messaging infrastructure for cross-service state propagation. The Camunda job executor provides internal async but is not a substitute for managed messaging between services. |
| **Recommendation** | Introduce Amazon SQS or EventBridge for cross-service event propagation — e.g., invoice approval events, payment notification events. This decouples the invoice process from downstream consumers and enables event-driven integration. |
| **Evidence** | `examples/invoice/src/main/resources/invoice.v2.bpmn` (`camunda:async="true"`), `pom.xml` (no messaging dependencies) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network configuration found anywhere in the repository. No IaC for networking exists. The application is deployed directly on application servers with no evidence of network segmentation or isolation. |
| **Gap** | No network security configuration — services are deployed without VPC isolation, private subnets, or security groups. Blast radius is undefined. |
| **Recommendation** | Define VPC architecture in IaC with private subnets for application and database tiers, security groups with least-privilege rules, and VPC endpoints for AWS service access. |
| **Evidence** | Repository-wide search for `aws_vpc`, `aws_subnet`, `aws_security_group` returned no results. No `.tf`, `.cfn.yaml`, or CDK files found. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or load balancer configuration found. The Camunda application is deployed directly on application servers (Tomcat, WildFly, GlassFish) with context root `/camunda-invoice`. The `engine-rest` module provides a REST API but no managed entry point is configured. |
| **Gap** | Services are exposed directly through the application server — no throttling, no centralized authentication, no request validation, no traffic management. |
| **Recommendation** | Deploy an Application Load Balancer (ALB) in front of the Camunda application with health checks and path-based routing. For the REST API, add API Gateway with throttling and JWT authorizer. |
| **Evidence** | `examples/invoice/src/main/webapp/WEB-INF/jboss-web.xml` (context-root="/camunda-invoice"), `engine-rest/` module |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*`, `aws_appautoscaling_*`, Lambda concurrency limits, or DynamoDB auto-scaling. No IaC exists to define any scaling configuration. |
| **Gap** | All capacity is statically provisioned. The application cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | After containerizing, configure ECS Service Auto-Scaling with target tracking policies based on CPU utilization and request count. For the database, configure Aurora auto-scaling for read replicas. |
| **Evidence** | Repository-wide search for auto-scaling resources returned no results. No IaC files found. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no `backup_retention_period`, no `point_in_time_recovery`, no S3 versioning, no EBS snapshot lifecycle policies. The Camunda engine stores process state, history, and variables in the database, but no backup strategy is defined for this data. |
| **Gap** | No automated backups — a data loss event could wipe all process state, task history, and user data with no recovery path. |
| **Recommendation** | Configure automated daily backups with 30-day retention for the production database. Enable PITR for Aurora/RDS. Define and test a restore procedure. Implement cross-region backup replication for critical data. |
| **Evidence** | Repository-wide search for backup resources returned no results. No IaC files found. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration found. No `multi_az = true` on any database resource, no `availability_zones` spanning multiple AZs, no load balancer with cross-zone configuration. No IaC exists to define HA topology. |
| **Gap** | Single point of failure — an AZ outage would take down the entire application with no automatic recovery. |
| **Recommendation** | Deploy compute across 2+ AZs behind an ALB. Configure Aurora Multi-AZ for automatic database failover. Ensure all stateful resources span multiple AZs. |
| **Evidence** | Repository-wide search for multi-AZ and availability zone configurations returned no results. No IaC files found. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code found. No Terraform (`.tf`), CloudFormation (`.cfn.yaml`), CDK (`cdk.json`), Helm (`Chart.yaml`), or Kustomize (`kustomization.yaml`) files exist in the repository. The entire infrastructure (compute, networking, databases, load balancers, monitoring) is assumed to be manually created. |
| **Gap** | 0% IaC coverage — all infrastructure is manual (ClickOps). Infrastructure changes are error-prone, non-reproducible, and block automated deployments, environment parity, and disaster recovery. |
| **Recommendation** | Start with Terraform or CDK to codify the production infrastructure: VPC/subnets, compute (ECS/EKS), database (Aurora), networking (ALB, security groups), and monitoring (CloudWatch alarms). This is the foundation for all other modernization pathways. |
| **Evidence** | Repository-wide search for `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` returned no results. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Jenkins pipeline (`Jenkinsfile`) provides extensive CI/CD with build, test, and artifact publishing. The ASSEMBLY stage performs Maven build with `source:jar deploy` to Nexus snapshot repository. Parallel test stages include: `db-UNIT-h2`, `engine-UNIT-historylevel-audit`, `quarkus-UNIT`, `engine-IT-tomcat-10-postgresql-170`, `engine-IT-wildfly-postgresql-170`, `engine-IT-XA-wildfly-postgresql-170`, `webapp-IT-tomcat-10-h2`, `webapp-IT-wildfly-h2`, `camunda-run-IT`, `spring-boot-starter-IT`. GitHub Actions workflows include `codeql.yml` (SAST), `java-dependency-check.yml`, `renovate-auto-merge.yml`. Downstream EE pipeline triggering is configured. Jenkins uses Vault for secrets (`withVault`). |
| **Gap** | No automated production deployment — the pipeline stops at artifact publishing to Nexus. No CodeDeploy, no Helm install, no `kubectl apply`. No automated rollback capability. |
| **Recommendation** | Extend the Jenkins pipeline (or migrate to CodePipeline) with deployment stages that target production infrastructure: build → test → deploy-to-staging → integration-test → deploy-to-production with automated rollback. |
| **Evidence** | `Jenkinsfile`, `.github/workflows/codeql.yml`, `.github/workflows/java-dependency-check.yml`, `.ci/config/stage-types.yaml`, `.ci/config/matrices.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java is the primary language — Java 17 is used for builds (`jdk-17-latest` in Jenkinsfile) with compiler source/target set to JDK 11 in the release parent. Java has first-class AWS SDK coverage, broad cloud-native tooling (Spring Boot, Quarkus, Micronaut), and a mature framework ecosystem. JavaScript is used in BPMN task listeners (`camunda:script scriptFormat="javascript"` in `invoice.v2.bpmn`) and the webapps frontend. |
| **Gap** | No gap — Java is a Tier 1 language for AWS cloud-native development. |
| **Recommendation** | No change needed. When modernizing, leverage Java's AWS SDK v2, Spring Boot 3, and native compilation (GraalVM) for containerized/serverless targets. |
| **Evidence** | `pom.xml` (Java project), `Jenkinsfile` (`jdk-17-latest`), `examples/invoice/src/main/resources/invoice.v2.bpmn` (JavaScript task listeners) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Camunda Platform 7 is a tightly-coupled monolith. The root `pom.xml` defines 30+ Maven modules (engine, engine-rest, engine-dmn, engine-cdi, engine-spring, webapps, examples, spring-boot-starter, quarkus-extension, etc.) compiled and deployed together as a single platform. The `examples/invoice` module is a process application WAR deployed into the shared Camunda engine instance. All modules share the same database schema — engine tables for runtime (`ACT_RU_*`), history (`ACT_HI_*`), identity (`ACT_ID_*`), authorization, and job execution. 542 SQL files define this shared schema across 6 database platforms. The entire platform is a single deployable unit with pervasive shared state. |
| **Gap** | Tightly-coupled monolith with no clear module boundaries at runtime. All 30+ modules share a single database schema with no independent deployment capability. Changes to any module require rebuilding and redeploying the entire platform. |
| **Recommendation** | Adopt Strangler Fig decomposition: extract the invoice process application as the first independent service. Migrate to Camunda 8 (cloud-native, zeebe-based) or AWS Step Functions for new workflows. See Decomposition Strategy section. |
| **Evidence** | `pom.xml` (30+ modules), `examples/invoice/pom.xml` (WAR packaging), `engine/src/main/resources/org/camunda/bpm/engine/db/` (542 shared SQL files) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | For the `stateful-crud` archetype, a mix of async and sync with async for key workflows is expected. The invoice process uses Camunda's internal async mechanism: `camunda:async="true"` on the ArchiveInvoiceService task enables asynchronous execution via the Camunda job executor. User tasks are inherently asynchronous (persist-and-wait pattern). However, the primary communication pattern is synchronous — form submissions (`StartEvent_1` with `camunda:formKey`), task completions, and process start events are all synchronous HTTP operations. No external messaging (SQS, SNS, EventBridge) exists for cross-service state propagation. |
| **Gap** | Primarily synchronous communication with only Camunda-internal async. No managed messaging for cross-service state changes — limiting decoupling and resilience between services. |
| **Recommendation** | Introduce EventBridge or SQS for cross-service event propagation (e.g., invoice approved → notify downstream systems). Maintain synchronous patterns for user-facing task operations where appropriate. |
| **Evidence** | `examples/invoice/src/main/resources/invoice.v2.bpmn` (`camunda:async="true"`, `camunda:formKey`), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` (synchronous process start) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | For the `stateful-crud` archetype, most long-running operations should be handled asynchronously. The Camunda BPMN engine inherently handles long-running processes — process instances persist across human task waits that span days or weeks. User tasks in the invoice process have due dates of 1-2 weeks (`camunda:dueDate="${dateTime().plusWeeks(1).toDate()}"`). The `ArchiveInvoiceService` uses `camunda:async="true"` for async execution with built-in retry handling via the job executor. The `reviewInvoice` call activity delegates to a sub-process for long-running review cycles. This is a strong async pattern for long-running operations. |
| **Gap** | Long-running process handling is Camunda-specific rather than using generic cloud-native async patterns (Step Functions, SQS with visibility timeout). The Camunda engine itself needs to be running for these patterns to work. |
| **Recommendation** | For new workflows, use AWS Step Functions with wait states and callbacks for long-running human approval flows. For the existing Camunda workflows, the pattern is solid — prioritize migration to Camunda 8 or Step Functions as part of the broader decomposition. |
| **Evidence** | `examples/invoice/src/main/resources/invoice.v2.bpmn` (user tasks with due dates, async service task, call activity), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | BPMN process definitions use version tags (`camunda:versionTag="V2.0"` on `invoice.v2.bpmn`). The application deploys both v1 and v2 of the invoice process via `InvoiceApplicationHelper.createDeployment()`, which deploys `invoice.v1.bpmn` first and `invoice.v2.bpmn` in the main process archive. The `engine-rest` module provides a REST API and the `engine-rest-openapi` module generates OpenAPI specifications. However, this is process definition versioning within Camunda — not API versioning. No `/v1/`, `/v2/` URL patterns, no Accept-Version headers, no API versioning strategy for the REST API. |
| **Gap** | Versioning is ad hoc — BPMN process versioning exists but no API versioning strategy for the REST API. Breaking changes to the REST API would affect all consumers simultaneously. |
| **Recommendation** | Implement URL-path-based API versioning (`/api/v1/`, `/api/v2/`) for the Camunda REST API. Use the OpenAPI spec from `engine-rest-openapi` as the foundation for a versioned API contract. |
| **Evidence** | `examples/invoice/src/main/resources/invoice.v2.bpmn` (`camunda:versionTag="V2.0"`), `engine-rest/engine-rest-openapi/`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism found. The application is deployed as a WAR in a single application server with no dynamic service resolution. The process engine reference is hard-coded: `BpmPlatform.getProcessEngineService().getProcessEngine("default")` in `InvoiceProcessApplication.java`. The `processes.xml` references `<process-engine>default</process-engine>`. No AWS Service Discovery, Consul, Istio, or environment-variable-based endpoint configuration. |
| **Gap** | All service endpoints are hard-coded. No dynamic discovery, no service registry, no ability to relocate or scale services without code changes. |
| **Recommendation** | Introduce environment-variable-based endpoint configuration as a first step. When containerizing, adopt ECS Service Discovery or Kubernetes Service DNS for dynamic service resolution. |
| **Evidence** | `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceProcessApplication.java` (`getProcessEngine("default")`), `examples/invoice/src/main/resources/META-INF/processes.xml` |

<!-- TODO: Section 9 - Learning Materials -->

<!-- TODO: Section 10 - Evidence Index -->
