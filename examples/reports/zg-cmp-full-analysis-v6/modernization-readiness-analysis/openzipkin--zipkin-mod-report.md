# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | openzipkin--zipkin |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | data-gateway (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, observability, tracing |
| **Context** | Distributed tracing system. |
| **Overall Score** | 2.28 / 4.0 |

**Archetype Justification**: Zipkin is primarily a read-heavy data access layer — its core function is ingesting trace spans (via collectors) and serving read queries over stored trace data (via the Query API). The query API dominates the application surface with pagination, filtering, and lookup operations. Database queries (Cassandra, Elasticsearch, MySQL) are the primary logic. Classified as data-gateway.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.73 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 2.22 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.28 / 4.0** | **🟠 Needs Work** | **Remediation Required** |

**Scoring Notes:**
- INF: (2+2+4+4+1+1+1+1+1+1+2) / 11 = 19/11 = 1.73
- APP: (4+2+4+4+1+2) / 6 = 17/6 = 2.83 (APP-Q3 and APP-Q4 are Not Evaluated archetype-N/A but since data-gateway has evaluatable rubric, they score 4)
- DATA: (2+3+2+3) / 4 = 10/4 = 2.50
- SEC: (1+1+1+2+3+3+4) / 7 = 15/7 = 2.14
- OPS: (4+1+1+1+2+3+1+1+1) / 9 = 20/9 = 2.22

---

## Classification

**Tier: Remediation Required**

This repo has 5 High findings, 20 Medium findings, 5 Low findings. The matched rule is: "2-11 High → Remediation Required."

MOD classification is softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. For MOD, 2-11 High findings indicates significant modernization work is needed across multiple dimensions.

**Classification Consistency Check:** consistent (V5 Needs Work band ≡ V6 Remediation Required tier)

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q5: Network Security | 1 | No IaC defining VPC, subnets, or security groups | No network segmentation or isolation defined |
| 2 | INF-Q6: API Entry Point | 1 | No API Gateway, ALB, or managed entry point defined | Direct service exposure without throttling or auth |
| 3 | INF-Q10: Infrastructure as Code Coverage | 1 | No Terraform, CloudFormation, or CDK found — 0% IaC coverage | Infrastructure changes are manual, non-reproducible |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration | No forensic or compliance trail |
| 5 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption configuration for data stores | Data at rest is not encrypted via managed keys |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2, partially automated). GitHub Actions workflows are present for test, deploy, and release.
- **What it enables:** An agent that triggers deployments, checks build status, and manages releases via the existing GitHub Actions pipeline surface.
- **Additional steps:** Formalize API access to the CI/CD pipeline (GitHub API tokens with appropriate scopes for workflow dispatch).
- **Effort:** Low

### Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 = 4). Zipkin IS a tracing system with full distributed tracing support.
- **What it enables:** An agent that queries traces, correlates spans with service behavior, and suggests root causes for latency issues.
- **Additional steps:** Expose Zipkin's own query API as an agent tool interface with appropriate authentication.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (primary trigger < 3) AND INF-Q1 = 2 (supporting trigger < 3). Both conditions met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 2 but Dockerfiles exist extensively (29 Docker files). Contextual guard: container definitions found. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 3 (minimal stored procedures). No commercial DB engines detected — MySQL (open-source via MariaDB client), Cassandra, Elasticsearch are all open-source. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 2 (databases self-managed in Docker), DATA-Q3 = 2 (versions unpinned in IaC). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 for data-gateway archetype. No data processing workloads requiring managed analytics detected. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 2 (partial CI/CD automation — no IaC deploy), OPS-Q5 = 2 (rolling only, no canary/blue-green). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
- Single deployable monolith (`zipkin-server`) packaging all collectors, storage backends, query API, and UI into one Spring Boot application (APP-Q2 = 2)
- Well-structured Maven multi-module layout with clear separation: `zipkin` (core), `zipkin-collector/*` (6 collectors), `zipkin-storage/*` (3 backends), `zipkin-server` (assembly), `zipkin-lens` (UI)
- Components cannot scale independently — collectors, query API, and storage all share the same JVM

**Compute Model Gaps:**
- Containerized but not on managed orchestration (INF-Q1 = 2)
- No EKS, ECS, or Fargate resources defined

**Communication Pattern Strengths (no gaps):**
- APP-Q3 = 4: Synchronous reads are correct for data-gateway archetype; async collectors already supported
- APP-Q4 = 4: No long-running operations — query timeout bounded at 11s

**Recommended Decomposition Approach:**
For a data-gateway archetype, full microservices decomposition is NOT the recommended path. Instead, a bounded decomposition separating the write path (collectors) from the read path (query API) provides the primary scaling benefit. See the Decomposition Strategy section below for detailed approach options.

**Representative AWS Services:** EKS, API Gateway, EventBridge (for decoupling collectors), CloudWatch

**Recommended Patterns:**
- **Anti-corruption Layer** — Isolate the new collector service from the query service's data model
- **Event Sourcing** — Use EventBridge for collector-to-storage decoupling in high-volume deployments
- **Hexagonal Architecture** — Already partially implemented via the StorageComponent interface

**Links:**
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- Databases run as self-managed Docker containers (MySQL, Cassandra, Elasticsearch) per docker-compose examples
- No IaC defines managed database resources (no `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*` resources)
- Database engine versions are defined only in Docker image tags (e.g., `ghcr.io/openzipkin/zipkin-mysql:latest`) with no explicit version pinning in infrastructure code
- Connection pooling (HikariCP) and SSL support already exist in the application

**Recommended Migration Targets (respecting preferences — prefer EKS, Aurora, DynamoDB):**
- **MySQL → Amazon Aurora MySQL**: Aurora provides Multi-AZ failover, automated backups, and read replicas. The existing JOOQ-based data access layer and HikariCP pooling would require only connection string changes.
- **Cassandra → Amazon Keyspaces (or self-managed on EKS)**: Given the `prefer: ["eks"]` preference, running Cassandra on EKS with managed operators is viable. Amazon Keyspaces offers a serverless Cassandra-compatible option but has feature gaps with CQL.
- **Elasticsearch → Amazon OpenSearch Service**: Already has OpenSearch compatibility tested (ITOpenSearchStorageV2). Migration to managed OpenSearch would be straightforward.

**Representative AWS Services:** Aurora, Amazon Keyspaces, Amazon OpenSearch Service, DMS

**Migration Tools:** AWS DMS for MySQL migration, native Cassandra migration tools, OpenSearch snapshot/restore

**Immediate Actions:**
1. Define database infrastructure in Terraform/CDK (Aurora MySQL, OpenSearch domain)
2. Update connection configuration to point to managed endpoints
3. Enable Multi-AZ and automated backups
4. Test with existing integration test suite (Testcontainers can be reconfigured to point at managed instances)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 1):** Zero infrastructure defined as code. All infrastructure (databases, networking, compute) is either Docker-compose examples or manually provisioned.
- **CI/CD (INF-Q11 = 2):** GitHub Actions handles application build, test, and Docker image publication. However, there is no infrastructure deployment automation — no Terraform apply, no CDK deploy, no CloudFormation stack updates in the pipeline.
- **Deployment Strategy (OPS-Q5 = 2):** Docker images are pushed to registries (GHCR, Docker Hub) but no canary or blue/green deployment strategy exists. Production deployment is manual.
- **Integration Testing (OPS-Q6 = 3):** Comprehensive Docker-based integration tests via Testcontainers, but they test storage backends in isolation rather than full end-to-end deployment scenarios.

**Recommended DevOps Toolchain (respecting preferences — prefer EKS):**
- **IaC:** Terraform or CDK for defining EKS cluster, Aurora/OpenSearch, VPC networking, and security groups
- **Container Orchestration:** EKS with Helm charts for Zipkin deployment
- **CI/CD Enhancement:** Extend GitHub Actions with Terraform plan/apply stages and EKS deployment via Helm
- **Deployment Strategy:** Implement canary deployments via Argo Rollouts on EKS or AWS App Mesh traffic shifting

**Representative AWS Services:** EKS, CodeBuild, CodePipeline, CloudFormation/CDK, ECR, X-Ray, CloudWatch

**Immediate Actions:**
1. Define VPC and EKS cluster in Terraform/CDK
2. Create Helm chart for Zipkin server deployment
3. Add Terraform plan/apply stages to GitHub Actions pipeline
4. Implement canary deployment strategy via Argo Rollouts or Flagger

**Learning Resources:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

---

## Decomposition Strategy

Since APP-Q2 = 2 (monolith with identifiable modules), this section provides decomposition guidance.

### Recommended Approach: Conditional / Adaptive

| Approach | Description | Applicability to Zipkin | Level of Effort | Recommendation |
|----------|-------------|------------------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services while keeping the monolith running. | Applicable — extract collectors as independent services while keeping query API in the monolith initially. The Maven module boundaries (`zipkin-collector/*`) provide natural extraction points. | Medium to High | ✅ Viable |
| **Conditional / Adaptive** | Containerize as-is, then selectively extract high-value services based on business priority. | Best fit — deploy as a single container on EKS first (quick win), then selectively separate the collector (write) path from the query (read) path when independent scaling is needed. | Low to Medium | ✅ **Recommended** |
| **Big-Bang Rewrite** | Rewrite as microservices from scratch. | Not appropriate — the existing codebase is well-structured with clean interfaces and comprehensive test coverage. No justification for rewrite. | Very High | ⚠️ **Not Recommended** |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate the new collector service from the query service's data model. | When extracting collectors as a separate deployment — place an ACL between the collector service and the shared storage interface. |
| **Event Sourcing** | Capture spans as events for decoupled ingestion pipelines. | When separating write path — collectors publish span events to EventBridge/MSK, storage consumers process independently. |
| **Hexagonal Architecture (Ports and Adapters)** | Already partially implemented via the `StorageComponent` interface. | Already in place — maintain this pattern when creating new services. Each extracted service should preserve the ports/adapters structure. |

### Effort Estimation

| Factor | Signal | Analysis |
|--------|--------|------------|
| Module boundaries | Clear Maven multi-module structure (`zipkin-collector/*`, `zipkin-storage/*`, `zipkin-server`) with clean interfaces | Low effort — boundaries are already well-defined |
| Data coupling | StorageComponent abstraction provides a unified interface; all backends share the same logical schema | Medium effort — shared storage model requires coordination |
| Stored procedures | None — all logic in application layer via JOOQ and native drivers | Low effort — no database coupling |
| Communication patterns | Async collectors (Kafka, RabbitMQ) already supported alongside sync HTTP | Low effort — async infrastructure exists |
| CI/CD maturity | Application CI exists (GitHub Actions) but no IaC deployment | Medium effort — deployment pipeline needs creation |
| Test coverage | Comprehensive Testcontainers integration tests for all backends | Low effort — test suite can validate decomposition |

**Calibrated Estimate:** Low to Medium effort for the recommended Conditional/Adaptive approach. Initial EKS deployment (single container) is achievable quickly. Subsequent collector extraction is bounded by the need to define independent Helm charts and configure message broker routing.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is containerized — a multi-stage Dockerfile exists at `docker/Dockerfile` producing Alpine-based JRE images. Docker Compose files demonstrate various deployment configurations. However, no IaC defines managed container orchestration (no ECS/EKS/Fargate/Lambda resources). Deployment relies on manually running Docker containers or docker-compose. |
| **Gap** | No managed container orchestration defined. Containers exist but are not deployed to ECS, EKS, or Fargate via infrastructure code. |
| **Recommendation** | Deploy Zipkin on Amazon EKS (per preferences) with a Helm chart defining the deployment, service, and ingress. Define EKS cluster infrastructure in Terraform/CDK. |
| **Evidence** | `docker/Dockerfile`, `docker/examples/docker-compose*.yml`, absence of Terraform/CDK/CloudFormation |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Three database backends are supported: MySQL, Cassandra, and Elasticsearch. All are deployed as self-managed Docker containers in the example configurations. The application code supports SSL connections and connection pooling (HikariCP for MySQL, Cassandra driver pooling). No IaC defines managed database services. |
| **Gap** | All databases are self-managed in Docker containers. No RDS/Aurora, Keyspaces, or OpenSearch Service resources defined. |
| **Recommendation** | Migrate to Aurora MySQL, Amazon Keyspaces (or Cassandra on EKS), and Amazon OpenSearch Service. Define in Terraform/CDK with Multi-AZ enabled. |
| **Evidence** | `docker/examples/docker-compose-mysql.yml`, `docker/examples/docker-compose-cassandra.yml`, `docker/examples/docker-compose-elasticsearch.yml`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `data-gateway`. No multi-step workflows exist in the read path. The primary operations are span ingestion (write) and trace query (read), both of which are single-step request/response patterns. No background maintenance jobs requiring orchestration were identified. |
| **Gap** | N/A |
| **Recommendation** | Dedicated workflow orchestration is not applicable for this archetype. No gap exists. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `data-gateway`. Synchronous reads dominate the query path (correct design). For the write/ingestion path, Zipkin supports multiple managed and self-managed message collectors: Kafka, RabbitMQ, ActiveMQ, and Pulsar. These are configured via environment variables and can point to managed services (Amazon MSK, Amazon MQ). The architecture correctly separates sync reads from async write-path collection. |
| **Gap** | N/A — synchronous reads are appropriate for this archetype, and async ingestion via message collectors is already supported. |
| **Recommendation** | When deploying, use managed messaging services (Amazon MSK for Kafka, Amazon MQ for ActiveMQ/RabbitMQ) rather than self-managed brokers. The application already supports this via configuration. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (collector configuration for kafka, rabbitmq, activemq, pulsar) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defines VPC, subnets, security groups, NACLs, or any network segmentation. The Docker Compose examples expose services on default Docker networking with no isolation between tiers. No VPC endpoints, PrivateLink, or network policies are defined. |
| **Gap** | Zero network security infrastructure defined. Services would be deployed without isolation. |
| **Recommendation** | Define VPC with private subnets for databases and public subnet (or private + NAT) for the Zipkin server. Create security groups with least-privilege rules. Use VPC endpoints for AWS service access. |
| **Evidence** | Absence of any `.tf`, CloudFormation, or CDK files defining VPC/network resources |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point is defined. The Zipkin server exposes port 9411 directly. Docker Compose examples map the container port directly without any load balancer or gateway. |
| **Gap** | Direct service exposure with no throttling, authentication, or request validation at the edge. |
| **Recommendation** | Deploy an Application Load Balancer (ALB) in front of the Zipkin EKS service, or use API Gateway for the query API with throttling and optional authentication. |
| **Evidence** | `docker/Dockerfile` (EXPOSE 9411), `docker/examples/docker-compose.yml`, `zipkin-server/src/main/resources/zipkin-server-shared.yml` (server.port: 9411) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No ASG, ECS service scaling, EKS HPA, or Lambda concurrency limits are defined. The Docker deployments use static container counts. |
| **Gap** | All capacity is statically provisioned. No mechanism to handle traffic spikes or scale down during low demand. |
| **Recommendation** | When deploying on EKS, configure Horizontal Pod Autoscaler (HPA) based on CPU/memory and custom metrics (requests-per-second, queue depth for collectors). Consider Karpenter for node-level autoscaling. |
| **Evidence** | Absence of autoscaling configuration in any IaC or Kubernetes manifests |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup or recovery configuration exists. No `backup_retention_period`, no `aws_backup_plan`, no PITR configuration, no S3 versioning for data. The Docker-based databases have no backup automation. |
| **Gap** | No backup strategy for any data store. Data loss risk in case of failure. |
| **Recommendation** | When migrating to managed databases, enable automated backups: Aurora automated backups with PITR, OpenSearch automated snapshots, and define an AWS Backup plan for cross-service backup governance. |
| **Evidence** | Absence of backup configuration in any files |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration exists. Docker Compose examples run single instances of each service. No load balancer, no replica configuration, no AZ-awareness in any deployment artifact. |
| **Gap** | Single-instance deployment with no fault isolation. An instance failure takes down the entire service. |
| **Recommendation** | Deploy Zipkin on EKS across 2+ AZs with multiple replicas. Configure Aurora Multi-AZ for MySQL, multi-node Cassandra cluster, and multi-AZ OpenSearch domain. |
| **Evidence** | `docker/examples/docker-compose*.yml` (single container per service), absence of multi-AZ IaC |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure is defined as code. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist. All infrastructure (compute, networking, databases, messaging) would need to be created manually. |
| **Gap** | 0% IaC coverage. All infrastructure changes are manual and non-reproducible. |
| **Recommendation** | Create Terraform modules (or CDK stacks) defining: EKS cluster, VPC/networking, Aurora MySQL, OpenSearch domain, MSK cluster, ALB, and monitoring. Start with the compute and database layers as highest priority. |
| **Evidence** | Complete absence of IaC files in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides automated build, test, and Docker image publication. Workflows cover: multi-JDK testing (`test.yml`), Docker-based integration tests (`test.yml` - test_docker job), deployment to Sonatype/Docker Hub (`deploy.yml`), release creation (`create_release.yml`), and security scanning (`security.yml`). However, there is no infrastructure deployment automation — no Terraform plan/apply, no CDK deploy, no CloudFormation in the pipeline. |
| **Gap** | Application CI/CD exists but infrastructure deployment is entirely manual. No IaC automation in the pipeline. |
| **Recommendation** | Extend GitHub Actions with Terraform plan (on PR) and apply (on merge) stages. Add Helm deployment to EKS as a deploy step. Implement automated rollback on health check failure. |
| **Evidence** | `.github/workflows/test.yml`, `.github/workflows/deploy.yml`, `.github/workflows/create_release.yml`, `.github/workflows/security.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 17 (compilation target) with Spring Boot 3.5.12 and modern dependencies. The core library targets Java 8 for backward compatibility but the server and all modules compile to Java 17. Framework stack is modern: Spring Boot 3.x, Armeria 1.37.0 (modern async HTTP server), Jackson 2.21.2. Frontend uses TypeScript with React and Vite. CI tests on JDK 21 and 25. |
| **Gap** | N/A — language, framework, and SDK are all current. |
| **Recommendation** | N/A — the technology stack is mature and cloud-native ready. |
| **Evidence** | `pom.xml` (maven.compiler.release=17, spring-boot.version=3.5.12, armeria.version=1.37.0), `.github/workflows/test.yml` (java_version: 21, 25) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit (zipkin-server) that packages all collectors, storage backends, query API, and UI into one Spring Boot application. The codebase has a well-structured Maven multi-module layout with clear separation: `zipkin` (core), `zipkin-collector/*` (6 collectors), `zipkin-storage/*` (3 backends), `zipkin-server` (assembly), `zipkin-lens` (UI). Modules have clean interfaces. However, everything compiles into a single executable JAR and deploys as one container. Storage backends share the same JVM and deployment lifecycle. |
| **Gap** | Monolith with identifiable modules but shared deployment lifecycle. Collectors, query API, and storage all scale together even when only one dimension needs scaling. |
| **Recommendation** | For a data-gateway archetype, the modular monolith design is acceptable. If scaling becomes an issue, consider separating collectors (write path) from query API (read path) as independent deployments sharing the same storage backend. This is a bounded decomposition, not full microservices. |
| **Evidence** | `pom.xml` (single modules list), `docker/Dockerfile` (single image), `zipkin-server/src/main/java/zipkin/server/ZipkinServer.java` (single Spring Boot app) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `data-gateway`. Synchronous reads dominate the query API (correct design for trace lookups and service queries). The write path supports both synchronous HTTP/gRPC ingestion AND asynchronous collection via Kafka, RabbitMQ, ActiveMQ, and Pulsar. This is the correct communication pattern for a data-gateway: sync reads are appropriate, and async write-back/ingestion uses managed messaging where configured. |
| **Gap** | N/A — synchronous reads are the correct design for this archetype, and async ingestion is already supported. |
| **Recommendation** | Synchronous query API is appropriate. No conversion to async is recommended for the read path. For high-volume deployments, prefer async collectors (Kafka/RabbitMQ) over HTTP for span ingestion to decouple producers from the storage write path. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (collector configs for kafka, rabbitmq, activemq, pulsar), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `data-gateway`. No user-facing operations exceed 30 seconds. The query API serves indexed trace lookups, service name queries, and dependency graphs — all bounded by database query timeouts (configurable via `QUERY_TIMEOUT: 11s`). Span ingestion is lightweight (decode + store). No batch exports, bulk reindexing, or heavy computation exists in the user-facing path. |
| **Gap** | N/A — no long-running operations exist in the user-facing surface. |
| **Recommendation** | No async job infrastructure is needed for the current surface. The query timeout configuration (11s default) provides appropriate bounded execution. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (query.timeout: 11s), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No formal API specification (OpenAPI/Swagger) exists. The API uses URL path versioning (`/api/v2/`) which is a good pattern, but no formal versioning strategy documentation, backward compatibility guarantees, or deprecation process exists. No API spec file that could enforce versioning consistency. |
| **Gap** | Ad hoc versioning — `/api/v2/` paths exist in code but no formal strategy, no OpenAPI spec, no backward compatibility guarantee documentation. |
| **Recommendation** | Generate an OpenAPI specification from the existing Java API annotations. Document the versioning strategy and backward compatibility guarantees. This also enables the API-aware agent win. |
| **Evidence** | `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (V2 in class name implies version), absence of OpenAPI/Swagger files |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zipkin includes Eureka service discovery support (configured via `EUREKA_SERVICE_URL` environment variable). Docker Compose examples demonstrate Eureka integration. However, this is optional and most deployment configurations use environment variables for endpoint configuration (e.g., `CASSANDRA_CONTACT_POINTS`, `ES_HOSTS`, `MYSQL_HOST`). No dynamic service discovery is the default. |
| **Gap** | Environment variables for service endpoints with no dynamic discovery as the default deployment pattern. Eureka support exists but is opt-in and legacy. |
| **Recommendation** | When deploying on EKS, leverage Kubernetes-native service discovery (CoreDNS, Service resources). For AWS-native discovery, consider AWS Cloud Map. Remove dependency on Eureka in favor of cloud-native alternatives. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (discovery.eureka section, env vars for all backend hosts), `docker/examples/docker-compose-eureka.yml` |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Trace data (spans, annotations) is structured but stored in databases (Cassandra, Elasticsearch, MySQL). Binary annotation values are stored as BLOBs in MySQL. No S3 or object storage is used for any data. Elasticsearch provides search capabilities over trace data. No document parsing pipeline exists (not needed for trace data). |
| **Gap** | Data stored in databases only. For long-term trace archival or large binary payloads, no object storage tier exists. |
| **Recommendation** | Consider S3 for long-term trace archival with lifecycle policies (e.g., archive traces older than 30 days to S3 Glacier). This reduces database costs for historical data while maintaining accessibility via Athena queries. |
| **Evidence** | `zipkin-storage/mysql-v1/src/main/resources/mysql.sql` (BLOB column for a_value), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configurations) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zipkin has a well-defined storage abstraction layer. The `zipkin2.storage.StorageComponent` interface provides a unified contract, with implementations for each backend (Cassandra, Elasticsearch, MySQL). The `zipkin-tests` module provides shared integration tests (`ITStorage`) that all backends must pass. Data access is centralized through the storage interface. Some direct access patterns exist in auxiliary code (e.g., the dependency linker). |
| **Gap** | Mostly centralized. The storage interface is clean, but some auxiliary operations (dependency calculation, autocomplete) have backend-specific paths. |
| **Recommendation** | The existing storage abstraction is well-designed. No immediate action needed — this is a strength of the architecture. |
| **Evidence** | `zipkin-storage/` module structure, `zipkin-tests/` shared integration tests, `zipkin/src/main/java/zipkin2/storage/` (StorageComponent interface) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database engine versions are defined in Docker image tags for test images (e.g., `zipkin-mysql`, `zipkin-cassandra`, `zipkin-elasticsearch8`, `zipkin-elasticsearch9`, `zipkin-opensearch2`). The application configuration uses generic connection parameters without version pinning. No IaC exists to define engine versions. The driver versions are pinned in the POM: Cassandra driver 4.19.2, MariaDB client 3.5.7. No explicit documentation of supported engine versions or EOL tracking. |
| **Gap** | Some versions implicit via Docker image tags; no explicit version pinning in infrastructure code; EOL status undocumented. |
| **Recommendation** | When defining databases in IaC, explicitly pin engine versions (e.g., `engine_version = "8.0.35"` for Aurora MySQL). Document supported engine versions and create a version update procedure. |
| **Evidence** | `pom.xml` (java-driver.version=4.19.2, mariadb-java-client.version=3.5.7), `docker/test-images/zipkin-elasticsearch8/`, `docker/test-images/zipkin-elasticsearch9/`, `docker/test-images/zipkin-opensearch2/` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The MySQL schema (`mysql.sql`) uses standard DDL only — `CREATE TABLE` and `ALTER TABLE ADD INDEX`. No stored procedures, triggers, or functions. The Cassandra schema uses standard CQL. Data access is through JOOQ (MySQL) and native Cassandra driver with prepared statements. No proprietary SQL constructs. Minimal use of MySQL-specific features (`ENGINE=InnoDB ROW_FORMAT=COMPRESSED`). |
| **Gap** | Minimal — MySQL-specific `ROW_FORMAT=COMPRESSED` and `ENGINE=InnoDB` are engine-specific but standard for MySQL/Aurora compatibility. No business logic in the database. |
| **Recommendation** | No action needed. The schema is portable and compatible with Aurora MySQL. The use of JOOQ provides an abstraction layer over SQL generation. |
| **Evidence** | `zipkin-storage/mysql-v1/src/main/resources/mysql.sql`, `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql` |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration exists. No IaC defines CloudTrail trails, log validation, or immutable storage. The application has internal logging (SLF4J with trace ID correlation in log patterns) but no cloud audit trail. |
| **Gap** | No CloudTrail or audit logging infrastructure defined. No forensic trail for API access or infrastructure changes. |
| **Recommendation** | Define CloudTrail in IaC with log file validation and S3 Object Lock for immutable storage. Enable CloudWatch Logs integration for centralized log management. |
| **Evidence** | Absence of `aws_cloudtrail` or equivalent in any IaC, `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging.pattern.level with traceId) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS or encryption at rest configuration exists. No IaC defines encryption for databases or storage. The Docker-based databases use default (unencrypted) storage. No `kms_key_id` references anywhere. |
| **Gap** | No encryption at rest configured for any data store. Trace data (which may contain sensitive service names, endpoints, and annotation values) is stored unencrypted. |
| **Recommendation** | When migrating to managed databases, enable encryption at rest: Aurora storage encryption with KMS, OpenSearch domain encryption, and define customer-managed KMS keys for sensitive data stores. |
| **Evidence** | Absence of KMS configuration in any files |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication is configured on the Zipkin server itself. The query API and collector endpoints are open by default. The configuration shows `allowed-origins: "*"` for CORS with no auth middleware. Elasticsearch backend connections use basic auth (`ES_USERNAME`/`ES_PASSWORD`), but this is backend-to-backend, not API-level auth. |
| **Gap** | All API endpoints are open with no authentication. Any client can query traces and submit spans without credentials. |
| **Recommendation** | Deploy API Gateway in front of Zipkin with OAuth2/JWT authentication for the query API. For the collector API, implement API key authentication or mTLS for service-to-service span submission. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (query.allowed-origins: "*", no auth config), absence of auth middleware in server code |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No centralized identity provider integration exists for the Zipkin API or UI. The application manages no authentication at all (open access). The Eureka test image has a basic security configuration (`EurekaSecurity.java`) for the Eureka registration endpoint, but this is test-only. The Elasticsearch backend supports credential files that can be dynamically refreshed (`DynamicCredentialsFileLoader`), suggesting potential for federation. |
| **Gap** | No identity provider integration. The application has no auth, so there's nothing to federate. |
| **Recommendation** | Integrate with Amazon Cognito for user authentication on the Zipkin UI and query API. Use IAM roles for service-to-service authentication (collectors to Zipkin server). |
| **Evidence** | `docker/test-images/zipkin-eureka/src/main/java/zipkin/test/EurekaSecurity.java` (test-only), `zipkin-server/src/main/java/zipkin2/server/internal/elasticsearch/DynamicCredentialsFileLoader.java` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Production credentials are managed via environment variables with no plaintext secrets in source code. The configuration file uses environment variable references for all sensitive values: `${CASSANDRA_PASSWORD:}`, `${ES_PASSWORD:}`, `${MYSQL_PASS:}`, `${RABBIT_PASSWORD:guest}`. GitHub Actions uses GitHub Secrets for CI/CD credentials (`secrets.GPG_SIGNING_KEY`, `secrets.SONATYPE_PASSWORD`, `secrets.DOCKERHUB_TOKEN`). Elasticsearch supports dynamic credential refresh from a file (`ES_CREDENTIALS_FILE`). However, no dedicated secrets management service (Secrets Manager, Vault) is referenced, and no rotation is configured. Docker Compose examples contain hardcoded default passwords (`MYSQL_USER=zipkin`, `MYSQL_PASS=zipkin`). |
| **Gap** | Environment variables for secrets without rotation. Docker Compose examples contain hardcoded default credentials (acceptable for development examples but not production). No Secrets Manager or Vault integration. |
| **Recommendation** | Integrate AWS Secrets Manager for database credentials with automated rotation. Reference Secrets Manager ARNs from EKS pods via External Secrets Operator or CSI Secrets Store driver. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (env var references for all credentials), `.github/workflows/deploy.yml` (GitHub Secrets), `docker/examples/docker-compose-mysql.yml` (hardcoded dev credentials) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Trivy vulnerability scanner runs in CI (`security.yml`) scanning for HIGH and CRITICAL severity vulnerabilities and secrets. The Docker image uses a minimal Alpine-based JRE image (`ghcr.io/openzipkin/java:${java_version}-jre`) which reduces attack surface. The container runs as a non-root user (`USER zipkin`). However, no SSM Patch Manager or formal patching process is defined (expected since no EC2 instances are used). |
| **Gap** | Vulnerability scanning in CI but no container image scanning in a registry (no ECR scanning). No formal patch management process documented. |
| **Recommendation** | Push images to ECR and enable ECR image scanning. Consider using AWS Inspector for continuous vulnerability monitoring of running containers on EKS. |
| **Evidence** | `.github/workflows/security.yml` (Trivy), `docker/Dockerfile` (non-root user, Alpine-based image) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Trivy runs in CI with filesystem scanning for both vulnerabilities and secrets, gating on HIGH/CRITICAL severity. This effectively provides dependency vulnerability scanning and secret detection in every PR and push to master. The pipeline fails on critical findings (exit-code: 1). Container image is built from a controlled base image with multi-stage builds minimizing attack surface. |
| **Gap** | N/A — security scanning is integrated into CI with blocking gates. |
| **Recommendation** | Consider adding SAST (SonarQube or Semgrep) for code-level vulnerability detection in addition to the existing dependency/secret scanning. |
| **Evidence** | `.github/workflows/security.yml` (Trivy with exit-code: 1, severity: HIGH,CRITICAL, scanners: vuln,secret) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Zipkin IS a distributed tracing system. The application itself supports self-tracing (`SELF_TRACING_ENABLED`) with configurable sample rates and flush intervals. The logging pattern includes trace ID propagation (`%X{traceId}/%X{spanId}`). The application natively understands and propagates trace context across all its internal operations. |
| **Gap** | N/A — this IS a tracing system with full self-tracing capabilities. |
| **Recommendation** | N/A — tracing is a core feature. Ensure self-tracing is enabled in production for operational visibility into Zipkin's own performance. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (self-tracing section, logging.pattern.level with traceId/spanId) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No CloudWatch alarms on latency percentiles, no error budget tracking, no formal service level objectives documented. The application has Micrometer metrics integration (micrometer.version=1.16.4) and Prometheus endpoint support, but no SLO definitions consume these metrics. |
| **Gap** | No formal SLOs defined for trace query latency, span ingestion rate, or availability. |
| **Recommendation** | Define SLOs for: (1) Query API p99 latency < 500ms, (2) Span ingestion success rate > 99.9%, (3) Service availability > 99.9%. Implement CloudWatch alarms based on these SLOs with error budget tracking. |
| **Evidence** | `pom.xml` (micrometer.version=1.16.4), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (prometheus endpoint), absence of SLO definitions |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application publishes Prometheus metrics via Micrometer (disabling auto-time in favor of custom naming: `metrics.web.server.auto-time-requests: false`). However, these appear to be infrastructure metrics. No custom business metrics (traces stored per minute, unique services reporting, query patterns, storage utilization trends) are explicitly defined in the observable code or configuration. |
| **Gap** | Infrastructure metrics only. No business outcome metrics (trace volume, service coverage, query patterns). |
| **Recommendation** | Publish custom CloudWatch metrics for: traces ingested per minute, unique services reporting traces, query volume by endpoint, storage growth rate. These metrics inform capacity planning and demonstrate value. |
| **Evidence** | `zipkin-server/src/main/resources/zipkin-server-shared.yml` (management.metrics section, auto-time-requests: false) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configuration exists. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. The application exports metrics to Prometheus but no alert rules are defined. The Docker Compose prometheus example (`docker-compose-prometheus.yml`) demonstrates metrics collection but not alerting. |
| **Gap** | No alerting configured. Degradation or outages would not be detected automatically. |
| **Recommendation** | Define CloudWatch alarms for: error rate spikes, latency anomalies, storage throttle activation, collector queue depth. Enable CloudWatch anomaly detection on key metrics. |
| **Evidence** | `docker/examples/docker-compose-prometheus.yml`, absence of alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker images are built and pushed to registries (GHCR, Docker Hub) via CI. The deployment process is: build image → push to registry → manual deployment (pull latest). No canary, blue/green, or rolling deployment with health checks is defined. The Docker health check (`docker-healthcheck`) provides basic container health verification but is not tied to a deployment strategy. |
| **Gap** | No staged rollout strategy. Deployments go directly to production with no traffic shifting or canary analysis. |
| **Recommendation** | Implement canary deployments on EKS using Argo Rollouts or Flagger with automated analysis based on error rate and latency metrics before promoting to full traffic. |
| **Evidence** | `.github/workflows/deploy.yml`, `docker/Dockerfile` (HEALTHCHECK), `build-bin/docker/docker_push` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive Docker-based integration tests exist using Testcontainers. Each storage backend (MySQL, Cassandra, Elasticsearch/OpenSearch) and collector (Kafka, RabbitMQ, ActiveMQ, Pulsar) has dedicated integration tests that run in CI via the `test_docker` job matrix. Tests cover actual database operations, message consumption, and API behavior against real backends. However, there are no end-to-end deployment integration tests (testing the full deployed stack). |
| **Gap** | Integration tests cover individual backends and collectors in isolation, not the full deployment topology. No smoke tests against a deployed environment. |
| **Recommendation** | Add post-deployment smoke tests that verify the full stack (collector → storage → query API) works end-to-end in a staging environment before production promotion. |
| **Evidence** | `.github/workflows/test.yml` (test_docker job matrix), `zipkin-storage/elasticsearch/src/test/java/zipkin2/elasticsearch/integration/IT*.java`, Testcontainers dependency in `pom.xml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no self-healing automation. No Systems Manager Automation documents, no Lambda-based remediation. The `SECURITY.md` file documents security vulnerability reporting process but not operational incident response. |
| **Gap** | No runbooks or incident response automation. All incident response is ad hoc. |
| **Recommendation** | Create operational runbooks for common failure scenarios: storage backend unavailable, collector queue backup, high query latency. Automate common remediations (restart unhealthy pods, scale collectors on queue depth). |
| **Evidence** | `SECURITY.md` (security process only), absence of runbook files |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS for observability assets, no per-service dashboards defined, no named alarm owners, no SLO definitions with team attribution. The project is open-source with community governance rather than formal operational ownership. |
| **Gap** | No observability ownership model. No dashboards, alarms, or SLOs with team attribution. |
| **Recommendation** | When deploying in an organizational context, define observability ownership: create CloudWatch dashboards per component (query, collectors, storage), assign alarm owners, and document escalation paths. |
| **Evidence** | Absence of CODEOWNERS referencing observability, absence of dashboard definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging exists because no IaC exists. No `default_tags`, no `tags` blocks, no tagging standards documented. Docker containers have labels (`org.opencontainers.image.description`) but no AWS resource tagging. |
| **Gap** | No tagging strategy. Cost allocation, ownership attribution, and environment identification are not possible. |
| **Recommendation** | When defining infrastructure in IaC, implement a tagging standard: `Environment`, `Service`, `Team`, `CostCenter`. Use Terraform `default_tags` provider block and enforce via AWS Config required-tags rule. |
| **Evidence** | `docker/Dockerfile` (OCI labels only), absence of IaC with tags |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | APP-Q1, DATA-Q3, OPS-Q1, OPS-Q2, OPS-Q6 | Parent POM with dependency versions, Java 17 target |
| `docker/Dockerfile` | INF-Q1, INF-Q6, SEC-Q6, OPS-Q5, OPS-Q9 | Multi-stage Docker build, non-root user, Alpine JRE |
| `zipkin-server/src/main/resources/zipkin-server-shared.yml` | INF-Q2, INF-Q3, INF-Q4, INF-Q6, APP-Q3, APP-Q4, APP-Q6, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q2, OPS-Q3 | Primary application configuration with all env var bindings |
| `.github/workflows/test.yml` | INF-Q11, OPS-Q6, APP-Q1 | CI test pipeline with multi-JDK and Docker integration tests |
| `.github/workflows/deploy.yml` | INF-Q11, SEC-Q5, OPS-Q5 | Deployment pipeline with GitHub Secrets |
| `.github/workflows/security.yml` | SEC-Q6, SEC-Q7 | Trivy vulnerability and secret scanning |
| `docker/examples/docker-compose-mysql.yml` | INF-Q2, SEC-Q5 | MySQL Docker deployment with hardcoded dev credentials |
| `docker/examples/docker-compose-cassandra.yml` | INF-Q2 | Cassandra Docker deployment |
| `docker/examples/docker-compose-elasticsearch.yml` | INF-Q2 | Elasticsearch Docker deployment |
| `zipkin-storage/mysql-v1/src/main/resources/mysql.sql` | DATA-Q1, DATA-Q4 | MySQL DDL schema — no stored procedures |
| `zipkin-storage/cassandra/src/main/resources/zipkin2-schema.cql` | DATA-Q4 | Cassandra schema — standard CQL |
| `zipkin-server/src/main/java/zipkin/server/ZipkinServer.java` | APP-Q2 | Single Spring Boot entry point |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` | APP-Q3, APP-Q4, APP-Q5, INF-Q3 | Query API implementation |
| `zipkin-server/src/main/java/zipkin2/server/internal/elasticsearch/DynamicCredentialsFileLoader.java` | SEC-Q4 | Dynamic credential refresh for Elasticsearch |
| `docker/test-images/zipkin-eureka/src/main/java/zipkin/test/EurekaSecurity.java` | SEC-Q4 | Test-only Eureka security config |
| `docker/examples/docker-compose-prometheus.yml` | OPS-Q4 | Prometheus metrics collection example |
| `SECURITY.md` | OPS-Q7 | Security vulnerability reporting process |
