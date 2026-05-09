# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Netflix--eureka |
| **Date** | 2026-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, service-discovery, microservices |
| **Context** | Netflix service-discovery server and client. |
| **Overall Score** | 1.50 / 4.0 |

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false

**Archetype Justification**: Eureka maintains in-memory instance registry state with CRUD operations (register, renew, cancel, status update) exposed via REST endpoints. It owns mutable state (the registry) and exposes read/write operations on business entities (service instances). Classified as stateful-crud despite lacking a traditional database — the in-memory registry is the persistent state within a running instance.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.29 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 1.83 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.40 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.50 / 4.0** | **❌ Not Ready** | **Critical** |

**Scoring Notes:**
- INF: (1+NE+1+1+1+1+1+NE+NE+1+2) / 7 = 9/7 = 1.29 (INF-Q2, INF-Q8, INF-Q9 Not Evaluated due to surface flags)
- APP: (2+2+2+2+1+2) / 6 = 11/6 = 1.83
- DATA: (3+NE+NE+NE) / 1 = 3/1 = 3.00 (DATA-Q2 scored, DATA-Q1 scored; DATA-Q3, DATA-Q4 Not Evaluated — no database)
- SEC: (1+NE+1+1+2+1+1) / 5 = 7/5 = 1.40 (SEC-Q2 Not Evaluated due to surface flag)
- OPS: (1+NE+1+1+1+1+1+1+1) / 8 = 8/6 = 1.33 (OPS-Q2 Not Evaluated due to surface flag)

*Correction on DATA: DATA-Q1=3 is the only non-N/A scored question (DATA-Q2 also applies). Recalculating:*
- DATA: DATA-Q1=3, DATA-Q2=3 → (3+3)/2 = 3.00

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute — no IaC, no containers, no serverless. WAR deployment only. | Cannot scale elastically, no container orchestration, high operational overhead. |
| 2 | INF-Q10: Infrastructure as Code | 1 | Zero IaC — all infrastructure is undefined in repository. | No reproducible infrastructure, no automated provisioning, no disaster recovery capability. |
| 3 | SEC-Q5: Secrets Management | 1 | Secrets used in CI/CD via GitHub Secrets but no application-level secrets management infrastructure. | No rotation, no audit trail, no centralized secrets governance. |
| 4 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — only library publishing to Maven Central. No production deployment automation. | No safe rollout mechanism, no canary/blue-green capability, high-risk releases. |
| 5 | APP-Q1: Programming Languages | 2 | Java 8 with Jersey 1.x, AWS SDK v1, Servlet 2.5 — compound legacy across language version, framework, and SDK. | Blocked from modern AWS features, security patches, and cloud-native frameworks. |

---

## Quick Agent Wins

No Quick Agent Wins identified. The system lacks the foundational capabilities (API documentation, CI/CD deployment automation, structured logging, workflow orchestration) needed to support agent integration. Address the gaps identified in this assessment before pursuing agent opportunities.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=2 |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | No commercial database engines detected; DATA-Q4 Not Evaluated (no database). |
| 4 | Move to Managed Databases | Not Triggered | — | — | No database deployed (has_persistent_data_store=false); INF-Q2 Not Evaluated. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; no streaming/ETL artifacts found. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q5=1, OPS-Q6=1 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:**
- APP-Q2=2: The application is a modular monolith (10 Gradle submodules) with identifiable boundaries, but all modules are coupled through shared in-memory state and deployed as a single WAR artifact.
- INF-Q1=1: No managed compute. The application is packaged as a WAR for traditional servlet containers with no containerization or serverless adoption.
- APP-Q3=2: All inter-service communication (peer replication) is synchronous HTTP with no async patterns for state propagation.

**Recommended Decomposition Approach:** Strangler Fig (Parallel Track) — the existing module boundaries (eureka-client, eureka-core, eureka-server) provide natural extraction points. Containerize the monolith first, then selectively extract services.

**Representative AWS Services:** EKS (preferred per context), API Gateway, EventBridge, ECS/Fargate
**Recommended Patterns:** Anti-corruption Layer, Hexagonal Architecture
**Learning Resources:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:**
- INF-Q1=1: Application is packaged as a WAR artifact deployed to a traditional servlet container (Jetty via Gretty plugin for development, external container for production).
- No Dockerfile, docker-compose, or Kubernetes manifest found in the repository.

**Container Readiness Indicators:**
- Multi-module Gradle build is well-structured for containerization
- Configuration is externalized via properties files (eureka-client.properties, eureka-server.properties)
- Port binding is configurable (eureka.port=8080)
- No local filesystem dependencies beyond in-memory registry

**Recommended Approach:**
1. Convert WAR to embedded server (Spring Boot or Jetty standalone)
2. Create Dockerfile with multi-stage build
3. Deploy to EKS (preferred per context) with Helm charts
4. Configure health checks via existing `/status` endpoint

**Representative AWS Services:** EKS, ECR, Fargate, App Runner
**Learning Resources:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- INF-Q10=1: Zero infrastructure as code. No Terraform, CloudFormation, CDK, or Helm files exist.
- INF-Q11=2: CI/CD exists for building and publishing library artifacts (GitHub Actions: build, snapshot, candidate/release to Maven Central), but there is no deployment pipeline for production workloads.
- OPS-Q5=1: No deployment strategy — the project only publishes JAR/WAR artifacts to Maven Central. No canary, blue/green, or rolling deployment.
- OPS-Q6=1: One integration test exists (EurekaClientServerRestIntegrationTest) but testing is primarily unit-level with JUnit 4.

**Recommended Actions:**
1. Add Terraform or CDK for EKS cluster, networking, and IAM (prefer EKS per context)
2. Extend GitHub Actions with container build, ECR push, and EKS deployment stages
3. Implement canary deployments via Argo Rollouts or AWS CodeDeploy
4. Add integration test suite that runs against containerized Eureka server in CI

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation/CDK, ECR
**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

APP-Q2 scored 2 (monolith with identifiable modules but shared state). The following decomposition guidance applies.

### Recommended Approach: Conditional / Adaptive

**Rationale:** Eureka has well-defined module boundaries (eureka-client, eureka-core, eureka-server, eureka-server-governator) and clear package separation. However, the modules share in-memory state (the instance registry) and are coupled through internal APIs. Given the nature of service discovery (all components need access to the registry), full microservices decomposition may not be architecturally appropriate. Instead:

1. **Phase 1 — Containerize as-is:** Convert the WAR to an embedded server, create a Docker image, deploy to EKS. This provides immediate operational benefits without architectural risk.
2. **Phase 2 — Selective extraction:** Extract the eureka-client as a standalone lightweight library (already semi-independent). Consider whether the server needs decomposition or whether a single containerized service with horizontal scaling is the correct end-state for a registry.

**Alternative consideration:** For service discovery workloads, the target architecture may be AWS Cloud Map (managed service discovery) rather than self-hosted Eureka, which would eliminate the decomposition question entirely.

### Pattern Recommendations

| Pattern | Application to Eureka |
|---------|----------------------|
| **Anti-corruption Layer** | Place between Cloud Map and existing Eureka clients during migration to managed service discovery. |
| **Hexagonal Architecture** | Structure the containerized Eureka server with clear ports (REST API, peer replication) and adapters (current Jersey, future Spring MVC). |

### Effort Estimation

| Factor | Assessment | Signal |
|--------|-----------|--------|
| Module boundaries | Clear (10 Gradle modules) | Low effort |
| Data coupling | Shared in-memory registry state | Medium effort |
| Stored procedures | None (no database) | N/A |
| Communication patterns | All synchronous HTTP | Medium effort |
| CI/CD maturity | Build/publish only, no deployment | High effort for deployment pipeline |
| Test coverage | ~110 test files, some integration | Medium — some safety net exists |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is undefined in the repository. The application is packaged as a WAR file (`eureka-server/build.gradle` applies the `war` plugin) for deployment to an external servlet container. No ECS, EKS, Lambda, Fargate, or EC2 resource definitions exist. The Gretty Gradle plugin (version 3.1.0 in root `build.gradle`) provides a development-time servlet container only. |
| **Gap** | No managed compute infrastructure. No containerization, no serverless, no IaC-defined compute resources. The deployment model is entirely manual — a WAR artifact published to Maven Central with no deployment target defined. |
| **Recommendation** | Containerize the application: convert from WAR to embedded server (Spring Boot or standalone Jetty), create a Dockerfile, and deploy to EKS (preferred). Define EKS cluster, node groups, and service resources in Terraform or CDK. |
| **Evidence** | `build.gradle` (Gretty plugin), `eureka-server/build.gradle` (war plugin), absence of any Dockerfile/Kubernetes/Terraform files. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. Eureka is an in-memory service registry — instance state is held in a `ConcurrentHashMap` in the JVM and replicated via peer-to-peer HTTP. No database driver dependencies, no database connection strings, no RDS/DynamoDB/DocumentDB resources exist. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database dependencies in any `build.gradle`. No JDBC/JPA/Hibernate/MongoDB drivers. No `aws_rds_*` or `aws_dynamodb_*` resources. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | This service is a `stateful-crud` with multi-step operations: peer replication involves multi-step coordination (batch replication tasks in `com/netflix/eureka/cluster/` and `com/netflix/eureka/util/batcher/`), self-preservation threshold calculation, and registry sync on startup are all hardcoded state machines with no dedicated orchestration service. |
| **Gap** | Multi-step operations (peer replication batching, registry sync, self-preservation) are entirely implemented as hardcoded application logic with custom batching frameworks (`TaskExecutors`, `AcceptorExecutor`). No Step Functions, Temporal, or equivalent orchestration. |
| **Recommendation** | For the containerized deployment, evaluate whether peer replication batching and registry sync workflows could benefit from Step Functions or EventBridge Pipes for better observability and error handling. However, given the latency-sensitive nature of service discovery, the current in-process approach may be architecturally appropriate — prioritize containerization and operational visibility first. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/batcher/` (custom batching framework), `eureka-core/src/main/java/com/netflix/eureka/cluster/` (peer replication logic). |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging infrastructure exists. All peer replication and client communication is synchronous HTTP. State changes (register, renew, cancel) are propagated to peers via synchronous HTTP batch requests. No SQS, SNS, EventBridge, Kafka, or any messaging system is used. For a `stateful-crud` service where state changes cross service boundaries (peer servers), this represents tight synchronous coupling. |
| **Gap** | State changes between Eureka server peers are propagated via synchronous HTTP batch requests. This creates tight coupling between peers — if a peer is slow or unreachable, the replication batch blocks. No async decoupling exists for cross-instance state propagation. |
| **Recommendation** | Evaluate EventBridge or SQS for peer state propagation to decouple peer replication from synchronous HTTP. Alternatively, when migrating to AWS Cloud Map, this becomes managed and the gap disappears. For the current architecture, adding managed messaging for peer replication would improve resilience. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (synchronous HTTP replication), absence of any messaging SDK dependencies in all `build.gradle` files. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security infrastructure is defined. No VPC, subnet, security group, or network policy definitions exist anywhere in the repository. The application is deployed without any IaC-defined network topology. |
| **Gap** | Zero network security configuration. No VPC isolation, no private subnets, no security groups, no NACLs. The deployment model is entirely undefined from a network perspective. |
| **Recommendation** | When adding IaC (Terraform/CDK), define a VPC with private subnets for Eureka servers, security groups restricting access to the Eureka port (8080) from known CIDR ranges only, and VPC endpoints for AWS service access. Consider VPC Lattice for service-to-service communication. |
| **Evidence** | Absence of any `.tf`, CloudFormation, or CDK files. No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point is defined. The Eureka REST API (configured via `web.xml` at `/v2/apps/*`) is exposed directly by the servlet container with no external load balancer or gateway. |
| **Gap** | Services exposed directly with no gateway, load balancer, throttling (rate limiting filter is commented out in web.xml), or centralized authentication. |
| **Recommendation** | Deploy behind an ALB (minimum) or API Gateway with throttling and authentication. For EKS deployment, use an Ingress controller (AWS Load Balancer Controller) with health checks. Consider API Gateway for external client access with throttling and request validation. |
| **Evidence** | `eureka-server/src/main/webapp/WEB-INF/web.xml` (rate limiting filter commented out), absence of any `aws_lb_*`, `aws_api_gateway_*` resources. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No ASG, ECS service scaling, EKS HPA, or Lambda concurrency configuration is defined. The application has AWS Auto Scaling SDK dependency (`aws-java-sdk-autoscaling`) but this is used to query ASG membership of registered instances — not to auto-scale Eureka itself. |
| **Gap** | No auto-scaling for the Eureka service itself. All capacity would need to be statically provisioned. |
| **Recommendation** | When deployed to EKS, configure Horizontal Pod Autoscaler (HPA) based on request rate or registry size. Define min/max replicas appropriate for the cluster size. |
| **Evidence** | `eureka-core/build.gradle` (`aws-java-sdk-autoscaling` dependency — used for querying, not self-scaling), absence of any `aws_autoscaling_*` or HPA resources. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. Eureka's registry is an in-memory data structure that is reconstructed from peer replication and client heartbeats on startup. There is no database, no S3 bucket, no EBS volume, and no persistent file storage. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database dependencies, no S3 usage, no EBS references, no backup configuration. Registry is rebuilt from peers on restart. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. No IaC defines compute resources, no Kubernetes manifests specify replica counts, and no deployment configuration exists. The application is designed for multi-instance peer replication (configuration supports multiple eureka.serviceUrl entries across AZs), but no deployment-level HA is defined in the repository. INF-Q9 does not apply because `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC, no Kubernetes manifests, no deployment configuration. `eureka-client.properties` shows commented-out multi-AZ example configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure as code. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. All infrastructure (if any exists) must be manually created. |
| **Gap** | 0% IaC coverage. No infrastructure is defined in code. No compute, networking, databases, messaging, or operational resources are codified. |
| **Recommendation** | Add Terraform or CDK to define: EKS cluster and node groups, VPC with private subnets, ALB/Ingress, ECR repository, IAM roles, CloudWatch alarms, and Route 53 records. Start with a Terraform module or CDK stack for the core infrastructure. |
| **Evidence** | Absence of any `.tf`, `.tfvars`, `cdk.json`, `template.yaml`, `Chart.yaml`, or `kustomization.yaml` files in the entire repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD exists for building and publishing library artifacts. GitHub Actions workflows automate: CI build (`nebula-ci.yml` — build on push/PR), snapshot publishing (`nebula-snapshot.yml` — publish on master push), and release publishing (`nebula-publish.yml` — publish on tag). However, there is no deployment pipeline — the CI/CD only produces artifacts (JARs/WARs to Maven Central), not deployments to running infrastructure. |
| **Gap** | Build is automated but deployment is entirely absent. No infrastructure deployment automation exists. The CI/CD pipeline ends at artifact publication with no container build, no image push, no deployment step, and no rollback capability. |
| **Recommendation** | Extend GitHub Actions with: Docker image build and ECR push, Helm chart packaging, EKS deployment via kubectl/Helm, health check verification, and automated rollback on failure. Add a separate IaC pipeline for Terraform/CDK changes. |
| **Evidence** | `.github/workflows/nebula-ci.yml`, `.github/workflows/nebula-snapshot.yml`, `.github/workflows/nebula-publish.yml` (build + publish only, no deployment). |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Java 8 (`sourceCompatibility = 1.8`, `targetCompatibility = 1.8` in `build.gradle`) with Jersey 1.x (1.19.1), AWS SDK v1 (1.11.277), and Servlet API 2.5. This is compound legacy across all three axes: language version (Java 8 — not current), framework (Jersey 1.x — EOL JAX-RS implementation, not Spring Boot 3.x or Jakarta REST), and AWS SDK (v1 — not v2). Additionally uses Log4j 1.x (EOL, security vulnerability CVE-2021-44228 vector via log4j-1.x bridge), JUnit 4.11 (not JUnit 5), and Netflix OSS libraries (Servo, Archaius, Governator — largely unmaintained). |
| **Gap** | Java 8 + Jersey 1.x + AWS SDK v1 + Servlet 2.5 = compound regression. Language version AND framework AND SDK are all regressed. Requires upgrades across all three axes to reach modern cloud-native capabilities. |
| **Recommendation** | Migrate to Java 17+ with Spring Boot 3.x (or Jakarta EE 10) and AWS SDK v2. This is the foundational prerequisite for all other modernization. Sequence: Java 17 → Spring Boot 3.x → AWS SDK v2 → Micrometer (replacing Servo). |
| **Evidence** | `build.gradle` (sourceCompatibility=1.8, awsVersion='1.11.277', servletVersion='2.5', jerseyVersion='1.19.1'), `.github/workflows/nebula-ci.yml` (java: [8]). |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a monolith with identifiable modules. 10 Gradle submodules provide clear package boundaries (eureka-client, eureka-core, eureka-server, etc.), but they are deployed as a single WAR artifact. The modules share state through the in-memory registry (`InstanceRegistry`) and have cross-module dependencies (eureka-server depends on eureka-core which depends on eureka-client). No independent deployment capability exists. |
| **Gap** | Single deployable unit despite modular structure. Shared in-memory state (instance registry) couples all server-side modules. Cannot independently scale, deploy, or version modules. Cross-module data access is direct (Java method calls to shared registry). |
| **Recommendation** | Containerize as a single service first (appropriate for a service registry). Evaluate whether AWS Cloud Map could replace self-hosted Eureka entirely. If continuing with self-hosted Eureka, the monolithic architecture may be architecturally correct for an in-memory registry — focus on containerization and horizontal scaling rather than decomposition. |
| **Evidence** | `settings.gradle` (10 modules), `eureka-server/build.gradle` (war plugin — single deployable), dependency chain: eureka-server → eureka-core → eureka-client. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | All communication is synchronous HTTP. Client-to-server registration/heartbeat uses synchronous HTTP (Jersey 1.x client). Server-to-server peer replication uses synchronous HTTP batch requests (`PeerEurekaNode`, `ReplicationClient`). No async patterns exist for state propagation. For a `stateful-crud` service, this is primarily synchronous with no async for cross-service state changes. |
| **Gap** | Primarily synchronous with no async patterns. Peer replication (state changes that cross service boundaries) is synchronous HTTP. Client heartbeats are synchronous. No event-driven or message-based communication exists where async would genuinely help (peer state propagation). |
| **Recommendation** | Add EventBridge or SQS for peer state propagation to decouple replication from synchronous HTTP. Keep client registration/heartbeat synchronous (appropriate for request/response). Alternatively, migrating to AWS Cloud Map eliminates this concern. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-client/src/main/java/com/netflix/discovery/shared/transport/` (Jersey HTTP clients), absence of any messaging dependencies. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Some background job processing exists but with inconsistent patterns. The batching framework (`eureka-core/src/main/java/com/netflix/eureka/util/batcher/`) processes replication tasks asynchronously using internal thread pools. Registry sync on startup can take significant time. However, these are internal background processes, not user-facing operations exceeding 30 seconds. Client-facing operations (register, heartbeat, fetch registry) are fast. The custom batching framework (`TaskExecutors`, `AcceptorExecutor`) is a homegrown async job processor. |
| **Gap** | Background processing exists (peer replication batching) but uses a custom, untested-in-production-at-scale batching framework rather than managed services. No status polling or callback patterns for long-running operations. |
| **Recommendation** | The current internal batching is likely adequate for the service discovery use case. When containerizing, ensure the batching framework's thread pool configuration is tunable via environment variables. Consider SQS for peer replication if peer count grows large. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/batcher/TaskExecutors.java`, `AcceptorExecutor.java`, `eureka-core/src/main/java/com/netflix/eureka/cluster/` (batch replication). |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No consistent API versioning strategy. The REST API uses `/v2/apps` URL paths, but this is a single version with no versioning strategy for evolution. The `Version` enum in `eureka-core` distinguishes V1 and V2 protocols, but there is no documented versioning policy, no backward compatibility guarantees, and no mechanism for introducing V3 without breaking existing clients. |
| **Gap** | Single version (`/v2/`) with no versioning strategy for API evolution. No Accept-Version headers, no version negotiation, no backward compatibility documentation. Breaking changes would need to be deployed simultaneously. |
| **Recommendation** | Document the current V2 API contract. Add OpenAPI specification generation from JAX-RS annotations. Define a versioning strategy (URL path-based is already partially in place with `/v2/`) and commit to backward compatibility guarantees for the current version. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (`/v2/apps` path), `eureka-core/src/main/java/com/netflix/eureka/Version.java` (V1/V2 enum), absence of any OpenAPI spec or versioning documentation. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Eureka IS a service discovery system — it provides discovery for other services. For its own infrastructure (finding peer Eureka servers), it uses configurable mechanisms: DNS-based lookup (`eureka.shouldUseDns=true` with TXT records) or explicit URL lists (`eureka.serviceUrl.default=http://localhost:8080/eureka/v2/`). Environment variables and properties files configure endpoints — not hard-coded in application code, but also not dynamic discovery. |
| **Gap** | Peer discovery uses environment variables/properties for endpoints rather than dynamic discovery. While DNS-based lookup is supported, the default configuration uses static URL lists. No service mesh or dynamic routing for the Eureka service itself. |
| **Recommendation** | When deploying to EKS, use Kubernetes service DNS for peer discovery (headless Service). This provides dynamic peer discovery without static configuration. Alternatively, configure DNS-based discovery with Route 53 for cross-AZ peer resolution. |
| **Evidence** | `eureka-server/src/main/resources/eureka-client.properties` (shouldUseDns=false, serviceUrl.default=http://localhost:8080), `eureka-client/src/main/java/com/netflix/discovery/endpoint/` (DNS resolver code). |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Eureka does not store unstructured data (documents, files, images) as part of its core function. The only "data" is the structured in-memory service registry (instance metadata: hostname, port, status, health URL). The `eureka-resources` module contains static web assets (CSS, JS, JSP for the status dashboard) which are packaged in the WAR and served from the classpath — not stored in external storage. No S3, EFS, or file system storage is used for application data. |
| **Gap** | Static web assets (JSP, CSS, JS) are bundled in the WAR rather than served from S3/CloudFront. This is a minor gap — the assets are small and bundling is appropriate for a service discovery server. |
| **Recommendation** | When containerizing, consider serving the status dashboard static assets via CloudFront + S3 if the dashboard needs to be independently deployable. For the core service, no unstructured data storage changes are needed. |
| **Evidence** | `eureka-resources/src/main/resources/` (css/, js/, jsp/ directories — static dashboard assets). |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The instance registry has a well-defined access layer. All data access goes through the `InstanceRegistry` interface (`eureka-core/src/main/java/com/netflix/eureka/registry/`), which provides a unified API for register, renew, cancel, and query operations. The registry is the single point of data access — no scattered database connections exist because there is no database. The access pattern is centralized and consistent. |
| **Gap** | The unified access layer exists but has no formal data contract (no schema validation, no API contract testing). The registry interface is clear but not documented as a formal contract. |
| **Recommendation** | Document the registry data contract. Add contract tests for the InstanceRegistry interface to ensure backward compatibility during modernization. This is a minor gap — the architecture is sound. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/InstanceRegistry.java` (interface), `AbstractInstanceRegistry.java` (implementation), `PeerAwareInstanceRegistryImpl.java` (peer-aware implementation). |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. Eureka uses an in-memory ConcurrentHashMap as its data store. No database engine, no database version, no EOL concern applies. DATA-Q3 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database dependencies in any build.gradle. No JDBC drivers, no ORM, no database connection configuration. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not use a database. No stored procedures, triggers, or proprietary SQL exist because there is no SQL database. All business logic is in the application layer (Java). DATA-Q4 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `.sql` files, no database dependencies, no ORM configuration, no stored procedure definitions anywhere in the repository. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging is configured. The application has basic request logging via `ServerRequestAuthFilter` (logs client identity headers), but this is application-level logging to Log4j 1.x with no audit trail guarantees, no immutable storage, and no CloudTrail integration. |
| **Gap** | No CloudTrail. No immutable audit logs. Application-level logging uses Log4j 1.x (EOL) with console appender only (no structured log output, no log aggregation, no retention policy). |
| **Recommendation** | When deploying to EKS, configure CloudTrail for API-level auditing. Add structured JSON logging (replace Log4j 1.x with Logback + JSON encoder). Ship logs to CloudWatch Logs with defined retention. Enable S3 Object Lock for audit log archives. |
| **Evidence** | `eureka-server/src/main/resources/log4j.properties` (console appender only), `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (basic request logging). Absence of any CloudTrail, CloudWatch, or audit configuration. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. Eureka's data is in-memory only. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No persistent storage resources defined. In-memory registry only. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication exists. The `ServerRequestAuthFilter` logs client identity headers (AUTH_NAME, AUTH_VERSION) but does NOT enforce authentication — it is a monitoring/logging filter only. All REST endpoints are open and unauthenticated. The rate limiting filter is commented out in web.xml. No OAuth2, JWT, API keys, or any authentication mechanism is enforced. |
| **Gap** | All API endpoints are completely open with no authentication. Any client can register, deregister, or query instances without credentials. The identity filter logs who is calling but does not block unauthorized callers. |
| **Recommendation** | Add mutual TLS (mTLS) for server-to-server peer replication. Add API Gateway with OAuth2/JWT for external client access. For EKS deployment, consider service mesh (Istio) for zero-trust mTLS between Eureka peers and registered services. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (logging only, no enforcement), `eureka-server/src/main/webapp/WEB-INF/web.xml` (no auth enforcement, rate limiter commented out). |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration. No Cognito, Okta, SAML, OIDC, or any centralized identity system is used. The application has no concept of user identity or authentication — it accepts all requests regardless of caller identity. |
| **Gap** | No centralized identity integration. No SSO, no federation, no external IdP. The application manages no authentication whatsoever. |
| **Recommendation** | When adding authentication (SEC-Q3), integrate with a centralized IdP (Cognito for AWS-native, or existing organizational IdP). For service-to-service auth, use IAM roles for EKS pods with IRSA (IAM Roles for Service Accounts). |
| **Evidence** | Absence of any Cognito, OIDC, SAML, OAuth2, or identity provider configuration in the entire repository. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD pipelines use GitHub Secrets for credentials (signing keys, repo passwords, Sonatype credentials) — these are not plaintext in the repository. However, no application-level secrets management exists. The application configuration (`eureka-client.properties`) contains no secrets currently (Eureka's in-memory design doesn't require database credentials), but the CI/CD secrets have no rotation configured. No AWS Secrets Manager, no Vault, no encrypted parameter store. |
| **Gap** | No plaintext credentials in source (Score 2 baseline met). However, no rotation is configured for CI/CD secrets. No Secrets Manager or Vault integration exists for the application runtime. When authentication is added (SEC-Q3), a secrets management solution will be needed for certificates, tokens, and API keys. |
| **Recommendation** | Adopt AWS Secrets Manager for runtime secrets (TLS certificates, API keys) when authentication is implemented. Configure automated rotation for signing keys used in CI/CD. Add IRSA for EKS pod-level AWS credentials instead of static keys. |
| **Evidence** | `.github/workflows/nebula-publish.yml` (secrets.ORG_SIGNING_KEY, secrets.ORG_SONATYPE_USERNAME, etc. — GitHub Secrets, not plaintext). No `.env` files committed. No hardcoded credentials in source code or properties files. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base images. The CI/CD uses `ubuntu-latest` GitHub Actions runner but no container image scanning, no dependency vulnerability scanning, and no hardened AMI references exist. Dependencies include known-vulnerable libraries (Log4j 1.x, XStream 1.4.19). |
| **Gap** | No patching strategy. No vulnerability scanning. Known-vulnerable dependencies: Log4j 1.x (potential Log4Shell vector via bridges), XStream 1.4.19 (multiple CVEs), Jetty 7.2.0 (test dependency — EOL). No container image to harden (no Docker). |
| **Recommendation** | Add dependency vulnerability scanning (Dependabot for GitHub, or Snyk) immediately — this requires no infrastructure changes. When containerizing, use Bottlerocket or hardened base images for EKS nodes. Add ECR image scanning. Upgrade Log4j 1.x to Logback (eliminate CVE surface). |
| **Evidence** | `build.gradle` (Log4j via slf4j-log4j12:1.6.1 in eureka-server), XStream 1.4.19 across multiple modules, Jetty 7.2.0 in tests. Absence of any Dependabot config, Snyk policy, or vulnerability scanning in CI/CD. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are configured in the CI/CD pipeline. No SAST (SonarQube, Semgrep, CodeGuru), no dependency scanning (Dependabot, npm audit, OWASP dependency-check), no container scanning (ECR scanning, Trivy). The CI pipeline (`nebula-ci.yml`) only runs `./gradlew build` with no security validation step. |
| **Gap** | Pipeline has no security validation. No Dependabot, no SAST, no container scanning. Known vulnerabilities in dependencies go undetected. No `.github/dependabot.yml` configuration file. |
| **Recommendation** | Add Dependabot for dependency vulnerability alerts (immediate, zero-effort). Add OWASP dependency-check Gradle plugin to the build. Add SonarQube or Semgrep as a CI step. When containerizing, add ECR image scanning. |
| **Evidence** | `.github/workflows/nebula-ci.yml` (build only, no security steps), absence of `.github/dependabot.yml`, absence of any SAST/DAST tool configuration. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry, X-Ray, Zipkin, or Jaeger dependencies exist. No trace ID propagation between Eureka clients and servers. The application uses Netflix Servo for metrics but has no tracing capability. |
| **Gap** | No distributed tracing. No trace ID propagation across Eureka server peers or between clients and servers. Debugging request flows across the Eureka cluster requires manual log correlation. |
| **Recommendation** | Add OpenTelemetry Java agent for auto-instrumentation when containerizing. Configure X-Ray or OTEL collector for trace aggregation. Propagate trace IDs through peer replication requests. |
| **Evidence** | Absence of any OpenTelemetry, X-Ray, Zipkin, or Jaeger dependencies in all `build.gradle` files. No `traceparent` or `X-Amzn-Trace-Id` header handling in code. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | While this system has an API surface (`has_api_surface=true`), it has no deployed workload (`has_deployed_workload=false`) and therefore no production SLOs can be defined or monitored. OPS-Q2 does not apply until the service is deployed to a production environment. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC, no deployment configuration, no SLO definitions, no CloudWatch alarms. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application publishes operational metrics via Netflix Servo (`EurekaMonitors` enum tracks RENEW, CANCEL, GET_ALL, REGISTER, EXPIRED, STATUS_UPDATE, RATE_LIMITED counts), but these are published to an internal Servo registry with no external aggregation. No CloudWatch custom metrics, no Prometheus exposition, no Datadog/New Relic integration. Metrics are effectively invisible outside the JVM. |
| **Gap** | Metrics exist in code (comprehensive Servo counters for all operations) but are not published to any external monitoring system. No dashboards, no alerting, no historical trending. The metrics infrastructure is Netflix-internal (Servo) with no cloud-native equivalent. |
| **Recommendation** | Replace Netflix Servo with Micrometer (supports CloudWatch, Prometheus, Datadog). Publish business metrics (registration rate, heartbeat success rate, registry size, peer sync latency) to CloudWatch. Create operational dashboards. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (comprehensive metrics enum), `eureka-client/build.gradle` (servo-core:0.12.21 dependency). No CloudWatch, Prometheus, or Datadog dependencies. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no threshold-based alerts. The application has a self-preservation mode (internal mechanism to detect mass expiration anomalies), but this is an in-process heuristic, not an external alerting system. |
| **Gap** | No external alerting. No anomaly detection. The only anomaly detection is the built-in self-preservation mode which prevents mass deregistration — this is an application-level safety mechanism, not an operational alerting system. |
| **Recommendation** | When deployed to EKS with Micrometer metrics, configure CloudWatch alarms for: registration rate drops, peer sync failures, self-preservation activation, error rates. Add CloudWatch anomaly detection on heartbeat rates. Integrate with PagerDuty or OpsGenie for on-call routing. |
| **Evidence** | Absence of any CloudWatch, PagerDuty, OpsGenie, or alerting configuration. Self-preservation logic in `eureka-core/src/main/java/com/netflix/eureka/registry/` (application-level only). |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The repository only publishes library artifacts (JARs/WARs) to Maven Central via `nebula-publish.yml`. There is no production deployment pipeline, no canary, no blue/green, no rolling update strategy. Deployment of the Eureka service itself is entirely manual and undefined. |
| **Gap** | No deployment strategy. No canary, no blue/green, no staged rollout. No deployment pipeline exists — only artifact publication. |
| **Recommendation** | When deployed to EKS, implement rolling update strategy (minimum) with readiness/liveness probes. For higher safety, implement canary deployments via Argo Rollouts or Flagger with traffic shifting based on error rate and registry health. |
| **Evidence** | `.github/workflows/nebula-publish.yml` (artifact publication only), absence of any CodeDeploy, Helm release, or Kubernetes deployment configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Limited integration testing exists. `EurekaClientServerRestIntegrationTest.java` tests client-server interaction by starting an embedded Jetty server with the Eureka WAR. However, this is a single integration test among ~110 test files that are primarily unit tests. The test uses JUnit 4 and an embedded Jetty 7.x server. No contract tests, no API test suites, no end-to-end multi-instance peer replication tests run in CI. |
| **Gap** | One integration test exists but test coverage is primarily unit-level. No peer replication integration tests, no multi-instance cluster tests, no API contract tests. The single integration test covers basic client-server registration only. |
| **Recommendation** | Add integration test suite using Testcontainers (when containerized) to test: multi-instance peer replication, client failover between servers, self-preservation activation, and full registry lifecycle. Run in CI as a post-build stage. |
| **Evidence** | `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java` (single integration test), `eureka-server/build.gradle` (`test.dependsOn war` — integration test loads WAR). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation. No runbooks (markdown, YAML, or JSON), no SSM Automation documents, no Lambda-based remediation, no self-healing automation beyond the built-in self-preservation mode. |
| **Gap** | No runbooks. No automated incident response. No escalation paths defined. Incident response is entirely ad hoc. |
| **Recommendation** | Create operational runbooks for common Eureka incidents: peer sync failure, mass deregistration, self-preservation activation, memory pressure. When deployed to EKS, implement automated pod restart on health check failure. Consider SSM Automation documents for infrastructure-level remediation. |
| **Evidence** | Absence of any runbook files, SSM documents, or incident response automation in the repository. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership is defined. No CODEOWNERS for monitoring configs, no named alarm owners, no team-specific dashboards, no SLO definitions with team attribution. No observability assets exist to own. |
| **Gap** | No observability ownership. No dashboards, no alarms, no SLO definitions, no team attribution. Monitoring is non-existent rather than reactive. |
| **Recommendation** | When implementing observability (CloudWatch dashboards, alarms), define ownership in CODEOWNERS. Assign alarm owners to on-call team. Create per-service dashboards with team labels. |
| **Evidence** | Absence of CODEOWNERS file, absence of any dashboard or alarm definitions, absence of SLO documents. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging because no IaC-defined resources exist. Zero tags on zero resources. No tagging standard, no tag enforcement, no cost allocation tags. |
| **Gap** | No tagging governance. No resources to tag (no IaC). When infrastructure is created, tagging standards must be established from the start. |
| **Recommendation** | When adding IaC (Terraform/CDK), define mandatory tags from day one: `Service=eureka`, `Environment={env}`, `Team={team}`, `CostCenter={cc}`. Use `default_tags` in Terraform provider block. Add AWS Config rule for required-tags enforcement. |
| **Evidence** | Absence of any IaC files, absence of any resource tags, absence of tagging policy documentation. |

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
| `build.gradle` | INF-Q1, APP-Q1, APP-Q2 | Root build config with Java 8, Gretty plugin, dependency versions |
| `settings.gradle` | APP-Q2 | 10 submodules defined |
| `eureka-server/build.gradle` | INF-Q1, INF-Q11, OPS-Q6 | WAR plugin, server dependencies, test.dependsOn war |
| `eureka-client/build.gradle` | APP-Q1, OPS-Q3 | Jersey 1.x, Servo, Archaius, AWS SDK v1 dependencies |
| `eureka-core/build.gradle` | INF-Q4, INF-Q7 | AWS SDK dependencies (ec2, autoscaling, sts, route53) |
| `.github/workflows/nebula-ci.yml` | INF-Q11, APP-Q1, SEC-Q7 | CI build with Java 8, no security steps |
| `.github/workflows/nebula-publish.yml` | INF-Q11, SEC-Q5, OPS-Q5 | Artifact publication, GitHub Secrets usage |
| `.github/workflows/nebula-snapshot.yml` | INF-Q11 | Snapshot publication on master push |
| `eureka-server/src/main/webapp/WEB-INF/web.xml` | INF-Q6, SEC-Q3 | Servlet deployment descriptor, rate limiter commented out |
| `eureka-server/src/main/resources/eureka-client.properties` | APP-Q6 | Peer discovery configuration, static URL lists |
| `eureka-server/src/main/resources/eureka-server.properties` | INF-Q9 | Server configuration (minimal) |
| `eureka-server/src/main/resources/log4j.properties` | SEC-Q1, SEC-Q6 | Log4j 1.x console appender configuration |
| `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` | SEC-Q1, SEC-Q3 | Identity logging filter (no enforcement) |
| `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` | OPS-Q3 | Servo metrics enum (comprehensive but internal) |
| `eureka-core/src/main/java/com/netflix/eureka/util/batcher/` | INF-Q3, APP-Q4 | Custom batching framework for replication |
| `eureka-core/src/main/java/com/netflix/eureka/cluster/` | INF-Q4, APP-Q3 | Peer replication via synchronous HTTP |
| `eureka-core/src/main/java/com/netflix/eureka/registry/` | APP-Q2, DATA-Q2 | InstanceRegistry interface and implementations |
| `eureka-core/src/main/java/com/netflix/eureka/resources/` | APP-Q5, INF-Q6 | JAX-RS REST resources (/v2/apps) |
| `eureka-server/src/test/java/.../EurekaClientServerRestIntegrationTest.java` | OPS-Q6 | Single integration test |
| `eureka-resources/src/main/resources/` | DATA-Q1 | Static web assets (css, js, jsp) |
