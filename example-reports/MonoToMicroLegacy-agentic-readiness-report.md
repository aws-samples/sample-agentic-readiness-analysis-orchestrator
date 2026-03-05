# Agentic Readiness Assessment Report
**Target**: MonoToMicroLegacy (Java Spring Boot 2.1.6 Monolith — Unicorn Shop)
**Date**: 2026-03-05
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment

---

## Table of Contents

1. Executive Summary
2. Top Priorities (Critical Gaps)
3. Readiness Roadmap
   - Microservices Decomposition Strategy
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Agent Enablement (Months 3–6)
4. Recommended Self-Paced Learning Materials
5. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
6. Appendix: Evidence Index

---

## Executive Summary

The MonoToMicroLegacy repository is a Java 8 Spring Boot 2.1.6 monolith ("Unicorn Shop") running directly on EC2 with no Infrastructure as Code, no CI/CD pipeline, no containerization, no API documentation, no tests, and hardcoded database credentials. It is significantly below agentic readiness across all five evaluation categories. The strongest area is Data Foundations, where the application benefits from a single MySQL data source, clean repository pattern via MyBatis, and no stored procedures — providing a low-friction migration path to managed databases. The most critical gaps are the complete absence of IaC, CI/CD, container definitions, observability, and the fact that all API endpoints are unauthenticated despite Spring Security OAuth2 dependencies being present. Substantial foundational modernization is required before any agentic workloads can be considered.

### Overall Score: 1.30 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 1.0 / 4.0 | ❌ |
| Application Architecture | 1.38 / 4.0 | ❌ |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.1 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

**1. No Infrastructure as Code — All infrastructure is manually provisioned (INF-Q5: 1/4)**
The repository contains zero IaC files — no Terraform, CloudFormation, CDK, or Helm charts. This means infrastructure cannot be versioned, audited, or reproduced reliably. Agentic workloads require predictable, repeatable environments for safe deployment and scaling. **First step**: Create a Terraform or CDK project defining the VPC, compute (ECS/Fargate), RDS MySQL instance, and security groups currently in use.

**2. Hardcoded database credentials in source code (SEC-Q1: 1/4)**
`application.properties` contains plaintext credentials (`MonoToMicroUser` / `MonoToMicroPassword`). This is a critical security vulnerability — credentials are committed to version control and visible to anyone with repository access. Agentic systems must have secrets managed externally since agents may need scoped, rotatable credentials. **First step**: Move database credentials to AWS Secrets Manager and update the application to retrieve them at startup using the AWS SDK or Spring Cloud AWS.

**3. No CI/CD pipeline — deployments are manual and unreproducible (INF-Q6: 1/4)**
No Jenkinsfile, GitHub Actions workflows, buildspec.yml, or any pipeline definition exists. Without automated CI/CD, there is no gating for code quality, security scanning, or automated testing — all essential for safe agentic deployments where agents may trigger code changes or need continuous evaluation. **First step**: Create a `buildspec.yml` or `.github/workflows/build.yml` with build, test, and deploy stages targeting the current EC2 environment.

**4. No containerization — application runs as raw JAR on EC2 (INF-Q1: 1/4)**
`HealthController.java` calls `EC2MetadataUtils.getInstanceInfo()` confirming direct EC2 deployment. `build.gradle` uses `bootJar { launchScript() }` for direct execution. Without containerization, the application cannot be deployed to ECS/EKS/Fargate, blocking auto-scaling, service mesh, and sidecar patterns required for agent observability. **First step**: Create a Dockerfile using `openjdk:8-jre-slim` as base image with the Spring Boot fat JAR, then validate local build and run.

**5. All API endpoints are unauthenticated (SEC-Q9: 1/4)**
`ResourceServerConfig.java` sets `authorizeRequests().anyRequest().permitAll()` and `Application.java` ignores all OPTIONS requests from security. Despite OAuth2/JWT dependencies in `build.gradle`, no authentication is enforced. Agentic systems must authenticate every request to enforce identity propagation, audit trails, and tool-level authorization. **First step**: Configure the existing Spring Security OAuth2 framework with a Cognito User Pool or external IdP, and replace `permitAll()` with role-based access on each endpoint.

---

## Readiness Roadmap

Cross-dependencies between phases are noted explicitly below. Containerization (Phase 1) is a prerequisite for ECS/EKS deployment (Phase 2). IaC (Phase 2) is a prerequisite for API Gateway and auto-scaling (Phase 2/3). CI/CD (Phase 1) must exist before automated testing and canary deployments (Phase 2/3).

### Microservices Decomposition Strategy

APP-Q4 scored 2/4: The application is a monolith with identifiable modules. The code exhibits reasonable separation — controllers (`rest/controller/`), services (`core/services/`), repositories (`core/repository/`), and models (`core/model/`) follow interface-based patterns with no observed circular dependencies. The Unicorn domain (product catalog + basket) and User domain share the same MySQL database (`unishop` schema) with three tables (`unicorns`, `unicorns_basket`, `unicorn_user`). The `unicorns_basket` table creates a cross-domain data dependency (user UUID → basket → unicorn UUID).

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure (containerize, create IaC, set up CI/CD) while incrementally extracting services
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract the **User service** first — it has the clearest domain boundary (`/user` endpoints, `UserController`, `UserService`, `UserRepository`, `unicorn_user` table), minimal shared state (only `uuid` is referenced in `unicorns_basket`), and no dependency on the Unicorn domain. The Basket service is the second candidate, but requires resolving the cross-domain join in `UnicornMapper.xml` (`getUnicornBasket` joins `unicorns` and `unicorns_basket`).
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently, containerize the monolith as-is first, then extract services opportunistically
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Containerize the entire monolith first (it already has clean interfaces via `UnicornService`, `UserService`), deploy to ECS, then extract modules as independent services when business need arises
- **When to Use**: When infrastructure modernization is the immediate priority and decomposition can be deferred

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

**Pattern Recommendations Based on Your Architecture:**

- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (hostname, path, or header-based). Since no service discovery exists (APP-Q12: 1/4), API Gateway provides routing, throttling, and auth without requiring service mesh infrastructure upfront.

- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extracting the Basket service. Without idempotency at the API level (APP-Q7: 2/4, only database-level `INSERT IGNORE`), service extraction risks data inconsistency.

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition. Repository methods currently swallow exceptions and return `null` (e.g., `UnicornRepositoryImpl.java`); microservices amplify failure modes so resilience patterns must be in place first.

### Phase 1 — Quick Wins (Days 1–30)

1. **Remove hardcoded credentials** from `application.properties`. Move `MonoToMicroUser`/`MonoToMicroPassword` to AWS Secrets Manager. Update application to fetch credentials via Spring Cloud AWS or AWS SDK at startup. *(Prerequisite for Phase 2 security hardening)*
2. **Create a Dockerfile** for the Spring Boot application. Use the commented-out docker task in `build.gradle` as a starting point. Validate the container runs locally with `docker build` and `docker run`. *(Prerequisite for Phase 2 ECS deployment)*
3. **Add structured logging**. Replace `System.out.println` (in `HealthController.java`) and `e.printStackTrace()` (in `UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`) with SLF4J + Logback JSON encoder. Add correlation IDs to all log output.
4. **Generate an OpenAPI spec** for the existing REST endpoints (`/unicorns`, `/unicorns/basket/{userUuid}`, `/user`, `/user/login`, `/health/ping`, `/health/ishealthy`, `/health/dbping`, `/data`). Use Springdoc OpenAPI to auto-generate from existing `@RequestMapping` annotations.
5. **Conduct domain modeling workshop** (EventStorming) to identify bounded contexts. Map the Unicorn (catalog), Basket (shopping cart), and User (identity) domains. Document current data coupling (the `unicorns_basket` table joins across Unicorn and User domains via UUIDs).

### Phase 2 — Foundation (Months 1–3)

1. **Create IaC** (Terraform or CDK) defining: VPC with public/private subnets, RDS MySQL instance (to confirm managed database), ECS Fargate cluster, ALB with target groups, security groups with least-privilege rules, Secrets Manager for credentials.
2. **Set up CI/CD pipeline** (CodePipeline + CodeBuild, or GitHub Actions): build JAR, run tests, build Docker image, push to ECR, deploy to ECS. Add automated test stage (requires writing initial integration tests first).
3. **Deploy containerized monolith to ECS Fargate**. Remove `EC2MetadataUtils` dependency from `HealthController.java` (replace with ECS task metadata endpoint). Configure ECS Service auto-scaling.
4. **Add API Gateway** in front of ALB. Configure throttling, request validation, and authentication (Cognito authorizer). Enable `@PreAuthorize` enforcement on all endpoints — replace `permitAll()` in `ResourceServerConfig.java`.
5. **Migrate to confirmed managed RDS MySQL**. Pin engine version in IaC. Enable automated backups, Multi-AZ, and encryption at rest with KMS.
6. **Add observability stack**: X-Ray or OpenTelemetry for distributed tracing, CloudWatch alarms for error rates and latency, structured log aggregation via CloudWatch Logs Insights.
7. **If Option B (Parallel Track)**: Extract User service using Strangler Fig pattern. Route `/user/*` traffic through API Gateway to the new User microservice. Implement service-to-service authentication. Keep the monolith serving Unicorn and Basket endpoints.

### Phase 3 — Agent Enablement (Months 3–6)

1. **Implement API versioning** (`/v1/unicorns`, `/v1/user`) to enable backward-compatible agent tool definitions.
2. **Add resilience patterns**: Integrate Resilience4j for circuit breakers, retries with exponential backoff, and timeouts on all external calls. Replace exception-swallowing patterns in repository classes.
3. **Implement async messaging**: Introduce SQS or EventBridge for basket operations (add/remove) to decouple write operations and support eventual consistency as services are extracted.
4. **Integrate AI/agent framework**: Add Amazon Bedrock SDK, define agent tools per API endpoint using the OpenAPI specs from Phase 1. Evaluate Strands Agents SDK or LangChain for Java.
5. **Set up agent evaluation pipeline**: Create golden datasets for API responses, implement automated evals with scoring, set up SLOs for agent task success rates.
6. **Continue service extraction** based on business priorities. Extract Basket service (resolves the cross-domain join in `UnicornMapper.xml`). Implement domain-specific agent tools per service boundary.
7. **Establish observability governance**: Define SLOs per service and per agent workflow, assign ownership, implement anomaly detection for agent behavioral baselines.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - Relevant because the application currently exposes REST endpoints directly on port 8080 with no API Gateway (INF-Q7: 1/4)
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
  - Directly applicable: this is a Java monolith that needs containerization and ECS migration
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7
  - Demonstrates the decomposition approach recommended in this assessment's roadmap

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
  - Priority learning path — containerizing the Spring Boot monolith and deploying to ECS Fargate is Phase 2 of the roadmap
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
  - Foundation for creating the Dockerfile needed in Phase 1
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
  - The application uses MySQL via JDBC (application.properties) with no confirmed managed database IaC. Migration to RDS/Aurora is Phase 2.
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
  - Relevant for future Aurora migration to gain auto-scaling and serverless capabilities

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Critical path — no CI/CD, no deployment strategy, no observability exist today (INF-Q6: 1/4, OPS-Q9: 1/4)
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Directly maps to Phase 2 CI/CD + ECS deployment goals
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - Relevant for creating the IaC foundation (INF-Q5: 1/4)
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
  - Specifically for Java/Spring Boot observability — directly applicable to this codebase
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for Phase 3 agent framework integration
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Key learning for understanding how agentic systems work and what they require from the underlying platform
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on lab for building the type of agent this assessment is preparing for
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Relevant for Phase 3 RAG implementation (DATA-Q3: 1/4)
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Addresses OPS-Q8 anomaly detection gap

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 1/4 ❌
- **Finding**: `HealthController.java` calls `EC2MetadataUtils.getInstanceInfo()` (line imports `com.amazonaws.util.EC2MetadataUtils`), confirming the application runs on raw EC2 instances. `build.gradle` configures `bootJar { launchScript() }` enabling the JAR to run as a Linux init.d service directly on EC2. No Dockerfile, ECS task definition, EKS manifest, or Lambda function found anywhere in the repository. A commented-out `docker` task exists in `build.gradle` but was never implemented.
- **Gap**: No container orchestration (ECS/EKS) or serverless (Lambda/Fargate) compute. Application is tightly coupled to EC2 via `EC2MetadataUtils`.
- **Recommendation**: Create a Dockerfile, remove `EC2MetadataUtils` dependency, and deploy to ECS Fargate.

#### INF-Q2: Databases
- **Score**: 1/4 ❌
- **Finding**: `application.properties` defines `spring.datasource.url: jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop`. The database endpoint is externalized via environment variable `MONO_TO_MICRO_DB_ENDPOINT`, but no IaC exists to confirm whether this is RDS, Aurora, or a self-managed MySQL instance on EC2. `build.gradle` includes `mysql:mysql-connector-java:8.0.11`. `database/create_tables.sql` defines the `unishop` schema with 3 tables using InnoDB engine. Without IaC evidence of a managed database resource, the score defaults to 1.
- **Gap**: No IaC defining managed database. Cannot confirm RDS/Aurora. Database could be self-managed.
- **Recommendation**: Define RDS MySQL (or Aurora MySQL) in Terraform/CDK with Multi-AZ, automated backups, and encryption at rest.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow engine references found. All business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` follows simple synchronous CRUD patterns. Event classes in `core/events/` (e.g., `ReadUnicornsEvent.java`, `UnicornsReadEvent.java`) are plain DTOs passed between controller and service layers — not workflow definitions.
- **Gap**: No workflow orchestration capability exists.
- **Recommendation**: Evaluate AWS Step Functions for future multi-step agent workflows (e.g., order processing, user registration with verification).

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, Kafka, or RabbitMQ references in `build.gradle` dependencies or Java source code. All inter-component communication is synchronous method calls within the monolith. No messaging SDK imports found.
- **Gap**: No async messaging infrastructure. All communication is synchronous.
- **Recommendation**: Introduce SQS or EventBridge for basket operations (add/remove unicorn) as a first async pattern.

#### INF-Q5: Infrastructure as Code
- **Score**: 1/4 ❌
- **Finding**: Zero IaC files found in the entire repository. No `.tf` files, no CloudFormation templates (`template.yaml`, `template.json`), no CDK stacks, no Helm charts, no Kustomize files. The repository contains only application source code, configuration, and database DDL.
- **Gap**: 0% of infrastructure is defined as code. All infrastructure is presumably manually provisioned.
- **Recommendation**: Create a Terraform or CDK project covering VPC, compute (ECS), database (RDS), load balancer (ALB), and security groups.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/` directory, no `Jenkinsfile`, no `buildspec.yml`, no `.gitlab-ci.yml`, no CodePipeline definitions in IaC. The `build.gradle` defines only build and package tasks — no deployment automation.
- **Gap**: No automated build, test, or deployment pipeline exists.
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or CodePipeline + CodeBuild) with build, test, Docker image build, ECR push, and ECS deploy stages.

#### INF-Q7: API Entry Point
- **Score**: 1/4 ❌
- **Finding**: `application.properties` sets `server.port=8080`. REST endpoints in `UnicornController.java`, `BasketController.java`, `UserController.java`, `HealthController.java`, and `DataReplicationController.java` are exposed directly on this port with no API Gateway, ALB, or CloudFront in front. No `aws_api_gateway_*`, `aws_lb_*`, or CDN IaC resources found.
- **Gap**: No API Gateway or load balancer. Services are directly exposed.
- **Recommendation**: Deploy an API Gateway (HTTP API or REST API) in front of the application with throttling, authentication (Cognito authorizer), and request validation.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or streaming service references in `build.gradle` or source code. No stream consumer patterns or event-driven data processing.
- **Gap**: No real-time streaming capability.
- **Recommendation**: Not immediately required for this application. Consider Kinesis Data Streams or EventBridge Pipes when implementing event-driven patterns in Phase 3.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions exist (no IaC). `MVCConfig.java` configures wide-open CORS: `registry.addMapping("/**").allowedMethods("HEAD", "GET", "PUT", "POST", "DELETE", "PATCH", "OPTIONS")`. Application.java CORS also allows `"GET", "POST", "OPTIONS"` on `/**`. No network segmentation is defined.
- **Gap**: No network security controls defined in code. CORS is permissive.
- **Recommendation**: Define VPC with private subnets for application and database tiers. Restrict security groups to minimum required ports. Constrain CORS origins.

#### INF-Q10: Auto-scaling
- **Score**: 1/4 ❌
- **Finding**: No ASG, ECS Service auto-scaling, or Lambda concurrency configurations found. No `aws_autoscaling_*` or `aws_appautoscaling_*` resources. Application runs as a single instance on EC2 with no scaling capability.
- **Gap**: No auto-scaling at any level.
- **Recommendation**: After containerizing to ECS, configure Service auto-scaling with target tracking on CPU/memory utilization.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: Java 8 (`sourceCompatibility = 1.8` in `build.gradle`). Spring Boot 2.1.6.RELEASE (2019 vintage). Java has a growing agent ecosystem via Spring AI and LangChain4j, but Python and TypeScript remain significantly ahead in agent framework maturity, tooling, and community support.
- **Gap**: Java 8 is past end-of-life. Spring Boot 2.1.x is no longer maintained. Agent framework ecosystem for Java is maturing but not yet as rich as Python/TypeScript.
- **Recommendation**: Upgrade to Java 17+ and Spring Boot 3.x to access Spring AI and modern agent framework integrations. This is a prerequisite for many agentic capabilities.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No `openapi.yaml`, `swagger.json`, or API documentation files found. No Springdoc (`springdoc-openapi-ui`) or SpringFox (`springfox-swagger2`) dependencies in `build.gradle`. No `@ApiOperation`, `@OpenAPIDefinition`, or `@Schema` annotations in controller classes. Endpoints are defined via `@RequestMapping` annotations only.
- **Gap**: Zero API documentation. Agents cannot discover or validate API contracts.
- **Recommendation**: Add Springdoc OpenAPI dependency to auto-generate OpenAPI 3.0 specs from existing `@RequestMapping` annotations. This is critical — agents need machine-readable API specifications to function as tools.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All 6 controllers (`UnicornController`, `BasketController`, `UserController`, `HealthController`, `DataReplicationController`, `CoreController`) use synchronous HTTP request/response exclusively. No message publishing, event handlers, queue consumers, or async patterns found. All service methods in `UnicornServiceImpl.java` and `UserServiceImpl.java` are synchronous calls to repository methods.
- **Gap**: 0% async communication. All operations are synchronous.
- **Recommendation**: Introduce SQS for basket write operations (add/remove) as a first async pattern. This enables decoupling and eventual consistency needed for service extraction.

#### APP-Q4: Monolith vs Microservices
- **Score**: 2/4 🟠
- **Finding**: Single deployable unit — `bootJar` task in `build.gradle` produces one fat JAR. All domains (Unicorn catalog, Basket, User, Health) share one Spring Boot application context and one MySQL database (`unishop` schema with 3 tables). However, the code exhibits reasonable modularity: interface-based service layer (`UnicornService`/`UnicornServiceImpl`, `UserService`/`UserServiceImpl`), repository pattern with mapper abstraction (`UnicornRepository`→`UnicornRepositoryImpl`→`UnicornMapper`), and controller-per-domain. No circular dependencies observed between Unicorn and User domains. The `unicorns_basket` table creates a cross-domain data dependency (user UUID + unicorn UUID).
- **Gap**: Single deployment unit with shared database. Cross-domain data coupling in `unicorns_basket` table.
- **Recommendation**: See Microservices Decomposition Strategy section above. Extract User service first (clearest boundary), then Basket service.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: Controllers return `ResponseEntity<>` objects with Java POJOs serialized to JSON via Jackson (included transitively by `spring-boot-starter-web`). `Unicorn.java` and `User.java` use `@JsonInclude(JsonInclude.Include.NON_NULL)`. `CoreModel.java` uses `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` and `@JsonIgnore` on internal fields (`id`, `creationDate`, etc.). All API responses are structured JSON.
- **Gap**: No standardized error response format. Controllers return raw `HttpStatus.BAD_REQUEST` without error details. `HealthController.java` returns plain `String` responses instead of JSON for health endpoints.
- **Recommendation**: Implement a standardized JSON error response format (`{ "error": "...", "code": "...", "timestamp": "..." }`) using `@ControllerAdvice`. Convert health endpoint responses to JSON.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration. Business logic in `UnicornServiceImpl.java` and `UserServiceImpl.java` consists of straightforward CRUD operations — get/add/remove unicorns, create/find users. Event classes in `core/events/` (17 classes including `ReadUnicornsEvent`, `UnicornsReadEvent`, `CreateUserEvent`, etc.) are simple DTOs carrying data between controller and service layers — they are not part of a workflow engine or event-driven architecture.
- **Gap**: No dedicated workflow orchestration. All business logic is inline.
- **Recommendation**: For current CRUD patterns, workflow orchestration is not immediately critical. Introduce Step Functions when implementing multi-step agent workflows in Phase 3.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: `INSERT IGNORE` is used in `UnicornMapper.xml` (`addUnicornToBasket`) and `UserMapper.xml` (`create`), providing database-level idempotency that prevents duplicate basket entries and duplicate user registrations. The `unicorns_basket` table has a `UNIQUE` constraint on `(uuid, unicornUuid)` and `unicorn_user` has a `UNIQUE` constraint on `(email)` per `create_tables.sql`. However, no API-level idempotency keys (`Idempotency-Key` header, idempotency tokens) are implemented.
- **Gap**: Database-level idempotency only. No API-level idempotency keys for safe retries by agent clients.
- **Recommendation**: Add idempotency key support at the API layer for all write operations (POST to `/unicorns/basket`, POST to `/user`). Use DynamoDB or a cache-backed idempotency store.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: `ResourceServerConfig.java` permits all requests (`authorizeRequests().anyRequest().permitAll()`). No rate limiting middleware (no `spring-boot-starter-rate-limiter`, no `bucket4j`, no custom filter). No API Gateway throttling (no API Gateway exists). No WAF rules.
- **Gap**: Zero rate limiting at any layer. APIs are completely unthrottled.
- **Recommendation**: Add API Gateway with throttling configuration as first line of defense. Optionally add Bucket4j or Spring Cloud Gateway rate limiting at the application layer.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No resilience libraries (Resilience4j, Hystrix, Polly) in `build.gradle`. Repository methods in `UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, and `HealthRepositoryImpl.java` catch all exceptions with `e.printStackTrace()` and return `null` or `false` — swallowing errors silently. No retry logic, no circuit breakers, no timeout configurations, no exponential backoff.
- **Gap**: No resilience patterns. Exceptions are silently swallowed. No retry, circuit breaker, or timeout.
- **Recommendation**: Add Resilience4j. Implement circuit breakers on database calls, retries with exponential backoff for transient failures, and explicit timeouts. Replace `e.printStackTrace()` with proper logging and error propagation.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All operations are synchronous database queries — `getUnicorns()`, `addUnicornToBasket()`, `create()` user, `getByEmail()`. No background job frameworks (Celery, Bull, SQS workers), no async invocation patterns, no job status APIs, no Step Functions. The `DataReplicationController.java` calls `unicornService.getAllBaskets()` synchronously.
- **Gap**: No mechanism for handling long-running operations asynchronously. While current operations are quick, no infrastructure exists for future async needs.
- **Recommendation**: Introduce async processing via SQS workers or Step Functions for any operation that could exceed 30 seconds as the application grows (e.g., data replication in `DataReplicationController`).

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: REST endpoints use unversioned URLs: `/unicorns`, `/unicorns/basket`, `/unicorns/basket/{userUuid}`, `/user`, `/user/login`, `/health/ping`, `/health/ishealthy`, `/health/dbping`, `/data`. No `/v1/` prefix, no `Accept-Version` header handling, no versioning annotations, no changelog files.
- **Gap**: No API versioning strategy. Breaking changes will break agent tool integrations.
- **Recommendation**: Implement URL path versioning (`/v1/unicorns`, `/v1/user`) before agent tools are built against these APIs.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith — no service-to-service communication exists. Database endpoint is externalized via `MONO_TO_MICRO_DB_ENDPOINT` environment variable in `application.properties`, which is a positive sign for configuration externalization. No AWS Service Discovery, App Mesh, Istio, Consul, or API catalog found.
- **Gap**: No service discovery mechanism. Will be needed when services are extracted.
- **Recommendation**: Use API Gateway as the initial service catalog and routing layer during decomposition. Add AWS Cloud Map or Service Discovery when multiple services are deployed.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` includes `com.amazonaws:aws-java-sdk:1.11.567` but this is AWS SDK v1 (2019) used only for `EC2MetadataUtils` in `HealthController.java`. No Bedrock, LangChain4j, Spring AI, LangGraph, CrewAI, Strands Agents, OpenAI, Anthropic, or MCP SDK imports found. No AI/ML-related code or configuration.
- **Gap**: No AI/agent framework integration. AWS SDK is v1 (2019), not v2 — lacking Bedrock support entirely.
- **Recommendation**: Upgrade to AWS SDK v2, add Amazon Bedrock SDK. Evaluate Strands Agents SDK or Spring AI for Java-based agent development. Define agent tools mapped to existing REST API endpoints.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No OpenSearch, pgvector, Aurora with vector extensions, S3 Vectors, Bedrock Knowledge Bases, Pinecone, Weaviate, or Chroma references found in `build.gradle`, source code, or configuration files.
- **Gap**: No vector database present. Required for semantic search, RAG, and agent memory.
- **Recommendation**: Add OpenSearch Service with k-NN plugin or use Bedrock Knowledge Bases with Aurora PostgreSQL pgvector extension as the vector store.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database present (see DATA-Q1). Not applicable.
- **Gap**: No vector DB to manage.
- **Recommendation**: When adding a vector store, use a managed service (OpenSearch Service, Bedrock Knowledge Bases) rather than self-hosted.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No embedding model calls, document chunking/splitting code, similarity search patterns, or RAG pipeline components found. No Bedrock Titan embedding, OpenAI ada, or any embedding-related imports in the codebase.
- **Gap**: No RAG capability. Required for agents to access product catalog knowledge, user context, and domain documentation.
- **Recommendation**: Implement a RAG pipeline using Bedrock Knowledge Bases. Index the unicorn product catalog and any business documentation for agent consumption.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source — MySQL database accessed via `jdbc:mysql://${MONO_TO_MICRO_DB_ENDPOINT}:3306/unishop` (defined in `application.properties`). Three tables (`unicorns`, `unicorns_basket`, `unicorn_user`) in one `unishop` schema (defined in `create_tables.sql`). No additional databases, external APIs, caches, or data stores referenced anywhere in the code. AWS SDK S3 dependency exists in `build.gradle` but is not used in any source file.
- **Gap**: None — single data source is ideal for simplicity.
- **Recommendation**: Maintain single-source simplicity. If additional data stores are introduced during decomposition, implement a unified data access layer or API-based access pattern.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Data access follows a layered repository pattern: Controllers → Services → Repositories → MyBatis Mappers → MySQL. `UnicornRepositoryImpl.java` and `UserRepositoryImpl.java` implement interface-based repositories (`UnicornRepository`, `UserRepository`) that delegate to MyBatis mapper interfaces (`UnicornMapper`, `UserMapper`). SQL is defined in XML mapper files (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`). However, all data access is via direct JDBC/MyBatis connections, not via APIs. Business logic directly calls repository methods.
- **Gap**: Data is accessed via direct database connections, not via well-defined data APIs. When services are extracted, they will need API-based data access.
- **Recommendation**: Expose data access via REST APIs before service extraction. The existing repository interfaces provide a clean abstraction that maps well to API endpoints.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` includes `com.amazonaws:aws-java-sdk-s3:1.11.567` but no S3 client usage found in any Java source file — the dependency appears unused. No Textract, Tika, or document parsing libraries. The `unicorns` table stores an `image` field as a VARCHAR(256) — likely a reference/filename, not actual image data. No file upload or processing endpoints.
- **Gap**: No unstructured data handling. S3 SDK dependency is unused.
- **Recommendation**: Remove unused S3 SDK dependency. When unstructured data processing is needed for agents, implement an S3-based document pipeline with Textract for parsing.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: `database/create_tables.sql` provides the complete schema definition with all 3 tables, constraints, and seed data (10 unicorn products). This serves as documentation but is not versioned — there is no Flyway, Liquibase, or Alembic migration framework. No JSON Schema, Avro, or Protobuf definitions. No schema registry. MyBatis XML mappers (`UnicornMapper.xml`, `UserMapper.xml`) document the SQL queries but are not formal schema documentation.
- **Gap**: Schema exists as a static DDL file but is not versioned or managed through migrations.
- **Recommendation**: Adopt Flyway or Liquibase for database migration management. Create versioned migration files from `create_tables.sql` as the baseline migration.

#### DATA-Q8: Data Access Layer
- **Score**: 3/4 🟡
- **Finding**: Centralized data access layer via MyBatis + repository pattern. All database access flows through: `MyBatisConfig.java` (configures `SqlSessionFactory`, registers mapper XMLs) → MyBatis Mapper interfaces (`UnicornMapper.java`, `UserMapper.java`, `HealthMapper.java`) → Repository implementations (`UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`). No direct SQL execution outside this pattern. Repository interfaces (`UnicornRepository.java`, `UserRepository.java`) provide clean abstractions.
- **Gap**: Repository implementations catch and swallow exceptions (return `null`), losing error context. No transactional consistency guarantees beyond `@Transactional` annotation at the repository class level.
- **Recommendation**: Improve error handling in repositories — propagate exceptions rather than swallowing them. The existing pattern is a solid foundation for API-ifying data access.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings, vector data, or index refresh mechanisms exist (no vector database present per DATA-Q1). No event-driven embedding triggers, no scheduled re-indexing, no CDC patterns.
- **Gap**: No embedding infrastructure to refresh.
- **Recommendation**: When implementing RAG (Phase 3), design for incremental index updates triggered by data changes (e.g., new unicorn products added to the `unicorns` table).

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 2/4 🟠
- **Finding**: `build.gradle` specifies `mysql:mysql-connector-java:8.0.11` (released 2018), suggesting MySQL 8.x compatibility. The `create_tables.sql` uses `ENGINE=InnoDB DEFAULT CHARSET=UTF8MB4`, compatible with MySQL 8.x. However, no IaC pins the database engine version — no `aws_rds_instance` resource with `engine_version` parameter exists. The connector version 8.0.11 is significantly outdated (current MySQL Connector/J is 8.x.y with many security patches since 2018).
- **Gap**: No IaC pins the database engine version. MySQL connector is outdated (2018). Cannot verify the running database version or assess EOL status without IaC.
- **Recommendation**: Define the database in IaC with an explicit `engine_version` parameter. Upgrade MySQL Connector/J to the latest 8.x release. Verify the running MySQL server version is not approaching EOL.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: `database/create_tables.sql` contains only `CREATE SCHEMA`, `CREATE TABLE`, and `INSERT INTO` statements — no `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION`, or proprietary SQL constructs. MyBatis mapper XMLs (`UnicornMapper.xml`, `UserMapper.xml`, `HealthMapper.xml`) use only standard SQL: `SELECT`, `INSERT IGNORE`, `DELETE`, `JOIN`. No ORM bypass patterns, no raw SQL execution, no proprietary MySQL-specific SQL beyond `INSERT IGNORE` (which is MySQL syntax but simple). All business logic resides in the Java application layer.
- **Gap**: None — no stored procedures or proprietary SQL. This is ideal for database migration.
- **Recommendation**: Maintain this pattern. The absence of stored procedures means database migration to RDS/Aurora (or even DynamoDB for specific tables) will have minimal friction.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: `application.properties` contains hardcoded database credentials in plaintext: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. These credentials are committed to version control. The database endpoint is partially externalized via `${MONO_TO_MICRO_DB_ENDPOINT}` environment variable, but the username and password are not. No AWS Secrets Manager, Vault, Parameter Store, or any secret management integration found in `build.gradle` or source code.
- **Gap**: Credentials hardcoded in plaintext in a version-controlled file. Critical security vulnerability.
- **Recommendation**: Immediately move credentials to AWS Secrets Manager. Use Spring Cloud AWS Secrets Manager integration or the AWS SDK to retrieve credentials at application startup. Remove credentials from `application.properties` and from git history.

#### SEC-Q2: IAM Least Privilege
- **Score**: 1/4 ❌
- **Finding**: No IAM policies defined anywhere — no IaC exists. `build.gradle` includes `com.amazonaws:aws-java-sdk:1.11.567` (the full SDK, not scoped individual services), suggesting the application may run with broad permissions. `HealthController.java` accesses EC2 instance metadata, implying an EC2 instance profile exists, but its policy scope cannot be determined from the codebase.
- **Gap**: No IAM policies defined in code. Full AWS SDK included as dependency (broad access potential). Cannot assess least privilege.
- **Recommendation**: Define per-service IAM roles in IaC. Scope SDK dependencies to only the needed services (e.g., replace `aws-java-sdk` with specific service SDKs). Create a task-scoped IAM role for the ECS task definition.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: OAuth2/JWT framework dependencies exist in `build.gradle`: `spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2` (v2.0.1), `spring-security-jwt` (v1.0.9). `ResourceServerConfig.java` has `@EnableResourceServer` annotation and `@Configuration`. `CoreConfig.java` configures a `BCryptPasswordEncoder`. However, `ResourceServerConfig.configure()` sets `authorizeRequests().anyRequest().permitAll()`, effectively disabling all authorization. No JWT token validation, no OAuth2 flow configuration, no token exchange between services.
- **Gap**: OAuth2/JWT framework is wired but completely disabled via `permitAll()`. No actual identity propagation occurs.
- **Recommendation**: Configure the OAuth2 Resource Server with a Cognito User Pool or external IdP. Replace `permitAll()` with role-based authorization on each endpoint. Implement JWT validation.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration (no IaC). No application-level audit logging. `HealthController.java` uses `System.out.println(infoStr)` for logging EC2 instance info. Repository classes use `e.printStackTrace()` for error output. No audit trail of user actions, data modifications, or API calls.
- **Gap**: No audit logging at any level. Cannot trace who did what.
- **Recommendation**: Enable CloudTrail in IaC. Implement application-level audit logging using SLF4J/Logback with structured JSON output. Log all data modification operations (create user, add/remove from basket).

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. No API Gateway (no IaC), no WAF rules, no application-level rate limiting middleware. `ResourceServerConfig.java` imposes no request throttling. All endpoints are unrestricted.
- **Gap**: Zero rate limiting. APIs are vulnerable to abuse and denial-of-service.
- **Recommendation**: Deploy API Gateway with throttling (burst and rate limits). Add per-client quotas via API Gateway usage plans. Consider WAF rate-based rules for DDoS protection.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: The `unicorn_user` table stores `email`, `first_name`, and `last_name` (defined in `create_tables.sql`). `User.java` model exposes these fields directly in API responses. `UserController.java` returns `User` objects with PII via `ResponseEntity<User>`. No PII detection, masking, or redaction logic found. No log scrubbing middleware. `e.printStackTrace()` in repository classes could leak PII in stack traces.
- **Gap**: PII (email, name) is returned unmasked in API responses and could be leaked in error logs.
- **Recommendation**: Implement PII redaction in logging (use SLF4J message masking). Add response filtering for sensitive fields based on caller authorization level. Enable Amazon Macie on data stores.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human-in-the-loop approval workflows. No Step Functions with human approval tasks (`waitForTaskToken`). No approval Lambda patterns. No manual approval stages in CI/CD (no CI/CD exists). All operations execute immediately without gating.
- **Gap**: No human approval gates for high-risk actions. Required for agentic systems to prevent autonomous execution of destructive operations.
- **Recommendation**: Implement human-in-the-loop approval via Step Functions for high-risk agent actions (e.g., bulk data modifications, account deletions). This is a Phase 3 requirement for safe agent deployment.

#### SEC-Q8: Encryption at Rest
- **Score**: 1/4 ❌
- **Finding**: No KMS configuration anywhere. No `aws_kms_key` resources (no IaC). No `kms_key_id` on any data store configuration. `application.properties` does not reference any encryption settings. No server-side encryption configuration for any data at rest.
- **Gap**: No encryption at rest verified. Database and any data stores may use default encryption only.
- **Recommendation**: Define customer-managed KMS keys in IaC. Apply KMS encryption to RDS, S3 (if used), and any EBS volumes. Enable SSL/TLS for the MySQL connection (add `useSSL=true` to JDBC URL).

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: All API endpoints use `@PreAuthorize("permitAll()")`: `UnicornController.getUnicorns()`, `BasketController.addUnicornToBasket()`, `BasketController.removeFromBasket()`, `BasketController.getUnicornBasket()`, `UserController.createUser()`, `UserController.login()`, `HealthController.ping()`, `HealthController.isHealthy()`, `HealthController.databasePing()`, `DataReplicationController.replicate()`. Additionally, `Application.java` ignores all OPTIONS requests from security with comment: "workaround to get CORS working with this old version, not recommended for production usage!" No actual authentication is enforced.
- **Gap**: Zero authentication on any endpoint. All endpoints are publicly accessible.
- **Recommendation**: Configure Cognito User Pool as the OAuth2 authorization server. Implement JWT validation in the Resource Server configuration. Apply role-based `@PreAuthorize` annotations per endpoint sensitivity.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` includes OAuth2/JWT dependencies suggesting integration was planned, but no identity provider is configured. No Cognito User Pool, no Okta, no OIDC/SAML configuration, no SSO setup found in `application.properties` or any configuration file. `UserController.java` has a `/user/login` endpoint that simply looks up a user by email via `userService.getByEmail()` — this is not OAuth2/JWT authentication.
- **Gap**: No centralized identity provider. Login mechanism is a simple database lookup, not standards-based authentication.
- **Recommendation**: Deploy Amazon Cognito User Pool as the centralized identity provider. Configure OIDC/OAuth2 flows. Migrate the `/user/login` endpoint to use Cognito authentication tokens.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, Zipkin, Jaeger, or Datadog SDK found in `build.gradle`. No trace context propagation (`traceparent`, `X-Amzn-Trace-Id`) in any controller or middleware. `spring-boot-starter-actuator` is present in `build.gradle` but provides only health/info endpoints — no tracing integration is configured. No `gen_ai.*` semantic conventions, no service mesh configs.
- **Gap**: Zero distributed tracing. Cannot reconstruct request flow or diagnose failures.
- **Recommendation**: Add AWS X-Ray SDK or OpenTelemetry Java agent. Enable auto-instrumentation for Spring Boot. Propagate trace IDs across all HTTP calls and log entries.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: `HealthController.java` uses `System.out.println(infoStr)` for logging EC2 metadata. `UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, and `HealthRepositoryImpl.java` use `e.printStackTrace()` for error logging. No SLF4J logger instances, no JSON log formatters (no Logback JSON encoder, no Log4j2 JSON layout), no correlation IDs, no structured log fields. All logging goes to stdout/stderr in unstructured text format.
- **Gap**: All logging is unstructured `System.out.println` and `e.printStackTrace()`. No correlation IDs. Logs are not queryable.
- **Recommendation**: Replace all `System.out.println` and `e.printStackTrace()` with SLF4J Logger. Add Logback JSON encoder for structured output. Add MDC-based correlation IDs. Enable CloudWatch Logs Insights queries.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no eval datasets, no scoring scripts, no LLM-as-judge patterns, no golden datasets, no A/B test infrastructure. No AI/agent components exist to evaluate.
- **Gap**: No agent evaluation infrastructure. Required before deploying any agentic capabilities.
- **Recommendation**: Implement evaluation pipeline in Phase 3 alongside agent framework integration. Create golden datasets for API responses, implement RAGAS-style metrics for RAG quality.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions in code, configuration, or documentation. No CloudWatch alarms (`aws_cloudwatch_metric_alarm`). No p99/p95 latency monitoring. No error budget tracking. The `spring-boot-starter-actuator` provides a `/health` endpoint but no SLO-related metrics or monitoring.
- **Gap**: No SLOs defined. No monitoring of latency, availability, or error rates.
- **Recommendation**: Define SLOs for critical user journeys (product listing, basket operations, user login). Create CloudWatch alarms on p99 latency and 5xx error rates. Implement SLO dashboards.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment configuration exists (no CI/CD). No blue/green, canary, or rolling deployment strategy. No CodeDeploy rollback triggers, no Helm rollback, no feature flags. No prompt versioning (no AI components). The `bootJar { launchScript() }` in `build.gradle` suggests manual JAR replacement on EC2 with no rollback mechanism.
- **Gap**: No automated rollback for code or configuration. Manual deployment implies manual rollback.
- **Recommendation**: Implement blue/green or canary deployments via CodeDeploy or ECS rolling updates. Add feature flags (LaunchDarkly, AWS AppConfig) for gradual rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No Bedrock, OpenAI, Anthropic, or any AI model calls. No token counting, no cost attribution, no usage tracking. No retention policies for observability data.
- **Gap**: No LLM infrastructure to track. This criterion becomes relevant in Phase 3.
- **Recommendation**: When integrating AI/agent frameworks (Phase 3), implement per-request token usage tracking with user/feature attribution from day one. Define tiered retention policies for LLM prompt/response pairs.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics, no business outcome tracking, no conversion metrics, no resolution rate monitoring. `spring-boot-starter-actuator` provides infrastructure metrics (health, info) but no business metrics. No `cloudwatch.put_metric_data` calls or CloudWatch SDK usage for custom metrics.
- **Gap**: No business metrics published. Only basic infrastructure health via Actuator.
- **Recommendation**: Add custom CloudWatch metrics for business events: basket additions/removals, user registrations, product catalog views. Create business outcome dashboards alongside infrastructure metrics.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection, no error rate alarms, no latency monitoring, no PagerDuty/OpsGenie integration. No alerting of any kind — not even basic CloudWatch alarms (no IaC). No behavioral baseline monitoring.
- **Gap**: Zero anomaly detection or alerting. Failures go undetected.
- **Recommendation**: Implement CloudWatch anomaly detection on p99 latency and error rates. Set up composite alarms with PagerDuty/OpsGenie integration. For agent workloads, implement behavioral baseline monitoring (tool call patterns, response lengths).

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment configuration. No CodeDeploy, Helm, Argo Rollouts, or Lambda traffic shifting. No ALB weighted target groups. No feature flags. `build.gradle` `bootJar { launchScript() }` suggests direct JAR deployment to EC2 — straight to production with no progressive rollout.
- **Gap**: No deployment strategy. Direct-to-production deployment assumed.
- **Recommendation**: After containerizing to ECS, implement canary or blue/green deployments using CodeDeploy with ECS. Add automatic rollback triggers on error rate thresholds.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: `build.gradle` includes `testImplementation('org.springframework.boot:spring-boot-starter-test')` but no test classes exist. No `src/test/` directory found. No integration tests, no unit tests, no API test suites (Postman/Newman), no contract tests, no end-to-end test pipelines. Zero test coverage.
- **Gap**: Zero tests of any kind despite test framework being available as a dependency.
- **Recommendation**: Create integration tests for all API endpoints using `@SpringBootTest`. Add TestContainers for MySQL integration testing. Implement test stage in CI/CD pipeline. Target critical workflows first: product listing, basket operations, user registration/login.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON) in the repository. No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns (auto-restart, auto-scaling on failure). `README.md` was not examined for operational procedures but is a basic project readme.
- **Gap**: No incident response automation or runbooks. Incidents require fully manual response.
- **Recommendation**: Create machine-readable runbooks for common failure scenarios (database connectivity issues, high error rates, service unavailability). Implement health check-based auto-restart in ECS task definitions.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No SLO definition files, no dashboards with named owners, no CODEOWNERS file, no team ownership files referencing observability assets. No platform team tooling or centralized observability stack configuration. No evidence of developer-owned service-level instrumentation.
- **Gap**: No observability ownership model. No shared responsibility model for service reliability.
- **Recommendation**: Establish observability ownership as part of Phase 2 modernization. Create CODEOWNERS file. Define per-service SLOs with named owners. Adopt an observability-as-a-product mindset with platform engineering support.

---

## Appendix: Evidence Index

| # | File | Key Finding |
|---|------|-------------|
| 1 | `build.gradle` | Spring Boot 2.1.6, Java 8, AWS SDK v1 (1.11.567), OAuth2/JWT dependencies, MyBatis, MySQL connector 8.0.11, spring-boot-starter-test present but unused. Commented-out Docker task. |
| 2 | `src/main/resources/application.properties` | Hardcoded DB credentials (MonoToMicroUser/MonoToMicroPassword). DB endpoint externalized via `MONO_TO_MICRO_DB_ENDPOINT`. Port 8080. |
| 3 | `database/create_tables.sql` | MySQL schema with 3 tables (unicorns, unicorns_basket, unicorn_user). InnoDB engine, UTF8MB4. No stored procedures. 10 seed unicorn products. |
| 4 | `src/main/java/com/monoToMicro/Application.java` | Spring Boot main class. Ignores all OPTIONS requests from security. Wide-open CORS configuration. |
| 5 | `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | @EnableResourceServer with `authorizeRequests().anyRequest().permitAll()` — OAuth2 framework present but all auth disabled. |
| 6 | `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | Uses `EC2MetadataUtils.getInstanceInfo()` confirming EC2 deployment. `System.out.println` for logging. |
| 7 | `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | GET `/unicorns` — returns all unicorns. @PreAuthorize("permitAll()"). Synchronous. |
| 8 | `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | POST/DELETE/GET `/unicorns/basket` — basket CRUD. All @PreAuthorize("permitAll()"). Synchronous. |
| 9 | `src/main/java/com/monoToMicro/rest/controller/UserController.java` | POST `/user` (create), POST `/user/login` (email lookup). @PreAuthorize("permitAll()"). Simple DB lookup login. |
| 10 | `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | GET `/data` — reads all baskets synchronously. Returns null on error. |
| 11 | `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | Implements UnicornService interface. CRUD operations delegating to UnicornRepository. Clean interface-based design. |
| 12 | `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | Implements UserService interface. User creation with UUID generation. Delegates to UserRepository. |
| 13 | `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | @Repository @Transactional. Catches all exceptions with `e.printStackTrace()`, returns null. No resilience patterns. |
| 14 | `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | Synchronized `create()` method. Catches all exceptions with `e.printStackTrace()`, returns null. |
| 15 | `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | MyBatis SQL: SELECT *, INSERT IGNORE (idempotent), DELETE, JOINs across unicorns and unicorns_basket tables. |
| 16 | `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | MyBatis SQL: INSERT IGNORE into unicorn_user (idempotent). SELECT by email. Uses cache. |
| 17 | `src/main/java/com/monoToMicro/core/model/Unicorn.java` | @JsonInclude(NON_NULL). Fields: uuid, name, description, price, image. Extends CoreModel. |
| 18 | `src/main/java/com/monoToMicro/core/model/CoreModel.java` | Base model with @JsonIgnore on internal fields (id, creationDate, etc.). @JsonSerialize(NON_NULL). Uses Joda DateTime. |
| 19 | `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | Configures SqlSessionFactory, registers 3 mapper XMLs, creates mapper beans. Central DB config. |
| 20 | `gradle/wrapper/gradle-wrapper.properties` | Gradle 7.4 wrapper distribution. |
