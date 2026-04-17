# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | MonoToMicroLegacy |
| **Date** | 2026-04-17 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | monolith, java, ec2, decomposition-target |
| **Context** | Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs. |
| **Overall Score** | **1.4 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.0 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 1.5 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.5 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.0 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.0 / 4.0 | ❌ Not Present |
| **Overall** | **1.4 / 4.0** | **❌ Not Present** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC — all infrastructure manually created (ClickOps) | Blocks reproducible environments, disaster recovery, and automated deployments. Foundation for all other modernization pathways. |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — all deployments are manual | Prevents continuous delivery, blocks safe decomposition, and makes every release a risk event. |
| 3 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith with single deployable unit, shared database, and no module boundaries | Prevents independent scaling, independent deployment, and team autonomy. Primary decomposition target per context. |
| 4 | SEC-Q5: Secrets Management | 1 | Database credentials hardcoded in plaintext in application.properties | Critical security vulnerability — credentials exposed in version control. Blocks compliance and production hardening. |
| 5 | INF-Q1: Managed Compute | 1 | All compute on raw EC2 with no managed container orchestration | Manual patching, no elastic scaling, no container orchestration. Blocks containerization and decomposition pathways. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2). The application uses a consistent Controller → Service → Repository → MyBatis Mapper pattern. All SQL is centralized in mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`), and the database schema is clearly defined in `database/create_tables.sql` with 3 well-structured tables (`unicorns`, `unicorns_basket`, `unicorn_user`).
- **What it enables:** A natural-language-to-SQL agent that can query unicorn catalog data, basket/order data, and user data through the existing MyBatis data access layer. This directly supports the context requirement: "The agent needs access to order and return data through discrete service APIs."
- **Additional steps:** Generate an OpenAPI specification from the existing Spring Boot REST endpoints to enable full API tool discovery. The current schema is simple enough for an agent to query directly via Amazon Bedrock with Aurora MySQL (post-migration).
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — `README.md` (minimal, links to workshop), `database/create_tables.sql` (schema definition with 3 tables and seed data), `application.properties` (configuration), and extensive Javadoc comments across all 48 Java source files providing class and method documentation.
- **What it enables:** A knowledge agent that indexes the codebase documentation, schema definitions, and code comments to answer developer questions about the application architecture, data model, and API behavior during the decomposition process.
- **Additional steps:** Aggregate documentation into a structured corpus. The existing documentation is minimal — enrich with auto-generated API documentation (e.g., Springfox/SpringDoc) and architecture decision records before indexing.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (monolith), INF-Q1=1 (raw EC2), APP-Q3=1 (all sync), APP-Q4=1 (all sync) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (raw EC2), no container definitions found; compute is EC2 (not Lambda/Fargate/ECS) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); MySQL is already open source — no commercial DB engines detected |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2=1 (self-managed MySQL), DATA-Q3=2 (version not pinned in IaC) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads found — application is a CRUD e-commerce API with no analytics or streaming |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (zero IaC), INF-Q11=1 (no CI/CD), OPS-Q5=1 (no deployment strategy), OPS-Q6=1 (no tests) |
| 7 | Move to AI | Triggered | Medium | Medium | Context contains "agent" (AI intent confirmed); no AI/agent frameworks, no vector DB, no RAG, no eval framework detected |

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a tightly-coupled Java Spring Boot monolith (APP-Q2=1) deployed on raw EC2 instances. `HealthController.java` uses `EC2MetadataUtils` to fetch instance metadata (accountId, AZ, instanceID, instanceType, region), confirming direct EC2 deployment. A single `build.gradle` produces one `bootJar` containing all domains: Unicorn catalog, Basket/Orders, User management, Health checks, and Data replication.

**Compute Model Gaps:** All compute runs on raw EC2 (INF-Q1=1). No ECS, EKS, or container orchestration is present. No auto-scaling (INF-Q7=1), no load balancer or API Gateway (INF-Q6=1).

**Communication Pattern Gaps:** All communication is synchronous HTTP request/response (APP-Q3=1). No messaging, event publishing, or async patterns exist. `DataReplicationController.replicate()` executes synchronously despite being potentially long-running (APP-Q4=1).

**Recommended Decomposition Approach:** Strangler Fig (Parallel Track) — see Decomposition Strategy section below. Three service boundaries are identifiable: (1) Unicorn Catalog Service, (2) Basket/Order Service, (3) User Service. Extract the Basket/Order service first to expose discrete order APIs for agent access per the stated context.

**Representative AWS Services:** Amazon EKS (preferred per user preferences), Amazon API Gateway (preferred), Amazon EventBridge (preferred for async communication), Amazon DynamoDB (preferred for basket data), AWS App Mesh for service mesh.

**Recommended Patterns:** Strangler Fig, Anti-corruption Layer, Event Sourcing, Saga, Hexagonal Architecture.

**Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** The Spring Boot application runs directly on raw EC2. `HealthController.java` fetches EC2 instance metadata. No Dockerfile, docker-compose.yml, Kubernetes manifests, or Helm charts exist in the repository. A commented-out `docker` block in `build.gradle` indicates containerization was considered but never implemented.

**Container Readiness Indicators:** The Spring Boot bootJar with `launchScript()` is a self-contained executable. The application reads its database endpoint from the `MONO_TO_MICRO_DB_ENDPOINT` environment variable, indicating some config externalization. Port 8080 is configured in `application.properties`. These are positive indicators for containerization — the application is nearly container-ready with minimal changes.

**Recommended Container Orchestration Platform:** Amazon EKS (preferred per user preferences — avoids self-managed Kubernetes and serverless/Lambda). Deploy the Spring Boot application as a Kubernetes Deployment with a Service on EKS. Use Amazon ECR for container image registry.

**Migration Approach:** Lift-and-containerize first — create a Dockerfile for the existing monolith, deploy to EKS, and validate. This is a prerequisite for the Strangler Fig decomposition (Move to Cloud Native pathway). Then refactor-and-extract services as decomposition progresses.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS App Runner (alternative), EKS managed node groups with Graviton instances for cost optimization.

**Prescriptive Guidance:** [Containerize and Migrate Applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/containerize-and-migrate-applications.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology:** Self-managed MySQL accessed via JDBC connection string `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The database runs on unknown infrastructure (no IaC defines it). Three tables: `unicorns`, `unicorns_basket`, `unicorn_user` in the `unishop` schema. MySQL connector version 8.0.11 (2018) is pinned in `build.gradle`, but actual server version is unknown (INF-Q2=1, DATA-Q3=2).

**Engine Version and EOL Status:** MySQL connector 8.0.11 dates from 2018 and is significantly outdated. The server version is unknown because no IaC defines the database. MySQL 8.0 is still supported, but the exact server version needs discovery before migration.

**Data Access Patterns:** Consistent Repository → MyBatis Mapper pattern (DATA-Q2=3). All SQL is standard (SELECT, INSERT, DELETE) with no stored procedures, triggers, or proprietary constructs (DATA-Q4=4). The `getUnicornBasket` query performs a JOIN between `unicorns` and `unicorns_basket` tables.

**Recommended Migration Target:** Amazon Aurora MySQL (preferred per user preferences for "aurora" and "aurora-mysql"). Aurora MySQL is wire-compatible with MySQL, enabling a drop-in migration with minimal application changes. For the Basket/Order service (post-decomposition), consider Amazon DynamoDB (preferred) for the `unicorns_basket` table to enable independent scaling.

**Migration Tools:** AWS Database Migration Service (DMS) for the initial data migration. No AWS Schema Conversion Tool (SCT) needed since MySQL → Aurora MySQL is homogeneous.

**Representative AWS Services:** Amazon Aurora MySQL, Amazon DynamoDB (for basket data post-decomposition), AWS DMS, Amazon RDS Proxy for connection pooling.

**Prescriptive Guidance:** [Migrate MySQL to Aurora MySQL](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/migrate-from-mysql-to-amazon-aurora-mysql.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:** Zero (INF-Q10=1). No Terraform, CloudFormation, CDK, Helm charts, or any IaC exists. All infrastructure is manually created. This is the most critical gap — without IaC, no other modernization pathway can be executed safely or reproducibly.

**Current CI/CD State:** None (INF-Q11=1). No GitHub Actions, GitLab CI, Jenkinsfile, buildspec.yml, or CodePipeline definitions. The `build.gradle` provides a Gradle build but deployment is entirely manual. `spring-boot-starter-test` is a declared dependency but no test files exist in `src/test/`.

**Deployment Strategy Gaps:** No deployment strategy (OPS-Q5=1). Direct-to-production with no canary, blue/green, or rolling updates. No feature flags.

**Testing Gaps:** No integration tests (OPS-Q6=1). No test files exist in the repository despite `spring-boot-starter-test` being declared as a dependency.

**Recommended DevOps Toolchain:**
1. **IaC:** Terraform (preferred per user preferences) for all AWS infrastructure — VPC, EKS cluster, Aurora MySQL, API Gateway, EventBridge, ECR.
2. **GitOps:** ArgoCD or Flux on EKS (preferred per user preferences for "gitops") for Kubernetes deployment management.
3. **CI/CD:** GitHub Actions or AWS CodePipeline with CodeBuild for build, test, container image build, and push to ECR. Avoid manual deployments (per preferences).
4. **Deployment Strategy:** Progressive delivery with ArgoCD Rollouts (canary/blue-green) on EKS.
5. **Testing:** Add JUnit integration tests, API contract tests, and container security scanning before any decomposition begins.

**Representative AWS Services:** AWS CodePipeline, AWS CodeBuild, Amazon ECR, Terraform with S3 backend, ArgoCD on EKS, AWS X-Ray for observability.

**Prescriptive Guidance:** [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-migration/devops.html)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Contextual Guard Check:** The context explicitly states: "The agent needs access to order and return data through discrete service APIs." The term "agent" is a recognized AI-related signal term. AI intent is confirmed — `has_ai_intent = true`.

**Current AI/Agent Infrastructure State:** No AI/agent framework usage detected. No Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, or HuggingFace imports in any of the 48 Java source files. No vector database infrastructure. No RAG implementation. No agent evaluation framework. The `build.gradle` contains only the AWS SDK v1 (`aws-java-sdk:1.11.567`) with no AI service clients.

**Application Domain and Potential AI Use Cases:** The context explicitly requires agent access to order and return data. Post-decomposition, the Basket/Order service API can serve as a tool endpoint for a Bedrock agent. Potential use cases:
- **Order Data Agent:** An Amazon Bedrock agent that queries order/basket data through the extracted Order Service API, enabling natural language queries against order history.
- **Product Catalog Agent:** A Bedrock agent that searches the unicorn product catalog for product information, pricing, and availability.
- **Customer Support Agent:** Combine order and user data APIs as agent tools for customer support automation.

**Foundation Requirements (must be in place before AI integration):**
1. Decompose the monolith to expose discrete REST APIs (Move to Cloud Native pathway — extract Basket/Order service first).
2. Generate OpenAPI specifications for extracted service APIs (enables Bedrock agent tool definition).
3. Implement API authentication (SEC-Q3=1 currently — APIs are open).
4. Migrate to Aurora MySQL (Move to Managed Databases pathway) to enable pgvector or OpenSearch for future RAG capabilities.

**Quick Wins:** See Quick Agent Wins section — the Data Query Agent can be an early proof-of-concept once the database is migrated to Aurora MySQL.

**Representative AWS Services:** Amazon Bedrock (preferred per user preferences), Amazon Bedrock AgentCore, Amazon Q Developer for code modernization assistance, Amazon OpenSearch Service (for future vector search/RAG).

**Prescriptive Guidance:** [Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

## Decomposition Strategy

> **Condition:** APP-Q2 = 1 (tightly-coupled monolith). This section provides concrete decomposition guidance.

### Architecture Analysis

The MonoToMicroLegacy application is a single-process Java Spring Boot monolith with the following structure:

- **Single deployable unit:** One `build.gradle` produces one `bootJar` with `launchScript()`.
- **Single entry point:** `Application.java` with `@SpringBootApplication`.
- **3 domain areas identified:**
  1. **Unicorn Catalog** — `UnicornController` → `UnicornService` → `UnicornRepository` → `UnicornMapper` (product CRUD)
  2. **Basket/Orders** — `BasketController` → `UnicornService` (add/remove/get basket) → `UnicornRepository` → `UnicornMapper` (basket operations)
  3. **User Management** — `UserController` → `UserService` → `UserRepository` → `UserMapper` (user CRUD, login)
- **Cross-cutting:** `HealthController` (health checks), `DataReplicationController` (data export), `CoreController` (shared base), `CoreModel` (shared model base)
- **Data coupling:** `unicorns_basket` table JOINs `unicorns` table (`UnicornMapper.xml` — `getUnicornBasket` query). All 3 tables share the single `unishop` MySQL schema.
- **Shared base classes:** `CoreModel` is extended by `Unicorn` and `User`; `CoreController` is extended by all controllers.

### Decomposition Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping it running. New features as services; existing features migrated over time. The monolith shrinks as services grow. | APP-Q2=1, but identifiable domain boundaries exist (Unicorn Catalog, Basket, User). Repository pattern provides separation. | **Medium to High** — 6-18 months. Each extraction is bounded. | ✅ **Recommended.** Lowest risk, incremental value delivery. Extract Basket/Order service first to enable agent access to order data. Run monolith and services side-by-side on EKS. |
| **Conditional / Adaptive** | Containerize monolith as-is on EKS, then selectively extract high-value services based on business priority. Some modules may remain in the monolith permanently. | Team has limited capacity. Business pressure requires quick wins before full architectural change. | **Low to Medium** — containerization in 2-4 weeks, selective extraction over 3-12 months. | ✅ **Recommended as Phase 1.** Containerize the monolith first on EKS, then extract Basket/Order service using Strangler Fig. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch, replacing the monolith in a single cutover. | Almost never. Only when the monolith is so degraded that incremental extraction is impossible. | **Very High** — 12-24+ months. High risk of scope creep, feature parity gaps, and failed cutover. | ⚠️ **Recommended against.** The existing code is structured enough (repository pattern, clean domain separation) for incremental extraction. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's data model. Prevent monolith design decisions from leaking into new services. | Every extraction — place ACL between the new Basket/Order service and the monolith to translate between models. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions across services that were previously a single DB transaction. | When extracting the Basket service — add-to-basket involves both `unicorns` and `unicorns_basket` tables. Post-decomposition, this spans two services. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture basket/order changes as events via Amazon EventBridge (preferred). Enable audit trails and event-driven integration. | When extracting Basket/Order service — publish basket events (item added, item removed) to EventBridge for downstream consumers and the agent. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear boundaries: business logic core, external interface ports, infrastructure adapters. | Every new extracted service — ensures testability, portability, and decoupling from EKS/Aurora/DynamoDB specifics. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors (Calibrated to This Codebase)

| Factor | Signal | Evidence | Impact on Effort |
|--------|--------|----------|------------------|
| Module boundaries | ✅ LOW effort | Repository pattern provides identifiable domain boundaries: `UnicornRepository`, `UserRepository`, `HealthRepository` with separate interfaces per domain. | Extraction boundaries are clear — each domain has its own Controller → Service → Repository stack. |
| Data coupling | 🟠 HIGH effort | `unicorns_basket` table JOINs `unicorns` table in `UnicornMapper.xml`. All 3 tables share the `unishop` schema on a single MySQL instance. | Basket extraction requires breaking the JOIN — either duplicate the unicorn data or use an API call. Schema separation needed. |
| Stored procedures | ✅ LOW effort | No stored procedures, triggers, or proprietary SQL (DATA-Q4=4). All SQL is standard INSERT/SELECT/DELETE in MyBatis mappers. | No database-layer business logic to extract. Clean migration path. |
| Communication patterns | 🟠 HIGH effort | All synchronous HTTP (APP-Q3=1). No async patterns, no event publishing, no message queues. | Must introduce EventBridge (preferred) for inter-service communication during decomposition. |
| CI/CD maturity | 🔴 HIGH effort | No CI/CD exists (INF-Q11=1). No build pipeline, no deployment automation. | Must build CI/CD pipeline from scratch before decomposition can begin safely. |
| Test coverage | 🔴 HIGH effort | No automated tests (OPS-Q6=1). `spring-boot-starter-test` declared but no test files in `src/test/`. | No safety net for extraction — must add tests before extracting any service. |

### Calibrated Effort Estimate

**Overall Effort: High.** While module boundaries exist and there are no stored procedures (both positive), the complete absence of CI/CD, testing, and container infrastructure means significant foundational work is needed before decomposition can begin safely.

**Recommended Phased Approach:**

1. **Phase 0 — Foundation (4-6 weeks):** Terraform IaC for VPC, EKS cluster, Aurora MySQL, ECR. CI/CD pipeline with GitHub Actions or CodePipeline. Containerize monolith with Dockerfile, deploy to EKS.
2. **Phase 1 — Migrate Database (2-4 weeks):** Migrate self-managed MySQL to Aurora MySQL using DMS. Update connection string. Validate.
3. **Phase 2 — Add Tests (2-4 weeks):** Add JUnit integration tests for Basket/Order and User workflows. Establish test baseline before extraction.
4. **Phase 3 — Extract Basket/Order Service (6-10 weeks):** Strangler Fig extraction of BasketController + basket-related UnicornService methods into a new Basket/Order microservice on EKS. New service uses DynamoDB (preferred) for basket data. API Gateway routes basket requests to new service, all other requests to monolith.
5. **Phase 4 — Agent Integration (4-6 weeks):** Generate OpenAPI spec for Basket/Order service. Configure Amazon Bedrock agent with order API as a tool. Implement API authentication (Cognito + API Gateway authorizer).
6. **Phase 5 — Extract Remaining Services (8-12 weeks):** Extract Unicorn Catalog service and User service. Introduce EventBridge for inter-service events.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs on raw EC2. `HealthController.java` uses `EC2MetadataUtils.getInstanceInfo()` to fetch accountId, AZ, instanceID, instanceType, and region — confirming direct EC2 deployment. No ECS, EKS, Lambda, or Fargate resources found. No container definitions exist. A commented-out `docker` block in `build.gradle` was never activated. |
| **Gap** | 100% of compute is unmanaged EC2 with no container orchestration, no auto-scaling, and no managed runtime. |
| **Recommendation** | Containerize the Spring Boot application and deploy to Amazon EKS (preferred). Create a Dockerfile, push to Amazon ECR, deploy as a Kubernetes Deployment. Use EKS managed node groups with Graviton instances for cost optimization. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (EC2MetadataUtils usage), `build.gradle` (commented-out docker block), absence of Dockerfile/K8s manifests |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The database is self-managed MySQL. `application.properties` shows JDBC connection to `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop` with hardcoded credentials. No IaC exists to define managed database resources (`aws_rds_*`, `aws_dynamodb_*`). The database endpoint is configured via environment variable but the database itself is not provisioned through any managed service configuration in the repository. |
| **Gap** | Database is entirely self-managed — no managed service, no automated failover, no automated backups configured in the repository. |
| **Recommendation** | Migrate to Amazon Aurora MySQL (preferred). Use AWS DMS for data migration. Define Aurora cluster in Terraform with Multi-AZ, automated backups, and RDS Proxy for connection pooling. |
| **Evidence** | `src/main/resources/application.properties` (JDBC connection string, hardcoded credentials), `database/create_tables.sql` (MySQL schema), `build.gradle` (mysql-connector-java:8.0.11), absence of IaC |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service detected. No Step Functions, Temporal, Camunda, or workflow engine imports in code or dependencies. All business logic follows a direct Controller → Service → Repository → Mapper chain with no orchestration layer. `UnicornServiceImpl.java` and `UserServiceImpl.java` implement business logic as direct synchronous method calls. |
| **Gap** | All workflow logic is hardcoded in application code with no dedicated orchestration, no visual workflow management, and no built-in retry/error handling. |
| **Recommendation** | For the Basket/Order service post-decomposition, consider AWS Step Functions for order workflow orchestration (order placement → payment → fulfillment). For the data replication workflow (`DataReplicationController`), use Step Functions to manage the long-running replication process. |
| **Evidence** | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java`, `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java`, `build.gradle` (no workflow dependencies) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure. No SQS, SNS, EventBridge, MSK, or Kinesis in dependencies or IaC. No message publishing patterns in code. All 5 controllers (`BasketController`, `UnicornController`, `UserController`, `DataReplicationController`, `HealthController`) use synchronous HTTP request/response exclusively. `build.gradle` contains no messaging SDK dependencies. |
| **Gap** | All communication is synchronous HTTP with no async patterns, no event-driven architecture, and no decoupled messaging. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for inter-service events during decomposition. Publish basket events (item added, item removed) as EventBridge events. Use SQS for reliable async processing of data replication. |
| **Evidence** | All controller files (synchronous patterns only), `build.gradle` (no messaging dependencies), absence of messaging configuration |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL definitions found. No IaC exists at all. The application exposes port 8080 directly (`server.port=8080` in `application.properties`). No network security configuration is present in the repository. `ResourceServerConfig.java` permits all requests with `anyRequest().permitAll()`. |
| **Gap** | No network segmentation, no security groups, no private subnets. Services potentially exposed directly to the internet with no network-level protection. |
| **Recommendation** | Define VPC with private subnets in Terraform (preferred). Deploy EKS worker nodes in private subnets. Use ALB Ingress Controller for external access with security groups restricting inbound traffic. Implement Kubernetes NetworkPolicies for pod-to-pod traffic control. |
| **Evidence** | `src/main/resources/application.properties` (server.port=8080), `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll), absence of any IaC or network configuration |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront defined. The Spring Boot application exposes port 8080 directly with no gateway, no throttling, no request validation, and no authentication at the entry point. `ResourceServerConfig.java` uses `permitAll()` with CORS enabled on all origins. `MVCConfig.java` allows all HTTP methods on all paths. |
| **Gap** | Services exposed directly with no managed entry point, no throttling, no authentication layer, and no request validation. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the managed entry point. Configure throttling, request validation, and Cognito authorizer. During decomposition, API Gateway routes requests to appropriate backend services on EKS via ALB. |
| **Evidence** | `src/main/resources/application.properties` (server.port=8080), `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, `src/main/java/com/monoToMicro/config/MVCConfig.java`, absence of gateway/ALB IaC |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No ASG, application auto-scaling, Lambda concurrency limits, or HPA (Horizontal Pod Autoscaler) definitions. `HealthController.java` fetches single-instance EC2 metadata, suggesting a single-instance deployment with no scaling capability. |
| **Gap** | All capacity is statically provisioned with no ability to respond to traffic spikes or scale down during low demand. |
| **Recommendation** | Deploy on EKS (preferred) with Horizontal Pod Autoscaler (HPA) based on CPU/memory utilization. Configure EKS Cluster Autoscaler or Karpenter for node-level scaling. Define resource requests and limits in Kubernetes manifests. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (single instance metadata), absence of IaC or scaling configuration |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no `backup_retention_period`, no PITR configuration, no S3 versioning. No IaC exists to define any backup strategy. The self-managed MySQL database has no backup automation defined in the repository. |
| **Gap** | No automated backups, no point-in-time recovery, no restore procedures. A data loss event would have no recovery path defined in the repository. |
| **Recommendation** | Migrate to Aurora MySQL (preferred) which includes automated backups with configurable retention and PITR by default. Define backup retention period in Terraform. For additional protection, configure AWS Backup with cross-region backup copies. |
| **Evidence** | Absence of any IaC, backup configuration, or backup-related code |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration found. `HealthController.java` fetches a single EC2 instance's availability zone, suggesting single-instance, single-AZ deployment. No load balancer distributes traffic across AZs. No IaC defines multi-AZ database or compute resources. |
| **Gap** | Single-AZ deployment — an AZ failure would take down the entire application with no automatic recovery. |
| **Recommendation** | Deploy EKS (preferred) with worker nodes across 2+ AZs. Configure Aurora MySQL (preferred) with Multi-AZ for automatic failover. Use Kubernetes pod anti-affinity rules to spread pods across AZs. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (single AZ in instance metadata), absence of IaC or multi-AZ configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform (`.tf`), CloudFormation (`.cfn.yaml`), CDK (`cdk.json`), Helm charts (`Chart.yaml`), Kustomize (`kustomization.yaml`), or Ansible playbooks found anywhere in the repository. All infrastructure — EC2 instances, MySQL database, networking — appears to be manually created (ClickOps). |
| **Gap** | 0% IaC coverage. Infrastructure changes are manual, error-prone, non-reproducible, and unauditable. No disaster recovery capability via IaC re-creation. |
| **Recommendation** | Adopt Terraform (preferred) for all infrastructure: VPC, subnets, security groups, EKS cluster, Aurora MySQL, ECR repositories, API Gateway, EventBridge. Store Terraform state in S3 with DynamoDB locking. This is the highest-priority gap — all other modernization pathways depend on IaC. |
| **Evidence** | Absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files in the entire repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline found. No GitHub Actions (`.github/workflows/`), GitLab CI (`.gitlab-ci.yml`), Jenkins (`Jenkinsfile`), CodeBuild (`buildspec.yml`), or CodePipeline definitions. The `build.gradle` provides a Gradle build with Spring Boot plugin, but there is no automation around build, test, or deploy. `spring-boot-starter-test` is declared as a dependency but no test files exist in `src/test/`. |
| **Gap** | All deployments are manual. No automated build, test, or deploy pipeline. No quality gates, no automated rollback, no deployment tracking. |
| **Recommendation** | Implement CI/CD with GitHub Actions or AWS CodePipeline + CodeBuild (avoid manual deployments per preferences). Pipeline stages: (1) Build Gradle project, (2) Run JUnit tests, (3) Build Docker image, (4) Push to ECR, (5) Deploy to EKS via ArgoCD (GitOps preferred). Add security scanning (SAST, dependency scanning) as pipeline gates. |
| **Evidence** | `build.gradle` (Gradle build exists but no CI/CD), absence of `.github/workflows/`, `Jenkinsfile`, `buildspec.yml`, or any pipeline configuration |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java is the primary and only language. Spring Boot 2.1.6 framework with `sourceCompatibility = 1.8` (Java 8). Java has a mature cloud-native ecosystem: excellent container support, extensive AWS SDK coverage (v1 and v2), rich Spring Cloud ecosystem, large community, strong tooling (Maven/Gradle, JUnit, IntelliJ/Eclipse). 48 Java source files under `src/main/java/com/monoToMicro/`. |
| **Gap** | Java 8 is at end-of-life. Spring Boot 2.1.6 is significantly outdated (2019). AWS SDK v1 (1.11.567) is in maintenance mode. These are version gaps, not language gaps — Java itself scores 4. |
| **Recommendation** | Upgrade to Java 17+ (LTS) and Spring Boot 3.x during containerization. Migrate from AWS SDK v1 to AWS SDK v2 for better performance and non-blocking I/O. These upgrades should be done before or during the containerization phase. |
| **Evidence** | `build.gradle` (Java, sourceCompatibility=1.8, Spring Boot 2.1.6, aws-java-sdk:1.11.567), all `.java` source files |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Tightly-coupled monolith with a single deployable unit. Single `@SpringBootApplication` entry point in `Application.java`. Single `build.gradle` produces one `bootJar`. All domains — Unicorn catalog, Basket/Orders, User management, Health checks, Data replication — share the same database (`unishop` schema), same deployment, and same JVM process. Shared database coupling: `unicorns_basket` table JOINs `unicorns` table in `UnicornMapper.xml`. Models share `CoreModel` base class. Controllers share `CoreController` base class. `UnicornService` handles both catalog and basket operations (mixed responsibilities). |
| **Gap** | No decomposition, no module boundaries, pervasive shared state through single MySQL database, shared base classes creating inheritance coupling. Cannot independently scale, deploy, or evolve any domain. |
| **Recommendation** | Execute Strangler Fig decomposition (see Decomposition Strategy section). Extract Basket/Order service first to enable agent access to order data. Use API Gateway (preferred) to route traffic between monolith and extracted services on EKS. |
| **Evidence** | `src/main/java/com/monoToMicro/Application.java`, `build.gradle` (single bootJar), all controller/service/repository files in single deployment, `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (JOIN between tables) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | 100% synchronous HTTP communication. All controllers return `ResponseEntity` synchronously: `BasketController.addUnicornToBasket()`, `UnicornController.getUnicorns()`, `UserController.createUser()`, `UserController.login()`, `DataReplicationController.replicate()`. No `CompletableFuture`, `@Async`, messaging SDK imports, event publishing patterns, or queue consumers in any source file. No SQS, SNS, or EventBridge usage. |
| **Gap** | All communication is synchronous with no async patterns. Creates tight coupling, cascading failure risk, and timeout vulnerability for operations like data replication. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for inter-service events during decomposition. Basket operations (add/remove) should publish events for downstream consumers. Data replication should be async via SQS. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `UnicornController.java`, `UserController.java`, `DataReplicationController.java` (all synchronous ResponseEntity returns), `build.gradle` (no messaging dependencies) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All operations are synchronous regardless of duration. `DataReplicationController.replicate()` fetches all baskets via `unicornService.getAllBaskets()` synchronously — this could be long-running for large datasets but has no async handling, no progress tracking, and no timeout management. No background job frameworks (Celery, Bull, SQS workers). No `@Async` annotations. No job status APIs. No Step Functions integration. |
| **Gap** | No async handling for potentially long-running operations. Data replication runs synchronously with no timeout protection, no progress reporting, and no retry capability. |
| **Recommendation** | Implement async job processing with SQS and EKS worker pods for data replication. Use Step Functions for complex multi-step workflows. Expose job status endpoints for progress tracking. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` (synchronous replicate), `build.gradle` (no async framework dependencies) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. Endpoints: `/unicorns` (GET), `/unicorns/basket` (POST, DELETE, GET), `/user` (POST), `/user/login` (POST), `/health/ping` (GET), `/health/ishealthy` (GET), `/health/dbping` (GET), `/data` (GET). None use `/v1/` prefix, versioning headers, or query parameters. No OpenAPI specification exists. No changelog files. |
| **Gap** | No versioning — any breaking API change would break all consumers simultaneously. No API documentation or specification. |
| **Recommendation** | Introduce URL-based versioning (`/v1/unicorns`, `/v1/basket`) during decomposition. Generate OpenAPI specifications using SpringDoc/Springfox. This is a prerequisite for Bedrock agent integration (agents require API specs for tool definition). |
| **Evidence** | All `@RequestMapping` annotations in controller files (unversioned paths), absence of `openapi.yaml`, `swagger.yaml`, or changelog files |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism. The application is a monolith — there is no inter-service communication because it IS the single service. The database endpoint is configured via the `MONO_TO_MICRO_DB_ENDPOINT` environment variable in `application.properties`, which is a basic configuration approach. No AWS Cloud Map, App Mesh, Consul, or Istio. No API Gateway serving as a service catalog. |
| **Gap** | No service discovery infrastructure. As decomposition proceeds, extracted services will need dynamic discovery to avoid hard-coded endpoints. |
| **Recommendation** | During decomposition, implement service discovery via Kubernetes DNS (built into EKS) for internal service-to-service communication. Use API Gateway (preferred) as the external service catalog and entry point. Consider AWS App Mesh for advanced traffic management as the number of services grows. |
| **Evidence** | `src/main/resources/application.properties` (MONO_TO_MICRO_DB_ENDPOINT env var), absence of service discovery configuration |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 usage for unstructured data. AWS SDK S3 dependency exists in `build.gradle` (`aws-java-sdk-s3:1.11.567`) but no S3 client code, bucket operations, or document processing logic found in any source file. The application deals exclusively with structured MySQL data (3 relational tables). No Textract, Tika, or document parsing libraries. Product images are referenced by name string only (`image` column in `unicorns` table) — actual image storage is not managed by this application. |
| **Gap** | No managed object storage for unstructured data. Product images are stored externally with no parsing pipeline. S3 SDK is imported but unused. |
| **Recommendation** | During decomposition, store product images in Amazon S3. If the application needs document processing capabilities in the future, integrate Amazon Textract or Rekognition. Remove unused S3 SDK dependency or implement S3 integration for product images. |
| **Evidence** | `build.gradle` (aws-java-sdk-s3:1.11.567 — unused), `database/create_tables.sql` (image column is varchar, not binary), absence of S3 client code in source files |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application uses a consistent Repository pattern: Controller → Service → Repository Interface → Repository Implementation → MyBatis Mapper → XML SQL. Three domain repositories exist: `UnicornRepository`/`UnicornRepositoryImpl`, `UserRepository`/`UserRepositoryImpl`, `HealthRepository`/`HealthRepositoryImpl`. All SQL is centralized in MyBatis mapper XML files (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`). `MyBatisConfig.java` wires all mappers through a single `SqlSessionFactory` with one `DataSource`. No scattered database connections. |
| **Gap** | While the repository pattern is consistent, there is no single unified data access contract. Each domain has its own repository interface. `UnicornService` handles both catalog and basket operations (mixed responsibility in the data access path). |
| **Recommendation** | During decomposition, each extracted service should own its data access layer completely. The existing repository pattern provides a clean extraction boundary — each service gets its own repository, mapper, and database. |
| **Evidence** | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`, `src/main/java/com/monoToMicro/config/MyBatisConfig.java`, mapper XMLs |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MySQL connector version is explicitly pinned in `build.gradle`: `mysql-connector-java:8.0.11`. This indicates MySQL 8.x compatibility. However, the actual MySQL server version is unknown — no IaC defines the database server. The connector version 8.0.11 dates from April 2018 and is significantly outdated (current is 8.x.35+). The `CREATE TABLE` statements in `create_tables.sql` use `ENGINE=InnoDB` and `UTF8MB4` charset — both MySQL 8.0 features. |
| **Gap** | Connector version is pinned but outdated (2018). Server version is unknown and unmanaged. No IaC pins the database engine version. EOL risk cannot be fully assessed without knowing the server version. |
| **Recommendation** | Discover the actual MySQL server version. Migrate to Aurora MySQL (preferred) with explicit engine version pinning in Terraform. Update mysql-connector-java to the latest 8.x version. Aurora MySQL provides automatic minor version upgrades. |
| **Evidence** | `build.gradle` (mysql-connector-java:8.0.11), `database/create_tables.sql` (InnoDB, UTF8MB4), absence of IaC with engine version |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. `database/create_tables.sql` contains only `CREATE SCHEMA`, `CREATE TABLE`, and `INSERT` statements — standard SQL with no vendor-specific extensions. All MyBatis mapper XMLs use standard SQL: `SELECT *`, `INSERT IGNORE INTO`, `DELETE FROM`, `JOIN` — all ANSI-compatible. All business logic resides in the application layer (`UnicornServiceImpl`, `UserServiceImpl`). No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` found anywhere. |
| **Gap** | None — this is a strength. No stored procedure coupling, no proprietary SQL, clean separation of business logic from database layer. |
| **Recommendation** | Maintain this pattern during decomposition. Keep all business logic in the application layer. This clean separation enables straightforward database migration (MySQL → Aurora MySQL) with no logic extraction required. |
| **Evidence** | `database/create_tables.sql`, `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration found. No IaC exists to define audit logging. Application-level logging is limited to `System.out.println()` in `HealthController.java` for instance info output and exception stack traces via `e.printStackTrace()` in repository implementations. No structured logging framework (SLF4J/Logback configured by Spring Boot but not customized). No log aggregation or immutable log storage. |
| **Gap** | No audit logging — no CloudTrail, no immutable logs, no structured application logging. Actions cannot be traced or forensically analyzed. |
| **Recommendation** | Enable CloudTrail with log file validation and S3 Object Lock for immutable storage via Terraform. Configure structured logging with SLF4J/Logback in the Spring Boot application. Ship application logs to CloudWatch Logs via the EKS Fluent Bit DaemonSet. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println), absence of IaC or logging configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS configuration found. No encryption at rest on any data store. No IaC exists to configure encryption. No `kms_key_id` references, no `aws_kms_key` resources, no encryption configuration on databases or storage. The self-managed MySQL database's encryption state is unknown and unmanaged by this repository. |
| **Gap** | No encryption at rest configured. Sensitive data (user emails, order data) stored without encryption guarantees. |
| **Recommendation** | Aurora MySQL (preferred) supports encryption at rest by default with AWS-managed keys. Define customer-managed KMS keys in Terraform for sensitive data stores. Enable encryption on all EBS volumes, S3 buckets, and database storage. |
| **Evidence** | Absence of any IaC, KMS configuration, or encryption-related code |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Security is configured but effectively disabled. Spring Security OAuth2 dependencies exist in `build.gradle` (`spring-boot-starter-security`, `spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`, `spring-security-jwt`). However, `ResourceServerConfig.java` uses `.authorizeRequests().anyRequest().permitAll()` — all requests are permitted. Every controller endpoint uses `@PreAuthorize("permitAll()")`. `Application.java` contains `CorsOptionsRequestSecurityConfigurationAdapter` that ignores all OPTIONS requests. The comment "workaround to get CORS working with this old version, not recommended for production usage!" confirms this is intentionally insecure. |
| **Gap** | All API endpoints are unauthenticated. Security framework is present but fully disabled. Anyone can access any endpoint without credentials. |
| **Recommendation** | Implement API authentication via Amazon Cognito user pool integrated with API Gateway (preferred). Add JWT validation middleware in the Spring Boot application. Remove `permitAll()` from `ResourceServerConfig.java` and all `@PreAuthorize` annotations. This is a prerequisite for agent integration — agents must authenticate to access APIs. |
| **Evidence** | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll), `src/main/java/com/monoToMicro/Application.java` (OPTIONS workaround), all controllers (@PreAuthorize("permitAll()")), `build.gradle` (security dependencies present but unused) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, Okta, OIDC, SAML, or SSO configuration. OAuth2 dependencies are present but not configured with any identity provider. The application manages its own user authentication via `UserController.login()` — a simple email lookup (`userService.getByEmail()`) with no password validation, no token issuance, and no session management. User registration in `UserController.createUser()` stores only email, first name, and last name — no password field exists. |
| **Gap** | Application has no real authentication. The "login" endpoint merely looks up a user by email with no password check. No integration with any identity provider. |
| **Recommendation** | Integrate Amazon Cognito (user pool) as the centralized identity provider. Use Cognito hosted UI for user registration and login. Configure API Gateway authorizer with Cognito JWT tokens. Remove the custom login endpoint — delegate authentication entirely to Cognito. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/UserController.java` (login method — email lookup only), `database/create_tables.sql` (unicorn_user table has no password column), absence of IdP configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Database credentials are hardcoded in plaintext in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. These credentials are committed to version control. The database endpoint uses an environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) but the username and password are plaintext in the configuration file. No AWS Secrets Manager, HashiCorp Vault, Parameter Store, or any secrets management system is used. |
| **Gap** | **Critical security vulnerability.** Database credentials are hardcoded in a file committed to version control. No secrets rotation, no access audit trail, no encryption of credentials at rest. |
| **Recommendation** | **Immediate action required.** Rotate the compromised credentials. Migrate secrets to AWS Secrets Manager with automated rotation via Terraform. Reference secrets in the application using the AWS Secrets Manager Spring Boot integration or environment variable injection from EKS Secrets Store CSI Driver. Remove hardcoded credentials from `application.properties`. |
| **Evidence** | `src/main/resources/application.properties` (hardcoded username=MonoToMicroUser, password=MonoToMicroPassword) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No evidence of patching strategy. No SSM Patch Manager, AWS Inspector, Snyk, or vulnerability scanning. No hardened AMI references (CIS, Bottlerocket). No EC2 Image Builder. The application uses outdated dependencies: Spring Boot 2.1.6 (2019), AWS SDK v1.11.567 (2019), mysql-connector-java 8.0.11 (2018), MyBatis 3.2.2 (2013) — all with known CVEs. `spring-security-jwt:1.0.9` and `spring-cloud-starter-oauth2:2.0.1` are also outdated. |
| **Gap** | No patching automation, no vulnerability scanning, no hardened base images. Multiple outdated dependencies with known CVEs. |
| **Recommendation** | When containerizing on EKS (preferred), use Bottlerocket OS for worker nodes (CIS-hardened, minimal attack surface). Enable Amazon ECR image scanning. Add dependency vulnerability scanning (Snyk, Trivy) to the CI/CD pipeline. Upgrade all outdated dependencies during the Java 17 / Spring Boot 3.x migration. |
| **Evidence** | `build.gradle` (outdated dependency versions), absence of any IaC, security scanning, or hardening configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning in any CI/CD pipeline — because no CI/CD pipeline exists. No SonarQube, Semgrep, CodeGuru Reviewer, Dependabot, `npm audit`, `pip-audit`, or Snyk configuration. No `.snyk` policy files. No ECR image scanning configuration. No SAST, DAST, or dependency scanning of any kind. |
| **Gap** | No automated security validation. Vulnerabilities in dependencies and application code reach production undetected. |
| **Recommendation** | When implementing CI/CD (Move to Modern DevOps pathway), integrate: (1) SAST — SonarQube or Amazon CodeGuru Reviewer, (2) Dependency scanning — Snyk or OWASP Dependency-Check in Gradle, (3) Container scanning — Amazon ECR image scanning or Trivy, (4) Security gates — block deployment on critical findings. Add Dependabot or Renovate for automated dependency updates. |
| **Evidence** | Absence of CI/CD pipeline, `.snyk` files, SonarQube config, Dependabot config, or any security scanning configuration |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry SDK, X-Ray agent, or tracing library in `build.gradle` dependencies. No trace ID propagation headers (`traceparent`, `X-Amzn-Trace-Id`). Spring Boot Actuator (`spring-boot-starter-actuator`) is present and provides basic health/info/metrics endpoints but no distributed tracing. No tracing configuration files. |
| **Gap** | No distributed tracing — debugging failures requires manual log correlation. No request flow visibility. |
| **Recommendation** | Add OpenTelemetry Java auto-instrumentation agent to the container image. Configure OTLP exporter to AWS X-Ray via the ADOT (AWS Distro for OpenTelemetry) collector on EKS. This provides trace correlation across services during and after decomposition. |
| **Evidence** | `build.gradle` (spring-boot-starter-actuator present, no tracing dependencies), absence of tracing configuration |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs defined. No CloudWatch alarms on latency (p99/p95), error rates, or availability. No error budget tracking. No SLO definition files. No monitoring configuration of any kind in the repository. The `HealthController` provides basic `/health/ishealthy` and `/health/dbping` endpoints but these are not connected to any monitoring or alerting system. |
| **Gap** | No formal SLOs — no definition of acceptable service levels, no measurement of whether the system meets user expectations. |
| **Recommendation** | Define SLOs for critical user journeys: catalog browsing (p99 latency < 500ms), basket operations (availability > 99.9%), user login (p99 latency < 200ms). Implement SLO monitoring with CloudWatch Synthetics and Application Signals on EKS. Configure error budget alerts. |
| **Evidence** | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (basic health endpoints, not connected to monitoring), absence of monitoring configuration |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. No `cloudwatch.put_metric_data` calls or custom metric annotations. Spring Boot Actuator provides default JVM and HTTP metrics only (heap usage, thread count, request counts) — no business-specific metrics like "baskets created," "unicorns added to basket," or "user registrations." No custom dashboards. |
| **Gap** | Infrastructure metrics only. No business outcome metrics to drive informed modernization decisions or measure business value. |
| **Recommendation** | Add Micrometer custom metrics for business events: `basket.items.added`, `basket.items.removed`, `user.registrations`, `user.logins`, `catalog.views`. Publish to CloudWatch via the Micrometer CloudWatch registry. Create business dashboards. |
| **Evidence** | `build.gradle` (spring-boot-starter-actuator — default metrics only), absence of custom metric publishing in source code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured. No CloudWatch alarms (static threshold or anomaly detection). No PagerDuty, OpsGenie, or SNS alerting integration. No composite alarms. No error rate or latency monitoring. The application silently swallows exceptions via `e.printStackTrace()` in all repository implementations with no alerting on failure conditions. |
| **Gap** | No alerting at all. Production failures go unnoticed until users report them. No anomaly detection for gradual degradation. |
| **Recommendation** | Configure CloudWatch alarms for EKS pod health, Aurora MySQL performance, and API Gateway error rates. Enable CloudWatch anomaly detection on p99 latency and 5xx error rates. Integrate with SNS for alert notifications. |
| **Evidence** | Repository implementation files (e.printStackTrace() — silent exception handling), absence of monitoring/alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy. No CI/CD pipeline exists. No CodeDeploy, Helm canary, ArgoCD Rollouts, Lambda traffic shifting, ALB weighted target groups, or feature flags. Deployments appear to be direct-to-production with no staged rollout, no health check validation, and no automated rollback. |
| **Gap** | Direct-to-production deployment with no staged rollout. Every deployment is a full risk event with no ability to catch regressions before they affect all users. |
| **Recommendation** | Implement progressive delivery with ArgoCD Rollouts on EKS (GitOps preferred per user preferences). Configure canary deployments with automated analysis gates. For initial setup, use Kubernetes rolling updates with readiness/liveness probes as a baseline. |
| **Evidence** | Absence of CI/CD pipeline, deployment configuration, ArgoCD/Helm/Flux definitions, or feature flag configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No integration tests found. `build.gradle` declares `spring-boot-starter-test` as a `testImplementation` dependency, but no test files exist in `src/test/`. No integration test directories, no API test suites (Postman/Newman), no contract tests, no end-to-end test pipelines. Zero test coverage. |
| **Gap** | No automated tests of any kind. No safety net for code changes, deployments, or service extraction. Regression risk is unmanaged. |
| **Recommendation** | Before any decomposition, add: (1) JUnit integration tests for basket operations (add/remove/get), user creation/login, and catalog listing, (2) Spring Boot `@WebMvcTest` for controller-level API tests, (3) Testcontainers with MySQL for repository-level integration tests. Run all tests in the CI/CD pipeline. |
| **Evidence** | `build.gradle` (spring-boot-starter-test declared), absence of any test files in `src/test/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, SSM Automation documents, or self-healing patterns. No incident response automation. No Lambda-based remediation. No Step Functions for incident workflows. Exception handling in the codebase is limited to `try/catch` blocks with `e.printStackTrace()` — no structured error handling, no incident escalation, no automated recovery. |
| **Gap** | Incident response is entirely ad hoc. No runbooks, no automation, no self-healing. Mean-time-to-recovery depends entirely on manual intervention. |
| **Recommendation** | Create runbooks for common incident scenarios (database connectivity failure, high latency, out-of-memory). Implement Kubernetes liveness and readiness probes for automatic pod restart on EKS. Use SSM Automation for infrastructure-level remediation. |
| **Evidence** | Absence of runbook files, SSM documents, or incident automation; repository implementations use e.printStackTrace() with no structured error handling |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No per-service dashboards, no alarms with named owners, no CODEOWNERS file referencing observability assets. No team attribution on any monitoring or alerting resources (none exist). No SLO definitions with team ownership. |
| **Gap** | No observability ownership. No dashboards, no alarms, no monitoring assets exist to own. |
| **Recommendation** | Establish observability ownership as part of the decomposition process. Each extracted service team should own their dashboards, alarms, and SLOs. Add a CODEOWNERS file that includes observability configuration paths. Define on-call ownership for each service. |
| **Evidence** | Absence of CODEOWNERS file, dashboards, alarms, or any observability assets |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging found. No IaC exists to apply tags. No `default_tags` in Terraform provider (no Terraform exists). No `tags` on any resources. No Config rules for tag enforcement. No tag policies in AWS Organizations. |
| **Gap** | No resource tagging. Cannot track costs per workload, identify resource ownership during incidents, or enforce budget controls. |
| **Recommendation** | Define a tagging standard in Terraform `default_tags`: `Environment`, `Service`, `Team`, `CostCenter`, `Project`. Apply to all resources. Enforce with AWS Config `required-tags` rule. Enable cost allocation tags in AWS Billing. |
| **Evidence** | Absence of any IaC or tagging configuration |

## Learning Materials

The following learning resources are mapped to the 5 triggered pathways:

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
| `build.gradle` | INF-Q1, INF-Q2, INF-Q4, INF-Q11, APP-Q1, APP-Q2, APP-Q3, APP-Q4, DATA-Q1, DATA-Q3, SEC-Q3, SEC-Q6, OPS-Q1, OPS-Q3, OPS-Q6 | Primary dependency manifest — Spring Boot 2.1.6, Java 8, MySQL connector, AWS SDK v1, security dependencies, no messaging/tracing/AI deps |
| `src/main/resources/application.properties` | INF-Q2, INF-Q5, INF-Q6, APP-Q6, SEC-Q5 | Application configuration — JDBC connection string, hardcoded credentials (MonoToMicroUser/MonoToMicroPassword), server port 8080 |
| `database/create_tables.sql` | INF-Q2, DATA-Q1, DATA-Q3, DATA-Q4 | MySQL schema — 3 tables (unicorns, unicorns_basket, unicorn_user), InnoDB engine, UTF8MB4, seed data, no stored procedures |
| `src/main/java/com/monoToMicro/Application.java` | APP-Q2, SEC-Q3 | Spring Boot entry point — single @SpringBootApplication, CORS config, OPTIONS security bypass |
| `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | INF-Q1, INF-Q7, INF-Q9, SEC-Q1, OPS-Q2 | EC2MetadataUtils usage confirms raw EC2 deployment, System.out.println logging, health endpoints |
| `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | APP-Q2, APP-Q3, APP-Q5 | Basket CRUD — synchronous ResponseEntity returns, @PreAuthorize("permitAll()"), unversioned /unicorns/basket path |
| `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | APP-Q2, APP-Q3, APP-Q5 | Catalog listing — synchronous GET /unicorns, no versioning |
| `src/main/java/com/monoToMicro/rest/controller/UserController.java` | APP-Q2, APP-Q5, SEC-Q3, SEC-Q4 | User CRUD and login — email-only lookup with no password validation, @PreAuthorize("permitAll()") |
| `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | APP-Q4 | Synchronous data replication — potentially long-running getAllBaskets() with no async handling |
| `src/main/java/com/monoToMicro/rest/controller/CoreController.java` | APP-Q2 | Shared controller base class — inheritance coupling across all controllers |
| `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | INF-Q5, INF-Q6, SEC-Q3 | OAuth2 resource server — anyRequest().permitAll(), security effectively disabled |
| `src/main/java/com/monoToMicro/config/MVCConfig.java` | INF-Q6 | MVC configuration — CORS on all paths, all HTTP methods allowed |
| `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | DATA-Q2 | MyBatis configuration — single SqlSessionFactory, single DataSource, all mapper beans wired |
| `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | INF-Q3, APP-Q2, APP-Q3 | Unicorn + Basket service — synchronous method calls, mixed catalog and basket responsibilities |
| `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | INF-Q3, APP-Q2 | User service — synchronous create and getByEmail, UUID generation in application layer |
| `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | DATA-Q2 | Repository pattern implementation — delegates to UnicornMapper, try/catch with printStackTrace |
| `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | DATA-Q2 | Repository pattern implementation — delegates to UserMapper, synchronized create method |
| `src/main/java/com/monoToMicro/core/repository/HealthRepositoryImpl.java` | DATA-Q2 | Repository pattern implementation — delegates to HealthMapper for DB connectivity check |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | APP-Q2, DATA-Q2, DATA-Q4 | MyBatis SQL — standard SELECT/INSERT/DELETE, JOIN between unicorns and unicorns_basket tables |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | DATA-Q2, DATA-Q4 | MyBatis SQL — standard INSERT/SELECT for user operations |
| `src/main/resources/com/monoToMicro/core/repository/mappers/HealthMapper.xml` | DATA-Q2, DATA-Q4 | MyBatis SQL — SELECT COUNT(*) for database health check |
| `src/main/java/com/monoToMicro/core/model/CoreModel.java` | APP-Q2 | Shared model base class — id, dates, audit fields; extended by Unicorn and User (inheritance coupling) |
| `README.md` | Quick Agent Wins | Minimal documentation — links to external workshop URL |
| `gradle/wrapper/gradle-wrapper.properties` | APP-Q1 | Gradle 7.4 wrapper distribution |
