# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | eureka |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) — for eureka-server; eureka-client modules are libraries |
| **Priority** | P2 |
| **Tags** | java, service-discovery, microservices |
| **Context** | Netflix service-discovery server and client. |
| **Overall Score** | 2.29 / 4.0 |

**Archetype Justification**: The eureka-server maintains a persistent in-memory instance registry (ConcurrentHashMap) with full CRUD operations via REST API (register, renew, cancel, status update, delete). Write endpoints mutate shared state with lease management. Classified as `stateful-crud`. Client modules (eureka-client, eureka-client-jersey2, eureka-client-archaius2) are libraries with no independent deployable entry point and are not scored for archetype.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.55 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.33 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 4.00 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.14 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **2.29 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | Zero infrastructure-as-code — all infrastructure manually created (ClickOps). | No reproducible environments; disaster recovery impossible without manual reconstruction. Blocks all other modernization pathways. |
| 2 | SEC-Q3: API Authentication | 1 | ServerRequestAuthFilter only logs identity headers — does not enforce authentication. All API endpoints are open. | Unauthenticated registry API allows any client to register, deregister, or query instances. Critical security vulnerability in production. |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging infrastructure defined. | No forensic trail for registry mutations. Compliance risk and inability to trace unauthorized changes. |
| 4 | INF-Q1: Managed Compute | 1 | No managed compute defined — WAR deployment with no container or serverless infrastructure. | Server deployed to traditional servlet containers with manual capacity management. No elastic scaling or automated recovery. |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumentation — only Servo counters for aggregate metrics. | Cannot trace individual requests across Eureka server peers or client-server interactions. Debugging production issues is guesswork. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). GitHub Actions workflows (nebula-ci.yml, nebula-publish.yml, nebula-snapshot.yml) provide build and publish automation.
- **What it enables:** An agent that triggers builds, checks CI status, manages release candidates, and monitors snapshot publication to Maven Central. Could automate release notes generation from CHANGELOG.md.
- **Additional steps:** Extend CI workflows to expose build status via API or webhook for agent consumption. Consider adding GitHub Actions API integration.
- **Effort:** Low

### API-Aware Agent

- **Prerequisite:** API versioning exists (APP-Q5 = 3). Eureka exposes a RESTful API with /v2/ versioning across all endpoints (register, renew, cancel, query). Structured JSON/XML responses are well-defined via InstanceInfo and Applications models.
- **What it enables:** An agent that discovers and invokes Eureka API endpoints as tools — querying registry state, checking instance health, monitoring registration patterns, and performing administrative operations.
- **Additional steps:** Generate an OpenAPI specification from the existing JAX-RS annotations in ApplicationsResource.java, ApplicationResource.java, and InstanceResource.java for full agent tool discovery.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists. README.md references the [Eureka wiki](https://github.com/Netflix/eureka/wiki) for detailed documentation. Inline Javadoc is comprehensive across the codebase (AbstractInstanceRegistry, PeerAwareInstanceRegistryImpl, DiscoveryClient).
- **What it enables:** A knowledge agent that indexes Eureka documentation and source code Javadoc to answer developer questions about configuration, deployment patterns, self-preservation mode, and peer replication behavior.
- **Additional steps:** Index the wiki content and Javadoc output. Consider using Amazon Bedrock with a knowledge base for the retrieval pipeline.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with well-defined boundaries). Primary trigger not met. |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (WAR deployment, no managed compute); no container definitions found. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures); no commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 (in-memory by design, no databases to manage). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (zero IaC); INF-Q11 = 2 (build/publish only, no deployment). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
The eureka-server is packaged as a WAR file (`eureka-server/build.gradle` applies the `war` plugin) deployed to a traditional servlet container. No Dockerfiles, docker-compose files, or Kubernetes manifests exist in the repository. The `EurekaBootStrap.java` initializes the server via `ServletContextListener`, and `web.xml` configures filter chains for a Servlet 2.5 container. There is no evidence of managed compute (no ECS, EKS, Lambda, or Fargate resources).

**Container Readiness Indicators:**
- ✅ The application has a well-defined entry point (`EurekaBootStrap` as `ServletContextListener`)
- ✅ Configuration is externalized via properties files (`eureka-client.properties`, `eureka-server.properties`) and Archaius dynamic configuration
- ✅ Port binding is configurable (`eureka.port=8080`)
- ✅ Stateless server design (in-memory registry is reconstructed via peer sync on startup)
- ⚠️ WAR packaging requires a servlet container image base (Tomcat/Jetty)
- ⚠️ No health check endpoint is explicitly defined (relies on registry self-preservation)

**Recommended Container Orchestration:**
Deploy eureka-server as a containerized application on **Amazon EKS** (per technology preferences). Use a multi-replica Kubernetes Deployment with a headless Service for peer discovery, replacing the current DNS-based or config-based peer resolution.

**Migration Approach:** Lift-and-containerize
1. Create a Dockerfile using a Tomcat or Jetty base image with JDK 8
2. Package the WAR into the container image
3. Define Kubernetes manifests (Deployment, Service, ConfigMap for properties)
4. Configure peer discovery via Kubernetes DNS (headless Service)
5. Push to Amazon ECR; deploy to EKS cluster

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS Fargate (for simplified node management), Amazon API Gateway (for external access)

**Learning Resources:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure-as-code exists in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files were found. All infrastructure for running Eureka in production must be manually created. This is the single largest modernization blocker — without IaC, deployments are non-reproducible and disaster recovery is manual.

**Current CI/CD State (INF-Q11 = 2):**
Three GitHub Actions workflows exist:
- `nebula-ci.yml` — Runs `./gradlew build` on push/PR (build + unit/integration tests)
- `nebula-publish.yml` — Publishes release/candidate artifacts to Maven Central on tag push
- `nebula-snapshot.yml` — Publishes snapshot artifacts on master push

These workflows cover build and artifact publishing but not deployment to any environment. There are no deployment pipelines, no environment promotion stages, and no rollback mechanisms.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy is defined. The repository publishes library artifacts to Maven Central but has no mechanism for deploying the eureka-server WAR to any environment.

**Testing Gaps (OPS-Q6 = 3):**
Integration tests exist (`EurekaClientServerRestIntegrationTest.java`) and run in CI via `./gradlew build`. However, there are no environment-specific tests, contract tests, or smoke tests post-deployment.

**Recommended DevOps Toolchain:**
1. **IaC:** Define EKS cluster, networking, and Eureka server deployment using AWS CDK or Terraform
2. **Container Registry:** Amazon ECR for container images
3. **CI/CD Pipeline:** Extend GitHub Actions with deployment stages or adopt AWS CodePipeline with CodeBuild
4. **Deployment Strategy:** Blue/green deployment via AWS CodeDeploy or Kubernetes rolling updates
5. **Monitoring:** Amazon CloudWatch with X-Ray for distributed tracing

**Representative AWS Services:** AWS CDK, Amazon ECR, AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy, Amazon CloudWatch, AWS X-Ray

**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defines any compute resources. The eureka-server is packaged as a WAR file (`eureka-server/build.gradle` applies the `war` plugin). No Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources exist. No Dockerfiles or Kubernetes manifests were found anywhere in the repository. The WAR artifact implies deployment to a traditional, manually-provisioned servlet container. |
| **Gap** | All compute is unmanaged — no containerization, no serverless, no IaC-defined EC2. The deployment model is a legacy WAR-to-servlet-container pattern with no cloud-native compute abstraction. |
| **Recommendation** | Containerize the eureka-server WAR and deploy to Amazon EKS (preferred). Create a Dockerfile with a Tomcat/Jetty base, define Kubernetes Deployment manifests, and leverage EKS for elastic scaling and automated recovery. |
| **Evidence** | `eureka-server/build.gradle` (war plugin), `eureka-server/src/main/webapp/WEB-INF/web.xml` (Servlet 2.5 config), absence of any `.tf`, `Dockerfile`, `Chart.yaml`, or `kustomization.yaml` files in the repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Eureka does not use an external database. The instance registry is an in-memory `ConcurrentHashMap<String, Map<String, Lease<InstanceInfo>>>` in `AbstractInstanceRegistry.java`. This is intentional for a service discovery system — the registry is ephemeral and reconstructed via peer synchronization (`PeerAwareInstanceRegistryImpl.syncUp()`). No `aws_rds_*`, `aws_dynamodb_*`, or database connection strings exist. |
| **Gap** | None. The in-memory design is appropriate for a service registry where durability comes from peer replication rather than database persistence. |
| **Recommendation** | No action needed. The in-memory registry with peer sync is the correct architecture for a service discovery system. If persistence is ever needed (e.g., for audit or recovery), consider Amazon DynamoDB (preferred) as a secondary store. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (ConcurrentHashMap registry), `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (syncUp method). |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) Eureka-server has multi-step workflow operations: peer replication involves batching tasks via `TaskDispatchers` and `AcceptorExecutor`, processing replication queues, and handling failures with retry logic. These are structured in-code state machines using `TaskDispatcher`, `ReplicationTaskProcessor`, and `PeerEurekaNode` but use no dedicated orchestration service. No Step Functions, Temporal, or equivalent workflow orchestration is present. |
| **Gap** | The batch replication workflow is a custom in-code implementation with structured retry and batching logic, but it lacks the visibility, error handling dashboards, and operational controls that a managed orchestration service provides. |
| **Recommendation** | For the peer replication workflow, consider AWS Step Functions to orchestrate replication batches with built-in retry, error handling, and observability. This would replace the custom `TaskDispatchers`/`AcceptorExecutor` implementation with managed orchestration. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/batcher/TaskDispatchers.java`, `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (batchingDispatcher, nonBatchingDispatcher), `eureka-core/src/main/java/com/netflix/eureka/cluster/ReplicationTaskProcessor.java`. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) Eureka-server uses synchronous HTTP (Jersey) for all peer-to-peer replication and client-server communication. The `JerseyReplicationClient` sends replication requests via HTTP POST. The internal `AcceptorExecutor` provides async batching of replication tasks within the JVM, but the inter-node transport is synchronous HTTP. No SQS, SNS, EventBridge, MSK, Kinesis, or Amazon MQ is used. State changes (register, cancel, renew) cross service boundaries (to peer nodes) via synchronous HTTP replication. |
| **Gap** | For a stateful-crud service, cross-service state propagation should use managed messaging. Eureka's peer replication via synchronous HTTP creates tight coupling between peers — if a peer is slow or unavailable, the replication batch blocks. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) or Amazon SQS for peer replication events. State change events (register, cancel, status update) can be published to EventBridge with peer nodes consuming events asynchronously. This decouples peers and improves resilience to individual node failures. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/transport/JerseyReplicationClient.java`, `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (synchronous replicationClient calls), absence of any `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*` in repository. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation definitions exist anywhere in the repository. No IaC files exist at all — network infrastructure must be manually created. No `aws_vpc`, `aws_subnet`, `aws_security_group`, or `aws_vpc_endpoint` resources found. |
| **Gap** | Network security is entirely undefined. Without IaC-defined network controls, Eureka server could be deployed in a default VPC or public subnet with no segmentation. |
| **Recommendation** | Define VPC infrastructure in IaC (AWS CDK or Terraform) with private subnets for Eureka server instances, least-privilege security groups (allow only Eureka client ports from known CIDR ranges), and VPC endpoints for AWS service access. |
| **Evidence** | Absence of any `.tf`, CloudFormation, or CDK files in the repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync is defined as an entry point. The Eureka server exposes its REST API directly via the servlet container (web.xml filter chain → Jersey). Clients connect directly to `http://localhost:8080/eureka/v2/` as configured in `eureka-client.properties`. |
| **Gap** | Services exposed directly without gateway or load balancer. No throttling, authentication, or request validation at the entry point. The `RateLimitingFilter` exists but is commented out in web.xml. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) or an Application Load Balancer in front of Eureka server instances. Configure throttling, authentication (Cognito/JWT authorizer), and health checks at the gateway level. |
| **Evidence** | `eureka-server/src/main/webapp/WEB-INF/web.xml` (direct Jersey servlet, rate limiter commented out), `eureka-server/src/main/resources/eureka-client.properties` (serviceUrl.default=http://localhost:8080/eureka/v2/). |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No `aws_autoscaling_*`, `aws_appautoscaling_*`, Lambda concurrency limits, or Kubernetes HPA definitions found. All capacity must be statically provisioned manually. |
| **Gap** | No auto-scaling — all capacity is statically provisioned. The Eureka server cannot respond to traffic spikes (e.g., mass registration events during deployments) without manual intervention. |
| **Recommendation** | When containerized on EKS, configure Kubernetes Horizontal Pod Autoscaler (HPA) based on custom metrics (registration rate, renewal rate from EurekaMonitors). Define minimum and maximum replica counts for the Eureka server Deployment. |
| **Evidence** | Absence of any auto-scaling configuration in the repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. Eureka's in-memory registry is ephemeral by design — it relies on peer synchronization (`PeerAwareInstanceRegistryImpl.syncUp()`) and client re-registration for recovery. However, there is no documented recovery procedure, no backup plan for any ancillary data, and no cross-region backup replication. The `backup_retention_period` parameter is not applicable since no database is used. |
| **Gap** | While the in-memory design mitigates the need for traditional backups, there is no documented disaster recovery procedure for a complete cluster loss scenario. No `aws_backup_plan` or equivalent exists. |
| **Recommendation** | Document the disaster recovery procedure for Eureka: (1) cluster bootstrap sequence, (2) expected registry re-population time via client re-registration, (3) self-preservation mode behavior during recovery. If persistent state is added in the future, configure automated backups with defined retention. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (syncUp method), absence of any backup configuration. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Eureka is architecturally designed for high availability — `PeerAwareInstanceRegistryImpl` supports peer-to-peer replication, zone-aware deployment (`eureka.us-east-1.availabilityZones` in commented-out config), and self-preservation mode to survive network partitions. However, no IaC defines multi-AZ deployment. No `multi_az`, `availability_zones`, or multi-AZ subnet configurations exist. The HA design is in the application code, but the infrastructure to realize it is absent. |
| **Gap** | The application-level HA design (peer replication, zone affinity, self-preservation) is mature, but no infrastructure defines multi-AZ deployment. The gap is entirely in the infrastructure layer. |
| **Recommendation** | Define multi-AZ EKS deployment with Eureka server replicas spread across at least 2 AZs. Configure Kubernetes anti-affinity rules to ensure peers are in different AZs. Leverage the existing zone-aware configuration (`eureka.us-east-1.availabilityZones`). |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (peer sync, self-preservation), `eureka-server/src/main/resources/eureka-client.properties` (commented-out multi-AZ config), absence of IaC multi-AZ definitions. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC coverage. No Terraform files (`.tf`), CloudFormation templates, CDK stacks, Helm charts, or Kustomize files exist in the repository. All infrastructure required to run Eureka (compute, networking, DNS, monitoring) must be created manually. |
| **Gap** | 0% IaC coverage. Infrastructure changes are manual, error-prone, and non-reproducible. This is the most critical gap — it blocks automated deployments, environment consistency, and disaster recovery. |
| **Recommendation** | Adopt IaC using AWS CDK (Java) to leverage the team's Java expertise. Define EKS cluster, VPC networking, ECR repository, and Eureka server Kubernetes manifests. Start with the deployment infrastructure and expand to monitoring, alarms, and backup plans. |
| **Evidence** | Exhaustive search for `.tf`, `.cfn.yaml`, `.cfn.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` returned zero results. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Three GitHub Actions workflows exist: `nebula-ci.yml` runs `./gradlew build` (compile + test) on push/PR; `nebula-publish.yml` publishes releases to Maven Central on tag push; `nebula-snapshot.yml` publishes snapshots on master push. Build and artifact publication are automated, but no deployment automation exists — no stages for deploying to dev, staging, or production environments. |
| **Gap** | Build is automated but deployment is entirely absent. No deployment pipeline, no environment promotion, no rollback mechanisms. The CI/CD covers library publication (Maven Central) but not service deployment. |
| **Recommendation** | Extend the CI/CD pipeline with deployment stages. After container image build, add stages to push to Amazon ECR, deploy to EKS staging (via Helm or kubectl), run smoke tests, and promote to production with blue/green or canary strategy via AWS CodeDeploy or Argo Rollouts. |
| **Evidence** | `.github/workflows/nebula-ci.yml`, `.github/workflows/nebula-publish.yml`, `.github/workflows/nebula-snapshot.yml`. |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java is the sole programming language. Source/target compatibility is 1.8 (`sourceCompatibility = 1.8` in root `build.gradle`). CI builds with JDK 8 (`matrix: java: [8]`). Java has first-class AWS SDK coverage, broad cloud-native tooling, and the mature Spring/Jakarta ecosystem. While Java 8 is approaching community EOL, it remains the compilation target for this project, and the language itself scores at the highest tier. |
| **Gap** | None for language choice. Java 8 runtime EOL is a separate concern addressed in the dependency/upgrade lifecycle, not in language ecosystem maturity. |
| **Recommendation** | No language change needed. Consider upgrading to Java 17+ LTS when the project's dependencies (Servo, Archaius, Governator) support it, to access modern language features and improved container performance (CDS, ZGC). |
| **Evidence** | `build.gradle` (sourceCompatibility = 1.8), `.github/workflows/nebula-ci.yml` (java: [8]), `eureka-client/build.gradle`, `eureka-core/build.gradle` (all .java source files). |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Eureka is a multi-module Gradle monorepo with well-defined module boundaries. The eureka-server deploys as a single WAR file, but the internal architecture is modular: `eureka-client` (client library), `eureka-core` (server business logic), `eureka-server` (WAR packaging), plus variants (`jersey2`, `archaius2`, `governator`). Dependencies are unidirectional: `eureka-core` depends on `eureka-client`, `eureka-server` depends on both. No circular dependencies. Each module has clear interfaces (`InstanceRegistry`, `PeerAwareInstanceRegistry`, `EurekaClient`, `EurekaHttpClient`). The client modules are libraries embedded in consuming services — they are not independently deployed. |
| **Gap** | While module boundaries are clean, the eureka-server deploys as a single WAR with all server logic bundled. The monolith is modular but not decomposed into independently deployable services. However, for a service-discovery server, this is arguably the correct design — decomposing a registry into microservices would add unnecessary complexity. |
| **Recommendation** | No decomposition needed. The modular monolith pattern with clean interfaces is appropriate for a service-discovery system. If scale demands it, the well-defined module boundaries make future extraction straightforward. |
| **Evidence** | `settings.gradle` (10 modules), `eureka-server/build.gradle` (war plugin, depends on eureka-client + eureka-core), `eureka-core/build.gradle` (depends on eureka-client), absence of circular dependencies in module graph. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | (Archetype: stateful-crud) All inter-service communication is synchronous HTTP via Jersey. Client-server communication uses `AbstractJerseyEurekaHttpClient` for register, renew, cancel, and query operations. Server-to-server peer replication uses `JerseyReplicationClient` for HTTP POST batches. The `AcceptorExecutor` provides JVM-internal async batching, but the network transport remains synchronous HTTP. For a stateful-crud service, the state changes (register, cancel) that propagate to peers should ideally use async messaging. |
| **Gap** | Primarily synchronous with some internal async batching for background jobs. Cross-peer state propagation via synchronous HTTP creates coupling — a slow peer impacts replication latency for all peers. |
| **Recommendation** | Introduce async patterns for peer replication: publish state change events to Amazon EventBridge (preferred), with peer nodes consuming asynchronously. Retain synchronous HTTP for client-facing read operations (registry queries) where low latency is critical. |
| **Evidence** | `eureka-client/src/main/java/com/netflix/discovery/shared/transport/jersey/AbstractJerseyEurekaHttpClient.java`, `eureka-core/src/main/java/com/netflix/eureka/transport/JerseyReplicationClient.java`, `eureka-core/src/main/java/com/netflix/eureka/util/batcher/AcceptorExecutor.java`. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | (Archetype: stateful-crud) No Eureka operations exceed 30 seconds. All registry operations (register, renew, cancel, query) are in-memory `ConcurrentHashMap` lookups and mutations — sub-millisecond latency. Peer replication is handled asynchronously via `TaskDispatchers` with batching and expiry times (`maxProcessingDelayMs`). The `syncUp()` method during startup could take time but is a one-time bootstrap operation, not a user-facing request. The `ResponseCacheImpl` pre-computes and caches responses. |
| **Gap** | None. All user-facing operations are fast in-memory operations. Background processes (replication, eviction) are already async. |
| **Recommendation** | No action needed. The async job infrastructure (TaskDispatchers for replication, Timer-based eviction) is well-implemented for the service's needs. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (in-memory ConcurrentHashMap operations), `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (batchingDispatcher with maxProcessingDelayMs), `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java`. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Eureka uses URL path versioning consistently. The `ApplicationsResource` is annotated with `@Path("/{version}/apps")`, accepting version as a path parameter. The `Version.java` enum defines V1 and V2 with V2 as default. Configuration files reference `/eureka/v2/` in service URLs. The `web.xml` maps filter patterns to `/v2/apps` and `/v2/apps/*`. The `CurrentRequestVersion` thread-local tracks the active version per request. |
| **Gap** | Versioning is applied consistently but some infrastructure endpoints (status page at `/jsp/status.jsp`, welcome file) are unversioned. The Version enum supports V1 and V2 but there's no documented backward compatibility guarantee or deprecation policy. |
| **Recommendation** | Document the versioning policy and backward compatibility guarantees. Define a deprecation timeline for V1. Ensure all endpoints (including status and admin endpoints) follow the versioning convention. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (@Path("/{version}/apps")), `eureka-core/src/main/java/com/netflix/eureka/Version.java` (V1, V2 enum), `eureka-server/src/main/resources/eureka-client.properties` (/eureka/v2/ in serviceUrl), `eureka-server/src/main/webapp/WEB-INF/web.xml` (/v2/apps URL patterns). |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Eureka IS the service discovery system. It provides a comprehensive discovery mechanism: `ConfigClusterResolver` for static configuration-based peer resolution, `DnsTxtRecordClusterResolver` for DNS-based dynamic resolution, `ZoneAffinityClusterResolver` for zone-aware routing, and `AsyncResolver` for background resolution updates. Clients discover services via the `DiscoveryClient` which fetches the registry and caches it locally. No hard-coded service endpoints — all resolution is dynamic via the Eureka client library. |
| **Gap** | None. As a service-discovery system, Eureka provides multiple resolution strategies (config, DNS, zone-aware) with no hard-coded endpoints. |
| **Recommendation** | No action needed. The service discovery mechanism is mature and feature-complete. When migrated to EKS, consider integrating with Kubernetes native service discovery or running Eureka alongside it for backward compatibility with non-Kubernetes clients. |
| **Evidence** | `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/ConfigClusterResolver.java`, `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/DnsTxtRecordClusterResolver.java`, `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/ZoneAffinityClusterResolver.java`, `eureka-client/src/main/java/com/netflix/discovery/DiscoveryClient.java`. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Eureka does not store unstructured data. All data is structured: `InstanceInfo` objects containing application metadata (app name, host, port, status, health check URL, metadata map) stored in an in-memory `ConcurrentHashMap`. No S3, EFS, EBS, or file storage references exist. No documents, images, or unstructured content is processed. |
| **Gap** | None. Unstructured data storage is not applicable to a service registry. |
| **Recommendation** | No action needed. If future features require storing unstructured data (e.g., service documentation, API specs), use Amazon S3. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (structured InstanceInfo in ConcurrentHashMap), `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Eureka has a well-defined, centralized data access layer. All registry access goes through the `InstanceRegistry` interface hierarchy: `InstanceRegistry` → `PeerAwareInstanceRegistry` → `PeerAwareInstanceRegistryImpl` → `AbstractInstanceRegistry`. Read operations are further optimized via `ResponseCacheImpl` which pre-computes and caches serialized responses. No module bypasses this abstraction — all CRUD operations flow through the registry interface. |
| **Gap** | None. The data access pattern is exemplary — a single, well-abstracted registry interface with caching. |
| **Recommendation** | No action needed. The existing data access layer is a best-practice implementation. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java`. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No external database is used. Eureka stores all state in-memory. There is no database engine version to pin, no EOL concern, and no version lifecycle to manage. The in-memory design eliminates the entire class of database version management issues. |
| **Gap** | None. No database engine means no version/EOL risk. |
| **Recommendation** | No action needed. If an external database is introduced in the future, ensure engine version is explicitly pinned in IaC with documented upgrade procedures. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (ConcurrentHashMap, no JDBC/database driver imports), absence of any database configuration or connection strings. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No database means no stored procedures, triggers, or proprietary SQL. All business logic (registration, renewal, eviction, self-preservation, replication) is implemented in the Java application layer. No `.sql` files, no ORM configuration, no raw SQL execution patterns exist in the codebase. |
| **Gap** | None. All logic is cleanly in the application layer. |
| **Recommendation** | No action needed. The current design keeps all business logic in the application layer, which is the recommended pattern for cloud-native services. |
| **Evidence** | Absence of any `.sql` files, JDBC imports, or database driver dependencies. All business logic in `AbstractInstanceRegistry.java`, `PeerAwareInstanceRegistryImpl.java`. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging infrastructure is defined. No IaC exists to configure CloudTrail. The `ServerRequestAuthFilter` logs client identity headers (name, version) via Servo `DynamicCounter`, but this is metrics-based counting, not an audit trail of actions. Application-level logging via SLF4J/Log4j records registration/cancellation events, but these are operational logs, not immutable audit logs. |
| **Gap** | No audit logging infrastructure. Registry mutations (register, cancel, status update) are logged operationally but not in an immutable, queryable audit trail. No CloudTrail for API-level auditing. |
| **Recommendation** | Enable AWS CloudTrail for API-level audit logging. Implement application-level audit events for registry mutations and publish them to Amazon CloudWatch Logs with immutable retention (S3 with Object Lock). |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (logAuth method — metrics only), absence of `aws_cloudtrail` in any IaC. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS keys or encryption configuration exists. Eureka's registry data is in-memory (ephemeral), so encryption at rest is not directly applicable to the primary data store. However, no IaC defines encryption for any supporting resources (e.g., EBS volumes, S3 buckets for logs, etc.). No `kms_key_id` parameters found. |
| **Gap** | No encryption at rest configured for any resource. While the in-memory registry doesn't persist to disk, any future persistent storage (logs, backups) would need encryption. |
| **Recommendation** | When deploying to AWS, ensure all persistent resources (EBS volumes for EKS nodes, S3 buckets for logs, ECR repositories) use customer-managed KMS keys. Define encryption configuration in IaC as part of the Move to Modern DevOps initiative. |
| **Evidence** | Absence of any KMS, encryption, or security configuration in the repository. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The `ServerRequestAuthFilter` is registered in `web.xml` but does NOT enforce authentication. It only logs client identity information (`DiscoveryIdentity-Name`, `DiscoveryIdentity-Version` headers) via Servo counters. The `doFilter` method calls `logAuth(request)` then `chain.doFilter(request, response)` — it always passes the request through regardless of identity. All API endpoints are effectively open — any client can register, deregister, renew, or query instances without authentication. |
| **Gap** | All API endpoints are open with no authentication. The auth filter is logging-only, not enforcing. This is a critical security gap for a service registry — unauthorized clients can register malicious instances or deregister legitimate ones. |
| **Recommendation** | Implement per-request authentication using OAuth2/JWT tokens. Deploy Amazon API Gateway (preferred) with a Cognito authorizer in front of Eureka, or implement JWT validation in the `ServerRequestAuthFilter`. At minimum, add mutual TLS for peer-to-peer replication. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (doFilter → logAuth → chain.doFilter, no auth enforcement), `eureka-server/src/main/webapp/WEB-INF/web.xml` (requestAuthFilter mapping). |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, Okta, OIDC, or SAML configuration found. No `aws_cognito_*` resources in IaC (no IaC exists). The application manages identity entirely through custom header-based identification (`AbstractEurekaIdentity` headers) with no external IdP federation. |
| **Gap** | No centralized identity integration. The custom identity headers provide no authentication or authorization guarantees. |
| **Recommendation** | Integrate with Amazon Cognito (or Okta) as the centralized IdP. Configure Cognito user pools for Eureka client authentication and use Cognito tokens for API authorization. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (custom header-based identity), absence of any OIDC/SAML/Cognito configuration. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD workflows use GitHub Secrets for signing keys and repository credentials (`NETFLIX_OSS_SIGNING_KEY`, `NETFLIX_OSS_SIGNING_PASSWORD`, `NETFLIX_OSS_REPO_USERNAME`, `NETFLIX_OSS_REPO_PASSWORD`, `NETFLIX_OSS_SONATYPE_USERNAME`, `NETFLIX_OSS_SONATYPE_PASSWORD`). Service URLs in properties files contain only `http://localhost:8080/eureka/v2/` — no production credentials. However, no AWS Secrets Manager or HashiCorp Vault integration exists. No automated rotation. |
| **Gap** | CI secrets are managed via GitHub Secrets (acceptable for CI), but no Secrets Manager integration exists for runtime secrets. No automated rotation for any credentials. If production deployment requires database credentials or API keys in the future, there's no secrets management infrastructure. |
| **Recommendation** | Integrate AWS Secrets Manager for runtime secret management. Store service URLs, peer authentication credentials, and any API keys in Secrets Manager with automated rotation. Reference secrets in EKS via Kubernetes External Secrets Operator. |
| **Evidence** | `.github/workflows/nebula-publish.yml` (GitHub Secrets references), `eureka-server/src/main/resources/eureka-client.properties` (localhost URL, no production secrets). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching evidence. No SSM Patch Manager, AWS Inspector, Snyk, or vulnerability scanning configuration. No hardened AMI references (CIS, Bottlerocket). No EC2 Image Builder pipelines. The CI uses `ubuntu-latest` GitHub-hosted runners with `zulu` JDK 8 distribution, but there's no evidence of security hardening for production compute. |
| **Gap** | No compute hardening strategy. No vulnerability scanning for the runtime environment. Production compute patching is entirely manual or undefined. |
| **Recommendation** | When deploying to EKS, use Amazon Bottlerocket AMIs for EKS nodes (hardened, minimal attack surface). Enable Amazon Inspector for container image vulnerability scanning. Add Snyk or Trivy container scanning to the CI pipeline. |
| **Evidence** | `.github/workflows/nebula-ci.yml` (ubuntu-latest, no security scanning), absence of any SSM, Inspector, or hardening configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into the CI pipeline. The `nebula-ci.yml` workflow runs only `./gradlew build` — no SAST, DAST, or dependency vulnerability scanning. `codequality/checkstyle.xml` exists for code style checking, but Checkstyle is a code quality tool, not a security scanner. No Dependabot configuration, no `npm audit` equivalent, no SonarQube, no Semgrep, no container scanning. |
| **Gap** | No security scanning in the CI pipeline. Vulnerabilities in dependencies (AWS SDK 1.11.277 is severely outdated, Jackson 2.10.5 has known CVEs, Jettison 1.5.4 has had security advisories) reach production undetected. |
| **Recommendation** | Add dependency vulnerability scanning (OWASP Dependency-Check Gradle plugin or Snyk) as a CI step. Add SAST (SonarQube or Semgrep) for Java source code analysis. Configure Dependabot for automated dependency update PRs. Add container image scanning when Dockerfiles are created. |
| **Evidence** | `.github/workflows/nebula-ci.yml` (only `./gradlew build`), `codequality/checkstyle.xml` (code style, not security), absence of any `.snyk`, `.dependabot`, or security scanner configuration. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. Eureka uses Netflix Servo for metrics (`servo-core` dependency in `eureka-client/build.gradle`) providing aggregate counters and gauges, but no trace ID propagation exists. No OpenTelemetry SDK, X-Ray agent, or `traceparent` header handling found. The `x-netflix-discovery-replication` header is used for replication identification, not tracing. |
| **Gap** | No distributed tracing. Cannot trace individual requests through the Eureka server cluster or across client-server interactions. Debugging replication lag or failed registrations requires manual log correlation. |
| **Recommendation** | Instrument with AWS X-Ray SDK for Java or OpenTelemetry Java agent. Add trace context propagation to Jersey filters for client-server and peer-to-peer requests. Configure X-Ray sampling rules appropriate for the registration/renewal traffic volume. |
| **Evidence** | `eureka-client/build.gradle` (servo-core dependency, no tracing libraries), `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (HEADER_REPLICATION, no trace headers), absence of OpenTelemetry or X-Ray in any dependency manifest. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No SLO definition files, no error budget tracking, no p99/p95 latency alarms. `EurekaMonitors.java` provides raw counters (registrations, renewals, cancellations) but no threshold-based SLO monitoring. The self-preservation mode (`numberOfRenewsPerMinThreshold`) is a form of operational threshold but is not an SLO — it's a circuit breaker. |
| **Gap** | No formal SLO definitions. Cannot measure whether Eureka is meeting service level expectations for registration latency, query latency, or replication convergence time. |
| **Recommendation** | Define SLOs for critical Eureka operations: (1) registration latency p99 < 100ms, (2) query latency p99 < 50ms, (3) peer replication convergence < 30s, (4) availability > 99.99%. Monitor via CloudWatch custom metrics with error budget dashboards. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (raw counters only), `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (numberOfRenewsPerMinThreshold — not an SLO). |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Eureka publishes business-level metrics via Netflix Servo: `EurekaMonitors` enum tracks 20+ business metrics including REGISTER, CANCEL, RENEW, EXPIRED, GET_ALL, RATE_LIMITED counters with zone-specific breakdowns. `MeasuredRate` tracks renewals-per-minute. `PeerAwareInstanceRegistryImpl` exposes `numOfReplicationsInLastMin`, `localRegistrySize`, `isBelowRenewThreshold`, `isLeaseExpirationEnabled`, and `shouldAllowAccess` as Servo gauges. These are genuine business outcome metrics (registration velocity, self-preservation state, cluster health). |
| **Gap** | Business metrics exist but are published via Netflix Servo, not CloudWatch. No dashboards are defined. Metrics are emitted but not systematically visualized or alerted on across all features. |
| **Recommendation** | Bridge Servo metrics to Amazon CloudWatch using a Servo-to-CloudWatch publisher, or migrate to Micrometer with CloudWatch registry. Build CloudWatch dashboards for the existing business metrics (registration rate, renewal rate, self-preservation state, registry size). |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (20+ business metric counters), `eureka-core/src/main/java/com/netflix/eureka/util/MeasuredRate.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (Servo @Monitor annotations). |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no composite alarms. While Eureka's self-preservation mode is a form of anomaly detection (detects when renewals drop below threshold), it's an application-level circuit breaker, not operational alerting. No infrastructure exists to alert operators when the cluster degrades. |
| **Gap** | No alerting configured. Operators have no way to be notified of cluster degradation, peer failure, or abnormal registration patterns. Self-preservation mode reacts but doesn't alert. |
| **Recommendation** | Configure CloudWatch anomaly detection on Eureka business metrics: (1) registration rate anomalies, (2) renewal rate drops, (3) self-preservation mode activation, (4) peer replication failure rate. Integrate with Amazon SNS for alerts and PagerDuty/OpsGenie for escalation. |
| **Evidence** | Absence of any CloudWatch alarm, SNS topic, or alerting configuration in the repository. `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (self-preservation is application-level, not operational alerting). |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. The CI/CD publishes artifacts to Maven Central (library publication) but does not deploy the eureka-server to any environment. No CodeDeploy, Argo Rollouts, Helm canary, Lambda traffic shifting, or ALB weighted target groups. The repository has no concept of environment-specific deployment. |
| **Gap** | No deployment strategy — no staged rollout mechanism. Any production deployment is manual with no canary, blue/green, or rolling update capability. |
| **Recommendation** | Implement blue/green deployment using Kubernetes rolling updates on EKS, or Argo Rollouts for canary deployments. Eureka's peer-aware design is well-suited for rolling updates — new instances join the cluster and sync via `syncUp()` before old instances are drained. |
| **Evidence** | `.github/workflows/nebula-publish.yml` (Maven Central publication only), absence of any deployment configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist and run in CI. `EurekaClientServerRestIntegrationTest.java` (297 lines) instantiates a fully configured Jersey container with an embedded Jetty server to test the complete REST layer — client/server communication with content encoding/decoding (JSON, XML, compressed, uncompressed). Additional integration-level tests include `InstanceRegistryTest`, `PeerEurekaNodeTest`, codec integration tests. 99 test files total across the monorepo. All tests run via `./gradlew build` in the `nebula-ci.yml` CI workflow. |
| **Gap** | Integration tests cover client-server REST communication and core registry operations, but there are no environment-specific tests, no contract tests, and no end-to-end tests in a production-like environment. Tests use embedded Jetty, not a real deployment topology. |
| **Recommendation** | Add contract tests (Pact) to verify client-server API compatibility. Add end-to-end tests that exercise a multi-node Eureka cluster with peer replication. Run these as part of a deployment pipeline (post-deployment smoke tests). |
| **Evidence** | `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`, `eureka-core/src/test/java/com/netflix/eureka/registry/InstanceRegistryTest.java`, `eureka-core/src/test/java/com/netflix/eureka/cluster/PeerEurekaNodeTest.java`, `.github/workflows/nebula-ci.yml` (runs tests via gradlew build). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, SSM Automation documents, Lambda-based remediation, or self-healing patterns found. No incident response workflows are defined. The self-preservation mode in `PeerAwareInstanceRegistryImpl` is the closest to a self-healing pattern — it prevents mass eviction during network partitions — but it is application logic, not an operational runbook. |
| **Gap** | No incident response automation. Operators must diagnose and resolve issues manually. Common scenarios (peer failure, split brain, registry corruption) have no documented runbooks. |
| **Recommendation** | Create runbooks for common Eureka incidents: (1) peer node failure and recovery, (2) self-preservation mode activation, (3) registry divergence between peers, (4) mass client re-registration after restart. Implement as SSM Automation documents where possible. |
| **Evidence** | Absence of any runbook, automation document, or self-healing configuration in the repository. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file exists for observability assets. No team-attributed dashboards, no named alarm owners, no SLO definitions with team attribution. Servo metrics are registered globally (`EurekaMonitors.registerAllStats()`) with no ownership metadata. |
| **Gap** | No observability ownership. Monitoring is embedded in application code but has no operational ownership, no dashboards, and no team attribution. |
| **Recommendation** | Define CODEOWNERS for observability configuration. Create per-service CloudWatch dashboards with named owners. Tag all monitoring resources (alarms, dashboards) with team ownership for accountability. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (registerAllStats — global registration, no ownership), absence of CODEOWNERS file. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists. No IaC means no `default_tags`, no `tags` on resources, no tag enforcement via Config rules or Tag Policies. No cost allocation, ownership, or environment tagging is possible without infrastructure definitions. |
| **Gap** | No tags on any resources. Cost allocation, ownership tracking, and environment identification are impossible. |
| **Recommendation** | When creating IaC, define a tagging strategy from the start: mandatory tags for `Environment`, `Service`, `Team`, `CostCenter`. Use AWS CDK `Tags.of()` for default tags. Enforce via AWS Config `required-tags` rules. |
| **Evidence** | Absence of any IaC files or tagging configuration in the repository. |

## Learning Materials

The following learning resources correspond to the triggered pathways:

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
| `build.gradle` | INF-Q10, APP-Q1, APP-Q2 | Root build configuration: Java 8 sourceCompatibility, allprojects dependency versions, subproject configuration. |
| `settings.gradle` | APP-Q2 | Defines 10 submodules of the monorepo. |
| `gradle.properties` | INF-Q10 | Build configuration — no IaC. |
| `.github/workflows/nebula-ci.yml` | INF-Q11, OPS-Q6, SEC-Q6, SEC-Q7 | CI workflow: builds with JDK 8, runs tests via gradlew build. No security scanning. |
| `.github/workflows/nebula-publish.yml` | INF-Q11, SEC-Q5, OPS-Q5 | Release publication to Maven Central. Contains GitHub Secrets references. |
| `.github/workflows/nebula-snapshot.yml` | INF-Q11 | Snapshot publication workflow on master push. |
| `eureka-server/build.gradle` | INF-Q1, APP-Q2 | WAR plugin applied — produces deployable WAR artifact. Depends on eureka-client and eureka-core. |
| `eureka-server/src/main/webapp/WEB-INF/web.xml` | INF-Q1, INF-Q6, SEC-Q3, APP-Q5 | Servlet 2.5 config with filter chain: statusFilter, requestAuthFilter, rateLimitingFilter (commented out), gzipEncodingEnforcingFilter, jersey. |
| `eureka-server/src/main/resources/eureka-client.properties` | INF-Q6, APP-Q5, SEC-Q5 | Service URL configuration (/eureka/v2/), region/zone config examples. |
| `eureka-server/src/main/resources/eureka-server.properties` | INF-Q8 | Server configuration — minimal, mostly commented-out examples. |
| `eureka-core/build.gradle` | APP-Q1, APP-Q2 | Core module dependencies: AWS SDK 1.11.277, Servlet 2.5, XStream, Jackson. |
| `eureka-client/build.gradle` | APP-Q1, OPS-Q1 | Client module dependencies: Archaius, Servo, Jersey, Jackson, Guice. |
| `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` | INF-Q2, INF-Q8, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, APP-Q4 | Core registry implementation: ConcurrentHashMap, register/renew/cancel/evict operations. |
| `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` | INF-Q2, INF-Q9, OPS-Q2, OPS-Q3, OPS-Q4 | Peer-aware registry: replication, self-preservation, sync, Servo monitors. |
| `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` | INF-Q3, INF-Q4, APP-Q3, OPS-Q1 | Peer replication: batchingDispatcher, nonBatchingDispatcher, HTTP replication client. |
| `eureka-core/src/main/java/com/netflix/eureka/transport/JerseyReplicationClient.java` | INF-Q4, APP-Q3 | Synchronous HTTP replication transport. |
| `eureka-core/src/main/java/com/netflix/eureka/util/batcher/TaskDispatchers.java` | INF-Q3 | Batching task dispatchers for replication. |
| `eureka-core/src/main/java/com/netflix/eureka/util/batcher/AcceptorExecutor.java` | INF-Q3, APP-Q3 | JVM-internal async batching executor for replication tasks. |
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` | APP-Q5 | REST resource: @Path("/{version}/apps"), JSON/XML support, GZIP encoding. |
| `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` | APP-Q5 | REST resource for individual instance CRUD operations. |
| `eureka-core/src/main/java/com/netflix/eureka/Version.java` | APP-Q5 | Version enum: V1, V2 with V2 as default. |
| `eureka-core/src/main/java/com/netflix/eureka/EurekaBootStrap.java` | INF-Q1, INF-Q9 | Server bootstrap via ServletContextListener. Cloud/datacenter detection. |
| `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` | SEC-Q1, SEC-Q3, SEC-Q4 | Auth filter: logs identity headers only, does not enforce authentication. |
| `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` | OPS-Q2, OPS-Q3, OPS-Q8 | Servo-based business metrics: 20+ counters for registrations, renewals, cancellations, etc. |
| `eureka-core/src/main/java/com/netflix/eureka/util/MeasuredRate.java` | OPS-Q3 | Tracks measured rate (renewals per minute). |
| `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java` | DATA-Q2, APP-Q4 | Response cache: pre-computed and cached serialized responses. |
| `eureka-client/src/main/java/com/netflix/discovery/DiscoveryClient.java` | APP-Q6 | Main client: registry fetching, caching, service resolution. |
| `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/ConfigClusterResolver.java` | APP-Q6 | Config-based cluster resolution for Eureka peer discovery. |
| `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/DnsTxtRecordClusterResolver.java` | APP-Q6 | DNS-based dynamic cluster resolution. |
| `eureka-client/src/main/java/com/netflix/discovery/shared/resolver/aws/ZoneAffinityClusterResolver.java` | APP-Q6 | Zone-aware routing for cluster resolution. |
| `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java` | DATA-Q1 | Structured instance data model. |
| `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java` | OPS-Q6 | Integration test: full REST layer test with embedded Jetty. |
| `eureka-core/src/test/java/com/netflix/eureka/registry/InstanceRegistryTest.java` | OPS-Q6 | Registry unit/integration tests. |
| `eureka-core/src/test/java/com/netflix/eureka/cluster/PeerEurekaNodeTest.java` | OPS-Q6 | Peer replication tests. |
| `eureka-server-governator/src/main/webapp/WEB-INF/web.xml` | SEC-Q3 | Governator variant web.xml with GuiceFilter. |
| `codequality/checkstyle.xml` | SEC-Q7 | Code quality config — not security scanning. |
| `README.md` | Quick Agent Wins | Repository documentation, links to wiki. |
| `CHANGELOG.md` | Quick Agent Wins | Empty changelog file. |
