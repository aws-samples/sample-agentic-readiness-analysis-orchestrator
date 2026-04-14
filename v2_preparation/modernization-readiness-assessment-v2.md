# Modernization Readiness Assessment Guide

**A technical evaluation framework for assessing the cloud architecture maturity, operational readiness, and modernization potential of enterprise applications and infrastructure.**

AWS Agentic Practice | Version 2.0 | 2026

---

## What Is Modernization Readiness?

Modernization Readiness is the state where an enterprise's applications, infrastructure, and operational practices are mature enough to support iterative improvement — whether that means containerizing workloads, decomposing monoliths, migrating to managed services, eliminating license costs, or adopting modern DevOps practices.

This assessment evaluates the **current state** of cloud architecture maturity and identifies **modernization opportunities** across infrastructure, application architecture, data platforms, and operational practices. It is distinct from Agentic Readiness, which evaluates whether systems can safely serve as tools for autonomous AI agents. Modernization Readiness focuses on whether the foundation is solid for any transformation initiative — agentic or otherwise.

---

## How to Use This Guide

This framework evaluates the cloud maturity and modernization potential of applications and infrastructure. Run it per application or infrastructure repository. Each question is scored on a 1–4 scale:

| Score | Label | Meaning |
|-------|-------|---------|
| **4** | ✅ Mature | Fully meets the criterion. No gaps. Best-practice implementation. |
| **3** | 🟡 Partial | Partially meets the criterion. Minor gaps. Functional but improvable. |
| **2** | 🟠 Needs Work | Exists but significant gaps. Moderate effort needed. |
| **1** | ❌ Not Present | Missing entirely or fundamentally inadequate. |

### Scope Boundary

This assessment covers **cloud architecture and operational maturity** — the infrastructure, application patterns, data platforms, and DevOps practices that determine how ready a system is for modernization. It does not cover:

- **Agentic Readiness** — Whether systems can serve as agent tools (API surface, agent identity, transactional integrity, agent observability). See the Agentic Readiness Assessment Guide.
- **Agent design** — Prompt engineering, model selection, agent behavioral testing.


---

## Data Sources

- Infrastructure as Code (Terraform, CloudFormation, CDK, ACK, KRO)
- Declarative Config (Helm Charts, Kustomize, Ansible)
- Dependency manifests (package.json, requirements.txt, pom.xml, go.mod, *.csproj)
- CI/CD pipeline configurations (.github/*, buildspec.yml, Jenkinsfile)
- Container definitions (Dockerfile, docker-compose.yml, Kubernetes manifests)
- Application source code (GitHub, GitLab, CodeCommit)
- AWS resource inventory (via AWS Config)

---

## Repository Type Classification

Before running the assessment, the repository must be classified. This classification determines which questions apply (some are N/A for non-application repos) and which pathways are not applicable. The Power orchestrator performs this classification and passes `repo_type` to the TD. Users can override via `repo_type` in the portfolio config.

**Classification Decision Tree:**

| Repo Type | Detection Rule | Example |
|-----------|---------------|---------|
| `application` | Source code files exist with a deployable entry point (main(), server.listen(), Dockerfile, IaC) | Java service, Python API, Node.js app |
| `infrastructure-only` | Only IaC provisioning files exist (Terraform, CDK, CloudFormation) with no source code and no deployment configs | Terraform modules, CDK stacks, CloudFormation templates |
| `deployment-config` | Only deployment configurations, CI/CD definitions, or operational manifests exist — no application source code. Includes: CI/CD pipelines (GitHub Actions, Jenkinsfile, buildspec.yml), Kubernetes manifests (Helm charts, Kustomize overlays, ArgoCD app definitions), GitOps configs, Ansible playbooks, service mesh configs, environment definitions. | Helm chart repos, GitOps config repos, CI/CD pipeline repos, Ansible playbook repos |
| `monorepo` | Multiple independent service directories with separate build configs | Monorepo with services/ dirs each with own package manifest |
| `library` | Package manifest exists but no deployable entry point (no Dockerfile, no IaC, no main()) | Internal SDK, shared utilities package |

The `repo_type` is passed as `additionalPlanContext` to the TD. Users can always override via `repo_type` in the portfolio config.

**N/A Questions by Repo Type (MOD):**

| Repo Type | Questions Scored as N/A |
|-----------|----------------------|
| `application` | None — all 37 questions apply |
| `infrastructure-only` | APP-Q1 through APP-Q6, DATA-Q1 through DATA-Q2, DATA-Q4 |
| `deployment-config` | APP-Q1 through APP-Q6, DATA-Q1 through DATA-Q4, INF-Q1 through INF-Q4, INF-Q6 through INF-Q9 |
| `library` | INF-Q1 through INF-Q11, OPS-Q2 through OPS-Q9 |
| `monorepo` | None — all 37 questions apply (assessed per-service within the repo) |

**N/A Pathways by Repo Type:**

| Repo Type | Not Applicable Pathways |
|-----------|------------------------|
| `application` | None — all 7 pathways applicable |
| `infrastructure-only` | Move to Cloud Native, Move to Containers, Move to AI, Move to Managed Analytics |
| `deployment-config` | Move to Cloud Native, Move to Containers, Move to Open Source, Move to Managed Databases, Move to Managed Analytics, Move to AI |
| `library` | Move to Containers, Move to Modern DevOps, Move to Managed Databases, Move to Managed Analytics, Move to Cloud Native |
| `monorepo` | None — all 7 pathways applicable |

**How the TD Uses repo_type:**

1. Read `repo_type` from `additionalPlanContext`. If not provided, default to `application`.
2. Before evaluating each section, check the N/A Questions mapping above. If a question is N/A for the detected repo type, skip evaluation and record it as:
   - **Score**: N/A
   - **Finding**: This is a `{repo_type}` repository. This question does not apply.
   - **Gap**: N/A
   - **Recommendation**: N/A
3. N/A questions are excluded from category score averages (excluded from both numerator and denominator).
4. If ALL questions in a category are N/A, the category score is "N/A" and is excluded from the overall score average.
5. Before evaluating pathways, check the N/A Pathways mapping above. N/A pathways are listed in the pathway table with status "Not Applicable" and a reason.
6. All questions and pathways must still appear in the report — N/A items are listed with the N/A format, not omitted.

---

## 01 — Infrastructure, Platform, and DevOps

These questions evaluate the compute, networking, platform services, and deployment practices underpinning the application.

### INF-Q1: Managed Compute

**Question:** What percentage of compute workloads use managed container orchestration (EKS, ECS, Fargate) or serverless (Lambda) vs raw EC2?

**Why it matters:** Managed compute provides elastic scaling, reduced operational overhead, and faster deployment cycles. EC2 requires manual scaling, patching, and capacity planning. Modernization starts with moving off self-managed compute.

- Score 4: 80%+ of compute is ECS/EKS/Lambda/Fargate. EC2 only for edge cases.
- Score 3: Mix of managed and EC2, with managed compute for primary workloads.
- Score 2: Primarily EC2 with some containerization or Lambda for auxiliary functions.
- Score 1: All compute on raw EC2 or on-premises with no managed services.

> Look for: Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` vs `aws_instance`; CloudFormation resource types; Dockerfile presence; Kubernetes manifests.

### INF-Q2: Managed Databases

**Question:** Are databases fully managed (RDS/Aurora/DynamoDB/DocumentDB) vs self-managed?

**Why it matters:** Self-managed databases — regardless of where they run (EC2, containers, on-premises) — introduce maintenance windows, manual patching, and operational overhead. Migrating to managed services eliminates ops burden and enables automatic backups, failover, and scaling. This is a primary target for AWS DMS/SCT-based migration pathways.

- Score 4: All databases are managed services with automated failover.
- Score 3: Primary databases managed; some auxiliary self-managed instances remain.
- Score 2: Mix of managed and self-managed, or managed but single-AZ without failover.
- Score 1: All databases self-managed on EC2, containers, or on-premises.

> Look for: Terraform `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*` vs compute resources running database software; connection strings pointing to self-hosted instances; database engine installation in Dockerfiles or user-data scripts.

### INF-Q3: Workflow Orchestration

**Question:** Are workflow orchestration services used (Step Functions, Temporal, Camunda) or are workflows primarily implemented as hardcoded application logic?

**Why it matters:** Dedicated workflow orchestration provides visual workflow management, error handling, retry logic, and state management. Without it, all orchestration logic is buried in code — harder to maintain, debug, and evolve.

- Score 4: Dedicated workflow orchestration service in use for business-critical workflows.
- Score 3: Partial adoption — some workflows orchestrated, others still in code.
- Score 2: Simple state machines in code with some structure, but no dedicated service.
- Score 1: No orchestration — all workflow logic hardcoded in application code.

> Look for: `aws_sfn_*` in Terraform; Temporal SDK imports; workflow YAML definitions; state machine patterns in code.

### INF-Q4: Async Messaging and Streaming

**Question:** Is there managed messaging or streaming infrastructure (SQS, SNS, EventBridge, MSK, Kinesis) vs self-managed Kafka/RabbitMQ, or no messaging at all?

**Why it matters:** Managed messaging and streaming enable event-driven architectures with reduced operational overhead. Self-managed message brokers and streaming platforms require patching, scaling, and monitoring. Async patterns are foundational for decoupled, resilient architectures.

- Score 4: Managed messaging and/or streaming services in use for inter-service communication and data pipelines.
- Score 3: Managed messaging for some flows; synchronous HTTP or self-managed components for others.
- Score 2: Self-managed messaging/streaming (Kafka, RabbitMQ on EC2/containers).
- Score 1: No messaging or streaming infrastructure — all communication is synchronous HTTP, batch-only data pipelines.

> Look for: `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*` in IaC; SDK imports for messaging/streaming; event-driven patterns in code; stream consumer patterns.

### INF-Q5: Network Security

**Question:** Are services deployed in a VPC with private subnets, security groups, NACLs, and proper network segmentation?

**Why it matters:** Network segmentation limits blast radius of failures and security incidents. Services exposed directly to the internet without proper network controls are a security and operational risk.

- Score 4: Services in private subnets, least-privilege security groups, network segmentation present.
- Score 3: VPC with subnets but some overly permissive rules or missing segmentation.
- Score 2: Basic VPC setup but services in public subnets or with 0.0.0.0/0 rules.
- Score 1: No VPC configuration or services deployed outside VPC controls.

> Look for: `aws_vpc`, `aws_subnet`, `aws_security_group`; subnet tiers (public vs private); security group rules; overly permissive rules (0.0.0.0/0).

### INF-Q6: API Entry Point

**Question:** Is there an API Gateway, ALB, or CloudFront as the entry point vs direct service exposure?

**Why it matters:** A managed entry point provides throttling, authentication, request validation, and a single point of control. Direct service exposure lacks these protections and makes it harder to manage traffic patterns.

- Score 4: API Gateway with throttling, auth, and request validation.
- Score 3: ALB or CloudFront with basic routing and health checks.
- Score 2: Load balancer present but minimal configuration (no auth, no throttling).
- Score 1: Services exposed directly with no gateway or load balancer.

> Look for: `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*` in IaC; throttling and auth config on gateway.

### INF-Q7: Auto-Scaling

**Question:** Are auto-scaling mechanisms configured for compute workloads?

**Why it matters:** Without auto-scaling, workloads cannot respond to traffic spikes or scale down during low demand. This leads to either over-provisioning (cost waste) or under-provisioning (degraded experience).

- Score 4: All compute tiers have auto-scaling configured with appropriate min/max.
- Score 3: Auto-scaling on primary compute; some static capacity for auxiliary services.
- Score 2: Basic auto-scaling with default settings, not tuned for workload patterns.
- Score 1: No auto-scaling — all capacity is statically provisioned.

> Look for: `aws_autoscaling_*`, `aws_appautoscaling_*`; scaling policies; min/max capacity settings; Lambda concurrency limits.

### INF-Q8: Backup and Recovery

**Question:** Are automated backups configured for data stores with defined retention periods and tested restore procedures?

**Why it matters:** Without automated backups and tested restores, a data loss event can wipe application state and cause cascading failures. This is a foundational reliability requirement. (WAF: REL 9)

- Score 4: All production data stores have automated backups with defined retention; PITR enabled where supported; restore procedures documented or tested.
- Score 3: Automated backups configured but missing PITR or missing on some data stores; no documented restore testing.
- Score 2: Backups on primary database only; no backup plans for other data stores; no restore testing.
- Score 1: No backup configuration found; or backup_retention_period = 0.

> Look for: `backup_retention_period` on RDS; `point_in_time_recovery` on DynamoDB; `aws_backup_plan` resources; S3 versioning; EBS snapshot lifecycle policies.

### INF-Q9: High Availability and Fault Isolation

**Question:** Are production workloads deployed across multiple Availability Zones with fault isolation?

**Why it matters:** Single-AZ production deployments are one of the most common high-risk issues. An AZ failure takes down the entire workload with no automatic recovery. Multi-AZ ensures survivability without human intervention. (WAF: REL 10, REL 11)

- Score 4: All production compute and data stores span 2+ AZs; load balancers with cross-zone enabled.
- Score 3: Primary database is Multi-AZ but some compute or caches are single-AZ.
- Score 2: Database is single-AZ; compute spans multiple AZs but no explicit fault isolation.
- Score 1: All resources in a single AZ; or no AZ configuration found.

> Look for: `multi_az = true` on RDS; `availability_zones` spanning 2+ AZs in ASGs/ECS; subnet configurations across multiple AZs.


---

## 02 — Application Architecture

These questions evaluate the application's structural maturity, decomposition readiness, and communication patterns.

### INF-Q10: Infrastructure as Code Coverage

**Question:** What percentage of infrastructure is defined in IaC vs manually created?

**Why it matters:** Low IaC coverage means infrastructure changes are manual, error-prone, and non-reproducible. IaC is the foundation for automated deployments, environment consistency, and disaster recovery.

- Score 4: 90%+ of infrastructure defined in IaC (compute, networking, databases, messaging).
- Score 3: 70-90% IaC coverage — primary resources covered, some auxiliary resources manual.
- Score 2: Partial IaC — some resources defined, but significant manual infrastructure.
- Score 1: No IaC — all infrastructure created manually (ClickOps).

> Look for: Presence and coverage of .tf files, CDK stacks, CloudFormation templates, Helm charts. Check whether IaC covers compute, networking, databases, and messaging.

### INF-Q11: CI/CD Automation

**Question:** Are CI/CD pipelines automated with build, test, and deploy stages, or are deployments manual?

**Why it matters:** Manual deployments create bottlenecks, are error-prone, and prevent rapid iteration. Automated pipelines enable continuous delivery with consistent quality gates.

- Score 4: Full CI/CD automation with test, build, and deploy stages including automated rollback.
- Score 3: CI/CD pipeline exists with build and deploy, but limited automated testing.
- Score 2: Partial automation — build is automated but deployment is manual or semi-manual.
- Score 1: No CI/CD — all deployments are manual scripts or ClickOps.

> Look for: .github/workflows/, buildspec.yml, Jenkinsfile, CodePipeline definitions in IaC; pipeline stages with automated test, build, and deploy steps.

### APP-Q1: Programming Languages

**Question:** What programming languages are used and how mature is their ecosystem for cloud-native development?

**Why it matters:** Language choice affects framework availability, community support, hiring, and modernization options. Some languages have richer ecosystems for containers, serverless, and cloud-native patterns.

- Score 4: Python, TypeScript/JavaScript, Go, or Java/Kotlin — mature cloud-native ecosystems.
- Score 3: .NET, Ruby, or Rust — solid ecosystems with some gaps.
- Score 2: PHP, Perl, or older Java versions (< 11) — functional but limited modern tooling.
- Score 1: COBOL, VB6, Classic ASP, or legacy languages with minimal cloud-native support.

> Look for: File extensions; package.json, requirements.txt, pom.xml/build.gradle, go.mod, *.csproj.

### APP-Q2: Monolith vs Microservices

**Question:** Is the application a single deployable unit or multiple independently deployable services?

**Why it matters:** Monoliths limit independent scaling, deployment, and team autonomy. Understanding the current decomposition state and coupling level determines the modernization strategy — containerize as-is, strangler fig extraction, or full decomposition.

- Score 4: Microservices or modular monolith with well-defined module boundaries, no circular dependencies, clear interfaces.
- Score 3: Modular monolith with some coupling, or early-stage microservices with shared databases.
- Score 2: Monolith with identifiable modules but significant coupling (shared state, database coupling, circular dependencies).
- Score 1: Tightly-coupled monolith with no clear module boundaries, pervasive shared state.

> Look for: Single deployable vs multiple service directories; Helm charts for multiple services; Docker Compose with multiple services; IaC for multiple ECS tasks or Lambda functions. For monoliths: package/module structure, dependency graphs, circular dependencies, shared mutable state, database coupling.

### APP-Q3: Async vs Sync Communication

**Question:** What percentage of inter-service communication is asynchronous vs synchronous HTTP?

**Why it matters:** Synchronous-only architectures create tight coupling, cascading failures, and timeout risks. Async patterns enable decoupling, resilience, and better handling of variable-latency operations.

- Score 4: 50%+ async, or async available for all long-running operations.
- Score 3: Mix of async and sync with async for key workflows.
- Score 2: Primarily synchronous with some async for background jobs.
- Score 1: All communication is synchronous HTTP with no async patterns.

> Look for: HTTP client calls (axios, requests, RestTemplate, fetch) vs message publishing patterns; event-driven handlers; queue consumers.

### APP-Q4: Long-Running Process Handling

**Question:** Are operations over 30 seconds handled asynchronously with status polling or callbacks?

**Why it matters:** Blocking calls for long-running operations create timeout risks, poor user experience, and resource waste. Async patterns with status tracking enable better resource utilization and user feedback.

- Score 4: All operations over 30 seconds implemented as async jobs with status polling or callbacks.
- Score 3: Most long-running operations are async; some blocking calls remain.
- Score 2: Some background job processing but inconsistent patterns.
- Score 1: All operations are synchronous regardless of duration.

> Look for: Background job frameworks (Celery, Bull, SQS workers); async/polling patterns; job status APIs; Lambda async invocations; Step Functions for long processes.

### APP-Q5: API Versioning Strategy

**Question:** Is there a consistent API versioning strategy (URL paths, headers, query parameters)?

**Why it matters:** Without versioning, API changes break all consumers simultaneously. Versioning enables graceful migration and backward compatibility.

- Score 4: Consistent versioning strategy with backward compatibility guarantees.
- Score 3: Versioning present but inconsistent across endpoints.
- Score 2: Ad hoc versioning — some endpoints versioned, others not.
- Score 1: No versioning — breaking changes deployed directly.

> Look for: /v1/, /v2/ URL patterns; Accept-Version headers; versioning annotations; changelog files.

### APP-Q6: Service Discovery

**Question:** Is there a service registry, API catalog, or service mesh for service-to-service communication?

**Why it matters:** Hard-coded service endpoints create deployment coupling and make it difficult to scale, relocate, or replace services. Service discovery enables dynamic routing and decoupled deployments.

- Score 4: Service discovery mechanism present; no hard-coded service endpoints.
- Score 3: Partial service discovery — some services use discovery, others use hard-coded endpoints.
- Score 2: Environment variables for endpoints but no dynamic discovery.
- Score 1: All service endpoints hard-coded in application code or configuration.

> Look for: AWS Service Discovery, App Mesh, Istio, Consul; API Gateway as catalog; environment variables with hard-coded endpoints vs service discovery.


---

## 03 — Data Platform Modernization

These questions evaluate the data layer's modernization state — managed services, schema health, and migration readiness.

### DATA-Q1: Unstructured Data Storage

**Question:** Are documents and unstructured data stored in managed object storage (S3) with parsing capabilities (Textract, Tika)?

**Why it matters:** Unstructured data locked in file systems, local storage, or legacy document management systems is inaccessible for modern workloads. S3 with parsing pipelines enables search, analytics, and AI integration.

- Score 4: Unstructured data stored in S3 with parsing pipeline available.
- Score 3: Data in S3 but no automated parsing or extraction pipeline.
- Score 2: Data in managed storage but not S3 (EFS, EBS volumes) with limited accessibility.
- Score 1: Data on local file systems, legacy document management, or inaccessible storage.

> Look for: `aws_s3_bucket`; Textract calls; document parsing libraries; PDF/image processing.

### DATA-Q2: Unified Data Access Layer

**Question:** Is there a unified data access layer vs scattered database connections throughout the code?

**Why it matters:** Scattered data access means multiple integration points, inconsistent query patterns, and difficulty enforcing data contracts. A unified layer provides a single point of control for data access.

- Score 4: Unified data access layer; single point of data contract.
- Score 3: Mostly centralized with some direct access in auxiliary code paths.
- Score 2: Repository/DAO pattern in some modules but inconsistent across the codebase.
- Score 1: Database imports and queries scattered across many modules with no pattern.

> Look for: Centralized repository/DAO layer vs database imports spread across many modules; data access pattern consistency.

### DATA-Q3: Database Engine Version and EOL

**Question:** Does IaC or deployment configuration specify the database engine version, and have any engines approaching or past end-of-life (EOL) been identified?

**Why it matters:** EOL database engines introduce security vulnerabilities and lack modern features. Unversioned or implicitly-latest configurations are also a risk signal. Engine version awareness is a prerequisite for migration planning.

- Score 4: All database engine versions explicitly pinned in IaC; no engines at or past EOL.
- Score 3: Versions pinned but some approaching EOL within 12 months.
- Score 2: Some versions pinned, others implicit; EOL status unknown.
- Score 1: No version pinning; engines at or past EOL detected.

> Look for: Engine version parameters in `aws_rds_instance`, `aws_docdb_cluster`, `aws_elasticache_*`; engine version strings in docker-compose or Helm values; absence of explicit version pinning.

### DATA-Q4: Stored Procedures and Schema Complexity

**Question:** Does the application rely on stored procedures, triggers, or proprietary SQL constructs (e.g., T-SQL, PL/SQL)?

**Why it matters:** Stored procedures and proprietary SQL tightly couple business logic to the database engine, creating migration blockers. High stored procedure usage signals that database modernization will require significant effort beyond a lift-and-shift — logic extraction and schema refactoring become prerequisites.

- Score 4: No stored procedures or proprietary SQL; all business logic in application layer.
- Score 3: Minimal stored procedures for performance-critical operations only.
- Score 2: Moderate stored procedure usage with some proprietary SQL constructs.
- Score 1: Heavy reliance on stored procedures, triggers, and proprietary SQL across the application.

> Look for: `.sql` files containing `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION`; ORM bypass patterns (raw SQL execution); references to proprietary SQL dialects in migration files.


---

## 04 — Security Baseline

These questions evaluate the foundational security posture required for any modernization initiative.

### SEC-Q1: Audit Logging

**Question:** Is CloudTrail enabled with immutable logs?

**Why it matters:** Audit logging is a compliance and operational requirement for any production system. Immutable logs ensure that actions can be traced and forensic analysis is possible after incidents.

- Score 4: CloudTrail enabled with log file validation and immutable storage (S3 Object Lock).
- Score 3: CloudTrail enabled but without immutable storage or log validation.
- Score 2: Partial logging — some services logged, others not.
- Score 1: No CloudTrail or equivalent audit logging.

> Look for: `aws_cloudtrail` in IaC; CloudTrail log file validation enabled; S3 bucket with object lock for logs; CloudWatch log retention policies.

### SEC-Q2: Encryption at Rest

**Question:** Is KMS used for sensitive data at rest?

**Why it matters:** Encryption at rest is a baseline security requirement. Customer-managed KMS keys provide control over key rotation, access policies, and audit trails.

- Score 4: Customer-managed KMS keys for all sensitive data stores.
- Score 3: AWS-managed encryption enabled on most data stores.
- Score 2: Encryption enabled on some data stores but not all.
- Score 1: No encryption at rest configured.

> Look for: `kms_key_id` on S3/RDS/DynamoDB/EBS; `aws_kms_key` resources; encryption config on data stores.

### SEC-Q3: API Authentication

**Question:** Is there per-request authentication with OAuth2/JWT on all API endpoints?

**Why it matters:** Unauthenticated APIs are a security vulnerability. Per-request authentication ensures that every call is authorized and attributable.

- Score 4: Every API endpoint authenticated; OAuth2/JWT standard in use.
- Score 3: Most endpoints authenticated; some internal endpoints lack auth.
- Score 2: Basic authentication (API keys) without token-based auth.
- Score 1: No API authentication — endpoints are open.

> Look for: Auth middleware; API Gateway authorizers; Cognito user pools; OAuth2 flows; Bearer token validation; @Authenticated annotations.

### SEC-Q4: Centralized Identity Integration

**Question:** Does the application integrate with a centralized identity provider (Cognito, Okta, Ping), or does it manage its own authentication independently?

**Why it matters:** Applications with their own auth systems create inconsistency and increase attack surface. Detecting whether the app integrates with a centralized IdP signals modernization maturity. Apps with standalone auth are harder to integrate into unified access policies.

- Score 4: Application integrates with centralized IdP; SSO enabled.
- Score 3: Application uses centralized IdP for most flows; some legacy auth paths remain.
- Score 2: Application has its own auth but can federate with external IdPs.
- Score 1: Application manages its own authentication entirely with no external IdP integration.

> Look for: `aws_cognito_*`; OIDC/SAML configuration; identity provider federation; SSO configuration.

### SEC-Q5: Secrets Management

**Question:** Are secrets (database credentials, API keys, tokens) managed through a dedicated secrets management system (AWS Secrets Manager, HashiCorp Vault) with rotation, or are they hardcoded in code, environment variables, or configuration files?

**Why it matters:** Hardcoded secrets are a critical security vulnerability and a common finding in legacy applications. Secrets management with rotation and audit trails is a baseline security requirement for any production system, not just agentic workloads.

- Score 4: All secrets in Secrets Manager or Vault with automated rotation; no hardcoded credentials.
- Score 3: Most secrets managed; some legacy environment variables remain.
- Score 2: Mix of managed and hardcoded secrets; no rotation.
- Score 1: Secrets hardcoded in code or committed to version control.

> Look for: `aws_secretsmanager_*` in IaC; Vault client imports; hardcoded patterns (password=, secret=, api_key= in code); .env files committed to git.

### SEC-Q6: Compute Hardening and Patching

**Question:** Are compute resources hardened with managed patching and vulnerability scanning?

**Why it matters:** Unpatched compute resources are high-value targets. Managed patching and vulnerability scanning are baseline security requirements. (WAF: SEC 6)

- Score 4: SSM Patch Manager or equivalent configured; vulnerability scanning (Inspector/Snyk) enabled; hardened base images.
- Score 3: Some patching automation but not comprehensive; or vulnerability scanning present but not integrated into CI/CD.
- Score 2: Manual patching process; default AMIs with no hardening.
- Score 1: No evidence of patching strategy; no vulnerability scanning.

> Look for: SSM Agent in user-data; `aws_ssm_patch_baseline`; AWS Inspector or Snyk; hardened AMI references (CIS, Bottlerocket); EC2 Image Builder pipelines.

### SEC-Q7: Application Security Pipeline

**Question:** Are SAST, DAST, or dependency vulnerability scanning tools integrated into the CI/CD pipeline?

**Why it matters:** Without automated security scanning, vulnerabilities in dependencies or application code reach production undetected. Embedding security validation in the pipeline is a baseline practice. (WAF: SEC 11)

- Score 4: SAST + dependency scanning in CI/CD with security gates blocking on critical findings; container scanning if applicable.
- Score 3: At least one scanning tool in CI/CD but missing container scanning or no blocking gate.
- Score 2: Dependency scanning configured (e.g., Dependabot) but no SAST; or scanning not integrated into pipeline.
- Score 1: No security scanning in CI/CD pipeline.

> Look for: SonarQube, Semgrep, CodeGuru Reviewer in CI/CD; Dependabot config; `npm audit` or `pip-audit` in pipeline; ECR image scanning; `.snyk` policy files.

---

## 05 — Operations & Observability

These questions evaluate the operational maturity and observability practices that support reliable, evolvable systems.

### OPS-Q1: Distributed Tracing

**Question:** Is distributed tracing (X-Ray, OpenTelemetry, or partner solution) instrumented with trace ID propagation across service boundaries?

**Why it matters:** Without end-to-end tracing, debugging failures across service boundaries is guesswork. Distributed tracing is foundational for understanding request flows, identifying bottlenecks, and diagnosing production issues in any distributed system.

- Score 4: End-to-end distributed tracing with propagated trace IDs across all service boundaries.
- Score 3: Tracing on primary services; some gaps in propagation.
- Score 2: Basic tracing on individual services but no cross-service propagation.
- Score 1: No distributed tracing instrumented.

> Look for: OpenTelemetry SDK in dependency manifests, X-Ray instrumentation, traceparent/X-Amzn-Trace-Id header propagation.

### OPS-Q2: SLO Definitions

**Question:** Are SLOs defined for critical user journeys?

**Why it matters:** Without SLOs, you cannot measure whether the system is meeting user expectations or degrading over time. SLOs drive prioritization of operational improvements and modernization investments.

- Score 4: SLOs defined and monitored for all critical user-facing journeys with error budgets.
- Score 3: SLOs defined for primary journeys; monitoring in place but no error budget tracking.
- Score 2: Basic availability/latency alarms but no formal SLO definitions.
- Score 1: No SLOs — no formal definition of acceptable service levels.

> Look for: SLO definitions in code or config; CloudWatch alarms on p99/p95 latency; error budget tracking; SLO dashboards.

### OPS-Q3: Business Metrics

**Question:** Are custom metrics published for business outcomes, not just infrastructure metrics?

**Why it matters:** Infrastructure metrics (CPU, memory) tell you if the system is running, not if it's delivering value. Business metrics (conversion rates, resolution times, error rates by feature) drive informed modernization decisions.

- Score 4: Business outcome metrics published alongside infrastructure metrics with dashboards.
- Score 3: Some business metrics tracked but not systematically across all features.
- Score 2: Infrastructure metrics only with ad hoc business reporting.
- Score 1: No custom metrics — only default CloudWatch infrastructure metrics.

> Look for: `cloudwatch.put_metric_data` for business events; custom dashboards; business KPI alarms.

### OPS-Q4: Anomaly Detection and Alerting

**Question:** Is there anomaly detection or alerting on error rates and latency?

**Why it matters:** Static threshold-based alerting misses gradual degradation and novel failure modes. Anomaly detection catches unexpected behavior patterns that fixed thresholds cannot.

- Score 4: Anomaly detection enabled on error rates and latency for all critical paths.
- Score 3: Anomaly detection on primary paths; static thresholds on secondary paths.
- Score 2: Static threshold alarms only (e.g., CPU > 80%, error rate > 5%).
- Score 1: No alerting configured.

> Look for: CloudWatch anomaly detection; error rate alarms; latency p99 alarms; PagerDuty/OpsGenie integration; composite alarms.

### OPS-Q5: Deployment Strategy

**Question:** Is the deployment strategy blue/green, canary, or straight to production?

**Why it matters:** Direct-to-production deployments with no staged rollout eliminate the window to catch regressions before they affect all users. Canary and blue/green deployments enable safe, incremental releases.

- Score 4: Canary or blue/green deployments; no direct-to-production releases.
- Score 3: Blue/green for primary services; direct deployment for auxiliary services.
- Score 2: Rolling deployments with basic health checks but no traffic shifting.
- Score 1: Direct-to-production deployment with no staged rollout.

> Look for: CodeDeploy deployment config; Helm canary; Argo Rollouts; Lambda traffic shifting; ALB weighted target groups; feature flags.

### OPS-Q6: Integration Testing

**Question:** Are there integration tests for critical workflows that run in the CI pipeline?

**Why it matters:** Unit tests alone don't catch integration failures — broken API contracts, database schema drift, or misconfigured infrastructure. Integration tests validate that the system works end-to-end.

- Score 4: Integration test suites covering all critical workflows, run in CI pipeline.
- Score 3: Integration tests for primary workflows; some gaps in coverage.
- Score 2: Some integration tests but not run consistently in CI.
- Score 1: No integration tests — only unit tests or no automated tests at all.

> Look for: Integration test directories; test containers; pytest-integration; API test suites (Postman/Newman); contract tests; end-to-end test pipelines in CI.

### OPS-Q7: Incident Response Automation

**Question:** Are incident response workflows automated, and do runbooks exist in machine-readable or structured form?

**Why it matters:** Manual incident response is slow and error-prone. Automated runbooks and self-healing patterns reduce mean-time-to-recovery and free teams to focus on prevention rather than firefighting.

- Score 4: Self-healing automation resolves a defined class of incidents without human intervention; runbooks are versioned and machine-readable.
- Score 3: Automated runbooks for common incidents; manual escalation for complex ones.
- Score 2: Runbooks exist as documentation but are not automated.
- Score 1: No runbooks — incident response is entirely ad hoc.

> Look for: Runbook files (markdown, YAML, JSON); Systems Manager Automation documents; Lambda-based remediation; Step Functions for incident workflows; self-healing patterns.

### OPS-Q8: Observability Ownership

**Question:** Does the application have defined observability ownership — service-level dashboards, alarms with named owners, and SLO definitions tied to specific teams?

**Why it matters:** Without clear ownership of observability assets, monitoring gaps emerge. Detecting whether the repo has CODEOWNERS for observability configs, named alarm owners, or team-specific dashboards signals operational maturity.

- Score 4: Per-service dashboards and alarms with named owners; SLO definitions with team attribution.
- Score 3: Dashboards and alarms exist for most services; some gaps in ownership attribution.
- Score 2: Ad hoc observability — alarms exist but no clear ownership or team attribution.
- Score 1: No observability ownership — monitoring is reactive and fragmented.

> Look for: SLO definition files with named owners; CODEOWNERS referencing observability assets; per-service dashboards and alarms; team tags on CloudWatch resources.

### OPS-Q9: Resource Tagging Governance

**Question:** Are AWS resources consistently tagged for cost allocation, ownership, and environment identification?

**Why it matters:** Without consistent tagging, organizations cannot track costs per workload, identify resource ownership during incidents, or enforce budget controls. Tagging is foundational to cloud financial management and blast radius analysis. (WAF: COST 1-3)

- Score 4: All resources tagged with consistent keys; tag enforcement via Config rules or SCPs; cost allocation tags activated.
- Score 3: Most resources tagged but inconsistent key naming or missing on some resource types; no enforcement.
- Score 2: Some resources tagged but many untagged; no tagging standard.
- Score 1: No tags found on resources; or only Name tags with no cost/ownership attribution.

> Look for: `default_tags` in Terraform provider; `tags` on resources; `required-tags` Config rules; tag policies in AWS Organizations.


---

## 06 — AWS Modernization Pathways

Based on assessment scores, the following AWS Modernization Pathways can be evaluated for applicability. Multiple pathways can apply simultaneously.

### Move to Cloud Native (Containers and Serverless)

**Trigger conditions:**
- APP-Q2 < 3 (monolith or tightly coupled) — primary trigger
- INF-Q1 < 3 (EC2-heavy compute)
- APP-Q3 < 3 (sync-heavy communication)
- APP-Q4 < 3 (no async for long-running operations)

**Focus:** Decompose monolith applications into loosely coupled distributed architectures using microservices.
**Representative AWS Services:** Lambda, API Gateway, Step Functions, EventBridge.

### Move to Containers

**Trigger conditions:**
- INF-Q1 < 3 (no managed container orchestration or serverless) — contextual guard: must be EC2/VM-based
- No Dockerfile or container definitions found in discovery

**Focus:** Containerize existing workloads and adopt fully managed container orchestration.
**Representative AWS Services:** ECS, EKS, Fargate, ECR.

### Move to Open Source

**Trigger conditions:**
- DATA-Q4 < 3 (proprietary SQL/stored procedures detected)
- INF-Q2 findings mention commercial database engines (Oracle, SQL Server)

**Focus:** Move away from commercial workloads/licenses to open source.
**Representative AWS Services:** RDS open source engines (PostgreSQL, MySQL, MariaDB), EKS, Amazon Linux.

### Move to Managed Databases

**Trigger conditions:**
- INF-Q2 < 3 (self-managed databases detected)
- DATA-Q3 < 3 (EOL or unpinned database engine versions)

**Focus:** Adopt fully managed purpose-built cloud native databases.
**Representative AWS Services:** Aurora, RDS, DynamoDB, DocumentDB, ElastiCache, OpenSearch Service.

### Move to Managed Analytics

**Trigger conditions:**
- INF-Q4 < 3 (self-managed streaming detected) — contextual guard: evidence of data processing workloads must exist
- Data source sprawl with no unified access layer

**Focus:** Adopt fully managed, cost-optimized data lake and real-time analytics.
**Representative AWS Services:** Redshift, Kinesis, MSK Serverless, Athena, Lake Formation.

### Move to Modern DevOps

**Trigger conditions:**
- INF-Q10 < 3 (low IaC coverage)
- INF-Q11 < 3 (no CI/CD automation)
- OPS-Q5 < 3 (no canary/blue-green deployments)
- OPS-Q6 < 3 (no integration tests)

**Focus:** Adopt modern philosophies, practices, and tools for high-velocity application delivery.
**Representative AWS Services:** CodeCommit, CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK, X-Ray, CloudWatch.

### Move to AI

**Trigger conditions:**
- APP-Q1 findings show no AI/agent framework usage (no Bedrock, LangChain, Strands, OpenAI, Spring AI imports)
- No vector database or embeddings infrastructure detected
- No RAG implementation detected
- No agent evaluation framework detected

**Contextual guard:** None — in the context of modernization, AI readiness is universally relevant as organizations prepare for agentic workloads.

**Focus:** Leverage AWS AI services to transform applications with AI capabilities, bridging traditional modernization and AI-driven computing.
**Representative AWS Services:** Amazon Bedrock, Amazon Bedrock AgentCore, Amazon Q, SageMaker.

---

## Quick Agent Wins

Based on the assessment findings, identify agent opportunities that the current architecture can support. Only include wins where the system has enough foundation — these are not aspirational, they're actionable now.

| Condition Found | Suggested Agent Win |
|----------------|---------------------|
| API docs exist (APP-Q5 >= 2) and structured JSON responses | API-aware agent that discovers and invokes existing endpoints as tools |
| Database with clear, documented schema (DATA-Q2 >= 2) | Data query agent with natural language to SQL |
| CI/CD pipeline exists (INF-Q11 >= 2) | DevOps agent that triggers deployments, checks build status, and manages releases |
| Documentation, README, or wiki content exists in repo | RAG-based knowledge agent using existing documentation as a knowledge base |
| Workflow orchestration in place (INF-Q3 >= 2) | Workflow automation agent that monitors and manages existing Step Functions or orchestration workflows |
| Structured logging and tracing in place (OPS-Q1 >= 2) | Observability agent that queries logs, traces incidents, and suggests root causes |

These wins can be pursued in parallel with the modernization roadmap. They demonstrate agent value early while foundations are being improved.

---

## 07 — AWS Programs and Engagement Recommendations

These program recommendations apply at the portfolio level. Individual repo assessments surface the findings; the portfolio aggregation determines which programs are relevant.

| Program | Acronym | Trigger Condition |
|---------|---------|-------------------|
| Migration Acceleration Program | MAP | Portfolio has 3+ repos with overall score < 2.5 |
| Optimization and Licensing Assessment | OLA | Any repo has Oracle, SQL Server, VMware, or commercial license findings |
| Microsoft Modernization Program | MMP | Any repo has .NET or Windows workloads detected |
| VMware Modernization Program | VMP | Any repo has VMware references in IaC or deployment configs |
| Windows App Modernization Program | WAMP | Any repo has Windows-based deployment targets |
| Experience-Based Acceleration | EBA | Each triggered pathway = potential EBA engagement |
| ISV Workload Migration Program | ISV WMP | Portfolio is an ISV SaaS platform being modernized |
| Cloud Economics | CE | Portfolio has significant licensing costs or cost optimization is a priority |

Each triggered pathway can map to a separate EBA engagement. Programs can overlap — a portfolio may qualify for MAP, OLA, and multiple EBAs simultaneously.

---

## 08 — Recommended Learning Materials

Include relevant links based on triggered pathways:

- **Move to Cloud Native:** [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Move to Containers:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/)
- **Move to Open Source:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) (covers open source engine migration)
- **Move to Managed Databases:** [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- **Move to Managed Analytics:** [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV)
- **Move to Modern DevOps:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- **Move to AI:** [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Scoring and Roadmap

### Category Scores

Calculate each category average as the arithmetic mean of all question scores in that category:

| Category | Questions | Count |
|----------|-----------|-------|
| Infrastructure, Platform, and DevOps | INF-Q1 through INF-Q11 | 11 |
| Application Architecture | APP-Q1 through APP-Q6 | 6 |
| Data Platform Modernization | DATA-Q1 through DATA-Q4 | 4 |
| Security Baseline | SEC-Q1 through SEC-Q7 | 7 |
| Operations & Observability | OPS-Q1 through OPS-Q9 | 9 |

**Overall Score** = average of the 5 category scores (each category weighted equally regardless of question count).

**Important:** The overall score is a summary indicator, not a decision tool. A system scoring 4.0 in Infrastructure but 1.0 in Security is not "2.5 — Partial." Always review category scores individually. A single category below 2.0 signals a critical gap regardless of the overall score.

### How to Read the Scores

| Score Range | What It Means | What to Do |
|-------------|---------------|------------|
| 3.5 – 4.0 | Well-architected for this dimension. | Maintain. Optimize. No modernization needed here. |
| 2.5 – 3.4 | Functional with gaps. | Targeted improvements. Address specific low-scoring questions. |
| 1.5 – 2.4 | Significant gaps. | Structured remediation needed. Check which pathways are triggered. |
| < 1.5 | Missing or fundamentally inadequate. | Major investment required. This dimension blocks modernization progress. |

These ranges apply per category, not just overall. The pathway triggers (Section 06) translate low scores into specific modernization actions — use them to build the roadmap rather than following a generic phased template.

---

## Summary of Questions by Section

| Section | Questions | Count |
|---------|-----------|-------|
| 01 — Infrastructure, Platform, and DevOps | INF-Q1 through INF-Q11 | 11 |
| 02 — Application Architecture | APP-Q1 through APP-Q6 | 6 |
| 03 — Data Platform Modernization | DATA-Q1 through DATA-Q4 | 4 |
| 04 — Security Baseline | SEC-Q1 through SEC-Q7 | 7 |
| 05 — Operations & Observability | OPS-Q1 through OPS-Q9 | 9 |
| **Total** | | **37** |

