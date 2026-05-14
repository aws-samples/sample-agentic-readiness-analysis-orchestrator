# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | alluxio |
| **Date** | 2026-04-30 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, storage, distributed |
| **Context** | Data orchestration / virtual distributed file system. JVM, distributed storage caching layer. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true |
| **Overall Score** | **2.31 / 4.0** |

**Archetype Justification**: Masters own persistent state (RocksDB/Heap inode tree, block metadata) and expose CRUD operations on files and blocks via gRPC services. Workers manage tiered block storage with read/write operations. The job service coordinates distributed tasks but is secondary to the primary CRUD data path. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.82 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.75 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.89 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.31 / 4.0** | **🟠 Needs Work** |

**Scoring Notes:**
- INF: (3+1+2+2+1+2+1+2+2+2+2) / 11 = 20/11 = 1.82
- APP: (2+3+2+3+3+2) / 6 = 15/6 = 2.50
- DATA: (4+4+3+4) / 4 = 15/4 = 3.75
- SEC: (2+1+2+1+2+1+2) / 7 = 11/7 = 1.57
- OPS: (3+1+3+1+1+3+1+2+2) / 9 = 17/9 = 1.89
- Overall: (1.82+2.50+3.75+1.57+1.89) / 5 = 11.53/5 = 2.31

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group definitions in IaC. No network segmentation is defined. | Services may be exposed without proper network isolation; blast radius of failures and security incidents is unbounded. |
| 2 | INF-Q7: Auto-Scaling | 1 | No auto-scaling configuration for any workload. All capacity is statically provisioned via Helm values. | Cannot respond to traffic spikes; leads to over-provisioning (cost) or under-provisioning (degraded performance). |
| 3 | SEC-Q4: Centralized Identity | 1 | Custom SIMPLE/CUSTOM authentication with no integration to a centralized identity provider. | Inconsistent access policies, increased attack surface, no SSO or federated identity. |
| 4 | SEC-Q6: Compute Hardening | 1 | Dockerfile uses CentOS 7 / RockyLinux 8 base images with no vulnerability scanning or managed patching. | Unpatched container images are high-value targets; no evidence of CVE remediation process. |
| 5 | SEC-Q2: Encryption at Rest | 1 | No KMS or encryption-at-rest configuration for cached block data, journal data, or metastore data. | Data at rest on worker tiered storage and master journals is unencrypted; compliance risk. |

---

## Quick Agent Wins

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists — extensive `docs/` directory with architecture guides, configuration reference, security docs, and operational procedures; comprehensive `README.md`. Satisfies the documentation prerequisite.
- **What it enables:** A RAG-based knowledge agent that indexes Alluxio's documentation corpus to answer developer and operator questions about configuration, deployment, troubleshooting, and architecture. Could significantly reduce onboarding time for new contributors and operators.
- **Additional steps:** Index the `docs/` directory content and README into a vector store. Generate embeddings for document chunks. Consider using Amazon Bedrock with an embedding model and OpenSearch Service as the vector store (aligned with preferences).
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2) — GitHub Actions workflows for unit tests, integration tests, and checkstyle checks.
- **What it enables:** An agent that triggers test runs, checks build status, and reports test results. Can monitor CI pipeline health and alert on recurring failures.
- **Additional steps:** Extend GitHub Actions with API-accessible status endpoints. Add deployment pipeline stages that the agent can trigger and monitor.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and tracing infrastructure exists (OPS-Q1 = 3) — OpenTelemetry collector and agent configurations, Jaeger trace export, Prometheus metrics pipeline.
- **What it enables:** An agent that queries Prometheus metrics, correlates Jaeger traces, and identifies performance anomalies or degraded cache hit rates. Can suggest root causes for latency spikes by correlating master/worker metrics.
- **Additional steps:** Deploy the OpenTelemetry stack in the production environment. Ensure trace propagation is enabled across master-worker gRPC calls. Index historical metrics for agent queries.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (≥ 3 threshold). Application has modular distributed architecture with clear component boundaries. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 (≥ 3 threshold) and container definitions exist (Dockerfile + Helm chart). Already containerized. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (≥ 3 threshold). No commercial database engines detected. Alluxio is Apache-licensed, uses open-source RocksDB. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (< 3). RocksDB embedded metastore is self-managed. DATA-Q3 = 3 (supporting). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: No streaming, ETL, data pipeline, or analytics artifacts found. Alluxio is a caching/storage layer, not an analytics processor. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 2 (< 3), INF-Q11 = 2 (< 3). Partial IaC (Helm only), no deployment pipeline. OPS-Q5 = 1 (< 3), OPS-Q6 = 3 (supporting). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context: "Data orchestration / virtual distributed file system" contains no AI-related signal terms. |

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:** Alluxio uses RocksDB (v7.0.3) as an embedded key-value store for its master metastore (inode tree, block metadata). The metastore runs inside the master JVM process, with data stored on local disk or PersistentVolumeClaim. Journal data is stored locally or on HDFS/S3 as an under-storage. This is a fully self-managed data tier with no managed database service involvement.

**Gaps Identified:**
- RocksDB embedded metastore requires manual management of compaction, memory tuning, and backup/recovery
- No automated failover at the database level — HA depends on the embedded Raft journal protocol
- Metastore scaling is limited by the single-master node's resources

**Recommended Migration Targets (respecting preferences):**
- **Amazon DynamoDB** (preferred): Evaluate DynamoDB as the metadata store backend. DynamoDB provides automatic scaling, built-in replication, and managed backup/recovery. Alluxio's metastore interface (`InodeStore`, `BlockMetaStore`) could be adapted to use DynamoDB as a backend.
- **Amazon Aurora** (preferred): For workloads requiring relational metadata queries, Aurora PostgreSQL or Aurora MySQL provides managed, multi-AZ database with automated failover and backups.

**Representative AWS Services:** DynamoDB, Aurora, RDS

**Migration Approach:**
1. Abstract the `InodeStore` and `BlockMetaStore` interfaces to support pluggable backends
2. Implement a DynamoDB or Aurora backend adapter
3. Migrate metadata from RocksDB to the managed service with a dual-write period for validation
4. Remove RocksDB dependency once migration is validated

**Learning Resources:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 2):** Helm chart covers Kubernetes deployment of Alluxio components (master StatefulSet, worker DaemonSet, proxy, FUSE, CSI). No Terraform, CloudFormation, or CDK for cloud infrastructure — VPCs, security groups, IAM roles, S3 buckets, and EKS clusters are not codified.
- **CI/CD (INF-Q11 = 2):** GitHub Actions workflows handle build validation (unit tests, integration tests, checkstyle, SpotBugs). No automated deployment pipeline exists — no stages for container image build/push, Helm chart deployment to staging/production, or automated rollback.
- **Deployment Strategy (OPS-Q5 = 1):** StatefulSet uses `Parallel` podManagementPolicy. Logserver uses `Recreate` strategy. No canary, blue/green, or rolling update with traffic shifting.

**Recommendations (respecting preferences):**
1. **Adopt Terraform or CDK for cloud infrastructure** — Define EKS cluster (preferred), VPC, security groups, IAM roles, and S3 buckets as IaC. This closes the INF-Q5 and INF-Q10 gaps simultaneously.
2. **Build a deployment pipeline** — Extend GitHub Actions (or adopt AWS CodePipeline + CodeBuild) to include: container image build → push to ECR → Helm chart deployment to staging → integration test gate → promotion to production.
3. **Implement canary or rolling deployment** — Use Argo Rollouts or Helm hooks with progressive delivery for master StatefulSet updates. Worker DaemonSet updates can use `maxUnavailable` rolling strategy.
4. **Add security scanning to the pipeline** — Integrate dependency scanning (Dependabot, Snyk, or `mvn dependency-check:check`) and container image scanning (ECR image scanning or Trivy) into the CI pipeline.

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, EKS (preferred), ECR, CloudFormation/CDK, X-Ray, CloudWatch

**Learning Resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Alluxio is containerized and deployed on Kubernetes via a Helm chart. The master runs as a StatefulSet, workers as a DaemonSet, and the proxy/FUSE/logserver as optional Deployments or DaemonSets. A multi-stage Dockerfile builds the container image on RockyLinux 8 (Java 8) or CentOS 7 (Java 11) with a Go-based CSI driver compiled from source. The Kubernetes operator (`integration/kubernetes/operator/`) provides additional orchestration. No raw EC2 or on-premises compute definitions exist in the repository. However, no managed AWS compute IaC (EKS, ECS, Lambda, Fargate) is defined — the Helm chart assumes an existing Kubernetes cluster. |
| **Gap** | The Kubernetes cluster itself is not defined as IaC. Whether it runs on EKS (managed) or self-managed Kubernetes is unknown from the repository. The preference to avoid self-managed-kubernetes is not demonstrably satisfied. |
| **Recommendation** | Define the EKS cluster (preferred) as Terraform or CDK IaC alongside the Helm chart. This ensures the compute platform is managed and reproducible. Consider Fargate for stateless proxy/FUSE workloads to further reduce operational overhead. |
| **Evidence** | `integration/docker/Dockerfile`, `integration/kubernetes/helm-chart/alluxio/`, `integration/kubernetes/operator/`, `integration/kubernetes/helm-chart/alluxio/templates/master/statefulset.yaml`, `integration/kubernetes/helm-chart/alluxio/templates/worker/daemonset.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Alluxio uses RocksDB (v7.0.3, `rocksdbjni` dependency in `pom.xml`) as an embedded key-value store for the master metastore. It runs inside the master JVM process with data persisted to local disk or PVC. An alternative heap-based metastore is also available. The journal (write-ahead log) is stored locally or on HDFS/S3 UFS. No managed database service (RDS, DynamoDB, DocumentDB) is used or defined in IaC. Surface flag `has_persistent_data_store=true` — this question applies. |
| **Gap** | All persistent state (metastore, journal) is self-managed and embedded. No automated failover at the database level — HA depends on the Raft-based embedded journal protocol. No managed backup, patching, or scaling for the data tier. |
| **Recommendation** | Evaluate Amazon DynamoDB (preferred) or Aurora as managed metastore backends. Implement a pluggable metastore adapter that abstracts the `InodeStore` and `BlockMetaStore` interfaces. This would enable managed failover, automatic scaling, and backup without changing the Alluxio server architecture. |
| **Evidence** | `pom.xml` (rocksdb.version=7.0.3), `core/server/master/src/main/java/alluxio/master/metastore/rocks/`, `core/server/master/src/main/java/alluxio/master/metastore/heap/`, `integration/kubernetes/helm-chart/alluxio/values.yaml` (metastore PVC config) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Alluxio Job Service (`job/server/`) implements a built-in task coordination system for distributed operations (load, migrate, persist, replicate). The `Scheduler` class (`core/server/master/src/main/java/alluxio/master/scheduler/`) coordinates job execution across job workers. Task planning, execution, and status tracking are implemented in application code with no dedicated orchestration service (no Step Functions, Temporal, or MWAA). Archetype: stateful-crud — the job system coordinates multi-step workflows that would benefit from managed orchestration. |
| **Gap** | All workflow orchestration logic is hardcoded in Java application code. No visual workflow management, no managed retry/error handling, no state machine definitions. Job failure recovery relies on custom in-code logic. |
| **Recommendation** | Evaluate AWS Step Functions for coordinating distributed jobs (load, migrate, persist, replicate). Step Functions provides visual workflow management, built-in retry/backoff, error handling, and state tracking. The existing `Scheduler` abstraction can serve as the integration point — replace the in-process executor with Step Functions state machine invocations. For preference alignment, EventBridge (preferred) can trigger Step Functions workflows based on file system events. |
| **Evidence** | `job/server/`, `core/server/master/src/main/java/alluxio/master/scheduler/`, `core/transport/src/main/proto/grpc/job_master.proto` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Inter-component communication is primarily synchronous gRPC (master↔worker, client↔master, job-master↔job-worker). The gRPC service definitions in `core/transport/src/main/proto/grpc/` define synchronous request/response RPCs. Some async patterns exist: worker heartbeats are periodic, async persist operations use a callback model, and the journal uses a write-ahead-log pattern. No managed messaging (SQS, SNS, EventBridge, MSK, Kinesis) or self-managed messaging (Kafka, RabbitMQ) is used. Archetype: stateful-crud — cross-service state changes (block allocation, file metadata updates, cache eviction) currently flow through synchronous gRPC and would benefit from event-driven decoupling. |
| **Gap** | No messaging infrastructure for cross-service state change propagation. Worker registration, block reports, and cache eviction events are handled through synchronous gRPC polling patterns. No event bus for file system change notifications. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for file system event notifications (file created, deleted, metadata changed). This enables downstream consumers to react to Alluxio events without polling. For cache eviction coordination between workers and masters, consider Amazon SQS for durable, decoupled message delivery. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `core/transport/src/main/proto/grpc/file_system_master.proto`, `core/transport/src/main/proto/grpc/block_master.proto`, `core/transport/src/main/proto/grpc/block_worker.proto`, `core/transport/src/main/proto/grpc/job_master.proto` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL definitions exist in the repository. No Terraform, CloudFormation, or CDK networking resources are defined. The Helm chart supports `hostNetwork: false` (default) for all components, which uses Kubernetes pod networking. The chart does not define NetworkPolicies for inter-pod communication restriction. The `alluxio-site.properties.template` comments out security settings. No VPC endpoints, PrivateLink, or VPC Lattice configurations exist. |
| **Gap** | No network segmentation is defined. Services deployed with this Helm chart rely entirely on the underlying Kubernetes cluster's network configuration, which is not codified. No restriction on inter-pod communication — any pod in the namespace can reach Alluxio services. |
| **Recommendation** | 1. Define Kubernetes NetworkPolicies in the Helm chart to restrict ingress to Alluxio master/worker/proxy ports from authorized pods only. 2. Create Terraform/CDK IaC for the EKS cluster (preferred) VPC with private subnets, security groups, and VPC endpoints for S3/DynamoDB access. 3. Consider AWS VPC Lattice for service-to-service networking if Alluxio is part of a larger service mesh. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (hostNetwork settings), `conf/alluxio-site.properties.template`, absence of `*.tf`, `*.cfn.yaml`, NetworkPolicy resources |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Alluxio Proxy (`core/server/proxy/`) provides an S3-compatible REST API and a legacy REST API for file operations. It runs as a separate Kubernetes Deployment (via Helm, `proxy.enabled: false` by default). The proxy uses Jetty as the embedded web server with Jersey (JAX-RS 2.34) for REST endpoints. No managed API Gateway (AWS API Gateway, ALB, CloudFront) is defined in IaC. The Helm chart exposes services via Kubernetes Service objects with ClusterIP (no Ingress or LoadBalancer by default). The `S3AuthenticationFilter` provides basic AWS v2/v4 signature authentication on the S3 API path. |
| **Gap** | No managed entry point with throttling, request validation, or centralized auth. The proxy is directly exposed via Kubernetes Service with no rate limiting, WAF, or DDoS protection at the infrastructure level. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point for the S3-compatible REST API. API Gateway provides throttling, request validation, AWS IAM/Cognito authentication, and CloudWatch access logging. For internal gRPC traffic, consider an AWS ALB with gRPC support or AWS App Mesh for service mesh routing. |
| **Evidence** | `core/server/proxy/src/main/java/alluxio/proxy/`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`, `integration/kubernetes/helm-chart/alluxio/values.yaml` (proxy section) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The Helm chart defines static resource requests/limits for all components: master (4 CPU, 8Gi memory), worker (4 CPU, 4Gi memory), job master (4 CPU, 8Gi memory), job worker (4 CPU, 4Gi memory), proxy (4 CPU, 4Gi memory). Master replicas are set to `count: 1` by default. Workers run as a DaemonSet (one per node). No Horizontal Pod Autoscaler (HPA), Vertical Pod Autoscaler (VPA), or Kubernetes Event-Driven Autoscaling (KEDA) is configured. No DynamoDB auto-scaling (N/A — no DynamoDB in use). |
| **Gap** | All capacity is statically provisioned. Cannot respond to data access traffic spikes. Worker count is fixed to the number of nodes in the DaemonSet. Proxy instances do not scale with request volume. |
| **Recommendation** | 1. Add HPA for the proxy Deployment based on CPU/memory or custom metrics (requests per second). 2. Consider converting workers from DaemonSet to Deployment with HPA for elastic scaling based on cache pressure metrics. 3. Add Cluster Autoscaler or Karpenter to the EKS cluster (preferred) to scale nodes when worker pods need more capacity. 4. For the master, scaling is constrained by the Raft consensus protocol — consider read replicas or caching for read-heavy metadata operations. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (resource limits, replica counts), absence of HPA/VPA/KEDA resources in Helm templates |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Alluxio has built-in backup capabilities in application code. The `BackupTracker`, `BackupLeaderRole`, and `BackupWorkerRole` classes (`core/server/master/src/main/java/alluxio/master/backup/`) coordinate metadata backup across master nodes. Journal checkpointing provides periodic state snapshots. The Helm chart provisions PersistentVolumeClaims for journal and metastore storage. However, no automated backup scheduling (AWS Backup, cron-based), retention policies, or restore testing procedures are defined in the repository. No cross-region backup replication. |
| **Gap** | Backup capability exists in code but is not automated through IaC. No defined retention periods. No documented restore procedures. No PITR capability. |
| **Recommendation** | 1. Define AWS Backup plans in Terraform/CDK for EBS volumes backing PVCs. 2. Automate Alluxio journal backup using a CronJob in the Helm chart that triggers the built-in backup API on a schedule. 3. Document and test restore procedures. 4. For journal stored on S3 UFS, enable S3 versioning and lifecycle policies. |
| **Evidence** | `core/server/master/src/main/java/alluxio/master/backup/`, `core/server/common/src/main/java/alluxio/master/journal/`, `integration/kubernetes/helm-chart/alluxio/values.yaml` (journal PVC config) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Helm chart supports HA for masters via embedded Raft journal when `master.count > 1` and `journal.type: EMBEDDED`. The StatefulSet template dynamically generates `alluxio.master.embedded.journal.addresses` for multi-master configurations. Workers run as a DaemonSet, inherently spanning all eligible nodes. However, `master.count` defaults to `1` (single master), and no explicit multi-AZ topology constraints (topologySpreadConstraints, pod anti-affinity, or zone-aware scheduling) are defined in the Helm chart. The underlying Kubernetes cluster's AZ topology is not codified. |
| **Gap** | Default configuration is single-master (single point of failure). No pod anti-affinity or topology spread constraints to ensure masters/workers span multiple AZs. Multi-AZ deployment depends on the cluster operator's manual configuration. |
| **Recommendation** | 1. Set `master.count: 3` as the production default for HA. 2. Add `topologySpreadConstraints` or `podAntiAffinity` to master StatefulSet and worker DaemonSet in the Helm chart to spread pods across AZs. 3. Define the EKS cluster (preferred) with subnets across 3 AZs in Terraform/CDK. 4. Configure journal storage on S3 (multi-AZ by default) rather than local PVC for durability. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/templates/master/statefulset.yaml` (replicas, embedded journal config), `integration/kubernetes/helm-chart/alluxio/values.yaml` (master.count: 1, journal type) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Helm chart (`integration/kubernetes/helm-chart/alluxio/`) defines the Kubernetes deployment for all Alluxio components: master StatefulSet, worker DaemonSet, proxy Deployment, FUSE DaemonSet, CSI driver, logserver, ConfigMaps, Services, and PVCs. A Kubernetes operator exists (`integration/kubernetes/operator/`). However, no cloud infrastructure IaC exists — no Terraform, CloudFormation, or CDK files define VPCs, security groups, EKS clusters, IAM roles, S3 buckets, monitoring resources, or backup plans. Helm chart coverage is approximately 40–50% of the total infrastructure needed for a production deployment. |
| **Gap** | Cloud infrastructure (networking, compute platform, IAM, storage, monitoring, backup) is entirely manual or undocumented. Only Kubernetes-level deployment is codified. |
| **Recommendation** | Create Terraform or CDK modules (preferred: CDK with TypeScript) for: EKS cluster, VPC with private subnets, security groups, IAM roles (IRSA for pods), S3 buckets for journal/UFS, CloudWatch alarms, and AWS Backup plans. Target 90%+ IaC coverage including operational/DR resources. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/` (Helm chart), `integration/kubernetes/operator/`, absence of `*.tf`, `*.cfn.yaml`, `cdk.json` files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions workflows exist for: unit tests (`java8_unit_tests.yml` — matrix strategy across modules), integration tests (`java8_integration_tests.yml` — 7 test matrix configurations), checkstyle and SpotBugs (`checkstyle.yml`), FUSE integration tests (`fuse_integration_tests.yml`), and an ATX transform workflow. Build is automated with Maven inside Docker containers (`dev/github/run_docker.sh`). However, no deployment pipeline exists — no stages for container image build/push to ECR, Helm chart deployment to staging or production, or automated rollback. Deployments are manual. |
| **Gap** | Build and test are automated; deployment is manual. No container image CI (build+push). No staging environment deployment. No automated rollback. No IaC pipeline for infrastructure changes. |
| **Recommendation** | 1. Add GitHub Actions workflow stages for: Docker image build → push to ECR → Helm chart deployment to EKS staging → integration test gate → manual approval → production promotion. 2. Add separate pipeline for Terraform/CDK infrastructure changes with plan → approve → apply stages. 3. Consider AWS CodePipeline + CodeBuild for deployment pipeline integration with EKS. |
| **Evidence** | `.github/workflows/java8_unit_tests.yml`, `.github/workflows/java8_integration_tests.yml`, `.github/workflows/checkstyle.yml`, `.github/workflows/fuse_integration_tests.yml`, `.github/workflows/atx-transform.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Primary language is Java 8 (`java.version=1.8` in `pom.xml`). AWS SDK v1 (1.11.815) and v2 (2.16.104) are both used. Key framework versions: gRPC 1.54.1, Netty 4.1.87, Protobuf 3.19.6, Jetty 9.4.46, Jersey 2.34, Jackson 2.13.5, Log4j 2.17.1. Secondary languages: Go 1.18 (CSI driver, operator), TypeScript/React (WebUI). Java 8 is a compound legacy signal — it reached end of public updates in 2019 (Oracle) and limits access to modern JVM features (records, pattern matching, virtual threads). AWS SDK v1 is in maintenance mode. The combination of Java 8 + AWS SDK v1 + Jetty 9 (pre-Jakarta EE) represents compound regression across language, SDK, and framework axes. |
| **Gap** | Java 8 limits adoption of modern cloud-native libraries and JVM optimizations. AWS SDK v1 is in maintenance mode with no new features. Jetty 9 uses javax.servlet (pre-Jakarta). PowerMock usage in tests prevents easy migration to newer Java versions. |
| **Recommendation** | 1. Upgrade to Java 17 (LTS) or Java 21 (LTS) — enables records, sealed classes, pattern matching, virtual threads (21+). 2. Complete migration from AWS SDK v1 to v2 (already partially adopted). 3. Upgrade Jetty to 11+ (Jakarta EE) and Jersey to 3.x. 4. Replace PowerMock with Mockito 4+ inline mocking (PowerMock blocks Java 11+). 5. Update Go to 1.21+ for CSI driver and operator. |
| **Evidence** | `pom.xml` (java.version=1.8, aws.amazonaws.version=1.11.815, awssdk.version=2.16.104, jetty.version=9.4.46.v20220331, grpc.version=1.54.1, powermock.version=2.0.7) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Alluxio is a distributed system with well-defined component boundaries: Master (metadata management, file system operations), Worker (block storage, data caching), Job Master/Worker (distributed task execution), Proxy (S3/REST API gateway), FUSE (POSIX interface), and CSI (Kubernetes volume interface). Each component runs as a separate process with distinct gRPC service interfaces defined in protobuf. However, all components are built from a single Maven multi-module project with extensive shared libraries (`core/common/`, `core/client/`, `core/transport/`). The Helm chart deploys them as separate containers within the same pod (master + job-master share a pod). There is one shared data model across all components via the protobuf definitions. Module boundaries are clear, interfaces are well-defined via gRPC/protobuf, and no circular dependencies are evident between the major components. |
| **Gap** | Components share a single build artifact pipeline (Maven multi-module). Master and job-master are co-located in the same pod. Shared libraries create deployment coupling — a change to `core/common` requires rebuilding all components. |
| **Recommendation** | Consider splitting the Maven build into separate build pipelines for master, worker, proxy, and job services to enable independent deployment. Evaluate separating master and job-master into distinct pods for independent scaling and failure isolation. The existing modular structure is a strong foundation that does not require microservices decomposition. |
| **Evidence** | `pom.xml` (modules list), `core/transport/src/main/proto/grpc/` (service definitions), `integration/kubernetes/helm-chart/alluxio/templates/master/statefulset.yaml` (master + job-master in same pod), `core/common/` (shared library) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Inter-component communication is primarily synchronous gRPC. The protobuf service definitions (`file_system_master.proto`, `block_master.proto`, `block_worker.proto`, `job_master.proto`) define synchronous unary RPCs for all operations. Some async patterns exist: worker heartbeats use periodic gRPC calls, async persist uses a callback model via the job system, and streaming RPCs exist for block data transfer. The journal uses an async write-ahead-log pattern. Archetype calibration: stateful-crud — cross-service state changes (block allocation, cache eviction, metadata updates) would benefit from async decoupling beyond what currently exists. |
| **Gap** | Worker block reports, cache eviction events, and metadata change notifications all flow through synchronous gRPC calls. No event-driven patterns for state change propagation between master and workers. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for file system event notifications. This enables downstream analytics consumers to subscribe to Alluxio events (file created, cache hit/miss, eviction) without polling the master. For high-throughput worker→master state updates, consider SQS-backed batch reporting to reduce gRPC call frequency. |
| **Evidence** | `core/transport/src/main/proto/grpc/file_system_master.proto`, `core/transport/src/main/proto/grpc/block_master.proto`, `core/transport/src/main/proto/grpc/block_worker.proto` |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Job Service handles long-running operations (load, migrate, persist, replicate) with a proper async task execution model. The `Scheduler` coordinates task distribution across job workers. Job status can be queried via the `job_master.proto` gRPC service (GetJobStatus, ListAllJobs). Tasks are tracked with status states and progress reporting. The job master provides a web UI for monitoring job progress. This is a well-designed async job system that correctly handles operations that can take minutes to hours. |
| **Gap** | The job system is built into the application code rather than using a managed orchestration service. Job retry, failure handling, and timeout logic are custom implementations. No dead-letter queue for failed tasks. |
| **Recommendation** | The existing job system is functional and well-designed for the current use case. For future scalability, evaluate migrating the job orchestration to AWS Step Functions with SQS-backed task queues. This would provide built-in retry policies, visual workflow monitoring, and better integration with the AWS ecosystem (preferred: EventBridge triggers). |
| **Evidence** | `job/server/`, `core/server/master/src/main/java/alluxio/master/scheduler/`, `core/transport/src/main/proto/grpc/job_master.proto` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The gRPC/protobuf API surface uses the `proto-backwards-compatibility` Maven plugin (v1.0.7) to enforce backward compatibility of protobuf message definitions. This provides automated versioning checks at build time for the primary inter-component API. The S3-compatible REST API (`core/server/proxy/src/main/java/alluxio/proxy/s3/`) implicitly uses the S3 API version standard. The legacy REST API (`PathsRestServiceHandler`, `StreamsRestServiceHandler`) has no explicit versioning — no `/v1/` path prefixes, no version headers. |
| **Gap** | The legacy REST API lacks explicit versioning. Protobuf backward compatibility checks are good but only cover gRPC services, not the REST surface. No versioning convention for the S3 proxy extensions beyond the standard S3 API. |
| **Recommendation** | 1. Add explicit URL-path versioning (`/api/v1/`) to the legacy REST API endpoints. 2. Document the protobuf backward compatibility policy and breaking change process. 3. Add OpenAPI specification generation (the `swagger-maven-plugin` is already configured in `pom.xml` but not actively generating specs for the proxy). |
| **Evidence** | `pom.xml` (proto-backwards-compatibility v1.0.7, swagger-maven-plugin configured), `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`, `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service discovery uses configuration-based and environment variable approaches. The master hostname is configured via `alluxio.master.hostname` property (hardcoded in `alluxio-site.properties`). In Kubernetes, the Helm chart generates ConfigMaps with master addresses derived from StatefulSet pod names (`alluxio-master-0`). For HA, ZooKeeper-based leader election enables dynamic master discovery when `master.count > 1` with embedded journal. Workers discover the master through the configured hostname or ZooKeeper. No service mesh (Istio, App Mesh), AWS Cloud Map, or dynamic service registry is used. |
| **Gap** | Non-HA single-master deployments rely on a hardcoded hostname. In Kubernetes, discovery works via StatefulSet DNS but is not dynamic — adding masters requires Helm chart reconfiguration. No service mesh or API catalog for external consumers. |
| **Recommendation** | 1. For Kubernetes deployments: the StatefulSet-based DNS discovery is functional. Consider adding Kubernetes-native service discovery via headless Services (already partially in place). 2. For broader integration: consider AWS Cloud Map or API Gateway (preferred) service registry for S3 proxy endpoint discovery by external consumers. 3. Evaluate AWS App Mesh or Istio for advanced traffic management between Alluxio components. |
| **Evidence** | `conf/alluxio-site.properties.template` (alluxio.master.hostname), `integration/kubernetes/helm-chart/alluxio/templates/config/alluxio-conf.yaml` (ConfigMap with master address), `integration/kubernetes/helm-chart/alluxio/templates/master/service.yaml` |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Alluxio IS a unified storage abstraction layer — it provides a virtual distributed file system over multiple under-storage systems. The `underfs/` directory contains 18 storage backend implementations: S3 (`underfs/s3a`), HDFS, GCS, Azure Blob (ABFS, WASB, ADL), Ceph (native and Hadoop), OBS, OSS, COS, COSN, Kodo, Ozone, Swift, TOS, and local filesystem. The `UnderFileSystem` abstraction (`core/common/src/main/java/alluxio/underfs/`) provides a unified interface for reading and writing unstructured data across all backends. S3 is a first-class under-storage with full support via the `s3a` module. |
| **Gap** | N/A — this is a mature implementation. No parsing pipeline (Textract, Tika) is built in, but that is outside Alluxio's scope as a caching/storage layer. |
| **Recommendation** | No gap to close. The unified storage abstraction is a best-practice implementation. For downstream consumers needing document parsing, consider adding Textract integration as an Alluxio extension or a separate pipeline consuming from the S3 UFS. |
| **Evidence** | `underfs/` (18 storage backends), `core/common/src/main/java/alluxio/underfs/UnderFileSystem.java`, `core/common/src/main/java/alluxio/underfs/UnderFileSystemFactory.java`, `underfs/s3a/` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The `UnderFileSystem` abstraction provides a textbook unified data access layer. All storage access goes through the `UnderFileSystem` interface, which is resolved at runtime via `UnderFileSystemFactoryRegistry` using a factory pattern. Each storage backend registers its factory, and the appropriate implementation is selected based on the URI scheme (s3://, hdfs://, gs://, etc.). The `UfsManager` manages UFS connections. The `BaseUnderFileSystem`, `ObjectUnderFileSystem`, and `ConsistentUnderFileSystem` base classes provide shared behavior. This is a single, well-defined point of data contract with consistent interfaces across 18+ storage systems. |
| **Gap** | N/A — exemplary unified data access pattern. |
| **Recommendation** | No action needed. This is a best-practice implementation that other systems could model. |
| **Evidence** | `core/common/src/main/java/alluxio/underfs/UnderFileSystem.java`, `core/common/src/main/java/alluxio/underfs/UnderFileSystemFactory.java`, `core/common/src/main/java/alluxio/underfs/UnderFileSystemFactoryRegistry.java`, `core/common/src/main/java/alluxio/underfs/UfsManager.java` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | RocksDB version 7.0.3 is explicitly pinned in `pom.xml` (`rocksdb.version=7.0.3`). RocksDB 7.0.3 was released in March 2022 and is not EOL (RocksDB has no formal EOL policy as an open-source library), but it is 3+ major versions behind the current release (8.x/9.x as of 2024-2025). The RocksDB configuration templates (`conf/rocks-block.ini.template`, `conf/rocks-inode.ini.template`, `conf/rocks-block-bloom.ini.template`, `conf/rocks-inode-bloom.ini.template`) show tuned configurations for the metastore. No documented version-update procedure exists. |
| **Gap** | RocksDB 7.0.3 is aging (3+ years old). No documented version-update procedure. Performance improvements and bug fixes in newer versions are not available. |
| **Recommendation** | 1. Evaluate upgrading to RocksDB 8.x or 9.x for performance improvements and bug fixes. 2. Document the RocksDB version-update procedure including: compatibility testing, data migration (if format changes), rollback plan, and performance benchmarking. 3. Add RocksDB version to the regular dependency update cycle. |
| **Evidence** | `pom.xml` (rocksdb.version=7.0.3), `conf/rocks-block.ini.template`, `conf/rocks-inode.ini.template`, `conf/rocks-block-bloom.ini.template`, `conf/rocks-inode-bloom.ini.template` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Alluxio does not use any SQL database, stored procedures, triggers, or proprietary SQL constructs. All business logic (file system operations, block management, cache eviction, job scheduling) is implemented in the Java application layer. The metastore uses RocksDB key-value pairs, not SQL. No `.sql` files exist in the repository. The protobuf definitions serve as the data schema, and all data access logic resides in the application code (`InodeStore`, `BlockMetaStore`). |
| **Gap** | N/A — no database coupling through stored procedures. |
| **Recommendation** | No action needed. All business logic in the application layer is a best practice that enables maximum flexibility for future database migration. |
| **Evidence** | Absence of `.sql` files, `core/server/master/src/main/java/alluxio/master/metastore/` (Java-based metastore), `core/transport/src/main/proto/proto/meta/` (protobuf schemas) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Alluxio has built-in audit logging via `AsyncUserAccessAuditLogWriter` (`core/server/common/src/main/java/alluxio/master/audit/`) and `AuditContext` with specialized contexts for different masters (`FileSystemMasterAuditContext`, `JobMasterAuditContext`, `S3AuditContext`). Audit logs capture user operations on the file system with timestamps, user identity, operation type, and resource paths. However, no AWS CloudTrail configuration exists in IaC. No immutable log storage (S3 Object Lock) is configured. Audit logs are written to the local file system and optionally forwarded to the logserver via the Helm chart's logserver component. |
| **Gap** | No CloudTrail for AWS API audit logging. Alluxio audit logs are stored locally with no immutability guarantees. No centralized log aggregation to CloudWatch or S3 with retention policies. |
| **Recommendation** | 1. Enable CloudTrail in Terraform/CDK IaC for AWS API audit logging. 2. Forward Alluxio audit logs to CloudWatch Logs or S3 with lifecycle policies. 3. Enable S3 Object Lock for immutable audit log storage. 4. Configure log retention policies in the Helm chart logserver. |
| **Evidence** | `core/server/common/src/main/java/alluxio/master/audit/AsyncUserAccessAuditLogWriter.java`, `core/server/common/src/main/java/alluxio/master/audit/AuditContext.java`, `core/server/master/src/main/java/alluxio/master/file/FileSystemMasterAuditContext.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java` |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption-at-rest configuration exists for Alluxio's data surfaces. The worker tiered storage (RAM, SSD, HDD) caches block data unencrypted. The master metastore (RocksDB) stores metadata unencrypted on local disk or PVC. Journal data is stored unencrypted. No KMS key references, `kms_key_id` parameters, or encryption configuration exist in the Helm chart or application configuration. Surface flag `has_at_rest_data_surface=true` — cached block data, metastore data, and journal data all constitute data at rest. Note: When Alluxio reads from S3 with server-side encryption, the under-storage data is encrypted in S3 but decrypted when cached in Alluxio's tiered storage. |
| **Gap** | All data at rest in Alluxio's managed storage (cache, metastore, journal) is unencrypted. Compliance risk for regulated workloads. The caching layer specifically decrypts S3-encrypted data and stores it unencrypted. |
| **Recommendation** | 1. Enable EBS encryption (via StorageClass with `encrypted: "true"` and KMS key) for PVCs used by master journal and metastore. 2. Use encrypted instance storage or encrypted EBS-backed emptyDir for worker tiered storage. 3. Add KMS key management in Terraform/CDK IaC. 4. Evaluate Alluxio's data encryption capabilities or consider application-layer encryption for cached blocks. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (tieredstore config, journal PVC — no encryption), `conf/alluxio-site.properties.template` (no encryption settings), absence of KMS resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Alluxio provides SASL-based authentication with two providers: `SimpleAuthenticationProvider` (OS user identity) and `CustomAuthenticationProvider` (pluggable custom auth). The S3 proxy has `S3AuthenticationFilter` which validates AWS Signature V2 and V4 headers, providing credentials-based authentication for the S3 API surface. The gRPC services use SASL authentication via `AuthenticationServer` and `AuthenticationUtils`. Authentication type is configurable via `alluxio.security.authentication.type` (default: SIMPLE). No OAuth2, JWT, or token-based authentication is implemented. No API keys with rotation. |
| **Gap** | SIMPLE authentication provides only OS-level user identity without actual credential verification. The S3 proxy auth validates AWS signatures but manages credentials internally rather than through AWS IAM. No token-based auth (OAuth2/JWT) for modern API consumers. No centralized auth for gRPC services. |
| **Recommendation** | 1. Implement OAuth2/JWT authentication for the REST/S3 API surface. Use AWS API Gateway (preferred) with Cognito authorizer for token validation. 2. For gRPC services, implement mTLS or JWT-based per-request authentication. 3. Evaluate IRSA (IAM Roles for Service Accounts) in EKS for AWS credential management in pods. |
| **Evidence** | `core/common/src/main/java/alluxio/security/authentication/`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/auth/`, `conf/alluxio-site.properties.template` |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Alluxio manages authentication entirely independently. The `SimpleAuthenticationProvider` uses the OS user running the Alluxio process. The `CustomAuthenticationProvider` allows pluggable authentication but no built-in integration with centralized IdPs (Cognito, Okta, Ping, LDAP, Active Directory) exists in the codebase. Authorization uses a POSIX-style permission model (`core/common/src/main/java/alluxio/security/authorization/`). No OIDC, SAML, or SSO configuration exists. No federation with external identity providers. |
| **Gap** | No centralized identity integration. Each Alluxio deployment manages its own user identity independently. No SSO, no SAML/OIDC federation, no LDAP integration in the codebase. |
| **Recommendation** | 1. Implement OIDC/SAML integration with Amazon Cognito (or compatible IdP) for the S3 proxy REST API. 2. For internal gRPC services, evaluate Kubernetes-native service account auth combined with IRSA for AWS resource access. 3. Consider LDAP integration for the CustomAuthenticationProvider for enterprise environments. |
| **Evidence** | `core/common/src/main/java/alluxio/security/authentication/plain/SimpleAuthenticationProvider.java`, `core/common/src/main/java/alluxio/security/authentication/plain/CustomAuthenticationProvider.java`, `core/common/src/main/java/alluxio/security/authorization/` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Helm chart supports Kubernetes Secrets mounting for sensitive configuration (`values.yaml` secrets section). No plaintext credentials were found committed in the repository — the `alluxio-site.properties.template` uses placeholder comments for security-sensitive properties. Configuration properties are injected via ConfigMap environment variables. However, no AWS Secrets Manager, HashiCorp Vault, or external secrets operator integration exists. No rotation mechanism for credentials. The `update.check.auth.string` in `pom.xml` contains a base64-encoded string for diagnostics check, which is a low-risk finding (not a production credential). |
| **Gap** | No dedicated secrets management system with rotation. Credentials are managed through Kubernetes Secrets (no encryption at rest by default in etcd) or environment variables. No rotation configured for any credentials. |
| **Recommendation** | 1. Integrate AWS Secrets Manager via the External Secrets Operator for Kubernetes. 2. Store S3 credentials, database connection strings, and authentication keys in Secrets Manager with automated rotation. 3. Enable EKS envelope encryption for etcd to protect Kubernetes Secrets at rest. 4. Use IRSA for AWS credential management instead of static access keys. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/values.yaml` (secrets section), `conf/alluxio-site.properties.template` (commented-out security properties), `pom.xml` (update.check.auth.string — low risk) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The Dockerfile uses `rockylinux:8` (Java 8 path) or `centos:7` (Java 11 path, despite the name) as base images. CentOS 7 reached EOL on June 30, 2024. The Dockerfile installs packages via `yum` and compiles libfuse from source (GitHub clone). No vulnerability scanning (AWS Inspector, Trivy, Snyk) is configured. No base image hardening (CIS benchmarks, Bottlerocket). No SSM Patch Manager or equivalent managed patching. The image runs as a non-root user (`ALLUXIO_UID=1000` by default), which is a positive security practice. Go components use `golang:1.18-alpine3.17` which is also dated. |
| **Gap** | CentOS 7 base image is EOL. No vulnerability scanning in the container build process. No managed patching strategy. No hardened base images. Go 1.18 is past EOL. |
| **Recommendation** | 1. Migrate from CentOS 7/RockyLinux 8 to Amazon Linux 2023 or Bottlerocket for EKS-optimized, hardened base images. 2. Add Trivy or ECR image scanning to the container build pipeline. 3. Update Go base image to 1.22+ for CSI driver builds. 4. Implement a regular base image update cadence (monthly). 5. Add `docker scan` or Snyk container scanning to CI pipeline. |
| **Evidence** | `integration/docker/Dockerfile` (FROM rockylinux:8, centos:7, golang:1.18-alpine3.17), absence of vulnerability scanning in `.github/workflows/` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline includes Checkstyle (`maven-checkstyle-plugin` v3.1.2 with custom rules at `build/checkstyle/alluxio_checks.xml`) and SpotBugs (`spotbugs-maven-plugin` v4.0.4 with `build/findbugs/findbugs-exclude.xml`). These tools catch code style issues and common bug patterns. The `checkstyle.yml` GitHub Actions workflow runs these checks on every pull request. However, no SAST tool (SonarQube, Semgrep, CodeGuru Reviewer), no dependency vulnerability scanning (Dependabot, Snyk, OWASP dependency-check), no container scanning, and no DAST tool is configured. No security gate blocks merges on critical findings. |
| **Gap** | SpotBugs catches some security-relevant bug patterns, but it is not a dedicated SAST tool. No dependency scanning to detect known CVEs in the 100+ transitive dependencies. No container image scanning. No security blocking gate in CI. |
| **Recommendation** | 1. Add Dependabot configuration (`.github/dependabot.yml`) for automated dependency update PRs. 2. Add OWASP dependency-check Maven plugin or Snyk to the CI pipeline. 3. Add ECR image scanning or Trivy to the container build process. 4. Consider Amazon CodeGuru Reviewer or Semgrep for SAST. 5. Configure security gates to block PRs with critical/high CVEs. |
| **Evidence** | `pom.xml` (maven-checkstyle-plugin, spotbugs-maven-plugin), `.github/workflows/checkstyle.yml`, `build/checkstyle/`, `build/findbugs/findbugs-exclude.xml`, absence of Dependabot, Snyk, or SAST tools |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OpenTelemetry infrastructure is configured in `integration/metrics/`: OTel Collector (`otel-collector-config.yaml`) receives OTLP gRPC traces and exports to Jaeger and Prometheus. OTel Agent (`otel-agent-config.yaml`) forwards traces to the collector. Docker Compose files (`docker-compose-master.yaml`, `docker-compose-worker.yaml`) define Jaeger all-in-one, OTel Collector, OTel Agent, and Prometheus containers. Trace pipelines are defined for both metrics and traces. The infrastructure for trace collection and export is in place. However, trace ID propagation across all service boundaries (master→worker gRPC calls, proxy→master, job-master→job-worker) is not verified to be complete from the configuration alone. |
| **Gap** | Tracing infrastructure exists but may have gaps in cross-service propagation. The OTel configuration is in Docker Compose (development/testing) but not in the Helm chart for production deployment. Metrics are integrated in the Helm chart, but tracing is not. |
| **Recommendation** | 1. Add OpenTelemetry Java agent auto-instrumentation to the Helm chart JVM options for all components. 2. Ensure trace context propagation headers are forwarded across gRPC calls (master↔worker, job-master↔job-worker). 3. Deploy the OTel Collector as a sidecar or DaemonSet in the Helm chart for production. 4. Export traces to AWS X-Ray for integration with the AWS ecosystem. |
| **Evidence** | `integration/metrics/otel-collector-config.yaml`, `integration/metrics/otel-agent-config.yaml`, `integration/metrics/docker-compose-master.yaml`, `integration/metrics/prometheus.yaml` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist in the repository. No error budget tracking. No formal definition of acceptable service levels for latency, availability, or cache hit rates. The metrics system provides operational data (cache hit rates, RPC latencies, throughput) that could back SLO definitions, but no targets are defined. No CloudWatch alarms on p99/p95 latency. No SLO dashboards. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. Cannot measure whether the system is meeting user expectations. No error budget to drive prioritization of reliability investments. |
| **Recommendation** | 1. Define SLOs for critical operations: metadata RPC latency (p99 < X ms), cache hit rate (> Y%), data read throughput, and system availability. 2. Implement error budget tracking using Prometheus alerting rules or CloudWatch composite alarms. 3. Create SLO dashboards using the existing Prometheus/Grafana stack or CloudWatch dashboards. |
| **Evidence** | Absence of SLO definition files, absence of CloudWatch alarm definitions, `core/common/src/main/java/alluxio/metrics/MetricKey.java` (metrics that could back SLOs exist) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Alluxio has a rich custom metrics system built on Dropwizard Metrics with Prometheus integration. The `MetricKey` class defines hundreds of custom metrics including business-relevant operational metrics: `CLUSTER_BYTES_READ_LOCAL`, `CLUSTER_BYTES_READ_UFS`, `CLUSTER_CACHE_HIT_RATE`, `MASTER_FILES_COMPLETED`, `WORKER_BLOCKS_EVICTED`, RPC latencies, and throughput counters. The metrics system supports multiple sink types (Console, CSV, JMX, Graphite, Slf4j, Prometheus) configurable via `metrics.properties`. The Helm chart supports Prometheus pod annotations for metrics scraping. However, metrics are focused on system operational data rather than end-user business outcomes. |
| **Gap** | Metrics are comprehensive for system operations but lack end-user business outcome metrics (e.g., query acceleration factor, user job completion rates, cost savings from caching). |
| **Recommendation** | 1. Define business outcome metrics: data locality ratio (% of reads served from cache vs UFS), query latency reduction for downstream compute frameworks, and storage cost savings from tiered caching. 2. Publish these metrics alongside infrastructure metrics in the existing Prometheus pipeline. 3. Create business-focused Grafana dashboards. |
| **Evidence** | `core/common/src/main/java/alluxio/metrics/MetricKey.java`, `core/common/src/main/java/alluxio/metrics/MetricsSystem.java`, `core/common/src/main/java/alluxio/metrics/MetricsConfig.java`, `conf/metrics.properties.template`, `integration/kubernetes/helm-chart/alluxio/templates/config/alluxio-metrics.yaml` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration exists in the repository. Metrics are exported to Prometheus and Graphite but no alerting rules are defined. No CloudWatch alarms. No PagerDuty, OpsGenie, or SNS notification integration. The metrics infrastructure can support alerting but no alert definitions ship with the product. The WebUI for master and worker provides real-time metric dashboards but no threshold-based alerting. |
| **Gap** | No alerting configured. Operators cannot be notified of degraded performance, cache pressure, master failover, or worker disconnection without external configuration. |
| **Recommendation** | 1. Add Prometheus alerting rules (PrometheusRule resources in the Helm chart) for critical conditions: master availability, worker connectivity, cache hit rate degradation, RPC latency spikes, disk usage thresholds. 2. Configure CloudWatch anomaly detection on key metrics if forwarding to CloudWatch. 3. Add PagerDuty/OpsGenie/SNS integration for alert routing. 4. Ship default Grafana dashboard templates with the Helm chart. |
| **Evidence** | `integration/metrics/prometheus.yaml` (Prometheus config — no alerting rules), absence of PrometheusRule or CloudWatch alarm definitions in Helm chart |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The master StatefulSet uses `podManagementPolicy: Parallel` which starts/stops all pods simultaneously (not a staged rollout). The worker DaemonSet uses the default `RollingUpdate` strategy with no `maxUnavailable` customization. The logserver uses `strategy.type: Recreate`. No canary, blue/green, or traffic-shifting deployment strategy is defined. No CodeDeploy, Argo Rollouts, or Flagger integration. No feature flags for gradual rollout. The deployment approach is direct-to-production when Helm chart values are applied. |
| **Gap** | No staged deployment strategy. Master updates affect all master pods simultaneously. No ability to validate new versions before full rollout. No automated rollback on failure. |
| **Recommendation** | 1. Change master StatefulSet `podManagementPolicy` to `OrderedReady` and implement rolling updates with `maxUnavailable: 1` for controlled master upgrades. 2. Evaluate Argo Rollouts for canary deployments of the proxy component. 3. Implement health-check-based rollback using Helm hooks or Argo Rollouts analysis. 4. For workers (DaemonSet), configure `maxUnavailable` to limit the blast radius of updates (e.g., 10% at a time). |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/templates/master/statefulset.yaml` (podManagementPolicy: Parallel), `integration/kubernetes/helm-chart/alluxio/values.yaml` (logserver strategy: Recreate) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | A comprehensive integration test suite exists in the `tests/` module, executed via `java8_integration_tests.yml` GitHub Actions workflow. The test matrix covers 7 configurations testing: client CLI, file system operations (concurrent, IO), client operations, job/master/stress tests, and server tests. Integration tests run in Docker containers via `dev/github/run_docker.sh`. FUSE integration tests run in a separate workflow (`fuse_integration_tests.yml`). WebUI integration tests run in `java8_integration_tests_webui.yml`. Tests include minicluster-based integration tests using `minicluster/` for in-process cluster simulation. |
| **Gap** | Integration tests cover application-level functionality but do not test Kubernetes deployment scenarios (Helm chart deployment, upgrade, failover). No contract tests for the S3 API compatibility. No performance regression testing in CI. |
| **Recommendation** | 1. Add Helm chart deployment tests (helm test or kind/k3s-based) to validate Kubernetes deployment correctness. 2. Add S3 API compatibility contract tests against the official S3 API test suite. 3. Consider adding performance regression tests using the existing `stress/` and `microbench/` modules in CI (with baseline comparison). |
| **Evidence** | `.github/workflows/java8_integration_tests.yml`, `.github/workflows/fuse_integration_tests.yml`, `.github/workflows/java8_integration_tests_webui.yml`, `tests/`, `minicluster/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automated incident response, or self-healing automation exists. The `shell/src/main/java/alluxio/cli/bundler/` contains a `CollectInfo` diagnostic bundle tool that gathers system information, logs, and configuration for post-incident analysis. The `docs/` directory contains operational documentation. No Systems Manager Automation documents, Lambda-based remediation, or Step Functions for incident workflows. No automated recovery from common failure modes (master OOM, worker disconnection, journal corruption). |
| **Gap** | Incident response is entirely ad hoc. The CollectInfo bundler helps with diagnostics but provides no automated remediation. No runbooks — neither machine-readable nor as documentation. |
| **Recommendation** | 1. Create machine-readable runbooks (YAML or Markdown with structured steps) for common failure modes: master leader election, worker restart, journal backup/restore, metastore recovery. 2. Implement Kubernetes-native self-healing via PodDisruptionBudgets (already partially there via StatefulSet), liveness/readiness probes (configured in Helm chart), and custom Kubernetes operators for Alluxio-specific recovery. 3. Add AWS Systems Manager Automation documents for common operational tasks. |
| **Evidence** | `shell/src/main/java/alluxio/cli/bundler/` (CollectInfo diagnostic tool), absence of runbook files, `docs/` (operational documentation — not structured runbooks) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Component ownership is defined in `dev/github/component_owners.yaml` mapping 17 components to specific GitHub users (e.g., core→tcrain, job→rongrong, underfs→fuzhengjia, webui→tieujason330). The master and worker WebUI (`MasterWebServer`, `WorkerWebServer`) provide per-service dashboards showing operational metrics. However, no named owners for alarms or SLOs exist (no alarms or SLOs are defined). No team attribution on observability assets. The component owners file covers code ownership but not operational ownership of monitoring and alerting. |
| **Gap** | Code ownership is well-defined but operational/observability ownership is not. No alarm owners, no SLO owners, no team-attributed dashboards. |
| **Recommendation** | 1. Extend `component_owners.yaml` to include observability ownership (who owns alerting and SLOs for each component). 2. Create per-service Grafana dashboards with owner annotations. 3. When SLOs are defined (per OPS-Q2 recommendation), assign team owners to each SLO. |
| **Evidence** | `dev/github/component_owners.yaml`, `core/server/master/src/main/java/alluxio/web/MasterWebServer.java` (master WebUI), `core/server/worker/src/main/java/alluxio/web/WorkerWebServer.java` (worker WebUI) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Helm chart applies consistent Kubernetes labels to all resources: `app` (alluxio name), `chart` (chart version), `release` (Helm release name), `heritage` (Helm), and `role` (alluxio-master, alluxio-worker, etc.). These labels enable Kubernetes-native resource identification and selection. However, no AWS resource tagging is configured (no `default_tags` in Terraform, no tag policies, no cost allocation tags). No AWS Config rules for tag enforcement. The Helm chart does not support custom label/annotation injection for cloud-provider-specific tagging. |
| **Gap** | Kubernetes labels are consistent but no AWS-level resource tagging for cost allocation, ownership, or environment identification. |
| **Recommendation** | 1. Add a `tags` section to the Helm chart values that injects custom labels/annotations to all resources (enabling cloud-provider cost allocation integration). 2. When Terraform/CDK IaC is created (per INF-Q10 recommendation), include `default_tags` for all AWS resources with: Environment, Team, Project, CostCenter. 3. Enable AWS cost allocation tags and Config rules for tag governance. |
| **Evidence** | `integration/kubernetes/helm-chart/alluxio/templates/master/statefulset.yaml` (labels: app, chart, release, heritage, role), absence of AWS tagging configuration |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q1, INF-Q2, APP-Q1, APP-Q5, DATA-Q3, SEC-Q5, SEC-Q7 | Maven parent POM with Java 8, dependency versions (RocksDB 7.0.3, AWS SDK v1/v2, gRPC 1.54.1) |
| `integration/docker/Dockerfile` | INF-Q1, SEC-Q6 | Multi-stage Dockerfile: Go CSI build, RockyLinux 8/CentOS 7 base, Java 8/11, libfuse compilation |
| `integration/kubernetes/helm-chart/alluxio/values.yaml` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, OPS-Q4, OPS-Q5, OPS-Q9, SEC-Q2, SEC-Q5 | Helm chart values: component configs, resource limits, replica counts, journal settings, tiered storage |
| `integration/kubernetes/helm-chart/alluxio/templates/master/statefulset.yaml` | INF-Q1, INF-Q9, OPS-Q5, OPS-Q9 | Master StatefulSet: HA support, podManagementPolicy, probes, labels |
| `integration/kubernetes/helm-chart/alluxio/templates/worker/daemonset.yaml` | INF-Q1 | Worker DaemonSet definition |
| `integration/kubernetes/helm-chart/alluxio/templates/config/alluxio-conf.yaml` | APP-Q6 | ConfigMap with master addresses, worker/proxy JVM opts |
| `integration/kubernetes/helm-chart/alluxio/Chart.yaml` | INF-Q10 | Helm chart metadata (v0.6.54) |
| `.github/workflows/java8_unit_tests.yml` | INF-Q11 | Unit test CI pipeline with matrix strategy |
| `.github/workflows/java8_integration_tests.yml` | INF-Q11, OPS-Q6 | Integration test CI pipeline with 7 test configurations |
| `.github/workflows/checkstyle.yml` | INF-Q11, SEC-Q7 | Checkstyle, SpotBugs, and license check CI |
| `.github/workflows/fuse_integration_tests.yml` | OPS-Q6 | FUSE-specific integration tests |
| `core/transport/src/main/proto/grpc/` | APP-Q2, APP-Q3, INF-Q3, INF-Q4 | gRPC service protobuf definitions for all components |
| `core/server/master/src/main/java/alluxio/master/metastore/` | INF-Q2, DATA-Q3 | Metastore implementations (RocksDB, heap, caching) |
| `core/server/master/src/main/java/alluxio/master/backup/` | INF-Q8 | Backup/recovery implementation |
| `core/server/master/src/main/java/alluxio/master/scheduler/` | INF-Q3, APP-Q4 | Job scheduling and task coordination |
| `core/common/src/main/java/alluxio/underfs/` | DATA-Q1, DATA-Q2 | Unified data access layer: UnderFileSystem abstraction |
| `underfs/` | DATA-Q1 | 18 storage backend implementations (S3, HDFS, GCS, Azure, etc.) |
| `core/common/src/main/java/alluxio/security/` | SEC-Q3, SEC-Q4 | Authentication and authorization framework |
| `core/server/common/src/main/java/alluxio/master/audit/` | SEC-Q1 | Audit logging framework |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/` | INF-Q6, SEC-Q3 | S3-compatible REST API, authentication filter |
| `core/common/src/main/java/alluxio/metrics/` | OPS-Q3 | Metrics system with Dropwizard/Prometheus integration |
| `integration/metrics/` | OPS-Q1, OPS-Q4 | OpenTelemetry, Jaeger, Prometheus configuration |
| `conf/alluxio-site.properties.template` | INF-Q5, SEC-Q2, SEC-Q5, APP-Q6 | Configuration template with security and master address settings |
| `conf/rocks-*.ini.template` | DATA-Q3 | RocksDB tuning configurations |
| `dev/github/component_owners.yaml` | OPS-Q8 | Code/component ownership mapping |
| `job/server/` | INF-Q3, APP-Q4 | Job service for distributed task execution |
| `integration/kubernetes/operator/` | INF-Q1, INF-Q10 | Kubernetes operator for Alluxio management |
| `shell/src/main/java/alluxio/cli/bundler/` | OPS-Q7 | CollectInfo diagnostic bundle tool |
| `tests/` | OPS-Q6 | Integration test suite |
| `minicluster/` | OPS-Q6 | In-process cluster simulation for testing |
| `docs/` | Quick Agent Wins | Extensive documentation for knowledge agent |
| `README.md` | Quick Agent Wins | Project documentation and getting started guide |
