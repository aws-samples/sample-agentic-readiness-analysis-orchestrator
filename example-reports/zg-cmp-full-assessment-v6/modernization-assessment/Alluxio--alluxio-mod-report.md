# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Alluxio--alluxio |
| **Date** | 2026-05-07 |
| **Repo Type** | application |
| **Service Archetype** | data-gateway (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, storage, distributed |
| **Context** | Data orchestration / virtual distributed file system. JVM, distributed storage caching layer. |
| **Overall Score** | 1.90 / 4.0 |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true |

**Archetype Justification**: This system is a distributed storage caching layer whose primary operations are read-heavy data access (file reads, block reads, metadata lookups) served via gRPC and REST APIs. It has an embedded metadata store (RocksDB) but its core role is as a data access gateway between compute frameworks and underlying storage systems. Classified as data-gateway.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.25 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.90 / 4.0** | **🟠 Needs Work** | **Critical** |

**Scoring Notes:**
- INF: (3+2+4+1+2+1+1+2+2+2) / 10 = 20/10 = 2.00 (INF-Q3 excluded as Not Evaluated archetype-N/A)
- APP: (2+2+2+3) / 4 = 9/4 = 2.25 (APP-Q3, APP-Q4 excluded as Not Evaluated archetype-N/A)
- DATA: (2+3+2+4) / 4 = 11/4 = 2.75
- SEC: (1+1+2+1+2+1+1) / 7 = 9/7 = 1.29
- OPS: (2+1+1+1+1+2+1+1+1) / 9 = 11/9 = 1.22
- Overall: (2.00+2.25+2.75+1.29+1.22) / 5 = 9.51/5 = 1.90

---

## Classification

**Tier: 🟠 Remediation Required**

This repo has 5 High findings, 24 Medium findings, 3 Low findings. Rule matched: "2-11 High → Remediation Required".

MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. With 11 High-severity findings, this repository requires significant remediation effort across security, operations, and infrastructure before it can be considered cloud-native ready.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured in IaC | No forensic capability for security incidents |
| 2 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption-at-rest configuration for embedded RocksDB or journal data | Data-at-rest is unprotected |
| 3 | OPS-Q2: SLO Definitions | 1 | No SLO/SLI definitions or error budgets found | Cannot measure service quality or prioritize improvements |
| 4 | SEC-Q5: Secrets Management | 2 | No secrets management integration; AWS credentials written to plaintext in Vagrant scripts | Credential exposure risk |
| 5 | INF-Q5: Network Security | 1 | No VPC, security group, or network segmentation defined in any IaC | Services may be exposed without network isolation |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2 — GitHub Actions workflows for unit tests, integration tests, and style checks are in place)
- **What it enables:** An agent that triggers builds, checks test status, and manages PR workflows via GitHub Actions API
- **Additional steps:** Deployment automation needs to be added to CI/CD before the agent can manage full release lifecycle
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — 177 markdown files, extensive `docs/` directory with Jekyll site, configuration guides, and architecture documentation
- **What it enables:** A RAG-based knowledge agent that indexes Alluxio documentation to answer developer and operator questions about configuration, deployment, and troubleshooting
- **Additional steps:** Documentation needs to be indexed into a vector store; some docs may be outdated and need curation
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (distributed monolith), INF-Q1=3 (partial managed compute) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=3, container definitions already exist (12 Dockerfiles, Helm charts, K8s operator) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures), no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2=2 triggers, but database is embedded RocksDB by design — self-managed is architecturally correct for this system |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4=4 (sync is correct for data-gateway archetype); no data processing workloads detected |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=2 (partial IaC), INF-Q11=2 (no deployment automation), OPS-Q5=1 (no deployment strategy), OPS-Q6=2 (limited integration testing in CI) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Alluxio is a distributed monolith with a Master/Worker topology. The system is a single logical application deployed as tightly coupled Master and Worker processes that share code via a monorepo. While it has modular code structure (core/common, core/transport, underfs plugins), the deployment units are not independently deployable microservices — Master and Worker share heavy interdependencies.

**Compute Model:** The system has Helm charts and Kubernetes operator for containerized deployment (scoring INF-Q1=3), but the architecture itself remains a distributed monolith rather than cloud-native microservices.

**Recommended Decomposition Approach:** Given the system's nature as a storage caching layer, full microservices decomposition may not be appropriate. Instead, a Conditional/Adaptive approach is recommended:
1. Continue operating as a distributed system on EKS (preference: `eks`)
2. Extract the S3-compatible proxy into an independent service behind API Gateway
3. Extract the table/catalog service as an independent service
4. Consider serverless functions for auxiliary operations (health aggregation, metrics collection)

**Representative AWS Services:** EKS, API Gateway, EventBridge, Step Functions
**Recommended Patterns:** Strangler Fig (for proxy extraction), Anti-corruption Layer, Hexagonal Architecture

**Learning Resources:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=2):** Helm charts and Kubernetes manifests cover the container orchestration layer, but no Terraform, CloudFormation, or CDK exists for underlying cloud infrastructure (VPC, IAM, S3, networking). The Vagrant/Ansible integration is legacy and not production-grade IaC.

**Current CI/CD State (INF-Q11=2):** GitHub Actions provides unit test and integration test automation, but there is no deployment automation — no deploy stages, no artifact publishing to container registries as part of CI, no infrastructure pipeline.

**Deployment Strategy Gaps (OPS-Q5=1):** No canary, blue-green, or rolling deployment strategy configured. The Helm chart logserver uses `Recreate` strategy. No ArgoCD, Flux, or other GitOps tooling.

**Testing Gaps (OPS-Q6=2):** Integration tests exist in GitHub Actions (`java8_integration_tests.yml`) but are focused on functional correctness rather than deployment validation. No contract tests or end-to-end deployment verification.

**Recommended DevOps Toolchain:**
- **IaC:** Terraform or CDK for cloud infrastructure (VPC, IAM, S3 buckets, EKS cluster)
- **GitOps:** ArgoCD for Kubernetes deployment automation on EKS
- **CI/CD:** Extend GitHub Actions with build → push → deploy stages; add container image scanning
- **Deployment:** Implement canary deployments via ArgoCD Rollouts on EKS

**Representative AWS Services:** CodeBuild, CodePipeline, ECR, EKS, CloudFormation/CDK, X-Ray, CloudWatch
**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

*(Included because APP-Q2 = 2)*

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | APP-Q2=2 — identifiable modules (S3 proxy, table catalog, WebUI) can be extracted incrementally. | Medium to High | ✅ **Recommended for extracting the S3 proxy and table catalog services.** |
| **Conditional / Adaptive** | Team has limited capacity; the core Master/Worker topology may not need decomposition — it's architecturally sound as a distributed system. | Low to Medium | ✅ **Recommended overall approach.** Containerize on EKS first, then selectively extract high-value services. |
| **Big-Bang Rewrite** | Not appropriate — the system is functional and has clear internal modularity. | Very High | ⚠️ **Recommended against.** The distributed monolith architecture is appropriate for a storage system. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate extracted services from the internal gRPC transport layer | When extracting S3 proxy or table catalog |
| **Hexagonal Architecture** | Structure each extracted service with clear ports and adapters | Each new independently deployed service |

### Effort Estimation

| Factor | Signal | Assessment |
|--------|--------|-----------|
| Module boundaries | Clear package structure (core/, underfs/, table/, proxy/) | Low effort — boundaries exist |
| Data coupling | Embedded RocksDB per-process — no shared external database | Low effort — no DB to split |
| Stored procedures | None (DATA-Q4=4) | No blocker |
| Communication patterns | gRPC is the internal protocol — well-defined service interfaces already exist via .proto files | Medium effort — proto interfaces can become service contracts |
| CI/CD maturity | Partial (INF-Q11=2) — pipeline exists for testing but not deployment | Medium effort — deployment pipeline needed |
| Test coverage | 906 test files, integration tests in CI | Low effort — good test foundation |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Alluxio provides comprehensive Kubernetes deployment support via Helm charts (v0.6.54) and a dedicated Kubernetes Operator with CRDs (Dataset, Runtime). The Helm chart deploys Master as StatefulSet, Worker as DaemonSet, Proxy as DaemonSet, and includes a CSI driver. The Dockerfile uses multi-stage builds targeting Rocky Linux 8. However, the system also supports bare-metal deployment via shell scripts (`bin/alluxio-start.sh`) and Vagrant/Ansible for VM provisioning. |
| **Gap** | While Kubernetes deployment is well-supported, the Helm chart does not target any specific managed Kubernetes service (EKS, ECS). No Fargate or serverless compute options. The Vagrant/Ansible path targets raw VMs. |
| **Recommendation** | Standardize on EKS (per preferences) as the primary deployment target. Add EKS-specific configurations (IAM roles for service accounts, EBS CSI driver integration, ALB ingress controller). Deprecate Vagrant/VM deployment path. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/Chart.yaml`, `integration/kubernetes/operator/alluxio/Dockerfile`, `integration/docker/Dockerfile`, `integration/vagrant/Vagrantfile` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Alluxio uses embedded RocksDB as its metadata store, running within the Master process. This is self-managed — no external managed database service is used. RocksDB configuration is managed via `.ini.template` files (`conf/rocks-block.ini.template`, `conf/rocks-inode.ini.template`). The system also supports ZooKeeper for leader election (can be self-managed or use Amazon MSK-compatible ZooKeeper). |
| **Gap** | All persistent state (metadata in RocksDB, journal entries) is self-managed within the application process. No managed database service (Aurora, DynamoDB) is used. However, embedded RocksDB is an architecturally deliberate choice for a storage caching system — latency-sensitive metadata lookups benefit from local storage. |
| **Recommendation** | For the metadata tier, evaluate whether the journal/Raft consensus could leverage Aurora or DynamoDB (per preferences) for cross-region durability. For ZooKeeper leader election, migrate to Amazon MSK-compatible ZooKeeper or replace with a managed alternative. The embedded RocksDB for hot metadata may remain appropriate for latency requirements. |
| **Evidence** | `core/server/master/src/main/java/alluxio/master/metastore/rocks/RocksStore.java`, `conf/rocks-block.ini.template`, `conf/rocks-inode.ini.template` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `data-gateway`. Workflow orchestration is not applicable by design — the system serves read-heavy data access requests with no multi-step business workflows to orchestrate. The internal Raft consensus and journal replication are infrastructure-level concerns, not business workflows. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `data-gateway` where synchronous gRPC is the correct communication pattern. All client-to-master, client-to-worker, and master-to-worker communication uses synchronous gRPC (27 proto files defining service contracts). This is architecturally appropriate — data access operations require synchronous request/response for file reads, metadata lookups, and block operations. No messaging or streaming infrastructure is needed for the primary data path. |
| **Gap** | None — synchronous gRPC is the correct design for a distributed storage caching layer. |
| **Recommendation** | Adopting async messaging is NOT recommended for the primary data path — it would add latency and operational complexity without architectural benefit. If auxiliary flows (metrics aggregation, audit events) are added in the future, EventBridge (per preferences) would be appropriate for those specific use cases only. |
| **Evidence** | `core/transport/src/main/proto/grpc/file_system_master.proto`, `core/transport/src/main/proto/grpc/block_worker.proto`, `core/transport/src/main/proto/grpc/block_master.proto` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation is defined in any IaC. The Helm chart does not include NetworkPolicy resources. The Kubernetes operator does not define network isolation between Master and Worker pods. No VPC endpoints, PrivateLink, or VPC Lattice configurations exist. The OTEL collector config uses `insecure: true` for Jaeger communication. |
| **Gap** | Complete absence of network security infrastructure in IaC. Services deployed via the Helm chart have no network isolation — any pod in the cluster can reach Master and Worker gRPC ports. No TLS configured between components. |
| **Recommendation** | Add Kubernetes NetworkPolicy resources to the Helm chart restricting ingress/egress between Master, Worker, Proxy, and client pods. Deploy in private subnets on EKS with VPC endpoints for S3/DynamoDB access. Enable gRPC TLS between all components. Add VPC Lattice for service-to-service networking. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/templates/` (no NetworkPolicy files), `integration/metrics/otel-collector-config.yaml` (insecure: true) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Helm chart deploys a Kubernetes Service for Master and Worker, providing internal load balancing within the cluster. The S3-compatible REST proxy is exposed as a separate service. However, there is no API Gateway, ALB Ingress, or CloudFront distribution configured as the entry point. No throttling, authentication at the gateway level, or request validation exists at the infrastructure level. |
| **Gap** | No managed API entry point (API Gateway, ALB with auth) for the REST APIs. The S3-compatible proxy is directly exposed without gateway-level protection. |
| **Recommendation** | Add API Gateway (per preferences) in front of the S3-compatible REST proxy for throttling, request validation, and authentication. Configure ALB Ingress Controller on EKS for the WebUI and admin REST APIs. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/templates/proxy/daemonset.yaml`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling is configured. The Helm chart deploys Master as a StatefulSet with a fixed replica count and Worker as a DaemonSet (one per node). No HorizontalPodAutoscaler (HPA), Vertical Pod Autoscaler (VPA), or Cluster Autoscaler configurations exist. No KEDA or custom metrics-based scaling. |
| **Gap** | All capacity is statically provisioned. Worker count is fixed to the number of nodes. Master count is fixed. No scaling based on cache pressure, request rate, or storage utilization. |
| **Recommendation** | Implement HPA for the Proxy DaemonSet based on request rate. Configure Cluster Autoscaler or Karpenter on EKS to add/remove Worker nodes based on cache utilization metrics. Consider KEDA with custom CloudWatch metrics for scaling based on cache hit ratio or storage pressure. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (fixed counts), no HPA YAML files found |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. The Master's RocksDB metadata and Raft journal are stored on PersistentVolumeClaims but have no scheduled backup mechanism. No CronJob for snapshots, no AWS Backup plan, no S3 replication for journal data. The journal supports UFS (under filesystem) mode where journal entries can be written to S3, but no automated backup/restore procedure is documented in the deployment configs. |
| **Gap** | No automated backup for metadata (RocksDB) or journal data. No PITR capability. No documented restore procedure. Loss of the Master PVC means loss of all filesystem metadata. |
| **Recommendation** | Implement automated EBS snapshot lifecycle policies for Master PVCs. Configure the UFS journal to write to S3 with versioning enabled. Add a CronJob that performs Alluxio journal checkpoints and uploads to S3 with lifecycle policies. Document and test restore procedures. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (PVC definitions, no backup CronJob), `conf/` (no backup configs) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Helm chart supports multi-master HA via Raft consensus (configurable `master.count`). The system supports leader election via embedded Raft journal or ZooKeeper. However, no multi-AZ configuration is explicit in the Helm chart — no pod anti-affinity rules, no topology spread constraints, no explicit AZ distribution. Worker DaemonSet runs on all nodes but without AZ-awareness for data placement. |
| **Gap** | Multi-master HA is supported but not deployed multi-AZ by default. No pod anti-affinity or topology spread constraints ensure Masters are in different AZs. Worker data placement has no AZ-awareness for fault isolation. |
| **Recommendation** | Add `topologySpreadConstraints` to the Master StatefulSet requiring spread across AZs. Add pod anti-affinity rules. Configure Workers with AZ-aware data placement policies. Ensure PVCs use a StorageClass with `volumeBindingMode: WaitForFirstConsumer` for AZ-correct binding. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (master.count configurable, no topology constraints) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Kubernetes deployment is defined in Helm charts and operator CRDs — covering the container orchestration layer. However, no Terraform, CloudFormation, or CDK exists for the underlying cloud infrastructure (VPC, IAM roles, S3 buckets for UFS, EKS cluster itself, networking, monitoring). The Vagrant/Ansible integration covers VM provisioning but is legacy and not production-grade. |
| **Gap** | Partial IaC — Kubernetes resources are in Helm/operator, but 0% of cloud infrastructure (networking, IAM, storage, monitoring, EKS cluster) is defined in IaC. Infrastructure provisioning is presumably manual. |
| **Recommendation** | Create Terraform or CDK (per preference context) modules for: EKS cluster, VPC with private subnets, IAM roles for IRSA, S3 buckets for UFS storage, CloudWatch alarms, and Route 53 health checks. Target 90%+ IaC coverage. |
| **Evidence** | `integration/kubernetes/helm-chart/` (Helm IaC exists), no `.tf`, `.cfn.yaml`, or `cdk.json` files anywhere in repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides CI automation with 8 workflows: unit tests (Java 8), integration tests, fault tolerance tests, WebUI tests, FUSE tests, and checkstyle. Jenkins Dockerfiles exist for JDK 8/11/17 build environments. However, there is no CD — no deployment automation, no artifact publishing to ECR, no infrastructure pipeline, no automated release process. Deployments are manual. |
| **Gap** | Build and test are automated but deployment is entirely manual. No CD pipeline exists for promoting artifacts through environments. No infrastructure changes are automated. |
| **Recommendation** | Extend GitHub Actions with: container image build and push to ECR, Helm chart packaging and publishing, deployment to staging EKS cluster via ArgoCD, integration test against deployed environment, production promotion gate. Add a separate IaC pipeline for Terraform/CDK changes. |
| **Evidence** | `.github/workflows/java8_unit_tests.yml`, `.github/workflows/java8_integration_tests.yml`, `.github/workflows/checkstyle.yml`, `dev/jenkins/` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Primary language is Java 8 (source and target in `pom.xml`: `<java.version>1.8</java.version>`). AWS SDK has mixed v1 (1.11.815) and v2 (2.16.104). Framework stack: Jersey 2.34 (pre-Jakarta), Jetty 9.4.46 (EOL), gRPC 1.54.1. Secondary: Go 1.18 (EOL) for K8s operator, Node.js 10.11.0 (EOL) for WebUI with React 16.8. All three language version AND framework AND SDK are regressed — Java 8 + Jersey 2.x + AWS SDK v1. |
| **Gap** | Compound legacy signals: Java 8 (extended support only), Jetty 9 (EOL), Jersey 2.x (pre-Jakarta EE), AWS SDK v1 still in use, PowerMock (deprecated, blocks JUnit 5). Go and Node.js are also EOL versions. |
| **Recommendation** | Migrate to Java 17+ with Spring Boot 3.x or Jakarta EE 10 compatible Jersey 3.x. Complete AWS SDK v1 to v2 migration. Upgrade Go operator to Go 1.22+. Upgrade WebUI to Node.js 20+ with React 18. |
| **Evidence** | `pom.xml` (java.version=1.8, aws-sdk-v1=1.11.815, aws-sdk-v2=2.16.104, jetty=9.4.46), `integration/kubernetes/operator/alluxio/go.mod` (go 1.18), `webui/package.json` (node 10.11.0) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Alluxio is a distributed monolith — a single logical system deployed as Master and Worker processes from the same codebase. The module structure is identifiable: core/common, core/transport, core/server/master, core/server/worker, core/server/proxy, table/*, underfs/* (15 storage plugins). However, all modules compile into shared assemblies (`assembly/server`), share the same dependency tree, and are versioned together. The S3 proxy, table catalog, and WebUI are logically separable but deployed within the same artifact. |
| **Gap** | Monolith with identifiable modules but shared build artifacts and tight compile-time dependencies between modules. The Master and Worker cannot be independently versioned or deployed from different release trains. The S3 proxy and table catalog could be independent services. |
| **Recommendation** | Adopt a Conditional/Adaptive approach: keep the core Master/Worker topology as-is (it's architecturally sound for a distributed cache), but extract the S3-compatible proxy and table catalog as independently deployable services. Use gRPC proto files as service contracts for the extracted services. |
| **Evidence** | `pom.xml` (single version for all modules), `assembly/server/` (unified packaging), `core/server/proxy/` (separable S3 proxy), `table/` (separable catalog) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `data-gateway`. Synchronous gRPC request/response is the correct communication pattern for a storage caching layer. All read operations (file reads, block reads, metadata lookups) are inherently synchronous. The 27 proto files define synchronous unary and streaming RPCs. Async messaging is not needed for the primary data access path. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `data-gateway`. No user-facing operations exceed 30 seconds in the normal read path. Heavy operations like data migration and replication are handled by the internal Job framework (job/ module) which provides asynchronous job execution with status tracking. The data-gateway's primary surface (file reads, metadata lookups) operates within normal RPC timeout bounds. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | REST APIs use `/api/v1` URL path versioning (defined in `Constants.java`: `REST_API_PREFIX = "/api/v1"`). gRPC service versions are tracked via constants (e.g., `FILE_SYSTEM_MASTER_CLIENT_SERVICE_VERSION = 2`). However, there is only one version (`v1`) with no migration path to v2, no backward compatibility guarantees documented, and the gRPC versioning is informal (integer constants, not proto package versioning). |
| **Gap** | Versioning exists in a basic form (/api/v1 paths, integer service versions) but is applied ad-hoc. No formal versioning policy, no backward compatibility guarantee, no deprecation process. The gRPC services use integer version constants rather than proper proto package versioning (e.g., `alluxio.grpc.v1` vs `alluxio.grpc.v2`). |
| **Recommendation** | Adopt proper proto package versioning for gRPC services. Document a versioning policy with backward compatibility guarantees. Plan for `/api/v2` REST endpoints alongside v1 when breaking changes are needed. |
| **Evidence** | `core/common/src/main/java/alluxio/Constants.java` (REST_API_PREFIX="/api/v1", service version constants), `core/server/proxy/pom.xml` (basePath=/api/v1) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Kubernetes Services provide DNS-based service discovery for Master and Worker endpoints when deployed on K8s. The Helm chart creates headless services for StatefulSet (Master) and ClusterIP services for Worker. ZooKeeper-based leader election provides Master discovery in HA mode. In non-K8s deployments, `conf/masters` and `conf/workers` files provide static host lists. |
| **Gap** | Partial service discovery — Kubernetes DNS handles K8s deployments well, but non-K8s deployments rely on static host configuration files. No dynamic service registry for VM/bare-metal deployments. |
| **Recommendation** | For EKS deployments, the current Kubernetes DNS approach is appropriate. Consider adding AWS Cloud Map for cross-cluster discovery if multi-cluster EKS is needed. Deprecate the static `conf/masters` and `conf/workers` file approach in favor of dynamic discovery. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/templates/` (Service YAML), `conf/masters`, `conf/workers` |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Alluxio is itself a virtual filesystem that abstracts access to underlying storage including S3. The `underfs/s3a` module provides S3 integration via AWS SDK. However, within the Alluxio system itself, unstructured data (logs, journal snapshots) is stored on local filesystems or PersistentVolumes — not in managed object storage. No parsing pipeline (Textract, Tika) is configured for any data flowing through the system. |
| **Gap** | Operational data (logs, journal snapshots, metrics data) stored on local/PVC storage rather than S3. No automated parsing or extraction pipeline for operational data. The system itself provides S3 access to clients but does not use S3 for its own operational data. |
| **Recommendation** | Configure journal snapshots and operational logs to be stored in S3 with lifecycle policies. Use S3 File Gateway or direct S3 integration for log aggregation. This enables search, analytics, and long-term retention of operational data. |
| **Evidence** | `underfs/s3a/` (S3 integration exists for client data), `integration/kubernetes/helm-chart/alluxio/values.yaml` (PVC for journal/logs) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Alluxio has a well-structured data access layer. The `underfs/` module provides a unified `UnderFileSystem` interface with 15 storage backend implementations (S3, HDFS, GCS, ABFS, etc.). The `core/client/` module provides unified client APIs (FileSystem interface). The Master's metastore has a clear `MetaStore` interface with RocksDB implementation. This is mostly centralized with clean interfaces. |
| **Gap** | The unified access pattern is well-implemented for the storage backends. Minor gap: some test utilities and integration code access storage directly rather than through the unified interface. |
| **Recommendation** | Maintain the current clean interface pattern. No significant action needed — the `UnderFileSystem` interface is a well-designed data access layer. |
| **Evidence** | `underfs/` (15 storage backends with unified interface), `core/client/fs/` (unified client API), `core/server/master/src/main/java/alluxio/master/metastore/` (MetaStore interface) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | RocksDB is used as the embedded metadata store. The version is managed through Maven dependency management in the root POM but is not explicitly pinned to a specific RocksDB release version in the visible configuration. The RocksDB `.ini.template` files configure tuning parameters but do not specify the engine version. ZooKeeper version dependency is similarly managed through Maven but without explicit EOL tracking. |
| **Gap** | Database engine versions are managed implicitly through Maven dependency resolution rather than explicitly pinned and documented. No EOL tracking or version-update procedure documented for RocksDB or ZooKeeper dependencies. |
| **Recommendation** | Explicitly pin RocksDB and ZooKeeper versions in the POM with comments noting EOL dates. Document a version-update procedure covering testing requirements and rollback approach for embedded database upgrades. |
| **Evidence** | `pom.xml` (dependency management), `conf/rocks-block.ini.template` (tuning only, no version), `conf/rocks-inode.ini.template` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. All business logic resides in the Java application layer. The system uses RocksDB (key-value store) and Protocol Buffers for data serialization — no SQL database is involved. Data access is entirely through the application-layer MetaStore interface. |
| **Gap** | None — no stored procedures or proprietary SQL. |
| **Recommendation** | None needed. The current approach of keeping all logic in the application layer is appropriate. |
| **Evidence** | No `.sql` files with stored procedures found. `core/server/master/src/main/java/alluxio/master/metastore/` (all access through Java interfaces) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging infrastructure is configured in any IaC or deployment configuration. The application has Log4j-based application logging and the OTEL collector sends traces to Jaeger, but there is no immutable audit trail for security events, access patterns, or administrative actions. No `aws_cloudtrail` resource exists. |
| **Gap** | No audit logging infrastructure. No immutable log storage. No ability to perform forensic analysis after security incidents. |
| **Recommendation** | Enable CloudTrail for all AWS API calls. Configure S3 bucket with Object Lock for immutable audit log storage. Add application-level audit logging for filesystem operations (who accessed what, when) and ship to CloudWatch Logs with retention policies. |
| **Evidence** | No `aws_cloudtrail` or audit logging configuration found in any file. `integration/metrics/otel-collector-config.yaml` (traces only, not audit) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration exists for any data store. RocksDB metadata is stored unencrypted on PersistentVolumes. Journal data is unencrypted. No KMS key references in any IaC or configuration. The Helm chart PVC definitions do not specify encrypted StorageClasses. |
| **Gap** | All data at rest (metadata, journal, cached data) is unencrypted. No KMS integration. No encrypted storage class configured. |
| **Recommendation** | Configure EBS-backed StorageClasses with encryption enabled (AWS-managed or customer-managed KMS keys). Enable encryption for S3 buckets used as UFS storage. Add KMS key management via Terraform/CDK for centralized key governance. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (PVC definitions without encryption), no `kms_key_id` references anywhere |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Alluxio implements custom SASL-based authentication for gRPC channels. The S3 proxy validates AWS V2/V4 signatures for S3-compatible API requests. However, this is not OAuth2/JWT — it's a custom authentication framework (SIMPLE, CUSTOM, NOSASL modes). The REST admin APIs (Master/Worker REST handlers) do not appear to have authentication middleware. The WebUI endpoints are unauthenticated. |
| **Gap** | Custom SASL authentication exists but is not token-based (no OAuth2/JWT). Admin REST APIs and WebUI lack authentication. Authentication type defaults to "SIMPLE" which provides no security guarantees. No integration with modern identity standards. |
| **Recommendation** | Add OAuth2/JWT authentication for REST APIs via API Gateway authorizers. Integrate with Cognito or corporate OIDC provider for admin access. Maintain S3 signature validation for the S3 proxy. Upgrade SASL to use Kerberos or mutual TLS for internal gRPC communication. |
| **Evidence** | `core/common/src/main/java/alluxio/security/authentication/AuthType.java` (SIMPLE/CUSTOM/NOSASL), `core/server/proxy/src/main/java/alluxio/proxy/s3/signature/` (S3 signature validation) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Alluxio manages its own authentication entirely. The `AlluxioLoginModule` provides a custom JAAS login module. User identity is derived from OS-level user credentials or the SIMPLE auth mechanism. No integration with Cognito, Okta, LDAP, or any external identity provider for user authentication. No SSO, no OIDC, no SAML federation. |
| **Gap** | Completely standalone authentication with no external IdP integration. User management is local to the system with no centralized identity governance. |
| **Recommendation** | Integrate with a centralized IdP (Cognito per AWS preferences) for admin and API access. Implement OIDC federation for user authentication. Enable SSO for the WebUI. For internal service-to-service auth, use IAM roles for service accounts (IRSA) on EKS. |
| **Evidence** | `core/common/src/main/java/alluxio/security/login/AlluxioLoginModule.java`, `core/common/src/main/java/alluxio/security/authentication/` (custom auth framework, no OIDC/SAML) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No Secrets Manager or Vault integration exists. The Helm chart has a commented-out secrets mount mechanism but it's not configured. AWS credentials are read from environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`). The Vagrant init script (`integration/vagrant/bin/init_aws.py`) writes AWS credentials to `~/.boto` in plaintext. Configuration templates reference credential properties that would be set via environment variables at runtime. No plaintext credentials in committed source code (aside from the Vagrant example pattern). |
| **Gap** | No secrets management system in use. Production credentials would be in environment variables without rotation. The Vagrant script pattern of writing credentials to files is insecure but limited to development. |
| **Recommendation** | Integrate AWS Secrets Manager for all credentials (S3 access keys, ZooKeeper auth, TLS certificates). Use IRSA (IAM Roles for Service Accounts) on EKS to eliminate static AWS credentials entirely. Configure automated rotation for any remaining secrets. Remove the plaintext credential writing in Vagrant scripts. |
| **Evidence** | `integration/vagrant/bin/init_aws.py` (writes credentials to ~/.boto), `integration/kubernetes/helm-chart/alluxio/values.yaml` (commented-out secrets section), no `aws_secretsmanager` references |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No patching strategy or vulnerability scanning is configured. The production Dockerfile uses Rocky Linux 8 base (Java 8 path) or CentOS 7 (Java 11 path — EOL). Custom libfuse is compiled from source adding unvetted binary surface. No SSM Patch Manager, no AWS Inspector, no Snyk, no container image scanning. Jenkins build images use fixed JDK versions without update automation. The Go CSI driver uses Go 1.18 (EOL). |
| **Gap** | No patching automation. CentOS 7 base image is EOL. Custom-compiled binaries. No vulnerability scanning. No hardened base images (no CIS benchmarks, no Bottlerocket). |
| **Recommendation** | Replace base images with Amazon Linux 2023 or Bottlerocket for EKS nodes. Enable ECR image scanning for all container images. Integrate Snyk or Trivy into CI/CD pipeline. Upgrade Go to 1.22+ and Node.js to 20+. Remove CentOS 7 path entirely. Use multi-stage builds with distroless final images where possible. |
| **Evidence** | `integration/docker/Dockerfile` (Rocky Linux 8, CentOS 7, custom libfuse compilation), `dev/jenkins/Dockerfile-jdk8` (fixed base), no vulnerability scanning configs |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are configured. No Dependabot, no Snyk, no SonarQube, no CodeQL, no `npm audit`, no SAST tools in CI/CD. The GitHub Actions workflows run unit tests and checkstyle only — no security gates. No container image scanning. No dependency vulnerability scanning despite having 71 Maven POMs with hundreds of transitive dependencies. |
| **Gap** | Complete absence of security scanning. No dependency vulnerability detection. No SAST. No container scanning. No security gates in the pipeline. |
| **Recommendation** | Add Dependabot for Maven, Go, and npm dependency vulnerability scanning. Integrate CodeQL or SonarQube for SAST in GitHub Actions. Add ECR image scanning for container images. Add `mvn dependency-check:check` (OWASP dependency-check) to the build pipeline. Configure security gates that block merges on critical/high findings. |
| **Evidence** | `.github/workflows/` (no security scanning steps), no `.github/dependabot.yml`, no `.snyk` file, no SonarQube config |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | OpenTelemetry infrastructure exists: OTEL collector config (`integration/metrics/otel-collector-config.yaml`) receives OTLP traces and exports to Jaeger. OTEL agent configs exist for Master and Worker. However, the Java application source code does not import OpenTelemetry SDK — no `io.opentelemetry` imports found. The tracing appears to be JVM-agent-based (auto-instrumentation) rather than manual instrumentation with trace ID propagation across service boundaries. gRPC context propagation exists (`io.grpc.Context`) but for application state, not distributed tracing. |
| **Gap** | Tracing infrastructure (collector, agents) exists but application-level instrumentation with cross-service trace propagation is not implemented in source code. Auto-instrumentation may provide partial coverage but lacks custom spans for business operations. |
| **Recommendation** | Add OpenTelemetry SDK instrumentation to the Java source code with custom spans for key operations (file read, block allocation, metadata lookup). Ensure trace context propagation across Master-Worker gRPC calls. Replace Jaeger with AWS X-Ray or continue with OTEL but export to X-Ray via the ADOT collector. |
| **Evidence** | `integration/metrics/otel-collector-config.yaml` (OTEL infrastructure), `integration/metrics/otel-agent-config.yaml`, no `io.opentelemetry` imports in Java source |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO/SLI definitions found anywhere in the repository. No error budget tracking. No CloudWatch alarm definitions for latency percentiles. The monitoring Helm chart deploys Prometheus with 72h retention and Grafana but without SLO-based dashboards or alerting rules. No formal definition of acceptable service levels for cache hit ratio, metadata operation latency, or data read throughput. |
| **Gap** | No SLOs defined. No formal service level objectives for any user-facing operation. No error budgets. Cannot measure whether the system is meeting user expectations. |
| **Recommendation** | Define SLOs for critical operations: cache hit ratio (target: >95%), metadata operation p99 latency (<10ms), data read throughput (>1GB/s per worker). Implement SLO monitoring with CloudWatch composite alarms and error budget tracking. |
| **Evidence** | No SLO definition files found. `integration/kubernetes/helm-chart/monitor/values.yaml` (Prometheus + Grafana without SLO rules) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The system has extensive internal metrics (Prometheus metrics endpoint, OTEL metrics pipeline) but these are infrastructure metrics: JVM stats, RPC counts, cache sizes. The `conf/metrics.properties.template` configures metric sinks (CSV, Graphite, Prometheus) but all configured metrics are operational/infrastructure. No business outcome metrics (data access patterns, cache efficiency trends, storage cost optimization, user workload characteristics) are published. |
| **Gap** | Only infrastructure metrics exist. No business-level metrics that would inform modernization decisions (which storage backends are most used, cache hit patterns by workload type, cost-per-read by storage tier). |
| **Recommendation** | Add custom CloudWatch metrics for business outcomes: cache hit ratio by workload, data locality metrics, storage tier usage distribution, cost-per-operation estimates. Create dashboards combining infrastructure and business metrics. |
| **Evidence** | `conf/metrics.properties.template` (infrastructure metric sinks only), `integration/metrics/` (OTEL/Prometheus for infrastructure) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting rules configured. The Prometheus deployment in the monitoring Helm chart has no alert rules. No CloudWatch alarms defined. No PagerDuty/OpsGenie integration. No anomaly detection. The OTEL collector exports metrics to Prometheus but no alert manager or alerting rules consume them. |
| **Gap** | No alerting whatsoever — neither static thresholds nor anomaly detection. Failures would go undetected until users report problems. |
| **Recommendation** | Configure Prometheus AlertManager with rules for: Master unreachable, Worker disconnected, cache eviction spike, RPC error rate > threshold, journal lag > threshold. Enable CloudWatch anomaly detection for key metrics. Integrate with PagerDuty or OpsGenie for on-call routing. |
| **Evidence** | `integration/kubernetes/helm-chart/monitor/` (no alerting rules), no CloudWatch alarm definitions |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy configured beyond basic Kubernetes defaults. The logserver uses `Recreate` strategy. No canary, blue/green, or progressive delivery. No ArgoCD, Flux, or Argo Rollouts. No traffic shifting or feature flags. The GitHub Actions CI/CD has no deploy stage. Helm chart upgrades would be manual `helm upgrade` with no staged rollout. |
| **Gap** | Direct-to-production deployment with no staged rollout. No automated deployment at all — manual Helm upgrades only. No rollback automation. |
| **Recommendation** | Implement ArgoCD for GitOps-based deployment on EKS. Configure Argo Rollouts for canary deployments of the Alluxio Proxy (stateless, easy to canary). For Master/Worker (stateful), use rolling updates with readiness gates and automated rollback on health check failure. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (no deployment strategy config), `.github/workflows/` (no deploy stages) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Integration tests exist and run in GitHub Actions (`java8_integration_tests.yml`, `java8_integration_tests_ft.yml`, `fuse_integration_tests.yml`). These test functional correctness of Master/Worker interactions, fault tolerance, and FUSE integration. However, they run in a minicluster environment rather than against a real deployment. No deployment-level integration tests (smoke tests against deployed K8s, API contract tests, load tests). |
| **Gap** | Integration tests exist for functional correctness but not for deployment validation. No tests verify that a Helm chart upgrade succeeds without data loss. No API contract tests. No performance regression tests in CI. |
| **Recommendation** | Add deployment-level integration tests: Helm chart install/upgrade smoke tests, API contract tests against deployed proxy, performance baseline tests to catch regressions. Run these in a staging EKS cluster as part of the CD pipeline. |
| **Evidence** | `.github/workflows/java8_integration_tests.yml`, `.github/workflows/fuse_integration_tests.yml`, `minicluster/` (in-process test cluster) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found. No Systems Manager Automation documents. No Lambda-based remediation. No self-healing patterns. No incident response documentation in the repository. The system has health checks (liveness/readiness probes in Helm) but no automated remediation beyond Kubernetes restarting failed pods. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failures (Master failover, Worker data loss, journal corruption, storage backend unavailable). No automated remediation. |
| **Recommendation** | Create machine-readable runbooks for: Master failover procedure, Worker recovery, journal checkpoint and restore, cache invalidation, storage backend failover. Implement SSM Automation documents for common recovery actions. Add Step Functions workflows for complex incident response scenarios. |
| **Evidence** | No runbook files found. No SSM Automation documents. `integration/kubernetes/helm-chart/alluxio/values.yaml` (liveness/readiness probes only) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file referencing monitoring configs. No team attribution on alarms or dashboards. No per-service dashboards with named owners. The monitoring Helm chart deploys generic Prometheus/Grafana without any organizational structure. No SLO definitions with team attribution. |
| **Gap** | No observability ownership. Monitoring is undifferentiated — no team owns specific metrics, alarms, or dashboards. No on-call mapping. |
| **Recommendation** | Define observability ownership: assign Master metrics/alarms to a metadata team, Worker metrics to a caching team, Proxy metrics to an API team. Create per-component dashboards with named owners. Add CODEOWNERS for monitoring configuration files. |
| **Evidence** | No CODEOWNERS file, no team tags on monitoring resources, `integration/kubernetes/helm-chart/monitor/` (generic setup) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging governance. The Helm chart values.yaml has empty defaults for all annotation and label sections (`nodeSelector: {}`, `podAnnotations: {}`). No standard tags for cost allocation, environment, ownership, or team. No tag enforcement policies. No `default_tags` in any IaC (no Terraform exists). |
| **Gap** | No tags or labels for cost allocation, ownership, or environment identification. Cannot track costs per workload or identify resource ownership during incidents. |
| **Recommendation** | Define a tagging standard: `environment`, `team`, `service`, `cost-center`, `data-classification`. Apply default labels in the Helm chart. When Terraform/CDK is added, use `default_tags` provider configuration. Enforce via AWS Tag Policies in Organizations. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (empty nodeSelector, podAnnotations) |

---

## Learning Materials

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | APP-Q1, DATA-Q3, INF-Q2 | Java 8 target, dependency versions, Maven multi-module |
| `integration/kubernetes/helm-chart/alluxio/Chart.yaml` | INF-Q1 | Helm chart for K8s deployment |
| `integration/kubernetes/helm-chart/alluxio/values.yaml` | INF-Q1, INF-Q7, INF-Q8, INF-Q9, OPS-Q5, OPS-Q9, SEC-Q2, SEC-Q5 | Deployment configuration, scaling, security |
| `integration/docker/Dockerfile` | INF-Q1, APP-Q1, SEC-Q6 | Production container image build |
| `integration/kubernetes/operator/alluxio/Dockerfile` | INF-Q1 | K8s operator container |
| `integration/kubernetes/operator/alluxio/go.mod` | APP-Q1 | Go 1.18 (EOL) |
| `webui/package.json` | APP-Q1 | Node.js 10.11.0 (EOL) |
| `.github/workflows/java8_unit_tests.yml` | INF-Q11, OPS-Q6 | CI automation |
| `.github/workflows/java8_integration_tests.yml` | INF-Q11, OPS-Q6 | Integration tests |
| `.github/workflows/checkstyle.yml` | INF-Q11 | Code style enforcement |
| `core/transport/src/main/proto/` | INF-Q4, APP-Q3, APP-Q5 | 27 gRPC proto definitions |
| `core/common/src/main/java/alluxio/Constants.java` | APP-Q5 | REST_API_PREFIX, service versions |
| `core/common/src/main/java/alluxio/security/authentication/` | SEC-Q3, SEC-Q4 | Custom SASL auth framework |
| `core/common/src/main/java/alluxio/security/login/AlluxioLoginModule.java` | SEC-Q4 | Custom login module |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/signature/` | SEC-Q3 | S3 signature validation |
| `core/server/master/src/main/java/alluxio/master/metastore/rocks/` | INF-Q2, DATA-Q2 | RocksDB metadata store |
| `conf/alluxio-site.properties.template` | SEC-Q3 | Security config (defaults to SIMPLE) |
| `conf/rocks-block.ini.template` | INF-Q2, DATA-Q3 | RocksDB configuration |
| `integration/metrics/otel-collector-config.yaml` | OPS-Q1, INF-Q5 | OTEL tracing/metrics config |
| `integration/metrics/docker-compose-master.yaml` | OPS-Q1 | Metrics stack |
| `integration/kubernetes/helm-chart/monitor/values.yaml` | OPS-Q2, OPS-Q4 | Prometheus/Grafana monitoring |
| `integration/vagrant/bin/init_aws.py` | SEC-Q5 | Plaintext credential writing |
| `underfs/s3a/` | DATA-Q1, DATA-Q2 | S3 storage backend |
| `assembly/server/` | APP-Q2 | Unified packaging (monolith evidence) |
| `conf/masters`, `conf/workers` | APP-Q6 | Static host configuration |
| `minicluster/` | OPS-Q6 | In-process test cluster |
