# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | eureka |
| **Date** | 2025-07-15 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, service-discovery, microservices |
| **Context** | Netflix service-discovery server and client. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **1.82 / 4.0** |

**Archetype Justification**: The eureka-server maintains an in-memory instance registry with full CRUD operations (register, query, update, delete instances) and peer-to-peer replication. It has both read and write endpoints via JAX-RS resources. Despite using in-memory storage rather than a persistent database, it owns and manages stateful data — classified as stateful-crud.

> **Note:** Although `repo_type` is `monorepo`, this repository functions as a multi-module library that publishes JAR/WAR artifacts to Maven Central. The 10 Gradle modules (eureka-client, eureka-core, eureka-server, etc.) are library components, not independently deployable microservices. The primary assessable "service" is the eureka-server composite (eureka-core + eureka-server + eureka-server-governator). All 37 questions are evaluated against this composite.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.13 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.17 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.82 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files exist — all infrastructure is manually created or undefined | Blocks reproducible deployments and disaster recovery; triggers Move to Modern DevOps pathway |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute definitions; WAR packaged for legacy servlet container deployment | No path to elastic scaling, automated patching, or container orchestration; triggers Move to Containers pathway |
| 3 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency scanning in CI/CD pipeline | Vulnerabilities in dependencies (e.g., outdated Jackson, Jersey, XStream) reach production undetected |
| 4 | APP-Q1: Programming Languages | 2 | Java 8 with AWS SDK v1 (1.11.277), Jersey 1 (1.19.1), and legacy Netflix OSS libraries — compound legacy | Limits access to modern AWS features, cloud-native tooling, and active security patches |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumentation; Netflix Servo provides metrics only | Debugging peer replication failures and cross-service issues is guesswork |

---

<!-- SECTION: Quick Agent Wins -->
## Quick Agent Wins

### API-Aware Agent

- **Prerequisite:** APP-Q5 = 4 (consistent URL path versioning via `@Path("/{version}/apps")` across all JAX-RS resources). The API surface exists with structured JSON/XML responses.
- **What it enables:** An agent that discovers and invokes Eureka REST endpoints as tools — registry queries, instance lookups, status checks, and health monitoring across Eureka clusters.
- **Additional steps:** No OpenAPI/Swagger specification files exist in the repository. Generate an OpenAPI spec from the JAX-RS annotations (e.g., using `swagger-jaxrs` or `smallrye-openapi`) to enable full tool discovery by the agent.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (GitHub Actions CI pipeline exists — `nebula-ci.yml` runs `./gradlew build`; publish workflows handle Maven Central releases).
- **What it enables:** An agent that triggers CI builds, monitors build status, initiates snapshot/release publishes, and manages the release lifecycle via GitHub Actions API.
- **Additional steps:** None — the GitHub Actions API already supports programmatic triggering and status queries.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** README.md exists with building/contributing/support instructions. The [Eureka wiki](https://github.com/Netflix/eureka/wiki) is referenced for detailed documentation. CHANGELOG.md provides version history.
- **What it enables:** A knowledge agent that indexes Eureka documentation (wiki, README, CHANGELOG, Javadoc) and answers developer questions about configuration, deployment, API usage, and troubleshooting.
- **Additional steps:** The in-repo documentation is minimal (README.md is brief). The wiki is external and would need to be fetched/indexed. Javadoc generation from source would significantly enrich the knowledge base.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — modular monolith with clear module boundaries; primary trigger not met |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no managed compute), no container definitions found; WAR packaging implies legacy servlet deployment |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures), no commercial database engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated — no database exists to migrate |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; low INF-Q4 score is due to lack of async messaging for peer replication, not analytics |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 2 (build automated, deployment manual); OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 2 (limited integration testing) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Netflix service-discovery server and client") |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
The eureka-server is packaged as a WAR file (`eureka-server/build.gradle` applies the `war` plugin) designed for deployment to a servlet container (Jetty/Tomcat). There is no IaC, no Dockerfile, no container definitions, and no Kubernetes manifests anywhere in the repository. The WAR packaging implies traditional servlet container deployment with no managed compute orchestration.

**Container Readiness Indicators:**
- ✅ Application has a well-defined entry point (`EurekaBootStrap` as `ServletContextListener` in `web.xml`)
- ✅ Configuration is externalized via `.properties` files and environment variables (Archaius configuration)
- ✅ Port binding is configurable (`eureka.port=8080`)
- ✅ Logging goes to stdout via log4j console appender
- ⚠️ WAR packaging needs conversion to embedded server (executable JAR) or containerized servlet container
- ⚠️ Static web resources (JSP pages in `eureka-resources`) require a servlet container capable of JSP compilation

**Recommended Container Orchestration Platform:**
**Amazon EKS** (per user preferences favoring `eks`). EKS provides Kubernetes-native orchestration with managed control plane, aligning with Eureka's peer-to-peer clustering model where multiple server instances discover each other.

**Migration Approach — Lift-and-Containerize:**
1. Create a `Dockerfile` using a JDK 8 base image (e.g., `amazoncorretto:8`) with an embedded Tomcat/Jetty
2. Convert from WAR to executable JAR with embedded servlet container, or deploy WAR into a containerized Tomcat
3. Externalize all configuration to environment variables and ConfigMaps
4. Define Kubernetes Deployment, Service, and ConfigMap manifests
5. Configure peer discovery via Kubernetes DNS or headless Service
6. Define health checks using Eureka's `/eureka/v2/status` endpoint

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS Fargate (for simplified operations), AWS App Runner (for simpler deployment model)

**Learning Resources:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
No infrastructure-as-code files exist in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize overlays. All infrastructure for running Eureka servers is presumably created manually or managed outside this repository.

**Current CI/CD State (INF-Q11 = 2):**
Three GitHub Actions workflows exist:
- `nebula-ci.yml` — Runs `./gradlew build` on push/PR with JDK 8
- `nebula-snapshot.yml` — Publishes snapshots to Maven Central on master push
- `nebula-publish.yml` — Publishes releases on tag push

These pipelines handle build and library artifact publishing but include no deployment automation, no security scanning, no integration test stage, and no deployment strategy for the running Eureka service.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment configuration exists. No blue/green, no canary, no rolling deployment. The service has no defined deployment pipeline.

**Testing Gaps (OPS-Q6 = 2):**
Integration tests exist (e.g., `EurekaClientServerRestIntegrationTest.java`) but the CI pipeline runs only `./gradlew build` which includes the default `test` task. There is no separate integration test stage, no contract testing, and no end-to-end test pipeline.

**Recommended DevOps Toolchain:**
1. **IaC:** Define EKS cluster, networking, and service configuration using Terraform or CDK (aligning with containerization pathway)
2. **CI/CD Enhancement:**
   - Add dependency vulnerability scanning (e.g., `gradle dependencyCheckAnalyze` with OWASP Dependency-Check)
   - Add SAST (e.g., Semgrep or SonarQube) to the CI pipeline
   - Add a dedicated integration test stage
   - Add container image scanning (Amazon ECR image scanning or Trivy)
3. **Deployment Pipeline:** Create a deployment pipeline using AWS CodePipeline or extend GitHub Actions with:
   - Container image build and push to ECR
   - Kubernetes manifest deployment via ArgoCD or Flux
   - Canary/blue-green deployment using Argo Rollouts or EKS-native rolling updates
4. **Observability:** Integrate OpenTelemetry for distributed tracing and CloudWatch for metrics/alarms

**Representative AWS Services:** AWS CodeBuild, AWS CodePipeline, Amazon ECR, AWS CDK, CloudFormation, Amazon CloudWatch, AWS X-Ray

**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defining compute resources exists in the repository. No `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources. No Dockerfile or container definitions. The eureka-server is packaged as a WAR file (`eureka-server/build.gradle` applies the `war` plugin) designed for deployment to a traditional servlet container. The WAR includes static web resources (JSP, CSS, JS) from `eureka-resources`. The `eureka-server-governator` module also produces a WAR with Gretty plugin for local development. |
| **Gap** | All compute is undefined in IaC — the service has no managed container orchestration or serverless deployment model. WAR packaging is a legacy deployment pattern incompatible with modern container orchestration. |
| **Recommendation** | Containerize the eureka-server WAR using Amazon EKS (per preferences). Create a Dockerfile with JDK 8 base image and embedded servlet container. Define EKS Deployment, Service, and ConfigMap resources. Migrate from WAR to executable JAR with embedded Tomcat/Jetty for container-native deployment. |
| **Evidence** | `eureka-server/build.gradle` (war plugin), `eureka-server-governator/build.gradle` (war plugin, gretty plugin), `eureka-server/src/main/webapp/WEB-INF/web.xml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. Eureka uses an in-memory instance registry (`AbstractInstanceRegistry` backed by `ConcurrentHashMap`) with no persistent data store. `has_persistent_data_store=false`. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No dedicated workflow orchestration service (Step Functions, Temporal, Camunda) is used. The server has multi-step processes implemented entirely in application code: peer registry sync on startup (`syncUp()` in `PeerAwareInstanceRegistryImpl`), peer-to-peer replication (`replicateToPeers()`), self-preservation threshold updates (`scheduleRenewalThresholdUpdateTask()`), and AWS connection priming (`primeAwsReplicas()`). The replication batching system (`util/batcher/`) implements a complex task dispatch and retry mechanism entirely in code. |
| **Gap** | Multi-step workflow logic (peer sync, replication, self-preservation) is entirely hardcoded in application code with no dedicated orchestration service. This makes workflows harder to monitor, debug, and evolve. The replication batcher in particular implements retry, batching, and error handling patterns that would benefit from managed orchestration. |
| **Recommendation** | For the stateful-crud archetype, introduce AWS Step Functions or EventBridge Pipes to orchestrate the peer replication and registry sync workflows. This would provide visual workflow management, configurable retry policies, and error handling without custom code. Start with the `syncUp()` flow which has explicit retry logic (`getRegistrySyncRetries()`, `getRegistrySyncRetryWaitMs()`). |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (syncUp, replicateToPeers, scheduleRenewalThresholdUpdateTask), `eureka-core/src/main/java/com/netflix/eureka/util/batcher/` (TaskDispatchers, TaskExecutors, AcceptorExecutor) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure exists. No SQS, SNS, EventBridge, MSK, Kinesis, or Amazon MQ. Peer replication between Eureka server nodes uses synchronous HTTP (`PeerEurekaNode` calls peer endpoints directly via Jersey HTTP client). State changes (registrations, cancellations, heartbeats, status updates) are propagated to all peers via synchronous HTTP `replicateToPeers()`. The replication batcher (`util/batcher/`) provides some decoupling but is an in-process queue, not a managed messaging system. |
| **Gap** | No messaging where cross-service state changes (peer replication) could benefit from async patterns. Synchronous peer replication creates tight coupling between Eureka server instances — if a peer is slow or unreachable, replication calls block or fail, affecting the originating server's throughput. |
| **Recommendation** | Introduce Amazon EventBridge (per preferences) for peer state change propagation. Publish registration/cancellation/status events to an EventBridge event bus, and have each Eureka server instance subscribe to relevant events. This decouples peer replication from the request path, improving resilience when peers are unreachable. For the batch replication flow, SQS with batching would provide a managed replacement for the custom `AcceptorExecutor` batcher. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (replicateToPeers), `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-core/src/main/java/com/netflix/eureka/util/batcher/AcceptorExecutor.java` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defining VPC, subnets, security groups, NACLs, or network segmentation. No `aws_vpc`, `aws_subnet`, or `aws_security_group` resources. No evidence of network topology configuration. The application code references AWS concepts (availability zones, regions, EIPs in `AwsAsgUtil`, `EIPManager`, `Route53Binder`) but no infrastructure definitions exist in the repository. |
| **Gap** | Services would be deployed with no defined network security posture. Without VPC configuration, there is no network segmentation, no private subnet isolation, and no security group rules to limit traffic. |
| **Recommendation** | Define VPC infrastructure in IaC (Terraform or CDK) with private subnets for Eureka server instances, security groups allowing only necessary ports (8080 for client traffic, peer replication ports), and VPC endpoints for AWS service access. Deploy Eureka servers in private subnets behind an API Gateway (per preferences favoring `api-gateway`) or internal ALB. |
| **Evidence** | Repository-wide scan: no `.tf`, `.cfn.yaml`, `cdk.json`, or Helm chart files found. `eureka-core/src/main/java/com/netflix/eureka/aws/EIPManager.java`, `eureka-core/src/main/java/com/netflix/eureka/aws/Route53Binder.java` (AWS networking concepts in code but no IaC) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront configuration exists. The eureka-server exposes its REST API directly via a Jersey servlet filter configured in `web.xml`. The `RateLimitingFilter` provides basic rate limiting but is commented out in the default `web.xml` configuration. No throttling, authentication, or request validation at the gateway level. |
| **Gap** | Services are exposed directly with no gateway or load balancer providing throttling, authentication, request validation, or traffic management. |
| **Recommendation** | Deploy Amazon API Gateway (per preferences) as the entry point for Eureka client traffic. API Gateway provides throttling, request validation, and a centralized authentication point. For internal peer replication traffic, use VPC Lattice or an internal ALB. |
| **Evidence** | `eureka-server/src/main/webapp/WEB-INF/web.xml` (Jersey filter, commented-out rate limiter), `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or equivalent resources. No ASG, ECS service scaling, or Lambda concurrency settings. The application code references ASGs (`AwsAsgUtil` queries ASG status for registered instances) but does not define scaling for Eureka itself. All capacity would be statically provisioned. |
| **Gap** | No auto-scaling — all capacity is statically provisioned. The Eureka server cannot respond to traffic spikes (e.g., mass re-registration events during deployments) or scale down during low demand. |
| **Recommendation** | After containerization (Move to Containers pathway), configure Horizontal Pod Autoscaler (HPA) in EKS based on request rate metrics or custom CloudWatch metrics (registrations per minute, active lease count). |
| **Evidence** | Repository-wide scan: no auto-scaling IaC found. `eureka-core/src/main/java/com/netflix/eureka/aws/AwsAsgUtil.java` (ASG queries for registered instances, not self-scaling) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. Eureka uses an in-memory registry that is rebuilt from peer nodes and client re-registrations on restart. `has_persistent_data_store=false` and `has_at_rest_data_surface=false`. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (syncUp rebuilds registry from peers) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. `has_deployed_workload=false` — no IaC defines deployable compute, and no deployment manifests exist. The application code supports multi-AZ deployment (region/AZ-aware peer discovery, EIP binding, Route 53 DNS), but no infrastructure definitions exist to evaluate. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Repository-wide scan: no deployment manifests. `eureka-core/src/main/java/com/netflix/eureka/EurekaBootStrap.java` (AWS-aware initialization), `eureka-server/src/main/resources/eureka-client.properties` (commented AZ configuration examples) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository. No Terraform (`.tf`), CloudFormation templates, CDK stacks, Helm charts, Kustomize overlays, or Ansible playbooks. The repository contains only application source code, Gradle build files, and CI/CD workflow definitions. All infrastructure for running Eureka servers is either managed outside this repository or created manually. |
| **Gap** | No IaC — all infrastructure would be created manually (ClickOps). This means infrastructure changes are non-reproducible, non-auditable, and cannot be version-controlled. Disaster recovery requires manual reconstruction of the entire environment. |
| **Recommendation** | Adopt IaC using Terraform or AWS CDK. Define the complete Eureka deployment infrastructure: EKS cluster (per preferences), networking (VPC, subnets, security groups), API Gateway, CloudWatch alarms, and IAM roles. Store IaC alongside the application code in this repository or in a dedicated infrastructure repository. |
| **Evidence** | Repository-wide scan: `find . -name "*.tf" -o -name "*.cfn.yaml" -o -name "cdk.json" -o -name "Chart.yaml" -o -name "kustomization.yaml"` — no results |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Three GitHub Actions workflows exist: (1) `nebula-ci.yml` runs `./gradlew --info --stacktrace build` on push/PR with JDK 8 and Gradle caching; (2) `nebula-snapshot.yml` publishes snapshots to Maven Central on master push; (3) `nebula-publish.yml` publishes candidate/release artifacts on tag push. These pipelines automate build and library artifact publishing but include no deployment automation, no security scanning, no dedicated test stages, and no IaC deployment. |
| **Gap** | Build is automated but deployment is absent. No pipeline deploys the Eureka service itself — pipelines only publish library JARs/WARs to Maven Central. No security scanning steps (SAST, dependency scanning) in any pipeline. No IaC deployment pipeline. |
| **Recommendation** | Extend the CI/CD pipeline to include: (1) Dependency vulnerability scanning (OWASP Dependency-Check or Snyk); (2) SAST scanning (Semgrep or SonarQube); (3) Container image build and push to ECR; (4) Deployment to EKS via ArgoCD or Flux; (5) IaC validation and apply stages. |
| **Evidence** | `.github/workflows/nebula-ci.yml`, `.github/workflows/nebula-snapshot.yml`, `.github/workflows/nebula-publish.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Java 8 with `sourceCompatibility=1.8` and `targetCompatibility=1.8` (`.netflixoss` jdk=1.8, `build.gradle`). Compound legacy signals across all three axes: **Language:** Java 8 (approaching EOL for many LTS support programs). **Frameworks:** Primary dependencies use Jersey 1 (1.19.1) — a legacy JAX-RS implementation (com.sun.jersey). Jersey 2 (2.23.1) variants exist as alternative modules but are not the default. Archaius 0.7.6, Servo 0.12.21, Governator 1.17.5 — all legacy Netflix OSS libraries. **AWS SDK:** AWS SDK v1 (1.11.277) — `com.amazonaws:aws-java-sdk-core`, `aws-java-sdk-ec2`, `aws-java-sdk-autoscaling`, `aws-java-sdk-sts`, `aws-java-sdk-route53`. Jackson 2.10.5 (several minor versions behind). XStream 1.4.19 (legacy XML serialization). |
| **Gap** | Java 8 + Jersey 1 + AWS SDK v1 is a compound legacy signal. Java 8 limits access to modern language features, performance improvements, and will lose extended support. Jersey 1 (com.sun.jersey) is unmaintained and blocks migration to Jakarta EE. AWS SDK v1 lacks async clients, HTTP/2 support, and newer AWS service integrations available in SDK v2. |
| **Recommendation** | Plan a phased migration: (1) Upgrade to Java 17+ (LTS) with Amazon Corretto; (2) Complete migration from Jersey 1 to Jersey 2/3 or Jakarta RESTful Web Services — the jersey2 variant modules already exist; (3) Migrate from AWS SDK v1 to v2 (software.amazon.awssdk); (4) Replace legacy Netflix OSS libraries (Archaius, Servo, Governator) with modern alternatives (Spring Cloud Config or AWS AppConfig, Micrometer, Guice/Spring DI). |
| **Evidence** | `build.gradle` (sourceCompatibility=1.8, awsVersion='1.11.277', jerseyVersion='1.19.1', servoVersion='0.12.21', archaiusVersion='0.7.6'), `.netflixoss` (jdk=1.8), `eureka-core/build.gradle` (AWS SDK v1 deps), `eureka-client/build.gradle` (Jersey 1 deps) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The repository is a multi-module Gradle project with 10 modules that compile into a single deployable WAR. The modules have clear, well-defined boundaries: `eureka-client` (service discovery client), `eureka-core` (server-side business logic, registry, replication), `eureka-server` (WAR assembly with web.xml), `eureka-resources` (static web assets). The dependency chain is clean and unidirectional: eureka-client → eureka-core → eureka-server (no circular dependencies). Jersey 2 alternative modules (eureka-client-jersey2, eureka-core-jersey2) demonstrate interface-based module boundaries — they provide alternative transport implementations without changing business logic. The InstanceRegistry interface hierarchy provides clean abstraction: `InstanceRegistry` → `PeerAwareInstanceRegistry` → `AbstractInstanceRegistry` → `PeerAwareInstanceRegistryImpl` → `AwsInstanceRegistry`. |
| **Gap** | The modules compile to a single WAR deployment, which means they cannot be scaled or deployed independently. However, for a service discovery server, this is architecturally appropriate — the registry, replication, and API are tightly coupled by design. |
| **Recommendation** | No decomposition needed. The modular monolith with clear module boundaries is the correct architecture for a service discovery server. Focus modernization efforts on containerization and infrastructure maturity rather than decomposition. |
| **Evidence** | `settings.gradle` (10 modules), `build.gradle` (subproject configuration), `eureka-server/build.gradle` (WAR assembly, depends on eureka-client + eureka-core), `eureka-core/build.gradle` (depends on eureka-client) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All communication is synchronous HTTP. **Client-to-server:** DiscoveryClient uses synchronous HTTP via Jersey client (`JerseyApplicationClient`, `AbstractJerseyEurekaHttpClient`) for registration, heartbeat, and registry fetches. **Server-to-server:** Peer replication uses synchronous HTTP calls (`PeerEurekaNode.register()`, `.cancel()`, `.heartbeat()`, `.statusUpdate()`). The replication batcher (`util/batcher/`) provides in-process task queuing but the actual network calls remain synchronous HTTP. Remote region registry polling (`RemoteRegionRegistry`) is also synchronous HTTP-based. No async messaging patterns exist anywhere in the codebase — no SQS, SNS, EventBridge, or message queue consumers. |
| **Gap** | For the stateful-crud archetype, synchronous-only communication where cross-service state changes (peer replication across multiple server nodes) could benefit from async patterns represents a gap. When peer nodes are slow or unreachable, synchronous replication blocks or fails, potentially cascading to affect client request handling. |
| **Recommendation** | Introduce async patterns for peer replication: publish state change events (register, cancel, status update) to Amazon EventBridge or SQS, with each peer Eureka server subscribing to these events. Keep client-facing read APIs (GET /apps) synchronous as they are latency-sensitive. This separates the write-replication path from the read-serving path. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (sync HTTP replication), `eureka-client/src/main/java/com/netflix/discovery/shared/transport/jersey/AbstractJerseyEurekaHttpClient.java` (sync HTTP client), `eureka-core/src/main/java/com/netflix/eureka/registry/RemoteRegionRegistry.java` (sync HTTP polling) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The server has some background task processing but with inconsistent patterns. **Background tasks:** `TimedSupervisorTask` provides supervised execution of recurring tasks with exponential backoff on failure — used for cache refresh, heartbeat renewal, and instance info replication in the client. **Registry sync:** `syncUp()` can be long-running for large registries (retries with configurable delay via `getRegistrySyncRetries()` and `getRegistrySyncRetryWaitMs()`). **AWS priming:** `primeAwsReplicas()` contains a blocking while-loop with Thread.sleep that can run indefinitely until all peers are contactable. **Scheduled tasks:** `scheduleRenewalThresholdUpdateTask()` uses java.util.Timer for periodic renewal threshold updates. However, there is no explicit async job pattern with status polling or callbacks for any of these long-running operations. |
| **Gap** | Some background job processing exists (TimedSupervisorTask, Timer-based scheduling) but patterns are inconsistent. The `syncUp()` and `primeAwsReplicas()` methods are blocking synchronous operations without status polling or timeout bounds (primeAwsReplicas loops until success). No formal async job infrastructure. |
| **Recommendation** | Refactor long-running operations to use managed orchestration: (1) Replace `primeAwsReplicas()` blocking loop with a Step Functions workflow that retries with configurable backoff; (2) Add timeout bounds and status reporting to `syncUp()` — expose a /status/sync endpoint for monitoring; (3) Standardize background tasks on a single pattern (either TimedSupervisorTask everywhere or ScheduledExecutorService). |
| **Evidence** | `eureka-client/src/main/java/com/netflix/discovery/TimedSupervisorTask.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (syncUp, primeAwsReplicas, scheduleRenewalThresholdUpdateTask) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Consistent URL path versioning is implemented across all JAX-RS resources. `ApplicationsResource` uses `@Path("/{version}/apps")`, `PeerReplicationResource` uses `@Path("/{version}/peerreplication")`. The `Version` enum (`Version.java`) supports V1 and V2 with a `toEnum()` parser that defaults to V2. `CurrentRequestVersion` thread-local tracks the version per request. The response cache keys include version (`Key` constructor takes `CurrentRequestVersion.get()`), ensuring version-specific responses. Client-side, endpoints use `/v2/` path (e.g., `eureka.serviceUrl.default=http://localhost:8080/eureka/v2/`). |
| **Gap** | None — versioning is consistently applied with backward compatibility (V1 to V2 conversion support). |
| **Recommendation** | Maintain the current versioning strategy. When containerizing and adding API Gateway, propagate the URL path versioning through the gateway configuration. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (@Path("/{version}/apps")), `eureka-core/src/main/java/com/netflix/eureka/resources/PeerReplicationResource.java` (@Path("/{version}/peerreplication")), `eureka-core/src/main/java/com/netflix/eureka/Version.java`, `eureka-server/src/main/resources/eureka-client.properties` (eureka.serviceUrl.default=.../v2/) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Eureka IS a service discovery system — it provides service registration and discovery for client applications. However, for the Eureka server's own peer discovery and configuration, endpoints are configured via static properties: `eureka.serviceUrl.default=http://localhost:8080/eureka/v2/` in `eureka-client.properties`. The server supports DNS-based peer discovery (`eureka.shouldUseDns=true` with `eureka.eurekaServer.domainName`) as an alternative to static URLs, but the default configuration uses static URLs. AWS deployments can use AZ-specific service URLs. No Consul, Istio, or AWS Cloud Map integration for the server's own discovery. |
| **Gap** | Environment variables/properties for endpoints with no dynamic discovery for the server's own peers. The default configuration uses hard-coded static URLs (`eureka.serviceUrl.default`). While DNS-based discovery is available as an option, it requires external DNS infrastructure configuration. |
| **Recommendation** | When deploying on EKS (per containerization pathway), use Kubernetes headless Services for peer discovery. Each Eureka server instance can discover peers via DNS SRV records from the headless Service. This replaces static `eureka.serviceUrl` configuration with dynamic Kubernetes-native discovery. |
| **Evidence** | `eureka-server/src/main/resources/eureka-client.properties` (eureka.serviceUrl.default, eureka.shouldUseDns), `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/DnsTxtRecordClusterResolver.java` (DNS-based discovery), `eureka-examples/conf/sample-eureka-client.properties` (static serviceUrl) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 buckets, document storage, or unstructured data management. Eureka deals exclusively with structured instance registration metadata (application name, host, port, status, health check URL) stored in memory. The only file-based content is static web resources (JSP, CSS, JS) in `eureka-resources` used for the dashboard UI — these are not application data requiring S3 or parsing. |
| **Gap** | No unstructured data management capability. All data is structured instance metadata in memory with no document storage or parsing pipeline. |
| **Recommendation** | Not a priority for a service discovery server. If operational logs or audit trails need persistence, store them in S3 with lifecycle policies. This is lower priority than infrastructure and security gaps. |
| **Evidence** | `eureka-resources/src/main/resources/` (static web resources only — JSP, CSS, JS), `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (in-memory structured data only) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Eureka has a clean, well-defined registry abstraction hierarchy that serves as a unified data access layer. The interface chain is: `LeaseManager` + `LookupService` → `InstanceRegistry` → `PeerAwareInstanceRegistry` → `AbstractInstanceRegistry` (base implementation) → `PeerAwareInstanceRegistryImpl` → `AwsInstanceRegistry`. All data access goes through this single interface — registration, renewal, cancellation, status updates, and queries. The `ResponseCache` (`ResponseCacheImpl`) provides a caching layer over registry queries, separating read performance from write consistency. No module bypasses the registry interface to access data directly. |
| **Gap** | None — the data access pattern is exemplary. Single point of data contract via the `InstanceRegistry` interface. |
| **Recommendation** | Maintain the current clean data access abstraction. This architecture is well-suited for future enhancements like adding a persistent backing store without changing consumer code. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/InstanceRegistry.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No database engines are used. Eureka stores all data in-memory using `ConcurrentHashMap`-based data structures in `AbstractInstanceRegistry`. There are no database engine versions to pin, no EOL concerns, and no version management requirements. The in-memory design is intentional — Eureka servers rebuild their registry from peer nodes and client re-registrations on restart. |
| **Gap** | None — no database engines exist to introduce EOL or version management concerns. |
| **Recommendation** | No action needed. The in-memory design is architecturally appropriate for a service discovery registry where availability and speed are prioritized over durability. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (ConcurrentHashMap-based registry), no database-related dependencies in any `build.gradle` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the Java application layer. No database exists, so there is no database-coupled logic. The registry operations (register, renew, cancel, status update, eviction) are all implemented in `AbstractInstanceRegistry` and `PeerAwareInstanceRegistryImpl` as pure Java methods. |
| **Gap** | None — all business logic is in the application layer. |
| **Recommendation** | No action needed. Continue keeping all business logic in the application layer. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (all CRUD logic in Java), no `.sql` files or database migration files in the repository |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration. No `aws_cloudtrail` in IaC (no IaC exists). The application uses log4j for operational logging (`log4j.properties` in `eureka-server` and `eureka-server-governator` configure console output at INFO level). SLF4J/LoggerFactory is used throughout the codebase for application logging. The `ServerRequestAuthFilter` logs client identity headers (name, version) via Servo `DynamicCounter` for monitoring, but this is operational metrics, not immutable audit logging. No log file validation, no immutable storage, no structured audit trail. |
| **Gap** | No CloudTrail or equivalent audit logging. Application logs go to stdout via log4j with no immutable storage, no log file validation, and no audit-specific log streams. Actions (registrations, cancellations, status changes) are logged at DEBUG/INFO level but not in an audit-grade format. |
| **Recommendation** | Enable AWS CloudTrail for API-level audit logging. Configure application-level audit logging: (1) Add structured JSON logging for all registry mutations (register, cancel, status update) with timestamp, client identity, action, and outcome; (2) Ship logs to CloudWatch Logs with retention policies; (3) Enable log integrity validation with S3 Object Lock for compliance. |
| **Evidence** | `eureka-server/src/main/resources/log4j.properties` (console appender only), `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (logs client identity headers as metrics) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. `has_at_rest_data_surface=false`. All data is stored in-memory and is ephemeral. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Repository-wide scan: no S3, RDS, DynamoDB, EBS, or persistent storage resources defined |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-request authentication with OAuth2/JWT. The `ServerRequestAuthFilter` configured in `web.xml` only logs client identity headers (`DiscoveryIdentity-Name`, `DiscoveryIdentity-Version`) — it does not enforce authentication. The filter calls `chain.doFilter(request, response)` unconditionally, passing all requests through regardless of identity. No Cognito, OAuth2, JWT, or API key validation exists. The `RateLimitingFilter` provides rate limiting but is commented out in the default `web.xml` configuration and does not provide authentication. |
| **Gap** | No API authentication — all endpoints are effectively open. Any client that can reach the Eureka server on the network can register instances, modify status, query the registry, or trigger peer replication. This is a significant security gap for a production service discovery system. |
| **Recommendation** | Implement API authentication: (1) Deploy Amazon API Gateway (per preferences) with Cognito authorizer or Lambda authorizer for client traffic; (2) Add mutual TLS (mTLS) for peer-to-peer replication traffic; (3) Alternatively, integrate a JWT validation filter in the Jersey pipeline for direct-access scenarios. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (logs identity but does not enforce auth), `eureka-server/src/main/webapp/WEB-INF/web.xml` (requestAuthFilter configuration, commented-out rateLimitingFilter) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No integration with a centralized identity provider. No Cognito, OIDC, SAML, Okta, or Ping configuration. The `ServerRequestAuthFilter` reads custom Eureka identity headers (`DiscoveryIdentity-Name`, `DiscoveryIdentity-Version`) but these are informational — not tied to any identity provider or SSO system. No SSO, no federated identity, no external IdP integration. |
| **Gap** | Application manages its own (non-enforcing) identity detection with no external IdP integration. No centralized identity governance. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. When deploying behind API Gateway (per API Entry Point recommendation), use Cognito user pools for client authentication and IAM roles for service-to-service authorization. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java` (AUTH_NAME_HEADER_KEY, AUTH_VERSION_HEADER_KEY — custom headers, not IdP integration) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials are committed to the repository. The `.gitignore` excludes `secrets/signing-key`. CI/CD workflows use GitHub Secrets properly (`${{ secrets.ORG_SIGNING_KEY }}`, `${{ secrets.ORG_SIGNING_PASSWORD }}`, `${{ secrets.ORG_SONATYPE_USERNAME }}`, etc.). However, the application code reads AWS credentials from properties via `getAWSAccessId()` and `getAWSSecretKey()` in `DefaultEurekaServerConfig.java` (reads from `eureka.awsAccessId` and `eureka.awsSecretKey` properties). In `AwsAsgUtil.java`, these credentials are used to create `BasicAWSCredentials` objects. There is also an `InstanceProfileCredentialsProvider` path as an alternative, but the static credentials path remains available. The `getRemoteRegionTrustStorePassword()` method returns a default password of `"changeit"`. No Secrets Manager or Vault integration exists. |
| **Gap** | No plaintext credentials in source, but production AWS credentials are read from properties/environment variables without rotation or a dedicated secrets management system. The `BasicAWSCredentials` usage with static access keys is a legacy pattern. The hardcoded default trust store password (`"changeit"`) is a minor concern. |
| **Recommendation** | (1) Remove the static AWS credentials path (`getAWSAccessId()`/`getAWSSecretKey()`) and require IAM instance profiles or IRSA (IAM Roles for Service Accounts) on EKS; (2) Migrate any remaining secrets to AWS Secrets Manager with automated rotation; (3) Remove the hardcoded `"changeit"` default password. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (getAWSAccessId, getAWSSecretKey, getRemoteRegionTrustStorePassword), `eureka-core/src/main/java/com/netflix/eureka/aws/AwsAsgUtil.java` (BasicAWSCredentials usage), `.gitignore` (secrets/signing-key exclusion), `.github/workflows/nebula-publish.yml` (GitHub Secrets usage) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No evidence of compute hardening or patching strategy. No SSM Patch Manager, no AWS Inspector, no vulnerability scanning, no hardened base images. The CI builds on `ubuntu-latest` with Zulu JDK 8 (`actions/setup-java`) but no hardened base image or patching configuration for the runtime environment. No EC2 Image Builder pipelines or Bottlerocket references. |
| **Gap** | No patching strategy, no vulnerability scanning, no hardened base images. The runtime environment's security posture is entirely unknown. |
| **Recommendation** | When containerizing (Move to Containers pathway): (1) Use Amazon Corretto or Bottlerocket as the base image; (2) Enable Amazon ECR image scanning; (3) Configure SSM Patch Manager for any remaining EC2 instances; (4) Add container vulnerability scanning (Trivy or Snyk) to the CI pipeline. |
| **Evidence** | `.github/workflows/nebula-ci.yml` (ubuntu-latest runner, no security scanning), repository-wide scan: no SSM, Inspector, or hardening configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into any CI/CD pipeline. The `nebula-ci.yml` workflow runs only `./gradlew build` — no security scanning steps. No Dependabot configuration (`.github/dependabot.yml` does not exist). No SonarQube, Semgrep, CodeGuru Reviewer, or OWASP Dependency-Check. No `.snyk` policy file. No container scanning (no containers exist). The project has known outdated dependencies: XStream 1.4.19 (has had CVEs), Jackson 2.10.5 (multiple versions behind), Jersey 1.19.1 (unmaintained), Jetty 7.2.0 (very old test dependency). |
| **Gap** | No security scanning tools configured — no Dependabot, no SAST, no container scanning. Pipeline has no security validation step. Known outdated dependencies (XStream, Jackson, Jersey 1, Jetty) may have undetected vulnerabilities. |
| **Recommendation** | (1) Add Dependabot configuration for Gradle dependency updates; (2) Add OWASP Dependency-Check (`gradle dependencyCheckAnalyze`) or Snyk to the CI pipeline; (3) Add SAST scanning (Semgrep or SonarQube); (4) Configure security gates to block builds on critical/high findings; (5) Audit current dependencies for known CVEs — particularly XStream, Jackson, and Jetty. |
| **Evidence** | `.github/workflows/nebula-ci.yml` (no security steps), repository-wide scan: no `.github/dependabot.yml`, no `.snyk`, no SonarQube configuration. `build.gradle` (outdated dependency versions: xstream 1.4.19, jackson 2.10.5, jetty 7.2.0) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No OpenTelemetry SDK, X-Ray agent, or Zipkin integration in dependency manifests or source code. No `traceparent` or `X-Amzn-Trace-Id` header propagation. The codebase uses Netflix Servo (`servo-core`) for internal metrics (counters, gauges, timers via `@Monitor` annotations and `EurekaMonitors` enum), but Servo is a metrics library, not a tracing framework. No trace context propagation across peer replication or client-server communication. |
| **Gap** | No distributed tracing instrumented. Debugging failures across peer replication boundaries, client-server interactions, and remote region communication is guesswork. Without trace propagation, correlating a client registration request to its peer replication across multiple Eureka servers is impossible. |
| **Recommendation** | Instrument with OpenTelemetry Java SDK: (1) Add `opentelemetry-javaagent` or manual instrumentation; (2) Propagate trace context (W3C `traceparent` header) across peer replication HTTP calls in `PeerEurekaNode`; (3) Export traces to AWS X-Ray or a CloudWatch-compatible backend; (4) Add trace-aware logging (trace ID in log lines). |
| **Evidence** | `eureka-core/build.gradle` (servo-core dependency, no tracing dependency), `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (Servo metrics only), `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (no trace header propagation) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions, no error budget tracking, no latency alarms. The server has a self-preservation mode (`shouldEnableSelfPreservation()`) that prevents lease expiration when renewal rates drop below a configurable threshold (`getRenewalPercentThreshold()` defaults to 85%) — this is a basic availability protection mechanism but not a formal SLO definition. No CloudWatch alarms on p99/p95 latency. No SLO configuration files. No error budget dashboards. `has_api_surface=true`, so this question applies. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for the service discovery API. Without SLOs, there is no objective measure of whether Eureka is meeting its availability and latency requirements. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Registry query latency (GET /v2/apps) — target p99 < 100ms; (2) Registration success rate — target 99.9%; (3) Heartbeat renewal success rate — target 99.99%; (4) Peer replication lag — target < 5 seconds. Implement with CloudWatch metrics, alarms, and dashboards. Track error budgets to prioritize reliability investments. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (getRenewalPercentThreshold — basic availability threshold, not SLO), no SLO definition files found |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Netflix Servo is used for custom operational metrics: `EurekaMonitors` enum defines 20+ counters including RENEW, CANCEL, REGISTER, EXPIRED, GET_ALL, GET_APPLICATION, STATUS_UPDATE, RATE_LIMITED, FAILED_REPLICATIONS, REJECTED_REPLICATIONS. `@Monitor` annotations on `PeerAwareInstanceRegistryImpl` track localRegistrySize, numOfReplicationsInLastMin, isBelowRenewThreshold, isLeaseExpirationEnabled, shouldAllowAccess. `AwsAsgUtil` tracks numOfElementsinASGCache, numOfASGQueries, numOfASGQueryFailures. `MetricsCollectingEurekaHttpClient` tracks HTTP transport metrics. These are infrastructure/operational metrics — they measure system internals, not business outcomes. |
| **Gap** | Infrastructure/operational metrics only via Netflix Servo. No business outcome metrics (e.g., service discovery resolution success rate per consumer application, time-to-discovery for new registrations, impact of service discovery failures on downstream services). |
| **Recommendation** | Migrate from Netflix Servo to Micrometer for modern metrics support. Add business outcome metrics: (1) Service discovery resolution rate by consumer application; (2) Registration-to-availability latency (time from registration to appearing in registry queries); (3) Stale registration rate (registrations not renewed within expected interval). Publish to CloudWatch custom metrics for dashboarding and alerting. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (@Monitor annotations), `eureka-client/src/main/java/com/netflix/discovery/shared/transport/decorator/MetricsCollectingEurekaHttpClient.java` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudWatch anomaly detection, no alerting configuration, no alarms defined. No PagerDuty, OpsGenie, or SNS alerting integration. The self-preservation mode provides a basic anomaly detection mechanism (detects when renewal rates drop below threshold), but this is an in-application safety mechanism, not operational alerting infrastructure. No alarm definitions in IaC (no IaC exists). No composite alarms. |
| **Gap** | No alerting configured. There is no mechanism to notify operators of Eureka server issues — high error rates, replication failures, registry size anomalies, or self-preservation activation would go undetected until client applications experience service discovery failures. |
| **Recommendation** | Define CloudWatch alarms for: (1) Eureka self-preservation mode activation (critical); (2) Replication failure rate (FAILED_REPLICATIONS metric); (3) Registration/cancellation rate anomalies; (4) Registry size changes beyond normal bounds; (5) Response latency p99 exceeding thresholds. Configure SNS topics for alarm notifications. |
| **Evidence** | Repository-wide scan: no alarm definitions, no alerting configuration. `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (self-preservation mechanism — in-app only) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment configuration found. No CodeDeploy, Helm canary, Argo Rollouts, Lambda traffic shifting, or ALB weighted target groups. The CI/CD pipelines publish library artifacts to Maven Central but do not deploy the Eureka service. No deployment strategy is defined for transitioning between server versions. Shell scripts exist (`eureka-server/runclient.sh`, `eureka-server/runservice.sh`) but these are local development convenience scripts, not deployment automation. |
| **Gap** | Direct-to-production deployment with no staged rollout capability. A Eureka server upgrade would require manual deployment with no canary, blue/green, or rolling update strategy — risking service discovery outages during version transitions. |
| **Recommendation** | After containerization on EKS (Move to Containers pathway), implement a rolling update deployment strategy with Kubernetes-native rolling updates as a baseline, then evolve to canary deployments using Argo Rollouts. Eureka's peer-aware architecture makes rolling updates natural — new version instances join the peer group while old ones drain. |
| **Evidence** | `.github/workflows/` (publish only, no deployment), `eureka-server/runclient.sh`, `eureka-server/runservice.sh` (local development scripts) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Integration tests exist but coverage is limited. `EurekaClientServerRestIntegrationTest.java` in `eureka-server` is a full integration test that starts an embedded Jetty server with the eureka WAR and exercises the REST API (register, heartbeat, status update, batch replication). It depends on the WAR being built (`test.dependsOn war`). Other test infrastructure includes `MockRemoteEurekaServer` for client-side testing, `SimpleEurekaHttpServer` for transport testing, and `InstanceInfoGenerator` for test data. Tests use JUnit 4, Mockito 3.4.0, MockServer 3.9.2, and WireMock 2.25.1. The CI pipeline runs `./gradlew build` which includes the `test` task, so tests execute in CI. However, there is no separate integration test stage, no contract testing, and test coverage is not measured in the pipeline. |
| **Gap** | Some integration tests exist and run in CI (via `./gradlew build`), but they are mixed with unit tests — no dedicated integration test stage. No contract tests for the REST API. No end-to-end testing with multiple Eureka peers. No test coverage reporting in the pipeline. |
| **Recommendation** | (1) Separate integration tests into a dedicated Gradle task and CI stage; (2) Add contract tests for the REST API (e.g., using Pact or Spring Cloud Contract); (3) Add multi-peer integration tests that validate peer replication behavior; (4) Add test coverage reporting (JaCoCo) to the CI pipeline. |
| **Evidence** | `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`, `eureka-server/build.gradle` (test.dependsOn war), `eureka-client/src/test/java/com/netflix/discovery/MockRemoteEurekaServer.java`, `.github/workflows/nebula-ci.yml` (./gradlew build includes tests) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No self-healing patterns beyond the built-in self-preservation mode. No incident response documentation in the repository. The wiki is referenced in README but exists externally and does not contain runbook content (based on the in-repo reference). |
| **Gap** | No runbooks — incident response is entirely ad hoc. When Eureka servers experience issues (split-brain, replication failures, registry corruption), operators have no documented or automated response procedures. |
| **Recommendation** | Create operational runbooks for common failure scenarios: (1) Self-preservation mode activation — diagnose network issues vs genuine instance loss; (2) Peer replication failures — identify and remediate unreachable peers; (3) Registry inconsistency — force registry sync from healthy peer; (4) Full cluster restart procedure. Automate critical runbooks with SSM Automation documents. |
| **Evidence** | Repository-wide scan: no runbook files (markdown, YAML, JSON), no SSM documents, no remediation Lambda functions |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file, no per-service dashboards, no alarm ownership definitions, no SLO definitions with team attribution. No observability configuration files with named owners. The repository has a community-driven support model (README: "Community-driven mostly, feel free to open an issue"). No dedicated operations team or on-call rotation defined in the repository. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No team owns the operational health of Eureka. No dashboards, no alarms, no SLO ownership. |
| **Recommendation** | (1) Add a CODEOWNERS file defining ownership of operational configuration; (2) Create per-service CloudWatch dashboards for the Eureka server; (3) Define alarm ownership with named team or on-call rotation; (4) Link SLO definitions (when created) to specific team ownership. |
| **Evidence** | Repository-wide scan: no CODEOWNERS, no dashboard definitions, no alarm ownership configuration. README.md ("Community-driven mostly") |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC resources exist to tag. No `default_tags` in Terraform provider, no `tags` on CloudFormation resources, no `required-tags` Config rules. No tagging standard defined. When IaC is created (per Move to Modern DevOps pathway), tagging governance will need to be established from scratch. |
| **Gap** | No tags found on resources — because no resources are defined in IaC. When infrastructure is created, there will be no cost allocation, ownership, or environment identification without a tagging strategy. |
| **Recommendation** | When adopting IaC (per Move to Modern DevOps pathway), define a tagging standard from day one: required tags should include `Environment`, `Service` (eureka), `Team`, `CostCenter`, and `ManagedBy`. Enforce via Terraform `default_tags` block and AWS Tag Policies in Organizations. |
| **Evidence** | Repository-wide scan: no IaC resources, no tagging configuration |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `build.gradle` | INF-Q1, APP-Q1, APP-Q2, DATA-Q3, SEC-Q7 | Root Gradle config: sourceCompatibility=1.8, dependency versions (AWS SDK v1, Jersey 1/2, Jackson, Servo, Archaius) |
| `settings.gradle` | APP-Q2 | Lists all 10 Gradle modules |
| `.netflixoss` | APP-Q1 | JDK version pin: jdk=1.8 |
| `.gitignore` | SEC-Q5 | Excludes secrets/signing-key |
| `README.md` | OPS-Q8 | Community-driven support model, wiki reference |
| `eureka-server/build.gradle` | INF-Q1, APP-Q2 | WAR plugin, depends on eureka-client + eureka-core + eureka-resources |
| `eureka-server-governator/build.gradle` | INF-Q1 | WAR plugin, Gretty plugin for local dev |
| `eureka-core/build.gradle` | APP-Q1, INF-Q3 | AWS SDK v1 dependencies (ec2, autoscaling, sts, route53) |
| `eureka-client/build.gradle` | APP-Q1 | Jersey 1 (1.19.1), Archaius, Servo, XStream dependencies |
| `eureka-client-jersey2/build.gradle` | APP-Q1 | Jersey 2 (2.23.1) alternative client |
| `eureka-core-jersey2/build.gradle` | APP-Q1 | Jersey 2 alternative core |
| `.github/workflows/nebula-ci.yml` | INF-Q11, SEC-Q7, OPS-Q6 | CI pipeline: ./gradlew build, JDK 8, no security scanning |
| `.github/workflows/nebula-snapshot.yml` | INF-Q11 | Snapshot publish to Maven Central on master push |
| `.github/workflows/nebula-publish.yml` | INF-Q11, SEC-Q5 | Release publish, uses GitHub Secrets for signing |
| `eureka-server/src/main/webapp/WEB-INF/web.xml` | INF-Q1, INF-Q6, SEC-Q3 | Servlet config: EurekaBootStrap, ServerRequestAuthFilter, RateLimitingFilter (commented), Jersey filter |
| `eureka-server/src/main/resources/eureka-client.properties` | APP-Q6, INF-Q9 | Static peer URL config, AZ examples (commented) |
| `eureka-server/src/main/resources/eureka-server.properties` | — | Minimal server config |
| `eureka-server/src/main/resources/log4j.properties` | SEC-Q1 | Console-only logging at INFO level |
| `eureka-core/src/main/java/com/netflix/eureka/EurekaBootStrap.java` | INF-Q1, INF-Q9 | Server initialization, peer sync, AWS detection |
| `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` | INF-Q2, INF-Q3, INF-Q4, INF-Q8, APP-Q3, APP-Q4, OPS-Q4 | Peer replication, syncUp, self-preservation, scheduled tasks |
| `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` | INF-Q2, DATA-Q2, DATA-Q3, DATA-Q4 | In-memory ConcurrentHashMap registry, CRUD operations |
| `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java` | DATA-Q2 | Response cache layer |
| `eureka-core/src/main/java/com/netflix/eureka/registry/InstanceRegistry.java` | DATA-Q2 | Registry interface — unified data access contract |
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` | APP-Q5 | @Path("/{version}/apps") — URL path versioning |
| `eureka-core/src/main/java/com/netflix/eureka/resources/PeerReplicationResource.java` | APP-Q5 | @Path("/{version}/peerreplication") — URL path versioning |
| `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` | APP-Q3 | CRUD endpoints: GET, PUT (renew, status), DELETE (cancel), PUT (metadata) |
| `eureka-core/src/main/java/com/netflix/eureka/Version.java` | APP-Q5 | Version enum: V1, V2 |
| `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` | SEC-Q3, SEC-Q4 | Logs identity headers, does not enforce auth |
| `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` | SEC-Q5 | getAWSAccessId/getAWSSecretKey, getRemoteRegionTrustStorePassword |
| `eureka-core/src/main/java/com/netflix/eureka/aws/AwsAsgUtil.java` | INF-Q7, SEC-Q5, OPS-Q3 | ASG queries, BasicAWSCredentials, @Monitor annotations |
| `eureka-core/src/main/java/com/netflix/eureka/aws/EIPManager.java` | INF-Q5 | AWS EIP management (code only, no IaC) |
| `eureka-core/src/main/java/com/netflix/eureka/aws/Route53Binder.java` | INF-Q5 | Route 53 DNS binding (code only, no IaC) |
| `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` | INF-Q4, APP-Q3, OPS-Q1 | Synchronous HTTP peer replication, no trace propagation |
| `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` | OPS-Q1, OPS-Q3 | Servo-based operational metrics (counters for RENEW, CANCEL, REGISTER, etc.) |
| `eureka-core/src/main/java/com/netflix/eureka/util/batcher/AcceptorExecutor.java` | INF-Q3, INF-Q4 | In-process task batching for replication |
| `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` | INF-Q6 | Rate limiting filter (commented out in web.xml) |
| `eureka-client/src/main/java/com/netflix/discovery/TimedSupervisorTask.java` | APP-Q4 | Supervised background task execution with backoff |
| `eureka-client/src/main/java/com/netflix/discovery/shared/transport/jersey/AbstractJerseyEurekaHttpClient.java` | APP-Q3 | Synchronous HTTP client for client-server communication |
| `eureka-client/src/main/java/com/netflix/discovery/shared/transport/decorator/MetricsCollectingEurekaHttpClient.java` | OPS-Q3 | HTTP transport metrics collection |
| `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/DnsTxtRecordClusterResolver.java` | APP-Q6 | DNS-based peer discovery alternative |
| `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java` | SEC-Q4 | Custom identity headers (AUTH_NAME_HEADER_KEY, AUTH_VERSION_HEADER_KEY) |
| `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java` | OPS-Q6 | Full REST integration test with embedded Jetty |
| `eureka-client/src/test/java/com/netflix/discovery/MockRemoteEurekaServer.java` | OPS-Q6 | Mock server for client-side testing |
| `eureka-examples/conf/sample-eureka-client.properties` | APP-Q6 | Static eureka.serviceUrl.default example |
| `eureka-examples/conf/sample-eureka-service.properties` | APP-Q6 | Sample service registration properties |
| `eureka-server/runclient.sh` | OPS-Q5 | Local development script (not deployment automation) |
| `eureka-server/runservice.sh` | OPS-Q5 | Local development script (not deployment automation) |
