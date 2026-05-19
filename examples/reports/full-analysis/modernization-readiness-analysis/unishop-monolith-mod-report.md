# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | MonoToMicroLegacy |
| **Date** | 2026-05-18 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P0 |
| **Tags** | monolith, java, ec2, decomposition-target |
| **Context** | Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs. |
| **Overall Score** | 1.40 / 4.0 |

**Archetype Justification**: MySQL database with CRUD operations on unicorns, basket, and user entities. Write endpoints (POST/DELETE) with user-specific data (userUuid basket). Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 1.09 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 1.50 / 4.0 | ❌ Not Ready | Critical |
| Data Platform (DATA) | 2.25 / 4.0 | 🟠 Needs Work | Critical |
| Security Baseline (SEC) | 1.17 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.40 / 4.0** | **❌ Not Ready** | **Critical** |

**Scoring Notes:**
- INF: (1+1+2+1+1+1+1+1+1+1+1) / 11 = 12/11 = 1.09
- APP: (2+2+1+1+1+2) / 6 = 9/6 = 1.50
- DATA: (1+3+1+4) / 4 = 9/4 = 2.25
- SEC: (1+1+2+1+1+1) / 6 = 7/6 = 1.17 (SEC-Q1 Not Evaluated, excluded)
- OPS: (1+1+1+1+1+1+1+1+1) / 9 = 9/9 = 1.00
- Overall: (1.09+1.50+2.25+1.17+1.00) / 5 = 7.01/5 = 1.40

---

## Classification

**Tier: Remediation Required**

This repo has 11 High findings, 22 Medium findings, 1 Low finding. Rule matched: "2-11 High → Remediation Required."

MOD classification uses a softer threshold than ARA for single-High findings. ARA gates on agent safety where 1 High is a deployment blocker. MOD measures modernization maturity where 1 High is typically one modernization gap rather than a deployment blocker. For MOD, "1 High → Pilot-Ready" whereas ARA would classify that as Remediation Required.

> **⚠️ Classification Consistency Warning:** The score-based band (overall score 1.40 → "Not Ready") diverges from the count-based tier (11 High → "Remediation Required"). This divergence occurs because 29 of 36 evaluated questions score 1, but only 11 are on core questions (producing High findings). The remaining 18 score-1 findings on non-core questions produce Medium severity, keeping the High count at 11 rather than ≥12. The count-based tier ("Remediation Required") is authoritative for the classification. The extremely low overall score (1.40) reflects the breadth of gaps across all dimensions — this system requires comprehensive modernization across infrastructure, application architecture, security, and operations.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC — all infrastructure manually provisioned | No reproducibility, no disaster recovery automation, no environment consistency |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline exists | Manual deployments are error-prone, slow, and prevent continuous delivery |
| 3 | SEC-Q5: Secrets Management | 1 | Plaintext database password in application.properties committed to git | Critical security vulnerability — credentials exposed in source control |
| 4 | APP-Q2: Monolith vs Microservices | 2 | Tightly-coupled monolith with shared database schema | Cannot scale components independently, blocks team autonomy and deployment independence |
| 5 | INF-Q1: Managed Compute | 1 | All compute on raw EC2 with no managed services | Manual scaling, patching, and capacity planning required |

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 < 3 (primary); INF-Q1=1, APP-Q3=1, APP-Q4=1 (supporting) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 < 3; no container definitions found; compute is EC2 (not Lambda/Fargate/ECS) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no proprietary SQL detected |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 < 3; DATA-Q3=1 < 3 (supporting) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads (streaming, ETL, analytics) detected; contextual guard blocks |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 < 3; INF-Q11=1 < 3; OPS-Q5=1, OPS-Q6=1 (supporting) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Single Spring Boot JAR deployed on EC2. Monolithic architecture with shared MySQL database schema. All entities (unicorns, basket, users) coupled in one deployable unit. Identifiable domain boundaries exist (product catalog, basket, user management) but are tightly coupled through shared schema.

**Compute Model Gaps:** All compute on raw EC2 (INF-Q1=1). No managed container orchestration or serverless.

**Communication Pattern Gaps:** All communication is synchronous HTTP (APP-Q3=1). No async messaging for state change propagation. No background job processing for long-running operations (APP-Q4=1).

**Recommended Decomposition Approach:** See Decomposition Strategy section below.

**Recommended AWS Services** (aligned with preferences for EKS, Aurora, DynamoDB, API Gateway, EventBridge, containers, microservices-decomposition):
- Amazon EKS for container orchestration
- Amazon API Gateway for unified API entry point
- Amazon EventBridge for event-driven communication between decomposed services
- AWS Step Functions for workflow orchestration
- Amazon Aurora MySQL for managed relational data

**Recommended Patterns:**
- Strangler Fig pattern for incremental extraction
- Anti-corruption Layer between new services and legacy monolith
- Event Sourcing for state change propagation
- Saga pattern for distributed transactions

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Application runs as a Spring Boot executable JAR directly on EC2 (`bootJar { launchScript() }`). No Dockerfile or container definitions exist. No Kubernetes manifests or Helm charts.

**Container Readiness Indicators:**
- Application produces a self-contained JAR (good for containerization)
- External configuration via environment variable (`MONO_TO_MICRO_DB_ENDPOINT`)
- Single port binding (8080)
- No local filesystem dependencies for business data

**Recommended Container Platform** (aligned with preference for EKS, containers; avoiding self-managed-kubernetes):
- Amazon EKS with managed node groups for container orchestration
- Amazon ECR for container image registry
- Karpenter for node auto-scaling

**Migration Approach:** Lift-and-containerize first (create Dockerfile for existing JAR), then refactor architecture. Containerizing the monolith is a prerequisite for the Cloud Native pathway.

**AWS Container Migration Guidance:**
- [EKS Workshop](https://www.eksworkshop.com/)
- [Containerizing Java applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-containers/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** MySQL database referenced via environment variable (`MONO_TO_MICRO_DB_ENDPOINT:3306`). No IaC defines the database — likely manually provisioned on EC2 or standalone instance. MySQL connector 8.0.11 in use.

**Engine Versions and EOL Status:** No version pinning in IaC. MySQL connector 8.0.11 (released 2018) suggests an older MySQL 8.0 server. No version lifecycle management.

**Data Access Patterns:** Consistent MyBatis mapper layer (DATA-Q2=3). Simple CRUD operations on 3 tables. No stored procedures or proprietary SQL (DATA-Q4=4).

**Recommended Managed Database Target** (aligned with preferences for Aurora MySQL):
- **Amazon Aurora MySQL** — compatible engine, managed failover, automated backups, Multi-AZ by default
- Migration path: Use AWS Database Migration Service (DMS) for minimal-downtime migration
- Enable Multi-AZ for high availability
- Configure automated backups with PITR

**Migration Tools:**
- AWS Database Migration Service (DMS) for continuous replication during cutover
- AWS Schema Conversion Tool (SCT) if schema adjustments needed (minimal for MySQL → Aurora MySQL)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** 0% — no Terraform, CloudFormation, CDK, or any Infrastructure as Code exists (INF-Q10=1). All infrastructure is manually provisioned.

**Current CI/CD State:** No CI/CD pipeline exists (INF-Q11=1). No GitHub Actions, Jenkins, CodePipeline, CodeBuild, or any automation. Deployments are fully manual.

**Deployment Strategy Gaps:** No deployment strategy — direct manual deployment to production (OPS-Q5=1).

**Testing Gaps:** Zero automated tests despite `spring-boot-starter-test` being declared in dependencies (OPS-Q6=1).

**Recommended DevOps Toolchain** (aligned with preferences for Terraform, GitOps, containers; avoiding manual-deployments):
- **Terraform** for Infrastructure as Code (VPC, EKS, Aurora, security groups)
- **GitHub Actions or AWS CodePipeline** for CI/CD automation
- **ArgoCD** for GitOps-based deployment to EKS
- **AWS CodeBuild** for container image builds
- Progressive delivery via ArgoCD Rollouts (canary/blue-green)

**Immediate Actions:**
1. Define infrastructure in Terraform (VPC, subnets, security groups, Aurora, EKS)
2. Create CI pipeline: build → test → container image → push to ECR
3. Create CD pipeline: GitOps deployment via ArgoCD to EKS
4. Add integration test suite for critical workflows before decomposition

---

## Decomposition Strategy

APP-Q2 scored 2 — the application is a monolith with identifiable modules (product catalog, basket, user management) but shared database schema and tight coupling.

### Recommended Approach: Strangler Fig (Parallel Track)

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strengthen as Modular Monolith** | Keep single deployable; enforce module boundaries | Small team, acceptable deployment cadence | Low (2-6 months) | Consider as intermediate step before full decomposition |
| **Strangler Fig (Parallel Track)** | Incrementally extract services while monolith runs | Identifiable module boundaries exist; strong drivers for decomposition | Medium to High (6-18 months) | ✅ **Recommended** — lowest risk, incremental value delivery |
| **Conditional / Adaptive** | Containerize monolith first, then selectively extract | Limited capacity for full decomposition | Low to Medium (3-12 months) | ✅ **Recommended as starting point** given current state (no containers, no IaC) |
| **Big-Bang Rewrite** | Rewrite entire application as microservices | Almost never | Very High (12-24+ months) | ⚠️ **Recommended against** — high risk of failure |

**Recommended Strategy:** Start with **Conditional / Adaptive** — containerize the monolith on EKS first (Move to Containers pathway), establish CI/CD (Move to Modern DevOps pathway), then apply **Strangler Fig** to extract services incrementally.

### Extraction Priority (based on context: "agent needs access to order and return data through discrete service APIs"):
1. **Basket/Order Service** — Extract basket management as first independent service (highest business value for API access)
2. **User Service** — Extract user/authentication as independent service
3. **Product Catalog Service** — Extract unicorn product listing

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate new service from monolith's data model | Every extraction — place ACL between new service and monolith |
| **Saga Pattern** | Manage distributed transactions | When basket operations span multiple services |
| **Event Sourcing** | Capture state changes as events | When basket/order events need to propagate across services |
| **Hexagonal Architecture** | Clear boundaries in each new service | Every new service — ensures testability and decoupling |

### Effort Estimation Factors

| Factor | Signal | Assessment |
|--------|--------|------------|
| Module boundaries | Layered architecture with controllers/services/repos | Moderate — boundaries exist but are implicit |
| Data coupling | Single `unishop` schema, 3 tables with shared patterns | Moderate — tables are domain-specific but share schema |
| Stored procedures | None — all logic in application layer | Low effort (favorable) |
| Communication patterns | All synchronous, no async | High effort — need to introduce async |
| CI/CD maturity | None | High effort — need to build from scratch |
| Test coverage | Zero tests | High risk — no regression safety net |

**Calibrated Effort Estimate:** High effort overall due to zero test coverage and zero CI/CD. Establish testing and automation infrastructure BEFORE beginning service extraction.

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | High |
| **Phase** | 1 |
| **Finding** | All compute runs on raw EC2. The application produces an executable JAR with embedded launch script (`bootJar { launchScript() }` in build.gradle) deployed directly to EC2 instances. No managed container orchestration (ECS/EKS), no serverless (Lambda), no Fargate. |
| **Gap** | No managed compute services in use. All operational burden (patching, scaling, capacity planning) is manual. |
| **Recommendation** | Containerize the application and deploy on Amazon EKS with managed node groups. Create a Dockerfile for the Spring Boot JAR, push to ECR, and deploy via Helm charts to EKS. Use Karpenter for node auto-scaling. |
| **Evidence** | `build.gradle` (bootJar with launchScript); absence of Dockerfile, Kubernetes manifests, ECS/Lambda IaC |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | MySQL database referenced via `spring.datasource.url: jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. No IaC defines the database as a managed service. No evidence of RDS/Aurora — database is likely self-managed on EC2 given the context ("Legacy Java Spring Boot monolith on EC2 with MySQL"). |
| **Gap** | No managed database service. Self-managed MySQL requires manual patching, backup management, failover configuration, and scaling. |
| **Recommendation** | Migrate to Amazon Aurora MySQL — compatible engine with automated failover, backups, and Multi-AZ. Use AWS DMS for minimal-downtime migration. Enable automated backups with PITR. |
| **Evidence** | `src/main/resources/application.properties` (MySQL connection string); `database/create_tables.sql` (MySQL DDL); absence of `aws_rds_*` or `aws_aurora_*` in IaC |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | The application uses an internal event-driven pattern (16 event classes in `com.monoToMicro.core.events`) for structuring operations within the monolith. This provides some architectural structure to request handling but is not a dedicated orchestration service. No Step Functions, Temporal, or equivalent. Archetype: stateful-crud — the current operations (CRUD on basket/unicorns/users) are simple enough that dedicated orchestration is not critical, but the event pattern shows awareness of structured flow management. |
| **Gap** | Internal event pattern provides structure but no dedicated workflow orchestration for multi-step operations. As the system grows and decomposes, coordinated workflows (e.g., order processing) will need explicit orchestration. |
| **Recommendation** | When decomposing the monolith, adopt AWS Step Functions for multi-step business workflows (order processing, user onboarding). The existing event pattern provides a foundation for identifying workflow boundaries. |
| **Evidence** | `src/main/java/com/monoToMicro/core/events/` (16 event classes); absence of Step Functions, Temporal, or workflow engine |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No messaging or streaming infrastructure exists. All operations are synchronous HTTP request/response. The internal event classes are plain Java objects passed synchronously between layers — not async message passing. No SQS, SNS, EventBridge, Kafka, or any message broker. Archetype: stateful-crud — for a CRUD service with state changes (basket add/remove, user creation), managed messaging would enable decoupled event propagation. |
| **Gap** | No messaging infrastructure for state change propagation. Basket operations, user creation, and product changes are all synchronous with no event emission for downstream consumers. This blocks the decomposition goal where "the agent needs access to order and return data through discrete service APIs." |
| **Recommendation** | Introduce Amazon EventBridge for domain event publishing (basket changes, user events). When decomposing, each extracted service publishes events to EventBridge for loose coupling between services. Avoid self-managed Kafka per preferences. |
| **Evidence** | Absence of SQS/SNS/EventBridge/Kafka imports or IaC; all controller methods return synchronous responses; `com/monoToMicro/core/events/` contains synchronous POJOs only |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists in this repository. The application exposes port 8080 directly. No evidence of private subnets, least-privilege network rules, or managed networking services. |
| **Gap** | No network security configuration. Service likely exposed without proper isolation. No VPC endpoints, no PrivateLink, no network segmentation between application and database tiers. |
| **Recommendation** | Define VPC infrastructure in Terraform: private subnets for application and database tiers, public subnet only for ALB/API Gateway. Security groups with least-privilege rules. VPC endpoints for AWS service access. |
| **Evidence** | Absence of any VPC, subnet, or security group definitions; `application.properties` shows direct DB connection on port 3306 |

> ⚠️ Network security IaC may exist in a separate infrastructure repository. Score reflects evidence available in this repo only.

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No API Gateway, ALB, or CloudFront configured. The Spring Boot application serves directly on port 8080 with no managed entry point providing throttling, authentication, or request validation. |
| **Gap** | No managed API entry point. No throttling, no centralized auth, no request validation at the edge. Direct service exposure. |
| **Recommendation** | Deploy Amazon API Gateway as the entry point (aligned with preferences). Configure throttling, request validation, and integrate with Amazon Cognito for authentication. Route traffic through API Gateway to the application (or ALB in front of EKS after containerization). |
| **Evidence** | `application.properties` (`server.port=8080`); absence of API Gateway, ALB, or CloudFront IaC |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | No auto-scaling configuration exists. The application runs on EC2 with static capacity. No ASG, no ECS service scaling, no Lambda concurrency management, no DynamoDB auto-scaling. |
| **Gap** | All capacity is statically provisioned. Cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | After containerization on EKS, configure Horizontal Pod Autoscaler (HPA) with appropriate metrics. Use Karpenter for node-level auto-scaling. After database migration to Aurora, enable Aurora auto-scaling for read replicas. |
| **Evidence** | Absence of `aws_autoscaling_*`, `aws_appautoscaling_*`, HPA, or scaling policy definitions |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no backup retention settings, no PITR configuration, no S3 versioning, no EBS snapshot policies. The MySQL database has no documented backup strategy. |
| **Gap** | No automated backups. A data loss event would be unrecoverable without manual intervention (if backups exist externally). |
| **Recommendation** | After migrating to Aurora MySQL, automated backups are included (35-day retention default). Enable PITR. For additional protection, configure AWS Backup with cross-region replication for critical data. |
| **Evidence** | Absence of backup configuration in any file; no `backup_retention_period`, no `aws_backup_plan` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No multi-AZ deployment evidence. Single EC2 instance implied by context ("monolith on EC2"). No AZ configuration, no cross-zone load balancing, no multi-AZ database configuration. |
| **Gap** | Single-AZ deployment — an AZ failure takes down the entire workload with no automatic recovery. |
| **Recommendation** | After containerization on EKS, deploy pods across multiple AZs. Configure Aurora MySQL with Multi-AZ failover. Use ALB with cross-zone load balancing enabled. |
| **Evidence** | Absence of multi-AZ configuration; no `availability_zones`, no `multi_az = true`, no cross-zone settings |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | High |
| **Phase** | 1 |
| **Finding** | 0% IaC coverage. No Terraform, CloudFormation, CDK, Helm charts, or any Infrastructure as Code exists in this repository. All infrastructure (EC2, MySQL, networking) is manually provisioned. |
| **Gap** | All infrastructure is manually created (ClickOps). No reproducibility, no version control for infrastructure changes, no automated disaster recovery. |
| **Recommendation** | Define all infrastructure in Terraform (aligned with preferences): VPC, subnets, security groups, EKS cluster, Aurora MySQL, API Gateway, ECR repositories. Use Terraform modules for reusability. Store state in S3 with DynamoDB locking. |
| **Evidence** | Complete absence of `.tf`, `template.yaml`, `cdk.json`, or any IaC files in the repository |

> ⚠️ IaC may exist in a separate infrastructure repository. Score reflects evidence available in this repo only.

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | No CI/CD pipeline exists. No GitHub Actions workflows, no Jenkinsfile, no buildspec.yml, no appspec.yml, no CodePipeline definitions. All builds and deployments are manual. |
| **Gap** | All deployments are manual — error-prone, slow, and prevent continuous delivery. No automated testing, building, or deployment. |
| **Recommendation** | Implement CI/CD pipeline: GitHub Actions or AWS CodePipeline for automation. Stages: lint → build → test → container image → push to ECR → deploy via ArgoCD (GitOps). Add Terraform plan/apply stages for IaC changes. |
| **Evidence** | Absence of `.github/workflows/`, `Jenkinsfile`, `buildspec.yml`, `appspec.yml`, or pipeline definitions |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | High |
| **Phase** | 2 |
| **Finding** | Java 8 (`sourceCompatibility = 1.8`) with Spring Boot 2.1.6.RELEASE and AWS SDK v1.11.567. All three axes are regressed: Java 8 is EOL (since March 2022), Spring Boot 2.1.x is EOL (since November 2019), and AWS SDK v1 is in maintenance mode (v2 is the current generation). |
| **Gap** | Compound legacy — language version (Java 8), framework (Spring Boot 2.1.x), AND SDK (AWS SDK v1) are all past end-of-life or deprecated. This blocks access to modern features, security patches, and performance improvements. |
| **Recommendation** | Upgrade to Java 17+ with Spring Boot 3.x and AWS SDK v2. This is a prerequisite for containerization on modern base images and for accessing current AWS service features. Recommended upgrade path: Java 8 → 17, Spring Boot 2.1 → 3.x (requires javax → jakarta namespace migration), AWS SDK v1 → v2. |
| **Evidence** | `build.gradle` (`sourceCompatibility = 1.8`, Spring Boot 2.1.6.RELEASE, `com.amazonaws:aws-java-sdk:1.11.567`) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Severity** | Medium |
| **Priority** | P1 |
| **Effort** | High |
| **Phase** | 1 |
| **Finding** | Single deployable Spring Boot JAR containing all domains: product catalog (unicorns), shopping basket, and user management. Layered architecture exists (Controllers → Services → Repositories → MyBatis Mappers) with some domain separation. However, all three domains share the single `unishop` database schema. The `unicorns_basket` table references `unicornUuid` directly, coupling basket to product catalog at the data level. |
| **Gap** | Monolith with identifiable modules but shared database schema and direct cross-module data access. Cannot deploy, scale, or develop modules independently. Blocks the stated goal of "discrete service APIs" for order and return data access. |
| **Recommendation** | Apply Strangler Fig decomposition pattern. Start by containerizing the monolith, then extract basket/order service first (highest business value per context). Separate database schemas per service. See Decomposition Strategy section. |
| **Evidence** | Single `build.gradle` producing one JAR; shared `unishop` schema in `database/create_tables.sql`; single `Application.java` entry point; all controllers in one deployment |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | All communication is synchronous HTTP request/response. The internal event classes (`com.monoToMicro.core.events`) are synchronous POJOs passed between layers — not async message passing. No message queue consumers, no event-driven handlers, no async patterns. As a stateful-crud service, cross-service state propagation (basket changes, user creation) should use async messaging for decoupling. |
| **Gap** | 100% synchronous with no async patterns. When decomposed into microservices, this tight coupling creates cascading failure risk and blocks independent service evolution. |
| **Recommendation** | Introduce Amazon EventBridge for domain events when decomposing. Basket add/remove, user creation, and product changes should emit events consumed by interested services asynchronously. This enables the "discrete service APIs" goal without tight coupling. |
| **Evidence** | All controller methods return synchronous `ResponseEntity`; `core/events/` package contains synchronous data transfer objects only; no SQS/SNS/EventBridge imports |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 3 |
| **Finding** | All operations are synchronous regardless of duration. The current CRUD operations (basket add/remove, product listing) are fast, but no async job infrastructure exists. As the system grows (order processing, bulk operations, data exports), there is no pattern for handling operations >30 seconds. The `DataReplicationController` endpoint (`GET /data`) could potentially be long-running for large datasets but is handled synchronously. |
| **Gap** | No async job infrastructure. As the system evolves toward order processing (per context: "order and return data"), long-running operations (order fulfillment, returns processing, bulk data access) will need async handling with status polling. |
| **Recommendation** | Implement async job pattern: submit job → return job ID → poll status endpoint. Use AWS Step Functions for orchestrating multi-step order/return workflows. SQS for job queuing with worker services. |
| **Evidence** | All controller methods are synchronous; `DataReplicationController.java` handles data export synchronously; no background job framework (no Celery, Bull, SQS workers) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | No API versioning. All endpoints use unversioned paths: `/unicorns`, `/user`, `/health`, `/data`. No `/v1/` prefix, no version headers, no versioning annotations. |
| **Gap** | No versioning — any API change is a breaking change for all consumers. When the system is decomposed and APIs are exposed to agents/external consumers, breaking changes cannot be deployed safely. |
| **Recommendation** | Adopt URL-path versioning (`/v1/unicorns`, `/v1/basket`) as part of the decomposition. API Gateway supports versioning natively. Define backward compatibility policy for each service API. |
| **Evidence** | Controller mappings: `@RequestMapping("/unicorns")`, `@RequestMapping("/user")`, `@RequestMapping("/health")` — no version prefix |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | Environment variable used for the database endpoint (`${MONO_TO_MICRO_DB_ENDPOINT}`) — basic externalization but no dynamic discovery. As a monolith with one external dependency (MySQL), service discovery is minimally needed. No service mesh, no AWS Cloud Map, no Consul. |
| **Gap** | Environment variables for endpoints but no dynamic discovery mechanism. When decomposed into multiple services, hardcoded or static endpoint configuration will not scale. |
| **Recommendation** | After decomposition to EKS, use Kubernetes native service discovery (DNS-based). For cross-cluster or external service communication, use AWS Cloud Map or VPC Lattice. API Gateway provides a service catalog for external consumers. |
| **Evidence** | `application.properties` (`${MONO_TO_MICRO_DB_ENDPOINT}`); no service registry, Cloud Map, or mesh configuration |

---

### Data Platform (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | Product images are referenced by name strings in the database (`image varchar(256)`) but no S3 bucket or object storage is configured for storing/serving these images. AWS S3 SDK is included in dependencies (`com.amazonaws:aws-java-sdk-s3:1.11.567`) but no S3 usage was found in the application source code. Images appear to be served from an undocumented external source. |
| **Gap** | No managed object storage with parsing capabilities. Product images are not stored in S3 with metadata and parsing pipelines. No document storage strategy for potential future unstructured data (returns documentation, product descriptions, user uploads). |
| **Recommendation** | Store product images in Amazon S3 with appropriate lifecycle policies. For future order/return document processing, implement S3 with Amazon Textract for parsing. Define a clear unstructured data management strategy as part of decomposition. |
| **Evidence** | `database/create_tables.sql` (`image varchar(256)` stores name only); `build.gradle` (S3 SDK dependency present but unused in source); no `aws_s3_bucket` IaC |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Severity** | Low |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | Consistent repository pattern implemented throughout: Controllers → Services → Repositories → MyBatis Mappers. All database access is centralized through MyBatis mapper interfaces (`UnicornMapper`, `UserMapper`, `HealthMapper`) with XML-based SQL mapping files. No direct JDBC access scattered across the codebase. |
| **Gap** | Mostly centralized but the repository layer directly exposes MyBatis-specific patterns. No abstraction layer that would allow swapping the persistence technology without touching service code. Some coupling between service layer and MyBatis types. |
| **Recommendation** | Maintain the repository pattern during decomposition. When extracting services, each service should own its data access layer. Consider adopting Spring Data JPA or a similar abstraction for new services to reduce ORM coupling. |
| **Evidence** | `src/main/java/com/monoToMicro/core/repository/` (6 repository files); `src/main/resources/com/monoToMicro/core/repository/mappers/` (3 XML mapper files); consistent pattern across all domains |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | No database engine version is pinned in IaC (no IaC exists). The MySQL connector version 8.0.11 (released April 2018) suggests MySQL 8.0 server, but the exact server version is undetermined. No version lifecycle management, no documented upgrade procedure. MySQL 8.0 is still supported but reaches EOL in April 2026 — approaching end of support. |
| **Gap** | No version pinning, no lifecycle management. Database engine version is uncontrolled — could be running any MySQL 8.0.x patch level without awareness of security patches or EOL timeline. |
| **Recommendation** | After migrating to Aurora MySQL, engine versions are managed with configurable upgrade windows. Pin Aurora MySQL engine version in Terraform, enable minor version auto-upgrade, and document major version upgrade procedure with rollback plan. |
| **Evidence** | `build.gradle` (`mysql:mysql-connector-java:8.0.11`); absence of any IaC with engine version pinning |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. The `database/create_tables.sql` contains only DDL (CREATE SCHEMA, CREATE TABLE) and INSERT statements. All business logic resides in the Java application layer (services and repositories). MyBatis mapper XML files use standard SQL (SELECT, INSERT, DELETE) without MySQL-specific extensions. |
| **Gap** | N/A |
| **Recommendation** | N/A — continue keeping business logic in the application layer. This favorable state simplifies database migration (no logic extraction required). |
| **Evidence** | `database/create_tables.sql` (DDL only, no CREATE PROCEDURE/TRIGGER/FUNCTION); MyBatis mapper XMLs use standard SQL |

---

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This repository contains no IaC provisioning AWS resources. Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application source code only, which is the correct scope for an application repo. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Low |
| **Phase** | 1 |
| **Finding** | No encryption at rest configured for any data store. No KMS keys, no encryption settings on the MySQL database, no S3 bucket encryption, no EBS encryption. The database stores user data (email, names) and business data (products, baskets) without documented encryption. |
| **Gap** | No encryption at rest. User PII (email, names) stored unencrypted. No KMS key management, no rotation policy. |
| **Recommendation** | After migrating to Aurora MySQL, enable encryption at rest with AWS KMS customer-managed key. Aurora encrypts storage, backups, and replicas automatically. Define KMS key rotation policy. |
| **Evidence** | Absence of `kms_key_id`, `aws_kms_key`, or encryption configuration in any file; `database/create_tables.sql` stores PII (email, names) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | Security is effectively disabled. `ResourceServerConfig.java` extends `ResourceServerConfigurerAdapter` with `@EnableResourceServer` but configures all endpoints as `permitAll()`. Spring Security OAuth2 and JWT libraries are in dependencies but not enforced. All API endpoints are open without authentication. |
| **Gap** | No API authentication — all endpoints are publicly accessible without any credential verification. This is a critical security vulnerability. |
| **Recommendation** | Implement API authentication via Amazon API Gateway with Amazon Cognito authorizer. Configure OAuth2/JWT validation on all endpoints. Remove `permitAll()` from security configuration. For internal service-to-service auth after decomposition, use IAM roles or mutual TLS. |
| **Evidence** | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (all endpoints `permitAll()`); `build.gradle` (Spring Security OAuth2 dependencies present but not enforced) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | Spring Security OAuth2 Resource Server (`@EnableResourceServer`) and JWT libraries are configured, indicating the application is structurally prepared for external IdP federation. However, the configuration is non-functional — `permitAll()` bypasses all authentication. The application has its own user management (`UserController`, `unicorn_user` table) but could federate with external IdPs through the existing OAuth2 infrastructure. |
| **Gap** | OAuth2/JWT infrastructure exists but is disabled. Application manages its own user authentication (email/password in `unicorn_user` table) with no external IdP integration active. |
| **Recommendation** | Integrate with Amazon Cognito as centralized IdP. Migrate user authentication from the application's `unicorn_user` table to Cognito User Pool. Configure OAuth2 flows through Cognito. Enable SSO for consistent identity across decomposed services. |
| **Evidence** | `ResourceServerConfig.java` (`@EnableResourceServer`); `build.gradle` (`spring-security-oauth2-autoconfigure`, `spring-security-jwt`); `UserController.java` (custom login/create endpoints) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Low |
| **Phase** | 1 |
| **Finding** | Plaintext database credentials committed to source control in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. These are hardcoded values (not references to a secret store) checked into the repository. |
| **Gap** | Critical security vulnerability — plaintext credentials in version-controlled source. Anyone with repository access has database credentials. No secrets rotation, no audit trail for credential access. |
| **Recommendation** | Immediately move credentials to AWS Secrets Manager with automated rotation. Reference secrets via Spring Cloud AWS Secrets Manager integration or environment variables populated from Secrets Manager at deployment time. Remove plaintext credentials from application.properties and git history. |
| **Evidence** | `src/main/resources/application.properties` (`spring.datasource.password: MonoToMicroPassword`) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No evidence of compute hardening or patching strategy. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base images. No EC2 Image Builder pipelines. The application runs on unspecified EC2 AMIs with no documented patching process. |
| **Gap** | No patching strategy, no vulnerability scanning, no hardened images. EC2 instances may be running with known vulnerabilities. |
| **Recommendation** | After containerization on EKS, use hardened base images (Amazon Linux 2023 or Bottlerocket for nodes). Enable Amazon Inspector for container image scanning. Integrate Snyk or Trivy into CI/CD pipeline for dependency and container vulnerability scanning. |
| **Evidence** | Absence of SSM configuration, Inspector setup, or hardened AMI references; no vulnerability scanning tooling |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | No CI/CD pipeline exists, therefore no security scanning is integrated. No SAST tools (SonarQube, Semgrep, CodeGuru), no dependency scanning (Dependabot, Snyk), no container scanning. No `.snyk` policy file, no Dependabot configuration. |
| **Gap** | No security scanning — vulnerabilities in dependencies (many are outdated: Spring Boot 2.1.x, AWS SDK v1, MySQL connector 8.0.11) and application code reach production undetected. |
| **Recommendation** | When implementing CI/CD (Move to Modern DevOps pathway), include: Dependabot for dependency vulnerability alerts, Snyk or Trivy for container image scanning, Amazon CodeGuru Reviewer or SonarQube for SAST. Configure security gates to block deployment on critical findings. |
| **Evidence** | Absence of `.github/dependabot.yml`, `.snyk`, SonarQube config, or security scan steps in any pipeline |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | No distributed tracing instrumented. No X-Ray SDK, no OpenTelemetry dependencies, no trace ID propagation headers. Spring Boot Actuator is present but provides only basic metrics — not distributed tracing. |
| **Gap** | No tracing. Cannot trace requests through the application or (after decomposition) across service boundaries. Debugging production issues requires log correlation without structured trace context. |
| **Recommendation** | Instrument with AWS X-Ray SDK or OpenTelemetry (ADOT). After containerization on EKS, deploy the ADOT Collector as a DaemonSet for automatic trace collection. Propagate trace IDs in all inter-service calls. |
| **Evidence** | `build.gradle` (no X-Ray or OpenTelemetry dependencies); absence of trace instrumentation in source code |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No SLOs defined. No CloudWatch alarms, no latency targets, no error rate thresholds, no error budget tracking. The only monitoring is the basic Spring Boot Actuator health endpoint and a manual database ping endpoint (`/health/dbping`). |
| **Gap** | No formal definition of acceptable service levels. Cannot measure whether the system meets user expectations or track degradation over time. |
| **Recommendation** | Define SLOs for critical user journeys: product listing latency (p99 < 500ms), basket operations availability (99.9%), login success rate. Implement with CloudWatch alarms after infrastructure is in place. |
| **Evidence** | `HealthController.java` (basic health check only); absence of CloudWatch alarm definitions, SLO config files, or monitoring dashboards |

> ⚠️ SLO definitions may exist in external monitoring platforms not visible in this repository.

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No custom business metrics published. No `cloudwatch.put_metric_data` calls, no Micrometer custom metrics, no business KPI tracking. Only default Spring Boot Actuator infrastructure metrics (JVM, HTTP request counts). |
| **Gap** | No visibility into business outcomes — basket conversion rates, product view counts, user signups, abandoned baskets. Cannot make data-driven modernization or business decisions. |
| **Recommendation** | Instrument business metrics: basket additions/removals per minute, user registrations, product page views. Use Micrometer with CloudWatch exporter after Spring Boot upgrade. Define dashboards for business KPIs. |
| **Evidence** | Absence of custom metric publishing in any controller or service class; no Micrometer custom metrics configuration |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No alerting configured. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. No composite alarms, no error rate monitoring. |
| **Gap** | No alerting — the team has no automated notification when the system degrades or fails. Issues are discovered by users, not monitoring. |
| **Recommendation** | After infrastructure is defined in Terraform, configure CloudWatch alarms for: HTTP 5xx error rate > 1%, p99 latency > 2s, database connection failures. Enable CloudWatch anomaly detection on key metrics. Integrate with PagerDuty or OpsGenie for on-call notification. |
| **Evidence** | Absence of CloudWatch alarm definitions, monitoring configuration, or alerting integrations |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | No deployment strategy. No CodeDeploy configuration, no blue/green setup, no canary deployment, no rolling updates. The application is deployed directly to EC2 via manual process (JAR copy and restart implied by `bootJar { launchScript() }`). |
| **Gap** | Direct-to-production deployment with no staged rollout. Any deployment failure affects all users immediately with no automated rollback. |
| **Recommendation** | After containerization on EKS, implement progressive delivery via ArgoCD Rollouts with canary strategy (aligned with GitOps preference). Start with 10% canary → analysis → full promotion. Configure automated rollback on error rate increase. |
| **Evidence** | `build.gradle` (`bootJar { launchScript() }` — direct JAR execution on EC2); absence of CodeDeploy, Helm canary, ArgoCD, or deployment strategy configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | Zero automated tests. No test directory (`src/test/`) exists. The `spring-boot-starter-test` dependency is declared in `build.gradle` but no test classes have been written. No integration tests, no unit tests, no contract tests. |
| **Gap** | No automated testing whatsoever. Any code change (including the planned decomposition) carries unquantified regression risk. Cannot validate that extracted services maintain behavioral parity with the monolith. |
| **Recommendation** | Before beginning decomposition, establish integration test coverage for critical workflows: product listing, basket CRUD operations, user creation/login. Use Spring Boot Test with Testcontainers (MySQL container) for integration tests. Add contract tests (Pact) for API consumers. |
| **Evidence** | `build.gradle` (`testImplementation('org.springframework.boot:spring-boot-starter-test')` declared but unused); absence of `src/test/` directory |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 3 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. No Systems Manager Automation documents, no Lambda-based remediation, no incident workflow definitions. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (database connection failure, disk full, memory exhaustion, deployment rollback). |
| **Recommendation** | Create runbooks for common incidents. After migration to EKS, implement self-healing via Kubernetes liveness/readiness probes (restart unhealthy pods automatically). Define SSM Automation documents for infrastructure-level remediation. |
| **Evidence** | Absence of runbook files, SSM Automation documents, or remediation scripts |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No observability ownership defined. No per-service dashboards, no named alarm owners, no CODEOWNERS for observability assets, no team attribution on monitoring resources. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No one is explicitly responsible for service health metrics. |
| **Recommendation** | Define service ownership in CODEOWNERS file. Create per-service CloudWatch dashboards with named owners after decomposition. Tag all monitoring resources with owning team. |
| **Evidence** | Absence of CODEOWNERS file, dashboard definitions, or team-attributed monitoring configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | No resource tagging. No IaC exists, therefore no tags are defined on AWS resources. No tagging standard, no cost allocation tags, no ownership tags. |
| **Gap** | Cannot track costs per workload, identify resource ownership, or enforce budget controls. No foundation for cloud financial management. |
| **Recommendation** | Define tagging standard in Terraform: `default_tags` in provider block with Environment, Service, Team, CostCenter. Enforce via AWS Config `required-tags` rule. Activate cost allocation tags in AWS Billing. |
| **Evidence** | Absence of any IaC with `tags` blocks or `default_tags` configuration |

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
| `build.gradle` | INF-Q1, APP-Q1, APP-Q2, SEC-Q3, SEC-Q7, OPS-Q1, OPS-Q5, OPS-Q6 | Primary dependency manifest — Java 8, Spring Boot 2.1.6, AWS SDK v1, MySQL connector |
| `src/main/resources/application.properties` | INF-Q2, INF-Q5, INF-Q6, SEC-Q5, APP-Q6 | Database connection string with hardcoded credentials, server port |
| `database/create_tables.sql` | INF-Q2, APP-Q2, DATA-Q1, DATA-Q4, SEC-Q2 | MySQL schema DDL — 3 tables, no stored procedures |
| `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | SEC-Q3, SEC-Q4 | OAuth2 resource server with all endpoints permitAll() |
| `src/main/java/com/monoToMicro/Application.java` | APP-Q2 | Single Spring Boot application entry point |
| `src/main/java/com/monoToMicro/core/events/` | INF-Q3, INF-Q4, APP-Q3 | 16 event classes — synchronous POJOs, not async messaging |
| `src/main/java/com/monoToMicro/rest/controller/` | APP-Q3, APP-Q4, APP-Q5, OPS-Q3 | 6 REST controllers with synchronous endpoints, no versioning |
| `src/main/java/com/monoToMicro/core/repository/` | DATA-Q2 | Repository pattern — 6 files with consistent data access |
| `src/main/resources/com/monoToMicro/core/repository/mappers/` | DATA-Q2, DATA-Q4 | MyBatis XML mappers — standard SQL, no proprietary constructs |
| `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | OPS-Q2 | Basic health check endpoint using EC2 metadata |
