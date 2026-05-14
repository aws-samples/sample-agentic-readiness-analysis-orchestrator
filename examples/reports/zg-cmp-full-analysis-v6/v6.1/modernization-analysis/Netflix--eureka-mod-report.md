# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | Netflix--eureka |
| **Date** | 2026-05-08 |
| **TD Version** | modernization-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, service-discovery, microservices |
| **Context** | Netflix service-discovery server and client. |
| **Overall Score** | 2.08 / 4.0 |

**Archetype Justification**: The service maintains mutable in-memory state (service registry) and exposes both read (instance lookup, registry fetch) and write (registration, deregistration, heartbeat, status update) endpoints via REST API. Peer-to-peer replication propagates state mutations across instances. Classified as `stateful-crud`.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.13 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 4.00 / 4.0 | ✅ Mature | Ready |
| Security Baseline (SEC) | 1.40 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.38 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **2.08 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+1+1+1+1+1+2) / 8 evaluated = 9/8 = 1.13. Not Evaluated: INF-Q2 (no persistent data store), INF-Q8 (no data-at-rest surface), INF-Q9 (no deployed workload).
- APP: (2+3+1+3+2+4) / 6 = 15/6 = 2.50
- DATA: (4+4+4) / 3 evaluated = 12/3 = 4.00. Not Evaluated: DATA-Q3 (no persistent data store).
- SEC: (2+1+2+1+1) / 5 evaluated = 7/5 = 1.40. Not Evaluated: SEC-Q1 (no account-level IaC), SEC-Q2 (no data-at-rest surface).
- OPS: (1+1+2+1+3+1+1+1) / 8 evaluated = 11/8 = 1.38. Not Evaluated: OPS-Q5 (no deployed workload).
- Overall: (1.13 + 2.50 + 4.00 + 1.40 + 1.38) / 5 = 2.08

---

## Classification

**Tier: 🟠 Remediation Required**

**Classification Rationale:** This repo has 3 High findings, 20 Medium findings, and 3 Low findings. The matched rule is "2-11 High → Remediation Required." Note: ARA's "1 High" is an agent-deployment gate (blocking deployment); MOD's "1 High" is typically a single modernization gap. MOD requires 2+ High findings to enter Remediation Required because a single modernization gap is still pilot-worthy.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | All compute designed for raw EC2 deployment (WAR on servlet container with EIP/ENI binding) | Requires manual server management, patching, capacity planning; blocks containerization and serverless adoption |
| 2 | INF-Q10: Infrastructure as Code | 1 | No IaC exists — all infrastructure manually provisioned | Non-reproducible environments, manual error-prone deployments, no disaster recovery automation |
| 3 | INF-Q5: Network Security | 1 | No VPC/subnet/security group definitions in repo | No documented network isolation; services potentially directly exposed |
| 4 | SEC-Q7: Security Pipeline | 1 | No SAST, DAST, or dependency scanning in CI/CD pipeline | Vulnerabilities in dependencies (AWS SDK 1.11.277, Jersey 1.x) and code reach production undetected |
| 5 | APP-Q3: Async vs Sync Communication | 1 | All inter-node communication is synchronous HTTP with no async patterns for state propagation | Cascading failures during peer replication, tight coupling between Eureka nodes, no resilience to slow peers |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2) — GitHub Actions workflows for build, publish, and snapshot are functional.
- **What it enables:** An agent that triggers builds, checks CI status, monitors publish workflows, and manages release tagging.
- **Additional steps:** Add GitHub API access configuration for the agent to interact with Actions workflows programmatically.
- **Effort:** Low

### Integration Test Agent

- **Prerequisite:** Integration tests exist and run in CI (OPS-Q6 = 3) — `EurekaClientServerRestIntegrationTest`, MockServer, and WireMock tests are established.
- **What it enables:** An agent that monitors test results, identifies flaky tests, suggests test improvements, and correlates failures with code changes.
- **Additional steps:** Expose test result artifacts from CI in a structured format (JUnit XML reports).
- **Effort:** Low

No additional Quick Agent Wins identified. The system lacks API documentation (no OpenAPI spec), structured observability, workflow orchestration, and comprehensive logging that would enable API-aware, observability, or knowledge agents.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=3 (not triggered), but INF-Q1=1, APP-Q3=1 → supporting triggers met. Actually APP-Q2 ≥ 3, so primary trigger not met. |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (compute on raw EC2), no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2=Not Evaluated (no persistent data store); no database exists |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; contextual guard prevents trigger |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), INF-Q11=2 (partial CI/CD), OPS-Q6=3 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

Correction for Pathway 1: The primary trigger is APP-Q2 < 3. APP-Q2 = 3, so primary trigger is NOT met. Move to Cloud Native is Not Triggered.

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2=3 (meets threshold ≥3); primary trigger not met |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1, no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4; no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2=Not Evaluated; no database exists in this system |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads; contextual guard prevents trigger |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in service context |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** Eureka is deployed as a WAR file on a traditional servlet container (Tomcat/Jetty) running on EC2 instances. The architecture assumes direct EC2 instance identity — EIP binding (`EIPManager.java`), ENI binding (`ElasticNetworkInterfaceBinder.java`), and Route53 DNS registration (`Route53Binder.java`) are tightly coupled to EC2 metadata.

**Container Readiness Indicators:**
- Application is self-contained as a WAR with well-defined entry point (`EurekaBootStrap` listener)
- Configuration is externalized via properties files (Archaius)
- Port binding is configurable (`eureka.port`)
- No local filesystem dependencies for data persistence (in-memory registry)

**Challenges:**
- AWS EC2-specific code (EIP/ENI management) would need to be replaced with container-native service discovery
- Instance identity assumptions (EC2 metadata) need container-native alternatives (EKS pod identity, Fargate task metadata)

**Recommended Container Orchestration:** Amazon EKS (per preferences) with Kubernetes-native service discovery replacing EIP-based identity.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS Fargate

**Migration Approach:** Refactor-then-containerize — the EC2-specific AWS integrations (EIP, ENI, Route53 binder) need abstraction before containerization delivers full value.

**Learning Materials:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** No infrastructure-as-code exists in this repository. All infrastructure (EC2 instances, EIPs, security groups, Route53 records) is provisioned manually or outside this repo.

**Current CI/CD State (INF-Q11=2):** GitHub Actions provides automated build and test on push/PR, and automated publish to Maven Central on tag. However, there is no deployment automation — no CodeDeploy, no ECS/EKS deployment, no deployment pipeline stages.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK or Terraform to define EKS cluster, networking, and Eureka deployment resources
- **CI/CD:** Extend GitHub Actions with deployment stages using AWS CodeDeploy or ArgoCD for EKS
- **Observability:** CloudWatch Container Insights for EKS

**Representative AWS Services:** AWS CDK, CodeBuild, CodePipeline, CodeDeploy, CloudWatch, X-Ray

**Immediate Actions:**
1. Create IaC for the target deployment environment (VPC, subnets, EKS cluster or ECS service)
2. Add deployment stages to the existing GitHub Actions CI workflow
3. Implement integration testing in the deployment pipeline

**Learning Materials:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Eureka is designed for deployment as a WAR file on EC2 instances. The codebase contains deep EC2 integration: `EIPManager.java` manages Elastic IP binding, `ElasticNetworkInterfaceBinder.java` handles ENI attachment, `Route53Binder.java` manages DNS records, and `AmazonInfo.java` reads EC2 instance metadata. No managed compute (ECS, EKS, Lambda, Fargate) is used or supported. |
| **Gap** | All compute is on raw EC2 with no managed container orchestration or serverless. The WAR deployment model and EC2-specific identity code prevent adoption of managed compute without refactoring. |
| **Recommendation** | Containerize the Eureka server with a Dockerfile wrapping the WAR in a Tomcat/Jetty base image. Deploy on Amazon EKS (preferred). Abstract EC2-specific identity code behind an interface that supports both EC2 and Kubernetes service discovery. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/aws/EIPManager.java`, `eureka-core/src/main/java/com/netflix/eureka/aws/ElasticNetworkInterfaceBinder.java`, `eureka-core/src/main/java/com/netflix/eureka/aws/Route53Binder.java`, `eureka-client/src/main/java/com/netflix/appinfo/AmazonInfo.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml` (Servlet 2.5 WAR) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. Eureka uses an in-memory registry with no persistent data store. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No JDBC drivers, JPA, Hibernate, or database connection configuration found in any build.gradle or source file. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | This service is a `stateful-crud`. Multi-step workflows exist: peer replication (batch replication across cluster nodes), EIP/ENI lifecycle management (acquire → bind → verify → register DNS), and self-preservation mode transitions. All orchestration logic is hardcoded in application code with no dedicated workflow service. The `PeerEurekaNode` class implements batch replication as a hardcoded state machine. |
| **Gap** | No orchestration — all workflow logic (peer replication, EIP lifecycle, cluster formation) is hardcoded in application code. For a stateful-crud service with multi-step operations, this is a Score 1. |
| **Recommendation** | For containerized deployment on EKS, consider AWS Step Functions for EIP/DNS lifecycle operations during scaling events. Peer replication orchestration could benefit from EventBridge for event-driven cluster membership changes. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-core/src/main/java/com/netflix/eureka/aws/EIPManager.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | This service is a `stateful-crud`. No managed messaging or streaming infrastructure exists. All state propagation between Eureka nodes uses synchronous HTTP-based replication. Registration state changes (register, heartbeat, cancel, status update) are propagated to peers via synchronous REST calls in `PeerEurekaNode`. The in-process `netflix-eventbus` (0.3.0) is used for local event dispatch only, not cross-service messaging. |
| **Gap** | No messaging where state changes cross service boundaries — peer replication is entirely synchronous HTTP between Eureka nodes. This creates tight coupling between peers and risks cascading failures when a peer is slow or unreachable. For a stateful-crud service that propagates state mutations across instances, this represents a genuine gap. |
| **Recommendation** | Consider Amazon EventBridge (preferred per context) for decoupled peer notification of registry changes. SQS could buffer replication events to peers, preventing cascading failures during node degradation. This would decouple peer health from replication latency. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-client/build.gradle` (netflix-eventbus 0.3.0 — in-process only), no SQS/SNS/EventBridge/Kafka/MSK imports or IaC |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists in this repository. The application is designed for EC2 deployment but no networking infrastructure is defined. |
| **Gap** | Services deployed without documented network isolation. No VPC configuration, security groups, or network segmentation visible. |
| **Recommendation** | Define VPC infrastructure in IaC (CDK or Terraform) with private subnets for Eureka nodes. Implement least-privilege security groups allowing only intra-cluster communication and client traffic on the Eureka port. Use VPC endpoints for AWS API access. |
| **Evidence** | No `.tf` files, no CloudFormation templates, no CDK stacks. No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront serves as the entry point. Eureka nodes are designed to be accessed directly via their EIP or DNS record. The `Route53Binder` registers individual instance DNS records, and clients connect directly to Eureka instances. |
| **Gap** | Services exposed directly with no gateway or load balancer. No throttling, authentication, or request validation at the entry point beyond the application-level `RateLimitingFilter` and `ServerRequestAuthFilter`. |
| **Recommendation** | Deploy an Application Load Balancer (or API Gateway per preferences) in front of Eureka nodes for health checking, traffic distribution, and TLS termination. For EKS deployment, use an Ingress controller or AWS Load Balancer Controller. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/aws/Route53Binder.java` (direct DNS registration), `eureka-server/src/main/resources/eureka-client.properties` (direct URL: `http://localhost:8080/eureka/v2/`) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The codebase references AWS Auto Scaling Groups via `AwsAsgUtil.java` for reading ASG membership of registered services, but no auto-scaling is configured for Eureka itself. |
| **Gap** | No auto-scaling — all capacity is statically provisioned. Eureka instances are deployed as fixed-size clusters with no dynamic scaling. |
| **Recommendation** | For EKS deployment, configure Horizontal Pod Autoscaler (HPA) based on registered instance count and request rate. For EC2, define ASG with target tracking policies. Note that Eureka's peer-awareness protocol needs consideration during scale-out events. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/aws/AwsAsgUtil.java` (reads ASG info, does not configure scaling), no `aws_autoscaling_*` or `aws_appautoscaling_*` resources |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. Eureka maintains an in-memory registry that is reconstructed from peer replication and client re-registration on restart. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources, no S3 buckets, no EBS volumes. Registry is reconstructed from peer sync and client heartbeats. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No deployed workload found in this repo — high availability configuration cannot be assessed from source code alone. The application is designed for multi-node deployment (peer replication), but no deployment manifests exist to evaluate AZ distribution. Deployment orchestration may exist in a separate deployment-config or GitOps repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No Terraform, CloudFormation, Kubernetes manifests, or Helm charts defining multi-AZ deployment topology. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in this repository. No Terraform files, CloudFormation templates, CDK stacks, Helm charts, or Kustomize manifests were found. All infrastructure (EC2 instances, EIPs, ENIs, security groups, Route53 hosted zones) is provisioned manually or in a separate repository. |
| **Gap** | No IaC — all infrastructure created manually (ClickOps) or managed externally. Zero percent of infrastructure is codified in this repository. |
| **Recommendation** | Create IaC using AWS CDK (preferred for Java teams) or Terraform to define the full Eureka deployment stack: VPC, subnets, EKS cluster (or EC2 ASG), load balancer, security groups, and DNS records. Start with the target EKS architecture rather than codifying the legacy EC2 deployment. |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or any IaC files found in repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides automated CI (build and test on push/PR via `nebula-ci.yml`) and automated publishing (snapshot on master push via `nebula-snapshot.yml`, release on tag via `nebula-publish.yml`). However, there is no deployment automation — the pipeline builds artifacts and publishes to Maven Central/NetflixOSS but does not deploy to any environment. |
| **Gap** | Build is automated but deployment is manual. No deployment stages, no environment promotion, no automated rollback. The CI/CD pipeline covers build and publish but not deploy. |
| **Recommendation** | Extend the GitHub Actions pipeline with deployment stages: build container image → push to ECR → deploy to staging EKS → run integration tests → promote to production. Use ArgoCD or AWS CodeDeploy for GitOps-based deployment. |
| **Evidence** | `.github/workflows/nebula-ci.yml` (build+test), `.github/workflows/nebula-publish.yml` (publish release), `.github/workflows/nebula-snapshot.yml` (publish snapshot). No deployment workflow, no `appspec.yml`, no CodeDeploy or ECS deploy actions. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Java 8 with Jersey 1.19.1 (JAX-RS 1.1), AWS SDK v1 (1.11.277), Servlet 2.5, Guice 4.1.0, and Archaius 0.7.6. This represents compound legacy across all three axes: language version (Java 8 is past EOL for non-LTS), framework (Jersey 1.x is abandoned, Servlet 2.5 predates modern servlet spec), and SDK (AWS SDK v1 is maintenance mode). |
| **Gap** | Java 8, Jersey 1.x, AWS SDK v1, and Servlet 2.5 are all regressed. Java 8 lacks modern language features (records, sealed classes, pattern matching). AWS SDK v1 is in maintenance mode with no new features. Jersey 1.x and Servlet 2.5 are abandoned/legacy specifications. |
| **Recommendation** | Upgrade to Java 17+ (LTS) with Spring Boot 3.x or Jakarta EE 10 replacing Jersey 1.x. Migrate AWS SDK from v1 (1.11.x) to v2 (2.x) for improved performance and non-blocking I/O. This enables modern cloud-native patterns and container-friendly deployment. |
| **Evidence** | `build.gradle` (`sourceCompatibility = 1.8`, `awsVersion = '1.11.277'`, `jerseyVersion = '1.19.1'`, `servletVersion = '2.5'`) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-structured modular architecture with 10 subprojects having clear separation of concerns: `eureka-client` (client library), `eureka-core` (server logic), `eureka-server` (WAR packaging), `eureka-client-jersey2` (Jersey 2 transport), `eureka-client-archaius2` (Archaius2 config), `eureka-core-jersey2` (Jersey 2 server). Module boundaries are well-defined with clear interfaces. Dependencies flow from server → core → client with no circular dependencies. |
| **Gap** | Modular monolith — while module boundaries are clear, all server modules deploy as a single WAR unit. The monolith has identifiable modules but a shared deployment artifact. Client and server are properly separated as independent libraries. |
| **Recommendation** | The current modular structure is appropriate for a service registry. No decomposition is needed — Eureka is a cohesive service with a single responsibility (service discovery). Focus on containerization rather than decomposition. |
| **Evidence** | `settings.gradle` (10 subprojects), `eureka-core/build.gradle` (depends on eureka-client), `eureka-server/build.gradle` (WAR plugin, depends on eureka-core + eureka-client) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | This service is a `stateful-crud`. All inter-node communication is synchronous HTTP. Peer replication in `PeerEurekaNode` dispatches registration/heartbeat/cancel/status events to peer nodes via synchronous Jersey client HTTP calls. Client-to-server communication is also entirely synchronous REST (register, heartbeat, fetch registry). No async messaging patterns exist for cross-service state propagation. |
| **Gap** | All communication synchronous HTTP with no async patterns. For a stateful-crud service that propagates state mutations (registrations, heartbeats) across cluster nodes, this creates tight coupling and cascading failure risk when peers are slow. |
| **Recommendation** | Introduce EventBridge (preferred) or SQS for asynchronous peer notification of registry changes. This decouples peer health from replication latency. Synchronous reads (registry fetch) can remain synchronous — the gap is in write propagation. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (synchronous HTTP replication), `eureka-client/build.gradle` (Jersey HTTP client, Apache HttpClient 4.5.3) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | This service is a `stateful-crud`. Individual API operations (register, heartbeat, fetch) are sub-second. Peer replication uses batching via `ReplicationTaskProcessor` which processes replication events in batches asynchronously from the request path — the registering client does not wait for peer replication to complete. Initial registry sync on startup uses configurable retry with `waitTimeInMsWhenSyncEmpty`. No operations block callers for more than 30 seconds. |
| **Gap** | Most long-running operations are handled asynchronously (batch replication doesn't block the request path). Initial sync on startup may take time but uses retry/wait patterns. Minor gap: no formal status polling or callback pattern for cluster convergence status. |
| **Recommendation** | Consider exposing a cluster convergence status endpoint that consumers can poll to verify registry consistency across peers after scaling events. This is a minor improvement — current patterns are adequate for the service's requirements. |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (batched replication), `eureka-server/src/main/resources/eureka-server.properties` (`waitTimeInMsWhenSyncEmpty` configuration) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | URL path versioning is present (`/v2/apps`, `/v2/apps/*` visible in web.xml filter mappings and client properties). However, only version 2 exists — there is no evidence of version 1 API support, no backward compatibility strategy, and no versioning documentation or changelog describing version differences. |
| **Gap** | Versioning applied but limited — only `/v2/` URL path prefix exists with no multi-version support, no deprecation strategy, and no version negotiation. Breaking changes would affect all consumers simultaneously. |
| **Recommendation** | Document the API versioning strategy. If a v3 API is planned (e.g., for Jakarta EE migration), implement parallel version support with deprecation timeline. Consider OpenAPI specification to formalize the API contract. |
| **Evidence** | `eureka-server/src/main/webapp/WEB-INF/web.xml` (`/v2/apps`, `/v2/apps/*`), `eureka-server/src/main/resources/eureka-client.properties` (`serviceUrl.default=http://localhost:8080/eureka/v2/`) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Eureka IS the service discovery system. It implements a full service registry with client-side discovery, DNS-based discovery (`shouldUseDns` configuration), zone-aware load balancing, and dynamic endpoint resolution. Services register with Eureka and discover peers through the registry — no hard-coded endpoints for service-to-service communication. |
| **Gap** | N/A — the system fully implements service discovery as its core function. |
| **Recommendation** | N/A — service discovery is the primary function of this system and is fully implemented. For EKS migration, consider integration with Kubernetes native service discovery or AWS Cloud Map as a complement. |
| **Evidence** | `eureka-client/src/main/java/com/netflix/discovery/DiscoveryClient.java`, `eureka-server/src/main/resources/eureka-client.properties` (DNS-based and URL-based discovery configuration), `eureka-core/src/main/java/com/netflix/eureka/registry/` (registry implementation) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service registry does not produce or consume unstructured data (documents, images, PDFs). All data is structured registration information (instance metadata, health status, endpoints) held in memory. No unstructured data storage concern exists. |
| **Gap** | N/A — no unstructured data exists in this service's domain. |
| **Recommendation** | N/A |
| **Evidence** | No S3 interactions, no file upload/download, no document processing libraries. All data models in `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java` are structured objects. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Data access is fully centralized through the `InstanceRegistry` interface and its implementations (`PeerAwareInstanceRegistryImpl`, `AbstractInstanceRegistry`). All registry operations (register, cancel, renew, statusUpdate, getApplication) go through this unified layer. No scattered database connections exist because the data store is the in-memory registry itself with a clean interface. |
| **Gap** | N/A — data access is fully centralized through the registry interface. |
| **Recommendation** | N/A |
| **Evidence** | `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. The in-memory registry has no database engine to version or manage. DATA-Q3 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database drivers, no RDS/DynamoDB/DocumentDB resources, no engine version configuration anywhere in the codebase. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic (registration, eviction, self-preservation, peer replication) is implemented in the Java application layer. No database coupling of any kind. |
| **Gap** | N/A — all logic is in the application layer. |
| **Recommendation** | N/A |
| **Evidence** | No `.sql` files, no `CREATE PROCEDURE`, no ORM configuration, no database drivers. Business logic in `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application-level code only (no IaC provisioning AWS resources) which is the correct scope for an application repo. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_iac_provisioning_aws_resources=false`. No Terraform, CloudFormation, or CDK defining AWS resources. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_at_rest_data_surface=false`. In-memory registry with no persistent storage. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | A `ServerRequestAuthFilter` is configured in `web.xml` and mapped to all URL patterns. However, examining the implementation reveals it is a framework hook/extension point rather than a complete authentication implementation. No OAuth2/JWT token validation, no Cognito integration, no API Gateway authorizer. Rate limiting filter exists but is commented out in the filter-mapping. |
| **Gap** | API key or static credential authentication without token-based auth. The `ServerRequestAuthFilter` provides a hook but no evidence of OAuth2/JWT implementation. Authentication appears to be network-level (security groups) rather than per-request token-based. |
| **Recommendation** | Implement per-request authentication using OAuth2/JWT for Eureka API access. For EKS deployment, consider AWS API Gateway (preferred) with Cognito authorizer in front of the Eureka service, or integrate Spring Security OAuth2 if migrating to Spring Boot. |
| **Evidence** | `eureka-server/src/main/webapp/WEB-INF/web.xml` (`requestAuthFilter` mapped to `/*`), `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration exists. No Cognito, Okta, OIDC, SAML, or SSO configuration found. The `ServerRequestAuthFilter` is a custom framework hook with no external IdP integration. Authentication, if any, is managed entirely within the application boundary. |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. No SSO, no federated identity, no centralized access control. |
| **Recommendation** | Integrate with Amazon Cognito or an existing organizational IdP (Okta, Ping). For service-to-service authentication (Eureka clients registering with server), implement IAM-based authentication or mTLS with AWS Private CA. |
| **Evidence** | No `aws_cognito_*` references, no OIDC/SAML configuration, no identity provider libraries in build.gradle. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials exist in source code or configuration files. CI/CD secrets (signing keys, repository credentials) are properly stored in GitHub Actions secrets (`${{ secrets.ORG_SIGNING_KEY }}`, etc.). Application configuration files contain no embedded passwords or API keys. However, no AWS Secrets Manager, Vault, or rotation mechanism is configured for runtime secrets. |
| **Gap** | No plaintext credentials in source, but no managed secrets service with rotation for runtime credentials. The application relies on environment variables and Archaius configuration for runtime settings. No evidence of Secrets Manager or automated rotation. |
| **Recommendation** | Implement AWS Secrets Manager for runtime credentials (if any are needed for EKS deployment — e.g., peer authentication tokens). Configure automated rotation for high-risk secrets. Use EKS Secrets Store CSI Driver to mount secrets into pods. |
| **Evidence** | `.github/workflows/nebula-publish.yml` (secrets via `${{ secrets.* }}`), no `aws_secretsmanager_*` in IaC, no Vault client imports, no plaintext passwords in `.properties` files |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No evidence of compute hardening, managed patching, or vulnerability scanning. No SSM Patch Manager, no AWS Inspector, no hardened AMI references, no Bottlerocket. Dependencies include known-outdated versions (AWS SDK 1.11.277 from 2018, Jersey 1.19.1, Servlet 2.5). |
| **Gap** | No patching strategy; no vulnerability scanning. Legacy dependencies (AWS SDK v1, Jersey 1.x) have known CVEs that are not being tracked or remediated. |
| **Recommendation** | Add dependency vulnerability scanning (Dependabot, Snyk, or OWASP Dependency Check) to the CI pipeline. For deployment, use hardened base images (AWS Graviton with Bottlerocket for EKS) and enable SSM Patch Manager or EKS managed node group auto-updates. |
| **Evidence** | `build.gradle` (outdated versions: `awsVersion = '1.11.277'`, `jerseyVersion = '1.19.1'`, `servletVersion = '2.5'`), no `.snyk` policy, no SSM configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are configured in the CI/CD pipeline. The GitHub Actions workflows (`nebula-ci.yml`) run `./gradlew build` only — no SAST, no dependency scanning, no container scanning. No Dependabot configuration, no SonarQube, no Semgrep, no CodeGuru. Checkstyle exists (`codequality/checkstyle.xml`) for code style but not for security. |
| **Gap** | No security scanning tools configured — no Dependabot, no SAST, no container scanning. Pipeline has no security validation step. Given the outdated dependencies (AWS SDK 1.11.277, Jersey 1.19.1), this is a significant gap. |
| **Recommendation** | Add Dependabot or Renovate for automated dependency update PRs. Integrate SAST (SonarQube, Semgrep, or Amazon CodeGuru Reviewer) into the CI workflow. Add OWASP Dependency Check Gradle plugin for build-time vulnerability detection. |
| **Evidence** | `.github/workflows/nebula-ci.yml` (build only, no security steps), no `.github/dependabot.yml`, no SonarQube/Semgrep configuration |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No X-Ray SDK, no OpenTelemetry SDK, no Zipkin, no Jaeger. The application uses Netflix Servo for metrics collection (counters, gauges) but Servo provides metrics only, not distributed tracing or trace propagation. No trace ID headers (traceparent, X-Amzn-Trace-Id, X-B3-*) are propagated. |
| **Gap** | No distributed tracing instrumented. Cannot trace requests across Eureka peers or from client to server. Debugging replication failures or registration delays requires manual log correlation. |
| **Recommendation** | Instrument with AWS X-Ray SDK for Java or OpenTelemetry Java Agent (auto-instrumentation). Propagate trace context across peer replication calls. For EKS deployment, use AWS Distro for OpenTelemetry (ADOT) sidecar. |
| **Evidence** | `eureka-client/build.gradle` (no tracing dependencies), `eureka-core/build.gradle` (Netflix Servo for metrics only), no OpenTelemetry/X-Ray/Zipkin imports |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No availability targets, no latency percentile targets (p99, p95), no error budget tracking, no SLO-related CloudWatch alarms or dashboards. The application has an API surface (`has_api_surface=true`) so SLOs are applicable and meaningful for this service. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for the service registry. Critical for a service discovery system where availability directly impacts all dependent services. |
| **Recommendation** | Define SLOs for: registry availability (target 99.99%), registration latency p99 (< 100ms), heartbeat processing latency p99 (< 50ms), and registry fetch latency p99 (< 200ms). Implement error budget tracking using CloudWatch Metrics and Alarms. |
| **Evidence** | No SLO definition files, no CloudWatch alarm configurations, no error budget tracking code. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Netflix Servo provides custom metrics infrastructure with counters and gauges for operational events (registrations, renewals, cancellations, expirations). These are service-specific operational metrics rather than pure infrastructure metrics (CPU/memory). However, they are not business outcome metrics in the traditional sense (no conversion rates or revenue metrics — appropriate given the infrastructure service nature). Servo metrics are published but no CloudWatch integration or dashboard is configured. |
| **Gap** | Infrastructure-adjacent operational metrics exist (via Servo) but are not published to a centralized monitoring system and no dashboards are configured. No business-outcome-level metrics (e.g., service discovery success rate, time-to-discover, client cache hit ratio). |
| **Recommendation** | Publish Servo metrics to CloudWatch using Micrometer or a CloudWatch Servo plugin. Define business-meaningful metrics: service discovery success rate, registry consistency percentage across peers, mean time-to-discover for new registrations. |
| **Evidence** | Netflix Servo dependency (`servo-core:${servoVersion}`) in `eureka-client/build.gradle`, metric annotations in source code, no CloudWatch publishing configuration |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no anomaly detection on error rates or latency. The application has a self-preservation mode (triggered by lease expiration threshold) which is an internal circuit breaker, but no external alerting is configured. |
| **Gap** | No alerting configured. The self-preservation mechanism is an internal safeguard, not an operational alert. No external notification when the registry enters self-preservation mode, when peer replication fails, or when registration rates anomalously change. |
| **Recommendation** | Configure CloudWatch Alarms on key metrics: peer replication failure rate, registry size anomaly detection, self-preservation mode activation, heartbeat renewal success rate. Integrate with SNS for notification and PagerDuty/OpsGenie for incident management. |
| **Evidence** | No CloudWatch alarm definitions, no alerting configuration files, no PagerDuty/OpsGenie integration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No deployed workload found in this repo — deployment strategy cannot be assessed from source code alone. Deployment orchestration may exist in a separate deployment-config or GitOps repo. Future: provide deployment strategy evidence via `additionalPlanContext`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_deployed_workload=false`. No Dockerfile, no Kubernetes manifests, no Helm charts, no CodeDeploy/appspec configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist and run in the CI pipeline. `EurekaClientServerRestIntegrationTest` tests client-server REST interactions end-to-end. MockServer (3.9.2) and WireMock (2.25.1) are used for HTTP-level integration testing. Tests run as part of `./gradlew build` in the CI workflow. Multiple test modules cover cross-module integration (eureka-test-utils provides shared test infrastructure). |
| **Gap** | Integration tests exist for primary workflows but some gaps: no contract tests for the REST API, no chaos/fault-injection testing for peer replication, no integration tests covering AWS-specific paths (EIP binding, Route53, ASG integration). |
| **Recommendation** | Add contract tests (Pact or Spring Cloud Contract) for the Eureka REST API to prevent breaking changes. Add fault-injection tests for peer replication resilience. Consider Testcontainers for testing against real infrastructure in CI. |
| **Evidence** | `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`, `eureka-client/build.gradle` (WireMock 2.25.1, MockServer 3.9.2), `.github/workflows/nebula-ci.yml` (runs `./gradlew build` which executes tests) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns exist beyond the built-in self-preservation mode. No Systems Manager Automation documents, no Lambda-based remediation, no structured runbooks in any format. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No documented procedures for common failure scenarios (peer node failure, split-brain, EIP conflicts, registry inconsistency). |
| **Recommendation** | Create machine-readable runbooks (SSM Automation documents or Step Functions) for common incidents: peer node unresponsive, self-preservation mode triggered, EIP allocation failure, registry divergence between peers. Implement automated remediation for detectable failure patterns. |
| **Evidence** | No runbook files (markdown, YAML, JSON), no SSM documents, no Lambda remediation functions |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership patterns exist. No CODEOWNERS for observability assets, no per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No clear team attribution for service health, no defined escalation paths. |
| **Recommendation** | Define CODEOWNERS for observability configuration. Create per-service CloudWatch dashboards with team-attributed alarms. Document on-call responsibilities and escalation procedures. |
| **Evidence** | No CODEOWNERS file referencing observability, no dashboard definitions, no team-tagged CloudWatch resources |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists because no IaC exists. No `default_tags`, no `tags` blocks on resources, no tagging standards or policies. |
| **Gap** | No tags found on resources; no cost/ownership attribution. Cannot track costs or identify ownership during incidents. |
| **Recommendation** | When creating IaC (per INF-Q10 recommendation), implement consistent tagging from the start: `Service=eureka`, `Team=<owning-team>`, `Environment=<env>`, `CostCenter=<cc>`. Use CDK Aspects or Terraform `default_tags` for enforcement. |
| **Evidence** | No IaC files exist, therefore no tags. No tagging policy documents. |

---

## Learning Materials

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
| `build.gradle` | APP-Q1, INF-Q1, SEC-Q6 | Root build file with dependency versions, Java 8 source compatibility |
| `settings.gradle` | APP-Q2 | Defines 10 subproject modules |
| `.github/workflows/nebula-ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI build pipeline (build+test only) |
| `.github/workflows/nebula-publish.yml` | INF-Q11, SEC-Q5 | Release publishing with GitHub secrets |
| `.github/workflows/nebula-snapshot.yml` | INF-Q11 | Snapshot publishing on master push |
| `eureka-core/build.gradle` | APP-Q1, INF-Q1 | AWS SDK v1 dependencies, Jersey server |
| `eureka-client/build.gradle` | APP-Q1, APP-Q3, OPS-Q1, OPS-Q6 | Client dependencies (Jersey, Servo, HttpClient, WireMock) |
| `eureka-server/src/main/webapp/WEB-INF/web.xml` | INF-Q1, APP-Q5, SEC-Q3 | WAR deployment descriptor, filters, servlet config |
| `eureka-server/src/main/resources/eureka-client.properties` | APP-Q5, APP-Q6, INF-Q6 | Service URL configuration, DNS discovery settings |
| `eureka-core/src/main/java/com/netflix/eureka/aws/EIPManager.java` | INF-Q1, INF-Q3 | EC2 EIP lifecycle management |
| `eureka-core/src/main/java/com/netflix/eureka/aws/ElasticNetworkInterfaceBinder.java` | INF-Q1 | EC2 ENI binding |
| `eureka-core/src/main/java/com/netflix/eureka/aws/Route53Binder.java` | INF-Q1, INF-Q6 | Direct DNS registration |
| `eureka-core/src/main/java/com/netflix/eureka/aws/AwsAsgUtil.java` | INF-Q7 | ASG utility (reads, does not configure scaling) |
| `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` | INF-Q3, INF-Q4, APP-Q3 | Synchronous peer replication |
| `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` | DATA-Q2, INF-Q3 | Registry implementation with peer awareness |
| `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` | DATA-Q2, DATA-Q4 | Core registry logic |
| `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` | SEC-Q3, SEC-Q4 | Authentication filter framework hook |
| `eureka-client/src/main/java/com/netflix/appinfo/AmazonInfo.java` | INF-Q1 | EC2 metadata integration |
| `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java` | OPS-Q6 | Client-server integration test |
| `codequality/checkstyle.xml` | SEC-Q7 | Code style (not security scanning) |
| `eureka-server/src/main/resources/eureka-server.properties` | APP-Q4 | Server configuration (waitTimeInMsWhenSyncEmpty) |
