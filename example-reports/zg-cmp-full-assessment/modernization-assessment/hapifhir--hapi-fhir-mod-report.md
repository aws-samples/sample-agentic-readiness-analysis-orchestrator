# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | hapi-fhir |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, healthcare, rest-api |
| **Context** | Open-source Java implementation of the HL7 FHIR healthcare standard. |
| **Overall Score** | 2.28 / 4.0 |

**Archetype Justification**: JPA/Hibernate persistence with full CRUD operations on FHIR resources across multiple database backends (PostgreSQL, MySQL, MariaDB, Oracle, MSSQL, H2). Primary interface is synchronous REST API. Service owns its data and does not orchestrate downstream services. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 3.33 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.71 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.28 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no IaC for ECS/EKS/Lambda/EC2 | Deployers must build all compute infrastructure from scratch; no reference architecture exists |
| 2 | INF-Q10: IaC Coverage | 1 | Zero IaC coverage — no Terraform, CloudFormation, or CDK files | All infrastructure must be manually created, making deployments non-reproducible and error-prone |
| 3 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group definitions | No network security baseline for deployers to reference; deployment security is entirely ad hoc |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging infrastructure | Healthcare workloads require audit trails for compliance (HIPAA); no audit infrastructure exists |
| 5 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption-at-rest configuration | Healthcare data requires encryption at rest for compliance; no encryption configuration provided |

---

## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 4 (API versioning) — The `hapi-fhir-server-openapi` module provides OpenAPI/Swagger documentation capability with Swagger UI (webjar v5.21.0). The FHIR REST API surface is inherently well-documented via the FHIR specification.
- **What it enables:** An API-aware agent that discovers and invokes FHIR REST endpoints as tools — enabling natural language queries against FHIR resources (Patient, Observation, etc.), automated API testing, and API-driven workflow automation.
- **Additional steps:** Deploy an instance with the OpenAPI module enabled; generate the OpenAPI spec for the specific FHIR version (R4/R5) to provide complete tool discovery for the agent.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 4 (unified data access layer) — Strong DAO/Repository pattern with abstract storage interfaces in `hapi-fhir-storage`, JPA DAOs in `hapi-fhir-jpaserver-base`, and Spring Data repositories in `hapi-fhir-repositories`.
- **What it enables:** A data query agent translating natural language clinical queries to FHIR search parameters or HQL/SQL via the well-structured data access layer — enabling clinical staff to query patient records without learning FHIR search syntax.
- **Additional steps:** Expose the HFQL (HAPI FHIR Query Language) module (`hapi-fhir-jpaserver-hfql`) as a query interface for the agent. Document the schema and available search parameters.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 4 (CI/CD automation) — Full CI/CD pipeline with GitHub Actions (parallel module testing, checkstyle, Codecov), Azure DevOps (release pipeline, nightly SNAPSHOT deploys), and automated formatting checks.
- **What it enables:** A DevOps agent that triggers builds, checks PR status, manages release pipelines, and monitors SNAPSHOT deployment status across both GitHub Actions and Azure DevOps.
- **Additional steps:** Create API tokens for GitHub Actions and Azure DevOps; expose pipeline status endpoints as agent tools.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — `README.md`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTORS.md`, extensive `hapi-fhir-docs` module with changelogs and upgrade guides, plus the official HAPI FHIR documentation at hapifhir.io.
- **What it enables:** A RAG-based knowledge agent that indexes HAPI FHIR documentation, changelogs, and FHIR specification content to answer developer questions about FHIR resource handling, search parameter configuration, interceptor patterns, and migration guides.
- **Additional steps:** Index the `hapi-fhir-docs` module content and the FHIR specification resources. Consider using Amazon Bedrock for embeddings and retrieval.
- **Effort:** Medium

### Workflow Automation Agent

- **Prerequisite:** INF-Q3 = 2 (workflow orchestration) — The Batch2 framework (`hapi-fhir-storage-batch2`) implements asynchronous job processing for bulk exports, reindexing, MDM matching, and cleanup operations with job partitioning.
- **What it enables:** A workflow automation agent that monitors Batch2 job execution, triggers reindexing or bulk export jobs, and manages the lifecycle of long-running FHIR operations.
- **Additional steps:** Expose Batch2 job status APIs as agent tools; implement monitoring hooks for job completion and failure events.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3 (distributed tracing) — OpenTelemetry instrumentation annotations are a global dependency across all 60+ modules (`io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations`), with OpenTelemetry agent-for-testing for verification.
- **What it enables:** An observability agent that queries distributed traces, correlates FHIR operation latency with database query performance, and identifies slow search parameter indexing or subscription delivery bottlenecks.
- **Additional steps:** Deploy with the OpenTelemetry Java agent; configure trace export to AWS X-Ray or an OpenTelemetry Collector; build trace query tools for the agent.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — application is a well-structured modular monolith; primary trigger not met |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1, no deployment container definitions found; compute is not already on managed services |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL; ORM abstraction layer decouples from commercial engines |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 — no managed database infrastructure defined; DATA-Q3 = 3 strengthens case |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: no data processing/streaming/ETL workloads detected; Hibernate Search is application-level indexing, not analytics |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 — zero IaC coverage; OPS-Q5 = 1 — no deployment strategy defined |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
HAPI FHIR has no deployment infrastructure defined in the repository. The `.github/docker/Dockerfile` is a build-only image (`maven:3.9-eclipse-temurin-21-jammy` with GPG for signing) used exclusively for publishing artifacts to Maven Central. No Dockerfiles exist for running the FHIR server as a container. No Kubernetes manifests, Helm charts, or ECS/EKS task definitions are present.

**Container Readiness Indicators:**
- ✅ Java 17 with Spring Boot 3.4.x — excellent container support via `spring-boot-maven-plugin` (already in `pluginManagement`)
- ✅ Embedded Jetty 12 server — no external application server dependency
- ✅ Configuration externalization via Spring Boot properties — ready for environment variable injection
- ✅ Multi-database support via JDBC drivers — connection strings can be externalized
- ✅ Flyway migration support — database schema can be managed at container startup

**Recommended Container Orchestration Platform:**
Deploy on **Amazon EKS** (per preference: `prefer: ["eks"]`) with Fargate profiles for stateless workloads. Avoid self-managed Kubernetes (per preference: `avoid: ["self-managed-kubernetes"]`).

**Representative AWS Services:** Amazon EKS, AWS Fargate, Amazon ECR, AWS App Runner (for simpler deployments)

**Migration Approach:**
1. Create a production `Dockerfile` using `eclipse-temurin:17-jre` base image with the Spring Boot fat JAR
2. Configure health check endpoints (`/fhir/metadata` for FHIR capability statement)
3. Externalize database connection, Elasticsearch endpoint, and application configuration via environment variables
4. Build EKS cluster with managed node groups or Fargate profiles
5. Create Helm chart for deployment configuration (replicas, resources, health checks, ingress)

**Prescriptive Guidance:** [AWS EKS Workshop](https://www.eksworkshop.com/) · [Containerizing Java Applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-containers/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:**
HAPI FHIR supports multiple database backends via JDBC drivers pinned in `pom.xml`:
- PostgreSQL 42.7.7
- MySQL Connector/J 9.1.0
- MariaDB 3.0.4
- Microsoft SQL Server 12.4.3 (commercial)
- Oracle ojdbc11 23.6.0.24.10 (commercial)
- H2 2.3.232 (embedded/testing)

No IaC defines database resources — database provisioning is entirely left to deployers. The project does not provision managed or self-managed databases; it only provides driver compatibility.

**Engine Versions and EOL Status (DATA-Q3):**
Driver versions are pinned and current. No engines at EOL. However, deployers may run any engine version — no guidance or constraints are provided.

**Data Access Patterns (DATA-Q2):**
Excellent — centralized DAO/Repository pattern with abstract storage interfaces in `hapi-fhir-storage`, JPA DAOs in `hapi-fhir-jpaserver-base`, and Spring Data repositories in `hapi-fhir-repositories`. Flyway manages schema migrations via `hapi-fhir-sql-migrate`. Hibernate ORM provides database abstraction — switching backends requires only driver and dialect configuration changes.

**Recommended Managed Database Targets:**
- **Primary recommendation:** Amazon Aurora PostgreSQL (per preference: `prefer: ["aurora"]`) — best fit for HAPI FHIR's relational data model with Hibernate/JPA
- **For healthcare search workloads:** Amazon OpenSearch Service for Hibernate Search backend (replacing self-managed Elasticsearch)
- **For caching/sessions:** Amazon ElastiCache for Redis
- Avoid Oracle (per preference: `avoid: ["oracle"]`)

**Representative AWS Services:** Amazon Aurora, Amazon RDS (PostgreSQL, MySQL, MariaDB), Amazon OpenSearch Service, Amazon ElastiCache, Amazon DynamoDB (for metadata/config, per preference)

**Migration Tools:** AWS Database Migration Service (DMS), AWS Schema Conversion Tool (SCT) — though SCT is less relevant since HAPI uses ORM abstraction

**Prescriptive Guidance:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero IaC files exist in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize configurations were found. All infrastructure provisioning for HAPI FHIR deployments must be created manually. This is the most significant DevOps gap — without IaC, deployments are non-reproducible and environment consistency cannot be guaranteed.

**Current CI/CD State (INF-Q11 = 4):**
The project has excellent CI/CD automation for the build/test/publish lifecycle:
- GitHub Actions: Pull request pipeline with parallel per-module testing, checkstyle validation, Codecov coverage reporting, release workflow
- Azure DevOps: Release pipeline, nightly SNAPSHOT deployment to Maven Central via `snapshot-deploy-job.yml`
- Code quality: CodeQL SAST, Dependabot dependency scanning, WhiteSource vulnerability scanning, Spotless formatting

However, CI/CD covers **library publishing** only — there is no deployment pipeline for running HAPI FHIR as a service (no EKS/ECS deployment stages, no infrastructure provisioning).

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy exists for service deployment. The project publishes JAR/WAR artifacts to Maven Central but provides no blue/green, canary, or rolling deployment configuration for running the FHIR server.

**Testing Gaps (OPS-Q6 = 4):**
Strong — integration tests exist with Testcontainers, Failsafe plugin, and per-FHIR-version test modules.

**Recommended DevOps Toolchain:**
1. **IaC:** AWS CDK (Java) or Terraform for infrastructure provisioning — CDK is particularly well-suited as HAPI FHIR is a Java project, allowing infrastructure and application to share the same language
2. **Container Registry:** Amazon ECR for Docker image storage
3. **Deployment:** AWS CodeDeploy with EKS for blue/green deployments, or ArgoCD for GitOps-based deployment
4. **API Management:** Amazon API Gateway (per preference: `prefer: ["api-gateway"]`) as the entry point with throttling, auth, and request validation
5. **Event-Driven:** Amazon EventBridge (per preference: `prefer: ["eventbridge"]`) for FHIR subscription notifications and integration events

**Representative AWS Services:** AWS CDK, Amazon ECR, AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy, Amazon API Gateway, Amazon EventBridge, AWS CloudFormation

**Prescriptive Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

<!-- Decomposition Strategy section omitted: APP-Q2 = 3 (modular monolith with well-defined boundaries). Decomposition guidance is not needed. -->

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in the repository. The only Dockerfile (`.github/docker/Dockerfile`) is a build-only image (`maven:3.9-eclipse-temurin-21-jammy` with GPG) used for publishing artifacts to Maven Central. No ECS task definitions, EKS manifests, Lambda functions, EC2 instances, or Fargate configurations exist. The project provides database drivers and a Spring Boot application framework but leaves all deployment infrastructure to deployers. |
| **Gap** | No managed compute infrastructure exists. Deployers receive no reference architecture, Dockerfile, or container orchestration configuration for running HAPI FHIR as a service. |
| **Recommendation** | Create a production Dockerfile and EKS deployment manifests (per preference: `prefer: ["eks"]`). Provide a reference architecture using Amazon EKS with Fargate profiles, Amazon ECR for container images, and health check endpoints via the FHIR CapabilityStatement endpoint (`/fhir/metadata`). |
| **Evidence** | `.github/docker/Dockerfile` (build-only), `pom.xml` (Spring Boot 3.4.11, Jetty 12.0.32 embedded server), absence of `*.tf`, `*.cfn.*`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | HAPI FHIR includes JDBC driver dependencies for six database backends — PostgreSQL 42.7.7, MySQL Connector/J 9.1.0, MariaDB 3.0.4, MSSQL 12.4.3, Oracle ojdbc11 23.6.0.24.10, and H2 2.3.232 — but no IaC defines any database resources. The project supports multiple backends via Hibernate ORM dialect configuration but does not provision, manage, or configure databases. No `aws_rds_*`, `aws_dynamodb_*`, or equivalent resources exist. |
| **Gap** | No managed database infrastructure defined. Database provisioning mode (managed vs self-managed) is entirely left to deployers with no guidance or reference architecture. |
| **Recommendation** | Define database infrastructure in IaC using Amazon Aurora PostgreSQL (per preference: `prefer: ["aurora"]`) as the primary backend. Include Multi-AZ failover, automated backups, and encryption at rest. Provide a reference Terraform module or CDK construct for deployers. Avoid Oracle (per preference: `avoid: ["oracle"]`). |
| **Evidence** | `pom.xml` (database driver dependencies), absence of Terraform/CloudFormation database resource definitions |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `hapi-fhir-storage-batch2` and `hapi-fhir-storage-batch2-jobs` modules implement an application-level batch job framework for asynchronous processing of long-running operations: bulk exports, reindexing, MDM matching, and cleanup jobs. The framework supports job partitioning for scalability. However, this is entirely custom Java code — not a managed orchestration service like AWS Step Functions, Temporal, or MWAA. The orchestration logic is embedded in the application layer. Applying stateful-crud archetype calibration: dedicated workflow orchestration would improve reliability of multi-step batch operations. |
| **Gap** | Workflow orchestration is application-level code with no dedicated service. Error handling, retry logic, and state management for batch jobs are implemented in custom Java classes rather than a managed orchestrator. |
| **Recommendation** | Consider migrating Batch2 job orchestration to AWS Step Functions for managed state machine execution, visual monitoring, automatic retries, and error handling. This is particularly valuable for healthcare workloads where bulk export and reindexing reliability is critical. Amazon EventBridge (per preference: `prefer: ["eventbridge"]`) can trigger Step Functions workflows based on FHIR events. |
| **Evidence** | `CLAUDE.md` (Batch2 framework description), `hapi-fhir-storage-batch2/`, `hapi-fhir-storage-batch2-jobs/`, `.github/CODEOWNERS` (batch2 ownership) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `hapi-fhir-jpaserver-subscription` module implements FHIR Subscription delivery via REST-hooks, email (SimpleJavaMail), and WebSocket (Jetty WebSocket). This provides application-level async notification delivery. However, no managed messaging infrastructure is defined — no SQS, SNS, EventBridge, MSK, or Kinesis resources. The subscription delivery mechanism is embedded in the application with no external message broker. Applying stateful-crud archetype calibration: managed messaging would improve cross-service state propagation and subscription delivery reliability. |
| **Gap** | Async messaging for FHIR subscriptions and cross-service state changes relies on application-level code rather than managed messaging services. No event bus exists for decoupling subscription producers from consumers. |
| **Recommendation** | Implement Amazon EventBridge (per preference: `prefer: ["eventbridge"]`) as the event bus for FHIR subscription notifications and integration events. Use Amazon SQS for reliable message delivery to subscription endpoints. Avoid self-managed Kafka (per preference: `avoid: ["self-managed-kafka"]`). |
| **Evidence** | `hapi-fhir-jpaserver-subscription/`, `pom.xml` (SimpleJavaMail 8.12.2, Jetty WebSocket dependencies), absence of `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*` resources |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation definitions exist in the repository. No `aws_vpc`, `aws_subnet`, `aws_security_group` resources found. The project includes a CORS filter dependency (`ebay-cors-filter 1.0.1`) for cross-origin request handling but no network-level security configuration. |
| **Gap** | No network security baseline exists. Healthcare FHIR servers handle sensitive patient data requiring network isolation and least-privilege access controls. |
| **Recommendation** | Define network infrastructure in IaC: deploy HAPI FHIR in private subnets behind Amazon API Gateway (per preference: `prefer: ["api-gateway"]`) with security groups restricting ingress to the API Gateway only. Use VPC endpoints for accessing AWS services (Aurora, S3, Secrets Manager) without traversing the public internet. |
| **Evidence** | Absence of any `.tf`, `.cfn.*`, or CDK files defining VPC/subnet/security group resources; `pom.xml` (CORS filter dependency) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or other managed entry point is defined. The `hapi-fhir-server-openapi` module provides OpenAPI/Swagger documentation capability with Swagger UI (webjar v5.21.0), but no actual API gateway or load balancer is configured to front the FHIR server. The application exposes its servlet-based endpoints directly. |
| **Gap** | No managed entry point with throttling, authentication, or request validation. Direct service exposure lacks rate limiting and centralized auth — critical for healthcare APIs. |
| **Recommendation** | Deploy Amazon API Gateway (per preference: `prefer: ["api-gateway"]`) as the entry point for the FHIR REST API. Configure throttling for healthcare workload protection, Cognito or OAuth2 authorizers for authentication, and request validation using the OpenAPI spec generated by `hapi-fhir-server-openapi`. |
| **Evidence** | `hapi-fhir-server-openapi/` (OpenAPI capability), `pom.xml` (Swagger UI 5.21.0 webjar, Swagger Jakarta annotations 2.2.30), absence of `aws_api_gateway_*`, `aws_lb_*` resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists in the repository. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or Kubernetes HPA (HorizontalPodAutoscaler) definitions found. No Lambda concurrency limits, DynamoDB auto-scaling, or Aurora auto-scaling configuration. |
| **Gap** | Healthcare workloads can have variable demand (e.g., bulk data export requests, clinical event spikes). Without auto-scaling, the FHIR server cannot respond to traffic changes. |
| **Recommendation** | When deploying on EKS, configure Kubernetes HPA based on CPU/memory metrics and custom FHIR request rate metrics. Configure Aurora auto-scaling for read replicas. Use Fargate for burst capacity. |
| **Evidence** | Absence of any auto-scaling resource definitions in the repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. No `aws_backup_plan`, `backup_retention_period`, `point_in_time_recovery`, or S3 versioning configurations found. The project includes Flyway migrations (`hapi-fhir-sql-migrate`) which provide schema reproducibility but not data backup/recovery. |
| **Gap** | Healthcare data requires robust backup and recovery (HIPAA compliance). No backup strategy, retention policy, or restore procedure exists. |
| **Recommendation** | Configure automated backups on Aurora with at least 7-day retention and PITR (Point-In-Time Recovery). Enable AWS Backup plans for cross-region replication of healthcare data. Document and test restore procedures quarterly. |
| **Evidence** | `hapi-fhir-sql-migrate/` (schema migrations only), absence of backup resource definitions |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration exists. No `multi_az = true`, `availability_zones`, or cross-AZ load balancer configuration found. The project provides no reference architecture for high-availability deployment. |
| **Gap** | Single-AZ deployment of a healthcare FHIR server is a critical risk — an AZ failure would cause complete service outage for clinical systems. |
| **Recommendation** | Deploy HAPI FHIR on EKS across at least 2 Availability Zones. Configure Aurora Multi-AZ for automatic database failover. Use an Application Load Balancer with cross-zone load balancing enabled. |
| **Evidence** | Absence of any multi-AZ or HA resource definitions in the repository |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform files (`.tf`), CloudFormation templates, CDK stacks (`cdk.json`), Helm charts (`Chart.yaml`), or Kustomize configurations (`kustomization.yaml`) exist in the repository. All infrastructure for deploying HAPI FHIR must be created manually by deployers. |
| **Gap** | No infrastructure is defined as code. Deployments are non-reproducible, environment-specific configurations are undocumented, and disaster recovery requires manual reconstruction. |
| **Recommendation** | Create an `infrastructure/` directory with AWS CDK (Java) stacks defining: VPC/networking, EKS cluster, Aurora PostgreSQL, API Gateway, CloudWatch alarms, and backup plans. CDK Java is recommended because the HAPI FHIR team already uses Java, reducing the learning curve. |
| **Evidence** | Repository-wide search for `*.tf`, `*.cfn.*`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` returned zero results |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive CI/CD automation with multiple pipeline systems: **GitHub Actions** — pull request pipeline (`pull-request.yml`) with parallel per-module testing via reusable workflow (`parallel-pipeline-build.yml`), up to 256 parallel module test jobs, checkstyle validation, Codecov coverage reporting, Spotless formatting check (`spotless.yml`), CodeQL SAST analysis (`codeql-analysis.yml`), and release workflow (`release.yml`). **Azure DevOps** — release pipeline (`release-pipeline.yml`) with full build including unit and integration tests (360-minute timeout), nightly SNAPSHOT deployment to Maven Central (`snapshot-pipeline.yml` + `snapshot-deploy-job.yml`) with GPG signing, Slack failure notifications. Both pipelines include automated test, build, and deploy stages with automated artifact publishing. |
| **Gap** | CI/CD covers library publishing only. No deployment pipeline exists for running HAPI FHIR as a service (no container build/push, no EKS/ECS deployment stages). |
| **Recommendation** | Extend the existing CI/CD to include container image building (Dockerfile → ECR push), infrastructure provisioning (CDK deploy), and service deployment (EKS rolling update or blue/green via CodeDeploy). |
| **Evidence** | `.github/workflows/pull-request.yml`, `.github/workflows/parallel-pipeline-build.yml`, `.github/workflows/release.yml`, `.github/workflows/spotless.yml`, `.github/workflows/codeql-analysis.yml`, `release-pipeline.yml`, `snapshot-pipeline.yml`, `snapshot-deploy-job.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 17 with first-class AWS SDK coverage, mature Spring Boot 3.4.x / Spring Framework 6.2.x ecosystem, and comprehensive cloud-native tooling. The project enforces Java 17 via Maven enforcer plugin. The dependency stack includes Spring Boot, Hibernate 6.6.x, Jackson 2.20.x, and JUnit 5.11.x — all modern, actively maintained frameworks with excellent AWS integration support. |
| **Gap** | None — Java 17 is a Tier 1 language for AWS with the most comprehensive SDK coverage and cloud-native tooling ecosystem. |
| **Recommendation** | Continue with Java 17. Consider upgrading to Java 21 LTS when Spring Boot 3.x fully supports it for virtual threads (Project Loom), which would benefit the FHIR server's concurrent request handling. |
| **Evidence** | `pom.xml` (`<maven.compiler.release>17</maven.compiler.release>`, Spring Boot 3.4.11, Spring 6.2.12, Hibernate 6.6.4.Final) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | HAPI FHIR is a well-structured modular monolith with 60+ Maven modules organized in clear architectural layers: Foundation (hapi-fhir-base, structures), Client/Server Framework (hapi-fhir-client, hapi-fhir-server), Storage Abstraction (hapi-fhir-storage, hapi-fhir-jpa), JPA Server Features (hapi-fhir-jpaserver-base, subscription, MDM), and Specialized Features (batch2, openapi, cds-hooks). Modules have defined ownership boundaries via CODEOWNERS. Interfaces between layers are well-defined (abstract storage API, interceptor chain, DAO pattern). However, it produces a single deployable artifact — the JPA server with all features bundled. |
| **Gap** | Minor — modules are well-bounded but the deployment unit is monolithic. Some features (subscriptions, MDM, batch2, CDS Hooks) could potentially be extracted as independent services for independent scaling, but the current modular structure is functional and maintainable. |
| **Recommendation** | The modular monolith architecture is appropriate for HAPI FHIR's current use case. If scaling specific features independently becomes necessary (e.g., subscription delivery at high volume), the existing module boundaries provide clean extraction points for a Strangler Fig approach. No immediate decomposition is recommended. |
| **Evidence** | `pom.xml` (60+ module definitions), `CLAUDE.md` (5-layer architecture description), `.github/CODEOWNERS` (per-module ownership) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Applying stateful-crud archetype calibration: The primary FHIR REST API is synchronous (appropriate for CRUD operations). The subscription module adds async notification delivery (REST-hooks, WebSocket, email). The Batch2 framework handles async job processing for long-running operations. This is a healthy mix for a stateful-crud service — synchronous for direct CRUD operations, asynchronous for notifications and batch processing. Some cross-service state propagation (subscription delivery to external endpoints) still uses synchronous HTTP calls where async (SQS/EventBridge) would improve reliability. |
| **Gap** | Minor — subscription delivery to external endpoints uses synchronous HTTP calls. If a subscriber endpoint is slow or down, delivery retries are handled in-application rather than via a managed message queue with dead-letter queues. |
| **Recommendation** | For deployed instances, consider backing FHIR subscription delivery with Amazon SQS or EventBridge for guaranteed delivery and retry semantics. This does not require application changes — the subscription module already supports pluggable delivery channels. |
| **Evidence** | `hapi-fhir-jpaserver-subscription/`, `hapi-fhir-storage-batch2/`, `hapi-fhir-server/` (REST provider pattern), `CLAUDE.md` (interceptor chain for subscription delivery) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Applying stateful-crud archetype calibration: The Batch2 framework (`hapi-fhir-storage-batch2` + `hapi-fhir-storage-batch2-jobs`) explicitly handles long-running operations asynchronously with job partitioning. Bulk exports, reindexing, MDM matching, and cleanup operations are all implemented as Batch2 jobs with status polling, partitioned execution for scalability, and asynchronous completion. This fully meets the criterion for a stateful-crud service — all operations over 30 seconds are handled asynchronously with status tracking. |
| **Gap** | None — long-running operations are properly handled via the Batch2 async job framework. |
| **Recommendation** | Maintain the Batch2 pattern. When deploying on AWS, consider persisting Batch2 job state in DynamoDB (per preference: `prefer: ["dynamodb"]`) for faster state lookups and to decouple job state from the primary database. |
| **Evidence** | `hapi-fhir-storage-batch2/`, `hapi-fhir-storage-batch2-jobs/`, `CLAUDE.md` ("Batch2 Job Framework: Asynchronous batch processing for bulk operations, Partitionable jobs for scalability, Used for reindexing, cleanup, bulk exports") |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The FHIR specification provides inherent API versioning. HAPI FHIR supports multiple FHIR versions simultaneously — DSTU2, DSTU3, R4, R4B, and R5 — with separate structure modules for each version (`hapi-fhir-structures-dstu2`, `hapi-fhir-structures-r4`, etc.). Version selection is managed via `FhirVersionEnum` and `FhirContext`. The `hapi-fhir-server-openapi` module generates version-specific API documentation. The server can serve multiple FHIR versions on different URL paths simultaneously. Backward compatibility is maintained across FHIR version transitions. |
| **Gap** | None — the FHIR specification's inherent versioning combined with HAPI's multi-version support provides a best-in-class versioning strategy. |
| **Recommendation** | Continue the current multi-version support strategy. When deploying behind API Gateway, use path-based routing (`/fhir/r4/*`, `/fhir/r5/*`) to map FHIR versions to specific server instances or configurations. |
| **Evidence** | `hapi-fhir-structures-dstu2/`, `hapi-fhir-structures-dstu3/`, `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r4b/`, `hapi-fhir-structures-r5/`, `hapi-fhir-server-openapi/`, `CLAUDE.md` (FhirVersionEnum, FhirContext) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | HAPI FHIR is a monolithic application — service-to-service discovery in the microservices sense is not its primary concern. However, the application connects to external services (database endpoints, Elasticsearch endpoints, terminology servers, subscription delivery endpoints) via configuration. These endpoints are configured through Spring Boot properties or environment variables — functional but not using dynamic service discovery. No AWS Service Discovery, Consul, Istio, or service mesh configuration exists. |
| **Gap** | External service endpoints (database, Elasticsearch, terminology servers) are configured via environment variables or properties files. No dynamic discovery for database failover, Elasticsearch cluster changes, or load-balanced access to external terminology servers. |
| **Recommendation** | When deploying on AWS, use EKS service discovery (CoreDNS) for internal services, Aurora endpoints for automatic database failover, and Amazon OpenSearch Service endpoints for managed Elasticsearch. API Gateway can serve as a centralized catalog for the FHIR API surface. |
| **Evidence** | `hapi-fhir-spring-boot/` (Spring Boot autoconfigure with application.yml), `pom.xml` (Spring Boot 3.4.11), absence of service discovery or service mesh configurations |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | FHIR resources include Binary and Attachment types for storing unstructured data (documents, images, PDFs). HAPI FHIR stores these as BLOBs in the relational database via JPA/Hibernate. No S3 integration, document parsing pipeline (Textract, Tika), or object storage configuration exists. Binary resources are stored alongside structured FHIR data in the same database, which can impact database performance at scale. |
| **Gap** | Unstructured data (clinical documents, images, attachments) stored as database BLOBs rather than object storage. No parsing pipeline for document content extraction. |
| **Recommendation** | Implement S3-backed binary storage for FHIR Binary and Attachment resources. This offloads large objects from the database, reduces database storage costs, and enables content extraction via Amazon Textract for clinical document parsing. The existing storage abstraction layer in `hapi-fhir-storage` provides a clean integration point for S3 storage providers. |
| **Evidence** | `hapi-fhir-storage/` (abstract storage API), `hapi-fhir-jpa/` (JPA storage core with BLOB support), absence of S3 or object storage configuration |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | HAPI FHIR has an exemplary unified data access layer with multiple abstraction tiers: (1) `hapi-fhir-storage` provides abstract storage interfaces defining the data access contract; (2) `hapi-fhir-jpa` implements JPA/Hibernate storage core; (3) `hapi-fhir-jpaserver-base` contains JPA DAOs for all FHIR resource types; (4) `hapi-fhir-repositories` provides Spring Data repositories. All data access flows through this centralized DAO/Repository pattern — no scattered database connections. The interceptor chain provides hooks for auditing, authorization, and consent at the data access layer. |
| **Gap** | None — the data access layer is well-architected with clear separation of concerns. |
| **Recommendation** | Maintain the current DAO/Repository pattern. The abstraction layer already supports swapping database backends by changing driver and dialect configuration, making migration to Aurora PostgreSQL straightforward. |
| **Evidence** | `hapi-fhir-storage/`, `hapi-fhir-jpa/`, `hapi-fhir-jpaserver-base/`, `hapi-fhir-repositories/`, `CLAUDE.md` (DAO/Repository Pattern description) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database driver versions are explicitly pinned in `pom.xml`: PostgreSQL 42.7.7, MySQL Connector/J 9.1.0, MariaDB 3.0.4, MSSQL 12.4.3, Oracle ojdbc11 23.6.0.24.10, H2 2.3.232. All driver versions are current and not at EOL. Migration test resources reference specific database engine versions (e.g., `POSTGRES_9_4.sql`, `ORACLE_12C.sql`, `MSSQL_2012.sql` in migration test data) — these reference supported migration paths from older versions but the actual supported engine versions are current. However, no IaC pins database engine versions, and no documented version-update procedure exists. |
| **Gap** | Driver versions are pinned but no IaC defines database engine versions for deployments. Deployers may run any engine version without guidance. No documented version-update procedure covering downtime windows, rollback, and risk acknowledgment. |
| **Recommendation** | Document supported database engine versions (minimum and recommended) in deployment documentation. When IaC is created, explicitly pin engine versions (e.g., `engine_version = "15.4"` for Aurora PostgreSQL). Include a version-update procedure in operational runbooks. |
| **Evidence** | `pom.xml` (driver version properties), `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/releases/` (migration test data for multiple DB engines) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All business logic is in the Java application layer. Hibernate ORM handles data access via JPA entities and the DAO pattern. Flyway manages schema migrations through the `hapi-fhir-sql-migrate` module with Java-based migration tasks. No stored procedures, triggers, or proprietary SQL constructs were detected in the codebase. The migration SQL files contain DDL statements (CREATE TABLE, ALTER TABLE, CREATE INDEX) but no stored procedures or triggers. The application explicitly uses the JPA/Hibernate abstraction layer, making it database-engine-portable. |
| **Gap** | None — all business logic is in the application layer with no stored procedure dependencies. |
| **Recommendation** | Maintain the current approach. The ORM abstraction enables painless migration between database engines (e.g., from self-managed PostgreSQL to Aurora PostgreSQL) without stored procedure extraction or query rewriting. |
| **Evidence** | `hapi-fhir-sql-migrate/`, `hapi-fhir-jpa/`, `pom.xml` (Hibernate 6.6.4.Final, Flyway 10.20.1), migration SQL files in `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging infrastructure is defined — no IaC exists to configure any AWS audit services. The application uses SLF4J/Logback for application-level logging. The interceptor chain (`CLAUDE.md` references `AuthorizationInterceptor`, `ConsentInterceptor`) supports auditing hooks at the application layer, but no CloudTrail, CloudWatch Logs, or immutable log storage configuration exists. |
| **Gap** | No infrastructure-level audit logging. Healthcare FHIR servers require comprehensive audit trails for HIPAA compliance — who accessed what patient data, when, and from where. |
| **Recommendation** | Configure CloudTrail with log file validation and immutable storage (S3 with Object Lock). Configure CloudWatch Logs for application-level FHIR audit events. The existing interceptor chain provides application-level hooks — extend these to emit structured audit events to CloudWatch Logs for long-term retention and compliance analysis. |
| **Evidence** | Absence of `aws_cloudtrail` or CloudWatch Logs resources; `CLAUDE.md` (interceptor chain for authorization/consent); `pom.xml` (SLF4J 2.0.16, Logback 1.5.25) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS or encryption-at-rest configuration exists. No IaC defines encryption on data stores. No `kms_key_id`, `aws_kms_key`, or encryption configuration found for any data store. Healthcare FHIR data includes PHI (Protected Health Information) which requires encryption at rest under HIPAA. |
| **Gap** | No encryption at rest configured. Patient health records stored in the database are unencrypted at the infrastructure level (database-level encryption depends entirely on deployer configuration). |
| **Recommendation** | When provisioning Aurora PostgreSQL, enable encryption at rest with a customer-managed KMS key. Apply KMS encryption to all data stores: S3 buckets (for binary storage), EBS volumes, and CloudWatch Logs. Enable KMS key rotation and document the key management policy. |
| **Evidence** | Absence of any KMS or encryption resource definitions; no `encryption_configuration` in any IaC files |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | HAPI FHIR provides an authentication/authorization framework via interceptors — `AuthorizationInterceptor` and `ConsentInterceptor` are defined in `hapi-fhir-server` with CODEOWNERS protection by `@jamesagnew`. These interceptors provide hooks for per-request authorization decisions. However, no specific authentication mechanism is configured — no OAuth2/JWT validation, no Cognito integration, no API key validation. The framework enables auth but does not implement it. Authentication is left entirely to deployers. |
| **Gap** | Authentication framework exists (interceptors) but no specific authentication mechanism is configured. The FHIR server can be deployed without any authentication, exposing patient data. |
| **Recommendation** | Provide reference authentication configuration using Amazon Cognito with OAuth2/JWT validation at the API Gateway level (per preference: `prefer: ["api-gateway"]`). Document how to configure the `AuthorizationInterceptor` with JWT token validation for SMART on FHIR authorization. |
| **Evidence** | `.github/CODEOWNERS` (AuthorizationInterceptor, ConsentInterceptor protection), `CLAUDE.md` (restricted code for security classes), `hapi-fhir-server/` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration exists in the codebase. No Cognito, OIDC, SAML, or SSO configuration found. The interceptor chain supports identity integration (the framework can validate tokens passed by an external IdP), but no specific IdP configuration is provided. The FHIR healthcare standard defines SMART on FHIR for OAuth2-based authorization, but HAPI FHIR does not include a preconfigured SMART on FHIR implementation. |
| **Gap** | No centralized identity provider integration. Healthcare APIs require SMART on FHIR authorization for clinical data access — this is a standard requirement for EHR integration. |
| **Recommendation** | Integrate with Amazon Cognito as the centralized identity provider with SMART on FHIR scopes. Configure OIDC federation for clinical user authentication. Document the IdP configuration for deployers. |
| **Evidence** | Absence of Cognito, OIDC, SAML, or identity provider configuration in the repository |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS Secrets Manager, HashiCorp Vault, or other secrets management integration detected. No hardcoded secrets found in the visible source code (passwords, API keys, etc.). The Azure DevOps pipelines use Azure variable groups (`GPG_VARIABLE_GROUP`, `CENTRAL_VARIABLE_GROUP`) for CI/CD secrets, and GitHub Actions uses GitHub Secrets. However, no runtime secrets management solution is configured for deployed instances — database credentials, API keys, and other secrets management is left to deployers. |
| **Gap** | No runtime secrets management for deployed HAPI FHIR instances. Database credentials, Elasticsearch credentials, and email server passwords must be managed by deployers with no guidance. |
| **Recommendation** | Integrate with AWS Secrets Manager for runtime secrets (database credentials, Elasticsearch credentials, external service API keys). Configure automatic credential rotation for Aurora PostgreSQL. Provide reference Spring Boot configuration using AWS Secrets Manager integration. |
| **Evidence** | `snapshot-deploy-job.yml` (Azure variable groups for CI/CD secrets), `.github/workflows/` (GitHub Secrets for CI), absence of Secrets Manager or Vault runtime integration |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The build Dockerfile (`.github/docker/Dockerfile`) uses `maven:3.9-eclipse-temurin-21-jammy` — a well-maintained base image from the Eclipse Temurin project. Dependabot is configured for daily Maven dependency updates (`.github/dependabot.yml`), which catches vulnerable transitive dependencies. WhiteSource (`.whitesource`) scans for vulnerabilities at the `LOW` severity level. CodeQL analysis runs on push/PR/schedule. However, no production runtime hardening exists — no hardened base image for the FHIR server runtime, no SSM Patch Manager, no AWS Inspector configuration. |
| **Gap** | Build image uses a maintained base, and dependency scanning is active, but no runtime compute hardening exists. No hardened production base image, no patching automation for deployed instances. |
| **Recommendation** | For production deployment, use Amazon EKS with Bottlerocket nodes (hardened, minimal OS) or Fargate (no OS patching required). Use ECR image scanning for the production Docker image. Enable AWS Inspector for runtime vulnerability assessment. |
| **Evidence** | `.github/docker/Dockerfile` (Eclipse Temurin base image), `.github/dependabot.yml` (daily Maven scanning), `.whitesource` (LOW severity threshold), `.github/workflows/codeql-analysis.yml` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive application security pipeline with multiple scanning tools integrated into CI/CD: (1) **CodeQL SAST** — GitHub CodeQL analysis (`codeql-analysis.yml`) runs on every push, pull request, and on a weekly schedule (Monday 8 AM UTC), performing static analysis of Java source code. (2) **Dependabot** — configured for daily Maven dependency vulnerability scanning (`.github/dependabot.yml`). (3) **WhiteSource (Mend)** — vulnerability scanning at LOW severity level (`.whitesource`) with PR check run configured to fail on vulnerable dependencies. (4) **Checkstyle** — code quality validation integrated into CI pipeline. (5) **Error Prone** — static analysis via Maven profile (ERRORPRONE). Multiple scanning tools provide defense-in-depth for dependency and code vulnerabilities. |
| **Gap** | No container image scanning (ECR scanning) configured, but this is because no production container image exists yet. Once a production Dockerfile is created, container scanning should be added. |
| **Recommendation** | When the production Dockerfile is created, add ECR image scanning to the CI/CD pipeline. Consider adding DAST (Dynamic Application Security Testing) for the running FHIR server endpoints. The existing SAST + dependency scanning + vulnerability scanning provides excellent coverage. |
| **Evidence** | `.github/workflows/codeql-analysis.yml`, `.github/dependabot.yml`, `.whitesource`, `pom.xml` (checkstyle, error_prone_core), `.github/workflows/spotless.yml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry instrumentation annotations are declared as a global dependency across all 60+ modules in the root `pom.xml` (`io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations`). The OpenTelemetry instrumentation BOM (v2.10.0) is imported for version management. OpenTelemetry agent-for-testing (v2.10.0-alpha) is available for test verification of tracing instrumentation. This indicates active tracing instrumentation in the codebase — methods and operations are annotated for span creation. However, no trace propagation configuration or collector setup is defined in the repository. |
| **Gap** | Tracing annotations are present but no collector configuration, trace export setup, or trace propagation headers are configured. Deployers must configure the OpenTelemetry agent and collector independently. |
| **Recommendation** | Provide reference configuration for deploying HAPI FHIR with the OpenTelemetry Java agent, exporting traces to AWS X-Ray via the OpenTelemetry Collector. Document the trace propagation headers (W3C `traceparent`) for FHIR client-server trace correlation. |
| **Evidence** | `pom.xml` (global dependency: `opentelemetry-instrumentation-annotations`, BOM: `opentelemetry-instrumentation-bom` v2.10.0, test: `opentelemetry-agent-for-testing` v2.10.0-alpha) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definition files, error budget tracking, or formal service level definitions found in the repository. No CloudWatch alarms on p99/p95 latency, no SLO dashboards, no error budget policies. |
| **Gap** | No formal SLOs defined. Healthcare FHIR servers need defined service levels for clinical workflows — e.g., search response time SLOs, bulk export completion SLOs, subscription delivery latency SLOs. |
| **Recommendation** | Define SLOs for critical FHIR operations: search response p99 < 500ms, CRUD operation p99 < 200ms, bulk export completion within 1 hour for datasets < 1GB, subscription delivery latency < 5 seconds. Implement CloudWatch alarms and SLO dashboards. |
| **Evidence** | Absence of SLO definition files, CloudWatch alarm definitions, or error budget configurations |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics publishing detected. The application uses SLF4J/Logback for logging but no CloudWatch custom metrics, Prometheus metrics endpoints, or business KPI tracking. No `put_metric_data` calls, no Micrometer registry configuration, no metrics dashboards. |
| **Gap** | Only infrastructure metrics available. No FHIR-specific business metrics: resources created per hour, search queries per minute, subscription delivery success rate, bulk export throughput, validation errors by resource type. |
| **Recommendation** | Integrate Micrometer (available via Spring Boot actuator) to publish FHIR business metrics to CloudWatch: resource CRUD counts by type, search query rates, subscription delivery success/failure rates, batch job throughput, and validation error rates. These metrics are critical for capacity planning and clinical workflow monitoring. |
| **Evidence** | Absence of Micrometer, CloudWatch metrics, or business metric publishing in the codebase |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection, alerting configuration, or incident notification setup found. No CloudWatch anomaly detection, no static threshold alarms, no PagerDuty/OpsGenie integration. The Azure DevOps SNAPSHOT pipeline includes Slack failure notifications (`snapshot-deploy-job.yml`), but this covers build failures only — not runtime service health. |
| **Gap** | No runtime alerting for the deployed FHIR server. Error rate spikes, latency degradation, and database connection pool exhaustion would go undetected. |
| **Recommendation** | Configure CloudWatch anomaly detection on FHIR API error rates and p99 latency. Set static threshold alarms for database connection pool utilization, JVM heap usage, and Batch2 job failure rates. Integrate with PagerDuty or OpsGenie for on-call alerting. |
| **Evidence** | `snapshot-deploy-job.yml` (Slack notification for build failures only), absence of runtime alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists for service deployment. The CI/CD pipelines handle library artifact publishing to Maven Central (SNAPSHOT nightly, releases via Azure DevOps). The release pipeline (`release-pipeline.yml`) builds and publishes JAR artifacts but includes no service deployment stages. No blue/green, canary, rolling, or any other deployment strategy is defined for running HAPI FHIR as a service. |
| **Gap** | No deployment strategy for the FHIR server. Direct-to-production deployment with no staged rollout would be the default for deployers. |
| **Recommendation** | When deploying on EKS, implement blue/green or canary deployments using AWS CodeDeploy with EKS or ArgoCD Rollouts. Healthcare workloads cannot tolerate deployment-related outages — staged rollouts with automatic rollback on health check failures are essential. |
| **Evidence** | `release-pipeline.yml` (artifact publishing only), `snapshot-deploy-job.yml` (Maven Central deployment), absence of service deployment configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive integration test infrastructure: (1) JUnit 5 with parallel per-module testing in CI (up to 256 parallel jobs via `parallel-pipeline-build.yml`). (2) Testcontainers (v2.0.2) for database integration testing against real database instances. (3) Dedicated integration test modules per FHIR version (`hapi-fhir-jpaserver-test-dstu2`, `hapi-fhir-jpaserver-test-dstu3`, `hapi-fhir-jpaserver-test-r4`, `hapi-fhir-jpaserver-test-r4b`, `hapi-fhir-jpaserver-test-r5`). (4) Maven Failsafe plugin configured for integration tests (`*IT.java`). (5) ~50 integration test classes and ~1543 unit test classes found. (6) JPA test utilities providing base test classes (`BaseJpaR4Test`, etc.). (7) Storage test utilities for storage layer testing. (8) Elasticsearch test utilities (`hapi-fhir-jpaserver-elastic-test-utilities`). (9) ArchUnit for architecture compliance testing. All tests run in the CI pipeline on every pull request. |
| **Gap** | None — integration testing is comprehensive with per-FHIR-version coverage, database integration via Testcontainers, and CI execution. |
| **Recommendation** | Maintain the excellent test infrastructure. When deploying on AWS, consider adding smoke tests that verify the deployed FHIR server health against real Aurora and OpenSearch endpoints (post-deployment verification). |
| **Evidence** | `.github/workflows/parallel-pipeline-build.yml` (256 parallel test jobs), `pom.xml` (Testcontainers 2.0.2, JUnit 5.11.4, Failsafe 3.5.2, ArchUnit 1.3.0), `hapi-fhir-jpaserver-test-dstu2/` through `hapi-fhir-jpaserver-test-r5/`, `hapi-fhir-jpaserver-test-utilities/`, `hapi-fhir-storage-test-utilities/`, `hapi-fhir-jpaserver-elastic-test-utilities/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automation documents, or incident response workflows found. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The only automated notification is Slack alerts for SNAPSHOT build failures in Azure DevOps. |
| **Gap** | No incident response infrastructure for runtime FHIR server operations. Database connection failures, JVM memory issues, and search index corruption would require entirely manual remediation. |
| **Recommendation** | Create runbooks for common FHIR server incidents: database connection pool exhaustion (auto-restart), Elasticsearch index corruption (trigger reindex via Batch2), out-of-memory (auto-scale or restart), and subscription delivery backlog (scale consumers). Implement as SSM Automation documents for self-healing. |
| **Evidence** | Absence of runbook files, SSM documents, or incident automation; `snapshot-deploy-job.yml` (Slack notification for build failures only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CODEOWNERS defines ownership for key modules — data migrations (`@hapifhir/data-migrations`), CLI (`@nathandoef @tadgh @jamesagnew`), subscriptions (`@fil512 @tadgh @jamesagnew`), MDM (`@fil512 @tadgh @ad1306`), batch2 (`@michaelabuckley @jamesagnew @tadgh`), and security interceptors (`@jamesagnew`). This provides code ownership attribution but no observability ownership — no per-service dashboards, no alarm definitions with named owners, no SLO definitions with team attribution. |
| **Gap** | Code ownership exists but observability ownership does not. Alarms, dashboards, and SLOs are not defined, so they cannot be assigned to owners. |
| **Recommendation** | When deploying on AWS, create per-module CloudWatch dashboards with named owners matching CODEOWNERS. For example: batch2 dashboard owned by `@michaelabuckley`, subscription delivery dashboard owned by `@fil512`, search performance dashboard owned by the JPA server team. |
| **Evidence** | `.github/CODEOWNERS` (module ownership definitions), absence of dashboard or alarm definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging — no IaC exists to define tags on resources. No `default_tags` in Terraform provider, no `tags` on CloudFormation resources, no tag policies or enforcement rules. |
| **Gap** | No resource tagging baseline. Healthcare workloads require tagging for cost allocation by clinical department, HIPAA compliance tracking, and environment identification. |
| **Recommendation** | When creating IaC, define a tagging standard with required tags: `Environment` (dev/staging/prod), `Service` (hapi-fhir), `Owner` (team name), `CostCenter` (department), `Compliance` (hipaa), `FhirVersion` (r4/r5). Enforce via CDK aspects or Terraform required tags. Enable AWS Config rules for tag compliance. |
| **Evidence** | Absence of any IaC with resource tags |

---

## Learning Materials

The following learning resources correspond to the 3 triggered modernization pathways:

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q6, INF-Q11, APP-Q1, APP-Q2, APP-Q4, APP-Q5, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q6 | Root Maven POM with 60+ modules, dependency versions, build plugins, Java 17 configuration |
| `.github/workflows/pull-request.yml` | INF-Q11, OPS-Q6 | PR pipeline triggering parallel module testing |
| `.github/workflows/parallel-pipeline-build.yml` | INF-Q11, OPS-Q6 | Reusable workflow with up to 256 parallel test jobs, checkstyle, Codecov |
| `.github/workflows/release.yml` | INF-Q11 | Release workflow with version normalization and tag verification |
| `.github/workflows/spotless.yml` | INF-Q11, SEC-Q7 | Code formatting validation on pull requests |
| `.github/workflows/codeql-analysis.yml` | INF-Q11, SEC-Q7 | CodeQL SAST analysis on push/PR/schedule |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Daily Maven dependency vulnerability scanning |
| `.whitesource` | SEC-Q6, SEC-Q7 | WhiteSource/Mend vulnerability scanning at LOW severity |
| `.github/docker/Dockerfile` | INF-Q1, SEC-Q6 | Build-only Docker image (Maven + GPG for publishing) |
| `.github/CODEOWNERS` | APP-Q2, SEC-Q3, OPS-Q8 | Module ownership for batch2, subscriptions, MDM, security interceptors |
| `.pre-commit-config.yaml` | INF-Q11 | Pre-push hook for Spotless formatting |
| `release-pipeline.yml` | INF-Q11, OPS-Q5 | Azure DevOps release pipeline with full build (360-min timeout) |
| `snapshot-pipeline.yml` | INF-Q11 | Nightly SNAPSHOT publish schedule |
| `snapshot-deploy-job.yml` | INF-Q11, OPS-Q4, OPS-Q5, OPS-Q7, SEC-Q5 | SNAPSHOT deployment to Maven Central with GPG signing, Slack failure alerts |
| `CLAUDE.md` | INF-Q3, INF-Q4, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, DATA-Q2, SEC-Q1, SEC-Q3 | Architectural description — layers, patterns, batch2 framework, interceptor chain, security |
| `README.md` | Quick Agent Wins | Project overview, CI/CD badges, documentation links |
| `hapi-fhir-storage-batch2/` | INF-Q3, APP-Q4, Quick Agent Wins | Batch2 job framework for async processing |
| `hapi-fhir-storage-batch2-jobs/` | INF-Q3, APP-Q4 | Batch2 job definitions (reindex, bulk export, cleanup) |
| `hapi-fhir-jpaserver-subscription/` | INF-Q4, APP-Q3 | FHIR subscription delivery (REST-hooks, email, WebSocket) |
| `hapi-fhir-server-openapi/` | INF-Q6, APP-Q5, Quick Agent Wins | OpenAPI/Swagger documentation module |
| `hapi-fhir-server/` | APP-Q3, SEC-Q3 | REST server framework with interceptor chain |
| `hapi-fhir-storage/` | DATA-Q1, DATA-Q2 | Abstract storage API defining data access contracts |
| `hapi-fhir-jpa/` | DATA-Q2, DATA-Q4 | JPA/Hibernate storage core |
| `hapi-fhir-jpaserver-base/` | DATA-Q2 | JPA DAOs for all FHIR resource types |
| `hapi-fhir-repositories/` | DATA-Q2 | Spring Data repositories |
| `hapi-fhir-sql-migrate/` | INF-Q8, DATA-Q3, DATA-Q4 | Flyway database migration module |
| `hapi-fhir-structures-dstu2/` through `hapi-fhir-structures-r5/` | APP-Q5 | FHIR version-specific structure modules |
| `hapi-fhir-jpaserver-test-dstu2/` through `hapi-fhir-jpaserver-test-r5/` | OPS-Q6 | Per-FHIR-version integration test modules |
| `hapi-fhir-jpaserver-test-utilities/` | OPS-Q6, DATA-Q3 | JPA test base classes and migration test data |
| `hapi-fhir-jpaserver-elastic-test-utilities/` | OPS-Q6 | Elasticsearch test utilities |
| `hapi-fhir-spring-boot/` | APP-Q6 | Spring Boot autoconfigure with application.yml |
| `hapi-fhir-docs/` | Quick Agent Wins | Documentation module with changelogs and upgrade guides |
