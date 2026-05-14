# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | MonoToMicroLegacy |
| **Date** | 2025-07-17 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P0 |
| **Tags** | monolith, java, ec2, decomposition-target |
| **Context** | Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs. |
| **Overall Score** | 1.67 / 4.0 |

**Archetype Justification**: Application owns a MySQL database (`unishop` schema) with user, unicorn product, and shopping basket tables. It exposes CRUD REST endpoints (POST /user, POST /unicorns/basket, DELETE /unicorns/basket, GET /unicorns) and has no downstream service calls, no message queue consumers, and no event-driven patterns. Classified as `stateful-crud`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.45 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.67 / 4.0** | **🟠 Needs Work** |

**Scoring Notes:**
- INF: (1+2+2+1+2+1+1+1+1+3+1) / 11 = 1.45
- APP: (2+2+1+4+1+2) / 6 = 2.00
- DATA: (1+3+2+4) / 4 = 2.50
- SEC: (1+1+1+1+1+2+2) / 7 = 1.29
- OPS: (1+1+1+1+1+1+1+1+2) / 9 = 1.11
- Overall: (1.45+2.00+2.50+1.29+1.11) / 5 = 1.67

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | All compute runs on raw EC2 instances — no managed container orchestration or serverless | Triggers Move to Cloud Native and Move to Containers pathways; blocks elastic scaling and rapid deployment |
| 2 | SEC-Q5: Secrets Management | 1 | Database credentials hardcoded in `application.properties` and CloudFormation UserData scripts | Critical security vulnerability; credentials visible in source control and instance metadata |
| 3 | INF-Q11: CI/CD Automation | 1 | No build/test/deploy pipeline — only cfn-nag security scan exists; deployment is manual via cfn-init | Triggers Move to Modern DevOps pathway; blocks safe, repeatable deployments |
| 4 | APP-Q2: Monolith vs Microservices | 2 | Single deployable monolith with shared database schema — identifiable modules but tightly coupled through shared data | Triggers Move to Cloud Native pathway; blocks independent scaling and agent API access to order/return data |
| 5 | OPS-Q5: Deployment Strategy | 1 | Direct-to-production deployment via EC2 instance bootstrap — no blue/green, canary, or rolling updates | No safe rollback path; any deployment failure impacts all users immediately |

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2) — Unified data access layer exists via Repository pattern with MyBatis mapper layer. The `unishop` schema has 3 well-defined tables (`unicorns`, `unicorns_basket`, `unicorn_user`) with clear column semantics.
- **What it enables:** A natural language to SQL agent can query order/basket and product data directly, enabling the customer support agent described in the portfolio context to answer order inquiries ("What's in user X's basket?", "Show all available unicorn products").
- **Additional steps:** Generate an OpenAPI specification for the existing REST endpoints to provide the agent with tool definitions. Consider adding read-only database credentials scoped to SELECT-only access for agent queries. Migrate database to Aurora MySQL first (per Move to Managed Databases pathway) for connection pooling and IAM authentication support.
- **Effort:** Medium — Schema is clear and well-structured, but the agent needs a query interface (API or direct DB access with guardrails) and the database needs to be migrated to a managed service first for secure access.

### RAG-Based Knowledge Agent

- **Prerequisite:** README.md exists (detected during discovery) along with source code documentation (JavaDoc comments in all source files, SQL schema definitions in `create_tables.sql`).
- **What it enables:** A RAG-based knowledge agent can index the codebase documentation, SQL schema, and Java source files to answer developer questions about the Unicorn Shop architecture, data model, and business logic — accelerating onboarding and modernization planning.
- **Additional steps:** Documentation is minimal (README.md redirects to an external URL). Enrich the knowledge base with architecture decision records, API documentation, and operational runbooks as they are created during the modernization journey. Use Amazon Bedrock for embedding generation and knowledge base management.
- **Effort:** Medium — Source code and schema provide a foundation, but documentation needs enrichment for comprehensive agent knowledge.

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (monolith), INF-Q1=1 (all EC2), APP-Q3=1 (all sync) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (all EC2), no Dockerfile/container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); MySQL is already open source |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=2 (self-managed MySQL on EC2), DATA-Q3=2 (version EOL concerns) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; stateful-crud archetype with no streaming/ETL artifacts |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q11=1 (no CI/CD pipeline), OPS-Q5=1 (no deployment strategy), OPS-Q6=1 (no integration tests) |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks detected; portfolio context mentions "AI agent", "agent" — guard passed |

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a single-deployable Spring Boot 2.1 monolith (JAR) running on EC2 (`t3.small`). All business domains — product catalog (UnicornController), shopping basket (BasketController), user management (UserController), and health monitoring (HealthController) — are packaged into one artifact sharing a single MySQL database (`unishop` schema with 3 tables). Module boundaries are identifiable through the controller→service→repository pattern, but tightly coupled through the shared database schema (e.g., `getUnicornBasket` JOINs `unicorns` and `unicorns_basket` tables). APP-Q2 score: 2.

**Compute Model Gaps:** All compute is raw EC2 (INF-Q1 score: 1). No managed container orchestration (ECS/EKS) or serverless. The application runs as a systemd service on the EC2 instance, started by a bash script.

**Communication Pattern Gaps:** All communication is synchronous HTTP (APP-Q3 score: 1). No async messaging — basket state changes are local database operations with no event propagation. When services are extracted, state changes need to emit events for cross-service consistency.

**Recommended Decomposition Approach:** Strangler Fig with containerize-first strategy. See [Decomposition Strategy](#decomposition-strategy) section below. Containerize the monolith on EKS first (aligns with preferences), then incrementally extract services starting with the Basket/Order service to enable agent API access to order and return data.

**Representative AWS Services:** EKS (preferred), API Gateway, EventBridge (preferred for event propagation), Aurora MySQL (preferred for database per service).

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Saga Pattern.

**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Two EC2 instances (`t3.small`, Amazon Linux 2 AMI) — one for the application (MonoToMicroEC2) and one for the database (MonoToMicroDB). The application is deployed as a Spring Boot JAR via cfn-init on instance bootstrap. Nginx serves as a reverse proxy on the same EC2 instance. No Dockerfile, docker-compose.yml, or Kubernetes manifests exist anywhere in the repository.

**Container Readiness Indicators:**
- Application is a self-contained Spring Boot JAR (`bootJar` with `launchScript()` in `build.gradle`) — straightforward to containerize
- Port binding is explicit (`server.port=8080` in `application.properties`)
- Database endpoint is externalized via environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) — container-friendly
- Gradle build is already automated (`./gradlew clean build`)
- Java 11 is installed on EC2 (java-11-amazon-corretto-headless) — align container base image to Corretto 11+

**Recommended Container Orchestration:** Amazon EKS (per preferences — `prefer: ["eks"]`). Deploy on EKS with Fargate profile for compute to avoid self-managed Kubernetes node groups (per `avoid: ["self-managed-kubernetes"]`).

**Representative AWS Services:** EKS, ECR (for container image registry), EKS with Fargate (managed compute), AWS App Mesh or Istio (service mesh for future microservices).

**Migration Approach:** Lift-and-containerize first — create a Dockerfile for the monolith, push to ECR, deploy on EKS. This provides immediate benefits (reproducible deployments, scaling via Kubernetes) without requiring architectural changes. Refactoring into microservices follows as a separate initiative (see Move to Cloud Native pathway).

**AWS Container Migration Guidance:** [Containerize and migrate applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/containers-provision-environment/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** The primary database is self-managed MySQL 8.0 running on an EC2 instance (`t3.small`, MonoToMicroDB). MySQL is installed via `yum` from `mysql80-community-release-el7-1.noarch.rpm` during cfn-init. An Aurora MySQL cluster (`RDSCluster`) exists in the CloudFormation template, but it is configured as a DMS migration target — not the primary production database. The primary database has no automated backups, no Multi-AZ, and credentials hardcoded in CloudFormation UserData. INF-Q2 score: 2.

**Engine Versions and EOL Status:** Self-managed MySQL 8.0 (no explicit minor version pin). Aurora MySQL cluster specifies `EngineVersion: 5.7.mysql_aurora.2.11.2` — this is Aurora MySQL 2.x based on MySQL 5.7, which reached EOL in October 2024. DATA-Q3 score: 2.

**Data Access Patterns:** Centralized repository pattern via MyBatis mappers (DATA-Q2 score: 3). All SQL is standard MySQL (SELECT, INSERT IGNORE INTO, DELETE, JOIN) with no stored procedures or proprietary SQL (DATA-Q4 score: 4). This makes migration straightforward — no schema conversion or logic extraction needed.

**Recommended Managed Database Target:** Amazon Aurora MySQL (per preferences — `prefer: ["aurora", "aurora-mysql"]`). Aurora MySQL provides MySQL compatibility, automated backups, Multi-AZ by default, read replicas, and IAM authentication. The existing Aurora cluster in CloudFormation can be upgraded to Aurora MySQL 3.x (MySQL 8.0 compatible) and promoted to primary.

**Representative AWS Services:** Aurora MySQL (primary recommendation), DynamoDB (for basket data if decomposed — per preferences), Secrets Manager (for credential rotation).

**Migration Tools:** AWS DMS is already partially configured in the CloudFormation template (`MySQLSourceEndpoint`, `MySQLTargetEndpoint`, `MonoToMicroReplicationInstance`). Leverage this existing DMS infrastructure to migrate from self-managed MySQL to Aurora MySQL with minimal downtime.

**AWS Database Migration Guidance:** [Migrate to Aurora MySQL](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-aurora-mysql/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** CloudFormation template (`MonoToMicroCF.yaml`) covers VPC, subnets, route tables, NAT gateways, security groups, EC2 instances, RDS, DMS, S3, and IAM — approximately 70-90% of the infrastructure is defined in IaC. INF-Q10 score: 3. However, the preference is to migrate to Terraform (per `prefer: ["terraform"]`).

**Current CI/CD State:** Only one GitHub Actions workflow exists (`.github/workflows/cfn-security.yml`) running cfn-nag security scan on push. There is no build pipeline, no test pipeline, and no deployment pipeline. The application is deployed by creating/updating the CloudFormation stack, which bootstraps a new EC2 instance via cfn-init. INF-Q11 score: 1.

**Deployment Strategy Gaps:** Direct-to-production deployment via EC2 instance creation. No blue/green, canary, or rolling updates. Re-deployment requires destroying and recreating the EC2 instance. OPS-Q5 score: 1.

**Testing Gaps:** No test files exist despite `spring-boot-starter-test` being in dependencies. No integration tests, no API tests, no contract tests. OPS-Q6 score: 1.

**Recommended DevOps Toolchain:**
- **IaC:** Migrate from CloudFormation to Terraform (per preferences). Use Terraform modules for reusable infrastructure components.
- **CI/CD:** GitHub Actions (already in use for cfn-nag) extended with build, test, and deploy stages. Or AWS CodePipeline + CodeBuild if AWS-native preferred.
- **Deployment:** GitOps with ArgoCD on EKS (per `prefer: ["gitops"]`). Container image builds trigger ArgoCD sync for automated, declarative deployments.
- **Testing:** Add JUnit integration tests, API contract tests (Pact), and integration test suites in the pipeline.

**Representative AWS Services:** CodeBuild, CodePipeline, ECR, CloudFormation/CDK or Terraform, X-Ray, CloudWatch.

**AWS DevOps Prescriptive Guidance:** [DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-modernizing-applications/devops.html)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:** No AI or agent frameworks detected in the repository. No Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK imports found in source code or `build.gradle` dependencies. No vector database infrastructure, no RAG implementation patterns, no agent evaluation frameworks.

**Contextual Guard Evaluation:** Portfolio context contains AI-related signal terms: "AI agent" (matches "AI" and "agent"), "autonomous" (matches "autonomous"). The service-level context mentions "agent needs access to order and return data." Guard passed — AI intent is explicit in the portfolio.

**Application Domain and AI Use Cases:**
1. **Customer Support Agent** (from portfolio context): An agent that handles order inquiries, processes returns, and manages inventory restocking. Requires API access to basket/order data and user data — currently locked in the monolith.
2. **Product Recommendation Agent**: Leverage unicorn product catalog data to suggest items based on browsing/basket history.
3. **Inventory Management Agent**: Monitor stock levels and trigger restocking workflows when thresholds are met.

**Quick Wins:** See [Quick Agent Wins](#quick-agent-wins) section — Data Query Agent is immediately viable given the clear schema and repository pattern.

**Recommended AI Services:** Amazon Bedrock (per `prefer: ["bedrock"]`) for foundation model access, Amazon Bedrock Knowledge Bases for RAG, Amazon Bedrock AgentCore for agent runtime.

**Foundation Requirements Before AI Integration:**
1. **API Surface**: Generate OpenAPI specs for existing REST endpoints (currently undocumented). Decompose monolith to expose discrete order/basket/user APIs (per Move to Cloud Native pathway).
2. **Data Access**: Migrate to Aurora MySQL (per Move to Managed Databases pathway) for IAM authentication and secure agent database access.
3. **Secrets Management**: Move credentials to Secrets Manager before agent integration (agents need secure credential retrieval).
4. **Observability**: Add tracing (X-Ray/OpenTelemetry) for agent action visibility.

**AWS AI/ML Prescriptive Guidance:** [Generative AI on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/generative-ai-building/welcome.html)

## Decomposition Strategy

> This section is included because APP-Q2 scored 2 (< 3) — the application is a tightly-coupled monolith.

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping it running. New features built as services; existing features migrated over time. | The monolith has identifiable modules (Unicorn, Basket, User) that map to service boundaries. Team can sustain parallel development. | **Medium to High** — 6-12 months. Each extraction is bounded. | ✅ **Recommended.** Lowest risk, incremental value delivery. Start with Basket service extraction to enable agent API access to order data. |
| **Conditional / Adaptive** | Containerize the monolith as-is on EKS, then selectively extract high-value services based on business priority. | Team has limited capacity. Business pressure requires quick wins (containerization) before full decomposition. | **Low to Medium** — 2-4 weeks for containerization, 3-6 months per service extraction. | ✅ **Recommended as Phase 1.** Containerize first on EKS (aligns with preferences), then extract Basket service as first microservice. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch. | Almost never. Only when the monolith is truly unmaintainable. | **Very High** — 12-24+ months. High risk. | ⚠️ **Recommended against.** This monolith has clear module boundaries and is functional. Strangler Fig or Conditional approaches are significantly safer. |

### Recommended Phased Approach

**Phase 1 (Weeks 1-4): Containerize-First**
1. Create Dockerfile for the monolith using `amazoncorretto:11` base image
2. Push to ECR, deploy on EKS with Fargate profile
3. Set up GitOps with ArgoCD for automated deployments
4. Migrate database to Aurora MySQL (leverage existing DMS configuration)

**Phase 2 (Months 2-4): Extract Basket/Order Service**
1. Extract `BasketController` + `UnicornService.getUnicornBasket/addUnicornToBasket/removeUnicornFromBasket` into a standalone service
2. Create dedicated API (versioned) for basket operations — enables the customer support agent to access order data via discrete API
3. Add Anti-corruption Layer between new Basket service and monolith
4. Emit basket state change events to EventBridge (per preferences) for cross-service consistency

**Phase 3 (Months 4-8): Extract Product Catalog and User Service**
1. Extract `UnicornController` + `UnicornService.getUnicorns` into Product Catalog service
2. Extract `UserController` + `UserService` into User Management service
3. Each service gets its own database (schema-per-service on Aurora MySQL, or DynamoDB for basket per preferences)

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's data model. Prevents monolith design leaking into new services. | Every extraction — ACL between new service and monolith. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions across services for basket checkout flow. | When basket and product services are separated — checkout spans multiple services. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture basket state changes as events. Enables audit trails and EventBridge integration. | Basket service extraction — emit events on add/remove to basket for cross-service consistency. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters for testability and portability. | Every new service — ensures decoupling from infrastructure. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal | Analysis | Effort Impact |
|--------|--------|------------|---------------|
| Module boundaries | Controller→Service→Repository pattern with clear separation | APP-Q2 = 2 — boundaries exist but shared schema | **Low** — modules are identifiable |
| Data coupling | Single `unishop` schema; `getUnicornBasket` JOINs `unicorns` and `unicorns_basket` | DATA-Q2 = 3 — centralized access, but cross-table JOINs create extraction friction | **Medium** — need to resolve JOIN dependencies during extraction |
| Stored procedures | None — all logic in Java application layer | DATA-Q4 = 4 | **Low** — no database-locked logic to extract |
| Communication patterns | All synchronous HTTP, no async | APP-Q3 = 1 | **Medium-High** — need to add EventBridge for cross-service events |
| CI/CD maturity | No deployment pipeline | INF-Q11 = 1 | **High** — must build pipeline before decomposition |
| Test coverage | No tests exist | OPS-Q6 = 1 | **High** — regression risk during extraction; need test harness first |

**Calibrated Estimate:**
- **Containerize-first (Phase 1):** 2-4 weeks
- **First service extraction (Phase 2):** 3-4 months (includes building CI/CD pipeline and basic test suite)
- **Full decomposition (Phase 3):** 4-8 months additional
- **Total end-to-end:** 9-15 months

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs on raw EC2 instances. `MonoToMicroCF.yaml` defines two `AWS::EC2::Instance` resources: `EC2Instance` (application server, `t3.small`) and `DBInstance` (database server, `t3.small`). No `AWS::ECS::*`, `AWS::EKS::*`, `AWS::Lambda::*`, or Fargate resources exist. The application runs as a systemd service (`mono2micro.service`) executing a Spring Boot JAR directly on EC2. Nginx is installed on the same EC2 instance as a reverse proxy. |
| **Gap** | No managed compute — all workloads run on self-managed EC2 instances requiring manual patching, capacity planning, and scaling. |
| **Recommendation** | Containerize the monolith and deploy on Amazon EKS with Fargate profile. Create a Dockerfile using `amazoncorretto:11` base image, push to ECR, and deploy via EKS. This eliminates EC2 instance management while aligning with preferences for EKS and containers. Avoid self-managed Kubernetes node groups (per preferences). |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — `EC2Instance` (line ~280), `DBInstance` (line ~200) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The primary production database is self-managed MySQL 8.0 on EC2 (`DBInstance`). MySQL is installed via `yum` from `mysql80-community-release-el7-1.noarch.rpm` during cfn-init. An Aurora MySQL cluster (`RDSCluster`, engine `aurora-mysql`, version `5.7.mysql_aurora.2.11.2`) exists but is configured as a DMS migration target, not the active primary database. DMS endpoints (`MySQLSourceEndpoint`, `MySQLTargetEndpoint`) and a replication instance are configured for migration. The RDS instance has `MultiAZ: false`. |
| **Gap** | Primary production database is self-managed on EC2 with manual patching, no automated backups, and no failover. Aurora cluster exists but is a migration target, not yet promoted to primary. |
| **Recommendation** | Execute the DMS migration from self-managed MySQL to Aurora MySQL (infrastructure is already partially configured). Upgrade Aurora cluster to Aurora MySQL 3.x (MySQL 8.0 compatible) with Multi-AZ enabled. Configure automated backups and PITR. Use Secrets Manager for credential rotation. |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — `DBInstance` (EC2 with MySQL install), `RDSCluster` (Aurora), `MySQLSourceEndpoint`, `MySQLTargetEndpoint`, `MonoToMicroReplicationInstance` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated workflow orchestration service (Step Functions, Temporal, MWAA) is used. The application is a stateful-crud service with simple CRUD operations: add/remove items from basket, create/login user, list products. These are single-step database operations. However, the `DataReplicationController` (`/data` endpoint) orchestrates a data replication workflow (getAllBaskets) that could benefit from managed orchestration as the system grows. For the stateful-crud archetype, simple state machines in code with some structure but no dedicated service. |
| **Gap** | No workflow orchestration for the data replication flow or potential future multi-step operations (e.g., order processing when checkout is added). |
| **Recommendation** | As services are decomposed, adopt AWS Step Functions for multi-step workflows (e.g., order checkout: validate basket → process payment → update inventory → confirm order). Step Functions provide built-in retry logic, error handling, and visual workflow monitoring. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` — data replication as inline code; no `aws_sfn_*` or Temporal in `MonoToMicroCF.yaml` or `build.gradle` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure exists. No SQS, SNS, EventBridge, Kinesis, MSK, or Amazon MQ resources in CloudFormation. No messaging SDK imports in `build.gradle`. All operations are synchronous HTTP — basket state changes (add/remove unicorn) are local database writes with no event propagation. For the stateful-crud archetype, basket state changes crossing service boundaries should emit events, but currently there are no cross-service boundaries (monolith). |
| **Gap** | No messaging infrastructure for cross-service state propagation. When services are decomposed, basket state changes will need to propagate to other services (e.g., inventory, analytics, customer support agent). Without async messaging, decomposition creates tight synchronous coupling between services. |
| **Recommendation** | Adopt Amazon EventBridge (per preferences) for event-driven communication between decomposed services. Emit events on basket state changes (item added, item removed) and user events (user created, user logged in). EventBridge provides managed event routing with filtering, transformation, and dead-letter queues. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — no messaging resources; `build.gradle` — no SQS/SNS/EventBridge SDK; all controllers use synchronous request/response |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | VPC (`MonoToMicroVPC`, `10.0.0.0/16`) with 4 subnets: 2 public (`MonoToMicroSubnet1/2`, `MapPublicIpOnLaunch: true`) and 2 private (`MonoToMicroSubnet3/4`, `MapPublicIpOnLaunch: false`). NAT gateways in each public subnet enable private subnet outbound access. `EC2SecurityGroup` has overly permissive ingress: `0.0.0.0/0` on ports 80 and 443. `DBSecurityGroup` is properly scoped — only allows port 3306 from `EC2SecurityGroup`. However, both EC2 instances (app and DB) are deployed in `MonoToMicroSubnet1` (public subnet). The DB instance should be in a private subnet. |
| **Gap** | EC2 security group allows `0.0.0.0/0` ingress on ports 80/443. Database EC2 instance is in a public subnet (Subnet1) despite having a dedicated private subnet available (Subnet3/4). No VPC endpoints, PrivateLink, or zero-trust networking. |
| **Recommendation** | Move the database instance to a private subnet (Subnet3 or Subnet4). Restrict EC2 security group ingress to specific CIDR ranges or place behind an API Gateway (per preferences). Add VPC endpoints for S3 and other AWS services to keep traffic private. When migrated to EKS, implement network policies for pod-level segmentation. |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — `EC2SecurityGroup` (0.0.0.0/0 ingress), `DBSecurityGroup` (scoped), `MonoToMicroSubnet1` (public, used by both EC2 instances), `MonoToMicroSubnet3/4` (private, unused by EC2) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront configured. Nginx is installed directly on the EC2 instance as a reverse proxy (`sed` command replaces nginx root, `proxy_pass http://127.0.0.1:8080/` for `/api/` path). The application is accessed via the EC2 instance's public DNS name (stored in SSM parameter `UniShopPublicDnsName`). A `RefactorSpaces` environment and application are pre-created in CloudFormation with `ProxyType: API_GATEWAY`, but this is for future use — not currently routing traffic. |
| **Gap** | Direct EC2 exposure with no managed API entry point. No throttling, no request validation, no centralized authentication at the gateway level. Nginx on EC2 provides only basic reverse proxy functionality. |
| **Recommendation** | Deploy Amazon API Gateway (per preferences) as the entry point for all API traffic. Configure throttling, request validation, and API key management. When services are decomposed, API Gateway provides per-service routing, versioning support, and usage plans. The existing RefactorSpaces configuration can be leveraged during the migration to route traffic progressively from monolith to microservices. |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — nginx install in `EC2Instance` cfn-init, `PublicDnsNameSSMParam`, `UniShopRefactorSpacesApplication` (pre-created, not active) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configured anywhere. Both EC2 instances are single, standalone instances with no Auto Scaling Group. No `AWS::AutoScaling::*` or `AWS::ApplicationAutoScaling::*` resources in CloudFormation. The Aurora MySQL cluster has no auto-scaling configuration. All capacity is statically provisioned at `t3.small`. |
| **Gap** | All resources are statically sized. No ability to respond to traffic spikes or scale down during low demand. Single EC2 instance is a capacity ceiling and single point of failure. |
| **Recommendation** | When containerized on EKS, configure Horizontal Pod Autoscaler (HPA) for the application workloads and Cluster Autoscaler or Karpenter for node capacity. For Aurora MySQL, enable Aurora Auto Scaling for read replicas. |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — no auto-scaling resources; `EC2Instance` and `DBInstance` are standalone instances |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. The primary database (self-managed MySQL on EC2) has no automated backup — no EBS snapshots, no mysqldump cron, no `AWS::Backup::*` resources. The Aurora MySQL cluster does not specify `BackupRetentionPeriod` (defaults to 1 day for Aurora). No PITR configuration. No `S3 versioning` on data buckets. `RDSInstance` has `DeletionPolicy: Delete` — the RDS instance is deleted on stack deletion with no snapshot. |
| **Gap** | No automated backups for the primary self-managed MySQL database. Aurora cluster uses default retention. No tested restore procedures. No cross-region backup replication. `DeletionPolicy: Delete` on RDS risks data loss on stack operations. |
| **Recommendation** | Migrate to Aurora MySQL (per Move to Managed Databases pathway) which provides automated backups by default. Set `BackupRetentionPeriod` to 7+ days, enable PITR, and configure cross-region backup replication for disaster recovery. Change `DeletionPolicy` to `Snapshot` on Aurora resources. Add `AWS::Backup::BackupPlan` for centralized backup management. |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — no `AWS::Backup::*`, `RDSInstance` `DeletionPolicy: Delete`, no `BackupRetentionPeriod` on `RDSCluster` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Both EC2 instances are deployed in a single subnet (`MonoToMicroSubnet1`, AZ index 0). `RDSInstance` has `MultiAZ: false`. No load balancer to distribute traffic. No failover configuration. A single AZ failure takes down the entire application and database. The VPC has subnets in two AZs (`!Select ['0']` and `!Select ['1']`), but the compute resources only use AZ 0. |
| **Gap** | All resources in a single AZ. No Multi-AZ for database. No cross-AZ compute distribution. Single point of failure for the entire application stack. |
| **Recommendation** | When migrating to Aurora MySQL, enable Multi-AZ (`MultiAZ: true` on the DB instance, or add Aurora replicas in the second AZ). When containerized on EKS, deploy pods across both AZs with topology spread constraints. Place an Application Load Balancer in front of the EKS service for cross-AZ traffic distribution. |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — `EC2Instance` SubnetId: `MonoToMicroSubnet1` (AZ 0 only), `DBInstance` SubnetId: `MonoToMicroSubnet1`, `RDSInstance` `MultiAZ: false` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CloudFormation template (`MonoToMicroCF.yaml`, ~400 lines) defines the complete infrastructure: VPC with 4 subnets, route tables, NAT gateways, internet gateway, security groups, 2 EC2 instances with cfn-init configuration, Aurora MySQL cluster and instance, DMS replication infrastructure (endpoints, replication instance, subnet group), S3 buckets (UI and assets), IAM roles and policies, SSM parameters, CloudWatch log group, and RefactorSpaces environment. The application build and deployment are automated via cfn-init. However, operational/DR resources are limited — only a basic CloudWatch log group with 7-day retention. No CloudWatch alarms, no Route 53 health checks, no backup plans defined in IaC. |
| **Gap** | IaC covers compute, networking, databases, and storage (70-90% coverage) but missing operational resources: no CloudWatch alarms, no health checks, no backup plans, no dashboard definitions in IaC. Preference is to migrate to Terraform. |
| **Recommendation** | Migrate infrastructure to Terraform (per preferences) using modules for reusable components. Add Terraform resources for CloudWatch alarms, Route 53 health checks, AWS Backup plans, and dashboard definitions. When moving to EKS, define Kubernetes manifests and Helm charts as IaC alongside the Terraform infrastructure. Use GitOps (ArgoCD per preferences) for Kubernetes resource management. |
| **Evidence** | `MonoToMicroAssets/MonoToMicroCF.yaml` — comprehensive VPC, compute, database, DMS, S3, IAM, and RefactorSpaces resources; missing: alarms, health checks, backup plans |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Only one GitHub Actions workflow exists: `.github/workflows/cfn-security.yml` runs `cfn_nag` security scan on the `MonoToMicroAssets` directory on every push. There is no build pipeline (`./gradlew build` is only executed during EC2 cfn-init bootstrap, not in CI). No test pipeline. No deployment pipeline. Application deployment requires creating or updating the CloudFormation stack, which provisions a new EC2 instance and runs cfn-init to clone the repo, build the JAR, and start the service. Re-deployment requires stack update or instance replacement. |
| **Gap** | No CI/CD automation for build, test, or deploy. Deployment is manual (CloudFormation stack operations) and tightly coupled to EC2 instance lifecycle. The cfn-nag scan is security-only and does not constitute a deployment pipeline. |
| **Recommendation** | Extend GitHub Actions with a full CI/CD pipeline: (1) Build stage — `./gradlew clean build` and run unit tests, (2) Docker build — create container image and push to ECR, (3) Security scan — SAST + dependency scanning + container image scanning, (4) Deploy — trigger ArgoCD sync for GitOps deployment to EKS. Avoid manual deployments (per preferences). |
| **Evidence** | `.github/workflows/cfn-security.yml` — cfn-nag only; `MonoToMicroAssets/MonoToMicroCF.yaml` — deployment via cfn-init in EC2 UserData |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Java 8 (`sourceCompatibility = 1.8` in `build.gradle`) with Spring Boot 2.1.0/2.1.6. AWS SDK v1 (`com.amazonaws:aws-java-sdk:1.11.567`). Java is a first-class AWS SDK language with broad cloud-native tooling, but Java 8 is an older version (released 2014, long-term support ending). Spring Boot 2.1.x is also outdated (current LTS is Spring Boot 3.x). The EC2 instance installs Java 11 Corretto (`java-11-amazon-corretto-headless`), but the build targets Java 8 compatibility. AWS SDK v1 is in maintenance mode — v2 is recommended. |
| **Gap** | Java 8 source compatibility limits access to modern language features (records, sealed classes, pattern matching), modern Spring Boot 3.x features (Jakarta EE, native compilation, virtual threads), and AWS SDK v2 (requires Java 8+ but optimized for 11+). Spring Boot 2.1.x lacks security patches and modern integrations. |
| **Recommendation** | Upgrade source compatibility to Java 17+ (LTS), migrate to Spring Boot 3.x, and upgrade from AWS SDK v1 to v2. Use Amazon Corretto 17 or 21 as the base image when containerizing. This enables modern language features, better container performance, and access to the latest AWS SDK features. |
| **Evidence** | `build.gradle` — `sourceCompatibility = 1.8`, `springBootVersion = '2.1.0.RELEASE'`, `aws-java-sdk:1.11.567`; `MonoToMicroCF.yaml` — `java-11-amazon-corretto-headless` installed |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable Spring Boot JAR (`bootJar` with `launchScript()` in `build.gradle`). All business domains in one package: `UnicornController/Service/Repository` (product catalog), `BasketController` + `UnicornService` (shopping basket), `UserController/Service/Repository` (user management), `HealthController` (health checks), `DataReplicationController` (data sync). Single shared `unishop` MySQL schema with 3 tables (`unicorns`, `unicorns_basket`, `unicorn_user`) accessed by all domains. Module boundaries exist through the controller→service→repository pattern, but tightly coupled through: (1) shared database schema, (2) cross-table JOINs (`getUnicornBasket` joins `unicorns` and `unicorns_basket`), (3) shared `CoreModel` base class. |
| **Gap** | Monolith with identifiable modules but shared database schemas and cross-module data access. The `UnicornService` handles both product catalog AND basket operations, indicating insufficient domain separation. The shared `unishop` schema makes independent deployment impossible — all domains must be deployed together. |
| **Recommendation** | Decompose using the Strangler Fig approach with containerize-first strategy (see Decomposition Strategy section). Priority extraction order: (1) Basket/Order service — enables agent API access to order data per portfolio requirements, (2) Product Catalog service, (3) User Management service. Each extracted service should own its database schema. Use API Gateway for routing and EventBridge for cross-service events. |
| **Evidence** | `build.gradle` — `bootJar`, single artifact; `database/create_tables.sql` — single `unishop` schema; `UnicornMapper.xml` — `getUnicornBasket` JOIN across tables; all controllers in `com.monoToMicro.rest.controller` package |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All communication is synchronous HTTP. Controllers receive HTTP requests and respond synchronously after database operations. No async patterns — no message publishing, no event emission, no queue consumers. For the stateful-crud archetype, managed messaging (SQS, SNS, EventBridge) should be used for cross-service state changes. Currently there are no cross-service flows (monolith), but basket state changes (add/remove item) do not emit any events that downstream services could consume. No HTTP clients to external services found — all operations are internal to the monolith. |
| **Gap** | All communication synchronous with no async patterns. When decomposed, basket state changes will need to propagate asynchronously to other services (inventory, analytics, customer support agent). The absence of any event infrastructure means async patterns must be introduced from scratch during decomposition. |
| **Recommendation** | During decomposition, adopt EventBridge (per preferences) for event-driven state propagation. Emit `BasketItemAdded`, `BasketItemRemoved`, `UserCreated` events that downstream services and the customer support agent can consume. Avoid self-managed Kafka (per preferences). Implement async patterns incrementally alongside service extraction. |
| **Evidence** | All controllers (`BasketController.java`, `UnicornController.java`, `UserController.java`) — synchronous `ResponseEntity<>` returns; `build.gradle` — no messaging SDK dependencies; no `@Async`, `@EventListener`, or queue consumer annotations |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All operations are simple CRUD database queries completing in milliseconds — no operations approach 30 seconds. Product listing (`getUnicorns`): single SELECT on `unicorns` table (10 rows). Basket operations (`addUnicornToBasket`, `removeUnicornFromBasket`): single INSERT/DELETE on `unicorns_basket`. User operations (`create`, `getByEmail`): single INSERT/SELECT on `unicorn_user`. Health checks: SELECT COUNT(*). The `getAllBaskets` data replication query is a JOIN but on a small dataset. For the stateful-crud archetype, all operations are quick DB operations — async job infrastructure is not needed for the current surface. |
| **Gap** | N/A — No long-running operations exist in the current application surface. |
| **Recommendation** | No action needed for current operations. When decomposition introduces new capabilities (bulk exports, order processing, payment integration), evaluate whether new operations exceed 30 seconds and implement async patterns with status polling if needed. |
| **Evidence** | `UnicornMapper.xml` — all SQL operations are simple single-table or two-table JOINs; `BasketController.java`, `UserController.java` — synchronous CRUD; `database/create_tables.sql` — 10 seed rows in unicorns table |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. Endpoints use unversioned paths: `/unicorns` (GET), `/unicorns/basket` (POST, DELETE, GET `/{userUuid}`), `/user` (POST, POST `/login`), `/health/ping`, `/health/ishealthy`, `/health/dbping`, `/data` (GET). No `/v1/`, `/v2/` URL patterns, no `Accept-Version` headers, no versioning annotations. Breaking changes would affect all consumers simultaneously. |
| **Gap** | No API versioning — breaking changes deployed directly to all consumers. This is particularly critical given the decomposition plan, as extracted services need versioned APIs for backward compatibility with both the monolith (during transition) and the customer support agent (which needs stable API contracts). |
| **Recommendation** | Implement URL path versioning (`/v1/unicorns`, `/v1/user`, `/v1/basket`) when extracting services. Define versioned APIs in OpenAPI specifications. API Gateway (per preferences) provides native versioning support via stages. Establish a versioning policy: new versions for breaking changes, deprecation notices, minimum 6-month support for old versions. |
| **Evidence** | `BasketController.java` — `@RequestMapping("/unicorns/basket")`, `UnicornController.java` — `@RequestMapping("/unicorns")`, `UserController.java` — `@RequestMapping("/user")` — no version prefix in any mapping |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single monolith — no inter-service communication exists, so service discovery is not actively needed. The database endpoint is externalized via environment variable (`MONO_TO_MICRO_DB_ENDPOINT` in `application.properties` and `m2mcfg.sh`). AWS region and S3 bucket names are also externalized as environment variables. No hard-coded service endpoints in application code. However, there is no dynamic service discovery mechanism (no AWS Cloud Map, no Consul, no Istio service mesh). |
| **Gap** | Environment variables for endpoints but no dynamic discovery. When decomposed into microservices on EKS, services need a dynamic discovery mechanism to avoid hard-coded endpoints between services. |
| **Recommendation** | When deploying on EKS, leverage Kubernetes native service discovery (ClusterIP services, CoreDNS). For cross-cluster or cross-account service discovery, use AWS Cloud Map. API Gateway (per preferences) serves as an API catalog for external consumers (including the customer support agent). |
| **Evidence** | `application.properties` — `${MONO_TO_MICRO_DB_ENDPOINT}` env var; `MonoToMicroCF.yaml` — `m2mcfg.sh` exports `MONO_TO_MICRO_DB_ENDPOINT`, `AWS_DEFAULT_REGION`, `UI_RANDOM_NAME`, `ASSETS_RANDOM_NAME` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No evidence of unstructured data handling in the application. S3 buckets exist in CloudFormation (`UIBucket` for static website hosting, `AssetBucket` for build artifacts), but these are infrastructure assets — not application-level document or unstructured data storage. The application deals only with structured relational data (products, baskets, users). No Textract calls, no PDF/image processing, no document parsing libraries in `build.gradle`. Product images are referenced by name string only (`image` column in `unicorns` table) — actual image files are served from the UI bucket, not managed by the application. |
| **Gap** | Data on local file systems or inaccessible storage. Product images are served statically with no parsing or processing capability. No S3 integration for application-level document management. |
| **Recommendation** | If the e-commerce platform needs document handling (invoices, return receipts, product manuals), store documents in S3 with metadata tagging. Use Amazon Textract for document parsing if OCR is needed. For the customer support agent, S3-stored documents can be indexed by Amazon Bedrock Knowledge Bases for RAG-based retrieval. |
| **Evidence** | `MonoToMicroCF.yaml` — `UIBucket` (website), `AssetBucket` (artifacts); `database/create_tables.sql` — `image varchar(256)` stores image name only; `build.gradle` — no S3 data processing libraries |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Consistent repository pattern is used throughout. All database access flows through a structured chain: Controller → Service → Repository → MyBatis Mapper → SQL. `UnicornRepository/Impl` handles product and basket data access via `UnicornMapper`. `UserRepository/Impl` handles user data access via `UserMapper`. `HealthRepository/Impl` handles health checks via `HealthMapper`. MyBatis configuration is centralized in `MyBatisConfig.java`. No direct database access outside the repository layer. However, `UnicornService` handles both product catalog operations (`getUnicorns`) and basket operations (`addUnicornToBasket`, `getUnicornBasket`, `getAllBaskets`), blurring domain boundaries within the data access layer. |
| **Gap** | Mostly centralized with clear pattern, but `UnicornService/Repository` mixes product catalog and basket data access concerns. When decomposed, basket data access needs its own repository separate from product catalog. |
| **Recommendation** | During decomposition, split `UnicornRepository` into `ProductCatalogRepository` (product queries) and `BasketRepository` (basket CRUD). Each decomposed service should own its repository and mapper layer. Maintain the Repository pattern in all extracted services for consistency. |
| **Evidence** | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`; `src/main/java/com/monoToMicro/config/MyBatisConfig.java` — centralized mapper configuration |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Two database instances: (1) Self-managed MySQL on EC2 — installed from `mysql80-community-release-el7-1.noarch.rpm` (MySQL 8.0), but no explicit minor version pin. The `yum install` will pull whatever 8.0.x version is current, creating version drift between deployments. (2) Aurora MySQL cluster — `EngineVersion: 5.7.mysql_aurora.2.11.2` (Aurora MySQL 2.x based on MySQL 5.7). Aurora MySQL 2.x / MySQL 5.7 reached end of standard support in October 2024. While Amazon provides extended support, this incurs additional cost and the engine lacks MySQL 8.0 features. |
| **Gap** | Self-managed MySQL has no explicit version pin (version drift risk). Aurora MySQL engine is past EOL (MySQL 5.7 based). No documented version-update procedure. |
| **Recommendation** | When migrating to Aurora MySQL as primary (per Move to Managed Databases pathway), use Aurora MySQL 3.x (MySQL 8.0 compatible). Pin the `EngineVersion` explicitly (e.g., `8.0.mysql_aurora.3.07.1`). Establish a quarterly engine version review process. Document downtime windows, rollback procedures, and risk acknowledgment for version upgrades. |
| **Evidence** | `MonoToMicroCF.yaml` — `RDSCluster` `EngineVersion: 5.7.mysql_aurora.2.11.2`; `DBInstance` cfn-init — `mysql80-community-release-el7-1.noarch.rpm` (no minor version pin) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, functions, or proprietary SQL constructs found anywhere in the codebase. All SQL is standard MySQL via MyBatis mapper XMLs: `SELECT *`, `INSERT IGNORE INTO`, `DELETE FROM`, `SELECT ... JOIN ... WHERE`. All business logic resides in the Java application layer (Service implementations). The `create_tables.sql` file contains only DDL (CREATE SCHEMA, CREATE TABLE) and DML (INSERT seed data) — no procedural SQL. This is ideal for database migration — no logic extraction or schema refactoring needed. |
| **Gap** | N/A — No stored procedures or proprietary SQL. All business logic is in the application layer. |
| **Recommendation** | Maintain this pattern during decomposition. Keep all business logic in the application layer (Java services). Use standard SQL in MyBatis/JPA mappers. This ensures database portability — services can be backed by Aurora MySQL, DynamoDB (per preferences), or other data stores without stored procedure migration. |
| **Evidence** | `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` — standard SELECT/INSERT/DELETE/JOIN; `UserMapper.xml` — standard INSERT/SELECT; `HealthMapper.xml` — `SELECT COUNT(*)`; `database/create_tables.sql` — DDL and seed data only |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail resource in CloudFormation. No audit logging configured. CloudWatch agent is installed on the EC2 instance for application log collection (`app.log` → `InstanceLogGroup` with 7-day retention), but this is application logging — not an audit trail. No `AWS::CloudTrail::Trail` resource. No log file validation or immutable storage. Application uses `System.out.println` and `e.printStackTrace()` for logging — no structured audit events. |
| **Gap** | No CloudTrail or equivalent audit logging. No ability to trace API calls, user actions, or infrastructure changes. No immutable log storage. |
| **Recommendation** | Enable CloudTrail with log file validation and S3 storage with Object Lock for immutability. Add CloudTrail to the Terraform IaC when migrating. For application-level audit logging, implement structured audit events (JSON format) for user actions (login, basket operations) and send to CloudWatch Logs with extended retention. |
| **Evidence** | `MonoToMicroCF.yaml` — no `AWS::CloudTrail::*`; `InstanceLogGroup` with 7-day retention (app logs only); `HealthController.java` — `System.out.println` used for logging |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configured. S3 buckets (`UIBucket`, `AssetBucket`) have no encryption configuration — no `BucketEncryption` property, no `SSEAlgorithm`. `RDSCluster` has no `StorageEncrypted` property (defaults to `false` for Aurora MySQL 2.x). EC2 instances have no EBS encryption. No `AWS::KMS::Key` resources in CloudFormation. No customer-managed or AWS-managed KMS keys referenced anywhere. |
| **Gap** | No encryption at rest on any data store — S3 buckets, Aurora cluster, and EBS volumes are all unencrypted. This is a baseline security requirement. |
| **Recommendation** | Enable encryption at rest on all data stores: (1) S3 — enable default SSE-S3 or SSE-KMS encryption, (2) Aurora MySQL — set `StorageEncrypted: true` with a customer-managed KMS key, (3) EBS — enable default EBS encryption in the account. Create a centralized KMS key with rotation policy. When migrating to Terraform, use a KMS module for key management. |
| **Evidence** | `MonoToMicroCF.yaml` — `UIBucket` (no encryption), `AssetBucket` (no encryption), `RDSCluster` (no `StorageEncrypted`); no `AWS::KMS::Key` resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All API endpoints are unauthenticated. `ResourceServerConfig.java` configures Spring Security OAuth2 resource server but explicitly permits all requests: `.authorizeRequests().anyRequest().permitAll()`. Every controller method has `@PreAuthorize("permitAll()")` annotation. OAuth2 dependencies exist in `build.gradle` (`spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`, `spring-security-jwt`), but they are not configured — no JWT validation, no OAuth2 provider, no token verification. The `Application.java` inner class ignores all OPTIONS requests for CORS workaround. |
| **Gap** | No API authentication — all endpoints are open. OAuth2 libraries are present but configured to permit all requests. Any caller can create users, modify baskets, and access all data without authentication. This is a critical security vulnerability. |
| **Recommendation** | Implement token-based authentication using Amazon Cognito (integrate with the e-commerce platform's identity needs) or API Gateway authorizers (per preferences). When deploying on EKS behind API Gateway, use Cognito User Pool or Lambda authorizers for JWT validation. Remove `permitAll()` from `ResourceServerConfig` and controllers. |
| **Evidence** | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` — `.anyRequest().permitAll()`; all controllers — `@PreAuthorize("permitAll()")`; `build.gradle` — OAuth2 deps present but unconfigured |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. OAuth2 libraries are present (`spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`) but not configured for any external IdP. No Cognito, Okta, Ping, or SAML configuration. The application manages its own user authentication via email lookup (`/user/login` endpoint calls `userService.getByEmail`). No password verification — the login endpoint just checks if the email exists in the database. `CoreConfig.java` creates a `BCryptPasswordEncoder` bean but it is not used in any authentication flow. |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. The login flow has no actual password verification — it only checks email existence. No SSO, no federation, no MFA. |
| **Recommendation** | Integrate with Amazon Cognito as the centralized identity provider for the e-commerce platform. Cognito provides user pools, OAuth2/OIDC flows, MFA, and federation with external IdPs. When the customer support agent needs to access user data, Cognito provides machine-to-machine OAuth2 flows (client credentials grant) for secure agent authentication. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/UserController.java` — `/user/login` does email lookup only; `src/main/java/com/monoToMicro/config/CoreConfig.java` — `BCryptPasswordEncoder` bean unused; `build.gradle` — OAuth2 libs unconfigured |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Database credentials are hardcoded in multiple locations: (1) `application.properties` — `spring.datasource.username: MonoToMicroUser`, `spring.datasource.password: MonoToMicroPassword` in plain text. (2) `MonoToMicroCF.yaml` — MySQL root password (`MonoToMicroPassword`) and user credentials in cfn-init commands, `RDSCluster` `MasterUsername`/`MasterUserPassword` in plain text, DMS endpoint credentials in plain text. The password `MonoToMicroPassword` appears 8+ times across the template. No `AWS::SecretsManager::*` resources. No Vault client. The MySQL setup includes an intermediate root password (`Jasdfklj*%lkj98`) also in plain text. |
| **Gap** | Critical: Credentials hardcoded in source code and IaC templates committed to version control. Database passwords visible in plain text. No secrets management, no rotation, no audit trail for credential access. |
| **Recommendation** | Migrate all secrets to AWS Secrets Manager immediately. Create a Secrets Manager secret for database credentials with automatic rotation. Reference secrets in CloudFormation via dynamic references (`{{resolve:secretsmanager:...}}`). In application code, use the AWS SDK to retrieve secrets at runtime or use Spring Cloud AWS Secrets Manager integration. Remove all hardcoded credentials from `application.properties` and CloudFormation templates. |
| **Evidence** | `src/main/resources/application.properties` — plain text username/password; `MonoToMicroCF.yaml` — `MasterUserPassword: MonoToMicroPassword`, MySQL root password in cfn-init commands, DMS endpoint passwords |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | SSM Agent is installed on EC2 instances (`AmazonSSMManagedInstanceCore` managed policy attached to the IAM role; SSM Agent RPM installed in cfn-init). Basic OS updates are performed during instance bootstrap (`sudo yum update -y` in cfn-init). CloudWatch agent is installed for log collection (`CloudWatchAgentServerPolicy` managed policy). However: no vulnerability scanning (no Inspector, no Snyk), no hardened AMI (uses default Amazon Linux 2 AMI via `LatestAmiId` SSM parameter), no regular patching strategy (only patches on instance creation), no EC2 Image Builder pipeline. |
| **Gap** | Manual patching process (only on instance bootstrap). Default AMIs with no CIS hardening or Bottlerocket. No vulnerability scanning. SSM Agent is present but no SSM Patch Manager configuration for ongoing patching. |
| **Recommendation** | Configure SSM Patch Manager for automated patching schedules. Enable AWS Inspector for continuous vulnerability scanning. When containerizing, use minimal base images (Amazon Corretto on Amazon Linux 2023 or Bottlerocket for EKS nodes). Enable ECR image scanning for container vulnerabilities. |
| **Evidence** | `MonoToMicroCF.yaml` — `S3Role` with `AmazonSSMManagedInstanceCore` and `CloudWatchAgentServerPolicy`; cfn-init `yum update -y`; `LatestAmiId` parameter uses default AMI |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | One security scanning tool is configured: GitHub Actions workflow (`.github/workflows/cfn-security.yml`) runs `cfn_nag` on every push, scanning CloudFormation templates in the `MonoToMicroAssets` directory for security misconfigurations. This is infrastructure security scanning only — it does not cover application source code. No SAST tool (no SonarQube, no Semgrep, no CodeGuru). No dependency scanning (no Dependabot, no `gradle audit`, no OWASP dependency-check). No container scanning (no Dockerfiles to scan, but will need it after containerization). Known vulnerable dependencies: Spring Boot 2.1.x, MyBatis 3.2.2 (from 2013), AWS SDK 1.11.567 — all have known CVEs. |
| **Gap** | Only infrastructure security scanning (cfn-nag). No application SAST, no dependency vulnerability scanning, no container scanning. Multiple known-vulnerable dependencies in `build.gradle` (Spring Boot 2.1.x, MyBatis 3.2.2, AWS SDK 1.11.x). |
| **Recommendation** | Add OWASP Dependency-Check or Snyk to the GitHub Actions pipeline for dependency scanning. Add Semgrep or SonarQube for SAST. When containerized, add ECR image scanning and Trivy/Snyk container scanning. Configure security gates that block builds with critical vulnerabilities. Update all dependencies to current versions as part of the Java 17 / Spring Boot 3.x upgrade. |
| **Evidence** | `.github/workflows/cfn-security.yml` — cfn-nag on `MonoToMicroAssets`; `build.gradle` — `mybatis:3.2.2` (2013), `spring-boot:2.1.x` (2018), `aws-java-sdk:1.11.567` (2019) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No X-Ray SDK, no OpenTelemetry SDK, no Zipkin/Jaeger in `build.gradle` dependencies. No trace ID propagation in controllers or service layer. `spring-boot-starter-actuator` is included but not configured for tracing (no Micrometer Tracing, no Sleuth). Application logging uses `System.out.println` and `e.printStackTrace()` — no structured logging with trace/span IDs. |
| **Gap** | No distributed tracing — no ability to trace requests through the system. When decomposed into microservices, debugging cross-service failures will be impossible without end-to-end tracing. |
| **Recommendation** | Add OpenTelemetry Java Agent as a sidecar when containerizing on EKS. Configure trace propagation headers (`traceparent`/`X-Amzn-Trace-Id`) and export traces to AWS X-Ray. Replace `System.out.println` with structured logging (SLF4J/Logback with JSON format) including trace IDs. |
| **Evidence** | `build.gradle` — `spring-boot-starter-actuator` present but no tracing dependencies; no OpenTelemetry/X-Ray SDK; `HealthController.java` — `System.out.println` logging |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No error budget tracking. No CloudWatch alarms for latency, availability, or error rates. No SLO configuration files. No `AWS::CloudWatch::Alarm` resources in CloudFormation. The only monitoring is CloudWatch Logs for the application log file — no metrics-based monitoring. |
| **Gap** | No formal SLOs defined. No measurement of whether the system meets user expectations. No error budgets to guide modernization investment prioritization. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Product listing availability ≥ 99.9%, p99 latency ≤ 500ms, (2) Basket operations availability ≥ 99.95%, p99 latency ≤ 1s, (3) User login availability ≥ 99.9%. Implement CloudWatch Composite Alarms for SLO monitoring. Track error budgets to decide when to invest in reliability vs features. |
| **Evidence** | `MonoToMicroCF.yaml` — no `AWS::CloudWatch::Alarm` resources; no SLO files in repository |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. The CloudWatch agent collects only the application log file (`app.log`). No `cloudwatch.putMetricData` calls in source code. No custom dashboards. No business outcome tracking (conversion rates, basket abandonment, items per basket, user sign-up rates). Only default EC2 infrastructure metrics (CPU, network) are available from the CloudWatch agent. |
| **Gap** | Infrastructure metrics only with no business outcome tracking. Cannot measure business impact of modernization or identify feature-level issues. |
| **Recommendation** | Instrument custom CloudWatch metrics for business outcomes: `BasketItemsAdded`, `BasketItemsRemoved`, `UserRegistrations`, `LoginAttempts`, `LoginSuccesses`, `ProductViews`. Publish metrics using AWS SDK v2 CloudWatch client or Micrometer with CloudWatch registry. Create a CloudWatch dashboard for real-time business KPI visibility. |
| **Evidence** | `MonoToMicroCF.yaml` — CloudWatch agent config collects only `app.log`; no `PutMetricData` calls in source code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured. No `AWS::CloudWatch::Alarm` resources in CloudFormation. No anomaly detection. No PagerDuty, OpsGenie, or SNS notification integration. No static threshold alarms (CPU, error rate, disk space). The application has no health monitoring beyond the manual `/health/ishealthy` and `/health/dbping` endpoints. |
| **Gap** | No alerting — operational issues can only be discovered by manually checking logs or health endpoints. No proactive notification for degradation or failures. |
| **Recommendation** | Create CloudWatch alarms for: (1) HTTP 5xx error rate > 1%, (2) p99 latency > 2s, (3) Database connection failures, (4) Disk space utilization > 80%. Enable CloudWatch Anomaly Detection on error rates and latency for adaptive thresholds. Integrate with SNS → PagerDuty/OpsGenie for on-call notification. |
| **Evidence** | `MonoToMicroCF.yaml` — no `AWS::CloudWatch::Alarm`; `HealthController.java` — manual health endpoints only |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment via EC2 instance bootstrap. The application is deployed by CloudFormation cfn-init during instance creation — the EC2 instance clones the Git repository, builds the JAR with Gradle, installs Nginx, and starts the service. Re-deployment requires updating the CloudFormation stack (which may replace the EC2 instance) or manually SSHing into the instance. No blue/green, no canary, no rolling updates. No CodeDeploy, no Helm rollouts, no ArgoCD. The systemd service (`mono2micro.service`) has basic restart-on-failure but no traffic shifting or staged rollout. |
| **Gap** | Direct-to-production deployment with no staged rollout. Any deployment failure affects all users immediately. No automated rollback capability. Re-deployment is manual and disruptive. |
| **Recommendation** | When containerized on EKS, implement GitOps with ArgoCD (per preferences) for declarative, automated deployments. Use ArgoCD rollouts with canary strategy — deploy to a small percentage of traffic first, verify health, then promote. Configure automated rollback on health check failure. Avoid manual deployments (per preferences). |
| **Evidence** | `MonoToMicroCF.yaml` — cfn-init deployment in `EC2Instance` metadata; `m2mrun.sh` — direct JAR execution; `mono2micro.service` — systemd service with restart-on-failure |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No test files exist in the project. `build.gradle` includes `testImplementation('org.springframework.boot:spring-boot-starter-test')` as a dependency, but no test directory (`src/test/`) exists. No integration tests, no API tests, no contract tests, no end-to-end tests. No test execution in the CI pipeline (the only pipeline stage is cfn-nag security scan). No Postman/Newman collections. No test containers configuration. |
| **Gap** | No automated tests at all — neither unit tests nor integration tests. The `spring-boot-starter-test` dependency is unused. This creates significant regression risk during decomposition — extracting services without test coverage means no safety net for detecting broken functionality. |
| **Recommendation** | Before starting decomposition: (1) Write integration tests for all API endpoints using Spring Boot Test and MockMvc, (2) Write database integration tests using Testcontainers (MySQL container), (3) Add contract tests (Pact) for API contracts that the customer support agent will consume. Add test execution to the CI pipeline as a gate. |
| **Evidence** | `build.gradle` — `spring-boot-starter-test` in dependencies; no `src/test/` directory in project; `.github/workflows/cfn-security.yml` — no test stage |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found — no markdown, YAML, or JSON runbook files in the repository. No SSM Automation documents. No Lambda-based remediation. No self-healing automation. The systemd service has basic `Restart=on-failure` with `RestartSec=60`, which is the only automated recovery mechanism. Incident response is entirely ad hoc — no documented procedures for common failures (database connection loss, disk full, OOM). |
| **Gap** | No incident response automation. No runbooks. The only automated recovery is systemd restart-on-failure for the application process. |
| **Recommendation** | Create runbooks (markdown format, version-controlled) for common operational scenarios: database connection failure, disk space exhaustion, high memory usage, deployment rollback. Implement SSM Automation documents for automated remediation of the most common issues. When on EKS, leverage Kubernetes liveness/readiness probes and pod auto-restart for self-healing. |
| **Evidence** | No runbook files in repository; `MonoToMicroCF.yaml` — `mono2micro.service` with `Restart=on-failure` only; no SSM Automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file in the repository. No per-service dashboards (no dashboards at all). No named alarm owners (no alarms exist). Only a basic CloudWatch log group (`InstanceLogGroup`) with 7-day retention for application logs — no team attribution, no ownership tags. No SLO definitions with team attribution. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No dashboards, no alarms, no team-specific observability assets. When decomposed into microservices, each service team needs clear ownership of their observability stack. |
| **Recommendation** | Define CODEOWNERS for observability configurations (alarms, dashboards, SLOs). Create per-service CloudWatch dashboards during decomposition. Tag all observability resources with `team`, `service`, and `environment` tags. Assign named owners to each alarm. |
| **Evidence** | No CODEOWNERS file; `MonoToMicroCF.yaml` — `InstanceLogGroup` with no ownership tags; no dashboards or alarms |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Tags exist on some CloudFormation resources but are limited to `Name` tags only: `MonoToMicroVPC`, `MonoToMicroIGW`, `MonoToMicroSubnet1-4`, `MonoToMicroDBSG`, `MonoToMicroEC2SG`, `MonoToMicroDB`, `MonoToMicroEC2`, `MonoToMicroPublicRoute`, `MonoToMicroPrivateRoute1/2`. The RDS cluster has a `Name` tag. DMS endpoints have `Name` tags. However: no cost allocation tags (`CostCenter`, `Project`), no ownership tags (`Team`, `Owner`), no environment tags (`Environment: production`), no application tags (`Application: unishop`). No tag enforcement via Config rules or Tag Policies. S3 buckets and IAM roles have no tags. |
| **Gap** | Only `Name` tags with no cost/ownership/environment attribution. Cannot track costs per workload, identify resource ownership during incidents, or enforce budget controls. No tag enforcement. |
| **Recommendation** | Define a tagging standard: `Environment`, `Application`, `Team`, `CostCenter`, `ManagedBy` (terraform/manual). Apply tags to all resources via IaC. When migrating to Terraform, use `default_tags` in the AWS provider block for automatic tagging. Implement AWS Config `required-tags` rule and Tag Policies in AWS Organizations for enforcement. |
| **Evidence** | `MonoToMicroCF.yaml` — `Name` tags on VPC, subnets, security groups, EC2, RDS, DMS; missing: cost, ownership, environment, application tags; no tag enforcement resources |

## Learning Materials

The following learning resources are mapped to the 5 triggered modernization pathways:

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `MonoToMicroAssets/MonoToMicroCF.yaml` | INF-Q1 through INF-Q11, SEC-Q1, SEC-Q2, SEC-Q5, SEC-Q6, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q7, OPS-Q8, OPS-Q9, DATA-Q3 | CloudFormation template defining all infrastructure: VPC, EC2, RDS Aurora, DMS, S3, IAM, security groups, CloudWatch log group |
| `build.gradle` | APP-Q1, APP-Q2, APP-Q3, SEC-Q3, SEC-Q7, OPS-Q1, OPS-Q6 | Gradle build file with Spring Boot 2.1.x, Java 8, MyBatis, AWS SDK v1, OAuth2, and test dependencies |
| `src/main/resources/application.properties` | INF-Q2, APP-Q6, SEC-Q5 | Application configuration with database connection string and hardcoded credentials |
| `database/create_tables.sql` | APP-Q2, DATA-Q1, DATA-Q3, DATA-Q4 | MySQL DDL for `unishop` schema with 3 tables and seed data |
| `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | APP-Q2, APP-Q3, APP-Q4, APP-Q5 | REST controller for basket operations (add/remove/get) |
| `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | APP-Q2, APP-Q3, APP-Q5 | REST controller for product catalog listing |
| `src/main/java/com/monoToMicro/rest/controller/UserController.java` | APP-Q2, APP-Q3, APP-Q5, SEC-Q4 | REST controller for user creation and login |
| `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | OPS-Q1, OPS-Q4, SEC-Q1 | Health check controller with EC2 metadata |
| `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | INF-Q3 | Data replication endpoint with inline orchestration logic |
| `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | SEC-Q3, SEC-Q4 | OAuth2 resource server config — permits all requests |
| `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | DATA-Q2 | Centralized MyBatis mapper configuration |
| `src/main/java/com/monoToMicro/config/CoreConfig.java` | SEC-Q4 | BCryptPasswordEncoder bean (unused) |
| `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | APP-Q2, APP-Q4 | Service layer handling both product catalog and basket operations |
| `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | APP-Q2, APP-Q4 | Service layer for user CRUD operations |
| `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | DATA-Q2 | Repository implementation for unicorn and basket data access |
| `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | DATA-Q2 | Repository implementation for user data access |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | DATA-Q2, DATA-Q4 | MyBatis SQL mapper for product and basket queries (SELECT, INSERT, DELETE, JOIN) |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | DATA-Q2, DATA-Q4 | MyBatis SQL mapper for user queries (INSERT, SELECT) |
| `src/main/resources/com/monoToMicro/core/repository/mappers/HealthMapper.xml` | DATA-Q4 | MyBatis SQL mapper for health check query |
| `.github/workflows/cfn-security.yml` | INF-Q11, SEC-Q7, OPS-Q6 | GitHub Actions workflow running cfn-nag security scan only |
| `src/main/java/com/monoToMicro/Application.java` | APP-Q2, SEC-Q3 | Spring Boot entry point with CORS workaround |
| `gradle/wrapper/gradle-wrapper.properties` | APP-Q1 | Gradle 7.4 wrapper configuration |
| `README.md` | Quick Agent Wins | Minimal README redirecting to external workshop URL |
