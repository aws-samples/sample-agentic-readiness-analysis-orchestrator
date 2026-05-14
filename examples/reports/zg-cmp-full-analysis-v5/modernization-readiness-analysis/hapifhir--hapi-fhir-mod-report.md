# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | hapifhir--hapi-fhir |
| **Date** | 2026-04-30 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) — assessed holistically for the framework's dominant JPA server modules |
| **Priority** | P2 |
| **Tags** | java, healthcare, rest-api |
| **Context** | Open-source Java implementation of the HL7 FHIR healthcare standard. |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | 2.35 / 4.0 |

Repo type provided as `monorepo`. All 37 questions apply per monorepo rules. **Important context:** This repository is an open-source framework/library monorepo providing building blocks for FHIR server implementations — it is not itself a deployed application. Infrastructure scores reflect the absence of deployment artifacts, which is expected for an open-source library framework. Scores reflect the repository's code and CI/CD maturity.

**Archetype Justification**: The JPA server modules (hapi-fhir-jpaserver-base, hapi-fhir-jpa, hapi-fhir-jpa-hibernate-services) dominate the repository's runtime behavior when deployed. These modules own persistent state via JPA/Hibernate, expose CRUD operations on FHIR resources, and manage entity lifecycle. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.75 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.17 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.17 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.35 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No IaC defining compute resources; no deployment infrastructure in repository | Deployers must define all compute infrastructure from scratch; no reference architecture provided |
| 2 | INF-Q5: Network Security | 1 | No VPC, security group, or network segmentation definitions | Deployers have no network security blueprint; risk of insecure default deployments |
| 3 | INF-Q10: IaC Coverage | 1 | No Infrastructure as Code files in repository | Zero reproducibility for deployment infrastructure; entirely manual setup for deployers |
| 4 | OPS-Q3: Business Metrics | 1 | No custom business metrics publishing; only interceptor hooks available | No out-of-box observability for FHIR-specific business outcomes (resource operations, search latency) |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging infrastructure; interceptor framework provides hooks only | Deployers must build audit logging from scratch; compliance risk for healthcare deployments |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — the `hapi-fhir-docs/` module contains extensive documentation, `README.md` provides project overview, and the full FHIR specification documentation is embedded in the project changelogs and documentation resources.
- **What it enables:** A knowledge agent that indexes HAPI FHIR documentation, changelogs, and FHIR specification resources to answer developer questions about API usage, configuration, migration paths, and FHIR compliance.
- **Additional steps:** Index the `hapi-fhir-docs/src/main/resources/` directory and README into a vector store. Generate embeddings for changelog entries and documentation pages. Consider using Amazon Bedrock with Titan Embeddings.
- **Effort:** Medium

### API-aware Agent

- **Prerequisite:** API docs exist (APP-Q5 = 4). The OpenAPI interceptor (`hapi-fhir-server-openapi` module) generates OpenAPI specs dynamically for deployed FHIR servers. FHIR version-based API versioning is mature (DSTU2 through R5).
- **What it enables:** An agent that discovers and invokes FHIR REST endpoints as tools — supporting CRUD operations on FHIR resources, search operations, and batch processing.
- **Additional steps:** Deploy a HAPI FHIR server instance with the OpenAPI interceptor enabled. The generated OpenAPI spec provides the tool interface for the agent. Consider Amazon Bedrock for the agent runtime.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions workflows handle PR validation, release, CodeQL analysis, and formatting checks. Azure Pipelines handle snapshot and release publishing.
- **What it enables:** An agent that triggers builds, checks PR status, monitors release pipeline execution, and manages Maven artifact publishing.
- **Additional steps:** Expose GitHub Actions API and Azure Pipelines API as agent tools. Configure appropriate authentication scopes.
- **Effort:** Low

### Data Query Agent

- **Prerequisite:** Database with clear, documented schema (DATA-Q2 = 4). The JPA/Hibernate layer provides a unified data access pattern with well-defined entity models for all FHIR resources.
- **What it enables:** A data query agent that translates natural language queries about FHIR resources into structured FHIR search queries or HQL/SQL queries against the JPA data model.
- **Additional steps:** Map the FHIR resource DAOs and search parameter definitions as the query interface. Consider pairing with Amazon Bedrock for natural language to FHIR search translation.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 3). OpenTelemetry instrumentation is built into the framework with span attributes for batch job execution.
- **What it enables:** An agent that queries OpenTelemetry traces and logs to identify slow FHIR operations, batch job failures, and performance bottlenecks.
- **Additional steps:** Deploy with OpenTelemetry collector exporting to AWS X-Ray or CloudWatch. Index trace data for agent queries.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monorepo with shared build), INF-Q1 = 1 (no managed compute) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but a Dockerfile exists (.github/docker/Dockerfile for build). Contextual guard: no compute infrastructure exists to containerize — this is a library framework. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). Framework supports Oracle and MSSQL but no IaC deploys them; no commercial DB engine is in use by the repo itself. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated (no IaC deploying databases). Surface-gated — no database deployment in this repo. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 (broker API provides managed-friendly abstraction). No data processing workloads exist in the repository. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), OPS-Q5 = 1 (no deployment strategy). Supporting: OPS-Q6 = 4 (testing is strong). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context is "Open-source Java implementation of the HL7 FHIR healthcare standard" — no AI signal terms present. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The HAPI FHIR monorepo is a single Maven reactor build producing 60+ interdependent modules under a unified version (8.9.8-SNAPSHOT). APP-Q2 scores 2 — the monorepo has identifiable module boundaries (JPA server, storage, validation, structures) but tight coupling through shared database schemas, cross-module dependencies, and a single release train. When deployed, it operates as a monolithic FHIR server.

**Compute Model Gaps (INF-Q1 = 1):**
No IaC defines compute resources. The repository provides no reference deployment architecture — deployers must build compute infrastructure from scratch.

**Communication Pattern Strengths:**
- The broker API abstraction (hapi-fhir-storage/broker/) provides a pluggable messaging interface supporting both sync and async patterns
- The batch2 module provides a workflow orchestration framework for long-running operations
- APP-Q3 = 3 and APP-Q4 = 4 indicate good async readiness within the framework

**Recommended Approach:**
For organizations deploying HAPI FHIR, a reference cloud-native architecture should be provided:
- Deploy FHIR server workloads on **Amazon EKS** (per preferences) with separate deployments for read-heavy and write-heavy traffic
- Use **Amazon API Gateway** as the FHIR API entry point with throttling and authentication
- Leverage **Amazon EventBridge** for FHIR subscription notifications and async event processing
- Use the built-in batch2 framework with **AWS Step Functions** for bulk data export and reindexing operations

**Representative AWS Services:** EKS, API Gateway, EventBridge, Step Functions, Lambda (for lightweight FHIR event handlers)

**Patterns:** Strangler Fig (for decomposing the monolith into independently deployable modules), Anti-corruption Layer, Event Sourcing for FHIR resource versioning

**Reference:** [AWS Prescriptive Guidance — Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
No Infrastructure as Code files exist in the repository. All deployment infrastructure must be created manually by deployers. This is the single largest gap — there is no reference Terraform, CDK, CloudFormation, or Helm chart for deploying HAPI FHIR on AWS.

**Current CI/CD State (INF-Q11 = 3):**
CI/CD is well-established for build and publish:
- GitHub Actions: PR validation (`pull-request.yml`), parallel module testing (`parallel-pipeline-build.yml`), release pipeline (`release.yml`), CodeQL analysis (`codeql-analysis.yml`), formatting checks (`spotless.yml`)
- Azure Pipelines: Release builds (`release-pipeline.yml`), snapshot publishing (`snapshot-pipeline.yml`)
- The pipeline includes automated testing, code quality checks, and artifact publishing to Maven Central

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy is defined — the CI/CD pipeline is a build/publish pipeline, not a deployment pipeline. There are no Helm charts, Kubernetes manifests, CodeDeploy configurations, or blue/green deployment definitions.

**Testing Strengths (OPS-Q6 = 4):**
Extensive integration testing infrastructure with dedicated test modules per FHIR version (test-dstu2, test-dstu3, test-r4, test-r4b, test-r5), Testcontainers for database integration tests, and parallel test execution in CI.

**Recommendations:**
1. **Add Reference IaC** — Create a `deploy/` directory with EKS deployment manifests, Helm charts for HAPI FHIR server, and Terraform modules for Aurora PostgreSQL (per preferences), VPC networking, and API Gateway configuration. Avoid Oracle (per preferences).
2. **Add Deployment Pipeline** — Extend GitHub Actions with deployment stages targeting EKS. Implement canary deployments using Argo Rollouts or AWS CodeDeploy.
3. **Add Operational IaC** — Define CloudWatch dashboards, alarms, backup plans, and Route 53 health checks in IaC.

**Representative AWS Services:** CDK/Terraform, CodeBuild, CodePipeline, CodeDeploy, EKS, CloudFormation

**Reference:** [AWS SkillBuilder — Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

---

## Decomposition Strategy

*Included because APP-Q2 = 2 (monolith with identifiable modules but shared database schemas and single release train).*

### Current State

The HAPI FHIR monorepo comprises 60+ Maven modules in a single reactor build under version 8.9.8-SNAPSHOT. Key module groups:

| Module Group | Modules | Archetype | Coupling |
|-------------|---------|-----------|----------|
| Core Libraries | hapi-fhir-base, hapi-fhir-client, hapi-fhir-server | Library | Low — provides interfaces and base classes |
| FHIR Structures | hapi-fhir-structures-{dstu2,dstu3,r4,r4b,r5} | Library | Low — version-specific resource models |
| JPA Server | hapi-fhir-jpaserver-base, hapi-fhir-jpa, hapi-fhir-jpa-hibernate-services | stateful-crud | High — shared Hibernate entities and database schema |
| Storage/Batch | hapi-fhir-storage, hapi-fhir-storage-batch2 | event-processor | Medium — depends on JPA layer |
| Subscription/MDM | hapi-fhir-jpaserver-subscription, hapi-fhir-jpaserver-mdm | event-processor | High — deep integration with JPA server |
| Validation | hapi-fhir-validation, hapi-fhir-validation-resources-* | Library | Low — mostly standalone |

### Decomposition Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2 = 2 — identifiable module boundaries exist. The structures, validation, and core library modules can be extracted into independently versioned artifacts while the JPA server core remains monolithic. | **Medium to High** — 6-18 months | ✅ **Recommended.** Start by independently versioning FHIR structure modules, then extract storage-batch2 as a standalone service. |
| **Conditional / Adaptive** | Team capacity is limited. Containerize the monolithic FHIR server as-is on EKS, then selectively extract read-heavy operations (search, validation) as independent services. | **Low to Medium** — containerization in 2-4 weeks, selective extraction over 3-12 months | ✅ **Recommended when capacity is constrained.** Quick win: containerize on EKS first. |
| **Big-Bang Rewrite** | Not applicable — the HAPI FHIR codebase is mature, actively maintained, and functional. | **Very High** — 12-24+ months | ⚠️ **Recommended against.** The codebase is healthy; incremental decomposition is safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted modules from the monolithic JPA server's data model | When extracting search or validation into independent services |
| **Saga Pattern** | Manage distributed transactions across decomposed FHIR server modules | When extracting subscription processing or MDM matching into separate services |
| **Event Sourcing** | FHIR resource versioning already uses event-sourcing-like patterns (resource version history) | Formalize as part of the storage layer decomposition; leverage EventBridge |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters | All new services — ensures testability and infrastructure portability |

### Effort Estimation Factors

| Factor | Current Signal | Effort Impact |
|--------|---------------|---------------|
| Module boundaries | Clear package structure per module; CODEOWNERS defines ownership | Low — boundaries are well-defined |
| Data coupling | Shared Hibernate entities across JPA modules; single database schema | High — schema separation is the hardest part |
| Stored procedures | None (DATA-Q4 = 4) | Low — no database-coupled logic to extract |
| Communication patterns | Broker API provides async abstraction (APP-Q3 = 3) | Low — async patterns are already available |
| CI/CD maturity | Strong build/test automation (INF-Q11 = 3, OPS-Q6 = 4) | Low — pipeline can be extended for multi-service deployment |
| Test coverage | Extensive integration tests per FHIR version | Low — regression risk is managed |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defining compute resources exists in the repository. No Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources found. No Kubernetes manifests or Helm charts found. The only Dockerfile (`.github/docker/Dockerfile`) is a build-only image for Maven CI publishing, not a runtime container. This is expected for an open-source framework — compute is the deployer's responsibility. |
| **Gap** | No reference deployment architecture or compute infrastructure is provided. Deployers must define all compute resources from scratch without guidance from the framework project. |
| **Recommendation** | Add a reference EKS deployment architecture (per preferences) in a `deploy/` directory. Include Helm charts for deploying HAPI FHIR server on EKS with recommended resource limits, health check configurations, and readiness probes. Avoid self-managed Kubernetes (per preferences). |
| **Evidence** | `.github/docker/Dockerfile` (build-only), absence of `*.tf`, `Chart.yaml`, `kustomization.yaml`, Kubernetes manifests |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy any database. The repository provides a database abstraction layer (JPA/Hibernate with DriverTypeEnum supporting H2, Derby, MariaDB, MySQL, PostgreSQL, Oracle, MSSQL, CockroachDB) but no IaC provisions any database resource. `has_persistent_data_store=true` (the framework supports databases) but `has_at_rest_data_surface=false` (no IaC deploys storage). INF-Q2 evaluates whether deployed databases use managed services — there are no deployed databases to evaluate. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `hapi-fhir-sql-migrate/src/main/java/ca/uhn/fhir/jpa/migrate/DriverTypeEnum.java`, absence of `aws_rds_*` or `aws_dynamodb_*` in IaC |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `hapi-fhir-storage-batch2` module provides a dedicated internal workflow orchestration framework. It implements job step execution with chunking, reduction steps, gated step execution, and job coordination — functionally equivalent to a built-in workflow engine for FHIR batch operations (bulk export, reindexing, MDM matching). The `BatchJobOpenTelemetryUtils` class adds OpenTelemetry span attributes for job execution monitoring. However, this is an application-level orchestration framework, not a managed cloud service (Step Functions, Temporal). |
| **Gap** | Workflow orchestration is built into the application code rather than delegated to a managed service. When deployed, this means orchestration state management, retry logic, and monitoring are handled by the application rather than by AWS Step Functions or similar. |
| **Recommendation** | For production deployments, consider integrating the batch2 framework with AWS Step Functions for visual workflow management, built-in retry/error handling, and operational visibility. The existing batch2 step abstraction maps well to Step Functions states. |
| **Evidence** | `hapi-fhir-storage-batch2/` module, `BatchJobOpenTelemetryUtils.java`, CODEOWNERS ownership by `@michaelabuckley @jamesagnew @tadgh` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The broker API abstraction in `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/` provides a pluggable messaging interface with `IBrokerClient`, `IChannelProducer`, `IChannelConsumer`, `IMessageListener`, and `IRetryAwareMessageListener`. This supports both synchronous in-memory channels and external message brokers. The `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/jms/` directory indicates JMS adapter support. The subscription module (`hapi-fhir-jpaserver-subscription`) uses this broker API for FHIR Subscription processing. |
| **Gap** | The broker API is backend-agnostic but no out-of-box integration with AWS managed messaging services (SQS, SNS, EventBridge) is provided. The JMS adapter exists but deployers must configure the broker backend themselves. |
| **Recommendation** | Add reference implementations for Amazon EventBridge and Amazon SQS as broker backends (per preferences). Avoid self-managed Kafka (per preferences). EventBridge is well-suited for FHIR subscription event routing with content-based filtering. |
| **Evidence** | `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/api/` (16 files), `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/jms/` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation definitions found in the repository. No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. No Kubernetes NetworkPolicy definitions. This is expected for a framework repository — network security is entirely the deployer's responsibility. |
| **Gap** | No reference network architecture is provided. Healthcare deployments require strict network segmentation (HIPAA), and deployers have no blueprint from the project. |
| **Recommendation** | Add reference VPC architecture with private subnets for FHIR server workloads, security groups with least-privilege rules, and VPC endpoints for AWS service access. Include network segmentation between application, database, and management tiers. |
| **Evidence** | Absence of `*.tf`, CloudFormation templates, Kubernetes NetworkPolicy files |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or managed entry point configuration found. The framework provides a REST server (`hapi-fhir-server`) with interceptor hooks for authentication, authorization, and request handling, but no managed entry point is defined. The `hapi-fhir-server-openapi` module provides dynamic OpenAPI spec generation via `OpenApiInterceptor`, suggesting the framework is designed to sit behind an API gateway. |
| **Gap** | No reference API entry point architecture is provided. FHIR servers in production require throttling, authentication at the gateway level, and request validation — all absent from the repository. |
| **Recommendation** | Add reference configuration for Amazon API Gateway (per preferences) with FHIR-aware request validation, OAuth2/SMART-on-FHIR authorization, and rate limiting. Include CloudFront for caching of conformance/metadata responses. |
| **Evidence** | `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java`, absence of `aws_api_gateway_*` resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*`, `aws_appautoscaling_*`, Kubernetes HPA, or similar scaling definitions exist in the repository. |
| **Gap** | No scaling guidance or reference configuration for production deployments. FHIR servers experience variable load (bulk data operations, batch imports) requiring elastic scaling. |
| **Recommendation** | Include reference EKS HPA configurations with custom metrics (FHIR requests-per-second, search operation latency). Define scaling policies for both the FHIR server tier and the database tier (Aurora auto-scaling per preferences). |
| **Evidence** | Absence of auto-scaling configuration in any file |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. No IaC provisions databases, S3 buckets, or other data stores. The framework supports databases but does not deploy them. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_persistent_data_store=true` but `has_at_rest_data_surface=false` — no IaC deploys storage |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. `has_deployed_workload=false` — no deployment manifests, no ECS/EKS task definitions, no Lambda functions. The only Dockerfile is for CI build. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `.github/docker/Dockerfile` (build-only), `has_deployed_workload=false` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository. No Terraform (`.tf`), CloudFormation, CDK (`cdk.json`), Helm charts (`Chart.yaml`), or Kustomize (`kustomization.yaml`) files exist. Zero infrastructure is defined as code. |
| **Gap** | 0% IaC coverage. All deployment infrastructure must be created manually or sourced from external projects. This is the most significant infrastructure gap for organizations deploying HAPI FHIR. |
| **Recommendation** | Create a `deploy/` directory with reference IaC covering: (1) EKS cluster and node groups, (2) Aurora PostgreSQL database (per preferences — avoid Oracle), (3) VPC networking, (4) API Gateway, (5) CloudWatch monitoring, (6) Backup plans. Use Terraform or CDK. |
| **Evidence** | Absence of `*.tf`, `*.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI pipeline with automated build, test, and publish stages across two platforms: **GitHub Actions** — PR validation (`pull-request.yml` → `parallel-pipeline-build.yml` with per-module parallel testing), release workflow (`release.yml`), CodeQL SAST analysis (`codeql-analysis.yml`), formatting enforcement (`spotless.yml`). **Azure Pipelines** — Release builds (`release-pipeline.yml`), nightly snapshot publishing (`snapshot-pipeline.yml`). The CI pipeline includes checkstyle validation, parallel module testing with matrix strategy (up to 256 parallel jobs), test report assembly, and Codecov integration. |
| **Gap** | No deployment automation. The pipeline builds and publishes Maven artifacts but does not deploy to any environment. No infrastructure change automation (no IaC pipeline). The pipeline is build-and-publish, not build-test-deploy. |
| **Recommendation** | Extend CI/CD with deployment stages: (1) Add Helm chart packaging and publishing, (2) Add deployment pipeline targeting EKS staging/production environments, (3) Add IaC validation and deployment pipeline for Terraform/CDK. |
| **Evidence** | `.github/workflows/pull-request.yml`, `.github/workflows/parallel-pipeline-build.yml`, `.github/workflows/release.yml`, `.github/workflows/codeql-analysis.yml`, `.github/workflows/spotless.yml`, `release-pipeline.yml`, `snapshot-pipeline.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 17 with modern cloud-native framework stack: Spring Boot 3.4.11, Spring Framework 6.2.12, Hibernate 6.6.4.Final, Jackson 2.20.0, JUnit 5.11.4, Jetty 12.0.32, OpenTelemetry 2.10.0. Maven enforcer requires JDK 17+. All three axes are modern: Java 17 (current LTS), Spring Boot 3.x (latest generation), modern framework versions throughout. The project also uses Jakarta EE 10 APIs (jakarta.* namespace), confirming full migration from javax.* to Jakarta. |
| **Gap** | None — language, framework, and SDK are all at current versions. |
| **Recommendation** | Continue tracking Spring Boot and Hibernate releases. Consider Java 21 LTS adoption for virtual threads (Project Loom), which would benefit the synchronous FHIR REST server's concurrency model. |
| **Evidence** | `pom.xml` — `maven.compiler.release=17`, `spring_boot_version=3.4.11`, `spring_version=6.2.12`, `hibernate_version=6.6.4.Final`, `jackson_version=2.20.0`, `junit_version=5.11.4` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The repository is a monorepo with 60+ Maven modules sharing a single version (8.9.8-SNAPSHOT) and a single Maven reactor build. Module boundaries are identifiable — core libraries (hapi-fhir-base), structures (per FHIR version), JPA server, storage, subscription, validation — but all modules are tightly coupled through a shared version, shared Hibernate entities, and cross-module dependencies. The JPA server modules share a single database schema. All modules release simultaneously as a single artifact set. CODEOWNERS shows team-level ownership per module, indicating organizational separation exists. |
| **Gap** | Monolith with identifiable modules but shared database schemas and a single release train. Independent scaling, deployment, or release of individual modules is not possible without the full reactor build. Cross-module data access through shared Hibernate entities creates tight coupling. |
| **Recommendation** | See Decomposition Strategy section. Begin with independent versioning of structure modules (DSTU2, DSTU3, R4, R4B, R5) which have lower coupling. Consider modular monolith patterns with clear interfaces before full decomposition. |
| **Evidence** | `pom.xml` — 60+ `<module>` entries, single `<version>8.9.8-SNAPSHOT</version>`, `.github/CODEOWNERS` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The framework supports both synchronous and asynchronous communication patterns. The FHIR REST server (`hapi-fhir-server`) is synchronous by design — appropriate for a stateful-crud archetype. The broker API (`hapi-fhir-storage/broker/`) provides async communication for subscription processing, batch job coordination, and event-driven workflows. The batch2 module uses asynchronous job processing with chunked execution. Mix of sync REST for CRUD operations and async for background processing (subscriptions, bulk export, reindexing). |
| **Gap** | Async patterns are available but not all cross-service communication uses them. For deployed microservice scenarios, synchronous HTTP between components could create coupling. The broker API requires explicit backend configuration. |
| **Recommendation** | For deployed architectures, ensure FHIR Subscription processing uses EventBridge (per preferences) as the broker backend. Maintain synchronous REST for CRUD operations (appropriate for the archetype). |
| **Evidence** | `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/api/IBrokerClient.java`, `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/api/IChannelProducer.java`, `hapi-fhir-jpaserver-subscription/` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The batch2 module (`hapi-fhir-storage-batch2`) provides comprehensive async job handling for long-running operations. It implements: job step execution with chunking, reduction steps for aggregation, gated step execution, job instance tracking with status polling, OpenTelemetry instrumentation for monitoring, and retry-aware message handling (`IRetryAwareMessageListener`). This handles bulk data export, reindexing, MDM matching, and other operations exceeding 30 seconds — all asynchronously with status tracking. |
| **Gap** | None — the batch2 framework comprehensively addresses long-running process handling with async execution, status tracking, and monitoring. |
| **Recommendation** | Continue using the batch2 framework. For cloud deployments, consider exposing batch job status via a dedicated API endpoint compatible with FHIR Async Request Pattern (RFC 7231). |
| **Evidence** | `hapi-fhir-storage-batch2/` module, `BatchJobOpenTelemetryUtils.java`, `hapi-fhir-storage-batch2-jobs/` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | FHIR standard versions serve as a comprehensive API versioning strategy. The repository supports DSTU2, DSTU2.1, DSTU3, R4, R4B, and R5 through dedicated structure modules (`hapi-fhir-structures-{version}`). Each FHIR version defines a complete API contract with backward compatibility. The `hapi-fhir-server-openapi` module generates version-specific OpenAPI documentation. FHIR capability statements provide machine-readable version discovery. This is a standards-based versioning strategy with formal specification governance by HL7 — more rigorous than typical URL-path or header-based versioning. |
| **Gap** | None — versioning is inherent to the FHIR specification and fully implemented across all supported versions. |
| **Recommendation** | Maintain support for current FHIR versions. Consider deprecation strategy for DSTU2/DSTU2.1 as the community moves to R4/R5. |
| **Evidence** | `hapi-fhir-structures-dstu2/`, `hapi-fhir-structures-dstu3/`, `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r4b/`, `hapi-fhir-structures-r5/`, `hapi-fhir-server-openapi/` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No service registry, API catalog, or service mesh configuration found. This is expected for a framework — service discovery is the deployer's responsibility. The framework does support FHIR capability statements which serve as a form of service self-description (each server publishes its capabilities at the `/metadata` endpoint). Environment variables are the expected mechanism for configuring service endpoints in deployed HAPI FHIR servers. |
| **Gap** | No dynamic service discovery. Deployed HAPI FHIR servers use environment variables for endpoint configuration (database URLs, external service URLs) without dynamic discovery. |
| **Recommendation** | For EKS deployments (per preferences), leverage Kubernetes service DNS for service-to-service communication. Consider adding AWS Cloud Map integration for cross-cluster service discovery. |
| **Evidence** | `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/hapi-fhir-spring-boot-sample-server-jersey/src/main/resources/application.yml` (static configuration) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The framework supports FHIR Binary resources for unstructured data storage but stores them in the relational database by default (as BLOBs in JPA entities). No S3 integration or external binary storage provider is included in the framework. For large-scale deployments with medical images, documents, or attachments, database BLOB storage is inefficient and not scalable. |
| **Gap** | No managed object storage integration for FHIR Binary resources. Unstructured data is locked in the relational database BLOB store, limiting accessibility for analytics, AI/ML, and document processing pipelines. |
| **Recommendation** | Add an S3-backed binary storage provider that stores FHIR Binary resource contents in Amazon S3 while maintaining metadata in the database. Include lifecycle policies and Textract integration for document parsing (healthcare document extraction). |
| **Evidence** | JPA entity model in `hapi-fhir-jpaserver-base/`, absence of S3 SDK dependencies in any `pom.xml` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The framework provides an exemplary unified data access layer through the JPA/Hibernate persistence layer. All FHIR resource access goes through centralized DAO interfaces (`IFhirResourceDao` pattern in `hapi-fhir-storage`). The data access layer abstracts database operations behind a consistent API for all FHIR resource types. The `hapi-fhir-jpa` module provides the JPA implementation, `hapi-fhir-jpa-hibernate-services` provides Hibernate-specific services, and `hapi-fhir-sql-migrate` manages schema migrations programmatically. No scattered database connections — all access is centralized. |
| **Gap** | None — data access is fully centralized through the JPA/Hibernate DAO layer. |
| **Recommendation** | Maintain the centralized data access pattern. The existing abstraction supports DynamoDB (per preferences) through custom DAO implementations if needed. |
| **Evidence** | `hapi-fhir-jpa/`, `hapi-fhir-jpaserver-base/`, `hapi-fhir-jpa-hibernate-services/`, `hapi-fhir-sql-migrate/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DriverTypeEnum defines minimum supported database versions: H2 (embedded), Derby (embedded), MariaDB 10.1, MySQL 5.7, PostgreSQL 9.4, Oracle 12C, MSSQL 2012, CockroachDB 21.1. The naming convention in migration SQL files (e.g., `POSTGRES_9_4.sql`, `ORACLE_12C.sql`, `MSSQL_2012.sql`) indicates these are the minimum supported versions. **EOL concerns:** PostgreSQL 9.4 reached EOL in February 2020. MSSQL 2012 reached EOL in July 2022. Oracle 12c reached EOL in March 2022. MariaDB 10.1 reached EOL in October 2020. These version names in DriverTypeEnum represent minimum compatibility, not pinned deployment versions — but they signal that the framework is tested against and supports EOL database engines. |
| **Gap** | The framework's minimum supported database versions include multiple EOL engines (PostgreSQL 9.4, MSSQL 2012, Oracle 12C, MariaDB 10.1). While deployers can use newer versions, the naming convention and migration test files target these older versions, potentially encouraging outdated deployments. No documented version-update procedure exists. |
| **Recommendation** | Update DriverTypeEnum naming and migration test matrices to reflect currently supported database versions (PostgreSQL 14+, MySQL 8.0+, MSSQL 2019+). Deprecate support for EOL database versions. For new deployments, recommend Aurora PostgreSQL (per preferences — avoid Oracle). |
| **Evidence** | `hapi-fhir-sql-migrate/src/main/java/ca/uhn/fhir/jpa/migrate/DriverTypeEnum.java`, `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/releases/V8_4_0/data/POSTGRES_9_4.sql`, `ORACLE_12C.sql`, `MSSQL_2012.sql` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs found. Searched all 87 SQL files for `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` — zero results. All business logic resides in the Java application layer. Schema migrations are managed programmatically through `hapi-fhir-sql-migrate` using Java-based migration tasks, not SQL-based stored procedures. The Hibernate/JPA layer generates all SQL dynamically. This clean separation means database engine migration (e.g., Oracle to Aurora PostgreSQL) has no stored procedure extraction burden. |
| **Gap** | None — all business logic is in the application layer with no database-coupled logic. |
| **Recommendation** | Maintain this pattern. The absence of stored procedures significantly reduces effort for database engine migration (e.g., to Aurora PostgreSQL per preferences). |
| **Evidence** | 87 SQL files in `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/`, `hapi-fhir-sql-migrate/`, zero stored procedures found |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration, audit logging infrastructure, or immutable log storage found. The framework provides an interceptor-based extensibility model (Pointcut system in `hapi-fhir-base`, `AuthorizationInterceptor` in `hapi-fhir-server`) that enables deployers to implement audit logging, but no out-of-box audit logging implementation is included. For healthcare FHIR servers (HIPAA, HITRUST), audit logging is a compliance requirement. |
| **Gap** | No audit logging infrastructure. The interceptor framework provides hooks but deployers must implement audit logging from scratch. Critical for healthcare compliance. |
| **Recommendation** | Add a reference FHIR AuditEvent-generating interceptor that captures all REST operations and writes FHIR AuditEvent resources. Include CloudTrail configuration in reference IaC with log file validation and S3 Object Lock for immutable storage. |
| **Evidence** | `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java` (auth hooks exist), absence of `aws_cloudtrail` resources |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. `has_at_rest_data_surface=false`. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_at_rest_data_surface=false` — no IaC deploying storage resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The framework provides comprehensive authentication and authorization hooks: `AuthorizationInterceptor.java` for fine-grained access control rules, `ConsentInterceptor.java` for consent-based data filtering, and the interceptor framework supports custom authentication middleware. The `hapi-fhir-server-openapi` module includes `OpenApiInterceptorWithAuthorizationInterceptorTest.java`, demonstrating auth integration with OpenAPI. However, no default authentication implementation is included — the framework provides the hooks, not a working auth configuration. The FHIR specification defines SMART-on-FHIR (OAuth2-based) as the standard auth framework, and the interceptor model supports it. |
| **Gap** | No default authentication implementation. Deployers must configure OAuth2/SMART-on-FHIR authentication themselves. The auth hooks are mature but require explicit configuration. |
| **Recommendation** | Add a reference SMART-on-FHIR OAuth2 configuration using Amazon Cognito (or external IdP). Include API Gateway authorizer configuration for token validation (per preferences for API Gateway). |
| **Evidence** | `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java`, `.github/CODEOWNERS` (auth files owned by `@jamesagnew`) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No Cognito, OIDC, SAML, or external IdP integration found in the framework. The framework's interceptor model can federate with external identity providers, but no reference implementation is included. The SMART-on-FHIR specification (used in healthcare) is built on OAuth2/OIDC, and the framework's auth interceptors are designed to work with it, but the actual IdP integration is left to deployers. |
| **Gap** | No centralized identity integration. Deployers must implement their own IdP configuration. For healthcare deployments, SMART-on-FHIR requires OIDC/OAuth2 integration with a centralized IdP. |
| **Recommendation** | Add reference Amazon Cognito configuration with SMART-on-FHIR scopes and claims mapping. Include OIDC discovery endpoint integration. |
| **Evidence** | Absence of Cognito, OIDC, or SAML configuration in any module; `AuthorizationInterceptor.java` supports rule-based auth but no IdP binding |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No plaintext credentials found in non-test source code or configuration files. CI/CD pipelines use GitHub Secrets (`${{ secrets.CODECOV_TOKEN }}`, `${{ secrets.GITHUB_TOKEN }}`). No `.env` files committed to the repository. The `application.yml` sample files in Spring Boot starters contain only non-secret configuration (FHIR version, server path, logging levels). The `DriverTypeEnum` provides parameterized database connection methods accepting username/password arguments — no hardcoded credentials. The `snapshot-deploy-job.yml` references pipeline variables for sensitive values. No Secrets Manager or Vault integration exists, but for an open-source framework this is appropriate — secret management is the deployer's responsibility. |
| **Gap** | No reference Secrets Manager integration for database credentials, API keys, or other sensitive configuration. Deployers must configure secrets management themselves. |
| **Recommendation** | Add reference AWS Secrets Manager configuration in the reference deployment IaC for database credentials and API keys. Include secret rotation configuration. |
| **Evidence** | `.github/workflows/pull-request.yml` (uses `secrets.CODECOV_TOKEN`), `snapshot-deploy-job.yml`, `application.yml` samples (no credentials), `DriverTypeEnum.java` (parameterized credentials) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching configuration found. The build Dockerfile (`.github/docker/Dockerfile`) uses `maven:3.9-eclipse-temurin-21-jammy` as a base image — this is a CI build image, not a runtime container. No hardened base images (CIS, Bottlerocket), SSM Patch Manager configuration, or vulnerability scanning for runtime images exists. No EC2 Image Builder pipelines. |
| **Gap** | No compute hardening or patching strategy. For deployed FHIR servers, unpatched JVM images are a security risk. |
| **Recommendation** | Add a production-ready Dockerfile using a hardened base image (Amazon Corretto 17 on Amazon Linux 2023 or Bottlerocket for EKS). Include ECR image scanning in the CI pipeline. Reference SSM Patch Manager in deployment IaC. |
| **Evidence** | `.github/docker/Dockerfile` (build-only, non-hardened base), absence of Inspector/Snyk configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multiple security scanning tools are integrated: **CodeQL SAST** — `codeql-analysis.yml` runs on push, PR, and weekly schedule with full Maven build for compiled Java analysis. **Dependabot** — `dependabot.yml` configured for daily Maven dependency version updates. **WhiteSource/Mend** — `.whitesource` config with vulnerability check failure on findings. The CI pipeline includes checkstyle validation (`spotless.yml`). Combined, this provides SAST (CodeQL) + dependency scanning (Dependabot + WhiteSource) coverage. |
| **Gap** | No container scanning (no production Dockerfile to scan). CodeQL runs but has no blocking gate configuration visible in the workflow — findings may not block merges. No DAST (Dynamic Application Security Testing) configured. |
| **Recommendation** | Add container image scanning when a production Dockerfile is added (ECR image scanning or Snyk container). Configure CodeQL findings as required status check to block PR merges on critical findings. Consider adding OWASP ZAP for DAST of deployed FHIR endpoints. |
| **Evidence** | `.github/workflows/codeql-analysis.yml`, `.github/dependabot.yml`, `.whitesource` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry instrumentation is built into the framework at multiple levels: **Root-level dependency** — `opentelemetry-instrumentation-annotations` is a global dependency in the root `pom.xml`, meaning all modules have access to OTel annotations. **Batch job tracing** — `BatchJobOpenTelemetryUtils.java` adds structured span attributes (job definition ID, version, step ID, instance ID, chunk ID) to batch job execution spans. **OTel agent testing** — `opentelemetry-agent-for-testing` and `opentelemetry-testing-common` are in the dependency management BOM for test verification of trace propagation. OpenTelemetry instrumentation version 2.10.0 is current. |
| **Gap** | Tracing is instrumented on primary modules (batch2) but coverage across all modules is not verified. No explicit trace context propagation between the REST server and backend services. The OTel integration is present but not comprehensive across all service boundaries. |
| **Recommendation** | Extend OTel instrumentation to FHIR REST server interceptors for request-level tracing. Add trace context propagation to the broker API for async message tracing. Export to AWS X-Ray in deployment configurations. |
| **Evidence** | `pom.xml` (opentelemetry-instrumentation-annotations global dependency), `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java`, `pom.xml` (otel_instrumentation.version=2.10.0) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No CloudWatch alarm configurations, error budget tracking, or formal service level definitions. As an open-source framework, SLOs are the deployer's responsibility, but no reference SLO definitions are provided for common FHIR server operations (search latency, CRUD response time, bulk export completion time). |
| **Gap** | No SLO definitions or reference SLO configurations for deployed FHIR servers. Organizations deploying HAPI FHIR must define SLOs from scratch. |
| **Recommendation** | Add reference SLO definitions for common FHIR operations: search latency p99, CRUD response time p95, bulk export throughput, validation response time. Include CloudWatch alarm configurations in reference IaC. |
| **Evidence** | Absence of SLO definitions, CloudWatch alarm configurations, or error budget tracking in any file |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics publishing found. No `cloudwatch.put_metric_data`, custom Prometheus metrics, or business KPI tracking. The framework's interceptor model enables custom metrics collection, but no out-of-box FHIR-specific business metrics are implemented (e.g., resources created per minute, search operations per resource type, subscription delivery latency). Only the OpenTelemetry instrumentation in batch2 provides operational metrics. |
| **Gap** | No business metrics for FHIR-specific outcomes. Infrastructure-only metrics (CPU, memory) are insufficient for understanding FHIR server health and usage patterns. |
| **Recommendation** | Add FHIR-specific business metrics using the interceptor framework: resources created/updated/deleted per resource type, search operation count and latency by resource type, subscription delivery success/failure rates, validation pass/fail rates. Publish to CloudWatch custom metrics. |
| **Evidence** | Absence of custom metrics publishing in source code; only OTel batch job attributes found |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found. No CloudWatch anomaly detection, static threshold alarms, composite alarms, or PagerDuty/OpsGenie integration. |
| **Gap** | No alerting infrastructure. Deployed FHIR servers have no monitoring alerts for error rate spikes, latency degradation, or capacity issues. |
| **Recommendation** | Add reference CloudWatch alarms in deployment IaC: anomaly detection on FHIR search latency, error rate threshold alarms, database connection pool exhaustion alerts. Include SNS notification topic for alarm routing. |
| **Evidence** | Absence of CloudWatch alarm configurations, alerting integrations, or anomaly detection setup |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy configuration found. No Helm charts, Kubernetes manifests, CodeDeploy configurations, Argo Rollouts, or blue/green deployment definitions. The CI/CD pipeline is build-and-publish (Maven artifacts to Central), not deploy. There is no staged rollout, canary deployment, or traffic shifting for FHIR server releases. |
| **Gap** | Direct-to-production deployment with no staged rollout. No reference deployment strategy for organizations deploying HAPI FHIR. |
| **Recommendation** | Add reference EKS deployment with Argo Rollouts for canary deployments. Include Helm chart with configurable deployment strategy (rolling update, blue/green, canary). For the FHIR server, canary deployments allow safe validation of schema migrations and API changes. |
| **Evidence** | Absence of Helm charts, Kubernetes manifests, CodeDeploy configs; CI/CD publishes to Maven Central only |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Extensive integration testing infrastructure: **Dedicated test modules** — `hapi-fhir-jpaserver-test-dstu2`, `hapi-fhir-jpaserver-test-dstu3`, `hapi-fhir-jpaserver-test-r4`, `hapi-fhir-jpaserver-test-r4b`, `hapi-fhir-jpaserver-test-r5` with 282 test files in R4 and 66 in R5 alone. **Test utilities** — `hapi-fhir-jpaserver-test-utilities` (167 Java files), `hapi-fhir-storage-batch2-test-utilities`, `hapi-fhir-storage-test-utilities`, `hapi-fhir-jpaserver-elastic-test-utilities`. **Testcontainers** — version 2.0.2 in BOM for database integration tests. **CI integration** — Parallel module testing via `parallel-pipeline-build.yml` with matrix strategy (up to 256 parallel jobs), Codecov coverage reporting. Architecture tests via `archunit-junit5`. |
| **Gap** | None — integration testing is comprehensive across all FHIR versions with database integration via Testcontainers and parallel CI execution. |
| **Recommendation** | Maintain the excellent testing infrastructure. Consider adding contract tests for the FHIR REST API surface (consumer-driven contracts) for external integrators. |
| **Evidence** | `hapi-fhir-jpaserver-test-r4/` (282 test files), `hapi-fhir-jpaserver-test-r5/` (66 test files), `hapi-fhir-jpaserver-test-utilities/` (167 files), `pom.xml` (testcontainers_version=2.0.2), `.github/workflows/parallel-pipeline-build.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns found. No Systems Manager Automation documents, Lambda-based remediation, or Step Functions for incident workflows. No markdown/YAML runbook files. |
| **Gap** | No incident response automation or runbooks. Deployed FHIR servers have no automated remediation for common incidents (database connection exhaustion, JVM heap pressure, bulk export failures). |
| **Recommendation** | Add operational runbooks for common FHIR server incidents: database connection pool exhaustion, search timeout spikes, bulk export failures, reindexing issues. Include SSM Automation documents for automated remediation (restart, scaling, cache clearing). |
| **Evidence** | Absence of runbook files, SSM documents, or automated remediation patterns |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CODEOWNERS file exists with module-level ownership: `hapi-fhir-storage-batch2/**/*.java` owned by `@michaelabuckley @jamesagnew @tadgh`, `hapi-fhir-jpaserver-subscription/**/*.java` owned by `@fil512 @tadgh @jamesagnew`, `hapi-fhir-jpaserver-mdm/**/*.java` owned by `@fil512 @tadgh @ad1306`, auth interceptors owned by `@jamesagnew`, data migrations owned by `@hapifhir/data-migrations`. However, no per-service dashboards, named alarm owners, or SLO definitions with team attribution exist. CODEOWNERS addresses code ownership but not operational/observability ownership. |
| **Gap** | Code ownership is defined but observability ownership is not. No per-service dashboards, named alarm owners, or SLO attribution to teams. |
| **Recommendation** | Extend CODEOWNERS to cover observability assets (dashboards, alarms, SLO definitions). Add per-module observability ownership mapping. Define on-call responsibilities per module group. |
| **Evidence** | `.github/CODEOWNERS` (code ownership defined), absence of dashboards, alarm ownership, or SLO team attribution |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging found. No `default_tags` in Terraform provider, no `tags` on resources, no tag policies, no Config rules for required tags. No IaC exists to tag. |
| **Gap** | No resource tagging governance. Deployed HAPI FHIR infrastructure has no cost allocation, ownership, or environment tags by default. |
| **Recommendation** | Include mandatory tagging in reference deployment IaC: `Environment`, `Application`, `Owner`, `CostCenter`, `FhirVersion`. Use Terraform `default_tags` or CDK `Tags.of()` for consistent application. |
| **Evidence** | Absence of IaC files and therefore absence of any tagging configuration |

---

## Learning Materials

**Triggered Pathways Learning Resources:**

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q11, APP-Q1, APP-Q2, OPS-Q1 | Root Maven POM — Java 17, Spring Boot 3.4.11, 60+ modules, OpenTelemetry global dependency, version 8.9.8-SNAPSHOT |
| `.github/workflows/pull-request.yml` | INF-Q11, SEC-Q5 | PR validation pipeline using GitHub Secrets |
| `.github/workflows/parallel-pipeline-build.yml` | INF-Q11, OPS-Q6 | Parallel module testing with matrix strategy (256 max parallel), Codecov integration |
| `.github/workflows/release.yml` | INF-Q11 | Release pipeline with version normalization and tag verification |
| `.github/workflows/codeql-analysis.yml` | SEC-Q7 | CodeQL SAST analysis — push, PR, and weekly schedule |
| `.github/workflows/spotless.yml` | INF-Q11 | Formatting enforcement with Spotless Maven plugin |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot for daily Maven dependency scanning |
| `.whitesource` | SEC-Q7 | WhiteSource/Mend vulnerability scanning configuration |
| `.github/CODEOWNERS` | APP-Q2, INF-Q3, OPS-Q8 | Module-level code ownership (batch2, subscription, MDM, auth interceptors) |
| `.github/docker/Dockerfile` | INF-Q1, INF-Q9, SEC-Q6 | Build-only Dockerfile — maven:3.9-eclipse-temurin-21-jammy |
| `release-pipeline.yml` | INF-Q11 | Azure Pipelines release pipeline |
| `snapshot-pipeline.yml` | INF-Q11, SEC-Q5 | Azure Pipelines nightly snapshot publishing |
| `hapi-fhir-sql-migrate/src/main/java/ca/uhn/fhir/jpa/migrate/DriverTypeEnum.java` | INF-Q2, DATA-Q3 | Database driver enum — H2, Derby, MariaDB, MySQL 5.7, PostgreSQL 9.4, Oracle 12C, MSSQL 2012, CockroachDB 21.1 |
| `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java` | INF-Q3, OPS-Q1 | OpenTelemetry span attributes for batch job execution monitoring |
| `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/api/` | INF-Q4, APP-Q3 | Broker API abstraction — IBrokerClient, IChannelProducer, IChannelConsumer (16 files) |
| `hapi-fhir-storage/src/main/java/ca/uhn/fhir/broker/jms/` | INF-Q4 | JMS adapter for broker API |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java` | SEC-Q1, SEC-Q3 | Authorization interceptor with fine-grained access control rules |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java` | SEC-Q3 | Consent-based data filtering interceptor |
| `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java` | INF-Q6, APP-Q5 | Dynamic OpenAPI spec generation for FHIR servers |
| `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/hapi-fhir-spring-boot-sample-server-jersey/src/main/resources/application.yml` | APP-Q6, SEC-Q5 | Sample application configuration — no hardcoded credentials |
| `hapi-fhir-structures-dstu2/` through `hapi-fhir-structures-r5/` | APP-Q5 | FHIR version-specific structure modules (DSTU2, DSTU3, R4, R4B, R5) |
| `hapi-fhir-jpa/` | DATA-Q2 | JPA data access layer |
| `hapi-fhir-jpaserver-base/` | DATA-Q1, DATA-Q2 | JPA server base with FHIR resource DAO implementations |
| `hapi-fhir-jpa-hibernate-services/` | DATA-Q2 | Hibernate-specific service implementations |
| `hapi-fhir-sql-migrate/` | DATA-Q2, DATA-Q3 | Programmatic schema migration framework |
| `hapi-fhir-jpaserver-test-utilities/src/main/resources/migration/` | DATA-Q3, DATA-Q4 | 87 SQL migration files across multiple database platforms and HAPI versions |
| `hapi-fhir-jpaserver-test-r4/` | OPS-Q6 | R4 integration test module — 282 test files |
| `hapi-fhir-jpaserver-test-r5/` | OPS-Q6 | R5 integration test module — 66 test files |
| `hapi-fhir-jpaserver-test-utilities/` | OPS-Q6 | Test utility framework — 167 Java files |
| `hapi-fhir-storage-batch2/` | INF-Q3, APP-Q4 | Batch job orchestration framework with step execution, chunking, reduction |
| `hapi-fhir-jpaserver-subscription/` | INF-Q4, APP-Q3 | FHIR Subscription processing with broker API integration |
| `hapi-fhir-docs/` | Quick Agent Wins | Documentation module with changelogs and FHIR usage documentation |
| `README.md` | Quick Agent Wins | Project overview and links to documentation site |
