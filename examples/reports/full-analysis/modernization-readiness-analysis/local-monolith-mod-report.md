# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | monolith |
| **Date** | 2026-05-18 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P0 |
| **Tags** | monolith, php, containers |
| **Context** | PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions. |
| **Overall Score** | 1.82 / 4.0 |

**Archetype Justification**: Application owns persistent state (MySQL/RDS database with 9 tables), exposes CRUD operations on business entities (orders, inventory, payments, returns, users), and manages entity lifecycle (order status transitions). Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true, has_iac_provisioning_aws_resources=true

---

## Classification

**Tier: 🟠 Remediation Required**

This repo has 5 High findings, 22 Medium findings, 5 Low findings. Rule matched: "2-11 High → Remediation Required."

MOD classification note: MOD's "1 High" maps to Pilot-Ready (a single modernization gap), unlike ARA where "1 High" is a deployment blocker for agent safety. MOD measures modernization maturity — High findings represent significant modernization gaps requiring remediation before the system can be considered cloud-native ready.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 2.64 / 4.0 | 🟡 Partial | Critical |
| Application Architecture (APP) | 1.33 / 4.0 | ❌ Not Ready | Critical |
| Data Platform (DATA) | 2.25 / 4.0 | 🟠 Needs Work | Critical |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.82 / 4.0** | **🟠 Needs Work** | — |

### Scoring Notes

- INF: (4+4+2+1+3+2+2+3+4+3+1) / 11 = 29/11 = 2.64
- APP: (2+1+1+1+1+2) / 6 = 8/6 = 1.33
- DATA: (1+1+3+4) / 4 = 9/4 = 2.25
- SEC: (3+2+1+1+2+1) / 6 = 10/6 = 1.67 (SEC-Q1 excluded — Not Evaluated)
- OPS: (1+1+1+1+2+1+1+1+2) / 9 = 11/9 = 1.22
- Overall: (2.64+1.33+2.25+1.67+1.22) / 5 = 9.11/5 = 1.82

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith — 3192 lines in single PHP file, all business domains sharing one database with no module boundaries | Blocks independent scaling, deployment, and team autonomy; triggers Move to Cloud Native pathway |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — deployment is a manual bash script (deploy.sh) | Manual deployments are error-prone, slow, and prevent rapid iteration; triggers Move to Modern DevOps pathway |
| 3 | SEC-Q5: Secrets Management | 1 | Plaintext fallback credentials in source code (`'ecommerce_pass'` default in get_db()), seed passwords in code | Critical security vulnerability — credentials exposed in version control |
| 4 | OPS-Q6: Integration Testing | 1 | No test files found anywhere in the repository — no unit tests, no integration tests | Zero regression safety net; any change risks breaking production |
| 5 | DATA-Q1: Unstructured Data Storage | 1 | No managed object storage; product images referenced as filesystem paths with no S3 or parsing pipeline | Unstructured data locked in inaccessible storage; no path to AI/analytics integration |

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 < 3 (primary); APP-Q3=1 < 3, APP-Q4=1 < 3 (supporting) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=4 — compute already runs on App Runner (managed containerized service) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 — no stored procedures; MySQL is already open source |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2=4 — database already on RDS (fully managed) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4=1 < 3 but contextual guard blocks: no data processing workloads exist (simple CRUD e-commerce app) |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q11=1 < 3 (primary); OPS-Q5=2 < 3, OPS-Q6=1 < 3 (supporting) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a tightly-coupled monolith (APP-Q2=1) — a single 3192-line PHP file containing all business domains (orders, inventory, payments, returns, shipping, user management, customer interactions) with pervasive shared state through a single MySQL database. There are no module boundaries, no separation of concerns, and all 9 tables are directly accessed throughout the codebase.

**Communication Pattern Gaps:**
- APP-Q3=1: All operations are synchronous within the monolith. No async patterns exist for cross-domain state propagation (e.g., order confirmed → inventory reserved → payment processed → shipment initiated).
- APP-Q4=1: No async job processing. All operations execute synchronously within the HTTP request cycle.

**Recommended Decomposition Approach:**
Given the tightly-coupled nature (Score 1) and the user's preference for EKS, the recommended path is **Strangler Fig (Parallel Track)** — incrementally extract services starting with the inventory domain (needed for agent restocking decisions per the context). See Decomposition Strategy section below.

**Representative AWS Services (aligned with preferences):**
- **Amazon EKS** (preferred) for container orchestration of extracted microservices
- **Amazon API Gateway** (preferred) for unified API entry point with throttling and auth
- **Amazon EventBridge** (preferred) for event-driven communication between services
- **AWS Step Functions** for order workflow orchestration
- **Amazon Aurora** (preferred) for per-service databases after data separation

**Recommended Patterns:**
- Strangler Fig pattern for incremental extraction
- Anti-corruption Layer between monolith and new services
- Saga pattern for distributed order transactions
- Hexagonal Architecture for each new service

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current CI/CD State (INF-Q11=1):**
No CI/CD pipeline exists. Deployment is a manual bash script (`deploy.sh`) that runs `docker-compose build` and `docker-compose up`. AWS deployment follows manual CloudFormation instructions (build image, push to ECR, update stack via CLI).

**IaC Coverage (INF-Q10=3):**
CloudFormation covers primary infrastructure (VPC, RDS, App Runner, WAF, ECR, IAM) but lacks monitoring alarms, backup plans beyond RDS defaults, and operational resources.

**Deployment Strategy Gaps (OPS-Q5=2):**
App Runner provides basic rolling deployments with health checks, but no canary or blue/green traffic shifting is configured. No rollback automation.

**Testing Gaps (OPS-Q6=1):**
Zero automated tests — no unit tests, no integration tests, no contract tests. Any deployment carries full regression risk.

**Recommended DevOps Toolchain (aligned with preferences):**
- **Terraform** (preferred over CloudFormation) for IaC with GitOps workflow
- **GitHub Actions** or **AWS CodePipeline** for CI/CD automation
- **ArgoCD/FluxCD** (GitOps preferred) for deployment orchestration to EKS
- **AWS CodeBuild** for container image builds
- **Amazon ECR** (already in use) for container registry with scan-on-push

**Immediate Actions:**
1. Create CI/CD pipeline with build, test, and deploy stages
2. Add automated testing (start with integration tests for critical API endpoints)
3. Migrate IaC to Terraform with remote state and GitOps workflow
4. Implement canary or blue/green deployment strategy
5. Add security scanning (SAST + dependency scanning) to pipeline

**AWS Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)

---

## Decomposition Strategy

### Recommended Approach: Strangler Fig (Parallel Track)

Given APP-Q2=1 (tightly-coupled monolith with no module boundaries), the recommended approach is **Strangler Fig** — incrementally extract services while keeping the monolith running.

**Why Strangler Fig over other approaches:**
- The monolith is functional and deployed (App Runner + RDS) — no need for big-bang rewrite
- The context explicitly calls for "exposing inventory APIs the agent needs for restocking decisions" — this is a natural first extraction candidate
- The team preference for EKS + Terraform + GitOps aligns with incremental service extraction
- Risk is minimized: each extraction is bounded, and the monolith continues serving traffic during migration

### Approach Options

| Approach | Level of Effort | Recommendation |
|----------|-----------------|----------------|
| **Strengthen as Modular Monolith** | Low (2-6 months) | Not recommended — Score 1 indicates no module boundaries exist to strengthen, and the context requires independent API services |
| **Strangler Fig (Parallel Track)** | Medium to High (6-18 months) | ✅ **Recommended** — Extract inventory service first (context-driven), then orders, payments |
| **Conditional / Adaptive** | Low to Medium | Viable alternative — containerize as-is (already done), then selectively extract high-value services |
| **Big-Bang Rewrite** | Very High (12-24+ months) | ⚠️ **Not recommended** — High risk; the monolith is functional |

### Extraction Order (Priority-Driven)

1. **Inventory Service** (first) — Required for agent restocking decisions per context
2. **Orders Service** — Core business domain with clear entity boundaries
3. **Payments Service** — Separate compliance/security concerns
4. **Returns Service** — Independent lifecycle
5. **User/Auth Service** — Cross-cutting concern, extract last

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate new services from monolith data model | Every extraction — translate between monolith SQL and new service APIs |
| **Saga Pattern** | Distributed transactions (order → payment → inventory) | When extracting orders+payments — replace single DB transaction with orchestrated saga |
| **Event Sourcing** | Capture state changes as events | Inventory updates, order status changes — enables EventBridge integration |
| **Hexagonal Architecture** | Clean service boundaries | Every new service — ports/adapters for testability and portability |

### Effort Estimation Factors

| Factor | Current State | Effort Impact |
|--------|--------------|---------------|
| Module boundaries | None (Score 1) — all domains in one file | High effort to identify and separate concerns |
| Data coupling | Single shared database, all 9 tables accessed throughout | High effort — requires per-service database extraction |
| Stored procedures | None (Score 4) | Low effort — no database logic to extract |
| Communication patterns | All synchronous (Score 1) | Medium effort — need to introduce EventBridge |
| CI/CD maturity | None (Score 1) | Must build pipeline first before multi-service deployment |
| Test coverage | Zero tests (Score 1) | High risk during extraction — must add tests as guardrails |

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | Application runs on AWS App Runner, a fully managed containerized compute service. Auto-scaling configured (1-3 instances, MaxConcurrency: 100). No EC2 instances. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AWS::AppRunner::Service`, `AWS::AppRunner::AutoScalingConfiguration` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | Database is Amazon RDS MySQL 8.4.8 with Multi-AZ, encrypted storage, IAM authentication, enhanced monitoring, automated backups (7-day retention), and deletion protection. Fully managed with automated failover. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AWS::RDS::DBInstance` with `MultiAZ: true`, `StorageEncrypted: true`, `EnableIAMDatabaseAuthentication: true` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | Multi-step business operations (order creation: inventory check → order insert → items insert → payment → status update) are implemented as database transactions in application code. No dedicated workflow orchestration service. Archetype: stateful-crud — for within-DB transactions this is acceptable, but the order fulfillment lifecycle (pending → confirmed → shipped → delivered) is a hardcoded state machine with no visibility or error recovery. |
| **Gap** | Order fulfillment workflow is a simple state machine in code with basic structure (DB transactions) but no dedicated orchestration service for the multi-step lifecycle. |
| **Recommendation** | When decomposing the monolith, introduce AWS Step Functions for the order fulfillment workflow (order → payment → inventory reservation → shipping). This becomes critical once services are separated and single-DB transactions are no longer possible. |
| **Evidence** | `index.php` — `update_order_status()` function, order creation with `$db->beginTransaction()` / `$db->commit()` |

*Archetype calibration applied: stateful-crud. Within-database transactions are acceptable for single-service CRUD, but the absence of any orchestration for the multi-step order lifecycle (which includes external concerns like shipping) scores 2.*

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No messaging or streaming infrastructure exists. All operations are synchronous within the monolith. No SQS, SNS, EventBridge, or any message broker. State changes (order placed, payment processed, inventory updated, shipment initiated) all happen synchronously within HTTP request cycles. |
| **Gap** | No messaging where state changes cross domain boundaries. The monolith's domains (orders, inventory, payments, shipping) are tightly coupled through synchronous in-process calls. Upon decomposition, these will become cross-service boundaries requiring async decoupling. |
| **Recommendation** | Introduce Amazon EventBridge (preferred per context) for domain event publishing when decomposing the monolith. Start with inventory-level-changed events (needed for agent restocking decisions) and order-status-changed events. |
| **Evidence** | No `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*` in IaC. No message queue imports in source. All domain interactions are direct function calls in `index.php`. |

*Archetype calibration applied: stateful-crud. Score 1 reflects genuine gap — cross-domain state changes (order affects inventory, payment, shipping) have no async path.*

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Priority** | P1 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | Services deployed in a custom VPC with private subnets. RDS in private subnets accessible only from App Runner security group on non-default port (3307). App Runner connects via VPC Connector with scoped egress rules. Least-privilege security groups with explicit descriptions. VPC Flow Logs enabled with KMS encryption. |
| **Gap** | No managed networking services (VPC endpoints, PrivateLink, VPC Lattice). The HTTPS egress rule on the DB security group uses 0.0.0.0/0 (broad, though only port 443). |
| **Recommendation** | Add VPC endpoints for AWS services (ECR, CloudWatch Logs, Secrets Manager) to eliminate internet-bound traffic for AWS API calls. Consider VPC Lattice for service-to-service communication as microservices are extracted. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AWS::EC2::VPC`, `PrivateSubnet1`, `PrivateSubnet2`, `DBSecurityGroup` (ingress only from `AppRunnerSecurityGroup`), `VPCFlowLog` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | WAF Web ACL is associated with the App Runner service, providing IP whitelisting and Log4j exploit protection. App Runner provides a built-in HTTPS endpoint with health checks. However, there is no API Gateway with request validation, throttling policies, or usage plans. |
| **Gap** | No dedicated API Gateway with per-route throttling, request validation, or usage plans. WAF provides basic protection but not API management capabilities. |
| **Recommendation** | Deploy Amazon API Gateway (preferred per context) in front of the application to provide throttling, request validation, API keys/usage plans, and request/response transformation. This becomes essential when exposing inventory APIs for agent consumption. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AWS::WAFv2::WebACL`, `AWS::WAFv2::WebACLAssociation`. No `AWS::ApiGateway::*` or `AWS::ApiGatewayV2::*` resources. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | App Runner auto-scaling configured with min=1, max=3 instances, MaxConcurrency=100. Basic concurrency-based scaling. No auto-scaling on the database layer (fixed db.t3.micro). No custom scaling policies or business-metric-driven scaling. |
| **Gap** | Auto-scaling exists but uses only default/out-of-box App Runner settings. No scaling on the data layer. Database is a fixed db.t3.micro that cannot scale with traffic. No custom scaling policies. |
| **Recommendation** | Consider migrating to Aurora MySQL (preferred) which supports auto-scaling read replicas. If remaining on RDS, evaluate instance class scaling for production load. Add CloudWatch custom metrics (requests-per-second, queue depth) for more intelligent compute scaling when services are extracted to EKS. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AWS::AppRunner::AutoScalingConfiguration` (MinSize: 1, MaxSize: 3, MaxConcurrency: 100). `DBInstanceClass: db.t3.micro` with no scaling configuration. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | RDS has automated backups with 7-day retention, preferred backup window (03:00-04:00 UTC), and deletion protection. PITR is implicitly enabled (BackupRetentionPeriod > 0 enables PITR on RDS). DeletionPolicy: Snapshot ensures a final snapshot on deletion. |
| **Gap** | No documented restore testing procedures. No cross-region backup replication. No AWS Backup plan for centralized backup management. |
| **Recommendation** | Add an AWS Backup plan in IaC for centralized backup governance. Document and periodically test restore procedures. Consider cross-region backup replication for disaster recovery. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `BackupRetentionPeriod: 7`, `PreferredBackupWindow: '03:00-04:00'`, `DeletionPolicy: Snapshot`, `DeletionProtection: true` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | RDS MySQL is Multi-AZ (`MultiAZ: true`). App Runner is inherently multi-AZ (AWS-managed, distributes across AZs automatically). VPC spans 2 AZs with private subnets in each. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `MultiAZ: true` on DBInstance; `PrivateSubnet1` in AZ[0], `PrivateSubnet2` in AZ[1]; App Runner is multi-AZ by design. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | CloudFormation template covers: VPC, subnets, security groups, RDS, ECR, App Runner, WAF, IAM roles, KMS keys, VPC Flow Logs, auto-scaling. Primary infrastructure is well-defined in IaC. |
| **Gap** | No CloudWatch alarms, no SNS topics for notifications, no Route 53 health checks, no AWS Backup plans, no Secrets Manager resources. Monitoring and operational resources are not in IaC. |
| **Recommendation** | Migrate to Terraform (preferred per context) and extend IaC coverage to include CloudWatch alarms, Secrets Manager for credentials, AWS Backup plans, and Route 53 health checks. Adopt a GitOps workflow (preferred) for IaC changes. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — comprehensive resource coverage for compute/networking/database/security. Absence of `AWS::CloudWatch::Alarm`, `AWS::SNS::Topic`, `AWS::SecretsManager::Secret`, `AWS::Backup::BackupPlan`. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | No CI/CD pipeline exists. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline definition. Deployment is a manual bash script (`deploy.sh`) that runs `docker-compose build && docker-compose up`. AWS deployment follows manual CLI instructions documented in CloudFormation outputs. |
| **Gap** | All deployments are manual. No automated build, test, or deploy stages. No automated rollback. No pipeline for IaC changes. |
| **Recommendation** | Implement CI/CD immediately. Given preferences for GitOps and Terraform: (1) Create GitHub Actions pipeline with build/test/deploy stages, (2) Add Terraform CI with plan/apply workflow, (3) Integrate ArgoCD for EKS deployments as services are extracted. This is the highest-priority DevOps gap. |
| **Evidence** | `deploy.sh` — manual bash script. No CI/CD configuration files found. CloudFormation `DeploymentInstructions` output contains manual CLI steps. |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | High |
| **Phase** | 3 |
| **Finding** | PHP 8.2 on Apache. PHP has a functional AWS SDK but limited cloud-native tooling depth compared to languages like Go, Java, Python, or TypeScript. No Composer dependency management — all dependencies installed via apt-get in the Dockerfile. No framework (raw PHP with PDO). |
| **Gap** | PHP has narrower cloud-native tooling depth regardless of version. No dependency management (no Composer). No modern PHP framework (no Laravel, Symfony, etc.). |
| **Recommendation** | When extracting microservices, consider adopting languages with stronger cloud-native ecosystems for new services. For the inventory API (first extraction target), TypeScript/Node.js or Python would provide better AWS SDK integration, richer testing frameworks, and broader cloud-native tooling. Existing PHP code can remain for the monolith during Strangler Fig migration. |
| **Evidence** | `index.php` — PHP 8.2 source. `Dockerfile` — `FROM php:8.2-apache`. No `composer.json` found. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | High |
| **Phase** | 1 |
| **Finding** | Tightly-coupled monolith. Single 3192-line PHP file (`index.php`) contains ALL business domains: orders, inventory, payments, returns, shipping, user management, customer interactions. All 9 database tables are directly accessed throughout the file with inline SQL. No module boundaries, no separation of concerns, no dependency injection. All domains share a single database connection and execute within the same process. |
| **Gap** | No module boundaries whatsoever. All business logic, data access, routing, authentication, and UI rendering in one file. Shared mutable state through a single PDO connection. Circular dependencies between domains (order creation directly manipulates inventory, payments, and status history). |
| **Recommendation** | Begin Strangler Fig decomposition starting with the inventory domain (required for agent restocking decisions). Extract to an independent service on EKS (preferred) with its own database (Aurora MySQL preferred). See Decomposition Strategy section. |
| **Evidence** | `index.php` — 3192 lines, single file containing all routes (`/api/products`, `/api/orders`, `/api/returns`, `/api/admin/*`), all database DDL (9 tables), all business logic, full HTML/CSS/JS frontend. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | All operations are synchronous. Within the monolith, domain interactions (order creation triggers inventory update, payment processing, status history recording) are direct in-process function calls within a single HTTP request cycle. No async patterns, no event publishing, no message queues. |
| **Gap** | All communication synchronous with no async patterns. When decomposed, order-creation flow (check inventory → create order → process payment → update inventory → record status) will require async decoupling to avoid cascading failures and timeout amplification across service boundaries. |
| **Recommendation** | Introduce Amazon EventBridge (preferred) for domain event publishing as services are extracted. Start with: `inventory.stock-level-changed`, `order.status-changed`, `payment.completed` events. This enables loose coupling between extracted services and powers the agent's restocking decision data feed. |
| **Evidence** | `index.php` — order creation (line ~300) directly calls inventory check, payment insert, and status update within single `$db->beginTransaction()` block. No message publishing or event emission anywhere in code. |

*Archetype calibration applied: stateful-crud. Score 1 reflects genuine gap — cross-domain state changes have no async path, creating tight coupling that prevents safe decomposition.*

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 3 |
| **Finding** | All operations execute synchronously within the HTTP request cycle regardless of duration. No background job processing, no status polling, no callback patterns. Order creation (inventory check + order insert + items insert + payment + status update) executes entirely within one request. No async job infrastructure exists. |
| **Gap** | All operations synchronous regardless of duration. No patterns for async job processing. As the system scales or adds operations with variable latency (bulk inventory updates, external payment provider calls, shipping label generation), blocking calls will create timeout risks. |
| **Recommendation** | When decomposing, implement async patterns for operations that may exceed response time budgets. Use SQS + Lambda or EKS worker pods for: bulk inventory updates (agent restocking), payment processing with external providers, shipping label generation. Expose status polling endpoints for long-running operations. |
| **Evidence** | `index.php` — all API handlers return synchronously. No background job framework (no Bull, no Celery, no SQS consumer). No `/api/*/status` polling endpoints. |

*Archetype calibration applied: stateful-crud. Score 1 — all operations synchronous regardless of duration with no async infrastructure.*

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | No API versioning. Routes are unversioned: `/api/products`, `/api/orders`, `/api/returns`, `/api/admin/*`. No version prefix, no version headers, no changelog. Breaking changes would affect all consumers simultaneously. |
| **Gap** | No versioning strategy — breaking changes deployed directly to all consumers. Critical gap when exposing APIs for agent consumption (agents need stable API contracts). |
| **Recommendation** | Implement URL-path versioning (`/v1/api/products`) when extracting the inventory service. API Gateway (preferred) natively supports stage-based versioning. Establish backward compatibility guarantees for agent-facing endpoints. |
| **Evidence** | `index.php` — routes: `/api/products`, `/api/orders`, `/api/orders/me`, `/api/returns`, `/api/admin/orders/pending-fulfillment`, `/api/admin/pending-returns`, `/api/admin/approve-return`, `/api/admin/users`. No `/v1/` or version headers. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | Database endpoint is configured via environment variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`). In CloudFormation, the App Runner service receives the RDS endpoint via `!GetAtt DBInstance.Endpoint.Address`. No dynamic service discovery mechanism. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. When microservices are extracted, hard-coded or env-var-based service addresses will create deployment coupling. |
| **Recommendation** | Adopt AWS Cloud Map or Kubernetes-native service discovery (CoreDNS in EKS, preferred) when extracting services. API Gateway (preferred) can serve as a service catalog for external consumers. |
| **Evidence** | `index.php` — `getenv('DB_HOST')`. `infrastructure/monolith-apprunner.yaml` — `DB_HOST: !GetAtt DBInstance.Endpoint.Address` in RuntimeEnvironmentVariables. |

---

### Data Platform (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No managed object storage. Product images are referenced as filesystem paths (`/images/tshirt.jpg`) stored as VARCHAR URLs in the database. No S3 bucket defined in IaC. No document parsing pipeline. No Textract or file processing. |
| **Gap** | Unstructured data (product images) referenced as local filesystem paths with no managed storage. No S3 integration for static assets. No parsing pipeline for any unstructured content. |
| **Recommendation** | Create an S3 bucket for product images and static assets. Serve via CloudFront for performance. As the inventory service is extracted, store product images in S3 with metadata in DynamoDB (preferred) or Aurora. This enables future AI integration (image recognition, product categorization). |
| **Evidence** | `index.php` — seed data: `'/images/tshirt.jpg'`, `'/images/jeans.jpg'`, etc. in inventory table. No `AWS::S3::Bucket` in `infrastructure/monolith-apprunner.yaml`. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No data access layer. Raw PDO queries are scattered throughout the single PHP file. The `get_db()` function provides a connection factory, but every route handler constructs its own SQL queries directly. No repository pattern, no ORM, no data contract enforcement. |
| **Gap** | Database queries scattered throughout code with no abstraction pattern. Direct SQL construction in every route handler. No separation between business logic and data access. No data contract enforcement. |
| **Recommendation** | When extracting services, implement a repository/DAO pattern per service. Each extracted microservice should have a clean data access layer with defined interfaces. Use an ORM appropriate to the chosen language (e.g., Prisma for TypeScript, SQLAlchemy for Python). |
| **Evidence** | `index.php` — `$db->prepare('SELECT * FROM inventory...')` at line 293, `$db->prepare('INSERT INTO orders...')` at line 320, `$db->prepare('UPDATE inventory...')` at line 337. Raw SQL throughout all route handlers. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Priority** | P1 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | MySQL engine version explicitly pinned to 8.4.8 in CloudFormation (`EngineVersion: '8.4.8'`). MySQL 8.4 is the current Innovation Release and not approaching EOL. Docker-compose uses `mysql:8.0` for local development. AutoMinorVersionUpgrade enabled. |
| **Gap** | No documented version-update procedure (downtime windows, rollback plan, risk acknowledgment). Local development uses MySQL 8.0 while production uses 8.4.8 — version mismatch could cause compatibility issues. |
| **Recommendation** | Document a database version upgrade procedure. Align local development MySQL version with production (use `mysql:8.4` in docker-compose). Consider migrating to Aurora MySQL (preferred) which manages version upgrades more seamlessly. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `EngineVersion: '8.4.8'`, `AutoMinorVersionUpgrade: true`. `docker-compose.yml` — `image: mysql:8.0`. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | No stored procedures, no triggers, no proprietary SQL constructs. All business logic resides in the PHP application layer. Database schema uses standard SQL (CREATE TABLE, InnoDB, utf8mb4). Queries use standard MySQL-compatible SQL without proprietary extensions. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `index.php` — `init_db()` function uses only `CREATE TABLE IF NOT EXISTS` with standard DDL. All business logic in PHP. No `.sql` files with stored procedures. |

---

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application-level IaC only (App Runner, RDS, VPC, WAF for this service) which is the correct scope for an application repo. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — contains only application-level resources (App Runner, RDS, VPC, WAF, ECR, IAM roles for this service). No `AWS::CloudTrail::Trail`, no `AWS::Config::*`, no `AWS::GuardDuty::*`. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Priority** | P1 |
| **Effort** | Low |
| **Phase** | 2 |
| **Finding** | RDS storage encrypted (`StorageEncrypted: true`) using AWS-managed default encryption key. ECR repository encrypted with customer-managed KMS key (`ECRKMSKey`). VPC Flow Logs encrypted with customer-managed KMS key (`VPCFlowLogKMSKey`). Both KMS keys have `EnableKeyRotation: true`. |
| **Gap** | RDS uses AWS-managed encryption (no explicit `KmsKeyId` on DBInstance). Customer-managed KMS keys on ECR and logs but not on the primary data store (RDS). No centralized key management documentation. |
| **Recommendation** | Add a customer-managed KMS key for RDS encryption to gain control over key policy, rotation schedule, and audit trails. Document key rotation policy. All data stores should use customer-managed keys for full control. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `StorageEncrypted: true` (no KmsKeyId = AWS-managed). `ECRKMSKey` with `EnableKeyRotation: true`. `VPCFlowLogKMSKey` with `EnableKeyRotation: true`. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | Session-based authentication with bcrypt password hashing. All `/api/*` routes check `$_SESSION['user']` — unauthenticated requests receive 401. Login validates credentials against the `users` table. WAF provides IP whitelisting as an additional layer. |
| **Gap** | No token-based authentication (OAuth2/JWT). Session-based auth is not suitable for API consumption by agents or external services (sessions require cookies, are stateful, and don't support token expiry or scopes). |
| **Recommendation** | Implement OAuth2/JWT authentication via Amazon Cognito (integrates with API Gateway preferred). When extracting the inventory API for agent consumption, JWT tokens enable stateless authentication with scopes (e.g., `inventory:read`, `inventory:write`) and token-based access control. |
| **Evidence** | `index.php` — `session_start()`, `$_SESSION['user']` checks on API routes, `password_verify()` for login. No JWT library, no OAuth2 configuration. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | Application manages its own authentication entirely. Users stored in local `users` table with bcrypt passwords. PHP session-based login. No integration with any external identity provider (Cognito, Okta, Auth0). No SSO, no OIDC/SAML federation. |
| **Gap** | No external IdP integration. Standalone authentication system that cannot participate in centralized access policies or SSO. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management. When extracting services, Cognito provides: user pools, OAuth2/OIDC token issuance, social/enterprise federation, and integration with API Gateway authorizers. This enables unified access control across all extracted services. |
| **Evidence** | `index.php` — `CREATE TABLE IF NOT EXISTS users` with local password storage. `password_hash('admin123', PASSWORD_BCRYPT)` for seed users. No Cognito, Okta, or OIDC configuration. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Low |
| **Phase** | 1 |
| **Finding** | Plaintext fallback credentials in source code. The `get_db()` function contains `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'` — a hardcoded default database password. Seed data contains plaintext passwords (`'customer123'`, `'admin123'`). CloudFormation uses `NoEcho` parameters for `DBUsername`/`DBPassword` but these are passed directly to App Runner environment variables (no Secrets Manager). |
| **Gap** | Plaintext credentials in source code (fallback password, seed passwords). No AWS Secrets Manager or Vault usage. Production credentials passed as environment variables without encryption or rotation. Score 1 applies because plaintext secrets exist in version-controlled source. |
| **Recommendation** | Immediately: (1) Remove hardcoded fallback password from source code, (2) Move database credentials to AWS Secrets Manager with automated rotation, (3) Update App Runner to pull secrets from Secrets Manager at runtime. Remove seed passwords from source or move to a separate, non-committed seed script. |
| **Evidence** | `index.php` line 20 — `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. `index.php` line 166 — `password_hash('customer123', PASSWORD_BCRYPT)`. `infrastructure/monolith-apprunner.yaml` — `DB_PASS: !Ref DBPassword` in RuntimeEnvironmentVariables (plain env var, not Secrets Manager reference). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 3 |
| **Finding** | Container security practices are good: non-root user (`appuser`), read-only filesystem, `no-new-privileges` security option, health checks. ECR has scan-on-push enabled (vulnerability scanning). However: base image is standard `php:8.2-apache` (not hardened), no SSM Patch Manager (not applicable for App Runner), no Inspector integration, no automated patching workflow. |
| **Gap** | Default base image with no hardening. Vulnerability scanning exists (ECR scan-on-push) but is not integrated into a CI/CD pipeline (since no pipeline exists). No automated remediation workflow for detected vulnerabilities. |
| **Recommendation** | Switch to a hardened base image (e.g., Chainguard PHP image or custom-built minimal image). Once CI/CD is established, gate deployments on ECR scan results (fail build on critical/high vulnerabilities). Consider AWS Inspector for runtime vulnerability monitoring. |
| **Evidence** | `Dockerfile` — `FROM php:8.2-apache` (standard image), `USER appuser`, `HEALTHCHECK`. `docker-compose.yml` — `security_opt: - no-new-privileges:true`, `read_only: true`. `infrastructure/monolith-apprunner.yaml` — `ImageScanningConfiguration: ScanOnPush: true`. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | No security scanning tools configured. No CI/CD pipeline exists, so no SAST, DAST, or dependency scanning runs. No Dependabot, no Snyk, no SonarQube, no npm audit (no npm). ECR scan-on-push is the only security scanning, and it only runs on container image push (manual). |
| **Gap** | No security scanning in any automated workflow. No SAST for code vulnerabilities. No dependency scanning (and no dependency manifest to scan). No container scanning gate. |
| **Recommendation** | When building the CI/CD pipeline: (1) Add SAST tool (Semgrep or CodeGuru Reviewer), (2) Add container scanning gate (fail on critical ECR findings), (3) Add dependency scanning once Composer or other package manager is adopted. Gate deployments on scan results. |
| **Evidence** | No `.github/workflows/`, no `buildspec.yml`, no `.snyk`, no `sonar-project.properties`, no Dependabot configuration. Only scanning: `ImageScanningConfiguration: ScanOnPush: true` in CloudFormation. |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 3 |
| **Finding** | No distributed tracing instrumented. No X-Ray SDK, no OpenTelemetry, no trace ID propagation. The monolith has no tracing headers or span creation. App Runner provides basic request logging to CloudWatch but no distributed tracing. |
| **Gap** | No distributed tracing. As services are extracted, debugging cross-service request flows will be impossible without tracing infrastructure. |
| **Recommendation** | Instrument OpenTelemetry (or AWS X-Ray SDK) in extracted services from day one. EKS (preferred) supports AWS Distro for OpenTelemetry (ADOT) as a DaemonSet for automatic trace collection. Ensure trace context propagation (`traceparent` header) across all service boundaries. |
| **Evidence** | No OpenTelemetry, X-Ray, or tracing imports in `index.php`. No `aws-xray-sdk` in any dependency. No tracing configuration in IaC. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No SLO definitions. No CloudWatch alarms defined in IaC. No latency or error rate thresholds. App Runner provides basic health checks and CloudWatch metrics automatically, but no formal SLO definitions, error budget tracking, or alerting on service-level indicators. |
| **Gap** | No formal SLOs — no definition of acceptable latency, availability, or error rates. No alerting thresholds. Cannot measure whether the system is meeting user expectations. |
| **Recommendation** | Define SLOs for the inventory API (critical for agent restocking): p99 latency < 500ms, availability > 99.9%, error rate < 0.1%. Create CloudWatch alarms on these thresholds. Track error budgets. Start with App Runner's built-in CloudWatch metrics (RequestLatency, 5xxCount, 2xxCount). |
| **Evidence** | No `AWS::CloudWatch::Alarm` in `infrastructure/monolith-apprunner.yaml`. No SLO definitions in any configuration file. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No custom business metrics published. No CloudWatch `put_metric_data` calls in source. No custom dashboards. Only default App Runner infrastructure metrics (CPU, memory, request count) are available. No business KPIs tracked (order conversion rate, inventory turnover, restocking frequency). |
| **Gap** | No business outcome metrics. Cannot measure business value delivery or make data-driven modernization decisions. |
| **Recommendation** | Publish custom CloudWatch metrics for key business outcomes: orders-per-hour, inventory-stock-level (critical for agent restocking decisions), payment-success-rate, return-rate. Create business dashboards alongside infrastructure dashboards. |
| **Evidence** | `index.php` — no CloudWatch SDK calls, no metric publishing. No custom metric configuration in IaC. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No alerting configured. No CloudWatch alarms of any kind (static threshold or anomaly detection). No PagerDuty, OpsGenie, or other incident notification integration. RDS Enhanced Monitoring (MonitoringInterval: 60) provides metrics but no alarms act on them. |
| **Gap** | No alerting — degradation and failures go unnoticed until users report them. No anomaly detection on error rates or latency. |
| **Recommendation** | Add CloudWatch alarms for: App Runner 5xx error rate > 1%, p99 latency > 2s, RDS CPU > 80%, RDS free storage < 20%. Add anomaly detection on request patterns. Integrate with SNS for notifications. |
| **Evidence** | No `AWS::CloudWatch::Alarm`, no `AWS::SNS::Topic` in `infrastructure/monolith-apprunner.yaml`. RDS `MonitoringInterval: 60` provides metrics only. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 2 |
| **Finding** | App Runner performs rolling deployments by default when a new image is pushed — it gradually replaces old instances with new ones using health checks. Basic health check configured (HTTP GET to `/`, interval: 10s, healthy threshold: 1, unhealthy threshold: 5). No explicit canary or blue/green deployment configuration. |
| **Gap** | Rolling deployments with basic health checks but no traffic shifting, no canary analysis, no automated rollback on metrics degradation. Direct-to-production after image push with no staged rollout. |
| **Recommendation** | When migrating to EKS (preferred): implement canary deployments using Argo Rollouts or Flagger with automated rollback on error rate/latency degradation. For the current App Runner setup, consider App Runner's traffic-splitting feature for manual canary testing. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `HealthCheckConfiguration` with basic HTTP check. `deploy.sh` — direct `docker-compose up`. No CodeDeploy, no Argo Rollouts, no traffic shifting configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | High |
| **Priority** | P1 |
| **Effort** | Medium |
| **Phase** | 1 |
| **Finding** | No test files found anywhere in the repository. No unit tests, no integration tests, no API tests, no contract tests. No test framework configured. No test directories. Zero automated test coverage. |
| **Gap** | Zero automated testing. Every deployment carries full regression risk. Critical gap for safe monolith decomposition — cannot verify that extracted services maintain behavioral parity. |
| **Recommendation** | Immediately: (1) Add integration tests for critical API endpoints (GET /api/products, POST /api/orders) using a test container setup, (2) Add contract tests defining the API surface that extracted services must maintain, (3) Gate deployments on test passage. Start with the inventory API since it's the first extraction target. |
| **Evidence** | No `tests/`, `test/`, `spec/` directories. No `*Test.php`, `*_test.*`, `*.test.*` files. No PHPUnit, Pest, or other test framework configuration. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Medium |
| **Phase** | 3 |
| **Finding** | No runbooks, no incident response automation. No Systems Manager Automation documents. No Lambda-based remediation. No self-healing patterns. Incident response is entirely manual and ad hoc. |
| **Gap** | No incident response procedures documented or automated. Recovery from failures requires manual investigation and intervention. |
| **Recommendation** | Create runbooks for common incidents: (1) Database connection failures — restart App Runner or check RDS status, (2) High error rates — check recent deployments, rollback, (3) Inventory discrepancies — reconciliation procedure. Start with markdown runbooks, then automate with Systems Manager. |
| **Evidence** | No runbook files (markdown, YAML, JSON). No `AWS::SSM::Document` in IaC. No remediation Lambda functions. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | No observability ownership defined. No per-service dashboards. No alarms with named owners. No CODEOWNERS file. No team attribution on monitoring resources. RDS Enhanced Monitoring provides basic metrics but no ownership or alerting structure around them. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No team responsible for service health. No SLO ownership. |
| **Recommendation** | Define observability ownership: create CODEOWNERS file, assign dashboard and alarm ownership to specific team members, create per-service dashboards as services are extracted. Tag CloudWatch resources with `Owner` and `Team` tags. |
| **Evidence** | No CODEOWNERS file. No dashboards defined in IaC. No alarm ownership tags. No team-specific observability configuration. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Priority** | P2 |
| **Effort** | Low |
| **Phase** | 3 |
| **Finding** | Most resources tagged with `Name` tag. Some resources tagged with `Environment: Production`. ECR repository has both Name and Environment tags. However, no cost allocation tags (no `CostCenter`, no `Owner`, no `Team`). No tag enforcement mechanism. Inconsistent tagging — some resources only have Name, others have Name + Environment. |
| **Gap** | No cost allocation tags, no ownership tags, no team attribution. No tag enforcement via Config rules or Terraform required tags. Inconsistent tag coverage across resources. |
| **Recommendation** | Define a tagging standard: `Name`, `Environment`, `Owner`, `Team`, `CostCenter`, `Service`. When migrating to Terraform (preferred), use `default_tags` in the provider block for automatic enforcement. Add AWS Config rules for tag compliance. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — most resources have `Key: Name, Value: !Sub '${ServiceName}-*'`. ECR has `Key: Environment, Value: Production`. No `Owner`, `Team`, or `CostCenter` tags on any resource. |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `infrastructure/monolith-apprunner.yaml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, DATA-Q3, SEC-Q1, SEC-Q2, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q9 | CloudFormation template — App Runner, RDS, VPC, WAF, ECR, IAM, KMS, auto-scaling |
| `index.php` | INF-Q3, INF-Q4, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q3, SEC-Q4, SEC-Q5, OPS-Q1, OPS-Q3 | Single PHP monolith — all business logic, database schema, API routes, authentication |
| `Dockerfile` | APP-Q1, SEC-Q6 | PHP 8.2-apache container with non-root user, health check |
| `docker-compose.yml` | DATA-Q3, SEC-Q5, SEC-Q6 | Local development setup — MySQL 8.0, security hardening |
| `deploy.sh` | INF-Q11, OPS-Q5 | Manual deployment script — docker-compose build/up |
| `.htaccess` | APP-Q2 | Apache URL rewriting — all requests routed to index.php |
