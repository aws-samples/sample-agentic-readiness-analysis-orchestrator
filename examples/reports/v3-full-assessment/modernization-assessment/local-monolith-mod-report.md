# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | monolith |
| **Date** | 2026-04-27 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P0 |
| **Tags** | monolith, php, containers |
| **Context** | PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions. |
| **Overall Score** | 1.88 / 4.0 |

**Archetype Justification**: Application owns a MySQL database with 9 tables (orders, inventory, payments, returns, interactions, users, warehouses, order_items, order_status_history). Exposes CRUD endpoints for orders, returns, inventory, and users with entity lifecycle management (order status transitions: pending → confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered). No high fan-out to downstream services, no message queue consumers. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.55 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 1.33 / 4.0 | ❌ Not Present |
| Data Platform Modernization (DATA) | 2.25 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.88 / 4.0** | **🟠 Needs Work** |

> **Score Breakdown**: INF=28/11, APP=8/6, DATA=9/4, SEC=15/7, OPS=10/9. Overall = mean of 5 category scores.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith with all business domains in a single PHP file and shared database | Blocks independent scaling, deployment, and team autonomy; triggers Move to Cloud Native pathway |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — all deployments are manual shell scripts and CLI commands | Blocks safe, rapid iteration; triggers Move to Modern DevOps pathway; prerequisite for all other modernization |
| 3 | APP-Q3: Async vs Sync Communication | 1 | All communication is synchronous within the monolith; no async patterns for cross-domain state changes | Creates tight coupling between business domains; prevents event-driven decomposition |
| 4 | INF-Q4: Async Messaging and Streaming | 1 | No messaging infrastructure (SQS, SNS, EventBridge); all operations are synchronous HTTP | Cross-domain state changes (order→inventory→payment) are tightly coupled in single transactions |
| 5 | OPS-Q1: Distributed Tracing | 1 | No tracing, no observability instrumentation, no structured logging | Cannot diagnose performance issues or trace request flows; blocks operational maturity |

---

## Quick Agent Wins

No Quick Agent Wins identified. The system lacks the foundational capabilities needed to support agent integration today. Specifically:

- **API-aware agent** — Requires APP-Q5 ≥ 2 (API versioning). Score is 1 — no API versioning or OpenAPI spec exists. **Near-miss**: The application does expose structured JSON API endpoints (`/api/products`, `/api/orders`, `/api/returns`, etc.). Generating an OpenAPI specification from the existing routes would immediately enable this win.
- **Data query agent** — Requires DATA-Q2 ≥ 2 (unified data access). Score is 1 — SQL queries are scattered across 50+ locations in `index.php` with no centralized data access layer.
- **DevOps agent** — Requires INF-Q11 ≥ 2 (CI/CD pipeline). Score is 1 — no CI/CD pipeline exists.
- **RAG-based knowledge agent** — Requires documentation in the repository. No README, no wiki, no documentation files found.
- **Workflow automation agent** — Requires INF-Q3 ≥ 2 (workflow orchestration). Score is 1 — fulfillment workflow is entirely hardcoded.
- **Observability agent** — Requires OPS-Q1 ≥ 2 (distributed tracing). Score is 1 — no tracing instrumentation.

**Recommended Foundation Steps** (to enable agent wins in parallel with modernization):
1. Generate an OpenAPI spec from existing API routes → enables API-aware agent (lowest effort)
2. Add a CI/CD pipeline (GitHub Actions or CodePipeline) → enables DevOps agent
3. Add OpenTelemetry instrumentation → enables Observability agent
4. Add project documentation (README, architecture diagrams) → enables RAG knowledge agent

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 1 (tightly-coupled monolith), APP-Q3 = 1 (all sync), APP-Q4 = 1 (no async job handling) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 — compute already on App Runner (managed); Dockerfile exists; contextual guard: already containerized on managed compute |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures); MySQL is already open-source — no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — database is already fully managed RDS MySQL with Multi-AZ and automated failover |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but contextual guard prevents trigger — no data processing workloads (streaming, ETL, analytics) found in repository |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q11 = 1 (no CI/CD), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 1 (no integration tests) |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks detected; AI intent confirmed — context mentions "agent needs for restocking decisions" and portfolio references "customer support agent" and "AI agent integration" |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a tightly-coupled PHP monolith (`index.php`, ~2,500+ lines) containing all business domains — orders, inventory, payments, returns, user management, fulfillment workflow, and UI rendering — in a single file. All 9 database tables are in a shared MySQL schema. There are no module boundaries, no domain separation, and no independent deployability.

**Compute Model:**
App Runner (managed compute) is already in use — INF-Q1 scores 3. The containerization foundation exists (Dockerfile). The gap is not compute model but application architecture.

**Communication Pattern Gaps:**
- APP-Q3 = 1: All communication is synchronous within the monolith. Cross-domain operations (e.g., order creation updating inventory and creating payment records) are handled in single database transactions.
- APP-Q4 = 1: No async job handling. Return processing requires "24-48 hours manual review" but this is human latency, not managed async patterns.
- INF-Q4 = 1: No messaging infrastructure. State changes across domains are tightly coupled in PHP code.

**Recommended Decomposition Approach:**
Strangler Fig (parallel track) — see Decomposition Strategy section below. Key extraction candidates based on the fulfillment workflow:
1. **Inventory Service** (highest priority for AI agent integration — restocking decisions)
2. **Order Service** (core business domain with complex lifecycle)
3. **Fulfillment Service** (multi-step workflow: validate → assign → pick → pack → QC → ship)
4. **Returns Service** (manual process ripe for AI automation)
5. **User/Auth Service** (enable centralized identity)

**Representative AWS Services (respecting preferences):**
- **EKS** (preferred) for container orchestration of extracted microservices
- **API Gateway** (preferred) for managed API entry point with throttling, auth, and versioning
- **EventBridge** (preferred) for event-driven communication between services
- **Aurora MySQL** (preferred) for per-service databases during decomposition
- **Step Functions** for orchestrating the fulfillment workflow
- **Terraform** (preferred) for IaC, replacing CloudFormation
- **GitOps** (preferred) via ArgoCD or Flux for deployment management on EKS

**Recommended Patterns:**
- Strangler Fig pattern for incremental extraction
- Anti-corruption Layer between new services and monolith
- Saga pattern for distributed transactions (order fulfillment workflow)
- Event Sourcing for order status tracking (order_status_history table already captures state transitions)
- Hexagonal Architecture for each new service

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 3):**
CloudFormation template (`infrastructure/monolith-apprunner.yaml`) covers VPC, subnets, security groups, RDS, App Runner, ECR, WAF, IAM roles, and KMS keys — good production infrastructure coverage. However, operational resources (CloudWatch alarms, dashboards, backup plans, health checks) are not defined in IaC.

**Current CI/CD State (INF-Q11 = 1):**
No CI/CD pipeline exists. Deployment is entirely manual:
- Local development: `deploy.sh` runs `docker-compose build` and `docker-compose up -d`
- Production: CloudFormation Outputs provide manual CLI instructions for building, tagging, pushing to ECR, and updating the stack
- No automated build, test, or deploy stages

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No canary, blue/green, or rolling deployment strategy. App Runner provides automatic deployment on image push, but there is no staged rollout, no traffic shifting, and no automated rollback.

**Testing Gaps (OPS-Q6 = 1):**
No test files found in the repository — no unit tests, no integration tests, no test framework. Zero automated test coverage.

**Recommended DevOps Toolchain (respecting preferences):**
- **Terraform** (preferred) to replace CloudFormation for IaC — enables module reuse, state management, and multi-service infrastructure as the monolith decomposes
- **GitHub Actions** or **CodePipeline** for CI/CD pipeline with build, test, security scan, and deploy stages
- **GitOps** (preferred) with ArgoCD for Kubernetes deployments once services move to EKS
- **CodeDeploy** for canary/blue-green deployment strategy during the App Runner → EKS transition
- Avoid: manual deployments (per preferences)

**Recommended Implementation Order:**
1. **Week 1-2:** Create CI/CD pipeline (GitHub Actions) with build and ECR push stages
2. **Week 2-3:** Add automated testing framework (PHPUnit for existing monolith)
3. **Week 3-4:** Add security scanning (Dependabot, container scanning) to pipeline
4. **Week 4-6:** Migrate IaC from CloudFormation to Terraform
5. **Month 2-3:** Implement deployment strategy (canary via App Runner traffic splitting or CodeDeploy)

**AWS Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI/agent infrastructure exists in the repository:
- No AI/ML framework imports (no Bedrock SDK, no LangChain, no Strands, no OpenAI)
- No vector database infrastructure (no OpenSearch, no pgvector, no Pinecone)
- No RAG implementation (no embedding generation, no retrieval chains)
- No agent evaluation framework (no Ragas, no DeepEval)

**AI Intent Confirmed:**
The context explicitly references AI agent needs: "containerize and expose inventory APIs the agent needs for restocking decisions." The portfolio context confirms: "building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking."

**Application Domain & Potential AI Use Cases:**
Based on the assessment findings, the following AI use cases align with the existing application:
1. **Inventory Restocking Agent** — Uses inventory data (`/api/products`) to make autonomous restocking decisions based on stock levels, order velocity, and warehouse capacity
2. **Customer Support Agent** — Handles order inquiries (`/api/orders/me`), processes returns (`/api/returns`), and provides order status updates (`/api/orders/{id}/history`)
3. **Fulfillment Orchestration Agent** — Automates the manual fulfillment workflow (validation → warehouse assignment → picking → packing → QC → shipping) that currently requires human intervention at each step
4. **Fraud Detection Agent** — Leverages the validation data endpoint (`/api/orders/{id}/validation-data`) to make automated fraud decisions

**Foundation Requirements Before AI Integration:**
1. **API Surface** — Generate OpenAPI specs from existing routes; add API versioning (APP-Q5 gap)
2. **Authentication** — Migrate from PHP sessions to OAuth2/JWT for programmatic agent access (SEC-Q3 gap)
3. **Decomposition** — Extract Inventory and Returns services as independent APIs (APP-Q2 gap) to enable safe, scoped agent operations
4. **Observability** — Add tracing and structured logging (OPS-Q1 gap) to monitor agent behavior

**Recommended AI Services (respecting preferences):**
- **Amazon Bedrock** (preferred) for foundation model access (Claude for reasoning, decision-making)
- **Amazon Bedrock AgentCore** for agent orchestration and tool use
- **DynamoDB** (preferred) for agent session state and conversation history
- **EventBridge** (preferred) for agent-triggered events (restocking orders, return approvals)
- **OpenSearch Service** with vector engine for RAG-based knowledge retrieval

**AWS Prescriptive Guidance:**
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

<!-- SECTION: DECOMPOSITION STRATEGY -->
## Decomposition Strategy

APP-Q2 scores 1 (tightly-coupled monolith). This section provides concrete decomposition guidance.

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping it running. New features built as services; existing features migrated over time. | ✅ **Recommended.** Business domains are identifiable (Orders, Inventory, Payments, Returns, Users, Warehouses, Fulfillment) despite being in a single file. Team is actively containerizing and building AI agents — parallel track aligns with both goals. | **High** — 12-18 months for meaningful decomposition given no tests, no CI/CD, and shared database. | ✅ **Primary recommendation.** Start with Inventory Service extraction (highest AI agent value). |
| **Conditional / Adaptive** | Containerize monolith as-is (already done via App Runner), then selectively extract high-value services based on business priority. Not all modules need to become services. | Viable alternative if team capacity is limited. Focus extraction on Inventory and Returns (agent-critical services) while leaving Orders/Payments in the monolith longer. | **Low to Medium** — Selective extraction over 3-12 months after CI/CD is established. | ✅ **Recommended as Phase 1** — extract agent-critical services first, defer full decomposition. |
| **Big-Bang Rewrite** | Rewrite entire application as microservices from scratch. | Almost never. The monolith is functional and serving production traffic. No test coverage means regression risk is extremely high. | **Very High** — 12-24+ months with high risk of scope creep and feature parity gaps. | ⚠️ **Recommended against.** No test coverage makes safe rewrite nearly impossible. |

### Recommended Extraction Order (Aligned with AI Agent Needs)

1. **Inventory Service** (Priority: P0 — agent-critical)
   - Tables: `inventory`, `warehouses`
   - APIs: `/api/products`, `/api/warehouses/assignment-options`
   - Why first: Agent needs inventory APIs for restocking decisions (stated in context)

2. **Returns Service** (Priority: P0 — agent-critical)
   - Tables: `returns`, `interactions`
   - APIs: `/api/returns`, `/api/admin/pending-returns`, `/api/admin/approve-return`
   - Why second: Customer support agent needs to process returns autonomously

3. **Fulfillment Service** (Priority: P1)
   - Workflow: validate → assign warehouse → pick → pack → QC → ship → deliver
   - APIs: All `/api/orders/{id}/*` action endpoints
   - Why third: Complex workflow benefits most from Step Functions orchestration

4. **Order Service** (Priority: P1)
   - Tables: `orders`, `order_items`, `order_status_history`, `payments`
   - APIs: `/api/orders`, `/api/orders/me`, `/api/orders/{id}/history`

5. **User/Auth Service** (Priority: P2)
   - Tables: `users`
   - APIs: `/api/admin/users`, login/logout
   - Enables centralized identity (Cognito) integration

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new services from the monolith's shared MySQL schema. Translate between monolith data model and service-specific models. | Every extraction — the monolith's single `ecommerce` database schema must not leak into new services. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions for order fulfillment (validate → assign → pick → pack → QC → ship) that currently run as single-process operations. | When extracting Fulfillment Service — each step becomes a separate service call requiring coordination. Use Step Functions for orchestration. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture order state changes as events. The `order_status_history` table already captures transitions — formalize this as the source of truth. | When extracting Order Service — enables audit trails, temporal queries, and event-driven integration via EventBridge (preferred). | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear ports and adapters. Business logic in core, infrastructure adapters for database, messaging, and HTTP. | Every new service — ensures testability, portability, and clean boundaries from day one. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal Found | Effort Impact | Source |
|--------|-------------|---------------|--------|
| Module boundaries | No clear boundaries — all domains in single `index.php` file | 🔴 High effort — must identify and untangle domain boundaries | APP-Q2 finding |
| Data coupling | Single shared `ecommerce` MySQL database with cross-domain joins | 🔴 High effort — database-per-service requires data migration and schema separation | DATA-Q2 finding |
| Stored procedures | None — all business logic in PHP application layer | 🟢 Lower effort — no database-locked logic to extract | DATA-Q4 finding |
| Communication patterns | All synchronous, no async infrastructure | 🟡 Moderate effort — must introduce EventBridge (preferred) for inter-service events | APP-Q3 finding |
| CI/CD maturity | No CI/CD pipeline | 🔴 High effort — must establish pipeline before safe multi-service deployment | INF-Q11 finding |
| Test coverage | Zero automated tests | 🔴 High effort — no safety net for refactoring; must add tests before extraction | OPS-Q6 finding |

**Calibrated Effort Estimate:** Given zero test coverage and no CI/CD, the first 2-3 months should focus on establishing foundations (CI/CD pipeline, basic test coverage, Terraform migration) before beginning service extraction. Full decomposition via Strangler Fig: **12-18 months**. Selective extraction of agent-critical services (Inventory + Returns) via Conditional/Adaptive: **4-6 months** after CI/CD is in place.

---

<!-- SECTION: DETAILED FINDINGS -->
## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application runs on AWS App Runner (`AWS::AppRunner::Service`), a fully managed compute service. CloudFormation defines the App Runner service with ECR image source, VPC connector for private networking, and auto-scaling configuration. Dockerfile builds a PHP 8.2 Apache image. No raw EC2 instances are used. |
| **Gap** | App Runner is managed but has limited orchestration features compared to EKS. As the monolith decomposes into microservices, App Runner's single-service model will not scale to multi-service orchestration needs. |
| **Recommendation** | Migrate to EKS (preferred) as services are extracted from the monolith. EKS provides service mesh, advanced networking, GitOps integration (preferred), and multi-service orchestration that App Runner cannot deliver. Use App Runner for the monolith during the transition period. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (AppRunnerService, AutoScalingConfiguration), `Dockerfile` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | RDS MySQL instance (`AWS::RDS::DBInstance`) is fully managed with Multi-AZ enabled (`MultiAZ: true`), automated failover, storage encryption (`StorageEncrypted: true`), Enhanced Monitoring (`MonitoringInterval: 60`), automated backups (`BackupRetentionPeriod: 7`), deletion protection (`DeletionProtection: true`), IAM database authentication (`EnableIAMDatabaseAuthentication: true`), and custom port (`Port: 3307`). |
| **Gap** | None for current scope. As microservices are extracted, each service will need its own managed database (database-per-service pattern). |
| **Recommendation** | Maintain RDS for the monolith during decomposition. For extracted services, consider Aurora MySQL (preferred) for relational workloads and DynamoDB (preferred) for high-throughput, single-table-design workloads (e.g., inventory lookups, session state). |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (DBInstance resource) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application contains a complex multi-step fulfillment workflow (confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered) that is entirely hardcoded in `index.php`. Each step is a separate API endpoint with manual status transitions. No Step Functions, Temporal, or any workflow orchestration service is used. The `update_order_status()` function logs state transitions but provides no retry logic, error handling, or rollback capability. |
| **Gap** | No orchestration — all workflow logic is hardcoded in application code. This is a significant gap for a stateful-crud application with a clear multi-step business workflow. The fulfillment workflow has 8+ states and involves cross-domain operations (orders, inventory, warehouses, payments). |
| **Recommendation** | Implement Step Functions to orchestrate the fulfillment workflow. Each step (validate, assign warehouse, pick, pack, QC, ship) becomes a Step Functions state with built-in retry, error handling, and visual monitoring. EventBridge (preferred) can trigger workflow steps based on state change events. |
| **Evidence** | `index.php` (validate, assign-warehouse, pick, pack, quality-check, ship, deliver endpoints; `update_order_status()` function) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging infrastructure exists. No SQS, SNS, EventBridge, Kafka, Kinesis, or any message broker is defined in IaC or referenced in application code. All cross-domain operations are synchronous within the PHP process — order creation simultaneously updates inventory, creates payment records, and logs status history in a single database transaction. |
| **Gap** | No messaging where state changes cross service boundaries — tight synchronous coupling between domains that should be decoupled. When the order creation endpoint (`POST /api/orders`) fails mid-transaction, there is no compensating action beyond database rollback. As the monolith decomposes, this tight coupling must be replaced with event-driven communication. |
| **Recommendation** | Introduce EventBridge (preferred) for domain event publishing. Key events to model: `OrderCreated`, `OrderValidated`, `InventoryReserved`, `PaymentProcessed`, `ReturnRequested`, `ReturnApproved`. Each extracted service publishes and subscribes to domain events rather than making synchronous calls. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `index.php` (synchronous database transactions in order creation, return processing), `infrastructure/monolith-apprunner.yaml` (no messaging resources) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | VPC (`10.0.0.0/16`) with private subnets across 2 AZs. RDS in private subnets only (`PubliclyAccessible: false`). Security groups follow least-privilege: `DBSecurityGroup` allows MySQL (3307) only from App Runner SG; `AppRunnerSecurityGroup` allows outbound to RDS (3307) and HTTPS (443). VPC Flow Logs enabled with KMS-encrypted CloudWatch Log Group. VPC connector ensures App Runner traffic stays within VPC. |
| **Gap** | No VPC endpoints or PrivateLink configured. HTTPS outbound (0.0.0.0/0 on port 443) is broad — could be scoped to specific AWS service endpoints via VPC endpoints. No network segmentation beyond the two private subnets. |
| **Recommendation** | Add VPC endpoints for ECR, CloudWatch Logs, and S3 to eliminate internet-bound traffic for AWS service calls. Consider VPC Lattice for service-to-service networking as microservices are extracted. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (VPC, PrivateSubnet1, PrivateSubnet2, DBSecurityGroup, AppRunnerSecurityGroup, VPCConnector, VPCFlowLog) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | App Runner provides a built-in HTTPS endpoint with health checks (HTTP path `/`, interval 10s). WAF Web ACL is associated with the App Runner service, providing IP whitelisting (IPSet), and AWS Managed Rules (AWSManagedRulesKnownBadInputsRuleSet for Log4j protection). Default WAF action is Block — only whitelisted IPs can access. |
| **Gap** | No dedicated API Gateway with throttling, request validation, or API key management. App Runner's built-in endpoint lacks fine-grained traffic control. WAF provides IP filtering but not request-level validation or rate limiting per endpoint. |
| **Recommendation** | Add API Gateway (preferred) as the entry point when decomposing into microservices. API Gateway provides per-endpoint throttling, request/response validation, API keys, usage plans, and native integration with Cognito for OAuth2 authentication. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (AppRunnerService HealthCheckConfiguration, WebACL, IPSet, WebACLAssociation) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | App Runner auto-scaling is configured (`AWS::AppRunner::AutoScalingConfiguration`) with `MinSize: 1`, `MaxSize: 3`, `MaxConcurrency: 100`. This provides basic request-based scaling for the compute layer. |
| **Gap** | Auto-scaling exists but uses default/basic settings with limited range (max 3 instances). No database auto-scaling — RDS is a fixed `db.t3.micro` instance with no read replicas or auto-scaling configuration. No custom scaling policies or scheduled scaling for predictable traffic patterns. |
| **Recommendation** | Increase App Runner max instances based on traffic analysis. For the database, consider Aurora MySQL (preferred) with auto-scaling read replicas for read-heavy inventory queries. When migrating to EKS, implement Horizontal Pod Autoscaler with custom metrics. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (AutoScalingConfiguration, DBInstance — fixed db.t3.micro) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | RDS automated backups configured with `BackupRetentionPeriod: 7` days and preferred backup window (`03:00-04:00`). `DeletionPolicy: Snapshot` and `UpdateReplacePolicy: Snapshot` ensure data preservation on stack operations. `DeletionProtection: true` prevents accidental deletion. |
| **Gap** | No Point-in-Time Recovery (PITR) explicitly configured (though RDS enables PITR by default with backups). No cross-region backup replication. No documented restore procedures or tested restore processes. No backup for non-RDS data (application logs, configuration). |
| **Recommendation** | Enable cross-region read replica or AWS Backup with cross-region copy for disaster recovery. Document and test restore procedures. Consider AWS Backup plan for centralized backup management across all resources. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (DBInstance — BackupRetentionPeriod, DeletionPolicy, DeletionProtection) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | RDS Multi-AZ is enabled (`MultiAZ: true`) providing automated failover for the database. VPC connector spans 2 private subnets across 2 Availability Zones (`PrivateSubnet1` in AZ-0, `PrivateSubnet2` in AZ-1). App Runner inherently runs across multiple AZs. The database subnet group includes both private subnets. |
| **Gap** | None for current scope. Multi-AZ coverage is comprehensive for both compute and data layers. |
| **Recommendation** | Maintain current Multi-AZ configuration. When migrating to EKS, ensure pod anti-affinity rules spread workloads across AZs. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (DBInstance MultiAZ, PrivateSubnet1, PrivateSubnet2, VPCConnector, DBSubnetGroup) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CloudFormation template (`infrastructure/monolith-apprunner.yaml`, ~430 lines) covers: VPC, subnets, security groups, RDS instance, App Runner service, ECR repository, WAF Web ACL, IAM roles (4 roles with scoped policies), KMS keys (2), VPC Flow Logs, auto-scaling configuration. This represents good coverage of core production infrastructure. |
| **Gap** | No operational/DR resources in IaC: no CloudWatch alarms, no CloudWatch dashboards, no Route 53 health checks, no AWS Backup plans, no SNS notification topics for alerts. Local development uses `docker-compose.yml` which is not IaC for production. |
| **Recommendation** | Migrate to Terraform (preferred) and add operational resources: CloudWatch alarms for RDS CPU/connections/replication-lag, App Runner request count/latency/error rate, SNS topics for alert routing, and AWS Backup plans. Terraform modules enable reuse across environments and services as the monolith decomposes. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (all resources), `docker-compose.yml` (local dev only) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `appspec.yml`, no CodePipeline definitions. Deployment is entirely manual: `deploy.sh` runs `docker-compose build` and `docker-compose up -d` for local development. Production deployment requires manual CLI commands as documented in CloudFormation Outputs (docker build, ECR login, docker tag, docker push, aws cloudformation update-stack). |
| **Gap** | No CI/CD — all deployments are manual scripts or CLI commands. No automated build, test, security scan, or deploy stages. This is a critical gap that blocks safe iteration and is a prerequisite for all other modernization efforts. |
| **Recommendation** | Implement a CI/CD pipeline immediately. Recommended approach: GitHub Actions (or CodePipeline) with stages: (1) lint/test, (2) docker build, (3) security scan (Trivy/Snyk), (4) push to ECR, (5) deploy to App Runner. Avoid manual deployments (per preferences). Adopt GitOps (preferred) practices with infrastructure changes tracked in version control and applied via pipeline. |
| **Evidence** | `deploy.sh` (manual docker-compose script), `infrastructure/monolith-apprunner.yaml` (DeploymentInstructions output with manual CLI commands) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is written in PHP 8.2 (confirmed by `FROM php:8.2-apache` in Dockerfile). PHP has a functional AWS SDK (`aws-sdk-php`) but limited cloud-native tooling depth compared to Python, TypeScript, Go, or Java. No `composer.json` dependency manifest found — the application uses only built-in PHP extensions (PDO, PDO_MySQL, sessions). |
| **Gap** | PHP has narrower cloud-native tooling ecosystem. No dependency management (no Composer). The lack of a package manifest means no formal dependency tracking, no vulnerability scanning of dependencies, and no reproducible builds beyond the Docker image. |
| **Recommendation** | For extracted microservices, consider adopting languages with first-class AWS SDK and cloud-native tooling: Python or TypeScript for new services (especially AI agent integration with Bedrock). If PHP is retained, add `composer.json` for dependency management. |
| **Evidence** | `Dockerfile` (FROM php:8.2-apache), `index.php` (PHP source) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application is a tightly-coupled monolith. ALL business logic resides in a single `index.php` file (~2,500+ lines): order management, inventory tracking, payment processing, return handling, user management, fulfillment workflow (8+ states), warehouse assignment, picking/packing/QC/shipping, and complete HTML/CSS/JavaScript UI rendering. All 9 database tables share a single `ecommerce` MySQL schema. There are no packages, no modules, no namespaces, no class hierarchy — just procedural PHP with inline SQL queries and HTML output. |
| **Gap** | Tightly-coupled monolith with no clear module boundaries, pervasive shared state, and all domains in a single file. Cannot scale domains independently. Cannot deploy domains independently. A single change to any domain requires deploying the entire application. |
| **Recommendation** | Begin decomposition using Strangler Fig pattern (see Decomposition Strategy section). Extract Inventory Service first to enable AI agent integration (per context requirements). Use EKS (preferred) for orchestrating extracted services and API Gateway (preferred) for routing between monolith and new services. |
| **Evidence** | `index.php` (single file containing all business domains), `docker-compose.yml` (single `monolith` service), `infrastructure/monolith-apprunner.yaml` (single AppRunnerService) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All communication is synchronous within the monolith. As a stateful-crud application, the rubric requires async for cross-domain state propagation (e.g., order creation updating inventory and payments). The monolith handles this via synchronous database transactions (`$db->beginTransaction()` / `$db->commit()`) — when an order is created, inventory is decremented and payment is recorded in the same PHP process and database transaction. |
| **Gap** | All communication synchronous HTTP with no async patterns. Cross-domain state changes (order→inventory→payment→status-history) are tightly coupled in single database transactions. No event publishing, no message queues, no fire-and-forget patterns. |
| **Recommendation** | Introduce EventBridge (preferred) for domain event publishing during decomposition. Model key events: `OrderCreated`, `InventoryReserved`, `PaymentProcessed`, `ReturnRequested`. Avoid self-managed Kafka (per preferences). For the existing monolith, consider adding SQS-based async processing for the return approval workflow (currently requires "24-48 hours manual review"). |
| **Evidence** | `index.php` (POST /api/orders — synchronous transaction; POST /api/returns — synchronous insert; POST /api/admin/approve-return — synchronous multi-table update) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All operations are synchronous regardless of duration. The fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship → deliver) is executed as a series of individual synchronous HTTP requests, each blocking until the database transaction completes. Return processing mentions "24-48 hours manual review" but this is human latency managed outside the application — there is no async job queue, no status polling endpoint, no callback mechanism. |
| **Gap** | All operations synchronous regardless of duration. No background job frameworks (no Celery, no Bull, no SQS workers). No async/polling patterns. No job status APIs. The return approval process is the clearest candidate for async handling but has no automation infrastructure. |
| **Recommendation** | Implement Step Functions for the fulfillment workflow orchestration. Each step becomes an async state machine with built-in retry, timeout, and error handling. For return processing, add an SQS queue to decouple submission from approval. Use EventBridge (preferred) to trigger automated review logic when the AI agent is operational. |
| **Evidence** | `index.php` (fulfillment action endpoints — all synchronous; return submission with "24-48 hours manual review" message) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. All API routes are unversioned: `/api/products`, `/api/orders`, `/api/returns`, `/api/admin/pending-returns`, `/api/admin/approve-return`, `/api/admin/users`, etc. No `/v1/` prefix, no `Accept-Version` header, no versioning annotations, no changelog. |
| **Gap** | No versioning — breaking changes deployed directly. As the monolith decomposes and AI agents consume these APIs, versioning becomes critical. An unversioned API change could break all agent integrations simultaneously. |
| **Recommendation** | Add URL-path versioning (`/v1/api/products`) to all API endpoints before exposing them to AI agents. When API Gateway (preferred) is introduced, use stages for version management. Establish backward compatibility guarantees for at least one major version. |
| **Evidence** | `index.php` (all API route definitions — no version prefix) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The monolith uses environment variables for service endpoints: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS` are configured via Docker Compose environment and CloudFormation App Runner RuntimeEnvironmentVariables. The CloudFormation template passes the RDS endpoint directly to App Runner via `!GetAtt DBInstance.Endpoint.Address`. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. As the monolith decomposes into microservices, hard-coded environment variables for each service will create deployment coupling and make service relocation difficult. |
| **Recommendation** | When migrating to EKS (preferred), use Kubernetes-native service discovery (CoreDNS, Service resources). For cross-cluster or cross-account communication, use AWS Cloud Map or VPC Lattice. API Gateway (preferred) can serve as a service catalog for external consumers including AI agents. |
| **Evidence** | `docker-compose.yml` (environment variables: DB_HOST, DB_NAME, DB_USER, DB_PASS), `infrastructure/monolith-apprunner.yaml` (RuntimeEnvironmentVariables) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data handling detected. No S3 buckets defined in IaC. No file upload endpoints in the application. No document parsing libraries. Product images are referenced by URL paths (`/images/tshirt.jpg`, `/images/jeans.jpg`) but no actual image storage or S3 integration exists. All application data is structured MySQL data. |
| **Gap** | Data on local file systems or inaccessible storage. Product images referenced but not managed. No object storage for documents, media, or unstructured data. No parsing pipeline for document intelligence. |
| **Recommendation** | Add S3 for product image storage and any unstructured data. When AI agents are operational, S3 with Textract can enable document processing (receipts, return shipping labels, customer documents). Consider S3 as the data lake foundation for analytics. |
| **Evidence** | `index.php` (product `image_url` field with `/images/*.jpg` references), `infrastructure/monolith-apprunner.yaml` (no S3 resources) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Database access is scattered throughout `index.php`. The `get_db()` function creates a PDO connection, but SQL queries are embedded directly in route handlers. Over 50 `$db->prepare()` / `$stmt->execute()` calls are spread across the file — in order creation, return processing, admin approval, user management, fulfillment actions, validation data, warehouse options, picking details, packing options, quality checklists, and shipping options. No repository/DAO pattern, no ORM (no Doctrine, no Eloquent), no centralized query builder. |
| **Gap** | Database imports and queries scattered across many modules with no pattern. SQL strings are inline in every route handler. Schema changes require updating SQL in dozens of locations. No data contract enforcement. No query optimization layer. |
| **Recommendation** | As services are extracted, implement a repository/DAO pattern within each service. For the monolith, consider introducing a thin data access layer (PHP repositories per domain) as a preparatory step before extraction. For new services, use an ORM or structured query builder (e.g., Prisma for TypeScript, SQLAlchemy for Python) to centralize data access. |
| **Evidence** | `index.php` (50+ inline SQL prepare/execute calls throughout all route handlers) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CloudFormation specifies `EngineVersion: '8.4.8'` for RDS MySQL with `AutoMinorVersionUpgrade: true`. MySQL 8.4 is the current Innovation Release, actively supported. Docker Compose uses `mysql:8.0` image for local development. Version is explicitly pinned in IaC. |
| **Gap** | MySQL 8.4 is an Innovation Release with a shorter support lifecycle than LTS (Long-Term Support) releases. Docker Compose uses a different version (8.0) than production (8.4.8) — version drift between environments. No documented version-update procedure covering downtime windows, rollback, or risk acknowledgment. |
| **Recommendation** | Consider aligning to MySQL 8.0 LTS (longer support window) or planning for Aurora MySQL (preferred) which provides automatic patching and version management. Align Docker Compose MySQL version with production to eliminate version drift. Document version update procedures. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (DBInstance EngineVersion: '8.4.8', AutoMinorVersionUpgrade: true), `docker-compose.yml` (mysql:8.0 image) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the PHP application layer. SQL usage is standard MySQL-compatible: CREATE TABLE, INSERT, SELECT, UPDATE, DELETE with prepared statements. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements. The `init_db()` function uses standard DDL for schema creation. No vendor-specific SQL extensions (no T-SQL, no PL/SQL). |
| **Gap** | None. All business logic is in the application layer, making database migration straightforward. |
| **Recommendation** | Maintain this approach. When migrating to Aurora MySQL (preferred) or database-per-service with DynamoDB (preferred), the absence of stored procedures eliminates a major migration blocker. |
| **Evidence** | `index.php` (init_db() function — standard DDL; all route handlers — standard DML with prepared statements) |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | VPC Flow Logs are configured (`AWS::EC2::FlowLog`) with CloudWatch Logs destination, KMS encryption, and 30-day retention. However, no CloudTrail configuration exists in the CloudFormation template. No application-level audit logging — the `order_status_history` table tracks order state changes but this is business logic, not security audit logging. |
| **Gap** | Partial logging — VPC network traffic is logged but no API-level audit trail (CloudTrail) and no application-level audit logging. Cannot trace who accessed what API endpoints or when administrative actions (user creation, return approval) were performed. |
| **Recommendation** | Add CloudTrail configuration to IaC with log file validation and S3 Object Lock for immutable storage. Add application-level audit logging for administrative actions (user CRUD, return approvals, order status changes). Publish audit events to CloudWatch Logs with structured JSON format for agent consumption. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (VPCFlowLog, VPCFlowLogGroup, VPCFlowLogKMSKey — present; no AWS::CloudTrail::Trail resource) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | RDS storage encryption is enabled (`StorageEncrypted: true`) but uses AWS-managed keys — no customer-managed KMS key is specified for the RDS instance. ECR repository uses customer-managed KMS key (`ECRKMSKey` with `EnableKeyRotation: true`) for image encryption. VPC Flow Log CloudWatch Log Group uses customer-managed KMS key (`VPCFlowLogKMSKey` with `EnableKeyRotation: true`). |
| **Gap** | RDS uses AWS-managed encryption rather than customer-managed KMS keys. No centralized key management policy documented. Key rotation is enabled on the ECR and Flow Log keys but not governable for the RDS AWS-managed key. |
| **Recommendation** | Create a customer-managed KMS key for RDS encryption to enable centralized key management, custom key policies, and auditable key usage via CloudTrail. When adding S3 buckets (for unstructured data), ensure SSE-KMS with customer-managed keys. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (DBInstance StorageEncrypted: true — no KmsKeyId; ECRKMSKey; VPCFlowLogKMSKey) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Application uses PHP session-based authentication. The login endpoint (`POST /login`) verifies bcrypt-hashed passwords and stores user data in `$_SESSION`. All API endpoints check `$_SESSION['user']` and return HTTP 401 if not authenticated. Admin endpoints additionally check `$_SESSION['user']['role'] !== 'admin'` and return HTTP 403. |
| **Gap** | API key or static credential authentication without token-based auth. Session-based auth requires browser cookies and cannot be used by programmatic API consumers (AI agents, microservices). No OAuth2, no JWT, no API keys. Session tokens are not verifiable without server-side state. |
| **Recommendation** | Migrate to OAuth2/JWT authentication via Amazon Cognito (or API Gateway authorizers) when decomposing into microservices. JWT tokens enable stateless authentication across services and are consumable by AI agents. API Gateway (preferred) provides native Cognito integration for per-endpoint authorization. |
| **Evidence** | `index.php` (session_start(), $_SESSION['user'] checks, password_verify() for login, role-based access control on admin endpoints) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Application manages its own authentication entirely. User accounts are stored in a `users` MySQL table with bcrypt-hashed passwords. Authentication is handled via PHP sessions with no external identity provider integration. No Cognito, no OIDC, no SAML, no SSO, no federation. Seed data includes hardcoded demo credentials (`customer/customer123`, `admin/admin123`). |
| **Gap** | Application manages its own authentication entirely with no external IdP integration. This creates a standalone authentication silo that cannot participate in unified access policies, SSO, or MFA enforcement. |
| **Recommendation** | Integrate with Amazon Cognito as the centralized identity provider. Cognito provides user pools, OAuth2/OIDC, MFA, and federation with enterprise IdPs. For the decomposed architecture, Cognito tokens will authenticate both human users and AI agents across all services. |
| **Evidence** | `index.php` (users table with password_hash/password_verify, session-based auth, hardcoded seed credentials) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database credentials are managed via environment variables: CloudFormation parameters `DBUsername` and `DBPassword` with `NoEcho: true`, passed to App Runner as `RuntimeEnvironmentVariables`. Docker Compose uses `${MYSQL_PASSWORD:?Set MYSQL_PASSWORD}` (required env var). The `get_db()` function reads `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS` from environment with fallback defaults (hardcoded in code: `'ecommerce_user'`, `'ecommerce_pass'`). |
| **Gap** | Production database credentials in environment variables, not in Secrets Manager or Vault. Fallback credentials are hardcoded in `index.php` (`'ecommerce_user'` and `'ecommerce_pass'`). No rotation configured. CloudFormation NoEcho prevents display but credentials are stored in plaintext in the parameter store. |
| **Recommendation** | Migrate database credentials to AWS Secrets Manager with automated rotation. App Runner supports Secrets Manager integration via `RuntimeEnvironmentSecrets`. Remove hardcoded fallback credentials from `index.php`. For the decomposed architecture, each service should retrieve credentials from Secrets Manager at runtime. |
| **Evidence** | `index.php` (get_db() with hardcoded fallback credentials), `infrastructure/monolith-apprunner.yaml` (RuntimeEnvironmentVariables with DB_USER/DB_PASS), `docker-compose.yml` (MYSQL_PASSWORD env var) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Dockerfile creates a non-root user (`appuser`) and runs as that user (`USER appuser`). Docker Compose applies `security_opt: no-new-privileges:true` and `read_only: true` filesystem for both monolith and MySQL containers. ECR has `ScanOnPush: true` for container vulnerability scanning and `ImageTagMutability: IMMUTABLE` preventing tag overwriting. App Runner is a managed service — AWS handles OS-level patching. Healthcheck configured in Dockerfile. |
| **Gap** | No SSM Patch Manager or AWS Inspector configuration. ECR scanning occurs on push but findings are not gated in a pipeline (no CI/CD exists). No hardened base image (uses stock `php:8.2-apache`, not a CIS-benchmarked or Bottlerocket image). |
| **Recommendation** | When CI/CD is established, gate deployments on ECR scan findings (fail on critical/high vulnerabilities). Consider Bottlerocket or Amazon Linux 2023-based images when migrating to EKS. Add AWS Inspector for continuous vulnerability assessment of running containers. |
| **Evidence** | `Dockerfile` (USER appuser, HEALTHCHECK), `docker-compose.yml` (security_opt, read_only), `infrastructure/monolith-apprunner.yaml` (ECRRepository ScanOnPush, ImageTagMutability: IMMUTABLE) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | ECR `ScanOnPush: true` provides container image vulnerability scanning when images are pushed. `ImageTagMutability: IMMUTABLE` prevents image tag overwriting. However, no CI/CD pipeline exists, so there are no pipeline-integrated security scanning stages. No SAST tool (no SonarQube, no Semgrep, no CodeGuru). No Dependabot or `composer audit`. No `.snyk` policy file. |
| **Gap** | Dependency scanning configured (ECR scan on push) and running, but no SAST tool. No security gates blocking on critical findings. Scanning occurs at push time but is not integrated into a development workflow (no pipeline). No static analysis of PHP source code for vulnerabilities (SQL injection, XSS, etc.). |
| **Recommendation** | When CI/CD is established: add Snyk or Trivy for container scanning with blocking gates on critical findings, add Semgrep or PHPStan for SAST on PHP code, add Dependabot for dependency vulnerability tracking (once `composer.json` is added). |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (ECRRepository ScanOnPush: true, ImageTagMutability: IMMUTABLE), no `.github/`, no `buildspec.yml`, no security tool configs |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No X-Ray SDK, no OpenTelemetry SDK, no tracing libraries in dependencies (no `composer.json` exists). No trace ID propagation (no `traceparent` or `X-Amzn-Trace-Id` headers). No tracing configuration in Dockerfile, docker-compose, or CloudFormation. |
| **Gap** | No distributed tracing instrumented. Cannot trace request flows, identify bottlenecks, or diagnose issues across the application. As the monolith decomposes, tracing becomes critical for understanding cross-service request paths. |
| **Recommendation** | Add OpenTelemetry PHP SDK instrumentation. When migrating to EKS, use AWS Distro for OpenTelemetry (ADOT) as a sidecar collector. Configure X-Ray as the tracing backend. Ensure trace ID propagation from API Gateway (preferred) through all services. |
| **Evidence** | `index.php` (no tracing imports), `Dockerfile` (no tracing agent), `infrastructure/monolith-apprunner.yaml` (no tracing configuration) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No error budget tracking. No latency targets. No availability targets. No CloudWatch alarms on p99/p95 latency or error rates. |
| **Gap** | No SLOs — no formal definition of acceptable service levels. Cannot measure whether the system meets user expectations. No data to drive prioritization of operational improvements. |
| **Recommendation** | Define SLOs for critical user journeys: order placement latency (p99 < 2s), product listing availability (99.9%), return submission success rate (99.5%). Implement CloudWatch alarms for SLO breaches. Track error budgets to balance feature velocity with reliability. |
| **Evidence** | All repository files — no SLO definitions, no CloudWatch alarms, no error budget configs |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. No `cloudwatch.put_metric_data` calls. No business metric dashboards. The application tracks business events in the database (order status transitions in `order_status_history`, payment records in `payments`, return records in `returns`) but does not publish these as CloudWatch metrics for real-time monitoring. |
| **Gap** | No custom metrics — only default App Runner and RDS infrastructure metrics available. Cannot track business outcomes (orders per hour, return rate, fulfillment cycle time, revenue) in real-time. |
| **Recommendation** | Publish custom CloudWatch metrics for key business events: `OrdersCreated`, `OrdersShipped`, `ReturnsRequested`, `ReturnsApproved`, `InventoryStockLevel`, `FulfillmentCycleTime`. Create CloudWatch dashboards combining business and infrastructure metrics. These metrics will also inform AI agent performance monitoring. |
| **Evidence** | `index.php` (no CloudWatch SDK calls, no metric publishing), `infrastructure/monolith-apprunner.yaml` (no custom metric resources) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudWatch alarms configured. No anomaly detection. No alerting integration (no PagerDuty, no OpsGenie, no SNS alarm topics). RDS Enhanced Monitoring (`MonitoringInterval: 60`) provides OS-level metrics but no alarms are defined on them. WAF CloudWatch metrics are enabled but no alarms trigger on them. |
| **Gap** | No alerting configured. Infrastructure monitoring data exists (RDS Enhanced Monitoring, WAF metrics) but no one is notified when thresholds are breached. Cannot detect performance degradation, error spikes, or security anomalies. |
| **Recommendation** | Add CloudWatch alarms for: RDS CPU utilization > 80%, RDS free storage < 20%, RDS connection count, App Runner error rate > 1%, App Runner p99 latency, WAF blocked request spikes. Add SNS topic for alarm notifications with PagerDuty or OpsGenie integration. Enable CloudWatch anomaly detection on error rates. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (MonitoringInterval: 60 on RDS, CloudWatchMetricsEnabled on WAF — but no AWS::CloudWatch::Alarm resources) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. `deploy.sh` runs `docker-compose up -d` for local development — direct replacement with no health check validation. Production deployment is a manual CloudFormation stack update (`aws cloudformation update-stack`). App Runner does support automatic deployment on ECR image push, but no canary, blue/green, or rolling deployment strategy is configured. No traffic shifting, no staged rollout. |
| **Gap** | Direct-to-production deployment with no staged rollout. A bad image push to ECR would immediately affect all users. No automated rollback on health check failure. |
| **Recommendation** | For the current App Runner setup, implement image tag-based deployments with manual promotion. When migrating to EKS, implement canary deployments via Argo Rollouts or Flagger with progressive traffic shifting. Adopt GitOps (preferred) with ArgoCD for declarative deployment management. Avoid manual deployments (per preferences). |
| **Evidence** | `deploy.sh` (docker-compose up -d), `infrastructure/monolith-apprunner.yaml` (DeploymentInstructions with manual CLI commands) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No test files found anywhere in the repository. No test directories, no test framework configuration, no PHPUnit, no Pest, no Codeception. No integration tests, no unit tests, no API tests, no contract tests. Zero automated test coverage. |
| **Gap** | No integration tests — no automated tests of any kind. Cannot validate that API endpoints return correct responses, that database operations complete successfully, or that the fulfillment workflow transitions are valid. Extremely high regression risk during any modification. |
| **Recommendation** | Add PHPUnit or Pest for the existing monolith as a safety net before decomposition. Prioritize integration tests for critical workflows: order creation, return processing, fulfillment state transitions. For extracted microservices, implement contract tests (Pact) between services and integration tests using test containers in the CI pipeline. |
| **Evidence** | All repository files — no test files, no test directories, no test framework configuration |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found in the repository — no markdown runbooks, no YAML runbooks, no SSM Automation documents. No Lambda-based remediation. No self-healing patterns. No incident response workflows. |
| **Gap** | No runbooks — incident response is entirely ad hoc. No documented procedures for common failure scenarios (database connection failure, App Runner health check failure, ECR push failure, high error rate). |
| **Recommendation** | Create runbooks for common incidents: database connection timeout, high latency, deployment failure, WAF false positive. Implement SSM Automation documents for self-healing (e.g., automatic RDS failover trigger, App Runner service restart). Store runbooks as versioned markdown in the repository. |
| **Evidence** | All repository files — no runbook files, no automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file. No per-service dashboards (no dashboards at all). No SLO definitions with team attribution. No named alarm owners. No team tags on observability resources. |
| **Gap** | No observability ownership — monitoring is reactive and fragmented. No one is formally responsible for monitoring the application's health, responding to alerts, or maintaining observability infrastructure. |
| **Recommendation** | Add CODEOWNERS file with team attribution for infrastructure and application code. Create per-service CloudWatch dashboards. Assign named owners to alarms. When decomposing, each service team should own their observability stack (dashboards, alarms, SLOs, runbooks). |
| **Evidence** | All repository files — no CODEOWNERS, no dashboard definitions, no team attribution |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CloudFormation resources have `Name` tags and some have `Environment` tags (ECR: `Environment: Production`, App Runner: `Environment: Production`). Tags are present on: VPC, subnets, security groups, RDS, ECR, App Runner, WAF, KMS keys, VPC connector, auto-scaling configuration. |
| **Gap** | Some resources tagged but many lack cost allocation, ownership, or project attribution tags. No consistent tagging standard across all resources. No `Owner`, `CostCenter`, `Project`, or `Team` tags. No tag enforcement via IaC defaults or AWS Config rules. Tags are limited to `Name` and occasionally `Environment`. |
| **Recommendation** | Define a tagging standard: `Name`, `Environment`, `Owner`, `CostCenter`, `Project`, `Team`. Apply via Terraform (preferred) `default_tags` provider configuration. Add AWS Config `required-tags` rule to enforce compliance. Activate cost allocation tags in AWS Billing. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` (Tags on VPC, subnets, SGs, RDS, ECR, App Runner, WAF, KMS — Name and Environment only) |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `index.php` | INF-Q3, INF-Q4, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q3, SEC-Q4, SEC-Q5, OPS-Q1, OPS-Q3 | Single PHP monolith containing all business logic, API routes, database schema, SQL queries, authentication, and UI rendering (~2,500+ lines) |
| `Dockerfile` | INF-Q1, APP-Q1, SEC-Q6, OPS-Q1 | PHP 8.2 Apache image, non-root user, healthcheck, PDO MySQL extension |
| `docker-compose.yml` | INF-Q1, APP-Q6, DATA-Q3, SEC-Q5, SEC-Q6, OPS-Q5 | Local development composition: MySQL 8.0 + PHP monolith, security hardening (no-new-privileges, read_only), environment variable configuration |
| `infrastructure/monolith-apprunner.yaml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, DATA-Q1, DATA-Q3, SEC-Q1, SEC-Q2, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q4, OPS-Q9 | CloudFormation template (~430 lines): VPC, subnets, SGs, RDS MySQL 8.4.8 (Multi-AZ, encrypted), App Runner, ECR (KMS, scan-on-push), WAF, IAM roles, KMS keys, VPC Flow Logs, auto-scaling |
| `deploy.sh` | INF-Q11, OPS-Q5 | Manual deployment script: docker-compose build and up for local development |
| `.htaccess` | APP-Q2 | Apache rewrite rules routing all requests to index.php |
| `.gitignore` | — | Standard ignores: data/, logs, OS files, IDE files |
