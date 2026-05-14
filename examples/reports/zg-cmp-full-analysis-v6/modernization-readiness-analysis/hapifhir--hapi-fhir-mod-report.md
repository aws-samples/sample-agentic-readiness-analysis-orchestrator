# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | hapifhir--hapi-fhir |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, healthcare, rest-api |
| **Context** | Open-source Java implementation of the HL7 FHIR healthcare standard. |
| **Overall Score** | 2.35 / 4.0 |

**Archetype Justification**: The project implements a FHIR JPA server with full CRUD operations on healthcare resources (Patient, Encounter, Observation, etc.), uses JPA/Hibernate persistence with multiple database backends (PostgreSQL, Oracle, MSSQL, MySQL), and manages entity lifecycle through a two-tier DAO pattern. Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.17 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 2.25 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.35 / 4.0** | **🟠 Needs Work** | — |

**Scoring Notes:**
- INF: (1+1+2+2+1+1+1+1+1+2+2) / 11 = 16/11 = 1.45
- APP: (4+2+3+3+2+3) / 6 = 17/6 = 2.83
- DATA: (2+3+3+4) / 4 = 13/4 = 3.25
- SEC: (1+NE+2+1+3+2+3) / 6 = 13/6 = 2.17 (SEC-Q2 Not Evaluated, excluded)
- OPS: (3+NE+2+1+1+3+1+2+1) / 8 = 18/8 = 2.25 (OPS-Q2 Not Evaluated, excluded)

---

## Classification

**Tier: 🟠 Remediation Required**

**Rule Matched:** 2-11 High → Remediation Required

This repo has 7 High findings, 5 Medium findings, 5 Low findings. Under MOD classification rules, 2-11 High findings map to "Remediation Required." Note: MOD classification is deliberately softer than ARA classification on "1 High" — ARA gates on agent safety (a single High is a deployment blocker), whereas MOD measures modernization maturity (a single High is typically one modernization gap rather than a deployment blocker, mapping to Pilot-Ready instead of Remediation Required).

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute infrastructure defined — no ECS/EKS/Lambda/Fargate | Cannot deploy to cloud-native compute without full containerization effort |
| 2 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined | No network isolation for deployed workloads |
| 3 | INF-Q10: Infrastructure as Code | 1 | Zero IaC coverage — all infrastructure would be manual | No reproducible deployments, no disaster recovery automation |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging infrastructure defined | No compliance audit trail for healthcare data |
| 5 | SEC-Q4: Centralized Identity | 1 | No centralized IdP integration defined | No SSO or federated identity for deployed instances |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — extensive `hapi-fhir-docs` module, README.md, CLAUDE.md, changelog YAML files, and FHIR specification references throughout the codebase.
- **What it enables:** A knowledge agent that indexes HAPI FHIR documentation, FHIR specification details, and code-level documentation to answer developer questions about configuration, deployment, and FHIR resource handling.
- **Additional steps:** Index the `hapi-fhir-docs` module content and CLAUDE.md into a vector store; configure Amazon Bedrock for retrieval-augmented generation.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2) — GitHub Actions workflows and Azure DevOps pipelines are configured with build and test stages.
- **What it enables:** An agent that triggers builds, monitors test results across the 256-parallel module test matrix, identifies flaky tests, and reports build status.
- **Additional steps:** Expose GitHub Actions API and Azure DevOps API as agent tools; configure appropriate service account permissions.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured tracing in place (OPS-Q1 = 3) — OpenTelemetry 2.10.0 instrumentation is integrated.
- **What it enables:** An agent that queries traces, correlates performance issues across FHIR operations, and suggests optimization targets (e.g., slow search parameter indexing, heavy batch operations).
- **Additional steps:** Deploy OpenTelemetry collector with queryable backend (X-Ray, Jaeger); expose trace query API as agent tool.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=3 (primary + supporting met) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no container definitions found for deployment |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); commercial DB drivers present but logic is portable |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (no managed DB infrastructure defined) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected; no streaming/ETL artifacts |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=1, OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** HAPI FHIR is a large monolithic Java application (60+ Maven modules compiled as a single deployable unit). While it has modular internal structure (APP-Q2=2), modules share a database schema and have cross-module data access patterns. The JPA server, subscriptions, MDM, batch processing, and search indexing are all deployed as one unit.

**Compute Model Gaps:** No managed compute infrastructure exists (INF-Q1=1). The project has no Dockerfiles for deployment, no Kubernetes manifests, and no IaC defining compute resources.

**Communication Pattern Gaps:** Internal Spring messaging is used for FHIR Subscriptions (REST-hooks, email, WebSocket) but there is no external async messaging infrastructure for cross-service communication (APP-Q3=3 due to archetype — internal messaging exists but no managed external messaging).

**Recommended Decomposition Approach:** Given the monolithic architecture with identifiable module boundaries, a Strangler Fig (Parallel Track) approach is recommended. See Decomposition Strategy section below.

**Representative AWS Services:** EKS (preferred per context), API Gateway, EventBridge (preferred per context), Aurora (preferred per context), DynamoDB (preferred per context)

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Hexagonal Architecture

**References:**
- [AWS Prescriptive Guidance: Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** No deployment infrastructure exists. The only Dockerfile is a CI build image (`.github/docker/Dockerfile` for Maven builds), not a runtime container. No docker-compose for local development, no Kubernetes manifests, no Helm charts.

**Container Readiness Indicators:**
- Spring Boot 3.4.11 with embedded server (Jetty 12) — ready for containerization
- Configuration externalized via Spring Boot properties/YAML — container-friendly
- Database connections configurable via environment variables
- No file-system dependencies that would block containerization
- Maven build produces deployable JAR/WAR artifacts

**Recommended Container Orchestration:** Amazon EKS (preferred per context preferences). Deploy HAPI FHIR as a containerized Spring Boot application on EKS with:
- Multi-replica deployment for high availability
- HPA for auto-scaling based on request volume
- Service mesh (Istio/App Mesh) for traffic management

**Representative AWS Services:** EKS, ECR, Fargate (as EKS node type)

**Migration Approach:** Lift-and-containerize first (create Dockerfile, Helm chart, EKS deployment), then refactor for cloud-native patterns (externalize config to ConfigMaps/Secrets, add health probes, configure resource limits).

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** The application supports multiple database engines (PostgreSQL, Oracle, MSSQL, MySQL/MariaDB, H2) but no managed database infrastructure is defined. Database connections are configured at deployment time with no IaC provisioning.

**Engine Versions and EOL:** Database drivers are current (PostgreSQL 42.7.7, MySQL 9.1.0, Oracle 23.6.0.24.10, MSSQL 12.4.3) but no engine version pinning or lifecycle management exists in IaC.

**Data Access Patterns:** Two-tier DAO pattern with Spring Data JPA repositories (lower tier) and HAPI-specific DAOs (upper tier). The data access layer is fully centralized and database-portable — no stored procedures, no proprietary SQL.

**Recommended Managed Database Targets:**
- **Aurora PostgreSQL** (preferred per context) — primary recommendation given PostgreSQL is the most commonly used backend
- **DynamoDB** (preferred per context) — for specific use cases like session management, caching, or FHIR resource metadata if decomposed
- Avoid Oracle managed (per context preferences)

**Representative AWS Services:** Aurora PostgreSQL, DynamoDB, ElastiCache/MemoryDB (for caching layer)

**Migration Tools:** AWS DMS for data migration; no schema conversion needed (no stored procedures or proprietary SQL)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** Zero infrastructure defined in code. All deployment infrastructure is provisioned manually or not at all. No Terraform, CloudFormation, CDK, or Helm charts exist.

**Current CI/CD State (INF-Q11=2):** Dual CI/CD pipelines exist (GitHub Actions + Azure DevOps) with automated build and test stages (256-parallel module testing). However, there is no automated deployment stage — releases are published to Maven Central/Sonatype but there is no infrastructure deployment automation.

**Deployment Strategy Gaps (OPS-Q5=1):** No deployment strategy exists — no blue/green, no canary, no rolling updates. Releases are library publishes, not service deployments.

**Testing Gaps (OPS-Q6=3):** Integration tests exist using Testcontainers (PostgreSQL, MSSQL, Oracle, Elasticsearch) and run in CI. Coverage is good but not comprehensive across all critical FHIR workflows.

**Recommended DevOps Toolchain:**
- **IaC:** CDK or Terraform for EKS cluster, Aurora, networking
- **CI/CD:** Extend GitHub Actions with deployment stages (build → test → deploy to EKS)
- **Deployment:** ArgoCD or Flux for GitOps-based EKS deployment with canary releases
- **Observability:** CloudWatch + X-Ray integration with existing OpenTelemetry

**Representative AWS Services:** CodePipeline, CodeBuild, CDK, CloudFormation, X-Ray, CloudWatch

---

## Decomposition Strategy

APP-Q2 scored 2 (monolith with identifiable modules but shared database schemas). The application has clear module boundaries (60+ Maven modules with defined responsibilities) but deploys as a single unit with shared database access.

### Recommended Approach: Strangler Fig (Parallel Track)

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Identifiable module boundaries exist (hapi-fhir-jpaserver-subscription, hapi-fhir-storage-batch2, hapi-fhir-jpaserver-mdm) | Medium to High | ✅ **Recommended.** Extract high-value modules incrementally. |
| **Conditional / Adaptive** | Start with containerizing the monolith, selectively extract later | Low to Medium | ✅ **Also viable.** Containerize first, decompose high-value modules based on scaling needs. |
| **Big-Bang Rewrite** | — | Very High | ⚠️ **Not recommended.** The monolith is functional and well-structured. |

### Candidate Services for Extraction

Based on module analysis, these are high-value extraction candidates:

1. **Subscription Service** (`hapi-fhir-jpaserver-subscription`) — Already isolated with clear boundaries; handles FHIR Subscription delivery (REST-hooks, email, WebSocket). Natural fit for EventBridge (preferred).
2. **Batch Processing Service** (`hapi-fhir-storage-batch2`) — Custom workflow engine with job coordination. Natural fit for Step Functions or standalone EKS service.
3. **MDM Service** (`hapi-fhir-jpaserver-mdm`) — Master Data Management with dedicated CODEOWNERS. Clear domain boundary.
4. **Search/Indexing Service** (`hapi-fhir-jpaserver-searchparam` + Hibernate Search) — Could be extracted as a dedicated Elasticsearch/OpenSearch service.

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's shared database model | Every extraction — translate between monolith entity model and service-specific model |
| **Saga Pattern** | Manage distributed transactions (e.g., resource creation + subscription notification + index update) | When extracting subscription and batch services that participate in multi-step operations |
| **Event Sourcing** | Capture FHIR resource changes as events for downstream services | When extracting subscription service — FHIR already has a "history" concept that maps naturally to event sourcing |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters | Every new service — especially important for the multi-database support pattern |

### Effort Estimation

| Factor | Signal | Impact |
|--------|--------|--------|
| Module boundaries | Clear (60+ modules with defined responsibilities, CODEOWNERS) | Low effort for boundary identification |
| Data coupling | High (shared database schemas, cross-module JPA entity access) | High effort for data separation |
| Stored procedures | None (all logic in Java) | Low effort — no database logic extraction needed |
| Communication patterns | Internal Spring messaging exists | Medium effort — convert to managed external messaging |
| CI/CD maturity | Build/test automated, no deployment pipeline | Medium effort — need deployment automation first |
| Test coverage | Testcontainers integration tests exist | Low risk during extraction |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure is defined. The repository contains no Terraform, CloudFormation, CDK, ECS task definitions, EKS configurations, or Lambda function definitions. The only Dockerfile (`.github/docker/Dockerfile`) is a CI build image, not a runtime container. |
| **Gap** | All compute infrastructure is undefined — no managed container orchestration or serverless compute. Deployment model is entirely manual. |
| **Recommendation** | Define EKS cluster infrastructure in CDK/Terraform. Create a production Dockerfile for the Spring Boot application. Deploy on EKS with Fargate node pools for the FHIR server workload. |
| **Evidence** | `.github/docker/Dockerfile` (build-only); absence of any `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` resources |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed database infrastructure is defined. The application supports PostgreSQL, Oracle, MSSQL, MySQL/MariaDB, and H2 via JDBC drivers in `pom.xml`, but no IaC provisions any database instance. Database connections are configured at deployment time with no managed service definitions. |
| **Gap** | All databases would be self-managed or manually provisioned. No RDS, Aurora, or DynamoDB resources defined. |
| **Recommendation** | Provision Aurora PostgreSQL (preferred) via IaC with Multi-AZ, automated backups, and auto-scaling. Use DynamoDB for session/cache workloads. Avoid Oracle (per preferences). |
| **Evidence** | Root `pom.xml` database driver dependencies (PostgreSQL 42.7.7, Oracle 23.6.0.24.10, MSSQL 12.4.3, MySQL 9.1.0); absence of any `aws_rds_*`, `aws_dynamodb_*` resources |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `hapi-fhir-storage-batch2` module implements a custom workflow orchestration framework with job definitions, work chunk processing, reduction steps, and progress tracking. This is a bespoke solution — not Step Functions, Temporal, or any managed orchestration service. The framework handles multi-step batch operations (reindexing, bulk export, MDM matching). |
| **Gap** | Workflow orchestration exists but is entirely custom with no managed service backing. The custom Batch2 framework requires operational maintenance and lacks the visibility/debugging capabilities of managed orchestration. |
| **Recommendation** | Evaluate migrating the Batch2 framework to AWS Step Functions for job coordination, or maintain the custom framework but deploy it on managed compute (EKS) with proper monitoring. Step Functions would provide visual workflow management, built-in retry/error handling, and operational dashboards. |
| **Evidence** | `hapi-fhir-storage-batch2/` module (JobCoordinatorImpl, WorkChunk, JobDefinition, ReductionStepExecutorServiceImpl) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses Spring's internal messaging framework (`spring-messaging`, `spring-websocket`) for FHIR Subscription delivery (REST-hooks, email, WebSocket). The Batch2 framework uses channel-based messaging (`BatchJobSender`) for work distribution. However, there is no external managed messaging infrastructure (no SQS, SNS, EventBridge, MSK, or Kinesis). |
| **Gap** | Messaging is entirely in-process via Spring's messaging abstraction. For a stateful-crud service with cross-service state changes (subscription notifications, batch job distribution), managed external messaging should be in place for reliability and decoupling. |
| **Recommendation** | Adopt EventBridge (preferred) for FHIR Subscription event distribution and SQS for Batch2 work chunk queuing. This provides durability, retry, and dead-letter queue capabilities that in-process messaging lacks. |
| **Evidence** | `hapi-fhir-jpaserver-subscription/` (Spring messaging channels); `hapi-fhir-storage-batch2/` (BatchJobSender); absence of SQS/SNS/EventBridge/MSK dependencies in pom.xml |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security infrastructure is defined. No VPC, subnets, security groups, NACLs, or network segmentation configuration exists in the repository. |
| **Gap** | Network isolation is entirely undefined. A healthcare application handling PHI/PII would require strict network segmentation. |
| **Recommendation** | Define VPC with private subnets for EKS worker nodes and Aurora databases. Use security groups with least-privilege rules. Deploy VPC endpoints for AWS service access (S3, ECR, CloudWatch) to keep traffic off the public internet. |
| **Evidence** | Absence of any `aws_vpc`, `aws_subnet`, `aws_security_group` resources or network configuration files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API gateway, load balancer, or CloudFront distribution is defined. The application uses embedded Jetty 12 as its HTTP server but has no managed entry point infrastructure. |
| **Gap** | Direct service exposure with no throttling, authentication gateway, or request validation at the edge. For a healthcare REST API, this is a significant operational and security gap. |
| **Recommendation** | Deploy API Gateway (preferred) in front of the FHIR server for throttling, authentication, request validation, and usage tracking. Alternatively, use an ALB with WAF rules for healthcare-specific protections. |
| **Evidence** | Jetty 12.0.32 dependency in pom.xml (embedded server); absence of `aws_api_gateway_*`, `aws_lb_*` resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No ASG, ECS service scaling, EKS HPA, or Lambda concurrency settings are defined. |
| **Gap** | All capacity would be statically provisioned. A FHIR server handling variable clinical workloads needs elastic scaling. |
| **Recommendation** | Configure Kubernetes HPA on EKS for the FHIR server pods based on request rate and response latency. Configure Aurora auto-scaling for read replicas. |
| **Evidence** | Absence of any `aws_autoscaling_*`, `aws_appautoscaling_*` resources |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup or recovery configuration exists. No automated backup plans, retention periods, or point-in-time recovery settings are defined. |
| **Gap** | Healthcare data requires robust backup and recovery capabilities. No backup infrastructure means potential permanent data loss. |
| **Recommendation** | Configure Aurora automated backups with 35-day retention and PITR. Enable DynamoDB PITR. Create AWS Backup plans for all data stores with cross-region replication for disaster recovery. |
| **Evidence** | Absence of `aws_backup_plan`, `backup_retention_period`, or `point_in_time_recovery` configurations |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration exists. No availability zone configuration, cross-zone load balancing, or fault isolation patterns are defined. |
| **Gap** | Single point of failure risk. Healthcare systems require high availability for patient care continuity. |
| **Recommendation** | Deploy EKS across 3 AZs. Configure Aurora Multi-AZ with automatic failover. Ensure all stateful components span multiple AZs. |
| **Evidence** | Absence of `multi_az`, `availability_zones`, or cross-AZ deployment configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. All infrastructure would need to be created manually (ClickOps). |
| **Gap** | 0% IaC coverage. No reproducible deployments, no environment consistency, no disaster recovery automation. |
| **Recommendation** | Adopt CDK or Terraform to define all infrastructure: EKS cluster, Aurora PostgreSQL, VPC/networking, API Gateway, monitoring, and backup plans. Start with a reference architecture and iterate. |
| **Evidence** | Absence of `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dual CI/CD pipelines exist: GitHub Actions (7 workflows including PR builds with 256-parallel module testing, CodeQL security scanning, spotless formatting) and Azure DevOps (release pipeline, snapshot pipelines with GPG-signed Maven Central deployment). Build and test stages are automated, but there is no infrastructure deployment automation — releases publish library artifacts to Maven Central, not deploy services. |
| **Gap** | Build is automated but deployment is manual. No automated infrastructure or service deployment pipeline exists. The pipelines only handle library publishing, not service deployment to cloud infrastructure. |
| **Recommendation** | Extend the CI/CD pipeline with deployment stages: container image build → push to ECR → deploy to EKS via ArgoCD/Flux (GitOps). Add infrastructure deployment via CDK/Terraform in a separate pipeline. |
| **Evidence** | `.github/workflows/parallel-pipeline-build.yml`, `.github/workflows/release.yml`, `release-pipeline.yml`, `snapshot-pipeline.yml`, `snapshot-deploy-job.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 17 with Spring Boot 3.4.11, Spring Framework 6.2.12, Hibernate 6.6.4, and Jakarta EE namespace (fully migrated from javax). The technology stack is on the latest generation across all axes — language version, framework, and ORM. AWS SDK usage is minimal (only `hibernate-search-backend-elasticsearch-aws` for OpenSearch integration). |
| **Gap** | N/A — the technology stack is fully modern. |
| **Recommendation** | N/A — no action needed. The stack is current-generation Java with first-class AWS SDK coverage available when needed. |
| **Evidence** | Root `pom.xml` (maven.compiler.release=17, spring-boot.version=3.4.11, spring.version=6.2.12, hibernate.version=6.6.4.Final) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a monolith with identifiable modules. 60+ Maven modules compile into a single deployable unit. Modules have clear responsibilities (JPA server, subscriptions, MDM, batch processing, search, validation) with CODEOWNERS defining team ownership. However, modules share a database schema (common JPA entities in `hapi-fhir-jpaserver-model`), have cross-module data access through shared DAO layers, and deploy as one artifact. |
| **Gap** | Shared database schemas and cross-module entity access prevent independent deployment. The `ResourceTable` and related entities are accessed from subscription, MDM, batch, and search modules, creating tight data coupling. |
| **Recommendation** | Begin Strangler Fig decomposition starting with the Subscription service (clearest boundary, event-driven nature fits EventBridge). Define service contracts between modules before extraction. See Decomposition Strategy section. |
| **Evidence** | `hapi-fhir-jpaserver-model/` (shared JPA entities), `hapi-fhir-jpaserver-subscription/`, `hapi-fhir-storage-batch2/`, `hapi-fhir-jpaserver-mdm/`, `.github/CODEOWNERS` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | For a stateful-crud service, communication patterns are appropriate. The application uses synchronous HTTP for FHIR REST operations (correct for CRUD) and internal Spring messaging for asynchronous FHIR Subscription delivery (REST-hooks, email, WebSocket) and Batch2 work chunk distribution. Async is available for key workflows (subscription notification, batch processing) while reads and CRUD operations remain synchronous. |
| **Gap** | Async messaging is in-process (Spring channels) rather than on managed external infrastructure. For cross-service state propagation in a production deployment, this limits durability and observability. |
| **Recommendation** | When decomposing into services, adopt EventBridge for FHIR resource change events and SQS for reliable work distribution. The existing async patterns (subscriptions, batch) map naturally to managed messaging. |
| **Evidence** | `hapi-fhir-jpaserver-subscription/` (Spring messaging channels for REST-hooks, email, WebSocket); `hapi-fhir-storage-batch2/` (BatchJobSender channel-based work distribution) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Batch2 framework (`hapi-fhir-storage-batch2`) handles long-running operations asynchronously with status tracking. Operations like bulk export, reindexing, and MDM batch matching are processed as background jobs with work chunks, progress tracking (`InstanceProgress`), and status polling. FHIR `$export` and `$reindex` operations return immediately with a job ID for status polling. |
| **Gap** | While the Batch2 framework handles async jobs, some operations (large FHIR searches, transaction bundles) can still be synchronous and potentially long-running without explicit timeout handling or async fallback. |
| **Recommendation** | Ensure all operations that may exceed 30 seconds have async alternatives. For large transaction bundles, consider async processing with status callbacks. The existing Batch2 pattern is a good foundation — extend it to cover more operation types. |
| **Evidence** | `hapi-fhir-storage-batch2/` (JobCoordinatorImpl, WorkChunk, InstanceProgress, JobDefinition); FHIR async patterns ($export, $reindex) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No traditional REST API versioning (/v1/, /v2/, version headers) is used. The application versions by FHIR specification version (DSTU2, DSTU3, R4, R4B, R5) which is determined at deployment time by which structures module is loaded — not by URL path. This is a domain-specific versioning approach rather than a standard API versioning strategy. |
| **Gap** | No explicit API versioning mechanism for the REST surface beyond the FHIR specification version. Breaking changes to the FHIR REST API cannot be versioned independently of the full FHIR specification version. Custom operations and extensions have no versioning scheme. |
| **Recommendation** | Implement API versioning for custom operations and non-FHIR endpoints (e.g., admin APIs, metrics endpoints). Consider header-based versioning to maintain FHIR specification compliance while supporting API evolution. |
| **Evidence** | `hapi-fhir-structures-{dstu2,dstu3,r4,r4b,r5}/` modules; absence of `/v1/`, `/v2/` URL patterns in server configuration |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | As a single deployable monolith, internal service discovery is handled via Spring dependency injection (beans are discovered and wired at startup). External service endpoints (Elasticsearch, database) are configured via Spring Boot properties/YAML which can be externalized to environment variables at deployment time. No hard-coded service endpoints in application code. |
| **Gap** | Service discovery is configuration-based (environment variables/properties) rather than dynamic. If decomposed into microservices, dynamic service discovery would be needed. |
| **Recommendation** | When deploying on EKS, leverage Kubernetes service discovery (DNS-based). For cross-namespace or cross-cluster discovery, use AWS Cloud Map or service mesh (App Mesh/Istio). |
| **Evidence** | `hapi-fhir-spring-boot/` (Spring Boot auto-configuration); `application.yml` samples (externalized config); Spring DI for internal wiring |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | FHIR resources including Binary resources (documents, images, PDFs) are stored in the database via JPA entities. The application supports FHIR Binary and DocumentReference resources for unstructured data, but storage is in the relational database (as BLOBs or base64-encoded content), not in S3 or object storage. |
| **Gap** | Unstructured clinical data (documents, images, attachments) stored in RDBMS rather than managed object storage. This limits scalability and increases database costs for large clinical document repositories. |
| **Recommendation** | Implement an S3-backed Binary storage provider. HAPI FHIR supports pluggable Binary storage — configure it to store Binary resource content in S3 with metadata in the database. Add Textract integration for clinical document parsing. |
| **Evidence** | JPA entity model storing Binary content; `hapi-fhir-jpaserver-base/` (Binary resource DAO); absence of S3 configuration |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a well-structured two-tier DAO pattern: Spring Data JPA repositories (lower tier, e.g., `IResourceTableDao`) handle raw data access with `@Query` annotations, and HAPI-specific DAOs (upper tier, e.g., `JpaResourceDao`, `BaseHapiFhirDao`) provide FHIR-level business logic. All database access goes through this unified pattern. |
| **Gap** | While mostly centralized, there is some direct data access in auxiliary code paths (e.g., `HealthMarketScience SQLBuilder` for programmatic query construction in search parameter indexing, `datasource-proxy` for query tracing). The unified layer is strong but not absolute. |
| **Recommendation** | Continue maintaining the two-tier DAO pattern. When decomposing services, ensure each extracted service maintains its own clean data access layer with clear contracts. |
| **Evidence** | `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/dao/` (BaseHapiFhirDao, JpaResourceDao); `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/dao/data/` (Spring Data repositories) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Database driver versions are explicitly pinned in the root `pom.xml`: PostgreSQL 42.7.7, Oracle 23.6.0.24.10, MSSQL 12.4.3.jre11, MySQL 9.1.0, MariaDB 3.0.4, H2 2.3.232. All drivers are current versions. Migration files reference minimum database versions (PostgreSQL 9.4, Oracle 12C, MSSQL 2012) which are near or past EOL. |
| **Gap** | Migration files still reference older database versions (PostgreSQL 9.4 EOL Feb 2020, Oracle 12C EOL Jul 2022, MSSQL 2012 EOL Jul 2022) as minimum supported versions. While drivers are current, the minimum supported engine versions include EOL platforms. No documented version-update procedure. |
| **Recommendation** | Update minimum supported database versions to exclude EOL engines. Document a version-update procedure covering downtime windows, rollback, and risk acknowledgment. When deploying on Aurora PostgreSQL, target the latest engine version. |
| **Evidence** | Root `pom.xml` (driver version properties); `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/` (POSTGRES_9_4.sql, ORACLE_12C.sql, MSSQL_2012.sql file references) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. All business logic resides in the Java application layer. SQL migration files contain only DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX) and DML (INSERT) statements using standard SQL. The application is fully database-portable across 8 dialects (PostgreSQL, MySQL, MariaDB, Oracle, MSSQL, CockroachDB, H2, Derby). |
| **Gap** | N/A — clean separation of business logic from database. |
| **Recommendation** | N/A — the database-portable design is a significant modernization strength. |
| **Evidence** | `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/` (83 SQL files, all DDL/DML, no procedures/triggers); multi-dialect support in DDL generation |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging infrastructure is defined. The application code uses SLF4J for application-level logging and Hibernate Envers for entity audit trails (data-level auditing), but no infrastructure-level audit logging (CloudTrail, S3 bucket for logs, log validation) is configured. |
| **Gap** | No infrastructure audit logging. For healthcare applications handling PHI, CloudTrail with immutable logs is a compliance requirement (HIPAA, HITRUST). |
| **Recommendation** | Enable CloudTrail with log file validation and S3 Object Lock for immutable storage. Configure CloudWatch Logs for application-level audit events. Leverage the existing Hibernate Envers audit trail as the data-change audit layer. |
| **Evidence** | Hibernate Envers dependency in `hapi-fhir-jpaserver-base/pom.xml`; SLF4J logging throughout; absence of `aws_cloudtrail` or audit logging infrastructure |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar infrastructure is defined in IaC. The application code defines database schemas but does not provision or configure storage infrastructure. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_at_rest_data_surface=false`; absence of any deployed storage infrastructure |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application provides authentication interceptor infrastructure (`AuthorizationInterceptor`, `ConsentInterceptor` referenced in CODEOWNERS) and supports OIDC integration. However, no API Gateway authorizer, Cognito user pool, or OAuth2 flow is configured at the infrastructure level. Authentication is available as application-layer interceptors that must be configured by deployers. |
| **Gap** | Authentication is available in code but not enforced at the infrastructure level. No API Gateway with built-in auth, no managed authorizer configuration. Deployers must manually configure authentication interceptors. |
| **Recommendation** | Deploy API Gateway (preferred) with Cognito or OIDC authorizer in front of the FHIR server. Enforce authentication at the gateway level for all external-facing endpoints. Use the existing AuthorizationInterceptor for fine-grained FHIR resource-level access control. |
| **Evidence** | `.github/CODEOWNERS` (AuthorizationInterceptor.java, ConsentInterceptor.java); CLAUDE.md (Security-related classes restricted); absence of API Gateway authorizer configuration |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration is defined at the infrastructure level. The application supports OIDC at the code level (referenced in restricted classes), but no Cognito user pool, Okta integration, or SAML federation is configured. |
| **Gap** | No centralized IdP integration defined. Healthcare applications require federated identity for clinical user access (EHR integration, clinical SSO). |
| **Recommendation** | Integrate with Amazon Cognito as the centralized IdP. Configure OIDC federation with existing clinical identity providers (Epic MyChart, Cerner, etc.). Enable SSO for administrative and clinical user access. |
| **Evidence** | CLAUDE.md (Oidc-related classes listed as restricted); absence of `aws_cognito_*` or IdP configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No plaintext credentials are present in the repository. CI/CD pipelines use proper secret management: GitHub secrets (CODECOV_TOKEN, GIT_TOKEN), Azure DevOps secure variable groups (GPG keys, Sonatype credentials), and OIDC-based AWS credentials (`aws-actions/configure-aws-credentials@v4`). Database credentials are externalized via Spring Boot configuration properties (not committed). |
| **Gap** | While no plaintext secrets exist in source, there is no Secrets Manager or Vault integration for runtime secrets. Database credentials would be passed via environment variables at deployment time without rotation. |
| **Recommendation** | Integrate AWS Secrets Manager for runtime database credentials and API keys. Configure automatic rotation for database passwords. Reference Secrets Manager ARNs in EKS pod configurations via External Secrets Operator. |
| **Evidence** | `.github/workflows/` (GitHub secrets, OIDC AWS auth); `snapshot-deploy-job.yml` (Azure DevOps secure variable groups); absence of hardcoded credentials; absence of Secrets Manager integration |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CodeQL security scanning runs weekly and on PRs. WhiteSource/Mend vulnerability scanning is configured (minimum severity: LOW). Dependabot scans daily for Maven dependency updates. However, no compute-level hardening is defined — no SSM Patch Manager, no hardened base images, no Inspector scanning. The CI build image uses `maven:3.9-eclipse-temurin-21-jammy` (official but not hardened). |
| **Gap** | Application-level vulnerability scanning exists (CodeQL, WhiteSource, Dependabot) but no compute-level hardening or patching strategy. No hardened container base images for production deployment. |
| **Recommendation** | Use Amazon Linux 2023 or Bottlerocket as EKS node OS. Use ECR image scanning for container vulnerability detection. Create a hardened base image for the FHIR server container (minimal JRE, no shell, non-root user). |
| **Evidence** | `.github/workflows/codeql-analysis.yml`, `.whitesource`, `.github/dependabot.yml`; `.github/docker/Dockerfile` (maven:3.9-eclipse-temurin-21-jammy) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multiple security scanning tools are integrated into CI/CD: CodeQL (SAST) runs on push/PR/weekly schedule, WhiteSource/Mend (dependency scanning) configured with failure on vulnerabilities, Dependabot (daily dependency updates). However, no container scanning is configured (no ECR scanning, no Trivy/Snyk container scan) and no explicit security gate blocks merges on critical findings. |
| **Gap** | SAST and dependency scanning present, but no container image scanning and no blocking security gate in the merge workflow. CodeQL runs but does not block PRs on findings. |
| **Recommendation** | Add container image scanning (ECR scanning or Trivy) to the CI pipeline when containerization is implemented. Configure CodeQL and WhiteSource to block PR merges on critical/high findings. |
| **Evidence** | `.github/workflows/codeql-analysis.yml` (CodeQL SAST); `.whitesource` (vulnerability scanning, failure on findings); `.github/dependabot.yml` (daily Maven updates) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry Instrumentation 2.10.0 and Elastic APM Agent 1.52.0 are integrated as dependencies. The Batch2 framework includes `BatchJobOpenTelemetryUtils` for trace propagation in batch operations. OpenTelemetry provides the instrumentation foundation for distributed tracing. |
| **Gap** | Tracing instrumentation libraries are present, but no collector or backend configuration is defined. Trace propagation across service boundaries cannot be verified without deployment infrastructure. Some modules may not have complete instrumentation. |
| **Recommendation** | Deploy OpenTelemetry Collector on EKS (sidecar or DaemonSet). Configure X-Ray as the tracing backend for AWS-native integration. Ensure trace context propagation in all HTTP client calls and messaging channels. |
| **Evidence** | Root `pom.xml` (opentelemetry-instrumentation-bom 2.10.0, elastic-apm-agent 1.52.0); `hapi-fhir-storage-batch2/` (BatchJobOpenTelemetryUtils) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload with a user-facing surface for which SLOs are meaningful. The repository defines a library/framework — SLOs would be defined by deployers for their specific instances, not in the library itself. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_deployed_workload=false`; no SLO definitions, error budget configs, or latency alarm configurations |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has some metrics infrastructure — OpenTelemetry for telemetry, Hibernate statistics for database operations, and the Batch2 framework tracks job progress metrics. However, no explicit business metrics (FHIR operations per second, resource types accessed, search query performance, subscription delivery rates) are published to CloudWatch or a metrics backend. |
| **Gap** | Infrastructure-level metrics exist (via OpenTelemetry) but no systematic business outcome metrics are defined. FHIR-specific operational metrics (operations/sec, error rates by resource type, search performance) are not explicitly instrumented. |
| **Recommendation** | Instrument FHIR-specific business metrics: operations per second by type (read/search/create/update), error rates by resource type, subscription delivery success rate, batch job completion rates. Publish to CloudWatch custom metrics. |
| **Evidence** | OpenTelemetry instrumentation (general); `hapi-fhir-storage-batch2/` (InstanceProgress — internal tracking only); absence of CloudWatch custom metric publishing |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection is configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate thresholds, no latency alarms are defined. |
| **Gap** | No alerting of any kind. FHIR server performance degradation or errors would go undetected without manual monitoring. |
| **Recommendation** | Configure CloudWatch alarms on FHIR operation latency (p99), error rates, and database connection pool utilization. Add anomaly detection on search query latency and Batch2 job failure rates. Integrate with PagerDuty/OpsGenie for on-call notification. |
| **Evidence** | Absence of CloudWatch alarms, alerting configuration, or monitoring dashboard definitions |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The CI/CD pipelines publish library artifacts to Maven Central — they do not deploy services. No blue/green, canary, or rolling deployment configuration is defined. No CodeDeploy, Argo Rollouts, or traffic shifting configuration exists. |
| **Gap** | No service deployment strategy. Any deployment of the FHIR server would be manual with no staged rollout, no automatic rollback, and no traffic shifting capability. |
| **Recommendation** | Implement canary deployments on EKS using Argo Rollouts or Flagger. Define health checks and success criteria for progressive rollout. Configure automatic rollback on elevated error rates. |
| **Evidence** | `release-pipeline.yml` (publishes to Maven Central, not service deployment); absence of deployment strategy configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration tests exist using Testcontainers. The test infrastructure supports PostgreSQL 12/16, SQL Server (Standard, Azure, Enterprise), Oracle XE, and Elasticsearch containers. Tests run in CI via the 256-parallel module test matrix. The `hapi-fhir-jpaserver-test-utilities` module provides shared test infrastructure. |
| **Gap** | Integration tests cover database-level operations well, but end-to-end FHIR workflow testing (complete clinical scenarios spanning multiple resource types and operations) may not be comprehensive. Tests are per-module, not cross-module integration. |
| **Recommendation** | Add end-to-end FHIR workflow tests that span multiple operations (e.g., patient registration → encounter creation → observation recording → subscription delivery). These would validate the full FHIR interaction chain in CI. |
| **Evidence** | `hapi-fhir-jpaserver-test-utilities/` (PostgresEmbeddedDatabase, MsSqlEmbeddedDatabase, Oracle21EmbeddedDatabase, TestElasticsearchContainerHelper); `.github/workflows/parallel-pipeline-build.yml` (256-parallel test matrix) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks exist. No Systems Manager Automation documents, no Lambda-based remediation, no structured runbooks in any format. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common FHIR server incidents (database connection exhaustion, search index corruption, batch job failures). |
| **Recommendation** | Create runbooks for common incidents: database connection pool exhaustion, Elasticsearch index rebuild, Batch2 job failure recovery, subscription delivery backlog. Automate the most common remediation actions via Systems Manager Automation. |
| **Evidence** | Absence of runbook files, SSM documents, or incident response automation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CODEOWNERS file defines code ownership for key modules (batch2, subscriptions, MDM, security interceptors) with named individuals. However, no observability-specific ownership is defined — no per-service dashboards, no alarm ownership, no SLO team attribution. |
| **Gap** | Code ownership exists but does not extend to observability assets. No dashboards or alarms are owned by specific teams. |
| **Recommendation** | Extend CODEOWNERS to cover observability configurations. Define per-module dashboards and alarms with named owners matching the existing team structure (batch2 → @michaelabuckley, subscriptions → @fil512, etc.). |
| **Evidence** | `.github/CODEOWNERS` (module-level ownership defined); absence of observability ownership definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging configuration exists. No `default_tags`, no tagging standards, no Tag Policies or Config rules. No AWS resources are defined in the repository to tag. |
| **Gap** | Zero tagging governance. When infrastructure is created, cost allocation, ownership, and environment identification would be undefined. |
| **Recommendation** | Define a tagging standard before creating IaC: minimum tags should include `Environment`, `Service`, `Team`, `CostCenter`, and `DataClassification` (important for healthcare PHI tracking). Enforce via CDK constructs or Terraform `default_tags`. |
| **Evidence** | Absence of any IaC resources or tagging configuration |

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
| `pom.xml` | INF-Q1, INF-Q2, INF-Q4, APP-Q1, APP-Q5, DATA-Q3, DATA-Q4, OPS-Q1 | Root POM with dependency versions, Java 17, Spring Boot 3.4.11, database drivers |
| `.github/workflows/parallel-pipeline-build.yml` | INF-Q11, OPS-Q6 | Core CI pipeline with 256-parallel module testing |
| `.github/workflows/release.yml` | INF-Q11 | GitHub Actions release workflow |
| `.github/workflows/codeql-analysis.yml` | SEC-Q6, SEC-Q7 | CodeQL SAST scanning (push, PR, weekly) |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Daily Maven dependency vulnerability scanning |
| `.whitesource` | SEC-Q6, SEC-Q7 | WhiteSource/Mend vulnerability scanning configuration |
| `.github/docker/Dockerfile` | INF-Q1, SEC-Q6 | CI build image (maven:3.9-eclipse-temurin-21-jammy) |
| `.github/CODEOWNERS` | APP-Q2, OPS-Q8 | Module-level code ownership definitions |
| `release-pipeline.yml` | INF-Q11, OPS-Q5 | Azure DevOps release pipeline (Maven Central publish) |
| `snapshot-pipeline.yml` | INF-Q11 | Azure DevOps snapshot pipeline |
| `snapshot-deploy-job.yml` | INF-Q11, SEC-Q5 | Shared deployment job template with GPG signing |
| `hapi-fhir-jpaserver-base/pom.xml` | INF-Q2, INF-Q4, DATA-Q2 | JPA server dependencies (Spring Data JPA, Hibernate, SQLBuilder) |
| `hapi-fhir-jpaserver-model/` | APP-Q2, DATA-Q2 | Shared JPA entity definitions |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/dao/` | DATA-Q2 | Two-tier DAO pattern (BaseHapiFhirDao, JpaResourceDao) |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/dao/data/` | DATA-Q2 | Spring Data JPA repositories |
| `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/` | DATA-Q3, DATA-Q4 | 83 SQL migration files across 20 versions |
| `hapi-fhir-jpaserver-subscription/` | APP-Q2, APP-Q3, INF-Q4 | FHIR Subscription delivery (Spring messaging) |
| `hapi-fhir-storage-batch2/` | INF-Q3, APP-Q4, INF-Q4, OPS-Q1 | Custom batch/workflow orchestration framework |
| `hapi-fhir-jpaserver-mdm/` | APP-Q2 | Master Data Management module |
| `hapi-fhir-spring-boot/` | APP-Q6 | Spring Boot auto-configuration and externalized config |
| `hapi-fhir-jpaserver-test-utilities/` | OPS-Q6 | Testcontainers integration test infrastructure |
| `CLAUDE.md` | SEC-Q3, SEC-Q4 | AI agent guidance referencing security/OIDC classes |
